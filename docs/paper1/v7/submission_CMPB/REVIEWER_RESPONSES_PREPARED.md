# Prepared responses to the four most likely reviewer objections (internal; R6-CMPB, 2026-10-27)

Principle: concede what is true, give the number, state what we can and cannot do in a revision.

## 1. "The LLM comparator is unnamed; the comparison is not reproducible."
**Concede.** The platform routes among frontier model families and does not expose model or version; we therefore label it a capability tier, not an identity (Methods 2.5; Limitations). The 400 prompts and raw outputs are frozen and released, so the *scoring* is fully reproducible even though the *generation* is not.
**Offer.** In revision we can add a second LLM arm with a named, openly weighted model run locally with a fixed seed and temperature 0 on the identical 400 panels and the identical scoring script. This is feasible on CPU for a 7–8 B model within the revision window. We would report it as an additional row of Table 5, not replace the frontier arm.
**Do not offer.** Naming the frontier model from inference; re-running on a paid API (not possible for the authors).

## 2. "The source-concordance audit was done by an AI agent, single-rater — it is self-assessment."
**Concede.** Stated in the abstract, Methods, Results and Limitations. No inter-rater reliability is claimed.
**Argue.** The protocol was frozen before sampling, the sample is public, every verdict carries the retrieved text or the reason it could not be retrieved, and the headline figure (92 % unresolvable) is a property of the locators, not of rater judgement: a URL that returns an organisation landing page is unresolvable for any rater. The discordance floor (7.5 %) is conservative by construction.
**Offer.** A clinician or librarian re-rating of the same 200 rules under the same protocol; we will report raw κ whatever it is. If the editor requires it before acceptance, timeline ≈ 4 weeks.

## 3. "Only the demo subsets of eICU and MIMIC-IV were used."
**Concede.** Stated. The demo subsets are credential-free, which is why they could be used by authors without institutional access.
**Argue.** The scripts run unchanged on the credentialed releases (same schema); the eICU demo spans 186 hospitals and 2,314 stays, which is already larger than every published CDSS-vs-LLM comparison (36–201 cases). Confidence intervals are stay-clustered and narrow (±2 points at k = 5).
**Offer.** If a reviewer or editor with PhysioNet credentials wishes to run the released scripts on the full releases, the SAP specifies the analysis in advance; we cannot obtain credentials ourselves (requires an institutional reference).

## 4. "No clinician was involved; a secondary-school student cannot author a clinical rule base."
**Concede.** No clinician audited the rules or adjudicated outputs; the first author's status and financial interest are declared.
**Argue.** The paper's claims are about *verification methods* and what they found — including that the rule base is not auditable from its locators — not about clinical validity. The methods (property-based testing, frozen sampling protocol, hash-frozen one-shot evaluation) are software-engineering methods and are judged on reproducibility, which is complete. The co-authors are a biostatistician and a statistician who are responsible for the statistical design.
**Offer.** The physician rule-audit package (`eval/human/`) is prepared; if results arrive during revision they are added as a separate section labelled as a first application of the protocol by an independent clinician, with raw agreement reported.

## 5. (Likely minor) "Why is recall only 60 %? What is the engine for?"
Point to Discussion paragraph 3 (reference-standard ceiling: panel-supported recall 78/92 %; supervised models ≤ 0.82 AUROC on outcome groups; criterion-negative share 12.6 %; KDIGO-driven loss chosen) and to the positioning sentence in the Introduction. Do not add a new metric; do not retune the engine.

## 6. (Likely minor) "Main text exceeds 3,500 words."
Current 3,876. If asked, remove Section 3.6 external-cohort sentence and compress Discussion paragraph 4 (LLM benchmark criticisms) → ≈ 3,600.
