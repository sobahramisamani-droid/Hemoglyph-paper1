#!/usr/bin/env python3
"""Deep review 2026-10-23: (1) context-echo check of the ctx arm; (2) anatomy of the male/female gap (v5.1).
Writes eval/results/eicu_demo/deep_review_20261023.md"""
import json, collections, os
from collections import defaultdict
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(f"{R}/eval/results/run_20261023_v5/eicu_per_stay_v5_2_ctx.json"))
B = {r["stay"]: r for r in json.load(open(f"{R}/eval/results/run_20261023_v5/eicu_per_stay_v5_1.json"))}
L = ["# Deep review 2026-10-23 - context echo and sex gap", ""]

acc = defaultdict(lambda: [0, 0, 0]); ctxk = collections.Counter(); gg = defaultdict(lambda: [0, 0, 0])
for r in C:
    b = B.get(r["stay"])
    if not b: continue
    for a in r.get("ctx_applied", []): ctxk[json.dumps(a, ensure_ascii=False)[:90]] += 1
    for g in r["coded"]:
        key = "named_in_history" if g in r["in_hist"] else "not_named"
        c5 = r["gr"].get(g, 99) <= 5; l5 = b["gr"].get(g, 99) <= 5
        acc[key][0] += 1; acc[key][1] += c5; acc[key][2] += l5
        gg[g][0] += 1; gg[g][1] += c5; gg[g][2] += l5
L += ["## 1. Context arm vs labs-only on the SAME labels, split by whether the label is already named in the history", "",
      "| labels | n | ctx recall@5 | labs-only recall@5 | delta |", "|---|---:|---|---|---|"]
for k, (n, c, l) in acc.items(): L.append(f"| {k} | {n} | {100*c/n:.1f}% | {100*l/n:.1f}% | {100*(c-l)/n:+.1f} |")
L += ["", "Most frequent context actions: " + "; ".join(f"{k} x{v}" for k, v in ctxk.most_common(5)), "",
      "Per-group delta (ctx - labs) sorted:", "", "| group | n | ctx@5 | labs@5 | delta |", "|---|---:|---|---|---|"]
for g, (n, c, l) in sorted(gg.items(), key=lambda x: -(x[1][1] - x[1][2])):
    if n >= 20: L.append(f"| {g} | {n} | {100*c/n:.0f}% | {100*l/n:.0f}% | {100*(c-l)/n:+.1f} |")

# ---------- 2. sex gap anatomy (v5.1)
sg = defaultdict(lambda: defaultdict(lambda: [0, 0])); tot = defaultdict(lambda: [0, 0])
for r in B.values():
    for g in r["coded"]:
        s = r["sex"]; sg[g][s][0] += 1; sg[g][s][1] += (r["gr"].get(g, 99) <= 5); tot[s][0] += 1; tot[s][1] += (r["gr"].get(g, 99) <= 5)
L += ["", "## 2. Sex gap (v5.1 labs-only)", "", "| sex | labels | recall@5 |", "|---|---:|---|"]
for s, (n, h) in tot.items(): L.append(f"| {s} | {n} | {100*h/n:.1f}% |")
# direct standardisation: apply male per-group recall to female label mix and vice versa
def std(target_sex, source_sex):
    n = h = 0
    for g, d in sg.items():
        nt = d[target_sex][0]; ns, hs = d[source_sex]
        if nt and ns: n += nt; h += nt * hs / ns
    return 100 * h / n if n else float("nan")
L += ["", f"Female label mix scored with MALE per-group recall: {std('female','male'):.1f}% (vs observed female {100*tot['female'][1]/tot['female'][0]:.1f}%)",
      f"Male label mix scored with FEMALE per-group recall: {std('male','female'):.1f}% (vs observed male {100*tot['male'][1]/tot['male'][0]:.1f}%)",
      "If the standardised numbers converge, the gap is case-mix (which diagnoses women carry); if they stay apart, it is within-group performance (reference intervals / thresholds).", "",
      "| group | female n | female@5 | male n | male@5 | gap (F-M) |", "|---|---:|---|---:|---|---|"]
rows = []
for g, d in sg.items():
    nf, hf = d["female"]; nm, hm = d["male"]
    if nf >= 15 and nm >= 15: rows.append((100 * hf / nf - 100 * hm / nm, g, nf, hf, nm, hm))
for gap, g, nf, hf, nm, hm in sorted(rows):
    L.append(f"| {g} | {nf} | {100*hf/nf:.0f}% | {nm} | {100*hm/nm:.0f}% | {gap:+.0f} |")
# label burden
lb = defaultdict(list)
for r in B.values(): lb[r["sex"]].append(len(r["coded"]))
L += ["", "Scorable labels per stay: " + ", ".join(f"{s} mean {sum(v)/len(v):.2f}" for s, v in lb.items())]
txt = "\n".join(L); print(txt)
open(f"{R}/eval/results/eicu_demo/deep_review_20261023.md", "w").write(txt + "\n")
