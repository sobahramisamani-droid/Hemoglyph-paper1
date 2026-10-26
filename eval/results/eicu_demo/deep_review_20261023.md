# Deep review 2026-10-23 - context echo and sex gap

## 1. Context arm vs labs-only on the SAME labels, split by whether the label is already named in the history

| labels | n | ctx recall@5 | labs-only recall@5 | delta |
|---|---:|---|---|---|
| not_named | 2467 | 59.1% | 58.2% | +0.9 |
| named_in_history | 240 | 72.9% | 49.6% | +23.3 |

Most frequent context actions: ["hypertension", "listed_documented"] x1092; ["diabetes_mellitus", "confirmed"] x418; ["copd", "listed_documented"] x297; ["heart_failure", "listed_documented"] x255; ["chronic_kidney_disease", "confirmed"] x231

Per-group delta (ctx - labs) sorted:

| group | n | ctx@5 | labs@5 | delta |
|---|---:|---|---|---|
| diabetes | 255 | 70% | 47% | +22.4 |
| chronic_kidney_disease | 150 | 79% | 64% | +14.7 |
| hyperglycemia | 96 | 60% | 49% | +11.5 |
| heart_failure | 198 | 28% | 25% | +2.5 |
| hypothyroidism | 46 | 17% | 11% | +6.5 |
| cirrhosis_liver_failure | 32 | 56% | 50% | +6.2 |
| renal_impairment | 329 | 79% | 79% | +0.3 |
| gi_bleeding | 149 | 79% | 79% | +0.7 |
| metabolic_acidosis | 52 | 56% | 56% | +0.0 |
| alcohol_withdrawal | 42 | 29% | 29% | +0.0 |
| hypokalemia | 68 | 44% | 44% | +0.0 |
| hypomagnesemia | 38 | 37% | 37% | +0.0 |
| thrombocytopenia | 41 | 68% | 68% | +0.0 |
| acute_myocardial_infarction | 103 | 73% | 73% | +0.0 |
| hyponatremia | 52 | 65% | 65% | +0.0 |
| acute_pancreatitis | 33 | 39% | 39% | +0.0 |
| diabetic_ketoacidosis | 108 | 63% | 63% | +0.0 |
| lactic_acidosis | 23 | 52% | 52% | +0.0 |
| hypoglycemia | 21 | 29% | 29% | +0.0 |
| malnutrition | 23 | 0% | 0% | +0.0 |
| sepsis | 295 | 48% | 48% | -0.7 |
| anemia | 148 | 82% | 84% | -1.4 |
| coagulopathy | 33 | 39% | 45% | -6.1 |
| leukocytosis | 57 | 54% | 58% | -3.5 |
| hyperkalemia | 49 | 43% | 49% | -6.1 |
| acute_kidney_injury | 219 | 69% | 74% | -5.0 |

## 2. Sex gap (v5.1 labs-only)

| sex | labels | recall@5 |
|---|---:|---|
| male | 1682 | 58.5% |
| female | 1025 | 55.7% |

Female label mix scored with MALE per-group recall: 57.9% (vs observed female 55.7%)
Male label mix scored with FEMALE per-group recall: 56.0% (vs observed male 58.5%)
If the standardised numbers converge, the gap is case-mix (which diagnoses women carry); if they stay apart, it is within-group performance (reference intervals / thresholds).

| group | female n | female@5 | male n | male@5 | gap (F-M) |
|---|---:|---|---:|---|---|
| coagulopathy | 16 | 38% | 17 | 53% | -15 |
| acute_kidney_injury | 84 | 65% | 135 | 79% | -14 |
| gi_bleeding | 42 | 69% | 107 | 82% | -13 |
| acute_myocardial_infarction | 31 | 65% | 72 | 76% | -12 |
| renal_impairment | 125 | 74% | 204 | 82% | -9 |
| hyperkalemia | 16 | 44% | 33 | 52% | -8 |
| anemia | 65 | 80% | 83 | 87% | -7 |
| metabolic_acidosis | 21 | 52% | 31 | 58% | -6 |
| sepsis | 117 | 45% | 178 | 51% | -5 |
| diabetic_ketoacidosis | 47 | 62% | 61 | 64% | -2 |
| hypothyroidism | 20 | 10% | 26 | 12% | -2 |
| diabetes | 96 | 49% | 159 | 47% | +2 |
| heart_failure | 64 | 28% | 134 | 24% | +4 |
| hyperglycemia | 41 | 54% | 55 | 45% | +8 |
| leukocytosis | 20 | 65% | 37 | 54% | +11 |
| chronic_kidney_disease | 53 | 77% | 97 | 57% | +21 |
| hyponatremia | 20 | 80% | 32 | 56% | +24 |
| hypokalemia | 36 | 58% | 32 | 28% | +30 |

