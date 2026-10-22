# HƯỚNG DẪN QUY ƯỚC GÁN NHÃN ĐẦU NGƯỜI (CINESIGHT HEAD LABELING GUIDE)
> **Mục tiêu:** Huấn luyện mô hình YOLO nhận diện vị trí ĐẦU người (lớp `head`) trên ảnh camera rạp chiếu phim để phục vụ thuật toán ánh xạ tâm khung vào tọa độ ghế ngồi (point-in-polygon).

---

## 1. LỚP ĐỐI TƯỢNG (CLASSES)
- **Tên lớp:** `head`
- **Class ID:** `0` (duy nhất 1 lớp)

---

## 2. QUY TẮC VẼ KHUNG BAO (BOUNDING BOX)

### 2.1. Vị trí và kích thước khung
- **Phạm vi chuẩn:** Khung phải ôm sát từ **đỉnh đầu/tóc đến đáy cằm**.
- **Không bao gồm:** Tuyệt đối **KHÔNG** kéo khung xuống phần cổ hoặc bờ vai.
- **Tâm khung (Center Point):** Vì thuật toán ánh xạ ghế sử dụng tọa độ tâm khung $(x_{center}, y_{center})$, khung phải cân đối quanh phần đầu để điểm tâm rơi chính xác vào vị trí đầu của người ngồi trên ghế.

### 2.2. Xử lý trường hợp bị che khuất (Occlusion)
- **Che khuất một phần:** Nếu đầu bị che (bởi lưng ghế phía trước, người bên cạnh, tay nghe điện thoại) nhưng vẫn **nhìn thấy từ 50% diện tích đầu trở lên**:
  $\rightarrow$ **VẪN GÁN NHÃN**, và vẽ khung ước lượng cho **TOÀN BỘ đầu** (không chỉ vẽ phần lộ ra) để tâm khung không bị lệch khỏi vị trí ghế.
- **Che khuất quá nhiều:** Nếu đầu bị che khuất trên 50% (chỉ thấy chỏm tóc nhỏ không chắc chắn):
  $\rightarrow$ **BỎ QUA**, không gán nhãn để tránh làm nhiễu mô hình.

### 2.3. Tư thế và góc nhìn
- **Mọi tư thế đều gán:** Người quay lưng lại camera, nghiêng đầu, cúi đầu nhìn điện thoại, tựa đầu vào thành ghế.
- **Người đứng/đi lại:** Nếu có nhân viên hoặc khách đứng dậy đi vệ sinh/ra về trong tầm quan sát của camera: **VẪN GÁN NHÃN ĐẦU** (để AI phát hiện đúng là có người).

### 2.4. Ngưỡng kích thước tối thiểu (Minimum Size)
- **Ngưỡng:** Chiều cao khung đầu $\ge 12$ pixels trên ảnh gốc Full HD 1920x1080.
- **Quy tắc:** Các vùng quá xa xôi ở góc khuất camera mà đầu người nhỏ hơn 12 px hoặc mờ nhạt không rõ hình thù: **KHÔNG GÁN NHÃN**. Áp dụng nhất quán trên toàn bộ tập dữ liệu.

### 2.5. Xử lý khung hình không có người (Background / Negative Images)
- Nếu một khung hình (ví dụ lúc phòng chiếu hoàn toàn vắng khách trước giờ mở cửa) không có bất kỳ đầu người nào:
  $\rightarrow$ Giữ nguyên file `.txt` rỗng (kích thước 0 byte). Đây là ảnh nền quan trọng giúp mô hình giảm thiểu cảnh báo giả (False Positives). Tỉ lệ ảnh nền khuyến nghị: khoảng 5% - 10% tổng số ảnh.

---

## 3. ĐỊNH DẠNG TỆP NHÃN YOLO
Mỗi file `.txt` lưu cùng tên với file ảnh (ví dụ `room1_cam_edited_0012s.txt`).
Mỗi dòng đại diện cho một đầu người với 5 giá trị cách nhau bằng dấu cách:
```text
0 <x_center> <y_center> <width> <height>
```
*Tất cả các giá trị tọa độ đều được chuẩn hóa về khoảng $[0.0, 1.0]$.*

