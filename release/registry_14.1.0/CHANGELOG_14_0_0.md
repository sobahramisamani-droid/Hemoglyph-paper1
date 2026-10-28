# Hemoglyph clinical registry 14.0.0 — CHANGELOG (2026-10-24)

Base: 13.4.2. SAP Amendment 14 (C1–C3). See docstring of `eval/patches/registry_v14_0.py`.

## Added entities
- `systemic_inflammatory_response_syndrome`
- `quick_sofa_positive`
- `septic_shock`
- `reduced_gfr_chronicity_undetermined`

## Added rules
- `sirs_accp_sccm_1992_2_of_4_v14`
- `qsofa_sepsis3_rr_sbp_v14`
- `septic_shock_sepsis3_map_lactate_pattern_v14`
- `septic_shock_sbp_lactate_screen_v14`
- `sepsis_sirs_with_laboratory_support_v14`
- `sepsis_qsofa_physiological_screen_v14`
- `acute_myocardial_injury_udmi4_troponin_above_99th_v14`
- `reduced_gfr_single_panel_v14`
- `chronic_kidney_disease_chronicity_clues_v14`

## Demoted (diagnostic_criterion → screening)
- `acute_myocardial_infarction_esc_2023_hs_tni_rule_in_cur13` {'rule_type': 'diagnostic_criterion', 'weight': 6.0} → {'rule_type': 'screening', 'weight': 3.0}
- `acute_myocardial_infarction_esc_2023_hs_tnt_rule_in_cur13` {'rule_type': 'diagnostic_criterion', 'weight': 6.0} → {'rule_type': 'screening', 'weight': 3.0}
- `chronic_kidney_disease_kdigo_2024_g3_plus_cur13` {'rule_type': 'diagnostic_criterion', 'weight': 6.0} → {'rule_type': 'screening', 'weight': 3.0}
- `acute_kidney_injury_v1` {'rule_type': 'diagnostic_criterion', 'weight': 6.0} → {'rule_type': 'screening', 'weight': 4.0}

## Retired
- `acute_myocardial_injury_v1`

## Sources added
- `udmi4_2018` (10.1093/eurheartj/ehy462)
- `accp_sccm_sirs_1992` (10.1378/chest.101.6.1644)

## Executable rule-type counts
`{"screening": 10975, "diagnostic_criterion": 6140, "staging_severity": 9844, "exclusion_criterion": 6219}`
