# Hemoglyph: A Knowledge-Driven Hybrid Reasoning System for Interpreting Blood Test Reports — Design and Pre-Registered Multi-Dataset Evaluation with One-Shot Quarantine and a Blinded Comparison Against a GPT-4-Class Language Model

Sobhan Bahrami,^1^ Zhaleh Tahmasebinejad^2^ and Ehsan Bahrami Samani^3^

^1^ Allameh Helli 10 High School, National Organization for Development of Exceptional Talents (NODET), Tehran, Iran. ORCID 0009-0004-6639-5081.
^2^ Endocrine Research Center, Shahid Beheshti University of Medical Sciences, Tehran, Iran.
^3^ Faculty of Mathematical Sciences, Shahid Beheshti University, Tehran, Iran.

Corresponding author: Sobhan Bahrami (sobahramisamani@gmail.com)

## Abstract

Clinical decision support systems (CDSS) for laboratory medicine must reason under conflicting and incomplete evidence, remain explainable, and—increasingly—operate without transmitting patient data to external services. We present Hemoglyph, a desktop-based, fully offline CDSS that couples a multi-backend OCR layer with a mathematical consistency solver and a five-layer cross-reasoning engine (deterministic guideline rules, a clustered Bayesian network, adaptive fuzzy logic, a clinical knowledge graph and 100 published risk models), fused by a fixed weighted ensemble and a constrained Theory of Evidence (ToE) layer. The ToE layer uses a binary frame per disease, Yager's combination rule so that conflict is assigned to ignorance rather than to competing hypotheses, an explicit abstention state, and a calibrated point score for ranking with belief and plausibility reserved for evidence status. A curated expert syndrome layer and a causal-attribution step (engine v7) enforce guideline semantics such as KDIGO chronicity and the universal definition of myocardial infarction. The knowledge base comprises 2,045 analytes, 6,750 clinical entities and 33,183 executable rules from 785 cited sources; 272 rules are manually curated guideline anchors and 32,901 are AI-assisted and flagged as requiring specialist validation. Under a pre-registered statistical analysis plan with cryptographic freezes and two one-shot quarantine rounds (the first of which failed its superiority criteria and is reported), we evaluated the frozen engine on 2,314 ICU stays (eICU-CRD), 9,000 adults across three independent NHANES cycles, 14,420 patients of the PhysioNet/CinC 2019 sepsis challenge, the MIMIC-IV demo, and external thyroid, hepatitis C, liver and case-report cohorts. From laboratory values alone, 60.8% of clinician-listed ICU diagnoses appeared in the top-5 differential (74.1% top-10), and 78.0% / 91.8% of the 1,460 diagnoses that the first panel could actually support. Screening AUROCs of 0.92–0.99 reproduced across NHANES cycles with at most one false assertion among healthy adults. In a blinded, paired comparison on 400 stays with identical inputs, Hemoglyph listed 64.4% of diagnoses versus 59.6% for a GPT-4-class language model (McNemar p = 0.009) while being deterministic. The engine did not predict Sepsis-3 onset (AUROC 0.59–0.64, below a supervised logistic model), and raw scores required recalibration. Code, rules and evaluation scripts are released under open licences.

Keywords: clinical decision support system; laboratory medicine; Theory of Evidence; Yager combination rule; abstention; knowledge-based reasoning; pre-registration; large language models; explainability.

## 1. Introduction

With the expansion of artificial intelligence in medicine, clinical decision support systems have become one of its most prominent applications. These systems serve as advisors to physicians and researchers, facilitating more accurate and safer decisions in the identification of disease. By integrating clinical and laboratory data they are used for diagnosis, screening, treatment adjustment, prescribing, monitoring, alerting on critical values and drug interactions, and reminding clinicians of guideline recommendations; they also reduce medical error (Sutton et al., 2020).

Clinical decision support was introduced by Ledley and Lusted (1959), who applied symbolic logic and probability to the diagnosis of heart disease. Dambro (1972) developed a CDSS for acute abdominal pain that marked the first application of the simple Bayesian rule to generate diagnoses, and in 1974 the CASNET system employed if–then rules to guide antibiotic selection. These systems relied on explicit knowledge bases and rule-based reasoning but could not distinguish absence of evidence from conflicting evidence and behaved unpredictably under uncertainty. To address the requirement of earlier methods for a single, definitive probability, Dempster (1967) introduced upper and lower probabilities, in which each hypothesis is represented by an interval whose width expresses ignorance; Shafer (1976) formalised this into the Dempster–Shafer theory of evidence (DST). Because Dempster's rule normalises conflict away and may place excessive confidence in a single hypothesis, Yager (1987) proposed assigning the conflicting mass to ignorance so that no decision is forced when the evidence disagrees.

Recent work has revisited hybrid knowledge-based designs. Maqsood et al. (2024) combined machine-learning classifiers with a rule-based knowledge base; Damkliang et al. (2025) used Bayesian updating for iron-deficiency anaemia and thalassaemia screening; Ashworth et al. (2025) proposed an architecture that translates guidelines into a version-controlled knowledge base and uses a large language model (LLM) only for explanation; Nambison et al. (2024) built a fuzzy system interpreting pathology reports for 17 diseases; and LeukoAlert (2026) derived 72 complete-blood-count features for opportunistic leukaemia screening. In parallel, LLMs have been shown to interpret laboratory reports fluently but not reproducibly, to misclassify values as high or low even when reference ranges are supplied, and to fabricate references (Cadamuro et al., 2023; Kurstjens et al., 2024; Hager et al., 2024). Mature diagnostic generators such as Isabel and DXplain have recently been compared with GPT-4-class models and found within a few points on recall while being reproducible (Bridges, 2024, 2025; MGB, 2025; Bond et al., 2012); none of these studies isolated laboratory-only reasoning, and none was pre-registered. Meanwhile the public infrastructure for executable guideline knowledge has contracted: the AHRQ CDS Connect repository went offline in 2025 and no open, executable rule set for laboratory interpretation exists.

