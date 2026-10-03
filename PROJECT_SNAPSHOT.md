# DỮ LIỆU ĐỌC TỪ MÃ NGUỒN DỰ ÁN CINESIGHTAPP
*Snapshot tự động. Mọi bí mật đã bị che (REDACTED).*

## 1. MÔI TRƯỜNG
- **Hệ điều hành:** Microsoft Windows 11 Pro
- **Python:** Python 3.14.3
- **Node:** v24.14.0
- **Flutter:** Flutter 3.47.2 • channel stable
- **Git Branch:** main
- **Git Remote:**
```text
origin  https://github.com/duy2251220124-hub/CineSightApp.git (fetch)
origin  https://github.com/duy2251220124-hub/CineSightApp.git (push)
```

## 2. CÂY THƯ MỤC
*(Cấp 1 đến 3. Đã loại trừ nội dung venv, node_modules, .git, build, .dart_tool, __pycache__)*
```text
C:\CineSightApp
[.agents/] (1 files)
  [rules/]
[.vscode/] (1 files)
  settings.json (0.1 KB)
[ai_service/] (tổng 26966 files - bao gồm venv)
  [calibration_images/] (0 files)
  [datasets/] (0 files)
  [seats_configs/]
    seats_config_room1.json (0 KB)
  calibrate_seats.py (4.4 KB, 95 dòng)
  cinesight.db (12 KB)
  database.py (1 KB, 34 dòng)
  dataset.yaml (0.5 KB)
  main.py (3.7 KB, 87 dòng)
  requirements-lock.txt (1.9 KB)
  requirements.txt (0.1 KB)
  seat_mapper.py (2.1 KB, 53 dòng)
  train.py (1.5 KB, 29 dòng)
  yolov8n.pt (6396.3 KB)
[mobile_app/] (tổng 518 files - bao gồm build/.dart_tool)
  [.idea/]
  [android/]
  [assets/]
    [images/]
  [ios/]
  [lib/]
    [core/]
    [features/]
    [mock/]
    [screens/]
    [theme/]
    [widgets/]
    main.dart (1.2 KB, 36 dòng)
  [linux/]
  [macos/]
  [test/]
  [web/]
  [windows/]
  pubspec.yaml (4 KB)
[ngrok_bin/] (1 files)
  ngrok.exe (32494.8 KB)
[web_admin/] (tổng 866 files - bao gồm node_modules)
  [public/]
  [src/]
    [api/]
    [assets/]
    [pages/]
    [styles/]
    App.jsx (1.6 KB, 44 dòng)
    main.jsx (0.2 KB, 8 dòng)
  package.json (0.5 KB)
  vite.config.js (0.2 KB, 6 dòng)
ngrok.yml (0.1 KB)
ngrok.zip (11970.6 KB)
PROJECT_STATUS_v2.md (8.6 KB)
```

## 3. GIT
**git log --oneline (toàn bộ):**
```text
bccb682 feat(ui): Tích hợp thành công 19 màn hình UI từ Figma, nối toàn bộ luồng điều hướng
9c57b51 Dọn dẹp code rác; Dựng UI Mobile (Theme, Login, Home)
6cf760e Cấu hình CORS, cập nhật URL Ngrok và Vite allowedHosts chuẩn bị cho buổi Demo
dc67942 fix: Resolve CORS, SQLite persistence, and strict dependency lock
b39ac63 Cập nhật tiến độ: Khởi tạo Web Admin (React), Mạng kết nối API, CGV Data Tool và Kiến trúc Đa phòng chiếu
ddaa1e4 Cập nhật Mobile App: Thêm UI Camera và CSDL Offline (Hive)
a372a33 Khởi tạo dự án: Kiến trúc AI Service (FastAPI) và Mobile App (Flutter)
```

**git status --short:**
```text
?? .agents/
?? PROJECT_STATUS_v2.md
```

