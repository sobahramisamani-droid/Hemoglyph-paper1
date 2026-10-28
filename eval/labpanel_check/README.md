# LabPanel-Check 1.0.0 — black-box conformance benchmark for laboratory-panel readers

LabPanel-Check scores **any** reader of laboratory panels — a rule engine, a statistical model or a language model — on six
executable properties that a correct reader must satisfy, using identical, frozen, de-identified panels from public datasets.
It measures logical consistency and unsupported assertion, not diagnostic accuracy; no clinical label is involved.

| property | panels | question |
|---|---|---|
| P1 determinism | all | Does the reader give the same answer twice? |
| P2 unit invariance | 40 pairs (`P2:*` vs `REF:*`) | Same values in SI and conventional units — same top-5? |
| P3 presentation invariance | 40 pairs (`P3:*` vs `REF:*`) | Shuffled order plus five normal distractors — same top-5? |
| P4 monotonicity | 20 ladders × 3 (`P4:<stay>:1.0/1.5/2.0`) | Does the renal rank ever *fall* as creatinine rises? |
| P5 absent-analyte invariance | 40 (`P5:*`) | Is a diagnosis still asserted at rank ≤ 5 after its defining analyte was removed? |
| P6 healthy silence | 70 (`P6:*`; 40 guideline-healthy + 30 reference-positive, shuffled) | Is a disease asserted (p ≥ 0.5) in a guideline-healthy adult? |

## Run it on your reader (three steps)

1. Read `panels.json.gz` — `{panel_id: {age, sex, panel:[{analyte, value, unit}], ...}}`. Give the reader **only** `age`, `sex`
   and `panel` (ignore every other key; `target_group`, `healthy`, `reference_positive` are scorer-only fields).
2. Write `{panel_id: [{"name": "...", "probability": 0.0–1.0}, ...]}` in rank order (optional `id` for engine vocabularies,
   optional `tier` ∈ diagnosis|finding|syndrome). All 290 panel ids must be present.
3. `python3 score.py my_reads.json --label "my reader" [--second my_reads_run2.json] [--out card.json]`

`score.py` needs only the Python standard library. A free-text name is mapped to one of 31 diagnosis groups by the regular
expressions in `label_map.json`; an `id` is mapped by the entity lists. Nothing else is required.

## Reference cards (shipped)

```
python3 score.py reads_reference_engine.json.gz --label "Hemoglyph v8.2"
python3 score.py reads_reference_llm.json.gz    --label "unnamed frontier LLM (blind, 2026-10)"
```

The LLM card reproduces the manuscript exactly (Table 6, Supplementary Note 13): 8/40 (Jaccard 0.72), 10/40 (0.73), 0/20, 14/40
(strict 4/29), 4/40 healthy false assertions. The engine card, generated live at package build with engine v8.2 and registry
15.2.0, gives 35/40 (mean Jaccard 0.95; 0.96 in the manuscript run), 2/20, 3/40 (strict 1/29), 0/40 as in the manuscript and **39/40** on P2 where the manuscript reports 40/40
for the run of 2026-10-27. The single non-identical pair is `P2:508973`: the generator rounds creatinine 1.3 mg/dL to 115 µmol/L,
which the engine converts back to 1.3009 mg/dL, and that crosses the strict "> 1.3 mg/dL" leaf of rule
`reduced_gfr_single_panel_v14`; the twin is therefore not value-identical at that point (the same leaf fired in the earlier run,
but acute kidney injury was then in both top-5 sets). This is a generator artefact at a strict boundary, not a unit-handling
defect; it is left in place because the LLM read the rounded panels. All SI values in `P2:*` are rounded to two decimals
(factor < 1) or to integers (factor > 1), i.e. ≤ 0.1 % relative drift; readers with strict thresholds can legitimately differ on a
pair where a value sits exactly on a boundary — `score.py` lists every non-identical pair so such cases can be inspected.

Two caveats are inherent to the LLM card and are stated in `spec.json`: its `REF:*` readings come from an earlier session than its
`P2`/`P3` readings, so its P2/P3 Jaccard includes test–retest variability; and its P4 ladders were read with the ladder visible,
so 0/20 is not blind. The P6 detection rows are descriptive and differ from the 2026-10-21 B5 report in two places: engine CKD
10/18 (was 15/18) because registry 15.x caps single-panel CKD assertions below 0.5 per KDIGO chronicity, and LLM iron deficiency
7/8 (was 8/8) because the original script's match term was a bare string iterated character-wise — a bug fixed on 2026-10-28.
`tests/test_labpanel_check.py` asserts every number above.

## Files

- `panels.json.gz` — 290 panels (eICU-CRD demo v2.0.1 first panels; NHANES 2017-18), byte-reproducible archive
- `label_map.json` — 31 groups (entity ids + regex), renal union, P5 redundant-analyte table, P6 benign words and detection terms
- `spec.json` — machine-readable property definitions, input contract, provenance and licence
- `score.py` — the scorer (standard library only)
- `reads_reference_engine.json.gz`, `reads_reference_llm.json.gz` — the two reference readings
- `build_package.py` — how the package was assembled from the frozen benchmark (repository-dependent; not needed to score)
- `MANIFEST.sha256`

## Design notes

- Panels are drawn from the 400 eICU stays already read blind by the LLM, so no new label exposure occurred; the P5 target
  is the engine's top-ranked, criterion-met diagnosis whose single defining analyte was removed.
- The P5 *strict* row (declared after the first scoring run, 2026-10-27) excludes panels where a redundant analyte remained
  (haematocrit for haemoglobin; CK-MB/troponin T for troponin I; anion gap/pH/base excess for bicarbonate).
- P6 counts an entry as a disease assertion when probability ≥ 0.5, its `tier` is not finding/syndrome, and its name contains
  none of the benign words; readers without tiers are treated as asserting diagnoses.
- The suite tests consistency. A reader can pass every property and still be clinically wrong.

Licence: panels and reference readings CC BY-SA 4.0; `score.py` AGPL-3.0. Cite the accompanying manuscript.
