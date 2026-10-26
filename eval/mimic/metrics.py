# -*- coding: utf-8 -*-
"""
Compute the pre-specified metrics from results.jsonl (run_retrospective.py).

Primary outcome   : top-3 accuracy of 'full' (expected group's accepted
                    disease_id ranked <= 3), overall and in lab-detectable groups.
Secondary         : top-1, top-5, MRR; Brier score and expected calibration
                    error (ECE, 10 equal-width bins) of the probability assigned
                    to the target; AUROC-free by design (no negatives per class).
Comparators       : paired McNemar exact test (two-sided mid-p) on top-3 hits
                    full vs rule_only / naive_bayes / mean_fusion; bootstrap
                    (2,000 resamples, seed fixed) 95% CI of the difference.
Secondary analyses: per-group table; evidence-state analysis (hit rate when
                    the top candidate is 'supported' vs 'insufficient');
                    Bel–Pl gap of the target vs correctness.
Error listing     : first 100 misses of 'full' for clinician review
                    (hadm_id, group, top-5 with probabilities).

Usage: python eval/mimic/metrics.py --results eval/results/results.jsonl --out eval/results/metrics.md
"""
from __future__ import annotations
import argparse, csv, json, math, os, random, collections
HERE = os.path.dirname(os.path.abspath(__file__))

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 3
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d
def pct(k, n):
    p, lo, hi = wilson(k, n); return f"{100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f})"

def mcnemar_midp(b, c):
    """Exact binomial McNemar, two-sided mid-p. b = full hit & comp miss, c = full miss & comp hit."""
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    def pmf(i): return math.comb(n, i) * 0.5 ** n
    p = 2 * (sum(pmf(i) for i in range(0, k)) + 0.5 * pmf(k))
    return min(1.0, p)

