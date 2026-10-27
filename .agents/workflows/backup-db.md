---
description: Sao lưu cinesight.db ra ngoài thư mục dự án và đếm số dòng từng bảng
---
1. Kiểm tra cổng 8000 bằng `Test-NetConnection localhost -Port 8000`. Nếu đang chạy bởi tiến trình bạn không bật, hỏi người dùng trước.
2. Tạo thư mục `C:\CineSightApp_backup` nếu chưa có, rồi chép `ai_service\cinesight.db` thành `C:\CineSightApp_backup\cinesight_<lý do>_<yyyyMMdd_HHmmss>.db`.
3. Báo đường dẫn và kích thước bản sao lưu.
4. Mở bản sao bằng sqlite3: chạy `PRAGMA integrity_check` và đếm COUNT(*) từng bảng. Không in mật khẩu hay hash.
