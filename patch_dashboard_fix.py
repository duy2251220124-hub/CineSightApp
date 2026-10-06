import sys

with open(r'c:\CineSightApp\web_admin\src\pages\Dashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('className={server-dot }', 'className="server-dot"')
content = content.replace('a.created_at', 'a.timestamp')
content = content.replace('a.seat', 'a.seat_id')

with open(r'c:\CineSightApp\web_admin\src\pages\Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
