## Calibration of group-level probabilities (entity present in differential)

Pairs: 17332; label prevalence 0.107; mean probability 0.511; **ECE 0.404**; logistic recalibration slope 0.47, intercept -2.21 (slope < 1 and negative intercept = over-confidence).
Split-half: recalibration fitted on odd stays, applied to even stays: ECE 0.401 → 0.031.

| bin mean p | observed rate | n |
|---|---|---|
| 0.19 | 0.05 | 1733 |
| 0.28 | 0.07 | 1733 |
| 0.37 | 0.05 | 1733 |
| 0.45 | 0.06 | 1733 |
| 0.49 | 0.07 | 1734 |
| 0.56 | 0.11 | 1733 |
| 0.60 | 0.19 | 1733 |
| 0.63 | 0.09 | 1733 |
| 0.68 | 0.17 | 1733 |
| 0.85 | 0.21 | 1734 |

## Baseline B1 — raw analyte value vs. Hemoglyph group probability (same stays)

| group | n listed / not | B1 analyte (cut-off) | B1 AUROC | B1 sens/spec | Hemoglyph AUROC | Hemoglyph sens/spec @0.5 |
|---|---|---|---|---|---|---|
| hyperkalemia | 49 / 2195 | potassium (>5.1) | 0.96 | 88% / 92% | 0.92 | 88% / 94% |
| hypokalemia | 67 / 2177 | potassium (<3.5) | 0.77 | 54% / 88% | 0.72 | 54% / 88% |
| hyponatremia | 52 / 2215 | sodium (<135) | 0.91 | 88% / 80% | 0.89 | 81% / 88% |
| hypernatremia | 14 / 2253 | sodium (>145) | 0.88 | 86% / 94% | 0.88 | 64% / 98% |
| hypomagnesemia | 37 / 1255 | magnesium (<1.7) | 0.73 | 57% / 77% | 0.67 | 57% / 77% |
| hypocalcemia | 10 / 2187 | calcium_total (<8.5) | 0.68 | 70% / 58% | 0.67 | 70% / 62% |
| hypophosphatemia | 9 / 704 | phosphate (<2.5) | 0.82 | 67% / 78% | 0.73 | 67% / 78% |
| anemia | 147 / 2060 | hemoglobin (<12.0) | 0.83 | 90% / 53% | 0.70 | 93% / 44% |
| thrombocytopenia | 40 / 2141 | platelet_count (<150) | 0.90 | 92% / 80% | 0.87 | 90% / 81% |
| leukocytosis | 57 / 2158 | white_blood_cell_count (>11.0) | 0.78 | 86% / 56% | 0.50 | 0% / 100% |
| metabolic_acidosis | 51 / 2120 | bicarbonate (<22) | 0.76 | 71% / 75% | 0.75 | 55% / 83% |
| lactic_acidosis | 19 / 676 | lactate (>2.0) | 0.82 | 95% / 54% | 0.73 | 68% / 79% |
| acute_kidney_injury | 218 / 2048 | creatinine (>1.3) | 0.82 | 83% / 70% | 0.77 | 73% / 75% |
| renal_impairment | 326 / 1940 | creatinine (>1.3) | 0.85 | 81% / 73% | 0.76 | 75% / 74% |
| hyperglycemia | 96 / 2151 | glucose (>180) | 0.70 | 51% / 78% | 0.70 | 41% / 87% |
| diabetes | 246 / 2001 | glucose (>200) | 0.71 | 46% / 86% | 0.69 | 40% / 89% |
| hypothyroidism | 10 / 294 | thyroid_stimulating_hormone (>4.5) | 0.81 | 50% / 92% | 0.68 | 40% / 92% |
| acute_pancreatitis | 18 / 222 | lipase (>180) | 0.80 | 67% / 82% | 0.74 | 67% / 82% |
| acute_myocardial_infarction | 72 / 504 | troponin_i (>0.04) | 0.79 | 93% / 31% | 0.69 | 78% / 43% |
| heart_failure | 58 / 196 | b_type_natriuretic_peptide (>100) | 0.71 | 93% / 23% | 0.65 | 78% / 50% |
| rhabdomyolysis | 11 / 473 | creatine_kinase_total (>1000) | 0.94 | 82% / 91% | 0.92 | 82% / 91% |
| coagulopathy | 28 / 1051 | international_normalized_ratio (>1.5) | 0.84 | 75% / 76% | 0.58 | 7% / 100% |

## Safety S5 — critical values captured in top-5

| critical value | n stays | entity in top-5 |
|---|---|---|
| potassium >= 6.5 | 32 | 96.9% (84.3–99.4) |
| potassium <= 2.5 | 10 | 100.0% (72.2–100.0) |
| sodium <= 120 | 29 | 100.0% (88.3–100.0) |
| sodium >= 160 | 7 | 100.0% (64.6–100.0) |
| glucose <= 50 | 11 | 100.0% (74.1–100.0) |
| glucose >= 500 | 69 | 94.2% (86.0–97.7) |
| calcium_total >= 14 | 1 | 100.0% (20.7–100.0) |
| lactate >= 4 | 120 | 99.2% (95.4–99.9) |
| arterial_ph <= 7.2 | 124 | 85.5% (78.2–90.6) |
| hemoglobin <= 6 | 27 | 85.2% (67.5–94.1) |
| platelet_count <= 20 | 8 | 25.0% (7.1–59.1) |
| white_blood_cell_count >= 100 | 1 | 0.0% (0.0–79.3) |
| **all** | 439 | 92.0% (89.1–94.2) |
