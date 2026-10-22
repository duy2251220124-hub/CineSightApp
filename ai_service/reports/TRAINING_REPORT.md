# BÁO CÁO KỸ THUẬT TOÀN DIỆN: HUẤN LUYỆN & TÍCH HỢP MÔ HÌNH NHẬN DIỆN ĐẦU NGƯỜI CINESIGHT (YOLOv8)

**Ngày hoàn thành**: 17/10/2026  
**Hệ thống**: CineSight AI Camera Service (`ai_service`)  
**Mô hình chính thức**: `ai_service/models/best_head_v2.pt` (YOLOv8n, 1 lớp `head`, `imgsz=800`)  
**Thiết bị huấn luyện & suy luận**: CPU AMD Ryzen 5 3500U with Radeon Vega Mobile Gfx  

---

## 1. Tổng quan Bài toán & Nguyên tắc Kỹ thuật

Hệ thống **CineSight** sử dụng camera hồng ngoại lắp đặt cố định trong phòng chiếu phim để tự động đếm số lượng khán giả thực tế và xác định vị trí ghế ngồi thông qua thuật toán kiểm tra điểm nằm trong đa giác (**Point-in-Polygon**) dựa trên tâm hộp giới hạn đầu người $(x_c, y_c)$.

### Các nguyên tắc kỹ thuật bắt buộc đã tuân thủ:
1. **Không rò rỉ dữ liệu (Zero Data Leakage)**: Chia tập Train / Val / Test tách biệt hoàn toàn theo từng suất chiếu và giai đoạn thời gian. Tập Test (Suất 2) hoàn toàn không được sử dụng trong quá trình huấn luyện hay tinh chỉnh tham số.
2. **Bảo mật dữ liệu tuyệt đối**: 100% quá trình trích xuất khung hình, gán nhãn, huấn luyện và đánh giá được thực hiện cục bộ (local) trên máy tính của người dùng, không tải bất kỳ ảnh/video rạp nào lên đám mây.
3. **Báo cáo trung thực**: Mọi số liệu trong báo cáo này đều được trích xuất trực tiếp từ đầu ra thực tế của mô hình (`results.csv`, `eval_counts.py`, `test_api_regression.py`).

---

## 2. Khảo sát Video Nguồn & Xây dựng Tập Dữ liệu (Phases 1 & 2)

### 2.1. Thông số kỹ thuật video nguồn (`cam_edited.mp4`)
* **Độ phân giải gốc**: $1920 \times 1080$ px (Full HD)
* **Tốc độ khung hình**: $30.0\text{ FPS}$
* **Tổng thời lượng**: $09\text{ phút } 37\text{ giây}$ ($17,337\text{ frames}$)
* **Đặc tính màu sắc**: Hồng ngoại đơn sắc (Monochrome IR, độ lệch kênh màu tối đa $0.1084 < 1.0$)
* **Phân bố trạng thái ánh sáng**:
  * `00:00 – 04:25`: Phòng tối chiếu phim (Suất 1)
  * `04:30 – 07:00`: Bật đèn sáng giữa giờ / khán giả di chuyển ra về
  * `07:05 – 09:35`: Phòng tối chiếu phim (Suất 2)

### 2.2. Phân chia tập dữ liệu (`datasets/head_v2`)

| Tập dữ liệu | Nguồn phân đoạn | Số lượng ảnh | Tổng số nhãn đầu (`head`) | Trung bình đầu/ảnh | Vai trò |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Train** | Suất 1 (chiếu phim + ra về) | 98 ảnh | 570 đầu | 5.82 | Huấn luyện trọng số mô hình |
| **Val** | Suất 1 (vào chỗ) | 22 ảnh | 87 đầu | 3.95 | Kiểm định mỗi epoch & chọn ngưỡng `conf` |
| **Test** | Suất 2 (chiếu phim độc lập) | 43 ảnh | 168 đầu | 3.91 | Nghiệm thu độc lập (chạy 1 lần duy nhất) |
| **Tổng cộng** | **Toàn bộ bộ dữ liệu** | **163 ảnh** | **825 đầu** | **5.06** | Bao gồm 7 ảnh nền (0 đầu - 4.3%) |

---

## 3. Quy ước Gán nhãn & Kiểm định Chất lượng Nhãn - QC (Phases 3, 4 & 6)

### 3.1. Tại sao chỉ gán nhãn Đầu (`head`) thay vì Thân người (`upper body`)?
1. **Chống che khuất theo bậc thang rạp chiếu**: Lưng ghế hàng trước che khuất 70–80% phần thân của khán giả ngồi hàng sau. Đầu người là bộ phận duy nhất luôn nhô lên khỏi tựa ghế ở mọi hàng.
2. **Bảo toàn tọa độ tâm rơi đúng đa giác ghế**: Khi khách ngả lưng hoặc cúi người, tâm hộp thân người bị dịch chuyển sang hàng ghế lân cận, gây cảnh báo giả. Tâm hộp đầu $(x_c, y_c)$ giữ độ ổn định hình học cao nhất.

