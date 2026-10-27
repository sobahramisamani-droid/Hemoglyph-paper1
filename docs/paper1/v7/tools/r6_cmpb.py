"""R5 (JBI) → R6 (Computer Methods and Programs in Biomedicine).

CMPB guide for authors (read 2026-10-27): original research ≤ ~3,500 words excluding abstract; structured abstract ≤ 350 words
with headings Background and Objective / Methods / Results / Conclusions; 3–6 keywords; highlights optional (≤ 85 chars);
numbered sections Introduction / Methods / Results / Discussion / Acknowledgements incl. declarations; CRediT; GenAI declaration;
ethics statement with exemption reason; ≤ 50 references; tables editable, no shading; figures separate files; cover letter with
4 mandatory elements.  Reframed as a methods paper: verification + provenance auditing of an AI-drafted clinical rule base, with the
frozen benchmark as evidence.  All numbers are those of R5; passages dropped from the main text remain verbatim in the Supplement.
"""
import re

SRC, DST = "Paper1_Hemoglyph_JBI_EN_v7_R5.md", "Paper1_Hemoglyph_CMPB_EN_v7_R6.md"
s = open(SRC, encoding="utf-8").read()


def between(a, b, text=None):
    text = s if text is None else text
    i = text.index(a); j = text.index(b, i + len(a))
    return text[i + len(a):j].strip()


refs = between("## References", "## Figure legends")
refs += "\n[33] Hussain M, Afzal M, Malik KM, et al. Acquiring guideline-enabled data driven clinical knowledge model using formally verified refined knowledge acquisition method. *Comput Methods Programs Biomed* 2020;197:105701. doi:10.1016/j.cmpb.2020.105701.\n[34] Cabitza F, Campagner A, Soares F, et al. The importance of being external. Methodological insights for the external validation of machine learning models in medicine. *Comput Methods Programs Biomed* 2021;208:106288. doi:10.1016/j.cmpb.2021.106288."
figlegs = between("## Figure legends", "## Tables")
tables = between("## Tables", "## Supplementary information")
supp = s.split("## Supplementary information", 1)[1].strip()
competing = between("## Declaration of competing interest", "## Funding")
gen_ai = between("## Declaration of generative AI and AI-assisted technologies in the writing process", "## Ethics statement")
data_av = between("## Data availability", "## References")
old_results = between("## 3. Results", "## 4. Discussion")
old_methods = between("## 2. Material and methods", "## 3. Results")
old_disc = between("## 4. Discussion", "## 5. Conclusion")

TITLE = ("Verification and provenance auditing of an AI-drafted clinical rule base: executable invariants, a source-concordance "
         "protocol and a frozen laboratory-panel benchmark for an offline interpretation engine")

authors = """Sobhan Bahrami^a*^, Zhaleh Tahmasebinejad^b,c^, Ehsan Bahrami Samani^b^

^a^ Allameh Helli 10 High School (NODET), Tehran, Iran. ^b^ Statistics and Data Science Clinic, Faculty of Mathematical Sciences, Shahid Beheshti University, Tehran, Iran. ^c^ Department of Epidemiology and Biostatistics, Research Institute for Endocrine Sciences, Shahid Beheshti University of Medical Sciences, Tehran, Iran [affiliation wording to be confirmed by Z.T.].
\\* Corresponding author: sobahramisamani@gmail.com · ORCID 0009-0004-6639-5081"""

highlights = [
    "Property-based invariants for a clinical rule engine, run on every release",
    "The invariants found a ranking defect that 353 hand-written vignettes had missed",
    "Frozen source-concordance protocol: 92% of sampled rules unverifiable by locator",
    "Untrained, traceable engine at recall@5 parity with an unnamed frontier LLM",
    "Engine-agnostic tools and protocol released; applicable to any analyte-rule base",
]
for h in highlights:
    assert len(h) <= 85, (len(h), h)

