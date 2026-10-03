# BÁO CÁO TRẠNG THÁI DỰ ÁN CINESIGHTAPP (V3)
*Dựa trên việc kiểm chứng thực thi LIVE (chạy thật) thay vì chỉ quét file.*

## 1. PHÂN TÍCH THEO 5 NHÓM CÔNG NGHỆ

| Nhóm | Hạng mục | Nhãn trạng thái | Bằng chứng | Kiểm chứng lượt này (LIVE) |
|---|---|---|---|---|
| **Mobile App** | Tình trạng Code & Routing | ĐÃ VIẾT, CHƯA TEST | `HomeShell` trỏ tới `ScannerScreen()` (trong features) thay vì `CSScanScreen()` (của Figma mock). | ĐÃ XÁC NHẬN (Grep file) |
| | Nút Demo Quét | KHÔNG TỒN TẠI | Không tìm thấy bất kỳ nút "Demo" nào trong các file ở `lib/screens`. | ĐÃ XÁC NHẬN (Grep chữ "Demo" trả về rỗng) |
| | Logic Scanner | ĐÃ VIẾT, CHƯA TEST | Giá trị `code` lưu vào Hive là chuỗi QR thô, không được bóc tách: `final String code = barcodes.first.rawValue ?? '';` | ĐÃ XÁC NHẬN |
| **Backend & Web Admin**| Tình trạng UI React | ĐÃ VIẾT, CHƯA TEST | `Dashboard.jsx` có gọi API thật. State `result` có được render dưới dạng JSON thô ở dòng 102 (`{JSON.stringify(result, null, 2)}`). Tuy nhiên, bảng cảnh báo vẫn dùng `MOCK_ALERTS`. | ĐÃ XÁC NHẬN |
| | API `/` | ĐÃ CHẠY THẬT | Status 200, Body: `{"status":"CineSight AI Service đang chạy","version":"2.0.0"}` | ĐÃ CHẠY LỆNH |
| | API `/api/v1/sync_tickets` | ĐÃ CHẠY THẬT | Gọi với `["T1","T2"]`, DB lưu T1, T2. Gọi tiếp `["T3"]`, DB **chỉ còn T3** (Vé cũ bị xóa hoàn toàn). | ĐÃ CHẠY LỆNH (DB Query) |
| | API `/api/v1/analyze` | ĐÃ CHẠY THẬT | Gửi ảnh giả (`np.zeros` sinh bằng OpenCV, không đánh giá độ chính xác của AI). API trả về Status 200. Summary: `tap_A_from_app: ["T3"]`, `tap_B_from_camera: []`, Alerts: `missing_guests: ["T3"]`. | ĐÃ CHẠY LỆNH |
| | Đường dẫn thư mục AI | LỖI LOGIC | Tắt server, bật lại bằng `uvicorn ai_service.main:app` từ thư mục gốc, server lập tức **CRASH**. | ĐÃ CHẠY LỆNH (Lỗi `ModuleNotFoundError: No module named 'seat_mapper'`) |
| **Hệ thống AI (YOLO)** | Load Model YOLO | ĐÃ VIẾT, CHƯA TEST | Code trỏ về `yolov8n.pt`. Chưa có model fine-tune (`best.pt`). | (Đã quét ở V2) |
| | Tọa độ ghế (Seat Mapper) | ĐÃ VIẾT, CHƯA TEST | Tọa độ giả, lưới đều. | (Đã quét ở V2) |
| **Dữ liệu & CSDL** | CSDL Server SQLite | ĐÃ CHẠY THẬT | Hoạt động, nhưng logic DELETE toàn bộ trước khi INSERT. | ĐÃ CHẠY LỆNH (Test sync_tickets) |
| | Dữ liệu Video Camera | KHÔNG TỒN TẠI | 0 video. | (Đã quét ở V2) |
| **Huấn luyện AI** | Dataset & Model | MỚI LÀ KẾ HOẠCH | 0 ảnh trong train/val. | (Đã quét ở V2) |

---

## 2. THAY ĐỔI SO VỚI BÁO CÁO V2

*   **API AI Service (`/`, `/api/v1/sync_tickets`, `/api/v1/analyze`):** Nâng cấp từ "ĐÃ VIẾT, CHƯA TEST" lên **"ĐÃ CHẠY THẬT"**. Tôi đã bật server uvicorn (PID 22888) và gọi lệnh test thành công, trả về JSON chính xác. 
*   **Web Admin Dashboard:** Bổ sung bằng chứng: UI thực sự có in log JSON thật của `analyzeRoom` ra màn hình, không chỉ gọi ngầm.

---

## 3. CÁC HẠNG MỤC "HOÃN / TÙY CHỌN / NGOÀI PHẠM VI"
*   **WebSockets:** Hạng mục HOÃN (dùng Polling).
*   **Tiền xử lý CLAHE:** Hạng mục TÙY CHỌN.
*   **Thời điểm chụp tắt đèn:** Không áp dụng, AI sẽ chụp lúc T-3 đến T-5 đèn sáng.
*   **PostgreSQL / MySQL:** KHÔNG DÙNG, chốt dùng SQLite.
*   **Camera:** Nguồn ảnh là video CGV phát lại, không phải điện thoại.
*   **Nhóm màn hình Sự cố (Out of scope):** CSDamagedSeatScreen, CSAddIncidentScreen... chỉ được làm khi còn dư thời gian.

