# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 1135 ms, p95 1660 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 48.2% (46.3–50.2) (n=2432) | 51.8% (49.5–54.2) (n=1678) |
| top-5 | 60.8% (58.8–62.7) (n=2432) | 64.7% (62.3–66.9) (n=1678) |
| top-10 | 74.0% (72.2–75.7) (n=2432) | 77.4% (75.4–79.4) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 33.2% (31.3–35.1) (n=2432) |
| top-3 | 61.8% (59.9–63.8) (n=2432) |
| top-5 | 71.8% (69.9–73.5) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 30.6% (28.8–32.4) (n=2432) |
| top-3 | 56.0% (54.1–58.0) (n=2432) |
| top-5 | 67.4% (65.5–69.2) (n=2432) |
| top-10 | 77.5% (75.8–79.2) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 22.1% (21.0–23.2) of 5186

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 80.4% (75.7–84.3) | **0.78** (0.75–0.80) | 85.0% (80.7–88.4) | 66.3% (64.2–68.4) |
| sepsis | partial | 289 | 49.1% (43.4–54.9) | **0.68** (0.65–0.71) | 52.2% (46.5–57.9) | 82.0% (80.3–83.7) |
| diabetes | partial | 246 | 45.9% (39.8–52.2) | **0.69** (0.65–0.73) | 40.2% (34.3–46.5) | 88.7% (87.2–90.0) |
| acute_kidney_injury | yes | 218 | 77.1% (71.0–82.1) | **0.77** (0.75–0.80) | 83.5% (78.0–87.8) | 67.6% (65.6–69.6) |
| chronic_kidney_disease | yes | 148 | 35.1% (27.9–43.1) | **0.76** (0.72–0.80) | 40.5% (33.0–48.6) | 92.3% (91.0–93.3) |
| anemia | yes | 147 | 82.3% (75.3–87.6) | **0.78** (0.74–0.82) | 93.2% (87.9–96.3) | 43.4% (41.3–45.6) |
| gi_bleeding | partial | 145 | 77.9% (70.5–83.9) | **0.75** (0.71–0.79) | 91.0% (85.3–94.7) | 43.3% (41.1–45.4) |
| diabetic_ketoacidosis | yes | 107 | 64.5% (55.1–72.9) | **0.85** (0.80–0.89) | 64.5% (55.1–72.9) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 50.0% (40.2–59.8) | **0.70** (0.64–0.75) | 43.8% (34.3–53.7) | 86.8% (85.3–88.2) |
| acute_myocardial_infarction | yes | 84 | 88.1% (79.5–93.4) | **0.76** (0.70–0.82) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 44.8% (33.5–56.6) | **0.72** (0.65–0.77) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 84.5% (73.1–91.6) | **0.66** (0.59–0.74) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 42.1% (30.2–55.0) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.1–60.3) |
| hyponatremia | yes | 52 | 61.5% (48.0–73.5) | **0.89** (0.83–0.93) | 76.9% (63.9–86.3) | 89.6% (88.3–90.8) |
| metabolic_acidosis | yes | 51 | 54.9% (41.4–67.7) | **0.76** (0.67–0.82) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 49.0% (35.6–62.5) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 65.0% (49.5–77.9) | **0.88** (0.83–0.93) | 90.0% (76.9–96.0) | 80.8% (79.1–82.4) |
| hypomagnesemia | yes | 37 | 35.1% (21.8–51.2) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.65–0.83) | 60.7% (42.4–76.4) | 86.5% (84.3–88.4) |
| cirrhosis_liver_failure | partial | 25 | 56.0% (37.1–73.3) | **0.85** (0.75–0.92) | 64.0% (44.5–79.8) | 88.5% (86.8–90.0) |
| hypoglycemia | yes | 21 | 23.8% (10.6–45.1) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 63.2% (41.0–80.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.74** (0.61–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.46** (0.31–0.61) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 63.6% (35.4–84.8) | **0.88** (0.76–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.63** (0.47–0.76) | 30.0% (10.8–60.3) | 77.8% (76.0–79.5) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.69** (0.53–0.86) | 40.0% (16.8–68.7) | 92.2% (88.5–94.7) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.90) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.762 (k=24)
