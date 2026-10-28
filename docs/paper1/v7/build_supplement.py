"""Assemble the single Supplementary Information file for the CMPB submission (R8).

Order: cover/index · Note 1 SAP · Note 2 LLM protocol · Table S1 cohort flow · SUPPLEMENT_R1 (Notes 3–8, Tables S4–S16) ·
Note 8 addendum (second-rater attempts) · Notes 9–12 and 17 (from the manuscript tail) · TRIPOD+AI checklist.
Output: submission_CMPB/Supplementary_Information_R8.md and Supplementary_Information.docx (written to the submission package folder when present)
"""
import re, os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

V7 = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(V7, ".."))
SUP = os.path.join(P1, "supplement")
rd = lambda p: open(p, encoding="utf-8").read().strip()

man = rd(os.path.join(V7, "Paper1_Hemoglyph_CMPB_EN_v7_R9.md"))
notes_9_12 = man.split("## Supplementary information", 1)[1]
index_line = re.search(r"Notes: Note 1 SAP[^\n]*", notes_9_12).group(0)
notes_9_12 = notes_9_12.split("### Supplementary Note 9", 1)[1]
notes_9_12 = "### Supplementary Note 9" + notes_9_12

addendum = """## Supplementary Note 8 — Addendum (2026-10-27): rater statement

The audit reported in Note 8 and in main-text Section 3.2 is single-rater. The rater was an AI agent working under the first author's supervision; this is declared in the main text and in the GenAI declaration. The second-rater arm written into the protocol did not yield a dataset that met the protocol's validity rule (a CONCORDANT or DISCORDANT label must be supported by the verbatim source sentence containing the criterion) and is therefore not reported; no inter-rater reliability is claimed. For future runs the protocol requires a mandatory verbatim-quotation field with page or section for every non-UNRESOLVABLE verdict and a five-rule spot check against the sources for each rater before scoring."""