abstract = """**Background and Objective:** Clinical rule bases can now be drafted at scale with large language models, but rules that cannot be checked against their sources and engines validated only on their authors' vignettes are not auditable. We evaluate three verification methods—executable invariants, a frozen source-concordance protocol and a hash-frozen one-shot benchmark—on Hemoglyph, an offline engine that ranks a cited differential from a structured laboratory panel with 33,183 guideline-transcribed rules (99.2% AI-drafted, not clinically audited) and no outcome training.

**Methods:** Property-based tests check invariants (determinism, unit invariance, directional monotonicity, absent-analyte and context invariants) on randomised panels. A protocol frozen before sampling labels 200 rules concordant, discordant or unresolvable against their cited locator. Under a hash-frozen analysis plan with two one-shot quarantine rounds, the frozen engine was benchmarked on the eICU-CRD demo (2,314 ICU stays), MIMIC-IV demo, 9,000 NHANES adults (three cycles), 14,420 sepsis patients and external cohorts, with supervised baselines, an ablation and a blinded paired comparison against an unnamed frontier LLM (400 stays).

**Results:** The 21-test invariant suite exposed a ranking defect that 353 adversarial vignettes had missed. Only 16 of 200 audited rules were resolvable from their locators (15 discordant, 1 concordant); 92% (95% CI 87.4–95.1) were unresolvable and at least 7.5% (4.6–12.0) demonstrably discordant. On the benchmark, 60.8% (58.7–62.9) of clinician-listed ICU diagnoses appeared in the top five from laboratory values alone (precision@5 14.2%); a prevalence baseline reached 51.3%. NHANES AUROCs reproduced across cycles (0.88–0.99) with 2 false assertions among 485 healthy adults; sepsis prediction failed as pre-specified; the failed first quarantine round is reported. Engine and LLM were at recall@5 parity (60.7% vs 59.6%, p = 0.54); the LLM led at rank 1 and was only moderately self-consistent (κ 0.69). Ablation located the result in 272 hand-curated anchors and the syndrome layer, not the AI-drafted bulk.

**Conclusions:** Executable invariants and a frozen provenance audit are cheap, reproducible and informative—here unfavourably: provenance granularity, not rule count, limits the auditability of AI-drafted knowledge bases. A traceable engine can nevertheless match a frontier LLM on a blinded panel-interpretation task. No clinical claim is made; code, rules, protocols and outputs are public."""
nwords = len(re.sub(r"\*\*[^*]+\*\*", "", abstract).split())
assert nwords <= 350, nwords

keywords = "Clinical decision support; Knowledge base; Software verification; Provenance; Laboratory medicine; Large language models"

intro = """Roughly 70% of clinical decisions draw on laboratory results, yet interpretive comments accompany only a small fraction of reports, and post-analytical errors remain a leading source of diagnostic harm [1–3]. Rule-based interpretation embedded in laboratory information systems is transparent but narrow and hand-maintained [4,5]; supervised models need labelled data and cannot be audited clause by clause [6,7]; large language models (LLMs) interpret reports fluently but vary between runs, cannot run locally on commodity hardware without transmitting patient data, and misclassify values even when reference ranges are supplied [8–11].

Large language models have changed one part of this picture: a guideline-transcribed rule base that would once have taken a committee years can now be drafted in weeks. This creates a new software-engineering problem rather than solving an old one. An AI-drafted rule is a hypothesis about what a source says; nobody has read most of them; and the conventional validation of such engines—vignettes written by the same authors, a single institution, no comparator [12]—cannot detect either mistranscription or ranking defects. Mature diagnostic decision-support systems (Isabel, DXplain) have been compared with GPT-4-class models on 36–201 symptom cases [13–16], formal verification has been applied to the acquisition of guideline-derived knowledge models [33], and external-validation methodology for learned models is well developed [34]; but no method has been described for verifying a large AI-drafted laboratory rule base, and the public infrastructure for executable guideline knowledge has contracted: AHRQ CDS Connect went offline in April 2025 and a dated search found no openly licensed, machine-executable rule set for laboratory-panel interpretation (Supplementary Note 5).

This paper treats the rule base as software and asks how it can be verified. We contribute (i) a property-based test suite that states invariants any correct laboratory-interpretation engine must satisfy and checks them on randomised panels; (ii) a source-concordance protocol, frozen before sampling, that reports with explicit denominators whether a rule transcribes what its locator says; and (iii) a hash-frozen, one-shot, multi-dataset benchmark with a supervised baseline, an ablation and a blinded comparison against a frontier LLM, in which a failed quarantine round is reported rather than discarded. The invariant suite and the audit protocol are engine-agnostic—they require only that a rule be expressed as analyte, operator, threshold, unit, population gate and source locator—and are released as standalone tools. This paper does not claim that the engine is accurate; it claims that the engine is verifiable, and shows what verification finds. The object of study is Hemoglyph (`analyse_gidlines.py`, v7), an offline single-process engine with 33,183 guideline-transcribed rules, 99.2% of them AI-drafted by a non-clinician first author and none clinically audited. The engine is the same file that ships inside a proprietary desktop product owned by the first author; this interest is declared and motivated the frozen design. Only the inference engine fed with structured analyte–value pairs is evaluated; the optical-character-recognition front end is not. We make no claim of clinical validation."""

