"""Reviewer item B4 — component ablation of the frozen engine v7 / registry 14.1.0 on the eICU-CRD demo cohort
(2,314 stays, labs only, --encounter icu). Every arm uses the identical pipeline (eval_eicu.main) with ONE component
switched off or altered by environment variable / in-process monkey-patch; the engine file itself is NOT edited, so the
freeze manifest (FREEZE_v15) still describes the code under test.

    python3 eval/ablation/run_ablation.py <arm>       arms: see ARMS
    python3 eval/ablation/run_ablation.py --summarise  -> eval/results/eicu_demo/ABLATION_v7_full.md

Outputs per arm: eval/results/eicu_demo/per_stay_abl_<arm>.json.gz (stripped: stay, coded, labs, gr, gr2, gp) +
report_abl_<arm>.md. Full per-stay files are stripped after the run to respect the workspace budget.
"""
import os, sys, json, gzip, importlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
OUT = os.path.join(ROOT, "eval", "results", "eicu_demo")

ARMS = {
    "no_bayesian":   "Bayesian network layer disabled (HEMOGLYPH_DISABLE_LAYERS=bayesian)",
    "no_fuzzy":      "adaptive fuzzy layer disabled",
    "no_graph":      "knowledge-graph layer disabled",
    "no_risk":       "risk-model layer disabled",
    "no_rule":       "rule-engine vote disabled in fusion (registry rules AND expert-syndrome votes both enter through this channel)",
    "no_esl":        "expert syndrome layer returns no hits (registry rules intact)",
    "dempster":      "Theory-of-Evidence layer uses Dempster normalisation instead of Yager (conflict renormalised, not sent to ignorance)",
    "uniform_w":     "fusion weights uniform 0.20 x 5, all domain profiles collapsed to uniform",
    "no_shrink":     "discord shrinkage and single-source discount removed (MAX_DISCORD_SHRINK=0, SINGLE_SOURCE_DISCOUNT=1)",
    "anchor_only":   "registry restricted to the 272 manually curated guideline-anchored rules (32,911 AI-assisted rules non-executable)",
    "no_unverified": "28 rules with evidence_tier=unverified_source made non-executable",
    "w_rule_heavy":  "fusion weight sensitivity: rule_engine 0.55 / bayesian 0.15 / fuzzy 0.15 / graph 0.075 / risk 0.075 (all profiles)",
    "anchor_only_no_esl": "2x2 cell: registry restricted to 272 anchors AND expert syndrome layer off",
    "w_rule_light":  "fusion weight sensitivity: rule_engine 0.20 / bayesian 0.30 / fuzzy 0.25 / graph 0.125 / risk 0.125 (all profiles)",
}

def patch(arm, ag):
    if arm == "dempster":
        def _dempster(masses):
            if not masses: return 0.0, 1.0, 1.0, 0.0
            p_dt = p_nt = p_t = 1.0
            for (d2, n2, t2) in masses:
                tot = d2 + n2 + t2
                if tot <= 0: continue
                d2, n2, t2 = d2 / tot, n2 / tot, t2 / tot
                p_dt *= (d2 + t2); p_nt *= (n2 + t2); p_t *= t2
            d = max(0.0, p_dt - p_t); n = max(0.0, p_nt - p_t); k = max(0.0, 1.0 - d - n - p_t)
            s = d + n + p_t
            if s > 0: d, n, t = d / s, n / s, p_t / s
            else: d, n, t = 0.0, 0.0, 1.0
            return d, d + t, t, min(1.0, k)
        ag._yager_binary_combine = _dempster
    elif arm in ("no_esl", "anchor_only_no_esl"):
        ag._ExpertSyndromeLayer.evaluate = lambda self, observations, context=None: []
    elif arm == "uniform_w":
        for m in ag.MODEL_WEIGHTS: ag.MODEL_WEIGHTS[m] = 0.20
        for prof in ag.WEIGHT_PROFILES.values():
            for m in prof: prof[m] = 0.20
        ag.LAYER_RELIABILITY.clear(); ag.LAYER_RELIABILITY.update({m: min(0.95, 0.20 / 0.35) for m in ag.MODEL_WEIGHTS})
    elif arm in ("w_rule_heavy", "w_rule_light"):
        W = {"w_rule_heavy": {"rule_engine": 0.55, "bayesian": 0.15, "fuzzy": 0.15, "knowledge_graph": 0.075, "risk_models": 0.075},
             "w_rule_light": {"rule_engine": 0.20, "bayesian": 0.30, "fuzzy": 0.25, "knowledge_graph": 0.125, "risk_models": 0.125}}[arm]
        for m in ag.MODEL_WEIGHTS: ag.MODEL_WEIGHTS[m] = W[m]
        for prof in ag.WEIGHT_PROFILES.values():
            for m in prof: prof[m] = W[m]
        ag.LAYER_RELIABILITY.clear(); ag.LAYER_RELIABILITY.update({m: min(0.95, w / 0.35) for m, w in W.items()})
    elif arm == "no_shrink":
        ag.MAX_DISCORD_SHRINK = 0.0; ag.SINGLE_SOURCE_DISCOUNT = 1.0

