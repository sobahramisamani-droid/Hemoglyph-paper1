# Disclosure and Limitations text for Paper 1 (v5.3, registry 13.3.0) — drafted 2026-10-23, updated 2026-10-24

Status: ready-to-paste English text. It replaces the current Methods paragraph "Knowledge base" (disclosure) and the
Limitations paragraph of `Paper1_Hemoglyph_npj_EN.md`. The manuscript text (Methods, Discussion, Limitations) now carries the v5.3 numbers; items still awaiting the physician audit (A1) are marked PENDING and will be filled verbatim when the
ext11 chain completes. Nothing here softens a weakness; reviewers find these points anyway and the paper is stronger
when it states them first.

---

## A2 — Provenance of the knowledge base (Methods → "Knowledge base")

The two registries were **generated with the assistance of a large language model** and curated by the first author
(a non-physician developer), not by an expert panel. Concretely: disease entities, rule thresholds, reference
intervals and source citations were drafted by an LLM from prompts that named the governing guideline or textbook
(ADA, KDIGO, ATA, AASLD, ACR, CLSI, Tietz), then screened by code-level validators (schema, unit, monotonicity,
duplicate and dead-rule checks) and spot-corrected by the author. Of the 6,750 entities, about 60 % are automatically
generated `biomarker_pattern` entities that describe single-analyte deviations; the **operational stratum on which all
results in this paper rest is smaller: 186 diseases and 851 rules that surfaced in any top-5 of the eICU held-out
cohort**. Both strata are released verbatim (Brotli-compressed JSON, Zenodo DOI to be minted by the author at release) so that any
reader can audit any rule against its cited source.

Because an LLM-drafted knowledge base can carry plausible but wrong thresholds and fabricated citations, we treat it
as an untrusted artefact and report three independent checks rather than asserting correctness: (i) a
**pre-specified physician audit of 100 executable rules** (60 operational, 40 whole-registry; 3-level verdict,
severity A–D; form and sample fixed before results; `eval/human/A1_*`) — result: PENDING — physician audit not yet returned at the v5.3 freeze (2026-10-24); will be reported unchanged [error rate, Wilson CI, by
stratum; "not yet returned" if pending at submission]; (ii) **external behaviour** on 14,400 real patients across
five independent data sources with coded, engine-independent labels; (iii) a **fabrication-provocation battery**
(200 panels) in which the engine must not assert any diagnosis unsupported by the input (200/200 in v5.1).
Where the audit finds errors we will report them unchanged in this version and correct them in the next
registry release with a changelog; thresholds were **not** edited after seeing held-out results (SAP Amendments 2–9). One such
correction already exists: the external case-vignette probe exposed a defect class (76 pathogen-specific infectious entities
proposable from routine analytes alone); it is fixed in registry 13.2.0 *after* the v5.2 freeze, with zero change on the
400-panel blind comparison, and is reported as a post-audit version (SAP Amendment 10). A subsequent ten-class scan of the whole
registry (SAP Amendment 12) found further AI-curation defects — sex-blind thresholds on sex-dimorphic analytes (≈550 rules), mislabelled
troponin units, risk-factor rules on acute entities, 63 etiologic entities proposable from routine analytes, adult thresholds applied to
infants, and 57 over-stated specificity claims — repaired in registry 13.3.0 (B8 294/456 vs 293/456 before; PMC unchanged); both
patches are activated together after the freeze as v5.3 and reported next to v5.2.

The LLM used to draft the registries is not the LLM used as comparator (Methods, "Comparators"); the registries were
frozen (v13.1.0, SHA-256 in `FREEZE_v5.2_*.txt`) before any held-out evaluation.

## A4 — Limitations (Discussion)

1. **Knowledge-base provenance.** The registries were LLM-drafted and single-author curated. The physician audit
   covers 100 of 34,548 rules (0.3 %; 33,230 executable) and a stratified share of the 851 operational rules (count fixed in the A1 form); it estimates the error rate but
   does not certify the registry. Systematic errors that affect many rules at once (for example a wrong unit
   convention for one analyte) would propagate silently and are only partly caught by the external evaluations.

