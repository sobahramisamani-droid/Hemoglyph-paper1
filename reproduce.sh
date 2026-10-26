#!/bin/bash
# One-command reproduction of the Paper 1 evaluation (engine v5.2 freeze).  Linux/macOS, Python >= 3.11, ~2 GB RAM, no GPU.
#   bash reproduce.sh            # everything (~10 h single core; eICU 3 arms ~1.7 h, NHANES 7 cycles ~6 h, CinC-2019 ~1 h)
#   bash reproduce.sh quick      # gate only (unit tests + synthetic batteries + safety, ~15 min)
# Datasets are downloaded by the scripts in eval/realdata/ from their public sources (eICU-CRD demo, NHANES, PhysioNet/CinC 2019,
# UCI, ILPD, MIMIC-IV demo); nothing is bundled.  Every result file lands in eval/results/<cohort>/.
set -e; cd "$(dirname "$0")"
python3 -m pip install -q brotli pandas numpy pytest scikit-learn matplotlib
echo "== 0. integrity: compare engine + registries against the freeze =="
sha256sum -c FREEZE_v5.2_20261023_sha256.txt 2>/dev/null | grep -v ': OK' || echo "freeze OK"
echo "== 1. gate: unit tests, synthetic batteries, safety =="
python3 -m pytest -q tests/ 2>&1 | tail -1
for b in engine_battery hard_battery hard_battery2 hard_battery3 adversarial_battery; do python3 tests/$b.py | grep SCORE; done
python3 tests/healthy_sweep.py --n 200 --seed 1 | tail -1
python3 tests/fabrication_provocation.py | tail -1
[ "$1" = quick ] && exit 0
echo "== 2. eICU-CRD demo: labs-only, +context, +temporal, +both =="
python3 eval/realdata/eval_eicu.py                     # -> eval/results/eicu_demo/report.md, per_stay.json
python3 eval/realdata/eval_eicu.py --context --suffix _ctx
python3 eval/realdata/eval_eicu.py --temporal --suffix _tmp
python3 eval/realdata/eval_eicu.py --context --temporal --suffix _ctxtmp
python3 eval/error_audit.py --per-stay eval/results/eicu_demo/per_stay.json --label v5.2 --out eval/results/eicu_demo/error_audit_v5_2.md
python3 eval/subgroup_fairness.py --per-stay eval/results/eicu_demo/per_stay.json --out eval/results/eicu_demo/subgroup_fairness_v5_2.md
python3 eval/realdata/calibration_and_baseline.py
python3 eval/calibration_dca.py --per-stay eval/results/eicu_demo/per_stay.json --label v5.3 --out eval/results/eicu_demo/calibration_dca_v5_3.md --fig eval/results/eicu_demo/reliability_dca_v5_3.png
python3 eval/baselines/ml_baseline_eicu.py
python3 eval/baselines/b8_score.py                     # blind LLM read-outs are stored; this only re-scores them
echo "== 3. NHANES 2005-2018 (7 cycles), UCI, ILPD, CinC-2019 =="
for c in J I H G F E D; do python3 eval/realdata/fetch_nhanes_cycle.py $c; python3 eval/realdata/eval_nhanes.py --cycle $c --n-max 100000; done
python3 eval/realdata/eval_uci_hcv.py; python3 eval/realdata/eval_ilpd.py; python3 eval/realdata/eval_uci_thyroid.py
python3 eval/realdata/eval_sepsis2019.py
echo "== 4. figures + manuscript =="
( cd docs/paper1/v53 && python3 extract_numbers.py && python3 render.py && python3 render_fa.py && python3 make_figures_v53.py )   # EN + FA manuscripts, supplement, figures 2–6, S2
echo DONE
