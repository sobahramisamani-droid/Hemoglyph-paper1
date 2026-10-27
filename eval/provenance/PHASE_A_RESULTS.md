# Phase A — activity log of the shipped registry (14.2.0, engine v8.2), label-free

Cases: eicu 2314, nhanes_I 500, nhanes_J 1000

| Set | rules | share of 33,183 | anchors in set |
|---|---|---|---|
| active_core | 364 | 1.1 % | 46 |
| hot_core | 174 | 0.5 % | 32 |
| fired_not_contributing | 1627 | 4.9 % | 3 |
| dormant | 31192 | 94.0 % | 223 |

Anchors: 272 total; 46 in active core; 32 in hot core; 223 dormant.
Active core spans 258 disease ids; rule types: {'diagnostic_criterion': 158, 'screening': 141, 'staging_severity': 65}

Provenance class (first cited source) by set:
| class | all executable | active core | hot core | dormant |
|---|---|---|---|---|
| doi_resolved | 258 (0.8 %) | 38 (10.4 %) | 24 (13.8 %) | 215 (0.7 %) |
| generic_landing_page | 30104 (90.7 %) | 199 (54.7 %) | 72 (41.4 %) | 28860 (92.5 %) |
| landing_page | 2202 (6.6 %) | 69 (19.0 %) | 45 (25.9 %) | 1736 (5.6 %) |
| no_locator | 93 (0.3 %) | 10 (2.7 %) | 4 (2.3 %) | 49 (0.2 %) |
| other | 5 (0.0 %) | 4 (1.1 %) | 4 (2.3 %) | 1 (0.0 %) |
| unreachable | 518 (1.6 %) | 44 (12.1 %) | 25 (14.4 %) | 328 (1.1 %) |
| verified_manual | 3 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 3 (0.0 %) |

Most-cited sources in the active core: who_essential_lab_2024 (107); who_anaemia_2024 (19); acmg_act_2024 (17); esc_hf_2023 (12); ada_2026 (10); endocrine_guidelines (10); acg_crohn_2018 (8); endocrine_society_hypopituitarism_2016 (7); acmt_toxic_alcohols_2024 (7); tietz_7e_2023 (6); idsa_guidelines (6); aace_diabetes_2024 (6); bsh_hematology_2024 (5); surviving_sepsis_2024 (5); kdigo_ckd_2024 (5)

Most-cited sources in the hot core: who_essential_lab_2024 (30); ada_2026 (9); acmg_act_2024 (9); who_anaemia_2024 (9); esc_hf_2023 (8); endocrine_guidelines (6); kdigo_ckd_2024 (5); ssc_2026 (4); aace_diabetes_2024 (4); surviving_sepsis_2024 (4); tietz_7e_2023 (4); acg_crohn_2018 (3); idsa_guidelines (3); gold_copd_2024 (3); acmt_toxic_alcohols_2024 (3)

Registered expectations: core 800-4,000; anchors >= 30 % of hot core; see PROTOCOL.md.

## Registry composition (found while classifying the core; registry 14.2.0, executable rules)
| entity kind of the attached disease | executable rules | entities |
|---|---|---|
| biomarker_pattern (`co_*` two-analyte co-occurrence templates; all cite `who_essential_lab_2024`) | 24,293 (73.2 %) | 4,026 |
| clinical_entity | 4,265 | 1,383 |
| laboratory_finding | 2,918 | 753 |
| allergy | 736 | 184 |
| drug_level | 488 | 143 |
| serology_state | 432 | 222 |
| other/none | 51 | 45 |

In the active core: 105/364 rules are `co_*` templates (contrib10 sum 929, contrib5 sum 137); a `co_*` entity sat in the frozen v7 top-5 in 62/2,314 eICU stays (2.7 %).
Non-template active core: 259 rules; hot core 174 rules of which 28 templates.
Of the 200 rules in the Note 8 audit sample, 39 (all in stratum B2) were `co_*` templates and all were UNRESOLVABLE; the other 161 rules were 1 CONCORDANT / 15 DISCORDANT / 145 UNRESOLVABLE.

## Phase B — automated locator search over the active core (resource_core.py; sources fetched via registry URL, Europe PMC full text for DOIs, PubMed abstract fallback)
| outcome | rules |
|---|---|
| number_absent | 150 |
| generic_landing | 120 |
| unreachable | 63 |
| number_only | 17 |
| no_locator | 6 |
| statement_found_partial | 4 |
| statement_abstract | 2 |
| statement_found | 2 |

Reading: the registry's own locators lead to a document containing the rule's threshold for 8 of 364 active rules (2 full statements, 4 partial for multi-leaf rules, 2 abstract-level); 120 point to organisation landing pages, 63 are blocked from the sandbox (who.int, acmg.net, diabetesjournals, escardio, acc.org, easl.eu), 150 reach a page that does not contain the threshold (100 of them the CLSI EP28 shop page cited as second source by template rules), 17 contain the number without the analyte term, 6 cite nothing.
Registered expectation 'core 800-4,000' not met (364); 'anchors >= 30 % of hot core' not met (32/174 = 18 %); 'Phase B reachable-with-statement 30-60 %' not met (2 %).
