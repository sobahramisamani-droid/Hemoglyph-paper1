# An untrained, auditable, locally run guideline-rule engine for laboratory-panel interpretation: pre-registered multi-dataset evaluation with one-shot quarantine and a blinded comparison against a GPT-4-class language model

Sobhan Bahrami^1*^, Zhaleh Tahmasebinejad^2^, Ehsan Bahrami Samani^2^

^1^ Allameh Helli 10 High School (NODET), Tehran, Iran. ^2^ Statistics and Data Science Clinic, Shahid Beheshti University, Tehran, Iran.
\* Correspondence: sobahramisamani@gmail.com · ORCID 0009-0004-6639-5081

## Abstract

Laboratory interpretation remains largely manual; large language models interpret panels fluently but neither reproducibly nor locally. Hemoglyph is an offline engine that ranks a cited differential from a laboratory panel using 33,183 executable guideline rules, without outcome training. Under a pre-registered plan with frozen releases and two one-shot quarantine rounds (the first failed and is reported), we evaluated it on 2,314 ICU stays, 9,000 NHANES adults, 14,420 sepsis patients and external cohorts. From laboratory values alone, 60.8% of clinician-listed ICU diagnoses appeared in the top-5 (78.0% of those the first panel could support); screening AUROCs of 0.92–0.99 reproduced across cycles with ≤1 false assertion in healthy adults. Blinded on identical inputs, the engine listed 64.4% versus 59.6% for a GPT-4-class model (p = 0.009). It did not predict sepsis. Code and rules are released.

## Introduction

Roughly 70 % of clinical decisions draw on laboratory results, yet interpretive comments accompany only a small fraction of reports, and post-analytical errors—missed critical values, patterns that span several analytes, unit confusion—remain a leading source of diagnostic harm [1–3]. Three families of software address this gap. Rule-based expert systems embedded in laboratory information systems are transparent but typically narrow, hand-maintained and rarely evaluated outside their home institution [4,5]. Supervised machine-learning models discriminate specific targets well but need labelled training data, degrade under distribution shift and cannot be audited clause by clause [6,7]. Most recently, large language models (LLMs) have produced fluent interpretations of laboratory reports, but their outputs are not reproducible, cannot run on commodity laboratory hardware without transmitting patient data, fabricate references at non-trivial rates and misclassify values as high or low even when reference ranges are supplied [8–11].

A fourth option—an engine that interprets whole panels from an explicit, versioned knowledge base, runs offline and emits a ranked, explainable differential—has seldom been evaluated at scale. The barrier is methodological rather than technical: such engines are usually validated on vignettes written by their own authors, and the few real-data evaluations use a single institution and no comparator [12]. Mature diagnostic decision-support systems (Isabel, DXplain) have recently been compared with GPT-4-class models and found within a few percentage points on recall while being reproducible and free of fabricated references [13–16]; none isolated laboratory-only reasoning. At the same time, the public infrastructure for executable guideline knowledge has contracted: the AHRQ CDS Connect repository went offline in 2025 and no open, executable rule set for laboratory interpretation exists.

Here we report the design and a pre-registered, multi-dataset retrospective evaluation of Hemoglyph. Our aims were (i) to describe an architecture that keeps every output traceable to a cited rule; (ii) to evaluate the frozen engine against clinician- and guideline-derived reference standards in public datasets spanning intensive care, community survey, referral laboratory, hepatology and case reports; (iii) to compare the untrained engine with a single-analyte threshold, with supervised models trained on the same inputs and—blinded, on identical inputs—with a contemporary LLM; (iv) to quantify the ceiling imposed by the reference standard itself; and (v) to report failures transparently, including a quarantine round that failed and a pre-registered negative result. We frame this as an engineering and evaluation study, not a claim of clinical validation.

## Results

### System and knowledge base

Hemoglyph is a single-process Python engine (Fig. 1). Inputs are analyte–value pairs with units plus age, sex and encounter type; clinical context and serial values are optional. After UCUM-based unit normalisation and derivation of 100 indices (CKD-EPI 2021 eGFR, corrected anion gap, FIB-4 and others), a rule layer evaluates 33,183 executable rules (registry 14.1.0) derived from 785 guideline sources; a curated expert syndrome layer (~900 multi-analyte constellations with tiered anchor strengths and context guards) adjusts and guards; a fixed fusion step combines rule votes, Bayesian priors and fuzzy degrees; and a ranking-hygiene step applies causal attribution (a covering diagnosis explains its downstream findings), KDIGO chronicity rules and the universal definition of myocardial infarction. Output is a two-tier list—specific diagnoses and umbrella syndromes—each with `explained_by` findings, an evidence state and suggested next tests. The engine is deterministic (byte-identical output in 50/50 repeated stays), runs on CPU in ~1 s per panel and makes no network calls.

