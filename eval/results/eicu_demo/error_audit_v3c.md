# Structured error audit — eICU-CRD demo, engine v3 (ext6c)

Population: every (stay, clinician-listed group) pair with the key analyte measured and the group absent from the top-5 (N = 1269 misses across 2314 stays). A fixed-seed random sample of 200 misses was classified with a pre-declared, deterministic taxonomy (see script header); no manual relabelling.

| Category | n | % of sampled misses |
|---|---:|---:|
| A — not supported by the measured laboratory values (label = history/clinical context) | 119 | 59.5% |
| B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings | 39 | 19.5% |
| C1 — knowledge/logic miss: laboratory signature present, entity never proposed | 21 | 10.5% |
| C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5 | 21 | 10.5% |
| D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited) | 0 | 0.0% |

**Interpretation.** 119 / 200 (60%) of misses carry no laboratory signature of the listed condition and are not recoverable by any laboratory-only system without inventing evidence; 81 (40%) are in principle recoverable (engine-side), of which 21 are knowledge/logic gaps, 21 scoring/severity defects and 39 ranking displacements caused by the five-slot cut-off; 0 reflect the evaluation label map rather than the engine.

## By clinician-listed group (sampled misses)

| group | n | A | B | C1 | C2 | D |
|---|---:|---:|---:|---:|---:|---:|
| sepsis | 37 | 19 | 4 | 9 | 5 | 0 |
| chronic_kidney_disease | 22 | 4 | 2 | 5 | 11 | 0 |
| heart_failure | 22 | 21 | 0 | 0 | 1 | 0 |
| diabetes | 19 | 17 | 2 | 0 | 0 | 0 |
| renal_impairment | 12 | 6 | 4 | 1 | 1 | 0 |
| acute_kidney_injury | 11 | 2 | 9 | 0 | 0 | 0 |
| diabetic_ketoacidosis | 9 | 7 | 2 | 0 | 0 | 0 |
| hyperglycemia | 8 | 4 | 4 | 0 | 0 | 0 |
| acute_myocardial_infarction | 6 | 4 | 0 | 2 | 0 | 0 |
| hypothyroidism | 6 | 6 | 0 | 0 | 0 | 0 |
| hypokalemia | 5 | 4 | 1 | 0 | 0 | 0 |
| alcohol_withdrawal | 4 | 2 | 0 | 2 | 0 | 0 |
| gi_bleeding | 4 | 2 | 1 | 1 | 0 | 0 |
| anemia | 4 | 2 | 2 | 0 | 0 | 0 |
| metabolic_acidosis | 4 | 3 | 0 | 0 | 1 | 0 |
| coagulopathy | 4 | 3 | 0 | 0 | 1 | 0 |
| hypoglycemia | 3 | 3 | 0 | 0 | 0 | 0 |
| leukocytosis | 3 | 1 | 2 | 0 | 0 | 0 |
| hyperkalemia | 3 | 0 | 3 | 0 | 0 | 0 |
| malnutrition | 3 | 3 | 0 | 0 | 0 | 0 |
| hypocalcemia | 2 | 1 | 0 | 0 | 1 | 0 |
| hypomagnesemia | 2 | 1 | 1 | 0 | 0 | 0 |
| acute_pancreatitis | 2 | 2 | 0 | 0 | 0 | 0 |
| thrombocytopenia | 2 | 1 | 1 | 0 | 0 | 0 |
| hyponatremia | 2 | 1 | 1 | 0 | 0 | 0 |
| lactic_acidosis | 1 | 0 | 0 | 1 | 0 | 0 |

## Examples (first six per category, verbatim engine outputs)

