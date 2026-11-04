import sqlite3
import os
import datetime
from security import hash_password, verify_password

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

_TZ_VN = datetime.timezone(datetime.timedelta(hours=7))

# Phải khớp với SHIFTS trong main.py (code: ca_sang, ca_chieu, ca_toi, ca_dem)
SHIFT_LABELS = {
    "ca_sang": "Ca sáng",
    "ca_chieu": "Ca chiều",
    "ca_toi": "Ca tối",
    "ca_dem": "Ca đêm",
}


def get_dynamic_shift(role: str = None, now: datetime.datetime = None) -> tuple[str, str]:
    """Tính toán ca làm việc động dựa trên thời điểm đăng nhập/thao tác (Giờ Việt Nam UTC+7):
    - Nhân viên (Soát vé / Staff):
        + 07:30 - 13:00: Ca sáng (07:30 - 13:00) [ca_sang]
        + 13:00 - 16:00: Ca chiều (13:00 - 16:00) [ca_chieu]
        + 16:00 - 23:00: Ca tối (16:00 - 23:00) [ca_toi]
        + 23:00 - 07:30: Ca đêm (23:00 - 07:30) [ca_dem]
    - Quản lý (Manager / Admin):
        + 07:30 - 16:00: Ca sáng (07:30 - 16:00) [ca_sang]
        + 16:00 - 24:00: Ca tối (16:30 - 24:00) [ca_toi]
        + 00:00 - 07:30: Ca đêm (00:00 - 07:30) [ca_dem]
    """
    if now is None:
        now = datetime.datetime.now(_TZ_VN)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_TZ_VN)
    else:
        now = now.astimezone(_TZ_VN)

    minute_of_day = now.hour * 60 + now.minute
    is_manager = str(role or "").strip().lower() in ("quản lý", "quan ly", "manager", "admin")

    if is_manager:
        if 450 <= minute_of_day < 960:
            return "ca_sang", "Ca sáng (07:30 - 16:00)"
        elif 960 <= minute_of_day < 1440:
            return "ca_toi", "Ca tối (16:30 - 24:00)"
        else:
            return "ca_dem", "Ca đêm (00:00 - 07:30)"
    else:
        if 450 <= minute_of_day < 780:
            return "ca_sang", "Ca sáng (07:30 - 13:00)"
        elif 780 <= minute_of_day < 960:
            return "ca_chieu", "Ca chiều (13:00 - 16:00)"
        elif 960 <= minute_of_day < 1380:
            return "ca_toi", "Ca tối (16:00 - 23:00)"
        else:
            return "ca_dem", "Ca đêm (23:00 - 07:30)"



def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _normalize_room_id(room_id: str) -> str:
    if not room_id:
        return None
    cleaned = str(room_id).replace("seats_config_", "").strip()
    return cleaned if cleaned else None


def showtime_exists(room_id: str, show_id: str) -> bool:
    """Kiểm tra (room_id, show_id) có thực sự tồn tại trong bảng showtimes (status='scheduled') hay không."""
    clean_room = _normalize_room_id(room_id)
    if not clean_room or not show_id:
        return False
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM showtimes WHERE room_id = ? AND show_id = ? AND status = 'scheduled'",
            (clean_room, str(show_id).strip()),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def _require_showtime_exists(cursor, room_id: str, show_id: str) -> str:
    """Điểm 4A: Từ chối mọi thao tác tạo vé / cảnh báo / log AI cho suất chiếu không có trong lịch."""
    clean_room = _normalize_room_id(room_id)
    if not clean_room or not show_id:
        raise ValueError("Thiếu mã phòng chiếu (room_id) hoặc mã suất chiếu (show_id).")
    row = cursor.execute(
        "SELECT 1 FROM showtimes WHERE room_id = ? AND show_id = ? AND status = 'scheduled'",
        (clean_room, str(show_id).strip()),
    ).fetchone()
    if not row:
        raise ValueError(
            f"Suất chiếu '{show_id}' tại phòng '{clean_room}' không tồn tại trong lịch chiếu."
        )
    return clean_room


