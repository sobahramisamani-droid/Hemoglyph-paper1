# Subgroup and fairness analysis — eICU-CRD demo (n = 2314 stays), engine v4

Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.

Overall: recall@5 61.1%, recall@10 75.7%, chart support 23.3% (n = 3680), false-assertion proxy in stays with empty problem list 91.8% (n = 1136).

## By sex

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| male | 1392 | 1498 | 62.5% (59.7–65.4) | 77.5% | 24.7% | 0.81 | 0.69 | 0.79 | 0.83 |
| female | 922 | 934 | 58.8% (54.9–62.5) | 72.7% | 21.3% | 0.77 | 0.67 | 0.78 | 0.75 |

## By age band

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 65–79 | 820 | 844 | 61.6% (57.9–65.5) | 77.5% | 22.5% | 0.75 | 0.67 | 0.78 | 0.78 |
| 45–64 | 695 | 708 | 57.2% (52.8–61.3) | 71.8% | 22.5% | 0.84 | 0.70 | 0.76 | 0.82 |
| ≥80 | 426 | 476 | 64.3% (59.2–69.3) | 78.4% | 23.3% | 0.76 | 0.69 | 0.77 | 0.78 |
| <45 | 373 | 404 | 62.9% (57.5–68.7) | 75.5% | 26.9% | 0.82 | 0.68 | 0.81 | 0.80 |

## By ethnicity

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Caucasian | 1839 | 1827 | 60.8% (58.1–63.3) | 74.7% | 22.6% | 0.78 | 0.65 | 0.78 | 0.80 |
| African American | 220 | 201 | 61.7% (51.9–71.1) | 78.1% | 20.6% | 0.82 | 0.74 | 0.85 | 0.71 |
| Hispanic | 111 | 216 | 61.1% (52.7–68.9) | 80.6% | 32.5% | 0.90 | 0.80 | 0.76 | 0.86 |
| Other/Unknown | 74 | 96 | 59.4% (45.9–71.1) | 74.0% | 26.8% | 0.82 | 0.79 | — | 0.86 |
| Unknown | 30 | 31 | 67.7% (48.1–85.7) | 80.6% | 29.7% | — | 0.86 | — | — |
| Asian | 28 | 34 | 61.8% (43.6–80.0) | 76.5% | 20.3% | 0.89 | 0.69 | — | 0.87 |
| Native American | 12 | 27 | 74.1% (nan–nan) | 85.2% | 45.8% | — | — | — | — |

## By unit type

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Med-Surg ICU | 1735 | 1968 | 60.1% (57.5–62.7) | 74.8% | 23.5% | 0.79 | 0.67 | 0.80 | 0.79 |
| MICU | 130 | 109 | 79.8% (71.9–87.4) | 87.2% | 27.6% | 0.83 | 0.67 | 0.88 | 0.81 |
| Cardiac ICU | 123 | 128 | 68.8% (60.2–77.6) | 83.6% | 29.2% | 0.90 | 0.81 | 0.74 | 0.87 |
| SICU | 77 | 74 | 60.8% (47.8–75.4) | 73.0% | 15.8% | 0.75 | 0.66 | 0.64 | — |
| CCU-CTICU | 77 | 65 | 47.7% (35.1–60.0) | 67.7% | 17.3% | 0.54 | — | — | 0.73 |
| Neuro ICU | 62 | 24 | 54.2% (28.0–85.7) | 70.8% | 15.4% | — | — | — | — |
| CSICU | 62 | 16 | 81.2% (53.8–100.0) | 93.8% | 14.5% | — | — | — | — |
| CTICU | 48 | 48 | 54.2% (36.2–71.4) | 75.0% | 18.7% | 0.95 | — | 0.65 | — |

## By panel size

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| >20 | 2059 | 2269 | 60.6% (58.5–63.2) | 75.8% | 23.1% | 0.80 | 0.67 | 0.77 | 0.80 |
| 11–20 | 191 | 129 | 64.3% (54.2–74.1) | 72.9% | 27.5% | 0.71 | 0.66 | 0.86 | 0.61 |
| ≤10 analytes | 64 | 34 | 76.5% (61.9–88.2) | 79.4% | 24.1% | 0.86 | — | — | — |

## By hospital

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| hosp 146 | 35 | 21 | 85.7% (70.4–100.0) | 90.5% | 22.0% | — | — | — | — |
| hosp 157 | 23 | 18 | 66.7% (44.4–91.7) | 88.9% | 13.3% | 0.72 | — | — | — |
| hosp 171 | 22 | 25 | 56.0% (27.8–82.4) | 80.0% | 21.7% | 0.85 | — | — | 0.91 |
| hosp 167 | 21 | 1 | 100.0% (0.0–100.0) | 100.0% | 9.1% | — | — | — | — |
| hosp 243 | 21 | 27 | 81.5% (63.6–95.7) | 88.9% | 58.1% | 0.92 | — | — | — |
| hosp 154 | 20 | 13 | 23.1% (0.0–47.4) | 46.2% | 0.0% | — | 0.57 | — | — |
| hosp 165 | 19 | 1 | 100.0% (nan–nan) | 100.0% | 14.3% | — | — | — | — |
| hosp 283 | 19 | 11 | 45.5% (nan–nan) | 54.5% | 10.8% | — | 0.49 | — | — |

## Strata deviating by more than 10 percentage points from overall recall@5 (n ≥ 40)

- unit type = MICU: recall@5 79.8% vs overall 61.1%
- unit type = CCU-CTICU: recall@5 47.7% vs overall 61.1%
- unit type = CSICU: recall@5 81.2% vs overall 61.1%
- panel size = ≤10 analytes: recall@5 76.5% vs overall 61.1%
