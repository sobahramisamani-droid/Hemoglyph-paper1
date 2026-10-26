"""Stay-cluster bootstrap CI for the paired difference in flat recall@5 (and two-tier@5) between each ablation arm and full v7.
Reads per_stay_v7.json.gz and per_stay_abl_<arm>.json.gz; writes ABLATION_v7_ci.md (+json). Pure numpy, no engine import."""
import os, sys, json, gzip, re, ast, numpy as np
ROOT = "/home/user/Hemoglyph"; OUT = os.path.join(ROOT, "eval/results/eicu_demo")
src = open(os.path.join(ROOT, "eval/realdata/eval_eicu.py")).read()
m = re.search(r"^GROUPS\s*=\s*(\{.*?^\})", src, re.S | re.M)
try:
    GROUPS = ast.literal_eval(m.group(1))
except Exception:
    sys.path.insert(0, os.path.join(ROOT, "eval/realdata")); from eval_eicu import GROUPS
ARMS = ["no_bayesian","no_fuzzy","no_graph","no_risk","no_esl","dempster","uniform_w","no_shrink","anchor_only","no_rule","no_unverified","w_rule_heavy","w_rule_light","anchor_only_no_esl"]
def load(p): return {r["stay"]: r for r in json.load(gzip.open(p, "rt"))}
base = load(os.path.join(OUT, "per_stay_v7.json.gz"))
def hits(F, tier, k=5):
    """per-stay (n_labels, n_hits) over evaluable labels"""
    out = {}
    for s, r in F.items():
        n = h = 0
        for g in r["coded"]:
            if g not in GROUPS or not any(x in r["labs"] for x in GROUPS[g][2]): continue
            n += 1; h += r[tier].get(g, 999) <= k
        out[s] = (n, h)
    return out
rng = np.random.default_rng(20261025); B = 4000
rows = []; res = {}
hb = {t: hits(base, t) for t in ("gr", "gr2")}
for arm in ARMS:
    p = os.path.join(OUT, f"per_stay_abl_{arm}.json.gz")
    if not os.path.exists(p): continue
    F = load(p); line = {"arm": arm}
    for tier, name in (("gr", "flat5"), ("gr2", "tt5")):
        ha = hits(F, tier); stays = [s for s in ha if s in hb[tier] and hb[tier][s][0] > 0]
        n = np.array([hb[tier][s][0] for s in stays]); a = np.array([ha[s][1] for s in stays]); b = np.array([hb[tier][s][1] for s in stays])
        d0 = 100 * (a.sum() - b.sum()) / n.sum()
        idx = rng.integers(0, len(stays), (B, len(stays)))
        ds = 100 * (a[idx].sum(1) - b[idx].sum(1)) / n[idx].sum(1)
        lo, hi = np.percentile(ds, [2.5, 97.5]); pv = 2 * min((ds <= 0).mean(), (ds >= 0).mean())
        line[name] = {"delta": d0, "lo": lo, "hi": hi, "p_boot": min(1.0, pv), "n_labels": int(n.sum()), "n_stays": len(stays)}
    rows.append(line); res[arm] = line
L = ["# Ablation — stay-cluster bootstrap (4,000 resamples) for paired differences vs full v7", "",
     "| arm | Δ flat recall@5 (pp) | 95% CI | Δ two-tier recall@5 (pp) | 95% CI | n labels / stays |", "|---|---:|---|---:|---|---:|"]
for r in rows:
    f, t = r["flat5"], r["tt5"]
    L.append(f"| {r['arm']} | {f['delta']:+.1f} | {f['lo']:+.1f} to {f['hi']:+.1f} | {t['delta']:+.1f} | {t['lo']:+.1f} to {t['hi']:+.1f} | {f['n_labels']} / {f['n_stays']} |")
open(os.path.join(OUT, "ABLATION_v7_ci.md"), "w").write("\n".join(L) + "\n")
json.dump(res, open(os.path.join(OUT, "ABLATION_v7_ci.json"), "w"), indent=1)
print("\n".join(L))
