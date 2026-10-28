# Registry 15.1.0 — gate results (2026-10-28)

Protocol `eval/registry_patches/PROTOCOL_15_0_0.md` (applied unchanged); patch `patch_15_1_0.py`; review `REVIEW_15_1_0.md` / `review_15_1_0.json`. Same engine (v8.2, `analyse_gidlines.py`, unchanged) for both arms; only the registry differs (control = `release/registry_15.0.0/`, loaded through `HEMOGLYPH_REGISTRY_OVERRIDE` / `--registry`). v7 and registry 14.1.0 (paper) untouched; the Phase A activity file `eval/provenance/activity_eicu.json.gz` is unchanged (SHA-256 86f7aaaa…).

## 1. What changed in the registry

| | 15.0.0 | 15.1.0 |
|---|---:|---:|
| total rules | 34,673 | 34,673 |
| executable rules | 32,905 | 31,070 |
| retired in this release | — | 1,835 (R7 1,217 arithmetic tiers; R2a-wide 585 single ubiquitous analyte on a clinical entity; R8 30 placeholder entities; R9 3 impossible thresholds) |
| thresholds changed / rules added / sources changed | — | 0 / 0 / 0 |
| source records | 792 | 792 |

All four classes are defined by the rule text (see REVIEW §2); the allow-list (real cut-offs that coincide with the arithmetic) and keep-list (entity-defining single analytes) were fixed before the patch ran.

## 2. Gate 1 — unit tests and batteries

| check | 15.0.0 | 15.1.0 |
|---|---|---|
| pytest `tests/` | 709 passed, 9 skipped | **709 passed, 9 skipped** (first pass clean) |
| hard battery 1 | 151/151 | 151/151 |
| hard battery 2 | 124/124 | 124/124 |
| hard battery 3 | 77/78 (Alcoholic pancreatitis rank 2) | 77/78 (same pre-existing case) |
| healthy sweep n=200 | 0 syndrome false-fires, 0 dx ≥ 0.5 | 0 / 0 (worst p = 0.45, hypercholesterolaemia #15, unchanged) |

## 3. Gate 2 — eICU-CRD demo, labs only, `--encounter icu`, 2,314 stays, 2,432 coded labels

| metric | 15.0.0 | 15.1.0 | Δ |
|---|---|---|---:|
| flat recall@3 | 48.0 % (1167/2432) | 48.0 % (1167/2432) | 0 |
| flat recall@5 | 61.2 % (1488/2432) | 61.2 % (1488/2432) | 0 |
| flat recall@10 | 74.3 % (1807/2432) | 74.3 % (1807/2432) | 0 |
| two-tier recall@1 / @3 / @5 | 33.3 / 62.3 / 72.5 % | 33.3 / 62.3 / 72.5 % | 0 |
| grouped recall@1 / @3 / @5 / @10 | 29.0 / 54.9 / 67.1 / 77.9 % | identical | 0 |
| mean AUROC, 24 lab-detectable groups | 0.766 | 0.766 | 0 |

Paired stay×label analysis (`eval/results/gate_15_1_0/paired.py`): **0 gained, 0 lost at every k, flat and grouped.** Only 2 of 2,314 stays have a different top-5 (one 5th slot `folate_deficiency` → `bacterial_infection`; one probability 0.143 → 0.134). Template `co_*` slots in the top-5: 88/11,020 in both arms; distinct entities in any top-5 166 → 165.

**Reading.** 1,835 rules (5.6 % of the executable set, 303 + 201 + 30 of which had fired on this corpus) were removed without moving a single benchmark hit. That is the expected signature of the classes retired: low-weight `candidate` votes that pile onto entities the engine already ranks by its curated/anchored rules, or onto entities that never reach the differential. It also means this gate cannot distinguish a correct retirement from a harmless one; the justification is the review record, not this table.

## 4. Gate 3 — NHANES 2017–18, 1,000 adults, `--encounter community`

| task | 15.0.0 AUROC | 15.1.0 AUROC |
|---|---:|---:|
| diabetes | 0.946 | 0.946 |
| diabetes (self-report only) | 0.915 | 0.915 |
| CKD (eGFR < 60 or ACR ≥ 30) | 0.959 | 0.959 |
| CKD self-report | 0.769 | 0.769 |
| anaemia (WHO) | 0.9725 | 0.9722 |
| iron deficiency (ferritin < 15) | 0.991 | 0.991 |
| hypercholesterolaemia | 0.898 | 0.898 |
| hyperuricaemia | 0.948 | 0.948 |
| ALT elevation | 0.856 | 0.856 |

False-assertion rate in guideline-healthy adults 0/51 in both arms; the healthy top-1 list is identical.

## 5. Gate 4 — activity log on the same 2,314 eICU panels

| set (eICU only) | 15.0.0 | 15.1.0 |
|---|---:|---:|
| executable | 32,905 | 31,070 |
| fired at least once | 1,555 | 1,046 |
| active core (contributed to a top-10 entity ≥ 1) | 193 | 192 |
| hot core (≥ 10) | 83 | 82 |
| curated anchors in active / hot core (same method both arms) | 37 / 26 | 37 / 26 |
| template `co_*` in active / hot core | 89 / 21 | 90 / 21 |

Rules that left the active core: `sepsis_screening_4_v1` (CRP > 10 → sepsis, contrib10 = 12; R2a) and `hemochromatosis_hereditary_hemochromatosis_hb_male_anemia_v1` (Hb < 13 → haemochromatosis, 1; R2a). One template rule entered with contrib10 = 1. Hot-core provenance classes: rule_text_verified 14, reference_interval_convention 20, locator_only 2, generated_template 21, other_unverified 25 (15.0.0: 14 / 20 / 2 / 21 / 23 + 3 source-verified-rule-not-checked; the latter label is folded into other_unverified here).

The fired-rule count fell by a third (1,555 → 1,046): the retired families were firing constantly (e.g. `decreased_eosinophils_percent_diagnostic_criterion_1_v1` 678 panels, the IDSA `*_staging_severity_1_v1` CRP/WBC/PCT tiers 390 each, `echinococcosis_exclusion_criterion_3_v1` 1,061 — a *normal* ALP cast as a positive vote) without ever reaching the top-10. They cost compute and explanation space, not accuracy.

## 6. Files

`release/registry_15.1.0/` (registry + SHA256SUMS + CHANGELOG_15_1_0.md); `eval/results/eicu_demo/{report,summary,per_stay}_r1500_icu|_r1510_icu.*`; `eval/results/nhanes_2017/{report,summary,per_subject}_r1500|_r1510.*`; `eval/results/gate_15_1_0/` (eICU/NHANES/activity logs, batteries, healthy, `paired.py`/`paired.txt`, `activity_eicu_r1510.json.gz`, `core_summary.json`).
