import os
import sys
import argparse
import cv2
import numpy as np

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class HeadLabeler:
    def __init__(self, item_list, base_data_dir, display_size=(1280, 720)):
        """
        item_list: list of (split, filename), ví dụ ('train', 'room1_cam_edited_0000s.jpg')
        """
        self.item_list = item_list
        self.base_data_dir = base_data_dir
        self.img_w, self.img_h = display_size
        
        # VÙNG ĐỆM: Đặt thanh header và footer ở NGOÀI ảnh để KHÔNG che hàng ghế trên cùng!
        self.header_h = 42
        self.footer_h = 32
        self.canvas_w = self.img_w
        self.canvas_h = self.img_h + self.header_h + self.footer_h

        self.current_idx = 0
        self.boxes = []
        self.orig_w = 1920
        self.orig_h = 1080
        
        self.drawing = False
        self.start_pt = None
        self.current_pt = None
        self.window_name = "CineSight - Cong cu gan nhan DAU NGUOI (OpenCV)"

    def get_paths(self, split, filename):
        img_path = os.path.join(self.base_data_dir, "images", split, filename)
        txt_name = os.path.splitext(filename)[0] + ".txt"
        lbl_dir = os.path.join(self.base_data_dir, "labels", split)
        lbl_path = os.path.join(lbl_dir, txt_name)
        prelabel_path = os.path.join(self.base_data_dir, "labels_prelabel", split, txt_name)
        return img_path, lbl_dir, lbl_path, prelabel_path

    def load_labels(self, lbl_path, prelabel_path):
        boxes = []
        is_prelabel = False
        target_path = lbl_path
        if not os.path.exists(lbl_path) and os.path.exists(prelabel_path):
            target_path = prelabel_path
            is_prelabel = True

        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        _, xc, yc, w, h = map(float, parts[:5])
                        x1 = int((xc - w / 2) * self.orig_w)
                        y1 = int((yc - h / 2) * self.orig_h)
                        x2 = int((xc + w / 2) * self.orig_w)
                        y2 = int((yc + h / 2) * self.orig_h)
                        boxes.append([x1, y1, x2, y2])
        return boxes, is_prelabel

    def save_labels(self, lbl_dir, lbl_path):
        os.makedirs(lbl_dir, exist_ok=True)
        with open(lbl_path, "w", encoding="utf-8") as f:
            for b in self.boxes:
                x1, y1, x2, y2 = b
                xmin, xmax = min(x1, x2), max(x1, x2)
                ymin, ymax = min(y1, y2), max(y1, y2)
                w_px = xmax - xmin
                h_px = ymax - ymin
                if w_px <= 2 or h_px <= 2:
                    continue
                xc = (xmin + w_px / 2.0) / self.orig_w
                yc = (ymin + h_px / 2.0) / self.orig_h
                w = w_px / float(self.orig_w)
                h = h_px / float(self.orig_h)
                f.write(f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

    def mouse_callback(self, event, x, y, flags, param):
        # Tọa độ x, y là trên canvas toàn phần
        # Ảnh thực tế nằm từ y = header_h đến y = header_h + img_h
        img_y = y - self.header_h
        img_x = x

        # Giới hạn trong vùng ảnh rạp
        img_x = max(0, min(self.img_w - 1, img_x))
        img_y = max(0, min(self.img_h - 1, img_y))

        # Quy đổi ngược về tọa độ gốc (1920x1080)
        orig_x = int(img_x * (self.orig_w / self.img_w))
        orig_y = int(img_y * (self.orig_h / self.img_h))

        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_pt = (orig_x, orig_y)
            self.current_pt = (orig_x, orig_y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.current_pt = (orig_x, orig_y)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                self.current_pt = (orig_x, orig_y)
                x1, y1 = self.start_pt
                x2, y2 = self.current_pt
                if abs(x2 - x1) > 4 and abs(y2 - y1) > 4:
                    self.boxes.append([min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)])

    def run(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        total_imgs = len(self.item_list)
        if total_imgs == 0:
            print("Danh sách ảnh rỗng!")
            return

        while 0 <= self.current_idx < total_imgs:
            split, img_name = self.item_list[self.current_idx]
            img_path, lbl_dir, lbl_path, prelabel_path = self.get_paths(split, img_name)

            frame = cv2.imread(img_path)
            if frame is None:
                print(f"Lỗi: Không đọc được ảnh {img_path}")
                self.current_idx += 1
                continue

            self.orig_h, self.orig_w = frame.shape[:2]
            self.boxes, is_prelabel = self.load_labels(lbl_path, prelabel_path)

            while True:
                # 1. Vẽ các box lên ảnh rạp gốc
                display_img = frame.copy()
                for b in self.boxes:
                    x1, y1, x2, y2 = b
                    box_color = (0, 255, 255) if is_prelabel else (0, 255, 0)
                    cv2.rectangle(display_img, (x1, y1), (x2, y2), box_color, 2)
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    cv2.circle(display_img, (cx, cy), 3, (0, 0, 255), -1)

                if self.drawing and self.start_pt and self.current_pt:
                    x1, y1 = self.start_pt
                    x2, y2 = self.current_pt
                    cv2.rectangle(display_img, (min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2)), (255, 255, 0), 2)

                # Thu nhỏ ảnh rạp
                resized_frame = cv2.resize(display_img, (self.img_w, self.img_h))

                # 2. Tạo Canvas có vùng đệm trên và dưới (KHÔNG ĐÈ LÊN ẢNH RẠP)
                canvas = np.zeros((self.canvas_h, self.canvas_w, 3), dtype=np.uint8)
                canvas[self.header_h : self.header_h + self.img_h, 0 : self.img_w] = resized_frame

                # 3. Header thông tin
                status_tag = "[TIEN NHAN GOI Y]" if is_prelabel else "[DA XAC MINH]"
                header = f"[{self.current_idx + 1}/{total_imgs}] [{split.upper()}] {img_name} | {status_tag} | Dau: {len(self.boxes)}"
                header_color = (0, 255, 255) if is_prelabel else (0, 255, 0)
                cv2.putText(canvas, header, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, header_color, 2)

                # Đường kẻ phân cách
                cv2.line(canvas, (0, self.header_h - 1), (self.canvas_w, self.header_h - 1), (50, 50, 50), 1)

                # 4. Hướng dẫn phím tắt
                footer_y = self.header_h + self.img_h
                cv2.line(canvas, (0, footer_y), (self.canvas_w, footer_y), (50, 50, 50), 1)
                help_text = "[U] Undo | [C] Clear | [D/Space] Xac nhan & Tiep | [A] Lui | [Q/Esc] Luu & Thoat"
                cv2.putText(canvas, help_text, (12, footer_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

                cv2.imshow(self.window_name, canvas)
                key = cv2.waitKey(20) & 0xFF

                if key in [ord('q'), 27]:  # Q / Esc
                    self.save_labels(lbl_dir, lbl_path)
                    cv2.destroyAllWindows()
                    print(f"Đã lưu tiến độ tại ảnh {self.current_idx + 1}/{total_imgs}. Đóng công cụ.")
                    return

                elif key in [ord('d'), 32]:  # D / Space -> Tiếp
                    self.save_labels(lbl_dir, lbl_path)
                    self.current_idx += 1
                    break

                elif key == ord('a'):  # A -> Lùi lại
                    self.save_labels(lbl_dir, lbl_path)
                    self.current_idx = max(0, self.current_idx - 1)
                    break

                elif key == ord('u'):  # U -> Undo
                    if len(self.boxes) > 0:
                        self.boxes.pop()

                elif key == ord('c'):  # C -> Clear
                    self.boxes = []

        cv2.destroyAllWindows()
        print(f"\nCHÚC MỪNG: Bạn đã hoàn thành duyệt/gán nhãn toàn bộ {total_imgs} ảnh!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Công cụ gán nhãn đầu người CineSight")
    parser.add_argument("--base_dir", default=r"c:\CineSightApp\ai_service\datasets\head_v2", help="Thư mục gốc head_v2")
    parser.add_argument("--mode", default="unverified", choices=["stage_a", "unverified", "all"],
                        help="Chế độ nạp ảnh: 'unverified' (chỉ ảnh chưa duyệt), 'all' (toàn bộ 163 ảnh), 'stage_a' (40 ảnh Stage A)")
    args = parser.parse_args()

    items = []
    if args.mode == "stage_a":
        stage_a_file = os.path.join(args.base_dir, "stage_a_list.txt")
        if os.path.exists(stage_a_file):
            with open(stage_a_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "/" in line:
                        split, fname = line.split("/", 1)
                        items.append((split, fname))
        print(f"Chế độ Giai đoạn A: Nạp {len(items)} ảnh chọn lọc từ stage_a_list.txt")
    else:
        for s in ["train", "val", "test"]:
            s_img_dir = os.path.join(args.base_dir, "images", s)
            s_lbl_dir = os.path.join(args.base_dir, "labels", s)
            if os.path.exists(s_img_dir):
                for f in sorted(os.listdir(s_img_dir)):
                    if f.lower().endswith((".jpg", ".png")):
                        txt_name = os.path.splitext(f)[0] + ".txt"
                        official_lbl = os.path.join(s_lbl_dir, txt_name)
                        if args.mode == "unverified" and os.path.exists(official_lbl):
                            continue
                        items.append((s, f))
        print(f"Chế độ '{args.mode}': Nạp {len(items)} ảnh")

    labeler = HeadLabeler(items, args.base_dir)
    labeler.run()
