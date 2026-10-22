import sys
import re

content = open('database.py', 'r', encoding='utf-8').read()

old_save_alerts = """def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    for seat in seats:
        cursor.execute("INSERT INTO alerts (room_id, show_id, alert_type, seat_id) VALUES (?, ?, ?, ?)",
                      (room_id, show_id, alert_type, seat))
    conn.commit()
    conn.close()"""

new_save_alerts = """def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    import datetime
    current_time = datetime.datetime.now().astimezone().isoformat()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        cursor = conn.cursor()
        for seat in seats:
            cursor.execute("INSERT INTO alerts (room_id, show_id, alert_type, seat_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                          (room_id, show_id, alert_type, seat, current_time))
        conn.commit()
    finally:
        conn.close()"""

content = content.replace(old_save_alerts, new_save_alerts)
open('database.py', 'w', encoding='utf-8').write(content)
