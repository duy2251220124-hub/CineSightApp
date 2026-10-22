
"""Kiểm tra sự hiện diện của khóa TMDB. KHÔNG gọi mạng, KHÔNG in giá trị khóa.

Chỉ in: "đã có khóa loại X, độ dài N" hoặc "chưa có khóa".
"""
import argparse
import sys

from env_loader import DEFAULT_ENV_PATH, get_tmdb_credential, load_env

# Độ dài tham khảo (chỉ để cảnh báo nhập nhầm loại; không in nội dung khóa):
# API Key v3 thường 32 ký tự; Read Access Token là chuỗi JWT dài (hàng trăm ký tự).
API_KEY_EXPECTED_LEN = 32
READ_TOKEN_MIN_LEN = 100


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Kiểm tra khóa TMDB (không in khóa).")
    parser.add_argument("--env-file", default=None, help="Đường dẫn .env khác (dùng khi test).")
    args = parser.parse_args()

    load_env(args.env_file)
    kind, value = get_tmdb_credential()
    if kind is None:
        print("chưa có khóa")
        return 1

    print(f"đã có khóa loại {kind}, độ dài {len(value)}")
    if kind == "API_KEY" and len(value) != API_KEY_EXPECTED_LEN:
        print(f"CẢNH BÁO: API Key v3 thường dài {API_KEY_EXPECTED_LEN} ký tự; độ dài hiện tại khác.")
    if kind == "READ_TOKEN" and len(value) < READ_TOKEN_MIN_LEN:
        print("CẢNH BÁO: Read Access Token thường rất dài; có thể bạn dán nhầm API Key vào TMDB_READ_TOKEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

