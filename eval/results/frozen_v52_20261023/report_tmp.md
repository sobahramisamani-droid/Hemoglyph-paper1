# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)

**Input arm:** labs only + within-window time series (ESL ext 11-T)

Stays evaluated: 2314 from 186 hospitals; median inputs 31; latency median 1164 ms, p95 1734 ms.

## Recall of clinician-listed diagnoses (key analyte measured)

| k | all groups | lab-detectable groups |
|---|---|---|
| top-3 | 48.7% (46.7–50.7) (n=2432) | 53.2% (50.8–55.6) (n=1678) |
| top-5 | 63.2% (61.2–65.1) (n=2432) | 68.4% (66.1–70.5) (n=1678) |
| top-10 | 77.1% (75.4–78.7) (n=2432) | 81.1% (79.2–82.9) (n=1678) |

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
| hyponatremia_acute_fall | 4 |

## Chart support of confident outputs (p ≥ 0.7): 22.0% (20.9–23.2) of 5168

## Per-group (stays with key analyte measured)

| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---:|---|---|---|---|
| renal_impairment | yes | 326 | 81.9% (77.4–85.7) | **0.79** (0.77–0.82) | 84.4% (80.0–87.9) | 69.6% (67.5–71.6) |
| sepsis | partial | 289 | 47.8% (42.1–53.5) | **0.68** (0.65–0.71) | 52.2% (46.5–57.9) | 82.2% (80.4–83.8) |
| diabetes | partial | 246 | 45.5% (39.4–51.8) | **0.69** (0.66–0.73) | 40.2% (34.3–46.5) | 88.7% (87.2–90.0) |
| acute_kidney_injury | yes | 218 | 78.9% (73.0–83.8) | **0.79** (0.77–0.82) | 83.9% (78.5–88.2) | 70.6% (68.6–72.5) |
| chronic_kidney_disease | yes | 148 | 62.8% (54.8–70.2) | **0.80** (0.76–0.84) | 68.2% (60.4–75.2) | 83.3% (81.7–84.9) |
| anemia | yes | 147 | 83.7% (76.9–88.8) | **0.79** (0.75–0.83) | 95.9% (91.4–98.1) | 39.8% (37.7–41.9) |
| gi_bleeding | partial | 145 | 80.0% (72.8–85.7) | **0.76** (0.72–0.80) | 93.8% (88.6–96.7) | 39.6% (37.5–41.8) |
| diabetic_ketoacidosis | yes | 107 | 62.6% (53.2–71.2) | **0.86** (0.81–0.90) | 63.6% (54.1–72.1) | 98.8% (98.2–99.1) |
| hyperglycemia | yes | 96 | 43.8% (34.3–53.7) | **0.70** (0.64–0.75) | 43.8% (34.3–53.7) | 86.8% (85.3–88.2) |
| acute_myocardial_infarction | yes | 84 | 95.2% (88.4–98.1) | **0.68** (0.63–0.72) | 94.0% (86.8–97.4) | 27.6% (24.1–31.3) |
| hypokalemia | yes | 67 | 41.8% (30.7–53.7) | **0.72** (0.65–0.78) | 53.7% (41.9–65.1) | 87.8% (86.4–89.1) |
| heart_failure | yes | 58 | 84.5% (73.1–91.6) | **0.66** (0.58–0.73) | 77.6% (65.3–86.4) | 50.0% (43.1–56.9) |
| leukocytosis | yes | 57 | 54.4% (41.6–66.6) | **0.73** (0.68–0.77) | 86.0% (74.7–92.7) | 58.3% (56.2–60.4) |
| hyponatremia | yes | 52 | 65.4% (51.8–76.8) | **0.89** (0.83–0.93) | 76.9% (63.9–86.3) | 89.5% (88.1–90.7) |
| metabolic_acidosis | yes | 51 | 52.9% (39.5–65.9) | **0.76** (0.67–0.82) | 58.8% (45.2–71.2) | 82.5% (80.9–84.1) |
| hyperkalemia | yes | 49 | 46.9% (33.7–60.6) | **0.92** (0.87–0.96) | 87.8% (75.8–94.3) | 93.9% (92.9–94.9) |
| thrombocytopenia | yes | 40 | 67.5% (52.0–79.9) | **0.89** (0.84–0.93) | 90.0% (76.9–96.0) | 81.1% (79.4–82.7) |
| hypomagnesemia | yes | 37 | 37.8% (24.1–53.9) | **0.68** (0.60–0.76) | 56.8% (40.9–71.3) | 76.9% (74.5–79.1) |
| alcohol_withdrawal | partial | 33 | 30.3% (17.4–47.3) | **0.65** (0.56–0.75) | 21.2% (10.7–37.8) | 95.7% (94.6–96.7) |
| coagulopathy | yes | 28 | 53.6% (35.8–70.5) | **0.75** (0.65–0.84) | 60.7% (42.4–76.4) | 86.3% (84.1–88.2) |
| cirrhosis_liver_failure | partial | 25 | 52.0% (33.5–70.0) | **0.87** (0.79–0.93) | 64.0% (44.5–79.8) | 89.7% (88.0–91.1) |
| hypoglycemia | yes | 21 | 28.6% (13.8–50.0) | **0.64** (0.55–0.76) | 28.6% (13.8–50.0) | 99.6% (99.2–99.8) |
| lactic_acidosis | yes | 19 | 57.9% (36.3–76.9) | **0.74** (0.63–0.85) | 68.4% (46.0–84.6) | 78.4% (75.1–81.3) |
| acute_pancreatitis | yes | 18 | 66.7% (43.7–83.7) | **0.74** (0.62–0.85) | 66.7% (43.7–83.7) | 81.5% (75.9–86.1) |
| malnutrition | partial | 16 | 0.0% (0.0–19.4) | **0.48** (0.32–0.63) | 0.0% (0.0–19.4) | 100.0% (99.7–100.0) |
| hypernatremia | yes | 14 | 64.3% (38.8–83.7) | **0.88** (0.77–0.99) | 64.3% (38.8–83.7) | 98.2% (97.5–98.7) |
| rhabdomyolysis | yes | 11 | 63.6% (35.4–84.8) | **0.92** (0.86–0.96) | 81.8% (52.3–94.9) | 91.3% (88.5–93.5) |
| hypocalcemia | yes | 10 | 20.0% (5.7–51.0) | **0.63** (0.47–0.77) | 30.0% (10.8–60.3) | 77.9% (76.1–79.5) |
| hypothyroidism | yes | 10 | 50.0% (23.7–76.3) | **0.68** (0.52–0.85) | 40.0% (16.8–68.7) | 91.8% (88.1–94.5) |
| hypophosphatemia | yes | 9 | 22.2% (6.3–54.7) | **0.73** (0.54–0.91) | 66.7% (35.4–87.9) | 78.4% (75.2–81.3) |

Mean AUROC over lab-detectable groups with ≥ 5 listed stays: 0.765 (k=24)
