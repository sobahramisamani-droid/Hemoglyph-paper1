# Reproducing Paper 1 (CMPB submission) from a clean clone

```bash
git clone https://github.com/sobahramisamani-droid/Hemoglyph && cd Hemoglyph
bash reproduce.sh quick   # ≈ 8 min: integrity, 720 tests, verification ledger, mutation table
bash reproduce.sh v7      # quick + frozen v7 on NHANES 2017-18 (downloads ≈ 1 MB from CDC; ≈ 60 min on one core)
bash reproduce.sh eicu    # quick + frozen v7 on eICU-CRD demo (needs the PhysioNet demo CSVs, see below; ≈ 1 h)
bash reproduce.sh all     # everything above
```

Every step prints `PASS` or `FAIL` and the script exits non-zero on the first failure. Python ≥ 3.11; pinned
dependencies in `requirements.txt` (installed by the script). No GPU, ≈ 1 GB RAM.

## What each step verifies

| step | what | compared against |
|---|---|---|
| 0 integrity | `tools/make_frozen_engine_dir.py` assembles engine **v7** from git tag `engine-v7-frozen` plus registry 14.1.0 into `/tmp/hemoglyph_v7` and checks every file against `FREEZE_v15_20261025_sha256.txt`; registries 14.1.0 / 15.1.0 / 15.3.0 against their `SHA256SUMS.txt` | freeze manifests |
| 1 tests | `pytest tests` — unit tests, property-based invariants (`tests/test_properties.py`), LabPanel-Check reference cards (Table 6) | 720 passed, 9 skipped |
| 2 ledger | `eval/verification_ledger/build_ledger.py` rebuilt from the committed frozen inputs | `ledger_counts.json` (Note 18) must be identical |
| 3 mutation | `eval/audit/mutate.py` on registry 15.1.0 with the frozen detectors | `mutation_results.json.gz` recall table (Note 16, Fig. 3c) must be identical |
| 4 NHANES | `eval/realdata/eval_nhanes.py --cycle J --n-max 3000 --encounter community --engine-dir /tmp/hemoglyph_v7` | `eval/results/nhanes_2017/report_v7.md` (headline AUROCs) via `tools/compare_reports.py` |
| 5 eICU | `eval/realdata/eval_eicu.py --encounter icu --engine-dir /tmp/hemoglyph_v7` | `eval/results/eicu_demo/report_v7.md` (Table 3: top-k, two-tier, AUROC) |

Result of the run performed by the authors on a clean clone: `REPRODUCTION_LOG.md` (also Supplementary Note 21).

## Known, documented difference

`FREEZE_v15_20261025_sha256.txt` lists the feature registry `HEMOGLYPH_FEATURE_REGISTRY.json.br` with hash
`953d8daa…`. The file in the repository has hash `115427e7…`: the 15.2.0 patch script rewrote it in place (ACTH unit
entry only; `release/registry_15.2.0/CHANGELOG_15_2_0.md`, item C3), and no copy of the pre-patch bytes exists. Step 0 reports this
as `DOCUMENTED-DIFFERENCE`, not as a failure. ACTH does not occur in any cohort of the paper, so no reported number
depends on it; the v7 results reproduced in steps 4–5 are produced with the current feature registry.

## Data

| cohort | how obtained | licence |
|---|---|---|
| NHANES 2017–18 (cycle J) | fetched automatically by `eval/realdata/fetch_nhanes_cycle.py J` | public domain |
| eICU-CRD demo 2.0.1 | download the CSVs from physionet.org/files/eicu-crd-demo/2.0.1/ into `eval/realdata/eicu_demo/` (`lab.csv.gz`, `patient.csv.gz`, `diagnosis.csv.gz`, `pastHistory.csv.gz`) | PhysioNet open demo |
| MIMIC-IV demo, PhysioNet/CinC 2019, UCI HCV / thyroid, ILPD | as described in Supplementary Table S17; not part of `reproduce.sh` | public |

The 400 blind LLM read-outs are frozen artefacts (the model cannot be re-queried; Note 2). All scripts that produced a
number in the paper are listed in Supplementary Table S17 with their inputs and the engine/registry version.

## Registry versions in this repository

| version | role | tracked file |
|---|---|---|
| 14.1.0 | frozen with engine v7; every main-text benchmark | `release/registry_14.1.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br` |
| 15.1.0 | calibration set of the audit study (Note 16) | `release/registry_15.1.0/…` |
| 15.2.0 | verification-ledger snapshot (Note 18) | `release/registry_15.2.0/…` |
| 15.3.0 | current release; seed pool of the held-out mutation test (Note 20) | `release/registry_15.3.0/…` and the root registry |

Engine v8.2 (current `analyse_gidlines.py`) is a development version; v7 is reconstructed from the git tag.
