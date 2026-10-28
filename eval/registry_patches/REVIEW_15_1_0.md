# Registry 15.1.0 — review record

Protocol: `PROTOCOL_15_0_0.md` (unchanged). Patch: `patch_15_1_0.py` (`--dry-run` reproduces the classification without writing). Machine-readable log: `review_15_1_0.json` (rule_id → class, reason). Date 2026-10-28.

## 1. How the scope was built

Rules were selected for review by a property of the registry alone: executable, non-template (`co_*` excluded), status `candidate_*`, no `provenance.verified_quote`. Within that set four textual patterns were tested mechanically; every hit was then inspected by family (source, analyte, threshold) and the exceptions below were written down before the patch ran. No benchmark label or output ranking was consulted when deciding a class.

## 2. Counts by class

| Class | Rules | Definition (checkable from the rule text) |
|---|---:|---|
| R7 | 1217 | `staging_severity`/`diagnostic_criterion` rule whose every threshold = 1.5× or 0.5× of the same entity's own screening threshold for the same analyte; not on the published-cut-off allow-list |
| R2a-wide | 585 | clinical entity (not a finding), whole expression = one ubiquitous analyte; not on the keep-list |
| R8 | 30 | placeholder entity `uptodate_condition_NN` |
| R9 | 3 | impossible threshold (analyte `< 0`) |
| total | 1835 | executable 32,905 → 31,070 |

## 3. R7 — the arithmetic-tier family

The most common (analyte, tier, screening) triples make the mechanism visible:

| analyte | tier threshold | = factor × screening | rules |
|---|---:|---|---:|
| c_reactive_protein | > 15.0 | 1.5 × 10 | 35 |
| aspartate_aminotransferase | > 60.0 | 1.5 × 40 | 22 |
| lactate_dehydrogenase | > 420.0 | 1.5 × 280 | 22 |
| eosinophil_count_absolute | > 0.75 | 1.5 × 0.5 | 21 |
| white_blood_cell_count | > 16.5 | 1.5 × 11 | 18 |
| hemoglobin | < 6.5 | 0.5 × 13 | 17 |
| procalcitonin | > 0.75 | 1.5 × 0.5 | 16 |
| erythrocyte_sedimentation_rate | > 22.5 | 1.5 × 15 | 13 |
| cerebrospinal_fluid_total_protein | > 67.5 | 1.5 × 45 | 12 |
| creatinine | > 1.95 | 1.5 × 1.3 | 10 |
| platelets | < 75.0 | 0.5 × 150 | 9 |
| carcinoembryonic_antigen | > 7.5 | 1.5 × 5 | 8 |
| urine_rbc_count | > 3.0 | 1.5 × 2 | 8 |
| alanine_aminotransferase | > 75.0 | 1.5 × 50 | 7 |
| calcium_total | > 15.75 | 1.5 × 10.5 | 7 |
| squamous_cell_carcinoma_antigen | > 2.25 | 1.5 × 1.5 | 6 |
| cerebrospinal_fluid_white_blood_cells | > 7.5 | 1.5 × 5 | 6 |
| n_terminal_pro_bnp | > 450.0 | 1.5 × 300 | 5 |
| urine_wbc_count | > 7.5 | 1.5 × 5 | 5 |
| lymphocyte_count_absolute | < 0.5 | 0.5 × 1 | 5 |
| total_bilirubin | > 1.8 | 1.5 × 1.2 | 5 |
| thyroid_stimulating_hormone | > 6.0 | 1.5 × 4 | 5 |
| ca_19_9 | > 55.5 | 1.5 × 37 | 4 |
| ca_125 | > 52.5 | 1.5 × 35 | 4 |
| neuron_specific_enolase | > 24.0 | 1.5 × 16 | 4 |

Entity kinds: {'clinical_entity': 444, 'laboratory_finding': 700, 'drug_level': 73}. First sources: `who_essential_lab_2024` 772, `idsa_guidelines` 96, `acmg_act_2024` 48, `nccn` 40, `acr_eular_sle_2024` 21, `efns_myasthenia_2024` 11, `bsh_hematology_2024` 9, `kdigo_glomerular_2021` 9.

