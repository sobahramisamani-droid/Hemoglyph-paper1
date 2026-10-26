# Statistical Analysis Plan (SAP) — Hemoglyph v1.3.1 retrospective diagnostic-accuracy evaluation

Version 1.0 — 2026-10-21 — author: Sobhan Bahrami. To be time-stamped on OSF before any
evaluation listed in §4 is run on the frozen engine. Amendments after registration must be
listed in §9 with date and rationale.

## 1. Objective
Estimate the diagnostic accuracy, calibration and safety of Hemoglyph (knowledge-driven,
untrained laboratory interpretation engine; registry 13.1.0; engine file SHA-256 `e0231327…d800f6` (v1 freeze, 2026-10-21) / `48313758…` (v2 = v1 + ESL extension 5, 2026-10-21, see Amendment 2),
registry SHA-256 `cebe06ae…c5d298` (unchanged between v1 and v2)) against clinician- and guideline-derived reference standards on
external real-world data, without any modification of the engine after the freeze.

## 2. Index test
Hemoglyph `ClinicalRuleEngine.interpret(observations, None, patient)` with the ranked
differential (list length 40 in evaluation, 15 in the UI), probabilities, evidence state,
expert-syndrome hits and critical alerts. Inputs: all laboratory analytes available in the
pre-specified window in the dataset's native units, plus age, sex, pregnancy and, where the
dataset provides them, medications. No free text, no vital signs, no imaging.

## 3. Datasets and roles
| Dataset | Role | Window | Reference standard |
|---|---|---|---|
| MIMIC-IV demo v2.2 (n=235 adm.) | **development** (error analysis 2026-10-21; fixes applied) | −6 h..+24 h of admission | ICD-9/10 discharge codes |
| UCI HCV (n=615) | held-out (run before freeze; archived as `uci_hcv_v1_before_fixes`; re-run after freeze) | single panel | source-lab class |
| NHANES 2017–18 (adults, random 3,000) | held-out | single exam | guideline lab definitions + self-reported physician diagnosis |
| UCI Thyroid thyroid0387 (n≈7,000 with TSH) | held-out | single panel | clinician diagnosis letters |
| ILPD (n=583) | held-out, stress test | single panel | clinic label |
| eICU-CRD demo v2.0.1 (≈2,000 stays, 186 hospitals) | held-out, **multi-centre** | −6 h..+24 h of ICU admission | ICU clinician problem list |
| MIMIC-IV v3.1 full / eICU-CRD full | confirmatory (credentialed; pending) | as above | ICD + adjudication subsample |

## 4. Endpoints
Primary (per cohort with multi-label clinical labels — eICU demo, MIMIC full):
P1 Recall@5 of listed/coded lab-detectable diagnoses whose key analyte was measured.
Secondary:
S1 Recall@3 / Recall@10; S2 per-group AUROC (listed vs. not listed, key analyte measured);
S3 chart-support precision of outputs with p ≥ 0.7; S4 calibration (reliability diagram, ECE,
slope/intercept of logistic recalibration) on group-level probabilities; S5 critical-value
safety: proportion of stays with K ≥ 6.5, Na ≤ 120/≥ 160, glucose ≤ 50, Ca ≥ 14, lactate ≥ 4,
pH ≤ 7.20, Hb ≤ 6, PLT ≤ 20, WBC ≥ 100 in which the corresponding entity appears in
`critical_alerts` or top-5 (target: 100%; report misses with Wilson CI); S6 latency.
Single-task cohorts (HCV, NHANES, thyroid, ILPD): AUROC with 95% bootstrap CI (2,000 draws),
sensitivity and specificity at the fixed operating point p = 0.5, and the healthy
false-assertion rate (NHANES T8).

## 5. Pre-specified task definitions
As written in the docstring of each script (`eval/realdata/eval_*.py`, `eval/mimic/*.py`) at
the time of registration; the scripts are part of the registered material.

## 6. Analysis populations
Adults ≥ 18 y; ≥ 8 analytes in window (ICU cohorts); pregnancy excluded in NHANES; a labelled
group is evaluable only if its key analyte was measured. No imputation. No survey weights.

## 7. Statistics
Wilson 95% CI for proportions; percentile bootstrap for AUROC; DeLong test for AUROC
comparisons against baselines (§8); Hosmer–Lemeshow not used (ECE with 10 equal-mass bins
instead). No multiplicity adjustment (descriptive accuracy study); all pre-specified endpoints
are reported regardless of result. Subgroups: sex, age (<65/≥65), hospital (eICU), unit system.

## 8. Baselines (to be run on identical inputs, after the freeze)
B1 reference-range flagging + published single-analyte decision rules; B2 LightGBM per group
trained on the MIMIC-IV development split (where available); B3 two general LLMs zero-shot
with a fixed prompt (model names/versions recorded; outputs parsed to entity ids; cost and
latency recorded). Comparison endpoint: Recall@5 and AUROC per group.

## 9. Amendments
(none)

## 10. Deviations already known at registration
- MIMIC-IV demo was used for error analysis; all engine changes made as a result are listed in
  the HARDENING changelog (summary file removed 2026-10-23; metrics retained in `eval/results/frozen_v1_20261021/`). Its metrics
  are reported as development-set metrics.
- UCI HCV was run once before four engine changes (insufficient-evidence ceiling, ESL
  primary protection, ESL mild-tier removal, list-length parameter); both runs are reported.


## Amendment 2 (2026-10-21) — ESL extension 5 after held-out error analysis

The v1 engine (hash above) was frozen on 2026-10-21 and run unchanged on eICU-CRD demo,
UCI HCV, ILPD, UCI thyroid0387 and NHANES 2017–18.  Error analysis of those **held-out** runs
(not of the development set) identified five safety/coverage defects:

1. platelets ≤ 20 ×10⁹/L in top-5 only 25 % (eICU S5);
2. WBC 470 ×10⁹/L → `nephrotic_syndrome` top-1 (no hyperleukocytosis anchor);
3. Hb 4.1 g/dL absent from top-5; INR 8.5 absent from top-5 (no coagulopathy anchor);
4. pH 7.18 with HCO₃ 34 (acute hypercapnic acidaemia) absent from top-5;
5. overt hyperthyroidism reported with *total* T4 (UCI thyroid0387) scored ≤ 0.44; urate > 7 mg/dL
   (NHANES) scored ≤ 0.34.

These were fixed by one additive change (`eval/patches/esl_ext5_20261021.py`: 20 severity-tiered
syndromes, two new group keys `tt4`/`tt3`, no change to rules, weights, registries or thresholds).
Evaluator label maps were also extended with existing registry ids that had been omitted
(`leukocytosis_pattern`, `elevated_inr_pattern`, `pancytopenia`, liver/vitamin-K coagulopathy ids).

**Reporting rule:** every held-out table in the manuscript reports **both** v1 (pre-specified,
frozen) and v2 (post-hoc, after one round of error analysis) side by side; v2 is labelled as
post-hoc and the datasets used for the error analysis are named.  No further engine change will
be made after the v2 freeze without a new amendment.  v1 outputs are archived under
`eval/results/frozen_v1_20261021/` and `eval/results/eicu_demo_v1_frozen_origmap/`.

## Amendment 3 — engine v3 (ESL extension 6 + clinical-salience re-ranking), 2026-10-21

**Trigger.** A blind zero-shot LLM baseline (B3, n = 100 eICU-demo stays, same stays scored for the engine)
reached recall@5 66.0 % vs 48.9 % for the pre-specified v1 engine. Error analysis of the 21 LLM-only hits
showed that in 19/21 the correct entity was already present in the engine's differential at rank 6–15; the
top-5 was occupied by family duplicates, derived `co_*` pair patterns, flat single-electrolyte findings, or
anchors firing in the wrong context. One real value (HCO3 1.7 mmol/L) was rejected by the plausibility floor.
**The guideline registry was not changed**; the amendment is confined to the expert-syndrome layer and the
ordering of the differential.

**Changes (all in `eval/patches/esl_ext6_ranking_20261021.py`, applied to `analyse_gidlines.py`):**
1. `ABSOLUTE_LIMITS["bicarbonate"]` lower bound 2.0 → 0.5 mmol/L.
2. Exclusions added: Gilbert anchor (glucose > 250, pH < 7.30, WBC > 15, lactate > 4, CRP > 50, Cr > 2.0, HCO3 < 15);
   RTA-4 anchor (Cr > 1.8, BUN > 40, lactate > 4, glucose > 400); toxic-alcohol anchor (glucose > 300).
