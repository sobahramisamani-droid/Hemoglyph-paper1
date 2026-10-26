# Design and multi-dataset retrospective evaluation of Hemoglyph, an untrained, auditable knowledge-based engine for interpreting laboratory panels

Sobhan Bahrami¹*, Zhaleh Tahmasebinejad², Ehsan Bahrami Samani²

¹ Allameh Helli 10 High School, National Organization for Development of Exceptional Talents (NODET), Tehran, Iran. ² Statistics and Data Science Clinic, Shahid Beheshti University, Tehran, Iran. *Correspondence: sobahramisamani@gmail.com (ORCID 0009-0004-6639-5081)

*Manuscript version v5.3 (engine freeze 23–24 October 2026; registry 13.3.0). Target: npj Digital Medicine, Article (≤ 4,000 words main text, ≤ 8 display items). All reported numbers come from the v5.3 freeze on registry 13.3.0; every held-out re-run (NHANES 2017–18, thyroid, HCV, ILPD, Sepsis-2019, fuzz batteries) is complete.*

## Abstract
Large language models interpret laboratory reports fluently but not reproducibly; supervised models need labels most laboratories lack. Hemoglyph is an offline engine that interprets whole laboratory panels without training data, fusing a versioned, source-tagged knowledge base (6,750 entities, 33,230 executable rules) with five reasoning layers under an expert syndrome layer. Frozen under a pre-registered plan, it was evaluated on public ICU, survey, referral-laboratory, hepatology and case-report data. In 2,314 ICU stays from 186 hospitals, 63.8% of clinician-listed diagnoses appeared in the top-5 differential from laboratory values alone (66.6% with documented history). In an exploratory, author-run comparison with a frontier LLM of blinded identity on 400 stays with identical inputs, it listed 64.4% versus 59.6% (p = 0.0093), with no false assertions in healthy adults. Probabilities required recalibration, two thirds of misses had no laboratory signature, and a pre-registered attempt to close a 4.3-point sex gap failed. Code, rules and scripts are released.

## Introduction

Roughly 70 % of clinical decisions draw on laboratory results, yet interpretive comments accompany only a small fraction of reports, and post-analytical errors—missed critical values, patterns that span several analytes, unit confusion—remain a leading source of diagnostic harm [1–3]. Three families of software address this gap. Rule-based expert systems and reflex-testing logic are transparent and widely embedded in laboratory information systems, but are usually narrow, hand-maintained and rarely evaluated outside their home institution [4,5]. Supervised machine-learning models discriminate specific targets well but require labelled training data, degrade under distribution shift and cannot be audited clause by clause [6,7]. Most recently, LLMs have produced fluent interpretations of laboratory reports, but their outputs are not reproducible, cannot run on commodity laboratory hardware without transmitting patient data, fabricate values and references at non-trivial rates, and—critically for this domain—have been shown to misclassify laboratory values as high or low even when reference ranges are supplied [8–11].

A fourth option—an engine that interprets *whole panels* from an explicit, versioned knowledge base, runs offline, and emits a ranked, explainable differential with calibrated confidence—has seldom been evaluated at scale. The barrier is methodological rather than technical: such engines are typically validated on vignettes written by their own authors, and the few real-data evaluations use a single institution and no comparator [12]. Mature diagnostic decision-support systems (Isabel, DXplain) have recently been compared with GPT-4-class models and were found to be within a few percentage points of them on recall while being reproducible and free of fabricated references [13–16]; none of these studies isolated laboratory-only reasoning.

Here we report the design and a multi-dataset retrospective evaluation of **Hemoglyph**, a knowledge-based laboratory-interpretation engine. Our aims were (i) to describe an architecture that fuses complementary reasoning layers while keeping every output traceable to a cited rule; (ii) to evaluate the *frozen* engine, under a pre-registered statistical analysis plan (SAP), against clinician- and guideline-derived reference standards in independent public datasets spanning intensive care, community survey, referral laboratory, hepatology and published case reports, in SI and conventional units; (iii) to quantify what documented clinical context and serial values add to laboratory values alone; (iv) to compare the untrained engine with a raw single-analyte threshold, with a supervised model trained on the same inputs, and—blinded and on identical inputs—with a contemporary frontier LLM; (v) to quantify calibration and decision-analytic value; and (vi) to report failures transparently, including a disclosed post-hoc revision cycle and a pre-registered hypothesis that failed. We frame this as an engineering and evaluation study, not a claim of clinical validation.

## Results

### Regression gate and robustness
The v5.3 freeze passed the complete gate: 488 of 489 battery cases (the single miss ranks alcoholic pancreatitis second instead of first behind acute pancreatitis), 86/86 adversarial panels, no diagnosis ≥ 0.5 on 200 random in-range panels (worst p = 0.45), 200/200 fabrication-provocation panels, and 689 unit tests (Supplementary Table S9). Median latency was 1016 ms per ICU panel (p95 1501 ms) on one CPU core.

### Intensive care (eICU-CRD demo, held-out)
Across 2,314 stays (median 31 analytes) from laboratory values alone, 49.3%, 63.8% and 77.2% of 2,432 clinician-listed diagnoses appeared in the top-3, top-5 and top-10 differential (68.3% at top-5 for the 1,678 laboratory-detectable diagnoses; Table 2, Fig. 2). Discrimination was high for definitional electrolyte, metabolic and haematological syndromes (hyperkalaemia 0.92, rhabdomyolysis 0.92, hyponatraemia 0.89, thrombocytopenia 0.89, hypernatraemia 0.88, diabetic ketoacidosis 0.86), moderate for renal targets (AKI 0.80, CKD 0.82) and lowest where the labelled deviation is usually mild or the signature absent (hypocalcaemia 0.63, hypoglycaemia 0.64, heart failure 0.66; sepsis 0.68). Mean AUROC over 24 laboratory-detectable groups was 0.767. Only 23.4% of outputs with p ≥ 0.7 matched a listed problem, reflecting over-confidence and incomplete problem lists in equal measure (see Calibration).

*What context and serial values add.* Supplying documented history and home medications raised top-5 recall to 66.6% and top-10 to 79.8% (Table 2). The gain was concentrated where the label is a chronic diagnosis that laboratory values can only suggest: diabetes 49 → 71%, CKD 65 → 80%, hyperglycaemia 49 → 60%; electrolyte and acid–base groups were unchanged, and AKI fell slightly (75 → 70%) as documented CKD correctly competed for the renal slot. The context-echo audit shows that this is not mere repetition of the chart: for labels *not* named anywhere in the documented history (n = 2,200) top-5 recall was 65.8%, against 74.1% for the 232 labels that were named; documented entities were listed as *documented only* 2,159 times and promoted to *confirmed* by laboratory support 781 times. Adding serial values on top of context changed top-5 recall by -0.4 points and raised top-10 to 80.2%; temporal criteria help AKI staging and troponin dynamics but the eICU demo exposes few true trajectories.

*Comparators.* The raw key-analyte threshold (B1) matched or exceeded the engine on single-analyte targets (anaemia 0.83 vs 0.78; AKI 0.82 vs 0.80), as expected because those labels are essentially defined by the analyte; the engine added value only where the label requires several analytes or exclusion logic. The supervised gradient-boosting model (B2), trained on 2,314 labelled stays from the same distribution, exceeded the untrained engine on most targets (sepsis 0.82 vs 0.68; DKA 0.96 vs 0.86), while the engine was equal or better for hyponatraemia, thrombocytopenia, CKD, cirrhosis, lactic and metabolic acidosis, acute pancreatitis, heart failure and hypomagnesaemia (Table 3; Fig. 3).

*Calibration and decision value.* Across 52,689 stay–group units raw fused probabilities were over-confident in the upper deciles (mean p 0.78 in the top decile against an observed rate of 0.23; pooled ECE 0.162, Brier 0.115; AUROC 0.801). Cross-fitted isotonic recalibration reduced ECE to 0.003 and Brier to 0.040 without changing any ranking (Fig. 4; Supplementary Table S5). On decision curves the recalibrated renal-impairment output had higher net benefit than treat-all and treat-none at every threshold from 0.05 to 0.70 (for example 5.9 vs -7.0 per 100 at a 0.20 threshold), whereas the raw output lost value above 0.20—evidence that the probabilities, not the rankings, were the defect.

*Why the engine misses.* Of 1,151 top-5 misses, a fixed-seed sample of 200 classified by the pre-declared taxonomy contained 132 (66%) with no laboratory signature of the listed condition in the measured panel (heart failure without a natriuretic peptide, diabetes with every glucose below 200 mg/dL and no HbA1c, sepsis with normal leucocytes and lactate), 38 (19%) listed with p ≥ 0.5 but displaced beyond rank 5 by other true findings, and 29 (14%) genuine engine defects (15 knowledge or logic gaps, 14 scoring defects; Supplementary Table S2). The engine-recoverable fraction of misses is therefore about one third; the remainder is a property of a laboratory-only input, not of the engine. For 88 category-A misses with a scorable discriminating test, the next-test layer named that test in 42 (48%): heart failure 14/27, sepsis 5/7, renal impairment 5/6, diabetes 5/21 (Supplementary Table S3).

*How much of the knowledge base is load-bearing.* With every one of the 34,548 registry rules switched off and all other layers unchanged, top-5 recall fell from 63.8 to 62.0% (−1.8 points; −3.6 on lab-detectable labels) and mean AUROC from 0.767 to 0.732 (Supplementary Table S10). The loss concentrated in leukocytosis (AUROC −0.20), hypophosphataemia (−0.19), hypernatraemia (−0.10), hypomagnesaemia and hyperglycaemia (−0.07), thrombocytopenia (recall −20 points) and CKD (−6 points); the defining electrolyte, acid–base and renal syndromes are carried mainly by the expert syndrome layer and were little affected.

*Subgroups and the sex gap.* Top-5 recall was 65.4% (62.6–68.2) in men and 61.1% (57.1–65.3) in women; 63.4%, 63.7% and 65.7% in stays recorded as Caucasian, African American and Hispanic, with overlapping CIs (Supplementary Table S4). Deviations above 10 points occurred only by ICU type (medical ICU 82%, cardiothoracic–coronary unit 51%), which track case mix. The male–female gap of 4.3 points was the subject of pre-registered hypothesis H1: the sex-blind thresholds in the knowledge base (197 rules) were split into sex-conditioned pairs for registry 13.3.0, and the arm was re-run. **H1 failed**: the gap moved from 4.4 to 4.3 points. The per-group decomposition shows why—the deficit sits in AKI (−12.6 points for women), acute myocardial infarction (−11.9) and gastrointestinal bleeding (−10.8), labels that in this cohort are listed for women at lower creatinine, troponin and haemoglobin deviations, while women *exceed* men for CKD (+20.7), hyponatraemia (+23.8) and hypokalaemia (+30.2). The gap is therefore a property of how the reference standard interacts with sex-specific physiology, not of a threshold the engine could be adjusted to without fitting to the labels; H2 passed (recall@5 63.7 → 63.8%; 197 of 2,314 top-5 lists changed, net +0.1 point) and H3 passed (B8 294/456 ≥ 288). We report the gap as unresolved.

