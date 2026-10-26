# Hemoglyph — PhysioNet/CinC Challenge 2019 (hospital A subsample) held-out evaluation

patients in file 4964; with >=3 lab analytes in ICU h 1–24: 4871; evaluated 4871; sepsis (Sepsis-3, any hour) 439 (9.0%)

Task: PREDICTION of Sepsis-3 onset at any time during the ICU stay from the laboratory values of the first 24 h (labs only + temperature). This is deliberately harder than the eICU diagnosis task; labels are not visible to the engine.

| metric | value |
|---|---|
| AUROC sepsis-group probability (labs first 24 h) | 0.600 (0.575–0.625) |
| Supervised logistic baseline, 5-fold CV, same patients/features | 0.691 (0.664–0.718) |
| recall@5 of sepsis group among sepsis patients | 33.5% (29.2–38.0; 147/439) |
| sepsis group in top-5 among NON-sepsis patients (flag rate) | 17.0% (16.0–18.2; 755/4432) |
| sensitivity at p>=0.5 | 29.4% (25.3–33.8; 129/439) |
| specificity at p>=0.5 | 85.7% (84.6–86.7; 3798/4432) |
| latency ms median / p95 | 694 / 1145 |

Top-1 disease among sepsis patients: anemia 127, sepsis 68, acute_kidney_injury 63, hypocalcemia 20, hepatocellular_injury_pattern 19, leukocytosis_pattern 18, reduced_gfr_chronicity_undetermined 13, copd 11

Top-1 disease among non-sepsis patients: anemia 1960, acute_kidney_injury 512, sepsis 370, leukocytosis_pattern 224, hypocalcemia 158, reduced_gfr_chronicity_undetermined 139, hepatocellular_injury_pattern 120, acute_myocardial_infarction 84

Source: https://physionet.org/content/challenge-2019/1.0.0/ (Reyna et al. 2020). Subsample: every 4th file of training_setA; labs-only columns kept.
