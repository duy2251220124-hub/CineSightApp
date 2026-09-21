import cv2
import json
import numpy as np
import os

def load_seats_config(room_id: str):
    """
    Đọc file cấu hình ghế của MỘT PHÒNG CỤ THỂ.
    Mỗi phòng có 1 file JSON riêng trong thư mục seats_configs/
    """
    config_path = f"seats_configs/seats_config_{room_id}.json"
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            data = json.load(f)
            print(f"[OK] Đã tải bản đồ ghế phòng '{room_id}': {len(data)} ghế.")
            return data
    except FileNotFoundError:
        print(f"[-] Chưa có file cấu hình cho phòng '{room_id}'.")
        print(f"    Hãy chạy: python calibrate_seats.py {room_id}")
        return {}

def process_ai_detections(detected_heads, seats_config):
    """
    Ánh xạ tọa độ đầu người (từ YOLO) vào mã ghế cụ thể.
    Dùng thuật toán Point-in-Polygon của OpenCV.
    """
    set_B = set()
    for head in detected_heads:
        head_point = (float(head[0]), float(head[1]))
        for seat_name, polygon in seats_config.items():
            poly_np = np.array(polygon, np.int32)
            is_inside = cv2.pointPolygonTest(poly_np, head_point, False)
            if is_inside >= 0:
                set_B.add(seat_name)
                break
    return set_B

def generate_alerts(set_A: set, set_B: set, room_id: str):
    """Sinh cảnh báo chênh lệch cho 1 phòng chiếu cụ thể."""
    print(f"\n--- BÁO CÁO KIỂM ĐẾM PHÒNG [{room_id.upper()}] ---")
    print(f"Tập A (App soát vé) : {set_A}")
    print(f"Tập B (AI Camera)   : {set_B}")

    khach_lau = set_B - set_A
    khach_vang = set_A - set_B

    if khach_lau:
        print(f"[ĐỎ] Ngồi không có vé tại: {khach_lau}")
    if khach_vang:
        print(f"[VÀNG] Có vé nhưng ghế trống tại: {khach_vang}")
    if not khach_lau and not khach_vang:
        print("[XANH] Tất cả khớp! An toàn chiếu phim.")
    
    return {
        "room_id": room_id,
        "illegal_occupants": list(khach_lau),
        "missing_guests": list(khach_vang),
    }
