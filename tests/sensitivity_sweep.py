"""Sensitivity analysis of the fusion constants.

Every hand-set constant of the decision-fusion layer is perturbed one at a
time (x0.75, x0.9, x1.1, x1.25, clamped to its legal range) and the engine
battery is re-run. A ranking that flips on a 10-25 % nudge of one constant is
tuned, not robust; the report lists, per constant, how many expected
diagnoses leave their accepted rank. No dataset needed: the question is
"does the conclusion depend on the exact value of this number?".

    python tests/sensitivity_sweep.py            # all constants
    python tests/sensitivity_sweep.py --quick    # +-25 % only
"""
from __future__ import annotations
import argparse
import os
import sys
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.disable(logging.CRITICAL)

import analyse_gidlines as ag  # noqa: E402
import engine_battery as B  # noqa: E402

# (name, legal_min, legal_max)
CONSTANTS = [
    ("RED_FLAG_RULE_VOTE", 0.3, 0.95), ("RED_FLAG_FLOOR_FRACTION", 0.3, 0.95), ("MAX_DISCORD_SHRINK", 0.0, 0.9),
    ("SINGLE_SOURCE_DISCOUNT", 0.3, 1.0), ("RULE_ABSTAIN_BELOW", 0.0, 0.3), ("DEFINITIONAL_FINDING_SCORE", 0.4, 0.95),
    ("GUIDELINE_ANCHOR_RULE_SCORE", 0.6, 0.99), ("GUIDELINE_ANCHOR_MIN_WEIGHT_SHARE", 0.35, 1.0),
    ("_TAK_SHART_SCREENING_FACTOR", 0.05, 1.0), ("PATHOGEN_MARKER_MIN_SPECIFICITY", 0.2, 1.0),
    ("DECISIVE_DIAGNOSTIC_MIN_SPECIFICITY", 0.3, 1.0),
]
WEIGHT_KEYS = ["rule_engine", "bayesian", "fuzzy", "knowledge_graph", "risk_models"]


def _run_battery(engine, D):
    misses = []
    for name, obs, pt, exp, max_rank in B.CASES:
        o = B.mk(obs)
        try:
            der = D.compute(o, pt).to_dict()["results"]
            derived = {k: {"value": v["value"], "unit": v["unit"]} for k, v in der.items()}
        except Exception:
            derived = {}
        diff = engine.interpret(o, derived, pt).to_dict()["differential_diagnosis"]
        hits = [x["rank"] for x in diff if x["disease_id"] in exp]
        if not hits or hits[0] > max_rank:
            misses.append(name)
    return misses


def main(quick: bool = False) -> int:
    import calcu
    D = calcu.DerivedFeatureEngine(os.path.join(ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json"))
    engine = ag.ClinicalRuleEngine()
    factors = (0.75, 1.25) if quick else (0.75, 0.9, 1.1, 1.25)
    base = _run_battery(engine, D)
    print(f"baseline misses: {len(base)} {base}")
    total_flips = 0
    rows = []
    for name, lo, hi in CONSTANTS:
        orig = getattr(ag, name)
        worst = 0
        detail = []
        for f in factors:
            val = min(hi, max(lo, orig * f))
            if abs(val - orig) < 1e-12:
                continue
            setattr(ag, name, val)
            engine._expression_cache.clear() if hasattr(engine, "_expression_cache") else None
            misses = _run_battery(engine, D)
            new = sorted(set(misses) - set(base))
            worst = max(worst, len(new))
            if new:
                detail.append(f"x{f:g}->{val:.3g}: {new}")
        setattr(ag, name, orig)
        total_flips += worst
        rows.append((name, orig, worst, detail))
        print(f"{name:<38} base={orig:<6g} worst new misses={worst}  {'; '.join(detail)}")
    # model weights: shift 25 % of one layer's weight onto the others
    for k in WEIGHT_KEYS:
        orig = dict(ag.MODEL_WEIGHTS)
        for f in factors:
            w = dict(orig)
            w[k] = orig[k] * f
            s = sum(w.values())
            for kk in w:
                w[kk] = w[kk] / s
            ag.MODEL_WEIGHTS.clear(); ag.MODEL_WEIGHTS.update(w)
            ag.LAYER_RELIABILITY.clear(); ag.LAYER_RELIABILITY.update({m: min(0.95, ww / 0.35) for m, ww in w.items()})
            misses = _run_battery(engine, D)
            new = sorted(set(misses) - set(base))
            if new:
                total_flips += len(new)
                print(f"MODEL_WEIGHTS[{k}] x{f:g}: new misses {new}")
        ag.MODEL_WEIGHTS.clear(); ag.MODEL_WEIGHTS.update(orig)
        ag.LAYER_RELIABILITY.clear(); ag.LAYER_RELIABILITY.update({m: min(0.95, ww / 0.35) for m, ww in orig.items()})
    print(f"\nTOTAL rank flips across all perturbations: {total_flips}")
    print("Interpretation: 0 = conclusions do not hinge on the exact value of any single constant "
          "(within +-25 %). Each flip names a case whose ranking is constant-sensitive.")
    return total_flips


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if main(a.quick) == 0 else 1)
