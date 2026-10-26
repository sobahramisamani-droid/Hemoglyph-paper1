# Hemoglyph — PhysioNet/CinC Challenge 2019 (hospital A subsample) held-out evaluation

patients in file 4991; with >=3 lab analytes in ICU h 1–24: 4529; evaluated 4529; sepsis (Sepsis-3, any hour) 269 (5.9%)

Task: PREDICTION of Sepsis-3 onset at any time during the ICU stay from the laboratory values of the first 24 h (labs only + temperature). This is deliberately harder than the eICU diagnosis task; labels are not visible to the engine.

| metric | value |
|---|---|
| AUROC sepsis-group probability (labs first 24 h) | 0.588 (0.559–0.616) |
| Supervised logistic baseline, 5-fold CV, same patients/features | 0.679 (0.646–0.714) |
| recall@5 of sepsis group among sepsis patients | 24.5% (19.8–30.0; 66/269) |
| sepsis group in top-5 among NON-sepsis patients (flag rate) | 11.8% (10.9–12.8; 502/4260) |
| sensitivity at p>=0.5 | 20.4% (16.1–25.7; 55/269) |
| specificity at p>=0.5 | 90.0% (89.0–90.8; 3832/4260) |
| latency ms median / p95 | 711 / 1493 |

Top-1 disease among sepsis patients: anemia 63, myocardial_injury_acuity_undetermined 46, acute_kidney_injury 38, sepsis 27, acute_myocardial_infarction 21, reduced_gfr_chronicity_undetermined 15, hepatocellular_injury_pattern 8, systemic_inflammatory_response_syndrome 7

Top-1 disease among non-sepsis patients: anemia 1583, myocardial_injury_acuity_undetermined 645, acute_kidney_injury 383, reduced_gfr_chronicity_undetermined 334, sepsis 225, acute_myocardial_infarction 183, leukocytosis_pattern 120, hypokalemia 83

Source: https://physionet.org/content/challenge-2019/1.0.0/ (Reyna et al. 2020). Subsample: every 4th file of training_setA; labs-only columns kept.
