# Structured error audit — eICU-CRD demo, engine v5

Population: every (stay, clinician-listed group) pair with the key analyte measured and the group absent from the top-5 (N = 1163 misses across 2314 stays). A fixed-seed random sample of 200 misses was classified with a pre-declared, deterministic taxonomy (see script header); no manual relabelling.

| Category | n | % of sampled misses |
|---|---:|---:|
| A — not supported by the measured laboratory values (label = history/clinical context) | 139 | 69.5% |
| B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings | 35 | 17.5% |
| C1 — knowledge/logic miss: laboratory signature present, entity never proposed | 12 | 6.0% |
| C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5 | 13 | 6.5% |
| D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited) | 1 | 0.5% |

**Interpretation.** 139 / 200 (70%) of misses carry no laboratory signature of the listed condition and are not recoverable by any laboratory-only system without inventing evidence; 60 (30%) are in principle recoverable (engine-side), of which 12 are knowledge/logic gaps, 13 scoring/severity defects and 35 ranking displacements caused by the five-slot cut-off; 1 reflect the evaluation label map rather than the engine.

## By clinician-listed group (sampled misses)

| group | n | A | B | C1 | C2 | D |
|---|---:|---:|---:|---:|---:|---:|
| heart_failure | 34 | 33 | 1 | 0 | 0 | 0 |
| sepsis | 29 | 16 | 4 | 7 | 1 | 1 |
| diabetes | 21 | 18 | 2 | 0 | 1 | 0 |
| renal_impairment | 14 | 11 | 3 | 0 | 0 | 0 |
| chronic_kidney_disease | 12 | 8 | 2 | 0 | 2 | 0 |
| acute_kidney_injury | 9 | 3 | 4 | 0 | 2 | 0 |
| gi_bleeding | 7 | 3 | 3 | 0 | 1 | 0 |
| hypothyroidism | 6 | 6 | 0 | 0 | 0 | 0 |
| diabetic_ketoacidosis | 6 | 5 | 0 | 0 | 1 | 0 |
| acute_myocardial_infarction | 6 | 5 | 0 | 1 | 0 | 0 |
| hypokalemia | 5 | 4 | 1 | 0 | 0 | 0 |
| alcohol_withdrawal | 5 | 3 | 0 | 2 | 0 | 0 |
| hyperglycemia | 5 | 4 | 1 | 0 | 0 | 0 |
| anemia | 4 | 0 | 4 | 0 | 0 | 0 |
| acute_pancreatitis | 4 | 4 | 0 | 0 | 0 | 0 |
| coagulopathy | 4 | 3 | 0 | 0 | 1 | 0 |
| hyperkalemia | 4 | 0 | 4 | 0 | 0 | 0 |
| thrombocytopenia | 3 | 1 | 2 | 0 | 0 | 0 |
| hyponatremia | 3 | 1 | 1 | 0 | 1 | 0 |
| leukocytosis | 3 | 1 | 2 | 0 | 0 | 0 |
| metabolic_acidosis | 3 | 2 | 0 | 1 | 0 | 0 |
| hypomagnesemia | 3 | 3 | 0 | 0 | 0 | 0 |
| hypophosphatemia | 2 | 1 | 1 | 0 | 0 | 0 |
| malnutrition | 2 | 1 | 0 | 0 | 1 | 0 |
| hypoglycemia | 2 | 2 | 0 | 0 | 0 | 0 |
| cirrhosis_liver_failure | 2 | 0 | 0 | 0 | 2 | 0 |
| hypocalcemia | 1 | 1 | 0 | 0 | 0 | 0 |
| lactic_acidosis | 1 | 0 | 0 | 1 | 0 | 0 |

## Examples (first six per category, verbatim engine outputs)

