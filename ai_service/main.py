import json
import sys
import os
import re
sys.path.append(os.path.dirname(__file__))

from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Body, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
import cv2
import numpy as np
from database import (
    get_seats,
    init_db,
    save_alerts,
    refresh_showtime_alerts,
    get_active_alerts,
    get_grouped_active_alerts,
    resolve_room_alerts,
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
    update_incident_photo,
    get_employee,
    showtime_exists,
    touch_employee_last_seen,
    is_inactive_account_with_valid_password,
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
    emp = get_employee(user_id)
    if not emp:
        return None
    # Vấn đề 6: từ chối token của tài khoản đã ngưng hoạt động
    if emp.get("is_active", 1) == 0:
        return None
    touch_employee_last_seen(user_id)
    return emp


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


CAMERA_KEY_HEADER = "x-camera-key"


def _camera_key_ok(request: Request) -> bool:
    if request is None:
        return False
    import hmac
    expected = os.environ.get("CINESIGHT_CAMERA_KEY", "CINESIGHT_CAM_SECURE_2026")
    given = request.headers.get(CAMERA_KEY_HEADER) or ""
    return bool(given) and hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))


def _is_internal_request(request: Request) -> bool:
    """Gọi trực tiếp từ nội bộ máy chủ (không đi qua tunnel/proxy Internet)."""
    if request is None:
        return True
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "testclient"):
        return False
    return not (request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For"))


def _analyze_auth_error(request: Request) -> Optional[JSONResponse]:
    """Dual auth cho /analyze: Bearer hợp lệ HOẶC X-Camera-Key khớp HOẶC gọi nội bộ."""
    if _extract_bearer_user(request) or _camera_key_ok(request) or _is_internal_request(request):
        return None
    return JSONResponse(
        status_code=401,
        content={"error": "Yêu cầu Bearer Token hoặc X-Camera-Key hợp lệ."},
    )


def _sync_auth_error(request: Request) -> Optional[JSONResponse]:
    """/sync_tickets: Bearer Token (app soát vé) hoặc X-Camera-Key (khóa đồng bộ nội bộ)."""
    if request is None or _extract_bearer_user(request) or _camera_key_ok(request):
        return None
    return JSONResponse(
        status_code=401,
        content={"error": "Yêu cầu đăng nhập (Bearer Token) hoặc X-Camera-Key hợp lệ."},
    )


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

WEB_ADMIN_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web_admin", "dist"))


@app.get("/")
def health_check(request: Request = None):
    accept = request.headers.get("accept", "") if request else ""
    index_path = os.path.join(WEB_ADMIN_DIST, "index.html")
    if "text/html" in accept and os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"status": "CineSight AI Service đang chạy", "version": "2.0.0"}

