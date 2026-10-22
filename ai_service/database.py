import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            room_id TEXT,
            show_id TEXT,
            ticket_id TEXT,
            seat_id TEXT,
            PRIMARY KEY (room_id, show_id, ticket_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT,
            show_id TEXT,
            alert_type TEXT,
            seat_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'shift' not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN shift TEXT NULL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            severity TEXT,
            title TEXT,
            description TEXT,
            room_id TEXT,
            show_id TEXT,
            seat_ids TEXT,
            reporter_id INTEGER,
            reporter_name TEXT,
            reporter_role TEXT,
            shift_label TEXT,
            created_at TEXT,
            status TEXT,
            resolved_by_id INTEGER NULL,
            resolved_by_name TEXT NULL,
            resolved_at TEXT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS showtimes (
            show_id TEXT,
            room_id TEXT,
            room_name TEXT,
            movie_name TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_minutes INTEGER,
            break_minutes INTEGER,
            date TEXT,
            PRIMARY KEY (room_id, show_id)
        )
    """)

    # Insert default config if not exists
    cursor.execute("INSERT OR IGNORE INTO configs (key, value) VALUES ('capacity_threshold', '0')")
    conn.commit()
    conn.close()

def save_tickets(room_id: str, show_id: str, tickets: list):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    if tickets:
        cursor.executemany(
            "INSERT OR IGNORE INTO tickets (room_id, show_id, ticket_id, seat_id) VALUES (?, ?, ?, ?)",
            [(room_id, show_id, t['ticket'], t['seat']) for t in tickets]
        )
    conn.commit()
    conn.close()

def get_seats(room_id: str, show_id: str) -> set:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM tickets WHERE room_id = ? AND show_id = ?", (room_id, show_id))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def get_tickets_list(room_id: str, show_id: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if show_id and show_id not in ("undefined", "null", ""):
        cursor.execute("SELECT * FROM tickets WHERE room_id = ? AND show_id = ?", (room_id, show_id))
    else:
        cursor.execute("SELECT * FROM tickets WHERE room_id = ?", (room_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_tickets(room_id: str = None, show_id: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    if room_id and show_id and str(show_id) not in ('undefined', 'null', ''):
        cursor.execute('DELETE FROM tickets WHERE room_id = ? AND show_id = ?', (room_id, show_id))
    elif room_id and str(room_id) not in ('undefined', 'null', ''):
        cursor.execute('DELETE FROM tickets WHERE room_id = ?', (room_id,))
    else:
        cursor.execute('DELETE FROM tickets')
    conn.commit()
    conn.close()

init_db()

def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    import datetime
    current_time = datetime.datetime.now().astimezone().isoformat()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        cursor = conn.cursor()
        # Chỉ lưu nếu ghế chưa có cảnh báo chưa giải quyết
        for seat in seats:
            if seat is None:
                cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id IS NULL AND alert_type=? AND resolved=0", 
                              (room_id, show_id, alert_type))
            else:
                cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type=? AND resolved=0", 
                              (room_id, show_id, seat, alert_type))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO alerts (room_id, show_id, alert_type, seat_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                              (room_id, show_id, alert_type, seat, current_time))
        conn.commit()
    finally:
        conn.close()

def get_active_alerts(room_id: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if room_id:
        cursor.execute("SELECT * FROM alerts WHERE room_id=? AND resolved=0 ORDER BY timestamp DESC", (room_id,))
    else:
        cursor.execute("SELECT * FROM alerts WHERE resolved=0 ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_alerts(room_id: str = None, alert_type: str = None, status: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    
    if room_id and str(room_id).lower() != "all":
        query += " AND room_id=?"
        params.append(room_id)
        
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
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
        conn.commit()
    finally:
        conn.close()

def get_configs():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM configs")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_config(key: str, value: str):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configs (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_employees():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role, created_at, shift FROM employees ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_employee(emp_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_employee(username: str, password: str, name: str, role: str, shift: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO employees (username, password, name, role, shift) VALUES (?, ?, ?, ?, ?)", (username, password, name, role, shift))
        emp_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return emp_id

def update_employee(emp_id: int, username: str, password: str, name: str, role: str, shift: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    if password and str(password).strip():
        cursor.execute("UPDATE employees SET username=?, password=?, name=?, role=?, shift=? WHERE id=?", (username, password, name, role, shift, emp_id))
    else:
        cursor.execute("UPDATE employees SET username=?, name=?, role=?, shift=? WHERE id=?", (username, name, role, shift, emp_id))
    conn.commit()
    conn.close()

def delete_employee(emp_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()

def create_incident(category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_name, reporter_role, shift_label, created_at, status):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidents 
        (category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_name, reporter_role, shift_label, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_name, reporter_role, shift_label, created_at, status))
    incident_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return incident_id

def list_incidents(room_id=None, status=None, category=None, from_time=None, to_time=None, limit=None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM incidents WHERE 1=1"
    params = []
    
    if room_id:
        query += " AND room_id=?"
        params.append(room_id)
    if status:
        query += " AND status=?"
        params.append(status)
    if category:
        query += " AND category=?"
        params.append(category)
    if from_time:
        query += " AND created_at >= ?"
        params.append(from_time)
    if to_time:
        query += " AND created_at <= ?"
        params.append(to_time)
        
    query += " ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
        
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_incident(incident_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE id=?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def resolve_incident(incident_id: int, resolver_id: int, resolver_name: str, resolved_at: str):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE incidents 
        SET status='resolved', resolved_by_id=?, resolved_by_name=?, resolved_at=? 
        WHERE id=?
    """, (resolver_id, resolver_name, resolved_at, incident_id))
    conn.commit()
    conn.close()


