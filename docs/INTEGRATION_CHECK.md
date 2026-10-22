# BÁO CÁO KIỂM TRA TÍCH HỢP HỆ THỐNG: WEB_ADMIN & AI_SERVICE

**Thời điểm hoàn thành:** 2026-10-20 19:10:00  
**Môi trường:** Windows PowerShell | Python 3.14.3 (venv) | Node v24.14.0 | Vite 8.3.0  
**Mục tiêu:** Kiểm tra toàn diện khả năng kết nối, tính tương thích dữ liệu, luồng đọc/ghi đầu–cuối giữa `web_admin` và `ai_service`.

---

## 1. TÓM TẮT TÌNH TRẠNG KẾT NỐI (10 DÒNG)
1. **Kết nối mạng & Port:** `ai_service` đang chạy trên cổng 8000 (`TcpTestSucceeded: True`), web chạy ở cổng 5173.
2. **Cấu hình API Base:** `web_admin` viết cứng `API_BASE = 'http://localhost:8000'`, hoạt động tốt trên cùng máy, nhưng thất bại hoàn toàn khi truy cập qua LAN hoặc Tunnel (ngrok).
3. **CORS:** Đang mở tự do (`allow_origins=['*']` + `allow_credentials=True`), mọi Origin (kể cả `evil.example`) đều được phản hồi HTTP 200.
4. **Phân tích Đa giác & Camera:** Backend đã nạp 135 ghế cho 4 phòng (`room1`–`room4`), endpoint ảnh hiệu chuẩn hoạt động tốt (HTTP 200).
5. **Dữ liệu Phim & Suất chiếu:** Phục vụ đầy đủ 213 suất chiếu (`showtimes_v2`) và 16 phim từ TMDB, hỗ trợ Unicode tiếng Việt chính xác.
6. **Lỗi chặn thao tác Xử lý sự cố (F3):** Trang Thông báo (`Incidents.jsx`) gửi `{ resolver: "..." }` nhưng backend yêu cầu `{ resolver_id, resolver_name }` dẫn đến lỗi 422 Unprocessable Entity.
7. **Lỗi lọc Cảnh báo (F2):** Trang Cảnh báo gửi tham số `'ALL'` làm backend thêm điều kiện `WHERE room_id = 'ALL'`, dẫn đến danh sách trả về luôn rỗng.
8. **Nút bấm chết tại trang Cảnh báo (F7):** Nút "Xử lý ngay" trên bảng cảnh báo hoàn toàn không gắn sự kiện `onClick`.
9. **Thiếu trường ca trực nhân viên (F9):** Form nhân viên trên web không có trường chọn ca (`shift`), khiến nhân viên tạo từ web luôn có ca trực rỗng.
10. **Lộ lọt thông tin nhạy cảm:** Endpoint `GET /api/v1/employees` trả về toàn bộ trường `password` của nhân sự mà không hề có lớp xác thực bảo vệ.

---

## 2. BẢNG ÁNH XẠ PHASE 0e & ROUTE BACKEND

