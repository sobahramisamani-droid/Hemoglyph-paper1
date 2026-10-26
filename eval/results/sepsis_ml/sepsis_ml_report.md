# Sepsis risk module — interpretable supervised companion (trained once on set A; evaluated on untouched B and B2)

## Logistic model — 20 largest standardised coefficients (signed; fully inspectable)

| feature | coefficient |
|---|---:|
| Resp | +0.485 |
| ICULOS | +0.454 |
| Creatinine | +0.389 |
| BaseExcess_miss | -0.346 |
| MAP_miss | -0.334 |
| SBP_miss | +0.310 |
| shock_index | -0.278 |
| HR | +0.260 |
| Temp_max12 | +0.230 |
| FiO2_miss | -0.210 |
| sirs_temp | +0.198 |
| Creatinine_max12 | -0.182 |
| SBP | -0.177 |
| BaseExcess | +0.177 |
| Glucose_miss | +0.176 |
| Resp_max12 | -0.175 |
| pH_miss | +0.146 |
| WBC_miss | +0.140 |
| Resp_d6 | -0.137 |
| Platelets_min12 | +0.130 |

## Held-out performance

| set | model | hourly AUROC | hourly AUPRC | patient AUROC (n sepsis / n no) | AUROC at −6 h / −12 h / −24 h | utility (thr from A) |
|---|---|---|---|---|---|---|
| A (development) | logistic | 0.773 | 0.091 | 0.658 (446 / 4518) | 0.754 / 0.800 / 0.818 | 0.364 |
| A (development) | gradient boosting | 0.934 | 0.319 | 0.832 (446 / 4518) | 0.950 / 0.909 / 0.865 | 0.689 |
| B (held out) | logistic | 0.717 | 0.051 | 0.552 (280 / 4699) | 0.698 / 0.780 / 0.776 | 0.199 |
| B (held out) | gradient boosting | 0.757 | 0.066 | 0.654 (280 / 4699) | 0.775 / 0.799 / 0.774 | 0.253 |
| B2 (held out) | logistic | 0.726 | 0.052 | 0.557 (280 / 4711) | 0.709 / 0.778 / 0.783 | 0.216 |
| B2 (held out) | gradient boosting | 0.750 | 0.068 | 0.631 (280 / 4711) | 0.774 / 0.765 / 0.786 | 0.220 |

Hourly AUROC = every ICU hour as a unit (challenge framing). Patient AUROC = maximum score over hours before the shifted label for septic patients vs maximum over all hours for non-septic patients (closest to the engine's per-patient 'prediction frame'). Horizon AUROC = score exactly h hours before t_sepsis vs a random hour of each non-septic patient. Utility = official PhysioNet/CinC 2019 normalised utility (Reyna 2020), alert threshold fixed on set A. Inputs are the 5,000-patient public subsets used throughout the paper; the rule engine's own sepsis score on the same sets was 0.600 / 0.610 / 0.588 (patient-level, labs only).

This module is a predictive risk score, not a diagnosis; it is trained on outcome labels and therefore sits outside the untrained guideline engine. It is reported with its contributing features so that every alert can be inspected.

Runtime 38 s.
