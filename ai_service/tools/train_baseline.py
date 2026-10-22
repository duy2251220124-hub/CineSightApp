import os
import sys
import time
import json
import shutil
from ultralytics import YOLO

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("=" * 60)
    print("=== BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH BASELINE (PHASE 5) ===")
    print("=" * 60)
    
    base_dir = r"c:\CineSightApp\ai_service"
    dataset_yaml = os.path.join(base_dir, "dataset_stage_a.yaml")
    base_weights = os.path.join(base_dir, "yolov8n.pt")
    models_dir = os.path.join(base_dir, "models")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    print(f"Dataset YAML: {dataset_yaml}")
    print(f"Pretrained weights: {base_weights}")
    print("Cấu hình huấn luyện:")
    print("  - Kích thước ảnh (imgsz): 800")
    print("  - Số epochs: 50")
    print("  - Batch size: 4")
    print("  - Thiết bị: CPU (AMD Ryzen 5 3500U)")
    print("  - Dự kiến thời gian: ~40 phút")
    print("-" * 60)
    
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
        name="baseline_stage_a",
        exist_ok=True,
        seed=42,
        plots=True,
        verbose=True
    )
    
    t_train = time.time() - t_start
    print("-" * 60)
    print(f"Hoàn thành huấn luyện 50 epochs trong: {t_train / 60:.2f} phút ({t_train:.1f} giây)")
    
    # 2. Lưu trọng số tốt nhất vào models/baseline_stage_a.pt
    best_weights_src = os.path.join(base_dir, "runs", "detect", "baseline_stage_a", "weights", "best.pt")
    target_best_weights = os.path.join(models_dir, "baseline_stage_a.pt")
    
    if os.path.exists(best_weights_src):
        shutil.copy2(best_weights_src, target_best_weights)
        print(f"Đã sao chép best weights: {target_best_weights}")
    else:
        print(f"Cảnh báo: Không tìm thấy {best_weights_src}, tìm kiếm last.pt...")
        last_weights_src = os.path.join(base_dir, "runs", "detect", "baseline_stage_a", "weights", "last.pt")
        if os.path.exists(last_weights_src):
            shutil.copy2(last_weights_src, target_best_weights)
            print(f"Đã sao chép last weights: {target_best_weights}")
    
    # 3. Đánh giá chất lượng mô hình trên tập Val Stage A
    print("\n--- ĐÁNH GIÁ MÔ HÌNH BASELINE TRÊN TẬP VAL (STAGE A) ---")
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
    
    print("\nKết quả Baseline Validation Metrics:")
    print(f"  - Precision (P): {precision:.4f}")
    print(f"  - Recall (R)   : {recall:.4f}")
    print(f"  - mAP@50       : {map50:.4f}")
    print(f"  - mAP@50-95    : {map50_95:.4f}")
    
    # Ghi báo cáo metrics
    report_file = os.path.join(reports_dir, "baseline_stage_a_metrics.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=== BASELINE MODEL METRICS (STAGE A - 50 EPOCHS - IMGSZ 800) ===\n")
        f.write(f"Training Time: {t_train / 60:.2f} mins\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall: {recall:.4f}\n")
        f.write(f"mAP@50: {map50:.4f}\n")
        f.write(f"mAP@50-95: {map50_95:.4f}\n")
        f.write(f"Weights file: {target_best_weights}\n")
    print(f"Đã ghi báo cáo metrics vào: {report_file}")
    
    # 4. Sinh tiền nhãn (Pre-labels) cho 123 ảnh còn lại
    print("\n" + "=" * 60)
    print("=== SINH TIỀN NHÃN (PRE-LABELS) CHO CÁC ẢNH CÒN LẠI ===")
    print("=" * 60)
    
    head_v2_dir = os.path.join(base_dir, "datasets", "head_v2")
    prelabel_root = os.path.join(head_v2_dir, "labels_prelabel")
    stage_a_file = os.path.join(head_v2_dir, "stage_a_list.txt")
    
    stage_a_set = set()
    if os.path.exists(stage_a_file):
        with open(stage_a_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    stage_a_set.add(line)
    
    splits = ["train", "val", "test"]
    prelabel_stats = {
        "train": {"total_frames": 0, "prelabeled_frames": 0, "heads": 0},
        "val": {"total_frames": 0, "prelabeled_frames": 0, "heads": 0},
        "test": {"total_frames": 0, "prelabeled_frames": 0, "heads": 0}
    }
    
    prelabel_meta = {}
    
    for split in splits:
        img_split_dir = os.path.join(head_v2_dir, "images", split)
        out_lbl_dir = os.path.join(prelabel_root, split)
        os.makedirs(out_lbl_dir, exist_ok=True)
        
        if not os.path.exists(img_split_dir):
            continue
            
        img_files = sorted([f for f in os.listdir(img_split_dir) if f.lower().endswith((".jpg", ".png"))])
        prelabel_stats[split]["total_frames"] = len(img_files)
        
        for img_name in img_files:
            key = f"{split}/{img_name}"
            # Bỏ qua 40 ảnh Stage A đã được gán thủ công và xác minh
            if key in stage_a_set:
                continue
                
            img_path = os.path.join(img_split_dir, img_name)
            txt_name = os.path.splitext(img_name)[0] + ".txt"
            out_txt_path = os.path.join(out_lbl_dir, txt_name)
            
            # Chạy dự đoán
            pred_results = val_model.predict(
                source=img_path,
                imgsz=800,
                conf=0.25,
                iou=0.6,
                device="cpu",
                verbose=False
            )
            
            boxes_info = []
            with open(out_txt_path, "w", encoding="utf-8") as lf:
                if len(pred_results) > 0 and pred_results[0].boxes is not None:
                    boxes = pred_results[0].boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        if cls_id != 0:
                            continue
                        conf = float(box.conf[0].item())
                        # normalized xywh: box.xywhn
                        xywhn = box.xywhn[0].tolist()
                        xc, yc, w, h = xywhn
                        lf.write(f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                        boxes_info.append({"conf": round(conf, 4), "box": [round(c, 6) for c in [xc, yc, w, h]]})
            
            prelabel_stats[split]["prelabeled_frames"] += 1
            prelabel_stats[split]["heads"] += len(boxes_info)
            prelabel_meta[key] = {
                "head_count": len(boxes_info),
                "predictions": boxes_info
            }
            
    # Ghi metadata chi tiết kèm độ tin cậy
    meta_path = os.path.join(reports_dir, "prelabels_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(prelabel_meta, f, indent=2, ensure_ascii=False)
        
    print("\nThống kê tiền nhãn đã sinh:")
    total_pre_frames = 0
    total_pre_heads = 0
    for split, s in prelabel_stats.items():
        print(f"  - Split '{split}': {s['prelabeled_frames']} ảnh đã sinh tiền nhãn | Tổng {s['heads']} đầu người")
        total_pre_frames += s["prelabeled_frames"]
        total_pre_heads += s["heads"]
        
    print(f"\nTổng cộng: Đã sinh tiền nhãn cho {total_pre_frames} ảnh còn lại ({total_pre_heads} đầu người).")
    print(f"Thư mục lưu tiền nhãn: {prelabel_root}")
    print(f"Tệp metadata độ tin cậy: {meta_path}")
    print("=" * 60)
    print("=== HOÀN TẤT HUẤN LUYỆN BASELINE VÀ SINH TIỀN NHÃN (PHASE 5) ===")
    print("=" * 60)

if __name__ == "__main__":
    main()

