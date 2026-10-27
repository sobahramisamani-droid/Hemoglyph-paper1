## Supplementary Note 15 — Activity-guided provenance audit (protocol frozen 2026-10-27 before any run; registry 14.2.0, engine harness v8.2; frozen v7 results untouched)

**Question.** Which of the 33,183 executable rules actually influence Hemoglyph's output on real panels, and whether concentrating the source audit on those rules changes the picture of Note 8.

**Phase A — activity log.** For every rule and every one of 3,814 real panels (2,314 eICU first panels; 1,000 NHANES 2017–18 and 500 NHANES 2015–16 adults, seed 20261027) the harness recorded whether the rule fired and whether its disease entered the top-10 differential. *Active core*: contributed ≥ 1 time; *hot core*: ≥ 10 times.

| set | rules | share | curated anchors |
|---|---|---|---|
| active core | 364 | 1.1 % | 46 |
| hot core | 174 | 0.5 % | 32 |
| fired, never contributed | 1,627 | 4.9 % | 3 |
| dormant on these corpora | 31,192 | 94.0 % | 223 |

Composition quantified while classifying: 24,293 executable rules (73.2 %) belong to 4,026 generated two-analyte co-occurrence pattern entities (`co_*`, entity kind `biomarker_pattern`; every one cites the generic WHO essential-diagnostics landing page); 8,890 rules are attached to 2,502 disease, finding, allergy, drug-level or serology entities. In the active core 105/364 rules are templates; a template entity appeared in the frozen v7 top-5 in 62/2,314 eICU stays (2.7 %). First-cited source class, active core vs all executable: DOI-resolved 10.4 % vs 0.8 %; organisation or generic landing page 73.7 % vs 97.3 %; unreachable 12.1 % vs 1.6 %.

**Phase B — automated locator search.** Each active rule's registry locator was fetched (HTML text or PDF via pypdf), DOIs were additionally resolved through Europe PMC full text and PubMed abstracts, and the text was searched for the rule's threshold within 160 characters of an analyte name or synonym. Outcome for 364 rules: statement found for all leaves 2; for some leaves of a multi-leaf rule 4; in abstract only 2; number present without the analyte term 17; reachable page without the statement 150 (100 of them the CLSI EP28 shop page cited as second source by template rules); organisation landing page 120; locator blocked or 404 (who.int, acmg.net, diabetesjournals.org, escardio.org, acc.org, easl.eu, cff.org) 63; no locator 6.

**Phase C — fresh concordance sample.** 100 rules were drawn (seed 20261028) from the active core excluding the 200 rules of Note 8 and labelled under the Note 8 rules by the same single AI rater. Every CONCORDANT or DISCORDANT label carries a verbatim quote and the document location; multi-leaf rules were CONCORDANT only when every numeric leaf is stated (partially supported rules remain UNRESOLVABLE with the leaf count recorded); a strict-versus-inclusive boundary mismatch against an explicit source inequality was DISCORDANT; where a publisher page rate-limited automated access the identical article was read from its PubMed Central deposit and this is recorded.

| | n | CONCORDANT | DISCORDANT | UNRESOLVABLE (Wilson 95 % CI) |
|---|---|---|---|---|
| all sampled | 100 | 6 | 2 | 92 (85.0–95.9 %) |
| non-template rules | 70 | 6 | 2 | 62 (88.6 %; 79.0–94.1) |
| hot-core rules | 37 | 3 | 2 | 32 (86.5 %; 72.0–94.1) |
| Note 8 sample | 200 | 1 | 15 | 184 (92.0 %; 87.4–95.0) |

Concordant: ADA Standards of Care 2026 diabetes criteria (two rules; the random-glucose leaf lacks the source's "classic symptoms" qualifier), ADA 2026 prediabetes ranges, ADA/EASD 2024 severe-DKA tier (pH < 7.0, bicarbonate < 10 mmol/L, β-hydroxybutyrate > 6.0 mmol/L), ADA/EASD 2024 HHS criteria (glucose ≥ 600 mg/dL, total osmolality > 320 mOsm/kg; read from Fig. 2B; the rule omits the source's two exclusion criteria), BSG 2021 iron-deficiency anaemia (ferritin < 30 µg/L with WHO haemoglobin cut-offs). Discordant: HbA1c "> 5.7 %" prediabetes pattern (source 5.7–6.4 % inclusive with upper bound); CK "≥ 1000 U/L" rhabdomyolysis (source "> 1000 IU/L", a systematic review rather than a guideline). Partially supported, left unresolvable: the SIRS-with-laboratory-support rule (8/10 leaves in Sepsis-3 Box 1 and the septic-shock lactate criterion; procalcitonin and CRP leaves absent) and a cyanide screen (lactate ≥ 8 mmol/L stated; bicarbonate leaf absent). Among the 62 unresolvable non-template rules at least 18 cite a specific document whose topic does not address the rule's analyte or disease (an ACG Crohn's guideline for bilirubin, albumin and leucocytes; an AAN status-epilepticus guideline for creatine kinase and leucocytes; the AAP well-child schedule for chloride, sodium and potassium; a myasthenia guidance for lactate), 30 cite only an organisation landing page, and five cite a WHO URL that returns HTTP 404.

**Registered expectations.** Core 800–4,000 rules: not met (364). Anchors ≥ 30 % of hot core: not met (18 %). Locator search finding the statement for 30–60 % of active rules: not met (2.2 %). Unresolvable < 92 % in the fresh sample: not met (92.0 %).

**Reading and limits.** The output-bearing part of the registry is small and identifiable, its provenance is better than the bulk's but still mostly unauditable from the cited locators, and the fresh sample reproduces the Note 8 failure modes—generic locators, topic-mismatched citations, broken URLs—while finding a small number of verbatim-concordant guideline criteria that Note 8 had not reached. "Dormant" is relative to the analyte coverage of the two corpora (about 50 analytes each); rules on analytes absent from both cannot fire. The audit is single-rater by a declared AI agent and no inter-rater reliability is claimed. No rule, threshold, weight or locator in the shipped registry was modified.
