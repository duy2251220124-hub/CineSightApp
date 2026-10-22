import sqlite3
from database import DB_PATH, save_alerts

save_alerts("room1", "2026-10-09T18:00", "missing_guest", ["Z99"])

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT timestamp FROM alerts ORDER BY id DESC LIMIT 1")
print("Alert time in DB:", cursor.fetchone()[0])
conn.close()
