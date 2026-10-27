---
name: cinesight-db-safety
description: "Applies when editing, migrating, querying or testing the SQLite database (cinesight.db, database.py, tables tickets, alerts, incidents, employees, movies, showtimes). Dùng khi sửa CSDL, thêm bảng/cột, chạy test ghi dữ liệu, di chuyển dữ liệu. Enforces backup, idempotent migrations, parameterized SQL, test-data cleanup."
---

## Mục tiêu
Không làm mất hoặc làm hỏng dữ liệu trong cinesight.db.

## Trước khi GHI bất kỳ dữ liệu nào
1. Kiểm tra cổng 8000: `Test-NetConnection localhost -Port 8000`. Nếu đang chạy bởi tiến trình bạn không bật, hỏi người dùng trước khi tắt.
2. Sao lưu ra NGOÀI thư mục dự án: `Copy-Item ai_service\cinesight.db C:\CineSightApp_backup\cinesight_<lý do>_<yyyyMMdd_HHmmss>.db`. Báo đường dẫn, kích thước và COUNT(*) từng bảng.
3. Chưa có bản sao lưu thì không ghi.

## Quy tắc khi viết code SQL
- Luôn dùng tham số `?`. Tên bảng và tên cột chỉ lấy từ danh sách cho phép (whitelist), không nối chuỗi từ đầu vào người dùng hoặc tham số dòng lệnh.
- Mở kết nối bằng try/finally hoặc contextlib.closing; commit rõ ràng; một thay đổi logic = một transaction; lỗi thì rollback toàn bộ.
- Migration phải chạy lại được nhiều lần (idempotent): kiểm tra PRAGMA table_info hoặc sqlite_master trước khi ALTER hoặc CREATE. Chạy trong 1 transaction và dán schema trước/sau.
- Không DROP TABLE, không DELETE thiếu WHERE, không xóa dòng do người khác tạo. Muốn bỏ bảng cũ thì đổi tên (RENAME) và giữ lại.
- Mốc thời gian mới: chuỗi ISO 8601 có +07:00 do hàm giờ dùng chung của ai_service tạo (tìm bằng grep "now_vn"). Không dùng CURRENT_TIMESTAMP (giờ UTC).
- Dedup cảnh báo có seat_id NULL: dùng `seat_id IS ?`, không dùng `seat_id = ?`.

## Dữ liệu test
- Tiền tố `zz_` cho tên nhân viên, tiêu đề sự cố, mã vé test (ví dụ ZZTEST-1).
- Nếu API kiểm tra (room_id, show_id) có trong lịch chiếu thì dùng một suất THẬT của lịch và dọn đúng các dòng đã tạo (theo id). Chỉ dùng show_id giả khi API không kiểm tra.
- Sau test: COUNT(*) từng bảng phải bằng lúc trước (bộ đếm AUTOINCREMENT được phép tăng). Dán bảng so sánh.

## Cấm
- In giá trị mật khẩu hoặc hash. Chỉ in số lượng hoặc "có/không có tiền tố pbkdf2_sha256$".
- Để lại dữ liệu test trong DB thật.

## Đầu ra bắt buộc
Đường dẫn bản sao lưu; COUNT trước/sau; schema trước/sau (nếu có migration); danh sách lệnh đã chạy.
