# Reviewer items B5/B6 — calibration metrics and multiplicity / panel-size sensitivity (engine v7, eICU demo)

## B5 Calibration (raw engine probabilities; stay-cluster bootstrap CI, 500 reps)

| set | units | prev | calibration slope | calibration-in-the-large (intercept) | Brier (95% CI) | log-loss | AUROC |
|---|---:|---:|---:|---:|---|---:|---:|
| ALL pooled | 52689 | 0.046 | 0.25 | -2.50 | 0.117 (0.114–0.119) | 0.379 | 0.797 |
| renal_impairment | 2266 | 0.144 | 0.25 | -2.23 | 0.236 (0.224–0.247) | 0.727 | 0.777 |
| sepsis | 2215 | 0.130 | 0.13 | -1.28 | 0.171 (0.159–0.182) | 0.789 | 0.682 |
| diabetes | 2247 | 0.109 | 0.14 | -1.43 | 0.150 (0.142–0.158) | 0.572 | 0.692 |
| acute_kidney_injury | 2266 | 0.096 | 0.26 | -2.37 | 0.213 (0.204–0.223) | 0.621 | 0.774 |
| anemia | 2207 | 0.067 | 0.36 | -2.94 | 0.244 (0.235–0.254) | 0.662 | 0.782 |
| acute_myocardial_infarction | 668 | 0.126 | 0.23 | +nan | 0.492 (0.467–0.518) | 1.412 | 0.758 |
| hyperkalemia | 2244 | 0.022 | 0.49 | -1.68 | 0.029 (0.025–0.033) | 0.096 | 0.917 |

Interpretation: slope < 1 and strongly negative intercept = raw scores are over-confident ranks, not probabilities (as stated in the manuscript); the cross-fitted isotonic map (calibration_dca_v7.md) removes this for display purposes only.

## B6a Multiplicity control over per-group AUROC (H0: AUROC = 0.5; Mann–Whitney U, two-sided; Holm and BH-FDR at 0.05; label-level, exploratory)

| group | n coded | AUROC | raw p | Holm-adjusted | BH q | significant after BH |
|---|---:|---:|---:|---:|---:|---|
| renal_impairment | 326 | 0.777 | 4.39e-62 | 1.18e-60 | 4.24e-61 | yes |
| sepsis | 289 | 0.682 | 2.09e-31 | 3.98e-30 | 5.52e-31 | yes |
| diabetes | 246 | 0.692 | 5.28e-24 | 8.44e-23 | 1.09e-23 | yes |
| acute_kidney_injury | 218 | 0.774 | 3.14e-44 | 7.53e-43 | 1.52e-43 | yes |
| chronic_kidney_disease | 148 | 0.783 | 3.77e-39 | 8.30e-38 | 1.37e-38 | yes |
| anemia | 147 | 0.782 | 1.28e-31 | 2.57e-30 | 3.72e-31 | yes |
| gi_bleeding | 145 | 0.751 | 3.82e-25 | 6.88e-24 | 9.23e-25 | yes |
| diabetic_ketoacidosis | 107 | 0.855 | 1.19e-89 | 3.33e-88 | 1.72e-88 | yes |
| hyperglycemia | 96 | 0.699 | 1.28e-11 | 1.41e-10 | 1.96e-11 | yes |
| acute_myocardial_infarction | 84 | 0.758 | 1.32e-14 | 1.99e-13 | 2.56e-14 | yes |
| hypokalemia | 67 | 0.716 | 3.06e-24 | 5.21e-23 | 6.83e-24 | yes |
| heart_failure | 58 | 0.664 | 1.35e-04 | 5.42e-04 | 1.51e-04 | yes |
| leukocytosis | 57 | 0.729 | 7.85e-12 | 9.42e-11 | 1.26e-11 | yes |
| hyponatremia | 52 | 0.887 | 7.25e-41 | 1.67e-39 | 3.00e-40 | yes |
| metabolic_acidosis | 51 | 0.757 | 1.77e-13 | 2.30e-12 | 3.02e-13 | yes |
| hyperkalemia | 49 | 0.917 | 6.31e-90 | 1.83e-88 | 1.72e-88 | yes |
| thrombocytopenia | 40 | 0.889 | 1.03e-31 | 2.16e-30 | 3.32e-31 | yes |
| hypomagnesemia | 37 | 0.673 | 1.42e-06 | 9.95e-06 | 1.79e-06 | yes |
| alcohol_withdrawal | 33 | 0.652 | 5.67e-07 | 4.53e-06 | 7.47e-07 | yes |
| coagulopathy | 28 | 0.751 | 1.86e-11 | 1.86e-10 | 2.70e-11 | yes |
| cirrhosis_liver_failure | 25 | 0.865 | 4.79e-14 | 6.71e-13 | 8.69e-14 | yes |
| hypoglycemia | 21 | 0.641 | 1.28e-52 | 3.32e-51 | 9.25e-52 | yes |
| lactic_acidosis | 19 | 0.735 | 1.97e-06 | 1.18e-05 | 2.38e-06 | yes |
| acute_pancreatitis | 18 | 0.733 | 8.08e-06 | 4.04e-05 | 9.38e-06 | yes |
| malnutrition | 16 | 0.515 | 8.33e-01 | 8.33e-01 | 8.33e-01 | no |
| hypernatremia | 14 | 0.883 | 6.04e-49 | 1.51e-47 | 3.50e-48 | yes |
| rhabdomyolysis | 11 | 0.919 | 9.60e-09 | 8.64e-08 | 1.33e-08 | yes |
| hypocalcemia | 10 | 0.627 | 1.19e-01 | 2.37e-01 | 1.23e-01 | no |
| hypothyroidism | 10 | 0.684 | 1.37e-03 | 4.11e-03 | 1.47e-03 | yes |

27 of 29 groups remain significant after BH-FDR; all per-group comparisons other than the pre-specified primary (flat recall@5) are labelled exploratory in the manuscript.

## B6b Sensitivity of recall to the minimum number of analytes in the first panel

| minimum analytes (n_in) | stays | labels | flat @3 | flat @5 | flat @10 | two-tier @5 |
|---:|---:|---:|---:|---:|---:|---:|
| ≥ 8 | 2314 | 2432 | 47.9 | 60.8 | 74.1 | 71.9 |
| ≥ 10 | 2269 | 2401 | 47.6 | 60.7 | 74.0 | 71.8 |
| ≥ 12 | 2236 | 2389 | 47.4 | 60.6 | 73.9 | 71.7 |
| ≥ 16 | 2186 | 2349 | 47.3 | 60.5 | 73.9 | 71.8 |
| ≥ 20 | 2099 | 2294 | 47.1 | 60.5 | 74.0 | 71.9 |
| ≥ 25 | 1829 | 2090 | 46.2 | 59.8 | 73.6 | 71.4 |

Distribution of n_in: median 31, IQR 25–35, min 8, max 49. Stays with < 8 analytes (n = 198 of 2,512 adults) were excluded by the SAP; they cannot be re-included without re-running the cohort builder, and their labels are listed in Table S3.

