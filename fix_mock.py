import os

path = r'c:\CineSightApp\mobile_app\lib\mock\mock_data.dart'
out_path = r'c:\CineSightApp\mobile_app\lib\mock\mock_data_fixed.dart'

with open(path, 'r', encoding='utf-8-sig') as f: # Use utf-8-sig to handle BOM
    text = f.read()

# Try to fix double encoding
fixed = False
try:
    # If the text literally contains 'Gháº¿', it was read as utf-8 but originally meant to be cp1252 bytes interpreted as utf-8
    raw_bytes = text.encode('cp1252')
    fixed_text = raw_bytes.decode('utf-8')
    text = fixed_text
    fixed = True
except Exception as e:
    # Maybe it's not strictly cp1252 double encoded, or it contains mixed strings
    pass

# We can also do a manual dictionary replace for common mojibake just in case
replacements = {
    'Gháº¿': 'Ghế',
    'cÃ³ vÃ©': 'có vé',
    'nhÆ°ng trá»‘ng': 'nhưng trống',
    'ngÆ°á» i': 'người',
    'ChÆ°a soÃ¡t vÃ©': 'Chưa soát vé',
    'Ngá»“i sai gháº¿': 'Ngồi sai ghế',
    'Lá» c khÃ¡ch': 'Lọt khách',
    'KhÃ¡ch chÆ°a cÃ³ vÃ©': 'Khách chưa có vé',
    'Ä Ã£ giáº£i quyáº¿t': 'Đã giải quyết',
    'Chá»  xá»­ lÃ½': 'Chờ xử lý',
    'KhÃ´ng xÃ¡c Ä‘á»‹nh': 'Không xác định',
    'PhÃ²ng': 'Phòng',
    'phÃ²ng': 'phòng',
    'Ä‘ang chiáº¿u': 'đang chiếu',
    'Sáº¯p chiáº¿u': 'Sắp chiếu',
    'vÃ©': 'vé',
    'soÃ¡t': 'soát',
    'suáº¥t': 'suất',
    'thÃ nh cÃ´ng': 'thành công',
    'báº£o trÃ¬': 'bảo trì',
    'Báº£o trÃ¬': 'Bảo trì',
    'mÃ¡y': 'máy',
    'MÃ¡y': 'Máy',
    'MÃƒ': 'MÃ', # Wait, MÃƒ -> MÃ
    'Há»¢P': 'HỢP',
    'Lá»†': 'LỆ',
    'Lá»—i': 'Lỗi',
    'Lá»–I': 'LỖI',
    'Dá»®': 'DỮ',
    'LIá»†U': 'LIỆU',
    'QUÃ‰T': 'QUÉT',
    'THÃ€NH CÃ”NG': 'THÀNH CÔNG',
    'KHÃ”NG': 'KHÔNG',
    'XÃ C': 'XÁC',
    'Ä á»ŠNH': 'ĐỊNH',
    'VÃ‰': 'VÉ',
    'Ä Ãƒ': 'ĐÃ',
    'PHÃ’NG': 'PHÒNG',
    'SUáº¤T': 'SUẤT',
    'Ráº¡p': 'Rạp',
    'Â·': '·',
    'Ã¡': 'á',
    'Ã ': 'à',
    'Ã¢': 'â',
    'Ã£': 'ã',
    'Ã©': 'é',
    'Ã¨': 'è',
    'Ãª': 'ê',
    'Ã­': 'í',
    'Ã¬': 'ì',
    'Ã³': 'ó',
    'Ã²': 'ò',
    'Ã´': 'ô',
    'Ãµ': 'õ',
    'Ãº': 'ú',
    'Ã¹': 'ù',
    'Ã½': 'ý',
    'Ä‘': 'đ',
    'Ä ': 'Đ',
    # More compound vowels
    'áº£': 'ả', 'áº¡': 'ạ',
    'áº¥': 'ấ', 'áº§': 'ầ', 'áº©': 'ẩ', 'áº«': 'ẫ', 'áº­': 'ậ',
    'áº¯': 'ắ', 'áº±': 'ằ', 'áº³': 'ẳ', 'áºµ': 'ẵ', 'áº·': 'ặ',
    'áº»': 'ẻ', 'áº½': 'ẽ', 'áº¹': 'ẹ',
    'áº¿': 'ế', 'á» ': 'ề', 'á»ƒ': 'ể', 'á»…': 'ễ', 'á»‡': 'ệ',
    'á»‰': 'ỉ', 'á»©': 'ĩ', 'á»‹': 'ị',
    'á» ': 'ỏ', 'á»‘': 'ố', 'á»“': 'ồ', 'á»•': 'ổ', 'á»—': 'ỗ', 'á»™': 'ộ',
    'á»›': 'ớ', 'á» ': 'ờ', 'á»Ÿ': 'ở', 'á»¡': 'ỡ', 'á»£': 'ợ',
    'á»§': 'ủ', 'á»©': 'ứ', 'á»«': 'ừ', 'á»': 'ử', 'á»¯': 'ữ', 'á»±': 'ự',
    'á»³': 'ỳ', 'á»µ': 'ỷ', 'á»·': 'ỹ', 'á»¹': 'ỵ',
}

for bad, good in replacements.items():
    text = text.replace(bad, good)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Attempted fix')
