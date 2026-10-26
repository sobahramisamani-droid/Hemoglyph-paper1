# FREEZE v5.3 — 2026-10-24 04:40 UTC

* Engine: analyse_gidlines.py (release 1.3.1, v5.3 evaluation build); disease–guideline registry 13.3.0-CLINICAL-CURATED — entities 6750, rules 34548, executable 33230; feature registry 2,045 analytes.
* Manifest: `FREEZE_v5.3_20261024_sha256.txt` — 261 files, 24.4 MB. Verify with `sha256sum -c FREEZE_v5.3_20261024_sha256.txt`.
* Chain markers present at freeze: ablation_regoff, audit53, cal53, eicu53, eicu53_ctx, eicu53_ctxtmp, gate53, hcv53, ilpd53, nt53, pmc53, subg53, thyroid53.
* Headline (eICU-CRD demo, 2,314 stays, labs only): recall@3/5/10 = 49.3 / 63.8 / 77.2 %; +context 52.1 / 66.6 / 79.8; +context+temporal 51.7 / 66.2 / 80.2; mean AUROC 0.767 (k = 24).
* Pre-registered hypotheses (SAP Amendment 12): H1 FAILED (sex gap 4.4 → 4.3), H2 PASSED (63.7 → 63.8), H3 PASSED (B8 294/456 ≥ 288).
* Registry-off ablation: recall@5 63.8 → 62.0 (−1.8), mean AUROC 0.767 → 0.732.
* Any result file whose chain marker is absent above was still being (re-)computed under registry 13.3.0 at freeze time and is marked † in the manuscript; the v5.2 figure stands for it until the re-run is appended as an addendum manifest.