**Nội dung .gitignore:**
```text
# Ngrok
ngrok.yml
ngrok.zip
ngrok_bin/

# AI Data & Models
*.db
*.pt
*.engine
```

- **Tổng số file đang theo dõi:** 198
- **File đang theo dõi lớn hơn 1MB:** (Không có)

## 4. DEPENDENCY
**ai_service/requirements.txt:**
```text
ultralytics>=8.0.0
opencv-python>=4.8.0
fastapi>=0.100.0
uvicorn>=0.23.0
numpy>=1.24.0
pydantic>=2.0.0

python-multipart
```

**ai_service/requirements-lock.txt (10 dòng đầu):**
```text
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.7.22
charset-normalizer==3.5.1
click==8.5.0
cloudpickle==3.1.2
contourpy==1.4.0
cycler==0.12.1
fastapi==0.141.1
```

**mobile_app/pubspec.yaml:**
```yaml
dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.8
  mobile_scanner: ^7.4.2
  dio: ^5.11.1
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  flutter_riverpod: ^3.4.3
  go_router: ^18.0.1
  google_fonts: ^6.2.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
```

**web_admin/package.json:**
```json
  "dependencies": {
    "axios": "^1.20.0",
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@vitejs/plugin-react": "^6.1.1",
    "oxlint": "^1.81.0",
    "vite": "^8.3.0"
  }
```

## 5. AI_SERVICE

### main.py
```python
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import numpy as np
from database import get_tickets, init_db
from seat_mapper import load_seats_config, process_ai_detections, generate_alerts

app = FastAPI(
    title="CineSight AI Camera API",
    version="2.0.0"
)

# Enable CORS for Web Admin & Mobile App
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'], # Cấu hình tạm thời cho giai đoạn demo,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Database SQLite khi app chạy
init_db()

# ENDPOINT 0: HEALTH CHECK
# ----------------------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "CineSight AI Service đang chạy", "version": "2.0.0"}

# ENDPOINT 1: DÀNH CHO APP KIỂM VÉ CỦA NHÂN VIÊN CGV (Đồng bộ Tập A)
# ----------------------------------------------------------------------
@app.post("/api/v1/sync_tickets")
def sync_tickets_from_app(
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1"),
    scanned_tickets: str = Form(..., description="Mảng JSON chứa các ID vé hợp lệ (Tập A)"),
):
    import json
    try:
        tickets_list = json.loads(scanned_tickets)
        from database import save_tickets
        save_tickets(room_id, set(tickets_list))
        return {"status": "success", "message": f"Đã lưu {len(tickets_list)} vé cho phòng {room_id}"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

# ENDPOINT 2: DÀNH RIÊNG CHO CAMERA RẠP PHIM (Nhận Ảnh -> Tạo Tập B)
# ----------------------------------------------------------------------
@app.post("/api/v1/analyze")
async def analyze_cinema_room(
    image: UploadFile = File(..., description="Ảnh chụp từ camera CCTV phòng chiếu"),
    room_id: str = Form(..., description="Mã phòng chiếu. VD: room1")
):
    # Lấy Tập A đã được App đồng bộ từ trước. Nếu chưa có thì coi như rỗng.
    tap_A = get_tickets(room_id)

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

print("[INFO] Đang tải mô hình YOLO...")
try:
    model = YOLO('yolov8n.pt')
    print("[OK] Tải mô hình thành công.")
except Exception as e:
    print(f"[LỖI] Không thể tải mô hình YOLO: {e}")
    model = None
```
*(Nguyên văn đủ 87 dòng)*

### database.py
```python
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cinesight.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            room_id TEXT,
            ticket_id TEXT,
            PRIMARY KEY (room_id, ticket_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_tickets(room_id: str, tickets: set):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE room_id = ?", (room_id,))
    if tickets:
        cursor.executemany(
            "INSERT INTO tickets (room_id, ticket_id) VALUES (?, ?)",
            [(room_id, t) for t in tickets]
        )
    conn.commit()
    conn.close()

def get_tickets(room_id: str) -> set:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM tickets WHERE room_id = ?", (room_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

init_db()
```
*(Nguyên văn)*

