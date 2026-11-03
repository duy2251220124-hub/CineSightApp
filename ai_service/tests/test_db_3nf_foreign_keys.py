import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    DB_PATH,
    authenticate_employee,
    create_incident,
    get_incident,
    list_incidents,
    resolve_incident,
)
from security import hash_password, is_password_hashed, verify_password


class TestDatabase3NFAndForeignKeys(unittest.TestCase):
    def test_0_passwords_are_pbkdf2_hashed(self):
        """Mọi mật khẩu trong bảng employees đều được băm chuẩn PBKDF2-HMAC-SHA256, không còn plaintext."""
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute("SELECT id, username, password FROM employees").fetchall()
            self.assertGreaterEqual(len(rows), 3)
            for emp_id, username, pw in rows:
                self.assertTrue(
                    is_password_hashed(pw),
                    f"Tài khoản {username} (id={emp_id}) vẫn chưa được băm PBKDF2!",
                )
        finally:
            conn.close()

        # Kiểm tra xác thực đúng và sai mật khẩu
        staff_uname = "khanh"
        staff_pw = f"{staff_uname}@1234"
        user_ok = authenticate_employee(staff_uname, staff_pw)
        self.assertIsNotNone(user_ok)
        self.assertEqual(user_ok["id"], 2)
        self.assertIsNone(authenticate_employee(staff_uname, "wrong_pass"))
        self.assertIsNone(authenticate_employee("non_existent", "123"))

        # Kiểm tra hàm hash/verify độc lập
        h = hash_password("secret_2026")
        self.assertTrue(is_password_hashed(h))
        self.assertTrue(verify_password("secret_2026", h))
        self.assertFalse(verify_password("secret_2027", h))

    def test_1_incidents_table_is_strictly_3nf(self):
        """Bảng incidents không còn 4 cột lưu thừa (reporter_name, reporter_role, shift_label, resolved_by_name)
        và có cột reporter_shift (snapshot ca trực lúc báo sự cố - Điểm 5)."""
        conn = sqlite3.connect(DB_PATH)
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(incidents)").fetchall()]
            self.assertNotIn("reporter_name", cols)
            self.assertNotIn("reporter_role", cols)
            self.assertNotIn("shift_label", cols)
            self.assertNotIn("resolved_by_name", cols)
            self.assertIn("reporter_id", cols)
            self.assertIn("reporter_shift", cols)
            self.assertIn("resolved_by_id", cols)
            self.assertIn("room_id", cols)
        finally:
            conn.close()

    def test_2_foreign_keys_declared_and_valid(self):
        """Mọi bảng nghiệp vụ (showtimes, tickets, alerts, incidents) đều có Khóa Ngoại và 0 vi phạm."""
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            for tbl in ("showtimes", "tickets", "alerts", "incidents"):
                fks = conn.execute(f"PRAGMA foreign_key_list({tbl})").fetchall()
                self.assertGreaterEqual(len(fks), 2, f"Bảng {tbl} thiếu Khóa Ngoại")
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            self.assertEqual(violations, [], f"Có vi phạm Khóa Ngoại: {violations}")
        finally:
            conn.close()

    def test_3_incidents_left_join_returns_full_contract(self):
        """list_incidents() và get_incident() nối bảng employees trả đủ các trường cho Mobile/Web."""
        items = list_incidents()
        self.assertGreater(len(items), 0)
        sample = items[0]
        for required_key in (
            "id",
            "category",
            "severity",
            "title",
            "room_id",
            "reporter_id",
            "reporter_name",
            "reporter_role",
            "shift_label",
            "status",
            "resolved_by_id",
            "resolved_by_name",
        ):
            self.assertIn(required_key, sample)

        single = get_incident(sample["id"])
        self.assertIsNotNone(single)
        self.assertEqual(single["reporter_name"], sample["reporter_name"])

    def test_4_ai_inference_logs_table_and_fk(self):
        """Bảng ai_inference_logs tồn tại, có yolo_time_ms & mapping_time_ms, và có Khóa Ngoại chuẩn."""
        conn = sqlite3.connect(DB_PATH)
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(ai_inference_logs)").fetchall()]
            self.assertIn("inference_time_ms", cols)
            self.assertIn("yolo_time_ms", cols)
            self.assertIn("mapping_time_ms", cols)
            self.assertIn("detected_heads_count", cols)
            fks = conn.execute("PRAGMA foreign_key_list(ai_inference_logs)").fetchall()
            self.assertGreaterEqual(len(fks), 2)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