**A — not supported by the measured laboratory values (label = history/clinical context)**
- stay 1323983 (53m) coded **hypokalemia** rank=None p=0.00; top-5 ['diabetic_ketoacidosis', 'metabolic_acidosis', 'diabetes_mellitus', 'hyponatremia', 'type_2_diabetes']; key values {'creatinine': 1.26, 'glucose': 473.0, 'bicarbonate': 11.0, 'potassium': 5.0, 'sodium': 127.0, 'hemoglobin': 15.2, 'platelet_count': 230.0, 'white_blood_cell_count': 11.8, 'lactate': 1.3, 'albumin': 4.1, 'international_normalized_ratio': 0.99}
- stay 1785133 (67m) coded **diabetes** rank=None p=0.00; top-5 ['heart_failure', 'cardiorenal_syndrome', 'acute_kidney_injury', 'malnutrition', 'hyperchloremia']; key values {'creatinine': 0.98, 'glucose': 96.0, 'bicarbonate': 29.0, 'potassium': 4.4, 'sodium': 139.0, 'hemoglobin': 15.4, 'platelet_count': 229.0, 'white_blood_cell_count': 7.5, 'albumin': 3.3, 'international_normalized_ratio': 1.03, 'troponin_i': 0.04, 'b_type_natriuretic_peptide': 418.0}
- stay 1568171 (84m) coded **sepsis** rank=None p=0.00; top-5 ['acute_kidney_injury', 'anemia', 'hyponatremia', 'respiratory_acidosis', 'chronic_kidney_disease']; key values {'creatinine': 2.13, 'glucose': 165.0, 'bicarbonate': 27.0, 'potassium': 5.6, 'sodium': 129.0, 'hemoglobin': 8.6, 'platelet_count': 208.0, 'white_blood_cell_count': 8.55, 'lactate': 1.2, 'albumin': 3.3, 'international_normalized_ratio': 1.2}
- stay 2826676 (68m) coded **sepsis** rank=12 p=0.49; top-5 ['acute_myocardial_injury', 'metabolic_acidosis', 'hyponatremia', 'acute_kidney_injury', 'leukocytosis_pattern']; key values {'creatinine': 1.61, 'glucose': 208.0, 'bicarbonate': 17.0, 'potassium': 3.7, 'sodium': 126.0, 'hemoglobin': 15.8, 'platelet_count': 128.0, 'white_blood_cell_count': 11.3, 'albumin': 3.1, 'international_normalized_ratio': 1.2, 'troponin_i': 0.06}
- stay 2778495 (64m) coded **heart_failure** rank=None p=0.00; top-5 ['diabetes_mellitus', 'acute_kidney_injury', 'leukocytosis_pattern', 'hyperkalemia', 'chronic_kidney_disease']; key values {'creatinine': 1.67, 'glucose': 268.0, 'bicarbonate': 24.0, 'potassium': 6.0, 'sodium': 133.0, 'hemoglobin': 14.9, 'platelet_count': 169.0, 'white_blood_cell_count': 12.7, 'lactate': 0.9, 'albumin': 3.7, 'international_normalized_ratio': 1.1}
- stay 2792350 (69m) coded **heart_failure** rank=None p=0.00; top-5 ['acute_kidney_injury', 'acute_myocardial_injury', 'anemia', 'leukocytosis_pattern', 'hyperchloremia']; key values {'creatinine': 2.8, 'glucose': 80.0, 'bicarbonate': 20.0, 'potassium': 3.6, 'sodium': 144.0, 'hemoglobin': 10.6, 'platelet_count': 232.0, 'white_blood_cell_count': 12.6, 'albumin': 1.2, 'troponin_i': 0.1}

