import sqlite3
import os
import json
import datetime
from security import hash_password, verify_password, verify_ticket_qr_signature
from seat_mapper import get_seat_tier, normalize_seat

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

_TZ_VN = datetime.timezone(datetime.timedelta(hours=7))

# Phải khớp với SHIFTS trong main.py (code: ca_sang, ca_chieu, ca_toi, ca_dem)
SHIFT_LABELS = {
    "ca_sang": "Ca sáng",
    "ca_chieu": "Ca chiều",
    "ca_toi": "Ca tối",
    "ca_dem": "Ca đêm",
}


def get_dynamic_shift(
    role: str = None,
    now: datetime.datetime = None,
    assigned_shift: str = None,
) -> tuple[str, str]:
    """Tính toán ca làm việc động dựa trên thời điểm đăng nhập/thao tác (Giờ Việt Nam UTC+7),
    kèm biên độ đệm ±30 phút (chuẩn bị đầu ca 07:00-07:30 và bàn giao cuối ca 23:00-23:30)
    và nối liền 100% khung giờ Quản lý (xóa khoảng trống 16:00-16:30):
    - Nhân viên (Soát vé / Staff):
        + 07:30 - 13:00 (đệm vào ca từ 07:00): Ca sáng (07:30 - 13:00) [ca_sang]
        + 13:00 - 16:00: Ca chiều (13:00 - 16:00) [ca_chieu]
        + 16:00 - 23:00 (đệm bàn giao đến 23:30): Ca tối (16:00 - 23:00) [ca_toi]
        + 23:30 - 07:00: Ca đêm (23:00 - 07:30) [ca_dem]
    - Quản lý (Manager / Admin):
        + 07:30 - 16:00 (đệm vào ca từ 07:00): Ca sáng (07:30 - 16:00) [ca_sang]
        + 16:00 - 24:00: Ca tối (16:00 - 24:00) [ca_toi]
        + 00:00 - 07:00: Ca đêm (00:00 - 07:30) [ca_dem]
    Nếu nhân viên có ca phân công (`assigned_shift`) và giờ hiện tại nằm trong khung giờ
    ca đó ±30 phút thì ưu tiên giữ nguyên ca được phân công.
    """
    if now is None:
        now = datetime.datetime.now(_TZ_VN)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_TZ_VN)
    else:
        now = now.astimezone(_TZ_VN)

    minute_of_day = now.hour * 60 + now.minute
    is_manager = str(role or "").strip().lower() in ("quản lý", "quan ly", "manager", "admin")
    assigned = str(assigned_shift or "").strip().lower()

    if is_manager:
        if assigned == "ca_sang" and 420 <= minute_of_day <= 990:
            return "ca_sang", "Ca sáng (07:30 - 16:00)"
        if assigned == "ca_toi" and (930 <= minute_of_day < 1440 or minute_of_day <= 30):
            return "ca_toi", "Ca tối (16:00 - 24:00)"
        if 420 <= minute_of_day < 960:
            return "ca_sang", "Ca sáng (07:30 - 16:00)"
        elif 960 <= minute_of_day < 1440:
            return "ca_toi", "Ca tối (16:00 - 24:00)"
        else:
            return "ca_dem", "Ca đêm (00:00 - 07:30)"
    else:
        if assigned == "ca_sang" and 420 <= minute_of_day <= 810:
            return "ca_sang", "Ca sáng (07:30 - 13:00)"
        if assigned == "ca_chieu" and 750 <= minute_of_day <= 990:
            return "ca_chieu", "Ca chiều (13:00 - 16:00)"
        if assigned == "ca_toi" and 930 <= minute_of_day <= 1410:
            return "ca_toi", "Ca tối (16:00 - 23:00)"
        if 420 <= minute_of_day < 780:
            return "ca_sang", "Ca sáng (07:30 - 13:00)"
        elif 780 <= minute_of_day < 960:
            return "ca_chieu", "Ca chiều (13:00 - 16:00)"
        elif 960 <= minute_of_day <= 1410:
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
        seats_cnt = 132 if idx == 3 else 136
        cursor.execute(
            "INSERT OR IGNORE INTO rooms (id, name, total_seats, screen_type, is_active, created_at) VALUES (?, ?, ?, '2D Standard', 1, ?)",
            (f"room{idx}", f"Phòng chiếu {idx}", seats_cnt, now_iso),
        )
    cursor.execute("UPDATE rooms SET total_seats = 132 WHERE id = 'room3' AND total_seats != 132")

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
            seat_tier TEXT DEFAULT 'STANDARD',
            signature TEXT NULL,
            device_id TEXT NULL,
            scanned_by_id INTEGER NULL,
            scanned_at TEXT NULL,
            source TEXT DEFAULT 'QR_SCAN',
            PRIMARY KEY (room_id, show_id, ticket_id),
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
        )
    """)
    ticket_cols = [row[1] for row in cursor.execute("PRAGMA table_info(tickets)").fetchall()]
    if "seat_tier" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN seat_tier TEXT DEFAULT 'STANDARD'")
    if "signature" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN signature TEXT NULL")
    if "device_id" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN device_id TEXT NULL")
    if "scanned_by_id" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN scanned_by_id INTEGER NULL")
    if "scanned_at" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN scanned_at TEXT NULL")
    if "source" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN source TEXT DEFAULT 'QR_SCAN'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            show_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            seat_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            resolution TEXT NULL,
            resolved_by_id INTEGER NULL,
            resolved_at TEXT NULL,
            detail TEXT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
        )
    """)
    alert_cols = [row[1] for row in cursor.execute("PRAGMA table_info(alerts)").fetchall()]
    if "resolution" not in alert_cols:
        cursor.execute("ALTER TABLE alerts ADD COLUMN resolution TEXT NULL")
    if "resolved_by_id" not in alert_cols:
        cursor.execute("ALTER TABLE alerts ADD COLUMN resolved_by_id INTEGER NULL")
    if "resolved_at" not in alert_cols:
        cursor.execute("ALTER TABLE alerts ADD COLUMN resolved_at TEXT NULL")
    if "detail" not in alert_cols:
        cursor.execute("ALTER TABLE alerts ADD COLUMN detail TEXT NULL")
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

