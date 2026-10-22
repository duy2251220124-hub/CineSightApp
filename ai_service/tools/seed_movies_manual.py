"""Kịch bản nạp danh sách 8 phim dự phòng (manual seed) vào bảng movies trong SQLite.
Chỉ dùng thư viện chuẩn: argparse, json, sys, os, pathlib.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Thêm đường dẫn gốc ai_service vào sys.path để import movies_repo
AI_SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from movies_repo import init_movies_tables, upsert_manual_movie, get_all_movies


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Nạp danh sách phim dự phòng vào SQLite.")
    parser.add_argument("--file", default=str(AI_SERVICE_DIR / "data" / "movies_manual.json"), help="Đường dẫn tệp JSON phim thủ công.")
    parser.add_argument("--db", default=None, help="Đường dẫn DB khác (nếu dùng kiểm thử).")
    args = parser.parse_args()

    json_path = Path(args.file)
    if not json_path.is_file():
        print(f"LỖI: Không tìm thấy tệp JSON tại {json_path}")
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        movies_list = json.load(f)

    # 1. Khởi tạo bảng nếu chưa có
    init_movies_tables(args.db)

    print(f"Đang nạp {len(movies_list)} phim từ {json_path.name}...")
    stats = {"inserted": 0, "updated": 0}

    for item in movies_list:
        mid, action = upsert_manual_movie(item, args.db)
        stats[action] += 1
        print(f" - [{action.upper()}] ID={mid:2d} | {item.get('title_vi')} ({item.get('title_original')}) | {item.get('runtime_min')} phút | pop={item.get('popularity')}")

    print("\n=== KẾT QUẢ NẠP PHIM DỰ PHÒNG ===")
    print(f"Thêm mới: {stats['inserted']} | Cập nhật: {stats['updated']} | Tổng cộng: {len(movies_list)}")

    # In lại danh sách đang hoạt động trong DB
    all_movies = get_all_movies(active_only=True, db_path=args.db)
    print(f"Tổng số phim active trong bảng movies: {len(all_movies)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
