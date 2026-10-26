# Structured error audit — eICU-CRD demo, engine v4

Population: every (stay, clinician-listed group) pair with the key analyte measured and the group absent from the top-5 (N = 1218 misses across 2314 stays). A fixed-seed random sample of 200 misses was classified with a pre-declared, deterministic taxonomy (see script header); no manual relabelling.

| Category | n | % of sampled misses |
|---|---:|---:|
| A — not supported by the measured laboratory values (label = history/clinical context) | 118 | 59.0% |
| B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings | 39 | 19.5% |
| C1 — knowledge/logic miss: laboratory signature present, entity never proposed | 21 | 10.5% |
| C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5 | 20 | 10.0% |
| D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited) | 2 | 1.0% |

**Interpretation.** 118 / 200 (59%) of misses carry no laboratory signature of the listed condition and are not recoverable by any laboratory-only system without inventing evidence; 80 (40%) are in principle recoverable (engine-side), of which 21 are knowledge/logic gaps, 20 scoring/severity defects and 39 ranking displacements caused by the five-slot cut-off; 2 reflect the evaluation label map rather than the engine.

## By clinician-listed group (sampled misses)

| group | n | A | B | C1 | C2 | D |
|---|---:|---:|---:|---:|---:|---:|
| sepsis | 34 | 14 | 2 | 12 | 5 | 1 |
| heart_failure | 28 | 25 | 0 | 0 | 3 | 0 |
| diabetes | 25 | 20 | 3 | 0 | 2 | 0 |
| acute_kidney_injury | 10 | 3 | 5 | 0 | 2 | 0 |
| chronic_kidney_disease | 10 | 3 | 5 | 0 | 2 | 0 |
| hypokalemia | 9 | 8 | 1 | 0 | 0 | 0 |
| renal_impairment | 8 | 4 | 4 | 0 | 0 | 0 |
| alcohol_withdrawal | 8 | 3 | 0 | 4 | 0 | 1 |
| diabetic_ketoacidosis | 8 | 6 | 2 | 0 | 0 | 0 |
| hyperglycemia | 6 | 3 | 2 | 0 | 1 | 0 |
| anemia | 5 | 2 | 3 | 0 | 0 | 0 |
| leukocytosis | 5 | 1 | 4 | 0 | 0 | 0 |
| hypomagnesemia | 4 | 3 | 1 | 0 | 0 | 0 |
| acute_myocardial_infarction | 4 | 3 | 0 | 1 | 0 | 0 |
| hyperkalemia | 4 | 1 | 3 | 0 | 0 | 0 |
| acute_pancreatitis | 4 | 4 | 0 | 0 | 0 | 0 |
| coagulopathy | 3 | 1 | 0 | 1 | 1 | 0 |
| thrombocytopenia | 3 | 1 | 2 | 0 | 0 | 0 |
| gi_bleeding | 3 | 2 | 0 | 1 | 0 | 0 |
| hypothyroidism | 3 | 3 | 0 | 0 | 0 | 0 |
| metabolic_acidosis | 3 | 1 | 0 | 0 | 2 | 0 |
| hypernatremia | 2 | 1 | 0 | 1 | 0 | 0 |
| malnutrition | 2 | 1 | 0 | 0 | 1 | 0 |
| hyponatremia | 2 | 1 | 0 | 0 | 1 | 0 |
| lactic_acidosis | 2 | 1 | 0 | 1 | 0 | 0 |
| hypophosphatemia | 2 | 0 | 2 | 0 | 0 | 0 |
| cirrhosis_liver_failure | 1 | 1 | 0 | 0 | 0 | 0 |
| hypoglycemia | 1 | 1 | 0 | 0 | 0 | 0 |
| rhabdomyolysis | 1 | 1 | 0 | 0 | 0 | 0 |

## Examples (first six per category, verbatim engine outputs)

