#!/usr/bin/env python3
"""Hybrid arm (declared post-freeze experiment, 2026-10-27): does a trained layer on top of the frozen engine
raise group-level recall@k on eICU-CRD demo, and where?

Three rankers on the SAME 2,314 stays, SAME 31 label groups, SAME scoring:
  engine  : groups sorted by the frozen v7 group probability (gp; 0 when the group is absent)
  ml      : groups sorted by 5-fold out-of-fold HistGradientBoosting probability (same inputs: raw analytes, age, sex)
  hybrid  : groups sorted by max(engine, ml) — no weight, no threshold, nothing fitted to the test fold
  hybrid6 : engine everywhere except the six groups without a single-analyte criterion
            (diabetes, sepsis, cirrhosis, malnutrition, GI bleeding, alcohol withdrawal), where max(engine, ml) is used

Metric: group-level recall@k over labels whose key analyte is measured (the same 2,432 scorable labels as Table 3).
Group-level engine recall is NOT the flat entity-level figure in the paper (one group can occupy several entity slots);
all four rankers are compared on this one metric only. Nothing here changes any frozen number.
Output: eval/results/eicu_demo/hybrid_arm_v7.md (small).
"""
from __future__ import annotations
import os, sys, json, gzip, ast
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from eval_eicu import GROUPS  # noqa: E402

P = lambda x: ast.literal_eval(x) if isinstance(x, str) else x
rows = json.load(gzip.open(os.path.join(ROOT, "eval/results/eicu_demo/per_stay_v7.json.gz")))
for r in rows:
    for k in ("vals", "labs", "coded", "gp"):
        r[k] = P(r[k])
    r["age"] = float(r["age"])

feats = sorted({k for r in rows for k in r["vals"]})
X = np.full((len(rows), len(feats) + 2), np.nan)
for i, r in enumerate(rows):
    for j, f in enumerate(feats):
        if f in r["vals"]:
            X[i, j] = r["vals"][f]
    X[i, -2] = r["age"]; X[i, -1] = 1.0 if r["sex"] == "female" else 0.0

groups = list(GROUPS)
ml = np.zeros((len(rows), len(groups)))
eng = np.zeros((len(rows), len(groups)))
scorable = np.zeros((len(rows), len(groups)), bool)
y = np.zeros((len(rows), len(groups)), int)
for gi, g in enumerate(groups):
    keyan = GROUPS[g][2]
    idx = np.array([i for i, r in enumerate(rows) if any(k in r["labs"] for k in keyan)])
    yy = np.array([1 if g in rows[i]["coded"] else 0 for i in idx])
    y[idx, gi] = yy; scorable[idx, gi] = True
    eng[:, gi] = [r["gp"].get(g, 0.0) for r in rows]
    if yy.sum() < 15 or (len(yy) - yy.sum()) < 15:
        continue
    oof = np.zeros(len(yy))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=20261021).split(X[idx], yy):
        m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=1)
        m.fit(X[idx][tr], yy[tr]); oof[te] = m.predict_proba(X[idx][te])[:, 1]
    ml[idx, gi] = oof

six = [groups.index(g) for g in groups if GROUPS[g][3] != "yes"]
hyb = np.maximum(eng, ml)
hyb6 = eng.copy(); hyb6[:, six] = hyb[:, six]


def recall_at(score, k):
    hit = tot = 0
    per = {}
    for i in range(len(rows)):
        order = np.argsort(-score[i])[:k]
        top = set(order.tolist())
        for gi in np.where(scorable[i] & (y[i] == 1))[0]:
            tot += 1; h = int(gi in top); hit += h
            a = per.setdefault(groups[gi], [0, 0]); a[0] += h; a[1] += 1
    return hit / tot, tot, per


def recall_idx(score, k, s):
    hit = tot = 0
    for i in s:
        top = set(np.argsort(-score[i])[:k].tolist())
        for gi in np.where(scorable[i] & (y[i] == 1))[0]:
            tot += 1; hit += int(gi in top)
    return hit / tot


def boot(a, b, k, n=1000, seed=7):
    rng = np.random.default_rng(seed); N = len(rows); d = []
    for _ in range(n):
        s = rng.integers(0, N, N); d.append(recall_idx(b, k, s) - recall_idx(a, k, s))
    return np.percentile(d, [2.5, 97.5])


out = ["# Hybrid arm — frozen engine v7 + out-of-fold supervised layer (eICU-CRD demo, 2,314 stays, group-level recall)", "",
       "Declared post-freeze experiment (2026-10-27). Group-level metric; not comparable to the flat entity-level Table 3. "
       "`hybrid` = max(engine, ML) for all groups; `hybrid6` = engine except the six groups without a single-analyte criterion. "
       "No weight or threshold was fitted; ML probabilities are 5-fold out-of-fold.", "",
       "| ranker | recall@3 | recall@5 | recall@10 | Δ@5 vs engine (95% bootstrap CI) |", "|---|---:|---:|---:|---|"]
R = {}
for name, sc in [("engine (group-level)", eng), ("ML only", ml), ("hybrid (all groups)", hyb), ("hybrid6 (six outcome groups)", hyb6)]:
    r3, _, _ = recall_at(sc, 3); r5, tot, per = recall_at(sc, 5); r10, _, _ = recall_at(sc, 10)
    R[name] = per
    ci = "—" if sc is eng else "%+.1f (%+.1f to %+.1f)" % ((r5 - recall_at(eng, 5)[0]) * 100, *(boot(eng, sc, 5) * 100))
    out.append(f"| {name} | {r3*100:.1f} | {r5*100:.1f} | {r10*100:.1f} | {ci} |")
out += ["", f"Scorable labels: {tot}.", "", "## Per-group recall@5 (hits/labels)", "", "| group | n | engine | ML | hybrid | hybrid6 |", "|---|---:|---:|---:|---:|---:|"]
for g in groups:
    if g not in R["engine (group-level)"]:
        continue
    n = R["engine (group-level)"][g][1]
    cells = [f"{R[k][g][0]/n*100:.0f}%" for k in R]
    out.append(f"| {g} | {n} | " + " | ".join(cells) + " |")
txt = "\n".join(out)
print(txt)
open(os.path.join(ROOT, "eval/results/eicu_demo/hybrid_arm_v7.md"), "w").write(txt + "\n")
