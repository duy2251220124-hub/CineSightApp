import cv2
import requests
import time
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Client giả lập Camera phòng chiếu, gửi khung hình lên AI Service liên tục.")
    parser.add_argument("--room", default="room1", help="Mã phòng chiếu (VD: room1)")
    parser.add_argument("--show", default="2026-09-29T19:30", help="Mã suất chiếu (VD: 2026-09-29T19:30)")
    parser.add_argument("--interval", type=int, default=5, help="Khoảng thời gian (giây) giữa các lần chụp")
    parser.add_argument("--source", default="0", help="Nguồn video: 0 (webcam) hoặc đường dẫn file .mp4")
    parser.add_argument("--endpoint", default="http://localhost:8000/api/v1/analyze", help="URL của API analyze")
    args = parser.parse_args()

    print(f"=======================================")
    print(f" KHỞI ĐỘNG CAMERA CLIENT - PHÒNG: {args.room}")
    print(f" Suất chiếu: {args.show}")
    print(f" API Server: {args.endpoint}")
    print(f"=======================================")

        source_val = 0 if args.source == "0" else args.source
    cap = cv2.VideoCapture(source_val)
    if not cap.isOpened():
        print("[LỖI] Không thể mở webcam. Vui lòng kiểm tra lại thiết bị!")
        sys.exit(1)

    print("[OK] Đã kết nối webcam. Đang chạy vòng lặp chụp ảnh...")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[-] Không thể đọc frame từ webcam, thử lại...")
                time.sleep(1)
                continue
            
            # Hiển thị cửa sổ camera cho người dùng thấy
            cv2.imshow(f"Camera - {args.room}", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Đã nhận lệnh thoát (Q).")
                break

            # Ghi frame ra file tạm
            tmp_filename = "temp_frame.jpg"
            cv2.imwrite(tmp_filename, frame)

            # Gửi lên AI Service
            print(f"\n[*] Đang gửi frame lên AI Service...")
            try:
                with open(tmp_filename, "rb") as f:
                    files = {"image": ("temp_frame.jpg", f, "image/jpeg")}
                    data = {"room_id": args.room, "show_id": args.show}
                    response = requests.post(args.endpoint, files=files, data=data, timeout=10)
                
                if response.status_code == 200:
                    res_json = response.json()
                    alerts = res_json.get("alerts", {})
                    
                    print(f"[+] Trả về thành công!")
                    print(f"  - Người phát hiện (YOLO): {res_json['summary']['total_detected_people']}")
                    print(f"  - Tập A (Đã soát vé): {res_json['summary']['tap_A_from_app']}")
                    print(f"  - Tập B (Đang ngồi) : {res_json['summary']['tap_B_from_camera']}")
                    
                    if alerts.get("illegal_occupants"):
                        print(f"  ❌ CẢNH BÁO: Khách lọt chưa vé tại ghế: {alerts['illegal_occupants']}")
                    if alerts.get("missing_guests"):
                        print(f"  ⚠️ CẢNH BÁO: Ghế có vé nhưng trống tại: {alerts['missing_guests']}")
                    if alerts.get("over_capacity"):
                        print(f"  🚨 CẢNH BÁO: VƯỢT SỨC CHỨA CỦA PHÒNG!")
                        
                    if not alerts.get("illegal_occupants") and not alerts.get("missing_guests"):
                        print(f"  ✅ Mọi thứ khớp! Không có cảnh báo.")
                else:
                    print(f"[-] Server trả về lỗi: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"[-] Lỗi kết nối tới server: {e}")

            print(f"[*] Đợi {args.interval} giây cho lần chụp tiếp theo...")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nĐã ngắt bằng Keyboard (Ctrl+C).")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        import os
        if os.path.exists("temp_frame.jpg"):
            os.remove("temp_frame.jpg")
        print("Đã tắt camera client.")

if __name__ == "__main__":
    main()
