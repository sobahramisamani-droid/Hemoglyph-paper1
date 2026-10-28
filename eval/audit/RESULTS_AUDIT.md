# Audit study — results (2026-10-28)

Protocol: `PROTOCOL_AUDIT.md` (committed `9c87645` together with the frozen detectors `audit.py`). Code:
`make_core_registry.py` (Part 2), `audit.py` + `mutate.py` (Part 1), `llm_prompt.txt` + `convert_llm_corpus.py`
(Part 3). Frozen v7 results are untouched; every run here uses the v8.2 harness and registry 15.1.0 (or the stated
comparison registry). Reported in the order the parts were executed (2 → 1 → 3), because Part 1 could only be run
after the detectors were frozen and Part 3 only after Part 1.

## Pre-freeze calibration (declared)

The seven static detectors (R2a single ubiquitous analyte, R7 arithmetic severity tier, R9 impossible/flat tier,
DIR direction contradiction, UNIT unit–physiology mismatch, POP adult threshold on neonates/infants, SRC source-scope
mismatch) were calibrated on registry 15.1.0 **before** freezing. The first raw run flagged 1,241 rules (unit 713,
src 349, r9 188, dir 40), the overwhelming majority false positives of the heuristics (unit-string synonyms,
domain neighbours such as hepatology↔gastroenterology, deliberate multi-tier severities). Calibration consisted of
whitelists and synonym tables (`QUANT_UNITS`, `CONV`, `DOM_NEIGHBOURS`, `SCOPE2DOM`, `KEEP_SINGLE`, `UBIQUITOUS`);
no rule was changed. Final density on 15.1.0 after calibration: 87 flagged rules of 6,777 non-template executable
rules (1.28 per 100). Consequence, stated in advance: the 15.1.0 density is a *trained-on* number and is a lower
bound for the detectors' true positive rate on that registry; the 14.1.0 and Part 3 densities are out-of-sample
with respect to the whitelists, except that `KEEP_SINGLE` exempts 13 named 15.1.0 rules by identifier (see Part 3).

## Part 2 — Sufficiency of the audited core (registry arm CORE vs full 15.1.0)

CORE = the 335 executable rules of 15.1.0 that are either curated anchors or belong to the activity-defined active
core (every other rule set non-executable; sources untouched). Same harness, same cohorts, same seeds.

| metric | full 15.1.0 | CORE (335 rules) | Δ (pts) | paired full−CORE (gained / lost, exact McNemar p) |
|---|---|---|---|---|
| eICU flat recall@3 | 48.0 | 47.8 | −0.21 | +40 / −35, n.s. |
| eICU flat recall@5 | 61.2 | 61.2 | +0.04 | +45 / −49, n.s. |
| eICU flat recall@10 | 74.3 | 73.1 | −1.23 | +65 / −36, p = 0.005 |
| eICU two-tier @1 / @3 / @5 | 33.3 / 62.3 / 72.4 | 32.3 / 60.9 / 70.1 | −0.99 / −1.36 / −2.30 | @1 +25 / −9, p = 0.009 |
| eICU grouped @1 / @3 / @5 / @10 | 29.0 / 54.8 / 67.1 / 77.9 | 28.7 / 55.3 / 67.1 / 76.2 | −0.25 / +0.49 / −0.04 / −1.69 | @10 +69 / −28, p = 3.8e-5 |
| eICU mean per-label AUROC | .766 | .761 | −.005 | — |
| NHANES 2017–18 AUROCs (7 targets) | identical | identical | 0 | — |
| healthy-adult false assertions | 0/51 | 0/51 | 0 | — |

Denominator 2,432 labelled stay–diagnosis pairs in 2,314 stays. The gains of the full registry at @10 are driven by
diabetes (+28 grouped@10, +31 flat@10) and AKI/renal pattern templates; no `co_` template appears in any CORE top-5
(0 vs 88 in the full arm). Verdict under the protocol's pre-stated thresholds: the un-audited 30,735 executable
rules are **not load-bearing at @3/@5 (|Δ| ≤ 0.5 pt)** and **partially load-bearing at @10 and in the two-tier
metric (1.0–2.3 pt, significant)**. The activity-defined core of 1.1 % of rules therefore carries the ranking at the
cut-offs the paper reports as primary. Files: `eval/results/eicu_demo/*_core_icu.*`, `eval/results/nhanes_2017/*_core.*`,
`eval/audit/part2/paired_core.txt` (there A = CORE, B = full).

## Part 1 — Mutation testing of the frozen detectors (registry 15.1.0, detectors `9c87645`)

303 seed rules (every curated rule plus a seeded sample of active-core rules). Each mutation class is applied to
every seed to which it is applicable; a mutant is "detected" if any detector flags it and the unmutated seed is not
flagged for the same reason.

