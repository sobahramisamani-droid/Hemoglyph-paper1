# Supplementary Information — Hemoglyph Paper 1, revision R1 (2026-10-26)

*Companion to `Paper1_Hemoglyph_npj_EN_v7_R1` and `Paper1_Hemoglyph_SampleStyle_v7_R1`. Every table below is generated from a file in `eval/results/` named in its heading; the numbers are not retyped.*

Contents: Supplementary Note 1 (SAP and amendments) = `SAP_Hemoglyph_v1.md`; Note 2 (LLM protocol) = `LLM_COMPARISON_PROTOCOL.md`; Note 3 (fusion and Theory-of-Evidence algorithm) below; Table S1 (cohort flow) = `TABLE_S1_cohort_flow.md`; Tables S6–S12 below; Supplementary Figure S (historical LLM comparison) below; TRIPOD+AI checklist = `TRIPOD_AI_checklist_Hemoglyph.md`.

---

## Supplementary Note 3 — Fusion and Theory-of-Evidence layer, as implemented (`analyse_gidlines.py`, `tarkib_ensemble`, `_yager_binary_combine`, v7)

**Inputs.** For each candidate entity *D* the five layers return a vote in [0, 1] or abstain: rule engine *v_R* (abstains when < 0.05, because the rule layer reports support only, never refutation), Bayesian network *v_B*, fuzzy engine *v_F*, knowledge graph *v_G*, risk models *v_K*. Let *P* be the set of participating (non-abstaining) layers.

**Step 1 — weighted mean with a domain profile.** Weights *w_m* come from the entity's domain profile (Table N3-1); they are renormalised over *P* (*ŵ_m = w_m / Σ_{m∈P} w_m*). The weighted mean is *μ = Σ ŵ_m v_m*. The share of profile weight that spoke, *s = Σ_{m∈P} w_m / Σ_all w_m*, penalises thin evidence: *score₀ = μ · (0.60 + 0.40 s)*. For guideline-anchored entities with a rule vote *s ≥ 0.75*; for a met expert-syndrome constellation *s = 1*.

**Step 2 — conflict and confidence.** Conflict *c* = weighted mean absolute pairwise disagreement, *c = Σ_{i<j} ŵ_i ŵ_j |v_i − v_j| / Σ_{i<j} ŵ_i ŵ_j*. Confidence = (1 − *c*) if |*P*| > 1 else 0.4, multiplied by min(1, 0.45 + 0.2 |*P*|) and by (0.5 + 0.5 *r*), where *r* is the input-reliability factor (OCR confidence; 1 for structured input).

**Step 3 — discord shrinkage toward the sceptical cluster.** Soft sceptic membership *m_i = clip((μ − v_i)/0.15, 0, 1)*; sceptic weight *W = Σ ŵ_i m_i*; sceptic target *T = Σ v_i ŵ_i m_i / W*; shrink *λ = min(0.45, 0.45 · c · min(1, W/0.35))*; *score₁ = (1 − λ) score₀ + λ T*.

**Step 4 — floors.** If *v_R ≥ 0.70* (red-flag rule): *score ≥ 0.65 v_R*. Met expert constellation: *score ≥ 0.90 v_R*; anchor-strength (definitional) constellation: *score ≥ v_R*.

**Step 5 — mass assignment and reliability discounting (Shafer discounting).** Discount factor per layer *α_m = ρ_m · (0.5 + 0.5 r) · min(1, w_m^profile / w_m^default)*, with *ρ_m = min(0.95, w_m^default / 0.35)* (Table N3-1). If only one layer participates and the entity is not anchored, *α* is multiplied by 0.70 (single-source discount). On the binary frame Θ = {D, ¬D}: rule layer (one-sided evidence) *m(D) = α v_R, m(¬D) = 0, m(Θ) = 1 − α v_R*; every other layer *m(D) = α v, m(¬D) = α(1 − v), m(Θ) = 1 − α*.

**Step 6 — closed-form Yager combination.** With *n* masses (*d_i, n_i, t_i*): *q(D) = Π(d_i + t_i) − Π t_i*, *q(¬D) = Π(n_i + t_i) − Π t_i*, *q(Θ) = Π t_i*, conflict mass *K = 1 − q(D) − q(¬D) − q(Θ)*. Yager's rule assigns *K* to Θ instead of renormalising: *m(Θ) ← q(Θ) + K*. The closed form is used because a sequential pairwise Yager fold is not associative. Outputs: Belief = *m(D)*, Plausibility = *m(D) + m(Θ)*, ignorance = *m(Θ)*, conflict = *K*.

**Step 7 — evidence state.** `conflicting` if pairwise conflict *c ≥ 0.45*; else `supported` if Bel ≥ 0.5; else `refuted` if Pl ≤ 0.35; else `insufficient` if Pl − Bel ≥ 0.40; else `weak`. A met expert constellation that lands in conflicting/weak/insufficient is reported `supported`.

**Step 8 — ceilings and final score.** Single non-rule layer: *score ≤ (Bel + Pl)/2*. `insufficient` single-source non-anchored non-finding entity: *score ≤ 0.49* (below the 0.5 assertion point). Entities whose rules read only ubiquitous analytes: *score ≤ 0.35*. Finally *score_cal = score* if confidence ≥ 0.3, else *score · confidence/0.3* when score < 0.5 and *0.5 + (score − 0.5)·confidence* otherwise. **This final value is the rank score; it is not a probability** (calibration slope 0.25, main text Section on calibration). Ranking uses the rank score; Bel/Pl/state are displayed, not ranked.

**Table N3-1. Fusion weights, profiles and reliability.**

| profile (trigger domains) | rule | Bayesian | fuzzy | graph | risk |
|---|---:|---:|---:|---:|---:|
| default | 0.35 | 0.25 | 0.20 | 0.10 | 0.10 |
| toxicology (toxicology, TDM, poisoning) | 0.55 | 0.15 | 0.15 | 0.05 | 0.10 |
| critical (critical care, acid–base, blood gas, electrolyte, emergency) | 0.50 | 0.20 | 0.15 | 0.05 | 0.10 |
| autoimmune (autoimmune, rheumatology, immunology, vasculitis) | 0.30 | 0.20 | 0.20 | 0.25 | 0.05 |
| oncology (oncology, tumour markers, haematologic malignancy) | 0.30 | 0.35 | 0.15 | 0.15 | 0.05 |
| endocrine (endocrine, thyroid, adrenal, pituitary, reproductive) | 0.35 | 0.25 | 0.25 | 0.10 | 0.05 |
| cardiometabolic (cardiovascular, lipid, metabolic, diabetes) | 0.30 | 0.20 | 0.15 | 0.10 | 0.25 |
| reliability ρ_m = min(0.95, w/0.35) | 0.95 | 0.71 | 0.57 | 0.29 | 0.29 |

Constants: `RULE_ABSTAIN_BELOW` 0.05, `SCEPTIC_SOFTNESS` 0.15, `MAX_DISCORD_SHRINK` 0.45, `SINGLE_SOURCE_DISCOUNT` 0.70, `RED_FLAG_RULE_VOTE` 0.70, `RED_FLAG_FLOOR_FRACTION` 0.65, `GUIDELINE_ANCHOR_MIN_WEIGHT_SHARE` 0.75, `INSUFFICIENT_CEILING` 0.49, `NONSPECIFIC_ONLY_CEILING` 0.35. The weights were set by the first author a priori and never fitted; their influence is measured in Table 5 (uniform weights −1.4 points; Dempster instead of Yager −0.1) and Table S12.

**Table N3-2. The 27 cross-field consistency identities of the post-OCR solver (`ocr_consistency.py`, `CHECKS`).** Each identity is evaluated when all its analytes are present; a failed identity triggers a search for a single-field repair (decimal shift ×0.1–×1000, glyph confusions 1↔7, 0↔8, 5↔6, 3↔8, 6↔8, 2↔7, 4↔9, 0↔6, 1↔4, 6↔9) that is kept only if every identity involving that field then passes. The solver is structural (no data, no model) and acts only on the OCR path, not on the structured-input evaluations in this paper.

