# -*- coding: utf-8 -*-
"""Minimal Markdown -> .docx renderer used for the manuscript, supplement, cover letter and the Persian version.

    md_to_docx(md_text, out_path, figdir=None, fig_map=None, rtl=False, font=None)

Supports: # / ## / ### headings, paragraphs, **bold**, *italic*, pipe tables, numbered references,
figure captions (a caption line that starts with **Fig. N |** inserts figures/<fig_map[N]>.png above it).
rtl=True sets right-to-left paragraph direction and bidi runs (Persian/Arabic manuscripts) and uses `font`
(default Vazirmatn, falling back to the system default if the font is not installed on the reader's machine).
"""
import os, re
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def _set_rtl(paragraph, on=True):
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi"); bidi.set(qn("w:val"), "1" if on else "0"); pPr.append(bidi)


def _run_rtl(run, font):
    rPr = run._r.get_or_add_rPr()
    rtl = OxmlElement("w:rtl"); rtl.set(qn("w:val"), "1"); rPr.append(rtl)
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts"); rPr.append(rFonts)
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(k), font)


def md_to_docx(md, out_path, figdir=None, fig_map=None, rtl=False, font=None, base_size=12, double_space=True, line_numbers=True):
    font = font or ("Vazirmatn" if rtl else "Times New Roman")
    fig_map = fig_map or {}
    d = Document()
    s = d.styles["Normal"]; s.font.name = font; s.font.size = Pt(base_size)
    s.element.rPr.rFonts.set(qn("w:eastAsia"), font); s.element.rPr.rFonts.set(qn("w:cs"), font)
    s.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE if double_space else WD_LINE_SPACING.ONE_POINT_FIVE
    s.paragraph_format.space_after = Pt(0)
    for name, size in (("Title", 16), ("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)):
        h = d.styles[name]; h.font.name = font; h.font.size = Pt(size); h.font.bold = True
        h.font.color.rgb = RGBColor(0, 0, 0); h.element.rPr.rFonts.set(qn("w:eastAsia"), font); h.element.rPr.rFonts.set(qn("w:cs"), font)
        h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        if name == "Heading 3": h.font.italic = True
    for sec in d.sections:
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2.5)
        if line_numbers:
            ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous"); sec._sectPr.append(ln)
        if rtl:
            bidi = OxmlElement("w:bidi"); sec._sectPr.append(bidi)
        fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run(); f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
        f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end"); r._r.append(f1); r._r.append(it); r._r.append(f2)

    def add_rich(p, text, size=None):
        for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text):
            if not part: continue
            if part.startswith("**"): run = p.add_run(part[2:-2]); run.bold = True
            elif part.startswith("`"): run = p.add_run(part[1:-1]); run.font.name = "Consolas"
            elif part.startswith("*") and part.endswith("*") and len(part) > 2: run = p.add_run(part[1:-1]); run.italic = True
            else: run = p.add_run(part)
            if size: run.font.size = Pt(size)
            if rtl: _run_rtl(run, font)

    def para(text, size=None, single=False, align=None):
        p = d.add_paragraph(); add_rich(p, text, size)
        if single: p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; p.paragraph_format.space_after = Pt(6)
        if rtl: _set_rtl(p); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif align is not None: p.alignment = align
        return p

    md = re.sub(r"(?m)^(#{1,3} [^\n]*)\n(?!\n)", r"\1\n\n", md)
    for block in md.split("\n\n"):
        b = block.strip()
        if not b: continue
        if b.startswith("|"):
            rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in b.splitlines()
                    if ln.strip().startswith("|") and not set(ln.replace("|", "").strip()) <= set("-: ")]
            if not rows: continue
            ncol = max(len(r) for r in rows)
            t = d.add_table(rows=len(rows), cols=ncol); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
            if rtl:
                tblPr = t._tbl.tblPr; bv = OxmlElement("w:bidiVisual"); tblPr.append(bv)
            for i, r in enumerate(rows):
                for j in range(ncol):
                    c = r[j] if j < len(r) else ""
                    cell = t.cell(i, j); cell.text = ""; p = cell.paragraphs[0]
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    add_rich(p, c, size=8.5 if ncol > 5 else 9)
                    if i == 0:
                        for run in p.runs: run.bold = True
                    if rtl: _set_rtl(p); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            d.add_paragraph(); continue
        if b.startswith("# "):
            h = d.add_heading(b[2:], 0)
            if rtl: _set_rtl(h); h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            continue
        if b.startswith("## "):
            h = d.add_heading(b[3:], 1)
            if rtl: _set_rtl(h); h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            continue
        if b.startswith("### "):
            h = d.add_heading(b[4:], 2)
            if rtl: _set_rtl(h); h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            continue
        lines = b.splitlines() if b.startswith(("**Fig", "**Table", "**Supplementary", "**شکل", "**جدول", "- ", "* ")) else [b]
        for line in lines:
            m = re.match(r"\*\*(?:Supplementary )?(?:Fig\.|شکل) (S?[\d۰-۹]+)", line)
            if m and figdir and fig_map.get(m.group(1)) and os.path.exists(os.path.join(figdir, fig_map[m.group(1)])):
                d.add_picture(os.path.join(figdir, fig_map[m.group(1)]), width=Inches(6.3))
                d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if line.startswith(("- ", "* ")):
                p = para(line[2:], single=True); p.paragraph_format.left_indent = Cm(0.6)
                p.paragraph_format.first_line_indent = Cm(-0.4); continue
            is_caption = bool(m) or line.startswith(("**Table", "**Supplementary Table", "**جدول"))
            is_ref = bool(re.match(r"^\d+\. ", line))
            para(line, size=10 if is_caption else None, single=is_caption or is_ref)
    d.save(out_path)
    return out_path
