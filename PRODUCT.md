# Product

<!-- impeccable:product-schema 1 -->

## Platform

adaptive

## Users

1. **Nhân viên soát vé rạp (Cinema Ticket Checkers / Ushers):** Làm việc trực tiếp tại cửa phòng chiếu và bên trong rạp trong điều kiện ánh sáng yếu; sử dụng Mobile App để quét vé QR, kiểm tra nhanh vé hợp lệ và nhận diện phim trực quan.
2. **Kỹ thuật viên / Quản lý ca trực (Floor Supervisors / Cinema Operators):** Giám sát trạng thái phòng chiếu, nhận diện ghế ngồi sai quy định do AI phát hiện, xử lý ghế hỏng và thực hiện bàn giao ca trực.
3. **Ban Quản lý Rạp (Cinema Managers / Control Room):** Theo dõi tổng thể tỷ lệ lấp đầy, đối soát số vé đã quét so với số người thực tế có trong rạp qua CCTV và ngăn ngừa thất thoát vé trên Web Admin.

## Product Purpose

CineSight tự động hóa và nâng cao độ chính xác của quy trình kiểm soát vé và ghế ngồi trong rạp chiếu phim bằng trí tuệ nhân tạo (Computer Vision). Thành công của sản phẩm được đo lường bằng:
- Tốc độ soát vé nhanh (< 1 giây/vé) kể cả khi ngoại tuyến (offline-first).
- Tỷ lệ phát hiện chính xác các trường hợp gian lận hoặc ngồi sai ghế thông qua đối soát tự động giữa camera CCTV và dữ liệu vé đã quét.
- Giảm thiểu tối đa thao tác thủ công và loại bỏ tình trạng spam thông báo rời rạc cho nhân viên vận hành.

## Positioning

Hệ thống duy nhất tích hợp liền mạch giữa camera giám sát góc rộng CCTV của từng phòng chiếu với thuật toán AI Seat Mapping để liên tục đối soát chéo:
$$\text{Ghế cảnh báo} = \{ \text{Ghế có người ngồi thực tế} \} \setminus \{ \text{Ghế đã được soát vé hợp lệ} \}$$
Cung cấp dữ liệu cảnh báo tức thì có ngữ cảnh đầy đủ: Số vé đã quét của rạp, số người thực tế hiện có trong rạp, và danh sách các ghế vi phạm cụ thể.

## Operating Context

- **Không gian rạp chiếu phim:** Môi trường ánh sáng tối, yêu cầu giao diện Dark Mode độ tương phản cao, thao tác một tay trên điện thoại di động và phản hồi rung xúc giác (Haptic Feedback).
- **Hạ tầng kết nối:** 
  - Máy chủ AI Backend (`FastAPI`) kết nối camera CCTV và cơ sở dữ liệu SQLite chuẩn 3NF (`cinesight.db`).
  - Mobile App kết nối Internet qua Ngrok Tunnel an toàn hoặc mạng nội bộ (LAN).
  - Hỗ trợ lưu trữ vé offline tại máy di động qua Hive khi mất kết nối mạng đột ngột.

## Capabilities and Constraints

- **Khả năng cốt lõi:**
  - Quét vé mã QR đơn lẻ và vé mua cụm nhiều ghế.
  - Tự động đồng bộ và hiển thị poster phim TMDB chính thức trên mọi danh sách suất chiếu.
  - Tự động ưu tiên đưa suất chiếu đang chiếu lên đầu danh sách trong ngày hiện tại.
  - Đánh dấu ghế hỏng và ghi nhận biên bản sự cố, bàn giao ca trực.
  - Bảng điều khiển giám sát 2D theo thời gian thực trên Web Admin.
- **Ràng buộc kỹ thuật & giao diện:**
  - Tuyệt đối không để xảy ra lỗi tràn màn hình (`RenderFlex overflow`) khi bật bàn phím ảo hoặc trên các dòng máy màn hình nhỏ; áp dụng chuẩn `LayoutBuilder` + `SingleChildScrollView`.
  - Không spam thông báo: Thông báo trên Mobile App và Web Admin phải tổng hợp đầy đủ số vé đã soát, số người thực tế và danh sách ghế vi phạm.

## Brand Commitments

- **Tên sản phẩm:** CineSight.
- **Khẩu hiệu / Phụ đề:** Hệ thống kiểm soát vé & giám sát ghế ngồi thông minh bằng AI.
- **Bảng màu nhận diện:** Dark Mode nền tối chuyên dụng rạp phim (`#0A0E17`, `#0F1420`, `#141926`), dải màu công nghệ Electric Blue (`#2563EB`, `#38BDF8`), tín hiệu xanh hoạt động (`#10B981`) và đỏ cảnh báo (`#EF4444`).
- **Logo chính thức:** Biểu tượng tròn viền trắng 1.5 với icon vé điện ảnh tại `mobile_app/assets/images/logo.png`.

## Evidence on Hand

- Cơ sở dữ liệu SQLite 3NF hoạt động thực tế: `ai_service/cinesight.db` chứa 30+ suất chiếu thực tế, danh mục phim đồng bộ TMDB và sơ đồ ghế các phòng chiếu (`room1`, `room2`, `room3`, `room4`).
- Bằng chứng kiểm thử mô hình YOLO AI nhận diện người ngồi qua CCTV: `ai_service/tests/`, `tools/qr_generator.html`.
- Ảnh chụp màn hình và tài liệu vận hành đã kiểm chứng: `docs/RUNNING_GUIDE.md`, `docs/TAI_KHOAN_HE_THONG.md`.

## Product Principles

1. **Hiển thị trực quan, tức thời (Zero-Cognitive Load):** Mọi suất chiếu phải có hình ảnh poster phim để nhận diện tức thì; nhân viên không phải căng mắt đọc chữ trong bóng tối.
2. **Cảnh báo có ngữ cảnh, chống spam (Contextual & Consolidated Alerts):** Mọi cảnh báo phải đi kèm bộ 3 chỉ số cốt lõi (vé đã quét, người thực tế, số ghế nghi vấn) thay vì phát thông báo vụn vặt.
3. **Độ tin cậy tuyệt đối tại hiện trường (Resilient & Offline-Ready):** Ứng dụng di động không được crash hoặc tràn giao diện trong bất kỳ tình huống nhập liệu nào; hỗ trợ soát vé ngoại tuyến ngay cả khi đứt mạng.
4. **Trung thực với dữ liệu thực tế (Empirical Truth):** Mọi trạng thái ghế và số liệu lấp đầy phòng chiếu phải phản ánh đúng 100% dữ liệu thực từ camera CCTV và lượt soát vé.

## Accessibility & Inclusion

- Giao diện Dark Mode tương phản cao theo chuẩn WCAG dành riêng cho nhân viên vận hành rạp chiếu phim trong môi trường bóng tối.
- Phản hồi đa giác quan: Kết hợp rung xúc giác (Haptic Feedback) và màu sắc tín hiệu (Xanh / Vàng / Đỏ) kèm biểu tượng rõ ràng, hỗ trợ nhân viên nhận biết tức thời trong rạp mà không cần bật âm thanh gây ồn cho khán giả.

