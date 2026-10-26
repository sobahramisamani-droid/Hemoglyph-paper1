# Hemoglyph — NHANES 2013–2014 held-out evaluation (cycle H)

Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): 5556; evaluated random subsample n=3000 (seed 20261021).
Median inputs per participant 42 (IQR 42–44); latency median 1017 ms, p95 1268 ms.

| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 483/2515 | **0.938** (0.925–0.951) | 65.8% (61.5–69.9) | 99.0% (98.5–99.3) |
| diabetes_selfreport | told by doctor only (independent of labs) | 369/2539 | **0.914** (0.897–0.931) | 65.6% (60.6–70.2) | 96.8% (96.0–97.4) |
| ckd | eGFR <60 or ACR ≥30 (KDIGO) | 497/2461 | **0.968** (0.957–0.977) | 87.1% (83.9–89.8) | 98.9% (98.5–99.3) |
| ckd_selfreport | told of weak/failing kidneys (independent of labs) | 101/2733 | **0.748** (0.695–0.801) | 58.4% (48.7–67.5) | 85.5% (84.1–86.7) |
| anemia | WHO Hb cut-offs | 295/2705 | **0.994** (0.991–0.996) | 100.0% (98.7–100.0) | 99.0% (98.6–99.3) |
| hypercholesterolemia | TC ≥240 mg/dL | 312/2688 | **0.883** (0.873–0.893) | 99.0% (97.2–99.7) | 75.8% (74.1–77.4) |
| hyperuricemia | urate >7.0 M / >6.0 F | 547/2453 | **0.958** (0.946–0.968) | 91.2% (88.6–93.3) | 100.0% (99.8–100.0) |
| alt_elevation | ALT >33 M / >25 F (ACG) | 649/2351 | **0.880** (0.865–0.894) | 24.7% (21.5–28.1) | 99.1% (98.6–99.4) |

## T8 false-assertion rate in guideline-healthy adults

246 participants had every core analyte inside its reference interval; 1 (0.4% (0.1–2.3)) received at least one non-finding entity with p ≥ 0.5.

Most frequent top-1 outputs among healthy participants: None (99), siadh (33), hypertriglyceridemia (19), mcardle_disease (18), viral_infection (15), co_decreased_gamma_glutamyl_transferase_with_decreased_lactate_dehydrogenase (15), metabolic_syndrome (12), thalassemia_trait (5)
