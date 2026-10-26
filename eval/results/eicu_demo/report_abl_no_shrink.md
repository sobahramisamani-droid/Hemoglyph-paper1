# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 1016 ms, p95 1576 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 47.7% (45.7–49.7) (n=2432) | 51.4% (49.0–53.8) (n=1678) |
| top-5 | 60.4% (58.4–62.3) (n=2432) | 63.7% (61.4–66.0) (n=1678) |
| top-10 | 73.5% (71.7–75.2) (n=2432) | 76.5% (74.4–78.4) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 32.7% (30.9–34.6) (n=2432) |
| top-3 | 61.5% (59.6–63.4) (n=2432) |
| top-5 | 71.7% (69.8–73.4) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 29.9% (28.1–31.7) (n=2432) |
| top-3 | 55.2% (53.2–57.2) (n=2432) |
| top-5 | 66.8% (64.9–68.7) (n=2432) |
| top-10 | 77.9% (76.2–79.5) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 22.7% (21.6–24.0) of 4631

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 81.0% (76.4–84.9) | **0.78** (0.75–0.81) | 83.7% (79.3–87.4) | 69.0% (66.9–71.0) |
| sepsis | partial | 289 | 49.1% (43.4–54.9) | **0.68** (0.65–0.71) | 52.9% (47.2–58.6) | 77.9% (76.0–79.7) |
| diabetes | partial | 246 | 47.6% (41.4–53.8) | **0.69** (0.66–0.73) | 45.5% (39.4–51.8) | 86.8% (85.3–88.2) |
| acute_kidney_injury | yes | 218 | 73.9% (67.6–79.2) | **0.77** (0.75–0.80) | 78.0% (72.0–83.0) | 72.0% (70.0–73.9) |
| chronic_kidney_disease | yes | 148 | 30.4% (23.6–38.2) | **0.78** (0.74–0.82) | 36.5% (29.2–44.5) | 92.8% (91.6–93.8) |
| anemia | yes | 147 | 83.0% (76.1–88.2) | **0.79** (0.75–0.82) | 93.2% (87.9–96.3) | 43.1% (40.9–45.2) |
| gi_bleeding | partial | 145 | 77.9% (70.5–83.9) | **0.75** (0.71–0.79) | 91.0% (85.3–94.7) | 42.9% (40.8–45.0) |
| diabetic_ketoacidosis | yes | 107 | 64.5% (55.1–72.9) | **0.86** (0.82–0.90) | 64.5% (55.1–72.9) | 98.7% (98.1–99.1) |
| hyperglycemia | yes | 96 | 47.9% (38.2–57.8) | **0.70** (0.64–0.75) | 45.8% (36.2–55.8) | 84.6% (83.0–86.0) |
| acute_myocardial_infarction | yes | 84 | 88.1% (79.5–93.4) | **0.76** (0.69–0.81) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 49.3% (37.7–60.9) | **0.72** (0.65–0.77) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 81.0% (69.1–89.1) | **0.66** (0.59–0.73) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 36.8% (25.5–49.8) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.2–60.3) |
| hyponatremia | yes | 52 | 63.5% (49.9–75.2) | **0.89** (0.83–0.93) | 76.9% (63.9–86.3) | 89.6% (88.3–90.8) |
| metabolic_acidosis | yes | 51 | 56.9% (43.3–69.5) | **0.76** (0.68–0.83) | 60.8% (47.1–73.0) | 81.9% (80.2–83.5) |
| hyperkalemia | yes | 49 | 49.0% (35.6–62.5) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 62.5% (47.0–75.8) | **0.88** (0.83–0.93) | 90.0% (76.9–96.0) | 80.9% (79.1–82.5) |
| hypomagnesemia | yes | 37 | 35.1% (21.8–51.2) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 39.4% (24.7–56.3) | **0.65** (0.56–0.75) | 42.4% (27.2–59.2) | 86.9% (85.1–88.6) |
| coagulopathy | yes | 28 | 42.9% (26.5–60.9) | **0.76** (0.68–0.85) | 60.7% (42.4–76.4) | 86.5% (84.3–88.4) |
| cirrhosis_liver_failure | partial | 25 | 60.0% (40.7–76.6) | **0.87** (0.79–0.93) | 72.0% (52.4–85.7) | 82.8% (80.8–84.6) |
| hypoglycemia | yes | 21 | 23.8% (10.6–45.1) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 63.2% (41.0–80.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.74** (0.61–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.48** (0.32–0.63) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.63** (0.47–0.76) | 30.0% (10.8–60.3) | 77.8% (76.0–79.5) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.68** (0.52–0.84) | 40.0% (16.8–68.7) | 87.8% (83.5–91.0) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.90) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.766 (k=24)