A review of the literature therefore indicates that although individual studies address specific aspects of laboratory-report interpretation—OCR, single-disease classification, evidence combination, or LLM explanation—none provides a comprehensive, integrated and independently evaluated solution. In this paper we present Hemoglyph, a framework that combines multiple OCR back-ends and a consistency solver with a five-layer cross-reasoning engine and a constrained Theory-of-Evidence fusion, and—unlike our earlier description of the system—we report a pre-registered, multi-dataset evaluation of the frozen engine, including a quarantine round that failed, a pre-registered negative result, and a blinded comparison with a frontier LLM on identical inputs. The contributions are: (i) an architecture in which every output is traceable to a cited rule and in which conflict is handled by Yager-type combination with explicit abstention; (ii) a quantified account of the ceiling imposed by the reference standard in real ICU data; (iii) evidence that an untrained knowledge-based engine matches supervised models wherever a guideline definition exists and matches or exceeds a GPT-4-class LLM on laboratory-only inputs; and (iv) full disclosure of the provenance of an AI-assisted knowledge base and of the limits of the evidence.

The paper is organised as follows. Section 2 describes the Hemoglyph system. Section 3 describes the evaluation methodology, including pre-registration, freezes and quarantine. Section 4 reports results. Section 5 discusses principal findings, comparison with prior work, clinical implications, the changes made since the earlier version of the system, and limitations.

## 2. The Hemoglyph System