2. **Reference standards.** eICU labels are routine ICU problem-list codes, not adjudicated diagnoses: they
   under-record laboratory diagnoses (depressing measured precision), and a 100-stay audit of our regex label map
   found 2 misses in 150 positives (sensitivity 98.7 %, 0 false positives; `label_audit_n100.md`). NHANES
   guideline labels share inputs with the engine (circularity; mitigated by also scoring self-report labels, where
   discrimination is lower — CKD AUROC 0.79, hypercholesterolaemia specificity 77 %). UCI thyroid "no comment"
   records include treated patients. ILPD labels are hospital-assigned.

3. **Public demo subsets only.** eICU-CRD demo (2,314 stays, 186 hospitals) and MIMIC-IV demo were used; the full
   databases require credentialing the author could not complete from Iran. The demo is a random sample, but the
   sample size limits per-diagnosis estimates (12 of 62 groups have < 20 positives) and precludes
   hospital-level clustering analyses beyond what Table S2 reports.

4. **Retrospective, non-interventional.** No claim is made about clinical impact, reader performance, time saved
   or harm. The engine was run once per stay on the admission panel (plus the pre-specified context and
   trajectory arms); real use involves iterative ordering that we did not simulate.

5. **LLM comparator (exploratory, self-run).** The comparator is a GPT‑4‑class model accessed through the Arena.ai
   agent platform; vendor, version, temperature and seed were not exposed, the same agent produced the LLM answers
   and scored both arms with a fixed keyword map, and the author cannot purchase API access to a named model. We
   mitigate with (i) pre-specified keys and a blinded protocol, (ii) a 40-panel test–retest (κ 0.69, Jaccard 0.75),
   (iii) releasing all 400 panels, answers and the scorer so that anyone can rerun a named model
   (`labbench_score.py`), and (iv) the published GPT‑4 results of Bhasuran et al. on the 50 PMC-Patients cases
   as an external anchor. The result (recall@5 64.4 % vs 59.6 %, McNemar p = 0.009) should be read as "a
   deterministic rule engine with labs only is in the same range as a frontier LLM on this task", not as
   superiority over any particular product.

6. **Input modality.** Hemoglyph interprets numbers; it does not read the narrative. On the Bhasuran vignettes the
   syndrome-level top‑5 rises from 44 % (end-to-end prose parser) to 68 % (author-structured panel), so in the
   application the free-text parser, not the reasoning layer, is the limiting component for narrative input; the
   parser was built for tabular laboratory reports and is evaluated as such (OCR batteries). Symptoms and
   vital signs are deliberately out of scope of this paper (Paper 2).

7. **Developer-run evaluation.** All evaluations were performed by the developer. The compensating measures are
   the pre-registered SAP with dated amendments, frozen artefacts with SHA-256, deterministic engine (byte-identical
   outputs across freezes), release of every per-stay output, and the open benchmark package (LabBench v1) with a
   system-agnostic scorer. An independent replication has not yet occurred.

8. **Calibration and thresholds.** Raw probabilities were over-confident (ECE 0.161); the reported calibration
   (ECE 0.002, Brier 0.040) uses isotonic recalibration fitted on the development split and is validated on
   held-out stays only for groups with ≥ 20 positives. Decision-curve net benefit is computed against problem-list
   labels and therefore inherits limitation 2.

9. **Generalisability.** Three of five data sources are US (eICU, NHANES, MIMIC demo); the Persian-language
   OCR/parsing path was validated on synthetic and author-supplied reports only. Performance in Iranian laboratories
   with local reference intervals, units and reporting styles is the subject of the planned prospective study.

10. **Pre-analytical and OCR errors** were tested with synthetic injections and 200 real-format reports, not on a
    consecutive sample of scanned reports from a real laboratory; the OCR stage uses a cloud vision model and is
    not part of the offline claim.

## A5 — Mechanical source-provenance audit and registry 13.4.1 (added 2026-10-24)

