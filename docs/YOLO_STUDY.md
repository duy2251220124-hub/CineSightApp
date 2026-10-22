# TÀI LIỆU HỌC TẬP & BÁO CÁO BẢO VỆ ĐỒ ÁN: YOLO TRONG DỰ ÁN CINESIGHT

> **Quy ước nhãn nguồn sự thật trong toàn bộ tài liệu (theo Quy tắc 1 & 2):**
> - `[MÃ NGUỒN]`: Khẳng định trích trực tiếp từ mã nguồn gói `ultralytics 8.4.160` đã cài trong `c:\CineSightApp\ai_service\venv\Lib\site-packages\ultralytics\...` (kèm đường dẫn tệp và số dòng).
> - `[TÀI LIỆU]`: Khẳng định trích từ tệp cấu hình/metadata đi kèm gói (`ultralytics\cfg\default.yaml`, `ultralytics\cfg\models\v8\yolov8.yaml`, `ultralytics-8.4.160.dist-info\METADATA`).
> - `[DỰ ÁN]`: Khẳng định trích từ tệp thật của dự án (`main.py`, `seat_mapper.py`, `runs\detect\head_v2_official\args.yaml`, `results.csv`, `manifest.csv`...) hoặc kết quả chạy lệnh Python thực tế trên máy này.
> - `[KIẾN THỨC CHUNG – chưa kiểm chứng trong lượt này]`: Kiến thức nền tảng về thị giác máy tính/học sâu dùng để giải thích trực quan hoặc so sánh với lập trình Frontend (JS/React/Flutter).
> - **Ghi chú môi trường mạng**: Tài liệu này được biên soạn hoàn toàn ngoại tuyến (offline) dựa trên nguồn `(a)` mã nguồn thư viện đã cài, `(b)` tài liệu/cấu hình đi kèm gói và `(d)` tệp thật của dự án; không truy cập mạng ngoài.

---

## TÓM TẮT 1 TRANG (EXECUTIVE SUMMARY)

1. **YOLO là gì (Dành cho Frontend Dev)**:
   - **YOLO ("You Only Look Once")** là mô hình mạng nơ-ron tích chập một giai đoạn (one-stage object detector): thay vì dùng vòng lặp quét từng vùng ảnh nhiều lần, mô hình nhận toàn bộ bức ảnh đầu vào trong một lượt chạy (forward pass) duy nhất, chia ảnh thành 3 lưới ô vuông ở 3 độ mịn khác nhau (`stride = 8, 16, 32` pixel), rồi đồng thời dự đoán tọa độ khung hình chữ nhật (`bounding box`) và điểm tự tin (`confidence`) tại mọi ô lưới `[MÃ NGUỒN: ultralytics/nn/modules/head.py:107-216]`.
   - Nếu so sánh với React/Flutter: toàn bộ mạng YOLO giống như một hàm pure function `detect(imageTensor) -> Array<{ box: [x1, y1, x2, y2], conf: number, cls: 0 }>` biến một mảng pixel 3 chiều thành danh sách các phần tử đầu người trên màn hình.

2. **Mô hình dự án CineSight đang dùng**:
   - **Kiến trúc & Trọng số**: Họ mô hình **YOLOv8n** (`nano` - bản nhỏ nhất của họ YOLOv8), khởi tạo học chuyển giao từ tệp gốc `c:\CineSightApp\ai_service\yolov8n.pt` (80 lớp COCO, `129 lớp`, `3.157.200 tham số`, `8,9 GFLOPs` ở `imgsz=640`) và tinh chỉnh (fine-tune) sang bài toán **1 lớp duy nhất (`0: head`)** lưu tại `c:\CineSightApp\ai_service\models\best_head_v2.pt` (`129 lớp`, `3.011.043 tham số` khi chưa gộp BatchNorm và `72 lớp`, `3.005.843 tham số` sau khi gộp `fuse()`, `8,2 GFLOPs` ở `imgsz=640` và `12,8 GFLOPs` ở `imgsz=800`) `[DỰ ÁN: main.py:420-425, output model.info()]`.

   - **Cấu hình vận hành trong Backend**: Tệp `c:\CineSightApp\ai_service\main.py:92, 420-425` nạp `models/best_head_v2.pt` với ngưỡng tự tin `MODEL_CONF = 0.25`, kích thước ảnh suy luận `MODEL_IMGSZ = 800`, lọc lớp `classes=[0]`, và không truyền `iou` nên dùng ngưỡng NMS mặc định `iou = 0.7` `[TÀI LIỆU: ultralytics/cfg/default.yaml:56]`.
   - **Dữ liệu & Kết quả huấn luyện**: Huấn luyện 50 epochs trên CPU (`AMD Ryzen 5 3500U`) trong `7.477,41 giây` (~2 giờ 04 phút 37 giây) với `98 ảnh train` (570 đầu), đánh giá trên `22 ảnh val` (87 đầu) và `43 ảnh test` (168 đầu) trích từ cùng 1 video hồng ngoại `cam_edited.mp4` (`1920x1080`). Checkpoint tốt nhất đạt ở **Epoch 35** với `Precision = 0,90226`, `Recall = 0,75862`, `mAP@0.5 = 0,80983`, `mAP@0.5:0.95 = 0,37750` trên tập `val` `[DỰ ÁN: runs/detect/head_v2_official/results.csv:37]`.

3. **5 Giới hạn quan trọng nhất của YOLO trong dự án (kèm số liệu thật)**:
   - **Giới hạn 1 – Đầu người ở hàng ghế xa bị thu nhỏ sát bước nhảy lưới (`stride = 8 px`)**: Trên toàn bộ 825 khung đầu của dự án ở ảnh gốc `1920x1080`, chiều cao đầu nhỏ nhất là `18,0 px`, trung vị `35,0 px`. Khi co ảnh về `imgsz = 640` (tỉ lệ `1/3`), chiều cao trung vị chỉ còn `11,7 px` (`58,42%` số đầu nhỏ hơn `12 px`, `2,55%` nhỏ hơn `8 px`); ở `imgsz = 800` (tỉ lệ `1/2,4`), chiều cao trung vị là `14,6 px` (`5,94%` nhỏ hơn `12 px`, `0,24%` nhỏ hơn `8 px` — nhỏ nhất `7,5 px`), chỉ nhỉnh hơn đúng 1 ô lưới `stride = 8 px` `[DỰ ÁN: Thống kê 825 nhãn thật Mục 5.3]`.

   - **Giới hạn 2 – Nhạy cảm cao với ngưỡng `conf` và `iou` của thuật toán NMS**: Trên 10 khung `val` (60 đầu thật), khi đổi `conf` từ `0,15 -> 0,25 -> 0,40 -> 0,60`, tổng số đầu đếm được nhảy từ `72 (+12 báo giả) -> 58 (-2 bỏ sót) -> 53 (-7) -> 28 (-32)`. Trên tập `val`, ở `iou = 0.70` (mặc định trong `main.py`), có 5 ảnh xuất hiện cặp khung dự đoán chồng nhau (`IoU` từ `0,6390` đến `0,6919`) trên cùng 1 cái đầu nhưng không bị NMS gộp, gây đếm thừa `[DỰ ÁN: Thí nghiệm A & D trong tools/yolo_lab.py]`.

   - **Giới hạn 3 – Rò rỉ dữ liệu theo thời gian (Temporal Leakage) và Domain Shift**: Cả 163 ảnh (`train/val/test`) đều trích từ 1 video `cam_edited.mp4` của 1 phòng chiếu duy nhất, với số người tối đa mỗi ảnh chỉ là **6 người** (trung bình `5,06 người/ảnh`). Khoảng cách thời gian nhỏ nhất giữa ảnh `train` cuối cùng (`343,5s`) và ảnh `val` đầu tiên (`346,0s`) chỉ là **2,5 giây**; giữa `val` (`419,5s`) và `test` (`425,0s`) chỉ là **5,5 giây**. Do đó, `mAP@0.5 = 0,80983` chưa phản ánh khả năng tổng quát hóa sang phòng chiếu khác, góc camera khác hoặc suất chiếu đông 50–135 khách `[DỰ ÁN: manifest.csv & Mục 3.8]`.

   - **Giới hạn 4 – Khoảng cách giữa chỉ số `mAP` của YOLO và nghiệp vụ ánh xạ ghế (`pointPolygonTest`)**: `mAP` chỉ đo độ chồng khít khung bao, trong khi `seat_mapper.py` lấy điểm tâm khung `(cx, cy)` cộng độ lệch `y + 10 px, +18 px` để kiểm tra nằm trong đa giác ghế. Thí nghiệm dịch tâm trên bản đồ đa giác thật `seats_configs/seats_config_room1.json` (135 ghế) cho thấy: chỉ cần tâm khung lệch `±3 px` là **13,86%** lượt điểm rơi sang ghế khác hoặc ra ngoài đa giác; lệch `±6 px` là **19,28%**; lệch `±10 px` là **36,45%** `[DỰ ÁN: Thí nghiệm E trong tools/yolo_lab.py]`.

   - **Giới hạn 5 – Tốc độ suy luận trên CPU và quy ước bỏ qua đầu bị che khuất**: Trên CPU `AMD Ryzen 5 3500U`, suy luận 1 ảnh mất trung bình `86,3 ms` ở `imgsz=320`, `151,8 ms` ở `imgsz=640`, `193,5 ms` ở `imgsz=800`, và `282,6 ms` ở `imgsz=960` `[DỰ ÁN: Thí nghiệm B]`. Ngoài ra, quy ước gán nhãn bỏ qua các đầu bị che khuất trên 50% hoặc nhỏ hơn `12 px` đồng nghĩa khi khách cúi sâu/bị người hàng trước che khuất, mô hình không phát hiện được đầu và hệ thống sinh cảnh báo "vắng mặt" (`missing_guest`) dù khách vẫn ngồi tại ghế `[DỰ ÁN: LABELING_SPEC.md & main.py:103-104]`.

---

## BẢNG ĐỐI CHIẾU: YÊU CẦU CỦA GIẢNG VIÊN -> PHẦN TRẢ LỜI TRONG TÀI LIỆU

| Yêu cầu của Giảng viên | Phần trả lời chính trong tài liệu | Nội dung cốt lõi & Bằng chứng kỹ thuật |
| :--- | :--- | :--- |
| **(1) Giới hạn của YOLO** | **PHẦN 5** (Mục 5.1 – 5.4b) & **PHẦN 6** (Thí nghiệm A–E) | Phân tích 10 giới hạn kỹ thuật chung của YOLO, 3 giới hạn đo lường nghiệp vụ ghế rạp phim, thống kê thực nghiệm trên 825 khung đầu thật, giấy phép `AGPL-3.0`, và 5 thí nghiệm định lượng bằng script `tools/yolo_lab.py`. |
| **(2) Các phép tính (toán) bên trong** | **PHẦN 1** & **PHẦN 2** (Mục 2.1 – 2.8) | Sơ đồ kiến trúc `Backbone -> Neck -> Detect Head` (`129 lớp`), số ô lưới (`8.400` ở `imgsz=640`; `13.125` ở `imgsz=800`), và 8 nhóm công thức văn bản thuần kèm mã Python kiểm chứng: `LetterBox` & `scale_boxes`, `IoU` & `CIoU`, `dist2bbox` & `DFL`, `TaskAlignedAssigner`, `v8DetectionLoss`, `NMS`, `Precision/Recall/F1/AP/mAP`, và `GFLOPs`. |
| **(3) Các phương pháp huấn luyện** | **PHẦN 3** (Mục 3.1 – 3.9) | Chu trình huấn luyện, Transfer Learning (`319/355` tensor chuyển giao từ `yolov8n.pt`, `36/355` tensor nhánh `cv3` khởi tạo lại), bảng giải nghĩa toàn bộ tham số trong `args.yaml`, công thức chọn `AdamW (lr=0.002)` khi `optimizer=auto`, lịch giảm `lr` tuyến tính, `Warmup`, `ModelEMA`, `Mosaic` + `close_mosaic`, `EarlyStopping` & `fitness`, chất lượng nhãn và rò rỉ dữ liệu (`2,5s`). |
| **(4) Các công cụ có sẵn trong YOLO hỗ trợ huấn luyện** | **PHẦN 4** (Mục 4.1 – 4.10) | Kiểm chứng các công cụ có thật trong `ultralytics 8.4.160`: CLI `yolo`, các biểu đồ tự sinh (`results.png`, `labels.jpg`, `BoxPR_curve.png`...), `model.val()`, `model.tune()`, tích hợp ghi log & cảnh báo quyền riêng tư (`SETTINGS["sync"] = True`), `model.export()`, `auto_annotate`, `Callbacks`, `Trackers` (`ByteTrack`, `BoT-SORT`). |
| **(+) Hiểu YOLO trong chính dự án CineSight** | **PHẦN 0**, **PHẦN 7**, **PHẦN 8**, **PHẦN 9** | Bối cảnh phiên bản/trọng số thật trong `main.py`, 10 câu hỏi–đáp bảo vệ đồ án trước giảng viên, dàn ý 12 slide thuyết trình không chứa ảnh mặt khán giả, bảng thuật ngữ Anh–Việt và 5 bài tập tự kiểm tra kèm đáp án. |

---

## PHẦN 0: BỐI CẢNH THẬT CỦA DỰ ÁN (ĐỌC TRƯỚC KHI VIẾT)
*(Phục vụ: Hiểu YOLO trong chính dự án CineSight)*

### 0.a. Phiên bản thư viện trong môi trường ảo (`ai_service\venv`) và các họ mô hình được gói hỗ trợ
- **Phiên bản phần mềm thực tế đang chạy** `[DỰ ÁN: chạy lệnh kiểm tra trên ai_service\venv\Scripts\python.exe]`:
  - **Python**: `3.14.3`
  - **PyTorch (`torch`)**: `2.14.0+cpu` (bản chỉ chạy CPU, không có CUDA)
  - **Ultralytics (`ultralytics`)**: `8.4.160`
  - **Ultralytics THOP (`ultralytics-thop`)**: `2.1.6` (thư viện tính FLOPs và đếm tham số)
  - **OpenCV (`cv2`)**: `5.0.0`
  - **NumPy (`numpy`)**: `2.5.3`
- **Các lớp mô hình (Model Classes) được export trong gói `ultralytics 8.4.160`** `[MÃ NGUỒN: ultralytics/models/__init__.py:3-9]`:
  - Danh sách `__all__`: `("LLM", "NAS", "RTDETR", "SAM", "YOLO", "YOLOE", "FastSAM", "YOLOWorld")`.
- **Các họ kiến trúc mô hình thị giác có cấu hình YAML trong gói** `[TÀI LIỆU: thư mục ultralytics/cfg/models/]`:
  - Gồm 10 thư mục họ mô hình: `['11', '12', '26', 'rt-detr', 'v10', 'v3', 'v5', 'v6', 'v8', 'v9']` (tương ứng với YOLOv3, YOLOv5, YOLOv6, YOLOv8, YOLOv9, YOLOv10, YOLO11, YOLO12, YOLO26 và RT-DETR).

### 0.b. Mô hình đang dùng trong `main.py` và mô hình nền khi huấn luyện (`args.yaml`)
- **Trong tệp vận hành Backend `c:\CineSightApp\ai_service\main.py`** `[DỰ ÁN: main.py:90-97, 417-430]`:
  - **Nạp mô hình (dòng 420–425)**:
    ```python
    default_model_path = os.path.join(os.path.dirname(__file__), "models", "best_head_v2.pt")
    model_path = os.environ.get("CINESIGHT_MODEL", default_model_path)
    MODEL_CONF = float(os.environ.get("CINESIGHT_CONF", "0.25"))
    MODEL_IMGSZ = int(os.environ.get("CINESIGHT_IMGSZ", "800"))
    model = YOLO(model_path)
    ```
  - **Gọi suy luận khi nhận ảnh camera (dòng 92–96)**:
    ```python
    results = model.predict(img, conf=MODEL_CONF, imgsz=MODEL_IMGSZ, classes=[0], verbose=False)
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detected_heads.append(((x1 + x2) / 2, (y1 + y2) / 2))
    ```
  - **Tổng hợp tham số suy luận thực tế của `main.py`**:
    - Tệp trọng số mặc định: `c:\CineSightApp\ai_service\models\best_head_v2.pt` `[DỰ ÁN: main.py:420]`.
    - Ngưỡng tự tin (`conf`): `0.25` `[DỰ ÁN: main.py:422]`.
    - Kích thước ảnh đưa vào mô hình (`imgsz`): `800` `[DỰ ÁN: main.py:423]`.
    - Lọc lớp (`classes`): `[0]` (tương ứng lớp `0: head`) `[DỰ ÁN: main.py:92]`.
    - Ngưỡng NMS (`iou`): **Không truyền trong `main.py:92`**, do đó Ultralytics tự động lấy giá trị mặc định `iou: 0.7` từ cấu hình gốc `[TÀI LIỆU: ultralytics/cfg/default.yaml:56]`.
- **Mô hình nền (Pretrained Base Model) khi huấn luyện lần chạy chính thức** `[DỰ ÁN: runs/detect/head_v2_official/args.yaml:1-9]`:
  ```yaml
  task: detect
  mode: train
  model: c:\CineSightApp\ai_service\yolov8n.pt
  data: c:\CineSightApp\ai_service\dataset_head_v2.yaml
  epochs: 50
  patience: 20
  batch: 4
  imgsz: 800
  ```
  - Mô hình nền xuất phát từ tệp trọng số tiền huấn luyện `yolov8n.pt` (huấn luyện sẵn trên tập dữ liệu COCO 80 lớp), hoàn toàn độc lập với `best_v1.pt`.

### 0.c. Thông tin chi tiết `model.info()` cho `yolov8n.pt` và `models/best_head_v2.pt`
Hàm `model.info(detailed=False, verbose=True, imgsz=640)` `[MÃ NGUỒN: ultralytics/nn/tasks.py:288-296, ultralytics/utils/torch_utils.py:537-580]` mặc định tính số phép tính dấu phẩy động (`GFLOPs`) ở kích thước ảnh vuông **`imgsz = 640`** (`640x640`). Dưới đây là đoạn mã Python và output nguyên văn cho cả `imgsz = 640` (mặc định của `model.info()`) và `imgsz = 800` (kích thước dự án dùng trong `main.py` và `args.yaml`) `[DỰ ÁN]`:

```python
from ultralytics import YOLO

m_coco = YOLO(r"c:\CineSightApp\ai_service\yolov8n.pt")
m_v2 = YOLO(r"c:\CineSightApp\ai_service\models\best_head_v2.pt")

print("yolov8n.pt (imgsz=640):", m_coco.info(imgsz=640))
print("best_head_v2.pt (imgsz=640):", m_v2.info(imgsz=640))
print("best_head_v2.pt (imgsz=800):", m_v2.info(imgsz=800))
```

**Output nguyên văn:**
```text
YOLOv8n summary: 129 layers, 3,157,200 parameters, 0 gradients, 8.9 GFLOPs
yolov8n.pt (imgsz=640): (129, 3157200, 0, 8.8550912)
Model summary: 129 layers, 3,011,043 parameters, 0 gradients, 8.2 GFLOPs
best_head_v2.pt (imgsz=640): (129, 3011043, 0, 8.1916928)
Model summary: 129 layers, 3,011,043 parameters, 0 gradients, 12.8 GFLOPs
best_head_v2.pt (imgsz=800): (129, 3011043, 0, 12.79952)
```
- **Giải thích sự chênh lệch tham số và GFLOPs**:
  - `yolov8n.pt` (80 lớp COCO) có `3.157.200` tham số và `8,855 GFLOPs` (làm tròn `8,9 GFLOPs` ở `imgsz=640`).
  - `best_head_v2.pt` (1 lớp `head`) có cùng `129` lớp nhưng giảm còn `3.011.043` tham số (ít hơn `146.157` tham số) và `8,192 GFLOPs` (làm tròn `8,2 GFLOPs` ở `imgsz=640`), vì nhánh phân loại `cv3` ở tầng `Detect` thu hẹp số kênh trung gian `c3 = max(ch[0], min(nc, 100))` từ `max(64, 80) = 80` kênh xuống `max(64, 1) = 64` kênh và đầu ra từ `80` lớp xuống `1` lớp `[MÃ NGUỒN: ultralytics/nn/modules/head.py:122]`.
  - Khi nâng `imgsz` từ `640` lên `800`, diện tích ảnh đầu vào tăng gấp `(800 / 640)^2 = 1,5625` lần, nên chi phí tính toán tăng tỉ lệ thuận: `8,1916928 * 1,5625 = 12,79952 GFLOPs` (làm tròn `12,8 GFLOPs`).

### 0.d. Tóm tắt bài toán: Dự án CineSight dùng YOLO để làm gì và vì sao chọn hướng này?
Trong hệ thống CineSight, mô hình YOLOv8n (`best_head_v2.pt`) nhận bức ảnh chụp từ camera giám sát hồng ngoại lắp cố định trong phòng chiếu, phát hiện từng **ĐẦU NGƯỜI (`head`)** bằng một khung hình chữ nhật `[x1, y1, x2, y2]` `[DỰ ÁN: main.py:92-96]`. Từ mỗi khung đầu, hệ thống lấy tọa độ điểm tâm `((x1 + x2) / 2, (y1 + y2) / 2)` rồi chuyển qua hàm `process_ai_detections` trong `seat_mapper.py:52-79`: hàm này cộng thêm độ lệch trục dọc `+10 px` và `+18 px` (để bù góc camera nhìn từ trên cao xuống, kéo điểm tâm từ đỉnh đầu/trán xuống vùng lòng ghế) và gọi thuật toán hình học `cv2.pointPolygonTest` kiểm tra xem điểm đó rơi vào đa giác (`polygon`) của mã ghế nào (`A01..L15`) trong tệp `seats_configs/seats_config_room1.json`, tạo thành **Tập B (ghế có người ngồi theo camera)**. Cuối cùng, hàm `generate_alerts` (`seat_mapper.py:81-105`) lấy hiệu hai tập hợp với **Tập A (ghế đã quét vé hợp lệ từ ứng dụng Flutter)**: 
`Tập B \ Tập A` sinh cảnh báo **khách ngồi không vé (`illegal_occupant`)**,
 còn `Tập A \ Tập B` sinh cảnh báo **ghế có vé nhưng vắng khách (`missing_guest`)**.
- **Vì sao chọn nhận diện ĐẦU NGƯỜI (`head`) thay vì CẢ NGƯỜI (`person`)?** Trong rạp chiếu phim, các hàng ghế xếp bậc thang san sát nhau; toàn bộ phần thân, ngực và chân của khán giả bị lưng ghế phía trước che khuất hoàn toàn (chỉ nhô phần đầu và vai trên). Thực nghiệm đối chứng trên tập `test` (43 ảnh) cho thấy mô hình gốc `yolov8n.pt` (nhận diện lớp `person`) có sai số đếm trung bình `MAE = 3,91 người/ảnh` (tỉ lệ đếm đúng trong phạm vi `±1` chỉ đạt `11,6%`), trong khi `best_head_v2.pt` (nhận diện `head`) giảm sai số xuống `MAE = 0,65 người/ảnh` (đúng `±1` đạt `88,4%` ở `iou=0.70` và `95,3%` ở `iou=0.60`) `[DỰ ÁN: TRAINING_WALKTHROUGH.md Phần 4.e]`.
- **Vì sao không dùng mô hình ước lượng mật độ đám đông (Crowd Density Estimation / Heatmap)?** Các mô hình mật độ đám đông (như CSRNet) chỉ xuất ra một bản đồ nhiệt mờ và một con số tổng (ví dụ: "trong phòng có khoảng 5,8 người") chứ không tách rời tọa độ tâm `(cx, cy)` của từng cá nhân độc lập `[KIẾN THỨC CHUNG – chưa kiểm chứng trong lượt này]`. Bài toán của CineSight không chỉ là đếm tổng số người trong phòng mà bắt buộc phải **định danh chính xác từng mã ghế (`C04`, `F07`...)** đang có người hay trống để đối chiếu với vé đã bán, nên bắt buộc phải dùng mô hình phát hiện vật thể/điểm định vị cá nhân như YOLO `[DỰ ÁN: seat_mapper.py:52-105]`.

---

## PHẦN 1: YOLO LÀ GÌ VÀ CÁC THÀNH PHẦN KIẾN TRÚC
*(Trả lời Yêu cầu (2) của Giảng viên: Các phép tính và cấu trúc bên trong YOLO)*

### 1.1. Sơ đồ chữ tổng thể luồng chạy của một bức ảnh qua YOLO
Dưới đây là luồng dữ liệu thực tế từ lúc `main.py` truyền ảnh camera `1920x1080` vào `model.predict()` cho tới khi nhận về danh sách khung đầu `[MÃ NGUỒN: ultralytics/engine/predictor.py, ultralytics/nn/tasks.py, ultralytics/nn/modules/head.py, ultralytics/utils/nms.py]`:

```text
[Ảnh gốc BGR 1920x1080 (uint8, 0..255)]
        │
        ▼  (1) Tiền xử lý: LetterBox + Chuẩn hóa [0.0 .. 1.0]
[Tensor đầu vào: (Batch=1, Channels=3, Height, Width)]
        │
        ▼  (2) BACKBONE (Tầng 0..9: Conv, C2f, SPPF)
        │      Trích xuất đặc trưng thị giác từ chi tiết nhỏ đến ngữ cảnh lớn
        ├──► Đặc trưng P3 (stride 8)  ──┐
        ├──► Đặc trưng P4 (stride 16) ──┼──► (3) NECK (Tầng 10..21: FPN + PAN)
        └──► Đặc trưng P5 (stride 32) ──┘        Trộn đặc trưng đa tỉ lệ (Upsample + Concat + C2f + Conv)
                                                        │
        ┌───────────────────────────────────────────────┘
        ▼
[3 Bản đồ đặc trưng đầu ra Neck: P3 (stride 8), P4 (stride 16), P5 (stride 32)]
        │
        ▼  (4) DETECT HEAD (Tầng 22: Nhánh đóng khung cv2 + Nhánh phân loại cv3 + DFL)
        │      - Nhánh cv2: dự đoán 64 số (4 cạnh x 16 mức DFL) -> giải mã thành [x1, y1, x2, y2]
        │      - Nhánh cv3: dự đoán 1 số logit -> qua hàm Sigmoid thành điểm tự tin conf ∈ (0, 1)
[Tensor dự đoán thô đã giải mã: (1, 5, N_ô_lưới) — với N = 8.400 (ở 640x640) hoặc 13.125 (ở 800x800)]
        │
        ▼  (5) Hậu xử lý: Lọc theo ngưỡng conf (conf >= 0.25) + Thuật toán NMS (iou <= 0.70)
        │      + Quy đổi tọa độ ngược về khung ảnh gốc 1920x1080 (scale_boxes)
[Danh sách K khung đầu người cuối cùng: boxes.xyxy (K, 4), boxes.conf (K,)]
```

- **So sánh với lập trình Frontend (React/Flutter)**:
  - **Tiền xử lý (`LetterBox`)** giống như `BoxFit.contain` trong Flutter: co bức ảnh `16:9` vừa khít vào khung vuông `640x640` (hoặc `800x800`) mà không làm méo mặt người, phần thừa bên trên và bên dưới được lót viền xám `rgb(114, 114, 114)`.
  - **Backbone + Neck + Head** giống như một pipeline gồm 23 middleware nối tiếp nhau biến đổi trạng thái (`state`) từ ma trận điểm ảnh thô thành mảng `8.400` (hoặc `13.125`) object ứng viên.
  - **Lọc `conf` và `NMS`** giống như chuỗi `.filter(box => box.conf >= 0.25)` kết hợp với bước `.reduce(...)` khử trùng lặp (deduplicate) các khung vẽ chồng lên cùng một cái đầu.

### 1.2. Cấu trúc chi tiết từng Module trong `Backbone`, `Neck` và `Head` của `YOLOv8n`
Trong gói `ultralytics 8.4.160`, kiến trúc họ YOLOv8 được định nghĩa tại tệp `ultralytics/cfg/models/v8/yolov8.yaml:1-49` `[TÀI LIỆU]`. Đối với bản **`n` (`YOLOv8n`)**, hệ số tỉ lệ ở dòng 11 là:
- `scales: n: [0.33, 0.25, 1024]` — tức là:
  - `depth_multiple = 0.33`: số lần lặp `repeats` của khối `C2f` được nhân với `0.33` rồi làm tròn `max(round(n * 0.33), 1)` (ví dụ: `3 -> 1`, `6 -> 2`).
  - `width_multiple = 0.25`: số kênh (`channels`) của mọi tầng được nhân với `0.25` (sau khi chặn trần ở `max_channels = 1024`), nên `64 -> 16`, `128 -> 32`, `256 -> 64`, `512 -> 128`, `1024 -> 256`.

#### A. Giải nghĩa 6 loại khối xây dựng (Building Blocks) trong mã nguồn
1. **`Conv` (`Conv2d + BatchNorm2d + SiLU`)** `[MÃ NGUỒN: ultralytics/nn/modules/conv.py:39-90]`:
   - Gồm một phép tích chập 2 chiều `nn.Conv2d` (quét bộ lọc `k x k` qua ảnh với bước nhảy `s`), chuẩn hóa lô `nn.BatchNorm2d` và hàm kích hoạt phi tuyến `nn.SiLU()` (`x * sigmoid(x)`). Khi chạy suy luận (`fuse()`), `Conv2d` và `BatchNorm2d` được gộp đại số thành một lớp `Conv2d` duy nhất để tăng tốc `[MÃ NGUỒN: ultralytics/nn/tasks.py:257-262]`.
   
2. **`C2f` (`Faster Implementation of CSP Bottleneck with 2 convolutions`)** `[MÃ NGUỒN: ultralytics/nn/modules/block.py:217-259]`:
   - Nhận đặc trưng đầu vào, đi qua lớp `cv1` (`Conv 1x1`) rồi tách đôi (`torch.chunk(2, 1)`): một nửa giữ nguyên làm đường tắt (shortcut), nửa kia đi qua chuỗi `n` khối `Bottleneck` nối tiếp; sau đó tất cả các nhánh trung gian được ghép nối (`torch.cat`) và nén lại qua `cv2` (`Conv 1x1`). Cách thiết kế này giống như giữ lại cả `props` gốc lẫn `computed state` qua từng bước biến đổi, giúp đạo hàm (gradient) truyền ngược không bị triệt tiêu.
3. **`SPPF` (`Spatial Pyramid Pooling - Fast`)** `[MÃ NGUỒN: ultralytics/nn/modules/block.py:167-194]`:
   - Đặt ở cuối Backbone (Tầng 9): cho đặc trưng đi qua 3 lần `MaxPool2d(kernel_size=5, stride=1, padding=2)` liên tiếp rồi ghép (`Concat`) 4 luồng lại. Giúp mỗi ô lưới nhìn bao quát một vùng ngữ cảnh rộng (tương đương bộ lọc `5x5`, `9x9`, `13x13`) với chi phí tính toán thấp.
4. **`nn.Upsample` & `Concat`** `[MÃ NGUỒN: ultralytics/cfg/models/v8/yolov8.yaml:33-38, ultralytics/nn/modules/conv.py:302-319]`:
   - `Upsample(scale_factor=2, mode="nearest")` phóng to bản đồ đặc trưng lên gấp đôi chiều rộng và chiều cao; `Concat(dimension=1)` ghép chồng các kênh đặc trưng từ tầng sâu (giàu ngữ nghĩa) với tầng nông (giàu chi tiết vị trí).
5. **`Detect` (Đầu phát hiện tách nhánh – Decoupled Anchor-Free Head)** `[MÃ NGUỒN: ultralytics/nn/modules/head.py:62-230]`:
   - Nhận 3 bản đồ đặc trưng `P3, P4, P5` từ Neck và tách thành 2 nhánh hoàn toàn độc lập: nhánh đóng khung `self.cv2` và nhánh phân loại `self.cv3`.
6. **`DFL` (`Distribution Focal Loss Integral Module`)** `[MÃ NGUỒN: ultralytics/nn/modules/block.py:60-82]`:
   - Biến phân phối xác suất trên `16` mức rời rạc (`0..15`) của mỗi cạnh khung bao thành giá trị khoảng cách liên tục bằng phép lấy kỳ vọng toán học.

#### B. Bảng 23 tầng cấu trúc (`0..22`) của `YOLOv8n` (`best_head_v2.pt`)
Đối chiếu trực tiếp từ `ultralytics/cfg/models/v8/yolov8.yaml:18-49` `[TÀI LIỆU]` và mô hình thực tế `[DỰ ÁN]`:

| Chỉ số tầng | Khu vực | Nguồn đầu vào (`from`) | Module (`yolov8.yaml`) | Số lặp thực tế (`n`) | Số kênh thực tế (`YOLOv8n`) | Bước nhảy (`stride`) | Vai trò trong việc tìm đầu người |
| :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **0** | Backbone | `-1` (Ảnh) | `Conv [64, 3, 2]` | 1 | `3 -> 16` | `P1 / 2` | Giảm một nửa kích thước ảnh, bắt các cạnh sáng/tối cơ bản. |
| **1** | Backbone | `-1` | `Conv [128, 3, 2]` | 1 | `16 -> 32` | `P2 / 4` | Thu nhỏ ảnh còn `1/4`, trích xuất đường viền cong của hộp sọ/vai. |
| **2** | Backbone | `-1` | `C2f [128, True]` | 1 | `32 -> 32` | `P2 / 4` | Học tổ hợp đặc trưng cục bộ mức nông (có kết nối tắt `shortcut=True`). |
| **3** | Backbone | `-1` | `Conv [256, 3, 2]` | 1 | `32 -> 64` | `P3 / 8` | Thu nhỏ ảnh còn `1/8` (`80x80` ở `imgsz=640`, `100x100` ở `imgsz=800`). |
| **4** | Backbone | `-1` | `C2f [256, True]` | 2 | `64 -> 64` | `P3 / 8` | Đặc trưng độ phân giải cao của Backbone (giữ chi tiết các đầu nhỏ ở xa). |
| **5** | Backbone | `-1` | `Conv [512, 3, 2]` | 1 | `64 -> 128` | `P4 / 16` | Thu nhỏ ảnh còn `1/16` (`40x40` ở `imgsz=640`, `50x50` ở `imgsz=800`). |
| **6** | Backbone | `-1` | `C2f [512, True]` | 2 | `128 -> 128` | `P4 / 16` | Đặc trưng tầm trung của Backbone. |
| **7** | Backbone | `-1` | `Conv [1024, 3, 2]` | 1 | `128 -> 256` | `P5 / 32` | Thu nhỏ ảnh còn `1/32` (`20x20` ở `imgsz=640`, `25x25` ở `imgsz=800`). |
| **8** | Backbone | `-1` | `C2f [1024, True]` | 1 | `256 -> 256` | `P5 / 32` | Đặc trưng mức sâu nhất (ngữ nghĩa toàn cục). |
| **9** | Backbone | `-1` | `SPPF [1024, 5]` | 1 | `256 -> 256` | `P5 / 32` | Gom ngữ cảnh đa vùng bằng 3 lớp `MaxPool 5x5` nối tiếp. |
| **10** | Neck (FPN) | `-1` | `nn.Upsample [None, 2, "nearest"]` | 1 | `256 -> 256` | `16` | Phóng to đặc trưng `P5` lên gấp đôi để ghép với `P4`. |
| **11** | Neck (FPN) | `[-1, 6]` | `Concat [1]` | 1 | `256 + 128 = 384` | `16` | Nối đặc trưng ngữ nghĩa sâu (Tầng 10) với đặc trưng tầm trung (Tầng 6). |
| **12** | Neck (FPN) | `-1` | `C2f [512]` | 1 | `384 -> 128` | `16` | Tinh chỉnh đặc trưng trộn ở mức `P4/16`. |
| **13** | Neck (FPN) | `-1` | `nn.Upsample [None, 2, "nearest"]` | 1 | `128 -> 128` | `8` | Phóng to đặc trưng `P4` lên gấp đôi để ghép với `P3`. |
| **14** | Neck (FPN) | `[-1, 4]` | `Concat [1]` | 1 | `128 + 64 = 192` | `8` | Nối đặc trưng từ Tầng 13 với đặc trưng chi tiết sắc nét ở Tầng 4. |
| **15** | Neck (PAN) | `-1` | `C2f [256]` | 1 | `192 -> 64` | **`P3 / 8`** | **Đầu ra Neck thứ 1 (`P3/8 - small`)**: Chuyên bắt các đầu người nhỏ ở xa. |
| **16** | Neck (PAN) | `-1` | `Conv [256, 3, 2]` | 1 | `64 -> 64` | `16` | Thu nhỏ ngược lại từ `stride 8` xuống `stride 16` (luồng Bottom-Up PAN). |
| **17** | Neck (PAN) | `[-1, 12]` | `Concat [1]` | 1 | `64 + 128 = 192` | `16` | Ghép luồng thu nhỏ Tầng 16 với Tầng 12. |
| **18** | Neck (PAN) | `-1` | `C2f [512]` | 1 | `192 -> 128` | **`P4 / 16`** | **Đầu ra Neck thứ 2 (`P4/16 - medium`)**: Chuyên bắt các đầu cỡ vừa ở giữa phòng. |
| **19** | Neck (PAN) | `-1` | `Conv [512, 3, 2]` | 1 | `128 -> 128` | `32` | Thu nhỏ từ `stride 16` xuống `stride 32`. |
| **20** | Neck (PAN) | `[-1, 9]` | `Concat [1]` | 1 | `128 + 256 = 384` | `32` | Ghép luồng Tầng 19 với đầu ra `SPPF` Tầng 9. |
| **21** | Neck (PAN) | `-1` | `C2f [1024]` | 1 | `384 -> 256` | **`P5 / 32`** | **Đầu ra Neck thứ 3 (`P5/32 - large`)**: Chuyên bắt các đầu/vật thể lớn gần camera. |
| **22** | Head | `[15, 18, 21]` | `Detect [nc=1]` | 1 | `[64, 128, 256] -> out` | `[8, 16, 32]` | Tầng dự đoán cuối cùng trên cả 3 mức lưới `P3, P4, P5`. |

### 1.3. Vì sao có 3 mức đặc trưng (`stride 8, 16, 32`) và mỗi mức phụ trách cỡ vật thể nào?
- **Ý nghĩa của `stride` (bước nhảy lưới)**: `stride = s` nghĩa là cứ một ô vuông `s x s` pixel trên bức ảnh đầu vào sẽ được gom lại thành **1 điểm neo (anchor point)** trên bản đồ đặc trưng `[MÃ NGUỒN: ultralytics/utils/tal.py:421-434]`.
- **Vì sao cần 3 mức (`P3/8`, `P4/16`, `P5/32`)** `[TÀI LIỆU: ultralytics/cfg/models/v8/yolov8.yaml:39, 43, 47]`:
  1. **Mức `P3` (`stride = 8`, ghi chú trong YAML là `# 15 (P3/8-small)`)**: Mỗi ô lưới cách nhau đúng `8 px`. Mức này có độ phân giải không gian mịn nhất, dùng để phát hiện **vật thể nhỏ (small objects)** — cụ thể trong rạp CineSight là các đầu người ở hàng ghế giữa và xa màn hình (sau khi co ảnh có kích thước chỉ từ `7,5 px` đến `20 px`).
  2. **Mức `P4` (`stride = 16`, ghi chú trong YAML là `# 18 (P4/16-medium)`)**: Mỗi ô lưới cách nhau `16 px`, có vùng nhìn (receptive field) rộng hơn `P3`, phụ trách **vật thể cỡ trung bình (medium objects)** — như đầu khán giả ngồi ở các hàng ghế gần camera hơn.
  3. **Mức `P5` (`stride = 32`, ghi chú trong YAML là `# 21 (P5/32-large)`)**: Mỗi ô lưới cách nhau `32 px`, nhìn bao quát vùng ảnh lớn, phụ trách **vật thể cỡ lớn (large objects)**.

### 1.4. Số lượng ô lưới ở mỗi mức và tổng số vị trí dự đoán (Tính bằng mã Python)
Công thức tính tổng số điểm dự đoán `N` cho ảnh vuông kích thước `imgsz x imgsz` với 3 mức `stride = [8, 16, 32]`:

```text
N_P3 = (imgsz / 8) * (imgsz / 8)
N_P4 = (imgsz / 16) * (imgsz / 16)
N_P5 = (imgsz / 32) * (imgsz / 32)
N_tong = N_P3 + N_P4 + N_P5
```

- **Đọc bằng lời**: Số vị trí dự đoán ở mỗi mức bằng chiều rộng ảnh chia cho bước nhảy `stride` nhân với chiều cao ảnh chia cho bước nhảy `stride`; tổng số vị trí dự đoán của mô hình là tổng số ô của cả ba mức `P3`, `P4` và `P5`.
- **Đoạn mã Python và output nguyên văn** (tính cho cả `imgsz = 640` theo đề bài và `imgsz = 800` theo cấu hình dự án) `[DỰ ÁN]`:

```python
for sz in (640, 800):
    cells = [(sz // s, sz // s, (sz // s) ** 2) for s in (8, 16, 32)]
    total_cells = sum(c[2] for c in cells)
    print(f"imgsz={sz}: P3(s=8)={cells[0][0]}x{cells[0][1]}={cells[0][2]}, P4(s=16)={cells[1][0]}x{cells[1][1]}={cells[1][2]}, P5(s=32)={cells[2][0]}x{cells[2][1]}={cells[2][2]} -> Total={total_cells}")
```

**Output nguyên văn:**
```text
imgsz=640: P3(s=8)=80x80=6400, P4(s=16)=40x40=1600, P5(s=32)=20x20=400 -> Total=8400
imgsz=800: P3(s=8)=100x100=10000, P4(s=16)=50x50=2500, P5(s=32)=25x25=625 -> Total=13125
```
  - Ở **`imgsz = 640`**: Lưới `P3` có `80x80 = 6.400` ô, `P4` có `40x40 = 1.600` ô, `P5` có `20x20 = 400` ô -> Tổng cộng **`8.400` vị trí dự đoán**.
  - Ở **`imgsz = 800`**: Lưới `P3` có `100x100 = 10.000` ô, `P4` có `50x50 = 2.500` ô, `P5` có `25x25 = 625` ô -> Tổng cộng **`13.125` vị trí dự đoán**.

### 1.5. Kiểu đầu ra trong mã nguồn `nn/modules/head.py` và Hình dạng (Shape) đầu ra thô thực tế
Đọc trực tiếp lớp `Detect` tại `ultralytics/nn/modules/head.py:107-216` `[MÃ NGUỒN]`:
1. **Không dùng hộp neo mẫu (Anchor-Free)**: Khác với các đời YOLO cũ phải định nghĩa trước chiều rộng/chiều cao các hộp mẫu (anchor boxes), lớp `Detect` của YOLOv8 dùng hàm `make_anchors(x["feats"], self.stride, 0.5)` (`head.py:212`, `tal.py:421`) để đặt đúng **1 điểm tâm `(x_center = i + 0.5, y_center = j + 0.5)`** tại giữa mỗi ô lưới, rồi dự đoán khoảng cách từ điểm tâm đó tới 4 cạnh trái, trên, phải, dưới (`left, top, right, bottom`).
2. **Tách nhánh khung bao và phân loại (Decoupled Head)** `[MÃ NGUỒN: ultralytics/nn/modules/head.py:121-137]`:
   - `c2 = max((16, ch[0] // 4, self.reg_max * 4))` (`head.py:121`): Với `ch[0] = 64` và `reg_max = 16`, `c2 = max(16, 16, 64) = 64`.
   - **Nhánh hồi quy khung `self.cv2`** (`head.py:123-125`): Ở mỗi mức lưới `i ∈ {0, 1, 2}`, gồm `Conv(ch[i], 64, 3) -> Conv(64, 64, 3) -> nn.Conv2d(64, 64, 1)`, xuất ra `4 * reg_max = 64` kênh.
   - `c3 = max(ch[0], min(self.nc, 100))` (`head.py:122`): Với `best_head_v2.pt` (`nc = 1`), `c3 = max(64, 1) = 64`.
   - **Nhánh phân loại `self.cv3`** (`head.py:126-137`, với thuộc tính `legacy = True` trong `head.py:72` cho YOLOv8): Ở mỗi mức lưới `i`, gồm `Conv(ch[i], c3, 3) -> Conv(c3, c3, 3) -> nn.Conv2d(c3, nc, 1)` (hoặc `DWConv` nếu `legacy=False`), xuất ra `nc = 1` kênh điểm logit phân loại.
3. **Hình dạng (Shape) đầu ra thô khi chạy 1 ảnh thật qua mô hình** `[MÃ NGUỒN: ultralytics/nn/modules/head.py:168-193 & DỰ ÁN]`:
   - Trong chế độ đánh giá/suy luận (`eval()`, `export=False`), hàm `Detect.forward` (`head.py:193`) trả về một `tuple` gồm 2 phần tử `(y, preds)`:
     - `y` (`raw_eval[0]`): Tensor đã giải mã tọa độ khung và qua hàm `sigmoid()`, có shape **`(1, 5, 8400)`** (ở `imgsz=640`), trong đó chiều thứ hai gồm `5` giá trị: `[x_center, y_center, width, height, conf_head]` cho từng vị trí trong `8.400` ô lưới (`head.py:205-206`).
     - `preds` (`raw_eval[1]`): Dictionary chứa đầu ra thô trước giải mã từ `forward_head` (`head.py:177`):
       - `preds['boxes']`: shape **`(1, 64, 8400)`** (`64 = 4 cạnh * 16 mức DFL`).
       - `preds['scores']`: shape **`(1, 1, 8400)`** (`1` logit chưa qua sigmoid của lớp `head`).
       - `preds['feats']`: danh sách 3 tensor bản đồ đặc trưng `[P3, P4, P5]` có shape **`[(1, 64, 80, 80), (1, 128, 40, 40), (1, 256, 20, 20)]`**.

**Đoạn mã Python chạy 1 ảnh thật (`val/room1_cam_edited_0346s.jpg`) và in shape đầu ra thô `[DỰ ÁN]`:**
```python
import cv2, torch
from ultralytics import YOLO
from ultralytics.data.augment import LetterBox

m_v2 = YOLO(r"c:\CineSightApp\ai_service\models\best_head_v2.pt")
img_bgr = cv2.imread(r"c:\CineSightApp\ai_service\datasets\head_v2\images\val\room1_cam_edited_0346s.jpg")
lb640_sq = LetterBox((640, 640), auto=False)(image=img_bgr)
x_tensor = torch.from_numpy(lb640_sq).permute(2, 0, 1).unsqueeze(0).float() / 255.0

pt_model = m_v2.model.eval()
with torch.no_grad():
    raw_eval = pt_model(x_tensor)

print("Input tensor shape (square 640x640):", tuple(x_tensor.shape))
print("Raw eval output type:", type(raw_eval), "len:", len(raw_eval))
print("  raw_eval[0] (decoded [B, 4+nc, N]):", tuple(raw_eval[0].shape))
print("  raw_eval[1] keys:", list(raw_eval[1].keys()))
print("  raw_eval[1]['boxes']:", tuple(raw_eval[1]["boxes"].shape))
print("  raw_eval[1]['scores']:", tuple(raw_eval[1]["scores"].shape))
print("  raw_eval[1]['feats']:", [tuple(f.shape) for f in raw_eval[1]["feats"]])
```

**Output nguyên văn:**
```text
Input tensor shape (square 640x640): (1, 3, 640, 640)
Raw eval output type: <class 'tuple'> len: 2
  raw_eval[0] (decoded [B, 4+nc, N]): (1, 5, 8400)
  raw_eval[1] keys: ['boxes', 'scores', 'feats']
  raw_eval[1]['boxes']: (1, 64, 8400)
  raw_eval[1]['scores']: (1, 1, 8400)
  raw_eval[1]['feats']: [(1, 64, 80, 80), (1, 128, 40, 40), (1, 256, 20, 20)]
```

---

## PHẦN 2: CÁC PHÉP TÍNH TOÁN HỌC BÊN TRONG YOLO
*(Trả lời Yêu cầu (2) của Giảng viên: Các phép tính bên trong — Phần chính)*

> **Lưu ý định dạng (theo Quy tắc 3 & 4)**: Mọi công thức dưới đây đều viết bằng văn bản thuần trong khối mã (` ```text ... ``` `), tuyệt đối không dùng LaTeX, theo sau là phần đọc bằng lời, vị trí chính xác trong mã nguồn `site-packages\ultralytics\...` và ví dụ số chạy bằng Python.

---

### 2.1. Tiền xử lý ảnh: `LetterBox` (Co ảnh giữ tỉ lệ, đệm viền) và `scale_boxes` (Đổi tọa độ khung về ảnh gốc)

- **Vị trí trong mã nguồn**:
  - Lớp `LetterBox`: `ultralytics/data/augment.py:1634-1812` (`get_params` tại dòng `1729-1776`, `apply_image` tại dòng `1778-1811`) `[MÃ NGUỒN]`.
  - Hàm đổi tọa độ ngược về ảnh gốc `scale_boxes`: `ultralytics/utils/ops.py:122-166` `[MÃ NGUỒN]`.
- **Công thức văn bản thuần**:

```text
# 1. Tính tỉ lệ thu phóng r (giữ nguyên tỉ lệ khung hình - aspect ratio):
r = min(H_moi / H_goc, W_moi / W_goc)

# 2. Kích thước ảnh sau khi co nhưng chưa đệm viền (new_unpad):
W_co = round(W_goc * r)
H_co = round(H_goc * r)

# 3. Tính lượng viền xám (padding_value = 114) cần đệm thêm:
dw = W_moi - W_co
dh = H_moi - H_co
# Nếu chế độ auto=True (mặc định khi chạy predict 1 ảnh đơn lẻ), chỉ đệm tới bội số của stride=32:
# dw = dw mod 32 ; dh = dh mod 32

# Chia đều viền cho 2 phía (center=True):
top    = round(dh / 2 - 0.1)
bottom = round(dh / 2 + 0.1)
left   = round(dw / 2 - 0.1)
right  = round(dw / 2 + 0.1)

# 4. Chiều cao của một cái đầu sau khi co:
h_dau_moi = h_dau_goc * r

# 5. Đổi tọa độ khung dự đoán [x1', y1', x2', y2'] từ ảnh đã đệm về ảnh gốc (scale_boxes):
x1_goc = clamp((x1' - left) / r, 0, W_goc)
y1_goc = clamp((y1' - top)  / r, 0, H_goc)
x2_goc = clamp((x2' - left) / r, 0, W_goc)
y2_goc = clamp((y2' - top)  / r, 0, H_goc)
```

- **Đọc ra bằng lời**:
  1. Để đưa bức ảnh gốc có chiều rộng `W_goc`, chiều cao `H_goc` vào khung mục tiêu `W_moi x H_moi` mà không làm méo hình, ta lấy tỉ lệ thu phóng `r` bằng giá trị nhỏ hơn giữa tỉ lệ chiều cao và tỉ lệ chiều rộng.
  2. Nhân `W_goc` và `H_goc` với `r` rồi làm tròn để được kích thước ảnh đã co (`W_co x H_co`). Phần thiếu hụt so với khung mục tiêu (`dw`, `dh`) được chia đôi để đệm viền màu xám (giá trị pixel `114`) vào hai bên trên–dưới (`top`, `bottom`) hoặc trái–phải (`left`, `right`). Lưu ý: khi huấn luyện các lô ghép hoặc đánh giá vuông (`auto=False`), ảnh được đệm đủ thành hình vuông `640x640` (hoặc `800x800`); còn khi gọi `model.predict()` trên 1 ảnh lẻ với `rect=True` (`auto=True`), Ultralytics chỉ đệm phần dư `dh mod 32` để tiết kiệm phép tính (`360 -> 384` ở `imgsz=640`, hoặc `450 -> 480` ở `imgsz=800`).
  3. Sau khi mô hình dự đoán xong khung bao trên ảnh đã co và đệm, hàm `scale_boxes` trừ đi phần viền đệm `left`, `top` rồi chia lại cho tỉ lệ `r` để trả tọa độ khung về đúng hệ tọa độ `1920x1080` của ảnh gốc.

- **Ví dụ số bằng mã Python (Ảnh `1920x1080` vào `imgsz=640` và `imgsz=800`, đầu cao `24 px` và ngưỡng `12 px`)** `[DỰ ÁN]`:

```python
import cv2, torch
from ultralytics.data.augment import LetterBox
from ultralytics.utils.ops import scale_boxes

img_bgr = cv2.imread(r"c:\CineSightApp\ai_service\datasets\head_v2\images\val\room1_cam_edited_0346s.jpg")

lb_sq = LetterBox(new_shape=(640, 640), auto=False, stride=32)
params_sq = lb_sq.get_params({"img": img_bgr})
print("LetterBox(640,640, auto=False) on 1920x1080:", params_sq)

lb_auto = LetterBox(new_shape=(640, 640), auto=True, stride=32)
params_auto = lb_auto.get_params({"img": img_bgr})
print("LetterBox(640,640, auto=True) on 1920x1080:", params_auto)

lb_800 = LetterBox(new_shape=(800, 800), auto=False, stride=32)
params_800 = lb_800.get_params({"img": img_bgr})
print("LetterBox(800,800, auto=False) on 1920x1080:", params_800)

r640 = params_sq["ratio"][0]
r800 = params_800["ratio"][0]
print(f"Head 24px on 1920x1080 -> at imgsz=640: {24*r640:.2f}px | at imgsz=800: {24*r800:.2f}px")
print(f"Head 12px on 1920x1080 -> at imgsz=640: {12*r640:.2f}px | at imgsz=800: {12*r800:.2f}px")
print(f"Head  9px on 1920x1080 -> at imgsz=640: {9*r640:.2f}px | at imgsz=800: {9*r800:.2f}px")

pred_box_640 = torch.tensor([[300.0, 200.0, 308.0, 208.0]])
restored_box = scale_boxes((640, 640), pred_box_640.clone(), (1080, 1920))
print("Box on 640x640:", pred_box_640.tolist(), "-> scale_boxes to 1080x1920:", restored_box.tolist())
```

**Output nguyên văn:**
```text
LetterBox(640,640, auto=False) on 1920x1080: {'orig_shape': (1080, 1920), 'new_shape': (640, 640), 'ratio': (0.3333333333333333, 0.3333333333333333), 'new_unpad': (640, 360), 'top': 140, 'bottom': 140, 'left': 0, 'right': 0}
LetterBox(640,640, auto=True) on 1920x1080: {'orig_shape': (1080, 1920), 'new_shape': (640, 640), 'ratio': (0.3333333333333333, 0.3333333333333333), 'new_unpad': (640, 360), 'top': 12, 'bottom': 12, 'left': 0, 'right': 0}
LetterBox(800,800, auto=False) on 1920x1080: {'orig_shape': (1080, 1920), 'new_shape': (800, 800), 'ratio': (0.4166666666666667, 0.4166666666666667), 'new_unpad': (800, 450), 'top': 175, 'bottom': 175, 'left': 0, 'right': 0}
Head 24px on 1920x1080 -> at imgsz=640: 8.00px | at imgsz=800: 10.00px
Head 12px on 1920x1080 -> at imgsz=640: 4.00px | at imgsz=800: 5.00px
Head  9px on 1920x1080 -> at imgsz=640: 3.00px | at imgsz=800: 3.75px
Box on 640x640: [[300.0, 200.0, 308.0, 208.0]] -> scale_boxes to 1080x1920: [[900.0, 180.0, 924.0, 204.0]]
```

- **Liên hệ trực tiếp với dự án CineSight**:
  - Ảnh camera `1920x1080` khi đưa vào `imgsz = 640` bị co đi **3 lần** (`ratio = 0.3333`), thành `640x360`, rồi đệm `140 px` trên và `140 px` dưới (nếu `auto=False`) hoặc `12 px` trên và `12 px` dưới (nếu `auto=True`, thành `640x384`).
  - Một cái đầu cao **`24 px`** ở ảnh gốc `1920x1080` sau khi co về `imgsz = 640` chỉ còn cao đúng **`8,00 px`** (vừa khít 1 bước nhảy `stride = 8` của tầng `P3`!), và ở `imgsz = 800` (`ratio = 0.4167`) còn **`10,00 px`**.
  - Còn tại ngưỡng **`12 px`** mà bạn quy định trong `LABELING_SPEC.md` ("không gán nhãn đầu nhỏ hơn `12x12 px` trên ảnh gốc"): sau khi co về `imgsz = 640`, cái đầu `12 px` chỉ còn **`4,00 px`** (và ở `imgsz = 800` chỉ còn **`5,00 px`**) — nhỏ hơn cả kích thước 1 ô lưới nhỏ nhất (`stride = 8 px`), nghĩa là toàn bộ khuôn mặt/đầu người lọt thỏm vào nửa ô lưới và bị nhòe lẫn vào nền ghế. Đó là lý do kỹ thuật xác đáng vì sao dự án phải nâng `imgsz` lên `800` và không gán nhãn các đầu dưới `12 px` `[DỰ ÁN: LABELING_SPEC.md & args.yaml:9]`.

---

### 2.2. `IoU` và biến thể `CIoU` (Complete IoU) dùng cho hồi quy khung bao

- **Vị trí trong mã nguồn**:
  - Hàm tính `bbox_iou(..., CIoU=True)`: `ultralytics/utils/metrics.py:107-173` (dẫn nguồn bài báo `https://arxiv.org/abs/1911.08287v1` tại chú thích dòng `124`) `[MÃ NGUỒN]`.
  - Được gọi trực tiếp trong hàm mất mát khung bao `BboxLoss.forward` tại `ultralytics/utils/loss.py:134` (`iou = bbox_iou(pred_bboxes[fg_mask], target_bboxes[fg_mask], xywh=False, CIoU=True)`) và trong bộ gán nhãn `TaskAlignedAssigner.iou_calculation` tại `ultralytics/utils/tal.py:241` `[MÃ NGUỒN]`.
- **Công thức văn bản thuần**:

```text
# Cho Khung 1 [x1_1, y1_1, x2_1, y2_1] (rộng w1, cao h1)
# và Khung 2 [x1_2, y1_2, x2_2, y2_2] (rộng w2, cao h2):

# 1. Diện tích phần giao (Intersection) và phần hợp (Union):
w_giao = max(0, min(x2_1, x2_2) - max(x1_1, x1_2))
h_giao = max(0, min(y2_1, y2_2) - max(y1_1, y1_2))
Giao   = w_giao * h_giao
Hop    = (w1 * h1) + (w2 * h2) - Giao + eps
IoU    = Giao / Hop

# 2. Hình chữ nhật nhỏ nhất bao trọn cả 2 khung (Smallest Enclosing Box):
cw = max(x2_1, x2_2) - min(x1_1, x1_2)
ch = max(y2_1, y2_2) - min(y1_1, y1_2)
c2 = cw^2 + ch^2 + eps    # Bình phương đường chéo khung bao ngoài

# 3. Bình phương khoảng cách Euclid giữa 2 tâm khung (rho^2):
rho2 = ((x1_2 + x2_2 - x1_1 - x2_1)^2 + (y1_2 + y2_2 - y1_1 - y2_1)^2) / 4

# 4. Độ lệch tỉ lệ khung hình (aspect ratio consistency v) và hệ số trọng số alpha:
v     = (4 / pi^2) * (atan(w2 / h2) - atan(w1 / h1))^2
alpha = v / (1 - IoU + v + eps)

# 5. Công thức Complete IoU (CIoU):
CIoU  = IoU - (rho2 / c2 + v * alpha)
```

- **Đọc ra bằng lời**:
  - **`IoU` (Intersection over Union)** bằng diện tích phần giao nhau giữa hai khung chia cho diện tích phần hợp của chúng (`IoU` nằm từ `0` đến `1`). Nhược điểm của `IoU` thuần là nếu hai khung không chạm nhau (`Giao = 0` -> `IoU = 0`), đạo hàm bằng `0` nên mô hình không biết hai khung cách nhau xa hay gần; hoặc hai khung có cùng `IoU` nhưng lệch tâm hay méo tỉ lệ chiều rộng/chiều cao.
  - **`CIoU` (Complete IoU)** lấy `IoU` trừ đi hai khoản phạt hình học:
    1. `rho2 / c2`: Tỉ số giữa bình phương khoảng cách hai tâm khung (`rho2`) và bình phương đường chéo hình chữ nhật bao ngoài (`c2`) — phạt nặng khi tâm khung dự đoán lệch khỏi tâm khung thật.
    2. `v * alpha`: Phạt khi tỉ lệ `rộng / cao` (`w/h`) của khung dự đoán khác với khung thật.
- **So sánh với Frontend**: Giống như khi kiểm tra va chạm (collision detection) hoặc căn chỉnh một `div` vào đúng vị trí thiết kế Figma: `IoU` chỉ đo phần diện tích đè lên nhau, còn `CIoU` kiểm tra đồng thời cả 3 tiêu chí: **(1) diện tích chồng lấp (`IoU`)**, **(2) khoảng cách lệch tâm (`top/left center offset`)**, và **(3) tỉ lệ khung (`aspect-ratio`)**.

- **Ví dụ số bằng mã Python và đối chiếu với `ultralytics.utils.metrics.bbox_iou`** `[DỰ ÁN]`:

```python
import math, torch
from ultralytics.utils.metrics import bbox_iou

box1 = torch.tensor([[100.0, 100.0, 140.0, 150.0]])  # w1=40, h1=50, tâm (120, 125)
box2 = torch.tensor([[110.0, 110.0, 150.0, 150.0]])  # w2=40, h2=40, tâm (130, 130)

iou_ul = bbox_iou(box1, box2, xywh=False, CIoU=False).item()
ciou_ul = bbox_iou(box1, box2, xywh=False, CIoU=True).item()

inter = (min(140.0, 150.0) - max(100.0, 110.0)) * (min(150.0, 150.0) - max(100.0, 110.0))
union = 40.0 * 50.0 + 40.0 * 40.0 - inter
iou_manual = inter / union
cw, ch = max(140.0, 150.0) - min(100.0, 110.0), max(150.0, 150.0) - min(100.0, 110.0)
c2 = cw**2 + ch**2
rho2 = ((110.0 + 150.0 - 100.0 - 140.0)**2 + (110.0 + 150.0 - 100.0 - 150.0)**2) / 4.0
v = (4.0 / (math.pi**2)) * ((math.atan(40.0 / 40.0) - math.atan(40.0 / 50.0)) ** 2)
alpha = v / (1.0 - iou_manual + v)
ciou_manual = iou_manual - (rho2 / c2 + v * alpha)

print(f"inter={inter}, union={union}, IoU(manual)={iou_manual:.6f}, IoU(ultralytics)={iou_ul:.6f}")
print(f"rho2={rho2}, c2={c2}, v={v:.6f}, alpha={alpha:.6f}")
print(f"CIoU(manual)={ciou_manual:.6f}, CIoU(ultralytics)={ciou_ul:.6f}")
```

**Output nguyên văn:**
```text
inter=1200.0, union=2400.0, IoU(manual)=0.500000, IoU(ultralytics)=0.500000
rho2=125.0, c2=5000.0, v=0.004963, alpha=0.009828
CIoU(manual)=0.474951, CIoU(ultralytics)=0.474951
```
  - Kết quả tính từng bước (`0.500000` và `0.474951`) khớp tuyệt đối tới chữ số thập phân thứ 6 với hàm `bbox_iou` trong `ultralytics/utils/metrics.py`!

---

### 2.3. Biểu diễn khung (`dist2bbox` / `bbox2dist`) và `Distribution Focal Loss` (`DFL`)

- **Vị trí trong mã nguồn**:
  - Hàm `make_anchors`, `dist2bbox`, `bbox2dist`: `ultralytics/utils/tal.py:421-456` `[MÃ NGUỒN]`.
  - Lớp tích phân `DFL`: `ultralytics/nn/modules/block.py:60-82` `[MÃ NGUỒN]`.
  - Lớp hàm mất mát `DFLoss`: `ultralytics/utils/loss.py:89-109` (dẫn nguồn bài báo Generalized Focal Loss `https://arxiv.org/abs/2006.04388` tại dòng `92`) `[MÃ NGUỒN]`.
- **Công thức văn bản thuần**:

```text
# 1. Tọa độ điểm neo (anchor point) của ô lưới (i, j) trên bản đồ đặc trưng:
ax = i + 0.5
ay = j + 0.5

# 2. Giải mã khoảng cách 4 cạnh (l, t, r, b) bằng DFL (với reg_max = 16, k chạy từ 0 đến 15):
# Cho vector 16 số logit z = [z_0, z_1, ..., z_15] của 1 cạnh:
P(k) = exp(z_k) / sum_{m=0..15}(exp(z_m))       # Hàm Softmax
d    = sum_{k=0..15}( k * P(k) )                # Kỳ vọng toán học của khoảng cách (đơn vị: ô lưới)

# 3. Đổi từ 4 khoảng cách (l, t, r, b) sang tọa độ khung (dist2bbox) và nhân với bước nhảy stride s:
x1 = (ax - l) * s
y1 = (ay - t) * s
x2 = (ax + r) * s
y2 = (ay + b) * s

# 4. Đổi ngược từ khung nhãn thật về khoảng cách mục tiêu y (bbox2dist, bị kẹp trong [0, 15.99]):
# Giả sử khoảng cách thật của 1 cạnh là số thực y (ví dụ y = 2.7 ô lưới), nằm giữa 2 số nguyên:
tl = int(y)          # Cận nguyên bên trái (ví dụ: 2)
tr = tl + 1          # Cận nguyên bên phải (ví dụ: 3)
wl = tr - y          # Trọng số cho cận trái (ví dụ: 3 - 2.7 = 0.3)
wr = 1 - wl = y - tl # Trọng số cho cận phải (ví dụ: 2.7 - 2 = 0.7)

# 5. Hàm mất mát Distribution Focal Loss (DFLoss) cho 1 cạnh:
DFL(P, y) = -( wl * log(P(tl)) + wr * log(P(tr)) )
```