def init_db():
    conn = _connect()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

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
    for idx in range(1, 5):
        cursor.execute(
            "INSERT OR IGNORE INTO rooms (id, name, total_seats, screen_type, is_active, created_at) VALUES (?, ?, 136, '2D Standard', 1, ?)",
            (f"room{idx}", f"Phòng chiếu {idx}", now_iso),
        )

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            room_id TEXT NOT NULL,
            show_id TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            seat_id TEXT NOT NULL,
            PRIMARY KEY (room_id, show_id, ticket_id),
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            show_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            seat_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            role TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            shift TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            last_seen_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'shift' not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN shift TEXT NULL")
    # Vấn đề 6: Ngưng hoạt động mềm (soft-deactivate) và dấu vết hoạt động gần nhất
    if 'is_active' not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
    if 'last_seen_at' not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN last_seen_at TEXT NULL")

    # Làm sạch mã ca cũ không hợp lệ (ví dụ 'morning' -> NULL)
    cursor.execute(
        "UPDATE employees SET shift = NULL WHERE shift IS NOT NULL AND shift NOT IN ('ca_sang', 'ca_chieu', 'ca_toi', 'ca_dem')"
    )

    # Điểm 3: Không đặt mật khẩu chữ thường cứng trong mã nguồn.
    # Chỉ khởi tạo admin từ biến môi trường CINESIGHT_ADMIN_PASSWORD nếu CSDL hoàn toàn trống.
    init_admin_pw = os.environ.get("CINESIGHT_ADMIN_PASSWORD", "").strip()
    if init_admin_pw:
        cursor.execute(
            """
            INSERT OR IGNORE INTO employees (id, username, password, name, role, created_at, shift)
            VALUES (1, 'admin', ?, 'Quản trị viên', 'Quản lý', ?, NULL)
            """,
            (hash_password(init_admin_pw), now_iso),
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            room_id TEXT NULL,
            show_id TEXT NULL,
            seat_ids TEXT,
            reporter_id INTEGER NULL,
            reporter_shift TEXT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'resolved')),
            resolved_by_id INTEGER NULL,
            resolved_at TEXT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
            FOREIGN KEY (reporter_id) REFERENCES employees(id) ON DELETE SET NULL,
            FOREIGN KEY (resolved_by_id) REFERENCES employees(id) ON DELETE SET NULL
        )
    """)
    inc_cols = [row[1] for row in cursor.execute("PRAGMA table_info(incidents)").fetchall()]
    if "reporter_shift" not in inc_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN reporter_shift TEXT NULL")
    if "image_path" not in inc_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN image_path TEXT NULL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_inference_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            show_id TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            image_width INTEGER NOT NULL,
            image_height INTEGER NOT NULL,
            total_seats INTEGER NOT NULL,
            booked_tickets_count INTEGER NOT NULL,
            detected_heads_count INTEGER NOT NULL,
            mapped_seats_count INTEGER NOT NULL,
            illegal_count INTEGER NOT NULL,
            missing_count INTEGER NOT NULL,
            over_capacity BOOLEAN NOT NULL DEFAULT 0,
            inference_time_ms REAL NOT NULL,
            yolo_time_ms REAL NULL,
            mapping_time_ms REAL NULL,
            trigger_source TEXT NOT NULL DEFAULT 'MANUAL',
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
        )
    """)
    log_cols = [row[1] for row in cursor.execute("PRAGMA table_info(ai_inference_logs)").fetchall()]
    if "yolo_time_ms" not in log_cols:
        cursor.execute("ALTER TABLE ai_inference_logs ADD COLUMN yolo_time_ms REAL NULL")
    if "mapping_time_ms" not in log_cols:
        cursor.execute("ALTER TABLE ai_inference_logs ADD COLUMN mapping_time_ms REAL NULL")
    if "trigger_source" not in log_cols:
        cursor.execute("ALTER TABLE ai_inference_logs ADD COLUMN trigger_source TEXT NOT NULL DEFAULT 'MANUAL'")

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_ai_logs_room_show ON ai_inference_logs(room_id, show_id)"
    )

    # Insert default config if not exists
    cursor.execute("INSERT OR IGNORE INTO configs (key, value) VALUES ('capacity_threshold', '0')")
    conn.commit()
    conn.close()

def save_tickets(room_id: str, show_id: str, tickets: list):
    conn = _connect()
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        if tickets:
            cursor.executemany(
                "INSERT OR IGNORE INTO tickets (room_id, show_id, ticket_id, seat_id) VALUES (?, ?, ?, ?)",
                [(clean_room, show_id, t['ticket'], t['seat']) for t in tickets]
            )
        conn.commit()
    finally:
        conn.close()

