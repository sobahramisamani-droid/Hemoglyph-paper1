# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)

Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: 1500 seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. Analysed: cases 247, controls 652. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.609** (0.576–0.642) | 0.751 (0.717–0.783); values only, no missing-indicators: 0.676 | 26.7% (21.6–32.6; 66/247) | 10.4% (8.3–13.0; 68/652) | 23.5 % / 93.1 % |
| concurrent, labs + vital signs (optional context module) | **0.638** (0.601–0.675) | 0.744 (0.710–0.777); values only, no missing-indicators: 0.680 | 33.2% (27.6–39.3; 82/247) | 16.1% (13.5–19.1; 105/652) | 24.3 % / 92.9 % |

Not assessable from laboratory values alone (neither lactate nor WBC in the window): cases 30/247, controls 93/652. In arm B the SIRS/qSOFA syndrome layer can still assess these windows from vital signs.

Top-1 (arm B) among cases: acute_kidney_injury 45, anemia 44, myocardial_injury_acuity_undetermined 23, sepsis 22, systemic_inflammatory_response_syndrome 18, hypocalcemia 13, reduced_gfr_chronicity_undetermined 11, acute_myocardial_infarction 8

Top-1 (arm B) among controls: anemia 182, acute_kidney_injury 93, systemic_inflammatory_response_syndrome 65, myocardial_injury_acuity_undetermined 57, acute_myocardial_infarction 26, sepsis 23, leukocytosis_pattern 21, hypocalcemia 20

Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy.
