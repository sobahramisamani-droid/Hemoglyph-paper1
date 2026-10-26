# Pre-registered analysis protocol — retrospective evaluation of Hemoglyph on MIMIC-IV

Version 1.0 — 2026-10-20 — Sobhan Bahrami. Freeze this file (hash + timestamp,
e.g. OSF registration or a signed git tag) **before** any MIMIC-IV data is read.
Engine version under test: Hemoglyph 1.3.1, `analyse_gidlines.py` at the commit
that contains the two dry-run fixes listed in §9 (no further engine change is
allowed after freezing; any change requires a protocol amendment with a
dated reason).

## 1. Objective
Estimate how often the laboratory-only differential produced by Hemoglyph
contains the admission's primary diagnosis, how well its probabilities are
calibrated, and whether the five-layer evidence-fusion combiner adds anything
over simpler combiners — on real, retrospectively collected hospital panels.

## 2. Design
Retrospective diagnostic-accuracy study, single-centre data (Beth Israel
Deaconess Medical Center, MIMIC-IV ≥ v2.2, PhysioNet credentialed access).
The engine is a fixed, deterministic function; no fitting on the cohort;
no hyper-parameter is changed after freezing. Reporting follows
TRIPOD-AI / DECIDE-AI items applicable to offline validation.

## 3. Population (hospital admissions, `hadm_id` level)
Inclusion
- age ≥ 18 at admission (anchor_age + (admit year − anchor_year));
- primary discharge diagnosis (`diagnoses_icd.seq_num = 1`, `icd_version = 10`)
  whose code starts with one of the prefixes in `eval/mimic/icd10_map.csv`
  (66 groups);
- ≥ 8 distinct mapped analytes with a numeric value between −6 h and +24 h of
  `admittime` (emergency-department draws before the admission order are
  included).
Exclusion: none other than the above. No manual case selection.
Sampling: all eligible admissions, or if the run time is prohibitive, a
seeded random cap per group (`--max-per-group`, seed 20261020) — the cap value
must be written here before running: **cap = 300 per group**.

## 4. Index test
Hemoglyph `ClinicalRuleEngine.interpret()` with the first value of each
analyte in the window, patient age and sex only (no notes, vitals,
medications, imaging, prior history). Analyte mapping is fixed in
`eval/mimic/itemid_map.csv` (69 itemids). `build_cohort.py` aborts if any
`d_labitems` label fails the per-itemid regex — the map cannot silently drift.

## 5. Reference standard
Primary ICD-10 code → group → the set of accepted engine `disease_id`s
(`icd10_map.csv`, column `accepted_disease_ids`). A case is a hit at rank k
if **any** accepted id appears at rank ≤ k. Known weaknesses of this
reference standard (coding errors, billing bias, diagnoses not inferable from
the first 24-h panel) are accepted and discussed, not corrected post hoc.

## 6. Outcomes
Primary: **top-3 accuracy of the `full` configuration among groups with
`lab_detectable = yes`**, with Wilson 95% CI.
Secondary: top-1, top-5, MRR; Brier score of the probability assigned to the
target; ECE (10 equal-width bins) of the top-1 probability vs observed top-1
correctness, with reliability table; the same outcomes on all groups and on
`lab_detectable = partial`; median latency.
Comparators (paired, same cases): `rule_only`, `naive_bayes`, `mean_fusion`
(definitions in `run_retrospective.py` docstring). Statistic: difference in
top-3 accuracy with 2,000-resample bootstrap 95% CI (seed 20261020) and
exact McNemar mid-p. The study is not powered for equivalence; no
superiority claim will be made unless the CI excludes 0.
Pre-specified subgroups: age (<65 / ≥65), sex, number of analytes (8–12 /
13–20 / >20), per group table. No other subgroup will be reported as
confirmatory.
Pre-specified composite (secondary only): for N17 (AKI) a hit on
`chronic_kidney_disease` is additionally counted as "renal impairment,
chronicity undetermined", because a single creatinine cannot satisfy KDIGO
criteria for either; this composite is reported separately and never
substituted for the primary outcome.

## 7. Error analysis
The first 100 top-3 misses (in cohort order) are classified by a clinician
blinded to configuration into: (A) knowledge gap, (B) fusion/ranking error,
(C) label noise, (D) not lab-detectable from the panel, (E) input/mapping
problem. Counts per class are reported.

