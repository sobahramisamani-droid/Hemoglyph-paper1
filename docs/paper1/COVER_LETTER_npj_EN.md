# Cover letter

Sobhan Bahrami
Independent researcher, Iran
sobahramisamani@gmail.com

24 October 2026

The Editors, *npj Digital Medicine*

Dear Editors,

Please consider the enclosed Article, **"Design and multi-dataset retrospective evaluation of Hemoglyph, an untrained, auditable knowledge-based engine for interpreting laboratory panels"**, for publication in *npj Digital Medicine*.

**What the paper reports.** Hemoglyph interprets whole laboratory panels offline, without training data, from a versioned and citable knowledge base (6,750 entities, 33,230 executable rules, 2,045 analytes), and returns a ranked, source-traced differential with calibrated probabilities and a confirmatory-test recommendation. We froze the engine under a pre-registered statistical analysis plan and evaluated it on public data from intensive care (2,314 stays, 186 hospitals), a national community survey, a referral laboratory, two hepatology cohorts and a published case-report benchmark, in both SI and conventional units. Against clinician problem lists the top-5 differential contained 63.8 % of listed diagnoses from laboratory values alone and 66.6 % with documented history; in a blinded comparison on 400 stays with identical inputs it listed 64.4 % versus 59.6 % for a zero-shot frontier LLM (McNemar p = 0.0093), with zero false assertions in guideline-healthy adults and bit-identical reruns.

**Why it fits npj Digital Medicine.** The journal has recently published the evidence that motivates this work—that LLMs cannot reliably classify laboratory values even with reference ranges, that laboratory data raise LLM differential accuracy, and that "evaluation illusions" arise when systems are tested on their authors' own vignettes. Our study answers with the methodological ingredients those papers call for: a pre-registered plan with every amendment disclosed, independent public datasets, raw-threshold and trained-model comparators, calibration and decision curves, a deterministic error taxonomy, subgroup reporting under TRIPOD+AI, and the complete release of code, knowledge base and evaluation harness.

**What we do not claim, and what failed.** We do not claim clinical validation or superiority over an LLM. We report that a supervised model trained on the target data discriminates better; that raw probabilities were over-confident until recalibrated; that two thirds of residual misses have no laboratory signature; that the knowledge base was drafted with LLM assistance and curated by a single non-physician author; that switching the entire rule registry off costs only 1.8 points of top-5 recall; and that a pre-registered hypothesis—that a sex-balanced knowledge base would close a 4.4-point male–female recall gap—failed, leaving the gap unresolved. We also disclose two execution errors caught by the regression gate during the final freeze. We believe this level of transparency is itself a contribution to how knowledge-based clinical software should be evaluated.

The main text (Introduction, Results, Discussion) is approximately 2,850 words, with a 145-word abstract, six figures and five tables. It has not been published or submitted elsewhere. All data are public and de-identified; no ethical approval was required. The authors (Sobhan Bahrami; Zhaleh Tahmasebinejad and Ehsan Bahrami Samani, Statistics and Data Science Clinic, Shahid Beheshti University) declare no competing interests and received no funding; all authors have approved the submission. The LLM used as a comparator was accessed through a platform that blinds model identity; this limitation is stated in the Methods and Limitations.

Suggested reviewers (no conflicts): experts in laboratory medicine informatics, clinical decision support evaluation, and LLM evaluation in medicine; we would be grateful for at least one reviewer from clinical chemistry.

Thank you for your consideration.

Sincerely,

Sobhan Bahrami (corresponding author), on behalf of all authors
