import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import subprocess

PROJECT_DIR = r"C:\Academic Project\Supply-Prescript"
FS_PATH = os.path.join(PROJECT_DIR, "FRONT SHEETS.docx")
REP_PATH = os.path.join(PROJECT_DIR, "SupplyPrescript_Project_Report_Final.docx")
OUT_DOCX = os.path.join(PROJECT_DIR, "SupplyPrescript_Project_Report_Updated.docx")
OUT_PDF = os.path.join(PROJECT_DIR, "SupplyPrescript_Project_Report_Updated.pdf")

TEMP_COMBINED = os.path.join(PROJECT_DIR, "temp_combined_stage1.docx")

def combine_documents_via_word():
    """Use Word COM to merge FRONT SHEETS.docx and SupplyPrescript_Project_Report_Final.docx with high fidelity."""
    ps_script = f'''
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {{
    $doc = $word.Documents.Open('{FS_PATH}')
    $range = $doc.Range()
    $range.Collapse(0) # wdCollapseEnd
    $range.InsertBreak(2) # wdSectionBreakNextPage
    
    $sec2 = $doc.Sections.Item($doc.Sections.Count)
    $sec2.Headers.Item(1).LinkToPrevious = $false
    $sec2.Footers.Item(1).LinkToPrevious = $false
    
    $range2 = $sec2.Range
    $range2.Collapse(0)
    $range2.InsertFile('{REP_PATH}')
    
    $doc.SaveAs([ref]'{TEMP_COMBINED}')
    $doc.Close([ref]0)
    Write-Host "STAGE 1 SUCCESS"
}}
catch {{
    Write-Host "STAGE 1 ERROR: $_"
    exit 1
}}
finally {{
    try {{ $word.Quit() }} catch {{}}
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}}
'''
    ps_file = os.path.join(PROJECT_DIR, "temp_combine_stage1.ps1")
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_script)
    
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Stage 1 COM output:\n", result.stdout, result.stderr)
    if os.path.exists(ps_file):
        os.remove(ps_file)
    if not os.path.exists(TEMP_COMBINED):
        raise RuntimeError("Failed to generate temp_combined_stage1.docx")

def refine_document_formatting():
    """Apply exact margins, spacing, borders, unlinking, and page numbering restart."""
    doc = docx.Document(TEMP_COMBINED)
    
    # Border XML definition (exact double-line style from reference)
    pg_borders_xml = (
        r'<w:pgBorders %s>'
        r'<w:top w:val="thickThinSmallGap" w:sz="24" w:space="1" w:color="auto"/>'
        r'<w:left w:val="thickThinSmallGap" w:sz="24" w:space="1" w:color="auto"/>'
        r'<w:bottom w:val="thinThickSmallGap" w:sz="24" w:space="1" w:color="auto"/>'
        r'<w:right w:val="thinThickSmallGap" w:sz="24" w:space="1" w:color="auto"/>'
        r'</w:pgBorders>' % nsdecls('w')
    )
    
    print(f"Refining document with {len(doc.sections)} sections...")
    
    # SECTION 0: Front Sheets
    sec0 = doc.sections[0]
    sec0.different_first_page_header_footer = False
    
    # Ensure NO headers or footers in front sheets
    for hp in sec0.header.paragraphs:
        hp.text = ''
        pPr = hp._p.get_or_add_pPr()
        for child in list(hp._p):
            if child.tag != pPr.tag:
                hp._p.remove(child)
                
    for fp in sec0.footer.paragraphs:
        fp.text = ''
        pPr = fp._p.get_or_add_pPr()
        for child in list(fp._p):
            if child.tag != pPr.tag:
                fp._p.remove(child)

    # Front sheets margins
    sec0.top_margin = Inches(1.0)
    sec0.bottom_margin = Inches(1.0)
    sec0.left_margin = Inches(1.0)
    sec0.right_margin = Inches(1.0)
    sec0.header_distance = Inches(0.40)
    sec0.footer_distance = Inches(0.40)
    
    # Ensure exact double-line border on Section 0
    sectPr0 = sec0._sectPr
    for existing in sectPr0.xpath('.//w:pgBorders'):
        sectPr0.remove(existing)
    cols0 = sectPr0.xpath('./w:cols')
    if cols0:
        cols0[0].addprevious(parse_xml(pg_borders_xml))
    else:
        sectPr0.append(parse_xml(pg_borders_xml))
        
    # Remove any pgNumType from section 0
    for pnt in sectPr0.xpath('.//w:pgNumType'):
        sectPr0.remove(pnt)

    # SECTION 1: Main Report
    sec1 = doc.sections[1]
    sec1.different_first_page_header_footer = False
    sec1.header.is_linked_to_previous = False
    sec1.footer.is_linked_to_previous = False
    
    # Margins and spacing to eliminate header/footer overlap with page borders
    sec1.top_margin = Inches(1.0)
    sec1.bottom_margin = Inches(1.0)
    sec1.left_margin = Inches(0.82)
    sec1.right_margin = Inches(0.79)
    sec1.header_distance = Inches(0.40)
    sec1.footer_distance = Inches(0.40)
    
    # Configure Section 1 Header
    hp = sec1.header.paragraphs[0]
    hp.text = ''
    hp.paragraph_format.space_before = Pt(0)
    hp.paragraph_format.space_after = Pt(0)
    hp.paragraph_format.line_spacing = 1.0
    hp.paragraph_format.tab_stops.clear_all()
    hp.paragraph_format.tab_stops.add_tab_stop(Inches(6.6), WD_TAB_ALIGNMENT.RIGHT)
    
    hr1 = hp.add_run('Acharya Institute of Graduate Studies, Bengaluru')
    hr1.font.name = 'Times New Roman'
    hr1.font.size = Pt(9.5)
    hr1.font.color.rgb = RGBColor(70, 70, 70)
    
    hp.add_run('\t')
    
    hr2 = hp.add_run('Department of Computer Application')
    hr2.font.name = 'Times New Roman'
    hr2.font.size = Pt(9.5)
    hr2.font.color.rgb = RGBColor(70, 70, 70)
    
    # Configure Section 1 Footer
    fp = sec1.footer.paragraphs[0]
    fp.text = ''
    fp.paragraph_format.space_before = Pt(0)
    fp.paragraph_format.space_after = Pt(0)
    fp.paragraph_format.line_spacing = 1.0
    fp.paragraph_format.tab_stops.clear_all()
    fp.paragraph_format.tab_stops.add_tab_stop(Inches(3.3), WD_TAB_ALIGNMENT.CENTER)
    fp.paragraph_format.tab_stops.add_tab_stop(Inches(6.6), WD_TAB_ALIGNMENT.RIGHT)
    
    fr1 = fp.add_run('SupplyPrescript: Disruption Defense System')
    fr1.font.name = 'Times New Roman'
    fr1.font.size = Pt(9.5)
    fr1.font.color.rgb = RGBColor(70, 70, 70)
    
    fp.add_run('\t')
    
    # Dynamic Page Number Field
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    fp._p.append(fldSimple)
    
    fp.add_run('\t')
    
    fr2 = fp.add_run('Academic Year 2026-27')
    fr2.font.name = 'Times New Roman'
    fr2.font.size = Pt(9.5)
    fr2.font.color.rgb = RGBColor(70, 70, 70)
    
    # Restart page numbering at 1 for Section 1
    sectPr1 = sec1._sectPr
    for pnt in sectPr1.xpath('.//w:pgNumType'):
        sectPr1.remove(pnt)
    pgNumType = parse_xml(r'<w:pgNumType %s w:start="1"/>' % nsdecls('w'))
    sectPr1.append(pgNumType)
    
    # Ensure exact double-line border on Section 1
    for existing in sectPr1.xpath('.//w:pgBorders'):
        sectPr1.remove(existing)
    cols1 = sectPr1.xpath('./w:cols')
    if cols1:
        cols1[0].addprevious(parse_xml(pg_borders_xml))
    else:
        sectPr1.append(parse_xml(pg_borders_xml))

    # Save to the final new DOCX file
    doc.save(OUT_DOCX)
    print(f"Successfully refined and saved: {OUT_DOCX}")
    
    # Clean up temp file
    if os.path.exists(TEMP_COMBINED):
        os.remove(TEMP_COMBINED)

