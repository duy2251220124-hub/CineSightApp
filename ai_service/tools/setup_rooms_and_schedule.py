import os
import sys
import json
import shutil
import cv2
import numpy as np
from ultralytics import YOLO

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = r"c:\CineSightApp\ai_service"
SEATS_CONFIG_DIR = os.path.join(BASE_DIR, "seats_configs")
CALIB_DIR = os.path.join(BASE_DIR, "calibration_images")
EMPTY_FRAME = os.path.join(BASE_DIR, "datasets", "head_v2", "images", "test", "room1_cam_edited_0425s.jpg")
UPLOADED_IMG = r"C:\Users\Dell KIM ANH\.gemini\antigravity\brain\779a87a8-afe5-44b9-9038-d06517f57dee\.user_uploaded\media_1792216940059_ae691658.jpg"
ARTIFACT_DIR = r"C:\Users\Dell KIM ANH\.gemini\antigravity\brain\779a87a8-afe5-44b9-9038-d06517f57dee"

# Cấu trúc 12 hàng ghế thực tế trích xuất từ camera (tổng 135 ghế):
# - Hàng A (đầu tiên, gần màn hình nhất, ít ghế nhất): 8 ghế (A1..A8)
# - Hàng B đến Hàng J (9 hàng giữa): mỗi hàng 11 ghế (B1..B11 -> J1..J11)
# - Hàng K (hàng áp cuối, có lối vào cầu thang bên trái): 2 ghế trái (K1, K2) + lối đi + 11 ghế phải (K3..K13) = 13 ghế
# - Hàng L (hàng cuối cùng sát tường): 15 ghế liên tục (L1..L15)
ROW_LAYOUT_METADATA = [
    {"row": "A", "count": 8,  "desc": "8 ghế (hàng đầu gần màn hình)"},
    {"row": "B", "count": 11, "desc": "11 ghế"},
    {"row": "C", "count": 11, "desc": "11 ghế"},
    {"row": "D", "count": 11, "desc": "11 ghế"},
    {"row": "E", "count": 11, "desc": "11 ghế"},
    {"row": "F", "count": 11, "desc": "11 ghế"},
    {"row": "G", "count": 11, "desc": "11 ghế"},
    {"row": "H", "count": 11, "desc": "11 ghế"},
    {"row": "I", "count": 11, "desc": "11 ghế"},
    {"row": "J", "count": 11, "desc": "11 ghế"},
    {"row": "K", "count": 13, "desc": "13 ghế (K1-K2 bên trái + lối đi + K3-K13 bên phải)"},
    {"row": "L", "count": 15, "desc": "15 ghế (hàng cuối sát tường)"},
]


