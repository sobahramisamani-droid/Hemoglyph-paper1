# Engine v6 — change log for Registry 14.0.0 (SAP Amendment 14), development phase

All edits in `analyse_gidlines.py` / `calcu.py` were made and tested on development data only
(unit/hard batteries, eICU demo, Sepsis-2019 set A, NHANES 2017-18). Quarantined data untouched.

## Output structure (C1)
* `tier_of()` / `_is_finding()` extended: `entity_kind` ∈ {laboratory_finding, biomarker_pattern, serology_state}
  → tier `finding`; new kind `syndrome` (SIRS, qSOFA) → tier `syndrome`; everything else `diagnosis`.
  Each differential entry now carries `tier`; flat rank retained for comparability with 13.x.

## Finding-vs-diagnosis ordering (defects found by the 14.0.0 gate)
1. `critical_findings` ("never buried") now keeps only (a) ESL severity anchors and (b) ESL anchor/strong hits whose
   primary entity is a diagnosis, **or a finding asserted at anchor strength** (critical values: INR ≥ 4.5, K ≥ 6.5 …).
   Findings asserted at *strong* strength (reduced GFR from one creatinine, moderate anaemia) are listed beneath the
   diagnosis that accounts for them. (Regression seen: reduced GFR above sepsis / adrenal crisis.)
2. `_accounts()`: a diagnosis whose evidence_state is `insufficient` and final < 0.60 no longer buries a definitional
   finding (single creatinine 2.0 in a community panel → reduced GFR 0.92 @1, AKI 0.50 insufficient @2).
3. Evidence subsumption: a finding never "explains" a diagnosis (direction is diagnosis → finding). Previously
   `reduced_gfr` (creatinine) subsumed AKI (creatinine) and lowered it 0.74 → 0.67.
4. Final pass immediately before the sort: findings already placed beneath an accounting diagnosis are re-capped to
   0.95 × the best accounting diagnosis (final ≥ 0.6) **after** all competitor / subsumption / renal caps, so later
   score reductions of the diagnosis cannot re-order the pair (adrenal crisis 0.76 vs reduced GFR 0.79 → 0.72).
   Findings not accounted for by any diagnosis keep their score (fusion invariant test).

## Renal chronicity
* ESL `aki_kdigo_imputed_baseline_acute_care` (KDIGO 2012 §2.1, imputed baseline, acute-care encounter, no known CKD)
  is treated by `_apply_renal_chronicity` like a KDIGO criterion when < 2 chronicity markers are present.
* ESL `ckd_documented_history_reduced_egfr`: documented CKD / renal insufficiency + eGFR < 60 → CKD strong (KDIGO 2024
  chronicity criterion met by history); caps `reduced_gfr_chronicity_undetermined` at 0.60.

## Units (`calcu.py`)
* UCUM `mm[Hg]`, `torr` → mmHg; `/min`, `1/min`, `bpm`, `{beats}/min`, `{breaths}/min` → /min; `Cel`, `degC`, `°C`;
  `[degF]`, `°F`. Before this fix UCUM `mm[Hg]` blood pressures were silently dropped (Amendment 13 arm B had no BP).

## Evaluation scripts
* `eval_eicu.py`: `--encounter`, `--suffix`, renal union group, two-tier reporting.
* `eval_sepsis2019.py` / `eval_sepsis2019_concurrent.py`: `--encounter`, `--suffix`, `--data`; concurrent script:
  correct vital units, SaO2, anchor-lab availability (`not_assessable`), values-only logistic baseline.

## Gate (this directory)
`run_gate.sh` → pytest (689), hard batteries 1–3, eICU labs-only `_v1400` (encounter = icu). Results in `*.txt`,
`../eicu_demo/report_v1400.md`.

## Addendum (same day) — coverage rule for the finding demotion
* A finding asserted by an expert-syndrome hit (anchor/strong) is capped beneath the best accounting diagnosis only
  when the analytes behind the syndrome's REQUIRED groups are part of that diagnosis's own fired evidence
  (eGFR ≡ creatinine). Otherwise the diagnosis does not account for the finding and the finding keeps its score
  (IgG4 620 mg/dL is not "explained" by an eosinophilia-driven strongyloidiasis; reduced GFR IS explained by CKD,
  AKI or adrenal crisis whose rules fired on creatinine). Required-group → analyte mapping uses `_ESL_GROUPS`.