@app.post("/api/v1/sync_tickets")
def sync_tickets_from_app(
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1"),
    show_id: str = Form(..., description="Mã suất chiếu. VD: 2026-09-25T19:30"),
    scanned_tickets: str = Form(..., description="Mảng JSON chứa các Object vé hợp lệ (Tập A)"),
    request: Request = None,
):
    import json
    auth_err = _sync_auth_error(request)
    if auth_err:
        return auth_err
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
    show_id: str = Form(..., description="Mã suất chiếu. VD: 2026-09-25T19:30"),
    trigger_source: str = Form("MANUAL", description="Nguồn kích hoạt: MANUAL, AUTO_T_MINUS_5, AUTO_T_MINUS_3"),
    request: Request = None,
):
    auth_err = _analyze_auth_error(request)
    if auth_err:
        return auth_err

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

    # Vấn đề 2: tiền kiểm tra chất lượng ảnh (cảnh báo mềm, không chặn cứng)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = round(float(np.mean(gray)), 2)
    sharpness = round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2)
    quality_warnings = []
    clahe_applied = False
    if brightness < 40.0:
        quality_warnings.append("LOW_LIGHT")
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        img = cv2.cvtColor(cv2.merge((l_ch, a_ch, b_ch)), cv2.COLOR_LAB2BGR)
        clahe_applied = True
    if sharpness < 35.0:
        quality_warnings.append("LOW_SHARPNESS")

    tap_A = get_seats(room_id, show_id)

    h_img, w_img = img.shape[:2]
    scale_x = 1920.0 / w_img if w_img > 0 else 1.0
    scale_y = 1080.0 / h_img if h_img > 0 else 1.0

    import time
    from database import save_inference_log

    t_start = time.perf_counter()
    detected_heads = []
    results = model.predict(img, conf=MODEL_CONF, iou=0.45, imgsz=MODEL_IMGSZ, classes=[0], augment=False, verbose=False)
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0].item()) if box.conf is not None and len(box.conf) > 0 else 1.0
            cx = ((x1 + x2) / 2.0) * scale_x
            cy = (y1 + 0.78 * (y2 - y1)) * scale_y
            bw = (x2 - x1) * scale_x
            bh = (y2 - y1) * scale_y
            detected_heads.append((cx, cy, conf, bw, bh))
    t_after_yolo = time.perf_counter()

    tap_B = process_ai_detections(detected_heads, seats_config)
    valid_people_count = len(tap_B)
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
        total_detected_people=valid_people_count,
        capacity_threshold=threshold
    )

    clean_trigger_source = (
        str(trigger_source).strip().upper()
        if isinstance(trigger_source, str) and trigger_source.strip()
        else "MANUAL"
    )

    refresh_info = refresh_showtime_alerts(room_id, show_id, alert_result)

    save_inference_log(
        room_id=room_id,
        show_id=show_id,
        image_width=w_img,
        image_height=h_img,
        total_seats=len(seats_config),
        booked_tickets_count=len(tap_A),
        detected_heads_count=valid_people_count,
        mapped_seats_count=len(tap_B),
        illegal_count=len(alert_result["illegal_occupants"]),
        missing_count=len(alert_result["missing_guests"]),
        over_capacity=bool(alert_result.get("over_capacity")),
        inference_time_ms=inference_time_ms,
        yolo_time_ms=yolo_time_ms,
        mapping_time_ms=mapping_time_ms,
        trigger_source=clean_trigger_source,
    )

    no_tickets_warning = len(tap_A) == 0
    verification_note = (
        "Suất chiếu này chưa có vé được quét (Tập A = 0). Không thể đối soát khách vắng mặt (missing_guest); mọi ghế có người đang được tính là chưa có vé."
        if no_tickets_warning
        else ""
    )

    return {
        "status": "success",
        "room_id": room_id,
        "show_id": show_id,
        "trigger_source": clean_trigger_source,
        "summary": {
            "total_seats": len(seats_config),
            "total_detected_people": valid_people_count,
            "empty_seats_count": max(0, len(seats_config) - len(tap_B)),
            "no_tickets_warning": no_tickets_warning,
            "verification_note": verification_note,
            "tap_A_from_app": sorted(list(tap_A)),
            "tap_B_from_camera": sorted(list(tap_B)),
            "inference_time_ms": inference_time_ms,
            "yolo_time_ms": yolo_time_ms,
            "mapping_time_ms": mapping_time_ms,
            "trigger_source": clean_trigger_source,
            "auto_resolved_alerts": refresh_info.get("auto_resolved_count", 0),
            "image_quality": {
                "brightness": brightness,
                "sharpness": sharpness,
                "clahe_applied": clahe_applied,
                "warnings": quality_warnings,
            },
        },
        "alerts": alert_result
    }


@app.get("/api/v1/inference_logs")
def fetch_inference_logs(room_id: str = None, show_id: str = None, limit: int = 50):
    from database import get_inference_logs
    logs = get_inference_logs(room_id=room_id, show_id=show_id, limit=limit)
    return {"status": "success", "logs": logs}


class ResolveRoomAlertsPayload(BaseModel):
    room_id: str
    show_id: str

@app.get("/api/v1/alerts")
def fetch_alerts(room_id: str = None):
    alerts = get_active_alerts(room_id)
    grouped = get_grouped_active_alerts(room_id)
    return {
        "status": "success",
        "alerts": alerts,
        "grouped_alerts": grouped,
        "total_active_alerts": len(alerts),
        "total_active_rooms": len(grouped),
    }

