# FREEZE v14 — 2026-10-25 04:48 UTC

* Registry: 14.1.0-CLINICAL-CURATED — executable rules 33183, sources 785; engine v6 (SAP Amendment 14, changes C1–C10).
* Manifest: `FREEZE_v14_20261025_sha256.txt` — 261 files, 35.2 MB. Verify with `sha256sum -c FREEZE_v14_20261025_sha256.txt`.
* Development results at freeze (eICU-CRD demo, 2,314 stays, labs only): v14.1 flat 48.5/60.8/74.1, two-tier@5 71.7, grouped@5 68.8; same-engine 13.4.2 control flat 47.7/60.9/75.5, two-tier@5 72.2, grouped@5 68.1; 14.0.0 flat 43.8/58.4/73.8, two-tier@5 72.2, grouped@5 68.6.
* Quarantined data (`eval/quarantine/`: Sepsis-2019 set B, NHANES 2013–14 H, MIMIC-IV demo, post-freeze PMC cases) have NOT been read before this manifest was written.
* Pre-stated validation criteria (SAP Amendment 14, unchanged): MIMIC-IV demo top-5 ≥ 65 % / top-1 ≥ 45 %; set B arm B AUROC ≥ 0.65 and control flag ≤ 20 %; NHANES H AUROCs within 0.03 of J; new PMC top-5 ≥ 60 %; healthy 0/40; fuzz 0/1000.
* Development-set expectation recorded honestly before validation: set A arm B AUROC .592 → the set-B AUROC criterion is expected to FAIL; it will be reported as such.
