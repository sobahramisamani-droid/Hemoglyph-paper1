# Source-concordance audit of the Hemoglyph rule registry — protocol (frozen before sampling)

Date frozen: 2026-10-26 (before any sample was drawn or any source text inspected for this audit).
Registry audited: release/registry_14.1.0 (the frozen v7 registry reported in Paper 1).

## Purpose and scope
Estimate how faithfully executable rules transcribe their cited sources. This audit checks **transcription
concordance**, not clinical validity: a rule can be perfectly transcribed and still clinically wrong (outdated
threshold, inappropriate population), and a discordant rule is not necessarily harmful. No clinician takes part.

## Sampling (seed 20261026, Python `random.Random`)
Stratum A: 100 rules drawn uniformly from the 272 `curated_guideline_anchored` rules.
Stratum B: 100 `candidate_requires_specialist_validation` executable rules, split 50/50:
  B1 "eICU-relevant" — feature_id among analytes present in >= 50 % of eICU first panels AND disease_id in the
     31 evaluated label groups (the candidates most likely to have influenced the reported results);
  B2 uniform from all remaining executable candidates.
Sampling is by rule_id after sorting, so it is reproducible from the public registry.

## Fields compared (rule expression vs source text)
1. analyte identity; 2. operator and threshold (with unit); 3. population/context qualifier (age, sex, pregnancy)
when the rule specifies one; 4. direction/claimed role (e.g. diagnostic criterion vs screening) and the disease
the rule is attached to being the disease the source statement is about.

## Labels (per rule, each rater independently)
CONCORDANT — all four fields match the source statement (unit conversions allowed).
DISCORDANT — any field contradicts the source (wrong threshold, wrong disease attribution, population mismatch,
             source does not contain such a statement although it is reachable and on-topic).
UNRESOLVABLE — source unreachable from the audit environment, no locator, or source text too ambiguous to decide.
Tie-break rule: when in doubt, UNRESOLVABLE, never CONCORDANT. UNRESOLVABLE is **not** counted as concordant.

## Raters
Rater 1: AI agent (the same class of tool that drafted the rules) under the first author's supervision — declared.
Rater 2: a human non-clinician co-author (statistics), blind to rater-1 labels. Disagreements are reported, not
adjudicated away; the primary estimate uses rater-2 labels where available, rater-1 otherwise, and both are shown.

## Analysis
Discordance rate per stratum with Wilson 95 % CI, with two denominators: (a) resolvable rules only, (b) all sampled
rules (UNRESOLVABLE shown separately). Inter-rater agreement: Cohen's kappa over the three labels and over the
binary discordant/not. Examples of every discordant rule listed verbatim. Whatever the rates are, they are reported.

## Source access
Sources are retrieved by the registry URL / DOI landing page from the sandbox (curl, 20 s timeout). Pages that
block the sandbox (known: NICE, WHO, EASL, ESC, ACOG) will produce UNRESOLVABLE; the count is reported.