### seat_mapper.py
```python
import cv2
import json
import numpy as np
import os

def load_seats_config(room_id: str):
    """
    Đọc file cấu hình ghế của MỘT PHÒNG CỤ THỂ.
    Mỗi phòng có 1 file JSON riêng trong thư mục seats_configs/
    """
    config_path = f"seats_configs/seats_config_{room_id}.json"
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            data = json.load(f)
            print(f"[OK] Đã tải bản đồ ghế phòng '{room_id}': {len(data)} ghế.")
            return data
    except FileNotFoundError:
        print(f"[-] Chưa có file cấu hình cho phòng '{room_id}'.")
        print(f"    Hãy chạy: python calibrate_seats.py {room_id}")
        return {}

def process_ai_detections(detected_heads, seats_config):
    """
    Ánh xạ tọa độ đầu người (từ YOLO) vào mã ghế cụ thể.
    Dùng thuật toán Point-in-Polygon của OpenCV.
    """
    set_B = set()
    for head in detected_heads:
        head_point = (float(head[0]), float(head[1]))
        for seat_name, polygon in seats_config.items():
            poly_np = np.array(polygon, np.int32)
            is_inside = cv2.pointPolygonTest(poly_np, head_point, False)
            if is_inside >= 0:
                set_B.add(seat_name)
                break
    return set_B

def generate_alerts(set_A: set, set_B: set, room_id: str):
    """Sinh cảnh báo chênh lệch cho 1 phòng chiếu cụ thể."""
    print(f"\n--- BÁO CÁO KIỂM ĐẾM PHÒNG [{room_id.upper()}] ---")
    print(f"Tập A (App soát vé) : {set_A}")
    print(f"Tập B (AI Camera)   : {set_B}")

    khach_lau = set_B - set_A
    khach_vang = set_A - set_B

    if khach_lau:
        print(f"[ĐỎ] Ngồi không có vé tại: {khach_lau}")
    if khach_vang:
        print(f"[VÀNG] Có vé nhưng ghế trống tại: {khach_vang}")
    if not khach_lau and not khach_vang:
        print("[XANH] Tất cả khớp! An toàn chiếu phim.")
    
    return {
        "room_id": room_id,
        "illegal_occupants": list(khach_lau),
        "missing_guests": list(khach_vang),
    }
```
*(Nguyên văn)*

### train.py
```python
from ultralytics import YOLO

def main():
    print("[INFO] Bắt đầu khởi tạo huấn luyện mô hình YOLOv8s...")
    
    # Load mô hình YOLOv8 small pre-trained (cân bằng tốt giữa tốc độ và độ chính xác)
    model = YOLO('yolov8n.pt')
    
    # Bắt đầu quá trình Fine-tune (Huấn luyện lại) trên dữ liệu đầu người ảnh hồng ngoại
    results = model.train(
        data='dataset.yaml',   # Đường dẫn tới file cấu hình dữ liệu
        epochs=50,             # Số vòng lặp huấn luyện (Đồ án nên để 50-100 vòng)
        imgsz=640,             # Kích thước ảnh đầu vào chuẩn của YOLO
        batch=8,               # Số ảnh nạp vào mỗi lần (Hạ xuống 4 nếu máy báo hết RAM)
        name='ir_head_detect', # Tên thư mục lưu kết quả huấn luyện
        # Lưu ý: Nếu máy bạn có Card rời NVIDIA, hãy đổi device='cpu' thành device='0' để chạy siêu tốc.
        device='cpu',
        # Các thông số chống Overfitting cơ bản
        patience=10,           
        save=True
    )
    
    print("\n" + "="*50)
    print("[THÀNH CÔNG] Huấn luyện hoàn tất!")
    print("File weights tốt nhất (model hoàn chỉnh) được lưu tại:")
    print("-> runs/detect/ir_head_detect/weights/best.pt")
    print("Bạn hãy copy file best.pt này, sửa lại trong file main.py thay cho yolov8n.pt nhé!")
    print("="*50)

if __name__ == '__main__':
    main()
```
*(Nguyên văn)*

