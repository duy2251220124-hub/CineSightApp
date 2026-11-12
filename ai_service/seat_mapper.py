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


# Quy ước hạng ghế chuẩn cho cả 4 phòng chiếu (chỉ gồm Ghế Thường & Ghế VIP, không có Sweetbox):
# - Hàng F, G, H, I, J: Ghế VIP (trung tâm tầm nhìn chuẩn)
# - Hàng A, B, C, D, E, K, L: Ghế Thường (STANDARD)
VIP_ROWS = ("F", "G", "H", "I", "J")


def get_seat_tier(seat_code: str, room_id: str = None) -> str:
    """Trả về hạng ghế ('VIP' hoặc 'STANDARD') dựa trên hàng ghế."""
    norm = normalize_seat(seat_code)
    m = re.match(r"([A-Z]+)", norm)
    row_letter = m.group(1) if m else ""
    if row_letter in VIP_ROWS:
        return "VIP"
    return "STANDARD"


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
    - Hỗ trợ đầu vào (cx, cy, conf, box_w, box_h) hoặc (cx, cy) tương thích ngược.
    - Lọc khử trùng khoảng cách phối cảnh (Perspective Distance Suppression) theo độ tự tin giảm dần.
    - Lọc vùng ghế (ROI Filter) với dung sai viền <= 8px, loại bỏ nhiễu cầu thang/lối đi/loa tường.
    - Mỗi đa giác ghế đại diện đúng 1 ghế vật lý (1 ghế = tối đa 1 người), tuyệt đối không đẩy tràn sang next_seat.
    """
    if not detected_heads or not seats_config:
        return set()

    # Chuẩn hóa đầu vào: (cx, cy, conf, box_w, box_h)
    normalized_heads = []
    for item in detected_heads:
        if len(item) >= 5:
            cx, cy, conf, bw, bh = (
                float(item[0]),
                float(item[1]),
                float(item[2]),
                float(item[3]),
                float(item[4]),
            )
        elif len(item) == 3:
            cx, cy, conf = float(item[0]), float(item[1]), float(item[2])
            bw, bh = 0.0, 0.0
        else:
            cx, cy = float(item[0]), float(item[1])
            conf, bw, bh = 1.0, 0.0, 0.0
        normalized_heads.append((cx, cy, conf, bw, bh))

    # Sắp xếp giảm dần theo độ tự tin (conf) để ưu tiên giữ khung nhận diện chuẩn nhất
    normalized_heads.sort(key=lambda p: (-p[2], p[1], p[0]))

    # Bộ lọc khử trùng khoảng cách phối cảnh (Perspective Distance Suppression)
    filtered_heads = []
    for cand in normalized_heads:
        cx1, cy1, conf1, bw1, bh1 = cand
        is_duplicate = False
        for kept in filtered_heads:
            cx2, cy2, conf2, bw2, bh2 = kept
            max_w = max(bw1, bw2)
            max_h = max(bh1, bh2)
            if max_w > 0.0 and max_h > 0.0:
                if abs(cx1 - cx2) < 0.48 * max_w and abs(cy1 - cy2) < 0.60 * max_h:
                    is_duplicate = True
                    break
            else:
                if abs(cx1 - cx2) < 12.0 and abs(cy1 - cy2) < 12.0:
                    is_duplicate = True
                    break
        if not is_duplicate:
            filtered_heads.append(cand)

    set_B = set()
    for hx, hy, conf, bw, bh in filtered_heads:
        matched_seat = None

        # Bước 1: Kiểm tra điểm neo nằm lọt bên trong đa giác ghế (hoặc dời xuống phần đệm ghế)
        for check_y in (hy + 10.0, hy + 18.0, hy, hy + 5.0):
            for seat_name, polygon in seats_config.items():
                poly_np = np.array(polygon, np.int32)
                is_inside = cv2.pointPolygonTest(poly_np, (hx, check_y), False)
                if is_inside >= 0:
                    matched_seat = seat_name
                    break
            if matched_seat:
                break

        # Bước 2: Bù dung sai nhỏ (<= 8px) nếu khách nghiêng đầu sát tay vịn/viền đa giác ghế
        # Chỉ xét khi điểm neo chưa rơi lọt vào đa giác nào ở Bước 1
        if not matched_seat:
            best_dist = -9999.0
            best_seat = None
            probe_x_offsets = (0.0, 0.05 * bw, -0.05 * bw) if bw > 0.0 else (0.0,)
            for seat_name, polygon in seats_config.items():
                if seat_name in set_B:
                    continue
                poly_np = np.array(polygon, np.int32)
                for dx in probe_x_offsets:
                    d = cv2.pointPolygonTest(poly_np, (hx + dx, hy + 10.0), True)
                    if d >= -8.0 and d > best_dist:
                        best_dist = d
                        best_seat = seat_name
            if best_seat:
                matched_seat = best_seat

        # Bước 3: Mỗi đa giác ghế chỉ chứa tối đa 1 người (không đẩy tràn sang next_seat)
        if matched_seat and matched_seat not in set_B:
            set_B.add(matched_seat)

    return set_B

def generate_alerts(set_A: set, set_B: set, room_id: str, total_seats: int, total_detected_people: int = None, capacity_threshold: int = 0):
    """Sinh cảnh báo chênh lệch cho 1 phòng chiếu cụ thể, kèm suy luận tự ý nâng hạng ghế VIP (VIP Seat Hopping)."""
    print(f"\n--- BÁO CÁO KIỂM ĐẾM PHÒNG [{room_id.upper()}] ---")
    print(f"Tập A (App soát vé) : {set_A}")
    print(f"Tập B (AI Camera)   : {set_B}")

    khach_lau = sorted(set_B - set_A)
    khach_vang = sorted(set_A - set_B)
    detected_count = total_detected_people if total_detected_people is not None else len(set_B)
    over_capacity = (detected_count > total_seats) or (capacity_threshold > 0 and len(khach_lau) >= capacity_threshold)

    # Luật suy luận VIP Seat Hopping:
    # Khi có ghế thuộc B \ A nằm ở hàng VIP đồng thời có ghế thuộc A \ B nằm ở hàng STANDARD
    illegal_vip = [s for s in khach_lau if get_seat_tier(s, room_id) == "VIP"]
    missing_standard = [s for s in khach_vang if get_seat_tier(s, room_id) == "STANDARD"]
    vip_seat_hopping = []
    for std_seat, vip_seat in zip(missing_standard, illegal_vip):
        vip_seat_hopping.append({
            "from_seat": std_seat,
            "to_seat": vip_seat,
            "from_tier": "STANDARD",
            "to_tier": "VIP",
            "same_headcount": len(set_B) == len(set_A),
            "message": f"Nghi vấn khách tự ý chuyển từ ghế Thường {std_seat} lên ghế VIP {vip_seat}",
        })

    if khach_lau:
        print(f"[ĐỎ] Ngồi không có vé tại: {khach_lau}")
    if khach_vang:
        print(f"[VÀNG] Có vé nhưng ghế trống tại: {khach_vang}")
    if vip_seat_hopping:
        print(f"[TÍM] Nghi vấn tự ý nâng hạng ghế VIP: {vip_seat_hopping}")
    if over_capacity:
        print(f"[ĐỎ] VƯỢT SỨC CHỨA! Phát hiện {detected_count} người / {total_seats} ghế.")
    if not khach_lau and not khach_vang and not over_capacity:
        print("[XANH] Tất cả khớp! An toàn chiếu phim.")

    seat_tiers = {s: get_seat_tier(s, room_id) for s in (set(set_A) | set(set_B))}

    return {
        "room_id": room_id,
        "illegal_occupants": list(khach_lau),
        "missing_guests": list(khach_vang),
        "over_capacity": over_capacity,
        "vip_seat_hopping": vip_seat_hopping,
        "seat_tiers": seat_tiers,
    }