S1S2 = """## Supplementary Table S1 — Engine change log C1–C16 (registry 14.0.0 → 14.1.0, engine v6 → v7; all declared in SAP Amendments 14–15 before the corresponding quarantine run)

| ID | Date | Change | Guideline source | Trigger | Outcome-fitted? |
|---|---|---|---|---|---|
| C1 | 2026-10-24 | Two-tier output: entity kind ∈ diagnosis / laboratory finding / syndrome; top-k scored on diagnoses, findings always reported | — (output structure) | Amendment 14 closed list | no |
| C2 | 2026-10-24 | Syndrome layer: SIRS, qSOFA, SOFA sub-scores; sepsis asserted only as syndrome + laboratory support, otherwise "hyperlactataemia, cause undetermined"; `not_assessable` when anchor analytes absent | Sepsis-3 (Singer 2016); SSC 2021 | Amendment 14 closed list | no |
| C3 | 2026-10-24 | KDIGO chronicity: single creatinine → "renal impairment, chronicity undetermined"; CKD requires > 90-day persistence or chronicity markers; AKI requires KDIGO delta | KDIGO 2012/2024 | Amendment 14 closed list | no |
| C4 | 2026-10-24 | `n_of` operator; absent ≠ normal in `all` criteria | — (rule semantics) | Amendment 14 closed list | no |
| C5 | 2026-10-24 | Missing guideline patterns: alcohol-related liver pattern, R-ratio, bilirubin classification, septic shock, toxic alcohol (osmolal gap), MASLD/FIB-4, PSGN | each with a located source (registry) | Amendment 14 closed list | no |
| C6 | 2026-10-24 | Hypoglycaemia/hypocalcaemia threshold-unit fixes only if the 20-case audit shows an engine error; malnutrition → requires clinical data | GLIM | Amendment 14 closed list | no |
| — | 2026-10-24 | Unit aliases: UCUM `mm[Hg]`, `torr`, `/min`, `Cel`… (blood gases and blood pressures were silently dropped in every 13.x run) | UCUM | defect found by the 14.0.0 gate | no |
| C7 | 2026-10-25 | Screening-syndrome hits capped at 0.45 ("possible", non-anchoring); hypotension added as organ-dysfunction support | SSC 2021 (screen = prompt for evaluation); Sepsis-3 | development-set flag rate 26.1 % > 20 % — **declared openly as a development-set trigger**; rule content guideline-sourced | trigger yes, content no |
| C8 | 2026-10-25 | Explained findings sorted after self-standing asserted entities (probabilities unchanged) | — (ordering) | development error audit (displacement) | no |
| C9 | 2026-10-25 | Ischaemic-context MI syndrome (injury + ischaemia) | 4th UDMI; ESC 2023 rule-in | development error audit | no |
| C10 | 2026-10-25 | Single troponin > 99th URL → "myocardial injury, acuity undetermined"; acute injury requires rise/fall | 4th UDMI §3 | development error audit | no |
| v6.1 | 2026-10-25 | Anchor-strength constellation floor = full constellation vote (fusion asymmetry found by perturbation fuzz) | — (ordering principle anchor > strong > pattern) | synthetic fuzz, declared before any run | no |
| C11 | 2026-10-25 | Causal attribution map: a diagnosis explains a finding only if its fired evidence covers the finding's analytes or the pair is in a curated cause→finding map; explainer < 0.80 cannot pull a better-established finding beneath it | per-entry guideline sources (KDIGO, ADA, AHA/ACC, SSC, AASLD/EASL, ATA, ACOG 222, ASH) | Amendment 15 closed list | no |
| C12 | 2026-10-25 | Renal parsimony: presumptive AKI, zero chronicity markers, no documented CKD → CKD ≤ 0.49 | KDIGO 2012 | Amendment 15 closed list | no |
| C13 | 2026-10-25 | Non-thyroidal illness in acute care requires an abnormal thyroid test (low T3/FT4 with non-suppressed TSH; TSH 0.1–0.4; recovery TSH 4.5–10); revised after firing on a normal TSH in a 300-stay smoke | Fliers 2015; ATA/AACE 2012 | Amendment 15 closed list (+ dev smoke) | no |
| C14 | 2026-10-25 | Urate 7.0–9.0 mg/dL = pattern (0.80); ≥ 9.0 = strong (0.88) | ACR 2020; Cairo–Bishop | Amendment 15 closed list | no |
| C15 | 2026-10-25 | Hypocalcaemia anchor/strong grades require albumin-corrected or ionised calcium; uncorrected total calcium < 7.5 mg/dL = pattern | Cooper & Gittoes 2008 | Amendment 15 closed list | no |
| C16 | 2026-10-25 | Sickle-cell context guard: acute chest syndrome / vaso-occlusive crisis capped at 0.3 unless SCD documented or HbS measured | NHLBI 2014; ASH 2020 | Amendment 15 closed list | no |

Not allowed at any point (SAP Amendment 14): weights tuned to a dataset; rules written for a specific missed case; thresholds without a source. No registry edit after 14.1.0. The development-gate clause "flat top-3/5 not worse than 13.4.2" was **not** met by v6 (43.8/58.4 vs 49.3/63.7 %) and is recorded as such; C8–C10 recovered the loss to the same-engine control (60.8 vs 60.9 % at top-5).

## Supplementary Table S2 — Quarantine criteria and outcomes, rounds 1 and 2 (one run each, after SHA-256 freeze; no re-tuning after)

| Round / freeze | Criterion (pre-stated) | Threshold | Result | Met |
|---|---|---|---|---|
| 1 — `FREEZE_v14_20261025` (registry 14.1.0, engine v6.1) | MIMIC-IV demo, labs-only, lab-detectable coded diagnoses: top-5 / top-1 (primary) | ≥ 65 % / ≥ 45 % | 47.9 % / ≈ 18 % (control 13.3.0 registry, same engine: 50.1 %); difference driven by CKD recall 27.7 vs 50.8 % (KDIGO chronicity) | **no** |
| 1 | Sepsis-2019 set B (4,558 windows / 268 sepsis), concurrent, labs + vitals: AUROC (primary) | ≥ 0.65 | 0.638 (0.601–0.675); control 0.639 | **no** |
| 1 | set B flag rate in non-sepsis windows | ≤ 20 % | 16.1 % | yes |
| 1 | NHANES 2013–14 (H): diabetes, CKD, anaemia, iron-deficiency AUROC within 0.03 of NHANES J (13.3.0); CKD false positives not higher | 0.03 | all within 0.03; CKD false positives lower | yes |
| 1 | New PMC case reports: top-5 | ≥ 60 % | 68 % syndrome-level / 26 % specific (manual extraction) | partial (syndrome yes, specific no) |
| 1 | Safety: healthy false flags; fuzz | 0/40; 0/1000 | 0/40; fuzz 753/755 (2 pre-existing) | yes |
| Interpretation rule (round 1) | any primary missed → reported verbatim as failure; prior release remains headline | — | applied: no recall-improvement claim for 14.x | — |
| 2 — `FREEZE_v15_20261025` (registry 14.1.0, engine v7; criteria re-specified as non-inferiority in Amendment 15, dated after round 1 and before any round-2 file was opened) | NHANES 2015–16 (I): diabetes, CKD, anaemia, iron deficiency, hypercholesterolaemia, hyperuricaemia AUROC within 0.03 of H/J; healthy false flags | 0.03; ≤ 1 % | .924 / .962 / .983 / .972 / .886 / .955 (largest deviation 0.018); healthy 0/79 | yes |
| 2 | Sepsis-2019 set B2 (5,000 records disjoint from set B), concurrent arm B: AUROC not lower than set B (0.638) by more than 0.02; flag rate | −0.02; ≤ 20 % | 0.635 (0.597–0.673); 14.2 % | yes |
| 2 | Safety: healthy sweep; fuzz | 0/1000; no new breaks | 0/1000; 753/755 | yes |
| Interpretation rule (round 2) | criteria met → v7 ships as the frozen engine at parity, **no improvement claim**; eICU/MIMIC changes reported as development results | — | applied | — |

Because the criteria were weakened between rounds (superiority → non-inferiority), round 2 is supportive evidence of non-regression, not the confirmatory test originally planned (main text Section 2.5). Two data-preparation corrections after the round-2 freeze (participant-id type; recomputed NHANES ACR column) are documented in `eval/results/validation_v15/VALIDATION_REPORT_v15.md`; no engine, registry or evaluation file changed."""

S5 = "## Supplementary Table S5 — Next-test utility on category-A misses (eICU-CRD demo; computed on engine v5.3, 2026-10-23; metric defined in SAP Amendment 6; not re-run on v7 because the recommendation layer was unchanged by C1–C16 and the metric is reported for completeness only)\n\n" + rd(os.path.join(P1, "..", "..", "eval", "results", "eicu_demo", "next_test_utility_v5_3.md")).split("## Examples")[0].split("\n", 2)[2].strip()

