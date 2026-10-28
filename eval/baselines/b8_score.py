"""Score the B8 blind LLM read-out (n=240 eICU-demo stays) against coded labels and the engine (v5.1 labs-only),
then pool with B3 (n=100) and B4 (n=60) -> n=400 paired comparison.

python3 eval/baselines/b8_score.py
Outputs eval/results/eicu_demo/b8_score_n240.md and b3b4b8_pooled_n400.md (+ json).
Rules identical to llm_zero_shot.score(): label counted when its key analyte was measured; LLM hit = any of the
first 5 LLM entries matches the group's SYN regex; engine hit = engine rank <= 5. McNemar exact (binomial) on
discordant label-level pairs.
"""
import json, re, sys, os, math, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.dirname(__file__))
from eval_eicu import GROUPS
from llm_zero_shot import SYN
R = os.path.join(ROOT, "eval", "results", "eicu_demo")


def llm_ranks(entries):
    gr = {}
    for rank, d in enumerate(entries, 1):
        nm = str(d.get("name", ""))
        for g, rx in SYN.items():
            if re.search(rx, nm, re.I):
                gr.setdefault(g, rank)
    return gr


def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def fmt(k, n):
    p, lo, hi = wilson(k, n); return f"{100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f}; {k}/{n})"


def mcnemar(b, c):
    """exact two-sided binomial on discordant pairs b (engine only) vs c (LLM only)"""
    n = b + c
    if n == 0: return 1.0
    k = min(b, c); p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(1.0, p)


def pairs_from(rows, llm_key, eng_key):
    """rows: list with labs, coded, <llm entries>, <engine rank dict>. returns list of (group, eng_hit, llm_hit)"""
    out = []
    for r in rows:
        lg = llm_ranks(r[llm_key]); eg = r[eng_key]
        for g in r["coded"]:
            if g not in GROUPS or not any(k in r["labs"] for k in GROUPS[g][2]): continue
            out.append((g, (eg.get(g) or 99) <= 5, (lg.get(g) or 99) <= 5))
    return out


def report(title, pairs, n_stays):
    E = sum(e for _, e, _ in pairs); L = sum(l for _, _, l in pairs); N = len(pairs)
    b = sum(e and not l for _, e, l in pairs); c = sum(l and not e for _, e, l in pairs)
    lines = [f"# {title}", "", f"stays {n_stays}; scorable labels {N}", "",
             f"| | Recall@5 |", "|---|---|", f"| Hemoglyph | {fmt(E, N)} |", f"| GPT-4-class LLM (agent, blind) | {fmt(L, N)} |", "",
             f"Discordant: engine-only {b}, LLM-only {c}; McNemar exact p = {mcnemar(b, c):.2g}; difference {100*(E-L)/N:+.1f} pp", "",
             "| group | n | Hemoglyph | LLM |", "|---|---:|---|---|"]
    byg = collections.defaultdict(lambda: [0, 0, 0])
    for g, e, l in pairs:
        byg[g][0] += 1; byg[g][1] += e; byg[g][2] += l
    for g, (n, e, l) in sorted(byg.items(), key=lambda x: -x[1][0]):
        lines.append(f"| {g} | {n} | {100*e/n:.0f}% | {100*l/n:.0f}% |")
    return "\n".join(lines), dict(n_labels=N, engine=E, llm=L, b=b, c=c, p=mcnemar(b, c))


llm = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_blind_n240.json")))["cases"]}
key = json.load(open(os.path.join(R, "b8_key_n240.json")))
panels = {p["case"]: p for p in json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))}
rows8 = [dict(labs=list(panels[k["case"]]["labs"]), coded=k["coded"], llm=llm[k["case"]], gr=k["engine_gr"]) for k in key]
p8 = pairs_from(rows8, "llm", "gr")
t8, s8 = report("B8 — blind LLM vs Hemoglyph v5.1 (labs-only), 240 new eICU-demo stays", p8, 240)
open(os.path.join(R, "b8_score_n240.md"), "w").write(t8 + "\n")

v51 = {r["stay"]: r for r in json.load(open(os.path.join(ROOT, "eval/results/run_20261023_v5/eicu_per_stay_v5_1.json")))}
def load_b(path):
    rows = json.load(open(os.path.join(R, path))); out = []
    for r in rows:
        eg = v51[r["stay"]]["gr"] if r["stay"] in v51 else r["gr"]
        out.append(dict(labs=r["labs"], coded=r["coded"], llm=r["llm"], gr=eg, src=("v5.1" if r["stay"] in v51 else "stored")))
    return out
rows3 = load_b("llm_agent_b3_n100.json")
b4llm = json.load(open(os.path.join(R, "b4_llm_blind_n60.json")))
rows4 = []
for r in json.load(open(os.path.join(R, "b4_oos_n60_vs_v3.json"))):
    eg = v51[r["stay"]]["gr"] if r["stay"] in v51 else r["gr"]
    rows4.append(dict(labs=r["labs"], coded=r["coded"], llm=[{"name": n, "probability": p} for n, p in b4llm[str(r["stay"])]], gr=eg, src=("v5.1" if r["stay"] in v51 else "stored")))
cov = sum(r["src"] == "v5.1" for r in rows3 + rows4)
p3 = pairs_from(rows3, "llm", "gr"); p4 = pairs_from(rows4, "llm", "gr")
t3, s3 = report("B3 (n=100) rescored with engine v5.1 ranks", p3, 100)
t4, s4 = report("B4 (n=60) rescored with engine v5.1 ranks", p4, 60)
tp, sp = report("POOLED B3+B4+B8 — blind GPT-4-class LLM (agent) vs Hemoglyph v5.1, n=400 eICU-demo stays", p3 + p4 + p8, 400)
hdr = (f"engine ranks taken from eicu_per_stay_v5_1.json for {cov}/160 B3+B4 stays (rest: stored ranks of the run they were scored with).\n"
       "LLM read-outs: B3/B4 2026-10-21/22, B8 2026-10-23; all by the same agent model class, blinded to labels and engine output.\n")
open(os.path.join(R, "b3b4b8_pooled_n400.md"), "w").write(hdr + "\n" + tp + "\n\n" + t8 + "\n\n" + t3 + "\n\n" + t4 + "\n")
json.dump(dict(b8=s8, b3=s3, b4=s4, pooled=sp), open(os.path.join(R, "b3b4b8_pooled_n400.json"), "w"), indent=1)
print(tp); print(); print(t8.split("\n\n")[1]); print(t8.split("\n\n")[2])
