#!/usr/bin/env python3
"""Isotonic recalibration (split-half, cross-fitted), reliability diagrams, ECE and decision-curve analysis
on a multi-label per-stay file (eICU demo).

python3 eval/calibration_dca.py --per-stay eval/results/run_20261023_v5/eicu_per_stay_v5_1.json --label v5.1 \
       --out eval/results/eicu_demo/calibration_dca_v5_1.md --fig docs/paper1/figures/fig7_reliability_dca.png

Method (pre-specified 2026-10-23):
  * unit = (stay, group) pair where the group's key analyte was measured; y = group in coded labels;
    p = engine group probability (0 if the group was not in the differential).
  * pooled over all groups AND per group for the 5 largest groups.
  * isotonic regression fitted on odd-indexed stays, applied to even-indexed stays and vice versa (cross-fitted,
    so every reported calibrated probability is out-of-sample).  ECE with 10 equal-mass bins; Brier score.
  * decision curve: net benefit NB(t) = TP/N - FP/N * t/(1-t) for thresholds 0.05..0.80, for raw p, calibrated p,
    'treat all' and 'treat none'; computed per group (5 largest) on the cross-fitted calibrated probabilities.
"""
from __future__ import annotations
import argparse, json, os, sys, math, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from eval_eicu import GROUPS  # noqa: E402
from sklearn.isotonic import IsotonicRegression

ap = argparse.ArgumentParser()
ap.add_argument("--per-stay", required=True); ap.add_argument("--label", default="v5.1")
ap.add_argument("--out", required=True); ap.add_argument("--fig", default=None)
ap.add_argument("--groups", default="renal_impairment,sepsis,diabetes,acute_kidney_injury,anemia")
a = ap.parse_args()
import gzip
rows = json.load(gzip.open(a.per_stay, 'rt') if a.per_stay.endswith('.gz') else open(a.per_stay))
units = []
for i, r in enumerate(rows):
    for g, (_, ids, keys, _) in GROUPS.items():
        if not any(k in r["labs"] for k in keys): continue
        units.append((i, g, float(r["gp"].get(g, 0.0)), int(g in r["coded"])))
U = np.array([(u[0], u[2], u[3]) for u in units], dtype=float); G = np.array([u[1] for u in units])

def ece(p, y, bins=10):
    order = np.argsort(p); p, y = p[order], y[order]; n = len(p); e = 0.0; tab = []
    for b in range(bins):
        sl = slice(b * n // bins, (b + 1) * n // bins)
        if sl.stop <= sl.start: continue
        pm, ym = p[sl].mean(), y[sl].mean(); e += abs(pm - ym) * (sl.stop - sl.start) / n; tab.append((pm, ym, sl.stop - sl.start))
    return e, tab

def crossfit(p, y, idx):
    """isotonic fitted on odd stays -> applied to even, and vice versa"""
    odd = (idx % 2 == 1); q = np.zeros_like(p)
    for fit_mask, app_mask in ((odd, ~odd), (~odd, odd)):
        if fit_mask.sum() < 20 or y[fit_mask].sum() < 3:
            q[app_mask] = p[app_mask]; continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(p[fit_mask], y[fit_mask])
        q[app_mask] = iso.predict(p[app_mask])
    return q

def nb_curve(p, y, ts):
    N = len(y); out = []
    for t in ts:
        pred = p >= t; tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum())
        out.append(tp / N - fp / N * t / (1 - t))
    return np.array(out)

