# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 176 ms, p95 236 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 46.8% (44.9–48.8) (n=2432) | 49.9% (47.5–52.3) (n=1678) |
| top-5 | 59.9% (57.9–61.8) (n=2432) | 62.6% (60.2–64.9) (n=1678) |
| top-10 | 72.5% (70.6–74.2) (n=2432) | 74.3% (72.2–76.3) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 31.0% (29.2–32.9) (n=2432) |
| top-3 | 59.0% (57.0–60.9) (n=2432) |
| top-5 | 68.9% (67.0–70.7) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 27.1% (25.4–28.9) (n=2432) |
| top-3 | 53.0% (51.0–54.9) (n=2432) |
| top-5 | 64.5% (62.6–66.4) (n=2432) |
| top-10 | 75.8% (74.0–77.4) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 22.2% (21.0–23.5) of 4512

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 81.6% (77.0–85.4) | **0.77** (0.74–0.79) | 83.4% (79.0–87.1) | 70.5% (68.4–72.5) |
| sepsis | partial | 289 | 51.9% (46.2–57.6) | **0.68** (0.64–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 44.7% (38.6–51.0) | **0.64** (0.60–0.67) | 13.0% (9.4–17.8) | 96.2% (95.3–97.0) |
| acute_kidney_injury | yes | 218 | 73.4% (67.2–78.8) | **0.76** (0.72–0.78) | 77.5% (71.5–82.6) | 73.8% (71.9–75.7) |
| chronic_kidney_disease | yes | 148 | 35.1% (27.9–43.1) | **0.79** (0.75–0.83) | 29.1% (22.3–36.8) | 94.7% (93.7–95.6) |
| anemia | yes | 147 | 87.1% (80.7–91.6) | **0.79** (0.75–0.83) | 93.2% (87.9–96.3) | 43.1% (41.0–45.3) |
| gi_bleeding | partial | 145 | 81.4% (74.3–86.9) | **0.75** (0.71–0.79) | 91.0% (85.3–94.7) | 42.9% (40.8–45.1) |
| diabetic_ketoacidosis | yes | 107 | 63.6% (54.1–72.1) | **0.87** (0.82–0.91) | 61.7% (52.2–70.3) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 46.9% (37.2–56.8) | **0.63** (0.58–0.67) | 10.4% (5.8–18.1) | 95.4% (94.5–96.2) |
| acute_myocardial_infarction | yes | 84 | 90.5% (82.3–95.1) | **0.75** (0.69–0.81) | 95.2% (88.4–98.1) | 24.0% (20.7–27.6) |
| hypokalemia | yes | 67 | 37.3% (26.7–49.3) | **0.72** (0.65–0.77) | 23.9% (15.3–35.3) | 98.1% (97.4–98.6) |
| heart_failure | yes | 58 | 86.2% (75.1–92.8) | **0.64** (0.57–0.72) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 5.3% (1.8–14.4) | **0.53** (0.50–0.57) | 8.8% (3.8–18.9) | 98.1% (97.4–98.6) |
| hyponatremia | yes | 52 | 61.5% (48.0–73.5) | **0.85** (0.79–0.91) | 38.5% (26.5–52.0) | 98.5% (97.9–98.9) |
| metabolic_acidosis | yes | 51 | 56.9% (43.3–69.5) | **0.75** (0.66–0.81) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 44.9% (31.9–58.7) | **0.92** (0.87–0.96) | 59.2% (45.2–71.8) | 98.5% (97.8–98.9) |
| thrombocytopenia | yes | 40 | 50.0% (35.2–64.8) | **0.88** (0.82–0.92) | 37.5% (24.2–53.0) | 97.4% (96.7–98.0) |
| hypomagnesemia | yes | 37 | 21.6% (11.4–37.2) | **0.61** (0.53–0.68) | 32.4% (19.6–48.5) | 89.6% (87.8–91.2) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.65–0.83) | 60.7% (42.4–76.4) | 86.9% (84.7–88.8) |
| cirrhosis_liver_failure | partial | 25 | 64.0% (44.5–79.8) | **0.86** (0.78–0.93) | 64.0% (44.5–79.8) | 89.7% (88.0–91.1) |
| hypoglycemia | yes | 21 | 28.6% (13.8–50.0) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 68.4% (46.0–84.6) | **0.74** (0.63–0.86) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.73** (0.62–0.84) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 6.2% (1.1–28.3) | **0.56** (0.40–0.71) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 57.1% (32.6–78.6) | **0.78** (0.64–0.92) | 57.1% (32.6–78.6) | 99.2% (98.7–99.5) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.92** (0.85–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.54** (0.44–0.67) | 10.0% (1.8–40.4) | 96.0% (95.1–96.7) |
| hypothyroidism | yes | 10 | 50.0% (23.7–76.3) | **0.68** (0.52–0.86) | 40.0% (16.8–68.7) | 91.8% (88.1–94.5) |
| hypophosphatemia | yes | 9 | 11.1% (2.0–43.5) | **0.54** (0.48–0.65) | 11.1% (2.0–43.5) | 97.3% (95.8–98.3) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.732 (k=24)
