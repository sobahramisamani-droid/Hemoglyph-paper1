# Ablation — stay-cluster bootstrap (4,000 resamples) for paired differences vs full v7

| arm | Δ flat recall@5 (pp) | 95% CI | Δ two-tier recall@5 (pp) | 95% CI | n labels / stays |
|---|---:|---|---:|---|---:|
| no_bayesian | -1.3 | -2.0 to -0.6 | -3.7 | -4.8 to -2.7 | 2432 / 1092 |
| no_fuzzy | +0.3 | -0.1 to +0.8 | -0.1 | -0.4 to +0.2 | 2432 / 1092 |
| no_graph | +0.1 | -0.3 to +0.6 | +0.3 | -0.1 to +0.8 | 2432 / 1092 |
| no_risk | +0.0 | +0.0 to +0.0 | +0.0 | +0.0 to +0.0 | 2432 / 1092 |
| no_esl | -9.5 | -11.1 to -7.9 | -6.0 | -7.3 to -4.6 | 2432 / 1092 |
| dempster | -0.1 | -0.3 to +0.1 | -0.0 | -0.2 to +0.1 | 2432 / 1092 |
| uniform_w | -1.4 | -2.1 to -0.7 | +0.3 | -0.2 to +0.8 | 2432 / 1092 |
| no_shrink | -0.4 | -1.0 to +0.2 | -0.2 | -0.7 to +0.3 | 2432 / 1092 |
| anchor_only | -0.9 | -2.1 to +0.2 | -3.0 | -4.0 to -2.1 | 2432 / 1092 |
| no_rule | -12.1 | -14.4 to -9.8 | -14.3 | -16.3 to -12.4 | 2432 / 1092 |
| no_unverified | +0.0 | +0.0 to +0.0 | +0.0 | +0.0 to +0.0 | 2432 / 1092 |
| w_rule_heavy | -0.0 | -0.6 to +0.5 | -0.2 | -0.7 to +0.4 | 2432 / 1092 |
| w_rule_light | -1.1 | -1.8 to -0.3 | +0.3 | -0.2 to +0.8 | 2432 / 1092 |
| anchor_only_no_esl | -12.6 | -14.5 to -10.6 | -11.1 | -12.7 to -9.4 | 2432 / 1092 |
