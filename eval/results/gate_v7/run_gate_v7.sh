#!/bin/bash
# Engine v7 development gate (SAP Amendment 15). Two lanes in parallel (RAM ~2 GB allows two processes).
cd /home/user/Hemoglyph; G=eval/results/gate_v7; rm -f $G/STATUS
( python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v7 > $G/eicu_v7.log 2>&1; echo "exit $?" >> $G/eicu_v7.log; echo G7_EICU_DONE >> $G/STATUS
  python3 eval/mimic/multilabel_eval.py --mimic-dir eval/quarantine/mimic_iv_demo --out $G/mimic_v7 --encounter inpatient > $G/mimic_v7.log 2>&1; echo "exit $?" >> $G/mimic_v7.log; echo G7_MIMIC_DONE >> $G/STATUS ) &
( for b in hard_battery hard_battery2 hard_battery3; do python3 tests/$b.py > $G/${b}_v7.txt 2>&1; echo "exit $?" >> $G/${b}_v7.txt; done
  python3 tests/healthy_sweep.py --n 1000 --seed 7 > $G/healthy_v7.txt 2>&1; echo "exit $?" >> $G/healthy_v7.txt
  python3 tests/perturbation_fuzz.py --battery hard_battery --noise 0.03 --reps 5 --seed 1 > $G/pert3_v7.txt 2>&1; echo "exit $?" >> $G/pert3_v7.txt
  python3 eval/probes/probe_v14.py > $G/probe_v7.txt 2>&1
  echo G7_UNIT_DONE >> $G/STATUS ) &
wait
python3 -m pytest tests -q -x --no-header -p no:cacheprovider > $G/pytest_v7.txt 2>&1; echo "exit $?" >> $G/pytest_v7.txt
echo G7_ALL_DONE >> $G/STATUS
