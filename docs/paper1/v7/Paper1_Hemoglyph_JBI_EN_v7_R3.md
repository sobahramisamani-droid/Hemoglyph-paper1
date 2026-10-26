# A verifiable, auditable, locally run rule engine for laboratory-panel interpretation: architecture, property-based verification, source-concordance audit, pre-specified retrospective evaluation and blinded comparison with an unnamed frontier LLM

*Research prototype — not approved or intended for clinical use. Revision R3 (2026-10-26) — methodological/technical article; target: Journal of Biomedical Informatics.*

**Highlights**
- Offline rule engine ranks a cited laboratory differential; every output traces to a rule and source
- Property-based verification exposed one ranking defect that 353 vignettes had missed
- A frozen, one-shot evaluation on >20,000 encounters; the first quarantine round failed and is reported
- Untrained engine at parity with an unnamed frontier LLM on recall@5; deterministic where the LLM was not
- Source-concordance audit: 92 % of sampled rules not verifiable from their locators; limits stated

Sobhan Bahrami^1*^, Zhaleh Tahmasebinejad^2,3^, Ehsan Bahrami Samani^2^

^1^ Allameh Helli 10 High School (NODET), Tehran, Iran. ^2^ Statistics and Data Science Clinic, Faculty of Mathematical Sciences, Shahid Beheshti University, Tehran, Iran. ^3^ Research Institute for Endocrine Sciences, Shahid Beheshti University of Medical Sciences, Tehran, Iran [to be confirmed by Z.T.].
\* Correspondence: sobahramisamani@gmail.com · ORCID 0009-0004-6639-5081

## Abstract

Hemoglyph is an offline research-prototype engine that ranks a cited differential from a structured laboratory panel using 33,183 guideline-transcribed executable rules (99.2% AI-drafted by a non-clinician author, not yet clinically audited) without outcome training. Under an internal, hash-frozen analysis plan with two one-shot quarantine rounds—the first failed its superiority criteria, which were then weakened to non-inferiority—the frozen engine was evaluated on the eICU demo (2,314 ICU stays), MIMIC-IV demo, 9,000 NHANES adults, 14,420 sepsis patients and external cohorts. From laboratory values alone, 60.8% (95% CI 58.7–62.9) of clinician-listed ICU diagnoses appeared in the top-5 at precision@5 14.2% against an incomplete problem list; a prevalence baseline reached 51.3%, so the engine contributes ordering, not coverage. NHANES AUROCs reproduced across three cycles (0.88–0.99), with 2 false assertions among 485 healthy adults. Blinded on identical inputs, the engine and an unnamed frontier LLM were at parity on recall@5 (60.7% vs 59.6%, p = 0.54); the LLM led at rank 1 but was only moderately self-consistent (κ 0.69). Sepsis prediction failed as pre-specified. Ablation located the result in 272 hand-curated anchors and the syndrome layer, not the AI-drafted bulk. A non-clinical source-concordance audit of 200 sampled rules (Supplementary Note 8) found 92% unverifiable from their locators and 7.5% demonstrably discordant; a clinical audit has not been performed. Iranian populations were not evaluated. Code and rules are public.

## Introduction

Roughly 70% of clinical decisions draw on laboratory results, yet interpretive comments accompany only a small fraction of reports, and post-analytical errors—missed critical values, patterns spanning several analytes, unit confusion—remain a leading source of diagnostic harm [1–3]. Three families of software address this gap. Rule-based expert systems embedded in laboratory information systems are transparent but narrow, hand-maintained and rarely evaluated outside their home institution [4,5]. Supervised models discriminate specific targets well but need labelled data, degrade under distribution shift and cannot be audited clause by clause [6,7]. Large language models (LLMs) produce fluent interpretations of laboratory reports, but their outputs vary between runs, generally cannot run on commodity laboratory hardware without transmitting patient data, fabricate references and misclassify values as high or low even when reference ranges are supplied [8–11].

A fourth option—an engine that interprets whole panels from an explicit, versioned knowledge base, runs offline and emits a ranked, explainable differential—has seldom been evaluated at scale. The barrier is methodological: such engines are usually validated on vignettes written by their own authors, and the few real-data evaluations use a single institution and no comparator [12]. Mature diagnostic decision-support systems (Isabel, DXplain) have been compared with GPT-4-class models and found within a few percentage points on recall while being reproducible [13–16]; none isolated laboratory-only reasoning. Meanwhile the public infrastructure for executable guideline knowledge has contracted: the AHRQ CDS Connect repository went offline in April 2025, and a dated search (2026-10-24) of CDS Connect, ECRI Guidelines Trust, NICE, WHO SMART guideline kits, OpenCDS/Arden collections and PubMed found no openly licensed, machine-executable rule set specific to laboratory-panel interpretation (Supplementary Note 5).

Here we report the design and a pre-specified, multi-dataset retrospective evaluation of Hemoglyph. Every result concerns the inference engine fed with structured analyte–value pairs; the optical-character-recognition front end of the desktop product was not evaluated, and the figures below are not end-to-end performance from a scanned report. Our aims were (i) to describe an architecture that keeps every output traceable to a cited rule; (ii) to evaluate the frozen engine against clinician- and guideline-derived reference standards in public datasets spanning intensive care, community survey, referral laboratory, hepatology and case reports; (iii) to compare it with a single-analyte threshold, with supervised models trained on the same inputs and—blinded, on identical inputs—with a contemporary LLM; (iv) to quantify the ceiling imposed by the reference standard; and (v) to report failures transparently. The engine evaluated here (`analyse_gidlines.py`, v7) is the same file that ships inside a proprietary desktop product owned by the first author; this interest is declared under Competing interests and motivated the frozen, one-shot design. We frame this as an engineering and retrospective evaluation study of a research prototype, not a claim of clinical validation.

## Results

### System and knowledge base

Hemoglyph is a single-process Python engine (Fig. 1). Inputs are analyte–value pairs with units plus age, sex and encounter type; clinical context and serial values are optional. After UCUM-based unit normalisation and derivation of 100 indices (CKD-EPI 2021 eGFR, corrected anion gap, FIB-4 and others), a rule layer evaluates 33,183 executable rules (registry 14.1.0: 272 hand-curated anchors and 32,911 AI-drafted, unaudited candidates) derived from 785 guideline sources; a curated expert syndrome layer (~900 multi-analyte constellations with tiered strengths and context guards) adjusts and guards; a fixed fusion step combines rule votes, Bayesian priors and fuzzy degrees; and a ranking-hygiene step applies causal attribution (a covering diagnosis explains its downstream findings), KDIGO chronicity rules and the universal definition of myocardial infarction. Output is a two-tier list—specific diagnoses and umbrella syndromes—each with `explained_by` findings, an evidence state and suggested next tests. The engine is deterministic (byte-identical output in 50/50 repeated stays), runs on one CPU core in ~1 s per panel and makes no network calls. Open and proprietary components are tabulated in Supplementary Table S15; only the open components were evaluated.

The registry was constructed with AI assistance from guideline text and filtered by automated consistency audits; it has not been audited rule-by-rule by clinicians, so the per-rule error rate is unknown. Each output entry displays its rule's status and evidence tier as machine-readable fields. A provenance audit resolved 112 DOIs via Crossref and reached 533 landing pages; 39 sources were unreachable from our sandbox, 34 lacked a locator, nine invalid DOIs were removed and 28 rules were flagged `unverified_source` (Supplementary Table S10, Fig. S1).

