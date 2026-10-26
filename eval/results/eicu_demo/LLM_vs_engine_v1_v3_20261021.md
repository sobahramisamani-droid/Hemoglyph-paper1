# Blind LLM baseline vs Hemoglyph v1 / v3 — eICU-CRD demo (2026-10-21)

LLM = the Arena agent itself, zero-shot, labs + age/sex only, blind to coded diagnoses, ≤10 entries/stay.
Scorer: `eval/baselines/llm_zero_shot.py --score` (recall@5 over coded label groups whose key analyte was measured).

| set | stays / labels | LLM recall@5 | v1 (pre-specified) | v3 (post-hoc) |
|---|---|---|---|---|
| B3 — development set (v3 was tuned after inspecting these) | 100 / 94 | 66.0 % (55.9–74.7) | 48.9 % (39.1–58.9) | 64.9 % (54.8–73.8) |
| B4 — held-out set (stays 101–160 of the same shuffle; LLM answers written BEFORE the engine was run on them; no engine change afterwards) | 60 / 46 | 58.7 % (44.3–71.7) | 50.0 % (36.1–63.9) | 58.7 % (44.3–71.7) |

Per-group AUROC on B3 (LLM / v3): AKI .76/.80, renal .78/.77, diabetes .65/.72, DKA 1.00/.96, sepsis .66/.71.

Reading: v3 closes the gap to the LLM on the held-out set (parity, not superiority); the remaining LLM-only hits
are heart failure without BNP and sepsis without any infection marker (prior-driven guesses the labs cannot
support), plus label noise (e.g. "hypokalaemia" coded with K 5.7; "AKI" with creatinine 0.9).
Limitations: single unnamed LLM that is also the author of the v3 patch; n small; v3 post-hoc on B3; ~25–29 %
of LLM entries unmapped by the synonym table (conservative for the LLM).
Files: `llm_agent_b3_n100.json`, `b3_n100_vs_v3*.json/md`, `b4_llm_blind_n60.json`, `b4_oos_stays_n60.json`,
`b4_stays_engine_v3_n60.json`, `b4_oos_n60_vs_{v1,v3}*.json/md`. Engine freeze: `FREEZE_v3_20261021_sha256.txt`.
