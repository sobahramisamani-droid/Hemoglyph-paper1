#!/usr/bin/env python3
"""Verified consensus arm (protocol: eval/consensus/PROTOCOL.md, committed before this script existed).

F = reciprocal-rank fusion (k = 0) of the frozen engine's group ranking with the LLM entries that the engine's
criteria support (verdict "supported" in eval/verifier/entry_verdicts.json). G = engine list followed by supported
LLM groups absent from it. Output: eval/consensus/RESULTS.md, results.json
"""
import json, os, sys, gzip, random, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.join(ROOT, "eval", "baselines")); sys.path.insert(0, os.path.join(ROOT, "eval", "verifier"))
from eval_eicu import GROUPS
from panel_supported_metric import CRIT
import verify_llm_output as V

rows, reads = V.rows, V.reads
ent = json.load(open(os.path.join(ROOT, "eval", "verifier", "entry_verdicts.json")))
by_stay = collections.defaultdict(list)
for e in ent: by_stay[e["stay"]].append(e)

def bprime_ranks(s):
    gr = {}; r = 0
    for e in sorted(by_stay[s], key=lambda e: e["rank"]):
        if e["verdict"] != "supported": continue
        r += 1
        for g in e["groups"]: gr.setdefault(g, r)
    return gr

def fuse_F(A, B):
    sc = {g: (1.0 / A[g] if g in A else 0.0) + (1.0 / B[g] if g in B else 0.0) for g in set(A) | set(B)}
    order = sorted(sc, key=lambda g: (-sc[g], A.get(g, 999), B.get(g, 999)))
    return {g: i + 1 for i, g in enumerate(order)}

def fuse_G(A, B):
    order = sorted(A, key=A.get) + [g for g in sorted(B, key=B.get) if g not in A]
    return {g: i + 1 for i, g in enumerate(order)}

arms = {"engine_v7": {}, "llm_raw": {}, "F_rrf_verified": {}, "G_append_verified": {}}
for s in reads:
    A = rows[s]["gr"]; B = bprime_ranks(s)
    arms["engine_v7"][s] = A; arms["llm_raw"][s] = V.ranks_from_entries(reads[s])
    arms["F_rrf_verified"][s] = fuse_F(A, B); arms["G_append_verified"][s] = fuse_G(A, B)

def labels(s): return V.labels(rows[s])
def recall(arm, k, S=None):
    S = S or list(reads); n = h = 0
    for s in S:
        for g in labels(s): n += 1; h += arm[s].get(g, 99) <= k
    return h / n
def boot(a, b, k, B=4000, seed=7):
    rnd = random.Random(seed); S = list(reads); d = []
    for _ in range(B):
        smp = [S[rnd.randrange(len(S))] for _ in S]; d.append(recall(a, k, smp) - recall(b, k, smp))
    d.sort(); p = 2 * min(sum(x <= 0 for x in d), sum(x >= 0 for x in d)) / B
    return d[int(0.025 * B)], d[int(0.975 * B)], min(1.0, p)

def unsup(arm):
    u = n = 0
    for s in reads:
        for g, rk in arm[s].items():
            if rk <= 5 and CRIT.get(g): n += 1; u += V.verdict(g, rows[s]) in V.UNSUP
    return u, n
src = collections.Counter()
for s in reads:
    for g, rk in arms["F_rrf_verified"][s].items():
        if rk <= 5: src["engine_list" if g in rows[s]["gr"] else "llm_supported_only"] += 1
strata = collections.defaultdict(lambda: collections.Counter())
for s in reads:
    for g in labels(s):
        st = "no_criterion" if not CRIT.get(g) else {True: "criterion_met", False: "criterion_not_met", None: "analyte_missing"}[CRIT[g](V.crit_vals(rows[s]["vals"]), rows[s])]
        strata[st]["n"] += 1
        for a in arms: strata[st][a] += arms[a][s].get(g, 99) <= 5

res = {"recall": {a: {k: recall(arm, k) for k in (1, 3, 5, 10)} for a, arm in arms.items()},
       "paired": {"F_minus_engine": {k: boot(arms["F_rrf_verified"], arms["engine_v7"], k) for k in (1, 3, 5, 10)},
                  "F_minus_llm": {k: boot(arms["F_rrf_verified"], arms["llm_raw"], k) for k in (1, 3, 5, 10)},
                  "G_minus_engine": {5: boot(arms["G_append_verified"], arms["engine_v7"], 5)}},
       "top5_unsupported": {a: unsup(arm) for a, arm in arms.items()}, "F_top5_source": dict(src),
       "strata_recall5": {st: dict(c) for st, c in strata.items()}, "n_labels": sum(len(labels(s)) for s in reads)}
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)

L = ["# Verified consensus arm — 400 blind eICU stays (fusion rule fixed in PROTOCOL.md before computation)", "",
     "| Arm | recall@1 | @3 | @5 | @10 | top-5 unsupported (criterion groups) |", "|---|---|---|---|---|---|"]
for a, rr in res["recall"].items():
    u, n = res["top5_unsupported"][a]
    L.append(f"| {a} | " + " | ".join(f"{100*rr[k]:.1f}" for k in (1, 3, 5, 10)) + f" | {u}/{n} ({100*u/n:.1f} %) |")
L += ["", "Paired differences (stay-clustered bootstrap, 4000 reps), points:"]
for nm, d in res["paired"].items():
    L.append(f"- {nm}: " + "; ".join(f"@{k} {100*(lo+hi)/2:+.1f}* ({100*lo:+.1f} to {100*hi:+.1f}, p={p:.4f})" for k, (lo, hi, p) in d.items()) + "  (*midpoint of CI; point estimate in table)")
L += ["", f"F top-5 entries: {src['engine_list']} from the engine list, {src['llm_supported_only']} admitted via the LLM and the criterion only.",
      "", "recall@5 by label stratum (criterion status in the panel):", "| stratum | n | engine | LLM | F | G |", "|---|---|---|---|---|---|"]
for st, c in res["strata_recall5"].items():
    L.append(f"| {st} | {c['n']} | " + " | ".join(f"{100*c[a]/c['n']:.1f}" for a in arms) + " |")
L += ["", "Registered predictions: F recall@5 63-67 %; F recall@1 >= 29 %; F top-5 unsupported <= 15.3 %; G within 1 point of F at k=5; F < 62 % => not complementary."]
open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