Scorable labels per stay: female mean 1.11, male mean 1.21

## 3. Interpretation (written 2026-10-23 before the v5.2 freeze; no code or registry changed)

**Context arm.** The headline gain (+2.8 points recall@5, 63.7 -> 66.5 %) is almost entirely a *context echo*: on the 2,467 labels
NOT already named in the documented history the gain is +0.9 points; on the 240 labels that ARE named it is +23.3 points
(diabetes, CKD, hypothyroidism). Worse, documented-only entries (e.g. "hypertension listed_documented" x1092) consume ranking slots and
cost recall for lab-driven diagnoses: AKI -5.0, hyperkalaemia -6.1, coagulopathy -6.1, leukocytosis -3.5. Consequences for the paper:
(a) the pre-specified primary metric for the context arm must be recall on NOT-named labels (SAP Amendment 8 already splits them; the
headline number should be the not-named one); (b) v5.3 design change: `listed_documented` entities are presented in a separate
"documented problems" block and excluded from the ranked differential used for recall@k; (c) the AKI loss is clinically meaningful
(AKI-on-CKD is under-ranked once CKD is confirmed) and goes to the error audit.

**Sex gap.** Direct standardisation shows the gap (58.5 vs 55.7 %) is mostly *within-group performance*, not case mix (female label mix
scored at male rates = 57.9 %). The largest female deficits are AKI (-14), GI bleeding (-13), AMI (-12), renal impairment (-9).
Registry check: the AKI screening rule uses creatinine > 1.3 mg/dL for ALL sexes although the feature registry itself carries sex-specific
reference ranges (F 0.5-1.1, M 0.7-1.3); women with creatinine 1.1-1.3 are therefore invisible to the rule. Troponin I uses one cut-off
(0.04 ng/mL) with no sex-specific 99th percentile (ESC 2020 / 4th UDMI recommend sex-specific limits for hs-assays). GI bleeding relies on
BUN/creatinine ratio and haemoglobin fall - both shifted by the same creatinine issue. Also found: `acute_myocardial_infarction` carries
RISK-FACTOR rules (total cholesterol >= 200, LDL >= 115, hs-CRP > 3) typed as screening for an acute event - a mislabelled rule class
that belongs to risk entities and should be re-homed (candidate for the A1 physician audit form, category "wrong entity").

**Planned corrections (v13.3, post-freeze, pre-registered here):** sex-specific creatinine thresholds in AKI/CKD screening rules
(use the registry's own reference ranges); sex-specific troponin limits where the assay is hs; re-home risk-factor rules from acute disease
ids; exclude documented-only entities from ranked recall. Each will be reported with before/after on the same frozen cohorts.

## 4. Registry hygiene found while checking the troponin hypothesis (not an active bug, masked by the engine)

Scan of executable rules: 92 sex-blind creatinine leaves in the 1.0-1.5 mg/dL band (44 x ">1.3" screening, 27 x ">1.5"); hs-troponin
rules carry thresholds in TWO conventions under the same declared unit ("high_sensitivity_troponin_t 14.0 ng/mL" x25 and "0.014 ng/mL" x3;
hs-TnI 20 / 30 "ng/mL" x31), and the feature registry accepts only ng/mL for hs-troponins with "conversion_review_required".
Engine probe (v5.1, live): hs-TnT 50 ng/L and 0.05 ng/mL give identical output (acute_myocardial_injury 0.80 > AMI 0.46, correct per
4th UDMI); 8 ng/L gives nothing - i.e. the computed/ESL troponin layer normalises to ng/L and the inconsistent registry rules are
not what decides the output. Still a hygiene defect that a physician audit will (rightly) flag: v13.3 will set hs-troponin canonical
unit ng/L with ng/mL x1000 conversion and rewrite the 59 leaves to one convention with sex-specific 99th percentiles.

## 5. Single-panel "CKD" (open issue, 76/564 dev FP at p>=0.5)
KDIGO defines CKD by >= 3 months; from one panel the engine can only assert reduced GFR. v5.3 proposal: when neither a temporal series
(>= 90 days) nor documented CKD context exists, output `renal_failure_unspecified`/reduced-GFR with CKD and AKI as sub-options rather
than CKD at p >= 0.5. This is consistent with the existing `renal_impairment` union in the label map and would lower CKD false
positives without touching recall of the union group.
