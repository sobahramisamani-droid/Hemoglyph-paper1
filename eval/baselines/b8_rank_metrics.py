"""Rank-based metrics and LLM test-retest reproducibility for the blind LLM comparison (B3+B4+B8, n=400).

Adds to b8_score.py: Recall@1/3/5/10, mean reciprocal rank (MRR), rank distribution for engine and LLM,
and test-retest agreement of the LLM on 40 re-read B8 panels (second independent blind read, seed 20261024):
label-level hit agreement (Cohen kappa), Jaccard of the top-5 group sets, and Spearman rho of group ranks.
Mirrors the reporting of Riches et al. (Diagnosis 2024 / JAMIA Open 2025) for Isabel vs GPT-4.

python3 eval/baselines/b8_rank_metrics.py  ->  eval/results/eicu_demo/rank_metrics_n400.md (+ .json)
"""
import json, os, sys, math, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.dirname(__file__))
from eval_eicu import GROUPS
from b8_score import llm_ranks, wilson, rows8, rows3, rows4
R = os.path.join(ROOT, "eval", "results", "eicu_demo")


def label_ranks(rows):
    """(group, engine_rank, llm_rank) per scorable coded label; rank None if absent"""
    out = []
    for r in rows:
        lg = llm_ranks(r["llm"]); eg = r["gr"]
        for g in r["coded"]:
            if g not in GROUPS or not any(k in r["labs"] for k in GROUPS[g][2]):
                continue
            out.append((g, eg.get(g), lg.get(g)))
    return out


def summarise(trip):
    N = len(trip); res = {}
    for who, idx in (("engine", 1), ("llm", 2)):
        rk = [t[idx] for t in trip]
        res[who] = {f"recall@{k}": wilson(sum(1 for x in rk if x is not None and x <= k), N) for k in (1, 3, 5, 10)}
        res[who]["mrr"] = sum(1.0 / x for x in rk if x is not None) / N
        res[who]["median_rank_when_listed"] = sorted(x for x in rk if x is not None)[len([x for x in rk if x is not None]) // 2]
        res[who]["not_listed"] = sum(1 for x in rk if x is None) / N
        res[who]["rank_hist"] = collections.Counter(("1" if x == 1 else "2-3" if x and x <= 3 else "4-5" if x and x <= 5 else "6-10" if x and x <= 10 else "absent") for x in rk)
    res["n_labels"] = N
    return res


def bootstrap_mrr_diff(trip, B=2000, seed=1):
    import random
    rnd = random.Random(seed); N = len(trip); d = []
    for _ in range(B):
        s = [trip[rnd.randrange(N)] for _ in range(N)]
        d.append(sum(1.0 / t[1] for t in s if t[1]) / N - sum(1.0 / t[2] for t in s if t[2]) / N)
    d.sort(); return d[int(0.025 * B)], d[int(0.975 * B)]


def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa = sum(a) / n; pb = sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def spearman(x, y):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for i, j in enumerate(s): r[j] = i + 1
        return r
    rx, ry = rk(x), rk(y); n = len(x)
    if n < 3: return float("nan")
    return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))