FIGS = """## Supplementary Figures

![Fig. S1. Provenance audit of the shipped registry (14.1.0): source-locator classes and verification outcome per rule; see Note 8 for the sampled concordance audit.](../fig/src_fig08_provenance.png)

![Fig. S2. eICU-CRD demo (2,314 ICU stays, labs only): flat and two-tier top-k recall per engine/registry release, 13.4.2 → v7; identical inputs and label map.](../fig/src_fig02_eicu_versions.png)

![Fig. S3. Per-group recall@5 on panel-supported labels, frozen engine v7 (secondary metric defined after the ceiling was observed; see main text Section 3.4).](../fig/src_fig04_groups.png)

![Fig. S4. Per-group expected calibration error, raw scores vs cross-fitted isotonic recalibration (Table S6b).](../fig/src_fig09_calibration.png)

![Fig. S5. Context-echo analysis: the gain of the context arm is concentrated in labels that are restatements of documented history.](../fig/src_fig13_context_echo.png)

![Fig. S6. Participant flow for all evaluation cohorts (TRIPOD+AI 14a; counts in Table S3).](../../figures/figS1_participant_flow.png)"""


HYBRID = """

#### Note 9 addendum — hybrid arm and the limits of post-freeze improvement (declared experiment, 2026-10-27)

To test whether a trained layer on top of the frozen engine would raise recall, a 5-fold out-of-fold gradient-boosting probability per label group (identical inputs: raw analytes, age, sex) was combined with the frozen v7 group probability by a parameter-free rule, max(engine, ML). On the group-level metric (same 2,432 scorable labels) recall@5 was 58.8 % for the engine, 60.6 % for the hybrid (+1.8, 95 % bootstrap CI +1.2 to +2.5), 59.8 % when the ML term was allowed only for the six groups without a single-analyte criterion (+1.0), and 68.8 % for ML alone (+10.0). The ML-only gain comes from sepsis (94 %), diabetes (91 %) and CKD (65 %) — cohort priors learned from the labels — while ML loses most single-analyte groups (hyponatraemia 38 %, metabolic acidosis 12 %, hypomagnesaemia 3 %). A taxonomy of the engine's DKA misses (40 of 108) found only 2 panels meeting ADA criteria that the engine failed; 32 had bicarbonate ≥ 18 mmol/L or glucose < 250 mg/dL at the first panel (resolving or treated DKA) and 5 had glucose without acid–base data. Together with the earlier input arms (full in-window time series 63.7 → 63.2 %; documented history +2.9 points, mostly echo), these results indicate that the frozen figure is bounded by the reference standard rather than by rule content, and no post-freeze rule change was made (`eval/hybrid_arm.py`; `eval/results/eicu_demo/hybrid_arm_v7.md`).
"""


