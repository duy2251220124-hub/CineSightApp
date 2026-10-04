import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import numpy as np
from database import get_seats, init_db, save_alerts, get_active_alerts
from seat_mapper import load_seats_config, process_ai_detections, generate_alerts

app = FastAPI(
    title="CineSight AI Camera API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/")
def health_check():
    return {"status": "CineSight AI Service đang chạy", "version": "2.0.0"}

@app.post("/api/v1/sync_tickets")
def sync_tickets_from_app(
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1"),
    show_id: str = Form(..., description="Mã suất chiếu. VD: 2026-09-25T19:30"),
    scanned_tickets: str = Form(..., description="Mảng JSON chứa các Object vé hợp lệ (Tập A)"),
):
    import json
    try:
        tickets_list = json.loads(scanned_tickets)
        from database import save_tickets
        from seat_mapper import normalize_seat
        
        # Chuẩn hóa seat_id trước khi lưu
        for t in tickets_list:
            t['seat'] = normalize_seat(t['seat'])
            
        save_tickets(room_id, show_id, tickets_list)
        return {"status": "success", "message": f"Đã lưu {len(tickets_list)} vé cho phòng {room_id}, suất {show_id}"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/v1/analyze")
async def analyze_cinema_room(
    image: UploadFile = File(..., description="Ảnh chụp từ camera CCTV phòng chiếu"),
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1"),
    show_id: str = Form(..., description="Mã suất chiếu. VD: 2026-09-25T19:30")
):
    tap_A = get_seats(room_id, show_id)

    seats_config = load_seats_config(room_id)
    if not seats_config:
        return JSONResponse(
            status_code=404,
            content={"error": f"Chưa có bản đồ ghế cho phòng '{room_id}'."}
        )

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    detected_heads = []
    if model:
        results = model.predict(img, conf=0.4, classes=[0], verbose=False)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detected_heads.append(((x1 + x2) / 2, (y1 + y2) / 2))

    tap_B = process_ai_detections(detected_heads, seats_config)
    alert_result = generate_alerts(tap_A, tap_B, room_id, len(seats_config))

    # LÆ°u cáº£nh bÃ¡o vÃ o Database
    if alert_result["illegal_occupants"]:
        save_alerts(room_id, show_id, "illegal_occupant", alert_result["illegal_occupants"])
    if alert_result["missing_guests"]:
        save_alerts(room_id, show_id, "missing_guest", alert_result["missing_guests"])

    return {
        "status": "success",
        "room_id": room_id,
        "show_id": show_id,
        "summary": {
            "total_seats": len(seats_config),
            "total_detected_people": len(detected_heads),
            "tap_A_from_app": list(tap_A),
            "tap_B_from_camera": list(tap_B),
        },
        "alerts": alert_result
    }


@app.get("/api/v1/alerts")
def fetch_alerts(room_id: str = None):
    alerts = get_active_alerts(room_id)
    return {"status": "success", "alerts": alerts}

print("[INFO] Đang tải mô hình YOLO...")
try:
    import os
    model_path = os.path.join(os.path.dirname(__file__), 'yolov8n.pt')
    model = YOLO(model_path)
    print("[OK] Tải mô hình thành công.")
except Exception as e:
    print(f"[LỖI] Không thể tải mô hình YOLO: {e}")
    model = None
