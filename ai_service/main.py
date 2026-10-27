import json
import sys
import os
sys.path.append(os.path.dirname(__file__))

from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Body, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
import cv2
import numpy as np
from database import (
    get_seats,
    init_db,
    save_alerts,
    get_active_alerts,
    get_all_alerts,
    resolve_alert,
    get_tickets_list,
    get_configs,
    update_config,
    get_employees,
    add_employee,
    update_employee,
    delete_employee,
    create_incident,
    list_incidents,
    get_incident,
    resolve_incident,
    get_employee,
    showtime_exists,
)
from security import create_token, verify_token
from seat_mapper import load_seats_config, process_ai_detections, generate_alerts
from movies_repo import init_movies_tables, get_all_movies, get_catalog_showtimes

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB giới hạn ảnh upload (Điểm 9)


def _extract_bearer_user(request: Request) -> Optional[dict]:
    """Trích xuất và xác thực Bearer Token từ Header Authorization (Điểm 1A)."""
    if request is None:
        return None
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    if not auth_header.lower().startswith("bearer "):
        return None
    raw_token = auth_header[7:].strip()
    user_id = verify_token(raw_token)
    if user_id is None:
        return None
    return get_employee(user_id)


def _require_auth_error(request: Request, require_manager: bool = False) -> Optional[JSONResponse]:
    """Kiểm tra xác thực và phân quyền (Điểm 1A):
    - Nếu không có token hợp lệ -> trả về 401.
    - Nếu require_manager=True nhưng user.role != 'Quản lý' -> trả về 403.
    """
    user = _extract_bearer_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Yêu cầu đăng nhập (thiếu hoặc hết hạn Bearer Token)."},
        )
    if require_manager and str(user.get("role", "")).strip() != "Quản lý":
        return JSONResponse(
            status_code=403,
            content={"error": "Chỉ tài khoản Quản lý mới có quyền thực hiện thao tác này."},
        )
    return None


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
        if not isinstance(tickets_list, list):
            return JSONResponse(status_code=400, content={"error": "scanned_tickets phải là mảng JSON."})
        from database import save_tickets
        from seat_mapper import normalize_seat
        
        # Chuẩn hóa seat_id trước khi lưu
        for t in tickets_list:
            t['seat'] = normalize_seat(t['seat'])
            
        save_tickets(room_id, show_id, tickets_list)
        return {"status": "success", "message": f"Đã lưu {len(tickets_list)} vé cho phòng {room_id}, suất {show_id}"}
    except ValueError as ve:
        return JSONResponse(status_code=404, content={"error": str(ve)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/v1/analyze")
async def analyze_cinema_room(
    image: UploadFile = File(..., description="Ảnh chụp từ camera CCTV phòng chiếu"),
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1"),
    show_id: str = Form(..., description="Mã suất chiếu. VD: 2026-09-25T19:30")
):
    # Điểm 8: Không cho phép chạy âm thầm khi mô hình YOLO chưa tải được
    if model is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Mô hình AI (YOLO) chưa sẵn sàng. Không thể phân tích ảnh lúc này."}
        )

    # Điểm 4A: Từ chối phân tích nếu suất chiếu không tồn tại trong lịch chiếu
    if not showtime_exists(room_id, show_id):
        return JSONResponse(
            status_code=404,
            content={"error": f"Suất chiếu '{show_id}' tại phòng '{room_id}' không tồn tại trong lịch chiếu."}
        )

    seats_config = load_seats_config(room_id)
    if not seats_config:
        return JSONResponse(
            status_code=404,
            content={"error": f"Chưa có bản đồ ghế cho phòng '{room_id}'."}
        )

    # Điểm 9: Kiểm tra kích thước và tính hợp lệ của file ảnh trước khi decode
    contents = await image.read()
    if not contents:
        return JSONResponse(status_code=400, content={"error": "File ảnh tải lên bị rỗng."})
    if len(contents) > MAX_IMAGE_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": f"Kích thước ảnh vượt quá giới hạn cho phép ({MAX_IMAGE_BYTES // (1024 * 1024)}MB)."}
        )

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None or img.size == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "Dữ liệu tải lên không phải là định dạng ảnh hợp lệ (JPEG/PNG)."}
        )

    tap_A = get_seats(room_id, show_id)

    h_img, w_img = img.shape[:2]
    scale_x = 1920.0 / w_img if w_img > 0 else 1.0
    scale_y = 1080.0 / h_img if h_img > 0 else 1.0

    import time
    from database import save_inference_log

    t_start = time.perf_counter()
    detected_heads = []
    results = model.predict(img, conf=MODEL_CONF, iou=0.45, imgsz=MODEL_IMGSZ, classes=[0], verbose=False)
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = ((x1 + x2) / 2) * scale_x
            cy = ((y1 + y2) / 2) * scale_y
            detected_heads.append((cx, cy))
    t_after_yolo = time.perf_counter()

    tap_B = process_ai_detections(detected_heads, seats_config)
    t_after_map = time.perf_counter()

    yolo_time_ms = round((t_after_yolo - t_start) * 1000.0, 2)
    mapping_time_ms = round((t_after_map - t_after_yolo) * 1000.0, 2)
    inference_time_ms = round((t_after_map - t_start) * 1000.0, 2)

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

    save_inference_log(
        room_id=room_id,
        show_id=show_id,
        image_width=w_img,
        image_height=h_img,
        total_seats=len(seats_config),
        booked_tickets_count=len(tap_A),
        detected_heads_count=len(detected_heads),
        mapped_seats_count=len(tap_B),
        illegal_count=len(alert_result["illegal_occupants"]),
        missing_count=len(alert_result["missing_guests"]),
        over_capacity=bool(alert_result.get("over_capacity")),
        inference_time_ms=inference_time_ms,
        yolo_time_ms=yolo_time_ms,
        mapping_time_ms=mapping_time_ms,
    )

    return {
        "status": "success",
        "room_id": room_id,
        "show_id": show_id,
        "summary": {
            "total_seats": len(seats_config),
            "total_detected_people": len(detected_heads),
            "tap_A_from_app": list(tap_A),
            "tap_B_from_camera": list(tap_B),
            "inference_time_ms": inference_time_ms,
            "yolo_time_ms": yolo_time_ms,
            "mapping_time_ms": mapping_time_ms,
        },
        "alerts": alert_result
    }


