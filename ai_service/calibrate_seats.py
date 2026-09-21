import cv2
import json
import numpy as np
import os

# Biến toàn cục để lưu trữ trạng thái vẽ
current_polygon = []
seats_data = {}
image = None
clone = None

def click_and_crop(event, x, y, flags, param):
    global current_polygon, image, clone
    
    # Bắt sự kiện click chuột trái để chọn điểm
    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))
        cv2.circle(image, (x, y), 3, (0, 255, 0), -1)
        
        # Nối các điểm lại với nhau thành đường viền
        if len(current_polygon) > 1:
            cv2.line(image, current_polygon[-2], current_polygon[-1], (0, 255, 0), 2)
        cv2.imshow("Calibration Tool", image)

def main():
    global image, clone, current_polygon, seats_data
    
    # 1. Load ảnh chụp từ camera hồng ngoại thực tế
    # Bạn hãy đổi file sample_image.jpg thành ảnh lấy từ camera rạp phim của bạn
    img_path = 'sample_image.jpg'
    
    if os.path.exists(img_path):
        image = cv2.imread(img_path)
    else:
        print(f"[CẢNH BÁO] Không tìm thấy '{img_path}'. Tạo ảnh đen giả lập để bạn test tool.")
        image = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.putText(image, "NO IMAGE FOUND", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 2)
        cv2.putText(image, "Doi ten anh camera cua ban thanh 'sample_image.jpg'", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
        
    clone = image.copy()
    cv2.namedWindow("Calibration Tool")
    cv2.setMouseCallback("Calibration Tool", click_and_crop)

    print("\n" + "="*50)
    print(" HƯỚNG DẪN SỬ DỤNG TOOL HIỆU CHUẨN TỌA ĐỘ GHẾ")
    print("="*50)
    print("1. Click chuột trái để chấm các góc của vùng ghế.")
    print("2. Nhấn phím 'c' khi chấm xong 1 ghế (chương trình sẽ hỏi mã ghế).")
    print("3. Nhấn phím 'r' để reset lại bức ảnh (xóa các nét vẽ nháp).")
    print("4. Nhấn phím 's' để LƯU toàn bộ cấu hình ra file JSON.")
    print("5. Nhấn phím 'q' để Thoát.")
    print("="*50 + "\n")

    while True:
        cv2.imshow("Calibration Tool", image)
        key = cv2.waitKey(1) & 0xFF

        # Nhấn 'c' để chốt polygon (hoàn thành 1 ghế)
        if key == ord("c"):
            if len(current_polygon) > 2:
                # Nối điểm cuối với điểm đầu để đóng vòng
                cv2.line(image, current_polygon[-1], current_polygon[0], (0, 255, 0), 2)
                cv2.imshow("Calibration Tool", image)
                
                # Hỏi user nhập mã ghế
                seat_name = input("-> Nhập mã ghế vừa vẽ (VD: A1, B3): ")
                seats_data[seat_name] = current_polygon.copy()
                print(f"[+] Đã lưu ghế {seat_name} với các tọa độ: {current_polygon}")
                
                # Reset mảng vẽ cho ghế tiếp theo
                current_polygon = []
            else:
                print("[-] LỖI: Bạn phải click ít nhất 3 điểm để tạo thành một vùng ghế!")
        
        # Nhấn 'r' để reset ảnh
        elif key == ord("r"):
            image = clone.copy()
            current_polygon = []
            print("[*] Đã reset bản vẽ!")
            
        # Nhấn 's' để lưu ra JSON
        elif key == ord("s"):
            with open("seats_config.json", "w", encoding='utf-8') as f:
                json.dump(seats_data, f, indent=4)
            print("[V] Đã xuất cấu hình thành công ra file 'seats_config.json'!")
            
        # Nhấn 'q' để thoát
        elif key == ord("q"):
            print("Thoát chương trình...")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

