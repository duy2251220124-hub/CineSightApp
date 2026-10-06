import sys

with open(r'c:\CineSightApp\web_admin\src\pages\Dashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('await fetchAlerts()', 'await getActiveAlerts()')

with open(r'c:\CineSightApp\web_admin\src\pages\Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
