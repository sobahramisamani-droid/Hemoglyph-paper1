engine ranks taken from eicu_per_stay_v5_1.json for 160/160 B3+B4 stays (rest: stored ranks of the run they were scored with).
LLM read-outs: B3/B4 2026-10-21/22, B8 2026-10-23; all by the same agent model class, blinded to labels and engine output.

# POOLED B3+B4+B8 — blind GPT-4-class LLM (agent) vs Hemoglyph v5.1, n=400 eICU-demo stays

stays 400; scorable labels 596

| | Recall@5 |
|---|---|
| Hemoglyph | 64.4% (60.5–68.2; 384/596) |
| GPT-4-class LLM (agent, blind) | 59.6% (55.6–63.4; 355/596) |

Discordant: engine-only 73, LLM-only 44; McNemar exact p = 0.0093; difference +4.9 pp

| group | n | Hemoglyph | LLM |
|---|---:|---|---|
| renal_impairment | 75 | 81% | 75% |
| sepsis | 71 | 38% | 42% |
| diabetes | 62 | 55% | 37% |
| acute_kidney_injury | 49 | 80% | 76% |
| gi_bleeding | 38 | 87% | 50% |
| anemia | 36 | 86% | 83% |
| chronic_kidney_disease | 35 | 51% | 20% |
| diabetic_ketoacidosis | 30 | 73% | 83% |
| acute_myocardial_infarction | 27 | 89% | 81% |
| hyperglycemia | 22 | 55% | 64% |
| heart_failure | 17 | 94% | 94% |
| hypokalemia | 17 | 53% | 41% |
| metabolic_acidosis | 14 | 57% | 79% |
| thrombocytopenia | 12 | 75% | 75% |
| leukocytosis | 11 | 45% | 55% |
| alcohol_withdrawal | 11 | 36% | 45% |
| hyponatremia | 10 | 60% | 70% |
| hyperkalemia | 10 | 70% | 90% |
| coagulopathy | 8 | 38% | 50% |
| lactic_acidosis | 7 | 57% | 57% |
| malnutrition | 6 | 0% | 0% |
| cirrhosis_liver_failure | 5 | 80% | 60% |
| hypernatremia | 4 | 50% | 75% |
| hypoglycemia | 4 | 0% | 0% |
| hypomagnesemia | 4 | 25% | 50% |
| rhabdomyolysis | 3 | 67% | 100% |
| hypothyroidism | 2 | 50% | 50% |
| hypocalcemia | 2 | 50% | 50% |
| hypophosphatemia | 2 | 0% | 0% |
| acute_pancreatitis | 2 | 50% | 50% |

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

# B3 (n=100) rescored with engine v5.1 ranks

stays 100; scorable labels 94

| | Recall@5 |
|---|---|
| Hemoglyph | 64.9% (54.8–73.8; 61/94) |
| GPT-4-class LLM (agent, blind) | 66.0% (55.9–74.7; 62/94) |

Discordant: engine-only 7, LLM-only 8; McNemar exact p = 1; difference -1.1 pp

| group | n | Hemoglyph | LLM |
|---|---:|---|---|
| renal_impairment | 14 | 79% | 79% |
| diabetes | 12 | 50% | 42% |
| acute_kidney_injury | 11 | 73% | 73% |
| sepsis | 9 | 67% | 44% |
| diabetic_ketoacidosis | 7 | 71% | 100% |
| acute_myocardial_infarction | 5 | 80% | 80% |
| anemia | 4 | 50% | 50% |
| hyperglycemia | 4 | 25% | 50% |
| chronic_kidney_disease | 4 | 50% | 50% |
| heart_failure | 3 | 67% | 100% |
| hypokalemia | 3 | 33% | 33% |
| metabolic_acidosis | 2 | 100% | 100% |
| hyponatremia | 2 | 50% | 100% |
| leukocytosis | 2 | 100% | 100% |
| hyperkalemia | 2 | 50% | 50% |
| thrombocytopenia | 2 | 100% | 100% |
| hypothyroidism | 1 | 0% | 0% |
| lactic_acidosis | 1 | 100% | 100% |
| rhabdomyolysis | 1 | 100% | 100% |
| coagulopathy | 1 | 0% | 0% |
| hypernatremia | 1 | 100% | 100% |
| cirrhosis_liver_failure | 1 | 100% | 100% |
| gi_bleeding | 1 | 0% | 0% |
| alcohol_withdrawal | 1 | 100% | 0% |

# B4 (n=60) rescored with engine v5.1 ranks

stays 60; scorable labels 46

| | Recall@5 |
|---|---|
| Hemoglyph | 65.2% (50.8–77.3; 30/46) |
| GPT-4-class LLM (agent, blind) | 58.7% (44.3–71.7; 27/46) |

Discordant: engine-only 5, LLM-only 2; McNemar exact p = 0.45; difference +6.5 pp

| group | n | Hemoglyph | LLM |
|---|---:|---|---|
| renal_impairment | 6 | 100% | 83% |
| diabetes | 6 | 0% | 0% |
| sepsis | 4 | 0% | 0% |
| chronic_kidney_disease | 4 | 75% | 75% |
| thrombocytopenia | 4 | 75% | 75% |
| acute_myocardial_infarction | 3 | 100% | 100% |
| anemia | 3 | 100% | 67% |
| gi_bleeding | 3 | 100% | 33% |
| acute_kidney_injury | 3 | 100% | 67% |
| heart_failure | 2 | 100% | 100% |
| coagulopathy | 2 | 50% | 100% |
| diabetic_ketoacidosis | 1 | 0% | 0% |
| hyponatremia | 1 | 100% | 100% |
| alcohol_withdrawal | 1 | 0% | 0% |
| leukocytosis | 1 | 100% | 100% |
| hyperkalemia | 1 | 0% | 100% |
| metabolic_acidosis | 1 | 100% | 100% |
