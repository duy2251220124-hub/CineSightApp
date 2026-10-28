import os
import sys
import shutil
import time
from ultralytics import YOLO

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("=" * 70)
    print("=== HUẤN LUYỆN MÔ HÌNH V4 TỪ DỮ LIỆU ĐA DẠNG ÁNH SÁNG VIDEO 30 PHÚT ===")
    print("=" * 70)

    base_dir = r"C:\CineSightApp\ai_service"
    dataset_yaml = os.path.join(base_dir, "dataset_head_v2.yaml")
    base_weights = os.path.join(base_dir, "models", "best_head_v3.pt")
    models_dir = os.path.join(base_dir, "models")

    if not os.path.exists(base_weights):
        base_weights = os.path.join(base_dir, "models", "best_head_v2.pt")

    print(f"[+] Khởi tạo từ trọng số nền tốt nhất: {base_weights}")
    model = YOLO(base_weights)

    t_start = time.time()
    print("\n[+] Bắt đầu fine-tune 15 epochs trên toàn bộ tập dữ liệu (Phòng 1 + Phòng 3 đa thời điểm)...")
    results = model.train(
        data=dataset_yaml,
        epochs=15,
        imgsz=640,
        batch=8,
        workers=2,
        device="cpu",
        lr0=0.0008,
        lrf=0.01,
        project=os.path.join(base_dir, "runs", "detect"),
        name="head_v4_video_30min",
        exist_ok=True,
        seed=42,
        plots=True,
        patience=8,
        verbose=True
    )
    duration = time.time() - t_start

    best_trained = os.path.join(base_dir, "runs", "detect", "head_v4_video_30min", "weights", "best.pt")
    target_v4 = os.path.join(models_dir, "best_head_v4.pt")
    target_active = os.path.join(models_dir, "best_head_v2.pt")

    if os.path.exists(best_trained):
        shutil.copy2(best_trained, target_v4)
        shutil.copy2(best_trained, target_active)
        print("\n" + "=" * 70)
        print(f"[THÀNH CÔNG] ĐÃ HOÀN TẤT HUẤN LUYỆN MODEL V4:")
        print(f"  -> Đã lưu mô hình: {target_v4}")
        print(f"  -> Đã cập nhật vào mô hình chạy chính: {target_active}")
        print(f"  Thời gian huấn luyện: {duration / 60.0:.2f} phút")
        print("=" * 70)
    else:
        print("[!] Không tìm thấy best.pt trong thư mục kết quả huấn luyện.")

if __name__ == "__main__":
    main()

