# Hemoglyph — UCI Thyroid (thyroid0387) held-out evaluation

Records with TSH measured and non-TBG/non-discordant labels: 7743; no-comment controls: 6082; median latency 291 ms.

| Task | n pos / n neg | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|
| H1 hypothyroid (E/F/G/H) vs no-comment | 655 / 6082 | **0.979** (0.974–0.983) | 96.2% (94.4–97.4) | 95.4% (94.8–95.9) |
| H2 hyperthyroid (A/B/C/D) vs no-comment | 195 / 6082 | **0.862** (0.844–0.879) | 0.0% (0.0–1.9) | 100.0% (99.9–100.0) |
| H3 primary hypothyroid (F) vs no-comment | 239 / 6082 | **0.981** (0.976–0.986) | 97.1% (94.1–98.6) | 95.4% (94.8–95.9) |
| H4 compensated hypothyroid (G) vs no-comment | 408 / 6082 | **0.982** (0.979–0.985) | 96.8% (94.6–98.1) | 95.4% (94.8–95.9) |
| H2b hyperthyroid vs no-comment, not on thyroxine | 191 / 5326 | **0.879** (0.862–0.895) | 0.0% (0.0–2.0) | 100.0% (99.9–100.0) |

Most frequent top-1 in no-comment controls: None (4301), hyperthyroidism (1214), hypothyroidism (423), graves_disease (84), co_decreased_thyroid_stimulating_hormone_with_elevated_total_thyroxine (49), co_decreased_thyroid_stimulating_hormone_with_decreased_total_thyroxine (10), co_elevated_thyroid_stimulating_hormone_with_elevated_total_thyroxine (1)

Note: the 'no comment' class includes patients on thyroxine replacement with abnormal TSH; the engine is not told the clinician's judgement that replacement is adequate, so part of the false-positive rate reflects label semantics.
