import json
import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
import cv2
import numpy as np
from database import get_seats, init_db, save_alerts, get_active_alerts, get_all_alerts, resolve_alert, get_tickets_list, get_configs, update_config, get_employees, add_employee, update_employee, delete_employee, create_incident, list_incidents, get_incident, resolve_incident, get_employee, get_showtimes, save_showtime, seed_default_showtimes
from seat_mapper import load_seats_config, process_ai_detections, generate_alerts
from movies_repo import init_movies_tables, get_all_movies, get_catalog_showtimes




app = FastAPI(
    title="CineSight AI Camera API",
    version="2.0.0"
)

SHIFTS = [
    {"code": "ca_sang", "label": "Ca sáng", "start": "08:00", "end": "16:00"},
    {"code": "ca_toi", "label": "Ca tối", "start": "16:00", "end": "24:00"}
]

INCIDENT_CATEGORIES = [
    {"code": "seat_damage", "label": "Ghế hỏng"},
    {"code": "equipment", "label": "Lỗi thiết bị (máy chiếu, âm thanh...)"},
    {"code": "facility", "label": "Vệ sinh/Cơ sở vật chất"},
    {"code": "other", "label": "Khác"}
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
init_movies_tables()
seed_default_showtimes()

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
        results = model.predict(img, conf=MODEL_CONF, imgsz=MODEL_IMGSZ, classes=[0], verbose=False)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detected_heads.append(((x1 + x2) / 2, (y1 + y2) / 2))

    tap_B = process_ai_detections(detected_heads, seats_config)

    configs = get_configs()
    try:
        threshold = int(configs.get("capacity_threshold", 0))
    except (ValueError, TypeError):
        threshold = 0

    alert_result = generate_alerts(
        tap_A, 
        tap_B, 
        room_id, 
        len(seats_config),
        total_detected_people=len(detected_heads),
        capacity_threshold=threshold
    )

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
        for config_path in sorted(glob.glob(os.path.join(configs_dir, "*.json"))):
            raw_name = os.path.splitext(os.path.basename(config_path))[0]
            room_id = raw_name.replace("seats_config_", "")
            room_num = room_id.replace("room", "")
            room_name = f"Phòng chiếu {room_num}" if room_num.isdigit() else room_id
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    seats_data = json.load(f)
                total_seats = len(seats_data)
                is_calibrated = os.path.exists(os.path.join(calibration_dir, f"{room_id}.jpg"))
                rooms.append({
                    "room_id": room_id,
                    "name": room_name,
                    "total_seats": total_seats,
                    "rows": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                    "row_counts": {"A": 8, "B": 11, "C": 11, "D": 11, "E": 11, "F": 11, "G": 11, "H": 11, "I": 11, "J": 11, "K": 13, "L": 16},
                    "is_calibrated": is_calibrated,
                    "config_file": f"seats_configs/{raw_name}.json"
                })
            except Exception as e:
                print(f"Lỗi đọc config {room_id}: {e}")
                
    return {"status": "success", "rooms": rooms}
 
@app.get("/api/v1/calibration_image/{room_id}")
def get_calibration_image(room_id: str):
    clean_room_id = room_id.replace("seats_config_", "")
    calib_dir = os.path.join(os.path.dirname(__file__), "calibration_images")
    annotated_path = os.path.join(calib_dir, f"{clean_room_id}_annotated.jpg")
    if os.path.exists(annotated_path):
        return FileResponse(annotated_path, media_type="image/jpeg")
    raw_path = os.path.join(calib_dir, f"{clean_room_id}.jpg")
    if os.path.exists(raw_path):
        return FileResponse(raw_path, media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"error": "Calibration image not found"})

@app.get("/api/v1/rooms/{room_id}/seats")
def fetch_room_seats(room_id: str):
    clean_room_id = room_id.replace("seats_config_", "")
    seats_config = load_seats_config(clean_room_id)
    if not seats_config:
        return JSONResponse(status_code=404, content={"error": f"Không tìm thấy sơ đồ ghế cho phòng '{clean_room_id}'"})
    room_num = clean_room_id.replace("room", "")
    room_name = f"Phòng chiếu {room_num}" if room_num.isdigit() else clean_room_id
    return {
        "status": "success",
        "room_id": clean_room_id,
        "name": room_name,
        "rows": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
        "row_counts": {"A": 8, "B": 11, "C": 11, "D": 11, "E": 11, "F": 11, "G": 11, "H": 11, "I": 11, "J": 11, "K": 13, "L": 16},
        "total_seats": len(seats_config),
        "seats": list(seats_config.keys()),
        "polygons": seats_config
    }

class ShowtimePayload(BaseModel):
    room_id: str
    date: str
    start_time: str
    duration_minutes: int
    movie_name: str
    break_minutes: int = 10

