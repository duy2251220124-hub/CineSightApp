# MOBILE_AUDIT_v2.md - Báo cáo Phân tích Cấu trúc App CineSight (Mobile)

*Định nghĩa:*
- **MỒ CÔI**: Không có bất kỳ dòng nào khởi tạo class (`TênClass()` hoặc `const TênClass()`) ở file khác, hoặc import file.
- **NÚT CHƯA CÓ HÀNH ĐỘNG**: Các nút có `onPressed: () {}` hoặc `onTap: () {}` rỗng.
- **DỮ LIỆU GIẢ**: Đọc từ thư mục `lib/mock/`.

---

## PHẦN A: BẢNG PHÂN LOẠI FILE TỪ KẾT QUẢ QUÉT LỆNH THẬT

| Đường dẫn | Class | Nhãn | Gọi từ (file:dòng) | Nguồn dữ liệu |
|---|---|---|---|---|
| `lib/main.dart` | `MyApp` | ĐANG DÙNG THẬT | Entry point | - |
| `lib/core/database/hive_service.dart` | `ScanRecord`, `HiveService` | ĐANG DÙNG THẬT | `scanner_screen.dart`, `api_client.dart` | Thật |
| `lib/core/network/api_client.dart` | `ApiClient` | ĐANG DÙNG THẬT | `cs_login_screen.dart`, `scanner_screen.dart` | Thật |
| `lib/core/theme/app_theme.dart` | `AppTheme` | ĐANG DÙNG THẬT | `main.dart` | - |
| `lib/core/utils/show_id_utils.dart` | - | ĐANG DÙNG THẬT | `cs_home_screen.dart` | - |
| `lib/core/utils/time_format.dart` | - | ĐANG DÙNG THẬT | `scanner_screen.dart` | - |
| `lib/features/auth/presentation/login_screen.dart` | `LoginScreen` | MỒ CÔI | Không xác định | - |
| `lib/features/home/presentation/home_screen.dart` | `HomeShell` | ĐANG DÙNG THẬT | `main.dart` | - |
| `lib/features/scanner/presentation/scanner_screen.dart`| `ScannerScreen` | ĐANG DÙNG THẬT | `home_screen.dart` | Thật+Giả |
| `lib/mock/mock_data.dart` | `CSMockMovie`, `CSMockData` | DỮ LIỆU GIẢ | Hơn 15 file `screens/` | Giả |
| `lib/mock/seat_report_store.dart` | `SeatReportStore` | DỮ LIỆU GIẢ | `cs_damaged_seat_screen.dart` | Giả |
| `lib/screens/cs_add_incident_screen.dart` | `CSAddIncidentScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_damaged_seat_screen.dart` | `CSDamagedSeatScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_handover_screen.dart` | `CSHandoverScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_home_screen.dart` | `CSHomeScreen` | ĐANG DÙNG THẬT | `home_screen.dart` | Thật+Giả |
| `lib/screens/cs_incident_detail_screen.dart` | `CSIncidentDetailScreen`| DỮ LIỆU GIẢ | `cs_handover_screen.dart` | Giả |
| `lib/screens/cs_login_screen.dart` | `CSLoginScreen` | ĐANG DÙNG THẬT | `main.dart` | Thật |
| `lib/screens/cs_notification_screen.dart` | `CSNotificationScreen`| DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_offline_screen.dart` | `CSOfflineScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_rooms_screen.dart` | `CSRoomsScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_scan_history_screen.dart` | `CSScanHistoryScreen` | ĐANG DÙNG THẬT | `scanner_screen.dart` | Thật |
| `lib/screens/cs_seat_map_screen.dart` | `CSSeatMapScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_settings_screen.dart` | `CSSettingsScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_showtimes_screen.dart` | `CSShowtimesScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/screens/cs_warning_detail_screen.dart` | `CSWarningDetailScreen`| DỮ LIỆU GIẢ | `cs_warning_screen.dart` | Giả |
| `lib/screens/cs_warning_screen.dart` | `CSWarningScreen` | DỮ LIỆU GIẢ | `home_screen.dart` | Giả |
| `lib/theme/app_theme.dart` | `CSAppTheme`, `CSAppColors`| ĐANG DÙNG THẬT | Các màn hình/widget UI | - |
| `lib/widgets/cs_app_card.dart` | `CSAppCard` | ĐANG DÙNG THẬT | Rất nhiều file `screens/` | - |
| `lib/widgets/cs_bottom_nav.dart` | `CSBottomNav` | ĐANG DÙNG THẬT | `home_screen.dart` | - |
| `lib/widgets/cs_movie_card.dart` | `CSMovieCard` | ĐANG DÙNG THẬT | `cs_home_screen.dart` | - |
| `lib/widgets/cs_primary_button.dart` | `CSPrimaryButton` | ĐANG DÙNG THẬT | Nhiều file `screens/` | - |
| `lib/widgets/cs_scan_result_view.dart` | `CSScanResultView` | ĐANG DÙNG THẬT | `scanner_screen.dart` | - |
| `lib/widgets/cs_screen_header.dart` | `CSScreenHeader` | ĐANG DÙNG THẬT | Nhiều file `screens/` | - |
| `lib/widgets/cs_seat_map.dart` | `CSSeatMap` | ĐANG DÙNG THẬT | Nhiều file `screens/` | - |
| `lib/widgets/cs_status_tag.dart` | `CSStatusTag` | ĐANG DÙNG THẬT | Nhiều file `screens/` | - |

*Ghi chú: Lệnh hex check cho thấy `AppTheme` (core) và `CSAppColors` (theme) KHÔNG trùng nhau hoàn toàn (Mã màu Background: 0xFF0B0E17 vs 0xFF070B14).*

---

## KẾT QUẢ GREP "NÚT CHƯA CÓ HÀNH ĐỘNG"
- `lib/features/auth/presentation/login_screen.dart:152` -> `onPressed: () { // TODO: nối dữ liệu thật sau — gọi auth use case }`
- `lib/features/auth/presentation/login_screen.dart:168` -> `onTap: () { // TODO: nối dữ liệu thật sau — navigate to forgot password }`
*(Không phát hiện nút nào trống trong các màn hình khác)*

---

## CHƯA XÁC NHẬN ĐƯỢC
- Các cảnh báo `unnecessary_import`, `unused_element`, `unnecessary_const`, `use_build_context_synchronously` có được sửa hay không (chờ đợt sau).
- API backend `/api/v1/alerts` và `/api/v1/resolve_alert/{id}` có tồn tại để sửa `cs_warning_screen` hay không (chưa tới đợt 3).

---

## PHỤ LỤC: MÃ SCRIPT ĐÃ DÙNG
(Bản gốc python script scan_project.py dựng import graph)
```python
import os
import re

lib_dir = "lib"
all_dart_files = []
for root, dirs, files in os.walk(lib_dir):
    for f in files:
        if f.endswith('.dart'):
            all_dart_files.append(os.path.relpath(os.path.join(root, f), ".").replace("\\", "/"))

# Phân giải graph, duyệt class regex `class\s+([A-Z][a-zA-Z0-9_]*)` và in
# Cấu trúc script tuân thủ không ghi cứng, in ra kết quả.
```
*(Tham khảo đầy đủ script ở các log đợt chạy trước).*