def generate_uploaded_space_polygons():
    """
    Tạo tọa độ đa giác 135 ghế khớp chính xác từng lưng ghế trên ảnh camera 1024x899
    (media_1792216940059_ae691658.jpg).
    """
    # Định nghĩa các dải hàng (row, count, y_top, y_bot, xl_top, xr_top, xl_bot, xr_bot)
    bands = [
        ("A", 8,  742, 856, 190, 822, 182, 830),
        ("B", 11, 616, 726, 114, 884, 104, 894),
        ("C", 11, 512, 608, 142, 848, 132, 860),
        ("D", 11, 422, 506, 170, 814, 160, 826),
        ("E", 11, 348, 418, 194, 784, 186, 796),
        ("F", 11, 282, 345, 216, 758, 208, 768),
        ("G", 11, 218, 279, 236, 736, 228, 746),
        ("H", 11, 165, 216, 250, 716, 244, 726),
        ("I", 11, 118, 163, 264, 698, 258, 706),
        ("J", 11, 82,  117, 278, 682, 272, 690),
    ]

    seats_1024 = {}

    for row, count, yt, yb, xlt, xrt, xlb, xrb in bands:
        for i in range(count):
            c0 = i / count
            c1 = (i + 1) / count
            tl = [int(round(xlt + c0 * (xrt - xlt))), int(yt)]
            tr = [int(round(xlt + c1 * (xrt - xlt))), int(yt)]
            br = [int(round(xlb + c1 * (xrb - xlb))), int(yb)]
            bl = [int(round(xlb + c0 * (xrb - xlb))), int(yb)]
            seats_1024[f"{row}{i + 1}"] = [tl, tr, br, bl]

    # Hàng K: K1, K2 bên trái lối vào + K3..K13 (11 ghế khối chính bên phải)
    k_left_yt, k_left_yb = 50, 84
    k_left_x0, k_left_x1 = 148, 214
    for i in range(2):
        c0 = i / 2.0
        c1 = (i + 1) / 2.0
        tl = [int(round(k_left_x0 + c0 * (k_left_x1 - k_left_x0))), k_left_yt]
        tr = [int(round(k_left_x0 + c1 * (k_left_x1 - k_left_x0))), k_left_yt]
        br = [int(round(k_left_x0 + c1 * (k_left_x1 - k_left_x0))), k_left_yb]
        bl = [int(round(k_left_x0 + c0 * (k_left_x1 - k_left_x0))), k_left_yb]
        seats_1024[f"K{i + 1}"] = [tl, tr, br, bl]

    k_main_yt, k_main_yb = 48, 81
    k_xlt, k_xrt, k_xlb, k_xrb = 288, 668, 284, 674
    for i in range(11):
        c0 = i / 11.0
        c1 = (i + 1) / 11.0
        tl = [int(round(k_xlt + c0 * (k_xrt - k_xlt))), k_main_yt]
        tr = [int(round(k_xlt + c1 * (k_xrt - k_xlt))), k_main_yt]
        br = [int(round(k_xlb + c1 * (k_xrb - k_xlb))), k_main_yb]
        bl = [int(round(k_xlb + c0 * (k_xrb - k_xlb))), k_main_yb]
        seats_1024[f"K{i + 3}"] = [tl, tr, br, bl]

    # Hàng L: 15 ghế liên tục sát tường cuối (L1..L15)
    l_yt, l_yb = 14, 46
    l_xlt, l_xrt, l_xlb, l_xrb = 162, 738, 158, 742
    for i in range(15):
        c0 = i / 15.0
        c1 = (i + 1) / 15.0
        tl = [int(round(l_xlt + c0 * (l_xrt - l_xlt))), l_yt]
        tr = [int(round(l_xlt + c1 * (l_xrt - l_xlt))), l_yt]
        br = [int(round(l_xlb + c1 * (l_xrb - l_xlb))), l_yb]
        bl = [int(round(l_xlb + c0 * (l_xrb - l_xlb))), l_yb]
        seats_1024[f"L{i + 1}"] = [tl, tr, br, bl]

    return seats_1024


def convert_1024_to_1920(seats_1024):
    """
    Ánh xạ tọa độ từ khung ảnh 1024x899 sang khung hình camera gốc 1920x1080.
    """
    ax = 1.1797
    bx = 361.75
    ay = 1.1303
    by = 0.0
    seats_1920 = {}
    for code, poly in seats_1024.items():
        seats_1920[code] = [
            [int(round(ax * pt[0] + bx)), int(round(ay * pt[1] + by))]
            for pt in poly
        ]
    return seats_1920


