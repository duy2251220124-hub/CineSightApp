import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    # Insert default config if not exists
    cursor.execute("INSERT OR IGNORE INTO configs (key, value) VALUES ('capacity_threshold', '0')")
    conn.commit()
    conn.close()

def save_tickets(room_id: str, show_id: str, tickets: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if tickets:
        cursor.executemany(
            "INSERT OR IGNORE INTO tickets (room_id, show_id, ticket_id, seat_id) VALUES (?, ?, ?, ?)",
            [(room_id, show_id, t['ticket'], t['seat']) for t in tickets]
        )
    conn.commit()
    conn.close()

def get_seats(room_id: str, show_id: str) -> set:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM tickets WHERE room_id = ? AND show_id = ?", (room_id, show_id))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def get_tickets_list(room_id: str, show_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE room_id = ? AND show_id = ?", (room_id, show_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

init_db()

def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    conn = sqlite3.connect(DB_PATH)
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
            cursor.execute("INSERT INTO alerts (room_id, show_id, alert_type, seat_id) VALUES (?, ?, ?, ?)",
                          (room_id, show_id, alert_type, seat))
    conn.commit()
    conn.close()

def get_active_alerts(room_id: str = None):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    
    if room_id and room_id != "all":
        query += " AND room_id=?"
        params.append(room_id)
        
    if alert_type and alert_type != "all":
        query += " AND alert_type=?"
        params.append(alert_type)
        
    if status == "active":
        query += " AND resolved=0"
    elif status == "resolved":
        query += " AND resolved=1"
        
    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_alert(alert_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()

def get_configs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM configs")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_config(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configs (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_employees():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role, created_at FROM employees ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_employee(username: str, password: str, name: str, role: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (username, password, name, role) VALUES (?, ?, ?, ?)", (username, password, name, role))
    emp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return emp_id

def delete_employee(emp_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()