# Quy định lịch chiếu chuẩn cho 4 phòng chiếu:
# - Bắt đầu lúc 08:30 sáng
# - Thời lượng phim từ 105 phút (1h45p) đến 120 phút (2h00p)
# - Thời gian nghỉ dọn phòng giữa 2 suất liên tiếp: 10 phút
DEFAULT_ROOM_SCHEDULES = {
    "room1": {
        "room_name": "Phòng chiếu 1",
        "shows": [
            {"start": "08:30", "end": "10:15", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "10:25", "end": "12:10", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "12:20", "end": "14:05", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "14:15", "end": "16:00", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "16:10", "end": "17:55", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "18:05", "end": "19:50", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "20:00", "end": "22:00", "duration": 120, "movie": "Spider-Man: Brand New Day"},
            {"start": "22:10", "end": "00:10", "duration": 120, "movie": "Spider-Man: Brand New Day"},
        ],
    },
    "room2": {
        "room_name": "Phòng chiếu 2",
        "shows": [
            {"start": "08:30", "end": "10:30", "duration": 120, "movie": "Spider-Man: Brand New Day"},
            {"start": "10:40", "end": "12:40", "duration": 120, "movie": "The Odyssey"},
            {"start": "12:50", "end": "14:50", "duration": 120, "movie": "The Odyssey"},
            {"start": "15:00", "end": "16:50", "duration": 110, "movie": "Insidious: Out Of The Dark"},
            {"start": "17:00", "end": "18:50", "duration": 110, "movie": "Insidious: Out Of The Dark"},
            {"start": "19:00", "end": "20:50", "duration": 110, "movie": "Insidious: Out Of The Dark"},
            {"start": "21:00", "end": "22:50", "duration": 110, "movie": "Insidious: Out Of The Dark"},
        ],
    },
    "room3": {
        "room_name": "Phòng chiếu 3",
        "shows": [
            {"start": "08:30", "end": "10:20", "duration": 110, "movie": "Nghỉ Hè Sợ Nghỉ"},
            {"start": "10:30", "end": "12:20", "duration": 110, "movie": "Nghỉ Hè Sợ Nghỉ"},
            {"start": "12:30", "end": "14:20", "duration": 110, "movie": "Nghỉ Hè Sợ Nghỉ"},
            {"start": "14:30", "end": "16:20", "duration": 110, "movie": "Nghỉ Hè Sợ Nghỉ"},
            {"start": "16:30", "end": "18:20", "duration": 110, "movie": "Nghỉ Hè Sợ Nghỉ"},
            {"start": "18:30", "end": "20:20", "duration": 110, "movie": "Nghỉ Hè Sợ Nghỉ"},
            {"start": "20:30", "end": "22:15", "duration": 105, "movie": "The Djinn's Curse"},
            {"start": "22:25", "end": "00:10", "duration": 105, "movie": "The Djinn's Curse"},
        ],
    },
    "room4": {
        "room_name": "Phòng chiếu 4",
        "shows": [
            {"start": "08:30", "end": "10:20", "duration": 110, "movie": "Insidious: Out Of The Dark"},
            {"start": "10:30", "end": "12:25", "duration": 115, "movie": "(Rerun 2026) One Piece Film: Red"},
            {"start": "12:35", "end": "14:20", "duration": 105, "movie": "The Djinn's Curse"},
            {"start": "14:30", "end": "16:20", "duration": 110, "movie": "The End Of Oasis"},
            {"start": "16:30", "end": "18:15", "duration": 105, "movie": "2DDUB Paw Patrol"},
            {"start": "18:25", "end": "20:10", "duration": 105, "movie": "2DDUB Crayon Shinchan"},
            {"start": "20:20", "end": "22:10", "duration": 110, "movie": "Whistle"},
            {"start": "22:20", "end": "00:10", "duration": 110, "movie": "Whistle"},
        ],
    },
}


