# Structured error audit — eICU-CRD demo, engine v5.1

Population: every (stay, clinician-listed group) pair with the key analyte measured and the group absent from the top-5 (N = 1152 misses across 2314 stays). A fixed-seed random sample of 200 misses was classified with a pre-declared, deterministic taxonomy (see script header); no manual relabelling.

| Category | n | % of sampled misses |
|---|---:|---:|
| A — not supported by the measured laboratory values (label = history/clinical context) | 134 | 67.0% |
| B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings | 39 | 19.5% |
| C1 — knowledge/logic miss: laboratory signature present, entity never proposed | 10 | 5.0% |
| C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5 | 17 | 8.5% |
| D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited) | 0 | 0.0% |

**Interpretation.** 134 / 200 (67%) of misses carry no laboratory signature of the listed condition and are not recoverable by any laboratory-only system without inventing evidence; 66 (33%) are in principle recoverable (engine-side), of which 10 are knowledge/logic gaps, 17 scoring/severity defects and 39 ranking displacements caused by the five-slot cut-off; 0 reflect the evaluation label map rather than the engine.

## By clinician-listed group (sampled misses)

| group | n | A | B | C1 | C2 | D |
|---|---:|---:|---:|---:|---:|---:|
| heart_failure | 30 | 28 | 0 | 0 | 2 | 0 |
| diabetes | 23 | 19 | 2 | 0 | 2 | 0 |
| sepsis | 21 | 13 | 4 | 3 | 1 | 0 |
| renal_impairment | 12 | 4 | 5 | 1 | 2 | 0 |
| acute_kidney_injury | 11 | 5 | 4 | 0 | 2 | 0 |
| hypothyroidism | 10 | 10 | 0 | 0 | 0 | 0 |
| hyperkalemia | 7 | 3 | 4 | 0 | 0 | 0 |
| chronic_kidney_disease | 7 | 4 | 2 | 0 | 1 | 0 |
| hypokalemia | 7 | 7 | 0 | 0 | 0 | 0 |
| anemia | 7 | 2 | 5 | 0 | 0 | 0 |
| gi_bleeding | 7 | 4 | 2 | 1 | 0 | 0 |
| alcohol_withdrawal | 6 | 3 | 0 | 2 | 1 | 0 |
| metabolic_acidosis | 6 | 5 | 0 | 0 | 1 | 0 |
| acute_myocardial_infarction | 5 | 4 | 0 | 1 | 0 | 0 |
| hyperglycemia | 5 | 4 | 1 | 0 | 0 | 0 |
| thrombocytopenia | 4 | 1 | 3 | 0 | 0 | 0 |
| leukocytosis | 4 | 2 | 2 | 0 | 0 | 0 |
| hyponatremia | 4 | 1 | 2 | 0 | 1 | 0 |
| malnutrition | 3 | 2 | 0 | 0 | 1 | 0 |
| acute_pancreatitis | 3 | 3 | 0 | 0 | 0 | 0 |
| hypoglycemia | 3 | 3 | 0 | 0 | 0 | 0 |
| diabetic_ketoacidosis | 3 | 3 | 0 | 0 | 0 | 0 |
| hypomagnesemia | 2 | 1 | 1 | 0 | 0 | 0 |
| lactic_acidosis | 2 | 0 | 0 | 2 | 0 | 0 |
| cirrhosis_liver_failure | 2 | 0 | 1 | 0 | 1 | 0 |
| hypophosphatemia | 2 | 1 | 1 | 0 | 0 | 0 |
| hypocalcemia | 1 | 0 | 0 | 0 | 1 | 0 |
| rhabdomyolysis | 1 | 1 | 0 | 0 | 0 | 0 |
| hypernatremia | 1 | 0 | 0 | 0 | 1 | 0 |
| coagulopathy | 1 | 1 | 0 | 0 | 0 | 0 |

## Examples (first six per category, verbatim engine outputs)

