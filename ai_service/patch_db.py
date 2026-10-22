import os
import re

db_path = "C:/CineSightApp/ai_service/database.py"
with open(db_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update init_db
old_init = """        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            role TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Insert default config"""

new_init = """        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            role TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    cursor.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'shift' not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN shift TEXT NULL")
        
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            severity TEXT,
            title TEXT,
            description TEXT,
            room_id TEXT,
            show_id TEXT,
            seat_ids TEXT,
            reporter_id INTEGER,
            reporter_name TEXT,
            reporter_role TEXT,
            shift_label TEXT,
            created_at TEXT,
            status TEXT,
            resolved_by_id INTEGER NULL,
            resolved_by_name TEXT NULL,
            resolved_at TEXT NULL
        )
    \"\"\")
    # Insert default config"""

content = content.replace(old_init, new_init)

# 2. Update employee functions
old_employees = """def get_employees():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, name, role, created_at FROM employees ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_employee(username: str, password: str, name: str, role: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (username, password, name, role) VALUES (?, ?, ?, ?)", (username, password, name, role))
    emp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return emp_id

def update_employee(emp_id: int, username: str, password: str, name: str, role: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET username=?, password=?, name=?, role=? WHERE id=?", (username, password, name, role, emp_id))
    conn.commit()
    conn.close()"""

new_employees = """def get_employees():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, name, role, created_at, shift FROM employees ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_employee(emp_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_employee(username: str, password: str, name: str, role: str, shift: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (username, password, name, role, shift) VALUES (?, ?, ?, ?, ?)", (username, password, name, role, shift))
    emp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return emp_id

def update_employee(emp_id: int, username: str, password: str, name: str, role: str, shift: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET username=?, password=?, name=?, role=?, shift=? WHERE id=?", (username, password, name, role, shift, emp_id))
    conn.commit()
    conn.close()"""

content = content.replace(old_employees, new_employees)

# 3. Add incident functions
incidents_code = """
def create_incident(category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_name, reporter_role, shift_label, created_at, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        INSERT INTO incidents 
        (category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_name, reporter_role, shift_label, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    \"\"\", (category, severity, title, description, room_id, show_id, seat_ids, reporter_id, reporter_name, reporter_role, shift_label, created_at, status))
    incident_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return incident_id

def list_incidents(room_id=None, status=None, category=None, from_time=None, to_time=None, limit=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM incidents WHERE 1=1"
    params = []
    
    if room_id:
        query += " AND room_id=?"
        params.append(room_id)
    if status:
        query += " AND status=?"
        params.append(status)
    if category:
        query += " AND category=?"
        params.append(category)
    if from_time:
        query += " AND created_at >= ?"
        params.append(from_time)
    if to_time:
        query += " AND created_at <= ?"
        params.append(to_time)
        
    query += " ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
        
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_incident(incident_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE id=?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def resolve_incident(incident_id: int, resolver_id: int, resolver_name: str, resolved_at: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        UPDATE incidents 
        SET status='resolved', resolved_by_id=?, resolved_by_name=?, resolved_at=? 
        WHERE id=?
    \"\"\", (resolver_id, resolver_name, resolved_at, incident_id))
    conn.commit()
    conn.close()
"""

if "def create_incident" not in content:
    content += incidents_code

with open(db_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Patched database.py")
