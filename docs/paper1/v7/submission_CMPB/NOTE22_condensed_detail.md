## Supplementary Note 22 — Detail condensed from the main text in revision R9 (verbatim; no number changed)

The R9 revision shortened and re-worded the main text for readability. Every quantitative statement that was removed from the main text is reproduced here verbatim so that nothing reported in earlier revisions is lost.

**Section 2.3 (verifier).** "…reciprocal-rank fusion (k = 0) of the engine's ranking with the LLM entries marked supported… Protocols and predictions were committed before computation."

**Section 2.4 (activity log).** The activity log was run with "registry 14.2.0, whose rule layer equals v7's".

**Section 2.6 (sufficiency arm).** "…only 94 of the 364 active-core rules are among them [the 335 sufficiency-arm rules]."

**Section 3.2 (provenance scan).** "A provenance scan of all 785 sources resolved 112 DOIs via Crossref and reached 533 landing pages; 39 were unreachable, 34 lacked a locator, nine invalid DOIs were removed and 28 rules were flagged `unverified_source` (Supplementary Table S10, Fig. S1)."

**Section 3.3 (active core).** "…its first-cited source is a resolved DOI for 10.4% of rules against 0.8% registry-wide." Unresolvable share "88.6% among the 70 non-template rules". "Of the unresolvable rules, at least 18 cite a specific document that does not address the rule's analyte, 30 an organisation page and 5 a WHO URL returning 404."

**Section 3.7 (black-box conformance).** "Re-scored through the released package with registry 15.2.0, the engine card is unchanged except P2 39/40: in the one discordant pair the generator's rounding (1.3 mg/dL → 115 µmol/L → 1.3009 mg/dL) crosses a strict > 1.3 mg/dL rule leaf, a generator artefact, not a unit defect." Absent-analyte probe: "(1/29 versus 4/29 with no redundant analyte left, post hoc)".

**Section 3.8 (verified consensus).** Recall@5 of the fusion arm versus the engine: "+0.6 versus the engine, CI −2.2 to 3.4"; criterion-met labels "82.1% versus 77.9/81.0%".

**Section 3.9 (sufficiency, transfer, ledger).** "grouped@10 p = 3.8 × 10⁻⁵". Transfer: "where single-analyte screens (6.0) and adult thresholds without a population gate (3.3) predominated; 37 of 51 flags were true defects, 8 false positives and 6 undetermined". Ledger: "8 carry a discordant verdict (6 uncorrected)"; "the executable invariants reach the analyte of 104 of the 219 active-core rules still executable"; closure in 15.3.0: "two were re-sourced with retrieved quotes, two reclassified as reference-interval conventions, two retired, one boundary written, and the five flags inspected and left in place as recorded exceptions"; gate: "eICU flat and two-tier recall identical; NHANES AUROCs identical; grouped recall@1 −0.3 points".

**Section 2.1 (engine).** Syndrome-layer anchor strengths "0.95/0.88/0.80/0.72/0.45".

**Section 3.4 (discussion of precision bounds).** "supervised models did not exceed 0.82 AUROC for outcome-defined groups".

**Further detail condensed in the submitted (shortened) main text.** Engine: "The Bayesian layer has 75 disease nodes with hand-coded priors"; curated-anchor arm "32,911 AI-drafted rules off". Active core locators: "120 locators were organisation landing pages, 63 blocked or 404, 150 reached a page without the statement". eICU recall@5 by group also included "77.5% (acute kidney injury)" and "45.1% (diabetes)". NHANES hypercholesterolaemia AUROC "0.905/0.883/0.886". External cohorts: "UCI thyroid 0.979/0.798, HCV 0.925, ILPD 0.704, MIMIC-IV demo top-5 47.5%, PMC case reports 26% specific/68% syndrome"; "raw-score calibration (pooled AUROC 0.797; Fig. 8)". Ledger: anchors "101 cite a reachable but unchecked source". Black-box: "the LLM's 0/20 is not blind because the step was visible". Discussion: "a prevalence baseline overtakes any method at k = 10"; "only 12.6% are criterion-negative … 69.0% an upper bound"; "supervised models did not exceed 0.82 AUROC for outcome-defined groups".
