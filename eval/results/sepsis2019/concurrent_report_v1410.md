# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)

Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: 1500 seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. Analysed: cases 387, controls 786. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.559** (0.534–0.586) | 0.666 (0.633–0.698); values only, no missing-indicators: 0.610 | 23.3% (19.3–27.7; 90/387) | 13.0% (10.8–15.5; 102/786) | 19.4 % / 89.2 % |
| concurrent, labs + vital signs (optional context module) | **0.592** (0.563–0.621) | 0.687 (0.656–0.720); values only, no missing-indicators: 0.665 | 29.5% (25.1–34.2; 114/387) | 18.1% (15.5–20.9; 142/786) | 20.7 % / 88.7 % |

Not assessable from laboratory values alone (neither lactate nor WBC in the window): cases 76/387, controls 160/786. In arm B the SIRS/qSOFA syndrome layer can still assess these windows from vital signs.

Top-1 (arm B) among cases: systemic_inflammatory_response_syndrome 89, anemia 65, acute_kidney_injury 54, sepsis 37, hypercapnia_pattern 16, hepatocellular_injury_pattern 15, reduced_gfr_chronicity_undetermined 11, respiratory_acidosis 10

Top-1 (arm B) among controls: anemia 262, systemic_inflammatory_response_syndrome 105, acute_kidney_injury 89, sepsis 54, reduced_gfr_chronicity_undetermined 21, hepatocellular_injury_pattern 20, hypocalcemia 20, leukocytosis_pattern 18

Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy.
