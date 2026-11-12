# -*- coding: utf-8 -*-
"""
Trình biên dịch Báo cáo Đồ án Tốt nghiệp chuẩn mẫu Khoa CNTT - Trường Đại học Kiến trúc Đà Nẵng (DAU)
Chuyển đổi toàn bộ nội dung, bảng biểu, công thức và hình ảnh từ BAO_CAO_DO_AN_CINESIGHT.docx
sang định dạng chuẩn của 2 file mẫu:
  - PL02_A_BiaThuyetMinh(MẪU).docx
  - PL03_B_RuotThuyetMinh(MẪU).docx

Đầu ra: C:\\CineSightApp\\docs\\tailieu_doc\\BAO_CAO_DO_AN_TOT_NGHIEP_CINESIGHT_DAU.docx
"""

import io
import os
import re
import sys
import zipfile
import docx
from docx.shared import Cm, Emu, Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COVER_TPL = r"C:\Users\Dell KIM ANH\.gemini\antigravity\brain\779a87a8-afe5-44b9-9038-d06517f57dee\.user_uploaded\media_1794488697906_9c477d04.docx"
SRC_DOCX = r"C:\CineSightApp\docs\tailieu_doc\BAO_CAO_DO_AN_CINESIGHT.docx"
FIG16_FALLBACK = r"C:\CineSightApp\tools\qr_sample\CCTV_ROOM4_ANNOTATED_SEATS.jpg"
OUT_DOCX = r"C:\CineSightApp\docs\tailieu_doc\BAO_CAO_DO_AN_TOT_NGHIEP_CINESIGHT_DAU.docx"

THESIS_TITLE_UPPER = "HỆ THỐNG SOÁT VÉ VÀ KIỂM ĐẾM KHÁN GIẢ RẠP CHIẾU PHIM ỨNG DỤNG THỊ GIÁC MÁY TÍNH (CINESIGHT)"
THESIS_TITLE_NORMAL = "Hệ thống soát vé và kiểm đếm khán giả rạp chiếu phim ứng dụng thị giác máy tính (CineSight)"
STUDENT_NAME_UPPER = "[HỌ VÀ TÊN SINH VIÊN]"
STUDENT_NAME = "[Họ và tên sinh viên]"
STUDENT_ID = "2251220124"
STUDENT_CLASS = "[Lớp của bạn]"
ADVISOR_NAME = "[Học hàm, học vị. Họ và tên GVHD]"
DATE_STR = "Đà Nẵng, 11/2026"

# Mapping old global Figure numbers (1..26) -> new per-chapter Figure numbers
FIG_REMAP = {
    1: "1.1",
    2: "2.1", 3: "2.2", 4: "2.3", 5: "2.4",
    6: "2.5", 7: "2.6", 8: "2.7", 9: "2.8",
    10: "3.1", 11: "3.2", 12: "3.3", 13: "3.4", 14: "3.5",
    15: "3.6", 16: "3.7", 17: "3.8", 18: "3.9", 19: "3.10",
    20: "3.11", 21: "3.12", 22: "3.13", 23: "3.14", 24: "3.15",
    25: "3.16", 26: "3.17",
}

SYMBOLS_DATA = [
    ("R", "Phòng chiếu phim trong cụm rạp (R ∈ {1, 2, 3, 4})"),
    ("A", "Tập hợp các mã ghế đã được quét mã QR hợp lệ tại cửa rạp"),
    ("B", "Tập hợp các mã ghế được hệ thống AI xác nhận đang có khán giả ngồi"),
    ("A ∩ B", "Tập hợp các ghế hợp lệ (đã soát vé và có khán giả ngồi đúng chỗ)"),
    ("B \\ A", "Tập hợp các ghế vi phạm / ngồi chui / ngồi sai vị trí"),
    ("A \\ B", "Tập hợp các ghế đã soát vé nhưng hiện tại vắng mặt trên camera"),
    ("|A|, |B|", "Lực lượng (số phần tử) của tập hợp A và tập hợp B"),
    ("(x₁, y₁, x₂, y₂)", "Tọa độ khung bao (Bounding Box) vùng đầu người từ YOLOv8n"),
    ("(x_anchor, y_anchor)", "Tọa độ điểm neo phối cảnh tính tại mức 78% chiều cao khung bao"),
    ("ε", "Dung sai biên đa giác ghế theo điểm ảnh (Edge Tolerance = 8,0 px)"),
    ("IoU", "Chỉ số giao trên hợp (Intersection over Union) đánh giá khung bao"),
    ("mAP@0.5", "Độ chuẩn xác trung bình tại ngưỡng IoU = 0,5"),
]


# ==============================================================================
# XML / FONT / PARAGRAPH HELPERS
# ==============================================================================

def set_run_tnr(run, size_pt=13, bold=None, italic=None, color=RGBColor(0, 0, 0), font_name="Times New Roman"):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:cs"), font_name)
    rFonts.set(qn("w:eastAsia"), font_name)


def clear_paragraph(p):
    pElement = p._element
    for child in list(pElement):
        if child.tag != qn("w:pPr"):
            pElement.remove(child)


def add_styled_paragraph(doc, text="", style=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                         size_pt=13, bold=False, italic=False, line_spacing=1.3,
                         space_before=0, space_after=4, left_indent_cm=0, first_line_cm=0,
                         keep_with_next=False, font_name="Times New Roman"):
    p = doc.add_paragraph()
    if style:
        p.style = style
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line_spacing
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.keep_with_next = keep_with_next
    if left_indent_cm:
        pf.left_indent = Cm(left_indent_cm)
    if first_line_cm:
        pf.first_line_indent = Cm(first_line_cm)
    if text:
        r = p.add_run(text)
        set_run_tnr(r, size_pt=size_pt, bold=bold, italic=italic, font_name=font_name)
    return p


def add_chapter_title(doc, title_text, page_break=True, blank_lines=2, in_toc=True):
    """Tiêu đề mục lớn / Chương: Times New Roman, Bold, 14pt, Center, để 2 dòng trống."""
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    if in_toc:
        p.style = doc.styles["Heading 1"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.line_spacing = 1.15
    pf.space_before = Pt(8)
    pf.space_after = Pt(6)
    pf.keep_with_next = True
    r = p.add_run(title_text)
    set_run_tnr(r, size_pt=14, bold=True, italic=False)
    for _ in range(blank_lines):
        bp = add_styled_paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13,
                                  line_spacing=1.3, space_before=0, space_after=0)
        bp.paragraph_format.keep_with_next = True
    return p