def target_rank(diff, accepted):
    for d in diff:
        if d["disease_id"] in accepted:
            return d["rank"], d
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", default="eval/results/metrics.md")
    ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261020)
    a = ap.parse_args()
    groups = {r["group"]: (set(r["accepted_disease_ids"].split("|")), r["lab_detectable"]) for r in csv.DictReader(open(os.path.join(HERE, "icd10_map.csv"), encoding="utf-8"))}
    recs = [json.loads(l) for l in open(a.results, encoding="utf-8")]
    cfgs = ["full", "rule_only", "naive_bayes", "mean_fusion"]

    per = {c: [] for c in cfgs}     # list of dicts per case
    for r in recs:
        acc, det = groups[r["group"]]
        for c in cfgs:
            diff = r["results"].get(c, {}).get("differential", [])
            rk, d = target_rank(diff, acc)
            p = float(d["probability"]) if d else 0.0
            top = diff[0] if diff else None
            per[c].append({"hadm": r["hadm_id"], "group": r["group"], "det": det, "rank": rk, "p": p,
                           "top_state": (top or {}).get("evidence_state"), "gap": (float(d["plausibility"]) - float(d["belief"])) if d and d.get("plausibility") is not None and d.get("belief") is not None else None,
                           "top5": [(x["disease_id"], round(float(x["probability"]), 2)) for x in diff[:5]], "ms": r["results"].get(c, {}).get("ms")})

    def hits(rows, k): return [1 if (x["rank"] is not None and x["rank"] <= k) else 0 for x in rows]
    def mrr(rows): return sum(1 / x["rank"] for x in rows if x["rank"]) / max(1, len(rows))
    def brier(rows): return sum((x["p"] - 1.0) ** 2 for x in rows) / max(1, len(rows))   # target always present → outcome 1; penalises low p on target
    def ece(rows, bins=10):
        # calibration of P(top-1 correct) using the top candidate's probability
        tot = 0.0; n = len(rows); table = []
        for b in range(bins):
            lo, hi = b / bins, (b + 1) / bins
            sel = [x for x in rows if x["top5"] and lo <= x["top5"][0][1] < hi + (1e-9 if b == bins - 1 else 0)]
            if not sel: table.append((lo, hi, 0, None, None)); continue
            conf = sum(x["top5"][0][1] for x in sel) / len(sel)
            acc = sum(1 for x in sel if x["rank"] == 1) / len(sel)
            tot += len(sel) / n * abs(acc - conf); table.append((lo, hi, len(sel), conf, acc))
        return tot, table

    L = [f"# Retrospective evaluation — metrics\n\nCases: {len(recs)}; groups: {len(set(r['group'] for r in recs))}; configurations: {', '.join(cfgs)}.\n"]
    L.append("## Primary and secondary outcomes\n\n| Config | top-1 | top-3 (primary) | top-5 | MRR | Brier(target) | ECE(top-1) | median ms |\n|---|---|---|---|---|---|---|---|")
    for c in cfgs:
        rows = per[c]; n = len(rows)
        e, _ = ece(rows); ms = sorted(x["ms"] for x in rows if x["ms"] is not None)
        L.append(f"| {c} | {pct(sum(hits(rows,1)), n)} | **{pct(sum(hits(rows,3)), n)}** | {pct(sum(hits(rows,5)), n)} | {mrr(rows):.3f} | {brier(rows):.3f} | {e:.3f} | {ms[len(ms)//2]:.0f} |" if ms else f"| {c} | {pct(sum(hits(rows,1)), n)} | **{pct(sum(hits(rows,3)), n)}** | {pct(sum(hits(rows,5)), n)} | {mrr(rows):.3f} | {brier(rows):.3f} | {e:.3f} | — |")
    # lab-detectable subset
    L.append("\n### Lab-detectable groups only\n\n| Config | n | top-1 | top-3 | top-5 |\n|---|---|---|---|---|")
    for c in cfgs:
        rows = [x for x in per[c] if x["det"] == "yes"]; n = len(rows)
        L.append(f"| {c} | {n} | {pct(sum(hits(rows,1)), n)} | {pct(sum(hits(rows,3)), n)} | {pct(sum(hits(rows,5)), n)} |")

    # paired comparisons
    L.append("\n## Paired comparison vs full (top-3)\n\n| Comparator | full✓ comp✗ | full✗ comp✓ | Δ top-3 (full − comp) | bootstrap 95% CI | McNemar mid-p |\n|---|---|---|---|---|---|")
    rng = random.Random(a.seed); hf = hits(per["full"], 3)
    for c in cfgs[1:]:
        hc = hits(per[c], 3); b = sum(1 for x, y in zip(hf, hc) if x and not y); cc = sum(1 for x, y in zip(hf, hc) if y and not x)
        n = len(hf); d0 = (sum(hf) - sum(hc)) / n
        ds = []
        for _ in range(a.boot):
            idx = [rng.randrange(n) for _ in range(n)]
            ds.append(sum(hf[i] - hc[i] for i in idx) / n)
        ds.sort(); lo, hi = ds[int(0.025 * a.boot)], ds[int(0.975 * a.boot) - 1]
        L.append(f"| {c} | {b} | {cc} | {100*d0:+.1f} pp | {100*lo:+.1f} to {100*hi:+.1f} | {mcnemar_midp(b, cc):.4f} |")

    # calibration table (full)
    e, table = ece(per["full"])
    L.append(f"\n## Calibration of top-1 probability (full), ECE = {e:.3f}\n\n| bin | n | mean confidence | observed top-1 accuracy |\n|---|---|---|---|")
    for lo, hi, n, conf, acc in table:
        L.append(f"| {lo:.1f}–{hi:.1f} | {n} | {'—' if conf is None else f'{conf:.2f}'} | {'—' if acc is None else f'{acc:.2f}'} |")

    # evidence state / Bel-Pl gap
    rows = per["full"]
    sup = [x for x in rows if x["top_state"] == "supported"]; ins = [x for x in rows if x["top_state"] and x["top_state"] != "supported"]
    L.append("\n## Evidence state of the top candidate vs correctness (full)\n")
    L.append(f"- top candidate 'supported': n={len(sup)}, top-1 correct {pct(sum(hits(sup,1)), len(sup))}")
    L.append(f"- top candidate other state: n={len(ins)}, top-1 correct {pct(sum(hits(ins,1)), len(ins))}")
    g_ok = [x["gap"] for x in rows if x["gap"] is not None and x["rank"] == 1]; g_bad = [x["gap"] for x in rows if x["gap"] is not None and x["rank"] != 1]
    if g_ok and g_bad:
        L.append(f"- mean Bel–Pl gap of target when top-1 correct {sum(g_ok)/len(g_ok):.3f} vs otherwise {sum(g_bad)/len(g_bad):.3f}")

    # per group
    L.append("\n## Per-group top-3 (full / rule_only / naive_bayes / mean_fusion)\n\n| Group | n | detectable | full | rule_only | naive_bayes | mean_fusion |\n|---|---|---|---|---|---|---|")
    byg = collections.defaultdict(list)
    for i, x in enumerate(per["full"]): byg[x["group"]].append(i)
    for g, idx in sorted(byg.items(), key=lambda kv: -len(kv[1])):
        cells = []
        for c in cfgs:
            h = [1 if (per[c][i]["rank"] and per[c][i]["rank"] <= 3) else 0 for i in idx]
            cells.append(pct(sum(h), len(h)))
        L.append(f"| {g} | {len(idx)} | {groups[g][1]} | " + " | ".join(cells) + " |")

    # misses for review
    L.append("\n## First 100 top-3 misses of full (for clinician error classification)\n\n| hadm_id | group | target rank | top-5 (p) |\n|---|---|---|---|")
    k = 0
    for x in per["full"]:
        if x["rank"] is None or x["rank"] > 3:
            L.append(f"| {x['hadm']} | {x['group']} | {x['rank'] or '—'} | {', '.join(f'{d} ({p})' for d, p in x['top5'])} |"); k += 1
            if k >= 100: break
    L.append("\nError-classification scheme (to be applied by the clinical co-author, blinded to configuration): (A) knowledge gap — no rule/LR covers the pattern; (B) fusion/ranking error — correct candidate present but out-ranked; (C) label noise — ICD primary code not supported by the labs; (D) not lab-detectable from first-24 h panel; (E) input problem — unit/mapping.")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L[:30])); print("saved", a.out)

if __name__ == "__main__":
    main()
