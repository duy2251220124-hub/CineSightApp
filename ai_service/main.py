from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import cv2
import numpy as np
import json
from seat_mapper import load_seats_config, process_ai_detections, generate_alerts

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CineSight AI Vision API",
    description="API kiá»ƒm Ä‘áº¿m khÃ¡n giáº£ ráº¡p chiáº¿u phim báº±ng thá»‹ giÃ¡c mÃ¡y tÃ­nh. Há»— trá»£ nhiá»u phÃ²ng chiáº¿u.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

print("[INFO] Äang táº£i mÃ´ hÃ¬nh YOLO...")
try:
    model = YOLO('yolov8n.pt')
    print("[OK] Táº£i model thÃ nh cÃ´ng!")
except Exception as e:
    print(f"[ERROR] KhÃ´ng táº£i Ä‘Æ°á»£c model: {e}")
    model = None


from database import save_tickets, get_tickets

@app.get("/")
def health_check():
    return {"status": "CineSight AI Service Ä‘ang cháº¡y", "version": "2.0.0"}


@app.post("/api/v1/sync_tickets")
def sync_tickets_from_app(
    room_id: str = Form(..., description="MÃ£ phÃ²ng chiáº¿u. VD: room1"),
    scanned_tickets: str = Form(..., description="Danh sÃ¡ch vÃ© tá»« Hive DB. VD: [\"A1\", \"B2\"]")
):
    try:
        tap_A = set(json.loads(scanned_tickets))
        save_tickets(room_id, tap_A)
        print(f"[SYNC] ÄÃ£ nháº­n {len(tap_A)} vÃ© cá»§a phÃ²ng {room_id} tá»« App Mobile.")
        return {"status": "success", "message": f"ÄÃ£ Ä‘á»“ng bá»™ {len(tap_A)} vÃ© cho phÃ²ng {room_id}"}
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "scanned_tickets pháº£i lÃ  JSON array."})

# ----------------------------------------------------------------------
# ENDPOINT 2: DÃ€NH RIÃŠNG CHO CAMERA Ráº P PHIM (Nháº­n áº¢nh -> Táº¡o Táº­p B)
# ----------------------------------------------------------------------
@app.post("/api/v1/analyze")
async def analyze_cinema_room(
    image: UploadFile = File(..., description="áº¢nh chá»¥p tá»« camera CCTV phÃ²ng chiáº¿u"),
    room_id: str = Form(..., description="MÃ£ phÃ²ng chiáº¿u. VD: room1")
):
    # Láº¥y Táº­p A Ä‘Ã£ Ä‘Æ°á»£c App Ä‘á»“ng bá»™ tá»« trÆ°á»›c. Náº¿u chÆ°a cÃ³ thÃ¬ coi nhÆ° rá»—ng.
    tap_A = get_tickets(room_id)

    # Äá»c báº£n Ä‘á»“ gháº¿
    seats_config = load_seats_config(room_id)
    if not seats_config:
        return JSONResponse(
            status_code=404,
            content={"error": f"ChÆ°a cÃ³ báº£n Ä‘á»“ gháº¿ cho phÃ²ng '{room_id}'."}
        )

    # Äá»c áº£nh camera gá»­i lÃªn
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Cháº¡y AI
    detected_heads = []
    if model:
        results = model.predict(img, conf=0.4, classes=[0], verbose=False)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detected_heads.append(((x1 + x2) / 2, (y1 + y2) / 2))

    # Ãnh xáº¡ Táº­p B
    tap_B = process_ai_detections(detected_heads, seats_config)

    # Äá»‘i chiáº¿u
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