3. New syndromes: `mi_massive_troponin` (cTn > 5000 ng/L, no CK veto), `renal_failure_marked` (Cr ≥ 2.0) and
   `renal_failure_moderate`, `sepsis_bandemia`, `sepsis_marked_leukocytosis_organ`, `sepsis_sirs_two_organ`
   (pattern strength), `dka_mild_ketones_unmeasured` (ADA/EASD 2024 mild tier), `acute_hepatocellular_injury`
   (pattern; vetoed by aetiology-specific serology), guards `ck_elevation_no_context_guard` and
   `pseudohypocalcemia_guard`; `hyperuricemia_female` now requires adult age + one co-finding.
4. Renal chronicity: two chronicity markers transfer the renal signal to CKD instead of capping AKI at 0.75 × a
   low CKD score (which deleted the renal entry altogether).
5. Clinical-salience re-ranking of the differential (probabilities unchanged): tier 0 diseases/syndromes
   (p ≥ 0.5); tier 1 low-salience single-analyte findings (p 0.5–0.75); tier 2 p < 0.5; tier 3 `co_*` pairs and
   intra-family duplicates (child id = parent id + suffix; `*_support_pattern` next to its base entity).
6. eICU label map: `heart_failure` group now also accepts the plain `heart_failure`, `acute_heart_failure`,
   `chronic_heart_failure`, `cardiorenal_syndrome` identifiers (previously only BNP-pattern ids).

**Status.** Post-hoc. v3 was developed after inspection of eICU-demo outputs (4 index stays and per-group counts
on the 100 B3 stays); eICU-demo recall for v3 is therefore an optimistically biased estimate and is reported
side by side with v1, never in its place. NHANES, UCI thyroid, UCI HCV and ILPD were not inspected when v3 was
designed and remain held-out with respect to ext 6, although the ext 5 changes (Amendment 2) had used them.

**Regression before release of v3:** pytest 598 passed (586 + 12 new in `tests/test_esl_ext6_20261021.py`;
one ext-5 test re-pinned for the female urate tier); engine 50/50; hard 151/151; hard2 124/124; hard3 78/78;
adversarial 86/86; healthy sweep 300/300 clean. Freeze: `FREEZE_v3_20261021_sha256.txt`.
Quick look on the 100 B3 stays (same stays, coded labels incl. non-lab-detectable): recall@5 v1 43.4 % → v3 54.7 %
(LLM 66.0 %); remaining misses are dominated by heart failure without BNP (8/9 absent) and sepsis without
infection markers — categories the labs cannot support.

**Amendment 3b (same day).** `eval/patches/esl_ext6b_20261021.py`: stem-based family dedup in the re-ranking
(severity/acuity prefixes, pattern suffixes) and two Sepsis-3 operational screens at pattern strength
(`sepsis_lactate_organ`, `sepsis_leukocytosis_one_organ`). Regression unchanged (598 pytest, all batteries 100 %).
Held-out check B4 (60 new stays, LLM answers fixed before engine run): LLM 58.7 % vs v1 50.0 % vs v3 58.7 %.

**Amendment 3c (same day) — anti-overclaim ceilings.** `eval/patches/esl_ext6c_20261021.py`: three dx-less guards
capping entities that laboratory data cannot establish — thyroid storm / thyrotoxic AF without systemic markers
(Burch-Wartofsky), any "shock" label without hypotension or vasopressor context (Sepsis-3), and PE / aortic
dissection / DVT on an isolated D-dimer (ESC 2019) — at 0.40–0.49; ceilings lift when context (`heart_rate`,
`systolic_bp`, `vasopressor_required`, conditions, medications) or corroborating labs are present. New ESL
context predicates `attr_true`, `attr_lt`, `attr_gt`. Regression: 601 pytest, all batteries 100 %.

**Amendment 3d (same day) — post-hoc fixes after the blind NHANES specificity test (B5).**
`eval/patches/esl_ext6d_20261021.py`: (i) metabolic syndrome accepts only *fasting* glucose ≥ 100 or A1c ≥ 5.7 as
the third harmonised criterion (random glucose, urate and ALT removed); a two-criteria guard caps it at 0.45
without BMI/waist/BP context; (ii) new computed key `egfr_c` (reported eGFR, else CKD-EPI 2021 from creatinine +
age + sex, adults only) with KDIGO CKD syndromes: G3+ & A2+ (strong), G3b (pattern), G3a + one corroborating
marker (pattern); an expert-anchored CKD is no longer capped beneath a prior-driven AKI in `_apply_renal_chronicity`.
B5 was run with ext 6c first (engine 1/40 false, CKD 9/18); ext 6d results (0/40, 15/18) are therefore **in-sample
for B5** and are reported next to the pre-fix numbers. Regression: 606 pytest, all five batteries 100 %.
Test anchors B5–B7 results are in `eval/results/nhanes_2017/` and `eval/results/eicu_demo/b7_critical_values.md`; the LLM reader in all of
them is the Arena agent (disclosed).

## Amendment 4 (2026-10-22) — engine v4 (ESL extension 7/7b) and evaluation-mapping clarification

**Scope.** All changes were motivated by inspection of eICU-demo stays 0–1200 (development split) and the NHANES T8 healthy-adult audit; stays 1200–2314 were not inspected before the clean-split check. No parameter was fitted to outcome labels. Fusion weights were *not* changed: a five-configuration sweep on 300 development stays (`eval/results/run_20261022_v4/weight_sweep_n300.md`) spanned recall@5 69.6–70.8 % and mean AUROC .841–.845, i.e. the weight vector is not a lever and the pre-specified default was retained.

**Engine changes (v3 → v4), all guideline-backed and mirrored in `eval/patches/esl_ext7_20261022.py`:** liver R-ratio requires ALT or ALP above ULN; nephrotic/HHS/DKA definition guards; non-specific-only ceiling (.35); CKD chronicity logic (KDIGO 2024: eGFR <60 with ≥2 chronicity markers or single-value G3b/G4 → CKD listed alongside AKI when chronicity is undetermined; AKI no longer capped beneath an anchored CKD); `ckd_anemia` requires normocytic indices and excludes rhabdomyolysis/lactic acidosis; fuzzy defining-feature gate for measured-but-normal defining analytes (7b). Regression gate: pytest 620, scripted batteries 489/489, healthy sweep 200 → 0 false assertions.

**Pre-specified vs post-hoc reporting.** Paper tables report v1 (frozen 2026-10-21, pre-specified) and v4 side by side on every dataset; v4 numbers on eICU-demo are development-set numbers and are labelled as such. Clean-split delta (stays 1200–1800, not inspected): recall@5 62.6 % → 63.7 %; CKD recall@5 5/26 → 16/26; diabetes 34/68 → 30/68 (displaced from rank 5 by CKD, documented).

**UCI thyroid H2 mapping.** The pre-specified positive set for H2 counted every entity whose id contains "hyperthyroid", including `subclinical_hyperthyroidism`. The thyroid0387 classes A–D denote overt hyperthyroidism; suppressed TSH with normal FT4/T3 in "no comment" records is therefore scored as a false positive under that mapping. H2 is retained unchanged; an additional row **H2c (overt entities only)** is reported, with the subclinical-rate shown separately as a label-semantics note. The v1 archive (`eval/results/frozen_v1_20261021/`) stores only `top3` per record, so v1 H2c is approximated from `top3` and flagged as such.

## Amendment 5 (2026-10-22) — structured error audit and subgroup analysis (added post hoc, taxonomy fixed before execution)

**Error audit.** Population = all (stay, clinician-listed group) pairs on eICU-CRD demo with the key analyte measured and the group absent from the top-5. Sample = 200 pairs, `random.Random(20261022)`. Taxonomy (deterministic, coded in `eval/error_audit.py`, written before the first run and not changed after seeing results): A no laboratory signature (SAP guideline thresholds per group); B listed with p ≥ 0.5, rank 6–25; C1 signature present, entity absent; C2 signature present, entity present with p < 0.5; D synonymous entity in top-5 not in SAP id list (reported, never credited). Run on v3 (ext6c) outputs and repeated unchanged on v4 outputs.

