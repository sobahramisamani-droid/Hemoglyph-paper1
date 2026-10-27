# Executable verifier for LLM differentials — protocol (declared before any result was computed)

Date: 2026-10-27. Status: frozen at commit time; results file does not yet exist.

## Question
Can the rule engine's guideline criteria be used as an *executable verifier* behind an LLM: label each LLM
differential entry as supported / contradicted / analyte-absent / not-verifiable from the same panel, and
does demoting unsupported entries reduce unsupported assertions without a material recall cost?

## Data (all already exist; no new LLM call)
- 400 eICU-CRD demo stays read blind by the unnamed frontier LLM (B3 n=100, B4 n=60, B8 n=240), ten named
  entries with probabilities each; same files as main-text Table 5 / Supplementary Note 2.
- Frozen engine v7 per-stay outputs (`per_stay_v7.json.gz`) for the engine arm and for the symmetric check.
- Label groups, synonym map (SYN) and criterion functions (CRIT) exactly as already used (eval_eicu.GROUPS,
  llm_zero_shot.SYN, panel_supported_metric.CRIT). Nothing is re-tuned.

## Verifier (deterministic, no learning)
For each entry mapped by SYN to a label group g:
- not_verifiable: g has no criterion function (sepsis, cirrhosis, GI bleeding, malnutrition, alcohol
  withdrawal) or the entry maps to no group (out of vocabulary) -> left untouched.
- supported: CRIT[g](panel) is True.
- contradicted: defining analyte present, CRIT[g](panel) is False.
- absent: CRIT[g](panel) is None (defining analyte not in the panel).
Secondary verdict (engine-based): g present anywhere in the engine's v7 differential for that stay.

## Arms
A  LLM raw (as Table 5).           B  LLM, contradicted/absent entries demoted below all others (order kept).
C  LLM, contradicted/absent removed. D  Engine v7 (as Table 5).
E  Engine v7 passed through the same verifier (symmetry: engine's own unsupported rate; thresholds are the
   engine's, so this is a consistency check, not an independent audit).

## Metrics (existing definitions only)
recall@1/3/5/10 against clinician labels (b8 label rule: coded group with a key analyte in the panel),
stay-clustered bootstrap for the paired A-B difference; unsupported-assertion rate = share of mapped top-5
entries with verdict contradicted or absent (the P5 quantity on unperturbed panels); verifier cost = number
and share of demoted entries that were clinician labels; agreement of the two verdicts.

## Registered predictions
LLM top-5 unsupported rate 15-30 %; after demotion < 5 %; recall@5 change between -2 and +1 points;
demoted entries that were clinician labels <= 10 % of demoted; engine top-5 unsupported rate 5-15 %.

## Not done
No threshold is changed to improve any number; no new metric; frozen v7 untouched; results reported whatever
their direction, including verifier false alarms.