def get_seats(room_id: str, show_id: str) -> set:
    clean_room = _normalize_room_id(room_id) or room_id
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM tickets WHERE room_id = ? AND show_id = ?", (clean_room, show_id))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def get_tickets_list(room_id: str, show_id: str = None):
    clean_room = _normalize_room_id(room_id) or room_id
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if show_id and show_id not in ("undefined", "null", ""):
        cursor.execute("SELECT * FROM tickets WHERE room_id = ? AND show_id = ?", (clean_room, show_id))
    else:
        cursor.execute("SELECT * FROM tickets WHERE room_id = ?", (clean_room,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_tickets(room_id: str = None, show_id: str = None):
    clean_room = _normalize_room_id(room_id)
    conn = _connect()
    cursor = conn.cursor()
    if clean_room and show_id and str(show_id) not in ('undefined', 'null', ''):
        cursor.execute('DELETE FROM tickets WHERE room_id = ? AND show_id = ?', (clean_room, show_id))
    elif clean_room and str(clean_room) not in ('undefined', 'null', ''):
        cursor.execute('DELETE FROM tickets WHERE room_id = ?', (clean_room,))
    else:
        cursor.execute('DELETE FROM tickets')
    conn.commit()
    conn.close()

def clear_alerts(room_id: str = None, show_id: str = None):
    clean_room = _normalize_room_id(room_id)
    conn = _connect()
    cursor = conn.cursor()
    if clean_room and show_id and str(show_id) not in ('undefined', 'null', ''):
        cursor.execute('DELETE FROM alerts WHERE room_id = ? AND show_id = ?', (clean_room, show_id))
    elif clean_room and str(clean_room) not in ('undefined', 'null', ''):
        cursor.execute('DELETE FROM alerts WHERE room_id = ?', (clean_room,))
    else:
        cursor.execute('DELETE FROM alerts')
    conn.commit()
    conn.close()

init_db()

def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    current_time = datetime.datetime.now().astimezone().isoformat()
    conn = _connect()
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        # Chỉ lưu nếu ghế chưa có cảnh báo chưa giải quyết
        for seat in seats:
            if seat is None:
                cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id IS NULL AND alert_type=? AND resolved=0", 
                              (clean_room, show_id, alert_type))
            else:
                cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type=? AND resolved=0", 
                              (clean_room, show_id, seat, alert_type))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO alerts (room_id, show_id, alert_type, seat_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                              (clean_room, show_id, alert_type, seat, current_time))
        conn.commit()
    finally:
        conn.close()


def refresh_showtime_alerts(room_id: str, show_id: str, alert_result: dict) -> dict:
    """Quy tắc 15.5 (Idempotent Alert Refresh):
    Khi phân tích lại cùng (room_id, show_id) ở mốc sau (VD: T-3 sau T-5):
    - Tự động đóng (resolved = 1) các cảnh báo đang mở (resolved = 0) nếu ghế đó nay đã hợp lệ.
    - Lưu các cảnh báo mới phát sinh mà không tạo trùng lặp.
    """
    conn = _connect()
    conn.row_factory = sqlite3.Row
    auto_resolved = 0
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        illegal_set = set(alert_result.get("illegal_occupants") or [])
        missing_set = set(alert_result.get("missing_guests") or [])
        over_cap = bool(alert_result.get("over_capacity"))

        open_rows = cursor.execute(
            "SELECT id, alert_type, seat_id FROM alerts WHERE room_id=? AND show_id=? AND resolved=0",
            (clean_room, str(show_id).strip()),
        ).fetchall()

        ids_to_resolve = []
        for r in open_rows:
            atype = r["alert_type"]
            sid = r["seat_id"]
            if atype == "illegal_occupant" and sid not in illegal_set:
                ids_to_resolve.append(r["id"])
            elif atype == "missing_guest" and sid not in missing_set:
                ids_to_resolve.append(r["id"])
            elif atype == "over_capacity" and not over_cap:
                ids_to_resolve.append(r["id"])

        if ids_to_resolve:
            placeholders = ",".join("?" for _ in ids_to_resolve)
            cursor.execute(
                f"UPDATE alerts SET resolved = 1 WHERE id IN ({placeholders})",
                tuple(ids_to_resolve),
            )
            auto_resolved = len(ids_to_resolve)
        conn.commit()
    finally:
        conn.close()

    if alert_result.get("illegal_occupants"):
        save_alerts(room_id, show_id, "illegal_occupant", alert_result["illegal_occupants"])
    if alert_result.get("missing_guests"):
        save_alerts(room_id, show_id, "missing_guest", alert_result["missing_guests"])
    if alert_result.get("over_capacity"):
        save_alerts(room_id, show_id, "over_capacity", [None])

    return {"auto_resolved_count": auto_resolved}

def cleanup_finished_showtimes_alerts(cursor):
    """Tự động đóng (resolved = 1) tất cả cảnh báo của các suất chiếu đã kết thúc trong quá khứ,
    tránh rò rỉ cảnh báo của ca trước sang ca tiếp theo."""
    try:
        now_iso = datetime.datetime.now().astimezone().isoformat()
        cursor.execute("""
            UPDATE alerts 
            SET resolved = 1 
            WHERE resolved = 0 
              AND show_id IN (
                  SELECT show_id FROM showtimes WHERE end_at < ?
              )
        """, (now_iso,))
    except Exception:
        pass