The registry was constructed with AI assistance from guideline text and curated by automated consistency audits; it has not yet been audited rule-by-rule by clinicians. A provenance audit resolved 112 DOIs via Crossref and reached 533 landing pages; 39 sources were unreachable from our sandbox, 34 lacked a locator, nine invalid DOIs were removed and 28 rules were flagged `unverified_source` (Supplementary Fig. S1).

### Pre-registration, freezes and quarantine

Evaluation followed a statistical analysis plan with 15 dated amendments (Supplementary Note 1). Before each quarantine round the code and registry were frozen with a SHA-256 manifest (261 and 316 files). Quarantine data had never been run before the freeze and were run once. Round 1 (MIMIC-IV demo, NHANES 2013–14, PhysioNet sepsis set B) failed two primary criteria that had been written as superiority over the prior release; the cause was that guideline-correctness changes (e.g. a single creatinine no longer asserts chronic kidney disease) lowered label recall for CKD. We report that failure, re-specified the criteria as non-inferiority with dated justification, implemented six further correctness changes (engine v7) and ran Round 2 (NHANES 2015–16, sepsis set B2, new healthy sweep), which met all criteria (Fig. 2a; Supplementary Table S2). All results below are for the frozen v7/14.1.0 release unless stated.

### Intensive care (eICU-CRD demo)

In 2,314 adult ICU stays from 186 US hospitals, using the first panel with ≥ 8 analytes and no clinical text, 47.9% (95% CI 45.9–49.9) of 2,432 clinician-listed, laboratory-relevant diagnoses appeared in the top-3, 60.8% (58.8–62.7) in the top-5 and 74.1% (72.3–75.8) in the top-10 of the flat differential (Table 2). Counting either tier, top-5 recall was 71.9%. Recall@5 was 88.1% for acute myocardial infarction, 82.8% for heart failure, 83.0% for anaemia, 77.5% for acute kidney injury and 77.9% for gastrointestinal bleeding, but 49.1% for sepsis, 45.1% for diabetes and 35.8% for CKD.

The reference standard bounds this metric (Fig. 2b). Of 2,707 label targets, 541 belonged to groups with no single laboratory criterion, 275 lacked the key analyte in the first panel and 431 were contradicted by the first panel (e.g. hypokalaemia coded with potassium 4.1 mmol/L after repletion). Among the 1,460 labels whose first panel met the guideline criterion—a secondary metric with thresholds fixed before scoring—flat recall was 29.6/62.5/78.0/91.8% at k = 1/3/5/10 and two-tier recall 43.0/77.7/89.2/97.2%. Per-group recall on this subset exceeded 85% for renal impairment, AKI, anaemia, AMI, DKA, heart failure, hypokalaemia and pancreatitis; the only groups where v7 lost against the previous release were CKD (41.1% vs 74.4%, by design) and leukocytosis (46.9% vs 67.3%) (Supplementary Fig. S3).

Three comparators used identical inputs (Fig. 3). A raw key-analyte threshold matched or exceeded the engine's AUROC for single-analyte groups (hyperkalaemia 0.96 vs 0.92; anaemia 0.83 vs 0.78), as expected for findings that are definitions. Gradient boosting and logistic regression trained on the labels (five-fold out-of-fold) exceeded the untrained engine only in outcome-defined groups without a laboratory signature—sepsis (0.82 vs 0.68), GI bleeding (0.85 vs 0.75), alcohol withdrawal (0.80 vs 0.54)—and were matched or beaten in nine guideline-defined groups (CKD 0.79 vs 0.81; hyponatraemia 0.85 vs 0.89; thrombocytopenia 0.85 vs 0.89; cirrhosis 0.83 vs 0.87). Disabling the rule registry (syndrome layer only) reduced flat recall@5 from 63.7% to 62.0% and mean 24-group AUROC from 0.767 to 0.732, with leukocytosis falling from 57.9% to 8.8%; on panel-supported labels recall@5 fell from 78.0% to 75.3%.

