"""Công cụ kiểm thử và xác thực độc lập 11 quy tắc lập lịch suất chiếu CineSight.
Chạy mô phỏng (dry-run, không ghi CSDL) trên 7 ngày liên tiếp từ ngày hiện tại.
Đảm bảo in rõ PASS/FAIL cho từng quy tắc theo yêu cầu.
"""
import datetime
from datetime import date, timedelta
import os
import re
import sqlite3
import sys

# Đảm bảo in tiếng Việt chuẩn trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm thư mục ai_service vào sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scheduler import (
    DEFAULT_CONFIG,
    TZ_VN,
    SchedulerConfig,
    build_day_schedule,
    ceil5,
    filter_eligible,
    load_movie_rows,
    normalize_movie,
)

DB_PATH = os.path.join(BASE_DIR, "cinesight.db")
SHOW_ID_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")


class ShowtimeValidator:
    def __init__(self, cfg: SchedulerConfig = None):
        self.cfg = cfg or DEFAULT_CONFIG
        self.rules = {
            "R01_NO_OVERLAP": {
                "name": "Không chồng giờ trong cùng một phòng",
                "passed": True,
                "errors": [],
            },
            "R02_GAP_MIN": {
                "name": f"Thời gian nghỉ giữa 2 suất liên tiếp >= {self.cfg.GAP_MIN} phút",
                "passed": True,
                "errors": [],
            },
            "R03_START_DIV_5": {
                "name": "Giờ bắt đầu mọi suất phải chia hết cho 5 phút",
                "passed": True,
                "errors": [],
            },
            "R04_RUNTIME_MATCH": {
                "name": "Thời lượng suất chiếu (end - start) đúng bằng runtime phim",
                "passed": True,
                "errors": [],
            },
            "R05_LAST_START": {
                "name": f"Giờ bắt đầu muộn nhất <= 22:30 ({self.cfg.LAST_START_MIN} phút)",
                "passed": True,
                "errors": [],
            },
            "R06_ELIGIBLE_MOVIES": {
                "name": f"Mọi phim đều đủ điều kiện (active=1, runtime {self.cfg.MIN_RUNTIME}-{self.cfg.MAX_RUNTIME}p, khởi chiếu <= ngày <= khởi chiếu + {self.cfg.WINDOW_DAYS} ngày)",
                "passed": True,
                "errors": [],
            },
            "R07_FIRST_SHOW_START": {
                "name": "Suất đầu mỗi phòng = giờ mở cửa + offset phòng (làm tròn lên bội 5)",
                "passed": True,
                "errors": [],
            },
            "R08_NO_CONSECUTIVE_SAME": {
                "name": "Không có 2 suất liên tiếp chiếu cùng 1 phim trong cùng phòng (khi có >= 2 phim)",
                "passed": True,
                "errors": [],
            },
            "R09_DETERMINISTIC": {
                "name": "Tính xác định: sinh lại lần 2 ra kết quả 100% giống hệt lần 1",
                "passed": True,
                "errors": [],
            },
            "R10_SHOW_COUNT_BOUNDS": {
                "name": "Số suất mỗi phòng mỗi ngày nằm trong khoảng từ 5 đến 9 suất",
                "passed": True,
                "errors": [],
            },
            "R11_SHOW_ID_AND_UNIQUE": {
                "name": "show_id đúng định dạng YYYY-MM-DDTHH:mm và không trùng cặp (room_id, show_id)",
                "passed": True,
                "errors": [],
            },
        }
        self.total_days = 0
        self.total_shows = 0

    def fail_rule(self, code: str, msg: str):
        self.rules[code]["passed"] = False
        if len(self.rules[code]["errors"]) < 5:  # Giới hạn in 5 lỗi đầu để không tràn màn hình
            self.rules[code]["errors"].append(msg)

    def validate_7_days(self, start_date: date, movies_rows: list):
        """Thực thi kiểm tra toàn bộ 7 ngày."""
        movie_dict = {m["id"]: m for m in [normalize_movie(r) for r in movies_rows]}

        for day_idx in range(7):
            current_day = start_date + timedelta(days=day_idx)
            self.total_days += 1

            # Lấy danh sách phim đủ điều kiện cho ngày hiện tại
            eligible = filter_eligible(movies_rows, current_day, self.cfg)
            eligible_ids = set(m["id"] for m in eligible)

            # Lần sinh 1
            schedule_1 = build_day_schedule(current_day, self.cfg.ROOMS, movies_rows, self.cfg)
            # Lần sinh 2 (để kiểm tra tính xác định deterministic)
            schedule_2 = build_day_schedule(current_day, self.cfg.ROOMS, movies_rows, self.cfg)

            # Kiểm tra R09: Tính xác định
            if schedule_1 != schedule_2:
                self.fail_rule("R09_DETERMINISTIC", f"Ngày {current_day}: Lần 2 khác lần 1!")

            seen_room_show = set()

            for room_id in self.cfg.ROOMS:
                shows = schedule_1.get(room_id, [])
                self.total_shows += len(shows)

                # Kiểm tra R10: Số suất nằm trong [5, 9] (nếu có phim đủ điều kiện)
                if eligible and not (5 <= len(shows) <= 9):
                    self.fail_rule(
                        "R10_SHOW_COUNT_BOUNDS",
                        f"Ngày {current_day}, {room_id}: Có {len(shows)} suất (ngoài khoảng 5-9)",
                    )

                if not shows:
                    continue

                # Kiểm tra R07: Suất đầu tiên của phòng
                expected_first_start = ceil5(self.cfg.OPEN_MIN + self.cfg.ROOM_OFFSET_MIN[room_id])
                if shows[0]["start_min"] != expected_first_start:
                    self.fail_rule(
                        "R07_FIRST_SHOW_START",
                        f"Ngày {current_day}, {room_id}: Suất đầu là {shows[0]['start_min']}p, kỳ vọng {expected_first_start}p",
                    )

                prev_show = None
                for s in shows:
                    s_id = s["show_id"]
                    m_id = s["movie_id"]
                    runtime = s["runtime"]
                    start_min = s["start_min"]
                    end_min = s["end_min"]

                    # Kiểm tra R11: Định dạng show_id & trùng lặp
                    if not SHOW_ID_REGEX.match(s_id):
                        self.fail_rule("R11_SHOW_ID_AND_UNIQUE", f"show_id không khớp regex: '{s_id}'")
                    if not s_id.startswith(current_day.isoformat()):
                        self.fail_rule("R11_SHOW_ID_AND_UNIQUE", f"show_id '{s_id}' không khớp ngày {current_day}")
                    pair = (room_id, s_id)
                    if pair in seen_room_show:
                        self.fail_rule("R11_SHOW_ID_AND_UNIQUE", f"Trùng lặp suất ({room_id}, {s_id})")
                    seen_room_show.add(pair)

                    # Kiểm tra R03: start_min chia hết cho 5
                    if start_min % 5 != 0:
                        self.fail_rule("R03_START_DIV_5", f"{s_id} tại {room_id}: start_min={start_min} không chia hết cho 5")

                    # Kiểm tra R04: end - start == runtime
                    if (end_min - start_min) != runtime:
                        self.fail_rule("R04_RUNTIME_MATCH", f"{s_id}: end-start ({end_min - start_min}) != runtime ({runtime})")

                    # Kiểm tra R05: start_min <= 1350 (22:30)
                    if start_min > self.cfg.LAST_START_MIN:
                        self.fail_rule("R05_LAST_START", f"{s_id}: Bắt đầu lúc {start_min}p > {self.cfg.LAST_START_MIN}p (22:30)")

                    # Kiểm tra R06: Mọi phim phải đủ điều kiện
                    if m_id not in eligible_ids:
                        self.fail_rule("R06_ELIGIBLE_MOVIES", f"{s_id}: Phim #{m_id} không nằm trong danh sách đủ điều kiện của ngày {current_day}")

                    # Kiểm tra tương quan với suất liền trước trong phòng
                    if prev_show is not None:
                        # Kiểm tra R01: Không chồng giờ
                        if start_min < prev_show["end_min"]:
                            self.fail_rule("R01_NO_OVERLAP", f"Chồng giờ tại {room_id}: suất sau bắt đầu {start_min}p < suất trước kết thúc {prev_show['end_min']}p")

                        # Kiểm tra R02: Nghỉ giữa 2 suất >= GAP_MIN
                        gap = start_min - prev_show["end_min"]
                        if gap < self.cfg.GAP_MIN:
                            self.fail_rule("R02_GAP_MIN", f"Thời gian nghỉ giữa 2 suất tại {room_id} là {gap}p < {self.cfg.GAP_MIN}p")

                        # Kiểm tra R08: Không 2 suất liên tiếp cùng phim khi có >= 2 phim
                        if len(eligible) >= 2 and m_id == prev_show["movie_id"]:
                            self.fail_rule("R08_NO_CONSECUTIVE_SAME", f"Hai suất liên tiếp chiếu cùng phim #{m_id} tại {room_id}")

                    prev_show = s

    def print_report(self):
        print("=" * 80)
        print(" BÁO CÁO KIỂM ĐỊNH TỰ ĐỘNG 11 QUY TẮC LẬP LỊCH CHIẾU (VALIDATOR REPORT)")
        print(f" - Tổng số ngày kiểm định : {self.total_days} ngày")
        print(f" - Tổng số suất đã thẩm tra: {self.total_shows} suất")
        print("=" * 80)
        print(f"{'MÃ LUẬT':<25} | {'TRẠNG THÁI':<8} | {'NỘI DUNG QUY TẮC'}")
        print("-" * 80)

        all_passed = True
        for code, info in self.rules.items():
            status_str = "[PASS]" if info["passed"] else "[FAIL]"
            if not info["passed"]:
                all_passed = False
            print(f"{code:<25} | {status_str:<8} | {info['name']}")
            if not info["passed"]:
                for err in info["errors"]:
                    print(f"   => LỖI: {err}")

        print("=" * 80)
        if all_passed:
            print("[KẾT LUẬN TOÀN DIỆN]: TẤT CẢ 11/11 QUY TẮC ĐẠT CHUẨN 100% (PASS)")
        else:
            print("[KẾT LUẬN TOÀN DIỆN]: CÓ QUY TẮC KHÔNG ĐẠT (FAIL)")
        print("=" * 80)
        return all_passed


def main():
    if not os.path.exists(DB_PATH):
        print(f"[LỖI] Không tìm thấy file CSDL: {DB_PATH}")
        sys.exit(1)

    today_vn = datetime.datetime.now(TZ_VN).date()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        movies = load_movie_rows(conn)
    finally:
        conn.close()

    print(f"[KHỞI ĐỘNG] Đọc {len(movies)} phim từ CSDL. Bắt đầu thẩm định 7 ngày kể từ {today_vn}...")
    validator = ShowtimeValidator(DEFAULT_CONFIG)
    validator.validate_7_days(today_vn, movies)
    success = validator.print_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

