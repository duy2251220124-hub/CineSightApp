import cv2
import json
import numpy as np
import os
import re
from datetime import datetime

def to_show_id(date: str, start_time: str) -> str:
    """
    Chuyển ngày (yyyy-MM-dd hoặc dd/MM/yyyy) và giờ bắt đầu (HH:mm)
    thành chuỗi show_id chuẩn: "yyyy-MM-ddTHH:mm"
    
    Ví dụ:
        to_show_id("2026-09-29", "19:30")  -> "2026-09-29T19:30"
        to_show_id("29/09/2026", "19:30")  -> "2026-09-29T19:30"
    """
    # Thử parse định dạng dd/MM/yyyy
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(date.strip(), fmt)
            h, m = start_time.strip().split(":")
            return f"{d.strftime('%Y-%m-%d')}T{int(h):02d}:{int(m):02d}"
        except ValueError:
            continue
    raise ValueError(f"Không parse được ngày: '{date}'")

def normalize_seat(code: str) -> str:
    """Chuẩn hóa mã ghế về dạng Chữ + 2 số (VD: C04)"""
    m = re.match(r'([a-zA-Z]+)\s*(\d+)', str(code).strip())
    if m:
        return f"{m.group(1).upper()}{int(m.group(2)):02d}"
    return str(code).strip().upper()

def load_seats_config(room_id: str):
    """
    Đọc file cấu hình ghế của MỘT PHÒNG CỤ THỂ.
    Mỗi phòng có 1 file JSON riêng trong thư mục seats_configs/
    """
    config_path = os.path.join(os.path.dirname(__file__), "seats_configs", f"seats_config_{room_id}.json")
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            data = json.load(f)
            # Chuẩn hóa keys
            normalized_data = {normalize_seat(k): v for k, v in data.items()}
            print(f"[OK] Đã tải bản đồ ghế phòng '{room_id}': {len(normalized_data)} ghế.")
            return normalized_data
    except FileNotFoundError:
        print(f"[-] Chưa có file cấu hình cho phòng '{room_id}'.")
        print(f"    Hãy chạy: python calibrate_seats.py {room_id}")
        return {}

def process_ai_detections(detected_heads, seats_config):
    """
    Ánh xạ tọa độ đầu người (từ YOLO) vào mã ghế cụ thể.
    Hỗ trợ bù góc nhìn nghiêng camera và xử lý 2 khách ngồi cạnh nhau nghiêng đầu sát nhau.
    """
    set_B = set()
    sorted_heads = sorted(detected_heads, key=lambda p: (float(p[1]), float(p[0])))
    for head in sorted_heads:
        hx, hy = float(head[0]), float(head[1])
        matched_seat = None
        for check_y in (hy + 10.0, hy + 18.0, hy):
            for seat_name, polygon in seats_config.items():
                poly_np = np.array(polygon, np.int32)
                is_inside = cv2.pointPolygonTest(poly_np, (hx, check_y), False)
                if is_inside >= 0:
                    matched_seat = seat_name
                    break
            if matched_seat:
                break
        if matched_seat:
            if matched_seat in set_B:
                m = re.match(r'([A-Z]+)(\d+)', matched_seat)
                if m:
                    next_seat = f"{m.group(1)}{int(m.group(2)) + 1:02d}"
                    if next_seat in seats_config and next_seat not in set_B:
                        matched_seat = next_seat
            set_B.add(matched_seat)
    return set_B

def generate_alerts(set_A: set, set_B: set, room_id: str, total_seats: int, total_detected_people: int = None, capacity_threshold: int = 0):
    """Sinh cảnh báo chênh lệch cho 1 phòng chiếu cụ thể."""
    print(f"\n--- BÁO CÁO KIỂM ĐẾM PHÒNG [{room_id.upper()}] ---")
    print(f"Tập A (App soát vé) : {set_A}")
    print(f"Tập B (AI Camera)   : {set_B}")

    khach_lau = set_B - set_A
    khach_vang = set_A - set_B
    detected_count = total_detected_people if total_detected_people is not None else len(set_B)
    over_capacity = (detected_count > total_seats) or (capacity_threshold > 0 and len(khach_lau) >= capacity_threshold)

    if khach_lau:
        print(f"[ĐỎ] Ngồi không có vé tại: {khach_lau}")
    if khach_vang:
        print(f"[VÀNG] Có vé nhưng ghế trống tại: {khach_vang}")
    if over_capacity:
        print(f"[ĐỎ] VƯỢT SỨC CHỨA! Phát hiện {detected_count} người / {total_seats} ghế.")
    if not khach_lau and not khach_vang and not over_capacity:
        print("[XANH] Tất cả khớp! An toàn chiếu phim.")
    
    return {
        "room_id": room_id,
        "illegal_occupants": list(khach_lau),
        "missing_guests": list(khach_vang),
        "over_capacity": over_capacity
    }
