"""Perturbation fuzz: each HARD-battery case is replayed R times with
multiplicative analytical noise (default ±3 %, the typical total allowable
error of core chemistry/haematology analytes per CLIA/Ricos) on every
numeric analyte. Binary results (0/1) are left untouched.

Pass criterion per replicate: an acceptable id still within `max_rank`.
Reports per-case robustness and the global replicate pass rate.

Usage: python tests/perturbation_fuzz.py [--noise 0.03] [--reps 5] [--seed 1] [--verbose]
"""
from __future__ import annotations
import os, sys, argparse, logging, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
logging.disable(logging.CRITICAL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--battery", default="hard_battery", help="tests module exposing CASES (hard_battery | hard_battery2)")
    ap.add_argument("--noise", type=float, default=0.03)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    import analyse_gidlines as ag
    import importlib
    CASES = importlib.import_module(a.battery).CASES
    E = ag.ClinicalRuleEngine()
    rng = random.Random(a.seed)
    total = ok_total = 0; brittle = []
    for name, obs, pt, accept, max_rank in CASES:
        ok = 0
        for r in range(a.reps):
            payload = {}
            for f, (v, u) in obs.items():
                if u == "1" or v in (0, 1) and float(v).is_integer() and u in ("1", "{titer}"):
                    payload[f] = {"value": v, "unit": u}
                else:
                    payload[f] = {"value": v * (1 + rng.uniform(-a.noise, a.noise)), "unit": u}
            rep = E.interpret(payload, None, pt).to_dict()
            if accept == ["__QUIET__"]:
                rank = 0 if all(x["probability"] < 0.5 for x in rep["differential_diagnosis"]) else None
            elif any(str(x).startswith("!") for x in accept):
                neg = {x[1:] for x in accept if str(x).startswith("!")}
                bad = [x for x in rep["differential_diagnosis"][:max_rank] if x["disease_id"] in neg and x["probability"] >= 0.5]
                rank = 0 if not bad else None
            else:
                rank = next((x["rank"] for x in rep["differential_diagnosis"] if x["disease_id"] in set(accept)), None)
            good = rank is not None and rank <= max_rank
            ok += good
            if not good and a.verbose:
                print(f"   miss {name!r} rep{r}: top={[(x['disease_id'], round(x['probability'],2)) for x in rep['differential_diagnosis'][:3]]}")
        total += a.reps; ok_total += ok
        if ok < a.reps:
            brittle.append((name, ok))
            print(f"[BRITTLE] {name}: {ok}/{a.reps}")
    print(f"\nPERTURBATION ({a.noise*100:.0f}% noise, {a.reps} reps): replicates passed {ok_total}/{total} ({100*ok_total/total:.1f}%); "
          f"fully robust cases {len(CASES)-len(brittle)}/{len(CASES)}")
    return 0 if ok_total / total >= 0.95 else 1


if __name__ == "__main__":
    sys.exit(main())
