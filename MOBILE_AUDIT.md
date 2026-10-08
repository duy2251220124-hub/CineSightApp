import json

with open('audit_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Hardcoded data from previous analysis
audit_content = """# MOBILE_AUDIT.md - Báo cáo Phân tích Cấu trúc App CineSight (Mobile)

## 1. PHÂN LOẠI TOÀN BỘ FILE

Dưới đây là danh sách toàn bộ các file `.dart` trong `lib/`. Nhãn được xác định dựa trên việc đồ thị import từ `main.dart` có đi tới file đó không, và class trong file có thực sự được khởi tạo (`ClassName()`) ở file khác không.

| Đường dẫn | Class chính | Nhãn | Gọi từ đâu (Bằng chứng) | Dữ liệu (Mock/Thật) |
|---|---|---|---|---|
| `lib/main.dart` | `MyApp` | ĐANG DÙNG THẬT | Entry point của Flutter | - |
| `lib/core/database/hive_service.dart` | `HiveService` | ĐANG DÙNG THẬT | `main.dart:13`, `api_client.dart:48` | Thật |
| `lib/core/network/api_client.dart` | `ApiClient` | ĐANG DÙNG THẬT | `cs_home_screen.dart:39`, `cs_login_screen.dart:187` | Thật |
| `lib/core/theme/app_theme.dart` | `AppTheme` | ĐANG DÙNG THẬT | `main.dart:27` | - |
| `lib/core/utils/show_id_utils.dart` | - | ĐANG DÙNG THẬT | `cs_home_screen.dart` (import utils) | - |
| `lib/core/utils/time_format.dart` | - | ĐANG DÙNG THẬT | `cs_home_screen.dart` (import utils) | - |
| `lib/features/auth/presentation/login_screen.dart` | `LoginScreen` | KHÔNG CÒN DÙNG (ĐÃ BỊ THAY THẾ) | Bị bỏ mồ côi (không ai import) | Không xác định |
| `lib/features/home/presentation/home_screen.dart` | `HomeShell` | ĐANG DÙNG THẬT | `main.dart:35` | - |
| `lib/features/scanner/presentation/scanner_screen.dart` | `ScannerScreen` | ĐANG DÙNG THẬT | `home_screen.dart:141` | Mock + API + Hive |
| `lib/mock/mock_data.dart` | `CSMockData` | ĐANG DÙNG THẬT | `cs_settings_screen.dart:99`, `cs_offline_screen.dart:39` | Mock |
| `lib/mock/seat_report_store.dart` | `SeatReportStore` | ĐANG DÙNG THẬT | `cs_damaged_seat_screen.dart:37` | Mock |
| `lib/screens/cs_add_incident_screen.dart` | `CSAddIncidentScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:103` | Mock |
| `lib/screens/cs_damaged_seat_screen.dart` | `CSDamagedSeatScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:100` | Mock |
| `lib/screens/cs_handover_screen.dart` | `CSHandoverScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:122` | Mock |
| `lib/screens/cs_home_screen.dart` | `CSHomeScreen` | ĐANG DÙNG THẬT | `home_screen.dart:81` | Thật (ApiClient) + Mock |
| `lib/screens/cs_incident_detail_screen.dart`| `CSIncidentDetailScreen`| ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `cs_handover_screen.dart:113` | Mock |
| `lib/screens/cs_login_screen.dart` | `CSLoginScreen` | ĐANG DÙNG THẬT | `main.dart:31` | Thật (ApiClient) |
| `lib/screens/cs_notification_screen.dart` | `CSNotificationScreen`| ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:129` | Mock |
| `lib/screens/cs_offline_screen.dart` | `CSOfflineScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:174` | Mock |
| `lib/screens/cs_rooms_screen.dart` | `CSRoomsScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:94` | Mock |
| `lib/screens/cs_scan_history_screen.dart` | `CSScanHistoryScreen` | ĐANG DÙNG THẬT | `scanner_screen.dart:298` | Hive (Thật) |
| `lib/screens/cs_seat_map_screen.dart` | `CSSeatMapScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:97` | Mock |
| `lib/screens/cs_settings_screen.dart` | `CSSettingsScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:168` | Mock |
| `lib/screens/cs_showtimes_screen.dart` | `CSShowtimesScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:84` | Mock |
| `lib/screens/cs_warning_detail_screen.dart` | `CSWarningDetailScreen`| ĐANG DÙNG NHƯNG CHỈ VỚI 

DỮ LIỆU GIẢ | `home_screen.dart:152` | Mock |
| `lib/screens/cs_warning_screen.dart` | `CSWarningScreen` | ĐANG DÙNG NHƯNG CHỈ VỚI DỮ LIỆU GIẢ | `home_screen.dart:149` | Mock |
| `lib/theme/app_theme.dart` | `CSAppColors` | ĐANG DÙNG THẬT | `cs_settings_screen.dart:79` | - |
| `lib/widgets/*` (cs_app_card.dart, v.v.) | (Các Widget UI) | ĐANG DÙNG THẬT | Rất nhiều file trong `screens/` | - |

*(Chú thích: Các file trong `widgets/` đều đang được dùng như thư viện component UI)*

---

## 2. SƠ ĐỒ ĐƯỜNG ĐI THẬT (ROUTING) KHI APP CHẠY

Dựa trên cấu trúc code từ `main.dart` và `HomeShell`:

```text
[main.dart:31] -> CSLoginScreen (Đăng nhập)
                     |
                     v (Khi gọi onLogin thành công)
[main.dart:35] -> HomeShell (Giao diện chính với Bottom Navigation)
                     |
  +------------------+------------------+------------------+
  | (Tab 0)          | (Tab 1 - Nút QR) | (Tab 2)          |
  v                  v                  v                  |
 CSHomeScreen      ScannerScreen      CSSettingsScreen     |
  |                  |                  |                  |
  |-- (Bấm Suất chiếu) -> CSShowtimesScreen                |
  |-- (Bấm Phòng chiếu)-> CSRoomsScreen                    |
  |-- (Bấm Sự cố & BG) -> CSHandoverScreen                 |
  |                       |-- (Bấm item) -> CSIncidentDetailScreen
  |                       |-- (Bấm thêm) -> CSAddIncidentScreen
  |-- (Bấm Cảnh báo)   -> CSWarningScreen                  |
  |                       |-- (Bấm item) -> CSWarningDetailScreen
  |-- (Bấm Chuông)     -> CSNotificationScreen             |
```

**Các màn hình mồ côi (Không có nút bấm thật để dẫn tới):**
- **Empty / Pop Action:** `CSAddIncidentScreen` (nút thêm chỉ gọi pop), `CSIncidentDetailScreen`, `CSNotificationScreen` hiện tại có các nút `onPressed: () {}` (chưa có logic thật).

---

## 3. SO SÁNH CÁC CẶP FILE NGHI NGỜ TRÙNG LẶP

| Cặp File | Kết luận bản nào ĐANG DÙNG | Giải thích / Bằng chứng |
|---|---|---|
| `features/auth/.../login_screen.dart` vs `screens/cs_login_screen.dart` | **`screens/cs_login_screen.dart`** | Bản trong `features` sinh ra từ commit `9c57b51` nhưng đã bị thay thế hoàn toàn bởi `cs_login_screen.dart` trong commit `bccb682` ("Tích hợp 19 màn hình từ Figma"). `main.dart` hiện tại trỏ tới `CSLoginScreen`. |
| `features/home/.../home_screen.dart` vs `screens/cs_home_screen.dart` | **CẢ HAI ĐỀU DÙNG (Không trùng)** | `features/home/.../home_screen.dart` đóng vai trò là Shell (chứa Bottom Navigation & Routing), còn `screens/cs_home_screen.dart` là giao diện nội dung của Tab đầu tiên. |
| `theme/app_theme.dart` vs `core/theme/app_theme.dart` | **CẢ HAI ĐỀU DÙNG (Trùng lặp một phần)** | `core/theme/` chứa `AppTheme` dùng trong `main.dart`. `theme/` chứa `CSAppColors` dùng trực tiếp trong rất nhiều màn hình `screens/cs_*.dart`. |

---

## 4. KIỂM TRA THƯ VIỆN & ASSETS

1. **Thư viện KHÔNG DÙNG trong `pubspec.yaml` (dựa trên import analysis):**
   - `flutter_riverpod` (Khai báo nhưng không thấy import nào)
   - `go_router` (Đã được comment trong `main.dart` là "thay bằng go_router sau", hiện tại vẫn dùng Navigator tĩnh)
   - `cupertino_icons` (Không import trực tiếp)

2. **Assets:**
   - `assets/images/logo.png`: CHỈ được dùng trong file `features/auth/presentation/login_screen.dart`. Vì file này bị mồ côi, hình ảnh này thực chất không xuất hiện trên app hiện tại.

3. **Test:**
   - 2 Test cases (Counter, Race condition) đều **FAILED** khi chạy lệnh `flutter test` (Do test cũ `widget_test.dart` vẫn tìm `MyApp` giao diện mặc định đếm số, nhưng app đã đổi thành CineSight).

---

## 5. GIẢI THÍCH VAI TRÒ THƯ MỤC CHO FE DEV

- **`features/` và `core/`**: Đây là cách chia thư mục theo kiểu "Feature-First" (hoặc Clean Architecture). Kiểu này giống như trong React bạn chia `src/features/auth` và `src/features/dashboard`. Mục tiêu ban đầu của code là đi theo hướng này (ví dụ `features/auth/` và `features/scanner/`).
- **`screens/` và `widgets/`**: Đây là kiểu chia "Loại component" (như `src/pages` và `src/components`). Toàn bộ UI Figma mới nhất đã được ném thẳng vào `screens/` và `widgets/` thông qua 1 commit lớn (`bccb682`).
- **Vì sao `screens/` vẫn tồn tại?**: Vì người code (hoặc team) đã dùng `screens/` để chứa nhanh 19 màn hình từ Figma, thay vì tái cấu trúc chúng cẩn thận vào từng `features/`. `screens/` ĐANG là bộ mặt chính của app.
- **Tóm lại**: Dự án đang bị "trộn" cả 2 mô hình (vừa chia theo tính năng, vừa chia theo loại). Bạn có thể tưởng tượng nó giống hệt 1 dự án React ban đầu định dùng tính năng (`src/features`) nhưng sau đó vội release nên đẩy hết vào `src/pages` (`screens/`).

---

## 6. ĐỀ XUẤT (CHƯA THỰC HIỆN - CẦN BẠN QUYẾT ĐỊNH)

**a. An toàn xoá (Có bằng chứng 100% không dùng):**
- Thư mục `lib/features/auth/` (vì đã thay bằng `cs_login_screen.dart`).
- Xoá `flutter_riverpod` và `go_router` khỏi `pubspec.yaml` nếu chưa có ý định nối luồng bằng router/state manager.
- Xoá file `assets/images/logo.png` (không hiển thị ở đâu).
- Xoá `test/widget_test.dart` (test mặc định của Flutter bị hỏng vì app đã đổi).

**b. Nên giữ (Chờ nối vào luồng):**
- Hầu hết các file trong `screens/` (ví dụ `cs_incident_detail_screen.dart`, `cs_add_incident_screen.dart`). Chúng đã nối được UI, đang xài `mock_data`, cần bạn thay thế logic nút bấm bằng data thật từ `ApiClient`.

**c. Cần FE Dev (bạn) quyết định:**
- Gom `theme/app_theme.dart` (chứa `CSAppColors`) và `core/theme/app_theme.dart` (chứa `AppTheme`) thành 1 file duy nhất để tránh hiểu lầm.
- Gom dần các file từ `screens/` về cấu trúc `features/` (ví dụ: move `cs_showtimes_screen.dart` vào `features/showtimes/`) để code sạch sẽ hơn giống cấu trúc React của bạn.
"""

with open('MOBILE_AUDIT.md', 'w', encoding='utf-8') as f:
    f.write(audit_content)