@app.post("/api/v1/resolve_room_alerts")
@app.post("/api/v1/alerts/resolve_room")
def mark_room_alerts_resolved(payload: ResolveRoomAlertsPayload, request: Request):
    auth_err = _require_auth_error(request, require_manager=False)
    if auth_err:
        return auth_err
    count = resolve_room_alerts(payload.room_id, payload.show_id)
    return {
        "status": "success",
        "resolved_count": count,
        "room_id": payload.room_id,
        "show_id": payload.show_id,
        "message": f"Đã đánh dấu xử lý {count} cảnh báo của phòng {payload.room_id}.",
    }

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
    room_name = "Tất cả phòng chiếu (Đồng bộ)" if clean_room_id.lower() == "all" else (f"Phòng chiếu số {room_num}" if room_num.isdigit() else clean_room_id)
    rows_dict = {}
    for sname in sorted(seats_config.keys()):
        m = re.match(r'([A-Za-z]+)', sname)
        if m:
            r_code = m.group(1).upper()
            rows_dict[r_code] = rows_dict.get(r_code, 0) + 1
    rows_list = sorted(list(rows_dict.keys()))

    return {
        "status": "success",
        "room_id": clean_room_id,
        "name": room_name,
        "rows": rows_list,
        "row_counts": rows_dict,
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
    is_active: Optional[int] = None

@app.get("/api/v1/employees")
def fetch_employees(request: Request = None):
    authed_user = _extract_bearer_user(request)
    if authed_user:
        return {"status": "success", "employees": get_employees(viewer_id=authed_user["id"])}
    # Không có token: không bao giờ lộ tài khoản Quản lý
    return {"status": "success", "employees": [e for e in get_employees() if e.get("role") != "Quản lý"]}

@app.post("/api/v1/employees")
def create_employee(payload: EmployeePayload, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
    if str(payload.role).strip() == "Quản lý":
        return JSONResponse(
            status_code=403,
            content={"error": "Không được phép tạo tài khoản Quản lý mới qua API. Chỉ được tạo nhân viên Soát vé."},
        )
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
    authed_user = _extract_bearer_user(request)
    target_emp = get_employee(emp_id)
    if not target_emp:
        return JSONResponse(status_code=404, content={"error": "Không tìm thấy nhân viên."})
    is_self = target_emp["id"] == authed_user["id"]
    if target_emp["role"] == "Quản lý" and not is_self:
        return JSONResponse(status_code=403, content={"error": "Không có quyền chỉnh sửa tài khoản Quản lý khác."})
    if not is_self and str(payload.role).strip() == "Quản lý":
        return JSONResponse(status_code=403, content={"error": "Không được phép nâng quyền nhân viên lên Quản lý."})
    if is_self and str(payload.role).strip() != target_emp["role"]:
        return JSONResponse(status_code=403, content={"error": "Không thể tự thay đổi vai trò của chính mình."})
    if is_self and payload.is_active == 0:
        return JSONResponse(status_code=403, content={"error": "Không thể tự ngưng hoạt động tài khoản của chính mình."})
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        update_employee(emp_id, payload.username, payload.password, payload.name, payload.role,
                        payload.shift, payload.is_active)
        return {"status": "success", "message": f"Đã cập nhật nhân viên {emp_id}"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.delete("/api/v1/employees/{emp_id}")
def remove_employee(emp_id: int, request: Request):
    auth_err = _require_auth_error(request, require_manager=True)
    if auth_err:
        return auth_err
    authed_user = _extract_bearer_user(request)
    target_emp = get_employee(emp_id)
    if not target_emp:
        return JSONResponse(status_code=404, content={"error": "Không tìm thấy nhân viên."})
    if emp_id == authed_user["id"]:
        return JSONResponse(status_code=403, content={"error": "Không thể tự xóa tài khoản của chính mình."})
    if target_emp["role"] == "Quản lý":
        return JSONResponse(status_code=403, content={"error": "Không có quyền xóa tài khoản Quản lý khác."})
    result = delete_employee(emp_id)
    msg = ("Nhân viên đã có biên bản sự cố nên được chuyển sang Ngưng hoạt động."
           if result["action"] == "deactivated" else "Đã xóa nhân viên.")
    return {"status": "success", "action": result["action"], "id": emp_id, "message": msg}

class LoginPayload(BaseModel):
    username: str
    password: str
    client: Optional[str] = None

@app.post("/api/v1/login")
def login_user(payload: LoginPayload):
    from database import authenticate_employee
    user = authenticate_employee(payload.username, payload.password)
    if user:
        if (payload.client or "").strip().lower() == "web_admin" and user.get("role") != "Quản lý":
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Tài khoản Nhân viên (Soát vé) chỉ được đăng nhập trên Mobile App. Vui lòng dùng tài khoản Quản lý cho Web Admin!"
                },
            )
        token = create_token(user["id"])
        return {"status": "success", "token": token, "user": user}
    if is_inactive_account_with_valid_password(payload.username, payload.password):
        return JSONResponse(status_code=401, content={"error": "Tài khoản đã ngưng hoạt động"})
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


INCIDENTS_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "incidents")
os.makedirs(INCIDENTS_UPLOAD_DIR, exist_ok=True)

