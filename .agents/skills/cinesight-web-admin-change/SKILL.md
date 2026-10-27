---
name: cinesight-web-admin-change
description: "Applies when editing web_admin (React + Vite): pages, cineSightApi.js, dashboard.css, Dashboard.jsx. Dùng khi sửa giao diện web quản trị. Enforces configurable API base URL, polling rules, UI states and design tokens."
---

## Địa chỉ API
- Không viết cứng `http://localhost:8000` trong trang hay component. Đọc từ `import.meta.env.VITE_API_BASE` với giá trị dự phòng rõ ràng, và ghi vào tệp `.env.example`. Lý do: máy khác (LAN, tunnel) gọi `localhost` sẽ trỏ vào chính nó; trang https gọi API http bị trình duyệt chặn (mixed content).
- Mọi lệnh gọi mạng đi qua `src\api\cineSightApi.js`.

## Polling và state
- Polling bằng setInterval trong useEffect, có cleanup (`return () => clearInterval(...)`). Mặc định 5 giây; không dùng WebSocket.
- Mảng phụ thuộc của effect polling phải ổn định (rỗng hoặc giá trị không đổi mỗi lần tải). KHÔNG đưa state được cập nhật bởi chính lần tải đó vào mảng phụ thuộc (gây gọi liên tục). Kiểm chứng: đếm số lần gọi trong 20 giây phải khoảng 4-5 lần.
- Không dùng `alert()` để báo lỗi; hiển thị thông báo trong giao diện.

## Giao diện
- Mỗi trang có 3 trạng thái: đang tải; rỗng (có hướng dẫn); lỗi kết nối (rõ ràng + nút thử lại).
- Dùng lại biến CSS và class sẵn có của Dashboard (soc-*). Không tạo phong cách mới và tránh bộ "thẻ bo góc giống hệt nhau".
- Màu cảnh báo: khách lậu đỏ, vắng mặt cam, vượt sức chứa xanh dương; có ký hiệu kèm theo, không chỉ dựa vào màu.
- Giờ hiển thị theo giờ Việt Nam từ chuỗi ISO có offset. Phòng và suất lấy từ API, không viết cứng.
- Nhãn bằng từ vận hành thực tế; có focus bàn phím rõ ràng.

## Sau khi sửa
1. `cd web_admin; npm run lint` và `npm run build`. Dán output.
2. Liệt kê các trang gọi hàm API đã đổi và đã kiểm tra từng trang.
3. Ghi "CHƯA XÁC NHẬN TRÊN TRÌNH DUYỆT" cho những gì cần tôi mở F12 kiểm tra (Network, Console).