Adding documented history and medications raised recall@5 from 58.2% to 59.1% for labels not named in the history (n = 2,467) but from 49.6% to 72.9% for labels already named (n = 240); the context arm therefore mainly echoes documentation and is reported only in the Supplement.

### Community survey: three independent NHANES cycles

In 3,000 adults per cycle, AUROCs reproduced across the development cycle (2017–18) and the two quarantine cycles (2013–14, 2015–16): diabetes 0.945/0.938/0.924, CKD 0.958/0.968/0.962, anaemia 0.973/0.994/0.983, iron deficiency 0.990/–/0.972, hyperuricaemia 0.943/0.958/0.955 and hypercholesterolaemia 0.902/0.883/0.886 (Fig. 4; Table 3). These laboratory-defined labels overlap the inputs and test criterion recognition; against self-reported physician diagnosis, which is independent of the inputs, AUROC was 0.90–0.92 for diabetes and 0.75–0.82 for kidney disease. Among adults with all indices normal, the engine asserted a disease in 1/160, 1/246 and 0/79 (and in 0/1,000 synthetic healthy panels).

### External cohorts and case reports

On the UCI thyroid referral set (3,162 records) AUROC was 0.979 for hypothyroidism (sensitivity 0.969, specificity 0.951) and 0.798 for hyperthyroidism; on the HCV cohort (n = 615) 0.925 (0.881–0.962) for any liver disease and 0.909 for cirrhosis; on ILPD (n = 583) 0.704 (0.661–0.747). In MIMIC-IV demo (235 admissions, ICD-coded reference, quarantine round 1) top-5/10 recall was 47.5/62.1%. On 50 PMC case reports given only the laboratory paragraph, the correct specific diagnosis was in the top-5 in 26% and the correct syndrome in 68% (automatic parsing: 10% and 44%), a lower bound without history (Table 3).

### Pre-registered negative result: sepsis

In PhysioNet/CinC 2019, the engine's sepsis score from first-24-h laboratory values discriminated Sepsis-3 onset with AUROC 0.600, 0.610 and 0.588 (95% CI 0.559–0.616) in sets A, B and B2, versus 0.691, 0.712 and 0.679 for a supervised logistic model on the same features. A post-hoc concurrent analysis (labs and vital signs within ±6 h of onset; Amendment 13) reached 0.635 (0.597–0.673) versus 0.726 (Fig. 5). Hemoglyph is not a sepsis predictor.

### Blinded comparison with a GPT-4-class LLM

On 400 stays (596 labels) a general-purpose GPT-4-class LLM received the identical panel, age and sex and returned ten ranked diagnoses, blinded to labels. Recall@5—the pre-specified primary comparison—was 64.4% (60.5–68.2) for Hemoglyph (v5.1) versus 59.6% (55.6–63.4) for the LLM (McNemar p = 0.0093); recall@10 74.5% vs 65.1%; mean reciprocal rank 0.397 vs 0.408 (difference CI −0.037 to +0.014). The LLM placed more labels at rank 1 (168 vs 139) and the engine left fewer absent (152 vs 208) (Fig. 6; Table 4). The engine was better for GI bleeding (87 vs 50%), CKD (51 vs 20%) and diabetes (55 vs 37%); the LLM for DKA (83 vs 73%) and metabolic acidosis (79 vs 57%). On 40 re-read panels the LLM's label-level agreement with itself was 85.7% (κ = 0.69); the engine is deterministic. Both flagged 39/39 CAP critical values in 50 stays.

### Calibration and subgroups

Pooled over 52,689 stay–group units, AUROC was 0.801 but expected calibration error was 0.161 (Brier 0.115); cross-fitted isotonic recalibration reduced ECE to 0.002 (Brier 0.040). Raw scores are therefore ranks and are not displayed as probabilities. Recall@5 was 65.4% (62.6–68.2) in men and 61.1% (57.1–65.3) in women, 60–67% across age bands and 63–66% across the three largest ethnicity strata; the engine contains no race term.

### Robustness

The release passed 689/689 unit tests, 352/353 adversarial vignettes (the one failure, alcoholic pancreatitis, was deliberately not patched with a case-specific rule), 753/755 perturbation pairs and the SI/conventional unit-twin battery.

