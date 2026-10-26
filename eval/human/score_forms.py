"""Score the returned human-validation forms.

A1: python3 eval/human/score_forms.py a1 eval/human/A1_rule_audit_form_FILLED.csv
    -> error rate (incorrect / total) with Wilson 95% CI, by rule_type and by severity; ambiguous reported separately.
B1: python3 eval/human/score_forms.py b1 eval/human/B1_blind_panel_form_FILLED.csv
    -> Recall@5 / MRR for the physician on the 40 panels, scored with the SAME keyword map used for the LLM
       (llm_zero_shot.SYN), plus the engine (v5.1 labs-only) and LLM read 1 / read 2 on the same 40 panels.
Outputs eval/results/eicu_demo/human_A1_result.md or human_B1_result.md.
"""
import os, sys, csv, json, math, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.join(ROOT, "eval", "baselines"))
R = os.path.join(ROOT, "eval", "results", "eicu_demo")


def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def a1(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    vcol = [c for c in rows[0] if c.startswith("VERDICT")][0]; scol = [c for c in rows[0] if c.startswith("SEVERITY")][0]
    v = [(r["rule_type"], r[vcol].strip(), r[scol].strip().upper()[:1]) for r in rows if r[vcol].strip()]
    strata = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        if r[vcol].strip(): strata[r.get("stratum", "?")][0] += 1; strata[r.get("stratum", "?")][1] += r[vcol].strip() == "2"; strata[r.get("stratum", "?")][2] += r[vcol].strip() == "3"
    n = len(v); inc = sum(1 for _, x, _ in v if x == "2"); amb = sum(1 for _, x, _ in v if x == "3")
    p, lo, hi = wilson(inc, n)
    L = ["# A1 — physician audit of 100 random executable rules", "", f"rules judged {n}/{len(rows)}", "",
         f"| incorrect | {inc}/{n} = {100*p:.1f}% (95% CI {100*lo:.1f}–{100*hi:.1f}) |", f"| ambiguous / context-dependent | {amb}/{n} = {100*amb/n:.1f}% |",
         f"| correct | {n-inc-amb}/{n} = {100*(n-inc-amb)/n:.1f}% |", "", "| stratum | n | incorrect (95% CI) | ambiguous |", "|---|---:|---|---:|"]
    for st, (a, b, c) in sorted(strata.items()):
        pp, l2, h2 = wilson(b, a); L.append(f"| {st} | {a} | {b} = {100*pp:.1f}% ({100*l2:.1f}–{100*h2:.1f}) | {c} |")
    L += ["", "| rule_type | n | incorrect | ambiguous |", "|---|---:|---:|---:|"]
    by = collections.defaultdict(lambda: [0, 0, 0])
    for t, x, _ in v: by[t][0] += 1; by[t][1] += x == "2"; by[t][2] += x == "3"
    for t, (a, b, c) in sorted(by.items()): L.append(f"| {t} | {a} | {b} | {c} |")
    sev = collections.Counter(s for _, x, s in v if x == "2")
    L += ["", "| severity of incorrect rules | n |", "|---|---:|"] + [f"| {k or '?'} | {c} |" for k, c in sorted(sev.items())]
    open(os.path.join(R, "human_A1_result.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))


def b1(path):
    from eval_eicu import GROUPS
    from b8_score import llm_ranks
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    phys = collections.defaultdict(list)
    for r in rows:
        if r["diagnosis"].strip(): phys[r["case"]].append({"name": r["diagnosis"], "rank": int(r["rank"])})
    for c in phys: phys[c].sort(key=lambda d: d["rank"])
    key = {k["case"]: k for k in json.load(open(os.path.join(R, "b8_key_n240.json")))}
    panels = {p["case"]: p for p in json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))}
    l1 = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_blind_n240.json")))["cases"]}
    l2 = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_rerun40.json")))["cases"]}
    arms = {"physician": {}, "LLM read 1": {}, "LLM read 2": {}, "Hemoglyph v5.1": {}}
    hits = {a: [] for a in arms}; rr = {a: [] for a in arms}
    for c in phys:
        k = key[c]; gp = llm_ranks(phys[c]); g1 = llm_ranks(l1[c]); g2 = llm_ranks(l2[c]); ge = k["engine_gr"]
        for g in k["coded"]:
            if g not in GROUPS or not any(x in panels[c]["labs"] for x in GROUPS[g][2]): continue
            for a, gr in (("physician", gp), ("LLM read 1", g1), ("LLM read 2", g2), ("Hemoglyph v5.1", ge)):
                r = gr.get(g); hits[a].append(bool(r and r <= 5)); rr[a].append(1.0 / r if r else 0.0)
    n = len(hits["physician"])
    L = [f"# B1 — blind physician reading vs LLM vs Hemoglyph on the same {len(phys)} panels ({n} scorable coded labels)", "", "| arm | Recall@5 (95% CI) | MRR |", "|---|---|---|"]
    for a in arms:
        p, lo, hi = wilson(sum(hits[a]), n); L.append(f"| {a} | {100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f}) | {sum(rr[a])/n:.3f} |")
    L += ["", "Scoring identical for all arms: label counted when its key analyte was measured; hit = any of the first 5 entries matches the group keyword map (llm_zero_shot.SYN). Physician free text may need synonyms added to SYN — log any additions in the SAP."]
    open(os.path.join(R, "human_B1_result.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    {"a1": a1, "b1": b1}[sys.argv[1]](sys.argv[2])
