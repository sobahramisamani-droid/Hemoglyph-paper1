#!/usr/bin/env python3
"""FREEZE v15 — SHA-256 manifest of engine v7, registry 14.1.0, evaluation code, SAP (Amendment 15 + development log),
tests, patches and every development-phase result file. Written ONCE, BEFORE any quarantined file is read.
Usage: python3 eval/freeze_v15.py  → FREEZE_v15_<date>_sha256.txt + FREEZE_v15_<date>_summary.md  (nothing is modified).
"""
import hashlib, os, glob, datetime, json, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT); sys.path.insert(0, ROOT)
PATTERNS = [
    "analyse_gidlines.py", "calcu.py", "cache_registry.py", "preflight_check.py", "app.py", "ocr.py",
    "HEMOGLYPH_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_FEATURE_REGISTRY.json.br",
    "eval/*.py", "eval/*.sh", "eval/patches/registry_v14_*.py", "eval/realdata/*.py", "eval/mimic/*.py", "eval/probes/*.py",
    "eval/results/eicu_demo/*", "eval/results/nhanes_2017/*", "eval/results/sepsis2019/*",
    "eval/results/gate_14_0_0/*", "eval/results/gate_14_1_0/*", "eval/results/gate_v7/*", "eval/results/validation_v14/*", "eval/engine_13_4_2_ref/*",
    "release/registry_14.*/*", "tests/*.py", "docs/paper1/supplement/SAP_Hemoglyph_v1.md", "eval/quarantine/README.md",
]
files = set()
for p in PATTERNS:
    for f in glob.glob(p, recursive=True):
        if os.path.isfile(f) and not f.endswith((".pyc", ".partial.json")):
            files.add(f)
files = sorted(files); date = datetime.date.today().strftime("%Y%m%d")
man = f"FREEZE_v15_{date}_sha256.txt"; total = 0
with open(man, "w") as out:
    for f in files:
        h = hashlib.sha256(); size = 0
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk); size += len(chunk)
        total += size; out.write(f"{h.hexdigest()}  {f}\n")
import cache_registry
meta = cache_registry.bargozari_registry("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")["registry_metadata"]
def rec(tag):
    try:
        s = json.load(open(f"eval/results/eicu_demo/summary{tag}.json"))
        f = lambda k, n: round(100 * s[k][n][0] / s[k][n][1], 1)
        return f"flat {f('recall','3')}/{f('recall','5')}/{f('recall','10')}, two-tier@5 {f('recall_two_tier','5')}, grouped@5 {f('recall_grouped','5')}"
    except Exception as e:
        return f"(n/a: {e})"
summ = f"""# FREEZE v14 — {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC

* Registry: {meta.get('version')} — executable rules {meta.get('executable_rules')}, sources {meta.get('total_guideline_sources', meta.get('total_sources'))}; engine v6 (SAP Amendment 14, changes C1–C10).
* Manifest: `{man}` — {len(files)} files, {total/1e6:.1f} MB. Verify with `sha256sum -c {man}`.
* Development results at freeze (eICU-CRD demo, 2,314 stays, labs only): v14.1 {rec('_v1410')}; same-engine 13.4.2 control {rec('_v1342_v6engine_g')}; 14.0.0 {rec('_v1400')}.
* Quarantined data (`eval/quarantine/`: Sepsis-2019 set B, NHANES 2013–14 H, MIMIC-IV demo, post-freeze PMC cases) have NOT been read before this manifest was written.
* Pre-stated validation criteria (SAP Amendment 14, unchanged): MIMIC-IV demo top-5 ≥ 65 % / top-1 ≥ 45 %; set B arm B AUROC ≥ 0.65 and control flag ≤ 20 %; NHANES H AUROCs within 0.03 of J; new PMC top-5 ≥ 60 %; healthy 0/40; fuzz 0/1000.
* Development-set expectation recorded honestly before validation: set A arm B AUROC .592 → the set-B AUROC criterion is expected to FAIL; it will be reported as such.
"""
open(f"FREEZE_v15_{date}_summary.md", "w").write(summ); print(summ); print("manifest:", man)
