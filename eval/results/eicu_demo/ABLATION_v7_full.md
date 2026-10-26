# Component ablation — engine v7 / registry 14.1.0, eICU-CRD demo (2,314 stays, labs only)

Each arm switches off or alters exactly one component (environment variable or in-process patch; engine file unchanged). Same stays, same label map, same scorer. Flat = specific-diagnosis tier; PS = panel-supported subset (secondary, post hoc; n = 1,460).

| arm | n labels | flat @3 | flat @5 | flat @10 | Δ@5 vs full | two-tier @5 | PS @5 | PS @10 | stays with top-5 identical to full |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **full v7 (reference)** | 2432 | 47.9 | 60.8 | 74.1 | — | 71.9 | 78.0 | 91.8 | — |
| no_bayesian | 2432 | 47.5 | 59.5 | 69.9 | -1.3 | 68.2 | 77.3 | 89.7 | 36% |
| no_fuzzy | 2432 | 47.9 | 61.1 | 73.8 | +0.3 | 71.8 | 78.4 | 91.7 | 77% |
| no_graph | 2432 | 48.3 | 60.9 | 74.3 | +0.1 | 72.2 | 78.5 | 92.1 | 83% |
| no_risk | 2432 | 47.9 | 60.8 | 74.1 | +0.0 | 71.9 | 78.0 | 91.8 | 100% |
| no_rule | 2432 | 34.7 | 48.7 | 67.0 | -12.1 | 57.6 | 61.1 | 82.6 | 3% |
| no_esl | 2432 | 39.5 | 51.3 | 68.3 | -9.5 | 66.0 | 69.5 | 86.7 | 37% |
| dempster | 2432 | 47.6 | 60.7 | 74.0 | -0.1 | 71.9 | 77.9 | 91.8 | 99% |
| uniform_w | 2432 | 47.5 | 59.4 | 73.1 | -1.4 | 72.2 | 75.7 | 89.9 | 61% |
| no_shrink | 2432 | 47.7 | 60.4 | 73.5 | -0.4 | 71.7 | 77.3 | 90.8 | 71% |
| anchor_only | 2432 | 46.8 | 59.9 | 72.5 | -0.9 | 68.9 | 73.3 | 86.6 | 19% |
| no_unverified | 2432 | 47.9 | 60.8 | 74.1 | +0.0 | 71.9 | 78.0 | 91.8 | 100% |
| w_rule_heavy | 2432 | 48.2 | 60.8 | 74.0 | -0.0 | 71.8 | 77.9 | 91.8 | 65% |
| anchor_only_no_esl | 2432 | 38.0 | 48.2 | 68.1 | -12.6 | 60.9 | 57.1 | 82.3 | 4% |
| w_rule_light | 2432 | 47.6 | 59.7 | 73.3 | -1.1 | 72.2 | 76.0 | 90.1 | 61% |

## Arms

- `no_bayesian`: Bayesian network layer disabled (HEMOGLYPH_DISABLE_LAYERS=bayesian)
- `no_fuzzy`: adaptive fuzzy layer disabled
- `no_graph`: knowledge-graph layer disabled
- `no_risk`: risk-model layer disabled
- `no_rule`: rule-engine vote disabled in fusion (registry rules AND expert-syndrome votes both enter through this channel)
- `no_esl`: expert syndrome layer returns no hits (registry rules intact)
- `dempster`: Theory-of-Evidence layer uses Dempster normalisation instead of Yager (conflict renormalised, not sent to ignorance)
- `uniform_w`: fusion weights uniform 0.20 x 5, all domain profiles collapsed to uniform
- `no_shrink`: discord shrinkage and single-source discount removed (MAX_DISCORD_SHRINK=0, SINGLE_SOURCE_DISCOUNT=1)
- `anchor_only`: registry restricted to the 272 manually curated guideline-anchored rules (32,911 AI-assisted rules non-executable)
- `no_unverified`: 28 rules with evidence_tier=unverified_source made non-executable
- `w_rule_heavy`: fusion weight sensitivity: rule_engine 0.55 / bayesian 0.15 / fuzzy 0.15 / graph 0.075 / risk 0.075 (all profiles)
- `anchor_only_no_esl`: 2x2 cell: registry restricted to 272 anchors AND expert syndrome layer off
- `w_rule_light`: fusion weight sensitivity: rule_engine 0.20 / bayesian 0.30 / fuzzy 0.25 / graph 0.125 / risk 0.125 (all profiles)

