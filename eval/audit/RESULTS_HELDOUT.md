# Held-out mutation test — results (Note 20)

Protocol: `PROTOCOL_HELDOUT.md` (committed before this run). Detectors frozen (audit.py @ 9c87645).

**P1 registry 15.3.0, AI-drafted non-curated rules** — seeds 300; unmutated seeds unflagged 0.987 (95% CI 0.966–0.995)

| family | applicable n | detected (any) | recall-any | 95% Wilson CI | detector(s) that fired |
|---|---|---|---|---|---|
| H1 | 300 | 0 | 0.0 | 0.0–0.013 | — |
| H2 | 142 | 2 | 0.014 | 0.004–0.05 | src 2 |
| H3 | 255 | 0 | 0.0 | 0.0–0.015 | — |
| H4 (benign conversion; must NOT flag) | 25 | 0 | specificity 1.0 | 0.867–1.0 | — |
| H5 | 300 | 1 | 0.003 | 0.001–0.019 | r9 1 |
| H6 | 300 | 38 | 0.127 | 0.094–0.169 | dir 21, r9 26 |
| H7 | 108 | 87 | 0.806 | 0.721–0.869 | unit 87 |
| H8 | 255 | 60 | 0.235 | 0.187–0.291 | dir 60 |

**P2 external LLM corpus (Note 17)** — seeds 400; unmutated seeds unflagged 0.875 (95% CI 0.839–0.904)

| family | applicable n | detected (any) | recall-any | 95% Wilson CI | detector(s) that fired |
|---|---|---|---|---|---|
| H1 | 400 | 0 | 0.0 | 0.0–0.01 | — |
| H2 | 280 | 5 | 0.018 | 0.008–0.041 | src 5 |
| H3 | 400 | 0 | 0.0 | 0.0–0.01 | — |
| H4 (benign conversion; must NOT flag) | 107 | 0 | specificity 1.0 | 0.965–1.0 | — |
| H5 | 400 | 4 | 0.01 | 0.004–0.025 | pop 3, r9 1 |
| H6 | 400 | 62 | 0.155 | 0.123–0.194 | dir 16, r7 2, r9 53 |
| H7 | 158 | 110 | 0.696 | 0.621–0.763 | unit 110 |
| H8 | 400 | 14 | 0.035 | 0.021–0.058 | dir 14 |

Notes. Recall-any counts a mutant as detected when at least one detector raises a flag that was not present on the
unmutated seed. H4 applicability follows the amended definition (protocol §6). P2 unmutated-seed flags (12.5 %) are the
Part-3 findings of Note 17, not false positives of this study. Comparison with Note 16 (15.1.0 curated seeds): M4 unit
swap 0.743 vs H7 0.806 (P1) / 0.696 (P2); M3 operator flip 0.131 vs H8 0.235 (P1) / 0.035 (P2); M2 ±10 % 0.003 vs
H5 ±20 % 0.003 / 0.010. H1, H2, H3 are at or near zero in both pools, as pre-stated.