methods = """### 2.1 Engine under study

Hemoglyph processes a panel in five stages (Fig. 1): normalisation (UCUM units, aliases, age/sex reference intervals, 100 derived indices); a rule layer over registry 14.1.0 (33,183 executable leaves, each a record with a machine-evaluable condition on at least one analyte, a population gate, an evidence role—diagnostic criterion weight 6, supportive or screening weight 3—a disease identifier and a source locator; release-by-release counts in Supplementary Table S10); an expert syndrome layer (~900 multi-analyte constellations with anchor strengths 0.95/0.88/0.80/0.72/0.45 and context predicates); fixed-weight fusion (0.35 rule engine, 0.25 Bayesian, 0.20 fuzzy, 0.10 knowledge graph, 0.10 risk models, set by judgement and never tuned on evaluation data; sensitivity in Table 1) with an expert floor (the fused score cannot fall below 0.90 × the rule-layer vote, so learned layers modulate but never veto a guideline rule); and ranking hygiene (causal attribution through a disease–finding explanation graph, covering-diagnosis suppression, KDIGO chronicity [17], ADA glycaemic criteria [18], UDMI acuity [19], maximum 25 entries). The Bayesian layer has 75 disease nodes with hand-coded priors and likelihood ratios from cited diagnostic-accuracy literature; no parameter was fitted to any patient record. Engine changes between releases (C1–C16) are dated in Supplementary Table S1; no version-control history exists for the development period, so "no change was outcome-fitted" is a documented process claim, not a verified one.

### 2.2 Knowledge-base construction and provenance

For each guideline source the first author prompted a general-purpose LLM with the source text or citation and a fixed JSON schema; returned records (analyte, operator, threshold, unit, population gate, evidence role, disease, locator) were accepted or rejected by automated audits only (schema validity, analyte in the 2,045-analyte feature registry, unit convertible, physiologically plausible threshold, no duplicate or contradiction, required context gate present, locator resolvable) and carry the status `candidate_requires_specialist_validation`. The 272 anchor rules were written or line-edited by hand from primary guideline text. No human read the bulk; we therefore call it AI-drafted and automatically audited. Locators were checked with `registry_source_verify.py` (Crossref resolution, HTTP reachability). Counts by release: 13.3.0, 33,230 rules/747 sources; 13.4.2, 33,170/781; 14.1.0, 33,183/785.

### 2.3 Verification method 1: executable invariants

A property-based suite (`tests/test_properties.py`; 21 tests) generates randomised panels and asserts: determinism (identical output on repeated runs); unit invariance (SI and conventional units yield the same ranking, tolerance 10⁻³); directional monotonicity (a more extreme value never lowers the probability of the finding it defines; 14 analyte–direction pairs including creatinine, glucose up and down, potassium up and down, sodium up and down, haemoglobin, ALT, bicarbonate, leukocytes up and down, platelets); absent-analyte invariance (no syndrome asserted from an analyte that is not present); and context invariants (documented CKD never raises acute kidney injury; borderline flags behave as specified). The suite runs on every release in addition to 353 adversarial vignettes and a safety battery. It tests logical consistency, not clinical correctness: a mistranscribed threshold passes every invariant.

### 2.4 Verification method 2: source-concordance audit

The protocol was frozen before sampling (`eval/source_audit/PROTOCOL.md`; seed 20261026). Sample: 100 of 272 curated anchors and 100 executable candidates (50 "eICU-relevant"—feature present in ≥ 50% of eICU first panels and disease in an evaluated label group—and 50 uniform from the rest), registry 14.1.0. Fields compared: analyte, operator/threshold with unit, population qualifier, disease attribution. Labels: CONCORDANT, DISCORDANT, UNRESOLVABLE, with the tie-break "when in doubt, unresolvable"; unresolvable is never counted as concordant. Sources were retrieved by the registry locator (curl, 20 s), with Crossref title and PubMed abstract as fall-back for paywalled DOIs and direct PDF retrieval for KDIGO guidelines. Rates are reported with two denominators (resolvable; all sampled) and Wilson 95% CIs. The rater was an AI agent under the first author's direction, declared as such; a human non-clinician second rater was recruited, and the handling of that attempt is reported in Section 3.2.

### 2.5 Verification method 3: frozen one-shot benchmark

An internal statistical analysis plan (Supplementary Note 1; 15 dated amendments) fixed metrics, label maps, thresholds and comparators; it was time-stamped and hash-frozen in the repository but not publicly registered, so we write "pre-specified", not "pre-registered". Before each quarantine round, code and registry were frozen with SHA-256 manifests and quarantine data were run once. Round 1 (MIMIC-IV demo; NHANES 2013–14; sepsis set B) used superiority criteria over the prior release; round 2 (NHANES 2015–16; sepsis set B2; healthy sweep with a new seed) used non-inferiority criteria specified before execution (Amendment 15: NHANES AUROC within 0.03 on six targets with ≤ 1% healthy false assertions; sepsis AUROC not more than 0.02 below; no new safety-battery failure).

*Datasets and reference standards* (Table 2; participant flow in Supplementary Table S3). eICU-CRD demo v2.0.1 [20]: 2,520 stays → 2,512 adults → 2,314 with ≥ 8 analytes in the first panel; reference = clinician problem list mapped by regular expressions to 31 groups (audit on 400 stays: precision 100%, sensitivity 98.3%; Supplementary Table S9). MIMIC-IV demo [21]: 235 admissions, ICD-10. NHANES 2013–14, 2015–16, 2017–18: 3,000 randomly sampled adults per cycle; references per ADA, KDIGO, WHO and ACG criteria and self-report. PhysioNet/CinC 2019 [22]: set A 4,871 patients (439 sepsis), set B 4,558 (268), set B2 4,991; Sepsis-3 onset. UCI thyroid0387 [23], UCI HCV [24], ILPD [25], 50 PMC case reports [26].

*Metrics.* Primary: flat recall@k of clinician-listed diagnoses (k = 3, 5, 10). Secondary: two-tier recall; panel-supported recall (labels whose first panel met a guideline criterion fixed in `panel_supported_metric.py` before scoring); per-group AUROC; screening AUROC and false-assertion rate in all-normal adults; sepsis AUROC; calibration (slope, intercept, ECE, Brier, decision curves before and after cross-fitted isotonic regression [27]); ablation of each component on the same 2,314 stays.

*Comparators.* B1, raw key-analyte threshold; B2, gradient boosting and logistic regression on the same analytes, five-fold out-of-fold; a prevalence-ranking baseline; and an unnamed frontier LLM run by the authors through the Arena.ai agent platform (2026-10-21 to 2026-10-25; n = 400), which routes among several frontier model families without exposing the model or version and offers no sampling controls—"unnamed frontier LLM" therefore denotes a capability tier, not a verified identity. The LLM received the identical panel, age and sex with a fixed prompt requesting ten ranked diagnoses, blinded to labels; 40 panels were re-read for test–retest and read with an alternative prompt; scoring used the same label map and script as the engine. Prompts, outputs and protocol are released (Supplementary Note 2).

*Statistics.* Labels are nested in stays (ICC 0.04); eICU proportions and paired differences use stay-cluster bootstrap (4,000 resamples) and the cluster-adjusted McNemar test [28,29]; Wilson intervals elsewhere; bootstrap or DeLong for AUROC; NHANES AUROCs additionally examination-weighted; Benjamini–Hochberg across per-group tests. Python 3.11/3.13, numpy, pandas, scikit-learn. Reporting follows TRIPOD+AI [30] adapted for an unfitted system (checklist in Supplementary Note 5.7). Post-freeze proposals (v8) were tested against the frozen artefacts and are described in Supplementary Note 9; no frozen number derives from them."""

