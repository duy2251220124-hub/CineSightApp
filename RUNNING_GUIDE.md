# HƯỚNG DẪN CHẠY TOÀN BỘ HỆ THỐNG CINESIGHT (A-Z)

Đây là tài liệu chuẩn để khởi động hệ thống CineSight gồm 3 thành phần: AI Server (Backend), Web Admin (Frontend) và Mobile App (Flutter). Hãy chạy tuần tự theo đúng các bước dưới đây để đảm bảo mọi thứ kết nối thành công.

---

### BƯỚC 1: Bật AI Server (Backend)

Server AI phải được bật ĐẦU TIÊN, vì nó là trung tâm xử lý. Nếu server không chạy, Web và Mobile đều sẽ báo lỗi "Network Error".

1. Mở Terminal (PowerShell) và gõ lệnh sau:
   ```powershell
   cd c:\CineSightApp\ai_service
   .\venv\Scripts\Activate.ps1
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Lưu ý: Bắt buộc phải kích hoạt `venv` (môi trường ảo) để có đủ thư viện AI (YOLO, FastAPI...). Tham số `host 0.0.0.0` giúp server nhận kết nối từ mọi thiết bị khác ngoài máy tính của bạn.*

2. **Cách xác nhận thành công:**
   - Mở trình duyệt web, gõ địa chỉ: `http://localhost:8000/`
   - Nếu bạn thấy màn hình trắng hiện dòng chữ `{"status":"CineSight AI Service đang chạy","version":"2.0.0"}` => Server đã sống. (Nếu không thấy, tuyệt đối không làm tiếp bước 2).

---

### BƯỚC 2: Bật Ngrok (Cầu nối Internet cho Mobile App)

Do Mobile App (chạy trên điện thoại hoặc máy ảo) cần đường dẫn Internet để chọc về máy tính của bạn, ta cần Ngrok tạo 1 "đường hầm" (tunnel).

1. Mở một cửa sổ Terminal THỨ 2:
   ```powershell
   cd c:\CineSightApp
   .\ngrok_bin\ngrok http 8000
   ```

2. **Cách xác nhận & lấy URL mới:**
   - Trong màn hình đen của ngrok, tìm dòng có chữ `Forwarding`. Bạn sẽ thấy link dạng `https://xxxx-xxxx.ngrok-free.app`.
   - **Mẹo kiểm tra chắc chắn:** Mở trình duyệt, vào `http://127.0.0.1:4040/api/tunnels`. Bạn sẽ thấy chi tiết cấu hình ngrok đang trỏ về đúng `localhost:8000`.
   
3. **Chỗ CẦN SỬA trong code Mobile:**
   - Copy link `https://...` ở trên.
   - Mở file: `c:\CineSightApp\mobile_app\lib\core\network\api_client.dart`
   - Tại **dòng 12** (`static const String baseUrl = '...';`), dán đè link mới vào. Lưu file lại.

---

### BƯỚC 3: Bật Web Admin (Frontend)

Trang quản trị chạy độc lập và sẽ giao tiếp trực tiếp với AI Server trên máy tính.

1. Mở cửa sổ Terminal THỨ 3:
   ```powershell
   cd c:\CineSightApp\web_admin
   npm run dev
   ```

2. **Cách xác nhận thành công:**
   - Vào link mà Vite cấp (thường là `http://localhost:5173`).
   - Mở **F12 (DevTools)** -> tab **Network**. Tải lại trang (F5).
   - Nhấn qua lại giữa các tab (Dashboard, Nhân sự...). Nếu không có thông báo đỏ nào hiện lên và danh sách nhân sự tải ra bình thường => Kết nối Web ↔ Server hoàn hảo.

---

### BƯỚC 4: Chạy Mobile App

1. Mở cửa sổ Terminal THỨ 4 (hoặc chạy trực tiếp qua VS Code / Android Studio):
   ```powershell
   cd c:\CineSightApp\mobile_app
   flutter run
   ```

2. **Xác nhận kết nối & Bắt lỗi:**
   - Quét thử 1 mã QR và bấm nút "Đồng bộ".
   - **Nếu lỗi:** Mở console/terminal của Flutter, tìm log có chữ `[NETWORK]`. Nó sẽ in ra chi tiết tại sao bị chặn (SocketException, Timeout, 404, 500...).

---

### MỤC 5: CÁC LỖI THƯỜNG GẶP & CÁCH NHẬN BIẾT

**Lỗi 1: Web Admin báo `Lỗi tải dữ liệu: Network Error`**
- *Triệu chứng:* Chuyển tab trên Web Admin là bị văng popup lỗi "Network Error". F12 Console báo lỗi CORS Policy hoặc `net::ERR_CONNECTION_REFUSED`.
- *Nguyên nhân:*
  - (CORS bị chặn): Nếu code Web Admin đang xài link Ngrok. Trình duyệt tự gửi request `OPTIONS` kiểm tra bảo mật, nhưng bị màn hình cảnh báo miễn phí của Ngrok chặn lại => Báo lỗi CORS.
  - (Refused): AI Server ở Bước 1 chưa được bật, hoặc bị sập ngầm.
- *Cách sửa:* Web Admin nên luôn trỏ về `http://localhost:8000` (đã fix trong `cineSightApi.js`). Nếu vẫn bị, quay lại Terminal 1 kiểm tra xem code server có đang báo lỗi sập chữ đỏ không.

**Lỗi 2: Mobile App bấm Đồng bộ nhưng không thấy lên dữ liệu**
- *Triệu chứng:* Bấm nút trên App nhưng check bên màn hình "Danh sách vé" của Web Admin không có gì mới. Log Flutter báo `SocketException` hoặc `Connection refused`.
- *Nguyên nhân:* URL Ngrok trong file `api_client.dart` (Dòng 12) đã cũ/hết hạn. Mỗi lần bật lại Ngrok (bản free), URL sẽ đổi. Code flutter đang gửi dữ liệu vào khoảng không.
- *Cách sửa:* Tắt Ngrok, bật lại, copy link mới cập nhật vào dòng 12 của `api_client.dart`, lưu lại và Hot Restart (Shift + R) app Flutter.

**Lỗi 3: AI Server báo lỗi `ModuleNotFoundError: No module named 'ultralytics'`**
- *Triệu chứng:* Terminal 1 văng đầy lỗi màu đỏ chữ trắng và sập ngay sau khi bạn gõ lệnh chạy uvicorn.
- *Nguyên nhân:* Bạn đang dùng Python của hệ thống chung, thay vì môi trường ảo của dự án. Hệ thống chung không có cài bộ nhận diện YOLO (ultralytics).
- *Cách sửa:* Bắt buộc chạy lệnh `.\venv\Scripts\Activate.ps1` trước để Terminal hiện chữ `(venv)` ở đầu, rồi mới chạy lệnh uvicorn.
