---
name: cinesight-api-contract
description: "Applies when adding or changing a FastAPI endpoint, request or response fields, or any call in web_admin (cineSightApi.js) or mobile_app (api_client.dart). Dùng khi thêm hoặc sửa API, đổi tên trường, sửa lệnh gọi từ web hoặc app. Prevents payload mismatches such as HTTP 422, wrong field names, unsafe unauthenticated endpoints."
---

## Mục tiêu
Backend, web và mobile luôn nói cùng một "hợp đồng" dữ liệu.

## Quy trình (làm đủ, theo thứ tự)
1. Tìm mọi nơi dùng endpoint: grep đường dẫn trong `web_admin\src` và `mobile_app\lib`.
2. Lập bảng: tên trường | kiểu backend | web gửi/đọc | mobile gửi/đọc. Chỗ nào lệch thì đưa vào danh sách phải sửa.
3. Sửa backend VÀ mọi nơi tiêu thụ trong cùng một tác vụ. Không đổi tên trường ở một nơi duy nhất.
4. Test bằng ĐÚNG payload sao chép từ code client (không tự viết tay). Dán status và body (che bí mật).
5. Thử ít nhất một đầu vào sai: phải trả 400, 404, 409 hoặc 422 kèm thông báo rõ ràng, không được 500.

## Quy ước
- Lỗi trả dạng `{"error": "<thông báo tiếng Việt>"}` với mã HTTP đúng.
- Danh sách là mảng thật (ví dụ seat_ids là mảng, không phải chuỗi JSON).
- Giờ là chuỗi ISO có +07:00. Bộ lọc coi "ALL" và "all" như nhau.
- Response không bao giờ chứa mật khẩu, hash hoặc token.
- Tên đường dẫn theo phong cách sẵn có: `/api/v1/<hành_động_hoặc_danh_từ>`; thao tác xử lý dùng POST (ví dụ resolve_alert).
- API chưa có xác thực: KHÔNG thêm endpoint nhập dữ liệu từ ngoài, huấn luyện, đồng bộ phim, sinh lịch, xóa hàng loạt. Những việc đó là công cụ dòng lệnh trong ai_service\tools. Chỉ thêm endpoint ĐỌC hoặc thao tác nghiệp vụ nhỏ.

## Đầu ra bắt buộc
Bảng hợp đồng trước/sau; danh sách file đã sửa ở cả ba phía; output các lệnh gọi thử.
