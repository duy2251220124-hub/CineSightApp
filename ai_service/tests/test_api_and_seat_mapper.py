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
        # Đăng nhập bằng tài khoản Soát vé trên Mobile App -> 200 OK
        staff_uname = "khanh"
        staff_pw = f"{staff_uname}@1234"
        res = self.client.post("/api/v1/login", json={"username": staff_uname, "password": staff_pw})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("token", body)
        staff_token = body["token"]
        self.assertEqual(body["user"]["id"], 2)

        # Đăng nhập bằng tài khoản Soát vé trên Web Admin (client='web_admin') -> 403 Forbidden
        res_web_staff = self.client.post(
            "/api/v1/login",
            json={"username": staff_uname, "password": staff_pw, "client": "web_admin"},
        )
        self.assertEqual(res_web_staff.status_code, 403)

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

        # Gọi /api/v1/sync_tickets không có token -> 401
        res_unauth = self.client.post(
            "/api/v1/sync_tickets",
            data={
                "room_id": "room1",
                "show_id": fake_show,
                "scanned_tickets": json.dumps([{"ticket": "T-999", "seat": "A1"}]),
            },
        )
        self.assertEqual(res_unauth.status_code, 401)

        # Có token hợp lệ -> kiểm tra suất chiếu ma -> 404
        staff_token = create_token(user_id=2)
        res = self.client.post(
            "/api/v1/sync_tickets",
            data={
                "room_id": "room1",
                "show_id": fake_show,
                "scanned_tickets": json.dumps([{"ticket": "T-999", "seat": "A1"}]),
            },
            headers={"Authorization": f"Bearer {staff_token}"},
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
                "SELECT room_id, show_id FROM showtimes WHERE status='scheduled' ORDER BY end_at DESC LIMIT 1"
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



    def test_5_issue6_employee_isolation_peer_protection_and_soft_deactivate(self):
        """Vấn đề 6: Lọc danh sách nhân viên, bảo vệ đồng cấp Quản lý, chống tự xóa và soft-deactivate khi có sự cố."""
        from database import add_employee, get_employee
        conn = sqlite3.connect(DB_PATH)
        mgr_b_id = None
        staff_inc_id = None
        staff_clean_id = None
        inc_id = None
        try:
            # Dọn sạch dữ liệu thử nghiệm cũ nếu có
            conn.execute("DELETE FROM incidents WHERE title LIKE 'zz_%'")
            conn.execute("DELETE FROM employees WHERE username LIKE 'zz_%'")
            conn.commit()

            # Tạo Quản lý B trực tiếp trong DB (vì API chặn tạo Quản lý)
            mgr_b_id = add_employee("zz_mgr_b", "pass123", "zz_Quản Lý B", "Quản lý", "ca_sang")
            staff_inc_id = add_employee("zz_staff_inc", "pass123", "zz_Nhân Viên Có Sự Cố", "Soát vé", "ca_sang")
            staff_clean_id = add_employee("zz_staff_clean", "pass123", "zz_Nhân Viên Sạch", "Soát vé", "ca_toi")

            mgr_a_token = create_token(user_id=1)  # Quản lý A (id=1)

            # 1. Quản lý gọi POST /api/v1/employees với role="Quản lý" -> 403
            res_create_mgr = self.client.post(
                "/api/v1/employees",
                json={
                    "username": "zz_mgr_illegal",
                    "password": "123",
                    "name": "zz_Illegal Manager",
                    "role": "Quản lý",
                    "shift": "ca_sang",
                },
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_create_mgr.status_code, 403)

            # 2. Quản lý A gọi PUT hoặc DELETE lên Quản lý B -> 403
            res_put_peer = self.client.put(
                f"/api/v1/employees/{mgr_b_id}",
                json={
                    "username": "zz_mgr_b",
                    "password": "",
                    "name": "zz_Hacked Name",
                    "role": "Quản lý",
                    "shift": "ca_toi",
                },
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_put_peer.status_code, 403)

            res_del_peer = self.client.delete(
                f"/api/v1/employees/{mgr_b_id}",
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_del_peer.status_code, 403)

            # 3. Quản lý A tự gọi DELETE lên chính mình -> 403
            res_del_self = self.client.delete(
                "/api/v1/employees/1",
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_del_self.status_code, 403)

            # 4. GET /api/v1/employees với token của Quản lý A -> chỉ thấy Soát vé + chính Quản lý A (không lộ Quản lý B)
            res_list = self.client.get(
                "/api/v1/employees",
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_list.status_code, 200)
            emps = res_list.json()["employees"]
            returned_ids = {e["id"] for e in emps}
            self.assertIn(1, returned_ids)
            self.assertIn(staff_inc_id, returned_ids)
            self.assertNotIn(mgr_b_id, returned_ids)
            for e in emps:
                self.assertNotIn("password", e)
                self.assertIn("is_active", e)
                self.assertIn("last_seen_at", e)
                self.assertIn("is_online", e)
                if e["id"] != 1:
                    self.assertNotEqual(e["role"], "Quản lý")

            # 5. Xóa nhân viên Soát vé ĐÃ CÓ biên bản sự cố -> soft-deactivate (is_active = 0), đăng nhập bị từ chối (401)
            inc_id = create_incident(
                category="seat_damage",
                severity="low",
                title="zz_Test Incident For Soft Delete",
                description="zz_desc",
                room_id="room1",
                show_id=None,
                seat_ids='["A01"]',
                reporter_id=staff_inc_id,
            )
            res_soft_del = self.client.delete(
                f"/api/v1/employees/{staff_inc_id}",
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_soft_del.status_code, 200)
            self.assertEqual(res_soft_del.json().get("action"), "deactivated")

            deactivated_emp = get_employee(staff_inc_id)
            self.assertIsNotNone(deactivated_emp)
            self.assertEqual(deactivated_emp["is_active"], 0)

            res_login_deactivated = self.client.post(
                "/api/v1/login",
                json={"username": "zz_staff_inc", "password": "pass123"},
            )
            self.assertEqual(res_login_deactivated.status_code, 401)

            # Token cũ của nhân viên đã bị ngưng hoạt động cũng bị từ chối
            dead_token = create_token(user_id=staff_inc_id)
            res_dead_token = self.client.delete(
                "/api/v1/tickets",
                headers={"Authorization": f"Bearer {dead_token}"},
            )
            self.assertEqual(res_dead_token.status_code, 401)

            # 6. Xóa nhân viên Soát vé CHƯA CÓ biên bản sự cố -> xóa vật lý (deleted)
            res_hard_del = self.client.delete(
                f"/api/v1/employees/{staff_clean_id}",
                headers={"Authorization": f"Bearer {mgr_a_token}"},
            )
            self.assertEqual(res_hard_del.status_code, 200)
            self.assertEqual(res_hard_del.json().get("action"), "deleted")
            self.assertIsNone(get_employee(staff_clean_id))
        finally:
            if inc_id is not None:
                conn.execute("DELETE FROM incidents WHERE id=?", (inc_id,))
            conn.execute("DELETE FROM incidents WHERE title LIKE 'zz_%'")
            conn.execute("DELETE FROM employees WHERE username LIKE 'zz_%'")
            conn.commit()
            conn.close()

    def test_6_issues_2_and_3_dual_auth_and_image_quality_clahe(self):
        """Vấn đề 2 & 3: Dual Auth cho /api/v1/analyze và tiền kiểm tra chất lượng ảnh + CLAHE."""
        import numpy as np
        import cv2

        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT room_id, show_id FROM showtimes WHERE status='scheduled' ORDER BY end_at DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        valid_room, valid_show = row[0], row[1]

        # Tạo 1 ảnh tối & phẳng (brightness < 40, sharpness < 35)
        dark_img = np.full((120, 160, 3), 10, dtype=np.uint8)
        ok, buf = cv2.imencode(".jpg", dark_img)
        self.assertTrue(ok)
        img_bytes = buf.tobytes()

        # 1. Request từ ngoài Internet (có X-Forwarded-For) nhưng KHÔNG có Token và KHÔNG có X-Camera-Key -> 401
        res_ext_unauth = self.client.post(
            "/api/v1/analyze",
            data={"room_id": valid_room, "show_id": valid_show},
            files={"image": ("dark.jpg", io.BytesIO(img_bytes), "image/jpeg")},
            headers={"X-Forwarded-For": "203.0.113.50"},
        )
        self.assertEqual(res_ext_unauth.status_code, 401)

        conn_clean = sqlite3.connect(DB_PATH)
        try:
            max_log_row = conn_clean.execute("SELECT COALESCE(MAX(id), 0) FROM ai_inference_logs").fetchone()
            max_alert_row = conn_clean.execute("SELECT COALESCE(MAX(id), 0) FROM alerts").fetchone()
            max_log_id = max_log_row[0] if max_log_row else 0
            max_alert_id = max_alert_row[0] if max_alert_row else 0

            # 2. Request có X-Camera-Key hợp lệ -> 200 OK và trả về image_quality có LOW_LIGHT, LOW_SHARPNESS, clahe_applied=True
            res_cam_ok = self.client.post(
                "/api/v1/analyze",
                data={"room_id": valid_room, "show_id": valid_show},
                files={"image": ("dark.jpg", io.BytesIO(img_bytes), "image/jpeg")},
                headers={
                    "X-Forwarded-For": "203.0.113.50",
                    "X-Camera-Key": "CINESIGHT_CAM_SECURE_2026",
                },
            )
            self.assertEqual(res_cam_ok.status_code, 200)
            summary = res_cam_ok.json()["summary"]
            self.assertIn("image_quality", summary)
            iq = summary["image_quality"]
            self.assertTrue(iq["clahe_applied"])
            self.assertIn("LOW_LIGHT", iq["warnings"])
            self.assertIn("LOW_SHARPNESS", iq["warnings"])
        finally:
            conn_clean.execute("DELETE FROM ai_inference_logs WHERE image_width=160 AND image_height=120")
            conn_clean.execute("DELETE FROM ai_inference_logs WHERE id > ?", (max_log_id,))
            conn_clean.execute("DELETE FROM alerts WHERE id > ?", (max_alert_id,))
            conn_clean.commit()
            conn_clean.close()



    def test_7_issue12_scheduler_time_warp_and_idempotent_alert_refresh(self):
        """Vấn đề 12: Bộ lập lịch Time-Warp T-3 phút (AUTO_T_MINUS_3) và tự động gỡ cảnh báo cũ khi khách vào muộn (Idempotent Alert Refresh)."""
        from database import refresh_showtime_alerts, get_active_alerts, get_inference_logs
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT room_id, show_id FROM showtimes WHERE status='scheduled' ORDER BY end_at DESC LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(row)
            valid_room, valid_show = row[0], row[1]

            max_log_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM ai_inference_logs").fetchone()[0]
            max_alert_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM alerts").fetchone()[0]

            # 1. Kiểm tra Idempotent Alert Refresh: Lúc T-5 khách ghế C04 chưa vào -> missing_guest
            refresh_showtime_alerts(
                valid_room,
                valid_show,
                {"illegal_occupants": [], "missing_guests": ["C04"], "over_capacity": False},
            )
            active_t5 = [
                a for a in get_active_alerts(valid_room)
                if a["show_id"] == valid_show and a["seat_id"] == "C04" and a["alert_type"] == "missing_guest"
            ]
            self.assertEqual(len(active_t5), 1)

            # Lúc T-3 khách ghế C04 đã vào ngồi đúng ghế -> missing_guests không còn C04 -> tự động đóng cảnh báo cũ
            ref_res = refresh_showtime_alerts(
                valid_room,
                valid_show,
                {"illegal_occupants": [], "missing_guests": [], "over_capacity": False},
            )
            self.assertGreaterEqual(ref_res["auto_resolved_count"], 1)
            active_t3 = [
                a for a in get_active_alerts(valid_room)
                if a["show_id"] == valid_show and a["seat_id"] == "C04" and a["alert_type"] == "missing_guest"
            ]
            self.assertEqual(len(active_t3), 0)

            # 2. Kiểm tra POST /api/v1/scheduler/trigger_pre_show với offset_minutes=-3 -> ghi nhận AUTO_T_MINUS_3
            res_trig = self.client.post(
                "/api/v1/scheduler/trigger_pre_show",
                json={"room_id": valid_room, "show_id": valid_show, "offset_minutes": -3},
            )
            self.assertEqual(res_trig.status_code, 200)
            body = res_trig.json()
            self.assertEqual(body.get("trigger_source"), "AUTO_T_MINUS_3")
            self.assertEqual(body["summary"].get("trigger_source"), "AUTO_T_MINUS_3")
            self.assertIn("scheduler_simulation", body)

            logs = get_inference_logs(room_id=valid_room, show_id=valid_show, limit=5)
            self.assertTrue(any(lg.get("trigger_source") == "AUTO_T_MINUS_3" for lg in logs))
        finally:
            conn.execute("DELETE FROM ai_inference_logs WHERE id > ?", (max_log_id,))
            conn.execute("DELETE FROM alerts WHERE id > ?", (max_alert_id,))
            conn.commit()
            conn.close()


    def test_8_grouped_alerts_and_one_tap_batch_resolve(self):
        """Kiểm tra Gom nhóm cảnh báo theo phòng (3 chỉ số: vé đã quét, người trong rạp, ghế vi phạm)
        và API Xử lý 1 chạm hàng loạt (POST /api/v1/resolve_room_alerts)."""
        from database import save_alerts, get_active_alerts, resolve_room_alerts
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT room_id, show_id FROM showtimes WHERE status='scheduled' ORDER BY end_at DESC LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(row)
            valid_room, valid_show = row[0], row[1]

            max_alert_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM alerts").fetchone()[0]

            # 1. Tạo 2 cảnh báo vi phạm cho phòng
            save_alerts(valid_room, valid_show, "illegal_occupant", ["Z01", "Z02"])

            # 2. Gọi GET /api/v1/alerts -> Kiểm tra cấu trúc trả về
            res = self.client.get(f"/api/v1/alerts?room_id={valid_room}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertIn("grouped_alerts", data)

            # Kiểm tra cụm gom nhóm
            groups = [g for g in data["grouped_alerts"] if g["room_id"] == valid_room and g["show_id"] == valid_show]
            self.assertEqual(len(groups), 1)
            grp = groups[0]
            self.assertIn("scanned_tickets_count", grp)
            self.assertIn("detected_people_count", grp)
            self.assertIn("all_alerted_seats", grp)
            self.assertIn("total_alerts", grp)
            self.assertIn("Z01", grp["all_alerted_seats"])
            self.assertIn("Z02", grp["all_alerted_seats"])

            # 3. Kiểm tra API Xử lý 1 chạm: POST /api/v1/resolve_room_alerts
            # 3A: Không gửi token -> chặn 401 Unauthorized
            res_unauth = self.client.post(
                "/api/v1/resolve_room_alerts",
                json={"room_id": valid_room, "show_id": valid_show},
            )
            self.assertEqual(res_unauth.status_code, 401)

            # 3B: Gửi Bearer Token hợp lệ của nhân viên -> 200 OK
            staff_token = create_token(user_id=2)
            res_resolve = self.client.post(
                "/api/v1/resolve_room_alerts",
                json={"room_id": valid_room, "show_id": valid_show},
                headers={"Authorization": f"Bearer {staff_token}"},
            )
            self.assertEqual(res_resolve.status_code, 200)
            res_body = res_resolve.json()
            self.assertEqual(res_body["status"], "success")
            self.assertGreaterEqual(res_body["resolved_count"], 2)

            # Sau khi giải quyết hàng loạt, không còn cảnh báo mở cho 2 ghế Z01, Z02
            active_after = [
                a for a in get_active_alerts(valid_room)
                if a["show_id"] == valid_show and a["seat_id"] in ("Z01", "Z02")
            ]
            self.assertEqual(len(active_after), 0)
        finally:
            conn.execute("DELETE FROM alerts WHERE id > ?", (max_alert_id,))
            conn.commit()
            conn.close()

    def test_9_four_business_logic_fixes(self):
        """Kiểm thử toàn diện 4 cải tiến logic nghiệp vụ (Lỗi 1.1, 1.2, 2, 3, 4)."""
        from datetime import datetime
        from database import get_dynamic_shift, get_active_alerts, get_seats, save_alerts
        from seat_mapper import get_seat_tier, generate_alerts
        from security import sign_ticket_qr, verify_ticket_qr_signature

        # --- LỖI 2: Dynamic Shift phủ kín 24h & đệm ±30 phút ---
        # Quản lý đăng nhập lúc 16:15 (khoảng trống cũ 16:00-16:30) -> nhận ('ca_toi', 'Ca tối (16:00 - 24:00)')
        self.assertEqual(
            get_dynamic_shift("Quản lý", datetime(2026, 11, 12, 16, 15)),
            ("ca_toi", "Ca tối (16:00 - 24:00)"),
        )
        # Nhân viên đến sớm lúc 07:15 -> nhận 'ca_sang' (nhờ đệm 30 phút)
        self.assertEqual(
            get_dynamic_shift("Soát vé", datetime(2026, 11, 12, 7, 15))[0],
            "ca_sang",
        )
        # Nhân viên bàn giao ca muộn lúc 23:15 -> nhận 'ca_toi' (nhờ đệm 30 phút)
        self.assertEqual(
            get_dynamic_shift("Soát vé", datetime(2026, 11, 12, 23, 15))[0],
            "ca_toi",
        )

        # --- LỖI 4: Hạng ghế VIP / STANDARD (không có Sweetbox) & suy luận VIP Seat Hopping ---
        self.assertEqual(get_seat_tier("B04"), "STANDARD")
        self.assertEqual(get_seat_tier("J10"), "VIP")
        self.assertEqual(get_seat_tier("G05"), "VIP")
        hop_res = generate_alerts(
            set_A={"B04"},
            set_B={"G05"},
            room_id="room3",
            total_seats=132,
            total_detected_people=1,
        )
        self.assertEqual(hop_res["illegal_occupants"], ["G05"])
        self.assertEqual(hop_res["missing_guests"], ["B04"])
        self.assertEqual(len(hop_res["vip_seat_hopping"]), 1)
        self.assertEqual(hop_res["vip_seat_hopping"][0]["from_seat"], "B04")
        self.assertEqual(hop_res["vip_seat_hopping"][0]["to_seat"], "G05")

        # --- LỖI 1.1, 1.2 & LỖI 3 trên Database & API ---
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT room_id, show_id FROM showtimes WHERE status='scheduled' ORDER BY end_at DESC LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(row)
            valid_room, valid_show = row[0], row[1]
            max_alert_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM alerts").fetchone()[0]

            staff_token = create_token(user_id=2)

            # Lỗi 1.1: Ký số HMAC-SHA256 hợp lệ & phát hiện vé giả mạo chữ ký số
            sig_ok = sign_ticket_qr(valid_room, valid_show, "TICK-TEST-F01", "F01")
            self.assertTrue(verify_ticket_qr_signature(valid_room, valid_show, "TICK-TEST-F01", "F01", sig_ok))
            self.assertFalse(verify_ticket_qr_signature(valid_room, valid_show, "TICK-TEST-F01", "F01", "0000deadbeef0000"))

            # Gửi 1 vé chữ ký giả lên /api/v1/sync_tickets -> bị chặn và sinh cảnh báo forged_ticket
            res_forged = self.client.post(
                "/api/v1/sync_tickets",
                data={
                    "room_id": valid_room,
                    "show_id": valid_show,
                    "device_id": "dev_hacker",
                    "scanned_tickets": json.dumps([
                        {"ticket": "TICK-FORGED-99", "seat": "H09", "sig": "bad_signature_123"}
                    ]),
                },
                headers={"Authorization": f"Bearer {staff_token}"},
            )
            self.assertEqual(res_forged.status_code, 200)
            forged_body = res_forged.json()
            self.assertTrue(forged_body["has_forged"])
            self.assertNotIn("H09", get_seats(valid_room, valid_show))

            # Lỗi 1.2: Quét trùng vé qua 2 thiết bị Offline (dev_gate_1 và dev_gate_2)
            sig_f02 = sign_ticket_qr(valid_room, valid_show, "TICK-DUP-F02", "F02")
            res_dev1 = self.client.post(
                "/api/v1/sync_tickets",
                data={
                    "room_id": valid_room,
                    "show_id": valid_show,
                    "device_id": "dev_gate_1",
                    "scanned_tickets": json.dumps([
                        {"ticket": "TICK-DUP-F02", "seat": "F02", "sig": sig_f02}
                    ]),
                },
                headers={"Authorization": f"Bearer {staff_token}"},
            )
            self.assertEqual(res_dev1.status_code, 200)
            self.assertFalse(res_dev1.json()["has_conflicts"])

            # Thiết bị 2 đồng bộ cùng mã vé đó lên sau -> phát hiện xung đột đa thiết bị
            res_dev2 = self.client.post(
                "/api/v1/sync_tickets",
                data={
                    "room_id": valid_room,
                    "show_id": valid_show,
                    "device_id": "dev_gate_2",
                    "scanned_tickets": json.dumps([
                        {"ticket": "TICK-DUP-F02", "seat": "F02", "sig": sig_f02}
                    ]),
                },
                headers={"Authorization": f"Bearer {staff_token}"},
            )
            self.assertEqual(res_dev2.status_code, 200)
            self.assertTrue(res_dev2.json()["has_conflicts"])
            dup_alerts = [
                a for a in get_active_alerts(valid_room)
                if a["show_id"] == valid_show and a["alert_type"] == "duplicate_scan" and a["seat_id"] == "F02"
            ]
            self.assertGreaterEqual(len(dup_alerts), 1)

            # Lỗi 3: Xử lý cảnh báo với resolution='ticket_verified' -> tự động thêm ghế E08 vào Tập A
            save_alerts(valid_room, valid_show, "illegal_occupant", ["E08"])
            res_verify = self.client.post(
                "/api/v1/resolve_room_alerts",
                json={
                    "room_id": valid_room,
                    "show_id": valid_show,
                    "resolution": "ticket_verified",
                },
                headers={"Authorization": f"Bearer {staff_token}"},
            )
            self.assertEqual(res_verify.status_code, 200)
            self.assertEqual(res_verify.json()["resolution"], "ticket_verified")
            # Ghế E08 đã nằm trong Tập A (get_seats) nên Mốc 2 và Mốc 3 không báo động giả lại
            self.assertIn("E08", get_seats(valid_room, valid_show))
        finally:
            conn.execute(
                "DELETE FROM tickets WHERE room_id=? AND show_id=? AND seat_id IN ('F01', 'F02', 'H09', 'E08')",
                (valid_room, valid_show),
            )
            conn.execute("DELETE FROM alerts WHERE id > ?", (max_alert_id,))
            conn.commit()
            conn.close()


if __name__ == "__main__":
    unittest.main()
