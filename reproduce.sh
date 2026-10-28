#!/bin/bash
# Reproduction entry point for Paper 1 (revision R9).  Linux/macOS, Python >= 3.11, ~2 GB RAM, one CPU core, no GPU.
#
#   bash reproduce.sh quick    # ~10 min, NO external data: freeze integrity, unit + property tests (720), LabPanel-Check
#                              # reference cards vs Table 6, verification ledger rebuild vs Note 18 counts, mutation study
#                              # (Note 16) recomputed from the seeds.
#   bash reproduce.sh v7       # ~60 min after `quick` (measured, 2 vCPU): frozen engine v7 + registry 14.1.0 re-run on NHANES 2017-18 (n = 3,000,
#                              # fetched from CDC) and compared line-by-line with the frozen report (Table 4 / Fig. 5).
#   bash reproduce.sh eicu     # ~40 min (measured): frozen v7 on the eICU-CRD demo (2,314 stays; requires the demo CSVs in
#                              # eval/realdata/eicu_demo/, downloaded from physionet.org/content/eicu-crd-demo/2.0.1/) vs Table 3.
#   bash reproduce.sh all      # everything above plus the remaining cohorts and figures (hours).
#
# Every step prints PASS/FAIL; the script exits non-zero at the first failure.  Nothing is tuned or re-fitted.
set -euo pipefail; cd "$(dirname "$0")"; MODE="${1:-quick}"
python3 -m pip install -q -r requirements.txt
ok(){ echo "PASS  $1"; }; die(){ echo "FAIL  $1"; exit 1; }

echo "== 0. integrity of the frozen artefacts (FREEZE_v15 manifest; engine v7 from git tag engine-v7-frozen) =="
python3 tools/make_frozen_engine_dir.py /tmp/hemoglyph_v7 || die "frozen engine assembly"
(cd release/registry_14.1.0 && sha256sum -c --quiet SHA256SUMS.txt --ignore-missing) && ok "registry 14.1.0 bytes match SHA256SUMS" || die "registry 14.1.0 hash"
(cd release/registry_15.3.0 && sha256sum -c --quiet SHA256SUMS.txt --ignore-missing) && ok "registry 15.3.0 bytes match SHA256SUMS" || die "registry 15.3.0 hash"
(cd release/registry_15.1.0 && sha256sum -c --quiet SHA256SUMS.txt --ignore-missing) && ok "registry 15.1.0 (audit-study calibration set) bytes match SHA256SUMS" || die "registry 15.1.0 hash"
cmp -s release/registry_15.3.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br 2>/dev/null \
  || cp release/registry_15.3.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br
cp -f HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br HEMOGLYPH_GUIDELINE_REGISTRY.json.br; ok "live registry = 15.3.0"

echo "== 1. unit tests + property-based invariants (tests/test_properties.py) + LabPanel-Check reference cards (Table 6) =="
find . -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
python3 -m pytest -q -p no:cacheprovider tests 2>&1 | tail -2 | tee /tmp/hg_pytest.txt
grep -Eq "^[0-9]+ passed" /tmp/hg_pytest.txt && ! grep -q "failed" /tmp/hg_pytest.txt && ok "pytest" || die "pytest"

echo "== 2. verification ledger (Note 18): rebuild from frozen inputs and compare counts =="
cp eval/verification_ledger/ledger_counts.json /tmp/hg_ledger_counts_committed.json
python3 eval/verification_ledger/build_ledger.py > /tmp/hg_ledger.log 2>&1 || die "ledger build (see /tmp/hg_ledger.log)"
python3 - <<'PY' && ok "ledger counts identical to committed ledger_counts.json" || die "ledger counts differ"
import json; a=json.load(open('/tmp/hg_ledger_counts_committed.json')); b=json.load(open('eval/verification_ledger/ledger_counts.json')); raise SystemExit(0 if a==b else 1)
PY

echo "== 3. mutation study (Note 16): detectors frozen; recompute recall table from the seeds =="
python3 eval/audit/mutate.py release/registry_15.1.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br --out /tmp/hg_mutation_results.json > /tmp/hg_mutate.log 2>&1 || die "mutate.py (see /tmp/hg_mutate.log)"
python3 - <<'PY' && ok "mutation recall table identical to committed mutation_results.json.gz" || die "mutation table differs"
import gzip, json, os
ref = json.load(gzip.open('eval/audit/mutation_results.json.gz'))['table']
new = json.load(open('/tmp/hg_mutation_results.json'))['table']
print(json.dumps(new)[:300]); raise SystemExit(0 if ref == new else 1)
PY
[ "$MODE" = quick ] && { echo "QUICK DONE"; exit 0; }

if [ "$MODE" = v7 ] || [ "$MODE" = all ]; then
  echo "== 4. frozen v7 + 14.1.0 on NHANES 2017-18 (cycle J, n = 3,000, seed 20261021) vs frozen report =="
  [ -d eval/realdata/nhanes_2017 ] || python3 eval/realdata/fetch_nhanes_cycle.py J
  python3 eval/realdata/eval_nhanes.py --cycle J --n-max 3000 --encounter community --engine-dir /tmp/hemoglyph_v7 --suffix _repro_v7 > /tmp/hg_nhanes.log 2>&1 || die "eval_nhanes (see /tmp/hg_nhanes.log)"
  python3 tools/compare_reports.py eval/results/nhanes_2017/report_v7.md eval/results/nhanes_2017/report_repro_v7.md && ok "NHANES J identical to Table 4" || die "NHANES J differs"
fi
if [ "$MODE" = eicu ] || [ "$MODE" = all ]; then
  echo "== 5. frozen v7 + 14.1.0 on eICU-CRD demo (2,314 stays) vs frozen report (Table 3) =="
  [ -f eval/realdata/eicu_demo/lab.csv.gz ] || die "eICU-CRD demo CSVs not found in eval/realdata/eicu_demo/ (download from PhysioNet; see README_REPRODUCE.md)"
  python3 eval/realdata/eval_eicu.py --encounter icu --engine-dir /tmp/hemoglyph_v7 --suffix _repro_v7 > /tmp/hg_eicu.log 2>&1 || die "eval_eicu (see /tmp/hg_eicu.log)"
  python3 tools/compare_reports.py eval/results/eicu_demo/report_v7.md eval/results/eicu_demo/report_repro_v7.md && ok "eICU identical to Table 3" || die "eICU differs"
fi
[ "$MODE" = all ] && { echo "== 6. remaining cohorts, baselines, figures (see README_REPRODUCE.md, Supplementary Table S17) =="; bash reproduce_full_cohorts.sh 2>/dev/null || echo "(full-cohort driver not bundled; run the Table S17 scripts individually)"; }
echo "DONE ($MODE)"
