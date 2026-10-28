# CMPB submission checklist (Editorial Manager: https://submit.elsevier.com/CMPB) — updated 2026-10-28 (R9)

## Files to upload

| EM item | File | Status |
|---|---|---|
| Cover letter | `../COVER_LETTER_CMPB.md` (paste as text; fill the corresponding-author block) | ready |
| Title page (separate; single corresponding author; full postal addresses; ORCIDs) | `TITLE_PAGE.md` | **needs**: telephone, postal address, Z.T. affiliation wording, co-author ORCIDs |
| Manuscript (.docx, single column, double spaced, numbered sections, figures embedded at end for review) | `../../../../ارسال پیپر ۱/Manuscript_Paper1_Hemoglyph_CMPB_R9.docx` | ready — abstract 350 w, main text ≈4,900 w (CMPB norm ≈3,500; excess justified in cover letter), 34 refs, 8 figures, 7 tables |
| Highlights (3–5 bullets, ≤85 characters each incl. spaces) | `highlights.txt` | ready (79–82 chars) |
| Figures, separate files, ≥300 dpi, numbered in order of citation | `../../../../ارسال پیپر ۱/figures/Figure_1.png … Figure_8.png` (2,600–3,200 px wide, tagged 300 dpi) | ready |
| Graphical abstract (optional) | `../fig/Graphical_abstract.png` | ready |
| Supplementary Information (single file) | `../../../../ارسال پیپر ۱/Supplementary_Information.docx` — Notes 1–22, Tables S1–S18, Figs S1–S6, TRIPOD+AI (≈42k words) | ready (file name keeps the R8 tag; content is R9) |
| Supplementary Data 1 | `../../supplement/Supplementary_Data_1_sources_13.4.1.xlsx` | ready |
| Declaration of competing interest form (Elsevier template) | generate at EM from the manuscript text | **to do at upload** |
| Co-author approval of the submitted version | — | **pending (Z.T., E.B.S.)** |

## Statements inside the manuscript (all present)

Ethics (public de-identified data, no human participants) · Funding (none) · Competing interest (first author's commercial product) · Generative-AI declaration (three declared uses) · CRediT · Data and code availability (GitHub + `reproduce.sh`; Zenodo DOI to be inserted) · Software availability.

## Before pressing Submit

1. Push HEAD to GitHub and confirm `bash reproduce.sh quick` passes on the public clone (last authors' run: PASS, `REPRODUCTION_LOG.md`).
2. Mint the Zenodo DOI for the frozen snapshot and replace "will be archived" with the DOI in Data availability (both manuscript and `TITLE_PAGE.md` are unaffected otherwise).
3. Confirm with Z.T. and E.B.S.: affiliation wording, ORCIDs, CRediT lines, approval of the submitted version.
4. Re-read the Declarations block and the cover letter once in full.

## Archival (do not upload)

`../Paper1_Hemoglyph_CMPB_EN_v7_R9_long.md` (un-condensed R9 text; every passage removed from the submission version is also in Supplementary Note 22) · `EXEMPLARS_CMPB.md` · `REVIEWER_RESPONSES_PREPARED.md` · `SUBMISSION_CHECKLIST_FA.md`.
