# Activity-guided provenance audit — results (registry 14.2.0, engine v8.2 harness; frozen v7 numbers untouched)

Protocol: `PROTOCOL.md` (frozen before any data were produced). Scripts: `activity_log.py` (Phase A logger), `core_analysis.py` (Phase A summary), `resource_core.py` (Phase B automated locator search), sample in `phase_c_sample_100.csv` (Phase C, single AI rater, verbatim quotes).

## Phase A — which rules actually drive output (label-free)

3,814 real panels (2,314 eICU stays; 1,000 NHANES 2017–18 and 500 NHANES 2015–16 participants, seed 20261027). A rule is *active* when it fired and its disease entered the top-10 differential at least once (`contrib10 ≥ 1`), *hot* when `contrib10 ≥ 10`.

| set | rules | share of 33,183 executable | anchors |
|---|---|---|---|
| active core | 364 | 1.1 % | 46 |
| hot core | 174 | 0.5 % | 32 |
| fired, never contributed | 1,627 | 4.9 % | 3 |
| dormant on these corpora | 31,192 | 94.0 % | 223 |

Composition found while classifying: 24,293 of the 33,183 executable rules (73.2 %) belong to 4,026 generated two-analyte co-occurrence pattern entities (`co_*`, entity kind `biomarker_pattern`), every one of them citing the generic `who_essential_lab_2024` landing page; 8,890 rules are attached to 2,502 disease, finding, allergy, drug-level or serology entities. In the active core 105/364 rules are such templates; a template entity sat in the frozen v7 top-5 in 62/2,314 eICU stays (2.7 %). Provenance class of the first cited source: DOI-resolved 10.4 % in the active core vs 0.8 % overall; generic landing page 54.7 % vs 90.7 %.

Registered expectations: core 800–4,000 → **not met** (364); anchors ≥ 30 % of hot core → **not met** (32/174 = 18 %).

## Phase B — automated locator search over the active core

For each active rule the registry locator was fetched (HTML/PDF), DOIs were additionally resolved through Europe PMC full text and PubMed abstracts, and the document text was searched for the rule's threshold within 160 characters of an analyte term.

| outcome | rules |
|---|---|
| threshold statement found (all leaves) | 2 |
| statement found for some leaves of a multi-leaf rule | 4 |
| statement in abstract only | 2 |
| number present, analyte term absent | 17 |
| reachable page, threshold absent (100 = CLSI EP28 shop page) | 150 |
| organisation landing page | 120 |
| locator blocked/404 (who.int, acmg.net, diabetesjournals, escardio, acc.org, easl.eu, cff.org) | 63 |
| no locator | 6 |

Registered expectation "reachable with statement 30–60 %" → **not met** (8/364 = 2.2 %).

## Phase C — fresh concordance sample (n = 100, seed 20261028, active core excluding the 200 rules of Supplementary Note 8)

Labels as in Note 8 (CONCORDANT / DISCORDANT / UNRESOLVABLE), single AI rater, every CONCORDANT or DISCORDANT label carries a verbatim quote and the document location (`phase_c_sample_100.csv`). Multi-leaf rules were labelled CONCORDANT only when every numeric leaf is stated; partially supported rules were left UNRESOLVABLE with the leaf count in the note. A strict-vs-inclusive boundary mismatch against an explicit source inequality was labelled DISCORDANT. Where the registry locator rate-limited automated access, the identical article was read from its PubMed Central deposit and this is recorded in the locator column.

| | n | CONCORDANT | DISCORDANT | UNRESOLVABLE (Wilson 95 % CI) |
|---|---|---|---|---|
| all sampled | 100 | 6 | 2 | 92 (85.0–95.9) |
| non-template rules | 70 | 6 | 2 | 62 — 88.6 % (79.0–94.1) |
| hot-core rules | 37 | 3 | 2 | 32 — 86.5 % (72.0–94.1) |
| Note 8 sample, for comparison | 200 | 1 | 15 | 184 — 92.0 % (87.4–95.0) |

CONCORDANT: ADA 2026 diabetes criteria (two rules), ADA 2026 prediabetes ranges, ADA/EASD 2024 severe-DKA tier, ADA/EASD 2024 HHS criteria (read from Fig. 2B), BSG 2021 iron-deficiency anaemia (ferritin < 30 µg/L with WHO haemoglobin cut-offs). DISCORDANT: HbA1c "> 5.7 %" prediabetes pattern (source: 5.7–6.4 % inclusive, with upper bound); CK "≥ 1000 U/L" rhabdomyolysis (source: > 1000 IU/L, a systematic review rather than a guideline). Among the 62 unresolvable non-template rules, at least 18 cite a specific document whose topic does not address the rule's analyte or disease (e.g. an ACG Crohn's guideline cited for bilirubin, a status-epilepticus guideline for creatine kinase, a well-child schedule for chloride); 30 cite only an organisation landing page; the WHO anaemia locator returns HTTP 404 (five rules).

Registered expectation "unresolvable < 92 %" → **not met** (92.0 %).

## Reading

The rules that actually produce Hemoglyph's output are a small, identifiable set (364 of 33,183), and their provenance is better than the bulk (DOI-resolved 10 % vs 0.8 %) but still mostly unauditable: 6 of 100 freshly sampled active rules could be traced verbatim to their cited source, 2 were found discordant at the boundary, and 92 could not be checked from the cited locator. The audit therefore changes the shape of the problem rather than its size: verification effort can be concentrated on a few hundred rules, and the first 100 of them show the same failure modes as the bulk sample — generic locators, topic-mismatched citations and broken URLs — plus a 73 % share of generated two-analyte templates that is disclosed here for the first time. No rule, threshold, weight or locator in the shipped registry was modified by this audit.
