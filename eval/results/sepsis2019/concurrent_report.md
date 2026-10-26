# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)

Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: 1500 seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. Analysed: cases 388, controls 772. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.534** (0.508–0.561) | 0.667 (0.635–0.700) | 21.6% (17.8–26.0; 84/388) | 14.8% (12.4–17.4; 114/772) | 19.8 % / 86.8 % |
| concurrent, labs + vital signs (optional context module) | **0.534** (0.508–0.561) | 0.703 (0.671–0.735) | 21.6% (17.8–26.0; 84/388) | 14.8% (12.4–17.4; 114/772) | 19.8 % / 86.8 % |

Top-1 (arm B) among cases: anemia 119, acute_kidney_injury 46, sepsis 28, chronic_kidney_disease 20, leukocytosis_pattern 17, hepatocellular_injury_pattern 13, hypocalcemia 12, respiratory_acidosis 11

Top-1 (arm B) among controls: anemia 349, acute_kidney_injury 66, sepsis 52, leukocytosis_pattern 38, chronic_kidney_disease 31, hypocalcemia 31, hypokalemia 21, hepatocellular_injury_pattern 19

Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy.

## Descriptive strata (added after the table; not pre-stated)
| stratum (arm A) | cases / controls | engine AUROC | sepsis group in top-5: cases / controls |
|---|---|---|---|
| lactate measured in window | 144 / 166 | 0.472 (0.411–0.529) | 54/144 / 67/166 |
| lactate not measured | 244 / 606 | 0.522 (0.496–0.548) | 30/244 / 47/606 |
| lactate + WBC measured | 101 / 138 | 0.498 (0.417–0.569) | 43/101 / 60/138 |

Mechanism. Registry 13.3.0's sepsis entity is anchored on procalcitonin/CRP (+ lactate, WBC); the challenge file contains **no procalcitonin and no CRP**, lactate is present in 37 % of case windows (22 % of controls) and the sepsis group therefore never enters the differential for 74 % of cases (probability 0). Where lactate *is* measured, ICU controls are themselves hypoperfused for other reasons and the lactate-driven score does not separate Sepsis-3 cases (AUROC 0.47). Vital signs (arm B) changed the differential (e.g. `septic_shock_severe_lactic_acidosis` appears) but not the sepsis-group probability in any of the 1,160 windows, because no 13.3.0 sepsis rule uses heart rate, respiratory rate or blood pressure. The supervised baseline's advantage (0.67–0.70) comes largely from measurement pattern (missing-indicator features: lactate is ordered more often when sepsis is suspected), which an interpreter that reasons only from values cannot and should not exploit.

Verdict under the pre-stated rule (Amendment 13, ii): concurrent AUROC 0.534 < 0.65 → the engine's laboratory-only sepsis group is genuinely weak on this data; this is stated in Limitations. No rule or weight was changed in response.
