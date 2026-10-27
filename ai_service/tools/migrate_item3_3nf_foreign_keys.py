"""Di trú CSDL Hạng mục 3: Chuẩn hóa 3NF bảng `incidents` + Thiết lập bảng `rooms` & Khóa Ngoại (Foreign Keys).

Các bước thực hiện trong 1 Transaction (All-or-Nothing):
1. Tự động sao lưu `cinesight.db` vào `ai_service/backups/`.
2. Tạo bảng danh mục `rooms` (room1..room4, 136 ghế) làm bảng cha chuẩn cho `room_id`.
3. Đảm bảo bảng `employees` có nhân viên quản trị gốc `id=1` ('admin' - 'Quản trị viên') để không có khóa ngoại mồ côi.
4. Nâng cấp bảng `showtimes`: bổ sung `FOREIGN KEY (room_id) REFERENCES rooms(id)` và `FOREIGN KEY (movie_id) REFERENCES movies(id)`.
5. Nâng cấp bảng `tickets`: bổ sung `FOREIGN KEY (room_id) REFERENCES rooms(id)` và `FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE`.
6. Nâng cấp bảng `alerts`: bổ sung `FOREIGN KEY (room_id) REFERENCES rooms(id)` và `FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE`.
7. Chuẩn hóa 3NF bảng `incidents`:
   - Loại bỏ 4 cột lưu thừa: `reporter_name`, `reporter_role`, `shift_label`, `resolved_by_name`.
   - Làm sạch dữ liệu lịch sử (`seats_config_room1` -> `room1`).
   - Bổ sung 3 khóa ngoại tới `rooms(id)` và `employees(id)`.
8. Kiểm định toàn vẹn tham chiếu bằng `PRAGMA foreign_key_check`.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AI_SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB = os.path.join(AI_SERVICE_DIR, "cinesight.db")
VN_TZ = timezone(timedelta(hours=7))


def get_cols(cur, table):
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]


def get_fks(cur, table):
    return cur.execute(f"PRAGMA foreign_key_list({table})").fetchall()


def clean_room_id(raw_room):
    if not raw_room:
        return None
    cleaned = str(raw_room).replace("seats_config_", "").strip()
    return cleaned if cleaned else None


def migrate(db_path=DEFAULT_DB):
    if not os.path.exists(db_path):
        print(f"[LỖI] Không tìm thấy file CSDL: {db_path}")
        return 1

    # Kiểm tra xem đã di trú chưa
    probe = sqlite3.connect(db_path)
    pcur = probe.cursor()
    inc_cols = get_cols(pcur, "incidents")
    inc_fks = get_fks(pcur, "incidents")
    ticket_fks = get_fks(pcur, "tickets")
    has_rooms = bool(get_cols(pcur, "rooms"))
    probe.close()

    if has_rooms and "reporter_name" not in inc_cols and len(inc_fks) >= 3 and len(ticket_fks) >= 2:
        print("[OK] CSDL đã ở chuẩn 3NF và đầy đủ Khóa Ngoại (Hạng mục 3). Không cần di trú lại.")
        return 0

    # 1. Backup
    backup_dir = os.path.join(AI_SERVICE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(
        backup_dir, f"cinesight_before_item3_3nf_{datetime.now():%Y%m%d_%H%M%S}.db"
    )
    shutil.copy2(db_path, backup_path)
    print(f"[BACKUP] Đã sao lưu CSDL an toàn tại: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.isolation_level = None  # Tự quản lý transaction
    cur = conn.cursor()

    now_iso = datetime.now(VN_TZ).isoformat(timespec="seconds")

    try:
        # Tắt tạm thời foreign_keys trong lúc tái cấu trúc bảng (chuẩn SQLite migration)
        cur.execute("PRAGMA foreign_keys = OFF")
        cur.execute("BEGIN")

        # ------------------------------------------------------------------
        # BƯỚC 1: Tạo bảng `rooms` (Bảng cha cho room_id)
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                total_seats INTEGER NOT NULL DEFAULT 136,
                screen_type TEXT NOT NULL DEFAULT '2D Standard',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        default_rooms = [
            ("room1", "Phòng chiếu 1", 136, "2D Standard", 1, now_iso),
            ("room2", "Phòng chiếu 2", 136, "2D Standard", 1, now_iso),
            ("room3", "Phòng chiếu 3", 136, "2D Standard", 1, now_iso),
            ("room4", "Phòng chiếu 4", 136, "2D Standard", 1, now_iso),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO rooms (id, name, total_seats, screen_type, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            default_rooms,
        )
        print("[1/6] Đã khởi tạo bảng `rooms` (4 phòng chiếu chuẩn, 136 ghế/phòng).")

        # ------------------------------------------------------------------
        # BƯỚC 2: Đảm bảo nhân viên quản trị gốc id=1 tồn tại trong `employees`
        # ------------------------------------------------------------------
        cur.execute(
            """
            INSERT OR IGNORE INTO employees (id, username, password, name, role, created_at, shift)
            VALUES (1, 'admin', 'admin123', 'Quản trị viên', 'Quản lý', ?, 'morning')
            """,
            (now_iso,),
        )
        valid_emp_ids = {r[0] for r in cur.execute("SELECT id FROM employees").fetchall()}
        valid_room_ids = {r[0] for r in cur.execute("SELECT id FROM rooms").fetchall()}
        print(f"[2/6] Đã kiểm tra bảng `employees` (IDs hợp lệ: {sorted(valid_emp_ids)}).")

        # ------------------------------------------------------------------
        # BƯỚC 3: Nâng cấp bảng `showtimes` (Thêm FK tới rooms(id) & movies(id))
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE showtimes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                show_id TEXT NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'cancelled')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE RESTRICT,
                UNIQUE (room_id, show_id)
            )
        """)
        cur.execute("""
            INSERT INTO showtimes_new (id, room_id, movie_id, show_id, start_at, end_at, status, created_at)
            SELECT id, room_id, movie_id, show_id, start_at, end_at, status, created_at
            FROM showtimes
        """)
        cur.execute("DROP TABLE showtimes")
        cur.execute("ALTER TABLE showtimes_new RENAME TO showtimes")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_showtimes_room_date ON showtimes(room_id, start_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_showtimes_show_id ON showtimes(show_id)")
        n_showtimes = cur.execute("SELECT COUNT(*) FROM showtimes").fetchone()[0]
        print(f"[3/6] Đã nâng cấp bảng `showtimes` ({n_showtimes} dòng, 2 Khóa Ngoại: rooms & movies).")

        # Đảm bảo mọi cặp (room_id, show_id) đang có trong tickets/alerts đều tồn tại trong showtimes
        first_movie_row = cur.execute("SELECT id FROM movies WHERE is_active=1 ORDER BY id LIMIT 1").fetchone()
        fallback_movie_id = first_movie_row[0] if first_movie_row else 1

        for tbl in ("tickets", "alerts"):
            pairs = cur.execute(f"SELECT DISTINCT room_id, show_id FROM {tbl}").fetchall()
            for r_id, s_id in pairs:
                clean_r = clean_room_id(r_id) or "room1"
                if clean_r not in valid_room_ids:
                    clean_r = "room1"
                exists = cur.execute(
                    "SELECT 1 FROM showtimes WHERE room_id=? AND show_id=?", (clean_r, s_id)
                ).fetchone()
                if not exists and s_id:
                    start_iso = f"{s_id}:00+07:00" if len(s_id) == 16 else s_id
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO showtimes (room_id, movie_id, show_id, start_at, end_at, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'scheduled', ?)
                        """,
                        (clean_r, fallback_movie_id, s_id, start_iso, start_iso, now_iso),
                    )

        # ------------------------------------------------------------------
        # BƯỚC 4: Nâng cấp bảng `tickets` (Thêm 2 Khóa Ngoại tới rooms & showtimes)
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE tickets_new (
                room_id TEXT NOT NULL,
                show_id TEXT NOT NULL,
                ticket_id TEXT NOT NULL,
                seat_id TEXT NOT NULL,
                PRIMARY KEY (room_id, show_id, ticket_id),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
            )
        """)
        ticket_rows = cur.execute("SELECT room_id, show_id, ticket_id, seat_id FROM tickets").fetchall()
        for r_id, s_id, t_id, seat_id in ticket_rows:
            clean_r = clean_room_id(r_id) or "room1"
            cur.execute(
                "INSERT OR IGNORE INTO tickets_new (room_id, show_id, ticket_id, seat_id) VALUES (?, ?, ?, ?)",
                (clean_r, s_id, t_id, seat_id),
            )
        cur.execute("DROP TABLE tickets")
        cur.execute("ALTER TABLE tickets_new RENAME TO tickets")
        n_tickets = cur.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        print(f"[4/6] Đã nâng cấp bảng `tickets` ({n_tickets} dòng, 2 Khóa Ngoại: rooms & showtimes).")

        # ------------------------------------------------------------------
        # BƯỚC 5: Nâng cấp bảng `alerts` (Thêm 2 Khóa Ngoại tới rooms & showtimes)
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE alerts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                show_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                seat_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (room_id, show_id) REFERENCES showtimes(room_id, show_id) ON DELETE CASCADE
            )
        """)
        alert_rows = cur.execute(
            "SELECT id, room_id, show_id, alert_type, seat_id, timestamp, resolved FROM alerts"
        ).fetchall()
        for a_id, r_id, s_id, a_type, seat_id, ts, resolved in alert_rows:
            clean_r = clean_room_id(r_id) or "room1"
            cur.execute(
                """
                INSERT INTO alerts_new (id, room_id, show_id, alert_type, seat_id, timestamp, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (a_id, clean_r, s_id, a_type, seat_id, ts, resolved),
            )
        cur.execute("DROP TABLE alerts")
        cur.execute("ALTER TABLE alerts_new RENAME TO alerts")
        n_alerts = cur.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        print(f"[5/6] Đã nâng cấp bảng `alerts` ({n_alerts} dòng, 2 Khóa Ngoại: rooms & showtimes).")

        # ------------------------------------------------------------------
        # BƯỚC 6: Chuẩn hóa 3NF bảng `incidents` (Bỏ 4 cột lưu thừa + Thêm 3 Khóa Ngoại)
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE incidents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                room_id TEXT NULL,
                show_id TEXT NULL,
                seat_ids TEXT,
                reporter_id INTEGER NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'resolved')),
                resolved_by_id INTEGER NULL,
                resolved_at TEXT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
                FOREIGN KEY (reporter_id) REFERENCES employees(id) ON DELETE SET NULL,
                FOREIGN KEY (resolved_by_id) REFERENCES employees(id) ON DELETE SET NULL
            )
        """)
        inc_rows = cur.execute(
            """
            SELECT id, category, severity, title, description, room_id, show_id, seat_ids,
                   reporter_id, created_at, status, resolved_by_id, resolved_at
            FROM incidents
            """
        ).fetchall()
        cleaned_rooms_count = 0
        for row in inc_rows:
            (
                i_id, cat, sev, title, desc, raw_room, s_id, seat_ids,
                rep_id, created_at, status, res_id, resolved_at
            ) = row
            clean_r = clean_room_id(raw_room)
            if raw_room != clean_r:
                cleaned_rooms_count += 1
            if clean_r is not None and clean_r not in valid_room_ids:
                clean_r = None
            clean_rep_id = rep_id if rep_id in valid_emp_ids else (1 if rep_id is not None else None)
            clean_res_id = res_id if res_id in valid_emp_ids else (1 if res_id is not None else None)
            clean_status = status if status in ("open", "resolved") else "open"

            cur.execute(
                """
                INSERT INTO incidents_new (
                    id, category, severity, title, description, room_id, show_id, seat_ids,
                    reporter_id, created_at, status, resolved_by_id, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    i_id, cat or "other", sev or "normal", title or "", desc or "",
                    clean_r, s_id, seat_ids or "", clean_rep_id, created_at or now_iso,
                    clean_status, clean_res_id, resolved_at
                ),
            )
        cur.execute("DROP TABLE incidents")
        cur.execute("ALTER TABLE incidents_new RENAME TO incidents")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_incidents_room_status ON incidents(room_id, status)")
        n_incidents = cur.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        print(
            f"[6/6] Đã chuẩn hóa 3NF bảng `incidents` ({n_incidents} dòng, "
            f"đã loại bỏ 4 cột lưu thừa, làm sạch {cleaned_rooms_count} mã phòng, thêm 3 Khóa Ngoại)."
        )

        # Kiểm tra toàn vẹn khóa ngoại trước khi COMMIT
        cur.execute("PRAGMA foreign_keys = ON")
        fk_violations = cur.execute("PRAGMA foreign_key_check").fetchall()
        if fk_violations:
            raise RuntimeError(f"Phát hiện vi phạm Khóa Ngoại sau di trú: {fk_violations}")

        cur.execute("COMMIT")
        print("[THÀNH CÔNG] Đã COMMIT Transaction. Kiểm tra PRAGMA foreign_key_check = 0 lỗi!")
        return 0

    except Exception as e:
        cur.execute("ROLLBACK")
        print(f"[ROLLBACK] Đã hoàn tác toàn bộ thay đổi do lỗi: {e}")
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(migrate())

