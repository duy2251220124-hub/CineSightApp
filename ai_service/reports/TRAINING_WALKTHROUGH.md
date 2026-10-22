# GIẢI THÍCH TOÀN DIỆN & KIỂM TOÁN TRUNG THỰC QUÁ TRÌNH HUẤN LUYỆN MÔ HÌNH NHẬN DIỆN ĐẦU NGƯỜI (`best_head_v2.pt`)

> **Quy ước phân loại thông tin trong báo cáo này:**
> - **[ĐÃ XÁC MINH]**: Có bằng chứng trực tiếp từ tệp mã nguồn, cấu hình YAML/CSV/JSON, thời gian tệp (`LastWriteTime`), hoặc kết quả chạy lệnh thực tế.
> - **[SUY LUẬN]**: Kết luận hợp lý suy ra từ bằng chứng kỹ thuật (nêu rõ căn cứ).
> - **[KHÔNG BIẾT / KHÔNG TÌM THẤY]**: Không có log hoặc tệp lưu lại trên ổ đĩa; tuyệt đối không đoán hoặc tự điền.

---

## TÓM TẮT 1 TRANG (10 DÒNG CỐT LÕI)

1. **[Đã làm gì - Dữ liệu]**: Từ 1 video hồng ngoại duy nhất `C:\Users\Dell KIM ANH\Downloads\cam_edited.mp4` ($1920\times 1080$, $30\text{ FPS}$, dài $577,9\text{s}$), script `tools/extract_frames.py` trích xuất **163 khung hình** (bước nhảy $3,5\text{s}$, ngưỡng lọc trùng $\text{diff} < 1,5$) và chia theo 4 phân đoạn thời gian thành **98 ảnh Train (570 đầu), 22 ảnh Val (87 đầu), 43 ảnh Test (168 đầu)** — tổng cộng **825 khung đầu**.
2. **[Đã làm gì - Gán nhãn Bán tự động]**: 40 ảnh Giai đoạn A (`32 train + 8 val` trong `datasets/head_v2/stage_a_list.txt`) được gán nhãn tay hoàn toàn để huấn luyện mô hình nháp `models/baseline_stage_a.pt`; mô hình nháp này tự động gán nhãn gợi ý cho 123 ảnh còn lại (`labels_prelabel/`), sau đó người dùng mở `tools/label_heads_cv.py` duyệt qua cả 123 ảnh (chỉnh sửa tọa độ/số khung ở **73 ảnh**, bấm xác nhận giữ nguyên ở **50 ảnh**).
3. **[Đã làm gì - Huấn luyện]**: Mô hình chính thức được huấn luyện từ trọng số gốc `yolov8n.pt` (không dùng `best_v1.pt` và không trộn `coco128`) bằng script `tools/train_official.py` với `epochs=50`, `imgsz=800`, `batch=4`, `device=cpu`, mất **7.477,41 giây (~124,62 phút)**, đạt đỉnh fitness tại **Epoch 35/50** và xuất ra `models/best_head_v2.pt`.
4. **[Mô hình nào đang dùng]**: Backend FastAPI (`ai_service/main.py:420-425` và `main.py:92`) đang nạp trực tiếp `c:\CineSightApp\ai_service\models\best_head_v2.pt` với cấu hình mặc định `MODEL_CONF = 0.25`, `MODEL_IMGSZ = 800`, `classes = [0]` (`head`), và ngưỡng NMS mặc định của Ultralytics là `iou = 0.70`.
5. **[Số đo nào ĐÁNG TIN - Phần 1]**: Sự cải thiện vượt bậc so với mô hình cũ trên cùng góc máy `room1`: trên 43 ảnh `test` ở `conf=0.25`, `yolov8n.pt` gốc (lớp `person`) và `best_v1.pt` (huấn luyện trên `coco128`) đều thất bại nặng với sai số đếm trung bình **$\text{MAE} = 3,91\text{ người/ảnh}$** (đếm thiếu gần như toàn bộ khán giả vì chỉ nhìn thấy chỏm đầu trong bóng tối), trong khi `best_head_v2.pt` giảm $\text{MAE}$ xuống **$0,65\text{ người/ảnh}$** (ở `iou=0.70`) và **$0,44\text{ người/ảnh}$** (ở `iou=0.60`).
6. **[Số đo nào ĐÁNG TIN - Phần 2]**: Quy trình kỹ thuật từ trích xuất khung hình, kiểm tra định dạng nhãn (163/163 tệp hợp lệ, 0 khung trùng $\text{IoU}>0,9$), huấn luyện hội tụ hàm mất mát (`train/box_loss` giảm từ $2,119 \to 1,182$; `val/box_loss` giảm từ $2,000 \to 1,430$) đến tích hợp API (`POST /api/v1/analyze`) đều hoạt động thật 100% và tái lập được bằng lệnh.
7. **[Số đo nào KHÔNG ĐÁNG TIN làm "độ chính xác thực tế" - Rò rỉ cảnh & khách]**: Con số **`mAP@50 = 80,98%` (Val)** và **`MAE = 0,88` hay `0,44 người/ảnh` (Test)** KHÔNG đại diện cho độ chính xác tổng quát ngoài thực tế vì cả 3 tập `train/val/test` đều cắt ra từ **cùng 1 video dài 9 phút 38 giây**, cùng 1 phòng (`room1`), cùng 1 góc camera, và xoay quanh **cùng một nhóm chỉ từ 0 đến tối đa 6 khán giả**; khoảng cách thời gian giữa ảnh cuối tập `train` ($343,5\text{s}$) và ảnh đầu tập `val` ($346,0\text{s}$) chỉ là **2,5 giây**, và giữa ảnh cuối tập `val` ($419,5\text{s}$) với ảnh đầu tập `test` ($425,0\text{s}$) chỉ là **5,5 giây**.
8. **[Số đo nào KHÔNG ĐÁNG TIN - Lệch cấu hình & Chọn ngưỡng trên Test]**: Trong `tools/eval_counts.py:63,152`, ngưỡng chọn tự động từ tập `val` là `conf = 0.15` với `iou = 0.60` (cho Test $\text{MAE} = 0,88$), nhưng khi đưa vào `main.py:422` lại đổi sang `MODEL_CONF = 0.25` (dựa trên bảng khảo sát tập `test` tại `reports/TRAINING_REPORT.md:100-106` — tức là đã nhìn tập `test` để chốt `conf=0.25`) và quên truyền `iou=0.60` vào `main.py:92` (khiến API chạy ở `iou=0.70` mặc định, làm Test $\text{MAE}$ thực tế của API ở `conf=0.25` là **$0,65$** chứ không phải $0,44$).
9. **[Số đo nào KHÔNG ĐÁNG TIN - Bản đồ ghế]**: Sơ đồ 135 ghế (`seats_configs/seats_config_room1..4.json`) được dựng nội suy hình học bằng script `tools/setup_rooms_and_schedule.py:43-126` từ 1 ảnh chụp màn hình $1024\times 899$ rồi phóng tuyến tính sang $1920\times 1080$ và nhân bản y hệt cho cả 4 phòng (`room1..room4`), chưa được chấm từng ghế trực tiếp trên khung hình gốc $1920\times 1080$ của từng phòng.
10. **[Kết luận cốt lõi]**: Bạn đã có một **pipeline kỹ thuật hoàn chỉnh, chạy thật từ đầu đến cuối** và chứng minh được phương pháp phát hiện đầu người (`head` ở `imgsz=800`) giải quyết được bài toán camera hồng ngoại rạp phim mà YOLO gốc thất bại; nhưng về mặt khoa học dữ liệu, đây mới là **Proof-of-Concept trên 1 phiên quay đơn lẻ (tối đa 6 khách)**, cần kiểm định thêm trên ít nhất 1 video khác ngày/khác suất và đồng bộ `iou=0.60` vào `main.py`.

---

## PHẦN 1: DÒNG THỜI GIAN & ĐỐI CHIẾU KẾ HOẠCH 10 PHASE

> **Góc nhìn Frontend Dev**: Hãy hình dung việc dựng lại dòng thời gian này giống như bạn đọc **Git Commit History + Build Artifacts + Webpack Bundle Timestamps** để biết chính xác bản build đang chạy trên production được biên dịch lúc mấy giờ, từ những file source nào, và có bước nào trong CI/CD pipeline bị sửa tay hay chạy tắt không.

### 1.1. Dòng thời gian thực tế (Dựng từ `CreationTime`, `LastWriteTime`, `git log`, `results.csv`)

Toàn bộ lịch sử dự án chia làm **2 đợt tách biệt**: Đợt 0 (chạy thử nghiệm giả lập từ ngày 04/10/2026) và Đợt Chính thức (huấn luyện thật từ video camera rạp ngày 13/10/2026 và tích hợp ngày 17/10/2026).

| Thứ tự | Mốc thời gian thực tế | Sự kiện & Hành động kỹ thuật | Bằng chứng xác minh (`filepath:line` / timestamp) | Phân loại |
| :---: | :--- | :--- | :--- | :---: |
| **0** | `04/10/2026 19:33:16 – 19:47:13` | **Chạy bản nháp cũ (`v1`) trên bộ dữ liệu mẫu `coco128`**: Tải `yolov8n.pt` (`19:33:16`) và `coco128.zip` (`19:35:25`), chạy `train_v1.py` (10 epochs, `imgsz=320`) xuất ra `best_v1.pt` (`19:45:48`, copy lúc `19:47:13`) và `train_log.txt` (`19:47:13`). Đây là mô hình học 80 lớp đồ vật tổng quát của COCO128, không phải đầu người rạp phim. | `ai_service/train_v1.py:20-45`, `ai_service/train_log.txt`, `LastWriteTime` của `best_v1.pt` (`10/4/2026 7:45:48 PM`). | **[ĐÃ XÁC MINH]** |
| **1** | `13/10/2026 16:04:16 – 16:06:45` | **Phase 1 — Khảo sát video gốc `cam_edited.mp4`**: Tạo thư mục `ai_service/reports` (`16:04:16`), đo biến thiên độ sáng toàn video xuất ra `reports/brightness_profile.png` (`16:06:38`) và lưới 24 ảnh đại diện `reports/contact_sheet_cam_edited.jpg` (`16:06:45`). | `LastWriteTime` của `reports/brightness_profile.png` (`10/13/2026 4:06:38 PM`) và `reports/contact_sheet_cam_edited.jpg` (`4:06:45 PM`). | **[ĐÃ XÁC MINH]** |
| **2** | `13/10/2026 16:16:27 – 16:20:59` | **Phase 2 — Dọn dữ liệu cũ & Trích xuất 163 khung hình**: Di chuyển dữ liệu/runs cũ vào `datasets_archive/` (`16:16:27`) và `runs_archive/` (`16:16:27`). Viết và chạy `tools/extract_frames.py` (`16:18:27 – 16:20:46`), trích 163 ảnh vào `datasets/head_v2/images/{train,val,test}`, tạo `manifest.csv` (lần đầu), `stage_a_list.txt` (`16:20:57`), `dataset_head_v2.yaml` (`16:20:58`), và `reports/sampled_frames_contact_sheet.jpg` (`16:20:59`). | `tools/extract_frames.py:1-250`, `LastWriteTime` của `datasets/head_v2/stage_a_list.txt` (`16:20:57`) và `dataset_head_v2.yaml` (`16:20:58`). | **[ĐÃ XÁC MINH]** |
| **3** | `13/10/2026 16:28:40 – 18:30:38` | **Phase 3 & 4 — Quy ước nhãn, Công cụ gán nhãn & Gán tay Giai đoạn A (40 ảnh)**: Soạn `reports/LABELING_GUIDE.md` (`16:28:40 – 16:31:27`), viết công cụ GUI OpenCV `tools/label_heads_cv.py` (`16:29:45`). Người dùng trực tiếp vẽ khung đầu bằng chuột trên 40 ảnh Giai đoạn A (`32 train + 8 val`); tệp nhãn đầu tiên trong `datasets/head_v2/labels/` được lưu lúc `18:05:20` (ảnh cuối lưu lúc `18:30:38`). | `reports/LABELING_GUIDE.md:1-47`, `tools/label_heads_cv.py:1-239`, `min(mtime)` của `datasets/head_v2/labels/` = `2026-10-13 18:05:20.667876`. | **[ĐÃ XÁC MINH]** |
| **4** | `13/10/2026 18:33:37 – 18:51:20` | **Kiểm tra QC Giai đoạn A & Tạo cấu hình Stage A**: Viết `tools/dataset_stats.py` (`18:33:37`), tạo thư mục `reports/qc_overlays` (`18:33:50`), tạo danh sách `train_stage_a.txt` (32 ảnh), `val_stage_a.txt` (8 ảnh) và `dataset_stage_a.yaml` (`18:51:20`). | `ai_service/dataset_stage_a.yaml:1-8` (`LastWriteTime: 10/13/2026 6:51:20 PM`). | **[ĐÃ XÁC MINH]** |
| **5** | `13/10/2026 19:01:28 – 20:14:58` | **Phase 5 — Huấn luyện Baseline Stage A & Tự động gán nháp 123 ảnh còn lại**: Viết `tools/train_baseline.py` (`19:01:28 – 19:03:27`), bắt đầu huấn luyện `runs/detect/baseline_stage_a` lúc `19:03:13`, kết thúc lúc `20:14:33` (tổng thời gian đồng hồ `4269,82s = 71,16 phút` do máy bị ngắt quãng/sleep `2373,89s` giữa epoch 44 và 45). Lưu `models/baseline_stage_a.pt` (`20:14:28`), chạy dự đoán tự động (`conf=0.25, imgsz=800`) sinh 123 tệp nhãn nháp vào `datasets/head_v2/labels_prelabel/` (`20:14:38 – 20:14:58`) và `reports/prelabels_metadata.json` (`20:14:58`). | `runs/detect/baseline_stage_a/results.csv:45-51`, `models/baseline_stage_a.pt` (`20:14:28`), `reports/prelabels_metadata.json` (`20:14:58`). | **[ĐÃ XÁC MINH]** |
| **6** | `13/10/2026 20:20:32 – 20:58:14` | **Phase 6 — Người dùng duyệt/sửa 123 ảnh Giai đoạn B & Chạy QC toàn tập**: Người dùng mở `label_heads_cv.py --mode unverified` duyệt toàn bộ 123 ảnh còn lại, lưu tệp cuối cùng trong `datasets/head_v2/labels/` lúc `20:42:46`. Sau đó lúc `20:55:06 – 20:58:14`, chạy lại `tools/dataset_stats.py` để kiểm tra 163/163 nhãn, xuất 30 ảnh vào `reports/qc_overlays/` (`20:55:06`) và cập nhật `datasets/head_v2/manifest.csv` (`20:55:06`). | `max(mtime)` của `labels/` = `2026-10-13 20:42:46.446012`; `LastWriteTime` của `manifest.csv` và `reports/qc_overlays` = `20:55:06`. | **[ĐÃ XÁC MINH]** |
| **7** | `13/10/2026 20:57:04 – 23:02:59` | **Phase 7 — Huấn luyện Mô hình Chính thức (`head_v2_official`)**: Viết `tools/train_official.py` (`20:57:04 – 20:58:12`), bắt đầu huấn luyện 50 epochs trên 98 ảnh `train` / 22 ảnh `val` ở `imgsz=800` lúc `20:57:50`, kết thúc lúc `23:02:44` (`7477,41s = 124,62 phút`). Sao chép `weights/best.pt` (tốt nhất ở Epoch 35) sang `models/best_head_v2.pt` (`23:02:32`), chạy `model.val()` lưu vào `runs/detect/val-2` (`23:02:46 – 23:02:59`) và ghi `reports/official_training_summary.txt` (`23:02:59`). | `runs/detect/head_v2_official/results.csv:2-51`, `models/best_head_v2.pt` (`23:02:32`), `reports/official_training_summary.txt` (`23:02:59`). | **[ĐÃ XÁC MINH]** |
| **8** | `13/10/2026 23:09:47 – 23:15:34` | **Phase 8 — Đánh giá sai số đếm trên tập Test & Tạm nghỉ**: Viết và chạy `tools/eval_counts.py` (`23:09:47 – 23:10:15`), xuất 19 ảnh ca lỗi vào `reports/failure_cases/` và tạo `reports/EVAL_REPORT_PHASE8.md` (`23:10:17`). Lập kế hoạch `reports/TOMORROW_PLAN.md` (`23:15:34`) và tạm dừng. | `tools/eval_counts.py:1-319`, `reports/EVAL_REPORT_PHASE8.md` (`23:10:17`), `reports/TOMORROW_PLAN.md` (`23:15:34`). | **[ĐÃ XÁC MINH]** |
| **9** | `17/10/2026 11:41:29 – 11:48:02` | **Phase 9b & 10 — Tích hợp vào `main.py`, Kiểm thử hồi quy & Ẩn danh ảnh báo cáo**: Cập nhật `main.py` nạp `models/best_head_v2.pt`, viết và chạy `tools/test_api_regression.py` (`11:42:35 – 11:42:55`), viết và chạy `tools/anonymize_figures.py` (`11:44:28`) làm mờ mặt trên 49 ảnh vào `reports/anonymized_figures/`, và viết `reports/TRAINING_REPORT.md` (`11:46:59`). | `tools/test_api_regression.py`, `tools/anonymize_figures.py`, `reports/TRAINING_REPORT.md` (`10/17/2026 11:46:59 AM`). | **[ĐÃ XÁC MINH]** |
| **10** | `17/10/2026 12:38:08 – 13:17:30` | **Cập nhật sơ đồ 135 ghế (`A–L`) cho 4 phòng & Lịch chiếu**: Viết `tools/setup_rooms_and_schedule.py` (`12:38:08 – 13:16:10`), tạo `seats_config_room1..4.json` (`12:46:50 – 13:16:29`) và cập nhật `seat_mapper.py` (`13:17:30`), `main.py` (`12:51:43`). | `tools/setup_rooms_and_schedule.py`, `seat_mapper.py:52-79`, `main.py:132-222`. | **[ĐÃ XÁC MINH]** |

---

### 1.2. Đối chiếu với Kế hoạch 10 Phase & Các điểm lệch thực tế

