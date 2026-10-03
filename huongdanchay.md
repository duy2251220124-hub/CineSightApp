Created api_client.dart

Tôi hiểu rồi! Việc dùng Ngrok rất hợp lý nếu bạn muốn test bằng 4G hoặc khi điện thoại và máy tính không bắt chung một mạng Wi-Fi. 

Tôi đã sửa lại file `api_client.dart` sử dụng cấu hình URL của Ngrok. Tuy nhiên, do bản Ngrok miễn phí sẽ **thay đổi link mỗi lần bạn bật lại**, nên bạn cần làm theo đúng thứ tự dưới đây để toàn bộ hệ thống hoạt động trơn tru:

### HƯỚNG DẪN CHẠY DỰ ÁN CINESIGHT (TỪ A-Z)

Bạn cần mở **3 cửa sổ Terminal (PowerShell)** riêng biệt để chạy 3 thành phần của hệ thống.

#### Bước 1: Khởi động Server AI (Cửa sổ Terminal 1)
Mở cửa sổ dòng lệnh (Terminal) đầu tiên và gõ lần lượt các lệnh sau:
```powershell
cd c:\CineSightApp\ai_service
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
👉 *Lúc này Backend AI đã chạy tại cổng 8000 trên máy tính của bạn.*

#### Bước 2: Bật Ngrok để đẩy Server ra Internet (Cửa sổ Terminal 2)
Mở cửa sổ Terminal thứ 2 và gõ:
```powershell
.\ngrok_bin\ngrok http 8000
```
- Trên màn hình đen của Ngrok, bạn sẽ thấy một dòng có chữ `Forwarding`. 
- Hãy **Copy cái link HTTPS** ở dòng đó (Nó trông giống như `https://abcd-1234.ngrok-free.app`).

#### Bước 3: Gắn link Ngrok vào App và chạy App (Chỉnh sửa Code)
1. Bạn mở file `c:\CineSightApp\mobile_app\lib\core\network\api_client.dart` (tôi vừa chỉnh sửa lại file này xong).
2. Dán đè cái link Ngrok bạn vừa copy vào biến `baseUrl` ở dòng số **10**. 
   *(Hiện tại tôi đang để sẵn link cũ của bạn là `https://quill-device-deny.ngrok-free.dev`, bạn nhớ thay bằng link mới của ngày hôm nay nhé).*
3. Sau khi lưu file, bạn có thể chạy App Flutter lên điện thoại thật hoặc máy ảo như bình thường:
```powershell
cd c:\CineSightApp\mobile_app
flutter run
```

#### Bước 4: Chạy Web Admin (Cửa sổ Terminal 3) (Dành cho sau này)
Mở cửa sổ Terminal thứ 3:
```powershell
cd c:\CineSightApp\web_admin
npm run dev
```
👉 *Truy cập `http://localhost:5173` trên trình duyệt máy tính để xem màn hình quản lý rạp.*

---
**Luồng hoạt động sẽ diễn ra như sau:**
Khi bạn mở app trên điện thoại (dù đang xài 4G) -> Quét vé -> Bấm lưu -> App sẽ bắn dữ liệu qua link Ngrok -> Chạy thẳng vào cái Terminal 1 (AI Server) ở nhà bạn -> Lưu vào Database!

Bạn thao tác thử các bước trên xem Ngrok đã nhảy ra link mới và app đẩy dữ liệu thành công chưa nhé. Có khó khăn ở bước nào cứ nhắn tôi!

.\ngrok_bin\ngrok http 8000
