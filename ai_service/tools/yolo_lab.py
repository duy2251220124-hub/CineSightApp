"""
CineSight YOLO Study Lab (tools/yolo_lab.py)
Chạy 5 thí nghiệm CHỈ SUY LUẬN (read-only inference) trên tập val để minh họa giới hạn của YOLO.
Mọi đầu ra tạm (nếu có) được ghi vào reports/yolo_study_tmp/ và tự động xóa sau khi chạy xong.
Không sửa mô hình, không sửa dữ liệu, không đổi cài đặt dự án.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from ultralytics.utils.metrics import bbox_iou

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "best_head_v2.pt"
VAL_IMG_DIR = BASE_DIR / "datasets" / "head_v2" / "images" / "val"
VAL_LBL_DIR = BASE_DIR / "datasets" / "head_v2" / "labels" / "val"
TMP_DIR = BASE_DIR / "reports" / "yolo_study_tmp"
SEATS_JSON = BASE_DIR / "seats_configs" / "seats_config_room1.json"


def count_gt_boxes(lbl_path: Path) -> int:
    if not lbl_path.exists():
        return 0
    with open(lbl_path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def load_val_samples() -> list[tuple[Path, Path, int]]:
    imgs = sorted(VAL_IMG_DIR.glob("*.jpg"))
    samples = []
    for img_p in imgs:
        lbl_p = VAL_LBL_DIR / f"{img_p.stem}.txt"
        samples.append((img_p, lbl_p, count_gt_boxes(lbl_p)))
    return samples


def exp_a_conf_sweep(model: YOLO, samples: list[tuple[Path, Path, int]]) -> None:
    print("=" * 72)
    print("THÍ NGHIỆM A: QUÉT NGƯỠNG CONF (0.15 / 0.25 / 0.40 / 0.60) TRÊN 10 KHUNG VAL")
    print("=" * 72)
    confs = [0.15, 0.25, 0.40, 0.60]
    sub_samples = samples[:10]
    header = f"{'Khung hình (val)':<30} | {'Nhãn thật':>9} | " + " | ".join(f"conf={c:<4}" for c in confs)
    print(header)
    print("-" * len(header))

    totals_pred = {c: 0 for c in confs}
    abs_err = {c: [] for c in confs}
    signed_err = {c: [] for c in confs}
    total_gt = 0

    for img_p, _, gt_count in sub_samples:
        total_gt += gt_count
        # Chạy 1 lần ở conf=0.05, iou=0.70, imgsz=640 rồi lọc theo ngưỡng conf
        res = model.predict(str(img_p), conf=0.05, iou=0.70, imgsz=640, verbose=False)[0]
        box_confs = res.boxes.conf.cpu().numpy() if len(res.boxes) else np.array([])
        row_counts = []
        for c in confs:
            cnt = int((box_confs >= c).sum())
            totals_pred[c] += cnt
            abs_err[c].append(abs(cnt - gt_count))
            signed_err[c].append(cnt - gt_count)
            row_counts.append(f"{cnt:>9}")
        print(f"{img_p.name:<30} | {gt_count:>9} | " + " | ".join(row_counts))

    print("-" * len(header))
    print(f"{'TỔNG SỐ ĐẦU ĐẾM ĐƯỢC':<30} | {total_gt:>9} | " + " | ".join(f"{totals_pred[c]:>9}" for c in confs))
    print(f"{'MAE (Sai số tuyệt đối TB)':<30} | {'0.00':>9} | " + " | ".join(f"{np.mean(abs_err[c]):>9.2f}" for c in confs))
    print(f"{'Bias (Sai số có dấu TB)':<30} | {'+0.00':>9} | " + " | ".join(f"{np.mean(signed_err[c]):>+9.2f}" for c in confs))
    print()


def exp_b_imgsz_sweep(model: YOLO, samples: list[tuple[Path, Path, int]]) -> None:
    print("=" * 72)
    print("THÍ NGHIỆM B: QUÉT IMGSZ SUY LUẬN (320 / 480 / 640 / 800 / 960) & ĐO TỐC ĐỘ CPU")
    print("=" * 72)
    sizes = [320, 480, 640, 800, 960]
    sub_samples = samples[:10]
    total_gt = sum(x[2] for x in sub_samples)

    # Warmup 1 lần trên ảnh đầu tiên
    first_img = str(sub_samples[0][0])
    _ = model.predict(first_img, conf=0.25, iou=0.70, imgsz=640, verbose=False)

    print(f"{'imgsz':>6} | {'Kích thước sau LetterBox':<24} | {'Tổng nhãn':>9} | {'Tổng đếm':>8} | {'MAE (10 ảnh)':>12} | {'TB 10 lần/ảnh (ms)':>18}")
    print("-" * 92)
    for sz in sizes:
        # 1. Đếm trên 10 ảnh val
        preds = []
        errs = []
        for img_p, _, gt_count in sub_samples:
            r = model.predict(str(img_p), conf=0.25, iou=0.70, imgsz=sz, verbose=False)[0]
            c = len(r.boxes)
            preds.append(c)
            errs.append(abs(c - gt_count))
            lb_shape = r.boxes.orig_shape

        # 2. Đo thời gian suy luận 10 lần (bỏ lần chạy đầu warmup cho mỗi imgsz)
        _ = model.predict(first_img, conf=0.25, iou=0.70, imgsz=sz, verbose=False)
        times_ms = []
        for _ in range(10):
            t0 = time.perf_counter()
            r0 = model.predict(first_img, conf=0.25, iou=0.70, imgsz=sz, verbose=False)[0]
            times_ms.append((time.perf_counter() - t0) * 1000.0)

        # Tính kích thước LetterBox thực tế của predictor (auto=True, stride=32)
        gain = min(sz / 1080.0, sz / 1920.0)
        unpad_w, unpad_h = round(1920 * gain), round(1080 * gain)
        pad_h = int(np.mod(sz - unpad_h, 32))
        lb_h = unpad_h + pad_h
        print(
            f"{sz:>6} | {f'{unpad_w}x{unpad_h} -> {unpad_w}x{lb_h}':<24} | "
            f"{total_gt:>9} | {sum(preds):>8} | {np.mean(errs):>12.2f} | "
            f"{np.mean(times_ms):>11.1f} ± {np.std(times_ms):>4.1f}"
        )
    print()


def exp_c_degradation(model: YOLO, samples: list[tuple[Path, Path, int]]) -> None:
    print("=" * 72)
    print("THÍ NGHIỆM C: LÀM SUY GIẢM CHẤT LƯỢNG ẢNH (MỜ, GIẢM SÁNG, GIẢM ĐỘ PHÂN GIẢI 50%)")
    print("=" * 72)
    # Chọn khung đông nhất trong tập val
    crowded_img_p, _, crowded_gt = max(samples, key=lambda x: x[2])
    orig = cv2.imread(str(crowded_img_p))
    h, w = orig.shape[:2]

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    variants = {
        "1. Ảnh gốc (1920x1080)": orig,
        "2. Làm mờ Gaussian (k=15x15)": cv2.GaussianBlur(orig, (15, 15), 5.0),
        "3. Giảm sáng 60% (x0.4)": np.clip(orig.astype(np.float32) * 0.4, 0, 255).astype(np.uint8),
        "4. Giảm sáng 80% (x0.2)": np.clip(orig.astype(np.float32) * 0.2, 0, 255).astype(np.uint8),
        "5. Giảm độ phân giải 50% (960x540)": cv2.resize(orig, (w // 2, h // 2), interpolation=cv2.INTER_AREA),
        "6. Giảm 25% rồi phóng lại (480x270->1920x1080)": cv2.resize(
            cv2.resize(orig, (w // 4, h // 4), interpolation=cv2.INTER_AREA), (w, h), interpolation=cv2.INTER_LINEAR
        ),
    }

    print(f"Khung hình kiểm thử: {crowded_img_p.name} (Số đầu nhãn thật = {crowded_gt})")
    print(f"{'Biến thể suy giảm ảnh':<46} | {'Số đầu (conf>=0.25)':>19} | {'Conf TB':>8} | {'Conf Max':>8}")
    print("-" * 90)
    for name, img_arr in variants.items():
        r = model.predict(img_arr, conf=0.25, iou=0.70, imgsz=640, verbose=False)[0]
        confs = r.boxes.conf.cpu().numpy() if len(r.boxes) else np.array([])
        mean_c = f"{confs.mean():.3f}" if len(confs) else "0.000"
        max_c = f"{confs.max():.3f}" if len(confs) else "0.000"
        print(f"{name:<46} | {len(confs):>19} | {mean_c:>8} | {max_c:>8}")
    print()


def exp_d_nms_iou(model: YOLO, samples: list[tuple[Path, Path, int]]) -> None:
    print("=" * 72)
    print("THÍ NGHIỆM D: QUÉT IOU NMS (0.40 / 0.50 / 0.60 / 0.70 / 0.85) TRÊN KHUNG ĐÔNG NHẤT")
    print("=" * 72)
    crowded_img_p, _, crowded_gt = max(samples, key=lambda x: x[2])
    ious = [0.40, 0.50, 0.60, 0.70, 0.85]
    print(f"Khung đông nhất tập val: {crowded_img_p.name} (Nhãn thật = {crowded_gt} đầu)")

    results_by_iou = {}
    for iou_thr in ious:
        r = model.predict(str(crowded_img_p), conf=0.25, iou=iou_thr, imgsz=640, verbose=False)[0]
        boxes = r.boxes.xyxy.cpu()
        confs = r.boxes.conf.cpu()
        results_by_iou[iou_thr] = (boxes, confs)
        print(f"  - iou={iou_thr:.2f}: giữ lại {len(boxes)} khung dự đoán")

    # Phân tích cặp khung chồng lấp cao nhất ở iou=0.85 (hoặc 0.70) bị loại khi hạ iou
    boxes_hi, confs_hi = results_by_iou[0.85]
    n = len(boxes_hi)
    if n >= 2:
        print("\nCác cặp khung dự đoán có IoU > 0.0 trên khung này (ở iou=0.85):")
        found_overlap = False
        for i in range(n):
            for j in range(i + 1, n):
                ov = float(bbox_iou(boxes_hi[i], boxes_hi[j], xywh=False, CIoU=False).item())
                if ov > 0.01:
                    found_overlap = True
                    b1 = [round(float(x), 1) for x in boxes_hi[i].tolist()]
                    b2 = [round(float(x), 1) for x in boxes_hi[j].tolist()]
                    print(
                        f"  + Cặp ({i}, {j}): IoU = {ov:.4f} | "
                        f"Box {i} {b1} (conf={float(confs_hi[i]):.3f}) <-> "
                        f"Box {j} {b2} (conf={float(confs_hi[j]):.3f})"
                    )
        if not found_overlap:
            print("  + Ở conf>=0.25 trên khung này, các khung giữ lại cách rời nhau (IoU <= 0.01).")

    # Quét toàn bộ 22 ảnh val để tìm các khung có sự thay đổi giữa iou=0.50, 0.60, 0.70
    print("\nQuét toàn bộ 22 ảnh val (conf=0.25, imgsz=640) để tìm các cặp khung bị NMS gộp khi đổi iou (0.50 / 0.60 / 0.70):")
    for img_p, _, gt_c in samples:
        r70 = model.predict(str(img_p), conf=0.25, iou=0.70, imgsz=640, verbose=False)[0]
        r60 = model.predict(str(img_p), conf=0.25, iou=0.60, imgsz=640, verbose=False)[0]
        r50 = model.predict(str(img_p), conf=0.25, iou=0.50, imgsz=640, verbose=False)[0]
        b70, c70 = r70.boxes.xyxy.cpu(), r70.boxes.conf.cpu()
        if len(b70) != len(r50.boxes) or len(b70) != len(r60.boxes):
            print(f"  * {img_p.name} (GT={gt_c}): iou=0.70 -> {len(b70)} đầu | iou=0.60 -> {len(r60.boxes)} đầu | iou=0.50 -> {len(r50.boxes)} đầu")
            for i in range(len(b70)):
                for j in range(i + 1, len(b70)):
                    ov = float(bbox_iou(b70[i], b70[j], xywh=False, CIoU=False).item())
                    if ov >= 0.45:
                        print(
                            f"      Cặp bị gộp: Box#{i} {[round(float(x),1) for x in b70[i]]} (conf={float(c70[i]):.3f}) "
                            f"và Box#{j} {[round(float(x),1) for x in b70[j]]} (conf={float(c70[j]):.3f}) có IoU={ov:.4f}"
                        )
    print()


def exp_e_center_shift(model: YOLO, samples: list[tuple[Path, Path, int]]) -> None:
    print("=" * 72)
    print("THÍ NGHIỆM E: ĐỘ NHẠY DỊCH TÂM KHUNG (±3 px, ±6 px, ±10 px) KHI ÁNH XẠ GHẾ")
    print("=" * 72)
    # Thu thập toàn bộ tâm khung dự đoán (cx, cy) và (cx, y2) trên 22 ảnh val
    all_boxes = []
    for img_p, _, _ in samples:
        r = model.predict(str(img_p), conf=0.25, iou=0.70, imgsz=640, verbose=False)[0]
        for box in r.boxes.xyxy.cpu().numpy():
            all_boxes.append(box)  # [x1, y1, x2, y2]

    total_preds = len(all_boxes)
    print(f"Tổng số khung dự đoán trên 22 ảnh val (conf=0.25, iou=0.70): {total_preds} khung")

    # 1. Mô phỏng trên SƠ ĐỒ LƯỚI GIẢ ĐỊNH ĐỀU (ô ghế kích thước 40x30 px - tương đương vùng ghế ở hàng xa)
    print("\n1) MÔ PHỎNG TRÊN SƠ ĐỒ LƯỚI GHẾ GIẢ ĐỊNH ĐỀU (Mỗi ô ghế rộng 40 px, cao 30 px):")
    rng = np.random.default_rng(42)
    shifts = [3, 6, 10]
    trials = 20  # 20 lần lấy mẫu ngẫu nhiên mỗi khung
    for n_px in shifts:
        changed = 0
        total_trials = total_preds * trials
        for x1, y1, x2, y2 in all_boxes:
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            orig_cell = (int(cx // 40), int(cy // 30))
            for _ in range(trials):
                dx = rng.choice([-n_px, n_px])
                dy = rng.choice([-n_px, n_px])
                new_cell = (int((cx + dx) // 40), int((cy + dy) // 30))
                if new_cell != orig_cell:
                    changed += 1
        pct = changed * 100.0 / total_trials if total_trials else 0.0
        print(f"  - Dịch tâm ±{n_px:>2} px: {changed}/{total_trials} lượt ({pct:.2f}%) bị nhảy sang ô ghế bên cạnh")

    # 2. Kiểm tra trên BẢN ĐỒ ĐA GIÁC GHẾ THẬT (seats_configs/seats_config_room1.json)
    if SEATS_JSON.exists():
        with open(SEATS_JSON, encoding="utf-8") as f:
            raw_seats = json.load(f)
        polys = {
            sid: np.array(poly, dtype=np.int32)
            for sid, poly in raw_seats.items()
            if isinstance(poly, list)
        }

        def find_seat(pt_x: float, pt_y: float, use_mapper_offset: bool = False) -> str | None:
            y_candidates = (pt_y + 10.0, pt_y + 18.0, pt_y) if use_mapper_offset else (pt_y,)
            for cy_test in y_candidates:
                for sid, poly in polys.items():
                    if cv2.pointPolygonTest(poly, (float(pt_x), float(cy_test)), False) >= 0:
                        return sid
            return None

        print(f"\n2) KIỂM TRA TRÊN BẢN ĐỒ ĐA GIÁC THẬT (seats_configs/seats_config_room1.json, {len(polys)} ghế):")
        for mode_label, use_off in [
            ("Tâm khung thuần (cx, cy)", False),
            ("Bù góc nghiêng camera (cx, cy+10/+18/cy - như seat_mapper.py:62)", True),
        ]:
            print(f"  * Quy tắc điểm neo: {mode_label}")
            for n_px in shifts:
                changed_real = 0
                total_t = total_preds * 4  # 4 hướng (-N,-N), (-N,+N), (+N,-N), (+N,+N)
                for x1, y1, x2, y2 in all_boxes:
                    px, py = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    s0 = find_seat(px, py, use_off)
                    for dx in (-n_px, n_px):
                        for dy in (-n_px, n_px):
                            s1 = find_seat(px + dx, py + dy, use_off)
                            if s1 != s0:
                                changed_real += 1
                pct_r = changed_real * 100.0 / total_t if total_t else 0.0
                print(f"    - Dịch ±{n_px:>2} px (4 góc): {changed_real}/{total_t} lượt ({pct_r:.2f}%) bị đổi trạng thái/mã ghế")
    print()


def cleanup_tmp() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    print(f"[CLEANUP] Đã xóa thư mục tạm: {TMP_DIR} (exists={TMP_DIR.exists()})")


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        model = YOLO(str(MODEL_PATH))
        samples = load_val_samples()
        exp_a_conf_sweep(model, samples)
        exp_b_imgsz_sweep(model, samples)
        exp_c_degradation(model, samples)
        exp_d_nms_iou(model, samples)
        exp_e_center_shift(model, samples)
    finally:
        cleanup_tmp()


if __name__ == "__main__":
    main()