def run(arm):
    assert arm in ARMS, arm
    env = {"no_bayesian": "bayesian", "no_fuzzy": "fuzzy", "no_graph": "knowledge_graph", "no_risk": "risk_models", "no_rule": "rule_engine"}
    if arm in env: os.environ["HEMOGLYPH_DISABLE_LAYERS"] = env[arm]
    reg = {"anchor_only": "REGISTRY_ANCHOR_ONLY.json.br", "anchor_only_no_esl": "REGISTRY_ANCHOR_ONLY.json.br", "no_unverified": "REGISTRY_NO_UNVERIFIED.json.br"}
    if arm in reg: os.environ["HEMOGLYPH_REGISTRY_OVERRIDE"] = os.path.join(ROOT, "eval", "ablation", reg[arm])
    import analyse_gidlines as ag
    patch(arm, ag)
    import eval_eicu
    sys.argv = ["eval_eicu.py", "--encounter", "icu", "--suffix", f"_abl_{arm}"]
    eval_eicu.main()
    for cand in (f"per_stay_abl_{arm}.json.gz", f"per_stay_abl_{arm}.json"):
        p = os.path.join(OUT, cand)
        if os.path.exists(p):
            rows = json.load(gzip.open(p, "rt") if p.endswith(".gz") else open(p))
            slim = [{k: r.get(k) for k in ("stay", "coded", "labs", "gr", "gr2", "gp", "top5")} for r in rows]
            json.dump(slim, gzip.open(os.path.join(OUT, f"per_stay_abl_{arm}.json.gz"), "wt"))
            if not p.endswith(".gz"): os.remove(p)
            break
    open(os.path.join(OUT, f"ABL_{arm}.done"), "w").write(ARMS[arm])

def summarise():
    sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
    from panel_supported_metric import score
    from eval_eicu import GROUPS
    def load(p):
        rows = json.load(gzip.open(p, "rt")); return {r["stay"]: r for r in rows}
    base = load(os.path.join(OUT, "per_stay_v7.json.gz"))
    def metrics(F):
        ev = lambda r, g: any(k in r["labs"] for k in GROUPS[g][2])
        n = h = {}; res = {}
        for tier in ("gr", "gr2"):
            cnt = {k: 0 for k in (3, 5, 10)}; tot = 0
            for r in F.values():
                for g in r["coded"]:
                    if g not in GROUPS or not ev(r, g): continue
                    tot += 1; rk = r[tier].get(g, 999)
                    for k in cnt: cnt[k] += rk <= k
            res[tier] = {k: 100 * cnt[k] / tot for k in cnt}; res["n"] = tot
        ps, ex, un, mi = score(list(F.values()), "gr"); res["ps5"] = 100 * ps[5][0] / ps[5][1]; res["ps10"] = 100 * ps[10][0] / ps[10][1]
        return res
    def pg(F):
        d = {}
        for r in F.values():
            for g in r["coded"]:
                if g not in GROUPS or not any(k in r["labs"] for k in GROUPS[g][2]): continue
                a = d.setdefault(g, [0, 0]); a[0] += 1; a[1] += r["gr"].get(g, 999) <= 5
        return d
    mb = metrics(base); pb = pg(base)
    L = ["# Component ablation — engine v7 / registry 14.1.0, eICU-CRD demo (2,314 stays, labs only)", "",
         "Each arm switches off or alters exactly one component (environment variable or in-process patch; engine file unchanged). Same stays, same label map, same scorer. Flat = specific-diagnosis tier; PS = panel-supported subset (secondary, post hoc; n = 1,460).", "",
         "| arm | n labels | flat @3 | flat @5 | flat @10 | Δ@5 vs full | two-tier @5 | PS @5 | PS @10 | stays with top-5 identical to full |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
         f"| **full v7 (reference)** | {mb['n']} | {mb['gr'][3]:.1f} | {mb['gr'][5]:.1f} | {mb['gr'][10]:.1f} | — | {mb['gr2'][5]:.1f} | {mb['ps5']:.1f} | {mb['ps10']:.1f} | — |"]
    rows_pg = {}
    for arm in ARMS:
        p = os.path.join(OUT, f"per_stay_abl_{arm}.json.gz")
        if not os.path.exists(p): L.append(f"| {arm} | not run | | | | | | | | |"); continue
        F = load(p)
        for s_, r_ in F.items():
            if "vals" not in r_ and s_ in base:
                for k_, v_ in base[s_].items():
                    if k_ not in ("gr", "gr2", "gr3", "gp", "top5"): r_.setdefault(k_, v_)
        m = metrics(F); same = sum(1 for s in F if s in base and [x[0] for x in (F[s].get('top5') or [])] == [x[0] for x in (base[s].get('top5') or [])])
        L.append(f"| {arm} | {m['n']} | {m['gr'][3]:.1f} | {m['gr'][5]:.1f} | {m['gr'][10]:.1f} | {m['gr'][5]-mb['gr'][5]:+.1f} | {m['gr2'][5]:.1f} | {m['ps5']:.1f} | {m['ps10']:.1f} | {100*same/len(F):.0f}% |")
        rows_pg[arm] = pg(F)
    L += ["", "## Arms", ""] + [f"- `{a}`: {d}" for a, d in ARMS.items()]
    if rows_pg:
        arms = list(rows_pg); L += ["", "## Per-group flat recall@5 (groups with n ≥ 20)", "", "| group | n | full | " + " | ".join(arms) + " |", "|---|---:|---:|" + "---:|" * len(arms)]
        for g, (n, h) in sorted(pb.items(), key=lambda x: -x[1][0]):
            if n < 20: continue
            L.append(f"| {g} | {n} | {100*h/n:.0f} | " + " | ".join(f"{100*rows_pg[a].get(g,[1,0])[1]/max(1,rows_pg[a].get(g,[1,0])[0]):.0f}" for a in arms) + " |")
    open(os.path.join(OUT, "ABLATION_v7_full.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__":
    if sys.argv[1] == "--summarise": summarise()
    else: run(sys.argv[1])
