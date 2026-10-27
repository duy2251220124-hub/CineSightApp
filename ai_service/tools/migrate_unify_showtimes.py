"""Di trú CSDL: hợp nhất showtimes (cũ) + showtimes_v2 thành MỘT bảng `showtimes`.

- Sao lưu cinesight.db vào ai_service/backups/ trước khi thay đổi.
- Xóa bảng showtimes kiểu cũ (movie_name dạng chữ, dữ liệu mồi cứng), đổi tên showtimes_v2 -> showtimes.
- Tạo lại chỉ mục idx_showtimes_room_date / idx_showtimes_show_id.
- Chạy trong 1 transaction, kiểm tra số dòng sau khi đổi tên; lỗi thì rollback.
- Idempotent: chạy lần 2 sẽ báo "đã ở cấu trúc mới".
Dùng: python tools/migrate_unify_showtimes.py [--db đường_dẫn]
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AI_SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB = os.path.join(AI_SERVICE_DIR, "cinesight.db")


def cols(cur, table):
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})")]


def migrate(db_path):
    probe = sqlite3.connect(db_path)
    cur = probe.cursor()
    legacy = "movie_name" in cols(cur, "showtimes")
    has_v2 = bool(cols(cur, "showtimes_v2"))
    probe.close()

    if not has_v2 and not legacy:
        print("[OK] CSDL đã ở cấu trúc mới (một bảng showtimes). Không cần di trú.")
        return 0
    if not has_v2:
        print("[LỖI] Có bảng showtimes cũ nhưng không có showtimes_v2: dừng, không xóa gì.")
        return 2

    backup_dir = os.path.join(AI_SERVICE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup = os.path.join(backup_dir, f"cinesight_before_unify_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(db_path, backup)
    print(f"[BACKUP] {backup}")

    conn = sqlite3.connect(db_path)
    conn.isolation_level = None  # tự quản lý transaction
    cur = conn.cursor()
    try:
        n_v2 = cur.execute("SELECT COUNT(*) FROM showtimes_v2").fetchone()[0]
        cur.execute("BEGIN")
        if legacy:
            n_old = cur.execute("SELECT COUNT(*) FROM showtimes").fetchone()[0]
            cur.execute("DROP TABLE showtimes")
            print(f"[XÓA] Bảng showtimes cũ ({n_old} dòng, đã có bản sao lưu)")
        cur.execute("DROP INDEX IF EXISTS idx_showtimes_v2_room_date")
        cur.execute("DROP INDEX IF EXISTS idx_showtimes_v2_show_id")
        cur.execute("ALTER TABLE showtimes_v2 RENAME TO showtimes")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_showtimes_room_date ON showtimes(room_id, start_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_showtimes_show_id ON showtimes(show_id)")
        n_new = cur.execute("SELECT COUNT(*) FROM showtimes").fetchone()[0]
        if n_new != n_v2:
            raise RuntimeError(f"Số dòng lệch: {n_v2} -> {n_new}")
        cur.execute("COMMIT")
        print(f"[XONG] showtimes_v2 -> showtimes ({n_new} dòng giữ nguyên)")
        return 0
    except Exception as exc:
        cur.execute("ROLLBACK")
        print(f"[LỖI] Đã rollback, CSDL không đổi: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Hợp nhất showtimes + showtimes_v2")
    ap.add_argument("--db", default=DEFAULT_DB)
    sys.exit(migrate(ap.parse_args().db))
