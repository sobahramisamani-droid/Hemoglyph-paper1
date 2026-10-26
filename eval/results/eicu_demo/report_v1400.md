# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 980 ms, p95 1413 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 43.8% (41.9–45.8) (n=2432) | 48.7% (46.4–51.1) (n=1678) |
| top-5 | 58.4% (56.4–60.3) (n=2432) | 63.1% (60.8–65.4) (n=1678) |
| top-10 | 73.8% (72.1–75.6) (n=2432) | 77.5% (75.5–79.5) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 30.4% (28.6–32.3) (n=2432) |
| top-3 | 61.0% (59.0–62.9) (n=2432) |
| top-5 | 72.2% (70.3–73.9) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 32.9% (31.0–34.7) (n=2432) |
| top-3 | 57.2% (55.2–59.1) (n=2432) |
| top-5 | 68.6% (66.8–70.4) (n=2432) |
| top-10 | 78.6% (76.9–80.2) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 22.9% (21.7–24.1) of 4561

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 84.0% (79.7–87.6) | **0.79** (0.77–0.82) | 84.0% (79.7–87.6) | 69.2% (67.1–71.2) |
| sepsis | partial | 289 | 45.0% (39.4–50.7) | **0.68** (0.65–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 41.5% (35.5–47.7) | **0.69** (0.66–0.73) | 40.2% (34.3–46.5) | 88.7% (87.2–90.0) |
| acute_kidney_injury | yes | 218 | 74.3% (68.1–79.7) | **0.78** (0.75–0.81) | 82.6% (77.0–87.0) | 71.1% (69.1–73.1) |
| chronic_kidney_disease | yes | 148 | 30.4% (23.6–38.2) | **0.79** (0.75–0.82) | 41.9% (34.2–49.9) | 90.9% (89.6–92.0) |
| anemia | yes | 147 | 74.8% (67.2–81.2) | **0.78** (0.74–0.82) | 93.2% (87.9–96.3) | 43.3% (41.1–45.4) |
| gi_bleeding | partial | 145 | 72.4% (64.6–79.0) | **0.75** (0.70–0.79) | 91.0% (85.3–94.7) | 43.1% (40.9–45.2) |
| diabetic_ketoacidosis | yes | 107 | 62.6% (53.2–71.2) | **0.86** (0.82–0.90) | 63.6% (54.1–72.1) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 39.6% (30.4–49.6) | **0.70** (0.64–0.75) | 43.8% (34.3–53.7) | 86.8% (85.3–88.2) |
| acute_myocardial_infarction | yes | 84 | 95.2% (88.4–98.1) | **0.71** (0.65–0.77) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 43.3% (32.1–55.2) | **0.72** (0.65–0.77) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 77.6% (65.3–86.4) | **0.66** (0.58–0.73) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 43.9% (31.8–56.7) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.2–60.3) |
| hyponatremia | yes | 52 | 59.6% (46.1–71.8) | **0.89** (0.83–0.93) | 76.9% (63.9–86.3) | 89.6% (88.3–90.8) |
| metabolic_acidosis | yes | 51 | 51.0% (37.7–64.1) | **0.76** (0.67–0.82) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 38.8% (26.4–52.8) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 67.5% (52.0–79.9) | **0.89** (0.84–0.93) | 90.0% (76.9–96.0) | 80.9% (79.2–82.5) |
| hypomagnesemia | yes | 37 | 37.8% (24.1–53.9) | **0.68** (0.60–0.76) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 53.6% (35.8–70.5) | **0.75** (0.65–0.84) | 60.7% (42.4–76.4) | 86.9% (84.7–88.8) |
| cirrhosis_liver_failure | partial | 25 | 52.0% (33.5–70.0) | **0.87** (0.79–0.93) | 64.0% (44.5–79.8) | 89.7% (88.0–91.1) |
| hypoglycemia | yes | 21 | 28.6% (13.8–50.0) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 57.9% (36.3–76.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.74** (0.62–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.51** (0.37–0.67) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 20.0% (5.7–51.0) | **0.63** (0.47–0.77) | 30.0% (10.8–60.3) | 77.9% (76.1–79.5) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.68** (0.52–0.85) | 40.0% (16.8–68.7) | 91.8% (88.1–94.5) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.91) | 66.7% (35.4–87.9) | 78.4% (75.2–81.3) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.765 (k=24)
