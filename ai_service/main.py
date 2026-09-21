from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import cv2
import numpy as np
import json
from seat_mapper import load_seats_config, process_ai_detections, generate_alerts

app = FastAPI(
    title="CineSight AI Vision API",
    description="API kiểm đếm khán giả rạp chiếu phim bằng thị giác máy tính. Hỗ trợ nhiều phòng chiếu.",
    version="2.0.0"
)

print("[INFO] Đang tải mô hình YOLO...")
try:
    model = YOLO('yolov8n.pt')
    print("[OK] Tải model thành công!")
except Exception as e:
    print(f"[ERROR] Không tải được model: {e}")
    model = None

# ======================================================================
# CƠ SỞ DỮ LIỆU TẠM THỜI (Trong thực tế sẽ dùng MySQL/MongoDB/Firebase)
# Dùng để lưu trữ danh sách vé (Tập A) do App Mobile đẩy lên
# ======================================================================
active_tickets_db = {}

@app.get("/")
def health_check():
    return {"status": "CineSight AI Service đang chạy", "version": "2.0.0"}

# ----------------------------------------------------------------------
# ENDPOINT 1: DÀNH RIÊNG CHO APP MOBILE (Nhận Tập A)
# ----------------------------------------------------------------------
@app.post("/api/v1/sync_tickets")
def sync_tickets_from_app(
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1"),
    scanned_tickets: str = Form(..., description="Danh sách vé từ Hive DB. VD: [\"A1\", \"B2\"]")
):
    try:
        tap_A = set(json.loads(scanned_tickets))
        active_tickets_db[room_id] = tap_A
        print(f"[SYNC] Đã nhận {len(tap_A)} vé của phòng {room_id} từ App Mobile.")
        return {"status": "success", "message": f"Đã đồng bộ {len(tap_A)} vé cho phòng {room_id}"}
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "scanned_tickets phải là JSON array."})

# ----------------------------------------------------------------------
# ENDPOINT 2: DÀNH RIÊNG CHO CAMERA RẠP PHIM (Nhận Ảnh -> Tạo Tập B)
# ----------------------------------------------------------------------
@app.post("/api/v1/analyze")
async def analyze_cinema_room(
    image: UploadFile = File(..., description="Ảnh chụp từ camera CCTV phòng chiếu"),
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1")
):
    # Lấy Tập A đã được App đồng bộ từ trước. Nếu chưa có thì coi như rỗng.
    tap_A = active_tickets_db.get(room_id, set())

    # Đọc bản đồ ghế
    seats_config = load_seats_config(room_id)
    if not seats_config:
        return JSONResponse(
            status_code=404,
            content={"error": f"Chưa có bản đồ ghế cho phòng '{room_id}'."}
        )

    # Đọc ảnh camera gửi lên
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Chạy AI
    detected_heads = []
    if model:
        results = model.predict(img, conf=0.4, classes=[0], verbose=False)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detected_heads.append(((x1 + x2) / 2, (y1 + y2) / 2))

    # Ánh xạ Tập B
    tap_B = process_ai_detections(detected_heads, seats_config)

    # Đối chiếu
    alert_result = generate_alerts(tap_A, tap_B, room_id)

    return {
        "status": "success",
        "room_id": room_id,
        "summary": {
            "total_seats": len(seats_config),
            "total_detected_people": len(detected_heads),
            "tap_A_from_app": list(tap_A),
            "tap_B_from_camera": list(tap_B),
        },
        "alerts": alert_result
    }