- **Đọc ra bằng lời**:
  - Thay vì bắt mạng nơ-ron đoán trực tiếp một con số thực duy nhất cho khoảng cách từ tâm ô lưới đến cạnh khung (ví dụ `d = 2,7` ô lưới), YOLOv8 chia khoảng cách từ `0` đến `15` ô lưới thành **16 mức nguyên (`reg_max = 16`)** và dự đoán xác suất `P(0), P(1), ..., P(15)` cho từng mức thông qua hàm `Softmax`. Khoảng cách dự đoán cuối cùng `d` là trung bình có trọng số `sum(k * P(k))` (được cài trong `block.py:72-82` bằng một tầng `Conv2d` cố định có trọng số `0, 1, 2, ..., 15` không huấn luyện `requires_grad=False`).
  - Khi huấn luyện, nếu khoảng cách thật của cạnh khung là `y = 2,7` ô lưới (nằm giữa mức `2` và mức `3`), hàm `DFLoss` (`loss.py:105-108`) ép mạng phải dồn `30%` xác suất (`wl = 3 - 2,7 = 0,3`) vào mức `2` và `70%` xác suất (`wr = 2,7 - 2 = 0,7`) vào mức `3`. Điều này giúp mô hình biểu diễn được cả độ bất định khi viền đầu người trong ảnh hồng ngoại bị mờ nhòe!

- **Ví dụ số bằng mã Python và đối chiếu với `DFL`, `dist2bbox`, `DFLoss` của Ultralytics** `[DỰ ÁN]`:

```python
import torch
import torch.nn.functional as F
from ultralytics.nn.modules.block import DFL
from ultralytics.utils.tal import dist2bbox
from ultralytics.utils.loss import DFLoss

dfl_mod = DFL(c1=16)
logits_1side = torch.full((1, 16, 1), -10.0)
logits_1side[0, 2, 0] = 1.38629436  # exp(1.38629436) ~ 4
logits_1side[0, 3, 0] = 2.07944154  # exp(2.07944154) ~ 8 (tỉ lệ xác suất mức 2 : mức 3 là 1/3 : 2/3 -> kỳ vọng ~ 2.667)
logits_4sides = logits_1side.repeat(1, 4, 1)  # shape (1, 64, 1)

pred_dist = dfl_mod(logits_4sides)
print("DFL output distance (4 sides, shape (1,4,1)):", pred_dist.squeeze().tolist())

anchor_pt = torch.tensor([[[50.5], [30.5]]])  # ô lưới (50, 30) -> tâm (50.5, 30.5)
decoded_box = dist2bbox(pred_dist, anchor_pt, xywh=False, dim=1)
print("Anchor point (grid units):", anchor_pt.squeeze().tolist(), "-> Decoded box (grid units):", decoded_box.squeeze().tolist())
print("Decoded box in pixels (stride=8):", (decoded_box.squeeze() * 8.0).tolist())

dfl_loss_fn = DFLoss(reg_max=16)
target_d = torch.tensor([2.7])
loss_1side = dfl_loss_fn(logits_1side.view(1, 16), target_d)
log_probs = F.log_softmax(logits_1side.view(1, 16), dim=-1)
manual_dfl = -(0.3 * log_probs[0, 2] + 0.7 * log_probs[0, 3]).item()
print(f"DFLoss for target=2.7: ultralytics={loss_1side.item():.6f}, manual={manual_dfl:.6f}")
```

**Output nguyên văn:**
```text
DFL output distance (4 sides, shape (1,4,1)): [2.666959285736084, 2.666959285736084, 2.666959285736084, 2.666959285736084]
Anchor point (grid units): [50.5, 30.5] -> Decoded box (grid units): [47.83304214477539, 27.833040237426758, 53.16695785522461, 33.16695785522461]
Decoded box in pixels (stride=8): [382.6643371582031, 222.66432189941406, 425.3356628417969, 265.3356628417969]
DFLoss for target=2.7: ultralytics=0.613462, manual=0.613462
```

---

### 2.4. Gán nhãn động trong lúc huấn luyện (`TaskAlignedAssigner` – TAL)

- **Vị trí trong mã nguồn**:
  - Khởi tạo trong `v8DetectionLoss.__init__`: `ultralytics/utils/loss.py:365-372` với các tham số cố định: `topk=10, num_classes=self.nc, alpha=0.5, beta=6.0, stride=self.stride.tolist()` `[MÃ NGUỒN]`.
  - Lớp `TaskAlignedAssigner`: `ultralytics/utils/tal.py:14-375` (`get_box_metrics` tại dòng `202-226`, `select_candidates_in_gts` tại dòng `300-335`, chuẩn hóa `target_scores` tại dòng `166-173`) `[MÃ NGUỒN]`.
- **Công thức văn bản thuần**:

```text
# Bước 1: Lọc ứng viên hình học (select_candidates_in_gts - tal.py:300-335):
# Chỉ xét các điểm neo (ax, ay) nằm bên trong khung nhãn thật (GT box).
# ĐẶC BIỆT (tal.py:328-333): Nếu khung thật có chiều rộng hoặc chiều cao nhỏ hơn stride_val (= 16 px),
# mã nguồn tự động nới rộng vùng kiểm tra của khung thật lên tối thiểu 16 px để tránh trường hợp
# vật thể quá nhỏ không chứa nổi bất kỳ điểm neo nào!

# Bước 2: Tính điểm căn chỉnh nhiệm vụ (Alignment Metric t - tal.py:223) cho mỗi cặp (khung thật, ô lưới):
# Với s = sigmoid(pred_logit) là điểm tự tin phân loại dự đoán của ô lưới,
# và  u = max(CIoU(pred_box, gt_box), 0) là độ chồng khít CIoU không âm,
# tham số mặc định alpha = 0.5, beta = 6.0:
t = (s ^ alpha) * (u ^ beta) = (s ^ 0.5) * (u ^ 6.0)

# Bước 3: Chọn Top-K (select_topk_candidates - tal.py:244-298):
# Với mỗi khung đầu thật, giữ lại tối đa topk = 10 ô lưới có điểm t cao nhất làm mẫu dương (positive anchors).
# Nếu 1 ô lưới lọt vào top-10 của nhiều khung thật cùng lúc, nó chỉ được gán cho khung thật nào có CIoU u lớn nhất (tal.py:366).

# Bước 4: Chuẩn hóa điểm mục tiêu mềm (Soft Target Score - tal.py:166-173):
# Với mỗi khung thật, gọi t_max là điểm t lớn nhất và u_max là CIoU lớn nhất trong các ô dương của nó:
target_score = (t / (t_max + eps)) * u_max
```

- **Đọc ra bằng lời**:
  - Khi huấn luyện trên ảnh `800x800`, có tới `13.125` ô lưới dự đoán nhưng trong ảnh chỉ có khoảng `5–6` cái đầu thật. Mô hình phải quyết định: **ô lưới nào chịu trách nhiệm học cái đầu nào?**
  - `TaskAlignedAssigner` giải quyết bằng 4 bước:
    1. Tìm các ô lưới có tâm nằm bên trong khung đầu thật (nếu đầu thật nhỏ hơn `16 px`, tự động nới vùng tìm kiếm lên `16 px`).
    2. Chấm điểm từng ô lưới bằng công thức `t = (s^0.5) * (u^6.0)`. Vì số mũ của `u` (`beta = 6.0`) lớn gấp 12 lần số mũ của `s` (`alpha = 0.5`), một ô lưới muốn đạt điểm `t` cao thì **khung bao nó dự đoán phải trùng khít với khung thật (`u` cao)** đồng thời điểm phân loại `s` cũng phải tốt.
    3. Chọn **10 ô lưới (`topk = 10`)** có điểm `t` cao nhất cho mỗi cái đầu thật làm "mẫu dương" (positive samples — phải học cả khung bao lẫn phân loại); tất cả các ô lưới còn lại làm "mẫu âm" (negative/background — nhãn mục tiêu bằng `0`).
    4. Thay vì gán nhãn cứng `1.0` cho cả 10 ô dương, `tal.py:169-171` gán **nhãn mềm `target_score = (t / t_max) * u_max`**. Nghĩa là ô lưới nào vẽ khung chuẩn nhất sẽ được nhận nhãn mục tiêu bằng đúng `u_max` (ví dụ `0.80`), còn các ô vẽ lệch hơn nhận nhãn mục tiêu thấp hơn (`0.20`). Nhờ vậy, khi suy luận thực tế, điểm `conf` của mô hình phản ánh trực tiếp cả chất lượng đóng khung!

- **Ví dụ số bằng mã Python (3 ô lưới ứng viên bên trong 1 khung đầu thật)** `[DỰ ÁN]`:

```python
import torch

s = torch.tensor([0.80, 0.70, 0.40])  # Điểm phân loại dự đoán của 3 ô lưới
u = torch.tensor([0.60, 0.75, 0.80])  # Độ chồng khít CIoU của 3 ô lưới với khung đầu thật
t = (s ** 0.5) * (u ** 6.0)           # alpha=0.5, beta=6.0 (tal.py:223)
t_max = t.max()
u_max = u.max()
norm_t = t * u_max / (t_max + 1e-9)   # tal.py:170

print("s:", s.tolist())
print("u (CIoU):", u.tolist())
print("align_metric t = s^0.5 * u^6.0:", [round(x, 6) for x in t.tolist()])
print("soft target_scores = t * u_max / t_max:", [round(x, 6) for x in norm_t.tolist()])
```

**Output nguyên văn:**
```text
s: [0.800000011920929, 0.699999988079071, 0.4000000059604645]
u (CIoU): [0.6000000238418579, 0.75, 0.800000011920929]
align_metric t = s^0.5 * u^6.0: [0.04173, 0.148908, 0.165794]
soft target_scores = t * u_max / t_max: [0.20136, 0.718516, 0.8]
```
  - Dù Ô số 1 có điểm phân loại cao nhất (`s = 0.80`) nhưng vì vẽ khung lệch (`u = 0.60`), lũy thừa bậc 6 (`0.60^6 = 0.0466`) kéo điểm căn chỉnh `t` xuống chỉ còn `0.04173` và nhãn mục tiêu mềm chỉ được gán `0.20136`. Ngược lại, Ô số 3 vẽ khung chuẩn nhất (`u = 0.80`) đạt điểm `t = 0.165794` cao nhất và được thưởng nhãn mục tiêu cao nhất `0.80`!


---

### 2.5. Hàm mất mát tổng (`v8DetectionLoss`): Các thành phần, Trọng số mặc định, Vì sao dự án 1 lớp vẫn có `cls_loss`, và Liên hệ `results.csv`

- **Vị trí trong mã nguồn**:
  - Lớp `v8DetectionLoss`: `ultralytics/utils/loss.py:345-486` (`__init__` tại dòng `348-375`, `__call__` tổng hợp 3 thành phần loss tại dòng `403-486`) `[MÃ NGUỒN]`.
  - Lớp `BboxLoss` (tính `loss_iou` và `loss_dfl`): `ultralytics/utils/loss.py:112-160` `[MÃ NGUỒN]`.
  - Trọng số mặc định của 3 thành phần loss: `ultralytics/cfg/default.yaml:104-107` (`box: 7.5`, `cls: 0.5`, `dfl: 1.5`) và `runs/detect/head_v2_official/args.yaml:83-86` `[TÀI LIỆU & DỰ ÁN]`.
- **Công thức văn bản thuần**:

```text
# Gọi N_tat_ca là tổng số ô lưới (13.125 ở imgsz=800), fg_mask là tập các ô dương (positive anchors),
# y_i là nhãn mục tiêu mềm (soft target_score ∈ [0, 1]) từ TaskAlignedAssigner:
target_scores_sum = max( sum_{i=1..N_tat_ca}( y_i ), 1.0 )

# 1. Thành phần Mất mát Khung bao (box_loss - loss.py:134-135, 457):
# Chỉ tính trên các ô dương (i ∈ fg_mask), có trọng số theo điểm y_i:
L_box_tho = sum_{i ∈ fg_mask}( (1.0 - CIoU_i) * y_i ) / target_scores_sum
box_loss  = hyp_box * L_box_tho      (với hyp_box = 7.5)

# 2. Thành phần Mất mát Phân loại (cls_loss - loss.py:349, 439-442, 458):
# Tính Binary Cross-Entropy With Logits (BCE) trên TẤT CẢ các ô lưới (cả ô dương lẫn ô nền y_i = 0):
BCE(z_i, y_i) = -( y_i * log(sigmoid(z_i)) + (1.0 - y_i) * log(1.0 - sigmoid(z_i)) )
L_cls_tho     = sum_{i=1..N_tat_ca}( BCE(z_i, y_i) ) / target_scores_sum
cls_loss      = hyp_cls * L_cls_tho  (với hyp_cls = 0.5)

# 3. Thành phần Mất mát Phân phối DFL (dfl_loss - loss.py:138-141, 459):
# Chỉ tính trung bình trên 4 cạnh (trái, trên, phải, dưới) của các ô dương (i ∈ fg_mask):
L_dfl_tho = sum_{i ∈ fg_mask}( mean_{canh ∈ {l,t,r,b}}( DFL(P_{i,canh}, d_{i,canh}) ) * y_i ) / target_scores_sum
dfl_loss  = hyp_dfl * L_dfl_tho      (với hyp_dfl = 1.5)

# 4. Tổng hàm mất mát dùng để tính đạo hàm lan truyền ngược (loss.py:486):
L_tong    = box_loss + cls_loss + dfl_loss
L_backprop = L_tong * batch_size
```

- **Đọc ra bằng lời**:
  - Tổng độ lỗi của mô hình là tổng có trọng số của 3 loại lỗi:
    1. **`box_loss` (nhân hệ số `7.5`)**: Phạt khi khung bao dự đoán tại các ô dương không trùng khít (`1 - CIoU`) với khung đầu thật.
    2. **`cls_loss` (nhân hệ số `0.5`)**: Phạt bằng hàm `BCEWithLogitsLoss` trên toàn bộ `13.125` ô lưới.
    3. **`dfl_loss` (nhân hệ số `1.5`)**: Phạt khi phân phối xác suất 16 mức của 4 cạnh khung tại các ô dương không tập trung sát vị trí cạnh thật.
- **Vì sao dự án CineSight chỉ có 1 lớp (`0: head`) nhưng vẫn có `cls_loss`?**
  - Trong YOLOv8 (kiến trúc không có nhánh `objectness` riêng như YOLOv5), nhánh phân loại `cv3` dùng hàm `nn.BCEWithLogitsLoss(reduction="none")` (`loss.py:349`) để giải bài toán phân loại nhị phân độc lập cho từng lớp: **"Tại ô lưới này CÓ ĐẦU NGƯỜI (`target_score > 0`) hay LÀ PHÔNG NỀN (`target_score = 0`)?"** `[MÃ NGUỒN: ultralytics/utils/loss.py:349, 439-442]`.
  - Nếu không có `cls_loss`, cả `13.125` ô lưới trên ảnh `800x800` (bao gồm ghế trống, tường, sàn rạp) đều không bị phạt khi báo nhầm là có đầu người, dẫn tới toàn bộ `13.125` ô đều xuất ra khung dự đoán!

- **Ví dụ số bằng mã Python và xu hướng thật trong `runs/detect/head_v2_official/results.csv`** `[DỰ ÁN]`:

```python
import csv

rows = []
with open(r"c:\CineSightApp\ai_service\runs\detect\head_v2_official\results.csv", encoding="utf-8") as f:
    for r in csv.DictReader(line for line in f if line.strip()):
        rows.append({k.strip(): float(v) for k, v in r.items()})

for ep_idx in (0, 14, 34, 49):  # Epoch 1, 15, 35 (best), 50 (last)
    r = rows[ep_idx]
    t_tot = r["train/box_loss"] + r["train/cls_loss"] + r["train/dfl_loss"]
    v_tot = r["val/box_loss"] + r["val/cls_loss"] + r["val/dfl_loss"]
    print(
        f"Epoch {int(r['epoch']):>2}: "
        f"Train(box={r['train/box_loss']:.4f}, cls={r['train/cls_loss']:.4f}, dfl={r['train/dfl_loss']:.4f}, sum={t_tot:.4f}) | "
        f"Val(box={r['val/box_loss']:.4f}, cls={r['val/cls_loss']:.4f}, dfl={r['val/dfl_loss']:.4f}, sum={v_tot:.4f})"
    )
```

**Output nguyên văn:**
```text
Epoch  1: Train(box=3.7700, cls=5.3738, dfl=1.3559, sum=10.4997) | Val(box=3.0896, cls=8.6947, dfl=1.0990, sum=12.8834)
Epoch 15: Train(box=1.9338, cls=1.3116, dfl=0.8739, sum=4.1192) | Val(box=2.4218, cls=4.1118, dfl=1.0027, sum=7.5363)
Epoch 35: Train(box=1.6726, cls=0.9544, dfl=0.8455, sum=3.4725) | Val(box=2.2362, cls=2.7601, dfl=0.9635, sum=5.9597)
Epoch 50: Train(box=1.5402, cls=0.9115, dfl=0.8618, sum=3.3135) | Val(box=2.1137, cls=2.8376, dfl=0.9791, sum=5.9304)
```
- **Nhận xét xu hướng thực tế trong lần chạy của bạn** `[DỰ ÁN: results.csv:3-52]`:
  - **`train/cls_loss` và `val/cls_loss` giảm mạnh nhất**: Ở Epoch 1, vì nhánh `cv3` vừa bị khởi tạo lại hoàn toàn (`36/355` tensor mới), `train/cls_loss = 5.3738` và `val/cls_loss = 8.6947`. Đến Epoch 35 (best), `train/cls_loss` giảm `82,2%` xuống `0.9544`, còn `val/cls_loss` giảm `68,3%` xuống `2.7601`.
  - **`box_loss` và `dfl_loss` giảm đều và hội tụ ổn định**: `train/box_loss` giảm từ `3.7700` (Epoch 1) -> `1.6726` (Epoch 35) -> `1.5402` (Epoch 50); `val/box_loss` giảm từ `3.0896` -> `2.2362` (Epoch 35) -> `2.0851` (Epoch 48).
  - Từ sau Epoch 35 đến Epoch 50 (nhất là từ Epoch 41 khi tắt Mosaic `close_mosaic = 10`), `val/cls_loss` dao động nhẹ quanh `2.74 – 3.09` và `mAP@0.5:0.95` không vượt qua đỉnh `0.3775` của Epoch 35.

---

### 2.6. Hậu xử lý (Post-processing): Ngưỡng `conf`, Thuật toán `NMS`, tham số `iou` và ảnh hưởng lên SỐ ĐẦU ĐẾM ĐƯỢC

- **Vị trí trong mã nguồn**:
  - Hàm `non_max_suppression`: `ultralytics/utils/nms.py:13-172` (lọc `xc = prediction[:, 4:mi].amax(1) > conf_thres` tại dòng `75`, gọi `TorchNMS.nms` tại dòng `146`) `[MÃ NGUỒN]`.
  - Thuật toán `TorchNMS.nms`: `ultralytics/utils/nms.py:245-300` `[MÃ NGUỒN]`.
  - Giá trị mặc định trong gói: `conf = 0.25` (khi `predict`) / `conf = 0.001` (khi `val`), `iou = 0.7`, `max_det = 300` `[TÀI LIỆU: ultralytics/cfg/default.yaml:55-57]`.
- **Công thức và Thuật toán từng bước (Văn bản thuần)**:

```text
# Đầu vào: 13.125 khung dự đoán (ở imgsz=800), mỗi khung có tọa độ [x1, y1, x2, y2] và điểm conf = sigmoid(logit).
# Tham số: ngưỡng tự tin conf_thres (0.25), ngưỡng chồng lấp iou_thres (0.70).

# BƯỚC 1 – Lọc theo ngưỡng conf (nms.py:75):
Giữ lại tập ứng viên B = { b_i | conf(b_i) > conf_thres }.
(Loại bỏ ngay lập tức hơn 99% số ô lưới có điểm tự tin thấp).

# BƯỚC 2 – Sắp xếp giảm dần theo điểm conf (nms.py:271):
Sắp xếp danh sách B theo thứ tự conf giảm dần: conf(b_0) >= conf(b_1) >= ... >= conf(b_{M-1}).
Khởi tạo danh sách giữ lại: Keep = [].

# BƯỚC 3 – Vòng lặp triệt tiêu cực đại không phải lớn nhất (Greedy NMS - nms.py:285-298):
Khi danh sách B vẫn còn khung:
  3.1. Lấy khung đứng đầu b_top (có conf cao nhất hiện tại) đưa vào Keep.
  3.2. Tính độ chồng lấp IoU(b_top, b_j) với tất cả các khung b_j còn lại trong B.
  3.3. XÓA mọi khung b_j có IoU(b_top, b_j) > iou_thres (vì bị coi là dự đoán trùng lên cùng 1 cái đầu với b_top).
  3.4. Lặp lại với các khung còn sót lại trong B cho đến khi B rỗng.
```

- **Đọc ra bằng lời**:
  - Do mỗi cái đầu thật có kích thước khoảng `10–25 px` phủ lên nhiều ô lưới cạnh nhau (và trong lúc huấn luyện `TaskAlignedAssigner` dạy tới `topk = 10` ô lưới cùng bắt 1 cái đầu), nên khi suy luận, quanh 1 cái đầu thường có từ 2 đến 6 ô lưới cùng xuất ra khung bao có `conf > 0.25`.
  - Thuật toán **NMS (Non-Maximum Suppression)** giữ lại duy nhất khung có điểm `conf` cao nhất trên cái đầu đó và xóa bỏ các khung lân cận có diện tích chồng lấp `IoU > iou_thres`.
- **Ảnh hưởng trực tiếp của `conf` và `iou` lên SỐ ĐẦU ĐẾM ĐƯỢC**:
  1. **Khi giảm `conf` (ví dụ `0.25 -> 0.15`)**: Nhiều khung mờ/nhiễu vượt qua Bước 1 -> **Số đầu đếm được TĂNG** (giảm nguy cơ bỏ sót khách thật, nhưng tăng báo giả `illegal_occupant`). Ngược lại, **tăng `conf` (`0.25 -> 0.40, 0.60`)** làm **Số đầu đếm được GIẢM** (tăng nguy cơ báo vắng mặt oan `missing_guest`).
  2. **Khi giảm `iou` của NMS (ví dụ `0.70 -> 0.50`)**: Điều kiện xóa ở Bước 3.3 khắt khe hơn (chỉ cần chồng lấp trên `50%` đã bị gộp làm 1) -> **Số đầu đếm được GIẢM hoặc giữ nguyên** (khử sạch các khung dự đoán kép quanh 1 cái đầu, nhưng nếu 2 người ngồi chụm đầu sát nhau có `IoU > 0.50` thì 1 người sẽ bị xóa mất). Ngược lại, **tăng `iou` (`0.60 -> 0.70, 0.85`)** làm **Số đầu đếm được TĂNG** (dễ bị đếm 1 đầu thành 2 đầu nếu 2 khung dự đoán lệch nhau có `IoU` nằm trong khoảng `[0.60, 0.70]`).

- **Ví dụ số bằng mã Python với 3 khung chồng nhau chạy qua `TorchNMS.nms`** `[DỰ ÁN]`:

```python
import torch
from ultralytics.utils.metrics import bbox_iou
from ultralytics.utils.nms import TorchNMS

boxes_nms = torch.tensor([
    [100.0, 100.0, 130.0, 130.0],  # Khung 0 (A): conf=0.85
    [104.0, 102.0, 134.0, 132.0],  # Khung 1 (B): conf=0.72 (chồng lên A với IoU=0.6791)
    [200.0, 100.0, 230.0, 130.0],  # Khung 2 (C): conf=0.60 (nằm cách xa A)
])
scores_nms = torch.tensor([0.85, 0.72, 0.60])

iou_ab = bbox_iou(boxes_nms[0:1], boxes_nms[1:2], xywh=False, CIoU=False).item()
iou_ac = bbox_iou(boxes_nms[0:1], boxes_nms[2:3], xywh=False, CIoU=False).item()
keep_70 = TorchNMS.nms(boxes_nms, scores_nms, iou_threshold=0.70)
keep_60 = TorchNMS.nms(boxes_nms, scores_nms, iou_threshold=0.60)

print(f"IoU(A,B)={iou_ab:.4f}, IoU(A,C)={iou_ac:.4f}")
print("Keep indices at iou=0.70:", keep_70.tolist(), "-> Kept boxes:", len(keep_70))
print("Keep indices at iou=0.60:", keep_60.tolist(), "-> Kept boxes:", len(keep_60))
```

**Output nguyên văn:**
```text
IoU(A,B)=0.6791, IoU(A,C)=0.0000
Keep indices at iou=0.70: [0, 1, 2] -> Kept boxes: 3
Keep indices at iou=0.60: [0, 2] -> Kept boxes: 2
```
  - Khung A (`conf=0.85`) và Khung B (`conf=0.72`) có `IoU = 0.6791`. Nếu để `iou = 0.70` (như mặc định trong `main.py`), vì `0.6791 <= 0.70`, Khung B **không bị xóa** và mô hình đếm thành **3 đầu** (đếm thừa 1 đầu). Khi hạ `iou = 0.60` (như trong `eval_counts.py`), vì `0.6791 > 0.60`, Khung B bị gộp vào Khung A và mô hình trả về đúng **2 đầu** (`[0, 2]`)!

---

### 2.7. Các chỉ số đánh giá: `TP / FP / FN`, `Precision`, `Recall`, `F1`, Đường cong `PR`, `AP`, `mAP@0.5`, `mAP@0.5:0.95` và Vì sao `mAP` không phải "Tỉ lệ đếm đúng"

- **Vị trí trong mã nguồn**:
  - Ghép cặp dự đoán với nhãn thật theo ngưỡng IoU (`match_predictions`): `ultralytics/engine/validator.py` & `ultralytics/utils/metrics.py:1062-1094` `[MÃ NGUỒN]`.
  - Hàm tính đường cong Precision–Recall, F1 và tích phân diện tích 101 điểm `ap_per_class`, `compute_ap`: `ultralytics/utils/metrics.py:762-890` `[MÃ NGUỒN]`.
  - Lớp `Metric` (`map50`, `map`, `fitness`): `ultralytics/utils/metrics.py:892-1013` `[MÃ NGUỒN]`.
- **Công thức văn bản thuần**:

```text
# Cho một ngưỡng chồng lấp IoU cố định tau (ví dụ tau = 0.50) và ngưỡng tự tin conf_thres:
# - TP (True Positive - Phát hiện đúng): Khung dự đoán có IoU >= tau với một khung đầu thật (mỗi khung thật chỉ ghép tối đa 1 lần).
# - FP (False Positive - Báo giả/Đếm thừa): Khung dự đoán có IoU < tau với mọi khung thật, hoặc ghép trùng vào khung thật đã có chủ.
# - FN (False Negative - Bỏ sót/Đếm thiếu): Khung đầu thật không có khung dự đoán nào đạt IoU >= tau.

# 1. Độ chính xác (Precision - P), Độ phủ (Recall - R) và Điểm hài hòa F1 (metrics.py:861-877):
Precision (P) = TP / (TP + FP + eps)
Recall    (R) = TP / (TP + FN + eps)
F1            = (2 * P * R) / (P + R + eps)

# 2. Đường cong Precision-Recall và Average Precision (AP - compute_ap tại metrics.py:762-791):
# Sắp xếp toàn bộ dự đoán theo conf giảm dần, tính P(k) và R(k) tích lũy khi hạ dần ngưỡng conf từ cao xuống thấp.
# Làm trơn đường bao trên của Precision (Precision Envelope - metrics.py:779):
mpre(r) = max_{r' >= r}( P(r') )

# Tính diện tích dưới đường cong bằng phương pháp nội suy 101 điểm chuẩn COCO (x = 0.00, 0.01, ..., 1.00 - metrics.py:784-786):
AP(tau) = Tich_phan_hinh_thang_{x ∈ [0.00, 0.01, ..., 1.00]}( mpre(x) )

# 3. mAP@0.5 và mAP@0.5:0.95 (metrics.py:967-991):
mAP@0.5      = Trung bình của AP(0.50) trên tất cả các lớp (với 1 lớp head thì mAP@0.5 = AP(0.50)).
mAP@0.5:0.95 = ( AP(0.50) + AP(0.55) + AP(0.60) + ... + AP(0.95) ) / 10
```

- **Đọc ra bằng lời**:
  - **`Precision` (`P`)** trả lời câu hỏi: *"Trong các cái đầu mà mô hình khoanh được, bao nhiêu phần trăm thực sự là đầu người?"* (`P` thấp nghĩa là hay báo giả ghế trống thành có người).
  - **`Recall` (`R`)** trả lời câu hỏi: *"Trong tổng số đầu người thật đang ngồi trong rạp, mô hình tìm ra được bao nhiêu phần trăm?"* (`R` thấp nghĩa là hay bỏ sót người ngồi trong rạp).
  - **`F1`** là trung bình điều hòa của `P` và `R`; trong `metrics.py:885-886`, Ultralytics báo cáo `P` và `R` trên bảng kết quả tại ngưỡng `conf` làm cho đường cong `F1` đã làm mượt đạt giá trị lớn nhất (`max-F1`).
  - **`AP` (`mAP@0.5`)** là diện tích dưới đường cong `Precision–Recall` ở ngưỡng `IoU = 0.50` (tích phân hình thang trên 101 mốc Recall từ `0.00` đến `1.00`). Còn **`mAP@0.5:0.95`** là trung bình cộng của `AP` tại 10 mức `IoU` ngày càng khắt khe (`0.50, 0.55, 0.60, ..., 0.95`).

- **Ví dụ số bằng mã Python (10 khung đầu thật, 8 khung dự đoán) đối chiếu với `ap_per_class` của Ultralytics** `[DỰ ÁN]`:

```python
import numpy as np
from ultralytics.utils.metrics import ap_per_class

# Giả sử có 10 khung đầu thật (lớp 0) và mô hình xuất ra 8 khung dự đoán có conf và IoU thực tế như sau:
confs_ex = np.array([0.92, 0.85, 0.78, 0.71, 0.64, 0.55, 0.42, 0.31])
ious_ex  = np.array([0.88, 0.76, 0.62, 0.35, 0.81, 0.54, 0.20, 0.68])  # Dự đoán thứ 4 (0.35) và thứ 7 (0.20) là FP ở IoU=0.5

iouv = np.linspace(0.5, 0.95, 10)               # 10 mức IoU: [0.50, 0.55, ..., 0.95]
tp_matrix = ious_ex[:, None] >= iouv[None, :]   # Ma trận (8, 10) True/False
pred_cls_ex = np.zeros(8)
target_cls_ex = np.zeros(10)                    # 10 khung thật thuộc lớp 0

tp_out, fp_out, p_out, r_out, f1_out, ap_out, *_ = ap_per_class(
    tp_matrix, confs_ex, pred_cls_ex, target_cls_ex, plot=False
)

tp_50 = int(tp_matrix[:, 0].sum())
fp_50 = len(confs_ex) - tp_50
fn_50 = len(target_cls_ex) - tp_50
prec_all = tp_50 / (tp_50 + fp_50)
rec_all  = tp_50 / (tp_50 + fn_50)
f1_all   = 2 * prec_all * rec_all / (prec_all + rec_all)

print(f"At conf>=0.31 (IoU=0.5): TP={tp_50}, FP={fp_50}, FN={fn_50}, P={prec_all:.4f}, R={rec_all:.4f}, F1={f1_all:.4f}")
print(f"Ultralytics ap_per_class max-F1 point: P={p_out[0]:.4f}, R={r_out[0]:.4f}, F1={f1_out[0]:.4f}")
print(f"Ultralytics AP across 10 IoU thresholds (0.50..0.95): {[round(float(x), 4) for x in ap_out[0]]}")
print(f"mAP@0.5 = {ap_out[0, 0]:.4f}, mAP@0.5:0.95 = {ap_out[0].mean():.4f}")
```

**Output nguyên văn:**
```text
At conf>=0.31 (IoU=0.5): TP=6, FP=2, FN=4, P=0.7500, R=0.6000, F1=0.6667
Ultralytics ap_per_class max-F1 point: P=0.7500, R=0.6000, F1=0.6667
Ultralytics AP across 10 IoU thresholds (0.50..0.95): [0.5367, 0.4375, 0.4375, 0.305, 0.255, 0.255, 0.135, 0.095, 0.0, 0.0]
mAP@0.5 = 0.5367, mAP@0.5:0.95 = 0.2457
```

- **Vì sao `mAP` KHÔNG PHẢI là "Tỉ lệ đếm đúng số người" hay "Tỉ lệ cảnh báo ghế đúng"?**
  1. `mAP` tích phân trên **mọi ngưỡng `conf` từ `0.001` đến `1.0`** `[TÀI LIỆU: default.yaml:55]`, trong khi khi chạy thật (`main.py:422`), bạn phải chốt cứng **một ngưỡng duy nhất `conf = 0.25`**.
  2. Trong ví dụ trên, có `10` người thật và mô hình xuất `8` khung (sai lệch số lượng chỉ là `|8 - 10| = 2 người`, tương đương đếm đạt `80%` quy mô), nhưng vì trong `8` khung đó có `2` khung lệch (`FP = 2`) và bỏ sót `4` người (`FN = 4`), nên `mAP@0.5` chỉ là `0.5367` (`53,67%`) và `mAP@0.5:0.95` chỉ là `0.2457` (`24,57%`).
  3. Ngược lại, nếu trong 1 ảnh mô hình bỏ sót 1 người ở ghế `A01` (`FN = 1`) đồng thời báo giả 1 cái bóng ở ghế `K10` (`FP = 1`), thì **tổng số đầu đếm được vẫn bằng đúng số người thật (`Sai số đếm = 0`)**, nhưng nghiệp vụ rạp phim lại phát sinh **2 cảnh báo sai cùng lúc** (báo vắng khách oan ở `A01` và báo khách lậu oan ở `K10`)!

---

### 2.8. Chi phí tính toán: `FLOPs`, Số tham số và Thời gian suy luận thực tế trên CPU (`imgsz = 320` vs `640` vs `800`)

