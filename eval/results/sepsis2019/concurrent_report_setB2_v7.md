# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)

Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: 1500 seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. Analysed: cases 247, controls 600. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.595** (0.563–0.627) | 0.721 (0.685–0.757); values only, no missing-indicators: 0.695 | 24.7% (19.7–30.4; 61/247) | 8.7% (6.7–11.2; 52/600) | 22.7 % / 92.3 % |
| concurrent, labs + vital signs (optional context module) | **0.635** (0.597–0.673) | 0.726 (0.689–0.764); values only, no missing-indicators: 0.710 | 28.3% (23.1–34.3; 70/247) | 14.2% (11.6–17.2; 85/600) | 23.5 % / 92.2 % |

Not assessable from laboratory values alone (neither lactate nor WBC in the window): cases 32/247, controls 75/600. In arm B the SIRS/qSOFA syndrome layer can still assess these windows from vital signs.

Top-1 (arm B) among cases: anemia 42, systemic_inflammatory_response_syndrome 40, myocardial_injury_acuity_undetermined 26, acute_kidney_injury 26, sepsis 25, reduced_gfr_chronicity_undetermined 13, quick_sofa_positive 9, acute_myocardial_infarction 8

Top-1 (arm B) among controls: anemia 188, systemic_inflammatory_response_syndrome 64, acute_kidney_injury 60, myocardial_injury_acuity_undetermined 58, reduced_gfr_chronicity_undetermined 46, acute_myocardial_infarction 33, sepsis 26, leukocytosis_pattern 15

Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy.
