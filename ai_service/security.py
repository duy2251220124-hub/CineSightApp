"""Module bảo mật mật khẩu chuẩn NIST/OWASP cho CineSight AI Service.

Sử dụng thuật toán PBKDF2-HMAC-SHA256 (100,000 vòng lặp) kèm Salt ngẫu nhiên 16 bytes
và so sánh chống tấn công thời gian (Timing-Attack Resistant) bằng `hmac.compare_digest`.
Chỉ dùng thư viện chuẩn của Python (`hashlib`, `hmac`, `secrets`), không phụ thuộc thư viện ngoài.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 100_000
SALT_BYTES = 16


def is_password_hashed(value: str) -> bool:
    """Kiểm tra xem chuỗi mật khẩu đã ở định dạng băm PBKDF2-HMAC-SHA256 chưa."""
    if not value or not isinstance(value, str):
        return False
    parts = value.split("$")
    return len(parts) == 4 and parts[0] == ALGORITHM and parts[1].isdigit()


def hash_password(plain_password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Băm mật khẩu chữ thường thành chuỗi chuẩn `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`.
    Nếu đầu vào đã được băm sẵn thì trả về nguyên vẹn (idempotent).
    """
    if plain_password is None:
        raise ValueError("Mật khẩu không được để trống")
    clean_pw = str(plain_password).strip()
    if is_password_hashed(clean_pw):
        return clean_pw

    salt_hex = secrets.token_hex(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        clean_pw.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return f"{ALGORITHM}${int(iterations)}${salt_hex}${dk.hex()}"


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Xác thực mật khẩu người dùng nhập vào với giá trị lưu trong CSDL.
    Sử dụng `hmac.compare_digest` để chống tấn công đo thời gian (Timing Attack).
    """
    if plain_password is None or not stored_password:
        return False
    clean_input = str(plain_password).strip()
    stored_str = str(stored_password).strip()

    if is_password_hashed(stored_str):
        try:
            _, iter_str, salt_hex, expected_hash_hex = stored_str.split("$")
            dk = hashlib.pbkdf2_hmac(
                "sha256",
                clean_input.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iter_str),
            )
            return hmac.compare_digest(dk.hex(), expected_hash_hex)
        except Exception:
            return False

    # Tương thích ngược nếu còn mật khẩu chữ thường chưa di trú
    return hmac.compare_digest(clean_input.encode("utf-8"), stored_str.encode("utf-8"))



# ---------------------------------------------------------------------------
# Token phiên đăng nhập (HMAC-SHA256, dạng JWT rút gọn, chỉ dùng thư viện chuẩn)
# Định dạng: base64url(payload_json) + "." + base64url(HMAC-SHA256(payload))
# ---------------------------------------------------------------------------
TOKEN_TTL_HOURS_DEFAULT = 12
_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".auth_secret")
_secret_cache = None


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def get_secret() -> bytes:
    """Khóa ký token. Ưu tiên biến môi trường CINESIGHT_SECRET; nếu không có thì
    dùng tệp ai_service/.auth_secret (tự sinh lần đầu, đã nằm trong .gitignore)."""
    global _secret_cache
    if _secret_cache:
        return _secret_cache
    env_value = os.environ.get("CINESIGHT_SECRET", "").strip()
    if env_value:
        _secret_cache = env_value.encode("utf-8")
        return _secret_cache
    if not os.path.exists(_SECRET_FILE):
        with open(_SECRET_FILE, "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(32))
    with open(_SECRET_FILE, "r", encoding="utf-8") as f:
        _secret_cache = f.read().strip().encode("utf-8")
    return _secret_cache


def _token_ttl_seconds() -> int:
    try:
        hours = float(os.environ.get("CINESIGHT_TOKEN_TTL_HOURS", TOKEN_TTL_HOURS_DEFAULT))
    except ValueError:
        hours = TOKEN_TTL_HOURS_DEFAULT
    return int(hours * 3600)


def create_token(user_id: int, now: float = None) -> str:
    """Tạo token cho nhân viên. Token chỉ chứa id; vai trò luôn được tra lại từ CSDL
    ở mỗi request nên đổi vai trò hoặc xóa nhân viên có hiệu lực ngay."""
    issued = int(now if now is not None else time.time())
    payload = {"sub": int(user_id), "iat": issued, "exp": issued + _token_ttl_seconds()}
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _b64e(hmac.new(get_secret(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_token(token: str, now: float = None):
    """Trả về user_id (int) nếu token hợp lệ và chưa hết hạn, ngược lại trả None."""
    if not token or not isinstance(token, str) or token.count(".") != 1:
        return None
    body, sig = token.split(".")
    try:
        expected = _b64e(hmac.new(get_secret(), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64d(body).decode("utf-8"))
        current = now if now is not None else time.time()
        if int(payload["exp"]) <= current:
            return None
        return int(payload["sub"])
    except Exception:
        return None
