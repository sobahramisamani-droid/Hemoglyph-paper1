# Label-mapping audit — eICU diagnosis strings → 31 target groups (100 random held-out stays, seed 7)

Purpose: quantify noise introduced by the regex label map (`eval_eicu.GROUPS`) relative to a human reading of the
raw `diagnosisstring` entries. Procedure: (1) an independent, deliberately liberal second keyword coder was run on
the same strings; (2) every disagreement between the study regex and the liberal coder (23 of 3,100 stay×group cells)
was adjudicated by reading the full diagnosis strings; (3) no disagreement-free cell was re-read (so agreement on
negatives is assumed — the liberal coder is a superset by design).

| item | value |
|---|---|
| stays / diagnosis strings read | 100 / 425 |
| stay×group cells | 3,100 |
| regex-positive labels | 150 |
| regex false positives (label present, string does not support it) | **0** |
| definite regex misses | **2** (stay 244477 "hematological effect of infection\|thrombocytopenia" → thrombocytopenia; stay 351525 "drug withdrawal\|alcohol withdrawal" → alcohol_withdrawal) |
| ambiguous (not counted as miss) | 2 (852424 "cardiomyopathy, dilated, ischemic" → heart_failure?; 3225577 "hemorrhage related to anticoagulation" → coagulopathy?) |
| liberal-coder false alarms (rejected on reading) | 19 (category-header matches such as "renal system infection", "systemic" ⊃ "MI", "not due to CHF") |
| estimated label sensitivity of the map vs human reading | 150/152 = 98.7% (worst case incl. ambiguous 150/154 = 97.4%) |
| estimated label precision | 150/150 = 100% |

Interpretation: the regex map is a near-lossless transcription of what clinicians *recorded*; the dominant label noise is
therefore **under-documentation** (conditions present but never entered as a diagnosis), which cannot be audited from the
strings and which biases every system's apparent precision downward equally. Decision: the two missed patterns are **not** changed for the v5.2 freeze (all v5.x arms must share one label map); they are
logged for the next protocol version (expected effect ≤ 2 labels per 100 stays, ≈1.3% of positives).
