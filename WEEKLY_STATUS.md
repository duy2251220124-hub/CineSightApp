# BÁO CÁO TRẠNG THÁI DỰ ÁN (QUÉT TRỰC TIẾP TRÊN ĐĨA)

## 1. DANH SÁCH "ĐANG LÀM / ĐÃ XONG"

### PHẦN 1: AI SERVICE
* **Server khởi động:** [ĐÃ CHẠY THẬT] Lệnh `uvicorn main:app --app-dir ai_service --port 8011` đã khởi động thành công (output: `Application startup complete`). Gửi POST `/api/v1/sync_tickets` thành công HTTP 200 OK.

* **API `sync_tickets`:** [ĐÃ VIẾT, CHƯA TEST] Hàm nhận `room_id: str`, `show_id: str`, `scanned_tickets: str`.

* **API `analyze`:** [ĐÃ VIẾT, CHƯA TEST] Đã nhận đủ `show_id: str`. `tap_A` được lấy từ hàm `get_seats(room_id, show_id)`.

* **Hàm `generate_alerts`:** [ĐÃ VIẾT, CHƯA TEST] Đã có đủ 3 loại cảnh báo: Khách ngồi lậu (`khach_lau = set_B - set_A`), Khách vắng (`khach_vang = set_A - set_B`), Vượt sức chứa (`over_capacity = len(set_B) > total_seats`).

* **Đường dẫn `seats_configs`:** [ĐÃ VIẾT, CHƯA TEST] Đã dùng đường dẫn tuyệt đối: `os.path.join(os.path.dirname(__file__), "seats_configs", f"seats_config_{room_id}.json")`.

* **Hàm `normalize_seat()`:** [ĐÃ VIẾT, CHƯA TEST] Đã viết trong `seat_mapper.py`. Đã được gọi khi tải file config (`{normalize_seat(k): v for k, v in data.items()}`) và khi sync vé (`t['seat'] = normalize_seat(t['seat'])`).

* **Load Model:** [ĐÃ VIẾT, CHƯA TEST] Đang load model mặc định: `os.path.join(os.path.dirname(__file__), 'yolov8n.pt')`.

* **Requirements:** [ĐÃ XÁC NHẬN] Các thư viện cốt lõi (`ultralytics`, `opencv-python`, `fastapi`, v.v.) và `python-multipart` đều có mặt trong `requirements.txt`.

### PHẦN 2: MOBILE APP
* **Tab Quét Vé:** [ĐÃ VIẾT, CHƯA TEST] HomeShell (file `home_screen.dart`) đang điều hướng tới bản thật: `ScannerScreen(roomId: _selectedMovie.roomId, showId: _currentShowId)`.
* **`scanner_screen.dart`:** [ĐÃ VIẾT, CHƯA TEST] Đã parse 4 field (`ticket, room, seat, show`). Đã đủ 4 bước kiểm tra (lỗi cú pháp, sai phòng, sai suất, vé đã quét).
* **Gọi API Sync:** [ĐÃ VIẾT, CHƯA TEST] Đã thêm code gọi: `ApiClient.syncTicketsToServer(widget.roomId, widget.showId)` ngay sau khi lưu Hive.
* **`make_qr.py`:** [ĐĐ CHẠY THẬT] Có trên đĩa, ngày sinh QR khớp tuyệt đối Phương án A: `2026-09-29T19:30`.
* **`flutter analyze`:** [ĐÃ CHẠY THẬT] Quét ra 7 issues: 4 `avoid_print`, 2 `undefined_getter` (lỗi không tìm thấy `date` và `roomId` trên lớp `CSMockMovie` trong `home_screen.dart`), 1 `unnecessary_brace`.

### PHẦN 4: HẠ TẦNG
* **Git:** [ĐÃ CHẠY THẬT] Commit gần nhất `bccb682`. Đang có nhiều file modified chưa commit (`main.py`, `scanner_screen.dart`, `Dashboard.jsx`, v.v.).
* **Virtual Env (Venv):** [ĐÃ CHẠY THẬT] Pip trả về thư viện nằm đúng trong `ai_service\venv\Lib\site-packages`.

---

## 2. DANH SÁCH "CHƯA LÀM" (Xếp theo mức ảnh hưởng)

1. **`best.pt` Model:** [KHÔNG TỒN TẠI] Model đã train bằng dữ liệu thật của rạp chiếu phim không tồn tại trên đĩa.
2. **Dataset:** [KHÔNG TỒN TẠI] Không có file ảnh nào trong thư mục `datasets/images/train` và `val` (số lượng đếm được = 0). Cũng không có bất kỳ file video `.mp4`/`.avi` nào trong toàn bộ dự án.
3. **Web Admin Dashboard:** [MỚI LÀ KẾ HOẠCH] Dù API đã sửa, nhưng `Dashboard.jsx` vẫn đang sử dụng mảng cứng `MOCK_ALERTS` để vẽ bảng thay vì render kết quả biến `result` từ API. (Code: `{MOCK_ALERTS.map(a => ...}`).
4. **Trigger Camera & Cron Job:** [KHÔNG TỒN TẠI] Các file `extract_frames.py` và `capture_camera.py` không có mặt trên hệ thống. 
5. **Cải thiện độ sáng (CLAHE):** [KHÔNG TỒN TẠI] Không tìm thấy từ khóa `clahe` hay thuật toán tối ưu ảnh trong thư mục `ai_service`.
6. **Màn hình CSIncidentDetailScreen:** [KHÔNG TỒN TẠI] Không tồn tại màn hình mồ côi này trong toàn bộ thư mục lib.

---

## 3. DANH SÁCH "ĐÃ SỬA SO VỚI LẦN QUÉT TRƯỚC"

* **Lệch Tập A/B:** ĐÃ SỬA. Cả hai tập đều dùng `normalize_seat()` ra chuẩn chung chữ + 2 chữ số (VD: `C04`).
* **Đường dẫn tương đối `seats_configs`:** ĐÃ SỬA. Đã thành đường dẫn tuyệt đối bằng `__file__`.
* **ScanScreen giả vs thật:** ĐÃ SỬA. App đang gọi vào giao diện chức năng camera thật (`ScannerScreen`).
* **show_id DateTime.now() vs field date:** ĐÃ SỬA. Dùng giá trị `date` từ JSON thay vì lấy giờ hiện tại.
* **Xóa toàn bộ Hive khi Sync (Race Condition):** CÒN NGUYÊN VẤN ĐỀ. Trong `hive_service.dart`, hàm `clearTicketsAfterSync()` vẫn gọi lệnh `await box.clear();` để xóa sạch toàn bộ DB, nguy cơ mất vé nếu người dùng đang quét tiếp trong lúc sync.

---

## 4. MỤC "CHƯA XÁC NHẬN ĐƯỢC"
* **Ngrok Process:** KHÔNG XÁC ĐỊNH ĐƯỢC. Lệnh `Get-Process ngrok` báo lỗi object not found, có thể ngrok đang không chạy trên máy của bạn (nhưng URL `quill-device-deny.ngrok-free.dev` vẫn đang được gán cứng trong code).

---
ĐÃ LÀM (Các lệnh đã chạy trên Terminal Windows), ĐÃ XÁC NHẬN (bằng chứng có trong Báo cáo), CẦN TÔI QUYẾT ĐỊNH (Bạn muốn khắc phục 2 lỗi thiếu biến `date` trong `flutter analyze` hay xóa race condition của `hive` trước?).