## Discussion

A guideline-rule engine with no training data recovered 61% of clinician-listed ICU diagnoses in five suggestions from laboratory values alone, 78% of those diagnoses the first panel could support, and reproduced screening AUROCs of 0.92–0.99 across three NHANES cycles while asserting disease in at most one of 246 healthy adults. In a blinded paired comparison on identical inputs it was not inferior—and on the pre-specified metric superior—to a GPT-4-class model, while being deterministic, local and traceable to a cited rule. It failed, as pre-registered, to predict sepsis.

Three findings shape how these numbers should be read. First, the apparent ~60% ceiling is largely a property of the reference standard: a quarter of admission-level labels were not inferable from the first panel, and a supervised model trained on the labels themselves did not exceed 0.82 AUROC for outcome-defined groups. The panel-supported metric, though pre-specified, was defined after the ceiling was observed and is structurally optimistic; we present it alongside, not instead of, the flat metric. Second, the untrained engine matched supervised models wherever a guideline definition exists and lost wherever the label is an outcome (sepsis, bleeding, withdrawal) that the model learns from hidden correlates. This is the expected division of labour between knowledge and learning, and it argues for hybrid rather than replacement designs. Third, the LLM was better at rank 1 and worse at coverage; the two systems make different errors, which is itself a reason to study them together rather than to declare a winner.

Our evaluation design addresses several criticisms levelled at recent LLM benchmarks—unstable metrics, leakage and post-hoc selection [17,18]. Releases were frozen with manifests; quarantine data were run once; a round that failed is reported with its original criteria; and the sepsis analysis that was added after a disappointing result is labelled post-hoc. The cost of correctness is visible: moving from the product release (13.4.2) to v7 cost three points of flat recall, almost entirely because a single creatinine no longer asserts CKD and a normal leukocyte count no longer yields a syndrome. We consider that trade accepted and disclose it.

Compared with Isabel and DXplain, which take symptoms and have been evaluated on 36–201 cases [13–16,30], this study isolates laboratory-only reasoning on more than 20,000 real encounters and releases its knowledge base under an open licence, into an ecosystem in which public executable guideline repositories have been withdrawn. Because our rules were drafted with AI assistance, the open release is a precondition for—not a substitute for—expert audit. We regard the knowledge base as a living artefact: every leaf carries a source locator, so a clinician can accept, amend or reject a rule and the change is versioned; the provenance audit already identifies the 34 sources that cannot be traced and the 28 rules that depend on them.

Where might such an engine be used? Not as an autonomous diagnostician. Its natural positions are the post-analytical step of a laboratory information system—interpretive comments and critical-pattern alerts generated locally, without transmitting patient data—and as a reproducible, auditable baseline against which LLM-based interpretation can be measured. The determinism and traceability that make it attractive for regulated settings are precisely the properties that the LLM in our comparison lacked (test–retest κ = 0.69), and the two architectures could be combined: a language model to extract and normalise free-text results (the step at which our automatic parser lost half the PMC cases) and a rule engine to reason over them.

Several design decisions deserve justification. We chose laboratory-only inputs as the primary arm because documented history inflates recall mainly by echoing the diagnosis already written down (+23 points for labels named in the history versus +1 point otherwise); evaluations that feed problem lists to the system under test risk measuring transcription, not inference. We scored recall against a clinician problem list rather than adjudicated diagnoses because adjudication at this scale was beyond our means; we quantified rather than hid the resulting ceiling. We did not tune the engine to the sepsis task after the pre-registered result because an outcome-fitted rule would have been a supervised model in disguise; the guideline-sourced SIRS/qSOFA rules that were added under Amendment 15 were developed on set A and validated once on set B2.

What would change the evidence level? First, a rule audit by independent clinicians on a random sample, with inter-rater agreement reported; second, the credentialed full eICU and MIMIC-IV releases, on which the released scripts run unchanged; third, a clinician-in-the-loop study measuring diagnostic accuracy, time and automation bias with and without the engine, for which a crossover protocol has been drafted. Until then, the claims of this paper are deliberately bounded to retrospective, laboratory-only performance.

### Limitations

