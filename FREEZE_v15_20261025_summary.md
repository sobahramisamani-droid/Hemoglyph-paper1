# FREEZE v15 — 2026-10-25 10:01 UTC

* Registry: 14.1.0-CLINICAL-CURATED — executable rules 33183, sources 785; engine v7 (SAP Amendment 15, changes C11–C16 on top of v6.1).
* Manifest: `FREEZE_v15_20261025_sha256.txt` — 316 files, 34.1 MB. Verify with `sha256sum -c FREEZE_v15_20261025_sha256.txt`.
* Development results at freeze (eICU-CRD demo, 2,314 stays, labs only): v7 flat 47.9/60.8/74.1, two-tier@1/3/5 33.1/62.0/71.9, panel-supported top-5 78.0; v14.1 flat 48.5/60.8/74.1, two-tier@5 71.7, grouped@5 68.8; same-engine 13.4.2 control flat 47.7/60.9/75.5, two-tier@5 72.2, grouped@5 68.1; 14.0.0 flat 43.8/58.4/73.8, two-tier@5 72.2, grouped@5 68.6.
* Quarantined data (`eval/quarantine_v15/`: Sepsis-2019 set B2 (5,000 records disjoint from the Amendment-14 subsample), NHANES 2015–16 I) have NOT been read before this manifest was written.
* Pre-stated validation criteria (SAP Amendment 15, non-inferiority): NHANES I AUROCs (diabetes, CKD, anaemia, iron deficiency, hypercholesterolaemia, hyperuricaemia) within 0.03 of the NHANES H values of 14.1; healthy-subset false flags ≤ 1 %; set B2 arm B concurrent AUROC ≥ 0.638 − 0.02, flag ≤ 20 %; healthy 0/1000; fuzz no new breaks.
* Development-set expectation recorded before validation: engine v7 is at recall parity with 14.1 on eICU; set B2 is expected near the set-B value (0.638); NHANES I expected within 0.02 of H.
