"""Repository thao tác dữ liệu movies và showtimes trong SQLite.
Chỉ sử dụng thư viện chuẩn: sqlite3, os, datetime, json.

Tuân thủ:
- Tên hiệu lực: override > title_vi > title_original
- Thời lượng hiệu lực: override > runtime_min
- Đồng bộ KHÔNG BAO GIỜ ghi đè: title_override, runtime_override, is_active
- Bảo vệ dữ liệu: kiểm tra liên kết với tickets và incidents trước khi hủy suất.
"""
import os
import sqlite3
from datetime import datetime, timedelta

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")


def get_connection(db_path=None):
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _table_columns(cursor, table):
    return [r[1] for r in cursor.execute(f"PRAGMA table_info({table})")]


def init_movies_tables(db_path=None):
    """Khởi tạo bảng movies và showtimes (idempotent, CREATE TABLE IF NOT EXISTS).

    Nếu phát hiện CSDL cũ (bảng showtimes kiểu cũ có cột movie_name, hoặc còn showtimes_v2)
    thì dừng và yêu cầu chạy công cụ di trú: ai_service/tools/migrate_unify_showtimes.py
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        legacy_cols = _table_columns(cursor, "showtimes")
        has_v2 = bool(_table_columns(cursor, "showtimes_v2"))
        if "movie_name" in legacy_cols or has_v2:
            raise RuntimeError(
                "CSDL còn cấu trúc cũ (showtimes kiểu cũ / showtimes_v2). "
                "Hãy chạy: python tools/migrate_unify_showtimes.py"
            )
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                total_seats INTEGER NOT NULL DEFAULT 136,
                screen_type TEXT NOT NULL DEFAULT '2D Standard',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL CHECK(source IN ('manual', 'tmdb')),
                tmdb_id INTEGER UNIQUE NULL,
                title_vi TEXT NOT NULL,
                title_original TEXT NOT NULL,
                release_date TEXT NOT NULL,
                release_date_source TEXT NOT NULL CHECK(release_date_source IN ('vn_release_dates', 'list_field', 'manual')),
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
            CREATE TABLE IF NOT EXISTS showtimes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                show_id TEXT NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'cancelled')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE RESTRICT,
                UNIQUE (room_id, show_id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_active ON movies(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_tmdb_id ON movies(tmdb_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_showtimes_room_date ON showtimes(room_id, start_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_showtimes_show_id ON showtimes(show_id)")
        conn.commit()
    finally:
        conn.close()


def row_to_movie_dict(row):
    """Quy đổi Row thành dict kèm theo các giá trị hiệu lực (effective values)."""
    if row is None:
        return None
    d = dict(row)
    title_override = d.get("title_override")
    title_vi = d.get("title_vi") or ""
    title_orig = d.get("title_original") or ""
    effective_title = title_override if title_override else (title_vi if title_vi else title_orig)

    runtime_override = d.get("runtime_override")
    runtime_min = d.get("runtime_min") or 0
    effective_runtime = runtime_override if (runtime_override is not None and runtime_override > 0) else runtime_min

    d["title"] = effective_title
    d["effective_title"] = effective_title
    d["effective_runtime"] = effective_runtime
    d["is_active"] = bool(d.get("is_active", 1))
    return d


def get_all_movies(active_only=True, db_path=None):
    """Lấy danh sách phim trong bảng movies."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM movies WHERE is_active = 1 ORDER BY popularity DESC, release_date DESC")
        else:
            cursor.execute("SELECT * FROM movies ORDER BY popularity DESC, release_date DESC")
        return [row_to_movie_dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_movie_by_id(movie_id, db_path=None):
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
        row = cursor.fetchone()
        return row_to_movie_dict(row) if row else None
    finally:
        conn.close()


def upsert_manual_movie(movie_data, db_path=None):
    """Thêm mới hoặc cập nhật phim nguồn thủ công (manual).
    Không bao giờ ghi đè title_override, runtime_override, is_active nếu đã tồn tại."""
    conn = get_connection(db_path)
    now_iso = datetime.now().isoformat(timespec="seconds")
    try:
        cursor = conn.cursor()
        title_orig = movie_data.get("title_original", "").strip()
        cursor.execute("SELECT id, title_override, runtime_override, is_active FROM movies WHERE source = 'manual' AND title_original = ?", (title_orig,))
        existing = cursor.fetchone()

        if existing:
            movie_id = existing["id"]
            cursor.execute("""
                UPDATE movies
                SET title_vi = ?,
                    release_date = ?,
                    release_date_source = ?,
                    runtime_min = ?,
                    poster_path = ?,
                    backdrop_path = ?,
                    popularity = ?,
                    fetched_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                movie_data.get("title_vi", title_orig),
                movie_data.get("release_date", ""),
                movie_data.get("release_date_source", "manual"),
                int(movie_data.get("runtime_min", 120)),
                movie_data.get("poster_path"),
                movie_data.get("backdrop_path"),
                float(movie_data.get("popularity", 0.0)),
                now_iso,
                now_iso,
                movie_id
            ))
            conn.commit()
            return movie_id, "updated"
        else:
            cursor.execute("""
                INSERT INTO movies (
                    source, tmdb_id, title_vi, title_original, release_date,
                    release_date_source, runtime_min, poster_path, backdrop_path,
                    popularity, title_override, runtime_override, is_active,
                    fetched_at, created_at, updated_at
                ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 1, ?, ?, ?)
            """, (
                "manual",
                movie_data.get("title_vi", title_orig),
                title_orig,
                movie_data.get("release_date", ""),
                movie_data.get("release_date_source", "manual"),
                int(movie_data.get("runtime_min", 120)),
                movie_data.get("poster_path"),
                movie_data.get("backdrop_path"),
                float(movie_data.get("popularity", 0.0)),
                now_iso,
                now_iso,
                now_iso
            ))
            conn.commit()
            return cursor.lastrowid, "inserted"
    finally:
        conn.close()


def upsert_tmdb_movie(movie_data, db_path=None):
    """Thêm mới hoặc cập nhật phim từ TMDB theo tmdb_id.
    Không ghi đè title_override, runtime_override, is_active."""
    conn = get_connection(db_path)
    now_iso = datetime.now().isoformat(timespec="seconds")
    try:
        cursor = conn.cursor()
        tmdb_id = int(movie_data["tmdb_id"])
        cursor.execute("SELECT id FROM movies WHERE tmdb_id = ?", (tmdb_id,))
        existing = cursor.fetchone()

        if existing:
            movie_id = existing["id"]
            cursor.execute("""
                UPDATE movies
                SET title_vi = ?,
                    title_original = ?,
                    release_date = ?,
                    release_date_source = ?,
                    runtime_min = ?,
                    poster_path = ?,
                    backdrop_path = ?,
                    popularity = ?,
                    fetched_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                movie_data.get("title_vi", ""),
                movie_data.get("title_original", ""),
                movie_data.get("release_date", ""),
                movie_data.get("release_date_source", "vn_release_dates"),
                int(movie_data.get("runtime_min", 120)),
                movie_data.get("poster_path"),
                movie_data.get("backdrop_path"),
                float(movie_data.get("popularity", 0.0)),
                now_iso,
                now_iso,
                movie_id
            ))
            conn.commit()
            return movie_id, "updated"
        else:
            cursor.execute("""
                INSERT INTO movies (
                    source, tmdb_id, title_vi, title_original, release_date,
                    release_date_source, runtime_min, poster_path, backdrop_path,
                    popularity, title_override, runtime_override, is_active,
                    fetched_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 1, ?, ?, ?)
            """, (
                "tmdb",
                tmdb_id,
                movie_data.get("title_vi", ""),
                movie_data.get("title_original", ""),
                movie_data.get("release_date", ""),
                movie_data.get("release_date_source", "vn_release_dates"),
                int(movie_data.get("runtime_min", 120)),
                movie_data.get("poster_path"),
                movie_data.get("backdrop_path"),
                float(movie_data.get("popularity", 0.0)),
                now_iso,
                now_iso,
                now_iso
            ))
            conn.commit()
            return cursor.lastrowid, "inserted"
    finally:
        conn.close()