**Subgroups (TRIPOD+AI 19).** Strata: sex, age band (<45, 45–64, 65–79, ≥80), eICU `ethnicity`, `unittype`, hospital (top 8), panel size (≤10, 11–20, >20 analytes). Metrics: pooled recall@5 (1,000 stay-level bootstrap CI), recall@10, chart support at p ≥ 0.7, AUROC for the four largest groups. A stratum with ≥ 40 stays deviating by > 10 percentage points in recall@5 is flagged and discussed; no stratum-specific tuning is permitted. Script `eval/subgroup_fairness.py`.

## Amendment 6 (2026-10-22) — next-test layer (ESL extension 8) and the next-test-utility metric (post hoc, exploratory)

Motivation: 60 % of top-5 misses carry no laboratory signature of the listed condition (Amendment 5, category A). For those, a laboratory-only engine should name the test that would settle the question rather than guess. Extension 8 adds a cited confirmatory-test library (SSC 2021, ADA 2024, KDIGO 2012/2024, ESC HF 2021, BSH, ISTH, ACG 2017/2024, Spasovski 2014, Fourth UDMI) keyed by entities already in the differential plus one value-level trigger (random glucose 140–199 mg/dL → HbA1c). It changes no probability or ranking. Metric: among category-A misses whose discriminating test is distinct from the measured key analyte, the proportion for which `next_tests` or per-entity `recommended_tests` names that test. Reported as exploratory; not part of the pre-specified endpoints.

## Amendment 7 (2026-10-23) — ranking-hygiene layer (ESL ext 9) and scoring-map synonyms
*Post hoc, after the v4 error audit.* (1) Engine: three display-order rules (synonym families; aetiology-beneath-finding when its confirmatory marker is unmeasured and it does not out-score the finding; organising-diagnosis precedence for creatinine-defined renal failure, DKA and HHS) — probabilities and all threshold-based metrics (AUROC, sensitivity/specificity at 0.5, calibration) are unchanged by construction; only rank-based metrics (recall@k) can move. (2) Scoring map: `alcoholic_liver_disease`, `alcoholic_liver_pattern` (alcohol / cirrhosis groups) and `septic_shock_support_pattern`, `septic_shock_severe_lactic_acidosis` (sepsis) added as synonyms found in the D-category audit. Frozen v1/v3/v4 result files are not re-scored; v5 is reported alongside them. Pre-registered v1 remains the primary analysis.

## Amendment 8 (2026-10-23) — two additional eICU input arms (ESL extension 11: temporal module and clinical-context layer)
*Post hoc; added after the v5.1 scorecard. The primary labs-only protocol (Section 4) is unchanged and remains the headline result.*

**Motivation.** 67 % of residual top-5 misses on eICU v5.1 are category A (no laboratory signature of the listed condition); the two largest remediable sources are (i) chronicity / trajectory information discarded by the "first value per analyte" protocol and (ii) documented comorbidity that the labs-only arm never sees.

**Engine (ext 11, optional, inert when the data are absent).** (T) An observation may carry `series: [{t_hours, value}]`; the ESL reduces each series to trajectory keys and ten constellations implement KDIGO 2012 dynamic AKI criteria (≥ 0.3 mg/dL / 48 h or ≥ 1.5×, with peak ≥ 1.0 mg/dL), 4th-UDMI acute (≥ 20 %/≥ 50 % delta with a value > 99th percentile) vs chronic (flat) myocardial injury, lactate clearance (Jones 2010), Hb fall ≥ 2 g/dL / 24 h, > 50 % platelet fall (HIT only with documented heparin; DIC with a coagulation abnormality), and the ESE 2014 sodium over-correction warning (guard, no diagnosis). (C) `known_conditions` / `current_medications` map to registry entities by a fixed, conservative phrase table; a documented diagnosis with laboratory support on the panel is listed as established (0.80), without support at 0.49 (`documented_history`, below the operating point); documented CKD resolves renal chronicity; warfarin, metformin and statin constellations are ordinary ESL entries gated on the medication. No prior is injected.

**Evaluation arms (eICU-CRD demo, same 2,314 stays, same labels, same scoring map).** Arm A = labs only (primary). Arm B = labs + `pastHistory` (all entries except "Performed"/"Not Obtainable"/"No Health Problems", organ-system path retained) + `medication` rows with `drugstartoffset ≤ 0` (started at or before ICU admission). `admissionDx` is excluded as label leakage. Arm C = labs + all values of each analyte within −6 h…+24 h as a series (scalar = first value, as in Arm A). Arm B+C combined.

**Pre-specified reporting for Arm B.** Recall is reported separately for labels whose group is already *named* in the supplied history/medications (context echo) and for labels that are not; only the latter is interpretable as diagnostic gain. For Arm C the count of stays with ≥ 1 series and the firing count per temporal constellation are reported.

**Outputs.** `eval/results/run_20261023_v5/eicu_report_v5_2_{ctx,tmp,ctx_tmp}.md`, per-stay JSONs, `gate_ext11.txt`; tests `tests/test_esl_ext11_20261023.py` (22); patcher `eval/patches/esl_ext11_20261023.py`.


## Amendment 9 (2026-10-23) — reporting additions, label-map audit, human-validation instruments, provenance inputs
*Post hoc additions motivated by the literature review of CDSS-vs-LLM comparisons (Riches 2024/2025; Bhasuran 2025; Bond 2012). None changes the primary endpoint or the label map used for v5.x.*

1. **Rank-based secondary metrics** for the blinded LLM comparison: recall@1/3/10, mean reciprocal rank, rank-bin distribution, "not listed" rate; bootstrap CI of the MRR difference (`eval/baselines/b8_rank_metrics.py` → `rank_metrics_n400.md`). Pre-specified interpretation: recall@5 remains primary; recall@10 and "absent" structurally favour the engine (25 vs 10 slots) and are reported with that caveat.
2. **LLM test–retest**: 40 of the 240 B8 panels (seed 20261024) re-read blind by the same agent model class; agreement reported as label-level κ, Jaccard of top-5 group sets, Spearman ρ of shared group ranks. Engine determinism is reported as 100 % by construction (byte-identical per-stay files across freezes).
3. **Label-map audit** (`eval/results/eicu_demo/label_audit_n100.md`): 100 random held-out stays, 3,100 stay×group cells; study regex vs a deliberately liberal second coder; all 23 disagreements adjudicated by reading the diagnosis strings. Result: 0 false-positive labels, 2 definite misses (sensitivity 98.7 %), 2 ambiguous. The two missed patterns ("hematological effect of infection|thrombocytopenia", "drug withdrawal|alcohol withdrawal") are **not** changed for v5.2 so that all v5.x arms share one map; they are scheduled for the next protocol version.
4. **Human-validation instruments** (to be completed by an independent physician; results reported whatever they show): Form A1 — 100 executable rules, 60 from the operational set (186 diseases surfaced in any eICU top-5) + 40 from the whole registry, stratified by rule type, 3-level verdict + severity A–D; error rate with Wilson CI by stratum. Form B1 — the same 40 B8 panels as item 2, read blind with labs + age/sex only, ≤10 ranked diagnoses, scored with the identical keyword map → three-arm physician/LLM/engine comparison. Files in `eval/human/`; scorer `eval/human/score_forms.py`.
5. **Participant flow** (TRIPOD+AI 14) regenerated from raw files: `supplement/TABLE_S1_cohort_flow.md`, `figures/figS1_participant_flow.png`. eICU: 2,520 stays → 2,512 adults → 2,314 with ≥8 mapped analytes; 2,707 coded labels of which 2,432 scorable.
6. **Input provenance**: OCR-detected specimen flags (haemolysis / lipaemia / icterus, clotted, recollect; EN+FA with negation handling), specimen type, collection time and smear-morphology comments are now extracted (`ocr.detect_preanalytical`) and passed to the engine's existing `preanalytical_gate` through the clinical context (`AnalysisService._merge_preanalytical`); clinician entries override. Covered by `tests/test_preanalytical_provenance.py` (9 tests). This affects the application path only; evaluation cohorts carry no specimen flags, so no evaluation number changes. Documented in `supplement/INPUT_SCHEMA_v1.md`.
7. **Engineering**: `eval_eicu.py` now checkpoints every 200 stays and resumes (deterministic engine → identical results); Sepsis-2019 subsample fetched in 10 resumable parts.
8. **External case-vignette probe (B6, exploratory, pre-specified key)**: the 50 PMC-Patients case reports of Bhasuran et al. (npj Digit Med 2025;8:159; GitHub `balubhasuran/DDx_CaseReports`, ESM `sd_1.xlsx`). Only the "Lab Tests" paragraph plus age/sex is given to the engine; the Symptoms and Case Report columns are never used. Scoring key (`eval/realdata/pmc_cases/scoring_key_prespecified.json`) was written per case **before** any run: *specific* = the published final diagnosis; *syndrome* = the laboratory syndrome that contains it; `lab_detectable=false` for 3 cases (thallium poisoning, AMAN-GBS, lymphomatoid papulosis). Two arms, same key: (a) **parser arm**, free text → Hemoglyph prose parser → engine, no human in the loop; (b) **manual arm**, the author transcribed each paragraph into analyte/value/unit before seeing engine output (`panel_overrides.json`, every imputation flagged in `_note`; 2 cases have 0 numeric analytes and are scored as misses). Results (`eval/results/pmc_cases/report.md`): parser arm, all 50 — specific top‑1/5/10 = 2/10/12 %, syndrome 28/44/46 %; manual arm — specific 16/26/26 %, syndrome **40/68/70 %** (lab‑detectable n=47: 43/72/72 %). Pre-specified interpretation: the manual arm bounds what the laboratory paragraph alone carries; the parser arm shows that the application's prose parser (built for tabular reports) is the weakest link on narrative input, not the reasoning engine. The published GPT‑4 figures on the same 50 cases (top‑1 60 %, top‑5 81 %, top‑10 83 %) used the **full vignette** with lenient clinician scoring and are reported as context, not as a head‑to‑head comparison. Error-audit items opened from this probe: `ebola`/`lassa_fever` surfacing in top‑3 of two mild-transaminitis cases with negative viral serology (33365209, 30235756); apixaban INR 27 case (35844332) not mapped to an anticoagulant-effect syndrome (no drug context given); DILI entity never surfaces without drug context (expected by design — drug exposure is a context field, see Amendment 8).

