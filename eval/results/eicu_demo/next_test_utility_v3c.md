# Next-test utility on category-A misses (eICU-CRD demo)

Category-A misses in the fixed-seed audit sample with a scorable discriminating test: 82. For each, the engine was re-run and its `next_tests` / per-entity `recommended_tests` were searched for the test that would establish the listed condition (e.g. BNP for heart failure, HbA1c for diabetes, lactate/procalcitonin/cultures for sepsis, prior creatinine/ACR/cystatin C for CKD).

| listed condition (no lab signature) | n | discriminating test recommended | % |
|---|---:|---:|---:|
| heart failure | 21 | 8 | 38% |
| sepsis | 19 | 11 | 58% |
| diabetes | 17 | 3 | 18% |
| renal impairment | 6 | 4 | 67% |
| hyperglycemia | 4 | 3 | 75% |
| chronic kidney disease | 4 | 2 | 50% |
| coagulopathy | 3 | 1 | 33% |
| malnutrition | 3 | 0 | 0% |
| acute kidney injury | 2 | 2 | 100% |
| alcohol withdrawal | 2 | 0 | 0% |
| hypocalcemia | 1 | 0 | 0% |
| **all** | **82** | **34** | **41%** |

Median number of next-test recommendations per stay: 12.

## Examples

- stay 1785133 listed **diabetes** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Urinalysis with microscopy', 'Urine sodium / FENa', 'C-reactive protein', 'Cystatin C'] → ✗
- stay 1568171 listed **sepsis** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serum osmolality', 'Urine osmolality and urine sodium', 'Repeat potassium (non-haemolysed, no fist clenching)', 'Blood cultures ×2'] → ✓
- stay 2826676 listed **sepsis** (no lab signature) → next tests: ['Serial high-sensitivity troponin', 'Prior creatinine (≥ 3 months)', 'β-hydroxybutyrate', 'Venous blood gas', 'Serum lactate'] → ✓
- stay 2778495 listed **heart_failure** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Ionised calcium (or albumin-corrected calcium)', 'Blood cultures ×2 before antibiotics', 'Repeat potassium (non-haemolysed, no fist clenching)', 'Potassium, phosphate, calcium, uric acid'] → ✗
- stay 2792350 listed **heart_failure** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Serial high-sensitivity troponin', 'Serum lactate', 'Blood cultures ×2 before antibiotics', 'INR and albumin'] → ✓
- stay 197617 listed **diabetes** (no lab signature) → next tests: ['Serum lactate', 'β-hydroxybutyrate', 'Ionised calcium (or albumin-corrected calcium)', 'Baseline / prior creatinine (chronicity)', 'Peripheral blood smear (clumping, schistocytes, blasts)'] → ✗
- stay 2791385 listed **diabetes** (no lab signature) → next tests: ['Baseline / prior creatinine (chronicity)', 'Blood cultures ×2', 'β-hydroxybutyrate', 'Serial high-sensitivity troponin', 'Ionised calcium (or albumin-corrected calcium)'] → ✗
- stay 2743241 listed **heart_failure** (no lab signature) → next tests: ['Serum lactate (repeat if > 2 mmol/L)', 'Blood cultures ×2', 'Arterial blood gas', 'Serum osmolality', 'Urine osmolality and urine sodium'] → ✗
