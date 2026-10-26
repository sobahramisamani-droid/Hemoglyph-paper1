# Hemoglyph-LabBench v1 — an open benchmark for laboratory-only differential diagnosis

Author: Sobhan Bahrami (sobahramisamani@gmail.com). Licence: code and documents/keys as stated in the repository LICENSE file (**to be chosen and committed by the author before release — none exists yet**); eICU-derived panels inherit the eICU-CRD demo ODbL 1.0 terms (attribution, share-alike).
Built 2026-10-23 from the Hemoglyph repository at commit/freeze listed in MANIFEST.sha256.

## Why
Language models cannot reliably classify laboratory values as high or low even when reference ranges are
supplied (Hager et al., Nat Med 2024, Ext. Fig. 4), and most diagnostic benchmarks hand the model the whole
narrative. LabBench isolates the question *what can be inferred from the numbers alone* (labs + age + sex),
with pre-specified keys, blinded comparison material and safety batteries, so that any engine, LLM or
clinician can be scored the same way.

## Tasks
| id | task | n | input | primary metric | key |
|---|---|---:|---|---|---|
| T1 | eICU-CRD demo lab-only differential | 2,314 ICU stays, 186 hospitals | labs (+ optional context / trajectory arms) | recall@5 of clinician problem-list groups (62-group regex map) | `eval_eicu.py: GROUPS` |
| T2 | blinded LLM-vs-engine comparison | 400 panels (596 labels) | labs + age/sex, de-identified text | recall@5, MRR, rank bins, test–retest | `b8_key_n240.json` |
| T3 | safety | 200 fabrication panels, 200 healthy panels, critical values | labs | unsupported-assertion rate; false-alarm rate | scripts |
| T4 | single-label validations | NHANES 7 cycles, UCI HCV 615, UCI thyroid 3,162, ILPD 583 | labs | AUROC | scripts |
| T5 | PMC-Patients case vignettes (Bhasuran 2025) | 50 | lab paragraph only (parser arm / manual arm) | top-1/5/10 specific & syndrome | `scoring_key_prespecified.json` |
| H  | human validation instruments | 100 rules; 40 panels | — | error rate; 3-arm recall@5 | forms + `score_forms.py` |

## Data access (not redistributed here)
* eICU-CRD demo 2.0.1 — PhysioNet, open access (ODbL): https://physionet.org/content/eicu-crd-demo/2.0.1/
* NHANES — CDC public files (fetch_nhanes_cycle.py)
* UCI HCV / thyroid, ILPD — UCI ML repository (fetch inside the eval scripts)
* PMC-Patients 50 vignettes — ESM of Bhasuran et al. 2025 (`sd_1.xlsx`) and https://github.com/balubhasuran/DDx_CaseReports
* PhysioNet/CinC 2019 sepsis — https://physionet.org/content/challenge-2019/1.0.0/

## How to score your own system on T2 (the easiest entry point)
1. Read `T2_blind_llm_comparison/b8_blind_panels_n240.json` (field `panel_text`; also `b4_oos_stays_n60.json`, `b3_stays_engine_v3_n100.json`).
2. Produce ≤10 ranked diagnoses per panel, save as `{stay_id: [dx, ...]}`.
3. `python labbench_score.py --answers your.json --key b8_key_n240.json` → recall@1/3/5/10, MRR, "not listed" rate; the synonym
   map (`SYN` in llm_zero_shot.py) is the one used for all published arms. Report the scoring-map version with your result.

## Pre-registration and reporting
SAP with all amendments (`docs/SAP_Hemoglyph_v1.md`), TRIPOD+AI checklist, Bond-2012 DDx-generator checklist, cohort flow.
Nothing in the keys was changed after seeing results; where a map was found imperfect (label audit, 2 misses /
150 positives) the change is deferred to the next protocol version and documented.

## Known limitations of the benchmark itself
Reference standard of T1 is the routine clinician problem list (not adjudicated); T2 LLM arm is a single
GPT-4-class model run by the author (exploratory); T5 keys were written by the author; the human-validation
forms (H) are instruments, their results are added when returned.
