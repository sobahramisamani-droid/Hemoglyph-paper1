# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 992 ms, p95 1478 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 47.5% (45.5–49.4) (n=2432) | 51.6% (49.2–54.0) (n=1678) |
| top-5 | 59.5% (57.6–61.5) (n=2432) | 64.1% (61.8–66.4) (n=1678) |
| top-10 | 69.9% (68.0–71.7) (n=2432) | 74.9% (72.8–76.9) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 32.1% (30.2–34.0) (n=2432) |
| top-3 | 59.8% (57.8–61.7) (n=2432) |
| top-5 | 68.2% (66.3–70.0) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 31.2% (29.4–33.0) (n=2432) |
| top-3 | 55.1% (53.1–57.1) (n=2432) |
| top-5 | 65.3% (63.4–67.2) (n=2432) |
| top-10 | 73.0% (71.2–74.7) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 22.7% (21.5–23.9) of 4701

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 81.0% (76.4–84.9) | **0.78** (0.75–0.80) | 83.4% (79.0–87.1) | 70.3% (68.2–72.3) |
| sepsis | partial | 289 | 50.5% (44.8–56.2) | **0.68** (0.65–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 36.2% (30.4–42.4) | **0.66** (0.63–0.70) | 40.2% (34.3–46.5) | 88.7% (87.2–90.0) |
| acute_kidney_injury | yes | 218 | 77.1% (71.0–82.1) | **0.77** (0.74–0.80) | 81.7% (76.0–86.2) | 72.2% (70.2–74.1) |
| chronic_kidney_disease | yes | 148 | 31.1% (24.2–38.9) | **0.72** (0.68–0.76) | 33.1% (26.0–41.0) | 93.8% (92.7–94.8) |
| anemia | yes | 147 | 79.6% (72.4–85.3) | **0.78** (0.73–0.82) | 93.2% (87.9–96.3) | 43.4% (41.3–45.6) |
| gi_bleeding | partial | 145 | 76.6% (69.0–82.7) | **0.76** (0.72–0.80) | 90.3% (84.4–94.2) | 43.3% (41.2–45.5) |
| diabetic_ketoacidosis | yes | 107 | 64.5% (55.1–72.9) | **0.83** (0.79–0.87) | 64.5% (55.1–72.9) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 36.5% (27.5–46.4) | **0.66** (0.60–0.71) | 43.8% (34.3–53.7) | 86.8% (85.3–88.2) |
| acute_myocardial_infarction | yes | 84 | 89.3% (80.9–94.3) | **0.77** (0.70–0.82) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 49.3% (37.7–60.9) | **0.72** (0.65–0.78) | 53.7% (41.9–65.1) | 87.7% (86.2–89.0) |
| heart_failure | yes | 58 | 86.2% (75.1–92.8) | **0.67** (0.59–0.74) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 43.9% (31.8–56.7) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.2% (56.2–60.3) |
| hyponatremia | yes | 52 | 63.5% (49.9–75.2) | **0.88** (0.82–0.93) | 76.9% (63.9–86.3) | 89.9% (88.6–91.1) |
| metabolic_acidosis | yes | 51 | 56.9% (43.3–69.5) | **0.75** (0.66–0.81) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 53.1% (39.4–66.3) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 67.5% (52.0–79.9) | **0.88** (0.82–0.93) | 90.0% (76.9–96.0) | 80.8% (79.1–82.4) |
| hypomagnesemia | yes | 37 | 32.4% (19.6–48.5) | **0.67** (0.59–0.75) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.65–0.84) | 60.7% (42.4–76.4) | 87.2% (85.0–89.0) |
| cirrhosis_liver_failure | partial | 25 | 60.0% (40.7–76.6) | **0.85** (0.76–0.93) | 64.0% (44.5–79.8) | 89.1% (87.5–90.6) |
| hypoglycemia | yes | 21 | 23.8% (10.6–45.1) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 68.4% (46.0–84.6) | **0.73** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.73** (0.61–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.39** (0.27–0.52) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 72.7% (43.4–90.3) | **0.87** (0.73–0.97) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 20.0% (5.7–51.0) | **0.64** (0.49–0.78) | 30.0% (10.8–60.3) | 77.8% (76.0–79.5) |
| hypothyroidism | yes | 10 | 30.0% (10.8–60.3) | **0.69** (0.54–0.85) | 10.0% (1.8–40.4) | 97.3% (94.7–98.6) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.90) | 66.7% (35.4–87.9) | 78.3% (75.1–81.2) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.757 (k=24)
