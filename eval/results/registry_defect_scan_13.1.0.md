# Registry defect scan - 13.1.0 (34005 executable rules, 6750 entities)

| class | description | count | examples |
|---|---|---:|---|
| D1 | sex-blind threshold on sex-dimorphic analyte | 800 | [('iron_deficiency_anemia_hb_male_anemia_v1', 'hemoglobin', '<', 13.0, 'F LLN 12.0 / M LLN 13.5'), ('iron_deficiency_anemia_ferritin_iron_depletion_v1', 'ferritin', '<', 15.0, 'F LLN 15.0 / M LLN 30.0'), ('iron_deficienc |
| D2 | unit/scale inconsistency (>=100x, same declared unit) | 34 | [('indirect_bilirubin', 'mg/dL', 0.05, 25.0, 84), ('thyroid_stimulating_hormone', 'u[IU]/mL', 0.1, 10.0, 199), ('aspartate_aminotransferase', 'U/L', 5.0, 1000.0, 173)] |
| D3 | risk-factor feature used for an acute entity | 6 | [('acute_myocardial_infarction_total_cholesterol_screen_v1', 'acute_myocardial_infarction', ['total_cholesterol']), ('acute_myocardial_infarction_ldl_direct_target_v1', 'acute_myocardial_infarction', ['ldl_cholesterol_di |
| D4 | physiologically impossible threshold | 0 | [] |
| D5 | etiologic (non-syndromic) entity proposable from routine analytes only | 100 | [('disseminated_intravascular_coagulation', ['coagulation'], ['d_dimer', 'fibrinogen', 'international_normalized_ratio', 'platelets', 'prothrombin_time'], 2, 6.0), ('warfarin_over_anticoagulation', ['coagulation'], ['pro |
| D6 | feature_id missing from feature registry | 0 | [] |
| D7 | neonate/infant population on adult threshold | 418 | [('chronic_kidney_disease_v1', 'egfr_ckd_epi_creatinine', '<', 60.0, ['adolescent', 'adult', 'child']), ('acute_kidney_injury_v1', 'creatinine', '>', 1.3, ['adolescent', 'adult', 'child']), ('minimal_change_disease_hyper |
| D8 | specific claimed for single routine-analyte diagnostic rule | 91 | [('acute_appendicitis_diagnostic_criterion_1_v1', 'acute_appendicitis', 'procalcitonin'), ('community_acquired_pneumonia_diagnostic_criterion_1_v1', 'community_acquired_pneumonia', 'procalcitonin'), ('elevated_red_blood_ |
| D9 | source_id not in guideline_sources | 0 | [] |
| D10 | single routine analyte with diagnosis_allowed | 0 | [] |

