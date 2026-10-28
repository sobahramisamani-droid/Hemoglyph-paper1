# -*- coding: utf-8 -*-
"""
Held-out real-patient evaluation: UCI "HCV data" (Hoffmann G, et al. 2018;
Lichtinghagen R, Klawonn F, Hoffmann G; UCI ML Repository id 571; CC BY 4.0).
615 subjects from Hannover Medical School: 533 blood donors (+7 'suspect'),
24 hepatitis C, 21 fibrosis, 30 cirrhosis. Ten routine chemistry analytes in
SI units (ALB g/L, ALP/ALT/AST/GGT U/L, BIL umol/L, CHE kU/L, CHOL mmol/L,
CREA umol/L, PROT g/L) plus age and sex.

PRE-SPECIFIED analysis (written before the engine was run on this file; the
engine was NOT modified after seeing any result from this dataset):
  Task A  liver disease (hepatitis+fibrosis+cirrhosis, n=75) vs blood donors
          (n=533; the 7 'suspect' donors are excluded from A/B and reported
          separately).  Score = max probability over differential entries whose
          disease_id contains 'hepat', 'cirrho', 'liver', 'cholesta' or
          'fibros' (case-insensitive) and does not contain 'hepatorenal'.
  Task B  cirrhosis (n=30) vs everyone else without cirrhosis (donors + hepatitis
          + fibrosis).  Score = max probability over ids containing 'cirrho'.
  Metrics AUROC (Mann-Whitney), sensitivity/specificity at score >= 0.5 and
          >= 0.7, Wilson 95% CI; bootstrap 2000 for AUROC CI (seed 20261021).
  Also    top-1 disease per class (descriptive), latency.
Usage: python eval/realdata/eval_uci_hcv.py
"""
from __future__ import annotations
import os, sys, csv, json, math, time, random, logging, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT); logging.disable(logging.CRITICAL)
SRC = "eval/realdata/uci_hcv/hcvdat0.csv"; OUT = "eval/results/uci_hcv"; os.makedirs(OUT, exist_ok=True)

def wilson(k, n, z=1.96):
    if n == 0: return float("nan"), float("nan"), float("nan")
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d
def pct(k, n):
    p, lo, hi = wilson(k, n); return f"{100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f})"