def purge_old_tmdb_movies(days=180, dry_run=False, db_path=None):
    """Đánh dấu is_active = 0 (soft-delete) cho các phim TMDB có fetched_at cũ hơn N ngày.
    TUYỆT ĐỐI KHÔNG dùng DELETE.
    Nếu dry_run=True: chỉ đếm số bản ghi bị ảnh hưởng mà không cập nhật DB."""
    conn = get_connection(db_path)
    now_dt = datetime.now()
    threshold = (now_dt - timedelta(days=days)).isoformat(timespec="seconds")
    now_iso = now_dt.isoformat(timespec="seconds")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title_vi, title_original, fetched_at
            FROM movies
            WHERE source = 'tmdb' AND is_active = 1 AND fetched_at < ?
        """, (threshold,))
        candidates = cursor.fetchall()
        count = len(candidates)
        if not dry_run and count > 0:
            cursor.execute("""
                UPDATE movies
                SET is_active = 0, updated_at = ?
                WHERE source = 'tmdb' AND is_active = 1 AND fetched_at < ?
            """, (now_iso, threshold))
            conn.commit()
        return {
            "count": count,
            "threshold": threshold,
            "candidates": [dict(c) for c in candidates]
        }
    finally:
        conn.close()


def check_showtime_has_records(room_id, show_id, db_path=None):
    """Kiểm tra xem suất chiếu có vé bán hoặc sự cố gắn liền hay không.
    Hỗ trợ cả định dạng room1 lẫn seats_config_room1."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        room_variants = (room_id, f"seats_config_{room_id}")

        placeholders = ",".join("?" for _ in room_variants)
        cursor.execute(f"SELECT COUNT(*) FROM tickets WHERE room_id IN ({placeholders}) AND show_id = ?", (*room_variants, show_id))
        ticket_count = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM incidents WHERE room_id IN ({placeholders}) AND show_id = ?", (*room_variants, show_id))
        incident_count = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM alerts WHERE room_id IN ({placeholders}) AND show_id = ?", (*room_variants, show_id))
        alert_count = cursor.fetchone()[0]

        has_data = (ticket_count > 0 or incident_count > 0 or alert_count > 0)
        return {
            "has_records": has_data,
            "tickets": ticket_count,
            "incidents": incident_count,
            "alerts": alert_count
        }
    finally:
        conn.close()