**A — not supported by the measured laboratory values (label = history/clinical context)**
- stay 2670190 (84f) coded **hyperkalemia** rank=None p=0.00; top-5 ['respiratory_acidosis', 'chronic_kidney_disease', 'anemia', 'hypomagnesemia', 'acute_kidney_injury']; key values {'creatinine': 1.48, 'glucose': 107.0, 'bicarbonate': 29.0, 'potassium': 4.6, 'sodium': 140.0, 'hemoglobin': 9.2, 'platelet_count': 240.0, 'white_blood_cell_count': 9.1}
- stay 450383 (55m) coded **sepsis** rank=None p=0.00; top-5 ['anemia', 'hypocalcemia', 'co_decreased_blood_urea_nitrogen_with_decreased_creatinine', 'co_elevated_platelet_count_with_decreased_red_blood_cell_count', 'vitamin_d_deficiency']; key values {'creatinine': 0.55, 'glucose': 94.0, 'bicarbonate': 28.0, 'potassium': 4.0, 'sodium': 137.0, 'hemoglobin': 8.9, 'platelet_count': 458.0, 'white_blood_cell_count': 8.7, 'lactate': 0.8}
- stay 3142620 (22m) coded **hypokalemia** rank=None p=0.00; top-5 ['acute_pancreatitis', 'metabolic_acidosis', 'hyperkalemia', 'sepsis', 'leukocytosis_pattern']; key values {'creatinine': 0.8, 'glucose': 141.0, 'bicarbonate': 9.0, 'potassium': 6.1, 'sodium': 136.0, 'hemoglobin': 14.9, 'platelet_count': 198.0, 'white_blood_cell_count': 15.2, 'albumin': 3.6}
- stay 2818995 (68m) coded **heart_failure** rank=None p=0.00; top-5 ['type_2_diabetes', 'thalassemia_trait', 'malnutrition', 'hyperchloremia']; key values {'creatinine': 0.8, 'glucose': 112.0, 'bicarbonate': 29.0, 'potassium': 3.5, 'sodium': 143.0, 'hemoglobin': 15.4, 'platelet_count': 207.0, 'white_blood_cell_count': 7.3, 'lactate': 1.0, 'albumin': 3.4}
- stay 3352230 (41m) coded **acute_myocardial_infarction** rank=None p=0.00; top-5 ['sepsis', 'anemia', 'leukocytosis_pattern', 'hypertriglyceridemia', 'thrombocytopenia']; key values {'creatinine': 1.31, 'glucose': 182.0, 'bicarbonate': 26.1, 'potassium': 4.0, 'sodium': 138.0, 'hemoglobin': 9.1, 'platelet_count': 84.0, 'white_blood_cell_count': 19.6, 'international_normalized_ratio': 1.33}
- stay 2646210 (62m) coded **sepsis** rank=None p=0.00; top-5 ['acute_kidney_injury', 'chronic_kidney_disease', 'anemia', 'alcohol_use_disorder', 'alcoholic_liver_pattern']; key values {'creatinine': 2.5, 'glucose': 105.0, 'bicarbonate': 25.0, 'potassium': 4.8, 'sodium': 140.0, 'hemoglobin': 8.3, 'platelet_count': 121.0, 'white_blood_cell_count': 5.21, 'lactate': 1.0, 'albumin': 3.2, 'troponin_i': 0.01}

