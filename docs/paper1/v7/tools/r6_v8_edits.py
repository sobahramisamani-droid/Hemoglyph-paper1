"""Round-6 edits: report the post-freeze v8 development step (2026-10-26) in both manuscripts, the supplement and
the response letter. Every anchor must match exactly once; the script refuses to write otherwise. Run once."""
import pathlib, sys
D = pathlib.Path("/home/user/Hemoglyph/docs/paper1")
NPJ = D / "v7/Paper1_Hemoglyph_npj_EN_v7_R1.md"; SMP = D / "v7/Paper1_Hemoglyph_SampleStyle_v7_R1.md"
SUP = D / "supplement/SUPPLEMENT_R1.md"; RSP = D / "v7/RESPONSE_TO_REVIEWERS_R1.md"

RESULTS_V8 = """### Post-freeze development step (engine v8, registry 14.2.0): what the roadmap did and did not deliver

After the frozen v7 results above were complete, the twelve improvement proposals raised in review were each tested against the frozen v7 artefacts before any code was changed (Supplementary Note 7). Three were supported and implemented; the others were refuted by the data or require resources we do not have. (i) *Adaptive truncation of the differential to raise precision@5*: on the v7 top-5, every precision gain was paid for almost one-for-one in recall (fixed k = 5: precision 14.2%, recall 60.8%; score ≥ 0.6: 19.0% / 53.5%; score ≥ 0.7: 23.3% / 43.3%), and the precision ceiling under perfect ranking is about 21% because the problem list carries ~1.05 evaluable labels per stay; v8 therefore adds a descriptive `confidence_band` and a `concise` flag to each entry without changing the ranking. (ii) *Asymmetric suppression of a covering diagnosis (e.g. diabetes hiding ketoacidosis)*: of 107 coded ketoacidosis stays, 68 were in the top-5, 7 at ranks 6–10 and 26 absent; the absent stays lacked bicarbonate, anion gap or ketones in the panel (glucose 382–853 mg/dL with no bicarbonate), so the cause is a missing criterion, not suppression, and asserting ketoacidosis from glucose alone would contradict the ADA criteria. (iii) *Dropping the 28 rules whose source locator had been removed in 13.4.1*: these are toxicology, transfusion and endocrine thresholds (lithium, digoxin, salicylate, toxic alcohols, cyanide, amatoxin, β-blocker, TACO, valproate hyperammonaemia, central diabetes insipidus, pseudohyponatraemia, protein-losing enteropathy); ablation showed no effect only because eICU contains no such cases, so instead of deleting them registry 14.2.0 re-sources them with 13 Crossref-resolved DOIs (verified 2026-10-26), leaving zero rules without a locator and no logic changed. (iv) *Further derived indices*: v8 adds MELD/MELD-Na (computed only when bilirubin > 2 mg/dL or INR > 1.5; prognostic, never a diagnostic vote) and the platelet-to-lymphocyte ratio (informational); CURB-65, HAS-BLED, CHA₂DS₂-VASc and Child-Pugh need non-laboratory inputs and were not added. (v) *A supervised sepsis component*: because sepsis onset is an outcome rather than a laboratory criterion, we built a transparent companion risk model outside the untrained engine (L2 logistic regression and a regularised gradient-boosting reference over last-observation-carried-forward vitals and laboratory values, their 6- and 12-h trends, SIRS/qSOFA components and time since admission), trained once on PhysioNet set A and evaluated on the untouched sets B and B2. Hourly AUROC was 0.757 / 0.750 (boosting) and 0.717 / 0.726 (logistic); the score 6, 12 and 24 h before onset discriminated with AUROC 0.78 / 0.80 / 0.77 (B) and 0.77 / 0.77 / 0.79 (B2); the official PhysioNet utility at a threshold fixed on set A was 0.253 / 0.220 (challenge winner on the full hidden test: 0.36); and in the patient-level frame used for the engine the companion reached 0.654 / 0.631 against the engine's 0.610 / 0.588 (Supplementary Table S16). The gain is real but modest, and the module is labelled predictive, not diagnostic. The v8 development gate reproduced every v7 safety battery result and every eICU count exactly (flat recall@5 60.8%, two-tier@5 71.9%; 680 unit tests plus 4 new); v8 has not been through a quarantine round and no frozen number in this paper derives from it."""

