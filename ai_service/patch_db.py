import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type=? AND resolved=0", \n                      (room_id, show_id, seat, alert_type))',
    '''if seat is None:
            cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id IS NULL AND alert_type=? AND resolved=0", 
                          (room_id, show_id, alert_type))
        else:
            cursor.execute("SELECT id FROM alerts WHERE room_id=? AND show_id=? AND seat_id=? AND alert_type=? AND resolved=0", 
                          (room_id, show_id, seat, alert_type))'''
)

if 'def resolve_alert' not in content:
    content += '''

def resolve_alert(alert_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
'''

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