def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 2"]
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.line_spacing = 1.3
    pf.space_before = Pt(8)
    pf.space_after = Pt(4)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run_tnr(r, size_pt=13, bold=True, italic=False)
    return p


def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 3"]
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.line_spacing = 1.3
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run_tnr(r, size_pt=13, bold=True, italic=True)
    return p


def ensure_custom_caption_styles(doc):
    for sname in ("DAU_TableCaption", "DAU_FigureCaption"):
        if sname not in [s.name for s in doc.styles]:
            st = doc.styles.add_style(sname, docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = doc.styles["Normal"]
            st.font.name = "Times New Roman"
            st.font.size = Pt(13)
            st.font.color.rgb = RGBColor(0, 0, 0)


def add_caption(doc, label_prefix, title_body, is_table=True):
    """Bảng: nằm TRÊN bảng; Hình: nằm DƯỚI hình. Times New Roman, 13pt, dãn dòng 1.3, căn giữa."""
    style_name = "DAU_TableCaption" if is_table else "DAU_FigureCaption"
    p = doc.add_paragraph()
    p.style = doc.styles[style_name]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.line_spacing = 1.3
    pf.space_before = Pt(6 if is_table else 3)
    pf.space_after = Pt(4 if is_table else 8)
    pf.keep_with_next = is_table  # Table caption sticks to the table below it

    r1 = p.add_run(label_prefix)
    set_run_tnr(r1, size_pt=13, bold=True, italic=True)
    if title_body:
        r2 = p.add_run(" " + title_body)
        set_run_tnr(r2, size_pt=13, bold=False, italic=True)
    return p


def add_word_field(paragraph, field_instruction, size_pt=10, bold=False, italic=False, placeholder="1"):
    """Insert an OOXML complex field (PAGE, TOC, etc.) cleanly."""
    run_begin = paragraph.add_run()
    set_run_tnr(run_begin, size_pt=size_pt, bold=bold, italic=italic)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    fld_begin.set(qn("w:dirty"), "true")
    run_begin._element.append(fld_begin)

    run_instr = paragraph.add_run()
    set_run_tnr(run_instr, size_pt=size_pt, bold=bold, italic=italic)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {field_instruction} "
    run_instr._element.append(instr)

    run_sep = paragraph.add_run()
    set_run_tnr(run_sep, size_pt=size_pt, bold=bold, italic=italic)
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run_sep._element.append(fld_sep)

    run_val = paragraph.add_run(placeholder)
    set_run_tnr(run_val, size_pt=size_pt, bold=bold, italic=italic)

    run_end = paragraph.add_run()
    set_run_tnr(run_end, size_pt=size_pt, bold=bold, italic=italic)
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run_end._element.append(fld_end)


def set_section_page_layout(section, pg_fmt=None, pg_start=None):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.header_distance = Cm(1.6)
    section.footer_distance = Cm(1.6)
    section.different_first_page_header_footer = False

    sectPr = section._sectPr
    for old in sectPr.findall(qn("w:pgNumType")):
        sectPr.remove(old)
    if pg_fmt or pg_start is not None:
        pg = OxmlElement("w:pgNumType")
        if pg_fmt:
            pg.set(qn("w:fmt"), pg_fmt)
        if pg_start is not None:
            pg.set(qn("w:start"), str(pg_start))
        sectPr.append(pg)


def set_paragraph_border(p, top=False, bottom=False):
    pPr = p._element.get_or_add_pPr()
    for b in pPr.findall(qn("w:pBdr")):
        pPr.remove(b)
    pBdr = OxmlElement("w:pBdr")
    if top:
        t = OxmlElement("w:top")
        t.set(qn("w:val"), "single")
        t.set(qn("w:sz"), "4")
        t.set(qn("w:space"), "2")
        t.set(qn("w:color"), "000000")
        pBdr.append(t)
    if bottom:
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "2")
        b.set(qn("w:color"), "000000")
        pBdr.append(b)
    pPr.append(pBdr)


def clear_header_footer(section):
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    for hp in section.header.paragraphs:
        clear_paragraph(hp)
    for fp in section.footer.paragraphs:
        clear_paragraph(fp)
    for tbl in list(section.footer.tables):
        tbl._element.getparent().remove(tbl._element)


def configure_roman_footer(section):
    clear_header_footer(section)
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_word_field(fp, r"PAGE \* lowerRoman", size_pt=10, placeholder="i")


def set_table_top_border_only(row, color="000000", sz="4"):
    for cell in row.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        for b in tcPr.findall(qn("w:tcBorders")):
            tcPr.remove(b)
        borders = OxmlElement("w:tcBorders")
        top = OxmlElement("w:top")
        top.set(qn("w:val"), "single")
        top.set(qn("w:sz"), sz)
        top.set(qn("w:space"), "0")
        top.set(qn("w:color"), color)
        borders.append(top)
        for edge in ("left", "bottom", "right"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "none")
            borders.append(el)
        tcPr.append(borders)
        set_cell_margins(cell, top=50, bottom=0, left=0, right=0)


def configure_main_header_footer(section):
    clear_header_footer(section)
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hp.paragraph_format.space_before = Pt(0)
    hp.paragraph_format.space_after = Pt(2)
    set_paragraph_border(hp, bottom=True)
    hr = hp.add_run(THESIS_TITLE_UPPER)
    set_run_tnr(hr, size_pt=8.8, bold=False, italic=True)

    # Clear default empty footer paragraph and use a clean 3-col table (sum = 16.0 cm)
    for fp in list(section.footer.paragraphs):
        fp.paragraph_format.space_before = Pt(0)
        fp.paragraph_format.space_after = Pt(0)
        fp.paragraph_format.line_spacing = 1.0
    tbl = section.footer.add_table(rows=1, cols=3, width=Cm(16.0))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    widths = [Cm(6.7), Cm(7.8), Cm(1.5)]
    for idx, w in enumerate(widths):
        tbl.rows[0].cells[idx].width = w
    set_table_top_border_only(tbl.rows[0])

    c0, c1, c2 = tbl.rows[0].cells
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(0)
    set_run_tnr(p0.add_run(f"SVTH: {STUDENT_NAME} ({STUDENT_ID})"), size_pt=9.5)

    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(2)
    p1.paragraph_format.space_after = Pt(0)
    set_run_tnr(p1.add_run(f"GVHD: {ADVISOR_NAME}"), size_pt=9.5)

    p2 = c2.paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p2.paragraph_format.space_before = Pt(2)
    p2.paragraph_format.space_after = Pt(0)
    add_word_field(p2, "PAGE", size_pt=9.5, placeholder="1")