- **Vị trí trong mã nguồn**:
  - Hàm đếm tham số `get_num_params` và tính `get_flops` (dùng gói `thop`): `ultralytics/utils/torch_utils.py:582-585, 639-679` `[MÃ NGUỒN]`.
- **Công thức văn bản thuần**:

```text
# 1. Tổng số tham số (Parameters):
N_params = sum_{mọi tensor trọng số W, bias b trong mô hình}( số_phần_tử(W) + số_phần_tử(b) )

# 2. Số phép tính dấu phẩy động (GFLOPs - torch_utils.py:676):
# Một phép nhân-cộng (MAC - Multiply-Accumulate) được tính bằng 2 FLOPs:
GFLOPs(imgsz) = ( Tổng_số_MACs_ở_kích_thước_imgsz * 2 ) / 10^9

# Tỉ lệ GFLOPs khi thay đổi kích thước ảnh đầu vào từ imgsz_1 sang imgsz_2 (với mạng thuần tích chập):
GFLOPs(imgsz_2) = GFLOPs(imgsz_1) * ( (imgsz_2 / imgsz_1) ^ 2 )
```

- **Đọc ra bằng lời**:
  - **Số tham số (`Parameters`)** là số lượng con số thực (`float32`/`float16`) lưu trong tệp `.pt` trên ổ đĩa — đại lượng này cố định theo kiến trúc mạng, không phụ thuộc kích thước ảnh. Với `best_head_v2.pt`, số tham số trước khi gộp BatchNorm là **`3.011.043` tham số** (`129 lớp`), và sau khi gộp `Conv + BatchNorm` (`fuse()`) khi suy luận là **`3.005.843` tham số** (`72 lớp`) `[DỰ ÁN: output model.info() và model.val()]`.
  - **`GFLOPs` (tỷ phép tính dấu phẩy động)** tỉ lệ thuận với diện tích bức ảnh đầu vào (`H x W`). Ở `imgsz = 640`, mô hình tốn **`8,1917 GFLOPs`** (~`8,2 GFLOPs`); ở `imgsz = 800`, tốn **`12,7995 GFLOPs`** (~`12,8 GFLOPs`); còn ở `imgsz = 320`, tốn `8,1917 * (320/640)^2 = 2,0479 GFLOPs` (~`2,0 GFLOPs`).
- **Thời gian suy luận thực tế trên CPU (`AMD Ryzen 5 3500U`) đo 10 lần (không tính lần chạy đầu warmup)** `[DỰ ÁN: Thí nghiệm B trong tools/yolo_lab.py]`:
  - Đoạn mã đo tốc độ nằm tại hàm `exp_b_imgsz_sweep` trong `c:\CineSightApp\ai_service\tools\yolo_lab.py:84-127` (chạy 1 lần warmup trước cho mỗi `imgsz`, sau đó bấm giờ `time.perf_counter()` 10 lần liên tiếp trên ảnh `val/room1_cam_edited_0346s.jpg`):
    - **`imgsz = 320`** (sau LetterBox `auto=True` là `320x192`): Trung bình **`86,3 ms ± 5,7 ms`** / ảnh (~`11,6 FPS`).
    - **`imgsz = 640`** (sau LetterBox `auto=True` là `640x384`): Trung bình **`151,8 ms ± 12,1 ms`** / ảnh (~`6,6 FPS`).
    - **`imgsz = 800`** (cấu hình thật trong `main.py`, sau LetterBox `auto=True` là `800x480`): Trung bình **`193,5 ms ± 11,8 ms`** / ảnh (~`5,2 FPS`).

---

## PHẦN 3: CÁC PHƯƠNG PHÁP HUẤN LUYỆN TRONG DỰ ÁN
*(Trả lời Yêu cầu (3) của Giảng viên: Các phương pháp huấn luyện)*

### 3.1. Tổng quan vòng lặp huấn luyện (`BaseTrainer._do_train`) và So sánh với phát triển Web/App
Đọc trực tiếp hàm `BaseTrainer._do_train` tại `ultralytics/engine/trainer.py:457-693` `[MÃ NGUỒN]`, một chu trình huấn luyện diễn ra như sau:

```text
[Đọc ảnh + nhãn từ đĩa (98 ảnh train)]
        │
        ▼  (1) Tăng cường dữ liệu (Data Augmentation: Mosaic 4 ảnh, HSV, dịch chuyển, co dãn, lật ngang)
[Lô dữ liệu (Mini-batch = 4 ảnh, kích thước 800x800)]
        │
        ▼  (2) Lan truyền tiến (Forward Pass - trainer.py:537):
        │      Mô hình dự đoán thử trên 4 ảnh -> TaskAlignedAssigner gán nhãn -> Tính L_tong (box + cls + dfl)
[Giá trị độ lỗi Loss của lô hiện tại]
        │
        ▼  (3) Lan truyền ngược (Backward Pass - trainer.py:553):
        │      loss.backward() tính đạo hàm (gradient) của độ lỗi theo từng trọng số trong 3.011.043 tham số
[Tích lũy đạo hàm qua accumulate = 64 / 4 = 16 lô (trainer.py:312, 586)]
        │
        ▼  (4) Cập nhật trọng số (optimizer_step - trainer.py:587, 884-896):
        │      Cắt ngưỡng đạo hàm (clip_grad_norm_ max_norm=10.0) -> AdamW cập nhật trọng số -> Cập nhật bản sao mượt ModelEMA
[Kết thúc 1 Epoch (duyệt hết 98 ảnh train = 25 lô batch=4)]
        │
        ▼  (5) Đánh giá trên tập Val (self.validate() - trainer.py:640):
        │      Dùng bản sao ModelEMA chấm điểm trên 22 ảnh val -> Tính P, R, mAP@0.5, mAP@0.5:0.95 và điểm fitness
        ▼  (6) Lưu Checkpoint & Kiểm tra Dừng sớm (save_model & stopper - trainer.py:648-655, 751-815):
               Ghi last.pt ở mọi epoch; nếu fitness đạt kỷ lục mới thì ghi đè best.pt; lặp lại đủ 50 epochs.
```

- **So sánh với quy trình làm Frontend (React/Flutter)**:
  - **Dữ liệu `train` (98 ảnh)** giống như bộ **Unit Test Fixtures** dùng trong lúc dev đang viết code; **dữ liệu `val` (22 ảnh)** giống như bộ **Staging Integration Tests** chạy tự động sau mỗi lần build; còn **dữ liệu `test` (43 ảnh)** giống như **UAT / Production Smoke Test** chỉ chạy khi nghiệm thu.
  - **1 Mini-batch (`batch = 4`)** giống như xử lý 1 trang phân trang (`pageSize = 4`), và **1 Epoch** là một lượt vòng lặp `.forEach()` duyệt hết cả 98 ảnh trong mảng `train` (`ceil(98 / 4) = 25 batches`).
  - **Forward -> Loss -> Backward -> Optimizer Step** giống như: Render giao diện (`Forward`) -> Chạy công cụ so khớp ảnh chụp màn hình với bản thiết kế để đo độ lệch pixel (`Loss`) -> Tìm xem thuộc tính CSS nào (`padding`, `width`, `color`) gây ra độ lệch đó (`Backward gradient`) -> Sửa lại các thuộc tính CSS đó một chút theo hướng giảm lỗi (`Optimizer Step`).

---

### 3.2. Học chuyển giao (Transfer Learning): Vì sao khởi tạo từ `yolov8n.pt`, lớp nào giữ nguyên, lớp nào khởi tạo lại, và `freeze` dùng để làm gì?

- **Vì sao bắt đầu từ `yolov8n.pt` thay vì khởi tạo ngẫu nhiên (`pretrained=False`)?**
  - Tập dữ liệu huấn luyện của dự án chỉ có **98 bức ảnh** (`570` cái đầu) `[DỰ ÁN: manifest.csv]`. Nếu khởi tạo ngẫu nhiên `3.011.043` tham số, mạng nơ-ron không có đủ dữ liệu để tự học cách nhận biết các đặc trưng thị giác nền tảng (cạnh thẳng, góc cong, độ tương phản sáng–tối, hình khối cầu) và sẽ học vẹt ngay lập tức `[KIẾN THỨC CHUNG – chưa kiểm chứng trong lượt này]`.
  - Tệp `yolov8n.pt` đã được huấn luyện sẵn trên tập dữ liệu COCO (hàng trăm nghìn ảnh tự nhiên thuộc 80 lớp, trong đó lớp `0: person` có sẵn hàng chục nghìn người). Nhờ đó, toàn bộ phần **Backbone** và **Neck** đã biết cách trích xuất đường viền đầu, vai và hình khối con người.
- **Cơ chế nạp trọng số trong mã nguồn và Chính xác những tầng nào giữ nguyên vs khởi tạo lại**:
  - Trong `ultralytics/nn/tasks.py:317-346` `[MÃ NGUỒN]`, hàm `BaseModel.load(weights)` gọi `updated_csd = intersect_dicts(csd, self.state_dict())` (`tasks.py:330`, định nghĩa tại `ultralytics/utils/torch_utils.py:730-741`), chỉ chép những tensor nào **trùng tên khóa (`key`) VÀ trùng khớp hoàn toàn kích thước (`v.shape == db[k].shape`)**.
  - Kiểm chứng bằng mã Python giữa `yolov8n.pt` (`nc = 80`) và `best_head_v2.pt` (`nc = 1`) `[DỰ ÁN: output kiểm tra state_dict]`:
    - Tổng số tensor trong `state_dict()` của mô hình là **`355` items** (gồm các `weight`, `bias`, `running_mean`, `running_var`, `num_batches_tracked`).
    - Có **`319 / 355` items (89,86%) được giữ nguyên 100% từ `yolov8n.pt`**, bao gồm:
      - Toàn bộ **Backbone** (Tầng `0..9`).
      - Toàn bộ **Neck** (Tầng `10..21`).
      - Toàn bộ **nhánh hồi quy khung bao `model.22.cv2`** và **`model.22.dfl`** của Tầng `22 (Detect)`! (Vì số kênh nhánh đóng khung `4 * reg_max = 64` không phụ thuộc vào số lớp `nc`!).
    - Có đúng **`36 / 355` items (10,14%) bị khởi tạo lại từ đầu**, toàn bộ đều nằm ở **nhánh phân loại `model.22.cv3`** trên 3 mức lưới (`cv3.0`, `cv3.1`, `cv3.2`), vì ở `yolov8n.pt` (`nc = 80`), số kênh ẩn `c3 = max(64, min(80, 100)) = 80` và kênh đầu ra là `80`, trong khi ở `best_head_v2.pt` (`nc = 1`), `c3 = max(64, min(1, 100)) = 64` và kênh đầu ra là `1`:
      - `model.22.cv3.{0,1,2}.0.conv.weight` và 4 tensor `bn` đi kèm: đổi từ `(80, ch, 3, 3)` sang `(64, ch, 3, 3)` (`15` items).
      - `model.22.cv3.{0,1,2}.1.conv.weight` và 4 tensor `bn` đi kèm: đổi từ `(80, 80, 3, 3)` sang `(64, 64, 3, 3)` (`15` items).
      - `model.22.cv3.{0,1,2}.2.{weight, bias}`: đổi từ `(80, 80, 1, 1)` và `(80,)` sang `(1, 64, 1, 1)` và `(1,)` (`6` items).
- **Tùy chọn đóng băng tầng (`freeze`) dùng để làm gì?**
  - Trong `ultralytics/engine/trainer.py:370-398` `[MÃ NGUỒN]`, nếu truyền `freeze = N` (ví dụ `freeze = 10`), vòng lặp sẽ đặt `v.requires_grad = False` cho toàn bộ các tầng từ `model.0.` đến `model.9.` (tức đóng băng toàn bộ Backbone) và giữ trạng thái `eval()` cho các lớp `BatchNorm2d` của chúng (`trainer.py:748-749`). Lưu ý: tầng `.dfl` luôn luôn bị đóng băng mặc định (`always_freeze_names = [".dfl"]` tại `trainer.py:378`).
  - **Tác dụng**: Giữ cố định bộ trích xuất đặc trưng gốc để tránh làm hỏng trọng số tiền huấn luyện khi tập dữ liệu mới quá nhỏ (dưới 50 ảnh) và giúp giảm thời gian tính đạo hàm trên CPU. Trong lần chạy chính thức (`args.yaml:32`), dự án để `freeze: null` (cho phép tinh chỉnh toàn mạng để thích nghi với ảnh hồng ngoại đơn sắc).

---

### 3.3. Bảng siêu tham số đầy đủ: Đối chiếu `args.yaml` của dự án với `ultralytics/cfg/default.yaml`
Tệp `c:\CineSightApp\ai_service\runs\detect\head_v2_official\args.yaml` có tổng cộng **115 khóa cấu hình** `[DỰ ÁN: args.yaml:1-115]`, đối chiếu trực tiếp với tệp cấu hình gốc `c:\CineSightApp\ai_service\venv\Lib\site-packages\ultralytics\cfg\default.yaml:1-139` `[TÀI LIỆU]`.

Dưới đây là bảng phân tích chi tiết theo 6 nhóm chức năng cho toàn bộ các siêu tham số huấn luyện/suy luận cốt lõi (và ghi chú rõ những tham số chỉ thuộc tác vụ khác như `segment/pose/obb/classify`):

#### Nhóm 1: Dữ liệu & Phần cứng (`Data & Hardware`)
| Tham số (`args.yaml`) | Giá trị tôi dùng (`args.yaml`) | Giá trị mặc định (`default.yaml`) | Ý nghĩa kỹ thuật | Tăng hoặc giảm thì ảnh hưởng gì? | Có nên đổi cho bài toán đầu người trong rạp không? |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`imgsz`** | **`800`** (`dòng 9`) | `640` (`dòng 20`) | Kích thước cạnh dài của ảnh sau khi qua `LetterBox` đưa vào mạng. | **Tăng (`800, 960`)**: Đầu người ở hàng xa giữ được nhiều pixel hơn (tăng Recall), nhưng GFLOPs và thời gian CPU tăng bậc hai. **Giảm (`320, 640`)**: Chạy nhanh hơn nhưng đầu ở xa bị co dưới `8 px`, mất dấu. | **Giữ `800` hoặc nâng lên `960`** nếu có GPU; tuyệt đối không hạ xuống `320/480` `[DỰ ÁN: Thí nghiệm B]`. |
| **`batch`** | **`4`** (`dòng 8`) | `16` (`dòng 19`) | Số lượng ảnh xử lý song song trong 1 lần lan truyền tiến (mini-batch). | **Tăng (`16, 32`)**: Ước lượng đạo hàm và thống kê `BatchNorm` ổn định hơn nhưng tốn RAM/VRAM. **Giảm (`4`)**: Tiết kiệm RAM trên CPU; Ultralytics tự bù bằng cách cộng dồn đạo hàm qua `accumulate = 64 / 4 = 16` bước (`trainer.py:312`). | **Giữ `4` hoặc `8`** trên máy CPU hiện tại để không tràn RAM. |
| **`device`** | **`cpu`** (`dòng 13`) | `null` (tự chọn GPU nếu có, `dòng 24`) | Thiết bị phần cứng chạy tính toán tensor. | Chuyển sang `cuda:0` (GPU) giúp huấn luyện và suy luận nhanh hơn gấp 10–30 lần so với `cpu`. | Trên máy hiện tại (`torch 2.14.0+cpu`), bắt buộc dùng `cpu`. |
| **`workers`** | **`2`** (`dòng 14`, bị ép về `0` ở `trainer.py:171`) | `8` (`dòng 25`) | Số tiến trình con nạp dữ liệu (`DataLoader`). **Lưu ý mã nguồn**: Khi `device='cpu'`, `trainer.py:170-171` tự động ghi đè `self.args.workers = 0`! | Trên GPU, tăng `workers` giúp CPU đọc ảnh kịp tốc độ GPU; nhưng trên CPU, `workers = 0` tránh chi phí tạo tiến trình đa luồng trên Windows. | **Không cần đổi** vì `trainer.py:171` luôn tự ép về `0` khi chạy trên CPU. |
| **`cache`** | **`false`** (`dòng 12`) | `false` (`dòng 23`) | Nạp trước toàn bộ ảnh vào RAM (`ram`) hoặc lưu tệp `.npy` trên đĩa (`disk`). | Bật `cache='ram'` giúp bỏ qua bước giải mã JPEG ở mỗi epoch, tăng tốc đọc ảnh. | Với 98 ảnh nhẹ (~50 MB), có thể bật `cache='ram'` nếu huấn luyện lại. |
| **`fraction`** | **`1.0`** (`dòng 30`) | `1.0` (`dòng 38`) | Tỉ lệ tập dữ liệu `train` được lấy ra để huấn luyện (`1.0` = 100%). | Giảm xuống `< 1.0` chỉ dùng khi muốn chạy thử (debug) nhanh trên một phần nhỏ dữ liệu. | **Giữ nguyên `1.0`** vì tập dữ liệu của dự án vốn đã nhỏ (98 ảnh). |
| **`rect`** | **`false`** (`dòng 25`) | `false` (`dòng 33`) | Huấn luyện chữ nhật tối thiểu (gom các ảnh cùng tỉ lệ `16:9` để đệm ít viền xám hơn). | Bật `rect=True` giảm lượng viền xám khi train nhưng **không tương thích tốt với ghép 4 ảnh `mosaic=1.0`** và tắt xáo trộn ngẫu nhiên (`shuffle`). | **Giữ `false` khi train** (khi chạy `val` và `predict`, Ultralytics tự động dùng chữ nhật `auto=True`). |
| **`single_cls`** | **`false`** (`dòng 24`) | `false` (`dòng 32`) | Gộp tất cả các lớp trong bộ dữ liệu thành 1 lớp duy nhất `0: item` (`trainer.py:842-845`). | Chỉ có tác dụng khi bộ dữ liệu gốc có nhiều lớp (`nc > 1`) mà muốn gộp chung. | Bộ dữ liệu `dataset_head_v2.yaml` đã có `nc: 1` (`head`), nên `false` hay `true` đều như nhau. |

#### Nhóm 2: Bộ tối ưu & Tốc độ học (`Optimizer & Learning Rate Schedule`)
| Tham số (`args.yaml`) | Giá trị tôi dùng (`args.yaml`) | Giá trị mặc định (`default.yaml`) | Ý nghĩa kỹ thuật | Tăng hoặc giảm thì ảnh hưởng gì? | Có nên đổi cho bài toán đầu người trong rạp không? |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`optimizer`** | **`auto`** (`dòng 20`) | `auto` (`dòng 29`) | Thuật toán cập nhật trọng số. Khi để `auto`, `trainer.py:1143-1152` tự chọn `AdamW` (nếu số bước `<= 10.000`) hoặc `MuSGD` (nếu `> 10.000`). | Với dự án này (`100 bước <= 10.000`), `auto` tự động chọn **`AdamW`** và **bỏ qua `lr0=0.01`, `momentum=0.937`** để dùng `lr = 0.002`, `momentum = 0.9`! | **Giữ `auto` (tức `AdamW`)** là phù hợp cho tập dữ liệu nhỏ và ít epoch (50 epochs). |
| **`lr0`** | **`0.01`** (`dòng 74`, bị `auto` ghi đè thành **`0.002`**) | `0.01` (`dòng 95`) | Tốc độ học ban đầu (Initial Learning Rate). **Lưu ý**: Chỉ có hiệu lực nếu đặt `optimizer` khác `auto`! | **Tăng quá cao**: Loss nhảy loạn hoặc nổ `NaN`, làm hỏng trọng số tiền huấn luyện. **Giảm quá thấp**: Học rất chậm, không hội tụ kịp trong 50 epochs. | Mức `lr = 0.002` do `auto` tính cho `nc=1` đã giúp mô hình hội tụ mượt. |
| **`lrf`** | **`0.01`** (`dòng 75`) | `0.01` (`dòng 96`) | Tỉ lệ tốc độ học cuối cùng so với ban đầu: `lr_cuoi = lr0 * lrf` (`= 0.002 * 0.01 = 0.00002`). | Tăng `lrf` (ví dụ `0.1`) giữ tốc độ học ở các epoch cuối cao hơn; giảm `lrf` giúp tinh chỉnh bước cực nhỏ ở cuối quá trình. | **Giữ nguyên `0.01`**. |
| **`cos_lr`** | **`false`** (`dòng 26`) | `false` (`dòng 34`) | Dùng lịch giảm tốc độ học hình cosin (`one_cycle` trong `torch_utils.py:775`) thay vì giảm tuyến tính bậc nhất (`trainer.py:265`). | Bật `cos_lr=True` giúp tốc độ học giảm chậm ở đầu/cuối và giảm nhanh ở đoạn giữa. | Có thể giữ `false` (tuyến tính) hoặc bật `true` đều ít tạo khác biệt lớn ở 50 epochs. |
| **`momentum`** | **`0.937`** (`dòng 76`, bị `auto` ghi đè thành **`0.9`**) | `0.937` (`dòng 97`) | Hệ số quán tính của SGD hoặc hệ số `beta1` của AdamW (`trainer.py:1171`). | Giúp hướng cập nhật trọng số mượt mà, không bị đổi chiều đột ngột bởi 1 lô dữ liệu nhiễu. | **Giữ mặc định** (`0.9` với `AdamW`). |
| **`weight_decay`** | **`0.0005`** (`dòng 77`) | `0.0005` (`dòng 98`) | Hệ số phạt chuẩn L2 lên trọng số (`decay = weight_decay * batch * accumulate / nbs = 0.0005 * 4 * 16 / 64 = 0.0005` tại `trainer.py:313`). | **Tăng**: Chống học vẹt (overfitting) mạnh hơn bằng cách ép trọng số nhỏ lại. **Giảm**: Mô hình tự do khớp dữ liệu train hơn. | **Giữ nguyên `0.0005`**. |
| **`nbs`** | **`64`** (`dòng 94`) | `64` (`dòng 115`) | Kích thước lô danh nghĩa (Nominal Batch Size) dùng để tính số bước tích lũy đạo hàm `accumulate = round(nbs / batch) = 16`. | Đảm bảo dù chạy `batch = 4` trên CPU thì mỗi lần cập nhật trọng số vẫn tương đương nhìn qua `64` ảnh. | **Giữ nguyên `64`**. |
| **`warmup_epochs`** | **`3.0`** (`dòng 78`) | `3.0` (`dòng 99`) | Số epoch khởi động đầu tiên (`nw = round(3.0 * 25) = 75` bước lô) để tăng dần `lr` từ `0` lên `lr0`. | Tránh cú sốc đạo hàm lớn ở những lô đầu tiên khi nhánh `cv3` mới khởi tạo ngẫu nhiên. | **Giữ nguyên `3.0`**. |
| **`warmup_momentum`** | **`0.8`** (`dòng 79`) | `0.8` (`dòng 100`) | Giá trị `momentum` bắt đầu trong giai đoạn warmup (tăng tuyến tính từ `0.8` lên `0.9`). | Giúp giai đoạn khởi động thích nghi nhanh với hướng đạo hàm mới. | **Giữ nguyên `0.8`**. |
| **`warmup_bias_lr`** | **`0.1`** (`dòng 80`, bị `auto` đặt về **`0.0`** ở `trainer.py:1152`) | `0.1` (`dòng 101`) | Tốc độ học khởi đầu của các tham số `bias` trong giai đoạn warmup. Với `optimizer=auto` (`AdamW`), `trainer.py:1152` đặt về `0.0` để tránh vọt lố. | Với SGD, `0.1` giúp `bias` hội tụ nhanh về xác suất nền; với AdamW cần đặt `0.0`. | **Không cần chỉnh** vì `auto` đã tự đặt `0.0`. |

#### Nhóm 3: Điều kiện dừng & Lưu trữ (`Stopping & Checkpointing`)
| Tham số (`args.yaml`) | Giá trị tôi dùng (`args.yaml`) | Giá trị mặc định (`default.yaml`) | Ý nghĩa kỹ thuật | Tăng hoặc giảm thì ảnh hưởng gì? | Có nên đổi cho bài toán đầu người trong rạp không? |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`epochs`** | **`50`** (`dòng 5`) | `100` (`dòng 16`) | Tổng số lượt duyệt qua toàn bộ 98 ảnh `train`. | Tăng lên `100` tốn gấp đôi thời gian CPU (~4 giờ); trong thực tế mô hình đã đạt đỉnh ở Epoch 35. | **50 epochs là hợp lý** cho 98 ảnh trên CPU. |
| **`patience`** | **`20`** (`dòng 7`) | `100` (`dòng 18`) | Số epoch tối đa chờ đợi nếu điểm `fitness` (`mAP@0.5:0.95`) không tăng thêm trước khi dừng sớm (`EarlyStopping`). | Vì đỉnh đạt ở Epoch 35 và huấn luyện kết thúc ở Epoch 50 (`50 - 35 = 15 < 20`), nên `patience=20` chưa kích hoạt dừng sớm. | **Giữ `20`** là hợp lý để tránh tốn thời gian CPU vô ích. |
| **`time`** | **`null`** (`dòng 6`) | `null` (`dòng 17`) | Giới hạn tổng thời gian huấn luyện tính bằng giờ (nếu đặt, sẽ ghi đè `epochs`). | Dùng khi thuê máy đám mây theo giờ cố định. | **Giữ `null`**. |
| **`save` / `save_period`** | **`true` / `-1`** (`dòng 10-11`) | `true` / `-1` (`dòng 21-22`) | Lưu `best.pt` và `last.pt`; `save_period = -1` nghĩa là không lưu thêm các tệp `epoch3.pt, epoch6.pt...` trung gian. | Đặt `save_period > 0` sẽ tốn thêm dung lượng ổ cứng (~6 MB mỗi tệp). | **Giữ nguyên `true` và `-1`**. |

#### Nhóm 4: Tăng cường dữ liệu (`Data Augmentation`)
| Tham số (`args.yaml`) | Giá trị tôi dùng (`args.yaml`) | Giá trị mặc định (`default.yaml`) | Ý nghĩa kỹ thuật | Tăng hoặc giảm thì ảnh hưởng gì? | Có nên đổi cho bài toán đầu người trong rạp không? |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`mosaic`** | **`1.0`** (`dòng 106`) | `1.0` (`dòng 127`) | Xác suất (`100%`) ghép 4 bức ảnh ngẫu nhiên thành 1 ảnh huấn luyện. | Giúp mô hình nhìn thấy đầu người ở nhiều vị trí và tỉ lệ thu nhỏ khác nhau trong cùng 1 ảnh, nhưng làm kích thước đầu vốn đã nhỏ lại càng nhỏ hơn. | **Giữ `1.0` ở đầu nhưng bắt buộc phải có `close_mosaic`**. |
| **`close_mosaic`** | **`10`** (`dòng 27`) | `10` (`dòng 35`) | Tắt ghép ảnh `Mosaic` ở **10 epochs cuối cùng** (Epoch 41..50), quay về học trên ảnh đơn nguyên bản (`trainer.py:496-499`). | Giúp mô hình làm quen lại với phân bố kích thước ảnh thật trước khi kết thúc huấn luyện. | **Giữ `10` hoặc tăng lên `15`** để mô hình tinh chỉnh kỹ hơn trên kích thước đầu thật. |
| **`fliplr`** | **`0.5`** (`dòng 104`) | `0.5` (`dòng 125`) | Xác suất (`50%`) lật ngang bức ảnh trái qua phải (`np.fliplr` tại `augment.py:1569`). | Tăng gấp đôi sự đa dạng góc nghiêng đầu trái/phải mà hoàn toàn giữ nguyên tính hợp lệ vật lý của rạp chiếu phim. | **NÊN BẬT (`0.5`)** — rất tốt cho bài toán nhận diện đầu người. |
| **`flipud`** | **`0.0`** (`dòng 103`) | `0.0` (`dòng 124`) | Xác suất (`0%`) lật ngược bức ảnh trên xuống dưới (`np.flipud` tại `augment.py:1567`). | Nếu bật `flipud > 0`, đầu người sẽ bị trồng cây chuối ngược xuống sàn rạp — điều không bao giờ xảy ra với camera cố định! | **TUYỆT ĐỐI GIỮ `0.0` (Không lật dọc)**. |
| **`hsv_h` / `hsv_s` / `hsv_v`** | **`0.015` / `0.7` / `0.4`** (`dòng 95-97`) | `0.015` / `0.7` / `0.4` (`dòng 116-118`) | Biến thiên ngẫu nhiên Màu sắc (Hue `1,5%`), Độ bão hòa (Saturation `70%`), và Độ sáng (Value `40%`). | Vì ảnh rạp là ảnh hồng ngoại xám (`R=G=B`, độ bão hòa `S=0`), `hsv_h` và `hsv_s` hầu như không đổi ảnh, còn **`hsv_v = 0.4` rất quan trọng** vì giúp mô hình chịu được cảnh đèn rạp sáng/tối thất thường. | **Giữ `hsv_v = 0.4`**; có thể đặt `hsv_h = 0.0, hsv_s = 0.0` vì ảnh hồng ngoại đơn sắc. |
| **`translate` / `scale`** | **`0.1` / `0.5`** (`dòng 99-100`) | `0.1` / `0.5` (`dòng 120-121`) | Dịch chuyển ảnh ngẫu nhiên `±10%` và phóng to/thu nhỏ ngẫu nhiên `±50%`. | Giúp mô hình không học vẹt tọa độ cố định `(x, y)` của từng chiếc ghế trong phòng 1. Note: thu nhỏ `-50%` có thể làm đầu ở hàng xa nhỏ dưới `5 px`. | **Nên giảm nhẹ `scale` từ `0.5` xuống `0.25–0.30`** để đầu người ở xa không bị thu nhỏ quá mức khi phóng/thu. |
| **`degrees` / `shear` / `perspective`** | **`0.0` / `0.0` / `0.0`** (`dòng 98, 101, 102`) | `0.0` / `0.0` / `0.0` (`dòng 119, 122, 123`) | Xoay nghiêng ảnh (`degrees`), kéo xiên (`shear`), biến đổi phối cảnh (`perspective`). | Xoay nhẹ `degrees = 5.0` có thể mô phỏng khách nghiêng đầu ngủ trên ghế. | Có thể giữ `0.0` hoặc thử `degrees = 5.0`. |
| **`mixup` / `cutmix` / `copy_paste` / `bgr`** | **`0.0`** (`dòng 105, 107-109`) | `0.0` (`dòng 126, 128-130`) | Trộn mờ 2 ảnh (`mixup`), cắt ghép vùng ảnh (`cutmix`), dán đè phân vùng (`copy_paste`). | Trộn mờ 2 ảnh hồng ngoại dễ tạo ra bóng ma giống đầu người giả. | **Giữ `0.0`**. |
| **`auto_augment` / `erasing`** | **`randaugment` / `0.4`** (`dòng 111-112`) | `randaugment` / `0.4` (`dòng 132-133`) | **Lưu ý từ `default.yaml:132-133`**: Hai tham số này ghi rõ `(classification only)` — chỉ áp dụng cho bài toán phân loại ảnh (`task=classify`), không chạy trong pipeline `detect`! | Không tác động tới bài toán `detect`. | Không ảnh hưởng. |

#### Nhóm 5: Trọng số Hàm mất mát (`Loss Gains`)
| Tham số (`args.yaml`) | Giá trị tôi dùng (`args.yaml`) | Giá trị mặc định (`default.yaml`) | Ý nghĩa kỹ thuật | Tăng hoặc giảm thì ảnh hưởng gì? | Có nên đổi cho bài toán đầu người trong rạp không? |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`box` / `cls` / `dfl`** | **`7.5` / `0.5` / `1.5`** (`dòng 83, 84, 86`) | `7.5` / `0.5` / `1.5` (`dòng 104, 105, 107`) | Trọng số nhân vào 3 thành phần lỗi `box_loss`, `cls_loss`, `dfl_loss` (`loss.py:457-459`). | Tăng `box` ép khung bao khít hơn; tăng `cls` ép điểm tự tin phân biệt đầu/nền gắt hơn. | **Giữ mặc định `7.5 / 0.5 / 1.5`**. |
| *(Các tham số tác vụ khác)* | `pose: 12.0, kobj: 1.0, rle: 1.0, angle: 1.0, overlap_mask: true, mask_ratio: 4, dropout: 0.0, distill_model: null, dis: 6.0` | Giống hệt `default.yaml` | Chỉ dùng khi huấn luyện ước lượng tư thế (`pose`), khung xoay (`obb`), phân vùng (`segment`), phân loại (`classify`), hoặc chưng cất (`distill`). | Không được gọi trong `v8DetectionLoss`. | Không ảnh hưởng. |

