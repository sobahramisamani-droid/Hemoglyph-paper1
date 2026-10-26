#!/bin/bash
# Engine v8.1 development gate (covering-inversion fix, measurement-uncertainty reporting, property tests P1-P6).
cd /home/user/Hemoglyph; G=eval/results/gate_v81; rm -f $G/STATUS
( python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v81 > $G/eicu_v81.log 2>&1; echo "exit $?" >> $G/eicu_v81.log; echo G81_EICU_DONE >> $G/STATUS ) &
( for b in hard_battery hard_battery2 hard_battery3; do python3 tests/$b.py > $G/${b}_v81.txt 2>&1; echo "exit $?" >> $G/${b}_v81.txt; done
  python3 tests/healthy_sweep.py --n 1000 --seed 7 > $G/healthy_v81.txt 2>&1; echo "exit $?" >> $G/healthy_v81.txt
  python3 tests/perturbation_fuzz.py --battery hard_battery --noise 0.03 --reps 5 --seed 1 > $G/pert3_v81.txt 2>&1; echo "exit $?" >> $G/pert3_v81.txt
  python3 eval/probes/probe_v14.py > $G/probe_v81.txt 2>&1
  echo G81_UNIT_DONE >> $G/STATUS ) &
wait
python3 -m pytest tests -q -x --no-header -p no:cacheprovider > $G/pytest_v81.txt 2>&1; echo "exit $?" >> $G/pytest_v81.txt
echo G81_ALL_DONE >> $G/STATUS
