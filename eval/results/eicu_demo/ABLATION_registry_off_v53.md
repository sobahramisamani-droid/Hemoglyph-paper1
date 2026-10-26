# Registry-off ablation — eICU-CRD demo, engine v5.3, 2026-10-24

Arm: labs only, identical pipeline; `HEMOGLYPH_REGISTRY_OVERRIDE=eval/ablation/REGISTRY_OFF.json.br` = registry 13.3.0 with **all 34,548 rules marked non-executable** (entities, synonyms and features retained so that the loader validates). Everything else (Bayesian, fuzzy, knowledge-graph, risk-model layers, expert syndrome layer, fusion, safety) unchanged. Same 2,314 stays / 2,432 labels.

| metric | registry ON (v5.3) | registry OFF | Δ (ON−OFF) |
|---|---:|---:|---:|
| recall@3, all labels | 49.3 % | 47.6 % | +1.7 |
| recall@5, all labels | 63.8 % | 62.0 % | +1.8 |
| recall@10, all labels | 77.2 % | 75.4 % | +1.8 |
| recall@3, lab-detectable | 53.9 % | 50.5 % | +3.5 |
| recall@5, lab-detectable | 68.3 % | 64.7 % | +3.6 |
| recall@10, lab-detectable | 81.0 % | 77.4 % | +3.6 |
| chart support of p≥0.7 outputs | 23.4 % (1079/4616) | 22.9 % (981/4288) | |
| mean AUROC, 24 lab-detectable groups | 0.767 | 0.732 | +0.035 |

## Per group (coded n ≥ 9)

| group | n | recall@5 ON | OFF | Δ | AUROC ON | OFF | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| leukocytosis | 57 | 57.9 | 8.8 | +49.1 | 0.732 | 0.534 | +0.197 |
| hypophosphatemia | 9 | 22.2 | 11.1 | +11.1 | 0.734 | 0.542 | +0.193 |
| hypernatremia | 14 | 64.3 | 57.1 | +7.1 | 0.882 | 0.781 | +0.101 |
| hypocalcemia | 10 | 20.0 | 20.0 | +0.0 | 0.630 | 0.536 | +0.094 |
| hyperglycemia | 96 | 49.0 | 50.0 | -1.0 | 0.699 | 0.627 | +0.072 |
| hypomagnesemia | 37 | 37.8 | 27.0 | +10.8 | 0.678 | 0.612 | +0.066 |
| diabetes | 246 | 49.2 | 50.0 | -0.8 | 0.692 | 0.635 | +0.057 |
| malnutrition | 16 | 0.0 | 6.2 | -6.2 | 0.509 | 0.556 | -0.047 |
| hyponatremia | 52 | 65.4 | 63.5 | +1.9 | 0.890 | 0.851 | +0.038 |
| renal_impairment | 326 | 79.8 | 78.5 | +1.2 | 0.800 | 0.777 | +0.023 |
| acute_kidney_injury | 218 | 74.8 | 72.5 | +2.3 | 0.798 | 0.776 | +0.022 |
| diabetic_ketoacidosis | 107 | 63.6 | 63.6 | +0.0 | 0.857 | 0.878 | -0.021 |
| heart_failure | 58 | 86.2 | 86.2 | +0.0 | 0.657 | 0.638 | +0.018 |
| thrombocytopenia | 40 | 70.0 | 50.0 | +20.0 | 0.890 | 0.876 | +0.013 |
| chronic_kidney_disease | 148 | 64.9 | 58.8 | +6.1 | 0.815 | 0.807 | +0.008 |
| metabolic_acidosis | 51 | 56.9 | 56.9 | +0.0 | 0.755 | 0.748 | +0.008 |
| sepsis | 289 | 48.4 | 52.2 | -3.8 | 0.684 | 0.679 | +0.006 |
| acute_pancreatitis | 18 | 66.7 | 66.7 | +0.0 | 0.736 | 0.733 | +0.004 |
| coagulopathy | 28 | 53.6 | 53.6 | +0.0 | 0.754 | 0.750 | +0.003 |
| lactic_acidosis | 19 | 63.2 | 68.4 | -5.3 | 0.736 | 0.740 | -0.003 |
| cirrhosis_liver_failure | 25 | 60.0 | 64.0 | -4.0 | 0.864 | 0.862 | +0.003 |
| anemia | 147 | 84.4 | 87.8 | -3.4 | 0.780 | 0.782 | -0.002 |
| rhabdomyolysis | 11 | 63.6 | 63.6 | +0.0 | 0.918 | 0.916 | +0.002 |
| hyperkalemia | 49 | 49.0 | 44.9 | +4.1 | 0.916 | 0.915 | +0.001 |
| hypokalemia | 67 | 44.8 | 37.3 | +7.5 | 0.717 | 0.717 | +0.001 |
| gi_bleeding | 145 | 81.4 | 82.8 | -1.4 | 0.751 | 0.751 | +0.000 |
| acute_myocardial_infarction | 84 | 89.3 | 89.3 | +0.0 | 0.703 | 0.702 | +0.000 |
| hypoglycemia | 21 | 28.6 | 28.6 | +0.0 | 0.641 | 0.641 | -0.000 |
| alcohol_withdrawal | 33 | 33.3 | 36.4 | -3.0 | 0.652 | 0.652 | +0.000 |
| hypothyroidism | 10 | 50.0 | 50.0 | +0.0 | 0.683 | 0.683 | +0.000 |

## Reading

The disease–guideline registry contributes about +1.8 points of top-5 recall on all labels (+3.6 on lab-detectable labels) and +0.035 mean AUROC; the larger part of the engine's performance comes from the expert syndrome layer, the Bayesian/fuzzy/knowledge-graph layers and the fusion/safety logic. This is consistent with H2 (13.1.0 → 13.3.0 moved recall by +0.1) and is reported in the manuscript as a limitation of how much of the 33,230-rule base is load-bearing, not as evidence that the registry is unnecessary: the groups that depend on it most are listed above (largest ΔAUROC first). No tuning followed this ablation.