**A — not supported by the measured laboratory values (label = history/clinical context)**
- stay 1325742 (79m) coded **renal_impairment** rank=None p=0.00; top-5 ['sepsis', 'leukocytosis_pattern', 'hyperchloremia', 'hypophosphatemia', 'hypocalcemia']; key values {'creatinine': 1.12, 'glucose': 153.0, 'bicarbonate': 20.5, 'potassium': 3.5, 'sodium': 137.0, 'hemoglobin': 13.4, 'platelet_count': 205.0, 'white_blood_cell_count': 15.6, 'lactate': 2.1, 'albumin': 2.4}
- stay 1573546 (77m) coded **heart_failure** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'acute_kidney_injury', 'chronic_kidney_disease', 'leukocytosis_pattern', 'alcoholic_liver_disease']; key values {'creatinine': 2.59, 'glucose': 115.0, 'bicarbonate': 24.0, 'potassium': 4.3, 'sodium': 139.0, 'hemoglobin': 15.0, 'platelet_count': 159.0, 'white_blood_cell_count': 17.99, 'lactate': 1.6, 'albumin': 2.9, 'international_normalized_ratio': 1.3, 'troponin_i': 24.1}
- stay 453326 (85m) coded **heart_failure** rank=None p=0.00; top-5 ['acute_myocardial_injury', 'anemia', 'acute_kidney_injury', 'metabolic_acidosis', 'type_2_diabetes']; key values {'creatinine': 1.2, 'glucose': 117.0, 'bicarbonate': 22.0, 'potassium': 4.6, 'sodium': 141.0, 'hemoglobin': 12.5, 'platelet_count': 182.0, 'white_blood_cell_count': 6.9, 'troponin_i': 0.07}
- stay 2691019 (72m) coded **diabetes** rank=9 p=0.42; top-5 ['anemia', 'hypercalcemia', 'hypokalemia', 'primary_hyperparathyroidism', 'leukocytosis_pattern']; key values {'creatinine': 0.97, 'glucose': 144.0, 'bicarbonate': 26.0, 'potassium': 2.8, 'sodium': 142.0, 'hemoglobin': 8.9, 'platelet_count': 639.0, 'white_blood_cell_count': 18.4}
- stay 2784403 (65f) coded **heart_failure** rank=None p=0.00; top-5 ['acute_kidney_injury', 'chronic_kidney_disease', 'anemia', 'type_2_diabetes', 'bacterial_infection']; key values {'creatinine': 3.81, 'glucose': 151.0, 'bicarbonate': 26.0, 'potassium': 4.3, 'sodium': 135.0, 'hemoglobin': 9.8, 'platelet_count': 227.0, 'white_blood_cell_count': 9.4}
- stay 2603291 (79m) coded **hypothyroidism** rank=None p=0.00; top-5 ['leukocytosis_pattern', 'alcoholic_liver_disease', 'liver_cirrhosis', 'malnutrition', 'hyponatremia']; key values {'creatinine': 0.96, 'bicarbonate': 24.7, 'potassium': 4.7, 'sodium': 133.0, 'hemoglobin': 13.9, 'platelet_count': 169.0, 'white_blood_cell_count': 11.3, 'albumin': 3.1}

**B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings**
- stay 3153894 (68m) coded **anemia** rank=7 p=0.56; top-5 ['acute_myocardial_infarction', 'liver_cirrhosis', 'elevated_inr_pattern', 'sepsis', 'diabetes_mellitus']; key values {'creatinine': 1.2, 'glucose': 283.0, 'bicarbonate': 18.0, 'potassium': 3.7, 'sodium': 135.0, 'hemoglobin': 11.1, 'platelet_count': 127.0, 'white_blood_cell_count': 15.8, 'lactate': 1.7, 'albumin': 2.9, 'international_normalized_ratio': 3.7, 'troponin_i': 24.43}
- stay 3159396 (48m) coded **renal_impairment** rank=9 p=0.79; top-5 ['liver_cirrhosis', 'acute_myocardial_infarction', 'mixed_metabolic_and_respiratory_acidosis', 'respiratory_acidosis', 'sepsis']; key values {'creatinine': 4.8, 'glucose': 101.0, 'bicarbonate': 16.0, 'potassium': 4.2, 'sodium': 134.0, 'hemoglobin': 9.7, 'platelet_count': 52.0, 'white_blood_cell_count': 23.6, 'lactate': 17.9, 'albumin': 2.4, 'international_normalized_ratio': 1.37, 'troponin_i': 1.59, 'b_type_natriuretic_peptide': 1530.0}
- stay 1714981 (47m) coded **hypokalemia** rank=6 p=0.62; top-5 ['acute_myocardial_infarction', 'acute_kidney_injury', 'chronic_kidney_disease', 'metabolic_acidosis', 'hyponatremia']; key values {'creatinine': 2.3, 'glucose': 134.0, 'bicarbonate': 21.0, 'potassium': 3.3, 'sodium': 131.0, 'hemoglobin': 15.6, 'platelet_count': 182.0, 'white_blood_cell_count': 12.36, 'lactate': 1.3, 'albumin': 4.0, 'international_normalized_ratio': 1.1, 'troponin_i': 0.15}
- stay 3075813 (83m) coded **hypophosphatemia** rank=10 p=0.64; top-5 ['mixed_metabolic_and_respiratory_acidosis', 'respiratory_acidosis', 'acute_kidney_injury', 'chronic_kidney_disease', 'anemia']; key values {'creatinine': 2.54, 'glucose': 177.0, 'bicarbonate': 20.0, 'potassium': 4.2, 'sodium': 143.0, 'hemoglobin': 12.2, 'platelet_count': 527.0, 'white_blood_cell_count': 15.0, 'albumin': 3.1}
- stay 472359 (63f) coded **thrombocytopenia** rank=6 p=0.79; top-5 ['refeeding_syndrome', 'hypophosphatemia', 'liver_cirrhosis', 'hepatocellular_injury_pattern', 'elevated_inr_pattern']; key values {'creatinine': 1.75, 'glucose': 250.0, 'bicarbonate': 23.0, 'potassium': 3.4, 'sodium': 140.0, 'hemoglobin': 10.4, 'platelet_count': 36.0, 'white_blood_cell_count': 13.6, 'albumin': 1.7, 'international_normalized_ratio': 2.3}
- stay 341782 (49m) coded **heart_failure** rank=7 p=0.85; top-5 ['copd', 'hypomagnesemia', 'respiratory_acidosis', 'acute_kidney_injury', 'chronic_kidney_disease']; key values {'creatinine': 3.18, 'glucose': 99.0, 'bicarbonate': 32.5, 'potassium': 3.9, 'sodium': 134.0, 'hemoglobin': 7.3, 'platelet_count': 155.0, 'white_blood_cell_count': 7.0, 'albumin': 3.4, 'international_normalized_ratio': 1.2, 'b_type_natriuretic_peptide': 1282.0}

