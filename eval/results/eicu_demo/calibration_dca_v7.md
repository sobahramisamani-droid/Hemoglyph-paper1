# Calibration (cross-fitted isotonic) and decision-curve analysis — eICU demo, engine v7

stays 2314; (stay, group) units 52689; positives 2432

| set | n | prev | ECE raw | ECE isotonic (cross-fit) | Brier raw | Brier iso | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL groups pooled | 52689 | 0.046 | 0.162 | 0.003 | 0.117 | 0.040 | 0.797 |
| renal_impairment | 2266 | 0.144 | 0.289 | 0.031 | 0.236 | 0.105 | 0.777 |
| sepsis | 2215 | 0.130 | 0.183 | 0.025 | 0.171 | 0.105 | 0.682 |
| diabetes | 2247 | 0.109 | 0.201 | 0.024 | 0.150 | 0.093 | 0.692 |
| acute_kidney_injury | 2266 | 0.096 | 0.282 | 0.012 | 0.213 | 0.078 | 0.774 |
| anemia | 2207 | 0.067 | 0.349 | 0.016 | 0.244 | 0.056 | 0.782 |

Reliability (pooled): equal-mass deciles — mean predicted vs observed

| decile | raw p | obs | iso p | obs |
|---:|---:|---:|---:|---:|
| 1 | 0.00 | 0.01 | 0.01 | 0.02 |
| 2 | 0.00 | 0.01 | 0.01 | 0.01 |
| 3 | 0.00 | 0.01 | 0.01 | 0.01 |
| 4 | 0.00 | 0.02 | 0.01 | 0.01 |
| 5 | 0.00 | 0.02 | 0.01 | 0.01 |
| 6 | 0.00 | 0.01 | 0.01 | 0.01 |
| 7 | 0.10 | 0.03 | 0.02 | 0.03 |
| 8 | 0.43 | 0.05 | 0.05 | 0.05 |
| 9 | 0.60 | 0.08 | 0.08 | 0.08 |
| 10 | 0.80 | 0.22 | 0.23 | 0.22 |

## Decision curves (net benefit per 100 units; cross-fitted isotonic probabilities vs raw vs treat-all)

### renal_impairment (n=2266, prevalence 0.14)

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 10.6 | 10.4 | 9.9 | 0.0 |
| 0.10 | 7.9 | 9.1 | 4.9 | 0.0 |
| 0.15 | 4.9 | 7.5 | -0.7 | 0.0 |
| 0.20 | 1.5 | 5.5 | -7.0 | 0.0 |
| 0.25 | -2.2 | 3.4 | -14.2 | 0.0 |
| 0.30 | -6.6 | 0.4 | -22.3 | 0.0 |
| 0.40 | -17.4 | 0.2 | -42.7 | 0.0 |
| 0.50 | -14.3 | 0.3 | -71.2 | 0.0 |
| 0.60 | -25.8 | 0.2 | -114.0 | 0.0 |
| 0.70 | -43.8 | -0.1 | -185.4 | 0.0 |
| 0.80 | -41.4 | 0.0 | -328.1 | 0.0 |

isotonic model beats both default strategies at thresholds: 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.55, 0.60

### sepsis (n=2215, prevalence 0.13)

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 6.5 | 8.5 | 8.5 | 0.0 |
| 0.10 | 4.9 | 4.9 | 3.4 | 0.0 |
| 0.15 | 3.3 | 4.0 | -2.3 | 0.0 |
| 0.20 | 1.4 | 2.9 | -8.7 | 0.0 |
| 0.25 | -0.7 | 1.6 | -15.9 | 0.0 |
| 0.30 | -2.9 | 1.2 | -24.2 | 0.0 |
| 0.40 | -8.7 | -0.1 | -44.9 | 0.0 |
| 0.50 | -8.7 | -0.2 | -73.9 | 0.0 |
| 0.60 | -15.8 | -0.5 | -117.4 | 0.0 |
| 0.70 | -28.2 | 0.0 | -189.8 | 0.0 |
| 0.80 | -17.7 | 0.0 | -334.8 | 0.0 |

isotonic model beats both default strategies at thresholds: 0.10, 0.15, 0.20, 0.25, 0.30, 0.35

### diabetes (n=2247, prevalence 0.11)

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 6.0 | 6.0 | 6.3 | 0.0 |
| 0.10 | 2.9 | 3.6 | 1.1 | 0.0 |
| 0.15 | -0.6 | 2.7 | -4.8 | 0.0 |
| 0.20 | -4.5 | 1.6 | -11.3 | 0.0 |
| 0.25 | -8.4 | 0.6 | -18.7 | 0.0 |
| 0.30 | -10.7 | -0.2 | -27.2 | 0.0 |
| 0.40 | -12.2 | 0.0 | -48.4 | 0.0 |
| 0.50 | -5.7 | 0.0 | -78.1 | 0.0 |
| 0.60 | -8.5 | -0.1 | -122.6 | 0.0 |
| 0.70 | -3.7 | -0.1 | -196.8 | 0.0 |
| 0.80 | -0.1 | -0.2 | -345.3 | 0.0 |

isotonic model beats both default strategies at thresholds: 0.10, 0.15, 0.20, 0.25, 0.40, 0.45

### acute_kidney_injury (n=2266, prevalence 0.10)

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 6.2 | 6.5 | 4.9 | 0.0 |
| 0.10 | 3.4 | 5.0 | -0.4 | 0.0 |
| 0.15 | 0.2 | 3.4 | -6.3 | 0.0 |
| 0.20 | -3.3 | 1.6 | -13.0 | 0.0 |
| 0.25 | -7.2 | 0.3 | -20.5 | 0.0 |
| 0.30 | -11.7 | -0.3 | -29.1 | 0.0 |
| 0.40 | -22.7 | 0.0 | -50.6 | 0.0 |
| 0.50 | -18.1 | 0.0 | -80.8 | 0.0 |
| 0.60 | -27.4 | -0.1 | -125.9 | 0.0 |
| 0.70 | -38.0 | 0.0 | -201.3 | 0.0 |
| 0.80 | -13.7 | 0.0 | -351.9 | 0.0 |

isotonic model beats both default strategies at thresholds: 0.05, 0.10, 0.15, 0.20, 0.25, 0.40, 0.45

### anemia (n=2207, prevalence 0.07)

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 3.2 | 3.3 | 1.7 | 0.0 |
| 0.10 | -0.2 | 1.8 | -3.7 | 0.0 |
| 0.15 | -4.1 | 1.5 | -9.8 | 0.0 |
| 0.20 | -8.3 | 0.6 | -16.7 | 0.0 |
| 0.25 | -13.1 | 0.5 | -24.5 | 0.0 |
| 0.30 | -18.6 | 0.4 | -33.3 | 0.0 |
| 0.40 | -30.5 | 0.1 | -55.6 | 0.0 |
| 0.50 | -46.9 | -0.4 | -86.7 | 0.0 |
| 0.60 | -45.2 | 0.0 | -133.3 | 0.0 |
| 0.70 | -22.5 | 0.0 | -211.1 | 0.0 |
| 0.80 | -10.9 | 0.0 | -366.7 | 0.0 |

isotonic model beats both default strategies at thresholds: 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40

Interpretation: raw engine probabilities are over-confident on the multi-label task (ECE raw) — the figure shown in the paper is the
cross-fitted isotonic mapping, which is what a deployment would apply; the decision curves show the threshold ranges where
acting on the engine's calibrated probability has higher net benefit than treating everyone or no one.  No label information
leaks into any reported probability (odd/even stay cross-fitting).
