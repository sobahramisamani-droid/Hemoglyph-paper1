"""Reviewer response B1+B2: re-score the blind LLM comparison (n=400 stays) against the FROZEN engine v7
(per_stay_v7.json.gz, registry 14.1.0) instead of the historical v5.1, and replace label-level Wilson/McNemar
with stay-clustered inference:
  * cluster bootstrap (resample stays, 4000 reps) for recall@k of each arm and for the paired difference;
  * cluster-adjusted McNemar (Durkalski 2003, Stat Med 22:2305) for recall@5;
  * design effect / intraclass correlation of the paired-difference indicator.
No LLM output is re-generated: the stored blind read-outs (B3 2026-10-21, B4 2026-10-22, B8 2026-10-23) are reused.
Output: eval/results/eicu_demo/llm_vs_v7_cluster_n400.md (+ .json)
"""
import json, os, sys, gzip, math, random, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.dirname(__file__))
from eval_eicu import GROUPS
import re
from llm_zero_shot import SYN
def llm_ranks(entries):
    gr = {}
    for rank, d in enumerate(entries, 1):
        nm = str(d.get("name", ""))
        for g, rx in SYN.items():
            if re.search(rx, nm, re.I): gr.setdefault(g, rank)
    return gr
R = os.path.join(ROOT, "eval", "results", "eicu_demo")

v7 = {r["stay"]: r for r in json.load(gzip.open(os.path.join(R, "per_stay_v7.json.gz"), "rt"))}
key = json.load(open(os.path.join(R, "b8_key_n240.json")))
panels = {p["case"]: p for p in json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))}
llm8 = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_blind_n240.json")))["cases"]}
b3 = json.load(open(os.path.join(R, "llm_agent_b3_n100.json")))
b4s = json.load(open(os.path.join(R, "b4_oos_n60_vs_v3.json"))); b4l = json.load(open(os.path.join(R, "b4_llm_blind_n60.json")))

stays = []
for k in key: stays.append((k["stay"], list(panels[k["case"]]["labs"]), k["coded"], llm8[k["case"]]))
for r in b3: stays.append((r["stay"], r["labs"], r["coded"], r["llm"]))
for r in b4s: stays.append((r["stay"], r["labs"], r["coded"], [{"name": n, "probability": p} for n, p in b4l[str(r["stay"])]]))
assert len(stays) == 400 and len({s[0] for s in stays}) == 400
missing = [s[0] for s in stays if s[0] not in v7]
assert not missing, f"stays absent from per_stay_v7: {missing[:5]}"

def triples(tier="gr"):
    """per stay: list of (group, engine_rank or None, llm_rank or None)"""
    out = {}
    for stay, labs, coded, llm in stays:
        lg = llm_ranks(llm); eg = v7[stay][tier]
        lab = []
        for g in coded:
            if g not in GROUPS or not any(k in labs for k in GROUPS[g][2]): continue
            lab.append((g, eg.get(g), lg.get(g)))
        if lab: out[stay] = lab
    return out

def hit(x, k): return x is not None and x <= k

def recall(T, idx, k, S=None):
    S = S if S is not None else list(T)
    n = sum(len(T[s]) for s in S); h = sum(hit(t[idx], k) for s in S for t in T[s]); return h / n

def cluster_boot(T, k, B=4000, seed=7):
    rnd = random.Random(seed); S = list(T); e, l, d = [], [], []
    for _ in range(B):
        smp = [S[rnd.randrange(len(S))] for _ in S]
        re_, rl = recall(T, 1, k, smp), recall(T, 2, k, smp); e.append(re_); l.append(rl); d.append(re_ - rl)
    q = lambda v: (sorted(v)[int(0.025 * B)], sorted(v)[int(0.975 * B)])
    pd = 2 * min(sum(x <= 0 for x in d), sum(x >= 0 for x in d)) / B
    return q(e), q(l), q(d), min(1.0, pd)

def durkalski(T, k):
    """cluster-adjusted McNemar (Durkalski et al. 2003): Z = sum_i (b_i - c_i) / sqrt(sum_i (b_i - c_i)^2)"""
    num = 0.0; den = 0.0; b = c = 0
    for s, lab in T.items():
        bi = sum(hit(t[1], k) and not hit(t[2], k) for t in lab); ci = sum(hit(t[2], k) and not hit(t[1], k) for t in lab)
        num += bi - ci; den += (bi - ci) ** 2; b += bi; c += ci
    z = num / math.sqrt(den) if den else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p, b, c

def mcnemar_exact(b, c):
    n = b + c
    if n == 0: return 1.0
    p = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * p)

