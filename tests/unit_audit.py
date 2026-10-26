"""Unit-conversion audit: for every registry feature, every pair of
(canonical, allowed/accepted) units must convert in both directions and
round-trip within 1e-6 relative. Prints unconvertible pairs grouped by analyte.

Usage: python tests/unit_audit.py [--verbose]
Exit 0 always (informational); the count is reported for tracking.
Known-unconvertible residue (2026-10-21): ck_mb U/L<->ng/mL (activity vs mass),
vWF / protein S U/L->% (assay-specific), PDW %->fL, "G/L" cell counts, ALT/AST
"uimt"/"U/mL", globulin U/L, ACR/PCR "ratio", reticulocytes 10^9/L->%.
"""
from __future__ import annotations
import os, sys, argparse, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verbose", action="store_true"); a = ap.parse_args()
    import analyse_gidlines as ag
    from calcu import convert_unit, normalize_unit
    E = ag.ClinicalRuleEngine(); F = E.registry.features
    n_pairs = 0; fails = []
    for fid, meta in F.items():
        meas = meta.get("measurement") or {}; units = meta.get("units") or {}
        canon = meas.get("canonical_unit") or units.get("canonical")
        if not canon:
            continue
        allowed = set(meas.get("allowed_units") or []) | set(units.get("accepted") or []) | set(units.get("common") or [])
        for u in allowed:
            if normalize_unit(u) == normalize_unit(canon):
                continue
            n_pairs += 1
            try:
                v = convert_unit(10.0, canon, u, fid)
                back = convert_unit(v, u, canon, fid) if v is not None else None
                ok = v is not None and back is not None and abs(back - 10.0) <= 1e-6 * 10.0
            except Exception as exc:
                ok = False; v = f"EXC {type(exc).__name__}"
            if not ok:
                fails.append((fid, canon, u, v))
            elif a.verbose:
                print(f"  ok  {fid}: 10 {canon} = {v:g} {u}")
    for fid, canon, u, v in fails:
        print(f"[FAIL] {fid}: {canon} -> {u}  ({v})")
    print(f"\nUNIT AUDIT: {n_pairs} pairs, {len(fails)} unconvertible ({100*(n_pairs-len(fails))/max(n_pairs,1):.1f}% convertible)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
