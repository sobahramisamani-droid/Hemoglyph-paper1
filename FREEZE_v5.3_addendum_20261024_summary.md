# FREEZE v5.3 — 2026-10-24 13:24 UTC

* Engine: analyse_gidlines.py (release 1.3.1, v5.3 evaluation build); disease–guideline registry 13.4.2-CLINICAL-CURATED — entities 6750, rules 34659, executable 33170; feature registry 2,045 analytes.
* Manifest: `FREEZE_v5.3_addendum_20261024_sha256.txt` — 323 files, 37.8 MB. Verify with `sha256sum -c FREEZE_v5.3_addendum_20261024_sha256.txt`.
* Chain markers present at freeze: ablation_regoff, audit53, cal53, eicu53, eicu53_ctx, eicu53_ctxtmp, gate53, hcv53, healthy1k, ilpd53, nhfull_D, nhfull_E, nhfull_F, nhfull_G, nhfull_H, nhfull_I, nhfull_J, nt53, pert3, pmc53, sepsis19, subg53, thyroid53, twin.
* Headline (eICU-CRD demo, 2,314 stays, labs only): recall@3/5/10 = 49.3 / 63.8 / 77.2 %; +context 52.1 / 66.6 / 79.8; +context+temporal 51.7 / 66.2 / 80.2; mean AUROC 0.767 (k = 24).
* Pre-registered hypotheses (SAP Amendment 12): H1 FAILED (sex gap 4.4 → 4.3), H2 PASSED (63.7 → 63.8), H3 PASSED (B8 294/456 ≥ 288).
* Registry-off ablation: recall@5 63.8 → 62.0 (−1.8), mean AUROC 0.767 → 0.732.
* ADDENDUM: chain V53_ALLDONE — every held-out re-run (NHANES 2017–18 cycle J, Sepsis-2019, healthy-1000, perturbation, unit-twin) completed under registry 13.3.0; no † remains in the manuscript. NHANES J: diabetes 0.941, CKD 0.959, anaemia 0.971, iron deficiency 0.989; Sepsis-2019 AUROC 0.593 (logistic 0.689); healthy sweep 0/1000; perturbation 755/755; unit-twin 149/149. Provenance audit: Supplementary Data 1 (13.4.1), 9 fabricated DOIs removed in release 13.4.1 (rule logic = 13.4.0); shipped registry 13.4.2 (nine D19 finding rules demoted after an eICU top-5 crowding regression: 13.4.1 61.7 % → 13.4.2 63.7 % vs 13.3.0 63.8 %; full gate green).