## Amendment 10 (2026-10-23) — registry patch 13.2.0: pathogen-specific entities gated on exposure context

**Trigger.** B6 error audit (Amendment 9, item 8): `ebola` and `lassa_fever` in the top-3 of two mild-transaminitis vignettes with negative viral serology. Root cause: their only proposing rules were AST > 40 / ALT > 50 (/ platelets < 150), weight 0.3 — demoted in registry passes 9.3/9.4 but still surfacing whenever competition is thin. A registry scan (`eval/patches/registry_v13_2_0_exposure_gate.py`, `ROUTINE` set) found **76 infectious clinical entities whose screening/diagnostic rules use only routine chemistry/CBC analytes** — the same defect class.

**Change (registry content only; `analyse_gidlines.py` untouched).** (i) 53 pathogen-specific entities (viral haemorrhagic fevers, rickettsioses, zoonoses, helminths, endemic mycoses, organism-named bacterial infections): every leaf of their routine-only proposing rules gains `context: {exposure_history: true}` (135 rules). Through the engine's existing context mechanism the rule is *unknown* (not proposing) unless the clinician supplies `exposure_history: true` (travel / vector / animal / outbreak / occupational exposure) — a new optional context field documented in `INPUT_SCHEMA_v1.md`. (ii) 9 "*_pattern" entities whose only rule was CRP: rule retired (`retired_v13_2_nonspecific_single_marker`). (iii) 23 qualitative-positive specific-marker rules added where the feature registry already had an unambiguous test (PCR / antigen / IgM / culture → diagnostic_criterion weight 6; IgG-only serology or KOH → screening weight 3, `diagnosis_allowed: false`); no numeric threshold invented. Syndromic entities (sepsis patterns, pneumonia, cellulitis, osteomyelitis, cholangitis, gastroenteritis, tuberculosis) and ESL-driven, engine-guarded entities (leptospirosis, scrub typhus, PCP) are not gated.

**Pre-activation verification** (`eval/patches/test_registry_v13_2_0.py` → `eval/patches/cand/test_registry_v13_2_0.md`; `tests/test_registry_v13_2_exposure_gate.py`, 5 tests): target vignettes clean; gate opens with `exposure_history: true`; hantavirus IgM still proposes hantavirus at rank 2; healthy panel empty; **B8 240 blind panels: recall@5 293/456 before and after, 0 label-level changes**; PMC manual arm 34/50 before and after, 0 rank changes; pathogen entities in any eICU/PMC top-10 after patch: 0 (one legitimate strongyloidiasis with IgE 3770 + eosinophilia remains).

**Activation rule.** The patch is **not** applied while the v5.2 three-arm eICU chain is running (all v5.x arms must share registry 13.1.0). It is applied immediately after `FREEZE_v5.2` is written, becomes registry 13.2.0, and the affected evaluations are re-run as v5.3 with the 13.2.0 hash in a separate freeze file; the paper reports v5.2 (13.1.0) as primary and v5.3 as the post-audit correction, with this amendment cited. This is the first worked example of the "errors found by audit are corrected in the next registry release with a changelog" policy stated in the Limitations.


## Amendment 11 (2026-10-23) — pre-registered findings from the v5.2 context-arm review and sex-gap anatomy

Source: `eval/results/eicu_demo/deep_review_20261023.md`, written before the v5.2 freeze; no code or registry changed.

1. **Context arm is largely a context echo.** Same labels, ctx vs labs-only: NOT named in history (n=2,467) +0.9 points recall@5; named in history (n=240) +23.3 points. Documented-only entries consume ranking slots and reduce recall for AKI (−5.0), hyperkalaemia (−6.1), coagulopathy (−6.1). **Reporting rule:** the context arm's headline number in the paper is recall@5 on NOT-named labels; the all-label number is given with the echo decomposition. **v5.3 design change (pre-registered):** `listed_documented` entities are shown in a separate "documented problems" block and excluded from the ranked differential that recall@k is computed on.
2. **Sex gap is within-group, not case-mix.** Direct standardisation: female label mix at male per-group rates = 57.9 % vs observed 55.7 % (male 58.5 %). Largest female deficits: AKI −14, GI bleeding −13, AMI −12, renal impairment −9 points. Root cause located in the registry: AKI screening uses creatinine > 1.3 mg/dL for all sexes while the feature registry carries sex-specific ranges (F 0.5–1.1); troponin I has a single cut-off (0.04 ng/mL) without sex-specific 99th percentiles. **v13.3 corrections (pre-registered):** sex-specific creatinine thresholds in AKI/CKD screening rules; sex-specific troponin limits for hs-assays (ESC 2020 / 4th UDMI); before/after reported on the same frozen cohorts and in the fairness table.
3. **Mislabelled rule class:** `acute_myocardial_infarction` carries risk-factor rules (total cholesterol ≥ 200, LDL ≥ 115, hs-CRP > 3) typed as screening for an acute event. These will be re-homed to risk entities in v13.3 and are added to the A1 physician audit sample as a "wrong entity" exemplar.

## Amendment 12 (2026-10-23) — registry patch 13.3.0: systematic defect-class repair (pre-registered before any evaluation on the patched registry)

**Trigger.** A read-only defect scanner (`eval/registry_defect_scan.py`, ten classes D1–D10) was run on registry 13.1.0 (34,005 executable rules, 6,750 entities) after the Amendment-11 review. Output: `eval/results/registry_defect_scan_13.1.0.md/.json`.

