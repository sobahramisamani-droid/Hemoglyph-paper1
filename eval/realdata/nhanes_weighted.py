"""Reviewer response B3: survey-weighted re-analysis of the three NHANES cycles.
Re-uses the stored per-subject engine scores (no engine re-run) and the SAP reference standards of eval_nhanes.py,
and adds the MEC examination weight WTMEC2YR with the masked design variables SDMVSTRA / SDMVPSU
(fetched from the public DEMO files; eval/realdata/nhanes_weights_{H,I,J}.csv.gz).
  * weighted AUROC = weighted Mann-Whitney statistic (pairs weighted by w_i * w_j);
  * 95% CI by cluster bootstrap over PSU-within-stratum (1,000 replicates), i.e. the standard NHANES design unit;
  * weighted sensitivity/specificity at 0.5 and weighted false-assertion share among guideline-healthy adults.
The evaluated subjects are a seeded random subsample (n = 3,000) of eligible adults; weights are applied as relative
weights within that subsample, so estimates are design-weighted but not population totals.
Output: eval/results/nhanes_weighted_v7.md (+ .json)
"""
import os, sys, json, gzip, math, random, collections
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from eval_nhanes import egfr_ckdepi2021
CYC = {"J": ("eval/realdata/nhanes_2017", "eval/results/nhanes_2017/per_subject_v7.json.gz", "2017–18 (development; v7 re-run)"),
       "H": ("eval/quarantine/nhanes_2013_H", "eval/results/nhanes_2013/per_subject_v1410.json.gz", "2013–14 (quarantine 1; 14.1)"),
       "I": ("eval/realdata/nhanes_2015", "eval/results/nhanes_2015/per_subject_v7.json.gz", "2015–16 (quarantine 2; v7)")}
TASKS = ["diabetes", "diabetes_selfreport", "ckd", "ckd_selfreport", "anemia", "iron_deficiency", "hypercholesterolemia", "hyperuricemia", "alt_elevation"]

def rd(d, name, c):
    p = os.path.join(ROOT, d, f"{name}_{c}.csv.gz"); return pd.read_csv(p) if os.path.exists(p) else None

def build(c):
    d, ps, _ = CYC[c]
    df = rd(d, "DEMO", c)
    for f in ["BIOPRO", "CBC", "GHB", "GLU", "ALB_CR", "FERTIN", "TCHOL"]:
        t = rd(d, f, c)
        if t is not None: df = df.merge(t, on="SEQN", how="left")
    for f in ["DIQ", "KIQ_U"]:
        t = rd(d, f, c); df = df.merge(t, on="SEQN", how="left")
    for col in ["LBXGH", "LBXGLU", "URDACT", "LBXFER", "LBXTC", "LBXSUA", "LBXSATSI", "LBXHGB", "LBXSCR", "DIQ010", "KIQ022", "LBXSGL"]:
        if col not in df.columns: df[col] = np.nan
    w = pd.read_csv(os.path.join(ROOT, f"eval/realdata/nhanes_weights_{c}.csv.gz")); df = df.merge(w, on="SEQN", how="left")
    sub = json.load(gzip.open(os.path.join(ROOT, ps), "rt")) if ps.endswith(".gz") else json.load(open(os.path.join(ROOT, ps)))
    S = pd.DataFrame(sub); df = S.merge(df, on="SEQN", how="left")
    female = df.RIAGENDR == 2
    egfr = np.array([egfr_ckdepi2021(x, a, f) for x, a, f in zip(df.LBXSCR, df.RIDAGEYR, female)])
    ref = {"diabetes": ((df.LBXGH >= 6.5) | (df.LBXGLU >= 126) | (df.DIQ010 == 1)).astype(int), "diabetes_selfreport": (df.DIQ010 == 1).astype(int),
           "ckd": ((egfr < 60) | (df.URDACT >= 30)).astype(int), "ckd_selfreport": (df.KIQ022 == 1).astype(int),
           "anemia": np.where(female, df.LBXHGB < 12, df.LBXHGB < 13).astype(int), "iron_deficiency": (df.LBXFER < 15).astype(int),
           "hypercholesterolemia": (df.LBXTC >= 240).astype(int), "hyperuricemia": np.where(female, df.LBXSUA > 6.0, df.LBXSUA > 7.0).astype(int),
           "alt_elevation": np.where(female, df.LBXSATSI > 25, df.LBXSATSI > 33).astype(int)}
    avail = {"diabetes": df.LBXGH.notna(), "diabetes_selfreport": df.DIQ010.isin([1, 2]), "ckd": df.URDACT.notna(), "ckd_selfreport": df.KIQ022.isin([1, 2]),
             "anemia": df.LBXHGB.notna(), "iron_deficiency": df.LBXFER.notna(), "hypercholesterolemia": df.LBXTC.notna(), "hyperuricemia": df.LBXSUA.notna(), "alt_elevation": df.LBXSATSI.notna()}
    score_col = {"diabetes_selfreport": "diabetes", "ckd_selfreport": "ckd"}
    return df, ref, avail, score_col

