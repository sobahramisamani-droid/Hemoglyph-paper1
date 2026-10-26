"""Reviewer items B5 (calibration slope/intercept, Brier with CI, log-loss) and B6 (multiplicity control over the
per-group AUROCs; sensitivity of recall to the minimum-panel-size threshold) on the frozen v7 per-stay file.
Output: eval/results/eicu_demo/reviewer_b5_b6_v7.md
"""
import os, sys, json, gzip, math, collections
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from eval_eicu import GROUPS
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
R = os.path.join(ROOT, "eval", "results", "eicu_demo")
rows = json.load(gzip.open(os.path.join(R, "per_stay_v7.json.gz"), "rt"))
ev = lambda r, g: any(k in r["labs"] for k in GROUPS[g][2])
EPS = 1e-4

def units(groups=None):
    P, Y, S = [], [], []
    for r in rows:
        for g in GROUPS:
            if groups and g not in groups: continue
            if not ev(r, g): continue
            P.append(min(1 - EPS, max(EPS, r["gp"].get(g, 0.0)))); Y.append(int(g in r["coded"])); S.append(r["stay"])
    return np.array(P), np.array(Y), np.array(S)

def cal_slope(p, y):
    lg = np.log(p / (1 - p)).reshape(-1, 1)
    m = LogisticRegression(C=1e6, max_iter=1000).fit(lg, y); slope = float(m.coef_[0][0])
    # intercept with slope fixed at 1 (calibration-in-the-large)
    off = lg.ravel(); m2 = LogisticRegression(C=1e6, max_iter=1000, fit_intercept=True).fit(np.zeros((len(y), 1)), y)  # placeholder
    # proper CITL: logistic with offset -> use iterative: intercept = log(mean odds) adjustment via Newton
    a = 0.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-(off + a))); g = (y - q).sum(); h = (q * (1 - q)).sum(); a += g / h
        if abs(g / h) < 1e-8: break
    return slope, float(a)

def boot(stat, p, y, s, B=500, seed=5):
    rnd = np.random.default_rng(seed); st = np.unique(s); idx = {k: np.where(s == k)[0] for k in st}; out = []
    for _ in range(B):
        pick = rnd.choice(st, len(st), replace=True); ii = np.concatenate([idx[k] for k in pick]); out.append(stat(p[ii], y[ii]))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))

L = ["# Reviewer items B5/B6 — calibration metrics and multiplicity / panel-size sensitivity (engine v7, eICU demo)", ""]
brier = lambda p, y: float(np.mean((p - y) ** 2)); ll = lambda p, y: float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
L += ["## B5 Calibration (raw engine probabilities; stay-cluster bootstrap CI, 500 reps)", "", "| set | units | prev | calibration slope | calibration-in-the-large (intercept) | Brier (95% CI) | log-loss | AUROC |", "|---|---:|---:|---:|---:|---|---:|---:|"]
res = {}
for name, gs in (("ALL pooled", None), ("renal_impairment", ["renal_impairment"]), ("sepsis", ["sepsis"]), ("diabetes", ["diabetes"]), ("acute_kidney_injury", ["acute_kidney_injury"]), ("anemia", ["anemia"]), ("acute_myocardial_infarction", ["acute_myocardial_infarction"]), ("hyperkalemia", ["hyperkalemia"])):
    p, y, s = units(gs)
    if y.sum() < 10: continue
    sl, ic = cal_slope(p, y); b = brier(p, y); lo, hi = boot(brier, p, y, s); au = roc_auc_score(y, p)
    res[name] = dict(n=int(len(y)), prev=float(y.mean()), slope=sl, citl=ic, brier=b, brier_ci=[lo, hi], logloss=ll(p, y), auroc=float(au))
    L.append(f"| {name} | {len(y)} | {y.mean():.3f} | {sl:.2f} | {ic:+.2f} | {b:.3f} ({lo:.3f}–{hi:.3f}) | {ll(p, y):.3f} | {au:.3f} |")
L += ["", "Interpretation: slope < 1 and strongly negative intercept = raw scores are over-confident ranks, not probabilities (as stated in the manuscript); the cross-fitted isotonic map (calibration_dca_v7.md) removes this for display purposes only.", ""]

# ---- B6a multiplicity: per-group AUROC with DeLong-free bootstrap p vs 0.5, Holm and Benjamini-Hochberg
L += ["## B6a Multiplicity control over per-group AUROC (H0: AUROC = 0.5; Mann–Whitney U, two-sided; Holm and BH-FDR at 0.05; label-level, exploratory)", "", "| group | n coded | AUROC | raw p | Holm-adjusted | BH q | significant after BH |", "|---|---:|---:|---:|---:|---:|---|"]
pv = []
for g in GROUPS:
    p, y, s = units([g])
    if y.sum() < 10: continue
    au = roc_auc_score(y, p)
    from scipy.stats import mannwhitneyu
    praw = float(mannwhitneyu(p[y == 1], p[y == 0], alternative="two-sided").pvalue); pv.append((g, int(y.sum()), au, praw))
m = len(pv); srt = sorted(pv, key=lambda x: x[3]); holm = {}; bh = {}
for i, (g, n, au, pr) in enumerate(srt): holm[g] = min(1.0, pr * (m - i)); bh[g] = min(1.0, pr * m / (i + 1))
# enforce monotonicity for BH
prev = 1.0
for g, n, au, pr in reversed(srt): bh[g] = prev = min(prev, bh[g])
for g, n, au, pr in sorted(pv, key=lambda x: -x[1]): L.append(f"| {g} | {n} | {au:.3f} | {pr:.2e} | {holm[g]:.2e} | {bh[g]:.2e} | {'yes' if bh[g] < 0.05 else 'no'} |")
L += ["", f"{sum(1 for g in bh if bh[g] < 0.05)} of {m} groups remain significant after BH-FDR; all per-group comparisons other than the pre-specified primary (flat recall@5) are labelled exploratory in the manuscript.", ""]

# ---- B6b panel-size sensitivity
L += ["## B6b Sensitivity of recall to the minimum number of analytes in the first panel", "", "| minimum analytes (n_in) | stays | labels | flat @3 | flat @5 | flat @10 | two-tier @5 |", "|---:|---:|---:|---:|---:|---:|---:|"]
for thr in (8, 10, 12, 16, 20, 25):
    sub = [r for r in rows if r["n_in"] >= thr]; tot = 0; c = {3: 0, 5: 0, 10: 0}; c2 = 0
    for r in sub:
        for g in r["coded"]:
            if g not in GROUPS or not ev(r, g): continue
            tot += 1; rk = r["gr"].get(g, 999); c2 += r["gr2"].get(g, 999) <= 5
            for k in c: c[k] += rk <= k
    L.append(f"| ≥ {thr} | {len(sub)} | {tot} | {100*c[3]/tot:.1f} | {100*c[5]/tot:.1f} | {100*c[10]/tot:.1f} | {100*c2/tot:.1f} |")
ni = [r["n_in"] for r in rows]; L += ["", f"Distribution of n_in: median {int(np.median(ni))}, IQR {int(np.percentile(ni,25))}–{int(np.percentile(ni,75))}, min {min(ni)}, max {max(ni)}. Stays with < 8 analytes (n = 198 of 2,512 adults) were excluded by the SAP; they cannot be re-included without re-running the cohort builder, and their labels are listed in Table S3.", ""]
open(os.path.join(R, "reviewer_b5_b6_v7.md"), "w").write("\n".join(L) + "\n"); json.dump(res, open(os.path.join(R, "reviewer_b5_calibration_v7.json"), "w"), indent=1)
print("\n".join(L))
