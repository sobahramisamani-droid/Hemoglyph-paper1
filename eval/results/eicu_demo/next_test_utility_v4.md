# Next-test utility on category-A misses (eICU-CRD demo)

Category-A misses in the fixed-seed audit sample with a scorable discriminating test: 77. For each, the engine was re-run and its `next_tests` / per-entity `recommended_tests` were searched for the test that would establish the listed condition (e.g. BNP for heart failure, HbA1c for diabetes, lactate/procalcitonin/cultures for sepsis, prior creatinine/ACR/cystatin C for CKD).

| listed condition (no lab signature) | n | discriminating test recommended | % |
|---|---:|---:|---:|
| heart failure | 25 | 15 | 60% |
| diabetes | 20 | 7 | 35% |
| sepsis | 14 | 8 | 57% |
| renal impairment | 4 | 2 | 50% |
| hyperglycemia | 3 | 2 | 67% |
| alcohol withdrawal | 3 | 2 | 67% |
| acute kidney injury | 3 | 3 | 100% |
| chronic kidney disease | 3 | 1 | 33% |
| coagulopathy | 1 | 0 | 0% |
| malnutrition | 1 | 0 | 0% |
| **all** | **77** | **40** | **52%** |

Median number of next-test recommendations per stay: 12.

## Examples

- stay 876268 listed **renal_impairment** (no lab signature) → next tests: ['Peripheral blood smear (clumping, schistocytes, blasts)', 'PT/INR, aPTT, fibrinogen, D-dimer', 'Ionised calcium (or albumin-corrected calcium)', 'Prior creatinine (≥ 3 months)', 'Hepatitis B surface antigen, hepatitis C antibody'] → ✓
- stay 1144659 listed **sepsis** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Blood cultures ×2', 'Ferritin and transferrin saturation', 'Reticulocyte count', 'Urinalysis with microscopy'] → ✓
- stay 2372698 listed **heart_failure** (no lab signature) → next tests: ['Serial high-sensitivity troponin (0/1 h or 0/3 h)', 'Prior creatinine (≥ 3 months)', 'Blood cultures ×2 before antibiotics', 'Ionised calcium (or albumin-corrected calcium)', 'BNP / NT-proBNP'] → ✓
- stay 1567943 listed **heart_failure** (no lab signature) → next tests: ['Serial high-sensitivity troponin (0/1 h or 0/3 h)', 'Repeat potassium (non-haemolysed, no fist clenching)', 'Serum lactate (repeat if > 2 mmol/L)', 'Blood cultures ×2', 'Fibrinogen, D-dimer, platelet trend'] → ✓
- stay 3057805 listed **hyperglycemia** (no lab signature) → next tests: ['Blood gas (bicarbonate)', 'Ferritin and transferrin saturation', 'Reticulocyte count', 'Vitamin B12 and folate', 'LDH, haptoglobin, bilirubin'] → ✗
- stay 508973 listed **diabetes** (no lab signature) → next tests: ['Prior creatinine (≥ 3 months)', 'Ionised calcium (or albumin-corrected calcium)', 'Arterial/venous blood gas', 'Serum lactate', 'β-hydroxybutyrate'] → ✗
- stay 2822610 listed **diabetes** (no lab signature) → next tests: ['Blood cultures ×2', 'Hepatitis B surface antigen, hepatitis C antibody', 'Procalcitonin', 'GGT and ethanol', 'Liver Ultrasound'] → ✗
- stay 3066852 listed **alcohol_withdrawal** (no lab signature) → next tests: ['Peripheral blood smear (clumping, schistocytes, blasts)', 'PT/INR, aPTT, fibrinogen, D-dimer', 'INR and albumin', 'Serum osmolality', 'Urine osmolality and urine sodium'] → ✓