METHODS_V8 = """### Post-freeze development version (v8)

Engine v8 (2026-10-26) differs from the frozen v7 in three presentation- or index-level additions—MELD/MELD-Na (Kamath 2001; Kim 2008; OPTN formula with sodium clamped to 125–137 mmol/L and creatinine capped at 4 mg/dL) and the platelet-to-lymphocyte ratio as derived patterns with `supports = []`, and a `confidence_band`/`concise` field on each differential entry (bands ≥ 0.70 high, 0.60–0.69 moderate, 0.50–0.59 low, otherwise consider; descriptive, calibrated on the development set only)—and in registry 14.2.0, which re-sources 28 rules (9 source records) with Crossref-resolved DOIs and changes no rule logic, threshold, weight or executable flag (`eval/registry_patches/patch_14_2_0.py`). The sepsis companion (`eval/sepsis_ml/sepsis_risk_module.py`) uses the 5,000-patient public subsets of PhysioNet/CinC 2019; features are listed in the script; the logistic model is class-balanced L2 (C = 0.05); the gradient-boosting reference uses depth ≤ 4, ≤ 15 leaves, ≥ 300 samples per leaf, L2 = 5 and early stopping on 15% of set A. The alert threshold for the utility score was chosen on set A over a grid of score quantiles. Disclosure: the boosting hyper-parameters were tightened once after a first evaluation on set B showed over-fitting (training AUROC 0.997, set B 0.719); set B2 was not opened until the final configuration. Patient-level AUROC uses the maximum score over hours before the shifted label for septic patients and over all hours for non-septic patients; horizon AUROC compares the score exactly h hours before onset with a random hour of each non-septic patient. The v8 gate (`eval/results/gate_v8/`) repeats the v7 gate (three vignette batteries, 1,000-panel healthy sweep, 755-pair perturbation battery, unit tests, eICU labs-only run) with a pre-stated non-inferiority margin of 0.5 recall points."""

LIMIT_V8 = " Engine v8 and the sepsis companion are post-freeze development work: they have not been through a quarantine round, the companion's boosting model was regularised once after a look at set B, and none of the frozen numbers in this paper derive from them."

DISC_V8 = " A post-freeze analysis of twelve reviewer-suggested improvements (Supplementary Note 7) found that the two that promised the largest gains—truncating the differential to raise precision, and suppressing covering diagnoses—would have traded recall for precision one-for-one or asserted diagnoses without their guideline criteria; the remaining recall ceiling on eICU is set by panels that lack the defining analyte and by the problem-list reference standard rather than by the reasoning layer, which is why we moved the supervised sepsis component outside the engine instead of training the engine."