**What was done.** After the v5.3 freeze every source record of the release registry was audited by script
(`eval/registry_source_verify.py`): each DOI was resolved through the Crossref API and its title compared with the
registry record (token-overlap, with two documented manual adjudications); each URL was probed; the result is
Supplementary Data 1 (`Supplementary_Data_1_sources_13.4.1.xlsx`, one row per source, 781 rows) and
`eval/results/source_verification_13.4.1.json`.

**What was found (781 source records).**

| status | n | meaning |
|---|---|---|
| verified / verified_manual | 110 + 2 | DOI resolves to the intended document |
| url_only | 63 | no DOI; a specific document URL is reachable (includes CLSI EP28, cited by 27,582 executable rules) |
| generic_landing_page | 533 | no DOI; URL is an organisation or catalogue landing page — a family of documents, not one citable item |
| url_unreachable | 39 | not confirmable from the verification host (acog.org 15, who.int, easl.eu, eular.org … mostly bot-blocking) |
| no_locator | 34 | neither DOI nor URL (25 original + 9 removed below) |

**Fabricated locators.** Nine DOIs were wrong: six resolved to unrelated articles (`acmt_cyanide_2021`,
`acmt_beta_blocker_2017`, `aga_ple_2022`, `easl_amatoxin_2017`, `nhsn_taco_2021`, `ese_dm_insipidus_2022`) and three do
not exist (`acep_toxicology_consensus`, `clsi_pseudohyponatremia_2020`, `vpa_hyperammonemia_2020`). This is the classic
citation-hallucination failure of the drafting model and was not caught by single-author curation. **Registry 13.4.1**
(`release/registry_13.4.1/`, provenance-only patch, rule logic byte-identical to 13.4.0) removes the nine locators,
keeps the organisation/title/year, records the removed string for audit, and flags the 28 executable rules that cite
only those sources as `evidence_tier = unverified_source`. Five of those 28 (methanol and ethylene-glycol osmolal-gap
rules; three valproate-hyperammonaemia rules) belong to entities that appeared in at least one eICU top-5 list, so the
reported tables are not entirely free of rules with an invalid locator; the thresholds themselves are textbook values.
No numbers in the paper change (13.3.0 remains the evaluated registry); the 13.3.0 source table contains the same nine
records, which is disclosed here rather than silently corrected.

**Rule-level reading (13.4.1, 33,170 executable rules).** 255 (0.8 %) cite ≥ 1 DOI-verified source; 30,785 (92.8 %)
cite ≥ 1 specific document — but this figure is dominated by CLSI EP28 and the WHO essential-diagnostics list, i.e. the
bulk of the rule base carries *reference-interval* provenance, not disease-specific guideline citations; 1,752 (5.3 %)
cite only landing pages; 633 (1.9 %) cite only unreachable/unlocated/removed sources. The honest summary: the registry is
a transparent, machine-checkable draft of guideline knowledge, not an expert-curated reference, and the 100-rule physician
audit (A1/B1) remains the decisive check.

## A6 — Registry versions: 13.3.0 (evaluated) → 13.4.0 → 13.4.1 (shipped)

| item | 13.3.0 (all Paper 1 results) | 13.4.0 | 13.4.1 (shipped in release 1.3.1) |
|---|---|---|---|
| rules total / executable / retired-retained | 34,548 / 33,230 / 1,318 | 34,659 / 33,170 / 1,489 | identical to 13.4.0 |
| source records | 747 | 781 | 781 (9 locators removed, records kept) |
| change | — | D21: 171 domain-artefact single-analyte rules retired (e.g. *hypercalcaemia of malignancy ← glucose ≥ 140*); D19: 111 dormant entities anchored with one specific-analyte rule at the cited decision limit; D20: 48 duplicate entities retired, CKD G1–G5 staged by parent; 84 entities stay catalogued-only | provenance-only (A5) |
| gate | v5.3 gate 488/489 | pytest 689/689, hard 151/151, hard3 77/78 | same (re-run after live apply, 2026-10-24) |
| SHA-256 (disease file) | `91cdb766…` | `778a8385…` | `5082e8fd…` |

