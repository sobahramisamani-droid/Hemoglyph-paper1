#!/bin/bash
# Amendment 14 development chain (sequential, low memory): eICU grouped-rank run, NHANES J (community), Sepsis-2019 set A (ICU) concurrent + prediction
cd /home/user/Hemoglyph; G=eval/results/gate_14_0_0
python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v1400 > $G/eicu_run3g.log 2>&1; echo "exit $?" >> $G/eicu_run3g.log; echo CHAIN_EICU_DONE > $G/STATUS
python3 eval/realdata/eval_nhanes.py --cycle J --encounter community --suffix _v1400 > $G/nhanesJ_v1400.log 2>&1; echo "exit $?" >> $G/nhanesJ_v1400.log; echo CHAIN_NHANES_DONE > $G/STATUS
python3 eval/realdata/eval_sepsis2019_concurrent.py --registry HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br --encounter icu --suffix _v1400 > $G/sepsisA_conc_v1400.log 2>&1; echo "exit $?" >> $G/sepsisA_conc_v1400.log; echo CHAIN_SEPSIS_CONC_DONE > $G/STATUS
python3 eval/realdata/eval_sepsis2019.py --encounter icu --suffix _v1400 > $G/sepsisA_pred_v1400.log 2>&1; echo "exit $?" >> $G/sepsisA_pred_v1400.log; echo CHAIN_ALL_DONE > $G/STATUS