def get_active_alerts(room_id: str = None):
    clean_room = _normalize_room_id(room_id)
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cleanup_finished_showtimes_alerts(cursor)
    conn.commit()
    if clean_room:
        cursor.execute("SELECT * FROM alerts WHERE room_id=? AND resolved=0 ORDER BY timestamp DESC", (clean_room,))
    else:
        cursor.execute("SELECT * FROM alerts WHERE resolved=0 ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    alerts_list = [dict(r) for r in rows]
    # Gắn thêm context (số vé đã quét, số người AI đếm, chùm ghế vi phạm) để phục vụ thông báo
    if alerts_list:
        try:
            grouped = get_grouped_active_alerts(room_id)
            meta_map = {(g["room_id"], g["show_id"]): g for g in grouped}
            for a in alerts_list:
                g = meta_map.get((a.get("room_id"), a.get("show_id")))
                if g:
                    a["scanned_tickets_count"] = g["scanned_tickets_count"]
                    a["detected_people_count"] = g["detected_people_count"]
                    a["room_alert_count"] = g["total_alerts"]
                    a["room_illegal_seats"] = g["illegal_seats"]
                    a["room_missing_seats"] = g["missing_seats"]
                    a["all_alerted_seats"] = g["all_alerted_seats"]
                else:
                    a["scanned_tickets_count"] = 0
                    a["detected_people_count"] = 0
                    a["room_alert_count"] = 1
                    a["room_illegal_seats"] = [a["seat_id"]] if a.get("seat_id") else []
                    a["room_missing_seats"] = []
                    a["all_alerted_seats"] = [a["seat_id"]] if a.get("seat_id") else []
        except Exception:
            pass
    return alerts_list

def get_grouped_active_alerts(room_id: str = None) -> list:
    """Gom nhóm các cảnh báo đang mở (resolved = 0) theo từng Phòng & Suất chiếu.
    Mỗi nhóm cung cấp đầy đủ 3 chỉ số theo yêu cầu:
    1. scanned_tickets_count: Số vé đã quét của rạp này (Tập A)
    2. detected_people_count: Số người hiện có trong rạp (Camera AI đếm)
    3. all_alerted_seats: Danh sách các ghế được cảnh báo (illegal/missing)
    """
    clean_room = _normalize_room_id(room_id)
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cleanup_finished_showtimes_alerts(cursor)
        conn.commit()
        if clean_room:
            cursor.execute(
                "SELECT * FROM alerts WHERE room_id = ? AND resolved = 0 ORDER BY timestamp DESC",
                (clean_room,),
            )
        else:
            cursor.execute(
                "SELECT * FROM alerts WHERE resolved = 0 ORDER BY timestamp DESC"
            )
        rows = [dict(r) for r in cursor.fetchall()]

        groups = {}
        for r in rows:
            key = (r["room_id"], r["show_id"])
            if key not in groups:
                groups[key] = {
                    "room_id": r["room_id"],
                    "show_id": r["show_id"],
                    "latest_timestamp": r["timestamp"],
                    "alert_ids": [],
                    "illegal_seats": [],
                    "missing_seats": [],
                    "over_capacity": False,
                    "raw_alerts": [],
                }
            g = groups[key]
            g["alert_ids"].append(r["id"])
            g["raw_alerts"].append(r)
            atype = r.get("alert_type")
            sid = r.get("seat_id")
            if atype == "illegal_occupant" and sid:
                if sid not in g["illegal_seats"]:
                    g["illegal_seats"].append(sid)
            elif atype == "missing_guest" and sid:
                if sid not in g["missing_seats"]:
                    g["missing_seats"].append(sid)
            elif atype == "over_capacity":
                g["over_capacity"] = True

        result = []
        for (r_id, s_id), g in groups.items():
            # 1. Số vé đã quét của rạp này
            cursor.execute(
                "SELECT COUNT(*) FROM tickets WHERE room_id = ? AND show_id = ?",
                (r_id, s_id),
            )
            scanned_count = cursor.fetchone()[0]

            # 2. Số người hiện có trong rạp (lấy từ log AI mới nhất của suất này)
            cursor.execute(
                """
                SELECT detected_heads_count, mapped_seats_count 
                FROM ai_inference_logs 
                WHERE room_id = ? AND show_id = ? 
                ORDER BY id DESC LIMIT 1
                """,
                (r_id, s_id),
            )
            log_row = cursor.fetchone()
            if log_row:
                detected_count = log_row[0] if log_row[0] is not None else log_row[1]
            else:
                detected_count = max(0, scanned_count + len(g["illegal_seats"]) - len(g["missing_seats"]))

            g["illegal_seats"].sort()
            g["missing_seats"].sort()
            all_seats = list(dict.fromkeys(g["illegal_seats"] + g["missing_seats"]))

            result.append({
                "room_id": r_id,
                "show_id": s_id,
                "latest_timestamp": g["latest_timestamp"],
                "scanned_tickets_count": scanned_count,
                "detected_people_count": detected_count,
                "total_alerts": len(g["alert_ids"]),
                "alert_ids": g["alert_ids"],
                "illegal_seats": g["illegal_seats"],
                "missing_seats": g["missing_seats"],
                "all_alerted_seats": all_seats,
                "over_capacity": g["over_capacity"],
            })

        return result
    finally:
        conn.close()

def resolve_room_alerts(room_id: str, show_id: str) -> int:
    """Xử lý hàng loạt toàn bộ cảnh báo đang mở của một phòng & suất chiếu (One-Tap Resolve)."""
    clean_room = _normalize_room_id(room_id)
    clean_show = str(show_id).strip()
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alerts SET resolved = 1 WHERE room_id = ? AND show_id = ? AND resolved = 0",
            (clean_room, clean_show),
        )
        count = cursor.rowcount
        conn.commit()
        return count
    finally:
        conn.close()

