# Black-box property conformance — engine under test (working tree) vs unnamed frontier LLM (identical perturbed panels)

| property | engine | LLM |
|---|---|---|
| P2_units: top-5 Jaccard vs original (identical/n) | 1.00 (40/40) live twin; 0.95 (34/40) vs stored run; label Δ +0 | 0.72 (8/40); label Δ +3
| P3_presentation: top-5 Jaccard vs original (identical/n) | 0.96 (35/40) live twin; 0.91 (30/40) vs stored run; label Δ +0 | 0.73 (10/40); label Δ +3
| P4 monotonicity violations / ladders | 2/20 | 0/20 |
| P5 unsupported assertions (target still at rank ≤ 5 without its analyte) | 3/40 | 14/40 |
| P5 post hoc: panels with no redundant analyte left (n = 29) | 1/29 | 4/29 |

## Notes

- Engine reference for P2/P3: live run on the conventional-unit twin built by the same generator (deterministic). LLM reference: the original blind reading from a different session, so LLM Jaccard also contains session-to-session variability (κ 0.69).
- P4 LLM reads were produced with the creatinine ladder visible (the panel key carries the ladder), so 0/20 is not a blind test for the LLM; the engine was run on each panel independently.
- P5 post hoc row (declared after the first scoring run): excludes panels in which a redundant analyte (haematocrit for haemoglobin; CK-MB/troponin T for troponin I; anion gap/pH/base excess for bicarbonate) remained, because asserting the target from it is clinically supported.
- Engine arm = the working-tree engine (v8.1 at the first run; v8.2 after the alias-unit fix below). The first run (RESULTS_before_fix_v8.1.md) found 4/40 P2 twins non-identical; all four traced to one defect: a record mirrored under an engine-internal legacy id (bilirubin_total) kept its reported unit, so a normal bilirubin of 9 µmol/L was compared with the 8 mg/dL panic threshold (false critical alert; cholestasis 0.49 -> 0.58). Fixed in v8.2 (alias ids resolve to registry metadata before canonicalisation); regression test tests/test_properties.py::test_p2_unit_invariance_legacy_alias_ids fails before and passes after the fix; the 705-test suite passes. v7 frozen results are untouched.
- P3 residual (5/40): three stays where the generator's alias distractors (mcv 89, tsh 1.8) duplicated an analyte already present with a different value (measured MCV 100.5; TSH 4.7/4.3), i.e. the perturbation was not value-preserving there; two stays with differentials shorter than five entries, where 0.15-probability items entered the top-5 set. No engine defect was identified in P3.
- P4 engine violations (2/20): in both, the renal cluster's best rank fell at the x2.0 step because the engine switched from 'reduced GFR, chronicity undetermined' (anchor 0.92) to 'acute kidney injury' at a lower score; recorded as a candidate v9 item, not changed here.
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
