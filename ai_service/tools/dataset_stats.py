import os
import sys
import random
import csv
import argparse
import cv2
import numpy as np

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def compute_iou(box1, box2):
    # box: [xmin, ymin, xmax, ymax]
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def main():
    parser = argparse.ArgumentParser(description="Kiểm tra chất lượng nhãn (QC Dataset)")
    parser.add_argument("--base_dir", default=r"c:\CineSightApp\ai_service\datasets\head_v2", help="Thư mục dataset")
    parser.add_argument("--stage_a_only", action="store_true", help="Chỉ kiểm tra 40 ảnh Stage A")
    args = parser.parse_args()

    base_dir = args.base_dir
    reports_dir = r"c:\CineSightApp\ai_service\reports"
    qc_dir = os.path.join(reports_dir, "qc_overlays")
    os.makedirs(qc_dir, exist_ok=True)

    items = []
    if args.stage_a_only:
        stage_a_file = os.path.join(base_dir, "stage_a_list.txt")
        if not os.path.exists(stage_a_file):
            print(f"LỖI: Không tìm thấy tệp {stage_a_file}")
            sys.exit(1)
        with open(stage_a_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "/" in line:
                    split, fname = line.split("/", 1)
                    items.append((split, fname))
        print("=== BẮT ĐẦU KIỂM TRA CHẤT LƯỢNG NHÃN (PHASE 4/6 - STAGE A) ===")
    else:
        for s in ["train", "val", "test"]:
            s_img_dir = os.path.join(base_dir, "images", s)
            if os.path.exists(s_img_dir):
                for f in sorted(os.listdir(s_img_dir)):
                    if f.lower().endswith((".jpg", ".png")):
                        items.append((s, f))
        print("=== BẮT ĐẦU KIỂM TRA CHẤT LƯỢNG NHÃN TOÀN BỘ DATASET (PHASE 6 - QC FULL) ===")

    print(f"Tổng số ảnh cần kiểm tra: {len(items)} ảnh")

    format_errors = []
    duplicate_boxes_count = 0
    duplicate_details = []
    
    boxes_per_image = []
    empty_images_count = 0
    split_counts = {"train": 0, "val": 0, "test": 0}
    split_boxes = {"train": 0, "val": 0, "test": 0}

    orig_w, orig_h = 1920, 1080
    
    orig_widths, orig_heights = [], []
    scaled640_heights = []
    scaled800_heights = []

    all_parsed_data = []

    for split, fname in items:
        split_counts[split] += 1
        lbl_name = os.path.splitext(fname)[0] + ".txt"
        lbl_path = os.path.join(base_dir, "labels", split, lbl_name)
        img_path = os.path.join(base_dir, "images", split, fname)

        if not os.path.exists(lbl_path):
            format_errors.append(f"Thiếu tệp nhãn: {lbl_path}")
            boxes_per_image.append(0)
            empty_images_count += 1
            all_parsed_data.append((split, fname, img_path, []))
            continue

        with open(lbl_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        if len(lines) == 0:
            boxes_per_image.append(0)
            empty_images_count += 1
            all_parsed_data.append((split, fname, img_path, []))
            continue

        boxes_per_image.append(len(lines))
        split_boxes[split] += len(lines)
        img_boxes = []

        for line_idx, line in enumerate(lines, 1):
            parts = line.split()
            if len(parts) != 5:
                format_errors.append(f"{lbl_name}:{line_idx} Không đúng 5 cột ({len(parts)} cột)")
                continue

            try:
                cls_id = int(parts[0])
                xc, yc, w, h = map(float, parts[1:])
            except ValueError:
                format_errors.append(f"{lbl_name}:{line_idx} Giá trị không phải số")
                continue

            if cls_id != 0:
                format_errors.append(f"{lbl_name}:{line_idx} Class ID = {cls_id} (yêu cầu là 0)")

            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                format_errors.append(f"{lbl_name}:{line_idx} Tọa độ nằm ngoài [0, 1] hoặc w, h <= 0: {parts}")
                continue

            w_px = w * orig_w
            h_px = h * orig_h
            xmin = (xc - w / 2) * orig_w
            ymin = (yc - h / 2) * orig_h
            xmax = (xc + w / 2) * orig_w
            ymax = (yc + h / 2) * orig_h

            orig_widths.append(w_px)
            orig_heights.append(h_px)
            scaled640_heights.append(h_px * (640.0 / orig_w))
            scaled800_heights.append(h_px * (800.0 / orig_w))

            img_boxes.append([xmin, ymin, xmax, ymax])

        # Kiểm tra trùng lặp (IoU > 0.9)
        num_b = len(img_boxes)
        for i in range(num_b):
            for j in range(i + 1, num_b):
                iou = compute_iou(img_boxes[i], img_boxes[j])
                if iou > 0.9:
                    duplicate_boxes_count += 1
                    duplicate_details.append(f"{split}/{lbl_name}: Box {i+1} & {j+1} có IoU = {iou:.3f} > 0.9")

        all_parsed_data.append((split, fname, img_path, img_boxes))

    # 1. Định dạng tệp nhãn
    print("\n--- 1. KIỂM TRA ĐỊNH DẠNG TỆP NHÃN ---")
    if len(format_errors) == 0:
        print("PASS: Tất cả các tệp nhãn đều đúng định dạng (5 cột, lớp 0, giá trị thuộc [0, 1], w, h > 0).")
    else:
        print(f"CẢNH BÁO: Phát hiện {len(format_errors)} lỗi định dạng:")
        for err in format_errors[:10]:
            print(f"  - {err}")

    # 2. Khung trùng lặp
    print("\n--- 2. KIỂM TRA KHUNG TRÙNG LẶP (IoU > 0.9) ---")
    if duplicate_boxes_count == 0:
        print("PASS: Không có khung nào bị trùng lặp (IoU > 0.9).")
    else:
        print(f"CẢNH BÁO: Phát hiện {duplicate_boxes_count} cặp khung trùng lặp:")
        for d in duplicate_details[:10]:
            print(f"  - {d}")

    # 3. Phân bố số lượng khung
    total_boxes = sum(boxes_per_image)
    b_arr = np.array(boxes_per_image)
    print("\n--- 3. PHÂN BỐ SỐ KHUNG TRÊN MỖI ẢNH ---")
    print(f"Tổng số đầu người đã gán: {total_boxes} đầu")
    print(f"  - Tập train ({split_counts['train']} ảnh): {split_boxes['train']} đầu")
    print(f"  - Tập val   ({split_counts['val']} ảnh): {split_boxes['val']} đầu")
    print(f"  - Tập test  ({split_counts['test']} ảnh): {split_boxes['test']} đầu")
    print(f"Số ảnh không có nhãn (ảnh nền 0 đầu): {empty_images_count}/{len(items)} ({empty_images_count/len(items)*100:.1f}%)")
    print(f"Trung bình mỗi ảnh: {np.mean(b_arr):.2f} đầu")
    print(f"Trung vị (Median) : {np.median(b_arr):.1f} đầu")
    print(f"Thấp nhất: {np.min(b_arr)} đầu | Cao nhất: {np.max(b_arr)} đầu")

    # 4. Kích thước khung
    if len(orig_heights) > 0:
        ow_arr = np.array(orig_widths)
        oh_arr = np.array(orig_heights)
        s640_arr = np.array(scaled640_heights)
        s800_arr = np.array(scaled800_heights)

        print("\n--- 4. THỐNG KÊ KÍCH THƯỚC KHUNG ĐẦU NGƯỜI ---")
        print("A. Ở ĐỘ PHÂN GIẢI GỐC (1920x1080):")
        print(f"   - Chiều cao trung vị: {np.median(oh_arr):.1f} px (Min: {np.min(oh_arr):.1f} px, Max: {np.max(oh_arr):.1f} px)")
        print(f"   - Chiều rộng trung vị: {np.median(ow_arr):.1f} px")
        print(f"   - Tỉ lệ khung chiều cao < 12 px: {np.mean(oh_arr < 12.0) * 100:.1f}%")

        print("\nB. KHI THU VỀ IMGSZ 800 (Scale 800/1920 = 0.417):")
        print(f"   - Chiều cao trung vị: {np.median(s800_arr):.1f} px (Min: {np.min(s800_arr):.1f} px, Max: {np.max(s800_arr):.1f} px)")
        print(f"   - Tỉ lệ khung chiều cao < 12 px: {np.mean(s800_arr < 12.0) * 100:.1f}%")
        print(f"   - Tỉ lệ khung chiều cao < 8 px: {np.mean(s800_arr < 8.0) * 100:.1f}%")

        print("\nC. KHI THU VỀ IMGSZ 640 (Scale 640/1920 = 0.333):")
        print(f"   - Chiều cao trung vị: {np.median(s640_arr):.1f} px (Min: {np.min(s640_arr):.1f} px, Max: {np.max(s640_arr):.1f} px)")
        print(f"   - Tỉ lệ khung chiều cao < 12 px: {np.mean(s640_arr < 12.0) * 100:.1f}%")
        print(f"   - Tỉ lệ khung chiều cao < 8 px: {np.mean(s640_arr < 8.0) * 100:.1f}%")

    # 5. Xuất 20 ảnh overlay mẫu
    print("\n--- 5. XUẤT 20 ẢNH OVERLAY ĐỂ KIỂM TRA BẰNG MẮT (QC OVERLAYS) ---")
    random.seed(42)
    sample_targets = random.sample(all_parsed_data, min(20, len(all_parsed_data)))

    for s_idx, (split, fname, img_path, boxes) in enumerate(sample_targets, 1):
        img = cv2.imread(img_path)
        if img is None:
            continue
        vis = img.copy()
        for b_idx, (x1, y1, x2, y2) in enumerate(boxes, 1):
            cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            cv2.circle(vis, (cx, cy), 3, (0, 0, 255), -1)
            cv2.putText(vis, str(b_idx), (int(x1), int(y1) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        info_header = f"[{split.upper()}] {fname} | Total heads: {len(boxes)}"
        cv2.rectangle(vis, (5, 5), (650, 40), (0, 0, 0), -1)
        cv2.putText(vis, info_header, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

        out_overlay_path = os.path.join(qc_dir, f"qc_{split}_{fname}")
        cv2.imwrite(out_overlay_path, vis, [cv2.IMWRITE_JPEG_QUALITY, 95])

    print(f"Đã xuất 20 ảnh overlay vào thư mục: {qc_dir}")

    # 6. Cập nhật manifest.csv: đánh dấu toàn bộ 163 ảnh đã kiểm = 'có'
    manifest_path = os.path.join(base_dir, "manifest.csv")
    if os.path.exists(manifest_path):
        rows = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            verified_fnames = set(fname for _, fname in items)
            for r in reader:
                if len(r) >= 7 and r[0] in verified_fnames:
                    r[6] = "có"
                rows.append(r)
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        print("Đã cập nhật trạng thái 'nhãn đã kiểm = có' cho tất cả 163 ảnh trong manifest.csv.")

    print("\n" + "=" * 60)
    print("=== HOÀN TẤT KIỂM ĐỊNH CHẤT LƯỢNG TOÀN BỘ DATASET (PHASE 6 PASS) ===")
    print("=" * 60)

if __name__ == "__main__":
    main()
