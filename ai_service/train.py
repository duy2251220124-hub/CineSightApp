from ultralytics import YOLO

def main():
    print("[INFO] Bắt đầu khởi tạo huấn luyện mô hình YOLOv8s...")
    
    # Load mô hình YOLOv8 small pre-trained (cân bằng tốt giữa tốc độ và độ chính xác)
    model = YOLO('yolov8n.pt')
    
    # Bắt đầu quá trình Fine-tune (Huấn luyện lại) trên dữ liệu đầu người ảnh hồng ngoại
    results = model.train(
        data='dataset.yaml',   # Đường dẫn tới file cấu hình dữ liệu
        epochs=50,             # Số vòng lặp huấn luyện (Đồ án nên để 50-100 vòng)
        imgsz=640,             # Kích thước ảnh đầu vào chuẩn của YOLO
        batch=8,               # Số ảnh nạp vào mỗi lần (Hạ xuống 4 nếu máy báo hết RAM)
        name='ir_head_detect', # Tên thư mục lưu kết quả huấn luyện
        # Lưu ý: Nếu máy bạn có Card rời NVIDIA, hãy đổi device='cpu' thành device='0' để chạy siêu tốc.
        device='cpu',
        # Các thông số chống Overfitting cơ bản
        patience=10,           
        save=True
    )
    
    print("\n" + "="*50)
    print("[THÀNH CÔNG] Huấn luyện hoàn tất!")
    print("File weights tốt nhất (model hoàn chỉnh) được lưu tại:")
    print("-> runs/detect/ir_head_detect/weights/best.pt")
    print("Bạn hãy copy file best.pt này, sửa lại trong file main.py thay cho yolov8n.pt nhé!")
    print("="*50)

if __name__ == '__main__':
    main()

