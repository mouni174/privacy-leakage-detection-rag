import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import shutil

INPUT_PATH = r"c:\Users\tmoun\Downloads\IEEE FORMATE RESEARCH PAPER (1).docx"
OUTPUT_PATH = r"c:\Users\tmoun\Downloads\IEEE_FORMATE_RESEARCH_PAPER_Revised.docx"

doc = docx.Document(INPUT_PATH)

print(f"Loaded {INPUT_PATH}")
print(f"Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}")

# Helper to format table cells in IEEE style
def style_table(table):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row_idx, row in enumerate(table.rows):
        for cell in row.cells:
            # Subtle cell padding
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = OxmlElement('w:tcMar')
            for m in ['top', 'bottom', 'left', 'right']:
                node = OxmlElement(f'w:{m}')
                node.set(qn('w:w'), '100')
                node.set(qn('w:type'), 'dxa')
                tcMar.append(node)
            tcPr.append(tcMar)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(8.5)
                    if row_idx == 0:
                        r.font.bold = True

print("Helper defined.")