### Pre-specification, freezes and quarantine

Evaluation followed an internal statistical analysis plan with 15 dated amendments (Supplementary Note 1), time-stamped and hash-frozen inside the repository but not publicly registered; we therefore write 'pre-specified', not 'pre-registered'. Before each quarantine round, code and registry were frozen with a SHA-256 manifest, and quarantine data were run once (the MIMIC-IV demo re-run with v7 is the labelled exception). Round 1 (MIMIC-IV demo, NHANES 2013–14, PhysioNet sepsis set B) failed two primary criteria written as superiority over the prior release, because guideline-correctness changes (a single creatinine no longer asserts chronic kidney disease) lowered CKD label recall. We report that failure, re-specified the criteria as non-inferiority (Amendment 15, dated after Round 1 and before any Round-2 file was opened: NHANES AUROC within 0.03 on six targets with ≤1% healthy false assertions; sepsis AUROC not more than 0.02 below; no new safety-battery failure), implemented six further correctness changes (v7) and ran Round 2 (NHANES 2015–16, sepsis set B2, new healthy sweep), which met them (Fig. 2a; Supplementary Table S2). Because the criteria changed between rounds, Round 2 is supportive evidence of non-regression, not the confirmatory test originally planned. All results below are for frozen v7/14.1.0 unless stated.

### Intensive care (eICU-CRD demo)

In 2,314 adult ICU stays from 186 US hospitals, using the first panel with ≥8 analytes and no clinical text, 47.9% (stay-clustered 95% CI 45.8–50.0) of 2,432 clinician-listed, laboratory-relevant diagnoses appeared in the top-3, 60.8% (58.7–62.9) in the top-5 and 74.1% (72.2–76.0) in the top-10 of the flat differential (Table 2); a further 275 coded labels lacked the key analyte and are reported as 'analyte missing'. Raising the analyte threshold to ≥25 changed top-5 recall by ≤1 point. Counting either tier, top-5 recall was 71.9%. Precision@5 was 14.2% (13.3–15.2), F1@5 23.1% and NDCG@5 56.5% (54.1–58.8) against an incomplete problem list (lower bounds). Recall@5 was 88.1% for acute myocardial infarction, 82.8% for heart failure, 83.0% for anaemia and 77.5% for acute kidney injury, but 49.1% for sepsis, 45.1% for diabetes and 35.8% for CKD.

A prevalence-ranking baseline (most frequent groups whose key analyte is present) reached recall@5 51.3% and NDCG@5 39.0%; at k = 10 its recall (76.8%) exceeded the engine's 74.1%, so the engine's advantage is ranking, not coverage (Supplementary Table S11). Automated laboratory-criterion matching of the 10,380 top-5 assertions (fixed single-analyte criteria written before scoring, not clinician adjudication) found 14.2% on the problem list, 54.8% not coded but satisfying the group's laboratory criterion in the same panel, 12.6% criterion-negative—the closest available estimate of true false positives—and 18.4% in groups without a single-analyte criterion. Precision@5 therefore lies between 14.2% and 69.0%; whether the uncoded criterion-positive findings were clinically useful cannot be judged without a clinician.

The reference standard bounds these metrics (Fig. 2b). Of 2,707 label targets, 541 belonged to groups with no single laboratory criterion, 275 lacked the key analyte and 431 were contradicted by the first panel (e.g. hypokalaemia coded with potassium 4.1 mmol/L after repletion). Among the 1,460 labels whose first panel met the guideline criterion—a secondary metric whose thresholds were fixed before scoring but whose definition followed observation of the ceiling—flat recall was 29.6/62.5/78.0/91.8% at k = 1/3/5/10 (Supplementary Fig. S3).

Three comparators used identical inputs (Fig. 3). A raw key-analyte threshold matched or exceeded the engine's AUROC for single-analyte groups (hyperkalaemia 0.96 vs 0.92; anaemia 0.83 vs 0.78), as expected for findings that are definitions. Gradient boosting and logistic regression trained on the labels (five-fold out-of-fold) exceeded the untrained engine only in outcome-defined groups without a laboratory signature—sepsis (0.82 vs 0.68), GI bleeding (0.85 vs 0.75), alcohol withdrawal (0.80 vs 0.54)—and were matched or beaten in nine guideline-defined groups (CKD 0.79 vs 0.81; hyponatraemia 0.85 vs 0.89; cirrhosis 0.83 vs 0.87). Adding documented history and medications raised recall@5 by 0.9 points for labels not named in the history (n = 2,467) but by 23.3 points for labels already named (n = 240); the context arm mainly echoes documentation and is reported only in the Supplement.

### Component ablation

Two components carry the signal (Table 5; Supplementary Table S12). Removing the rule-engine vote cost 12.1 points of flat recall@5 (−14.4 to −9.8) and removing the expert syndrome layer cost 9.5 points (−11.1 to −7.9). The Bayesian network contributed 1.3 points; the fuzzy, knowledge-graph and risk-model layers and the fusion refinements each lay within ±0.5 points; uniform fusion weights cost 1.4 points and rule-heavy or rule-light weights changed recall by ≤1.1 points, so the hand-set weights are not a hidden tuning knob. Restricting the registry to the 272 curated anchors (32,911 AI-drafted rules off) lowered flat recall@5 by 0.9 points (−2.1 to +0.2) with the syndrome layer on and by 3.1 points with it off; the syndrome layer contributed 9.5 points with the full registry and 11.7 with anchors only. The AI-drafted bulk is therefore partly redundant with the syndrome layer rather than inert, but the headline rests on the curated anchors and syndrome constellations—the components not yet independently audited—and registry scale is not claimed as a merit.

### Community survey: three independent NHANES cycles

In 3,000 adults per cycle, unweighted AUROCs reproduced across the development cycle (2017–18) and the two quarantine cycles (2013–14, 2015–16): diabetes 0.946/0.938/0.924, CKD 0.959/0.968/0.962, anaemia 0.972/0.994/0.983, iron deficiency 0.989/–/0.972, hyperuricaemia 0.943/0.958/0.955, hypercholesterolaemia 0.905/0.883/0.886 and ALT elevation 0.872/0.880/0.877 (Fig. 4; Table 3). A correction: the previous version quoted 0.721 for ALT in 2017–18; that value came from registry 14.0.0, not the frozen v7. These laboratory-defined labels overlap the inputs and test criterion recognition; against self-reported physician diagnosis, AUROC was 0.90–0.92 for diabetes and 0.75–0.82 for kidney disease. Examination weights changed laboratory-defined AUROCs by ≤0.015 but lowered self-reported kidney disease in 2017–18 from 0.816 to 0.744 (Supplementary Table S7). Among guideline-healthy adults (30-analyte filter, Supplementary Note 5), the engine asserted a disease in 1/160, 1/246 and 0/79 (2/485, 0.4%); because the filter covers 30 analytes, this is a lower bound on false assertions. Separately, 0/1,000 synthetic guideline-normal panels produced a disease (a regression check, not evidence).

### External cohorts and case reports

