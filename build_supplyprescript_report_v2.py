import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

from report_chapters.ch1_intro import add_chapter_1
from report_chapters.ch2_analysis import add_chapter_2
from report_chapters.ch3_design import add_chapter_3
from report_chapters.ch4_testing import add_chapter_4
from report_chapters.ch5_implementation import add_chapter_5
from report_chapters.ch6_maintenance import add_chapter_6
from report_chapters.ch7_future import add_chapter_7
from report_chapters.ch8_conclusion import add_chapter_8
from report_chapters.ch9_appendix import add_chapter_9
from report_chapters.ch10_bibliography import add_chapter_10

OUTPUT_PATH = r"C:\Academic Project\Supply-Prescript\SupplyPrescript_Project_Report.docx"
ASSETS_DIR = r"C:\Academic Project\Supply-Prescript\scratch_report_assets"

# Initialize Document
doc = docx.Document()

# 1. Page Setup (A4, matching reference margins exactly)
for sec in doc.sections:
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    sec.top_margin = Inches(0.67)
    sec.bottom_margin = Inches(0.83)
    sec.left_margin = Inches(0.82)
    sec.right_margin = Inches(0.79)
    sec.header_distance = Inches(0.79)
    sec.footer_distance = Inches(0.83)

def style_header_footer(sec):
    # Header
    sec.header.is_linked_to_previous = False
    hp = sec.header.paragraphs[0]
    hp.text = ''
    hp.paragraph_format.tab_stops.add_tab_stop(Inches(6.6), WD_TAB_ALIGNMENT.RIGHT)
    hr1 = hp.add_run('Acharya Institute of Graduate Studies, Bengaluru')
    hr1.font.name = 'Times New Roman'
    hr1.font.size = Pt(9.5)
    hr1.font.color.rgb = RGBColor(70, 70, 70)
    
    hr_tab = hp.add_run('\t')
    
    hr2 = hp.add_run('Department of Computer Application')
    hr2.font.name = 'Times New Roman'
    hr2.font.size = Pt(9.5)
    hr2.font.color.rgb = RGBColor(70, 70, 70)
    
    # Footer
    sec.footer.is_linked_to_previous = False
    fp = sec.footer.paragraphs[0]
    fp.text = ''
    fp.paragraph_format.tab_stops.add_tab_stop(Inches(3.3), WD_TAB_ALIGNMENT.CENTER)
    fp.paragraph_format.tab_stops.add_tab_stop(Inches(6.6), WD_TAB_ALIGNMENT.RIGHT)
    
    fr1 = fp.add_run('SupplyPrescript: Disruption Defense System')
    fr1.font.name = 'Times New Roman'
    fr1.font.size = Pt(9.5)
    fr1.font.color.rgb = RGBColor(70, 70, 70)
    
    fr_tab1 = fp.add_run('\t')
    
    # Dynamic Page Number Field
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    fp._p.append(fldSimple)
    
    fr_tab2 = fp.add_run('\t')
    fr2 = fp.add_run('Academic Year 2026-27')
    fr2.font.name = 'Times New Roman'
    fr2.font.size = Pt(9.5)
    fr2.font.color.rgb = RGBColor(70, 70, 70)

style_header_footer(doc.sections[0])

# Formatting helpers
def add_chapter_cover(title):
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(140)
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(24)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.space_after = Pt(200)
    
    doc.add_page_break()

def add_chapter_title(title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(14)

def add_heading_14(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)

def add_heading_12(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)

def add_body(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)

def add_bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(4)

def add_code_block(code_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(code_text)
    r.font.name = 'Courier New'
    r.font.size = Pt(9.0)
    r.font.color.rgb = RGBColor(30, 30, 30)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    shd = parse_xml(r'<w:shd %s w:fill="F4F4F6"/>' % nsdecls('w'))
    pPr.append(shd)

def add_image_figure(image_path, caption_text, width_inches=6.0):
    if os.path.exists(image_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(image_path, width=Inches(width_inches))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run(caption_text)
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(11)
        r_cap.font.bold = True
        p_cap.paragraph_format.space_after = Pt(12)
    else:
        print(f"Warning: Image file not found: {image_path}")

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(r'<w:tcMar %s><w:top w:w="%d" w:type="dxa"/><w:bottom w:w="%d" w:type="dxa"/><w:left w:w="%d" w:type="dxa"/><w:right w:w="%d" w:type="dxa"/></w:tcMar>' % (nsdecls('w'), top, bottom, left, right))
    tcPr.append(tcMar)

def set_table_borders(table):
    tblPr = table._element.xpath('w:tblPr')[0]
    borders = parse_xml(
        r'<w:tblBorders %s>'
        r'<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        r'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        r'<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        r'<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        r'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        r'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        r'</w:tblBorders>' % nsdecls('w')
    )
    tblPr.append(borders)

def format_custom_table(table_data, col_widths, is_compact=False):
    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    
    for row_idx, row in enumerate(table.rows):
        is_header = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.width = Inches(col_widths[col_idx])
            set_cell_margins(cell, top=75 if is_compact else 110, bottom=75 if is_compact else 110, left=90, right=90)
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(2)
            
            r = p.add_run(table_data[row_idx][col_idx])
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.0 if is_compact else 10.5)
            r.font.bold = is_header
            
            if is_header:
                tcPr = cell._tc.get_or_add_tcPr()
                shd = parse_xml(r'<w:shd %s w:fill="EDEDED"/>' % nsdecls('w'))
                tcPr.append(shd)
                
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(2)
    p_sp.paragraph_format.space_after = Pt(6)

h = {
    'add_chapter_cover': add_chapter_cover,
    'add_chapter_title': add_chapter_title,
    'add_heading_14': add_heading_14,
    'add_heading_12': add_heading_12,
    'add_body': add_body,
    'add_bullet': add_bullet,
    'add_code_block': add_code_block,
    'add_image_figure': add_image_figure,
    'format_custom_table': format_custom_table
}

print("Appending Chapter 1...")
add_chapter_1(doc, h)

print("Appending Chapter 2...")
add_chapter_2(doc, h)

print("Appending Chapter 3...")
add_chapter_3(doc, h)

print("Appending Chapter 4...")
add_chapter_4(doc, h)

print("Appending Chapter 5...")
add_chapter_5(doc, h)

print("Appending Chapter 6...")
add_chapter_6(doc, h)

print("Appending Chapter 7...")
add_chapter_7(doc, h)

print("Appending Chapter 8...")
add_chapter_8(doc, h)

print("Appending Chapter 9...")
add_chapter_9(doc, h)

print("Appending Chapter 10...")
add_chapter_10(doc, h)

# Save document
doc.save(OUTPUT_PATH)
print(f"Successfully generated expanded report at: {OUTPUT_PATH}")