| Phase trong Kế hoạch | Nội dung theo Kế hoạch | Trạng thái | Chi tiết thực hiện & Chỗ lệch so với kế hoạch (kèm bằng chứng) |
| :--- | :--- | :---: | :--- |
| **Phase 1: Khảo sát video** | Đo độ phân giải, FPS, thời lượng, độ sáng từng giây để tìm đoạn đèn sáng / đèn tối và chọn vùng cắt. | **ĐÃ LÀM** | Đã xuất `reports/brightness_profile.png` và `reports/contact_sheet_cam_edited.jpg`. **Điểm lưu ý**: Không lưu script khảo sát thành tệp `.py` cố định trong `tools/` mà chỉ lưu 2 tệp ảnh kết quả trong `reports/`. **[ĐÃ XÁC MINH]** |
| **Phase 2: Trích khung & Chia tập** | Trích khung theo bước nhảy thời gian, lọc khung trùng, chia `train/val/test` theo phiên và lập `manifest.csv`. | **ĐÃ LÀM (CÓ LỆCH NHỎ)** | Thực hiện bởi `tools/extract_frames.py`. **Chỗ lệch**: (1) Trong docstring `extract_frames.py:8-11` ghi phân đoạn 3 kết thúc ở `420s`, nhưng trong code `extract_frames.py:124` đặt `345.0 <= sec <= 422.0`; (2) Gọi tập `test` là `"suat2_phim_chieu"` nhưng thực chất vẫn cắt từ phút `07:05 – 09:32` của **cùng 1 tệp video `cam_edited.mp4`**, chỉ cách tập `val` đúng **5,5 giây** (`419,5s` $\to$ `425,0s`). **[ĐÃ XÁC MINH]** |
| **Phase 3: Quy ước nhãn & Công cụ gán** | Viết tài liệu quy ước gán nhãn `head` và chuẩn bị công cụ gán nhãn. | **ĐÃ LÀM** | Đã tạo `reports/LABELING_GUIDE.md` và công cụ `tools/label_heads_cv.py` có thanh đệm header/footer ngoài vùng ảnh (`header_h=42, footer_h=32` tại `label_heads_cv.py:24-27`) để không che hàng ghế sát mép trên. **[ĐÃ XÁC MINH]** |
| **Phase 4: Gán nhãn Giai đoạn A** | Người dùng tự gán nhãn tay khoảng 40 ảnh đại diện để làm tập hạt giống. | **ĐÃ LÀM** | Người dùng đã gán tay 40 ảnh (`32 train + 8 val` theo `datasets/head_v2/stage_a_list.txt`) từ `18:05:20` đến `18:30:38` ngày 13/10/2026. **[ĐÃ XÁC MINH]** |
| **Phase 5: Huấn luyện Giai đoạn A & Pre-label** | Huấn luyện mô hình nháp trên 40 ảnh Stage A, sau đó chạy suy luận gán nhãn nháp cho các ảnh còn lại. | **ĐÃ LÀM** | Thực hiện bởi `tools/train_baseline.py` (`baseline_stage_a.pt` đạt `mAP@50 = 0.7872` trên 8 ảnh val), sinh 505 khung đầu nháp cho 123 ảnh còn lại vào `datasets/head_v2/labels_prelabel/`. **Sự cố thực tế**: Giữa epoch 44 (`1732,96s`) và epoch 45 (`4106,85s`), tiến trình bị ngắt/ngủ đông mất `2373,89s` (~39,5 phút) khiến tổng thời gian ghi trong `results.csv` là `71,16 phút` thay vì ~32 phút. **[ĐÃ XÁC MINH]** |
| **Phase 6: QC & Đo tốc độ (`imgsz`) + Duyệt Giai đoạn B** | Người dùng duyệt/sửa 123 nhãn nháp; chạy script kiểm tra chất lượng nhãn (QC) và benchmark tốc độ `imgsz=640` vs `800`. | **LÀM KHÁC KẾ HOẠCH (2 ĐIỂM)** | 1. **Về cờ `"nhãn đã kiểm"` trong `manifest.csv`**: Thay vì cập nhật từng dòng khi người dùng bấm phím trong `label_heads_cv.py`, script `tools/dataset_stats.py:249` đã chạy vòng lặp gán cứng `row[6] = "có"` cho toàn bộ 163 ảnh khi thấy đủ 163 file `.txt` trong `labels/`. Tuy nhiên, kiểm tra đối chiếu nội dung file (`labels/` vs `labels_prelabel/`) xác nhận người dùng **có mở duyệt thật** toàn bộ 123 ảnh trong `label_heads_cv.py` (73/123 ảnh có thay đổi tọa độ/số lượng khung, 50/123 ảnh giữ nguyên gợi ý).<br>2. **Về đo tốc độ `imgsz=640` vs `800`**: Không có tệp log benchmark riêng trong `reports/` (`KHÔNG TÌM THẤY` tệp log benchmark), chỉ có kết luận ghi lại trong `reports/TRAINING_REPORT.md:58-60` và comment tại `tools/train_baseline.py:66` (`imgsz=800` giảm tỉ lệ đầu $<12\text{px}$ từ $58,4\%$ xuống $5,9\%$). **[ĐÃ XÁC MINH]** |
| **Phase 7: Huấn luyện chính thức** | Huấn luyện mô hình chính thức trên toàn bộ tập `train` (98 ảnh) và `val` (22 ảnh) từ `yolov8n.pt`. | **ĐÃ LÀM** | Thực hiện bởi `tools/train_official.py` (50 epochs, `imgsz=800`, `batch=4`, `seed=42`), lưu `models/best_head_v2.pt` và `reports/official_training_summary.txt`. **[ĐÃ XÁC MINH]** |
| **Phase 8: Đánh giá độc lập trên tập Test** | Chọn ngưỡng `conf` trên tập `val`, rồi chạy đánh giá mù **duy nhất 1 lần** trên tập `test` (43 ảnh). | **LÀM KHÁC KẾ HOẠCH (QUAN TRỌNG)** | Trong `tools/eval_counts.py:106-152`, quét tập `val` chọn ra `conf = 0.15` (với `iou = 0.60`) và chạy trên tập `test` ra `MAE = 0.88` (`reports/EVAL_REPORT_PHASE8.md:4-15`). Tuy nhiên, sau đó tập `test` lại được quét thêm ở các mức `conf = 0.20, 0.25, 0.30` (bảng tại `reports/TRAINING_REPORT.md:100-106`) để thấy `conf = 0.25` cho `MAE = 0.44` tốt hơn trên tập `test`, rồi dùng chính con số `conf = 0.25` đó đưa vào `main.py:422`. Điều này vi phạm nguyên tắc "chỉ dùng ngưỡng chọn từ tập `val`, không nhìn tập `test` để chọn lại ngưỡng". **[ĐÃ XÁC MINH]** |
| **Phase 9 (9a & 9b): Hiệu chuẩn ghế & Đưa vào hệ thống** | Hiệu chuẩn bản đồ ghế thật (`calibrate_seats.py`) và tích hợp mô hình mới vào `main.py` kèm kiểm thử hồi quy. | **LÀM KHÁC KẾ HOẠCH (PHẦN GHẾ)** | - **Phase 9b (`main.py` & test API)**: **ĐÃ LÀM** (`main.py:420-425`, `tools/test_api_regression.py`). Nhưng `main.py:92` không truyền `iou=0.60` như `eval_counts.py:63`.<br>- **Phase 9a (Bản đồ ghế)**: Không dùng `calibrate_seats.py` để chấm tay trên khung hình $1920\times 1080$, mà dùng `tools/setup_rooms_and_schedule.py` dựng lưới nội suy 135 ghế (`A–L`) từ ảnh chụp màn hình $1024\times 899$ rồi ánh xạ tuyến tính sang $1920\times 1080$ và copy giống hệt nhau cho cả 4 phòng `room1..room4`. **[ĐÃ XÁC MINH]** |
| **Phase 10: Ẩn danh & Báo cáo** | Làm mờ mặt khán giả trên ảnh minh họa và viết báo cáo tổng kết. | **ĐÃ LÀM** | Thực hiện bởi `tools/anonymize_figures.py` (làm mờ 49 ảnh vào `reports/anonymized_figures/`) và xuất `reports/TRAINING_REPORT.md`. **Lưu ý**: Các ảnh gốc chưa làm mờ trong `reports/qc_overlays/` và `reports/failure_cases/` vẫn còn nằm trên ổ đĩa cục bộ. **[ĐÃ XÁC MINH]** |

---

## PHẦN 2: DỮ LIỆU (VIDEO, TRÍCH KHUNG, CHIA TẬP, NHÃN & THỐNG KÊ)

> **Góc nhìn Frontend Dev**: Trong phát triển web/app, dữ liệu huấn luyện (`train`) giống như **mock data dùng khi bạn viết code**, tập `val` giống như **bộ unit test chạy mỗi lần bạn bấm Save (hot-reload)** để xem code mới sửa có tốt hơn không, còn tập `test` giống như **bộ kiểm thử UAT (User Acceptance Test) của QA** chỉ chạy một lần cuối trước khi release. Nếu dữ liệu UAT thực chất chỉ là bản copy-paste từ mock data cách đó vài giây, bài test UAT sẽ xanh 100% nhưng khi lên production gặp người dùng thật thì vẫn có thể vỡ.

### 2.a. Video gốc (`cam_edited.mp4`)

Tất cả các con số dưới đây được đo trực tiếp bằng OpenCV trên tệp video gốc và đối chiếu với `tools/extract_frames.py`:

- **Đường dẫn tệp**: `C:\Users\Dell KIM ANH\Downloads\cam_edited.mp4` (`tools/extract_frames.py:16`). **[ĐÃ XÁC MINH]**
- **Dung lượng tệp**: `1.456.225.950 bytes` ($\approx 1,356\text{ GB}$). **[ĐÃ XÁC MINH - Output lệnh Mục 2 Phụ lục]**
- **Độ phân giải**: **$1920 \times 1080\text{ px}$** (Full HD, tỉ lệ $16:9$). **[ĐÃ XÁC MINH]**
- **Tốc độ khung hình (FPS)**: **$30,0\text{ FPS}$**. **[ĐÃ XÁC MINH]**
- **Tổng số khung hình & Thời lượng**: **$17.337\text{ frames}$**, tương đương **$577,90\text{ giây}$** ($9\text{ phút } 37,9\text{ giây}$). **[ĐÃ XÁC MINH]**
- **Ảnh xám hay ảnh màu (Đo lại bằng số)**:
  - Mặc dù tệp `.mp4` lưu 3 kênh màu BGR (OpenCV đọc ra mảng `(1080, 1920, 3)`), phép đo độ lệch tuyệt đối giữa các kênh màu $|R-G|$, $|G-B|$ và độ bão hòa màu HSV (`Saturation`, thang $0-255$) tại 5 mốc thời gian trên toàn video cho kết quả:
    - Tại $t = 10\text{s}$ (chiếu phim tối): $\text{Brightness} = 95,36$, $\text{Saturation} = 0,14$, $|R-G| = 0,01$, $|G-B| = 0,03$.
    - Tại $t = 150\text{s}$ (chiếu phim tối): $\text{Brightness} = 95,54$, $\text{Saturation} = 1,31$, $|R-G| = 0,05$, $|G-B| = 0,31$.
    - Tại $t = 300\text{s}$ (đèn sáng ra về): $\text{Brightness} = 106,87$, $\text{Saturation} = 2,20$, $|R-G| = 0,07$, $|G-B| = 0,41$.
    - Tại $t = 380\text{s}$ (đèn sáng vào chỗ): $\text{Brightness} = 106,90$, $\text{Saturation} = 0,00$, $|R-G| = 0,00$, $|G-B| = 0,00$.
    - Tại $t = 500\text{s}$ (chiếu phim tối Suất 2): $\text{Brightness} = 98,38$, $\text{Saturation} = 0,00$, $|R-G| = 0,00$, $|G-B| = 0,00$.
  - **Kết luận**: Video thực chất là **ảnh xám hồng ngoại đơn sắc (Monochrome Infrared - IR)** ($R \approx G \approx B$ gần như tuyệt đối; ở $t=380\text{s}$ và $500\text{s}$ ba kênh bằng nhau $100\%$). **[ĐÃ XÁC MINH - Output lệnh Mục 2 Phụ lục]**
- **Các đoạn đèn sáng, đoạn chiếu phim, đoạn được dùng và đoạn bị loại (`tools/extract_frames.py:114-129`)**:
  1. **`0,0s – 265,0s` (`00:00 – 04:25`)**: Đoạn chiếu phim đèn tắt (độ sáng trung bình $\sim 94 - 96$) $\rightarrow$ **ĐƯỢC DÙNG** làm `train` (`suat1_phim_chieu`).
  2. **`265,0s – 270,0s` (`04:25 – 04:30`, dài 5 giây)**: Đoạn chuyển tiếp bật đèn $\rightarrow$ **BỊ LOẠI** (do khoảng trống giữa hai điều kiện `if 0.0 <= sec <= 265.0` và `elif 270.0 <= sec < 345.0` tại `extract_frames.py:117-120` để tránh vùng giao thoa và nhiễu chuyển trạng thái ánh sáng).
  3. **`270,0s – 345,0s` (`04:30 – 05:45`)**: Đoạn bật đèn sáng khán giả di chuyển/ra về (độ sáng trung bình $\sim 106 - 107$) $\rightarrow$ **ĐƯỢC DÙNG** làm `train` (`suat1_den_sang_ra_ve`).
  4. **`345,0s – 422,0s` (`05:45 – 07:02`)**: Đoạn bật đèn sáng khán giả vào chỗ (độ sáng trung bình $\sim 106 - 107$) $\rightarrow$ **ĐƯỢC DÙNG** làm `val` (`suat1_den_sang_vao_cho`). *(Lưu ý: Không có khoảng đệm giây nào bị loại giữa `train` kết thúc ở `<345,0s` và `val` bắt đầu ở `>=345,0s`)*.
  5. **`422,0s – 425,0s` (`07:02 – 07:05`, dài 3 giây)**: Đoạn chuyển tiếp tắt đèn $\rightarrow$ **BỊ LOẠI** (`extract_frames.py:124-126`).
  6. **`425,0s – 575,0s` (`07:05 – 09:35`)**: Đoạn chiếu phim đèn tắt (độ sáng trung bình $\sim 94 - 99$) $\rightarrow$ **ĐƯỢC DÙNG** làm `test` (`suat2_phim_chieu`).
  7. **`575,0s – 577,9s` (`09:35 – 09:37,9`, dài 2,9 giây cuối)**: **BỊ LOẠI** (`extract_frames.py:126-129`).

---

### 2.b. Tham số trích khung hình (`tools/extract_frames.py`)

- **Khoảng cách lấy mẫu (`step_sec`)**: **$3,5\text{ giây}$** (`step_frames = int(3.5 * fps) = 105 frames`, tại `tools/extract_frames.py:55-56`). **[ĐÃ XÁC MINH]**
- **Ngưỡng bỏ khung trùng (`diff_thresh`)**: **`1.5`** (`tools/extract_frames.py:57, 136-143`). Cụ thể, mỗi khung hình ứng viên được chuyển sang ảnh xám, thu nhỏ về kích thước $320\times 180\text{ px}$, rồi tính trung bình độ lệch tuyệt đối pixel `cv2.absdiff(gray_small, last_saved_gray_by_split[split]).mean()`. Nếu `diff_val < 1.5` (khán giả ngồi yên hoàn toàn so với khung vừa lưu trước đó trong cùng tập), khung hình đó bị bỏ qua. **[ĐÃ XÁC MINH]**
- **Tổng số khung hình đã lưu**: **163 khung hình** (trên tổng số $\lfloor 575 / 3,5 \rfloor \approx 164$ vị trí lấy mẫu; chỉ có rất ít khung bị loại bởi ngưỡng `1.5` vì nhiễu hạt hồng ngoại và chuyển động nhỏ của khán giả/màn hình chiếu luôn giữ `diff >= 1.5`). **[ĐÃ XÁC MINH]**
- **Số khung mỗi đoạn thời gian (`datasets/head_v2/manifest.csv:2-164`)**:
  - `suat1_phim_chieu` (`train`): **76 khung** (từ `0,0s` đến `262,5s`).
  - `suat1_den_sang_ra_ve` (`train`): **22 khung** (từ `270,0s` đến `343,5s`).
  - `suat1_den_sang_vao_cho` (`val`): **22 khung** (từ `346,0s` đến `419,5s`).
  - `suat2_phim_chieu` (`test`): **43 khung** (từ `425,0s` đến `572,0s`).

---

### 2.c. Chia tập (`train` / `val` / `test`) & Bằng chứng khoảng cách thời gian (Rò rỉ dữ liệu)

| Tập dữ liệu | Số lượng ảnh (`images/`) | Số khung đầu (`labels/`) | Phân đoạn trong `manifest.csv` | Dải thời gian chiếm trong video `cam_edited.mp4` | Tệp đầu tiên $\rightarrow$ Tệp cuối cùng |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`train`** | **98 ảnh** (60,1%) | **570 đầu** (69,1%) | `suat1_phim_chieu` (76 ảnh) + `suat1_den_sang_ra_ve` (22 ảnh) | **`0,0s` $\rightarrow$ `262,5s`** và **`270,0s` $\rightarrow$ `343,5s`** | `room1_cam_edited_0000s.jpg` $\rightarrow$ `room1_cam_edited_0344s.jpg` (`manifest.csv:2-99`) |
| **`val`** | **22 ảnh** (13,5%) | **87 đầu** (10,5%) | `suat1_den_sang_vao_cho` (22 ảnh) | **`346,0s` $\rightarrow$ `419,5s`** | `room1_cam_edited_0346s.jpg` $\rightarrow$ `room1_cam_edited_0420s.jpg` (`manifest.csv:100-121`) |
| **`test`** | **43 ảnh** (26,4%) | **168 đầu** (20,4%) | `suat2_phim_chieu` (43 ảnh) | **`425,0s` $\rightarrow$ `572,0s`** | `room1_cam_edited_0425s.jpg` $\rightarrow$ `room1_cam_edited_0572s.jpg` (`manifest.csv:122-164`) |
| **Tổng cộng** | **163 ảnh** (100%) | **825 đầu** (100%) | 4 phân đoạn liên tiếp | **`0,0s` $\rightarrow$ `572,0s`** | 163 tệp `.jpg` và 163 tệp `.txt` |

- **Cách chia tập**: Chia **theo lát cắt thời gian tuần tự trên CÙNG 1 tệp video `cam_edited.mp4`** (`tools/extract_frames.py:114-129`), không chia ngẫu nhiên từng khung, nhưng cũng **không phải từ các tệp video độc lập của các ngày/phòng khác nhau**. **[ĐÃ XÁC MINH]**
- **Khoảng cách thời gian nhỏ nhất giữa các tập (Tính từ cột `thời điểm (giây)` trong `datasets/head_v2/manifest.csv`)**:
  1. **Giữa tập `val` và khung `train` gần nhất**:
     - Khung cuối cùng của `train`: `room1_cam_edited_0344s.jpg` tại thời điểm **$343,5\text{ giây}$** (`manifest.csv:99`).
     - Khung đầu tiên của `val`: `room1_cam_edited_0346s.jpg` tại thời điểm **$346,0\text{ giây}$** (`manifest.csv:100`).
     - $\Rightarrow$ **Khoảng cách nhỏ nhất giữa `val` và `train` = $346,0 - 343,5 = \mathbf{2,5\text{ giây}}$** (chưa bằng 1 bước nhảy lấy mẫu $3,5\text{s}$!). **[ĐÃ XÁC MINH]**
  2. **Giữa tập `test` và khung `val` gần nhất**:
     - Khung cuối cùng của `val`: `room1_cam_edited_0420s.jpg` tại thời điểm **$419,5\text{ giây}$** (`manifest.csv:121`).
     - Khung đầu tiên của `test`: `room1_cam_edited_0425s.jpg` tại thời điểm **$425,0\text{ giây}$** (`manifest.csv:122`).
     - $\Rightarrow$ **Khoảng cách nhỏ nhất giữa `test` và `val` = $425,0 - 419,5 = \mathbf{5,5\text{ giây}}$**. **[ĐÃ XÁC MINH]**
  3. **Giữa tập `test` và khung `train` gần nhất**:
     - $\Rightarrow$ **Khoảng cách nhỏ nhất giữa `test` và `train` = $425,0 - 343,5 = \mathbf{81,5\text{ giây}}$** ($1\text{ phút } 21,5\text{ giây}$). **[ĐÃ XÁC MINH]**

---

### 2.d. Nguồn gốc nhãn: Người gán tay vs Mô hình gán nháp (`labels/` vs `labels_prelabel/` & `manifest.csv`)

Khi đối chiếu 3 nguồn dữ liệu thật: (1) danh sách 40 ảnh hạt giống `datasets/head_v2/stage_a_list.txt`, (2) thư mục nhãn nháp do `baseline_stage_a.pt` sinh ra `datasets/head_v2/labels_prelabel/`, và (3) thư mục nhãn chính thức `datasets/head_v2/labels/` (đã tính cả phép biến đổi làm tròn pixel nguyên khi công cụ `label_heads_cv.py:55-83` đọc tọa độ chuẩn hóa $\to$ đổi ra pixel nguyên $\to$ lưu lại khi người dùng bấm `D/Space`), ta có con số chính xác tuyệt đối:

| Tập dữ liệu | Tổng số ảnh | (1) Người gán tay hoàn toàn từ đầu (`stage_a_list.txt`) | (2) Mô hình gán nháp $\rightarrow$ Người dùng **có vẽ thêm/xóa/sửa khung** | (3) Mô hình gán nháp $\rightarrow$ Người dùng **bấm duyệt giữ nguyên 100% khung gợi ý** | Cờ `"nhãn đã kiểm"` trong `manifest.csv` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`train`** | **98 ảnh** | **32 ảnh** (32,7%) | **28 ảnh** (28,6%) | **38 ảnh** (38,8%) | `98/98 = "có"` |
| **`val`** | **22 ảnh** | **8 ảnh** (36,4%) | **11 ảnh** (50,0%) | **3 ảnh** (13,6%) | `22/22 = "có"` |
| **`test`** | **43 ảnh** | **0 ảnh** (0,0%) | **34 ảnh** (79,1%) | **9 ảnh** (20,9%) | `43/43 = "có"` |
| **Tổng cộng** | **163 ảnh** | **40 ảnh** (**24,5%**) | **73 ảnh** (**44,8%**) | **50 ảnh** (**30,7%**) | `163/163 = "có"` |

- **Giải thích chi tiết và trung thực**:
  1. **40 ảnh (24,5%)** thuộc Giai đoạn A (`32 train + 8 val`) hoàn toàn không có tệp trong `labels_prelabel/` — 100% do người dùng tự vẽ tay từ đầu lúc `18:05 – 18:30` ngày 13/10/2026. **[ĐÃ XÁC MINH]**
  2. **123 ảnh còn lại (75,5%)** (`66 train + 14 val + 43 test`) được `baseline_stage_a.pt` gán nháp lúc `20:14:38 – 20:14:58` với tổng cộng **505 khung đầu gợi ý** (`360 train + 43 val + 102 test`). Sau khi người dùng mở `tools/label_heads_cv.py` duyệt từ `20:20:32` đến `20:42:46` (trong khoảng 22 phút), tổng số khung đầu trên 123 ảnh này tăng từ **505 lên 604 khung** (`382 train + 54 val + 168 test`, tức người dùng đã vẽ bổ sung thêm ròng **+99 khung đầu** mà mô hình nháp bỏ sót!). **[ĐÃ XÁC MINH - Output lệnh Mục 1 Phụ lục]**
  3. Tuy nhiên, trong 123 ảnh có nhãn nháp đó, có **50 ảnh (`38 train + 3 val + 9 test`)** mà tọa độ các khung trong `labels/` trùng khớp 100% (sau làm tròn pixel của `label_heads_cv.py`) với nhãn nháp của `baseline_stage_a.pt` — nghĩa là khi mở tới ảnh đó, người dùng thấy khung vàng gợi ý đã khớp nên bấm `D/Space` để sang ảnh tiếp theo mà không vẽ lại. Do đó, trong tập `train` (98 ảnh), có **38/98 ảnh (38,8%)** mang tọa độ khung do chính `baseline_stage_a.pt` sinh ra. **[ĐÃ XÁC MINH]**
  4. **Về cờ `"nhãn đã kiểm"` trong `manifest.csv`**: Cột thứ 7 của `datasets/head_v2/manifest.csv` ghi `"có"` cho cả 163 ảnh, nhưng cần biết rằng giá trị `"có"` này được gán hàng loạt bởi đoạn code `tools/dataset_stats.py:246-249` (`if os.path.exists(lbl_path): row[6] = "có"`). Không có ảnh nào thiếu tệp nhãn `.txt` trong dữ liệu huấn luyện. **[ĐÃ XÁC MINH]**

