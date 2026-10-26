# -*- coding: utf-8 -*-
"""Render Paper 1 v5.3 (EN): numbers.py -> tables_en.py/text_en.py -> Markdown + DOCX (+ supplement docx).

    python3 docs/paper1/v53/extract_numbers.py && python3 docs/paper1/v53/render.py
Outputs: docs/paper1/Paper1_Hemoglyph_npj_EN.md / .docx and docs/paper1/Paper1_Supplement_EN.docx
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tables_en as T
import text_en as X
from md_to_docx import md_to_docx

main_tables = "\n\n".join(f() for f in T.ALL_MAIN)
supp_tables = "\n\n".join(f() for f in T.ALL_SUPP)
RESULTS = X.results()

doc = f"""# {X.TITLE}

{X.AUTHORS}

## Abstract
{X.ABSTRACT}

{X.INTRO}

{RESULTS}

{X.DISCUSSION}

{X.METHODS}

{X.BACK}

## Tables

{main_tables}

## Supplementary information

Supplementary File 1 — Statistical analysis plan with Amendments 1–13 (Amendment 13 = post-hoc Sepsis-2019 re-analysis, Supplementary Table S12) (`supplement/SAP_Hemoglyph_v1.md`). Supplementary File 2 — Disclosure and limitations statement. Supplementary File 3 — TRIPOD+AI checklist. Supplementary File 4 — Input schema (`INPUT_SCHEMA_v1.md`). Supplementary Note S11 — Protocol of the planned clinical-use evaluation (multi-reader crossover study and silent prospective run; `docs/paper2/READER_STUDY_PROTOCOL_v0.1.md`). Supplementary Data 1 — Knowledge-source inventory with per-source verification status (XLSX).

{supp_tables}
"""

out_md = os.path.join(HERE, "..", "Paper1_Hemoglyph_npj_EN.md")
open(out_md, "w", encoding="utf-8").write(doc)
words = len((X.INTRO + RESULTS + X.DISCUSSION).split()); mw = len(X.METHODS.split())
print("wrote", os.path.abspath(out_md), "| main text (Intro+Results+Discussion, npj limit 4000) =", words, "| Methods =", mw, "| abstract words", len(X.ABSTRACT.split()))

figdir = os.path.join(HERE, "..", "figures")
FIGS = {"1": "fig1_architecture.png", "2": "fig2_auroc_forest.png", "3": "fig3_eicu_baselines.png", "4": "fig4_calibration_dca.png",
        "5": "fig5_llm_comparison.png", "6": "fig6_audit_nexttest.png", "S1": "figS1_participant_flow.png", "S2": "figS2_synthetic.png"}
main_doc = doc.split("## Supplementary information")[0]
supp_doc = "# Supplementary information — " + X.TITLE + "\n\n" + doc.split("## Supplementary information")[1]
md_to_docx(main_doc, os.path.join(HERE, "..", "Paper1_Hemoglyph_npj_EN.docx"), figdir=figdir, fig_map=FIGS)
md_to_docx(supp_doc, os.path.join(HERE, "..", "Paper1_Supplement_EN.docx"), figdir=figdir, fig_map=FIGS, double_space=False)
print("wrote docx (main + supplement)")