### dataset.yaml
```yaml
# Cấu hình Dataset cho mô hình YOLO Head Detection (Camera Hồng ngoại)

# Đường dẫn gốc tới thư mục chứa dữ liệu
path: ./datasets 
train: images/train  # Ảnh dùng để huấn luyện
val: images/val      # Ảnh dùng để kiểm thử (đánh giá độ chính xác)

# Số lượng class (Chỉ có 1 mục tiêu duy nhất là cái đầu của khán giả)
nc: 1

# Tên của các class tương ứng với ID (ID 0)
names:
  0: head
```
*(Nguyên văn)*

### calibrate_seats.py
- **Docstring:** (Không khai báo docstring ở đầu file)
- **Danh sách hàm:** `click_and_crop(event, x, y, flags, param)`, `main()`
- **30 Dòng đầu:**
```python
import cv2
import json
import numpy as np
import os
import sys

# Biến toàn cục
current_polygon = []
seats_data = {}
image = None
clone = None

def click_and_crop(event, x, y, flags, param):
    global current_polygon, image, clone
    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))
        cv2.circle(image, (x, y), 3, (0, 255, 0), -1)
        if len(current_polygon) > 1:
            cv2.line(image, current_polygon[-2], current_polygon[-1], (0, 255, 0), 2)
        cv2.imshow("Calibration Tool", image)

def main():
    global image, clone, current_polygon, seats_data

    # ================================================================
    # THAY ĐỔI CHÍNH: Nhận tên phòng từ dòng lệnh
    # Chạy bằng lệnh: python calibrate_seats.py room1
    #                 python calibrate_seats.py room2
    #                 python calibrate_seats.py room3
    # ================================================================
```

### seats_config_room1.json
- **Tổng số ghế:** 1
- **Danh sách Key cấp 1:** `"A1"`
- **2 ghế đầu tiên (Nguyên văn):** 
```json
{"A1": [[0,0], [100,0], [100,100], [0,100]]}
```

### Bảng Endpoint
| Method | Path | File:Dòng |
|---|---|---|
| GET | `/` | `ai_service/main.py:30` |
| POST | `/api/v1/sync_tickets` | `ai_service/main.py:34` |
| POST | `/api/v1/analyze` | `ai_service/main.py:48` |

### Thư mục dữ liệu AI
- **datasets/:** 0 file
- **calibration_images/:** 0 file
- **runs/:** KHÔNG TỒN TẠI

## 6. MOBILE_APP

### main.dart (Khai báo route & HomeShell)
```dart
import 'package:flutter/material.dart';

import 'core/database/hive_service.dart';
import 'core/theme/app_theme.dart';
import 'screens/cs_login_screen.dart';
import 'features/home/presentation/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await HiveService.init();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CineSight',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      home: Builder(
        builder: (ctx) => CSLoginScreen(
          onLogin: () {
            Navigator.pushReplacement(
              ctx,
              MaterialPageRoute(builder: (_) => const HomeShell()),
            );
          },
        ),
      ),
    );
  }
}
```