**A — not supported by the measured laboratory values (label = history/clinical context)**
- stay 876268 (78m) coded **renal_impairment** rank=12 p=0.19; top-5 ['liver_cirrhosis', 'anemia', 'thrombocytopenia', 'hypophosphatemia', 'malnutrition']; key values {'creatinine': 1.21, 'glucose': 183.0, 'bicarbonate': 23.2, 'potassium': 3.7, 'sodium': 137.0, 'hemoglobin': 11.5, 'platelet_count': 128.0, 'white_blood_cell_count': 11.0, 'lactate': 1.4, 'albumin': 3.0, 'international_normalized_ratio': 1.5}
- stay 1144659 (77f) coded **sepsis** rank=None p=0.00; top-5 ['heart_failure', 'cardiorenal_syndrome', 'anemia', 'respiratory_alkalosis', 'acute_kidney_injury']; key values {'creatinine': 0.82, 'glucose': 102.0, 'bicarbonate': 25.0, 'potassium': 3.7, 'sodium': 142.0, 'hemoglobin': 7.6, 'platelet_count': 157.0, 'white_blood_cell_count': 6.07, 'lactate': 1.5, 'albumin': 2.3, 'international_normalized_ratio': 1.01, 'b_type_natriuretic_peptide': 9155.0}
- stay 2372698 (89f) coded **heart_failure** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'chronic_kidney_disease', 'leukocytosis_pattern', 'anemia', 'hypomagnesemia']; key values {'creatinine': 1.35, 'glucose': 202.0, 'bicarbonate': 25.0, 'potassium': 4.1, 'sodium': 137.0, 'hemoglobin': 11.1, 'platelet_count': 276.0, 'white_blood_cell_count': 13.2, 'lactate': 1.3, 'troponin_i': 2.76}
- stay 1567943 (83m) coded **heart_failure** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'hyperkalemia', 'sepsis', 'elevated_inr_pattern', 'diabetes_mellitus']; key values {'creatinine': 2.0, 'glucose': 333.0, 'bicarbonate': 22.0, 'potassium': 6.1, 'sodium': 134.0, 'hemoglobin': 17.7, 'platelet_count': 346.0, 'white_blood_cell_count': 13.65, 'albumin': 3.6, 'international_normalized_ratio': 2.7, 'troponin_i': 0.186}
- stay 3057805 (79f) coded **hyperglycemia** rank=None p=0.00; top-5 ['hypokalemia', 'anemia', 'acute_gastroenteritis']; key values {'creatinine': 0.77, 'glucose': 108.0, 'bicarbonate': 25.0, 'potassium': 3.1, 'sodium': 139.0, 'hemoglobin': 12.1, 'platelet_count': 177.0, 'white_blood_cell_count': 8.2, 'international_normalized_ratio': 1.0}
- stay 3151890 (62m) coded **hypokalemia** rank=None p=0.00; top-5 ['sepsis', 'anemia', 'leukopenia', 'thrombocytopenia', 'acute_leukemia']; key values {'creatinine': 0.89, 'glucose': 98.0, 'bicarbonate': 25.0, 'potassium': 3.6, 'sodium': 137.0, 'hemoglobin': 9.7, 'platelet_count': 136.0, 'white_blood_cell_count': 1.6}

**B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings**
- stay 975257 (70f) coded **hyperglycemia** rank=7 p=0.68; top-5 ['acute_myocardial_infarction', 'acute_kidney_injury', 'metabolic_acidosis', 'chronic_kidney_disease', 'sepsis']; key values {'creatinine': 4.22, 'glucose': 385.0, 'bicarbonate': 18.0, 'potassium': 4.5, 'sodium': 137.0, 'hemoglobin': 11.2, 'platelet_count': 310.0, 'white_blood_cell_count': 23.7, 'albumin': 3.0, 'international_normalized_ratio': 1.0, 'troponin_i': 0.42}
- stay 1751224 (83m) coded **hypokalemia** rank=7 p=0.63; top-5 ['thalassemia_trait', 'beta_thalassemia_minor', 'beta_thalassemia_trait', 'acute_myocardial_injury', 'metabolic_acidosis']; key values {'creatinine': 1.75, 'glucose': 137.0, 'bicarbonate': 20.0, 'potassium': 3.4, 'sodium': 139.0, 'hemoglobin': 18.8, 'platelet_count': 513.0, 'white_blood_cell_count': 25.6, 'albumin': 4.6, 'international_normalized_ratio': 1.56, 'troponin_i': 0.05}
- stay 1075126 (78f) coded **sepsis** rank=6 p=0.72; top-5 ['acute_myocardial_infarction', 'acute_kidney_injury', 'hypokalemia', 'anemia', 'chronic_kidney_disease']; key values {'creatinine': 3.5, 'glucose': 185.0, 'bicarbonate': 22.2, 'potassium': 2.7, 'sodium': 141.0, 'hemoglobin': 8.9, 'platelet_count': 295.0, 'white_blood_cell_count': 13.41, 'lactate': 1.6, 'international_normalized_ratio': 2.33}
- stay 490809 (71m) coded **renal_impairment** rank=6 p=0.62; top-5 ['hypernatremia', 'sepsis', 'lactic_acidosis', 'diabetes_mellitus', 'hypokalemia']; key values {'creatinine': 2.25, 'glucose': 443.0, 'bicarbonate': 18.9, 'potassium': 3.3, 'sodium': 158.0, 'hemoglobin': 12.9, 'platelet_count': 164.0, 'white_blood_cell_count': 18.28, 'lactate': 5.0, 'albumin': 2.2}
- stay 472359 (63f) coded **anemia** rank=9 p=0.68; top-5 ['refeeding_syndrome', 'hypophosphatemia', 'liver_cirrhosis', 'hepatocellular_injury_pattern', 'elevated_inr_pattern']; key values {'creatinine': 1.75, 'glucose': 250.0, 'bicarbonate': 23.0, 'potassium': 3.4, 'sodium': 140.0, 'hemoglobin': 10.4, 'platelet_count': 36.0, 'white_blood_cell_count': 13.6, 'albumin': 1.7, 'international_normalized_ratio': 2.3}
- stay 3085970 (62m) coded **hypomagnesemia** rank=10 p=0.64; top-5 ['immune_thrombocytopenia', 'acute_pancreatitis', 'hepatocellular_injury_pattern', 'hypokalemia', 'thrombocytopenia']; key values {'creatinine': 0.72, 'glucose': 79.0, 'bicarbonate': 28.0, 'potassium': 2.5, 'sodium': 129.0, 'hemoglobin': 13.3, 'platelet_count': 49.0, 'white_blood_cell_count': 9.9, 'albumin': 3.3, 'troponin_i': 0.509}

