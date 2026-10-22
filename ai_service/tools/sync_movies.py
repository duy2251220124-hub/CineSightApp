"""Công cụ đồng bộ danh mục phim từ TMDB vào SQLite (cinesight.db).
Chỉ dùng thư viện chuẩn Python (urllib, json, sqlite3, datetime, argparse, os, sys).

Tính năng:
- Đồng bộ tối đa --max-now (mặc định 10) phim đang chiếu và --max-upcoming (mặc định 5) phim sắp chiếu.
- Tự động phân giải ngày khởi chiếu tại thị trường Việt Nam (release_dates với iso_3166_1='VN').
- Bảo toàn tuyệt đối các trường hiệu chỉnh: title_override, runtime_override, is_active.
- Cờ --dry-run: chỉ hiển thị bảng kế hoạch đối chiếu, không ghi vào CSDL.
- Cờ --from-snapshot <đường-dẫn>: nạp từ snapshot JSON để kiểm thử offline và tránh lỗi mạng rớt gói.
- Cờ --purge-older-than-days N (mặc định 180): dọn dẹp mềm (is_active=0) các phim TMDB cũ.
- Tự động che giấu credential trong log và báo lỗi (redact).
- Bắt buộc ghi nhận nguồn bản quyền TMDB.
"""
import argparse
import datetime
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Đảm bảo import được các module trong ai_service và ai_service/tools
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from env_loader import redact, load_env
from movies_repo import (
    DEFAULT_DB_PATH,
    get_connection,
    init_movies_tables,
    purge_old_tmdb_movies,
    upsert_tmdb_movie,
)

TMDB_ATTRIBUTION_NOTICE = "This product uses the TMDB API but is not endorsed or certified by TMDB."


def extract_vn_release_date(release_dates_resp):
    """Trích xuất ngày phát hành tại thị trường Việt Nam (iso_3166_1 == 'VN').
    Ưu tiên theatrical release (type == 3), nếu không lấy ngày phát hành nhỏ nhất."""
    if not release_dates_resp or "results" not in release_dates_resp:
        return None

    vn_entry = None
    for item in release_dates_resp.get("results", []):
        if item.get("iso_3166_1") == "VN":
            vn_entry = item
            break

    if not vn_entry:
        return None

    dates = vn_entry.get("release_dates", [])
    if not dates:
        return None

    # Tìm theatrical release (type 3)
    theatrical = [d for d in dates if d.get("type") == 3 and d.get("release_date")]
    chosen = theatrical[0] if theatrical else dates[0]
    raw_date = chosen.get("release_date", "")
    return raw_date[:10] if len(raw_date) >= 10 else None


