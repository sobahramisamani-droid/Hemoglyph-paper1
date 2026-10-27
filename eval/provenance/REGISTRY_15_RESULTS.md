# Registry 15.0.0 — gate results (2026-10-27)

Protocol `eval/registry_patches/PROTOCOL_15_0_0.md`; patch `patch_15_0_0.py`; review `REVIEW_15_0_0.md` / `review_15_0_0.json`. Same engine (v8.2, `analyse_gidlines.py` at commit 12d7c25) for both arms; only the registry differs. v7 and registry 14.1.0 (paper) untouched.

## 1. What changed in the registry

| | 14.2.0 | 15.0.0 |
|---|---:|---:|
| total rules | 34,673 | 34,673 |
| executable rules | 33,183 | 32,905 |
| retired in this release | — | 278 (R2a 100+134, R2b 25, R2c 19) |
| template `co_*` rules re-attributed to `generated_pair_pattern` | 0 | 24,308 |
| rules with verbatim verified quote (`provenance.verified_quote`) | 0 | 37 (R3 37 incl. the AKI surrogate; R5 rules counted once) |
| rules attributed to `reference_interval_convention` | 0 | 36 as first source (19 formerly citing the Endocrine Society collection page, 17 formerly citing topic-mismatched documents) + 2 as second source |
| logic corrections (R5) | — | 6: child_anemia_who_2024_v2, iron_deficiency_anemia_v1, prediabetes_hba1c_pattern_screening_1_v1, fasting_hypoglycemia_authentic_criterion_v1, rhabdomyolysis_ck_5x_uln_diagnostic_cur13, euglycemic_diabetic_ketoacidosis_authentic_criterion_v1 |
| source records | 785 | 792 (7 added, 18 repaired) |

Protocol deviation (recorded in REVIEW §4): `acute_kidney_injury_v1` was not retired; the test gate showed the ESL layer depends on it. It is now labelled `single_panel_surrogate` with the KDIGO 2012 definition quote.

## 2. Gate 1 — unit tests and batteries

| check | 14.2.0 (gate_14_1_0 / last run) | 15.0.0 |
|---|---|---|
| pytest `tests/` | 705 passed | **709 passed, 9 skipped** (first pass: 6 failures, all AKI, caused by the planned retirement of `acute_kidney_injury_v1`; reversed as above; second pass clean) |
| hard battery 1 | 151/151 | 151/151 |
| hard battery 2 | 124/124 | 124/124 |
| hard battery 3 | 77/78 (Alcoholic pancreatitis rank 2) | 77/78 (same pre-existing case) |
| healthy sweep n=200 | 0 false fires | 0 syndrome false-fires, 0 dx ≥ 0.5 |

## 3. Gate 2 — eICU-CRD demo, labs only, `--encounter icu`, 2,314 stays, 2,432 coded labels

| metric | 14.2.0 | 15.0.0 | Δ pts |
|---|---|---|---:|
| flat recall@3 | 48.4 % (1178/2432) | 48.0 % (1167/2432) | -0.5 |
| flat recall@5 | 61.0 % (1484/2432) | 61.2 % (1488/2432) | +0.2 |
| flat recall@10 | 74.1 % (1801/2432) | 74.3 % (1807/2432) | +0.2 |
| two-tier recall@1 | 33.5 % (815/2432) | 33.3 % (809/2432) | -0.2 |
| two-tier recall@3 | 62.3 % (1514/2432) | 62.3 % (1515/2432) | +0.0 |
| two-tier recall@5 | 72.1 % (1753/2432) | 72.5 % (1762/2432) | +0.4 |
| grouped recall@1 | 30.2 % (735/2432) | 29.0 % (705/2432) | -1.2 |
| grouped recall@3 | 55.6 % (1352/2432) | 54.9 % (1334/2432) | -0.7 |
| grouped recall@5 | 67.3 % (1637/2432) | 67.1 % (1632/2432) | -0.2 |
| grouped recall@10 | 77.9 % (1894/2432) | 77.9 % (1895/2432) | +0.0 |

Chart support of confident outputs (p ≥ 0.7): 23.1 % of 4,818 vs 23.1 % of 4,822. Template `co_*` entities in the top-5: 72/11,075 vs 88/11,020 slots (0.65 % → 0.80 %; retiring disease-level single-marker rules leaves more slots to the untouched template layer — R1 changed only their provenance label, not their logic). Distinct entities appearing in any top-5: 186 → 166.

Paired stay×label changes (exact binomial sign test):

