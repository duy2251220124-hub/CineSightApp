import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            room_id TEXT,
            show_id TEXT,
            ticket_id TEXT,
            seat_id TEXT,
            PRIMARY KEY (room_id, show_id, ticket_id)
        )
    ''')
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
