# Executable verifier behind the LLM — 400 blind eICU stays, no new LLM call

Labels: 596 (b8 rule). Entry verdicts over 2424 LLM entries: absent 15, contradicted 182, not_verifiable 263, out_of_vocabulary 525, supported 1439

| Arm | recall@1 | @3 | @5 | @10 |
|---|---|---|---|---|
| A_llm_raw | 28.2 | 50.8 | 59.6 | 65.1 |
| B_llm_demoted | 29.4 | 50.3 | 59.4 | 65.1 |
| C_llm_removed | 29.4 | 50.2 | 58.4 | 63.8 |
| D_engine_v7 | 24.0 | 47.0 | 60.7 | 72.0 |

Paired difference (stay-clustered bootstrap, 4000 reps), points:
- paired_B_minus_A: @1 +1.2 (+0.2 to +2.3, p=0.014); @3 -0.5 (-1.3 to +0.2, p=0.227); @5 -0.2 (-0.5 to +0.0, p=0.753); @10 +0.0 (+0.0 to +0.0, p=1.000)
- paired_C_minus_A: @1 +1.2 (+0.2 to +2.3, p=0.014); @3 -0.7 (-1.6 to +0.0, p=0.123); @5 -1.2 (-2.1 to -0.4, p=0.001); @10 -1.3 (-2.4 to -0.5, p=0.001)

Unsupported assertions among mapped top-5 entries: LLM raw 140/1486 (9.4 %); LLM after demotion 84/1464 (5.7 %); engine v7 top-5 (criterion groups) 233/1518 (15.3 %).
Verifier cost: 10 of 197 demoted entries were clinician labels (5.1 %):
  - stay 1278738: 'prerenal azotemia / GI bleeding (BUN/Cr 40)' [contradicted] labels ['gi_bleeding'] vals {'hemoglobin': 11.4}
  - stay 294032: 'acute respiratory acidosis / hypercapnic respiratory failure' [contradicted] labels ['metabolic_acidosis'] vals {'bicarbonate': 28.2}
  - stay 2825782: 'high anion gap metabolic acidosis (alcoholic ketoacidosis / toxic alcohol)' [contradicted] labels ['alcohol_withdrawal'] vals {'aspartate_aminotransferase': 160.0}
  - stay 3131438: 'hyperglycemia stress' [contradicted] labels ['hyperglycemia'] vals {'glucose': 134.0}
  - stay 1772933: 'prerenal azotemia / GI bleeding (BUN 47/Cr 1.07)' [contradicted] labels ['gi_bleeding'] vals {'hemoglobin': 10.2}
  - stay 2684065: 'prerenal azotemia mild' [contradicted] labels ['renal_impairment'] vals {'creatinine': 0.94}
  - stay 3086265: 'acute hypercapnic respiratory failure / respiratory acidosis with hypoxemia (pCO2 56, pO2 56, pH 7.24)' [contradicted] labels ['metabolic_acidosis'] vals {'bicarbonate': 26.0}
  - stay 426975: 'coagulopathy' [contradicted] labels ['coagulopathy'] vals {'international_normalized_ratio': 1.4}
  - stay 310446: 'metabolic acidosis / DKA (possible)' [absent] labels ['diabetic_ketoacidosis'] vals {'glucose': 382.0, 'bicarbonate': None}
  - stay 2767923: 'high anion gap metabolic acidosis / early DKA' [contradicted] labels ['diabetic_ketoacidosis'] vals {'glucose': 353.0, 'bicarbonate': 24.0}

Sensitivity (post hoc): 34 of the LLM's unsupported top-5 entries are respiratory-acidosis names mapped to the metabolic-acidosis group by the frozen synonym map; excluding them, 106/1486 (7.1 %).
Engine top-5 unsupported by group (criterion is a proxy stricter than some engine rules; e.g. the diabetes label group also contains hyperglycaemia ids while its criterion is glucose >= 200 mg/dL or HbA1c >= 6.5 %):
  - diabetes contradicted: 54/123
  - renal_impairment contradicted: 49/197
  - acute_kidney_injury contradicted: 39/170
  - hyperglycemia contradicted: 33/123
  - hypocalcemia contradicted: 17/53
  - metabolic_acidosis contradicted: 13/85
  - anemia contradicted: 5/202
  - acute_myocardial_infarction contradicted: 4/78
  - hypothyroidism contradicted: 3/6
  - diabetic_ketoacidosis contradicted: 3/26
  - rhabdomyolysis contradicted: 3/7
  - chronic_kidney_disease contradicted: 2/35
  - hypercalcemia contradicted: 2/3
  - metabolic_acidosis absent: 2/85
  - lactic_acidosis contradicted: 2/28
  - anemia absent: 1/202
  - heart_failure contradicted: 1/38

Criterion verdict vs engine differential (per mapped group with a criterion): crit_True_engine_True 1685, crit_False_engine_True 136, crit_False_engine_False 124, crit_True_engine_False 51

Notes: CRIT's coagulopathy function reads key 'inr' while panels store 'international_normalized_ratio'; aliased here (threshold unchanged). The same gap means the published panel-supported metric treated every coagulopathy label as analyte-missing (excluded); frozen results were not re-run.
Registered predictions (PROTOCOL.md): LLM top-5 unsupported 15-30 %; after demotion < 5 %; recall@5 change -2..+1; demoted-that-were-labels <= 10 %; engine top-5 unsupported 5-15 %.