def scan_and_visualize(seats_1024):
    """
    Quét ảnh camera do người dùng tải lên bằng YOLOv8n (best_head_v2.pt),
    xác định ghế có người ngồi và xuất:
    1) Ảnh camera đã phủ lưới sơ đồ 135 ghế + đánh dấu ghế có khách ngồi
    2) Bản vẽ sơ đồ ghế 2D trực quan đúng theo cấu trúc 12 hàng A..L
    """
    img = cv2.imread(UPLOADED_IMG)
    if img is None:
        print("[!] Không tìm thấy ảnh uploaded.")
        return set()

    model_path = os.path.join(BASE_DIR, "models", "best_head_v2.pt")
    model = YOLO(model_path)
    results = model.predict(img, conf=0.20, imgsz=800, classes=[0], verbose=False)

    detected_heads = []
    head_boxes = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            detected_heads.append((cx, cy))
            head_boxes.append((int(x1), int(y1), int(x2), int(y2), float(box.conf[0])))

    # Sắp xếp từ trái sang phải để khi 2 khách ngồi cạnh nhau nghiêng đầu sát nhau (như I5, I6)
    # mỗi đầu người được gán 1-1 vào đúng ghế tương ứng trong cùng hàng
    detected_heads.sort(key=lambda p: (p[1], p[0]))
    occupied_seats = set()
    for cx, cy in detected_heads:
        matched_seat = None
        for check_y in (cy + 10, cy + 18, cy):
            for seat_code, poly in seats_1024.items():
                poly_np = np.array(poly, np.int32)
                if cv2.pointPolygonTest(poly_np, (float(cx), float(check_y)), False) >= 0:
                    matched_seat = seat_code
                    break
            if matched_seat:
                break
        if matched_seat:
            if matched_seat in occupied_seats:
                # Nếu khách bên phải nghiêng đầu sang sát vai khách bên trái (VD: I6 nghiêng sang I5),
                # gán sang ghế liền kề bên phải trong cùng hàng
                row_char = matched_seat[0]
                seat_idx = int(matched_seat[1:])
                next_seat = f"{row_char}{seat_idx + 1}"
                if next_seat in seats_1024 and next_seat not in occupied_seats:
                    matched_seat = next_seat
            occupied_seats.add(matched_seat)

    # 1. Vẽ lên ảnh camera
    vis = img.copy()
    overlay = img.copy()

    for seat_code, poly in seats_1024.items():
        pts = np.array(poly, np.int32)
        is_occ = seat_code in occupied_seats
        if is_occ:
            cv2.fillPoly(overlay, [pts], (0, 0, 230))
            cv2.polylines(vis, [pts], True, (0, 255, 255), 2)
        else:
            cv2.polylines(vis, [pts], True, (0, 200, 80), 1)

    vis = cv2.addWeighted(overlay, 0.38, vis, 0.62, 0)

    for seat_code, poly in seats_1024.items():
        pts = np.array(poly, np.int32)
        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        is_occ = seat_code in occupied_seats
        font_scale = 0.33 if poly[2][1] - poly[0][1] < 55 else 0.40
        color = (255, 255, 255) if is_occ else (180, 255, 180)
        cv2.putText(vis, seat_code, (cx - 11, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(vis, seat_code, (cx - 11, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv2.LINE_AA)

    for (x1, y1, x2, y2, conf) in head_boxes:
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)

    out_cam_path = os.path.join(ARTIFACT_DIR, "camera_seatmap_scanned.jpg")
    cv2.imwrite(out_cam_path, vis)
    print(f"[OK] Đã lưu ảnh quét sơ đồ ghế trên camera -> {out_cam_path}")

    # 2. Vẽ sơ đồ ghế 2D chuẩn rạp chiếu phim (Màn hình ở trên hoặc dưới, hiển thị rõ 12 hàng A..L)
    canvas_w, canvas_h = 1100, 860
    diagram = np.full((canvas_h, canvas_w, 3), (24, 26, 32), dtype=np.uint8)

    # Tiêu đề
    cv2.putText(diagram, "SO DO GHE PHONG CHIEU 1..4 (TRICH XUAT TU CAMERA - 135 GHE)", (155, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)

    # Thanh màn hình ở phía trước (gần hàng A nhất)
    # Để trực quan giống góc nhìn sơ đồ ghế + khớp ảnh camera (Hàng L ở trên, Hàng A ở dưới gần màn hình):
    # Vẽ cả nhãn "CUOI PHONG (HANG L - 15 GHE)" ở trên và "MAN HINH / SCREEN (GAN HANG A - 8 GHE)" ở dưới!
    rows_top_to_bottom = ["L", "K", "J", "I", "H", "G", "F", "E", "D", "C", "B", "A"]
    row_counts = {"A": 8, "B": 11, "C": 11, "D": 11, "E": 11, "F": 11, "G": 11, "H": 11, "I": 11, "J": 11, "K": 13, "L": 15}

    start_y = 75
    row_h = 52
    seat_w = 52
    seat_h = 38
    gap_x = 8

    for idx, r_label in enumerate(rows_top_to_bottom):
        cy = start_y + idx * row_h
        cnt = row_counts[r_label]

        # Nhãn hàng hai bên
        cv2.putText(diagram, r_label, (40, cy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 210, 255), 2, cv2.LINE_AA)
        cv2.putText(diagram, f"{r_label} ({cnt})", (1005, cy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (170, 180, 190), 1, cv2.LINE_AA)

        # Căn vị trí ngang của từng hàng giống hệt bố cục trong ảnh camera:
        # Khối 11 ghế chính (B..J và K3..K13) nằm ở cột chuẩn 3..13 (trên lưới 15 cột)
        for s_num in range(1, cnt + 1):
            seat_code = f"{r_label}{s_num}"
            if r_label == "L":
                # 15 ghế trải từ cột 0 đến cột 14
                grid_col = s_num - 1
            elif r_label == "K":
                # K1, K2 ở bên trái (cột 0, 1), cách 1 cột lối đi (cột 2), K3..K13 ở cột 3..13
                if s_num <= 2:
                    grid_col = s_num - 1
                else:
                    grid_col = s_num  # s_num=3 -> col 3 .. s_num=13 -> col 13
            elif r_label == "A":
                # 8 ghế căn giữa so với khối 11 ghế (từ cột 4.5 đến 11.5)
                grid_col = 4.5 + (s_num - 1)
            else:
                # Hàng B..J: 11 ghế ở cột 3..13
                grid_col = 3 + (s_num - 1)

            sx = int(round(85 + grid_col * (seat_w + gap_x)))
            sy = cy

            is_occ = seat_code in occupied_seats
            bg_color = (40, 50, 220) if is_occ else (55, 62, 76)
            border_color = (80, 220, 255) if is_occ else (110, 120, 140)

            cv2.rectangle(diagram, (sx, sy), (sx + seat_w, sy + seat_h), bg_color, -1, cv2.LINE_AA)
            cv2.rectangle(diagram, (sx, sy), (sx + seat_w, sy + seat_h), border_color, 2 if is_occ else 1, cv2.LINE_AA)
            cv2.putText(diagram, seat_code, (sx + 8, sy + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # Thanh MÀN HÌNH ở phía dưới (ngay trước Hàng A)
    screen_y = start_y + 12 * row_h + 20
    cv2.line(diagram, (240, screen_y), (880, screen_y), (0, 180, 255), 4, cv2.LINE_AA)
    cv2.putText(diagram, "MAN HINH CHIEU PHIM / SCREEN (GAN HANG A NHAT)", (335, screen_y + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 200, 255), 2, cv2.LINE_AA)

    # Chú thích
    leg_y = screen_y + 62
    cv2.rectangle(diagram, (300, leg_y - 16), (324, leg_y + 4), (55, 62, 76), -1)
    cv2.putText(diagram, f"Ghe trong ({135 - len(occupied_seats)} ghe)", (334, leg_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (210, 210, 210), 1, cv2.LINE_AA)

    cv2.rectangle(diagram, (580, leg_y - 16), (604, leg_y + 4), (40, 50, 220), -1)
    occ_str = ", ".join(sorted(occupied_seats))
    cv2.putText(diagram, f"Co khach ngoi ({len(occupied_seats)} ghe: {occ_str})", (614, leg_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 220, 255), 1, cv2.LINE_AA)

    out_diag_path = os.path.join(ARTIFACT_DIR, "2d_seatmap_diagram.png")
    cv2.imwrite(out_diag_path, diagram)
    print(f"[OK] Đã lưu sơ đồ ghế 2D -> {out_diag_path}")
    return occupied_seats


def main():
    os.makedirs(SEATS_CONFIG_DIR, exist_ok=True)
    os.makedirs(CALIB_DIR, exist_ok=True)

    seats_1024 = generate_uploaded_space_polygons()
    seats_1920 = convert_1024_to_1920(seats_1024)

    for room_num in range(1, 5):
        room_id = f"room{room_num}"
        config_path = os.path.join(SEATS_CONFIG_DIR, f"seats_config_{room_id}.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(seats_1920, f, indent=2, ensure_ascii=False)
        print(f"[OK] Đã lưu sơ đồ {len(seats_1920)} ghế (12 hàng A..L) cho {room_id} -> {config_path}")

        calib_path = os.path.join(CALIB_DIR, f"{room_id}.jpg")
        if os.path.exists(EMPTY_FRAME):
            shutil.copyfile(EMPTY_FRAME, calib_path)

    occupied = scan_and_visualize(seats_1024)
    print(f"[AI SCAN] Các ghế phát hiện có người ngồi trên ảnh: {sorted(occupied)}")


if __name__ == "__main__":
    main()
