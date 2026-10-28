# Held-out mutation test of the static audit detectors (Supplementary Note 20)

Status: protocol written and committed **before** `mutate_heldout.py` was run. Detectors (`audit.py`) are frozen at
commit 9c87645 and are not modified by this study. Nothing in the frozen v7 benchmark or in Notes 1–19 changes.

## 1. Why

Note 16 reports the recall of the seven static detectors on eight seeded-defect families (M1–M8). Its seeds were the
curated / quote-verified rules of registry 15.1.0, and the detector thresholds (physiological bounds, the ≥3-rule
direction rule, the domain-neighbour table) were tuned while inspecting flag output on that same registry. The
recall figures in Note 16 are therefore an *in-sample* estimate. This note estimates recall on material and on
defect families that were not available when the detectors were written.

## 2. Seed pools (fixed before running)

| pool | definition | independence from detector calibration |
|---|---|---|
| **P1** | executable rules of registry **15.3.0** that are *neither* `curated_*` nor `verified_quote` (i.e. AI-drafted, never used as Note-16 seeds), with ≥1 numeric leaf; uniform random sample n = 300, `random.Random(20261028)` over the sorted rule-id list | **partial**: different rules, but the same registry lineage whose flag output was inspected while writing the detectors |
| **P2** | all 400 rules of the external LLM corpus (`llm_corpus.tsv`, Note 17; converted by `convert_llm_corpus.py`) that have ≥1 numeric leaf | **full**: produced by an external model after the detectors were frozen; never used for calibration |

Both pools are reported separately; no pooled figure is used as a headline.

## 3. Mutation families (none appears in Note 16)

Each family produces at most one mutant per seed, applied to the first numeric leaf (as in `mutate.py`). A family is
*applicable* to a seed only when its precondition holds; recall is computed over applicable seeds.

| id | mutation | precondition | detector that *should* respond | **pre-stated expectation** |
|---|---|---|---|---|
| H1 | population gate removed: `population.age_groups` → all ages | rule has a restricted age gate | none exists | **≈0 %** — a known blind spot; `pop` only tests neonate/infant *addition* |
| H2 | source swapped for another source **of the same domain** | ≥2 sources map to the entity domain | `src` cannot distinguish | **≈0 %** — `src` compares domains only, not statements |
| H3 | contradictory conjunction: leaf duplicated into `all:[x op v, x op' v]` with `op'` the opposite operator | leaf has `<,<=,>,>=` | none directly (`dir` skips analytes that appear twice) | **≈0 %** — a known blind spot |
| H4 | **benign** consistent unit conversion: unit and value both converted with the `CONV` factor | `(feature, unit)` in `CONV` with a numeric factor, and the target unit accepted for the feature | **must not flag** (specificity probe) | ≥95 % unflagged |
| H5 | threshold ±20 % (sign by RNG) | always | none (no threshold ground truth) | **≈0 %**, as M2 (±10 %) was 0.3 % |
| H6 | decimal-place error: value ×10 or ÷10 (sign by RNG) | always | `r9` / `unit` physiological bounds | moderate; depends on bound width |
| H7 | unit swapped mass↔molar **without** converting the value (M4 analogue) | as M4 | `unit` | similar to M4 (74 % on 15.1.0) |
| H8 | operator flipped (M3 analogue) | leaf has `<,<=,>,>=` | `dir` | similar to or below M3 (13 % on 15.1.0) |

H1, H2, H3 and H5 are included deliberately although they are expected to be missed: the purpose of the study is
to bound what the static layer *cannot* see, not to produce a flattering table.

## 4. Procedure

1. Load registry (P1: 15.3.0 `.br`; P2: `llm_corpus_part3` built by `convert_llm_corpus.py` into `/tmp`) and the
   feature registry; build `Audit(reg, feats)`.
2. Baseline: run all detectors on every unmutated seed; a seed already flagged for detector *d* cannot count as a
   detection of *d* after mutation (same rule as `mutate.py`: only *new* flags count).
3. For each seed × family, if applicable: substitute the mutant into the registry copy, run the detectors
   (rebuilding `Audit` for H3 and H8 because they change the per-entity direction counters), record new flags, restore.
4. Outcomes per pool × family: applicable n, detected-any n, recall-any with 95 % Wilson CI; which detector fired.
   Specificity: fraction of unmutated seeds with no flag, and fraction of H4 mutants with no *new* flag, both with
   Wilson CI.
5. Output `heldout_results.json.gz` + `RESULTS_HELDOUT.md`; the markdown table is copied verbatim into the
   supplement (Note 20).

## 5. What will and will not be concluded

- A recall for H7/H8 within the Wilson CI of M4/M3 is reported as "no evidence of in-sample optimism" for those two
  detectors; a materially lower figure on P2 is reported as such.
- H1/H2/H3/H5 recall is reported as the measured blind spot of the static layer and cited in the limitations.
- No detector will be modified in response to these results in this paper. If a result motivates a new detector, it
  is future work and will be labelled as such.
- The study does not test clinical correctness of any rule; it tests whether the audit notices a *change*.