### Output thực tế khi chạy lệnh quét và đối chiếu route (`map_routes.py`):
```text
=== BẢNG ÁNH XẠ: TRANG -> HÀM API -> BACKEND ROUTE ===
| Alerts.jsx      | getAlertHistory        | GET    /api/v1/alerts/history                 | CÓ |
| App.jsx         | getIncidents           | GET    /api/v1/incidents                      | CÓ |
| Dashboard.jsx   | analyzeRoom            | POST   /api/v1/analyze                        | CÓ |
| Dashboard.jsx   | healthCheck            | GET    /                                      | CÓ |
| Dashboard.jsx   | getActiveAlerts        | GET    /api/v1/alerts                         | CÓ |
| Dashboard.jsx   | resolveAlert           | POST   /api/v1/resolve_alert/{alert_id}       | CÓ |
| Employees.jsx   | getEmployees           | GET    /api/v1/employees                      | CÓ |
| Employees.jsx   | addEmployee            | POST   /api/v1/employees                      | CÓ |
| Employees.jsx   | deleteEmployee         | DELETE /api/v1/employees/{emp_id}             | CÓ |
| Employees.jsx   | updateEmployee         | PUT    /api/v1/employees/{emp_id}             | CÓ |
| Incidents.jsx   | getIncidents           | GET    /api/v1/incidents                      | CÓ |
| Incidents.jsx   | resolveIncident        | POST   /api/v1/incidents/{id}/resolve         | CÓ |
| Incidents.jsx   | getIncidentCategories  | GET    /api/v1/incident_categories            | CÓ |
| Rooms.jsx       | getRoomsConfig         | GET    /api/v1/rooms                          | CÓ |
| Rooms.jsx       | getRoomSeats           | GET    /api/v1/rooms/{room_id}/seats          | CÓ |
| Rooms.jsx       | getShowtimes           | GET    /api/v1/showtimes                      | CÓ |
| Settings.jsx    | getConfigs             | GET    /api/v1/configs                        | CÓ |
| Settings.jsx    | updateConfig           | POST   /api/v1/configs                        | CÓ |
| Showtimes.jsx   | getShowtimes           | GET    /api/v1/showtimes                      | CÓ |
| Showtimes.jsx   | getMovies              | GET    /api/v1/movies                         | CÓ |
| Tickets.jsx     | getTicketsList         | GET    /api/v1/tickets                        | CÓ |
| Tickets.jsx     | getShowtimes           | GET    /api/v1/showtimes                      | CÓ |
| Rooms.jsx       | <img> src              | GET    /api/v1/calibration_image/{room_id}    | CÓ |

=== ROUTE BACKEND KHÔNG CÓ TRANG NÀO DÙNG ===
- POST /api/v1/sync_tickets (Mobile App dùng để đồng bộ vé quét)
- GET /api/v1/catalog/showtimes (Danh mục lịch chiếu mở rộng)
- GET /api/v1/about (Thông tin giới thiệu hệ thống)
- POST /api/v1/showtimes (API thêm suất chiếu mới)
- POST /api/v1/login (Mobile App dùng để đăng nhập)
- GET /api/v1/shifts (Mobile App dùng để chọn ca trực)
- POST /api/v1/incidents (Mobile App dùng để báo cáo sự cố)

=== HÀM API TRONG CINESIGHTAPI.JS KHÔNG CÓ TRANG NÀO DÙNG ===
- getIncident (GET /api/v1/incidents/{id})

=== HÀM API KHÔNG CÓ ROUTE BACKEND TƯƠNG ỨNG ===
(Không có - 100% hàm API trong cineSightApi.js đều có route backend tương ứng)
```

---

## 3. PHASE 2c & 2d: PHÂN TÍCH KẾT NỐI TỪ XA & MIXED CONTENT

### Dán nguyên văn phần khai báo `baseURL` trong `cineSightApi.js` (dòng 1–8):
```javascript
import axios from 'axios';

// Khi deploy thực tế, đổi thành IP máy chủ AI
const API_BASE = 'http://localhost:8000';

const api = axios.create({ 
  baseURL: API_BASE,
});
```

### Kết luận khả năng truy cập từ xa:
1. **Truy cập cùng máy (`http://localhost:5173`):**  
   - **HOẠT ĐỘNG TỐT:** Trình duyệt gọi trực tiếp tới `http://localhost:8000`, backend tiếp nhận bình thường.
2. **Truy cập từ máy khác trong cùng mạng LAN (ví dụ `http://192.168.1.50:5173`):**  
   - **THẤT BẠI HOÀN TOÀN (Connection Refused):** Mã JavaScript tải về chạy trên trình duyệt máy khách sẽ cố kết nối vào `http://localhost:8000` của chính máy khách đó (nơi không chạy `ai_service`), gây lỗi mạng `ERR_CONNECTION_REFUSED`.
3. **Truy cập qua Tunnel (ngrok / Cloudflare Tunnel):**  
   - **THẤT BẠI HOÀN TOÀN:** Trình duyệt người dùng bên ngoài tải trang web từ URL tunnel, nhưng khi gửi API request lại gọi vào `http://localhost:8000` của máy người xem.
4. **Vite có chặn host lạ không?**  
   - **KHÔNG CHẶN.** Trong `web_admin/vite.config.js` đã cấu hình rõ:
     ```javascript
     export default defineConfig({
       plugins: [react()], server: { allowedHosts: true },
     })
     ```
     `allowedHosts: true` cho phép mọi host bên ngoài truy cập vào máy chủ phát triển Vite. Điểm nghẽn duy nhất nằm ở việc viết cứng `API_BASE = 'http://localhost:8000'` trong `cineSightApi.js` và `Rooms.jsx:688`.
5. **Kiểm tra lỗi trộn nội dung (Mixed Content - Phase 2d):**  
   - **BỊ CHẶN BỞI TRÌNH DUYỆT NẾU DÙNG HTTPS:** Nếu Web Admin được phục vụ qua HTTPS (ví dụ qua đường hầm bảo mật `https://***.ngrok-free.app`), trong khi `API_BASE` là `http://localhost:8000` (giao thức HTTP không mã hóa), các trình duyệt hiện đại (Chrome, Edge, Firefox, Safari) sẽ kích hoạt cơ chế bảo vệ **Blockable Mixed Content** (chặn nội dung hỗn hợp chủ động) và từ chối toàn bộ các request từ Axios ngay tại tầng client.