BLACKBOX = """## Supplementary Note 13 — Black-box property-conformance benchmark (engine and LLM on identical perturbed panels; declared 2026-10-27)

**Rationale.** The invariants of Section 2.3 run inside the engine's process. Four of them can be stated for any reader that maps a panel to a ranked list, so they were run as a black-box benchmark on real panels with the engine and the LLM of Note 2 receiving identical inputs. The panel generator, the scoring script and all metric definitions were committed before any reading was collected; predictions registered at that time were: LLM top-5 Jaccard 0.6–0.8 for P2/P3, engine violations 10–30 % for P4, LLM unsupported assertions 30–60 % for P5.

**Panels** (`eval/blackbox/make_property_panels.py`, seed 20261027; base stays drawn from the 400 already read blind, so no new label exposure). P2: 40 panels re-expressed in SI units (creatinine µmol/L, glucose/urea/calcium/magnesium/phosphate/lipids mmol/L, bilirubin µmol/L, haemoglobin/albumin/protein g/L, lactate mg/dL). P3: the same 40 with analyte order shuffled and up to five normal-valued distractors appended (MCV 89 fL, alkaline phosphatase 72 U/L, total protein 6.9 g/dL, chloride 102 mmol/L, TSH 1.8 mIU/L; a distractor was only added when the analyte id was absent, but two distractor ids were aliases of analytes already present, see Residuals). P4: 20 stays with baseline creatinine 0.6–1.3 mg/dL, each at ×1.0/×1.5/×2.0. P5: 40 stays in which a criterion-met diagnosis ranked ≤ 3 by the frozen engine; its defining analyte (for creatinine also urea) was removed; the reader never saw the target or the removed analyte. The healthy-adult property (P6) was not re-run because the earlier blinded NHANES 2017–18 test (40 guideline-healthy + 30 reference-positive adults, same reader) already covers it.

**Reads.** Engine: live run on each panel; reference for P2/P3 = live run on the conventional-unit twin built by the same generator (deterministic). LLM: the same agent-platform reader as Note 2, blind to labels, targets and removed analytes, returning ten named entries with probabilities, mapped to label groups by the synonym table of Note 2. The LLM reference for P2/P3 is its original blind reading from an earlier session, so its Jaccard includes test–retest variability (κ 0.69). For P4 the ladder step was visible to the LLM reader (the panel key carries it), so the LLM P4 row is not a blind result.

**Metrics** (`eval/blackbox/score_property_panels.py`). P2/P3: Jaccard of top-5 label-group sets versus the reference, share of identical sets, and the change in clinician-label recall@5. P4: share of ladders in which the best renal rank (acute kidney injury, renal impairment, CKD) worsens at any step. P5: share of panels in which the target group is still at rank ≤ 5; a post-hoc row (declared after the first scoring run) excludes panels in which a redundant analyte remained (haematocrit for haemoglobin, CK-MB/troponin T for troponin I, anion gap/pH/base excess for bicarbonate).

| Property (n) | Engine | LLM |
|---|---|---|
| P2 SI units: identical top-5 / mean Jaccard / label Δ (40) | 40/40 / 1.00 / 0 (v8.1 first run: 36/40 / 0.98) | 8/40 / 0.72 / +3 |
| P3 shuffle + distractors (40) | 35/40 / 0.96 / 0 | 10/40 / 0.73 / +3 |
| P4 monotonicity violations (20 ladders) | 2/20 | 0/20 (step visible) |
| P5 unsupported assertion (40) | 3/40 | 14/40 |
| P5, no redundant analyte left (29; post hoc) | 1/29 | 4/29 |
| Healthy adults, disease asserted at p ≥ 0.5 (40; NHANES 2017–18) | 0/40 | 4/40 |

**Defect found and fixed.** The first engine run gave 36/40 identical P2 sets. All four discrepancies traced to one cause: a record mirrored under an engine-internal legacy identifier (`bilirubin_total`) was not canonicalised because that identifier has no registry metadata, so a normal bilirubin of 9 µmol/L was compared with the 8 mg/dL panic threshold (false critical alert) and scored as high by the fuzzy and Bayesian layers (cholestasis 0.49 → 0.58). The in-process P2 test had not reached this path because it used glucose and creatinine. The fix resolves legacy identifiers to the registry feature they mirror before canonicalisation and before the panic check; a regression test (`tests/test_properties.py::test_p2_unit_invariance_legacy_alias_ids`, bilirubin/urea/phosphate in SI units) fails before and passes after the fix; the 705-test suite passes; the fix is in v8.2 and the frozen v7 results are unchanged.

**Residuals.** P3 engine 5/40: in three stays the alias distractors (`mcv` 89, `tsh` 1.8) duplicated an analyte already present under its canonical id with a different value (measured MCV 100.5 fL; TSH 4.7 and 4.3 mIU/L), so the perturbation was not value-preserving there; in two stays the differential had fewer than five entries and 0.15-probability items entered the top-5 set. P4 engine 2/20: at the ×2.0 step the renal cluster's best rank fell because the engine switched from "reduced GFR, chronicity undetermined" (anchor 0.92) to a lower-scored acute-kidney-injury entry; logged as a candidate for the next release, not changed. P5 engine 3/40: two anaemia panels with haematocrit present (supported) and one assertion of acute kidney injury with neither creatinine nor urea in the panel (a defect candidate). P5 LLM 14/40: ten with a redundant analyte present (eight anaemia with haematocrit, one myocardial infarction with CK-MB 28 ng/mL, one metabolic acidosis with anion gap 24.5); four without (three "diabetic ketoacidosis" from acid–base data alone, one heart failure without BNP).

**Interpretation.** The engine kept unit and presentation invariance where the LLM's ranking changed in most panels, and asserted the target without its defining analyte less often; but the LLM's P2/P3 figures are bounded by its own retest variability, the P4 LLM row is not blind, and the properties test consistency, not correctness. The practical difference is that an engine violation is a reproducible bug report (two were found here), whereas an LLM's changed answer is not actionable.

**LabPanel-Check (released package, `eval/labpanel_check/`).** The 180 perturbed eICU panels and their 40 conventional references, the 70 NHANES panels of the B5 blind test, the 31-group label map (entity ids and free-text regular expressions), a scorer that depends only on the Python standard library (`score.py`) and both reference readings are packaged so that any reader can be scored with one command; `tests/test_labpanel_check.py` asserts that the scorer reproduces every figure of this Note from the stored readings. The engine reference card was regenerated at package build with engine v8.2 and registry 15.2.0 and differs from the table above in one cell: P2 39/40 instead of 40/40. In the discordant pair (eICU stay 508973) the generator rounds creatinine 1.3 mg/dL to 115 µmol/L, which converts back to 1.3009 mg/dL and crosses the strict "> 1.3 mg/dL" leaf of rule `reduced_gfr_single_panel_v14`; the same leaf fired in the 2026-10-27 run, but acute kidney injury was then in both top-5 sets. All SI values in P2 are rounded (two decimals when the factor is below 1, integers otherwise; ≤ 0.1 % drift), so the package documents this and the scorer lists every non-identical pair. Two descriptive P6 detection rows also changed: engine CKD 10/18 (was 15/18) because registry 15.x caps single-panel CKD assertions below 0.5, and LLM iron deficiency 7/8 (was 8/8) because the original B5 script's match term was a bare string iterated character-wise, a scoring bug corrected on 2026-10-28; the 0/40 and 4/40 healthy-adult rows are unchanged.
"""

