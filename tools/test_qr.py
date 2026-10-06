import sys
import os
import cv2

def decode_qr(filepath):
    img = cv2.imread(filepath)
    if img is None:
        return 'Khong the doc file anh'
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(img)
    return data

print('=== TEST 1: Tuy Chinh ===')
os.system('python make_qr.py --ticket TICK-999 --room room1 --seat C05 --show 2026-10-05T19:30')
qr_custom_path = 'qr_samples/TICK-999.png'
custom_data = decode_qr(qr_custom_path)
print(f'Decoded TICK-999.png: {custom_data}')

print('\n=== TEST 2: Mac Dinh ===')
os.system('python make_qr.py')
qr_default_path = 'qr_samples/valid_ticket_1.png'
default_data = decode_qr(qr_default_path)
print(f'Decoded valid_ticket_1.png: {default_data}')

