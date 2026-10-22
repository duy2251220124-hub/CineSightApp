"""Công cụ dòng lệnh (CLI) sinh lịch suất chiếu mô phỏng cho CineSight.
Sử dụng bộ sinh lịch scheduler.py, chỉ dùng thư viện chuẩn Python.
Mặc định chạy dry-run (chỉ xem thử, không ghi CSDL).
Chỉ ghi CSDL khi có cờ --write.
Tuyệt đối không có cờ --force để tuân thủ quy tắc đóng băng lịch cũ.
"""
import argparse
import datetime
from datetime import date, timedelta
import os
import sqlite3
import sys

# Đảm bảo in tiếng Việt chuẩn trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm thư mục ai_service vào sys.path để import scheduler
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scheduler import (
    DEFAULT_CONFIG,
    TZ_VN,
    SchedulerConfig,
    filter_eligible,
    load_movie_rows,
    minutes_to_hhmm,
    run_for_day,
    to_datetimes,
    validate_table_name,
)

DB_PATH = os.path.join(BASE_DIR, "cinesight.db")

WEEKDAYS_VI = [
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
]


def format_room_name(room_id: str) -> str:
    """Đổi mã phòng thành tên tiếng Việt dễ đọc (room1 -> Phòng 1)."""
    num = room_id.replace("room", "")
    return f"Phòng {num}" if num.isdigit() else room_id


def print_day_detail(day: date, day_schedule: dict, cfg: SchedulerConfig):
    """In chi tiết lịch chiếu từng phòng trong ngày theo định dạng Bước 6.5."""
    weekday_str = WEEKDAYS_VI[day.weekday()]
    print(f"  Ngày {day.isoformat()} ({weekday_str}):")

    movie_stats = {}
    room_stats = {}
    total_shows = 0

    for room_id in cfg.ROOMS:
        shows = day_schedule.get(room_id, [])
        room_name = format_room_name(room_id)
        room_stats[room_id] = len(shows)
        total_shows += len(shows)

        print(f"    {room_name} ({len(shows)} suất):")
        if not shows:
            print("      (Không có suất chiếu)")
            continue

        for s in shows:
            start_str, end_str = to_datetimes(day, s["start_min"], s["end_min"], cfg)
            # Lấy phần HH:MM từ chuỗi ISO
            start_hhmm = start_str[11:16]
            end_hhmm = end_str[11:16]
            runtime = s["runtime"]
            title = s["title"]
            print(f"      {start_hhmm} - {end_hhmm} ({runtime}p) | {title}")

            # Thống kê theo phim
            movie_stats[title] = movie_stats.get(title, 0) + 1

    # Thống kê cuối ngày
    print(f"  Thống kê Ngày {day.isoformat()}:")
    print("    - Theo phim:")
    for title, count in sorted(movie_stats.items(), key=lambda x: -x[1]):
        print(f"      + {title}: {count} suất")
    rooms_summary = ", ".join(f"{r}: {c}" for r, c in room_stats.items())
    print(f"    - Theo phòng: {rooms_summary}")
    print(f"    - Tổng suất trong ngày: {total_shows} suất")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Sinh lịch suất chiếu mô phỏng cho CineSight (showtimes_v2)"
    )
    # Lấy ngày hiện tại theo múi giờ chuẩn VN (UTC+7)
    today_vn = datetime.datetime.now(TZ_VN).date()
    parser.add_argument(
        "--from",
        dest="from_date",
        default=today_vn.isoformat(),
        help="Ngày bắt đầu (YYYY-MM-DD), mặc định: hôm nay giờ VN",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_CONFIG.DEFAULT_DAYS,
        help="Số ngày cần sinh (mặc định: 7)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Ghi vào CSDL thật (nếu không có: chạy dry-run xem thử)",
    )
    parser.add_argument(
        "--table",
        default="showtimes_v2",
        help="Tên bảng đích trong CSDL (mặc định: showtimes_v2)",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Chỉ in dòng tóm tắt, không in chi tiết từng suất",
    )

    args = parser.parse_args()

    try:
        start_date = date.fromisoformat(args.from_date)
    except ValueError:
        print(f"[LỖI] Định dạng ngày --from không hợp lệ: '{args.from_date}'. Cần định dạng YYYY-MM-DD.")
        sys.exit(1)

    if args.days <= 0:
        print(f"[LỖI] Số ngày --days phải lớn hơn 0 (nhận được: {args.days}).")
        sys.exit(1)

    try:
        validate_table_name(args.table)
    except ValueError as e:
        print(f"[LỖI BẢNG CSDL] {e}")
        sys.exit(1)

    cfg = DEFAULT_CONFIG
    mode_label = "[GHI THỰC TẾ]" if args.write else "[DRY-RUN (CHỈ XEM THỬ)]"

    print("=" * 70)
    print(f" CINESIGHT SHOWTIMES GENERATOR {mode_label}")
    print(f" - Bảng đích      : {args.table}")
    print(f" - Ngày bắt đầu   : {start_date} ({WEEKDAYS_VI[start_date.weekday()]})")
    print(f" - Số ngày        : {args.days}")
    print(f" - Danh sách phòng: {', '.join(cfg.ROOMS)} ({len(cfg.ROOMS)} phòng)")
    print(f" - File CSDL      : {DB_PATH}")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"[LỖI] Không tìm thấy file CSDL tại: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        total_generated = 0
        days_processed = 0

        for i in range(args.days):
            current_day = start_date + timedelta(days=i)
            res = run_for_day(
                conn=conn,
                day=current_day,
                rooms=cfg.ROOMS,
                cfg=cfg,
                write=args.write,
                table_name=args.table,
            )

            status = res["status"]
            count = res["count"]
            schedule = res["schedule"]

            if status == "dry":
                room_breakdown = ", ".join(
                    f"{r}: {len(schedule.get(r, []))}" for r in cfg.ROOMS
                )
                unique_movies = len(
                    set(s["movie_id"] for shows in schedule.values() for s in shows)
                )
                print(
                    f"[DRY-RUN] Ngày {current_day.isoformat()}: {count} suất ({room_breakdown}) - {unique_movies} phim tham gia"
                )
                if not args.brief:
                    print_day_detail(current_day, schedule, cfg)
                total_generated += count
                days_processed += 1

            elif status == "written":
                room_breakdown = ", ".join(
                    f"{r}: {len(schedule.get(r, []))}" for r in cfg.ROOMS
                )
                print(f"[ĐÃ GHI]  Ngày {current_day.isoformat()}: {count} suất ({room_breakdown})")
                if not args.brief:
                    print_day_detail(current_day, schedule, cfg)
                total_generated += count
                days_processed += 1

            elif status == "skipped":
                print(
                    f"[BỎ QUA]  Ngày {current_day.isoformat()}: đã có lịch trong CSDL (bảo vệ lịch cũ, đóng băng)"
                )

            elif status == "empty":
                print(
                    f"[TRỐNG]   Ngày {current_day.isoformat()}: 0 phim đủ điều kiện khởi chiếu"
                )

        print("-" * 70)
        action_word = "Đã ghi" if args.write else "Đã mô phỏng"
        print(f"[HOÀN TẤT] {action_word} {total_generated} suất chiếu qua {days_processed}/{args.days} ngày.")
        print("-" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

