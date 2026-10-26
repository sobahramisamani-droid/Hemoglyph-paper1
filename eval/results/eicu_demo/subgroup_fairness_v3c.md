# Subgroup and fairness analysis — eICU-CRD demo (n = 2314 stays), engine v3 (ext6c)

Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.

Overall: recall@5 59.0%, recall@10 74.2%, chart support 21.5% (n = 3524), false-assertion proxy in stays with empty problem list 91.5% (n = 1136).

## By sex

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| male | 1392 | 1498 | 60.4% (57.5–63.3) | 76.2% | 22.5% | 0.80 | 0.69 | 0.79 | 0.82 |
| female | 922 | 934 | 56.6% (52.6–60.6) | 71.0% | 19.9% | 0.77 | 0.67 | 0.77 | 0.76 |

## By age band

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 65–79 | 820 | 844 | 60.0% (56.1–63.7) | 76.7% | 20.7% | 0.75 | 0.67 | 0.78 | 0.78 |
| 45–64 | 695 | 708 | 55.5% (51.2–59.7) | 70.5% | 21.0% | 0.84 | 0.70 | 0.76 | 0.82 |
| ≥80 | 426 | 476 | 61.8% (56.4–67.0) | 75.2% | 20.9% | 0.74 | 0.69 | 0.77 | 0.77 |
| <45 | 373 | 404 | 59.7% (54.2–65.4) | 74.3% | 25.2% | 0.83 | 0.68 | 0.81 | 0.80 |

## By ethnicity

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Caucasian | 1839 | 1827 | 59.0% (56.3–61.7) | 73.4% | 20.9% | 0.78 | 0.65 | 0.78 | 0.79 |
| African American | 220 | 201 | 58.7% (49.4–67.6) | 76.1% | 18.2% | 0.80 | 0.74 | 0.85 | 0.72 |
| Hispanic | 111 | 216 | 57.4% (49.8–65.1) | 77.8% | 29.6% | 0.89 | 0.80 | 0.76 | 0.86 |
| Other/Unknown | 74 | 96 | 54.2% (41.8–65.5) | 70.8% | 24.3% | 0.83 | 0.79 | — | 0.85 |
| Unknown | 30 | 31 | 67.7% (48.1–85.7) | 80.6% | 29.7% | — | 0.86 | — | — |
| Asian | 28 | 34 | 61.8% (43.6–80.0) | 76.5% | 18.3% | 0.89 | 0.69 | — | 0.87 |
| Native American | 12 | 27 | 74.1% (nan–nan) | 85.2% | 44.0% | — | — | — | — |

## By unit type

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Med-Surg ICU | 1735 | 1968 | 58.2% (55.5–60.7) | 73.4% | 21.7% | 0.78 | 0.67 | 0.80 | 0.78 |
| MICU | 130 | 109 | 77.1% (69.6–84.6) | 83.5% | 24.1% | 0.79 | 0.67 | 0.87 | 0.82 |
| Cardiac ICU | 123 | 128 | 64.8% (55.6–73.5) | 81.2% | 27.7% | 0.92 | 0.81 | 0.73 | 0.88 |
| SICU | 77 | 74 | 58.1% (46.2–71.9) | 73.0% | 13.9% | 0.74 | 0.66 | 0.64 | — |
| CCU-CTICU | 77 | 65 | 47.7% (35.1–60.0) | 69.2% | 17.6% | 0.54 | — | — | 0.73 |
| Neuro ICU | 62 | 24 | 41.7% (17.8–70.6) | 62.5% | 11.9% | — | — | — | — |
| CSICU | 62 | 16 | 81.2% (55.6–100.0) | 93.8% | 13.2% | — | — | — | — |
| CTICU | 48 | 48 | 52.1% (35.3–68.8) | 75.0% | 16.4% | 0.96 | — | 0.66 | — |

## By panel size

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| >20 | 2059 | 2269 | 58.5% (56.3–61.0) | 74.2% | 21.4% | 0.80 | 0.68 | 0.77 | 0.80 |
| 11–20 | 191 | 129 | 62.0% (52.6–71.3) | 72.9% | 23.0% | 0.68 | 0.66 | 0.85 | 0.60 |
| ≤10 analytes | 64 | 34 | 76.5% (61.9–88.2) | 79.4% | 25.0% | 0.80 | — | — | — |

## By hospital

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| hosp 146 | 35 | 21 | 90.5% (75.0–100.0) | 95.2% | 22.0% | — | — | — | — |
| hosp 157 | 23 | 18 | 50.0% (33.3–70.0) | 66.7% | 9.4% | 0.68 | — | — | — |
| hosp 171 | 22 | 25 | 52.0% (25.7–78.4) | 80.0% | 18.6% | 0.84 | — | — | 0.89 |
| hosp 167 | 21 | 1 | 100.0% (0.0–100.0) | 100.0% | 7.7% | — | — | — | — |
| hosp 243 | 21 | 27 | 66.7% (50.0–81.8) | 81.5% | 52.6% | 0.98 | — | — | — |
| hosp 154 | 20 | 13 | 23.1% (0.0–47.4) | 46.2% | 0.0% | — | 0.57 | — | — |
| hosp 165 | 19 | 1 | 100.0% (nan–nan) | 100.0% | 13.3% | — | — | — | — |
| hosp 283 | 19 | 11 | 45.5% (nan–nan) | 54.5% | 11.1% | — | 0.49 | — | — |

## Strata deviating by more than 10 percentage points from overall recall@5 (n ≥ 40)

- unit type = MICU: recall@5 77.1% vs overall 59.0%
- unit type = CCU-CTICU: recall@5 47.7% vs overall 59.0%
- unit type = Neuro ICU: recall@5 41.7% vs overall 59.0%
- unit type = CSICU: recall@5 81.2% vs overall 59.0%
- panel size = ≤10 analytes: recall@5 76.5% vs overall 59.0%