### api_client.dart
```dart
import 'package:dio/dio.dart';
import 'dart:convert';

class ApiClient {
  // Lưu ý: Nếu chạy máy ảo Android, dùng 'http://10.0.2.2:8000'
  // Nếu cắm điện thoại thật, dùng IP của máy tính (VD: 'http://192.168.1.15:8000')
  static const String baseUrl = 'https://quill-device-deny.ngrok-free.dev';
  
  static final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 3),
  ));

  /// Hàm đóng gói danh sách vé quét được bắn lên AI Server
  static Future<bool> syncTicketsToServer(String roomId, List<String> tickets) async {
    try {
      final formData = FormData.fromMap({
        'room_id': roomId,
        'scanned_tickets': jsonEncode(tickets),
      });
      
      final response = await _dio.post('/api/v1/sync_tickets', data: formData);
      
      if (response.statusCode == 200) {
        print('[NETWORK] Đồng bộ thành công ${tickets.length} vé cho phòng $roomId');
        return true;
      }
      return false;
    } catch (e) {
      print('[NETWORK] Lỗi đồng bộ: $e');
      return false;
    }
  }
}
```
*(Nguyên văn)*

### hive_service.dart
```dart
import 'package:hive_flutter/hive_flutter.dart';

class HiveService {
  static const String _ticketBoxName = 'scanned_tickets_box';

  /// Khởi tạo Hive Database (Chạy 1 lần duy nhất khi mở App)
  static Future<void> init() async {
    // Khởi tạo engine lưu trữ trên điện thoại
    await Hive.initFlutter();

    // Mở một cái "Hộp" (Bảng) để chứa danh sách vé
    await Hive.openBox<String>(_ticketBoxName);
  }

  /// Hàm lưu mã vé vừa quét vào bộ nhớ máy (Dành cho lúc rớt mạng)
  static Future<void> saveScannedTicket(String ticketCode) async {
    final box = Hive.box<String>(_ticketBoxName);

    // Thuật toán chống lưu trùng lặp: Nếu trong máy chưa có vé này thì mới lưu
    if (!box.values.contains(ticketCode)) {
      await box.add(ticketCode);
      print('[HIVE] Đã lưu vé $ticketCode vào bộ nhớ Offline thành công!');
    }
  }

  /// Lấy danh sách toàn bộ vé đang lưu trong máy để chuẩn bị đẩy lên AI Server
  static List<String> getAllScannedTickets() {
    final box = Hive.box<String>(_ticketBoxName);
    return box.values.toList();
  }

  /// Xóa toàn bộ vé trong máy SAU KHI đã đồng bộ lên mạng thành công
  static Future<void> clearTicketsAfterSync() async {
    final box = Hive.box<String>(_ticketBoxName);
    await box.clear();
    print('[HIVE] Đã dọn dẹp bộ nhớ Offline sau khi đồng bộ!');
  }
}
```
*(Nguyên văn)*

### scanner_screen.dart (Các dòng import và gọi)
- Dòng 2: `import 'package:mobile_scanner/mobile_scanner.dart';`
- Dòng 7: `import '../../../core/database/hive_service.dart';`
- Dòng 46: `await HiveService.saveScannedTicket(code);`
- Dòng 61: `body: MobileScanner(`
*(Không có dòng nào import hoặc gọi `ApiClient`)*

### Bảng các màn hình trong `lib/screens`