| # | identity | analytes |
|---|---|---|
| 1 | `mchc_identity` | hemoglobin, hematocrit, mean_corpuscular_hemoglobin_concentration |
| 2 | `mcv_identity` | hematocrit, red_blood_cell_count, mean_corpuscular_volume |
| 3 | `mch_identity` | hemoglobin, red_blood_cell_count, mean_corpuscular_hemoglobin |
| 4 | `rule_of_three` | hemoglobin, hematocrit |
| 5 | `differential_sum` | neutrophils_percent, lymphocytes_percent, monocytes_percent, eosinophils_percent, basophils_percent |
| 6 | `anc_identity` | white_blood_cell_count, neutrophils_percent, neutrophil_count_absolute |
| 7 | `alc_identity` | white_blood_cell_count, lymphocytes_percent, lymphocyte_count_absolute |
| 8 | `direct_le_total_bilirubin` | total_bilirubin, direct_bilirubin |
| 9 | `bilirubin_sum` | total_bilirubin, direct_bilirubin, indirect_bilirubin |
| 10 | `albumin_le_total_protein` | albumin, total_protein |
| 11 | `globulin_identity` | albumin, total_protein, globulin |
| 12 | `ldl_hdl_le_tc` | total_cholesterol, ldl_cholesterol_calculated, ldl_cholesterol_direct, hdl_cholesterol |
| 13 | `friedewald` | total_cholesterol, hdl_cholesterol, triglycerides, ldl_cholesterol_calculated, ldl_cholesterol_direct |
| 14 | `non_hdl_identity` | total_cholesterol, hdl_cholesterol, non_hdl_cholesterol |
| 15 | `urea_bun_ratio` | blood_urea_nitrogen, urea |
| 16 | `anion_gap` | sodium, chloride, bicarbonate, anion_gap, potassium |
| 17 | `tsat_identity` | serum_iron, total_iron_binding_capacity, transferrin_saturation |
| 18 | `egfr_creatinine_monotonic` | creatinine, egfr_ckd_epi_creatinine |
| 19 | `amc_identity` | white_blood_cell_count, monocytes_percent, monocyte_count_absolute |
| 20 | `aec_identity` | white_blood_cell_count, eosinophils_percent, eosinophil_count_absolute |
| 21 | `abc_identity` | white_blood_cell_count, basophils_percent, basophil_count_absolute |
| 22 | `ag_ratio_identity` | albumin, globulin, albumin_to_globulin_ratio |
| 23 | `vldl_identity` | triglycerides, vldl_cholesterol |
| 24 | `eag_identity` | hemoglobin_a1c, estimated_average_glucose |
| 25 | `corrected_calcium_identity` | calcium_total, albumin, corrected_calcium_for_serum_albumin |
| 26 | `transferrin_tibc` | transferrin, total_iron_binding_capacity |
| 27 | `ldl_direct_vs_calculated` | ldl_cholesterol_direct, ldl_cholesterol_calculated, triglycerides |

---

**Table N3-3. Ablation arm definitions (`eval/ablation/run_ablation.py`).**

| arm | exact change |
|---|---|
| no_bayesian / no_fuzzy / no_graph / no_risk | that layer's vote set to abstain in fusion (`HEMOGLYPH_DISABLE_LAYERS`) |
| no_rule | the rule_engine channel set to abstain; both registry rules and expert-syndrome constellations enter fusion through this channel, so this arm is a superset of no_esl |
| no_esl | expert syndrome layer returns no hits; registry rules intact |
| dempster | conflict mass renormalised (Dempster) instead of assigned to Θ (Yager) |
| uniform_w / w_rule_heavy / w_rule_light | weights and all profiles replaced as given in Table S12; reliability ρ recomputed from the new weights |
| no_shrink | MAX_DISCORD_SHRINK = 0 and SINGLE_SOURCE_DISCOUNT = 1 |
| anchor_only | registry with only the 272 curated anchor rules executable |
| no_unverified | 28 `unverified_source` rules non-executable |
| anchor_only_no_esl | 2 × 2 cell added in revision round 4: anchor-only registry **and** syndrome layer off (flat@5 48.2 %, Δ −12.6 (−14.5 to −10.6); two-tier@5 60.9 %; mean AUROC 0.708). Interaction: AI-drafted rules contribute 0.9 points with the syndrome layer present and 3.1 points without it; the syndrome layer contributes 9.5 points with the full registry and 11.7 with anchors only |

## Supplementary Table S6 — Calibration metrics, per group and pooled (engine v7, eICU demo; `reviewer_b5_b6_v7.md`)

| set | units | prev | calibration slope | calibration-in-the-large (intercept) | Brier (95% CI) | log-loss | AUROC |
|---|---:|---:|---:|---:|---|---:|---:|
| ALL pooled | 52689 | 0.046 | 0.25 | -2.50 | 0.117 (0.114–0.119) | 0.379 | 0.797 |
| renal_impairment | 2266 | 0.144 | 0.25 | -2.23 | 0.236 (0.224–0.247) | 0.727 | 0.777 |
| sepsis | 2215 | 0.130 | 0.13 | -1.28 | 0.171 (0.159–0.182) | 0.789 | 0.682 |
| diabetes | 2247 | 0.109 | 0.14 | -1.43 | 0.150 (0.142–0.158) | 0.572 | 0.692 |
| acute_kidney_injury | 2266 | 0.096 | 0.26 | -2.37 | 0.213 (0.204–0.223) | 0.621 | 0.774 |
| anemia | 2207 | 0.067 | 0.36 | -2.94 | 0.244 (0.235–0.254) | 0.662 | 0.782 |
| acute_myocardial_infarction | 668 | 0.126 | 0.23 | +nan | 0.492 (0.467–0.518) | 1.412 | 0.758 |
| hyperkalemia | 2244 | 0.022 | 0.49 | -1.68 | 0.029 (0.025–0.033) | 0.096 | 0.917 |

## Supplementary Table S6b — Cross-fitted isotonic recalibration and decision curves (`calibration_dca_v7.md`)

| set | n | prev | ECE raw | ECE isotonic (cross-fit) | Brier raw | Brier iso | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL groups pooled | 52689 | 0.046 | 0.162 | 0.003 | 0.117 | 0.040 | 0.797 |
| renal_impairment | 2266 | 0.144 | 0.289 | 0.031 | 0.236 | 0.105 | 0.777 |
| sepsis | 2215 | 0.130 | 0.183 | 0.025 | 0.171 | 0.105 | 0.682 |
| diabetes | 2247 | 0.109 | 0.201 | 0.024 | 0.150 | 0.093 | 0.692 |
| acute_kidney_injury | 2266 | 0.096 | 0.282 | 0.012 | 0.213 | 0.078 | 0.774 |
| anemia | 2207 | 0.067 | 0.349 | 0.016 | 0.244 | 0.056 | 0.782 |

| decile | raw p | obs | iso p | obs |
|---:|---:|---:|---:|---:|
| 1 | 0.00 | 0.01 | 0.01 | 0.02 |
| 2 | 0.00 | 0.01 | 0.01 | 0.01 |
| 3 | 0.00 | 0.01 | 0.01 | 0.01 |
| 4 | 0.00 | 0.02 | 0.01 | 0.01 |
| 5 | 0.00 | 0.02 | 0.01 | 0.01 |
| 6 | 0.00 | 0.01 | 0.01 | 0.01 |
| 7 | 0.10 | 0.03 | 0.02 | 0.03 |
| 8 | 0.43 | 0.05 | 0.05 | 0.05 |
| 9 | 0.60 | 0.08 | 0.08 | 0.08 |
| 10 | 0.80 | 0.22 | 0.23 | 0.22 |

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 10.6 | 10.4 | 9.9 | 0.0 |
| 0.10 | 7.9 | 9.1 | 4.9 | 0.0 |
| 0.15 | 4.9 | 7.5 | -0.7 | 0.0 |
| 0.20 | 1.5 | 5.5 | -7.0 | 0.0 |
| 0.25 | -2.2 | 3.4 | -14.2 | 0.0 |
| 0.30 | -6.6 | 0.4 | -22.3 | 0.0 |
| 0.40 | -17.4 | 0.2 | -42.7 | 0.0 |
| 0.50 | -14.3 | 0.3 | -71.2 | 0.0 |
| 0.60 | -25.8 | 0.2 | -114.0 | 0.0 |
| 0.70 | -43.8 | -0.1 | -185.4 | 0.0 |
| 0.80 | -41.4 | 0.0 | -328.1 | 0.0 |

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 6.5 | 8.5 | 8.5 | 0.0 |
| 0.10 | 4.9 | 4.9 | 3.4 | 0.0 |
| 0.15 | 3.3 | 4.0 | -2.3 | 0.0 |
| 0.20 | 1.4 | 2.9 | -8.7 | 0.0 |
| 0.25 | -0.7 | 1.6 | -15.9 | 0.0 |
| 0.30 | -2.9 | 1.2 | -24.2 | 0.0 |
| 0.40 | -8.7 | -0.1 | -44.9 | 0.0 |
| 0.50 | -8.7 | -0.2 | -73.9 | 0.0 |
| 0.60 | -15.8 | -0.5 | -117.4 | 0.0 |
| 0.70 | -28.2 | 0.0 | -189.8 | 0.0 |
| 0.80 | -17.7 | 0.0 | -334.8 | 0.0 |

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 6.0 | 6.0 | 6.3 | 0.0 |
| 0.10 | 2.9 | 3.6 | 1.1 | 0.0 |
| 0.15 | -0.6 | 2.7 | -4.8 | 0.0 |
| 0.20 | -4.5 | 1.6 | -11.3 | 0.0 |
| 0.25 | -8.4 | 0.6 | -18.7 | 0.0 |
| 0.30 | -10.7 | -0.2 | -27.2 | 0.0 |
| 0.40 | -12.2 | 0.0 | -48.4 | 0.0 |
| 0.50 | -5.7 | 0.0 | -78.1 | 0.0 |
| 0.60 | -8.5 | -0.1 | -122.6 | 0.0 |
| 0.70 | -3.7 | -0.1 | -196.8 | 0.0 |
| 0.80 | -0.1 | -0.2 | -345.3 | 0.0 |

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 6.2 | 6.5 | 4.9 | 0.0 |
| 0.10 | 3.4 | 5.0 | -0.4 | 0.0 |
| 0.15 | 0.2 | 3.4 | -6.3 | 0.0 |
| 0.20 | -3.3 | 1.6 | -13.0 | 0.0 |
| 0.25 | -7.2 | 0.3 | -20.5 | 0.0 |
| 0.30 | -11.7 | -0.3 | -29.1 | 0.0 |
| 0.40 | -22.7 | 0.0 | -50.6 | 0.0 |
| 0.50 | -18.1 | 0.0 | -80.8 | 0.0 |
| 0.60 | -27.4 | -0.1 | -125.9 | 0.0 |
| 0.70 | -38.0 | 0.0 | -201.3 | 0.0 |
| 0.80 | -13.7 | 0.0 | -351.9 | 0.0 |

| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |
|---:|---:|---:|---:|---:|
| 0.05 | 3.2 | 3.3 | 1.7 | 0.0 |
| 0.10 | -0.2 | 1.8 | -3.7 | 0.0 |
| 0.15 | -4.1 | 1.5 | -9.8 | 0.0 |
| 0.20 | -8.3 | 0.6 | -16.7 | 0.0 |
| 0.25 | -13.1 | 0.5 | -24.5 | 0.0 |
| 0.30 | -18.6 | 0.4 | -33.3 | 0.0 |
| 0.40 | -30.5 | 0.1 | -55.6 | 0.0 |
| 0.50 | -46.9 | -0.4 | -86.7 | 0.0 |
| 0.60 | -45.2 | 0.0 | -133.3 | 0.0 |
| 0.70 | -22.5 | 0.0 | -211.1 | 0.0 |
| 0.80 | -10.9 | 0.0 | -366.7 | 0.0 |

## Supplementary Table S6c — Multiplicity control (Holm, BH-FDR) and panel-size sensitivity (`reviewer_b5_b6_v7.md`)

### B6a Multiplicity control over per-group AUROC (H0: AUROC = 0.5; Mann–Whitney U, two-sided; Holm and BH-FDR at 0.05; label-level, exploratory)

| group | n coded | AUROC | raw p | Holm-adjusted | BH q | significant after BH |
|---|---:|---:|---:|---:|---:|---|
| renal_impairment | 326 | 0.777 | 4.39e-62 | 1.18e-60 | 4.24e-61 | yes |
| sepsis | 289 | 0.682 | 2.09e-31 | 3.98e-30 | 5.52e-31 | yes |
| diabetes | 246 | 0.692 | 5.28e-24 | 8.44e-23 | 1.09e-23 | yes |
| acute_kidney_injury | 218 | 0.774 | 3.14e-44 | 7.53e-43 | 1.52e-43 | yes |
| chronic_kidney_disease | 148 | 0.783 | 3.77e-39 | 8.30e-38 | 1.37e-38 | yes |
| anemia | 147 | 0.782 | 1.28e-31 | 2.57e-30 | 3.72e-31 | yes |
| gi_bleeding | 145 | 0.751 | 3.82e-25 | 6.88e-24 | 9.23e-25 | yes |
| diabetic_ketoacidosis | 107 | 0.855 | 1.19e-89 | 3.33e-88 | 1.72e-88 | yes |
| hyperglycemia | 96 | 0.699 | 1.28e-11 | 1.41e-10 | 1.96e-11 | yes |
| acute_myocardial_infarction | 84 | 0.758 | 1.32e-14 | 1.99e-13 | 2.56e-14 | yes |
| hypokalemia | 67 | 0.716 | 3.06e-24 | 5.21e-23 | 6.83e-24 | yes |
| heart_failure | 58 | 0.664 | 1.35e-04 | 5.42e-04 | 1.51e-04 | yes |
| leukocytosis | 57 | 0.729 | 7.85e-12 | 9.42e-11 | 1.26e-11 | yes |
| hyponatremia | 52 | 0.887 | 7.25e-41 | 1.67e-39 | 3.00e-40 | yes |
| metabolic_acidosis | 51 | 0.757 | 1.77e-13 | 2.30e-12 | 3.02e-13 | yes |
| hyperkalemia | 49 | 0.917 | 6.31e-90 | 1.83e-88 | 1.72e-88 | yes |
| thrombocytopenia | 40 | 0.889 | 1.03e-31 | 2.16e-30 | 3.32e-31 | yes |
| hypomagnesemia | 37 | 0.673 | 1.42e-06 | 9.95e-06 | 1.79e-06 | yes |
| alcohol_withdrawal | 33 | 0.652 | 5.67e-07 | 4.53e-06 | 7.47e-07 | yes |
| coagulopathy | 28 | 0.751 | 1.86e-11 | 1.86e-10 | 2.70e-11 | yes |
| cirrhosis_liver_failure | 25 | 0.865 | 4.79e-14 | 6.71e-13 | 8.69e-14 | yes |
| hypoglycemia | 21 | 0.641 | 1.28e-52 | 3.32e-51 | 9.25e-52 | yes |
| lactic_acidosis | 19 | 0.735 | 1.97e-06 | 1.18e-05 | 2.38e-06 | yes |
| acute_pancreatitis | 18 | 0.733 | 8.08e-06 | 4.04e-05 | 9.38e-06 | yes |
| malnutrition | 16 | 0.515 | 8.33e-01 | 8.33e-01 | 8.33e-01 | no |
| hypernatremia | 14 | 0.883 | 6.04e-49 | 1.51e-47 | 3.50e-48 | yes |
| rhabdomyolysis | 11 | 0.919 | 9.60e-09 | 8.64e-08 | 1.33e-08 | yes |
| hypocalcemia | 10 | 0.627 | 1.19e-01 | 2.37e-01 | 1.23e-01 | no |
| hypothyroidism | 10 | 0.684 | 1.37e-03 | 4.11e-03 | 1.47e-03 | yes |

27 of 29 groups remain significant after BH-FDR; all per-group comparisons other than the pre-specified primary (flat recall@5) are labelled exploratory in the manuscript.

### B6b Sensitivity of recall to the minimum number of analytes in the first panel

| minimum analytes (n_in) | stays | labels | flat @3 | flat @5 | flat @10 | two-tier @5 |
|---:|---:|---:|---:|---:|---:|---:|
| ≥ 8 | 2314 | 2432 | 47.9 | 60.8 | 74.1 | 71.9 |
| ≥ 10 | 2269 | 2401 | 47.6 | 60.7 | 74.0 | 71.8 |
| ≥ 12 | 2236 | 2389 | 47.4 | 60.6 | 73.9 | 71.7 |
| ≥ 16 | 2186 | 2349 | 47.3 | 60.5 | 73.9 | 71.8 |
| ≥ 20 | 2099 | 2294 | 47.1 | 60.5 | 74.0 | 71.9 |
| ≥ 25 | 1829 | 2090 | 46.2 | 59.8 | 73.6 | 71.4 |

Distribution of n_in: median 31, IQR 25–35, min 8, max 49. Stays with < 8 analytes (n = 198 of 2,512 adults) were excluded by the SAP; they cannot be re-included without re-running the cohort builder, and their labels are listed in Table S3.

## Supplementary Table S7 — Survey-weighted NHANES AUROCs (WTMEC2YR; PSU-in-stratum bootstrap; `nhanes_weighted_v7.md`)

