# Structured error audit — eICU-CRD demo, engine v5.3

Population: every (stay, clinician-listed group) pair with the key analyte measured and the group absent from the top-5 (N = 1151 misses across 2314 stays). A fixed-seed random sample of 200 misses was classified with a pre-declared, deterministic taxonomy (see script header); no manual relabelling.

| Category | n | % of sampled misses |
|---|---:|---:|
| A — not supported by the measured laboratory values (label = history/clinical context) | 132 | 66.0% |
| B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings | 38 | 19.0% |
| C1 — knowledge/logic miss: laboratory signature present, entity never proposed | 15 | 7.5% |
| C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5 | 14 | 7.0% |
| D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited) | 1 | 0.5% |

**Interpretation.** 132 / 200 (66%) of misses carry no laboratory signature of the listed condition and are not recoverable by any laboratory-only system without inventing evidence; 67 (34%) are in principle recoverable (engine-side), of which 15 are knowledge/logic gaps, 14 scoring/severity defects and 38 ranking displacements caused by the five-slot cut-off; 1 reflect the evaluation label map rather than the engine.

## By clinician-listed group (sampled misses)

| group | n | A | B | C1 | C2 | D |
|---|---:|---:|---:|---:|---:|---:|
| heart_failure | 29 | 27 | 0 | 0 | 2 | 0 |
| sepsis | 25 | 7 | 5 | 9 | 3 | 1 |
| diabetes | 22 | 21 | 1 | 0 | 0 | 0 |
| renal_impairment | 12 | 6 | 5 | 0 | 1 | 0 |
| acute_kidney_injury | 12 | 5 | 7 | 0 | 0 | 0 |
| chronic_kidney_disease | 10 | 7 | 1 | 0 | 2 | 0 |
| diabetic_ketoacidosis | 9 | 8 | 0 | 1 | 0 | 0 |
| hyperglycemia | 9 | 7 | 2 | 0 | 0 | 0 |
| hypokalemia | 7 | 7 | 0 | 0 | 0 | 0 |
| alcohol_withdrawal | 6 | 4 | 0 | 1 | 1 | 0 |
| cirrhosis_liver_failure | 6 | 2 | 1 | 0 | 3 | 0 |
| acute_pancreatitis | 5 | 5 | 0 | 0 | 0 | 0 |
| malnutrition | 5 | 4 | 0 | 0 | 1 | 0 |
| hyperkalemia | 5 | 0 | 5 | 0 | 0 | 0 |
| hypothyroidism | 5 | 5 | 0 | 0 | 0 | 0 |
| anemia | 4 | 1 | 3 | 0 | 0 | 0 |
| hypoglycemia | 4 | 4 | 0 | 0 | 0 | 0 |
| acute_myocardial_infarction | 4 | 2 | 0 | 1 | 1 | 0 |
| leukocytosis | 4 | 3 | 1 | 0 | 0 | 0 |
| metabolic_acidosis | 4 | 2 | 1 | 1 | 0 | 0 |
| coagulopathy | 3 | 0 | 2 | 1 | 0 | 0 |
| gi_bleeding | 3 | 3 | 0 | 0 | 0 | 0 |
| hyponatremia | 3 | 1 | 2 | 0 | 0 | 0 |
| lactic_acidosis | 2 | 0 | 1 | 1 | 0 | 0 |
| thrombocytopenia | 1 | 0 | 1 | 0 | 0 | 0 |
| hypomagnesemia | 1 | 1 | 0 | 0 | 0 | 0 |

## Examples (first six per category, verbatim engine outputs)

