# Engine v8.1 gate (2026-10-26) — PASS (non-inferior; small gains)

Changes gated: (1) finding-demotion passes no longer cap a finding below a presumptive (< 0.80) explainer
(covering inversion found by property test P3); (2) measurement-uncertainty reporting (`borderline_values`, no score effect);
(3) property tests P1–P6 (21 tests). Registry unchanged (14.2.0). No eICU-informed parameter was touched.

| Check | v8 | v8.1 |
|---|---|---|
| hard_battery / 2 / 3 | 151/151, 124/124, 77/78 | 151/151, 124/124, 77/78 (same miss: alcoholic pancreatitis) |
| perturbation 3 %×5 | 753/755 (thiazide 3/5) | 753/755 (same) |
| healthy sweep n=1000 | 0 false, worst p .45 | 0 false, worst p .45 |
| pytest (alone) | 680 passed / 9 skipped | 705 passed / 9 skipped |
| eICU labs-only flat @3/5/10 | 47.9 / 60.8 / 74.1 | **48.4 / 61.0 / 74.1** (+13 / +5 / 0 labels of 2,432) |
| two-tier @1/3/5 | 33.1 / 62.0 / 71.9 | 33.5 / 62.3 / 72.1 |
| grouped @1/3/5/10 | 30.1 / 55.6 / 67.4 / 77.9 | 30.2 / 55.6 / 67.3 / 77.9 |
| mean AUROC (24 groups) | .767 | .766 |
| groups moved | — | renal_impairment AUROC .777→.795, recall@5 .813→.816; hyperkalaemia recall@5 .490→.571; AKI recall@5 .775→.780; sepsis recall@5 .491→.488 (−1 stay); AMI AUROC .758→.751 |

Interpretation: the gain is where the fix acts (renal findings no longer pulled under a presumptive AKI; a stronger
reduced-GFR entry also stops displacing hyperkalaemia from top-5 in the same stays). Differences are within the v7 CIs and
are reported as parity, not as improvement, in the paper. Latency unchanged (hard median ≈0.5 s).
