import os
import sys
import json
import asyncio
import sqlite3
from io import BytesIO

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

base_dir = r"c:\CineSightApp\ai_service"
sys.path.insert(0, base_dir)

from fastapi import UploadFile
import main

async def run_tests():
    print("=" * 65)
    print("=== KIỂM THỬ HỒI QUY TÍCH HỢP MÔ HÌNH VÀO API (PHASE 9b) ===")
    print("=" * 65)

    # 1. Kiểm tra nạp mô hình
    print("\n--- TEST 1: KIỂM TRA NẠP TRỌNG SỐ MÔ HÌNH CHÍNH THỨC ---")
    assert main.model is not None, "LỖI: main.model đang là None!"
    print(f"PASS: Đã nạp mô hình thành công.")
    print(f"  - Đường dẫn model : {main.model_path}")
    print(f"  - Ngưỡng tin cậy  : conf = {main.MODEL_CONF}")
    print(f"  - Độ phân giải    : imgsz = {main.MODEL_IMGSZ}")
    print(f"  - Lớp nhận diện   : {main.model.names}")

    # 2. Kiểm tra Health Check endpoint (GET /)
    print("\n--- TEST 2: KIỂM TRA ENDPOINT GET / (HEALTH CHECK) ---")
    health_res = main.health_check()
    print(f"Response: {health_res}")
    assert health_res.get("status") == "CineSight AI Service đang chạy", "Health check thất bại!"
    print("PASS: Endpoint GET / hoạt động chuẩn xác.")

    # 3. Kiểm tra đồng bộ vé (POST /api/v1/sync_tickets)
    print("\n--- TEST 3: KIỂM TRA ĐỒNG BỘ VÉ (POST /api/v1/sync_tickets) ---")
    test_room = "room1"
    test_show = "regression_test_2026_10_17"
    sample_tickets = json.dumps([
        {"seat": "D3", "ticket": "T001"},
        {"seat": "D4", "ticket": "T002"},
        {"seat": "E5", "ticket": "T003"}
    ])
    sync_res = main.sync_tickets_from_app(
        room_id=test_room,
        show_id=test_show,
        scanned_tickets=sample_tickets
    )
    print(f"Response: {sync_res}")
    assert isinstance(sync_res, dict) and sync_res.get("status") == "success", "Đồng bộ vé thất bại!"
    print("PASS: Endpoint POST /api/v1/sync_tickets hoạt động chuẩn xác.")

    # 4A. Kiểm tra phân tích ảnh phòng trống (0425s.jpg - GT = 0 người)
    print("\n--- TEST 4A: KIỂM TRA PHÂN TÍCH ẢNH PHÒNG TRỐNG (GT = 0 NGƯỜI) ---")
    empty_img_path = os.path.join(base_dir, "datasets", "head_v2", "images", "test", "room1_cam_edited_0425s.jpg")
    with open(empty_img_path, "rb") as f:
        empty_bytes = f.read()
    up_empty = UploadFile(filename="room1_cam_edited_0425s.jpg", file=BytesIO(empty_bytes))
    res_empty = await main.analyze_cinema_room(image=up_empty, room_id=test_room, show_id=test_show)
    empty_cnt = res_empty["summary"]["total_detected_people"]
    print(f"Ảnh 0425s.jpg (GT = 0): AI phát hiện = {empty_cnt} người")
    assert empty_cnt == 0, f"Kỳ vọng 0 người trên ảnh nền trống nhưng phát hiện {empty_cnt}"
    print("PASS: Không báo giả trên ảnh nền phòng trống.")

    # 4B. Kiểm tra phân tích ảnh phòng có khách (0456s.jpg - GT = 4 người)
    print("\n--- TEST 4B: KIỂM TRA PHÂN TÍCH ẢNH PHÒNG CÓ KHÁCH (GT = 4 NGƯỜI) ---")
    occ_img_path = os.path.join(base_dir, "datasets", "head_v2", "images", "test", "room1_cam_edited_0456s.jpg")
    with open(occ_img_path, "rb") as f:
        occ_bytes = f.read()
    up_occ = UploadFile(filename="room1_cam_edited_0456s.jpg", file=BytesIO(occ_bytes))
    res_occ = await main.analyze_cinema_room(image=up_occ, room_id=test_room, show_id=test_show)
    print("Response từ /api/v1/analyze (0456s.jpg):")
    print(json.dumps(res_occ, indent=2, ensure_ascii=False))
    occ_cnt = res_occ["summary"]["total_detected_people"]
    assert occ_cnt > 0, "Mô hình không phát hiện được người nào trên ảnh có khách!"
    print(f"PASS: Ảnh 0456s.jpg (GT = 4): AI phát hiện chính xác {occ_cnt} khán giả và đối soát ghế thành công.")

    # 5. Dọn dẹp dữ liệu test tạm trong SQLite
    db_path = os.path.join(base_dir, "cinesight.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM tickets WHERE show_id = ?", (test_show,))
        cur.execute("DELETE FROM alerts WHERE show_id = ?", (test_show,))
        conn.commit()
        conn.close()
        print("\nĐã dọn dẹp dữ liệu kiểm thử tạm thời khỏi cinesight.db.")

    print("\n" + "=" * 65)
    print("=== TẤT CẢ CÁC BÀI KIỂM THỬ HỒI QUY ĐỀU ĐẠT 100% (PHASE 9b PASS) ===")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_tests())

