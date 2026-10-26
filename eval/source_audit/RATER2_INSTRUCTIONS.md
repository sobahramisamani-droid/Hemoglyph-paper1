# Instructions for Rater 2 (blind) — Hemoglyph source-concordance audit

Time: ~3 h. Do NOT ask the first author about any rule before finishing.

For each of the 200 rows in `sample_200_BLIND_for_rater2.xlsx`:
1. Read `expression` + `population` + `disease_id` (analyte, operator, threshold+unit, population, disease).
2. Open the source locator(s) in `source_urls` / `source_ids`. Spend ≤5 minutes per rule.
   If a DOI is paywalled, use the abstract or any freely accessible full text (PubMed, PMC); do not use other sources.
3. Write ONE of three labels in `rater2_label`:
   - CONCORDANT — the source states this analyte, this direction/threshold (same unit or exact conversion), this population and this disease.
   - DISCORDANT — the source clearly says something different (different threshold/definition) OR the source is about another condition (attribution error).
   - UNRESOLVABLE — you cannot find the statement: page not reachable, abstract only, generic standard (WHO list, CLSI document), landing page, or any doubt.
   Rule: when in doubt → UNRESOLVABLE. Never guess CONCORDANT.
4. Optional short note in `rater2_note` (e.g. "403", "abstract only", "guideline is about hyponatraemia").
Save and return the file unchanged in structure. Thank you.
