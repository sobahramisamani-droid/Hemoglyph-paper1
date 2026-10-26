# Hemoglyph — NHANES 2017–2018 held-out evaluation

Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): 5103; evaluated random subsample n=3000 (seed 20261021).
Median inputs per participant 45 (IQR 45–47); latency median 1005 ms, p95 1223 ms.

| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 605/2391 | **0.944** (0.932–0.955) | 68.6% (64.8–72.2) | 99.4% (99.0–99.7) |
| diabetes_selfreport | told by doctor only (independent of labs) | 460/2456 | **0.918** (0.901–0.933) | 69.8% (65.4–73.8) | 96.5% (95.7–97.1) |
| ckd | eGFR <60 or ACR ≥30 (KDIGO) | 556/2396 | **0.937** (0.923–0.949) | 68.0% (64.0–71.7) | 99.9% (99.6–100.0) |
| ckd_selfreport | told of weak/failing kidneys (independent of labs) | 131/2712 | **0.767** (0.721–0.809) | 56.5% (47.9–64.7) | 88.8% (87.6–90.0) |
| anemia | WHO Hb cut-offs | 306/2694 | **0.972** (0.966–0.977) | 99.3% (97.6–99.8) | 93.9% (93.0–94.8) |
| iron_deficiency | ferritin <15 ng/mL (WHO) | 163/2827 | **0.990** (0.986–0.992) | 95.1% (90.6–97.5) | 96.7% (95.9–97.3) |
| hypercholesterolemia | TC ≥240 mg/dL | 306/2691 | **0.905** (0.896–0.913) | 100.0% (98.8–100.0) | 77.5% (75.9–79.0) |
| hyperuricemia | urate >7.0 M / >6.0 F | 589/2410 | **0.862** (0.844–0.880) | 0.3% (0.1–1.2) | 100.0% (99.8–100.0) |
| alt_elevation | ALT >33 M / >25 F (ACG) | 535/2465 | **0.724** (0.701–0.747) | 24.1% (20.7–27.9) | 97.6% (97.0–98.2) |

## T8 false-assertion rate in guideline-healthy adults

160 participants had every core analyte inside its reference interval; 2 (1.2% (0.3–4.4)) received at least one non-finding entity with p ≥ 0.5.

Most frequent top-1 outputs among healthy participants: thalassemia_trait (91), hypertriglyceridemia (15), viral_infection (10), hemochromatosis (7), None (6), co_decreased_gamma_glutamyl_transferase_with_decreased_lactate_dehydrogenase (5), sepsis (5), cholestasis (4)