The knowledge base has not been audited rule-by-rule by clinicians; 34 sources lack a locator. Only the open demo subsets of eICU and MIMIC-IV were used; the reference standards are admission-level problem lists and ICD codes, not adjudicated panel-level diagnoses. The LLM comparison is an author-run self-baseline with one model, one prompt, no retrieval augmentation and the v5.1 engine. Laboratory-defined NHANES labels overlap the inputs. Raw scores are uncalibrated. No clinician-in-the-loop evaluation was performed; a pre-registered crossover reader study with an automation-bias endpoint is in preparation. Iranian populations and non-English laboratory conventions were not evaluated. The first author is a secondary-school student and the system was developed with AI-agent assistance, declared below.

### Conclusion

An open, offline, guideline-rule engine can interpret laboratory panels to the ceiling the first panel allows, reproduce population-screening performance across independent survey cycles and match a frontier LLM blind, while remaining auditable. Its limits—outcome-defined syndromes, uncalibrated scores and an unaudited AI-drafted rule base—are stated so that they can be measured and closed.

## Methods

### Engine

Hemoglyph (`analyse_gidlines.py`, v7) processes a panel in five stages: normalisation (UCUM units, aliases, age/sex reference intervals, 100 derived indices); a rule layer over registry 14.1.0 (33,183 leaves; each with analyte conditions, population gates, evidence role—diagnostic criterion weight 6, supportive or screening weight 3—disease identifier and source); an expert syndrome layer (~900 constellations with anchor strengths 0.95/0.88/0.80/0.72/0.45, operators absent/between/neg/present and context predicates for pregnancy, age, sex, medication, condition, family history and encounter); fixed-weight fusion with an expert floor of 0.90 × rule vote; and ranking hygiene (causal attribution via a disease–finding explanation graph, covering-diagnosis suppression of explained findings, KDIGO chronicity, UDMI acuity, maximum 25 entries). Engine changes between releases (C1–C16) are listed with dates in Supplementary Table S1; none was fitted to outcome data and no rule was written for a specific missed case.

### Knowledge base construction and provenance

Rules were drafted from guideline text (KDIGO, ADA, WHO, ACC/AHA, EASL, ATA, ESC, CLSI, Tietz) with AI assistance, converted to executable form and filtered by automated audits (duplicates, contradictions, out-of-range thresholds, unit mismatch, missing context gates). Source locators were verified with `registry_source_verify.py` (Crossref resolution, HTTP reachability). Counts by release: 13.3.0, 33,230 rules/747 sources; 13.4.2, 33,170/781; 14.1.0, 33,183/785.

### Pre-registration, freezes and quarantine

The SAP (Supplementary Note 1) fixed metrics, label maps, thresholds and comparators; 15 amendments are dated and justified. Freezes v14 and v15 recorded SHA-256 manifests. Quarantine round 1 (MIMIC-IV demo; NHANES 2013–14; sepsis set B) used superiority criteria and failed; round 2 (NHANES 2015–16; sepsis set B2; healthy sweep with a new seed) used non-inferiority criteria specified before execution and passed. Two data-loader defects discovered during round 2 (string patient identifiers; a dropped derived NHANES variable) were fixed before scoring without touching the engine and are documented.

### Datasets and reference standards

eICU-CRD demo v2.0.1 [19]: 2,520 stays → 2,512 adults → 2,314 with ≥ 8 analytes in the first panel; reference = clinician problem list mapped by regular expressions to 31 groups (audit on 100 stays/425 strings: precision 100%, sensitivity 98.7%). MIMIC-IV demo [20]: 235 admissions, ICD-10 reference. NHANES 2013–14, 2015–16, 2017–18: 3,000 randomly sampled adults per cycle with biochemistry and CBC; references per ADA, KDIGO, WHO and ACG criteria and self-reported diagnoses. PhysioNet/CinC 2019 [24]: set A 4,871 patients (439 sepsis), set B 4,558 (268), set B2 4,991; Sepsis-3 onset label; concurrent analysis 247 cases/600 dwell-time-matched controls. UCI thyroid0387 [22], UCI HCV [21], ILPD [23], PMC-Patients 50 case reports [17]. Participant flow in Supplementary Table S3.

### Metrics

Primary: flat recall@k of clinician-listed diagnoses (k = 3, 5, 10). Secondary: two-tier recall; panel-supported recall (labels whose first panel met a guideline criterion fixed in `panel_supported_metric.py` before scoring; groups without a single criterion excluded); per-group AUROC of the group score. Screening: AUROC and false-assertion rate in all-normal adults. Sepsis: AUROC of the sepsis-group score. Calibration: ECE and Brier before and after cross-fitted isotonic regression [29].

