import qrcode
import json
import os

output_dir = os.path.join(os.path.dirname(__file__), 'qr_samples')
os.makedirs(output_dir, exist_ok=True)

samples = [
    {
        'filename': 'valid_ticket_1.png',
        'data': {'v':1,'ticket':'TICK-8842','room':'room1','seat':'F12','show':'2026-09-29T19:30'}
    },
    {
        'filename': 'valid_ticket_2.png',
        'data': {'v':1,'ticket':'TICK-8843','room':'room1','seat':'C04','show':'2026-09-29T19:30'}
    },
    {
        'filename': 'wrong_room.png',
        'data': {'v':1,'ticket':'TICK-9999','room':'room2','seat':'A01','show':'2026-09-29T19:30'}
    },
    {
        'filename': 'future_show.png',
        'data': {'v':1,'ticket':'TICK-7777','room':'room1','seat':'D05','show':'2029-12-31T23:59'}
    }
]

for sample in samples:
    json_data = json.dumps(sample['data'], separators=(',', ':'))
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(json_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    file_path = os.path.join(output_dir, sample['filename'])
    img.save(file_path)
    print(f"Created: {file_path} -> {json_data}")

print("Done generating new QR samples.")
