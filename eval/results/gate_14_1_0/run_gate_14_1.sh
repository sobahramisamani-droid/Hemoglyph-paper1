#!/bin/bash
# Gate 14.1.0 (dev data): unit gate, then eICU v14.1 (lane 1) and Sepsis set A concurrent + prediction (lane 2)
cd /home/user/Hemoglyph; G=eval/results/gate_14_1_0; rm -f $G/STATUS
python3 -m pytest -q -x tests/ > $G/pytest.txt 2>&1; echo "pytest exit $?" >> $G/pytest.txt
python3 tests/hard_battery.py > $G/hard1.txt 2>/dev/null; echo "exit $?" >> $G/hard1.txt
python3 tests/hard_battery2.py > $G/hard2.txt 2>/dev/null; echo "exit $?" >> $G/hard2.txt
python3 tests/hard_battery3.py > $G/hard3.txt 2>/dev/null; echo "exit $?" >> $G/hard3.txt
echo G141_UNIT_DONE >> $G/STATUS
( python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v1410 > $G/eicu_v1410.log 2>&1; echo "exit $?" >> $G/eicu_v1410.log; echo G141_EICU_DONE >> $G/STATUS ) &
( python3 eval/realdata/eval_sepsis2019_concurrent.py --registry HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br --encounter icu --suffix _v1410 > $G/sepsisA_conc_v1410.log 2>&1; echo "exit $?" >> $G/sepsisA_conc_v1410.log; echo G141_CONC_DONE >> $G/STATUS
  python3 eval/realdata/eval_sepsis2019.py --encounter icu --suffix _v1410 > $G/sepsisA_pred_v1410.log 2>&1; echo "exit $?" >> $G/sepsisA_pred_v1410.log; echo G141_PRED_DONE >> $G/STATUS ) &
wait; echo G141_ALL_DONE >> $G/STATUS
