# CMPB submission checklist (Editorial Manager: https://submit.elsevier.com/CMPB)

| Item | File | Status |
|---|---|---|
| Cover letter (why CMPB / what is known / what this adds / not published elsewhere) | `../COVER_LETTER_CMPB.md` | ready |
| Title page, separate, single corresponding author, full postal addresses | `TITLE_PAGE.md` | **needs**: telephone, postal address, Z.T. affiliation wording, co-author ORCIDs |
| Manuscript (.docx, single column, double spaced, numbered sections, no author names in main file for blinding not required — CMPB is single-anonymised) | `../Paper1_Hemoglyph_CMPB_EN_v7_R6.docx` | ready (≈3,700 words; CMPB norm 3,500 — stated in cover letter) |
| Structured abstract ≤350 w (Background and Objective / Methods / Results / Conclusions) | in manuscript | 345 w |
| Keywords 3–6 | in manuscript | 6 |
| Highlights (optional, ≤85 chars each) | `highlights.txt` | ready |
| Figures as separate files, ≥300 dpi, cited in order 1–7 | `../fig/Fig1.png, Fig3.png, Fig4.png, Fig5.png, Fig6.png, Fig7_llm_v7.png, Fig8_calibration_dca.png` → rename Figure_1…Figure_7 at upload | ready |
| Graphical abstract (optional at CMPB) | `../fig/Graphical_abstract.png` | ready |
| Tables editable, no shading, numbered by appearance | in manuscript | ready |
| Supplementary material (one PDF/docx: Notes 1–12, Tables S1–S15, Figs S1–S…) | build from manuscript "Supplementary information" section | **to build** (`build_supplement.py`) |
| Ethics statement with exemption reason | in manuscript (Acknowledgements and declarations) | ready |
| Declaration of competing interest, funding, GenAI, CRediT | in manuscript | ready; **co-author confirmation pending** |
| Data statement (Option: public repositories + GitHub; Zenodo DOI before publication) | in manuscript | ready; Zenodo DOI to add if available |
| Co-author approval of the submitted version | — | **pending (Z.T., E.B.S.)** |


## Package contents (2026-10-27, after step 2)

| File | Status |
|---|---|
| `Paper1_Hemoglyph_CMPB_EN_v7_R6.docx` (manuscript, double spaced, 34 refs, main text 3,814 w) | ready |
| `TITLE_PAGE.md` | needs phone/postal address, Z.T. affiliation, ORCIDs |
| `highlights.txt` (5 × ≤ 85 chars) | ready |
| `Figure_1.png … Figure_7.png` (Fig1, Fig3, Fig4, Fig5, Fig6, Fig7_llm_v7, Fig8_calibration_dca; 1,360–2,080 px wide, tagged 300 dpi) | ready; if EM flags resolution, re-export from the matplotlib scripts at dpi=600 |
| `Supplementary_Information_R6.docx` (Notes 1–12, Tables S1–S16, TRIPOD+AI, ~30k words) | ready |
| `Supplementary_Data_1_sources_13.4.1.xlsx` (in `docs/paper1/supplement/`) | upload as Supplementary Data 1 |
| `COVER_LETTER_CMPB.md` | ready (fill the corresponding-author block) |
| `EXEMPLARS_CMPB.md` | internal, do not upload |