ts = np.arange(0.05, 0.81, 0.05)
L = [f"# Calibration (cross-fitted isotonic) and decision-curve analysis — eICU demo, engine {a.label}", "",
     f"stays {len(rows)}; (stay, group) units {len(units)}; positives {int(U[:,2].sum())}", "",
     "| set | n | prev | ECE raw | ECE isotonic (cross-fit) | Brier raw | Brier iso | AUROC |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
from eval_nhanes import auroc  # noqa: E402
figs = []
def block(name, mask):
    p, y, idx = U[mask, 1], U[mask, 2].astype(int), U[mask, 0].astype(int)
    q = crossfit(p, y, idx)
    e0, t0 = ece(p, y); e1, t1 = ece(q, y)
    L.append(f"| {name} | {len(p)} | {y.mean():.3f} | {e0:.3f} | {e1:.3f} | {np.mean((p-y)**2):.3f} | {np.mean((q-y)**2):.3f} | {auroc(y, p):.3f} |")
    figs.append((name, t0, t1, p, q, y))
    return p, q, y
block("ALL groups pooled", np.ones(len(U), bool))
big = [g for g in a.groups.split(",") if g in GROUPS]
per = {}
for g in big:
    per[g] = block(g, G == g)
L += ["", "Reliability (pooled): equal-mass deciles — mean predicted vs observed", "", "| decile | raw p | obs | iso p | obs |", "|---:|---:|---:|---:|---:|"]
_, t0, t1, *_ = figs[0]
for k in range(min(len(t0), len(t1))):
    L.append(f"| {k+1} | {t0[k][0]:.2f} | {t0[k][1]:.2f} | {t1[k][0]:.2f} | {t1[k][1]:.2f} |")
L += ["", "## Decision curves (net benefit per 100 units; cross-fitted isotonic probabilities vs raw vs treat-all)", ""]
for g in big:
    p, q, y = per[g]
    nb_raw = nb_curve(p, y, ts); nb_iso = nb_curve(q, y, ts); prev = y.mean(); nb_all = prev - (1 - prev) * ts / (1 - ts)
    L += [f"### {g} (n={len(y)}, prevalence {prev:.2f})", "", "| threshold | NB raw | NB isotonic | NB treat-all | NB treat-none |", "|---:|---:|---:|---:|---:|"]
    for t, r1, r2, r3 in zip(ts, nb_raw, nb_iso, nb_all):
        if round(t * 100) % 10 == 0 or abs(t - 0.05) < 1e-9 or abs(t - 0.15) < 1e-9 or abs(t - 0.25) < 1e-9:
            L.append(f"| {t:.2f} | {100*r1:.1f} | {100*r2:.1f} | {100*r3:.1f} | 0.0 |")
    useful = [f"{t:.2f}" for t, r2, r3 in zip(ts, nb_iso, nb_all) if r2 > max(r3, 0) + 1e-9]
    L += ["", f"isotonic model beats both default strategies at thresholds: {', '.join(useful) if useful else 'none'}", ""]
L += ["Interpretation: raw engine probabilities are over-confident on the multi-label task (ECE raw) — the figure shown in the paper is the",
      "cross-fitted isotonic mapping, which is what a deployment would apply; the decision curves show the threshold ranges where",
      "acting on the engine's calibrated probability has higher net benefit than treating everyone or no one.  No label information",
      "leaks into any reported probability (odd/even stay cross-fitting)."]
os.makedirs(os.path.dirname(a.out), exist_ok=True); open(a.out, "w").write("\n".join(L) + "\n"); print("\n".join(L[:12]))
if a.fig:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for ax, (name, t0, t1, p, q, y) in zip(axes[0], figs[:3]):
        ax.plot([0, 1], [0, 1], "k--", lw=0.8)
        ax.plot([x[0] for x in t0], [x[1] for x in t0], "o-", color="#c0392b", label="raw")
        ax.plot([x[0] for x in t1], [x[1] for x in t1], "s-", color="#1f77b4", label="isotonic (cross-fit)")
        ax.set_title(name); ax.set_xlabel("mean predicted"); ax.set_ylabel("observed"); ax.legend(fontsize=8)
    for ax, g in zip(axes[1], big[:3]):
        p, q, y = per[g]; prev = y.mean()
        ax.plot(ts, 100 * nb_curve(q, y, ts), color="#1f77b4", label="Hemoglyph (isotonic)")
        ax.plot(ts, 100 * nb_curve(p, y, ts), color="#c0392b", ls=":", label="Hemoglyph (raw)")
        ax.plot(ts, 100 * (prev - (1 - prev) * ts / (1 - ts)), color="grey", label="treat all"); ax.axhline(0, color="k", lw=0.8, label="treat none")
        ax.set_ylim(-5, 100 * prev + 5); ax.set_title(f"decision curve — {g}"); ax.set_xlabel("threshold probability"); ax.set_ylabel("net benefit / 100"); ax.legend(fontsize=7)
    fig.suptitle(f"Hemoglyph {a.label} — eICU demo held-out: reliability (top) and decision curves (bottom)")
    fig.tight_layout(); os.makedirs(os.path.dirname(a.fig), exist_ok=True); fig.savefig(a.fig, dpi=160); print("figure", a.fig)
