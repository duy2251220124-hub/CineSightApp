import os
import shutil
import json
import qrcode
from PIL import Image, ImageDraw, ImageFont

output_dir = 'tools/qr_sample'
os.makedirs(output_dir, exist_ok=True)

# 1. Copy CCTV image
src_cctv = r'C:/Users/Dell KIM ANH/.gemini/antigravity/brain/779a87a8-afe5-44b9-9038-d06517f57dee/.user_uploaded/media_1792669880147_d414efe1.jpg'
dst_cctv = os.path.join(output_dir, 'CAMERA_CCTV_RAP1_TODAY.jpg')
shutil.copyfile(src_cctv, dst_cctv)
print('Copied CCTV test frame to:', dst_cctv)

# 2. Test tickets specification for TODAY 2026-10-22
tickets = [
    {
        'id': 'TICK-TODAY-G05',
        'file_prefix': '01_VE_HOP_LE_G05',
        'title': 'VE HOP LE (GHE G05)',
        'room': 'room1',
        'room_name': 'Phong Chieu 1',
        'show': '2026-10-22T20:00',
        'show_time': '20:00 - 22:00 (Hom nay 22/10/2026)',
        'seat': 'G05',
        'movie': 'Spider-Man: Brand New Day',
        'customer': 'Nguyen Van A',
        'expected': 'HOP LE - Quet thanh cong lan 1. AI xac nhan ghe co nguoi!',
        'bg_color': (17, 24, 39),
        'accent': (16, 185, 129) # emerald
    },
    {
        'id': 'TICK-TODAY-G06',
        'file_prefix': '02_VE_HOP_LE_G06',
        'title': 'VE HOP LE (GHE G06)',
        'room': 'room1',
        'room_name': 'Phong Chieu 1',
        'show': '2026-10-22T20:00',
        'show_time': '20:00 - 22:00 (Hom nay 22/10/2026)',
        'seat': 'G06',
        'movie': 'Spider-Man: Brand New Day',
        'customer': 'Tran Thi B',
        'expected': 'HOP LE - Quet thanh cong lan 1. AI xac nhan ghe co nguoi!',
        'bg_color': (17, 24, 39),
        'accent': (16, 185, 129) # emerald
    },
    {
        'id': 'TICK-ERR-ROOM2',
        'file_prefix': '03_VE_SAI_PHONG_ROOM2',
        'title': 'VE LOI: SAI PHONG CHIEU',
        'room': 'room2',
        'room_name': 'Phong Chieu 2',
        'show': '2026-10-22T20:00',
        'show_time': '20:00 - 22:00 (Hom nay 22/10/2026)',
        'seat': 'C04',
        'movie': 'Spider-Man: Brand New Day',
        'customer': 'Le Sai Phong',
        'expected': 'BAO DO - Ve sai phong (Khach mua Phong 2 nhung vao Phong 1)!',
        'bg_color': (31, 19, 21),
        'accent': (239, 68, 68) # red
    },
    {
        'id': 'TICK-ERR-SHOWTIME',
        'file_prefix': '04_VE_SAI_SUAT_0830',
        'title': 'VE LOI: SAI SUAT CHIEU',
        'room': 'room1',
        'room_name': 'Phong Chieu 1',
        'show': '2026-10-22T08:30',
        'show_time': '08:30 - 10:15 (Suat chieu sang)',
        'seat': 'G07',
        'movie': '2DDUB Crayon Shinchan',
        'customer': 'Pham Sai Suat',
        'expected': 'BAO DO - Ve sai suat (Suat sang 08:30 di nham vao suat toi 20:00)!',
        'bg_color': (30, 27, 18),
        'accent': (245, 158, 11) # amber
    }
]

for t in tickets:
    payload = {
        'ticket': t['id'],
        'room': t['room'],
        'seat': t['seat'],
        'show': t['show'],
        'movie': t['movie'],
        'customer': t['customer']
    }
    json_str = json.dumps(payload, separators=(',', ':'))

    # Generate QR Code image
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=3
    )
    qr.add_data(json_str)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB')

    # 1. Pure QR file
    pure_qr_path = os.path.join(output_dir, f"{t['file_prefix']}_QR_ONLY.png")
    qr_img.save(pure_qr_path)

    # 2. Visual Ticket Card (Width: 600, Height: 850)
    card = Image.new('RGB', (600, 850), color=t['bg_color'])
    draw = ImageDraw.Draw(card)

    # Header bar
    draw.rectangle([(0, 0), (600, 70)], fill=t['accent'])
    draw.text((300, 35), t['title'], fill=(255, 255, 255), anchor='mm')

    # Card info
    draw.text((40, 95), 'HE THONG CINESIGHT - VE XEM PHIM TEST', fill=(156, 163, 175))
    draw.text((40, 125), f"Phim: {t['movie']}", fill=(255, 255, 255))
    draw.text((40, 160), f"Suat: {t['show_time']}", fill=(56, 189, 248))
    draw.text((40, 195), f"Phong: {t['room_name']} ({t['room']}) -- Ghe: {t['seat']}", fill=(251, 191, 36))
    draw.text((40, 230), f"Khach: {t['customer']} -- Ma: {t['id']}", fill=(229, 231, 235))

    # Separator
    draw.line([(30, 265), (570, 265)], fill=(55, 65, 81), width=1)

    # Paste QR in center
    qr_resized = qr_img.resize((380, 380), Image.Resampling.LANCZOS)
    qr_x = (600 - 380) // 2
    qr_y = 285
    card.paste(qr_resized, (qr_x, qr_y))

    # Bottom notes
    draw.line([(30, 685), (570, 685)], fill=(55, 65, 81), width=1)
    draw.text((300, 710), f"KY VONG: {t['expected']}", fill=t['accent'], anchor='mm')
    draw.text((300, 745), 'Quet ma bang CineSight Mobile App tren man hinh', fill=(156, 163, 175), anchor='mm')
    draw.text((300, 775), 'Anti-passback: Quet lai lan 2 de test loi VE DA QUET', fill=(107, 114, 128), anchor='mm')
    draw.text((300, 810), f"Raw: {json_str[:60]}...", fill=(75, 85, 99), anchor='mm')

    card_path = os.path.join(output_dir, f"{t['file_prefix']}.png")
    card.save(card_path)
    print(f"Generated: {card_path} and {pure_qr_path}")

print("All 4 test QR tickets generated successfully!")

