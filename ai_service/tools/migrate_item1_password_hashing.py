"""Di trú CSDL Hạng mục 1: Băm mật khẩu nhân viên trong bảng `employees` theo chuẩn PBKDF2-HMAC-SHA256.

- Tự động sao lưu `cinesight.db` vào `ai_service/backups/` trước khi thay đổi.
- Chuyển đổi toàn bộ mật khẩu chữ thường (plaintext) sang định dạng `pbkdf2_sha256$100000$<salt>$<hash>`.
- Idempotent: nếu mật khẩu đã được băm sẵn thì bỏ qua, không băm chồng 2 lần.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AI_SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, AI_SERVICE_DIR)

from security import hash_password, is_password_hashed, verify_password  # noqa: E402

DEFAULT_DB = os.path.join(AI_SERVICE_DIR, "cinesight.db")


def migrate(db_path=DEFAULT_DB):
    if not os.path.exists(db_path):
        print(f"[LỖI] Không tìm thấy file CSDL: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute("SELECT id, username, password FROM employees").fetchall()
    unhashed = [(emp_id, username, pw) for emp_id, username, pw in rows if not is_password_hashed(pw)]
    conn.close()

    if not unhashed:
        print("[OK] Toàn bộ mật khẩu trong bảng `employees` đã ở chuẩn PBKDF2-HMAC-SHA256. Không cần di trú lại.")
        return 0

    backup_dir = os.path.join(AI_SERVICE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(
        backup_dir, f"cinesight_before_item1_hash_{datetime.now():%Y%m%d_%H%M%S}.db"
    )
    shutil.copy2(db_path, backup_path)
    print(f"[BACKUP] Đã sao lưu CSDL an toàn tại: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.isolation_level = None
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        for emp_id, username, plain_pw in unhashed:
            hashed_pw = hash_password(plain_pw)
            if not verify_password(plain_pw, hashed_pw):
                raise RuntimeError(f"Kiểm tra đối chiếu hash thất bại cho tài khoản id={emp_id}")
            cur.execute("UPDATE employees SET password = ? WHERE id = ?", (hashed_pw, emp_id))
            print(f"  + Đã băm mật khẩuPBKDF2-SHA256 cho nhân viên ID={emp_id} (username='{username}')")

        cur.execute("COMMIT")
        print(f"[THÀNH CÔNG] Đã nâng cấp bảo mật mật khẩu cho {len(unhashed)} tài khoản nhân viên!")
        return 0
    except Exception as e:
        cur.execute("ROLLBACK")
        print(f"[ROLLBACK] Đã hoàn tác do lỗi: {e}")
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(migrate())

