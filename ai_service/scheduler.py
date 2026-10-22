"""Bộ sinh lịch suất chiếu mô phỏng (Scheduler) cho CineSight.
Chỉ dùng thư viện chuẩn: datetime, hashlib, random.
Hàm thuần túy, không phụ thuộc CSDL bên ngoài, không gọi mạng.
"""
import datetime
from datetime import date, datetime as dt_cls, timedelta, timezone
import hashlib
import random
import sys

# Múi giờ chuẩn Việt Nam UTC+7
TZ_VN = timezone(timedelta(hours=7))


class SchedulerConfig:
    """Cấu hình tham số sinh lịch tập trung, không dùng số cứng rải rác."""
    def __init__(
        self,
        ROOMS=None,
        OPEN_MIN=510,             # 08:30
        ROOM_OFFSET_MIN=None,
        LAST_START_MIN=1350,      # 22:30
        GAP_MIN=15,               # Nghỉ giữa 2 suất 15 phút
        ALLOW_PAST_MIDNIGHT=True,
        MIN_RUNTIME=60,
        MAX_RUNTIME=240,
        WINDOW_DAYS=90,
        NEW_MOVIE_DAYS=14,
        NEW_WEIGHT=3.0,
        OLD_WEIGHT=1.0,
        TZ=None,
        DEFAULT_DAYS=7,
    ):
        self.ROOMS = list(ROOMS) if ROOMS is not None else ["room1", "room2", "room3", "room4"]
        self.OPEN_MIN = OPEN_MIN
        self.ROOM_OFFSET_MIN = dict(ROOM_OFFSET_MIN) if ROOM_OFFSET_MIN is not None else {
            "room1": 0,
            "room2": 10,
            "room3": 25,
            "room4": 45,
        }
        self.LAST_START_MIN = LAST_START_MIN
        self.GAP_MIN = GAP_MIN
        self.ALLOW_PAST_MIDNIGHT = ALLOW_PAST_MIDNIGHT
        self.MIN_RUNTIME = MIN_RUNTIME
        self.MAX_RUNTIME = MAX_RUNTIME
        self.WINDOW_DAYS = WINDOW_DAYS
        self.NEW_MOVIE_DAYS = NEW_MOVIE_DAYS
        self.NEW_WEIGHT = NEW_WEIGHT
        self.OLD_WEIGHT = OLD_WEIGHT
        self.TZ = TZ or TZ_VN
        self.DEFAULT_DAYS = DEFAULT_DAYS


# Cấu hình mặc định toàn hệ thống
DEFAULT_CONFIG = SchedulerConfig()