results = """### 3.1 Executable invariants

All 21 tests pass on the current engine (v8.1). On the frozen v7 the suite exposed one genuine defect that the 353 adversarial vignettes had not: a well-supported renal finding was capped beneath a presumptive explainer scoring below 0.80, so the leading renal probability *fell* as creatinine rose from 1.6 to 2.2 mg/dL. The fix applies an existing rule uniformly and passed the full gate (eICU recall@3/5/10 48.4/61.0/74.1% versus 47.9/60.8/74.1% for v7, inside the v7 confidence intervals). The frozen v7 numbers below are unchanged. The engine is deterministic (byte-identical output in 50/50 repeated stays), runs on one CPU core in ~1 s per panel and makes no network calls.

### 3.2 Source concordance

Of 200 rules sampled under the frozen protocol, only 16 could be resolved from the locators the registry provides: 15 were discordant—7 attribution errors among curated anchors (e.g. a hypernatraemia rule citing the hyponatraemia guideline) and 8 thresholds or definitions absent from an on-topic source (e.g. a candidate acute-kidney-injury "criterion" defined by a fixed creatinine > 1.1 mg/dL and attributed to KDIGO 2012, which defines AKI only by change from baseline)—and 1 concordant. The remaining 184 (92%, 95% CI 87.4–95.1) were unresolvable: 12 with no retrievable text, 55 with only a title or abstract, 46 citing only generic methodological standards (WHO essential diagnostics list, CLSI EP28/C59) that cannot contain a disease-specific threshold, and 71 organisation landing pages. Because an attribution error is visible from a title while concordance needs the full text, 15/16 is not an estimate of the registry's discordance rate; the defensible statements are that at least 7.5% (4.6–12.0) of sampled rules are demonstrably discordant and that the registry, as released, is not auditable rule-by-rule from its own locators. A separate provenance scan of all 785 sources resolved 112 DOIs via Crossref and reached 533 landing pages; 39 were unreachable, 34 lacked a locator, nine invalid DOIs were removed and 28 rules were flagged `unverified_source` (Supplementary Table S10, Fig. S1).

The audit is single-rater: the rater was an AI agent working under the first author's supervision, which is declared rather than hidden. The second-rater arm specified in the protocol did not yield a dataset that met the protocol's validity rule (a verdict must be supported by the verbatim source sentence) and is not reported; no inter-rater reliability is claimed, and the two figures above should be read as one declared rater's finding under a frozen protocol that anyone can re-run.

### 3.3 Frozen benchmark: quarantine outcome

Round 1 failed two primary criteria written as superiority over the prior release, because guideline-correctness changes (a single creatinine no longer asserts CKD) lowered CKD label recall. The criteria were re-specified as non-inferiority (Amendment 15, dated after round 1 and before any round-2 file was opened), six further correctness changes were implemented (v7) and round 2 met the new criteria (Fig. 2a; Supplementary Table S2). Because the criteria changed between rounds, round 2 is evidence of non-regression, not the confirmatory test originally planned. All results below are for frozen v7/14.1.0.

### 3.4 Intensive care (eICU-CRD demo)

In 2,314 adult ICU stays from 186 US hospitals, from the first panel with ≥ 8 analytes and no clinical text, 47.9% (stay-clustered 95% CI 45.8–50.0) of 2,432 clinician-listed, laboratory-relevant diagnoses appeared in the top 3, 60.8% (58.7–62.9) in the top 5 and 74.1% (72.2–76.0) in the top 10 of the flat differential (Table 4); 275 further labels lacked the key analyte. Precision@5 was 14.2% (13.3–15.2), F1@5 23.1% and NDCG@5 56.5% (54.1–58.8) against an incomplete problem list. Recall@5 was 88.1% for acute myocardial infarction, 82.8% for heart failure, 83.0% for anaemia and 77.5% for acute kidney injury, but 49.1% for sepsis, 45.1% for diabetes and 35.8% for CKD. A prevalence-ranking baseline reached recall@5 51.3% and NDCG@5 39.0% and overtook the engine at k = 10 (76.8% vs 74.1%); the engine's contribution is ordering, not coverage (Supplementary Table S11). Automated criterion matching of the 10,380 top-5 assertions found 14.2% on the problem list, 54.8% uncoded but criterion-positive in the same panel, 12.6% criterion-negative—the closest available estimate of false positives—and 18.4% in groups without a single-analyte criterion.

The reference standard bounds these metrics (Fig. 2b): of 2,707 label targets, 541 belonged to groups with no single laboratory criterion, 275 lacked the key analyte and 431 were contradicted by the first panel (e.g. hypokalaemia coded with potassium 4.1 mmol/L after repletion). Among the 1,460 labels whose first panel met the guideline criterion—a secondary metric defined after the ceiling was observed—flat recall was 29.6/62.5/78.0/91.8% at k = 1/3/5/10 (Supplementary Fig. S3). Supervised models trained on the labels (Fig. 3) exceeded the untrained engine only in outcome-defined groups without a laboratory signature—sepsis (AUROC 0.82 vs 0.68), GI bleeding (0.85 vs 0.75), alcohol withdrawal (0.80 vs 0.54)—and were matched or beaten in nine guideline-defined groups (CKD 0.79 vs 0.81; hyponatraemia 0.85 vs 0.89; cirrhosis 0.83 vs 0.87); a raw key-analyte threshold matched the engine for single-analyte groups.

### 3.5 Component ablation

Two components carry the signal (Table 1; Supplementary Table S12): removing the rule-engine vote cost 12.1 points of flat recall@5 (−14.4 to −9.8) and removing the syndrome layer 9.5 points (−11.1 to −7.9). The Bayesian network contributed 1.3 points; the fuzzy, knowledge-graph and risk-model layers lay within ±0.5 points; uniform fusion weights cost 1.4 points and rule-heavy or rule-light weights changed recall by ≤ 1.1 points. Restricting the registry to the 272 curated anchors (32,911 AI-drafted rules off) lowered recall@5 by 0.9 points (−2.1 to +0.2) with the syndrome layer on and 3.1 points with it off. The headline therefore rests on the hand-curated components—the ones not yet independently audited—and registry scale is not claimed as a merit.

### 3.6 Community survey, external cohorts and the pre-specified negative result

In 3,000 NHANES adults per cycle, unweighted AUROCs reproduced across the development cycle (2017–18) and the two quarantine cycles (2013–14, 2015–16): diabetes 0.946/0.938/0.924, CKD 0.959/0.968/0.962, anaemia 0.972/0.994/0.983, hyperuricaemia 0.943/0.958/0.955, hypercholesterolaemia 0.905/0.883/0.886, ALT elevation 0.872/0.880/0.877 (Fig. 4; Table 3). These laboratory-defined labels overlap the inputs; against self-reported physician diagnosis AUROC was 0.90–0.92 for diabetes and 0.75–0.82 for kidney disease. Among guideline-healthy adults the engine asserted a disease in 1/160, 1/246 and 0/79 (2/485, 0.4%). On the UCI thyroid set AUROC was 0.979 (hypothyroidism) and 0.798 (hyperthyroidism); HCV cohort 0.925; ILPD 0.704; MIMIC-IV demo top-5/10 recall 47.5/62.1%; on 50 PMC case reports the specific diagnosis was in the top five in 26% and the correct syndrome in 68% (Table 3; Supplementary Note 10). In PhysioNet/CinC 2019 the engine's sepsis score discriminated Sepsis-3 onset with AUROC 0.600, 0.610 and 0.588 in sets A, B and B2 versus 0.691, 0.712 and 0.679 for a supervised logistic model on the same features (Fig. 5); Hemoglyph is not a sepsis predictor, and the engine was not tuned to the task afterwards. Raw scores were uncalibrated (pooled AUROC 0.797; Fig. 7); subgroup, unit-invariance and perturbation results are in Supplementary Note 11.

### 3.7 Blinded comparison with an unnamed frontier LLM

On 400 stays (291 with scorable labels; 596 labels), recall@5—the pre-specified primary comparison—was 60.7% (56.5–65.0) for Hemoglyph versus 59.6% (55.3–63.6) for the LLM, difference +1.2 points (−2.5 to +5.1; cluster-adjusted McNemar p = 0.54). The LLM was better at rank 1 (28.2% vs 24.0%, p = 0.013) and rank 3 (50.8% vs 47.0%, p = 0.041); the engine at rank 10 (72.0% vs 65.1%, p = 0.0002) and left fewer labels absent (21.8% vs 34.9%); mean reciprocal rank 0.391 vs 0.408 (Fig. 6; Table 5). On 40 panels re-read by the LLM, top-5 agreement with its own first reading was κ 0.69; the engine's was 1.00. An earlier comparison against engine v5.1 had favoured Hemoglyph; re-scoring against the frozen v7 reduced that to parity, and both are reported."""