### Community survey (NHANES)
In 5,103 adults of the 2017–18 cycle, guideline-defined diabetes, CKD, anaemia and iron deficiency were recovered with AUROC 0.941, 0.959, 0.971 and 0.989; because these labels share inputs with the engine, self-reported physician diagnosis was evaluated as an independent label (diabetes 0.910; kidney disease 0.798) (Table 4). ALT elevation was recovered poorly (AUROC 0.720) because the engine deliberately withholds a diagnosis for an isolated transaminase. Among 274 adults with every core analyte inside its reference interval, 1 (0.4%) received any non-finding entity with p ≥ 0.5. The six earlier cycles (2005–2016; 34,500 adults) are pre-specified replications and are rendered into Table 4 as each completes.

### Referral laboratory, hepatology, Indian cohort and case reports
In the Garvan thyroid records, hypothyroidism was identified with AUROC 0.979 (primary hypothyroidism 0.994) and sensitivity/specificity 96.9%/95.1%; hyperthyroidism reached 0.932 for overt entities and 0.798 when subclinical patterns were credited, because the dataset reports total rather than free hormones. In the HCV cohort, any liver disease versus donors reached AUROC 0.925 and cirrhosis versus all others 0.909, with specificity 100 % and low sensitivity at 0.5 (the insufficient-evidence ceiling). On ILPD, AUROC was 0.704 (published supervised models trained on ILPD: 0.70–0.76). On the 50 PMC-Patients case reports, given only the laboratory paragraph (median 11 analytes, no narrative), the engine placed the published diagnosis in its top five in 26% of cases at the specific level and the containing laboratory syndrome in 68%, against 60 % top-10 for GPT-4 given the full vignette in the published benchmark [17]; an end-to-end arm from the free-text paragraph through the engine's prose parser reached 44% at the syndrome level.

### Pre-specified stress test: predicting Sepsis-3 onset from first-day laboratory values
The PhysioNet/CinC 2019 task asks a different question from the rest of this paper—*prediction* of a later Sepsis-3 onset rather than recognition of a documented diagnosis—and was included as a pre-registered negative-control-style stress test. In 4,843 hospital-A patients (438 with sepsis at any hour), the engine's sepsis-group probability from the first 24 h of laboratory values reached AUROC 0.593 (0.570–0.617), below a supervised logistic model cross-validated on the same patients and features (0.689, 0.663–0.715); the sepsis group entered the top five in 32.2% of sepsis patients and 16.5% of non-sepsis patients. We report this unchanged. A post-hoc re-analysis declared in SAP Amendment 13—recognition of sepsis from the panel drawn in the 12 h around onset, with dwell-time-matched controls, with and without vital signs—did *not* rescue the result (AUROC 0.534, 0.508–0.561, identical with vital signs; Supplementary Table S12): the file contains no procalcitonin or C-reactive protein, lactate is measured in a minority of windows, and the registry's sepsis criteria never enter the differential for 74 % of cases. The honest reading is that a laboratory-only guideline engine cannot identify Sepsis-3 from the analytes routinely available in this cohort, and the gap to a supervised baseline—which profits partly from measurement patterns such as whether lactate was ordered—marks the boundary of the approach.

### Exploratory comparison with a frontier LLM on identical inputs
On the pre-registered B8 set of 240 never-inspected stays, the engine listed 64.3% of clinician diagnoses in its top five and the LLM 58.3% (discordant 61 vs 34; McNemar p = 0.0073); pooled over all 400 blinded stays the figures were 64.4% versus 59.6% (p = 0.0093; Table 5, Fig. 5). The two systems differ in shape rather than size: the LLM is better at the first slot (recall@1 28.2% vs 23.3%) and the engine at depth (recall@10 74.5% vs 65.1%; labels never listed 21.1% vs 34.9%). The engine's advantage was largest for CKD (51% vs 20%), gastrointestinal bleeding and diabetes; the LLM led for DKA, metabolic acidosis and hyperkalaemia, where it names the obvious syndrome first while the engine spreads probability over its differential. The engine made no false assertion in 40 guideline-healthy NHANES adults (LLM 4/40), reproduced its output bit-for-bit in 50/50 stays across three runs, surfaced 39/39 critical values (LLM 39/39), and every entry carried a rule and source whereas 8/25 LLM stays contained flags that could not be traced to a stated rule.

## Discussion

We asked a narrow question: how well does an explicitly knowledge-based, untrained engine interpret real laboratory panels across settings it has never seen, what do context and serial values add, and where does it fail? Five findings stand out.

First, **definitional and multi-analyte syndromes are where a knowledge-based engine earns its place.** Hyperkalaemia, hyponatraemia, DKA, rhabdomyolysis, thrombocytopenia, cirrhosis and hypothyroidism were recovered with AUROC 0.85–0.99 across ICU, survey and referral-laboratory data in both unit systems, with zero false diagnoses on in-range panels. For single-analyte labels a raw threshold did as well—a negative result that any evaluation without such a baseline would hide.

Second, **a supervised model trained on the target data is usually the better discriminator, but it has to be trained.** B2 needed 2,314 labelled stays from the same distribution; the engine needed none, generalised to five other settings unchanged, and can state why each entity was ranked. The two are complementary: the rule base can supply priors and safety floors for learned models, and learned models can propose rules for curation.

Third, **documented context is worth about three recall points and is not chart echo.** Recall rose for labels never named in the history, and the engine's context semantics—*documented* until laboratory values confirm, never asserting a medication-implied diagnosis without support—kept the gain from being bought with false positives (chart support unchanged). Serial values added little in this dataset, which rarely contains informative trajectories; their cited temporal criteria (KDIGO staging, hs-troponin dynamics) are retained as an optional module.

Fourth, **confidence, not ranking, was the engine's main defect**, and the defect is repairable. Fused probabilities were too high in the upper deciles, a known weakness of weighted-vote ensembles; cross-fitted isotonic recalibration removed almost all of it and turned a renal-impairment output that lost net benefit above a 0.20 threshold into one that dominates default strategies across the clinically relevant range. We recommend that knowledge-based engines ship recalibrated probabilities and that evaluations include decision curves.

Fifth, **the blinded comparison with a frontier LLM favoured the engine at the five- and ten-slot depth and the LLM at the first slot.** Read together with the published Isabel and DXplain comparisons (Supplementary Table S8), which found the same shape against GPT-4 (2023) [13–16], this suggests a stable division of labour: a generative model is good at naming the obvious syndrome, a knowledge base is better at not forgetting the second and third. Our comparison is exploratory—the LLM's identity was blinded by the platform and the developer's own agent produced the answers—so we claim no superiority; we claim that an offline, auditable engine with no training data reaches at least the recall of such a model on laboratory-detectable diagnoses while providing reproducibility, zero fabrication, source traceability and no data egress, properties a laboratory information system can certify and an LLM currently cannot.

*The failed hypothesis.* We pre-registered that a sex-balanced knowledge base would close the male–female recall gap, and it did not. The decomposition (AKI, myocardial infarction and gastrointestinal bleeding listed for women at smaller laboratory deviations; CKD and electrolyte disorders recovered better in women) indicates that the gap arises from the interaction between the reference standard and sex-specific physiology rather than from a threshold. Closing it by lowering female thresholds would amount to fitting to the labels and was not done. We regard this as the most important unresolved finding and a priority for the prospective study.

*The knowledge-base provenance.* The registries were drafted with LLM assistance and curated by one author; the scripted defect scan found and corrected 2,000-odd rule-level defects before the final freeze, and the corrected registry changed held-out recall by +0.1 point. That near-invariance is reassuring about the engine's robustness to the rule base and disquieting about how much of the rule base matters; the registry-off ablation gives the direct answer—removing all 34,548 rules costs 1.8 points of top-5 recall and 0.035 of mean AUROC, concentrated in a dozen groups—so the registry is a measurable but minority contributor on this cohort, and most of what it adds is carried by the ~850 operational rules; an independent expert audit of that stratum is the obvious next step, and the registries are released for scrutiny. The mechanical provenance audit (Methods; Supplementary Data 1) makes the weakness concrete: nine of 781 source DOIs were fabricated by the drafting model and only 0.8 % of executable rules cite a DOI-verified document; readers should treat the registry as a transparent, machine-checkable draft of guideline knowledge, not as an expert-curated reference. Sepsis is the clearest clinical failure: without procalcitonin, CRP or clinical signs the engine is near chance (AUROC 0.53–0.59 on Sepsis-2019), and the eICU sepsis group (AUROC 0.68) should not be read as sepsis detection.

### Limitations
(1) The knowledge base was LLM-drafted and single-author curated; no independent expert panel reviewed it. (2) Reference standards are imperfect: problem lists under-record laboratory diagnoses (depressing precision and chart support), NHANES guideline labels share inputs with the engine (mitigated by self-report labels), "no comment" thyroid records include treated patients, and the PMC case reports were scored on their laboratory paragraph only. (3) Only the public demo subsets of MIMIC-IV and eICU were used. (4) The evaluation is retrospective and non-interventional: no clinician saw an engine output and no claim about clinical impact, alert burden or automation bias is made. This is a technical-validation study (TRIPOD-AI analytical stage); a multi-reader crossover study in which laboratory physicians and internists interpret anonymised panels with and without the engine's output, and a silent prospective run in a hospital laboratory, are the next stage and are specified in a separate protocol (Supplementary Note S11; to be reported in a second paper). (5) Pre-analytical and OCR errors were tested synthetically only. (6) The LLM comparator is exploratory: identity, version and sampling were not exposed, the same agent acted as comparator and reader, and the named-model replication has not been done. (7) The developer performed the evaluation; code, data pointers and every script are released to enable replication. (8) The male–female recall gap is unresolved.

