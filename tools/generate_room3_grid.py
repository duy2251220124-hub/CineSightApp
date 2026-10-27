import cv2
import numpy as np
import json
import os
from ultralytics import YOLO

# 1. Tải ảnh camera gốc Rạp 3 (1024 x 575)
img_path = r'C:\CineSightApp\ai_service\calibration_images\room3.jpg'
img = cv2.imread(img_path)
orig_h, orig_w = img.shape[:2]

# Hệ số quy đổi sang canvas 1920x1080 (chuẩn của CineSight)
SCALE_X = 1920.0 / orig_w
SCALE_Y = 1080.0 / orig_h

# 2. Sử dụng YOLO để lấy tâm các đầu người đang ngồi thực tế
model = YOLO(r'C:\CineSightApp\ai_service\models\best_head_v2.pt')
results = model.predict(img, conf=0.25, imgsz=800, verbose=False)

detections = []
for box in results[0].boxes:
    xyxy = box.xyxy[0].cpu().numpy()
    cx = float((xyxy[0] + xyxy[2]) / 2)
    cy = float((xyxy[1] + xyxy[3]) / 2)
    detections.append((cx, cy))

print(f"Tổng số điểm người phát hiện: {len(detections)}")

# 3. Định nghĩa hình học 10 hàng ghế (từ trên xuống: J, I, H, G, F, E, D, C, B, A)
# Đo đạc trực tiếp trên tọa độ 1024x575:
# Nhìn từ camera:
# Hàng A (dưới cùng, gần camera nhất): y ~ 515 - 555, x từ 275 đến 740, 10 ghế
# Hàng B: y ~ 455 - 490, x từ 230 đến 785, 13 ghế
# Hàng C: y ~ 400 - 435, x từ 245 đến 770, 13 ghế
# Hàng D: y ~ 350 - 380, x từ 270 đến 745, 13 ghế
# Hàng E: y ~ 305 - 335, x từ 288 đến 725, 13 ghế
# Hàng F: y ~ 265 - 295, x từ 305 đến 710, 13 ghế
# Hàng G: y ~ 228 - 255, x từ 320 đến 695, 13 ghế
# Hàng H: y ~ 194 - 218, x từ 332 đến 682, 13 ghế
# Hàng I: y ~ 162 - 184, x từ 342 đến 670, 13 ghế
# Hàng J (sát tường sau): y ~ 124 - 146, x từ 335 đến 745, 18 ghế

row_definitions = [
    # (row_letter, seat_count, y_top, y_bot, x_left, x_right)
    ('A', 10, 500, 560, 275, 740),
    ('B', 13, 442, 495, 235, 785),
    ('C', 13, 390, 438, 252, 768),
    ('D', 13, 342, 386, 272, 746),
    ('E', 13, 298, 338, 290, 728),
    ('F', 13, 258, 294, 306, 712),
    ('G', 13, 222, 254, 320, 696),
    ('H', 13, 188, 218, 334, 682),
    ('I', 13, 156, 184, 344, 670),
    ('J', 18, 120, 148, 335, 745),
]

seats_1920 = {}
preview_img = img.copy()

total_generated = 0

for row_letter, count, y_top, y_bot, x_left, x_right in row_definitions:
    # Bề rộng mỗi ghế
    row_w = x_right - x_left
    seat_w = row_w / count
    
    # Khoảng đệm giữa các ghế
    pad_x = seat_w * 0.08
    
    for idx in range(count):
        seat_num = idx + 1
        seat_name = f"{row_letter}{seat_num:02d}"
        
        # Tọa độ 4 góc trên ảnh 1024x575
        sx1 = x_left + idx * seat_w + pad_x
        sx2 = x_left + (idx + 1) * seat_w - pad_x
        sy1 = y_top
        sy2 = y_bot
        
        # Quy đổi sang tọa độ chuẩn 1920x1080
        p1 = [round(sx1 * SCALE_X, 1), round(sy1 * SCALE_Y, 1)]
        p2 = [round(sx2 * SCALE_X, 1), round(sy1 * SCALE_Y, 1)]
        p3 = [round(sx2 * SCALE_X, 1), round(sy2 * SCALE_Y, 1)]
        p4 = [round(sx1 * SCALE_X, 1), round(sy2 * SCALE_Y, 1)]
        p5 = [round(sx1 * SCALE_X, 1), round(sy1 * SCALE_Y, 1)] # Khép kín đa giác
        
        seats_1920[seat_name] = [p1, p2, p3, p4, p5]
        total_generated += 1
        
        # Vẽ lên ảnh xem trước (preview 1024x575)
        pts = np.array([[int(sx1), int(sy1)], [int(sx2), int(sy1)], 
                        [int(sx2), int(sy2)], [int(sx1), int(sy2)]], np.int32)
        cv2.polylines(preview_img, [pts], True, (0, 255, 0), 1, cv2.LINE_AA)
        
        # Ghi nhãn ghế
        cx = int((sx1 + sx2) / 2)
        cy = int((sy1 + sy2) / 2)
        
        font_scale = 0.28 if row_letter in ['H', 'I', 'J'] else (0.33 if row_letter in ['D', 'E', 'F', 'G'] else 0.38)
        # Chỉ vẽ tên hàng hoặc số ghế để tránh rối mắt
        if count <= 13:
            label = f"{row_letter}{seat_num}"
        else:
            label = f"{seat_num}"
        cv2.putText(preview_img, label, (cx - 7, cy + 3), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)

print(f"Đã sinh hoàn chỉnh {total_generated} ghế cho Phòng 3!")

# Lưu file JSON cấu hình
out_json = r'C:\CineSightApp\ai_service\seats_configs\seats_config_room3.json'
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(seats_1920, f, indent=2, ensure_ascii=False)
print(f"Đã lưu file: {out_json}")

# Lưu ảnh xem trước để user duyệt
out_annotated = r'C:\CineSightApp\ai_service\calibration_images\room3_annotated.jpg'
cv2.imwrite(out_annotated, preview_img)

out_artifact = r'C:\Users\Dell KIM ANH\.gemini\antigravity\brain\779a87a8-afe5-44b9-9038-d06517f57dee\ROOM3_AUTO_GRID_ANNOTATED.jpg'
cv2.imwrite(out_artifact, preview_img)
print(f"Đã lưu ảnh trực quan: {out_artifact}")

