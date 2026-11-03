# -*- coding: utf-8 -*-
"""
Script xuất tự động Chương 3 Báo cáo Đồ án Tốt nghiệp sang định dạng Word (.docx):
CHƯƠNG 3: THIẾT KẾ HỆ THỐNG (SYSTEM DESIGN) - DỰ ÁN CINESIGHT
Đọc trực tiếp từ docs/CHAPTER3_SYSTEM_DESIGN.md và kết xuất 7 sơ đồ kỹ thuật 300 DPI.
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = r"C:\CineSightApp\docs"
MD_PATH = os.path.join(DOCS_DIR, "CHAPTER3_SYSTEM_DESIGN.md")
FIG_DIR = os.path.join(DOCS_DIR, "figures_ch3")
OUTPUT_DOCX = os.path.join(DOCS_DIR, "CHUONG_3_THIET_KE_HE_THONG.docx")

os.makedirs(FIG_DIR, exist_ok=True)


# ==============================================================================
# 1. HỆ THỐNG VẼ 7 SƠ ĐỒ KỸ THUẬT 300 DPI CHO CHƯƠNG 3
# ==============================================================================

def _draw_box(ax, x, y, w, h, title, lines=None, bg="#EFF6FF", border="#1E3A8A", title_color="#0F172A", fontsize=8.8):
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.6",
        edgecolor=border,
        facecolor=bg,
        linewidth=1.6
    )
    ax.add_patch(box)
    if lines:
        ax.text(x + w / 2, y + h - 2.2, title, fontsize=fontsize + 0.6, fontweight="bold",
                ha="center", va="top", color=title_color)
        body = "\n".join(lines)
        ax.text(x + 1.4, y + h - 5.2, body, fontsize=fontsize,
                ha="left", va="top", color="#1E293B", linespacing=1.35)
    else:
        ax.text(x + w / 2, y + h / 2, title, fontsize=fontsize + 0.4, fontweight="bold",
                ha="center", va="center", color=title_color)


def generate_fig3_1_architecture():
    path = os.path.join(FIG_DIR, "fig3_1_architecture.png")
    fig, ax = plt.subplots(figsize=(13, 9.5), dpi=300)
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Tier 1: Client Tier
    t1 = patches.FancyBboxPatch((2, 68), 126, 29, boxstyle="round,pad=0.8",
                                edgecolor="#1D4ED8", facecolor="#F8FAFC", lw=2.0)
    ax.add_patch(t1)
    ax.text(65, 95.3, "TẦNG 1: GIAO DIỆN NGƯỜI DÙNG & THIẾT BỊ HIỆN TRƯỜNG (CLIENT TIER)",
            fontsize=11, fontweight="bold", ha="center", va="center", color="#1E3A8A")

    _draw_box(ax, 5, 70, 58, 22, "Mobile App — Nhân viên Soát vé (Flutter 3.47)", [
        "• Khối chức năng (features/): auth, home, rooms, scanner, alerts, settings",
        "• Lõi kết nối (ApiClient - Dio): Tự động gắn Bearer Token & Ngrok Header",
        "• Lưu trữ Offline-First (HiveService): scanned_tickets_box,",
        "  scan_history_box, settings_box (Chống quét trùng Anti-passback)"
    ], bg="#ECFDF5", border="#047857", title_color="#065F46")

    _draw_box(ax, 67, 70, 58, 22, "Web Admin — Trung tâm Chỉ huy SOC (React 19 + Vite 8)", [
        "• 8 Trang vận hành (src/pages/): Dashboard, Rooms, Showtimes,",
        "  Tickets, Alerts, Incidents, Employees, Settings",
        "• Tầng tích hợp (cineSightApi.js): 29 hàm RESTful API,",
        "  quản lý BASE_URL động & Bearer Token qua localStorage"
    ], bg="#EFF6FF", border="#1D4ED8", title_color="#1E3A8A")

    # Network Bar
    _draw_box(ax, 12, 57.5, 106, 6.5,
              "TẦNG GIAO TIẾP MẠNG: HTTP/REST (JSON & Multipart) | Localhost / Emulator (10.0.2.2) / LAN IP / Reverse Tunnel\nHeader chuẩn: Authorization: Bearer <HMAC_TOKEN> | X-CineSight-Key | ngrok-skip-browser-warning: true",
              bg="#FEF3C7", border="#D97706", title_color="#92400E", fontsize=8.3)

    # Tier 2: Backend & AI Core
    t2 = patches.FancyBboxPatch((2, 21), 126, 32.5, boxstyle="round,pad=0.8",
                                edgecolor="#0F172A", facecolor="#F1F5F9", lw=2.0)
    ax.add_patch(t2)
    ax.text(65, 51.8, "TẦNG 2: DỊCH VỤ BACKEND & LÕI TRÍ TUỆ NHÂN TẠO (ai_service — FastAPI + Uvicorn)",
            fontsize=11, fontweight="bold", ha="center", va="center", color="#0F172A")

    _draw_box(ax, 5, 43, 120, 6.2,
              "Cổng định tuyến RESTful API (main.py — 33 Endpoints: Auth, Nhân sự, Sự cố, Cảnh báo, Phòng, Phim/Lịch, Vé & AI)",
              bg="#E0E7FF", border="#4338CA", title_color="#312E81", fontsize=8.6)

    _draw_box(ax, 5, 23, 38, 17.5, "Bảo mật & Nghiệp vụ", [
        "• security.py: PBKDF2-HMAC-SHA256",
        "  (100.000 vòng) & HMAC Token",
        "• movies_repo.py: Đồng bộ TMDB",
        "• scheduler.py: Xếp lịch tự động"
    ], bg="#FFFFFF", border="#475569")

    _draw_box(ax, 46, 23, 42, 17.5, "Pipeline Thị giác máy tính & Đối soát", [
        "• YOLOv8n (models/best_head_v2.pt)",
        "  imgsz=800, conf=0.28, iou=0.45",
        "• seat_mapper.py: Điểm neo 0.78,",
        "  Khử trùng phối cảnh, ROI <= 8px"
    ], bg="#FFFBEB", border="#B45309", title_color="#92400E")

    _draw_box(ax, 91, 23, 34, 17.5, "Dữ liệu & Bản đồ Ghế", [
        "• database.py: Truy vấn 3NF",
        "• seats_configs/*.json:",
        "  - Room 1,2,4: 136 ghế (A..L)",
        "  - Room 3 VIP: 132 ghế (A..J)"
    ], bg="#FFFFFF", border="#475569")

    # Tier 3: Database Tier
    _draw_box(ax, 12, 3, 106, 13.5, "TẦNG 3: CƠ SỞ DỮ LIỆU QUAN HỆ CHUẨN 3NF (SQLite — ai_service/cinesight.db)", [
        "• Cấu hình đồng thời: PRAGMA journal_mode = WAL | foreign_keys = ON | busy_timeout = 10000 ms | synchronous = NORMAL",
        "• 10 Bảng hiện hành: rooms (4), movies (25), showtimes (423), tickets (16), alerts (509),",
        "  ai_inference_logs (79), employees (7), incidents (4), configs (1), sqlite_sequence (6)"
    ], bg="#F0FDF4", border="#15803D", title_color="#14532D", fontsize=8.6)

    # Arrows
    for x_arr in (34, 96):
        ax.annotate("", xy=(x_arr, 64.2), xytext=(x_arr, 69.8),
                    arrowprops=dict(arrowstyle="<->", color="#1E3A8A", lw=1.8))
        ax.annotate("", xy=(x_arr, 53.7), xytext=(x_arr, 57.3),
                    arrowprops=dict(arrowstyle="<->", color="#B45309", lw=1.8))
    ax.annotate("", xy=(65, 16.8), xytext=(65, 22.8),
                arrowprops=dict(arrowstyle="<->", color="#15803D", lw=2.0))

    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def generate_fig3_2_ai_pipeline():
    path = os.path.join(FIG_DIR, "fig3_2_ai_pipeline.png")
    fig, ax = plt.subplots(figsize=(12, 10.5), dpi=300)
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 110)
    ax.axis("off")

    stages = [
        (92, 14, "GIAI ĐOẠN 1: TIỀN XỬ LÝ & CHUẨN HÓA HỆ QUY CHIẾU (1920x1080)", [
            "• Giải mã khung hình CCTV qua cv2.imdecode(np_img, cv2.IMREAD_COLOR), lấy kích thước thực (W_img, H_img).",
            "• Tính hệ số tỷ lệ chuẩn hóa: scale_x = 1920.0 / W_img  |  scale_y = 1080.0 / H_img."
        ], "#EFF6FF", "#1D4ED8"),
        (71, 16, "GIAI ĐOẠN 2: SUY LUẬN ĐẦU NGƯỜI YOLOv8n & CHIẾU ĐIỂM NEO PHỐI CẢNH", [
            "• Thực thi mô hình models/best_head_v2.pt (MODEL_IMGSZ = 800, MODEL_CONF = 0.28, iou = 0.45, classes = [0]).",
            "• Hạ điểm neo dọc xuống 78% chiều cao khung bao (vùng cổ/vai) để triệt tiêu sai lệch phối cảnh góc cao:",
            "  cx = ((x1 + x2) / 2.0) * scale_x   |   cy = (y1 + 0.78 * (y2 - y1)) * scale_y   |   bw, bh quy đổi về 1920x1080."
        ], "#ECFDF5", "#047857"),
        (50, 16, "GIAI ĐOẠN 3: BỘ LỌC KHỬ TRÙNG KHOẢNG CÁCH PHỐI CẢNH (PERSPECTIVE SUPPRESSION)", [
            "• Sắp xếp các phát hiện giảm dần theo độ tự tin: normalized_heads.sort(key=lambda p: (-p[2], p[1], p[0])).",
            "• Loại bỏ khung nhận diện kép trên cùng 1 khách ngồi nghiêng đầu khi thỏa mãn đồng thời:",
            "  |cx1 - cx2| < 0.48 * max(bw1, bw2)   VÀ   |cy1 - cy2| < 0.60 * max(bh1, bh2)."
        ], "#FFFBEB", "#D97706"),
        (26, 19, "GIAI ĐOẠN 4: ÁNH XẠ ĐA GIÁC 3 BƯỚC & LỌC VÙNG ROI (process_ai_detections)", [
            "• Bước 1 (Dò dọc đa điểm): Kiểm tra cv2.pointPolygonTest(poly, (hx, check_y), False) >= 0 tại (hy+10, hy+18, hy, hy+5).",
            "• Bước 2 (Bù dung sai viền <= 8px & Lọc ROI): Dò ngang (0, ±0.05*bw) tại hy+10 với khoảng cách có dấu >= -8.0 px",
            "  (Tự động loại bỏ hoàn toàn nhiễu ở cầu thang, lối đi hai bên và loa treo tường).",
            "• Bước 3 (Ràng buộc vật lý 1-1): Mỗi ghế trong set_B nhận tối đa 1 người; tuyệt đối không đẩy tràn sang next_seat."
        ], "#FEF2F2", "#DC2626"),
        (4, 17, "GIAI ĐOẠN 5: ĐỐI SOÁT TẬP HỢP & GHI NHẬT KÝ KIỂM TOÁN (generate_alerts)", [
            "• Đồng bộ chỉ số đếm N_detected = |B|. Đối soát với Tập A (vé đã quét từ bảng tickets):",
            "  Khách lậu (illegal_occupants) = B \\ A  |  Khách vắng (missing_guests) = A \\ B  |  Over-capacity & Cờ no_tickets_warning.",
            "• Cập nhật bảng alerts, lưu nhật ký kiểm toán vào bảng ai_inference_logs và trả JSON Response về Client."
        ], "#F3E8FF", "#7E22CE"),
    ]

    for y, h, title, lines, bg, border in stages:
        _draw_box(ax, 6, y, 108, h, title, lines, bg=bg, border=border, title_color=border, fontsize=8.7)

    for y_top, y_bot in [(92, 87), (71, 66), (50, 45), (26, 21)]:
        ax.annotate("", xy=(60, y_bot), xytext=(60, y_top),
                    arrowprops=dict(arrowstyle="->", color="#0F172A", lw=2.2))

    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def generate_fig3_3_erd():
    path = os.path.join(FIG_DIR, "fig3_3_erd.png")
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Draw 10 tables in 3 columns
    _draw_box(ax, 4, 68, 36, 28, "rooms (4 dòng)", [
        "PK  id : TEXT",
        "    name : TEXT NOT NULL",
        "    total_seats : INTEGER (136/132)",
        "    screen_type : TEXT",
        "    is_active : INTEGER",
        "    created_at : TEXT"
    ], bg="#EFF6FF", border="#1D4ED8")

    _draw_box(ax, 4, 34, 36, 28, "movies (25 dòng)", [
        "PK  id : INTEGER AUTOINCREMENT",
        "    source : TEXT (tmdb/manual)",
        "UK  tmdb_id : INTEGER",
        "    title_vi, title_original : TEXT",
        "    release_date : TEXT",
        "    runtime_min : INTEGER",
        "    poster_path, backdrop_path : TEXT",
        "    popularity : REAL | is_active : INT"
    ], bg="#EFF6FF", border="#1D4ED8")

    _draw_box(ax, 4, 4, 36, 24, "employees (7 dòng)", [
        "PK  id : INTEGER AUTOINCREMENT",
        "UK  username : TEXT",
        "    password : TEXT (PBKDF2 hash)",
        "    name, role (admin/staff) : TEXT",
        "    shift : TEXT | is_active : INT",
        "    last_seen_at : TEXT"
    ], bg="#ECFDF5", border="#047857")

    # Center column
    _draw_box(ax, 50, 56, 38, 36, "showtimes (423 dòng)", [
        "PK  id : INTEGER AUTOINCREMENT",
        "FK  room_id -> rooms.id (CASCADE)",
        "FK  movie_id -> movies.id (RESTRICT)",
        "UK  show_id : TEXT (yyyy-MM-ddTHH:mm)",
        "    start_at, end_at : TEXT",
        "    status : TEXT (scheduled/...)",
        "    created_at : TEXT",
        "    UNIQUE(room_id, show_id)"
    ], bg="#FFFBEB", border="#D97706")

    _draw_box(ax, 50, 22, 38, 28, "incidents (4 dòng)", [
        "PK  id : INTEGER AUTOINCREMENT",
        "    category, severity, title : TEXT",
        "FK  room_id -> rooms.id (SET NULL)",
        "    show_id, seat_ids : TEXT",
        "FK  reporter_id -> employees.id (SET NULL)",
        "FK  resolved_by_id -> employees.id",
        "    status (open/resolved), created_at"
    ], bg="#ECFDF5", border="#047857")

    _draw_box(ax, 50, 4, 38, 13, "configs (1) & sqlite_sequence (6)", [
        "• configs: PK key (TEXT), value (TEXT)",
        "• sqlite_sequence: name, seq (Hệ thống)"
    ], bg="#F1F5F9", border="#475569")

    # Right column
    _draw_box(ax, 98, 74, 38, 22, "tickets (16 dòng)", [
        "PK,FK room_id -> rooms.id (CASCADE)",
        "PK,FK show_id -> showtimes (CASCADE)",
        "PK    ticket_id : TEXT",
        "      seat_id : TEXT NOT NULL"
    ], bg="#FEF2F2", border="#DC2626")

    _draw_box(ax, 98, 46, 38, 24, "alerts (509 dòng)", [
        "PK    id : INTEGER AUTOINCREMENT",
        "FK    room_id -> rooms.id (CASCADE)",
        "FK    show_id -> showtimes (CASCADE)",
        "      alert_type : TEXT",
        "      seat_id : TEXT | resolved : BOOL",
        "      timestamp : DATETIME"
    ], bg="#FEF2F2", border="#DC2626")

    _draw_box(ax, 98, 4, 38, 38, "ai_inference_logs (79 dòng)", [
        "PK    id : INTEGER AUTOINCREMENT",
        "FK    room_id -> rooms.id (CASCADE)",
        "FK    show_id -> showtimes (CASCADE)",
        "      captured_at : TEXT",
        "      image_width, image_height : INT",
        "      total_seats, booked_tickets_count",
        "      detected_heads_count : INT",
        "      mapped_seats_count : INT",
        "      illegal_count, missing_count : INT",
        "      inference_time_ms, yolo_time_ms"
    ], bg="#F3E8FF", border="#7E22CE")

    # Relationship arrows
    arrows = [
        ((40, 80), (50, 78), "#1D4ED8"),
        ((40, 48), (50, 66), "#1D4ED8"),
        ((88, 80), (98, 84), "#DC2626"),
        ((88, 72), (98, 58), "#DC2626"),
        ((88, 62), (98, 30), "#7E22CE"),
        ((40, 16), (50, 32), "#047857"),
        ((22, 68), (50, 42), "#047857"),
    ]
    for src, dst, col in arrows:
        ax.annotate("", xy=dst, xytext=src,
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.8))

    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def _draw_sequence_diagram(filename, title, participants, messages):
    path = os.path.join(FIG_DIR, filename)
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 95)
    ax.axis("off")

    ax.text(65, 92.5, title, fontsize=11.5, fontweight="bold", ha="center", va="center", color="#0F172A")

    n = len(participants)
    xs = [12 + i * (106.0 / max(1, n - 1)) for i in range(n)]

    for x, p_name in zip(xs, participants):
        _draw_box(ax, x - 11, 81, 22, 7.5, p_name, bg="#EFF6FF", border="#1D4ED8", fontsize=8.3)
        ax.plot([x, x], [6, 81], color="#64748B", lw=1.3, ls="--")

    y = 75.5
    step = 68.0 / max(1, len(messages))
    for idx, (src_i, dst_i, label, is_return) in enumerate(messages, start=1):
        x1, x2 = xs[src_i], xs[dst_i]
        col = "#047857" if is_return else "#1E3A8A"
        ls = "--" if is_return else "-"
        if src_i == dst_i:
            ax.annotate("", xy=(x1 + 0.5, y - 2.2), xytext=(x1 + 0.5, y),
                        arrowprops=dict(arrowstyle="->", color="#B45309", lw=1.5,
                                        connectionstyle="arc3,rad=-1.5"))
            ax.text(x1 + 3.5, y - 1.1, f"{idx}. {label}", fontsize=8.2, ha="left", va="center",
                    color="#78350F", fontweight="bold")
        else:
            ax.annotate("", xy=(x2, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="->", color=col, lw=1.6, linestyle=ls))
            mid_x = (x1 + x2) / 2.0
            ax.text(mid_x, y + 1.1, f"{idx}. {label}", fontsize=8.2, ha="center", va="bottom",
                    color="#0F172A", bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="none", alpha=0.85))
        y -= step

    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def generate_all_ch3_figures():
    f1 = generate_fig3_1_architecture()
    f2 = generate_fig3_2_ai_pipeline()
    f3 = generate_fig3_3_erd()
    f4 = _draw_sequence_diagram(
        "fig3_4_seq_auth.png",
        "LUỒNG 1: XÁC THỰC NGƯỜI DÙNG (PBKDF2), CẤP HMAC TOKEN & HEARTBEAT PING",
        ["Nhân sự\n(Admin/Staff)", "Client App\n(Mobile/Web)", "FastAPI\n(main.py)", "Bảo mật\n(security.py)", "SQLite DB\n(cinesight.db)"],
        [
            (0, 1, "Nhập username, password", False),
            (1, 2, "POST /api/v1/auth/login", False),
            (2, 4, "get_employee_by_username() & kiểm tra is_active == 1", False),
            (4, 2, "Trả bản ghi nhân viên (password_hash, role, shift)", True),
            (2, 3, "verify_password(plain, hash) bằng hmac.compare_digest", False),
            (3, 2, "Xác thực hợp lệ & create_token(user_id) (HMAC-SHA256, TTL=12h)", True),
            (2, 4, "touch_employee_last_seen(emp_id) -> Cập nhật last_seen_at", False),
            (2, 1, "HTTP 200 {access_token, user} -> Lưu Hive / localStorage", True),
            (1, 2, "Định kỳ: POST /api/v1/employees/{id}/ping (Bearer Token)", False),
            (2, 4, "Cập nhật last_seen_at -> Duy trì trạng thái Online trên SOC", False),
        ]
    )
    f5 = _draw_sequence_diagram(
        "fig3_5_seq_qr.png",
        "LUỒNG 2: QUÉT MÃ QR VÉ OFFLINE-FIRST TRÊN MOBILE APP & ĐỒNG BỘ TẬP A",
        ["Nhân viên\nSoát vé", "ScannerScreen\n(Flutter)", "HiveService\n(Local Boxes)", "FastAPI\n(main.py)", "SQLite DB\n(cinesight.db)"],
        [
            (0, 1, "Đưa mã QR vé vào khung ngắm Camera", False),
            (1, 1, "Giải mã JSON QR, chuẩn hóa seat_id ('G05') & đối chiếu Suất chiếu", False),
            (1, 2, "isTicketScanned(room_id, show_id, ticket_id)", False),
            (2, 1, "False (Vé mới hợp lệ, chưa bị quét trùng Anti-passback)", True),
            (1, 2, "markTicketScanned() & saveScanRecord(isSynced = false)", False),
            (1, 0, "Hiển thị thẻ XANH: 'VÉ HỢP LỆ - Mời vào ghế'", True),
            (1, 3, "Đồng bộ nền: POST /api/v1/tickets/sync (Bearer Token)", False),
            (3, 4, "Kiểm tra khóa ngoại showtimes & INSERT INTO tickets (Tập A)", False),
            (4, 3, "Xác nhận lưu thành công Tập A", True),
            (3, 1, "HTTP 200 {total_synced} -> Cập nhật Hive isSynced = true", True),
        ]
    )
    f6 = _draw_sequence_diagram(
        "fig3_6_seq_ai.png",
        "LUỒNG 3: SUY LUẬN THỊ GIÁC MÁY TÍNH (/api/v1/analyze) & ĐỐI SOÁT GHẾ 2D",
        ["Người vận hành\n(Admin/Staff)", "Giao diện\nSơ đồ ghế", "FastAPI\n(/api/v1/analyze)", "YOLOv8n &\nSeatMapper", "SQLite DB\n(cinesight.db)"],
        [
            (0, 1, "Chọn Phòng, Suất chiếu & Tải ảnh chụp CCTV", False),
            (1, 2, "POST /api/v1/analyze (Multipart: room_id, show_id, file)", False),
            (2, 3, "Giải mã ảnh, chuẩn hóa 1920x1080 & chạy YOLOv8n (conf=0.28, imgsz=800)", False),
            (3, 3, "Chiếu điểm neo 0.78, Khử trùng phối cảnh & Dò đa giác 3 bước (ROI <= 8px)", False),
            (3, 2, "Trả Tập B (tap_B) & đồng bộ total_detected_people = len(tap_B)", True),
            (2, 4, "Truy vấn Tập A (get_tickets_for_show) & ngưỡng capacity_threshold", False),
            (2, 3, "generate_alerts(): Tính Khách lậu (B \\ A) & Khách vắng (A \\ B)", False),
            (2, 4, "Lưu bảng alerts & ghi nhật ký kiểm toán ai_inference_logs", False),
            (2, 1, "HTTP 200 JSON {summary (kèm no_tickets_warning), details, alerts}", True),
            (1, 0, "Tô màu Sơ đồ ghế 2D (Xanh: Hợp lệ, Đỏ: Khách lậu, Vàng: Vắng mặt)", True),
        ]
    )
    f7 = _draw_sequence_diagram(
        "fig3_7_seq_incidents.png",
        "LUỒNG 4: BÁO CÁO BIÊN BẢN SỰ CỐ HIỆN TRƯỜNG & XỬ LÝ TRÊN TRUNG TÂM SOC",
        ["Nhân viên\n(Mobile App)", "Màn hình\nSự cố / Bàn giao", "FastAPI\n(main.py)", "SQLite DB\n(cinesight.db)", "Quản trị viên\n(Web Admin)"],
        [
            (0, 1, "Nhập loại sự cố (damaged_seat/handover...), mức độ, mã ghế & mô tả", False),
            (1, 2, "POST /api/v1/incidents (Header: Authorization: Bearer <token>)", False),
            (2, 3, "Gán reporter_id, reporter_shift & INSERT INTO incidents (status='open')", False),
            (3, 2, "Trả bản ghi biên bản sự cố vừa tạo", True),
            (2, 1, "HTTP 200 {status: 'success'} -> Báo thành công trên Mobile", True),
            (4, 2, "GET /api/v1/incidents?status=open (Truy vấn từ trang Incidents.jsx)", False),
            (2, 3, "SELECT incidents JOIN employees (Lấy tên người báo cáo)", False),
            (2, 4, "Trả danh sách sự cố đang chờ xử lý", True),
            (4, 2, "Bấm 'Đánh dấu đã xử lý' -> PATCH /api/v1/incidents/{id}/resolve", False),
            (2, 3, "UPDATE incidents SET status='resolved', resolved_by_id, resolved_at", False),
        ]
    )
    return [f1, f2, f3, f4, f5, f6, f7]


# ==============================================================================
# 2. TIỆN ÍCH ĐỊNH DẠNG BẢNG & VĂN BẢN WORD CHUẨN ĐỒ ÁN TỐT NGHIỆP
# ==============================================================================

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))


def set_cell_margins(cell, top=90, bottom=90, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_borders(cell, color="B0B0B0", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f"""
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        </w:tcBorders>
    """)
    tcPr.append(tcBorders)


def clean_md_inline(text: str) -> str:
    """Làm sạch cú pháp Markdown/LaTeX inline để hiển thị đẹp trên Word."""
    s = text.strip()
    # Bỏ link markdown [text](url) -> text
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    # Thay thế ký hiệu LaTeX thông dụng sang ký hiệu Toán học Unicode
    replacements = {
        r"\times": "×",
        r"\setminus": " \\ ",
        r"\le": "≤",
        r"\ge": "≥",
        r"\ll": "≪",
        r"\in": "∈",
        r"\notin": "∉",
        r"\cup": "∪",
        r"\cap": "∩",
        r"\lor": "∨",
        r"\land": "∧",
        r"\theta_{\text{cap}}": "θ_cap",
        r"N_{\text{detected}}": "N_detected",
        r"N_{\text{total\_seats}}": "N_total_seats",
        r"W_{\text{img}}": "W_img",
        r"H_{\text{img}}": "H_img",
        r"\text{scale}_x": "scale_x",
        r"\text{scale}_y": "scale_y",
        r"\max\_w": "max_w",
        r"\max\_h": "max_h",
        r"\max": "max",
        r"\Delta x": "Δx",
        r"\;": " ",
        r"\quad": "   ",
        r"<br>": "\n",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = s.replace("$", "")
    s = s.replace("`", "")
    return s


def add_formatted_runs(p, raw_text: str, font_size=13, default_bold=False, default_italic=False):
    """Phân tách chuỗi có **in đậm** thành các Run Times New Roman chuẩn."""
    text = clean_md_inline(raw_text)
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    for part in parts:
        if not part:
            continue
        is_bold = default_bold
        content = part
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            is_bold = True
            content = part[2:-2]
        run = p.add_run(content)
        run.bold = is_bold
        run.italic = default_italic
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)


def render_markdown_table(doc, table_lines):
    rows_parsed = []
    for line in table_lines:
        stripped = line.strip().strip("|")
        cells = [c.strip() for c in stripped.split("|")]
        # Bỏ dòng phân cách :---
        if all(re.match(r"^:?-{2,}:?$", c) for c in cells if c):
            continue
        rows_parsed.append(cells)

    if not rows_parsed:
        return

    num_cols = max(len(r) for r in rows_parsed)
    tbl = doc.add_table(rows=len(rows_parsed), cols=num_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Tính độ rộng cột cân đối trên tổng khổ giấy 6.5 inches
    total_w = 6.5
    if num_cols == 3:
        widths = [1.4, 3.3, 1.8]
    elif num_cols == 5:
        widths = [1.1, 1.0, 1.3, 0.8, 2.3]
    elif num_cols == 6:
        widths = [0.45, 0.65, 1.45, 1.15, 0.95, 1.85]
    else:
        widths = [total_w / num_cols] * num_cols

    for r_idx, r_data in enumerate(rows_parsed):
        is_header = (r_idx == 0)
        for c_idx in range(num_cols):
            val = r_data[c_idx] if c_idx < len(r_data) else ""
            cell = tbl.rows[r_idx].cells[c_idx]
            cell.width = Inches(widths[c_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_borders(cell, color="B0B0B0", sz="4")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

            p = cell.paragraphs[0]
            p.text = ""
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15

            if is_header:
                set_cell_background(cell, "DCE6F1")
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_formatted_runs(p, val, font_size=11.5, default_bold=True)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 and num_cols >= 5 else WD_ALIGN_PARAGRAPH.LEFT
                add_formatted_runs(p, val, font_size=11.5, default_bold=False)


def build_chapter3_docx():
    figure_paths = generate_all_ch3_figures()
    fig_idx = 0

    with open(MD_PATH, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    doc = Document()

    # Cấu hình lề trang chuẩn Đồ án: Trên 2cm, Dưới 2cm, Trái 3cm, Phải 2cm
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(1.18)
        section.right_margin = Inches(0.79)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_after = Pt(4)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped == "---":
            i += 1
            continue

        # Khối code hoặc Mermaid
        if stripped.startswith("```"):
            lang = stripped[3:].strip().lower()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # Bỏ dòng đóng ```

            if lang == "mermaid":
                if fig_idx < len(figure_paths) and os.path.exists(figure_paths[fig_idx]):
                    p_img = doc.add_paragraph()
                    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_img.paragraph_format.space_before = Pt(6)
                    p_img.paragraph_format.space_after = Pt(4)
                    p_img.add_run().add_picture(figure_paths[fig_idx], width=Inches(6.3))
                    fig_idx += 1
            else:
                # Khối mã nguồn / công thức cấu trúc
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.rows[0].cells[0]
                cell.width = Inches(6.4)
                set_cell_background(cell, "F8FAFC")
                set_cell_borders(cell, color="CBD5E1", sz="4")
                set_cell_margins(cell, top=80, bottom=80, left=140, right=140)
                p_code = cell.paragraphs[0]
                p_code.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_code.paragraph_format.line_spacing = 1.15
                p_code.paragraph_format.space_after = Pt(0)
                r_code = p_code.add_run("\n".join(code_lines))
                r_code.font.name = "Consolas"
                r_code.font.size = Pt(10.5)
                r_code.font.color.rgb = RGBColor(15, 23, 42)
            continue

        # Khối công thức toán học $$ ... $$
        if stripped.startswith("$$") and stripped.endswith("$$"):
            formula_txt = stripped.strip("$").strip()
            formula_txt = formula_txt.replace(r"\frac{1920.0}{W_{\text{img}}}", "1920.0 / W_img")
            formula_txt = formula_txt.replace(r"\frac{1080.0}{H_{\text{img}}}", "1080.0 / H_img")
            formula_txt = formula_txt.replace(r"\left(\frac{x_1 + x_2}{2.0}\right)", "((x1 + x2) / 2.0)")
            formula_txt = formula_txt.replace(r"\left(", "(").replace(r"\right)", ")")
            p_eq = doc.add_paragraph()
            p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_eq.paragraph_format.space_before = Pt(4)
            p_eq.paragraph_format.space_after = Pt(6)
            add_formatted_runs(p_eq, formula_txt, font_size=12.5, default_bold=True, default_italic=True)
            i += 1
            continue

        # Khối bảng Markdown
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i])
                i += 1
            render_markdown_table(doc, table_lines)
            continue

        # Tiêu đề H1..H4
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(12)
            r = p.add_run(clean_md_inline(stripped[2:]))
            r.bold = True
            r.font.size = Pt(16)
            r.font.name = "Times New Roman"
            r.font.color.rgb = RGBColor(15, 23, 42)
            i += 1
            continue

        if stripped.startswith("## "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run(clean_md_inline(stripped[3:]))
            r.bold = True
            r.font.size = Pt(14)
            r.font.name = "Times New Roman"
            r.font.color.rgb = RGBColor(30, 58, 138)
            i += 1
            continue

        if stripped.startswith("### "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(clean_md_inline(stripped[4:]))
            r.bold = True
            r.font.size = Pt(13)
            r.font.name = "Times New Roman"
            r.font.color.rgb = RGBColor(15, 23, 42)
            i += 1
            continue

        if stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(clean_md_inline(stripped[5:]))
            r.bold = True
            r.italic = True
            r.font.size = Pt(12.5)
            r.font.name = "Times New Roman"
            r.font.color.rgb = RGBColor(30, 64, 175)
            i += 1
            continue

        # Chú thích Hình / Bảng (*Hình 3.x...* hoặc *Bảng 3.x...*)
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            caption = stripped.strip("*")
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(10)
            add_formatted_runs(p, caption, font_size=12, default_italic=True)
            i += 1
            continue

        # Danh sách Bullet hoặc Đánh số
        if stripped.startswith("- ") or re.match(r"^\d+\.\s+", stripped):
            p = doc.add_paragraph(style="List Bullet" if stripped.startswith("- ") else None)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.25
            content = stripped[2:] if stripped.startswith("- ") else stripped
            add_formatted_runs(p, content, font_size=13)
            i += 1
            continue

        # Đoạn văn bản thường
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.3
        add_formatted_runs(p, stripped, font_size=13)
        i += 1

    doc.save(OUTPUT_DOCX)
    print(f"[OK] Đã xuất thành công tệp Word: {OUTPUT_DOCX}")
    print(f"[OK] Dung lượng: {os.path.getsize(OUTPUT_DOCX):,} bytes ({os.path.getsize(OUTPUT_DOCX)/1024:.2f} KB)")
    print(f"[OK] Số sơ đồ 300 DPI đã nhúng: {fig_idx}/{len(figure_paths)}")


if __name__ == "__main__":
    build_chapter3_docx()