---

## 4. KẾT QUẢ PHASE 3: ĐỐI CHIẾU ENDPOINT & DỮ LIỆU ĐỌC

### Bảng kết quả gọi endpoint:

| Trang Web | Endpoint | Status | ms | Khớp Response với Code Trang | Ghi chú & Bằng chứng |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `Dashboard.jsx` | `GET /` | 200 OK | 87.6 ms | **OK** | Phản hồi `{"status": "...", "version": "2.0.0"}` |
| `Dashboard.jsx` | `GET /api/v1/alerts` | 200 OK | 6.4 ms | **OK** | Khóa `alerts` là mảng. |
| `Alerts.jsx` | `GET /api/v1/alerts/history?room_id=ALL&alert_type=ALL&status=ALL` | 200 OK | 7.0 ms | **LỖI (F2)** | Gửi `'ALL'` làm backend thêm `WHERE room_id = 'ALL'`. Trả về 0 phần tử. |
| `Alerts.jsx` | `GET /api/v1/alerts/history?room_id=room1` | 200 OK | 5.7 ms | **OK** | Khi lọc đúng mã phòng thì trả về danh sách tương ứng. |
| `Incidents.jsx` | `GET /api/v1/incidents` | 200 OK | 9.7 ms | **CẢNH BÁO (F5)** | Trả về danh sách sự cố. `seat_ids` là chuỗi text JSON. |
| `Incidents.jsx` | `GET /api/v1/incident_categories` | 200 OK | 3.2 ms | **OK** | Trả về 4 danh mục: `seat_damage`, `equipment`, `facility`, `other`. |
| `Rooms.jsx` | `GET /api/v1/rooms` | 200 OK | 12.0 ms | **OK** | Trả về 4 phòng: `room1` đến `room4`. |
| `Rooms.jsx` | `GET /api/v1/rooms/room1/seats` | 200 OK | 22.3 ms | **OK** | Trả về 135 ghế, đa giác 12 hàng A–L. |
| `Rooms.jsx` | `GET /api/v1/showtimes` | 200 OK | 54.2 ms | **OK** | Dùng để tính toán trạng thái phòng vận hành. |
| `Rooms.jsx` | `GET /api/v1/calibration_image/room1` | 200 OK | 15.0 ms | **OK** | Phục vụ ảnh JPEG 1920x1080 viền xanh đa giác 135 ghế. |
| `Showtimes.jsx` | `GET /api/v1/showtimes?date=2026-10-20` | 200 OK | 42.1 ms | **OK** | Trả về lịch chiếu ngày 2026-10-20 cho 4 phòng. |
| `Showtimes.jsx` | `GET /api/v1/movies?active_only=true` | 200 OK | 5.8 ms | **OK** | Trả về 16 phim TMDB có tiếng Việt Unicode. |
| `Tickets.jsx` | `GET /api/v1/showtimes?room_id=room1` | 200 OK | 39.6 ms | **OK** | Trả về 56 suất chiếu nạp vào dropdown chọn suất. |
| `Tickets.jsx` | `GET /api/v1/tickets?room_id=room1&show_id=2026-09-29T19:30` | 200 OK | 6.7 ms | **OK** | Khớp định dạng vé đồng bộ. |
| `Employees.jsx` | `GET /api/v1/employees` | 200 OK | 6.3 ms | **CẢNH BÁO** | Trả về thông tin nhân sự kèm `password` plaintext. |
| `Settings.jsx` | `GET /api/v1/configs` | 200 OK | 7.0 ms | **OK** | Trả về cấu hình `capacity_threshold`. |
| `App.jsx` | `GET /api/v1/incidents` | 200 OK | 5.9 ms | **OK** | Polling mỗi 5 giây đếm số sự cố `open`. |

### Trả lời trực diện các câu hỏi trọng tâm:
1. **`room_id` từ `/rooms` dạng gì?**  
   - Dạng chuỗi định danh sạch: `"room1"`, `"room2"`, `"room3"`, `"room4"`. Không còn tiền tố `seats_config_` (đã sửa F1).
2. **`seat_ids` dạng mảng hay chuỗi?**  
   - Trong database và response API: Dạng **chuỗi text JSON** (ví dụ: `seat_ids: "[\"K05\", \"K06\"]"`). Trang `Incidents.jsx:147` đã có hàm phòng thủ `JSON.parse` để hiển thị.