@app.post("/api/v1/incidents/{incident_id}/photo")
def upload_incident_photo_endpoint(incident_id: int, image: UploadFile = File(...)):
    try:
        import shutil
        inc = get_incident(incident_id)
        if not inc:
            return JSONResponse(status_code=404, content={"error": f"Không tìm thấy sự cố {incident_id}"})
        
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        clean_ext = ext if ext.lower() in [".jpg", ".jpeg", ".png", ".webp"] else ".jpg"
        saved_filename = f"incident_{incident_id}_{int(datetime.datetime.now().timestamp())}{clean_ext}"
        saved_path = os.path.join(INCIDENTS_UPLOAD_DIR, saved_filename)
        
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        relative_url = f"/api/v1/incidents/photo/{saved_filename}"
        update_incident_photo(incident_id, relative_url)
        return {"status": "success", "image_url": relative_url, "message": "Đã lưu ảnh sự cố thành công."}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/v1/incidents/photo/{filename}")
def get_incident_photo_endpoint(filename: str):
    file_path = os.path.join(INCIDENTS_UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"error": "Ảnh sự cố không tồn tại"})


@app.delete("/api/v1/incidents/resolved/clear")
def clear_resolved_incidents_endpoint():
    try:
        from database import clear_resolved_incidents
        count = clear_resolved_incidents()
        return {"status": "success", "message": f"Đã xóa toàn bộ {count} sự cố đã khắc phục.", "count": count}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.delete("/api/v1/incidents/{incident_id}")
def remove_incident_endpoint(incident_id: int):
    try:
        from database import delete_incident
        success = delete_incident(incident_id)
        if not success:
            return JSONResponse(status_code=404, content={"error": f"Không tìm thấy sự cố {incident_id}"})
        return {"status": "success", "message": f"Đã xóa sự cố {incident_id} thành công."}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})



# ---------------------------------------------------------------------------
# Vấn đề 12: Bộ lập lịch 3 chế độ (Rule-based T-5 & T-3 + Time-Warp Simulation)
# ---------------------------------------------------------------------------
import asyncio
from io import BytesIO

SCHEDULER_STATE = {
    "enabled": True,
    "interval_seconds": 30,
    "milestones_minutes": [-5, -3],
    "last_check_at": None,
    "last_simulated_clock": None,
    "last_triggered": None,
}


def _resolve_room_camera_snapshot(room_id: str) -> Optional[str]:
    """Tìm tệp khung hình camera mẫu đại diện cho phòng chiếu để phục vụ chụp tự động T-5 / T-3."""
    clean_room = str(room_id).replace("seats_config_", "").strip()
    base_dir = os.path.dirname(__file__)
    env_override = os.environ.get(f"CINESIGHT_SNAPSHOT_{clean_room.upper()}", "").strip()
    if env_override and os.path.isfile(env_override):
        return env_override

    candidates = []
    if clean_room == "room3":
        candidates.append(os.path.join(base_dir, "calibration_images", "room3.jpg"))
    else:
        # Ưu tiên khung hình có khách thực tế cho room1/2/4 để demo đối soát trực quan
        candidates.append(os.path.join(base_dir, "datasets", "head_v2", "images", "test", "room1_cam_edited_0456s.jpg"))
        candidates.append(os.path.join(base_dir, "calibration_images", f"{clean_room}.jpg"))
    candidates.append(os.path.join(base_dir, "calibration_images", "room1.jpg"))

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _has_milestone_already_run(room_id: str, show_id: str, trigger_source: str) -> bool:
    from database import _connect, _normalize_room_id
    clean_room = _normalize_room_id(room_id)
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM ai_inference_logs WHERE room_id=? AND show_id=? AND trigger_source=? LIMIT 1",
            (clean_room, str(show_id).strip(), trigger_source),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