* Refinement: the finding is capped beneath the best **covering** accounting diagnosis (required analytes ⊆ its
  fired evidence), not the best overall one (creatinine 11 + HAGMA: reduced GFR sits under AKI, not under
  metabolic acidosis); when no diagnosis covers it the finding keeps its score.
* ESL `eosinophilia_parasitic` (eosinophils + IgE → strongyloidiasis) now requires exposure / immunosuppression
  context (`ctx_any`); without context a new `eosinophilia_ige_nonspecific` pattern reports eosinophilia only
  (no infection asserted from two analytes). `tests/hard_battery2.py` IgG4 case now also accepts
  `igg4_related_disease` at rank 1 (clinically the stricter target).

## eICU dev run 1 (14.0.0, with the "uncovered finding keeps its score" exemption) — REGRESSION, superseded
flat top-3/5/10 43.5/58.2/73.8 % vs 13.4.2 49.3/63.7/76.9 %; two-tier top-1/3/5 30.3/60.8/72.1 %; chart support 23.0 %.
Slot analysis (top-5 occupants, 2,314 stays): reduced_gfr 0→614, acute_myocardial_injury 165→480, hypoxemia 0→209,
hypercapnia_pattern 0→202, SIRS 0→51; CKD 479→213, anemia 1172→997, leukocytosis 701→598. Labels lost from top-5:
CKD 266, gi_bleeding 177, anemia 171, leukocytosis 109, AKI 98 (+50 gained), diabetes 86, hyperglycaemia 86.
Decision: the exemption is removed (generic 13.x cap applies to uncovered findings; the capping diagnosis prefers the
covering one). CKD-specific recall loss is the expected consequence of KDIGO-correct chronicity handling (single eGFR
→ reduced GFR, chronicity undetermined; renal union recall 79.8 → 84.0 %). Files: `report_v1400_run1_exempt.md`.
Run 2 started with the exemption removed (`eicu_run2.log`).

