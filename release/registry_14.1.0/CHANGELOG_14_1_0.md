# Hemoglyph clinical registry 14.1.0 — CHANGELOG (2026-10-25)

Base: 14.0.0. SAP Amendment 14 (C5). See docstring of `eval/patches/registry_v14_1.py`.

## Added entities
- `myocardial_injury_acuity_undetermined`
- `post_streptococcal_glomerulonephritis`

## Added rules
- `masld_alt_above_acg_uln_male_with_cardiometabolic_v14`
- `masld_alt_above_acg_uln_female_with_cardiometabolic_v14`
- `masld_exclusion_viral_hepatitis_v14`
- `psgn_low_c3_haematuria_v14`
- `psgn_low_c3_haematuria_renal_impairment_v14`

## Retargeted rules (C10)
- `acute_myocardial_injury_udmi4_troponin_above_99th_v14` -> myocardial_injury_acuity_undetermined

## Sources added
- `aasld_masld_2023` (10.1097/HEP.0000000000000323)
- `acg_liver_chemistries_2017` (10.1038/ajg.2016.517)

## Executable rule-type counts
`{"screening": 10979, "diagnostic_criterion": 6140, "staging_severity": 9844, "exclusion_criterion": 6220}`
