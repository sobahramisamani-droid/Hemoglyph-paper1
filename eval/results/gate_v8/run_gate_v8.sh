#!/bin/bash
# Engine v8 development gate (v8 candidate: MELD-Na + PLR indices, confidence bands, registry 14.2.0). Two lanes in parallel (RAM ~2 GB allows two processes).
cd /home/user/Hemoglyph; G=eval/results/gate_v8; rm -f $G/STATUS
( python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v8 > $G/eicu_v8.log 2>&1; echo "exit $?" >> $G/eicu_v8.log; echo G8_EICU_DONE >> $G/STATUS ) &
( for b in hard_battery hard_battery2 hard_battery3; do python3 tests/$b.py > $G/${b}_v8.txt 2>&1; echo "exit $?" >> $G/${b}_v8.txt; done
  python3 tests/healthy_sweep.py --n 1000 --seed 7 > $G/healthy_v8.txt 2>&1; echo "exit $?" >> $G/healthy_v8.txt
  python3 tests/perturbation_fuzz.py --battery hard_battery --noise 0.03 --reps 5 --seed 1 > $G/pert3_v8.txt 2>&1; echo "exit $?" >> $G/pert3_v8.txt
  python3 eval/probes/probe_v14.py > $G/probe_v8.txt 2>&1
  echo G8_UNIT_DONE >> $G/STATUS ) &
wait
python3 -m pytest tests -q -x --no-header -p no:cacheprovider > $G/pytest_v8.txt 2>&1; echo "exit $?" >> $G/pytest_v8.txt
echo G8_ALL_DONE >> $G/STATUS
