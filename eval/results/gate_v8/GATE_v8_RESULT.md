# Engine v8 development gate — result (2026-10-26)

Candidate: `analyse_gidlines.py` + MELD/MELD-Na and PLR derived patterns + `confidence_band`/`concise` presentation
fields; registry 14.2.0 (28 rules re-sourced with Crossref-verified DOIs, no logic change). Frozen v7 artefacts untouched.

| lane | v8 | v7 reference |
|---|---|---|
| hard battery 1 / 2 / 3 | 151/151, 124/124, 77/78 (same pre-existing miss: alcoholic pancreatitis) | identical |
| healthy sweep n=1000 seed 7 | 0 syndrome fires, 0 dx ≥ 0.5 (worst p 0.45) | identical |
| perturbation fuzz 3 % × 5 | 753/755, fully robust 150/151 | identical |
| pytest | 680 passed, 9 skipped (+4 new in `tests/test_v8_indices.py`, run separately: 4/4) | 689 collected |
| eICU labs-only 2,314 stays, `--encounter icu` | flat 47.9 / 60.8 / 74.1; two-tier 33.1 / 62.0 / 71.9; grouped 30.1 / 55.6 / 67.4 / 77.9; every per-group count identical to v7 (`summary_v8.json` == `summary_v7.json` on `recall`, `recall_two_tier`, `groups`) | same |

Non-inferiority criterion (flat@5 ≥ 60.3, two-tier@5 ≥ 71.4): MET at exact parity, as designed — v8 adds
prognostic indices and presentation metadata without touching ranking. Results: `eval/results/eicu_demo/{summary,report,per_stay}_v8.*`.
Companion (outside engine): sepsis risk module, `eval/results/sepsis_ml/sepsis_ml_report.md`.