def get_all_alerts(room_id: str = None, alert_type: str = None, status: str = None):
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    
    if room_id and str(room_id).lower() != "all":
        query += " AND room_id=?"
        params.append(_normalize_room_id(room_id))
        
    if alert_type and str(alert_type).lower() != "all":
        query += " AND alert_type=?"
        params.append(alert_type)
        
    if status:
        st_lower = str(status).lower()
        if st_lower == "active":
            query += " AND resolved=0"
        elif st_lower == "resolved":
            query += " AND resolved=1"
        
    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_alert(alert_id: int):
    conn = _connect()
    try:
        cursor = conn.cursor()
        row = cursor.execute("SELECT room_id, show_id FROM alerts WHERE id=?", (alert_id,)).fetchone()
        if row and row[0] and row[1]:
            cursor.execute("UPDATE alerts SET resolved=1 WHERE room_id=? AND show_id=? AND resolved=0", (row[0], row[1]))
        else:
            cursor.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
        conn.commit()
    finally:
        conn.close()

def get_configs():
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM configs")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_config(key: str, value: str):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configs (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

_TZ_VN = datetime.timezone(datetime.timedelta(hours=7))
ONLINE_WINDOW_SECONDS = 300  # Dưới 5 phút kể từ lần hoạt động cuối = "đang trực tuyến"


def _now_vn_iso() -> str:
    return datetime.datetime.now(_TZ_VN).isoformat(timespec="seconds")