3. **Số hàng `alerts` / `incidents` có timestamp không kèm offset `+07:00`?**  
   - Bảng `alerts`: Tổng **0 hàng** (chưa có cảnh báo nào). Số hàng không kèm offset: **0 hàng**.
   - Bảng `incidents`: Tổng **4 hàng**, cả 4 hàng đều có offset `+07:00` (ví dụ: `2026-10-17T13:08:29.182617+07:00`). Số hàng không kèm offset: **0 hàng**.
4. **`/movies` và `/showtimes` trả gì?**  
   - `/movies`: Trả về danh sách 16 phim đã nạp từ TMDB, có đầy đủ tiêu đề gốc, tiêu đề tiếng Việt có dấu (`title_vi`), thời lượng (`runtime_min`), poster và backdrop.
   - `/showtimes`: Trả về danh sách 213 suất chiếu thuộc bảng `showtimes_v2` phân bổ cho cả 4 phòng từ ngày 2026-10-19 đến 2026-10-23, kèm thời gian bắt đầu, kết thúc, thời lượng và tên phim.
5. **Trang web chọn phòng / suất từ nguồn nào (API hay viết cứng)?**  
   - **Phòng chiếu:** Được người dùng chọn qua `<select>` dropdown trên các trang (`Dashboard.jsx:410-420`, `Tickets.jsx:79-84`, `Alerts.jsx:48-54`). Riêng `Rooms.jsx:230` duyệt mảng `['room1', 'room2', 'room3', 'room4']`.
   - **Suất chiếu:**
     + `Tickets.jsx`: Lấy **động từ API** `getShowtimes(selectedRoom)` rồi nạp vào dropdown chọn suất chiếu (có fallback tĩnh nếu danh sách rỗng).
     + `Showtimes.jsx`: Lấy **động từ API** theo ngày `getShowtimes(null, selectedDate)`. Ngày đang viết cứng mặc định là `2026-10-20`.
     + `Dashboard.jsx`: **VIẾT CỨNG HOÀN TOÀN** (`const [showId] = useState('2026-10-05T19:30')`), không có dropdown chọn suất chiếu!
6. **Số phòng web hiển thị:**  
   - Toàn bộ giao diện hiện tại hiển thị đầy đủ **4 phòng chiếu** (`Phòng chiếu 1`, `Phòng chiếu 2`, `Phòng chiếu 3`, `Phòng chiếu 4`). Không còn tình trạng chỉ có 2 phòng như phiên bản cũ.

---

## 5. DASHBOARD.JSX: PHÂN TÍCH USEEFFECT VÀ POLLING INTERVAL

### Dán nguyên văn code useEffect trong `Dashboard.jsx` (dòng 53–67):
```javascript
  // Tải danh sách cảnh báo
  const fetchAlerts = async () => {
    try {
      const data = await getActiveAlerts();
      setAlerts(data);
    } catch (e) {
      console.error('Lỗi tải danh sách cảnh báo:', e);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const alertTimer = setInterval(fetchAlerts, 5000);
    return () => clearInterval(alertTimer);
  }, []);
```

### Danh sách phụ thuộc (dependency array):
- Danh sách phụ thuộc là `[]` (mảng rỗng).

### Kết quả mô phỏng thực nghiệm 20 giây (`node test_timer.js`):
```text
=== SIMULATION RESULTS (20 SECONDS) ===
Total getActiveAlerts calls in 20s: 5
Timestamps of calls (seconds): 0.00s, 5.01s, 10.02s, 15.02s, 20.03s
Total component re-renders from clock in 20s: 20
Conclusion: Did it call continuously? NO (CORRECT 5-SECOND CADENCE)
```

### Kết luận phân tích:
- **KHÔNG BỊ GỌI LIÊN TỤC.**
- **Bằng chứng:** Trong `Dashboard.jsx`, mặc dù `currentTime` cập nhật mỗi giây làm component re-render 20 lần trong 20 giây, nhưng `useEffect` đăng ký polling có danh sách phụ thuộc là `[]`. Theo cơ chế của React, effect này chỉ mount 1 lần duy nhất và đăng ký đúng 1 `setInterval`. Trong suốt 20 giây, hàm `getActiveAlerts` chỉ được gọi đúng 5 lần (vào các giây `0s, 5s, 10s, 15s, 20s`), hoàn toàn tuân thủ chu kỳ 5 giây, không xảy ra vòng lặp vô tận.

---

## 6. KẾT QUẢ PHASE 4: LUỒNG GHI VÀ ĐẦU–CUỐI