async def _run_auto_snapshot_for_showtime(room_id: str, show_id: str, trigger_source: str, simulated_clock_iso: str = None) -> dict:
    snap_path = _resolve_room_camera_snapshot(room_id)
    if not snap_path:
        return {"status": "error", "error": f"Không tìm thấy tệp snapshot camera cho phòng {room_id}."}
    with open(snap_path, "rb") as f:
        img_bytes = f.read()
    upload = UploadFile(filename=os.path.basename(snap_path), file=BytesIO(img_bytes))
    res = await analyze_cinema_room(
        image=upload,
        room_id=room_id,
        show_id=show_id,
        trigger_source=trigger_source,
        request=None,
    )
    if isinstance(res, JSONResponse):
        return json.loads(res.body.decode("utf-8"))
    res["scheduler_simulation"] = {
        "trigger_source": trigger_source,
        "simulated_clock": simulated_clock_iso,
        "snapshot_file": os.path.basename(snap_path),
    }
    SCHEDULER_STATE["last_triggered"] = {
        "room_id": room_id,
        "show_id": show_id,
        "trigger_source": trigger_source,
        "simulated_clock": simulated_clock_iso,
        "triggered_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return res


async def check_and_run_scheduled_scans(now_dt: Optional[datetime.datetime] = None) -> list:
    """Chế độ 1: Kiểm tra mọi suất chiếu đang cách giờ hiện tại 5 phút (T-5) hoặc 3 phút (T-3)."""
    from database import _connect
    tz_vn = datetime.timezone(datetime.timedelta(hours=7))
    ref_now = now_dt or datetime.datetime.now(tz_vn)
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=tz_vn)
    SCHEDULER_STATE["last_check_at"] = ref_now.isoformat(timespec="seconds")

    date_prefix = ref_now.strftime("%Y-%m-%d")
    conn = _connect()
    conn.row_factory = lambda cur, row: {col[0]: row[idx] for idx, col in enumerate(cur.description)}
    try:
        shows = conn.execute(
            "SELECT room_id, show_id, start_at FROM showtimes WHERE status='scheduled' AND show_id LIKE ?",
            (f"{date_prefix}%",),
        ).fetchall()
    finally:
        conn.close()

    triggered_results = []
    for sh in shows:
        room_id = sh["room_id"]
        show_id = sh["show_id"]
        try:
            if sh.get("start_at"):
                start_dt = datetime.datetime.fromisoformat(str(sh["start_at"]))
            else:
                start_dt = datetime.datetime.fromisoformat(str(show_id)).replace(tzinfo=tz_vn)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=tz_vn)
        except Exception:
            continue

        minutes_until_start = (start_dt - ref_now).total_seconds() / 60.0
        for milestone_min, source_label in ((5.0, "AUTO_T_MINUS_5"), (3.0, "AUTO_T_MINUS_3")):
            if (milestone_min - 0.5) <= minutes_until_start <= (milestone_min + 0.5):
                if not _has_milestone_already_run(room_id, show_id, source_label):
                    out = await _run_auto_snapshot_for_showtime(
                        room_id=room_id,
                        show_id=show_id,
                        trigger_source=source_label,
                        simulated_clock_iso=ref_now.isoformat(timespec="seconds"),
                    )
                    triggered_results.append(out)
    return triggered_results


async def _scheduler_daemon_loop():
    while True:
        try:
            if SCHEDULER_STATE.get("enabled", True) and model is not None:
                await check_and_run_scheduled_scans()
            from database import cleanup_resolved_incidents
            cleanup_resolved_incidents(hours=1.0)
        except Exception as e:
            print(f"[SCHEDULER] Lỗi kiểm tra lịch tự động: {e}")
        await asyncio.sleep(SCHEDULER_STATE.get("interval_seconds", 30))


@app.on_event("startup")
async def _start_camera_scheduler():
    asyncio.create_task(_scheduler_daemon_loop())