VERIFIER = """## Supplementary Note 14 — The engine's criteria as an executable verifier behind the LLM, and the verified-consensus arm (protocols committed 2026-10-27 before computation)

**Question.** Whether the guideline criteria already used by the panel-supported metric can serve as a deterministic verifier of an LLM differential drawn from the same panel, and what demoting unsupported entries costs in recall. No LLM call was made: the 400 stored blind readings of Note 2 were re-used.

**Verifier.** Each LLM entry is mapped to label groups by the frozen synonym map of Note 2 and receives one verdict: *supported* (criterion met in the panel), *contradicted* (defining analyte present, criterion not met), *absent* (defining analyte not in the panel), or *not verifiable* (no criterion for the group—sepsis, cirrhosis, GI bleeding, malnutrition, alcohol withdrawal—or no mapped group). An entry mapping to several groups is unsupported only if every verifiable group is unsupported. One key alias was added (the criterion function reads `inr`; panels store `international_normalized_ratio`); no threshold was changed. The same alias gap means the published panel-supported metric treated every coagulopathy label as analyte-missing and excluded it; the frozen numbers were not re-run, and the effect is confined to that one group.

**Arms and metrics.** A, LLM raw; B, unsupported entries demoted below all others with order preserved; C, unsupported entries removed; D, engine v7; E, the engine's own top-5 passed through the verifier. Recall@k against clinician labels (596, b8 rule) with stay-clustered bootstrap (4,000 resamples); unsupported-assertion rate among mapped, verifiable top-5 entries; verifier cost = demoted entries that were clinician labels. Registered predictions: LLM top-5 unsupported 15–30 %; after demotion < 5 %; recall@5 change −2 to +1 points; cost ≤ 10 %; engine top-5 unsupported 5–15 %.

**Results** (`eval/verifier/verify_llm_output.py`). Of 2,424 LLM entries: 1,439 supported, 182 contradicted, 15 absent, 263 not verifiable, 525 out of vocabulary. Top-5 unsupported: LLM 140/1,486 (9.4 %; 10 absent-type), engine 233/1,518 (15.3 %; 0 absent-type). After demotion 84/1,464 (5.7 %). Recall@1/3/5/10: A 28.2/50.8/59.6/65.1; B 29.4/50.3/59.4/65.1; C 29.4/50.2/58.4/63.8; D 24.0/47.0/60.7/72.0. Paired B − A: @1 +1.2 (95 % CI +0.2 to +2.3, p = 0.014); @5 −0.2 (−0.5 to 0.0, p = 0.75). Paired C − A: @5 −1.2 (−2.1 to −0.4, p = 0.001). Cost: 10/197 demoted entries were clinician labels (5.1 %)—stays 1278738 and 1772933 ("prerenal azotemia / GI bleeding", renal criterion not met, GI-bleeding group not verifiable), 294032 and 3086265 (respiratory acidosis matched by "acidosis" to the metabolic-acidosis group; bicarbonate 28.2 and 26.0), 2825782 (alcoholic ketoacidosis; withdrawal label not verifiable), 3131438 (stress hyperglycaemia, glucose 134), 2684065 (mild prerenal azotaemia, creatinine 0.94), 426975 (coagulopathy, INR 1.4), 310446 (DKA, bicarbonate absent), 2767923 (early DKA, bicarbonate 24). Post hoc: 34 of the LLM's 140 unsupported top-5 entries are respiratory-acidosis names; excluding them, 106/1,486 (7.1 %). Engine top-5 failures by group: diabetes 54/123 and hyperglycaemia 33/123 (the label groups contain hyperglycaemia identifiers while the criterion is glucose ≥ 200 mg/dL or HbA1c ≥ 6.5 %, and ≥ 140 mg/dL respectively), renal impairment 49/197 and acute kidney injury 39/170 (entries ranked from the urea:creatinine ratio at creatinine 0.9–1.2 mg/dL in men), hypocalcaemia 17/53 (albumin-corrected calcium), metabolic acidosis 13/85. Agreement between the criterion verdict and the engine's own differential (per mapped group with a criterion): both positive 1,685; criterion negative, engine positive 136; both negative 124; criterion positive, engine negative 51.

**Predictions.** Two of five met (recall change; cost). The LLM's raw rate was lower than predicted, the post-demotion rate higher than the < 5 % target (entries remain in the top-5 when a reading has fewer than five supported or non-verifiable entries), and the engine's rate was just above its range.

**Interpretation and limits.** The verifier removed 40 % of the LLM's unsupported top-5 assertions at no measurable recall cost and improved rank 1; removing rather than demoting costs about one point. The engine is not exempt: its own output fails the same proxy criteria more often than the LLM's, mostly where its rules are more permissive than the criterion (hyperglycaemia; prerenal patterns), but never without the defining analyte, which is the asymmetry the P5 property measured. The verdicts bound rather than measure unsupported assertion: the criteria are single-threshold proxies, the synonym map is coarse ("acidosis"), and 788 of 2,424 entries could not be verified at all. Nothing was tuned on these results; the thresholds and synonym map are those frozen for Table 5.

**Verified consensus arm (protocol committed separately before computation; `eval/consensus/verified_consensus.py`).** One parameter-free rule: B′ = LLM entries with verdict *supported*, in original order; F = reciprocal-rank fusion with k = 0, score(g) = 1/rank_engine(g) + 1/rank_B′(g), ties by engine rank; secondary G = engine list followed by B′ groups absent from it. Registered: F recall@5 63–67 %, recall@1 ≥ 29 %, F top-5 unsupported ≤ 15.3 %, G within 1 point of F; F < 62 % to be reported as "not complementary". Results, recall@1/3/5/10: engine 24.0/47.0/60.7/72.0; LLM 28.2/50.8/59.6/65.1; **F 21.8/46.6/61.2/76.3**; G 19.1/46.1/59.7/76.2. Paired F − engine: @1 −2.2 (95 % CI −4.9 to +0.5), @5 +0.6 (−2.2 to +3.4, p = 0.77), @10 +4.5 (+2.2 to +6.8, p = 0.0005); F − LLM: @1 −6.4 (−9.7 to −3.2), @5 +1.7 (−1.2 to +4.7, p = 0.27), @10 +11.3 (+7.9 to +14.8). Top-5 unsupported (per group): engine 233/1,518 (15.3 %), LLM 179/1,512 (11.8 %), F 209/1,581 (13.2 %), G 244/1,500 (16.3 %). Of F's 1,870 top-5 entries, 1,836 were already in the engine list and 34 were admitted through the LLM and the criterion only. recall@5 by label stratum (n): criterion met (357) engine 77.9 / LLM 81.0 / F 82.1 / G 77.9; no criterion (131) 51.9 / 43.5 / 42.7 / 46.6; criterion not met (107) 15.0 / 7.5 / 15.0 / 15.9. Only the unsupported-rate prediction was met; F fell below the 62 % rule and is reported as not complementary. Mechanism: the filter discards every LLM entry about a group without a criterion, so the second vote reaches only criterion-defined groups and the engine's constellation-ranked outcome syndromes (sepsis, bleeding, cirrhosis, withdrawal) are pushed down; the gain appears only at rank 10, where the longer fused list recovers labels. No second rule was tried; the negative result bounds what verifier-gated fusion can add on this reference standard.
"""