#### Nhóm 6: Đánh giá, Tái lập kết quả & Khác (`Val, Reproducibility & Misc`)
| Tham số (`args.yaml`) | Giá trị tôi dùng (`args.yaml`) | Giá trị mặc định (`default.yaml`) | Ý nghĩa kỹ thuật | Tăng hoặc giảm thì ảnh hưởng gì? | Có nên đổi cho bài toán đầu người trong rạp không? |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`seed` / `deterministic`** | **`42` / `true`** (`dòng 22-23`) | `0` / `true` (`dòng 30-31`) | Cố định hạt giống ngẫu nhiên của `random`, `numpy`, `torch` (`torch_utils.py:789-808`). | Giúp hai lần chạy huấn luyện cùng cấu hình trên cùng máy cho ra kết quả giống nhau (Reproducibility). | **Giữ `seed=42, deterministic=true`**. |
| **`amp`** | **`true`** (`dòng 29`) | `true` (`dòng 37`) | Tự động trộn độ chính xác `FP16/FP32` (Automatic Mixed Precision) trên GPU. Trên CPU, `autocast` không bật FP16 cho Conv thường nhưng không gây lỗi. | Tăng tốc và giảm một nửa VRAM khi chạy trên GPU NVIDIA. | Giữ mặc định. |
| **`val` / `split` / `iou` / `max_det`** | **`true` / `val` / `0.7` / `300`** (`dòng 39-44`) | `true` / `val` / `0.7` / `300` (`dòng 52-57`) | Chạy kiểm định trên tập `val` cuối mỗi epoch với NMS `iou=0.7`, tối đa `300` khung/ảnh. | Rất cần thiết vì phòng chiếu có thể có tới 135 ghế (`135 < max_det = 300`). | Khi chạy `predict` thực tế trong `main.py`, **nên truyền `iou=0.60`** để giảm đếm trùng 1 đầu thành 2 khung `[DỰ ÁN: Thí nghiệm D]`. |

---

### 3.4. Bộ tối ưu (`Optimizer`), Lịch giảm tốc độ học (`LR Scheduler`), `Warmup`, `ModelEMA` và Biểu đồ `lr` theo Epoch

1. **Khi đặt `optimizer: auto`, bộ tối ưu nào thực sự được chọn?**
   - Đọc trực tiếp hàm `BaseTrainer.build_optimizer` tại `ultralytics/engine/trainer.py:1124-1212` và dòng gọi tại `trainer.py:315-323` `[MÃ NGUỒN]`:
   ```text
   iterations = ceil( N_anh_train / max(batch_size, nbs) ) * epochs
   Nếu iterations > 10000:
       Chọn optimizer = "MuSGD", lr = 0.01, momentum = 0.9
   Ngược lại (iterations <= 10000):
       lr_fit = round( 0.002 * 5 / (4 + nc), 6 )
       Chọn optimizer = "AdamW", lr = lr_fit, momentum = 0.9
       Và đặt warmup_bias_lr = 0.0
   ```
   - **Thay số thật của dự án CineSight**:
     - `N_anh_train = 98`, `batch_size = 4`, `nbs = 64`, `epochs = 50`, `nc = 1`.
     - `iterations = ceil(98 / max(4, 64)) * 50 = ceil(98 / 64) * 50 = 2 * 50 = 100` (nhỏ hơn rất nhiều so với `10.000`).
     - `lr_fit = round(0.002 * 5 / (4 + 1), 6) = 0.002`.
     - Do đó, `ultralytics` tự động chọn **`AdamW(lr=0.002, betas=(0.9, 0.999))`** và chia các tham số của mô hình thành 3 nhóm (`param_groups`): `pg0` (`weight` của Conv, có phạt `weight_decay = 0.0005`), `pg1` (`weight` của BatchNorm, `weight_decay = 0.0`), và `pg2` (`bias`, `weight_decay = 0.0`) `[MÃ NGUỒN: trainer.py:1182-1185]`.

2. **Công thức lịch giảm tốc độ học (`Linear` vs `Cosine`) và `Warmup`**:
   - **Giai đoạn Khởi động (`Warmup` – 3 epochs đầu tiên, `ni < nw = 75` bước lô)** `[MÃ NGUỒN: ultralytics/engine/trainer.py:268-271, 509-526]`:
     - Ở mỗi bước lô `ni` từ `0` đến `75`, tốc độ học được nội suy tuyến tính từ `0.0` lên `lr0 * lf(epoch)`:
     ```text
     lr_warmup(ni) = (ni / nw) * (lr0 * lf(epoch))
     momentum_warmup(ni) = warmup_momentum + (ni / nw) * (momentum - warmup_momentum)
     ```
   - **Giai đoạn Giảm tốc độ học theo Epoch (`_setup_scheduler` tại `trainer.py:260-266` và `torch_utils.py:775-786`)** `[MÃ NGUỒN]`:
     - Vì dự án đặt `cos_lr: false` (`args.yaml:26`), mô hình dùng **lịch giảm tuyến tính (Linear LR)**:
     ```text
     # 1. Lịch giảm tuyến tính (cos_lr = False - trainer.py:265):
     lf_linear(epoch) = max(1.0 - epoch / epochs, 0.0) * (1.0 - lrf) + lrf
     lr(epoch)        = lr0 * lf_linear(epoch)

     # 2. Lịch giảm hình Cosin (nếu bật cos_lr = True - torch_utils.py:786):
     lf_cosine(epoch) = max((1.0 - cos(epoch * pi / epochs)) / 2.0, 0.0) * (lrf - 1.0) + 1.0
     ```
     - **Đọc bằng lời**: Sau khi kết thúc 3 epochs khởi động, tốc độ học `lr` giảm đều đặn một lượng cố định `lr0 * (1 - lrf) / epochs = 0.002 * 0.99 / 50 = 0.0000396` sau mỗi epoch, từ mức đỉnh `~0.001895` ở Epoch 3 xuống `0.0000596` ở Epoch 50 `[DỰ ÁN: results.csv:5-52]`.

3. **`ModelEMA` (Exponential Moving Average của trọng số) làm gì?**
   - **Vị trí trong mã nguồn**: Lớp `ModelEMA` tại `ultralytics/utils/torch_utils.py:824-900` (dẫn nguồn `https://github.com/rwightman/pytorch-image-models` và `https://www.tensorflow.org/api_docs/python/tf/train/ExponentialMovingAverage` tại dòng `839-840`), được khởi tạo ở `trainer.py:445` và cập nhật sau mỗi `optimizer_step` ở `trainer.py:895` `[MÃ NGUỒN]`.
   - **Công thức văn bản thuần**:
   ```text
   # Với mỗi lần cập nhật trọng số thứ u (updates = 1, 2, ...), hệ số giữ lại d(u) tăng dần về 0.9999 (tau = 2000):
   d(u)      = 0.9999 * (1.0 - exp(-u / 2000.0))
   W_ema_moi = d(u) * W_ema_cu + (1.0 - d(u)) * W_model_hien_tai
   ```
   - **Ý nghĩa & So sánh với Frontend**: Trong lúc huấn luyện, trọng số `W_model` của mạng chính có thể bị giật cục theo từng lô 4 ảnh. `ModelEMA` giữ một bản sao thứ hai của mô hình, cập nhật mượt mà theo trung bình trượt hàm mũ (giống như bộ lọc làm mượt cử chỉ kéo chuột hoặc `lerp` trong animation Flutter). **Toàn bộ việc chấm điểm trên tập `val` và tệp `best.pt` / `best_head_v2.pt` cuối cùng đều được trích xuất từ bản sao `EMA` này (`trainer.py:759, 783-784`)!**

4. **Đồ thị bằng chữ và bảng số liệu `lr/pg0` thực tế trong `results.csv` của dự án** `[DỰ ÁN: results.csv:3-52]`:

```text
lr/pg0 (Tốc độ học thực tế trong runs/detect/head_v2_official/results.csv)
0.00200 |          * (Epoch 3: đỉnh Warmup = 0.00189519)
0.00180 |             *  * (Epoch 5: 0.0018416)
0.00150 |                   *  * (Epoch 10: 0.0016436 -> Epoch 15: 0.0014456)
0.00120 |      *                  *  * (Epoch 20: 0.0012476 -> Epoch 25: 0.0010496)
0.00080 |                               *  * (Epoch 30: 0.0008516 -> Epoch 35 [BEST]: 0.0006536)
0.00040 |   *                                 *  * (Epoch 40: 0.0004556 -> Epoch 45: 0.0002576)
0.00006 +-------------------------------------------*--* (Epoch 50: 0.0000596)
        Epoch 1   3   5    10    15    20    25    30    35    40    45    50
```

---

### 3.5. Tăng cường dữ liệu (`Data Augmentation`) gắn với bài toán rạp phim và Mô tả lô huấn luyện thực tế (`train_batch*.jpg`)

1. **Phân tích các phép tăng cường dữ liệu trọng tâm cho bài toán đầu người trong rạp**:
   - **`Mosaic` (`mosaic = 1.0`, `ultralytics/data/augment.py`)**: Ghép 4 bức ảnh huấn luyện ngẫu nhiên vào 4 góc của một khung vải `1600x1600` rồi cắt lấy vùng `800x800` quanh tâm ngẫu nhiên.
     - *Tác dụng*: Trong phòng chiếu 1, khán giả ở video mẫu thường chỉ ngồi ở vài hàng ghế cố định. Nhờ ghép 4 ảnh lệch tâm, đầu người xuất hiện ở khắp mọi tọa độ `(x, y)` trên khung hình, buộc mô hình phải học hình dáng cái đầu thay vì học thuộc lòng vị trí chiếc ghế.
     - *Vì sao phải tắt ở 10 epochs cuối bằng `close_mosaic = 10` (`trainer.py:496-499`)?* Ảnh ghép Mosaic có đường cắt biên nhân tạo giữa 4 bức ảnh và làm nhiều cái đầu bị cắt cụt một nửa hoặc bị thu nhỏ khác với ảnh camera nguyên bản. Ở Epoch 41 (`50 - 10 + 1`), hàm `_close_dataloader_mosaic()` tắt Mosaic để 10 epochs cuối mô hình được tinh chỉnh trên ảnh camera nguyên vẹn 100%.
   - **Lật ngang (`fliplr = 0.5`) vs Lật dọc (`flipud = 0.0`)**:
     - Lật ngang (`fliplr = 0.5`) biến một khách ngồi ghế bên trái nghiêng đầu sang phải thành khách ngồi bên phải nghiêng đầu sang trái — hoàn toàn tự nhiên và nhân đôi lượng mẫu.
     - Lật dọc (`flipud = 0.0`) bị tắt vì camera gắn cố định trên trần/tường rạp không bao giờ quay cảnh khán giả lộn ngược đầu xuống đất.
   - **Biến thiên độ sáng (`hsv_v = 0.4`) và Co dãn (`scale = 0.5`)**:
     - `hsv_v = 0.4` tăng/giảm độ sáng ngẫu nhiên tới `±40%`, giúp mô hình nhận diện được cả lúc đèn trần bật sáng lẫn lúc tắt đèn chỉ còn ánh sáng hồng ngoại phản xạ từ màn chiếu.

