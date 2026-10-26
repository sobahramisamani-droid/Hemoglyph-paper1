# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 981 ms, p95 1432 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 47.5% (45.6–49.5) (n=2432) | 52.9% (50.5–55.3) (n=1678) |
| top-5 | 59.4% (57.5–61.4) (n=2432) | 64.2% (61.9–66.5) (n=1678) |
| top-10 | 73.1% (71.3–74.8) (n=2432) | 76.9% (74.8–78.8) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 32.4% (30.6–34.3) (n=2432) |
| top-3 | 62.2% (60.3–64.1) (n=2432) |
| top-5 | 72.2% (70.4–73.9) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 29.2% (27.5–31.1) (n=2432) |
| top-3 | 54.6% (52.7–56.6) (n=2432) |
| top-5 | 66.4% (64.5–68.2) (n=2432) |
| top-10 | 78.0% (76.3–79.6) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 23.2% (22.0–24.4) of 4535

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 82.2% (77.7–86.0) | **0.78** (0.75–0.80) | 83.7% (79.3–87.4) | 69.9% (67.9–71.9) |
| sepsis | partial | 289 | 50.2% (44.4–55.9) | **0.68** (0.64–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 34.6% (28.9–40.7) | **0.69** (0.65–0.73) | 12.6% (9.0–17.3) | 96.3% (95.3–97.0) |
| acute_kidney_injury | yes | 218 | 78.0% (72.0–83.0) | **0.77** (0.74–0.80) | 80.7% (75.0–85.4) | 72.5% (70.5–74.4) |
| chronic_kidney_disease | yes | 148 | 33.8% (26.7–41.7) | **0.79** (0.75–0.83) | 36.5% (29.2–44.5) | 92.4% (91.2–93.5) |
| anemia | yes | 147 | 83.0% (76.1–88.2) | **0.78** (0.74–0.82) | 93.2% (87.9–96.3) | 43.4% (41.3–45.6) |
| gi_bleeding | partial | 145 | 76.6% (69.0–82.7) | **0.76** (0.72–0.80) | 90.3% (84.4–94.2) | 43.3% (41.1–45.4) |
| diabetic_ketoacidosis | yes | 107 | 63.6% (54.1–72.1) | **0.87** (0.83–0.91) | 63.6% (54.1–72.1) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 31.2% (22.9–41.1) | **0.69** (0.63–0.74) | 9.4% (5.0–16.9) | 95.5% (94.5–96.3) |
| acute_myocardial_infarction | yes | 84 | 89.3% (80.9–94.3) | **0.76** (0.70–0.82) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 44.8% (33.5–56.6) | **0.72** (0.65–0.78) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 82.8% (71.1–90.4) | **0.66** (0.58–0.73) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 43.9% (31.8–56.7) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.1–60.3) |
| hyponatremia | yes | 52 | 61.5% (48.0–73.5) | **0.89** (0.83–0.94) | 76.9% (63.9–86.3) | 89.7% (88.3–90.9) |
| metabolic_acidosis | yes | 51 | 54.9% (41.4–67.7) | **0.77** (0.68–0.83) | 60.8% (47.1–73.0) | 81.7% (80.0–83.3) |
| hyperkalemia | yes | 49 | 53.1% (39.4–66.3) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 70.0% (54.6–81.9) | **0.89** (0.84–0.93) | 90.0% (76.9–96.0) | 80.8% (79.1–82.4) |
| hypomagnesemia | yes | 37 | 35.1% (21.8–51.2) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.65–0.83) | 60.7% (42.4–76.4) | 86.9% (84.7–88.8) |
| cirrhosis_liver_failure | partial | 25 | 60.0% (40.7–76.6) | **0.86** (0.78–0.93) | 60.0% (40.7–76.6) | 90.5% (88.9–91.8) |
| hypoglycemia | yes | 21 | 23.8% (10.6–45.1) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 63.2% (41.0–80.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.73** (0.61–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.51** (0.36–0.67) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 63.6% (35.4–84.8) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.64** (0.49–0.78) | 30.0% (10.8–60.3) | 78.6% (76.9–80.3) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.68** (0.52–0.86) | 40.0% (16.8–68.7) | 92.2% (88.5–94.7) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.53–0.90) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.767 (k=24)
