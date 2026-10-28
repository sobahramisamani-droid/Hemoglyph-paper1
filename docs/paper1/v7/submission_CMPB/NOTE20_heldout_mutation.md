## Supplementary Note 20 — Held-out mutation test of the static detectors (protocol committed before the run; detectors unchanged; no frozen number affected)

**Why.** Note 16 estimated detector recall on the curated / quote-verified rules of registry 15.1.0, the same registry whose flag output was inspected while the detectors' physiological bounds, direction rule and domain-neighbour table were written. Those recalls are therefore in-sample. Section 4.1 already states this; the present note measures it. The protocol (`eval/audit/PROTOCOL_HELDOUT.md`) was written and committed before `mutate_heldout.py` was run and pre-states, family by family, what the detectors were expected to miss.

**Seed pools.** *P1*: 300 rules drawn uniformly (seed 20261028) from the 6,470 executable rules of registry 15.3.0 that are neither `curated_*` nor quote-verified, i.e. AI-drafted rules never used as seeds in Note 16. P1 is only partially independent: the rules are new, but they belong to the registry lineage the detectors were tuned on. *P2*: all 400 rules of the second LLM-written corpus (Note 17), produced after the detectors were frozen and never used for calibration; P2 is the stronger test.

**Families.** Eight mutation families, none of which appears in Note 16: H1 population gate removed; H2 source replaced by another source *of the same domain*; H3 the leaf duplicated into a contradictory conjunction (`x > v` AND `x < v`); H4 a *benign* unit conversion in which unit and value are converted together (a specificity probe that must not be flagged); H5 threshold ±20 %; H6 decimal-place error (×10 or ÷10); H7 unit swapped without converting the value (the analogue of M4); H8 operator flipped (the analogue of M3). One mutant per applicable seed, first numeric leaf, only flags that were not already present on the unmutated seed count, exactly as in Note 16. The protocol pre-stated recall near zero for H1, H2, H3 and H5.

**Results.**

| family | P1 (15.3.0, AI-drafted) n | recall-any (95 % CI) | P2 (external LLM corpus) n | recall-any (95 % CI) | fired |
|---|---|---|---|---|---|
| H1 population gate removed | 300 | 0.000 (0.000–0.013) | 400 | 0.000 (0.000–0.010) | — |
| H2 same-domain source swap | 142 | 0.014 (0.004–0.050) | 280 | 0.018 (0.008–0.041) | src |
| H3 contradictory conjunction | 255 | 0.000 (0.000–0.015) | 400 | 0.000 (0.000–0.010) | — |
| H5 threshold ±20 % | 300 | 0.003 (0.001–0.019) | 400 | 0.010 (0.004–0.025) | r9, pop |
| H6 decimal error ×10/÷10 | 300 | 0.127 (0.094–0.169) | 400 | 0.155 (0.123–0.194) | r9, dir, r7 |
| H7 unit swap, value unchanged (cf. M4 0.743) | 108 | 0.806 (0.721–0.869) | 158 | 0.696 (0.621–0.763) | unit |
| H8 operator flip (cf. M3 0.131) | 255 | 0.235 (0.187–0.291) | 400 | 0.035 (0.021–0.058) | dir |
| H4 benign conversion — *specificity* | 25 | 1.000 unflagged (0.867–1.000) | 107 | 1.000 unflagged (0.965–1.000) | — |
| unmutated seeds unflagged | 300 | 0.987 (0.966–0.995) | 400 | 0.875 (0.839–0.904) | (P2: the Note 17 findings) |

**Reading.** (i) For the two families with a Note 16 analogue, recall on held-out material was within or above the in-sample figure for unit swaps (0.81 and 0.70 against 0.74) and, for operator flips, higher on P1 (0.24) but much lower on the external corpus (0.035 against 0.13): the direction detector depends on an entity having at least three other rules on the same analyte, which the 2-rules-per-entity LLM corpus almost never provides. The operator-flip recall of Note 16 should therefore be read as an upper bound for sparse registries. (ii) The decimal-place family, not anticipated when the detectors were written, is caught in only 13–16 % of cases, because a ×10 error leaves most thresholds inside the wide physiological bounds the detectors use. (iii) H1, H2, H3 and H5 are at or near zero in both pools, as pre-stated; removing a population gate, citing a plausible but wrong source, encoding an unsatisfiable conjunction and shifting a threshold by 20 % are invisible to the static layer. These are the defect classes that only the source-concordance audit (Notes 8, 15, 19) can reach, and three of them are exactly the classes found there. (iv) The benign-conversion probe was never flagged, so the unit detector responds to inconsistency, not to the mere presence of a non-canonical unit. No detector was changed in response to these results.

Scripts and inputs: Table S17.