**A — not supported by the measured laboratory values (label = history/clinical context)**
- stay 2737587 (84m) coded **acute_pancreatitis** rank=None p=0.00; top-5 ['acute_myocardial_injury', 'acute_kidney_injury', 'hyperkalemia', 'rhabdomyolysis', 'diabetes_mellitus']; key values {'creatinine': 2.26, 'glucose': 360.0, 'bicarbonate': 22.0, 'potassium': 6.1, 'sodium': 137.0, 'hemoglobin': 10.3, 'platelet_count': 132.0, 'white_blood_cell_count': 11.1, 'albumin': 3.0, 'international_normalized_ratio': 1.2, 'troponin_i': 0.05}
- stay 3085970 (62m) coded **malnutrition** rank=18 p=0.39; top-5 ['immune_thrombocytopenia', 'acute_pancreatitis', 'hepatocellular_injury_pattern', 'hypokalemia', 'thrombocytopenia']; key values {'creatinine': 0.72, 'glucose': 79.0, 'bicarbonate': 28.0, 'potassium': 2.5, 'sodium': 129.0, 'hemoglobin': 13.3, 'platelet_count': 49.0, 'white_blood_cell_count': 9.9, 'albumin': 3.3, 'troponin_i': 0.509}
- stay 2579022 (59m) coded **heart_failure** rank=None p=0.00; top-5 ['hyponatremia', 'hypochloremia', 'isolated_hyperbilirubinemia_pattern', 'hypocalcemia', 'bacterial_infection']; key values {'creatinine': 0.7, 'glucose': 132.0, 'bicarbonate': 30.0, 'potassium': 3.5, 'sodium': 130.0, 'hemoglobin': 14.9, 'platelet_count': 248.0, 'white_blood_cell_count': 8.34, 'albumin': 2.9, 'international_normalized_ratio': 1.2}
- stay 1494982 (25f) coded **heart_failure** rank=None p=0.00; top-5 ['acute_kidney_injury', 'chronic_kidney_disease', 'anemia', 'hyperphosphatemia', 'respiratory_acidosis']; key values {'creatinine': 7.78, 'glucose': 101.0, 'bicarbonate': 25.0, 'potassium': 3.9, 'sodium': 141.0, 'hemoglobin': 11.5, 'platelet_count': 156.0, 'white_blood_cell_count': 5.7, 'albumin': 2.9}
- stay 2860378 (36f) coded **acute_pancreatitis** rank=None p=0.00; top-5 ['diabetes_mellitus', 'hypochloremia', 'hypomagnesemia', 'hypophosphatemia', 'acute_kidney_injury']; key values {'creatinine': 1.0, 'glucose': 504.0, 'bicarbonate': 22.0, 'potassium': 4.1, 'sodium': 136.0, 'hemoglobin': 16.6, 'platelet_count': 291.0, 'white_blood_cell_count': 8.7, 'albumin': 4.4}
- stay 1573546 (77m) coded **heart_failure** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'acute_kidney_injury', 'chronic_kidney_disease', 'leukocytosis_pattern', 'alcoholic_liver_disease']; key values {'creatinine': 2.59, 'glucose': 115.0, 'bicarbonate': 24.0, 'potassium': 4.3, 'sodium': 139.0, 'hemoglobin': 15.0, 'platelet_count': 159.0, 'white_blood_cell_count': 17.99, 'lactate': 1.6, 'albumin': 2.9, 'international_normalized_ratio': 1.3, 'troponin_i': 24.1}

**B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings**
- stay 681745 (63m) coded **renal_impairment** rank=7 p=0.72; top-5 ['acute_myocardial_infarction', 'sepsis', 'lactic_acidosis', 'hepatocellular_injury_pattern', 'diabetic_ketoacidosis']; key values {'creatinine': 2.58, 'glucose': 416.0, 'bicarbonate': 7.0, 'potassium': 5.7, 'sodium': 135.0, 'hemoglobin': 12.2, 'platelet_count': 79.0, 'white_blood_cell_count': 16.0, 'lactate': 15.1, 'albumin': 2.6, 'troponin_i': 0.26}
- stay 472969 (44m) coded **diabetes** rank=6 p=0.77; top-5 ['diabetic_ketoacidosis', 'metabolic_acidosis', 'hypophosphatemia', 'sepsis', 'lactic_acidosis']; key values {'creatinine': 1.09, 'glucose': 431.0, 'bicarbonate': 3.6, 'potassium': 4.5, 'sodium': 130.0, 'hemoglobin': 15.8, 'platelet_count': 148.0, 'white_blood_cell_count': 12.6, 'lactate': 2.2, 'albumin': 3.3}
- stay 3158919 (74m) coded **hyperkalemia** rank=8 p=0.79; top-5 ['liver_cirrhosis', 'mixed_metabolic_and_respiratory_acidosis', 'respiratory_acidosis', 'acute_kidney_injury', 'sepsis']; key values {'creatinine': 3.7, 'glucose': 99.0, 'bicarbonate': 20.0, 'potassium': 6.5, 'sodium': 141.0, 'hemoglobin': 16.0, 'platelet_count': 134.0, 'white_blood_cell_count': 19.0, 'lactate': 2.7, 'albumin': 3.3, 'international_normalized_ratio': 1.46}
- stay 1564685 (53f) coded **sepsis** rank=6 p=0.72; top-5 ['lactic_acidosis', 'acute_kidney_injury', 'metabolic_acidosis', 'hepatocellular_injury_pattern', 'acute_myocardial_infarction']; key values {'creatinine': 2.92, 'glucose': 95.0, 'bicarbonate': 16.0, 'potassium': 4.2, 'sodium': 140.0, 'hemoglobin': 14.6, 'platelet_count': 183.0, 'white_blood_cell_count': 7.31, 'lactate': 8.4, 'albumin': 3.0, 'international_normalized_ratio': 1.2, 'troponin_i': 0.115}
- stay 2704188 (84f) coded **hyperkalemia** rank=7 p=0.57; top-5 ['acute_kidney_injury', 'chronic_kidney_disease', 'anemia', 'metabolic_acidosis', 'sepsis']; key values {'creatinine': 1.9, 'glucose': 115.0, 'bicarbonate': 15.0, 'potassium': 5.2, 'sodium': 136.0, 'hemoglobin': 7.7, 'platelet_count': 213.0, 'white_blood_cell_count': 8.8, 'lactate': 3.3, 'albumin': 2.3}
- stay 3098657 (53m) coded **renal_impairment** rank=7 p=0.59; top-5 ['metabolic_acidosis', 'sepsis', 'lactic_acidosis', 'diabetic_ketoacidosis', 'diabetes_mellitus']; key values {'creatinine': 1.4, 'glucose': 211.0, 'bicarbonate': 17.0, 'potassium': 4.4, 'sodium': 138.0, 'hemoglobin': 18.2, 'platelet_count': 279.0, 'white_blood_cell_count': 20.1, 'lactate': 3.7, 'albumin': 3.8, 'international_normalized_ratio': 1.1}

