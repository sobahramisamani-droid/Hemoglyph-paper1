# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)

Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: 1500 seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. Analysed: cases 247, controls 652. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.610** (0.577–0.643) | 0.751 (0.717–0.783); values only, no missing-indicators: 0.676 | 27.1% (22.0–33.0; 67/247) | 10.6% (8.4–13.2; 69/652) | 23.9 % / 93.1 % |
| concurrent, labs + vital signs (optional context module) | **0.639** (0.601–0.676) | 0.744 (0.710–0.777); values only, no missing-indicators: 0.680 | 37.2% (31.5–43.4; 92/247) | 19.0% (16.2–22.2; 124/652) | 24.7 % / 92.9 % |

Not assessable from laboratory values alone (neither lactate nor WBC in the window): cases 30/247, controls 93/652. In arm B the SIRS/qSOFA syndrome layer can still assess these windows from vital signs.

Top-1 (arm B) among cases: anemia 62, chronic_kidney_disease 30, sepsis 26, hypocalcemia 19, acute_kidney_injury 15, type_2_diabetes 11, acute_myocardial_infarction 10, hypokalemia 9

Top-1 (arm B) among controls: anemia 269, chronic_kidney_disease 53, acute_kidney_injury 40, leukocytosis_pattern 31, acute_myocardial_infarction 29, type_2_diabetes 27, sepsis 26, hypocalcemia 25

Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy.