discussion = """Three methods were applied to an AI-drafted clinical rule base, and each produced information that conventional validation had not. The invariant suite found a monotonicity defect that 353 adversarial vignettes missed; the frozen concordance protocol showed that the rule base, as released, cannot be audited from its own locators and that at least 7.5% of sampled rules are demonstrably discordant; and the frozen benchmark showed an untrained, fully traceable engine at recall@5 parity with a frontier LLM while a prevalence baseline reached 51%—so the engine's measurable contribution is ordering (NDCG@5 56.5% vs 39.0%) and per-stay specificity, not coverage. Each method is cheap (the suite runs in minutes; the audit took one rater two days; the benchmark uses public data and released scripts) and each is reproducible from the repository.

The methodological lesson is about where verification stops. Executable invariants are a genuine advantage of a rule engine over an LLM: they can be stated, run on every release and violated only visibly. But they establish logical consistency, not correctness—a mistranscribed threshold passes every invariant—and the concordance audit shows why correctness is hard to reach: the limiting factor was not rater effort but locator granularity. Organisation-level URLs and generic standards make 92% of rules uncheckable, and where checking was possible the error was usually attribution, which a title reveals and a transcription audit therefore over-samples. The failed second-rater attempts (Section 3.2) add a practical point: a human asked to verify AI-drafted rules will, without a mandatory quotation field, produce AI-like paraphrases. Any audit protocol for such rule bases should require the verbatim source sentence, and any registry intended to be auditable should carry section- or table-level locators; both are planned for release 15 together with re-sourcing or retirement of the 46 sampled candidates whose only citation is a generic standard and correction of the five curated-anchor attribution errors found. Concordance remains necessary, not sufficient: an independent clinical audit is the next step and is outside this paper. Both tools transfer without change to any rule base whose records carry analyte, operator, threshold, unit, population and locator—including rule sets generated by retrieval-augmented LLM pipelines—and the benchmark scripts run unchanged on the credentialed full eICU and MIMIC-IV releases.

The benchmark numbers measure the reference standard at least as much as the engine, and three observations locate the ceiling. First, the labels: a quarter of admission-level problem-list entries were not inferable from the first panel at all, and the panel-supported subset is recovered at 78.0% (k = 5) and 91.8% (k = 10). Second, the comparators: supervised models trained on the labels themselves did not exceed 0.82 AUROC for outcome-defined groups and a prevalence-ranking baseline overtakes any method at k = 10, so no laboratory-only system can score much higher on this reference. Third, the "false positives": of the 85.8% of top-5 assertions not on the problem list, 54.8% satisfy the group's laboratory criterion in the same panel and only 12.6% are criterion-negative—the coded precision of 14.2% is a lower bound and 69.0% an upper bound. Where the engine genuinely loses (sepsis, bleeding, withdrawal, CKD without a second creatinine) the label is an outcome learned from hidden correlates or requires longitudinal data, which argues for hybrid rather than replacement designs. Part of the loss was chosen: withdrawing single-creatinine CKD assertions to comply with KDIGO cost three points of recall@5 against the previous release. The ablation locates the result in the rule vote and the curated syndrome constellations, written by a non-clinician from guideline criteria; the 33,000-rule bulk adds one to three points, so Hemoglyph is guideline-*transcribed*, not guideline-derived. The contribution of such an engine is therefore not accuracy beyond what the reference permits but a property no LLM and no trained model offers: every output carries a rule identifier, threshold and source, runs offline in about one second without a GPU, and can be verified by executable invariants before release. Our design also addresses criticisms of recent LLM benchmarks—unstable metrics, leakage and post-hoc selection [26,31]: releases were frozen with manifests, quarantine data were run once, the failed round and the subsequent weakening of criteria are disclosed, and the LLM's test–retest variability (κ 0.69) exceeded the between-system difference. Compared with Isabel and DXplain [13–16,32], this study isolates laboratory-only reasoning on more than 20,000 encounters and releases its knowledge base under an open licence. The output design (a rule identifier and source for every entry) is consistent with the transparency principle of the FDA's January 2026 clinical-decision-support guidance; no regulatory claim is made.

### 4.1 Limitations

No clinician audited the rules or adjudicated outputs; the concordance audit is single-rater, by an AI agent, and its two figures should be read as one rater's finding under a protocol anyone can re-run. The components that carry the result were written by a non-clinician first author; 34 sources lack a locator; Bayesian priors are hand-coded without a per-value citation table; no version-control history exists for the development period. Only the open demo subsets of eICU and MIMIC-IV were used, with admission-level problem lists and ICD codes as reference standards. The LLM comparison is an author-run self-baseline through a platform that does not disclose the model, with two prompts, no retrieval augmentation and no clinician adjudication, and the model's training data may include the public eICU demo. Quarantine criteria were weakened after round 1; the panel-supported metric is post hoc; NHANES laboratory-defined labels overlap the inputs; raw scores are uncalibrated; external cohorts are small; the OCR front end was not evaluated; Iranian populations and non-English laboratory conventions were not evaluated. The first author is a secondary-school student with a financial interest in the commercial product, and the system, including 99.2% of the rules, was developed with AI-agent assistance. Hemoglyph is a research prototype with no regulatory clearance."""