**B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings**
- stay 1090039 (77m) coded **renal_impairment** rank=6 p=0.68; top-5 ['lactic_acidosis', 'metabolic_acidosis', 'hepatocellular_injury_pattern', 'hypokalemia', 'sepsis']; key values {'creatinine': 1.9, 'glucose': 262.0, 'bicarbonate': 14.0, 'potassium': 2.8, 'sodium': 140.0, 'hemoglobin': 13.1, 'platelet_count': 207.0, 'white_blood_cell_count': 8.5, 'lactate': 7.4, 'albumin': 3.7, 'international_normalized_ratio': 1.2, 'troponin_i': 0.06}
- stay 1751224 (83m) coded **hypokalemia** rank=7 p=0.63; top-5 ['thalassemia_trait', 'beta_thalassemia_minor', 'beta_thalassemia_trait', 'acute_myocardial_injury', 'metabolic_acidosis']; key values {'creatinine': 1.75, 'glucose': 137.0, 'bicarbonate': 20.0, 'potassium': 3.4, 'sodium': 139.0, 'hemoglobin': 18.8, 'platelet_count': 513.0, 'white_blood_cell_count': 25.6, 'albumin': 4.6, 'international_normalized_ratio': 1.56, 'troponin_i': 0.05}
- stay 3149587 (26m) coded **acute_kidney_injury** rank=6 p=0.62; top-5 ['respiratory_acidosis', 'sepsis', 'thrombocytopenia', 'diabetes_mellitus', 'hypokalemia']; key values {'creatinine': 2.1, 'glucose': 479.0, 'bicarbonate': 21.0, 'potassium': 3.4, 'sodium': 138.0, 'hemoglobin': 14.8, 'platelet_count': 36.0, 'white_blood_cell_count': 22.0, 'albumin': 3.9, 'b_type_natriuretic_peptide': 197.0}
- stay 958720 (34m) coded **sepsis** rank=6 p=0.72; top-5 ['respiratory_acidosis', 'acute_kidney_injury', 'acute_myocardial_injury', 'elevated_inr_pattern', 'anemia']; key values {'creatinine': 2.93, 'glucose': 107.0, 'bicarbonate': 30.0, 'potassium': 3.9, 'sodium': 139.0, 'hemoglobin': 8.4, 'platelet_count': 190.0, 'white_blood_cell_count': 14.9, 'albumin': 1.8, 'international_normalized_ratio': 2.8, 'troponin_i': 0.04}
- stay 1546668 (73m) coded **sepsis** rank=6 p=0.72; top-5 ['hypernatremia', 'hypomagnesemia', 'lactic_acidosis', 'acute_kidney_injury', 'metabolic_acidosis']; key values {'creatinine': 7.37, 'glucose': 165.0, 'bicarbonate': 10.0, 'potassium': 4.8, 'sodium': 178.0, 'hemoglobin': 9.4, 'platelet_count': 308.0, 'white_blood_cell_count': 9.8, 'lactate': 6.9, 'albumin': 2.3, 'international_normalized_ratio': 1.4}
- stay 2740440 (65m) coded **leukocytosis** rank=9 p=0.59; top-5 ['lactic_acidosis', 'sepsis', 'diabetic_ketoacidosis', 'metabolic_acidosis', 'acute_kidney_injury']; key values {'creatinine': 1.49, 'glucose': 658.0, 'bicarbonate': 6.0, 'potassium': 4.8, 'sodium': 128.0, 'hemoglobin': 16.7, 'platelet_count': 338.0, 'white_blood_cell_count': 19.6, 'lactate': 4.0, 'albumin': 4.7}