---

### 2.e. Thống kê nhãn chi tiết (Chạy lại logic `tools/dataset_stats.py` ở chế độ chỉ đọc)

> **Lưu ý tuân thủ Quy tắc 2**: Bản thân tệp `tools/dataset_stats.py:215-253` có lệnh ghi đè ảnh vào `reports/qc_overlays/` và ghi đè `datasets/head_v2/manifest.csv`. Để tuân thủ tuyệt đối quy tắc **"không sửa dữ liệu"**, phần thống kê dưới đây chạy lại chính xác thuật toán của `dataset_stats.py` ở chế độ chỉ đọc (xem Output nguyên văn tại Phụ lục).

| Chỉ số thống kê | Tập `train` (98 ảnh) | Tập `val` (22 ảnh) | Tập `test` (43 ảnh) | Toàn bộ `head_v2` (163 ảnh) |
| :--- | :---: | :---: | :---: | :---: |
| **Tổng số khung đầu (`head`)** | **570 khung** | **87 khung** | **168 khung** | **825 khung** |
| **Số đầu / ảnh (Trung bình $\pm$ Trung vị)** | **$5,82$** (Trung vị: $6,0$) | **$3,95$** (Trung vị: $4,5$) | **$3,91$** (Trung vị: $4,0$) | **$5,06$** (Trung vị: $6,0$) |
| **Số đầu / ảnh (Nhỏ nhất – Lớn nhất)** | $4 \rightarrow 6\text{ đầu}$ | $0 \rightarrow 6\text{ đầu}$ | $0 \rightarrow 6\text{ đầu}$ | **$0 \rightarrow 6\text{ đầu}$** |
| **Phân bố số đầu mỗi ảnh (`{số_đầu: số_ảnh}`)** | `{4: 3, 5: 12, 6: 83}` | `{0: 3, 1: 3, 3: 1, 4: 4, 5: 1, 6: 10}` | `{0: 4, 1: 1, 3: 3, 4: 26, 6: 9}` | `{0: 7, 1: 4, 3: 4, 4: 33, 5: 13, 6: 102}` |
| **Số ảnh không đầu (Ảnh nền trống - `0 head`)** | **0 ảnh (0,0%)** | **3 ảnh (13,6%)** | **4 ảnh (9,3%)** | **7 ảnh (4,29%)** |
| **Kích thước gốc ($1920\times 1080$) — Trung vị $W \times H$** | $34,0 \times 36,0\text{ px}$ | $35,0 \times 36,0\text{ px}$ | $30,0 \times 32,0\text{ px}$ | **$33,0 \times 35,0\text{ px}$** |
| **Kích thước gốc ($1920\times 1080$) — Nhỏ nhất $W \times H$** | $17,0 \times 18,0\text{ px}$ | $15,0 \times 18,0\text{ px}$ | $18,0 \times 23,0\text{ px}$ | **$15,0 \times 18,0\text{ px}$** |
| **Tỉ lệ khung gốc $< 12\text{ px}$ (trên $1920\times 1080$)** | $0 / 570$ (**0,00%**) | $0 / 87$ (**0,00%**) | $0 / 168$ (**0,00%**) | **$0 / 825$ (0,00%)** |
| **Sau khi thu về `imgsz=800` ($800\times 450$, tỉ lệ $\times 0,4167$) — Trung vị $W \times H$** | $14,17 \times 15,00\text{ px}$ | $14,58 \times 15,00\text{ px}$ | $12,50 \times 13,33\text{ px}$ | **$13,75 \times 14,58\text{ px}$** |
| **Sau khi thu về `imgsz=800` — Chiều cao $H < 8\text{ px}$ / Chiều rộng $W < 8\text{ px}$** | $H<8$: $1$ ($0,18\%$) / $\min(W,H)<8$: $4$ (**0,70%**) | $H<8$: $1$ ($1,15\%$) / $\min(W,H)<8$: $1$ (**1,15%**) | $H<8$: $0$ ($0,00\%$) / $\min(W,H)<8$: $1$ (**0,60%**) | $H<8$: **2 (0,24%)** / $W<8$: **5 (0,61%)** / $\min(W,H)<8$: **6 (0,73%)** |
| **Sau khi thu về `imgsz=800` — Chiều cao $H < 12\text{ px}$ / $\min(W,H) < 12\text{ px}$** | $H<12$: **30 (5,26%)** / $\min<12$: **102 (17,89%)** | $H<12$: **7 (8,05%)** / $\min<12$: **11 (12,64%)** | $H<12$: **12 (7,14%)** / $\min<12$: **60 (35,71%)** | $H<12$: **49 (5,94%)** / $W<12$: **151 (18,30%)** / $\min<12$: **173 (20,97%)** |
| **Tệp nhãn lỗi định dạng / trùng khung ($\text{IoU} > 0,9$)** | **0 tệp lỗi / 0 trùng** | **0 tệp lỗi / 0 trùng** | **0 tệp lỗi / 0 trùng** | **0 tệp lỗi / 0 trùng** |

> **Phát hiện quan trọng từ bảng thống kê trên**:
> 1. Tập `train` **không có bất kỳ ảnh nền trống nào (`0 ảnh 0 đầu`)** — mọi ảnh `train` đều có từ 4 đến 6 đầu người (`83/98` ảnh có đúng 6 đầu), trong khi tập `val` có 3 ảnh trống và tập `test` có 4 ảnh trống! **[ĐÃ XÁC MINH]**
> 2. Trong toàn bộ 163 ảnh, **số lượng đầu người tối đa trong 1 ảnh chỉ là 6 đầu** (`max = 6`). Không có bất kỳ khung hình nào có từ 7 khách trở lên trên tổng số 135 ghế của phòng chiếu. **[ĐÃ XÁC MINH]**

---

## PHẦN 3: HUẤN LUYỆN (`runs/detect/head_v2_official`)

### 3.a. Cấu hình huấn luyện thực tế (`runs/detect/head_v2_official/args.yaml`)

Dưới đây là các tham số thực tế trích xuất trực tiếp từ `c:\CineSightApp\ai_service\runs\detect\head_v2_official\args.yaml` và script khởi chạy `c:\CineSightApp\ai_service\tools\train_official.py:29-56`:

- **Script đã dùng**: `c:\CineSightApp\ai_service\tools\train_official.py` (chạy bằng `c:\CineSightApp\ai_service\venv\Scripts\python.exe`). **[ĐÃ XÁC MINH]**
- **Phiên bản môi trường**:
  - `Python`: **`3.14.3`**
  - `PyTorch`: **`2.14.0+cpu`**
  - `Ultralytics`: **`8.4.160`**
  - `OpenCV`: **`5.0.0`**
  - `NumPy`: **`2.5.3`** **[ĐÃ XÁC MINH - Output lệnh Mục 1 Phụ lục]**
- **Tham số cốt lõi trong `args.yaml`**:
  - `model`: `c:\CineSightApp\ai_service\yolov8n.pt` (`args.yaml:3`)
  - `data`: `c:\CineSightApp\ai_service\dataset_head_v2.yaml` (`args.yaml:4`)
  - `epochs` đặt: **`50`** (`args.yaml:5`)
  - `patience` đặt: **`20`** (`args.yaml:7`)
  - **Số epochs thực chạy**: **Chạy đủ 50/50 epochs, KHÔNG bị dừng sớm (Early Stopping)** vì đỉnh fitness đạt tại **Epoch 35**, mà $35 + 20 = 55 > 50$ (`runs/detect/head_v2_official/results.csv:2-51`).
  - `imgsz`: **`800`** (`args.yaml:9`) — ảnh $1920\times 1080$ được thu về $800\times 450$ kèm đệm xám (letterbox) thành $800\times 800$ khi đưa vào mạng.
  - `batch`: **`4`** (`args.yaml:8`) — với 98 ảnh `train`, mỗi epoch gồm $\lceil 98 / 4 \rceil = 25$ bước cập nhật trọng số (iterations/batches).
  - `device`: **`cpu`** (`args.yaml:12`)
  - `workers`: **`2`** (`args.yaml:13`)
  - `seed`: **`42`** (`args.yaml:22`) và `deterministic: true` (`args.yaml:23`)
  - `optimizer`: **`auto`** (`args.yaml:17`, Ultralytics tự chọn `AdamW` hoặc `SGD` theo quy tắc nội bộ; với tập nhỏ 1 lớp và `lr0: 0.01`, `lrf: 0.01`, `momentum: 0.937`, `weight_decay: 0.0005`, `warmup_epochs: 3.0` tại `args.yaml:68-73`).
  - **Trọng số hàm mất mát**: `box: 7.5`, `cls: 0.5`, `dfl: 1.5` (`args.yaml:76-78`).
  - **Augmentation (Biến đổi tăng cường dữ liệu trong `args.yaml:84-102`)**:
    - Biến đổi màu/độ sáng: `hsv_h: 0.015`, `hsv_s: 0.7`, `hsv_v: 0.4` (tăng/giảm độ sáng $\pm 40\%$).
    - Biến đổi hình học: `translate: 0.1` (dịch chuyển $\pm 10\%$), `scale: 0.5` (phóng to/thu nhỏ $\pm 50\%$), `fliplr: 0.5` (lật ngang trái-phải xác suất $50\%$), `degrees: 0.0`, `flipud: 0.0`.
    - Ghép ảnh: `mosaic: 1.0` (ghép 4 ảnh thành 1 với xác suất $100\%$ trong 40 epochs đầu), `close_mosaic: 10` (`args.yaml:39` — tắt Mosaic ở 10 epochs cuối, tức từ Epoch 41 đến 50, để mô hình tinh chỉnh trên khung hình nguyên bản).
    - Tự động tăng cường & xóa ngẫu nhiên: `auto_augment: randaugment`, `erasing: 0.4` (`args.yaml:100-101`).

---

### 3.b. Xác nhận Mô hình nền & Dữ liệu

1. **Khởi tạo từ `yolov8n.pt` gốc**: Trong `tools/train_official.py:21, 29` và `runs/detect/head_v2_official/args.yaml:3`, đường dẫn model là `c:\CineSightApp\ai_service\yolov8n.pt` (`6.549.796 bytes`), **KHÔNG phải** `best_v1.pt` và cũng **KHÔNG phải** `baseline_stage_a.pt` (nhằm tránh hiện tượng học chồng chéo trên các nhãn nháp do chính `baseline_stage_a.pt` tạo ra). **[ĐÃ XÁC MINH]**
2. **Dữ liệu KHÔNG gồm `coco128`**: Tệp `c:\CineSightApp\ai_service\dataset_head_v2.yaml:1-7` chỉ trỏ duy nhất tới `path: c:/CineSightApp/ai_service/datasets/head_v2`, `train: images/train` (98 ảnh rạp), `val: images/val` (22 ảnh rạp), `nc: 1`, `names: {0: head}`. Bộ `coco128` cũ đã được dời sang `ai_service/datasets_archive/coco128` từ lúc `16:16:27` ngày 13/10/2026. **[ĐÃ XÁC MINH]**

---

### 3.c. Danh sách toàn bộ 24 tệp kết quả trong `runs/detect/head_v2_official/`

| STT | Tên tệp (Đường dẫn tương đối) | Dung lượng | Giải thích công dụng của tệp |
| :---: | :--- | :---: | :--- |
| 1 | `weights/best.pt` | `6.244.586 B` | Trọng số mô hình có điểm `fitness` cao nhất trên tập `val` (đạt tại **Epoch 35**); tệp này đã được copy sang `models/best_head_v2.pt` để chạy chính thức. |
| 2 | `weights/last.pt` | `6.244.586 B` | Trọng số mô hình ở vòng lặp cuối cùng (**Epoch 50**), dùng để resume nếu muốn huấn luyện tiếp. |
| 3 | `args.yaml` | `1.894 B` | Lưu toàn bộ 106 siêu tham số (hyperparameters) và đường dẫn đã dùng trong lần chạy. |
| 4 | `results.csv` | `6.204 B` | Bảng số liệu dạng CSV ghi lại thời gian, 3 loại train loss, 3 loại val loss, Precision, Recall, mAP50, mAP50-95 và learning rate của từng epoch từ 1 đến 50. |
| 5 | `results.png` | `288.789 B` | Đồ thị tổng hợp 10 đường cong (train/val losses và P, R, mAP50, mAP50-95) theo 50 epochs. |
| 6 | `BoxF1_curve.png` | `103.952 B` | Đường cong điểm trung hòa $F_1 = \frac{2PR}{P+R}$ theo ngưỡng độ tin cậy `conf` từ $0,0$ đến $1,0$ trên tập `val`. |
| 7 | `BoxPR_curve.png` | `75.308 B` | Đường cong Precision–Recall trên tập `val`; diện tích dưới đường cong này chính là $\text{mAP@50} = 0,810$. |
| 8 | `BoxP_curve.png` | `91.876 B` | Đường cong độ chuẩn xác (Precision) theo ngưỡng `conf` trên tập `val`. |
| 9 | `BoxR_curve.png` | `92.641 B` | Đường cong độ phủ (Recall) theo ngưỡng `conf` trên tập `val`. |
| 10 | `confusion_matrix.png` | `86.159 B` | Ma trận nhầm lẫn đếm số lượng tuyệt đối (số đầu phát hiện đúng, số lần báo giả trên nền `background`, số đầu bị bỏ sót) trên tập `val`. |
| 11 | `confusion_matrix_normalized.png` | `90.458 B` | Ma trận nhầm lẫn chuẩn hóa theo tỉ lệ phần trăm ($0,00 - 1,00$) trên tập `val`. |
| 12 | `labels.jpg` | `94.783 B` | Biểu đồ thống kê phân bố vị trí tâm $(x_c, y_c)$ và kích thước $(w, h)$ của 570 khung đầu trong tập `train`. |
| 13 | `train_batch0.jpg` | `360.993 B` | Ảnh minh họa lô huấn luyện đầu tiên (Batch 0, Epoch 1) sau khi qua phép ghép 4 ảnh `mosaic=1.0` và biến đổi sáng/xóa. |
| 14 | `train_batch1.jpg` | `329.609 B` | Ảnh minh họa lô huấn luyện thứ 2 (Batch 1, Epoch 1) với dữ liệu đã qua augmentation. |
| 15 | `train_batch2.jpg` | `269.855 B` | Ảnh minh họa lô huấn luyện thứ 3 (Batch 2, Epoch 1) với dữ liệu đã qua augmentation. |
| 16 | `train_batch1000.jpg` | `212.963 B` | Ảnh minh họa lô huấn luyện thứ 1000 (bắt đầu Epoch 41, khi `close_mosaic=10` vừa tắt ghép ảnh Mosaic, trở về ảnh đơn nguyên bản). |
| 17 | `train_batch1001.jpg` | `267.328 B` | Ảnh minh họa lô huấn luyện thứ 1001 (Epoch 41, không còn Mosaic). |
| 18 | `train_batch1002.jpg` | `208.578 B` | Ảnh minh họa lô huấn luyện thứ 1002 (Epoch 41, không còn Mosaic). |
| 19 | `val_batch0_labels.jpg` | `378.702 B` | Ảnh ghép lô kiểm định 0 của tập `val` vẽ khung **nhãn thật (Ground Truth)** để đối chiếu bằng mắt. |
| 20 | `val_batch0_pred.jpg` | `383.649 B` | Ảnh ghép lô kiểm định 0 của tập `val` vẽ khung **dự đoán của mô hình (Predictions)**. |
| 21 | `val_batch1_labels.jpg` | `378.598 B` | Ảnh ghép lô kiểm định 1 của tập `val` vẽ khung nhãn thật. |
| 22 | `val_batch1_pred.jpg` | `380.864 B` | Ảnh ghép lô kiểm định 1 của tập `val` vẽ khung dự đoán của mô hình. |
| 23 | `val_batch2_labels.jpg` | `295.601 B` | Ảnh ghép lô kiểm định 2 của tập `val` vẽ khung nhãn thật. |
| 24 | `val_batch2_pred.jpg` | `294.290 B` | Ảnh ghép lô kiểm định 2 của tập `val` vẽ khung dự đoán của mô hình. |

- **Tiêu chí chọn `best.pt` và ở Epoch nào**:
  - Ultralytics chấm điểm mỗi epoch trên tập `val` bằng công thức hàm mục tiêu `fitness`:
    $$\text{fitness} = 0,1 \times \text{mAP@50} + 0,9 \times \text{mAP@50:95}$$
  - Duyệt toàn bộ 50 dòng trong `runs/detect/head_v2_official/results.csv`, giá trị `fitness` đạt cực đại tại **Epoch 35** (dòng 36 của `results.csv`) với:
    - $\text{mAP@50} = 0,80983$
    - $\text{mAP@50:95} = 0,37750$
    - $\Rightarrow \text{fitness} = 0,1 \times 0,80983 + 0,9 \times 0,37750 = \mathbf{0,420733}$ (cao nhất trong 50 epochs). Do đó, `weights/best.pt` (và `models/best_head_v2.pt`) chính là bản chụp trọng số tại **Epoch 35**. **[ĐÃ XÁC MINH]**

---

### 3.d. Thời gian huấn luyện thực tế

- **Tổng thời gian huấn luyện (`results.csv:51`, cột `time`)**: **$7.477,41\text{ giây}$** = **$124,62\text{ phút}$** ($\approx 2\text{ giờ } 04\text{ phút } 37\text{ giây}$), chạy liên tục từ `20:57:50` đến `23:02:44` tối ngày 13/10/2026 trên CPU AMD Ryzen 5 3500U. **[ĐÃ XÁC MINH]**
- **Thời gian trung bình mỗi epoch**: **$7.477,41 / 50 = \mathbf{149,55\text{ giây/epoch}}$** ($\approx 2\text{ phút } 30\text{ giây/epoch}$, tương đương $\sim 5,98\text{ giây/batch}$ với 25 batches/epoch). **[ĐÃ XÁC MINH]**

---

## PHẦN 4: KẾT QUẢ HUẤN LUYỆN & ĐÁNH GIÁ

### 4.a. Bảng số liệu theo Epoch từ `runs/detect/head_v2_official/results.csv`

Dưới đây là bảng trích xuất chính xác từ `c:\CineSightApp\ai_service\runs\detect\head_v2_official\results.csv` tại các mốc quan trọng (Epoch 1, 5, 10, 15, 20, 25, 30, **35 - Tốt nhất**, 40, 41 - Tắt Mosaic, 45, 50 - Cuối cùng):