## 8. Sample size
With 1,000 admissions and an expected top-3 accuracy of 0.60 the Wilson CI
half-width is ≈ 3 pp; with 300 per group the per-group half-width is ≈ 5.5 pp.
For the paired comparison, 10% discordance and a 3-pp difference give ≈ 80%
power at α 0.05 with n ≈ 1,000.

## 9. Dry-run on a synthetic fixture (before freezing) — engine changes
A 60-admission synthetic fixture (`eval/mimic/fixture/`, invented values in
MIMIC schema; **not** patient data) exercised the pipeline end to end and
exposed two ranking defects that were fixed before this protocol was frozen:
1. The parent-term demotion (child at ≥ 0.30 caps the umbrella term at
   0.85 × child) was applied even when the child was `insufficient`;
   Graves' (no TRAb) pushed overt hyperthyroidism (TSH 0.01, FT4 4.1;
   belief 0.89) from rank 1 to rank 6. Now requires the child to be
   `supported`.
2. The renal-chronicity rule let any "acute cause" candidate ≥ 0.45 cap AKI
   at 0.9 × cause, even when that candidate was `insufficient`
   (prior-driven sepsis entry without lactate/WBC evidence). Now requires
   `supported`.
A behavioural audit (`eval/deep_audit.py`: determinism, 200 fully normal
routine panels, 200 perturbed panels, metamorphic monotonicity) then exposed
a third defect class — hand-derived ratios computed on *normal* values:
3. R ratio (ALT/ALP) fired "cholestatic, high significance" with both enzymes
   normal; now requires ALT or ALP above its ULN (Aithal 2011 definition).
4. BUN/Cr > 20 supported AKI with BUN and creatinine both normal; now requires
   azotaemia (BUN > 20 mg/dL or creatinine above the sex-specific ULN).
5. Anion gap > 12 with normal bicarbonate supported AKI/sepsis; now requires
   bicarbonate < 22 (or AG > 20).
6. Delta ratio computed for AG 13 / HCO3 23; now requires AG ≥ 16 and HCO3 < 22.
7. De Ritis ratio fired "alcoholic pattern" with AST 30 / ALT 12; now requires
   AST or ALT above ULN.
A second audit (`eval/deep_audit2.py`) added:
8. **Unit invariance.** The rule layer canonicalised units but the Bayesian,
   fuzzy and derived-pattern layers received raw values (Hb 91 g/L scored
   against g/dL thresholds): IDA 0.85 vs 0.77, AKI 0.81 vs 0.62 between
   conventional and SI input. Observations are now canonicalised once before
   all layers; the three test panels are identical to 3 decimals afterwards.
9. Pregnancy: anion-gap pattern required HCO3 < 22, but 18–22 is
   physiological in pregnancy → a normal 28-week panel read "sepsis 0.55";
   the floor is 18 mmol/L when pregnant.
Effect on 200 normal panels (seed 20261020): top-1 probability ≥ 0.5 in
200/200 → 0/200; 'supported' candidates 4/200 → 0/200; empty differential
0/200 → 176/200. Ordering violations ('insufficient' above best 'supported')
on perturbed panels 32.7 % → 16.2 % (all entities) and 0/19 when restricted
to diagnosis-level entities (bare findings such as 'hyperkalaemia' excluded). All fixes are logged here because they
were motivated by evaluation tooling; the 50-case engine battery (50/50) and the 543-test suite were
unchanged after them. Fixture results are **not** evidence of performance
and will not be reported as such.

## 10. Reproducibility
Commands (in this order):
```
python eval/mimic/build_cohort.py --mimic-dir <hosp/> --out eval/results/cohort.jsonl --max-per-group 300
python eval/mimic/run_retrospective.py --cohort eval/results/cohort.jsonl --out eval/results/results.jsonl
python eval/mimic/metrics.py --results eval/results/results.jsonl --out eval/results/metrics.md
python eval/solver_simulation.py --real-csv eval/results/cohort_panels.csv   # OCR-solver study on real value distributions
```
Outputs are deterministic given the seed. Per-case JSON (`results.jsonl`)
is retained for audit; raw MIMIC rows are never copied out of the credentialed
environment.
