## Calibration of group-level probabilities (entity present in differential)

Pairs: 18616; label prevalence 0.107; mean probability 0.550; **ECE 0.444**; logistic recalibration slope 0.69, intercept -2.41 (slope < 1 and negative intercept = over-confidence).
Split-half: recalibration fitted on odd stays, applied to even stays: ECE 0.437 → 0.025.

| bin mean p | observed rate | n |
|---|---|---|
| 0.21 | 0.03 | 1861 |
| 0.32 | 0.04 | 1862 |
| 0.42 | 0.05 | 1861 |
| 0.48 | 0.05 | 1862 |
| 0.53 | 0.08 | 1862 |
| 0.59 | 0.07 | 1861 |
| 0.63 | 0.10 | 1862 |
| 0.69 | 0.18 | 1861 |
| 0.78 | 0.23 | 1862 |
| 0.86 | 0.25 | 1862 |

## Baseline B1 — raw analyte value vs. Hemoglyph group probability (same stays)

| group | n listed / not | B1 analyte (cut-off) | B1 AUROC | B1 sens/spec | Hemoglyph AUROC | Hemoglyph sens/spec @0.5 |
|---|---|---|---|---|---|---|
| hyperkalemia | 49 / 2195 | potassium (>5.1) | 0.96 | 88% / 92% | 0.92 | 88% / 94% |
| hypokalemia | 67 / 2177 | potassium (<3.5) | 0.77 | 54% / 88% | 0.72 | 54% / 88% |
| hyponatremia | 52 / 2215 | sodium (<135) | 0.91 | 88% / 80% | 0.89 | 77% / 90% |
| hypernatremia | 14 / 2253 | sodium (>145) | 0.88 | 86% / 94% | 0.88 | 64% / 98% |
| hypomagnesemia | 37 / 1255 | magnesium (<1.7) | 0.73 | 57% / 77% | 0.68 | 57% / 77% |
| hypocalcemia | 10 / 2187 | calcium_total (<8.5) | 0.68 | 70% / 58% | 0.63 | 30% / 78% |
| hypophosphatemia | 9 / 704 | phosphate (<2.5) | 0.82 | 67% / 78% | 0.73 | 67% / 78% |
| anemia | 147 / 2060 | hemoglobin (<12.0) | 0.83 | 90% / 53% | 0.78 | 93% / 44% |
| thrombocytopenia | 40 / 2141 | platelet_count (<150) | 0.90 | 92% / 80% | 0.89 | 90% / 81% |
| leukocytosis | 57 / 2158 | white_blood_cell_count (>11.0) | 0.78 | 86% / 56% | 0.73 | 86% / 58% |
| metabolic_acidosis | 51 / 2120 | bicarbonate (<22) | 0.76 | 71% / 75% | 0.76 | 59% / 83% |
| lactic_acidosis | 19 / 676 | lactate (>2.0) | 0.82 | 95% / 54% | 0.74 | 68% / 78% |
| acute_kidney_injury | 218 / 2048 | creatinine (>1.3) | 0.82 | 83% / 70% | 0.80 | 80% / 73% |
| renal_impairment | 326 / 1940 | creatinine (>1.3) | 0.85 | 81% / 73% | 0.80 | 81% / 72% |
| hyperglycemia | 96 / 2151 | glucose (>180) | 0.70 | 51% / 78% | 0.70 | 44% / 87% |
| diabetes | 246 / 2001 | glucose (>200) | 0.71 | 46% / 86% | 0.69 | 40% / 89% |
| hypothyroidism | 10 / 294 | thyroid_stimulating_hormone (>4.5) | 0.81 | 50% / 92% | 0.68 | 40% / 92% |
| acute_pancreatitis | 18 / 222 | lipase (>180) | 0.80 | 67% / 82% | 0.74 | 67% / 82% |
| acute_myocardial_infarction | 72 / 504 | troponin_i (>0.04) | 0.79 | 93% / 31% | 0.72 | 81% / 42% |
| heart_failure | 58 / 196 | b_type_natriuretic_peptide (>100) | 0.71 | 93% / 23% | 0.66 | 78% / 50% |
| rhabdomyolysis | 11 / 473 | creatine_kinase_total (>1000) | 0.94 | 82% / 91% | 0.92 | 82% / 91% |
| coagulopathy | 28 / 1051 | international_normalized_ratio (>1.5) | 0.84 | 75% / 76% | 0.75 | 61% / 87% |

## Safety S5 — critical values captured in top-5

| critical value | n stays | entity in top-5 |
|---|---|---|
| potassium >= 6.5 | 32 | 71.9% (54.6–84.4) |
| potassium <= 2.5 | 10 | 100.0% (72.2–100.0) |
| sodium <= 120 | 29 | 100.0% (88.3–100.0) |
| sodium >= 160 | 7 | 100.0% (64.6–100.0) |
| glucose <= 50 | 11 | 100.0% (74.1–100.0) |
| glucose >= 500 | 69 | 95.7% (88.0–98.5) |
| calcium_total >= 14 | 1 | 100.0% (20.7–100.0) |
| lactate >= 4 | 120 | 100.0% (96.9–100.0) |
| arterial_ph <= 7.2 | 124 | 93.5% (87.8–96.7) |
| hemoglobin <= 6 | 27 | 96.3% (81.7–99.3) |
| platelet_count <= 20 | 8 | 100.0% (67.6–100.0) |
| white_blood_cell_count >= 100 | 1 | 100.0% (20.7–100.0) |
| **all** | 439 | 95.2% (92.8–96.9) |
