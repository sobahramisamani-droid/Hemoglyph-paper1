#!/bin/bash
# SAP Amendment 14 — ONE-SHOT validation on quarantined data. Run ONLY after FREEZE_v14_*_sha256.txt exists.
# Arms: v14.1 (live registry 14.1.0 + engine v6) and control (frozen registry 13.3.0 + the SAME engine v6; the 13.3.0-era engine is not
# available, so the control isolates the registry, not the engine). Two lanes, low memory.
cd /home/user/Hemoglyph; V=eval/results/validation_v14; rm -f $V/STATUS
ls FREEZE_v14_*_sha256.txt >/dev/null 2>&1 || { echo "NO FREEZE MANIFEST — refusing to open quarantine" | tee $V/STATUS; exit 1; }
R133=eval/frozen_registry_13_3_0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br
SB=eval/quarantine/sepsis2019_setB/training_setB_sub5000.csv.gz
# lane 1: Sepsis-2019 set B
( python3 eval/realdata/eval_sepsis2019_concurrent.py --data $SB --registry HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br --encounter icu --suffix _setB_v1410 > $V/setB_conc_v1410.log 2>&1; echo "exit $?" >> $V/setB_conc_v1410.log; echo V_SETB_CONC_V14_DONE >> $V/STATUS
  python3 eval/realdata/eval_sepsis2019_concurrent.py --data $SB --registry $R133 --suffix _setB_ctrl133 > $V/setB_conc_ctrl133.log 2>&1; echo "exit $?" >> $V/setB_conc_ctrl133.log; echo V_SETB_CONC_CTRL_DONE >> $V/STATUS
  python3 eval/realdata/eval_sepsis2019.py --data $SB --encounter icu --suffix _setB_v1410 > $V/setB_pred_v1410.log 2>&1; echo "exit $?" >> $V/setB_pred_v1410.log; echo V_SETB_PRED_V14_DONE >> $V/STATUS
  python3 eval/realdata/eval_sepsis2019.py --data $SB --registry $R133 --suffix _setB_ctrl133 > $V/setB_pred_ctrl133.log 2>&1; echo "exit $?" >> $V/setB_pred_ctrl133.log; echo V_SETB_PRED_CTRL_DONE >> $V/STATUS ) &
# lane 2: MIMIC-IV demo (full, 275 admissions) then NHANES 2013-14 (H)
( python3 eval/mimic/multilabel_eval.py --mimic-dir eval/quarantine/mimic_iv_demo --out $V/mimic_v1410 --encounter inpatient > $V/mimic_v1410.log 2>&1; echo "exit $?" >> $V/mimic_v1410.log; echo V_MIMIC_V14_DONE >> $V/STATUS
  python3 eval/mimic/multilabel_eval.py --mimic-dir eval/quarantine/mimic_iv_demo --out $V/mimic_ctrl133 --registry $R133 > $V/mimic_ctrl133.log 2>&1; echo "exit $?" >> $V/mimic_ctrl133.log; echo V_MIMIC_CTRL_DONE >> $V/STATUS
  python3 eval/realdata/eval_nhanes.py --cycle H --data-dir eval/quarantine/nhanes_2013_H --encounter community --suffix _v1410 > $V/nhanesH_v1410.log 2>&1; echo "exit $?" >> $V/nhanesH_v1410.log; echo V_NHANESH_V14_DONE >> $V/STATUS
  python3 eval/realdata/eval_nhanes.py --cycle H --data-dir eval/quarantine/nhanes_2013_H --registry $R133 --suffix _ctrl133 > $V/nhanesH_ctrl133.log 2>&1; echo "exit $?" >> $V/nhanesH_ctrl133.log; echo V_NHANESH_CTRL_DONE >> $V/STATUS ) &
wait
# safety sweeps on the frozen engine (synthetic, not quarantined)
python3 tests/healthy_sweep.py --n 1000 --seed 7 > $V/healthy_1000_s7.txt 2>&1
python3 tests/perturbation_fuzz.py --battery hard_battery --noise 0.03 --reps 5 --seed 1 > $V/pert3_hard.txt 2>&1
echo V_ALL_DONE >> $V/STATUS
