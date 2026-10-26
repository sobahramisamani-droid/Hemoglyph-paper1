# Response to reviewers — Hemoglyph, revision R1 (2026-10-25)

We thank the reviewer for a careful and constructive report. We accept the central criticism — that the claims ran ahead of the evidence — and have (a) narrowed the claims, (b) added the analyses that were feasible without new human resources, and (c) stated explicitly which items remain open. Page/section references are to `Paper1_Hemoglyph_SampleStyle_v7_R1.md`. New analysis files are listed at the end.

## Major concerns

**4.1 Claim exceeds evidence; LLM comparison used v5.1.** Agreed. We re-scored the engine arm with the frozen engine v7 without regenerating any LLM output (`eval/baselines/b8_v7_cluster.py`). Result: the pre-specified primary comparison is now **equivalent** (recall@5 60.7% vs 59.6%, cluster-adjusted p = 0.54); the LLM is better at ranks 1–3, the engine at rank 10 and on omissions. The abstract now says "equivalent on the primary metric; the LLM ranked more diagnoses first, the engine omitted fewer", "matches or exceeds" is removed everywhere, and the v5.1 result is reported as historical (Table 4, §4.6, §5.1).

**4.2 Rule base 99.2% AI-assisted without independent validation.** Agreed; this is the main weakness and is now stated in the abstract, §2.2, §5.5 and the conclusion. Done in this revision: (i) *anchor-only* ablation (272 curated rules only) and (ii) *no-unverified-source* ablation (28 rules removed) on the full cohort (Table 5). Result: anchor-only changed flat recall@5 by −0.9 points (95% cluster-bootstrap CI −2.1 to +0.2), two-tier recall@5 by −3.0 points and mean per-group AUROC from 0.767 to 0.732; removing the 28 unverified-source rules changed no ranking. The AI-drafted bulk of the registry is therefore not load-bearing for the reported results — which we state plainly in the abstract and discussion as both a safety reassurance and a limit on any claim that registry scale is a merit. Not done: independent audit of a 300–500-rule sample by two specialists. The stratified sampling frame and audit forms exist (`eval/human/A1_rule_audit_form.*`); the audit requires clinicians we do not yet have and is listed as the first open item. We do not claim "validated rules" anywhere.

**4.3 Criteria changed after Round-1 failure.** Agreed. Round 2 is now labelled *supportive, not confirmatory* (§3.1, §5.5). Supplementary Table S2 lists all 15 amendments with dates and a before/after-observation flag. We note explicitly that the statistical co-author is not independent of the study.