def touch_employee_last_seen(emp_id: int, iso_now: str = None):
    """Cập nhật last_seen_at (ISO 8601, múi giờ +07:00) cho nhân viên."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE employees SET last_seen_at=? WHERE id=?",
            (iso_now or _now_vn_iso(), emp_id),
        )
        conn.commit()
    finally:
        conn.close()


def is_employee_online(last_seen_at_str: str, window_seconds: int = ONLINE_WINDOW_SECONDS) -> bool:
    """True nếu last_seen_at cách hiện tại dưới window_seconds giây."""
    if not last_seen_at_str:
        return False
    try:
        dt = datetime.datetime.fromisoformat(str(last_seen_at_str))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_TZ_VN)
    delta = (datetime.datetime.now(_TZ_VN) - dt).total_seconds()
    return 0 <= delta < window_seconds or (-5 < delta < 0)


def _decorate_employee(d: dict) -> dict:
    d.pop("password", None)
    d["is_active"] = int(d.get("is_active", 1) if d.get("is_active") is not None else 1)
    d["is_online"] = bool(d["is_active"]) and is_employee_online(d.get("last_seen_at"))

    # Chỉ hiển thị ca làm việc khi nhân viên đã đăng nhập vào hệ thống
    last_seen = d.get("last_seen_at")
    logged_in = False
    if last_seen:
        try:
            dt = datetime.datetime.fromisoformat(str(last_seen))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_TZ_VN)
            # Chỉ tính là đã đăng nhập nếu có hoạt động trong ngày hôm nay
            logged_in = dt.astimezone(_TZ_VN).date() == datetime.datetime.now(_TZ_VN).date()
        except Exception:
            logged_in = False

    shift_code = d.get("shift")
    if logged_in and shift_code and shift_code in SHIFT_LABELS:
        d["shift_label"] = SHIFT_LABELS[shift_code]
    else:
        d["shift"] = None
        d["shift_label"] = "Chưa có"
    return d


_EMP_COLS = "id, username, name, role, created_at, shift, is_active, last_seen_at"


def get_employees(viewer_id: int = None, viewer_role: str = None):
    """Danh sách nhân viên (KHÔNG có password).

    Nếu truyền viewer_id: chỉ trả các dòng (role != 'Quản lý' OR id = viewer_id).
    """
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        if viewer_id is not None:
            cursor.execute(
                f"SELECT {_EMP_COLS} FROM employees WHERE (role != 'Quản lý' OR id = ?) ORDER BY created_at DESC",
                (viewer_id,),
            )
        else:
            cursor.execute(f"SELECT {_EMP_COLS} FROM employees ORDER BY created_at DESC")
        rows = cursor.fetchall()
    finally:
        conn.close()
    return [_decorate_employee(dict(r)) for r in rows]


def get_employee(emp_id: int):
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {_EMP_COLS} FROM employees WHERE id=?", (emp_id,))
        row = cursor.fetchone()
    finally:
        conn.close()
    return _decorate_employee(dict(row)) if row else None


def add_employee(username: str, password: str, name: str, role: str, shift: str = None):
    conn = _connect()
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        cursor.execute(
            "INSERT INTO employees (username, password, name, role, shift) VALUES (?, ?, ?, ?, ?)",
            (username.strip(), hashed_pw, name, role, shift),
        )
        emp_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return emp_id


def update_employee(emp_id: int, username: str, password: str, name: str, role: str,
                    shift: str = None, is_active: int = None):
    conn = _connect()
    cursor = conn.cursor()
    try:
        if password and str(password).strip():
            hashed_pw = hash_password(password)
            cursor.execute(
                "UPDATE employees SET username=?, password=?, name=?, role=?, shift=? WHERE id=?",
                (username.strip(), hashed_pw, name, role, shift, emp_id),
            )
        else:
            cursor.execute(
                "UPDATE employees SET username=?, name=?, role=?, shift=? WHERE id=?",
                (username.strip(), name, role, shift, emp_id),
            )
        if is_active is not None:
            cursor.execute(
                "UPDATE employees SET is_active=? WHERE id=?",
                (1 if int(is_active) else 0, emp_id),
            )
        conn.commit()
    finally:
        conn.close()


def set_employee_active(emp_id: int, is_active: int):
    """Kích hoạt lại / ngưng hoạt động một tài khoản."""
    conn = _connect()
    try:
        conn.execute("UPDATE employees SET is_active=? WHERE id=?", (1 if int(is_active) else 0, emp_id))
        conn.commit()
    finally:
        conn.close()


def authenticate_employee(username: str, password: str):
    """Xác thực nhân viên bằng PBKDF2-HMAC-SHA256 (`verify_password`).

    Trả None nếu sai thông tin HOẶC tài khoản đã ngưng hoạt động (is_active = 0).
    Đăng nhập thành công sẽ cập nhật last_seen_at.
    """
    if not username or password is None:
        return None
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password, name, role, shift, is_active FROM employees WHERE LOWER(username)=LOWER(?)",
            (username.strip(),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        if not verify_password(password, row["password"]):
            return None
        if row["is_active"] == 0:
            return None
        # Tự động tính ca làm việc theo giờ đăng nhập thực tế
        dyn_shift_code, dyn_shift_label = get_dynamic_shift(row["role"])
        conn.execute(
            "UPDATE employees SET last_seen_at=?, shift=? WHERE id=?",
            (_now_vn_iso(), dyn_shift_code, row["id"])
        )
        conn.commit()
        return {
            "id": row["id"],
            "name": row["name"],
            "role": row["role"],
            "shift": dyn_shift_code,
            "shift_label": dyn_shift_label,
        }
    finally:
        conn.close()


def is_inactive_account_with_valid_password(username: str, password: str) -> bool:
    """True nếu đúng mật khẩu nhưng tài khoản đã ngưng hoạt động (để API báo lỗi rõ ràng)."""
    if not username or password is None:
        return False
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT password, is_active FROM employees WHERE LOWER(username)=LOWER(?)",
            (username.strip(),),
        ).fetchone()
        return bool(row) and row["is_active"] == 0 and verify_password(password, row["password"])
    finally:
        conn.close()


def delete_employee(emp_id: int) -> dict:
    """Xóa nhân viên. Nếu đã có biên bản sự cố liên quan -> chỉ ngưng hoạt động (giữ toàn vẹn dữ liệu)."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        used = cursor.execute(
            "SELECT 1 FROM incidents WHERE reporter_id = ? OR resolved_by_id = ? LIMIT 1",
            (emp_id, emp_id),
        ).fetchone()
        if used:
            cursor.execute("UPDATE employees SET is_active = 0 WHERE id = ?", (emp_id,))
            conn.commit()
            return {"action": "deactivated", "id": emp_id}
        cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
        conn.commit()
        return {"action": "deleted", "id": emp_id}
    finally:
        conn.close()


def _format_incident_row(row_dict: dict) -> dict:
    """Chuẩn hóa kết quả LEFT JOIN giữa incidents và employees (Chuẩn 3NF)."""
    shift_code = row_dict.pop("reporter_shift", None)
    row_dict["shift_label"] = SHIFT_LABELS.get(shift_code, "Chưa phân ca")
    if not row_dict.get("reporter_name"):
        row_dict["reporter_name"] = "Nhân viên"
    if not row_dict.get("reporter_role"):
        row_dict["reporter_role"] = "Soát vé"
    return row_dict


