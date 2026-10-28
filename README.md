# Hemoglyph — verifying an AI-drafted laboratory-interpretation rule base

Code, rule registries, frozen evaluation outputs and manuscript sources for:

**Verifying an AI-drafted laboratory-interpretation rule base before clinical audit: executable invariants, frozen source-concordance protocols and a hash-frozen benchmark applied to the open Hemoglyph engine** — Bahrami, Tahmasebinejad, Bahrami Samani; submitted to *Computer Methods and Programs in Biomedicine*, 2026.

Research prototype. Not a medical device; not approved or intended for clinical use. The rule base is largely AI-drafted and carries the status `candidate_requires_specialist_validation`; the paper is about how such a rule base can be verified, not a claim that it is correct.

**Start here:** `README_REPRODUCE.md` (one command, `bash reproduce.sh quick`, re-derives the main tables from a clean clone) and `REPRODUCTION_LOG.md` (the authors' own clean-clone run).

## What is here

| Component | Path | Licence |
|---|---|---|
| Inference engine (single file, no training, no network) | `analyse_gidlines.py` (+ `calcu.py`, `cache_registry.py`) | AGPL-3.0-or-later |
| Rule registries, release 14.1.0 (33,183 executable rules, 785 sources; 99.2 % AI-drafted, status `candidate_requires_specialist_validation`) | `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br`, `HEMOGLYPH_GUIDELINE_REGISTRY.json.br` | CC BY-SA 4.0 |
| Verification method 1 — property-based invariant suite (25 tests) | `tests/test_properties.py`, `tests/test_bayes_properties.py` | AGPL-3.0 |
| Safety and regression batteries | `tests/hard_battery.py`, `hard_battery2.py`, `hard_battery3.py`, `tests/healthy_sweep.py`, `tests/perturbation_fuzz.py` | AGPL-3.0 |
| Verification method 2 — source-concordance protocol and frozen sample | `eval/source_audit/PROTOCOL.md`, `eval/source_audit/sample_200.csv`, `eval/registry_source_verify.py` | CC BY-SA 4.0 |
| Verification method 3 — frozen benchmark scripts | `eval/realdata/*.py`, `eval/baselines/*.py`, `eval/ablation/run_ablation.py`, `eval/calibration_dca.py`, `eval/subgroup_fairness.py` | AGPL-3.0 |
| Statistical analysis plan with dated amendments | `docs/paper1/supplement/SAP_Hemoglyph_v1.md` | CC BY-SA 4.0 |
| Freeze manifests (SHA-256) | `FREEZE_v14_20261025_*`, `FREEZE_v15_20261025_*` | — |
| Manuscript, supplement, figures | `docs/paper1/v7/` | CC BY 4.0 (text) |

## Requirements

Python ≥ 3.11; `numpy`, `pandas`, `brotli` for the engine; additionally `scikit-learn`, `scipy`, `pytest`, `matplotlib`, `openpyxl` for the evaluation. No GPU. One panel is processed in about one second on one CPU core.

```bash
pip install numpy pandas brotli scikit-learn scipy pytest matplotlib openpyxl
```

## Ten-minute check

```bash
sha256sum -c --ignore-missing FREEZE_v15_20261025_sha256.txt   # expected differences (engine now v8.2, registries 15.x, amended SAP) are listed in REPRODUCTION_LOG.md; engine v7 is rebuilt from tag engine-v7-frozen by reproduce.sh
python -m pytest tests/test_properties.py -q        # the 25 invariant tests of Section 2.3
python tests/hard_battery.py && python tests/healthy_sweep.py
python examples_quickstart.py                       # one panel in, cited differential out (~1 s)
```

## Reproducing the tables and figures

The mapping from every table and figure to its script, input data and engine version is the *Reproducibility map* at the end of the Supplementary Information (`docs/paper1/v7/submission_CMPB/Supplementary_Information_R8.md`); `reproduce.sh` automates the frozen-engine steps. Public inputs: eICU-CRD demo v2.0.1 and MIMIC-IV demo (PhysioNet, credential-free), NHANES 2013–14 / 2015–16 / 2017–18 (CDC), PhysioNet/CinC 2019, UCI thyroid0387, UCI HCV, ILPD, PMC-Patients. Download helpers are in `eval/realdata/`. The 400 blinded LLM prompts and raw outputs are frozen artefacts under `eval/results/eicu_demo/` and are re-scored, never regenerated.

Full run on one core: about 10 h. `eval/realdata/eval_eicu.py --encounter icu` alone reproduces Table 3 in about 40 min.

## What is not here

Patient data (download from the sources above); the desktop application built on this engine (separate, proprietary, not part of the paper); any clinician evaluation (none was performed for this paper — the pre-specified protocol is Supplementary Note 19).

## Contact

Sobhan Bahrami — sobahramisamani@gmail.com — ORCID 0009-0004-6639-5081

## Licence

- Engine source code: GNU AGPL-3.0-or-later (`LICENSE`).
- Rule registries (`HEMOGLYPH_*_REGISTRY.json.br`, `release/registry_*`) and aggregated evaluation outputs: CC BY-SA 4.0 (`LICENSE-DATA.md`), with the provenance notice that the registries were AI-drafted and single-author curated.
- Manuscript text and figures: CC BY 4.0.
