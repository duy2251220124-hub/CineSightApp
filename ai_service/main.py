import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
import cv2
import numpy as np
from database import get_seats, init_db, save_alerts, get_active_alerts, get_all_alerts, resolve_alert, get_tickets_list, get_configs, update_config, get_employees, add_employee, delete_employee
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

    if alert_result["illegal_occupants"]:
        save_alerts(room_id, show_id, "illegal_occupant", alert_result["illegal_occupants"])
    if alert_result["missing_guests"]:
        save_alerts(room_id, show_id, "missing_guest", alert_result["missing_guests"])
    if alert_result.get("over_capacity"):
        save_alerts(room_id, show_id, "over_capacity", [None])

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

@app.get("/api/v1/alerts/history")
def fetch_alerts_history(room_id: str = None, alert_type: str = None, status: str = None):
    alerts = get_all_alerts(room_id, alert_type, status)
    return {"status": "success", "alerts": alerts}

@app.get("/api/v1/rooms")
def fetch_rooms():
    import json
    import glob
    
    configs_dir = os.path.join(os.path.dirname(__file__), "seats_configs")
    calibration_dir = os.path.join(os.path.dirname(__file__), "calibration_images")
    
    rooms = []
    if os.path.exists(configs_dir):
        for config_path in glob.glob(os.path.join(configs_dir, "*.json")):
            room_id = os.path.splitext(os.path.basename(config_path))[0]
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    seats_data = json.load(f)
                total_seats = len(seats_data)
                is_calibrated = os.path.exists(os.path.join(calibration_dir, f"{room_id}.jpg"))
                rooms.append({
                    "room_id": room_id,
                    "total_seats": total_seats,
                    "is_calibrated": is_calibrated,
                    "config_file": f"seats_configs/{room_id}.json"
                })
            except Exception as e:
                print(f"Lỗi đọc config {room_id}: {e}")
                
    return {"status": "success", "rooms": rooms}

@app.get("/api/v1/tickets")
def fetch_tickets(room_id: str, show_id: str):
    tickets = get_tickets_list(room_id, show_id)
    return {"status": "success", "tickets": tickets}

@app.post("/api/v1/resolve_alert/{alert_id}")
def mark_alert_resolved(alert_id: int):
    resolve_alert(alert_id)
    return {"status": "success", "message": f"Đã đánh dấu cảnh báo {alert_id} là đã xử lý."}

class ConfigPayload(BaseModel):
    key: str
    value: str

@app.get("/api/v1/configs")
def fetch_configs():
    return {"status": "success", "configs": get_configs()}

@app.post("/api/v1/configs")
def save_config(payload: ConfigPayload):
    update_config(payload.key, payload.value)
    return {"status": "success"}

class EmployeePayload(BaseModel):
    username: str
    password: str
    name: str
    role: str

@app.get("/api/v1/employees")
def fetch_employees():
    return {"status": "success", "employees": get_employees()}

@app.post("/api/v1/employees")
def create_employee(payload: EmployeePayload):
    try:
        emp_id = add_employee(payload.username, payload.password, payload.name, payload.role)
        return {"status": "success", "id": emp_id}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.delete("/api/v1/employees/{emp_id}")
def remove_employee(emp_id: int):
    delete_employee(emp_id)
    return {"status": "success"}

class LoginPayload(BaseModel):
    username: str
    password: str

@app.post("/api/v1/login")
def login_user(payload: LoginPayload):
    import sqlite3
    from database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role FROM employees WHERE username=? AND password=?", (payload.username, payload.password))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": "success", "user": {"id": row[0], "name": row[1], "role": row[2]}}
    return JSONResponse(status_code=401, content={"error": "Tài khoản hoặc mật khẩu không chính xác"})

print("[INFO] Đang tải mô hình YOLO...")
try:
    import os
    model_path = os.path.join(os.path.dirname(__file__), 'best_v1.pt')
    model = YOLO(model_path)
    print("[OK] Tải mô hình thành công.")
except Exception as e:
    print(f"[LỖI] Không thể tải mô hình YOLO: {e}")
    model = None