@app.get("/api/v1/showtimes")
def fetch_showtimes_endpoint(room_id: str = None, date: str = None, movie_id: int = None):
    clean_room = room_id.replace("seats_config_", "") if room_id else None
    catalog_items = get_catalog_showtimes(date_str=date, room_id=clean_room, movie_id=movie_id)
    return {
        "status": "success",
        "count": len(catalog_items),
        "rules": {
            "first_show_start": "08:30",
            "gap_minutes": 15,
            "rooms": ["room1", "room2", "room3", "room4"]
        },
        "showtimes": catalog_items
    }

@app.get("/api/v1/catalog/showtimes")
def fetch_catalog_showtimes_endpoint(date: str = None, room_id: str = None, movie_id: int = None):
    clean_room = room_id.replace("seats_config_", "") if room_id else None
    items = get_catalog_showtimes(date_str=date, room_id=clean_room, movie_id=movie_id)
    return {
        "status": "success",
        "count": len(items),
        "showtimes": items
    }

@app.get("/api/v1/movies")
def fetch_movies_endpoint(active_only: bool = True):
    movies = get_all_movies(active_only=active_only)
    return {
        "status": "success",
        "count": len(movies),
        "movies": movies
    }

@app.get("/api/v1/about")
def about_endpoint():
    return {
        "status": "success",
        "app_name": "CineSight AI Cinema Monitoring System",
        "version": "2.1.0",
        "tmdb_attribution": {
            "notice": "This product uses the TMDB API but is not endorsed or certified by TMDB.",
            "terms_url": "https://www.themoviedb.org/api-terms-of-use",
            "website": "https://www.themoviedb.org",
            "logos_url": "https://www.themoviedb.org/about/logos-attribution"
        },
        "data_sources": [
            {
                "type": "movies_catalog",
                "sources": ["tmdb", "manual"],
                "description": "Metadata phim (tiêu đề, thời lượng, poster, ngày phát hành) từ TMDB API v3 và danh mục dự phòng."
            },
            {
                "type": "showtimes",
                "source": "simulation",
                "description": "Lịch suất chiếu được sinh mô phỏng tự động theo quy tắc rạp chiếu phim (lưới 5 phút, nghỉ 15 phút, 4 phòng)."
            },
            {
                "type": "seat_occupancy",
                "source": "ai_computer_vision",
                "description": "Phát hiện vị trí khán giả qua camera giám sát góc cao bằng mô hình YOLOv8n fine-tuned (head detection)."
            }
        ]
    }

@app.post("/api/v1/showtimes")
def create_showtime_endpoint(payload: ShowtimePayload):
    if payload.duration_minutes < 105 or payload.duration_minutes > 120:
        return JSONResponse(
            status_code=400,
            content={"error": "Thời lượng phim theo quy định phải từ 105 phút (1h45p) đến 120 phút (2h00p)."}
        )
    item = save_showtime(
        room_id=payload.room_id.replace("seats_config_", ""),
        date=payload.date,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        movie_name=payload.movie_name,
        break_minutes=payload.break_minutes
    )
    return {"status": "success", "showtime": item}

@app.delete("/api/v1/tickets")
def delete_tickets_endpoint(room_id: str = None, show_id: str = None):
    from database import clear_tickets
    clear_tickets(room_id, show_id)
    return {"status": "success", "message": "Đã xóa toàn bộ vé"}

@app.get("/api/v1/tickets")
def fetch_tickets(room_id: str, show_id: str = None):
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
    shift: str = None

@app.get("/api/v1/employees")
def fetch_employees():
    return {"status": "success", "employees": get_employees()}

@app.post("/api/v1/employees")
def create_employee(payload: EmployeePayload):
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        emp_id = add_employee(payload.username, payload.password, payload.name, payload.role, payload.shift)
        return {"status": "success", "id": emp_id}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.put("/api/v1/employees/{emp_id}")
def edit_employee(emp_id: int, payload: EmployeePayload):
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        update_employee(emp_id, payload.username, payload.password, payload.name, payload.role, payload.shift)
        return {"status": "success", "message": f"Đã cập nhật nhân viên {emp_id}"}
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
    username_clean = payload.username.strip()
    password_clean = payload.password.strip()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role, shift FROM employees WHERE LOWER(username)=LOWER(?) AND password=?", (username_clean, password_clean))
    row = cursor.fetchone()
    conn.close()
    if row:
        shift_code = row[3]
        shift_label = "Chưa phân ca"
        if shift_code:
            for s in SHIFTS:
                if s["code"] == shift_code:
                    shift_label = s["label"]
                    break
        return {"status": "success", "user": {"id": row[0], "name": row[1], "role": row[2], "shift": shift_code, "shift_label": shift_label}}
    return JSONResponse(status_code=401, content={"error": "Tài khoản hoặc mật khẩu không chính xác"})


