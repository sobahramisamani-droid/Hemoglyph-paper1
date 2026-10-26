# Subgroup and fairness analysis — eICU-CRD demo (n = 2314 stays), engine v4

Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.

Overall: recall@5 63.7%, recall@10 76.7%, chart support 24.5% (n = 4003), false-assertion proxy in stays with empty problem list 91.8% (n = 1136).

## By sex

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| male | 1392 | 1498 | 65.4% (62.6–68.2) | 78.9% | 25.7% | 0.81 | 0.70 | 0.79 | 0.83 |
| female | 922 | 934 | 61.0% (57.0–65.2) | 73.1% | 22.7% | 0.78 | 0.67 | 0.77 | 0.75 |

## By age band

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 65–79 | 820 | 844 | 64.2% (60.5–68.3) | 78.6% | 23.4% | 0.76 | 0.68 | 0.77 | 0.79 |
| 45–64 | 695 | 708 | 60.0% (55.5–64.5) | 72.9% | 23.5% | 0.84 | 0.70 | 0.77 | 0.82 |
| ≥80 | 426 | 476 | 66.4% (61.5–71.0) | 78.8% | 24.3% | 0.77 | 0.68 | 0.77 | 0.77 |
| <45 | 373 | 404 | 66.1% (61.3–71.2) | 77.0% | 29.3% | 0.82 | 0.68 | 0.81 | 0.79 |

## By ethnicity

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Caucasian | 1839 | 1827 | 63.4% (60.8–66.1) | 75.7% | 24.0% | 0.78 | 0.66 | 0.78 | 0.80 |
| African American | 220 | 201 | 63.7% (54.1–72.9) | 78.1% | 20.3% | 0.81 | 0.73 | 0.85 | 0.70 |
| Hispanic | 111 | 216 | 65.3% (58.2–72.3) | 82.9% | 34.5% | 0.90 | 0.83 | 0.75 | 0.85 |
| Other/Unknown | 74 | 96 | 60.4% (46.7–72.3) | 75.0% | 26.1% | 0.81 | 0.79 | — | 0.85 |
| Unknown | 30 | 31 | 74.2% (54.8–89.8) | 80.6% | 30.0% | — | 0.84 | — | — |
| Asian | 28 | 34 | 64.7% (45.8–84.6) | 76.5% | 22.2% | 0.86 | 0.69 | — | 0.87 |
| Native American | 12 | 27 | 70.4% (nan–nan) | 85.2% | 50.0% | — | — | — | — |

## By unit type

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Med-Surg ICU | 1735 | 1968 | 62.1% (59.6–64.7) | 75.8% | 24.9% | 0.79 | 0.67 | 0.80 | 0.79 |
| MICU | 130 | 109 | 81.7% (73.8–89.1) | 87.2% | 26.4% | 0.83 | 0.66 | 0.87 | 0.81 |
| Cardiac ICU | 123 | 128 | 76.6% (68.1–84.5) | 85.9% | 30.1% | 0.90 | 0.81 | 0.74 | 0.87 |
| SICU | 77 | 74 | 66.2% (53.1–81.5) | 75.7% | 17.1% | 0.74 | 0.73 | 0.64 | — |
| CCU-CTICU | 77 | 65 | 50.8% (37.9–64.4) | 67.7% | 16.7% | 0.53 | — | — | 0.70 |
| Neuro ICU | 62 | 24 | 58.3% (32.0–90.0) | 70.8% | 15.9% | — | — | — | — |
| CSICU | 62 | 16 | 87.5% (62.5–100.0) | 93.8% | 13.8% | — | — | — | — |
| CTICU | 48 | 48 | 64.6% (43.8–83.3) | 75.0% | 22.4% | 0.95 | — | 0.65 | — |

## By panel size

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| >20 | 2059 | 2269 | 63.5% (61.3–65.9) | 76.8% | 24.5% | 0.80 | 0.68 | 0.77 | 0.80 |
| 11–20 | 191 | 129 | 65.1% (55.2–74.2) | 74.4% | 26.6% | 0.72 | 0.66 | 0.86 | 0.61 |
| ≤10 analytes | 64 | 34 | 76.5% (61.9–88.2) | 79.4% | 19.5% | 0.78 | — | — | — |

## By hospital

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| hosp 146 | 35 | 21 | 85.7% (70.4–100.0) | 90.5% | 20.5% | — | — | — | — |
| hosp 157 | 23 | 18 | 66.7% (44.4–91.7) | 88.9% | 13.1% | 0.72 | — | — | — |
| hosp 171 | 22 | 25 | 72.0% (52.4–89.5) | 80.0% | 24.5% | 0.82 | — | — | 0.91 |
| hosp 167 | 21 | 1 | 100.0% (0.0–100.0) | 100.0% | 7.7% | — | — | — | — |
| hosp 243 | 21 | 27 | 81.5% (63.6–95.7) | 88.9% | 56.2% | 0.92 | — | — | — |
| hosp 154 | 20 | 13 | 23.1% (0.0–47.4) | 53.8% | 0.0% | — | 0.57 | — | — |
| hosp 165 | 19 | 1 | 100.0% (nan–nan) | 100.0% | 14.3% | — | — | — | — |
| hosp 283 | 19 | 11 | 63.6% (nan–nan) | 63.6% | 12.8% | — | 0.60 | — | — |

## Strata deviating by more than 10 percentage points from overall recall@5 (n ≥ 40)

- unit type = MICU: recall@5 81.7% vs overall 63.7%
- unit type = Cardiac ICU: recall@5 76.6% vs overall 63.7%
- unit type = CCU-CTICU: recall@5 50.8% vs overall 63.7%
- unit type = CSICU: recall@5 87.5% vs overall 63.7%
- panel size = ≤10 analytes: recall@5 76.5% vs overall 63.7%