| target | cycle | n (pos) | unweighted AUROC | weighted AUROC (95% PSU-bootstrap CI) | Δ | weighted sens / spec @0.5 |
|---|---|---|---|---|---|---|
| diabetes | J 2017–18 | 2996 (605) | 0.946 | 0.951 (0.937–0.966) | +0.005 | 69.5 / 99.5 |
| diabetes_selfreport | J 2017–18 | 2916 (460) | 0.919 | 0.932 (0.914–0.951) | +0.013 | 70.3 / 97.7 |
| ckd | J 2017–18 | 2952 (556) | 0.959 | 0.947 (0.934–0.961) | -0.012 | 76.0 / 99.1 |
| ckd_selfreport | J 2017–18 | 2843 (131) | 0.816 | 0.744 (0.693–0.794) | -0.072 | 51.8 / 90.2 |
| anemia | J 2017–18 | 3000 (306) | 0.972 | 0.981 (0.977–0.985) | +0.009 | 99.8 / 94.8 |
| iron_deficiency | J 2017–18 | 2990 (163) | 0.989 | 0.991 (0.988–0.993) | +0.001 | 95.4 / 97.5 |
| hypercholesterolemia | J 2017–18 | 2997 (306) | 0.905 | 0.901 (0.891–0.911) | -0.004 | 100.0 / 76.4 |
| hyperuricemia | J 2017–18 | 2999 (589) | 0.943 | 0.933 (0.915–0.951) | -0.009 | 86.7 / 100.0 |
| alt_elevation | J 2017–18 | 3000 (535) | 0.872 | 0.872 (0.854–0.891) | +0.000 | 26.9 / 97.9 |
| guideline-healthy adults, any disease asserted | J | 160 | 1/160 unweighted | weighted share 0.56% | | |
| diabetes | H 2013–14 | 2998 (483) | 0.938 | 0.939 (0.920–0.957) | +0.001 | 67.5 / 99.0 |
| diabetes_selfreport | H 2013–14 | 2908 (369) | 0.914 | 0.922 (0.900–0.944) | +0.008 | 67.9 / 97.6 |
| ckd | H 2013–14 | 2958 (497) | 0.968 | 0.967 (0.959–0.975) | -0.000 | 86.1 / 99.1 |
| ckd_selfreport | H 2013–14 | 2834 (101) | 0.748 | 0.733 (0.674–0.802) | -0.015 | 53.1 / 87.8 |
| anemia | H 2013–14 | 3000 (295) | 0.994 | 0.996 (0.994–0.998) | +0.002 | 100.0 / 99.2 |
| hypercholesterolemia | H 2013–14 | 3000 (312) | 0.884 | 0.882 (0.869–0.895) | -0.002 | 97.9 / 75.6 |
| hyperuricemia | H 2013–14 | 3000 (547) | 0.958 | 0.959 (0.949–0.968) | +0.001 | 91.7 / 100.0 |
| alt_elevation | H 2013–14 | 3000 (649) | 0.880 | 0.879 (0.866–0.892) | -0.001 | 24.3 / 99.2 |
| guideline-healthy adults, any disease asserted | H | 246 | 1/246 unweighted | weighted share 0.77% | | |
| diabetes | I 2015–16 | 2999 (563) | 0.924 | 0.923 (0.909–0.937) | -0.001 | 62.8 / 99.0 |
| diabetes_selfreport | I 2015–16 | 2934 (431) | 0.898 | 0.903 (0.885–0.922) | +0.006 | 66.8 / 97.1 |
| ckd | I 2015–16 | 2960 (478) | 0.962 | 0.958 (0.949–0.966) | -0.004 | 78.0 / 99.2 |
| ckd_selfreport | I 2015–16 | 2875 (116) | 0.799 | 0.805 (0.760–0.839) | +0.006 | 51.6 / 89.9 |
| anemia | I 2015–16 | 3000 (346) | 0.983 | 0.990 (0.987–0.992) | +0.007 | 100.0 / 97.2 |
| iron_deficiency | I 2015–16 | 783 (148) | 0.972 | 0.980 (0.974–0.986) | +0.008 | 90.3 / 97.0 |
| hypercholesterolemia | I 2015–16 | 2999 (322) | 0.886 | 0.872 (0.864–0.880) | -0.015 | 100.0 / 70.8 |
| hyperuricemia | I 2015–16 | 2999 (505) | 0.955 | 0.947 (0.933–0.961) | -0.008 | 89.4 / 100.0 |
| alt_elevation | I 2015–16 | 3000 (656) | 0.877 | 0.870 (0.851–0.886) | -0.007 | 19.0 / 99.0 |
| guideline-healthy adults, any disease asserted | I | 79 | 0/79 unweighted | weighted share 0.00% | | |

Design note: the 3,000 evaluated adults per cycle are a seeded random subsample of eligible MEC participants; weights act as relative weights within the subsample. Strata with a single sampled PSU are resampled as themselves. Domain estimation (subsetting) is approximated by weighting within the evaluated set.

## Supplementary Table S8 — Per-group calibration slope / intercept / Brier

See Table S6 (same file); per-group rows are the slope, calibration-in-the-large, Brier (95% cluster-bootstrap CI), log-loss and AUROC for the eight largest groups.

## Supplementary Table S9 — Label-mapping audit, 400 stays (100 + 300; `label_audit_n300.md`, `label_audit_n100.md`)

# Label-mapping audit, extension to 300 further stays (seed 11; disjoint from the first 100) — author adjudication

| item | value |
|---|---|
| stays / diagnosis strings | 300 / 1113 |
| regex-positive labels | 376 |
| regex false positives | **0** |
| definite misses | **7** |
| ambiguous (excluded) | 37 |
| precision | 100.0% | 
| sensitivity | 98.2% |

| group | TP | FP | FN | precision | sensitivity |
|---|---:|---:|---:|---:|---:|
| sepsis | 42 | 0 | 1 | 100% | 98% |
| diabetes | 42 | 0 | 0 | 100% | 100% |
| renal_impairment | 35 | 0 | 1 | 100% | 97% |
| heart_failure | 26 | 0 | 0 | 100% | 100% |
| anemia | 26 | 0 | 0 | 100% | 100% |
| acute_kidney_injury | 22 | 0 | 0 | 100% | 100% |
| hyperglycemia | 21 | 0 | 0 | 100% | 100% |
| gi_bleeding | 20 | 0 | 0 | 100% | 100% |
| diabetic_ketoacidosis | 18 | 0 | 0 | 100% | 100% |
| chronic_kidney_disease | 15 | 0 | 0 | 100% | 100% |
| leukocytosis | 8 | 0 | 2 | 100% | 80% |
| alcohol_withdrawal | 9 | 0 | 0 | 100% | 100% |
| acute_myocardial_infarction | 9 | 0 | 0 | 100% | 100% |
| hypokalemia | 9 | 0 | 0 | 100% | 100% |
| malnutrition | 7 | 0 | 2 | 100% | 78% |
| metabolic_acidosis | 8 | 0 | 0 | 100% | 100% |
| hyponatremia | 7 | 0 | 0 | 100% | 100% |
| hypothyroidism | 6 | 0 | 0 | 100% | 100% |
| thrombocytopenia | 5 | 0 | 0 | 100% | 100% |
| hypoglycemia | 5 | 0 | 0 | 100% | 100% |
| coagulopathy | 5 | 0 | 0 | 100% | 100% |
| acute_pancreatitis | 5 | 0 | 0 | 100% | 100% |
| cirrhosis_liver_failure | 4 | 0 | 1 | 100% | 80% |
| rhabdomyolysis | 4 | 0 | 0 | 100% | 100% |
| hyperkalemia | 4 | 0 | 0 | 100% | 100% |
| hypomagnesemia | 3 | 0 | 0 | 100% | 100% |
| lactic_acidosis | 3 | 0 | 0 | 100% | 100% |
| hypernatremia | 3 | 0 | 0 | 100% | 100% |
| hypocalcemia | 3 | 0 | 0 | 100% | 100% |
| hypophosphatemia | 2 | 0 | 0 | 100% | 100% |

Pooled with the first 100-stay audit (150 TP, 0 FP, 2 FN): precision 100.0%, sensitivity 98.3% over 400 stays.

Disagreement cells were generated by a deliberately over-inclusive keyword coder; only disagreeing cells were read (agreement on negatives assumed). Regex-positive cells were verified at the category level (every positive arises from the expected eICU category branch, e.g. `endocrine|glucose metabolism|…` for diabetes); they were not individually re-read, so precision is a category-level estimate. Adjudicator: first author (with AI-agent assistance); not an independent clinical audit.

Definite misses (7): `protein-calorie malnutrition` (2), `hematological effect of infection|leukocytosis` (2), `acute renal failure|due to sepsis` (1), `encephalopathy|hepatic` (1), `hypertension|with renal failure` (1). Ambiguous (37): DKA / hyperosmolar coma for the hyperglycaemia group (18), acute pulmonary oedema / cardiomyopathy for heart failure (6), acute coronary syndrome without infarction (5), `signs and symptoms of sepsis (SIRS)` (2), kidney transplant / `due to renal disease` (3), varices / acute hepatic dysfunction (2), `drug withdrawal syndrome` unspecified (1), diabetic foot infection (1). The label map is frozen; none of these patterns was changed.

