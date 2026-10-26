# Hemoglyph — UCI Thyroid (thyroid0387) held-out evaluation

Records with TSH measured and non-TBG/non-discordant labels: 7743; no-comment controls: 6082; median latency 332 ms.

| Task | n pos / n neg | AUROC (95% CI) | sens @0.5 | spec @0.5 |
|---|---|---|---|---|
| H1 hypothyroid (E/F/G/H) vs no-comment | 655 / 6082 | **0.984** (0.979–0.987) | 96.9% (95.3–98.0) | 95.4% (94.8–95.9) |
| H2 hyperthyroid (A/B/C/D) vs no-comment | 195 / 6082 | **0.798** (0.783–0.814) | 67.2% (60.3–73.4) | 80.5% (79.5–81.5) |
| H3 primary hypothyroid (F) vs no-comment | 239 / 6082 | **0.995** (0.989–0.998) | 99.2% (97.0–99.8) | 95.4% (94.8–95.9) |
| H4 compensated hypothyroid (G) vs no-comment | 408 / 6082 | **0.982** (0.979–0.985) | 96.8% (94.6–98.1) | 95.4% (94.8–95.9) |
| H2b hyperthyroid vs no-comment, not on thyroxine | 191 / 5326 | **0.820** (0.804–0.835) | 67.5% (60.6–73.8) | 83.0% (82.0–84.0) |
| H2c hyperthyroid (A/B/C/D) vs no-comment, overt entities only (amendment 4) | 195 / 6082 | **0.932** (0.911–0.949) | 55.4% (48.4–62.2) | 99.2% (98.9–99.4) |

Most frequent top-1 in no-comment controls: None (4301), subclinical_hyperthyroidism (1136), hypothyroidism (415), hyperthyroidism (216), primary_hypothyroidism (8), graves_disease (5), co_elevated_thyroid_stimulating_hormone_with_elevated_total_thyroxine (1)

Note: the 'no comment' class includes patients on thyroxine replacement with abnormal TSH; the engine is not told the clinician's judgement that replacement is adequate, so part of the false-positive rate reflects label semantics.
