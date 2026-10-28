# LabPanel-Check on a named open-weights model — results (run 2026-10-28, scored with the unchanged `score.py`)

Model Qwen2.5-1.5B-Instruct, official Q3_K_M GGUF (SHA-256 `58cb5c05…e4b993`), llama.cpp b11966, CPU, greedy decoding,
protocol `PROTOCOL_OPEN_MODEL.md` (two amendments, both made before any result was examined and both about memory, not
about the model's behaviour). Files: `reads_qwen25_1p5b.json` (290 readings), `reads_qwen25_1p5b_raw.json` (verbatim replies),
`reads_qwen25_1p5b_REF_run2.json` (second pass over the 40 REF panels), `card_qwen25_1p5b.json` (scorer output).
Wall time 1 h 50 min for 330 readings on 2 vCPU (≈ 18–20 s per panel).

## Conformance card (as printed by `score.py`)

| property | open model | engine v8.2 | frontier LLM |
|---|---|---|---|
| P1 determinism, REF panels read twice, identical lists | 39/40 | 50/50 (byte-identical) | κ 0.69 (40 re-read stays) |
| P2 unit invariance: top-5 identical (mean Jaccard), 40 pairs | 12/40 (0.65) | 40/40 (1.00) | 8/40 (0.72) |
| P3 presentation invariance: top-5 identical (mean Jaccard), 40 pairs | 0/40 (0.44) | 35/40 (0.96) | 10/40 (0.73) |
| P4 creatinine ladders with a renal-rank fall, 20 | 2/20 | 2/20 | 0/20 (step visible) |
| P5 target still at rank ≤ 5 after its defining analyte removed, 40 | 3/40 | 3/40 | 14/40 |
| P5 strict subset (29) | 3/29 | 1/29 | 4/29 |
| P6 guideline-healthy adults with a disease asserted at p ≥ 0.5, 40 | 26/40 | 0/40 | 4/40 |

## Parsing failures (pre-stated expectation 4) — these change how the rows must be read

28 of 290 replies (9.7%) contained no parsable JSON after one retry (typically `{"Hypokalemia","probability":0.95}` — the
`"name"` key dropped) and were scored as empty lists, as the protocol requires. Their distribution is not uniform:

| stratum | panels | unparsable |
|---|---|---|
| REF / P2 | 80 | 0 |
| P3 | 40 | 1 |
| P4 (60 ladder steps) | 60 | 2 (one ladder) |
| P5 | 40 | 0 |
| P6 healthy | 40 | 14 |
| P6 reference-positive | 30 | 11 |

Consequences, stated so that the card is not over-read:
- **P6.** Among the 26 healthy panels that produced a parsable list, **26/26** asserted at least one disease at p ≥ 0.5. The
  26/40 in the card is therefore a floor; the true false-assertion rate of this reader on healthy adults is at or near 100%.
- **P5.** 3/40 is *not* evidence of restraint comparable to the engine's 3/40: the model asserts few diseases per panel
  (mean 7.1 entries, many of them electrolyte findings), so the removed target was rarely in its top five to begin with.
  The property measures unsupported persistence, and a reader that rarely names the target cannot persist in it.
- **P4.** 2/20 includes one ladder with an unparsable step; the other violation is genuine (renal rank fell at ×2.0).
- **P1.** Greedy decoding on CPU was not perfectly deterministic (39/40): one REF panel changed between passes.

## Reading

The open model satisfies none of the invariants the engine satisfies and is worse than the frontier LLM on presentation
invariance (0/40 vs 10/40) and healthy silence (≥ 26/40 vs 4/40), while being nominally better on unit invariance (12/40 vs
8/40) — a comparison that the frontier figure's cross-session test–retest component and the open model's small output sets make
uninformative. The column's value is that **anyone can reproduce it on a laptop in two hours** with a hash-identified model
and a frozen prompt, which is what the frontier column cannot offer. It is a floor for the class "small open instruct model,
zero-shot, no retrieval", not a statement about frontier capability.

No panel, prompt, scorer line or threshold was changed after the first reading. Nothing from this run feeds back into the engine.
