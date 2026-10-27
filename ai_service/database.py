import sqlite3
import os
import datetime
from security import hash_password, verify_password

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

# Phải khớp với SHIFTS trong main.py (code: ca_sang, ca_toi)
SHIFT_LABELS = {
    "ca_sang": "Ca sáng",
    "ca_toi": "Ca tối",
}


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
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
            shift TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'shift' not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN shift TEXT NULL")

    # Làm sạch mã ca cũ không hợp lệ (ví dụ 'morning' -> NULL)
    cursor.execute(
        "UPDATE employees SET shift = NULL WHERE shift IS NOT NULL AND shift NOT IN ('ca_sang', 'ca_toi')"
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
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
        )
    """)
    log_cols = [row[1] for row in cursor.execute("PRAGMA table_info(ai_inference_logs)").fetchall()]
    if "yolo_time_ms" not in log_cols:
        cursor.execute("ALTER TABLE ai_inference_logs ADD COLUMN yolo_time_ms REAL NULL")
    if "mapping_time_ms" not in log_cols:
        cursor.execute("ALTER TABLE ai_inference_logs ADD COLUMN mapping_time_ms REAL NULL")

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

def get_active_alerts(room_id: str = None):
    clean_room = _normalize_room_id(room_id)
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if clean_room:
        cursor.execute("SELECT * FROM alerts WHERE room_id=? AND resolved=0 ORDER BY timestamp DESC", (clean_room,))
    else:
        cursor.execute("SELECT * FROM alerts WHERE resolved=0 ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

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

def get_employees():
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role, created_at, shift FROM employees ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_employee(emp_id: int):
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role, created_at, shift FROM employees WHERE id=?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

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


def update_employee(emp_id: int, username: str, password: str, name: str, role: str, shift: str = None):
    conn = _connect()
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()


def authenticate_employee(username: str, password: str):
    """Xác thực nhân viên bằng PBKDF2-HMAC-SHA256 (`verify_password`)."""
    if not username or password is None:
        return None
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password, name, role, shift FROM employees WHERE LOWER(username)=LOWER(?)",
            (username.strip(),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        if not verify_password(password, row["password"]):
            return None
        shift_code = row["shift"]
        return {
            "id": row["id"],
            "name": row["name"],
            "role": row["role"],
            "shift": shift_code,
            "shift_label": SHIFT_LABELS.get(shift_code, "Chưa phân ca"),
        }
    finally:
        conn.close()

def delete_employee(emp_id: int):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
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
            "SELECT id, shift FROM employees WHERE id=?",
            (int(reporter_id),),
        ).fetchone()
        if not emp_row:
            raise ValueError(f"Nhân viên báo cáo (id={reporter_id}) không tồn tại trong hệ thống.")

        clean_rep_id = int(emp_row[0])
        snapshot_shift = reporter_shift if reporter_shift in SHIFT_LABELS else emp_row[1]

        now_iso = created_at or datetime.datetime.now().astimezone().isoformat()
        clean_status = status if status in ("open", "resolved") else "open"

        cursor.execute(
            """
            INSERT INTO incidents 
            (category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_shift, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        i.resolved_at
    FROM incidents i
    LEFT JOIN employees e_rep ON i.reporter_id = e_rep.id
    LEFT JOIN employees e_res ON i.resolved_by_id = e_res.id
"""


def list_incidents(room_id=None, status=None, category=None, from_time=None, to_time=None, limit=None):
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
) -> int:
    """Lưu nhật ký phân tích AI (Audit & Performance Log) cho mỗi lần gọi /api/v1/analyze."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        captured_at = datetime.datetime.now().astimezone().isoformat()
        cursor.execute(
            """
            INSERT INTO ai_inference_logs (
                room_id, show_id, captured_at, image_width, image_height,
                total_seats, booked_tickets_count, detected_heads_count, mapped_seats_count,
                illegal_count, missing_count, over_capacity, inference_time_ms,
                yolo_time_ms, mapping_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