## Supplementary Table S10 — Registry count reconciliation (computed from the shipped 14.1.0 file on 2026-10-26)

| quantity (release 14.1.0, live file) | value | note |
|---|---:|---|
| rule records | 34,673 | |
| status `candidate_requires_specialist_validation` | 32,901 | executable |
| status `retired_v13_3_0` | 1,139 | non-executable (retired) |
| status `curated_guideline_anchored` | 272 | executable |
| status `retired_v13_4_0_domain_artefact` | 171 | non-executable (retired) |
| status `retired_template_artifact` | 164 | non-executable (retired) |
| status `retired_v13_2_nonspecific_single_marker` | 9 | non-executable (retired) |
| status `curated_guideline_anchored_demoted_v13_4_2` | 9 | executable |
| status `curated_guideline_anchored_demoted_v14_0` | 4 | executable |
| status `retired_empty_expression` | 3 | non-executable (retired) |
| status `retired_v14_0` | 1 | non-executable (retired) |
| retired, total | 1,487 | manuscript v7 draft said 1,474 (omitted the 13 demoted anchors, which remain executable) |
| candidates lacking `executable` flag | 3 | counted in 32,901 in the draft; not executable |
| executable rules | 33,183 | = 272 anchors + 13 demoted anchors + 32,898 candidates |
| executable by evidence tier | tier_c: 27,885, tier_a: 2,937, tier_b: 2,278, None: 55, unverified_source: 28 | 55 executable rules carry no tier field |
| guideline sources listed | 785 | metadata field `total_sources` still reads 781 (stale, from 13.4.1) |
| sources cited by ≥ 1 executable rule | 388 | of the other 397: 3 are cited only by retired rules and 394 by no rule at all — background/general references (textbooks, CLSI documents, guideline overviews) imported into the source table during registry construction and retained for provenance; they contribute nothing to any output |
| disease records | 6,756 | metadata `total_diseases` reads 6,750; 6,528 diseases have ≥ 1 executable rule |

**Executable-rule flow across releases (computed from the archived registry files `*.bak_v13_1_0`, `*.bak_v13_3_0`, `*.bak_v13_4_2`, `*.bak_v14_0_0` and the live 14.1.0 file, 2026-10-26).** The near-constancy of the executable count (33,170–33,230) across 13.3.0–14.1.0 is not a coincidence of bookkeeping: it is the net of retirements and guideline-sourced additions.

| transition | records added | rules retired (executable → non-executable) | new executable rules | executable total after | sources |
|---|---:|---:|---:|---:|---:|
| 13.1.0 (baseline) | — | — | — | 34,005 | 747 |
| 13.1.0 → 13.3.0 | +373 | 1,135 | 360 | 33,230 | 747 |
| 13.3.0 → 13.4.2 | +111 | 171 | 111 | 33,170 | 781 |
| 13.4.2 → 14.0.0 | +9 | 1 | 9 | 33,178 | 783 |
| 14.0.0 → 14.1.0 | +5 | 0 | 5 | 33,183 | 785 |
| total since 13.1.0 | +498 | 1,307 | 485 | | |

No rule was re-activated after retirement; 170 records were already non-executable in 13.1.0 (164 template artefacts, 3 empty expressions, 3 un-flagged candidates), giving the 1,487 + 3 non-executable records of Table S10.

Earlier text quoted 1,474 retired records and 32,901 candidates (sum 33,199) and, elsewhere, 33,173; the discrepancies arose from mixing release-13.4.x counts with 14.1.0 counts and from counting the 13 demoted anchors and 3 non-executable candidates inconsistently. All manuscript counts now derive from this table.

## Supplementary Table S11 — Precision, F1, NDCG, alert burden, per-group PPV and prevalence-ranking baseline (`reviewer_r2_metrics_v7.md`; script `eval/reviewer_r2_metrics.py`)

Prediction set at k = label groups whose best flat-list entry has rank ≤ k and whose key analyte is present (the same evaluability rule used for recall). Reference = clinician problem list mapped to 31 groups (admission-level; incompleteness means 'false positives' are an upper bound on true false positives). CIs: stay-cluster bootstrap, 2,000 resamples.

| metric | k=3 | k=5 | k=10 |
|---|---:|---:|---:|
| engine v7 precision@k (%) | 16.5 (15.4–17.6) | 14.2 (13.3–15.2) | 11.8 (11.1–12.6) |
| engine v7 recall@k (%) | 47.9 (45.6–50.3) | 60.8 (58.5–63.0) | 74.1 (72.0–76.0) |
| engine v7 f1@k (%) | 24.6 (23.2–26.0) | 23.1 (21.8–24.3) | 20.4 (19.3–21.5) |
| engine v7 ndcg@k (%) | 53.1 (50.6–55.5) | 56.5 (54.1–58.8) | 60.6 (58.6–62.8) |
| prevalence-ranking baseline precision@k (%) | 12.6 | 10.8 | 8.1 |
| prevalence-ranking baseline recall@k (%) | 36.1 | 51.3 | 76.8 |
| prevalence-ranking baseline f1@k (%) | 18.7 | 17.8 | 14.7 |
| prevalence-ranking baseline ndcg@k (%) | 34.9 | 39.0 | 49.9 |
| engine: label-group assertions per stay | 3.04 | 4.49 | 6.57 |

Alert burden: mean 8.0 (median 8, IQR 5–11) label-group entries in the full flat differential (max list length 25); mean flat list carries 4.8 entries in the top-5.

### Per-group PPV and sensitivity at k = 5 (problem-list reference)

| group | coded (evaluable) | asserted@5 | PPV@5 (%) | sensitivity@5 (%) | prevalence baseline sens@5 (%) |
|---|---:|---:|---:|---:|---:|
| renal_impairment | 326 | 1066 | 25 | 81 | 100 |
| sepsis | 289 | 532 | 27 | 49 | 100 |
| diabetes | 246 | 611 | 18 | 45 | 100 |
| acute_kidney_injury | 218 | 947 | 18 | 78 | 100 |
| chronic_kidney_disease | 148 | 239 | 22 | 36 | 100 |
| anemia | 147 | 1141 | 11 | 83 | 7 |
| gi_bleeding | 145 | 1123 | 10 | 78 | 3 |
| diabetic_ketoacidosis | 107 | 98 | 69 | 64 | 3 |
| hyperglycemia | 96 | 611 | 7 | 47 | 0 |
| acute_myocardial_infarction | 84 | 436 | 17 | 88 | 1 |
| hypokalemia | 67 | 259 | 13 | 49 | 0 |
| heart_failure | 58 | 168 | 29 | 83 | 0 |
| leukocytosis | 57 | 597 | 4 | 40 | 2 |
| hyponatremia | 52 | 246 | 13 | 63 | 0 |
| metabolic_acidosis | 51 | 444 | 6 | 55 | 0 |
| hyperkalemia | 49 | 77 | 31 | 49 | 0 |
| thrombocytopenia | 40 | 300 | 9 | 65 | 2 |
| hypomagnesemia | 37 | 161 | 8 | 35 | 0 |
| alcohol_withdrawal | 33 | 90 | 12 | 33 | 0 |
| coagulopathy | 28 | 119 | 11 | 46 | 0 |
| cirrhosis_liver_failure | 25 | 187 | 8 | 60 | 0 |
| hypoglycemia | 21 | 13 | 38 | 24 | 0 |
| lactic_acidosis | 19 | 154 | 8 | 63 | 0 |
| acute_pancreatitis | 18 | 54 | 22 | 67 | 0 |
| malnutrition | 16 | 150 | 0 | 0 | 0 |
| hypernatremia | 14 | 49 | 16 | 57 | 0 |
| rhabdomyolysis | 11 | 43 | 14 | 55 | 0 |
| hypocalcemia | 10 | 359 | 0 | 10 | 0 |
| hypothyroidism | 10 | 26 | 12 | 30 | 0 |

Interpretation: PPV against an admission problem list is a lower bound (uncoded but present conditions count as false positives); it is reported to quantify alert burden, not accuracy.

### Criterion-supported precision at k = 5 (addendum 2026-10-26)

Of 10,380 label-group assertions in the top-5, 1,479 (14.2%) are on the problem list (= precision@5). Of the remaining 8,901: 5,684 (54.8% of all assertions) satisfy the group's fixed laboratory criterion in the same panel (laboratory-supported but uncoded), 1,309 (12.6%) do not satisfy it (criterion-negative: the closest thing to a verified false positive without a clinician), and 1,908 (18.4%) belong to groups without a single-analyte criterion or lack the criterion analyte.
Upper-bound precision (coded OR criterion-positive) = 69.0%; lower bound = 14.2%; criterion-negative share = 12.6%.

