"""Compare two gate runs (eICU + NHANES summaries) by suffix. Usage: gate_compare.py _r1510 _r1520"""
import json, sys, os
HG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
a, b = sys.argv[1], sys.argv[2]
ea = json.load(open(f"{HG}/eval/results/eicu_demo/summary{a}_icu.json")); eb = json.load(open(f"{HG}/eval/results/eicu_demo/summary{b}_icu.json"))
rows = []
for key in ("recall", "recall_two_tier", "recall_grouped"):
    for k in ea[key]:
        na, da = ea[key][k]; nb, db = eb[key][k]
        rows.append((f"eICU {key}@{k}", na, nb, 100 * nb / db - 100 * na / da))
rows.append(("eICU support", ea["support"][0], eb["support"][0], 0))
import statistics
ma = statistics.mean(g["auroc"] for g in ea["groups"].values()); mb = statistics.mean(g["auroc"] for g in eb["groups"].values())
print(f"{'metric':28s} {a:>8s} {b:>8s}  delta_pts")
for m, x, y, d in rows: print(f"{m:28s} {x:8d} {y:8d}  {d:+.2f}")
print(f"{'eICU mean AUROC':28s} {ma:8.3f} {mb:8.3f}  {mb-ma:+.4f}")
na_ = json.load(open(f"{HG}/eval/results/nhanes_2017/summary{a}.json")); nb_ = json.load(open(f"{HG}/eval/results/nhanes_2017/summary{b}.json"))
for t in na_:
    if isinstance(na_[t], dict) and "auroc" in na_[t]:
        print(f"{'NHANES '+t:28s} {na_[t]['auroc']:8.3f} {nb_[t]['auroc']:8.3f}  {nb_[t]['auroc']-na_[t]['auroc']:+.4f}")
    else: print("NHANES", t, na_[t], nb_[t])