| Epoch | Thời gian lũy kế (s) | `train/box_loss` | `train/cls_loss` | `train/dfl_loss` | `val/box_loss` | `val/cls_loss` | `val/dfl_loss` | `Precision (B)` | `Recall (B)` | `mAP50 (B)` | `mAP50-95 (B)` | `Fitness` ($0,1\cdot\text{mAP50}+0,9\cdot\text{mAP50-95}$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `162,74` | `2,11906` | `4,46249` | `1,30306` | `2,00023` | `3,96227` | `1,25086` | `0,67123` | `0,56322` | `0,54535` | `0,22526` | `0,25727` |
| **5** | `754,84` | `1,76911` | `1,67921` | `1,09593` | `1,85296` | `2,46983` | `1,15035` | `0,84221` | `0,62069` | `0,71946` | `0,30594` | `0,34729` |
| **10** | `1511,76` | `1,63675` | `1,33478` | `1,04593` | `1,74046` | `1,21023` | `1,09717` | `0,84611` | `0,69539` | `0,77378` | `0,32258` | `0,36770` |
| **15** | `2315,07` | `1,56117` | `1,20146` | `1,02116` | `1,69702` | `1,20647` | `1,07368` | `0,91042` | `0,70103` | `0,77558` | `0,34276` | `0,38604` |
| **20** | `3087,25` | `1,49788` | `1,05355` | `1,01334` | `1,70454` | `1,06980` | `1,07733` | `0,82972` | `0,72821` | `0,79207` | `0,33154` | `0,37759` |
| **25** | `3866,01` | `1,54634` | `1,05937` | `1,01595` | `1,58734` | `0,98395` | `1,03883` | `0,92854` | `0,74659` | `0,79039` | `0,36211` | `0,40494` |
| **30** | `4622,56` | `1,49661` | `0,99416` | `1,01500` | `1,60958` | `1,00174` | `1,02531` | `0,87989` | `0,74713` | `0,79055` | `0,35675` | `0,40013` |
| **35 ★** | **`5360,40`** | **`1,45873`** | **`0,97236`** | **`0,99124`** | **`1,54911`** | **`0,94270`** | **`1,00836`** | **`0,90226`** | **`0,75862`** | **`0,80983`** | **`0,37750`** | **`0,42073` (BEST)** |
| **40** | `6121,67` | `1,44577` | `0,93730` | `0,98689` | `1,54203` | `0,90727` | `1,01696` | `0,91662` | `0,75845` | `0,79572` | `0,35942` | `0,40305` |
| **41** *(Tắt Mosaic)* | `6260,81` | `1,25711` | `0,77333` | `0,91224` | `1,47267` | `0,88450` | `0,97585` | `0,91439` | `0,73668` | `0,78548` | `0,37317` | `0,41440` |
| **45** | `6797,29` | `1,18249` | `0,72255` | `0,90677` | `1,43043` | `0,87846` | `0,96654` | `0,90273` | `0,74713` | `0,79725` | `0,37541` | `0,41759` |
| **50** *(Last)* | `7477,41` | `1,18799` | `0,71590` | `0,89916` | `1,45201` | `0,87948` | `0,97223` | `0,90261` | `0,74713` | `0,79753` | `0,37041` | `0,41312` |

---

### 4.b. Mô tả hình dạng đường cong huấn luyện bằng lời (`results.csv` & `results.png`)

1. **Giai đoạn khởi động và hội tụ nhanh (Epoch 1 $\rightarrow$ Epoch 15)**:
   - Ba hàm mất mát trên tập `train` và `val` đều giảm rất dốc: `train/cls_loss` rơi từ $4,462 \to 1,201$, `val/cls_loss` rơi từ $3,962 \to 1,206$; `mAP50` nhảy vọt từ $54,5\% \to 77,6\%$. Đây là lúc mạng thích nghi từ lớp tổng quát của COCO sang đặc trưng đầu người hồng ngoại. **[ĐÃ XÁC MINH]**
2. **Giai đoạn tinh chỉnh với Mosaic (Epoch 16 $\rightarrow$ Epoch 40)**:
   - Đường loss giảm chậm và đều đặn (`train/box_loss` từ $1,56 \to 1,45$; `val/box_loss` từ $1,70 \to 1,54$). `mAP50` đi ngang (dao động nhẹ trong dải hẹp $78,5\% - 81,0\%$) và đạt đỉnh ở **Epoch 35** (`mAP50 = 80,98%`, `mAP50-95 = 37,75%`). **[ĐÃ XÁC MINH]**
3. **Giai đoạn tắt Mosaic 10 epochs cuối (Epoch 41 $\rightarrow$ Epoch 50)**:
   - Ngay tại Epoch 41 khi `close_mosaic=10` kích hoạt, `train/box_loss` sụt bậc thang từ $1,446$ xuống $1,257$ rồi $1,182$ (vì ảnh đơn không ghép 4 dễ đoán hơn ảnh Mosaic). Đáng chú ý là `val/box_loss` cũng giảm từ $1,542$ xuống đáy $1,430$ ở Epoch 45 (không bị vọt ngược lên), trước khi nhích nhẹ lên $1,452$ ở Epoch 48–50. Trong khi đó `mAP50` đi ngang quanh $79,7\%$ và `mAP50-95` giữ ở $37,0\% - 37,5\%$. **[ĐÃ XÁC MINH]**

---

### 4.c. Minh bạch tập đo của từng chỉ số & Số lần sử dụng tập `test`

- **Các chỉ số trong `results.csv` (`Precision = 0.9023`, `Recall = 0.7586`, `mAP50 = 0.8098`, `mAP50-95 = 0.3775`)**:
  - Đo trên **tập `val`** gồm **22 ảnh / 87 khung đầu** (sau mỗi epoch từ 1 đến 50, tổng cộng 50 lần trong lúc train + 1 lần `model.val()` cuối script `train_official.py:67`). **[ĐÃ XÁC MINH]**
- **Tập `test` (43 ảnh / 168 khung đầu) đã được dùng bao nhiêu lần và để làm gì?**
  1. **Lần 1**: Trong Phase 5 (`tools/train_baseline.py:130`), `baseline_stage_a.pt` đã chạy dự đoán trên cả 43 ảnh `test` để tạo nhãn nháp vào `datasets/head_v2/labels_prelabel/test/`, sau đó người dùng mở sửa để làm nhãn Ground Truth cho tập `test`.
  2. **Lần 2**: Trong Phase 8 (`tools/eval_counts.py:155-315`), chạy đánh giá sai số đếm với `conf = 0.15` (chọn từ `val`) và `iou = 0.60`, xuất ra `reports/EVAL_REPORT_PHASE8.md`.
  3. **Lần 3**: Khảo sát độ nhạy ngưỡng `conf = 0.15, 0.20, 0.25, 0.30` trực tiếp trên tập `test` và ghi vào bảng Mục 5.2 của `reports/TRAINING_REPORT.md:100-106`, từ đó chọn `conf = 0.25` làm cấu hình mặc định cho `main.py:422`.
  4. **Lần 4**: Trong Phase 9b (`tools/test_api_regression.py:62,74`), dùng 2 ảnh của tập `test` (`0425s.jpg` và `0456s.jpg`) để chạy kiểm thử hồi quy API.
  - **Nội dung nguyên văn của `reports/EVAL_REPORT_PHASE8.md` (kết quả chạy `tools/eval_counts.py`)**:
    - Đã được đọc nguyên văn ở đầu lượt này: tại `conf = 0.15` (với `iou = 0.60`), trên 43 ảnh `test`: `MAE = 0.88 người/ảnh`, `RMSE = 1.56 người/ảnh`, `Exact Match = 55.8% (24/43 ảnh)`, `Đúng ±1 = 74.4% (32/43 ảnh)`, `Max Error = 5 người`; phân bố độ lệch: `0` (24 ảnh), `+1` (8 ảnh), `+2` (7 ảnh), `+3` (2 ảnh), `+5` (2 ảnh) — không có ảnh nào đếm thiếu ($<0$). **[ĐÃ XÁC MINH]**

---

### 4.d. Ngưỡng `conf` và NMS `iou`: Đối chiếu giữa `eval_counts.py` và `main.py`

Đây là một phát hiện kỹ thuật rất quan trọng khi kiểm toán code:

| Thành phần | Ngưỡng `conf` | Ngưỡng NMS `iou` | Nguồn gốc chọn ngưỡng | Có khớp nhau không? |
| :--- | :---: | :---: | :--- | :---: |
| **`BoxF1_curve.png` (Ultralytics Val)** | Đỉnh $F_1$ nằm ở vùng `conf ≈ 0.20 – 0.30` | `iou = 0.70` (mặc định `val`) | Đường cong $F_1$ trên tập `val` (22 ảnh) | — |
| **`tools/eval_counts.py` (Phase 8)** | **`conf = 0.15`** (`eval_counts.py:152`, `EVAL_REPORT_PHASE8.md:4,31`) | **`iou = 0.60`** (`eval_counts.py:49,63`) | Quét `conf` từ `0.15` đến `0.60` trên tập `val` (22 ảnh) tối ưu theo `MAE` đếm số lượng | **KHÔNG KHỚP** với `main.py` cả về `conf` lẫn `iou`! |
| **`ai_service/main.py` (Đang chạy thật)** | **`MODEL_CONF = 0.25`** (`main.py:422`) | **`iou = 0.70`** (do `main.py:92` không truyền tham số `iou`, dùng mặc định của Ultralytics) | Chọn `conf = 0.25` sau khi xem bảng khảo sát trên tập `test` (`TRAINING_REPORT.md:105`) | **Lệch cả `conf` (`0.25` vs `0.15`) và `iou` (`0.70` vs `0.60`)** |

- **Hệ quả thực tế của việc thiếu `iou=0.60` trong `main.py:92`**:
  - Ở `conf = 0.25`: Nếu có `iou = 0.60` (như trong `eval_counts.py`), sai số đếm trên tập `test` là `MAE = 0.44`, đúng $\pm 1$ đạt `95.3%`. Nhưng vì `main.py:92` chạy với `iou = 0.70` mặc định, một số đầu người có 2 khung dự đoán chồng lên nhau ở mức $\text{IoU} \in [0.60, 0.70)$ không bị NMS gộp lại, làm `MAE` trên tập `test` ở `conf = 0.25, iou = 0.70` tăng lên **`0.65 người/ảnh`** (đúng $\pm 1$ đạt `88.4%`). **[ĐÃ XÁC MINH - Output lệnh Mục 3 Phụ lục]**

---

### 4.e. Bảng Sai số Đếm đầy đủ trên tập `val` (22 ảnh) và `test` (43 ảnh)

Bảng dưới đây tổng hợp đầy đủ mọi chỉ số yêu cầu (`MAE`, `Trung vị |pred - gt|`, `Max |pred - gt|`, `RMSE`, `Độ lệch có dấu (pred - gt)`, tỉ lệ đúng tuyệt đối `0`, tỉ lệ sai không quá `±1` và `±2`) cho cả cấu hình `iou = 0.60` (`eval_counts.py`) và `iou = 0.70` (`main.py` hiện tại):

| Cấu hình (`best_head_v2.pt`) | Tập đo | MAE ($\|\text{pred}-\text{gt}\|$ TB) | Trung vị $\|\text{pred}-\text{gt}\|$ | Lớn nhất (`Max`) | RMSE | Độ lệch có dấu ($\text{pred}-\text{gt}$) | Đúng 100% (`0`) | Sai không quá `±1` | Sai không quá `±2` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `conf=0.15, iou=0.60` *(Phase 8)* | **Val (22 ảnh)** | `0,50` | `0,0` | `2` | `0,76` | `+0,05` | `59,1%` (13/22) | `95,5%` (21/22) | `100,0%` (22/22) |
| `conf=0.15, iou=0.60` *(Phase 8)* | **Test (43 ảnh)** | **`0,88`** | **`0,0`** | **`5`** | **`1,56`** | **`+0,88`** | **`55,8%` (24/43)** | **`74,4%` (32/43)** | **`90,7%` (39/43)** |
| `conf=0.25, iou=0.60` *(Báo cáo)* | **Test (43 ảnh)** | `0,44` | `0,0` | `3` | `0,88` | `+0,26` | `69,8%` (30/43) | `95,3%` (41/43) | `95,3%` (41/43) |
| `conf=0.15, iou=0.70` | **Val (22 ảnh)** | `0,77` | `1,0` | `3` | `1,19` | `+0,05` | `45,5%` (10/22) | `86,4%` (19/22) | `90,9%` (20/22) |
| `conf=0.15, iou=0.70` | **Test (43 ảnh)** | `1,49` | `1,0` | `7` | `2,15` | `+1,49` | `20,9%` (9/43) | `69,8%` (30/43) | `83,7%` (36/43) |
| **`conf=0.25, iou=0.70` (`main.py`)** | **Val (22 ảnh)** | **`0,64`** | **`0,0`** | **`3`** | **`1,09`** | **`-0,36`** | **`59,1%` (13/22)** | **`81,8%` (18/22)** | **`95,5%` (21/22)** |
| **`conf=0.25, iou=0.70` (`main.py`)** | **Test (43 ảnh)** | **`0,65`** | **`0,0`** | **`5`** | **`1,31`** | **`+0,47`** | **`62,8%` (27/43)** | **`88,4%` (38/43)** | **`90,7%` (39/43)** |

---

### 4.f. So sánh Baseline trên CÙNG khung hình và CÙNG cách đếm (`imgsz=800, iou=0.70`)

Để kiểm chứng khách quan xem quá trình huấn luyện có thực sự tạo ra giá trị hay không, cả 4 mô hình hiện có trên ổ đĩa được chạy trên **cùng 22 ảnh `val` và 43 ảnh `test`** với cùng hàm `model.predict(..., imgsz=800, classes=[0])` (xem Output nguyên văn tại Mục 3 Phụ lục):

| Mô hình so sánh | Lớp `0` là gì? | Tập đo | Ngưỡng `conf` | MAE (người/ảnh) | Trung vị lỗi | Độ lệch có dấu | Max Error | Đúng 100% | Sai $\le \pm 1$ | Sai $\le \pm 2$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. `yolov8n.pt` (Gốc COCO)** | `person` | **TEST (43 ảnh)** | `0.25` | **`3,91`** | `4,0` | **`-3,91`** | `6` | `9,3%` *(chỉ đúng 4 ảnh trống)* | `11,6%` | `11,6%` |
| **1. `yolov8n.pt` (Gốc COCO)** | `person` | **VAL (22 ảnh)** | `0.25` | **`4,00`** | `4,5` | **`-3,55`** | `6` | `9,1%` | `22,7%` | `22,7%` |
| **2. `best_v1.pt` (COCO128 v1)** | `person` | **TEST (43 ảnh)** | `0.25` | **`3,91`** | `4,0` | **`-3,91`** | `6` | `9,3%` *(chỉ đúng 4 ảnh trống)* | `11,6%` | `11,6%` |
| **2. `best_v1.pt` (COCO128 v1)** | `person` | **VAL (22 ảnh)** | `0.25` | **`3,91`** | `4,5` | **`-3,91`** | `6` | `13,6%` | `27,3%` | `31,8%` |
| **3. `baseline_stage_a.pt` (32 ảnh)** | `head` | **TEST (43 ảnh)** | `0.25` | **`1,47`** | `1,0` | `-1,47` | `5` | `27,9%` | `55,8%` | `79,1%` |
| **3. `baseline_stage_a.pt` (32 ảnh)** | `head` | **VAL (22 ảnh)** | `0.25` | **`0,86`** | `1,0` | `-0,59` | `3` | `40,9%` | `77,3%` | `95,5%` |
| **4. `best_head_v2.pt` (98 ảnh - Chính thức)** | `head` | **TEST (43 ảnh)** | `0.25` | **`0,65`** | **`0,0`** | **`+0,47`** | **`5`** | **`62,8%`** | **`88,4%`** | **`90,7%`** |
| **4. `best_head_v2.pt` (98 ảnh - Chính thức)** | `head` | **VAL (22 ảnh)** | `0.25` | **`0,64`** | **`0,0`** | **`-0,36`** | **`3`** | **`59,1%`** | **`81,8%`** | **`95,5%`** |

> **Nhận xét từ số liệu thực nghiệm**:
> - Trên 43 ảnh `test` (chiếu phim trong tối, trung bình $3,91\text{ người/ảnh}$), cả `yolov8n.pt` gốc lẫn `best_v1.pt` ở `conf=0.25` đều có **`MAE = 3.91` và `Signed Error = -3.91`** — tức là **dự đoán `0 người` trên toàn bộ 43/43 ảnh** (chỉ ăn may đúng 4/43 ảnh=9,3% vì 4 ảnh đó vốn là phòng trống 0 người!). Lý do: lớp `person` của COCO cần thấy cả thân người, trong khi ghế rạp phim che mất 80% cơ thể. **[ĐÃ XÁC MINH]**
> - Khi chuyển sang học lớp `head` với 32 ảnh (`baseline_stage_a.pt`), `MAE` trên `test` giảm từ `3,91` xuống `1,47`. Khi tăng lên 98 ảnh (`best_head_v2.pt`), `MAE` giảm tiếp hơn một nửa xuống còn **`0,65`** (và còn **`0,44`** nếu bật `iou=0.60`). **[ĐÃ XÁC MINH]**

---

## PHẦN 5: KIỂM TOÁN TRUNG THỰC (PHẦN QUAN TRỌNG NHẤT)

### 1. Rò rỉ dữ liệu (Data Leakage)
- **Bằng chứng**:
  - Cả 3 tập `train` (98 ảnh), `val` (22 ảnh) và `test` (43 ảnh) đều được trích từ **cùng 1 tệp video duy nhất** `C:\Users\Dell KIM ANH\Downloads\cam_edited.mp4`, cùng 1 phòng chiếu (`room1`), cùng 1 góc lắp camera cố định, và trong cùng 1 khoảng thời gian dài 9 phút 38 giây (`datasets/head_v2/manifest.csv:2-164`). **[ĐÃ XÁC MINH]**
  - Khoảng cách thời gian nhỏ nhất giữa `train` và `val` là **$2,5\text{ giây}$** (`343,5s` vs `346,0s`), giữa `val` và `test` là **$5,5\text{ giây}$** (`419,5s` vs `425,0s`), và giữa `train` với `test` là **$81,5\text{ giây}$** (`343,5s` vs `425,0s`). **[ĐÃ XÁC MINH]**
  - Hơn nữa, nhóm khán giả ngồi ở khu vực hàng giữa (`G, H, I`, cột `5–8`) trong đoạn `test` (`425s – 572s`) có vị trí ghế, kiểu tóc và phản xạ hồng ngoại gần như trùng khớp với nhóm khán giả đã xuất hiện trong `train` và `val` vài chục giây trước đó. **[SUY LUẬN từ tọa độ nhãn trong `manifest.csv` và `prelabels_metadata.json`]**
  - Ngoài ra, ngưỡng `MODEL_CONF = 0.25` đang dùng trong `main.py` được chọn sau khi lập bảng khảo sát sai số trực tiếp trên tập `test` (`reports/TRAINING_REPORT.md:100-106`). **[ĐÃ XÁC MINH]**
- **Kết luận mức độ rủi ro**: **CAO (HIGH)** đối với khả năng tổng quát hóa sang phòng khác / ngày khác / nhóm khách khác; **VỪA (MEDIUM)** nếu chỉ xét trong phạm vi demo cố định tại đúng phòng `room1` đó.
- **Hệ quả & Số nào KHÔNG được ghi vào báo cáo như "độ chính xác thực tế"**:
  - Các con số **`mAP@50 = 81,0%`**, **`Test MAE = 0,88` (hay `0,44`)**, và **`Đúng ±1 = 95,3%`** bị thổi phồng do mô hình đã nhìn thấy chính nền ghế đó và chính những cái đầu người đó ở các giây liền kề trong tập `train`.
  - **Tuyệt đối KHÔNG được ghi**: *"Mô hình đạt độ chính xác đếm thực tế 95,3% ở mọi phòng chiếu"* mà phải ghi đúng bản chất: *"Đạt 88,4% – 95,3% (sai số $\le \pm 1$) trên phân đoạn kiểm thử độc lập theo thời gian của cùng góc máy `room1` với quy mô 0–6 khách"*.

### 2. Quá khớp (Overfitting)
- **So sánh `train loss` và `val loss` (`runs/detect/head_v2_official/results.csv`)**:
  - Tại Epoch 1: `train/box_loss = 2.119` vs `val/box_loss = 2.000` (chênh `-0.119`).
  - Tại Epoch 35 (Best): `train/box_loss = 1.459` vs `val/box_loss = 1.549` (chênh `+0.090`); `train/cls_loss = 0.972` vs `val/cls_loss = 0.943`.
  - Tại Epoch 50 (Last, sau khi tắt Mosaic): `train/box_loss = 1.188` vs `val/box_loss = 1.452` (độ chênh nới rộng lên **`+0.264`**); `train/cls_loss = 0.716` vs `val/cls_loss = 0.879` (chênh **`+0.163`**). Từ Epoch 45 đến 50, `val/box_loss` bắt đầu nhích tăng nhẹ từ `1.430` lên `1.452` và `mAP50-95` giảm nhẹ từ `0.3754` xuống `0.3704`. **[ĐÃ XÁC MINH]**
- **Đánh giá độ đa dạng**:
  - Mặc dù trên đồ thị `results.png`, `val loss` không bị vọt ngược lên mạnh (nhờ tập `val` lấy từ cùng video và cùng góc máy với `train`), nhưng bộ dữ liệu **98 ảnh `train` lấy cách nhau 3,5 giây từ cùng 1 cảnh tĩnh** có mức độ trùng lặp nền (background redundancy) cực cao. Mô hình có nguy cơ đã "học thuộc lòng" kết cấu thành ghế và bóng đèn phản xạ tại từng tọa độ $(x, y)$ cố định của `room1` (ví dụ: tại `EVAL_REPORT_PHASE8.md:44-62`, khi ánh sáng màn hình chiếu thay đổi ở Suất 2 làm bóng ghế sáng lên, mô hình lập tức đoán nhầm bóng ghế thành người, gây lệch dương `+1` đến `+5`). **[ĐÃ XÁC MINH]**

### 3. Độ đa dạng của dữ liệu & Các điều kiện CHƯA được kiểm tra
- **Đã có trong dữ liệu**:
  - **Số phòng**: **1 phòng duy nhất** (`room1`). **[ĐÃ XÁC MINH]**
  - **Số góc camera**: **1 góc cố định duy nhất**. **[ĐÃ XÁC MINH]**
  - **Mức độ đông khách (phân bố số đầu/ảnh trên 163 ảnh)**: Chỉ từ **0 đến 6 khách/ảnh** (`0 đầu`: 7 ảnh; `1 đầu`: 4 ảnh; `3 đầu`: 4 ảnh; `4 đầu`: 33 ảnh; `5 đầu`: 13 ảnh; `6 đầu`: 102 ảnh; **không có ảnh nào có 2 đầu, và không có ảnh nào $> 6$ đầu**). **[ĐÃ XÁC MINH]**
  - **Che khuất (Occlusion)**: Chỉ có 1 tình huống 2 khách ngồi cạnh chụm đầu vào nhau ở khu vực hàng giữa (khoảng 4 ảnh `22–25`, theo `TRAINING_REPORT.md:51`), chưa có cảnh hàng ghế trước ngồi kín che khuất hàng ghế sau. **[ĐÃ XÁC MINH]**
- **Các điều kiện CHƯA được kiểm tra (0 ảnh)**:
  1. **Phòng chiếu khác (`room2, room3, room4`)** với kiểu ghế, độ dốc sàn hoặc tiêu cự ống kính khác.
  2. **Suất chiếu đông khách** (ví dụ 30 – 135 khách/phòng, khi các đầu người xếp sát nhau tạo thành đám đông dày đặc và che khuất chồng lớp giữa các hàng).
  3. **Ánh sáng ban ngày / đèn vệ sinh công suất lớn / cảnh trailer chớp sáng mạnh** chiếu thẳng vào hàng ghế đầu `A, B, C`.
  4. **Khán giả ngồi ở các hàng rất gần màn hình (`A, B, C, D`) hoặc sát tường cuối (`K, L`) và hai rìa trái/phải**: Trong `labels.jpg` và `prelabels_metadata.json`, gần như toàn bộ 825 nhãn đầu đều tập trung ở vùng trung tâm ảnh ($x_c \in [0.44, 0.52], y_c \in [0.14, 0.30]$ — tức khu vực hàng `G, H, I`). **[ĐÃ XÁC MINH]**

### 4. Độ tin cậy của nhãn & Hiện tượng "Mô hình tự học lại chính nó" (Confirmation Bias)
- **Bằng chứng số lượng**:
  - Tỉ lệ nhãn **chỉ do người gán tay từ đầu**: **40 / 163 ảnh (24,5%)** (`32/98 = 32,7%` trong tập `train`, `8/22 = 36,4%` trong tập `val`, và **`0/43 = 0,0%` trong tập `test`**). **[ĐÃ XÁC MINH]**
  - Trong 66 ảnh `train` còn lại (Giai đoạn B), có **28 ảnh (28,6% tập `train`)** được người dùng chỉnh sửa khung so với bản nháp của `baseline_stage_a.pt`, nhưng có **38 ảnh (38,8% tập `train`)** được người dùng bấm duyệt giữ nguyên 100% khung nháp của `baseline_stage_a.pt`. **[ĐÃ XÁC MINH]**
- **Đánh giá rủi ro**:
  - Việc 38,8% ảnh `train` giữ nguyên tọa độ khung của `baseline_stage_a.pt` giải thích vì sao `best_head_v2.pt` hội tụ rất mượt nhưng điểm `mAP@50-95` (đòi hỏi khung bao cực kỳ khít ở ngưỡng $\text{IoU} = 0,50 \to 0,95$) dừng ở mức **$37,75\%$**: những sai lệch viền khung 2–4 pixel của mô hình nháp `baseline_stage_a.pt` đã được "đóng băng" thành nhãn Ground Truth trong 38 ảnh `train` và 9 ảnh `test`. Tuy nhiên, vì người dùng đã trực tiếp vẽ bù thêm **+99 khung đầu bị sót** trên 73 ảnh đã sửa, rủi ro bỏ sót cả cái đầu đã được giảm đáng kể. **[SUY LUẬN có căn cứ từ Mục 2.d]**

### 5. Kích thước đầu người so với `imgsz = 800` & Khả năng bỏ sót đầu ở xa
- **Thống kê kích thước sau khi thu về `imgsz = 800` ($800\times 450\text{ px}$)**:
  - Trên toàn bộ 825 đầu: chỉ có **2 đầu (0,24%)** có chiều cao $H < 8\text{ px}$, **5 đầu (0,61%)** có chiều rộng $W < 8\text{ px}$ (tổng cộng **6/825 đầu = 0,73%** có cạnh nhỏ nhất $\min(W, H) < 8\text{ px}$).
  - Có **49/825 đầu (5,94%)** có chiều cao $H < 12\text{ px}$ và **173/825 đầu (20,97%)** có $\min(W, H) < 12\text{ px}$. **[ĐÃ XÁC MINH - Output lệnh Mục 4 Phụ lục]**
- **Điểm Recall thực tế đo theo kích thước đầu (`best_head_v2.pt`, khớp ở $\text{IoU} \ge 0,50$)**:
  - **Trên tập `val` (22 ảnh, 87 đầu)**:
    - Với nhóm **đầu nhỏ ở xa** (chiều cao sau thu nhỏ $H_{\text{800}} < 12\text{ px}$, tương ứng $H_{\text{gốc}} < 28,8\text{ px}$, gồm 7 đầu): Recall chỉ đạt **`1/7 = 14,3%`** (ở `conf=0.25`) và **`2/7 = 28,6%`** (ở `conf=0.15`)!
    - Với nhóm **đầu lớn hơn** ($H_{\text{800}} \ge 12\text{ px}$, gồm 80 đầu): Recall đạt **`65/80 = 81,2%`** (ở `conf=0.25`) và **`66/80 = 82,5%`** (ở `conf=0.15`).
  - **Trên tập `test` (43 ảnh, 168 đầu)**:
    - Với nhóm **đầu nhỏ** ($H_{\text{800}} < 12\text{ px}$, gồm 12 đầu): Recall đạt **`9/12 = 75,0%`** (ở `conf=0.25`) và **`10/12 = 83,3%`** (ở `conf=0.15`).
    - Với nhóm **đầu lớn hơn** ($H_{\text{800}} \ge 12\text{ px}$, gồm 156 đầu): Recall đạt **`140/156 = 89,7%`** (ở `conf=0.25`) và **`145/156 = 92,9%`** (ở `conf=0.15`).
  - **Kết luận**: Ngay cả ở `imgsz=800`, mô hình **vẫn bỏ sót tới 71% – 85% các đầu nhỏ ($H_{\text{800}} < 12\text{ px}$) trên tập `val`**, chứng tỏ khi khách ngồi ở các hàng xa camera nhất hoặc cúi thấp đầu làm chiều cao hộp dưới $28\text{ px}$ trên ảnh Full HD, mạng YOLOv8n (stride nhỏ nhất là $8\text{ px}$) rất dễ đánh mất đặc trưng. **[ĐÃ XÁC MINH - Output lệnh Mục 4 Phụ lục]**

### 6. Ba kết luận ĐƯỢC PHÉP nói với giảng viên & Ba điều KHÔNG ĐƯỢC khẳng định

- **3 kết luận ĐƯỢC PHÉP nói (Có căn cứ 100% từ dữ liệu thật)**:
  1. *"Trên video camera hồng ngoại thực tế của rạp chiếu phim trong điều kiện tắt đèn, mô hình YOLOv8n gốc của COCO (lớp `person`) thất bại hoàn toàn (bỏ sót 100% khán giả ở ngưỡng `conf=0.25`, `MAE = 3,91 người/ảnh`), trong khi việc chuyển sang bài toán phát hiện riêng vùng đầu (`head`) ở độ phân giải `imgsz=800` đã giúp mô hình nhận diện được khán giả với `MAE = 0,65 người/ảnh` (và `0,44 người/ảnh` khi chỉnh `iou=0.60`) trên phân đoạn kiểm thử."*
  2. *"Quy trình gán nhãn bán tự động 2 giai đoạn (gán tay 40 ảnh hạt giống $\to$ huấn luyện `baseline_stage_a.pt` sinh nhãn nháp cho 123 ảnh $\to$ con người duyệt và vẽ bù thêm 99 đầu bị sót) giúp tiết kiệm khoảng 60% thời gian gán nhãn thủ công mà vẫn nâng `mAP@50-95` trên tập `val` từ 26,3% lên 37,8%."*
  3. *"Toàn bộ luồng tích hợp kỹ thuật từ nhận ảnh qua `POST /api/v1/analyze`, suy luận bằng `models/best_head_v2.pt`, lấy tâm hộp đầu $(x_c, y_c)$, kiểm tra điểm trong đa giác ghế (`cv2.pointPolygonTest`) đến đối chiếu với tập vé đã quét từ ứng dụng Flutter để sinh cảnh báo vào SQLite đã chạy thông suốt end-to-end."*

- **3 điều TUYỆT ĐỐI KHÔNG ĐƯỢC khẳng định (Vì chưa đủ căn cứ hoặc sai sự thật)**:
  1. *"Mô hình đạt độ chính xác 95,3% (hoặc mAP 81%) cho mọi phòng chiếu và mọi suất chiếu trong thực tế"* — **Sai**, vì toàn bộ 163 ảnh `train/val/test` chỉ lấy từ 1 video duy nhất dài 9 phút 38 giây của 1 phòng chiếu với tối đa 6 khách.
  2. *"Tập Test hoàn toàn độc lập, không có bất kỳ sự rò rỉ thông tin nào từ tập Train/Val"* — **Sai**, vì tập `test` nằm cách tập `val` chỉ 5,5 giây trên cùng 1 tệp video, cùng góc máy, và ngưỡng `conf=0.25` đang dùng trong `main.py` được chốt sau khi đã xem kết quả trên tập `test`.
  3. *"Hệ thống đã định vị chính xác tuyệt đối 135 ghế của cả 4 phòng chiếu trong mọi tình huống"* — **Sai**, vì `seats_config_room1..4.json` hiện tại được nội suy hình học từ 1 ảnh chụp màn hình và nhân bản giống hệt cho cả 4 phòng, đồng thời chưa hề được kiểm nghiệm khi phòng có từ 7 đến 135 khách ngồi.

### 7. Kế hoạch kiểm tra khắt khe và rẻ nhất (Low-cost Strict Validation Plan)
- **Mục tiêu**: Biết được độ chính xác **thực chất** của `models/best_head_v2.pt` khi không còn hiệu ứng "nhớ cảnh/nhớ khách" mà chỉ tốn khoảng **45 – 60 phút công sức**.
- **Kế hoạch cụ thể**:
  1. **Chọn video nào**: Lấy **1 đoạn video mới dài 5 – 10 phút** quay vào **một ngày khác hoặc suất chiếu khác hoàn toàn** (ưu tiên suất chiếu có từ **15 – 40 khán giả** ngồi rải rác ở cả hàng đầu `A–D`, hàng giữa `E–I` và hàng cuối `J–L`; nếu có video của `room2` thì càng tốt).
  2. **Trích bao nhiêu khung**: Dùng `tools/extract_frames.py` với `step_sec = 10.0` giây để trích ra đúng **35 – 40 khung hình** (cách xa nhau 10 giây để các khung không giống nhau).
  3. **Gán nhãn**: Dùng `tools/label_heads_cv.py` gán nhãn tay (hoặc sửa nhãn nháp) cho 35–40 khung này (mất khoảng 30 phút).
  4. **Đo lường cố định**: Chạy `eval_counts.py` ở chế độ chỉ đánh giá (không quét chọn lại ngưỡng!) tại đúng cấu hình đang dùng (`conf = 0.25, iou = 0.60` và `iou = 0.70`, `imgsz = 800`). Con số `MAE` và `Recall` thu được trên 35–40 khung này mới chính là **độ chính xác thực tế ngoài đời** của mô hình.

---

## PHẦN 6: GIẢNG KHÁI NIỆM ML BẰNG SỐ LIỆU CỦA CHÍNH LẦN CHẠY NÀY (DÀNH CHO FRONTEND DEV)

### 1. YOLO phát hiện vật thể thế nào (Lưới / Grid, Khung bao / Bounding Box, Độ tin cậy / Confidence)
- **Giải thích**: Thay vì quét ảnh nhiều lần như vòng lặp lồng nhau, YOLO ("You Only Look Once") chia bức ảnh đầu vào `imgsz = 800` ($800\times 800\text{ px}$) thành 3 lưới ô vuông ở 3 độ mịn khác nhau (bước nhảy $8\text{ px}, 16\text{ px}, 32\text{ px}$ — tạo ra tổng cộng $800/8\times 800/8 + \dots = 13.125$ điểm neo dự đoán). Tại mỗi ô lưới, mô hình đồng thời trả về tọa độ khung hình chữ nhật `[x_center, y_center, width, height]` và một điểm số **Confidence** $\in [0, 1]$ thể hiện xác suất "ô này thực sự chứa một cái đầu người".
- **Con số thật từ lần chạy**: Trên ảnh `train/room1_cam_edited_0004s.jpg`, mô hình xuất ra 5 khung đầu với điểm `conf` lần lượt là **`0.7155`, `0.6569`, `0.5663`, `0.5052`, `0.3931`** (`reports/prelabels_metadata.json:6-49`).
- **So sánh với Web/App**: Giống như một `GridView.builder` trong Flutter chia màn hình thành hàng nghìn ô nhỏ; mỗi ô là một component tự tính toán xem có phần tử DOM/Widget (`head`) nào đang nằm tại vị trí của nó không và trả về `{ rect: {x, y, w, h}, score: 0.72 }`.

### 2. Transfer Learning (Học chuyển giao — Vì sao bắt đầu từ `yolov8n.pt` chứ không từ số 0?)
- **Giải thích**: Một mạng nơ-ron thị giác cần hàng chục lớp đầu tiên (Backbone) chỉ để học cách nhận biết những nét cơ bản nhất như cạnh thẳng, đường cong, góc tối, độ tương phản sáng–tối. Thay vì khởi tạo 3,2 triệu trọng số bằng các số ngẫu nhiên (`Math.random()`) rồi bắt nó học từ chỉ **98 ảnh rạp phim**, ta nạp tệp `yolov8n.pt` (`6,55 MB`) vốn đã được huấn luyện sẵn trên 118.000 ảnh của bộ COCO, rồi chỉ thay "đầu ra cuối cùng" (Detection Head) từ 80 lớp đồ vật thành **1 lớp duy nhất (`nc: 1`, `0: head`)**.
- **Con số thật từ lần chạy**: Nhờ bắt đầu từ `yolov8n.pt` (`runs/detect/head_v2_official/args.yaml:3`), ngay ở **Epoch 1** (chỉ sau 162,7 giây), mô hình đã đạt **`mAP@50 = 54,54%`** trên tập `val` (`results.csv:2`) — điều không thể xảy ra nếu học từ con số 0 với 98 ảnh.
- **So sánh với Web/App**: Giống như khi bạn làm app thương mại điện tử bằng React/Flutter, bạn cài bộ UI Kit chuẩn (Material UI / Ant Design) đã xử lý sẵn layout, typography, animation rồi chỉ custom lại CSS theme cho thương hiệu của bạn, thay vì tự viết lại bộ dựng chữ từ WebGL/Canvas thuần.

### 3. Epoch, Batch và Learning Rate (`lr0`, `lrf`)
- **Giải thích**:
  - **Batch (`batch = 4`)**: Vì CPU/RAM không nên nuốt cả 98 ảnh cùng một lúc để tính đạo hàm, dữ liệu được cắt thành từng lô nhỏ gồm **4 ảnh**; cứ xem xong 4 ảnh thì mô hình sửa trọng số 1 lần (1 iteration).
  - **Epoch (`epochs = 50`)**: Một **Epoch** là khi mô hình duyệt hết toàn bộ mảng 98 ảnh `train` đúng 1 lượt ($\lceil 98 / 4 \rceil = 25\text{ batches}$). Huấn luyện 50 epochs nghĩa là duyệt đi duyệt lại mảng 98 ảnh đó 50 lần.
  - **Learning Rate (`lr0 = 0.01` $\to$ `lrf = 0.01`)**: Là "bước nhảy" mỗi lần mô hình sửa trọng số; ở những epoch đầu bước nhảy lớn (`~0.0033`) để tiến nhanh tới vùng đúng, sau đó giảm dần về cuối (`0.000298` ở Epoch 50 trong `results.csv:51`) để không bị văng khỏi điểm tối ưu.
- **Con số thật từ lần chạy**: Với `batch = 4` và `epochs = 50` (`args.yaml:5,8`), mô hình đã thực hiện tổng cộng $25 \times 50 = \mathbf{1.250\text{ lần cập nhật trọng số}}$, mỗi epoch mất trung bình **149,55 giây**.
- **So sánh với Web/App**: Một **Epoch** giống như 1 vòng lặp `for (const batch of chunk(trainImages, 4))` duyệt hết toàn bộ bộ `test fixtures`; **Batch = 4** giống như phân trang `pageSize = 4` khi gọi API; còn **Learning Rate** giống như độ nhạy thanh trượt (step size) khi bạn tinh chỉnh tọa độ CSS (`10px` lúc căn thô ban đầu, giảm xuống `0.1px` lúc căn khít pixel cuối cùng).

### 4. Ba hàm mất mát: `box_loss`, `cls_loss` và `dfl_loss`
- **Giải thích**: Hàm mất mát (**Loss**) là điểm "phạt" đo mức độ sai lệch giữa dự đoán của mô hình và nhãn thật (càng nhỏ càng tốt, giống số lượng lỗi lint/test fail). YOLOv8 tách điểm phạt thành 3 phần:
  1. **`box_loss`** (Trọng số `7.5`): Phạt khi khung hình chữ nhật dự đoán bị lệch tâm hoặc sai kích thước so với khung nhãn thật (dựa trên chỉ số chồng lấp CIoU).
  2. **`cls_loss`** (Trọng số `0.5`): Phạt khi mô hình phân loại sai "đây là đầu người (`head`)" hay "đây chỉ là nền ghế trống (`background`)".
  3. **`dfl_loss`** (Distribution Focal Loss, trọng số `1.5`): Phạt khi đường viền 4 cạnh của khung bao bị nhòe, không sắc nét tại ranh giới chỏm tóc/cằm.
- **Con số thật từ lần chạy**: Từ Epoch 1 đến Epoch 35 (tốt nhất), trên tập `val`, `box_loss` giảm từ **`2,0002` xuống `1,5491`**, `cls_loss` giảm mạnh từ **`3,9623` xuống `0,9427`**, và `dfl_loss` giảm từ **`1,2509` xuống `1,0084`** (`results.csv:2,36`).
- **So sánh với Web/App**: Giống như khi chấm điểm giao diện tự động (Visual Regression Test): `cls_loss` là lỗi render nhầm thẻ `<Button>` vào chỗ trống (sai loại component), `box_loss` là lỗi đặt lệch tọa độ `top/left/width/height` của `<div class="head">`, còn `dfl_loss` là lỗi nhòe viền `border-box` do căn sub-pixel chưa chuẩn.

### 5. IoU (Intersection over Union — Độ chồng lấp khung)
- **Giải thích**: **IoU** đo xem khung dự đoán của AI ($A$) và khung nhãn thật của bạn ($B$) trùng khít nhau đến mức nào, bằng cách lấy **Diện tích phần giao nhau ($A \cap B$) chia cho Diện tích phần hợp nhau ($A \cup B$)**. Nếu hai khung đè khít 100% thì $\text{IoU} = 1,0$; nếu không chạm nhau thì $\text{IoU} = 0,0$; trong bài toán nhận diện, một khung dự đoán thường được công nhận là "Bắt trúng (True Positive)" khi **$\text{IoU} \ge 0,50$** (trùng ít nhất một nửa diện tích).
- **Con số thật từ lần chạy**: Trong bước kiểm định chất lượng nhãn (`reports/TRAINING_REPORT.md:56`), toàn bộ 825 khung đầu được quét kiểm tra và có **0 cặp khung nào đè lên nhau vượt ngưỡng `IoU > 0.90`**.
- **So sánh với Web/App**: Giống hệt bài toán kiểm tra va chạm (**Collision Detection / Hitbox Overlap**) giữa 2 phần tử DOM bằng `getBoundingClientRect()` trong game 2D JavaScript hoặc kéo-thả (drag-and-drop) trên giao diện.

### 6. NMS (Non-Maximum Suppression — Lọc bỏ khung trùng lặp)
- **Giải thích**: Vì YOLO có tới 13.125 ô lưới cùng dự đoán, một cái đầu người thật thường bị 3–5 ô lưới đứng cạnh nhau cùng vẽ khung bao quanh (với `conf` مثلاً `0.78`, `0.62`, `0.45`). Thuật toán **NMS** sẽ giữ lại khung có `conf` cao nhất (`0.78`), rồi kiểm tra tất cả các khung còn lại: khung nào đè lên khung `0.78` đó với độ chồng lấp **$\text{IoU} > \text{iou\_threshold}$** thì bị xóa bỏ vì đang chỉ vào cùng 1 cái đầu.
- **Con số thật từ lần chạy**: Trên 43 ảnh `test` ở cùng `conf = 0.25`, khi đặt ngưỡng NMS `iou = 0.60` (`tools/eval_counts.py:63`), các khung đè nhau từ 60% trở lên bị gộp sạch nên sai số đếm chỉ là **`MAE = 0,44`**; nhưng trong `main.py:92` để mặc định `iou = 0.70`, các khung đè nhau ở mức $60\% - 69\%$ không bị xóa nên đếm thừa thành 2 người, đẩy sai số lên **`MAE = 0,65`**.
- **So sánh với Web/App**: Giống hệt hàm **`debounce()` / `lodash.uniqWith()`** khi người dùng bấm đúp nút Submit hoặc khi bạn gộp các marker bản đồ nằm quá sát nhau (`distance < threshold` thì gộp thành 1 marker duy nhất).

### 7. Precision, Recall, `mAP@0.5` và `mAP@0.5:0.95`
- **Giải thích bằng chính con số tại Epoch 35 (`results.csv:36`, tập `val` gồm 22 ảnh / 87 đầu thật)**:
  - **Precision (`0,9023` $\approx 90,2\%$)**: Độ chuẩn xác khi "nổ súng". Nghĩa là cứ 100 cái khung mà mô hình khoanh và bảo "đây là đầu người", thì có **~90 khung là đầu người thật**, còn **~10 khung là báo nhầm** (khoanh nhầm lưng ghế hoặc bóng phản xạ hồng ngoại).
  - **Recall (`0,7586` $\approx 75,9\%$)**: Độ phủ (không bỏ sót). Nghĩa là trong **87 cái đầu thật** có mặt trên 22 ảnh `val`, mô hình **tìm thấy được 66 cái đầu** ($66 / 87 = 75,86\%$), và **bỏ sót mất 21 cái đầu** (chủ yếu là các đầu nhỏ ở xa hoặc lúc khách đang di chuyển ở lối đi).
  - **`mAP@0.5` (`0,8098` $\approx 81,0\%$)**: Điểm trung bình tổng hợp cả Precision và Recall trên mọi mức ngưỡng `conf`, với điều kiện dễ tính là chỉ cần khung dự đoán trùng với khung thật từ **50% diện tích trở lên ($\text{IoU} \ge 0,50$)**.
  - **`mAP@0.5:0.95` (`0,3775` $\approx 37,8\%$)**: Điểm trung bình khắt khe nhất, tính trung bình của 10 mức IoU từ `0,50` (trùng vừa) đến `0,95` (trùng khít gần như tuyệt đối từng milimet). Con số `37,8%` cho thấy mô hình xác định **vị trí có đầu người** khá tốt (`mAP@0.5 = 81%`), nhưng viền khung dự đoán vẫn lệch vài pixel so với khung vẽ tay (với đầu rộng chỉ `14 px` ở `imgsz=800`, lệch `2 px` đã làm IoU tụt mạnh!).
- **So sánh với Web/App**: Giống tính năng **Tìm kiếm (Search / Filter)**: **Recall** là tìm ra được bao nhiêu % kết quả đúng đang có trong Database (không bỏ sót), **Precision** là trong các kết quả hiện lên màn hình có bao nhiêu % thực sự đúng ý người dùng (không lẫn rác), **`mAP@0.5`** là chấm điểm chức năng tìm kiếm tương đối (fuzzy match), còn **`mAP@0.5:0.95`** là chấm điểm cả độ khớp chính xác từng ký tự (exact match).

### 8. Ngưỡng `conf` (Confidence Threshold) & Sự đánh đổi trực tiếp tới Cảnh báo "Khách lậu" vs "Vắng mặt"
- **Giải thích**: Ngưỡng `conf` là cái "phễu lọc" `boxes.filter(b => b.conf >= MODEL_CONF)` trước khi đưa tọa độ đầu vào bản đồ ghế.
  - Nếu **hạ `conf` xuống thấp (ví dụ `0.15`)**: Phễu mở rộng $\rightarrow$ bắt được cả những đầu mờ (giảm bỏ sót / giảm cảnh báo giả **"Khách vắng mặt"** `missing_guests`), nhưng lại để lọt nhiều bóng phản xạ trên ghế trống thành người $\rightarrow$ làm **tăng vọt cảnh báo giả "Khách lậu không vé"** (`illegal_occupants`).
  - Nếu **nâng `conf` lên cao (ví dụ `0.45 – 0.50`)**: Phễu siết chặt $\rightarrow$ hết báo nhầm ghế trống thành người (giảm cảnh báo giả **"Khách lậu"**), nhưng những khán giả ngồi hàng xa hoặc cúi đầu có `conf = 0.28` sẽ bị lọc mất $\rightarrow$ hệ thống tưởng ghế đó trống dù đã soát vé, làm **tăng vọt cảnh báo giả "Có vé nhưng vắng mặt"** (`missing_guests`).
- **Con số thật từ lần chạy**: Trên 43 ảnh `test`, khi để `conf = 0.15` (`EVAL_REPORT_PHASE8.md:19-25`), mô hình không bỏ sót khách nào (`0 ảnh đếm thiếu`) nhưng báo thừa ở **19/43 ảnh** (`MAE = 0,88`, tổng lệch dương `+38 người`); khi nâng lên `conf = 0.25`, số lần báo thừa giảm mạnh giúp `MAE` hạ xuống **`0,44`** (ở `iou=0.60`) và **`0,65`** (ở `iou=0.70`), nhưng nếu nâng tiếp lên `conf = 0.50` trên tập `val` thì `MAE` lại vọt lên **`1,50 người/ảnh`** do bỏ sót khách (`EVAL_REPORT_PHASE8.md:38`).

### 9. Overfitting (Quá khớp) & Vì sao bắt buộc phải có tập `val` / `test`?
- **Giải thích**: **Overfitting** xảy ra khi mô hình không học đặc trưng tổng quát của "đầu người" mà lại đi "học vẹt" vị trí tọa độ, nếp gấp vải ghế hoặc đốm sáng cố định trong 98 ảnh `train`. Nếu chỉ nhìn điểm trên tập `train`, bạn sẽ tưởng mô hình ngày càng giỏi, nhưng khi đưa ảnh mới vào thì nó đoán sai. Tập **`val`** đóng vai trò giám khảo chấm điểm sau mỗi epoch để biết lúc nào mô hình bắt đầu học vẹt (nhằm lấy `best.pt`), còn tập **`test`** là bài thi cuối kỳ độc lập không được chạm vào trong lúc học.
- **Con số thật từ lần chạy**: Ở Epoch 50, `train/box_loss` giảm xuống tận **`1,188`** (thấp hơn rất nhiều so với Epoch 35 là `1,459`), nhưng điểm trên tập `val` (`mAP@50-95`) ở Epoch 50 lại chỉ đạt **`0,3704`**, thấp hơn đỉnh **Epoch 35 (`0,3775`)** (`results.csv:36,51`). Nhờ có tập `val`, Ultralytics đã giữ lại trọng số Epoch 35 thay vì lấy Epoch 50.
- **So sánh với Web/App**: Overfitting giống hệt việc một lập trình viên lười viết thuật toán tính thuế mà dùng câu lệnh `if (input === 100) return 10; if (input === 200) return 20;` (**hardcode đáp án**) cho đúng 98 ca trong file `unit_test.spec.js`: chạy test локаl thì pass 100%, nhưng người dùng nhập `150` trên production thì hàm trả về `undefined`.

### 10. Vì sao phải chia tập theo Phiên/Đoạn thời gian chứ không chia ngẫu nhiên theo từng khung (`Random Split`)?
- **Giải thích**: Trong một video quay liên tục 30 khung hình/giây, khung hình ở giây thứ `10,0s` và giây thứ `13,5s` trong rạp chiếu phim gần như **giống hệt nhau tới 99%** (cùng 6 khán giả ngồi yên một chỗ xem phim, cùng ánh sáng màn hình). Nếu bạn gộp 163 ảnh lại rồi dùng `Math.random()` bốc ngẫu nhiên 70% vào `train`, 15% vào `val`, 15% vào `test`, thì chắc chắn ảnh ở giây `10,0s` sẽ nằm trong `train` còn ảnh ở giây `13,5s` nằm trong `test` — bài thi `test` biến thành "nhìn đáp án đã học cách đó 3,5 giây".
- **Con số thật từ lần chạy**: `tools/extract_frames.py:114-129` đã chia theo 4 dải thời gian (`0–265s` và `270–345s` cho `train`; `345–422s` cho `val`; `425–575s` cho `test`). Tuy nhiên, như đã chỉ ra ở Phần 2.c và Phần 5.1, vì cả 4 dải thời gian này vẫn nằm trong **cùng 1 tệp video dài 9,6 phút**, ranh giới giữa `train` (`343,5s`) và `val` (`346,0s`) vẫn chỉ cách nhau **2,5 giây**, nên mới giải quyết được một nửa bài toán chống rò rỉ; chuẩn mực cao nhất là mỗi tập phải lấy từ **một suất chiếu/ngày quay khác nhau hoàn toàn**.
- **So sánh với Web/App**: Chia ngẫu nhiên trên cùng 1 video giống như bạn test hiệu năng bộ nhớ đệm (`Cache`) bằng cách gửi 2 request giống hệt nhau cách nhau 3 giây rồi kết luận "Database query nhanh 1ms", trong khi thực tế request thứ 2 chỉ đang đọc lại kết quả đã cache từ request thứ 1!

---

## PHẦN 7: TÍCH HỢP VÀO HỆ THỐNG (`main.py` & `seat_mapper.py`)

### 7.a. `main.py` đang nạp tệp trọng số nào và lấy cấu hình từ đâu?

Trích xuất nguyên văn từ `c:\CineSightApp\ai_service\main.py:417-430` và `main.py:90-96`:

```python
# main.py:417-430 (Khi khởi động server FastAPI)
print("[INFO] Đang tải mô hình YOLO...")
try:
    import os
    default_model_path = os.path.join(os.path.dirname(__file__), "models", "best_head_v2.pt")
    model_path = os.environ.get("CINESIGHT_MODEL", default_model_path)
    MODEL_CONF = float(os.environ.get("CINESIGHT_CONF", "0.25"))
    MODEL_IMGSZ = int(os.environ.get("CINESIGHT_IMGSZ", "800"))
    model = YOLO(model_path)
    print(f"[OK] Tải mô hình thành công: {model_path} (conf={MODEL_CONF}, imgsz={MODEL_IMGSZ})")
```

```python
# main.py:90-96 (Bên trong endpoint POST /api/v1/analyze)
    detected_heads = []
    if model:
        results = model.predict(img, conf=MODEL_CONF, imgsz=MODEL_IMGSZ, classes=[0], verbose=False)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detected_heads.append(((x1 + x2) / 2, (y1 + y2) / 2))
```

- **Tệp trọng số thực sự đang dùng khi chạy**: `c:\CineSightApp\ai_service\models\best_head_v2.pt` (`6.244.586 bytes`, bản sao của `runs/detect/head_v2_official/weights/best.pt` tại Epoch 35). Có thể ghi đè qua biến môi trường `CINESIGHT_MODEL` (`main.py:420-421`). **[ĐÃ XÁC MINH]**
- **Cấu hình suy luận**:
  - `conf`: Lấy từ biến môi trường `CINESIGHT_CONF`, mặc định là hằng số chuỗi `"0.25"` $\rightarrow$ `float 0.25` (`main.py:422`).
  - `imgsz`: Lấy từ biến môi trường `CINESIGHT_IMGSZ`, mặc định là `"800"` $\rightarrow$ `int 800` (`main.py:423`).
  - `classes`: Hardcode cố định `classes=[0]` (`main.py:92`), tương ứng với lớp `{0: 'head'}`.
  - `iou` (NMS threshold): **Không được khai báo trong `main.py`** $\rightarrow$ Ultralytics tự dùng giá trị mặc định `iou = 0.70` (lệch với `iou = 0.60` trong `tools/eval_counts.py:63`). **[ĐÃ XÁC MINH]**

---

### 7.b. Luồng xử lý từ Ảnh $\rightarrow$ Cảnh báo & Kiểm toán Bản đồ ghế (`seats_config`)

1. **Luồng xử lý từng bước (Kèm tên hàm và dòng code)**:
   - **Bước 1 — Lấy danh sách ghế đã soát vé (Tập $A$)**: Tại `main.py:77`, hàm `analyze_cinema_room()` gọi `tap_A = get_seats(room_id, show_id)` (`database.py`) để truy vấn SQLite bảng `tickets` lấy tập hợp các mã ghế hợp lệ đã quét QR từ ứng dụng Flutter (ví dụ `{"I04", "I05"}`).
   - **Bước 2 — Tải bản đồ đa giác ghế của phòng**: Tại `main.py:79`, gọi `seats_config = load_seats_config(room_id)` (`seat_mapper.py:34-50`), đọc tệp `seats_configs/seats_config_{room_id}.json` và chuẩn hóa mã ghế về dạng `Chữ + 2 số` (ví dụ `"I5"` $\to$ `"I05"` qua `normalize_seat()` tại `seat_mapper.py:27-32`).
   - **Bước 3 — Giải mã ảnh & Suy luận YOLO**: Tại `main.py:86-96`, đọc bytes ảnh upload thành mảng OpenCV BGR `img`, gọi `model.predict(img, conf=MODEL_CONF, imgsz=MODEL_IMGSZ, classes=[0])`, rồi lấy tọa độ tâm của từng hộp đầu: `((x1 + x2) / 2, (y1 + y2) / 2)` đưa vào mảng `detected_heads`.
   - **Bước 4 — Ánh xạ tọa độ tâm đầu vào mã ghế (Tập $B$)**: Tại `main.py:98`, gọi `tap_B = process_ai_detections(detected_heads, seats_config)` (`seat_mapper.py:52-79`). Hàm này sắp xếp các điểm đầu theo thứ tự từ trên xuống dưới, từ trái sang phải (`sorted_heads`), sau đó thử lần lượt 3 điểm dịch xuống dưới cằm/vai `check_y in (hy + 10.0, hy + 18.0, hy)` với hàm hình học **`cv2.pointPolygonTest(poly_np, (hx, check_y), False) >= 0`** (`seat_mapper.py:62-66`) để bù góc camera nhìn nghiêng từ trên cao. Nếu 2 khách ngồi cạnh nhau nghiêng đầu làm cả 2 điểm rơi vào cùng 1 ghế (ví dụ `I05`), đoạn code `seat_mapper.py:72-78` sẽ đẩy người thứ hai sang ghế liền kề bên phải (`I06`) nếu ghế đó đang trống.
   - **Bước 5 — Đối sánh tập hợp & Lưu cảnh báo vào DB**: Tại `main.py:99-107`, gọi `generate_alerts(tap_A, tap_B, room_id, len(seats_config))` (`seat_mapper.py:81-105`):
     - **Khách lậu (`illegal_occupants`)** $= B \setminus A$ (`set_B - set_A` tại `seat_mapper.py:87`): Ghế có đầu người trên camera nhưng không có vé quét.
     - **Khách vắng mặt (`missing_guests`)** $= A \setminus B$ (`set_A - set_B` tại `seat_mapper.py:88`): Ghế đã quét vé nhưng không thấy người ngồi.
     - **Vượt sức chứa (`over_capacity`)** $= |B| > \text{total\_seats}$ (`seat_mapper.py:89`).
     - Cuối cùng `save_alerts()` (`main.py:101-106`) ghi cảnh báo vào bảng `alerts` trong `cinesight.db`.

2. **Kiểm toán trung thực trạng thái Bản đồ ghế (`seats_configs/*.json`) hiện tại**:
   - **Trước ngày 17/10/2026**: Tệp `seats_config_room1.json` chỉ có 1 ghế giả `{"A1": [[100,100],[200,100],[200,200],[100,200]]}`.
   - **Hiện tại (sau khi chạy `tools/setup_rooms_and_schedule.py` lúc `13:16:29` ngày 17/10/2026)**:
     - Cả 4 phòng `room1`, `room2`, `room3`, `room4` đều có tệp `seats_configs/seats_config_room{1..4}.json` (mỗi tệp dài `10.129 bytes`, chứa **135 đa giác ghế** thuộc 12 hàng `A..L`: `A=8, B..J=11, K=13, L=15`) và ảnh `calibration_images/room{1..4}.jpg`. **[ĐÃ XÁC MINH]**
     - **NHƯNG CẦN LƯU Ý RÕ**:
       1. Tọa độ 135 ghế của `room1` được sinh tự động bằng **phép chia lưới nội suy tuyến tính** theo từng dải hàng (`bands` tại `tools/setup_rooms_and_schedule.py:49-108`) trên ảnh chụp màn hình $1024\times 899$, rồi nhân hệ số tịnh tiến `ax=1.1797, bx=361.75, ay=1.1303` (`setup_rooms_and_schedule.py:112-126`) sang khung $1920\times 1080$ — chứ **không phải** dùng `calibrate_seats.py` chấm tay từng góc của 135 chiếc ghế thật trên ảnh $1920\times 1080$. Do hiệu ứng cong ống kính góc rộng (fisheye/barrel distortion) ở rìa phòng và độ lệch cột ghế giữa các hàng, các ghế ở rìa trái/phải hoặc hàng xa có thể bị lệch 1–2 cột ghế so với thực tế!
       2. Ba phòng **`room2`, `room3`, `room4` hiện đang dùng bản copy 100% tọa độ của `room1`** (`setup_rooms_and_schedule.py:293-298`), tức là **giả lập cho đủ 4 phòng**, chưa có camera thật của phòng 2, 3, 4. **[ĐÃ XÁC MINH]**

---

### 7.c. Chạy thử thực tế trên 3 khung hình thuộc tập `test` (Qua `reports\walkthrough_tmp\` và đã xóa)

Trong lượt này, mô hình đang chạy trong `main.py` (`models/best_head_v2.pt`, `conf=0.25`, `imgsz=800`, `iou=0.70`) cùng hàm `process_ai_detections()` đã được chạy trực tiếp trên 3 khung hình đại diện cho 3 mức khách của tập `test` (`0 khách`, `4 khách`, `6 khách`). Ảnh minh họa vẽ khung dự đoán được lưu tạm vào `c:\CineSightApp\ai_service\reports\walkthrough_tmp\` rồi **xóa sạch ngay sau khi kiểm tra** (xem Output nguyên văn tại Mục 5 Phụ lục):

| Tên tệp ảnh thuộc tập `test` | Số khung nhãn thật (`GT_heads`) | Số người AI phát hiện (`total_detected_people` ở `conf=0.25`) | Sai lệch | Danh sách ghế ánh xạ (`tap_B_from_camera`) | Tên tệp ảnh minh họa tạm đã tạo và đã xóa |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`room1_cam_edited_0425s.jpg`** | **`0`** | **`0`** | **`0`** (Khớp 100%) | `[]` (Phòng trống) | `tmp_pred_room1_cam_edited_0425s.jpg` *(Đã xóa)* |
| **`room1_cam_edited_0456s.jpg`** | **`4`** | **`4`** | **`0`** (Khớp 100%) | `['I04', 'I05', 'I06', 'I07']` | `tmp_pred_room1_cam_edited_0456s.jpg` *(Đã xóa)* |
| **`room1_cam_edited_0551s.jpg`** | **`6`** | **`6`** | **`0`** (Khớp 100%) | `['H07', 'H08', 'I05', 'I06', 'I07', 'I08']` | `tmp_pred_room1_cam_edited_0551s.jpg` *(Đã xóa)* |

- **Xác nhận xóa thư mục tạm**: Lệnh `shutil.rmtree(r'c:\CineSightApp\ai_service\reports\walkthrough_tmp')` đã thực thi và kiểm tra `os.path.exists` trả về **`False`**. Không có bất kỳ ảnh mặt khán giả nào được nhúng vào báo cáo này. **[ĐÃ XÁC MINH]**

---

## PHẦN 8: BẢN ĐỒ TỆP, CÁCH CHẠY LẠI TỪNG BƯỚC & KIỂM TOÁN `.gitignore`

### 8.1. Bản đồ tệp và thư mục trong `ai_service/`

| Tệp / Thư mục | Vai trò trong hệ thống | Tạo / Cập nhật bởi lệnh hoặc công cụ nào | Có nên Commit lên Git không? |
| :--- | :--- | :--- | :--- |
| `C:\Users\Dell KIM ANH\Downloads\cam_edited.mp4` | Video gốc quay từ camera hồng ngoại phòng chiếu (`1,356 GB`). | Dữ liệu thô bên ngoài. | **KHÔNG** (Nặng & chứa hình ảnh khán giả). |
| `ai_service/dataset_stage_a.yaml` | Cấu hình dữ liệu YOLO cho Giai đoạn A (32 train / 8 val). | Tạo thủ công / script chuẩn bị Phase 4. | **CÓ** (File cấu hình văn bản nhẹ, 127 B). |
| `ai_service/dataset_head_v2.yaml` | Cấu hình dữ liệu YOLO chính thức (98 train / 22 val / 43 test, lớp `0: head`). | Tạo bởi `tools/extract_frames.py:216-231`. | **CÓ** (File cấu hình YAML nhẹ, 224 B). |
| `ai_service/datasets/head_v2/images/{train,val,test}/` | 163 ảnh `.jpg` ($1920\times 1080$) trích từ video gốc. | Tạo bởi `python tools/extract_frames.py`. | **KHÔNG** (Dữ liệu ảnh chứa mặt khán giả). |
| `ai_service/datasets/head_v2/labels/{train,val,test}/` | 163 tệp nhãn `.txt` chuẩn YOLO (tổng 825 khung đầu). | Tạo bởi `tools/label_heads_cv.py`. | **KHÔNG** (Đi kèm bộ ảnh nội bộ; chỉ backup riêng). |
| `ai_service/datasets/head_v2/labels_prelabel/` | 123 tệp nhãn nháp do `baseline_stage_a.pt` sinh tự động. | Tạo bởi `python tools/train_baseline.py`. | **KHÔNG** (Dữ liệu trung gian). |
| `ai_service/datasets/head_v2/manifest.csv` | Bảng danh mục 163 ảnh (tên tệp, thời điểm giây, độ sáng, đoạn, tập, số đầu, cờ đã kiểm). | Tạo bởi `tools/extract_frames.py:163`, cập nhật bởi `tools/dataset_stats.py:238`. | **TÙY CHỌN** (Hiện nằm trong `datasets/` nên đang được `.gitignore` chặn). |
| `ai_service/tools/extract_frames.py` | Script cắt khung hình cách 3,5s, lọc trùng và chia tập `train/val/test`. | Viết trong Phase 2. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/tools/label_heads_cv.py` | Công cụ GUI OpenCV để vẽ/sửa khung đầu người bằng chuột. | Viết trong Phase 3–4. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/tools/dataset_stats.py` | Script kiểm tra định dạng nhãn, đếm số đầu, tính kích thước px và vẽ ảnh QC. | Viết trong Phase 4 & 6. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/tools/train_baseline.py` | Script huấn luyện Stage A (32 ảnh) và sinh nhãn nháp cho 123 ảnh. | Viết trong Phase 5. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/tools/train_official.py` | Script huấn luyện mô hình chính thức 50 epochs ở `imgsz=800`. | Viết trong Phase 7. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/tools/eval_counts.py` | Script chọn ngưỡng `conf` trên `val` và đo sai số đếm trên `test`. | Viết trong Phase 8. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/tools/test_api_regression.py` | Script kiểm thử tự động các endpoint FastAPI và nạp model. | Viết trong Phase 9b. | **CÓ** (Mã nguồn kiểm thử). |
| `ai_service/tools/anonymize_figures.py` | Script làm mờ mặt khán giả trên các ảnh báo cáo. | Viết trong Phase 10. | **CÓ** (Mã nguồn công cụ). |
| `ai_service/models/baseline_stage_a.pt` | Trọng số YOLO nháp Giai đoạn A (`6,24 MB`). | Tạo bởi `python tools/train_baseline.py`. | **KHÔNG** (File binary `.pt`). |
| `ai_service/models/best_head_v2.pt` | **Trọng số YOLO chính thức đang chạy (`6,24 MB`)**. | Tạo bởi `python tools/train_official.py`. | **KHÔNG** (Mặc định không commit `.pt` lên Git; phân phối qua Release/Drive). |
| `ai_service/runs/detect/head_v2_official/` | Toàn bộ log CSV, biểu đồ đường cong, ảnh batch và `weights/best.pt`. | Tạo bởi Ultralytics khi chạy `train_official.py`. | **KHÔNG** (Đã chặn bởi `runs/` trong `.gitignore`). |
| `ai_service/reports/*.md`, `*.txt`, `*.png` | Các báo cáo kỹ thuật, biểu đồ đường cong và thống kê. | Tạo bởi các script Phase 1, 5, 7, 8, 10. | **CHỈ COMMIT FILE `.md`/`.txt` VÀ BIỂU ĐỒ `.png`**; **TUYỆT ĐỐI KHÔNG COMMIT** thư mục `reports/qc_overlays/` và `reports/failure_cases/` (chứa ảnh gốc chưa che mặt!). |
| `ai_service/main.py` & `seat_mapper.py` | Server FastAPI và module ánh xạ tọa độ đầu vào đa giác ghế. | Mã nguồn chính của Backend. | **CÓ** (Mã nguồn cốt lõi). |
| `ai_service/seats_configs/seats_config_room1..4.json` | Tọa độ đa giác 135 ghế (`A–L`) của 4 phòng chiếu. | Tạo bởi `tools/setup_rooms_and_schedule.py` / `calibrate_seats.py`. | **CÓ** (Cấu hình JSON nhẹ). |

---

### 8.2. Các lệnh chuẩn để chạy lại từng bước (Khi cần tái lập)

Tất cả các lệnh dưới đây chạy tại thư mục `c:\CineSightApp\ai_service` bằng Python trong `venv`:

1. **Bước 1 — Trích xuất khung hình từ video gốc**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\extract_frames.py
   ```
2. **Bước 2 — Mở công cụ gán nhãn / duyệt nhãn bằng chuột**:
   ```powershell
   # Duyệt các ảnh chưa kiểm:
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\label_heads_cv.py --mode unverified
   # Hoặc xem lại toàn bộ 163 ảnh:
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\label_heads_cv.py --mode all
   ```
3. **Bước 3 — Chạy thống kê nhãn & xuất ảnh kiểm tra chất lượng (QC)**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\dataset_stats.py
   ```
4. **Bước 4 — Huấn luyện mô hình nháp Stage A (40 ảnh) & sinh nhãn nháp**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\train_baseline.py
   ```
5. **Bước 5 — Huấn luyện mô hình chính thức (`best_head_v2.pt`, 50 epochs, `imgsz=800`)**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\train_official.py
   ```
6. **Bước 6 — Đánh giá sai số đếm trên tập `val` / `test` & xuất ca lỗi**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\eval_counts.py
   ```
7. **Bước 7 — Vẽ khung dự đoán lên ảnh bất kỳ để kiểm tra**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe -c "from ultralytics import YOLO; m=YOLO('models/best_head_v2.pt'); m.predict(source='datasets/head_v2/images/test/room1_cam_edited_0456s.jpg', conf=0.25, iou=0.60, imgsz=800, save=True, project='reports/walkthrough_tmp', name='pred')"
   ```
8. **Bước 8 — Kiểm thử hồi quy tích hợp API (`main.py`)**:
   ```powershell
   c:\CineSightApp\ai_service\venv\Scripts\python.exe c:\CineSightApp\ai_service\tools\test_api_regression.py
   ```

---

### 8.3. Kiểm toán `.gitignore` & Những tệp đang bị Git theo dõi nhầm / có nguy cơ lọt lên Git

Đối chiếu giữa `c:\CineSightApp\.gitignore`, `c:\CineSightApp\ai_service\.gitignore`, danh sách `git ls-files` và `git status -s` (xem Output nguyên văn tại Mục 6 Phụ lục):

1. **Những gì `.gitignore` ĐÃ CHẶN ĐÚNG**:
   - Đã chặn: `venv/`, `__pycache__/`, `datasets/`, `datasets_archive/`, `runs/`, `runs_archive/`, `models/`, `*.pt`, `*.mp4`, `*.db` (`cinesight.db`), `reports/*.log`, và `*.jpg` (nhờ dòng 27 của `ai_service/.gitignore`: `*.jpg`). **[ĐÃ XÁC MINH]**
2. **Những tệp ĐANG BỊ GIT THEO DÕI NHẦM (`git ls-files` đã trót commit từ trước)**:
   - `ai_service/coco128.zip` (tệp nén dữ liệu mẫu COCO128 nặng ~6,8 MB đã được commit từ trước).
   - `ai_service/train_log.txt`, `ai_service/uvicorn_log.txt`, `ai_service/test_flow_output.txt` (các tệp log chạy thử từ đợt cũ).
   - `ai_service/dataset.yaml`, `ai_service/train.py`, `ai_service/train_v1.py` (script và cấu hình cũ dùng cho `coco128`). **[ĐÃ XÁC MINH - Output lệnh Mục 6 Phụ lục]**
3. **Những tệp rác / nhạy cảm ĐANG UNTRACKED (`??`) chưa được `.gitignore` chặn**:
   - **Trong `ai_service/`**: Hàng loạt script vá lỗi tạm thời đang hiện `??` trong `git status`: `fix.py`, `fix2.py`, `fix3.py`, `fix_db.py`, `patch.py`, `patch_alerts_time.py`, `patch_main.py`, `patch_save_alerts.py`, `test_alert.py`, `test_alert_time.py`, `test_api.py`, `test_shift.py`.
   - **Trong `ai_service/reports/`**: Mặc dù `ai_service/.gitignore:27` có dòng `*.jpg` (vô tình giúp chặn các tệp `.jpg` trong `reports/qc_overlays/` và `reports/failure_cases/`), nhưng `reports/prelabels_metadata.json` và các tệp `.png` chưa được quy định rõ, và tốt nhất nên thêm hẳn `reports/qc_overlays/`, `reports/failure_cases/`, `reports/walkthrough_tmp/` vào `.gitignore` để không bao giờ đẩy nhầm ảnh gốc của khán giả lên GitHub حتی nếu đổi đuôi sang `.png`. **[ĐÃ XÁC MINH]**

---

## PHẦN 9: VIỆC CÒN LẠI, XẾP HẠNG THEO MỨC ĐỘ ẢNH HƯỞNG TỚI KẾT QUẢ THỰC TẾ

| Hạng | Công việc cần làm | Giải thích tác động (1 câu) | Ước lượng công sức |
| :---: | :--- | :--- | :---: |
| **1 (Quan trọng nhất)** | **Kiểm tra trên video / phiên chiếu khác hoàn toàn** | Đây là cách duy nhất để biết độ chính xác thật của `best_head_v2.pt` khi tách khỏi hiệu ứng "nhớ cảnh và nhớ 6 vị khách của `cam_edited.mp4`" (hiện đang có rủi ro rò rỉ dữ liệu cao). | **45 – 60 phút** (quay/lấy 1 video khác, trích 35–40 khung, gán nhãn và chạy `eval_counts.py`). |
| **2** | **Thêm dữ liệu cho khung đông khách (>15–100 người) và bị che khuất** | Toàn bộ 163 ảnh hiện tại chỉ có tối đa 6 khách ngồi ở vùng giữa phòng, nên nếu gặp suất chiếu đông khách có hàng trước che khuất hàng sau hoặc khách ngồi ở 4 góc phòng thì mô hình chưa từng được học. | **2 – 3 giờ** (trích 80–100 khung từ suất chiếu đông khách, dùng `best_head_v2.pt` gán nháp rồi sửa tay và train lại 50 epochs). |
| **3** | **Hiệu chuẩn bản đồ ghế thật (`seats_config`) trực tiếp trên khung hình $1920\times 1080$ của từng phòng** | Hiện tại 135 ghế đang được chia lưới nội suy đều nhau từ ảnh $1024\times 899$ và nhân bản giống hệt cho cả 4 phòng (`room1..4`), nên dù AI có chấm đúng tâm đầu người ở rìa phòng thì vẫn có thể bị gán lệch sang ghế bên cạnh. | **30 – 45 phút / phòng** (chấm 4 góc của từng cụm/ghế trực tiếp trên ảnh gốc $1920\times 1080$ của mỗi phòng). |
| **4** | **Chọn lại ngưỡng (`conf`, `iou`) trên tập `val` độc lập và đồng bộ vào `main.py`** | Cần truyền tường minh `iou=0.60` vào `main.py:92` (để khớp với `eval_counts.py`, giảm ngay `MAE` từ `0,65` xuống `0,44` trên tập test hiện tại) và chốt lại `conf` trên tập `val` của video mới thay vì nhìn tập `test`. | **5 phút** (sửa 1 dòng trong `main.py:92` thêm `iou=MODEL_IOU` và test lại). |
| **5** | **Nối luồng chụp ảnh từ Camera RTSP / Video vào Backend theo lịch chiếu tự động** | Hiện tại `run_camera_client.py` phải chạy tay bằng lệnh CLI với tham số `--room` và `--show` cố định (và dòng 22 của `run_camera_client.py` đang bị lỗi thụt lề `IndentationError`), cần sửa và tự động lấy `show_id` đang chiếu từ bảng `showtimes`. | **30 – 45 phút** (sửa lỗi dòng 22 `run_camera_client.py` và nối API `/api/v1/showtimes`). |
| **6** | **Thử nghiệm độ phân giải lớn hơn (`imgsz = 960` hoặc `1280`)** | Sẽ giúp cứu nhóm **71% – 85% đầu người nhỏ ở xa** ($H_{\text{800}} < 12\text{ px}$) đang bị bỏ sót trên tập `val`, đổi lại thời gian suy luận trên CPU sẽ tăng từ ~0,25s lên ~0,5–0,7s/ảnh (hoàn toàn chấp nhận được vì 5 giây mới chụp 1 lần). | **2,5 – 3,5 giờ chạy máy** (chỉ cần đổi `imgsz=960` hoặc `1280` trong `train_official.py` và treo máy chạy). |
| **7** | **Nâng cấp kiến trúc mô hình từ `yolov8n` (Nano) lên `yolov8s` (Small)** | Tăng dung lượng mạng từ 3,2 triệu lên 11,2 triệu tham số giúp học biên dạng đầu trong bóng tối tốt hơn, nhưng chỉ thực sự phát huy tác dụng sau khi đã có thêm dữ liệu đa dạng ở Hạng 1 và Hạng 2 (nếu nâng ngay trên 98 ảnh hiện tại sẽ càng dễ học vẹt hơn). | **3 – 4 giờ chạy máy** trên CPU (hoặc 10 phút nếu chạy trên Google Colab GPU T4). |

---

## PHẦN 10: KIỂM TRA HIỂU BÀI (3 CÂU HỎI TỰ LUẬN DỰA TRÊN SỐ LIỆU THẬT)

Hãy thử tự trả lời 3 câu hỏi dưới đây bằng lời của bạn (như khi hội đồng chấm đồ án hỏi xoáy) trước khi xem phần gợi ý ở cuối:

### Câu hỏi 1:
> **"Trong `results.csv` (Epoch 35), chỉ số `mAP@50` của em đạt tới `80,98%` trên tập `val` (22 ảnh), và trên tập `test` (43 ảnh) ở `conf=0.25, iou=0.60` sai số đếm trung bình `MAE` chỉ là `0,44 người/ảnh`. Dựa trên cách chia tập từ tệp `cam_edited.mp4` (khoảng cách giây giữa các tập và phân bố số đầu mỗi ảnh), hãy giải thích vì sao nếu ngày mai mang nguyên mô hình `best_head_v2.pt` này sang lắp cho Phòng chiếu 2 vào suất chiếu tối thứ Bảy có 80 khán giả thì các con số `80,98%` và `0,44` kia gần như chắc chắn không còn đúng nữa?"**

### Câu hỏi 2:
> **"Giả sử trong tệp `ai_service/main.py:422`, em đổi ngưỡng `MODEL_CONF` từ `0.45` xuống `0.15` (giữ nguyên bản đồ ghế và danh sách vé đã soát Tập $A$). Khi đó, số lượng phần tử của Tập $B$ (`tap_B_from_camera`) sẽ thay đổi thế nào, dẫn tới loại cảnh báo nào (`illegal_occupants` - khách lậu hay `missing_guests` - khách vắng mặt) sẽ TĂNG LÊN và loại cảnh báo nào sẽ GIẢM XUỐNG? Hãy dùng chính số liệu của bảng khảo sát ngưỡng trong `EVAL_REPORT_PHASE8.md` (`conf=0.15` vs `conf=0.45`) để minh họa."**

### Câu hỏi 3:
> **"Trong tài liệu `reports/LABELING_GUIDE.md` (Mục 2.2 và 2.4), quy ước đặt ra là: *'Nếu đầu bị che khuất trên 50% (chỉ thấy chỏm tóc nhỏ) hoặc chiều cao đầu nhỏ hơn 12 px thì BỎ QUA, không gán nhãn'*. Quy ước này giúp mô hình không bị nhiễu khi học, nhưng trong thực tế vận hành ở rạp phim, khi một khán giả cao 1m50 ngồi lọt thỏm sau lưng ghế hoặc bị người hàng trước che khuất 60% đầu (mà người đó ĐÃ mua vé và quét QR hợp lệ vào Tập $A$), quy ước không gán nhãn này sẽ gây ra hậu quả gì cho hệ thống cảnh báo tại `seat_mapper.py:88`?"**

---

<details>
<summary><b>💡 GỢI Ý ĐÁP ÁN (Tách riêng — Chỉ mở xem sau khi bạn đã tự trả lời)</b></summary>

- **Gợi ý Câu 1 (4 ý cốt lõi)**:
  1. **Cùng cảnh nền tĩnh & khoảng cách thời gian quá sát**: Tập `val` cách tập `train` chỉ **2,5 giây** (`343,5s` $\to$ `346,0s`) và tập `test` cách tập `val` chỉ **5,5 giây** (`419,5s` $\to$ `425,0s`) trên cùng 1 video `cam_edited.mp4`, nên mô hình đã quen thuộc hoàn toàn với kết cấu ghế và ánh sáng hồng ngoại của `room1`.
  2. **Cùng một nhóm khán giả**: Cả 3 tập chỉ xoay quanh đúng 1 nhóm từ **0 đến tối đa 6 khán giả** ngồi chủ yếu ở khu vực giữa phòng (`G, H, I`); mô hình chưa từng nhìn thấy 80 khuôn mặt/kiểu tóc khác nhau.
  3. **Mật độ đám đông & Che khuất**: Khi có 80 khán giả, các đầu người ở hàng trước sẽ che khuất một phần hàng sau và các khung bao sẽ nằm sát cạnh nhau (dễ bị thuật toán NMS gộp nhầm hoặc bỏ sót), khác hẳn cảnh thưa thớt 4–6 người.
  4. **Khác góc lắp camera & kích thước đầu ở xa**: Phòng chiếu 2 có thể lắp camera cao/xa hơn; mà ngay trên tập `val` hiện tại, với các đầu nhỏ sau khi thu về `imgsz=800` có chiều cao $<12\text{ px}$, Recall của mô hình đã tụt xuống chỉ còn **14,3% – 28,6%**.

- **Gợi ý Câu 2 (Cơ chế tập hợp $B \setminus A$ và $A \setminus B$)**:
  1. Khi hạ `MODEL_CONF` từ `0.45` xuống `0.15`, điều kiện lọc `box.conf >= MODEL_CONF` lỏng hơn rất nhiều $\rightarrow$ số lượng đầu người được giữ lại tăng lên $\rightarrow$ **kích thước Tập $B$ (`tap_B_from_camera`) phình to ra**.
  2. Vì `illegal_occupants = set_B - set_A` (Khách lậu: có trong $B$ nhưng không có vé trong $A$), khi $B$ phình to và bắt nhầm cả bóng phản xạ hồng ngoại trên ghế trống thành người (như trên tập `test` ở `conf=0.15` có tới 19/43 ảnh bị đếm thừa từ `+1` đến `+5` người), **cảnh báo "Khách lậu" (`illegal_occupants`) sẽ TĂNG VỌT (nhiều báo động giả)**.
  3. Ngược lại, vì `missing_guests = set_A - set_B` (Khách vắng mặt: có vé trong $A$ nhưng camera không thấy trong $B$), khi hạ xuống `conf=0.15` mô hình hầu như không bỏ sót khách thật nào (`0/43` ảnh đếm thiếu trên tập `test`, trong khi ở `conf=0.45` trên tập `val` sai số `MAE` tăng lên `1,05` do đếm thiếu), nên **cảnh báo "Khách vắng mặt" (`missing_guests`) sẽ GIẢM XUỐNG mức tối thiểu**.

- **Gợi ý Câu 3 (Mâu thuẫn giữa Quy ước nhãn ML và Logic nghiệp vụ rạp phim)**:
  1. Khi ta quy ước **không vẽ nhãn** cho các đầu bị che khuất $>50\%$ hoặc nhỏ $<12\text{ px}$, trong quá trình huấn luyện, những vùng đầu bị che khuất đó bị tính là **nền (`background`)** — tức là mô hình bị phạt (`cls_loss`) nếu dám dự đoán đó là đầu người!
  2. Kết quả là khi chạy thật, gặp vị khách cao 1m50 bị lưng ghế che 60% đầu, mô hình sẽ tuân thủ đúng những gì đã học: **bỏ qua không nhận diện người đó** (điểm `conf` cực thấp).
  3. Khi đó, ghế của vị khách này **có nằm trong Tập $A$** (vì khách đã quét vé QR ở cửa), nhưng **không có trong Tập $B$** (vì AI không phát hiện ra đầu) $\rightarrow$ phép trừ `khach_vang = set_A - set_B` tại `seat_mapper.py:88` sẽ phát sinh **cảnh báo giả `[VÀNG] Có vé nhưng ghế trống` (`missing_guest`)**, dù khách vẫn đang ngồi xem phim ngay tại ghế đó.

</details>

---

## PHẦN PHỤ LỤC: LỆNH ĐÃ CHẠY TRONG LƯỢT NÀY KÈM OUTPUT NGUYÊN VĂN & MỤC "CHƯA XÁC NHẬN ĐƯỢC"

### A.1. Lệnh 1 — Kiểm tra `git status`, `git log` và thời gian tệp (`CreationTime`, `LastWriteTime`)

- **Lệnh đã chạy**:
```powershell
$env:PYTHONIOENCODING="utf-8"
Write-Output "=== 1. GIT STATUS & GIT LOG ==="
git status -s
git log -n 5 --oneline
Write-Output "=== 2. AI_SERVICE FILES & TIMESTAMPS ==="
Get-ChildItem -Path "c:\CineSightApp\ai_service" -Force | Select-Object Name, Length, CreationTime, LastWriteTime | Format-Table -AutoSize
Get-ChildItem -Path "c:\CineSightApp\ai_service\tools" -Force | Select-Object Name, Length, CreationTime, LastWriteTime | Format-Table -AutoSize
Get-ChildItem -Path "c:\CineSightApp\ai_service\models" -Force | Select-Object Name, Length, CreationTime, LastWriteTime | Format-Table -AutoSize
Get-ChildItem -Path "c:\CineSightApp\ai_service\reports" -Force | Select-Object Name, Length, CreationTime, LastWriteTime | Format-Table -AutoSize
Get-ChildItem -Path "c:\CineSightApp\ai_service\runs\detect" -Force -ErrorAction SilentlyContinue | Select-Object Name, CreationTime, LastWriteTime | Format-Table -AutoSize
```

- **Output nguyên văn (Trích phần `git log` và bảng `ai_service`)**:
```text
e58f8ff Checkpoint truoc khi don dep mobile_app
8bda2a1 feat(admin+backend): Hoàn thiện hệ thống cấp phát tài khoản Nhân sự và phân luồng Network
fe47a22 feat(ai_service): add alerts table and endpoints to persist warnings
cc8ac2a fix(network): add ngrok-skip-browser-warning header and clean baseUrl
9fabb3c fix(mock): rewrite mock_data.dart to resolve all mojibake encoding issues
=== 2. AI_SERVICE FILES & TIMESTAMPS ===

Name                  Length  CreationTime          LastWriteTime         
----                  ------  ------------          -------------         
calibration_images            9/21/2026 7:27:34 PM  10/17/2026 12:46:50 PM
datasets                      9/20/2026 9:22:49 PM  10/13/2026 4:18:55 PM 
datasets_archive              10/13/2026 4:16:27 PM 10/13/2026 4:16:58 PM 
models                        10/13/2026 7:03:08 PM 10/13/2026 11:02:46 PM
reports                       10/13/2026 4:04:16 PM 10/17/2026 11:46:59 AM
runs                          10/4/2026 7:35:23 PM  10/4/2026 7:35:23 PM  
runs_archive                  10/13/2026 4:16:27 PM 10/13/2026 4:16:47 PM 
seats_configs                 9/21/2026 7:27:39 PM  10/17/2026 12:46:50 PM
tools                         10/13/2026 4:17:48 PM 10/17/2026 12:46:07 PM
venv                          9/23/2026 7:09:36 PM  9/23/2026 7:10:37 PM  
__pycache__                   9/21/2026 5:34:19 PM  10/17/2026 1:18:50 PM 
.gitignore            351     9/21/2026 6:06:45 PM  10/13/2026 4:19:57 PM 
best_v1.pt            6201322 10/4/2026 7:47:13 PM  10/4/2026 7:45:48 PM  
```

---

### A.2. Lệnh 2 — Kiểm tra phiên bản môi trường, độ lệch màu video, nguồn gốc nhãn và thống kê kích thước khung

- **Output nguyên văn**:
```text
=== 1. VERSIONS ===
Python: 3.14.3
Torch: 2.14.0+cpu
Ultralytics: 8.4.160
OpenCV: 5.0.0
NumPy: 2.5.3

=== 2. VIDEO COLOR/GRAYSCALE CHECK ===
Video exists: C:\Users\Dell KIM ANH\Downloads\cam_edited.mp4 | size=1456225950 bytes | 1920x1080 @ 30.0 fps | 17337 frames (577.90s)
  t=10s: mean_brightness=95.36, mean_saturation=0.14, |R-G|=0.01, |G-B|=0.03
  t=150s: mean_brightness=95.54, mean_saturation=1.31, |R-G|=0.05, |G-B|=0.31
  t=300s: mean_brightness=106.87, mean_saturation=2.20, |R-G|=0.07, |G-B|=0.41
  t=380s: mean_brightness=106.90, mean_saturation=0.00, |R-G|=0.00, |G-B|=0.00
  t=500s: mean_brightness=98.38, mean_saturation=0.00, |R-G|=0.00, |G-B|=0.00

=== 3. STAGE A & PRELABEL PROVENANCE ===
stage_a_list.txt count: 40
Stage A by split: {'train': 32, 'val': 8}
In labels/ vs labels_prelabel/: identical=6, modified=117, only_in_labels(Stage A)=40
labels/ mtime range: 2026-10-13 18:05:20.667876 -> 2026-10-13 20:42:46.446012
labels_prelabel/ mtime range: 2026-10-13 20:14:38.032725 -> 2026-10-13 20:14:58.270943

=== 4. LABEL & BOX SIZE STATS (ORIGINAL 1920x1080 AND IMGSZ=800) ===
Split train: imgs=98, heads=570, mean=5.82, median=6.0, max=6, empty=0 (0.0%)
  count_dist={4: 3, 5: 12, 6: 83}
  Orig 1920x1080 px: W_med=34.0, H_med=36.0, W_min=17.0, H_min=18.0, H<12px=0 (0.00%)
  Scaled imgsz=800 (800x450): W_med=14.17, H_med=15.00, W_min=7.08, H_min=7.50, min_dim<8px=4 (0.70%), min_dim<12px=102 (17.89%), H<12px=30 (5.26%)
Split val: imgs=22, heads=87, mean=3.95, median=4.5, max=6, empty=3 (13.6%)
  count_dist={0: 3, 1: 3, 3: 1, 4: 4, 5: 1, 6: 10}
  Orig 1920x1080 px: W_med=35.0, H_med=36.0, W_min=15.0, H_min=18.0, H<12px=0 (0.00%)
  Scaled imgsz=800 (800x450): W_med=14.58, H_med=15.00, W_min=6.25, H_min=7.50, min_dim<8px=1 (1.15%), min_dim<12px=11 (12.64%), H<12px=7 (8.05%)
Split test: imgs=43, heads=168, mean=3.91, median=4.0, max=6, empty=4 (9.3%)
  count_dist={0: 4, 1: 1, 3: 3, 4: 26, 6: 9}
  Orig 1920x1080 px: W_med=30.0, H_med=32.0, W_min=18.0, H_min=23.0, H<12px=0 (0.00%)
  Scaled imgsz=800 (800x450): W_med=12.50, H_med=13.33, W_min=7.50, H_min=9.58, min_dim<8px=1 (0.60%), min_dim<12px=60 (35.71%), H<12px=12 (7.14%)
OVERALL 825 heads: Orig W_med=33.0px, H_med=35.0px | Scaled 800: W_med=13.75px, H_med=14.58px | W<8px=5 (0.61%), H<8px=2 (0.24%), W<12px=151 (18.30%), H<12px=49 (5.94%)
```

---

### A.3. Lệnh 3 — Kiểm tra chỉnh sửa nhãn thật, danh sách tệp run, so sánh 4 mô hình Baseline, Recall theo kích thước, chạy thử 3 ảnh qua `walkthrough_tmp` và kiểm toán Git

- **Output nguyên văn**:
```text
=== 1. PRELABEL ROUNDTRIP VS ACTUAL HUMAN EDIT CHECK ===
Split train: Stage_A(manual)=32, Prelabel_accepted_as_is=38, Prelabel_edited_by_human=28 (pre_heads=360 -> final_heads=382)
Split val: Stage_A(manual)=8, Prelabel_accepted_as_is=3, Prelabel_edited_by_human=11 (pre_heads=43 -> final_heads=54)
Split test: Stage_A(manual)=0, Prelabel_accepted_as_is=9, Prelabel_edited_by_human=34 (pre_heads=102 -> final_heads=168)

=== 2. FILES IN runs/detect/head_v2_official ===
  BoxF1_curve.png (103952 bytes)
  BoxPR_curve.png (75308 bytes)
  BoxP_curve.png (91876 bytes)
  BoxR_curve.png (92641 bytes)
  args.yaml (1894 bytes)
  confusion_matrix.png (86159 bytes)
  confusion_matrix_normalized.png (90458 bytes)
  labels.jpg (94783 bytes)
  results.csv (6204 bytes)
  results.png (288789 bytes)
  train_batch0.jpg (360993 bytes)
  train_batch1.jpg (329609 bytes)
  train_batch1000.jpg (212963 bytes)
  train_batch1001.jpg (267328 bytes)
  train_batch1002.jpg (208578 bytes)
  train_batch2.jpg (269855 bytes)
  val_batch0_labels.jpg (378702 bytes)
  val_batch0_pred.jpg (383649 bytes)
  val_batch1_labels.jpg (378598 bytes)
  val_batch1_pred.jpg (380864 bytes)
  val_batch2_labels.jpg (295601 bytes)
  val_batch2_pred.jpg (294290 bytes)
  weights\best.pt (6244586 bytes)
  weights\last.pt (6244586 bytes)

=== 3. COUNT EVALUATION & BASELINE COMPARISON ON VAL (22) & TEST (43) ===
yolov8n.pt (COCO person) | VAL | conf=0.15 -> MAE=4.05, MedAE=5.0, RMSE=4.60, Signed=-3.23, Max=6, Exact=9.1%, <=1=22.7%, <=2=22.7%
yolov8n.pt (COCO person) | VAL | conf=0.25 -> MAE=4.00, MedAE=4.5, RMSE=4.55, Signed=-3.55, Max=6, Exact=9.1%, <=1=22.7%, <=2=22.7%
yolov8n.pt (COCO person) | TEST | conf=0.15 -> MAE=3.91, MedAE=4.0, RMSE=4.23, Signed=-3.91, Max=6, Exact=9.3%, <=1=11.6%, <=2=11.6%
yolov8n.pt (COCO person) | TEST | conf=0.25 -> MAE=3.91, MedAE=4.0, RMSE=4.23, Signed=-3.91, Max=6, Exact=9.3%, <=1=11.6%, <=2=11.6%
best_v1.pt (COCO128 v1) | VAL | conf=0.15 -> MAE=3.86, MedAE=4.5, RMSE=4.54, Signed=-3.86, Max=6, Exact=13.6%, <=1=31.8%, <=2=31.8%
best_v1.pt (COCO128 v1) | VAL | conf=0.25 -> MAE=3.91, MedAE=4.5, RMSE=4.55, Signed=-3.91, Max=6, Exact=13.6%, <=1=27.3%, <=2=31.8%
best_v1.pt (COCO128 v1) | TEST | conf=0.15 -> MAE=3.26, MedAE=3.0, RMSE=3.62, Signed=-3.26, Max=6, Exact=9.3%, <=1=11.6%, <=2=25.6%
best_v1.pt (COCO128 v1) | TEST | conf=0.25 -> MAE=3.91, MedAE=4.0, RMSE=4.23, Signed=-3.91, Max=6, Exact=9.3%, <=1=11.6%, <=2=11.6%
baseline_stage_a.pt | VAL | conf=0.15 -> MAE=1.23, MedAE=1.0, RMSE=1.58, Signed=+0.41, Max=3, Exact=22.7%, <=1=72.7%, <=2=81.8%
baseline_stage_a.pt | VAL | conf=0.25 -> MAE=0.86, MedAE=1.0, RMSE=1.22, Signed=-0.59, Max=3, Exact=40.9%, <=1=77.3%, <=2=95.5%
baseline_stage_a.pt | TEST | conf=0.15 -> MAE=0.86, MedAE=1.0, RMSE=1.21, Signed=+0.12, Max=3, Exact=39.5%, <=1=79.1%, <=2=95.3%
baseline_stage_a.pt | TEST | conf=0.25 -> MAE=1.47, MedAE=1.0, RMSE=1.95, Signed=-1.47, Max=5, Exact=27.9%, <=1=55.8%, <=2=79.1%
best_head_v2.pt (Official) | VAL | conf=0.15 -> MAE=0.77, MedAE=1.0, RMSE=1.19, Signed=+0.05, Max=3, Exact=45.5%, <=1=86.4%, <=2=90.9%
best_head_v2.pt (Official) | VAL | conf=0.25 -> MAE=0.64, MedAE=0.0, RMSE=1.09, Signed=-0.36, Max=3, Exact=59.1%, <=1=81.8%, <=2=95.5%
best_head_v2.pt (Official) | TEST | conf=0.15 -> MAE=1.49, MedAE=1.0, RMSE=2.15, Signed=+1.49, Max=7, Exact=20.9%, <=1=69.8%, <=2=83.7%
best_head_v2.pt (Official) | TEST | conf=0.25 -> MAE=0.65, MedAE=0.0, RMSE=1.31, Signed=+0.47, Max=5, Exact=62.8%, <=1=88.4%, <=2=90.7%

=== 4. RECALL BY HEAD SIZE ON VAL & TEST (best_head_v2.pt, conf=0.25 & 0.15) ===
VAL (conf=0.15): Small heads (scaled H<12px): 2/7 (28.6%) | Larger heads (scaled H>=12px): 66/80 (82.5%)
VAL (conf=0.25): Small heads (scaled H<12px): 1/7 (14.3%) | Larger heads (scaled H>=12px): 65/80 (81.2%)
TEST (conf=0.15): Small heads (scaled H<12px): 10/12 (83.3%) | Larger heads (scaled H>=12px): 145/156 (92.9%)
TEST (conf=0.25): Small heads (scaled H<12px): 9/12 (75.0%) | Larger heads (scaled H>=12px): 140/156 (89.7%)

=== 5. PART 7c: 3 TEST FRAMES INFERENCE VIA walkthrough_tmp & CLEANUP ===
[INFO] Đang tải mô hình YOLO...
[OK] Tải mô hình thành công: C:\CineSightApp\ai_service\models\best_head_v2.pt (conf=0.25, imgsz=800)
[OK] Đã tải bản đồ ghế phòng 'room1': 135 ghế.
Frame room1_cam_edited_0425s.jpg: GT_heads=0, Pred_heads(conf=0.25)=0, tap_B=[], saved_tmp=tmp_pred_room1_cam_edited_0425s.jpg (exists=True)
Frame room1_cam_edited_0456s.jpg: GT_heads=4, Pred_heads(conf=0.25)=4, tap_B=['I04', 'I05', 'I06', 'I07'], saved_tmp=tmp_pred_room1_cam_edited_0456s.jpg (exists=True)
Frame room1_cam_edited_0551s.jpg: GT_heads=6, Pred_heads(conf=0.25)=6, tap_B=['H07', 'H08', 'I05', 'I06', 'I07', 'I08'], saved_tmp=tmp_pred_room1_cam_edited_0551s.jpg (exists=True)
Files created in reports/walkthrough_tmp: ['tmp_pred_room1_cam_edited_0425s.jpg', 'tmp_pred_room1_cam_edited_0456s.jpg', 'tmp_pred_room1_cam_edited_0551s.jpg']
Deleted reports/walkthrough_tmp -> exists now: False

=== 6. GIT TRACKED & UNTRACKED AUDIT ===
Tracked in ai_service/: ['ai_service/.gitignore', 'ai_service/calibrate_seats.py', 'ai_service/coco128.zip', 'ai_service/database.py', 'ai_service/dataset.yaml', 'ai_service/main.py', 'ai_service/patch_db.py', 'ai_service/requirements-lock.txt', 'ai_service/requirements.txt', 'ai_service/run_camera_client.py', 'ai_service/test_flow.py', 'ai_service/test_flow_output.txt', 'ai_service/test_model.py', 'ai_service/train.py', 'ai_service/train_log.txt', 'ai_service/train_v1.py', 'ai_service/uvicorn_log.txt']
```

---

### B. Mục "CHƯA XÁC NHẬN ĐƯỢC / KHÔNG TÌM THẤY"

1. **`reports/*.log` (Tệp log console lúc chạy `train_baseline.py` và `train_official.py`)**: **`KHÔNG TÌM THẤY`**. Trong thư mục `c:\CineSightApp\ai_service\reports\` không có tệp `.log` nào (chỉ có `.md`, `.txt`, `.json`, `.png`, `.jpg`), vì `tools/train_baseline.py` và `tools/train_official.py` không ghi hướng dòng chuẩn `stdout` ra tệp `.log` mà để Ultralytics tự ghi vào `runs/detect/*/results.csv`.
2. **Script khảo sát video Phase 1 và Script đo tốc độ (benchmark) `imgsz=640` vs `800` ở Phase 6**: **`KHÔNG TÌM THẤY`** tệp `.py` trong `ai_service/tools/`. Chỉ còn lưu kết quả đầu ra là `reports/brightness_profile.png`, `reports/contact_sheet_cam_edited.jpg` và các con số tóm tắt trong comment của `tools/train_baseline.py:66` cùng `reports/TRAINING_REPORT.md:58-60`.
3. **Độ chính xác của `best_head_v2.pt` trên phòng chiếu khác (`room2..room4`), ngày quay khác, hoặc khi phòng đông khách ($> 6\text{ người}$)**: **`KHÔNG BIẾT`** vì trong toàn bộ ổ đĩa chỉ có duy nhất 1 tệp video `cam_edited.mp4` với tối đa 6 khách.

---

## TỔNG KẾT TRẠNG THÁI CUỐI CÙNG

- **ĐÃ LÀM**:
  1. Đọc và đối chiếu toàn bộ mã nguồn, tệp cấu hình YAML/CSV/JSON, thời gian sửa đổi tệp (`CreationTime`/`LastWriteTime`), lịch sử Git và kết quả huấn luyện thật trong `c:\CineSightApp\ai_service`.
  2. Chạy kiểm tra chỉ đọc (read-only) xác minh thông số video gốc, độ lệch kênh màu, tỉ lệ nhãn gán tay vs nhãn nháp chỉnh sửa, kích thước khung đầu ở $1920\times 1080$ và `imgsz=800`, điểm Recall theo kích thước đầu, và so sánh 4 mô hình (`yolov8n.pt`, `best_v1.pt`, `baseline_stage_a.pt`, `best_head_v2.pt`) trên cùng tập `val`/`test`.
  3. Chạy thử suy luận trên 3 khung hình thuộc tập `test` (`0425s.jpg`, `0456s.jpg`, `0551s.jpg`), ghi ảnh minh họa vào `c:\CineSightApp\ai_service\reports\walkthrough_tmp\` rồi **xóa hoàn toàn thư mục `reports\walkthrough_tmp\`** ngay sau khi xong.
  4. Xuất bản báo cáo giải thích & kiểm toán đầy đủ tại `c:\CineSightApp\ai_service\reports\TRAINING_WALKTHROUGH.md` mà không sửa đổi bất kỳ dòng code hay dữ liệu nào của dự án.

- **ĐÃ XÁC NHẬN (CÓ OUTPUT)**:
  1. Mô hình đang chạy trong `main.py:420-425` là `models/best_head_v2.pt` (bản chụp tại **Epoch 35/50** của `runs/detect/head_v2_official`, khởi tạo từ `yolov8n.pt` gốc, không trộn `coco128`), chạy ở `MODEL_CONF=0.25`, `MODEL_IMGSZ=800`, `iou=0.70` (mặc định).
  2. Khoảng cách thời gian nhỏ nhất giữa `train` và `val` là **2,5 giây**, giữa `val` và `test` là **5,5 giây**, và giữa `train` với `test` là **81,5 giây** trên cùng 1 video `cam_edited.mp4` (tối đa 6 khách/ảnh).
  3. Trong 163 nhãn chính thức (`labels/`), có **40 ảnh (24,5%)** gán tay từ đầu (Stage A), **73 ảnh (44,8%)** do mô hình nháp gán rồi người dùng sửa/vẽ bù (+99 đầu), và **50 ảnh (30,7%)** người dùng duyệt giữ nguyên khung nháp của `baseline_stage_a.pt`.
  4. Thư mục tạm `c:\CineSightApp\ai_service\reports\walkthrough_tmp` đã được xóa sạch (`exists = False`).

- **CHƯA XÁC NHẬN / CẦN TÔI QUYẾT ĐỊNH**:
  1. **Đồng bộ tham số `iou=0.60` vào `main.py:92`**: Hiện `main.py:92` đang để mặc định `iou=0.70` (cho Test `MAE = 0,65`), trong khi `eval_counts.py:63` dùng `iou=0.60` (cho Test `MAE = 0,44`). Bạn có muốn thêm `iou=0.60` vào `main.py` ở bước tiếp theo không?
  2. **Dọn dẹp Git & `.gitignore`**: Bạn có muốn xóa các tệp rác `fix*.py`, `patch*.py` chưa commit, bỏ theo dõi `ai_service/coco128.zip` (`git rm --cached`), và bổ sung `reports/qc_overlays/`, `reports/failure_cases/` vào `.gitignore` để bảo vệ quyền riêng tư tuyệt đối không?
  3. **Kiểm định trên video mới**: Bạn có video quay ở suất chiếu khác / phòng khác (hoặc cảnh đông khách hơn) để thực hiện bài kiểm tra độc lập 35–40 khung hình như kế hoạch ở Mục 5.7 không?

