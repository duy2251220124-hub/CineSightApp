import cv2
import json
import numpy as np
import os
import sys

# Biến toàn cục
current_polygon = []
seats_data = {}
image = None
clone = None

def click_and_crop(event, x, y, flags, param):
    global current_polygon, image, clone
    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))
        cv2.circle(image, (x, y), 3, (0, 255, 0), -1)
        if len(current_polygon) > 1:
            cv2.line(image, current_polygon[-2], current_polygon[-1], (0, 255, 0), 2)
        cv2.imshow("Calibration Tool", image)

def main():
    global image, clone, current_polygon, seats_data

    # ================================================================
    # THAY ĐỔI CHÍNH: Nhận tên phòng từ dòng lệnh
    # Chạy bằng lệnh: python calibrate_seats.py room1
    #                 python calibrate_seats.py room2
    #                 python calibrate_seats.py room3
    # ================================================================
    if len(sys.argv) < 2:
        print("LỖI: Vui lòng cung cấp tên phòng chiếu!")
        print("Cú pháp: python calibrate_seats.py <tên_phòng>")
        print("Ví dụ  : python calibrate_seats.py room1")
        sys.exit(1)

    room_id = sys.argv[1]  # VD: "room1", "room2", "imax", "4dx"
    
    # Mỗi phòng có ảnh đầu vào và file JSON đầu ra riêng biệt
    img_path = f'calibration_images/{room_id}.jpg'
    output_path = f'seats_config_{room_id}.json'

    print(f"\n{'='*55}")
    print(f" HIỆU CHUẨN PHÒNG: [{room_id.upper()}]")
    print(f" Đọc ảnh từ  : {img_path}")
    print(f" Lưu JSON ra : {output_path}")
    print(f"{'='*55}")

    # Tạo thư mục chứa ảnh nếu chưa có
    os.makedirs('calibration_images', exist_ok=True)
    os.makedirs('seats_configs', exist_ok=True)
    output_path = f'seats_configs/seats_config_{room_id}.json'

    if os.path.exists(img_path):
        image = cv2.imread(img_path)
        print(f"[OK] Đã tải ảnh phòng {room_id} thành công!")
    else:
        print(f"[CẢNH BÁO] Không tìm thấy '{img_path}'.")
        print(f"[HƯỚNG DẪN] Hãy chụp 1 ảnh phòng chiếu TRỐNG từ góc nhìn camera,")
        print(f"            đặt tên '{room_id}.jpg' vào thư mục 'calibration_images/'")
        print(f"            rồi chạy lại lệnh này.")
        print(f"\nĐang tạo ảnh đen giả lập để bạn có thể test tool trước...")
        image = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.putText(image, f"PHONG: {room_id.upper()}", (200, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 200, 255), 3)
        cv2.putText(image, "Dat anh rạp trung vao calibration_images/", (30, 320),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    clone = image.copy()
    cv2.namedWindow("Calibration Tool")
    cv2.setMouseCallback("Calibration Tool", click_and_crop)

    print("\n HƯỚNG DẪN:")
    print("  Click chuột trái → Chấm góc của 1 ghế")
    print("  Phím 'C'         → Chốt ghế (nhập mã ghế trong Terminal)")
    print("  Phím 'R'         → Reset bản vẽ nháp")
    print("  Phím 'S'         → Lưu toàn bộ ra file JSON")
    print("  Phím 'Q'         → Thoát\n")

    while True:
        cv2.imshow("Calibration Tool", image)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("c"):
            if len(current_polygon) > 2:
                cv2.line(image, current_polygon[-1], current_polygon[0], (0, 255, 0), 2)
                cv2.imshow("Calibration Tool", image)
                seat_name = input(f"-> Nhập mã ghế vừa vẽ (VD: A1, B3): ")
                seats_data[seat_name] = current_polygon.copy()
                print(f"[+] Đã lưu ghế '{seat_name}' cho phòng '{room_id}'!")
                current_polygon = []
            else:
                print("[-] Cần ít nhất 3 điểm để tạo vùng ghế!")

        elif key == ord("r"):
            image = clone.copy()
            current_polygon = []
            print("[*] Đã reset bản vẽ!")

        elif key == ord("s"):
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(seats_data, f, indent=4, ensure_ascii=False)
            print(f"[✓] Đã lưu {len(seats_data)} ghế của phòng '{room_id}' vào '{output_path}'!")

        elif key == ord("q"):
            print("Thoát chương trình.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
