import os
import sys
import time
import shutil
from ultralytics import YOLO

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("=" * 65)
    print("=== BẮT ĐẦU HUẤN LUYỆN CHÍNH THỨC TOÀN BỘ DATASET (PHASE 7) ===")
    print("=" * 65)

    base_dir = r"c:\CineSightApp\ai_service"
    dataset_yaml = os.path.join(base_dir, "dataset_head_v2.yaml")
    base_weights = os.path.join(base_dir, "yolov8n.pt")
    models_dir = os.path.join(base_dir, "models")
    reports_dir = os.path.join(base_dir, "reports")
    downloads_dir = r"C:\Users\Dell KIM ANH\Downloads"

    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    print(f"Dataset YAML: {dataset_yaml}")
    print(f"Pretrained weights: {base_weights}")
    print("Cấu hình huấn luyện chính thức:")
    print("  - Kích thước ảnh (imgsz): 800")
    print("  - Số epochs: 50")
    print("  - Batch size: 4")
    print("  - Early stopping patience: 20")
    print("  - Thiết bị: CPU (AMD Ryzen 5 3500U)")
    print("  - Tập huấn luyện (Train): 98 ảnh (570 đầu người)")
    print("  - Tập kiểm tra (Val): 22 ảnh (87 đầu người)")
    print("  - Tập Test hoàn toàn độc lập (Test): 43 ảnh (chỉ dùng ở Phase 8)")
    print("-" * 65)

    t_start = time.time()

    model = YOLO(base_weights)

    train_results = model.train(
        data=dataset_yaml,
        epochs=50,
        imgsz=800,
        batch=4,
        workers=2,
        device="cpu",
        project=os.path.join(base_dir, "runs", "detect"),
        name="head_v2_official",
        exist_ok=True,
        seed=42,
        plots=True,
        patience=20,
        verbose=True
    )

    t_train = time.time() - t_start
    print("-" * 65)
    print(f"Hoàn thành huấn luyện trong: {t_train / 60:.2f} phút ({t_train:.1f} giây)")

    # 2. Lưu trọng số tốt nhất vào models/best_head_v2.pt
    best_weights_src = os.path.join(base_dir, "runs", "detect", "head_v2_official", "weights", "best.pt")
    target_best_weights = os.path.join(models_dir, "best_head_v2.pt")

    if os.path.exists(best_weights_src):
        shutil.copy2(best_weights_src, target_best_weights)
        print(f"Đã sao chép best weights: {target_best_weights}")
    else:
        last_weights_src = os.path.join(base_dir, "runs", "detect", "head_v2_official", "weights", "last.pt")
        if os.path.exists(last_weights_src):
            shutil.copy2(last_weights_src, target_best_weights)
            print(f"Đã sao chép last weights: {target_best_weights}")

    # 3. Đánh giá kiểm định mô hình chính thức trên tập Val (22 ảnh)
    print("\n--- ĐÁNH GIÁ MÔ HÌNH CHÍNH THỨC TRÊN TẬP VAL (22 ẢNH) ---")
    val_model = YOLO(target_best_weights)
    val_metrics = val_model.val(
        data=dataset_yaml,
        imgsz=800,
        device="cpu",
        split="val"
    )

    precision = float(val_metrics.box.mp)
    recall = float(val_metrics.box.mr)
    map50 = float(val_metrics.box.map50)
    map50_95 = float(val_metrics.box.map)

    print("\nKết quả Official Validation Metrics:")
    print(f"  - Precision (P): {precision:.4f} ({precision * 100:.1f}%)")
    print(f"  - Recall (R)   : {recall:.4f} ({recall * 100:.1f}%)")
    print(f"  - mAP@50       : {map50:.4f} ({map50 * 100:.1f}%)")
    print(f"  - mAP@50-95    : {map50_95:.4f} ({map50_95 * 100:.1f}%)")

    # 4. Sao chép biểu đồ kết quả
    run_dir = os.path.join(base_dir, "runs", "detect", "head_v2_official")
    for fname, target_name in [
        ("results.png", "official_results.png"),
        ("val_batch0_pred.jpg", "official_val_pred.jpg"),
        ("confusion_matrix.png", "official_confusion_matrix.png"),
        ("BoxF1_curve.png", "official_F1_curve.png"),
        ("BoxPR_curve.png", "official_PR_curve.png")
    ]:
        src = os.path.join(run_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(reports_dir, target_name))
            if os.path.exists(downloads_dir):
                shutil.copy2(src, os.path.join(downloads_dir, target_name))
            print(f"Đã sao chép biểu đồ: {target_name}")

    # Ghi tệp báo cáo tổng hợp
    summary_path = os.path.join(reports_dir, "official_training_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=== OFFICIAL MODEL TRAINING SUMMARY (PHASE 7) ===\n")
        f.write(f"Training Time: {t_train / 60:.2f} mins\n")
        f.write(f"Train images: 98 (570 heads)\n")
        f.write(f"Val images: 22 (87 heads)\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall: {recall:.4f}\n")
        f.write(f"mAP@50: {map50:.4f}\n")
        f.write(f"mAP@50-95: {map50_95:.4f}\n")
        f.write(f"Official Weights: {target_best_weights}\n")

    print(f"Đã ghi báo cáo tóm tắt vào: {summary_path}")
    print("=" * 65)
    print("=== HOÀN TẤT HUẤN LUYỆN CHÍNH THỨC (PHASE 7) ===")
    print("=" * 65)

if __name__ == "__main__":
    main()

