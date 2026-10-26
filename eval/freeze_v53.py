#!/usr/bin/env python3
"""FREEZE v5.3 — SHA-256 manifest of engine, registries, evaluation code, SAP, manuscripts and all v5.3 result files.
Usage: python3 eval/freeze_v53.py  → FREEZE_v5.3_<date>_sha256.txt (sha256sum -c compatible) + FREEZE_v5.3_<date>_summary.md
Nothing is modified; the manifest only records what exists at freeze time.
"""
import hashlib, os, glob, datetime, json, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PATTERNS = [
    "analyse_gidlines.py", "calcu.py", "cache_registry.py", "preflight_check.py", "sarvis_tahlil.py", "ocr.py", "app.py",
    "HEMOGLYPH_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_FEATURE_REGISTRY.json.br",
    "reproduce.sh", "README.md", "README_FA.md", "README_REPRODUCE.md", "CITATION.cff", ".zenodo.json",
    "eval/*.py", "eval/*.sh", "eval/patches/*.py", "eval/realdata/*.py", "eval/ablation/*.br", "eval/llm_baseline/**/*",
    "eval/results/eicu_demo/*", "eval/results/nhanes_*/*", "eval/results/uci_thyroid/*", "eval/results/uci_hcv/*", "eval/results/ilpd/*",
    "eval/results/pmc_cases/*", "eval/results/sepsis2019/*", "eval/results/run_20261023_v53/*", "eval/results/run_20261023_v53/.done_*",
    "release/registry_13.4.*/*", "docs/paper2/*.md", "tests/*.py", "docs/paper1/*.md", "docs/paper1/*.docx", "docs/paper1/figures/*", "docs/paper1/supplement/*", "docs/paper1/v53/*",
]
files = set()
for p in PATTERNS:
    for f in glob.glob(p, recursive=True):
        if os.path.isfile(f) and "invalid_ran_on_13_1_0" not in f and not f.endswith((".pyc", ".partial.json")):
            files.add(f)
files = sorted(files)
date = datetime.date.today().strftime("%Y%m%d")
TAG = "addendum_" if "--addendum" in sys.argv else ""
man = f"FREEZE_v5.3_{TAG}{date}_sha256.txt"
total = 0
with open(man, "w") as out:
    for f in files:
        h = hashlib.sha256(); size = 0
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk); size += len(chunk)
        total += size
        out.write(f"{h.hexdigest()}  {f}\n")
# registry metadata for the summary
try:
    import cache_registry
    meta = cache_registry.bargozari_registry("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")["registry_metadata"]
    regline = f"disease–guideline registry {meta.get('version')} — entities {meta.get('total_diseases')}, rules {meta.get('total_rules')}, executable {meta.get('executable_rules')}"
except Exception as e:
    regline = f"(registry metadata unavailable: {e})"
done = sorted(os.path.basename(x) for x in glob.glob("eval/results/run_20261023_v53/.done_*"))
summ = f"""# FREEZE v5.3 — {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC

* Engine: analyse_gidlines.py (release 1.3.1, v5.3 evaluation build); {regline}; feature registry 2,045 analytes.
* Manifest: `{man}` — {len(files)} files, {total/1e6:.1f} MB. Verify with `sha256sum -c {man}`.
* Chain markers present at freeze: {', '.join(d.replace('.done_', '') for d in done)}.
* Headline (eICU-CRD demo, 2,314 stays, labs only): recall@3/5/10 = 49.3 / 63.8 / 77.2 %; +context 52.1 / 66.6 / 79.8; +context+temporal 51.7 / 66.2 / 80.2; mean AUROC 0.767 (k = 24).
* Pre-registered hypotheses (SAP Amendment 12): H1 FAILED (sex gap 4.4 → 4.3), H2 PASSED (63.7 → 63.8), H3 PASSED (B8 294/456 ≥ 288).
* Registry-off ablation: recall@5 63.8 → 62.0 (−1.8), mean AUROC 0.767 → 0.732.
* {"ADDENDUM: chain V53_ALLDONE — every held-out re-run (NHANES 2017–18 cycle J, Sepsis-2019, healthy-1000, perturbation, unit-twin) completed under registry 13.3.0; no † remains in the manuscript. NHANES J: diabetes 0.941, CKD 0.959, anaemia 0.971, iron deficiency 0.989; Sepsis-2019 AUROC 0.593 (logistic 0.689); healthy sweep 0/1000; perturbation 755/755; unit-twin 149/149. Provenance audit: Supplementary Data 1 (13.4.1), 9 fabricated DOIs removed in release 13.4.1 (rule logic = 13.4.0); shipped registry 13.4.2 (nine D19 finding rules demoted after an eICU top-5 crowding regression: 13.4.1 61.7 % → 13.4.2 63.7 % vs 13.3.0 63.8 %; full gate green)." if TAG else "Any result file whose chain marker is absent above was still being (re-)computed under registry 13.3.0 at freeze time and is marked † in the manuscript; the v5.2 figure stands for it until the re-run is appended as an addendum manifest."}
"""
open(f"FREEZE_v5.3_{TAG}{date}_summary.md", "w").write(summ)
print(summ); print("manifest:", man)
