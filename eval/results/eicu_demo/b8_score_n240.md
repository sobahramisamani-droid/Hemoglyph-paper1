# B8 — blind LLM vs Hemoglyph v5.1 (labs-only), 240 new eICU-demo stays

stays 240; scorable labels 456

| | Recall@5 |
|---|---|
| Hemoglyph | 64.3% (59.8–68.5; 293/456) |
| GPT-4-class LLM (agent, blind) | 58.3% (53.8–62.8; 266/456) |

Discordant: engine-only 61, LLM-only 34; McNemar exact p = 0.0073; difference +5.9 pp

| group | n | Hemoglyph | LLM |
|---|---:|---|---|
| sepsis | 58 | 36% | 45% |
| renal_impairment | 55 | 80% | 73% |
| diabetes | 44 | 64% | 41% |
| acute_kidney_injury | 35 | 80% | 77% |
| gi_bleeding | 34 | 88% | 53% |
| anemia | 29 | 90% | 90% |
| chronic_kidney_disease | 27 | 48% | 7% |
| diabetic_ketoacidosis | 22 | 77% | 82% |
| acute_myocardial_infarction | 19 | 89% | 79% |
| hyperglycemia | 18 | 61% | 67% |
| hypokalemia | 14 | 57% | 43% |
| heart_failure | 12 | 100% | 92% |
| metabolic_acidosis | 11 | 45% | 73% |
| alcohol_withdrawal | 9 | 33% | 56% |
| leukocytosis | 8 | 25% | 38% |
| hyponatremia | 7 | 57% | 57% |
| hyperkalemia | 7 | 86% | 100% |
| thrombocytopenia | 6 | 67% | 67% |
| malnutrition | 6 | 0% | 0% |
| lactic_acidosis | 6 | 50% | 50% |
| coagulopathy | 5 | 40% | 40% |
| hypoglycemia | 4 | 0% | 0% |
| hypomagnesemia | 4 | 25% | 50% |
| cirrhosis_liver_failure | 4 | 75% | 50% |
| hypernatremia | 3 | 33% | 67% |
| rhabdomyolysis | 2 | 50% | 100% |
| hypocalcemia | 2 | 50% | 50% |
| hypophosphatemia | 2 | 0% | 0% |
| acute_pancreatitis | 2 | 50% | 50% |
| hypothyroidism | 1 | 100% | 100% |