On the UCI thyroid referral set (6,932 scored records) AUROC was 0.979 (0.974–0.983) for hypothyroidism and 0.798 (0.783–0.814) for hyperthyroidism; on the HCV cohort (n = 615) 0.925 (0.881–0.962) for any liver disease and 0.909 (0.837–0.969) for cirrhosis; on ILPD (n = 583) 0.704 (0.661–0.747). In MIMIC-IV demo (235 admissions, ICD-coded) top-5/10 recall was 47.9/61.7% for v6 in quarantine round 1 and 47.5/62.1% for the post-hoc v7 re-run. On 50 PMC case reports given only the laboratory paragraph, the specific diagnosis was in the top-5 in 26% and the correct syndrome in 68% (automatic parsing: 10% and 44%) (Table 3).

### Pre-specified negative result: sepsis

In PhysioNet/CinC 2019, the engine's sepsis score from first-24-h laboratory values discriminated Sepsis-3 onset with AUROC 0.600 (0.575–0.625) in set A, 0.610 (0.583–0.640) in quarantine set B and 0.588 (0.559–0.616) in set B2, versus 0.691, 0.712 and 0.679 for a supervised logistic model on the same features (Fig. 5). Guideline-sourced SIRS/qSOFA rules added afterwards (Amendment 15; developed on A, validated once on B2) added about 0.04 AUROC and are labelled post hoc. Hemoglyph is not a sepsis predictor.

### Blinded comparison with an unnamed frontier LLM

On 400 stays (291 with scorable labels; 596 labels) an unnamed frontier LLM, accessed through an agent platform that does not disclose the model, received the identical panel, age and sex and returned ten ranked diagnoses, blinded to labels (Supplementary Note 2). Recall@5—the pre-specified primary comparison—was 60.7% (56.5–65.0) for Hemoglyph versus 59.6% (55.3–63.6), difference +1.2 points (−2.5 to +5.1; cluster-adjusted McNemar p = 0.54). The LLM was better at rank 1 (28.2% vs 24.0%, p = 0.013) and rank 3 (50.8% vs 47.0%, p = 0.041); the engine at rank 10 (72.0% vs 65.1%, p = 0.0002) and left fewer labels absent (21.8% vs 34.9%); mean reciprocal rank 0.391 vs 0.408 (Fig. 6; Table 4). Crediting either engine tier—a post-hoc metric with no LLM counterpart—gave 69.8% vs 59.6%. An earlier comparison with engine v5.1 had favoured Hemoglyph (64.4%, p = 0.009); the v7 correctness changes removed that advantage. The engine led for GI bleeding (84 vs 50%), diabetes (50 vs 37%) and hypokalaemia (59 vs 41%); the LLM for metabolic acidosis (79 vs 50%), hyperkalaemia (90 vs 70%) and DKA (83 vs 73%). On 40 re-read panels the LLM's agreement with itself was 85.7% (κ = 0.69) and its recall@5 varied by ±5 points across reads and prompts—more than the engine–LLM difference. Both flagged 39/39 CAP critical values in 50 stays, a shared safety floor.

### Calibration, subgroups and robustness

Pooled over 52,689 stay–group units, AUROC was 0.797 but raw scores were over-confident: calibration slope 0.25, ECE 0.162, Brier 0.117 (Fig. 7). Split-half cross-fitted isotonic recalibration reduced ECE to 0.003 within eICU—evidence that ranks are recalibrable, not a transferable calibration. Raw scores are therefore ranks, not probabilities. Twenty-seven of 29 groups with ≥10 labels had AUROC above 0.5 after Benjamini–Hochberg adjustment (exceptions: malnutrition, hypocalcaemia). Recall@5 was 62.3% in men and 58.5% in women, 58–64% across age bands and 59–61% across the three largest ethnicity strata (Supplementary Table S4); three strata in one US dataset do not support a fairness claim. The engine contains no race or ethnicity term, and its optional `ethnicity` field is parsed but never read. The release passed the non-regression gate: 689/689 unit tests, 352/353 adversarial vignettes (alcoholic pancreatitis ranked second behind alcohol-use disorder, deliberately not patched), 753/755 perturbation pairs (both failures are replicates of one thiazide-hyponatraemia vignette under 3% noise) and the SI/conventional unit-twin battery (Supplementary Note 4).

### Verification: executable invariants and source concordance

Two further checks were added after the freeze; neither alters a frozen number. First, a property-based test suite
(`tests/test_properties.py`, engine v8.1) states invariants that any correct laboratory-interpretation engine must satisfy
and checks them on randomised panels rather than hand-written vignettes: determinism (identical output on repeated runs),
unit invariance (SI and conventional units give the same ranking, tolerance 10⁻³), directional monotonicity (a more extreme
value never lowers the probability of the finding it defines; 14 analyte–direction pairs including creatinine, glucose up and
down, potassium up and down, sodium up and down, haemoglobin, ALT, bicarbonate, leukocytes up and down, platelets),
absent-analyte invariance (a syndrome is never asserted from an analyte that is not present) and context invariants
(documented CKD never raises acute kidney injury; borderline-value flags behave as specified). All 21 tests pass. The suite
exposed one genuine defect that the 353 adversarial vignettes had not: a well-supported renal finding was capped beneath a
presumptive explainer scoring below 0.80, so the leading renal probability fell as creatinine rose from 1.6 to 2.2 mg/dL; the
fix applies an existing rule uniformly and passed the full gate (eICU 48.4/61.0/74.1% versus 47.9/60.8/74.1%, inside the v7
confidence intervals). These tests establish logical consistency, not clinical correctness: a mistranscribed threshold passes
every invariant.

Second, a source-concordance audit asked whether the rule transcribes what its cited source says (Methods; Supplementary
Note 8). Of 200 rules sampled under a frozen protocol (100 curated anchors, 100 candidates), only 16 could be resolved from
the locators the registry provides: 15 were discordant (7 attribution errors among curated anchors, such as a hypernatraemia
rule citing the hyponatraemia guideline, and 8 thresholds or definitions absent from an on-topic source, including a
candidate AKI "criterion" defined by a fixed creatinine > 1.1 mg/dL and attributed to KDIGO 2012, which defines AKI only by
change from baseline) and 1 concordant. The remaining 184 (92%, 95% CI 87.4–95.1) were unresolvable—12 with no retrievable
text, 55 with only a title or abstract, 46 citing only generic methodological standards (WHO essential diagnostics list, CLSI
EP28/C59) that cannot contain a disease-specific threshold, and 71 landing pages. Because an attribution error is visible from
a title while concordance needs the full text, the 15/16 ratio is not an estimate of the registry's discordance rate; the
defensible statements are that at least 7.5% (4.6–12.0) of sampled rules are demonstrably discordant and that the registry,
as released, is not auditable rule-by-rule from its own locators. Rater 1 was an AI agent (declared); a second, human
non-clinician rater and inter-rater agreement are pending and will be added before submission.

## Discussion

A guideline-transcribed rule engine with no training data recovered 61% of clinician-listed ICU diagnoses in five suggestions from laboratory values alone (78% on the post-hoc panel-supported subset), reproduced screening AUROCs across three NHANES cycles while asserting disease in at most one adult per healthy cohort, and was statistically indistinguishable from an unnamed frontier LLM on the pre-specified metric, with the LLM stronger at rank 1 and the engine at coverage. Its advantages are determinism, local execution and traceability to a cited rule, not accuracy. It failed, as pre-specified, to predict sepsis.

