---
description: Kiểm tra nhanh sau khi sửa code (git status, test backend, analyze Flutter, lint và build web, gọi thử API)
---
1. Chạy `git status --short`, liệt kê file thay đổi và đối chiếu với phạm vi yêu cầu. Báo file nằm ngoài phạm vi.
2. Nếu file trong ai_service đổi: `cd ai_service; .\venv\Scripts\python.exe -m unittest discover -s tests -v`. Dán output.
3. Nếu file trong mobile_app đổi: `cd mobile_app; flutter analyze; flutter test`. Dán số issue và kết quả test.
4. Nếu file trong web_admin đổi: `cd web_admin; npm run lint; npm run build`. Dán output.
5. Nếu endpoint đổi: gọi thử bằng đúng payload của client, dán status và body (che bí mật).
6. Báo cáo theo mẫu ĐÃ LÀM / ĐÃ XÁC NHẬN / CHƯA XÁC NHẬN. Không nói "xong" nếu có bước lỗi.