def save_tickets(
    room_id: str,
    show_id: str,
    tickets: list,
    scanned_by_id: int = None,
    device_id: str = None,
    require_signature: bool = False,
) -> dict:
    """Lưu danh sách vé đã soát (Tập A) kèm kiểm tra:
    - Chữ ký số HMAC-SHA256 (`sig`) chống vé giả mạo (Lỗi 1.1).
    - Xung đột quét trùng ghế/vé từ nhiều thiết bị khi Offline đồng bộ lên (Lỗi 1.2).
    """
    now_iso = datetime.datetime.now().astimezone().isoformat()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    saved_count = 0
    conflicts = []
    forged_tickets = []
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        clean_show = str(show_id).strip()
        for t in (tickets or []):
            t_id = str(t.get("ticket") or "").strip()
            s_id = normalize_seat(t.get("seat") or "")
            if not t_id or not s_id:
                continue
            s_tier = str(t.get("tier") or get_seat_tier(s_id, clean_room)).upper()
            if s_tier not in ("STANDARD", "VIP"):
                s_tier = get_seat_tier(s_id, clean_room)
            sig = str(t.get("sig") or "").strip()
            t_dev = str(t.get("device_id") or device_id or "").strip() or None
            t_time = str(t.get("scanned_at") or now_iso).strip()

            # 1. Xác thực chữ ký số HMAC-SHA256 nếu có cung cấp sig hoặc bắt buộc require_signature
            if sig or require_signature:
                if not verify_ticket_qr_signature(clean_room, clean_show, t_id, s_id, sig):
                    forged_info = {
                        "ticket": t_id,
                        "seat": s_id,
                        "device_id": t_dev,
                        "reason": "invalid_hmac_signature",
                    }
                    forged_tickets.append(forged_info)
                    # Tạo cảnh báo vé giả mạo trên Dashboard SOC
                    cursor.execute(
                        "SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type='forged_ticket' AND resolved=0",
                        (clean_room, clean_show, s_id),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO alerts (room_id, show_id, alert_type, seat_id, timestamp, detail) VALUES (?, ?, 'forged_ticket', ?, ?, ?)",
                            (clean_room, clean_show, s_id, now_iso, json.dumps(forged_info, ensure_ascii=False)),
                        )
                    continue

            # 2. Kiểm tra xung đột quét trùng (cùng ghế nhưng khác mã vé, hoặc cùng vé/ghế nhưng quét từ thiết bị khác)
            existing_rows = cursor.execute(
                "SELECT ticket_id, seat_id, device_id, scanned_by_id, source FROM tickets WHERE room_id=? AND show_id=? AND (seat_id=? OR ticket_id=?)",
                (clean_room, clean_show, s_id, t_id),
            ).fetchall()

            if not existing_rows:
                cursor.execute(
                    """
                    INSERT INTO tickets (room_id, show_id, ticket_id, seat_id, seat_tier, signature, device_id, scanned_by_id, scanned_at, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'QR_SCAN')
                    """,
                    (clean_room, clean_show, t_id, s_id, s_tier, sig or None, t_dev, scanned_by_id, t_time),
                )
                saved_count += 1
            else:
                ex = existing_rows[0]
                ex_ticket = ex["ticket_id"]
                ex_seat = ex["seat_id"]
                ex_dev = ex["device_id"]
                ex_source = ex["source"] or "QR_SCAN"

                # Nếu ghế được tạo tự động từ 'ticket_verified' trước đó và nay vé thật đồng bộ lên -> nâng cấp sang QR_SCAN
                if ex_source == "MANUAL_VERIFIED" and ex_seat == s_id:
                    cursor.execute(
                        "DELETE FROM tickets WHERE room_id=? AND show_id=? AND ticket_id=?",
                        (clean_room, clean_show, ex_ticket),
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO tickets (room_id, show_id, ticket_id, seat_id, seat_tier, signature, device_id, scanned_by_id, scanned_at, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'QR_SCAN')
                        """,
                        (clean_room, clean_show, t_id, s_id, s_tier, sig or None, t_dev, scanned_by_id, t_time),
                    )
                    saved_count += 1
                    continue

                is_different_ticket_same_seat = (ex_seat == s_id and ex_ticket != t_id)
                is_different_device_same_ticket = (
                    ex_ticket == t_id and ex_dev and t_dev and ex_dev != t_dev
                )

                if is_different_ticket_same_seat or is_different_device_same_ticket:
                    conflict_info = {
                        "seat": s_id,
                        "ticket": t_id,
                        "existing_ticket": ex_ticket,
                        "device_id": t_dev,
                        "existing_device_id": ex_dev,
                        "reason": "different_ticket_same_seat"
                        if is_different_ticket_same_seat
                        else "duplicate_scan_multi_device",
                    }
                    conflicts.append(conflict_info)
                    cursor.execute(
                        "SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type='duplicate_scan' AND resolved=0",
                        (clean_room, clean_show, s_id),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO alerts (room_id, show_id, alert_type, seat_id, timestamp, detail) VALUES (?, ?, 'duplicate_scan', ?, ?, ?)",
                            (clean_room, clean_show, s_id, now_iso, json.dumps(conflict_info, ensure_ascii=False)),
                        )
                # Ngược lại: cùng mã vé + cùng ghế + cùng thiết bị (idempotent retry) -> bỏ qua an toàn

        conn.commit()
        return {
            "saved_count": saved_count,
            "conflicts": conflicts,
            "forged_tickets": forged_tickets,
        }
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

def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list, details_by_seat: dict = None):
    current_time = datetime.datetime.now().astimezone().isoformat()
    conn = _connect()
    try:
        cursor = conn.cursor()
        clean_room = _require_showtime_exists(cursor, room_id, show_id)
        details_map = details_by_seat or {}
        # Chỉ lưu nếu ghế chưa có cảnh báo chưa giải quyết
        for seat in seats:
            detail_val = details_map.get(seat)
            if isinstance(detail_val, (dict, list)):
                detail_str = json.dumps(detail_val, ensure_ascii=False)
            elif detail_val is not None:
                detail_str = str(detail_val)
            elif seat is not None:
                detail_str = json.dumps({"seat_tier": get_seat_tier(seat, clean_room)}, ensure_ascii=False)
            else:
                detail_str = None

            if seat is None:
                cursor.execute(
                    "SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id IS NULL AND alert_type=? AND resolved=0",
                    (clean_room, show_id, alert_type),
                )
            else:
                cursor.execute(
                    "SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type=? AND resolved=0",
                    (clean_room, show_id, seat, alert_type),
                )
            existing = cursor.fetchone()
            if not existing:
                cursor.execute(
                    "INSERT INTO alerts (room_id, show_id, alert_type, seat_id, timestamp, detail) VALUES (?, ?, ?, ?, ?, ?)",
                    (clean_room, show_id, alert_type, seat, current_time, detail_str),
                )
            elif detail_str:
                cursor.execute(
                    "UPDATE alerts SET detail=? WHERE id=?",
                    (detail_str, existing[0]),
                )
        conn.commit()
    finally:
        conn.close()


def refresh_showtime_alerts(room_id: str, show_id: str, alert_result: dict) -> dict:
    """Quy tắc 15.5 (Idempotent Alert Refresh):
    Khi phân tích lại cùng (room_id, show_id) ở mốc sau (VD: T-3 sau T-5):
    - Tự động đóng (resolved = 1, resolution = 'auto_resolved') các cảnh báo đang mở (resolved = 0) nếu ghế đó nay đã hợp lệ.
    - Lưu các cảnh báo mới phát sinh mà không tạo trùng lặp, kèm gắn nhãn VIP Seat Hopping nếu có.
    """
    now_iso = datetime.datetime.now().astimezone().isoformat()
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
                f"UPDATE alerts SET resolved = 1, resolution = 'auto_resolved', resolved_at = ? WHERE id IN ({placeholders})",
                (now_iso, *ids_to_resolve),
            )
            auto_resolved = len(ids_to_resolve)
        conn.commit()
    finally:
        conn.close()

    hopping_list = alert_result.get("vip_seat_hopping") or []
    illegal_details = {}
    missing_details = {}
    for s in (alert_result.get("illegal_occupants") or []):
        illegal_details[s] = {"seat_tier": get_seat_tier(s, room_id)}
    for s in (alert_result.get("missing_guests") or []):
        missing_details[s] = {"seat_tier": get_seat_tier(s, room_id)}
    for h in hopping_list:
        to_vip = h.get("to_seat")
        from_std = h.get("from_seat")
        if to_vip:
            illegal_details[to_vip] = {
                "seat_tier": "VIP",
                "suspected_type": "vip_seat_hopping",
                "hopping_from": from_std,
                "same_headcount": bool(h.get("same_headcount")),
                "message": h.get("message") or f"Nghi vấn khách tự ý chuyển từ ghế Thường {from_std} lên ghế VIP {to_vip}",
            }
        if from_std:
            missing_details[from_std] = {
                "seat_tier": "STANDARD",
                "suspected_type": "vip_seat_hopping",
                "hopping_to": to_vip,
                "same_headcount": bool(h.get("same_headcount")),
                "message": h.get("message") or f"Nghi vấn khách rời ghế Thường {from_std} lên ghế VIP {to_vip}",
            }

    if alert_result.get("illegal_occupants"):
        save_alerts(room_id, show_id, "illegal_occupant", alert_result["illegal_occupants"], details_by_seat=illegal_details)
    if alert_result.get("missing_guests"):
        save_alerts(room_id, show_id, "missing_guest", alert_result["missing_guests"], details_by_seat=missing_details)
    if alert_result.get("over_capacity"):
        save_alerts(room_id, show_id, "over_capacity", [None])

    return {"auto_resolved_count": auto_resolved, "vip_seat_hopping": hopping_list}

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
    # Gắn thêm context (số vé đã quét, số người AI đếm, chùm ghế vi phạm, hạng ghế & VIP Seat Hopping)
    if alerts_list:
        try:
            grouped = get_grouped_active_alerts(room_id)
            meta_map = {(g["room_id"], g["show_id"]): g for g in grouped}
            for a in alerts_list:
                sid = a.get("seat_id")
                a["seat_tier"] = get_seat_tier(sid, a.get("room_id")) if sid else None
                parsed_detail = {}
                if a.get("detail"):
                    try:
                        parsed_detail = json.loads(a["detail"]) if isinstance(a["detail"], str) else dict(a["detail"])
                    except Exception:
                        parsed_detail = {}
                a["detail_parsed"] = parsed_detail
                a["suspected_type"] = parsed_detail.get("suspected_type")
                a["hopping_from"] = parsed_detail.get("hopping_from")
                a["hopping_to"] = parsed_detail.get("hopping_to")
                a["hopping_message"] = parsed_detail.get("message")

                g = meta_map.get((a.get("room_id"), a.get("show_id")))
                if g:
                    a["scanned_tickets_count"] = g["scanned_tickets_count"]
                    a["detected_people_count"] = g["detected_people_count"]
                    a["room_alert_count"] = g["total_alerts"]
                    a["room_illegal_seats"] = g["illegal_seats"]
                    a["room_missing_seats"] = g["missing_seats"]
                    a["all_alerted_seats"] = g["all_alerted_seats"]
                    a["vip_seat_hopping"] = g.get("vip_seat_hopping", [])
                    a["duplicate_scan_seats"] = g.get("duplicate_scan_seats", [])
                    a["forged_ticket_seats"] = g.get("forged_ticket_seats", [])
                else:
                    a["scanned_tickets_count"] = 0
                    a["detected_people_count"] = 0
                    a["room_alert_count"] = 1
                    a["room_illegal_seats"] = [a["seat_id"]] if a.get("seat_id") else []
                    a["room_missing_seats"] = []
                    a["all_alerted_seats"] = [a["seat_id"]] if a.get("seat_id") else []
                    a["vip_seat_hopping"] = []
                    a["duplicate_scan_seats"] = []
                    a["forged_ticket_seats"] = []
        except Exception:
            pass
    return alerts_list

def get_grouped_active_alerts(room_id: str = None) -> list:
    """Gom nhóm các cảnh báo đang mở (resolved = 0) theo từng Phòng & Suất chiếu.
    Mỗi nhóm cung cấp đầy đủ:
    1. scanned_tickets_count: Số vé đã quét của rạp này (Tập A)
    2. detected_people_count: Số người hiện có trong rạp (Camera AI đếm)
    3. all_alerted_seats: Danh sách các ghế được cảnh báo
    4. vip_seat_hopping: Các cặp nghi vấn tự ý chuyển từ ghế Thường lên ghế VIP (Lỗi 4)
    5. duplicate_scan_seats & forged_ticket_seats: Các ghế bị quét trùng đa thiết bị hoặc vé giả (Lỗi 1.1 & 1.2)
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
                    "duplicate_scan_seats": [],
                    "forged_ticket_seats": [],
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
            elif atype == "duplicate_scan" and sid:
                if sid not in g["duplicate_scan_seats"]:
                    g["duplicate_scan_seats"].append(sid)
            elif atype == "forged_ticket" and sid:
                if sid not in g["forged_ticket_seats"]:
                    g["forged_ticket_seats"].append(sid)
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
            g["duplicate_scan_seats"].sort()
            g["forged_ticket_seats"].sort()
            all_seats = list(dict.fromkeys(
                g["illegal_seats"] + g["missing_seats"] + g["duplicate_scan_seats"] + g["forged_ticket_seats"]
            ))

            # Suy luận VIP Seat Hopping trên tập ghế cảnh báo hiện hành của phòng
            illegal_vip = [s for s in g["illegal_seats"] if get_seat_tier(s, r_id) == "VIP"]
            missing_std = [s for s in g["missing_seats"] if get_seat_tier(s, r_id) == "STANDARD"]
            vip_seat_hopping = []
            for std_s, vip_s in zip(missing_std, illegal_vip):
                vip_seat_hopping.append({
                    "from_seat": std_s,
                    "to_seat": vip_s,
                    "from_tier": "STANDARD",
                    "to_tier": "VIP",
                    "same_headcount": detected_count == scanned_count,
                    "message": f"Nghi vấn khách tự ý chuyển từ ghế Thường {std_s} lên ghế VIP {vip_s}",
                })

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
                "duplicate_scan_seats": g["duplicate_scan_seats"],
                "forged_ticket_seats": g["forged_ticket_seats"],
                "vip_seat_hopping": vip_seat_hopping,
                "all_alerted_seats": all_seats,
                "over_capacity": g["over_capacity"],
            })

        return result
    finally:
        conn.close()