class PreShowTriggerPayload(BaseModel):
    room_id: str
    show_id: str
    offset_minutes: int = -3


@app.post("/api/v1/scheduler/trigger_pre_show")
async def trigger_pre_show_endpoint(payload: PreShowTriggerPayload, request: Request = None):
    """Chế độ 2 (Time-Warp Simulation):
    Đặt đồng hồ mô phỏng về đúng mốc T-5 hoặc T-3 phút trước giờ bắt đầu của suất chiếu đang chọn
    và tự động kích hoạt chụp & phân tích AI cho phòng chiếu đó.
    """
    auth_err = _analyze_auth_error(request)
    if auth_err:
        return auth_err

    if model is None:
        return JSONResponse(status_code=503, content={"error": "Mô hình AI (YOLO) chưa sẵn sàng."})

    clean_room = str(payload.room_id).replace("seats_config_", "").strip()
    clean_show = str(payload.show_id).strip()
    if not showtime_exists(clean_room, clean_show):
        return JSONResponse(
            status_code=404,
            content={"error": f"Suất chiếu '{clean_show}' tại phòng '{clean_room}' không tồn tại trong lịch chiếu."},
        )

    offset = int(payload.offset_minutes or -3)
    abs_min = 5 if abs(offset) == 5 else 3
    trigger_source = f"AUTO_T_MINUS_{abs_min}"

    tz_vn = datetime.timezone(datetime.timedelta(hours=7))
    try:
        show_start_dt = datetime.datetime.fromisoformat(clean_show)
        if show_start_dt.tzinfo is None:
            show_start_dt = show_start_dt.replace(tzinfo=tz_vn)
        sim_dt = show_start_dt - datetime.timedelta(minutes=abs_min)
        sim_iso = sim_dt.isoformat(timespec="seconds")
    except Exception:
        sim_iso = datetime.datetime.now(tz_vn).isoformat(timespec="seconds")

    SCHEDULER_STATE["last_simulated_clock"] = sim_iso
    result = await _run_auto_snapshot_for_showtime(
        room_id=clean_room,
        show_id=clean_show,
        trigger_source=trigger_source,
        simulated_clock_iso=sim_iso,
    )
    if result.get("status") == "error":
        return JSONResponse(status_code=404, content=result)
    return result


@app.get("/api/v1/scheduler/status")
def get_scheduler_status_endpoint():
    from database import get_inference_logs
    return {
        "status": "success",
        "scheduler": SCHEDULER_STATE,
        "recent_logs": get_inference_logs(limit=10),
    }

print("[INFO] Đang tải mô hình YOLO...")
try:
    default_model_path = os.path.join(os.path.dirname(__file__), "models", "best_head_v2.pt")
    model_path = os.environ.get("CINESIGHT_MODEL", default_model_path)
    MODEL_CONF = float(os.environ.get("CINESIGHT_CONF", "0.28"))
    MODEL_IMGSZ = int(os.environ.get("CINESIGHT_IMGSZ", "800"))
    model = YOLO(model_path)
    print(f"[OK] Tải mô hình thành công: {model_path} (conf={MODEL_CONF}, imgsz={MODEL_IMGSZ})")
except Exception as e:
    print(f"[LỖI] Không thể tải mô hình YOLO: {e}")
    model = None
    MODEL_CONF = 0.28
    MODEL_IMGSZ = 800


# ---------------------------------------------------------------------------
# Vấn đề 5: FastAPI phục vụ luôn bản build Web Admin (1 cổng duy nhất).
# Đặt SAU toàn bộ route /api/v1/... để route API luôn được ưu tiên.
# ---------------------------------------------------------------------------
if os.path.isdir(os.path.join(WEB_ADMIN_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB_ADMIN_DIST, "assets")), name="admin-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_web_admin(full_path: str):
        if full_path.startswith("api/") or full_path in ("docs", "openapi.json", "redoc"):
            return JSONResponse(status_code=404, content={"error": "Not found"})
        candidate = os.path.abspath(os.path.join(WEB_ADMIN_DIST, full_path))
        if full_path and candidate.startswith(WEB_ADMIN_DIST + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(WEB_ADMIN_DIST, "index.html"))
