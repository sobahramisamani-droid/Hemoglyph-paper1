# Prompt sensitivity — 40 B8 panels, 91 scorable labels

| arm | recall@1 | recall@3 | recall@5 | recall@10 | absent |
|---|---|---|---|---|---|
| LLM P1 read 1 | 26.4% | 51.6% | 61.5% | 69.2% | 30.8% |
| LLM P1 read 2 | 28.6% | 54.9% | 67.0% | 71.4% | 28.6% |
| LLM P2 (alt prompt) | 25.3% | 48.4% | 61.5% | 74.7% | 25.3% |
| engine v5.1 | 24.2% | 51.6% | 69.2% | 78.0% | 15.4% |
| engine v7 | 19.8% | 45.1% | 64.8% | 73.6% | 16.5% |
| engine v7 two-tier | 29.7% | 65.9% | 72.5% | 83.5% | 16.5% |

Label-level recall@5 agreement: P1r1 vs P1r2 85.7%; P1r1 vs P2 89.0%; P1r2 vs P2 83.5%.

P2 = 'ICU attending writing the admission problem list' framing (b8_llm_prompt2_n40.json); P1 = original laboratory-medicine prompt. Same model class, same blinding, 2026-10-25. n = 40 panels: exploratory, indicates the order of magnitude of prompt-induced variation only.
