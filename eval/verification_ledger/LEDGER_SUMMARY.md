# Verification Ledger — summary (registry 15.2.0; built from frozen artefacts, nothing re-measured)

Rows: 605 rules = union of the 285 curated rules of 14.1.0 (272 anchors + 13 demoted), the 364-rule active core and the 335-rule CORE arm.

## Status precedence (first matching label wins)

1. `retired` — non-executable in 15.2.0 with a `retired_*` status (15.0.0/15.1.0 patches under written protocol).
2. `discordant_open` — a frozen-sample verdict of DISCORDANT and no change to the rule since (status unchanged, no patch touched it).
3. `discordant_corrected` — DISCORDANT verdict, and a later release patch (under written protocol) touched the rule; Note 8 verdicts (2026-10-26) precede 15.0.0, Note 15 verdicts (2026-10-28) precede only 15.2.0.
4. `quote_verified` — the registry carries a verbatim source quote for the rule (15.0.0 R3) or a frozen-sample verdict of CONCORDANT with quote.
5. `flagged_open` — at least one static-detector flag on 15.2.0 (calibrated detectors; a flag is a candidate defect, not a verdict).
6. `source_reachable_unverified` — first source resolves to a DOI or a specific document page, but no one has checked the rule against it.
7. `unresolvable` — first source is a generic standards page, an organisation landing page, unreachable, or absent; or the sampled verdict was UNRESOLVABLE.

`quote_verified` means transcription concordance by a single declared AI rater; it is not clinical validation.

## Counts

| set | n | retired | discordant_open | discordant_corrected | quote_verified | flagged_open | source_reachable_unverified | unresolvable |
|---|---|---|---|---|---|---|---|---|
| curated anchors (272, 14.1.0) | 272 | 1 (0%) | 7 (3%) | 1 (0%) | 18 (7%) | 3 (1%) | 101 (37%) | 141 (52%) |
| active core (364) | 364 | 145 (40%) | 4 (1%) | 1 (0%) | 37 (10%) | 3 (1%) | 17 (5%) | 157 (43%) |
| hot core (174) | 174 | 71 (41%) | 4 (2%) | 1 (1%) | 30 (17%) | 1 (1%) | 10 (6%) | 57 (33%) |
| CORE arm of the sufficiency study (335, 15.1.0) | 335 | 0 (0%) | 8 (2%) | 1 (0%) | 37 (11%) | 3 (1%) | 108 (32%) | 178 (53%) |
| union (all ledger rows) | 605 | 145 (24%) | 8 (1%) | 1 (0%) | 37 (6%) | 5 (1%) | 115 (19%) | 294 (49%) |

## Facts the ledger makes explicit

- The CORE arm (335) is **not** the active core: it is 284 curated rules + 19 quote-verified non-curated rules + 32 reference-interval conventions; only 94 of the 364 active-core rules are in it.
- Of the 364 active-core rules, 219 are still executable in 15.2.0 (145 retired under the 15.0.0 protocol).
- Invariant tests reach the analyte of 104 of the 219 executable active-core rules; the rest are untouched by any executable property.
- Static detectors flag 6 ledger rules on 15.2.0 (was 120 on 14.1.0).
- Concordance verdicts exist for 116 ledger rules from the 200-rule sample and 100 from the active-core sample.

## Open items (input to the next registry protocol; nothing patched here)

- `acquired_hemophilia_a_reanchor_scre_v13_4` — discordant_open: Note 8: attribution: acquired haemophilia A cites the BSH rare coagulation disorders guideline, which excludes FVIII deficiency (covered by a separate BSH guideline)
- `acute_kidney_injury_kdigo_2012_creatinine_absolute_cur13` — flagged_open: ; r2a: single ubiquitous analyte creatinine for clinical entity acute_kidney_injury
- `hepatitis_a_igm_anti_hav_positive_cur13` — discordant_open: Note 8: attribution: hepatitis A IgM criterion cites the EASL hepatitis E guideline
- `hyperosmolar_hyperglycemic_state_ada_easd_2024_hhs_ketoacidosis_exclusion_cur13` — flagged_open: ; src: source ada_easd_hyperglycemic_crises_2024 scope ['endocrine'] vs entity domain critical_care
- `hyperprolactinemia_pituitary_2023_prolactin_elevated_cur13` — discordant_open: Note 8: threshold: Pituitary Society 2023 consensus (full text retrieved) defers to assay-specific reference ranges and does not state 25 ng/mL
- `hypomagnesemia_severe_1_2_cur13` — discordant_open: Note 8: attribution: severe hypomagnesaemia <1.2 mg/dL cites the KDIGO potassium/dyskalaemia conference report
- `isoniazid_hepatotoxicity_dx_p131` — flagged_open: ; src: source ats_isoniazid_hepatotoxicity_2006 scope ['liver'] vs entity domain toxicology_tdm
- `lactic_acidosis_lactate_4_acidemia_cur13` — flagged_open: ; src: source sepsis3_2016 scope ['critical_care', 'infectious'] vs entity domain diabetes_metabolic
- `prediabetes_hba1c_pattern_screening_1_v1` — discordant_open: Note 15: boundary: source range 5.7–6.4 % inclusive with upper bound; rule '> 5.7' excludes 5.7 and has no upper bound
- `pseudohypoparathyroidism_hypocalcemia_high_pth_normal_renal_cur13` — discordant_open: Note 8: attribution: pseudohypoparathyroidism criteria cite the primary hyperparathyroidism workshop guideline (different disease)
- `rhabdomyolysis_ck_5x_uln_diagnostic_cur13` — discordant_open: Note 15: boundary: source '> 1000', rule '>= 1000'; source is a systematic review, not a guideline
- `septic_shock_severe_lactic_acidosis_sepsis3_lactate_4_cur13` — discordant_open: Note 8: threshold: cited Sepsis-3 defines septic shock with lactate >2 mmol/L; the >4 mmol/L cut-off is not in the cited source (it derives from the SSC resuscitation bundle)
- `urea_cycle_disorder_otc_deficiency_nh3_diagnostic_v1` — flagged_open: ; src: source acmg_act_2024 scope ['genetics'] vs entity domain critical_care

Files: `LEDGER.json.gz` (records), `ledger_counts.json`, `build_ledger.py` (reproducible definition).