**B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings**
- stay 3159396 (48m) coded **chronic_kidney_disease** rank=9 p=0.79; top-5 ['liver_cirrhosis', 'acute_myocardial_infarction', 'mixed_metabolic_and_respiratory_acidosis', 'respiratory_acidosis', 'sepsis']; key values {'creatinine': 4.8, 'glucose': 101.0, 'bicarbonate': 16.0, 'potassium': 4.2, 'sodium': 134.0, 'hemoglobin': 9.7, 'platelet_count': 52.0, 'white_blood_cell_count': 23.6, 'lactate': 17.9, 'albumin': 2.4, 'international_normalized_ratio': 1.37, 'troponin_i': 1.59, 'b_type_natriuretic_peptide': 1530.0}
- stay 3135611 (69m) coded **anemia** rank=7 p=0.56; top-5 ['acute_myocardial_infarction', 'copd', 'respiratory_acidosis', 'chronic_kidney_disease', 'acute_kidney_injury']; key values {'creatinine': 1.8, 'glucose': 148.0, 'bicarbonate': 35.0, 'potassium': 5.4, 'sodium': 138.0, 'hemoglobin': 11.7, 'platelet_count': 209.0, 'white_blood_cell_count': 9.0, 'troponin_i': 0.7}
- stay 431760 (56f) coded **anemia** rank=6 p=0.56; top-5 ['chronic_kidney_disease', 'acute_kidney_injury', 'metabolic_acidosis', 'hyponatremia', 'leukocytosis_pattern']; key values {'creatinine': 7.29, 'glucose': 188.0, 'bicarbonate': 20.0, 'potassium': 4.4, 'sodium': 132.0, 'hemoglobin': 5.7, 'platelet_count': 155.0, 'white_blood_cell_count': 24.05, 'albumin': 2.2, 'international_normalized_ratio': 1.5}
- stay 224606 (76f) coded **thrombocytopenia** rank=6 p=0.52; top-5 ['metabolic_acidosis', 'acute_myocardial_injury', 'liver_cirrhosis', 'sepsis', 'leukocytosis_pattern']; key values {'creatinine': 1.1, 'glucose': 220.0, 'bicarbonate': 21.0, 'potassium': 4.4, 'sodium': 136.0, 'hemoglobin': 12.2, 'platelet_count': 52.0, 'white_blood_cell_count': 35.2, 'lactate': 1.9, 'albumin': 2.2, 'international_normalized_ratio': 1.5, 'troponin_i': 0.03}
- stay 1088206 (76m) coded **gi_bleeding** rank=7 p=0.68; top-5 ['liver_cirrhosis', 'acute_kidney_injury', 'thrombocytopenia', 'pancytopenia', 'sepsis']; key values {'creatinine': 3.75, 'glucose': 107.0, 'bicarbonate': 28.0, 'potassium': 4.9, 'sodium': 131.0, 'hemoglobin': 7.0, 'platelet_count': 40.0, 'white_blood_cell_count': 3.5, 'albumin': 3.1, 'international_normalized_ratio': 1.77}
- stay 3154460 (61m) coded **thrombocytopenia** rank=6 p=0.52; top-5 ['sepsis', 'acute_kidney_injury', 'hyponatremia', 'hyperkalemia', 'anemia']; key values {'creatinine': 4.4, 'glucose': 70.0, 'bicarbonate': 6.7, 'potassium': 8.8, 'sodium': 132.0, 'hemoglobin': 10.8, 'platelet_count': 66.0, 'white_blood_cell_count': 4.0, 'lactate': 0.7, 'albumin': 3.7}

