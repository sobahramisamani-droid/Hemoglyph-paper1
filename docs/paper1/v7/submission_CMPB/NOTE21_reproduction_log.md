## Supplementary Note 21 — Clean-environment reproduction of the frozen results (one command; log of the authors' run)

**What was done.** The repository was cloned into an empty directory on a fresh machine image (Python 3.13, 2 vCPU, 2 GB RAM, no GPU) and `bash reproduce.sh` was run in its `quick`, `v7` and `eicu` modes. The script (i) rebuilds engine v7 from the git tag `engine-v7-frozen` and registry 14.1.0 into a separate directory and checks every file against the freeze manifest, (ii) runs the 729 tests including the property-based invariants and the LabPanel-Check reference cards, (iii) rebuilds the verification ledger (Note 18) and the mutation table (Note 16) from the committed frozen inputs and requires them to be identical to the committed outputs, (iv) runs the frozen v7 engine on NHANES 2017–18 (downloaded from CDC by the script) and (v) on the eICU-CRD demo (PhysioNet CSVs supplied by the user), and compares the headline numbers with the frozen reports of Tables 3 and 4 by exact string match, failing on any difference. The full log of this run is `REPRODUCTION_LOG.md` in the repository.

**Results.**

| step | outcome | time |
|---|---|---|
| 0 integrity (freeze manifest; three registry `SHA256SUMS`) | PASS; feature registry reported as a documented difference (below) | seconds |
| 1 tests | 720 passed, 9 skipped | 6 min |
| 2 verification ledger rebuilt | identical to the committed Note 18 counts | 20 s |
| 3 mutation table rebuilt | identical to the committed Note 16 table | 1 min |
| 4 NHANES 2017–18, n = 3,000, frozen v7 | all nine AUROCs identical to Table 4 (0.946, 0.919, 0.959, 0.816, 0.972, 0.989, 0.905, 0.943, 0.872) | 61 min |
| 5 eICU-CRD demo, 2,314 stays, frozen v7 | flat recall@3/5/10 47.9/60.8/74.1, two-tier @1/3/5 33.1/62.0/71.9 and grouped @1/3/5/10 30.1/55.6/67.4/77.9 — all identical to Table 3 | 41 min |

**What the run exposed.** The first clean-clone attempt failed at step 2 because two inputs of the ledger build existed only in the authors' working copy (one registry snapshot excluded by a `.gitignore` pattern and one source-verification file). They were committed and the run repeated; no number changed. We report this because it is precisely the class of defect that a clean-environment run exists to find, and because an earlier revision of this paper cited those files as if they were public.

**Documented difference.** The freeze manifest of 2026-10-25 records the feature registry at SHA-256 `953d8daa…`; the repository holds `115427e7…`. The 15.2.0 patch rewrote the file in place to correct the ACTH unit entry and the pre-patch bytes were not archived, so the original hash cannot be reproduced. ACTH occurs in no cohort of this paper, and steps 4 and 5 reproduce the frozen v7 numbers with the current file, which is the empirical evidence that the difference is immaterial. Both registries are now tracked in git, so the loss cannot recur in the same way.

**Not covered.** MIMIC-IV demo, the sepsis sets, UCI/ILPD, the PMC case series, the ablation and calibration analyses and the 400 blind LLM readings (frozen artefacts; Note 2) are not part of `reproduce.sh`; their scripts and inputs are listed in Table S17 and were not re-run in the clean environment.