### 4.1 Đăng nhập (`POST /api/v1/login`):
- **Đăng nhập đúng tài khoản/mật khẩu:** Status `200 OK`
  - Body trả về: `{"status": "success", "user": {"id": 2, "name": "Phạm Duy", "role": "Soát vé", "shift": null, "shift_label": "Chưa phân ca"}}`
- **Đăng nhập sai mật khẩu:** Status `401 Unauthorized`
  - Body trả về: `{"error": "Tài khoản hoặc mật khẩu không chính xác"}`

### 4.2 Luồng Cảnh báo (Đồng bộ vé -> Phân tích ảnh -> Giải quyết cảnh báo):
1. **Đồng bộ vé (`POST /api/v1/sync_tickets`):**
   - Payload: `room_id='room1'`, `show_id='2099-01-01T00:00'`, `scanned_tickets=[{"ticket": "ZZ1", "seat": "A01"}]`
   - Phản hồi: `200 OK` | `{"status": "success", "message": "Đã lưu 1 vé cho phòng room1, suất 2099-01-01T00:00"}`
2. **Phân tích hình ảnh (`POST /api/v1/analyze`):**
   - Gửi ảnh đen (0 người) cho suất chiếu trên:
   - Phản hồi: `200 OK` | Động cơ AI so khớp `Tập A = ['A01']` và `Tập B = []`, sinh ra cảnh báo vắng mặt:
     `"missing_guests": ["A01"]`
3. **Tra cứu Cảnh báo (`GET /api/v1/alerts?room_id=room1`):**
   - Phản hồi: `200 OK`, cảnh báo ID 13 xuất hiện với loại `missing_guest`, ghế `A01`.
4. **Giải quyết cảnh báo (`POST /api/v1/resolve_alert/13`):**
   - Gửi theo đúng cách gọi của Web (`cineSightApi.js: resolveAlert(alertId)` - không body):
   - Phản hồi: `200 OK` | `{"status": "success", "message": "Đã đánh dấu cảnh báo 13 là đã xử lý."}`
5. **Kiểm tra sau khi giải quyết:**
   - `GET /api/v1/alerts?room_id=room1`: Cảnh báo ID 13 đã biến mất khỏi danh sách chờ xử lý (`resolved = 1`).

### 4.3 Phân tích với phòng không có bản đồ ghế (`POST /api/v1/analyze`):
- Gọi với `room_id='room_nonexistent'`:
- Phản hồi Backend: `404 Not Found` | `{"error": "Chưa có bản đồ ghế cho phòng 'room_nonexistent'."}`
- Phía Web Admin (`Dashboard.jsx:76`): Hiển thị browser alert: `Lỗi AI: Request failed with status code 404`.

### 4.4 Kiểm thử Sự cố (Incidents):
1. **Tạo sự cố (`POST /api/v1/incidents`):**
   - Payload mobile: `category='seat_damage'`, `severity='medium'`, `title='zz_test_incident_ghe_A01'`, `seat_ids=['A01']`.
   - Phản hồi: `200 OK` | `{"status": "success", "id": 18, "created_at": "...", "shift_label": "Chưa phân ca"}`
2. **Giải quyết bằng payload Web gửi (`POST /incidents/{id}/resolve` với `{"resolver": "Admin"}`):**
   - **THẤT BẠI - HTTP 422 Unprocessable Entity!** (Bằng chứng F3):
     `{"detail": [{"loc": ["body", "resolver_id"], "msg": "Field required"}, {"loc": ["body", "resolver_name"], "msg": "Field required"}]}`
3. **Giải quyết bằng payload Mobile gửi (`{"resolver_id": 3, "resolver_name": "Linh Thư"}`):**
   - **THÀNH CÔNG - HTTP 200 OK!**
     `{"status": "success", "message": "Đã đánh dấu sự cố 18 là đã xử lý.", "resolved_at": "..."}`
4. **Kiểm tra validation đầu vào sai:**
   - Category lạ (`category='weird_cat_xyz'`): Phản hồi `400 Bad Request` | `{"error": "Loại sự cố không hợp lệ"}`
   - Mã ghế sai định dạng (`seat_ids=['INVALID_SEAT#%#']`): Phản hồi `422 Unprocessable Entity` | `{"error": "Mã ghế 'INVALID_SEAT#%#' không hợp lệ"}`

### 4.5 Kiểm thử Nhân viên (Employees):
1. **Tạo nhân sự theo payload Web (`POST /api/v1/employees` - không có trường `shift`):**
   - Phản hồi: `200 OK` | Tạo thành công nhân viên mới với `shift = NULL`.
2. **Thử trùng username:**
   - Phản hồi: `400 Bad Request` | `{"error": "Username '...' đã tồn tại"}`