| group | asserted@5 | coded | uncoded, criterion-positive | uncoded, criterion-negative | no criterion / analyte |
|---|---:|---:|---:|---:|---:|
| anemia | 1141 | 122 | 961 | 58 | 0 |
| gi_bleeding | 1123 | 113 | 0 | 0 | 1010 |
| renal_impairment | 1066 | 265 | 541 | 260 | 0 |
| acute_kidney_injury | 947 | 169 | 556 | 222 | 0 |
| diabetes | 611 | 111 | 201 | 299 | 0 |
| hyperglycemia | 611 | 45 | 397 | 169 | 0 |
| leukocytosis | 597 | 23 | 574 | 0 | 0 |
| sepsis | 532 | 142 | 0 | 0 | 390 |
| metabolic_acidosis | 444 | 28 | 345 | 71 | 0 |
| acute_myocardial_infarction | 436 | 74 | 310 | 52 | 0 |
| hypocalcemia | 359 | 1 | 250 | 108 | 0 |
| thrombocytopenia | 300 | 26 | 274 | 0 | 0 |
| hypokalemia | 259 | 33 | 226 | 0 | 0 |
| hyponatremia | 246 | 33 | 213 | 0 | 0 |
| chronic_kidney_disease | 239 | 53 | 163 | 23 | 0 |
| cirrhosis_liver_failure | 187 | 15 | 0 | 0 | 172 |
| heart_failure | 168 | 48 | 112 | 8 | 0 |
| hypomagnesemia | 161 | 13 | 148 | 0 | 0 |
| lactic_acidosis | 154 | 12 | 139 | 3 | 0 |
| malnutrition | 150 | 0 | 0 | 0 | 150 |
| coagulopathy | 119 | 13 | 0 | 0 | 106 |
| diabetic_ketoacidosis | 98 | 68 | 13 | 16 | 1 |
| alcohol_withdrawal | 90 | 11 | 0 | 0 | 79 |
| hyperkalemia | 77 | 24 | 53 | 0 | 0 |
| hypophosphatemia | 62 | 2 | 60 | 0 | 0 |
| acute_pancreatitis | 54 | 12 | 41 | 1 | 0 |
| hypernatremia | 49 | 8 | 41 | 0 | 0 |
| rhabdomyolysis | 43 | 6 | 31 | 6 | 0 |

## Supplementary Table S12 — Fusion-weight sensitivity

Arms `uniform_w` (all five weights 0.20, all profiles), `w_rule_heavy` (0.55/0.15/0.15/0.075/0.075) and `w_rule_light` (0.20/0.30/0.25/0.125/0.125), run on the same 2,314 stays with the frozen engine file and environment switches only (`eval/ablation/run_ablation.py`). Stay-cluster bootstrap CIs (B = 4,000, seed 20261025).

| arm | weights (rule / Bayesian / fuzzy / graph / risk) | flat @3 | flat @5 | flat @10 | Δ@5 vs full (95% CI) | two-tier @5 | panel-supported @5 / @10 | stays with identical top-5 |
|---|---|---:|---:|---:|---|---:|---|---:|
| full (default profiles) | 0.35 / 0.25 / 0.20 / 0.10 / 0.10 + 6 domain profiles | 47.9 | 60.8 | 74.1 | — | 71.9 | 78.0 / 91.8 | 100% |
| uniform_w | 0.20 × 5, all profiles | 47.5 | 59.4 | 73.1 | −1.4 (−2.1 to −0.7) | 72.2 | 75.7 / 89.9 | 61% |
| w_rule_heavy | 0.55 / 0.15 / 0.15 / 0.075 / 0.075, all profiles | 48.2 | 60.8 | 74.0 | −0.0 (−0.6 to +0.5) | 71.8 | 77.9 / 91.8 | 65% |
| w_rule_light | 0.20 / 0.30 / 0.25 / 0.125 / 0.125, all profiles | 47.6 | 59.7 | 73.3 | −1.1 (−1.8 to −0.3) | 72.2 | 76.0 / 90.1 | 61% |

Reading: moving weight toward the rule layer changes nothing measurable; moving it away costs about one point of flat recall@5 while leaving two-tier recall unchanged. The headline is insensitive to the hand-set weights within this range, which is consistent with the layer ablation (rule vote −12.1, syndrome layer −9.5, every other layer ≤ 1.3 points). Files: `eval/results/eicu_demo/{report_abl_w_rule_heavy.md, report_abl_w_rule_light.md, ABLATION_v7_ci.md, ABLATION_v7_full.md}`; chain completed 2026-10-26 01:07 UTC.

## Supplementary Figure S — Historical LLM comparison against the superseded engine v5.1

![Fig S](../v7/fig/Fig6_llm_v51.png)

Same 400 stays and LLM outputs as the main-text comparison, scored against engine v5.1 (the release current when the LLM was run): recall@5 64.4% (engine) vs 59.6% (LLM). The main text reports the re-score against the frozen v7 (60.7% vs 59.6%), because v7 is the evaluated release; the historical figure is kept so that the change in the engine's number is visible.

## Supplementary Table S13 — Participant flow, UCI thyroid0387 and UCI HCV cohorts

| cohort | step | n |
|---|---|---:|
| UCI thyroid0387 | records with a clinician diagnosis string | 9,172 |
| | excluded: TSH not measured | −842 |
| | excluded: classes R (discordant assay) and I/J/S (binding-protein abnormalities, not interpretable from TSH/T4 alone) | −587 |
| | **scorable records** | **7,743** |
| | → no-comment controls (negative set for every task) | 6,082 |
| | → hypothyroid classes E/F/G/H (task H1 positives) | 655 |
| | → hyperthyroid classes A/B/C/D (task H2 positives) | 195 |
| | → other classes, not positives or negatives of any task: K concurrent non-thyroidal illness 433; L/M/N replacement therapy 329; O/P/Q antithyroid treatment / miscellaneous 33; mixed MK 16 | 811 |
| UCI HCV (Hoffmann 2018) | records | 615 |
| | blood donors (negative set) | 533 |
| | suspect blood donors — ambiguous label, excluded from both tasks | 7 |
| | hepatitis / fibrosis / cirrhosis (task A positives, 24 + 21 + 30) | 75 |
| | task B cirrhosis: positives 30; negatives = donors + hepatitis + fibrosis | 30 vs 578 |
| ILPD | liver patients / non-patients (no exclusions) | 416 / 167 |

## Supplementary Note 4 — Regression gate: definition and residual failures

**Definition (unchanged since release 13.4.1).** A candidate engine/registry pair may be used for any real-data run only if (i) all unit tests pass; (ii) in the three adversarial vignette batteries (151, 124, 78 cases; expected diagnosis must appear at or above a per-case maximum rank) no case that passed in the previous shipped release fails; (iii) in the perturbation battery (151 cases × 5 replicates of 3% multiplicative noise = 755 pairs) no new pair fails and no case becomes "brittle" (< 4/5 replicates) that was not already brittle; (iv) the 1,000-panel healthy sweep produces zero syndrome fires and zero diagnoses ≥ 0.5; (v) the SI/conventional unit-twin battery produces identical rankings. The gate is non-regression, not perfection; it was chosen so that a correctness change can never be accepted at the price of a previously correct case.

**Residual failures in the frozen v7 (both pre-date v7 and are deliberately unpatched).**

| battery | case | v7 | 14.1 | reason not patched |
|---|---|---|---|---|
| vignettes 3 (78) | alcoholic pancreatitis vignette — expected rank 1, obtained rank 2 behind *alcohol-use disorder* (both "supported", 0.79) | 77/78 | 77/78 | a rule written for this vignette would be outcome-fitting; the ranking is clinically defensible |
| perturbation (755) | thiazide-associated hypovolaemic hyponatraemia (five noisy replicates of one vignette): 3/5 replicates keep the expected rank in v7, 2/5 in release 14.1 — i.e. v7 recovered one replicate; the two residual failures are replicates 2 and 4 of this single vignette and there is no other failing perturbation pair | 753/755 | 752/755 | the case sits on the sodium/urate decision boundary; moving the boundary for it was tried during development and rejected because it over-fired elsewhere |

## Supplementary Table S4 — Subgroup recall, frozen engine v7 (eICU demo, 2,314 stays; replaces the v6-era figures 65.4 %/61.1 % quoted in the first submission)

### Source table (`eval/results/eicu_demo/subgroups_v7.md`): Subgroup and fairness analysis — eICU-CRD demo (n = 2314 stays), engine v7

Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.

Overall: recall@5 60.8%, recall@10 74.1%, chart support 23.2% (n = 4218), false-assertion proxy in stays with empty problem list 93.8% (n = 1136).

