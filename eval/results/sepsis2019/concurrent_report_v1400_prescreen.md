# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)

Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: 1500 seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. Analysed: cases 387, controls 786. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.559** (0.534–0.586) | 0.666 (0.633–0.698); values only, no missing-indicators: 0.610 | 25.3% (21.2–29.9; 98/387) | 14.1% (11.9–16.7; 111/786) | 23.8 % / 87.2 % |
| concurrent, labs + vital signs (optional context module) | **0.590** (0.561–0.619) | 0.687 (0.656–0.720); values only, no missing-indicators: 0.665 | 42.6% (37.8–47.6; 165/387) | 26.1% (23.1–29.3; 205/786) | 42.1 % / 74.8 % |

Not assessable from laboratory values alone (neither lactate nor WBC in the window): cases 76/387, controls 160/786. In arm B the SIRS/qSOFA syndrome layer can still assess these windows from vital signs.

Top-1 (arm B) among cases: sepsis 80, anemia 69, systemic_inflammatory_response_syndrome 52, acute_kidney_injury 49, hypercapnia_pattern 16, hepatocellular_injury_pattern 15, respiratory_acidosis 10, reduced_gfr_chronicity_undetermined 9

Top-1 (arm B) among controls: anemia 270, sepsis 127, acute_kidney_injury 78, systemic_inflammatory_response_syndrome 40, hypocalcemia 24, reduced_gfr_chronicity_undetermined 23, hepatocellular_injury_pattern 20, leukocytosis_pattern 16

Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy.
