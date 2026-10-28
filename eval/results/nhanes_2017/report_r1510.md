# Hemoglyph — NHANES 2017–2018 held-out evaluation (cycle J)

Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): 5103; evaluated random subsample n=1000 (seed 20261021).
Median inputs per participant 45 (IQR 45–47); latency median 1161 ms, p95 1339 ms.

| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 217/783 | **0.946** (0.927–0.964) | 65.9% (59.4–71.9) | 99.2% (98.3–99.6) |
| diabetes_selfreport | told by doctor only (independent of labs) | 154/827 | **0.915** (0.888–0.940) | 70.1% (62.5–76.8) | 95.8% (94.2–96.9) |
| ckd | eGFR <60 or ACR ≥30 (KDIGO) | 179/803 | **0.959** (0.940–0.977) | 79.9% (73.4–85.1) | 99.1% (98.2–99.6) |
| ckd_selfreport | told of weak/failing kidneys (independent of labs) | 50/893 | **0.769** (0.692–0.841) | 58.0% (44.2–70.6) | 86.8% (84.4–88.9) |
| anemia | WHO Hb cut-offs | 93/907 | **0.972** (0.962–0.980) | 98.9% (94.2–99.8) | 94.7% (93.1–96.0) |
| iron_deficiency | ferritin <15 ng/mL (WHO) | 54/944 | **0.991** (0.985–0.995) | 90.7% (80.1–96.0) | 97.6% (96.4–98.4) |
| hypercholesterolemia | TC ≥240 mg/dL | 96/903 | **0.898** (0.884–0.912) | 100.0% (96.2–100.0) | 76.1% (73.2–78.7) |
| hyperuricemia | urate >7.0 M / >6.0 F | 192/808 | **0.948** (0.925–0.968) | 89.1% (83.9–92.7) | 100.0% (99.5–100.0) |
| alt_elevation | ALT >33 M / >25 F (ACG) | 190/810 | **0.856** (0.826–0.884) | 26.3% (20.6–33.0) | 98.6% (97.6–99.2) |

## T8 false-assertion rate in guideline-healthy adults

51 participants had every core analyte inside its reference interval; 0 (0.0% (0.0–7.0)) received at least one non-finding entity with p ≥ 0.5.

Most frequent top-1 outputs among healthy participants: None (15), anemia_of_chronic_disease (8), hypertriglyceridemia (6), thalassemia_trait (5), hemochromatosis (3), cholestasis (3), viral_infection (3), metabolic_acidosis (2)
