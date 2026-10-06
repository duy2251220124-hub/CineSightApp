from ultralytics import YOLO
import cv2
import os

def test():
    print("=== TEST INFERENCE (best_v1.pt) ===")
    model_path = "best_v1.pt"
    
    if not os.path.exists(model_path):
        print(f"[!] Không tìm thấy {model_path}. Vui lòng đợi train xong.")
        return
        
    # Load model
    print("[*] Đang load model best_v1.pt...")
    model = YOLO(model_path)
    print("[OK] Đã load model thành công.")
    
    # Chọn ảnh test ngẫu nhiên từ tập val
    test_image = r"datasets\images\val\000000000036.jpg" # Một ảnh bất kỳ trong tập COCO
    if not os.path.exists(test_image):
        import glob
        files = glob.glob(r"datasets\images\val\*.jpg")
        if files:
            test_image = files[0]
        else:
            print("[!] Không tìm thấy ảnh test.")
            return
            
    print(f"[*] Đang chạy Inference trên ảnh: {test_image}")
    
    # Chạy inference
    results = model(test_image, conf=0.1) # Để conf thấp để chắc chắn bắt được
    
    print("\n--- KẾT QUẢ INFERENCE ---")
    boxes = results[0].boxes
    if len(boxes) == 0:
        print("[!] Không phát hiện được đối tượng nào (class 0/head).")
    else:
        print(f"[+] Đã phát hiện {len(boxes)} đối tượng (Head/Person)!")
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            print(f"  - Đối tượng {i+1}: Tọa độ (x1={x1:.1f}, y1={y1:.1f}, x2={x2:.1f}, y2={y2:.1f}) | Độ tin cậy: {conf:.2f}")
    
    # Lưu ảnh ra để xem
    output_path = "test_result.jpg"
    img = results[0].plot()
    cv2.imwrite(output_path, img)
    print(f"\n[OK] Đã xuất ảnh có vẽ bounding box ra file: {output_path}")

if __name__ == "__main__":
    test()

