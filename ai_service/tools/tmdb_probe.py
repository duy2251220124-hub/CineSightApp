"""Gọi thử TMDB có giới hạn (CHỈ ĐỌC, KHÔNG ghi DB). Lưu phản hồi thô vào data_raw\tmdb_probe_<ngày>.json.

Tổng số lệnh gọi tối đa: 6
  1) now_playing  region=VN language=vi-VN page=1
  2) upcoming     region=VN language=vi-VN page=1
  3) now_playing  KHÔNG region, language=en-US page=1   (để so sánh tác dụng của tham số region)
  4-6) chi tiết 3 phim (2 đầu danh sách đang chiếu + 1 đầu danh sách sắp chiếu)
       kèm append_to_response=release_dates (1 lệnh/phim)
"""
import datetime
import json
import re
import sys
from pathlib import Path

from env_loader import BASE_DIR, get_tmdb_credential, load_env
from tmdb_client import TmdbClient, TmdbError

LIST_PARAMS = {"region": "VN", "language": "vi-VN", "page": 1}
# Ký tự tiếng Việt có dấu đặc trưng: nếu tên chứa ký tự này thì coi là đã có tên Việt.
VI_CHARS = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)


def vn_theatrical_dates(release_dates_block):
    """Từ khối release_dates của phim, lấy các ngày chiếu rạp (type 2 hoặc 3) của VN."""
    out = []
    for entry in (release_dates_block or {}).get("results", []):
        if entry.get("iso_3166_1") == "VN":
            for rd in entry.get("release_dates", []):
                if rd.get("type") in (2, 3):
                    out.append((rd.get("type"), (rd.get("release_date") or "")[:10]))
    return sorted(out, key=lambda x: x[1])


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    load_env()
    kind, secret = get_tmdb_credential()
    if kind is None:
        print("chưa có khóa")
        return 2
    print(f"đã có khóa loại {kind}, độ dài {len(secret)}")
    client = TmdbClient()
    raw = {"fetched_at": datetime.datetime.now().isoformat(timespec="seconds"), "requests": []}

    def call(label, path, params):
        data = client.get(path, params)
        raw["requests"].append({"label": label, "path": path, "params": params, "response": data})
        return data

    try:
        now_vn = call("now_playing_VN", "/movie/now_playing", LIST_PARAMS)
        up_vn = call("upcoming_VN", "/movie/upcoming", LIST_PARAMS)
        now_any = call("now_playing_noregion", "/movie/now_playing", {"language": "en-US", "page": 1})

        for label, data in (("now_playing VN", now_vn), ("upcoming VN", up_vn)):
            res = data.get("results", [])
            print(f"\n[{label}] kết quả trang 1: {len(res)} | total_results={data.get('total_results')} "
                  f"| total_pages={data.get('total_pages')} | dates={data.get('dates')}")
            if res:
                print("  tên các khóa của 1 phần tử:", sorted(res[0].keys()))
            print("  5 tên mẫu (title | original_title | release_date | popularity):")
            for m in res[:5]:
                print(f"   - {m.get('title')} | {m.get('original_title')} | {m.get('release_date')} | {m.get('popularity')}")
            diff = sum(1 for m in res if m.get("title") != m.get("original_title"))
            has_vi = sum(1 for m in res if VI_CHARS.search(m.get("title") or ""))
            print(f"  title khác original_title: {diff}/{len(res)} | title có ký tự tiếng Việt có dấu: {has_vi}/{len(res)}")
            print("  có trường 'runtime' trong danh sách:", any("runtime" in m for m in res))

        ids_vn = [m["id"] for m in now_vn.get("results", [])]
        ids_any = [m["id"] for m in now_any.get("results", [])]
        print(f"\n[tác dụng của region] now_playing VN: {len(ids_vn)} phim, không region: {len(ids_any)} phim, "
              f"trùng nhau: {len(set(ids_vn) & set(ids_any))} | dates không region: {now_any.get('dates')}")

        sample = [("now_playing", m) for m in now_vn.get("results", [])[:2]] + \
                 [("upcoming", m) for m in up_vn.get("results", [])[:1]]
        print("\n[chi tiết 3 phim, language=vi-VN, append_to_response=release_dates]")
        for src, m in sample:
            d = call("details_%s" % m["id"], "/movie/%s" % m["id"],
                     {"language": "vi-VN", "append_to_response": "release_dates"})
            vn = vn_theatrical_dates(d.get("release_dates"))
            print(f" - id={d.get('id')} [{src}] title={d.get('title')!r} original={d.get('original_title')!r}")
            print(f"     runtime={d.get('runtime')} | status={d.get('status')} | adult={d.get('adult')} | "
                  f"popularity={d.get('popularity')} | vote_count={d.get('vote_count')}")
            print(f"     release_date trong danh sách={m.get('release_date')} | release_date trong chi tiết={d.get('release_date')} "
                  f"| VN theatrical (type,ngày)={vn}")
            ref = vn[0][1] if vn else None
            print("     ngày danh sách khớp ngày chiếu rạp VN sớm nhất:",
                  ("KHÔNG CÓ DỮ LIỆU VN" if ref is None else m.get("release_date") == ref))
    except TmdbError as exc:
        print("LỖI TMDB:", exc)
        print("số lệnh gọi đã gửi:", client.calls)
        return 1

    out_dir = BASE_DIR / "data_raw"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / ("tmdb_probe_%s.json" % datetime.date.today().isoformat())
    out_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    leaked = secret in out_path.read_text(encoding="utf-8")
    print(f"\nđã lưu phản hồi thô: data_raw\\{out_path.name} ({out_path.stat().st_size} byte) | chứa khóa: {'CÓ - LỖI' if leaked else 'không'}")
    print("tổng số lệnh gọi đã gửi:", client.calls)
    return 1 if leaked else 0


if __name__ == "__main__":
    sys.exit(main())

