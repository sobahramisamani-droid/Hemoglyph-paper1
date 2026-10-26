#!/usr/bin/env python3
"""Generic LabBench T2 scorer: score ANY system's ranked differentials on the 240 blind panels.

python3 eval/baselines/labbench_score.py --answers my_answers.json [--key eval/results/eicu_demo/b8_key_n240.json] [--k 5]

answers.json: {"B8-000": ["acute kidney injury", "sepsis", ...], ...}   (free-text names, <=10 per case, rank order)
Each coded label whose key analyte was measured in the panel (GROUPS rule) is a hit at rank r if any answer among the first r matches the label's synonym regex
(SYN in llm_zero_shot.py — the identical map used for the published LLM and engine arms). Reports recall@1/3/5/10,
MRR and "not listed" rate with Wilson 95% CIs, label-level, exactly as in b8_score.py / b8_rank_metrics.py.
"""
import argparse, json, math, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from llm_zero_shot import SYN
from eval_eicu import GROUPS


def wilson(k, n, z=1.96):
    if n == 0: return 0, 0, 0
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--answers", required=True)
    ap.add_argument("--key", default=os.path.join(ROOT, "eval", "results", "eicu_demo", "b8_key_n240.json"))
    ap.add_argument("--panels", default=os.path.join(ROOT, "eval", "results", "eicu_demo", "b8_blind_panels_n240.json")); a = ap.parse_args()
    ans = json.load(open(a.answers)); key = json.load(open(a.key))
    labs = {p["case"]: set(p["labs"]) for p in json.load(open(a.panels))}
    ranks, n_cases = [], 0
    for c in key:
        lst = ans.get(c["case"]) or ans.get(str(c.get("stay")))
        if lst is None: continue
        n_cases += 1
        for g in c["coded"]:
            rx = SYN.get(g)
            # label counted only when its key analyte was measured (identical rule to b8_score.py)
            if not rx or g not in GROUPS or not any(k in labs.get(c["case"], ()) for k in GROUPS[g][2]): continue
            r = next((i for i, nm in enumerate(lst[:10], 1) if re.search(rx, str(nm), re.I)), None)
            ranks.append(r)
    n = len(ranks)
    print(f"cases scored {n_cases}/{len(key)}; labels {n}")
    for k in (1, 3, 5, 10):
        h = sum(1 for r in ranks if r and r <= k); p, lo, hi = wilson(h, n)
        print(f"recall@{k:<2} {100*p:5.1f}% ({100*lo:.1f}–{100*hi:.1f})  {h}/{n}")
    print(f"MRR {sum(1/r for r in ranks if r)/max(n,1):.3f}; not listed {100*sum(1 for r in ranks if not r)/max(n,1):.1f}%")
    print("Published reference on the same 240 panels (b8_score_n240.md): Hemoglyph v5.1 and the GPT-4-class blind arm.")


if __name__ == "__main__":
    main()
