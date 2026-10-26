# Hemoglyph — NHANES 2017–2018 held-out evaluation (cycle J)

Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): 5103; evaluated random subsample n=3000 (seed 20261021).
Median inputs per participant 45 (IQR 45–47); latency median 1156 ms, p95 1301 ms.

| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 605/2391 | **0.945** (0.933–0.955) | 68.8% (65.0–72.3) | 99.4% (99.0–99.7) |
| diabetes_selfreport | told by doctor only (independent of labs) | 460/2456 | **0.918** (0.901–0.933) | 70.0% (65.7–74.0) | 96.5% (95.7–97.1) |
| ckd | eGFR <60 or ACR ≥30 (KDIGO) | 556/2396 | **0.958** (0.947–0.968) | 79.1% (75.6–82.3) | 99.2% (98.7–99.5) |
| ckd_selfreport | told of weak/failing kidneys (independent of labs) | 131/2712 | **0.816** (0.772–0.856) | 65.6% (57.2–73.2) | 86.3% (84.9–87.5) |
| anemia | WHO Hb cut-offs | 306/2694 | **0.973** (0.968–0.978) | 99.7% (98.2–99.9) | 94.2% (93.2–95.0) |
| iron_deficiency | ferritin <15 ng/mL (WHO) | 163/2827 | **0.990** (0.987–0.992) | 95.1% (90.6–97.5) | 97.1% (96.4–97.7) |
| hypercholesterolemia | TC ≥240 mg/dL | 306/2691 | **0.902** (0.892–0.910) | 100.0% (98.8–100.0) | 77.5% (75.9–79.0) |
| hyperuricemia | urate >7.0 M / >6.0 F | 589/2410 | **0.943** (0.929–0.955) | 88.3% (85.4–90.6) | 100.0% (99.8–100.0) |
| alt_elevation | ALT >33 M / >25 F (ACG) | 535/2465 | **0.721** (0.697–0.744) | 29.0% (25.3–33.0) | 97.6% (96.9–98.1) |

## T8 false-assertion rate in guideline-healthy adults

160 participants had every core analyte inside its reference interval; 1 (0.6% (0.1–3.5)) received at least one non-finding entity with p ≥ 0.5.

Most frequent top-1 outputs among healthy participants: None (39), anemia_of_chronic_disease (24), hypertriglyceridemia (18), mcardle_disease (14), viral_infection (11), hemochromatosis (8), thalassemia_trait (8), metabolic_acidosis (6)
