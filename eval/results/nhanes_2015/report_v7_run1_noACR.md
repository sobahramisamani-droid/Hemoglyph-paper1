# Hemoglyph — NHANES 2015–2016 held-out evaluation (cycle I)

Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): 5298; evaluated random subsample n=3000 (seed 20261021).
Median inputs per participant 42 (IQR 41–43); latency median 1170 ms, p95 1357 ms.

| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 563/2436 | **0.925** (0.910–0.939) | 66.8% (62.8–70.6) | 99.1% (98.7–99.4) |
| diabetes_selfreport | told by doctor only (independent of labs) | 431/2503 | **0.899** (0.879–0.916) | 68.4% (63.9–72.7) | 96.3% (95.5–97.0) |
| ckd_selfreport | told of weak/failing kidneys (independent of labs) | 116/2759 | **0.771** (0.721–0.818) | 44.8% (36.1–53.9) | 95.8% (95.0–96.5) |
| anemia | WHO Hb cut-offs | 346/2654 | **0.983** (0.978–0.987) | 100.0% (98.9–100.0) | 95.9% (95.0–96.5) |
| iron_deficiency | ferritin <15 ng/mL (WHO) | 148/635 | **0.972** (0.961–0.982) | 89.9% (84.0–93.8) | 95.4% (93.5–96.8) |
| hypercholesterolemia | TC ≥240 mg/dL | 322/2677 | **0.886** (0.877–0.896) | 100.0% (98.8–100.0) | 73.0% (71.3–74.7) |
| hyperuricemia | urate >7.0 M / >6.0 F | 505/2494 | **0.955** (0.943–0.967) | 91.1% (88.3–93.3) | 100.0% (99.8–100.0) |
| alt_elevation | ALT >33 M / >25 F (ACG) | 656/2344 | **0.877** (0.862–0.891) | 23.6% (20.5–27.0) | 98.8% (98.2–99.1) |

## T8 false-assertion rate in guideline-healthy adults

0 participants had every core analyte inside its reference interval; 0 (nan% (nan–nan)) received at least one non-finding entity with p ≥ 0.5.

Most frequent top-1 outputs among healthy participants: 
