# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 150 from 12 hospitals; median inputs 30; latency median 860 ms, p95 1306 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 50.5% (40.9–60.0) (n=101) | 58.2% (46.3–69.3) (n=67) |
| top-5 | 68.3% (58.7–76.6) (n=101) | 77.6% (66.3–85.9) (n=67) |
| top-10 | 86.1% (78.1–91.6) (n=101) | 89.6% (80.0–94.8) (n=67) |

## Chart support of confident outputs (p ≥ 0.7): 22.3% (17.4–28.1) of 233

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 17 | 94.1% (73.0–99.0) | **0.88** (0.81–0.93) | 88.2% (65.7–96.7) | 76.2% (67.9–82.9) |
| diabetes | partial | 14 | 42.9% (21.4–67.4) | **0.74** (0.60–0.87) | 28.6% (11.7–54.6) | 94.4% (88.8–97.2) |
| sepsis | partial | 12 | 33.3% (13.8–60.9) | **0.68** (0.51–0.84) | 41.7% (19.3–68.0) | 89.8% (83.4–94.0) |
| acute_kidney_injury | yes | 9 | 77.8% (45.3–93.7) | **0.86** (0.78–0.94) | 88.9% (56.5–98.0) | 76.2% (68.1–82.7) |
| chronic_kidney_disease | yes | 9 | 77.8% (45.3–93.7) | **0.92** (0.86–0.97) | 88.9% (56.5–98.0) | 83.8% (76.6–89.2) |
| anemia | yes | 6 | 83.3% (43.6–97.0) | **0.90** (0.81–0.99) | 100.0% (61.0–100.0) | 53.0% (44.6–61.2) |
| acute_myocardial_infarction | yes | 6 | 83.3% (43.6–97.0) | **0.66** (0.32–0.93) | 66.7% (30.0–90.3) | 32.3% (18.6–49.9) |
| thrombocytopenia | yes | 5 | 60.0% (23.1–88.2) | **0.96** (0.92–1.00) | 100.0% (56.6–100.0) | 83.7% (76.6–89.0) |
| gi_bleeding | partial | 5 | 100.0% (56.6–100.0) | **0.90** (0.73–1.00) | 100.0% (56.6–100.0) | 52.6% (44.2–60.8) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.862 (k=6)
