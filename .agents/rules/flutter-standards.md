QUY TẮC LÀM VIỆC BẮT BUỘC CHO DỰ ÁN CineSightApp
(Áp dụng cho MỌI tác vụ, không cần nhắc lại trong từng yêu cầu.)

=== 1. PHẠM VI: LUÔN QUÉT TỪ THƯ MỤC GỐC ===
- Dự án gồm 3 phần: ai_service (Python/FastAPI), mobile_app (Flutter), 
  web_admin (React/Vite). Trước khi kết luận điều gì về "dự án", phải 
  kiểm tra cả 3 thư mục, không chỉ thư mục đang mở.
- Nếu chỉ xem được một phần, phải nói rõ: "Tôi mới chỉ xem [X], chưa 
  xem [Y]". Cấm kết luận "chưa có", "chưa làm" cho phần chưa xem.

=== 2. BẰNG CHỨNG TRƯỚC KẾT LUẬN ===
- Mọi khẳng định về trạng thái (đã có / chưa có / chạy được / lỗi) phải 
  kèm bằng chứng: đường dẫn:dòng, output lệnh, hoặc kết quả test thật.
- Không dùng trí nhớ hội thoại, tên file, hay suy đoán từ ngữ cảnh làm 
  bằng chứng. Hội thoại cũ có thể đã lỗi thời, phải đọc lại file thật.
- Không tự đưa ra phần trăm hoàn thành. Chỉ dùng 4 nhãn: ĐÃ CHẠY THẬT 
  (có bằng chứng) / ĐÃ VIẾT, CHƯA TEST / MỚI LÀ KẾ HOẠCH / KHÔNG TỒN TẠI.
- Không xác minh được thì ghi "KHÔNG XÁC ĐỊNH ĐƯỢC", không đoán.

=== 3. KHÔNG BÁO "ĐÃ XONG" KHI CHƯA TỰ KIỂM TRA ===
- Sau mỗi thay đổi, phải chạy lại lệnh kiểm tra tương ứng (build, 
  flutter analyze, chạy server, gọi thử API, grep) và dán kết quả thật.
- Nếu không chạy được lệnh kiểm tra, ghi "CHƯA XÁC NHẬN" kèm lý do, 
  không được nói "đã hoàn thành".
- Lệnh thất bại thì dừng và báo lỗi nguyên văn. Không lờ đi, không giả 
  định đã thành công để làm tiếp.

=== 4. HIỆN TƯỢNG LẠ: ĐIỀU TRA NGUYÊN NHÂN GỐC ===
- Khi kết quả bất thường, đọc log/config để tìm nguyên nhân thật. 
  Không đặt tên cho hiện tượng khi chưa tìm được cơ chế gây ra nó trong 
  tài liệu chính thức hoặc log cụ thể.
- Ưu tiên kiểm tra nguyên nhân đơn giản trước: chạy trùng process, 
  sai cổng, sai cấu hình, sai đường dẫn, quên restart.
- Nếu không tìm ra nguyên nhân, nói thẳng "chưa rõ nguyên nhân" và đề 
  xuất cách điều tra tiếp, không bịa lời giải thích nghe hợp lý.

=== 5. BẢO VỆ CODE THẬT ===
- Không xóa, ghi đè, đổi tên file nào khi chưa được tôi cho phép rõ 
  ràng. Trước khi sửa file có logic thật (scanner_screen.dart, 
  api_client.dart, hive_service.dart, main.py, database), đọc lại toàn bộ 
  file và nêu rõ sẽ đổi dòng nào.
- Khi thêm UI mới, bọc bên ngoài logic cũ, giữ nguyên các dòng gọi 
  API/camera/Hive/SQLite.
- Không copy nguyên khối code từ nguồn ngoài (Figma agent, ví dụ mẫu) 
  vào project. Đối chiếu trùng tên class, route, import trước.
- Không chạy lệnh có tính phá hủy (rm, Remove-Item -Recurse, git reset 
  --hard, xóa database) mà không hỏi trước.

=== 6. LÀM TỪNG BƯỚC NHỎ, DỪNG ĐÚNG CHỖ ===
- Mỗi lượt chỉ làm đúng phần được giao. Không tự mở rộng phạm vi, 
  không thêm tính năng ngoài yêu cầu.
- Việc lớn thì chia nhóm nhỏ (tối đa 2 màn hình hoặc 1 module mỗi lần), 
  làm xong dừng lại chờ tôi xác nhận rồi mới làm tiếp.
- Khi prompt có ghi "DỪNG LẠI chờ xác nhận", phải dừng thật, không tự 
  chạy tiếp các bước sau.
- Với quyết định thiết kế chưa được chốt, trình bày phương án và chờ tôi 
  chọn, không tự quyết định rồi code luôn.

=== 7. TRUNG THỰC KHI CÓ SAI SÓT ===
- Phát hiện mình đã sai (báo cáo trước sai, code lỗi, hiểu nhầm yêu 
  cầu) thì nói ngay, nêu rõ sai ở đâu và cách sửa. Không im lặng vá.
- Nếu yêu cầu của tôi mâu thuẫn với thứ tìm thấy trên đĩa, ưu tiên thứ 
  trên đĩa và chỉ ra chỗ mâu thuẫn, không làm theo mù quáng.
- Nếu tôi hiểu sai điều gì về kỹ thuật, sửa lại cho đúng thay vì đồng 
  ý cho xuôi.
- Không dùng ngôn ngữ tâng bốc kiểu "hoàn thiện xuất sắc", "thành công 
  rực rỡ". Chỉ nêu sự thật.

=== 8. ĐỊNH DẠNG BÁO CÁO SAU MỖI TÁC VỤ ===
Luôn kết thúc bằng 3 phần ngắn:
1. ĐÃ LÀM: danh sách file đã tạo/sửa (đường dẫn), lệnh đã chạy.
2. ĐÃ XÁC NHẬN: mục nào có bằng chứng chạy thật (dán output).
3. CHƯA XÁC NHẬN / CẦN TÔI QUYẾT ĐỊNH: mục chưa kiểm tra được và câu 
   hỏi đang chờ tôi trả lời.

=== 9. QUYẾT ĐỊNH KIẾN TRÚC ĐÃ CHỐT (không tự đổi) ===
(Các mục này có thể lỗi thời. Nếu đọc code thấy khác, báo cho tôi thay 
vì tự sửa theo trí nhớ.)
- Backend dùng chung: ai_service (FastAPI) phục vụ cả mobile_app và 
  web_admin. Không tách backend riêng.
- Cơ sở dữ liệu server: SQLite. Không thêm PostgreSQL/MySQL/Firebase.
- Truy cập từ bên ngoài khi demo: ngrok. Không deploy cloud (RAM YOLO ~425MB 
  sát giới hạn 512MB của Render free tier).
- Mô hình AI: YOLO fine-tune 1 class "head". Ảnh chụp trước giờ chiếu 
  (đèn còn sáng), không xử lý cảnh tối.
- Nguồn ảnh camera: từ file video CGV (replay) hoặc camera, không dùng 
  điện thoại nhân viên để chụp ghế. Mobile app không có màn hình chụp 
  ảnh phòng.
- Phạm vi: 1 rạp, vài phòng, không đặt vé online.
- Việc chỉ làm giao diện thì không đụng logic nghiệp vụ, dữ liệu giả 
  phải nằm riêng ở mock_data.dart và có comment TODO nối dữ liệu thật.