@app.get("/api/v1/shifts")
def get_shifts():
    return {"status": "success", "shifts": SHIFTS}

@app.get("/api/v1/incident_categories")
def get_incident_categories():
    return {"status": "success", "categories": INCIDENT_CATEGORIES}

class IncidentPayload(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    room_id: str = None
    show_id: str = None
    seat_ids: list = []
    reporter_id: int
    reporter_name: str
    reporter_role: str

import datetime

@app.post("/api/v1/incidents")
def add_incident(payload: IncidentPayload):
    try:
        # Validate category
        if payload.category not in [c["code"] for c in INCIDENT_CATEGORIES]:
            return JSONResponse(status_code=400, content={"error": "Loại sự cố không hợp lệ"})
            
        import re
        if payload.show_id and not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$', payload.show_id):
            return JSONResponse(status_code=422, content={"error": "Định dạng show_id không hợp lệ (cần ISO yyyy-MM-ddTHH:mm)"})
            
        from seat_mapper import normalize_seat
        normalized_seats = []
        if payload.seat_ids:
            for s in payload.seat_ids:
                if not re.match(r'^[a-zA-Z]+\s*\d+$', str(s).strip()):
                    return JSONResponse(status_code=422, content={"error": f"Mã ghế '{s}' không hợp lệ"})
                normalized_seats.append(normalize_seat(s))
        import json
        seat_ids_json = json.dumps(normalized_seats) if normalized_seats else ""
        
        # Determine shift label based on reporter_id
        shift_label = "Chưa phân ca"
        emp = get_employee(payload.reporter_id)
        if emp and len(emp) > 4 and emp.get('shift'):
            shift_code = emp.get('shift')
            for s in SHIFTS:
                if s["code"] == shift_code:
                    shift_label = s["label"]
                    break

        created_at = datetime.datetime.now().astimezone().isoformat()
        
        inc_id = create_incident(
            category=payload.category,
            severity=payload.severity,
            title=payload.title,
            description=payload.description,
            room_id=payload.room_id,
            show_id=payload.show_id,
            seat_ids=seat_ids_json,
            reporter_id=payload.reporter_id,
            reporter_name=payload.reporter_name,
            reporter_role=payload.reporter_role,
            shift_label=shift_label,
            created_at=created_at,
            status="open"
        )
        return {"status": "success", "id": inc_id, "created_at": created_at, "shift_label": shift_label}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/v1/incidents")
def fetch_incidents(room_id: str = None, status: str = None, category: str = None, from_time: str = None, to_time: str = None, limit: int = None):
    try:
        incidents = list_incidents(room_id, status, category, from_time, to_time, limit)
        for inc in incidents:
            if isinstance(inc.get("seat_ids"), str):
                try:
                    inc["seat_ids"] = json.loads(inc["seat_ids"]) if inc["seat_ids"] else []
                except Exception:
                    pass
        return {"status": "success", "incidents": incidents}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/v1/incidents/{incident_id}")
def fetch_incident(incident_id: int):
    try:
        incident = get_incident(incident_id)
        if not incident:
            return JSONResponse(status_code=404, content={"error": "Không tìm thấy sự cố"})
        return {"status": "success", "incident": incident}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

class ResolveIncidentPayload(BaseModel):
    resolver_id: int = 1
    resolver_name: str = "Quản trị viên"
    resolver: str = None

@app.post("/api/v1/incidents/{incident_id}/resolve")
def resolve_incident_endpoint(incident_id: int, payload: ResolveIncidentPayload):
    try:
        resolved_at = datetime.datetime.now().astimezone().isoformat()
        res_name = payload.resolver_name if payload.resolver_name != "Quản trị viên" else (payload.resolver or payload.resolver_name)
        res_id = payload.resolver_id or 1
        resolve_incident(incident_id, res_id, res_name, resolved_at)
        return {"status": "success", "message": f"Đã đánh dấu sự cố {incident_id} là đã xử lý.", "resolved_at": resolved_at}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

print("[INFO] Đang tải mô hình YOLO...")
try:
    import os
    default_model_path = os.path.join(os.path.dirname(__file__), "models", "best_head_v2.pt")
    model_path = os.environ.get("CINESIGHT_MODEL", default_model_path)
    MODEL_CONF = float(os.environ.get("CINESIGHT_CONF", "0.25"))
    MODEL_IMGSZ = int(os.environ.get("CINESIGHT_IMGSZ", "800"))
    model = YOLO(model_path)
    print(f"[OK] Tải mô hình thành công: {model_path} (conf={MODEL_CONF}, imgsz={MODEL_IMGSZ})")
except Exception as e:
    print(f"[LỖI] Không thể tải mô hình YOLO: {e}")
    model = None
    MODEL_CONF = 0.25
    MODEL_IMGSZ = 800



