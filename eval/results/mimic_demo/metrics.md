# Retrospective evaluation — metrics

Cases: 30; groups: 12; configurations: full, rule_only, naive_bayes, mean_fusion.

## Primary and secondary outcomes

| Config | top-1 | top-3 (primary) | top-5 | MRR | Brier(target) | ECE(top-1) | median ms |
|---|---|---|---|---|---|---|---|
| full | 13.3% (5.3–29.7) | **13.3% (5.3–29.7)** | 26.7% (14.2–44.4) | 0.187 | 0.576 | 0.662 | 1204 |
| rule_only | 13.3% (5.3–29.7) | **20.0% (9.5–37.3)** | 26.7% (14.2–44.4) | 0.193 | 0.558 | 0.714 | 1072 |
| naive_bayes | 13.3% (5.3–29.7) | **16.7% (7.3–33.6)** | 23.3% (11.8–40.9) | 0.189 | 0.571 | 0.676 | 1062 |
| mean_fusion | 10.0% (3.5–25.6) | **16.7% (7.3–33.6)** | 16.7% (7.3–33.6) | 0.158 | 0.571 | 0.806 | 0 |

### Lab-detectable groups only

| Config | n | top-1 | top-3 | top-5 |
|---|---|---|---|---|
| full | 15 | 26.7% (10.9–52.0) | 26.7% (10.9–52.0) | 46.7% (24.8–69.9) |
| rule_only | 15 | 26.7% (10.9–52.0) | 33.3% (15.2–58.3) | 46.7% (24.8–69.9) |
| naive_bayes | 15 | 26.7% (10.9–52.0) | 33.3% (15.2–58.3) | 40.0% (19.8–64.3) |
| mean_fusion | 15 | 20.0% (7.0–45.2) | 33.3% (15.2–58.3) | 33.3% (15.2–58.3) |

## Paired comparison vs full (top-3)

| Comparator | full✓ comp✗ | full✗ comp✓ | Δ top-3 (full − comp) | bootstrap 95% CI | McNemar mid-p |
|---|---|---|---|---|---|
| rule_only | 0 | 2 | -6.7 pp | -16.7 to +0.0 | 0.2500 |
| naive_bayes | 0 | 1 | -3.3 pp | -10.0 to +0.0 | 0.5000 |
| mean_fusion | 0 | 1 | -3.3 pp | -10.0 to +0.0 | 0.5000 |

## Calibration of top-1 probability (full), ECE = 0.662

| bin | n | mean confidence | observed top-1 accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | — | — |
| 0.1–0.2 | 0 | — | — |
| 0.2–0.3 | 0 | — | — |
| 0.3–0.4 | 0 | — | — |
| 0.4–0.5 | 0 | — | — |
| 0.5–0.6 | 2 | 0.58 | 0.00 |
| 0.6–0.7 | 6 | 0.65 | 0.00 |
| 0.7–0.8 | 5 | 0.79 | 0.20 |
| 0.8–0.9 | 13 | 0.85 | 0.08 |
| 0.9–1.0 | 4 | 0.95 | 0.50 |

## Evidence state of the top candidate vs correctness (full)

- top candidate 'supported': n=29, top-1 correct 13.8% (5.5–30.6)
- top candidate other state: n=1, top-1 correct 0.0% (0.0–79.3)
- mean Bel–Pl gap of target when top-1 correct 0.186 vs otherwise 0.536

## Per-group top-3 (full / rule_only / naive_bayes / mean_fusion)

| Group | n | detectable | full | rule_only | naive_bayes | mean_fusion |
|---|---|---|---|---|---|---|
| sepsis | 5 | partial | 0.0% (-0.0–43.4) | 20.0% (3.6–62.4) | 0.0% (-0.0–43.4) | 0.0% (-0.0–43.4) |
| acute_myocardial_infarction | 4 | yes | 75.0% (30.1–95.4) | 75.0% (30.1–95.4) | 75.0% (30.1–95.4) | 75.0% (30.1–95.4) |
| acute_kidney_injury | 4 | yes | 0.0% (0.0–49.0) | 25.0% (4.6–69.9) | 25.0% (4.6–69.9) | 0.0% (0.0–49.0) |
| type_2_diabetes | 3 | yes | 33.3% (6.1–79.2) | 33.3% (6.1–79.2) | 33.3% (6.1–79.2) | 66.7% (20.8–93.9) |
| heart_failure | 3 | yes | 0.0% (0.0–56.2) | 0.0% (0.0–56.2) | 0.0% (0.0–56.2) | 0.0% (0.0–56.2) |
| hepatic_encephalopathy | 2 | partial | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) |
| community_acquired_pneumonia | 2 | partial | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) |
| pulmonary_embolism | 2 | partial | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) |
| cirrhosis | 2 | partial | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) | 0.0% (0.0–65.8) |
| acute_myeloid_leukemia | 1 | yes | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) |
| alcoholic_liver_disease | 1 | partial | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) |
| protein_energy_malnutrition | 1 | partial | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) | 0.0% (0.0–79.3) |

## First 100 top-3 misses of full (for clinician error classification)

