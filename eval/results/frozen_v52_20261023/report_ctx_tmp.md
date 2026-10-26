# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only + documented history/home medications (pastHistory + medication≤0 min; admissionDx excluded) + within-window time series (ESL ext 11-T)

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 948 ms, p95 1426 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 51.6% (49.6–53.6) (n=2432) | 54.6% (52.3–57.0) (n=1678) |
| top-5 | 66.1% (64.2–67.9) (n=2432) | 69.3% (67.1–71.5) (n=1678) |
| top-10 | 79.8% (78.2–81.4) (n=2432) | 82.8% (81.0–84.6) (n=1678) |

## Context-echo audit (labels whose group is already NAMED in the documented history vs not)

| k | label named in history | label NOT named in history |
|---|---|---|
| top-3 | 56.9% (50.5–63.1) (n=232) | 51.0% (49.0–53.1) (n=2200) |
| top-5 | 72.0% (65.9–77.4) (n=232) | 65.5% (63.4–67.4) (n=2200) |
| top-10 | 87.9% (83.1–91.5) (n=232) | 79.0% (77.2–80.6) (n=2200) |

Stays with any context action: 1616/2314; documented entities confirmed by labs: 786; listed as documented-only: 2159.

## Temporal module: stays with ≥ 1 analyte series 1828/2314; median series per stay 15

| temporal constellation | fired (stays) |
|---|---:|
| acute_myocardial_injury_dynamic_troponin | 332 |
| acute_blood_loss_hb_fall | 198 |
| aki_recovering_creatinine_fall | 165 |
| aki_kdigo_creatinine_rise | 144 |
| chronic_myocardial_injury_flat_troponin | 87 |
| lactate_clearing | 57 |
| hyponatremia_overcorrection | 23 |
| lactate_non_clearance | 12 |
| consumptive_platelet_fall_dic | 11 |
| hit_platelet_fall_on_heparin | 4 |
| hyponatremia_acute_fall | 4 |

## Chart support of confident outputs (p ≥ 0.7): 22.3% (21.2–23.3) of 6089

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 82.2% (77.7–86.0) | **0.81** (0.78–0.83) | 86.2% (82.0–89.5) | 68.5% (66.4–70.5) |
| sepsis | partial | 289 | 47.4% (41.7–53.2) | **0.69** (0.65–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 68.7% (62.7–74.2) | **0.86** (0.84–0.87) | 70.7% (64.8–76.1) | 79.2% (77.3–80.9) |
| acute_kidney_injury | yes | 218 | 74.8% (68.6–80.1) | **0.80** (0.77–0.82) | 83.0% (77.5–87.4) | 72.6% (70.6–74.4) |
| chronic_kidney_disease | yes | 148 | 77.7% (70.3–83.7) | **0.88** (0.85–0.91) | 83.1% (76.3–88.3) | 80.2% (78.4–81.8) |
| anemia | yes | 147 | 81.0% (73.8–86.5) | **0.78** (0.75–0.82) | 95.9% (91.4–98.1) | 39.8% (37.7–41.9) |
| gi_bleeding | partial | 145 | 78.6% (71.3–84.5) | **0.76** (0.72–0.80) | 93.8% (88.6–96.7) | 39.6% (37.5–41.8) |
| diabetic_ketoacidosis | yes | 107 | 62.6% (53.2–71.2) | **0.86** (0.82–0.90) | 63.6% (54.1–72.1) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 56.2% (46.3–65.7) | **0.69** (0.63–0.74) | 55.2% (45.3–64.8) | 75.0% (73.1–76.8) |
| acute_myocardial_infarction | yes | 84 | 95.2% (88.4–98.1) | **0.68** (0.63–0.72) | 94.0% (86.8–97.4) | 27.6% (24.1–31.3) |
| hypokalemia | yes | 67 | 41.8% (30.7–53.7) | **0.72** (0.65–0.77) | 53.7% (41.9–65.1) | 87.8% (86.4–89.1) |
| heart_failure | yes | 58 | 86.2% (75.1–92.8) | **0.70** (0.63–0.76) | 82.8% (71.1–90.4) | 44.9% (38.1–51.9) |
| leukocytosis | yes | 57 | 52.6% (39.9–65.0) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.3% (56.2–60.4) |
| hyponatremia | yes | 52 | 65.4% (51.8–76.8) | **0.89** (0.83–0.93) | 76.9% (63.9–86.3) | 89.5% (88.2–90.7) |
| metabolic_acidosis | yes | 51 | 52.9% (39.5–65.9) | **0.75** (0.66–0.82) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 40.8% (28.2–54.8) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 94.0% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 67.5% (52.0–79.9) | **0.89** (0.84–0.93) | 90.0% (76.9–96.0) | 81.1% (79.4–82.7) |
| hypomagnesemia | yes | 37 | 37.8% (24.1–53.9) | **0.68** (0.60–0.76) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 30.3% (17.4–47.3) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 46.4% (29.5–64.2) | **0.75** (0.64–0.83) | 60.7% (42.4–76.4) | 86.3% (84.1–88.2) |
| cirrhosis_liver_failure | partial | 25 | 56.0% (37.1–73.3) | **0.93** (0.90–0.96) | 72.0% (52.4–85.7) | 89.3% (87.7–90.8) |
| hypoglycemia | yes | 21 | 28.6% (13.8–50.0) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 57.9% (36.3–76.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.74** (0.62–0.85) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.45** (0.30–0.60) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 64.3% (38.8–83.7) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 54.5% (28.0–78.7) | **0.92** (0.87–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 20.0% (5.7–51.0) | **0.63** (0.47–0.77) | 30.0% (10.8–60.3) | 77.9% (76.1–79.5) |
| hypothyroidism | yes | 10 | 50.0% (23.7–76.3) | **0.91** (0.86–0.95) | 50.0% (23.7–76.3) | 91.5% (87.7–94.2) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.91) | 66.7% (35.4–87.9) | 78.4% (75.2–81.3) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.779 (k=24)