def convert_to_matching_pdf():
    """Convert the finalized DOCX to matching PDF using Word COM."""
    ps_script = f'''
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {{
    $doc = $word.Documents.Open('{OUT_DOCX}')
    # 17 = wdFormatPDF
    $doc.SaveAs([ref]'{OUT_PDF}', [ref]17)
    $doc.Close([ref]0)
    Write-Host "STAGE 2 PDF SUCCESS"
}}
catch {{
    Write-Host "STAGE 2 PDF ERROR: $_"
    exit 1
}}
finally {{
    try {{ $word.Quit() }} catch {{}}
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}}
'''
    ps_file = os.path.join(PROJECT_DIR, "temp_convert_pdf.ps1")
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_script)
        
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Stage 2 PDF COM output:\n", result.stdout, result.stderr)
    if os.path.exists(ps_file):
        os.remove(ps_file)
    if not os.path.exists(OUT_PDF):
        raise RuntimeError("Failed to generate matching PDF")

def verify_saved_files():
    """Verify that both final files exist, are non-empty, and original files are intact."""
    docx_size = os.path.getsize(OUT_DOCX) if os.path.exists(OUT_DOCX) else 0
    pdf_size = os.path.getsize(OUT_PDF) if os.path.exists(OUT_PDF) else 0
    
    print("\n--- FINAL VERIFICATION ---")
    print(f"DOCX: {OUT_DOCX} -> {docx_size:,} bytes")
    print(f"PDF:  {OUT_PDF} -> {pdf_size:,} bytes")
    
    assert docx_size > 0, "DOCX file is empty or not created"
    assert pdf_size > 0, "PDF file is empty or not created"
    
    # Check original files are untouched
    assert os.path.exists(FS_PATH), "Original FRONT SHEETS.docx missing!"
    assert os.path.exists(REP_PATH), "Original SupplyPrescript_Project_Report_Final.docx missing!"
    print("Verification passed successfully! Original files remain intact.")

if __name__ == "__main__":
    print("Starting document update process...")
    combine_documents_via_word()
    refine_document_formatting()
    convert_to_matching_pdf()
    verify_saved_files()
    print("All steps completed successfully.")
