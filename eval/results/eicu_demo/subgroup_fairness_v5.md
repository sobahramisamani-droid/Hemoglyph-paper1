# Subgroup and fairness analysis — eICU-CRD demo (n = 2314 stays), engine v4

Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.

Overall: recall@5 63.3%, recall@10 76.4%, chart support 23.9% (n = 3632), false-assertion proxy in stays with empty problem list 91.8% (n = 1136).

## By sex

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| male | 1392 | 1498 | 65.0% (62.3–67.8) | 78.4% | 25.3% | 0.81 | 0.69 | 0.79 | 0.83 |
| female | 922 | 934 | 60.6% (56.8–64.5) | 73.1% | 21.8% | 0.77 | 0.67 | 0.78 | 0.75 |

## By age band

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 65–79 | 820 | 844 | 63.9% (60.2–67.8) | 78.1% | 22.8% | 0.75 | 0.67 | 0.78 | 0.78 |
| 45–64 | 695 | 708 | 58.9% (54.6–63.3) | 72.5% | 22.7% | 0.84 | 0.70 | 0.76 | 0.82 |
| ≥80 | 426 | 476 | 66.8% (61.9–71.5) | 78.6% | 24.1% | 0.76 | 0.69 | 0.77 | 0.78 |
| <45 | 373 | 404 | 65.8% (61.0–70.9) | 77.0% | 28.6% | 0.82 | 0.68 | 0.81 | 0.80 |

## By ethnicity

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Caucasian | 1839 | 1827 | 63.1% (60.5–65.6) | 75.4% | 23.2% | 0.78 | 0.65 | 0.78 | 0.80 |
| African American | 220 | 201 | 63.7% (53.8–73.0) | 78.1% | 21.1% | 0.82 | 0.74 | 0.85 | 0.71 |
| Hispanic | 111 | 216 | 63.4% (56.2–70.2) | 81.5% | 32.5% | 0.90 | 0.80 | 0.76 | 0.86 |
| Other/Unknown | 74 | 96 | 60.4% (46.7–72.3) | 75.0% | 26.8% | 0.82 | 0.79 | — | 0.86 |
| Unknown | 30 | 31 | 74.2% (54.8–89.8) | 80.6% | 29.7% | — | 0.86 | — | — |
| Asian | 28 | 34 | 64.7% (45.8–84.6) | 76.5% | 20.7% | 0.89 | 0.69 | — | 0.87 |
| Native American | 12 | 27 | 74.1% (nan–nan) | 85.2% | 50.0% | — | — | — | — |

## By unit type

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Med-Surg ICU | 1735 | 1968 | 61.8% (59.3–64.3) | 75.5% | 24.1% | 0.79 | 0.67 | 0.80 | 0.79 |
| MICU | 130 | 109 | 81.7% (73.8–89.1) | 87.2% | 27.8% | 0.83 | 0.67 | 0.88 | 0.81 |
| Cardiac ICU | 123 | 128 | 75.8% (67.7–83.7) | 85.9% | 29.5% | 0.90 | 0.81 | 0.74 | 0.87 |
| SICU | 77 | 74 | 64.9% (51.6–80.4) | 74.3% | 16.8% | 0.75 | 0.66 | 0.64 | — |
| CCU-CTICU | 77 | 65 | 50.8% (37.9–64.4) | 67.7% | 18.8% | 0.54 | — | — | 0.73 |
| Neuro ICU | 62 | 24 | 58.3% (32.0–90.0) | 70.8% | 15.4% | — | — | — | — |
| CSICU | 62 | 16 | 87.5% (62.5–100.0) | 93.8% | 13.0% | — | — | — | — |
| CTICU | 48 | 48 | 60.4% (42.2–77.3) | 75.0% | 19.2% | 0.95 | — | 0.65 | — |

## By panel size

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| >20 | 2059 | 2269 | 63.0% (60.9–65.4) | 76.4% | 23.7% | 0.80 | 0.67 | 0.77 | 0.80 |
| 11–20 | 191 | 129 | 65.1% (55.2–74.2) | 74.4% | 27.5% | 0.71 | 0.66 | 0.86 | 0.61 |
| ≤10 analytes | 64 | 34 | 76.5% (61.9–88.2) | 79.4% | 24.1% | 0.86 | — | — | — |

## By hospital

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| hosp 146 | 35 | 21 | 85.7% (70.4–100.0) | 90.5% | 22.0% | — | — | — | — |
| hosp 157 | 23 | 18 | 66.7% (44.4–91.7) | 88.9% | 13.3% | 0.72 | — | — | — |
| hosp 171 | 22 | 25 | 72.0% (52.4–89.5) | 80.0% | 23.3% | 0.85 | — | — | 0.91 |
| hosp 167 | 21 | 1 | 100.0% (0.0–100.0) | 100.0% | 9.1% | — | — | — | — |
| hosp 243 | 21 | 27 | 81.5% (63.6–95.7) | 88.9% | 58.1% | 0.92 | — | — | — |
| hosp 154 | 20 | 13 | 23.1% (0.0–47.4) | 53.8% | 0.0% | — | 0.57 | — | — |
| hosp 165 | 19 | 1 | 100.0% (nan–nan) | 100.0% | 14.3% | — | — | — | — |
| hosp 283 | 19 | 11 | 54.5% (nan–nan) | 54.5% | 10.8% | — | 0.49 | — | — |

## Strata deviating by more than 10 percentage points from overall recall@5 (n ≥ 40)

- unit type = MICU: recall@5 81.7% vs overall 63.3%
- unit type = Cardiac ICU: recall@5 75.8% vs overall 63.3%
- unit type = CCU-CTICU: recall@5 50.8% vs overall 63.3%
- unit type = CSICU: recall@5 87.5% vs overall 63.3%
- panel size = ≤10 analytes: recall@5 76.5% vs overall 63.3%