### Comparators

B1, raw key-analyte threshold; B2, gradient boosting and logistic regression trained on the same analytes, five-fold out-of-fold; registry-off ablation; LLM: a general-purpose GPT-4-class model (October 2026) run by the authors, blinded to labels, with a fixed prompt requesting ten ranked diagnoses from the identical panel, age and sex; 40 panels re-read for test–retest; scoring by the same label map and script. Model identity is withheld by design; prompts and outputs are released.

### Statistics and software

Wilson intervals for proportions; 1,000-sample bootstrap or DeLong for AUROC; McNemar for paired recall; bootstrap for MRR differences. Python 3.11/3.13, numpy, pandas, scikit-learn. Reporting follows TRIPOD+AI [25].

## Data availability

eICU-CRD demo (physionet.org/files/eicu-crd-demo/2.0.1/), MIMIC-IV demo, PhysioNet/CinC 2019 (physionet.org/files/challenge-2019/1.0.0/training/), NHANES (wwwn.cdc.gov/nchs/nhanes), UCI and ILPD repositories are public. Per-stay outputs, label maps, LLM prompts and outputs are provided as Supplementary Data.

## Code availability

Engine and evaluation scripts (AGPL-3.0-or-later) and the rule registries (CC BY-SA 4.0), together with freeze manifests and `reproduce.sh`, will be deposited on Zenodo with a DOI before publication; a GitHub mirror is available from the corresponding author.

## Author contributions

S.B. conceived the system, built the engine and knowledge base, designed and ran the evaluation and wrote the manuscript. Z.T. reviewed the statistical analysis plan and the reporting of the quarantine evaluation and revised the manuscript. E.B.S. supervised the statistical methodology and critically revised the manuscript. All authors approved the final version. *(Contributions of Z.T. and E.B.S. to be confirmed before submission.)*

## Competing interests

S.B. is the sole developer of Hemoglyph, whose desktop application is distributed under a proprietary licence; the engine and registries are open. Z.T. and E.B.S. declare no competing interests. No funding was received.

## Use of artificial intelligence

The rule registry was drafted with AI assistance and curated by automated audits. An AI coding agent assisted with evaluation scripts, figure generation and the blinded LLM arm under the first author's direction; all analyses were specified in the SAP and are reproducible from the released code. No AI tool is listed as an author.

## Ethics

All datasets are de-identified and publicly released under their data-use agreements; no ethical approval was required.

## References