#### By sex

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| male | 1392 | 1498 | 62.3% (59.5–64.9) | 75.8% | 24.3% | 0.78 | 0.69 | 0.79 | 0.80 |
| female | 922 | 934 | 58.5% (54.4–62.3) | 71.2% | 21.4% | 0.77 | 0.67 | 0.77 | 0.73 |

#### By age band

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 65–79 | 820 | 844 | 60.1% (55.9–64.2) | 75.5% | 21.8% | 0.73 | 0.68 | 0.77 | 0.76 |
| 45–64 | 695 | 708 | 58.1% (54.0–62.6) | 70.6% | 22.5% | 0.84 | 0.70 | 0.77 | 0.81 |
| ≥80 | 426 | 476 | 63.9% (58.7–68.5) | 75.8% | 22.5% | 0.71 | 0.68 | 0.76 | 0.71 |
| <45 | 373 | 404 | 63.6% (58.7–68.6) | 75.0% | 28.8% | 0.81 | 0.68 | 0.82 | 0.80 |

#### By ethnicity

| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | AUROC renal impairment | AUROC sepsis | AUROC anemia | AUROC acute kidney injury |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Caucasian | 1839 | 1827 | 60.9% (58.1–63.4) | 73.2% | 22.8% | 0.77 | 0.66 | 0.77 | 0.77 |
| African American | 220 | 201 | 60.2% (50.8–68.4) | 75.6% | 18.6% | 0.74 | 0.73 | 0.81 | 0.68 |
| Hispanic | 111 | 216 | 59.3% (51.5–67.2) | 79.2% | 31.4% | 0.84 | 0.83 | 0.81 | 0.85 |
| Other/Unknown | 74 | 96 | 58.3% (45.1–69.9) | 71.9% | 24.5% | 0.80 | 0.79 | — | 0.84 |
| Unknown | 30 | 31 | 74.2% (54.8–89.8) | 80.6% | 29.5% | — | 0.85 | — | — |
| Asian | 28 | 34 | 64.7% (45.8–84.6) | 76.5% | 21.9% | 0.77 | 0.69 | — | 0.80 |
| Native American | 12 | 27 | 63.0% (nan–nan) | 77.8% | 53.3% | — | — | — | — |



## Supplementary Note 5 — Definitions and audits added in revision round 4

### N5.1 'Guideline-healthy adult' (NHANES false-assertion denominator; `eval/realdata/eval_nhanes.py`, lines 212–220)
An adult is counted as healthy only if **all** of the following hold (sex-specific where shown, women/men): HbA1c < 5.7 %; fasting glucose < 100 mg/dL (when fasting sample available) and random glucose < 140 mg/dL; eGFR (CKD-EPI 2021) ≥ 90 mL/min/1.73 m²; urine ACR < 30 mg/g; haemoglobin ≥ 12/13 g/dL; MCV 80–100 fL; ferritin ≥ 30 µg/L (neutral if not collected in the cycle); total cholesterol < 200 mg/dL; fasting triglycerides < 150 and random triglycerides < 200 mg/dL; urate ≤ 6/7 mg/dL; ALT ≤ 25/33 U/L; sodium 135–145, potassium 3.5–5.1, chloride 98–107 mmol/L; calcium 8.6–10.3, phosphate 2.5–4.5 mg/dL; platelets 150–450 ×10⁹/L; WBC 4–11 ×10⁹/L; neutrophils 40–75 %, lymphocytes 20–45 %; CK ≤ 200/300 U/L; total bilirubin ≤ 1.2 mg/dL; ALP ≤ 130 U/L; GGT ≤ 60 U/L; albumin ≥ 3.5 g/dL; transferrin saturation 15–50 % (neutral if not collected). It is therefore a 30-analyte guideline-normal filter, not a requirement that all 2,045 registry analytes be normal. The filter was tightened once (2026-10-21, before the quarantine cycles were opened) because the first version let prediabetes by fasting glucose, mild hyperphosphataemia and microcytosis through and counted the engine's correct findings as false assertions.

### N5.2 Critical-value thresholds (`eval/baselines/b7_critical_values.py`; CAP/Kost 1990/Tietz consensus, conventional units)
K ≥ 6.5 or ≤ 2.5 mmol/L; Na ≤ 120 or ≥ 160 mmol/L; glucose ≤ 40 or ≥ 500 mg/dL; total Ca ≥ 13.5 or ≤ 6.0 mg/dL; Hb ≤ 6.5 g/dL; platelets ≤ 20 ×10⁹/L; WBC ≤ 1.0 or ≥ 50 ×10⁹/L; INR ≥ 5; arterial pH ≤ 7.10 or ≥ 7.60; bicarbonate ≤ 8 mmol/L; lactate ≥ 8 mmol/L; creatinine ≥ 7.5 mg/dL (no dialysis information available). Sample: 25 stays with ≥ 1 critical value plus 25 without, drawn with a fixed seed from the 400-stay LLM subset; 39 critical values in total. Both arms flagged 39/39.

### N5.3 Race and ethnicity audit of the knowledge base (2026-10-26)
Full-text search of the decompressed disease-guideline registry 14.1.0: 'race' 0, 'ethnic' 0, 'African' 0, 'Black' 0, 'Caucasian' 0, 'Hispanic' 0; 'white' 496 occurrences, all within 'white blood cell(s)'; 'Asian' 1 occurrence, inside a free-text source note on WHO BMI action thresholds that is not an executable condition. eGFR is CKD-EPI 2021 (race-free). The engine's context dataclass has an optional `ethnicity` field (an alias for the input key `race`); a search of `analyse_gidlines.py` finds no read of that field by any rule, layer or fusion step.

### N5.4 Hardware and software for all timings
2 vCPU Intel Xeon @ 2.60 GHz, 1.98 GB RAM, Linux 6.1, Python 3.13 (sandbox); engine single-process, no GPU, no network.

### N5.5 Novelty search for open laboratory-interpretation rule sets (2026-10-24)
Searched: AHRQ CDS Connect (repository and authoring tool offline since 28 April 2025; continuing as HL7 'CDS Connect Community Edition'), ECRI Guidelines Trust ('temporarily unavailable' since 2024), NICE (content outside the UK is personal-use only; product use requires written permission and a fee), WHO SMART Guidelines digital adaptation kits (ANC, family planning, HIV, TB, child health, immunisation, BP self-monitoring — no laboratory-interpretation kit), OpenCDS, Arden-syntax MLM collections and PubMed/Google Scholar ('open' AND 'rule base' AND 'laboratory interpretation'). No openly licensed, machine-executable rule set covering multi-analyte laboratory interpretation was found; the claim in the Discussion is bounded to this search and dated.

### N5.6 LLM arm — model identity
The LLM arm was run through the Arena.ai agent platform, which routes requests among several frontier model families (GPT, Claude, Gemini and others) and does not expose the model or version used for a given response. 'GPT-4-class' is therefore a capability-tier label, not a verified identity. Consequences: (i) the LLM arm cannot be reproduced against a named model version; (ii) the test–retest reads (κ = 0.69) may have been served by different models; (iii) the comparison should be read as 'a contemporary frontier assistant as a clinician would encounter it', not as a benchmark of a specific model. Prompts, raw outputs and scoring code are released so that the arm can be re-run against any named model.

### N5.7 Reporting checklist
TRIPOD+AI was adapted (the engine is not a prediction model fitted to data; items on model development/training are answered 'not applicable' with justification), and the DECIDE-AI early-stage clinical-evaluation items were consulted for the Limitations. The completed checklist follows.

### TRIPOD+AI (BMJ 2024;385:e078378) checklist — Hemoglyph Paper 1 (updated 2026-10-24, engine v5.3 / registry 13.3.0)

Status key: ✅ available now · 🟡 partly / needs the pending work · ❌ not yet.
(Hemoglyph is a knowledge-based, untrained system; items on "training data" are answered as
"not applicable — knowledge base construction described instead", which TRIPOD+AI permits.)

