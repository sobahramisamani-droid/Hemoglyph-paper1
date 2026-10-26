# Registry defect scan - 13.3.0 (33230 executable rules, 6750 entities)

| class | description | count | examples |
|---|---|---:|---|
| D1 | sex-blind threshold on sex-dimorphic analyte | 76 | [('iron_deficiency_anemia_ferritin_iron_depletion_v1', 'ferritin', '<', 15.0, 'F LLN 15.0 / M LLN 30.0'), ('iron_deficiency_without_anemia_ferritin_iron_depletion_v1', 'ferritin', '<', 15.0, 'F LLN 15.0 / M LLN 30.0'), ( |
| D2 | unit/scale inconsistency (>=100x, same declared unit) | 32 | [('indirect_bilirubin', 'mg/dL', 0.05, 25.0, 86), ('aspartate_aminotransferase', 'U/L', 5.0, 1000.0, 229), ('thyroid_stimulating_hormone', 'u[IU]/mL', 0.1, 10.0, 144)] |
| D3 | risk-factor feature used for an acute entity | 0 | [] |
| D4 | physiologically impossible threshold | 0 | [] |
| D5 | etiologic (non-syndromic) entity proposable from routine analytes only | 17 | [('disseminated_intravascular_coagulation', ['coagulation'], ['d_dimer', 'fibrinogen', 'international_normalized_ratio', 'platelets', 'prothrombin_time'], 2, 6.0), ('warfarin_over_anticoagulation', ['coagulation'], ['pro |
| D6 | feature_id missing from feature registry | 0 | [] |
| D7 | neonate/infant population on adult threshold | 0 | [] |
| D8 | specific claimed for single routine-analyte diagnostic rule | 0 | [] |
| D9 | source_id not in guideline_sources | 0 | [] |
| D10 | single routine analyte with diagnosis_allowed | 0 | [] |


## Second-wave classes

| class | description | count | examples |
|---|---|---:|---|
| D13 | duplicate executable rules (same entity/type/expression) | 0 | [] |
| D14 | exclusion co-fires with its own proposing rule | 0 | [] |
| D15 | screening weight above strongest diagnostic weight | 1 | [('latent_autoimmune_diabetes', 'latent_autoimmune_diabetes_screening_3_v1', 3.0, 0.5)] |
| D16 | single-leaf exclusion threshold inside reference range | 31 | [('primary_hypothyroidism_exclusion_tsh_normal_v1', 'thyroid_stimulating_hormone', '<', 4.0, (0.45, 4.5)), ('primary_hyperparathyroidism_exclusion_no_hypercalcemia_v1', 'calcium_total', '<', 10.2, (8.6, 10.3)), ('alpha_1 |