## Per-group flat recall@5 (groups with n ≥ 20)

| group | n | full | no_bayesian | no_fuzzy | no_graph | no_risk | no_rule | no_esl | dempster | uniform_w | no_shrink | anchor_only | no_unverified | w_rule_heavy | anchor_only_no_esl | w_rule_light |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| renal_impairment | 326 | 81 | 81 | 82 | 82 | 81 | 65 | 82 | 82 | 82 | 81 | 82 | 81 | 80 | 83 | 82 |
| sepsis | 289 | 49 | 51 | 49 | 48 | 49 | 5 | 17 | 49 | 50 | 49 | 52 | 49 | 49 | 31 | 50 |
| diabetes | 246 | 45 | 36 | 46 | 47 | 45 | 66 | 50 | 45 | 35 | 48 | 45 | 45 | 46 | 52 | 35 |
| acute_kidney_injury | 218 | 78 | 77 | 78 | 78 | 78 | 65 | 53 | 77 | 78 | 74 | 73 | 78 | 77 | 17 | 78 |
| chronic_kidney_disease | 148 | 36 | 31 | 36 | 37 | 36 | 31 | 9 | 34 | 34 | 30 | 35 | 36 | 35 | 13 | 37 |
| anemia | 147 | 83 | 80 | 83 | 82 | 83 | 92 | 86 | 83 | 83 | 83 | 87 | 83 | 82 | 95 | 83 |
| gi_bleeding | 145 | 78 | 77 | 79 | 78 | 78 | 89 | 86 | 78 | 77 | 78 | 81 | 78 | 78 | 91 | 77 |
| diabetic_ketoacidosis | 107 | 64 | 64 | 64 | 64 | 64 | 76 | 2 | 64 | 64 | 64 | 64 | 64 | 64 | 9 | 64 |
| hyperglycemia | 96 | 47 | 36 | 47 | 47 | 47 | 65 | 49 | 47 | 31 | 48 | 47 | 47 | 50 | 48 | 35 |
| acute_myocardial_infarction | 84 | 88 | 89 | 87 | 88 | 88 | 0 | 92 | 88 | 89 | 88 | 90 | 88 | 88 | 92 | 89 |
| hypokalemia | 67 | 49 | 49 | 49 | 49 | 49 | 45 | 45 | 49 | 45 | 49 | 37 | 49 | 45 | 22 | 45 |
| heart_failure | 58 | 83 | 86 | 83 | 81 | 83 | 47 | 83 | 83 | 83 | 81 | 86 | 83 | 84 | 88 | 81 |
| leukocytosis | 57 | 40 | 44 | 40 | 40 | 40 | 0 | 58 | 40 | 44 | 37 | 5 | 40 | 42 | 0 | 44 |
| hyponatremia | 52 | 63 | 63 | 63 | 63 | 63 | 75 | 83 | 63 | 62 | 63 | 62 | 63 | 62 | 56 | 62 |
| metabolic_acidosis | 51 | 55 | 57 | 55 | 55 | 55 | 71 | 51 | 55 | 55 | 57 | 57 | 55 | 55 | 51 | 57 |
| hyperkalemia | 49 | 49 | 53 | 51 | 49 | 49 | 12 | 14 | 49 | 53 | 49 | 45 | 49 | 49 | 4 | 53 |
| thrombocytopenia | 40 | 65 | 68 | 65 | 65 | 65 | 32 | 72 | 65 | 70 | 62 | 50 | 65 | 65 | 35 | 70 |
| hypomagnesemia | 37 | 35 | 32 | 35 | 35 | 35 | 0 | 38 | 35 | 35 | 35 | 22 | 35 | 35 | 24 | 35 |
| alcohol_withdrawal | 33 | 33 | 33 | 33 | 33 | 33 | 0 | 12 | 33 | 33 | 39 | 33 | 33 | 33 | 33 | 33 |
| coagulopathy | 28 | 46 | 46 | 46 | 46 | 46 | 11 | 4 | 46 | 46 | 43 | 46 | 46 | 46 | 4 | 46 |
| cirrhosis_liver_failure | 25 | 60 | 60 | 56 | 60 | 60 | 76 | 68 | 60 | 60 | 60 | 64 | 60 | 56 | 72 | 60 |
| hypoglycemia | 21 | 24 | 24 | 24 | 24 | 24 | 0 | 29 | 24 | 24 | 24 | 29 | 24 | 24 | 29 | 24 |
