# Black-box property conformance — frozen engine v7 vs unnamed frontier LLM (identical perturbed panels)

| property | engine | LLM |
|---|---|---|
| P2_units: top-5 Jaccard vs original (identical/n) | 0.98 (36/40) live twin; 0.93 (31/40) vs stored run; label Δ +0 | 0.72 (8/40); label Δ +3
| P3_presentation: top-5 Jaccard vs original (identical/n) | 0.96 (35/40) live twin; 0.91 (30/40) vs stored run; label Δ +0 | 0.73 (10/40); label Δ +3
| P4 monotonicity violations / ladders | 2/20 | 0/20 |
| P5 unsupported assertions (target still at rank ≤ 5 without its analyte) | 3/40 | 14/40 |
| P5 post hoc: panels with no redundant analyte left (n = 29) | 1/29 | 4/29 |

## Notes

- Engine reference for P2/P3: live run on the conventional-unit twin built by the same generator (deterministic). LLM reference: the original blind reading from a different session, so LLM Jaccard also contains session-to-session variability (κ 0.69).
- P4 LLM reads were produced with the creatinine ladder visible (the panel key carries the ladder), so 0/20 is not a blind test for the LLM; the engine was run on each panel independently.
- P5 post hoc row (declared after the first scoring run): excludes panels in which a redundant analyte (haematocrit for haemoglobin; CK-MB/troponin T for troponin I; anion gap/pH/base excess for bicarbonate) remained, because asserting the target from it is clinically supported.
- P6 (healthy adults) is not re-run here: the pre-existing blind B5 test on NHANES 2017-18 (40 guideline-healthy adults, same blind reader) already covers it: LLM 4/40 false assertions vs engine 0/40.

## P5 detail (stay, target, removed analyte, engine unsupported, LLM unsupported, redundant analytes present)

- ('1291973', 'acute_myocardial_infarction', 'troponin_i', False, False, [])
- ('280350', 'heart_failure', 'b_type_natriuretic_peptide', False, False, [])
- ('2787684', 'hypernatremia', 'sodium', False, False, [])
- ('3092621', 'thrombocytopenia', 'platelet_count', False, False, [])
- ('688938', 'hypomagnesemia', 'magnesium', False, False, [])
- ('2857326', 'hyponatremia', 'sodium', False, False, [])
- ('2751276', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('3141080', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('2859392', 'acute_pancreatitis', 'lipase', False, False, [])
- ('2872788', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('1067235', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('2832466', 'anemia', 'hemoglobin', False, True, ['hematocrit'])
- ('2757872', 'acute_myocardial_infarction', 'troponin_i', False, True, ['creatine_kinase_mb'])
- ('2523738', 'anemia', 'hemoglobin', True, True, ['hematocrit'])
- ('2596753', 'diabetic_ketoacidosis', 'glucose', False, True, [])
- ('2758779', 'acute_myocardial_infarction', 'troponin_i', False, False, ['creatine_kinase_mb'])
- ('939222', 'anemia', 'hemoglobin', False, True, ['hematocrit'])
- ('1278738', 'hyperglycemia', 'glucose', False, False, [])
- ('221005', 'anemia', 'hemoglobin', False, True, ['hematocrit'])
- ('387984', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('562305', 'diabetic_ketoacidosis', 'glucose', False, True, [])
- ('347475', 'heart_failure', 'b_type_natriuretic_peptide', False, True, [])
- ('2108150', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('539482', 'thrombocytopenia', 'platelet_count', False, False, [])
- ('264276', 'anemia', 'hemoglobin', False, True, ['hematocrit'])
- ('1835141', 'hyperglycemia', 'glucose', False, False, [])
- ('1297084', 'heart_failure', 'b_type_natriuretic_peptide', False, False, [])
- ('2248699', 'acute_pancreatitis', 'lipase', False, False, [])
- ('1599068', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('257802', 'anemia', 'hemoglobin', True, True, ['hematocrit'])
- ('1118948', 'anemia', 'hemoglobin', False, True, ['hematocrit'])
- ('2602775', 'diabetic_ketoacidosis', 'glucose', False, True, [])
- ('3009480', 'renal_impairment', 'creatinine', False, False, [])
- ('3214314', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('3033797', 'hyperkalemia', 'potassium', False, False, [])
- ('1758977', 'anemia', 'hemoglobin', False, True, ['hematocrit'])
- ('2371837', 'acute_kidney_injury', 'creatinine', True, False, [])
- ('2935023', 'acute_kidney_injury', 'creatinine', False, False, [])
- ('2695180', 'metabolic_acidosis', 'bicarbonate', False, True, ['anion_gap'])
- ('302668', 'heart_failure', 'b_type_natriuretic_peptide', False, False, [])
