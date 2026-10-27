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

def prepare_oversampling():
    base_dir = r"C:\CineSightApp\ai_service\datasets\head_v2"
    train_img = os.path.join(base_dir, "images", "train")
    train_lbl = os.path.join(base_dir, "labels", "train")
    
    src_img = os.path.join(train_img, "room3_real_enhanced.jpg")
    src_lbl = os.path.join(train_lbl, "room3_real_enhanced.txt")
    
    if not os.path.exists(src_img) or not os.path.exists(src_lbl):
        print("[-] Missing room3_real_enhanced.jpg or .txt in train set")
        return
        
    # Oversample 12 copies so Room 3 has ~12% weight in training
    print("[+] Cân bằng dữ liệu (Oversampling) cho Phòng chiếu số 3 (12 bản sao)...")
    for i in range(1, 13):
        aug_img = os.path.join(train_img, f"room3_aug_{i:02d}.jpg")
        aug_lbl = os.path.join(train_lbl, f"room3_aug_{i:02d}.txt")
        shutil.copy2(src_img, aug_img)
        shutil.copy2(src_lbl, aug_lbl)
    print("    -> Đã bổ sung 12 bản sao vào tập train thành công.")

def main():
    print("=" * 70)
    print("=== BẮT ĐẦU HUẤN LUYỆN FINE-TUNE YOLO VỚI DỮ LIỆU CAMERA RẠP 3 (58 ĐẦU NGƯỜI) ===")
    print("=" * 70)

    base_dir = r"C:\CineSightApp\ai_service"
    dataset_yaml = os.path.join(base_dir, "dataset_head_v2.yaml")
    base_weights = os.path.join(base_dir, "models", "best_head_v2.pt")
    models_dir = os.path.join(base_dir, "models")
    
    label_path = os.path.join(base_dir, "datasets", "head_v2", "labels", "train", "room3_real_enhanced.txt")
    if not os.path.exists(label_path):
        print(f"[-] Chưa tìm thấy file nhãn tại: {label_path}")
        return

    with open(label_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    print(f"[✓] Đã nạp chính xác {len(lines)} nhãn đầu người thực tế của Phòng chiếu số 3.")

    prepare_oversampling()

    print(f"\n[+] Khởi tạo mô hình nền: {base_weights}")
    model = YOLO(base_weights)

    t_start = time.time()
    print("\n[+] Đang chạy huấn luyện 15 epochs (Fine-tune chuyển giao)...")
    results = model.train(
        data=dataset_yaml,
        epochs=15,
        imgsz=640,
        batch=8,
        workers=2,
        device="cpu",
        lr0=0.001,
        lrf=0.01,
        project=os.path.join(base_dir, "runs", "detect"),
        name="head_v3_room3",
        exist_ok=True,
        seed=42,
        plots=True,
        patience=8,
        verbose=True
    )
    duration = time.time() - t_start

    best_trained = os.path.join(base_dir, "runs", "detect", "head_v3_room3", "weights", "best.pt")
    target_v3 = os.path.join(models_dir, "best_head_v3.pt")
    target_active = os.path.join(models_dir, "best_head_v2.pt")

    if os.path.exists(best_trained):
        shutil.copy2(best_trained, target_v3)
        backup_v2 = os.path.join(models_dir, "best_head_v2_backup_before_r3.pt")
        if not os.path.exists(backup_v2):
            shutil.copy2(target_active, backup_v2)
        shutil.copy2(best_trained, target_active)
        print("\n" + "=" * 70)
        print(f"[THÀNH CÔNG] ĐÃ HOÀN TẤT HUẤN LUYỆN MODEL MỚI:")
        print(f"  -> Đã lưu: {target_v3}")
        print(f"  -> Đã cập nhật vào model chính: {target_active}")
        print(f"  Thời gian huấn luyện: {duration / 60.0:.2f} phút")
        print("=" * 70)
    else:
        print("[!] Không tìm thấy best.pt trong thư mục kết quả huấn luyện.")

if __name__ == "__main__":
    main()
