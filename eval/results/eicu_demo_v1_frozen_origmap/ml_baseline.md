# Baseline B2 — supervised models trained on the same eICU inputs (5-fold out-of-fold)

| group | n listed | HGB AUROC (95% CI) | LogReg AUROC | Hemoglyph AUROC (untrained) |
|---|---:|---|---|---|
| acute_kidney_injury | 218 | 0.83 (0.80–0.86) | 0.72 | 0.77 |
| chronic_kidney_disease | 148 | 0.79 (0.74–0.83) | 0.77 | 0.73 |
| renal_impairment | 326 | 0.83 (0.80–0.85) | 0.77 | 0.76 |
| diabetes | 246 | 0.75 (0.71–0.78) | 0.67 | 0.69 |
| hyperglycemia | 96 | 0.78 (0.73–0.82) | 0.64 | 0.70 |
| diabetic_ketoacidosis | 107 | 0.96 (0.93–0.98) | 0.95 | 0.85 |
| hypoglycemia | 21 | 0.76 (0.63–0.85) | 0.51 | 0.64 |
| hypokalemia | 67 | 0.76 (0.70–0.82) | 0.79 | 0.72 |
| hyperkalemia | 49 | 0.91 (0.84–0.96) | 0.93 | 0.92 |
| hyponatremia | 52 | 0.85 (0.79–0.90) | 0.85 | 0.89 |
| hypomagnesemia | 37 | 0.59 (0.50–0.67) | 0.66 | 0.67 |
| metabolic_acidosis | 51 | 0.75 (0.67–0.83) | 0.69 | 0.75 |
| lactic_acidosis | 19 | 0.58 (0.48–0.70) | 0.69 | 0.73 |
| anemia | 147 | 0.79 (0.75–0.83) | 0.79 | 0.70 |
| thrombocytopenia | 40 | 0.85 (0.79–0.90) | 0.84 | 0.87 |
| leukocytosis | 57 | 0.71 (0.65–0.77) | 0.62 | 0.50 |
| sepsis | 289 | 0.82 (0.80–0.84) | 0.73 | 0.63 |
| cirrhosis_liver_failure | 25 | 0.83 (0.74–0.91) | 0.75 | 0.87 |
| acute_pancreatitis | 18 | 0.67 (0.53–0.80) | 0.60 | 0.74 |
| acute_myocardial_infarction | 84 | 0.73 (0.66–0.78) | 0.63 | 0.67 |
| heart_failure | 58 | 0.58 (0.50–0.66) | 0.64 | 0.65 |
| coagulopathy | 28 | 0.81 (0.73–0.88) | 0.74 | 0.58 |
| malnutrition | 16 | 0.66 (0.53–0.78) | 0.40 | 0.48 |
| gi_bleeding | 145 | 0.85 (0.81–0.89) | 0.84 | 0.65 |
| alcohol_withdrawal | 33 | 0.80 (0.71–0.88) | 0.80 | 0.54 |