| level | gained | lost | p | groups driving the change |
|---|---:|---:|---:|---|
| flat@1 | +1 | −17 | <0.001 | renal_impairment −9, acute_kidney_injury −5, sepsis −2 |
| flat@3 | +2 | −13 | 0.007 | acute_kidney_injury −4, renal_impairment −4, diabetes −2 |
| flat@5 | +5 | −1 | 0.22 | diabetes +2 |
| flat@10 | +8 | −1 | 0.039 | chronic_kidney_disease +2 |
| grouped@1 | +4 | −34 | <0.001 | acute_kidney_injury −6, renal_impairment −6, sepsis −4, diabetes −3 |
| grouped@3 | +3 | −21 | <0.001 | acute_kidney_injury −5, sepsis −5, diabetes −4 |
| grouped@5 | +4 | −9 | 0.27 | sepsis −5, diabetes +3 |
| grouped@10 | +7 | −6 | 1.00 | — |

Per-group AUROC unchanged to two decimals except CKD 0.78 → 0.79; AKI recall 78.0 % both arms; mean AUROC over 24 groups 0.766 both arms.

**Reading.** The release is neutral at @5/@10 and costs 0.4–1.2 points at top-1/top-3, almost entirely in the renal and sepsis groups. The lost renal top-1 hits come from `acute_kidney_injury_v1_f13_3` (creatinine > 1.1 / 1.02, thresholds traceable to no source; contrib10 = 308 in the 14.2.0 activity log) and from retired sepsis/leukocytosis tiers with unsourced thresholds (WBC > 16.5, lactate > 3.3, CRP > 15). Under the standing rule—fidelity changes are decided from the rule text and its source, never from benchmark labels—these rules are not reinstated. The numbers are reported as they are.

## 4. Gate 3 — NHANES 2017–18, 1,000 adults, `--encounter community`

| task | 14.2.0 AUROC | 15.0.0 AUROC |
|---|---:|---:|
| diabetes | 0.946 | 0.946 |
| diabetes (self-report only) | 0.915 | 0.915 |
| CKD (eGFR < 60 or ACR ≥ 30) | 0.971 | 0.959 |
| CKD self-report | 0.768 | 0.769 |
| anaemia (WHO) | 0.972 | 0.972 |
| iron deficiency (ferritin < 15) | 0.991 | 0.991 |
| hypercholesterolaemia | 0.898 | 0.898 |
| hyperuricaemia | 0.948 | 0.948 |
| ALT elevation | 0.856 | 0.856 |

Within the pre-registered 0.03 band (largest change CKD −0.012, from the retired `acute_kidney_injury_v1_f13_3`). False-assertion rate in guideline-healthy adults 0/51 both arms; `mcardle_disease` (CK-only rule, R2a) no longer appears among healthy participants' top-1 outputs.

## 5. Gate 4 — activity log on the same 2,314 eICU panels

| set (eICU only) | 14.2.0 | 15.0.0 |
|---|---:|---:|
| executable | 33,183 | 32,905 |
| fired at least once | 1,743 | 1,555 |
| active core (contributed to a top-10 entity ≥ 1) | 293 | 193 |
| hot core (≥ 10) | 120 | 83 |
| curated anchors in active core | 38 | 41 |
| template `co_*` in active / hot core | 85 / 19 | 89 / 21 |

Provenance class of the hot core after the release (first cited source; 15.0.0 labels applied to both arms so the columns are comparable):

| class | 14.2.0 hot core | 15.0.0 hot core |
|---|---:|---:|
| rule_text_verified | 15 | 14 |
| source_text_verified_rule_not_checked | 6 | 3 |
| locator_only | 2 | 2 |
| reference_interval_convention | 19 | 20 |
| generated_template | 19 | 21 |
| other_unverified | 59 | 23 |

Of the 201 retired rules that had fired in the 14.2.0 run, 119 were in the eICU active core and 44 in the hot core (top: `acute_kidney_injury_v1_f13_3` 308, `acute_myocardial_infarction_urgent_v1` 211, `hypercapnia_pattern_diagnostic_criterion_1_v1` 193, `sepsis_staging_severity_3_v1` 171, `sepsis_screening_3_v1` 138, `frailty_older_v2` 130, `heart_failure_staging_severity_2_v1` 126). The 'other_unverified' share of the hot core fell from 59/120 to 23/83; rules whose threshold is now backed by a verbatim quote or an explicit convention record are 34/83.

## 6. Files

`release/registry_15.0.0/` (registry + SHA256SUMS + CHANGELOG_15_0_0.md); `eval/results/eicu_demo/{report,summary,per_stay}_r142_icu|_r150_icu.*`; `eval/results/nhanes_2017/{report,summary,per_subject}_r142|_r150.*`; `eval/results/gate_15_0_0/` (pytest/batteries/healthy logs, `activity_eicu_r142|r150.json.gz`, `core_summary.json`). The Phase A files under `eval/provenance/` (paper) are unchanged (`activity_eicu.json.gz` SHA-256 86f7aaaa…).