def auroc(pos, neg):
    if not pos or not neg: return float("nan")
    pts = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg]); n = len(pts); ranks = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and pts[j + 1][0] == pts[i][0]: j += 1
        for k in range(i, j + 1): ranks[k] = (i + j) / 2 + 1
        i = j + 1
    rpos = sum(r for r, (s, y) in zip(ranks, pts) if y == 1)
    return (rpos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
def boot_auc(pos, neg, B=2000, seed=20261021):
    rng = random.Random(seed); vals = []
    for _ in range(B):
        vals.append(auroc([rng.choice(pos) for _ in pos], [rng.choice(neg) for _ in neg]))
    vals.sort(); return vals[int(0.025 * B)], vals[int(0.975 * B)]

LIVER_KEYS = ("hepat", "cirrho", "liver", "cholesta", "fibros")
def liver_score(diff):
    best = 0.0
    for d in diff:
        i = d["disease_id"].lower()
        if "hepatorenal" in i: continue
        if any(k in i for k in LIVER_KEYS): best = max(best, d["probability"])
    return best
def cirr_score(diff):
    return max([d["probability"] for d in diff if "cirrho" in d["disease_id"].lower()] or [0.0])

def main():
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine()
    E._reasoner.max_differential = 40  # evaluation: do not truncate the ranked list
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    MAP = [("ALB", "albumin", "g/L"), ("ALP", "alkaline_phosphatase", "U/L"), ("ALT", "alanine_aminotransferase", "U/L"), ("AST", "aspartate_aminotransferase", "U/L"),
           ("BIL", "total_bilirubin", "umol/L"), ("CHE", "cholinesterase", "kU/L"), ("CHOL", "total_cholesterol", "mmol/L"), ("CREA", "creatinine", "umol/L"), ("GGT", "gamma_glutamyl_transferase", "U/L"), ("PROT", "total_protein", "g/L")]
    known = set(E.registry.features); missing = [f for _, f, _ in MAP if f not in known]
    if missing: print("WARNING unknown feature ids:", missing)
    res = []; t0 = time.time()
    for n, r in enumerate(rows):
        obs = {}
        for col, fid, unit in MAP:
            v = r.get(col, "").strip()
            if v and v != "NA": obs[fid] = {"value": float(v), "unit": unit}
        pt = {"age_years": int(r["Age"]), "sex_at_birth": "male" if r["Sex"] == "m" else "female"}
        t1 = time.perf_counter()
        rep = E.interpret(obs, None, pt).to_dict(); diff = rep["differential_diagnosis"]
        res.append(dict(id=r[""], cat=r["Category"], liver=liver_score(diff), cirr=cirr_score(diff), top=[(d["disease_id"], round(d["probability"], 3)) for d in diff[:3]], ms=round((time.perf_counter() - t1) * 1000), warnings=len(rep.get("warnings") or [])))
        if (n + 1) % 100 == 0: print(f"  {n+1}/{len(rows)} {time.time()-t0:.0f}s")
    json.dump(res, open(f"{OUT}/per_subject.json", "w"), indent=0)
    donors = [x for x in res if x["cat"].startswith("0=")]; suspect = [x for x in res if x["cat"].startswith("0s")]
    hep = [x for x in res if x["cat"].startswith("1=")]; fib = [x for x in res if x["cat"].startswith("2=")]; cir = [x for x in res if x["cat"].startswith("3=")]
    dis = hep + fib + cir
    md = ["# UCI HCV dataset (Hoffmann 2018) — held-out real-patient evaluation", "",
          f"n = {len(res)} (donors {len(donors)}, suspect donors {len(suspect)}, hepatitis {len(hep)}, fibrosis {len(fib)}, cirrhosis {len(cir)}). "
          "Engine not modified after running on this data. Inputs in native SI units (conversion exercised).", ""]
    def task(name, pos, neg, key):
        P = [x[key] for x in pos]; N = [x[key] for x in neg]; au = auroc(P, N); lo, hi = boot_auc(P, N)
        s5 = sum(p >= 0.5 for p in P); sp5 = sum(p < 0.5 for p in N); s7 = sum(p >= 0.7 for p in P); sp7 = sum(p < 0.7 for p in N)
        md.extend([f"## {name}", "", f"- AUROC = **{au:.3f}** (bootstrap 95% CI {lo:.3f}–{hi:.3f}); positives {len(P)}, negatives {len(N)}",
                   f"- threshold 0.5: sensitivity {pct(s5, len(P))}, specificity {pct(sp5, len(N))}",
                   f"- threshold 0.7: sensitivity {pct(s7, len(P))}, specificity {pct(sp7, len(N))}", ""])
        return dict(task=name, auroc=au, ci=(lo, hi), n_pos=len(P), n_neg=len(N), sens50=s5 / len(P), spec50=sp5 / len(N), sens70=s7 / len(P), spec70=sp7 / len(N))
    summary = [task("Task A — any liver disease vs blood donors", dis, donors, "liver"),
               task("Task B — cirrhosis vs all non-cirrhotic subjects", cir, donors + hep + fib, "cirr"),
               task("Task A' — hepatitis only vs donors", hep, donors, "liver"), task("Task A'' — fibrosis only vs donors", fib, donors, "liver"), task("Task A''' — cirrhosis vs donors", cir, donors, "liver")]
    md += ["## Per-class sensitivity of the liver score (threshold 0.5)", "", "| class | n | liver score ≥ 0.5 | cirrhosis score ≥ 0.5 | most frequent top-1 |", "|---|---:|---|---|---|"]
    for name, grp in (("blood donor", donors), ("suspect donor", suspect), ("hepatitis", hep), ("fibrosis", fib), ("cirrhosis", cir)):
        if not grp: continue
        c = collections.Counter(x["top"][0][0] if x["top"] else "—" for x in grp).most_common(3)
        md.append(f"| {name} | {len(grp)} | {pct(sum(x['liver'] >= 0.5 for x in grp), len(grp))} | {pct(sum(x['cirr'] >= 0.5 for x in grp), len(grp))} | {', '.join(f'{a} ({b})' for a, b in c)} |")
    lat = sorted(x["ms"] for x in res); md += ["", f"Latency median {lat[len(lat)//2]} ms, p95 {lat[int(0.95*len(lat))-1]} ms."]
    fp = [x for x in donors if x["liver"] >= 0.5]
    md += ["", f"## False-positive donors (liver score ≥ 0.5): {len(fp)}", ""] + [f"- donor {x['id']}: {x['top']}" for x in fp[:40]]
    md += ["", "## Missed liver-disease subjects (liver score < 0.5)", ""] + [f"- {x['cat']} #{x['id']}: {x['top']}" for x in dis if x["liver"] < 0.5][:60]
    open(f"{OUT}/report.md", "w", encoding="utf-8").write("\n".join(md)); json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
    print("\n".join(md[:40]))

if __name__ == "__main__":
    main()
