# Rank metrics — Hemoglyph v5.1 (labs-only) vs blind GPT-4-class LLM, pooled B3+B4+B8 (n=400 stays)

## Pooled n=400 — 596 scorable coded labels

| metric | Hemoglyph | LLM |
|---|---|---|
| recall@1 | 23.3% (20.1–26.9) | 28.2% (24.7–31.9) |
| recall@3 | 49.5% (45.5–53.5) | 50.8% (46.8–54.8) |
| recall@5 | 64.4% (60.5–68.2) | 59.6% (55.6–63.4) |
| recall@10 | 74.5% (70.8–77.8) | 65.1% (61.2–68.8) |
| MRR | 0.397 | 0.408 |
| median rank when listed | 3 | 2 |
| not listed at all | 21.1% | 34.9% |

| rank bin | Hemoglyph | LLM |
|---|---|---|
| 1 | 139 | 168 |
| 2-3 | 156 | 135 |
| 4-5 | 89 | 52 |
| 6-10 | 60 | 33 |
| absent | 152 | 208 |

## B8 only n=240 — 456 scorable coded labels

| metric | Hemoglyph | LLM |
|---|---|---|
| recall@1 | 22.6% (19.0–26.6) | 28.7% (24.8–33.0) |
| recall@3 | 48.5% (43.9–53.0) | 50.4% (45.9–55.0) |
| recall@5 | 64.3% (59.8–68.5) | 58.3% (53.8–62.8) |
| recall@10 | 73.5% (69.2–77.3) | 63.6% (59.1–67.9) |
| MRR | 0.390 | 0.406 |
| median rank when listed | 3 | 2 |
| not listed at all | 21.7% | 36.4% |

| rank bin | Hemoglyph | LLM |
|---|---|---|
| 1 | 103 | 131 |
| 2-3 | 118 | 99 |
| 4-5 | 72 | 36 |
| 6-10 | 42 | 24 |
| absent | 121 | 166 |

MRR difference (engine − LLM), bootstrap 95% CI: -0.037 to +0.014

Note: the LLM list is capped at 10 free-text entries and the engine at 25 ranked diseases; recall@10 and 'absent' therefore favour the engine structurally — recall@5 is the pre-specified primary comparison.

## LLM test–retest reproducibility (40 B8 panels, second blind read)

| metric | value |
|---|---|
| panels / scorable labels | 40 / 91 |
| Recall@5 read 1 / read 2 | 61.5% / 67.0% |
| label-level hit agreement | 85.7% |
| Cohen κ | 0.69 |
| mean Jaccard of top-5 group sets | 0.75 |
| mean Spearman ρ of shared group ranks (n=39) | 0.81 |

The engine is deterministic (test–retest agreement 100% by construction; verified by byte-identical per-stay outputs across freezes).
Reference: Isabel Pro vs GPT-4 (JAMIA Open 2025) reported GPT-4 run-to-run r² 0.34–0.44.
