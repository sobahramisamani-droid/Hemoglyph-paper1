# Engine v7 development gate — result (2026-10-25)

Unit lane: pytest 689/689 (after the sickle-guard trigger was narrowed to Hb < 9; the first full run stopped at
`test_esl_silent_on_healthy_panels` because the guard fired at Hb < 13 — log `pytest_v7.txt`; the rerun after the fix
passed in the foreground, 225 s); hard batteries 151/151, 124/124, 77/78 (same pre-existing miss); healthy sweep
1000/seed 7: 0 syndrome fires, 0 dx ≥ 0.5; perturbation fuzz 753/755 (14.1: 752/755).

eICU demo, 2,314 stays, labs-only, `--encounter icu` (`summary_v7.json` vs `summary_v1410.json`):

| metric | v7 | 14.1 (v6.1 not run) | 13.4.2 legacy |
|---|---|---|---|
| flat top-3 / 5 / 10 | 47.9 / **60.8** / 74.1 | 48.5 / 60.8 / 74.1 | 49.3 / 63.7 / 76.9 |
| two-tier @1 / 3 / 5 | **33.1** / 62.0 / **71.9** | 32.3 / 62.3 / 71.7 | — |
| grouped @1 / 3 / 5 / 10 | 30.1 / 55.6 / 67.4 / 77.9 | 31.0 / 57.2 / 68.8 / 78.4 | — |
| panel-supported flat @1 / 3 / 5 / 10 (n = 1,460) | 29.6 / 62.5 / 78.0 / 91.8 | 31.1 / 63.6 / 78.0 / 91.8 | 30.2 / 64.7 / 81.6 / 95.1 |
| panel-supported two-tier @1 / 3 / 5 / 10 | 43.0 / 77.7 / 89.2 / 97.2 | 41.7 / 77.9 / 88.9 / 97.2 | — |
| group recall@5: anaemia / AMI / HF / GI bleed | 83.0 / 88.1 / 82.8 / 77.9 | 81.6 / 82.1 / 79.3 / 76.6 | |
| group recall@5: AKI / CKD / sepsis / diabetes | 77.5 / 35.8 / 49.1 / 45.1 | 78.9 / 39.9 / 49.5 / 44.7 | |

MIMIC-IV demo (now development data; 235 admissions, 507 lab-detectable pairs): v7 top-3/5/10 35.3 / 47.5 / 62.1 vs 14.1 36.3 / 47.9 / 61.7.

**Pre-stated numeric gate ("flat top-5 > 60.8 AND two-tier@3 ≥ 62.3"): NOT MET — parity** (60.8 = 60.8; 62.0 vs 62.3,
7 labels of 2,432). No improvement in ICD-label recall is claimed for v7.

Panel-supported analysis: the whole 13.4.2 → v6/v7 difference on panel-supported labels is two groups —
CKD (96 → 53 hits of 129; a single creatinine cannot establish chronicity, KDIGO 2012; the renal UNION group is
255 vs 250 in favour of v7) and leukocytosis (33 → 23; `leukocytosis_pattern` is listed beneath sepsis when sepsis
explains it). Every other group is within ±2 hits. Of 2,432 labels, 541 belong to groups without a single laboratory
criterion, 275 have the key analyte absent from the first panel and 431 are NOT supported by the panel values
(e.g. hypocalcaemia coded with albumin-corrected calcium 9.3 mg/dL; pancreatitis with lipase 158 U/L) — the
labs-only ceiling on this reference standard is therefore ≈ 60 % of labels for the flat metric, which the engines
have reached.

Decision (recorded before the quarantine run): v7 is retained as a **correctness release at recall parity** — the
changes remove false attributions (INR "explained by" SIADH; anaemia capped beneath a 0.61 acute-chest-syndrome
leaf while cirrhosis 0.97 stood above), add guideline context guards (sickle complication, non-thyroidal illness,
total calcium without albumin) and grade urate. Its quarantine criteria (SAP Amendment 15) are non-inferiority
criteria; if they fail, 14.1/v6.1 remains the shipped engine.
