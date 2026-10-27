# Hybrid arm — frozen engine v7 + out-of-fold supervised layer (eICU-CRD demo, 2,314 stays, group-level recall)

Declared post-freeze experiment (2026-10-27). Group-level metric; not comparable to the flat entity-level Table 3. `hybrid` = max(engine, ML) for all groups; `hybrid6` = engine except the six groups without a single-analyte criterion. No weight or threshold was fitted; ML probabilities are 5-fold out-of-fold.

| ranker | recall@3 | recall@5 | recall@10 | Δ@5 vs engine (95% bootstrap CI) |
|---|---:|---:|---:|---|
| engine (group-level) | 42.3 | 58.8 | 80.1 | — |
| ML only | 54.3 | 68.8 | 86.7 | +10.0 (+7.6 to +12.3) |
| hybrid (all groups) | 44.3 | 60.6 | 85.6 | +1.8 (+1.2 to +2.5) |
| hybrid6 (six outcome groups) | 42.8 | 59.8 | 83.5 | +1.0 (+0.4 to +1.5) |

Scorable labels: 2432.

## Per-group recall@5 (hits/labels)

| group | n | engine | ML | hybrid | hybrid6 |
|---|---:|---:|---:|---:|---:|
| acute_kidney_injury | 218 | 64% | 85% | 64% | 62% |
| chronic_kidney_disease | 148 | 16% | 65% | 22% | 15% |
| renal_impairment | 326 | 82% | 97% | 82% | 81% |
| diabetes | 246 | 43% | 91% | 46% | 48% |
| hyperglycemia | 96 | 41% | 53% | 40% | 39% |
| diabetic_ketoacidosis | 107 | 61% | 87% | 73% | 61% |
| hypoglycemia | 21 | 29% | 5% | 29% | 29% |
| hypokalemia | 67 | 42% | 25% | 43% | 42% |
| hyperkalemia | 49 | 51% | 59% | 51% | 51% |
| hyponatremia | 52 | 63% | 38% | 63% | 63% |
| hypernatremia | 14 | 64% | 0% | 64% | 64% |
| hypomagnesemia | 37 | 41% | 3% | 43% | 41% |
| hypocalcemia | 10 | 20% | 0% | 20% | 20% |
| hypercalcemia | 1 | 100% | 0% | 100% | 100% |
| hypophosphatemia | 9 | 67% | 0% | 56% | 67% |
| metabolic_acidosis | 51 | 59% | 12% | 59% | 59% |
| lactic_acidosis | 19 | 63% | 0% | 63% | 63% |
| anemia | 147 | 82% | 69% | 82% | 82% |
| thrombocytopenia | 40 | 62% | 20% | 60% | 60% |
| leukocytosis | 57 | 56% | 14% | 56% | 56% |
| sepsis | 289 | 49% | 94% | 54% | 55% |
| hypothyroidism | 10 | 40% | 0% | 40% | 40% |
| cirrhosis_liver_failure | 25 | 60% | 16% | 60% | 60% |
| acute_pancreatitis | 18 | 61% | 39% | 61% | 61% |
| acute_myocardial_infarction | 84 | 95% | 61% | 95% | 95% |
| heart_failure | 58 | 88% | 88% | 88% | 88% |
| rhabdomyolysis | 11 | 55% | 0% | 55% | 55% |
| coagulopathy | 28 | 57% | 18% | 57% | 57% |
| malnutrition | 16 | 0% | 6% | 0% | 6% |
| gi_bleeding | 145 | 77% | 78% | 77% | 78% |
| alcohol_withdrawal | 33 | 30% | 24% | 33% | 42% |
