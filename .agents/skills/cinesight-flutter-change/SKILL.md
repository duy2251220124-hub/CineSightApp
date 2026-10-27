---
name: cinesight-flutter-change
description: "Applies when editing mobile_app (Flutter/Dart): screens, widgets, ApiClient, HiveService, scanner_screen. Dùng khi sửa app di động. Keeps scanning logic intact, avoids mock data in finished screens, runs flutter analyze and test."
---

## Trước khi sửa
1. Đọc nguyên file sẽ sửa và nêu rõ sẽ đổi dòng nào.
2. KHÔNG đổi logic quét QR (4 bước kiểm tra), cơ chế lịch sử quét (scan_history_box giữ vĩnh viễn), cơ chế đồng bộ trong scanner_screen.dart, hive_service.dart, api_client.dart, trừ khi yêu cầu nói rõ. Bọc giao diện bên ngoài logic cũ.

## Khi sửa
- Dùng màu và theme sẵn có (CSAppColors, AppTheme), widget CS... sẵn có. Không hardcode màu mới.
- Mỗi màn hình gọi mạng phải có đủ 3 trạng thái: đang tải; rỗng (thông báo rõ); lỗi mạng (thông báo rõ + nút thử lại). Lỗi thì không được hiện dữ liệu giả.
- Sau mỗi `await` mà còn dùng context: kiểm tra `if (!mounted) return;`.
- Dùng debugPrint, không dùng print.
- Màn hình hoàn chỉnh không được đọc mock_data.dart. Chỗ còn dùng mock phải có comment `// TODO: [CS-MERGE] Nối dữ liệu thật`.
- Đồng bộ vé: nhóm theo (room, show); chỉ xóa khỏi hộp chờ đúng các khóa đã gửi thành công; mục JSON hỏng thì bỏ qua và KHÔNG xóa.
- Mã suất lấy từ API, không tự tính.

## Sau khi sửa
1. `cd mobile_app; flutter analyze` và `flutter test`. Dán kết quả (số issue, test đạt/trượt).
2. Test dùng Hive phải dùng thư mục tạm riêng cho mỗi test (không dùng thư mục cố định trong repo).
3. Không nói giao diện "đã chạy đúng" khi chưa có ảnh chụp hoặc xác nhận của người dùng; ghi "CHƯA XÁC NHẬN TRÊN THIẾT BỊ" kèm các bước tôi cần thử tay.

## Đầu ra bắt buộc
Danh sách file đổi + dòng; kết quả analyze/test; danh sách việc cần thử tay trên thiết bị.
