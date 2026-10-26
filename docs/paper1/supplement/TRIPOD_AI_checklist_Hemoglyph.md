# TRIPOD+AI (BMJ 2024;385:e078378) checklist — Hemoglyph Paper 1 (updated 2026-10-24, engine v5.3 / registry 13.3.0)

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
