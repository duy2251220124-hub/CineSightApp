import io
import json
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
import main
from database import (
    DB_PATH,
    create_incident,
    get_incident,
    resolve_incident,
    save_tickets,
    showtime_exists,
)
from seat_mapper import (
    generate_alerts,
    normalize_seat,
    process_ai_detections,
    to_show_id,
)
from security import create_token, verify_token


class TestSeatMapperAndSecurity(unittest.TestCase):
    def test_1_seat_mapper_helpers(self):
        """Kiểm thử to_show_id, normalize_seat, process_ai_detections và generate_alerts."""
        self.assertEqual(to_show_id("2026-10-27", "19:30"), "2026-10-27T19:30")
        self.assertEqual(to_show_id("27/10/2026", "8:30"), "2026-10-27T08:30")
        self.assertEqual(normalize_seat(" a 5 "), "A05")
        self.assertEqual(normalize_seat("b12"), "B12")

        fake_polygons = {
            "A01": [[100, 100], [200, 100], [200, 200], [100, 200]],
            "A02": [[300, 100], [400, 100], [400, 200], [300, 200]],
        }
        # 1 điểm nằm trong A01, 1 điểm nằm ngoài mọi ghế
        detected = [(150.0, 150.0), (50.0, 50.0)]
        tap_b = process_ai_detections(detected, fake_polygons)
        self.assertEqual(tap_b, {"A01"})

        # Tập A = {A02} (có vé nhưng vắng mặt), Tập B = {A01} (ngồi sai ghế / không vé)
        alerts = generate_alerts(
            set_A={"A02"},
            set_B=tap_b,
            room_id="room1",
            total_seats=2,
            total_detected_people=2,
            capacity_threshold=1,
        )
        self.assertEqual(alerts["illegal_occupants"], ["A01"])
        self.assertEqual(alerts["missing_guests"], ["A02"])
        self.assertTrue(alerts["over_capacity"])

    def test_2_bearer_token_signing_and_expiration(self):
        """Kiểm thử tạo, xác thực, giả mạo và hết hạn Bearer Token (Điểm 1A)."""
        tok = create_token(user_id=2, now=1_700_000_000)
        self.assertEqual(verify_token(tok, now=1_700_000_100), 2)
        # Quá hạn
        self.assertIsNone(verify_token(tok, now=1_700_200_000))
        # Giả mạo chữ ký
        tampered = tok[:-4] + "abcd"
        self.assertIsNone(verify_token(tampered, now=1_700_000_100))
        self.assertIsNone(verify_token("invalid.token.format"))


class TestApiAndStrictRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_1_login_returns_token_and_protects_admin_routes(self):
        """Điểm 1A: /api/v1/login trả về token; các API quản trị chặn 401/403 đúng vai trò."""
        # Đăng nhập bằng tài khoản Soát vé (duy / 123)
        res = self.client.post("/api/v1/login", json={"username": "duy", "password": "123"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("token", body)
        staff_token = body["token"]
        self.assertEqual(body["user"]["id"], 2)

        # Không gửi token -> 401 khi gọi POST /api/v1/configs
        res_unauth = self.client.post(
            "/api/v1/configs",
            json={"key": "capacity_threshold", "value": "50"},
        )
        self.assertEqual(res_unauth.status_code, 401)

        # Gửi token của Soát vé (không phải Quản lý) -> 403 khi gọi POST /api/v1/configs
        res_forbidden = self.client.post(
            "/api/v1/configs",
            json={"key": "capacity_threshold", "value": "50"},
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        self.assertEqual(res_forbidden.status_code, 403)

        # Token của Quản lý (id=1) -> 200 OK
        manager_token = create_token(user_id=1)
        old_cfg = self.client.get("/api/v1/configs").json()["configs"].get("capacity_threshold", "0")
        res_ok = self.client.post(
            "/api/v1/configs",
            json={"key": "capacity_threshold", "value": str(old_cfg)},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(res_ok.status_code, 200)

    def test_2_point_4a_rejects_nonexistent_showtime(self):
        """Điểm 4A: Không tự động bịa suất chiếu ma khi đồng bộ vé hoặc phân tích ảnh."""
        fake_show = "2099-12-31T23:55"
        self.assertFalse(showtime_exists("room1", fake_show))

        with self.assertRaises(ValueError):
            save_tickets("room1", fake_show, [{"ticket": "T-999", "seat": "A1"}])

        res = self.client.post(
            "/api/v1/sync_tickets",
            data={
                "room_id": "room1",
                "show_id": fake_show,
                "scanned_tickets": json.dumps([{"ticket": "T-999", "seat": "A1"}]),
            },
        )
        self.assertEqual(res.status_code, 404)

    def test_3_point_5_incident_shift_snapshot_and_strict_employee_check(self):
        """Điểm 5: Lưu snapshot ca trực lúc báo sự cố và từ chối reporter_id/resolver_id ảo."""
        # reporter_id không tồn tại -> raise ValueError thay vì tự gán cho admin (id=1)
        with self.assertRaises(ValueError):
            create_incident(
                category="seat_damage",
                severity="low",
                title="Test",
                description="Desc",
                room_id="room1",
                show_id=None,
                seat_ids="[]",
                reporter_id=999999,
            )

        with self.assertRaises(ValueError):
            resolve_incident(incident_id=1, resolver_id=999999)

        # Kiểm tra snapshot ca trực: Tạo sự cố với ca 'ca_sang', sau đó dù đổi ca nhân viên thì sự cố cũ vẫn giữ 'Ca sáng'
        conn = sqlite3.connect(DB_PATH)
        inc_id = None
        orig_shift = None
        try:
            orig_shift = conn.execute("SELECT shift FROM employees WHERE id=2").fetchone()[0]
            inc_id = create_incident(
                category="seat_damage",
                severity="medium",
                title="Snapshot Shift Test",
                description="Testing shift snapshot",
                room_id="room1",
                show_id=None,
                seat_ids='["A1"]',
                reporter_id=2,
                reporter_shift="ca_sang",
            )
            # Giả sử nhân viên id=2 đổi sang ca_toi
            conn.execute("UPDATE employees SET shift='ca_toi' WHERE id=2")
            conn.commit()

            inc_data = get_incident(inc_id)
            self.assertEqual(inc_data["shift_label"], "Ca sáng")
        finally:
            if orig_shift is not None:
                conn.execute("UPDATE employees SET shift=? WHERE id=2", (orig_shift,))
            if inc_id is not None:
                conn.execute("DELETE FROM incidents WHERE id=?", (inc_id,))
            conn.commit()
            conn.close()

    def test_4_points_8_and_9_analyze_validation(self):
        """Điểm 8 & 9: /api/v1/analyze trả 503 khi model=None và 400 khi file ảnh hỏng/rỗng."""
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT room_id, show_id FROM showtimes WHERE status='scheduled' LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        valid_room, valid_show = row[0], row[1]

        # Điểm 9: Gửi file text giả làm ảnh -> 400 Bad Request (không crash 500)
        res_bad_img = self.client.post(
            "/api/v1/analyze",
            data={"room_id": valid_room, "show_id": valid_show},
            files={"image": ("corrupt.jpg", io.BytesIO(b"not-a-valid-jpeg-binary"), "image/jpeg")},
        )
        self.assertEqual(res_bad_img.status_code, 400)

        # Điểm 8: Giả lập model = None -> 503 Service Unavailable
        saved_model = main.model
        try:
            main.model = None
            res_no_model = self.client.post(
                "/api/v1/analyze",
                data={"room_id": valid_room, "show_id": valid_show},
                files={"image": ("test.jpg", io.BytesIO(b"123"), "image/jpeg")},
            )
            self.assertEqual(res_no_model.status_code, 503)
        finally:
            main.model = saved_model


if __name__ == "__main__":
    unittest.main()