Allow-list (kept even when the arithmetic matches): eGFR 45/30/15; faecal elastase 100; UPCR 0.3; ACR 300; Hb 8/7; platelets 100/50/20; ANC 1.0/0.5; lactate 4/2; K 6.0/2.5; Na 125/120; Ca 14/7; glucose 250/54; bilirubin 2/3; INR 1.5/5; albumin 3.0/2.5; CK 5000; ammonia 100; TSH 10/0.1; CRP 100; PCT 10/2/0.25; WBC 25; eosinophils 1.5; TG 500/880; LDL 190; HCO3 18/15; phosphate 1.0; Mg 1.0; urate 10; Hct 65; MCV 120; fibrinogen 150/100; pH 7.2/7.1. Each is a published cut-off the reviewer could name; the list is in the patch file.

## 4. R2a-wide — examples of what was retired

| rule | expression | why it cannot stand |
|---|---|---|
| `irritable_bowel_syndrome_staging_severity_2_v1` | c_reactive_protein < 0.0 | CRP < 0 is impossible (R9) |
| `diabetes_insipidus_central_fasting_glucose_diabetes` | fasting_plasma_glucose >= 126.0 | ADA diabetes criterion attached to diabetes insipidus — name confusion |
| `hemochromatosis_hereditary_hemochromatosis_transferrin_saturation_low_v1` | transferrin_saturation < 20.0 | haemochromatosis has HIGH transferrin saturation; rule votes on LOW |
| `echinococcosis_exclusion_criterion_3_v1` | alkaline_phosphatase <= 120.0 | a NORMAL ALP cast as a positive screening vote (weight 6) for echinococcosis |
| `thalassemia_trait_beta_thalassemia_trait_ferritin_iron_depletion_v1` | ferritin < 15.0 | ferritin < 15 defines iron deficiency, which thalassaemia trait is meant to be distinguished from |
| `acute_myeloid_leukemia_aml_hb_male_anemia` | hemoglobin < 13.0 | WHO anaemia cut-off cloned onto a specific leukaemia |
| `reactive_arthritis_screening_1_v1` | c_reactive_protein > 10.0 | CRP > 10 votes for one specific arthritis |
| `gestational_diabetes_screening_2_v1` | hemoglobin_a1c > 5.7 | A1c > 5.7 is not an ACOG GDM criterion |
| `adrenal_incidentaloma_staging_severity_1_v1` | cortisol_after_dexamethasone > 2.7 | K < 1.75 mmol/L is a multiplier artefact (3.5 × 0.5) |

Keep-list (single-analyte rules that ARE entity-defining, left untouched): `hereditary_hemochromatosis_c282y_screening_1_v1` (TSAT > 45 %), `familial_chylomicronemia_syndrome_existing_*` (TG > 880 / 1000 mg/dL), `tangier_disease_*` and `lcat_deficiency_*` (HDL-C < 10 / < 5 mg/dL), `malignant_hyperthermia_stage_p131` (CK > 20,000), `acute_hepatitis_screen_p131` (ALT > 200), `warfarin_over_anticoagulation_authentic_criterion_v1` (PT > 30 s), `sepsis_screening_1_v1` (PCT > 0.5). These remain `candidate` and unverified; they are kept because the analyte is the entity's defining measurement, not because they are proven.

## 5. Decided NOT to change (open items, in writing)

- 139 `_f13_3` sex-specific variants: thresholds derived in 13.3.0 from female reference limits (documented derivation `D1b`). Not an invented tier, not text-verified either. Left for the physician review.
- Single-analyte troponin / NT-proBNP / eGFR / ACR rules on cardiac and renal entities: organ-specific analytes; thresholds need text verification (ESC ACS 2023, KDIGO CKD 2024) that the sandbox could not retrieve. Left as `candidate`.
- Hb / platelet / ferritin clones attached to finding-type and biomarker-pattern entities (`iron_deficiency_without_anemia_thrombocytosis_mpn_screen_v1` etc.): outside the R2a definition (entity is itself a finding). Flagged, not retired.
- `acute_kidney_injury_v1`: unchanged surrogate (see 15.0.0 review §4).
- Of the 1,328 rules in the review scope (curated or eICU/NHANES-active, no verified quote), 568 fall in the classes above; 760 remain unverified — mostly reference-interval screening rules on finding entities (`who_essential_lab_2024` 77), curated Tietz/CLSI re-anchors (33), ESC ACS troponin (28), KDIGO CKD (28), ISTH (28). None of these was changed.

## 6. What this patch does not claim

Retirement is a statement about provenance, not about clinical truth: a retired rule may describe a real association (eosinophilia and helminths; anaemia and myeloma). What it lacks is a source that defines the entity by that analyte, and the registry's standing rule is that such a vote may not exist without one. Benchmark effects were measured after the decisions (see `eval/provenance/REGISTRY_15_1_RESULTS.md`) and would not have reversed any of them.
