"""Subgroup / fairness analysis on eICU-CRD demo per-stay engine outputs (TRIPOD+AI item 'performance in key subgroups').

Strata: sex, age band, ethnicity (eICU 'ethnicity' field), ICU unit type, hospital (top-8 by stays), panel size.
Metrics per stratum (pooled over all lab-detectable clinician-listed groups): recall@5, recall@10, chart support of
p >= 0.7 outputs, AUROC for the four largest groups, and false-assertion proxy (entities p >= 0.5 with no listed problem in
stays with an empty problem list). Bootstrap 95 % CIs (1,000 resamples over stays). No subgroup-specific tuning exists in
the engine; creatinine-based eGFR uses CKD-EPI 2021 (race-free) throughout.

python3 eval/subgroup_fairness.py --per-stay eval/results/eicu_demo/per_stay.json --out eval/results/eicu_demo/subgroup_fairness_v4.md
"""
import json, argparse, collections, sys, gzip
import numpy as np, pandas as pd
sys.path.insert(0, "eval/realdata")
from eval_nhanes import auroc

ap = argparse.ArgumentParser(); ap.add_argument("--per-stay", required=True); ap.add_argument("--out", required=True); ap.add_argument("--label", default="v4")
a = ap.parse_args()
import gzip
rows = json.load(gzip.open(a.per_stay,'rt') if a.per_stay.endswith('.gz') else open(a.per_stay))
pt = pd.read_csv("eval/realdata/eicu_demo/patient.csv.gz", usecols=["patientunitstayid", "ethnicity", "unittype", "hospitalid"]).set_index("patientunitstayid")
sys.path.insert(0, "eval/realdata"); import eval_eicu as ee
KEY = {g: t[2] for g, t in ee.GROUPS.items()}
BIG = ["renal_impairment", "sepsis", "anemia", "acute_kidney_injury"]


def age_band(x): return "<45" if x < 45 else "45–64" if x < 65 else "65–79" if x < 80 else "≥80"


def strat(r):
    p = pt.loc[r["stay"]] if r["stay"] in pt.index else None
    eth = str(p["ethnicity"]) if p is not None and isinstance(p["ethnicity"], str) else "Unknown"
    return {"sex": r["sex"], "age band": age_band(r["age"]), "ethnicity": eth,
            "unit type": str(p["unittype"]) if p is not None else "Unknown", "hospital": f"hosp {p['hospitalid']}" if p is not None else "Unknown",
            "panel size": "≤10 analytes" if r["n_in"] <= 10 else "11–20" if r["n_in"] <= 20 else ">20"}


def metrics(sub):
    r5 = r10 = tot = 0; sup = [0, 0]; fa = [0, 0]; au = {}
    for r in sub:
        for g in r["coded"]:
            if g not in KEY or not any(k in r["labs"] for k in KEY[g]): continue
            tot += 1; rk = r["gr"].get(g) or 99; r5 += rk <= 5; r10 += rk <= 10
        for d, p in r["top5"]:
            if p >= 0.7:
                sup[1] += 1; sup[0] += any(d in ee.GROUPS[g][1] for g in r["coded"] if g in ee.GROUPS)
        if not r["coded"]:
            fa[1] += 1; fa[0] += any(p >= 0.5 for _, p in r["top5"])
    for g in BIG:
        pos = [r["gp"].get(g, 0.0) for r in sub if g in r["coded"] and any(k in r["labs"] for k in KEY[g])]
        neg = [r["gp"].get(g, 0.0) for r in sub if g not in r["coded"] and any(k in r["labs"] for k in KEY[g])]
        au[g] = auroc(np.array([1] * len(pos) + [0] * len(neg)), np.array(pos + neg)) if len(pos) >= 5 and len(neg) >= 5 else float("nan")
    return dict(n=len(sub), listed=tot, r5=r5 / max(tot, 1), r10=r10 / max(tot, 1), sup=sup[0] / max(sup[1], 1), nsup=sup[1],
                fa=fa[0] / max(fa[1], 1), nfa=fa[1], au=au)


def boot_r5(sub, n=1000, seed=0):
    rng = np.random.default_rng(seed); vals = []
    for _ in range(n):
        s = [sub[i] for i in rng.integers(0, len(sub), len(sub))]; vals.append(metrics(s)["r5"])
    return np.percentile(vals, [2.5, 97.5])


S = [strat(r) for r in rows]
overall = metrics(rows)
L = [f"# Subgroup and fairness analysis — eICU-CRD demo (n = {len(rows)} stays), engine {a.label}", "",
     "Metrics are pooled over all laboratory-detectable clinician-listed diagnoses in the stratum. recall@5 CI = 1,000-stay bootstrap. "
     "AUROC columns use the per-stay group probability for the four most frequent groups; '—' = fewer than 5 positives or negatives. "
     "The engine contains no race, ethnicity or hospital term; eGFR is CKD-EPI 2021 (race-free). Strata with < 40 stays are shown but not interpreted.", "",
     f"Overall: recall@5 {100*overall['r5']:.1f}%, recall@10 {100*overall['r10']:.1f}%, chart support {100*overall['sup']:.1f}% (n = {overall['nsup']}), "
     f"false-assertion proxy in stays with empty problem list {100*overall['fa']:.1f}% (n = {overall['nfa']}).", ""]
flags = []
for dim in ("sex", "age band", "ethnicity", "unit type", "panel size", "hospital"):
    groups = collections.defaultdict(list)
    for r, s in zip(rows, S): groups[s[dim]].append(r)
    items = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    if dim == "hospital": items = items[:8]
    L += [f"## By {dim}", "", "| stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p≥0.7 | " + " | ".join(f"AUROC {g.replace('_', ' ')}" for g in BIG) + " |",
          "|---|---:|---:|---|---:|---:|" + "---:|" * len(BIG)]
    for k, sub in items:
        m = metrics(sub); lo, hi = boot_r5(sub) if len(sub) >= 20 else (float("nan"), float("nan"))
        L.append(f"| {k} | {m['n']} | {m['listed']} | {100*m['r5']:.1f}% ({100*lo:.1f}–{100*hi:.1f}) | {100*m['r10']:.1f}% | {100*m['sup']:.1f}% | "
                 + " | ".join("—" if np.isnan(m['au'][g]) else f"{m['au'][g]:.2f}" for g in BIG) + " |")
        if len(sub) >= 40 and abs(m["r5"] - overall["r5"]) > 0.10: flags.append(f"{dim} = {k}: recall@5 {100*m['r5']:.1f}% vs overall {100*overall['r5']:.1f}%")
    L.append("")
L += ["## Strata deviating by more than 10 percentage points from overall recall@5 (n ≥ 40)", ""] + ([f"- {f}" for f in flags] or ["- none"])
open(a.out, "w").write("\n".join(L) + "\n"); print("\n".join(L[:8])); print("flags:", flags)