1. Plebani M. The detection and prevention of errors in laboratory medicine. *Ann Clin Biochem* 2010;47:101–110.
2. Hallworth MJ, et al. Current evidence and future perspectives on the effective practice of patient-centered laboratory medicine. *Clin Chem* 2015;61:589–599.
3. Epner PL, Gans JE, Graber ML. When diagnostic testing leads to harm. *BMJ Qual Saf* 2013;22:ii6–ii10.
4. Vasikaran S, et al. Interpretative commenting. *Clin Biochem Rev* 2008;29(Suppl 1):S99–S103.
5. Sutton RT, et al. An overview of clinical decision support systems: benefits, risks, and strategies for success. *npj Digit Med* 2020;3:17.
6. Rank N, et al. Deep-learning-based real-time prediction of acute kidney injury outperforms human predictive performance. *npj Digit Med* 2020;3:139.
7. Fleuren LM, et al. Machine learning for the prediction of sepsis: a systematic review and meta-analysis. *Intensive Care Med* 2020;46:383–400.
8. Cadamuro J, et al. Potentials and pitfalls of ChatGPT and natural-language artificial intelligence models for the understanding of laboratory medicine test results. *Clin Chem Lab Med* 2023;61:1158–1166.
9. Kurstjens S, et al. Accuracy of large language models in answering laboratory medicine questions. *Clin Chem Lab Med* 2024.
10. Hager P, et al. Evaluation and mitigation of the limitations of large language models in clinical decision-making. *Nat Med* 2024;30:2613–2622.
11. Savage T, et al. Diagnostic reasoning prompts reveal the potential for large language model interpretability in medicine. *npj Digit Med* 2024;7:20.
12. Laposata M, Dighe A. "Pre-pre" and "post-post" analytical error. *Clin Chem Lab Med* 2007;45:712–719.
13. Bridges JM. Computerized diagnostic decision support systems – a comparative performance study of Isabel Pro vs. ChatGPT4. *Diagnosis (Berl)* 2024;11:250–258.
14. Bridges JM. Comparative performance of Isabel Pro and ChatGPT-4, part II. *JAMIA Open* 2025;8:ooaf048.
15. Massachusetts General Brigham Laboratory of Computer Science. DXplain versus GPT-4 and Gemini on 36 clinical cases with and without laboratory data. 2025 (record to be confirmed).
16. Shea YF, et al. Use of GPT-4 to analyze medical records of patients with extensive investigations and delayed diagnosis. *JAMA Netw Open* 2023;6:e2325000.
17. Bhasuran B, et al. Preliminary analysis of the impact of lab results on large language model generated differential diagnoses. *npj Digit Med* 2025;8:159.
18. The evaluation illusion: benchmark instability in clinical large-language-model studies. *npj Digit Med* 2025 (s41746-025-01963-x).
19. Pollard TJ, et al. The eICU Collaborative Research Database. *Sci Data* 2018;5:180178.
20. Johnson AEW, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data* 2023;10:1.
21. Hoffmann G, et al. Using machine learning techniques to generate laboratory diagnostic pathways—a case study. *J Lab Precis Med* 2018;3:58.
22. Quinlan JR. Thyroid disease data set (thyroid0387). UCI Machine Learning Repository.
23. Ramana BV, et al. A critical study of selected classification algorithms for liver disease diagnosis. *Int J Database Manag Syst* 2011;3:101–114.
24. Reyna MA, et al. Early prediction of sepsis from clinical data: the PhysioNet/Computing in Cardiology Challenge 2019. *Crit Care Med* 2020;48:210–217.
25. Collins GS, et al. TRIPOD+AI statement. *BMJ* 2024;385:e078378.
26. KDIGO 2024 Clinical Practice Guideline for CKD. *Kidney Int* 2024;105:S117–S314.
27. American Diabetes Association. Standards of Care in Diabetes—2024. *Diabetes Care* 2024;47(Suppl 1).
28. Thygesen K, et al. Fourth universal definition of myocardial infarction. *Eur Heart J* 2019;40:237–269.
29. Vickers AJ, Elkin EB. Decision curve analysis. *Med Decis Making* 2006;26:565–574.
30. Bond WF, et al. Differential diagnosis generators: an evaluation of currently available computer programs. *J Gen Intern Med* 2012;27:213–219.

*(Reference list to be verified against publisher records before submission; ref. 15 and 18 need final citations.)*

## Figure legends

**Fig. 1 | Architecture.** Panel, age/sex and optional context → UCUM normalisation and derived indices → rule layer (33,183 guideline rules) → expert syndrome layer → fusion → ranking hygiene (causal attribution, chronicity, UDMI) → two-tier cited differential.

**Fig. 2 | Pre-registration workflow and the reference-standard ceiling.** (a) SAP, freezes and the two one-shot quarantine rounds, including the failed round. (b) Decomposition of 2,707 eICU label targets and recall on the 1,460 panel-supported labels for the product release, v7 and the registry-off ablation.

**Fig. 3 | Untrained engine versus supervised models on identical inputs (eICU).** Per-group AUROC of Hemoglyph, five-fold out-of-fold gradient boosting and logistic regression.

**Fig. 4 | NHANES screening across three independent cycles.** AUROC per task for the development cycle (2017–18) and quarantine cycles (2013–14, 2015–16), n = 3,000 each.

**Fig. 5 | Sepsis: a pre-registered negative result.** Engine versus supervised logistic AUROC in prediction and concurrent frames across sets A, B and B2.

**Fig. 6 | Blinded LLM comparison (400 stays, 596 labels).** Per-group recall@5 and rank-bin distribution for Hemoglyph and the GPT-4-class model.

## Tables

**Table 1 | Data sources, reference standards and roles.**

