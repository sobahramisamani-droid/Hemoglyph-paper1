# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 986 ms, p95 1461 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 47.9% (45.9–49.9) (n=2432) | 51.9% (49.5–54.3) (n=1678) |
| top-5 | 61.1% (59.2–63.1) (n=2432) | 65.1% (62.8–67.4) (n=1678) |
| top-10 | 73.8% (72.0–75.5) (n=2432) | 77.4% (75.3–79.3) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 32.9% (31.0–34.7) (n=2432) |
| top-3 | 62.0% (60.0–63.9) (n=2432) |
| top-5 | 71.8% (70.0–73.5) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 30.3% (28.5–32.2) (n=2432) |
| top-3 | 55.9% (53.9–57.8) (n=2432) |
| top-5 | 67.8% (65.9–69.6) (n=2432) |
| top-10 | 77.5% (75.8–79.2) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 22.8% (21.6–24.1) of 4613

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 82.2% (77.7–86.0) | **0.78** (0.75–0.80) | 84.0% (79.7–87.6) | 69.2% (67.1–71.2) |
| sepsis | partial | 289 | 48.8% (43.1–54.5) | **0.68** (0.65–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 46.3% (40.2–52.6) | **0.69** (0.65–0.73) | 40.2% (34.3–46.5) | 88.7% (87.2–90.0) |
| acute_kidney_injury | yes | 218 | 78.4% (72.5–83.4) | **0.77** (0.75–0.80) | 82.1% (76.5–86.6) | 71.4% (69.4–73.4) |
| chronic_kidney_disease | yes | 148 | 35.8% (28.5–43.8) | **0.76** (0.72–0.80) | 39.2% (31.7–47.2) | 92.1% (90.9–93.2) |
| anemia | yes | 147 | 83.0% (76.1–88.2) | **0.78** (0.74–0.82) | 93.2% (87.9–96.3) | 43.1% (41.0–45.3) |
| gi_bleeding | partial | 145 | 78.6% (71.3–84.5) | **0.75** (0.71–0.79) | 91.0% (85.3–94.7) | 43.0% (40.8–45.1) |
| diabetic_ketoacidosis | yes | 107 | 63.6% (54.1–72.1) | **0.86** (0.81–0.90) | 63.6% (54.1–72.1) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 46.9% (37.2–56.8) | **0.70** (0.64–0.75) | 43.8% (34.3–53.7) | 86.8% (85.3–88.2) |
| acute_myocardial_infarction | yes | 84 | 86.9% (78.1–92.5) | **0.76** (0.70–0.82) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 49.3% (37.7–60.9) | **0.72** (0.65–0.77) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 82.8% (71.1–90.4) | **0.66** (0.59–0.73) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 40.4% (28.6–53.3) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.2–60.3) |
| hyponatremia | yes | 52 | 63.5% (49.9–75.2) | **0.89** (0.83–0.93) | 76.9% (63.9–86.3) | 89.6% (88.3–90.8) |
| metabolic_acidosis | yes | 51 | 54.9% (41.4–67.7) | **0.75** (0.66–0.81) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 51.0% (37.5–64.4) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 65.0% (49.5–77.9) | **0.89** (0.84–0.93) | 90.0% (76.9–96.0) | 80.8% (79.1–82.4) |
| hypomagnesemia | yes | 37 | 35.1% (21.8–51.2) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.66–0.84) | 60.7% (42.4–76.4) | 87.2% (85.0–89.0) |
| cirrhosis_liver_failure | partial | 25 | 56.0% (37.1–73.3) | **0.81** (0.71–0.91) | 64.0% (44.5–79.8) | 91.6% (90.1–92.9) |
| hypoglycemia | yes | 21 | 23.8% (10.6–45.1) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 63.2% (41.0–80.9) | **0.73** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.73** (0.61–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.51** (0.37–0.66) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.63** (0.47–0.76) | 30.0% (10.8–60.3) | 77.8% (76.0–79.5) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.68** (0.52–0.84) | 10.0% (1.8–40.4) | 97.3% (94.7–98.6) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.90) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.764 (k=24)
