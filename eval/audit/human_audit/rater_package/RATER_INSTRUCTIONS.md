# Hemoglyph independent concordance audit — rater instructions

*Protocol: Supplementary Note 19 of the manuscript (frozen 2026-10-28, before any rater was approached). This sheet paraphrases it; the protocol text governs.*

## What you are asked to do

You will receive `Hemoglyph_human_audit_rater_form.xlsx` with 100 rows. Each row is one executable rule from an openly licensed laboratory-interpretation rule base, together with the source the rule base cites for it. For every row, decide whether the **cited source actually states the rule as encoded**, and record a verdict with a verbatim quote.

You are **not** asked whether the rule is medically reasonable, whether a better source exists, or whether the threshold is the one you would use. The question is narrower: *does this source, at this locator, say this?*

## Columns you fill in

| Column | What to enter |
|---|---|
| **VERDICT (C / D / U)** | **C** — the source states the same analyte, operator, threshold, unit and population as the rule, or an exact equivalent after unit conversion (e.g. 126 mg/dL = 7.0 mmol/L glucose). **D** — the source states a *different* threshold, operator, unit or population, or explicitly does not support the rule. **U** — you cannot find, in the cited source at the cited locator, a statement that settles the question (document unreachable, paywalled, landing page only, or the statement is simply not there). |
| **verbatim quote supporting verdict** | Required for every **C** and **D**: copy the sentence or table cell from the source, unchanged. For **U**, write what you reached (e.g. "landing page only", "paywall", "full text reached, no threshold given"). |
| **page or section** | Page number, table number or section heading where the quote is. |
| **comment** | Optional: anything that would help an adjudicator. |
| **minutes spent** | Approximate time on the item, to the nearest minute. |

## Rules of the audit

1. Use **only the cited source at the cited URL/DOI**. If the URL is a landing page, you may navigate within the same document (table of contents, PDF of the same guideline), but not to a different publication. If the page is paywalled and you have institutional access, you may use it; note this in the comment.
2. Spend **at most 15 minutes** per item. If the statement cannot be located within that time, record **U** with a note.
3. Rate every item **independently**; do not discuss items with the other rater until both forms have been returned.
4. Do not skip items and do not reorder rows. Do not edit any column other than the five above.
5. You have not seen, and will not be shown until your form is returned, the verdicts previously given by the AI rater for the same rules.
6. Return the form by e-mail to the corresponding author. The file's SHA-256 will be recorded on receipt and the raw verdicts will be published alongside the consensus.

## What happens afterwards

Disagreements between the two raters are resolved by discussion; items that remain unresolved go to a third clinician. The pre-specified outcomes are the discordance proportion among resolvable rules (D / (C + D)) with Wilson intervals, the unresolvable proportion, and Cohen's κ between raters and between each rater and the sealed AI verdicts. No rule will be edited and no engine component tuned on the basis of your verdicts before the audit result is published.

## Time and acknowledgement

Expected total effort: 8–15 hours per rater. Raters are named in the Acknowledgements (or, if they prefer and have contributed substantively to interpretation, invited as co-authors of the audit report) and receive no payment unless stated otherwise in writing before the audit begins.

*Contact: Sobhan Bahrami — sobahramisamani@gmail.com*
