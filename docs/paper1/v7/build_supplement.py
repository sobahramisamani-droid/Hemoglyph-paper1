"""Assemble the single Supplementary Information file for the CMPB submission (R6).

Order: cover/index · Note 1 SAP · Note 2 LLM protocol · Table S1 cohort flow · SUPPLEMENT_R1 (Notes 3–8, Tables S4–S16) ·
Note 8 addendum (second-rater attempts) · Notes 9–12 (from the R6 manuscript) · TRIPOD+AI checklist.
Output: submission_CMPB/Supplementary_Information_R6.{md,docx}
"""
import re, os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

V7 = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(V7, ".."))
SUP = os.path.join(P1, "supplement")
rd = lambda p: open(p, encoding="utf-8").read().strip()

man = rd(os.path.join(V7, "Paper1_Hemoglyph_CMPB_EN_v7_R6.md"))
notes_9_12 = man.split("## Supplementary information", 1)[1]
index_line = notes_9_12.split("\n\n", 2)[1]
notes_9_12 = notes_9_12.split("### Supplementary Note 9", 1)[1]
notes_9_12 = "### Supplementary Note 9" + notes_9_12

addendum = """## Supplementary Note 8 — Addendum (2026-10-27): second-rater attempts and why none is used

The protocol named a human non-clinician second rater blind to rater-1 labels. Three submissions were received and all were rejected under the protocol's validity rule (a CONCORDANT or DISCORDANT label must be supported by the verbatim source sentence containing the criterion); none is averaged into any figure in the paper.

| Round | Date | Labels (C/D/U) | Agreement with rater 1 | Reason for rejection |
|---|---|---|---|---|
| 1 (200 rules) | 2026-10-26 | templated | κ = 0.05 | verdicts without any source quotation; identical label pattern across strata |
| 2 (100 stratum-A rules) | 2026-10-27 | 72/3/25 | 26/100 raw; κ = 0.03 | the mandatory quotation field contained the guideline *title* in 70 of 72 CONCORDANT rows; one row contained a literal placeholder; attribution errors visible from the title (e.g. hepatitis A IgM cited to an EASL hepatitis E guideline) were labelled CONCORDANT |
| 2b ("revised", same rules) | 2026-10-27 | 70/5/25 | κ = 0.04 | quotations were numeric sentences paraphrasing the rule, not the source: "Hb < 10.67 g/dL" (a unit-conversion artefact of the rule), Sepsis-3 quoted as "lactate > 4.0 mmol/L" (source: > 2 mmol/L), the Atlanta classification quoted with "≥ 180 U/L" (source: 3 × ULN), sentences attributed to WHO landing pages that return no text |

All three files are archived verbatim in `eval/source_audit/` (`REJECTED_rater2_submission_2026-10-26.csv`, `REJECTED_rater2_round2_submission_2026-10-27.csv`, `REJECTED_rater2_round2b_REVISED_2026-10-27.csv`) with a written rejection note. The audit in the paper is therefore single-rater (an AI agent under the first author's direction, declared), and no inter-rater reliability is claimed. The episode is reported in the main text (Section 3.2) because it bears on the method: a human asked to verify AI-drafted rules reproduced, without opening the sources, exactly the failure the audit is designed to detect; a mandatory verbatim-quotation field with page/section is therefore part of the protocol going forward, together with a five-row spot check against sources for every rater."""

parts = [
    "# Supplementary Information\n\n*Verification and provenance auditing of an AI-drafted clinical rule base — Bahrami, Tahmasebinejad, Bahrami Samani. Revision R6 (2026-10-27), Computer Methods and Programs in Biomedicine.*\n\n**Index.** " + index_line,
    "## Supplementary Note 1 — Statistical analysis plan and amendments\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "SAP_Hemoglyph_v1.md")), flags=re.M).replace("\n## ", "\n### "),
    "## Supplementary Note 2 — LLM comparison protocol\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "LLM_COMPARISON_PROTOCOL.md")), flags=re.M).replace("\n## ", "\n### "),
    "## Supplementary Table S1/S3 — Cohort and participant flow\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "TABLE_S1_cohort_flow.md")), flags=re.M).replace("\n## ", "\n### "),
    rd(os.path.join(SUP, "SUPPLEMENT_R1.md")).split("\n", 1)[1].strip(),
    addendum,
    notes_9_12.replace("### Supplementary Note", "## Supplementary Note"),
    "## Supplementary Note 5.7 — TRIPOD+AI checklist\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "TRIPOD_AI_checklist_Hemoglyph.md")), flags=re.M).replace("\n## ", "\n### "),
]
md = "\n\n".join(parts) + "\n"
os.makedirs(os.path.join(V7, "submission_CMPB"), exist_ok=True)
open(os.path.join(V7, "submission_CMPB", "Supplementary_Information_R6.md"), "w", encoding="utf-8").write(md)

# ---------------- docx
doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(2.0)
n = doc.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(10); n.paragraph_format.line_spacing = 1.15; n.paragraph_format.space_after = Pt(4)


def inline(p, text, size=None):
    for pt in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\^[^^]+\^)", text):
        if not pt:
            continue
        if pt.startswith("**"): r = p.add_run(pt[2:-2]); r.bold = True
        elif pt.startswith("*"): r = p.add_run(pt[1:-1]); r.italic = True
        elif pt.startswith("`"): r = p.add_run(pt[1:-1]); r.font.name = "Consolas"
        elif pt.startswith("^"): r = p.add_run(pt[1:-1]); r.font.superscript = True
        else: r = p.add_run(pt)
        if size: r.font.size = Pt(size)


lines = md.split("\n"); i = 0
while i < len(lines):
    l = lines[i]
    if l.startswith("# "):
        p = doc.add_paragraph(); inline(p, l[2:], 16); p.runs[0].bold = True
    elif l.startswith("## "):
        h = doc.add_heading(l[3:], 1); h.runs[0].font.color.rgb = RGBColor(0, 0, 0)
    elif l.startswith("### "):
        h = doc.add_heading(l[4:], 2); h.runs[0].font.color.rgb = RGBColor(0x30, 0x30, 0x30)
    elif l.startswith("#### ") or l.startswith("##### "):
        h = doc.add_heading(l.lstrip("#").strip(), 3); h.runs[0].font.color.rgb = RGBColor(0x30, 0x30, 0x30)
    elif l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
        body = [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r if c)]
        hdr = rows[0]
        t = doc.add_table(rows=1 + len(body), cols=len(hdr)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r, row in enumerate([hdr] + body):
            for c, cell in enumerate((row + [""] * len(hdr))[:len(hdr)]):
                cl = t.cell(r, c); cl.text = ""; p = cl.paragraphs[0]; p.paragraph_format.space_after = Pt(0); inline(p, cell, 7.5)
                if r == 0:
                    for x in p.runs: x.bold = True
        doc.add_paragraph(); continue
    elif l.startswith("```"):
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            p = doc.add_paragraph(); r = p.add_run(lines[i]); r.font.name = "Consolas"; r.font.size = Pt(8); p.paragraph_format.space_after = Pt(0); i += 1
    elif l.strip() == "":
        pass
    elif re.match(r"^\s*[-*] ", l):
        p = doc.add_paragraph(style="List Bullet"); inline(p, re.sub(r"^\s*[-*] ", "", l))
    else:
        p = doc.add_paragraph(); inline(p, l)
    i += 1
out = os.path.join(V7, "submission_CMPB", "Supplementary_Information_R6.docx")
doc.save(out)
print("supplement ok:", out, "| words", len(md.split()))
