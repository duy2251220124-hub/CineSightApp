import sqlite3

db_path = r"C:\CineSightApp\ai_service\cinesight.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name")
tables = [row[0] for row in cur.fetchall()]

print("=" * 60)
print(f"CSDL: {db_path}")
print("=" * 60)

for table in tables:
    cur.execute(f"SELECT count(*) FROM {table}")
    count = cur.fetchone()[0]
    
    cur.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in cur.fetchall()]
    
    print(f"\n[BẢNG: {table}] - {count} bản ghi")
    print("Các cột:", ", ".join(cols))
    
    # In 2 dòng mẫu
    cur.execute(f"SELECT * FROM {table} LIMIT 2")
    sample_rows = cur.fetchall()
    for row in sample_rows:
        print("  ->", row)

