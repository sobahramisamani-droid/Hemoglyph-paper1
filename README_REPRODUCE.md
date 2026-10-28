# Reproducing the Paper 1 evaluation

```bash
git clone <repo> Hemoglyph && cd Hemoglyph
bash reproduce.sh quick     # 15 min: integrity check against FREEZE_v5.3 + unit tests + synthetic/safety gate
bash reproduce.sh           # ~10 h on one core: all public cohorts, baselines, calibration, figures, manuscript
```

| step | script | output |
|---|---|---|
| integrity | `sha256sum -c FREEZE_v5.3_*_sha256.txt` | engine + registries byte-identical to the frozen version |
| gate | `pytest tests/`, `tests/*_battery.py`, `healthy_sweep.py`, `fabrication_provocation.py` | 665 unit tests; 489/489 synthetic cases; 0 healthy false positives; 200/200 fabrication refusals |
| eICU-CRD demo | `eval/realdata/eval_eicu.py [--context] [--temporal]` | `eval/results/eicu_demo/report*.md`, `per_stay*.json` |
| audits | `eval/error_audit.py`, `eval/subgroup_fairness.py`, `eval/calibration_dca.py`, `eval/realdata/calibration_and_baseline.py` | error taxonomy, fairness, calibration + decision curves, B1 baseline, S5 safety |
| baselines | `eval/baselines/ml_baseline_eicu.py`, `eval/baselines/b8_score.py` | supervised ML (B2); blind LLM read-outs re-scored (B3/B4/B8, n = 400) |
| NHANES | `eval/realdata/fetch_nhanes_cycle.py <letter>` then `eval_nhanes.py --cycle <letter>` | `eval/results/nhanes_<year>/report.md` |
| other cohorts | `eval_uci_hcv.py`, `eval_ilpd.py`, `eval_uci_thyroid.py`, `eval_sepsis2019.py` | per-cohort `report.md` + per-subject JSON |
| manuscript | `docs/paper1/make_figures_paper1.py`, `docs/paper1/build_paper1_en.py --v4` | `docs/paper1/figures/*.png`, `Paper1_Hemoglyph_npj_EN.docx` |

Data licences: eICU-CRD demo and MIMIC-IV demo (PhysioNet open data, ODbL/credential-free demo), NHANES (public domain), PhysioNet/CinC 2019 (ODC-By 1.0), UCI HCV/ILPD/thyroid (CC BY 4.0). Raw downloads are not redistributed in this repository; the scripts fetch them.

The blind LLM read-outs (`eval/results/eicu_demo/{llm_agent_b3_n100,b4_llm_blind_n60,b8_llm_blind_n240}.json`) are frozen artefacts: they were produced by a frontier-tier LLM whose identity the platform does not disclose, operating through an agent interface, from panels containing only age, sex and laboratory values, before the labels or engine outputs were opened. They are re-scored, not regenerated, by `reproduce.sh`.

## Added 2026-10-23
* `eval/realdata/eval_pmc_cases.py` — B6: 50 PMC-Patients vignettes (Bhasuran 2025), three arms (parser / manual / manual_strict); key and panels in `eval/realdata/pmc_cases/`.
* `eval/make_benchmark_package.py` — builds `eval/results/labbench/Hemoglyph-LabBench-v1.zip`; `eval/baselines/labbench_score.py` scores any system on the 240 blind panels.
* `eval/patches/registry_v13_2_0_exposure_gate.py` (+ `test_registry_v13_2_0.py`, `tests/test_registry_v13_2_exposure_gate.py`) — registry 13.2.0 candidate; apply with `--apply` only after the v5.2 freeze.
* `eval/deep_review_ctx_sex.py` — context-echo decomposition and sex-gap standardisation (SAP Amendment 11).
* `eval/human/A1_rule_audit_form_ANNEX_flagged.csv` — 7 non-random suspect rules for the physician, scored separately.


### Registry activation note (2026-10-23 evening)
The engine loads `HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br` (`DEFAULT_DISEASE_REGISTRY_PATH`); `HEMOGLYPH_GUIDELINE_REGISTRY.json.br` is the distribution copy and `preflight_check.py` requires the two to be identical. Registry 13.2.0 + 13.3.0 were activated at 21:03 UTC by copying the 13.3.0 candidate to **both** files (backups `*.bak_v13_1_0`). An earlier activation at 19:43 UTC updated only the distribution copy; the v5.3 gate/eICU results produced between 19:43 and 21:00 therefore ran on 13.1.0 and were moved to `eval/results/run_20261023_v53/invalid_ran_on_13_1_0/` (kept only as evidence; not reported). The patch scripts' `--apply` now updates both files.

## LabPanel-Check (black-box conformance package)

`eval/labpanel_check/` — 290 frozen panels, label map, standard-library scorer and two reference cards. Score any reader: `python3 eval/labpanel_check/score.py READS.json --label NAME`. `pytest tests/test_labpanel_check.py` asserts that the shipped reference readings reproduce the manuscript's Table 6 / Note 13 figures (see the package README for the two documented differences).