| Dataset | Setting | Reference standard | Role | n evaluated |
|---|---|---|---|---|
| eICU-CRD demo v2.0.1 | 186 US ICUs | clinician problem list → 31 groups | development and per-release gate | 2,314 stays; 2,432 labels |
| MIMIC-IV demo | US tertiary hospital | ICD-10 codes | quarantine 1 | 235 admissions; 507 pairs |
| NHANES 2017–18 (J) | US community survey | guideline criteria; self-report | development | 3,000 adults |
| NHANES 2013–14 (H) | idem | idem | quarantine 1 | 3,000 |
| NHANES 2015–16 (I) | idem | idem | quarantine 2 | 3,000 (healthy subset 79) |
| PhysioNet/CinC 2019 A / B / B2 | US ICU hourly records | Sepsis-3 onset | pre-registered single target; B, B2 quarantine | 4,871 / 4,558 / 4,991 patients |
| UCI thyroid0387 | referral laboratory | expert comment | external | 3,162 records |
| UCI HCV | donors and hepatology clinic | clinical category | external | 615 |
| ILPD | Andhra Pradesh, India | liver-patient status | external | 583 |
| PMC-Patients | published case reports | published diagnosis | external anchor | 50 |
| Synthetic healthy panels | generated | all-normal | safety | 1,000 per seed |

**Table 2 | eICU-CRD demo (n = 2,314 stays), laboratory values only: recall of clinician-listed diagnoses by release.**

| Release | flat @3 | flat @5 | flat @10 | two-tier @5 | panel-supported @5 / @10 (n = 1,460) | two-tier panel-supported @5 / @10 |
|---|---|---|---|---|---|---|
| 13.4.2 (product) | 49.3 | 63.7 | 76.9 | — | 81.6 / 95.1 | — |
| 14.1.0 + v6 | 48.5 | 60.8 | 74.1 | 71.7 | 78.0 / 91.8 | 88.9 / 97.2 |
| **14.1.0 + v7 (frozen)** | **47.9** | **60.8** | **74.1** | **71.9** | **78.0 / 91.8** | **89.2 / 97.2** |
| registry off (ablation) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |

**Table 3 | External and quarantine datasets, engine v7.**

| Dataset / task | Metric | Value (95% CI) |
|---|---|---|
| NHANES I: diabetes / CKD / anaemia / iron deficiency / hyperuricaemia / hypercholesterolaemia | AUROC | 0.924 / 0.962 / 0.983 / 0.972 / 0.955 / 0.886 |
| NHANES I: self-reported diabetes / kidney disease | AUROC | 0.898 / 0.799 |
| NHANES H/I/J healthy adults | false assertions | 1/246, 0/79, 1/160 |
| UCI thyroid: hypothyroidism / hyperthyroidism | AUROC | 0.979 / 0.798 |
| UCI HCV: any liver disease / cirrhosis | AUROC | 0.925 (0.881–0.962) / 0.909 |
| ILPD | AUROC | 0.704 (0.661–0.747) |
| MIMIC-IV demo | recall @5 / @10 | 47.5 / 62.1% |
| PMC case reports, manual labs: specific / syndrome | top-5 | 26% / 68% |
| Sepsis set B2 prediction / concurrent (labs + vitals) | AUROC | 0.588 (0.559–0.616) / 0.635 (0.597–0.673); logistic 0.679 / 0.726 |

**Table 4 | Blinded comparison with a GPT-4-class LLM, 400 eICU stays, 596 labels.**

| Metric | Hemoglyph | LLM |
|---|---|---|
| recall@1 | 23.3% (20.1–26.9) | 28.2% (24.7–31.9) |
| recall@3 | 49.5% (45.5–53.5) | 50.8% (46.8–54.8) |
| recall@5 (primary) | **64.4% (60.5–68.2)** | 59.6% (55.6–63.4); McNemar p = 0.0093 |
| recall@10 | 74.5% (70.8–77.8) | 65.1% (61.2–68.8) |
| MRR | 0.397 | 0.408 |
| label absent from list | 21.1% | 34.9% |
| test–retest (40 panels) | deterministic | agreement 85.7%, κ 0.69 |
| critical values flagged (50 stays) | 39/39 | 39/39 |

## Supplementary information

Note 1 SAP and amendments; Table S1 engine changes C1–C16; Table S2 quarantine criteria and outcomes; Table S3 participant flow; Fig. S1 provenance audit; Fig. S2 per-release eICU metrics; Fig. S3 per-group panel-supported recall; Fig. S4 calibration; Fig. S5 context-echo analysis; Table S4 subgroup analysis; Table S5 next-test utility; Data 1 per-stay outputs and LLM prompts/outputs.