**Findings (13.1.0, after manual triage of scanner output).** D1 sex-blind thresholds on sex-dimorphic analytes: 800 flagged, of which 197 rules carried `_male_`/`_female_` in their id but `population.sex = all`, and ≈350 proposing rules on creatinine/Hb/Hct/RBC/ALT/AST/urate used the male or mixed limit for both sexes (ferritin and serum iron flags are false positives: WHO cut-offs are sex-independent). D2 unit/scale: hs-troponin I/T leaves declared in ng/mL with values 14–50 (ng/L values mislabelled; 67 leaves) and 13 sperm-morphology leaves > 100 %. D3: six risk-factor rules (lipids, hs-CRP) typed as screening for acute entities (AMI ×3, ischaemic stroke, acute pericarditis ×2). D5: 100 etiologic clinical entities proposable from routine analytes alone, of which 63 are non-syndromic (sarcomas, lymphomas, vasculitides, ALS, aortic dissection, upper-respiratory infections, 30+ infections not covered by 13.2.0) and 18 are genuine laboratory syndromes kept unchanged (DIC, TMA, warfarin over-anticoagulation, biliary obstruction, cholecystitis, contrast nephropathy, kwashiorkor, NEC, GSD-1, hypophosphatasia, lymphangiectasia, chylomicronaemia, pyloric stenosis, PROM, biliary atresia, hypothermia, heat stroke, pattern 026). D7: 511 rules applied adult thresholds (creatinine ≥ 1.0, Hb ≤ 11, ALP ≥ 130, bilirubin ≥ 1.2, eGFR ≤ 60, urate ≥ 6) to neonates/infants. D8: 57 single-routine-analyte diagnostic rules on clinical entities claimed `specificity: specific` (e.g. procalcitonin → appendicitis). D4/D6/D9/D10 (impossible values, undefined features, dangling sources, single-analyte diagnosis_allowed): 0.

**Repair (`eval/patches/registry_v13_3_0_quality.py`, stacked on the 13.2.0 candidate; registry content only, engine untouched).** D1a: `population.sex` set from the rule id (197). D1b: 350 rules split into a male rule (original threshold) and a female rule `<id>_f13_3` whose threshold is the female reference limit from the feature registry (Tietz/KDIGO/WHO) when the original equalled the male limit, otherwise scaled by the limit ratio; urate thresholds < 7.0 (solubility limit 6.8) are not split; with sex unknown both variants are evaluated (the more sensitive one governs — documented behaviour). D2: 67 troponin leaves relabelled ng/L; 13 sperm-morphology rules retired. D3: six rules re-homed to `atherosclerotic_cardiovascular_risk_lipid_pattern` as non-specific screening, `diagnosis_allowed: false`. D5: 63 entities gated — infectious ones on `exposure_history: true`, all others on a new optional context key `clinical_suspicion: true` (same engine mechanism; entity is never proposed from routine analytes without it). D7: neonate/infant (and child for ALP) removed from the population of 511 rules; no paediatric thresholds invented; neonatal entities untouched. D8: 57 rules downgraded to `non_specific`, `diagnosis_allowed: false`. Executable rules after patch: 34,356 (+350 female variants, −13 retired).

**Verification.** Scanner re-run on the candidate: D3/D4/D6/D7/D8/D9/D10 = 0; D1 residue = ferritin/iron (documented), staging/component rules and one dengue Hct warning-sign rule; D5 residue = the KEEP list exactly. Structural tests `tests/test_registry_v13_3_quality.py` (9) pass. Functional regression (`eval/patches/test_registry_v13_3_0.py`, B8 240 panels and PMC manual arm, plus sex-specific probes) is reported in `eval/patches/cand/test_registry_v13_3_0.md`.

**Pre-registered expectations and reporting rule.** 13.2.0 + 13.3.0 are activated together after the v5.2 freeze and produce v5.3. Primary pre-registered hypotheses: (H1) female−male recall@5 gap on the eICU held-out cohort narrows from −2.8 points (v5.1) to within ±1.5; (H2) no decrease > 1 point in overall recall@5; (H3) B8 recall@5 ≥ 293/456 − 5. v5.3 is reported next to v5.2 on the same cohort with per-group deltas; failure of H2/H3 leads to reverting the specific class responsible, not to silent re-tuning. The residual limitation stands: the repair was AI-executed from reference-range tables, logged per rule, and remains subject to the A1 physician audit.

**Amendment 12, addendum (same day, second scanner wave, before any v5.3 evaluation).** Four further classes were found and folded into the same 13.3.0 candidate: D12 — 282 rules applied adult creatinine/eGFR/ALP thresholds to the *child* age group (child creatinine ULN ≈ 0.3–0.7 mg/dL; CKD-EPI is adult-only): child removed from their population. D13 — 6 exact duplicate executable rules (same entity, type and expression; evidence counted twice): older copy retired. **D17 — domain-template broadcast:** five haematology screening rules (platelets ≥ 450, Hb < 13, platelets < 100, ferritin < 15, TSAT < 20) had been attached to *every* haematology entity (195 entities, including thrombophilias, haemophilia, PE/DVT, ITP, polycythaemia), six endocrine screens (low/high fT4, hypo/hyper-TSH, glucose < 55, morning cortisol) to all 31 endocrine entities (e.g. PCOS, Paget's, pheochromocytoma) and three renal screens to 24–36 renal entities; 940 of these 1,192 rules were retired using a per-template compatibility pattern recorded in `TEMPLATE_COMPAT` (kept only where the analyte change is part of the entity's known laboratory picture). **D18 — placeholder entities:** 90 entities named "Expanded laboratory pattern 001–090" carry no clinical identity (templated rules plus one "analyte > 0" rule); all their rules were retired and the entities flagged `placeholder_retired_v13_3_0`. Consequently the registry entity count quoted in the manuscript (6,750) must be reported as 6,660 clinically named entities (+90 retired placeholders), and a number of alias entities (e.g. `acute_myeloid_leukemia` / `acute_myeloid_leukemia_aml`) are now gated on `clinical_suspicion` because their only remaining rules are routine-analyte templates (D5 re-run after D17: 87 entities gated in total). Executable rules after the full patch: 33,230 (from 34,005). The pre-registered hypotheses H1–H3 above apply unchanged; D17 is the class most likely to move overall recall and is therefore reported separately (ablation: 13.3.0 with and without D17) if H2 fails.

**Amendment 12, activation record (2026-10-23 21:03–21:25 UTC).** Activation requires copying the candidate to *both* `HEMOGLYPH_GUIDELINE_REGISTRY.json.br` and the engine default `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br`; the first attempt updated only the former, so the runs produced 19:43–21:00 UTC are void (`run_20261023_v53/invalid_ran_on_13_1_0/`). Two corrections were made on the real 13.3.0 gate, both recorded here before any held-out result was examined: (i) D8 had wrongly downgraded single-analyte diagnostic rules of laboratory-finding entities (`*_pattern`, -emia/-penia/-cytosis/-uria) — e.g. `hypertriglyceridemia_pattern` — which the engine merges into the parent entity; D8 now excludes finding entities (57 → 12 downgrades) and the engine battery returned to 50/50. (ii) `test_profound_neutropenia_named_and_cultures_requested` previously required `severe_neutropenia` at rank 1 for a pancytopenic panel (WBC 0.2, platelets 19, Hb 6.7); that rank depended on the D17 template rules (Hb < 13, platelets < 100 voting for neutropenia entities), which are clinically unjustified. The test now requires severe_neutropenia within the top 4 with p ≥ 0.6 plus cultures/lactate in next tests; the ranking among three co-true findings is reported as a known behavioural change, not corrected by re-adding rules.

## Amendment 13 (2026-10-24, 11:40 UTC) — POST-HOC concurrent-diagnosis analysis of Sepsis-2019 (declared after the pre-registered result was known)

**Status.** Exploratory. The pre-registered Sepsis-2019 analysis (prediction of Sepsis-3 onset at any hour from the first-24-h laboratory panel; `eval/realdata/eval_sepsis2019.py`) was run on registry 13.3.0 and gave AUROC 0.593 (0.570–0.617) against a supervised logistic baseline of 0.689. **That result is final and is reported unchanged in the main text.** This amendment adds a second analysis of the same file that matches the task the engine was designed for (recognition of a concurrent diagnosis, as in eICU) and tests the optional vital-signs context; it was written and dated *before* the new analysis was run, but *after* the pre-registered result was known, and is therefore labelled post-hoc wherever it is reported.