def main():
    pooled = label_ranks(rows3 + rows4 + rows8); r8 = label_ranks(rows8)
    S = {"pooled_n400": summarise(pooled), "b8_n240": summarise(r8)}
    S["pooled_n400"]["mrr_diff_engine_minus_llm_ci95"] = bootstrap_mrr_diff(pooled)
    first = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_blind_n240.json")))["cases"]}
    second = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_rerun40.json")))["cases"]}
    key = {k["case"]: k for k in json.load(open(os.path.join(R, "b8_key_n240.json")))}
    panels = {p["case"]: p for p in json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))}
    a, b, jac, rho = [], [], [], []
    for c in second:
        g1, g2 = llm_ranks(first[c]), llm_ranks(second[c])
        t1 = {g for g, r in g1.items() if r <= 5}; t2 = {g for g, r in g2.items() if r <= 5}
        jac.append(len(t1 & t2) / len(t1 | t2) if (t1 | t2) else 1.0)
        common = sorted(set(g1) & set(g2))
        if len(common) >= 3: rho.append(spearman([g1[g] for g in common], [g2[g] for g in common]))
        for g in key[c]["coded"]:
            if g in GROUPS and any(k in panels[c]["labs"] for k in GROUPS[g][2]):
                a.append((g1.get(g) or 99) <= 5); b.append((g2.get(g) or 99) <= 5)
    rt = {"n_panels": len(second), "n_labels": len(a), "recall5_read1": sum(a) / len(a), "recall5_read2": sum(b) / len(b),
          "hit_agreement": sum(x == y for x, y in zip(a, b)) / len(a), "kappa": kappa(a, b),
          "jaccard_top5_groups_mean": sum(jac) / len(jac), "spearman_rho_mean": (sum(rho) / len(rho)) if rho else None, "n_rho": len(rho)}
    S["llm_test_retest_40"] = rt
    json.dump(S, open(os.path.join(R, "rank_metrics_n400.json"), "w"), indent=1, default=str)
    L = ["# Rank metrics — Hemoglyph v5.1 (labs-only) vs blind GPT-4-class LLM, pooled B3+B4+B8 (n=400 stays)", ""]
    for name, sm in (("Pooled n=400", S["pooled_n400"]), ("B8 only n=240", S["b8_n240"])):
        L += [f"## {name} — {sm['n_labels']} scorable coded labels", "", "| metric | Hemoglyph | LLM |", "|---|---|---|"]
        for k in ("recall@1", "recall@3", "recall@5", "recall@10"):
            e, l = sm["engine"][k], sm["llm"][k]
            L.append(f"| {k} | {100*e[0]:.1f}% ({100*e[1]:.1f}–{100*e[2]:.1f}) | {100*l[0]:.1f}% ({100*l[1]:.1f}–{100*l[2]:.1f}) |")
        L.append(f"| MRR | {sm['engine']['mrr']:.3f} | {sm['llm']['mrr']:.3f} |")
        L.append(f"| median rank when listed | {sm['engine']['median_rank_when_listed']} | {sm['llm']['median_rank_when_listed']} |")
        L.append(f"| not listed at all | {100*sm['engine']['not_listed']:.1f}% | {100*sm['llm']['not_listed']:.1f}% |")
        L.append("")
        L += ["| rank bin | Hemoglyph | LLM |", "|---|---|---|"]
        for bn in ("1", "2-3", "4-5", "6-10", "absent"):
            L.append(f"| {bn} | {sm['engine']['rank_hist'].get(bn,0)} | {sm['llm']['rank_hist'].get(bn,0)} |")
        L.append("")
    lo, hi = S["pooled_n400"]["mrr_diff_engine_minus_llm_ci95"]
    L += [f"MRR difference (engine − LLM), bootstrap 95% CI: {lo:+.3f} to {hi:+.3f}", "",
          "Note: the LLM list is capped at 10 free-text entries and the engine at 25 ranked diseases; recall@10 and 'absent' therefore favour the engine structurally — recall@5 is the pre-specified primary comparison.", "",
          "## LLM test–retest reproducibility (40 B8 panels, second blind read)", "",
          f"| metric | value |", "|---|---|", f"| panels / scorable labels | {rt['n_panels']} / {rt['n_labels']} |",
          f"| Recall@5 read 1 / read 2 | {100*rt['recall5_read1']:.1f}% / {100*rt['recall5_read2']:.1f}% |",
          f"| label-level hit agreement | {100*rt['hit_agreement']:.1f}% |", f"| Cohen κ | {rt['kappa']:.2f} |",
          f"| mean Jaccard of top-5 group sets | {rt['jaccard_top5_groups_mean']:.2f} |",
          f"| mean Spearman ρ of shared group ranks (n={rt['n_rho']}) | {rt['spearman_rho_mean']:.2f} |" if rt["spearman_rho_mean"] is not None else "| Spearman | n/a |",
          "", "The engine is deterministic (test–retest agreement 100% by construction; verified by byte-identical per-stay outputs across freezes).",
          "Reference: Isabel Pro vs GPT-4 (JAMIA Open 2025) reported GPT-4 run-to-run r² 0.34–0.44."]
    open(os.path.join(R, "rank_metrics_n400.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