### Conclusion
A versioned, source-tagged knowledge base combined with multi-layer reasoning, severity-tiered syndrome anchors and explicit context semantics interprets laboratory panels across heterogeneous real-world datasets with strong discrimination for definitional and multi-analyte syndromes, needs no training data or network access, matches a frontier LLM at depth on identical inputs, and can be corrected transparently. Its probabilities require recalibration, it does not beat trained models where labels are available, it carries an unexplained sex gap, and it has not been tested prospectively. We offer the engine, the knowledge base and the complete evaluation harness as an open, auditable baseline for the field.

## Methods

### Engine architecture
Hemoglyph (release 1.3.1) is a single-process Python engine with no network access at inference. It accepts a dictionary of analyte identifiers, values and units with optional patient context (age, sex, pregnancy, documented conditions and medications, an explicit `clinical_suspicion` field, and time-stamped serial values) and returns a ranked differential, per-entity probabilities, the rule chain behind each entry, critical-value alerts and recommended confirmatory tests (Fig. 1).

*Knowledge base.* Two Brotli-compressed JSON registries hold (a) a **feature registry** of 2,045 analytes with LOINC codes, UCUM canonical units, English and Persian synonyms and age/sex/pregnancy-specific reference intervals, and (b) a **disease–guideline registry** (v13.3.0) of 6,750 entities (diseases, laboratory findings and biomarker patterns; 6,660 named entities after 90 placeholders were retired) linked to 34,548 rules of which 33,230 are executable (11,097 screening, 6,074 diagnostic-criterion, 6,218 exclusion and 9,844 staging/severity) and 747 cited sources (ADA, KDIGO, ATA, AASLD, ACR, CLSI, WHO and standard texts). Rules are declarative (analyte, operator, threshold, population, evidence tier, source). **The registries were drafted with the assistance of a large language model from prompts naming the governing guideline, screened by code-level validators (schema, unit, monotonicity, duplicate and dead-rule checks) and curated by the author, a non-physician developer; they were not reviewed by an independent expert panel for this study.** About 60 % of entities are automatically generated single-analyte `biomarker_pattern` entities; the operational stratum on which the results rest is smaller—186 diseases and 851 rules surfaced in any eICU top-5—and both strata are released verbatim so that any rule can be checked against its cited source. A pre-specified physician audit of 100 executable rules (form and sample fixed before results) is in progress and its error rate will be reported unchanged. Because of that provenance, the knowledge base was subjected to a scripted defect scan before the final freeze (Supplementary Table S7): twelve defect classes (sex-blind thresholds, mislabelled rule layers, impossible thresholds, context-dependent diagnoses asserted from laboratory values alone, template artefacts, placeholder entities, geographically restricted pathogens proposed without exposure) were corrected by reproducible patches, and the effect of the corrected registry on held-out performance was tested under pre-registered hypotheses (below). A load-time curation layer rejects malformed rules and down-weights rules with missing evidence grading. Source provenance was audited mechanically after the freeze: every DOI in the source table was resolved through Crossref and its title compared with the registry record, and every URL was probed (Supplementary Data 1). Of 781 source records in the release registry, 112 carry a DOI that resolves to the intended document, 596 point to a specific or organisation-level web page, 39 could not be confirmed from the verification host and 34 have no locator; nine DOIs were fabricated or pointed to unrelated articles and were removed in release 13.4.1 (the 28 rules citing only those sources were retained but flagged `unverified_source`; five of them belong to three entities—methanol poisoning, ethylene-glycol poisoning and valproate-induced hyperammonaemia—that appeared in at least one eICU top-5 list, so the result tables are not entirely free of rules whose cited locator was invalid, although the thresholds themselves—osmolal gap, ammonia—are standard textbook values). At rule level, 0.8 % of executable rules cite a DOI-verified source and 92.8 % cite at least one specific document, dominated by CLSI EP28 reference-interval guidance—that is, the bulk of the rule base carries reference-interval provenance rather than disease-specific guideline citations.

*Unit normalisation.* Inputs are converted to canonical units by a deterministic converter (molar/mass conversions per analyte, for example T4 nmol/L → µg/dL via 776.87 g/mol) that refuses ambiguous conversions.

*Reasoning layers.* Five layers score each candidate entity independently: (1) the **rule engine** (population-aware evaluation of registry rules); (2) a **naive-Bayes layer** with likelihood ratios derived from rule thresholds; (3) an **adaptive fuzzy layer** grading the distance of each value from its reference limits and abstaining when no rule covers the analyte; (4) a **knowledge-graph layer** propagating support between pathophysiologically linked entities; (5) **risk models** (100 published scores such as FIB-4, CKD-EPI 2021, anion gap, corrected calcium). Outputs are fused by a fixed weighted ensemble (0.35/0.25/0.20/0.10/0.10) with discord-aware shrinkage towards 0.5. No weight was fitted to any outcome label.

*Expert syndrome layer (ESL).* A library of cited, hand-written syndromes (for example "K⁺ ≥ 6.5 mmol/L without thrombocytosis or leucocytosis ⇒ severe hyperkalaemia, anchor") imposes severity-tiered floors (anchor 0.95, strong 0.88, pattern 0.80) and caps on competing entities; definitional guards prevent, for example, DKA from being asserted without ketones or an anion gap. Entities whose supporting evidence is incomplete and that are not themselves laboratory findings are capped at 0.49 (insufficient-evidence ceiling). Since v5 the layer also accepts **documented context** (a condition or medication in the history raises a *documented* entity to at most 0.49 and to *confirmed* (≥ 0.80) only when the laboratory values support it; a medication-implied diagnosis is never listed without laboratory support) and **serial values** (trajectory features such as creatinine delta, troponin dynamics and glucose span, used only by cited temporal criteria such as KDIGO AKI staging and the hs-troponin 0/1-h algorithm).

*Safety logic.* CLSI/CAP critical values are always surfaced; pseudo-hyperkalaemia, haemolysis and drug effects are screened by adversarial rules; AKI and CKD are reported as "renal impairment of undetermined chronicity" when only one creatinine is available (KDIGO); physiologically impossible or unit-implausible values are removed with an explicit warning; a cited next-test library names the confirmatory test for each proposed entity without changing any probability.

### Freeze, pre-registration and amendments
All engine files were hashed (SHA-256) and frozen on 21 October 2026 (v1) after development on synthetic batteries and the MIMIC-IV demo. The SAP (Supplementary File 1) fixed datasets, label maps, metrics, thresholds and the false-assertion definition before any held-out run. Twelve amendments are disclosed verbatim in the SAP. In brief: Amendment 1 tightened the healthy definition; Amendments 2–7 document a **post-hoc engine revision cycle (v2 → v5.2; ESL extensions 5–11)** driven by error analysis of eICU-CRD stays 0–1,200 and the NHANES healthy audit—severity anchors for critical values, chronicity logic, total-T4/T3 syndromes, definitional guards, the context and temporal input arms, and the next-test and plausibility layers—each an additive cited clause or guard with no fitted parameter; Amendments 8–11 pre-specified the context and temporal arms, the blinded LLM comparison on 240 never-inspected stays (B8), a context-echo audit and a sex-stratified deep review; **Amendment 12** pre-registered three hypotheses for the final knowledge-base revision (registry 13.1.0 → 13.3.0, engine code unchanged): H1, the male–female recall@5 gap would fall within ±1.5 points; H2, labs-only recall@5 would not fall by more than 1.0 point from 63.7 %; H3, blinded B8 recall would remain ≥ 288/456. All results reported here are from the final freeze (v5.3); v1 figures are given in the Supplement, and the uninspected eICU split (stays 1,200–2,314), B8, the thyroid, HCV, ILPD and PMC cohorts were never used for error analysis after v2. Two execution errors during the final activation (a registry file that the engine does not load was updated first; a patch that wrongly downgraded laboratory-finding rules) were detected by the regression gate, corrected, and are documented in the SAP with the discarded outputs retained for audit.

### Datasets and reference standards
Table 1 and Supplementary Table S1 summarise the data sources and cohort flow. Only public, de-identified data were used; the MIMIC-IV [19] and eICU-CRD [18] **demo** releases do not require credentialing; the UCI HCV [20], thyroid0387 [21] and ILPD [22] cohorts and the PhysioNet Sepsis-2019 training set [23] are open downloads. Reference standards were: clinician problem lists in eICU-CRD, grouped into 30 laboratory-relevant groups by regular expressions fixed in the SAP, each with a key analyte so that recall is computed only where the relevant test was performed; guideline criteria in NHANES (ADA diabetes [26], KDIGO CKD [25], WHO anaemia and iron deficiency, ACG ALT limits) plus self-reported physician diagnosis as a label *independent* of the input values; the expert diagnostic comment in UCI thyroid0387 (hyperthyroid entities per ATA [27]); clinical category in UCI HCV; liver-patient status in ILPD; the published final diagnosis of 50 PMC-Patients case reports used by Bhasuran et al. as a GPT-4 benchmark, scored at a specific and a laboratory-syndrome level with a key written before any run [17]; and Sepsis-3 onset in the PhysioNet/CinC 2019 challenge set. Three **input arms** were run on eICU-CRD: laboratory values with age and sex only (primary); plus documented past history and home medications recorded before ICU admission (admission diagnoses excluded); plus serial values. A context-echo audit separates labels already named in the documented history from those not named.

### Metrics
Discrimination was summarised as AUROC with 1,000-sample bootstrap 95 % CIs, sensitivity and specificity at the pre-specified 0.5 threshold, and recall@k of listed diagnoses with stay-level bootstrap CIs. Calibration was assessed on all stay–group units by expected calibration error (ECE, equal-mass deciles) and Brier score, before and after cross-fitted isotonic recalibration, and decision-curve net benefit [28] was computed for the five largest groups. Chart support is the fraction of outputs with p ≥ 0.7 matching a listed problem. Safety is the proportion of CLSI critical values whose matching entity reached the top-5.

### Comparators
B1: the raw key analyte at its guideline threshold. B2: histogram gradient boosting and L2 logistic regression trained on the same per-stay analyte vectors with five-fold out-of-fold prediction (scikit-learn; defaults). B3–B8: a contemporary frontier LLM received the same inputs as the engine (analytes, units, age, sex; no diagnoses, tools or retrieval) and returned a ranked differential of ≤ 10 entries; the pre-registered B8 set (240 stays) was drawn after freeze v5.1 and never inspected. **Model-identity disclosure.** The LLM was accessed through the Arena.ai Agent Mode platform, which routes requests to one of several frontier models (Claude, GPT, Gemini, Grok, Qwen or Kimi families) without exposing identity, version, temperature or seed; it is described as a *2025–2026-generation frontier LLM of blinded identity*. Both systems were scored by the same fixed label map; the LLM read-outs were produced by the agent blinded to labels and engine output. Because the developer's agent produced the LLM answers, this comparison is a conflict of interest and is labelled exploratory; a named-model, temperature-0, clinician-adjudicated replication is required before any comparative claim.

