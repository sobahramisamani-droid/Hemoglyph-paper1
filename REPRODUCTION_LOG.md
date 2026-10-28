# Clean-environment reproduction log (2026-10-28)

Performed by the first author's AI agent in a fresh sandbox, from `git clone` of this repository into an empty
directory (`/tmp/hg_clean`), with `reproduce.sh` installing the pinned `requirements.txt`. Python 3.13.16, 2 vCPU,
2 GB RAM, no GPU. Commit under test: `f35c299` (steps 0–4) and the same tree for step 5.

| step | result | wall time | note |
|---|---|---|---|
| 0 integrity | PASS | < 5 s | engine v7 rebuilt from tag `engine-v7-frozen`; 5/6 freeze hashes identical; feature registry reported as `DOCUMENTED-DIFFERENCE` (see below) |
| 1 tests | PASS 720 passed, 9 skipped | 5 min 53 s | property-based invariants and LabPanel-Check reference cards included |
| 2 verification ledger | PASS | ≈ 20 s | rebuilt `ledger_counts.json` identical to the committed Note 18 counts |
| 3 mutation study | PASS | ≈ 1 min | recall table identical to the committed Note 16 table (M1–M8, specificity) |
| 4 NHANES 2017–18, n = 3,000 | PASS — all 9 AUROCs identical to Table 4 | 61 min (+ CDC download ≈ 1 MB) | diabetes 0.946, diabetes self-report 0.919, CKD 0.959, CKD self-report 0.816, anaemia 0.972, iron deficiency 0.989, hypercholesterolaemia 0.905, hyperuricaemia 0.943, ALT 0.872 |
| 5 eICU-CRD demo, 2,314 stays | PASS — flat @3/5/10 47.9/60.8/74.1, two-tier @1/3/5 33.1/62.0/71.9, grouped @1/3/5/10 30.1/55.6/67.4/77.9 identical to Table 3 | 41 min | PhysioNet CSVs copied into the clone by hand (the script does not download them) |

## What the first attempt caught

The first `quick` run on the clean clone **failed at step 2**: two inputs of the ledger build were present in the
working copy but not in the repository (`release/registry_15.2.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br`, which
a `.gitignore` pattern excluded, and `eval/results/source_verification_13.4.1.json.gz`). Both were committed
(`f35c299`) and the run was repeated from step 2. This is exactly the failure class a clean-environment run exists to
expose, and it is reported rather than hidden; no number changed.

## Documented difference

`FREEZE_v15_20261025_sha256.txt` records the feature registry at `953d8daa…`; the repository holds `115427e7…`. The
15.2.0 patch rewrote the file in place (ACTH unit entry; `release/registry_15.2.0/CHANGELOG_15_2_0.md` C3) and the
pre-patch bytes were not archived, so the original hash can no longer be reproduced. ACTH does not occur in any cohort
of the paper; steps 4–5 reproduce the frozen v7 numbers with the current feature registry, which is the empirical
evidence that the difference is immaterial to the reported results. Both registries are now tracked in git (release snapshots and the root files), so the pre-patch bytes of any later patch are recoverable from history; the loss cannot recur in the same way.

## Not covered by `reproduce.sh`

MIMIC-IV demo, PhysioNet/CinC 2019 sepsis sets, UCI thyroid/HCV, ILPD, the PMC case series, the 400 blind LLM readings
(frozen artefacts; the model cannot be re-queried), the ablation and the calibration analyses. Their scripts and
inputs are listed in Supplementary Table S17; they were not re-run in the clean environment.
