# OSF registration — ready-to-paste text for the clinician concordance audit (Supplementary Note 19)

**REGISTERED 2026-10-29:** https://osf.io/8mdyq — doi:10.17605/OSF.IO/8MDYQ (Open-Ended Registration, public, CC BY 4.0; archived files: PROTOCOL_Note19.md, human_audit_sample_100.csv, SHA256SUMS, Hemoglyph_human_audit_rater_form.xlsx, analyse_human_audit.py). An earlier registration of the same text, archived without files owing to an upload error, is withdrawn and points to this one.

**How (15 minutes, free, corresponding author's account):** osf.io → *Create new project* (title below) → *Registrations* →
*New registration* → template **"Open-Ended Registration"** → paste the *Summary* below → attach `PROTOCOL_Note19.md`,
`human_audit_sample_100.csv`, `SHA256SUMS` and `RATER_INSTRUCTIONS.md` → *Register* → choose **public immediately**
(no embargo). Send the resulting registration URL to be inserted into Supplementary Note 19 ("registered at …").

**Honesty rule for the registration:** register only what is true. The *sample* was drawn and hashed on 2026-10-28; *no rater
has been approached and no verdict exists*. The registration is prospective for the audit itself. Do not describe the paper's
other analyses as pre-registered.

---

## Title
Independent clinician concordance audit of 100 rules from an AI-drafted laboratory-interpretation rule base (Hemoglyph registry 15.2.0): pre-registered protocol

## Summary (paste verbatim)

**Background.** Hemoglyph is an open-source laboratory-panel interpretation engine whose rule base (33,183 executable rules, registry 14.1.0; 15.2.0 at the time of sampling) was largely drafted with large language models. A manuscript under review reports two source-concordance audits performed by a single declared AI rater: 92% of a 200-rule sample could not be resolved from the registry's own source locators and at least 7.5% were demonstrably discordant. Those estimates have no human rater and no inter-rater reliability. This registration fixes, before any rater is approached, the protocol for the independent clinician audit.

**Objective.** To estimate, with two clinician raters blinded to the AI verdicts, (i) the proportion of rules whose analyte, operator, threshold, unit and population gate are concordant with the cited source, and (ii) inter-rater reliability, for the two rule populations that carry the engine's output: the active core and the curated anchors.

**Sample (already drawn, frozen, hashed).** 100 rules, deterministic draw with seed 20261028 from the verification ledger at registry 15.2.0: 50 active-core rules still executable (25 hot-core, 25 other) and 50 curated anchors that are not active-core members. File `human_audit_sample_100.csv`, SHA-256 in `SHA256SUMS` (attached). The AI rater's verdicts for the same 100 rules are sealed in `ai_verdicts_sealed.json` (hash attached) and will be opened only for the agreement analysis. The analysis code (`analyse_human_audit.py`: Wilson intervals, Cohen's κ on the three-level and binary verdicts, agreement with the sealed verdicts, and the interpretation thresholds below) is committed in the same folder before any verdict exists and will be run unchanged.

**Raters.** Two independent raters, each a specialist in laboratory medicine/clinical pathology or a board-certified internist, with no role in the project, no financial relationship with the first author and no prior sight of the AI verdicts. Names, recruitment route and any compensation will be disclosed.

**Materials.** For each item: rule identifier, entity, executable logic, population gate, cited source identifier, title, organisation, year and locator (URL/DOI). Raters use only the cited source at the cited locator; at most 15 minutes per item; a verbatim quote is required for every Concordant or Discordant verdict.

**Verdicts.** Concordant (C): the source states the threshold, operator, unit and population as encoded, or an exact equivalent after unit conversion. Discordant (D): the source states a different threshold, operator, unit or population, or does not support the rule. Unresolvable (U): the statement cannot be located in the cited source at the cited locator.

**Primary outcome.** Discordance proportion among resolvable rules, D/(C+D), overall and by stratum, Wilson 95% CI, from the consensus verdict. **Secondary outcomes.** Unresolvable proportion U/n; Cohen's κ between the two raters on the three-level verdict and on the binary resolvable/unresolvable split; κ between each rater and the sealed AI verdicts; median minutes per item.

**Consensus.** Disagreements resolved by discussion between the raters; unresolved items go to a third clinician whose verdict is final. Raw individual verdicts are published alongside the consensus.

**Sample size.** n = 100 gives a Wilson half-width of about 6 percentage points at 10% discordance (8–9 points per stratum of 50) and a standard error of about 0.07–0.10 for κ ≈ 0.6.

**Pre-specified interpretation.** If the human unresolvable proportion is ≥ 80%, the published conclusion that locator granularity, not rater effort, limits auditability is confirmed. If human raters resolve substantially more rules than the AI rater (unresolvable ≤ 60%), the AI audit under-reported auditability and this will be stated. If discordance among resolvable rules exceeds 25%, the rule base will be described as unsafe for any use without rule-by-rule review.

**What will not be done.** No rule will be edited between sampling and audit; raters' verdicts will not be used to tune any engine component before the audit result is published; items will not be dropped after verdicts are seen; κ will not be reported from fewer than 50 double-rated items.

**Where the frozen materials live.** Repository github.com/sobahramisamani-droid/Hemoglyph-paper1, folder `eval/audit/human_audit/` (sample, sealed verdicts, analysis code, hashes); the submitted snapshot is archived at doi:10.5281/zenodo.23750557.

**Timeline.** Recruitment after registration; results reported whatever they are, as an addendum to the manuscript or as a separate report, with the registration DOI cited.

**Conflicts.** The first author owns a proprietary desktop product built on the engine; the audit is designed so that this interest cannot influence the verdicts (blinded independent raters, sealed AI verdicts, frozen sample).

## Attachments
`PROTOCOL_Note19.md`, `human_audit_sample_100.csv`, `SHA256SUMS`, `RATER_INSTRUCTIONS.md`, `Hemoglyph_human_audit_rater_form.xlsx`
