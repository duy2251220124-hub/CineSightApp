import os
import json
import cv2
import numpy as np
from ultralytics import YOLO
from seat_mapper import load_seats_config, process_ai_detections

def main():
    base_dir = r"C:\CineSightApp\ai_service"
    model_path = os.path.join(base_dir, "models", "best_head_v3.pt")
    img_path = os.path.join(base_dir, "calibration_images", "room3_enhanced.jpg")
    artifact_dir = r"C:\Users\Dell KIM ANH\.gemini\antigravity\brain\779a87a8-afe5-44b9-9038-d06517f57dee"

    print("=" * 70)
    print("=== ĐỐI SOÁT KIỂM THỬ MODEL V3 VỚI SƠ ĐỒ PHÒNG CHIẾU SỐ 3 ===")
    print("=" * 70)
    print(f"Model: {model_path}")
    print(f"Frame kiểm thử: {img_path}")

    # Load seats config
    seats_config = load_seats_config("room3")
    total_seats = len(seats_config)
    print(f"Tổng số ghế Phòng chiếu số 3: {total_seats} ghế")

    # Load model
    model = YOLO(model_path)

    # Load image
    img = cv2.imread(img_path)
    h_img, w_img = img.shape[:2]
    scale_x = 1920.0 / w_img if w_img > 0 else 1.0
    scale_y = 1080.0 / h_img if h_img > 0 else 1.0

    print(f"Kích thước ảnh: {w_img}x{h_img} (Hệ số chuẩn hóa scale: x={scale_x:.3f}, y={scale_y:.3f})")

    # Predict with conf=0.35
    results = model.predict(source=img, conf=0.35, imgsz=640, verbose=False)
    
    detected_heads_norm = []
    raw_boxes = []

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0].tolist())
            raw_boxes.append((x1, y1, x2, y2, conf))
            
            cx = ((x1 + x2) / 2) * scale_x
            cy = ((y1 + y2) / 2) * scale_y
            detected_heads_norm.append((cx, cy))

    total_detected = len(detected_heads_norm)
    print(f"\n[✓] Tổng số đầu người phát hiện: {total_detected} (Mục tiêu nhãn thực tế: 58)")

    # Ánh xạ qua logic cốt lõi seat_mapper
    tap_B = process_ai_detections(detected_heads_norm, seats_config)
    print(f"[✓] Số ghế được xác định CÓ NGƯỜI (Tập B): {len(tap_B)} / {total_seats} ghế")
    print(f"    Tỉ lệ lấp đầy rạp: {len(tap_B)/total_seats*100:.1f}%")
    sorted_occ = sorted(list(tap_B))
    print(f"    Một số ghế có người: {sorted_occ[:15]}...")

    # Vẽ trực quan hóa
    annotated = img.copy()

    # 1. Vẽ ghế (chuyển tọa độ 1920x1080 về kích thước ảnh hiện tại)
    for seat_name, polygon in seats_config.items():
        is_occ = (seat_name in tap_B)
        color = (255, 120, 0) if is_occ else (60, 60, 60) # Xanh dương (có người) / Xám (trống)
        thick = 2 if is_occ else 1
        
        # scale về ảnh
        poly_img = np.array([
            [int(p[0] / scale_x), int(p[1] / scale_y)] for p in polygon
        ], dtype=np.int32)

        cv2.polylines(annotated, [poly_img], isClosed=True, color=color, thickness=thick)

        # Chấm tâm và tên ghế nếu có người
        cx = int(sum(p[0] for p in poly_img) / len(poly_img))
        cy = int(sum(p[1] for p in poly_img) / len(poly_img))
        if is_occ:
            cv2.circle(annotated, (cx, cy), 3, (255, 200, 0), -1)

    # 2. Vẽ các đầu người được nhận diện (Hộp xanh lá)
    for (x1, y1, x2, y2, conf) in raw_boxes:
        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        cv2.circle(annotated, (cx, cy), 2, (0, 0, 255), -1)

    # 3. Thanh tiêu đề thông tin
    banner = f"CineSight Model V3 | Rạp 3 (132 ghế) | Heads Detected: {total_detected}/58 | Occupied: {len(tap_B)} seats"
    cv2.rectangle(annotated, (0, 0), (w_img, 36), (15, 20, 30), -1)
    cv2.putText(annotated, banner, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 180), 2)

    # Xuất ra artifact
    out_file = os.path.join(artifact_dir, "VERIFICATION_MODEL_V3_ROOM3.jpg")
    cv2.imwrite(out_file, annotated)
    print(f"\n[+] ĐÃ XUẤT ẢNH ĐỐI SOÁT THÀNH CÔNG VÀO:")
    print(f"    -> {out_file}")

    return total_detected, len(tap_B)

if __name__ == "__main__":
    main()

