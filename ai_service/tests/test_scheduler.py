import datetime
from datetime import date, timedelta
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scheduler
from scheduler import (
    DEFAULT_CONFIG,
    SchedulerConfig,
    build_day_schedule,
    build_room_schedule,
    ceil5,
    filter_eligible,
    minutes_to_hhmm,
    seed_for,
    to_datetimes,
)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.D = date(2026, 10, 20)
        self.cfg = DEFAULT_CONFIG

        # 7 phim giả lập theo quy định
        self.mock_movies = [
            {"id": 1, "title": "Phim 1", "runtime_min": 120, "release_date": (self.D - timedelta(days=5)).isoformat(), "is_active": 1},   # Mới (5 ngày)
            {"id": 2, "title": "Phim 2", "runtime_min": 100, "release_date": (self.D - timedelta(days=60)).isoformat(), "is_active": 1},  # Cũ (60 ngày <= 90)
            {"id": 3, "title": "Phim 3", "runtime_min": 150, "release_date": (self.D - timedelta(days=20)).isoformat(), "is_active": 1},  # Cũ (20 ngày <= 90)
            {"id": 4, "title": "Phim 4", "runtime_min": 90, "release_date": (self.D + timedelta(days=3)).isoformat(), "is_active": 1},    # Chưa chiếu (D+3)
            {"id": 5, "title": "Phim 5", "runtime_min": 30, "release_date": (self.D - timedelta(days=10)).isoformat(), "is_active": 1},   # Runtime < 60p
            {"id": 6, "title": "Phim 6", "runtime_min": 110, "release_date": (self.D - timedelta(days=10)).isoformat(), "is_active": 0},  # is_active = 0
            {"id": 7, "title": "Phim 7", "runtime_min": 115, "release_date": (self.D - timedelta(days=120)).isoformat(), "is_active": 1}, # Quá 90 ngày (D-120)
        ]

    def test_T1_only_eligible_movies_appear(self):
        """T1: Chỉ ID 1, 2, 3 xuất hiện trong lịch; các ID 4, 5, 6, 7 bị loại."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        movie_ids_in_sched = set()
        for room, shows in sched.items():
            for s in shows:
                movie_ids_in_sched.add(s["movie_id"])
        self.assertEqual(movie_ids_in_sched, {1, 2, 3})
        for excluded_id in [4, 5, 6, 7]:
            self.assertNotIn(excluded_id, movie_ids_in_sched)

    def test_T2_no_overlap_and_gap_respected(self):
        """T2: Trong mỗi phòng, suất sau bắt đầu >= suất trước kết thúc + GAP_MIN."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        for room, shows in sched.items():
            for i in range(len(shows) - 1):
                prev_end = shows[i]["end_min"]
                next_start = shows[i + 1]["start_min"]
                self.assertGreaterEqual(
                    next_start,
                    prev_end + self.cfg.GAP_MIN,
                    f"Phòng {room} suất {i+1} vi phạm khoảng nghỉ: start={next_start} < prev_end={prev_end} + {self.cfg.GAP_MIN}"
                )

    def test_T3_all_start_minutes_divisible_by_5(self):
        """T3: Mọi start_min chia hết cho 5."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        for room, shows in sched.items():
            for s in shows:
                self.assertEqual(s["start_min"] % 5, 0, f"Suất {s['show_id']} có start_min {s['start_min']} không chia hết cho 5")

    def test_T4_first_show_and_last_start_bounds(self):
        """T4: Suất đầu của mỗi phòng >= OPEN_MIN + offset; mọi start_min <= LAST_START_MIN."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        for room, shows in sched.items():
            self.assertTrue(len(shows) > 0)
            expected_min_start = ceil5(self.cfg.OPEN_MIN + self.cfg.ROOM_OFFSET_MIN[room])
            self.assertGreaterEqual(shows[0]["start_min"], expected_min_start)
            for s in shows:
                self.assertLessEqual(
                    s["start_min"],
                    self.cfg.LAST_START_MIN,
                    f"Suất {s['show_id']} bắt đầu lúc {s['start_min']} > {self.cfg.LAST_START_MIN}"
                )

    def test_T5_deterministic_generation(self):
        """T5: Sinh 2 lần cùng đầu vào cho kết quả GIỐNG HỆT (so sánh cả danh sách)."""
        sched1 = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        sched2 = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        self.assertEqual(sched1, sched2)

    def test_T6_rooms_have_staggered_starts(self):
        """T6: Các phòng có giờ suất đầu khác nhau theo cấu hình offset."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        first_starts = [sched[room][0]["start_min"] for room in self.cfg.ROOMS]
        # Tất cả các phòng đều phải có giờ suất đầu khác nhau
        self.assertEqual(len(first_starts), len(set(first_starts)))

    def test_T7_empty_eligible_produces_empty_schedule(self):
        """T7: 0 phim đủ điều kiện thì lịch rỗng, không ném ngoại lệ."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, [], self.cfg)
        for room in self.cfg.ROOMS:
            self.assertEqual(sched[room], [])

    def test_T8_single_eligible_movie_succeeds(self):
        """T8: Đúng 1 phim đủ điều kiện thì vẫn sinh được lịch (phim đó lặp lại), không lỗi."""
        single_movie = [self.mock_movies[0]]  # Phim 1 duy nhất
        sched = build_day_schedule(self.D, self.cfg.ROOMS, single_movie, self.cfg)
        for room in self.cfg.ROOMS:
            shows = sched[room]
            self.assertGreater(len(shows), 0)
            for s in shows:
                self.assertEqual(s["movie_id"], 1)

    def test_T9_disallow_past_midnight_bounds_end_min(self):
        """T9: Nếu ALLOW_PAST_MIDNIGHT=False thì mọi end_min <= 1440."""
        cfg_no_midnight = SchedulerConfig(
            ROOMS=self.cfg.ROOMS,
            OPEN_MIN=self.cfg.OPEN_MIN,
            ROOM_OFFSET_MIN=self.cfg.ROOM_OFFSET_MIN,
            LAST_START_MIN=self.cfg.LAST_START_MIN,
            GAP_MIN=self.cfg.GAP_MIN,
            ALLOW_PAST_MIDNIGHT=False,
        )
        sched = build_day_schedule(self.D, cfg_no_midnight.ROOMS, self.mock_movies, cfg_no_midnight)
        for room, shows in sched.items():
            for s in shows:
                self.assertLessEqual(
                    s["end_min"],
                    1440,
                    f"Suất {s['show_id']} phòng {room} kết thúc sau nửa đêm: end_min={s['end_min']} > 1440"
                )

    def test_T10_show_id_regex_and_date_match(self):
        r"""T10: show_id đúng định dạng: khớp regex ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$ và phần ngày = D."""
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        for room, shows in sched.items():
            for s in shows:
                show_id = s["show_id"]
                self.assertTrue(pattern.match(show_id), f"show_id không khớp định dạng: {show_id}")
                self.assertTrue(show_id.startswith(self.D.isoformat()), f"show_id không bắt đầu bằng {self.D.isoformat()}: {show_id}")

    def test_T11_to_datetimes_offset_and_cross_midnight(self):
        """T11: to_datetimes: kết quả kết thúc bằng +07:00; với start_min=1350 và runtime 150 thì end_at là ngày D+1, 01:00."""
        start_iso, end_iso = to_datetimes(self.D, 1350, 1350 + 150, self.cfg)
        self.assertTrue(start_iso.endswith("+07:00"))
        self.assertTrue(end_iso.endswith("+07:00"))
        self.assertEqual(start_iso, "2026-10-20T22:30:00+07:00")
        self.assertEqual(end_iso, "2026-10-21T01:00:00+07:00")

    def test_T12_different_days_produce_different_schedules(self):
        """T12: Ngày khác (D+1) cho lịch KHÁC ngày D ít nhất ở một phòng; cùng ngày D chạy lại thì giống."""
        D_next = self.D + timedelta(days=1)
        sched_D = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        sched_D_next = build_day_schedule(D_next, self.cfg.ROOMS, self.mock_movies, self.cfg)
        
        # So sánh cấu trúc danh sách phim giữa 2 ngày: phải có ít nhất 1 phòng có thứ tự phim khác nhau
        movies_D = {room: [s["movie_id"] for s in sched_D[room]] for room in self.cfg.ROOMS}
        movies_D_next = {room: [s["movie_id"] for s in sched_D_next[room]] for room in self.cfg.ROOMS}
        self.assertNotEqual(movies_D, movies_D_next)

    def test_T13_no_consecutive_same_movie_when_multiple_eligible(self):
        """T13: Hai suất liên tiếp trong cùng phòng không cùng 1 phim khi có từ 2 phim đủ điều kiện trở lên."""
        sched = build_day_schedule(self.D, self.cfg.ROOMS, self.mock_movies, self.cfg)
        for room, shows in sched.items():
            for i in range(len(shows) - 1):
                cur_movie = shows[i]["movie_id"]
                next_movie = shows[i + 1]["movie_id"]
                self.assertNotEqual(
                    cur_movie,
                    next_movie,
                    f"Phòng {room} có 2 suất liên tiếp cùng chiếu phim #{cur_movie} lúc {shows[i]['show_id']} và {shows[i+1]['show_id']}"
                )


if __name__ == "__main__":
    unittest.main()