**Design (fixed; engine and registry unchanged — registry 13.3.0 is loaded explicitly although 13.4.2 is live).** Cases: all sepsis patients; window ICULOS ∈ [t_L, t_L + 12] where t_L is the first labelled hour (the challenge label precedes clinical onset by 6 h, so the window is ≈ onset − 6 … + 6 h). Controls: 1,500 non-sepsis patients drawn with seed 20261024, each given a 12-h window whose start is drawn (same seed) from the empirical distribution of case t_L and clipped to the stay, so ICU dwell time is matched. Inclusion ≥ 3 laboratory analytes in the window (vitals and temperature do not count). Arm A: labs + temperature (as pre-registered). Arm B: labs + HR, SBP, MAP, respiratory rate, temperature as observations and as patient context. Score, metrics, bootstrap and supervised baseline exactly as in the pre-registered analysis; baseline B adds the vitals.

**Pre-stated interpretation rules.** (i) Neither arm replaces the pre-registered number; both are tabulated with it. (ii) An engine AUROC in arm A of ≥ 0.70 would support the claim that the 0.59 reflects the prediction framing rather than an inability to recognise the septic panel; < 0.65 would indicate the engine's sepsis group is genuinely weak and this is stated in Limitations. (iii) Arm B − arm A is reported as the contribution of vital signs; no threshold is attached because the context module is optional. (iv) Known biases stated with the result: label-anchored windows are not operational; cases are sampled more densely around onset (the ≥ 3-lab filter retains a larger share of cases than controls); Sepsis-3 labels are themselves algorithmic.

**Outputs.** `eval/results/sepsis2019/concurrent_report.md`, `concurrent_summary.json`, `concurrent_per_patient.json`; reported in the Supplement (Table S-Sepsis) and one sentence of the Results paragraph, flagged post-hoc.


**Outcome (recorded 2026-10-24 after execution).** 388 cases / 772 controls. Arm A AUROC 0.534 (0.508–0.561); arm B 0.534 (identical in all 1,160 windows — no 13.3.0 sepsis rule consumes vital signs); logistic baseline 0.667 / 0.703; recall@5 21.6 %; flag rate 14.8 %. Rule (iii) applies: < 0.65 → the laboratory-only sepsis group is genuinely weak on real ICU data; stated in Results and Limitations; Supplementary Table S12. Mechanism: no PCT/CRP in the file, lactate in 37 % / 22 % of windows, sepsis probability 0 in 74 % of cases. No rule or weight changed.

---

## Amendment 14 — Registry 14.0 / engine v6 development with a quarantined external validation (dated 2026-10-24, written BEFORE any change)

**Why.** Pre-registered and post-hoc analyses (Amendments 1–13) exposed four mechanistic weaknesses: (a) laboratory findings displace causal diagnoses from the top ranks; (b) the sepsis group is anchored on PCT/CRP and ignores clinical signs; (c) CKD is asserted from a single creatinine (KDIGO requires chronicity); (d) `all`-type criteria are silenced by one unmeasured analyte. We now fix these **by design, from guideline sources**, not by fitting to outcomes.

**Data roles (fixed now).** *Development (may be inspected freely):* eICU-CRD demo, Sepsis-2019 set A, NHANES 2017–18 (J), the existing PMC case set, UCI/ILPD. *Quarantined validation (`eval/quarantine/`, not opened by any script or person until FREEZE_v14):* Sepsis-2019 **set B (hospital B)**, NHANES **2013–14 (H)**, **MIMIC-IV demo (all admissions)**, and **50 new PMC case reports** collected after the freeze by the fixed query recorded in `eval/realdata/eval_pmc_cases.py`. Caveat: 30 MIMIC-IV demo admissions were used in a 2026-10-21 smoke test (`eval/results/mimic_demo/`); no 14.0 change is derived from them.

**Changes allowed (closed list).** C1 two-tier output (`kind ∈ diagnosis | laboratory_finding | syndrome`; top-k scored on diagnoses; findings always reported). C2 syndrome layer: SIRS, qSOFA, SOFA sub-scores from Sepsis-3 (Singer 2016) and SSC 2021, as `syndrome` rules; sepsis asserted only as syndrome + lab support, otherwise `hyperlactataemia, cause undetermined`; `not_assessable` status when a group's anchor analytes are absent. C3 KDIGO chronicity: single creatinine → `renal_impairment (chronicity undetermined)`; CKD requires >90-day persistence or chronicity markers; AKI requires KDIGO delta. C4 `n_of` operator and absent≠normal handling in `all` criteria. C5 missing guideline patterns: alcohol-related liver pattern, R-ratio cholestatic/hepatocellular, bilirubin classification, septic shock, toxic alcohol (osmolal gap), MASLD/FIB-4, PSGN — each with a source located by direct web lookup. C6 label-audit-driven fixes for hypoglycaemia/hypocalcaemia only if the audit of 20 missed cases shows an engine error (threshold/unit/albumin-corrected calcium); malnutrition moved to `requires clinical data` per GLIM. **Not allowed:** weights tuned to a dataset; rules written for a specific missed case; thresholds without a source.

**Development gate (per change, on development data).** pytest full; hard batteries 1–3 no regression; eICU labs-only top-1/3/5 not worse than 13.4.2 (49.3/63.7/76.9) and healthy-panel false flags 0/40; fuzz 0 false-fires/1000.

**Pre-stated success criteria on the quarantined set (one run, registry frozen, no re-tuning after):**
1. MIMIC-IV demo, labs-only, lab-detectable groups: top-5 ≥ 65 %, top-1 ≥ 45 %. (Primary.)
2. Sepsis-2019 set B, concurrent framing as Amendment 13, arm B (labs + vitals): AUROC ≥ 0.65; flag rate in non-sepsis windows ≤ 20 %. (Primary for C2.)
3. NHANES H: diabetes, CKD, anaemia, iron deficiency AUROC each within 0.03 of the NHANES J values for 13.3.0; CKD false-positive rate not higher than 13.3.0 on the same file.
4. New PMC cases: top-5 ≥ 60 %.
5. Safety: healthy-panel false flags 0/40; fuzz 0/1000.
**Interpretation rule:** every criterion met → 14.0 reported as "improved and externally validated"; any primary criterion missed → reported verbatim as a failure of that component, 13.3.0 remains the headline, no further tuning on the validation data. Both 13.3.0 (pre-registered) and 14.0 (this amendment) appear in the paper, labelled.

**Expected effect sizes (for honesty, recorded now):** C1 eICU top-1 +5–8 points; C2 set B AUROC 0.65–0.72; C3 CKD false positives 76 → < 30 on the dev file.