def wauroc(y, s, w):
    y = np.asarray(y); s = np.asarray(s, float); w = np.asarray(w, float)
    pos = y == 1; neg = ~pos
    if pos.sum() == 0 or neg.sum() == 0: return float("nan")
    # weighted Mann-Whitney via sorting negatives
    sn, wn = s[neg], w[neg]; o = np.argsort(sn); sn, wn = sn[o], wn[o]; cw = np.concatenate([[0], np.cumsum(wn)])
    lo = np.searchsorted(sn, s[pos], "left"); hi = np.searchsorted(sn, s[pos], "right")
    num = (w[pos] * (cw[lo] + 0.5 * (cw[hi] - cw[lo]))).sum(); return float(num / (w[pos].sum() * wn.sum()))

def psu_boot(df, mask, y, s, B=1000, seed=11):
    """resample PSUs within strata with replacement; return 2.5/97.5 percentiles of weighted AUROC"""
    rnd = np.random.default_rng(seed); d = df[mask].copy(); d["_y"] = np.asarray(y)[mask]; d["_s"] = np.asarray(s)[mask]
    d["_cl"] = d.SDMVSTRA.astype(int).astype(str) + ":" + d.SDMVPSU.astype(int).astype(str)
    groups = {k: g for k, g in d.groupby("_cl")}; strata = collections.defaultdict(list)
    for k in groups: strata[k.split(":")[0]].append(k)
    out = []
    for _ in range(B):
        parts = []
        for st, cls in strata.items():
            pick = rnd.choice(cls, size=len(cls), replace=True); parts += [groups[k] for k in pick]
        b = pd.concat(parts); out.append(wauroc(b._y, b._s, b.WTMEC2YR))
    out = [x for x in out if not math.isnan(x)]; return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))

def main():
    res = {}; L = ["# Survey-weighted NHANES re-analysis (reviewer item B3) — WTMEC2YR weights, PSU-in-stratum bootstrap CI", "",
                   "Unweighted values are those reported in the manuscript (same subjects, same scores). Δ = weighted − unweighted AUROC.", "",
                   "| target | cycle | n (pos) | unweighted AUROC | weighted AUROC (95% PSU-bootstrap CI) | Δ | weighted sens / spec @0.5 |", "|---|---|---|---|---|---|---|"]
    for c in "JHI":
        df, ref, avail, sc = build(c); res[c] = {}
        assert df.WTMEC2YR.notna().all(), f"missing weights cycle {c}"
        for t in TASKS:
            col = sc.get(t, t)
            if col not in df.columns or df[col].isna().all(): continue
            m = avail[t].values & df[col].notna().values; y = np.asarray(ref[t]); s = df[col].fillna(0).values; w = df.WTMEC2YR.values
            if y[m].sum() == 0: continue
            au_u = wauroc(y[m], s[m], np.ones(m.sum())); au_w = wauroc(y[m], s[m], w[m]); lo, hi = psu_boot(df, m, y, s)
            pred = s[m] >= 0.5; ww = w[m]; yy = y[m]
            sens = (ww * (pred & (yy == 1))).sum() / (ww * (yy == 1)).sum(); spec = (ww * (~pred & (yy == 0))).sum() / (ww * (yy == 0)).sum()
            res[c][t] = dict(n=int(m.sum()), pos=int(yy.sum()), auroc_unweighted=au_u, auroc_weighted=au_w, ci=[lo, hi], sens_w=sens, spec_w=spec)
            L.append(f"| {t} | {c} {CYC[c][2].split(' ')[0]} | {int(m.sum())} ({int(yy.sum())}) | {au_u:.3f} | {au_w:.3f} ({lo:.3f}–{hi:.3f}) | {au_w-au_u:+.3f} | {100*sens:.1f} / {100*spec:.1f} |")
        # healthy false-assertion, weighted
        if "healthy" in df.columns:
            h = df.healthy.astype(bool).values; w = df.WTMEC2YR.values; fa = df.any50.astype(bool).values
            k = int((h & fa).sum()); n = int(h.sum()); wr = (w[h] * fa[h]).sum() / w[h].sum() if n else float("nan")
            res[c]["healthy"] = dict(n=n, false_assert=k, weighted_share=float(wr))
            L.append(f"| guideline-healthy adults, any disease asserted | {c} | {n} | {k}/{n} unweighted | weighted share {100*wr:.2f}% | | |")
    L += ["", "Design note: the 3,000 evaluated adults per cycle are a seeded random subsample of eligible MEC participants; weights act as relative weights within the subsample. Strata with a single sampled PSU are resampled as themselves. Domain estimation (subsetting) is approximated by weighting within the evaluated set.", ""]
    os.makedirs(os.path.join(ROOT, "eval/results"), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, "eval/results/nhanes_weighted_v7.json"), "w"), indent=1)
    open(os.path.join(ROOT, "eval/results/nhanes_weighted_v7.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__": main()