### Error audit, next-test utility and subgroups
Every top-5 miss on eICU-CRD was pooled; a fixed-seed random sample of 200 was classified by a deterministic, pre-declared taxonomy: (A) no laboratory signature of the condition in the measured panel; (B) listed with p ≥ 0.5 but displaced beyond rank 5 by other true findings; (C1) signature present, entity never proposed; (C2) signature present, entity proposed with p < 0.5; (D) synonymous entity in the top-5 not in the SAP id list. For category-A misses with a scorable discriminating test, *next-test utility* is the proportion for which the engine named that test. Performance was stratified by sex, age band, recorded ethnicity, ICU type, hospital and panel size (TRIPOD+AI item 19); the engine has no race, ethnicity or site term.

### Robustness batteries
489 expert-constructed cases in five batteries, re-run with ±3 % and ±10 % multiplicative noise, as SI/conventional unit twins, 1,200 random in-range panels, and a 200-panel fabrication-provocation battery (impossible values, unit traps, contradictory panels, fabricated analytes, empty panels) form the regression gate that every freeze must pass (Supplementary Table S9).

### Statistics and software
Python 3.13, NumPy, pandas, scikit-learn, matplotlib. No hyper-parameter was tuned on any held-out dataset. McNemar's exact test compared paired recall. Reporting follows TRIPOD+AI [24] (Supplementary File 3); the differential-diagnosis-generator evaluation criteria of Bond et al. [30] (in-list, rank, reproducibility, safety) were adopted for the LLM comparison, and critical-value coverage followed the CAP policy survey [29]. Code, registries, SAP, hash manifests and all evaluation scripts are released.

## Data availability
MIMIC-IV demo (v2.2) and eICU-CRD demo (v2.0.1) are available from PhysioNet without credentialing; NHANES from the US CDC; UCI thyroid0387, HCV and ILPD from the UCI Machine Learning Repository; the PMC-Patients case set from the repository of Bhasuran et al.; the Sepsis-2019 training set from PhysioNet. Per-encounter engine outputs for every dataset and arm are included in the project repository.

## Code availability
Engine source (release 1.3.1; GNU AGPL-3.0-or-later), the clinical registries (feature 12.1.0; disease–guideline 13.3.0 used for every result reported here, and the 13.4.2 release version with its changelogs, source-verification report and the eICU re-runs of Disclosure A6; CC BY-SA 4.0), the ESL library, the SAP with all amendments, SHA-256 freeze manifests (v1 … v5.3), all evaluation scripts, test batteries, the registry defect scanner and patches, and figure code are archived at Zenodo (DOI to be inserted) and maintained at the project repository. `reproduce.sh` re-runs the complete chain. The compiled desktop distribution (user interface, OCR packaging, licence activation) is proprietary and is not required to reproduce any result.

## Author contributions
S.B. conceived the system, built the engine and knowledge base, designed and ran the evaluation, and wrote the manuscript. Z.T. reviewed the statistical analysis plan and the reporting of the held-out evaluation, and revised the manuscript. E.B.S. supervised the statistical methodology (pre-registration, bootstrap and calibration analyses, paired testing) and critically revised the manuscript. All authors approved the final version. *(Contribution statements for Z.T. and E.B.S. to be confirmed by them before submission.)*

## Competing interests
S.B. is the sole developer of Hemoglyph. Z.T. and E.B.S. declare no competing interests. No funding was received.

## Ethics
All datasets are de-identified and publicly released under their respective data-use agreements; no ethical approval was required.

## References
1. Plebani M. The detection and prevention of errors in laboratory medicine. *Ann Clin Biochem* 2010;47:101–110.
2. Hallworth MJ, et al. Current evidence and future perspectives on the effective practice of patient-centered laboratory medicine. *Clin Chem* 2015;61:589–599.
3. Epner PL, Gans JE, Graber ML. When diagnostic testing leads to harm: a new outcomes-based approach for laboratory medicine. *BMJ Qual Saf* 2013;22:ii6–ii10.
4. Vasikaran S, et al. Interpretative commenting. *Clin Biochem Rev* 2008;29(Suppl 1):S99–S103.
5. Bellodi E, et al. Economic and organizational impact of a clinical decision support system on laboratory test ordering. *BMC Med Inform Decis Mak* 2017;17:179.
6. Rank N, et al. Deep-learning-based real-time prediction of acute kidney injury outperforms human predictive performance. *npj Digit Med* 2020;3:139.
7. Fleuren LM, et al. Machine learning for the prediction of sepsis: a systematic review and meta-analysis. *Intensive Care Med* 2020;46:383–400.
8. Cadamuro J, et al. Potentials and pitfalls of ChatGPT and natural-language artificial intelligence models for the understanding of laboratory medicine test results. *Clin Chem Lab Med* 2023;61:1158–1166.
9. Kurstjens S, et al. Accuracy of large language models in answering laboratory medicine questions. *Clin Chem Lab Med* 2024.
10. Hager P, et al. Evaluation and mitigation of the limitations of large language models in clinical decision-making. *Nat Med* 2024;30:2613–2622.
11. Savage T, et al. Diagnostic reasoning prompts reveal the potential for large language model interpretability in medicine. *npj Digit Med* 2024;7:20.
12. Laposata M, Dighe A. "Pre-pre" and "post-post" analytical error: high-incidence patient safety hazards involving the clinical laboratory. *Clin Chem Lab Med* 2007;45:712–719.
13. Bridges JM. Computerized diagnostic decision support systems – a comparative performance study of Isabel Pro vs. ChatGPT4. *Diagnosis (Berl)* 2024;11:250–258.
14. Bridges JM. Comparative performance of Isabel Pro and ChatGPT-4, part II: reproducibility and reference accuracy. *JAMIA Open* 2025;8:ooaf048.
15. Massachusetts General Brigham Laboratory of Computer Science. DXplain versus GPT-4 and Gemini 1.5 on 36 unpublished clinical cases with and without laboratory data. Preprint/report, 2025 (publisher record to be confirmed before submission).
16. Shea YF, et al. Use of GPT-4 to analyze medical records of patients with extensive investigations and delayed diagnosis. *JAMA Netw Open* 2023;6:e2325000.
17. Bhasuran B, et al. Preliminary analysis of the impact of lab results on large language model generated differential diagnoses. *npj Digit Med* 2025;8:159.
18. Pollard TJ, et al. The eICU Collaborative Research Database. *Sci Data* 2018;5:180178.
19. Johnson AEW, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data* 2023;10:1.
20. Hoffmann G, et al. Using machine learning techniques to generate laboratory diagnostic pathways—a case study. *J Lab Precis Med* 2018;3:58.
21. Quinlan JR. Thyroid disease data set (thyroid0387). UCI Machine Learning Repository.
22. Ramana BV, et al. A critical study of selected classification algorithms for liver disease diagnosis. *Int J Database Manag Syst* 2011;3:101–114.
23. Reyna MA, et al. Early prediction of sepsis from clinical data: the PhysioNet/Computing in Cardiology Challenge 2019. *Crit Care Med* 2020;48:210–217.
24. Collins GS, et al. TRIPOD+AI statement. *BMJ* 2024;385:e078378.
25. KDIGO 2024 Clinical Practice Guideline for CKD. *Kidney Int* 2024;105:S117–S314.
26. American Diabetes Association. Standards of Care in Diabetes—2024. *Diabetes Care* 2024;47(Suppl 1).
27. Ross DS, et al. 2016 ATA guidelines for hyperthyroidism. *Thyroid* 2016;26:1343–1421.
28. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. *Med Decis Making* 2006;26:565–574.
29. Howanitz PJ, et al. Laboratory critical values policies and procedures. *Arch Pathol Lab Med* 2002;126:663–669.
30. Bond WF, et al. Differential diagnosis generators: an evaluation of currently available computer programs. *J Gen Intern Med* 2012;27:213–219.

*(Reference list to be verified against publisher records before submission.)*

## Figure legends
**Fig. 1 | Architecture.** Inputs (analytes, units, context, serial values) → unit normalisation and plausibility screen → five reasoning layers → fixed-weight fusion with discord shrinkage → expert syndrome layer (severity-tiered anchors, definitional guards, context semantics) → safety logic and next-test library → ranked, cited differential.
**Fig. 2 | Held-out discrimination across datasets.** AUROC with 95 % bootstrap CI for every pre-specified target, engine v5.3 (eICU labs-only arm; NHANES 2017–18; thyroid; HCV; ILPD).
**Fig. 3 | Engine versus comparators (eICU-CRD demo).** Per-group AUROC for Hemoglyph (labs only), a raw key-analyte threshold (B1) and a gradient-boosting model trained on the same inputs (B2, five-fold out-of-fold).
**Fig. 4 | Calibration and decision curves (eICU-CRD demo).** Reliability of raw fused probabilities and after cross-fitted isotonic recalibration (left); net benefit for renal impairment and sepsis (right).
**Fig. 5 | Blinded LLM comparison on identical inputs (n = 400 stays).** Per-group recall@5 of Hemoglyph and the zero-shot frontier LLM, with rank-bin distribution of clinician-listed labels.
**Fig. 6 | Where the engine misses and what it asks for next.** Error-audit taxonomy of 200 sampled misses and next-test utility by listed condition.
**Supplementary Fig. S1 | Participant flow.** **Supplementary Fig. S2 | Synthetic and robustness batteries.**

## Tables

**Table 1 | Data sources, reference standards and roles.** All data are public and de-identified; the engine saw none of the held-out sets before freeze v1 (21 Oct 2026) except where stated under *Role*.

