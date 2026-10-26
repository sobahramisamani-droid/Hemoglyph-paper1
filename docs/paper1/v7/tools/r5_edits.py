"""Round-5 review edits, npj manuscript. Each replacement must match exactly once."""
import pathlib, re
P = pathlib.Path("/home/user/Hemoglyph/docs/paper1/v7/Paper1_Hemoglyph_npj_EN_v7_R1.md")
t = P.read_text(encoding="utf-8")

NEW_ABSTRACT = ("Laboratory interpretation remains largely manual; large language models (LLMs) interpret panels fluently but neither reproducibly nor locally. "
"Hemoglyph is a research-prototype offline engine that ranks a cited differential from a structured laboratory panel using 33,183 executable rules transcribed from guidelines—99.2% drafted with AI assistance by a non-clinician author and not yet audited by clinicians—without outcome training. "
"All results concern structured analyte–value pairs; the optical-character-recognition front end was not evaluated. "
"Under an internal, hash-frozen analysis plan (not publicly registered) with two one-shot quarantine rounds—the first failed its superiority criteria and the criteria were then changed to non-inferiority, so the second round is supportive, not confirmatory—we evaluated the frozen engine retrospectively on the public eICU demo (2,314 ICU stays), MIMIC-IV demo, 9,000 NHANES adults, 14,420 sepsis patients and external cohorts. "
"From laboratory values alone, 60.8% (95% CI clustered by stay 58.7–62.9) of clinician-listed ICU diagnoses appeared in the top-5 at precision@5 of 14.2% against an incomplete problem list; a prevalence-ranking baseline reached 51.3% at k = 5 and overtook the engine at k = 10, so the engine's contribution is ordering (NDCG@5 56.5% vs 39.0%), not coverage. "
"Screening AUROCs reproduced across three NHANES cycles (0.88–0.99 for six laboratory-defined targets; 0.87–0.88 for ALT elevation) with 2 false assertions among 485 guideline-healthy adults. "
"Blinded on identical inputs, the engine and an unnamed frontier LLM accessed through an agent platform were at parity on recall@5 (60.7% vs 59.6%, p = 0.54); the LLM led at rank 1, omitted more labels (34.9% vs 21.8%) and agreed with itself on 85.7% of labels on re-reading (κ 0.69), whereas the engine is deterministic. "
"Sepsis AUROC was 0.60 (pre-specified negative result; guideline SIRS/qSOFA rules added afterwards were validated once on a held-out set). "
"Ablation located the result in the 272 hand-curated anchor rules and the syndrome layer—the components not yet independently audited—with the AI-drafted bulk adding 0.9 points (3.1 without the syndrome layer); guideline-correctness fixes cost three recall points relative to the product release. "
"Iranian populations were not evaluated. Code and rules are public (GitHub; Zenodo DOI before publication) for audit.")

