---
description: Quét toàn bộ dự án từ thư mục gốc và báo trạng thái từng hạng mục bằng nhãn có bằng chứng
---
1. Chạy `git status --short` và `git log --oneline -10`.
2. ai_service: liệt kê route trong main.py; chạy unittest; nếu server đang chạy thì gọi GET / và dán kết quả.
3. mobile_app: `flutter analyze`; liệt kê màn hình còn đọc mock_data.dart (grep); liệt kê màn hình chưa được gọi từ đâu cả.
4. web_admin: `npm run lint`; liệt kê trang và hàm API mỗi trang dùng; tìm giá trị viết cứng (localhost, suất, phòng, MOCK_).
5. Dữ liệu: COUNT từng bảng; số ảnh trong datasets; tồn tại hay không của best.pt và các tệp mô hình đang dùng.
6. Lập bảng Hạng mục | Nhãn | Bằng chứng theo skill cinesight-evidence-report, rồi liệt kê việc còn thiếu theo mức ảnh hưởng tới phần lõi (đối chiếu vé với ghế bằng AI).
