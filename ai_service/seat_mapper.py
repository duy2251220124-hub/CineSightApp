import cv2
import json
import numpy as np

def load_seats_config(config_path="seats_config.json"):
    """Đọc cấu hình đa giác (polygon) của các ghế đã được calibrate"""
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[-] Lỗi: Không tìm thấy '{config_path}'. Vui lòng chạy calibrate_seats.py trước.")
        return {}

def process_ai_detections(detected_heads, seats_config):
    """
    Hàm ánh xạ đầu người (do AI phát hiện) vào mã ghế.
    
    Args:
        detected_heads: Mảng chứa tâm của các bounding box (x_center, y_center). 
                        (Lấy từ output của YOLO)
        seats_config: Dictionary cấu hình ghế đọc từ JSON.
        
    Returns:
        Tập B (Set): Danh sách các mã ghế ĐANG CÓ NGƯỜI NGỒI.
    """
    # Tập hợp B (những ghế có người)
    set_B = set()
    
    for head in detected_heads:
        head_point = (float(head[0]), float(head[1]))
        
        for seat_name, polygon in seats_config.items():
            # Chuyển đổi list tọa độ sang numpy array
            poly_np = np.array(polygon, np.int32)
            
            # Thuật toán Point in Polygon (OpenCV)
            # Trả về: > 0 (bên trong), 0 (nằm trên viền), < 0 (bên ngoài)
            is_inside = cv2.pointPolygonTest(poly_np, head_point, False)
            
            if is_inside >= 0:
                set_B.add(seat_name)
                # Đã tìm được ghế cho người này, break vòng lặp để check người tiếp theo
                break 
                
    return set_B

def generate_alerts(set_A, set_B):
    """
    Sinh cảnh báo chênh lệch giữa Hệ thống (A) và AI đếm thực tế (B)
    """
    print("\n--- BÁO CÁO KIỂM ĐẾM ---")
    print(f"Tập A (App soát vé ghi nhận) : {set_A}")
    print(f"Tập B (AI Camera đếm được)   : {set_B}")
    
    # B \ A (AI thấy có người, nhưng app soát vé không thấy vé)
    khach_lau = set_B - set_A
    if khach_lau:
        print(f"[CẢNH BÁO ĐỎ] Phát hiện có người ngồi không vé / lọt khách tại các ghế: {khach_lau}")
        
    # A \ B (Đã soát vé nhưng AI thấy ghế trống)
    khach_vang = set_A - set_B
    if khach_vang:
        print(f"[CẢNH BÁO VÀNG] Khách chưa vào rạp hoặc ngồi sai chỗ. Ghế trống: {khach_vang}")
        
    if not khach_lau and not khach_vang:
        print("[OK] Số liệu khớp hoàn toàn! An toàn chiếu phim.")

if __name__ == "__main__":
    # --- MÔ PHỎNG LUỒNG CHẠY THỰC TẾ ---
    
    # 1. Tải cấu hình ghế
    seats_config = load_seats_config()
    
    if seats_config:
        # 2. Giả lập Dữ liệu từ YOLO
        # Trong thực tế, bạn sẽ chạy YOLO.predict(frame), lấy x_center, y_center của các bbox
        mock_detected_heads = [
            (100, 150),  # Tọa độ giả định nằm trong ghế A1
            (300, 400),  # Tọa độ giả định nằm trong ghế B2
            (50, 50)     # Tọa độ nằm ngoài
        ]
        
        # 3. Ánh xạ tọa độ ra mã ghế (Tạo Tập B)
        tap_B = process_ai_detections(mock_detected_heads, seats_config)
        
        # 4. Giả lập Dữ liệu soát vé từ App (Tập A)
        tap_A = {"A1", "A2"} 
        
        # 5. Đối chiếu sinh cảnh báo
        generate_alerts(tap_A, tap_B)

