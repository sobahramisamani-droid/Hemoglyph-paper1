# Next-test utility on category-A misses (eICU-CRD demo)

Category-A misses in the fixed-seed audit sample with a scorable discriminating test: 83. For each, the engine was re-run and its `next_tests` / per-entity `recommended_tests` were searched for the test that would establish the listed condition (e.g. BNP for heart failure, HbA1c for diabetes, lactate/procalcitonin/cultures for sepsis, prior creatinine/ACR/cystatin C for CKD).

| listed condition (no lab signature) | n | discriminating test recommended | % |
|---|---:|---:|---:|
| heart failure | 28 | 10 | 36% |
| diabetes | 19 | 6 | 32% |
| sepsis | 13 | 6 | 46% |
| acute kidney injury | 5 | 2 | 40% |
| chronic kidney disease | 4 | 1 | 25% |
| renal impairment | 4 | 1 | 25% |
| hyperglycemia | 4 | 3 | 75% |
| alcohol withdrawal | 3 | 2 | 67% |
| malnutrition | 2 | 2 | 100% |
| coagulopathy | 1 | 1 | 100% |
| **all** | **83** | **34** | **41%** |

Median number of next-test recommendations per stay: 12.

## Examples

- stay 450383 listed **sepsis** (no lab signature) → next tests: ['Ionised calcium (or albumin-corrected calcium)', 'Ferritin and transferrin saturation', 'Reticulocyte count', 'Vitamin B12 and folate', 'LDH, haptoglobin, bilirubin'] → ✗
- stay 2818995 listed **heart_failure** (no lab signature) → next tests: ['HbA1c', 'C-reactive protein', 'Urine albumin-creatinine ratio', 'Lipid panel', 'OGTT'] → ✗
- stay 2646210 listed **sepsis** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Peripheral blood smear (clumping, schistocytes, blasts)', 'PT/INR, aPTT, fibrinogen, D-dimer', 'INR and albumin', 'Urinalysis with microscopy'] → ✗
- stay 3058804 listed **chronic_kidney_disease** (no lab signature) → next tests: ['Blood cultures ×2 (peripheral + any line) before antibiotics', 'Peripheral blood smear (clumping, schistocytes, blasts)', 'PT/INR, aPTT, fibrinogen, D-dimer', 'Arterial blood gas', 'β-hydroxybutyrate'] → ✗
- stay 3058972 listed **sepsis** (no lab signature) → next tests: ['Serial high-sensitivity troponin (0/1 h or 0/3 h)', 'Urine osmolality and urine sodium', 'Prior creatinine (≥ 3 months)', 'BNP / NT-proBNP', 'Urine albumin-creatinine ratio'] → ✗
- stay 3098657 listed **alcohol_withdrawal** (no lab signature) → next tests: ['β-hydroxybutyrate', 'Blood cultures ×2', 'Baseline / prior creatinine (chronicity)', 'Ionised calcium (or albumin-corrected calcium)', 'Serum osmolality (osmolal gap)'] → ✗
- stay 2792350 listed **diabetes** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serial high-sensitivity troponin', 'Serum lactate', 'Blood cultures ×2 before antibiotics', 'INR and albumin'] → ✗
- stay 341781 listed **heart_failure** (no lab signature) → next tests: ['Prior creatinine (≥ 3 months)', 'Serum osmolality', 'Urine osmolality and urine sodium', 'Serum lactate', 'Blood cultures ×2 before antibiotics'] → ✗
