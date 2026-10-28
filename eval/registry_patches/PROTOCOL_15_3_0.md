# Registry 15.3.0 — closing the open items of the verification ledger (protocol written 2026-10-28 before the patch ran)

Scope. Exactly the 13 open items listed in `eval/verification_ledger/LEDGER_SUMMARY.md` (8 `discordant_open`,
5 `flagged_open`) plus the per-rule ledger label. Every action is defined by the rule text and a retrieved source, not
by any benchmark number. No threshold is tuned, no rule is added, no source is cited from memory: a source is attached
only if its text was retrieved in this session and the quote is recorded in the patch. The eICU/NHANES gate is run
once afterwards as a non-regression check and its result is reported whatever it is; a drop > 0.5 points in any
primary metric means stop-and-report, not re-tuning. Frozen v7 / 14.1.0 results and the paper's tables do not change.

## D1 — attribution discordances recorded in Note 8 (6 rules)

| rule | finding (Note 8) | action | basis |
|---|---|---|---|
| `pseudohypoparathyroidism_hypocalcemia_high_pth_normal_renal_cur13` | cites the primary hyperparathyroidism workshop | `source_ids` → new source `php_consensus_2018` with verified quote | Mantovani et al., first international Consensus Statement, Nat Rev Endocrinol 2018, doi 10.1038/s41574-018-0042-0, PMC6541219 (full text retrieved): "The definition of PTH resistance is as follows: The association of hypocalcaemia, hyperphosphataemia and elevated serum levels of PTH in the absence of vitamin D deficiency and when magnesium levels and renal function are normal." |
| `hepatitis_a_igm_anti_hav_positive_cur13` | cites the HEV guideline | `source_ids` → new source `cdc_hav_case_definition_2019` with verified quote | CDC/CSTE Hepatitis A, Acute 2019 case definition (page retrieved): "Confirmatory laboratory evidence: Immunoglobulin M (IgM) antibody to hepatitis A virus (anti-HAV) positive, OR Nucleic acid amplification test … for hepatitis A virus RNA positive". |
| `hypomagnesemia_severe_1_2_cur13` | KDIGO potassium report does not define it | `source_ids` → `reference_interval_convention` (precedent: C4c hypernatraemia in 15.2.0, R4 in 15.0.0); limitation recorded | < 1.2 mg/dL is a severity convention, not a guideline criterion; no guideline text defining it was retrieved |
| `hyperprolactinemia_pituitary_2023_prolactin_elevated_cur13` | consensus defers to assay-specific ranges; 25 ng/mL not stated | `source_ids` → `reference_interval_convention`; limitation recorded | 25 ng/mL is the usual female upper reference limit; the cited consensus does not state it |
| `septic_shock_severe_lactic_acidosis_sepsis3_lactate_4_cur13` | Sepsis-3 uses > 2 mmol/L; > 4 is not in the cited source | status `retired_v15_3_0_discordant_source`, executable = false | single-analyte assertion of septic shock from lactate alone, with a threshold absent from its source; the 15.0.0 R2a principle (no syndrome from one nonspecific marker) applies; no verifiable replacement source retrieved |
| `acquired_hemophilia_a_reanchor_scre_v13_4` | cited BSH rare-factor guideline excludes FVIII deficiency | status `retired_v15_3_0_discordant_source`, executable = false | FVIII < 40 % alone does not distinguish acquired from congenital haemophilia A or von Willebrand disease; the matching BSH acquired-haemophilia guideline was not retrievable in this session, so no source is attached from memory |

## D2 — boundary discordances recorded in Note 15 (2 rules)

| rule | finding | state in 15.2.0 | action |
|---|---|---|---|
| `rhabdomyolysis_ck_5x_uln_diagnostic_cur13` | source "> 1000", rule ">= 1000" (14.2.0 text) | already `> 1000` (15.0.0 R5) | none; ledger label → `discordant_corrected` |
| `prediabetes_hba1c_pattern_screening_1_v1` | source range 5.7–6.4 % inclusive; rule had no upper bound | 15.0.0 R5 protocol promised `>= 5.7 and <= 6.4` but `patch_15_0_0.py` l.351 only changed the operator — **the upper bound was never written** | expression → `all[ A1c >= 5.7 %, A1c <= 6.4 % ]` (quote already in `provenance.verified_quote`); the 15.0.0 implementation gap is recorded in `review_15_3_0.json` |

## D3 — open static-detector flags (5 rules): inspected, no change

| rule | flag | decision |
|---|---|---|
| `acute_kidney_injury_kdigo_2012_creatinine_absolute_cur13` | r2a single ubiquitous analyte | kept deliberately in 15.0.0 as the KDIGO absolute-creatinine surrogate (see PROTOCOL_15_0_0); accepted exception, recorded |
| `hyperosmolar_hyperglycemic_state_…_ketoacidosis_exclusion_cur13` | src scope endocrine vs domain critical_care | ADA/EASD 2024 hyperglycaemic-crises consensus is the correct source; the mismatch is between the entity's domain tag and the source scope list, not a rule error |
| `isoniazid_hepatotoxicity_dx_p131` | src scope liver vs toxicology_tdm | ATS 2006 hepatotoxicity statement is the correct source; same domain-tag mismatch |
| `lactic_acidosis_lactate_4_acidemia_cur13` | src scope critical_care vs diabetes_metabolic | rule requires lactate ≥ 4 **and** acidaemia; source scope mismatch only. Noted: Sepsis-3 does not define lactic acidosis; the rule stays flagged (`flagged_open`) rather than being re-sourced from memory |
| `urea_cycle_disorder_otc_deficiency_nh3_diagnostic_v1` | src scope genetics vs critical_care | ACMG ACT sheet is the correct source type; domain-tag mismatch |

## L — per-rule ledger label

For each of the 605 ledger rules, `provenance.ledger_15_3_0 = {"status": <label>, "built_from": "registry 15.2.0 ledger"}`
with the label updated for the D1/D2 actions above: `quote_verified` for the two re-sourced rules, `retired` for the two
retirements, `discordant_corrected` for prediabetes and rhabdomyolysis, and `convention_unverified` (a label added here,
meaning "threshold is a stated convention with no guideline text") for the two rules moved to
`reference_interval_convention`. The engine does not read this field.

## Expected touched counts (asserted by the patch)
D1 re-sourced 2, D1 convention 2, D1 retired 2, D2 changed 1, L labelled 605. Nothing else moves.