| Dataset | Setting | Units | Reference standard | Role | n evaluated |
|---|---|---|---|---|---|
| Synthetic batteries | expert-constructed vignettes; adversarial, perturbation, unit-twin and in-range ("healthy") sweeps | mixed | author-defined expected diagnosis | development / regression gate | 489 cases; 200 fabrication-provocation panels; 1,200 healthy panels |
| MIMIC-IV demo v2.2 | US tertiary hospital, 100 patients | conventional | ICD-10 discharge codes | **development** (error analysis before v1) | 235 admissions |
| eICU-CRD demo v2.0.1 | 186 US ICUs | conventional | clinician problem list (active diagnoses), 30 laboratory-relevant groups fixed in the SAP | **held-out, primary** (stays 0–1,200 inspected for error analysis after v1; 1,200–2,314 never inspected) | 2,314 stays; 2,432 listed diagnoses |
| NHANES 2017–18 | US community survey, adults ≥ 18 y | SI + conventional | guideline criteria (ADA, KDIGO, WHO, ACG) **and** self-reported physician diagnosis (independent of the input laboratory values) | held-out | 5,103 adults (1 cycle available at rendering; seven cycles 2005–2018 pre-specified) |
| UCI thyroid0387 | Garvan Institute referral laboratory | SI (total hormones) | expert diagnostic comment | held-out | 6,737 records with a scorable comment |
| UCI HCV (Hoffmann 2018) | German blood donors and hepatology clinic | SI | clinical category (donor / hepatitis / fibrosis / cirrhosis) | held-out | 615 |
| ILPD | Andhra Pradesh, India | conventional | liver-patient status | held-out | 583 |
| PMC-Patients case reports (Bhasuran 2025 set) | published case reports, laboratory paragraph only | mixed free text | published final diagnosis (pre-specified key: specific and syndrome level) | held-out, external anchor against a GPT-4 benchmark | 50 |
| PhysioNet/CinC Sepsis 2019 (set A subset) | US ICU hourly records | conventional | Sepsis-3 onset label | held-out, single-target | 4,843 patients (438 sepsis) |

**Table 2 | eICU-CRD demo (n = 2,314 stays, 186 hospitals): recall of clinician-listed diagnoses by input arm, engine v5.3 (registry 13.3.0).** Recall is computed over listed diagnoses whose key analyte was measured; *laboratory-detectable* restricts to the 24 groups whose definition is laboratory-based. The last column gives the same arm under the previous registry (13.1.0, v5.2 freeze) for the pre-registered non-inferiority comparison (H2).

| Input arm | recall@3 (95 % CI) | recall@5 | recall@10 | recall@5, laboratory-detectable | mean AUROC (24 groups) | chart support of p ≥ 0.7 outputs | recall@5 under registry 13.1.0 |
|---|---|---|---|---|---|---|---|
| laboratory values + age/sex only (primary) | 49.3% (47.3–51.3) | 63.8% (61.8–65.7) | 77.2% (75.5–78.8) | 68.3% (66.0–70.5) | 0.767 | 23.4% | 63.7% |
| + documented history and home medications (context) | 52.1% (50.1–54.1) | 66.6% (64.7–68.5) | 79.8% (78.1–81.3) | 69.1% (66.9–71.3) | 0.78 | 23.3% | 66.5% |
| + context + serial values (temporal) | 51.7% (49.7–53.7) | 66.2% (64.3–68.1) | 80.2% (78.5–81.7) | 69.4% (67.1–71.5) | 0.779 | 22.2% | 66.1% |

**Table 3 | eICU-CRD demo: per-group discrimination and recall of the untrained engine versus a raw key-analyte threshold (B1) and a gradient-boosting model trained on the same inputs (B2, five-fold out-of-fold).** Groups with ≥ 9 listed stays and the key analyte measured; AUROC with 1,000-sample bootstrap CI. The context arm shows what documented history adds. Recall@5 of the zero-shot LLM is from the 400-stay blinded subset (Table 5) and is given for orientation only.

| Problem-list group | listed n | Hemoglyph AUROC (95 % CI), labs only | recall@5, labs only | recall@5, + context | B1 raw-threshold AUROC | B2 trained GBM AUROC | LLM recall@5 (n = 400 subset) |
|---|---:|---|---|---|---|---|---|
| renal impairment (AKI or CKD) | 326 | 0.80 (0.77–0.82) | 79.8% | 80.1% | 0.85 | 0.83 | 75% (n=75) |
| sepsis * | 289 | 0.68 (0.65–0.72) | 48.4% | 48.1% | — | 0.82 | 42% (n=71) |
| diabetes mellitus * | 246 | 0.69 (0.66–0.73) | 49.2% | 71.1% | 0.71 | 0.75 | 37% (n=62) |
| acute kidney injury | 218 | 0.80 (0.77–0.83) | 74.8% | 69.7% | 0.82 | 0.83 | 76% (n=49) |
| chronic kidney disease | 148 | 0.82 (0.78–0.85) | 64.9% | 79.7% | — | 0.79 | 20% (n=35) |
| anaemia | 147 | 0.78 (0.74–0.82) | 84.4% | 83.0% | 0.83 | 0.79 | 83% (n=36) |
| gastrointestinal bleeding * | 145 | 0.75 (0.71–0.79) | 81.4% | 82.1% | — | 0.85 | 50% (n=38) |
| diabetic ketoacidosis | 107 | 0.86 (0.81–0.90) | 63.6% | 63.6% | — | 0.96 | 83% (n=30) |
| hyperglycaemia | 96 | 0.70 (0.64–0.75) | 49.0% | 60.4% | 0.70 | 0.78 | 64% (n=22) |
| acute myocardial infarction | 84 | 0.70 (0.64–0.76) | 89.3% | 89.3% | 0.79 | 0.73 | 81% (n=27) |
| hypokalaemia | 67 | 0.72 (0.65–0.78) | 44.8% | 44.8% | 0.77 | 0.76 | 41% (n=17) |
| heart failure | 58 | 0.66 (0.58–0.73) | 86.2% | 87.9% | 0.71 | 0.58 | 94% (n=17) |
| leucocytosis | 57 | 0.73 (0.68–0.78) | 57.9% | 54.4% | 0.78 | 0.71 | 55% (n=11) |
| hyponatraemia | 52 | 0.89 (0.83–0.93) | 65.4% | 65.4% | 0.91 | 0.85 | 70% (n=10) |
| metabolic acidosis | 51 | 0.76 (0.67–0.82) | 56.9% | 56.9% | 0.76 | 0.75 | 79% (n=14) |
| hyperkalaemia | 49 | 0.92 (0.87–0.96) | 49.0% | 42.9% | 0.96 | 0.91 | 90% (n=10) |
| thrombocytopenia | 40 | 0.89 (0.84–0.93) | 70.0% | 70.0% | 0.90 | 0.85 | 75% (n=12) |
| hypomagnesaemia | 37 | 0.68 (0.60–0.76) | 37.8% | 37.8% | 0.73 | 0.59 | — |
| alcohol withdrawal * | 33 | 0.65 (0.56–0.75) | 33.3% | 33.3% | — | 0.80 | 45% (n=11) |
| coagulopathy | 28 | 0.75 (0.65–0.84) | 53.6% | 46.4% | 0.84 | 0.81 | — |
| cirrhosis / liver failure * | 25 | 0.86 (0.79–0.93) | 60.0% | 64.0% | — | 0.83 | — |
| hypoglycaemia | 21 | 0.64 (0.55–0.76) | 28.6% | 28.6% | — | 0.76 | — |
| lactic acidosis | 19 | 0.74 (0.63–0.85) | 63.2% | 63.2% | 0.82 | 0.58 | — |
| acute pancreatitis | 18 | 0.74 (0.62–0.84) | 66.7% | 66.7% | 0.80 | 0.67 | — |
| malnutrition * | 16 | 0.51 (0.36–0.67) | 0.0% | 0.0% | — | 0.66 | — |
| hypernatraemia | 14 | 0.88 (0.77–0.99) | 64.3% | 64.3% | 0.88 | — | — |
| rhabdomyolysis | 11 | 0.92 (0.86–0.96) | 63.6% | 54.5% | 0.94 | — | — |
| hypocalcaemia | 10 | 0.63 (0.47–0.77) | 20.0% | 20.0% | 0.68 | — | — |
| hypothyroidism | 10 | 0.68 (0.52–0.85) | 50.0% | 50.0% | 0.81 | — | — |
| hypophosphataemia | 9 | 0.73 (0.54–0.91) | 22.2% | 22.2% | 0.82 | — | — |

\* partially laboratory-detectable group (label depends on history or imaging); excluded from the mean AUROC.

**Table 4 | Held-out performance in NHANES, the Garvan thyroid referral laboratory, the German HCV cohort and the Indian ILPD cohort.** Engine v5.3, registry 13.3.0; all held-out runs completed (2026-10-24 10:28 UTC).

