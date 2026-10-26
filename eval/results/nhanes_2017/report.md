# Hemoglyph — NHANES 2017–2018 held-out evaluation (cycle J)

Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): 5103; evaluated random subsample n=5103 (seed 20261021).
Median inputs per participant 45 (IQR 45–47); latency median 1193 ms, p95 1391 ms.

| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 1045/4054 | **0.941** (0.932–0.950) | 67.5% (64.6–70.2) | 99.6% (99.4–99.8) |
| diabetes_selfreport | told by doctor only (independent of labs) | 792/4148 | **0.910** (0.898–0.921) | 66.7% (63.3–69.9) | 96.3% (95.7–96.8) |
| ckd | eGFR <60 or ACR ≥30 (KDIGO) | 936/4076 | **0.959** (0.951–0.967) | 73.8% (70.9–76.5) | 99.9% (99.7–100.0) |
| ckd_selfreport | told of weak/failing kidneys (independent of labs) | 202/4655 | **0.798** (0.763–0.833) | 58.4% (51.5–65.0) | 87.6% (86.6–88.5) |
| anemia | WHO Hb cut-offs | 535/4568 | **0.971** (0.967–0.975) | 99.4% (98.4–99.8) | 93.8% (93.1–94.5) |
| iron_deficiency | ferritin <15 ng/mL (WHO) | 281/4801 | **0.989** (0.986–0.991) | 94.7% (91.4–96.7) | 96.9% (96.4–97.4) |
| hypercholesterolemia | TC ≥240 mg/dL | 509/4590 | **0.901** (0.894–0.908) | 99.8% (98.9–100.0) | 77.1% (75.9–78.3) |
| hyperuricemia | urate >7.0 M / >6.0 F | 1006/4095 | **0.943** (0.932–0.952) | 88.2% (86.0–90.0) | 100.0% (99.9–100.0) |
| alt_elevation | ALT >33 M / >25 F (ACG) | 890/4213 | **0.720** (0.702–0.738) | 29.2% (26.3–32.3) | 97.8% (97.3–98.2) |

## T8 false-assertion rate in guideline-healthy adults

274 participants had every core analyte inside its reference interval; 1 (0.4% (0.1–2.0)) received at least one non-finding entity with p ≥ 0.5.

Most frequent top-1 outputs among healthy participants: None (61), anemia_of_chronic_disease (42), hypertriglyceridemia (31), mcardle_disease (22), viral_infection (21), metabolic_acidosis (14), siadh (13), thalassemia_trait (13)
