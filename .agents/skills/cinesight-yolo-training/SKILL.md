---
name: cinesight-yolo-training
description: "Applies when preparing video frames, labeling heads, training, evaluating or deploying YOLO models in ai_service (train.py, dataset yaml, datasets, runs, models). Dùng khi trích khung video, gán nhãn, huấn luyện, đánh giá, đưa mô hình vào hệ thống. Prevents data leakage, misleading metrics and privacy leaks."
---

## Nguyên tắc dữ liệu
- Một lớp duy nhất `head` (id 0). Bắt đầu từ `yolov8n.pt` gốc. KHÔNG dùng `best_v1.pt` (huấn luyện trên COCO128, nhãn là "person", không phải đầu người). Không trộn dữ liệu COCO vào dữ liệu rạp.
- Chia train/val/test THEO PHIÊN hoặc theo video, không chia ngẫu nhiên theo khung (các khung cùng phiên gần như giống nhau). Nếu chỉ có một video: chia theo đoạn thời gian cách nhau, ghi khoảng cách nhỏ nhất (giây) giữa khung val/test và khung train gần nhất, và nói rõ rủi ro rò rỉ.
- Tập test và đoạn video demo KHÔNG dùng để huấn luyện, chọn ngưỡng hay chỉnh tham số. Tập test chạy đánh giá MỘT lần với ngưỡng đã chốt trên val.
- Mọi ảnh ghi vào manifest.csv: tệp, video nguồn, mốc thời gian, phòng, tập, cờ "đã kiểm". Nhãn do mô hình tự sinh để riêng; chỉ vào dữ liệu huấn luyện sau khi người đã kiểm từng ảnh.

## Quyền riêng tư
Video chứa khách thật. Không tải video, ảnh hay nhãn lên dịch vụ đám mây. Gitignore: data_raw, datasets, runs, models, *.mp4, *.avi, *.pt. Không đưa ảnh có mặt người vào báo cáo hoặc slide; chỉ dùng ảnh đã làm mờ.

## Huấn luyện
- Đo tốc độ thật (giây/epoch) trên CPU trước khi chọn số epoch. Chạy nền, ghi log vào tệp, có thể resume.
- Ghi lại cấu hình đầy đủ (args.yaml), phiên bản ultralytics/torch/python, mã băm manifest.

## Báo cáo số đo
- Mỗi con số ghi rõ: đo trên tập nào, bao nhiêu ảnh, bao nhiêu khung đầu.
- Số trên val không được gọi là "độ chính xác thực tế". Mục tiêu (mAP@0.5 80-90%, sai số đếm ±1-2 người) là MỤC TIÊU, không phải kết quả.
- Đo cả sai số đếm |dự đoán - nhãn| (trung bình, trung vị, lớn nhất, độ lệch có dấu), không chỉ mAP.
- Ghi giới hạn: số phòng, số góc camera, số phiên, đầu bị che dưới 50% không được gán nhãn.

## Đưa vào hệ thống
Không đổi mô hình trong main.py khi chưa được duyệt. Cấu hình conf và iou lấy từ kết quả trên val. Bản đồ ghế phải được hiệu chuẩn trên khung đúng góc camera; nếu còn là cấu hình giả thì cảnh báo theo ghế chưa đáng tin dù mô hình đếm tốt.
