# Hemoglyph — PhysioNet/CinC Challenge 2019 (hospital A subsample) held-out evaluation

patients in file 4979; with >=3 lab analytes in ICU h 1–24: 4558; evaluated 4558; sepsis (Sepsis-3, any hour) 268 (5.9%)

Task: PREDICTION of Sepsis-3 onset at any time during the ICU stay from the laboratory values of the first 24 h (labs only + temperature). This is deliberately harder than the eICU diagnosis task; labels are not visible to the engine.

| metric | value |
|---|---|
| AUROC sepsis-group probability (labs first 24 h) | 0.611 (0.584–0.642) |
| Supervised logistic baseline, 5-fold CV, same patients/features | 0.712 (0.679–0.744) |
| recall@5 of sepsis group among sepsis patients | 24.3% (19.5–29.7; 65/268) |
| sepsis group in top-5 among NON-sepsis patients (flag rate) | 11.6% (10.7–12.6; 499/4290) |
| sensitivity at p>=0.5 | 23.5% (18.8–28.9; 63/268) |
| specificity at p>=0.5 | 90.9% (90.0–91.8; 3901/4290) |
| latency ms median / p95 | 561 / 978 |

Top-1 disease among sepsis patients: anemia 80, chronic_kidney_disease 35, sepsis 27, acute_kidney_injury 17, hypocalcemia 15, hypokalemia 14, acute_myocardial_infarction 14, hepatocellular_injury_pattern 13

Top-1 disease among non-sepsis patients: anemia 1841, chronic_kidney_disease 468, leukocytosis_pattern 223, hypocalcemia 220, acute_kidney_injury 201, sepsis 199, acute_myocardial_infarction 193, diabetes_mellitus 124

Source: https://physionet.org/content/challenge-2019/1.0.0/ (Reyna et al. 2020). Subsample: every 4th file of training_setA; labs-only columns kept.
