# -*- coding: utf-8 -*-
"""
Run Hemoglyph and the pre-specified comparator configurations on a cohort
(eval/results/cohort.jsonl from build_cohort.py, or any JSONL with the same keys).

Configurations (all use identical inputs; nothing is tuned on the cohort):
  full          Hemoglyph as shipped.
  rule_only     HEMOGLYPH_DISABLE_LAYERS=bayesian,fuzzy,knowledge_graph,risk_models
  naive_bayes   cluster discounting removed (WITHIN=CROSS=1.0): classical
                independence-assuming LR multiplication inside the Bayesian layer.
  mean_fusion   same five layer votes as 'full' but combined by a plain
                profile-weighted mean (no weight-share scaling, discord shrink,
                red-flag floor, anchor or Yager); re-ranked by that mean.
                Implemented post hoc from `ensemble_votes`, so it is an exact
                ablation of the combiner only.
Per case the differential (disease_id, rank, probability, belief,
plausibility, conflict, evidence_state, ensemble_votes) is stored for every
configuration, plus latency.  Results are written incrementally so a long run
can be resumed (--resume).

Usage:
  python eval/mimic/run_retrospective.py --cohort eval/results/cohort.jsonl --out eval/results/results.jsonl
"""
from __future__ import annotations
import argparse, json, os, sys, time, logging
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
logging.disable(logging.CRITICAL)
import analyse_gidlines as ag
import calcu

CONFIGS = ["full", "rule_only", "naive_bayes", "mean_fusion"]
_W = ag.MODEL_WEIGHTS

def mean_fusion_rerank(diff):
    """Plain weighted mean of the layer votes that participated (vote > 0 or rule >= abstain)."""
    out = []
    for d in diff:
        votes = d.get("ensemble_votes") or {}
        num = den = 0.0
        for layer, v in votes.items():
            w = _W.get(layer, 0.0)
            if layer == "rule_engine" and v < ag.RULE_ABSTAIN_BELOW: continue
            if layer != "rule_engine" and v <= 0.0: continue
            num += w * v; den += w
        out.append((num / den if den else 0.0, d))
    out.sort(key=lambda x: -x[0])
    return [{**d, "rank": i + 1, "probability": p, "fusion": "mean"} for i, (p, d) in enumerate(out)]

def slim(x):
    return {k: x.get(k) for k in ("disease_id", "rank", "probability", "belief", "plausibility", "conflict",
                                  "confidence", "evidence_state", "ensemble_votes", "weight_profile")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--resume", action="store_true"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    done = set()
    if a.resume and os.path.exists(a.out):
        for line in open(a.out, encoding="utf-8"):
            try: done.add(json.loads(line)["hadm_id"])
            except Exception: pass
    E = ag.ClinicalRuleEngine()
    E._reasoner.max_differential = 40  # evaluation: do not truncate the ranked list
    D = calcu.DerivedFeatureEngine(os.path.join(ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json"))
    fh = open(a.out, "a", encoding="utf-8")
    n = 0; t_start = time.time()
    for line in open(a.cohort, encoding="utf-8"):
        c = json.loads(line)
        if c["hadm_id"] in done: continue
        if a.limit and n >= a.limit: break
        obs = {k: {"value": v[0], "unit": v[1]} for k, v in c["labs"].items()}
        pt = {"age_years": c["age"], "sex_at_birth": c["sex"]}
        try:
            der = D.compute(obs, pt).to_dict()["results"]
            derived = {k: {"value": v["value"], "unit": v["unit"]} for k, v in der.items()}
        except Exception:
            derived = {}
        rec = {"hadm_id": c["hadm_id"], "group": c["group"], "icd_code": c["icd_code"], "n_labs": len(obs), "results": {}}
        for cfg in CONFIGS:
            os.environ.pop("HEMOGLYPH_DISABLE_LAYERS", None)
            BN = ag.ClinicalBayesianNetwork
            w_in, w_x = BN.WITHIN_CLUSTER_SECONDARY_WEIGHT, BN.CROSS_CLUSTER_WEIGHT
            if cfg == "rule_only":
                os.environ["HEMOGLYPH_DISABLE_LAYERS"] = "bayesian,fuzzy,knowledge_graph,risk_models"
            if cfg == "naive_bayes":
                BN.WITHIN_CLUSTER_SECONDARY_WEIGHT = 1.0; BN.CROSS_CLUSTER_WEIGHT = 1.0
            t = time.time()
            try:
                if cfg == "mean_fusion":
                    diff = rec["results"]["full"]["differential"]      # reuse full votes
                    diff = mean_fusion_rerank(diff)
                else:
                    d = E.interpret(obs, derived, pt).to_dict()
                    diff = d["differential_diagnosis"]
                rec["results"][cfg] = {"ms": (time.time() - t) * 1000, "differential": [slim(x) for x in diff[: a.top]] if cfg != "mean_fusion" else diff[: a.top]}
            except Exception as ex:
                rec["results"][cfg] = {"error": repr(ex)[:300], "differential": []}
            finally:
                BN.WITHIN_CLUSTER_SECONDARY_WEIGHT, BN.CROSS_CLUSTER_WEIGHT = w_in, w_x
                os.environ.pop("HEMOGLYPH_DISABLE_LAYERS", None)
        fh.write(json.dumps(rec) + "\n"); fh.flush(); n += 1
        if n % 50 == 0:
            el = time.time() - t_start
            print(f"{n} cases, {el/n:.2f} s/case")
    print("done", n, "cases ->", a.out)

if __name__ == "__main__":
    main()
