import sys
import re

content = open('database.py', 'r', encoding='utf-8').read()

old_func = """def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
    conn = sqlite3.connect(DB_PATH, timeout=10)
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
    conn.close()"""

new_func = """def save_alerts(room_id: str, show_id: str, alert_type: str, seats: list):
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
        conn.close()"""

# Because of unicode encoding mismatches with powershell vs python, I'll use regex if direct replace fails.
if old_func in content:
    content = content.replace(old_func, new_func)
else:
    # use regex
    pattern = r"def save_alerts.*?conn\.close\(\)"
    content = re.sub(pattern, new_func, content, flags=re.DOTALL)

open('database.py', 'w', encoding='utf-8').write(content)