def load_from_snapshot(snapshot_path):
    """Đọc dữ liệu thô từ file snapshot JSON."""
    with open(snapshot_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def fetch_from_tmdb_live(client, max_now=10, max_upcoming=5):
    """Gọi trực tiếp TMDB API v3 với rate limit và backoff."""
    print(" [NET] Đang gọi TMDB: /movie/now_playing (region=VN, language=vi-VN)...")
    now_resp = client.get("/movie/now_playing", {"region": "VN", "language": "vi-VN", "page": 1})

    print(" [NET] Đang gọi TMDB: /movie/upcoming (region=VN, language=vi-VN)...")
    up_resp = client.get("/movie/upcoming", {"region": "VN", "language": "vi-VN", "page": 1})

    now_results = now_resp.get("results", [])[:max_now]
    up_results = up_resp.get("results", [])[:max_upcoming]

    # Thu thập danh sách ID không trùng lặp
    combined_movies = {}
    for m in now_results:
        combined_movies[m["id"]] = ("now_playing", m)
    for m in up_results:
        if m["id"] not in combined_movies:
            combined_movies[m["id"]] = ("upcoming", m)

    movie_details = {}
    release_dates = {}

    for mid, (category, m) in combined_movies.items():
        print(f" [NET] Đang lấy chi tiết phim TMDB #{mid}...")
        try:
            det = client.get(f"/movie/{mid}", {"language": "vi-VN"})
            movie_details[str(mid)] = det
        except Exception as e:
            print(f"  ! Lỗi lấy chi tiết phim #{mid}: {redact(str(e))}")

        try:
            rd = client.get(f"/movie/{mid}/release_dates")
            release_dates[str(mid)] = rd
        except Exception as e:
            print(f"  ! Lỗi lấy release dates #{mid}: {redact(str(e))}")

    snapshot_data = {
        "fetched_at": datetime.datetime.now().isoformat(),
        "region": "VN",
        "language": "vi-VN",
        "now_playing": now_resp,
        "upcoming": up_resp,
        "movie_details": movie_details,
        "release_dates": release_dates,
    }
    return snapshot_data


def process_sync(snapshot_data, max_now=10, max_upcoming=5, dry_run=False, purge_days=180, db_path=None):
    """Xử lý dữ liệu đồng bộ, đối chiếu CSDL và in bảng báo cáo chi tiết."""
    init_movies_tables(db_path=db_path)
    conn = get_connection(db_path=db_path)

    now_list = snapshot_data.get("now_playing", {}).get("results", [])[:max_now]
    up_list = snapshot_data.get("upcoming", {}).get("results", [])[:max_upcoming]
    details_map = snapshot_data.get("movie_details", {})
    releases_map = snapshot_data.get("release_dates", {})

    # Ghép danh sách độc nhất (ưu tiên now_playing trước)
    ordered_items = []
    seen_ids = set()
    for m in now_list:
        mid = m.get("id")
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            ordered_items.append(("Đang chiếu", m))

    for m in up_list:
        mid = m.get("id")
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            ordered_items.append(("Sắp chiếu", m))

    report_rows = []
    added_count = 0
    updated_count = 0
    skipped_rows = []

    cursor = conn.cursor()

    for category, base_item in ordered_items:
        mid = base_item["id"]
        det = details_map.get(str(mid), {})
        rd = releases_map.get(str(mid), {})

        # Không bịa dữ liệu: thiếu thời lượng hoặc ngày chiếu thì BỎ QUA và ghi vào báo cáo
        _rt = det.get("runtime")
        _has_runtime = bool(_rt) and int(_rt) > 0
        _vn = extract_vn_release_date(rd)
        _list_rd = (det.get("release_date") or base_item.get("release_date") or "")[:10]
        if not _has_runtime or not (_vn or _list_rd):
            reason = "thiếu runtime" if not _has_runtime else "thiếu ngày chiếu"
            skipped_rows.append((mid, base_item.get("title") or base_item.get("original_title") or "?", reason))
            continue

        # Tên gốc và tên tiếng Việt
        title_orig = det.get("original_title") or base_item.get("original_title") or base_item.get("title") or ""
        title_vi_cand = det.get("title") or base_item.get("title") or title_orig

        # Kiểm tra xem phim đã có trong DB chưa
        cursor.execute("SELECT id, title_vi, title_original, title_override, runtime_override, release_date, runtime_min, poster_path, is_active FROM movies WHERE tmdb_id = ?", (mid,))
        existing = cursor.fetchone()

        if existing:
            action_status = "Cập nhật" if not dry_run else "Kế hoạch cập nhật"
            updated_count += 1
            db_id = existing["id"]
            title_override = existing["title_override"]
        else:
            action_status = "Thêm mới" if not dry_run else "Kế hoạch thêm mới"
            added_count += 1
            db_id = None
            title_override = None

        # Xác định tên hiển thị và nguồn tên
        if title_override:
            disp_title = title_override
            name_source = "override"
        elif title_vi_cand and title_vi_cand.strip() != title_orig.strip():
            disp_title = title_vi_cand
            name_source = "vi"
        else:
            disp_title = title_orig
            name_source = "gốc"

        # Phân giải ngày khởi chiếu tại VN
        vn_date = extract_vn_release_date(rd)
        if vn_date:
            release_date = vn_date
            rd_source_str = "VN"
            db_rd_source = "vn_release_dates"
        else:
            raw_rd = det.get("release_date") or base_item.get("release_date") or ""
            release_date = raw_rd[:10] if raw_rd else "Chưa rõ"
            rd_source_str = "Toàn cầu"
            db_rd_source = "list_field"

        # Phân giải thời lượng
        runtime = det.get("runtime")
        if runtime and int(runtime) > 0:
            runtime_min = int(runtime)
            runtime_str = f"{runtime_min}p"
        else:
            runtime_min = 120
            runtime_str = "120p (mặc định)"

        poster = det.get("poster_path") or base_item.get("poster_path")
        backdrop = det.get("backdrop_path") or base_item.get("backdrop_path")
        poster_str = "Có" if poster else "Không"
        popularity = float(det.get("popularity") or base_item.get("popularity") or 0.0)

        # Thực thi ghi DB nếu không dry-run
        if not dry_run:
            movie_record = {
                "tmdb_id": mid,
                "title_vi": title_vi_cand,
                "title_original": title_orig,
                "release_date": release_date if release_date != "Chưa rõ" else "2026-01-01",
                "release_date_source": db_rd_source,
                "runtime_min": runtime_min,
                "poster_path": poster,
                "backdrop_path": backdrop,
                "popularity": popularity,
            }
            db_id, _ = upsert_tmdb_movie(movie_record, db_path=db_path)

        report_rows.append({
            "tmdb_id": mid,
            "db_id": db_id,
            "title": disp_title,
            "name_source": name_source,
            "release_date_display": f"{release_date} ({rd_source_str})",
            "runtime_display": runtime_str,
            "poster_display": poster_str,
            "status": action_status,
            "category": category,
        })

    # Dọn dẹp mềm các phim cũ hơn N ngày
    purge_result = purge_old_tmdb_movies(days=purge_days, dry_run=dry_run, db_path=db_path)

    conn.close()

    # In Bảng Báo Cáo dạng Text Table
    print("\n" + "=" * 105)
    mode_text = "DRY-RUN (CHỈ MÔ PHỎNG KẾ HOẠCH, CHƯA GHI DB)" if dry_run else "THỰC THI THẬT (ĐÃ LƯU VÀO CSDL)"
    print(f" BẢNG BÁO CÁO ĐỒNG BỘ DANH MỤC PHIM TMDB - CHẾ ĐỘ: {mode_text}")
    print("=" * 105)

    header = f"| {'ID TMDB':<9} | {'Tên hiển thị':<36} | {'Nguồn':<7} | {'Ngày khởi chiếu':<18} | {'Thời lượng':<12} | {'Poster':<6} | {'Trạng thái':<18} |"
    sep = "+" + "-" * 11 + "+" + "-" * 38 + "+" + "-" * 9 + "+" + "-" * 20 + "+" + "-" * 14 + "+" + "-" * 8 + "+" + "-" * 20 + "+"

    print(sep)
    print(header)
    print(sep)

    for r in report_rows:
        title_truncated = r["title"][:34] + ".." if len(r["title"]) > 36 else r["title"]
        row_str = (
            f"| {str(r['tmdb_id']):<9} "
            f"| {title_truncated:<36} "
            f"| {r['name_source']:<7} "
            f"| {r['release_date_display']:<18} "
            f"| {r['runtime_display']:<12} "
            f"| {r['poster_display']:<6} "
            f"| {r['status']:<18} |"
        )
        print(row_str)

    print(sep)
    print(f"\n--- TỔNG KẾT TIẾN TRÌNH ĐỒNG BỘ ({'DRY-RUN' if dry_run else 'HOÀN TẤT'}) ---")
    print(f" - Tổng số phim xử lý: {len(report_rows)} ({len(now_list)} đang chiếu, {len(up_list)} sắp chiếu)")
    print(f" - Phim thêm mới      : {added_count}")
    print(f" - Phim cập nhật      : {updated_count}")
    print(f" - Phim bỏ qua (thiếu dữ liệu): {len(skipped_rows)}")
    for sid, stitle, sreason in skipped_rows:
        print(f"     x {sid} | {stitle} -> {sreason}")
    print(f" - Dọn dẹp mềm (> {purge_days} ngày): {purge_result['count']} phim chuyển sang is_active=0")
    print(f"\n[BẢN QUYỀN TMDB BẮT BUỘC]: \"{TMDB_ATTRIBUTION_NOTICE}\"")
    print("=" * 105)

    return report_rows


def main():
    parser = argparse.ArgumentParser(description="Đồng bộ danh mục phim TMDB vào SQLite cinesight.db")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ lập bảng kế hoạch, không ghi CSDL")
    parser.add_argument("--max-now", type=int, default=10, help="Số phim đang chiếu tối đa (mặc định: 10)")
    parser.add_argument("--max-upcoming", type=int, default=5, help="Số phim sắp chiếu tối đa (mặc định: 5)")
    parser.add_argument("--from-snapshot", type=str, default=None, help="Đường dẫn file snapshot JSON để nạp offline")
    parser.add_argument("--purge-older-than-days", type=int, default=180, help="Số ngày để đánh dấu is_active=0 (mặc định: 180)")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Đường dẫn file SQLite DB")
    parser.add_argument("--output-snapshot", type=str, default=None, help="Đường dẫn lưu snapshot khi gọi online")
    parser.add_argument("--allow-synthetic", action="store_true", help="Cho phép nạp snapshot đánh dấu _synthetic (chỉ để test)")

    args = parser.parse_args()
    load_env()

    snapshot_data = None
    if args.from_snapshot:
        print(f" [OFFLINE] Nạp dữ liệu phim từ file snapshot: {args.from_snapshot}")
        if not os.path.exists(args.from_snapshot):
            print(f" [LỖI] Không tìm thấy tệp snapshot: {args.from_snapshot}")
            return 1
        snapshot_data = load_from_snapshot(args.from_snapshot)
        if snapshot_data.get("_synthetic") and not args.allow_synthetic:
            print(" [TỪ CHỐI] Snapshot này là dữ liệu GIẢ (_synthetic=true), không được nạp vào DB.")
            print("           Dùng snapshot do TMDB trả về thật, hoặc thêm --allow-synthetic khi test trên DB tạm.")
            return 2
    else:
        # Gọi trực tiếp qua TmdbClient
        try:
            from tools.tmdb_client import TmdbClient, TmdbError
            client = TmdbClient(max_per_sec=4)
            print(f" [ONLINE] Khởi động TmdbClient (loại khóa: {client.kind})...")
            snapshot_data = fetch_from_tmdb_live(client, max_now=args.max_now, max_upcoming=args.max_upcoming)

            # Lưu snapshot nếu thành công
            raw_dir = os.path.join(AI_SERVICE_DIR, "data_raw")
            os.makedirs(raw_dir, exist_ok=True)
            today_str = datetime.date.today().strftime("%Y%m%d")
            out_file = args.output_snapshot or os.path.join(raw_dir, f"tmdb_sync_{today_str}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            print(f" [CACHE] Đã lưu snapshot dữ liệu thô vào: {out_file}")
        except Exception as e:
            from env_loader import redact
            print(f" [LỖI MẠNG] Không thể kết nối TMDB: {redact(str(e))}")
            print(" [HƯỚNG DẪN] Do DNS nhà mạng chặn domain TMDB, hãy sử dụng flag --from-snapshot để nạp dữ liệu offline an toàn.")
            return 1

    process_sync(
        snapshot_data,
        max_now=args.max_now,
        max_upcoming=args.max_upcoming,
        dry_run=args.dry_run,
        purge_days=args.purge_older_than_days,
        db_path=args.db
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
