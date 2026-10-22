import sqlite3
from database import DB_PATH
import datetime

conn = sqlite3.connect(DB_PATH, timeout=10)
cursor = conn.cursor()
cursor.execute("INSERT INTO alerts (room_id, show_id, alert_type, seat_id) VALUES (?, ?, ?, ?)", ("room1", "2026-10-09T18:00", "over_capacity", None))
alert_id = cursor.lastrowid
conn.commit()

cursor.execute("SELECT timestamp FROM alerts WHERE id=?", (alert_id,))
timestamp = cursor.fetchone()[0]
conn.close()

print("Múi giờ máy:", datetime.datetime.now().astimezone().isoformat())
print("Giờ lưu trong DB của alerts (UTC):", timestamp)
