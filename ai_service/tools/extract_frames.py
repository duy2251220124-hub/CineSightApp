import os
import sys
import argparse
import csv
import cv2
import numpy as np

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def parse_args():
    parser = argparse.ArgumentParser(description="Trích xuất khung hình từ video camera rạp")
    parser.add_argument("--video", default=r"C:\Users\Dell KIM ANH\Downloads\cam_edited.mp4", help="Đường dẫn video")
    parser.add_argument("--room", default="room1", help="Mã phòng chiếu")
    parser.add_argument("--video_name", default="cam_edited", help="Tên nhận diện video")
    parser.add_argument("--out_dir", default=r"c:\CineSightApp\ai_service\datasets\head_v2", help="Thư mục xuất dataset")
    parser.add_argument("--diff_thresh", type=float, default=1.5, help="Ngưỡng khác biệt độ sáng để lọc khung gần trùng (0-255)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not os.path.exists(args.video):
        print(f"LỖI: Không tìm thấy tệp video tại: {args.video}")
        sys.exit(1)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"LỖI: Không thể mở video: {args.video}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0
    print(f"Mở video thành công: {args.video}")
    print(f"FPS: {fps:.2f}, Tổng frame: {total_frames}, Thời lượng: {duration_sec:.2f}s")

    # Cấu hình 4 phiên độc lập theo phân chia đã duyệt:
    # 1. suat1_phim_chieu: 00:00 - 04:25 (0s -> 265s) -> train
    # 2. suat1_den_sang_ra_ve: 04:30 - 05:45 (270s -> 345s) -> train
    # 3. suat1_den_sang_vao_cho: 05:46 - 07:00 (346s -> 420s) -> val
    # 4. suat2_phim_chieu: 07:05 - 09:35 (425s -> 575s) -> test
    sessions = [
        {
            "name": "suat1_phim_chieu",
            "split": "train",
            "start_sec": 0.0,
            "end_sec": 265.0,
            "step_sec": 3.5
        },
        {
            "name": "suat1_den_sang_ra_ve",
            "split": "train",
            "start_sec": 270.0,
            "end_sec": 345.0,
            "step_sec": 3.5
        },
        {
            "name": "suat1_den_sang_vao_cho",
            "split": "val",
            "start_sec": 346.0,
            "end_sec": 420.0,
            "step_sec": 3.5
        },
        {
            "name": "suat2_phim_chieu",
            "split": "test",
            "start_sec": 425.0,
            "end_sec": 575.0,
            "step_sec": 3.5
        }
    ]

    # Tạo cấu trúc thư mục datasets/head_v2/{images,labels}/{train,val,test}
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(args.out_dir, "images", split), exist_ok=True)
        os.makedirs(os.path.join(args.out_dir, "labels", split), exist_ok=True)

    manifest_path = os.path.join(args.out_dir, "manifest.csv")
    manifest_rows = []
    
    # Header theo đúng quy tắc
    manifest_header = [
        "tệp ảnh",
        "video nguồn",
        "mốc thời gian",
        "phòng",
        "phiên",
        "tập (train/val/test)",
        "nhãn đã kiểm (có/không)"
    ]

    total_extracted = 0
    total_skipped_dup = 0
    sampled_records = []
    stats = {}

    for sess in sessions:
        sess_name = sess["name"]
        split = sess["split"]
        start_t = sess["start_sec"]
        end_t = min(sess["end_sec"], duration_sec)
        step_t = sess["step_sec"]

        curr_t = start_t
        prev_gray = None
        sess_count = 0

        while curr_t <= end_t:
            target_frame = int(curr_t * fps)
            if target_frame >= total_frames:
                break

            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if not ret:
                break

            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Lọc khung gần trùng
            if prev_gray is not None:
                diff = float(np.mean(np.abs(curr_gray.astype(np.float32) - prev_gray.astype(np.float32))))
                if diff < args.diff_thresh:
                    total_skipped_dup += 1
                    curr_t += step_t
                    continue

            prev_gray = curr_gray

            # Tên file: <phòng>_<video>_<giây:04d>s.jpg
            sec_int = int(round(curr_t))
            filename = f"{args.room}_{args.video_name}_{sec_int:04d}s.jpg"
            out_img_path = os.path.join(args.out_dir, "images", split, filename)

            # Lưu ảnh JPEG chất lượng cao (95)
            cv2.imwrite(out_img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

            m = int(curr_t // 60)
            s = int(curr_t % 60)
            timestamp_str = f"{m:02d}:{s:02d} ({curr_t:.1f}s)"

            manifest_rows.append([
                filename,
                args.video_name,
                timestamp_str,
                args.room,
                sess_name,
                split,
                "không"
            ])

            sampled_records.append({
                "path": out_img_path,
                "label": f"{split.upper()} | {sess_name} | {m:02d}:{s:02d}"
            })

            sess_count += 1
            total_extracted += 1
            curr_t += step_t

        key = (split, args.room, sess_name)
        stats[key] = sess_count

    cap.release()

    # Ghi manifest.csv
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(manifest_header)
        writer.writerows(manifest_rows)

    # Ghi dataset_head_v2.yaml
    yaml_path = r"c:\CineSightApp\ai_service\dataset_head_v2.yaml"
    yaml_content = f"""path: {args.out_dir.replace(chr(92), '/')}
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: head
"""
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print("\n=== KẾT QUẢ TRÍCH XUẤT KHUNG HÌNH (PHASE 2) ===")
    print(f"Tổng số ảnh trích xuất: {total_extracted}")
    print(f"Số khung gần trùng đã lọc bỏ: {total_skipped_dup}")
    print(f"Đã lưu manifest tại: {manifest_path}")
    print(f"Đã tạo file cấu hình: {yaml_path}")

    # In bảng thống kê
    print("\n=== BẢNG THỐNG KÊ PHÂN BỔ DỮ LIỆU ===")
    print(f"{'TẬP (SPLIT)':<10} | {'PHÒNG':<8} | {'PHIÊN (SESSION)':<26} | {'SỐ ẢNH':<8}")
    print("-" * 62)
    split_totals = {"train": 0, "val": 0, "test": 0}
    session_to_splits = {}
    for (split, room, sess_name), count in stats.items():
        print(f"{split:<10} | {room:<8} | {sess_name:<26} | {count:<8}")
        split_totals[split] += count
        session_to_splits.setdefault(sess_name, set()).add(split)
    print("-" * 62)
    print(f"TỔNG TRAIN: {split_totals['train']} | VAL: {split_totals['val']} | TEST: {split_totals['test']} | TỔNG CỘNG: {total_extracted}")

    # Kiểm tra quy tắc: Không có phiên nào xuất hiện ở 2 tập
    print("\n=== KIỂM TRA TÍNH ĐỘC LẬP CỦA PHIÊN (LEAK CHECK) ===")
    has_leak = False
    for sess_name, splits in session_to_splits.items():
        if len(splits) > 1:
            print(f"CẢNH BÁO: Phiên '{sess_name}' xuất hiện ở nhiều tập: {splits}!")
            has_leak = True
        else:
            print(f"PASS: Phiên '{sess_name}' chỉ thuộc duy nhất tập '{list(splits)[0]}'")
    
    if not has_leak:
        print("KẾT LUẬN: ĐẠT! Không có phiên nào xuất hiện ở 2 tập khác nhau.")

    # Xuất contact sheet 16 khung (4 hàng x 4 cột)
    if len(sampled_records) >= 16:
        sample_indices = np.linspace(0, len(sampled_records) - 1, 16, dtype=int)
        thumbs = []
        tw, th = 480, 270
        for idx in sample_indices:
            rec = sampled_records[idx]
            img = cv2.imread(rec["path"])
            if img is not None:
                resized = cv2.resize(img, (tw, th))
                cv2.rectangle(resized, (5, 5), (380, 32), (0, 0, 0), -1)
                cv2.putText(resized, rec["label"], (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                thumbs.append(resized)

        if len(thumbs) == 16:
            r1 = np.hstack(thumbs[0:4])
            r2 = np.hstack(thumbs[4:8])
            r3 = np.hstack(thumbs[8:12])
            r4 = np.hstack(thumbs[12:16])
            sheet = np.vstack([r1, r2, r3, r4])
            cs_path = r"c:\CineSightApp\ai_service\reports\sampled_frames_contact_sheet.jpg"
            cv2.imwrite(cs_path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
            print(f"\nĐã xuất contact sheet 16 khung chọn lọc tại: {cs_path}")

if __name__ == "__main__":
    main()

