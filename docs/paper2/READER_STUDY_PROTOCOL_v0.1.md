# Hemoglyph Paper 2 — Clinical-use evaluation protocol (v0.1, 2026-10-24)

**Working title.** Effect of an explainable, offline laboratory-interpretation engine on clinicians' interpretation of laboratory panels: a multi-reader multi-case crossover study, with a silent prospective run in a hospital laboratory.

**Status.** Draft protocol written before any reader is recruited and before any engine output is shown to any clinician. To be registered (OSF) before data collection. Supersedes nothing; Paper 1 (technical validation, registry 13.3.0) is the prerequisite.

**Principal investigator.** Sobhan Bahrami. **Statistical oversight.** Zhaleh Tahmasebinejad, Ehsan Bahrami Samani (SBU Statistics & Data Science Clinic). **Clinical site(s).** To be confirmed (via SBMU/RIES contacts).

---

## 1. Why a second study
Paper 1 shows what the engine *says* on retrospective data. It does not show what happens when a clinician *reads* it: whether accuracy improves, whether time is saved, how often an incorrect suggestion misleads (automation bias), how many alerts a working laboratory would face per day, and whether users trust or ignore it. These are the questions reviewers of Paper 1 are expected to raise and the ones that decide whether a CDSS is useful rather than merely accurate.

## 2. Design overview (two components)

### Component A — Multi-reader, multi-case (MRMC) crossover reader study
- **Readers.** Target 12 (minimum 8): 4 laboratory physicians / clinical pathologists, 4 internists, 4 residents (year ≥ 2). Recruited through co-authors' institutions; no payment (voluntary; acknowledgement offered).
- **Cases.** 60 anonymised laboratory panels with age and sex only (no history), stratified: 20 from eICU-CRD demo (public, de-identified; licence permits), 20 from published case reports (PMC-Patients set used in Paper 1 B6), 20 healthy/near-normal panels (NHANES-derived, no diagnosis). Each case has an adjudicated reference answer (two clinicians + record/case-report diagnosis; disagreements resolved by a third) **fixed before the study**. Case difficulty balanced using Paper 1 per-case engine rank (⅓ engine rank 1, ⅓ rank 2–5, ⅓ engine miss or healthy) so that the engine is *not* uniformly right — this is what makes automation-bias measurable.
- **Crossover.** Two sessions ≥ 4 weeks apart. Session 1: half the cases unaided, half aided (engine's top-5 differential + rationale text + flagged critical values, exactly as the desktop app renders them). Session 2: the other way round. Case order randomised per reader; allocation balanced by Latin square.
- **Primary endpoint.** Top-3 diagnostic accuracy of the reader's written differential against the reference (aided vs unaided), analysed with a mixed-effects logistic model (random intercepts for reader and case; Obuchowski–Rockette/Hillis MRMC as sensitivity analysis).
- **Secondary endpoints.** (i) Time per case; (ii) critical-value recognition rate; (iii) **automation-bias rate**: proportion of cases where the reader was correct unaided but adopted an incorrect engine suggestion when aided; (iv) **appropriate rejection rate**: reader correct despite an engine miss; (v) calibration of reader confidence (0–100 %) aided vs unaided; (vi) System Usability Scale and a 5-item trust questionnaire after session 2; (vii) free-text reasons for disagreeing with the engine.
- **Sample size.** With 12 readers × 60 cases, unaided top-3 accuracy ≈ 0.60 and intraclass correlations from published lab-interpretation reader studies, an absolute improvement of 0.08 is detectable with power 0.80 at α = 0.05 (simulation-based; to be re-run with pilot ICCs on the first 3 readers). Minimum informative design: 8 readers × 60 cases for an effect of 0.10.
- **Blinding.** Readers do not know which cases are "engine misses". Adjudicators of reader answers are blinded to aided/unaided condition.
- **Engine version.** Frozen registry 13.4.0 and engine 1.3.1 (SHA-256 recorded); no change during the study.

### Component B — Silent prospective run (shadow mode)
- **Setting.** One hospital or referral laboratory willing to export daily de-identified result panels (LIS export of analyte, value, unit, age band, sex; no identifiers) for 8–12 weeks.
- **Procedure.** Engine runs locally on the laboratory's machine (offline); outputs are stored, **never displayed** to staff. At study end, outputs are compared with (a) discharge/final diagnoses or (b) the laboratory physician's own interpretive comments where these exist.
- **Endpoints.** Alert volume per 1,000 panels (overall, critical, per category); positive predictive value of critical flags; recall@5 for laboratory-detectable diagnoses on *future* data; drift versus Paper 1 figures; unit-parsing failure rate on real LIS exports; latency.
- **Why it matters.** Converts "accuracy on curated historical data" into "burden and yield on tomorrow's real stream" without exposing any patient to an intervention.

## 3. Ethics and data
- Component A uses public de-identified data and clinicians as participants: informed consent of readers; expected to qualify for expedited/minimal-risk review. Component B needs institutional ethics approval and a data-sharing agreement (de-identified export). No engine output influences patient care in either component.
- No data leave the site; the engine is offline by design. Reader responses stored pseudonymously.

## 4. Pre-specified analysis
Mixed-effects models (lme4 or statsmodels), two-sided α = 0.05, 95 % bootstrap CIs by reader and by case; MRMC sensitivity analysis; automation-bias and appropriate-rejection rates reported with exact binomial CIs; no interim looks. Primary hypothesis H1: aided top-3 accuracy > unaided. Secondary H2: automation-bias rate < 10 % of engine-miss cases (safety threshold set a priori). Analysis code and the frozen case set will be released with the paper; the adjudicated answers will be released after publication.

## 5. Reporting
STARD-AI / CONSORT-AI elements as applicable; DECIDE-AI (early-stage clinical evaluation of decision support) as the primary checklist for Component A; Component B reported as an observational performance study.

## 6. Timeline (realistic, zero budget)
| step | when |
|---|---|
| Protocol v1 + OSF registration | within 2 weeks of Paper 1 submission |
| Case set adjudication (60 cases) | weeks 2–4 |
| Reader recruitment (12) | weeks 2–6 |
| Session 1 / washout / Session 2 | weeks 6–14 |
| Site agreement for Component B; 8–12-week shadow run | parallel, weeks 4–20 |
| Analysis, manuscript | weeks 20–26 |

## 7. What this protocol deliberately does **not** do
No interventional display to clinicians treating real patients, no outcome claims, no training of the engine on site data, no identity of the LLM comparator (not part of this study).
