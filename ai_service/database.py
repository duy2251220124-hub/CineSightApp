import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            room_id TEXT,
            ticket_id TEXT,
            PRIMARY KEY (room_id, ticket_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_tickets(room_id: str, tickets: set):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE room_id = ?", (room_id,))
    if tickets:
        cursor.executemany(
            "INSERT INTO tickets (room_id, ticket_id) VALUES (?, ?)",
            [(room_id, t) for t in tickets]
        )
    conn.commit()
    conn.close()

def get_tickets(room_id: str) -> set:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM tickets WHERE room_id = ?", (room_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

init_db()