Hemoglyph is an intelligent medical assistant supported by a robust analytical infrastructure. By ingesting images of blood-test reports through multiple OCR back-ends, it extracts the laboratory parameters; it then performs an integrated analysis by simultaneously applying 33,183 executable rules drawn from 785 cited guideline sources, together with statistical, fuzzy and graph-based reasoning and 100 published risk scores, to rank candidate diagnoses and provide evidence-based, explainable outputs. Fig. 1 shows the core components: (1) a modular native architecture (Python 3.11, PySide6/QML, compiled with Nuitka); (2) a structured knowledge base (2,045 analytes with 85,828 aliases, 6,750 clinical entities, 33,183 executable rules); (3) a hybrid OCR layer producing JSON output validated by a consistency solver with 27 physiological constraints; (4) a five-layer cross-inference engine with fixed weighted fusion; (5) a constrained Theory-of-Evidence layer (binary frames, Yager's rule, abstention, calibrated scoring); and (6) an expert syndrome layer with causal attribution and guideline-semantics guards (engine v7).

Fig. 1. Core components of the Hemoglyph system.

### 2.1 Architecture and modules

The application is composed of independent modules: image extraction and pre-processing (`ocr.py`, `_ocr_support.py`); a consistency solver (`ocr_consistency.py`); an extraction-confidence model (`ocr_confidence.py`); the guideline-analysis and inference engine (`analyse_gidlines.py`), which hosts the rule engine, Bayesian network, fuzzy engine, knowledge graph, fusion, ToE and expert syndrome layers; a 100-model risk predictor (`prdicter.py`); unit conversion (`calcu.py`); and licence management and registry integrity (`license_engine.py`, `cache_registry.py`). The system runs entirely on the local CPU in about one second per panel, performs no network calls and transmits no medical data. The optional local chat assistant is disabled in the evaluated release (1.3.1); all inference reported here is produced by the deterministic engine.

### 2.2 Structured knowledge base

The knowledge base performs inference independently of any language model, relying exclusively on structured data and deterministic rules. Two Brotli-compressed JSON registries hold (a) a feature registry of 2,045 analytes with LOINC codes, UCUM canonical units, English and Persian synonyms (85,828 aliases) and age-, sex- and pregnancy-specific reference intervals; and (b) a disease–guideline registry (version 14.1.0) of 6,750 clinical entities—diseases, laboratory findings and biomarker patterns—linked to 34,673 rule records and 785 cited sources (society guidelines such as KDIGO, ADA, ATA, AASLD/EASL, ACC/AHA, ESC, ACR and CLSI, and standard texts). Rules are declarative (analyte, operator, threshold, unit, population, evidence role and weight, source) and are organised in four layers: screening (10,979), diagnostic criterion (6,140), exclusion criterion (6,220) and staging/severity (9,844). A code-level curation layer rejects malformed rules at load time.

The registries were drafted with the assistance of a large language model and curated by the first author through automated audits; they have not been reviewed by an independent expert panel (see Limitations). Fig. 2 shows the curation flow. Of 34,673 rule records, 1,474 were retired across releases 13.3–14.1 (superseded, domain artefacts or template artefacts), leaving 33,183 executable rules. Of these, 272 (0.8%) are manually curated guideline anchors and 32,901 (99.2%) carry the status `candidate_requires_specialist_validation`, which the engine exposes in every output so that the origin of knowledge is transparent. A provenance audit of the 781 sources in release 13.4.1 resolved 112 DOIs via Crossref, reached 533 landing pages, found 63 URL-only and 34 locator-less sources, and 39 that were unreachable from our environment (publisher sites that block automated access; unreachable is not fabricated); nine invalid DOIs were removed and 28 rules were flagged `unverified_source`.

Fig. 2. Curation and inclusion of clinical rules in the Hemoglyph knowledge base (release 14.1.0).

### 2.3 Extraction layer (OCR) and consistency solver

The extraction layer uses a hybrid method to reduce reading error. In the local pipeline, images are pre-processed before being passed to Tesseract, and an error analyser based on fuzzy matching and the alias registry corrects the extracted values. In the structured pipeline, a multimodal model produces JSON output (name, value, unit, reference range) and downstream inference is strictly limited to this structured data. To prevent "flawless inference on wrong numbers", a consistency solver defines 27 physiological and mathematical constraints—haematological and biochemical identities (e.g. MCH = Hb/RBC; anion gap; calculated LDL) and monotonicity requirements—and models common OCR errors (misplaced decimal, dropped digit) with explicit edit costs. A minimum-joint-cost search identifies a correction satisfying all constraints and uses culprit/exoneration reasoning to localise the erroneous field. The OCR layer was not part of the quantitative evaluation reported here; all datasets were ingested as structured values, and we make no claim about OCR accuracy or about offline operation of the multimodal pipeline.

### 2.4 Five-layer cross-inference engine and weighted fusion

Five layers score every candidate entity independently: (1) the rule engine, a population-aware deterministic evaluation of the registry across the four rule layers from screening to staging; (2) a clustered Bayesian network (75 disease nodes, 30 evidence clusters) whose likelihood ratios are derived from rule thresholds; (3) an adaptive fuzzy layer (35 rules, 20 clinical patterns) that grades the distance of each value from its reference limits and abstains when no rule covers the analyte; (4) a clinical knowledge graph (97 nodes, 112 cause–effect edges) that propagates support between pathophysiologically linked entities; and (5) 100 published risk models (FIB-4, APRI, eGFR CKD-EPI 2021, corrected calcium, albumin-corrected anion gap, TyG, HOMA-IR and others). Layer outputs are fused by a fixed weighted ensemble—0.35 rule engine, 0.25 Bayesian, 0.20 fuzzy, 0.10 graph, 0.10 risk models, with domain-specific profiles for toxicology, critical care, autoimmune, oncology, endocrine and cardiometabolic entities—followed by discord-aware shrinkage: when layers disagree the fused score is pulled towards the sceptical cluster by up to 45%, and a score supported by a single layer is discounted by 30%. No weight was fitted to outcome data; the weights were fixed before any real-data evaluation and a pre-registered weight sweep (Phase 7) produced no stable improvement and was abandoned.

### 2.5 Constrained Theory-of-Evidence layer

Because of the uncertainty inherent in clinical data, the collective voting layer is not simple voting or standard DST but a constrained variant with four structural modifications. First, to avoid the exponential cost of a single frame containing every diagnosis, a binary frame—presence, absence, ignorance—is defined for each disease. Second, Yager's rule replaces Dempster's rule: the conflict mass K is assigned to ignorance (Θ) rather than renormalised among hypotheses, so that when the five evidence sources disagree the system withholds a definitive decision instead of amplifying one side. Third, abstention is an explicit state: layers that abstain are excluded from both the conflict computation and the combination, and their weights are redistributed among the layers that spoke. Fourth, the final ranking is determined by the calibrated point score of Section 2.4, while belief and plausibility are used only to report the evidence status of each candidate (confirmed, probable, insufficient). Reliability discounting is applied to each source before combination. This design makes "confidently wrong" outputs structurally difficult and is the reason the engine asserted disease in 0 of 1,000 synthetic healthy panels and in at most 1 of 246 guideline-healthy NHANES adults (Section 4).

### 2.6 Expert syndrome layer, causal attribution and ranking hygiene (engine v6–v7)

Above the fused score sits an expert syndrome layer of approximately 900 hand-tuned multi-analyte constellations, each with a tiered anchor strength (anchor 0.95, strong 0.88, pattern 0.80, supportive 0.72, screen 0.45), operators (absent, between, negated, present) and context predicates (pregnancy, age, sex, medication, condition, family history, encounter). This layer can strengthen, weaken or guard a candidate but cannot introduce a diagnosis that the rule layer never proposed. Engine versions v6 and v7 added a ranking-hygiene stage that enforces guideline semantics: a disease–finding explanation graph lets a covering diagnosis explain its downstream findings (diabetic ketoacidosis explains hyperglycaemia, acidosis and the anion gap, which are then shown as `explained_by` rather than as competitors); an anchor finding such as a raised INR never loses its critical status; a diagnosis with insufficient evidence cannot bury a finding; a single creatinine yields "reduced GFR, chronicity undetermined" per KDIGO rather than chronic kidney disease; and a single troponin yields "myocardial injury, acuity undetermined" per the fourth universal definition of myocardial infarction. No syndrome may be asserted from a normal analyte. The output is a two-tier differential—specific diagnoses and umbrella syndromes—each with explained findings, an evidence state, cited sources and suggested next tests (maximum 25 entries). The engine is deterministic: byte-identical output was obtained in 50 of 50 repeated stays and across freezes.

### 2.7 Versioning and releases

Every release is versioned jointly for engine and registry and must pass a regression gate before any real-data run: 689 unit tests, three adversarial vignette batteries (151, 124 and 78 cases), a 1,000-panel healthy sweep, a 755-pair perturbation battery and an SI/conventional unit-twin battery. The evaluated release is engine v7 with registry 14.1.0; the shipped product release 1.3.1 uses registry 13.4.2. Engine changes C1–C16 between 13.4.2 and v7 are listed with dates in Supplementary Table S1; none was fitted to outcomes and no rule was written for a specific missed case (the one persistent failure in the adversarial battery, alcoholic pancreatitis, was deliberately left unpatched).

## 3. Evaluation Methodology

### 3.1 Pre-registration, freezes and quarantine

All analyses follow a statistical analysis plan (SAP) that fixed metrics, label maps, thresholds and comparators; fifteen dated amendments record every subsequent change with justification (Supplementary Note 1). Before each quarantine round the code and registries were frozen with a SHA-256 manifest (261 and 316 files). Quarantine datasets had never been run before the freeze and were run exactly once (Fig. 3a). Round 1 (MIMIC-IV demo, NHANES 2013–14, PhysioNet sepsis set B) used superiority criteria over the previous release and failed two of them, because guideline-correctness changes lowered label recall for chronic kidney disease; the failure is reported with its original criteria. The criteria were then re-specified as non-inferiority with dated justification, six further correctness changes were made (engine v7), the development gate showed parity, and Round 2 (NHANES 2015–16, sepsis set B2, healthy sweep with a new seed) met all criteria. Two data-loader defects discovered during Round 2 (patient identifiers stored as strings; a dropped derived NHANES variable) were corrected before scoring without touching the engine and are documented.

Fig. 3. (a) Pre-registration, freeze and one-shot quarantine workflow. (b) Decomposition of eICU label targets and recall on panel-supported labels.

### 3.2 Datasets and reference standards

Table 1 summarises the data sources. Only public datasets were used; the MIMIC-IV and eICU demo versions are subsets that do not require credentialing. Reference standards were: clinician problem lists in eICU-CRD, organised into 31 laboratory-relevant groups by regular expressions fixed in the SAP (an audit of 100 stays and 425 diagnosis strings found precision 100% and sensitivity 98.7% for the map); ICD-10 codes in MIMIC-IV; guideline criteria in NHANES (ADA diabetes, KDIGO CKD, WHO anaemia and iron deficiency, ACG ALT limits) and self-reported physician diagnosis as a label independent of the input values; the expert diagnostic comment in UCI thyroid0387; clinical category in UCI HCV; liver-patient status in ILPD; the published diagnosis in 50 PMC-Patients case reports (specific and syndrome level, key fixed in advance); and the Sepsis-3 onset label of the PhysioNet/CinC 2019 challenge.

Table 1. Data sources, reference standards and roles.

| Dataset | Setting | Units | Reference standard | Role | n evaluated |
|---|---|---|---|---|---|
| Synthetic batteries | expert-constructed vignettes; adversarial, perturbation, unit-twin and healthy sweeps | mixed | author-defined expected diagnosis | development / regression gate | 353 cases; 755 perturbation pairs; 1,000 healthy panels per seed |
| eICU-CRD demo v2.0.1 | 186 US ICUs | conventional | clinician problem list → 31 groups | development and per-release gate | 2,520 stays → 2,314 adults with ≥ 8 analytes; 2,432 labels |
| MIMIC-IV demo | US tertiary hospital | conventional | ICD-10 discharge codes | quarantine round 1 | 235 admissions; 507 pairs |
| NHANES 2017–18 (J) | US community survey, adults | SI + conventional | guideline criteria and self-report | development | 3,000 adults |
| NHANES 2013–14 (H) | idem | idem | idem | quarantine round 1 | 3,000 |
| NHANES 2015–16 (I) | idem | idem | idem | quarantine round 2 | 3,000 (healthy subset 79) |
| PhysioNet/CinC 2019 sets A / B / B2 | US ICU hourly records | conventional | Sepsis-3 onset | pre-registered single target; B and B2 quarantine | 4,871 (439 sepsis) / 4,558 (268) / 4,991 |
| UCI thyroid0387 | Garvan Institute referral laboratory | SI | expert diagnostic comment | external | 3,162 records |
| UCI HCV (Hoffmann 2018) | German donors and hepatology clinic | SI | clinical category | external | 615 |
| ILPD | Andhra Pradesh, India | conventional | liver-patient status | external | 583 |
| PMC-Patients (Bhasuran 2025) | published case reports, laboratory paragraph only | free text | published diagnosis | external anchor | 50 |

### 3.3 Metrics

The primary metric in eICU is flat recall@k (k = 3, 5, 10) of clinician-listed diagnoses in the specific-diagnosis tier. Secondary metrics are two-tier recall (either tier), per-group AUROC of the group score, and panel-supported recall—recall restricted to labels whose first panel met a guideline criterion fixed in code before scoring (`panel_supported_metric.py`), excluding groups without a single laboratory criterion. For screening datasets we report AUROC with 95% bootstrap confidence intervals, sensitivity and specificity at 0.5, and the false-assertion rate among adults with all indices normal. For sepsis we report the AUROC of the sepsis-group score. Calibration is assessed by expected calibration error (ECE) and Brier score before and after cross-fitted isotonic regression.

### 3.4 Comparators

Four comparators used identical inputs: (B1) a raw key-analyte threshold; (B2) gradient boosting and logistic regression trained on the same analytes with five-fold out-of-fold prediction; a registry-off ablation (syndrome layer only); and a general-purpose GPT-4-class LLM (October 2026) run by the authors, blinded to labels, with a fixed prompt requesting ten ranked diagnoses from the identical panel, age and sex, scored by the same label map and script; 40 panels were re-read to measure test–retest reproducibility. Model identity is withheld by design and the comparison is labelled as an author-run baseline; prompts and outputs are released.

### 3.5 Statistics

Wilson intervals for proportions; 1,000-sample bootstrap or DeLong intervals for AUROC; McNemar's test for paired recall; bootstrap for differences in mean reciprocal rank. Analyses used Python 3.11/3.13 with numpy, pandas and scikit-learn. Reporting follows TRIPOD+AI.

## 4. Results

### 4.1 Regression gate and robustness

The frozen release passed 689/689 unit tests, 151/151, 124/124 and 77/78 adversarial vignettes, 753/755 perturbation pairs, the unit-twin battery and the healthy sweep (0 assertions in 1,000 panels). In 50 real stays the engine and the LLM both flagged 39/39 CAP critical values; the engine produced identical top-10 lists and alerts in three repeated runs of every stay.

### 4.2 Intensive care (eICU-CRD demo)

In 2,314 adult ICU stays, using the first panel with at least eight analytes and no clinical text, 47.9% (95% CI 45.9–49.9) of 2,432 clinician-listed diagnoses appeared in the top-3, 60.8% (58.8–62.7) in the top-5 and 74.1% (72.3–75.8) in the top-10 of the flat differential; counting either tier, top-5 recall was 71.9% (Table 2). Recall@5 was 88.1% for acute myocardial infarction, 82.8% for heart failure, 83.0% for anaemia, 77.5% for acute kidney injury and 77.9% for gastrointestinal bleeding, but 49.1% for sepsis, 45.1% for diabetes and 35.8% for CKD.

The reference standard bounds this metric (Fig. 3b). Of 2,707 label targets, 541 belonged to groups with no single laboratory criterion, 275 lacked the key analyte in the first panel and 431 were contradicted by the first panel (for example hypokalaemia coded with potassium 4.1 mmol/L after repletion). Among the 1,460 labels whose first panel met the guideline criterion, flat recall was 29.6 / 62.5 / 78.0 / 91.8% at k = 1 / 3 / 5 / 10 and two-tier recall 43.0 / 77.7 / 89.2 / 97.2%. On this subset recall@5 exceeded 85% for renal impairment, acute kidney injury, anaemia, myocardial infarction, diabetic ketoacidosis, heart failure, hypokalaemia and pancreatitis; the only groups in which v7 lost against the product release were CKD (41.1% vs 74.4%, by design) and leukocytosis (46.9% vs 67.3%) (Supplementary Fig. S3).

Table 2. eICU-CRD demo (n = 2,314 stays), laboratory values only: recall of clinician-listed diagnoses by release.

| Release | flat @3 | flat @5 | flat @10 | two-tier @5 | panel-supported @5 / @10 (n = 1,460) | two-tier panel-supported @5 / @10 |
|---|---|---|---|---|---|---|
| 13.3.0 | 49.3 | 63.8 | 77.2 | — | — | — |
| 13.4.2 (product 1.3.1) | 49.3 | 63.7 | 76.9 | — | 81.6 / 95.1 | — |
| 14.1.0 + engine v6 | 48.5 | 60.8 | 74.1 | 71.7 | 78.0 / 91.8 | 88.9 / 97.2 |
| **14.1.0 + engine v7 (frozen)** | **47.9** | **60.8** | **74.1** | **71.9** | **78.0 / 91.8** | **89.2 / 97.2** |
| registry off (ablation) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |

### 4.3 Comparators on identical inputs

A raw key-analyte threshold matched or exceeded the engine's AUROC for single-analyte groups (hyperkalaemia 0.96 vs 0.92; anaemia 0.83 vs 0.78), as expected for findings that are definitions. Gradient boosting and logistic regression trained on the labels exceeded the untrained engine only in outcome-defined groups without a laboratory signature—sepsis (0.82 vs 0.68), gastrointestinal bleeding (0.85 vs 0.75), alcohol withdrawal (0.80 vs 0.54), diabetes (0.75 vs 0.69)—and were matched or beaten in nine guideline-defined groups (CKD 0.79 vs 0.81; hyponatraemia 0.85 vs 0.89; thrombocytopenia 0.85 vs 0.89; cirrhosis 0.83 vs 0.87; pancreatitis 0.67 vs 0.74) (Fig. 4). Disabling the rule registry reduced flat recall@5 from 63.7% to 62.0% and mean 24-group AUROC from 0.767 to 0.732, with leukocytosis falling from 57.9% to 8.8%; on panel-supported labels recall@5 fell from 78.0% to 75.3%. Adding documented history and medications raised recall@5 by 0.9 points for labels not named in the history (n = 2,467) but by 23.3 points for labels already named (n = 240); the context arm therefore mainly echoes documentation and is reported only in the Supplement.

Fig. 4. Untrained Hemoglyph versus supervised models trained on identical inputs (eICU-CRD demo): per-group AUROC.

### 4.4 Community survey: three independent NHANES cycles

Fig. 5 and Table 3 show that discrimination reproduced across the development cycle and the two quarantine cycles: diabetes 0.945 / 0.938 / 0.924, CKD 0.958 / 0.968 / 0.962, anaemia 0.973 / 0.994 / 0.983, iron deficiency 0.990 / – / 0.972 (ferritin not measured in 2013–14), hyperuricaemia 0.943 / 0.958 / 0.955, hypercholesterolaemia 0.902 / 0.883 / 0.886 and ALT elevation 0.721 / 0.880 / 0.877 (the lower 2017–18 value reflects a threshold definition corrected under Amendment 14). These laboratory-defined labels overlap the inputs and test criterion recognition; against self-reported physician diagnosis, which is independent of the inputs, AUROC was 0.918 / 0.914 / 0.898 for diabetes and 0.816 / 0.748 / 0.799 for kidney disease. Among guideline-healthy adults the engine asserted disease in 1/160, 1/246 and 0/79.

Fig. 5. NHANES screening across three independent cycles (n = 3,000 each).

Table 3. Held-out performance in NHANES (three cycles) and in the referral-laboratory, hepatology, Indian, MIMIC and case-report cohorts, engine v7.

| Target (reference standard) | 2017–18 (development) | 2013–14 (quarantine 1) | 2015–16 (quarantine 2) |
|---|---|---|---|
| Diabetes (HbA1c ≥ 6.5% or FPG ≥ 126 mg/dL) | 0.945 | 0.938 | 0.924 |
| Diabetes, self-report only | 0.918 | 0.914 | 0.898 |
| CKD (eGFR < 60 or ACR ≥ 30) | 0.958 | 0.968 | 0.962 |
| CKD, self-report only | 0.816 | 0.748 | 0.799 |
| Anaemia (WHO) | 0.973 | 0.994 | 0.983 |
| Iron deficiency (ferritin < 15 ng/mL) | 0.990 | — | 0.972 |
| Hypercholesterolaemia (TC ≥ 240 mg/dL) | 0.902 | 0.883 | 0.886 |
| Hyperuricaemia (> 7.0 M / > 6.0 F mg/dL) | 0.943 | 0.958 | 0.955 |
| ALT elevation (ACG sex-specific) | 0.721 | 0.880 | 0.877 |
| Guideline-healthy adults: any disease asserted | 1 / 160 | 1 / 246 | 0 / 79 |
| UCI thyroid0387: hypothyroidism / hyperthyroidism | AUROC 0.979 (sens 0.969, spec 0.951) / 0.798 | | |
| UCI HCV: any liver disease / cirrhosis | AUROC 0.925 (0.881–0.962) / 0.909 | | |
| ILPD: liver patient | AUROC 0.704 (0.661–0.747) | | |
| MIMIC-IV demo (ICD reference): recall @5 / @10 | 47.5% / 62.1% | | |
| PMC case reports, manual laboratory extraction: specific / syndrome, top-5 | 26% / 68% (automatic parsing 10% / 44%) | | |

### 4.5 Pre-registered negative result: sepsis

The engine's sepsis score from first-24-hour laboratory values discriminated Sepsis-3 onset with AUROC 0.600, 0.610 and 0.588 (95% CI 0.559–0.616) in sets A, B and B2, versus 0.691, 0.712 and 0.679 for a supervised logistic model on the same features. A post-hoc concurrent analysis (laboratory values and vital signs within ± 6 h of onset; Amendment 13) reached 0.635 (0.597–0.673) versus 0.726 (Fig. 6). Guideline-sourced SIRS/qSOFA rules developed on set A and validated once on set B2 added about 0.04; no outcome-fitted tuning was performed. Hemoglyph is not a sepsis predictor.

Fig. 6. Sepsis (PhysioNet/CinC 2019): engine versus supervised logistic AUROC in prediction and concurrent frames across sets A, B and B2.

### 4.6 Blinded comparison with a GPT-4-class LLM

On 400 stays (596 labels) the LLM received the identical panel, age and sex and returned ten ranked diagnoses, blinded to labels (Table 4; Fig. 7). Recall@5—the pre-specified primary comparison—was 64.4% (60.5–68.2) for Hemoglyph (v5.1) versus 59.6% (55.6–63.4) for the LLM (McNemar p = 0.0093); recall@10 74.5% vs 65.1%; mean reciprocal rank 0.397 vs 0.408 (difference CI −0.037 to +0.014). The LLM placed more labels at rank 1 (168 vs 139) and the engine left fewer absent (152 vs 208). The engine was better for gastrointestinal bleeding (87% vs 50%), CKD (51% vs 20%) and diabetes (55% vs 37%); the LLM was better for diabetic ketoacidosis (83% vs 73%) and metabolic acidosis (79% vs 57%). On 40 re-read panels the LLM agreed with itself on 85.7% of labels (κ = 0.69; mean Jaccard of top-5 sets 0.75); the engine is deterministic.

Table 4. Blinded comparison with a GPT-4-class LLM on identical inputs (400 eICU stays, 596 labels).

| Metric | Hemoglyph | LLM |
|---|---|---|
| recall@1 | 23.3% (20.1–26.9) | 28.2% (24.7–31.9) |
| recall@3 | 49.5% (45.5–53.5) | 50.8% (46.8–54.8) |
| recall@5 (primary) | **64.4% (60.5–68.2)** | 59.6% (55.6–63.4); McNemar p = 0.0093 |
| recall@10 | 74.5% (70.8–77.8) | 65.1% (61.2–68.8) |
| mean reciprocal rank | 0.397 | 0.408 |
| label absent from list | 21.1% | 34.9% |
| test–retest (40 panels) | deterministic | agreement 85.7%, κ 0.69 |
| critical values flagged (50 stays) | 39 / 39 | 39 / 39 |

Fig. 7. Blinded LLM comparison: per-group recall@5 and rank-bin distribution.

### 4.7 Calibration and subgroups

Pooled over 52,689 stay–group units, AUROC was 0.801 but ECE was 0.161 (Brier 0.115); cross-fitted isotonic recalibration reduced ECE to 0.002 (Brier 0.040), with per-group raw ECE from 0.186 (sepsis) to 0.346 (anaemia). Raw scores are therefore ranks and are not displayed as probabilities in the interface. Recall@5 was 65.4% (62.6–68.2) in men and 61.1% (57.1–65.3) in women, 60–67% across age bands and 63–66% across the three largest ethnicity strata; the engine contains no race term and uses the race-free CKD-EPI 2021 equation.

## 5. Discussion

### 5.1 Principal findings

Hemoglyph—a hybrid knowledge-based reasoning system with no training phase—recovered 61% of clinician-listed ICU diagnoses in five suggestions from laboratory values alone, 78% of those diagnoses that the first panel could actually support, and reproduced screening AUROCs of 0.92–0.99 across three independent NHANES cycles while asserting disease in at most one of 246 healthy adults. It was competitive with, and for guideline-defined conditions often superior to, supervised gradient boosting trained on the labels, and in a blinded paired comparison on identical inputs it listed more diagnoses than a GPT-4-class LLM on the pre-specified metric while remaining deterministic and traceable to cited rules. Its performance was weaker for multifactorial syndromes without a laboratory definition—sepsis, heart failure without natriuretic peptides, gastrointestinal bleeding—and it failed, as pre-registered, to predict Sepsis-3 onset.

Three findings govern how these numbers should be read. First, the apparent ceiling near 60% is largely a property of the reference standard: a quarter of admission-level labels were not inferable from the first panel, and a supervised model trained on the labels themselves did not exceed 0.82 AUROC for outcome-defined groups. The panel-supported metric, though its thresholds were fixed in code before scoring, was defined after the ceiling was observed and is structurally optimistic; we present it beside, not instead of, the flat metric. Second, the untrained engine matched supervised models wherever a guideline definition exists and lost wherever the label is an outcome that the model learns from hidden correlates—the expected division of labour between knowledge and learning, which argues for hybrid rather than replacement designs. Third, the LLM was better at rank 1 and worse at coverage; the two systems make different errors.

### 5.2 Comparison with prior work

Early CDSS such as CASNET could not distinguish lack of evidence from contradictory evidence; DST-based approaches addressed this gap but, through Dempster's normalisation, can become confident in a wrong hypothesis under severe conflict. Hemoglyph adopts Yager's combination within binary frames, assigning conflict mass to ignorance and treating abstention as a first-class state; the empirical consequence is visible in the healthy-adult sweeps and in a false-assertion proxy of 8% in stays with an empty problem list. Unlike architectures that use an LLM to generate explanations (Ashworth et al., 2025), the evaluated Hemoglyph release uses no language model at inference time, so hallucination is excluded by construction rather than mitigated. Unlike supervised models that require labelled data (Rank et al., 2020; Fleuren et al., 2020), it is transparent and portable across units and populations, which the unit-twin battery and the SI-based NHANES, UCI and HCV cohorts demonstrate. Compared with Isabel and DXplain, which take symptoms and have been evaluated on 36–201 cases (Bridges, 2024, 2025; MGB, 2025; Bond et al., 2012), this study isolates laboratory-only reasoning on more than 20,000 real encounters, pre-registers its analysis and releases its knowledge base under an open licence into an ecosystem in which public executable guideline repositories have been withdrawn.

### 5.3 Clinical implications

Hemoglyph is a fully offline, deterministic and explainable system: it operates locally with zero telemetry and therefore protects patient privacy by design. Its abstention mechanism is clinically important: when evidence is insufficient or inconsistent, the system declares uncertainty rather than issuing a definitive and potentially hazardous diagnosis—valuable when laboratory results are influenced by physiological confounders or pre-analytical error. Its natural positions are the post-analytical step of a laboratory information system—interpretive comments and critical-pattern alerts generated locally—and a reproducible, auditable baseline against which LLM-based interpretation can be measured. Clinicians should note that raw scores are ranks: thresholds must be calibrated to the target population (as the ALT task illustrates) and the interface does not present scores as probabilities. The two architectures could also be combined: a language model to extract and normalise free-text results—the step at which our automatic parser lost half of the PMC cases—and a rule engine to reason over them.

### 5.4 What changed since the earlier version of the system

Relative to the earlier description of Hemoglyph (registry 13.1.0, engine v1), the present work adds: (i) a pre-registered SAP with fifteen dated amendments, SHA-256 freezes and two one-shot quarantine rounds, including a failed round; (ii) the expert syndrome layer, causal attribution and guideline-semantics guards of engine v6–v7, which traded about three points of flat recall for correctness (a single creatinine no longer asserts CKD; a normal leukocyte count no longer yields a syndrome) and which we disclose as a deliberate trade; (iii) registry curation from 13.1.0 to 14.1.0 with 1,474 retired records, a provenance audit and `unverified_source` flags; (iv) the panel-supported metric that quantifies the reference-standard ceiling; (v) comparators on identical inputs—raw thresholds, supervised models, registry ablation and a blinded GPT-4-class LLM with test–retest; (vi) three NHANES cycles instead of one, three sepsis sets, MIMIC-IV demo and PMC case reports; (vii) calibration, decision-curve, subgroup and next-test analyses; and (viii) open licensing of engine (AGPL-3.0) and registries (CC BY-SA 4.0). The leukocytosis pattern that could not be diagnosed in version v1 is now recognised (57.9% recall@5 with the registry on).

### 5.5 Limitations

This study has significant limitations. First, no prospective or clinician-in-the-loop evaluation has been conducted; all evidence is retrospective, and a pre-registered crossover reader study with an automation-bias endpoint is in preparation. Second, of 33,183 executable rules only 272 (0.8%) are manually curated guideline anchors; the remaining 32,901 were generated with AI assistance and remain in the status `candidate_requires_specialist_validation`; 34 sources lack a locator. Third, the registries were developed by the first author with the assistance of a large language model and have not been reviewed by an independent expert panel. Fourth, only the open demo subsets of eICU-CRD and MIMIC-IV were used, and their reference standards—admission-level problem lists and ICD codes—are not adjudicated panel-level diagnoses; the panel-supported metric is structurally optimistic. Fifth, the LLM comparison is an author-run self-baseline with one model, one prompt, no retrieval augmentation and the v5.1 engine. Sixth, laboratory-defined NHANES labels overlap the inputs; only the self-reported labels are independent. Seventh, raw scores are uncalibrated, and sample sizes in UCI HCV and ILPD are small. Eighth, performance on multifactorial syndromes is weak and the engine does not predict sepsis. Ninth, Iranian populations and non-English laboratory conventions were not evaluated, and the OCR layer was not quantitatively assessed. Finally, the first author is a secondary-school student and the system and analyses were developed with AI-agent assistance, declared below.

### 5.6 Conclusion

An open, offline, knowledge-driven hybrid reasoning system can interpret laboratory panels to the ceiling that the first panel allows, reproduce population-screening performance across independent survey cycles and match a frontier LLM blind, while remaining deterministic, abstention-aware and auditable. Its limits—outcome-defined syndromes, uncalibrated scores and an AI-drafted rule base awaiting expert audit—are stated so that they can be measured and closed.

## Declarations

Author contributions. S.B. conceived the system, built the engine and knowledge base, designed and ran the evaluation and wrote the manuscript. Z.T. reviewed the statistical analysis plan and the reporting of the quarantine evaluation and revised the manuscript. E.B.S. supervised the statistical methodology and critically revised the manuscript. All authors approved the final version. (Contributions of Z.T. and E.B.S. to be confirmed before submission.)

Competing interests. S.B. is the sole developer of Hemoglyph, whose desktop application is distributed under a proprietary licence; the engine and registries are open. Z.T. and E.B.S. declare no competing interests. No funding was received.

Use of artificial intelligence. The rule registry was drafted with LLM assistance and curated by automated audits. An AI coding agent assisted with evaluation scripts, figure generation and the blinded LLM arm under the first author's direction; all analyses were specified in the SAP and are reproducible from the released code. No AI tool is an author.

Data availability. eICU-CRD demo, MIMIC-IV demo and PhysioNet/CinC 2019 (physionet.org), NHANES (wwwn.cdc.gov/nchs/nhanes), UCI thyroid0387 and HCV, and ILPD are public. Per-stay outputs, label maps, LLM prompts and outputs are provided as Supplementary Data.

Code availability. Engine and evaluation scripts (AGPL-3.0-or-later) and rule registries (CC BY-SA 4.0), with freeze manifests and `reproduce.sh`, will be deposited on Zenodo with a DOI before publication.

Ethics. All datasets are de-identified and publicly released under their data-use agreements; no ethical approval was required.

## References

1. Ledley, R. S., & Lusted, L. B. (1959). Reasoning foundations of medical diagnosis. *Science*, 130(3366), 9–21.
2. Dambro, M. R. (1972). *A computer-assisted medical diagnostic system*. Doctoral dissertation, University of Missouri.
3. Dempster, A. P. (1967). Upper and lower probabilities induced by a multivalued mapping. *Annals of Mathematical Statistics*, 38(2), 325–339.
4. Shafer, G. (1976). *A Mathematical Theory of Evidence*. Princeton University Press.
5. Yager, R. R. (1987). On the Dempster–Shafer framework and new combination rules. *Information Sciences*, 41(2), 93–137.
6. Maqsood, M., et al. (2024). A hybrid clinical decision support system integrating machine learning and a rule-based medical knowledge base. [Journal to be confirmed.]
7. Damkliang, K., et al. (2025). Bayesian probability updates for iron-deficiency anaemia and thalassaemia screening. [Journal to be confirmed.]
8. Ashworth, A., et al. (2025). Translating clinical guidelines into a structured, version-controlled knowledge base with LLM explanation. [Journal to be confirmed.]
9. Nambison, S., et al. (2024). A fuzzy-logic system for interpreting pathology reports across 17 diseases. [Journal to be confirmed.]
10. LeukoAlert Study Group. (2026). Opportunistic screening for occult leukaemia using 72 CBC-derived features. [Journal to be confirmed.]
11. Sutton, R. T., et al. (2020). An overview of clinical decision support systems: benefits, risks, and strategies for success. *npj Digital Medicine*, 3, 17.
12. Plebani, M. (2010). The detection and prevention of errors in laboratory medicine. *Annals of Clinical Biochemistry*, 47, 101–110.
13. Epner, P. L., Gans, J. E., & Graber, M. L. (2013). When diagnostic testing leads to harm. *BMJ Quality & Safety*, 22, ii6–ii10.
14. Cadamuro, J., et al. (2023). Potentials and pitfalls of ChatGPT and natural-language AI models for the understanding of laboratory medicine test results. *Clinical Chemistry and Laboratory Medicine*, 61, 1158–1166.
15. Kurstjens, S., et al. (2024). Accuracy of large language models in answering laboratory medicine questions. *Clinical Chemistry and Laboratory Medicine*.
16. Hager, P., et al. (2024). Evaluation and mitigation of the limitations of large language models in clinical decision-making. *Nature Medicine*, 30, 2613–2622.
17. Savage, T., et al. (2024). Diagnostic reasoning prompts reveal the potential for LLM interpretability in medicine. *npj Digital Medicine*, 7, 20.
18. Bridges, J. M. (2024). Computerized diagnostic decision support systems – a comparative performance study of Isabel Pro vs. ChatGPT4. *Diagnosis*, 11, 250–258.
19. Bridges, J. M. (2025). Comparative performance of Isabel Pro and ChatGPT-4, part II. *JAMIA Open*, 8, ooaf048.
20. Massachusetts General Brigham Laboratory of Computer Science. (2025). DXplain versus GPT-4 and Gemini on 36 clinical cases with and without laboratory data. [Record to be confirmed.]
21. Bond, W. F., et al. (2012). Differential diagnosis generators: an evaluation of currently available computer programs. *Journal of General Internal Medicine*, 27, 213–219.
22. Bhasuran, B., et al. (2025). Preliminary analysis of the impact of lab results on LLM-generated differential diagnoses. *npj Digital Medicine*, 8, 159.
23. Pollard, T. J., et al. (2018). The eICU Collaborative Research Database. *Scientific Data*, 5, 180178.
24. Johnson, A. E. W., et al. (2023). MIMIC-IV, a freely accessible electronic health record dataset. *Scientific Data*, 10, 1.
25. Reyna, M. A., et al. (2020). Early prediction of sepsis from clinical data: the PhysioNet/Computing in Cardiology Challenge 2019. *Critical Care Medicine*, 48, 210–217.
26. Hoffmann, G., et al. (2018). Using machine learning techniques to generate laboratory diagnostic pathways—a case study. *Journal of Laboratory and Precision Medicine*, 3, 58.
27. Quinlan, J. R. Thyroid disease data set (thyroid0387). UCI Machine Learning Repository.
28. Ramana, B. V., et al. (2011). A critical study of selected classification algorithms for liver disease diagnosis. *International Journal of Database Management Systems*, 3, 101–114.
29. Rank, N., et al. (2020). Deep-learning-based real-time prediction of acute kidney injury outperforms human predictive performance. *npj Digital Medicine*, 3, 139.
30. Fleuren, L. M., et al. (2020). Machine learning for the prediction of sepsis: a systematic review and meta-analysis. *Intensive Care Medicine*, 46, 383–400.
31. Collins, G. S., et al. (2024). TRIPOD+AI statement. *BMJ*, 385, e078378.
32. KDIGO. (2024). Clinical Practice Guideline for the Evaluation and Management of CKD. *Kidney International*, 105, S117–S314.
33. American Diabetes Association. (2024). Standards of Care in Diabetes—2024. *Diabetes Care*, 47(Suppl 1).
34. Thygesen, K., et al. (2019). Fourth universal definition of myocardial infarction. *European Heart Journal*, 40, 237–269.
35. Vickers, A. J., & Elkin, E. B. (2006). Decision curve analysis. *Medical Decision Making*, 26, 565–574.

(References 6–10 and 20 were carried from the co-authors' draft and must be completed with full publisher records before submission.)

## Supplementary information

Note 1 SAP and amendments 1–15; Table S1 engine changes C1–C16; Table S2 quarantine criteria and outcomes; Table S3 participant flow; Fig. S1 provenance audit; Fig. S2 per-release eICU metrics; Fig. S3 per-group panel-supported recall; Fig. S4 calibration and decision curves; Fig. S5 context-echo analysis; Table S4 subgroup analysis; Table S5 next-test utility; Data 1 per-stay outputs and LLM prompts/outputs.