**C1 — knowledge/logic miss: laboratory signature present, entity never proposed**
- stay 3086494 (34f) coded **renal_impairment** rank=None p=0.00; top-5 ['alcoholic_hepatitis_pattern', 'hepatocellular_injury_pattern', 'alcohol_use_disorder', 'alcoholic_liver_pattern', 'anemia']; key values {'creatinine': 1.22, 'glucose': 118.0, 'bicarbonate': 23.0, 'potassium': 3.6, 'sodium': 125.0, 'hemoglobin': 10.3, 'platelet_count': 162.0, 'white_blood_cell_count': 6.8, 'lactate': 1.8, 'albumin': 2.2, 'international_normalized_ratio': 1.7}
- stay 3079543 (72f) coded **lactic_acidosis** rank=None p=0.00; top-5 ['sepsis', 'acute_myocardial_injury', 'hyperkalemia', 'leukocytosis_pattern', 'acute_kidney_injury']; key values {'creatinine': 0.74, 'glucose': 111.0, 'bicarbonate': 26.2, 'potassium': 5.3, 'sodium': 139.0, 'hemoglobin': 14.6, 'platelet_count': 220.0, 'white_blood_cell_count': 12.2, 'lactate': 3.3, 'troponin_i': 0.03}
- stay 2309912 (57f) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['hypokalemia', 'leukocytosis_pattern', 'thrombocytopenia', 'hypocalcemia', 'liver_cirrhosis']; key values {'creatinine': 0.46, 'glucose': 96.0, 'bicarbonate': 23.0, 'potassium': 3.4, 'sodium': 135.0, 'hemoglobin': 13.3, 'platelet_count': 126.0, 'white_blood_cell_count': 12.1}
- stay 337621 (50m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['anemia', 'hypocalcemia', 'hyponatremia', 'leukocytosis_pattern', 'hypochloremia']; key values {'creatinine': 0.63, 'glucose': 168.0, 'bicarbonate': 24.8, 'potassium': 3.8, 'sodium': 131.0, 'hemoglobin': 6.6, 'platelet_count': 340.0, 'white_blood_cell_count': 21.5, 'albumin': 3.6, 'international_normalized_ratio': 1.3}
- stay 3173599 (67f) coded **acute_myocardial_infarction** rank=None p=0.00; top-5 ['heart_failure', 'cardiorenal_syndrome', 'hypercholesterolemia', 'leukocytosis_pattern', 'hypochloremia']; key values {'creatinine': 1.21, 'glucose': 138.0, 'bicarbonate': 25.0, 'potassium': 3.7, 'sodium': 136.0, 'hemoglobin': 13.8, 'platelet_count': 284.0, 'white_blood_cell_count': 13.8, 'international_normalized_ratio': 1.01, 'b_type_natriuretic_peptide': 1468.0}
- stay 1794248 (41f) coded **gi_bleeding** rank=None p=0.00; top-5 ['hypernatremia', 'hypokalemia', 'acute_kidney_injury', 'chronic_kidney_disease', 'hyperchloremia']; key values {'creatinine': 2.21, 'glucose': 96.0, 'potassium': 2.7, 'sodium': 154.0, 'albumin': 1.9}

**C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5**
- stay 172015 (48f) coded **alcohol_withdrawal** rank=8 p=0.49; top-5 ['liver_cirrhosis', 'hypomagnesemia', 'elevated_inr_pattern', 'thrombocytopenia', 'anemia']; key values {'creatinine': 1.16, 'glucose': 106.0, 'bicarbonate': 26.0, 'potassium': 4.2, 'sodium': 144.0, 'hemoglobin': 10.3, 'platelet_count': 45.0, 'white_blood_cell_count': 6.1, 'albumin': 1.6, 'international_normalized_ratio': 2.2}
- stay 3116577 (53f) coded **hypocalcemia** rank=12 p=0.45; top-5 ['refeeding_syndrome', 'hypophosphatemia', 'hypomagnesemia', 'sepsis', 'lactic_acidosis']; key values {'creatinine': 0.91, 'glucose': 193.0, 'bicarbonate': 19.0, 'potassium': 3.4, 'sodium': 136.0, 'hemoglobin': 11.2, 'platelet_count': 326.0, 'white_blood_cell_count': 19.6, 'lactate': 4.99, 'albumin': 2.3, 'international_normalized_ratio': 1.0, 'troponin_i': 0.01}
- stay 1576845 (37f) coded **acute_kidney_injury** rank=7 p=0.49; top-5 ['diabetic_ketoacidosis', 'metabolic_acidosis', 'diabetes_mellitus', 'anemia', 'leukocytosis_pattern']; key values {'creatinine': 1.36, 'glucose': 742.0, 'bicarbonate': 9.0, 'potassium': 4.8, 'sodium': 135.0, 'hemoglobin': 11.2, 'platelet_count': 373.0, 'white_blood_cell_count': 11.87, 'lactate': 1.5, 'albumin': 3.8}
- stay 263850 (62m) coded **chronic_kidney_disease** rank=8 p=0.23; top-5 ['subclinical_hyperthyroidism', 'hyponatremia', 'leukocytosis_pattern', 'acute_kidney_injury', 'hypochloremia']; key values {'creatinine': 1.66, 'glucose': 128.0, 'bicarbonate': 23.0, 'potassium': 4.4, 'sodium': 130.0, 'hemoglobin': 15.4, 'platelet_count': 278.0, 'white_blood_cell_count': 12.73, 'albumin': 4.0, 'international_normalized_ratio': 1.1}
- stay 202707 (78f) coded **cirrhosis_liver_failure** rank=7 p=0.38; top-5 ['thrombocytopenia', 'leukopenia', 'hyperchloremia', 'immune_thrombocytopenia', 'disseminated_intravascular_coagulation']; key values {'creatinine': 0.71, 'glucose': 173.0, 'bicarbonate': 28.0, 'potassium': 3.6, 'sodium': 146.0, 'hemoglobin': 12.4, 'platelet_count': 35.0, 'white_blood_cell_count': 3.1, 'international_normalized_ratio': 1.4}
- stay 1090567 (76m) coded **heart_failure** rank=8 p=0.40; top-5 ['sepsis', 'hypokalemia', 'acute_kidney_injury', 'hypocalcemia', 'chronic_kidney_disease']; key values {'creatinine': 1.6, 'glucose': 126.0, 'bicarbonate': 22.0, 'potassium': 3.3, 'sodium': 141.0, 'hemoglobin': 10.4, 'platelet_count': 183.0, 'white_blood_cell_count': 7.0, 'lactate': 1.9, 'b_type_natriuretic_peptide': 161.4}

**D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited)**