## Attribution runs (2026-10-24, `compare_arms.py`)
| arm | top-3 | top-5 | top-10 | two-tier top-5 | CKD r@5 | renal r@5 | anemia r@5 |
|---|---|---|---|---|---|---|---|
| 13.4.2 original (legacy units; pO2/pCO2 silently dropped) | 49.3 | 63.7 | 76.9 | — | 64.9 | 79.8 | 84.4 |
| v14 logic+registry, legacy units (ctrl A) | 44.4 | 59.5 | 74.8 | 72.7 | 29.7 | 84.4 | 75.5 |
| v6 engine + registry 13.4.2, fixed units (ctrl B) | 47.4 | 60.9 | 75.5 | 72.2 | 32.4 | 79.1 | 77.6 |
| v14 logic+registry, fixed units (run 2) | 43.6 | 58.2 | 73.8 | 72.1 | 27.7 | 84.0 | 71.4 |
Attribution: unit fix ≈ −1.3 pt top-5 (blood-gas findings now present), engine logic ≈ −1.5, registry 14 ≈ −2.7.
CKD-specific loss comes from the engine (ESL single-eGFR CKD patterns now need a chronicity clue) — KDIGO-correct.
Anaemia loss traced to the removal of the 13.x "ESL-strong finding never buried" rule → restored with the coverage
condition (covering diagnosis must be ≥ 0.6 and its evidence must contain the syndrome's required analytes); an
uncovered strong finding now follows the critical-finding tie rule (never beneath, tied with a ≥ 0.80 diagnosis).
UDMI rule added: AMI listed beneath myocardial injury (×0.85) when troponin is single/static and no ischaemic context.
Run 3 = full gate with these changes.

## Dev-chain results (2026-10-25, registry 14.0.0 + engine v6, dev data only)

**eICU demo labs-only, grouped rank** (entries whose `explained_by` points to a higher-listed entry inherit that entry's
position; the mechanism is the engine's own finding→diagnosis attribution, not a label-driven post-hoc merge):
top-1 32.9 %, top-3 57.2 %, top-5 68.6 %, top-10 78.6 % (n = 2,432). Flat 43.8/58.4/73.8 (top-3/5/10); two-tier 30.4/61.0/72.2.
Caveat: the 13.4.2 reference arm has not yet been scored with the grouped metric (its per-stay file predates `gr3`);
a same-metric control run is queued — until then, grouped rank must NOT be compared with the 13.4.2 flat numbers.

**NHANES 2017-18 (J), `--encounter community`, n-max 3000, v14 vs 13.3.0 (AUROC):** diabetes .945 vs .941; diabetes self-report
.918 vs .910; CKD .958 vs .959; CKD self-report .816 vs .798; anaemia .973 vs .971; iron deficiency .990 vs .989;
hypercholesterolaemia .902 vs .901; hyperuricaemia .943 vs .943; ALT .721 vs .720. All within 0.02 (criterion ≤0.03 met).
Healthy-adult false assertion: 1/160 (0.6 %) vs 1/274 (0.4 %) — different sampling of the 3000-subject subset.

**Sepsis-2019 set A concurrent run crashed** (`ValueError: truth value of a Series`) because `SaO2` appears in both the lab map
(added in the v14 unit pass) and the vital map, producing a duplicated column; fixed by excluding LAB keys from `vitcols`.
Re-run started separately; prediction run (`eval_sepsis2019.py --encounter icu --suffix _v1400`) continues in the chain.

## v6 change C7 (2026-10-25): SIRS sepsis screen downgraded to a non-asserting "screen" strength; hypotension as sepsis organ-dysfunction support

*Observation (set A concurrent, pre-change, `concurrent_report_v1400_prescreen.md`):* arm B AUROC .590 (13.3.0: .534), recall@5 42.6 % (21.6 %),
but flag rate among non-sepsis ICU controls 26.1 % (14.8 %) — above the pre-stated ≤20 % criterion. Control top-1 "sepsis" in 127/786.
*Cause:* `sirs_with_laboratory_support_sepsis_screen` carried strength "supportive" (0.72) → sepsis p≈0.72 (asserted) whenever
SIRS ≥2 plus a single lab (e.g. creatinine >1.5 or WBC >12), which most ICU patients meet without infection (Sprung 2006; Kaukonen NEJM 2015).
*Change (guideline-sourced, label-independent):* new ESL strength `screen` = 0.45 (below the 0.5 assertion line; tier stays "possible")
and screen hits do not mark the disease as guideline-anchored. SSC 2021 defines screening as a prompt for evaluation; Sepsis-3 removed SIRS
from the definition. Sepsis ≥0.5 now requires a Sepsis-3/organ-dysfunction syndrome (lactate + organ marker, bandaemia, marked leukocytosis + lactate).
`sepsis_lactate_organ` gained SBP <90 / MAP <65 as support (cardiovascular SOFA; septic-shock criterion) — only reachable with the vitals context module.
*Probes:* SIRS + Cr 1.6 → sepsis 0.41 (was ≈0.72); WBC 22 + lactate 3.5 + Cr 1.9 → 0.83; qSOFA + lactate 4 + SBP 85 → 0.72; hypotension without lactate → 0.26.
*Note:* this is a threshold placement motivated by a dev-set flag rate; it is recorded here and will be validated once on set B. No weight was fitted to labels.

## Dev chain 2 — final development results for registry 14.0.0 + engine v6 (incl. C7), 2026-10-25

| evaluation (dev data) | 13.3.0 / 13.4.2 reference | v14 final | note |
|---|---|---|---|
| eICU flat top-3/5/10 | 49.3 / 63.7 / 76.9 (13.4.2, legacy units) | 43.8 / 58.4 / 73.8 | flat criterion NOT met (−5.3 @5) |
| eICU two-tier top-1/3/5 | 30.6 / 61.1 / 72.2 (ctrl B, same engine) | 30.4 / 61.0 / 72.2 | diagnosis-tier ranking unchanged |
| eICU grouped top-1/3/5/10 | 30.8 / 55.8 / 68.1 / 78.7 (ctrl B `_v1342_v6engine_g`, same engine, same metric) | 32.9 / 57.2 / 68.6 / 78.6 | registry 14 ≈ +0.5 @5, +2.1 @1 |
| eICU per-group r@5 anaemia / sepsis / diabetes | 79.6 / 48.1 / 48.0 (ctrl B) | 74.8 / 45.0 / 41.5 | slot crowding by `reduced_gfr_chronicity_undetermined` |
| NHANES J AUROC (9 labels) | 13.3.0 | all within 0.02 | criterion met; C7 cannot fire (no vitals) |
| Sepsis set A prediction AUROC / r@5 / flag | .593 / 32.2 % / 16.5 % (13.3.0) | .600 / 33.5 % / 17.0 % | unchanged within CI |
| Sepsis set A concurrent arm A (labs) | .534 / 21.6 % / 14.8 % | .559 / 22.7 % / 13.0 % | |
| Sepsis set A concurrent arm B (labs + vitals) | .534 / 21.6 % / 14.8 % | .592 / 28.9 % / 18.1 % | pre-C7: .590 / 42.6 % / 26.1 % |
| Unit gate | 689 / 151 / 124 / 77 of 78 | identical | |

Reading: v14 is more KDIGO/UDMI/Sepsis-3-faithful and better calibrated on what it asserts (single creatinine → reduced GFR not CKD;
single troponin → injury not infarction; SIRS → screen not sepsis), and this costs flat top-5 recall on eICU chart labels, where the
labels reward the bolder 13.4.2 behaviour. The pre-registered set-B criterion (arm B AUROC ≥ .65) looks unlikely on the dev numbers
(.592); it will be tested once, as written, and reported whatever the result.

## Changes C8–C10 (2026-10-25) → registry 14.1.0 + engine v6 (gate: `eval/results/gate_14_1_0/`)

*Error analysis (dev eICU, v14 vs same-engine 13.4.2 control):* every anaemia/diabetes/sepsis top-5 loss was displacement by
`reduced_gfr_chronicity_undetermined` or `acute_myocardial_injury` listed *immediately beneath* the diagnosis that explains them
(AKI .90 → reduced GFR .86 at rank 2): the first-pass cap (0.95 × covering dx) keeps the explained finding adjacent, so the same
fact occupies two of five lines.

**C8 — explained findings sort after self-standing asserted entities.** In the final sort, a finding/syndrome with `explained_by`
set (non-critical) takes tier 0.5: after every asserted entity that stands on its own, before sub-threshold entries. Probabilities
unchanged. Converse UDMI branch added: when infarction is asserted (dynamics / ischaemic context / massive troponin) the injury finding
is `explained_by` the infarction. 250-stay dev smoke: flat top-3/5 48.2/61.9 → 52.1/64.6 (same-engine 13.4.2 control 51.4/63.8);
grouped unchanged 68.1.

**C9 — ischaemic-context MI syndrome.** New ctx predicate `sym` (presenting_complaint / chief_complaint / symptoms / presentation) and
ESL `mi_high_troponin_ischaemic_presentation`: hs-cTn ≥ 100 ng/L + ischaemic symptom/ECG term in context → acute MI (strong, 0.88)
per 4th UDMI (injury + ischaemia) and ESC 2023 rule-in. Excluded: dialysis/ESRD, myocarditis, cardiac surgery/PCI/cardioversion, CK > 5000.
Probes: hs-TnI 900 alone → injury .83 / MI .46; + "chest pain" → MI .88, injury .83 explained_by MI; + ESRD → injury only.

**C10 — single-troponin finding is acuity-undetermined (registry 14.1.0).** 4th UDMI §3: one cTn above the 99th URL = myocardial injury;
*acute* only with rise/fall. The eICU top-5 contained `acute_myocardial_injury` in 480 stays, median troponin-I 0.12 ng/mL (p25 0.06) —
values equally compatible with chronic injury in CKD/HF. New laboratory finding `myocardial_injury_acuity_undetermined` (ICD-10 R79.89);
rule `acute_myocardial_injury_udmi4_troponin_above_99th_v14` retargeted to it; ESL `mi` (troponin > 100 ng/L + non-ischaemic support such as
glucose/creatinine — previously asserted MI, unjustifiable under UDMI) and `myocardial_injury_single` retargeted to the finding;
`acute_myocardial_injury` now comes only from the temporal rise/fall syndrome, `acute_myocardial_infarction` from dynamics, ischaemic
context (C9) or massive troponin. eICU group `acute_myocardial_infarction` accepts the new finding exactly as it accepted
`acute_myocardial_injury` (partial credit for the troponin finding; documented metric change). Test
`test_single_troponin_is_injury_not_mi` accepts the new id. Registry 14.1.0: 33,183 executable rules, 785 sources, +MASLD (3 rules),
+PSGN (2 rules), +C10 entity; disease sha `0a2eeac0…`.
NHANES J not re-run for 14.1: AUROC/T8 use probabilities, which C8 does not change, and C9/C10 need troponin or symptoms (absent).

### C8 follow-ups found by the unit gate (2026-10-25)
- `severe_neutropenia` (ANC < 0.5) added to critical findings regardless of syndrome strength (IDSA 2010 / ASCO-IDSA 2018): C8 had
  listed it beneath the pancytopenia pattern. A critical finding is never subsumed by ANOTHER FINDING whose rule evidence merely
  contains its analyte (thrombocytopenia rule with a WBC leaf); diagnoses may still organise it (cyanide over lactate 9 — hard3).
- Finding→finding subsumption now requires the explained finding's defining analytes ⊆ the explaining finding's defining analytes
  (ESL `req_features`, new hit key). Tried and reverted: using required analytes only for ALL subsumption (−9 hard-battery cases:
  support leaves legitimately carry subsumption for DKA/ALF/AFLP patterns).
- Tried and reverted: exempting critical findings from organising-diagnosis precedence (test
  `test_marked_renal_failure_precedes_its_electrolyte_consequences` encodes cause-first as the design).
- New ESL `mi_very_high_troponin_with_ckmb` (troponin ≥ 500 ng/L AND CK-MB > URL → acute MI 0.88 / acute injury / ACS; ESRD, myocarditis,
  cardiac surgery, trauma excluded): CK-MB kinetics date the injury as acute; magnitude rarely chronic. Replaces the old `mi` syndrome's
  role for the hard-battery NSTEMI case with stricter, sourced criteria. Acuity-undetermined finding is listed beneath a determined
  acute/chronic injury (≥ 0.6).
- Known limitation kept: `explained_by` for a finding with no covering diagnosis may name the strongest co-occurring diagnosis (reduced GFR
  "explained by" MI when creatinine is only a support leaf of the MI syndrome). Cosmetic in the flat list; flagged for 14.2.

## Engine v7 (2026-10-25, SAP Amendment 15) — causal attribution; registry 14.1.0 unchanged

| id | change | location (`analyse_gidlines.py`) | source |
|---|---|---|---|
| C11 | `_CAUSAL_EXPLANATION` map + `_can_explain()` + `_causal_dx()`; finding-demotion pass names an explainer only if it covers the finding's analytes or is a mapped cause; otherwise the finding keeps its score (ties with a ≥0.80 diagnosis, no `explained_by`); subsumption dx→finding gated the same way | module block before `_LOW_SALIENCE_FINDINGS`; `differential_diagnosis` demotion + subsumption passes | per-entry comments (KDIGO, ADA, AHA/ACC, Surviving Sepsis, AASLD/EASL, ATA, ACOG 222, ASH, …) |
| C12 | presumptive AKI (imputed baseline) + 0 chronicity markers + no documented CKD → CKD ≤ 0.49 | `_apply_renal_chronicity` | KDIGO 2012 CKD chronicity (> 3 months) |
| C13 | ESL `nti_acute_care` (acute-care encounter, TSH 0.1–10, ≥1 supportive) → `euthyroid_sick_syndrome_nontr` pattern 0.80; caps central/subclinical thyroid dx | ESL list after `nti` | Fliers et al. Lancet D&E 2015; ATA/AACE 2012 |
| C14 | urate 7.0–9.0 → pattern 0.80; ≥ 9.0 (`hyperuricemia_marked`) → strong 0.88 | ESL graded electrolytes | ACR 2020; Cairo-Bishop 2004 |
| C15 | hypocalcaemia anchor/strong need albumin-corrected or ionised Ca; `hypocalcemia_total_uncorrected` (< 7.5 mg/dL, no albumin/iCa) pattern 0.80 | ESL `hypocalcemia_*` | Cooper & Gittoes BMJ 2008 |

Causal-map entries added during the gate: `hellp_syndrome`, `preeclampsia` (ACOG 222; hard-battery HELLP case would otherwise list unexplained hyperuricaemia first).
Lesson recorded: an eICU smoke run without `--encounter icu` is not comparable with `_v1410` (imputed-baseline AKI needs the acute-care context).
| C13′ | NTIS split into four acute-care syndromes requiring an abnormal thyroid test (`nti_acute_care_low_t3/_low_t4` pattern 0.80; `_low_tsh`, `_recovery_tsh` supportive 0.72); a normal TSH never fires | ESL | Fliers 2015 |
| C11′ | explainer = best-supported related dx (coverage or causal); causal explainer < 0.80 cannot cap a stronger finding; covering dx always explains | demotion pass | — |
| C16 | `sickle_complication_context_guard`: ACS / VOC / HbSS ≤ 0.3 without documented SCD or measured HbS | ESL guards | NHLBI 2014; ASH 2020 |
| metric | `eval/realdata/panel_supported_metric.py` (secondary, pre-specified in SAP Am. 15) | eval | — |