Five findings shape how these numbers should be read. First, the ~60% ceiling is largely a property of the reference standard: a quarter of admission-level labels were not inferable from the first panel, and a supervised model trained on the labels themselves did not exceed 0.82 AUROC for outcome-defined groups. The panel-supported metric was defined after the ceiling was observed and is structurally optimistic; we present it alongside, not instead of, the flat metric. Second, the untrained engine matched supervised models wherever a guideline definition exists and lost wherever the label is an outcome (sepsis, bleeding, withdrawal) learned from hidden correlates—the expected division of labour between knowledge and learning, which argues for hybrid rather than replacement designs. Third, the LLM and the engine make different errors: differences are small where a single analyte defines the label (renal impairment 83% vs 81%) and large where a multi-analyte pattern must be assembled or where the LLM prefers a broader term; the LLM's test–retest variability exceeded the between-system difference. Fourth, the ablation locates the result in the rule-engine vote and the curated syndrome constellations, written by a non-clinician first author from guideline criteria and not independently validated; the 33,000-rule registry adds one to three points. We therefore describe Hemoglyph as guideline-*transcribed* rather than guideline-derived: the result is what such a transcription achieves, not what the guidelines themselves would achieve. The expert floor (fused score ≥0.90 × rule vote) means the learned layers can modulate but not veto a rule—a deliberate bias towards explicit criteria that trades the possibility of a learned layer correcting a wrong rule for the guarantee that every surfaced diagnosis is traceable to one. Fifth, a prevalence-ranking baseline reaches recall@5 of 51% and overtakes the engine at k = 10; the engine's measurable contribution is ordering (NDCG@5 56.5% vs 39.0%; recall@3 47.9% vs 36.1%) and per-stay specificity (precision@5 14.2% vs 10.8%), and precision against an incomplete problem list remains low in absolute terms.

Our design addresses criticisms levelled at recent LLM benchmarks—unstable metrics, leakage and post-hoc selection [17,18]. Releases were frozen with manifests; quarantine data were run once; a failed round is reported with its original criteria and the subsequent weakening to non-inferiority is disclosed; the post-hoc sepsis additions are labelled. The cost of correctness is visible: moving from the product release to v7 cost three points of flat recall, almost entirely because a single creatinine no longer asserts CKD and a normal leukocyte count no longer yields a syndrome; our first submission reported superiority over the LLM against an earlier engine version, and re-scoring against the frozen release reduced that to parity. Compared with Isabel and DXplain, which take symptoms and have been evaluated on 36–201 cases [13–16,30], this study isolates laboratory-only reasoning on more than 20,000 real encounters and releases its knowledge base under an open licence at a time when the main public executable-guideline repository has been withdrawn. Because the rules were AI-drafted, open release is a precondition for—not a substitute for—expert audit; every leaf carries a source locator, so a clinician can accept, amend or reject a rule and the change is versioned.

Where might such an engine be used? Not as an autonomous diagnostician. Its natural positions are the post-analytical step of a laboratory information system—interpretive comments and critical-pattern alerts generated locally—and a reproducible, auditable baseline against which LLM-based interpretation can be measured. The two architectures could be combined: a language model to extract and normalise free-text results (the step at which our automatic parser lost half the PMC cases) and a rule engine to reason over them. We chose laboratory-only inputs as the primary arm because documented history inflates recall mainly by echoing the diagnosis already written down (+23 points for labels named in the history versus +1 otherwise). We did not tune the engine to the sepsis task after the pre-specified result because an outcome-fitted rule would have been a supervised model in disguise.

