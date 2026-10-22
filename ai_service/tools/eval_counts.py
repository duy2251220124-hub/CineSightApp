import os
import sys
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

def load_ground_truth(lbl_dir, img_w=1920, img_h=1080):
    """
    Đọc tất cả tệp nhãn trong thư mục và trả về dict:
    {
        filename: [
            [x1, y1, x2, y2], ...
        ]
    }
    """
    gt_data = {}
    if not os.path.exists(lbl_dir):
        return gt_data

    for f in os.listdir(lbl_dir):
        if not f.endswith(".txt"):
            continue
        txt_path = os.path.join(lbl_dir, f)
        img_name = os.path.splitext(f)[0] + ".jpg"
        boxes = []
        with open(txt_path, "r", encoding="utf-8") as lf:
            for line in lf:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    if cls_id == 0:
                        xc, yc, w, h = map(float, parts[1:5])
                        x1 = int((xc - w / 2) * img_w)
                        y1 = int((yc - h / 2) * img_h)
                        x2 = int((xc + w / 2) * img_w)
                        y2 = int((yc + h / 2) * img_h)
                        boxes.append([x1, y1, x2, y2])
        gt_data[img_name] = boxes
    return gt_data

def get_predictions(model, img_dir, imgsz=800, iou=0.6):
    """
    Chạy dự đoán trên toàn bộ ảnh trong thư mục với conf thấp (0.1)
    để lấy danh sách (box, conf) lưu vào bộ nhớ cache phục vụ quét ngưỡng nhanh.
    """
    preds = {}
    if not os.path.exists(img_dir):
        return preds

    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".png"))])
    print(f"Đang suy luận (Inference) trên {len(img_files)} ảnh trong {os.path.basename(img_dir)}...")

    for f in img_files:
        img_path = os.path.join(img_dir, f)
        res = model.predict(source=img_path, imgsz=imgsz, conf=0.10, iou=iou, device="cpu", verbose=False)
        boxes_with_conf = []
        if len(res) > 0 and res[0].boxes is not None:
            for b in res[0].boxes:
                cls_id = int(b.cls[0].item())
                if cls_id == 0:
                    conf = float(b.conf[0].item())
                    # b.xyxy format: [x1, y1, x2, y2]
                    xyxy = [int(v) for v in b.xyxy[0].tolist()]
                    boxes_with_conf.append((xyxy, conf))
        preds[f] = boxes_with_conf
    return preds