def ceil5(m: int) -> int:
    """Làm tròn lên bội số gần nhất của 5 phút."""
    return ((m + 4) // 5) * 5


def seed_for(date_str: str, room_id: str) -> int:
    """Sinh seed số nguyên xác định (deterministic) 64-bit từ SHA256.
    Tuyệt đối không dùng hash() của Python vì hash() đổi giá trị ngẫu nhiên mỗi lần chạy."""
    h = hashlib.sha256(f"{date_str}|{room_id}".encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def minutes_to_hhmm(m: int) -> str:
    """Chuyển số phút từ 00:00 sang chuỗi HH:mm (chỉ dùng cho giờ bắt đầu < 1440)."""
    return f"{m // 60:02d}:{m % 60:02d}"


def normalize_movie(row_or_dict) -> dict:
    """Chuẩn hóa dữ liệu phim từ sqlite3.Row hoặc dict thành dict thống nhất:
    {"id", "title", "runtime", "release_date", "is_active"}.
    """
    d = dict(row_or_dict)
    m_id = d.get("id")

    # Ưu tiên: title_override > title_vi > title_original > Phim #id
    title_override = d.get("title_override")
    title_vi = d.get("title_vi")
    title_orig = d.get("title_original")
    if title_override:
        title = title_override
    elif title_vi:
        title = title_vi
    elif title_orig:
        title = title_orig
    else:
        title = f"Phim #{m_id}"

    # Thời lượng: runtime_override > runtime_min
    runtime_override = d.get("runtime_override")
    runtime_min = d.get("runtime_min")
    if runtime_override is not None and runtime_override > 0:
        runtime = int(runtime_override)
    elif runtime_min is not None:
        try:
            runtime = int(runtime_min)
        except (ValueError, TypeError):
            runtime = 0
    else:
        runtime = 0

    # Ngày khởi chiếu: parse sang datetime.date
    raw_rel = d.get("release_date")
    rel_date = None
    if raw_rel:
        try:
            rel_date = date.fromisoformat(str(raw_rel)[:10])
        except (ValueError, TypeError):
            rel_date = None

    is_active = bool(d.get("is_active", 1))

    return {
        "id": m_id,
        "title": title,
        "runtime": runtime,
        "release_date": rel_date,
        "is_active": is_active,
    }


def is_eligible(movie: dict, day: date, is_active: bool, cfg: SchedulerConfig) -> bool:
    """Kiểm tra phim có đủ điều kiện xếp lịch cho ngày `day` không:
    - is_active là True
    - runtime là số nguyên và MIN_RUNTIME <= runtime <= MAX_RUNTIME
    - release_date khác None
    - release_date <= day <= release_date + WINDOW_DAYS
    """
    if not is_active:
        return False
    runtime = movie.get("runtime")
    if not isinstance(runtime, int) or not (cfg.MIN_RUNTIME <= runtime <= cfg.MAX_RUNTIME):
        return False
    rel_date = movie.get("release_date")
    if rel_date is None or not isinstance(rel_date, date):
        return False
    # Phim đã khởi chiếu và chưa quá WINDOW_DAYS
    if not (rel_date <= day <= rel_date + timedelta(days=cfg.WINDOW_DAYS)):
        return False
    return True


def filter_eligible(movies: list, day: date, cfg: SchedulerConfig) -> list:
    """Lọc danh sách phim đủ điều kiện xếp lịch cho ngày `day` và sắp xếp theo ID tăng dần."""
    eligible = []
    for m in movies:
        norm = normalize_movie(m)
        if is_eligible(norm, day, norm["is_active"], cfg):
            eligible.append(norm)
    eligible.sort(key=lambda x: x["id"])
    return eligible


def build_room_schedule(day: date, room_id: str, eligible: list, cfg: SchedulerConfig) -> list:
    """Xây dựng lịch chiếu chi tiết cho 1 phòng trong ngày `day` bằng thuật toán gieo hạt xác định."""
    if not eligible:
        return []

    # Khởi tạo RNG với seed cố định
    rng = random.Random(seed_for(day.isoformat(), room_id))
    used = {m["id"]: 0 for m in eligible}
    prev_id = None
    result = []

    # Giờ bắt đầu suất đầu tiên của phòng
    offset = cfg.ROOM_OFFSET_MIN.get(room_id, 0)
    start = ceil5(cfg.OPEN_MIN + offset)

    while start <= cfg.LAST_START_MIN:
        # Không lặp lại cùng một phim ở 2 suất liên tiếp (nếu có từ 2 phim trở lên)
        candidates = [m for m in eligible if not (len(eligible) > 1 and m["id"] == prev_id)]
        if not candidates:
            candidates = eligible

        weights = []
        for m in candidates:
            age = (day - m["release_date"]).days
            base = cfg.NEW_WEIGHT if age <= cfg.NEW_MOVIE_DAYS else cfg.OLD_WEIGHT
            weights.append(base / (1 + used[m["id"]]))

        movie = rng.choices(candidates, weights=weights, k=1)[0]
        end_min = start + movie["runtime"]

        # Nếu không cho phép kết thúc sau 00:00 (1440 phút) thì dừng
        if (not cfg.ALLOW_PAST_MIDNIGHT) and end_min > 1440:
            break

        result.append({
            "room_id": room_id,
            "movie_id": movie["id"],
            "title": movie["title"],
            "runtime": movie["runtime"],
            "start_min": start,
            "end_min": end_min,
            "show_id": f"{day.isoformat()}T{minutes_to_hhmm(start)}",
        })

        used[movie["id"]] += 1
        prev_id = movie["id"]
        start = ceil5(end_min + cfg.GAP_MIN)

    return result


def build_day_schedule(day: date, rooms: list, movies_rows: list, cfg: SchedulerConfig) -> dict:
    """Xây dựng lịch chiếu toàn cụm rạp cho ngày `day`."""
    eligible = filter_eligible(movies_rows, day, cfg)
    day_schedule = {}
    for room_id in rooms:
        day_schedule[room_id] = build_room_schedule(day, room_id, eligible, cfg)
    return day_schedule


def to_datetimes(day: date, start_min: int, end_min: int, cfg: SchedulerConfig = None) -> tuple:
    """Chuyển đổi (start_min, end_min) thành chuỗi ISO có múi giờ cố định +07:00."""
    tz = cfg.TZ if cfg else TZ_VN
    base_dt = dt_cls(day.year, day.month, day.day, tzinfo=tz)
    start_dt = base_dt + timedelta(minutes=start_min)
    end_dt = base_dt + timedelta(minutes=end_min)
    return (
        start_dt.isoformat(timespec="seconds"),
        end_dt.isoformat(timespec="seconds"),
    )


# ==============================================================================
# LỚP LƯU DỮ LIỆU CSDL (Nhận conn từ ngoài, hỗ trợ kiểm thử DB in-memory)
# ==============================================================================

def load_movie_rows(conn) -> list:
    """Đọc toàn bộ danh sách phim từ bảng movies trong SQLite."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, source, tmdb_id, title_vi, title_original, release_date,
               release_date_source, runtime_min, poster_path, backdrop_path,
               popularity, title_override, runtime_override, is_active,
               fetched_at, created_at, updated_at
        FROM movies
    """)
    cols = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


ALLOWED_TABLES = frozenset({"showtimes", "showtimes_v2"})


def validate_table_name(table_name: str) -> str:
    """Xác thực tên bảng đích phải nằm trong whitelist cho phép để ngăn ngừa SQL Injection."""
    if table_name not in ALLOWED_TABLES:
        allowed = ", ".join(sorted(list(ALLOWED_TABLES)))
        raise ValueError(
            f"Tên bảng '{table_name}' không được phép. Chỉ chấp nhận một trong các bảng sau: [{allowed}]"
        )
    return table_name


def day_has_showtimes(conn, day: date, table_name: str = "showtimes_v2") -> bool:
    """Kiểm tra ngày `day` đã có bất kỳ suất chiếu nào chưa (kể cả đã hủy).
    True nếu > 0 (kích hoạt luật đóng băng không ghi đè)."""
    validate_table_name(table_name)
    cursor = conn.cursor()
    pattern = f"{day.isoformat()}T%"
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE show_id LIKE ?", (pattern,))
    count = cursor.fetchone()[0]
    return count > 0


def persist_day(conn, day: date, day_schedule: dict, created_at_iso: str, cfg: SchedulerConfig = None, table_name: str = "showtimes_v2") -> int:
    """Ghi toàn bộ lịch chiếu của 1 ngày vào SQLite trong đúng 1 transaction duy nhất.
    Nếu có bất kỳ lỗi nào xảy ra (kể cả vi phạm UNIQUE), rollback 100% không để lại dữ liệu dở dang.
    """
    validate_table_name(table_name)
    cfg = cfg or DEFAULT_CONFIG
    cursor = conn.cursor()
    rows_to_insert = []

    for room_id, shows in day_schedule.items():
        for s in shows:
            start_at, end_at = to_datetimes(day, s["start_min"], s["end_min"], cfg)
            rows_to_insert.append((
                s["room_id"],
                s["movie_id"],
                s["show_id"],
                start_at,
                end_at,
                "scheduled",
                created_at_iso,
            ))

    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.executemany(f"""
            INSERT INTO {table_name}
            (room_id, movie_id, show_id, start_at, end_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)
        conn.commit()
        return len(rows_to_insert)
    except Exception as exc:
        conn.rollback()
        raise exc


def run_for_day(conn, day: date, rooms: list, cfg: SchedulerConfig = None, write: bool = False, table_name: str = "showtimes_v2") -> dict:
    """Điều phối sinh lịch cho 1 ngày theo 4 trạng thái:
    - 'skipped': Ngày đã có suất chiếu trong CSDL (bảo vệ đóng băng)
    - 'empty': Không có phim nào đủ điều kiện khởi chiếu
    - 'dry': Lập lịch mô phỏng thành công, không ghi DB
    - 'written': Đã ghi thành công vào CSDL
    """
    validate_table_name(table_name)
    cfg = cfg or DEFAULT_CONFIG

    # 1. Kiểm tra đóng băng ngày đã có lịch
    if day_has_showtimes(conn, day, table_name=table_name):
        return {"status": "skipped", "count": 0, "schedule": {}}

    # 2. Đọc phim và lọc phim đủ điều kiện
    movies = load_movie_rows(conn)
    eligible = filter_eligible(movies, day, cfg)
    if not eligible:
        return {"status": "empty", "count": 0, "schedule": {}}

    # 3. Xây dựng lịch chiếu cho từng phòng
    day_schedule = {}
    total_shows = 0
    for room_id in rooms:
        shows = build_room_schedule(day, room_id, eligible, cfg)
        day_schedule[room_id] = shows
        total_shows += len(shows)

    # 4. Chế độ xem thử (dry-run)
    if not write:
        return {"status": "dry", "count": total_shows, "schedule": day_schedule}

    # 5. Chế độ ghi thật (persist)
    created_at_iso = dt_cls.now(cfg.TZ).isoformat(timespec="seconds")
    persist_day(conn, day, day_schedule, created_at_iso, cfg=cfg, table_name=table_name)
    return {"status": "written", "count": total_shows, "schedule": day_schedule}

