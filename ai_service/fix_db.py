import sys
content = open('database.py', 'r', encoding='utf-8').read()

old_add = """def add_employee(username: str, password: str, name: str, role: str, shift: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (username, password, name, role, shift) VALUES (?, ?, ?, ?, ?)", (username, password, name, role, shift))
    emp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return emp_id"""

new_add = """def add_employee(username: str, password: str, name: str, role: str, shift: str = None):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (username, password, name, role, shift) VALUES (?, ?, ?, ?, ?)", (username, password, name, role, shift))
        emp_id = cursor.lastrowid
        conn.commit()
        return emp_id
    finally:
        conn.close()"""

content = content.replace(old_add, new_add)
open('database.py', 'w', encoding='utf-8').write(content)