**C1 — knowledge/logic miss: laboratory signature present, entity never proposed**
- stay 3136458 (72f) coded **metabolic_acidosis** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'heart_failure', 'cardiorenal_syndrome', 'prerenal_azotemia', 'acute_kidney_injury']; key values {'creatinine': 2.0, 'glucose': 89.0, 'bicarbonate': 20.0, 'potassium': 4.2, 'sodium': 137.0, 'hemoglobin': 11.3, 'platelet_count': 192.0, 'white_blood_cell_count': 11.2, 'lactate': 1.2, 'albumin': 1.4, 'troponin_i': 0.11, 'b_type_natriuretic_peptide': 11618.0}
- stay 2847703 (74m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['acute_myocardial_injury', 'liver_cirrhosis', 'anemia', 'thrombocytopenia', 'hyperchloremia']; key values {'creatinine': 0.57, 'glucose': 94.0, 'bicarbonate': 26.0, 'potassium': 4.0, 'sodium': 143.0, 'hemoglobin': 12.2, 'platelet_count': 139.0, 'white_blood_cell_count': 7.8, 'albumin': 3.4, 'troponin_i': 0.03}
- stay 1118948 (77f) coded **sepsis** rank=None p=0.00; top-5 ['elevated_inr_pattern', 'anemia', 'hypernatremia', 'hypokalemia', 'leukopenia']; key values {'creatinine': 0.5, 'glucose': 127.0, 'bicarbonate': 38.0, 'potassium': 3.4, 'sodium': 148.0, 'hemoglobin': 9.0, 'platelet_count': 171.0, 'white_blood_cell_count': 3.6, 'albumin': 2.2, 'international_normalized_ratio': 2.8}
- stay 618867 (54f) coded **sepsis** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'acute_kidney_injury', 'chronic_kidney_disease', 'anemia', 'hypokalemia']; key values {'creatinine': 1.7, 'glucose': 112.0, 'bicarbonate': 25.4, 'potassium': 3.2, 'sodium': 136.0, 'hemoglobin': 10.4, 'platelet_count': 335.0, 'white_blood_cell_count': 11.9, 'lactate': 1.2, 'albumin': 2.8, 'international_normalized_ratio': 1.4, 'troponin_i': 0.18}
- stay 2883334 (77m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['sepsis', 'acute_myocardial_injury', 'leukocytosis_pattern', 'isolated_hyperbilirubinemia_pattern', 'acute_myocardial_infarction']; key values {'creatinine': 0.9, 'glucose': 151.0, 'bicarbonate': 26.0, 'potassium': 3.9, 'sodium': 141.0, 'hemoglobin': 17.2, 'platelet_count': 170.0, 'white_blood_cell_count': 13.0, 'lactate': 3.4, 'albumin': 3.1, 'international_normalized_ratio': 1.1, 'troponin_i': 0.06}
- stay 1820689 (72f) coded **sepsis** rank=None p=0.00; top-5 ['thrombocytopenia', 'pancytopenia', 'anemia', 'hyponatremia', 'hypokalemia']; key values {'creatinine': 0.88, 'glucose': 233.0, 'potassium': 3.0, 'sodium': 132.0, 'hemoglobin': 6.7, 'platelet_count': 19.0, 'white_blood_cell_count': 0.2, 'albumin': 3.1}

**C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5**
- stay 1325742 (79m) coded **malnutrition** rank=7 p=0.47; top-5 ['sepsis', 'leukocytosis_pattern', 'hyperchloremia', 'hypophosphatemia', 'hypocalcemia']; key values {'creatinine': 1.12, 'glucose': 153.0, 'bicarbonate': 20.5, 'potassium': 3.5, 'sodium': 137.0, 'hemoglobin': 13.4, 'platelet_count': 205.0, 'white_blood_cell_count': 15.6, 'lactate': 2.1, 'albumin': 2.4}
- stay 263850 (62m) coded **chronic_kidney_disease** rank=8 p=0.23; top-5 ['subclinical_hyperthyroidism', 'hyponatremia', 'leukocytosis_pattern', 'acute_kidney_injury', 'hypochloremia']; key values {'creatinine': 1.66, 'glucose': 128.0, 'bicarbonate': 23.0, 'potassium': 4.4, 'sodium': 130.0, 'hemoglobin': 15.4, 'platelet_count': 278.0, 'white_blood_cell_count': 12.73, 'albumin': 4.0, 'international_normalized_ratio': 1.1}
- stay 646514 (90f) coded **gi_bleeding** rank=10 p=0.27; top-5 ['hypernatremia', 'hypokalemia', 'thrombocytopenia', 'hyperchloremia', 'acute_kidney_injury']; key values {'creatinine': 1.1, 'glucose': 121.0, 'bicarbonate': 26.0, 'potassium': 3.4, 'sodium': 149.0, 'hemoglobin': 12.1, 'platelet_count': 123.0, 'white_blood_cell_count': 11.0, 'albumin': 3.2, 'international_normalized_ratio': 1.2, 'troponin_i': 0.13}
- stay 498515 (71m) coded **diabetes** rank=10 p=0.49; top-5 ['sepsis', 'diabetic_ketoacidosis', 'acute_kidney_injury', 'metabolic_acidosis', 'hyponatremia']; key values {'creatinine': 11.1, 'glucose': 218.0, 'bicarbonate': 16.3, 'potassium': 6.0, 'sodium': 131.0, 'hemoglobin': 12.3, 'platelet_count': 177.0, 'white_blood_cell_count': 14.4, 'international_normalized_ratio': 1.2}
- stay 151900 (66f) coded **acute_kidney_injury** rank=8 p=0.49; top-5 ['acute_myocardial_infarction', 'metabolic_acidosis', 'anemia', 'diabetes_mellitus', 'thrombocytosis']; key values {'creatinine': 1.24, 'glucose': 276.0, 'bicarbonate': 20.0, 'potassium': 3.9, 'sodium': 134.0, 'hemoglobin': 10.9, 'platelet_count': 637.0, 'white_blood_cell_count': 9.9, 'lactate': 0.9, 'albumin': 2.4, 'international_normalized_ratio': 1.0, 'troponin_i': 0.84, 'b_type_natriuretic_peptide': 126.0}
- stay 3230503 (72m) coded **cirrhosis_liver_failure** rank=14 p=0.16; top-5 ['hyponatremia', 'leukopenia', 'anemia', 'hypochloremia', 'malnutrition']; key values {'creatinine': 1.18, 'glucose': 112.0, 'bicarbonate': 26.0, 'potassium': 4.7, 'sodium': 130.0, 'hemoglobin': 12.6, 'platelet_count': 152.0, 'white_blood_cell_count': 3.5, 'albumin': 3.0, 'international_normalized_ratio': 1.3}

**D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited)**
- stay 2714202 (59m) coded **sepsis** rank=None p=0.00; top-5 ['anemia', 'leukocytosis_pattern', 'hypomagnesemia', 'hypocalcemia', 'bacterial_infection']; key values {'creatinine': 1.1, 'glucose': 95.0, 'bicarbonate': 23.0, 'potassium': 4.1, 'sodium': 138.0, 'hemoglobin': 8.4, 'platelet_count': 351.0, 'white_blood_cell_count': 12.4, 'lactate': 0.9}