parts = [
    "# Supplementary Information\n\n*Verifying an AI-drafted laboratory-interpretation rule base before clinical audit: executable invariants, frozen source-concordance protocols and a hash-frozen benchmark applied to the open Hemoglyph engine — Bahrami, Tahmasebinejad, Bahrami Samani. Revision R9 (2026-10-28), Computer Methods and Programs in Biomedicine.*\n\n**Index.** " + index_line,
    "## Supplementary Note 1 — Statistical analysis plan and amendments\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "SAP_Hemoglyph_v1.md")), flags=re.M).replace("\n## ", "\n### "),
    S1S2,
    "## Supplementary Note 2 — LLM comparison protocol\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "LLM_COMPARISON_PROTOCOL.md")), flags=re.M).replace("\n## ", "\n### "),
    "## Supplementary Table S3 — Participant flow and baseline characteristics\n\n" + re.sub(r"^# ", "### ", rd(os.path.join(SUP, "TABLE_S1_cohort_flow.md")), flags=re.M).replace("\n## ", "\n### ").replace("### Table S1 —", "### Table S3 —"),
    S5,
    rd(os.path.join(SUP, "SUPPLEMENT_R1.md")).split("\n", 1)[1].strip(),
    addendum,
    notes_9_12.replace("### Supplementary Note", "## Supplementary Note").replace("\n## Supplementary Note 10", HYBRID + "\n## Supplementary Note 10", 1),
    BLACKBOX,
    VERIFIER,
    rd(os.path.join(V7, "submission_CMPB", "NOTE15_provenance.md")),
    rd(os.path.join(V7, "submission_CMPB", "NOTE16_audit_study.md")),
    rd(os.path.join(V7, "submission_CMPB", "NOTE18_verification_ledger.md")),
    rd(os.path.join(V7, "submission_CMPB", "NOTE19_human_audit_protocol.md")),
    rd(os.path.join(V7, "submission_CMPB", "NOTE20_heldout_mutation.md")),
    rd(os.path.join(V7, "submission_CMPB", "NOTE21_reproduction_log.md")),
    rd(os.path.join(V7, "submission_CMPB", "NOTE22_condensed_detail.md")),
    FIGS,
]
md = "\n\n".join(parts) + "\n"
md = md.replace("**Labels (rater 1 = AI agent, declared; rater 2 = human non-clinician co-author, pending).**", "**Labels (single rater: AI agent, declared; see Addendum).**")
md = md.replace("GPT-4-class general-purpose model accessed through the Arena.ai Agent Mode interface; model identity withheld", "frontier-tier general-purpose LLM accessed through the Arena.ai Agent Mode interface; model identity not disclosed by the platform and withheld")
md = md.replace("![Fig S](../v7/fig/Fig6_llm_v51.png)", "(figure withdrawn in R8: the superseded numbers are in Table S12b)")
md = md.replace("## Supplementary Figure S — Historical LLM comparison against the superseded engine v5.1", "## Supplementary Table S12b addendum — Historical LLM comparison against the superseded engine v5.1 (text only; superseded)")
md = md.replace("Supplementary Fig. S1 (figS1_participant_flow.png)", "Supplementary Fig. S6 (participant flow)")
md = md.replace("Table S1 (TABLE_S1_cohort_flow.md)", "Table S3 (cohort flow)")

