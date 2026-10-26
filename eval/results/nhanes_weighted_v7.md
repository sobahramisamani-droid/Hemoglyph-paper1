# Survey-weighted NHANES re-analysis (reviewer item B3) — WTMEC2YR weights, PSU-in-stratum bootstrap CI

Unweighted values are those reported in the manuscript (same subjects, same scores). Δ = weighted − unweighted AUROC.

| target | cycle | n (pos) | unweighted AUROC | weighted AUROC (95% PSU-bootstrap CI) | Δ | weighted sens / spec @0.5 |
|---|---|---|---|---|---|---|
| diabetes | J 2017–18 | 2996 (605) | 0.946 | 0.951 (0.937–0.966) | +0.005 | 69.5 / 99.5 |
| diabetes_selfreport | J 2017–18 | 2916 (460) | 0.919 | 0.932 (0.914–0.951) | +0.013 | 70.3 / 97.7 |
| ckd | J 2017–18 | 2952 (556) | 0.959 | 0.947 (0.934–0.961) | -0.012 | 76.0 / 99.1 |
| ckd_selfreport | J 2017–18 | 2843 (131) | 0.816 | 0.744 (0.693–0.794) | -0.072 | 51.8 / 90.2 |
| anemia | J 2017–18 | 3000 (306) | 0.972 | 0.981 (0.977–0.985) | +0.009 | 99.8 / 94.8 |
| iron_deficiency | J 2017–18 | 2990 (163) | 0.989 | 0.991 (0.988–0.993) | +0.001 | 95.4 / 97.5 |
| hypercholesterolemia | J 2017–18 | 2997 (306) | 0.905 | 0.901 (0.891–0.911) | -0.004 | 100.0 / 76.4 |
| hyperuricemia | J 2017–18 | 2999 (589) | 0.943 | 0.933 (0.915–0.951) | -0.009 | 86.7 / 100.0 |
| alt_elevation | J 2017–18 | 3000 (535) | 0.872 | 0.872 (0.854–0.891) | +0.000 | 26.9 / 97.9 |
| guideline-healthy adults, any disease asserted | J | 160 | 1/160 unweighted | weighted share 0.56% | | |
| diabetes | H 2013–14 | 2998 (483) | 0.938 | 0.939 (0.920–0.957) | +0.001 | 67.5 / 99.0 |
| diabetes_selfreport | H 2013–14 | 2908 (369) | 0.914 | 0.922 (0.900–0.944) | +0.008 | 67.9 / 97.6 |
| ckd | H 2013–14 | 2958 (497) | 0.968 | 0.967 (0.959–0.975) | -0.000 | 86.1 / 99.1 |
| ckd_selfreport | H 2013–14 | 2834 (101) | 0.748 | 0.733 (0.674–0.802) | -0.015 | 53.1 / 87.8 |
| anemia | H 2013–14 | 3000 (295) | 0.994 | 0.996 (0.994–0.998) | +0.002 | 100.0 / 99.2 |
| hypercholesterolemia | H 2013–14 | 3000 (312) | 0.884 | 0.882 (0.869–0.895) | -0.002 | 97.9 / 75.6 |
| hyperuricemia | H 2013–14 | 3000 (547) | 0.958 | 0.959 (0.949–0.968) | +0.001 | 91.7 / 100.0 |
| alt_elevation | H 2013–14 | 3000 (649) | 0.880 | 0.879 (0.866–0.892) | -0.001 | 24.3 / 99.2 |
| guideline-healthy adults, any disease asserted | H | 246 | 1/246 unweighted | weighted share 0.77% | | |
| diabetes | I 2015–16 | 2999 (563) | 0.924 | 0.923 (0.909–0.937) | -0.001 | 62.8 / 99.0 |
| diabetes_selfreport | I 2015–16 | 2934 (431) | 0.898 | 0.903 (0.885–0.922) | +0.006 | 66.8 / 97.1 |
| ckd | I 2015–16 | 2960 (478) | 0.962 | 0.958 (0.949–0.966) | -0.004 | 78.0 / 99.2 |
| ckd_selfreport | I 2015–16 | 2875 (116) | 0.799 | 0.805 (0.760–0.839) | +0.006 | 51.6 / 89.9 |
| anemia | I 2015–16 | 3000 (346) | 0.983 | 0.990 (0.987–0.992) | +0.007 | 100.0 / 97.2 |
| iron_deficiency | I 2015–16 | 783 (148) | 0.972 | 0.980 (0.974–0.986) | +0.008 | 90.3 / 97.0 |
| hypercholesterolemia | I 2015–16 | 2999 (322) | 0.886 | 0.872 (0.864–0.880) | -0.015 | 100.0 / 70.8 |
| hyperuricemia | I 2015–16 | 2999 (505) | 0.955 | 0.947 (0.933–0.961) | -0.008 | 89.4 / 100.0 |
| alt_elevation | I 2015–16 | 3000 (656) | 0.877 | 0.870 (0.851–0.886) | -0.007 | 19.0 / 99.0 |
| guideline-healthy adults, any disease asserted | I | 79 | 0/79 unweighted | weighted share 0.00% | | |

Design note: the 3,000 evaluated adults per cycle are a seeded random subsample of eligible MEC participants; weights act as relative weights within the subsample. Strata with a single sampled PSU are resampled as themselves. Domain estimation (subsetting) is approximated by weighting within the evaluated set.

