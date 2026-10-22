
### BƯỚC 1: Bật AI Server (Backend)

1. Mở Terminal (PowerShell) và gõ lệnh sau:
   ```powershell
   cd c:\CineSightApp\ai_service
   
   .\venv\Scripts\Activate.ps1
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

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
   
---

### BƯỚC 3: Bật Web Admin (Frontend)

Trang quản trị chạy độc lập và sẽ giao tiếp trực tiếp với AI Server trên máy tính.

1. Mở cửa sổ Terminal THỨ 3:
   ```powershell
   cd c:\CineSightApp\web_admin
   npm run dev
   ```
### BƯỚC 4: Chạy Mobile App

1. Mở cửa sổ Terminal THỨ 4 (hoặc chạy trực tiếp qua VS Code / Android Studio):
   ```powershell
   cd c:\CineSightApp\mobile_app
   flutter run


---


