# BÁO CÁO TIẾN TRÌNH DỰ ÁN CINESIGHT (Ngày 04/10/2026)

## 1. PHẦN 1: CÁC VIỆC ĐÃ GIAO Ở LẦN TRƯỚC
| Việc đã giao | Trạng thái | Bằng chứng (Tệp : Dòng / Output) |
| :--- | :--- | :--- |
| **Race condition Hive** (`clearTicketsAfterSync`) | **ĐÃ XONG** | `lib/core/database/hive_service.dart:18-20` sử dụng `await box.deleteAll(keysToDelete);` chỉ xóa đúng mảng key đã đối chiếu. Đã loại bỏ `box.clear()`. |
| **Thêm `date`, `roomId` vào `CSMockMovie`** | **ĐÃ XONG** | `lib/mock/mock_data.dart:6-7` chứa `final String roomId;` và `final String date;`. Không còn lỗi undefined_getter. |
| **Chạy `flutter analyze`** | **ĐÃ CHẠY THẬT** | Output lệnh: `No issues found! (ran in 103.4s)`. 7 issues cảnh báo lần trước đã hết. |
| **Tìm `CSScanScreen`** | **ĐÃ CHỨNG MINH LÀ MỒ CÔI** | Grep `CSScanScreen` chỉ tìm thấy nơi định nghĩa bên trong chính nó (`screens/cs_scan_screen.dart`), tuyệt đối không có nơi nào khác `import` hoặc gọi tới nó. |
| **Màn hình kết quả nhận data thật từ QR** | **ĐÃ XONG** | `features/scanner/presentation/scanner_screen.dart` (dòng 248): `_showResultBottomSheet('${data["ticket"] ?? "KHÔNG RÕ"}', seat: '${data["seat"] ?? ""}', ...)` - Data được trích xuất thẳng từ chuỗi quét được. |
| **Test end-to-end bằng 4 mã QR mẫu** | **CHƯA BẮT ĐẦU** | Chưa có log hay hành vi nào ghi nhận việc giả lập quét 4 mã QR `valid`, `wrong_room`, `future_show` trong lượt này. |

---

## 2. PHẦN 2: TRẠNG THÁI CÁC HẠNG MỤC CÒN TỒN ĐỌNG
| Hạng mục | Trạng thái | Bằng chứng (Tệp : Dòng / Output) |
| :--- | :--- | :--- |
| **Web Admin render `result` thay vì `MOCK_ALERTS`** | **CHƯA BẮT ĐẦU** | `web_admin/src/pages/Dashboard.jsx` vẫn còn vòng lặp cứng `{MOCK_ALERTS.map(a => ...)}`. Biến `result` thật chỉ được log ra dạng `JSON.stringify`. |
| **Tồn tại file model AI `best.pt` & dữ liệu train/val** | **KHÔNG TỒN TẠI** | Lệnh `Test-Path best.pt` = False. Đếm số lượng file trong thư mục `datasets/images/train` và `val` = 0. |
| **Video mô phỏng rạp chiếu phim (CGV.mp4)** | **KHÔNG TỒN TẠI** | Quét toàn bộ thư mục gốc tìm `*.mp4` và `*.avi` kết quả là mảng rỗng (0 file). |
| **Script `extract_frames.py`, `capture_camera.py`, API `trigger`** | **KHÔNG TỒN TẠI** | Không tìm thấy các file này. (Ghi chú: Đã tồn tại một biến thể khác thay thế tên là `run_camera_client.py` nhưng bản thiết kế cũ chưa được đáp ứng). Không có API `trigger_capture` trong `main.py`. |
| **`tools/make_qr.py` nhận tham số động (--date, --show)** | **CHƯA BẮT ĐẦU** | File `make_qr.py` không import `argparse`, vẫn đang gán cứng mảng 4 object: `samples = [{'filename': 'valid_ticket_1.png', 'data': {...}}]` ở dòng 9. |
| **Dọn cấu trúc thư mục trùng lặp trong `lib/`** | **ĐANG LÀM DỞ** | Tồn tại song song cả `screens/cs_login_screen.dart` lẫn `features/auth/presentation/login_screen.dart`. Tương tự với `theme/app_theme.dart` và `core/theme/app_theme.dart`. Hiện tại `main.dart` đang import xài bản cũ. 2 file kia là file thừa chưa bị dọn. |

---

## 3. PHẦN 3: KIỂM TRA MỚI — NGUY CƠ BỊ THỤT LÙI (REGRESSION)
* **BỊ THỤT LÙI**: **KHÔNG CÓ HẠNG MỤC NÀO BỊ THỤT LÙI**.
* Logic cảnh báo 3 lỗi (`illegal_occupants`, `missing_guests`, `over_capacity`) vẫn được duy trì nguyên vẹn ở `seat_mapper.py` dòng 68.
* Logic chuẩn hóa ghế `normalize_seat()` không bị xóa, vẫn được áp dụng ở `main.py` dòng 42 cho luồng App và `seat_mapper.py` dòng 32 cho luồng Camera.
* Đường dẫn `seats_configs` vẫn được bảo toàn sử dụng hàm tuyệt đối `os.path.join(os.path.dirname(__file__), ...)` chống sập đường dẫn.
* Git đã ghi nhận 5 commits giải quyết gọn gàng các lỗi của buổi trước (`mock_data`, `ngrok-skip-browser`, `alert endpoints`).

---

## 4. ƯU TIÊN LÀM TIẾP THEO (THEO THỨ TỰ THỐNG NHẤT)
1. Tải datasets, huấn luyện model YOLO để sinh ra `best.pt` (Nhận diện ghế/người).
2. Test dứt điểm end-to-end trên mobile app với 4 mã QR mẫu (Chạy kiểm thử).
3. Đưa ảnh phòng chiếu thật vào để hiệu chuẩn `seats_configs` thay cho cái ghế `A1` giả hiện tại.
4. Triển khai script bóc tách frame/camera theo đúng thiết kế (extract / capture_camera) hoặc hoàn chỉnh module liên quan.
5. Cập nhật `Dashboard.jsx` bên Web Admin để parse kết quả từ `/api/v1/alerts` thay vì mảng mock cứng.
6. Xóa sổ các file mồ côi và folder trùng lặp bên Mobile App (`screens/`, `theme/`).

---

## 5. CHƯA XÁC NHẬN ĐƯỢC
Không có lệnh nào bị lỗi trong lượt quét này, mọi thông tin đều được đọc từ mã nguồn thực tế và hiển thị kết quả truy xuất thành công.

---
**KẾT LUẬN CUỐI CÙNG:** ĐÃ LÀM, ĐÃ XÁC NHẬN (có output quét source code). Chờ quyết định tiếp theo từ user.