def configure_appendix_footer(section):
    clear_header_footer(section)
    for fp in list(section.footer.paragraphs):
        fp.paragraph_format.space_before = Pt(0)
        fp.paragraph_format.space_after = Pt(0)
        fp.paragraph_format.line_spacing = 1.0
    tbl = section.footer.add_table(rows=1, cols=2, width=Cm(16.0))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.rows[0].cells[0].width = Cm(14.0)
    tbl.rows[0].cells[1].width = Cm(2.0)
    set_table_top_border_only(tbl.rows[0])

    p0 = tbl.rows[0].cells[0].paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(0)
    set_run_tnr(p0.add_run("Phụ lục"), size_pt=10)

    p1 = tbl.rows[0].cells[1].paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p1.paragraph_format.space_before = Pt(2)
    p1.paragraph_format.space_after = Pt(0)
    add_word_field(p1, "PAGE", size_pt=10, placeholder="1")


def configure_base_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(k), "Times New Roman")

    existing_styles = {s.name for s in doc.styles}
    for lvl, (hname, hsz, hbold, hital, halign) in enumerate([
        ("Heading 1", 14, True, False, WD_ALIGN_PARAGRAPH.CENTER),
        ("Heading 2", 13, True, False, WD_ALIGN_PARAGRAPH.JUSTIFY),
        ("Heading 3", 13, True, True, WD_ALIGN_PARAGRAPH.JUSTIFY),
    ]):
        if hname in existing_styles:
            st = doc.styles[hname]
        else:
            st = doc.styles.add_style(hname, docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = doc.styles["Normal"]
        st.font.name = "Times New Roman"
        st.font.size = Pt(hsz)
        st.font.bold = hbold
        st.font.italic = hital
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.alignment = halign
        srPr = st.element.get_or_add_rPr()
        srFonts = srPr.find(qn("w:rFonts"))
        if srFonts is None:
            srFonts = OxmlElement("w:rFonts")
            srPr.insert(0, srFonts)
        for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            srFonts.set(qn(k), "Times New Roman")
        spPr = st.element.get_or_add_pPr()
        for old_lvl in spPr.findall(qn("w:outlineLvl")):
            spPr.remove(old_lvl)
        ol = OxmlElement("w:outlineLvl")
        ol.set(qn("w:val"), str(lvl))
        spPr.append(ol)

    ensure_custom_caption_styles(doc)

    # Set w:updateFields in settings.xml
    settings = doc.settings.element
    if settings.find(qn("w:updateFields")) is None:
        uf = OxmlElement("w:updateFields")
        uf.set(qn("w:val"), "true")
        settings.append(uf)


# ==============================================================================
# COVER PAGE EDITOR (FROM DAU TEMPLATE PL02_A)
# ==============================================================================

def update_cover_pages(doc):
    """Cập nhật Bìa chính (P0..P42), Bìa lót (P43..P82) và gáy sách giữ nguyên khung viền đôi DAU."""
    def edit_para_simple(idx, segments):
        p = doc.paragraphs[idx]
        clear_paragraph(p)
        for txt, sz, b, ital in segments:
            r = p.add_run(txt)
            set_run_tnr(r, size_pt=sz, bold=b, italic=ital)

    # Update spine textboxes (VML + DrawingML duplicates) so "Trần Văn Bình / 2017" is replaced cleanly
    for tb in doc.element.body.findall(".//" + qn("w:txbxContent")):
        t_nodes = tb.findall(".//" + qn("w:t"))
        if not t_nodes:
            continue
        joined = "".join(n.text or "" for n in t_nodes)
        if "Trần Văn Bình" in joined or "TÊN ĐỀ TÀI" in joined:
            spine_text = f"      {STUDENT_NAME}       HỆ THỐNG SOÁT VÉ VÀ KIỂM ĐẾM KHÁN GIẢ (CINESIGHT) ………     2026"
            t_nodes[0].text = spine_text
            for extra in t_nodes[1:]:
                extra.text = ""

    # Remove 6 empty bordered spacer paragraphs per cover so 3-line title fits strictly 1 page per cover
    to_remove = [doc.paragraphs[idx]._element for idx in (24, 25, 26, 27, 28, 29, 65, 66, 67, 68, 69, 70, 71)]
    # Update text BEFORE removing elements so indices remain stable!
    for title_idx in (17, 60):
        p = doc.paragraphs[title_idx]
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        edit_para_simple(title_idx, [(THESIS_TITLE_UPPER, 18, True, False)])

    for adv_idx, stu_idx, id_idx, cls_idx, date_idx in [
        (31, 32, 33, 34, 39),
        (73, 74, 75, 76, 82),
    ]:
        edit_para_simple(adv_idx, [("Người hướng dẫn: ", 14, False, False), (ADVISOR_NAME, 14, True, False)])
        edit_para_simple(stu_idx, [("Sinh viên thực hiện: ", 14, False, False), (STUDENT_NAME_UPPER, 14, True, False)])
        edit_para_simple(id_idx, [("Mã số sinh viên: ", 14, False, False), (STUDENT_ID, 14, True, False)])
        edit_para_simple(cls_idx, [("Lớp: ", 14, False, False), (STUDENT_CLASS, 14, True, False)])
        edit_para_simple(date_idx, [(DATE_STR, 13, True, False)])

    for el in to_remove:
        el.getparent().remove(el)


# ==============================================================================
# TEXT NORMALIZATION & TABLE / IMAGE HELPERS
# ==============================================================================

LATEX_INLINE_MAP = {
    "$(W_{img}, H_{img})$": "(W_img, H_img)",
    "$(x_1, y_1, x_2, y_2)$": "(x₁, y₁, x₂, y₂)",
    "$(x_{anchor}, y_{anchor})$": "(x_anchor, y_anchor)",
    "$1920 \\times 1080$": "1920 × 1080",
    "$8.0\\text{ px}$": "8,0 px",
    "$M(x_{anchor}, y_{anchor})$": "M(x_anchor, y_anchor)",
    "$N$": "N",
    "$P = \\{(x_{p1}, y_{p1}), (x_{p2}, y_{p2}), \\dots, (x_{pN}, y_{pN})\\}$": "P = {(xₚ₁, yₚ₁), (xₚ₂, yₚ₂), …, (xₚₙ, yₚₙ)}",
    "$P$": "P",
    "$R$": "R",
    "$\\ge -8.0\\text{ px}$": "≥ −8,0 px",
    "$d < \\max(8.0, 0.45 \\times s)$": "d < max(8,0; 0,45 × s)",
    "$s = (w + h)/2$": "s = (w + h)/2",
    "$scale_x = 1920 / W_{img}, scale_y = 1080 / H_{img}$": "scale_x = 1920 / W_img, scale_y = 1080 / H_img",
}


def clean_and_remap_text(text, chapter_num=None):
    # Remove any residual DUT / group phrasing in prose
    text = text.replace("nhóm chúng em", "em")
    text = text.replace("Nhóm xin trình bày", "Đồ án trình bày")
    text = text.replace("nhóm đã xây dựng công cụ", "em đã xây dựng công cụ")
    text = text.replace("Trường Đại học Bách Khoa, Đại học Đà Nẵng", "Trường Đại học Kiến trúc Đà Nẵng")
    text = text.replace("CHƯƠNG 1. CƠ SỞ LÝ THUYẾT", "CHƯƠNG 1: CƠ SỞ LÝ THUYẾT")
    text = text.replace("CHƯƠNG 2. PHÂN TÍCH THIẾT KẾ HỆ THỐNG", "CHƯƠNG 2: PHÂN TÍCH THIẾT KẾ HỆ THỐNG")
    text = text.replace("CHƯƠNG 3. KẾT QUẢ THỰC HIỆN VÀ ĐÁNH GIÁ", "CHƯƠNG 3: KẾT QUẢ THỰC HIỆN VÀ ĐÁNH GIÁ")

    # Convert inline LaTeX expressions to clean Unicode math and strip Markdown backticks
    for k, v in LATEX_INLINE_MAP.items():
        text = text.replace(k, v)
    text = text.replace("`", "")

    # Remap any inline cross-references to Hình N -> Hình X.Y
    def _repl_fig(m):
        num = int(m.group(1))
        if num in FIG_REMAP:
            return f"Hình {FIG_REMAP[num]}"
        return m.group(0)

    text = re.sub(r"Hình\s+(\d+)(?!\.\d)", _repl_fig, text)
    return text


def add_formatted_source_paragraph(doc, src_p, size_pt=13, line_spacing=1.3, is_list=False, is_ref=False):
    """Copy source paragraph preserving inline bold runs cleanly with Times New Roman."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.line_spacing = line_spacing
    pf.space_before = Pt(0)
    pf.space_after = Pt(4)
    if is_list:
        pf.left_indent = Cm(0.6)
        pf.first_line_indent = Cm(-0.35)
    elif is_ref:
        pf.left_indent = Cm(0.8)
        pf.first_line_indent = Cm(-0.8)

    # Reconstruct runs cleanly while updating text
    full_text = clean_and_remap_text(src_p.text)
    if not full_text.strip():
        return p

    # If bullet paragraph has "• Prefix: rest", bold the prefix for clean readability
    if is_list and ":" in full_text[:110] and full_text.lstrip().startswith("•"):
        idx_colon = full_text.find(":")
        prefix = full_text[: idx_colon + 1]
        rest = full_text[idx_colon + 1 :]
        r1 = p.add_run(prefix)
        set_run_tnr(r1, size_pt=size_pt, bold=True)
        if rest:
            r2 = p.add_run(rest)
            set_run_tnr(r2, size_pt=size_pt, bold=False)
        return p

    # Preserve inline run bold/italic flags where run lengths didn't shift drastically, else single clean run
    if any(r.bold or r.italic for r in src_p.runs):
        for r_src in src_p.runs:
            rt = clean_and_remap_text(r_src.text)
            if rt:
                r = p.add_run(rt)
                set_run_tnr(r, size_pt=size_pt, bold=bool(r_src.bold), italic=bool(r_src.italic))
    else:
        r = p.add_run(full_text)
        set_run_tnr(r, size_pt=size_pt, bold=False)
    return p


def set_cell_borders(cell, color="999999", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    for b in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(b)
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tcPr.append(borders)


def set_cell_shading(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    for sh in tcPr.findall(qn("w:shd")):
        tcPr.remove(sh)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tcPr.append(shd)


def set_cell_margins(cell, top=80, bottom=80, left=110, right=110):
    tcPr = cell._tc.get_or_add_tcPr()
    for m in tcPr.findall(qn("w:tcMar")):
        tcPr.remove(m)
    tcMar = OxmlElement("w:tcMar")
    for k, v in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        el = OxmlElement(f"w:{k}")
        el.set(qn("w:w"), str(v))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)
    tcPr.append(tcMar)


def add_styled_table(doc, rows_data, col_widths_cm=None, font_size=12, header_bg="E6EDF5",
                     center_cols=(), monospace=False):
    tbl = doc.add_table(rows=len(rows_data), cols=len(rows_data[0]))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Total width = 16.0 cm (21 - 3 - 2)
    for r_idx, row_vals in enumerate(rows_data):
        tr = tbl.rows[r_idx]
        trPr = tr._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if r_idx == 0:
            trPr.append(OxmlElement("w:tblHeader"))

        for c_idx, val in enumerate(row_vals):
            cell = tr.cells[c_idx]
            if col_widths_cm and c_idx < len(col_widths_cm):
                cell.width = Cm(col_widths_cm[c_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_borders(cell)
            set_cell_margins(cell)
            if r_idx == 0 and header_bg:
                set_cell_shading(cell, header_bg)

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            if r_idx == 0 or c_idx in center_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            txt = clean_and_remap_text(str(val).strip())
            r = p.add_run(txt)
            fname = "Consolas" if monospace else "Times New Roman"
            set_run_tnr(r, size_pt=font_size, bold=(r_idx == 0), font_name=fname)

    # Tiny breathing room after table
    sp = add_styled_paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=6, line_spacing=1.0, space_before=0, space_after=2)
    return tbl


def add_formula_block(doc, formula_lines, eq_number):
    """Đánh số công thức bên phải theo quy chuẩn DAU: (1.1), (1.2)..."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    c_left, c_right = tbl.rows[0].cells
    c_left.width = Cm(14.2)
    c_right.width = Cm(1.8)
    set_cell_borders(c_left, color="CBD5E1", sz="4")
    set_cell_shading(c_left, "F8FAFC")
    set_cell_margins(c_left, top=100, bottom=100, left=140, right=140)
    # Right number cell borderless
    tcPr = c_right._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        borders.append(el)
    tcPr.append(borders)
    c_right.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    p_f = c_left.paragraphs[0]
    p_f.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_f.paragraph_format.line_spacing = 1.25
    p_f.paragraph_format.space_before = Pt(0)
    p_f.paragraph_format.space_after = Pt(0)
    for i, line in enumerate(formula_lines):
        if i > 0:
            p_f.add_run("\n")
        r = p_f.add_run(line)
        set_run_tnr(r, size_pt=10.5, bold=(i == 0), italic=line.startswith("#"), font_name="Consolas")

    p_n = c_right.paragraphs[0]
    p_n.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_n.paragraph_format.space_before = Pt(0)
    p_n.paragraph_format.space_after = Pt(0)
    rn = p_n.add_run(f"({eq_number})")
    set_run_tnr(rn, size_pt=13, bold=False)

    add_styled_paragraph(doc, "", size_pt=6, line_spacing=1.0, space_before=0, space_after=2)


def add_code_tree_block(doc, text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.rows[0].cells[0]
    cell.width = Cm(16.0)
    set_cell_borders(cell, color="CBD5E1", sz="4")
    set_cell_shading(cell, "F8FAFC")
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(text.rstrip())
    set_run_tnr(r, size_pt=9.5, font_name="Consolas")
    add_styled_paragraph(doc, "", size_pt=6, line_spacing=1.0, space_before=0, space_after=2)


def add_picture_fit(doc, image_bytes, src_extent_emu=None):
    """Chèn ảnh từ bytes, bảo toàn tỷ lệ nguyên bản và giới hạn gọn trong vùng in 15.6 x 19.5 cm."""
    from PIL import Image
    stream = io.BytesIO(image_bytes)
    with Image.open(io.BytesIO(image_bytes)) as im:
        px_w, px_h = im.size
    aspect = px_h / px_w if px_w else 0.75

    max_w_cm = 15.5
    max_h_cm = 18.8

    if src_extent_emu:
        cx, cy = src_extent_emu
        w_cm = cx / 360000.0
    else:
        w_cm = 15.0 if aspect <= 1.1 else 7.2

    w_cm = min(max(w_cm, 4.5), max_w_cm)
    h_cm = w_cm * aspect
    if h_cm > max_h_cm:
        h_cm = max_h_cm
        w_cm = h_cm / aspect

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(stream, width=Cm(w_cm))
    return p


def extract_paragraph_image_info(src_p):
    blips = src_p._element.findall(".//" + qn("a:blip"))
    if not blips:
        return None
    rid = blips[0].get(qn("r:embed"))
    part = src_p.part.related_parts[rid]
    extents = src_p._element.findall(".//" + qn("wp:extent"))
    ext = None
    if extents:
        cx = int(extents[0].get("cx", 0))
        cy = int(extents[0].get("cy", 0))
        if cx > 0 and cy > 0:
            ext = (cx, cy)
    return part.blob, ext


def parse_caption_text(raw_caption, is_table=False):
    raw_caption = raw_caption.strip()
    if is_table:
        m = re.match(r"^(Bảng\s+\d+\.\d+\.?)\s*(.*)$", raw_caption)
        if m:
            label = m.group(1).rstrip(".") + ":"
            return label, m.group(2).strip()
        return "Bảng:", raw_caption
    else:
        m = re.match(r"^Hình\s+(\d+)\.?\s*(.*)$", raw_caption)
        if m:
            old_num = int(m.group(1))
            new_num = FIG_REMAP.get(old_num, str(old_num))
            return f"Hình {new_num}:", m.group(2).strip()
        return "Hình:", raw_caption


# ==============================================================================
# MAIN BUILD PIPELINE
# ==============================================================================

def build_thesis():
    doc = docx.Document(COVER_TPL)
    src = docx.Document(SRC_DOCX)

    configure_base_styles(doc)
    update_cover_pages(doc)

    # --------------------------------------------------------------------------
    # SECTION 1: TRANG NHẬN XÉT & TÓM TẮT (Không Header, Không Footer, Không Số trang)
    # --------------------------------------------------------------------------
    sec1 = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_page_layout(sec1)
    clear_header_footer(sec1)

    add_styled_paragraph(
        doc,
        "{Trang trắng này dùng để dán bản Nhận xét của người hướng dẫn, hoặc thay trang này bằng Nhận xét của người hướng dẫn}",
        align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=13, italic=True, space_before=160, space_after=12
    )
    doc.add_page_break()

    add_styled_paragraph(
        doc,
        "{Trang trắng này dùng để dán bản Nhận xét của người phản biện, hoặc thay trang này bằng Nhận xét của người phản biện}",
        align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=13, italic=True, space_before=160, space_after=12
    )
    doc.add_page_break()

    # TÓM TẮT (<= 1 trang, không đánh số trang)
    add_styled_paragraph(doc, "TÓM TẮT", align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=14, bold=True, line_spacing=1.15, space_after=6)
    add_styled_paragraph(doc, "", size_pt=13, line_spacing=1.3, space_after=0)  # 01 dòng trống
    for label, val in [
        ("Tên đề tài: ", THESIS_TITLE_NORMAL),
        ("Sinh viên thực hiện: ", STUDENT_NAME),
        ("Mã số SV: ", f"{STUDENT_ID}          Lớp: {STUDENT_CLASS}"),
    ]:
        p = add_styled_paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, line_spacing=1.3, space_after=3)
        r1 = p.add_run(label)
        set_run_tnr(r1, size_pt=13, bold=True)
        r2 = p.add_run(val)
        set_run_tnr(r2, size_pt=13, bold=False)

    add_styled_paragraph(
        doc,
        "Đồ án tốt nghiệp đề tài “Hệ thống soát vé và kiểm đếm khán giả rạp chiếu phim ứng dụng thị giác máy tính (CineSight)” giải quyết bài toán kiểm soát doanh thu và tự động phát hiện gian lận vị trí ghế ngồi trong cụm rạp chiếu phim thương mại (4 phòng chiếu, tổng quy mô 540 ghế). Trong bối cảnh phòng chiếu tối sử dụng camera hồng ngoại góc cao có hiện tượng thị sai và che khuất lẫn nhau, phương pháp đếm thủ công dễ sai sót và thiếu liên thông thời gian thực với dữ liệu soát vé tại cửa.",
        size_pt=13, line_spacing=1.3, space_before=6, space_after=4
    )
    add_styled_paragraph(
        doc,
        "Hệ thống được thiết kế theo kiến trúc phân tầng Khách – Chủ gồm ba phân hệ hợp nhất: (1) Dịch vụ Backend & Lõi AI (FastAPI + SQLite WAL chuẩn 3NF + YOLOv8n), trong đó mô hình đầu người best_head_v2.pt kết hợp công thức Điểm neo phối cảnh 78%, thuật toán Point-in-Polygon có dung sai biên 8,0 px và ràng buộc ghép cặp 1–1 để tạo tập ghế thực tế (Tập B), sau đó đối soát tự động bằng đại số tập hợp với tập ghế đã soát vé (Tập A) nhằm phát hiện kịp thời các trường hợp ngồi chui hoặc tự ý chuyển lên ghế VIP trái phép; (2) Trung tâm chỉ huy Web Admin SOC (React 19 + Vite + TailwindCSS) điều hành lịch chiếu, sơ đồ ghế trực quan, cảnh báo vi phạm và nhật ký sự cố; (3) Ứng dụng di động tác nghiệp hiện trường (Flutter Android / iOS PWA) hỗ trợ quét mã QR theo cơ chế Offline-First (Hive NoSQL), chống quét trùng, đồng bộ hai chiều và báo cáo sự cố kèm ảnh chụp.",
        size_pt=13, line_spacing=1.3, space_after=4
    )
    add_styled_paragraph(
        doc,
        "Kết quả thử nghiệm toàn trình trên dữ liệu thực tế cho thấy mô hình YOLOv8n đạt độ chính xác nhận diện cao trong môi trường thiếu sáng, pipeline xử lý mượt mà đáp ứng vận hành thời gian thực và toàn bộ luồng nghiệp vụ từ soát vé, cảnh báo đến bàn giao ca hoạt động ổn định, sẵn sàng triển khai thực tiễn.",
        size_pt=13, line_spacing=1.3, space_after=4
    )

    # --------------------------------------------------------------------------
    # SECTION 2: FRONT MATTER (Đánh số trang La Mã: i, ii, iii...)
    # --------------------------------------------------------------------------
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_page_layout(sec2, pg_fmt="lowerRoman", pg_start=1)
    configure_roman_footer(sec2)

    # 2.1 LỜI NÓI ĐẦU
    add_chapter_title(doc, "LỜI NÓI ĐẦU", page_break=False, blank_lines=2)
    add_styled_paragraph(
        doc,
        "Trong kỷ nguyên chuyển đổi số và sự phát triển mạnh mẽ của Trí tuệ nhân tạo (AI), công nghệ Thị giác máy tính đang được ứng dụng rộng rãi để tự động hóa các nghiệp vụ giám sát vận hành có độ chính xác cao. Đối với lĩnh vực vận hành cụm rạp chiếu phim thương mại, việc kiểm soát chặt chẽ lượng khán giả thực tế bên trong phòng chiếu tối và đối chiếu tức thì với dữ liệu vé bán ra là yêu cầu cấp thiết nhằm ngăn chặn thất thoát doanh thu cũng như nâng cao chất lượng dịch vụ.",
        size_pt=13, line_spacing=1.3, space_after=6
    )
    add_styled_paragraph(
        doc,
        "Từ nhu cầu thực tiễn đó, em đã nghiên cứu và xây dựng đề tài “Hệ thống soát vé và kiểm đếm khán giả rạp chiếu phim ứng dụng thị giác máy tính (CineSight)” nhằm hình thành một giải pháp phần mềm khép kín kết hợp giữa mô hình học sâu YOLOv8n, phân tích hình học không gian 2D, ứng dụng di động soát vé Offline-First và trung tâm điều hành Web Admin SOC.",
        size_pt=13, line_spacing=1.3, space_after=6
    )
    add_styled_paragraph(
        doc,
        f"Lời cảm ơn: Trong suốt quá trình học tập, nghiên cứu và hoàn thành đồ án tốt nghiệp này, em xin bày tỏ lòng biết ơn sâu sắc đến quý Thầy/Cô giảng viên Khoa Công nghệ Thông tin – Trường Đại học Kiến trúc Đà Nẵng đã tận tình truyền đạt kiến thức chuyên môn vững chắc trong suốt những năm đại học. Đặc biệt, em xin gửi lời cảm ơn chân thành nhất đến {ADVISOR_NAME} – người đã trực tiếp định hướng đề tài, tận tâm chỉ bảo, góp ý sâu sắc về mặt thuật toán cũng như cấu trúc hệ thống giúp em hoàn thiện đồ án này. Em cũng xin cảm ơn gia đình và bạn bè đã luôn động viên, hỗ trợ trong suốt thời gian thực hiện.",
        size_pt=13, line_spacing=1.3, space_after=6
    )

    # 2.2 CAM ĐOAN
    add_chapter_title(doc, "CAM ĐOAN", page_break=True, blank_lines=2)
    add_styled_paragraph(
        doc,
        f"Em xin cam đoan toàn bộ nội dung báo cáo đồ án tốt nghiệp với đề tài “{THESIS_TITLE_NORMAL}” là kết quả của quá trình tự nghiên cứu, thiết kế, lập trình và thực nghiệm nghiêm túc của cá nhân em dưới sự hướng dẫn khoa học của {ADVISOR_NAME}.",
        size_pt=13, line_spacing=1.3, space_after=6
    )
    add_styled_paragraph(
        doc,
        "Các số liệu thực nghiệm, sơ đồ kiến trúc, mã nguồn ứng dụng và kết quả kiểm thử trình bày trong báo cáo là hoàn toàn trung thực, không sao chép trái phép từ bất kỳ công trình hay đồ án nào khác. Mọi tài liệu tham khảo và thư viện mã nguồn mở sử dụng trong đề tài đều được trích dẫn đầy đủ và rõ ràng theo đúng quy định liêm chính học thuật của Trường Đại học Kiến trúc Đà Nẵng.",
        size_pt=13, line_spacing=1.3, space_after=24
    )
    add_styled_paragraph(doc, "Đà Nẵng, ngày ...... tháng 11 năm 2026", align=WD_ALIGN_PARAGRAPH.RIGHT, size_pt=13, italic=True, space_after=2)
    add_styled_paragraph(doc, "Sinh viên thực hiện", align=WD_ALIGN_PARAGRAPH.RIGHT, size_pt=13, bold=True, space_after=2)
    add_styled_paragraph(doc, "(Ký và ghi rõ họ tên)", align=WD_ALIGN_PARAGRAPH.RIGHT, size_pt=13, italic=True, space_after=36)
    add_styled_paragraph(doc, STUDENT_NAME, align=WD_ALIGN_PARAGRAPH.RIGHT, size_pt=13, bold=True, space_after=0)

    # 2.3 MỤC LỤC (Dynamic Word TOC field)
    add_chapter_title(doc, "MỤC LỤC", page_break=True, blank_lines=2)
    p_toc = add_styled_paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, line_spacing=1.3)
    add_word_field(p_toc, r'TOC \o "1-3" \h \z \u', size_pt=13, placeholder="[Mục lục tự động – nhấn F9 hoặc mở bằng Microsoft Word để hiển thị số trang]")

    # 2.4 DANH SÁCH CÁC BẢNG, HÌNH VẼ (Dynamic Word TOC by Caption Styles)
    add_chapter_title(doc, "DANH SÁCH CÁC BẢNG, HÌNH VẼ", page_break=True, blank_lines=2)
    add_styled_paragraph(doc, "DANH SÁCH CÁC BẢNG", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, bold=True, space_before=4, space_after=6)
    p_lot = add_styled_paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, line_spacing=1.3, space_after=12)
    add_word_field(p_lot, r'TOC \t "DAU_TableCaption,1" \h \z', size_pt=13, placeholder="[Danh sách Bảng tự động]")

    add_styled_paragraph(doc, "DANH SÁCH CÁC HÌNH VẼ", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, bold=True, space_before=10, space_after=6)
    p_lof = add_styled_paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, line_spacing=1.3)
    add_word_field(p_lof, r'TOC \t "DAU_FigureCaption,1" \h \z', size_pt=13, placeholder="[Danh sách Hình vẽ tự động]")

    # 2.5 DANH SÁCH CÁC KÝ HIỆU, CHỮ VIẾT TẮT
    add_chapter_title(doc, "DANH SÁCH CÁC KÝ HIỆU, CHỮ VIẾT TẮT", page_break=True, blank_lines=2)
    add_styled_paragraph(doc, "1. Danh sách các ký hiệu", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, bold=True, space_after=6)
    add_styled_table(
        doc,
        [("Ký hiệu", "Ý nghĩa và đơn vị / phạm vi biểu diễn")] + SYMBOLS_DATA,
        col_widths_cm=[4.2, 11.8], font_size=12, center_cols=(0,)
    )

    add_styled_paragraph(doc, "2. Danh sách các chữ viết tắt", align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=13, bold=True, space_before=10, space_after=6)
    abbr_rows = []
    t_abbr = src.tables[1]
    for r in t_abbr.rows:
        abbr_rows.append((r.cells[0].text.strip(), r.cells[1].text.strip()))
    add_styled_table(doc, abbr_rows, col_widths_cm=[4.2, 11.8], font_size=12, center_cols=(0,))

    # --------------------------------------------------------------------------
    # SECTION 3: NỘI DUNG CHÍNH (Đánh số trang Ả Rập: 1, 2, 3... từ MỞ ĐẦU)
    # --------------------------------------------------------------------------
    sec3 = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_page_layout(sec3, pg_fmt="decimal", pg_start=1)
    configure_main_header_footer(sec3)

    body = src.element.body
    p_idx_map = {p._element: i for i, p in enumerate(src.paragraphs)}
    t_idx_map = {t._element: i for i, t in enumerate(src.tables)}

    # Collect body elements from B111 (MỞ ĐẦU) to B347 (end of TÀI LIỆU THAM KHẢO)
    body_children = list(body)
    start_bi = next(idx for idx, el in enumerate(body_children) if el.tag.endswith("}p") and p_idx_map[el] == 109)  # P109 MỞ ĐẦU
    end_bi = next(idx for idx, el in enumerate(body_children) if el.tag.endswith("}p") and p_idx_map[el] == 334)   # P334 PHỤ LỤC (stop before!)

    # Define column widths (sum = 16.0 cm) for each source table index (T3..T13)
    table_widths = {
        3: [4.5, 11.5],                      # Bảng 2.1
        4: [1.3, 8.2, 1.8, 1.3, 1.4, 2.0],   # Bảng 2.2 Product Backlog
        5: [4.0, 12.0],                      # Bảng 2.3 UC01
        6: [4.0, 12.0],                      # Bảng 2.4 UC02
        7: [4.0, 12.0],                      # Bảng 2.5 UC03
        8: [4.0, 12.0],                      # Bảng 2.6 UC04
        9: [4.0, 12.0],                      # Bảng 2.7 UC05
        10: [2.8, 2.2, 6.2, 4.8],            # Bảng 2.8 ERD 3NF
        12: [4.8, 4.2, 7.0],                 # Bảng 2.9 REST API
        13: [4.6, 5.2, 6.2],                 # Bảng 3.1
    }

    i = start_bi
    pending_img = None
    first_section_in_main = True

    while i < end_bi:
        el = body_children[i]
        tag = el.tag.split("}")[-1]

        if tag == "tbl":
            ti = t_idx_map[el]
            tbl_obj = src.tables[ti]

            # Table 2 is the 78% Perspective Anchor Formula block
            if ti == 2:
                raw_txt = tbl_obj.rows[0].cells[0].text.strip()
                add_formula_block(doc, raw_txt.splitlines(), "1.1")
                i += 1
                continue

            # Table 11 is the Folder Structure tree block
            if ti == 11:
                add_code_tree_block(doc, tbl_obj.rows[0].cells[0].text)
                i += 1
                continue

            # Regular data tables (T3..T10, T12, T13): look ahead 1 element to grab its caption!
            next_el = body_children[i + 1] if (i + 1) < end_bi else None
            caption_text = None
            if next_el is not None and next_el.tag.endswith("}p"):
                np = src.paragraphs[p_idx_map[next_el]]
                if np.text.strip().startswith("Bảng "):
                    caption_text = np.text.strip()
                    i += 1  # consume caption below table and place ABOVE table!

            if caption_text:
                lbl, cap_body = parse_caption_text(caption_text, is_table=True)
                add_caption(doc, lbl, cap_body, is_table=True)

            rows_data = [[c.text.strip() for c in r.cells] for r in tbl_obj.rows]
            fsize = 10.5 if ti in (4, 10, 12) else 11.5
            ccols = (0, 2, 3, 4, 5) if ti == 4 else ((0,) if ti in (10,) else ())
            add_styled_table(
                doc, rows_data,
                col_widths_cm=table_widths.get(ti),
                font_size=fsize, center_cols=ccols
            )
            i += 1
            continue

        elif tag == "p":
            pi = p_idx_map[el]
            sp = src.paragraphs[pi]
            txt = sp.text.strip()
            sname = sp.style.name if sp.style else ""

            # Skip P112 (already moved to LỜI NÓI ĐẦU & updated to DAU)
            if pi == 112:
                i += 1
                continue

            # Handle Headings
            if sname == "Heading 1" or txt in ("MỞ ĐẦU", "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", "TÀI LIỆU THAM KHẢO") or txt.startswith("CHƯƠNG "):
                if txt == "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN":
                    h1_txt = "KẾT LUẬN"
                else:
                    h1_txt = clean_and_remap_text(txt)
                add_chapter_title(doc, h1_txt, page_break=(not first_section_in_main), blank_lines=2)
                first_section_in_main = False
                i += 1
                continue

            if sname == "Heading 2":
                add_heading_2(doc, clean_and_remap_text(txt))
                i += 1
                continue

            if sname == "Heading 3":
                add_heading_3(doc, clean_and_remap_text(txt))
                i += 1
                continue

            # Image paragraph
            img_info = extract_paragraph_image_info(sp)
            if img_info is not None:
                blob, ext = img_info
                add_picture_fit(doc, blob, ext)
                i += 1
                continue

            # Figure Caption paragraph
            if txt.startswith("Hình "):
                # Special fix: Hình 16 in source report lost its image — inject actual annotated room image before caption!
                if txt.startswith("Hình 16") and os.path.exists(FIG16_FALLBACK):
                    with open(FIG16_FALLBACK, "rb") as f:
                        add_picture_fit(doc, f.read(), None)
                lbl, cap_body = parse_caption_text(txt, is_table=False)
                add_caption(doc, lbl, cap_body, is_table=False)
                i += 1
                continue

            # Skip trailing blank paragraphs before chapter page breaks
            if not txt:
                i += 1
                continue

            is_list = (sname == "List Paragraph") or txt.startswith("•")
            is_ref = bool(re.match(r"^\[\d+\]", txt))
            add_formatted_source_paragraph(doc, sp, size_pt=13, line_spacing=1.3, is_list=is_list, is_ref=is_ref)
            i += 1
            continue

        i += 1

    # --------------------------------------------------------------------------
    # SECTION 4: PHỤ LỤC (Font 12pt, Footer "Phụ lục ... <số trang>")
    # --------------------------------------------------------------------------
    sec4 = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_page_layout(sec4, pg_fmt="decimal", pg_start=1)
    configure_appendix_footer(sec4)

    add_chapter_title(doc, "PHỤ LỤC 1", page_break=False, blank_lines=2)
    add_styled_paragraph(
        doc, "ĐƯỜNG DẪN TRUY CẬP HỆ THỐNG TRỰC TUYẾN (SINGLE-PORT DEPLOYMENT)",
        align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=12, bold=True, space_after=6
    )
    for pi in (336, 337, 338):
        add_formatted_source_paragraph(doc, src.paragraphs[pi], size_pt=12, line_spacing=1.3, is_list=True)

    add_chapter_title(doc, "PHỤ LỤC 2", page_break=True, blank_lines=2)
    add_styled_paragraph(
        doc, "DANH SÁCH TÀI KHOẢN KIỂM THỬ HỆ THỐNG (RBAC)",
        align=WD_ALIGN_PARAGRAPH.LEFT, size_pt=12, bold=True, space_after=6
    )
    add_caption(doc, "Bảng PL2.1:", "Danh sách tài khoản kiểm thử và phạm vi phân quyền hệ thống CineSight", is_table=True)
    t_app = src.tables[14]
    app_rows = [[c.text.strip() for c in r.cells] for r in t_app.rows]
    add_styled_table(doc, app_rows, col_widths_cm=[3.6, 3.0, 2.8, 6.6], font_size=11.5, center_cols=(1, 2))

    os.makedirs(os.path.dirname(OUT_DOCX), exist_ok=True)
    doc.save(OUT_DOCX)
    print(f"SUCCESS: Generated {OUT_DOCX}")


if __name__ == "__main__":
    build_thesis()
