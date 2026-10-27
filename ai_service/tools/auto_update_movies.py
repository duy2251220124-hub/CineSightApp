"""Script tự động hóa 1-Click:
1. Tự tìm file snapshot TMDB mới nhất trong ai_service/data_raw/tmdb_sync_*.json.
2. Tự động nạp danh mục phim vào CSDL SQLite (sync_movies.py).
3. Tự động sinh lịch chiếu 7 ngày kể từ ngày hôm nay (generate_showtimes.py --write).
4. Kiểm tra thẩm định 11 quy tắc rạp chiếu (validate_showtimes.py).
"""
import glob
import os
import subprocess
import sys
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PYTHON_EXE = sys.executable

DATA_RAW_DIR = os.path.join(AI_SERVICE_DIR, "data_raw")
snapshots = sorted(glob.glob(os.path.join(DATA_RAW_DIR, "tmdb_sync_*.json")))

if not snapshots:
    print(f"[LỖI] Không tìm thấy file snapshot tmdb_sync_*.json nào trong {DATA_RAW_DIR}")
    sys.exit(1)

latest_snapshot = snapshots[-1]
snapshot_name = os.path.basename(latest_snapshot)
print(f"======================================================================")
print(f" [CINESIGHT] TỰ ĐỘNG CẬP NHẬT PHIM VÀ LẬP LỊCH CHIẾU")
print(f" - File snapshot mới nhất: {snapshot_name}")
print(f"======================================================================")

# 1. Nạp phim vào DB
print(f"\n[BƯỚC 1/3] Đang nạp danh mục phim từ {snapshot_name}...")
sync_script = os.path.join(CURRENT_DIR, "sync_movies.py")
ret = subprocess.run([PYTHON_EXE, sync_script, "--from-snapshot", latest_snapshot])
if ret.returncode != 0:
    print("[LỖI] Không thể nạp phim vào CSDL.")
    sys.exit(ret.returncode)

# 2. Sinh lịch chiếu cho 7 ngày tới
today_str = date.today().isoformat()
print(f"\n[BƯỚC 2/3] Đang sinh lịch chiếu 7 ngày kể từ hôm nay ({today_str})...")
gen_script = os.path.join(CURRENT_DIR, "generate_showtimes.py")
ret = subprocess.run([PYTHON_EXE, gen_script, "--from", today_str, "--days", "7", "--write", "--brief"])
if ret.returncode != 0:
    print("[LỖI] Không thể sinh lịch chiếu.")
    sys.exit(ret.returncode)

# 3. Thẩm tra quy tắc rạp chiếu
print(f"\n[BƯỚC 3/3] Đang thẩm tra 11 quy tắc lập lịch rạp chiếu...")
val_script = os.path.join(CURRENT_DIR, "validate_showtimes.py")
subprocess.run([PYTHON_EXE, val_script])

print(f"\n======================================================================")
print(f" [HOÀN TẤT] Hệ thống đã cập nhật phim và lịch chiếu thành công!")
print(f"======================================================================")