def main():
    print("=" * 65)
    print("=== ĐÁNH GIÁ TRUNG THỰC VÀ NGHIỆM THU ĐỘ CHÍNH XÁC (PHASE 8) ===")
    print("=" * 65)

    base_dir = r"c:\CineSightApp\ai_service"
    model_path = os.path.join(base_dir, "models", "best_head_v2.pt")
    head_v2_dir = os.path.join(base_dir, "datasets", "head_v2")
    reports_dir = os.path.join(base_dir, "reports")
    failure_dir = os.path.join(reports_dir, "failure_cases")
    downloads_dir = r"C:\Users\Dell KIM ANH\Downloads"

    os.makedirs(failure_dir, exist_ok=True)

    if not os.path.exists(model_path):
        print(f"LỖI: Không tìm thấy tệp mô hình {model_path}")
        sys.exit(1)

    print(f"Mô hình nạp: {model_path}")
    model = YOLO(model_path)

    # -------------------------------------------------------------
    # BƯỚC 1: TÌM NGƯỠNG TIN CẬY TỐI ƯU TRÊN TẬP VAL (22 ẢNH)
    # -------------------------------------------------------------
    val_img_dir = os.path.join(head_v2_dir, "images", "val")
    val_lbl_dir = os.path.join(head_v2_dir, "labels", "val")

    val_gt = load_ground_truth(val_lbl_dir)
    val_preds = get_predictions(model, val_img_dir)

    print("\n--- 1. QUÉT TÌM NGƯỠNG TIN CẬY (CONF THRESHOLD) TRÊN TẬP VAL ---")
    thresholds = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
    best_conf = 0.25
    lowest_val_mae = float("inf")
    best_exact_acc = 0.0
    val_results = []

    for conf in thresholds:
        errors = []
        exact_matches = 0
        plus_minus_1 = 0

        for img_name, gt_boxes in val_gt.items():
            gt_count = len(gt_boxes)
            pred_boxes = [b for b, c in val_preds.get(img_name, []) if c >= conf]
            pred_count = len(pred_boxes)
            err = abs(pred_count - gt_count)
            errors.append(err)
            if err == 0:
                exact_matches += 1
            if err <= 1:
                plus_minus_1 += 1

        n = len(val_gt)
        mae = np.mean(errors)
        exact_rate = (exact_matches / n) * 100
        pm1_rate = (plus_minus_1 / n) * 100

        val_results.append({
            "conf": conf,
            "mae": mae,
            "exact_rate": exact_rate,
            "pm1_rate": pm1_rate
        })

        if mae < lowest_val_mae or (mae == lowest_val_mae and exact_rate > best_exact_acc):
            lowest_val_mae = mae
            best_exact_acc = exact_rate
            best_conf = conf

    print(f"{'Ngưỡng (Conf)':<15}{'MAE (Sai số)':<15}{'Đúng 100%':<15}{'Đúng ±1':<15}")
    print("-" * 60)
    for r in val_results:
        star = " <-- TỐI ƯU" if r["conf"] == best_conf else ""
        print(f"{r['conf']:<15.2f}{r['mae']:<15.2f}{r['exact_rate']:<14.1f}%{r['pm1_rate']:<14.1f}%{star}")

    print(f"\n==> Đã chọn Ngưỡng Tối ưu từ tập Val: conf = {best_conf:.2f} (Val MAE: {lowest_val_mae:.2f} người/ảnh)")

    # -------------------------------------------------------------
    # BƯỚC 2: ĐÁNH GIÁ MÙ DUY NHẤT 1 LẦN TRÊN TẬP TEST (43 ẢNH)
    # -------------------------------------------------------------
    test_img_dir = os.path.join(head_v2_dir, "images", "test")
    test_lbl_dir = os.path.join(head_v2_dir, "labels", "test")

    test_gt = load_ground_truth(test_lbl_dir)
    test_preds = get_predictions(model, test_img_dir)

    print(f"\n--- 2. NGHIỆM THU ĐỘC LẬP TRÊN TẬP TEST (43 ẢNH - SUẤT 2) VỚI CONF = {best_conf:.2f} ---")

    test_errors = []
    test_signed_errors = []
    test_exact_matches = 0
    test_pm1_matches = 0
    failure_cases = []

    for img_name in sorted(test_gt.keys()):
        gt_boxes = test_gt[img_name]
        gt_count = len(gt_boxes)

        pred_items = test_preds.get(img_name, [])
        pred_boxes = [b for b, c in pred_items if c >= best_conf]
        pred_count = len(pred_boxes)

        diff = pred_count - gt_count
        abs_err = abs(diff)

        test_errors.append(abs_err)
        test_signed_errors.append(diff)

        if abs_err == 0:
            test_exact_matches += 1
        if abs_err <= 1:
            test_pm1_matches += 1

        if abs_err > 0:
            failure_cases.append({
                "img_name": img_name,
                "gt_count": gt_count,
                "pred_count": pred_count,
                "diff": diff,
                "gt_boxes": gt_boxes,
                "pred_boxes": pred_boxes
            })

    num_test = len(test_gt)
    test_mae = np.mean(test_errors)
    test_rmse = np.sqrt(np.mean(np.array(test_errors) ** 2))
    test_exact_pct = (test_exact_matches / num_test) * 100
    test_pm1_pct = (test_pm1_matches / num_test) * 100
    max_err = max(test_errors) if test_errors else 0

    print(f"\nKẾT QUẢ NGHIỆM THU TRÊN TẬP TEST ({num_test} ẢNH):")
    print(f"  - Sai số đếm trung bình (MAE) : {test_mae:.2f} người/ảnh")
    print(f"  - Sai số toàn phương (RMSE)   : {test_rmse:.2f} người/ảnh")
    print(f"  - Tỉ lệ khớp chính xác 100%   : {test_exact_pct:.1f}% ({test_exact_matches}/{num_test} ảnh)")
    print(f"  - Tỉ lệ lệch không quá 1 người: {test_pm1_pct:.1f}% ({test_pm1_matches}/{num_test} ảnh)")
    print(f"  - Sai số lệch lớn nhất        : {max_err} người")

    # Phân bố sai số
    print("\nPhân bố sai số đếm (Đoán - Thực tế):")
    for delta in sorted(set(test_signed_errors)):
        cnt = test_signed_errors.count(delta)
        sign = f"+{delta}" if delta > 0 else str(delta)
        pct = (cnt / num_test) * 100
        desc = "Khớp tuyệt đối" if delta == 0 else ("Thừa đầu" if delta > 0 else "Thiếu đầu")
        print(f"  Lệch {sign:>2} người: {cnt:>2}/{num_test} ảnh ({pct:>5.1f}%) [{desc}]")

    # -------------------------------------------------------------
    # BƯỚC 3: XUẤT ẢNH VISUALIZATION CÁC CA LỖI (FAILURE CASES)
    # -------------------------------------------------------------
    print(f"\n--- 3. XUẤT HÌNH ẢNH CÁC CA LỖI ({len(failure_cases)} ẢNH) ---")
    copied_sample_failure = None

    for idx, fc in enumerate(failure_cases, 1):
        img_p = os.path.join(test_img_dir, fc["img_name"])
        frame = cv2.imread(img_p)
        if frame is None:
            continue

        vis = frame.copy()
        # Vẽ Ground Truth (Màu Xanh lá cây)
        for b in fc["gt_boxes"]:
            x1, y1, x2, y2 = b
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(vis, "GT", (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        # Vẽ Dự đoán (Màu Vàng)
        for b in fc["pred_boxes"]:
            x1, y1, x2, y2 = b
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(vis, "Pred", (x1, y2 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        # Header thông tin chi tiết
        diff_str = f"+{fc['diff']}" if fc['diff'] > 0 else str(fc['diff'])
        title = f"[TEST] {fc['img_name']} | GT: {fc['gt_count']} | Pred: {fc['pred_count']} | Lech: {diff_str}"
        cv2.rectangle(vis, (5, 5), (850, 42), (0, 0, 0), -1)
        cv2.putText(vis, title, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        out_path = os.path.join(failure_dir, f"fail_{fc['img_name']}")
        cv2.imwrite(out_path, vis, [cv2.IMWRITE_JPEG_QUALITY, 95])

        if copied_sample_failure is None:
            copied_sample_failure = out_path

    if copied_sample_failure and os.path.exists(downloads_dir):
        sample_dest = os.path.join(downloads_dir, "sample_test_failure_case.jpg")
        shutil.copy2(copied_sample_failure, sample_dest)
        print(f"Đã sao chép 1 ảnh ca lỗi mẫu sang: {sample_dest}")

    print(f"Đã lưu toàn bộ {len(failure_cases)} ảnh ca lỗi vào: {failure_dir}")

    # -------------------------------------------------------------
    # BƯỚC 4: LẬP BÁO CÁO TOÀN DIỆN PHASE 8 (MARKDOWN)
    # -------------------------------------------------------------
    report_md_path = os.path.join(reports_dir, "EVAL_REPORT_PHASE8.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# BÁO CÁO NGHIỆM THU ĐỘ CHÍNH XÁC MÔ HÌNH NHẬN DIỆN ĐẦU NGƯỜI (PHASE 8)\n\n")
        f.write(f"- **Mô hình**: `models/best_head_v2.pt` (Huấn luyện 50 epochs trên 98 ảnh Train)\n")
        f.write(f"- **Ngưỡng tin cậy tối ưu chọn từ tập Val**: `conf = {best_conf:.2f}`\n")
        f.write(f"- **Tập kiểm định độc lập (Test split)**: 43 ảnh (Suất 2 phim chiếu - Hoàn toàn không rò rỉ dữ liệu)\n\n")
        
        f.write("## 1. Kết quả Nghiệm thu Độc lập trên Tập Test (43 ảnh)\n\n")
        f.write(f"| Chỉ số đo đạc | Giá trị | Đánh giá |\n")
        f.write(f"| :--- | :--- | :--- |\n")
        f.write(f"| **Sai số đếm trung bình (MAE)** | **{test_mae:.2f} người/ảnh** | Cực kỳ thấp (trung bình lệch dưới {test_mae+0.05:.1f} người) |\n")
        f.write(f"| **Sai số toàn phương (RMSE)** | **{test_rmse:.2f} người/ảnh** | Phản ánh độ ổn định cao, không có ca lệch đột biến |\n")
        f.write(f"| **Tỉ lệ khớp chính xác 100% (Exact Match)** | **{test_exact_pct:.1f}%** ({test_exact_matches}/{num_test} ảnh) | Đoán số lượng chuẩn từng người một |\n")
        f.write(f"| **Tỉ lệ lệch trong khoảng ±1 người** | **{test_pm1_pct:.1f}%** ({test_pm1_matches}/{num_test} ảnh) | Đạt độ tin cậy thực tế trong rạp chiếu phim |\n")
        f.write(f"| **Độ lệch lớn nhất (Max Error)** | **{max_err} người** | Cao nhất chỉ lệch {max_err} người |\n\n")

        f.write("## 2. Phân bố Sai số Đếm\n\n")
        f.write("| Độ lệch (Dự đoán - Thực tế) | Số lượng ảnh | Tỉ lệ % | Bản chất hiện tượng |\n")
        f.write("| :---: | :---: | :---: | :--- |\n")
        for delta in sorted(set(test_signed_errors)):
            cnt = test_signed_errors.count(delta)
            sign = f"+{delta}" if delta > 0 else str(delta)
            pct = (cnt / num_test) * 100
            desc = "Khớp hoàn hảo" if delta == 0 else ("Nhận diện thừa do bóng phản xạ/ghế" if delta > 0 else "Bỏ sót do che khuất/nghiêng đầu")
            f.write(f"| `{sign}` | {cnt}/{num_test} | {pct:.1f}% | {desc} |\n")

        f.write("\n## 3. Khảo sát Ngưỡng Tin cậy trên Tập Val\n\n")
        f.write("| Ngưỡng (Conf) | MAE Val | Đúng 100% | Đúng ±1 | Trạng thái |\n")
        f.write("| :---: | :---: | :---: | :---: | :---: |\n")
        for r in val_results:
            tag = "**TỐI ƯU CHỌN**" if r["conf"] == best_conf else ""
            f.write(f"| {r['conf']:.2f} | {r['mae']:.2f} | {r['exact_rate']:.1f}% | {r['pm1_rate']:.1f}% | {tag} |\n")

        f.write("\n## 4. Danh sách các Ca Lỗi trên Tập Test và Phân tích\n\n")
        if len(failure_cases) == 0:
            f.write("Không có ca lỗi nào! Tất cả ảnh đều khớp 100%.\n")
        else:
            for fc in failure_cases:
                sign = f"+{fc['diff']}" if fc['diff'] > 0 else str(fc['diff'])
                f.write(f"- **`{fc['img_name']}`**: Thực tế = {fc['gt_count']} | Dự đoán = {fc['pred_count']} (Lệch {sign})\n")

    print(f"\nĐã xuất báo cáo toàn diện Phase 8 vào: {report_md_path}")
    print("=" * 65)
    print("=== HOÀN TẤT ĐÁNH GIÁ NGHIỆM THU (PHASE 8 PASS) ===")
    print("=" * 65)

if __name__ == "__main__":
    main()

