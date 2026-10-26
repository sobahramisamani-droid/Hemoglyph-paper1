# LLM baseline — eval/results/eicu_demo/llm_agent_b3_n100.json

stays 100; LLM entries 509, unmapped to any group 122 (24%)
Recall@5 (listed groups, key analyte measured): LLM 66.0% (55.9–74.7) vs Hemoglyph 48.9% (39.1–58.9) on the same stays

| group | n | LLM AUROC | Hemoglyph AUROC |
|---|---:|---|---|
| acute_kidney_injury | 11 | 0.76 | 0.76 |
| renal_impairment | 14 | 0.78 | 0.71 |
| diabetes | 12 | 0.65 | 0.72 |
| diabetic_ketoacidosis | 7 | 1.00 | 0.94 |
| sepsis | 9 | 0.66 | 0.65 |
| acute_myocardial_infarction | 5 | 0.83 | 0.64 |