@app.get("/api/v1/inference_logs")
def fetch_inference_logs(room_id: str = None, show_id: str = None, limit: int = 50):
    from database import get_inference_logs
    logs = get_inference_logs(room_id=room_id, show_id=show_id, limit=limit)
    return {"status": "success", "logs": logs}


@app.get("/api/v1/alerts")
def fetch_alerts(room_id: str = None):
    alerts = get_active_alerts(room_id)
    return {"status": "success", "alerts": alerts}

@app.get("/api/v1/alerts/history")
def fetch_alerts_history(room_id: str = None, alert_type: str = None, status: str = None):
    alerts = get_all_alerts(room_id, alert_type, status)
    return {"status": "success", "alerts": alerts}

@app.delete("/api/v1/alerts")
def delete_alerts_endpoint(request: Request, room_id: str = None, show_id: str = None):
    auth_err = _require_auth_error(request, require_manager=False)
    if auth_err:
        return auth_err
    from database import clear_alerts
    clear_alerts(room_id, show_id)
    return {"status": "success", "message": "Đã xóa toàn bộ cảnh báo"}

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
            room_name = f"Phòng chiếu số {room_num}" if room_num.isdigit() else room_id
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    seats_data = json.load(f)
                total_seats = len(seats_data)
                is_calibrated = os.path.exists(os.path.join(calibration_dir, f"{room_id}.jpg"))
                rows_dict = {}
                for sname in sorted(seats_data.keys()):
                    m = re.match(r'([A-Za-z]+)', sname)
                    if m:
                        r_code = m.group(1).upper()
                        rows_dict[r_code] = rows_dict.get(r_code, 0) + 1
                rows_list = list(rows_dict.keys())

                rooms.append({
                    "room_id": room_id,
                    "name": room_name,
                    "total_seats": total_seats,
                    "rows": rows_list,
                    "row_counts": rows_dict,
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
    clean_room_id = room_id.replace("seats_config_", "").strip()
    if clean_room_id.lower() == "all":
        best_cfg = {}
        for r in ["room1", "room4", "room2", "room3"]:
            cfg = load_seats_config(r)
            if cfg and len(cfg) > len(best_cfg):
                best_cfg = cfg
        seats_config = best_cfg
    else:
        seats_config = load_seats_config(clean_room_id)

    if not seats_config:
        return JSONResponse(status_code=404, content={"error": f"Không tìm thấy sơ đồ ghế cho '{clean_room_id}'"})
    room_num = clean_room_id.replace("room", "")
    room_name = "Tất cả phòng chiếu (Đồng bộ)" if clean_room_id.lower() == "all" else (f"Phòng chiếu {room_num}" if room_num.isdigit() else clean_room_id)
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

@app.post("/api/v1/rooms/{room_id}/seats")
async def save_room_seats_endpoint(room_id: str, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
    try:
        data = await request.json()
        clean_room_id = room_id.replace("seats_config_", "").strip().lower()
        targets = ["room1", "room2", "room3", "room4"] if clean_room_id == "all" else [clean_room_id]
        
        cfg_dir = os.path.join(os.path.dirname(__file__), "seats_configs")
        os.makedirs(cfg_dir, exist_ok=True)
        for r in targets:
            config_path = os.path.join(cfg_dir, f"seats_config_{r}.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
        msg = f"Đã lưu thành công {len(data)} ghế đồng bộ cho TẤT CẢ các phòng (room1 -> room4)" if clean_room_id == "all" else f"Đã lưu thành công {len(data)} ghế cho {clean_room_id}"
        return {"status": "success", "message": msg}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


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

@app.delete("/api/v1/tickets")
def delete_tickets_endpoint(request: Request, room_id: str = None, show_id: str = None):
    auth_err = _require_auth_error(request, require_manager=False)
    if auth_err:
        return auth_err
    from database import clear_tickets
    clear_tickets(room_id, show_id)
    return {"status": "success", "message": "Đã xóa toàn bộ vé"}

@app.get("/api/v1/tickets")
def fetch_tickets(room_id: str, show_id: str = None):
    tickets = get_tickets_list(room_id, show_id)
    return {"status": "success", "tickets": tickets}

@app.post("/api/v1/resolve_alert/{alert_id}")
def mark_alert_resolved(alert_id: int, request: Request):
    auth_err = _require_auth_error(request, require_manager=False)
    if auth_err:
        return auth_err
    resolve_alert(alert_id)
    return {"status": "success", "message": f"Đã đánh dấu cảnh báo {alert_id} là đã xử lý."}

class ConfigPayload(BaseModel):
    key: str
    value: str

@app.get("/api/v1/configs")
def fetch_configs():
    return {"status": "success", "configs": get_configs()}

@app.post("/api/v1/configs")
def save_config(payload: ConfigPayload, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
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
def create_employee(payload: EmployeePayload, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        emp_id = add_employee(payload.username, payload.password, payload.name, payload.role, payload.shift)
        return {"status": "success", "id": emp_id}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.put("/api/v1/employees/{emp_id}")
def edit_employee(emp_id: int, payload: EmployeePayload, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        update_employee(emp_id, payload.username, payload.password, payload.name, payload.role, payload.shift)
        return {"status": "success", "message": f"Đã cập nhật nhân viên {emp_id}"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.delete("/api/v1/employees/{emp_id}")
def remove_employee(emp_id: int, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
    delete_employee(emp_id)
    return {"status": "success"}

class LoginPayload(BaseModel):
    username: str
    password: str

@app.post("/api/v1/login")
def login_user(payload: LoginPayload):
    from database import authenticate_employee
    user = authenticate_employee(payload.username, payload.password)
    if user:
        token = create_token(user["id"])
        return {"status": "success", "token": token, "user": user}
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
    reporter_id: Optional[int] = None
    reporter_name: Optional[str] = None
    reporter_role: Optional[str] = None

import datetime

@app.post("/api/v1/incidents")
def add_incident(payload: IncidentPayload, request: Request):
    try:
        # Ưu tiên lấy người báo cáo từ Bearer Token nếu có (Điểm 1A & Điểm 5)
        authed_user = _extract_bearer_user(request)
        effective_reporter_id = authed_user["id"] if authed_user else payload.reporter_id
        if effective_reporter_id is None:
            return JSONResponse(status_code=401, content={"error": "Yêu cầu đăng nhập hoặc cung cấp reporter_id hợp lệ."})

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
        
        emp = get_employee(effective_reporter_id)
        if not emp:
            return JSONResponse(
                status_code=400,
                content={"error": f"Nhân viên báo cáo (id={effective_reporter_id}) không tồn tại."},
            )

        shift_label = "Chưa phân ca"
        shift_code = emp.get("shift")
        if shift_code:
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
            reporter_id=effective_reporter_id,
            created_at=created_at,
            status="open",
            reporter_shift=shift_code,
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
    resolver_id: Optional[int] = None
    resolver_name: Optional[str] = None
    resolver: Optional[str] = None

@app.post("/api/v1/incidents/{incident_id}/resolve")
def resolve_incident_endpoint(incident_id: int, request: Request, payload: ResolveIncidentPayload = Body(default=ResolveIncidentPayload())):
    try:
        # Ưu tiên lấy người xử lý từ Bearer Token (Điểm 1A, 2, 5)
        authed_user = _extract_bearer_user(request)
        effective_resolver_id = authed_user["id"] if authed_user else (payload.resolver_id if payload else None)
        if effective_resolver_id is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Yêu cầu đăng nhập hoặc cung cấp resolver_id hợp lệ để xác nhận xử lý sự cố."},
            )

        resolved_at = datetime.datetime.now().astimezone().isoformat()
        resolve_incident(incident_id, effective_resolver_id, None, resolved_at)
        return {
            "status": "success",
            "message": f"Đã đánh dấu sự cố {incident_id} là đã xử lý.",
            "resolved_at": resolved_at,
            "resolved_by_id": effective_resolver_id,
        }
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