| hadm_id | group | target rank | top-5 (p) |
|---|---|---|---|
| 21476294 | acute_myeloid_leukemia | — | acute_kidney_injury (0.59), eosinophilia (0.56), leukocytosis_pattern (0.56), immune_thrombocytopenia (0.55), thrombocytopenia (0.52) |
| 25864431 | hepatic_encephalopathy | — | alcoholic_hepatitis_pattern (0.88), chronic_kidney_disease (0.85), alcoholic_liver_pattern (0.82), metabolic_acidosis (0.82), liver_cirrhosis (0.66) |
| 27487226 | community_acquired_pneumonia | — | chronic_lymphocytic_leukemia (0.88), heart_failure (0.85), cardiorenal_syndrome (0.83), chronic_kidney_disease (0.79), metabolic_acidosis (0.77) |
| 27993466 | pulmonary_embolism | — | metabolic_acidosis (0.81), anemia (0.68), acute_kidney_injury (0.66), hyponatremia (0.64), thrombocytopenia (0.52) |
| 28335091 | acute_myocardial_infarction | — | diabetes_mellitus (0.66), anemia (0.63), hypochloremia (0.63), hyponatremia (0.63), leukocytosis_pattern (0.59) |
| 26013492 | acute_kidney_injury | 6 | neutrophilia_pattern (0.68), anemia (0.67), leukocytosis_pattern (0.59), lymphocytosis (0.59), hypocalcemia (0.59) |
| 26793610 | acute_kidney_injury | 5 | sideroblastic_anemia (0.88), chronic_kidney_disease (0.85), hemochromatosis (0.83), metabolic_acidosis (0.76), acute_kidney_injury (0.64) |
| 23819016 | sepsis | — | lactic_acidosis (0.83), gallstone_pancreatitis_support_pattern (0.81), acute_pancreatitis (0.79), metabolic_acidosis (0.77), hypocalcemia (0.64) |
| 22413744 | sepsis | 12 | metabolic_acidosis (0.82), chronic_kidney_disease (0.65), hypomagnesemia (0.64), hyponatremia (0.64), anemia_of_chronic_disease (0.63) |
| 22251969 | acute_kidney_injury | 5 | chronic_kidney_disease (0.83), anemia_of_chronic_disease (0.74), hyperphosphatemia (0.64), hypochloremia (0.64), acute_kidney_injury (0.6) |
| 29279905 | sepsis | 12 | nephrotic_syndrome (0.79), metabolic_acidosis (0.77), hypoxemia (0.69), neutrophilia_pattern (0.68), chronic_kidney_disease (0.68) |
| 22987108 | cirrhosis | 12 | hypochloremia (0.64), hyponatremia (0.64), metabolic_acidosis (0.63), hyperkalemia (0.62), acute_kidney_injury (0.62) |
| 24928679 | cirrhosis | 4 | chronic_kidney_disease (0.85), metabolic_acidosis (0.76), anemia (0.68), liver_cirrhosis (0.65), acute_kidney_injury (0.64) |
| 22205327 | pulmonary_embolism | — | acute_myocardial_infarction (0.95), ischemic_hepatitis_pattern (0.95), metabolic_acidosis (0.88), nephrotic_syndrome (0.79), acute_kidney_injury (0.7) |
| 27189241 | community_acquired_pneumonia | — | anemia_of_chronic_disease (0.79), nephrotic_syndrome (0.79), hypocalcemia (0.64), hypoxemia (0.64), anemia (0.63) |
| 28887654 | heart_failure | — | metabolic_acidosis (0.77), acute_kidney_injury (0.62), chronic_kidney_disease (0.62), anemia (0.61), isolated_hyperbilirubinemia_pattern (0.59) |
| 23488445 | sepsis | 9 | nephrotic_syndrome (0.79), metabolic_acidosis (0.76), neutrophilia_pattern (0.68), hypocalcemia (0.64), leukocytosis_pattern (0.59) |
| 25933959 | type_2_diabetes | 4 | hypermagnesemia (0.64), hyperphosphatemia (0.64), hypochloremia (0.64), diabetes_mellitus (0.63), acute_kidney_injury (0.61) |
| 27259207 | type_2_diabetes | — | fasting_hypoglycemia (0.83), prerenal_azotemia (0.76), acute_kidney_injury (0.74), chronic_kidney_disease (0.72), anemia_of_chronic_disease (0.7) |
| 29488258 | hepatic_encephalopathy | — | chronic_kidney_disease (0.85), metabolic_acidosis (0.75), anemia (0.65), acute_kidney_injury (0.64), hypermagnesemia (0.64) |
| 24698912 | sepsis | — | chronic_kidney_disease (0.86), metabolic_acidosis (0.83), anemia_of_chronic_disease (0.74), acute_kidney_injury (0.65), hyperphosphatemia (0.64) |
| 26228185 | acute_kidney_injury | 12 | chronic_lymphocytic_leukemia (0.95), metabolic_acidosis (0.76), anemia (0.67), diabetes_mellitus (0.66), leukocytosis_pattern (0.59) |
| 24420677 | heart_failure | — | acute_kidney_injury (0.58), chronic_kidney_disease (0.52), anemia (0.5), thrombocytopenia (0.5), type_2_diabetes (0.49) |
| 21607814 | heart_failure | — | cholestasis (0.65), hypochloremia (0.62), anemia (0.6), acute_kidney_injury (0.59), isolated_hyperbilirubinemia_pattern (0.59) |
| 20093566 | alcoholic_liver_disease | 11 | metabolic_acidosis (0.87), chronic_kidney_disease (0.85), anemia_of_chronic_disease (0.74), acute_kidney_injury (0.64), hyperphosphatemia (0.64) |
| 23052851 | protein_energy_malnutrition | — | chronic_kidney_disease (0.62), hypomagnesemia (0.59), leukopenia (0.59), dehydration (0.55), diabetes_insipidus (0.55) |

Error-classification scheme (to be applied by the clinical co-author, blinded to configuration): (A) knowledge gap — no rule/LR covers the pattern; (B) fusion/ranking error — correct candidate present but out-ranked; (C) label noise — ICD primary code not supported by the labs; (D) not lab-detectable from first-24 h panel; (E) input problem — unit/mapping.