def get_catalog_showtimes(date_str=None, room_id=None, movie_id=None, status="scheduled", db_path=None):
    """Truy vấn danh sách suất chiếu chuẩn hóa từ showtimes kèm thông tin phim."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        query = """
            SELECT s.id, s.room_id, s.movie_id, s.show_id, s.start_at, s.end_at, s.status, s.created_at,
                   m.title_vi, m.title_original, m.title_override, m.runtime_min, m.runtime_override,
                   m.poster_path, m.backdrop_path, m.source
            FROM showtimes s
            JOIN movies m ON s.movie_id = m.id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND s.status = ?"
            params.append(status)
        if room_id:
            query += " AND s.room_id = ?"
            params.append(room_id)
        if movie_id:
            query += " AND s.movie_id = ?"
            params.append(int(movie_id))
        if date_str:
            # start_at lưu ISO: 'yyyy-MM-ddTHH:mm:00+07:00'
            query += " AND substr(s.start_at, 1, 10) = ?"
            params.append(date_str)

        query += " ORDER BY s.start_at ASC, s.room_id ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            title_override = d.get("title_override")
            title_vi = d.get("title_vi") or ""
            title_orig = d.get("title_original") or ""
            m_title = title_override if title_override else (title_vi if title_vi else title_orig)
            d["movie_title"] = m_title
            d["movie_name"] = m_title  # Khớp với UI Mobile App và Web Admin

            room_id = d.get("room_id", "")
            room_num = room_id.replace("room", "")
            d["room_name"] = f"Phòng chiếu số {room_num}" if room_num.isdigit() else room_id
            d["break_minutes"] = 15

            runtime_override = d.get("runtime_override")
            runtime_min = d.get("runtime_min") or 0
            d["duration_minutes"] = runtime_override if (runtime_override is not None and runtime_override > 0) else runtime_min
            d["start_time"] = d["show_id"][11:16] if len(d["show_id"]) >= 16 else ""
            d["end_time"] = d["end_at"][11:16] if len(d["end_at"]) >= 16 else ""
            d["date"] = d["show_id"][:10] if len(d["show_id"]) >= 10 else ""
            results.append(d)
        return results
    finally:
        conn.close()