def seed_default_showtimes(date_str: str = None):
    import datetime
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    rows_to_insert = []
    for room_id, cfg in DEFAULT_ROOM_SCHEDULES.items():
        room_name = cfg["room_name"]
        for s in cfg["shows"]:
            show_id = f"{date_str}T{s['start']}"
            rows_to_insert.append((
                show_id,
                room_id,
                room_name,
                s["movie"],
                s["start"],
                s["end"],
                s["duration"],
                10,
                date_str,
            ))

    cursor.executemany("""
        INSERT OR IGNORE INTO showtimes
        (show_id, room_id, room_name, movie_name, start_time, end_time, duration_minutes, break_minutes, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)
    conn.commit()
    conn.close()


def get_showtimes(room_id: str = None, date: str = None):
    import datetime
    target_date = date.strip() if date else datetime.date.today().strftime("%Y-%m-%d")
    seed_default_showtimes(target_date)

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM showtimes WHERE date = ?"
    params = [target_date]
    if room_id and room_id.lower() != "all":
        query += " AND room_id = ?"
        params.append(room_id)
    query += " ORDER BY room_id ASC, start_time ASC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_showtime(room_id: str, date: str, start_time: str, duration_minutes: int, movie_name: str, break_minutes: int = 10):
    import datetime
    dt_start = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    dt_end = dt_start + datetime.timedelta(minutes=duration_minutes)
    end_time = dt_end.strftime("%H:%M")
    show_id = f"{date}T{start_time}"
    room_num = room_id.replace("room", "")
    room_name = f"Phòng chiếu {room_num}" if room_num.isdigit() else room_id

    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO showtimes
        (show_id, room_id, room_name, movie_name, start_time, end_time, duration_minutes, break_minutes, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (show_id, room_id, room_name, movie_name, start_time, end_time, duration_minutes, break_minutes, date))
    conn.commit()
    conn.close()
    return {
        "show_id": show_id,
        "room_id": room_id,
        "room_name": room_name,
        "movie_name": movie_name,
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "break_minutes": break_minutes,
        "date": date,
    }



