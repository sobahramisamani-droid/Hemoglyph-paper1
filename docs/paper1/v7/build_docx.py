import os
"""Build the CMPB manuscript .docx from the R8 markdown (Elsevier format: A4, 2.5 cm, Times New Roman 12, double spacing,
numbered sections, continuous line numbers, page numbers, editable tables, figures with legends at the end)."""
import re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx_style import setup_document, inline, add_table, heading

import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else "Paper1_Hemoglyph_CMPB_EN_v7_R9.md"
PKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "Paper1_submission_package")
OUT = sys.argv[2] if len(sys.argv) > 2 else (os.path.join(PKG, "Manuscript_Paper1_Hemoglyph_CMPB_R9.docx") if os.path.isdir(PKG) else SRC.replace(".md", ".docx"))
doc = Document(); setup_document(doc)
TEXT = open(SRC, encoding="utf-8").read()
# Supplementary Notes kept at the end of the markdown source are built into the separate Supplementary Information file; the manuscript stops before them.
MAIN, SUPP = TEXT.split("\n## Supplementary information", 1)
lines = (MAIN + "\n## Supplementary information\n\n" + SUPP.split("\n### Supplementary Note 9", 1)[0].strip() + "\n").split("\n"); i = 0
in_refs = False
while i < len(lines):
    l = lines[i]
    if l.startswith("# "):
        p = doc.add_paragraph(); inline(p, l[2:], 16); p.runs[0].bold = True; p.paragraph_format.line_spacing = 1.3; p.paragraph_format.space_after = Pt(12)
    elif l.startswith("## "):
        in_refs = l[3:].strip().lower().startswith("references")
        heading(doc, l[3:], 1)
    elif l.startswith("### "): heading(doc, l[4:], 2)
    elif l.startswith("#### "): heading(doc, l[5:], 3)
    elif l.startswith("##### "): heading(doc, l[6:], 3)
    elif l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
        add_table(doc, rows, 9); doc.add_paragraph(); continue
    elif l.strip() == "": pass
    elif re.match(r"^- ", l):
        p = doc.add_paragraph(style="List Bullet"); inline(p, l[2:]); p.paragraph_format.line_spacing = 1.5; p.paragraph_format.space_after = Pt(2)
    elif in_refs and re.match(r"^(\d+\. |\[\d+\] )", l):
        p = doc.add_paragraph(); inline(p, l, 11); p.paragraph_format.line_spacing = 1.5; p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Cm(0.8); p.paragraph_format.first_line_indent = Cm(-0.8)
    elif l.startswith("**Table "):
        p = doc.add_paragraph(); inline(p, l, 11); p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.5
    elif l.startswith("**Fig. ") and "|" in l:
        m = re.match(r"\*\*Fig\. (\d+) \| ([^*]+)\*\*(.*)", l)
        p = doc.add_paragraph(); r = p.add_run(f"Fig. {m.group(1)}. "); r.bold = True; r.font.size = Pt(11)
        inline(p, "**" + m.group(2).strip() + "**" + m.group(3), 11); p.paragraph_format.line_spacing = 1.5
    else:
        p = doc.add_paragraph(); inline(p, l); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    i += 1
doc.add_page_break(); heading(doc, "Figures", 1)
LEG = {}
for l in lines:
    m = re.match(r"\*\*Fig\. (\d+) \| ([^*]+)\*\*(.*)", l)
    if m: LEG[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())
for k in range(1, 9):
    pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER; pic.add_run().add_picture(f"fig/Figure_{k}.png", width=Cm(16))
    p = doc.add_paragraph(); r = p.add_run(f"Fig. {k}. "); r.bold = True; r.font.size = Pt(10)
    inline(p, "**" + LEG[k][0] + "** " + LEG[k][1], 10); p.paragraph_format.line_spacing = 1.15
    if k < 8: doc.add_page_break()
doc.save(OUT); print("docx ok")
