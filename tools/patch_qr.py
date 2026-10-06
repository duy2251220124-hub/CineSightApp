import sys

content = '''import qrcode
import json
import os
import argparse
import datetime
import sys

def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        return True
    except ValueError:
        return False

def generate_qr(data_dict, filename, output_dir):
    json_data = json.dumps(data_dict, separators=(',', ':'))
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(json_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    file_path = os.path.join(output_dir, filename)
    img.save(file_path)
    print(f"Created: {file_path} -> {json_data}")

def main():
    parser = argparse.ArgumentParser(description="Generate CineSight QR Codes")
    parser.add_argument("--ticket", help="Ticket ID")
    parser.add_argument("--room", help="Room ID")
    parser.add_argument("--seat", help="Seat ID")
    parser.add_argument("--show", help="Show time (yyyy-MM-ddTHH:mm)")
    parser.add_argument("--output", help="Output filename")
    
    args = parser.parse_args()
    
    output_dir = os.path.join(os.path.dirname(__file__), 'qr_samples')
    os.makedirs(output_dir, exist_ok=True)
    
    if any([args.ticket, args.room, args.seat, args.show, args.output]):
        if not all([args.ticket, args.room, args.seat, args.show]):
            print("Lỗi: Khi tạo QR tùy chỉnh, phải truyền đủ các tham số --ticket, --room, --seat, --show.")
            sys.exit(1)
            
        if not validate_date(args.show):
            print("Lỗi: Định dạng thời gian '--show' không hợp lệ! Yêu cầu: yyyy-MM-ddTHH:mm (VD: 2026-10-05T19:30)")
            sys.exit(1)
            
        filename = args.output if args.output else f"{args.ticket}.png"
        if not filename.endswith('.png'):
            filename += '.png'
            
        data = {'v': 1, 'ticket': args.ticket, 'room': args.room, 'seat': args.seat, 'show': args.show}
        generate_qr(data, filename, output_dir)
        print("Done generating custom QR sample.")
    else:
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
            generate_qr(sample['data'], sample['filename'], output_dir)
        print("Done generating new QR samples.")

if __name__ == '__main__':
    main()
'''

with open(r'c:\CineSightApp\tools\make_qr.py', 'w', encoding='utf-8') as f:
    f.write(content)
