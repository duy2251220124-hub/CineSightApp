# -*- coding: utf-8 -*-
"""
Script to generate the formal university thesis Chapter 2 in DOCX format:
CHƯƠNG 2: PHÂN TÍCH YÊU CẦU - DỰ ÁN CINESIGHT
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
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
    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 115)
    ax.axis('off')

    # Background system boundary
    sys_rect = patches.FancyBboxPatch(
        (34, 4), 74, 107,
        boxstyle="round,pad=1.5",
        edgecolor="#1E3A8A",
        facecolor="#F8FAFC",
        linewidth=2.5,
        linestyle='-'
    )
    ax.add_patch(sys_rect)
    ax.text(71, 107.5, "HỆ THỐNG CINESIGHT", fontsize=15, fontweight="bold", ha="center", va="center", color="#1E3A8A")

    # Helper function to draw stick figure actor
    def draw_actor(x, y, label, color="#0F172A"):
        # Head
        ax.add_patch(patches.Circle((x, y + 5), 2.2, edgecolor=color, facecolor="#FFFFFF", lw=2.2))
        # Body
        ax.plot([x, x], [y + 2.8, y - 4], color=color, lw=2.5)
        # Arms
        ax.plot([x - 4, x + 4], [y + 0.5, y + 0.5], color=color, lw=2.5)
        # Legs
        ax.plot([x, x - 3.5], [y - 4, y - 10], color=color, lw=2.5)
        ax.plot([x, x + 3.5], [y - 4, y - 10], color=color, lw=2.5)
        # Label
        ax.text(x, y - 13.5, label, fontsize=10.5, fontweight="bold", ha="center", va="top", color=color)

    # Helper to draw use case ellipse
    def draw_usecase(x, y, text, w=22, h=5.8, bg="#EFF6FF", border="#2563EB", lw=1.5, ls='-'):
        ellipse = patches.Ellipse((x, y), w, h, edgecolor=border, facecolor=bg, linewidth=lw, linestyle=ls)
        ax.add_patch(ellipse)
        ax.text(x, y, text, fontsize=9.2, ha="center", va="center", color="#0F172A", weight="bold" if border=="#2563EB" else "normal")

    # Draw Actors
    draw_actor(14, 88, "Nhân viên soát vé\n(Staff - Mobile)", color="#047857")
    draw_actor(14, 30, "Quản trị viên\n(Admin - Web)", color="#1E3A8A")
    draw_actor(126, 58, "Hệ thống AI / Camera\n(System Actor)", color="#B45309")

    # Main Core Use Cases (Center column)
    usecases = {
        "uc01": (53, 98, "UC01: Đăng nhập\nhệ thống"),
        "uc02": (53, 85, "UC02: Quét mã QR\nsoát vé"),
        "uc03": (53, 72, "UC03: Đồng bộ vé\n(Offline / Online)"),
        "uc04": (53, 56, "UC04: Phân tích ảnh\n& đối soát ghế AI"),
        "uc05": (53, 40, "UC05: Tiếp nhận &\nxử lý cảnh báo"),
        "uc06": (53, 26, "UC06: Báo cáo &\nxử lý sự cố rạp"),
        "uc_handover": (53, 13, "Bàn giao ca trực"),
        
        # Included / Sub Use Cases (Right inside system boundary)
        "inc_check": (92, 85, "<<include>>\nKiểm tra hợp lệ &\nChống quét trùng"),
        "inc_yolo": (92, 67, "<<include>>\nNhận diện đầu người\nYOLOv8n"),
        "inc_map": (92, 54, "<<include>>\nÁnh xạ đa giác ghế\nPoint-in-Polygon"),
        "inc_diff": (92, 41, "<<include>>\nĐối soát logic tập hợp\n(B trừ A)"),

        # Admin extra features
        "adm_dash": (53, 6, "Xem Dashboard SOC\n& Thống kê"),
    }

    # Draw regular usecases
    for k, (ux, uy, utext) in usecases.items():
        if k.startswith("inc_"):
            draw_usecase(ux, uy, utext, w=22, h=6.5, bg="#FEF3C7", border="#D97706", lw=1.3, ls='--')
        else:
            draw_usecase(ux, uy, utext, w=23, h=6.5, bg="#EFF6FF", border="#2563EB", lw=1.6)

    # Connect lines from Staff
    staff_pt = (17, 85)
    for target in ["uc01", "uc02", "uc03", "uc05", "uc06", "uc_handover"]:
        tx, ty, _ = usecases[target]
        ax.annotate("", xy=(tx - 11.5, ty), xytext=staff_pt,
                    arrowprops=dict(arrowstyle="->", color="#047857", lw=1.4))

    # Connect lines from Admin
    admin_pt = (17, 30)
    for target in ["uc01", "uc04", "uc05", "uc06", "adm_dash"]:
        tx, ty, _ = usecases[target]
        ax.annotate("", xy=(tx - 11.5, ty), xytext=admin_pt,
                    arrowprops=dict(arrowstyle="->", color="#1E3A8A", lw=1.4))

    # Connect lines from AI System
    ai_pt = (123, 58)
    for target in ["uc04", "uc05"]:
        tx, ty, _ = usecases[target]
        ax.annotate("", xy=(tx + 11.5, ty), xytext=ai_pt,
                    arrowprops=dict(arrowstyle="->", color="#B45309", lw=1.5))

    # Connect include arrows (dashed)
    def connect_include(src_k, dst_k):
        sx, sy, _ = usecases[src_k]
        dx, dy, _ = usecases[dst_k]
        ax.annotate("", xy=(dx - 11, dy), xytext=(sx + 11.5, sy),
                    arrowprops=dict(arrowstyle="->", color="#475569", lw=1.3, ls="--"))

    connect_include("uc02", "inc_check")
    connect_include("uc04", "inc_yolo")
    connect_include("uc04", "inc_map")
    connect_include("uc04", "inc_diff")

    plt.tight_layout()
    plt.savefig(DIAGRAM_PATH, bbox_inches='tight')
    plt.close()
    print("Generated diagram successfully at:", DIAGRAM_PATH)

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_borders(cell, color="A6A6A6", sz="4"):
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

    # Configure Margins: Top 2cm, Bottom 2cm, Left 3cm, Right 2cm
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.79)      # 2.0 cm
        section.bottom_margin = Inches(0.79)   # 2.0 cm
        section.left_margin = Inches(1.18)     # 3.0 cm
        section.right_margin = Inches(0.79)    # 2.0 cm

    # Default Style Font
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_after = Pt(4)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def add_p(text, bold_prefix="", italic_prefix="", bold=False, italic=False, space_after=4, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.3
        if bold_prefix:
            r = p.add_run(bold_prefix)
            r.bold = True
            r.font.name = 'Times New Roman'
        if italic_prefix:
            r = p.add_run(italic_prefix)
            r.italic = True
            r.font.name = 'Times New Roman'
        r2 = p.add_run(text)
        r2.bold = bold
        r2.italic = italic
        r2.font.name = 'Times New Roman'
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(12)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(16)
        r.font.name = 'Times New Roman'
        r.font.color.rgb = RGBColor(15, 23, 42)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(14)
        r.font.name = 'Times New Roman'
        r.font.color.rgb = RGBColor(30, 58, 138)
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(13)
        r.font.name = 'Times New Roman'
        r.font.color.rgb = RGBColor(15, 23, 42)
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.25
        if bold_prefix:
            r = p.add_run(bold_prefix)
            r.bold = True
            r.font.name = 'Times New Roman'
        r2 = p.add_run(text)
        r2.font.name = 'Times New Roman'
        return p

    def format_table(table, col_widths, align_cols=None):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row_idx, row in enumerate(table.rows):
            is_header = (row_idx == 0)
            for col_idx, cell in enumerate(row.cells):
                cell.width = Inches(col_widths[col_idx])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_borders(cell, color="B0B0B0", sz="4")
                set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
                
                if is_header:
                    set_cell_background(cell, "DCE6F1")
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

    # ==========================
    # 2. DOCUMENT BODY
    # ==========================

    add_h1("CHƯƠNG 2: PHÂN TÍCH YÊU CẦU")

    add_h2("2.1. Khảo sát hiện trạng")
    add_p("Hiện nay, quy trình soát vé và kiểm soát khán giả tại các cụm rạp chiếu phim phần lớn vẫn thực hiện theo phương thức bán thủ công truyền thống: khán giả nhận vé in nhiệt tại quầy hoặc xuất trình mã vé điện tử trên điện thoại, sau đó nhân viên kiểm soát tại cửa phòng chiếu sẽ kiểm tra bằng mắt thường hoặc dùng máy quét mã vạch độc lập để cho khách vào phòng. Đối với việc kiểm đếm số lượng khán giả thực tế bên trong phòng chiếu, nhân viên phải trực tiếp đi vào từng rạp (thường trong điều kiện phòng chiếu tối, phim đã bắt đầu chiếu) để đếm thủ công, sau đó ghi chép và đối chiếu lại với số vé bán ra trên hệ thống quản lý rạp (POS).")
    
    add_p("Quy trình quản lý thủ công này bộc lộ nhiều khó khăn và rủi ro nghiêm trọng:")
    add_bullet(" Khán giả sau khi vào rạp có thể tự ý di chuyển từ các vị trí ghế thường lên các vị trí ghế VIP trống, hoặc cố tình ở lại phòng chiếu sau khi kết thúc suất chiếu để xem tiếp các suất chiếu sau mà không mua vé.", bold_prefix="1. Thất thoát doanh thu và hiện tượng gian lận ('xem phim chui'):")
    add_bullet(" Phòng chiếu phim có diện tích rộng, bố trí dạng bậc thang dốc và ánh sáng tắt tối khi phim bắt đầu chiếu. Việc nhân viên đi lại đếm từng người gây bất tiện, làm gián đoạn trải nghiệm của khán giả khác và tỷ lệ sai sót số lượng là rất cao.", bold_prefix="2. Khó khăn trong việc kiểm đếm trong điều kiện thiếu sáng:")
    add_bullet(" Một nhân viên tại cụm rạp thường phải kiêm nhiệm nhiều đầu việc cùng lúc (soát vé tại cửa rạp, hướng dẫn chỗ ngồi, kiểm tra vệ sinh, giám sát an ninh phòng chiếu). Khi lượng khách đông vào các khung giờ cao điểm hoặc dịp lễ Tết, việc kiểm soát vé tại cửa dễ xảy ra tình trạng sót vé, quét trùng hoặc không kịp phát hiện vé sai suất/sai phòng.", bold_prefix="3. Quá tải áp lực lên nhân viên vận hành:")
    add_bullet(" Các cụm rạp hiện nay đều đã trang bị hệ thống camera an ninh (CCTV) trong phòng chiếu, tuy nhiên camera chỉ đóng vai trò ghi hình thụ động (lưu trữ video để xem lại khi có sự cố). Chưa có cơ chế tự động hóa kết nối giữa luồng hình ảnh camera với cơ sở dữ liệu vé đã soát để phát hiện ngay lập tức các trường hợp bất thường.", bold_prefix="4. Thiếu sự liên thông dữ liệu thời gian thực giữa camera và hệ thống vé:")

    add_p("Do đó, việc nghiên cứu và xây dựng hệ thống \"CineSight - Hệ thống soát vé và kiểm đếm khán giả rạp chiếu phim ứng dụng thị giác máy tính trên ảnh camera phòng chiếu\" là hoàn toàn cấp thiết, nhằm tự động hóa toàn diện khâu đối soát, tối ưu hóa năng suất vận hành của nhân viên và ngăn chặn triệt để thất thoát doanh thu cho rạp.")

    # --------------------------
    add_h2("2.2. Yêu cầu chức năng")
    add_p("Dựa trên kiến trúc và phạm vi thực tế của hệ thống CineSight, các yêu cầu chức năng được phân rã chi tiết theo từng tác nhân (Actor) tham gia vào hệ thống như sau:")

    add_h3("2.2.1. Chức năng của Quản trị viên (Admin - Web Admin)")
    add_bullet(" Thêm mới tài khoản nhân viên soát vé (họ và tên, tên đăng nhập, mật khẩu, số điện thoại, vai trò). Phân công ca làm việc (Ca sáng, Ca chiều, Ca tối) và gán phòng chiếu phụ trách. Chỉnh sửa thông tin, cập nhật ca trực hoặc xóa tài khoản nhân viên.", bold_prefix="Quản lý người dùng (CRUD Nhân viên):")
    add_bullet(" Xem danh sách toàn bộ các phòng chiếu trong cụm rạp kèm theo các thông số cấu hình: tổng số ghế, số hàng, số cột, trạng thái sẵn sàng. Xem sơ đồ ghế 2D trực quan tương ứng với ma trận cấu hình của từng phòng chiếu.", bold_prefix="Quản lý phòng chiếu (Rooms):")
    add_bullet(" Xem danh mục lịch chiếu phim theo từng ngày và theo từng phòng chiếu. Tạo mới suất chiếu: chọn phim, chọn phòng chiếu, thiết lập thời gian bắt đầu và thời gian kết thúc.", bold_prefix="Quản lý suất chiếu (Showtimes):")
    add_bullet(" Tra cứu và xem danh sách toàn bộ các vé đã được soát hợp lệ tại cổng theo từng phòng chiếu và suất chiếu cụ thể (mã vé, số ghế, loại ghế, thời điểm soát, nhân viên thực hiện).", bold_prefix="Quản lý danh sách vé (Tickets):")
    add_bullet(" Tải ảnh chụp khung hình (snapshot) từ camera CCTV phòng chiếu lên hệ thống. Kích hoạt tiến trình AI phân tích tự động: chạy mô hình nhận diện đầu người, ánh xạ tọa độ vào sơ đồ ghế và thực hiện đối soát tự động với danh sách vé đã quét.", bold_prefix="Giám sát và kích hoạt phân tích AI:")
    add_bullet(" Theo dõi các chỉ số vận hành tổng quan theo thời gian thực: tổng số vé đã quét trong ngày, tỷ lệ lấp đầy ghế (Occupancy Rate), tổng số cảnh báo vi phạm an ninh chưa xử lý. Quan sát trạng thái hoạt động tức thời của các phòng chiếu.", bold_prefix="Xem báo cáo, thống kê (Dashboard SOC):")
    add_bullet(" Tiếp nhận danh sách các cảnh báo chênh lệch vé do AI tự động gửi về, phân loại theo các nhóm: Khách lậu / Ngồi sai ghế không vé (B \\ A), Khách vắng mặt (A \\ B), và Cảnh báo vượt tải phòng chiếu (Over-capacity). Xem chi tiết danh sách mã ghế vi phạm kèm ảnh bằng chứng phân tích. Thực hiện thao tác \"Đánh dấu đã xử lý\" sau khi nhân viên rạp đã xử lý xong tại hiện trường.", bold_prefix="Quản lý cảnh báo vi phạm (Alerts):")
    add_bullet(" Tiếp nhận các báo cáo sự cố cơ sở vật chất (ghế hỏng/gãy, lỗi điều hòa, rác bẩn) do nhân viên gửi từ ứng dụng di động. Cập nhật trạng thái xử lý sự cố (Đang chờ xử lý → Đã khắc phục).", bold_prefix="Quản lý sự cố rạp chiếu (Incidents):")

    add_h3("2.2.2. Chức năng của Nhân viên soát vé (User / Staff - Mobile App)")
    add_bullet(" Đăng nhập vào ứng dụng bằng tài khoản nhân viên (username/password) đã được cấp. Xem thông tin ca trực hiện tại và danh sách phòng chiếu được phân công phụ trách.", bold_prefix="Đăng nhập và quản lý phiên làm việc:")
    add_bullet(" Lựa chọn phòng chiếu và suất chiếu sắp diễn ra để chuẩn bị quy trình mở cửa đón khách và soát vé.", bold_prefix="Lựa chọn phòng chiếu và suất chiếu:")
    add_bullet(" Kích hoạt camera điện thoại để quét mã vạch / mã QR trên vé của khán giả. Kiểm tra tính hợp lệ tức thì: kiểm tra định dạng vé, đối chiếu đúng phòng chiếu, đúng suất chiếu. Thực hiện cơ chế chống quét trùng vé (Anti-passback): từ chối các mã vé đã được quét trước đó để ngăn chặn hành vi một vé sử dụng cho nhiều người.", bold_prefix="Quét mã QR soát vé (Scanner):")
    add_bullet(" Tự động lưu trữ cục bộ toàn bộ dữ liệu vé đã quét vào cơ sở dữ liệu nội bộ trên thiết bị (Hive Box), đảm bảo ứng dụng hoạt động thông suốt ngay cả khi rạp bị mất kết nối mạng. Tự động đồng bộ (Auto-sync) toàn bộ danh sách vé hợp lệ lên máy chủ trung tâm ngay khi thiết bị có kết nối mạng Internet.", bold_prefix="Lưu trữ ngoại tuyến và đồng bộ dữ liệu (Offline-First):")
    add_bullet(" Xem danh sách chi tiết các vé đã quét thành công trong ca trực (mã vé, số ghế, giờ quét).", bold_prefix="Xem lịch sử soát vé:")
    add_bullet(" Xem trực quan sơ đồ ghế 2D của phòng chiếu để hỗ trợ hướng dẫn vị trí ngồi cho khán giả.", bold_prefix="Xem sơ đồ ghế phòng chiếu:")
    add_bullet(" Nhận thông báo chuông/rung và xem chi tiết cảnh báo từ hệ thống AI khi phát hiện có người ngồi ghế không hợp lệ tại phòng chiếu mình đang phụ trách.", bold_prefix="Tiếp nhận thông báo và cảnh báo an ninh:")
    add_bullet(" Tạo phiếu báo cáo sự cố cơ sở vật chất (chọn loại sự cố, nhập vị trí ghế hỏng, mô tả chi tiết) để chuyển về cho Quản trị viên xử lý.", bold_prefix="Báo cáo sự cố phòng chiếu:")
    add_bullet(" Thực hiện thao tác tổng kết số lượng vé đã soát, số lượng sự cố phát sinh và bàn giao ca làm việc cho nhân viên ca tiếp theo.", bold_prefix="Bàn giao ca trực (Shift Handover):")

    add_h3("2.2.3. Chức năng của Hệ thống AI / Camera (System Actor)")
    add_bullet(" Tiếp nhận ảnh chụp snapshot độ phân giải cao (Full HD 1920x1080) từ camera an ninh góc cao (High-Angle CCTV) của phòng chiếu.", bold_prefix="Tiếp nhận dữ liệu hình ảnh:")
    add_bullet(" Ứng dụng mô hình mạng nơ-ron tích chập YOLOv8n chuyên biệt để phát hiện chính xác vị trí tâm đầu người của toàn bộ khán giả trong điều kiện phòng chiếu tối/ánh sáng hồng ngoại.", bold_prefix="Nhận diện đầu người (Head Detection):")
    add_bullet(" Áp dụng thuật toán hình học tính toán (Ray Casting) để kiểm tra điểm tâm đầu người (x, y) nằm bên trong vùng đa giác tọa độ của 136 vị trí ghế đã được hiệu chuẩn (Calibration Matrix).", bold_prefix="Ánh xạ tọa độ ghế (Point-in-Polygon):")
    add_bullet(" Xác định tập hợp ghế có người ngồi thực tế (B); Truy vấn tập hợp các vé đã được nhân viên soát hợp lệ tại cổng (A); Tính toán chênh lệch: Ghế có người ngồi chui không có vé (B \\ A), Ghế đã soát vé nhưng thực tế để trống (A \\ B), Cảnh báo vượt công suất tối đa của phòng chiếu.", bold_prefix="Tự động đối soát logic tập hợp (Set Difference):")
    add_bullet(" Tự động tạo bản ghi cảnh báo vi phạm lưu vào cơ sở dữ liệu máy chủ và phát thông báo tức thời tới Web Admin và Mobile App.", bold_prefix="Tự động sinh và lưu trữ cảnh báo:")

    # --------------------------
    add_h2("2.3. Yêu cầu phi chức năng")
    add_p("Các yêu cầu phi chức năng nhằm bảo đảm tính tin cậy, an toàn, hiệu năng và khả năng mở rộng của hệ thống được quy định chi tiết trong Bảng 2.1:")

    # Table 2.1
    t1_data = [
        ["Loại yêu cầu", "Mô tả chi tiết"],
        ["Hiệu năng\n(Performance)", "- Thời gian thực thi mô hình AI (Inference time) của YOLOv8n trên ảnh Full HD (1920x1080) đạt ~15-25ms trên GPU và < 300ms trên CPU.\n- Thời gian xử lý API toàn trình /api/v1/analyze (từ khi nhận ảnh, chạy AI, ánh xạ đa giác 136 ghế, đối soát DB và lưu cảnh báo) đạt trung bình < 1.5 giây.\n- Tốc độ giải mã và phản hồi quét vé QR trên ứng dụng Mobile đạt < 100ms (kiểm tra cục bộ tức thì).\n- Hệ thống máy chủ đáp ứng xử lý đồng thời 50-100 phiên đồng bộ vé từ các thiết bị di động mà không gây nghẽn hàng đợi."],
        ["Bảo mật\n(Security)", "- Cơ sở dữ liệu SQLite quản lý tập trung với ràng buộc toàn vẹn khóa chính và khóa ngoại nghiêm ngặt giữa các bảng: nhân viên, phòng chiếu, suất chiếu, vé, cảnh báo và sự cố.\n- Áp dụng cơ chế chống gian lận soát vé (Anti-passback): mỗi mã vé là duy nhất cho từng suất chiếu và bị khóa ngay sau lần quét thành công đầu tiên.\n- Dữ liệu vé lưu tạm trên thiết bị di động được lưu trữ an toàn trong các hộp dữ liệu cô lập của Hive Box."],
        ["Khả dụng\n(Availability &\nOffline-First)", "- Tính khả dụng cao với kiến trúc Offline-First: Ứng dụng di động tiếp tục cho phép nhân viên quét vé và kiểm tra vé bình thường ngay cả khi mất sóng Wi-Fi/4G; dữ liệu sẽ tự động đẩy lên máy chủ ngay khi có mạng trở lại.\n- Giao diện Web Admin tương thích chuẩn trên các trình duyệt máy tính phòng điều hành; ứng dụng di động hiển thị trực quan, mượt mà trên hệ điều hành Android."],
        ["Độ chính xác\n(Accuracy)", "- Mô hình YOLOv8n nhận diện đầu người đạt độ chính xác phát hiện mAP@0.5 đạt trên 85% trong môi trường ánh sáng thực tế của phòng chiếu phim.\n- Thuật toán ánh xạ điểm trong đa giác (Ray Casting Point-in-Polygon) đảm bảo độ chính xác tuyệt đối (100%) về mặt toán học khi xác định tọa độ tâm rơi vào biên ghế."],
        ["Khả năng mở rộng\n(Scalability)", "- Kiến trúc hệ thống phân tách độc lập giữa Tầng trí tuệ nhân tạo (FastAPI AI Service), Tầng điều hành quản trị (React Vite Web Admin), và Tầng nghiệp vụ hiện trường (Flutter Mobile App).\n- Dễ dàng mở rộng cấu hình sơ đồ ghế cho các phòng chiếu mới (Phòng 1, Phòng 2, Phòng 3...) thông qua việc nạp tệp tọa độ đa giác JSON độc lập mà không cần thay đổi logic mã nguồn cốt lõi."]
    ]
    t1 = doc.add_table(rows=len(t1_data), cols=2)
    for r_idx, r_data in enumerate(t1_data):
        for c_idx, val in enumerate(r_data):
            t1.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(t1, [2.0, 4.6], align_cols=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.JUSTIFY])

    add_p("Bảng 2.1. Yêu cầu phi chức năng của hệ thống CineSight", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    # --------------------------
    add_h2("2.4. Product Backlog")
    add_p("Danh sách các hạng mục yêu cầu (User Stories) của hệ thống CineSight được tổng hợp, phân loại theo mức độ ưu tiên (MoSCoW) và quản lý theo tiến độ các Sprint:")

    t2_data = [
        ["ID", "User Story", "Priority", "Points", "Sprint", "Status"],
        ["US01", "Là Nhân viên, tôi muốn đăng nhập vào ứng dụng mobile bằng tài khoản được cấp để xác định danh tính và ca làm việc.", "Must", "3", "Sprint 1", "Done"],
        ["US02", "Là Nhân viên, tôi muốn chọn phòng chiếu và suất chiếu hiện tại để bắt đầu quy trình soát vé tại cửa phòng.", "Must", "2", "Sprint 1", "Done"],
        ["US03", "Là Nhân viên, tôi muốn quét mã QR trên vé để kiểm tra tính hợp lệ (đúng phòng, đúng suất chiếu, chưa bị quét trùng).", "Must", "5", "Sprint 1", "Done"],
        ["US04", "Là Nhân viên, tôi muốn ứng dụng tự động lưu trữ vé vào bộ nhớ nội bộ (Hive) khi mất mạng và tự động đồng bộ lên máy chủ khi có kết nối trở lại.", "Must", "5", "Sprint 2", "Done"],
        ["US05", "Là Quản trị viên, tôi muốn xem bảng điều khiển (Dashboard) thống kê tổng quan số vé đã soát, tỷ lệ lấp đầy ghế và số lượng cảnh báo vi phạm.", "Must", "3", "Sprint 2", "Done"],
        ["US06", "Là Quản trị viên, tôi muốn quản lý thông tin các phòng chiếu, xem sơ đồ ghế 2D và quản lý lịch các suất chiếu.", "Must", "5", "Sprint 2", "Done"],
        ["US07", "Là Quản trị viên, tôi muốn quản lý thông tin nhân viên soát vé (CRUD) và phân chia ca trực, phòng phụ trách.", "Must", "3", "Sprint 2", "Done"],
        ["US08", "Là Quản trị viên, tôi muốn tải ảnh camera phòng chiếu và bấm nút \"Chạy AI\" để kích hoạt phân tích đối soát trực tiếp từ Web Admin.", "Must", "5", "Sprint 3", "Done"],
        ["US09", "Là Hệ thống AI, tôi muốn nhận diện vị trí đầu người trong phòng chiếu bằng mô hình YOLOv8n trên ảnh snapshot camera.", "Must", "8", "Sprint 3", "Done"],
        ["US10", "Là Hệ thống AI, tôi muốn ánh xạ tọa độ đầu người vào ma trận đa giác ghế và tự động đối soát logic tập hợp với danh sách vé đã quét để phát hiện khách lậu, vắng khách.", "Must", "8", "Sprint 3", "Done"],
        ["US11", "Là Quản trị viên, tôi muốn xem danh sách cảnh báo vi phạm chi tiết trên Web Admin và đánh dấu xác nhận đã xử lý.", "Must", "3", "Sprint 4", "Done"],
        ["US12", "Là Nhân viên, tôi muốn nhận thông báo cảnh báo tức thời trên điện thoại khi phát hiện có khách ngồi sai ghế/ngồi không vé tại phòng chiếu mình phụ trách.", "Must", "3", "Sprint 4", "Done"],
        ["US13", "Là Nhân viên, tôi muốn gửi báo cáo sự cố cơ sở vật chất (ghế hỏng, điều hòa, vệ sinh) kèm vị trí cụ thể lên hệ thống.", "Should", "3", "Sprint 4", "Done"],
        ["US14", "Là Quản trị viên, tôi muốn theo dõi danh sách và cập nhật trạng thái khắc phục các sự cố rạp do nhân viên báo cáo.", "Should", "2", "Sprint 4", "Done"],
        ["US15", "Là Nhân viên, tôi muốn thực hiện thao tác bàn giao ca làm việc để tổng kết số lượng vé và sự cố cho ca tiếp theo.", "Should", "2", "Sprint 4", "Done"]
    ]
    t2 = doc.add_table(rows=len(t2_data), cols=6)
    for r_idx, r_data in enumerate(t2_data):
        for c_idx, val in enumerate(r_data):
            t2.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(t2, [0.7, 3.2, 0.7, 0.6, 0.8, 0.6], 
                 align_cols=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER])

    add_p("Bảng 2.2. Product Backlog hệ thống CineSight", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    # --------------------------
    add_h2("2.5. Use Case Diagram")
    add_p("Hệ thống bao gồm 3 tác nhân (Actor) chính tham gia vào quy trình vận hành:")
    add_bullet(" Tương tác thông qua ứng dụng Web Admin để quản trị hệ thống, giám sát vận hành rạp và xử lý các sự cố.", bold_prefix="1. Quản trị viên (Admin):")
    add_bullet(" Tương tác thông qua ứng dụng di động Flutter để thực hiện kiểm soát vé tại cửa phòng chiếu và nhận cảnh báo tức thời.", bold_prefix="2. Nhân viên soát vé (Staff / User):")
    add_bullet(" Đóng vai trò tác nhân hệ thống tự động, thực hiện phân tích thị giác máy tính và thuật toán đối soát hình học trên máy chủ backend.", bold_prefix="3. Hệ thống AI / Camera (System Actor):")

    add_p("Sơ đồ Use Case tổng quan của toàn bộ hệ thống CineSight được mô tả trực quan trong Hình 2.1 dưới đây:")

    # Add Figure 2.1 image
    if os.path.exists(DIAGRAM_PATH):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(DIAGRAM_PATH, width=Inches(6.4))
        add_p("Hình 2.1. Use Case Diagram tổng quan hệ thống CineSight", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    # --------------------------
    add_h2("2.6. Đặc tả Use Case")
    add_p("Phần này trình bày chi tiết đặc tả của 6 Use Case cốt lõi nhất cấu thành quy trình nghiệp vụ kiểm soát và đối soát của hệ thống CineSight theo chuẩn mẫu cấu trúc học thuật.")

    def add_usecase_table(title, rows_spec):
        add_h3(title)
        tbl = doc.add_table(rows=len(rows_spec), cols=2)
        for r_idx, (attr, content) in enumerate(rows_spec):
            c0 = tbl.rows[r_idx].cells[0]
            c1 = tbl.rows[r_idx].cells[1]
            c0.paragraphs[0].text = attr
            c1.paragraphs[0].text = content
        
        # Format table
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r_idx, row in enumerate(tbl.rows):
            cell0 = row.cells[0]
            cell1 = row.cells[1]
            cell0.width = Inches(1.8)
            cell1.width = Inches(4.8)
            cell0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            cell1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_borders(cell0, color="B0B0B0", sz="4")
            set_cell_borders(cell1, color="B0B0B0", sz="4")
            set_cell_margins(cell0, top=90, bottom=90, left=130, right=130)
            set_cell_margins(cell1, top=90, bottom=90, left=130, right=130)

            # Left column formatting (Header-like attribute)
            set_cell_background(cell0, "F1F5F9")
            p0 = cell0.paragraphs[0]
            p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p0.paragraph_format.space_after = Pt(0)
            p0.paragraph_format.line_spacing = 1.15
            for r in p0.runs:
                r.bold = True
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)

            # Right column formatting
            p1 = cell1.paragraphs[0]
            p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p1.paragraph_format.space_after = Pt(0)
            p1.paragraph_format.line_spacing = 1.15
            for r in p1.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)

    # UC01
    add_usecase_table("2.6.1. Use Case UC01: Đăng nhập hệ thống", [
        ("Tên Use Case", "UC01 - Đăng nhập hệ thống"),
        ("Actor", "Nhân viên soát vé (Mobile App), Quản trị viên (Web Admin)"),
        ("Mô tả", "Xác thực danh tính của người dùng để cấp quyền truy cập vào các chức năng tương ứng của hệ thống."),
        ("Tiền điều kiện", "Người dùng đã được cấp tài khoản hợp lệ trong cơ sở dữ liệu hệ thống."),
        ("Luồng sự kiện chính", "1. Người dùng mở ứng dụng và nhập Tên đăng nhập (username) và Mật khẩu (password).\n2. Người dùng nhấn nút \"Đăng nhập\".\n3. Ứng dụng gửi yêu cầu xác thực đến máy chủ qua API POST /api/v1/login.\n4. Máy chủ kiểm tra thông tin trong bảng employees.\n5. Máy chủ xác thực thành công và trả về thông tin nhân viên, vai trò (role), ca làm việc (shift) và phòng phụ trách.\n6. Ứng dụng lưu phiên làm việc và chuyển hướng người dùng đến màn hình chính (Dashboard/Home)."),
        ("Luồng ngoại lệ", "3a. Thiếu thông tin đầu vào: Người dùng để trống tên đăng nhập hoặc mật khẩu → Ứng dụng hiển thị cảnh báo \"Vui lòng nhập đầy đủ thông tin\".\n4a. Sai tài khoản hoặc mật khẩu: Máy chủ kiểm tra không khớp → Trả về mã lỗi 401 Unauthorized → Ứng dụng hiển thị thông báo \"Tài khoản hoặc mật khẩu không chính xác\".\n4b. Mất kết nối máy chủ: Không thể kết nối tới backend → Ứng dụng hiển thị thông báo \"Lỗi kết nối máy chủ, vui lòng kiểm tra mạng\"."),
        ("Hậu điều kiện", "Người dùng đăng nhập thành công và truy cập đúng phân quyền của mình.")
    ])
    add_p("Bảng 2.3. Đặc tả Use Case Đăng nhập hệ thống", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # UC02
    add_usecase_table("2.6.2. Use Case UC02: Quét mã QR soát vé", [
        ("Tên Use Case", "UC02 - Quét mã QR soát vé"),
        ("Actor", "Nhân viên soát vé"),
        ("Mô tả", "Nhân viên sử dụng camera trên ứng dụng di động để quét mã QR vé xem phim của khách tại cửa phòng chiếu, kiểm tra tính hợp lệ và ghi nhận trạng thái đã soát."),
        ("Tiền điều kiện", "Nhân viên đã đăng nhập thành công và đã chọn đúng Phòng chiếu, Suất chiếu hiện tại trên ứng dụng."),
        ("Luồng sự kiện chính", "1. Nhân viên mở màn hình Quét vé (Scanner Screen).\n2. Hướng camera thiết bị vào mã QR trên vé của khán giả.\n3. Ứng dụng tự động nhận diện, trích xuất chuỗi mã hóa và phân tích thông tin vé (Mã vé, Phòng chiếu, Suất chiếu, Số ghế).\n4. Ứng dụng kiểm tra tính hợp lệ: đối chiếu phòng chiếu và khung giờ suất chiếu đang chọn.\n5. Ứng dụng kiểm tra trùng lặp trong cơ sở dữ liệu ngoại tuyến (Hive Box): xác nhận vé chưa từng được quét.\n6. Ứng dụng phát âm thanh xác nhận thành công, hiển thị thông báo \"VÉ HỢP LỆ\" (màu xanh lá) kèm số ghế, đồng thời lưu bản ghi vé vào bộ nhớ thiết bị."),
        ("Luồng ngoại lệ", "3a. Mã QR không đúng định dạng: Ứng dụng báo lỗi \"Mã vé không hợp lệ\".\n4a. Vé sai phòng chiếu: Phòng trên vé khác phòng đang chọn → Báo lỗi màu đỏ \"SAI PHÒNG CHIẾU\" kèm thông tin phòng đúng của vé.\n4b. Vé sai suất chiếu: Giờ chiếu trên vé không khớp với suất chiếu đang diễn ra → Báo lỗi \"SAI SUẤT CHIẾU\".\n5a. Vé bị quét trùng (Anti-passback): Mã vé đã tồn tại trong danh sách vé đã quét → Phát chuông cảnh báo vi phạm, hiện thông báo đỏ \"CẢNH BÁO: VÉ ĐÃ ĐƯỢC QUÉT TRƯỚC ĐÓ\"."),
        ("Hậu điều kiện", "Vé hợp lệ được ghi nhận trạng thái \"Đã quét\" trong hệ thống và sẵn sàng để đồng bộ lên máy chủ.")
    ])
    add_p("Bảng 2.4. Đặc tả Use Case Quét mã QR soát vé", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # UC03
    add_usecase_table("2.6.3. Use Case UC03: Đồng bộ vé đã soát lên máy chủ", [
        ("Tên Use Case", "UC03 - Đồng bộ vé đã soát lên máy chủ"),
        ("Actor", "Nhân viên soát vé / Hệ thống Mobile App"),
        ("Mô tả", "Tự động đồng bộ các bản ghi vé đã quét hợp lệ từ bộ nhớ ngoại tuyến của ứng dụng di động lên cơ sở dữ liệu máy chủ trung tâm."),
        ("Tiền điều kiện", "Có ít nhất một vé hợp lệ đã được quét lưu trong Hive Box và thiết bị có kết nối mạng Internet."),
        ("Luồng sự kiện chính", "1. Ngay sau khi quét thành công một vé (hoặc khi nhân viên bấm nút \"Đồng bộ vé\"), ứng dụng kích hoạt tiến trình đồng bộ ngầm.\n2. Ứng dụng đóng gói danh sách vé chưa đồng bộ thành mảng JSON.\n3. Ứng dụng gửi yêu cầu qua giao thức HTTP POST tới API /api/v1/sync_tickets.\n4. Máy chủ nhận payload, kiểm tra ràng buộc và ghi các vé hợp lệ vào bảng tickets trong cơ sở dữ liệu SQLite.\n5. Máy chủ trả về phản hồi mã 200 OK với thông báo đồng bộ thành công.\n6. Ứng dụng di động cập nhật cờ isSynced = true cho các vé tương ứng trong bộ nhớ Hive."),
        ("Luồng ngoại lệ", "3a. Thiết bị mất kết nối mạng (Offline): Ứng dụng ghi nhận trạng thái chờ đồng bộ (isSynced = false), lưu trữ an toàn trong Hive và tự động thử lại khi phát hiện kết nối mạng được phục hồi.\n4a. Lỗi xung đột dữ liệu trên máy chủ: Máy chủ từ chối bản ghi trùng lặp và trả về danh sách các vé đã ghi nhận."),
        ("Hậu điều kiện", "Dữ liệu vé trên máy chủ trung tâm được cập nhật đầy đủ, tạo cơ sở dữ liệu cho bước đối soát AI.")
    ])
    add_p("Bảng 2.5. Đặc tả Use Case Đồng bộ vé đã soát lên máy chủ", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # UC04
    add_usecase_table("2.6.4. Use Case UC04: Phân tích ảnh camera và đối soát ghế tự động", [
        ("Tên Use Case", "UC04 - Phân tích ảnh camera và đối soát ghế tự động"),
        ("Actor", "Hệ thống AI / Quản trị viên (Admin)"),
        ("Mô tả", "Phân tích ảnh chụp snapshot camera phòng chiếu bằng mô hình thị giác máy tính, xác định vị trí khán giả ngồi thực tế và đối soát logic tập hợp với danh sách vé đã soát tại cổng."),
        ("Tiền điều kiện", "Suất chiếu đã bắt đầu (khoảng 10-15 phút sau giờ chiếu), phòng chiếu đã có tệp cấu hình tọa độ ghế đa giác (seats_config_roomX.json) và đã nhận dữ liệu vé đã đồng bộ."),
        ("Luồng sự kiện chính", "1. Quản trị viên chọn phòng chiếu trên Web Admin, tải ảnh chụp snapshot từ camera CCTV và nhấn nút \"⚡ Chạy AI\" (hoặc hệ thống định thời tự động kích hoạt).\n2. Hệ thống gửi ảnh tới API POST /api/v1/analyze kèm theo room_id và showtime_id.\n3. Mô hình YOLOv8n nhận diện toàn bộ các vị trí đầu người trong khung hình, trích xuất danh sách tọa độ tâm (x, y).\n4. Thuật toán Ray Casting đối chiếu từng tọa độ tâm với danh sách các đa giác ghế trong tệp cấu hình để xác định danh sách các ghế có người ngồi thực tế (Tập B).\n5. Hệ thống truy vấn cơ sở dữ liệu SQLite lấy danh sách các ghế đã soát vé hợp lệ cho suất chiếu đó (Tập A).\n6. Hệ thống thực hiện phép trừ đại số tập hợp:\n   - Xác định ghế ngồi không vé / khách lậu: B \\ A.\n   - Xác định ghế đã soát vé nhưng không có người ngồi: A \\ B.\n7. Hệ thống tự động lưu bản ghi phân tích và sinh cảnh báo vào bảng alerts.\n8. Trả về kết quả phân tích trực quan lên giao diện Web Admin."),
        ("Luồng ngoại lệ", "2a. Không tìm thấy tệp cấu hình đa giác ghế: Máy chủ trả về mã lỗi 404 \"Không tìm thấy cấu hình ghế cho phòng chiếu\".\n3a. Ảnh chụp bị mờ hoặc quá tối không nhận diện được: Mô hình trả về 0 người → Hệ thống cảnh báo chất lượng ảnh camera không đạt yêu cầu."),
        ("Hậu điều kiện", "Kết quả đối soát và các cảnh báo vi phạm được lưu trữ đầy đủ trong cơ sở dữ liệu hệ thống.")
    ])
    add_p("Bảng 2.6. Đặc tả Use Case Phân tích ảnh camera và đối soát ghế tự động", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # UC05
    add_usecase_table("2.6.5. Use Case UC05: Tiếp nhận và xử lý cảnh báo vi phạm", [
        ("Tên Use Case", "UC05 - Tiếp nhận và xử lý cảnh báo vi phạm"),
        ("Actor", "Quản trị viên (Admin), Nhân viên soát vé (Staff)"),
        ("Mô tả", "Tiếp nhận các cảnh báo lệch lượng khách do hệ thống AI sinh ra, kiểm tra thực tế và cập nhật trạng thái xử lý vi phạm."),
        ("Tiền điều kiện", "Hệ thống AI đã thực hiện xong tiến trình phân tích UC04 và ghi nhận có chênh lệch ghế vi phạm."),
        ("Luồng sự kiện chính", "1. Hệ thống phát tín hiệu cảnh báo: Web Admin hiển thị thẻ cảnh báo nổi bật trên Dashboard/Alerts; ứng dụng di động của nhân viên phụ trách phòng chiếu nhận thông báo âm thanh rung.\n2. Quản trị viên hoặc Nhân viên mở xem chi tiết cảnh báo: phòng chiếu, suất chiếu, loại vi phạm (ngồi lậu B \\ A, vắng khách A \\ B), danh sách mã ghế cụ thể.\n3. Nhân viên trực tiếp vào phòng chiếu kiểm tra vị trí ghế vi phạm được chỉ định.\n4. Sau khi nhắc nhở khán giả về đúng ghế hoặc mời khách mua bổ sung vé, người dùng nhấn nút \"Đánh dấu đã xử lý\" trên Web Admin (gọi API POST /api/v1/resolve_alert/{alert_id}).\n5. Máy chủ cập nhật trường resolved = 1 trong cơ sở dữ liệu.\n6. Giao diện chuyển trạng thái cảnh báo sang màu xanh \"Đã xử lý\"."),
        ("Luồng ngoại lệ", "4a. Lỗi kết nối mạng khi xác nhận: Không thể gọi API cập nhật → Hệ thống hiển thị thông báo lỗi \"Cập nhật trạng thái thất bại, vui lòng thử lại\"."),
        ("Hậu điều kiện", "Bản ghi cảnh báo được chuyển sang trạng thái đã xử lý hoàn tất, dữ liệu báo cáo SOC được cập nhật tức thời.")
    ])
    add_p("Bảng 2.7. Đặc tả Use Case Tiếp nhận và xử lý cảnh báo vi phạm", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # UC06
    add_usecase_table("2.6.6. Use Case UC06: Báo cáo và xử lý sự cố phòng chiếu", [
        ("Tên Use Case", "UC06 - Báo cáo và xử lý sự cố phòng chiếu"),
        ("Actor", "Nhân viên soát vé (Báo cáo), Quản trị viên (Tiếp nhận & Xử lý)"),
        ("Mô tả", "Cho phép nhân viên gửi báo cáo về các hư hỏng cơ sở vật chất phát hiện trong phòng chiếu và quản trị viên quản lý tiến độ khắc phục."),
        ("Tiền điều kiện", "Nhân viên đã đăng nhập vào ứng dụng di động; Quản trị viên đang truy cập trang Quản lý Sự cố trên Web Admin."),
        ("Luồng sự kiện chính", "1. Nhân viên phát hiện cơ sở vật chất gặp vấn đề (ghế gãy, rách đệm, lỗi điều hòa, rác bẩn).\n2. Nhân viên vào mục \"Báo cáo sự cố\" trên Mobile App.\n3. Chọn phòng chiếu, chọn danh mục sự cố (Ghế hỏng, Vệ sinh, Thiết bị), nhập số ghế cụ thể và ghi chú mô tả.\n4. Nhân viên nhấn nút \"Gửi báo cáo\".\n5. Ứng dụng gửi dữ liệu qua API POST /api/v1/incidents lên máy chủ.\n6. Máy chủ lưu bản ghi sự cố vào bảng incidents với trạng thái ban đầu là \"Chờ xử lý\" (Pending).\n7. Web Admin nhận thông tin sự cố mới, Quản trị viên điều phối bộ phận kỹ thuật khắc phục.\n8. Sau khi khắc phục xong, Quản trị viên nhấn nút \"Xác nhận đã khắc phục\" (gọi API POST /api/v1/incidents/{incident_id}/resolve).\n9. Hệ thống chuyển trạng thái sự cố sang \"Đã khắc phục\" (Resolved)."),
        ("Luồng ngoại lệ", "4a. Thiếu trường thông tin bắt buộc: Nhân viên chưa nhập vị trí hoặc mô tả → Ứng dụng nhắc nhở \"Vui lòng nhập đầy đủ thông tin sự cố\".\n5a. Mất kết nối khi gửi: Báo lỗi kết nối mạng và yêu cầu gửi lại khi có mạng."),
        ("Hậu điều kiện", "Sự cố được ghi nhận và theo dõi xuyên suốt vòng đời từ khi phát hiện đến khi được khắc phục triệt để.")
    ])
    add_p("Bảng 2.8. Đặc tả Use Case Báo cáo và xử lý sự cố phòng chiếu", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # Save docx
    doc.save(OUTPUT_DOCX)
    print("DOCX created successfully at:", OUTPUT_DOCX)

if __name__ == "__main__":
    build_docx()