**C1 — knowledge/logic miss: laboratory signature present, entity never proposed**
- stay 2825734 (64m) coded **sepsis** rank=None p=0.00; top-5 ['nephrotic_syndrome', 'leukocytosis_pattern', 'anemia', 'hyperchloremia', 'hypocalcemia']; key values {'creatinine': 1.09, 'glucose': 102.0, 'bicarbonate': 27.0, 'potassium': 3.8, 'sodium': 144.0, 'hemoglobin': 12.9, 'platelet_count': 195.0, 'white_blood_cell_count': 16.7, 'albumin': 2.8, 'international_normalized_ratio': 1.2}
- stay 3085970 (62m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['immune_thrombocytopenia', 'acute_pancreatitis', 'hepatocellular_injury_pattern', 'hypokalemia', 'thrombocytopenia']; key values {'creatinine': 0.72, 'glucose': 79.0, 'bicarbonate': 28.0, 'potassium': 2.5, 'sodium': 129.0, 'hemoglobin': 13.3, 'platelet_count': 49.0, 'white_blood_cell_count': 9.9, 'albumin': 3.3, 'troponin_i': 0.509}
- stay 1794248 (41f) coded **gi_bleeding** rank=None p=0.00; top-5 ['hypernatremia', 'hypokalemia', 'acute_kidney_injury', 'hyperchloremia', 'cystic_fibrosis']; key values {'creatinine': 2.21, 'glucose': 96.0, 'potassium': 2.7, 'sodium': 154.0, 'albumin': 1.9}
- stay 2778495 (64m) coded **sepsis** rank=None p=0.00; top-5 ['diabetes_mellitus', 'acute_kidney_injury', 'leukocytosis_pattern', 'hyperkalemia', 'chronic_kidney_disease']; key values {'creatinine': 1.67, 'glucose': 268.0, 'bicarbonate': 24.0, 'potassium': 6.0, 'sodium': 133.0, 'hemoglobin': 14.9, 'platelet_count': 169.0, 'white_blood_cell_count': 12.7, 'lactate': 0.9, 'albumin': 3.7, 'international_normalized_ratio': 1.1}
- stay 162841 (84f) coded **chronic_kidney_disease** rank=None p=0.00; top-5 ['acute_kidney_injury', 'acute_hepatitis', 'hepatocellular_injury_pattern', 'elevated_inr_pattern', 'sepsis']; key values {'creatinine': 2.34, 'glucose': 95.0, 'bicarbonate': 18.0, 'potassium': 3.2, 'sodium': 146.0, 'hemoglobin': 10.4, 'platelet_count': 136.0, 'white_blood_cell_count': 19.7, 'lactate': 1.7, 'albumin': 2.2, 'international_normalized_ratio': 2.1}
- stay 2552038 (73f) coded **sepsis** rank=None p=0.00; top-5 ['chronic_leukemia_support_pattern', 'leukocytosis_pattern', 'nephrotic_syndrome', 'anemia', 'diabetes_mellitus']; key values {'creatinine': 0.87, 'glucose': 373.0, 'bicarbonate': 22.0, 'potassium': 4.9, 'sodium': 128.0, 'hemoglobin': 8.2, 'platelet_count': 127.0, 'white_blood_cell_count': 469.8, 'lactate': 1.4, 'albumin': 2.7, 'international_normalized_ratio': 1.3}

**C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5**
- stay 3136458 (72f) coded **hypocalcemia** rank=8 p=0.45; top-5 ['acute_myocardial_infarction', 'heart_failure', 'cardiorenal_syndrome', 'prerenal_azotemia', 'anemia']; key values {'creatinine': 2.0, 'glucose': 89.0, 'bicarbonate': 20.0, 'potassium': 4.2, 'sodium': 137.0, 'hemoglobin': 11.3, 'platelet_count': 192.0, 'white_blood_cell_count': 11.2, 'lactate': 1.2, 'albumin': 1.4, 'troponin_i': 0.11, 'b_type_natriuretic_peptide': 11618.0}
- stay 589909 (34m) coded **chronic_kidney_disease** rank=13 p=0.43; top-5 ['respiratory_acidosis', 'sepsis', 'acute_kidney_injury', 'hyperkalemia', 'leukocytosis_pattern']; key values {'creatinine': 4.5, 'glucose': 91.0, 'bicarbonate': 25.0, 'potassium': 6.4, 'sodium': 136.0, 'hemoglobin': 12.6, 'platelet_count': 350.0, 'white_blood_cell_count': 17.2, 'lactate': 1.4, 'albumin': 2.1, 'international_normalized_ratio': 1.8, 'troponin_i': 0.02}
- stay 958719 (34m) coded **chronic_kidney_disease** rank=17 p=0.20; top-5 ['respiratory_acidosis', 'acute_kidney_injury', 'anemia', 'thrombocytopenia', 'copd']; key values {'creatinine': 4.3, 'glucose': 89.0, 'bicarbonate': 32.0, 'potassium': 4.4, 'sodium': 139.0, 'hemoglobin': 8.6, 'platelet_count': 132.0, 'white_blood_cell_count': 5.4, 'lactate': 0.6, 'albumin': 1.4, 'international_normalized_ratio': 1.5}
- stay 2681532 (73m) coded **sepsis** rank=8 p=0.13; top-5 ['leukocytosis_pattern', 'acute_myocardial_infarction', 'type_2_diabetes', 'malnutrition', 'bacterial_infection']; key values {'creatinine': 1.11, 'glucose': 124.0, 'bicarbonate': 35.0, 'potassium': 5.1, 'sodium': 142.0, 'hemoglobin': 13.5, 'platelet_count': 208.0, 'white_blood_cell_count': 16.9, 'albumin': 3.3, 'troponin_i': 0.4}
- stay 2894029 (55f) coded **sepsis** rank=7 p=0.23; top-5 ['anemia', 'pellagra', 'frailty', 'malnutrition', 'bacterial_infection']; key values {'creatinine': 0.79, 'glucose': 181.0, 'bicarbonate': 23.7, 'potassium': 3.6, 'sodium': 138.0, 'hemoglobin': 10.9, 'platelet_count': 184.0, 'white_blood_cell_count': 11.0, 'lactate': 2.1, 'albumin': 2.5}
- stay 399365 (49m) coded **chronic_kidney_disease** rank=16 p=0.21; top-5 ['acute_kidney_injury', 'diabetic_ketoacidosis', 'sepsis', 'diabetes_mellitus', 'anemia']; key values {'creatinine': 2.57, 'glucose': 737.0, 'bicarbonate': 11.3, 'potassium': 4.4, 'sodium': 139.0, 'hemoglobin': 10.0, 'platelet_count': 418.0, 'white_blood_cell_count': 19.7}

**D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited)**

