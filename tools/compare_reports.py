"""Compare the headline numbers of two Hemoglyph report.md files (eICU or NHANES) and exit 1 on any difference.
    python3 tools/compare_reports.py eval/results/eicu_demo/report_v7.md eval/results/eicu_demo/report_repro_v7.md
"""
import re, sys
def headline(path):
    out = {}; sec = ""
    for l in open(path, encoding="utf-8"):
        if l.startswith("## "): sec = l[3:].split("(")[0].strip()[:40]
        m = re.match(r"\| (top-\d+) \| \*?\*?([\d.]+)%", l)
        if m: out[f"{sec} {m.group(1)}"] = m.group(2)
        m = re.match(r"\| (\w+) \| [^|]+ \| [^|]+ \| \*\*([\d.]+)\*\*", l)
        if m: out[f"AUROC {m.group(1)}"] = m.group(2)
    return out
a, b = headline(sys.argv[1]), headline(sys.argv[2]); bad = 0
for k in sorted(set(a) | set(b)):
    same = a.get(k) == b.get(k); bad += not same
    print(("OK   " if same else "DIFF ") + f"{k}: {a.get(k)} vs {b.get(k)}")
print("compare:", "IDENTICAL" if not bad else f"{bad} DIFFERENCES"); sys.exit(1 if bad else 0)