| class | mutation | mutants | detected | recall |
|---|---|---|---|---|
| M1 | threshold shifted to a value that violates the feature's physiological limits | 73 | 40 | 0.548 |
| M2 | threshold shifted ×0.5 / ×2 inside physiological limits | 303 | 1 | 0.003 |
| M3 | comparison operator flipped (< ↔ >) | 274 | 36 | 0.131 |
| M4 | unit replaced by a quantitatively different unit of the same analyte | 152 | 113 | 0.743 |
| M5 | severity tier made arithmetically derived | 1 | 0 | — (not evaluable) |
| M6 | multi-leaf rule reduced to a single ubiquitous analyte | 141 | 138 | 0.979 |
| M7 | tier order inverted / made impossible | 301 | 301 | 1.000 |
| M8 | source replaced by a random source of a non-neighbouring domain | 88 | 40 | 0.455 |

Specificity on the 303 unmutated seeds: 8 flagged (0.974). On inspection four of the eight are **true defects**
(adult haemoglobin < 12 g/dL applied with a neonate population in the iron-deficiency and haemolytic `_cur13`
rules), one is the acknowledged fixed-threshold AKI surrogate, three are SRC false positives (HHS and lactic
acidosis cited to diabetes/critical-care sources). Interpretation: static detectors are strong for what they were
built for (structural and unit defects, M4/M6/M7) and essentially blind to plausible wrong thresholds (M2) and to
operator flips that remain within physiological range (M3). This is the limitation the paper states: *static audit
is necessary, not sufficient; a plausibly wrong number passes.* A first version of M8 that drew the replacement
source from the detector's own scope table was discarded as circular (recall 0.989) and replaced by the random
swap reported above.