def create_incident(
    category,
    severity,
    title,
    description,
    room_id,
    show_id,
    seat_ids,
    reporter_id,
    reporter_name=None,
    reporter_role=None,
    shift_label=None,
    created_at=None,
    status="open",
    reporter_shift=None,
    image_path=None,
):
    """Lưu sự cố theo chuẩn 3NF + Snapshot Ca trực (Điểm 5):
    - Chỉ lưu khóa ngoại room_id và reporter_id (không lưu thừa tên/chức vụ).
    - Lưu snapshot reporter_shift ngay tại thời điểm báo sự cố.
    - Kiểm tra nghiêm ngặt reporter_id tồn tại trong employees (không tự ý quy về admin id=1).
    """
    conn = _connect()
    try:
        cursor = conn.cursor()
        clean_room = _normalize_room_id(room_id)
        if clean_room:
            room_exists = cursor.execute("SELECT 1 FROM rooms WHERE id=?", (clean_room,)).fetchone()
            if not room_exists:
                clean_room = None

        if reporter_id is None:
            raise ValueError("Thiếu mã nhân viên báo cáo sự cố (reporter_id).")

        emp_row = cursor.execute(
            "SELECT id, shift, role FROM employees WHERE id=?",
            (int(reporter_id),),
        ).fetchone()
        if not emp_row:
            raise ValueError(f"Nhân viên báo cáo (id={reporter_id}) không tồn tại trong hệ thống.")

        clean_rep_id = int(emp_row[0])
        if reporter_shift and reporter_shift in SHIFT_LABELS:
            snapshot_shift = reporter_shift
        elif emp_row[1] and emp_row[1] in SHIFT_LABELS:
            snapshot_shift = emp_row[1]
        else:
            snapshot_shift, _ = get_dynamic_shift(emp_row[2] if len(emp_row) > 2 else None)

        now_iso = created_at or datetime.datetime.now().astimezone().isoformat()
        clean_status = status if status in ("open", "resolved") else "open"

        cursor.execute(
            """
            INSERT INTO incidents 
            (category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_shift, created_at, status, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category,
                severity,
                title,
                description,
                clean_room,
                show_id,
                seat_ids,
                clean_rep_id,
                snapshot_shift,
                now_iso,
                clean_status,
                image_path,
            ),
        )
        incident_id = cursor.lastrowid
        conn.commit()
        return incident_id
    finally:
        conn.close()


INCIDENT_JOIN_SELECT = """
    SELECT 
        i.id,
        i.category,
        i.severity,
        i.title,
        i.description,
        i.room_id,
        i.show_id,
        i.seat_ids,
        i.reporter_id,
        e_rep.name AS reporter_name,
        e_rep.role AS reporter_role,
        COALESCE(i.reporter_shift, e_rep.shift) AS reporter_shift,
        i.created_at,
        i.status,
        i.resolved_by_id,
        e_res.name AS resolved_by_name,
        i.resolved_at,
        i.image_path
    FROM incidents i
    LEFT JOIN employees e_rep ON i.reporter_id = e_rep.id
    LEFT JOIN employees e_res ON i.resolved_by_id = e_res.id
"""


def list_incidents(room_id=None, status=None, category=None, from_time=None, to_time=None, limit=None):
    try:
        cleanup_resolved_incidents(hours=1.0)
    except Exception:
        pass
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = INCIDENT_JOIN_SELECT + " WHERE 1=1"
    params = []

    if room_id:
        query += " AND i.room_id=?"
        params.append(_normalize_room_id(room_id))
    if status:
        query += " AND i.status=?"
        params.append(status)
    if category:
        query += " AND i.category=?"
        params.append(category)
    if from_time:
        query += " AND i.created_at >= ?"
        params.append(from_time)
    if to_time:
        query += " AND i.created_at <= ?"
        params.append(to_time)

    query += " ORDER BY i.created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [_format_incident_row(dict(r)) for r in rows]


def get_incident(incident_id: int):
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(INCIDENT_JOIN_SELECT + " WHERE i.id=?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    return _format_incident_row(dict(row)) if row else None


def resolve_incident(incident_id: int, resolver_id: int, resolver_name: str = None, resolved_at: str = None):
    """Cập nhật trạng thái xử lý theo chuẩn 3NF: chỉ lưu khóa ngoại resolved_by_id.
    Kiểm tra nghiêm ngặt resolver_id tồn tại trong employees (không tự ý quy về admin id=1).
    """
    conn = _connect()
    try:
        cursor = conn.cursor()
        if resolver_id is None:
            raise ValueError("Thiếu mã nhân viên xử lý sự cố (resolver_id).")

        emp_exists = cursor.execute(
            "SELECT id FROM employees WHERE id=?",
            (int(resolver_id),),
        ).fetchone()
        if not emp_exists:
            raise ValueError(f"Nhân viên xử lý (id={resolver_id}) không tồn tại trong hệ thống.")

        clean_res_id = int(emp_exists[0])

        now_iso = resolved_at or datetime.datetime.now().astimezone().isoformat()
        cursor.execute(
            """
            UPDATE incidents 
            SET status='resolved', resolved_by_id=?, resolved_at=? 
            WHERE id=?
            """,
            (clean_res_id, now_iso, incident_id),
        )
        conn.commit()
    finally:
        conn.close()

def cleanup_resolved_incidents(hours: float = 1.0) -> int:
    """Tự động loại bỏ các sự cố đã xử lý (status='resolved') quá 1 tiếng (3600s) kể từ lúc giải quyết."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        now = datetime.datetime.now().astimezone()
        cutoff = now - datetime.timedelta(hours=hours)

        cursor.execute("SELECT id, resolved_at, image_path FROM incidents WHERE status='resolved'")
        rows = cursor.fetchall()

        to_delete = []
        photos_to_remove = []

        for row in rows:
            inc_id = row[0]
            res_at_str = row[1]
            img_path = row[2]

            should_delete = False
            if res_at_str:
                try:
                    dt = datetime.datetime.fromisoformat(str(res_at_str).strip())
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=now.tzinfo)
                    if dt <= cutoff:
                        should_delete = True
                except Exception:
                    should_delete = True
            else:
                should_delete = True

            if should_delete:
                to_delete.append(inc_id)
                if img_path:
                    photos_to_remove.append(img_path)

        if to_delete:
            cursor.execute(
                f"DELETE FROM incidents WHERE id IN ({','.join(['?'] * len(to_delete))})",
                to_delete,
            )
            conn.commit()

            upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "incidents")
            for p in photos_to_remove:
                try:
                    fn = os.path.basename(p)
                    full_p = os.path.join(upload_dir, fn)
                    if os.path.exists(full_p):
                        os.remove(full_p)
                except Exception:
                    pass

        return len(to_delete)
    finally:
        conn.close()


