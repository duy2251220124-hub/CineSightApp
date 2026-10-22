import os
import sys
import re
import shutil
import cv2
import numpy as np
from ultralytics import YOLO

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def blur_region(img, x1, y1, x2, y2, pad_ratio=0.15):
    h, w = img.shape[:2]
    bw = x2 - x1
    bh = y2 - y1
    px = int(bw * pad_ratio)
    py = int(bh * pad_ratio)

    rx1 = max(0, int(x1 - px))
    ry1 = max(0, int(y1 - py))
    rx2 = min(w, int(x2 + px))
    ry2 = min(h, int(y2 + py))

    if rx2 <= rx1 or ry2 <= ry1:
        return

    roi = img[ry1:ry2, rx1:rx2]
    # 1. Pixelate (giảm độ phân giải xuống lưới thô 6x6 rồi phóng lại)
    rh, rw = roi.shape[:2]
    small_w = max(4, rw // 6)
    small_h = max(4, rh // 6)
    temp = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
    pixelated = cv2.resize(temp, (rw, rh), interpolation=cv2.INTER_NEAREST)
    # 2. Kết hợp Gaussian Blur mạnh
    blurred = cv2.GaussianBlur(pixelated, (31, 31), 15)
    img[ry1:ry2, rx1:rx2] = blurred

def load_all_gt_boxes(head_v2_dir):
    """
    Trả về dict: { base_stem (vd: 'room1_cam_edited_0000s'): [(xc, yc, w, h), ...] }
    """
    gt_map = {}
    lbl_root = os.path.join(head_v2_dir, "labels")
    for split in ["train", "val", "test"]:
        s_dir = os.path.join(lbl_root, split)
        if not os.path.exists(s_dir):
            continue
        for f in os.listdir(s_dir):
            if f.endswith(".txt"):
                stem = os.path.splitext(f)[0]
                boxes = []
                with open(os.path.join(s_dir, f), "r", encoding="utf-8") as lf:
                    for line in lf:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            _, xc, yc, bw, bh = map(float, parts[:5])
                            boxes.append((xc, yc, bw, bh))
                gt_map[stem] = boxes
    return gt_map

def main():
    print("=" * 65)
    print("=== CÔNG CỤ ẨN DANH GƯƠNG MẶT KHÁN GIẢ TRÊN ẢNH BÁO CÁO (PHASE 10) ===")
    print("=" * 65)

    base_dir = r"c:\CineSightApp\ai_service"
    reports_dir = os.path.join(base_dir, "reports")
    head_v2_dir = os.path.join(base_dir, "datasets", "head_v2")
    model_path = os.path.join(base_dir, "models", "best_head_v2.pt")
    anon_root = os.path.join(reports_dir, "anonymized_figures")
    downloads_dir = r"C:\Users\Dell KIM ANH\Downloads"

    os.makedirs(anon_root, exist_ok=True)

    gt_map = load_all_gt_boxes(head_v2_dir)
    model = YOLO(model_path) if os.path.exists(model_path) else None

    target_folders = [
        ("qc_overlays", os.path.join(reports_dir, "qc_overlays")),
        ("failure_cases", os.path.join(reports_dir, "failure_cases"))
    ]

    total_images_processed = 0
    total_regions_blurred = 0
    sample_saved_path = None

    for sub_name, folder_path in target_folders:
        if not os.path.exists(folder_path):
            continue
        out_sub_dir = os.path.join(anon_root, sub_name)
        os.makedirs(out_sub_dir, exist_ok=True)

        img_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".png"))])
        for fname in img_files:
            in_path = os.path.join(folder_path, fname)
            img = cv2.imread(in_path)
            if img is None:
                continue

            ih, iw = img.shape[:2]
            regions = []

            # Tìm stem gốc (vd: room1_cam_edited_0425s)
            m = re.search(r"(room1_cam_edited_\d+s)", fname)
            if m:
                stem = m.group(1)
                for (xc, yc, bw, bh) in gt_map.get(stem, []):
                    x1 = (xc - bw / 2) * iw
                    y1 = (yc - bh / 2) * ih
                    x2 = (xc + bw / 2) * iw
                    y2 = (yc + bh / 2) * ih
                    regions.append((x1, y1, x2, y2))

            # Chạy thêm YOLO với ngưỡng thấp để bắt mọi khuôn mặt phát sinh
            if model is not None:
                res = model.predict(img, conf=0.12, imgsz=800, classes=[0], verbose=False)
                for r in res:
                    if r.boxes is not None:
                        for b in r.boxes:
                            x1, y1, x2, y2 = b.xyxy[0].tolist()
                            regions.append((x1, y1, x2, y2))

            for (x1, y1, x2, y2) in regions:
                blur_region(img, x1, y1, x2, y2)
                total_regions_blurred += 1

            out_path = os.path.join(out_sub_dir, f"anon_{fname}")
            cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            total_images_processed += 1

            if sample_saved_path is None:
                sample_saved_path = out_path

        print(f"Đã ẩn danh {len(img_files)} ảnh trong thư mục '{sub_name}' -> {out_sub_dir}")

    if sample_saved_path and os.path.exists(downloads_dir):
        dest_sample = os.path.join(downloads_dir, "sample_anonymized_figure.jpg")
        shutil.copy2(sample_saved_path, dest_sample)
        print(f"Đã sao chép 1 ảnh mẫu đã làm mờ ẩn danh sang: {dest_sample}")

    print("-" * 65)
    print(f"Tổng số ảnh báo cáo đã ẩn danh : {total_images_processed} ảnh")
    print(f"Tổng số vùng đầu/mặt đã làm mờ : {total_regions_blurred} vùng")
    print(f"Thư mục lưu trữ an toàn        : {anon_root}")
    print("=" * 65)
    print("=== HOÀN TẤT ẨN DANH GƯƠNG MẶT BÁO CÁO (PHASE 10 PASS) ===")
    print("=" * 65)

if __name__ == "__main__":
    main()