**Development log (recorded 2026-10-24 during execution; quarantined data still unopened).**
*Build.* Registry 14.0.0 = 13.4.2 + 2 sources + 4 entities (SIRS, qSOFA — syndromes; septic shock; reduced GFR, chronicity undetermined — finding) + 8 guideline-anchored rules; engine v6 (`eval/results/gate_14_0_0/ENGINE_CHANGES_v6.md`).
*Defect found during the gate.* The feature registry's canonical unit for arterial pO2/pCO2 is UCUM `mm[Hg]` whereas the evaluation scripts (and HL7 inputs) supply `mmHg`; before the v6 unit-alias fix these analytes were **silently dropped in every 13.x eICU run** (and all blood pressures in the Amendment 13 arm B). The 13.4.2 reference numbers were therefore computed without blood gases.
*Attribution (eICU demo, 2,314 stays, labs-only, `compare_arms.py`):* 13.4.2 original 49.3/63.7/76.9 % (top-3/5/10, flat); v14 + legacy units 44.4/59.5/74.8; v6 engine + registry 13.4.2 + fixed units 47.4/60.9/75.5; v14 + fixed units 43.8/58.4/73.8. Two-tier top-5 (C1 metric) 72.2–72.7 % in all three v6 arms. Unit fix ≈ −1.3 pt, engine ≈ −1.5 pt, registry ≈ −2.7 pt on the flat metric; the loss is slot crowding by entities that are true statements about the panel but are not problem-list labels (reduced GFR 614 top-5 slots, myocardial injury +315, hypoxaemia 209, hypercapnia 202, SIRS 51) and the KDIGO-correct withdrawal of single-eGFR CKD assertions (CKD recall@5 64.9 → 30.4 %; renal union 79.8 → 84.0 %).
*Gate status.* pytest 689/689, hard batteries 151/151, 124/124, 77/78 (pre-existing miss). **The development-gate clause "flat top-3/5 not worse than 13.4.2" is NOT met** and is recorded as such; the C1-specified ranking (top-k on the structured output) is reported with two metrics — two-tier rank and grouped rank (entries nested under the diagnosis that explains them). No threshold or weight was changed in response to label outcomes; every engine change is listed with its guideline source in `ENGINE_CHANGES_v6.md`. Decision on which registry is shipped as "live" is deferred to the quarantined run; 13.4.2 remains the paper's primary.
*Development-log continuation (2026-10-25).* eICU grouped-rank metric (engine attribution; defined before this run): top-1 32.9 %, top-5 68.6 %, top-10 78.6 %; a same-metric 13.4.2 control run is required before any comparison is drawn. NHANES J (community encounter): all nine AUROCs within 0.02 of the 13.3.0 values (diabetes .945, CKD .958, anaemia .973, iron deficiency .990, ALT .721); healthy-adult false assertion 1/160. The Sepsis-2019 set A concurrent script failed on a duplicated `SaO2` column (software defect introduced by the v14 unit pass; corrected and re-run — no result had been produced). Quarantined data remain unopened.
*Development-log continuation 2 (2026-10-25).* Sepsis-2019 set A concurrent (v14, before change C7): labs-only AUROC .559, labs + vitals .590 (13.3.0: .534/.534), recall@5 42.6 % (21.6 %), control flag rate 26.1 % (14.8 %) — the flag-rate limit (≤20 %) was exceeded. Diagnosis: the SIRS-based screening syndrome asserted sepsis at p≈0.72. Change C7: screening hits are capped at 0.45 ("possible", non-anchoring), per SSC 2021 (screen = prompt for evaluation) and Sepsis-3 (SIRS not definitional); hypotension added as organ-dysfunction support for lactate-based sepsis. We state openly that the trigger for this change was a development-set operating characteristic; the rule content is guideline-derived and the single confirmatory test remains set B. All development evaluations (eICU, NHANES J, set A) are being re-run with the final engine.
*Development-log continuation 3 (2026-10-25, final dev numbers, all re-run with the final engine).* eICU flat 43.8/58.4/73.8 (criterion "not worse than 13.4.2" not met); two-tier@5 72.2 = same-engine 13.4.2 control; grouped@5 68.6 vs 68.1 (same engine, same metric, 13.4.2 registry). NHANES J within 0.02. Sepsis set A prediction .600 (13.3.0 .593); concurrent arm B .592, recall@5 28.9 %, flag 18.1 % (13.3.0: .534/21.6 %/14.8 %). On the development data the set-B AUROC criterion (≥ .65) would not be met; we proceed to the single quarantined test without further changes to the sepsis logic. Table of all arms: `eval/results/gate_14_0_0/ENGINE_CHANGES_v6.md`.
*Development-log continuation 4 (2026-10-25; registry 14.1.0).* Error analysis on development eICU showed that the flat-metric loss of v14 was displacement by explained findings listed adjacent to their explaining diagnosis. Three label-independent corrections: C8 explained findings are sorted after self-standing asserted entities (probabilities unchanged); C9 an ischaemic-context MI syndrome (4th UDMI injury + ischaemia; ESC 2023 rule-in); C10 a single troponin above the 99th URL now maps to a new finding "myocardial injury, acuity undetermined" (4th UDMI §3), with acute injury reserved for serial rise/fall — the same logic already applied to creatinine (reduced GFR, chronicity undetermined). The eICU infarction group accepts the new finding as it accepted the acute-injury finding. Registry 14.1.0 also carries the MASLD and PSGN rules (C5). Gate 14.1.0 (unit tests, eICU, set A) is running; quarantined data remain unopened.
*Development-log continuation 5 (2026-10-25; gate 14.1.0, final development numbers).* Unit lane: pytest 689/689, hard batteries 151/151, 124/124, 77/78 (same pre-existing miss). eICU demo (2,314 stays, labs-only, encounter = icu): flat top-3/5/10 **48.5 / 60.8 / 74.1 %** (14.0.0: 43.8/58.4/73.8; same-engine 13.4.2 control 47.7/60.9/75.5; original 13.4.2 49.3/63.7/76.9); two-tier@1/3/5 32.3/62.3/71.7; grouped@1/5/10 31.0/68.8/78.4; group recall@5 anaemia 81.6, sepsis 49.5, diabetes 44.7, AMI 82.1, AKI 78.9, CKD 39.9, HF 79.3, GI bleed 76.6. C8–C10 recovered the flat loss of 14.0 to within the same-engine control (−0.1 at top-5); the residual ≈ −2.9 vs the original 13.4.2 at top-5 is attributable to the ABG unit fix (≈ −1.3; previously dropped analytes now compete for slots) and KDIGO-correct CKD behaviour (≈ −1.5). Set A concurrent (post-C7, unchanged): labs .559, labs + vitals .592, flag 13.0 / 18.1 %. Remaining misses were reviewed and are not addressed by further rules: diabetes misses are mostly uncoded in the top-10 because real anaemia/AKI/sepsis outrank a single glucose (no single-glucose diabetes rule by design); sepsis misses are mostly stays whose lab panel contains no sepsis signal. **Development declared closed at this state; FREEZE_v14 follows and quarantined data are opened once, with the control arm = frozen registry 13.3.0 under the same v6 engine (the 13.3.0-era engine is not reconstructable; the control therefore isolates registry effects, and engine effects are carried by the same-engine eICU controls above).**
*Gate 14.1.0 closed (2026-10-25, exit 0 on all lanes).* Set A prediction (labs first 24 h): sepsis-group AUROC **0.600 (0.575–0.625)**, unchanged from 14.0.0 (13.3.0: 0.593; logistic reference 0.691); recall@5 33.3 %, flag rate 17.4 % (≤ 20 % criterion met on dev). FREEZE_v14 written immediately after this entry; quarantine opened once.

**Amendment 14 — validation outcome (2026-10-25, one shot after `FREEZE_v14_20261025`).** MIMIC-IV demo (235 admissions, all coded lab-detectable diagnoses): top-5 47.9 %, top-1 ≈ 18 % — criterion (≥ 65 / ≥ 45) **failed** in both arms (control 13.3.0 registry under the same engine 50.1 %); the arm difference is CKD recall (27.7 vs 50.8 %), a KDIGO-chronicity consequence, while AKI (56.7 vs 52.2) and infarction (71.4 vs 42.9, n = 7) improved. Sepsis-2019 set B (4,558 / 268): concurrent labs + vitals AUROC 0.638 (0.601–0.675) vs control 0.639 — criterion ≥ 0.65 **failed**, flag rate 16.1 % (≤ 20 %) met; first-24-h prediction 0.610 (0.583–0.640), control 0.611; the earlier expectation (0.65–0.72) was wrong. NHANES H: all five laboratory-defined tasks within 0.03 of cycle J (met); ALT elevation 0.880 vs control 0.742 (MASLD rules; above the band); CKD self-report −0.07 in both arms. Healthy sweep 0/1000; NHANES guideline-healthy 1/246 (both arms); perturbation 752/755. The post-freeze PMC-case criterion remains pending (collection only now permitted). Full table: `eval/results/validation_v14/VALIDATION_REPORT_v14.md`. Interpretation carried into the paper: 14.1 is a correctness release, neutral-to-negative on coded-diagnosis recall, positive on its specific targets; 13.3.0 remains the pre-registered primary analysis.

*Post-validation engine change v6.1 (declared 2026-10-25 BEFORE any run).* The perturbation fuzz on the frozen engine (synthetic hard battery, not quarantined data) exposed a fusion asymmetry: an anchor-strength expert-syndrome hit (0.95; the published decision limit itself) was floored at 0.90 × vote = 0.855 when a prior-driven layer disagreed, and therefore ranked below a weaker single-vote finding (0.88) that had no corroborating layer at all (sodium 121 mmol/L listed under uric acid 8.9 mg/dL). Change: for the primary diagnosis of an anchor-strength constellation the floor is the full constellation vote. This is a label-independent ordering principle (anchor > strong > pattern > supportive), not a case rule. Procedure: unit gate + eICU dev run; if the dev gate passes, the quarantined analyses are re-run once as a **second look** and BOTH looks are reported side by side (first look = v6.0, already recorded above); the second look does not replace the first.

## Amendment 15 — engine v7 "causal attribution" (declared 2026-10-25 BEFORE any evaluation on the new quarantine; `eval/quarantine_v15/` downloaded and unopened)

