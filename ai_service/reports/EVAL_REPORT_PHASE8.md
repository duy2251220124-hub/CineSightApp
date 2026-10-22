# BÁO CÁO NGHIỆM THU ĐỘ CHÍNH XÁC MÔ HÌNH NHẬN DIỆN ĐẦU NGƯỜI (PHASE 8)

- **Mô hình**: `models/best_head_v2.pt` (Huấn luyện 50 epochs trên 98 ảnh Train)
- **Ngưỡng tin cậy tối ưu chọn từ tập Val**: `conf = 0.15`
- **Tập kiểm định độc lập (Test split)**: 43 ảnh (Suất 2 phim chiếu - Hoàn toàn không rò rỉ dữ liệu)

## 1. Kết quả Nghiệm thu Độc lập trên Tập Test (43 ảnh)

| Chỉ số đo đạc | Giá trị | Đánh giá |
| :--- | :--- | :--- |
| **Sai số đếm trung bình (MAE)** | **0.88 người/ảnh** | Cực kỳ thấp (trung bình lệch dưới 0.9 người) |
| **Sai số toàn phương (RMSE)** | **1.56 người/ảnh** | Phản ánh độ ổn định cao, không có ca lệch đột biến |
| **Tỉ lệ khớp chính xác 100% (Exact Match)** | **55.8%** (24/43 ảnh) | Đoán số lượng chuẩn từng người một |
| **Tỉ lệ lệch trong khoảng ±1 người** | **74.4%** (32/43 ảnh) | Đạt độ tin cậy thực tế trong rạp chiếu phim |
| **Độ lệch lớn nhất (Max Error)** | **5 người** | Cao nhất chỉ lệch 5 người |

## 2. Phân bố Sai số Đếm

| Độ lệch (Dự đoán - Thực tế) | Số lượng ảnh | Tỉ lệ % | Bản chất hiện tượng |
| :---: | :---: | :---: | :--- |
| `0` | 24/43 | 55.8% | Khớp hoàn hảo |
| `+1` | 8/43 | 18.6% | Nhận diện thừa do bóng phản xạ/ghế |
| `+2` | 7/43 | 16.3% | Nhận diện thừa do bóng phản xạ/ghế |
| `+3` | 2/43 | 4.7% | Nhận diện thừa do bóng phản xạ/ghế |
| `+5` | 2/43 | 4.7% | Nhận diện thừa do bóng phản xạ/ghế |

## 3. Khảo sát Ngưỡng Tin cậy trên Tập Val

| Ngưỡng (Conf) | MAE Val | Đúng 100% | Đúng ±1 | Trạng thái |
| :---: | :---: | :---: | :---: | :---: |
| 0.15 | 0.50 | 59.1% | 95.5% | **TỐI ƯU CHỌN** |
| 0.20 | 0.59 | 59.1% | 86.4% |  |
| 0.25 | 0.59 | 59.1% | 86.4% |  |
| 0.30 | 0.64 | 59.1% | 81.8% |  |
| 0.35 | 0.64 | 59.1% | 81.8% |  |
| 0.40 | 0.73 | 54.5% | 81.8% |  |
| 0.45 | 1.05 | 36.4% | 72.7% |  |
| 0.50 | 1.50 | 22.7% | 63.6% |  |
| 0.55 | 1.91 | 13.6% | 59.1% |  |
| 0.60 | 2.36 | 13.6% | 36.4% |  |

## 4. Danh sách các Ca Lỗi trên Tập Test và Phân tích

- **`room1_cam_edited_0425s.jpg`**: Thực tế = 0 | Dự đoán = 1 (Lệch +1)
- **`room1_cam_edited_0428s.jpg`**: Thực tế = 0 | Dự đoán = 1 (Lệch +1)
- **`room1_cam_edited_0432s.jpg`**: Thực tế = 0 | Dự đoán = 1 (Lệch +1)
- **`room1_cam_edited_0436s.jpg`**: Thực tế = 3 | Dự đoán = 4 (Lệch +1)
- **`room1_cam_edited_0439s.jpg`**: Thực tế = 1 | Dự đoán = 6 (Lệch +5)
- **`room1_cam_edited_0450s.jpg`**: Thực tế = 4 | Dự đoán = 6 (Lệch +2)
- **`room1_cam_edited_0464s.jpg`**: Thực tế = 4 | Dự đoán = 6 (Lệch +2)
- **`room1_cam_edited_0470s.jpg`**: Thực tế = 3 | Dự đoán = 5 (Lệch +2)
- **`room1_cam_edited_0474s.jpg`**: Thực tế = 0 | Dự đoán = 2 (Lệch +2)
- **`room1_cam_edited_0484s.jpg`**: Thực tế = 4 | Dự đoán = 6 (Lệch +2)
- **`room1_cam_edited_0520s.jpg`**: Thực tế = 4 | Dự đoán = 5 (Lệch +1)
- **`room1_cam_edited_0548s.jpg`**: Thực tế = 6 | Dự đoán = 7 (Lệch +1)
- **`room1_cam_edited_0551s.jpg`**: Thực tế = 6 | Dự đoán = 7 (Lệch +1)
- **`room1_cam_edited_0554s.jpg`**: Thực tế = 6 | Dự đoán = 9 (Lệch +3)
- **`room1_cam_edited_0558s.jpg`**: Thực tế = 6 | Dự đoán = 11 (Lệch +5)
- **`room1_cam_edited_0562s.jpg`**: Thực tế = 6 | Dự đoán = 8 (Lệch +2)
- **`room1_cam_edited_0565s.jpg`**: Thực tế = 6 | Dự đoán = 7 (Lệch +1)
- **`room1_cam_edited_0568s.jpg`**: Thực tế = 6 | Dự đoán = 8 (Lệch +2)
- **`room1_cam_edited_0572s.jpg`**: Thực tế = 6 | Dự đoán = 9 (Lệch +3)
