import re
content = open('database.py', 'r', encoding='utf-8').read()
content = re.sub(r'try:\\n\s*cursor\.execute.*?finally:\\n\s*conn\.close\(\)', '''try:
        cursor.execute("INSERT INTO employees (username, password, name, role, shift) VALUES (?, ?, ?, ?, ?)", (username, password, name, role, shift))
        emp_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()''', content)
open('database.py', 'w', encoding='utf-8').write(content)
