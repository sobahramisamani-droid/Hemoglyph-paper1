# LabPanel-Check on a named open-weights model — protocol (frozen before the run)

**Written 2026-10-28, before any panel was read by the model.** Purpose: add to Table 6 a third, fully reproducible column —
a small open-weights model that anyone can download and run on a laptop CPU — next to the engine and the unnamed frontier LLM.
The column is a *reproducible floor*, not a representative of frontier capability, and it does not touch the n = 400 comparison
(Table 5), which is not re-run.

## Model and runtime (fixed)

| item | value |
|---|---|
| model | Qwen2.5-1.5B-Instruct, official GGUF release by the Qwen team (Apache-2.0), file `qwen2.5-1.5b-instruct-q3_k_m.gguf`, SHA-256 `58cb5c05ecef48e82961f1a2be6544145ea26136f69dddda4bbbd092f0e4b993` (amended from Q4_K_M before any result was examined: the Q4_K_M file, 1.12 GB, was killed by the 2 GB sandbox's out-of-memory handler after 10 panels when locked in RAM and thrashed when memory-mapped; Q3_K_M, 0.92 GB, is the largest official quantisation that fits; its 10 Q4_K_M readings were discarded) |
| runtime | llama.cpp build b11966 (`llama-server`, CPU only, 2 threads, model locked in RAM), OpenAI-compatible chat endpoint, model's own chat template |
| decoding | temperature 0 (greedy), top-k 1, seed 20261028, max 400 new tokens, context 1024 (amended from 2048 before any result was examined: with 2048 the 2 GB sandbox thrashed its page cache and generation fell from 12 to 1.3 tokens/s; the longest prompt is ≈ 410 tokens, so 1024 is sufficient; the 20 panels read under the first setting were discarded and the run restarted from the first panel) |
| hardware | 2 vCPU Intel Xeon 2.60 GHz, 2 GB RAM (same sandbox as the manuscript's timings) |

## Inputs and prompt (fixed)

Exactly the 290 panels of `panels.json.gz` (LabPanel-Check 1.0.0; MANIFEST unchanged). The model sees only `age`, `sex`, `panel`.

- `REF:*`, `P2:*`, `P3:*`, `P4:*`, `P5:*` (eICU first panels): prompt **P1 verbatim** from the manuscript's LLM arm
  (Supplementary Note 2): *"You are a clinical laboratory medicine expert. Given the following laboratory panel of an adult ICU
  patient (first 24 h of admission), list the most likely diagnoses or clinically important laboratory syndromes this panel
  supports. Return ONLY JSON of the form {"diagnoses":[{"name":"...","probability":0.0-1.0}]} with at most 10 entries, ordered by
  probability. Do not include explanations. Patient: {age}-year-old {sex}. Panel: {analyte value unit, …}"*
- `P6:*` (NHANES community adults): the same prompt with "an adult ICU patient (first 24 h of admission)" replaced by
  "an adult from a community health survey", because the ICU framing presupposes illness. This substitution is the only change.

Panels are presented one per request, in the file order, each with a fresh context (no history). Panel values are formatted
`analyte value unit` with underscores replaced by spaces, exactly as the engine's exporter did for the frontier arm.

## Output handling (fixed)

The first JSON object in the reply is parsed; entries are taken in listed order with their stated probability (clamped to
[0, 1]; missing → 0.5). If no JSON can be parsed, the reply is retried once with the same settings; if still unparsable the panel
is scored as an empty list (counted and reported). No manual editing of any reply.

## Scoring (fixed)

`score.py` unchanged, `--label "Qwen2.5-1.5B-Instruct Q4_K_M (greedy)"`. Determinism (P1) is tested by a complete second pass over
the 40 `REF:*` panels (`--second`). All six property rows are reported as the scorer prints them.

## Pre-stated expectations (so that the result cannot be shaped afterwards)

1. P2 unit invariance will be well below the engine's 40/40 and probably at or below the frontier LLM's 8/40.
2. P5 absent-analyte assertion and P6 healthy false assertions will be higher than the engine's (3/40, 0/40).
3. Greedy decoding will make P1 determinism near-perfect — which illustrates that determinism alone says nothing about correctness.
4. Parsing failures will occur; they are reported, not repaired.

## What will be written into the manuscript

One extra column in Table 6, one sentence in Section 3.7 and one in Limitations stating that the open model is a small
reproducible floor; the file names here appear only in the Reproducibility map. No number elsewhere changes.