| Tên File | Tên Class | Gọi từ (Route) | Dùng Mock Data? |
|---|---|---|---|
| `cs_add_incident_screen.dart` | `CSAddIncidentScreen` | `home_screen.dart:73` | CÓ |
| `cs_damaged_seat_screen.dart` | `CSDamagedSeatScreen` | `home_screen.dart:66` | CÓ |
| `cs_handover_screen.dart` | `CSHandoverScreen` | `home_screen.dart:92` | CÓ |
| `cs_home_screen.dart` | `CSHomeScreen` | `home_screen.dart:39` | CÓ |
| `cs_incident_detail_screen.dart`| `CSIncidentDetailScreen` | **MỒ CÔI** (Chỉ import tại `home_screen.dart:17` nhưng không gọi) | CÓ |
| `cs_login_screen.dart` | `CSLoginScreen` | `main.dart:28` | CÓ |
| `cs_notification_screen.dart` | `CSNotificationScreen` | `home_screen.dart:98` | CÓ |
| `cs_offline_screen.dart` | `CSOfflineScreen` | `home_screen.dart:139` | CÓ |
| `cs_rooms_screen.dart` | `CSRoomsScreen` | `home_screen.dart:104` | CÓ |
| `cs_scan_history_screen.dart` | `CSScanHistoryScreen` | `scanner_screen.dart:58` | CÓ |
| `cs_scan_screen.dart` | `CSScanScreen` | `home_screen.dart:45` | CÓ |
| `cs_scan_success_screen.dart` | `CSScanSuccessScreen` | `cs_scan_result_view.dart:28` | CÓ |
| `cs_scan_used_screen.dart` | `CSScanUsedScreen` | `cs_scan_result_view.dart:29` | CÓ |
| `cs_scan_wait_screen.dart` | `CSScanWaitScreen` | `cs_scan_result_view.dart:30` | CÓ |
| `cs_seat_map_screen.dart` | `CSSeatMapScreen` | `home_screen.dart:122` | CÓ |
| `cs_settings_screen.dart` | `CSSettingsScreen` | `home_screen.dart:126` | CÓ |
| `cs_showtimes_screen.dart` | `CSShowtimesScreen` | `home_screen.dart:82` | CÓ |
| `cs_warning_detail_screen.dart` | `CSWarningDetailScreen`| `home_screen.dart:112` | CÓ |
| `cs_warning_screen.dart` | `CSWarningScreen` | `home_screen.dart:118` | CÓ |

### Kết quả `flutter analyze`
```text
Analyzing mobile_app...                                         

   info - Don't invoke 'print' in production code. Try using a logging framework - lib\core\database\hive_service.dart:22:7 - avoid_print
   info - Don't invoke 'print' in production code. Try using a logging framework - lib\core\database\hive_service.dart:36:5 - avoid_print
   info - Don't invoke 'print' in production code. Try using a logging framework - lib\core\network\api_client.dart:26:9 - avoid_print
   info - Don't invoke 'print' in production code. Try using a logging framework - lib\core\network\api_client.dart:31:7 - avoid_print
warning - Unused import: '../../../screens/cs_incident_detail_screen.dart'. Try removing the import directive - lib\features\home\presentation\home_screen.dart:17:8 - unused_import

5 issues found. (ran in 7.0s)
```

## 7. WEB_ADMIN

### package.json
```json
{
  "name": "web_admin",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "oxlint",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.20.0",
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@vitejs/plugin-react": "^6.1.1",
    "oxlint": "^1.81.0",
    "vite": "^8.3.0"
  }
}
```

### vite.config.js
```javascript
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()], server: { allowedHosts: true },
})
```

### cineSightApi.js
```javascript
import axios from 'axios';

// Khi deploy thực tế, đổi thành IP máy chủ AI
const API_BASE = 'https://quill-device-deny.ngrok-free.dev';

const api = axios.create({ baseURL: API_BASE });

export const analyzeRoom = async (roomId, imageFile) => {
  const formData = new FormData();
  formData.append('room_id', roomId);
  formData.append('image', imageFile);
  const res = await api.post('/api/v1/analyze', formData);
  return res.data;
};

export const healthCheck = async () => {
  const res = await api.get('/');
  return res.data;
};
```