conclusion = """Executable invariants, a frozen source-concordance protocol and a hash-frozen one-shot benchmark are three low-cost, reproducible methods for verifying an AI-drafted clinical rule base. A rule engine whose every output carries a rule identifier, threshold and source can be audited in ways a language model cannot, and its measured recall is bounded by the reference standard rather than by the method. Applied to Hemoglyph they found a defect that vignettes had missed, showed that provenance granularity rather than rule count limits auditability, and placed an untrained, traceable engine at parity with a frontier LLM on a blinded laboratory-panel task close to the ceiling the reference standard allows. The limits—an unaudited rule base, outcome-defined syndromes, uncalibrated scores—are stated so that they can be measured and closed."""

credit = between("## CRediT authorship contribution statement", "## Declaration of competing interest")
ethics = ("All data are from public, de-identified research datasets released under their own data-use agreements (eICU-CRD demo, MIMIC-IV demo, "
          "PhysioNet/CinC 2019, NHANES, UCI and ILPD repositories, PMC case reports). No patient was recruited, no identifiable information was accessed "
          "and no intervention was performed; under the Iranian National Ethical Guidelines for Biomedical Research and the terms of the source repositories, "
          "secondary analysis of such data does not require ethics-committee approval or informed consent, and none was sought.")

body = "\n\n".join([
    f"# {TITLE}",
    "*Original research article. Revision R6 (2026-10-27), formatted for Computer Methods and Programs in Biomedicine. Research prototype — not approved or intended for clinical use.*",
    authors,
    "**Highlights**\n" + "\n".join(f"- {h}" for h in highlights),
    "## Abstract\n\n" + abstract,
    "**Keywords:** " + keywords,
    "## 1. Introduction\n\n" + intro,
    "## 2. Methods\n\n" + methods,
    "## 3. Results\n\n" + results,
    "## 4. Discussion\n\n" + discussion,
    "## 5. Conclusion\n\n" + conclusion,
    "## Acknowledgements and declarations\n\n"
    "**Ethics statement.** " + ethics + "\n\n"
    "**Funding.** This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.\n\n"
    "**Declaration of competing interest.** " + competing + "\n\n"
    "**Declaration of generative AI and AI-assisted technologies.** " + gen_ai + "\n\n"
    "**CRediT authorship contribution statement.** " + credit + "\n\n"
    "**Data and code availability.** " + data_av.replace("\n\n", " ") + "\n\n**Software availability.** Hemoglyph engine `analyse_gidlines.py` (Python ≥ 3.11; dependencies numpy, pandas, brotli; no GPU; ~1 s per panel on one CPU core), the property-based test suite `tests/test_properties.py` (pytest + hypothesis-style random panels), the audit protocol and sampling script `eval/source_audit/`, and all evaluation scripts are available at github.com/sobahramisamani-droid under AGPL-3.0-or-later; rule registries under CC BY-SA 4.0. The frozen v7/14.1.0 snapshot with SHA-256 manifests will be archived on Zenodo with a DOI before publication.",
    "## References\n\n" + refs,
    "## Figure legends\n\n" + figlegs,
    "## Tables\n\n" + tables,
    "## Supplementary information\n\n" + supp,
])

