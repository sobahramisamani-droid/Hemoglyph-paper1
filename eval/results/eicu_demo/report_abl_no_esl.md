# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 1021 ms, p95 1574 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 39.5% (37.6–41.5) (n=2432) | 43.8% (41.4–46.2) (n=1678) |
| top-5 | 51.3% (49.3–53.3) (n=2432) | 55.5% (53.1–57.8) (n=1678) |
| top-10 | 68.3% (66.5–70.2) (n=2432) | 72.4% (70.2–74.5) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 28.2% (26.4–30.0) (n=2432) |
| top-3 | 56.0% (54.1–58.0) (n=2432) |
| top-5 | 66.0% (64.0–67.8) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 19.0% (17.5–20.6) (n=2432) |
| top-3 | 41.2% (39.3–43.2) (n=2432) |
| top-5 | 52.8% (50.8–54.7) (n=2432) |
| top-10 | 69.0% (67.2–70.8) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 23.9% (22.1–25.8) of 2024

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 81.9% (77.4–85.7) | **0.81** (0.78–0.83) | 81.9% (77.4–85.7) | 72.7% (70.7–74.6) |
| sepsis | partial | 289 | 16.6% (12.8–21.3) | **0.62** (0.59–0.66) | 25.3% (20.6–30.6) | 93.6% (92.4–94.6) |
| diabetes | partial | 246 | 50.4% (44.2–56.6) | **0.69** (0.66–0.73) | 40.2% (34.3–46.5) | 89.1% (87.7–90.4) |
| acute_kidney_injury | yes | 218 | 52.8% (46.1–59.3) | **0.76** (0.73–0.79) | 62.4% (55.8–68.5) | 80.7% (78.9–82.4) |
| chronic_kidney_disease | yes | 148 | 8.8% (5.2–14.4) | **0.74** (0.70–0.78) | 18.2% (12.9–25.2) | 96.6% (95.7–97.2) |
| anemia | yes | 147 | 86.4% (79.9–91.0) | **0.70** (0.66–0.74) | 93.2% (87.9–96.3) | 43.1% (41.0–45.3) |
| gi_bleeding | partial | 145 | 85.5% (78.9–90.3) | **0.65** (0.61–0.68) | 91.0% (85.3–94.7) | 42.9% (40.8–45.1) |
| diabetic_ketoacidosis | yes | 107 | 1.9% (0.5–6.6) | **0.83** (0.78–0.87) | 3.7% (1.5–9.2) | 100.0% (99.8–100.0) |
| hyperglycemia | yes | 96 | 49.0% (39.2–58.8) | **0.70** (0.64–0.75) | 40.6% (31.3–50.6) | 87.1% (85.6–88.4) |
| acute_myocardial_infarction | yes | 84 | 91.7% (83.8–95.9) | **0.72** (0.67–0.77) | 91.7% (83.8–95.9) | 33.7% (30.0–37.7) |
| hypokalemia | yes | 67 | 44.8% (33.5–56.6) | **0.71** (0.64–0.76) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 82.8% (71.1–90.4) | **0.71** (0.63–0.78) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 57.9% (45.0–69.8) | **0.71** (0.66–0.76) | 86.0% (74.7–92.7) | 58.2% (56.1–60.3) |
| hyponatremia | yes | 52 | 82.7% (70.3–90.6) | **0.88** (0.82–0.93) | 80.8% (68.1–89.2) | 87.6% (86.2–88.9) |
| metabolic_acidosis | yes | 51 | 51.0% (37.7–64.1) | **0.75** (0.66–0.81) | 51.0% (37.7–64.1) | 84.7% (83.1–86.1) |
| hyperkalemia | yes | 49 | 14.3% (7.1–26.7) | **0.91** (0.86–0.95) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 72.5% (57.2–83.9) | **0.87** (0.82–0.91) | 90.0% (76.9–96.0) | 80.8% (79.0–82.4) |
| hypomagnesemia | yes | 37 | 37.8% (24.1–53.9) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 12.1% (4.8–27.3) | **0.63** (0.54–0.72) | 0.0% (0.0–10.4) | 100.0% (99.7–100.0) |
| coagulopathy | yes | 28 | 3.6% (0.6–17.7) | **0.60** (0.52–0.70) | 7.1% (2.0–22.6) | 99.7% (99.2–99.9) |
| cirrhosis_liver_failure | partial | 25 | 68.0% (48.4–82.8) | **0.88** (0.79–0.94) | 64.0% (44.5–79.8) | 91.1% (89.6–92.4) |
| hypoglycemia | yes | 21 | 28.6% (13.8–50.0) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 52.6% (31.7–72.7) | **0.70** (0.60–0.83) | 52.6% (31.7–72.7) | 88.3% (85.7–90.5) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.75** (0.62–0.86) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.51** (0.36–0.67) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 64.3% (38.8–83.7) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 63.6% (35.4–84.8) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.66** (0.49–0.82) | 70.0% (39.7–89.2) | 62.4% (60.3–64.4) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.68** (0.52–0.86) | 40.0% (16.8–68.7) | 92.2% (88.5–94.7) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.72** (0.53–0.89) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.751 (k=24)
