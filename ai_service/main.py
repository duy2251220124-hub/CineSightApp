from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import cv2
import numpy as np
import json
from seat_mapper import load_seats_config, process_ai_detections

app = FastAPI(
    title="Cinema AI Vision API",
    description="API xử lý ảnh hồng ngoại rạp chiếu phim, đếm người và đối chiếu vé",
    version="1.0.0"
)

# 1. Khởi tạo mô hình AI
print("[INFO] Đang tải mô hình YOLO...")
try:
    # Tạm thời dùng yolov8n.pt (mô hình chuẩn) để demo.
    # SAU NÀY KHI TRAIN XONG ẢNH HỒNG NGOẠI, bạn sẽ đổi thành: model = YOLO('runs/detect/train/weights/best.pt')
    model = YOLO('yolov8n.pt') 
except Exception as e:
    print("[ERROR] Không thể tải model YOLO:", e)
    model = None

# 2. Tải sơ đồ ghế
seats_config = load_seats_config()

@app.get("/")
def health_check():
    return {"status": "AI Service is running", "seats_configured": len(seats_config)}

@app.post("/api/v1/analyze")
async def analyze_cinema_room(
    image: UploadFile = File(..., description="Ảnh chụp từ camera rạp phim (Hồng ngoại/Ảnh xám)"),
    scanned_tickets: str = Form('[]', description="Danh sách vé đã soát từ App Mobile. Định dạng JSON VD: [\"A1\", \"A2\"]")
):
    """
    Endpoint chính để nhận ảnh từ Camera và danh sách vé từ App Mobile, 
    sau đó trả về kết quả đối chiếu.
    """
    # Parse danh sách vé từ App (Tập A)
    try:
        tap_A = set(json.loads(scanned_tickets))
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "scanned_tickets phải là chuỗi JSON array."})

    # Đọc dữ liệu ảnh từ Request
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    detected_heads = []
    
    # Chạy mô hình AI
    if model:
        # Tạm thời lọc class 0 (Person) của tập COCO.
        # Khi bạn train mô hình Head Detection, class sẽ là 0 (Head)
        results = model.predict(img, conf=0.4, classes=[0], verbose=False) 
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Tính tọa độ tâm của Bounding Box
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x_center = (x1 + x2) / 2
                y_center = (y1 + y2) / 2
                detected_heads.append((x_center, y_center))

    # Ánh xạ tọa độ sang mã ghế (Tập B)
    # Reload lại config để cập nhật nếu có vẽ thêm ghế mới
    current_seats_config = load_seats_config()
    tap_B = process_ai_detections(detected_heads, current_seats_config)

    # Sinh cảnh báo (Nghiệp vụ cốt lõi)
    khach_lau = list(tap_B - tap_A)  # AI thấy có người nhưng app chưa soát vé
    khach_vang = list(tap_A - tap_B) # Đã soát vé nhưng ghế đó trống

    # Trả về kết quả JSON cho Backend / Web Quản lý
    return {
        "status": "success",
        "timestamp": "auto-generated",
        "data": {
            "total_detected": len(detected_heads),
            "tap_B_ai_seats": list(tap_B),
            "tap_A_app_seats": list(tap_A),
            "alerts": {
                "illegal_occupants": khach_lau, 
                "missing_guests": khach_vang,
                "overcrowding_warning": len(detected_heads) > len(current_seats_config)
            }
        }
    }

