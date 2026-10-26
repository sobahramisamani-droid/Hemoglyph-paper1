#!/bin/bash
# SAP Amendment 15 — ONE-SHOT quarantine run (engine v7, registry 14.1.0). Run only after FREEZE_v15. Never re-run after a change.
cd /home/user/Hemoglyph; V=eval/results/validation_v15; rm -f $V/STATUS
test -f FREEZE_v15_*_sha256.txt || { echo "NO FREEZE"; exit 1; }
SB2=eval/quarantine_v15/sepsis2019_setB2/training_setB2_sub5000.csv.gz
( python3 eval/realdata/eval_sepsis2019_concurrent.py --data $SB2 --registry HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br --encounter icu --suffix _setB2_v7 > $V/setB2_conc_v7.log 2>&1; echo "exit $?" >> $V/setB2_conc_v7.log; echo V15_SETB2_CONC_DONE >> $V/STATUS
  python3 eval/realdata/eval_sepsis2019.py --data $SB2 --encounter icu --suffix _setB2_v7 > $V/setB2_pred_v7.log 2>&1; echo "exit $?" >> $V/setB2_pred_v7.log; echo V15_SETB2_PRED_DONE >> $V/STATUS ) &
( python3 eval/realdata/eval_nhanes.py --cycle I --data-dir eval/quarantine_v15/nhanes_2015_I --encounter community --suffix _v7 > $V/nhanesI_v7.log 2>&1; echo "exit $?" >> $V/nhanesI_v7.log; echo V15_NHANESI_DONE >> $V/STATUS
  python3 tests/healthy_sweep.py --n 1000 --seed 15 > $V/healthy_v7_s15.txt 2>&1; echo V15_HEALTHY_DONE >> $V/STATUS ) &
wait; echo V15_ALL_DONE >> $V/STATUS