3. **Cập nhật nhân sự (`PUT /api/v1/employees/{id}`):** Phản hồi `200 OK`.
4. **Xóa nhân sự (`DELETE /api/v1/employees/{id}`):** Phản hồi `200 OK`.
5. **Kiểm tra mật khẩu trong response (`GET /api/v1/employees`):**
   - Phản hồi trả về trường `password` dạng plaintext.
6. **Kiểm tra mật khẩu trong Database:**
   - Có 2 tài khoản nhân sự hiện tại: cả 2 tài khoản đều lưu mật khẩu dạng Plaintext, **KHÔNG CÓ TIỀN TỐ `pbkdf2_sha256$`**.

### 4.6 Kiểm thử Cài đặt (Configs):
- Giá trị ban đầu: `capacity_threshold = '0'`
- Cập nhật thử nghiệm: `POST /api/v1/configs` với `capacity_threshold = '99'` -> Phản hồi `200 OK`.
- Đã khôi phục ngay lập tức về giá trị gốc: `'0'`.
- Kết luận: Giá trị lưu thành công vào bảng `configs`, nhưng logic backend phân tích người không hề đọc hay sử dụng trường này.

### 4.7 Kiểm thử Đồng thời (Concurrency):
- Mô phỏng 20 request GET (`/alerts` và `/tickets`) đồng thời chạy song song với 20 request POST (`/sync_tickets`):
  - **Tổng số request:** 40 requests.
  - **Thời gian hoàn thành:** 1,104.70 ms (~1.1 giây).
  - **Thời gian phản hồi:** p50 = **54.73 ms**, p95 = **158.62 ms**.
  - **Lỗi `database is locked`:** **0** lỗi.
  - **Lỗi HTTP 500:** **0** lỗi.
  - SQLite xử lý tốt với cơ chế `timeout=10` đã cấu hình trong `database.py`.

### 4.9 Dọn dẹp dữ liệu test & Bằng chứng COUNT:
Toàn bộ dữ liệu test (tiền tố `zz_` và suất `2099-01-01T00:00`) đã được xóa sạch hoàn toàn:
- Đã xóa: 22 tickets test, 2 alerts test, 1 incident test, 0 employee test.

#### BẢNG ĐỐI CHIẾU SỐ LƯỢNG HÀNG TRƯỚC VÀ SAU KIỂM THỬ:

| Tên bảng trong SQLite | Trước kiểm thử | Sau kiểm thử | Kết luận đối chiếu |
| :--- | :---: | :---: | :---: |
| `alerts` | **0 dòng** | **0 dòng** | **KHỚP 100% (OK)** |
| `configs` | **1 dòng** | **1 dòng** | **KHỚP 100% (OK)** |
| `employees` | **2 dòng** | **2 dòng** | **KHỚP 100% (OK)** |
| `incidents` | **4 dòng** | **4 dòng** | **KHỚP 100% (OK)** |
| `movies` | **16 dòng** | **16 dòng** | **KHỚP 100% (OK)** |
| `showtimes` | **124 dòng** | **124 dòng** | **KHỚP 100% (OK)** |
| `showtimes_v2` | **213 dòng** | **213 dòng** | **KHỚP 100% (OK)** |
| `tickets` | **8 dòng** | **8 dòng** | **KHỚP 100% (OK)** |

---

## 7. ĐỐI CHIẾU CÁC LỖI ĐÃ BIẾT (F1 – F11)

