# Hemoglyph — PhysioNet/CinC Challenge 2019 (hospital A subsample) held-out evaluation

patients in file 4979; with >=3 lab analytes in ICU h 1–24: 4558; evaluated 4558; sepsis (Sepsis-3, any hour) 268 (5.9%)

Task: PREDICTION of Sepsis-3 onset at any time during the ICU stay from the laboratory values of the first 24 h (labs only + temperature). This is deliberately harder than the eICU diagnosis task; labels are not visible to the engine.

| metric | value |
|---|---|
| AUROC sepsis-group probability (labs first 24 h) | 0.610 (0.583–0.640) |
| Supervised logistic baseline, 5-fold CV, same patients/features | 0.712 (0.679–0.744) |
| recall@5 of sepsis group among sepsis patients | 23.9% (19.2–29.3; 64/268) |
| sepsis group in top-5 among NON-sepsis patients (flag rate) | 10.9% (10.0–11.8; 466/4290) |
| sensitivity at p>=0.5 | 23.1% (18.5–28.5; 62/268) |
| specificity at p>=0.5 | 91.0% (90.1–91.8; 3903/4290) |
| latency ms median / p95 | 555 / 946 |

Top-1 disease among sepsis patients: anemia 55, acute_kidney_injury 45, myocardial_injury_acuity_undetermined 42, sepsis 24, hypocalcemia 13, acute_myocardial_infarction 13, reduced_gfr_chronicity_undetermined 12, hepatocellular_injury_pattern 11

Top-1 disease among non-sepsis patients: anemia 1478, acute_kidney_injury 588, myocardial_injury_acuity_undetermined 552, sepsis 195, reduced_gfr_chronicity_undetermined 180, hypocalcemia 173, acute_myocardial_infarction 170, leukocytosis_pattern 163

Source: https://physionet.org/content/challenge-2019/1.0.0/ (Reyna et al. 2020). Subsample: every 4th file of training_setA; labs-only columns kept.
