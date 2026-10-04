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

init_db()

def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Chỉ lưu nếu ghế chưa có cảnh báo chưa giải quyết
    for seat in seats:
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
