"""Nạp biến môi trường từ ai_service\.env (chỉ dùng thư viện chuẩn).

Quy tắc:
- Đọc các dòng KEY=VALUE; bỏ dòng trống và dòng bắt đầu bằng '#'.
- KHÔNG ghi đè biến môi trường đã có sẵn (biến hệ thống luôn thắng tệp .env).
- Không bao giờ in giá trị khóa. Dùng redact() cho mọi thông báo lỗi có thể chứa URL/khóa.
"""
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = BASE_DIR / ".env"

# Thứ tự ưu tiên: Read Access Token (gửi qua header Authorization, không nằm trong URL)
# trước, API Key v3 (phải đặt trong query string nên dễ lọt vào log) sau.
TMDB_CREDENTIAL_VARS = (("READ_TOKEN", "TMDB_READ_TOKEN"), ("API_KEY", "TMDB_API_KEY"))


def parse_env_text(text):
    """Phân tích nội dung .env thành dict. Không xử lý chú thích cuối dòng
    (để không cắt nhầm ký tự '#' nằm trong giá trị)."""
    result = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def load_env(path=None):
    """Nạp tệp .env vào os.environ, không ghi đè biến đã có.
    Trả về danh sách TÊN biến đã nạp (không bao giờ trả về giá trị)."""
    env_path = Path(path) if path else DEFAULT_ENV_PATH
    loaded = []
    if not env_path.is_file():
        return loaded
    # utf-8-sig: chịu được BOM do Notepad trên Windows thêm vào.
    text = env_path.read_text(encoding="utf-8-sig")
    for key, value in parse_env_text(text).items():
        if key in os.environ:
            continue
        os.environ[key] = value
        loaded.append(key)
    return loaded


def get_tmdb_credential():
    """Trả về (loại, giá trị) hoặc (None, None). Loại là 'READ_TOKEN' hoặc 'API_KEY'."""
    for kind, var in TMDB_CREDENTIAL_VARS:
        value = os.environ.get(var, "").strip()
        if value:
            return kind, value
    # Tự động nạp từ .env nếu chưa nạp vào os.environ
    load_env()
    for kind, var in TMDB_CREDENTIAL_VARS:
        value = os.environ.get(var, "").strip()
        if value:
            return kind, value
    return None, None


def redact(text, extra_secrets=()):
    """Che khóa trong chuỗi bất kỳ (ví dụ thông báo lỗi của urllib có chèn URL).
    Che: mọi giá trị khóa đang có trong môi trường, tham số api_key=..., và 'Bearer ...'."""
    text = str(text)
    secrets = [os.environ.get(var, "").strip() for _, var in TMDB_CREDENTIAL_VARS]
    secrets += [s for s in extra_secrets if s]
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    text = re.sub(r"(?i)(api_key=)[^&\s'\"]+", r"\1***", text)
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+", r"\1***", text)
    return text

