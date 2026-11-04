# -*- coding: utf-8 -*-
"""
Script to generate the formal university thesis Chapter 2 in DOCX format:
CHƯƠNG 2: PHÂN TÍCH YÊU CẦU - DỰ ÁN CINESIGHT
Matches the user's exact Word template structure and updated system specifications.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = r"C:\CineSightApp\docs"
DIAGRAM_PATH = os.path.join(DOCS_DIR, "use_case_diagram.png")
OUTPUT_DOCX = os.path.join(DOCS_DIR, "CHUONG_2_PHAN_TICH_YEU_CAU.docx")


def generate_usecase_diagram():
    """
    Draws a publication-grade UML 2.5 System Use Case Diagram for CineSight
    with a strictly planar (zero line-crossing) 3-column architecture.
    """
    fig, ax = plt.subplots(figsize=(16.5, 11.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.set_xlim(0, 174)
    ax.set_ylim(0, 128)
    ax.axis("off")

    # 1. Outer System Boundary Box with Header Bar
    sys_shadow = patches.FancyBboxPatch(
        (29.6, 6.4), 113.0, 116.0,
        boxstyle="round,pad=1.2,rounding_size=2.0",
        edgecolor="none",
        facecolor="#E2E8F0",
        zorder=1
    )
    ax.add_patch(sys_shadow)

    sys_rect = patches.FancyBboxPatch(
        (29.0, 7.0), 113.0, 116.0,
        boxstyle="round,pad=1.2,rounding_size=2.0",
        edgecolor="#1E3A8A",
        facecolor="#F8FAFC",
        linewidth=2.2,
        zorder=2
    )
    ax.add_patch(sys_rect)

    # Top Header Banner inside System Boundary
    header_rect = patches.FancyBboxPatch(
        (29.0, 117.2), 113.0, 5.8,
        boxstyle="round,pad=1.2,rounding_size=2.0",
        edgecolor="#1E3A8A",
        facecolor="#1E3A8A",
        linewidth=1.5,
        zorder=3
    )
    ax.add_patch(header_rect)
    ax.text(
        85.5, 120.1,
        "«system»  HỆ THỐNG SOÁT VÉ VÀ ĐỐI SOÁT KHÁN GIẢ AI — CINESIGHT",
        fontsize=12.5, fontweight="bold", ha="center", va="center",
        color="#FFFFFF", zorder=4
    )

    # Subtle internal subsystem zone boxes
    zone_ops = patches.FancyBboxPatch(
        (31.5, 9.5), 35.0, 105.0,
        boxstyle="round,pad=0.6,rounding_size=1.5",
        edgecolor="#BFDBFE",
        facecolor="#EFF6FF",
        linewidth=1.1,
        linestyle="--",
        alpha=0.55,
        zorder=2
    )
    ax.add_patch(zone_ops)
    ax.text(
        49.0, 112.8, "Phân hệ Nghiệp vụ & Quản trị",
        fontsize=9.2, fontweight="bold", style="italic",
        ha="center", va="center", color="#1D4ED8", zorder=3
    )

    zone_ai = patches.FancyBboxPatch(
        (69.5, 36.0), 70.0, 78.5,
        boxstyle="round,pad=0.6,rounding_size=1.5",
        edgecolor="#FDE68A",
        facecolor="#FFFBEB",
        linewidth=1.1,
        linestyle="--",
        alpha=0.65,
        zorder=2
    )
    ax.add_patch(zone_ai)
    ax.text(
        104.5, 112.8, "Phân hệ Thị giác máy tính & Đối soát tự động",
        fontsize=9.2, fontweight="bold", style="italic",
        ha="center", va="center", color="#B45309", zorder=3
    )

    # 2. Helper to draw UML Stick Figure Actor with Role Card
    def draw_actor(x, y, title, subtitle, color="#0F172A", badge_bg="#F1F5F9"):
        # Pedestal / Card behind label
        card = patches.FancyBboxPatch(
            (x - 11.5, y - 18.8), 23.0, 7.6,
            boxstyle="round,pad=0.4,rounding_size=1.0",
            edgecolor=color, facecolor=badge_bg, linewidth=1.3, zorder=4
        )
        ax.add_patch(card)

        # Head (with subtle shadow)
        ax.add_patch(patches.Circle((x + 0.3, y + 5.2), 2.3, edgecolor="none", facecolor="#CBD5E1", zorder=3))
        ax.add_patch(patches.Circle((x, y + 5.5), 2.3, edgecolor=color, facecolor="#FFFFFF", lw=2.3, zorder=4))
        # Body
        ax.plot([x, x], [y + 3.2, y - 3.5], color=color, lw=2.5, solid_capstyle="round", zorder=4)
        # Arms
        ax.plot([x - 4.2, x + 4.2], [y + 1.0, y + 1.0], color=color, lw=2.5, solid_capstyle="round", zorder=4)
        # Legs
        ax.plot([x, x - 3.4], [y - 3.5, y - 9.2], color=color, lw=2.5, solid_capstyle="round", zorder=4)
        ax.plot([x, x + 3.4], [y - 3.5, y - 9.2], color=color, lw=2.5, solid_capstyle="round", zorder=4)

        # Label inside card
        ax.text(x, y - 13.7, title, fontsize=10.0, fontweight="bold", ha="center", va="center", color=color, zorder=5)
        ax.text(x, y - 16.8, subtitle, fontsize=8.5, ha="center", va="center", color="#334155", zorder=5)

    # Draw 3 Actors
    draw_actor(13.0, 91.0, "Nhân viên soát vé", "(User / Staff - Mobile App)", color="#047857", badge_bg="#ECFDF5")
    draw_actor(13.0, 36.0, "Quản trị viên", "(Admin - Web Admin)", color="#1E3A8A", badge_bg="#EFF6FF")
    draw_actor(159.5, 68.0, "Hệ thống AI / Camera", "(CCTV & AI Scheduler)", color="#B45309", badge_bg="#FEF3C7")

    # 3. Helper to draw UML Use Case Ellipse with shadow
    def draw_usecase(x, y, code, text, w=29.5, h=7.4, bg="#FFFFFF", border="#1D4ED8", code_bg="#1D4ED8", is_sub=False):
        # Drop shadow
        shadow = patches.Ellipse((x + 0.35, y - 0.35), w, h, edgecolor="none", facecolor="#CBD5E1", alpha=0.65, zorder=3)
        ax.add_patch(shadow)

        ellipse = patches.Ellipse(
            (x, y), w, h,
            edgecolor=border, facecolor=bg,
            linewidth=1.5 if not is_sub else 1.3,
            linestyle="-" if not is_sub else "--",
            zorder=4
        )
        ax.add_patch(ellipse)

        if code:
            full_label = f"{code}: {text}"
            ax.text(
                x, y, full_label,
                fontsize=8.9, fontweight="bold",
                ha="center", va="center", color="#0F172A",
                linespacing=1.22, zorder=5
            )
        else:
            ax.text(
                x, y, text,
                fontsize=8.5, fontweight="semibold" if not is_sub else "normal",
                ha="center", va="center", color="#1E293B",
                linespacing=1.2, zorder=5
            )

    # 4. Define Use Cases in Planar 3-Column Layout
    # Left Column (x = 49.0): Primary Actor Use Cases
    left_ucs = {
        "uc03": (49.0, 105.0, "UC03", "Quét mã QR soát vé\ntại cửa phòng chiếu", "#FFFFFF", "#059669"),
        "uc04": (49.0, 93.0,  "UC04", "Đồng bộ vé Offline-First\n(Hive Box → Server)", "#FFFFFF", "#059669"),
        "uc08": (49.0, 81.0,  "UC08", "Tổng kết & Bàn giao\nca trực", "#FFFFFF", "#059669"),
        "uc01": (49.0, 69.0,  "UC01", "Đăng nhập & Nhận diện\nca trực tự động", "#EFF6FF", "#1D4ED8"),
        "uc06": (49.0, 57.0,  "UC06", "Tiếp nhận & Xử lý cảnh báo\ntheo phòng (1 chạm)", "#EFF6FF", "#1D4ED8"),
        "uc07": (49.0, 45.0,  "UC07", "Báo cáo & Xử lý sự cố\ncơ sở vật chất (kèm ảnh)", "#EFF6FF", "#1D4ED8"),
        "uc02": (49.0, 31.0,  "UC02", "Quản lý phim TMDB &\nLập lịch chiếu tự động", "#FFFFFF", "#1E3A8A"),
        "uc09": (49.0, 17.0,  "UC09", "Quản lý Nhân sự, Phòng\n& Xem Dashboard SOC", "#FFFFFF", "#1E3A8A"),
    }

    for k, (ux, uy, ucode, utext, ubg, uborder) in left_ucs.items():
        draw_usecase(ux, uy, ucode, utext, w=30.0, h=7.8, bg=ubg, border=uborder)

    # Center Column (x = 88.5): Included Sub-Use Cases
    sub_ucs = {
        "inc_qr":   (88.5, 105.0, "", "Kiểm tra hợp lệ &\nChống quét trùng (Anti-passback)"),
        "inc_yolo": (88.5, 86.0,  "", "Nhận diện đầu người\n(Mô hình YOLOv8n)"),
        "inc_map":  (88.5, 68.0,  "", "Chiếu điểm neo 78% &\nÁnh xạ đa giác ghế (1–1)"),
        "inc_diff": (88.5, 50.0,  "", "Đối soát tập hợp (B \\ A, A \\ B)\n& Kiểm tra vượt tải"),
    }

    for k, (ux, uy, ucode, utext) in sub_ucs.items():
        draw_usecase(ux, uy, ucode, utext, w=29.0, h=7.8, bg="#FEF3C7", border="#D97706", is_sub=True)

    # Right Column (x = 125.0): Core AI Engine Use Case
    uc05_pos = (125.0, 68.0)
    draw_usecase(
        uc05_pos[0], uc05_pos[1],
        "UC05", "Phân tích ảnh Camera &\nĐối soát ghế AI tự động",
        w=28.5, h=8.6, bg="#FFF7ED", border="#C2410C"
    )

    # 5. Draw Solid Association Lines (Actors <-> Primary Use Cases)
    # Staff associations (Top-Left Actor)
    staff_anchor = (21.5, 88.0)
    for target_key in ["uc03", "uc04", "uc08", "uc01", "uc06", "uc07"]:
        tx, ty, *_ = left_ucs[target_key]
        ax.plot(
            [staff_anchor[0], tx - 15.0],
            [staff_anchor[1], ty],
            color="#047857", linewidth=1.45, zorder=3
        )

    # Admin associations (Bottom-Left Actor)
    admin_anchor = (21.5, 36.0)
    for target_key in ["uc01", "uc06", "uc07", "uc02", "uc09"]:
        tx, ty, *_ = left_ucs[target_key]
        ax.plot(
            [admin_anchor[0], tx - 15.0],
            [admin_anchor[1], ty],
            color="#1E3A8A", linewidth=1.45, zorder=3
        )

    # Admin -> UC05 (Manual AI trigger) routed cleanly through the open corridor y=24.0 between UC02 (y=31) and UC09 (y=17)
    verts = [
        admin_anchor,
        (36.0, 24.0),
        (72.0, 23.0),
        (105.0, 24.5),
        (122.0, 38.0),
        (uc05_pos[0], uc05_pos[1] - 4.3)
    ]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    curve_patch = patches.PathPatch(
        Path(verts, codes),
        facecolor="none", edgecolor="#1E3A8A", lw=1.45, linestyle="-", zorder=3
    )
    ax.add_patch(curve_patch)
    ax.text(
        92.0, 25.2, "Kích hoạt quét AI thủ công",
        fontsize=8.2, style="italic", fontweight="semibold", color="#1E3A8A", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#FFFFFF", edgecolor="#BFDBFE", lw=0.8),
        zorder=5
    )

    # AI / Camera Actor -> UC05 (Direct horizontal connection on the right)
    ai_anchor = (150.5, 68.0)
    ax.plot(
        [ai_anchor[0], uc05_pos[0] + 14.3],
        [ai_anchor[1], uc05_pos[1]],
        color="#B45309", linewidth=1.8, zorder=3
    )

    # 6. Helper to draw UML <<include>> / <<extend>> dashed arrows with pill badge
    def draw_stereotype_arrow(start_xy, end_xy, label="«include»", color="#475569", label_pos=0.5):
        ax.annotate(
            "",
            xy=end_xy, xytext=start_xy,
            arrowprops=dict(
                arrowstyle="->", color=color, lw=1.35,
                linestyle="--", shrinkA=0, shrinkB=0
            ),
            zorder=4
        )
        lx = start_xy[0] + (end_xy[0] - start_xy[0]) * label_pos
        ly = start_xy[1] + (end_xy[1] - start_xy[1]) * label_pos
        ax.text(
            lx, ly, label,
            fontsize=7.8, style="italic", fontweight="bold", color=color,
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor=color, lw=0.7),
            zorder=6
        )

    # UC03 --<<include>>--> inc_qr
    draw_stereotype_arrow(
        (49.0 + 15.0, 105.0),
        (88.5 - 14.5, 105.0),
        label="«include»", color="#047857"
    )

    # UC05 --<<include>>--> inc_yolo, inc_map, inc_diff
    draw_stereotype_arrow(
        (uc05_pos[0] - 13.0, uc05_pos[1] + 2.2),
        (88.5 + 14.5, 86.0),
        label="«include»", color="#B45309", label_pos=0.48
    )
    draw_stereotype_arrow(
        (uc05_pos[0] - 14.3, uc05_pos[1]),
        (88.5 + 14.5, 68.0),
        label="«include»", color="#B45309", label_pos=0.5
    )
    draw_stereotype_arrow(
        (uc05_pos[0] - 13.0, uc05_pos[1] - 2.2),
        (88.5 + 14.5, 50.0),
        label="«include»", color="#B45309", label_pos=0.48
    )

    # UC06 --<<extend>>--> inc_diff (Triggered when discrepancy B \ A is detected)
    draw_stereotype_arrow(
        (49.0 + 15.0, 57.0),
        (88.5 - 14.5, 50.0),
        label="«extend»", color="#DC2626", label_pos=0.5
    )

    # 7. Legend Bar at Bottom
    legend_box = patches.FancyBboxPatch(
        (29.0, 0.8), 113.0, 4.2,
        boxstyle="round,pad=0.4,rounding_size=1.0",
        edgecolor="#CBD5E1", facecolor="#F8FAFC", linewidth=1.0, zorder=3
    )
    ax.add_patch(legend_box)
    ax.text(33.0, 2.9, "Chú giải UML:", fontsize=8.8, fontweight="bold", color="#0F172A", va="center", zorder=5)
    ax.plot([46.0, 52.0], [2.9, 2.9], color="#1E3A8A", lw=1.8, zorder=5)
    ax.text(53.0, 2.9, "Quan hệ tương tác (Association)", fontsize=8.4, color="#334155", va="center", zorder=5)
    ax.plot([81.0, 87.0], [2.9, 2.9], color="#B45309", lw=1.6, ls="--", zorder=5)
    ax.text(88.0, 2.9, "«include» Quan hệ bắt buộc", fontsize=8.4, color="#334155", va="center", zorder=5)
    ax.plot([114.0, 120.0], [2.9, 2.9], color="#DC2626", lw=1.6, ls="--", zorder=5)
    ax.text(121.0, 2.9, "«extend» Mở rộng khi có vi phạm", fontsize=8.4, color="#334155", va="center", zorder=5)

    plt.tight_layout()
    plt.savefig(DIAGRAM_PATH, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print("Generated professional Use Case diagram at:", DIAGRAM_PATH)


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_borders(cell, color="808080", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        </w:tcBorders>
    ''')
    tcPr.append(tcBorders)


def build_docx():
    generate_usecase_diagram()
    doc = Document()

    # Configure standard academic margins: Left 3.0cm, Right 2.0cm, Top 2.0cm, Bottom 2.0cm
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(1.18)
        section.right_margin = Inches(0.79)

    # Default Normal style
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_after = Pt(4)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def add_p(text, bold_prefix="", bold=False, italic=False, space_after=4, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.3
        if bold_prefix:
            r = p.add_run(bold_prefix)
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(13)
        r2 = p.add_run(text)
        r2.bold = bold
        r2.italic = italic
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(13)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(12)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(16)
        r.font.name = "Times New Roman"
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(14)
        r.font.name = "Times New Roman"
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(13)
        r.font.name = "Times New Roman"
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.25
        if bold_prefix:
            r = p.add_run(bold_prefix)
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(13)
        r2 = p.add_run(text)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(13)
        return p

    def format_table(table, col_widths, align_cols=None):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row_idx, row in enumerate(table.rows):
            is_header = (row_idx == 0)
            for col_idx, cell in enumerate(row.cells):
                cell.width = Inches(col_widths[col_idx])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_borders(cell, color="808080", sz="4")
                set_cell_margins(cell, top=90, bottom=90, left=130, right=130)

                if is_header:
                    set_cell_background(cell, "D9E1F2")
                    for p in cell.paragraphs:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p.paragraph_format.space_after = Pt(0)
                        for r in p.runs:
                            r.bold = True
                            r.font.name = "Times New Roman"
                            r.font.size = Pt(12)
                else:
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(0)
                        p.paragraph_format.line_spacing = 1.15
                        if align_cols and col_idx < len(align_cols):
                            p.alignment = align_cols[col_idx]
                        for r in p.runs:
                            r.font.name = "Times New Roman"
                            r.font.size = Pt(12)

    # =====================================================
    # DOCUMENT CONTENT (MATCHING USER TEMPLATE EXACTLY)
    # =====================================================

    add_h1("CHƯƠNG 2: PHÂN TÍCH YÊU CẦU")

    # 2.1. Khảo sát hiện trạng
    add_h2("2.1. Khảo sát hiện trạng")
    add_p(
        "Hiện nay, quy trình soát vé và kiểm soát khán giả tại các cụm rạp chiếu phim phần lớn vẫn thực hiện theo phương thức bán thủ công truyền thống: khán giả nhận vé in nhiệt tại quầy hoặc xuất trình mã vé điện tử trên điện thoại, sau đó nhân viên kiểm soát tại cửa phòng chiếu kiểm tra bằng mắt thường hoặc dùng thiết bị quét độc lập để cho khách vào phòng. Đối với việc kiểm đếm số lượng khán giả thực tế bên trong phòng chiếu, nhân viên phải trực tiếp đi vào từng rạp (trong điều kiện phòng chiếu tắt đèn tối khi phim đã bắt đầu chiếu) để đếm thủ công và đối chiếu lại với số vé bán ra trên hệ thống POS."
    )
    add_p(
        "Hiện nay, việc kiểm soát vé tại cửa rạp và đối soát số lượng khán giả thực tế trong phòng chiếu còn gặp nhiều khó khăn như:"
    )
    add_bullet(
        " Khán giả sau khi qua cổng soát vé có thể tự ý di chuyển từ ghế thường lên các hàng ghế VIP/Sweetbox đang trống, hoặc cố tình ở lại phòng chiếu sau khi hết phim để xem tiếp các suất chiếu kế tiếp mà không mua vé.",
        bold_prefix="Thất thoát doanh thu và hiện tượng gian lận ('xem phim chui'):"
    )
    add_bullet(
        " Phòng chiếu có diện tích rộng, bố trí bậc thang dốc và ánh sáng rất yếu. Việc nhân viên đi lại đếm người bằng mắt thường gây gián đoạn trải nghiệm thưởng thức bộ phim của khán giả và thường xuyên xảy ra sai số.",
        bold_prefix="Khó khăn khi kiểm đếm thủ công trong môi trường thiếu sáng:"
    )
    add_bullet(
        " Nhân viên rạp phải kiêm nhiệm nhiều công việc cùng lúc (soát vé tại cửa, hướng dẫn vị trí ghế, kiểm tra vệ sinh và cơ sở vật chất). Vào các khung giờ cao điểm hoặc dịp lễ Tết, việc kiểm soát dễ xảy ra sót vé, quét trùng hoặc không phát hiện kịp thời vé sai phòng, sai suất chiếu.",
        bold_prefix="Quá tải áp lực lên nhân sự vận hành hiện trường:"
    )
    add_bullet(
        " Mặc dù các phòng chiếu đều đã lắp đặt camera an ninh (CCTV), nhưng dữ liệu hình ảnh chỉ dừng ở mức ghi hình thụ động để trích xuất lại khi cần, chưa có cơ chế tự động kết nối với cơ sở dữ liệu vé điện tử để phát hiện tức thời các vị trí ghế ngồi bất hợp lệ.",
        bold_prefix="Thiếu sự liên thông dữ liệu thời gian thực giữa camera phòng chiếu và hệ thống vé:"
    )
    add_p(
        "Do đó, việc xây dựng hệ thống CineSight (Hệ thống soát vé và kiểm đếm khán giả rạp chiếu phim ứng dụng thị giác máy tính trên ảnh camera phòng chiếu) là cần thiết nhằm tự động hóa toàn diện quy trình đối soát, nâng cao hiệu suất làm việc của nhân sự và ngăn chặn triệt để thất thoát doanh thu."
    )

    # 2.2. Yêu cầu chức năng
    add_h2("2.2. Yêu cầu chức năng")
    add_p("Các chức năng của hệ thống CineSight được phân tích và liệt kê chi tiết theo từng tác nhân (Actor) như sau:")

    # 2.2.1. Chức năng của Admin
    add_h3("2.2.1. Chức năng của Admin")
    add_bullet(
        " Thêm mới, chỉnh sửa, đặt lại mật khẩu và xóa tài khoản nhân sự (mã nhân viên, họ và tên, tên đăng nhập, mật khẩu, vai trò Quản lý hoặc Soát vé). Hệ thống tự động nhận diện ca làm việc (Dynamic Shift) theo thời điểm đăng nhập thực tế trong ngày: khi nhân sự chưa đăng nhập hiển thị 'Chưa có'; khi đăng nhập tự động xác định ca trực (Nhân viên: Ca sáng 07:30–13:00, Ca chiều 13:00–16:00, Ca tối 16:00–23:00; Quản lý: Ca sáng 07:30–16:00, Ca tối 16:30–24:00). Hỗ trợ theo dõi trạng thái trực tuyến ('Đang trực' / 'Ngoại tuyến'), khóa mềm tài khoản (is_active = 0) để bảo toàn khóa ngoại 3NF và chặn tài khoản nhân viên soát vé đăng nhập vào Web Admin (403 Forbidden).",
        bold_prefix="Quản lý người dùng (CRUD Nhân sự & Ca trực tự động):"
    )
    add_bullet(
        " Quản lý danh mục phim chiếu rạp (tên phim, thời lượng, thể loại, phân loại độ tuổi P/K/T13/T16/T18, poster) đồng bộ từ cơ sở dữ liệu điện ảnh quốc tế TMDB. Quản lý cấu hình 4 phòng chiếu kèm sơ đồ ghế 2D trực quan (Phòng 1, 2, 4 gồm 136 ghế - 12 hàng A..L; Phòng 3 VIP/Sweetbox gồm 132 ghế - 10 hàng A..J). Tạo suất chiếu thủ công hoặc kích hoạt trình lập lịch chiếu tự động chống chồng lấn khung giờ (tự động cộng 15 phút dọn vệ sinh giữa hai suất).",
        bold_prefix="Quản lý danh mục phim TMDB, phòng chiếu và lịch chiếu:"
    )
    add_bullet(
        " Xem bảng điều khiển trung tâm (Dashboard SOC) thống kê theo thời gian thực tổng số vé đã quét, tỷ lệ lấp đầy ghế (Occupancy Rate), số lượng cảnh báo vi phạm chưa xử lý, lịch sử vé đã soát và nhật ký kiểm toán suy luận AI (ai_inference_logs).",
        bold_prefix="Xem báo cáo, thống kê (Dashboard SOC & Nhật ký kiểm toán):"
    )
    add_bullet(
        " Tải ảnh snapshot từ camera CCTV phòng chiếu để kích hoạt phân tích AI theo yêu cầu. Tiếp nhận danh sách cảnh báo vi phạm được gom nhóm theo từng phòng chiếu (hiển thị 3 chỉ số: Vé đã quét, Trong rạp, Ghế vi phạm), xem ảnh bằng chứng khoanh vùng AI và xác nhận xử lý từng ghế hoặc 'Xử lý toàn bộ phòng (1 chạm)'. Tiếp nhận và cập nhật trạng thái khắc phục các sự cố cơ sở vật chất (status: open -> resolved) do nhân viên gửi về.",
        bold_prefix="Giám sát phân tích AI, quản lý cảnh báo theo phòng và xử lý sự cố:"
    )

    # 2.2.2. Chức năng của User
    add_h3("2.2.2. Chức năng của User")
    add_bullet(
        " Đăng nhập vào ứng dụng di động bằng tài khoản được cấp; hệ thống tự động ghi nhận giờ đăng nhập để hiển thị ca làm việc hiện tại (Ca sáng, Ca chiều, Ca tối) mà không cần gán cứng từ trước. Hỗ trợ xem hồ sơ cá nhân và đăng xuất an toàn.",
        bold_prefix="Đăng nhập, tự động nhận diện ca trực và quản lý phiên làm việc:"
    )
    add_bullet(
        " Linh hoạt lựa chọn bất kỳ phòng chiếu và suất chiếu nào đang diễn ra để làm nhiệm vụ. Tra cứu danh sách vé đã quét trong ca và xem trực quan sơ đồ ghế 2D của từng phòng chiếu (136 ghế hoặc 132 ghế) để hướng dẫn chỗ ngồi cho khán giả.",
        bold_prefix="Xem, tìm kiếm phòng chiếu, suất chiếu, lịch sử vé và sơ đồ ghế 2D:"
    )
    add_bullet(
        " Sử dụng camera điện thoại quét mã QR trên vé xem phim; kiểm tra tức thì định dạng vé, đúng phòng chiếu, đúng suất chiếu và chống quét trùng vé (Anti-passback). Tự động lưu trữ vé cục bộ vào Hive Box khi mất mạng (Offline-First) và tự động đồng bộ ngầm lên máy chủ ngay khi có kết nối Internet.",
        bold_prefix="Quét mã QR soát vé và đồng bộ dữ liệu ngoại tuyến (Offline-First):"
    )
    add_bullet(
        " Nhận thông báo chuông/rung khi AI phát hiện ghế có người ngồi nhưng chưa soát vé (B \\ A) và bấm nút 'Xử lý toàn bộ phòng (1 chạm)' ngay trên ứng dụng sau khi kiểm tra thực tế. Tạo báo cáo sự cố cơ sở vật chất (ghế hỏng, thiết bị, vệ sinh) kèm ảnh chụp hiện trường; các sự cố đã xử lý sẽ tự động ẩn sau 1 giờ hoặc cho phép xóa nhanh khỏi danh sách. Thực hiện tổng kết và bàn giao ca trực cuối ca.",
        bold_prefix="Xử lý cảnh báo nhanh 1 chạm, báo cáo sự cố kèm ảnh và bàn giao ca:"
    )

    # 2.2.3. Chức năng của Hệ thống AI / Camera
    add_h3("2.2.3. Chức năng của Hệ thống AI / Camera (System Actor)")
    add_bullet(
        " Tự động kích hoạt thu thập khung hình camera CCTV ở 3 mốc thời gian định kỳ mỗi suất chiếu (Đầu giờ, Giữa giờ, Cuối giờ) hoặc xử lý ngay khi nhận yêu cầu từ Quản trị viên.",
        bold_prefix="Tự động thu thập ảnh theo lịch trình 3 mốc/suất:"
    )
    add_bullet(
        " Thực thi mô hình học sâu YOLOv8n (imgsz=800, conf=0.28, iou=0.45) kết hợp Bộ lọc khử trùng khoảng cách phối cảnh (Perspective Distance Suppression) để nhận diện chính xác đầu người trong điều kiện thiếu sáng.",
        bold_prefix="Nhận diện đầu người bằng mô hình YOLOv8n:"
    )
    add_bullet(
        " Tính toán tọa độ điểm neo phối cảnh tại 78% chiều cao khung bao (y_anchor = y1 + 0.78*(y2 - y1)) nhằm triệt tiêu sai số thị sai giữa các hàng ghế dốc; thực hiện dò đa giác 3 bước (cv2.pointPolygonTest + bù dung sai viền <= 8px) theo ràng buộc vật lý 1–1 trên sơ đồ 136 ghế (Phòng 1, 2, 4) hoặc 132 ghế (Phòng 3).",
        bold_prefix="Chiếu điểm neo phối cảnh 78% và ánh xạ đa giác ghế (Point-in-Polygon):"
    )
    add_bullet(
        " Đối chiếu tập ghế có người ngồi thực tế (B) với tập ghế đã soát vé hợp lệ (A) để xác định khách ngồi không vé / sai ghế (B \\ A), khách vắng mặt (A \\ B) và cảnh báo vượt tải (|B| > |A|); lưu nhật ký kiểm toán ai_inference_logs và phát cảnh báo tức thời.",
        bold_prefix="Đối soát đại số tập hợp và tự động phát cảnh báo:"
    )

    # 2.3. Yêu cầu phi chức năng
    add_h2("2.3. Yêu cầu phi chức năng")
    t1_data = [
        ["Loại yêu cầu", "Mô tả"],
        [
            "Hiệu năng",
            "Thời gian phản hồi toàn trình API phân tích AI (/api/v1/analyze) đạt trung bình < 1.5 giây (nhanh hơn ngưỡng yêu cầu < 3 giây); thời gian suy luận YOLOv8n đạt ~15–25ms trên GPU và < 300ms trên CPU; tốc độ giải mã mã QR cục bộ trên Mobile < 100ms; hỗ trợ 50–100 thiết bị đồng bộ đồng thời."
        ],
        [
            "Bảo mật",
            "Mã hóa mật khẩu một chiều bằng thuật toán PBKDF2-HMAC-SHA256 (100.000 vòng lặp kèm Salt ngẫu nhiên), xác thực phiên bằng chữ ký số HMAC-SHA256 Bearer Token, phân quyền RBAC (Quản lý / Soát vé, chặn Staff vào Web Admin với mã 403 Forbidden), khóa mềm nhân sự (is_active = 0) và chống quay vòng vé (Anti-passback)."
        ],
        [
            "Khả dụng",
            "Uptime đạt 99% nhờ kiến trúc Offline-First trên Mobile App (lưu trữ cô lập trong Hive Box khi mất mạng, tự động đồng bộ khi có mạng) và cơ chế SQLite WAL (Write-Ahead Logging) chống khóa bảng khi đọc/ghi đồng thời; giao diện tương thích chuẩn trên Mobile/Tablet/Desktop."
        ],
        [
            "Độ chính xác",
            "Mô hình YOLOv8n huấn luyện chuyên biệt trên ảnh CCTV phòng chiếu đạt mAP@0.5 > 88% (F1-Score 0.955); thuật toán chiếu điểm neo phối cảnh 78% kết hợp Point-in-Polygon và ràng buộc 1–1 loại bỏ triệt để hiện tượng lệch thị sai giữa các hàng ghế."
        ],
        [
            "Khả năng mở rộng",
            "Kiến trúc module hóa 3 tầng độc lập (FastAPI AI Service, React Vite Web Admin, Flutter Mobile App); dễ dàng mở rộng thêm tính năng mới hoặc thêm phòng chiếu mới chỉ bằng cách nạp tệp cấu hình đa giác ghế JSON (seats_config_roomX.json)."
        ]
    ]
    t1 = doc.add_table(rows=len(t1_data), cols=2)
    for r_idx, r_data in enumerate(t1_data):
        for c_idx, val in enumerate(r_data):
            t1.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(t1, [1.8, 4.8], align_cols=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.JUSTIFY])
    add_p("Bảng 2.1. Yêu cầu phi chức năng", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # 2.4. Product Backlog
    add_h2("2.4. Product Backlog")
    add_p("Danh sách các User Stories của hệ thống CineSight được sắp xếp theo độ ưu tiên (MoSCoW) và phân bổ thực hiện qua các Sprint:")
    t2_data = [
        ["ID", "User Story", "Priority", "Points", "Sprint", "Status"],
        ["US01", "Là người dùng (nhân viên/quản lý), tôi muốn đăng nhập và được hệ thống tự động nhận diện ca trực theo giờ đăng nhập thực tế", "Must", "3", "1", "Done"],
        ["US02", "Là nhân viên, tôi muốn chọn phòng chiếu và suất chiếu linh hoạt để thực hiện soát vé tại cửa rạp", "Must", "2", "1", "Done"],
        ["US03", "Là nhân viên, tôi muốn quét mã QR trên vé để kiểm tra hợp lệ và chống quét trùng vé (Anti-passback)", "Must", "5", "1", "Done"],
        ["US04", "Là nhân viên, tôi muốn ứng dụng lưu vé vào Hive Box khi mất mạng và tự động đồng bộ lên máy chủ khi có mạng", "Must", "5", "1", "Done"],
        ["US05", "Là admin, tôi muốn quản lý người dùng (CRUD nhân sự), theo dõi ca trực động/trạng thái online và khóa mềm tài khoản", "Must", "5", "2", "Done"],
        ["US06", "Là admin, tôi muốn đồng bộ danh mục phim từ TMDB và lập lịch chiếu tự động chống chồng lấn khung giờ", "Must", "5", "2", "Done"],
        ["US07", "Là admin, tôi muốn quản lý 4 phòng chiếu (136 ghế Phòng 1, 2, 4 và 132 ghế Phòng 3) và xem thống kê trên Dashboard SOC", "Must", "3", "2", "Done"],
        ["US08", "Là hệ thống AI, tôi muốn nhận diện đầu người bằng YOLOv8n và chiếu điểm neo 78% vào đa giác ghế theo ràng buộc 1–1", "Must", "8", "3", "Done"],
        ["US09", "Là hệ thống AI, tôi muốn tự động quét định kỳ 3 mốc mỗi suất chiếu và đối soát tập hợp (B \\ A, A \\ B) để sinh cảnh báo", "Must", "8", "3", "Done"],
        ["US10", "Là admin/nhân viên, tôi muốn xem cảnh báo gom nhóm theo phòng chiếu và xử lý nhanh toàn bộ phòng chỉ với 1 chạm", "Must", "5", "4", "Done"],
        ["US11", "Là nhân viên, tôi muốn gửi báo cáo sự cố kèm ảnh chụp thực tế và tự động ẩn/xóa nhanh các sự cố đã xử lý sau 1 giờ", "Should", "3", "4", "Done"],
        ["US12", "Là nhân viên, tôi muốn tổng kết số lượng vé đã soát, số sự cố phát sinh và xác nhận bàn giao ca trực", "Should", "2", "4", "Done"],
    ]
    t2 = doc.add_table(rows=len(t2_data), cols=6)
    for r_idx, r_data in enumerate(t2_data):
        for c_idx, val in enumerate(r_data):
            t2.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(
        t2, [0.65, 3.45, 0.7, 0.6, 0.6, 0.6],
        align_cols=[
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER
        ]
    )
    add_p("Bảng 2.2. Product Backlog (trích)", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # 2.5. Use Case Diagram
    add_h2("2.5. Use Case Diagram")
    add_p(
        "Sơ đồ Use Case tổng quan của hệ thống CineSight mô tả sự tương tác giữa 3 tác nhân chính: Nhân viên soát vé (User / Staff - Mobile App), Quản trị viên (Admin - Web Admin) và Hệ thống AI / Camera (System Actor) với 9 Use Case nghiệp vụ cốt lõi và các Use Case phụ thuộc («include», «extend»):"
    )
    if os.path.exists(DIAGRAM_PATH):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(DIAGRAM_PATH, width=Inches(6.5))
        add_p("Hình 2.1. Use Case Diagram tổng quan hệ thống", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # 2.6. Đặc tả Use Case
    add_h2("2.6. Đặc tả Use Case")
    add_p("Phần dưới đây trình bày đặc tả chi tiết 7 Use Case chính của hệ thống CineSight:")

    def add_usecase_table(heading_text, caption_text, rows_spec):
        add_h3(heading_text)
        tbl = doc.add_table(rows=len(rows_spec), cols=2)
        for r_idx, (attr, content) in enumerate(rows_spec):
            tbl.rows[r_idx].cells[0].paragraphs[0].text = attr
            tbl.rows[r_idx].cells[1].paragraphs[0].text = content

        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row in tbl.rows:
            c0, c1 = row.cells[0], row.cells[1]
            c0.width = Inches(1.65)
            c1.width = Inches(4.95)
            c0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            c1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_borders(c0, color="808080", sz="4")
            set_cell_borders(c1, color="808080", sz="4")
            set_cell_margins(c0, top=85, bottom=85, left=120, right=120)
            set_cell_margins(c1, top=85, bottom=85, left=120, right=120)

            set_cell_background(c0, "F2F4F8")
            p0 = c0.paragraphs[0]
            p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p0.paragraph_format.space_after = Pt(0)
            p0.paragraph_format.line_spacing = 1.15
            for r in p0.runs:
                r.bold = True
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)

            p1 = c1.paragraphs[0]
            p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p1.paragraph_format.space_after = Pt(0)
            p1.paragraph_format.line_spacing = 1.15
            for r in p1.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)

        add_p(caption_text, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # 2.6.1. UC01
    add_usecase_table(
        "2.6.1. Use Case: Đăng nhập",
        "Bảng 2.3. Đặc tả Use Case Đăng nhập",
        [
            ("Tên Use Case", "UC01 - Đăng nhập và nhận diện ca trực tự động"),
            ("Actor", "User (Nhân viên soát vé), Admin (Quản trị viên)"),
            ("Mô tả", "Cho phép người dùng đăng nhập vào hệ thống (Mobile App hoặc Web Admin), kiểm tra phân quyền RBAC và tự động xác định ca làm việc dựa trên thời điểm đăng nhập thực tế."),
            ("Tiền điều kiện", "Người dùng đã có tài khoản hợp lệ trong bảng employees và trạng thái tài khoản đang hoạt động (is_active = 1)."),
            ("Luồng chính", "1. Người dùng nhập username và password trên màn hình đăng nhập.\n2. Hệ thống gửi yêu cầu xác thực tới API POST /api/v1/login (hoặc /api/v1/auth/login).\n3. Máy chủ kiểm tra tài khoản và đối chiếu mật khẩu băm PBKDF2-HMAC-SHA256.\n4. Hệ thống lấy giờ đăng nhập thực tế để tự động nhận diện ca làm việc (Nhân viên: 07:30–13:00 Ca sáng, 13:00–16:00 Ca chiều, 16:00–23:00 Ca tối; Quản lý: 07:30–16:00 Ca sáng, 16:30–24:00 Ca tối).\n5. Máy chủ cập nhật trạng thái trực tuyến (last_seen_at), cấp HMAC-SHA256 Bearer Token và đăng nhập thành công."),
            ("Luồng ngoại lệ", "1a. Để trống tên đăng nhập hoặc mật khẩu → Hiển thị cảnh báo yêu cầu nhập đầy đủ.\n3a. Sai thông tin hoặc tài khoản đã bị khóa mềm (is_active = 0) → Trả về lỗi 401 Unauthorized và hiển thị thông báo lỗi.\n3b. Tài khoản vai trò 'Soát vé' đăng nhập vào cổng Web Admin → Trả về lỗi 403 Forbidden và từ chối truy cập."),
            ("Hậu điều kiện", "Người dùng được chuyển đến trang chủ, trạng thái ca trực trên hệ thống tự động chuyển từ 'Chưa có' sang ca làm việc tương ứng.")
        ]
    )

    # 2.6.2. UC02
    add_usecase_table(
        "2.6.2. Use Case: Quản lý phim và lập lịch chiếu",
        "Bảng 2.4. Đặc tả Use Case Quản lý phim và lập lịch chiếu",
        [
            ("Tên Use Case", "UC02 - Quản lý phim TMDB và lập lịch chiếu tự động"),
            ("Actor", "Admin (Quản trị viên)"),
            ("Mô tả", "Cho phép Quản trị viên đồng bộ danh mục phim thực tế từ TMDB và tạo mới hoặc tự động xếp lịch chiếu chống chồng lấn khung giờ cho 4 phòng chiếu."),
            ("Tiền điều kiện", "Quản trị viên đã đăng nhập vào cổng Web Admin với quyền Quản lý."),
            ("Luồng chính", "1. Quản trị viên truy cập phân hệ Quản lý Phim hoặc Lịch chiếu trên Web Admin.\n2. Quản trị viên thêm phim mới hoặc đồng bộ danh sách phim từ gói dữ liệu TMDB vào bảng movies.\n3. Quản trị viên chọn tạo suất chiếu thủ công (POST /api/v1/showtimes) hoặc kích hoạt trình lập lịch tự động (POST /api/v1/showtimes/generate).\n4. Hệ thống tự động tính khung giờ kết thúc dựa trên thời lượng phim + 15 phút nghỉ dọn vệ sinh và kiểm tra chống trùng phòng/trùng giờ.\n5. Lưu danh sách suất chiếu hợp lệ vào bảng showtimes và cập nhật lên giao diện."),
            ("Luồng ngoại lệ", "4a. Khung giờ suất chiếu mới bị giao cắt với suất chiếu đã tồn tại của cùng phòng chiếu → Hệ thống từ chối và báo lỗi xung đột lịch chiếu."),
            ("Hậu điều kiện", "Danh mục phim và lịch chiếu 4 phòng được cập nhật đồng bộ trên toàn hệ thống.")
        ]
    )

    # 2.6.3. UC03
    add_usecase_table(
        "2.6.3. Use Case: Quét mã QR soát vé",
        "Bảng 2.5. Đặc tả Use Case Quét mã QR soát vé",
        [
            ("Tên Use Case", "UC03 - Quét mã QR soát vé tại cửa phòng chiếu"),
            ("Actor", "User (Nhân viên soát vé)"),
            ("Mô tả", "Nhân viên dùng camera trên ứng dụng di động quét mã QR trên vé của khách, kiểm tra tính hợp lệ và ngăn chặn vé quét trùng (Anti-passback)."),
            ("Tiền điều kiện", "Nhân viên đã đăng nhập Mobile App và chọn Phòng chiếu, Suất chiếu đang mở cửa đón khách."),
            ("Luồng chính", "1. Nhân viên mở màn hình Quét vé (Scanner) và hướng camera vào mã QR trên vé.\n2. Ứng dụng giải mã chuỗi thông tin vé (Mã vé, Phòng chiếu, Suất chiếu, Mã ghế, Hạng ghế).\n3. Ứng dụng kiểm tra đối chiếu đúng Phòng chiếu và đúng Suất chiếu đang chọn.\n4. Ứng dụng kiểm tra trong bộ nhớ cục bộ (Hive Box) và dữ liệu đồng bộ để xác nhận vé chưa từng được quét.\n5. Phát âm thanh xác nhận hợp lệ, hiển thị thông báo xanh 'VÉ HỢP LỆ' kèm số ghế và lưu vé vào Hive Box."),
            ("Luồng ngoại lệ", "2a. Mã QR sai định dạng → Hiển thị lỗi 'Mã vé không hợp lệ'.\n3a. Vé thuộc phòng khác hoặc suất chiếu khác → Báo lỗi đỏ 'SAI PHÒNG CHIẾU / SAI SUẤT CHIẾU'.\n4a. Vé đã từng được quét trước đó (Anti-passback) → Phát còi cảnh báo và hiện thông báo đỏ 'VÉ ĐÃ ĐƯỢC SỬ DỤNG TRƯỚC ĐÓ'."),
            ("Hậu điều kiện", "Vé hợp lệ được ghi nhận trạng thái đã soát (scanned) và chờ đồng bộ lên máy chủ.")
        ]
    )

    # 2.6.4. UC04
    add_usecase_table(
        "2.6.4. Use Case: Đồng bộ vé ngoại tuyến",
        "Bảng 2.6. Đặc tả Use Case Đồng bộ vé ngoại tuyến",
        [
            ("Tên Use Case", "UC04 - Đồng bộ vé đã soát lên máy chủ (Offline-First Sync)"),
            ("Actor", "User (Nhân viên soát vé), Hệ thống Mobile App"),
            ("Mô tả", "Tự động đồng bộ danh sách vé đã quét lưu trong bộ nhớ cục bộ (Hive Box) của thiết bị di động lên cơ sở dữ liệu máy chủ trung tâm."),
            ("Tiền điều kiện", "Có ít nhất một bản ghi vé chưa đồng bộ (isSynced = false) trong Hive Box và thiết bị có kết nối mạng."),
            ("Luồng chính", "1. Ngay sau khi quét vé hoặc khi mạng phục hồi, ứng dụng kích hoạt tiến trình đồng bộ ngầm.\n2. Đóng gói danh sách vé chưa đồng bộ thành mảng JSON.\n3. Gửi yêu cầu tới API POST /api/v1/tickets/sync (hỗ trợ tương thích /api/v1/sync_tickets).\n4. Máy chủ kiểm tra ràng buộc UNIQUE(showtime_id, seat_label) và ghi nhận vào bảng tickets (chế độ SQLite WAL).\n5. Máy chủ trả về mã 200 OK; ứng dụng cập nhật cờ isSynced = true trong Hive Box."),
            ("Luồng ngoại lệ", "3a. Mất kết nối mạng khi đang gửi → Giữ nguyên trạng thái isSynced = false trong Hive Box và tự động thử lại khi có mạng mà không làm gián đoạn việc quét vé."),
            ("Hậu điều kiện", "Danh sách ghế đã soát vé hợp lệ (Tập A) trên máy chủ được cập nhật đầy đủ theo thời gian thực.")
        ]
    )

    # 2.6.5. UC05
    add_usecase_table(
        "2.6.5. Use Case: Phân tích ảnh camera và đối soát ghế AI",
        "Bảng 2.7. Đặc tả Use Case Phân tích ảnh camera và đối soát ghế AI",
        [
            ("Tên Use Case", "UC05 - Phân tích ảnh camera và đối soát ghế AI tự động"),
            ("Actor", "Hệ thống AI / Camera, Admin (Quản trị viên)"),
            ("Mô tả", "Nhận diện đầu người bằng YOLOv8n, chiếu điểm neo phối cảnh 78% vào ma trận đa giác ghế (136 ghế Phòng 1, 2, 4 hoặc 132 ghế Phòng 3) và đối soát tập hợp với dữ liệu vé đã soát."),
            ("Tiền điều kiện", "Phòng chiếu đã có tệp cấu hình đa giác ghế (seats_config_roomX.json) và suất chiếu đang diễn ra."),
            ("Luồng chính", "1. Hệ thống tự động kích hoạt ở 3 mốc thời gian mỗi suất chiếu (Đầu giờ, Giữa giờ, Cuối giờ) hoặc Admin nhấn nút 'Chạy AI' gọi API POST /api/v1/analyze.\n2. Mô hình YOLOv8n nhận diện các khung bao đầu người và lọc khử trùng khoảng cách phối cảnh.\n3. Tính điểm neo phối cảnh tại 78% chiều cao khung bao (y_anchor = y1 + 0.78*(y2 - y1)) và dò đa giác 3 bước (cv2.pointPolygonTest + dung sai <= 8px) theo ràng buộc 1–1 để xác định tập ghế có người ngồi thực tế (Tập B).\n4. Truy vấn bảng tickets lấy tập ghế đã soát vé hợp lệ (Tập A).\n5. Tính toán chênh lệch tập hợp: Ghế ngồi không vé / sai ghế (B \\ A), ghế đã soát vé nhưng trống (A \\ B) và kiểm tra vượt tải (|B| > |A|).\n6. Lưu nhật ký vào bảng ai_inference_logs, sinh cảnh báo vào bảng alerts và trả về ảnh bằng chứng khoanh vùng."),
            ("Luồng ngoại lệ", "1a. Không tìm thấy tệp cấu hình đa giác ghế của phòng → Trả về lỗi 404 Not Found.\n2a. Ảnh camera bị lỗi hoặc tối đen hoàn toàn → Ghi nhận cảnh báo chất lượng luồng camera vào nhật ký."),
            ("Hậu điều kiện", "Kết quả đối soát ghế và các cảnh báo vi phạm được lưu trữ và đồng bộ tới Web Admin / Mobile App.")
        ]
    )

    # 2.6.6. UC06
    add_usecase_table(
        "2.6.6. Use Case: Tiếp nhận và xử lý cảnh báo vi phạm",
        "Bảng 2.8. Đặc tả Use Case Tiếp nhận và xử lý cảnh báo vi phạm",
        [
            ("Tên Use Case", "UC06 - Tiếp nhận và xử lý cảnh báo vi phạm theo phòng"),
            ("Actor", "Admin (Quản trị viên), User (Nhân viên soát vé)"),
            ("Mô tả", "Hiển thị cảnh báo vi phạm gom nhóm theo từng phòng chiếu và cho phép nhân viên/quản lý xác nhận xử lý từng ghế hoặc xử lý toàn bộ phòng chỉ với 1 chạm."),
            ("Tiền điều kiện", "Hệ thống AI đã thực hiện UC05 và phát hiện có ghế vi phạm chưa xử lý (resolved = 0)."),
            ("Luồng chính", "1. Web Admin và Mobile App hiển thị thẻ cảnh báo gom nhóm theo Phòng chiếu kèm 3 chỉ số (Vé đã quét, Trong rạp, Ghế vi phạm).\n2. Nhân viên xem danh sách mã ghế vi phạm cụ thể và ảnh khoanh vùng bằng chứng AI.\n3. Nhân viên trực tiếp vào phòng chiếu kiểm tra, nhắc nhở khách về đúng ghế hoặc yêu cầu mua vé bổ sung.\n4. Nhân viên hoặc Admin nhấn nút 'Xử lý toàn bộ phòng (1 chạm)' (POST /api/v1/alerts/resolve-room) hoặc xử lý từng cảnh báo (PUT /api/v1/alerts/{id}/resolve).\n5. Máy chủ cập nhật resolved = 1 và làm mới trạng thái an ninh của phòng chiếu."),
            ("Luồng ngoại lệ", "4a. Lỗi kết nối mạng khi gửi xác nhận → Hiển thị thông báo lỗi và cho phép bấm thử lại."),
            ("Hậu điều kiện", "Toàn bộ cảnh báo của phòng chiếu chuyển sang trạng thái 'Đã xử lý' trên cả Web Admin và Mobile App.")
        ]
    )

    # 2.6.7. UC07
    add_usecase_table(
        "2.6.7. Use Case: Báo cáo và xử lý sự cố phòng chiếu",
        "Bảng 2.9. Đặc tả Use Case Báo cáo và xử lý sự cố phòng chiếu",
        [
            ("Tên Use Case", "UC07 - Báo cáo và xử lý sự cố cơ sở vật chất"),
            ("Actor", "User (Nhân viên soát vé), Admin (Quản trị viên)"),
            ("Mô tả", "Nhân viên gửi báo cáo hư hỏng cơ sở vật chất kèm ảnh chụp thực tế từ Mobile App; Admin điều phối khắc phục và hệ thống tự động ẩn sự cố đã xử lý sau 1 giờ."),
            ("Tiền điều kiện", "Nhân viên đã đăng nhập ứng dụng di động; Quản trị viên đăng nhập Web Admin."),
            ("Luồng chính", "1. Nhân viên phát hiện sự cố (ghế hỏng, thiết bị, vệ sinh) và mở mục Báo cáo sự cố trên Mobile App.\n2. Chọn phòng chiếu, danh mục (seat_damage, equipment, facility, other), nhập vị trí ghế, mô tả và đính kèm ảnh chụp thực tế.\n3. Gửi yêu cầu tới API POST /api/v1/incidents; máy chủ lưu vào bảng incidents với trạng thái status = 'open' (Đang mở / Chờ xử lý).\n4. Admin xem chi tiết sự cố kèm ảnh trên Web Admin, điều phối khắc phục và bấm xác nhận hoàn tất (PUT /api/v1/incidents/{id}/resolve).\n5. Máy chủ cập nhật status = 'resolved' (Đã khắc phục); trên Mobile App sự cố đã xử lý tự động ẩn sau 1 tiếng hoặc nhân viên bấm xóa/ẩn ngay lập tức."),
            ("Luồng ngoại lệ", "2a. Thiếu thông tin mô tả hoặc phòng chiếu → Ứng dụng nhắc nhở điền đầy đủ các trường bắt buộc.\n3a. Tệp ảnh tải lên không hợp lệ → Hệ thống từ chối và thông báo chỉ hỗ trợ định dạng ảnh chuẩn (JPG/PNG)."),
            ("Hậu điều kiện", "Sự cố cơ sở vật chất được ghi nhận kèm hình ảnh minh chứng và theo dõi trọn vẹn đến khi khắc phục xong.")
        ]
    )

    doc.save(OUTPUT_DOCX)
    print("DOCX created successfully at:", OUTPUT_DOCX)


if __name__ == "__main__":
    build_docx()
