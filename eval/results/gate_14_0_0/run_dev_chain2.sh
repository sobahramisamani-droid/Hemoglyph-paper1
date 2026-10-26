#!/bin/bash
# Amendment 14 dev chain 2 (after SIRS-screen downgrade + hypotension support, 2026-10-25): unit gate, then two lanes.
cd /home/user/Hemoglyph; G=eval/results/gate_14_0_0; rm -f $G/STATUS
python3 -m pytest -q -x tests/ > $G/pytest.txt 2>&1; echo "pytest exit $?" >> $G/pytest.txt
python3 tests/hard_battery.py > $G/hard1.txt 2>/dev/null; echo "exit $?" >> $G/hard1.txt
python3 tests/hard_battery2.py > $G/hard2.txt 2>/dev/null; echo "exit $?" >> $G/hard2.txt
python3 tests/hard_battery3.py > $G/hard3.txt 2>/dev/null; echo "exit $?" >> $G/hard3.txt
echo C2_UNIT_DONE >> $G/STATUS
# lane 1: eICU v14 (grouped) then eICU control B grouped (13.4.2 registry, v6 engine, fixed units)
( python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v1400 > $G/eicu_run4.log 2>&1; echo "exit $?" >> $G/eicu_run4.log; echo C2_EICU_DONE >> $G/STATUS
  python3 eval/realdata/eval_eicu.py --encounter icu --engine-dir eval/engine_13_4_2_ref --suffix _v1342_v6engine_g > $G/eicu_ctrlB_g.log 2>&1; echo "exit $?" >> $G/eicu_ctrlB_g.log; echo C2_CTRLB_DONE >> $G/STATUS ) &
# lane 2: sepsis set A concurrent then prediction
( python3 eval/realdata/eval_sepsis2019_concurrent.py --registry HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br --encounter icu --suffix _v1400 > $G/sepsisA_conc_v1400.log 2>&1; echo "exit $?" >> $G/sepsisA_conc_v1400.log; echo C2_CONC_DONE >> $G/STATUS
  python3 eval/realdata/eval_sepsis2019.py --encounter icu --suffix _v1400 > $G/sepsisA_pred_v1400.log 2>&1; echo "exit $?" >> $G/sepsisA_pred_v1400.log; echo C2_PRED_DONE >> $G/STATUS ) &
wait; echo C2_ALL_DONE >> $G/STATUS
