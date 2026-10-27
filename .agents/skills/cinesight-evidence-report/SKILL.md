---
name: cinesight-evidence-report
description: "Applies when writing status reports, audits, progress checks, thesis chapter content or any statement about what is done, working, tested or missing in CineSight. Dùng khi báo cáo tiến độ, kiểm toán, viết nội dung báo cáo đồ án. Requires evidence labels and forbids invented numbers."
---

## Nhãn trạng thái (chỉ dùng các nhãn này)
- ĐÃ CHẠY THẬT: có output lệnh chạy TRONG LƯỢT NÀY, dùng dữ liệu thật.
- ĐÃ VIẾT, CHƯA TEST: có code, chưa có bằng chứng chạy.
- DỮ LIỆU GIẢ: có giao diện nhưng đọc dữ liệu mock.
- MỚI LÀ KẾ HOẠCH: chưa có code.
- KHÔNG TỒN TẠI: kiểm tra trên đĩa không thấy.
- KHÔNG XÁC ĐỊNH ĐƯỢC: không kiểm tra được, nêu lý do.
File tồn tại hoặc code tồn tại KHÔNG đủ để dùng nhãn ĐÃ CHẠY THẬT.

## Quy tắc
1. Bằng chứng là output lệnh của lượt này hoặc file:dòng. Không lấy báo cáo cũ hay trí nhớ làm bằng chứng; đọc lại file thật.
2. Quét từ thư mục gốc dự án, đủ cả ai_service, mobile_app, web_admin.
3. Không dùng phần trăm hoàn thành, không dùng từ tâng bốc.
4. Tách rõ "đã đo" (kèm con số, nguồn, điều kiện đo) và "mục tiêu". Chưa đo thì ghi "CẦN ĐO", không điền số ước chừng.
5. Mâu thuẫn giữa lời người dùng và thực tế trên đĩa: ưu tiên thực tế và nêu chỗ mâu thuẫn.
6. Không ghi nguyên nhân khi không có bằng chứng; chỉ ghi hiện tượng.
7. Che mật khẩu, hash, token, khóa, URL tunnel, thông tin cá nhân.
8. Nội dung đưa vào báo cáo đồ án (Word) tách khỏi bảng kiểm chứng nội bộ; không đưa file:dòng hay đường dẫn tệp vào phần Word.

## Mẫu kết thúc
ĐÃ LÀM (lệnh đã chạy, file đã đổi) / ĐÃ XÁC NHẬN (có output) / CHƯA XÁC NHẬN hoặc CẦN TÔI QUYẾT ĐỊNH.
