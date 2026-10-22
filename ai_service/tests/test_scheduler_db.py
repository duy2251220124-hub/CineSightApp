import datetime
from datetime import date, timedelta
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler import (
    DEFAULT_CONFIG,
    SchedulerConfig,
    build_day_schedule,
    day_has_showtimes,
    filter_eligible,
    load_movie_rows,
    persist_day,
    run_for_day,
    validate_table_name,
)


def create_in_memory_db():
    """Tạo CSDL SQLite trong RAM (:memory:) với schema chuẩn 100% của movies và showtimes_v2."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            tmdb_id INTEGER UNIQUE NULL,
            title_vi TEXT NOT NULL,
            title_original TEXT NOT NULL,
            release_date TEXT NOT NULL,
            release_date_source TEXT NOT NULL,
            runtime_min INTEGER NOT NULL,
            poster_path TEXT NULL,
            backdrop_path TEXT NULL,
            popularity REAL DEFAULT 0.0,
            title_override TEXT NULL,
            runtime_override INTEGER NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            fetched_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE showtimes_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            show_id TEXT NOT NULL,
            start_at TEXT NOT NULL,
            end_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            created_at TEXT NOT NULL,
            UNIQUE(room_id, show_id)
        )
    """)
    conn.commit()
    return conn


class TestSchedulerDB(unittest.TestCase):
    def setUp(self):
        self.conn = create_in_memory_db()
        self.D = date(2026, 10, 20)
        self.cfg = DEFAULT_CONFIG

        # Chèn 3 phim mẫu đủ điều kiện vào bảng movies
        cursor = self.conn.cursor()
        movies_data = [
            ("manual", None, "Phim Mới A", "New Movie A", (self.D - timedelta(days=5)).isoformat(), "manual", 120, None, None, 10.0, None, None, 1, "2026-10-19", "2026-10-19", "2026-10-19"),
            ("manual", None, "Phim Vừa B", "Mid Movie B", (self.D - timedelta(days=30)).isoformat(), "manual", 100, None, None, 8.0, None, None, 1, "2026-10-19", "2026-10-19", "2026-10-19"),
            ("manual", None, "Phim Cũ C", "Old Movie C", (self.D - timedelta(days=60)).isoformat(), "manual", 130, None, None, 5.0, None, None, 1, "2026-10-19", "2026-10-19", "2026-10-19"),
        ]
        cursor.executemany("""
            INSERT INTO movies (
                source, tmdb_id, title_vi, title_original, release_date,
                release_date_source, runtime_min, poster_path, backdrop_path,
                popularity, title_override, runtime_override, is_active,
                fetched_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, movies_data)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_D1_persist_and_count_and_timezone(self):
        """D1: persist rồi đếm: số dòng bằng số suất đã sinh; mỗi dòng có start_at kết thúc +07:00."""
        movies = load_movie_rows(self.conn)
        eligible = filter_eligible(movies, self.D, self.cfg)
        sched = build_day_schedule(self.D, self.cfg.ROOMS, movies, self.cfg)

        total_shows = sum(len(shows) for shows in sched.values())
        created_at_iso = datetime.datetime.now(self.cfg.TZ).isoformat(timespec="seconds")
        saved_count = persist_day(self.conn, self.D, sched, created_at_iso, cfg=self.cfg)

        self.assertEqual(saved_count, total_shows)

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM showtimes_v2")
        db_count = cursor.fetchone()[0]
        self.assertEqual(db_count, total_shows)

        cursor.execute("SELECT start_at, end_at FROM showtimes_v2")
        rows = cursor.fetchall()
        for start_at, end_at in rows:
            self.assertTrue(start_at.endswith("+07:00"), f"start_at {start_at} thiếu +07:00")
            self.assertTrue(end_at.endswith("+07:00"), f"end_at {end_at} thiếu +07:00")

    def test_D2_freeze_and_idempotent_skip(self):
        """D2: ĐÓNG BĂNG: day_has_showtimes True sau khi ghi; run_for_day lần 2 trả 'skipped' và số dòng KHÔNG đổi."""
        # Lần 1: ghi lịch thành công
        res1 = run_for_day(self.conn, self.D, self.cfg.ROOMS, cfg=self.cfg, write=True)
        self.assertEqual(res1["status"], "written")
        self.assertGreater(res1["count"], 0)

        # Kiểm tra day_has_showtimes
        self.assertTrue(day_has_showtimes(self.conn, self.D))

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM showtimes_v2")
        count_after_first = cursor.fetchone()[0]

        # Lần 2: chạy lại trên cùng ngày -> phải trả 'skipped' và không thêm dòng nào
        res2 = run_for_day(self.conn, self.D, self.cfg.ROOMS, cfg=self.cfg, write=True)
        self.assertEqual(res2["status"], "skipped")
        self.assertEqual(res2["count"], 0)

        cursor.execute("SELECT COUNT(*) FROM showtimes_v2")
        count_after_second = cursor.fetchone()[0]
        self.assertEqual(count_after_second, count_after_first)

    def test_D3_rollback_on_error(self):
        """D3: rollback: cố ý tạo lỗi giữa chừng thì sau lỗi số dòng của ngày đó = số dòng ban đầu."""
        cursor = self.conn.cursor()
        # Chèn trước 1 suất chiếu cố ý gây trùng khóa UNIQUE(room_id, show_id)
        duplicate_show_id = f"{self.D.isoformat()}T08:30"
        cursor.execute("""
            INSERT INTO showtimes_v2 (room_id, movie_id, show_id, start_at, end_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("room1", 1, duplicate_show_id, f"{duplicate_show_id}:00+07:00", f"{self.D.isoformat()}T10:30:00+07:00", "scheduled", "2026-10-19T00:00:00+07:00"))
        self.conn.commit()

        initial_count = cursor.execute("SELECT COUNT(*) FROM showtimes_v2").fetchone()[0]
        self.assertEqual(initial_count, 1)

        movies = load_movie_rows(self.conn)
        sched = build_day_schedule(self.D, self.cfg.ROOMS, movies, self.cfg)

        # persist_day sẽ cố chèn suất room1 lúc 08:30 và gây UNIQUE violation
        with self.assertRaises(Exception):
            persist_day(self.conn, self.D, sched, "2026-10-19T00:00:00+07:00", cfg=self.cfg)

        # Số dòng trong DB phải giữ nguyên = initial_count (1), không có dòng dở dang nào lọt vào
        current_count = cursor.execute("SELECT COUNT(*) FROM showtimes_v2").fetchone()[0]
        self.assertEqual(current_count, initial_count)

    def test_D4_movies_table_untouched(self):
        """D4: Không động vào bảng movies (so sánh nội dung trước/sau)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM movies ORDER BY id")
        before_movies = cursor.fetchall()

        # Thực thi sinh và ghi lịch
        run_for_day(self.conn, self.D, self.cfg.ROOMS, cfg=self.cfg, write=True)

        cursor.execute("SELECT * FROM movies ORDER BY id")
        after_movies = cursor.fetchall()

        self.assertEqual(before_movies, after_movies)

    def test_run_for_day_all_four_states(self):
        """Kiểm tra đủ 4 trạng thái của run_for_day: 'dry', 'written', 'skipped', 'empty'."""
        # 1. 'dry': write=False
        res_dry = run_for_day(self.conn, self.D, self.cfg.ROOMS, cfg=self.cfg, write=False)
        self.assertEqual(res_dry["status"], "dry")
        self.assertGreater(res_dry["count"], 0)
        self.assertEqual(day_has_showtimes(self.conn, self.D), False)

        # 2. 'empty': khi không có phim đủ điều kiện
        future_day = self.D + timedelta(days=300)  # Cả 3 phim đều quá 90 ngày
        res_empty = run_for_day(self.conn, future_day, self.cfg.ROOMS, cfg=self.cfg, write=True)
        self.assertEqual(res_empty["status"], "empty")
        self.assertEqual(res_empty["count"], 0)

        # 3. 'written': khi ghi thật
        res_written = run_for_day(self.conn, self.D, self.cfg.ROOMS, cfg=self.cfg, write=True)
        self.assertEqual(res_written["status"], "written")
        self.assertGreater(res_written["count"], 0)

        # 4. 'skipped': khi ngày đã có lịch
        res_skipped = run_for_day(self.conn, self.D, self.cfg.ROOMS, cfg=self.cfg, write=True)
        self.assertEqual(res_skipped["status"], "skipped")
        self.assertEqual(res_skipped["count"], 0)

    def test_D5_disallowed_table_name_rejected(self):
        """D5: Kiểm tra chỉ các bảng trong danh sách cho phép mới được chấp nhận; bảng lạ bị từ chối rõ ràng."""
        # 1. Bảng hợp lệ không ném lỗi
        self.assertEqual(validate_table_name("showtimes"), "showtimes")
        self.assertEqual(validate_table_name("showtimes_v2"), "showtimes_v2")

        # 2. Bảng lạ hoặc SQL injection bị ném ValueError
        invalid_tables = [
            "users",
            "showtimes; DROP TABLE movies;--",
            "showtimes_v3",
            "",
            "admin",
        ]
        for tbl in invalid_tables:
            with self.assertRaises(ValueError):
                validate_table_name(tbl)
            with self.assertRaises(ValueError):
                day_has_showtimes(self.conn, self.D, table_name=tbl)
            with self.assertRaises(ValueError):
                persist_day(self.conn, self.D, {}, "2026-10-19T00:00:00+07:00", table_name=tbl)
            with self.assertRaises(ValueError):
                run_for_day(self.conn, self.D, self.cfg.ROOMS, write=False, table_name=tbl)



if __name__ == "__main__":
    unittest.main()

