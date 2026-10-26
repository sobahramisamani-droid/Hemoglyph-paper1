"""Unit-twin fuzz: every HARD-battery case is re-expressed in alternative
allowed units (registry `measurement.allowed_units`) and must produce the
same top-1 disease, the same expert-syndrome set, and |delta p| <= 0.05.

Usage: python tests/unit_twin_fuzz.py [--verbose]
"""
from __future__ import annotations
import os, sys, argparse, logging, itertools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
logging.disable(logging.CRITICAL)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--battery", default="hard_battery", help="tests module exposing CASES (hard_battery | hard_battery2)")
    ap.add_argument("--verbose", action="store_true"); a = ap.parse_args()
    import analyse_gidlines as ag
    from calcu import convert_unit, normalize_unit
    import importlib
    CASES = importlib.import_module(a.battery).CASES
    E = ag.ClinicalRuleEngine(); F = E.registry.features
    n_ok = 0; fails = []; n_conv = 0; skipped = 0
    for name, obs, pt, *_ in CASES:
        base = {f: {"value": v, "unit": u} for f, (v, u) in obs.items()}
        twin = {}; changed = []
        for f, (v, u) in obs.items():
            meta = F.get(f) or {}
            allowed = list((meta.get("measurement") or {}).get("allowed_units") or []) + list(((meta.get("units") or {}).get("accepted")) or [])
            alt = None
            for cand in allowed:
                if normalize_unit(cand) == normalize_unit(u):
                    continue
                try:
                    nv = convert_unit(v, u, cand, f)
                except Exception:
                    continue
                if nv is not None and abs(nv) > 1e-9:
                    # round-trip must hold, else the pair is a label alias not a conversion
                    try:
                        back = convert_unit(nv, cand, u, f)
                    except Exception:
                        continue
                    if abs(back - v) <= 1e-6 * max(1.0, abs(v)):
                        alt = (nv, cand); break
            if alt:
                twin[f] = {"value": round(alt[0], 6), "unit": alt[1]}; changed.append((f, u, alt[1])); n_conv += 1
            else:
                twin[f] = {"value": v, "unit": u}
        if not changed:
            skipped += 1; continue
        r1 = E.interpret(base, None, pt).to_dict(); r2 = E.interpret(twin, None, pt).to_dict()
        d1, d2 = r1["differential_diagnosis"], r2["differential_diagnosis"]
        s1 = {h["syndrome_id"] for h in r1["expert_syndromes"]}; s2 = {h["syndrome_id"] for h in r2["expert_syndromes"]}
        t1 = (d1[0]["disease_id"], d1[0]["probability"]) if d1 else (None, 0); t2 = (d2[0]["disease_id"], d2[0]["probability"]) if d2 else (None, 0)
        ok = t1[0] == t2[0] and abs(t1[1] - t2[1]) <= 0.05 and s1 == s2
        if ok:
            n_ok += 1
            if a.verbose: print(f"[ OK ] {name}  {changed}")
        else:
            fails.append(name)
            print(f"[FAIL] {name}\n        base={t1} twin={t2}\n        syn base={sorted(s1)} twin={sorted(s2)}\n        changed={changed}")
    tot = n_ok + len(fails)
    print(f"\nUNIT-TWIN SCORE {n_ok}/{tot} ({100*n_ok/max(tot,1):.1f}%)  analyte conversions exercised: {n_conv}; cases without convertible analyte: {skipped}")
    if fails: print("FAILS:", fails)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
