# B5 — NHANES 2017-18 blind specificity / detection, LLM (Arena agent, blind) vs Hemoglyph (current engine)

70 adults: 40 guideline-healthy + 30 reference-positive, shuffled; reader saw labs + age/sex only.

| | LLM | Hemoglyph |
|---|---|---|
| False assertions in healthy (any disease p ≥ 0.5) | 4/40 (10%) | 0/40 (0%) |
| Detected diabetes (p ≥ 0.5) | 16/16 | 13/16 |
| Detected ckd (p ≥ 0.5) | 13/18 | 15/18 |
| Detected anemia (p ≥ 0.5) | 12/13 | 13/13 |
| Detected iron_deficiency (p ≥ 0.5) | 8/8 | 7/8 |
| Detected hypercholesterolemia (p ≥ 0.5) | 7/7 | 7/7 |

LLM false assertions: 94852: low hdl; 95321: low hdl; 95002: hypertriglyceridemia, low hdl; 93970: hyperferritinemia

Engine false assertions: 

Limitations: the blind reader is the same agent that developed the engine; n small; 'finding' entities (e.g. isolated mild hypochloraemia) are not counted as disease assertions for either system.