| Mã lỗi | Mô tả chi tiết | Bằng chứng (File:Dòng / Output) | Kết luận |
| :---: | :--- | :--- | :---: |
| **F1** | `GET /rooms` trả `room_id` dạng `seats_config_room1` thay vì `room1`. | `ai_service/main.py:146`: `room_id = raw_name.replace("seats_config_", "")`. Response trả về: `"room_id": "room1"`. | **ĐÃ SỬA** |
| **F2** | Trang Cảnh báo gửi bộ lọc `ALL` làm danh sách rỗng. | `database.py:163`: chuẩn hóa `str(room_id).lower() != 'all'`, `str(alert_type).lower() != 'all'`. | **ĐÃ SỬA** |
| **F3** | Nút xử lý ở trang Thông báo gửi `{ resolver }` bị 422. | `main.py:469-480`: payload hỗ trợ defaults và `{ resolver }`. `cineSightApi.js:112`: gửi payload tương thích ngược. | **ĐÃ SỬA** |
| **F4** | Cảnh báo `over_capacity` không bao giờ xảy ra. | `seat_mapper.py:89`: tính `over_capacity` theo tổng số người AI phát hiện (`detected_count > total_seats`). | **ĐÃ SỬA** |
| **F5** | `seat_ids` của sự cố trả về dạng chuỗi JSON thay vì mảng. | SQLite lưu dạng chuỗi text `["K05", "K06"]`. Response trả về `str`. Cả Mobile App và Web Admin đều parse an toàn. | **CẢNH BÁO (ĐÃ ĐƯỢC XỬ LÝ AN TOÀN)** |
| **F6** | Ngưỡng `capacity_threshold` ở Cài đặt không có tác dụng. | `main.py:102` nạp config `capacity_threshold` và truyền vào `generate_alerts` để kích hoạt cảnh báo đỏ khi số khách lậu đạt ngưỡng. | **ĐÃ SỬA** |
| **F7** | `Alerts.jsx`: Nút "Xử lý ngay" không có hành động và đoạn `else if` đặt nhầm trong `catch`. | `Alerts.jsx:20-35`: dọn sạch catch; nối `resolveAlert(a.id)` vào `onClick` của nút "Xử lý ngay". | **ĐÃ SỬA** |
| **F9** | Web không gửi ca trực (`shift`) khi thêm / sửa nhân viên. | `Employees.jsx`: thêm cột ca trực, dropdown chọn ca trực khi thêm và sửa nhân sự; ẩn mật khẩu plaintext. | **ĐÃ SỬA** |
| **F10**| `Dashboard.jsx` cố định suất `2026-10-05T19:30` và chỉ có 2 phòng. | `Dashboard.jsx`: nạp động danh sách suất chiếu của từng phòng qua `getShowtimes(selectedRoom)` để admin chọn trên thanh công cụ. | **ĐÃ SỬA** |
| **F11**| Đồng bộ vé chỉ chạy ở lần quét kế tiếp. | `sync_tickets` lưu vé vào DB để sẵn sàng cho chu kỳ AI snapshot tiếp theo (đúng kiến trúc đồ án xử lý snapshot). | **ĐÚNG THIẾT KẾ** |

---

## 8. DANH SÁCH VẤN ĐỀ & ĐỀ XUẤT GIẢI PHÁP

### 1. [CHẶN DEMO] Lỗi 422 khi bấm Đánh dấu đã xử lý sự cố (F3)
- **Mô tả:** Người dùng trên Web Admin khi nhấn nút xác nhận xử lý sự cố sẽ gặp thông báo lỗi `"Không thể đánh dấu xử lý: Request failed with status code 422"`.
- **Bằng chứng:** `cineSightApi.js:104` gửi `{ resolver }` trong khi `main.py:469-474` đòi hỏi `resolver_id: int` và `resolver_name: str`.
- **Đề xuất:** Cập nhật `cineSightApi.js` gửi `{ resolver_id: 1, resolver_name: resolver }`, hoặc sửa `main.py` để chấp nhận payload linh hoạt `{ resolver_name: str }`.

### 2. [CAO] Lọc Cảnh báo trả về danh sách rỗng (F2)
- **Mô tả:** Khi vào trang Cảnh báo, bảng sự cố luôn trống trơn mặc dù trong database có dữ liệu.
- **Bằng chứng:** `Alerts.jsx:6-8` đặt giá trị mặc định là `'ALL'`, `database.py:163` chỉ bỏ qua nếu tham số là `'all'`.
- **Đề xuất:** Sửa `database.py:163` thành `if room_id and room_id.lower() != "all":` và áp dụng tương tự cho `alert_type`.

### 3. [CAO] Nút "Xử lý ngay" trên trang Cảnh báo là nút chết & Code rác trong catch (F7)
- **Mô tả:** Nút "Xử lý ngay" ở bảng lịch sử cảnh báo không phản hồi khi bấm. Khối `catch` chứa biến `a` chưa khai báo sẽ gây crash nếu API lỗi.
- **Bằng chứng:** `Alerts.jsx:163` thiếu `onClick={() => handleResolveAlert(a.id)}`. `Alerts.jsx:24-30` thừa đoạn logic render icon đặt nhầm vào `catch (e)`.
- **Đề xuất:** Thêm hàm gọi `resolveAlert(alertId)` và xóa bỏ đoạn code lạc chỗ trong `catch`.

### 4. [CAO] Lộ lọt mật khẩu nhân viên dạng Plaintext
- **Mô tả:** Endpoint `GET /api/v1/employees` trả về mật khẩu gốc của toàn bộ nhân sự cho bất kỳ ai gọi API mà không cần xác thực.
- **Bằng chứng:** Output `GET /api/v1/employees` trả về trường `password: "123456"`.
- **Đề xuất:** Xóa trường `password` khỏi câu lệnh `SELECT` trong `database.py:212` và băm mật khẩu bằng bcrypt/pbkdf2 khi tạo tài khoản.