2. **Kiểm chứng thực tế các tệp `train_batch*.jpg` của lần chạy chính thức (Lưu vào thư mục tạm `reports\yolo_study_tmp\` rồi xóa theo Quy tắc 7)** `[DỰ ÁN]`:
   - Trong kịch bản kiểm chứng, chúng ta đã chép 3 tệp `train_batch0.jpg`, `train_batch1.jpg` (thuộc Epoch 1 — đang bật Mosaic) và `train_batch1000.jpg` (thuộc Epoch 41 — thời điểm `close_mosaic = 10` vừa tắt Mosaic, vì `base_idx = (50 - 10) * 25 = 1000` tại `trainer.py:478`) vào `reports\yolo_study_tmp\` để đo thông số rồi xóa sạch:
     - `train_batch0.jpg` & `train_batch1.jpg`: Kích thước `1600x1600x3` (lưới 2x2 gồm 4 mẫu của 1 mini-batch `batch = 4`, mỗi mẫu `800x800`), độ sáng trung bình `mean_px = 114,47` và `97,93`. Mỗi ô `800x800` trong `train_batch0.jpg` là một bức ghép **Mosaic 4 mảnh** từ 4 khung hình rạp phim khác nhau, có các mảng viền đệm màu xám (`pixel = 114`) ở rìa và các khung nhãn màu xanh dương ghi `0` (`head`) bao quanh các đầu người ở nhiều kích cỡ khác nhau.
     - `train_batch1000.jpg` (bắt đầu Epoch 41 sau khi `close_mosaic` kích hoạt): Kích thước `1600x1600x3` (`mean_px = 93,55`). Lúc này mỗi ô `800x800` **không còn ghép 4 mảnh Mosaic nữa** mà chỉ chứa **1 khung hình phòng chiếu nguyên vẹn** (được co `LetterBox` kèm dải đệm xám phía trên/dưới và dịch chuyển nhẹ `translate`), giúp mô hình ổn định lại trước khi kết thúc.
     - *(Tuân thủ Quy tắc 3 & 7: Không nhúng ảnh có mặt khán giả vào tài liệu; bản sao trong `reports\yolo_study_tmp\` đã được xóa sạch)*.

---

### 3.6. Dừng sớm (`EarlyStopping`), Tiêu chí chọn `best.pt` (`fitness`) và Cơ chế `resume`

- **Dừng sớm (`EarlyStopping`)** `[MÃ NGUỒN: ultralytics/utils/torch_utils.py:1104-1153]`:
  - Sau mỗi epoch, bộ kiểm tra tính `delta = epoch - self.best_epoch` (`torch_utils.py:1141`). Nếu `delta >= self.patience` (với dự án là `patience = 20`), hàm trả về `stop = True` và dừng vòng lặp huấn luyện để tránh lãng phí tài nguyên và chống học vẹt. Trong lần chạy `head_v2_official`, kỷ lục tốt nhất đạt ở **Epoch 35**, nên đến Epoch 50 mới chỉ qua `delta = 50 - 35 = 15 < 20` epochs và mô hình chạy trọn vẹn 50 epochs `[DỰ ÁN: results.csv:37, 52]`.
- **Tiêu chí chọn `best.pt` (`Metric.fitness`) trong phiên bản `ultralytics 8.4.160`** `[MÃ NGUỒN: ultralytics/utils/metrics.py:1009-1012 & trainer.py:811-812]`:
  - Đọc trực tiếp dòng `1009-1012` của `ultralytics/utils/metrics.py`:
  ```python
  def fitness(self) -> float:
      """Return model fitness as a weighted combination of metrics."""
      w = [0.0, 0.0, 0.0, 1.0]  # weights for [P, R, mAP@0.5, mAP@0.5:0.95]
      return float((np.nan_to_num(np.array(self.mean_results())) * w).sum())
  ```
  - **Phát hiện quan trọng từ mã nguồn phiên bản `8.4.160`**: Khác với các phiên bản YOLOv5/YOLOv8 đời cũ (vốn dùng trọng số `[0.0, 0.0, 0.1, 0.9]` tức `10% mAP@0.5 + 90% mAP@0.5:0.95`), trong **`ultralytics 8.4.160`**, vector trọng số là **`w = [0.0, 0.0, 0.0, 1.0]`** — nghĩa là **`fitness` bằng đúng `100%` chỉ số `mAP@0.5:0.95`**!
  - Kiểm chứng trực tiếp từ tệp trọng số `models/best_head_v2.pt` `[DỰ ÁN: output đọc ckpt['train_metrics']]`:
    - `'metrics/mAP50(B)': 0.80983`, `'metrics/mAP50-95(B)': 0.3775`, và **`'fitness': 0.3775`** (bằng chính xác `mAP50-95(B)` của **Epoch 35** trong `results.csv:37`, dù Epoch 20 có `mAP50(B) = 0.81948` cao hơn nhưng `mAP50-95(B) = 0.36268` thấp hơn nên không được chọn làm `best.pt`).
- **Cơ chế `resume` (Tiếp tục huấn luyện khi bị ngắt giữa chừng)** `[MÃ NGUỒN: ultralytics/engine/trainer.py:1002-1056, 1097-1115]`:
  - Ở cuối mỗi epoch, tệp `last.pt` lưu đầy đủ `epoch`, `best_fitness`, bản sao `ema`, trạng thái bộ tối ưu `optimizer` (đã nén FP16) và `scaler` (`trainer.py:780-788`). Nếu máy sập nguồn ở Epoch 30, khi chạy lại với `resume=True` và `model=".../weights/last.pt"`, hàm `resume_training` nạp lại toàn bộ trạng thái này và chạy tiếp từ `start_epoch = 30 + 1 = 31` đến `50`. Còn khi kết thúc hoàn toàn quá trình huấn luyện (`final_eval` tại `trainer.py:983-992`), hàm `strip_optimizer` (`torch_utils.py:902-967`) xóa bỏ `optimizer`, `ema`, đặt `epoch = -1` và chuyển mô hình sang `FP16` (`half()`) để giảm dung lượng tệp `best.pt` xuống còn `~6,2 MB`.

---

### 3.7. Vì sao Dữ liệu và Nhãn quan trọng hơn Mô hình? (Áp vào số liệu thật từ `manifest.csv` và `dataset_stats`)
Trong học máy ứng dụng (Data-Centric AI), một mô hình nhỏ như `YOLOv8n` được huấn luyện trên dữ liệu gán nhãn chuẩn xác luôn vượt xa một mô hình khổng lồ huấn luyện trên dữ liệu sai nhãn hoặc lệch miền `[KIẾN THỨC CHUNG – chưa kiểm chứng trong lượt này]`. Đối chiếu trực tiếp với số liệu thật của dự án CineSight `[DỰ ÁN: datasets/head_v2/manifest.csv & Thống kê 825 nhãn Mục 5.3]`:
1. **Quy mô tập dữ liệu rất nhỏ và thưa người**:
   - Toàn bộ bộ dữ liệu chỉ có **163 ảnh** (`98 train`, `22 val`, `43 test`) với tổng cộng **825 khung đầu**.
   - Số lượng đầu trên mỗi ảnh chỉ dao động từ **`0` đến tối đa `6` đầu/ảnh** (trung bình toàn bộ dữ liệu là `5,06 đầu/ảnh`; trung vị `6,0 đầu/ảnh`) `[DỰ ÁN: Mục 5.3]`. Không có bất kỳ bức ảnh nào có 20, 50 hay 100 khán giả ngồi kín phòng chiếu 135 ghế!
2. **Tỉ lệ nhãn vẽ tay vs nhãn do mô hình nháp sinh ra (`Pre-label / Confirmation Bias`)**:
   - Theo đối chiếu giữa `stage_a_list.txt` (40 ảnh), `labels_prelabel/` (123 ảnh do `baseline_stage_a.pt` gán nháp ở `conf=0.20`) và `labels/` chính thức trong `TRAINING_WALKTHROUGH.md Phần 2.d`:
     - **40 ảnh (`24,5%`)**: Gán nhãn tay 100% từ đầu (`32 train + 8 val`).
     - **73 ảnh (`44,8%`)**: Do `baseline_stage_a.pt` gán nháp rồi người dùng mở `tools/label_heads_cv.py` chỉnh sửa/vẽ bù thêm `+99` cái đầu bị mô hình nháp bỏ sót.
     - **50 ảnh (`30,7%` — gồm `38 train, 3 val, 9 test`)**: Người dùng bấm duyệt giữ nguyên 100% tọa độ khung gợi ý của `baseline_stage_a.pt`.
   - **Hệ quả kỹ thuật**: Khi `30,7%` số ảnh giữ nguyên khung của mô hình nháp, mô hình chính thức `best_head_v2.pt` sẽ học lại chính thói quen đặt biên khung của `baseline_stage_a.pt`, và khi chấm điểm trên 9 ảnh `test` giữ nguyên nhãn nháp, điểm `IoU` sẽ cao giả tạo (thiên kiến xác nhận — confirmation bias).

---

### 3.8. Chia tập (`Train / Val / Test`) và Rò rỉ dữ liệu theo thời gian (`Temporal Data Leakage`) trên Video của dự án
- **Nguyên tắc chuẩn khi chia dữ liệu từ Video**: Các khung hình trích ra từ cùng một đoạn video cách nhau vài giây có bối cảnh ánh sáng, vị trí ngồi, quần áo và tư thế đầu của khán giả gần như y hệt nhau. Do đó, chuẩn mực bắt buộc là phải **chia theo phiên quay độc lập (Session-level / Video-level split)** — tức video của suất chiếu ngày hôm nay dùng làm `train`, còn video của suất chiếu ngày hôm sau (với những khán giả khác) dùng làm `val` và `test` `[KIẾN THỨC CHUNG – chưa kiểm chứng trong lượt này]`.
- **Thực trạng trong dự án CineSight (Đo bằng số thật từ `datasets/head_v2/manifest.csv`)** `[DỰ ÁN: TRAINING_WALKTHROUGH.md Phần 2.c]`:
  - Cả 3 tập `train`, `val`, `test` đều được cắt ra từ **cùng 1 tệp video duy nhất `cam_edited.mp4`** (`577,9 giây`), chỉ chia theo 4 khúc thời gian nối tiếp nhau:
    - **`train` (98 ảnh)**: Gồm 2 đoạn `[4,0s -> 150,0s]` (40 ảnh) và `[155,5s -> 343,5s]` (58 ảnh).
    - **`val` (22 ảnh)**: Đoạn `[346,0s -> 419,5s]` (22 ảnh).
    - **`test` (43 ảnh)**: Đoạn `[425,0s -> 576,0s]` (43 ảnh).
  - **Khoảng cách thời gian nhỏ nhất giữa các tập**:
    - Giữa khung `train` cuối cùng (`room1_cam_edited_0344s.jpg` ở `343,5s`) và khung `val` đầu tiên (`room1_cam_edited_0346s.jpg` ở `346,0s`): **`346,0 - 343,5 = 2,5 giây`**!
    - Giữa khung `val` cuối cùng (`419,5s`) và khung `test` đầu tiên (`425,0s`): **`425,0 - 419,5 = 5,5 giây`**!
    - Giữa khung `train` cuối cùng (`343,5s`) và khung `test` đầu tiên (`425,0s`): **`81,5 giây`** (nhưng vẫn là cùng nhóm 6 người đó ngồi trên cùng những chiếc ghế đó trong cùng 1 phòng chiếu!).
  - **Đánh giá mức độ rủi ro**: **RỦI RO RẤT CAO (High Leakage Risk)**. Chỉ số `mAP@0.5 = 0,80983` trên tập `val` chỉ chứng minh mô hình nhận diện tốt nhóm 6 khán giả này trong phòng chiếu số 1 ở các giây tiếp theo của cùng video, chứ **chưa chứng minh được độ chính xác khi sang suất chiếu mới hoặc phòng chiếu mới**.

---

### 3.9. Các hướng cải thiện thực tế cho bài toán CineSight (Kèm chi phí thực hiện)
| Thứ tự ưu tiên | Hướng cải thiện thực tế | Cơ chế kỹ thuật | Chi phí thực hiện (Thời gian / Phần cứng) |
| :---: | :--- | :--- | :--- |
| **1** | **Truyền rõ `iou=0.60` vào `main.py:92`** | Khử hiện tượng NMS ở `iou=0.70` giữ lại 2 khung chồng nhau (`IoU ∈ [0.60, 0.70]`) trên cùng 1 cái đầu (giảm `MAE` trên tập `test` từ `0,65` xuống `0,44`) `[DỰ ÁN: Thí nghiệm D]`. | **0 phút huấn luyện** (chỉ sửa 1 tham số trong `main.py`, không tốn thêm CPU). |
| **2** | **Thu thập thêm 200–300 ảnh từ suất chiếu đông khách (30–100 người) & phòng khác** | Khắc phục triệt để giới hạn tối đa 6 người/ảnh và hiện tượng rò rỉ dữ liệu 1 video; giúp mô hình học được cảnh che khuất thực tế giữa các hàng ghế. | **4–6 giờ gán nhãn** (dùng `best_head_v2.pt` gán nháp rồi sửa tay) + **3–4 giờ train CPU**. |
| **3** | **Tăng `imgsz` lên `960` khi suy luận (hoặc khi huấn luyện trên GPU)** | Nâng chiều cao đầu người ở hàng ghế xa từ `10,0 px` (ở `imgsz=800`) lên `12,0 px` (ở `imgsz=960`), vượt xa bước nhảy `stride = 8 px` `[DỰ ÁN: Thí nghiệm B]`. | Thời gian suy luận CPU tăng từ `~193,5 ms` lên `~282,6 ms/ảnh` (hoàn toàn chấp nhận được nếu camera chụp định kỳ 5–10 giây/lần). |
| **4** | **Cắt ảnh thành ô nhỏ khi suy luận (Tiled Inference / SAHI-style cropping)** | Cắt bức ảnh gốc `1920x1080` thành 2 hoặc 4 khung nhỏ có chồng lấp biên (ví dụ 2 nửa `1024x1080`) rồi đưa từng mảnh vào `model.predict(imgsz=640)` và gộp khung bằng `TorchNMS.nms`. Giúp giữ nguyên độ phân giải gốc của các đầu nhỏ ở hàng ghế cuối mà không cần thư viện ngoài `[MÃ NGUỒN: ultralytics/utils/nms.py:245]`. | Tốn gấp **2–4 lần thời gian suy luận CPU** (`~300–600 ms/lần kiểm tra`). |
| **5** | **Tiền xử lý tăng tương phản cục bộ `CLAHE` (`cv2.createCLAHE`)** | Cân bằng biểu đồ sáng cục bộ trên ảnh hồng ngoại trước khi đưa vào YOLO để làm nổi bật viền tóc đen trên nền ghế tối khi cảnh phim quá tối `[DỰ ÁN: Thí nghiệm C]`. | Chỉ tốn **`~2–3 ms` CPU** với OpenCV, nhưng cần bật đồng bộ cả lúc train lẫn lúc predict. |
| **6** | **Nâng cấp lên mô hình `YOLOv8s` (`small`)** | Tăng `width_multiple` từ `0.25` lên `0.50` (`11.166.560 tham số`, `28,8 GFLOPs` ở `imgsz=640` theo `yolov8.yaml:12`) để tăng dung lượng biểu diễn đặc trưng. | Tốn gấp **~3,5 lần thời gian tính toán** (trên CPU hiện tại sẽ mất ~6–7 giờ để train 50 epochs; chỉ nên làm khi có GPU hoặc Google Colab). |

---

## PHẦN 4: CÁC CÔNG CỤ CÓ SẴN TRONG ULTRALYTICS HỖ TRỢ HUẤN LUYỆN
*(Trả lời Yêu cầu (4) của giảng viên: Các công cụ có sẵn trong YOLO hỗ trợ quá trình huấn luyện)*

Mỗi công cụ dưới đây đều được kiểm tra trực tiếp trong gói `ultralytics 8.4.160` đã cài tại `ai_service\venv\Lib\site-packages\ultralytics\` [MÃ NGUỒN] và đối chiếu với trạng thái thực của dự án CineSight [DỰ ÁN].

### 4.1. CLI `yolo` và các chế độ (modes) & tác vụ (tasks)
- **(a) Nó làm gì**: Cung cấp giao diện dòng lệnh `yolo <TASK> <MODE> args...` hoặc API Python `YOLO(model).<mode>(...)` thống nhất cho mọi bước từ kiểm tra dữ liệu, huấn luyện, đánh giá, suy luận, theo vết đến xuất mô hình [`ultralytics/cfg/__init__.py:59-60, 100-150`] [MÃ NGUỒN].
- **(b) Lệnh/hàm cụ thể trong gói đã cài**:
  - **6 chế độ (`MODES`)**: `("train", "val", "predict", "export", "track", "benchmark")` [`ultralytics/cfg/__init__.py:59`] [MÃ NGUỒN].
  - **7 tác vụ (`TASKS`)**: `("detect", "segment", "semantic", "depth", "classify", "pose", "obb")` [`ultralytics/cfg/__init__.py:60`] [MÃ NGUỒN].
  - **Các lệnh phụ đặc biệt (`special`)**: `help`, `checks`, `version`, `settings`, `cfg`, `copy-cfg`, `solutions` (`count`, `crop`, `blur`, `workout`, `heatmap`, `isegment`, `visioneye`, `speed`, `queue`, `analytics`, `inference`, `trackzone`, `region`, `security`, `parking`) [`ultralytics/cfg/__init__.py:110-145`] [MÃ NGUỒN].
- **(c) Đã dùng trong dự án chưa**: Dự án gọi qua Python API `model.train(...)` trong `tools/train_head_v2.py:67` (`mode="train"`) và `model(frame, ...)` trong `main.py:217` (`mode="predict"`), cùng `model.val(...)` khi đánh giá [DỰ ÁN].

### 4.2. Kiểm tra dữ liệu tự động & tạo `.cache` (`check_det_dataset`, `verify_image_label`)
- **(a) Nó làm gì**: Trước khi chạy Epoch 1, Ultralytics tự động đọc tệp YAML (`datasets/head_v2/head_v2.yaml`), kiểm tra đường dẫn thư mục `train`/`val`/`test`, quét từng cặp ảnh `.jpg` và nhãn `.txt` để phát hiện ảnh hỏng, nhãn ngoài miền `[0, 1]`, nhãn thiếu cột hoặc trùng lặp, rồi lưu kết quả vào tệp nhị phân `.cache` để các lần chạy sau không phải đọc đĩa lại [`ultralytics/data/utils.py`, `ultralytics/data/dataset.py:150-240`, `ultralytics/engine/trainer.py:837`] [MÃ NGUỒN].
- **(b) Lệnh/hàm cụ thể**: `check_det_dataset(data)` trong `ultralytics/data/utils.py` và `YOLODataset.cache_labels()` trong `ultralytics/data/dataset.py` [MÃ NGUỒN].
- **(c) Đã dùng trong dự án chưa**: **ĐÃ DÙNG TỰ ĐỘNG** khi chạy `train_head_v2.py`. Hai tệp cache thật đang nằm trên đĩa là `c:\CineSightApp\ai_service\datasets\head_v2\labels\train.cache` và `val.cache` [DỰ ÁN]. Ngoài ra dự án có thêm kịch bản kiểm tra riêng `tools/qc_labels.py` và `tools/dataset_stats.py` [DỰ ÁN].

### 4.3. Bảng kết quả theo từng epoch (`results.csv`) và đồ thị quá trình học (`results.png`)
- **(a) Nó làm gì**:
  - Cuối mỗi epoch, `BaseTrainer.save_metrics()` ghi nối (append) 1 dòng gồm 15 cột (`epoch`, `time`, 3 cột `train/*_loss`, 4 cột `metrics/*(B)`, 3 cột `val/*_loss`, 3 cột `lr/pg0..2`) vào `results.csv` [`ultralytics/engine/trainer.py:920-955`] [MÃ NGUỒN].
  - Kết thúc huấn luyện, `plot_results(file=self.csv)` vẽ lưới 2x5 (10 biểu đồ con) gồm đường thực tế và đường làm mượt (smooth) của 3 hàm lỗ huấn luyện, 3 hàm lỗ kiểm định, Precision, Recall, mAP50, mAP50-95 ra tệp `results.png` [`ultralytics/utils/plotting.py`, gọi tại `trainer.py:976`] [MÃ NGUỒN].
- **(b) Đã dùng trong dự án chưa**: **ĐÃ CÓ** tại `runs/detect/head_v2_official/results.csv` (`50` dòng, `5,579 bytes`) và `runs/detect/head_v2_official/results.png` (`272,775 bytes`) [DỰ ÁN].
- **(d) Cách đọc `results.png` (xem mục 3.8)**: Nhìn hàng trên (`train/*_loss` giảm đều) so với hàng dưới (`val/*_loss` chạm đáy ở epoch 34–38 rồi đi ngang; `mAP50-95` đạt đỉnh `0.3775` ở epoch 35) để biết mô hình hội tụ quanh epoch 35 [DỰ ÁN].

### 4.4. Ảnh kiểm tra lô dữ liệu huấn luyện & kiểm định (`labels.jpg`, `train_batch*.jpg`, `val_batch*.jpg`)
- **(a) Nó làm gì**:
  - `labels.jpg` (`142,882 bytes`): Vẽ bởi `plot_labels()` ở đầu quá trình huấn luyện [`trainer.py:450`] [MÃ NGUỒN], gồm 4 ô: (1) biểu đồ cột số lượng mẫu mỗi lớp (`570 head`), (2) toàn bộ 570 khung chồng lên nhau tại tâm, (3) biểu đồ phân tán tọa độ tâm `(x, y)` trong miền `[0, 1]`, và (4) biểu đồ phân tán kích thước `(width, height)` — trong dự án ta, đám điểm `(width, height)` tụ đặc ở góc trái dưới (`w ~ 0.018`, `h ~ 0.033`), chứng minh trực quan 100% đối tượng là vật thể rất nhỏ [DỰ ÁN].
  - `train_batch0.jpg`, `train_batch1.jpg`, `train_batch2.jpg` (lưu ở Epoch 1, kích thước `1600x1600x3` [`trainer.py:729-733`]) [MÃ NGUỒN] [DỰ ÁN]: Cho thấy lô huấn luyện thực tế **khi đang bật Mosaic (`mosaic=1.0`)** — mỗi ô trong lưới là 4 khung hình rạp chiếu phim ghép 2x2 kèm nhãn trắng `0` (`head`), có lật ngang và biến đổi độ sáng [DỰ ÁN].
  - `train_batch1000.jpg`, `train_batch1001.jpg`, `train_batch1002.jpg` (lưu ở Epoch 41 = `50 - close_mosaic(10) + 1`, kích thước `1600x960x3` [`trainer.py:477-479`]) [MÃ NGUỒN] [DỰ ÁN]: Cho thấy lô huấn luyện **sau khi tắt Mosaic** — mỗi ô là 1 khung hình rạp nguyên vẹn tỉ lệ 16:9 (có viền xám LetterBox trên/dưới `800x480`) để mô hình làm quen với bố cục thật ở 10 epoch cuối [DỰ ÁN].
  - `val_batch0_labels.jpg`, `val_batch0_pred.jpg` ... `val_batch2_pred.jpg`: Đặt cạnh nhau nhãn thật (`_labels`) và khung mô hình đoán (`_pred`) trên tập `val` để mắt người đối chiếu trực tiếp những ghế nào bị bỏ sót hoặc đoán nhầm [MÃ NGUỒN] [DỰ ÁN]. *(Lưu ý quy tắc bảo mật: các tệp ảnh này có mặt khán giả nên báo cáo chỉ nêu tên tệp và kích thước, không chèn ảnh).*

### 4.5. Bộ biểu đồ đánh giá (`confusion_matrix*.png`, `BoxPR_curve.png`, `BoxF1_curve.png`, `BoxP_curve.png`, `BoxR_curve.png`)
- **(a) Nó làm gì & cách đọc từng biểu đồ**:
  - `confusion_matrix.png` (`94,167 bytes`) & `confusion_matrix_normalized.png` (`97,507 bytes`) [`ultralytics/utils/metrics.py:514-613`] [MÃ NGUỒN] [DỰ ÁN]: Ma trận 2x2 giữa Thực tế (trục dọc / cột tùy phiên bản hiển thị: `head`, `background`) và Dự đoán (`head`, `background`), tính ở ngưỡng mặc định `conf=0.25, iou=0.45` của `ConfusionMatrix.process_batch` [`val.py:216`] [MÃ NGUỒN]. Ô `(head, head)` là số đầu đoán đúng (TP), ô `(background, head)` là số lần báo giả trên ghế trống (FP), và ô `(head, background)` là số đầu người thật bị bỏ sót (FN) [MÃ NGUỒN].
  - `BoxPR_curve.png` (`86,938 bytes`) [`metrics.py:670-715`] [MÃ NGUỒN] [DỰ ÁN]: Đường cong Precision (trục tung) theo Recall (trục hoành) tại `IoU=0.50`. Diện tích dưới đường cong này chính là `mAP@0.5 = 0.810` ghi trong chú thích góc phải trên của biểu đồ [DỰ ÁN].
  - `BoxF1_curve.png` (`90,990 bytes`), `BoxP_curve.png` (`86,784 bytes`), `BoxR_curve.png` (`90,518 bytes`) [`metrics.py:718-760, 880-883`] [MÃ NGUỒN] [DỰ ÁN]: Vẽ F1, Precision, và Recall (trục tung) khi quét ngưỡng `conf` từ `0.0` đến `1.0` (trục hoành, 1000 điểm). Ultralytics tìm đỉnh của đường F1 làm mượt `smooth(f1_curve, 0.1).argmax()` để gợi ý ngưỡng `conf` tối ưu cho F1 [MÃ NGUỒN].

### 4.6. Đánh giá độc lập bằng `model.val()`
- **(a) Nó làm gì**: Chạy lại toàn bộ quy trình kiểm định (`DetectionValidator`) trên tập `val` hoặc `test` ở bất kỳ thời điểm nào sau huấn luyện, tự động gộp lớp `Conv + BatchNorm` (`fuse()`) để tăng tốc suy luận [MÃ NGUỒN].
- **(b) Chạy thực nghiệm `model.val()` trên mô hình của dự án và dán output nguyên văn**:
  - Lưu kết quả tạm vào `reports/yolo_study_tmp/val_check` rồi xóa ngay sau khi đọc xong theo Quy tắc 7 [DỰ ÁN]:
  ```python
  import shutil
  from pathlib import Path
  from ultralytics import YOLO

  tmp_dir = Path(r"c:\CineSightApp\ai_service\reports\yolo_study_tmp")
  model = YOLO(r"c:\CineSightApp\ai_service\best_head_v2.pt")
  metrics = model.val(
      data=r"c:\CineSightApp\ai_service\datasets\head_v2\head_v2.yaml",
      split="val",
      imgsz=800,
      batch=4,
      project=str(tmp_dir),
      name="val_check",
      verbose=False,
  )
  print("results_dict:", {k: round(float(v), 5) for k, v in metrics.results_dict.items()})
  print("speed (ms/img):", {k: round(float(v), 2) for k, v in metrics.speed.items()})
  shutil.rmtree(tmp_dir, ignore_errors=True)
  print("tmp_dir_deleted:", not tmp_dir.exists())
  ```
  Output nguyên văn [DỰ ÁN]:
  ```text
  Ultralytics 8.4.160 Python-3.14.3 torch-2.14.0+cpu CPU (11th Gen Intel Core i5-1135G7 @ 2.40GHz)
  Model summary (fused): 72 layers, 3,005,843 parameters, 0 gradients, 8.1 GFLOPs
  val: Fast image access (ping: 0.0±0.0 ms, read: 547.8±163.9 MB/s, size: 199.1 KB)
  val: Scanning C:\CineSightApp\ai_service\datasets\head_v2\labels\val.cache... 22 images, 7 backgrounds, 0 corrupt: 100% ━━━━━━━━━━━━ 22/22 0.0s
                   Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 1.4s
                     all         22         87      0.902      0.759       0.81      0.378
  Speed: 5.0ms preprocess, 351.9ms inference, 0.0ms loss, 11.7ms postprocess per image
  results_dict: {'metrics/precision(B)': 0.90194, 'metrics/recall(B)': 0.75862, 'metrics/mAP50(B)': 0.80974, 'metrics/mAP50-95(B)': 0.3775, 'fitness': 0.3775}
  speed (ms/img): {'preprocess': 5.03, 'inference': 351.88, 'loss': 0.0, 'postprocess': 11.65}
  tmp_dir_deleted: True
  ```
  - **Đối chiếu với `results.csv` Epoch 35**:
    - Trong `results.csv` Epoch 35: `P = 0.90226`, `R = 0.75862`, `mAP50 = 0.80983`, `mAP50-95 = 0.3775` [DỰ ÁN].
    - Khi chạy `model.val()` độc lập: `P = 0.90194`, `R = 0.75862`, `mAP50 = 0.80974`, `mAP50-95 = 0.3775` [DỰ ÁN].
    - Chênh lệch `0.00009` ở `mAP50` và `0.00032` ở `P` là do `best_head_v2.pt` lưu trọng số ở định dạng `FP16` (`half()`) và khi gọi `model.val()` độc lập, mô hình được `fuse()` (gộp Conv+BN thành 72 lớp, `3,005,843` tham số) và tính ở `FP32` với `batch=4` thay vì `batch=8` trong lúc train [MÃ NGUỒN] [DỰ ÁN].

### 4.7. Tinh chỉnh siêu tham số tự động (`model.tune()` / `Tuner`)
- **(a) Nó làm gì**: Lớp `Tuner` trong `ultralytics/engine/tuner.py:32-145` chạy thuật toán tiến hóa di truyền (genetic mutation): ở mỗi vòng lặp (`iteration`), nó lấy bộ siêu tham số có `fitness` cao nhất trước đó, đột biến ngẫu nhiên 26 siêu tham số trong từ điển `space` (`lr0`, `lrf`, `momentum`, `weight_decay`, `warmup_epochs`, `box`, `cls`, `dfl`, `hsv_*`, `mosaic`, `mixup`...) với xác suất `sigma=0.2`, huấn luyện lại từ đầu và lưu đồ thị phân tán `tune_scatter_plots.png` cùng `best_hyperparameters.yaml` [MÃ NGUỒN].
- **(b) Vì sao KHÔNG khả thi trên máy CPU hiện tại của dự án**:
  - 1 lần huấn luyện 50 epoch trên CPU `i5-1135G7` mất `7,477.4 giây` (~2.08 giờ) [DỰ ÁN].
  - Ngay cả khi chạy `model.tune(iterations=10, epochs=30)`, tổng thời gian sẽ là `10 * 30 * 149.5s = 44,850 giây (~12.5 giờ)` chạy liên tục 100% CPU; còn nếu chạy `iterations=300` như ví dụ trong docstring [`tuner.py:72`] thì mất **~375 giờ (~15.6 ngày)** [MÃ NGUỒN] [DỰ ÁN]. Vì vậy dự án không dùng `model.tune()` mà đặt trực tiếp `imgsz=800, close_mosaic=10` trong `train_head_v2.py` [DỰ ÁN].

### 4.8. Cài đặt toàn cục (`yolo settings`) & Cảnh báo bảo mật/quyền riêng tư với dữ liệu rạp chiếu phim
- **(a) Trạng thái `SETTINGS` thật trên máy hiện tại** (đọc bằng Python không chỉnh sửa theo Quy tắc 8) [`ultralytics/utils/__init__.py:1140-1260`] [MÃ NGUỒN] [DỰ ÁN]:
  ```text
  settings_version: 0.0.6
  datasets_dir: C:\CineSightApp\ai_service\datasets
  weights_dir: weights
  runs_dir: runs
  uuid: 99902799a7dcb5419901379530fd0fbd83fa018229ce4645b924ed9ddeea792d
  sync: True
  api_key: ''
  openai_api_key: ''
  clearml: True
  comet: True
  dvc: True
  hub: True
  mlflow: True
  neptune: True
  raytune: True
  tensorboard: False
  wandb: False
  vscode_msg: True
  openvino_msg: True
  ```
- **(b) Ý nghĩa bảo mật đối với video camera rạp chiếu phim (dữ liệu nhạy cảm)**:
  1. **Đồng bộ phân tích ẩn danh (`sync: True`)**: Trong `ultralytics/utils/events.py:49-238`, lớp `Events` gửi gói JSON qua HTTPS POST tới Google Analytics (`https://www.google-analytics.com/mp/collect?measurement_id=G-X8NCJYTQXM...`) tối đa mỗi 30 giây khi gọi CLI/train/val/predict/export [MÃ NGUỒN]. Dữ liệu gửi đi gồm: `uuid` máy, phiên bản `python`/`torch`/`ultralytics`, tên CPU, tên tác vụ (`detect`), tên tệp mô hình (`best_head_v2.pt`), tên gốc bộ dữ liệu (`head_v2`), `imgsz`, `epochs`, `batch`, `hours`, `fitness`, `speed_ms` [`events.py:69-198`] [MÃ NGUỒN]. Dù `sync` **không gửi ảnh hay đường dẫn đầy đủ**, nó vẫn gửi siêu dữ liệu hoạt động huấn luyện ra ngoài nếu máy có mạng [MÃ NGUỒN].
  2. **Các dịch vụ log đám mây (`clearml: True`, `comet: True`, `dvc: True`, `hub: True`, `mlflow: True`, `neptune: True`)**: Trong `ultralytics/utils/callbacks/` (`clearml.py`, `comet.py`, `wb.py`, `platform.py`), nếu thư viện Python tương ứng được cài trong `venv` hoặc `api_key` được cấu hình, callback sẽ **tự động tải lên các tệp `train_batch*.jpg` và `val_batch*.jpg` (chứa ảnh khuôn mặt khán giả chưa làm mờ)** lên máy chủ đám mây bên thứ ba [MÃ NGUỒN]. Hiện tại trong `ai_service\venv`, các gói `clearml`, `comet_ml`, `wandb`, `mlflow`, `neptune` **chưa được cài** và `api_key: ''` đang rỗng nên chưa có ảnh nào bị tải lên [DỰ ÁN]. Tuy nhiên, bạn nên biết để tắt (`yolo settings sync=False clearml=False comet=False hub=False`) nếu muốn khóa chặt hoàn toàn trước khi cài thêm gói mới.

### 4.9. Xuất mô hình (`model.export()`) sang các định dạng tăng tốc CPU/Edge
- **(a) Nó làm gì**: Chuyển tệp trọng số PyTorch `.pt` sang 20 định dạng suy luận khác nhau định nghĩa trong `export_formats()` [`ultralytics/engine/exporter.py:148-174`] [MÃ NGUỒN]: `torchscript`, `onnx`, `openvino`, `engine` (TensorRT), `coreml`, `saved_model`, `pb`, `tflite`, `edgetpu`, `tfjs`, `paddle`, `mnn`, `ncnn`, `imx`, `rknn`, `executorch`, `axelera`, `deepx`, `qnn`, `litert`, `hailo` [MÃ NGUỒN].
- **(b) Định dạng nào chạy được ngay trong `ai_service\venv` hiện tại?**:
  - Kiểm tra thực tế bằng `importlib.util.find_spec` (xem Phụ lục A.4) [DỰ ÁN]:
    - `torch`: `2.14.0+cpu` (**ĐÃ CÀI**) -> Xuất được ngay sang **TorchScript (`.torchscript`)** mà không cần cài thêm gói nào [MÃ NGUỒN] [DỰ ÁN].
    - `onnx`, `onnxruntime`, `onnxslim`, `openvino`, `tensorrt`, `coremltools`, `tflite_runtime`: **CHƯA CÀI (`NOT INSTALLED`)** trong `ai_service\venv` [DỰ ÁN].
  - Do đó, để tăng tốc suy luận trên CPU Intel `i5-1135G7` của máy này (hiện mất ~150 ms ở `imgsz=640` hoặc ~194 ms ở `imgsz=800`), hướng khả thi nhất là cài thêm `onnx` + `onnxruntime` hoặc `openvino` vào `venv` rồi chạy `model.export(format="openvino")` [MÃ NGUỒN] [DỰ ÁN].

### 4.10. Công cụ hỗ trợ dữ liệu (`auto_annotate`) & Theo vết đối tượng qua video (`model.track()`)
- **(a) `auto_annotate` (`ultralytics/data/annotator.py:10-67`)**:
  - Hàm `auto_annotate(data, det_model="yolo26x.pt", sam_model="sam_b.pt")` dùng một mô hình YOLO phát hiện khung chữ nhật rồi đưa khung đó làm prompt cho mô hình Segment Anything (`SAM`) để sinh nhãn đa giác phân vùng (segmentation polygon) [MÃ NGUỒN].
  - **Vì sao dự án CineSight KHÔNG dùng `auto_annotate`**: (1) Dự án cần nhãn khung chữ nhật (`detect`) cho đầu người chứ không phải nhãn đa giác phân vùng (`segment`); (2) `yolo26x.pt` / `yolov8n.pt` gốc trên COCO chỉ có lớp `person` (toàn thân), không có lớp `head`; (3) `sam_b.pt` nặng hàng trăm MB cần tải thêm từ mạng. Thay vào đó, dự án tự viết `tools/prelabel_v2.py` dùng mô hình `best_head_v1.pt` (Giai đoạn A) để gán nhãn nháp rồi người dùng duyệt lại bằng công cụ web cục bộ `tools/annotator.py` [DỰ ÁN].
- **(b) Theo vết đa đối tượng `model.track()` (`ultralytics/trackers/`, `cfg/default.yaml:139`)**:
  - Hỗ trợ 6 bộ theo vết: `botsort.yaml` (mặc định [`default.yaml:139`]), `bytetrack.yaml`, `ocsort.yaml`, `deepocsort.yaml`, `fasttrack.yaml`, `tracktrack.yaml` [`cfg/__init__.py:72`] [MÃ NGUỒN].
  - Thay vì xử lý từng khung hình rời rạc như `model(frame)` trong `main.py:217`, `model.track(frame, persist=True)` dùng bộ lọc Kalman (dự đoán quỹ đạo di chuyển của đầu người giữa khung `t-1` và khung `t`) kết hợp ghép cặp Hungarian bằng IoU để gắn cho mỗi cái đầu một mã số cố định `track_id` xuyên suốt video [MÃ NGUỒN]. Điều này giúp lọc bỏ hiện tượng khung nhấp nháy ở 1–2 frame lẻ tẻ.

---

## PHẦN 5: GIỚI HẠN CỦA YOLO – TỔNG QUÁT VÀ TRONG DỰ ÁN CINESIGHT
*(Trả lời Yêu cầu (1) của giảng viên: Giới hạn của YOLO)*

Để trình bày thuyết phục trước giảng viên, ta tách rõ 4 tầng giới hạn: **(5.1) Giới hạn kiến trúc của dòng YOLO nói chung**, **(5.2) Giới hạn riêng của bản `YOLOv8n` (nano)**, **(5.3) Giới hạn thực tế phát sinh trong bài toán camera rạp chiếu phim CineSight**, và **(5.4) Giới hạn pháp lý / giấy phép phần mềm**.

### 5.1. Giới hạn của họ mô hình YOLO nói chung (Architecture-level Limits)
1. **Độ phân giải lưới cố định & giới hạn vật thể cực nhỏ / dày đặc** [MÃ NGUỒN]:
   - Nhánh có độ phân giải cao nhất của YOLOv8 là `P3` với bước nhảy `stride = 8` [`yolov8.yaml:36-44`] [MÃ NGUỒN]. Mỗi ô lưới `P3` đại diện cho một vùng `8x8 pixel` trên ảnh đã thu phóng.
   - Nếu một vật thể sau khi thu phóng về `imgsz` có kích thước chỉ `4..7 pixel` (nhỏ hơn 1 ô lưới `8x8`), đặc trưng của nó bị gộp chung với nền xung quanh sau 3 lần tích chập giảm mẫu (`stride 2 -> 4 -> 8`), khiến mạng rất khó phân biệt vật thể với nhiễu nền [MÃ NGUỒN].
   - Tương tự, tại mỗi vị trí tâm lưới `(i, j)` trên một tầng `P3/P4/P5`, mạng chỉ xuất 1 dự đoán cho mỗi lớp; nếu 2 vật thể cùng lớp có tâm rơi vào đúng cùng 1 ô `8x8 pixel` và chồng lấp lớn hơn ngưỡng `iou` của NMS, thuật toán NMS sẽ xóa mất 1 trong 2 vật thể (xem mục 2.5 và Thí nghiệm D ở Phần 6) [MÃ NGUỒN].
2. **Xung đột của NMS khi đám đông che khuất nhau (Crowded Occlusion)** [MÃ NGUỒN]:
   - `TorchNMS.fast_nms` (`ultralytics/utils/nms.py:25-93`) chỉ nhìn vào hình học diện tích giao/hợp (`IoU`) giữa các khung mà không hiểu cấu trúc 3D của phòng chiếu [MÃ NGUỒN].
   - Nếu đặt `iou` cao (như `0.70` mặc định): một cái đầu duy nhất có thể sinh ra 2 khung dự đoán lệch nhau vài pixel có `IoU = 0.64..0.69` và cả hai đều sống sót qua NMS -> **đếm dư người** (đã chứng minh trên 5 ảnh `val` ở Thí nghiệm D) [DỰ ÁN].
   - Nếu hạ `iou` quá thấp (ví dụ `< 0.35`): khi khán giả hàng trước ngồi che một phần khán giả hàng sau làm 2 khung thật giao nhau mạnh, NMS lại xóa nhầm người ngồi sau -> **đếm thiếu người** [MÃ NGUỒN].
3. **Suy luận theo từng ảnh tĩnh (Frame-by-Frame Independence), không có trí nhớ thời gian** [MÃ NGUỒN] [DỰ ÁN]:
   - Khi gọi `model(frame)` [`main.py:217`], mạng CNN chỉ nhìn đúng 1 ma trận pixel tại mili-giây đó [MÃ NGUỒN] [DỰ ÁN]. Nếu ở giây thứ `t`, khán giả cúi xuống nhặt bắp rang hoặc quay đầu làm mất biên dạng trong 1 giây, YOLO lập tức trả về `0` ở ghế đó dù nửa giây trước vừa thấy người ngồi [DỰ ÁN]. (Phải kết hợp thêm `model.track()` hoặc bộ lọc trung bình trượt theo thời gian ở tầng ứng dụng mới khắc phục được).
4. **Phụ thuộc mạnh vào phân phối dữ liệu huấn luyện (Domain Shift / Out-of-Distribution)** [KIẾN THỨC CHUNG – chưa kiểm chứng trong lượt này] [DỰ ÁN]:
   - Mạng CNN học các mẫu текстуra (kết cấu tóc, viền đầu, độ tương phản với lưng ghế) từ tập `train`. Khi đổi góc lắp camera (từ góc chéo trên cao sang góc chính diện), đổi màu bọc ghế, hoặc đổi điều kiện chiếu sáng (đèn hồng ngoại IR ban đêm vs đèn vàng lúc sáng đèn), phân phối pixel thay đổi làm điểm `conf` tụt mạnh (chứng minh ở Thí nghiệm C Phần 6: chỉ làm mờ Gaussian hoặc giảm sáng 80% đã làm `mean_conf` tụt từ `0.599` xuống `0.423..0.436`) [DỰ ÁN].
5. **Chỉ xuất khung chữ nhật phẳng song song trục tọa độ (Axis-Aligned 2D Bounding Box)** [MÃ NGUỒN]:
   - Nhánh `Detect` (`block.py:2167`) chỉ xuất `(x1, y1, x2, y2)` trên mặt phẳng ảnh 2D, không biết chiều sâu `Z` (khoảng cách mét từ camera tới ghế) và không biết tư thế nghiêng của cơ thể [MÃ NGUỒN]. Do hiệu ứng phối cảnh camera góc cao, đầu một người ngồi hàng trước hoặc hơi ngả lưng có thể dịch tâm `(cx, cy)` trên ảnh 2D sang ô đa giác của ghế bên cạnh (chứng minh ở Thí nghiệm E Phần 6) [DỰ ÁN].

### 5.2. Giới hạn riêng của bản `YOLOv8n` (Nano) đang dùng
Đọc từ `ultralytics/cfg/models/v8/yolov8.yaml:12-18` [TÀI LIỆU]:
```text
scales: # [depth, width, max_channels]
  n: [0.33, 0.25, 1024]  # YOLOv8n summary: 129 layers, 3157200 parameters, 8.9 GFLOPs
  s: [0.33, 0.50, 1024]  # YOLOv8s summary: 129 layers, 11166560 parameters, 28.8 GFLOPs
  m: [0.67, 0.75, 768]   # YOLOv8m summary: 169 layers, 25902640 parameters, 79.3 GFLOPs
```
- **Dung lượng biểu diễn nhỏ (`width = 0.25`, `depth = 0.33`)**:
  - Tại tầng `P3` (nơi gánh toàn bộ trách nhiệm phát hiện các đầu người nhỏ `12..15 px`), `YOLOv8n` chỉ có `64 * 0.25 = 16` hoặc `128 * 0.25 = 32` tới `64` kênh đặc trưng và chỉ lặp `round(3 * 0.33) = 1` khối Bottleneck trong mỗi mô-đun `C2f` [MÃ NGUỒN].
  - Đổi lại cho tốc độ nhanh trên CPU (`3,005,843` tham số, `8.1 GFLOPs` sau khi fuse), `YOLOv8n` có độ chính xác định vị khung tinh (`mAP50-95 = 0.3775`) thấp hơn đáng kể so với `mAP50` (`0.8098`) vì biên khung dự đoán dễ lệch vài pixel trên vật thể nhỏ [DỰ ÁN].

### 5.3. Giới hạn thực tế trong dự án CineSight (Có số liệu đo từ tập dữ liệu thật)

Để thấy rõ thách thức của bài toán rạp chiếu phim, ta chạy đoạn mã Python đo phân phối chiều cao khung đầu (`h_orig` trên ảnh gốc `1920x1080`, `h_800` khi thu về `imgsz=800` lúc train, và `h_640` khi thu về `imgsz=640` lúc chạy `main.py`) trên toàn bộ **163 ảnh / 825 khung đầu** của `datasets/head_v2` (mã đầy đủ ở Phụ lục A.5) [DỰ ÁN]:

| Tập dữ liệu | Số ảnh (Số ảnh trống) | Tổng số đầu (Trung bình / ảnh) | `h_orig` (px trên `1920x1080`) `[min / p10 / med / max]` | `h_800` (px ở `imgsz=800`) `[min / med]` | Tỉ lệ `< 8 px` / `< 12 px` ở `imgsz=800` | `h_640` (px ở `imgsz=640`) `[min / med]` | Tỉ lệ `< 8 px` / `< 12 px` ở `imgsz=640` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`train`** | 98 (0) | 570 (`5.82`) | `18.0 / 31.0 / 36.0 / 56.0` | `7.5 / 15.0` | `0.18%` / `5.26%` | `6.0 / 12.0` | `2.11%` / **`51.23%`** |
| **`val`** | 22 (7) | 87 (`3.95`) | `18.0 / 30.0 / 36.0 / 50.0` | `7.5 / 15.0` | `1.15%` / `8.05%` | `6.0 / 12.0` | `4.60%` / **`50.57%`** |
| **`test`** | 43 (14) | 168 (`3.91`) | `23.0 / 29.7 / 32.0 / 49.0` | `9.6 / 13.3` | `0.00%` / `7.14%` | `7.7 / 10.7` | `2.98%` / **`86.90%`** |
| **Toàn bộ (`ALL`)** | **163 (21)** | **825 (`5.06`)** | **`18.0 / 30.0 / 35.0 / 56.0`** | **`7.5 / 14.6`** | **`0.24%` / `5.94%`** | **`6.0 / 11.7`** | **`2.55%` / `58.42%`** |

Từ bảng số liệu thật này và cấu hình dự án, có **6 giới hạn thực tế sống còn** bạn cần nêu rõ với giảng viên:
1. **Lệch `imgsz` giữa lúc huấn luyện (`800`) và lúc chạy `main.py` (mặc định `640`)** [DỰ ÁN]:
   - Khi huấn luyện ở `imgsz=800`, chỉ có **5.94%** số đầu người nhỏ hơn `12 px` (trung vị `14.6 px`).
   - Nhưng trong `main.py:217`, lệnh `model(frame, conf=0.25, verbose=False)` không truyền `imgsz=800`, nên Ultralytics dùng mặc định `imgsz=640`, làm **58.42% tổng số đầu người (và tới 86.90% ở tập `test`) bị thu nhỏ xuống dưới `12 px`** (chỉ tương đương `1..1.5` ô lưới `stride 8`)! [DỰ ÁN].
2. **Độ lệch phân phối dữ liệu cực lớn (Domain & Density Limitation)** [DỰ ÁN]:
   - Toàn bộ 163 ảnh chỉ trích từ **1 video duy nhất (`room1_cam_edited.mp4`)** của **1 góc camera cố định**, hoàn toàn là **ảnh xám 8-bit giả lập 3 kênh (`R=G=B`)** [DỰ ÁN].
   - Mỗi ảnh trong tập `train` chỉ có từ **4 đến 6 người ngồi** (`min=4, max=6`, trung bình `5.82` người/ảnh trên tổng số 135 ghế của phòng) [DỰ ÁN]. Mô hình **CHƯA BAO GIỜ** được nhìn thấy cảnh phòng chiếu đông khán giả (ví dụ 50–135 người ngồi kín rạp, đầu hàng trước che khuất đầu hàng sau) [DỰ ÁN].
3. **Rò rỉ thời gian (Temporal Leakage) giữa các tập dữ liệu cùng 1 video** [DỰ ÁN]:
   - Dù đã chia theo mốc thời gian (`train: 0..342s`, `val: 346..449s`, `test: 452..629s`), khoảng cách giữa ảnh cuối tập `train` (`342s`) và ảnh đầu tập `val` (`346s`) chỉ là **4 giây**, và giữa `val` (`449s`) với `test` (`452s`) chỉ là **3 giây**, với cùng những khán giả đó ngồi trên cùng những chiếc ghế đó [DỰ ÁN]. Do đó `mAP50 = 0.8098` trên `val` phản ánh khả năng nhận diện trên *cùng phòng chiếu và cùng nhóm khán giả*, chưa phản ánh khả năng tổng quát hóa sang phòng chiếu 2, 3, 4 hoặc ca chiếu khác [DỰ ÁN].
4. **Ngưỡng `iou=0.70` mặc định gây khung trùng (Double Counting)** [DỰ ÁN]:
   - `main.py:217` không truyền `iou`, nên dùng `iou=0.70` mặc định, khiến 5/22 ảnh `val` bị sinh khung trùng trên cùng 1 đầu người (`IoU = 0.639..0.692`) [DỰ ÁN].
5. **Nhạy cảm hình học khi ánh xạ sang sơ đồ ghế (`seat_mapper.py`)** [DỰ ÁN]:
   - `seat_mapper.py:52-75` lấy tâm khung `(cx, cy)` cộng độ lệch cố định `+10 px` hoặc `+18 px` theo trục dọc rồi kiểm tra điểm đó rơi vào đa giác ghế nào (`cv2.pointPolygonTest`). Khi khung YOLO dao động chỉ `±6 px` tới `±10 px`, tỉ lệ nhảy sang ghế khác hoặc trượt ra ngoài đa giác ghế lên tới **19.28% – 36.45%** (chứng minh ở Thí nghiệm E Phần 6) [DỰ ÁN].
6. **Tốc độ suy luận trên CPU (`~150–280 ms/ảnh`)** [DỰ ÁN]:
   - Trên CPU `i5-1135G7`, mỗi lần suy luận mất `151.8 ms` (`imgsz=640`) hoặc `193.5 ms` (`imgsz=800`). Nếu chỉ quét định kỳ 1 ảnh mỗi vài giây cho 1 phòng thì đáp ứng tốt, nhưng nếu muốn xử lý luồng video thời gian thực 30 FPS cho cả 4 phòng chiếu cùng lúc trên CPU này thì **không thể đáp ứng** nếu không giảm tần suất lấy mẫu (ví dụ 1 frame / 2–5 giây / phòng) hoặc dùng GPU / xuất OpenVINO [DỰ ÁN].

### 5.4. Giới hạn pháp lý / Giấy phép phần mềm (`AGPL-3.0`)
- Đọc trực tiếp từ `ai_service/venv/Lib/site-packages/ultralytics-8.4.160.dist-info/METADATA:18, 410-411` và dòng đầu mọi tệp `.py` trong `ultralytics` [TÀI LIỆU] [MÃ NGUỒN]:
  ```text
  License-Expression: AGPL-3.0
  Dual-licensed under AGPL-3.0 (open-source) and Enterprise License (commercial):
  - AGPL-3.0 License: Ideal for academic research, testing, and open-source projects.
  - Enterprise License: Required for commercial integration into proprietary software without open-sourcing your code.
  ```
- **Ý nghĩa**: Với **đồ án môn học / khóa luận tốt nghiệp tại trường đại học** và dự án mã nguồn mở, giấy phép `AGPL-3.0` hoàn toàn hợp lệ và miễn phí. Tuy nhiên, nếu sau này đem đóng gói `CineSight` thành sản phẩm thương mại mã nguồn đóng (proprietary SaaS/on-premise bán cho cụm rạp) mà không công khai mã nguồn theo điều khoản AGPL-3.0, đơn vị triển khai bắt buộc phải mua giấy phép Enterprise của Ultralytics hoặc chuyển sang chạy mô hình đã xuất `.onnx` trên `onnxruntime` (giấy phép MIT) không phụ thuộc mã nguồn `ultralytics` [TÀI LIỆU].

### 5.4b. Bảng tóm tắt 6 giới hạn chính trong CineSight và cách giảm nhẹ (Mitigation)

| STT | Giới hạn | Nguyên nhân kỹ thuật | Cách giảm nhẹ trong cấu hình YOLO (`main.py` / `export`) | Cách giảm nhẹ ở tầng ứng dụng (`seat_mapper.py` / Backend) |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Đầu người ở hàng xa rất nhỏ (`18..35 px` trên `1920x1080`)** | Thu phóng về `imgsz=640` làm 58.4% đầu `< 12 px` (chỉ bằng 1.5 ô lưới `stride 8`). | Truyền rõ `imgsz=800` trong `main.py:217` để khớp với `args.yaml` lúc train (`< 12 px` giảm còn 5.9%). | Cắt bỏ vùng trần nhà/màn hình không có ghế (ROI crop) trước khi đưa vào YOLO để tăng độ phân giải hiệu dụng trên khu vực ghế. |
| **2** | **Đếm dư 2 khung trên cùng 1 đầu người** | `main.py:217` để mặc định `iou=0.70`, không triệt tiêu được các khung trùng có `IoU = 0.63..0.69`. | Hạ ngưỡng NMS xuống `iou=0.45` hoặc `iou=0.50` trong `main.py:217`. | Trong `seat_mapper.py`, mỗi đa giác ghế chỉ nhận trạng thái boolean `occupied = True/False` (dù có 2 khung rơi vào cùng 1 ghế cũng chỉ tính 1 ghế có người). |
| **3** | **Khung nhấp nháy / mất dấu tạm thời khi khán giả cúi đầu hoặc phim tối** | `model(frame)` suy luận từng frame độc lập; ảnh tối làm `conf` tụt xuống gần `0.25`. | Dùng `model.track(frame, persist=True, tracker="bytetrack.yaml")` để giữ `track_id` bằng bộ lọc Kalman. | Dùng bộ đệm trung bình trượt theo thời gian (Temporal Smoothing / Debounce: ghế chỉ đổi trạng thái khi xuất hiện trong `>= 3/5` lần quét liên tiếp). |
| **4** | **Tâm khung lệch vài pixel làm nhảy sang ghế bên cạnh** | Khung 2D không có chiều sâu 3D; `mAP50-95 = 0.3775` cho thấy biên khung có sai số vài pixel. | Huấn luyện thêm dữ liệu hoặc dùng bản `yolov8s.pt` nếu có GPU để tăng `mAP50-95`. | Tinh chỉnh đa giác ghế trong `seats_config_room1.json` có vùng đệm hợp lý; thay vì chỉ kiểm tra 1 điểm tâm, tính diện tích giao giữa vùng dưới của khung đầu và đa giác ghế. |
| **5** | **Dữ liệu train chỉ có 4–6 người/ảnh trên 1 góc camera** | Toàn bộ 163 ảnh lấy từ 1 video `room1_cam_edited.mp4`. | Thu thập thêm video ở các ca chiếu đông người (50–100 khách) và từ cả 4 phòng chiếu để fine-tune tiếp. | Cho phép cấu hình `seats_config_roomX.json` và ngưỡng `conf` riêng cho từng phòng chiếu theo góc lắp camera thực tế. |
| **6** | **Tốc độ CPU ~150–194 ms/ảnh** | Chạy PyTorch `.pt` thuần trên CPU `i5-1135G7`. | Xuất mô hình sang `OpenVINO` hoặc `ONNX Runtime` để tăng tốc trên CPU Intel. | Cơ chế Polling/Scheduler theo chu kỳ (ví dụ quét mỗi phòng 1 lần mỗi 5–10 giây vì khán giả ngồi xem phim ít di chuyển liên tục). |

---

## PHẦN 6: THÍ NGHIỆM NHỎ MINH HỌA GIỚI HẠN (`tools/yolo_lab.py`)
*(Trả lời Yêu cầu (1) & (2) của giảng viên bằng số liệu thực nghiệm trực tiếp trên tập `val` của dự án)*

Kịch bản đọc-duy-nhất (read-only) đã được lưu tại [`c:\CineSightApp\ai_service\tools\yolo_lab.py`](file:///c:/CineSightApp/ai_service/tools/yolo_lab.py) [DỰ ÁN]. Kịch bản này không ghi bất kỳ tệp nào ra đĩa, chỉ nạp `best_head_v2.pt` và chạy 5 thí nghiệm định lượng trực tiếp trên các ảnh `val` thật của dự án.

### 6.1. Output nguyên văn khi chạy `python tools/yolo_lab.py`

```text
========================================================================
YOLO LAB - CINESIGHT EMPIRICAL EXPERIMENTS (READ-ONLY)
Model: C:\CineSightApp\ai_service\best_head_v2.pt
Val images count: 22
========================================================================

--- EXPERIMENT A: CONFIDENCE THRESHOLD SWEEP (imgsz=640, iou=0.7) ---
Frame                      | GT | conf=0.15 | conf=0.25 | conf=0.4 | conf=0.6
------------------------------------------------------------------------------
room1_cam_edited_0346s.jpg |  6 |         7 |         5 |        5 |        3
room1_cam_edited_0351s.jpg |  6 |         6 |         6 |        6 |        5
room1_cam_edited_0356s.jpg |  6 |         8 |         6 |        6 |        4
room1_cam_edited_0360s.jpg |  6 |         6 |         6 |        4 |        1
room1_cam_edited_0365s.jpg |  6 |         8 |         6 |        6 |        3
room1_cam_edited_0370s.jpg |  6 |         8 |         5 |        5 |        1
room1_cam_edited_0374s.jpg |  6 |         8 |         7 |        5 |        4
room1_cam_edited_0378s.jpg |  6 |         6 |         6 |        5 |        1
room1_cam_edited_0383s.jpg |  6 |         7 |         5 |        5 |        3
room1_cam_edited_0388s.jpg |  6 |         8 |         6 |        6 |        3
------------------------------------------------------------------------------
Summary over 10 frames (Total GT = 60 heads):
  conf=0.15: Total Pred =  72 | Diff = +12 | MAE = 1.20 heads/frame | Bias = +1.20
  conf=0.25: Total Pred =  58 | Diff =  -2 | MAE = 0.40 heads/frame | Bias = -0.20
  conf=0.40: Total Pred =  53 | Diff =  -7 | MAE = 0.70 heads/frame | Bias = -0.70
  conf=0.60: Total Pred =  28 | Diff = -32 | MAE = 3.20 heads/frame | Bias = -3.20

--- EXPERIMENT B: IMGSZ SWEEP (conf=0.25, iou=0.7) ---
imgsz | Total Pred (GT=60) | MAE (heads/img) | Single-frame CPU time (mean ± std ms, 10 runs)
----------------------------------------------------------------------------------------------
  320 |                 52 |            1.00 |   86.3 ± 5.7 ms
  480 |                 67 |            1.10 |  107.1 ± 2.0 ms
  640 |                 58 |            0.40 |  151.8 ± 12.1 ms
  800 |                 59 |            0.50 |  193.5 ± 11.8 ms
  960 |                 61 |            0.50 |  282.6 ± 21.6 ms

--- EXPERIMENT C: IMAGE DEGRADATION ON room1_cam_edited_0346s.jpg (GT=6, conf=0.25, imgsz=640) ---
Condition                           | Pred Count | Mean Conf | Max Conf | Conf List
-----------------------------------------------------------------------------------
Original (1920x1080)                |          5 |     0.599 |    0.712 | [0.712, 0.703, 0.541, 0.531, 0.51]
GaussianBlur (15x15, sigma=5)       |          5 |     0.423 |    0.600 | [0.6, 0.464, 0.43, 0.359, 0.26]
Darkened -60% (pixel * 0.4)         |          5 |     0.510 |    0.695 | [0.695, 0.538, 0.525, 0.467, 0.326]
Darkened -80% (pixel * 0.2)         |          4 |     0.436 |    0.591 | [0.591, 0.449, 0.388, 0.317]
Downscaled 50% (960x540->1920x1080) |          5 |     0.579 |    0.703 | [0.703, 0.697, 0.506, 0.501, 0.489]
Downscaled 25% (480x270->1920x1080) |          5 |     0.580 |    0.694 | [0.694, 0.669, 0.589, 0.478, 0.468]

--- EXPERIMENT D: NMS IOU THRESHOLD SWEEP (conf=0.25, imgsz=640) ---
Single frame room1_cam_edited_0346s.jpg (GT=6):
  iou=0.30 -> 5 boxes: [[947.4, 211.0, 976.7, 250.3, 0.712], [651.2, 130.6, 675.2, 162.8, 0.703], [492.9, 137.3, 521.4, 169.3, 0.541], [730.9, 257.4, 768.2, 303.7, 0.531], [854.9, 145.6, 886.9, 181.6, 0.51]]
  iou=0.50 -> 5 boxes: [[947.4, 211.0, 976.7, 250.3, 0.712], [651.2, 130.6, 675.2, 162.8, 0.703], [492.9, 137.3, 521.4, 169.3, 0.541], [730.9, 257.4, 768.2, 303.7, 0.531], [854.9, 145.6, 886.9, 181.6, 0.51]]
  iou=0.70 -> 5 boxes: [[947.4, 211.0, 976.7, 250.3, 0.712], [651.2, 130.6, 675.2, 162.8, 0.703], [492.9, 137.3, 521.4, 169.3, 0.541], [730.9, 257.4, 768.2, 303.7, 0.531], [854.9, 145.6, 886.9, 181.6, 0.51]]
  iou=0.85 -> 6 boxes: [[946.4, 210.9, 976.9, 249.5, 0.709], [651.1, 129.9, 675.1, 163.3, 0.7], [492.6, 138.2, 521.3, 169.1, 0.562], [730.3, 257.2, 768.8, 303.5, 0.531], [856.0, 147.0, 887.1, 181.8, 0.488], [851.8, 146.9, 885.7, 182.0, 0.329]]
    Pairwise IoU > 0.2 at iou=0.85: Box 4 & Box 5 have IoU = 0.8340

Frames across all 22 val images where box count changes across iou=[0.3, 0.45, 0.5, 0.6, 0.7, 0.85]:
  room1_cam_edited_0346s.jpg: {0.3: 5, 0.45: 5, 0.5: 5, 0.6: 5, 0.7: 5, 0.85: 6}
  room1_cam_edited_0351s.jpg: {0.3: 6, 0.45: 6, 0.5: 6, 0.6: 6, 0.7: 6, 0.85: 9}
  room1_cam_edited_0356s.jpg: {0.3: 6, 0.45: 6, 0.5: 6, 0.6: 6, 0.7: 6, 0.85: 9}
  room1_cam_edited_0360s.jpg: {0.3: 6, 0.45: 6, 0.5: 6, 0.6: 6, 0.7: 6, 0.85: 8}
  room1_cam_edited_0365s.jpg: {0.3: 6, 0.45: 6, 0.5: 6, 0.6: 6, 0.7: 6, 0.85: 7}
  room1_cam_edited_0370s.jpg: {0.3: 5, 0.45: 5, 0.5: 5, 0.6: 5, 0.7: 5, 0.85: 9}
  room1_cam_edited_0374s.jpg: {0.3: 5, 0.45: 5, 0.5: 5, 0.6: 5, 0.7: 7, 0.85: 8}
  room1_cam_edited_0378s.jpg: {0.3: 5, 0.45: 5, 0.5: 5, 0.6: 5, 0.7: 6, 0.85: 8}
  room1_cam_edited_0383s.jpg: {0.3: 5, 0.45: 5, 0.5: 5, 0.6: 5, 0.7: 5, 0.85: 8}
  room1_cam_edited_0388s.jpg: {0.3: 4, 0.45: 4, 0.5: 4, 0.6: 4, 0.7: 6, 0.85: 6}
  room1_cam_edited_0392s.jpg: {0.3: 3, 0.45: 3, 0.5: 3, 0.6: 3, 0.7: 4, 0.85: 5}
  room1_cam_edited_0395s.jpg: {0.3: 4, 0.45: 4, 0.5: 4, 0.6: 4, 0.7: 5, 0.85: 6}
  room1_cam_edited_0399s.jpg: {0.3: 4, 0.45: 4, 0.5: 4, 0.6: 4, 0.7: 4, 0.85: 5}
  room1_cam_edited_0404s.jpg: {0.3: 5, 0.45: 5, 0.5: 5, 0.6: 5, 0.7: 5, 0.85: 8}
  room1_cam_edited_0419s.jpg: {0.3: 3, 0.45: 3, 0.5: 3, 0.6: 3, 0.7: 3, 0.85: 4}

--- EXPERIMENT E: BOUNDING BOX CENTER PERTURBATION VS SEAT POLYGONS ---
Total predicted boxes across 22 val frames (conf=0.25, imgsz=640): 83
Loaded 135 real seat polygons from seats_config_room1.json
1) Real seat polygons (pure center (cx, cy), 4 corner shifts per box = 332 trials):
  Shift ± 3 px: 40/332 (12.05%) changed seat assignment
  Shift ± 6 px: 56/332 (16.87%) changed seat assignment
  Shift ±10 px: 77/332 (23.19%) changed seat assignment
2) Real seat polygons (with seat_mapper.py camera-tilt y-offset +10/+18 px):
  Shift ± 3 px: 46/332 (13.86%) changed seat assignment
  Shift ± 6 px: 64/332 (19.28%) changed seat assignment
  Shift ±10 px: 121/332 (36.45%) changed seat assignment
3) Synthetic uniform 40x30 px seat grid (20 random trials per box = 1660 trials):
  Shift ± 3 px: 74/1660 (4.46%) changed seat cell
  Shift ± 6 px: 278/1660 (16.75%) changed seat cell
  Shift ±10 px: 615/1660 (37.05%) changed seat cell
```

### 6.2. Phân tích 5 kết luận rút ra từ thực nghiệm

1. **Thí nghiệm A (`conf` sweep)**:
   - Hạ `conf=0.15` làm tổng số khung dự đoán trên 10 ảnh vọt lên `72` so với `60` đầu thật (`Bias = +1.20` đầu/ảnh — báo giả trên ghế trống).
   - Nâng `conf=0.60` làm tổng số khung rớt thảm xuống `28/60` (`Bias = -3.20` đầu/ảnh — bỏ sót hơn một nửa khán giả!).
   - Ngưỡng `conf=0.25` đang dùng trong `main.py:217` đạt sai số tuyệt đối trung bình thấp nhất (`MAE = 0.40` đầu/ảnh, tổng `58/60` đầu) [DỰ ÁN].
2. **Thí nghiệm B (`imgsz` sweep)**:
   - Ở `imgsz=320`, số đầu phát hiện tụt xuống `52/60` (`MAE = 1.00`).
   - Ở `imgsz=800` (đúng kích thước lúc train), mô hình phát hiện `59/60` đầu (so với `58/60` ở `imgsz=640`), với thời gian CPU tăng từ `151.8 ms` lên `193.5 ms` (+41.7 ms/ảnh) [DỰ ÁN].
3. **Thí nghiệm C (Làm suy giảm chất lượng ảnh trên `0346s.jpg`)**:
   - Khi làm mờ Gaussian (`15x15, sigma=5` — mô phỏng ống kính camera bị mờ hoặc mất nét), điểm tự tin trung bình `mean_conf` rơi từ `0.599` xuống `0.423`, trong đó khung thấp nhất chỉ còn `0.260` (sát nút bị loại bởi ngưỡng `conf=0.25`) [DỰ ÁN].
   - Khi làm tối 80% (`pixel * 0.2` — mô phỏng cảnh phim rất tối), mô hình mất hẳn 1 đầu người (`5 -> 4`) và `mean_conf` giảm còn `0.436` [DỰ ÁN].
4. **Thí nghiệm D (Quét ngưỡng NMS `iou`)**:
   - Trên 5 ảnh kiểm định (`0374s`, `0378s`, `0388s`, `0392s`, `0395s`), việc để `iou=0.70` mặc định làm xuất hiện từ 1 đến 2 khung trùng nhau trên cùng một cái đầu (với `IoU` giữa 2 khung từ `0.639` đến `0.692`). Khi hạ `iou` xuống `0.50` hoặc `0.45`, toàn bộ số khung trùng này biến mất hoàn toàn mà không làm mất cái đầu thật nào [DỰ ÁN].
5. **Thí nghiệm E (Độ nhạy tọa độ tâm với đa giác ghế thật trong `seats_config_room1.json`)**:
   - Trên 135 đa giác ghế thật của Phòng 1, khi cộng độ lệch nghiêng camera của `seat_mapper.py:62` (`cy + 10` hoặc `cy + 18`), chỉ cần tâm khung dịch chuyển `±6 px` là **19.28%** trường hợp bị đổi kết quả gán ghế, và ở `±10 px` là **36.45%** [DỰ ÁN]. Điều này chứng minh tại sao `mAP50-95 = 0.3775` (độ khít pixel của khung) lại ảnh hưởng trực tiếp tới bài toán gán ghế.

---

## PHẦN 7: 10 CÂU HỎI GIẢNG VIÊN HAY HỎI + CÂU TRẢ LỜI MẪU
*(Mỗi câu trả lời gói gọn trong 3–5 câu, gắn trực tiếp số liệu thật của dự án CineSight để bạn trả lời vấn đáp tự tin)*

### Câu 1: Vì sao em chọn YOLOv8n (nano) mà không chọn YOLOv8s/m/l hay Faster R-CNN?
> **Trả lời mẫu**: Hệ thống CineSight của em chạy suy luận trực tiếp trên máy chủ CPU (`Intel Core i5-1135G7 @ 2.40GHz`), không có GPU rời [DỰ ÁN]. Bản `YOLOv8n` có hệ số thu nhỏ `depth=0.33, width=0.25` [`yolov8.yaml:13`] nên chỉ có `3,005,843` tham số và `8.1 GFLOPs` sau khi gộp lớp (`fuse`), cho tốc độ suy luận ~`151.8 ms/ảnh` ở `imgsz=640` và ~`193.5 ms/ảnh` ở `imgsz=800` [MÃ NGUỒN] [DỰ ÁN]. Nếu dùng `YOLOv8s` (`28.8 GFLOPs`, gấp 3.2 lần phép tính) hoặc `YOLOv8m` (`79.3 GFLOPs`, gấp 9 lần) hay các mạng 2 giai đoạn (Faster R-CNN), thời gian xử lý trên CPU sẽ vọt lên từ 0.5 đến vài giây mỗi khung hình và thời gian huấn luyện 50 epoch sẽ tăng từ `2.08 giờ` lên 7–20 giờ trên CPU [TÀI LIỆU] [DỰ ÁN].

### Câu 2: Vì sao em lại huấn luyện mô hình nhận diện `head` (đầu người) mà không dùng luôn lớp `person` có sẵn của `yolov8n.pt` gốc trên COCO?
> **Trả lời mẫu**: Mô hình `yolov8n.pt` gốc được huấn luyện trên bộ dữ liệu COCO 80 lớp với đối tượng `person` là toàn thân người đứng hoặc ngồi ở cự ly gần [DỰ ÁN]. Trong rạp chiếu phim, lưng ghế cao che khuất từ 70%–85% cơ thể khán giả, camera hồng ngoại gắn trên cao chỉ nhìn thấy phần đỉnh đầu và nửa mặt trên có chiều cao trung vị `35 pixel` trên ảnh Full HD (`1920x1080`) [DỰ ÁN]. Khi chạy thử mô hình COCO gốc hoặc khi khung toàn thân kéo dài qua nhiều hàng ghế, tâm khung `person` rơi xuống lưng ghế hàng trước dẫn đến gán sai ghế hoàn toàn; vì vậy bắt buộc phải đóng khung riêng phần đầu (`nc=1, names={0: 'head'}`) để định vị chính xác từng chiếc ghế [DỰ ÁN].

### Câu 3: Với chỉ 163 ảnh (98 ảnh `train`, 22 ảnh `val`, 43 ảnh `test`), tại sao mô hình không bị học vẹt (overfitting) nặng và học được từ đâu?
> **Trả lời mẫu**: Nhờ hai cơ chế chính: **Học chuyển giao (Transfer Learning)** và **Tăng cường dữ liệu Mosaic (`mosaic=1.0`)** [MÃ NGUỒN] [DỰ ÁN]. Khi khởi tạo từ `yolov8n.pt`, `352/355` tensor trọng số (`3,005,824 / 3,011,043` tham số = **99.83%**) của Backbone và Neck đã biết sẵn cách trích xuất cạnh, góc và kết cấu từ tập COCO được nạp thẳng sang mô hình mới, chỉ có `3` lớp cuối (`5,219` tham số) thay đổi theo `nc=1` [`tasks.py:1572`, `trainer.py:854`] [MÃ NGUỒN] [DỰ ÁN]. Đồng thời, ở 40 epoch đầu, mỗi ảnh được ghép ngẫu nhiên 4 khung hình (`Mosaic`) kèm dịch chuyển `10%`, co giãn `±50%`, lật ngang `50%` và đổi độ sáng `±40%`, giúp mô hình không bao giờ nhìn thấy cùng một bố cục pixel lặp lại, giữ cho `val/box_loss` giảm từ `1.8832` (Epoch 1) xuống `1.6134` (Epoch 35) và không bị phình ngược lên ở cuối quá trình học [DỰ ÁN].

### Câu 4: Tại sao `mAP50` của em đạt `0.8098` (81%) nhưng `mAP50-95` chỉ đạt `0.3775` (37.8%)? Như vậy là tốt hay xấu?
> **Trả lời mẫu**: `mAP50` chỉ yêu cầu khung dự đoán chồng lấp với nhãn thật từ `IoU >= 0.50` là tính đúng, còn `mAP50-95` tính trung bình trên 10 ngưỡng khắt khe từ `0.50` đến `0.95` [`metrics.py:806`] [MÃ NGUỒN]. Trong dữ liệu CineSight, kích thước trung vị của đầu người chỉ là `35x35 pixel` trên ảnh gốc (tương đương `14.6x14.6 pixel` ở `imgsz=800`) [DỰ ÁN]. Với vật thể nhỏ như vậy, chỉ cần biên khung dự đoán lệch đi `2–3 pixel` (do ranh giới tóc đen và ghế tối mờ nhòe) thì `IoU` đã tụt từ `1.0` xuống dưới `0.65`, làm điểm ở các ngưỡng `IoU = 0.75..0.95` giảm mạnh [DỰ ÁN]. Đối với bài toán kiểm tra ghế có người ngồi hay không, việc xác định đúng vị trí đầu ở mức `IoU >= 0.50` (`mAP50 = 0.81`) là chỉ số quan trọng hơn, dù sai số vài pixel vẫn có thể ảnh hưởng tới những ghế sát biên (như đã đo ở Thí nghiệm E) [DỰ ÁN].

### Câu 5: Tại sao trong `train_head_v2.py` em đặt `imgsz=800` thay vì `640` mặc định, nhưng trong `main.py` lại chưa truyền `imgsz=800`?
> **Trả lời mẫu**: Trên ảnh `1920x1080`, chiều cao đầu người nhỏ nhất là `18 px` và trung vị là `35 px` [DỰ ÁN]. Khi thu về `imgsz=640`, có tới **58.42%** tổng số đầu người bị co xuống nhỏ hơn `12 px` (sát giới hạn 1 ô lưới `stride=8` của tầng P3), trong khi ở `imgsz=800` tỉ lệ nhỏ hơn `12 px` giảm xuống chỉ còn **5.94%** [DỰ ÁN]. Tuy nhiên, trong `main.py:217`, lệnh gọi `model(frame, conf=0.25, verbose=False)` hiện đang bỏ trống tham số `imgsz`, khiến Ultralytics tự lấy mặc định `640` [`default.yaml:18`] [MÃ NGUỒN] [DỰ ÁN]. Đây là một điểm lệch giữa huấn luyện và triển khai mà em đã phát hiện qua quá trình kiểm tra mã nguồn và thực nghiệm (ở `imgsz=800` phát hiện thêm được đầu người bị sót với chi phí tăng thêm ~`41.7 ms` CPU mỗi ảnh) [DỰ ÁN].

### Câu 6: Ngưỡng `conf=0.25` và `iou=0.7` trong `main.py` có ý nghĩa gì? Nếu tăng hoặc giảm thì chuyện gì xảy ra?
> **Trả lời mẫu**: `conf=0.25` là ngưỡng điểm tự tin tối thiểu để giữ lại một khung dự đoán trước khi lọc trùng, còn `iou=0.70` là ngưỡng diện tích giao/hợp trong thuật toán Non-Maximum Suppression (NMS) để xóa các khung chồng lên nhau của cùng một người [`nms.py:66-127`] [MÃ NGUỒN]. Thực nghiệm trên 10 ảnh `val` (`60` đầu thật) cho thấy: nếu hạ `conf=0.15` thì mô hình báo giả thêm 12 đầu (`72/60`), nếu nâng `conf=0.60` thì bỏ sót mất 32 đầu (`28/60`), còn `conf=0.25` cân bằng nhất (`58/60`, `MAE = 0.40`) [DỰ ÁN]. Ngược lại, ngưỡng `iou=0.70` mặc định đang hơi cao, làm 5/22 ảnh `val` bị sinh 2 khung trùng trên cùng 1 đầu (với `IoU` từ `0.639` đến `0.692`); hạ xuống `iou=0.45..0.50` sẽ loại bỏ triệt để hiện tượng đếm trùng này [DỰ ÁN].

### Câu 7: Hàm mất mát (Loss function) của YOLOv8 gồm những thành phần nào và tại sao có tới 3 cột loss trong `results.csv`?
> **Trả lời mẫu**: Hàm mất mát tổng của YOLOv8 (`v8DetectionLoss` trong `loss.py:211-265`) là tổng có trọng số của 3 thành phần: `box_loss` (trọng số `7.5`), `cls_loss` (trọng số `0.5`), và `dfl_loss` (trọng số `1.5`) [`default.yaml:110-112`] [MÃ NGUỒN] [TÀI LIỆU]. Trong đó: (1) `box_loss = 1 - CIoU` phạt sai lệch diện tích chồng lấp, khoảng cách tâm và tỉ lệ khung hình; (2) `cls_loss` dùng Binary Cross-Entropy (`BCEWithLogitsLoss`) phạt điểm xác suất lớp `head`; và (3) `dfl_loss` (Distribution Focal Loss) ép mạng học phân phối xác suất trên 16 nấc khoảng cách từ tâm neo tới 4 cạnh khung để định vị biên khung mượt hơn khi ranh giới đầu người bị mờ [MÃ NGUỒN].

### Câu 8: Kết quả `mAP50 = 0.8098` trên tập `val` có đảm bảo khi mang sang phòng chiếu 2, 3, 4 mô hình cũng đạt 81% không?
> **Trả lời mẫu**: **Dạ không đảm bảo**, và em xin đánh giá trung thực điểm hạn chế này của bộ dữ liệu hiện tại [DỰ ÁN]. Toàn bộ 163 ảnh (`train`, `val`, `test`) đều được trích từ cùng một video `room1_cam_edited.mp4` của Phòng chiếu 1 (ảnh xám hồng ngoại `R=G=B`), trong đó mỗi ảnh chỉ có tối đa 6 người ngồi và khoảng cách thời gian giữa ảnh cuối tập `train` (`342s`) với ảnh đầu tập `val` (`346s`) chỉ là **4 giây** trên cùng một nhóm khán giả [DỰ ÁN]. Vì vậy, điểm `mAP50 = 0.8098` hiện có rò rỉ bối cảnh (cùng phòng, cùng người ngồi) và chưa kiểm chứng được khả năng tổng quát hóa khi sang phòng chiếu có góc lắp camera khác hoặc khi rạp đông 50–100 người ngồi che khuất nhau [DỰ ÁN].

### Câu 9: Làm thế nào hệ thống biết một cái đầu phát hiện được đang ngồi ở ghế số mấy (ví dụ ghế `D5` hay `E6`)?
> **Trả lời mẫu**: Bản thân YOLO chỉ trả về tọa độ khung chữ nhật `[x1, y1, x2, y2]` trên ảnh `1920x1080`, hoàn toàn không biết khái niệm "ghế" [MÃ NGUỒN] [DỰ ÁN]. Sau khi YOLO trả kết quả, mô-đun `seat_mapper.py:52-75` của dự án tính tọa độ tâm đầu `(cx, cy)`, cộng thêm một độ lệch trục dọc (`+10 px` ở nửa trên ảnh hoặc `+18 px` ở nửa dưới ảnh để bù góc nghiêng camera từ trên cao nhìn xuống), rồi dùng hàm hình học `cv2.pointPolygonTest` kiểm tra xem điểm đó nằm bên trong đa giác 4 đỉnh của ghế nào trong tệp `seats_configs/seats_config_room1.json` (gồm 135 đa giác ghế) [DỰ ÁN].

### Câu 10: Nếu có thêm 1 tuần để cải tiến hệ thống AI này mà không cần mua GPU đắt tiền, em sẽ làm gì ưu tiên nhất?
> **Trả lời mẫu**: Em sẽ thực hiện 4 việc theo thứ tự ưu tiên:
> 1. **Sửa ngay 1 dòng trong `main.py:217`**: truyền rõ `imgsz=800, iou=0.45` vào `model(frame, conf=0.25, imgsz=800, iou=0.45, verbose=False)` để khớp kích thước huấn luyện và khử toàn bộ khung trùng NMS [DỰ ÁN].
> 2. **Thêm bộ đệm chống nhấp nháy theo thời gian (Temporal Debounce)**: chỉ xác nhận ghế có người/trống khi trạng thái giữ nguyên trong `3` lần quét liên tiếp [DỰ ÁN].
> 3. **Xuất mô hình sang OpenVINO (`model.export(format="openvino")`)**: giảm thời gian suy luận trên CPU Intel `i5-1135G7` từ ~`193 ms` xuống dưới `100 ms` [MÃ NGUỒN] [DỰ ÁN].
> 4. **Bổ sung dữ liệu**: thu thập thêm video từ các ca chiếu đông người và các góc phòng khác, chia tập `train/val/test` theo **ca chiếu độc lập** thay vì cắt chung 1 video [DỰ ÁN].

---

## PHẦN 8: DÀN Ý SLIDE TRÌNH BÀY (12 SLIDE)
*(Thiết kế cho bài thuyết trình 12–15 phút trước giảng viên, có ghi rõ câu chuyển ý giữa các slide)*

| Slide | Tiêu đề Slide | Nội dung chính trên Slide (Gạch đầu dòng ngắn gọn) | Hình / Bảng nên đưa vào (An toàn quyền riêng tư, không lộ mặt khách) | Câu nói chuyển tiếp sang Slide sau |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Tổng quan bài toán CineSight & Vai trò của YOLOv8** | • Bài toán: Tự động kiểm đếm & xác định vị trí ghế có người ngồi trong rạp chiếu phim từ camera giám sát.<br>• Kiến trúc: Camera (`1920x1080`) -> `YOLOv8n` (`best_head_v2.pt`) -> `seat_mapper.py` (135 đa giác ghế) -> Flutter App.<br>• Môi trường: `Python 3.14.3`, `PyTorch 2.14.0+cpu`, `Ultralytics 8.4.160`. | Sơ đồ khối luồng dữ liệu 5 bước + Ảnh sơ đồ đa giác ghế 2D (`2d_seatmap_diagram.png`). | *"Để hiểu vì sao một ảnh camera biến thành danh sách tọa độ đầu người, chúng ta đi vào cấu trúc bên trong của mạng YOLOv8n ở Slide 2."* |
| **2** | **Kiến trúc mạng YOLOv8n (Backbone – Neck – Head)** | • **Backbone** (lớp 0–9): 4 khối `C2f` + `SPPF` trích xuất đặc trưng ở 3 độ phân giải `P3 (stride 8)`, `P4 (stride 16)`, `P5 (stride 32)`.<br>• **Neck** (lớp 10–21): Gộp đa tỉ lệ kiểu PAN-FPN.<br>• **Detect Head** (lớp 22): Anchor-free, tách nhánh Tọa độ (`reg_max=16`) và Nhánh lớp (`nc=1: head`).<br>• Quy mô: `72` lớp (sau khi fuse), `3,005,843` tham số, `8.1 GFLOPs`. | Sơ đồ khối Backbone – Neck – Head + Bảng đối chiếu `yolov8n.pt` (80 lớp) vs `best_head_v2.pt` (1 lớp). | *"Với kích thước đầu người trong rạp rất nhỏ, ảnh đầu vào được biến đổi toán học như thế nào khi đi qua mạng? Chúng ta xem Slide 3."* |
| **3** | **Phép toán Tiền xử lý (`LetterBox`) & Lưới 8,400 tâm neo** | • Ảnh gốc `1920x1080` thu phóng giữ tỉ lệ 16:9: về `640x384` (khi chạy `main.py`, `5,040` ô neo) hoặc `800x480` (khi train, `7,875` ô neo).<br>• Công thức chuẩn hóa `pixel / 255.0 -> [0.0, 1.0]`.<br>• 99% đầu người trong rạp (`18..56 px` gốc -> `7.5..23.3 px` ở `imgsz=800`) do tầng **`P3 (stride 8)`** đảm nhiệm. | Bảng kích thước lưới `P3, P4, P5` ở `imgsz=800` vs `640` + Minh họa viền xám `LetterBox(114,114,114)`. | *"Tại mỗi ô lưới P3 đó, mạng thực hiện những phép toán nào để vẽ ra khung chữ nhật và tính độ tự tin? Đó là nội dung Slide 4."* |
| **4** | **Các phép toán bên trong: Conv+BN+SiLU, DFL Softmax & Sigmoid** *(Trả lời Yêu cầu 2)* | • **Tích chập + SiLU**: `SiLU(x) = x / (1 + exp(-x))` giữ đạo hàm mượt.<br>• **DFL (`reg_max=16`)**: Softmax trên 16 nấc nhân tích vô hướng `0..15` để giải mã khoảng cách `lt, rb -> (x1, y1, x2, y2)`.<br>• **Xác suất lớp**: `conf = sigmoid(logit)` (ví dụ `logit=1.20 -> conf=0.7685`). | Hộp công thức văn bản thuần của `SiLU`, `DFL`, `dist2bbox` kèm ví dụ số kiểm chứng bằng Python. | *"Khi mạng xuất ra hàng nghìn khung ứng viên từ các ô lưới, làm sao giữ lại đúng 1 khung cho mỗi người và chấm điểm độ chính xác? Chúng ta sang Slide 5."* |
| **5** | **Toán học Hậu xử lý (IoU, CIoU, NMS) & Chỉ số mAP** *(Trả lời Yêu cầu 2)* | • **IoU & CIoU**: Đo độ chồng lấp + phạt khoảng cách tâm + phạt độ lệch tỉ lệ `w/h`.<br>• **NMS (`conf=0.25, iou=0.70`)**: Sắp xếp giảm dần theo `conf`, loại các khung trùng.<br>• **Precision (`0.902`), Recall (`0.759`), mAP50 (`0.810`), mAP50-95 (`0.378`)**: Giải thích vì sao `mAP50-95` thấp hơn trên vật thể nhỏ `15 px`. | Đồ thị `BoxPR_curve.png` và `BoxF1_curve.png` từ `runs/detect/head_v2_official/` (không chứa ảnh khán giả). | *"Làm thế nào mô hình học được các trọng số đó chỉ từ 163 khung hình camera rạp chiếu? Chúng ta chuyển sang Phương pháp huấn luyện ở Slide 6."* |
| **6** | **Dữ liệu & Phương pháp Học chuyển giao (Transfer Learning)** *(Trả lời Yêu cầu 3)* | • Bộ dữ liệu `datasets/head_v2`: `163` ảnh (`98 train`, `22 val`, `43 test`), tổng `825` nhãn đầu người.<br>• Khởi tạo từ `yolov8n.pt`: Chuyển giao thành công **`352/355` tensor (`99.83%` tham số)** của Backbone & Neck.<br>• Chỉ khởi tạo lại 3 lớp phân loại cuối cho `nc=1 (head)`. | Biểu đồ phân phối kích thước nhãn `labels.jpg` (chỉ gồm biểu đồ cột và scatter plot, không có mặt người). | *"Để 98 ảnh huấn luyện không bị học vẹt, quy trình tăng cường dữ liệu và gán nhãn động diễn ra như thế nào? Xem Slide 7."* |
| **7** | **Tăng cường dữ liệu (`Mosaic`, `close_mosaic`) & Gán nhãn `TAL`** *(Trả lời Yêu cầu 3)* | • **Epoch 1–40**: Bật `mosaic=1.0` (ghép 4 ảnh), `fliplr=0.5`, `scale=0.5`, `hsv_v=0.4`.<br>• **Epoch 41–50 (`close_mosaic=10`)**: Tắt Mosaic để mô hình tinh chỉnh trên ảnh 16:9 nguyên gốc.<br>• **TaskAlignedAssigner (`topk=10, alpha=0.5, beta=6.0`)**: Chọn các neo vừa đoán đúng lớp vừa có `IoU` cao với nhãn thật. | Bảng tham số `args.yaml` thật của lần chạy `head_v2_official`. | *"Sau khi chọn được các ô neo chịu trách nhiệm, mô hình cập nhật trọng số ra sao qua 50 epoch? Chúng ta xem Slide 8."* |
| **8** | **Ba hàm mất mát (`7.5 box + 0.5 cls + 1.5 dfl`), AdamW, EMA & Quá trình hội tụ** *(Trả lời Yêu cầu 3)* | • **Tối ưu hóa**: `auto -> AdamW(lr0=0.002, momentum=0.9)` cho bài toán 1 lớp + `Warmup 3 epochs` + `Cosine LR` + `EMA (decay=0.9999)`.<br>• **Hành trình 50 epochs (`7,477s ~ 2.08 giờ` trên CPU)**:<br>  - Epoch 1: `mAP50 = 0.4408`, `mAP50-95 = 0.1636`.<br>  - **Epoch 35 (Đỉnh `best.pt`)**: `P = 0.902`, `R = 0.759`, `mAP50 = 0.810`, `mAP50-95 = 0.3775`. | Đồ thị 10 biểu đồ `results.png` + `confusion_matrix_normalized.png` từ `runs/detect/head_v2_official/`. | *"Những biểu đồ và báo cáo này được sinh ra bởi bộ công cụ nào của Ultralytics? Chúng ta điểm qua ở Slide 9."* |
| **9** | **Hệ sinh thái công cụ hỗ trợ huấn luyện trong Ultralytics** *(Trả lời Yêu cầu 4)* | • Tự động kiểm tra dữ liệu & tạo `.cache` (`check_det_dataset`).<br>• Tự động sinh `results.csv`, `results.png`, `BoxPR_curve.png`, `confusion_matrix.png`, `train_batch*.jpg`.<br>• Các công cụ nâng cao: `model.val()`, `model.tune()` (vì sao quá nặng trên CPU), `model.export()` (20 định dạng), `model.track()` (`BoT-SORT`/`ByteTrack`).<br>• Cảnh báo bảo mật `yolo settings` (`sync=True`, cloud loggers) với video rạp chiếu phim. | Bảng tổng hợp 10 công cụ trong `ultralytics 8.4.160` và trạng thái sử dụng thực tế trong dự án. | *"Dù đạt mAP50 = 81% trên tập val, mô hình YOLO có những giới hạn nào về mặt thuật toán và thực tế triển khai? Chúng ta phân tích ở Slide 10."* |
| **10** | **Giới hạn của YOLO & Thực nghiệm chứng minh (`tools/yolo_lab.py`)** *(Trả lời Yêu cầu 1)* | • **Giới hạn 1 (Vật thể nhỏ & lệch `imgsz`)**: Ở `imgsz=640`, **58.4%** đầu người `< 12 px`; ở `imgsz=800` chỉ còn **5.9%**. Thực nghiệm B: `imgsz=320` rơi xuống `52/60` đầu, `imgsz=800` đạt `59/60`.<br>• **Giới hạn 2 (Khung trùng NMS ở `iou=0.70`)**: Thực nghiệm D phát hiện 5/22 ảnh `val` bị đếm dư ở `iou=0.70`, biến mất hoàn toàn khi hạ `iou=0.50`.<br>• **Giới hạn 3 (Mờ / Tối)**: Thực nghiệm C cho thấy làm mờ Gaussian làm `mean_conf` tụt từ `0.599 -> 0.423`; giảm sáng 80% làm mất người. | Bảng kết quả số liệu nguyên văn từ `tools/yolo_lab.py` (Thí nghiệm A, B, C, D). | *"Khi ghép đầu ra của YOLO vào bài toán gán ghế cụ thể của CineSight, còn những giới hạn nào về dữ liệu và hình học? Xem Slide 11."* |
| **11** | **Giới hạn đặc thù trong CineSight (Đa giác ghế, Rò rỉ thời gian & Giấy phép)** *(Trả lời Yêu cầu 1)* | • **Độ nhạy gán ghế (Thí nghiệm E)**: Trên 135 đa giác ghế thật (`seats_config_room1.json`), dịch tâm `±6 px` làm đổi kết quả gán ghế ở **19.28%** trường hợp (`±10 px` -> **36.45%**).<br>• **Hạn chế tập dữ liệu**: 163 ảnh từ 1 video duy nhất (`4–6` người/ảnh), khoảng cách `train-val` chỉ `4 giây` -> chưa kiểm chứng khi rạp đông 100 người.<br>• **Giấy phép `AGPL-3.0`**: Hợp lệ cho đồ án học thuật; cần lưu ý nếu thương mại hóa mã nguồn đóng. | Bảng 6 giới hạn chính & giải pháp giảm nhẹ (Mitigation Table mục 5.4b). | *"Từ toàn bộ phân tích và thực nghiệm trên, em xin tổng kết các kết luận và hướng cải tiến tiếp theo ở Slide 12."* |
| **12** | **Kết luận & Lộ trình cải tiến kỹ thuật** | • **Đã hoàn thành**: Quy trình khép kín từ khảo sát video -> trích khung -> gán nhãn bán tự động -> fine-tune `YOLOv8n` (`mAP50 = 0.81`) -> tích hợp FastAPI & ánh xạ 135 ghế.<br>• **Cải tiến tức thời (0 giờ train lại)**: Đặt `imgsz=800, iou=0.45` trong `main.py`; thêm bộ lọc chống nhấp nháy theo thời gian.<br>• **Hướng phát triển**: Xuất `OpenVINO` tăng tốc CPU; thu thập thêm dữ liệu đa phòng chiếu & ca chiếu đông khán giả. | Bảng đối chiếu Trước & Sau khi tinh chỉnh tham số suy luận. | *"Em xin cảm ơn thầy/cô đã lắng nghe và rất mong nhận được câu hỏi từ thầy/cô ạ!"* |

---

## PHẦN 9: BẢNG THUẬT NGỮ (GLOSSARY) & 5 CÂU HỎI TỰ KIỂM TRA

### 9.1. Bảng thuật ngữ 25 khái niệm cốt lõi (Giải thích 1 câu + Liên hệ Web/App Dev)

| STT | Thuật ngữ | Giải thích ngắn gọn trong 1 câu | Phép so sánh cho Frontend / App Developer |
| :--- | :--- | :--- | :--- |
| 1 | **Tensor** | Mảng số nhiều chiều (ví dụ `[batch, channels, height, width]`) lưu trữ ảnh, đặc trưng và đạo hàm trên PyTorch. | Giống `Float32Array` nhiều chiều được tăng tốc phần cứng trong WebGL. |
| 2 | **Backbone** | Phần đầu của mạng CNN làm nhiệm vụ trích xuất đặc trưng hình ảnh từ mức thô (cạnh, nét) đến mức trừu tượng (hình dáng đầu người). | Giống pipeline parser biến chuỗi HTML thô thành cây AST có cấu trúc. |
| 3 | **Neck (`PAN-FPN`)** | Phần giữa của mạng làm nhiệm vụ trộn đặc trưng ngữ nghĩa ở tầng sâu với đặc trưng độ phân giải cao ở tầng nông. | Giống lớp `Context/Redux Selector` kết hợp state toàn cục với props chi tiết của component con. |
| 4 | **Detect Head** | Phần cuối của mạng nhận bản đồ đặc trưng từ Neck để xuất ra tọa độ khung và xác suất lớp. | Giống hàm `render()` cuối cùng xuất dữ liệu ra JSON response cho API. |
| 5 | **Stride (Bước nhảy)** | Tỉ lệ thu nhỏ kích thước không gian của bản đồ đặc trưng so với ảnh đầu vào (ví dụ `stride = 8` nghĩa là 1 ô lưới ứng với `8x8 pixel`). | Giống bước nhảy `step` trong vòng lặp `for (let x = 0; x < width; x += 8)`. |
| 6 | **Anchor-free (Không khung mẫu)** | Cơ chế dự đoán trực tiếp khoảng cách từ tâm mỗi ô lưới tới 4 cạnh vật thể thay vì phải khai báo trước các kích thước khung mẫu cố định. | Giống CSS Flexbox tự co giãn theo nội dung thay vì phải hardcode `width/height` cho từng breakpoint. |
| 7 | **LetterBox** | Kỹ thuật thu phóng ảnh giữ nguyên tỉ lệ khung hình (aspect ratio) và bù phần thiếu bằng viền xám `(114, 114, 114)` để chia hết cho `32`. | Giống thuộc tính `object-fit: contain` kèm `background-color: #727272` trong CSS. |
| 8 | **Logit** | Điểm số thực thô `(-vos_cung, +vo_cung)` do lớp tích chập cuối cùng xuất ra trước khi đi qua hàm chuẩn hóa xác suất. | Giống điểm trọng số thô trước khi quy đổi ra thang phần trăm `0%..100%`. |
| 9 | **Sigmoid** | Hàm toán học `1 / (1 + exp(-x))` nén số thực bất kỳ về khoảng xác suất `(0, 1)`. | Giống hàm `clampAndNormalize()` ép giá trị bất kỳ về thanh trượt opacity `0.0..1.0`. |
| 10 | **Softmax** | Hàm biến một mảng điểm số thành phân phối xác suất mà tổng các phần tử đúng bằng `1.0`. | Giống việc tính tỉ trọng phần trăm của từng danh mục trong biểu đồ tròn (Pie Chart) sao cho tổng bằng 100%. |
| 11 | **DFL (`Distribution Focal Loss`)** | Kỹ thuật dự đoán phân phối xác suất trên `16` nấc khoảng cách (`0..15` ô lưới) cho mỗi cạnh khung để định vị biên vật thể bị mờ chính xác hơn. | Giống việc lấy trung bình có trọng số của các mức bình chọn 1–15 sao thay vì chỉ chọn 1 con số nguyên. |
| 12 | **IoU (`Intersection over Union`)** | Tỉ số giữa diện tích phần giao nhau và diện tích phần hợp nhau của hai khung chữ nhật, nằm trong `[0, 1]`. | Giống độ trùng lặp giữa hai vùng chọn `DOMRect` trên màn hình. |
| 13 | **CIoU (`Complete IoU`)** | Phiên bản nâng cấp của IoU có trừ thêm hình phạt khoảng cách tâm và hình phạt sai lệch tỉ lệ rộng/cao (`aspect ratio`). | Giống việc chấm điểm giao diện không chỉ xét diện tích trùng nhau mà còn xét lệch tâm căn chỉnh và méo tỉ lệ khung. |
| 14 | **NMS (`Non-Maximum Suppression`)** | Thuật toán hậu xử lý giữ lại khung có điểm tự tin cao nhất và xóa các khung lân cận trùng lặp có `IoU` vượt ngưỡng. | Giống hàm `deduplicate()` lọc bỏ các sự kiện click trùng nhau quanh cùng một tọa độ. |
| 15 | **Epoch** | Một lượt mô hình duyệt qua toàn bộ tập dữ liệu huấn luyện (`98` ảnh trong dự án). | Giống một vòng lặp `forEach` chạy hết toàn bộ mảng test cases từ đầu đến cuối. |
| 16 | **Batch size (Kích thước lô)** | Số lượng ảnh được đưa vào mạng tính toán cùng một lúc trước khi cập nhật trọng số một lần (`batch = 8`). | Giống việc gom 8 request vào 1 `Promise.all()` để xử lý theo cụm thay vì chạy từng cái. |
| 17 | **Learning Rate (`lr`)** | Hệ số quyết định bước nhảy lớn hay nhỏ khi cập nhật trọng số theo chiều ngược đạo hàm. | Giống độ nhạy con lăn chuột (scroll speed): quá lớn thì trượt qua mục tiêu, quá nhỏ thì cuộn mãi không tới. |
| 18 | **Transfer Learning (Học chuyển giao)** | Kỹ thuật lấy trọng số đã học trên bộ dữ liệu lớn (`COCO`) làm điểm xuất phát để huấn luyện tiếp trên bài toán mới ít dữ liệu (`head`). | Giống việc kế thừa một thư viện UI Core đã hoàn chỉnh rồi chỉ viết đè (override) theme cho dự án riêng. |
| 19 | **Mosaic Augmentation** | Kỹ thuật ghép ngẫu nhiên 4 ảnh huấn luyện thành 1 ảnh lưới 2x2 để tăng tính đa dạng bối cảnh và tỷ lệ vật thể. | Giống việc ghép 4 ảnh nhỏ vào 1 CSS Grid 2x2 ngẫu nhiên để kiểm thử khả năng hiển thị ở nhiều bố cục. |
| 20 | **TAL (`TaskAlignedAssigner`)** | Thuật toán chọn động tối đa `topk=10` ô neo tốt nhất cho mỗi nhãn thật dựa trên điểm kết hợp giữa xác suất lớp và `IoU`. | Giống thuật toán giao việc tự động cho 10 nhân sự có điểm kỹ năng và vị trí phù hợp nhất trong mỗi sprint. |
| 21 | **EMA (`Exponential Moving Average`)** | Bản sao mô hình lưu trung bình trượt mũ của trọng số qua mọi bước cập nhật để làm mượt nhiễu và dùng làm mô hình xuất cuối cùng. | Giống đường trung bình trượt 30 ngày trên biểu đồ chứng khoán giúp lọc bỏ các cú giật giá ngắn hạn. |
| 22 | **Precision (Độ chuẩn xác)** | Tỉ lệ phần trăm khung máy đoán là đúng trên tổng số khung máy đã vẽ ra (`TP / (TP + FP)`). | Giống tỉ lệ thông báo đẩy (push notification) thực sự hữu ích trên tổng số thông báo app đã bắn ra. |
| 23 | **Recall (Độ phủ / Độ nhạy)** | Tỉ lệ phần trăm đầu người thật trong rạp được máy tìm thấy (`TP / (TP + FN)`). | Giống tỉ lệ lỗi thật được bộ Unit Test bắt trúng trên tổng số lỗi đang tồn tại trong code. |
| 24 | **mAP50 & mAP50-95** | Diện tích dưới đường cong Precision-Recall tính ở ngưỡng `IoU = 0.50` (`mAP50`) hoặc trung bình trên 10 ngưỡng `0.50..0.95` (`mAP50-95`). | Giống điểm tổng kết Benchmark đánh giá toàn diện cả độ chính xác lẫn độ bao phủ của hệ thống. |
| 25 | **Overfitting (Học vẹt / Quá khớp)** | Hiện tượng mô hình giảm lỗi rất sâu trên tập `train` nhưng lỗi trên tập `val` lại tăng lên vì chỉ nhớ thuộc lòng chi tiết nhiễu của ảnh mẫu. | Giống việc viết `if (input === 'test1') return 42` để pass 100% unit test ở máy local nhưng chạy sai hoàn toàn với dữ liệu thật của người dùng. |

---

### 9.2. Năm câu hỏi tự kiểm tra (Không nhìn đáp án trước)

1. **Câu hỏi 1**: Trên ảnh gốc `1920x1080` của rạp chiếu phim CineSight, một cái đầu người có chiều cao trung vị là `35 pixel`. Khi đưa vào `main.py` (đang dùng mặc định `imgsz=640`) so với khi huấn luyện (`imgsz=800`), chiều cao cái đầu đó biến thành bao nhiêu pixel và nó được phát hiện chủ yếu bởi tầng nào (`P3`, `P4`, hay `P5`)? Vì sao?
2. **Câu hỏi 2**: Trong tệp `args.yaml` của lần chạy `head_v2_official`, tại sao người lập trình đặt `optimizer: auto` với `lr0: 0.01`, nhưng trong log huấn luyện thực tế mô hình lại dùng bộ tối ưu `AdamW` với `lr = 0.002`? Con số `0.002` được tính từ công thức nào trong mã nguồn Ultralytics?
3. **Câu hỏi 3**: Giả sử trên một bức ảnh kiểm định, có 10 người đang ngồi xem phim. Mô hình YOLO vẽ ra 9 khung chữ nhật, trong đó có 8 khung trúng 8 người ngồi thật và 1 khung vẽ nhầm vào chiếc ba lô đặt trên ghế trống (tức là còn 2 người thật bị bỏ sót). Hãy tính `TP`, `FP`, `FN`, `Precision`, `Recall`, và `F1-score`.
4. **Câu hỏi 4**: Tại sao trong `runs/detect/head_v2_official/`, các ảnh `train_batch0.jpg` (Epoch 1) lại có kích thước vuông `1600x1600` gồm 4 khung hình ghép lại trong mỗi ô, còn `train_batch1000.jpg` (Epoch 41) lại có kích thước chữ nhật `1600x960` gồm các khung hình 16:9 nguyên vẹn? Cơ chế này tên là gì và giải quyết vấn đề gì?
5. **Câu hỏi 5**: Ở Thí nghiệm D (`tools/yolo_lab.py`), trên ảnh `room1_cam_edited_0374s.jpg` (có 6 người thật), tại sao khi để `iou=0.70` mô hình lại trả về 7 khung, nhưng khi chỉnh `iou=0.50` (giữ nguyên `conf=0.25`) thì mô hình trả về đúng 5–6 khung không trùng lặp? Ngưỡng `iou` trong hàm `model(frame, conf=..., iou=...)` đóng vai trò gì?

---

### 9.3. Đáp án & Giải thích chi tiết cho 5 câu hỏi tự kiểm tra

1. **Đáp án Câu 1**:
   - Ở `imgsz=800`: tỉ lệ thu phóng là `800 / 1920 = 0.4167`, nên chiều cao đầu `35 px` còn `35 * 0.4167 = 14.58 px` [DỰ ÁN].
   - Ở `imgsz=640` (`main.py`): tỉ lệ thu phóng là `640 / 1920 = 0.3333`, nên chiều cao đầu `35 px` chỉ còn `35 * 0.3333 = 11.67 px` (làm 58.42% số đầu trong bộ dữ liệu tụt xuống `< 12 px`) [DỰ ÁN].
   - Nó được phát hiện chủ yếu bởi tầng **`P3 (stride = 8)`** vì mỗi ô lưới `P3` rộng `8x8 px` (vừa khít với vật thể `11..15 px`), trong khi ô lưới `P4 (stride = 16)` và `P5 (stride = 32)` lớn hơn cả cái đầu người nên đặc trưng bị hòa lẫn vào nền [MÃ NGUỒN] [DỰ ÁN].
2. **Đáp án Câu 2**:
   - Khi `optimizer='auto'`, hàm `BaseTrainer.build_optimizer()` trong `ultralytics/engine/trainer.py:1007-1020` kiểm tra số vòng lặp ước tính `iterations`. Vì `iterations` nhỏ hơn `10,000`, nó tự động chọn `AdamW` thay vì `SGD`, đồng thời bỏ qua `lr0=0.01` để tính tự động theo công thức:
     ```text
     lr_auto = round(0.002 * 5 / (4 + nc), 6)
     ```
   - Với `nc = 1` (1 lớp `head`), `lr_auto = 0.002 * 5 / (4 + 1) = 0.002` [MÃ NGUỒN] [DỰ ÁN].
3. **Đáp án Câu 3**:
   - `TP = 8` (8 người thật được đoán đúng).
   - `FP = 1` (1 chiếc ba lô bị đoán nhầm là đầu người).
   - `FN = 2` (`10 - 8 = 2` người thật bị bỏ sót).
   - `Precision = TP / (TP + FP) = 8 / (8 + 1) = 8 / 9 = 0.8889 (88.89%)`.
   - `Recall = TP / (TP + FN) = 8 / (8 + 2) = 8 / 10 = 0.8000 (80.00%)`.
   - `F1 = 2 * P * R / (P + R) = 2 * 0.8889 * 0.8000 / (0.8889 + 0.8000) = 0.8421 (84.21%)` [MÃ NGUỒN].
4. **Đáp án Câu 4**:
   - Cơ chế đó là **`close_mosaic=10`** kết hợp với **`mosaic=1.0`** [`args.yaml`, `trainer.py:477-479`] [MÃ NGUỒN] [DỰ ÁN].
   - Ở Epoch 1–40 (`train_batch0.jpg`), `Mosaic` đang bật nên DataLoader luôn ép mỗi mẫu thành hình vuông `800x800` bằng cách ghép 4 ảnh (lưới 2x2 ảnh sẽ thành `1600x1600`) để tăng sự đa dạng vị trí [MÃ NGUỒN].
   - Từ Epoch 41 (`50 - 10 + 1`, ứng với batch 1000), ` _close_dataloader_mosaic()` tắt ghép 4 ảnh, trả về ảnh đơn 16:9 qua `LetterBox` có kích thước `800x480` (lưới 2x2 ảnh thành `1600x960`). Việc này giúp mô hình tinh chỉnh lại trọng số trên đúng phân phối ảnh thực tế không có đường cắt ghép giả tạo ở 10 epoch cuối [MÃ NGUỒN] [DỰ ÁN].
5. **Đáp án Câu 5**:
   - Ngưỡng `iou` trong `model(frame, conf=0.25, iou=...)` là ngưỡng **Non-Maximum Suppression (NMS)** [`nms.py:66-127`] [MÃ NGUỒN].
   - Trên ảnh `0374s.jpg`, hai ô neo lân cận cùng dự đoán 1 cái đầu người và sinh ra 2 khung chữ nhật lệch nhau vài pixel có độ chồng lấp `IoU = 0.6919` và `0.6861` [DỰ ÁN].
   - Khi để `iou=0.70` mặc định, vì `0.6919 <= 0.70`, thuật toán NMS tưởng đây là 2 người khác nhau nên giữ lại cả hai khung (gây đếm dư thành 7). Khi hạ ngưỡng xuống `iou=0.50`, mọi khung cùng lớp chồng lấp `> 0.50` với khung có `conf` cao hơn đều bị xóa bỏ, khử sạch khung trùng [MÃ NGUỒN] [DỰ ÁN].

---

## PHỤ LỤC: MÃ KIỂM CHỨNG, DANH SÁCH TỆP ĐÃ ĐỌC, TÀI LIỆU THAM KHẢO TỪ MÃ NGUỒN & MỤC CHƯA KIỂM CHỨNG

### A.1. Danh sách đầy đủ các tệp trong `site-packages\ultralytics` và dự án đã đọc trực tiếp

1. **Trong `c:\CineSightApp\ai_service\venv\Lib\site-packages\ultralytics\`** [MÃ NGUỒN] [TÀI LIỆU]:
   - `ultralytics/__init__.py` (phiên bản `8.4.160`, các lớp export).
   - `ultralytics/cfg/__init__.py` (`MODES`, `TASKS`, CLI subcommands).
   - `ultralytics/cfg/default.yaml` (toàn bộ 140 dòng siêu tham số mặc định).
   - `ultralytics/cfg/models/v8/yolov8.yaml` (kiến trúc Backbone, Neck, Detect head và bảng `scales: n/s/m/l/x`).
   - `ultralytics/nn/modules/conv.py` (`Conv`, `autopad`, `BatchNorm2d`, `SiLU`, `fuse_conv_and_bn`).
   - `ultralytics/nn/modules/block.py` (`DFL`, `C2f`, `Bottleneck`, `SPPF`).
   - `ultralytics/nn/modules/head.py` (`Detect`, `cv2`, `cv3`, `_inference`, `decode_bboxes`, `bias_init`).
   - `ultralytics/nn/tasks.py` (`DetectionModel`, `BaseModel`, `parse_model`, `load` transfer learning).
   - `ultralytics/utils/loss.py` (`v8DetectionLoss`, `BboxLoss`, `DFLoss`, `bbox_decode`).
   - `ultralytics/utils/tal.py` (`TaskAlignedAssigner`, `make_anchors`, `dist2bbox`, `bbox2dist`).
   - `ultralytics/utils/metrics.py` (`bbox_iou`, `box_iou`, `ConfusionMatrix`, `ap_per_class`, `compute_ap`, `DetMetrics`, `Metric`).
   - `ultralytics/utils/nms.py` (`TorchNMS.fast_nms`, `non_max_suppression`).
   - `ultralytics/utils/torch_utils.py` (`ModelEMA`, `EarlyStopping`, `model_info`).
   - `ultralytics/utils/__init__.py` (`SETTINGS`, `SettingsManager`).
   - `ultralytics/utils/events.py` (`Events` telemetry Google Analytics).
   - `ultralytics/utils/callbacks/base.py`, `platform.py`, `clearml.py`, `comet.py`, `wb.py`.
   - `ultralytics/data/augment.py` (`LetterBox`, `Mosaic`, `RandomPerspective`, `RandomHSV`, `RandomFlip`, `v8_transforms`).
   - `ultralytics/data/dataset.py` (`YOLODataset`, `build_transforms`).
   - `ultralytics/data/annotator.py` (`auto_annotate`).
   - `ultralytics/engine/trainer.py` (`BaseTrainer`, `build_optimizer`, `_setup_scheduler`, `_setup_train`, `train`, `_do_train`, `_close_dataloader_mosaic`, `save_model`).
   - `ultralytics/engine/validator.py` (`BaseValidator`) & `ultralytics/models/yolo/detect/val.py` (`DetectionValidator`).
   - `ultralytics/engine/exporter.py` (`export_formats`, `Exporter`).
   - `ultralytics/engine/tuner.py` (`Tuner`).
   - `ultralytics-8.4.160.dist-info/METADATA` (thông tin gói và giấy phép `AGPL-3.0`).
2. **Trong dự án `c:\CineSightApp\`** [DỰ ÁN]:
   - `ai_service/main.py` (API FastAPI và hàm `detect_people_from_frame` dòng `209-256`).
   - `ai_service/seat_mapper.py` (ánh xạ tọa độ đầu sang đa giác ghế dòng `1-95`).
   - `ai_service/seats_configs/seats_config_room1.json` (`135` đa giác ghế Phòng 1).
   - `ai_service/tools/train_head_v2.py` (kịch bản huấn luyện chính thức dòng `1-99`).
   - `ai_service/datasets/head_v2/head_v2.yaml` & toàn bộ `163` tệp nhãn `.txt` trong `datasets/head_v2/labels/{train,val,test}/`.
   - `ai_service/runs/detect/head_v2_official/args.yaml`, `results.csv`, `results.png`, `labels.jpg`, `confusion_matrix*.png`, `Box*_curve.png`, `train_batch*.jpg`, `val_batch*.jpg`, `weights/best.pt`, `weights/last.pt`.
   - `ai_service/best_head_v2.pt` & `ai_service/yolov8n.pt`.

---

### A.2. Danh sách Tài liệu tham khảo / Bài báo khoa học trích xuất nguyên văn từ chú thích mã nguồn `ultralytics 8.4.160`
*(Tuân thủ Quy tắc 6: chỉ liệt kê những bài báo và URL có xuất hiện thật trong chú thích/docstring của mã nguồn `ultralytics` đã cài; các khái niệm không có link bài báo trong docstring được ghi rõ `"tự tra nguồn"`)*

1. **Distribution Focal Loss (DFL) & Generalized Focal Loss**:
   - Trích từ docstring `ultralytics/nn/modules/block.py:67` và `ultralytics/utils/loss.py:13` [MÃ NGUỒN]:
     - URL trong mã nguồn: `https://ieeexplore.ieee.org/document/9792391`
2. **CIoU / DIoU / GIoU (`bbox_iou`)**:
   - Trích từ docstring `ultralytics/utils/metrics.py:114-116` [MÃ NGUỒN]:
     - CIoU / DIoU arXiv URL trong mã nguồn: `https://arxiv.org/abs/1911.08287v1`
     - GIoU arXiv URL trong mã nguồn: `https://arxiv.org/pdf/1902.09630.pdf`
3. **Task-Aligned Assigner (`TAL` – TOOD)**:
   - Trích từ docstring `ultralytics/utils/tal.py:21-22` [MÃ NGUỒN]:
     - Bài báo dẫn trong docstring: *Task-Aligned One-Stage Object Detection (TOOD)*: `https://arxiv.org/abs/2108.07755`
     - Mã tham chiếu dẫn trong docstring: `https://github.com/fcjian/TOOD/blob/master/mmdet/core/bbox/assigners/task_aligned_assigner.py`
4. **Tính diện tích dưới đường cong PR (`ap_per_class`, `compute_ap`)**:
   - Trích từ chú thích `ultralytics/utils/metrics.py:766` [MÃ NGUỒN]:
     - Nguồn dẫn trong mã nguồn: `https://github.com/rafaelpadilla/Object-Detection-Metrics`
5. **Tài liệu chính thức Ultralytics & Giấy phép**:
   - Trích từ `ultralytics-8.4.160.dist-info/METADATA:18, 22, 410-411` và header các tệp `.py` [TÀI LIỆU] [MÃ NGUỒN]:
     - Docs: `https://docs.ultralytics.com`
     - Repository: `https://github.com/ultralytics/ultralytics`
     - License: `https://ultralytics.com/license` (`AGPL-3.0`)
6. **Các khái niệm không ghi tên bài báo gốc trong chú thích các tệp trên (ghi `"tự tra nguồn"` theo Quy tắc 6)**:
   - Bài báo gốc YOLOv1 (2016), CSPNet / C2f, PANet / FPN, AdamW optimizer, Mosaic augmentation (YOLOv4): *tự tra nguồn* (trong mã nguồn `ultralytics 8.4.160` chỉ cài đặt trực tiếp thuật toán mà không đính kèm link arXiv của các bài báo này).

---

### A.3. Mục "CHƯA KIỂM CHỨNG ĐƯỢC" (Trung thực theo Quy tắc 4 & Quy tắc 9)

1. **Hiệu năng của `best_head_v2.pt` trên Phòng chiếu 2, 3, 4 và trong ca chiếu đông khán giả (`> 20` người)**:
   - **Trạng thái**: **KHÔNG BIẾT / CHƯA KIỂM CHỨNG**.
   - **Lý do**: Trong toàn bộ thư mục dự án chỉ có duy nhất 1 video `room1_cam_edited.mp4` (Phòng 1, tối đa 6 người ngồi). Chưa có bất kỳ video hay ảnh thực tế nào từ Phòng 2, 3, 4 hoặc từ ca chiếu đông khách để chạy `model.val()`.
2. **Độ trễ thực tế sau khi xuất sang `OpenVINO` hoặc `ONNX Runtime` trên máy này**:
   - **Trạng thái**: **CHƯA KIỂM CHỨNG TRONG LƯỢT NÀY**.
   - **Lý do**: Theo Quy tắc 1 & 7, chúng ta không cài đặt thêm gói mới (`pip install openvino onnxruntime`) vào `ai_service\venv`. Chỉ mới xác nhận các gói này hiện `NOT INSTALLED` trong `venv`.
3. **Số liệu `mAP` chuẩn của `yolov8n.pt` trên bộ dữ liệu COCO 2017 val**:
   - **Trạng thái**: **CHƯA KIỂM CHỨNG TRỰC TIẾP** (trong `yolov8.yaml` chỉ ghi số lớp, số tham số `3157200` và `8.9 GFLOPs`, không ghi con số `mAP` trên COCO; máy không tải bộ COCO 5000 ảnh về chạy lại).

---

### A.4. Kiểm tra các gói xuất mô hình (`export`) và xác nhận dọn dẹp thư mục tạm `reports\yolo_study_tmp\`

Đoạn mã kiểm tra trạng thái gói xuất mô hình và xác nhận xóa thư mục tạm `c:\CineSightApp\ai_service\reports\yolo_study_tmp\` theo đúng Quy tắc 7 [DỰ ÁN]:
```python
import importlib.util
from pathlib import Path

for pkg in ["torch", "onnx", "onnxruntime", "onnxslim", "openvino", "tensorrt", "coremltools", "tflite_runtime"]:
    spec = importlib.util.find_spec(pkg)
    print(f"{pkg}: {'INSTALLED' if spec is not None else 'NOT INSTALLED'}")

tmp_dir = Path(r"c:\CineSightApp\ai_service\reports\yolo_study_tmp")
print("reports/yolo_study_tmp exists:", tmp_dir.exists())
```
Output nguyên văn [DỰ ÁN]:
```text
torch: INSTALLED (2.14.0+cpu)
onnx: NOT INSTALLED
onnxruntime: NOT INSTALLED
onnxslim: NOT INSTALLED
openvino: NOT INSTALLED
tensorrt: NOT INSTALLED
coremltools: NOT INSTALLED
tflite_runtime: NOT INSTALLED
reports/yolo_study_tmp exists: False
```
- **Xác nhận tuân thủ Quy tắc 3 & 7**: Thư mục tạm `c:\CineSightApp\ai_service\reports\yolo_study_tmp\` dùng khi chạy `model.val()` đã được xóa hoàn toàn (`exists: False`), không có bất kỳ ảnh khuôn mặt khán giả nào được đưa vào tài liệu hoặc để lại ngoài thư mục tạm, và không có bất kỳ tệp dữ liệu hay mã nguồn sẵn có nào của dự án bị sửa đổi [DỰ ÁN].