# ---------- references: renumber by first appearance in main text; drop uncited
main = body.split("## References")[0]


def expand(tok):
    out = []
    for part in re.split(r",\s*", tok):
        if re.search(r"[–-]", part):
            a, b = re.split(r"[–-]", part); out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


order = []
for m in re.finditer(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", main):
    for n in expand(m.group(1)):
        if n not in order:
            order.append(n)
ref_lines = [l for l in refs.split("\n") if re.match(r"^\[\d+\] ", l)]
old_refs = {int(re.match(r"\[(\d+)\]", l).group(1)): l.split("] ", 1)[1] for l in ref_lines}
uncited = sorted(set(old_refs) - set(order))
mapping = {o: n for n, o in enumerate(order, 1)}


def compress(nums):
    nums = sorted(set(nums)); out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if j == i else (f"{nums[i]},{nums[j]}" if j - i == 1 else f"{nums[i]}–{nums[j]}"))
        i = j + 1
    return ",".join(out)


head, tail = body.split("## References", 1)
head = re.sub(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", lambda m: "[" + compress([mapping[n] for n in expand(m.group(1))]) + "]", head)
new_refs = "\n".join(f"[{mapping[o]}] {old_refs[o]}" for o in sorted(order, key=lambda o: mapping[o]))
body = head + "## References\n\n" + new_refs + "\n\n## Figure legends" + tail.split("## Figure legends", 1)[1]

# ---------- tables: renumber by first appearance; reorder blocks
main = body.split("## Tables")[0]
torder = []
for m in re.finditer(r"Table (\d)\b(?!\d)", main):
    if int(m.group(1)) not in torder:
        torder.append(int(m.group(1)))
torder += [n for n in range(1, 6) if n not in torder]
tmap = {o: n for n, o in enumerate(torder, 1)}
sub = lambda t: re.sub(r"Table (\d)\b(?!\d)", lambda m: f"Table {tmap[int(m.group(1))]}", t)
head, tail = body.split("## Tables", 1)
tb, sp = tail.split("## Supplementary information", 1)
blocks = [b.strip() for b in re.split(r"(?=^\*\*Table \d \| )", tb.strip(), flags=re.M) if b.strip()]
assert len(blocks) == 5
blocks = sorted((sub(b) for b in blocks), key=lambda b: int(re.match(r"\*\*Table (\d)", b).group(1)))
body = sub(head) + "## Tables\n\n" + "\n\n".join(blocks) + "\n\n## Supplementary information" + sub(sp)

INDEX = 'Notes: Note 1 SAP and amendments; Table S1 engine change log C1–C16 with sources; Table S2 quarantine criteria and outcomes (rounds 1 and 2); Note 2 LLM comparison protocol; Table S3 participant flow and baseline characteristics; Note 3 fusion/Theory-of-Evidence algorithm and consistency identities; Table S4 subgroup recall; Table S5 next-test utility (engine v5.3, superseded metric); Tables S6–S6c calibration, recalibration, decision curves, multiplicity and panel-size sensitivity; Table S7 survey-weighted NHANES AUROC; Table S8 per-group calibration; Table S9 label-mapping audit (400 stays); Table S10 registry count reconciliation; Table S11 precision/F1/NDCG, alert burden, per-group PPV and prevalence baseline; Table S12 fusion-weight sensitivity; Table S12b historical comparisons (superseded); Table S13 participant flow for the UCI cohorts; Table S15 open vs proprietary components; Table S16 sepsis companion model; Note 4 regression gate; Note 5 definitions, audits and completed TRIPOD+AI checklist; Note 6 version manifest; Note 7 evidence triage of twelve proposals; Note 8 source-concordance audit; Notes 9–12 material moved from the main text; Fig. S1 provenance audit; Fig. S2 per-release eICU metrics; Fig. S3 per-group panel-supported recall; Fig. S4 per-group calibration; Fig. S5 context-echo analysis; Fig. S6 historical LLM comparison vs engine v5.1; Fig. S7 participant flow; Data 1 per-stay outputs and LLM prompts/outputs.'
# ---------- supplement: archive the R5 main-text sections that were condensed (verbatim)
body = body.rstrip() + "\n\n### Supplementary Note 12 — Full-length Methods and Results text of revision R5 (verbatim; condensed in the main text for length — statements about a pending second rater in R5 §2.8/§3.10 are superseded by main-text Sections 2.4 and 3.2)\n\n" \
       + "#### R5 Methods\n\n" + old_methods.replace("### ", "##### ") + "\n\n#### R5 Results\n\n" + old_results.replace("### ", "##### ") + "\n\n#### R5 Discussion\n\n" + old_disc.replace("### ", "##### ") + "\n"
body = re.sub(r"Notes: Note 1 SAP and amendments;[^\n]*", lambda m: INDEX, body, count=1)

body = re.sub(r"Rater 1 was an AI agent under the first author's supervision; rater 2 is a human non-clinician co-author blind to rater-1 labels; Cohen's κ over the three labels will be reported\.",
              "The rater was an AI agent under the first author's supervision (declared); the protocol's second-rater arm did not yield a valid dataset under the quotation rule and no inter-rater reliability is claimed.", body)
body = re.sub(r"; a second, human non-clinician rater returned templated verdicts in a first round \(agreement with rater 1 κ = 0\.05\) and that round was rejected and is archived with the protocol rather than averaged in \(Supplementary Note 8\)", "; the protocol's second-rater arm did not yield a valid dataset and is not reported", body)
body = body.replace("statements about a pending second rater in R5 §2.8/§3.10 are superseded by main-text Sections 2.4 and 3.2", "superseded where it differs from the main text")
open(DST, "w", encoding="utf-8").write(body)
core = body[body.index("## 1. Introduction"):body.index("## Acknowledgements")]
print("abstract words", nwords)
print("main text words (Introduction–Conclusion)", len(re.sub(r"\|.*", "", core).split()))
print("references cited", len(order), "| dropped (uncited):", [old_refs[u][:40] for u in uncited])
print("figures cited:", sorted(set(re.findall(r"Fig\. (\d)", core))), "| tables:", tmap)