def sub(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.exit(f"ANCHOR {label}: {n} matches")
    return t.replace(old, new)

# ---------- npj ----------
t = NPJ.read_text(encoding="utf-8")
t = sub(t, "Hemoglyph is not a sepsis predictor.\n\n### Blinded comparison", "Hemoglyph is not a sepsis predictor.\n\n" + RESULTS_V8 + "\n\n### Blinded comparison", "npj results")
t = sub(t, "\n### Statistics and software", "\n" + METHODS_V8 + "\n\n### Statistics and software", "npj methods")
t = sub(t, "Iranian populations and non-English laboratory conventions were not evaluated.", "Iranian populations and non-English laboratory conventions were not evaluated." + LIMIT_V8, "npj limitations")
t = sub(t, "\n### Limitations", DISC_V8.strip() + "\n\n### Limitations", "npj discussion")
# supplement list
t = sub(t, "## Supplementary information\n", "## Supplementary information\n\nSupplementary Note 7 and Table S16 (post-freeze v8 triage and sepsis companion) were added in revision round 6.\n", "npj supp list")
NPJ.write_text(t, encoding="utf-8")

# ---------- sample style ----------
t = SMP.read_text(encoding="utf-8")
t = sub(t, "\n### 4.6 Blinded comparison with an unnamed frontier LLM", "\n" + RESULTS_V8.replace("### Post-freeze", "### 4.5b Post-freeze") + "\n\n### 4.6 Blinded comparison with an unnamed frontier LLM", "smp results")
t = sub(t, "\n### 3.5 Statistics", "\n" + METHODS_V8.replace("### Post-freeze", "### 3.4b Post-freeze") + "\n\n### 3.5 Statistics", "smp methods")
t = sub(t, "Iranian populations and non-English laboratory conventions were not evaluated, and the OCR layer", "Iranian populations and non-English laboratory conventions were not evaluated," + LIMIT_V8.rstrip(".") + ", and the OCR layer", "smp limitations")
t = sub(t, "\n### 5.5 Limitations", DISC_V8.strip() + "\n\n### 5.5 Limitations", "smp discussion")
SMP.write_text(t, encoding="utf-8")

# ---------- supplement ----------
s = SUP.read_text(encoding="utf-8")
s += """

## Supplementary Table S16 — Sepsis companion risk model (post-freeze, engine-external; added in revision round 6)

Trained once on PhysioNet/CinC 2019 set A (5,000-patient public subset; 446 septic), evaluated on the untouched subsets B (280 septic / 4,699) and B2 (280 / 4,711). Threshold for the utility score fixed on set A. Source: `eval/results/sepsis_ml/sepsis_ml_report.md`.

| set | model | hourly AUROC | hourly AUPRC | patient-level AUROC | AUROC at −6 / −12 / −24 h | PhysioNet utility |
|---|---|---|---|---|---|---|
| A (development) | logistic (L2) | 0.773 | 0.091 | 0.658 | 0.754 / 0.800 / 0.818 | 0.364 |
| A (development) | gradient boosting | 0.934 | 0.319 | 0.832 | 0.950 / 0.909 / 0.865 | 0.689 |
| B (held out) | logistic (L2) | 0.717 | 0.051 | 0.552 | 0.698 / 0.780 / 0.776 | 0.199 |
| B (held out) | gradient boosting | 0.757 | 0.066 | 0.654 | 0.775 / 0.799 / 0.774 | 0.253 |
| B2 (held out) | logistic (L2) | 0.726 | 0.052 | 0.557 | 0.709 / 0.778 / 0.783 | 0.216 |
| B2 (held out) | gradient boosting | 0.750 | 0.068 | 0.631 | 0.774 / 0.765 / 0.786 | 0.220 |
| reference: frozen engine v7 (labs only) | rules | — | — | 0.600 / 0.610 / 0.588 (A / B / B2) | — | — |

Largest standardised logistic coefficients (signed): respiratory rate +0.49, hours since ICU admission +0.45, creatinine +0.39, base-excess missing −0.35, MAP missing −0.33, SBP missing +0.31, shock index −0.28, heart rate +0.26, 12-h maximum temperature +0.23. Measurement-availability flags carry signal in this dataset (sampling intensity), a known property of the challenge data; the module is reported with its contributing features so each alert can be inspected. The boosting hyper-parameters were regularised once after a first look at set B (training AUROC 0.997 / B 0.719 in the first configuration); B2 was not opened until the final configuration.

## Supplementary Note 7 — Evidence triage of the twelve post-review improvement proposals (2026-10-26)

| # | proposal | evidence on frozen v7 artefacts | verdict | v8 action |
|---|---|---|---|---|
| 1 | Hybrid rule + interpretable ML for sepsis with vitals, time and utility score | companion model: Table S16 | supported (modest gain) | engine-external module, labelled predictive |
| 2a | Evidence-state thresholding / adaptive truncation for precision@5 | precision vs recall on v7 top-5: k = 5 14.2 / 60.8; relative ≥ 0.6 15.3 / 58.8; relative ≥ 0.8 18.1 / 48.9; absolute ≥ 0.6 19.0 / 53.5; absolute ≥ 0.7 23.3 / 43.3; absolute ≥ 0.8 25.7 / 23.4; gap > 0.15 16.7 / 45.4; k = 3 16.5 / 47.9; ceiling under perfect ranking ≈ 21% | refuted as an accuracy gain | descriptive `confidence_band`, no ranking change |
| 2b | Asymmetric covering-diagnosis suppression (DKA, GI bleed, pancreatitis) | DKA 107 coded: 68 top-5, 7 at 6–10, 26 absent; absent stays lack HCO₃/anion gap/ketones; entities above DKA when missed: diabetes 23, AKI 22, sepsis 18 | refuted (missing criterion, not suppression) | none |
| 3 | Remove or revive the four 'inert' fusion layers | ablation Δ flat@5: Bayesian −1.3, fuzzy +0.3, graph +0.1, risk 0.0; fuzzy/risk carry perturbation robustness and the documented risk models | partly | kept; reported as such |
| 4 | 'Probable' tiers for CKD, leukocytosis, diabetes | CKD surfaces as `reduced_gfr_chronicity_undetermined` (renal union 255 vs 250); leukocytosis correctly nested under sepsis; diabetes absent stays lack HbA1c with glucose < 200 mg/dL | refuted (would create false positives) | none |
| 5 | Prune registry, drop 28 `unverified_source` rules, remove 388 unused sources | the 28 rules are correct toxicology/transfusion/endocrine thresholds; ablation 0.0 only because eICU has no such cases | partly | registry 14.2.0: re-sourced with 13 Crossref DOIs; 0 unverified; unused sources retained as provenance |
| 6 | Audit and expand the syndrome layer | no matched evaluation set for new syndromes | deferred | clinician audit (resource) |
| 7 | Medication/history context as risk and trend rules | context predicates and `documented_history` tier already present; not measurable on labs-only eICU | already present | none |
| 8 | Derived indices (NLR, PLR, MELD, Child-Pugh, CURB-65, HAS-BLED, CHA₂DS₂-VASc, APRI, BARD, corrected Ca, osmolal gap, delta-delta) | present: corrected Ca, NLR, delta ratio, osmolal gap, effective osmolality, glucose-corrected Na, FIB-4, APRI, HOMA; scores needing clinical inputs excluded | partly | MELD/MELD-Na and PLR added |
| 9 | Post-hoc calibration map with disclosure | already in v7 (ECE 0.162 → 0.003; Fig. 8, Table S10) | already present | none |
| 10 | Thyroid and liver rules | thyroid AUROC 0.979 (TSH) / 0.798 (self-report); HCV 0.925; ILPD 0.704 (label noise) | no action supported | none |
| 11 | Fuzzy thresholds for perturbation | fuzzy layer active; 753/755 by design | already present | none |
| 12 | LLM extraction front end; path A/B/C on 'untrained' | path C: engine stays untrained; supervised components only as labelled companions | decided | item 1 is the first such component |

Gate for v8 (`eval/results/gate_v8/GATE_v8_RESULT.md`): batteries 151/151, 124/124, 77/78 (same pre-existing miss); healthy sweep 0/1,000; perturbation 753/755; 680 unit tests passed + 4 new; eICU labs-only counts identical to v7 in every group. The Supplementary Note 6 manifest refers to the v7 artefacts; the v8 registry (14.2.0) is archived at `release/registry_14.2.0/` with SHA-256 sums and the v7 registry at `release/registry_14.1.0/`.
"""
SUP.write_text(s, encoding="utf-8")

# ---------- response letter ----------
r = RSP.read_text(encoding="utf-8")
r += """

# Round 6 — post-freeze development step (engine v8) added 2026-10-26

The twelve improvement proposals in the latest report were triaged against the frozen v7 artefacts before any code changed (Supplementary Note 7). We implemented what the data supported and report, rather than argue, what they refuted.

| proposal | outcome | where |
|---|---|---|
| Supervised sepsis component with vitals and time | Built outside the engine; held-out hourly AUROC 0.757 / 0.750, horizon AUROC ≈ 0.77–0.80, utility 0.25 / 0.22, patient-level 0.654 / 0.631 vs engine 0.610 / 0.588. Modest, labelled predictive, one disclosed re-tune after set B. | Results §v8; Methods §v8; Table S16 |
| Adaptive truncation for precision@5 | Refuted: precision and recall trade ≈ 1:1; ceiling ≈ 21% from the reference standard. Added descriptive confidence bands only. | Results §v8; Note 7 |
| Covering-diagnosis suppression (DKA) | Refuted: the 26 absent DKA stays lack HCO₃/anion gap/ketones; no suppression. | Results §v8; Note 7 |
| Drop 28 `unverified_source` rules | Not dropped (clinically correct toxicology thresholds); re-sourced with 13 Crossref-verified DOIs in registry 14.2.0, 0 remaining. | Methods §v8; Note 7 |
| Derived indices | MELD/MELD-Na and PLR added; scores needing clinical inputs excluded. | Methods §v8 |
| 'Probable' tiers, layer removal, thyroid/liver rules | Not supported by the data; reasons tabulated. | Note 7 |

All frozen numbers in the manuscript are unchanged; v8 is explicitly a post-freeze development step without a quarantine round (Limitations). Files: `docs/V8_ROADMAP_TRIAGE.md`, `eval/sepsis_ml/`, `eval/results/sepsis_ml/`, `eval/results/gate_v8/`, `eval/registry_patches/patch_14_2_0.py`, `release/registry_14.2.0/`, `tests/test_v8_indices.py`.
"""
RSP.write_text(r, encoding="utf-8")
print("R6 edits applied")