---

## 4. VẤN ĐỀ LOGIC ĐÃ PHÁT HIỆN (CRITICAL)

1.  **Tập A/B Lệch loại dữ liệu:** App quét QR vé ra ID vé thô (VD: `T1`), nhưng Seat Mapper lại lấy mã ghế (VD: `A1`). Khi gộp đối chiếu, AI luôn báo lệch vì vé `T1` không khớp với ghế `A1`. Bắt buộc phải parse chuỗi QR ra ghế, hoặc server phải tra bảng ánh xạ vé->ghế.
2.  **Sync xóa vé cũ:** API `/api/v1/sync_tickets` dùng câu lệnh `DELETE FROM tickets WHERE room_id = ?` trước khi `INSERT`. Hậu quả: nhân viên A quét 2 vé, nhân viên B quét tiếp 1 vé đẩy lên, kết quả trên Server chỉ còn 1 vé của người B. Phải đổi logic sang gộp (append) thay vì ghi đè.
3.  **Đường dẫn tương đối sai lệch:** `main.py` dùng `from seat_mapper import...`. Nếu chạy lệnh uvicorn từ bên ngoài thư mục `ai_service`, code lập tức văng lỗi không tìm thấy thư viện.
4.  **Thiếu cảnh báo vượt sức chứa (Overcapacity):** Thuật toán chỉ trừ set `B - A` và `A - B`. Giả sử ghế `A1` có 1 vé nhưng có tới 2 đầu người xếp chồng/bế nhau (hoặc số lượng người phát hiện lớn hơn tổng ghế cấu hình), hệ thống không có hàm cảnh báo rạp bị quá tải.

---

## 5. DANH SÁCH "VIỆC CÒN THIẾU" (Theo ưu tiên lõi)

1.  **Dataset và fine-tune model:** (Chờ dài nhất). Quay video CGV, viết `extract_frames.py`, gán nhãn class "head", train ra `best.pt`. 
2.  **Sửa lỗi Logic & Nối UI với API thật:** Vá lỗi lệch loại dữ liệu (QR parse), sửa logic `DELETE` của sync API, thay `MOCK_ALERTS` trên Dashboard.
3.  **Hiệu chuẩn ghế thật (Calibration):** Thay tọa độ lưới vuông giả bằng đa giác thật từ một góc camera phòng chiếu cụ thể.
4.  **Capture_camera & trigger_capture:** Tạo vòng lặp replay video và API ra lệnh chụp.
5.  **Cải thiện UI phụ / Tùy chọn:** Màn hình sự cố, CLAHE, Websockets.

---

## 6. CÁC MỤC CHƯA XÁC NHẬN ĐƯỢC

*   **Chất lượng dự đoán của mô hình YOLOv8n:** Dù endpoint `/api/v1/analyze` đã chạy ra JSON (với ảnh đen giả), nhưng chưa có ảnh rạp thật để khẳng định YOLOv8n đếm ra bao nhiêu cái đầu trong góc độ hẹp của rạp chiếu.

---

## 7. ĐỀ CƯƠNG BẢN ĐỒ TƯ DUY (Dành cho NotebookLM)

*   Phát triển Mobile App
    *   Flutter UI Layout (ĐÃ VIẾT, CHƯA TEST)
    *   Quét mã QR & Lưu Offline (ĐÃ CHẠY THẬT)
    *   Gửi API Đồng bộ (ĐÃ VIẾT, CHƯA TEST - Chưa nối UI)
*   Hệ thống AI (AI Service)
    *   Logic API FastAPI & SQLite (ĐÃ CHẠY THẬT)
    *   Thuật toán đếm & đối soát Set A/B (ĐÃ CHẠY THẬT - Có lỗi logic)
    *   Model YOLO Head Detection (ĐÃ VIẾT, CHƯA TEST - Đang dùng yolov8n)
    *   Hiệu chuẩn ghế (ĐÃ VIẾT, CHƯA TEST - Data giả)
    *   Script lấy luồng Video (MỚI LÀ KẾ HOẠCH)
*   Hệ thống Web Admin
    *   Dashboard React (ĐÃ VIẾT, CHƯA TEST - Có hiển thị log JSON, báo cáo ảo)
    *   Kết nối API thật (ĐÃ CHẠY THẬT - Tích hợp gọi ngầm)
*   Công cụ Huấn luyện & Data
    *   Script Train YOLO (ĐÃ VIẾT, CHƯA TEST)
    *   Dữ liệu ảnh rạp (KHÔNG TỒN TẠI)
*   Ngoài phạm vi / Đã hoãn
    *   WebSockets (Hoãn)
    *   CLAHE (Tùy chọn)
    *   Postgres/MySQL (Không dùng)
