import cv2
import os
import json
import numpy as np
from ultralytics import YOLO

video_path = r"C:\Users\Dell KIM ANH\Downloads\ch05_20260902193017\ch05_20260902193017.mp4"
model_path = r"C:\CineSightApp\ai_service\models\best_head_v3.pt"
seats_path = r"C:\CineSightApp\ai_service\seats_configs\seats_config_room3.json"
output_dir = r"C:\CineSightApp\ai_service\video_samples_room3"
artifact_dir = r"C:\Users\Dell KIM ANH\.gemini\antigravity\brain\779a87a8-afe5-44b9-9038-d06517f57dee"

os.makedirs(output_dir, exist_ok=True)

# Load model and seats config
model = YOLO(model_path)
with open(seats_path, "r", encoding="utf-8") as f:
    seats_config = json.load(f)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration_sec = total_frames / fps

# Select 7 key moments: 1m, 5m, 10m, 15m, 20m, 25m, 30m
sample_minutes = [1, 5, 10, 15, 20, 25, 30]
results_summary = []

from seat_mapper import process_ai_detections

for m in sample_minutes:
    sec = m * 60
    if sec >= duration_sec:
        sec = duration_sec - 10
    frame_idx = int(sec * fps)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret:
        print(f"Failed to read frame at {m}m")
        continue

    # Resolution is 1920x1080
    h_f, w_f = frame.shape[:2]
    scale_x = 1920.0 / w_f
    scale_y = 1080.0 / h_f

    # Run YOLO detection with our calibrated optimal params: conf=0.28, iou=0.45
    res = model.predict(frame, conf=0.28, iou=0.45, imgsz=640, verbose=False)[0]

    detected_heads_norm = []
    raw_boxes = []
    for b in res.boxes:
        x1, y1, x2, y2 = b.xyxy[0].tolist()
        conf = float(b.conf[0])
        raw_boxes.append((x1, y1, x2, y2, conf))
        cx = ((x1 + x2) / 2) * scale_x
        cy = ((y1 + y2) / 2) * scale_y
        detected_heads_norm.append((cx, cy))

    tap_B = process_ai_detections(detected_heads_norm, seats_config)
    
    head_count = len(detected_heads_norm)
    occ_count = len(tap_B)

    results_summary.append({
        "minute": m,
        "seconds": int(sec),
        "frame_idx": frame_idx,
        "heads_detected": head_count,
        "seats_occupied": occ_count
    })

    print(f"[{m:02d}:00] ({int(sec):04d}s) -> Heads: {head_count} | Occupied Seats: {occ_count}/132")

    # Draw visualization on this sample
    ann = frame.copy()
    for s_name, poly in seats_config.items():
        is_occ = (s_name in tap_B)
        color = (255, 120, 0) if is_occ else (60, 60, 60)
        thick = 2 if is_occ else 1
        poly_np = np.array(poly, dtype=np.int32)
        cv2.polylines(ann, [poly_np], isClosed=True, color=color, thickness=thick)

    for (x1, y1, x2, y2, conf) in raw_boxes:
        cv2.rectangle(ann, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        cv2.circle(ann, (cx, cy), 3, (0, 0, 255), -1)

    banner = f"Room 3 Timeline [{m:02d}:00] | Heads: {head_count}/58 | Occupied: {occ_count}/132"
    cv2.rectangle(ann, (0, 0), (w_f, 50), (15, 20, 30), -1)
    cv2.putText(ann, banner, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 180), 2)

    # Save to samples directory and artifact
    sample_file = os.path.join(output_dir, f"sample_{m:02d}min.jpg")
    cv2.imwrite(sample_file, ann)

    # Also save raw frame for potential training dataset augmentation
    raw_save = os.path.join(output_dir, f"raw_{m:02d}min.jpg")
    cv2.imwrite(raw_save, frame)

cap.release()

# Save summary json
summary_path = os.path.join(output_dir, "timeline_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(results_summary, f, indent=2)

print("\n=== HOÀN TẤT TRÍCH XUẤT VÀ ĐÁNH GIÁ 30 PHÚT VIDEO ===")
print("Summary:", results_summary)

