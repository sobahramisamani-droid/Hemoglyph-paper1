# Validation of engine v7 (registry 14.1.0) on the second quarantine — SAP Amendment 15 (one shot, 2026-10-25)

Freeze manifest written before any quarantined file was opened: `FREEZE_v15_20261025_sha256.txt` (316 files). Quarantine: `eval/quarantine_v15/`
(NHANES 2015–16 cycle I; PhysioNet/CinC 2019 training set B second disjoint subsample "B2", 4,991 patients). Two data-preparation
corrections were needed after crashes/empty subsets and are documented in `eval/quarantine_v15/README_q15_notes.md` (set-B2 `pid` type;
NHANES derived ACR column dropped by the fetch filter — first run kept as `nhanes_2015/report_v7_run1_noACR.md`). No engine, registry or
evaluation-code file changed between freeze and these results (verify with `sha256sum -c`).

| # | Pre-stated criterion (non-inferiority) | Result v7 | Reference | Verdict |
|---|---|---|---|---|
| 1 | NHANES I (n 3,000): AUROC within 0.03 of NHANES H (14.1) for diabetes, CKD, anaemia, iron deficiency, hypercholesterolaemia, hyperuricaemia; healthy-subset false flags ≤ 1 % | diabetes **0.924** · CKD (KDIGO eGFR/ACR) **0.962** · anaemia **0.983** · iron deficiency **0.972** · hypercholesterolaemia **0.886** · hyperuricaemia **0.955** · ALT 0.877 · CKD self-report 0.799; healthy 0/79 (0.0 %, CI 0–4.6) | H: 0.938 / 0.968 / 0.994 / (J 0.990) / 0.883 / 0.958 / 0.880 / 0.748 | **Met** (largest Δ 0.018) |
| 2 | Sepsis-2019 set B2, concurrent window, arm B (labs + vitals): AUROC ≥ 0.638 − 0.02; control flag ≤ 20 % | **0.635 (0.597–0.673)**; flag 14.2 % (11.6–17.2); labs-only 0.595 (0.563–0.627), flag 8.7 %; logistic reference 0.726 / 0.721 | set B 14.1: 0.638, flag 16.1 % | **Met** |
| 2b | (secondary, not a criterion) pre-registered prediction framing, labs first 24 h | 0.588 (0.559–0.616); flag 11.8 %; logistic 0.679 | set B 14.1: 0.610; logistic 0.712 (different patients — B2 is a harder subsample for the supervised reference too) | reported |
| 3 | Safety: healthy 0/1000 (seed 15); fuzz no new breaks | 0/1000 (worst p 0.45); 753/755 | 14.1: 0/1000; 752/755 | **Met** |

## Reading
* v7 is **non-inferior** to 14.1 on every quarantined task and at **recall parity** on the development eICU set (flat top-5 60.8 = 60.8;
  two-tier@1 33.1 vs 32.3; two-tier@3 62.0 vs 62.3). The development gate's "strictly better" clause was not met and **no recall
  improvement is claimed** (`eval/results/gate_v7/GATE_v7_RESULT.md`).
* What v7 changes is *what the output says*, not how often the label is in the list: findings are no longer attributed to unrelated
  diagnoses (INR → "SIADH", anaemia → "acute chest syndrome"), total calcium without albumin is no longer an anchor-grade hypocalcaemia,
  a normal TSH in the ICU no longer becomes central hypothyroidism / subclinical hyperthyroidism, urate 7.1 mg/dL is no longer weighted
  like sodium 122, and sickle-cell complications need sickle-cell context.
* The new secondary metric (panel-supported recall) quantifies the reference-standard ceiling on eICU: 541/2,432 labels have no single
  laboratory criterion, 275 lack the analyte in the first panel, 431 are contradicted by the panel; on the remaining 1,460, v7 reaches
  78.0 % top-5 / 91.8 % top-10 (two-tier 89.2 / 97.2). The 13.4.2 legacy margin on this metric (81.6 / 95.1) is CKD-from-a-single-creatinine
  and leukocytosis-beneath-sepsis only.

## Decision
Engine v7 ships with registry 14.1.0 (desktop 1.3.1 engine; `analyse_gidlines.py` single file). The paper reports 13.3.0 (frozen),
14.1/v6 and v7 side by side with both looks (development and quarantine), and states explicitly that the labs-only ICD-recall ceiling
has been reached and that further gains require context/temporal inputs and a physician-adjudicated reference standard (Paper 2).

Files: `../nhanes_2015/report_v7.md`, `../sepsis2019/{concurrent_report,report}_setB2_v7.md`, `healthy_v7_s15.txt`, logs `*.log`.