**C1 — knowledge/logic miss: laboratory signature present, entity never proposed**
- stay 2778495 (64m) coded **sepsis** rank=None p=0.00; top-5 ['diabetes_mellitus', 'acute_kidney_injury', 'leukocytosis_pattern', 'hyperkalemia', 'chronic_kidney_disease']; key values {'creatinine': 1.67, 'glucose': 268.0, 'bicarbonate': 24.0, 'potassium': 6.0, 'sodium': 133.0, 'hemoglobin': 14.9, 'platelet_count': 169.0, 'white_blood_cell_count': 12.7, 'lactate': 0.9, 'albumin': 3.7, 'international_normalized_ratio': 1.1}
- stay 3157219 (36f) coded **coagulopathy** rank=None p=0.00; top-5 ['lactic_acidosis', 'mixed_metabolic_and_respiratory_acidosis', 'respiratory_acidosis', 'sepsis', 'hepatocellular_injury_pattern']; key values {'creatinine': 1.4, 'glucose': 337.0, 'bicarbonate': 16.4, 'potassium': 3.3, 'sodium': 154.0, 'hemoglobin': 12.8, 'platelet_count': 182.0, 'white_blood_cell_count': 15.1, 'lactate': 10.8, 'albumin': 3.2, 'international_normalized_ratio': 1.6, 'troponin_i': 0.02}
- stay 1118948 (77f) coded **sepsis** rank=None p=0.00; top-5 ['elevated_inr_pattern', 'anemia', 'hypernatremia', 'hypokalemia', 'leukopenia']; key values {'creatinine': 0.5, 'glucose': 127.0, 'bicarbonate': 38.0, 'potassium': 3.4, 'sodium': 148.0, 'hemoglobin': 9.0, 'platelet_count': 171.0, 'white_blood_cell_count': 3.6, 'albumin': 2.2, 'international_normalized_ratio': 2.8}
- stay 2552038 (73f) coded **sepsis** rank=None p=0.00; top-5 ['chronic_leukemia_support_pattern', 'leukocytosis_pattern', 'anemia', 'alcohol_use_disorder', 'diabetes_mellitus']; key values {'creatinine': 0.87, 'glucose': 373.0, 'bicarbonate': 22.0, 'potassium': 4.9, 'sodium': 128.0, 'hemoglobin': 8.2, 'platelet_count': 127.0, 'white_blood_cell_count': 469.8, 'lactate': 1.4, 'albumin': 2.7, 'international_normalized_ratio': 1.3}
- stay 337621 (50m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['anemia', 'hypocalcemia', 'hyponatremia', 'leukocytosis_pattern', 'hypochloremia']; key values {'creatinine': 0.63, 'glucose': 168.0, 'bicarbonate': 24.8, 'potassium': 3.8, 'sodium': 131.0, 'hemoglobin': 6.6, 'platelet_count': 340.0, 'white_blood_cell_count': 21.5, 'albumin': 3.6, 'international_normalized_ratio': 1.3}
- stay 2599455 (57f) coded **sepsis** rank=None p=0.00; top-5 ['alcoholic_hepatitis_pattern', 'alcoholic_liver_pattern', 'anemia', 'leukocytosis_pattern', 'cholestasis']; key values {'creatinine': 0.9, 'glucose': 156.0, 'bicarbonate': 21.0, 'potassium': 3.8, 'sodium': 140.0, 'hemoglobin': 3.3, 'platelet_count': 288.0, 'white_blood_cell_count': 20.65, 'albumin': 4.0, 'international_normalized_ratio': 1.1}

**C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5**
- stay 172015 (48f) coded **alcohol_withdrawal** rank=8 p=0.49; top-5 ['liver_cirrhosis', 'hypomagnesemia', 'elevated_inr_pattern', 'thrombocytopenia', 'anemia']; key values {'creatinine': 1.16, 'glucose': 106.0, 'bicarbonate': 26.0, 'potassium': 4.2, 'sodium': 144.0, 'hemoglobin': 10.3, 'platelet_count': 45.0, 'white_blood_cell_count': 6.1, 'albumin': 1.6, 'international_normalized_ratio': 2.2}
- stay 1571036 (90f) coded **chronic_kidney_disease** rank=11 p=0.21; top-5 ['sepsis', 'anemia', 'leukocytosis_pattern', 'hyperchloremia', 'hypocalcemia']; key values {'creatinine': 1.02, 'glucose': 81.0, 'bicarbonate': 19.5, 'potassium': 3.9, 'sodium': 144.0, 'hemoglobin': 10.7, 'platelet_count': 158.0, 'white_blood_cell_count': 18.41, 'international_normalized_ratio': 1.5}
- stay 600501 (85m) coded **acute_myocardial_infarction** rank=8 p=0.45; top-5 ['heart_failure', 'cardiorenal_syndrome', 'acute_kidney_injury', 'chronic_kidney_disease', 'metabolic_acidosis']; key values {'creatinine': 4.69, 'glucose': 91.0, 'bicarbonate': 20.0, 'potassium': 4.1, 'sodium': 142.0, 'hemoglobin': 11.1, 'platelet_count': 264.0, 'white_blood_cell_count': 7.2, 'troponin_i': 0.084, 'b_type_natriuretic_peptide': 8770.0}
- stay 263850 (62m) coded **chronic_kidney_disease** rank=8 p=0.23; top-5 ['subclinical_hyperthyroidism', 'hyponatremia', 'leukocytosis_pattern', 'acute_kidney_injury', 'hypochloremia']; key values {'creatinine': 1.66, 'glucose': 128.0, 'bicarbonate': 23.0, 'potassium': 4.4, 'sodium': 130.0, 'hemoglobin': 15.4, 'platelet_count': 278.0, 'white_blood_cell_count': 12.73, 'albumin': 4.0, 'international_normalized_ratio': 1.1}
- stay 202707 (78f) coded **cirrhosis_liver_failure** rank=7 p=0.38; top-5 ['thrombocytopenia', 'leukopenia', 'hyperchloremia', 'immune_thrombocytopenia', 'disseminated_intravascular_coagulation']; key values {'creatinine': 0.71, 'glucose': 173.0, 'bicarbonate': 28.0, 'potassium': 3.6, 'sodium': 146.0, 'hemoglobin': 12.4, 'platelet_count': 35.0, 'white_blood_cell_count': 3.1, 'international_normalized_ratio': 1.4}
- stay 3230503 (72m) coded **cirrhosis_liver_failure** rank=13 p=0.16; top-5 ['hyponatremia', 'leukopenia', 'anemia', 'hypochloremia', 'malnutrition']; key values {'creatinine': 1.18, 'glucose': 112.0, 'bicarbonate': 26.0, 'potassium': 4.7, 'sodium': 130.0, 'hemoglobin': 12.6, 'platelet_count': 152.0, 'white_blood_cell_count': 3.5, 'albumin': 3.0, 'international_normalized_ratio': 1.3}

**D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited)**
- stay 2714202 (59m) coded **sepsis** rank=None p=0.00; top-5 ['anemia', 'leukocytosis_pattern', 'hypomagnesemia', 'hypocalcemia', 'bacterial_infection']; key values {'creatinine': 1.1, 'glucose': 95.0, 'bicarbonate': 23.0, 'potassium': 4.1, 'sodium': 138.0, 'hemoglobin': 8.4, 'platelet_count': 351.0, 'white_blood_cell_count': 12.4, 'lactate': 0.9}

