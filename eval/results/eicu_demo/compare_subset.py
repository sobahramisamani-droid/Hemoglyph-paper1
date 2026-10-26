#!/usr/bin/env python3
"""Compare two eICU per-stay files on the stays common to both (flat gr, two-tier gr2, grouped gr3) over coded groups."""
import gzip, json, sys, ast
def load(p):
    o = gzip.open(p) if p.endswith(".gz") else open(p)
    d = json.load(o); return {str(r["stay"]): r for r in d}
def rec(rows, key, k):
    hit = n = 0
    for r in rows:
        coded = r["coded"]; coded = ast.literal_eval(coded) if isinstance(coded, str) else coded
        gr = r[key]; gr = ast.literal_eval(gr) if isinstance(gr, str) else gr
        for g in coded:
            n += 1; hit += int(gr.get(g, 999) <= k)
    return hit, n
A, B = load(sys.argv[1]), load(sys.argv[2]); common = sorted(set(A) & set(B))
print("common stays", len(common))
for key, name in (("gr", "flat"), ("gr2", "two-tier"), ("gr3", "grouped")):
    for k in (1, 3, 5, 10):
        ha, n = rec([A[s] for s in common], key, k); hb, _ = rec([B[s] for s in common], key, k)
        print(f"{name:9s}@{k:<2d} A {100*ha/n:5.1f}  B {100*hb/n:5.1f}  (n={n})")
