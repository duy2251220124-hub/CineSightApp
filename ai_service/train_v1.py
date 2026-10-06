from ultralytics import YOLO
import sys

# Chuyển hướng log
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger("train_log.txt")

def main():
    print("[INFO] Bắt đầu huấn luyện mô hình YOLOv8n (Bản V1 Placeholder)...")
    
    model = YOLO('yolov8n.pt')
    
    results = model.train(
        data='dataset.yaml',
        epochs=10,             # Theo thoả thuận
        imgsz=320,             # Giảm size để CPU chạy nhanh hơn nữa
        batch=4,
        name='head_detect_v1',
        device='cpu',
        save=True
    )
    
    print("\n" + "="*50)
    print("[THÀNH CÔNG] Huấn luyện hoàn tất!")
    print("File weights tốt nhất được lưu tại: runs/detect/head_detect_v1/weights/best.pt")
    
    # Copy file ra ngoài và đổi tên thành best_v1.pt
    import shutil, os
    best_path = 'runs/detect/head_detect_v1/weights/best.pt'
    if os.path.exists(best_path):
        shutil.copy(best_path, 'best_v1.pt')
        print("Đã copy ra root: best_v1.pt")
    
    print("="*50)

if __name__ == '__main__':
    main()
