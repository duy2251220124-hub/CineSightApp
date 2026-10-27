---
description: Đối chiếu payload endpoint giữa backend, web_admin và mobile_app
---
1. Hỏi người dùng đường dẫn endpoint cần kiểm tra (hoặc lấy toàn bộ route trong main.py nếu người dùng muốn kiểm tra hết).
2. Với mỗi endpoint, grep trong web_admin\src và mobile_app\lib, lập bảng: trường | backend | web | mobile | khớp hay lệch.
3. Gọi thử bằng đúng payload sao chép từ code client; dán status và body (che bí mật).
4. Liệt kê chỗ lệch kèm đề xuất sửa. Không sửa khi chưa được phép.
