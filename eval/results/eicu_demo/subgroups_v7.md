# Subgroup and fairness analysis — eICU-CRD demo (n = 2314 stays), engine v7

Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.

Overall: recall@5 60.8%, recall@10 74.1%, chart support 23.2% (n = 4218), false-assertion proxy in stays with empty problem list 93.8% (n = 1136).

## By sex

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| male | 1392 | 1498 | 62.3% (59.5–64.9) | 75.8% | 24.3% | 0.78 | 0.69 | 0.79 | 0.80 |
| female | 922 | 934 | 58.5% (54.4–62.3) | 71.2% | 21.4% | 0.77 | 0.67 | 0.77 | 0.73 |

## By age band

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 65–79 | 820 | 844 | 60.1% (55.9–64.2) | 75.5% | 21.8% | 0.73 | 0.68 | 0.77 | 0.76 |
| 45–64 | 695 | 708 | 58.1% (54.0–62.6) | 70.6% | 22.5% | 0.84 | 0.70 | 0.77 | 0.81 |
| ≥80 | 426 | 476 | 63.9% (58.7–68.5) | 75.8% | 22.5% | 0.71 | 0.68 | 0.76 | 0.71 |
| <45 | 373 | 404 | 63.6% (58.7–68.6) | 75.0% | 28.8% | 0.81 | 0.68 | 0.82 | 0.80 |

## By ethnicity

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Caucasian | 1839 | 1827 | 60.9% (58.1–63.4) | 73.2% | 22.8% | 0.77 | 0.66 | 0.77 | 0.77 |
| African American | 220 | 201 | 60.2% (50.8–68.4) | 75.6% | 18.6% | 0.74 | 0.73 | 0.81 | 0.68 |
| Hispanic | 111 | 216 | 59.3% (51.5–67.2) | 79.2% | 31.4% | 0.84 | 0.83 | 0.81 | 0.85 |
| Other/Unknown | 74 | 96 | 58.3% (45.1–69.9) | 71.9% | 24.5% | 0.80 | 0.79 | — | 0.84 |
| Unknown | 30 | 31 | 74.2% (54.8–89.8) | 80.6% | 29.5% | — | 0.85 | — | — |
| Asian | 28 | 34 | 64.7% (45.8–84.6) | 76.5% | 21.9% | 0.77 | 0.69 | — | 0.80 |
| Native American | 12 | 27 | 63.0% (nan–nan) | 77.8% | 53.3% | — | — | — | — |

## By unit type

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Med-Surg ICU | 1735 | 1968 | 59.9% (57.3–62.5) | 73.7% | 23.6% | 0.77 | 0.67 | 0.79 | 0.76 |
| MICU | 130 | 109 | 75.2% (67.0–82.5) | 83.5% | 22.9% | 0.78 | 0.66 | 0.85 | 0.79 |
| Cardiac ICU | 123 | 128 | 70.3% (60.8–79.9) | 82.0% | 28.5% | 0.87 | 0.79 | 0.79 | 0.83 |
| SICU | 77 | 74 | 58.1% (46.4–72.1) | 70.3% | 18.5% | 0.73 | 0.69 | 0.64 | — |
| CCU-CTICU | 77 | 65 | 53.8% (39.0–69.4) | 63.1% | 19.3% | 0.53 | — | — | 0.69 |
| Neuro ICU | 62 | 24 | 50.0% (24.3–80.0) | 66.7% | 11.6% | — | — | — | — |
| CSICU | 62 | 16 | 81.2% (55.6–100.0) | 87.5% | 11.8% | — | — | — | — |
| CTICU | 48 | 48 | 54.2% (35.7–72.1) | 66.7% | 22.1% | 0.95 | — | 0.73 | — |

## By panel size

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| >20 | 2059 | 2269 | 60.5% (58.3–62.9) | 74.0% | 23.1% | 0.78 | 0.68 | 0.77 | 0.78 |
| 11–20 | 191 | 129 | 62.8% (53.0–72.1) | 72.9% | 24.9% | 0.70 | 0.66 | 0.86 | 0.59 |
| ≤10 analytes | 64 | 34 | 73.5% (57.9–87.5) | 79.4% | 23.2% | 0.73 | — | — | — |

## By hospital

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| hosp 146 | 35 | 21 | 81.0% (60.7–100.0) | 90.5% | 20.0% | — | — | — | — |
| hosp 157 | 23 | 18 | 55.6% (33.3–75.0) | 83.3% | 8.5% | 0.62 | — | — | — |
| hosp 171 | 22 | 25 | 68.0% (48.1–87.9) | 80.0% | 22.4% | 0.78 | — | — | 0.83 |
| hosp 167 | 21 | 1 | 100.0% (0.0–100.0) | 100.0% | 0.0% | — | — | — | — |
| hosp 243 | 21 | 27 | 66.7% (50.0–82.8) | 81.5% | 51.5% | 0.95 | — | — | — |
| hosp 154 | 20 | 13 | 23.1% (0.0–40.0) | 38.5% | 5.0% | — | 0.57 | — | — |
| hosp 165 | 19 | 1 | 100.0% (nan–nan) | 100.0% | 13.3% | — | — | — | — |
| hosp 283 | 19 | 11 | 54.5% (nan–nan) | 63.6% | 13.2% | — | 0.60 | — | — |

## Strata deviating by more than 10 percentage points from overall recall@5 (n ≥ 40)

- unit type = MICU: recall@5 75.2% vs overall 60.8%
- unit type = Neuro ICU: recall@5 50.0% vs overall 60.8%
- unit type = CSICU: recall@5 81.2% vs overall 60.8%
- panel size = ≤10 analytes: recall@5 73.5% vs overall 60.8%