Defects in rules found incidentally during calibration, re-inspected against the engine and the sources before
release 15.2.0 (`eval/registry_patches/PROTOCOL_15_2_0.md`): MCV > 200 / < 20 fL and total protein > 16.6 / < 1.5
g/dL severity tiers (4 rules, retired); unit labels — ACTH thresholds numerically in pg/mL but labelled ng/mL (93
rules; the feature registry's canonical ng/mL was the wrong side, corrected to pg/mL), PTH ng/mL for pg/mL values
(14 rules), cortisol 60/230 ng/mL converted exactly to 6/23 µg/dL (19 rules); wrong sources — four pancreatitis
rules citing a GERD guideline, ten sodium/osmolality pattern rules citing a paediatric liver entry mis-keyed as a
sodium guideline. Two items first listed as defects were withdrawn on inspection: `rhabdomyolysis_v1` ("CK > 0")
carries a 5 × ULN context flag that the engine applies at run time (the static detector does not read `context` —
an audit false positive), and the β2-microglobulin inconsistency is on a different feature id (`beta_2_microglobulin_tumor`, 2 rules), left open. The four `_cur13` anaemia
rules with a neonatal population were restricted to ≥ adolescent.

## Part 3 — Application to a second LLM-authored corpus

Corpus: `llm_corpus.tsv`, SHA-256 `96d423f1dd65583692d491c37a9179e738ea6cba7f4b82c1f644e4ea58e9dca6`, 200 entities ×
2 rules = 400 rules (120 infectious, 80 haematology, 60 renal, 60 endocrine, 80 other), written under the prompt in
`llm_prompt.txt`. **Full disclosure of how the corpus was produced.** It was written by the same agent that wrote
the detectors, from memory, in one pass, without re-opening `audit.py`. Three edits were made *before* the hash was
taken and before any audit run: (i) the first pass produced 188 entities with the wrong stratum counts; four
endocrine/other entities were dropped and sixteen infectious/haematology/renal entities appended to reach the
pre-specified strata; (ii) ten cited source identifiers that did not exist in the 15.1.0 source list were replaced
by the nearest existing identifier (e.g. `cdc_tetanus_2024` → `idsa_guidelines`), because the prompt required
identifiers from that list; (iii) in conversion, 33 feature identifiers were mapped to their registry equivalents
(`FEATURE_ALIASES` in `convert_llm_corpus.py`), and population was set to all age groups except for three
explicitly neonatal entities, which is the default the Hemoglyph generator applied. 733 of 765 leaves (95.8 %)
reference a feature in the feature registry and are therefore unit-checkable; 32 are not. This is a second
LLM-authored corpus, not an independent knowledge base; it tests whether the defect classes recur under a
different generation process (one pass, no templates, no post-processing), not whether a third party would
produce them.

Densities per 100 rules (Wilson 95 % CI), same code, same tables:

| detector | 14.1.0 (paper registry; 8,890 non-template executable) | 15.1.0 (6,777) | LLM corpus (400) |
|---|---|---|---|
| R2a single ubiquitous analyte | 11.47 (10.83–12.15) | 0.01 (0.00–0.08) | 6.00 (4.06–8.77) |
| R7 arithmetic tier | 14.56 (13.84–15.30) | 0 (0–0.06) | 0.50 (0.14–1.80) |
| R9 impossible/flat tier | 0.12 (0.07–0.22) | 0.09 (0.04–0.19) | 0 (0–0.95) |
| DIR direction contradiction | 0.09 (0.05–0.18) | 0.01 (0.00–0.08) | 0 (0–0.95) |
| UNIT | 0.22 (0.15–0.35) | 0.24 (0.15–0.38) | 1.50 (0.69–3.23) |
| POP adult threshold on neonates | 0.15 (0.09–0.25) | 0.15 (0.08–0.27) | 3.25 (1.91–5.48) |
| SRC source-scope mismatch | 0.85 (0.68–1.07) | 0.80 (0.61–1.04) | 1.50 (0.69–3.23) |
| **any** | **23.62 (22.75–24.52)** | **1.28 (1.04–1.58)** | **12.75 (9.83–16.38)** |

The 14.1.0 density is dominated by the generated R2a/R7 rules that release 15 retired; the 15.1.0 density is the
calibration set (see above). Adjudication of the 51 LLM-corpus flags by the author (the same single rater as
elsewhere; verdicts are in `part3_llm_findings.json`):

* R2a (24): all are genuinely single-analyte screens on a ubiquitous analyte (CRP for cellulitis, creatinine for
  contrast nephropathy, lactate for septic shock, TSH for hypothyroidism, …). One of them has an exact Hemoglyph
  counterpart that `KEEP_SINGLE` exempts by identifier (lipase ≥ 3 × ULN for pancreatitis, Atlanta 2012); applying
  the same exemption gives 23 (5.75/100). Whether a single-analyte screen is a *defect* is a design position, the
  same one the paper takes for Hemoglyph; the number is comparable, not a verdict on the author.
* POP (13): all are haemoglobin < 12 g/dL with an all-ages population. The population is the converter's default,
  not something the prompt asked for; it is reported because it is exactly the defect found in Hemoglyph's own
  curated rules in Part 1 and arises from the same cause (no population gate written at generation time).
  Excluding POP, the density is 38/400 = 9.50/100 (7.00–12.77).
* UNIT (6): methylmalonic acid µmol/L, ACTH pg/mL, plasma metanephrines nmol/L, 17-OH-progesterone ng/dL — all
  conventional reporting units; the flags arise because the feature registry lists a single accepted unit. They
  are unit *inconsistencies between corpus and registry*, side undetermined, the same class recorded for PTH/ACTH
  in Part 1; they are not corpus errors.
* SRC (6): hepatorenal syndrome → EASL cirrhosis guideline, tumour lysis → NCCN ALL, post-streptococcal
  glomerulonephritis → KDIGO glomerular diseases. All three attributions are clinically correct; the flags are
  false positives of the domain-scope heuristic (the entity's domain label, not the source, is the odd one out).
* R7 (2): folate 2 vs 4 ng/mL and 25-OH-vitamin D 10 vs 20 ng/mL. Both pairs are the conventional thresholds;
  arithmetic coincidence, false positives.

Net: of 51 flags, 24 (R2a) + 13 (POP) are real under the paper's definitions, 6 (UNIT) are undetermined, and 8
(SRC, R7) are detector false positives — a positive predictive value of 0.73–0.84 on this corpus, consistent with
the 0.974 specificity measured in Part 1 on unmutated seeds (which are a much easier negative set).

## What the three parts say together

1. The un-audited bulk of the registry is not load-bearing at the primary cut-offs (Part 2), so the audit effort
   concentrated on the active core was aimed at the rules that matter.
2. The static detectors catch the structural defect classes they were designed for with recall 0.74–1.00 and are
   blind to plausible wrong numbers (recall ≤ 0.13) — the honest ceiling of static verification (Part 1).
3. A second LLM-authored corpus written without templates shows the same two dominant defect classes
   (single-analyte screens and missing population gates) at 6.0 and 3.3 per 100, and the detector false-positive
   pattern recurs (Part 3). The defect classes are properties of LLM-drafted rules, not of Hemoglyph's template
   generator; the fix (population gates, multi-analyte patterns, section-level locators) is generic.

## Release 15.2.0 (2026-10-28, after this study)

The defects above were corrected under a written protocol (`eval/registry_patches/PROTOCOL_15_2_0.md`): 4 tiers
retired, 4 population gates, 126 unit labels (ACTH 93, PTH 14, cortisol 19), 14 source corrections; no threshold
tuned. Frozen detectors re-run on 15.2.0: 68 flagged of 6,773 (1.00 per 100; was 1.28). Non-regression gate:
pytest 709/9; eICU every count identical to 15.1.0; NHANES all AUROCs identical; healthy 0/51 — as expected, since
none of the touched analytes fires on these panels. The paper's frozen results are unaffected.

