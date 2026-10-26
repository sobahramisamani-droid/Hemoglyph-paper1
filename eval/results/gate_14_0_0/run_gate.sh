#!/bin/bash
# Gate 14.0.0 (development data only): pytest, hard batteries 1-3, fuzz, eICU labs-only (encounter=icu) — sequential, low memory
cd /home/user/Hemoglyph; G=eval/results/gate_14_0_0
python3 -m pytest -q -x tests/ > $G/pytest.txt 2>&1; echo "pytest exit $?" >> $G/pytest.txt
python3 tests/hard_battery.py > $G/hard1.txt 2>/dev/null; echo "exit $?" >> $G/hard1.txt
python3 tests/hard_battery2.py > $G/hard2.txt 2>/dev/null; echo "exit $?" >> $G/hard2.txt
python3 tests/hard_battery3.py > $G/hard3.txt 2>/dev/null; echo "exit $?" >> $G/hard3.txt
echo GATE_UNIT_DONE > $G/STATUS
python3 eval/realdata/eval_eicu.py --encounter icu --suffix _v1400 > $G/eicu_run.log 2>&1; echo "exit $?" >> $G/eicu_run.log
echo GATE1400_DONE > $G/STATUS
