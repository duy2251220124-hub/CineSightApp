import cv2
import json
import numpy as np
import os
import sys

# Biến toàn cục
current_polygon = []
seats_data = {}
base_image = None
display_image = None
room_id = "all"
target_rooms = ["room1", "room2", "room3", "room4"]

def redraw_all():
    global base_image, display_image, seats_data, current_polygon
    display_image = base_image.copy()

    # 1. Vẽ toàn bộ các ghế đã lưu
    for seat_name, poly_pts in seats_data.items():
        pts = np.array(poly_pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(display_image, [pts], True, (0, 255, 120), 2, cv2.LINE_AA)
        
        # Tọa độ tâm để ghi tên ghế
        M = cv2.moments(pts)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx = int(np.mean(pts[:, 0]))
            cy = int(np.mean(pts[:, 1]))
            
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display_image, seat_name, (cx - 14, cy + 5), font, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. Vẽ đa giác đang chấm dở
    if current_polygon:
        for i, pt in enumerate(current_polygon):
            cv2.circle(display_image, pt, 5, (0, 0, 255), -1)
            cv2.putText(display_image, str(i + 1), (pt[0] + 6, pt[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        if len(current_polygon) > 1:
            for j in range(len(current_polygon) - 1):
                cv2.line(display_image, current_polygon[j], current_polygon[j + 1], (0, 255, 255), 2, cv2.LINE_AA)

def click_and_crop(event, x, y, flags, param):
    global current_polygon
    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))
        redraw_all()
        cv2.imshow("CineSight Seat Calibration Tool", display_image)
    elif event == cv2.EVENT_RBUTTONDOWN:
        if current_polygon:
            current_polygon.pop()
            redraw_all()
            cv2.imshow("CineSight Seat Calibration Tool", display_image)

def save_to_target_rooms(rooms, silent=False):
    global seats_data
    cfg_dir = 'ai_service/seats_configs'
    os.makedirs(cfg_dir, exist_ok=True)
    saved_list = []
    for r in rooms:
        out_p = os.path.join(cfg_dir, f'seats_config_{r}.json')
        with open(out_p, "w", encoding='utf-8') as f:
            json.dump(seats_data, f, indent=4, ensure_ascii=False)
        saved_list.append(r)
    if not silent:
        if len(saved_list) > 1:
            print(f"[✓] Đã lưu đồng bộ {len(seats_data)} ghế cho TẤT CẢ các phòng: {', '.join(saved_list)}!")
        else:
            print(f"[✓] Đã lưu {len(seats_data)} ghế cho phòng {saved_list[0]}!")

def main():
    global base_image, display_image, current_polygon, seats_data, room_id, target_rooms

    if len(sys.argv) > 1:
        room_id = sys.argv[1].lower().strip()
    else:
        room_id = "room3"

    all_available = ["room1", "room2", "room3", "room4"]
    if room_id in ["all", "tatca", "*"]:
        target_rooms = all_available
        room_title = "TẤT CẢ CÁC PHÒNG (room1, room2, room3, room4)"
    else:
        target_rooms = [room_id]
        room_title = f"Phòng Chiếu [{room_id.upper()}]"

    os.makedirs('ai_service/seats_configs', exist_ok=True)
    os.makedirs('ai_service/calibration_images', exist_ok=True)

    # Tìm ảnh nền (ưu tiên ảnh camera thật của chính phòng đó)
    candidate_imgs = [
        f'ai_service/calibration_images/{room_id}.jpg',
        f'ai_service/calibration_images/{room_id}.png',
        'ai_service/calibration_images/room3.jpg',
        'tools/qr_sample/CINEMA_EMPTY_ROOM.jpg',
        'ai_service/calibration_images/room_empty.jpg',
        'tools/qr_sample/CCTV_ROOM1_TEST_FRAME.jpg',
        'tools/qr_sample/CCTV_ROOM4_TEST_FRAME.jpg',
        'ai_service/calibration_images/room1.jpg',
    ]
    img_path = None
    for p in candidate_imgs:
        if os.path.exists(p):
            img_path = p
            break

    if not img_path:
        print("[-] Không tìm thấy ảnh rạp chiếu để hiệu chuẩn!")
        return

    print(f"[+] Sử dụng ảnh nền camera: {img_path}")
    orig = cv2.imread(img_path)
    # Chuẩn hóa về 1920x1080 (chuẩn tọa độ gốc của hệ thống CineSight)
    base_image = cv2.resize(orig, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)

    # Đọc cấu hình ghế đã có
    best_existing = {}
    for r in target_rooms:
        p = f'ai_service/seats_configs/seats_config_{r}.json'
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if len(cfg) > len(best_existing):
                        best_existing = cfg
            except Exception:
                pass

    seats_data = best_existing.copy()
    if seats_data:
        print(f"\n[!] Tìm thấy {len(seats_data)} ghế trong file cấu hình hiện tại.")
        ans = input("👉 Bạn có muốn XÓA TRẮNG để chấm lại từ đầu chính xác 100%? (Y/n, mặc định Y): ").strip().lower()
        if ans != 'n':
            seats_data = {}
            print("[*] Đã xóa trắng canvas. Sẵn sàng chấm tọa độ ghế chuẩn từ đầu!\n")
        else:
            print("[*] Giữ lại các ghế cũ để tiếp tục chỉnh sửa.\n")
    else:
        seats_data = {}

    # Danh sách thứ tự ghế gợi ý tự động (Dành cho Phòng 3: 132 ghế A10, B-I13, J18)
    if room_id == 'room3':
        expected_seats = []
        for i in range(1, 11): expected_seats.append(f"A{i:02d}")
        for r in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
            for i in range(1, 14): expected_seats.append(f"{r}{i:02d}")
        for i in range(1, 19): expected_seats.append(f"J{i:02d}")
    else:
        expected_seats = []
        for i in range(1, 9): expected_seats.append(f"A{i:02d}")
        for r in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
            for i in range(1, 12): expected_seats.append(f"{r}{i:02d}")
        for i in range(1, 14): expected_seats.append(f"K{i:02d}")
        for i in range(1, 17): expected_seats.append(f"L{i:02d}")

    cv2.namedWindow("CineSight Seat Calibration Tool", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("CineSight Seat Calibration Tool", 1366, 768)
    cv2.setMouseCallback("CineSight Seat Calibration Tool", click_and_crop)

    print("\n" + "="*72)
    print(f" CÔNG CỤ HIỆU CHUẨN TỌA ĐỘ GHẾ CINESIGHT - CÁCH B")
    print(f" Chế độ: {room_title} (Mục tiêu: {len(expected_seats)} ghế)")
    print("="*72)
    print(" HƯỚNG DẪN THAO TÁC:")
    print("  • Chuột TRÁI  : Click 4 góc của ghế (hoặc 3-5 góc tùy hình dáng)")
    print("  • Chuột PHẢI : Hủy điểm vừa click nhầm (Undo)")
    print("  • Phím 'C'    : Chốt ghế (Hệ thống TỰ ĐỘNG GỢI Ý mã ghế tiếp theo, chỉ cần nhấn ENTER!)")
    print("  • Phím 'D'    : Xóa một ghế theo mã (VD gõ: A01 để xóa vẽ lại)")
    print("  • Phím 'R'    : Reset các điểm đang chấm dở")
    print("  • Phím 'S'    : LƯU TOÀN BỘ ra file JSON (seats_config_room3.json)")
    print("  • Phím 'Q'    : Thoát chương trình")
    print("="*72 + "\n")

    redraw_all()

    while True:
        cv2.imshow("CineSight Seat Calibration Tool", display_image)
        key = cv2.waitKey(20) & 0xFF

        if key == ord("c"):
            if len(current_polygon) >= 3:
                cv2.line(display_image, current_polygon[-1], current_polygon[0], (0, 255, 255), 2)
                cv2.imshow("CineSight Seat Calibration Tool", display_image)
                
                # Tìm mã ghế gợi ý tiếp theo chưa có trong danh sách
                next_suggest = next((s for s in expected_seats if s not in seats_data), "")
                if not next_suggest:
                    next_suggest = f"S{len(seats_data) + 1:02d}"
                
                prompt_text = f"\n👉 Nhập mã ghế [Gợi ý: {next_suggest}] (Nhấn ENTER để lấy ngay): "
                user_input = input(prompt_text).strip().upper()
                seat_code = user_input if user_input else next_suggest

                # Đóng kín đa giác
                closed_poly = current_polygon.copy()
                if closed_poly[0] != closed_poly[-1]:
                    closed_poly.append(closed_poly[0])
                
                seats_data[seat_code] = closed_poly
                # Tự động lưu tức thì vào file
                try:
                    save_to_target_rooms(target_rooms, silent=True)
                    print(f"   [+] Đã chốt & TỰ ĐỘNG LƯU ghế '{seat_code}'! (Tổng hiện có: {len(seats_data)}/{len(expected_seats)} ghế)")
                except Exception as e:
                    print(f"   [+] Đã chốt ghế '{seat_code}' (Lỗi tự lưu: {e})")
                current_polygon = []
                redraw_all()
            else:
                print("[-] Bạn cần click ít nhất 3 hoặc 4 điểm để tạo thành một chiếc ghế!")

        elif key == ord("d"):
            del_code = input("\n👉 Nhập mã ghế muốn XÓA (VD: A01): ").strip().upper()
            if del_code in seats_data:
                del seats_data[del_code]
                try:
                    save_to_target_rooms(target_rooms, silent=True)
                    print(f"   [-] Đã xóa ghế '{del_code}' thành công! (Còn lại: {len(seats_data)} ghế)")
                except Exception as e:
                    print(f"   [-] Đã xóa ghế '{del_code}' (Lỗi ghi file: {e})")
                redraw_all()
            else:
                print(f"   [!] Không tìm thấy ghế '{del_code}' trong danh sách!")

        elif key == ord("r"):
            current_polygon = []
            print("[*] Đã xóa nháp các điểm đang chấm dở!")
            redraw_all()

        elif key == ord("s"):
            save_to_target_rooms(target_rooms, silent=False)
            print("   Hệ thống AI Service sẽ sử dụng ngay tọa độ mới này cho lần quét tiếp theo.\n")

        elif key == ord("q"):
            print("\nĐã đóng công cụ hiệu chuẩn.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
