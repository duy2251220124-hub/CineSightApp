import requests
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = 'http://127.0.0.1:8000'

def test_api():
    print('1. Upload anh de analyze...')
    image_path = 'datasets/images/val/000000000544.jpg'
    with open(image_path, 'rb') as img:
        files = {'image': img}
        data = {'room_id': 'room1', 'show_id': '2026-09-25T19:30'}
        res = requests.post(f'{BASE_URL}/api/v1/analyze', files=files, data=data)
        print('Analyze response status:', res.status_code)

    time.sleep(1)
    
    print('\n2. Lay danh sach alerts...')
    res = requests.get(f'{BASE_URL}/api/v1/alerts')
    alerts = res.json().get('alerts', [])
    print(f'So luong canh bao dang active: {len(alerts)}')
    for a in alerts:
        print(f' - ID: {a["id"]}, Loai: {a["alert_type"]}, Ghe: {a["seat_id"]}')
    
    if alerts:
        first_id = alerts[0]['id']
        print(f'\n3. Danh dau resolve canh bao ID {first_id}...')
        res = requests.post(f'{BASE_URL}/api/v1/resolve_alert/{first_id}')
        print('Resolve response:', res.json())
        
        time.sleep(1)
        
        print('\n4. Kiem tra lai danh sach alerts...')
        res = requests.get(f'{BASE_URL}/api/v1/alerts')
        new_alerts = res.json().get('alerts', [])
        print(f'So luong canh bao con lai: {len(new_alerts)}')
    else:
        print('Khong co canh bao nao de resolve.')

try:
    requests.get(BASE_URL)
    test_api()
except requests.exceptions.ConnectionError:
    print('Server chua chay tren cong 8000.')