| # | Item | Status | Where / what is needed |
|---|---|---|---|
| 1 | Title identifies study as development/evaluation of a prediction/diagnostic model with AI | ✅ | Paper 1 title: "...retrospective multi-cohort evaluation" |
| 2 | Abstract: TRIPOD+AI for Abstracts | ✅ | Paper 1 abstract (cohorts, n, recall@5 / AUROC with 95% CI, baselines) |
| 3a | Background, rationale | ✅ | manuscript intro |
| 3b | Target population, intended use, users | ✅ | laboratory physicians / clinicians; decision support, not autonomous |
| 4 | Objectives | ✅ | SAP §1 |
| 5a | Source of data, study design | ✅ | SAP §3 (6 public datasets) |
| 5b | Setting, dates, eligibility | ✅ | Paper 1 Methods table (eICU-CRD demo 2014–15; NHANES 2005–2018 (7 cycles); PhysioNet/CinC 2019; UCI HCV/ILPD/thyroid; MIMIC-IV demo) |
| 5c | Participants' eligibility | ✅ | SAP §6 |
| 6a | Outcome definition and assessment | ✅ | SAP §5, script docstrings |
| 6b | Outcome blinded to predictors? | ✅ | labels pre-exist in datasets; engine untrained |
| 7a | Predictors (inputs) | ✅ | analyte lists per dataset (map tables) |
| 7b | Predictors blinded to outcome | ✅ | yes |
| 8 | Sample size | ✅ | no formal power calculation (pre-specified fixed public cohorts); groups with < 20 events flagged "exploratory" in every table; eICU B3+B4+B8 LLM comparison n = 400 stays / 596 labels gives ±4 pp CI half-width |
| 9 | Missing data handling | ✅ | no imputation; key-analyte conditioning |
| 10a | Model building: how predictors handled | ✅ | registry/ESL/fusion description |
| 10b | Model type, training | n/a | knowledge base construction (AI-assisted curation + sources) — **registry audit needed (🟡)** |
| 10c | Hyper-parameters | ✅ | fusion constants table |
| 10d | Performance measures | ✅ | SAP §4 |
| 10e | Model updating | ✅ | ESL ext. 4 / fixes after MIMIC demo, disclosed |
| 11 | Fairness: subgroup analysis | ✅ | eval/subgroup_fairness.py → sex, age band, hospital, panel size (eICU v5.3: run_20261023_v53/subgroup.log; Supplementary Table S4; sex gap M 65.4 vs F 61.1 reported as unresolved, H1 failed) |
| 12 | Evaluation / internal validation design | ✅ | SAP §3 roles |
| 13 | Comparison to other models / baselines | ✅ | B1 single-analyte rule; B2 supervised ML (eICU); blind GPT-4-class LLM via agent (B3/B4/B8, n = 400, McNemar p = 0.009); supervised logistic baseline on Sepsis-2019; published Isabel/DXplain figures in Discussion (not head-to-head) |
| 14a | Participant flow diagram | ✅ | Supplementary Fig. S1 (figS1_participant_flow.png) + Table S1 (TABLE_S1_cohort_flow.md) |
| 14b | Participant characteristics | ✅ | Supplementary Table S1 (cohort flow + age/sex/panel size per cohort) |
| 15 | Model specification / availability | ✅ | code + registries public (GitHub); add Zenodo DOI |
| 16 | Model performance with CIs | ✅ | reports in eval/results |
| 17 | Model updating results | ✅ | before/after tables |
| 18a | Limitations | ✅ | REAL_DATA_VALIDATION §4 |
| 18b | Interpretation | ✅ | Paper 1 Discussion |
| 18c | Implications | ✅ | Paper 1 Discussion (decision support, not autonomous; calibration needed before thresholds are used) |
| 19 | Registration / protocol | 🟡 | SAP v1 + Amendments 1–12 time-stamped in git; OSF registration text ready (docs/paper1/supplement/OSF_REGISTRATION_TEXT.md) — upload needs the author's OSF account |
| 20 | Code, data availability | ✅/🟡 | code public (GitHub); all datasets public (URLs in Data availability); Zenodo DOI minted at release by the author |
| 21 | Funding, conflicts | ✅ | no funding; SB is the sole developer of Hemoglyph (declared) |
| 22 | Ethics approval | ✅ | public de-identified data; no IRB needed; state DUA terms |
| 23 | Patient & public involvement | ✅ | none — stated |
| 24 | Open science: data sharing, code | ✅ | — |
| 25 | Supplementary materials | ✅ | SAP + amendments; per-group tables; error audit taxonomy (A/B/C1/C2, n = 200); calibration + DCA; fairness; LLM blind protocol & raw read-outs |
| 26 | Human–AI interaction, deployment context | 🟡 | UI, explanation and alert hierarchy described; NO reader study (stated as limitation) |
| 27 | Safety / failure analysis | ✅ | S5 critical-value capture; B7 critical values; fabrication provocation 200/200; healthy sweep 0/1000; error audit n = 200 |

Also required by DECIDE-AI if a reader study / early live evaluation is added.

## Supplementary Table S12b — Historical comparisons from the first submission (superseded; moved out of the main tables in revision round 5)

| comparison | engine | result | why superseded |
|---|---|---|---|
| registry-off ablation | v5.3 (before registry revisions 13.3–14.1) | flat@3/5/10 47.6 / 62.0 / 75.4; panel-supported@5/10 75.3 / 89.9 | engine and registry both changed; the ablations of the evaluated release are in main Table 5 (arm `no_rule`, `anchor_only`, `anchor_only_no_esl`) |
| LLM comparison | v5.1 | recall@5 64.4 % (60.5–68.2) vs LLM 59.6 %, +4.9 pp, naive McNemar p = 0.009 | ignored stay clustering; re-scored with frozen v7 and cluster-adjusted inference → 60.7 % vs 59.6 %, p = 0.54 (main Table 4) |

## Supplementary Table S15 — What is open, what is proprietary, and what was evaluated

| component | licence / status | evaluated in this paper | where |
|---|---|---|---|
| inference engine `analyse_gidlines.py` (v7, single file) | AGPL-3.0-or-later, public | **yes — the only inference component evaluated** | GitHub; Zenodo snapshot before publication |
| disease-guideline registry 14.1.0 and feature registry (2,045 analytes) | CC BY-SA 4.0, public | yes | same |
| evaluation scripts, label maps, SAP, freeze manifests, per-stay outputs | AGPL-3.0-or-later / CC BY-SA 4.0, public | yes (they produce every number) | same |
| LLM prompts and raw outputs | CC BY-SA 4.0, public | yes | Supplementary Data |
| desktop shell (Qt/QML UI, licensing, node-locked activation, telemetry) | proprietary, first author | **no** | not released |
| OCR / report-image path (optional cloud OCR) | proprietary; transmits images | **no** | not released; explicitly out of scope |
| local chat assistant | disabled in release 1.3.1 | no | — |

## Supplementary Note 6 — Retrospective version manifest (added in revision round 5)

No version-control system was used during development; this is a stated limitation. What exists is a set of dated, hash-identified artefacts that bound what could have changed and when. SHA-256 prefixes and file-system timestamps (UTC) of the retained snapshots:

| artefact | mtime (UTC) | bytes | SHA-256 (first 16 hex) |
|---|---|---|---|
| `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br` | 2026-10-26 03:25 | 1,232,933 | 0a2eeac0fa1b365d… |
| `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br.bak_v13_1_0` | 2026-10-26 03:25 | 1,186,778 | cebe06ae07e53f17… |
| `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br.bak_v13_3_0` | 2026-10-26 03:25 | 1,210,768 | 91cdb766fbf5c009… |
| `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br.bak_v13_4_2` | 2026-10-26 03:25 | 1,227,539 | 48a0c2e6c5dcaaf1… |
| `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br.bak_v14_0_0` | 2026-10-26 03:25 | 1,231,539 | 6efc802ea33e7c28… |
| `HEMOGLYPH_FEATURE_REGISTRY.json.br` | 2026-10-26 03:25 | 3,113,259 | 953d8daa4d0fe4df… |
| `HEMOGLYPH_GUIDELINE_REGISTRY.json.br` | 2026-10-26 03:25 | 1,232,933 | 0a2eeac0fa1b365d… |
| `analyse_gidlines.py` | 2026-10-26 03:25 | 975,269 | 6670cf41b944ae12… |
| `eval/engine_13_4_2_ref/analyse_gidlines.py` | 2026-10-26 03:25 | 945,898 | 1780fab94ee8f213… |
| `eval/engine_13_4_2_ref/cache_registry.py` | 2026-10-26 03:25 | 3,982 | 123b829a2fce5af7… |
| `eval/engine_13_4_2_ref/calcu.py` | 2026-10-26 03:25 | 95,606 | 2e850f64cddc4cc4… |
| `eval/frozen_registry_13_3_0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br` | 2026-10-26 03:25 | 1,210,768 | 91cdb766fbf5c009… |

Together with the dated SAP amendments (Note 1), the engine change log C1–C16 (Table S1) and the v14/v15 freeze manifests (261 and 316 files), these allow a reader to verify that the frozen artefacts used for every reported number are the ones archived, but **not** to verify the intent or sequence of individual edits inside the development period. From revision round 5 onwards the project is tracked in Git (repository initialised 2026-10-26 with annotated tag `paper1-R1-round5`; every later change to engine, registries or manuscripts is a dated commit).
