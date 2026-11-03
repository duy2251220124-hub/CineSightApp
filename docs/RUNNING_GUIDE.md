
 ### Bật AI Server (Backend)

1. Mở Terminal (PowerShell) và gõ lệnh sau:
   ```powershell
   cd c:\CineSightApp\ai_service
   
   .\venv\Scripts\Activate.ps1
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Bật Ngrok (Cầu nối Internet cho Mobile App)

Do Mobile App (chạy trên điện thoại hoặc máy ảo) cần đường dẫn Internet để chọc về máy tính của bạn, ta cần Ngrok tạo 1 "đường hầm" (tunnel).

1. Mở một cửa sổ Terminal THỨ 2:
   ```powershell
   cd c:\CineSightApp
   .\ngrok_bin\ngrok http 8000
---

### Bật Web Admin (Frontend)

Trang quản trị chạy độc lập và sẽ giao tiếp trực tiếp với AI Server trên máy tính.

1. Mở cửa sổ Terminal THỨ 3:
   ```powershell
   cd c:\CineSightApp\web_admin
   npm run dev
   ```
### Chạy Mobile App

1. Mở cửa sổ Terminal THỨ 4 (hoặc chạy trực tiếp qua VS Code / Android Studio):
   ```powershell
   cd c:\CineSightApp\mobile_app
   flutter run


---
### update lịch phim mới cho adminweb
   cd C:\CineSightApp
python ai_service/tools/auto_update_movies.py

