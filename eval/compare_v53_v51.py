"""Compare v5.3 (registry 13.3.0) labs-only eICU per-stay output with the frozen v5.1 baseline.

Usage: python3 eval/compare_v53_v51.py <v53_per_stay.json[.gz]> [<v51_per_stay.json[.gz]>]
Reports: recall@1/3/5 for both, per-sex recall@5, number of stays whose top-5 changed, and the
per-disease-group recall@5 deltas (female-male gap before/after) for SAP Amendment 12 H1/H2.
"""
import gzip, json, sys
from collections import defaultdict

def load(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt") as f:
        d = json.load(f)
    return d["per_stay"] if isinstance(d, dict) and "per_stay" in d else d

def hit(st, k):
    gr = st.get("gr") or {}
    return any(0 < (gr.get(g) or 0) <= k for g in (st.get("coded") or []))

def summarise(rows):
    n = len(rows)
    out = {f"r@{k}": 100.0 * sum(hit(s, k) for s in rows) / n for k in (1, 3, 5)}
    for sx in ("male", "female"):
        sub = [s for s in rows if (s.get("sex") or "").lower().startswith(sx[0])]
        out[f"r@5_{sx}"] = 100.0 * sum(hit(s, 5) for s in sub) / max(1, len(sub))
        out[f"n_{sx}"] = len(sub)
    out["n"] = n
    return out

def by_group(rows):
    acc = defaultdict(lambda: {"male": [0, 0], "female": [0, 0]})
    for s in rows:
        sx = (s.get("sex") or "").lower()
        sx = "male" if sx.startswith("m") else "female" if sx.startswith("f") else None
        if not sx:
            continue
        gr = s.get("gr") or {}
        for g in set(s.get("coded") or []):
            acc[g][sx][1] += 1
            acc[g][sx][0] += int(0 < (gr.get(g) or 0) <= 5)
    return acc

def main():
    a = load(sys.argv[1])
    b = load(sys.argv[2]) if len(sys.argv) > 2 else load("eval/results/run_20261023_v5/eicu_per_stay_v5_1.json.gz")
    sa, sb = summarise(a), summarise(b)
    print("metric            v5.1      v5.3     delta")
    for k in ("r@1", "r@3", "r@5", "r@5_male", "r@5_female"):
        print(f"{k:14s} {sb[k]:8.1f} {sa[k]:8.1f} {sa[k]-sb[k]:+8.1f}")
    gap_b = sb["r@5_male"] - sb["r@5_female"]
    gap_a = sa["r@5_male"] - sa["r@5_female"]
    print(f"sex gap (M-F) v5.1 {gap_b:+.1f}  v5.3 {gap_a:+.1f}   H1 (|gap|<=1.5): {'PASS' if abs(gap_a) <= 1.5 else 'FAIL'}")
    print(f"H2 (recall@5 drop <= 1.0 vs 63.7): {'PASS' if sa['r@5'] >= 62.7 else 'FAIL'}")
    ia = {s["stay"]: s for s in a}; ib = {s["stay"]: s for s in b}
    common = [k for k in ia if k in ib]
    changed = [k for k in common if [x[0] for x in (ia[k].get("top5") or [])[:5]] != [x[0] for x in (ib[k].get("top5") or [])[:5]]]
    gained = sum(hit(ia[k], 5) and not hit(ib[k], 5) for k in common)
    lost = sum(hit(ib[k], 5) and not hit(ia[k], 5) for k in common)
    print(f"stays common {len(common)}  top5 changed {len(changed)}  recall@5 gained {gained}  lost {lost}")
    ga, gb = by_group(a), by_group(b)
    print("\nper-group recall@5 (n>=20 per sex): group  F-M gap v5.1 -> v5.3")
    rows = []
    for g in ga:
        if g in gb and min(ga[g]["male"][1], ga[g]["female"][1]) >= 20:
            def gap(d):
                return 100 * d["female"][0] / d["female"][1] - 100 * d["male"][0] / d["male"][1]
            rows.append((g, gap(gb[g]), gap(ga[g])))
    for g, x, y in sorted(rows, key=lambda r: r[1]):
        print(f"  {g:32s} {x:+6.1f} -> {y:+6.1f}")

if __name__ == "__main__":
    main()
