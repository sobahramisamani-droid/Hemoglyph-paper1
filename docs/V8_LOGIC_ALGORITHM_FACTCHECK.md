# Fact-check of the "logic & algorithm" roadmap against the engine (2026-10-26)

Method: each claim was checked against `analyse_gidlines.py` (v8) and the frozen v7/v8 evaluation artefacts before
deciding anything. Verdicts: ALREADY PRESENT (claim rests on a wrong premise) / REFUTED (data contradict the expected
gain) / IMPLEMENTED now / CANDIDATE (principled, needs its own gated cycle) / REJECTED (conflicts with the untrained,
guideline-only contract).

| # | claim | what the code/data actually show | verdict |
|---|---|---|---|
| 1 | Rules are flat; DKA/AKI/CKD are never composed; add Horn clauses | The expert syndrome layer *is* a composition layer: ~900 constellations with `req=[...]` conjunctions, `alt_req`, `excl`, context predicates. DKA alone has six composite definitions (`dka`, `euglycemic_dka`, `dka_ketones_unmeasured`, `dka_mild_ketones_unmeasured`, `dka_no_gap_severe/moderate`, l. 10439–12037), AKI has KDIGO trajectory and imputed-baseline constellations, CKD uses eGFR + ≥2 chronicity markers (l. 5060–5072). The DKA gap (26/107 absent) is panels **without** HCO₃/anion gap/ketones (triage 2026-10-26) — a conjunction cannot fire on a missing conjunct. Expected "+12/+10/+24 points" has no mechanism. | ALREADY PRESENT; gain REFUTED |
| 2 | Engine only rules in; add explicit "excluded" | `evidence_state` has `refuted`; registry has 6,220 `exclusion_criterion` rules; `kg.barresi_exclusions` removes contradicted candidates (l. 5258); dx-less guards carry absolute caps. The precision ceiling is the reference standard (~1.05 labels/stay → ≤ ~21 % at five assertions); the truncation simulation showed precision/recall trade ≈ 1:1 (14.2/60.8 → 19.0/53.5 → 23.3/43.3). "+6–11 points precision without recall loss" is arithmetically unavailable. | ALREADY PRESENT; gain REFUTED |
| 3 | Covering suppression too aggressive; make it asymmetric (acute > chronic) | `_apply_renal_chronicity` already orders AKI over CKD unless chronic markers/documented CKD; covering dx always explains, never buries an ESL-strong finding (v7 lessons). The DKA-under-diabetes case did not occur in the 107 coded DKA stays (misses were missing criteria). Property test P3 did find one covering-step inversion (renal lead 0.828 → 0.792 when `renal_failure_marked` fires) — logged below. | mostly PRESENT; one defect LOGGED |
| 4 | Context only echoes | Context predicates `med, cond, fh, pregnant, age_lt/ge, sex, encounter_in`, `ctx_any/ctx_excl`, pregnancy reference intervals, and `documented_history` tier exist; the eICU "echo" number measures a labs-only cohort where context was *withheld by design*. Medication → prior mappings (furosemide, steroids, metformin) exist as `med` predicates in constellations. | ALREADY PRESENT (unmeasurable on labs-only eICU) |
| 5 | Serial values unused | Temporal module is optional and present (`temporal_findings`, `aki_kdigo_creatinine_rise`, `aki_recovering_creatinine_fall`, troponin delta); eICU first-panel design is single time point by protocol. | ALREADY PRESENT (not exercised by the primary protocol) |
| 6 | Values treated as exact; add noise-aware inference | Fuzzy layer with `softness` per feature (128 references) and continuous memberships exists; P2 shows the differential moves continuously with value (300 vs 299.97 mg/dL → Δp 2×10⁻⁵). The one brittle perturbation case (thiazide hyponatraemia 3/5) is a threshold-straddling vignette; a formal measurement-uncertainty model (Na σ≈2) is principled (CLSI EP29) and is a **candidate** — but it would raise, not lower, the hyponatraemia assertion rate at Na 135–137 and must be gated against the healthy sweep. | CANDIDATE (gated) |
| 7 | Remove four inert layers | Ablation: Bayesian −1.3 (not inert); fuzzy/graph/risk ≈ 0 on *label recall*, but fuzzy carries perturbation robustness and the knowledge graph carries exclusions (#2) and `explained_by` nesting; the risk layer is the 100 documented risk models (product contract). Removing layers for a cleaner story is not an accuracy argument. | PARTLY; documented, not removed |
| 8 | Fusion weights from evidence tiers, not judgement | Rule scores already carry evidence tiers: anchors 0.92, definitional findings 0.80, ESL strengths anchor .95/strong .88/pattern .80/supportive .72/screen .45; `screening` leaves w3 vs `diagnostic_criterion` w6. The 0.35/0.25/… layer weights were shown insensitive (S12 sweep). Deriving layer weights "from priors" without data is still a judgement, relabelled. | PARTLY PRESENT; rest REJECTED as cosmetic |
| 9 | Expert floor 0.90 arbitrary | It encodes "a satisfied guideline criterion cannot be outvoted by prior-driven layers" (fusion-asymmetry fix v6.1, which removed a measured defect). Replacing it with a per-rule prior and Bayes would reintroduce exactly the vote dilution it fixed. | REJECTED (documented rationale) |
| 10 | Calibrate syndrome strengths by EM on 500 eICU labels | That is outcome-fitting of the knowledge layer on the evaluation cohort — forbidden by the untrained contract and by the user's standing rule (no outcome-fitted weights). | REJECTED |
| 11 | Ship a calibration map in the product | Already fitted and reported (ECE .162 → .003, slope .25; Fig. 8, S10) as a reporting layer; shipping it inside the product requires a development set that is not the evaluation set and a transfer check (MIMIC slope differs). Planned for the product, not the paper. | PRESENT (reporting); product item |
| 12 | Set-cover ranking | `explained_by` nesting + grouped rank *is* a greedy cover (entries explained by a diagnosis inherit its slot); grouped@5 67.4 vs flat 60.8 shows the effect. | ALREADY PRESENT |
| 13 | Missingness + next-test recommendation | `next_tests` (ESL ext. 8, `_NEXT_TEST_LIBRARY` with source per item) and `data_completeness` exist; entropy-optimal test choice would need calibrated posteriors (see #11). | PRESENT (heuristic); entropy version CANDIDATE |
| 14 | No property-based tests | True. **Implemented now**: `tests/test_properties.py` — P1 determinism, P2 unit invariance, P3 directional monotonicity (5 analytes), P4 absent key analyte never raises. Result: 10 passed, **1 genuine finding** (P3 creatinine, below). | IMPLEMENTED |
| 15 | No cross-dataset validation | MIMIC-IV demo (v7 35.3/47.5/62.1), NHANES ×3, UCI thyroid/HCV, ILPD, PMC cases, PhysioNet A/B/B2 are all reported; no eICU tuning occurred (change log C1–C16). | ALREADY PRESENT |

## Finding from the new property tests (not patched — "first evidence, then change")

Creatinine 1.6 → 2.2 mg/dL (55-year-old man, otherwise normal panel): the flat probability of the leading renal entity
falls 0.828 → 0.792, because at 2.2 the `renal_failure_marked` constellation fires, `acute_kidney_injury` (0.792) becomes
the covering entity and `reduced_gfr_chronicity_undetermined` (0.828 before) is nested beneath it at 0.752. Grouped and
two-tier outputs are monotone; the flat lead is not. Principle violated: a covering diagnosis should never score below
the entity it explains. Candidate fix for a gated v8.1: in the covering step, `cover.final_score = max(cover, covered_pre)`.
Recorded as `xfail(strict=True)` in `tests/test_properties.py` so it stays visible until fixed and gated.

## What would actually move the numbers (and what the data say)
- The eICU recall ceiling is set by panels lacking the defining analyte (275 labels) and by the problem-list reference
  standard (431 criterion-negative labels), not by composition, exclusion or covering logic.
- The only measured step this week was engine-external (sepsis companion, +4 points patient-level).
- The next real gains require clinician rule audit and credentialed full datasets — both parked for the user.
