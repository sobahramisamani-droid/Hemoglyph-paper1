"""Compile the 2026-10-21 test run (registry 13.1.0 + ESL ext-3) into
Markdown + JSON + CSV for the paper.  Reads eval/results/run_20261021_final/*.txt."""
import re, os, json, csv, glob, datetime
D = os.path.join(os.path.dirname(__file__), "results", "run_20261021_final")
rows = []
def rd(n):
    p = os.path.join(D, n)
    return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
def add(suite, kind, passed, total, extra="", file=""):
    rows.append(dict(suite=suite, kind=kind, passed=passed, total=total, pct=round(100*passed/total, 2) if total else None, extra=extra, file=file))

for f, label in [("engine.txt", "Engine battery (ordinary panels)"), ("hard.txt", "Hard battery 1"), ("hard2.txt", "Hard battery 2"), ("hard3.txt", "Hard battery 3 (13.1.0 entities + negatives)"), ("adv.txt", "Adversarial battery")]:
    t = rd(f); m = re.search(r"SCORE (\d+)/(\d+)", t)
    if m:
        med = re.search(r"median (\d+) ms", t); p95 = re.search(r"p95 (\d+) ms", t)
        add(label, "accuracy", int(m[1]), int(m[2]), f"median {med[1]} ms" + (f", p95 {p95[1]} ms" if p95 else "") if med else "", f)
t = rd("pytest.txt"); m = re.search(r"(\d+) passed", t)
if m: add("pytest unit/regression suite", "unit", int(m[1]), int(m[1]) + int((re.search(r"(\d+) failed", t) or [0, 0])[1]), re.search(r"in ([\d.]+s)", t)[1] if re.search(r"in ([\d.]+s)", t) else "", "pytest.txt")
for f in sorted(glob.glob(os.path.join(D, "twin_*.txt"))):
    t = open(f, encoding="utf-8").read(); m = re.search(r"UNIT-TWIN SCORE (\d+)/(\d+).*?exercised: (\d+)", t)
    if m: add(f"Unit-twin invariance ({os.path.basename(f)[5:-4]})", "robustness", int(m[1]), int(m[2]), f"{m[3]} conversions", os.path.basename(f))
for f in sorted(glob.glob(os.path.join(D, "pert*_*.txt"))):
    t = open(f, encoding="utf-8").read(); m = re.search(r"PERTURBATION \((\d+)% noise, (\d+) reps\): replicates passed (\d+)/(\d+).*?robust cases (\d+)/(\d+)", t)
    if m: add(f"Perturbation ±{m[1]}% ({os.path.basename(f).split('_',1)[1][:-4]})", "robustness", int(m[3]), int(m[4]), f"fully robust cases {m[5]}/{m[6]}", os.path.basename(f))
hs_tot = hs_fp = 0
for f in sorted(glob.glob(os.path.join(D, "healthy_*.txt"))):
    t = open(f, encoding="utf-8").read(); m = re.search(r"HEALTHY SWEEP n=(\d+): syndrome false-fires=(\d+)\s+dx>=0.5=(\d+)\s+worst p=([\d.]+) \((\S+)", t)
    if m:
        n = int(m[1]); fp = max(int(m[2]), int(m[3])); hs_tot += n; hs_fp += fp
        add(f"Healthy sweep ({os.path.basename(f)[8:-4]})", "specificity", n - fp, n, f"syn={m[2]} dx>=0.5={m[3]} worst p={m[4]} ({m[5]})", os.path.basename(f))
if hs_tot: add("Healthy sweep (pooled)", "specificity", hs_tot - hs_fp, hs_tot, f"false-positive rate {100*hs_fp/hs_tot:.2f}%")

os.makedirs(D, exist_ok=True)
json.dump(dict(generated=datetime.datetime.now().isoformat(timespec="seconds"), registry="13.1.0-CLINICAL-CURATED", engine_file="analyse_gidlines.py", rows=rows), open(os.path.join(D, "summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
with open(os.path.join(D, "summary.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
md = ["# Hemoglyph test report — 2026-10-21 (registry 13.1.0, ESL extension 3)", "",
      "All cases are developer-authored synthetic panels derived from textbook/guideline criteria. "
      "This is **engineering verification, not clinical validation**; no patient data were used.", "",
      "| Suite | Type | Passed | Total | % | Notes |", "|---|---|---:|---:|---:|---|"]
for r in rows: md.append(f"| {r['suite']} | {r['kind']} | {r['passed']} | {r['total']} | {r['pct']} | {r['extra']} |")
acc = [r for r in rows if r["kind"] == "accuracy"]; tot = sum(r["total"] for r in acc); ok = sum(r["passed"] for r in acc)
md += ["", f"**Pooled synthetic case accuracy:** {ok}/{tot} = {100*ok/tot:.2f}%" if tot else "", ""]
open(os.path.join(D, "test_report_20261021.md"), "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