def icc_design(T, k):
    """ICC (ANOVA estimator) of the within-pair difference indicator d = hit_engine - hit_llm; design effect 1+(m-1)ICC"""
    groups = [[int(hit(t[1], k)) - int(hit(t[2], k)) for t in lab] for lab in T.values() if len(lab) >= 1]
    N = sum(len(g) for g in groups); K = len(groups); gm = sum(sum(g) for g in groups) / N
    m0 = (N - sum(len(g) ** 2 for g in groups) / N) / (K - 1)
    msb = sum(len(g) * (sum(g) / len(g) - gm) ** 2 for g in groups) / (K - 1)
    msw = sum((x - sum(g) / len(g)) ** 2 for g in groups for x in g) / max(1, N - K)
    icc = (msb - msw) / (msb + (m0 - 1) * msw) if (msb + (m0 - 1) * msw) else 0.0
    return icc, 1 + (N / K - 1) * icc, N, K

def mrr(T, idx, S=None):
    S = S if S is not None else list(T); n = sum(len(T[s]) for s in S)
    return sum(1.0 / t[idx] for s in S for t in T[s] if t[idx]) / n

def main():
    out = {}; L = ["# Blind GPT-4-class LLM vs Hemoglyph **engine v7 / registry 14.1.0 (frozen)** — n=400 eICU-demo stays, stay-clustered inference", "",
                   "Same 400 stays, same stored blind LLM read-outs and SYN map as the v5.1 comparison; only the engine arm is re-scored from `per_stay_v7.json.gz`.",
                   "Inference treats the stay as the cluster: cluster bootstrap (4,000 resamples of stays) and Durkalski cluster-adjusted McNemar.", ""]
    for tier, nm in (("gr", "flat (specific-diagnosis tier; primary)"), ("gr2", "two-tier (either tier)")):
        T = triples(tier); N = sum(len(v) for v in T.values()); res = {"n_stays": len(T), "n_labels": N}
        L += [f"## {nm} — {len(T)} stays with scorable labels, {N} labels", "", "| metric | Hemoglyph v7 | LLM | difference (engine − LLM) | cluster-bootstrap p | naive McNemar p | Durkalski McNemar p |", "|---|---|---|---|---|---|---|"]
        for k in (1, 3, 5, 10):
            re_, rl = recall(T, 1, k), recall(T, 2, k); (elo, ehi), (llo, lhi), (dlo, dhi), pb = cluster_boot(T, k)
            z, pdk, b, c = durkalski(T, k); pn = mcnemar_exact(b, c)
            res[f"recall@{k}"] = dict(engine=[re_, elo, ehi], llm=[rl, llo, lhi], diff=[re_ - rl, dlo, dhi], p_boot=pb, p_mcnemar=pn, p_durkalski=pdk, b=b, c=c, z=z)
            L.append(f"| recall@{k}{' (primary)' if k == 5 else ''} | {100*re_:.1f}% ({100*elo:.1f}–{100*ehi:.1f}) | {100*rl:.1f}% ({100*llo:.1f}–{100*lhi:.1f}) | {100*(re_-rl):+.1f} pp ({100*dlo:+.1f} to {100*dhi:+.1f}) | {pb:.3f} | {pn:.4f} (b={b}, c={c}) | {pdk:.4f} (z={z:.2f}) |")
        me, ml = mrr(T, 1), mrr(T, 2)
        rnd = random.Random(3); S = list(T); d = sorted(mrr(T, 1, (s := [S[rnd.randrange(len(S))] for _ in S])) - mrr(T, 2, s) for _ in range(2000))
        res["mrr"] = dict(engine=me, llm=ml, diff_ci=[d[50], d[1949]])
        L.append(f"| MRR | {me:.3f} | {ml:.3f} | {me-ml:+.3f} ({d[50]:+.3f} to {d[1949]:+.3f}) | | | |")
        ab_e = sum(t[1] is None for v in T.values() for t in v) / N; ab_l = sum(t[2] is None for v in T.values() for t in v) / N
        L.append(f"| label absent from list | {100*ab_e:.1f}% | {100*ab_l:.1f}% | | | | |")
        icc, deff, _, K = icc_design(T, 5); res["icc_recall5_diff"] = icc; res["design_effect"] = deff
        L += ["", f"Clustering: {K} stays, {N/K:.2f} labels per stay; ICC of the paired recall@5 difference = {icc:.3f}; design effect = {deff:.2f}.", ""]
        pg = collections.defaultdict(lambda: [0, 0, 0])
        for v in T.values():
            for g, e, l in v: pg[g][0] += 1; pg[g][1] += hit(e, 5); pg[g][2] += hit(l, 5)
        L += ["| group | n | Hemoglyph v7 r@5 | LLM r@5 |", "|---|---:|---|---|"]
        for g, (n, e, l) in sorted(pg.items(), key=lambda x: -x[1][0]):
            if n >= 10: L.append(f"| {g} | {n} | {100*e/n:.0f}% | {100*l/n:.0f}% |")
        res["per_group"] = {g: v for g, v in pg.items()}; out[tier] = res; L.append("")
    json.dump(out, open(os.path.join(R, "llm_vs_v7_cluster_n400.json"), "w"), indent=1)
    open(os.path.join(R, "llm_vs_v7_cluster_n400.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__": main()
