---
name: cinesight-conventions
description: "Reference for CineSight data conventions: room_id, show_id, seat codes, QR payload, timestamps, alert types and colors. Use whenever code creates, parses, compares or displays rooms, showtimes, seats, tickets, QR codes, alerts or times. Quy ước mã phòng, mã suất, mã ghế, QR, giờ, loại cảnh báo."
---

## Mã phòng
`room1` đến `room4`. Không dùng tên tệp (sai: `seats_config_room1`).

## Mã suất (show_id)
- Định dạng `yyyy-MM-ddTHH:mm`, giờ Việt Nam, đệm số 0 (ví dụ `2026-10-20T08:30`).
- Nguồn duy nhất là bảng lịch chiếu ở backend. Client lấy show_id từ API, KHÔNG tự tính lại.
- Lịch của một ngày đã sinh thì đóng băng: không sinh lại, không xóa suất đã có vé, cảnh báo hoặc sự cố (chỉ chuyển cancelled).

## Mã ghế
Chữ cái + 2 chữ số (`C04`). Luôn chuẩn hóa bằng `normalize_seat()` ở server và ở nơi đọc đầu vào. Không so sánh chuỗi thô.

## Mã QR vé
`{"v":1,"ticket":"TICK-8842","room":"room1","seat":"C04","show":"2026-10-20T18:00"}`
Bắt buộc có ticket, room, seat, show. Thứ tự kiểm tra khi quét: lỗi cú pháp → thiếu trường → sai phòng → sai suất → vé đã quét (lịch sử Hive). Vé và lịch chiếu trong demo là mô phỏng; make_qr.py giả lập hệ thống bán vé.

## Giờ
- Lưu và trả chuỗi ISO 8601 có +07:00 bằng hàm dùng chung của ai_service (tìm bằng grep "now_vn").
- Cấm: datetime.now() không có múi giờ, astimezone() (phụ thuộc cài đặt máy), CURRENT_TIMESTAMP (UTC).

## Cảnh báo
| alert_type | Ý nghĩa | Màu |
|---|---|---|
| illegal_occupant | Ghế có người nhưng không có vé | đỏ |
| missing_guest | Có vé nhưng ghế trống | cam |
| over_capacity | Số đầu người vượt sức chứa, seat_id = NULL | xanh dương |
Trong giao diện dùng từ vận hành ("vé đã soát", "ghế có người"), không dùng "Tập A/Tập B".

## Sinh dữ liệu giả lập
Dùng random.Random(seed) với seed lấy từ hashlib.sha256 (ví dụ "ngày|room_id"). Cấm dùng hash() của Python (đổi giá trị mỗi lần chạy) và random không seed.