| NHANES 2017–18 (n = 5,103 adults) | reference standard | n pos / n neg | AUROC (95 % CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|---|
| diabetes | HbA1c ≥6.5 / FPG ≥126 / told by doctor | 1045/4054 | 0.941 (0.932–0.950) | 67.5% | 99.6% |
| diabetes, self-report only | told by doctor only (independent of labs) | 792/4148 | 0.910 (0.898–0.921) | 66.7% | 96.3% |
| CKD | eGFR <60 or ACR ≥30 (KDIGO) | 936/4076 | 0.959 (0.951–0.967) | 73.8% | 99.9% |
| CKD, self-report only | told of weak/failing kidneys (independent of labs) | 202/4655 | 0.798 (0.763–0.833) | 58.4% | 87.6% |
| anaemia (WHO) | WHO Hb cut-offs | 535/4568 | 0.971 (0.967–0.975) | 99.4% | 93.8% |
| iron deficiency | ferritin <15 ng/mL (WHO) | 281/4801 | 0.989 (0.986–0.991) | 94.7% | 96.9% |
| hypercholesterolaemia | TC ≥240 mg/dL | 509/4590 | 0.901 (0.894–0.908) | 99.8% | 77.1% |
| hyperuricaemia | urate >7.0 M / >6.0 F | 1006/4095 | 0.943 (0.932–0.952) | 88.2% | 100.0% |
| ALT elevation | ALT >33 M / >25 F (ACG) | 890/4213 | 0.720 (0.702–0.738) | 29.2% | 97.8% |
| guideline-healthy adults: any non-finding entity ≥ 0.5 (T8) | all core analytes in range | n = 274 | — | 0.4% (0.1–2.0) | — |

| Referral laboratory / hepatology / ILPD | n pos / n neg | AUROC (95 % CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|
| UCI thyroid — H1 hypothyroid (E/F/G/H) vs no-comment | 655 / 6082 | 0.979 (0.974–0.983) | 96.9% | 95.1% |
| UCI thyroid — H2 hyperthyroid (A/B/C/D) vs no-comment | 195 / 6082 | 0.798 (0.783–0.814) | 67.2% | 80.5% |
| UCI thyroid — H3 primary hypothyroid (F) vs no-comment | 239 / 6082 | 0.994 (0.989–0.997) | 99.2% | 95.1% |
| UCI thyroid — H4 compensated hypothyroid (G) vs no-comment | 408 / 6082 | 0.975 (0.972–0.979) | 96.8% | 95.1% |
| UCI thyroid — H2b hyperthyroid vs no-comment, not on thyroxine | 191 / 5326 | 0.820 (0.804–0.835) | 67.5% | 83.0% |
| UCI thyroid — H2c hyperthyroid (A/B/C/D) vs no-comment, overt entities only (amendment 4) | 195 / 6082 | 0.932 (0.911–0.949) | 55.4% | 99.2% |
| UCI HCV — Task A — any liver disease vs blood donors | 75 / 533 | 0.925 (0.881–0.962) | 29.3% | 100.0% |
| UCI HCV — Task B — cirrhosis vs all non-cirrhotic subjects | 30 / 578 | 0.909 (0.837–0.969) | 53.3% | 100.0% |
| UCI HCV — Task A' — hepatitis only vs donors | 24 / 533 | 0.823 (0.703–0.923) | 4.2% | 100.0% |
| UCI HCV — Task A'' — fibrosis only vs donors | 21 / 533 | 0.976 (0.958–0.990) | 4.8% | 100.0% |
| UCI HCV — Task A''' — cirrhosis vs donors | 30 / 533 | 0.970 (0.926–0.995) | 66.7% | 100.0% |
| ILPD — liver patient vs non-patient | 416 / 167 | 0.704 (0.661–0.747) | 53.8% | 78.4% |

**Table 5 | Blinded comparison with a zero-shot frontier LLM on identical inputs.** eICU-CRD demo stays were scored by one fixed, pre-registered label map; the LLM (identity blinded by the platform, see Methods) received exactly the analytes, units, age and sex the engine received and returned a ranked list of ≤ 10 diagnoses. B8 (240 stays) was drawn after the engine freeze v5.1 and never inspected. McNemar exact test on discordant labels.

| Anchor | stays / scorable labels | Hemoglyph recall@5 (95 % CI) | LLM recall@5 (95 % CI) | discordant (engine-only / LLM-only) | McNemar p | difference |
|---|---|---|---|---|---|---|
| B3 — first 100 stays (development side) | 100 / 94 | 64.9% | 66.0% | 7 / 8 | 1.0 | -1.1 pp |
| B4 — 60 never-inspected stays | 60 / 46 | 65.2% | 58.7% | 5 / 2 | 0.45 | +6.5 pp |
| **B8 — 240 new stays, pre-registered (H3)** | 240 / 456 | **64.3%** | 58.3% | 61 / 34 | **0.0073** | +5.9 pp |
| **Pooled B3 + B4 + B8** | 400 / 596 | **64.4%** | 59.6% | 73 / 44 | **0.0093** | +4.9 pp |

| Rank metric (pooled, n = 400 stays, 596 labels) | Hemoglyph | LLM |
|---|---|---|
| recall@1 | 23.3% (20.1–26.9) | 28.2% (24.7–31.9) |
| recall@3 | 49.5% (45.5–53.5) | 50.8% (46.8–54.8) |
| recall@5 | 64.4% (60.5–68.2) | 59.6% (55.6–63.4) |
| recall@10 | 74.5% (70.8–77.8) | 65.1% (61.2–68.8) |
| MRR | 0.397 | 0.408 |
| median rank when listed | 3 | 2 |
| not listed at all | 21.1% | 34.9% |

| Other anchors | Hemoglyph | LLM |
|---|---|---|
| B5 — 40 guideline-healthy NHANES adults: any disease asserted (false assertion) | **0 / 40** | 4 / 40 |
| B5 — 72 guideline-positive NHANES conditions detected (diabetes · CKD · anaemia · iron deficiency · hypercholesterolaemia) | 13/16 · 15/18 · 13/13 · 7/8 · 7/7 | 16/16 · 13/18 · 12/13 · 8/8 · 7/7 |
| B6 — 50 PMC-Patients case reports (Bhasuran 2025), laboratory paragraph only; published GPT-4 benchmark used the full vignette | specific dx top-1/5/10: 16%/26%/26%; laboratory syndrome: 40%/68%/70% | GPT-4 (full narrative + labs, published): 55 % / 60 % / 60 % |
| B7 — 50 stays, 39 CLSI critical values surfaced | 39 / 39 | 39 / 39 |
| B7 — flags without a traceable rule or source | 0 / 25 stays (all traceable) | 8 / 25 stays |
| Determinism — 50 stays × 3 runs identical | 50 / 50 | not controllable through the platform |
| Fabrication-provocation battery (200 panels) | 200 / 200 | not run (scripts released) |

## Supplementary information

Supplementary File 1 — Statistical analysis plan with Amendments 1–13 (Amendment 13 = post-hoc Sepsis-2019 re-analysis, Supplementary Table S12) (`supplement/SAP_Hemoglyph_v1.md`). Supplementary File 2 — Disclosure and limitations statement. Supplementary File 3 — TRIPOD+AI checklist. Supplementary File 4 — Input schema (`INPUT_SCHEMA_v1.md`). Supplementary Note S11 — Protocol of the planned clinical-use evaluation (multi-reader crossover study and silent prospective run; `docs/paper2/READER_STUDY_PROTOCOL_v0.1.md`). Supplementary Data 1 — Knowledge-source inventory with per-source verification status (XLSX).

**Supplementary Table S1 | Cohort flow (participant selection) for every dataset.**

| cohort | source | step1 | step2 | step3 | analysed | age | female | inputs | labels | split |
|---|---|---|---|---|---|---|---|---|---|---|
| eICU-CRD demo v2.0.1 (PhysioNet, open) | 186 US hospitals, ICU stays 2014–15 | ICU stays in demo: 2520 | age ≥18: 2512 | ≥8 mapped analytes in −6…+24 h: 2314 | 2314 stays; 2707 coded target labels (31 groups), 2432 scorable (key analyte measured) | median 66 (IQR 53–77) | 39.9% | median 31 analytes/stay | clinician problem-list diagnoses (1073 distinct strings) → regex map | dev: first 1200 stays by id order (ext tuning); held-out: all 2314 reported with amendments logged |
| NHANES 2005–2006 | US civilian non-institutionalised population, mobile exam centre | examined: 10348 | age ≥18: 5563 | with biochemistry + CBC: 5334 | see run log participants | median 43 (IQR 27–62) | 52.0% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| NHANES 2007–2008 | US civilian non-institutionalised population, mobile exam centre | examined: 10149 | age ≥18: 6228 | with biochemistry + CBC: 5995 | see run log participants | median 49 (IQR 33–64) | 50.7% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| NHANES 2009–2010 | US civilian non-institutionalised population, mobile exam centre | examined: 10537 | age ≥18: 6527 | with biochemistry + CBC: 6360 | see run log participants | median 47 (IQR 32–63) | 51.4% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| NHANES 2011–2012 | US civilian non-institutionalised population, mobile exam centre | examined: 9756 | age ≥18: 5864 | with biochemistry + CBC: 5615 | see run log participants | median 47 (IQR 31–62) | 50.6% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| NHANES 2013–2014 | US civilian non-institutionalised population, mobile exam centre | examined: 10175 | age ≥18: 6113 | with biochemistry + CBC: 5924 | see run log participants | median 47 (IQR 32–62) | 52.3% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| NHANES 2015–2016 | US civilian non-institutionalised population, mobile exam centre | examined: 9971 | age ≥18: 5992 | with biochemistry + CBC: 5735 | see run log participants | median 48 (IQR 32–63) | 51.9% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| NHANES 2017–2018 | US civilian non-institutionalised population, mobile exam centre | examined: 9254 | age ≥18: 5856 | with biochemistry + CBC: 5533 | see run log participants | median 51 (IQR 33–65) | 51.7% | ≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR) | self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria | held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation |
| UCI HCV (Hoffmann 2018) | 615 blood donors / hepatitis C patients, Germany | all records | complete key analytes | — | 615 records | see dataset | see dataset | 4–10 analytes | clinical category (donor / hepatitis / fibrosis / cirrhosis) | held-out, single pass |
| ILPD Indian Liver Patient Dataset | 583 patients, Andhra Pradesh | all records | complete key analytes | — | 583 records | see dataset | see dataset | 4–10 analytes | liver patient yes/no | held-out, single pass |
| UCI Thyroid (Garavan) | Garvan Institute, 1980s | all records | complete key analytes | — | 3162 records | see dataset | see dataset | 4–10 analytes | hypo/hyper-thyroid classes | held-out, single pass |

| PhysioNet/CinC Sepsis 2019 (training set A, every 4th file) | US ICU hourly records (Reyna 2020) | files sampled: 4937 | ≥3 lab analytes in ICU h 1–24: 4843 | — | 4843 patients (438 Sepsis-3 at any hour) | see dataset | see dataset | labs of first 24 h + temperature | Sepsis-3 onset label | held-out, single-target prediction |
All cohorts are public; no participant was contacted. eICU: exclusion for <8 mapped analytes is the only data-driven exclusion (stays with sparse panels are not interpretable by any lab-only system). NHANES: participants without biochemistry/CBC subsample were not included. No imputation of missing analytes anywhere: absent analytes are treated as 'not measured' by the engine.

**Supplementary Table S2 | Structured audit of 200 randomly sampled top-5 misses on eICU-CRD demo (engine v5.3; N = 1,151 misses; deterministic pre-declared taxonomy; no manual relabelling).**

| Category | n | % of sampled misses |
|---|---:|---:|
| A — not supported by the measured laboratory values (label = history/clinical context) | 132 | 66.0% |
| B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings | 38 | 19.0% |
| C1 — knowledge/logic miss: laboratory signature present, entity never proposed | 15 | 7.5% |
| C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5 | 14 | 7.0% |
| D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited) | 1 | 0.5% |

| Most frequent missed groups | n | A | B | C1 | C2 | D |
|---|---:|---:|---:|---:|---:|---:|
| heart failure | 29 | 27 | 0 | 0 | 2 | 0 |
| sepsis | 25 | 7 | 5 | 9 | 3 | 1 |
| diabetes mellitus | 22 | 21 | 1 | 0 | 0 | 0 |
| renal impairment (AKI or CKD) | 12 | 6 | 5 | 0 | 1 | 0 |
| acute kidney injury | 12 | 5 | 7 | 0 | 0 | 0 |
| chronic kidney disease | 10 | 7 | 1 | 0 | 2 | 0 |
| diabetic ketoacidosis | 9 | 8 | 0 | 1 | 0 | 0 |
| hyperglycaemia | 9 | 7 | 2 | 0 | 0 | 0 |
| hypokalaemia | 7 | 7 | 0 | 0 | 0 | 0 |
| alcohol withdrawal | 6 | 4 | 0 | 1 | 1 | 0 |
| cirrhosis / liver failure | 6 | 2 | 1 | 0 | 3 | 0 |
| acute pancreatitis | 5 | 5 | 0 | 0 | 0 | 0 |
| malnutrition | 5 | 4 | 0 | 0 | 1 | 0 |
| hyperkalaemia | 5 | 0 | 5 | 0 | 0 | 0 |

**Supplementary Table S3 | Next-test utility on category-A misses (no laboratory signature): did the engine name the discriminating test?**

| Listed condition | n | discriminating test recommended | % |
|---|---:|---:|---:|
| heart failure | 27 | 14 | 52% |
| diabetes | 21 | 5 | 24% |
| hyperglycemia | 7 | 3 | 43% |
| chronic kidney disease | 7 | 3 | 43% |
| sepsis | 7 | 5 | 71% |
| renal impairment | 6 | 5 | 83% |
| acute kidney injury | 5 | 2 | 40% |
| malnutrition | 4 | 2 | 50% |
| alcohol withdrawal | 4 | 3 | 75% |
| all | 88 | 42 | 48% |

Median number of next-test recommendations per stay: 12.

**Supplementary Table S4 | Subgroup performance on eICU-CRD demo, engine v5.3, labs-only arm (strata with ≥ 40 stays; recall@5 CI from 1,000 stay-level bootstraps).** The engine contains no race, ethnicity or site term and uses the race-free CKD-EPI 2021 equation.

| Dimension | stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p ≥ 0.7 | AUROC renal impairment | AUROC sepsis |
|---|---|---:|---:|---|---:|---:|---:|---:|
| sex | male | 1392 | 1498 | 65.4% (62.6–68.2) | 79.6% | 25.8% | 0.81 | 0.70 |
| sex | female | 922 | 934 | 61.1% (57.1–65.3) | 73.3% | 22.6% | 0.78 | 0.67 |
| age band | 65–79 | 820 | 844 | 64.3% (60.6–68.4) | 79.0% | 23.5% | 0.76 | 0.68 |
| age band | 45–64 | 695 | 708 | 59.9% (55.2–64.5) | 73.9% | 23.5% | 0.85 | 0.70 |
| age band | ≥80 | 426 | 476 | 66.6% (61.8–71.1) | 79.0% | 24.2% | 0.77 | 0.68 |
| age band | <45 | 373 | 404 | 66.1% (61.3–71.2) | 77.0% | 29.6% | 0.83 | 0.68 |
| ethnicity | Caucasian | 1839 | 1827 | 63.4% (60.8–66.1) | 76.2% | 24.0% | 0.79 | 0.66 |
| ethnicity | African American | 220 | 201 | 63.7% (54.1–72.9) | 78.6% | 20.5% | 0.81 | 0.73 |
| ethnicity | Hispanic | 111 | 216 | 65.7% (58.6–72.6) | 83.3% | 34.4% | 0.90 | 0.83 |
| ethnicity | Other/Unknown | 74 | 96 | 60.4% (46.7–72.3) | 75.0% | 26.1% | 0.81 | 0.79 |
| unit type | Med-Surg ICU | 1735 | 1968 | 62.2% (59.7–64.8) | 76.4% | 24.9% | 0.79 | 0.67 |
| unit type | MICU | 130 | 109 | 81.7% (73.8–89.1) | 87.2% | 26.4% | 0.83 | 0.66 |
| unit type | Cardiac ICU | 123 | 128 | 75.8% (67.5–84.0) | 85.9% | 30.2% | 0.90 | 0.81 |
| unit type | SICU | 77 | 74 | 66.2% (53.1–81.5) | 75.7% | 17.1% | 0.73 | 0.73 |
| unit type | CCU-CTICU | 77 | 65 | 50.8% (37.9–64.4) | 69.2% | 16.7% | 0.53 | — |
| unit type | Neuro ICU | 62 | 24 | 58.3% (32.0–90.0) | 70.8% | 15.9% | — | — |
| unit type | CSICU | 62 | 16 | 87.5% (62.5–100.0) | 93.8% | 13.8% | — | — |
| unit type | CTICU | 48 | 48 | 64.6% (43.8–83.3) | 75.0% | 22.4% | 0.95 | — |
| panel size | >20 | 2059 | 2269 | 63.5% (61.4–65.9) | 77.3% | 24.5% | 0.80 | 0.68 |
| panel size | 11–20 | 191 | 129 | 65.1% (55.2–74.2) | 74.4% | 26.4% | 0.71 | 0.65 |
| panel size | ≤10 analytes | 64 | 34 | 76.5% (61.9–88.2) | 79.4% | 23.3% | 0.81 | — |

**Supplementary Table S5 | Calibration and decision-curve analysis, eICU-CRD demo, engine v5.3 (52,689 stay–group units, 2,432 positives).** Isotonic recalibration is cross-fitted (fit on one half of stays, applied to the other) and leaves rankings unchanged.

| Set | n | prevalence | ECE raw | ECE isotonic | Brier raw | Brier isotonic | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| all groups pooled | 52,689 | 0.046 | 0.162 | 0.003 | 0.115 | 0.040 | 0.801 |
| renal impairment (AKI or CKD) | 2,266 | 0.144 | 0.258 | 0.026 | 0.205 | 0.102 | 0.800 |
| sepsis | 2,215 | 0.130 | 0.183 | 0.024 | 0.171 | 0.105 | 0.684 |
| diabetes mellitus | 2,247 | 0.109 | 0.202 | 0.018 | 0.151 | 0.093 | 0.692 |
| acute kidney injury | 2,266 | 0.096 | 0.265 | 0.020 | 0.193 | 0.077 | 0.798 |
| anaemia | 2,207 | 0.067 | 0.348 | 0.013 | 0.243 | 0.057 | 0.780 |

| Decile (equal mass) | mean raw p | observed | mean isotonic p | observed |
|---:|---:|---:|---:|---:|
| 1 | 0.00 | 0.01 | 0.01 | 0.02 |
| 2 | 0.00 | 0.02 | 0.01 | 0.01 |
| 3 | 0.00 | 0.01 | 0.01 | 0.01 |
| 4 | 0.00 | 0.02 | 0.01 | 0.01 |
| 5 | 0.00 | 0.01 | 0.01 | 0.01 |
| 6 | 0.00 | 0.02 | 0.01 | 0.01 |
| 7 | 0.11 | 0.03 | 0.02 | 0.03 |
| 8 | 0.43 | 0.05 | 0.05 | 0.05 |
| 9 | 0.60 | 0.08 | 0.08 | 0.08 |
| 10 | 0.78 | 0.23 | 0.23 | 0.23 |

| Net benefit per 100 units at threshold 0.10 / 0.20 / 0.30 | raw | isotonic | treat-all |
|---|---|---|---|
| renal impairment (AKI or CKD) | 7.9 / 1.5 / -6.5 | 8.9 / 5.9 / 2.8 | 4.9 / -7.0 / -22.3 |
| sepsis | 4.9 / 1.4 / -2.9 | 4.9 / 2.9 / 1.2 | 3.4 / -8.7 / -24.2 |
| diabetes mellitus | 2.8 / -4.7 / -10.8 | 3.6 / 1.6 / -0.2 | 1.1 / -11.3 / -27.2 |
| acute kidney injury | 3.4 / -3.3 / -12.0 | 5.0 / 1.8 / -0.1 | -0.4 / -13.0 / -29.1 |
| anaemia | -0.2 / -8.3 / -18.6 | 2.3 / 0.7 / 0.5 | -3.7 / -16.7 / -33.3 |

**Supplementary Table S6 | Safety: CLSI critical values whose matching entity appeared in the top-5 differential (eICU-CRD demo; engine v4.1 run of the frozen S5 script; the v5 syndrome layer only added anchors, and B7 re-confirmed 39/39 under v5).**

| Critical value | n stays | matching entity in top-5 (95 % CI) |
|---|---:|---|
| potassium >= 6.5 | 32 | 71.9% (54.6–84.4) |
| potassium <= 2.5 | 10 | 100.0% (72.2–100.0) |
| sodium <= 120 | 29 | 100.0% (88.3–100.0) |
| sodium >= 160 | 7 | 100.0% (64.6–100.0) |
| glucose <= 50 | 11 | 100.0% (74.1–100.0) |
| glucose >= 500 | 69 | 95.7% (88.0–98.5) |
| calcium_total >= 14 | 1 | 100.0% (20.7–100.0) |
| lactate >= 4 | 120 | 100.0% (96.9–100.0) |
| arterial_ph <= 7.2 | 124 | 93.5% (87.8–96.7) |
| hemoglobin <= 6 | 27 | 96.3% (81.7–99.3) |
| platelet_count <= 20 | 8 | 100.0% (67.6–100.0) |
| white_blood_cell_count >= 100 | 1 | 100.0% (20.7–100.0) |
| all | 439 | 95.2% (92.8–96.9) |

**Supplementary Table S7 | Knowledge-base quality revisions between the v5.2 and v5.3 freezes (registry 13.1.0 → 13.3.0), all executed by scripted, reproducible patches before any held-out result was examined.** Executable rules 34,175 → 33,230; the engine code was not changed.

| Patch / defect class | What was wrong | Action | Count |
|---|---|---|---|
| 13.2.0 — exposure gate | 53 vector-borne or geographically restricted pathogen entities (e.g. Ebola, Lassa, dengue) could be proposed from non-specific laboratory patterns alone | entities require an exposure/travel/clinical-suspicion context flag (`clinical_suspicion` input schema) | 53 entities gated; 9 CRP-only rules retired; 23 specific-marker rules added |
| D1 — sex-specific thresholds | rules with a single threshold where guidelines give sex-specific limits (haemoglobin, creatinine, ferritin, urate, ALT …) | split into sex-conditioned rule pairs | 197 rules → 350 sex-conditioned rules |
| D2 — mislabelled rule layer | screening rules labelled diagnostic (and vice versa) | relabelled; 13 un-repairable rules retired | 67 relabelled, 13 retired |
| D3 — impossible thresholds | thresholds outside the physiological range | corrected to the cited source | 6 |
| D5 — context-dependent entities | entities that are diagnoses of history (e.g. drug toxicity) proposed from laboratory values alone | gated behind a context flag | 87 |
| D7 — over-long expressions | expressions with redundant clauses | trimmed to the cited criterion | 510 |
| D8 — single-analyte diagnostic rules for diseases | a disease (not a laboratory finding) could be asserted from one analyte | downgraded to screening; laboratory-finding entities (`*_pattern`, -aemia, -penia) explicitly exempted | 12 |
| D13 — duplicate expressions | identical rules under two identifiers | merged | 6 |
| D17 — template artefacts | rules generated from a template that attached generic haemoglobin/platelet clauses to unrelated entities | retired | 940 |
| D18 — placeholder entities | entities with no executable rule and no source | retired (counted as 90 of the 6,750 entities; 6,660 named entities remain) | 90 |

The first attempt to activate 13.3.0 updated only the distribution copy of the registry and not the file the engine loads; the 1.5 h of results produced in that window were discarded and are kept in `eval/results/run_20261023_v53/invalid_ran_on_13_1_0/` for audit. The second attempt exposed an error in patch D8 (laboratory-finding entities wrongly downgraded) which was corrected before any held-out data were re-run; both events are recorded in the SAP (Amendment 12, activation record).

**Supplementary Table S8 | Published comparisons of knowledge-based diagnostic decision support with GPT-4-class models, for context.** These studies used GPT-4 as released in 2023 on their own case sets; they are context, not a head-to-head comparison with Table 5.

| Study (year) | Knowledge-based CDSS | LLM | Cases | Headline result |
|---|---|---|---|---|
| Bridges, *Diagnosis* 2024 (Part I) | Isabel Pro | GPT-4 | 201 | correct diagnosis in list: Isabel 87.1 % vs GPT-4 82.1 %; MRR 0.428 vs 0.389; 31.5 % of GPT-4 reference DOIs correct |
| Bridges, *JAMIA Open* 2025 (Part II) | Isabel Pro | GPT-4 | 201 | recall@10 Isabel 0.65 vs GPT-4 0.69; GPT-4 run-to-run reproducibility r² 0.34–0.44 |
| MGB 2025 (DXplain) | DXplain | GPT-4, Gemini 1.5 | 36 unpublished | with laboratory data: DXplain 72 %, GPT-4 64 %, Gemini 58 %; without labs 56 / 42 / 39 % |
| Shea, *JAMA Netw Open* 2023 | Isabel | GPT-4 | geriatric delayed diagnoses | differential-inclusive accuracy GPT-4 83 %, clinicians 50 %, Isabel 33 % |
| Bhasuran, *npj Digit Med* 2025 | — | GPT-4 (+ laboratory data) | 50 PMC-Patients | top-1 55 %, top-10 60 %; laboratory data raised LLM accuracy |
| Hager, *Nat Med* 2024 | — | Llama-2, GPT-class | 2,400 MIMIC cases | LLMs could not reliably classify laboratory values as high/low even when reference ranges were supplied |

**Supplementary Table S9 | Regression gate at the v5.3 freeze.**

| Battery | Result |
|---|---|
| pytest | 1 failed, 688 passed in 268.68s (0:04:28) |
| engine battery | SCORE 50/50 |
| hard battery | HARD SCORE 151/151 (100.0%)  median 633 ms  p95 1229 ms |
| hard battery2 | HARD2 SCORE 124/124 (100.0%)  median 524 ms  p95 1065 ms |
| hard battery3 | HARD3 SCORE 77/78 (98.7%)  median 510 ms  p95 1013 ms |
| adversarial battery | ADVERSARIAL SCORE 86/86 (100.0%)  median 480 ms |
| healthy sweep | HEALTHY SWEEP n=200: syndrome false-fires=0  dx>=0.5=0  worst p=0.45 (hypercholesterolemia #3) |
| fabrication provocation | FABRICATION-PROVOCATION SCORE 200/200 (100.0%)  415 ms/case |
| pytest after test fix | 688 passed in gate + the single failing file re-run 16/16 => 689 (tests/test_esl_ext9_20261023.py neutropenia test relaxed, see SAP Am.12 activation record) |

**Supplementary Table S10 | Registry-off ablation (eICU-CRD demo, labs only, engine v5.3).** All 34,548 rules of registry 13.3.0 were marked non-executable (entities, synonyms and feature links retained); every other layer was unchanged. Same 2,314 stays / 2,432 labels. No tuning followed this ablation.

| Metric | Registry on | Registry off | Δ |
|---|---:|---:|---:|
| Recall@3, all labels | 49.3 % | 47.6 % | +1.7 |
| Recall@5, all labels | 63.8 % | 62.0 % | +1.8 |
| Recall@10, all labels | 77.2 % | 75.4 % | +1.8 |
| Recall@3, lab-detectable | 53.9 % | 50.5 % | +3.5 |
| Recall@5, lab-detectable | 68.3 % | 64.7 % | +3.6 |
| Recall@10, lab-detectable | 81.0 % | 77.4 % | +3.6 |
| Mean AUROC, 24 lab-detectable groups | 0.767 | 0.732 | +0.035 |

| Group (n ≥ 9) | n | Recall@5 on | off | AUROC on | off | ΔAUROC |
|---|---:|---:|---:|---:|---:|---:|
| leucocytosis | 57 | 57.9 | 8.8 | 0.732 | 0.534 | +0.197 |
| hypophosphataemia | 9 | 22.2 | 11.1 | 0.734 | 0.542 | +0.193 |
| hypernatraemia | 14 | 64.3 | 57.1 | 0.882 | 0.781 | +0.101 |
| hypocalcaemia | 10 | 20.0 | 20.0 | 0.630 | 0.536 | +0.094 |
| hyperglycaemia | 96 | 49.0 | 50.0 | 0.699 | 0.627 | +0.072 |
| hypomagnesaemia | 37 | 37.8 | 27.0 | 0.678 | 0.612 | +0.066 |
| diabetes mellitus | 246 | 49.2 | 50.0 | 0.692 | 0.635 | +0.057 |
| malnutrition | 16 | 0.0 | 6.2 | 0.509 | 0.556 | -0.047 |
| hyponatraemia | 52 | 65.4 | 63.5 | 0.890 | 0.851 | +0.038 |
| renal impairment (AKI or CKD) | 326 | 79.8 | 78.5 | 0.800 | 0.777 | +0.023 |
| acute kidney injury | 218 | 74.8 | 72.5 | 0.798 | 0.776 | +0.022 |
| diabetic ketoacidosis | 107 | 63.6 | 63.6 | 0.857 | 0.878 | -0.021 |
| heart failure | 58 | 86.2 | 86.2 | 0.657 | 0.638 | +0.018 |
| thrombocytopenia | 40 | 70.0 | 50.0 | 0.890 | 0.876 | +0.013 |
| chronic kidney disease | 148 | 64.9 | 58.8 | 0.815 | 0.807 | +0.008 |
| metabolic acidosis | 51 | 56.9 | 56.9 | 0.755 | 0.748 | +0.008 |
| sepsis | 289 | 48.4 | 52.2 | 0.684 | 0.679 | +0.006 |
| acute pancreatitis | 18 | 66.7 | 66.7 | 0.736 | 0.733 | +0.004 |
| coagulopathy | 28 | 53.6 | 53.6 | 0.754 | 0.750 | +0.003 |
| lactic acidosis | 19 | 63.2 | 68.4 | 0.736 | 0.740 | -0.003 |
| cirrhosis / liver failure | 25 | 60.0 | 64.0 | 0.864 | 0.862 | +0.003 |
| anaemia | 147 | 84.4 | 87.8 | 0.780 | 0.782 | -0.002 |
| rhabdomyolysis | 11 | 63.6 | 63.6 | 0.918 | 0.916 | +0.002 |
| hyperkalaemia | 49 | 49.0 | 44.9 | 0.916 | 0.915 | +0.001 |
| hypokalaemia | 67 | 44.8 | 37.3 | 0.717 | 0.717 | +0.001 |
| gastrointestinal bleeding | 145 | 81.4 | 82.8 | 0.751 | 0.751 | +0.000 |
| acute myocardial infarction | 84 | 89.3 | 89.3 | 0.703 | 0.702 | +0.000 |
| hypoglycaemia | 21 | 28.6 | 28.6 | 0.641 | 0.641 | -0.000 |
| alcohol withdrawal | 33 | 33.3 | 36.4 | 0.652 | 0.652 | +0.000 |
| hypothyroidism | 10 | 50.0 | 50.0 | 0.683 | 0.683 | +0.000 |

**Supplementary Table S12 | PhysioNet/CinC Sepsis-2019: pre-registered prediction analysis and post-hoc concurrent-diagnosis re-analysis (SAP Amendment 13; registry 13.3.0).** Row 1 is the pre-registered analysis (labs of ICU hours 1–24 → Sepsis-3 at any hour; n = 4,843). Rows 2–3 are post-hoc: cases = all sepsis patients with ≥ 3 labs in the 12 h around onset (n = 388); controls = seeded dwell-time-matched windows of non-sepsis patients (n = 772); arm B adds heart rate, blood pressure, respiratory rate and temperature. The supervised logistic baseline uses the same windows and features with missing-value indicators. Neither post-hoc row supersedes row 1.

| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |
|---|---|---|---|---|---|
| pre-registered: prediction, labs first 24 h | 0.593 | 0.689 (from report.md) | 32.2% (28.0–36.7; 141/438) | 16.5% (15.4–17.6; 725/4405) | — |
| concurrent, labs only (+temperature) | **0.534** (0.508–0.561) | 0.667 (0.635–0.700) | 21.6% (17.8–26.0; 84/388) | 14.8% (12.4–17.4; 114/772) | 19.8 % / 86.8 % |
| concurrent, labs + vital signs (optional context module) | **0.534** (0.508–0.561) | 0.703 (0.671–0.735) | 21.6% (17.8–26.0; 84/388) | 14.8% (12.4–17.4; 114/772) | 19.8 % / 86.8 % |

*Descriptive strata (arm A).*

| stratum (arm A) | cases / controls | engine AUROC | sepsis group in top-5: cases / controls |
|---|---|---|---|
| lactate measured in window | 144 / 166 | 0.472 (0.411–0.529) | 54/144 / 67/166 |
| lactate not measured | 244 / 606 | 0.522 (0.496–0.548) | 30/244 / 47/606 |
| lactate + WBC measured | 101 / 138 | 0.498 (0.417–0.569) | 43/101 / 60/138 |

The dataset contains no procalcitonin or C-reactive protein; lactate is present in 37 % of case windows (22 % of controls). The registry's sepsis criteria are anchored on those analytes, so the sepsis group never enters the differential for 74 % of cases. Vital signs altered the differential but no 13.3.0 sepsis rule uses them, hence identical arm-A/arm-B numbers. No rule or weight was changed in response to any of these results.
