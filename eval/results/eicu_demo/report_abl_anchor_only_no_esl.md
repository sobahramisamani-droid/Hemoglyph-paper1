# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 124 ms, p95 271 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 38.0% (36.0–39.9) (n=2432) | 39.0% (36.7–41.3) (n=1678) |
| top-5 | 48.2% (46.3–50.2) (n=2432) | 47.1% (44.7–49.5) (n=1678) |
| top-10 | 68.1% (66.2–69.9) (n=2432) | 69.2% (67.0–71.4) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 26.9% (25.1–28.6) (n=2432) |
| top-3 | 50.1% (48.1–52.1) (n=2432) |
| top-5 | 60.9% (58.9–62.8) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 19.2% (17.7–20.9) (n=2432) |
| top-3 | 39.3% (37.3–41.2) (n=2432) |
| top-5 | 48.8% (46.9–50.8) (n=2432) |
| top-10 | 68.3% (66.5–70.2) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 23.3% (21.5–25.3) of 1922

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 83.4% (79.0–87.1) | **0.81** (0.78–0.83) | 80.1% (75.4–84.0) | 75.3% (73.3–77.2) |
| sepsis | partial | 289 | 31.5% (26.4–37.1) | **0.62** (0.58–0.65) | 25.3% (20.6–30.6) | 93.6% (92.4–94.6) |
| diabetes | partial | 246 | 52.4% (46.2–58.6) | **0.63** (0.60–0.67) | 5.7% (3.4–9.3) | 97.8% (97.1–98.4) |
| acute_kidney_injury | yes | 218 | 17.4% (13.0–23.0) | **0.68** (0.66–0.71) | 0.0% (0.0–1.7) | 100.0% (99.8–100.0) |
| chronic_kidney_disease | yes | 148 | 12.8% (8.4–19.2) | **0.74** (0.70–0.78) | 5.4% (2.8–10.3) | 98.7% (98.2–99.1) |
| anemia | yes | 147 | 94.6% (89.6–97.2) | **0.70** (0.67–0.74) | 93.2% (87.9–96.3) | 43.1% (41.0–45.3) |
| gi_bleeding | partial | 145 | 91.0% (85.3–94.7) | **0.65** (0.61–0.68) | 91.0% (85.3–94.7) | 42.9% (40.8–45.1) |
| diabetic_ketoacidosis | yes | 107 | 9.3% (5.2–16.4) | **0.86** (0.81–0.90) | 3.7% (1.5–9.2) | 100.0% (99.8–100.0) |
| hyperglycemia | yes | 96 | 47.9% (38.2–57.8) | **0.62** (0.57–0.66) | 3.1% (1.1–8.8) | 97.4% (96.7–98.0) |
| acute_myocardial_infarction | yes | 84 | 91.7% (83.8–95.9) | **0.72** (0.66–0.77) | 91.7% (83.8–95.9) | 33.7% (30.0–37.7) |
| hypokalemia | yes | 67 | 22.4% (14.1–33.7) | **0.70** (0.64–0.76) | 0.0% (0.0–5.4) | 100.0% (99.8–100.0) |
| heart_failure | yes | 58 | 87.9% (77.1–94.0) | **0.69** (0.61–0.77) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 0.0% (0.0–6.3) | **0.50** (0.50–0.50) | 0.0% (0.0–6.3) | 100.0% (99.8–100.0) |
| hyponatremia | yes | 52 | 55.8% (42.3–68.4) | **0.85** (0.79–0.90) | 21.2% (12.2–34.0) | 99.3% (98.8–99.6) |
| metabolic_acidosis | yes | 51 | 51.0% (37.7–64.1) | **0.75** (0.66–0.82) | 49.0% (35.9–62.3) | 84.8% (83.2–86.3) |
| hyperkalemia | yes | 49 | 4.1% (1.1–13.7) | **0.92** (0.87–0.96) | 0.0% (0.0–7.3) | 100.0% (99.8–100.0) |
| thrombocytopenia | yes | 40 | 35.0% (22.1–50.5) | **0.88** (0.82–0.92) | 12.5% (5.5–26.1) | 99.1% (98.6–99.4) |
| hypomagnesemia | yes | 37 | 24.3% (13.4–40.1) | **0.61** (0.53–0.68) | 29.7% (17.5–45.8) | 91.0% (89.3–92.5) |
| alcohol_withdrawal | partial | 33 | 33.3% (19.8–50.4) | **0.63** (0.54–0.72) | 0.0% (0.0–10.4) | 100.0% (99.7–100.0) |
| coagulopathy | yes | 28 | 3.6% (0.6–17.7) | **0.60** (0.51–0.69) | 7.1% (2.0–22.6) | 99.7% (99.2–99.9) |
| cirrhosis_liver_failure | partial | 25 | 72.0% (52.4–85.7) | **0.87** (0.79–0.94) | 64.0% (44.5–79.8) | 91.1% (89.6–92.4) |
| hypoglycemia | yes | 21 | 28.6% (13.8–50.0) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 52.6% (31.7–72.7) | **0.70** (0.60–0.82) | 52.6% (31.7–72.7) | 88.3% (85.7–90.5) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.75** (0.63–0.86) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 12.5% (3.5–36.0) | **0.56** (0.40–0.71) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 0.0% (0.0–21.5) | **0.71** (0.58–0.85) | 0.0% (0.0–21.5) | 100.0% (99.8–100.0) |
| rhabdomyolysis | yes | 11 | 72.7% (43.4–90.3) | **0.91** (0.85–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 10.0% (1.8–40.4) | **0.48** (0.43–0.59) | 0.0% (-0.0–27.8) | 100.0% (99.8–100.0) |
| hypothyroidism | yes | 10 | 50.0% (23.7–76.3) | **0.68** (0.52–0.86) | 40.0% (16.8–68.7) | 92.2% (88.5–94.7) |
| hypophosphatemia | yes | 9 | 0.0% (0.0–29.9) | **0.50** (0.49–0.50) | 0.0% (0.0–29.9) | 100.0% (99.5–100.0) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.708 (k=24)