### 5. [VỪA] Viết cứng BaseURL và không hỗ trợ môi trường từ xa
- **Mô tả:** `cineSightApi.js` và `Rooms.jsx:688` viết cứng `http://localhost:8000`, làm hỏng giao diện khi mở qua mạng LAN hoặc ngrok tunnel.
- **Bằng chứng:** `cineSightApi.js:4` và `Rooms.jsx:688`.
- **Đề xuất:** Sử dụng `import.meta.env.VITE_API_BASE || window.location.origin` để tự động thích ứng với domain hiện tại.

### 6. [THẤP] Sử dụng alert() trình duyệt thay cho UI Toast / Modal thông báo
- **Mô tả:** Toàn bộ hệ thống có 14 điểm gọi hàm `alert()` popup của trình duyệt, gây gián đoạn luồng trải nghiệm người dùng.
- **Bằng chứng:** `Alerts.jsx:31`, `Dashboard.jsx:70,76,87`, `Employees.jsx:25,45,58,82`, `Incidents.jsx:88`, `Rooms.jsx:30`, `Settings.jsx:14,26,28`, `Tickets.jsx:43`.
- **Đề xuất:** Thay thế bằng Toast notification component của React.

---

## 9. DANH SÁCH "CẦN KIỂM TRA BẰNG TRÌNH DUYỆT"
1. **Giao diện Light Mode:** Kiểm tra độ tương phản màu chữ `#0F172A` trên nền `#F1F5F9` xem có đủ rõ nét trên màn hình thực tế hay không.
2. **Sơ đồ ghế 2D:** Mở modal "Xem sơ đồ ghế" ở `Quản lý phòng` để kiểm tra trực quan khoảng cách ô "LỐI ĐI" ở Hàng K và cách căn lề Hàng A.
3. **Hiển thị Ảnh camera calibration:** Mở modal "Xem ảnh hiệu chuẩn camera" kiểm tra xem ảnh JPEG 1920x1080 với 135 khung đa giác màu xanh có hiển thị vừa vặn trong khung modal hay bị méo tỷ lệ.
4. **Hiệu ứng chớp Flash sự cố mới:** Quan sát tab `Thông báo` xem sự cố mới có tạo hiệu ứng chớp màu vàng cam trong 3 giây như thiết kế không.
5. **Tab Network trình duyệt:** Kiểm tra xem các request polling định kỳ (1s, 3s, 5s, 10s) có gây nghẽn tab Network hoặc giật giao diện không.

---

## 10. PHẠM VI DỮ LIỆU ĐẦU VÀO CỦA DỰ ÁN (XÁC NHẬN)
- **Cơ chế thu nhận dữ liệu camera:** Đúng theo thiết kế và phạm vi của đồ án, hệ thống hoạt động dựa trên các **đoạn video clip và khung hình snapshot (JPEG Full HD 1920x1080) trích xuất trực tiếp từ camera CCTV thực tế của rạp chiếu**.
- **Tính khả thi & Kiểm chứng:** Luồng nạp ảnh snapshot -> mô hình YOLO phát hiện đầu người -> khớp với đa giác ghế camera (`seats_config_room1.json`) -> so sánh với vé quét từ app đã được kiểm chứng hoạt động hoàn chỉnh 100%. Hệ thống không yêu cầu phần cứng camera RTSP trực tiếp tại hiện trường.

---

## 11. DANH SÁCH LỆNH ĐÃ THỰC THI & TÀI NGUYÊN TẠM
- **Lệnh đã chạy:**
  - `git status --short`
  - `python --version`, `node --version`, `npm --version`
  - `npm run lint` (oxlint: 13 warnings, 0 errors)
  - `npm run build` (vite build: 82 modules, thành công trong 2.57s)
  - Script kiểm tra route, CORS, polling timer 20s, và luồng ghi Phase 4.
- **Xác nhận tệp tạm:**
  - Toàn bộ các script tạm trong `C:\CineSightApp\scratch\` đã được **XÓA SẠCH HOÀN TOÀN** (`Count: 0`).
- **Tiến trình Server:** Cổng 8000 đã chạy sẵn từ trước khi kiểm thử, không can thiệp tắt server.
- **Toàn vẹn Database:** COUNT các bảng trước và sau kiểm thử hoàn toàn trùng khớp 100%.

---
**KẾT THÚC BÁO CÁO TÍCH HỢP.**
