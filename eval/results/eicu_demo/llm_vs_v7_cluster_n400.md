# Blind GPT-4-class LLM vs Hemoglyph **engine v7 / registry 14.1.0 (frozen)** — n=400 eICU-demo stays, stay-clustered inference

Same 400 stays, same stored blind LLM read-outs and SYN map as the v5.1 comparison; only the engine arm is re-scored from `per_stay_v7.json.gz`.
Inference treats the stay as the cluster: cluster bootstrap (4,000 resamples of stays) and Durkalski cluster-adjusted McNemar.

## flat (specific-diagnosis tier; primary) — 291 stays with scorable labels, 596 labels

| metric | Hemoglyph v7 | LLM | difference (engine − LLM) | cluster-bootstrap p | naive McNemar p | Durkalski McNemar p |
|---|---|---|---|---|---|---|
| recall@1 | 24.0% (20.6–27.7) | 28.2% (24.6–32.0) | -4.2 pp (-7.5 to -0.9) | 0.011 | 0.0199 (b=41, c=66) | 0.0129 (z=-2.49) |
| recall@3 | 47.0% (42.6–51.5) | 50.8% (46.5–55.1) | -3.9 pp (-7.4 to -0.3) | 0.038 | 0.0329 (b=42, c=65) | 0.0413 (z=-2.04) |
| recall@5 (primary) | 60.7% (56.5–65.0) | 59.6% (55.3–63.6) | +1.2 pp (-2.5 to +5.1) | 0.575 | 0.5760 (b=61, c=54) | 0.5439 (z=0.61) |
| recall@10 | 72.0% (67.9–75.8) | 65.1% (60.8–69.3) | +6.9 pp (+3.3 to +10.5) | 0.000 | 0.0001 (b=75, c=34) | 0.0002 (z=3.67) |
| MRR | 0.391 | 0.408 | -0.017 (-0.043 to +0.008) | | | |
| label absent from list | 21.8% | 34.9% | | | | |

Clustering: 291 stays, 2.05 labels per stay; ICC of the paired recall@5 difference = 0.041; design effect = 1.04.

| group | n | Hemoglyph v7 r@5 | LLM r@5 |
|---|---:|---|---|
| renal_impairment | 75 | 83% | 75% |
| sepsis | 71 | 39% | 42% |
| diabetes | 62 | 50% | 37% |
| acute_kidney_injury | 49 | 80% | 76% |
| gi_bleeding | 38 | 84% | 50% |
| anemia | 36 | 83% | 83% |
| chronic_kidney_disease | 35 | 23% | 20% |
| diabetic_ketoacidosis | 30 | 73% | 83% |
| acute_myocardial_infarction | 27 | 78% | 81% |
| hyperglycemia | 22 | 45% | 64% |
| hypokalemia | 17 | 59% | 41% |
| heart_failure | 17 | 88% | 94% |
| metabolic_acidosis | 14 | 50% | 79% |
| thrombocytopenia | 12 | 67% | 75% |
| leukocytosis | 11 | 36% | 55% |
| alcohol_withdrawal | 11 | 36% | 45% |
| hyponatremia | 10 | 60% | 70% |
| hyperkalemia | 10 | 70% | 90% |

## two-tier (either tier) — 291 stays with scorable labels, 596 labels

| metric | Hemoglyph v7 | LLM | difference (engine − LLM) | cluster-bootstrap p | naive McNemar p | Durkalski McNemar p |
|---|---|---|---|---|---|---|
| recall@1 | 35.2% (31.2–39.6) | 28.2% (24.6–32.0) | +7.0 pp (+3.4 to +10.9) | 0.001 | 0.0002 (b=83, c=41) | 0.0003 (z=3.58) |
| recall@3 | 62.6% (58.3–66.7) | 50.8% (46.5–55.1) | +11.7 pp (+7.6 to +15.8) | 0.000 | 0.0000 (b=105, c=35) | 0.0000 (z=5.00) |
| recall@5 (primary) | 69.8% (65.7–73.7) | 59.6% (55.3–63.6) | +10.2 pp (+6.7 to +13.9) | 0.000 | 0.0000 (b=89, c=28) | 0.0000 (z=5.17) |
| recall@10 | 77.5% (73.7–81.2) | 65.1% (60.8–69.3) | +12.4 pp (+8.8 to +16.0) | 0.000 | 0.0000 (b=100, c=26) | 0.0000 (z=5.92) |
| MRR | 0.498 | 0.408 | +0.090 (+0.059 to +0.120) | | | |
| label absent from list | 21.8% | 34.9% | | | | |

Clustering: 291 stays, 2.05 labels per stay; ICC of the paired recall@5 difference = 0.038; design effect = 1.04.

| group | n | Hemoglyph v7 r@5 | LLM r@5 |
|---|---:|---|---|
| renal_impairment | 75 | 87% | 75% |
| sepsis | 71 | 39% | 42% |
| diabetes | 62 | 68% | 37% |
| acute_kidney_injury | 49 | 86% | 76% |
| gi_bleeding | 38 | 95% | 50% |
| anemia | 36 | 92% | 83% |
| chronic_kidney_disease | 35 | 37% | 20% |
| diabetic_ketoacidosis | 30 | 73% | 83% |
| acute_myocardial_infarction | 27 | 96% | 81% |
| hyperglycemia | 22 | 73% | 64% |
| hypokalemia | 17 | 65% | 41% |
| heart_failure | 17 | 100% | 94% |
| metabolic_acidosis | 14 | 57% | 79% |
| thrombocytopenia | 12 | 92% | 75% |
| leukocytosis | 11 | 55% | 55% |
| alcohol_withdrawal | 11 | 55% | 45% |
| hyponatremia | 10 | 70% | 70% |
| hyperkalemia | 10 | 80% | 90% |