# ---- de-clutter: internal report/data file names are removed; scripts (.py/.sh) and the audit protocol are kept
_KEEP = ("PROTOCOL.md",)
def _strip_files(s):
    pat = re.compile(r"`([^`\n]*?\.(?:md|json|json\.gz|csv|csv\.gz|txt|xlsx|log)(?:/\.json)?)`")
    def rep(m):
        return m.group(0) if any(k in m.group(1) for k in _KEEP) else ""
    s = pat.sub(rep, s)
    s = re.sub(r"; script (?=`)", "; script ", s)
    s = re.sub(r"\((?:[ \t]*[;,][ \t]*)+", "(", s)
    s = re.sub(r"\([ \t]*\)", "", s)
    s = re.sub(r"\([ \t]*[;,]?[ \t]*(?=[^()\n]*\))", "(", s)
    s = re.sub(r"[ \t]+([;,.)])", r"\1", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\([ \t]*[;,][ \t]*", "(", s)
    s = re.sub(r"[;,][ \t]*\)", ")", s)
    s = s.replace("Full-length Methods and Results text of revision R5 (verbatim; condensed in the main text for length —", "Full-length Methods and Results text of revision R5 (verbatim; condensed in the main text for length —")
    return s
# apply to everything except Note 1 (the SAP is a dated protocol document and is reproduced verbatim) and Note 12 (verbatim R5)
_keep_verbatim = re.compile(r"(## Supplementary Note 1 — .*?)(?=\n## Supplementary Table S1 —)|(## Supplementary Note 12 — .*?)(?=\n## Supplementary Figures)", re.S)
_blocks = []
def _hold(m):
    _blocks.append(m.group(0)); return f"@@HOLD{len(_blocks)-1}@@"
md = _keep_verbatim.sub(_hold, md)
md = _strip_files(md)
for i, b in enumerate(_blocks):
    md = md.replace(f"@@HOLD{i}@@", b)

REPRO = """## Supplementary Table S17 — Reproducibility and version map

Every number in the main text and in this file is produced by a script in the public repository from a hash-frozen engine and registry (SHA-256 manifests `FREEZE_v15_20261025`; Note 6). Internal report file names are omitted throughout; the table below is the single place that links each item to its generating script and input.

| Item | Script (repository path) | Input data | Engine / registry |
|---|---|---|---|
| Table 3, Fig. 2, Fig. S2, Table S4, Table S6–S6c, Table S8, Table S11 | `eval/realdata/eval_eicu.py` (`--encounter icu`), `eval/realdata/panel_supported_metric.py`, `eval/subgroup_fairness.py`, `eval/reviewer_r2_metrics.py`, `eval/calibration_dca.py` | eICU-CRD demo v2.0.1 (2,314 ICU stays) | v7 / 14.1.0 |
| Table 5, Fig. 7, Note 2, Table S12b | `eval/baselines/llm_zero_shot.py`, `b8_score.py`, `b8_v7_cluster.py`, `b8_rank_metrics.py`, `b8_prompt_sensitivity.py` | 400 blinded eICU panels (Data 1) | v7 / 14.1.0 (historical: v5.1) |
| Table 1 | `eval/ablation/run_ablation.py` | eICU-CRD demo | v7 / 14.1.0 |
| Fig. 8, Table S6–S6c | `eval/calibration_dca.py` outputs (`eval/results/eicu_demo/calibration_dca_v7.md`, `reviewer_b5_calibration_v7.json`) | eICU-CRD demo (2,314 stays; 52,689 label scores) | v7 / 14.1.0 |
| Fig. 3 | `docs/paper1/v7/make_figures_R8.py` reading the frozen outputs of Notes 8, 15, 16 and 18 (no new measurement) | — | 14.1.0 (a, b); 15.1.0 (c); 15.2.0 (d) |
| Figs. 1–8 (rendering only) | `docs/paper1/v7/make_figures_R8.py` (reads `eval/results/eicu_demo/{ml_baseline.json, llm_vs_v7_cluster_n400.json, calibration_dca_v7.md}` and `eval/verification_ledger/ledger_counts.json`; NHANES, sepsis and recall values are transcribed from the frozen reports of the rows above and asserted against them in the script's constants) | frozen result files listed in this table | as per source row |
| Note 20 | `eval/audit/PROTOCOL_HELDOUT.md`, `mutate_heldout.py` (seed 20261028) | registry 15.3.0 (300 AI-drafted rules); second LLM-written corpus (400 rules) | detectors frozen; registry 15.3.0 (no v7 metric affected) |
| Note 21, Table S18 | `reproduce.sh` (modes `quick`, `v7`, `eicu`, `all`), `tools/make_frozen_engine_dir.py`, `tools/compare_reports.py`; `eval/source_audit/auditability_metrics.py` (reads the committed Note 8 files) | clean `git clone` of the repository; NHANES 2017–18; eICU-CRD demo | git tag `engine-v7-frozen`; registries 14.1.0, 15.1.0, 15.3.0 |
| Note 19 (protocol only; no result) | `eval/audit/human_audit/sample_rules.py`; frozen sample `human_audit_sample_100.csv` (seed 20261028; SHA-256 in `SHA256SUMS`) | verification ledger at 15.2.0 | 15.2.0 |
| Table 4, Fig. 5, Fig. 4 (ML baseline: `eval/baselines/ml_baseline_eicu.py`), Table S7, Table S13, Note 10 | `eval/realdata/eval_nhanes.py`, `eval_uci_thyroid.py`, `eval_uci_hcv.py`, `eval_ilpd.py`, `eval_pmc_cases.py`, `eval/mimic/run_retrospective.py` | NHANES H/I/J, UCI thyroid0387, UCI HCV, ILPD, MIMIC-IV demo, PMC case reports | v7 / 14.1.0 |
| Fig. 6, Table S16 | `eval/realdata/eval_sepsis2019.py`, `eval_sepsis2019_concurrent.py`, `eval/sepsis_ml/sepsis_risk_module.py` | PhysioNet Sepsis-2019 sets A, B, B2 | v7 / 14.1.0 |
| Section 3.1, Note 4 | `tests/test_properties.py`, `tests/test_bayes_properties.py`, `tests/hard_battery.py`, `hard_battery2.py`, `hard_battery3.py`, `tests/healthy_sweep.py`, `tests/perturbation_fuzz.py` | synthetic panels (seeded) | v7, v8, v8.1 |
| Section 3.7, Table 6, Note 13 | `eval/blackbox/make_property_panels.py`, `eval/blackbox/score_property_panels.py`; package `eval/labpanel_check/score.py` (`build_package.py`); healthy-adult row: `eval/baselines/b5_nhanes_blind.py` | 40/40/60/40 perturbed eICU panels from the 400 blinded stays; NHANES 2017–18 | v8.1 (first run) and v8.2; LLM as Note 2 |
| Section 3.7, Table 7, Note 14 | `eval/verifier/verify_llm_output.py`, `eval/consensus/verified_consensus.py` (protocols `PROTOCOL.md` in each folder) | the 400 blind LLM readings and engine v7 outputs of Table 5 | v7; no new LLM call |
| Section 3.2, Fig. S1, Note 8, Table S10 | `eval/source_audit/PROTOCOL.md` with the frozen sample `eval/source_audit/sample_200.csv` (seed 20261026), `eval/registry_source_verify.py` | registry 14.1.0 (seed 20261026) | 14.1.0 |
| Section 3.3, Note 15 | `eval/provenance/PROTOCOL.md`, `eval/provenance/activity_log.py`, `core_analysis.py`, `resource_core.py`; frozen sample `eval/provenance/phase_c_sample_100.csv` (seed 20261028) | eICU-CRD demo first panels; NHANES 2015–16 and 2017–18 | registry 14.2.0; harness v8.2 (activity only; no v7 metric affected) |
| Section 3.8, Note 16 | `eval/audit/PROTOCOL_AUDIT.md`, `make_core_registry.py`, `audit.py`, `mutate.py`, `convert_llm_corpus.py`; CORE arm re-runs with `eval/realdata/eval_eicu.py --encounter icu` and `eval/realdata/eval_nhanes.py --n-max 1000 --encounter community`; paired comparison as for the 15.1.0 gate | eICU-CRD demo (2,314 stays); NHANES 2017–18 (1,000 adults); registries 14.1.0 and 15.1.0; second LLM-written corpus (400 rules, hash-frozen) | registry 15.1.0 vs its 335-rule audited core, engine v8.2 in both arms (development; no v7 metric affected) |
| Section 3.8, Note 18 | `eval/verification_ledger/build_ledger.py` (join only; inputs are the frozen outputs of Notes 8, 15, 16, `eval/audit/audit.py` and `tests/test_properties.py`); `tests/test_verification_ledger.py` | none (no data touched) | registries 14.1.0, 15.1.0, 15.2.0 (no metric affected) |
| Note 18, release 15.3.0 | `eval/registry_patches/PROTOCOL_15_3_0.md`, `patch_15_3_0.py`, `gate_compare.py _r1520 _r1530`; gate re-runs as for 15.1.0 | eICU-CRD demo (2,314 stays); NHANES 2017–18 (1,000 adults) | registry 15.2.0 vs 15.3.0, engine v8.2 (development; no v7 metric affected) |
| Note 16, release 15.2.0 | `eval/registry_patches/PROTOCOL_15_2_0.md`, `patch_15_2_0.py`, `gate_compare.py`; gate re-runs as for 15.1.0 | eICU-CRD demo (2,314 stays); NHANES 2017–18 (1,000 adults) | registry 15.1.0 vs 15.2.0, engine v8.2 (development; no v7 metric affected) |
| Note 15, post-audit release | `eval/registry_patches/PROTOCOL_15_0_0.md`, `patch_15_0_0.py`; gate re-runs with `eval/realdata/eval_eicu.py --encounter icu`, `eval/realdata/eval_nhanes.py --n-max 1000 --encounter community`, `eval/provenance/activity_log.py --corpus eicu` | eICU-CRD demo (2,314 stays); NHANES 2017–18 (1,000 adults) | registry 14.2.0 vs 15.0.0, engine v8.2 in both arms (development; no v7 metric affected) |
| Table S1, Table S2, Note 1 | SAP document (dated amendments); freeze manifests | — | 14.0.0 → 14.1.0; v6 → v7 |
| Table S5 | `eval/next_test_utility.py` | eICU-CRD demo audit sample | v5.3 (superseded) |
| Table S9 | `eval/label_audit_300.py` (seed 11; the first 100 stays by the author adjudication described in Table S9) | 400 eICU stays | v7 |
| Fig. S5 | `eval/deep_review_ctx_sex.py` | eICU-CRD demo, context arm | v5.2 |
"""
S18 = rd(os.path.join(P1, "..", "..", "eval", "source_audit", "auditability_metrics.md"))
md = md.replace("## Supplementary Figures", REPRO + "\n" + S18 + "\n\n## Supplementary Figures", 1)

os.makedirs(os.path.join(V7, "submission_CMPB"), exist_ok=True)
open(os.path.join(V7, "submission_CMPB", "Supplementary_Information_R8.md"), "w", encoding="utf-8").write(md)

import sys; sys.path.insert(0, V7)
from docx_style import setup_document, inline, add_table, heading
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
doc = Document()
setup_document(doc, body_size=11, line_spacing=1.5, margins_cm=2.5, line_numbers=False, page_numbers=True, heading_sizes=(13, 12, 11, 11), space_after=4)

lines = md.split("\n"); i = 0
while i < len(lines):
    l = lines[i]
    if l.startswith("# "):
        p = doc.add_paragraph(); inline(p, l[2:], 16); p.runs[0].bold = True; p.paragraph_format.line_spacing = 1.3
    elif l.startswith("## "): heading(doc, l[3:], 1)
    elif l.startswith("### "): heading(doc, l[4:], 2)
    elif l.startswith("#### ") or l.startswith("##### "): heading(doc, l.lstrip("#").strip(), 3)
    elif l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
        add_table(doc, rows, 8); doc.add_paragraph(); continue
    elif l.startswith("!["):
        m = re.match(r"!\[(.*)\]\((.*)\)", l); cap, src = m.group(1), os.path.join(V7, "submission_CMPB", m.group(2))
        pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER; pic.add_run().add_picture(src, width=Cm(16))
        p = doc.add_paragraph(); inline(p, cap, 10); p.paragraph_format.line_spacing = 1.15
    elif l.startswith("```"):
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            p = doc.add_paragraph(); inline(p, "`" + lines[i] + "`", 9); p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0; i += 1
    elif l.strip() == "":
        pass
    elif re.match(r"^\s*[-*] ", l):
        p = doc.add_paragraph(style="List Bullet"); inline(p, re.sub(r"^\s*[-*] ", "", l)); p.paragraph_format.space_after = Pt(2)
    else:
        p = doc.add_paragraph(); inline(p, l)
    i += 1
PKG = os.path.join(V7, "..", "..", "..", "..", "ارسال پیپر ۱")
out = os.path.join(PKG, "Supplementary_Information.docx") if os.path.isdir(PKG) else os.path.join(V7, "submission_CMPB", "Supplementary_Information.docx")
doc.save(out)
print("supplement ok:", out, "| words", len(md.split()))
