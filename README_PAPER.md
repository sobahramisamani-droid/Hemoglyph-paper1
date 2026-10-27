# Hemoglyph — research artefacts for the paper

**Verification and provenance auditing of an AI-drafted clinical rule base: executable invariants, a source-concordance protocol and a frozen laboratory-panel benchmark for an offline interpretation engine** (Bahrami, Tahmasebinejad, Bahrami Samani; submitted to *Computer Methods and Programs in Biomedicine*, 2026).

Research prototype. Not approved or intended for clinical use. The product README is `README.md`; this file is the entry point for reviewers and for anyone reproducing the paper.

## What is here

| Component | Path | Licence |
|---|---|---|
| Inference engine (single file, no training, no network) | `analyse_gidlines.py` (+ `calcu.py`, `cache_registry.py`) | AGPL-3.0-or-later |
| Rule registries, release 14.1.0 (33,183 executable rules, 785 sources; 99.2 % AI-drafted, status `candidate_requires_specialist_validation`) | `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br`, `HEMOGLYPH_GUIDELINE_REGISTRY.json.br` | CC BY-SA 4.0 |
| Verification method 1 — property-based invariant suite (21 tests) | `tests/test_properties.py`, `tests/test_bayes_properties.py` | AGPL-3.0 |
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
sha256sum -c FREEZE_v15_20261025_sha256.txt        # engine + registry byte-identical to the frozen v7 / 14.1.0
python -m pytest tests/test_properties.py -q        # the 21 invariants of Section 2.3
python tests/hard_battery.py && python tests/healthy_sweep.py
python analyse_gidlines.py --demo                   # one annotated panel, cited differential on stdout
```

## Reproducing the tables and figures

The mapping from every table and figure to its script, input data and engine version is the *Reproducibility map* at the end of the Supplementary Information (`docs/paper1/v7/submission_CMPB/Supplementary_Information_R6.docx`). Public inputs: eICU-CRD demo v2.0.1 and MIMIC-IV demo (PhysioNet, credential-free), NHANES 2013–14 / 2015–16 / 2017–18 (CDC), PhysioNet/CinC 2019, UCI thyroid0387, UCI HCV, ILPD, PMC-Patients. Download helpers are in `eval/realdata/`. The 400 blinded LLM prompts and raw outputs are frozen artefacts under `eval/results/eicu_demo/` and are re-scored, never regenerated.

Full run on one core: about 10 h. `eval/realdata/eval_eicu.py --encounter icu` alone reproduces Table 3 in about 40 min.

## What is not here

Patient data (download from the sources above); the proprietary desktop packaging; any clinician evaluation (none was performed for this paper).

## Contact

Sobhan Bahrami — sobahramisamani@gmail.com — ORCID 0009-0004-6639-5081