def resolve_room_alerts(
    room_id: str,
    show_id: str,
    resolution: str = "violation_handled",
    resolver_id: int = None,
) -> int:
    """Xử lý hàng loạt cảnh báo đang mở của một phòng & suất chiếu (UC06).
    Hỗ trợ 2 kết quả nghiệp vụ (Lỗi 3):
    - 'violation_handled': Đã nhắc nhở khách về đúng ghế / mời ra ngoài (chỉ đóng cảnh báo hiện tại).
    - 'ticket_verified': Xác nhận khách có vé hợp lệ bị sót quét -> bổ sung các ghế thuộc B \\ A
      vào Tập A (`tickets` với source='MANUAL_VERIFIED') để Mốc 2 và Mốc 3 không báo động giả lại.
    """
    clean_room = _normalize_room_id(room_id)
    clean_show = str(show_id).strip()
    clean_res = "ticket_verified" if str(resolution or "").strip().lower() == "ticket_verified" else "violation_handled"
    now_iso = datetime.datetime.now().astimezone().isoformat()
    conn = _connect()
    try:
        cursor = conn.cursor()
        if clean_res == "ticket_verified":
            open_illegal = cursor.execute(
                "SELECT DISTINCT seat_id FROM alerts WHERE room_id = ? AND show_id = ? AND resolved = 0 AND alert_type = 'illegal_occupant' AND seat_id IS NOT NULL",
                (clean_room, clean_show),
            ).fetchall()
            for row in open_illegal:
                sid = normalize_seat(row[0])
                if sid:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO tickets (room_id, show_id, ticket_id, seat_id, seat_tier, scanned_by_id, scanned_at, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'MANUAL_VERIFIED')
                        """,
                        (clean_room, clean_show, f"VERIFIED-{sid}", sid, get_seat_tier(sid, clean_room), resolver_id, now_iso),
                    )
        cursor.execute(
            """
            UPDATE alerts
            SET resolved = 1, resolution = ?, resolved_by_id = ?, resolved_at = ?
            WHERE room_id = ? AND show_id = ? AND resolved = 0
            """,
            (clean_res, resolver_id, now_iso, clean_room, clean_show),
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


def resolve_alert(
    alert_id: int,
    resolution: str = "violation_handled",
    resolver_id: int = None,
    single_only: bool = False,
):
    """Xử lý cảnh báo đơn lẻ hoặc theo phòng (UC06) kèm 2 lựa chọn kết quả (Lỗi 3):
    - 'violation_handled': Đã xử lý vi phạm (mời khách về đúng ghế / ra ngoài).
    - 'ticket_verified': Xác nhận khách có vé hợp lệ bị sót quét -> bổ sung ghế vào Tập A (`tickets`).
    """
    clean_res = "ticket_verified" if str(resolution or "").strip().lower() == "ticket_verified" else "violation_handled"
    now_iso = datetime.datetime.now().astimezone().isoformat()
    conn = _connect()
    try:
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT room_id, show_id, seat_id, alert_type FROM alerts WHERE id=?",
            (alert_id,),
        ).fetchone()
        if not row:
            return
        r_id, s_id, seat_id, a_type = row[0], row[1], row[2], row[3]

        if clean_res == "ticket_verified":
            if single_only or not (r_id and s_id):
                if seat_id and a_type == "illegal_occupant":
                    norm_s = normalize_seat(seat_id)
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO tickets (room_id, show_id, ticket_id, seat_id, seat_tier, scanned_by_id, scanned_at, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'MANUAL_VERIFIED')
                        """,
                        (r_id, s_id, f"VERIFIED-{norm_s}", norm_s, get_seat_tier(norm_s, r_id), resolver_id, now_iso),
                    )
            else:
                open_illegal = cursor.execute(
                    "SELECT DISTINCT seat_id FROM alerts WHERE room_id=? AND show_id=? AND resolved=0 AND alert_type='illegal_occupant' AND seat_id IS NOT NULL",
                    (r_id, s_id),
                ).fetchall()
                for ir in open_illegal:
                    norm_s = normalize_seat(ir[0])
                    if norm_s:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO tickets (room_id, show_id, ticket_id, seat_id, seat_tier, scanned_by_id, scanned_at, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'MANUAL_VERIFIED')
                            """,
                            (r_id, s_id, f"VERIFIED-{norm_s}", norm_s, get_seat_tier(norm_s, r_id), resolver_id, now_iso),
                        )

        if not single_only and r_id and s_id:
            cursor.execute(
                "UPDATE alerts SET resolved=1, resolution=?, resolved_by_id=?, resolved_at=? WHERE room_id=? AND show_id=? AND resolved=0",
                (clean_res, resolver_id, now_iso, r_id, s_id),
            )
        else:
            cursor.execute(
                "UPDATE alerts SET resolved=1, resolution=?, resolved_by_id=?, resolved_at=? WHERE id=?",
                (clean_res, resolver_id, now_iso, alert_id),
            )
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
        # Tự động tính ca làm việc theo giờ đăng nhập thực tế (kết hợp ca phân công nếu trong đệm ±30 phút)
        dyn_shift_code, dyn_shift_label = get_dynamic_shift(row["role"], assigned_shift=row["shift"])
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