After the freeze, twelve review-driven improvement proposals were tested against the frozen artefacts before any code was changed (Supplementary Note 7; Methods). Four were supported—confidence bands, re-sourcing of 28 rules, MELD-Na/PLR indices and a separate supervised sepsis companion (held-out patient-level AUROC 0.654/0.631 versus the engine's 0.610/0.588)—and the rest were refuted: adaptive truncation traded precision for recall almost one-for-one, and the ketoacidosis misses were missing criteria, not covering suppression. The verification results reframe what this paper can claim. Executable invariants are a genuine methodological advantage of a rule engine over an LLM—they can be stated, run on every release and violated only visibly—and they found a defect that vignettes had missed. The source-concordance audit, however, shows the limit of such verification: the registry's locators are organisation-level URLs and generic standards, so most rules cannot be checked against their source at all, and where they could be checked the error was usually one of attribution. Concordance is a necessary, not sufficient, condition for validity—a rule can quote its source exactly and still encode an outdated threshold—so an independent clinical audit remains the essential next step, and section-level locators are a precondition for it. Consequent registry actions (planned for release 15, none altering the frozen v7 results): section- or table-level locators for every source, re-sourcing or retirement of the 46 sampled candidates—and the class they represent—whose only citation is a generic methodological standard, and correction of the five curated-anchor attribution errors identified. The output design (a rule identifier and source citation for every entry) is consistent with the transparency principle of Criterion 4 of the FDA's January 2026 clinical-decision-support guidance; determining regulatory status is outside the scope of this paper and no claim about it is made. None of these post-freeze versions (v8, v8.1) has been through a quarantine round, and no frozen number here derives from them.

What would change the evidence level? A rule audit by independent clinicians on a random sample with inter-rater agreement; the credentialed full eICU and MIMIC-IV releases, on which the released scripts run unchanged; and a clinician-in-the-loop crossover study measuring accuracy, time and automation bias, for which a protocol has been drafted. Until then, the claims of this paper are bounded to retrospective, laboratory-only performance.

### Limitations

The knowledge base has not been audited rule-by-rule by clinicians, and the non-clinical source-concordance audit reported here shows that 92% of sampled rules cannot even be checked against their cited source from the locator provided, while at least 7.5% are demonstrably discordant; the components that carry the result—272 anchor rules and ~900 syndrome constellations—were written by a non-clinician first author; 34 sources lack a locator; the Bayesian priors are hand-coded without a per-value citation table. No version-control history exists for the development period, so the claim that no change was outcome-fitted rests on the dated change log. Only the open demo subsets of eICU and MIMIC-IV were used; the reference standards are admission-level problem lists and ICD codes, not adjudicated panel-level diagnoses. The LLM comparison is an author-run self-baseline through an agent platform that does not disclose the model, so it is not reproducible against a named model; it used two prompts, no retrieval augmentation and no clinician adjudication, and the model's training data may include the public eICU demo. The quarantine criteria were weakened after round 1 failed; the panel-supported metric is post hoc; the OCR front end was not evaluated; laboratory-defined NHANES labels overlap the inputs; raw scores are uncalibrated; the external cohorts are small and ILPD discrimination was modest. No clinician-in-the-loop evaluation was performed. Iranian populations and non-English laboratory conventions were not evaluated. The first author is a secondary-school student with a financial interest in the commercial product, and the system, including 99.2% of the rules, was developed with AI-agent assistance. Hemoglyph is a research prototype with no regulatory clearance.

### Conclusion

An open, offline, guideline-transcribed rule engine—its rules drafted by one non-clinician author with AI assistance and not yet independently audited—interpreted structured laboratory panels close to the ceiling the first panel allows, reproduced population-screening performance across independent survey cycles under internally pre-specified criteria that were weakened after a failed first quarantine round, and was indistinguishable from an unnamed frontier LLM on a blinded paired primary metric, while remaining auditable. Its limits—outcome-defined syndromes, uncalibrated scores and an unaudited AI-drafted rule base—are stated so that they can be measured and closed.

## Methods

### Engine

Hemoglyph (`analyse_gidlines.py` [sic—historical file name], v7) processes a panel in five stages: normalisation (UCUM units, aliases, age/sex reference intervals, 100 derived indices); a rule layer over registry 14.1.0 (33,183 executable leaves, where a leaf is one registry record with a machine-evaluable condition on at least one analyte, a disease identifier and an `executable: true` flag—retired, template and empty-expression records are kept for provenance but never evaluated—a count that moved from 34,005 in release 13.1.0 through 33,230 (13.3.0), 33,170 (13.4.2) and 33,178 (14.0.0) as 1,307 rules were retired and 485 guideline-sourced rules were added, Supplementary Table S10; each with analyte conditions, population gates, evidence role—diagnostic criterion weight 6, supportive or screening weight 3—disease identifier and source); an expert syndrome layer (~900 constellations with anchor strengths 0.95/0.88/0.80/0.72/0.45, operators absent/between/neg/present and context predicates for pregnancy, age, sex, medication, condition, family history and encounter); fixed-weight fusion (weights 0.35 rule engine, 0.25 Bayesian, 0.20 fuzzy, 0.10 knowledge graph, 0.10 risk models, set by the first author as a judgement that explicit criteria should dominate, with four context profiles, e.g. toxicology 0.55 for rules; no weight was derived from or tuned on any evaluation dataset, and Table 5 reports the sensitivity to them) with an expert floor (the fused score of a diagnosis cannot fall below 0.90 × the rule-layer vote, so that the four other layers can modulate but never veto a guideline rule). The Bayesian layer has 75 disease nodes with hand-coded prevalence priors (constants or age bands, e.g. type 2 diabetes 0.08, CKD 0.10) and hand-coded likelihood ratios for 68 of them, taken from diagnostic-accuracy literature cited in code comments (e.g. lipase ≥ 3 × ULN, LR+ 18 for acute pancreatitis); none is estimated from data, so the engine remains untrained in the sense that no parameter was fitted to any patient record; and ranking hygiene (causal attribution via a disease–finding explanation graph, covering-diagnosis suppression of explained findings, KDIGO chronicity, UDMI acuity, maximum 25 entries). Engine changes between releases (C1–C16) are listed with dates in Supplementary Table S1; none was fitted to outcome data and no rule was written for a specific missed case. This is supported by the dated change log and by the fact that every change is expressed as a guideline citation plus a synthetic vignette rather than a parameter value; no version-control history exists for the development period, so the statement cannot be audited by commit diff and is offered as a documented process claim, not a verified one.

### Knowledge base construction and provenance

'AI assistance' means the following. For each guideline source the first author prompted a general-purpose LLM with the source text or citation and a fixed JSON schema; the model returned candidate rule records (analyte, operator, threshold, unit, population gate, evidence role, disease identifier, source locator). These records were not individually edited by a human: they were accepted or rejected by automated audits (schema validity, analyte exists in the 2,045-analyte feature registry, unit convertible, threshold within physiological range, no duplicate or contradictory record, context gate present where the guideline requires one, source locator resolvable) and carry the status `candidate_requires_specialist_validation`. The 272 anchor rules were written or line-edited by hand by the first author from the primary guideline text and carry higher weight; the 13 demoted anchors and all rules retired between releases were removed by rule-level review of defect reports, not by outcome data. No record of the proportion of candidate rules that a human read exists, and we therefore describe the bulk as AI-drafted and automatically audited, not human-reviewed. Sources: KDIGO, ADA, WHO, ACC/AHA, EASL, ATA, ESC, CLSI, Tietz and others listed in the registry. Source locators were verified with `registry_source_verify.py` (Crossref resolution, HTTP reachability). Counts by release: 13.3.0, 33,230 rules/747 sources; 13.4.2, 33,170/781; 14.1.0, 33,183/785.

### Pre-specification, freezes and quarantine

The SAP (Supplementary Note 1) fixed metrics, label maps, thresholds and comparators; 15 amendments are dated and justified. Freezes v14 and v15 recorded SHA-256 manifests. Quarantine round 1 (MIMIC-IV demo; NHANES 2013–14; sepsis set B) used superiority criteria and failed; round 2 (NHANES 2015–16; sepsis set B2; healthy sweep with a new seed) used non-inferiority criteria specified before execution and passed. Two data-loader defects discovered during round 2 (string patient identifiers; a dropped derived NHANES variable) were fixed before scoring without touching the engine and are documented.

### Datasets and reference standards

eICU-CRD demo v2.0.1 [19]: 2,520 stays → 2,512 adults → 2,314 with ≥ 8 analytes in the first panel; reference = clinician problem list mapped by regular expressions to 31 groups (audit on 400 stays: precision 100%, sensitivity 98.3%; per-group values in Supplementary Table S9). MIMIC-IV demo [20]: 235 admissions, ICD-10 reference. NHANES 2013–14, 2015–16, 2017–18: 3,000 randomly sampled adults per cycle with biochemistry and CBC; references per ADA, KDIGO, WHO and ACG criteria and self-reported diagnoses. PhysioNet/CinC 2019 [24]: set A 4,871 patients (439 sepsis), set B 4,558 (268), set B2 4,991; Sepsis-3 onset label; the post-hoc concurrent analysis (labs and vitals within ±6 h of onset) used 247 cases and 600 dwell-time-matched controls drawn from set B2 only, which is why Table 3 reports it for B2 alone. UCI thyroid0387 [22], UCI HCV [21], ILPD [23], PMC-Patients 50 case reports [17]. Participant flow in Supplementary Table S3.

### Metrics

Primary: flat recall@k of clinician-listed diagnoses (k = 3, 5, 10). Secondary: two-tier recall; panel-supported recall (labels whose first panel met a guideline criterion fixed in `panel_supported_metric.py` before scoring; groups without a single criterion excluded); per-group AUROC of the group score. Screening: AUROC and false-assertion rate in all-normal adults. Sepsis: AUROC of the sepsis-group score. Calibration: calibration slope and intercept, ECE (10 equal-frequency bins), Brier with cluster-bootstrap CI, log-loss and decision curves before and after cross-fitted isotonic regression [29]. Ablation: the frozen engine with one component disabled or altered per arm (each of five fusion layers, syndrome layer, registry, anchor-only registry, `unverified_source` rules removed, fusion-weight and shrinkage settings), scored on the same 2,314 stays.

### Comparators

B1, raw key-analyte threshold; B2, gradient boosting and logistic regression trained on the same analytes, five-fold out-of-fold; registry-off ablation; LLM: an unnamed frontier model run by the authors through a chat interface on 2026-10-21 (n = 60), 2026-10-22 (n = 100) and 2026-10-23 (n = 240), re-read 2026-10-24 and alternative prompt 2026-10-25; the interface exposes no temperature or sampling parameters, so these are the provider defaults; the LLM was accessed through the Arena.ai agent platform, which routes requests among several frontier model families (including GPT, Claude and Gemini) and does not expose the specific model or version to the user; 'unnamed frontier LLM' therefore denotes a capability tier, not a verified identity, and the comparison cannot be reproduced against a named model version—a limitation stated in the Discussion; blinded to labels, with a fixed prompt requesting ten ranked diagnoses from the identical panel, age and sex; 40 panels re-read for test–retest and read with an alternative prompt; scoring against the frozen engine v7 by the same label map and script. Prompts, outputs and the full protocol are released (Supplementary Note 2).

### Post-freeze development version (v8)

Engine v8 (2026-10-26) differs from the frozen v7 in three presentation- or index-level additions—MELD/MELD-Na (Kamath 2001; Kim 2008; OPTN formula with sodium clamped to 125–137 mmol/L and creatinine capped at 4 mg/dL; computed only when bilirubin > 2 mg/dL or INR > 1.5) and the platelet-to-lymphocyte ratio as derived patterns with `supports = []`, and a `confidence_band`/`concise` field on each differential entry (bands ≥ 0.70 high, 0.60–0.69 moderate, 0.50–0.59 low, otherwise consider; descriptive, calibrated on the development set only). The gate exists because MELD was derived in, and is calibrated for, patients with established hepatic dysfunction; computed on a panel with normal bilirubin and INR it reduces to a creatinine term and would mislabel isolated kidney injury as liver prognosis. The remaining difference is registry 14.2.0, which re-sources 28 rules (9 source records) with Crossref-resolved DOIs and changes no rule logic, threshold, weight or executable flag (`eval/registry_patches/patch_14_2_0.py`). The sepsis companion (`eval/sepsis_ml/sepsis_risk_module.py`) uses the same three PhysioNet/CinC 2019 subsets as the engine evaluation (set A 4,871 patients for training; sets B 4,558 and B2 4,991 held out; Table 1); features are listed in the script; the logistic model is class-balanced L2 (C = 0.05); the gradient-boosting reference uses depth ≤ 4, ≤ 15 leaves, ≥ 300 samples per leaf, L2 = 5 and early stopping on 15% of set A. The alert threshold for the utility score was chosen on set A over a grid of score quantiles. Disclosure: the boosting hyper-parameters were tightened once after a first evaluation on set B showed over-fitting (training AUROC 0.997, set B 0.719); set B2 was not opened until the final configuration. Patient-level AUROC uses the maximum score over hours before the shifted label for septic patients and over all hours for non-septic patients; horizon AUROC compares the score exactly h hours before onset with a random hour of each non-septic patient. The v8 gate (`eval/results/gate_v8/`) repeats the v7 gate (three vignette batteries, 1,000-panel healthy sweep, 755-pair perturbation battery, unit tests, eICU labs-only run) with a pre-stated non-inferiority margin of 0.5 recall points.

Engine v8.1 (2026-10-26) added a property-based test suite (determinism, unit invariance, directional monotonicity for 14 analyte–direction pairs, absent-analyte and context invariants), fixed the one defect it exposed (the final finding-demotion pass capped a well-supported finding beneath a presumptive explainer scoring < 0.80; the existing rule that a weak explainer organises but does not lower a finding is now applied uniformly) and added a reporting-only measurement-uncertainty layer (biological-variation-based probability that a value truly lies outside its reference limit; no effect on any score). Its development gate reproduced every safety-battery result; eICU flat recall@3/5/10 was 48.4/61.0/74.1% versus 47.9/60.8/74.1% for v8, a difference inside the v7 confidence intervals and reported as parity.

### Source-concordance audit

Protocol frozen before sampling (`eval/source_audit/PROTOCOL.md`). Seed 20261026; 100 of 272 curated anchors and 100 executable candidates (50 "eICU-relevant": feature present in ≥ 50% of eICU first panels and disease in an evaluated label group; 50 uniform from the rest), registry 14.1.0. Fields compared: analyte, operator/threshold with unit, population qualifier, disease attribution. Labels CONCORDANT / DISCORDANT / UNRESOLVABLE with the tie-break "when in doubt, unresolvable"; unresolvable is never counted as concordant. Sources were retrieved by the registry locator (curl, 20 s), with Crossref title and PubMed abstract as fall-back for paywalled DOIs and direct PDF retrieval for KDIGO guidelines. Rates are reported with two denominators (resolvable and all sampled) and Wilson 95% CIs. Rater 1 was an AI agent under the first author's supervision; rater 2 is a human non-clinician co-author blind to rater-1 labels; Cohen's κ over the three labels will be reported.

### Statistics and software

Labels are nested in stays (ICC 0.04); eICU proportions and paired differences use stay-cluster bootstrap (4,000 resamples) and the cluster-adjusted McNemar test [31,32]; Wilson intervals elsewhere; 1,000-sample bootstrap or DeLong for AUROC; NHANES AUROCs additionally weighted by examination weights; Benjamini–Hochberg across per-group tests. Python 3.11/3.13, numpy, pandas, scikit-learn. Reporting follows TRIPOD+AI [25], adapted for a system that is not fitted to data (model-training items answered "not applicable" with justification), with the DECIDE-AI early-stage items consulted for the Limitations; the completed checklist is Supplementary Note 5.7.

## Data availability

eICU-CRD demo (physionet.org/files/eicu-crd-demo/2.0.1/), MIMIC-IV demo, PhysioNet/CinC 2019 (physionet.org/files/challenge-2019/1.0.0/training/), NHANES (wwwn.cdc.gov/nchs/nhanes), UCI and ILPD repositories are public. Per-stay outputs, label maps, LLM prompts and outputs are provided as Supplementary Data.

## Code availability

Engine and evaluation scripts (AGPL-3.0-or-later) and the rule registries (CC BY-SA 4.0) are public on GitHub (github.com/sobahramisamani-droid); the frozen v7/14.1.0 snapshot with freeze manifests, per-stay outputs and `reproduce.sh` will be archived on Zenodo with a DOI before publication. Hardware used for all timings: 2 vCPU Intel Xeon 2.60 GHz, 2 GB RAM, Linux 6.1, Python 3.13.

## Author contributions

S.B. conceived the system, built the engine and knowledge base, designed and ran the evaluation and wrote the manuscript. Z.T. reviewed the statistical analysis plan and the reporting of the quarantine evaluation and revised the manuscript. E.B.S. supervised the statistical methodology and critically revised the manuscript. All authors approved the final version. *(Contributions of Z.T. and E.B.S. to be confirmed before submission.)*

## Competing interests

S.B. designed and wrote the Hemoglyph software, owns the proprietary desktop application and would benefit from its commercial distribution; this is a financial interest in a favourable evaluation, which the pre-specified one-shot design and released evaluation scripts are intended to constrain. The engine source, registries and evaluation code are open. Z.T. and E.B.S. declare no competing interests. No funding was received.

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
7. Amjad H, Hussain Z, Hasan M, Ul Hassan M. Machine learning-based models for screening of anemia and leukemia using features of complete blood count reports. *Sci Rep* 2025;15:33333.
8. Cadamuro J, et al. Potentials and pitfalls of ChatGPT and natural-language artificial intelligence models for the understanding of laboratory medicine test results. *Clin Chem Lab Med* 2023;61:1158–1166.
9. Kurstjens S, et al. Accuracy of large language models in answering laboratory medicine questions. *Clin Chem Lab Med* 2024.
10. Hager P, et al. Evaluation and mitigation of the limitations of large language models in clinical decision-making. *Nat Med* 2024;30:2613–2622.
11. Savage T, et al. Diagnostic reasoning prompts reveal the potential for large language model interpretability in medicine. *npj Digit Med* 2024;7:20.
12. Laposata M, Dighe A. "Pre-pre" and "post-post" analytical error. *Clin Chem Lab Med* 2007;45:712–719.
13. Bridges JM. Computerized diagnostic decision support systems – a comparative performance study of Isabel Pro vs. ChatGPT4. *Diagnosis (Berl)* 2024;11:250–258.
14. Bridges JM, Jiang X, Ige M, Toyobo O. Computerized diagnostic decision support systems—Isabel Pro versus ChatGPT-4 part II. *JAMIA Open* 2025;8:ooaf048. doi:10.1093/jamiaopen/ooaf048.
15. Feldman MJ, Hoffer EP, Conley JJ, et al. Dedicated AI expert system vs generative AI with large language model for clinical diagnoses. *JAMA Netw Open* 2025;8:e2512994. doi:10.1001/jamanetworkopen.2025.12994.
16. Shea YF, et al. Use of GPT-4 to analyze medical records of patients with extensive investigations and delayed diagnosis. *JAMA Netw Open* 2023;6:e2325000.
17. Bhasuran B, et al. Preliminary analysis of the impact of lab results on large language model generated differential diagnoses. *npj Digit Med* 2025;8:159.
18. Agrawal M, Chen IY, Gulamali F, Joshi S. The evaluation illusion of large language models in medicine. *npj Digit Med* 2025;8:600. doi:10.1038/s41746-025-01963-x.
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
31. Durkalski VL, Palesch YY, Lipsitz SR, Rust PF. Analysis of clustered matched-pair data. *Stat Med* 2003;22:2417–2428.
32. Obuchowski NA. On the comparison of correlated proportions for clustered data. *Stat Med* 1998;17:1495–1507.


## Figure legends

**Fig. 1 | Architecture.** Panel, age/sex and optional context → UCUM normalisation and derived indices → rule layer (33,183 guideline rules) → expert syndrome layer → fusion → ranking hygiene (causal attribution, chronicity, UDMI) → two-tier cited differential.

**Fig. 2 | Pre-specification workflow and the reference-standard ceiling.** (a) SAP, freezes and the two one-shot quarantine rounds, including the failed round. (b) Decomposition of 2,707 eICU label targets and recall on the 1,460 panel-supported labels for the product release, v7 and the registry-off ablation.

**Fig. 3 | Untrained engine versus supervised models on identical inputs (eICU).** Per-group AUROC of Hemoglyph, five-fold out-of-fold gradient boosting and logistic regression.

**Fig. 4 | NHANES screening across three independent cycles.** AUROC per task for the development cycle (2017–18, frozen-v7 re-run) and quarantine cycles (2013–14, 2015–16), n = 3,000 each; y-axis truncated at 0.5 (chance level) to resolve differences of 0.01–0.05.

**Fig. 5 | Sepsis: a pre-specified negative result.** Engine versus supervised logistic AUROC in prediction and concurrent frames across sets A, B and B2.

**Fig. 6 | Blinded LLM comparison (400 stays, 596 labels), frozen engine v7.** Per-group recall@5 and recall@k curves for Hemoglyph and the unnamed frontier LLM model.

**Fig. 7 | Calibration and decision curves (eICU, engine v7).** Reliability diagrams before and after cross-fitted isotonic recalibration and decision curves for the five largest groups.

## Tables

**Table 1 | Data sources, reference standards and roles.**

| Dataset | Setting | Reference standard | Role | n evaluated |
|---|---|---|---|---|
| eICU-CRD demo v2.0.1 | 186 US ICUs | clinician problem list → 31 groups | development and per-release gate | 2,314 stays; 2,432 labels |
| MIMIC-IV demo | US tertiary hospital | ICD-10 codes | quarantine 1 | 235 admissions; 507 pairs |
| NHANES 2017–18 (J) | US community survey | guideline criteria; self-report | development | 3,000 adults |
| NHANES 2013–14 (H) | idem | idem | quarantine 1 | 3,000 |
| NHANES 2015–16 (I) | idem | idem | quarantine 2 | 3,000 (healthy subset 79) |
| PhysioNet/CinC 2019 A / B / B2 | US ICU hourly records | Sepsis-3 onset | pre-specified single target; B, B2 quarantine | 4,871 / 4,558 / 4,991 patients |
| UCI thyroid0387 | referral laboratory | expert comment | external | 7,743 records with TSH; 6,932 scored (655 / 195 / 6,082) + 811 other classes |
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

CIs for the v7 row are stay-clustered (top-3 45.8–50.0; top-5 58.7–62.9; top-10 72.2–76.0). The historical registry-off ablation on engine v5.3 (first submission) is moved to Supplementary Table S12b; the ablations that belong to the evaluated release are those of Table 5. All scores in this table are rank-based and uncalibrated; after cross-fitted isotonic recalibration within eICU the pooled ECE fell from 0.162 to 0.003 and the Brier score from 0.117 to 0.040 without changing any rank, so recall values are unaffected. The shipped product displays ranks and evidence states, not probabilities, and applies no calibration map.

**Table 3 | External and quarantine datasets, engine v7.**

| Dataset / task | Metric | Value (95% CI) |
|---|---|---|
| NHANES J / H / I: diabetes | AUROC | 0.946 / 0.938 / 0.924 |
| NHANES J / H / I: CKD | AUROC | 0.959 / 0.968 / 0.962 |
| NHANES J / H / I: anaemia | AUROC | 0.972 / 0.994 / 0.983 |
| NHANES J / H / I: iron deficiency | AUROC | 0.989 / – / 0.972 |
| NHANES J / H / I: hyperuricaemia | AUROC | 0.943 / 0.958 / 0.955 |
| NHANES J / H / I: hypercholesterolaemia | AUROC | 0.905 / 0.883 / 0.886 |
| NHANES J / H / I: ALT elevation (ACG sex-specific) | AUROC | 0.872 / 0.880 / 0.877 |
| NHANES J / H / I: self-reported diabetes | AUROC | 0.919 / 0.914 / 0.898 |
| NHANES J / H / I: self-reported kidney disease | AUROC | 0.816 / 0.748 / 0.799 |
| NHANES H/I/J healthy adults | false assertions | 1/246, 0/79, 1/160 (2/485) |
| UCI thyroid0387 (9,172 records → 7,743 with TSH and non-excluded class; 811 in other classes not scored, Supplementary Table S13): hypothyroidism 655 vs 6,082 / hyperthyroidism 195 vs 6,082 | AUROC | 0.979 (0.974–0.983) / 0.798 (0.783–0.814) |
| UCI HCV (615 = 533 donors, 7 suspect donors excluded from both tasks, 75 with liver disease): any liver disease 75 vs 533 / cirrhosis 30 vs 578 | AUROC | 0.925 (0.881–0.962) / 0.909 (0.837–0.969) |
| ILPD: liver patient (416 vs 167) | AUROC | 0.704 (0.661–0.747) |
| MIMIC-IV demo (v6, one-shot quarantine 1 / v7 post-hoc re-run) | recall @5 / @10 | 47.9 / 61.7% / 47.5 / 62.1% |
| PMC case reports, manual labs: specific / syndrome | top-5 | 26% / 68% |
| Sepsis set B2 prediction / concurrent (labs + vitals) | AUROC | 0.588 (0.559–0.616) / 0.635 (0.597–0.673); logistic 0.679 / 0.726 |

**Table 4 | Blinded comparison with an unnamed frontier LLM (agent platform, model not disclosed), 400 eICU stays, 596 labels.** The historical v5.1 comparison from the first submission is in Supplementary Figure S (superseded).

| Metric | Hemoglyph v7 (flat) | LLM | Difference (95% CI) | Cluster-adjusted p |
|---|---|---|---|---|
| recall@1 | 24.0% (20.6–27.7) | 28.2% (24.6–32.0) | −4.2 pp (−7.5 to −0.9) | 0.013 |
| recall@3 | 47.0% (42.6–51.5) | 50.8% (46.5–55.1) | −3.9 pp (−7.4 to −0.3) | 0.041 |
| **recall@5 (primary)** | **60.7% (56.5–65.0)** | **59.6% (55.3–63.6)** | **+1.2 pp (−2.5 to +5.1)** | **0.54** |
| recall@10 | 72.0% (67.9–75.8) | 65.1% (60.8–69.3) | +6.9 pp (+3.3 to +10.5) | 0.0002 |
| MRR | 0.391 | 0.408 | −0.017 (−0.043 to +0.008) | — |
| label absent from list | 21.8% | 34.9% | | |
| two-tier recall@5 (secondary, post hoc) | 69.8% (65.7–73.7) | 59.6% | +10.2 pp (+6.7 to +13.9) | < 0.0001 |
| test–retest / alternative prompt (40 panels) | deterministic | 85.7% agreement, κ 0.69 / 83.5–89.0% | | |
| critical values flagged (50 stays; shared safety floor, non-discriminating) | 39/39 (91–100%) | 39/39 (91–100%) | | |

**Table 5 | Component ablation of the frozen engine v7 (2,314 eICU stays; the 28 `unverified_source` rules are a subset of the 33,183 executable rules).**

| Arm | flat @3 | flat @5 | flat @10 | Δ flat @5 (95% CI) | two-tier @5 | Δ two-tier @5 (95% CI) | mean AUROC (24 groups) |
|---|---:|---:|---:|---|---:|---|---:|
| **full v7 (reference)** | **47.9** | **60.8** | **74.1** | — | **71.9** | — | **0.767** |
| rule-engine vote off (registry + syndrome votes) | 34.7 | 48.7 | 67.0 | −12.1 (−14.4 to −9.8) | 57.6 | −14.3 (−16.3 to −12.4) | 0.664 |
| expert syndrome layer off (registry intact) | 39.5 | 51.3 | 68.3 | −9.5 (−11.1 to −7.9) | 66.0 | −6.0 (−7.3 to −4.6) | 0.751 |
| registry restricted to 272 curated anchor rules (32,911 AI-drafted rules off) | 46.8 | 59.9 | 72.5 | −0.9 (−2.1 to +0.2) | 68.9 | −3.0 (−4.0 to −2.1) | 0.732 |
| anchor rules only **and** expert syndrome layer off (2 × 2 cell) | 38.0 | 48.2 | 68.1 | −12.6 (−14.5 to −10.6) | 60.9 | −11.1 (−12.7 to −9.4) | 0.708 |
| Bayesian-network layer off | 47.5 | 59.5 | 69.9 | −1.3 (−2.0 to −0.6) | 68.2 | −3.7 (−4.8 to −2.7) | 0.757 |
| uniform fusion weights (0.20 × 5) | 47.5 | 59.4 | 73.1 | −1.4 (−2.1 to −0.7) | 72.2 | +0.3 (−0.2 to +0.8) | 0.767 |
| rule-heavy fusion weights (0.55 / 0.15 / 0.15 / 0.075 / 0.075) | 48.2 | 60.8 | 74.0 | −0.0 (−0.6 to +0.5) | 71.8 | −0.2 (−0.7 to +0.4) | 0.762 |
| rule-light fusion weights (0.20 / 0.30 / 0.25 / 0.125 / 0.125) | 47.6 | 59.7 | 73.3 | −1.1 (−1.8 to −0.3) | 72.2 | +0.3 (−0.2 to +0.8) | 0.767 |
| discord shrinkage and single-source discount off | 47.7 | 60.4 | 73.5 | −0.4 (−1.0 to +0.2) | 71.7 | −0.2 (−0.7 to +0.3) | 0.766 |
| Dempster instead of Yager combination | 47.6 | 60.7 | 74.0 | −0.1 (−0.3 to +0.1) | 71.9 | −0.0 (−0.2 to +0.1) | 0.765 |
| fuzzy layer off | 47.9 | 61.1 | 73.8 | +0.3 (−0.1 to +0.8) | 71.8 | −0.1 (−0.4 to +0.2) | 0.764 |
| knowledge-graph layer off | 48.3 | 60.9 | 74.3 | +0.1 (−0.3 to +0.6) | 72.2 | +0.3 (−0.1 to +0.8) | 0.765 |
| risk-model layer off | 47.9 | 60.8 | 74.1 | +0.0 (+0.0 to +0.0) | 71.9 | +0.0 (+0.0 to +0.0) | 0.765 |
| 28 `unverified_source` rules off | 47.9 | 60.8 | 74.1 | +0.0 (+0.0 to +0.0) | 71.9 | +0.0 (+0.0 to +0.0) | 0.765 |

Arm definitions (full definitions and environment switches in Supplementary Note 3 / `eval/ablation/run_ablation.py`): *rule-engine vote off* removes the rule_engine channel from fusion, through which both registry rules and expert-syndrome constellations vote, so it is a superset of *syndrome layer off*, which silences only the ~900 constellations while registry rules remain; *anchor-only* keeps the 272 curated rules and the syndrome layer. The mean AUROC column covers the 24 laboratory-detectable groups with ≥ 5 listed stays and a group score; the multiplicity analysis covers all 29 groups with ≥ 10 coded labels, including five without a single-analyte criterion.

## Supplementary information

Notes: Note 1 SAP and amendments; Table S1 engine changes C1–C16; Table S2 quarantine criteria and outcomes; Table S3 participant flow; Fig. S1 provenance audit; Fig. S2 per-release eICU metrics; Fig. S3 per-group panel-supported recall; Fig. S4 per-group calibration; Fig. S5 context-echo analysis; Table S4 subgroup analysis; Table S5 next-test utility; Table S6 missing-panel threshold sensitivity; Table S7 survey-weighted NHANES AUROC; Table S8 per-group calibration; Table S9 label-mapping audit (400 stays); Note 2 LLM comparison protocol; Note 3 formal fusion/Theory-of-Evidence algorithm, weight profiles and the 27 consistency identities; Fig. S2 historical LLM comparison vs engine v5.1; Table S10 registry count reconciliation; Table S11 precision/F1/NDCG, alert burden, per-group PPV and prevalence baseline; Table S12 fusion-weight sensitivity; Table S13 participant flow for the UCI thyroid and HCV cohorts; Note 4 regression-gate definition and residual failures; Note 5 healthy-adult definition, critical-value thresholds, race-term audit, hardware, novelty-search method, LLM model-identity statement and completed TRIPOD+AI checklist; Table S4 subgroup recall (v7); Note 7 evidence triage of the twelve post-review proposals (twelve rows: proposal, evidence, verdict, action); Table S16 sepsis companion risk model; Data 1 per-stay outputs and LLM prompts/outputs.
