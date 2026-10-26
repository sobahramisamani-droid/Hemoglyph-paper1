# Reviewer round-2 metrics — engine v7, eICU-CRD demo (2,314 stays, labs only), label-group level

Prediction set at k = label groups whose best flat-list entry has rank ≤ k and whose key analyte is present (the same evaluability rule used for recall). Reference = clinician problem list mapped to 31 groups (admission-level; incompleteness means 'false positives' are an upper bound on true false positives). CIs: stay-cluster bootstrap, 2,000 resamples.

| metric | k=3 | k=5 | k=10 |
|---|---:|---:|---:|
| engine v7 precision@k (%) | 16.5 (15.4–17.6) | 14.2 (13.3–15.2) | 11.8 (11.1–12.6) |
| engine v7 recall@k (%) | 47.9 (45.6–50.3) | 60.8 (58.5–63.0) | 74.1 (72.0–76.0) |
| engine v7 f1@k (%) | 24.6 (23.2–26.0) | 23.1 (21.8–24.3) | 20.4 (19.3–21.5) |
| engine v7 ndcg@k (%) | 53.1 (50.6–55.5) | 56.5 (54.1–58.8) | 60.6 (58.6–62.8) |
| prevalence-ranking baseline precision@k (%) | 12.6 | 10.8 | 8.1 |
| prevalence-ranking baseline recall@k (%) | 36.1 | 51.3 | 76.8 |
| prevalence-ranking baseline f1@k (%) | 18.7 | 17.8 | 14.7 |
| prevalence-ranking baseline ndcg@k (%) | 34.9 | 39.0 | 49.9 |
| engine: label-group assertions per stay | 3.04 | 4.49 | 6.57 |

Alert burden: mean 8.0 (median 8, IQR 5–11) label-group entries in the full flat differential (max list length 25); mean flat list carries 4.8 entries in the top-5.

## Per-group PPV and sensitivity at k = 5 (problem-list reference)

| group | coded (evaluable) | asserted@5 | PPV@5 (%) | sensitivity@5 (%) | prevalence baseline sens@5 (%) |
|---|---:|---:|---:|---:|---:|
| renal_impairment | 326 | 1066 | 25 | 81 | 100 |
| sepsis | 289 | 532 | 27 | 49 | 100 |
| diabetes | 246 | 611 | 18 | 45 | 100 |
| acute_kidney_injury | 218 | 947 | 18 | 78 | 100 |
| chronic_kidney_disease | 148 | 239 | 22 | 36 | 100 |
| anemia | 147 | 1141 | 11 | 83 | 7 |
| gi_bleeding | 145 | 1123 | 10 | 78 | 3 |
| diabetic_ketoacidosis | 107 | 98 | 69 | 64 | 3 |
| hyperglycemia | 96 | 611 | 7 | 47 | 0 |
| acute_myocardial_infarction | 84 | 436 | 17 | 88 | 1 |
| hypokalemia | 67 | 259 | 13 | 49 | 0 |
| heart_failure | 58 | 168 | 29 | 83 | 0 |
| leukocytosis | 57 | 597 | 4 | 40 | 2 |
| hyponatremia | 52 | 246 | 13 | 63 | 0 |
| metabolic_acidosis | 51 | 444 | 6 | 55 | 0 |
| hyperkalemia | 49 | 77 | 31 | 49 | 0 |
| thrombocytopenia | 40 | 300 | 9 | 65 | 2 |
| hypomagnesemia | 37 | 161 | 8 | 35 | 0 |
| alcohol_withdrawal | 33 | 90 | 12 | 33 | 0 |
| coagulopathy | 28 | 119 | 11 | 46 | 0 |
| cirrhosis_liver_failure | 25 | 187 | 8 | 60 | 0 |
| hypoglycemia | 21 | 13 | 38 | 24 | 0 |
| lactic_acidosis | 19 | 154 | 8 | 63 | 0 |
| acute_pancreatitis | 18 | 54 | 22 | 67 | 0 |
| malnutrition | 16 | 150 | 0 | 0 | 0 |
| hypernatremia | 14 | 49 | 16 | 57 | 0 |
| rhabdomyolysis | 11 | 43 | 14 | 55 | 0 |
| hypocalcemia | 10 | 359 | 0 | 10 | 0 |
| hypothyroidism | 10 | 26 | 12 | 30 | 0 |

Interpretation: PPV against an admission problem list is a lower bound (uncoded but present conditions count as false positives); it is reported to quantify alert burden, not accuracy.

## Criterion-supported precision at k = 5 (addendum 2026-10-26)

Of 10,380 label-group assertions in the top-5, 1,479 (14.2%) are on the problem list (= precision@5). Of the remaining 8,901: 5,684 (54.8% of all assertions) satisfy the group's fixed laboratory criterion in the same panel (laboratory-supported but uncoded), 1,309 (12.6%) do not satisfy it (criterion-negative: the closest thing to a verified false positive without a clinician), and 1,908 (18.4%) belong to groups without a single-analyte criterion or lack the criterion analyte.
Upper-bound precision (coded OR criterion-positive) = 69.0%; lower bound = 14.2%; criterion-negative share = 12.6%.

| group | asserted@5 | coded | uncoded, criterion-positive | uncoded, criterion-negative | no criterion / analyte |
|---|---:|---:|---:|---:|---:|
| anemia | 1141 | 122 | 961 | 58 | 0 |
| gi_bleeding | 1123 | 113 | 0 | 0 | 1010 |
| renal_impairment | 1066 | 265 | 541 | 260 | 0 |
| acute_kidney_injury | 947 | 169 | 556 | 222 | 0 |
| diabetes | 611 | 111 | 201 | 299 | 0 |
| hyperglycemia | 611 | 45 | 397 | 169 | 0 |
| leukocytosis | 597 | 23 | 574 | 0 | 0 |
| sepsis | 532 | 142 | 0 | 0 | 390 |
| metabolic_acidosis | 444 | 28 | 345 | 71 | 0 |
| acute_myocardial_infarction | 436 | 74 | 310 | 52 | 0 |
| hypocalcemia | 359 | 1 | 250 | 108 | 0 |
| thrombocytopenia | 300 | 26 | 274 | 0 | 0 |
| hypokalemia | 259 | 33 | 226 | 0 | 0 |
| hyponatremia | 246 | 33 | 213 | 0 | 0 |
| chronic_kidney_disease | 239 | 53 | 163 | 23 | 0 |
| cirrhosis_liver_failure | 187 | 15 | 0 | 0 | 172 |
| heart_failure | 168 | 48 | 112 | 8 | 0 |
| hypomagnesemia | 161 | 13 | 148 | 0 | 0 |
| lactic_acidosis | 154 | 12 | 139 | 3 | 0 |
| malnutrition | 150 | 0 | 0 | 0 | 150 |
| coagulopathy | 119 | 13 | 0 | 0 | 106 |
| diabetic_ketoacidosis | 98 | 68 | 13 | 16 | 1 |
| alcohol_withdrawal | 90 | 11 | 0 | 0 | 79 |
| hyperkalemia | 77 | 24 | 53 | 0 | 0 |
| hypophosphatemia | 62 | 2 | 60 | 0 | 0 |
| acute_pancreatitis | 54 | 12 | 41 | 1 | 0 |
| hypernatremia | 49 | 8 | 41 | 0 | 0 |
| rhabdomyolysis | 43 | 6 | 31 | 6 | 0 |
