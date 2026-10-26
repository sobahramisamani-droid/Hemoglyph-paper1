# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 1001 ms, p95 1521 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 34.7% (32.9–36.7) (n=2432) | 35.2% (32.9–37.5) (n=1678) |
| top-5 | 48.7% (46.7–50.7) (n=2432) | 50.8% (48.4–53.2) (n=1678) |
| top-10 | 67.0% (65.1–68.8) (n=2432) | 69.7% (67.4–71.8) (n=1678) |

## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)

| k | all groups |
|---|---|
| top-1 | 25.7% (24.0–27.4) (n=2432) |
| top-3 | 45.8% (43.9–47.8) (n=2432) |
| top-5 | 57.6% (55.6–59.6) (n=2432) |

## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position

| k | all groups |
|---|---|
| top-1 | 19.5% (18.0–21.2) (n=2432) |
| top-3 | 37.3% (35.4–39.3) (n=2432) |
| top-5 | 51.1% (49.1–53.1) (n=2432) |
| top-10 | 67.8% (65.9–69.6) (n=2432) |

## Chart support of confident outputs (p ≥ 0.7): 30.8% (22.7–40.2) of 104

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 64.7% (59.4–69.7) | **0.78** (0.75–0.80) | 20.9% (16.8–25.6) | 94.6% (93.5–95.6) |
| sepsis | partial | 289 | 4.8% (2.9–8.0) | **0.60** (0.57–0.64) | 0.0% (0.0–1.3) | 100.0% (99.8–100.0) |
| diabetes | partial | 246 | 66.3% (60.1–71.9) | **0.59** (0.56–0.63) | 0.0% (0.0–1.5) | 100.0% (99.8–100.0) |
| acute_kidney_injury | yes | 218 | 64.7% (58.1–70.7) | **0.80** (0.77–0.83) | 26.1% (20.8–32.4) | 94.4% (93.4–95.3) |
| chronic_kidney_disease | yes | 148 | 31.1% (24.2–38.9) | **0.71** (0.67–0.75) | 0.0% (0.0–2.5) | 100.0% (99.7–100.0) |
| anemia | yes | 147 | 91.8% (86.3–95.3) | **0.69** (0.65–0.73) | 23.8% (17.6–31.3) | 86.9% (85.4–88.3) |
| gi_bleeding | partial | 145 | 89.0% (82.8–93.1) | **0.63** (0.59–0.67) | 16.6% (11.4–23.4) | 87.0% (85.5–88.4) |
| diabetic_ketoacidosis | yes | 107 | 75.7% (66.8–82.8) | **0.86** (0.82–0.90) | 30.8% (22.9–40.1) | 99.4% (98.9–99.6) |
| hyperglycemia | yes | 96 | 64.6% (54.6–73.4) | **0.58** (0.53–0.63) | 0.0% (0.0–3.8) | 100.0% (99.8–100.0) |
| acute_myocardial_infarction | yes | 84 | 0.0% (0.0–4.4) | **0.50** (0.50–0.50) | 0.0% (0.0–4.4) | 100.0% (99.3–100.0) |
| hypokalemia | yes | 67 | 44.8% (33.5–56.6) | **0.71** (0.64–0.76) | 0.0% (0.0–5.4) | 100.0% (99.8–100.0) |
| heart_failure | yes | 58 | 46.6% (34.3–59.2) | **0.60** (0.52–0.68) | 0.0% (0.0–6.2) | 100.0% (98.1–100.0) |
| leukocytosis | yes | 57 | 0.0% (0.0–6.3) | **0.50** (0.50–0.50) | 0.0% (0.0–6.3) | 100.0% (99.8–100.0) |
| hyponatremia | yes | 52 | 75.0% (61.8–84.8) | **0.85** (0.79–0.90) | 0.0% (0.0–6.9) | 100.0% (99.8–100.0) |
| metabolic_acidosis | yes | 51 | 70.6% (57.0–81.3) | **0.75** (0.67–0.81) | 37.3% (25.3–51.0) | 88.3% (86.9–89.6) |
| hyperkalemia | yes | 49 | 12.2% (5.7–24.2) | **0.90** (0.86–0.95) | 0.0% (0.0–7.3) | 100.0% (99.8–100.0) |
| thrombocytopenia | yes | 40 | 32.5% (20.1–48.0) | **0.88** (0.84–0.91) | 0.0% (-0.0–8.8) | 100.0% (99.8–100.0) |
| hypomagnesemia | yes | 37 | 0.0% (0.0–9.4) | **0.50** (0.50–0.50) | 0.0% (0.0–9.4) | 100.0% (99.7–100.0) |
| alcohol_withdrawal | partial | 33 | 0.0% (0.0–10.4) | **0.50** (0.50–0.50) | 0.0% (0.0–10.4) | 100.0% (99.7–100.0) |
| coagulopathy | yes | 28 | 10.7% (3.7–27.2) | **0.55** (0.47–0.66) | 7.1% (2.0–22.6) | 99.6% (99.0–99.9) |
| cirrhosis_liver_failure | partial | 25 | 76.0% (56.6–88.5) | **0.85** (0.75–0.93) | 60.0% (40.7–76.6) | 93.4% (92.0–94.5) |
| hypoglycemia | yes | 21 | 0.0% (0.0–15.5) | **0.50** (0.50–0.50) | 0.0% (0.0–15.5) | 100.0% (99.8–100.0) |
| lactic_acidosis | yes | 19 | 0.0% (0.0–16.8) | **0.50** (0.50–0.50) | 0.0% (0.0–16.8) | 100.0% (99.4–100.0) |
| acute_pancreatitis | yes | 18 | 50.0% (29.0–71.0) | **0.75** (0.63–0.86) | 16.7% (5.8–39.2) | 97.7% (94.8–99.0) |
| malnutrition | partial | 16 | 43.8% (23.1–66.8) | **0.56** (0.40–0.71) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 0.0% (0.0–21.5) | **0.50** (0.50–0.50) | 0.0% (0.0–21.5) | 100.0% (99.8–100.0) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.83** (0.77–0.89) | 9.1% (1.6–37.7) | 97.7% (95.9–98.7) |
| hypocalcemia | yes | 10 | 30.0% (10.8–60.3) | **0.52** (0.38–0.66) | 0.0% (-0.0–27.8) | 100.0% (99.8–100.0) |
| hypothyroidism | yes | 10 | 50.0% (23.7–76.3) | **0.70** (0.54–0.87) | 40.0% (16.8–68.7) | 92.5% (88.9–95.0) |
| hypophosphatemia | yes | 9 | 0.0% (0.0–29.9) | **0.50** (0.50–0.50) | 0.0% (0.0–29.9) | 100.0% (99.5–100.0) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.664 (k=24)
