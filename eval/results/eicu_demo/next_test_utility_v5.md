# Next-test utility on category-A misses (eICU-CRD demo)

Category-A misses in the fixed-seed audit sample with a scorable discriminating test: 101. For each, the engine was re-run and its `next_tests` / per-entity `recommended_tests` were searched for the test that would establish the listed condition (e.g. BNP for heart failure, HbA1c for diabetes, lactate/procalcitonin/cultures for sepsis, prior creatinine/ACR/cystatin C for CKD).

| listed condition (no lab signature) | n | discriminating test recommended | % |
|---|---:|---:|---:|
| heart failure | 33 | 19 | 58% |
| diabetes | 18 | 5 | 28% |
| sepsis | 16 | 12 | 75% |
| renal impairment | 11 | 7 | 64% |
| chronic kidney disease | 8 | 5 | 62% |
| hyperglycemia | 4 | 2 | 50% |
| alcohol withdrawal | 3 | 1 | 33% |
| coagulopathy | 3 | 0 | 0% |
| acute kidney injury | 3 | 1 | 33% |
| malnutrition | 1 | 0 | 0% |
| hypocalcemia | 1 | 0 | 0% |
| **all** | **101** | **52** | **51%** |

Median number of next-test recommendations per stay: 12.

## Examples

- stay 1325742 listed **renal_impairment** (no lab signature) → next tests: ['Blood cultures ×2', 'Ionised calcium (or albumin-corrected calcium)', 'β-hydroxybutyrate', 'INR and albumin', 'Procalcitonin'] → ✗
- stay 1573546 listed **heart_failure** (no lab signature) → next tests: ['Serial high-sensitivity troponin (0/1 h or 0/3 h)', 'Baseline / prior creatinine (chronicity)', 'Blood cultures ×2 before antibiotics', 'BNP / NT-proBNP', 'Urinalysis with microscopy'] → ✓
- stay 453326 listed **heart_failure** (no lab signature) → next tests: ['Serial high-sensitivity troponin', 'Baseline / prior creatinine (chronicity)', 'Serum lactate', 'β-hydroxybutyrate', 'Blood cultures ×2'] → ✓
- stay 2691019 listed **diabetes** (no lab signature) → next tests: ['Serum lactate', 'Blood cultures ×2 before antibiotics', 'Ferritin and transferrin saturation', 'Reticulocyte count', 'Blood gas (bicarbonate)'] → ✓
- stay 2784403 listed **heart_failure** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serum lactate', 'Blood cultures ×2', 'Urinalysis with microscopy', 'Urine sodium / FENa'] → ✓
- stay 399713 listed **heart_failure** (no lab signature) → next tests: ['Serum lactate', 'Blood cultures ×2 before antibiotics', 'Baseline / prior creatinine (chronicity)', 'Arterial blood gas', 'Procalcitonin'] → ✓
- stay 2893348 listed **heart_failure** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serum lactate', 'Blood cultures ×2', 'Ionised calcium (or albumin-corrected calcium)', 'Ferritin and transferrin saturation'] → ✗
- stay 2893348 listed **diabetes** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serum lactate', 'Blood cultures ×2', 'Ionised calcium (or albumin-corrected calcium)', 'Ferritin and transferrin saturation'] → ✗