def delete_incident(incident_id: int) -> bool:
    """Xóa một sự cố ngay lập tức theo yêu cầu người dùng."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        row = cursor.execute("SELECT image_path FROM incidents WHERE id=?", (incident_id,)).fetchone()
        if not row:
            return False
        img_path = row[0]
        cursor.execute("DELETE FROM incidents WHERE id=?", (incident_id,))
        conn.commit()

        if img_path:
            try:
                upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "incidents")
                fn = os.path.basename(img_path)
                full_p = os.path.join(upload_dir, fn)
                if os.path.exists(full_p):
                    os.remove(full_p)
            except Exception:
                pass
        return True
    finally:
        conn.close()


def clear_resolved_incidents() -> int:
    """Xóa tất cả các sự cố đã khắc phục theo yêu cầu người dùng."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, image_path FROM incidents WHERE status='resolved'").fetchall()
        if not rows:
            return 0
        ids = [r[0] for r in rows]
        photos = [r[1] for r in rows if r[1]]
        cursor.execute(f"DELETE FROM incidents WHERE id IN ({','.join(['?'] * len(ids))})", ids)
        conn.commit()

        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "incidents")
        for p in photos:
            try:
                fn = os.path.basename(p)
                full_p = os.path.join(upload_dir, fn)
                if os.path.exists(full_p):
                    os.remove(full_p)
            except Exception:
                pass
        return len(ids)
    finally:
        conn.close()



def save_inference_log(
    room_id: str,
    show_id: str,
    image_width: int,
    image_height: int,
    total_seats: int,
    booked_tickets_count: int,
    detected_heads_count: int,
    mapped_seats_count: int,
    illegal_count: int,
    missing_count: int,
    over_capacity: bool,
    inference_time_ms: float,
    yolo_time_ms: float = None,
    mapping_time_ms: float = None,
    trigger_source: str = "MANUAL",
) -> int:
    """Lưu nhật ký phân tích AI (Audit & Performance Log) cho mỗi lần gọi /api/v1/analyze."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        captured_at = datetime.datetime.now().astimezone().isoformat()
        clean_source = str(trigger_source or "MANUAL").strip().upper()
        cursor.execute(
            """
            INSERT INTO ai_inference_logs (
                room_id, show_id, captured_at, image_width, image_height,
                total_seats, booked_tickets_count, detected_heads_count, mapped_seats_count,
                illegal_count, missing_count, over_capacity, inference_time_ms,
                yolo_time_ms, mapping_time_ms, trigger_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_room,
                show_id,
                captured_at,
                int(image_width),
                int(image_height),
                int(total_seats),
                int(booked_tickets_count),
                int(detected_heads_count),
                int(mapped_seats_count),
                int(illegal_count),
                int(missing_count),
                1 if over_capacity else 0,
                round(float(inference_time_ms), 2),
                round(float(yolo_time_ms), 2) if yolo_time_ms is not None else None,
                round(float(mapping_time_ms), 2) if mapping_time_ms is not None else None,
                clean_source,
            ),
        )
        log_id = cursor.lastrowid
        conn.commit()
        return log_id
    finally:
        conn.close()


def get_inference_logs(room_id: str = None, show_id: str = None, limit: int = 50):
    """Truy vấn lịch sử phân tích AI phục vụ thống kê & đánh giá hiệu năng đồ án."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM ai_inference_logs WHERE 1=1"
        params = []
        if room_id and str(room_id).lower() != "all":
            query += " AND room_id=?"
            params.append(_normalize_room_id(room_id))
        if show_id:
            query += " AND show_id=?"
            params.append(show_id)
        query += " ORDER BY captured_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query, tuple(params))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def update_incident_photo(incident_id: int, image_path: str):
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE incidents SET image_path = ? WHERE id = ?", (image_path, incident_id))
        conn.commit()
    finally:
        conn.close()
