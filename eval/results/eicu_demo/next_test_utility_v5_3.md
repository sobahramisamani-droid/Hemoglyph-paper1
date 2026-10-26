# Next-test utility on category-A misses (eICU-CRD demo)

Category-A misses in the fixed-seed audit sample with a scorable discriminating test: 88. For each, the engine was re-run and its `next_tests` / per-entity `recommended_tests` were searched for the test that would establish the listed condition (e.g. BNP for heart failure, HbA1c for diabetes, lactate/procalcitonin/cultures for sepsis, prior creatinine/ACR/cystatin C for CKD).

| listed condition (no lab signature) | n | discriminating test recommended | % |
|---|---:|---:|---:|
| heart failure | 27 | 14 | 52% |
| diabetes | 21 | 5 | 24% |
| hyperglycemia | 7 | 3 | 43% |
| chronic kidney disease | 7 | 3 | 43% |
| sepsis | 7 | 5 | 71% |
| renal impairment | 6 | 5 | 83% |
| acute kidney injury | 5 | 2 | 40% |
| malnutrition | 4 | 2 | 50% |
| alcohol withdrawal | 4 | 3 | 75% |
| **all** | **88** | **42** | **48%** |

Median number of next-test recommendations per stay: 12.

## Examples

- stay 3085970 listed **malnutrition** (no lab signature) → next tests: ['INR and albumin', 'Peripheral blood smear (clumping, schistocytes, blasts)', 'PT/INR, aPTT, fibrinogen, D-dimer', 'Serum osmolality', 'Urine osmolality and urine sodium'] → ✗
- stay 2579022 listed **heart_failure** (no lab signature) → next tests: ['Serum osmolality', 'Urine osmolality and urine sodium', 'Ionised calcium (or albumin-corrected calcium)', 'Serum lactate', 'Blood cultures ×2'] → ✗
- stay 1494982 listed **heart_failure** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serum lactate', 'β-hydroxybutyrate', 'Urinalysis with microscopy', 'Urine sodium / FENa'] → ✓
- stay 1573546 listed **heart_failure** (no lab signature) → next tests: ['Serial high-sensitivity troponin (0/1 h or 0/3 h)', 'Baseline / prior creatinine (chronicity)', 'Blood cultures ×2 before antibiotics', 'BNP / NT-proBNP', 'Urinalysis with microscopy'] → ✓
- stay 2614647 listed **renal_impairment** (no lab signature) → next tests: ['Ionised calcium (or albumin-corrected calcium)', 'Ferritin and transferrin saturation', 'Reticulocyte count', 'Magnesium and phosphate', 'Vitamin B12 and folate'] → ✗
- stay 3152675 listed **heart_failure** (no lab signature) → next tests: ['Repeat potassium (non-haemolysed, no fist clenching)', 'Blood gas', 'Baseline / prior creatinine (chronicity)', 'Blood cultures ×2', 'Urinalysis with microscopy'] → ✓
- stay 1599068 listed **heart_failure** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serum lactate', 'Blood cultures ×2', 'Free T4', 'Urinalysis with microscopy'] → ✓
- stay 496980 listed **hyperglycemia** (no lab signature) → next tests: ['Blood cultures ×2', 'Arterial blood gas', 'Peripheral blood smear (clumping, schistocytes, blasts)', 'PT/INR, aPTT, fibrinogen, D-dimer', 'Procalcitonin'] → ✓