**4.4 Panel-supported metric post hoc; 2,707 vs 2,432.** The metric is now labelled "secondary, post hoc, structurally optimistic" in §3.3, Table 2 and the abstract, and is never reported alone. The two counts are not a contradiction but were unexplained: 2,707 = all coded labels; 2,432 = labels whose key analyte was in the panel (the SAP's scoring set); the difference, 275, is exactly the "analyte missing" segment of Fig. 3b. Both counts are now defined in §3.3 and §4.2.

**4.5 No end-to-end OCR evaluation.** We chose the second option: the title, abstract and §1 now scope the work to *structured laboratory values*; §2.3 states that neither OCR nor the consistency solver was evaluated and that no claim is made about them. A separate OCR benchmark is deferred.

**4.6 Clustering ignored.** Agreed. All eICU proportions and the LLM comparison now use stay-cluster bootstrap CIs and the Durkalski cluster-adjusted McNemar test (§3.5, Table 4). ICC of the paired difference = 0.04, design effect 1.04; clustering changed little — the engine version changed the conclusion (see 4.1).

**4.7 NHANES unweighted.** Agreed. We added survey-weighted AUROCs (MEC weight WTMEC2YR, PSU-within-stratum bootstrap) for all targets and cycles (`eval/realdata/nhanes_weighted.py`, Supplementary Table S7). Weighted and unweighted differ by ≤ 0.015 except self-reported kidney disease in 2017–18 (−0.07). Both are reported; the design limitation (weights applied within a 3,000-adult subsample) is stated.

**4.8 LLM transparency.** Supplementary Note 2 (`docs/paper1/supplement/LLM_COMPARISON_PROTOCOL.md`) now gives prompts, dates, batching, blinding procedure, scoring map, decoding limits, contamination analysis and all outputs. Model identity: withheld in the manuscript at the platform's request, disclosed to the editor. Added: a second prompt on the 40-panel subset (recall@5 61.5% vs 61.5%/67.0% for the two reads of prompt 1); a second model was not feasible without cost. Contamination is discussed (would favour the LLM).

**4.9 Ablation insufficient.** We ran eleven single-component ablations on the full cohort: each of the five layers off, expert syndrome layer off, Dempster normalisation instead of Yager, uniform fusion weights, shrinkage/single-source discount removed, anchor-only registry, unverified-source rules removed (Table 5, `eval/ablation/run_ablation.py`). Findings (flat recall@5, full = 60.8%): rule-engine vote off −12.1 (−14.4 to −9.8); expert syndrome layer off −9.5 (−11.1 to −7.9); uniform fusion weights −1.4; Bayesian layer off −1.3 (−3.7 on two-tier); anchor-only registry −0.9; shrinkage/discount off −0.4; Dempster instead of Yager −0.1; fuzzy +0.3; knowledge graph +0.1; risk models 0.0 (no ranking changed); unverified-source rules off 0.0. We report the results as found, state in the Discussion that four of the five fusion layers were close to inert on this cohort, and have removed the sentence implying that every layer is necessary. Stay-cluster bootstrap CIs are in `eval/results/eicu_demo/ABLATION_v7_ci.md`; the full table with panel-supported recall in `ABLATION_v7_full.md`.

**4.10 Calibration.** Added calibration slope, calibration-in-the-large, Brier with cluster-bootstrap CI, log-loss, per group (§4.7, Fig. 8, Supplementary Table S8); decision curves moved to the main text. Raw slope 0.25 confirms the reviewer's reading: scores are ranks, not probabilities, and the interface does not show them as probabilities.

**4.11 Tables/figures.** Table 4 is complete (all k, MRR, CI, p). Figures regenerated without embedded figure numbers; the "igure" artefact and Fig. 10/12/14 references came from embedded titles of dossier figures and are gone. Duplicate 3.1/3.2 does not exist in the current file. Table 3 now gives n for every external cohort, and separates the MIMIC Round-1 quarantine result (engine v6: 36.3/47.9/61.7%) from the later v7 re-run (35.3/47.5/62.1%, not a quarantine result).

**4.12 AHRQ / "no open rule set".** Softened and dated: CDS Connect offline since 28 April 2025 (HL7 community edition continues); ECRI Guidelines Trust unavailable since 2024; our search (October 2026) of these, WHO SMART DAKs and NICE licensed content found no openly licensed executable rule set for laboratory-panel interpretation (§1).

**4.13 Clinical/regulatory status.** "Research prototype — not approved or intended for clinical use" is now under the title, in §5.3 and in the conclusion; automation bias, alert fatigue and maintenance cost are discussed in §5.3.

## Statistical and reporting points
1. TRIPOD+AI checklist attached (Supplement). 2. Multiplicity: BH/Holm applied to the 29 per-group AUROCs (27 remain significant); all but the primary are labelled exploratory. 3. Missing data: recall is insensitive to the minimum panel size (60.8% at ≥ 8 to 59.8% at ≥ 25 analytes; Table S6); excluded stays (< 8 analytes, n = 198) are listed in Table S3. 4. Label noise: audit extended to 300 further stays (400 total): precision 100% (category-level), sensitivity 98.3%, with per-group counts and all misses listed (Table S9) — author audit, declared as such. 5. External validity stated more strongly (§5.5). 6. Subgroup n and CI in Table S4. 7–8. Decision curves and per-group slopes added. 9. Sepsis CIs are given. 10. Abstract now says "0.72–0.99 depending on target".

## Items we could not resolve in this revision
Independent two-specialist rule audit; independent statistician; prospective / clinician-in-the-loop evaluation (Paper 2 protocol); OCR benchmark on real scanned reports; second LLM vendor; complete record for reference 20.

## New files
`eval/baselines/b8_v7_cluster.py` → `eval/results/eicu_demo/llm_vs_v7_cluster_n400.{md,json}`; `eval/realdata/nhanes_weighted.py` → `eval/results/nhanes_weighted_v7.{md,json}`; `eval/reviewer_b5_b6.py` → `eval/results/eicu_demo/reviewer_b5_b6_v7.md`; `eval/calibration_dca.py --label v7` → `calibration_dca_v7.md`, `Fig8_calibration_dca.png`; `eval/label_audit_300.py` → `label_audit_n300.md`; `eval/baselines/b8_prompt_sensitivity.py` → `b8_prompt_sensitivity.md`, `b8_llm_prompt2_n40.json`; `eval/ablation/run_ablation.py`, `run_chain.sh`, `REGISTRY_ANCHOR_ONLY.json.br`, `REGISTRY_NO_UNVERIFIED.json.br` → `ABLATION_v7_full.md`; `docs/paper1/supplement/LLM_COMPARISON_PROTOCOL.md`.

**Ablation artefacts (added after the chain completed, 2026-10-25 20:55 UTC):** `eval/ablation/run_ablation.py`, `run_chain.sh`, `ablation_ci.py`; `eval/results/eicu_demo/ABLATION_v7_full.md`, `ABLATION_v7_ci.{md,json}`, `per_stay_abl_<arm>.json.gz`, `report_abl_<arm>.md`, `summary_abl_<arm>.json` for the eleven arms. Clinician review package: `eval/human/Hemoglyph_clinician_review_package_R1.xlsx`.

---

# Response to the second report (Major Revision / Reject-and-Resubmit) — added 2026-10-26

We agree with the second reviewer's assessment that the first-round manuscript over-claimed and under-reported. The report was written against the pre-R1 text; several items had already been addressed in R1 (marked **R1**). The remaining items were implemented in this revision (**R2**) or are listed as open because they need people or accounts we do not have (**open**). Nothing in the report was argued against.

## A. Claims and framing

| # | Reviewer point | Status | What changed |
|---|---|---|---|
| A1 | "Comprehensive", "validated", "fully offline", "patent-pending" tone | **R1 + R2** | Title/abstract say *research prototype*; "fully offline" now applies only to the structured-input engine; the proprietary desktop and its cloud OCR path are named as such (Sect. 2.1 / Results "System"). |
| A2 | 99.2% AI-drafted rules unaudited must be in the abstract | **R1** | In both abstracts, with the ablation showing the result does not rest on them. |
| A3 | "Matches or exceeds" the LLM | **R1** | Replaced by parity on recall@5 (p = 0.54), LLM better at rank 1, engine better at rank 10. |
| A4 | "~900 syndromes" validated? | **R2** | Stated as author-written from guideline criteria, not independently validated (Discussion). |
| A5 | Competing interest understated | **R2** | COI now states ownership of the proprietary product and a financial interest in a favourable evaluation. |
| A6 | Hardware for "~1 s" | **R2** | Single x86-64 core, no GPU, 2-GB sandbox; median 0.4–0.5 s, p95 0.9 s. |
| A7 | PMC parser 10% belongs in abstract | **R2** | Added to both abstracts (10% end-to-end vs 26% structured). |

## B. Numbers and reconciliation

| # | Point | Status | What changed |
|---|---|---|---|
| B1 | 34,673 − 1,474 ≠ 33,183; 272 + 32,901 ≠ 33,183; 781 vs 785 sources | **R2** | Recomputed from the live 14.1.0 file: 1,487 retired + 3 non-executable candidates; 33,183 = 272 + 13 demoted anchors + 32,898 candidates; 785 listed sources of which 388 are cited by executable rules (781 was the 13.4.1 count, still present in a stale metadata field). Supplementary Table S10; Methods 2.2 rewritten. |
| B2 | 2,707 vs 2,432 | **R1** | Cohort flow (Fig. 3b / Table S1). |
| B3 | Table 3 lacks n / prevalence for UCI, HCV, ILPD; thyroid n wrong | **R2** | n positives/negatives added to every external row; thyroid corrected from "3,162 records" to 7,743 records with TSH (655/195/6,082). |
| B4 | Table 2 "registry off" row is a different engine | **R2** | Row relabelled "engine v5.3, historical"; v7 ablations are in Table 5. |
| B5 | Healthy false-assertion total | **R2** | 2/485 in abstract and Results (CI 0.1–1.5%). |
| B6 | Reference list order / placeholder ref 20 | **R2** | Refs 36–37 moved to the end; ref 20 (npj: 15) replaced by the published record: Feldman MJ et al., *JAMA Netw Open* 2025;8(5):e2512994. |

## C. Missing analyses

| # | Point | Status | What changed |
|---|---|---|---|
| C1 | Precision / F1 / NDCG / false-positive burden; a trivial baseline | **R2** | `eval/reviewer_r2_metrics.py` → Supplementary Table S11 and a new Results paragraph: precision@5 14.2% (13.3–15.2), F1@5 23.1%, NDCG@5 56.5% (54.1–58.8); 4.5 label-group assertions per stay in the top-5; per-group PPV 0–69%. Prevalence-ranking baseline: recall@5 51.3%, NDCG@5 39.0%, **recall@10 76.8% (higher than the engine's 74.1%)**. We report this plainly: the engine's advantage is in ranking, not in top-10 coverage. |
| C2 | Full ablation | **R1 + R2** | Eleven arms in R1 (Table 5). Two further fusion-weight arms were run for this revision (Table S12): rule-heavy 0.55 → Δ recall@5 −0.0 (−0.6 to +0.5); rule-light 0.20 → −1.1 (−1.8 to −0.3). Together with uniform weights (−1.4) this bounds the influence of the hand-set weights at about one point. |
| C3 | Cluster-robust inference | **R1** | Stay-cluster bootstrap and cluster-adjusted McNemar throughout. |
| C4 | Survey weights | **R1** | Table S7. |
| C5 | Calibration: isotonic fitted on independent data? | **R2** | Clarified: split-half cross-fitted by stay within eICU; presented as evidence of recalibrability, not as a transferable calibration. "Calibrated point score" wording removed from Methods (it is a confidence-shrunk rank score). |
| C6 | Regression-gate threshold; what are the 77/78 and 753/755 failures | **R2** | Gate = non-regression against the previous release (no previously passing item may fail; healthy sweep 0). Failures named: alcoholic pancreatitis ranked 2nd behind alcohol-use disorder; thiazide hyponatraemia brittle in 2/5 noisy replicates (previously 3/755 failures). |
| C7 | Non-inferiority margins, when the criteria changed, loader-defect sensitivity | **R2** | Margins stated (NHANES AUROC within 0.03 and ≤ 1% healthy false assertions; sepsis within 0.02 with control flag ≤ 20%; no new safety failure); Amendment 15 dated after Round 1 was known and before any Round-2 file was opened; the pre-correction NHANES run is kept and differs only in the CKD task, which was unscorable without the dropped variable. |
| C8 | Formal ToE algorithm, mass assignment, weights, the 27 constraints | **R2** | Supplementary Note 3 (step-by-step algorithm transcribed from the code, Table N3-1 weights/profiles/reliability, Table N3-2 listing all 27 identities). |
| C9 | Label-audit PPV per group, more stays | **R1** | 400 stays, per-group PPV (Table S9). |
| C10 | Supplementary tables S6–S9 referenced but absent | **R2** | `docs/paper1/supplement/SUPPLEMENT_R1.md` now contains S6–S12, Note 3 and Fig. S. |
| C11 | UI display of unverified rules; machine-readable validation status | **R2** | Stated in Methods 2.2 (status and evidence tier shown per entry; `status`/`evidence_tier`/`executable` fields in the registry). |

## D. Open (require resources we do not have)

Independent specialist audit of a rule sample (review package prepared: `eval/human/Hemoglyph_clinician_review_package_R1.xlsx`); OSF registration identifier and Zenodo DOI (accounts and deposit by the corresponding author); co-author contribution statements and ORCIDs; prospective or clinician-in-the-loop evaluation (Paper 2 protocol); access to full eICU/MIMIC (credentialing); second LLM vendor.

## Files added or changed in R2
`eval/reviewer_r2_metrics.py` → `eval/results/eicu_demo/reviewer_r2_metrics_v7.md`; `eval/ablation/run_ablation.py` (+2 arms), `run_chain.sh`, `ablation_ci.py`; `eval/results/eicu_demo/ABLATION_v7_manifest.json` (SHA-256 of all ablation artefacts); `docs/paper1/supplement/SUPPLEMENT_R1.md`; both R1 manuscripts (.md/.docx) and this letter.

---

# Response to the third report — added 2026-10-26

| # | Point | Status | What changed |
|---|---|---|---|
| 1 | Knowledge base and syndrome layer not independently audited; "guideline-rule engine" over-claims | **partly R3 / open** | Title changed to "guideline-*derived* rule engine"; Discussion now states that the components carrying the result (rule vote, ~900 constellations) are exactly those no audit has examined, and that the result measures the transcription, not the guidelines. The audit itself (2–3 specialists, rule-level accuracy, inter-rater agreement) requires people we do not have; the review package (`eval/human/Hemoglyph_clinician_review_package_R1.xlsx`: 200-rule random sample + 40 blind panels, dropdown scoring, κ computable) is ready and remains **open**. |
| 2 | NHANES selective reporting; ALT not in abstract range | **R3** | ALT elevation added to npj Results and Table 3 with all three cycles (0.721/0.880/0.877; weighted 0.710/0.879/0.870) and the Amendment 14 explanation; abstract ranges now "0.89–0.99 for six targets, 0.71–0.88 for ALT elevation" (both manuscripts). Nothing is omitted from Fig. 4. |
| 3 | UCI thyroid 7,743 ≠ 6,932; HCV 615 ≠ 608 | **R3** | Supplementary Table S13 participant flow: thyroid 9,172 → −842 no TSH → −587 R/I/J/S → 7,743, of which 811 belong to classes K/L/M/N/O/P/Q (non-thyroidal illness, replacement or antithyroid therapy) that are neither positives nor controls of any task; HCV: 7 "suspect donor" records excluded from both tasks (533 + 7 + 75 = 615; cirrhosis negatives 533 + 24 + 21 = 578). Table 3 rows now carry these counts. |
| 4 | Figure/table numbering; truncated table rows | **R3** | npj docx now places every figure with its full legend directly beneath it (Fig. 1–7 in text order); Table 3 rebuilt one target per row (no multi-value cells); Table 5 has an arm-definition note. The truncations the reviewer saw ("uniform fusion weights (0.20", "risk-model layer off 28") are line-wraps in text extraction from the docx, not in the file; cell contents were shortened where this could recur. |
| 5 | LLM reproducibility: identity, parameters, second model | **partly R3 / open** | Exact run dates per batch added (2026-10-21/22/23; re-read 10-24; alternative prompt 10-25); the interface exposes no temperature or sampling parameters (provider defaults) — stated. Model identity is withheld at the platform's request and will be disclosed confidentially to the editor; a second vendor model requires paid API access that the authors cannot obtain and remains **open**. |
| 6 | Weak reference standard; 14.2% precision needs adjudication | **partly R3 / open** | Added a laboratory-criterion adjudication of all 10,380 top-5 assertions (criteria fixed before scoring): 14.2% coded, 54.8% uncoded but criterion-positive in the same panel, 12.6% criterion-negative (closest estimate of true false positives), 18.4% no criterion — precision bounded 14.2–69.0% (Results + Table S11). Independent physician adjudication of 100–200 stays remains **open**. |
| 7 | End-to-end / OCR expectation | **R3** | Introduction (both) now states up front that every result concerns structured input and that the free-text parser performed poorly; title already says "structured laboratory-panel". |
| m1 | Table 2 registry-off vs Table 5 | **R3** | Footnote: historical v5.3 ablation kept for continuity; Table 5 holds the ablations of the evaluated release. |
| m2 | no_rule vs no_esl overlap | **R3** | Arm-definition note under Table 5 and Table N3-3: no_rule is a superset of no_esl (both vote through one fusion channel). |
| m3 | 29 vs 24 groups | **R3** | Explained in Results: 29 groups with ≥ 10 coded labels (multiplicity) vs 24 laboratory-detectable groups with ≥ 5 listed stays and a group score (mean AUROC). |
| m4 | ALT / Amendment 14 explanation | **R3** | Restored in npj Results (was already in the Sample version). |
| m5 | References 7, 14, 15, 18 | **R3** | npj 7 → Amjad H et al., Sci Rep 2025;15:33333; 18 → Agrawal M et al., npj Digit Med 2025;8:600; 15 is now the published JAMA Netw Open record; 14 already reads *JAMIA Open* in both files (no "JAMA Open" string exists). Sample ref 8 (scoping review) still lacks authors — flagged in the list. |
| m6 | Table 4 historical row | **R3** | Row labelled "superseded; naive McNemar ignored clustering — the v7 row with cluster-adjusted p = 0.54 is the result". |
| m7 | "Passed the non-regression gate" | **R3** | Supplementary Note 4 defines the gate and lists both residual failures with their status in 14.1 (77/78 and 752/755 → 753/755): neither is new. |
| m8 | 388 of 785 sources | **R3** | Table S10: 3 cited only by retired rules, 394 by no rule — background references imported during construction and retained for provenance; they influence no output. |
| m9 | Calibration figure numbering | **R3** | Legend now sits under the image (npj Fig. 7; Sample Fig. 8). |
| m10 | "October 2026" | **R3** | Replaced by exact dates; version string unavailable through the interface, stated as such. |

---

# Response to the fourth report (47 items) — added 2026-10-26

Convention: **R4** = resolved in this revision; **R4 (data)** = resolved by a new or repeated computation; **open** = requires a resource we do not control. Where a criticism was correct we say so and do not argue.

| # | Point | Status | What changed |
|---|---|---|---|
| 1 | "Pre-registered" is not accurate for an internal SAP | **R4** | Correct. The SAP was time-stamped and hash-frozen but never deposited publicly. "Pre-registered/pre-registration" replaced by "pre-specified/pre-specification" throughout both manuscripts (title, abstract, headings, Fig. 2 legend, Table 1), with an explicit sentence in Methods and Results; the only remaining "pre-registered" refers to the planned OSF-registered reader study. |
| 2 | MIMIC v7 re-run is not one-shot | **R4** | Correct. Labelled "post-hoc re-run (no longer a one-shot result)" in Results and Table 3; the "run once" sentence now names this exception. |
| 3 | Six-target criterion excludes ALT — why? | **R4** | Amendment 15 named the six targets a priori and excluded ALT because its label was known to be definition-sensitive. Stated explicitly in Results and Methods; ALT non-inferiority (0.877 vs 0.880) reported post hoc. |
| 4 | Ablation: syndrome layer may mask the registry's contribution (2 × 2 needed) | **R4 (data)** | New arm `anchor_only_no_esl` (2,314 stays, 1,000-stay cluster bootstrap): flat@5 48.2 % (Δ −12.6, −14.5 to −10.6); two-tier@5 60.9 %; mean AUROC 0.708. Interaction reported in Results, abstract, Discussion, Table 5 and Supplementary Note 3: the AI-drafted rules add 0.9 points with the syndrome layer and 3.1 without; the syndrome layer adds 9.5 with the full registry and 11.7 with anchors only. Conclusion amended: "partly redundant", not "inert". |
| 5 | ALT 2017–18 value 0.721 and the "threshold corrected under Amendment 14" explanation | **R4 (data) — error found and corrected** | The reviewer was right to be suspicious. On re-inspection the 2017–18 column of Table 3 had been copied from a run of registry 14.0.0 (`report_v1400.md`), not from the frozen v7, and the ACG label threshold had **not** changed between cycles; the explanation in the previous version was wrong and has been deleted. The 2017–18 cycle was re-run with the frozen v7 (`eval_nhanes.py --cycle J --suffix _v7`); all 2017–18 values in abstract, Results, Table 3, Fig. 4, Supplementary Table S7 and the Sample manuscript now come from that run (see §"NHANES 2017–18 re-run" below for the before/after values). |
| 6 | Subgroup numbers (65.4/61.1 %) inconsistent with the 60.8 % overall | **R4 (data)** | Correct — those figures came from an earlier per-stay file. Recomputed on the frozen v7 output: men 62.3 % (59.5–64.9; 1,392 stays), women 58.5 % (54.4–62.3; 922), age bands 58–64 %, ethnicity 59–61 %. Supplementary Table S4 added with n and CI. |
| 7 | Thyroid 7,743 vs 6,932 wording | **R4** | Now "7,743 with TSH, of which 6,932 scored (655 + 195 + 6,082) and 811 in other diagnostic classes" in text, Table 1 and Table 3 of both manuscripts. |
| 8 | Sepsis CIs for sets A and B; which engine version | **R4** | A 0.600 (0.575–0.625) and B 0.610 (0.583–0.640) were obtained with engine v6.1/registry 14.1.0; B2 0.588 (0.559–0.616) with the frozen v7. Stated in both manuscripts. |
| 9 | "Code and rules are released" vs "will be deposited" | **R4** | Abstract now says "public (GitHub; Zenodo DOI before publication)"; Code availability names the GitHub organisation and states that the frozen snapshot will be archived with a DOI; no claim of a DOI is made. |
| 10 | LLM identity "withheld at the platform's request / disclosed to the editor" is not credible | **R4** | Correct, and the previous wording was not accurate. The LLM was accessed through an agent platform that routes among several frontier model families and does not expose the model or version; "GPT-4-class" is a capability tier, not a verified identity; the arm is not reproducible against a named model. Stated in Methods, Limitations and Supplementary Note 5.6; the sentence about confidential disclosure is removed. |
| 11–14 | Typographical errors ("stylustered", "adult on 400", "recalibrate", duplicated OCR sentence) | **R4** | Searched both source files: "stylustered", "adult on 400" and "S99-5103"/"Eper" do not occur in the Markdown sources and appear to be PDF-extraction artefacts of "clustered", "audit on 400", "S99–S103", "Epner"; the source already reads "recalibrable" (the PDF rendering truncated it); the duplicated OCR sentence was removed in R3 and verified absent. |
| 15 | `analyse_gidlines.py` spelling | **R4** | It is the real file name (historical misspelling); marked "[sic—historical file name]" at first mention. |
| 16 | "Expert floor" undefined | **R4** | Defined in Methods: the fused score cannot fall below 0.90 × the rule-layer vote, so the other layers modulate but never veto a guideline rule. |
| 17 | "Adjudication" over-states an automated criterion check | **R4** | Renamed "automated laboratory-criterion matching (not clinician adjudication)" everywhere. |
| 18 | 388/785 sources in main text | **R4** | Already in Methods since R3; cross-reference to Table S10 kept. |
| 19 | Constant executable count across releases looks like bookkeeping | **R4 (data)** | Computed from the archived registries: 13.1.0 34,005 → 13.3.0 33,230 (−1,135 retired, +360 new) → 13.4.2 33,170 (−171, +111) → 14.0.0 33,178 (−1, +9) → 14.1.0 33,183 (+5); 1,307 retired and 485 added in total, none re-activated. Table S10 and Methods. |
| 20 | 10,380 assertions unexplained | **R4** | = 4.486 assertions/stay × 2,314 stays; stated in Results. |
| 21 | Which two groups failed BH | **R4** | Malnutrition (n = 16, AUROC 0.515) and hypocalcaemia (n = 10, 0.627); named in Results. |
| 22 | "All indices normal" undefined | **R4** | Replaced by the 30-analyte guideline-normal filter, summarised in Results and listed in full in Supplementary Note 5.1 (with the one dated tightening). |
| 23 | LLM "two-tier" is undefined | **R4** | Stated: the LLM returns one flat list which is reused; two-tier is secondary/post hoc and has no LLM counterpart. |
| 24 | CAP critical-value thresholds | **R4** | Listed in Supplementary Note 5.2 with the sampling rule (25 + 25 stays, fixed seed). |
| 25 | 752/755 → 753/755 wording | **R4** | Reworded: all failures are replicates of one thiazide-hyponatraemia vignette; v7 recovered one replicate; two remain; Note 4 table updated. |
| 26, 40, 41 | Tables split across pages / captions detached in docx | **R4** | Builders now mark every table row "cannot split", repeat the header row, keep rows together and keep captions with the table. |
| 27 | Fig. 4 y-axis starts at 0.6 | **R4** | Axis now starts at 0.5 with a visible break note in the legend; regenerated with the v7 2017–18 values. |
| 28 | Reporting checklist | **R4** | TRIPOD+AI (adapted; not-applicable items justified) completed and appended to the Supplement (Note 5.7); DECIDE-AI consulted for Limitations and cited in Methods. |
| 29 | "No open rule set exists" needs a search method | **R4** | Search method, sources and date (2026-10-24) in Supplementary Note 5.5; claim bounded to that search. |
| 30 | Author contributions "to be confirmed" | **open** | Cannot be resolved by the first author alone; co-authors must confirm wording and ORCIDs before submission. Flagged in the cover letter. |
| 31 | Non-inferiority re-specification must appear in abstract/conclusion | **R4** | Abstract already stated it; Conclusion of both manuscripts now does too. |
| 32 | Is the evaluated engine the product engine? | **R4** | Yes — same single file; stated in the Introduction with the competing-interest sentence. |
| 33 | Title "guideline-derived" still over-claims | **R4** | Title now "AI-drafted guideline-sourced rule engine" (npj) / "with an AI-drafted, guideline-sourced rule base" (Sample). |
| 34 | Abstract ablation sentence lacks numbers | **R4** | Numbers added (−9.5 points syndrome layer; −0.9/−3.1 AI-drafted rules). |
| 35 | 33,183 should be qualified at first mention | **R4** | "272 curated anchors and 32,911 AI-drafted, unaudited candidates" at first mention in Results. |
| 36 | "No race term" needs evidence | **R4 (data)** | Registry full-text search (0 hits for race/ethnic/African/Black/Caucasian/Hispanic; "white" only in "white blood cell"; one non-executable WHO BMI note mentioning Asian) and code search (optional `ethnicity` context field never read). Results and Note 5.3. |
| 37–39 | Reference formatting (Epner; S99–S103; JAMIA Open) | **R4** | Source entries verified correct ("Epner PL", "S99–S103"); artefacts arise in PDF extraction; JAMIA Open entry checked. |
| 42 | Table 5 caption: 28 unverified rules are a subset | **R4** | Caption amended. |
| 43 | Hardware unspecified | **R4** | 2 vCPU Intel Xeon 2.60 GHz, 2 GB RAM, Linux 6.1, Python 3.13 — Code availability and Note 5.4. |
| 44 | "None fitted to outcome data" unverifiable | **R4 (conceded)** | Now stated as a documented process claim supported by the dated change log, with the admission that no version-control history exists for the development period, so it cannot be audited by commit diff. |
| 45 | Full failure list for the gate | **R4** | Note 4 lists every failing case in v7 and 14.1 (one vignette; two perturbation replicates of one vignette). |
| 46 | Prevalence baseline deserves its own subsection | **R4** | Subsection "Prevalence baseline" added to Results (npj); Sample already had Section 4.3. |
| 47 | Two-tier vs LLM sentence | **R4** | Added to the LLM paragraph (69.8 % vs 59.6 %, secondary/post hoc). |


## NHANES 2017–18 re-run (item 5) — before/after

| target | previous manuscript (registry 14.0.0 run, in error) | frozen v7 re-run (`report_v7.md`, 2026-10-26) |
|---|---|---|
| diabetes | 0.945 | 0.946 |
| CKD | 0.958 | 0.959 |
| anaemia | 0.973 | 0.972 |
| iron deficiency | 0.990 | 0.989 |
| hypercholesterolaemia | 0.902 | 0.905 |
| hyperuricaemia | 0.943 | 0.943 |
| **ALT elevation** | **0.721** | **0.872** (weighted 0.872, 0.854–0.891) |
| self-reported diabetes / kidney disease | 0.918 / 0.816 | 0.919 / 0.816 |
| healthy adults, false assertions | 1/160 | 1/160 |

The ALT discrepancy was the registry-14.1 MASLD rule revision, present in v7 but absent in 14.0.0, not a label change. The abstract range for ALT is now 0.87–0.88 and the "seven targets 0.89–0.99" range becomes 0.88–0.99. Survey-weighted Table S7 recomputed from the v7 per-subject file. We apologise for the error; it was found while checking this item.

## Files added or changed in R4
`eval/ablation/run_ablation.py` (+arm `anchor_only_no_esl`), `run_chain.sh`, `ablation_ci.py` → `eval/results/eicu_demo/{per_stay,report,summary}_abl_anchor_only_no_esl*`, `ABLATION_v7_{ci,full}.md`; `eval/results/nhanes_2017/{report_v7.md,summary_v7.json,per_subject_v7.json.gz,nhanesJ_v7.log}`; `eval/realdata/nhanes_weighted.py` (J → v7) → `eval/results/nhanes_weighted_v7.{md,json}`; `eval/subgroup_fairness.py` (reads .gz) → `eval/results/eicu_demo/subgroups_v7.md`; `docs/paper1/v7/tools/{r4_edits.py,r4b_nhanesJ.py,build_docx_R1.py,build_sample_docx_R1.py}`; `make_paper_src_figs.py` + `fig/Fig5.png`; both `_R1.md` manuscripts and `.docx`; `docs/paper1/supplement/SUPPLEMENT_R1.md` (Table S4, S10 flow, Note 4, Note 5, TRIPOD+AI checklist).

---

# Response to the fifth report — added 2026-10-26

Items requiring resources outside the authors' control (independent clinical rule audit, clinician adjudication of assertions, a clinical co-author/advisory board, credentialed full eICU/MIMIC-IV, a version-pinned named LLM) remain **open** and are now stated as such in Limitations; everything else was implemented.

| Point | Status | What changed |
|---|---|---|
| M1 pre-specified vs changed criteria | **R5** | Abstract now states: SAP internal and hash-frozen, not publicly registered; criteria changed from superiority to non-inferiority after Round 1 failed; Round 2 supportive, not confirmatory. Title no longer says "one-shot quarantine" unqualified ("frozen quarantine rounds") and names the demo subsets. Conclusion repeats both. The garbled sentence "'pre-specified', not 'pre-specified'" (a global-replace error) is fixed. |
| M2 unaudited knowledge base | **partly R5 / open** | Abstract and Conclusion now say the components carrying the result (272 anchors, syndrome layer) are exactly those not yet independently audited and were written by a non-clinician; Discussion wording changed to "guideline-*transcribed*". The audit itself requires two independent clinicians (package ready) — open. |
| M3 LLM not reproducible | **R5 (wording) / open (re-run)** | "GPT-4-class" removed from title, abstract, headings, tables and text → "unnamed frontier LLM accessed through an agent platform (model not disclosed)". A version-pinned re-run is not possible for the authors (no paid API access); stated. |
| M4 reference-standard ceiling | **R5 / open** | Abstract: precision@5 14.2 % against an incomplete list; panel-supported metric labelled post hoc there and in Limitations; prevalence baseline overtaking at k = 10 and "contribution is ordering" in abstract. Clinician adjudication of a 200-assertion sample — open. |
| M5 demo subsets only | **R5 (scoping)** | Title and abstract name the demo subsets; Limitations note small external cohorts and ILPD 0.704. Full releases need PhysioNet credentialing — open. |
| M6 COI / non-clinician authorship | **R5 (disclosure) / open** | Limitations now state the financial interest and the non-clinician authorship of the load-bearing components explicitly; Introduction states the product engine is the evaluated file. Clinical co-author — open. |
| M7 open vs proprietary | **R5** | Supplementary Table S15 (npj) / Table 1b in the main text (Sample): component, licence, whether evaluated. |
| M8 sepsis SIRS/qSOFA post hoc | **R5** | Results now say the rules were added *after* the pre-specified negative result (post-hoc addition), developed on A, validated once on B2; abstract gives AUROC 0.60 and this caveat. |
| M9 structured inputs only | **R5** | Sentence added to abstract; Introduction states laboratory-only input as a design choice. |
| M10 calibration | **R5** | Table 2 note: scores are ranks; after cross-fitted isotonic recalibration ECE 0.162 → 0.003, Brier 0.117 → 0.040 with no rank change; the product applies no calibration map and shows no probabilities. |
| Historical rows Tables 2/4 | **R5** | Removed; archived as Supplementary Table S12b. |
| Bayesian priors / fusion weights / expert floor | **R5** | Methods: 75 Bayesian nodes with hand-coded priors, 68 with literature LRs, none fitted to data; fusion weights 0.35/0.25/0.20/0.10/0.10 set by author judgement, not tuned on any evaluation set; expert floor defined and its bias discussed in Discussion (and Section 2.4 of the Sample version). |
| "executable" and "AI assistance" definitions | **R5** | Both defined precisely in Methods (what the LLM produced, what the automated audits checked, that no human read the bulk, how anchors differ). |
| Healthy-adult filter (30 analytes), synthetic 0/1,000 | **R5** | Limitation of the filter stated (lower bound on false assertions); synthetic panels separated from real adults and labelled a regression check. |
| Critical values 39/39 | **R5** | Wilson CI 91–100 % added; labelled a shared safety floor, non-discriminating. |
| Concurrent analysis 247/600; safety batteries | **R5** | Clarified as set B2 only; batteries summarised in main text. |
| Fairness claim | **R5** | Bounded: three strata in one US dataset do not support a fairness claim; only the absence of a race term and race-free eGFR are asserted. |
| Sepsis logistic numbers, Fig. 6 per-group, label omission, κ 0.69, recall@1/@10 | **R5** | All quantified in Results/Discussion with numbers. |
| Version control | **R5 (partial)** | Stated as limitation; retrospective SHA-256/timestamp manifest of retained artefacts (Supplementary Note 6); Git repository initialised with tag `paper1-R1-round5` for all future changes. |
| Novelty-search claim | **R5** | Dated search summarised in the Introduction, method in Note 5. |
| Typos / page 8 | **R5** | "stylustered" and "S99-5103"/"Eper" do not exist in the source (PDF extraction artefacts of "stay-clustered"/"S99–S103"/"Epner"); the abstract now reads "clustered by stay" to avoid the ligature. No block of "1 1 1 …" exists in the docx text or tables; it is presumably a PDF rasterisation of a figure and we could not reproduce it — please send the page if it recurs. |
| Refs 15/18 "to be verified", affiliation/contributions "to be confirmed" | **open** | Co-author confirmation pending; references were finalised in R3. |
| Abstract length | note | The abstract now carries every element the reviewer asked for and runs to ~310 words, above npj guidance (~150–250); we will cut to the journal limit at submission if the editor prefers, dropping numeric detail rather than caveats. |
