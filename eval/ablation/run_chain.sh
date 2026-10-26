#!/bin/bash
# sequential ablation chain (one process at a time: ~2 GB sandbox); resumable — finished arms are skipped.
cd /home/user/Hemoglyph
for arm in no_bayesian no_fuzzy no_graph no_risk no_esl dempster uniform_w no_shrink anchor_only no_rule no_unverified w_rule_heavy w_rule_light anchor_only_no_esl; do
  if [ -f eval/results/eicu_demo/ABL_$arm.done ]; then echo "skip $arm"; continue; fi
  echo "=== $arm $(date)"; python3 eval/ablation/run_ablation.py $arm > eval/results/eicu_demo/abl_$arm.log 2>&1 || echo "FAILED $arm"
  rm -f eval/results/eicu_demo/per_stay_abl_$arm.json eval/results/eicu_demo/per_stay_abl_$arm.partial.json
done
python3 eval/ablation/run_ablation.py --summarise > /dev/null 2>&1; echo ABL_ALL_DONE $(date)
