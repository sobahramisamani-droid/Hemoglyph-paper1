# Physician review — instructions (v1, 2026-10-27)

**File:** `Hemoglyph_physician_review_package_v1.xlsx`; fill yellow cells only; return the .xlsx. ~4–5 h (Part 1) + ~2 h (Part 2).

**What Hemoglyph is.** A research rule engine that ranks candidate diagnoses from the numbers of one laboratory panel only (no history). Rules were transcribed from guidelines, largely AI-drafted, and never reviewed by a clinician. You are the first physician to see its outputs and rules; your verdicts are reported as given.

**Principles.** Blind to documented diagnoses and to which suggestions count as hits · judge the suggestion against the panel shown, not against the patient's true disease · no discussion with the first author until returned · no AI tools · "outside my expertise" (code 4) is a valid, reported answer.

**Part 1 — output review** (`P1_output_review`, `P1_case_summary`; full panels in `P1_panels`). 100 eICU-demo admission panels (public, de-identified), 5 engine suggestions each. Per suggestion: **1** reasonable for this panel · **2** not supported by this panel · **3** potentially harmful if acted on · **4** outside expertise; optional one-phrase reason for 2/3. Per case: **MISSED** (important diagnosis evident from the panel that the engine did not list; `none` if none) and **OVERALL** 1–5; minutes spent.

**Part 2 — haematology rule audit** (`P2_rule_audit_heme`). 27 haematology rules with their cited source. Question: does the cited source state exactly this (analyte, threshold/direction with unit, population, disease)? **CONCORDANT / DISCORDANT** require the exact sentence from the source containing the number or criterion, with page/section — a title is not a quote; the sentence must come from the URL/DOI given, not from another source. **UNRESOLVABLE** (page unreachable, abstract only, landing page, generic standard, any doubt) with one of six listed reasons. When in doubt → UNRESOLVABLE; never guess CONCORDANT. Optional last column: is the threshold clinically current?

**Reviewer sheet.** Name, specialty/board, affiliation, ORCID, email, relationship to the first author, dates, confirmation of personal completion without AI assistance.

**Afterwards.** A 5-row spot check against sources (same for every rater), then scripted analysis; results enter the paper verbatim (new §3.11 and Supplementary Note 8); you are added as co-author (*Validation; Investigation – clinical review; Writing – review & editing*).