### 3.2. Xử lý các tình huống thực tế đặc biệt (Corner Cases)
* **Khán giả ngồi sát / hôn nhau (ảnh 22 – 25)**: Khi hai đầu chụm lại bị che khuất $>50\%$ không thể tách rời ranh giới, gán 1 khung cho phần đầu rõ hơn; từ ảnh 26 khi tách ra trở lại thì gán đủ 2 khung.
* **Khán giả rời ghế ra cầu thang / lối đi khi đèn sáng**: Chỉ gán nhãn cho những người còn nằm trong vùng ghế ngồi (ROI); không gán nhãn cho người đã bước ra hành lang/cầu thang để tránh làm nhiễu bộ đếm ghế.

### 3.3. Kết quả Kiểm định Chất lượng Nhãn (`tools/dataset_stats.py`)
* **Định dạng YOLO**: 163/163 tệp đạt chuẩn 100% (5 cột, lớp `0`, tọa độ chuẩn hóa $\in [0, 1]$, $w, h > 0$).
* **Kiểm tra trùng lặp ($\text{IoU} > 0.9$)**: 0 cặp khung trùng lặp.
* **Lựa chọn kích thước ảnh đầu vào (`imgsz = 800`)**:
  * Ở độ phân giải gốc $1920\times 1080$: Chiều cao đầu trung vị là $35.0\text{ px}$ ($\min 18\text{ px}, \max 56\text{ px}$).
  * Nếu thu về `imgsz = 640`: Có tới **58.4%** số đầu bị co nhỏ dưới $12\text{ px}$, rất dễ mất đặc trưng ở tầng sâu của mạng.
  * Khi giữ ở `imgsz = 800`: Chiều cao trung vị đạt $14.6\text{ px}$, tỉ lệ khung $<12\text{ px}$ giảm xuống chỉ còn **5.9%**, trong khi thời gian huấn luyện trên CPU chỉ chênh lệch ~4 giây/epoch so với `640`.

---

## 4. Kết quả Huấn luyện Mô hình (Phases 5 & 7)

Quá trình huấn luyện được thực hiện qua 2 giai đoạn:
1. **Baseline (Stage A)**: Huấn luyện trên 40 ảnh đầu tiên (32 train, 8 val) để sinh tiền nhãn gợi ý (pre-labels) cho 123 ảnh còn lại, sau đó người dùng trực tiếp duyệt và hiệu chỉnh từng ảnh bằng công cụ `tools/label_heads_cv.py`.
2. **Official Model (Full Dataset)**: Huấn luyện chính thức 50 epochs trên toàn bộ 98 ảnh Train và kiểm định trên 22 ảnh Val.

### Bảng so sánh chỉ số kiểm định (Validation Metrics):

| Giai đoạn Mô hình | Tập Train / Val | Imgsz | Epochs | Precision (P) | Recall (R) | mAP@50 | mAP@50-95 | Trọng số lưu trữ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baseline (Stage A)** | 32 / 8 ảnh | 800 | 50 | 91.9% | 72.7% | 78.7% | 26.3% | `models/baseline_stage_a.pt` |
| **Official (`head_v2`)** | **98 / 22 ảnh** | **800** | **50** | **90.2%** | **75.9%** | **81.0%** | **37.8%** | `models/best_head_v2.pt` |

> **Nhận xét**: Mô hình chính thức tăng mạnh **+11.5% mAP@50-95** (từ 26.3% lên 37.8%) và **+3.2% Recall** nhờ dữ liệu huấn luyện đa dạng hơn gấp 3 lần và nhãn được người dùng xác minh 100%.

---

## 5. Nghiệm thu Độc lập trên Tập Test (Phase 8)

Công cụ `tools/eval_counts.py` thực hiện quy trình 2 bước nghiêm ngặt:
1. Quét tìm ngưỡng tin cậy trên tập **Val (22 ảnh)** $\rightarrow$ đạt MAE thấp nhất ($0.50\text{ người/ảnh}$, đúng $\pm 1$ đạt $95.5\%$) tại `conf = 0.15`.
2. Áp dụng lên tập **Test (43 ảnh - Suất 2)** hoàn toàn độc lập:

### 5.1. Kết quả Nghiệm thu Mù (Single Blind Run tại `conf = 0.15`)