### Dashboard.jsx (Ngữ cảnh)
```jsx
// Dòng 1-10:
import { useState, useEffect } from 'react';
import { analyzeRoom, healthCheck } from '../api/cineSightApi';
import '../styles/dashboard.css';

// Dữ liệu mẫu cảnh báo (sẽ thay bằng API thực tế sau)
const MOCK_ALERTS = [
  { id: 1, room: 'IMAX (room1)', seat: 'C4', type: 'illegal', time: '19:02:14', show: 'Avengers 5 - 19:00' },
  { id: 2, room: '2D (room2)', seat: 'A7', type: 'missing', time: '19:05:31', show: 'Inside Out 3 - 19:00' },
  { id: 3, room: '4DX (room3)', seat: 'B2', type: 'illegal', time: '19:07:05', show: 'Moana 2 - 19:00' },
];

// Dòng 15-25 (useEffect):
  useEffect(() => {
    const check = async () => {
      try {
        await healthCheck();
        setServerOnline(true);
      } catch {
        setServerOnline(false);
      }
    };
    check();
  }, []);

// Dòng 35-45 (analyzeRoom):
  const handleAnalyze = async () => {
    if (!imageFile) return alert('Hãy chọn một bức ảnh từ camera!');
    setIsAnalyzing(true);
    setResult(null);
    try {
      const data = await analyzeRoom(selectedRoom, imageFile);
      setResult(data);
    } catch (e) {
      setResult({ error: e.message });
    }
    setIsAnalyzing(false);
  };

// Dòng 50-60 (MOCK_ALERTS Render):
  const illegalCount = MOCK_ALERTS.filter(a => a.type === 'illegal').length;
  const missingCount = MOCK_ALERTS.filter(a => a.type === 'missing').length;
...
          <tbody>
            {MOCK_ALERTS.map(a => (
              <tr key={a.id}>
                <td style={{ color: '#888' }}>{a.time}</td>
                <td>{a.show}</td>
                <td>{a.room}</td>
```

## 8. HẠ TẦNG MẠNG
**ngrok.yml (ĐÃ CHE):**
```yaml
version: "3"
agent:
  authtoken: ***REDACTED*** 
tunnels:
  backend:
    proto: http
    addr: 8000
```
- **Tiến trình ngrok:** KHÔNG TỒN TẠI (Lệnh `Get-Process ngrok` trả về rỗng).
- **URL cố định:** Cả `api_client.dart` và `cineSightApi.js` đều chứa `https://quill-device-deny.ngrok-free.dev`.

## 9. MEDIA/DỮ LIỆU
*Toàn bộ ảnh/video tìm thấy trong dự án:*
```text
C:\CineSightApp\mobile_app\android\app\src\main\res\mipmap-hdpi\ic_launcher.png (3.4 KB)
C:\CineSightApp\mobile_app\android\app\src\main\res\mipmap-mdpi\ic_launcher.png (2.2 KB)
C:\CineSightApp\mobile_app\android\app\src\main\res\mipmap-xhdpi\ic_launcher.png (4.8 KB)
C:\CineSightApp\mobile_app\android\app\src\main\res\mipmap-xxhdpi\ic_launcher.png (7.5 KB)
C:\CineSightApp\mobile_app\android\app\src\main\res\mipmap-xxxhdpi\ic_launcher.png (10.4 KB)
C:\CineSightApp\mobile_app\assets\images\logo.png (18.1 KB)
C:\CineSightApp\web_admin\src\assets\hero.png (256.3 KB)
... và khoảng 35 file icon mặc định khác của hệ thống Flutter template (AppIcon/LaunchImage)
KHÔNG TỒN TẠI file .mp4, .avi nào.
```

## 10. QUÉT BÍ MẬT
*(Bí mật duy nhất được phát hiện bằng lệnh grep)*
- Cụm từ bị bắt: `password`, được dùng dưới dạng biến local cho UI (`_obscurePassword`, `onChangePassword`).
- File liên quan:
  - `mobile_app/lib/features/auth/presentation/login_screen.dart`
  - `mobile_app/lib/features/home/presentation/home_screen.dart`
  - `mobile_app/lib/screens/cs_login_screen.dart`
  - `mobile_app/lib/screens/cs_settings_screen.dart`
- Không phát hiện API_KEY, SECRET hay AUTHTOKEN nào bị leak trong git.
- **Lịch sử ngrok.yml:** Lệnh `git log --all --oneline -- ngrok.yml` trả về rỗng (File chưa từng được commit).

---
### KHÔNG ĐỌC ĐƯỢC / LỖI LỆNH
*(Không có lệnh nào lỗi gây mất dữ liệu)*
