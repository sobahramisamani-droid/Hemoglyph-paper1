# Verified consensus arm — 400 blind eICU stays (fusion rule fixed in PROTOCOL.md before computation)

| Arm | recall@1 | @3 | @5 | @10 | top-5 unsupported (criterion groups) |
|---|---|---|---|---|---|
| engine_v7 | 24.0 | 47.0 | 60.7 | 72.0 | 233/1518 (15.3 %) |
| llm_raw | 28.2 | 50.8 | 59.6 | 65.1 | 179/1512 (11.8 %) |
| F_rrf_verified | 21.8 | 46.6 | 61.2 | 76.3 | 209/1581 (13.2 %) |
| G_append_verified | 19.1 | 46.1 | 59.7 | 76.2 | 244/1500 (16.3 %) |

Paired differences (stay-clustered bootstrap, 4000 reps), points:
- F_minus_engine: @1 -2.2* (-4.9 to +0.5, p=0.1160); @3 -0.3* (-3.2 to +2.7, p=0.8520); @5 +0.6* (-2.2 to +3.4, p=0.7710); @10 +4.5* (+2.2 to +6.8, p=0.0005)  (*midpoint of CI; point estimate in table)
- F_minus_llm: @1 -6.4* (-9.7 to -3.2, p=0.0000); @3 -4.2* (-7.1 to -1.4, p=0.0040); @5 +1.7* (-1.2 to +4.7, p=0.2665); @10 +11.3* (+7.9 to +14.8, p=0.0000)  (*midpoint of CI; point estimate in table)
- G_minus_engine: @5 -1.0* (-3.1 to +1.2, p=0.3635)  (*midpoint of CI; point estimate in table)

F top-5 entries: 1836 from the engine list, 34 admitted via the LLM and the criterion only.

recall@5 by label stratum (criterion status in the panel):
| stratum | n | engine | LLM | F | G |
|---|---|---|---|---|---|
| criterion_met | 357 | 77.9 | 81.0 | 82.1 | 77.9 |
| no_criterion | 131 | 51.9 | 43.5 | 42.7 | 46.6 |
| criterion_not_met | 107 | 15.0 | 7.5 | 15.0 | 15.9 |
| analyte_missing | 1 | 0.0 | 100.0 | 0.0 | 0.0 |

Registered predictions: F recall@5 63-67 %; F recall@1 >= 29 %; F top-5 unsupported <= 15.3 %; G within 1 point of F at k=5; F < 62 % => not complementary.