E = [
 # title
 ("# An untrained, auditable, locally run, AI-drafted guideline-sourced rule engine for structured laboratory-panel interpretation: pre-specified multi-dataset evaluation with one-shot quarantine, component ablation and a blinded comparison against a GPT-4-class language model",
  "# An untrained, auditable, locally run, AI-drafted guideline-sourced rule engine for structured laboratory-panel interpretation: pre-specified evaluation on public datasets (eICU and MIMIC-IV demo subsets, NHANES, PhysioNet) with frozen quarantine rounds, component ablation and a blinded comparison against an unnamed frontier language model"),
 # intro: lab-only as design choice + novelty search summary
 ("and we are not aware of an openly licensed, executable rule set specific to laboratory-panel interpretation.",
  "and a dated search (2026-10-24) of AHRQ CDS Connect, ECRI Guidelines Trust, NICE, WHO SMART guideline kits, OpenCDS/Arden collections and PubMed found no openly licensed, machine-executable rule set specific to laboratory-panel interpretation (method in Supplementary Note 5). We restrict the engine and its evaluation to structured laboratory values by design: it isolates what can be inferred from the panel itself, the one input every laboratory report shares, and avoids measuring the transcription of a diagnosis already written in the history."),
 # pre-specified sentence (fix glob damage)
 ("we therefore use 'pre-specified', not 'pre-specified', throughout.", "we therefore write 'pre-specified', not 'pre-registered', throughout."),
 # sepsis results: SIRS/qSOFA post hoc + logistic numbers already there
 ("Hemoglyph is not a sepsis predictor.",
  "Guideline-sourced SIRS/qSOFA syndrome rules were added under Amendment 15 **after** the pre-specified negative result on sets A and B, developed on set A and validated once on B2, where they added about 0.04 AUROC; this is a post-hoc addition and is labelled as such. Hemoglyph is not a sepsis predictor."),
 # LLM naming in results
 ("a general-purpose GPT-4-class LLM received the identical panel", "an unnamed frontier LLM (accessed through an agent platform that does not disclose the model; see Methods) received the identical panel"),
 ("Both flagged 39/39 CAP critical values in 50 stays (thresholds listed in Supplementary Note 5).",
  "Both flagged 39/39 CAP critical values in 50 stays (Wilson 95% CI 91–100%; thresholds in Supplementary Note 5)—a shared safety floor, not a discriminating comparison."),
 ("**Table 4 | Blinded comparison with a GPT-4-class LLM, 400 eICU stays, 596 labels.**",
  "**Table 4 | Blinded comparison with an unnamed frontier LLM (agent platform, model not disclosed), 400 eICU stays, 596 labels.** The historical v5.1 comparison from the first submission is in Supplementary Figure S (superseded)."),
 ("| critical values flagged (50 stays) | 39/39 | 39/39 | | |",
  "| critical values flagged (50 stays; shared safety floor, non-discriminating) | 39/39 (91–100%) | 39/39 (91–100%) | | |"),
 # Table 2: remove historical row; calibrated footnote
 ("| registry off (ablation, v5.3 engine) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |\n", ""),
 ("The last row is a historical ablation performed on engine v5.3 before the registry revisions and is kept only for continuity with the first submission; the ablations that belong to the evaluated release are those of Table 5.",
  "The historical registry-off ablation on engine v5.3 (first submission) is moved to Supplementary Table S12b; the ablations that belong to the evaluated release are those of Table 5. All scores in this table are rank-based and uncalibrated; after cross-fitted isotonic recalibration within eICU the pooled ECE fell from 0.162 to 0.003 and the Brier score from 0.117 to 0.040 without changing any rank, so recall values are unaffected. The shipped product displays ranks and evidence states, not probabilities, and applies no calibration map."),
 # Discussion first paragraph numbers + stale ranges
 ("(0.89–0.99 for six targets; lower, 0.71–0.88, for ALT elevation)", "(0.88–0.99 for six targets; 0.87–0.88 for ALT elevation)"),
 ("the frozen engine and a GPT-4-class model were statistically indistinguishable on the pre-specified metric, with the LLM stronger at rank 1 and the engine at coverage;",
  "the frozen engine and an unnamed frontier LLM were statistically indistinguishable on the pre-specified metric (60.7% vs 59.6%), with the LLM stronger at rank 1 (28.2% vs 24.0%) and the engine at coverage (recall@10 72.0% vs 65.1%; labels absent from the list 21.8% vs 34.9%);"),
 ("Third, the LLM was better at rank 1 and worse at coverage; the two systems make different errors, which is itself a reason to study them together rather than to declare a winner.",
  "Third, the LLM was better at rank 1 (28.2% vs 24.0%) and worse at coverage (recall@10 65.1% vs 72.0%; it omitted 34.9% of labels against 21.8%), and its self-agreement on re-reading was only moderate (κ = 0.69, recall@5 varying by ±5 points—more than the engine–LLM difference). Per group (Fig. 6) the differences are small where a single analyte defines the label (renal impairment 83% LLM vs 81% engine; acute kidney injury 76% vs 80%; sepsis 45% vs 42%) and large where a multi-analyte pattern must be assembled or where the LLM prefers a broader term: the engine led for gastrointestinal bleeding (84% vs 50%), diabetes (50% vs 37%) and hypokalaemia (59% vs 41%), the LLM for metabolic acidosis (79% vs 50%), hyperkalaemia (90% vs 70%) and DKA (83% vs 73%), where the engine's covering-diagnosis suppression demotes the finding once a cause is named. The two systems make different errors, which is itself a reason to study them together rather than to declare a winner."),
 ("We therefore describe Hemoglyph as a guideline-*derived* engine: its knowledge was transcribed from guidelines by one non-clinician author with AI assistance,",
  "We therefore describe Hemoglyph as a guideline-*transcribed* engine rather than a guideline-derived one: its knowledge was transcribed from guidelines by one non-clinician author with AI assistance,"),
 # expert floor discussion
 ("the Bayesian, fuzzy, knowledge-graph and risk-model layers were, on this cohort, close to inert.",
  "the Bayesian, fuzzy, knowledge-graph and risk-model layers were, on this cohort, close to inert. Part of that inertness is by construction: the expert floor (fused score ≥ 0.90 × rule vote) means the rule layer can be modulated but not vetoed, a deliberate bias towards explicit guideline criteria that trades the possibility of a learned layer correcting a wrong rule for the guarantee that every surfaced diagnosis is traceable to one; the sensitivity analysis (Table 5, uniform and rule-light weights within 1.4 points) shows the result does not depend on the exact weights, but it cannot show what a design without the floor would do."),
 # methods: LLM
 ("LLM: a general-purpose GPT-4-class model run by the authors through a chat interface",
  "LLM: an unnamed frontier model run by the authors through a chat interface"),
 # methods: engine — define executable, priors, weights
 ("a rule layer over registry 14.1.0 (33,183 executable leaves—",
  "a rule layer over registry 14.1.0 (33,183 executable leaves, where a leaf is one registry record with a machine-evaluable condition on at least one analyte, a disease identifier and an `executable: true` flag—retired, template and empty-expression records are kept for provenance but never evaluated—"),
 ("fixed-weight fusion with an expert floor (the fused score of a diagnosis cannot fall below 0.90 × the rule-layer vote, so that the four learned-style layers can modulate but never veto a guideline rule);",
  "fixed-weight fusion (weights 0.35 rule engine, 0.25 Bayesian, 0.20 fuzzy, 0.10 knowledge graph, 0.10 risk models, set by the first author as a judgement that explicit criteria should dominate, with four context profiles, e.g. toxicology 0.55 for rules; no weight was derived from or tuned on any evaluation dataset, and Table 5 reports the sensitivity to them) with an expert floor (the fused score of a diagnosis cannot fall below 0.90 × the rule-layer vote, so that the four other layers can modulate but never veto a guideline rule). The Bayesian layer uses hand-coded prevalence priors for 315 diseases (constants or age bands, e.g. type 2 diabetes 0.08, CKD 0.10) and hand-coded likelihood ratios for 239 diseases taken from cited diagnostic-accuracy literature (e.g. lipase ≥ 3 × ULN, LR+ 18 for acute pancreatitis); none is estimated from data, so the engine remains untrained in the sense that no parameter was fitted to any patient record;"),
 # methods: AI assistance precise
 ("Rules were drafted from guideline text (KDIGO, ADA, WHO, ACC/AHA, EASL, ATA, ESC, CLSI, Tietz) with AI assistance, converted to executable form and filtered by automated audits (duplicates, contradictions, out-of-range thresholds, unit mismatch, missing context gates).",
  "'AI assistance' means the following. For each guideline source the first author prompted a general-purpose LLM with the source text or citation and a fixed JSON schema; the model returned candidate rule records (analyte, operator, threshold, unit, population gate, evidence role, disease identifier, source locator). These records were not individually edited by a human: they were accepted or rejected by automated audits (schema validity, analyte exists in the 2,045-analyte feature registry, unit convertible, threshold within physiological range, no duplicate or contradictory record, context gate present where the guideline requires one, source locator resolvable) and carry the status `candidate_requires_specialist_validation`. The 272 anchor rules were written or line-edited by hand by the first author from the primary guideline text and carry higher weight; the 13 demoted anchors and all rules retired between releases were removed by rule-level review of defect reports, not by outcome data. No record of the proportion of candidate rules that a human read exists, and we therefore describe the bulk as AI-drafted and automatically audited, not human-reviewed. Sources: KDIGO, ADA, WHO, ACC/AHA, EASL, ATA, ESC, CLSI, Tietz and others listed in the registry."),
 # methods: datasets — concurrent clarification; safety battery summary
 ("Sepsis-3 onset label; concurrent analysis 247 cases/600 dwell-time-matched controls.",
  "Sepsis-3 onset label; the post-hoc concurrent analysis (labs and vitals within ±6 h of onset) used 247 cases and 600 dwell-time-matched controls drawn from set B2 only, which is why Table 3 reports it for B2 alone."),
 ("The release passed the non-regression gate (defined in Supplementary Note 4:",
  "The release passed the non-regression gate (safety batteries = 353 adversarial vignettes with an expected diagnosis and maximum rank, 755 perturbation pairs that must keep the expected rank under 3% analyte noise and unit twins, and 1,000 synthetic guideline-normal panels that must yield no disease; defined in Supplementary Note 4:"),
 # healthy definition limitation + synthetic separation
 ("the engine asserted a disease in 1/160, 1/246 and 0/79 (2/485, 0.4%; and in 0/1,000 synthetic healthy panels).",
  "the engine asserted a disease in 1/160, 1/246 and 0/79 (2/485, 0.4%). The filter covers 30 analytes, so a false assertion driven by an analyte outside it (e.g. a mildly abnormal result in an unfiltered analyte) is counted as a true finding rather than an error; the figure is therefore a lower bound on false assertions. Separately, 0/1,000 synthetic guideline-normal panels produced a disease; these are generated, not real, and are reported as a regression check, not as evidence."),
 # fairness bounded
 ("The engine contains no race or ethnicity term:",
  "Three ethnicity strata in one US ICU dataset do not support a fairness claim; what can be said is narrower. The engine contains no race or ethnicity term:"),
 # Limitations additions
 ("The knowledge base has not been audited rule-by-rule by clinicians; 34 sources lack a locator.",
  "The knowledge base has not been audited rule-by-rule by clinicians; the components that carry the result—272 anchor rules and ~900 syndrome constellations—were written by a non-clinician first author and have not been independently audited; 34 sources lack a locator. The Bayesian priors and likelihood ratios are hand-coded from literature without a per-value citation table. No version-control history exists for the development period, so the claim that no change was outcome-fitted rests on the dated change log alone."),
 ("The first author is a secondary-school student and the system, including 99.2% of the rules, was developed with AI-agent assistance, declared below.",
  "The first author is a secondary-school student with a financial interest in the commercial product, and the system, including 99.2% of the rules, was developed with AI-agent assistance, declared below. Only demo subsets of eICU and MIMIC-IV were used; the external cohorts are small and ILPD discrimination was modest (0.704)."),
 # conclusion
 ("and was indistinguishable from a frontier LLM on a blinded paired primary metric, while remaining auditable. Its limits—outcome-defined syndromes, uncalibrated scores and an unaudited AI-drafted rule base—are stated so that t",
  "and was indistinguishable from an unnamed frontier LLM on a blinded paired primary metric, while remaining auditable. The components that carry the result are exactly those an independent clinical audit has not yet examined, and the LLM arm is not reproducible against a named model. Its limits—outcome-defined syndromes, uncalibrated scores and an unaudited AI-drafted rule base—are stated so that t"),
 # open vs proprietary pointer in Results system paragraph
 ("The desktop product around it is proprietary and node-locked;",
  "What is open and what is proprietary is tabulated in Supplementary Table S15 (engine source, registries, evaluation code and frozen outputs open; desktop shell, licensing and OCR path proprietary; only the open components were evaluated). The desktop product around it is proprietary and node-locked;"),
]
for a, b in E:
    c = t.count(a); assert c == 1, (c, a[:80])
    t = t.replace(a, b)
# abstract
lines = t.split("\n"); assert lines[11].startswith("Laboratory interpretation remains largely manual"), lines[11][:60]
lines[11] = NEW_ABSTRACT; t = "\n".join(lines)
# remove historical row from Table 4
t2 = re.sub(r"\| historical: engine v5\.1 \(first submission[^\n]*\n", "", t); assert t2 != t; t = t2
# global GPT-4-class residuals
t = t.replace("Mature diagnostic decision-support systems (Isabel, DXplain) have recently been compared with GPT-4-class models", "Mature diagnostic decision-support systems (Isabel, DXplain) have recently been compared with GPT-4 and successor models")
t = t.replace("GPT-4-class", "unnamed frontier LLM")
P.write_text(t, encoding="utf-8")
print("npj r5 ok; abstract words", len(NEW_ABSTRACT.split()))