No number in the paper is re-stated for 13.4.x. The only 13.4.x results reported are the eICU labs-only re-runs below
(Supplement only), so that readers can see whether the shipped registry moved the headline.

**eICU-CRD demo, labs only, 2,314 stays (same stays, same engine, registry swapped):**

| registry | recall@3 | recall@5 | recall@10 | chart support p ≥ 0.7 |
|---|---|---|---|---|
| 13.3.0 (paper) | 49.3 % | 63.8 % | 77.2 % | — |
| 13.4.1 (= 13.4.0 logic) | 48.4 % | 61.7 % | 76.2 % | 23.4 % |
| 13.4.2 (shipped) | 49.3 % | 63.7 % | 76.9 % | mean AUROC 0.767 (k = 24), identical to 13.3.0 |

The 13.4.0 clean-up **lowered** top-5 recall by 2.1 points. The per-stay diff is unambiguous: the loss is not from the 171
retired artefact rules but from top-5 *crowding* by entities that D19 re-anchored as diagnostic criteria (weight 6) although
they are laboratory findings on routine analytes already covered by active entities — `high_anion_gap_metabolic_acidosis`
(entered 243 top-5 lists that it was absent from on 13.3.0), `normal_anion_gap_metabolic_acidosis` (88),
`severe_hypocalcemia` (34), `conjugated_hyperbilirubinemia` (31), `unconjugated_hyperbilirubinemia` (8). Registry 13.4.2
demotes those rules (nine in total — the two ketone/lactate patterns were added after `ketoacidosis_pattern` pushed euglycaemic DKA to rank 3 in the hard battery) to the registry's standard modelling of single-analyte findings (`screening`, weight 3,
specificity general; e.g. `hyperkalemia_v1`) — no rule added, removed or re-thresholded — and the eICU run was repeated: 13.4.2 gives 49.3 / 63.7 / 76.9 % — within 0.1–0.3 points of 13.3.0 — with hard batteries 151/151, 124/124, 77/78.
This episode is itself evidence for Limitation 1 (A4): a registry edit that looked like a pure clean-up changed ranking
behaviour on real data, which is why every registry version is gated on a held-out cohort before it ships.

## A7 — Sepsis-2019: what was tried after the pre-registered result, and why nothing was "fixed" (2026-10-24)

Pre-registered: AUROC 0.593 (prediction framing). Post-hoc Amendment 13 (dated before execution, after the 0.593 was
known): concurrent-diagnosis framing, 12-h window around onset, dwell-time-matched controls, with/without vital signs →
**0.534 / 0.534**; supervised logistic on the same windows 0.667 / 0.703. Strata: lactate measured 0.47; not measured 0.52.
Cause: the file has no procalcitonin/CRP; the registry's sepsis criteria are anchored on them; the sepsis group is absent
from the differential in 74 % of cases; no 13.3.0 sepsis rule consumes vital signs. Options considered and rejected:
adding SIRS/qSOFA-style rules (heart rate, respiratory rate, blood pressure → sepsis) or a "lactate alone → sepsis" rule
would be tuning on the test set, would raise false sepsis flags in the 16 % of non-septic ICU patients already flagged,
and is explicitly prohibited by the SAP after unblinding. The correct remedy is a prospectively specified clinical-signs
module evaluated on an independent cohort (Paper 2), and the manuscript now says so in Results and Limitations.
Supplementary Table S12; `eval/results/sepsis2019/concurrent_report.md`; `eval/realdata/eval_sepsis2019_concurrent.py`.

## Short version for the Abstract / cover letter (≤ 60 words)

The knowledge base was LLM-drafted and single-author curated; results therefore rest on pre-registered external
behaviour (14,400 patients, five sources), a 100-rule physician audit, fabrication batteries and a released benchmark
with a system-agnostic scorer, not on any claim that the rules are correct a priori. The LLM comparison is
exploratory and self-run.