**Why.** The Amendment 14 validation showed no net recall gain of 14.1 over 13.3.0, and the development error audit (eICU, `eval/error_audit_v7.py`) located the main mechanism: the finding-demotion pass listed every laboratory finding beneath the *best-scoring* diagnosis and labelled it "explained by" that diagnosis even when no causal relationship exists (e.g. anaemia "explained by" hyperglycaemia). The two-tier output therefore hid findings under unrelated diagnoses, while unrelated diagnoses were promoted into the first lines. All v7 changes are guideline-sourced attribution/grading rules, developed only on development data; none uses an outcome-fitted threshold.

**Closed list of changes (engine v7; registry 14.1.0 unchanged).**
- C11 *causal attribution map* (`_CAUSAL_EXPLANATION`, `_can_explain`, `_causal_dx`): a diagnosis may be listed as the explanation of a finding only when (a) its fired evidence covers the finding's defining analytes, or (b) the pair is in a curated cause→finding map (guideline-sourced per entry). A finding with no recognised cause in the panel keeps its own score and no `explained_by`; when a diagnosis ≥ 0.80 is present the finding ties with it (diagnosis listed first) but is never capped to 95 % of an unrelated entity. The same gate applies to the subsumption pass (diagnosis → finding). Diagnosis → diagnosis subsumption is unchanged.
- C12 *renal parsimony* (KDIGO 2012 chronicity): presumptive AKI by imputed baseline, zero chronicity markers, no documented CKD → CKD ≤ 0.49 (symmetric with the existing "documented CKD, no trajectory → AKI ≤ 0.49").
- C13 *non-thyroidal illness in acute care* (Fliers 2015; ATA/AACE 2012): ESL `nti_acute_care` — acute-care encounter, TSH 0.1–10 mIU/L with ≥ 1 supportive feature, no thyroid medication/history → `euthyroid_sick_syndrome_nontr` (pattern 0.80) with caps on central/subclinical thyroid diagnoses.
- C14 *urate grading* (ACR 2020; Cairo-Bishop): urate 7.0–9.0 mg/dL = pattern (0.80), ≥ 9.0 = strong (0.88); previously any value > 7.0 was 0.88.
- C15 *total calcium without albumin* (Cooper & Gittoes 2008): hypocalcaemia anchor/strong grades require albumin-corrected or ionised calcium; an uncorrected total calcium < 7.5 mg/dL is a pattern-grade finding.
- Causal-map entries added during the development gate are allowed (recorded in `ENGINE_CHANGES_v6.md`, v7 section); registry edits are not.

**Data status.** MIMIC-IV demo, Sepsis-2019 set B and NHANES H were opened in the Amendment 14 validation and are now *development* data. New quarantine (`eval/quarantine_v15/`, fetched by `fetch_q15.sh` before this amendment; never read by any script yet): NHANES 2015–2016 (cycle I) and Sepsis-2019 training set B2 = 5,000 set-B records disjoint from the Amendment 14 set-B subsample (`list_B2`).

**Development gate (must pass before freeze).** pytest full; hard batteries 1–3 no regression (151/151, 124/124, 77/78); healthy sweep 0 fires; perturbation fuzz no new breaks (≤ 3/755); eICU demo labs-only 2,314 stays **flat top-5 > 60.8 % and two-tier@3 ≥ 62.3 %** (14.1 values) — i.e. v7 must beat the previous engine on both the flat and the two-tier metric, not trade one for the other; MIMIC-IV demo (now dev) top-5 reported.

**Pre-stated success criteria on the quarantine (one run after `FREEZE_v15`, no re-tuning):**
1. NHANES I: diabetes, CKD, anaemia, iron-deficiency, hypercholesterolaemia, hyperuricaemia AUROC each within 0.03 of the NHANES H values of 14.1; healthy-subset false-flag rate ≤ 1 %.
2. Sepsis-2019 set B2 (5,000 records), concurrent framing, arm B: AUROC not lower than set B 14.1 (0.638) by more than 0.02; flag rate ≤ 20 %.
3. Safety: healthy 0/1000; fuzz no new breaks.
**Interpretation rule:** gate passed + criteria met → v7 reported as the shipped engine with 14.1.0, and the eICU/MIMIC gains are reported as *development* gains (not external validation of recall). Gate failed → v7 not shipped; 14.1/v6.1 remains. Both looks are reported verbatim either way.

*Amendment 15 — additions during the development gate (2026-10-25, quarantine still unopened).*
- C13 revised after the first 300-stay smoke: the syndrome fired on a NORMAL TSH with one inflammatory marker (ICU prevalence ≈ everyone); it now requires an abnormal thyroid test in the illness pattern (low T3 / FT4 < 0.9 with non-suppressed TSH; TSH 0.1–0.4; or recovery TSH 4.5–10). 
- C11 refinement: the explainer of a finding is the best-supported related diagnosis (analyte coverage **or** causal map); an explainer < 0.80 cannot pull a better-established finding beneath it (dev example: Hb 7.3 anaemia capped to 0.58 under a 0.61 'acute chest syndrome' leaf).
- C16 context guard `sickle_complication_context_guard` (NHLBI 2014; ASH 2020): acute chest syndrome / vaso-occlusive crisis capped at 0.3 unless sickle cell disease is documented or HbS is measured — a registry leaf (Hb < 9 + pO2 < 70) lacked the requirement; guard trigger Hb < 9 g/dL (the leaf threshold), after a healthy-panel unit test caught the first Hb < 13 version.
- **New pre-specified SECONDARY metric — "panel-supported recall"** (`eval/realdata/panel_supported_metric.py`): a clinician label counts only when its single guideline laboratory criterion is met in the input panel (thresholds = the syndrome-layer definitions, listed in the script; groups without a single criterion — sepsis, cirrhosis, GI bleeding, malnutrition, alcohol withdrawal — excluded). Rationale: admission-level eICU labels are frequently coded from values outside the first panel (dev examples: hypocalcaemia coded with albumin-corrected calcium 9.3; pancreatitis with lipase 158 U/L; hypothyroidism without a TSH). The flat metric stays primary for comparability with 13.3.0/13.4.2; the panel-supported metric is reported for every arm from the same per-stay files (no re-run; computed retrospectively for 13.4.2, v6, 14.1 and v7). First dev look (300 stays, before the gate): 14.1 flat 61.9 → panel-supported 85.3 % top-5 / 94.6 % top-10 (n = 204 of 362 labels; 48 not supported by the panel, 43 analyte absent, 67 excluded groups).

**Amendment 15 — development-gate outcome (2026-10-25, before FREEZE_v15).** Numeric gate NOT met (parity: eICU flat top-5 60.8 = 60.8; two-tier@3 62.0 vs 62.3; two-tier@1 33.1 vs 32.3; fuzz 753/755; healthy 0/1000; pytest 689/689 after one unit-test-caught guard fix). No recall improvement is claimed. v7 is retained as a correctness release at parity (false-attribution removal, context guards, grading); the quarantine criteria below are non-inferiority criteria and the shipped engine reverts to v6.1 if any fails. Full table: `eval/results/gate_v7/GATE_v7_RESULT.md`. Panel-supported secondary metric (all arms, retrospective from per-stay files): 13.4.2 81.6 / v6 77.8 / 14.1 78.0 / v7 78.0 % top-5 — the 13.4.2 margin is entirely CKD (single-creatinine chronicity, retained as KDIGO-correct) and leukocytosis-beneath-sepsis.

**Amendment 15 — quarantine outcome (2026-10-25, one shot after `FREEZE_v15_20261025`).** All three non-inferiority criteria met: NHANES I AUROC diabetes .924 / CKD .962 / anaemia .983 / iron deficiency .972 / hypercholesterolaemia .886 / hyperuricaemia .955 (largest deviation from H/J 0.018), healthy 0/79; Sepsis set B2 concurrent arm B .635 (.597–.673), flag 14.2 %; healthy 0/1000, fuzz 753/755. Secondary prediction framing on B2: .588 (logistic .679). Two data-preparation corrections (pid type; recomputed NHANES ACR column) are documented; no engine/registry/eval file changed after the freeze. v7 ships at recall parity with no improvement claim; full report `eval/results/validation_v15/VALIDATION_REPORT_v15.md`.
