#!/bin/bash
cd /home/user/Hemoglyph; G=eval/results/gate_14_1_0; rm -f $G/STATUS_v61
python3 -m pytest tests -q -x --no-header -p no:cacheprovider > $G/pytest_v61.txt 2>&1; echo "exit $?" >> $G/pytest_v61.txt
for b in hard_battery hard_battery2 hard_battery3; do python3 tests/$b.py > $G/${b}_v61.txt 2>&1; echo "exit $?" >> $G/${b}_v61.txt; done
python3 tests/perturbation_fuzz.py --battery hard_battery --noise 0.03 --reps 5 --seed 1 > $G/pert3_v61.txt 2>&1
python3 tests/healthy_sweep.py --n 1000 --seed 7 > $G/healthy_v61.txt 2>&1
echo G61_UNIT_DONE >> $G/STATUS_v61
python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v1410_e61 > $G/eicu_v61.log 2>&1; echo "exit $?" >> $G/eicu_v61.log
echo G61_ALL_DONE >> $G/STATUS_v61
