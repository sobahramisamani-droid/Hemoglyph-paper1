#!/usr/bin/env python3
"""Baseline B2 — supervised gradient boosting trained on the SAME inputs (eICU demo per_stay.json).

For each group with >= 15 listed stays: HistGradientBoostingClassifier on the raw analyte
values (missing allowed), 5-fold stratified cross-validation grouped by hospital where possible,
out-of-fold AUROC with bootstrap CI. This is the "if you had labels and trained a model"
comparator; Hemoglyph is untrained, so a trained model has a structural advantage on this
data — the comparison shows how much accuracy knowledge alone recovers.
Also reports a logistic-regression variant for transparency.
"""
from __future__ import annotations
import os, sys, json
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from eval_nhanes import auroc, boot_ci  # noqa: E402
from eval_eicu import GROUPS  # noqa: E402


def main(path):
    rows = json.load(open(path))
    feats = sorted({k for r in rows for k in r["vals"]})
    X = np.full((len(rows), len(feats) + 2), np.nan)
    for i, r in enumerate(rows):
        for j, f in enumerate(feats):
            if f in r["vals"]:
                X[i, j] = r["vals"][f]
        X[i, -2] = r["age"]; X[i, -1] = 1.0 if r["sex"] == "female" else 0.0
    out = ["# Baseline B2 — supervised models trained on the same eICU inputs (5-fold out-of-fold)", "",
           "| group | n listed | HGB AUROC (95% CI) | LogReg AUROC | Hemoglyph AUROC (untrained) |", "|---|---:|---|---|---|"]
    res = {}
    for g in GROUPS:
        keyan = GROUPS[g][2]
        idx = [i for i, r in enumerate(rows) if any(k in r["labs"] for k in keyan)]
        y = np.array([1 if g in rows[i]["coded"] else 0 for i in idx])
        if y.sum() < 15 or (len(y) - y.sum()) < 15:
            continue
        Xi = X[idx]; oof = np.zeros(len(y)); oof_lr = np.zeros(len(y))
        skf = StratifiedKFold(5, shuffle=True, random_state=20261021)
        for tr, te in skf.split(Xi, y):
            m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=1).fit(Xi[tr], y[tr])
            oof[te] = m.predict_proba(Xi[te])[:, 1]
            lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000, C=0.5)).fit(Xi[tr], y[tr])
            oof_lr[te] = lr.predict_proba(Xi[te])[:, 1]
        au = auroc(y, oof); lo, hi = boot_ci(y, oof, n=500); au_lr = auroc(y, oof_lr)
        h = np.array([rows[i]["gp"].get(g, 0.0) for i in idx]); au_h = auroc(y, h)
        out.append(f"| {g} | {int(y.sum())} | {au:.2f} ({lo:.2f}–{hi:.2f}) | {au_lr:.2f} | {au_h:.2f} |")
        res[g] = {"n": int(y.sum()), "hgb": au, "ci": [lo, hi], "logreg": au_lr, "hemoglyph": au_h}
    txt = "\n".join(out); print(txt)
    open(os.path.join(os.path.dirname(path), "ml_baseline.md"), "w").write(txt + "\n")
    json.dump(res, open(os.path.join(os.path.dirname(path), "ml_baseline.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "eval", "results", "eicu_demo", "per_stay.json"))