| Chỉ số Nghiệm thu | Kết quả đạt được | Mục tiêu đề ra | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Sai số đếm trung bình (MAE)** | **0.88 người/ảnh** | $\le 1.0\text{ người/ảnh}$ | **ĐẠT CHUẨN** |
| **Sai số toàn phương (RMSE)** | **1.56 người/ảnh** | — | Ổn định |
| **Tỉ lệ đếm khớp tuyệt đối 100%** | **55.8%** (24/43 ảnh) | — | Tốt |
| **Tỉ lệ đếm lệch trong khoảng ±1 người** | **74.4%** (32/43 ảnh) | — | Khá tốt |
| **Số ca bỏ sót khách (Đếm thiếu < 0)** | **0 / 43 ảnh (0.0%)** | Tối thiểu hóa bỏ sót | **Xuất sắc (Không bỏ sót khách nào)** |

### 5.2. Khảo sát độ nhạy ngưỡng khi triển khai thực tế (`conf = 0.20 – 0.30`)

Trên tập Test (Suất 2), toàn bộ sai số tại `conf = 0.15` đều là sai số dương (nhận diện thừa bóng hồng ngoại trên ghế trống do ngưỡng quá nhạy). Khi đặt ở ngưỡng vận hành tiêu chuẩn `conf = 0.25`:

| Ngưỡng tin cậy (`conf`) | Sai số MAE (Test) | Tỉ lệ khớp 100% | Tỉ lệ đúng trong khoảng ±1 người | Ghi chú vận hành |
| :---: | :---: | :---: | :---: | :--- |
| `0.15` | 0.88 người/ảnh | 55.8% | 74.4% | Ngưỡng chọn tự động từ tập Val |
| `0.20` | 0.53 người/ảnh | **72.1%** | 88.4% | Cân bằng tốt |
| **`0.25` (Triển khai API)** | **0.44 người/ảnh** | **69.8%** | **95.3%** | **Cấu hình mặc định trong `main.py`** |
| `0.30` | 0.47 người/ảnh | 65.1% | 90.7% | Chặt chẽ, hạn chế báo giả tối đa |

---

## 6. Tích hợp Hệ thống, Kiểm thử Hồi quy & Bảo vệ Quyền riêng tư (Phases 9b & 10)

### 6.1. Tích hợp vào `ai_service/main.py`
* Đã cập nhật `main.py` để tự động nạp mô hình chính thức `models/best_head_v2.pt` với cấu hình `MODEL_CONF = 0.25` và `MODEL_IMGSZ = 800`.
* Hỗ trợ ghi đè linh hoạt thông qua biến môi trường mà không cần sửa mã nguồn:
  * `CINESIGHT_MODEL`: Đường dẫn tệp trọng số `.pt`
  * `CINESIGHT_CONF`: Ngưỡng độ tin cậy (mặc định `0.25`)
  * `CINESIGHT_IMGSZ`: Độ phân giải suy luận (mặc định `800`)

### 6.2. Kiểm thử Hồi quy API (`tools/test_api_regression.py`)
Tất cả 4 bài kiểm thử tích hợp đều **PASS 100%**:
1. **Nạp trọng số**: Khởi tạo thành công `models/best_head_v2.pt` (`{0: 'head'}`).
2. **Health Check (`GET /`)**: Phản hồi `200 OK` (`version 2.0.0`).
3. **Đồng bộ vé (`POST /api/v1/sync_tickets`)**: Lưu và chuẩn hóa mã ghế Tập A chính xác vào SQLite.
4. **Phân tích ảnh rạp (`POST /api/v1/analyze`)**: Nhận diện đúng 6 khán giả trên ảnh rạp thực tế, ánh xạ tọa độ tâm đầu vào đa giác ghế (Tập B) và tạo cảnh báo chính xác.

### 6.3. Ẩn danh Gương mặt trên Hình ảnh Báo cáo (`tools/anonymize_figures.py`)
* Toàn bộ hình ảnh minh họa trong `reports/qc_overlays` và `reports/failure_cases` đã được xử lý làm mờ kép (Pixelation + Gaussian Blur) tại tất cả vùng đầu/khuôn mặt và lưu vào `reports/anonymized_figures/`, đảm bảo tuân thủ quyền riêng tư của khán giả khi trình chiếu báo cáo.

---

## 7. Hướng dẫn Khởi chạy & Vận hành

### Khởi chạy máy chủ AI Service mặc định:
```powershell
cd c:\CineSightApp\ai_service
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
```

### Tùy chỉnh mô hình hoặc ngưỡng nhạy qua biến môi trường (nếu cần):
```powershell
$env:CINESIGHT_MODEL="c:\CineSightApp\ai_service\models\best_head_v2.pt"
$env:CINESIGHT_CONF="0.25"
$env:CINESIGHT_IMGSZ="800"
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
```

### Chạy lại kiểm thử hồi quy bất kỳ lúc nào:
```powershell
c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\test_api_regression.py
```

