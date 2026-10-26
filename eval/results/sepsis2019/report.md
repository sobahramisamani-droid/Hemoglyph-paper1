# Hemoglyph — PhysioNet/CinC Challenge 2019 (hospital A subsample) held-out evaluation

patients in file 4937; with >=3 lab analytes in ICU h 1–24: 4843; evaluated 4843; sepsis (Sepsis-3, any hour) 438 (9.0%)

Task: PREDICTION of Sepsis-3 onset at any time during the ICU stay from the laboratory values of the first 24 h (labs only + temperature). This is deliberately harder than the eICU diagnosis task; labels are not visible to the engine.

| metric | value |
|---|---|
| AUROC sepsis-group probability (labs first 24 h) | 0.593 (0.570–0.617) |
| Supervised logistic baseline, 5-fold CV, same patients/features | 0.689 (0.663–0.715) |
| recall@5 of sepsis group among sepsis patients | 32.2% (28.0–36.7; 141/438) |
| sepsis group in top-5 among NON-sepsis patients (flag rate) | 16.5% (15.4–17.6; 725/4405) |
| sensitivity at p>=0.5 | 29.9% (25.8–34.4; 131/438) |
| specificity at p>=0.5 | 85.8% (84.7–86.8; 3778/4405) |
| latency ms median / p95 | 624 / 1173 |

Top-1 disease among sepsis patients: anemia 144, sepsis 59, acute_kidney_injury 47, chronic_kidney_disease 34, leukocytosis_pattern 22, hypocalcemia 20, hepatocellular_injury_pattern 16, lactic_acidosis 12

Top-1 disease among non-sepsis patients: anemia 2117, acute_kidney_injury 374, sepsis 330, leukocytosis_pattern 287, chronic_kidney_disease 238, hypocalcemia 160, hepatocellular_injury_pattern 117, acute_myocardial_infarction 84

Source: https://physionet.org/content/challenge-2019/1.0.0/ (Reyna et al. 2020). Subsample: every 4th file of training_setA; labs-only columns kept.