**C1 — knowledge/logic miss: laboratory signature present, entity never proposed**
- stay 2309912 (57f) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['hypokalemia', 'leukocytosis_pattern', 'thrombocytopenia', 'hypocalcemia', 'vitamin_d_deficiency']; key values {'creatinine': 0.46, 'glucose': 96.0, 'bicarbonate': 23.0, 'potassium': 3.4, 'sodium': 135.0, 'hemoglobin': 13.3, 'platelet_count': 126.0, 'white_blood_cell_count': 12.1}
- stay 1733584 (60m) coded **sepsis** rank=None p=0.00; top-5 ['respiratory_acidosis', 'hypercalcemia', 'hypocalcemia', 'hyponatremia', 'anemia']; key values {'creatinine': 0.93, 'glucose': 117.0, 'bicarbonate': 33.0, 'potassium': 5.0, 'sodium': 132.0, 'hemoglobin': 9.5, 'platelet_count': 283.0, 'white_blood_cell_count': 9.1, 'lactate': 0.9, 'albumin': 1.5, 'international_normalized_ratio': 1.0, 'b_type_natriuretic_peptide': 94.0}
- stay 2728472 (54m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['sepsis', 'hepatocellular_injury_pattern', 'thrombocytopenia', 'leukopenia', 'anemia']; key values {'creatinine': 0.8, 'glucose': 141.0, 'bicarbonate': 33.0, 'potassium': 4.6, 'sodium': 134.0, 'hemoglobin': 10.2, 'platelet_count': 30.0, 'white_blood_cell_count': 3.2, 'lactate': 3.0, 'albumin': 2.4, 'troponin_i': 1.26}
- stay 741996 (79m) coded **sepsis** rank=None p=0.00; top-5 ['anemia', 'leukopenia', 'thrombocytopenia', 'acute_leukemia', 'aplastic_anemia']; key values {'creatinine': 0.8, 'glucose': 113.0, 'bicarbonate': 29.5, 'potassium': 4.5, 'sodium': 136.0, 'hemoglobin': 8.7, 'platelet_count': 111.0, 'white_blood_cell_count': 2.2, 'albumin': 2.4, 'troponin_i': 0.02, 'b_type_natriuretic_peptide': 246.0}
- stay 2796180 (78m) coded **sepsis** rank=None p=0.00; top-5 ['anemia', 'acute_kidney_injury', 'chronic_kidney_disease', 'leukocytosis_pattern', 'hypocalcemia']; key values {'creatinine': 1.93, 'glucose': 212.0, 'bicarbonate': 28.0, 'potassium': 4.5, 'sodium': 137.0, 'hemoglobin': 5.2, 'platelet_count': 194.0, 'white_blood_cell_count': 15.4, 'albumin': 2.2, 'international_normalized_ratio': 1.4}
- stay 417577 (53f) coded **sepsis** rank=None p=0.00; top-5 ['acute_myocardial_infarction', 'acute_heart_failure_support_pattern', 'leukocytosis_pattern', 'acute_kidney_injury', 'heart_failure_bnp_pattern']; key values {'creatinine': 1.3, 'glucose': 150.0, 'bicarbonate': 19.7, 'potassium': 3.78, 'sodium': 139.4, 'hemoglobin': 17.0, 'platelet_count': 258.0, 'white_blood_cell_count': 14.4, 'lactate': 1.0, 'albumin': 2.9, 'troponin_i': 1.965, 'b_type_natriuretic_peptide': 1684.6}

**C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5**
- stay 3027283 (74m) coded **acute_kidney_injury** rank=6 p=0.48; top-5 ['hyponatremia', 'liver_cirrhosis', 'hypochloremia', 'isolated_hyperbilirubinemia_pattern', 'alcoholic_liver_disease']; key values {'creatinine': 1.4, 'glucose': 134.0, 'bicarbonate': 38.0, 'potassium': 4.1, 'sodium': 120.0, 'albumin': 3.2, 'international_normalized_ratio': 1.16, 'troponin_i': 0.03}
- stay 2699440 (49f) coded **sepsis** rank=6 p=0.18; top-5 ['acute_myocardial_injury', 'acute_myocardial_infarction', 'malnutrition', 'takotsubo_cardiomyopathy', 'type_2_diabetes']; key values {'creatinine': 1.16, 'glucose': 186.0, 'bicarbonate': 23.0, 'potassium': 3.8, 'sodium': 138.0, 'hemoglobin': 13.5, 'platelet_count': 295.0, 'white_blood_cell_count': 8.3, 'lactate': 2.1, 'albumin': 3.2, 'international_normalized_ratio': 1.1, 'troponin_i': 0.07}
- stay 564486 (42m) coded **chronic_kidney_disease** rank=14 p=0.43; top-5 ['metabolic_acidosis', 'hypocalcemia', 'hyponatremia', 'rhabdomyolysis', 'sepsis']; key values {'creatinine': 17.5, 'glucose': 116.0, 'bicarbonate': 12.0, 'potassium': 7.2, 'sodium': 124.0, 'hemoglobin': 8.3, 'platelet_count': 613.0, 'white_blood_cell_count': 33.3, 'lactate': 1.3, 'albumin': 2.2, 'international_normalized_ratio': 1.3}
- stay 2894029 (55f) coded **sepsis** rank=7 p=0.23; top-5 ['anemia', 'frailty', 'pellagra', 'malnutrition', 'bacterial_infection']; key values {'creatinine': 0.79, 'glucose': 181.0, 'bicarbonate': 23.7, 'potassium': 3.6, 'sodium': 138.0, 'hemoglobin': 10.9, 'platelet_count': 184.0, 'white_blood_cell_count': 11.0, 'lactate': 2.1, 'albumin': 2.5}
- stay 3136458 (72f) coded **malnutrition** rank=8 p=0.46; top-5 ['acute_myocardial_infarction', 'heart_failure', 'cardiorenal_syndrome', 'prerenal_azotemia', 'anemia']; key values {'creatinine': 2.0, 'glucose': 89.0, 'bicarbonate': 20.0, 'potassium': 4.2, 'sodium': 137.0, 'hemoglobin': 11.3, 'platelet_count': 192.0, 'white_blood_cell_count': 11.2, 'lactate': 1.2, 'albumin': 1.4, 'troponin_i': 0.11, 'b_type_natriuretic_peptide': 11618.0}
- stay 1090567 (76m) coded **heart_failure** rank=7 p=0.40; top-5 ['chronic_kidney_disease', 'anemia', 'hypokalemia', 'acute_kidney_injury', 'hypocalcemia']; key values {'creatinine': 1.6, 'glucose': 126.0, 'bicarbonate': 22.0, 'potassium': 3.3, 'sodium': 141.0, 'hemoglobin': 10.4, 'platelet_count': 183.0, 'white_blood_cell_count': 7.0, 'lactate': 1.9, 'b_type_natriuretic_peptide': 161.4}

**D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited)**
- stay 197921 (67f) coded **sepsis** rank=None p=0.00; top-5 ['leukocytosis_pattern', 'isolated_hyperbilirubinemia_pattern', 'type_2_diabetes', 'bacterial_infection', 'malnutrition']; key values {'creatinine': 1.3, 'glucose': 151.0, 'bicarbonate': 22.0, 'potassium': 3.7, 'sodium': 137.0, 'hemoglobin': 13.9, 'platelet_count': 273.0, 'white_blood_cell_count': 20.9, 'lactate': 1.6, 'albumin': 3.3, 'international_normalized_ratio': 1.2, 'b_type_natriuretic_peptide': 12.0}
- stay 3111371 (39m) coded **alcohol_withdrawal** rank=None p=0.00; top-5 ['hepatocellular_injury_pattern', 'cholestasis', 'isolated_hyperbilirubinemia_pattern', 'alcoholic_liver_disease', 'primary_biliary_cholangitis']; key values {'creatinine': 0.53, 'glucose': 119.0, 'bicarbonate': 23.0, 'potassium': 3.5, 'sodium': 133.0, 'albumin': 3.7}

