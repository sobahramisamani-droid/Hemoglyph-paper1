# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 1058 ms, p95 1579 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 47.6% (45.6–49.6) (n=2432) | 53.2% (50.8–55.5) (n=1678) |
| top-5 | 59.7% (57.8–61.7) (n=2432) | 64.7% (62.3–66.9) (n=1678) |
| top-10 | 73.3% (71.5–75.0) (n=2432) | 77.2% (75.1–79.1) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 32.6% (30.7–34.5) (n=2432) |
| top-3 | 62.0% (60.1–64.0) (n=2432) |
| top-5 | 72.2% (70.4–73.9) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 29.3% (27.5–31.1) (n=2432) |
| top-3 | 54.6% (52.6–56.6) (n=2432) |
| top-5 | 66.5% (64.6–68.3) (n=2432) |
| top-10 | 78.3% (76.6–79.9) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 23.1% (21.9–24.4) of 4548

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 82.2% (77.7–86.0) | **0.78** (0.75–0.80) | 83.7% (79.3–87.4) | 69.6% (67.5–71.6) |
| sepsis | partial | 289 | 49.8% (44.1–55.6) | **0.68** (0.64–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 35.4% (29.7–41.5) | **0.69** (0.65–0.73) | 13.0% (9.4–17.8) | 96.2% (95.3–97.0) |
| acute_kidney_injury | yes | 218 | 77.5% (71.5–82.6) | **0.77** (0.75–0.80) | 81.7% (76.0–86.2) | 71.9% (69.9–73.8) |
| chronic_kidney_disease | yes | 148 | 37.2% (29.8–45.2) | **0.80** (0.76–0.83) | 38.5% (31.1–46.5) | 92.3% (91.1–93.4) |
| anemia | yes | 147 | 83.0% (76.1–88.2) | **0.78** (0.74–0.82) | 93.2% (87.9–96.3) | 43.1% (41.0–45.3) |
| gi_bleeding | partial | 145 | 76.6% (69.0–82.7) | **0.75** (0.71–0.79) | 91.0% (85.3–94.7) | 42.9% (40.8–45.1) |
| diabetic_ketoacidosis | yes | 107 | 63.6% (54.1–72.1) | **0.87** (0.82–0.91) | 63.6% (54.1–72.1) | 98.7% (98.1–99.1) |
| hyperglycemia | yes | 96 | 35.4% (26.6–45.4) | **0.69** (0.63–0.74) | 10.4% (5.8–18.1) | 95.4% (94.5–96.2) |
| acute_myocardial_infarction | yes | 84 | 89.3% (80.9–94.3) | **0.76** (0.70–0.82) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 44.8% (33.5–56.6) | **0.72** (0.65–0.77) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 81.0% (69.1–89.1) | **0.66** (0.58–0.73) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 43.9% (31.8–56.7) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.2–60.3) |
| hyponatremia | yes | 52 | 61.5% (48.0–73.5) | **0.89** (0.83–0.94) | 76.9% (63.9–86.3) | 89.7% (88.3–90.9) |
| metabolic_acidosis | yes | 51 | 56.9% (43.3–69.5) | **0.77** (0.68–0.83) | 64.7% (51.0–76.4) | 81.1% (79.4–82.7) |
| hyperkalemia | yes | 49 | 53.1% (39.4–66.3) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 70.0% (54.6–81.9) | **0.89** (0.84–0.93) | 90.0% (76.9–96.0) | 80.8% (79.1–82.4) |
| hypomagnesemia | yes | 37 | 35.1% (21.8–51.2) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.65–0.83) | 60.7% (42.4–76.4) | 86.8% (84.6–88.7) |
| cirrhosis_liver_failure | partial | 25 | 60.0% (40.7–76.6) | **0.86** (0.78–0.93) | 60.0% (40.7–76.6) | 90.0% (88.4–91.4) |
| hypoglycemia | yes | 21 | 23.8% (10.6–45.1) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 63.2% (41.0–80.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.73** (0.61–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.51** (0.36–0.67) | 0.0% (0.0–19.4) | 99.9% (99.5–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.64** (0.49–0.78) | 30.0% (10.8–60.3) | 78.6% (76.9–80.3) |
| hypothyroidism | yes | 10 | 40.0% (16.8–68.7) | **0.68** (0.52–0.85) | 40.0% (16.8–68.7) | 91.2% (87.4–93.9) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.53–0.90) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.767 (k=24)
