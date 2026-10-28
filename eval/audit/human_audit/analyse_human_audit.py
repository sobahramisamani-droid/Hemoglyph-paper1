"""Pre-registered analysis for Supplementary Note 19 (human concordance audit).

Written and committed before any rater verdict exists. Standard library only.

Usage
  python3 analyse_human_audit.py rater1.csv rater2.csv [--consensus consensus.csv] [--out result.json]

Each rater CSV is the distributed form (`human_audit_sample_100.csv` or the CSV export of the
.xlsx form) with the verdict column filled in with C, D or U. The optional consensus CSV has the
same layout and carries the verdict agreed after discussion/adjudication; when it is absent only
the per-rater and inter-rater figures are produced and the primary outcome is left empty.

Outputs, exactly as pre-specified in PROTOCOL_Note19.md:
  primary   discordance among resolvable rules D/(C+D), overall and per stratum, Wilson 95% CI
  secondary unresolvable proportion U/n; Cohen's kappa between raters (3-level and binary
            resolvable/unresolvable); agreement of the consensus (or each rater) with the sealed AI
            verdict, with kappa; per-item table
The AI verdict is taken from `ai_verdicts_sealed.json`: the last concordance label when one exists,
otherwise the ledger status (quote_verified -> C, discordant_* -> D, anything else -> U).
Nothing here reads the rater files before they are passed on the command line.
"""
import argparse
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "human_audit_sample_100.csv")
SEALED = os.path.join(HERE, "ai_verdicts_sealed.json")
VALID = {"C", "D", "U"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def kappa(a, b):
    assert len(a) == len(b) and a
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def kappa_se(a, b):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    cats = sorted(set(a) | set(b))
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe == 1.0 or n == 0:
        return float("nan")
    return math.sqrt(po * (1 - po) / (n * (1 - pe) ** 2))


def read_form(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    vcol = next((c for c in rows[0] if c.lower().startswith("verdict")), None)
    if vcol is None:
        sys.exit(f"{path}: no verdict column")
    out = {}
    for r in rows:
        v = (r.get(vcol) or "").strip().upper()[:1]
        if v not in VALID:
            sys.exit(f"{path}: item {r.get('item')} has verdict {r.get(vcol)!r}; every item must be C, D or U")
        out[r["rule_id"]] = v
    return out


def ai_verdict(entry):
    if entry.get("concordance"):
        lab = entry["concordance"][-1]["label"].upper()
        return {"CONCORDANT": "C", "DISCORDANT": "D"}.get(lab, "U")
    st = entry.get("verification_status", "")
    if st == "quote_verified":
        return "C"
    if st.startswith("discordant"):
        return "D"
    return "U"


def summarise(verdicts, items, label):
    res = {"label": label, "strata": {}}
    for stratum in ["all"] + sorted({it["stratum"] for it in items}):
        sub = [verdicts[it["rule_id"]] for it in items if stratum == "all" or it["stratum"] == stratum]
        n = len(sub)
        c, d, u = sub.count("C"), sub.count("D"), sub.count("U")
        res["strata"][stratum] = {
            "n": n, "C": c, "D": d, "U": u,
            "unresolvable_prop": u / n if n else None,
            "unresolvable_ci": wilson(u, n),
            "discordance_among_resolvable": d / (c + d) if (c + d) else None,
            "discordance_ci": wilson(d, c + d) if (c + d) else (None, None),
            "resolvable_n": c + d,
        }
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rater1")
    ap.add_argument("rater2", nargs="?")
    ap.add_argument("--consensus")
    ap.add_argument("--out", default=os.path.join(HERE, "RESULT_human_audit.json"))
    a = ap.parse_args()

    with open(SAMPLE, newline="", encoding="utf-8-sig") as fh:
        items = list(csv.DictReader(fh))
    ids = [it["rule_id"] for it in items]
    sealed = json.load(open(SEALED, encoding="utf-8"))
    ai = {rid: ai_verdict(sealed[rid]) for rid in ids}

    raters = {"rater1": read_form(a.rater1)}
    if a.rater2:
        raters["rater2"] = read_form(a.rater2)
    cons = read_form(a.consensus) if a.consensus else None
    for name, v in list(raters.items()) + ([("consensus", cons)] if cons else []):
        missing = [i for i in ids if i not in v]
        if missing:
            sys.exit(f"{name}: {len(missing)} sampled rules missing, e.g. {missing[:3]}")

    out = {"n_items": len(ids), "per_rater": {}, "inter_rater": None, "primary": None, "vs_ai": {}}
    for name, v in raters.items():
        out["per_rater"][name] = summarise(v, items, name)
    if len(raters) == 2:
        a1 = [raters["rater1"][i] for i in ids]
        a2 = [raters["rater2"][i] for i in ids]
        b1 = ["R" if x != "U" else "U" for x in a1]
        b2 = ["R" if x != "U" else "U" for x in a2]
        out["inter_rater"] = {
            "kappa_3level": kappa(a1, a2), "kappa_3level_se": kappa_se(a1, a2),
            "kappa_resolvable_binary": kappa(b1, b2), "kappa_resolvable_binary_se": kappa_se(b1, b2),
            "raw_agreement": sum(x == y for x, y in zip(a1, a2)) / len(ids),
            "disagreements": [i for i, x, y in zip(ids, a1, a2) if x != y],
        }
    if cons:
        out["primary"] = summarise(cons, items, "consensus")
    for name, v in list(raters.items()) + ([("consensus", cons)] if cons else []):
        h = [v[i] for i in ids]
        g = [ai[i] for i in ids]
        out["vs_ai"][name] = {
            "raw_agreement": sum(x == y for x, y in zip(h, g)) / len(ids),
            "kappa_3level": kappa(h, g),
            "human_resolved_ai_unresolved": sum(1 for x, y in zip(h, g) if x != "U" and y == "U"),
            "ai_resolved_human_unresolved": sum(1 for x, y in zip(h, g) if x == "U" and y != "U"),
            "human_D_ai_not_D": sum(1 for x, y in zip(h, g) if x == "D" and y != "D"),
        }
    out["items"] = [
        {"item": it["item"], "rule_id": it["rule_id"], "stratum": it["stratum"], "ai": ai[it["rule_id"]],
         **{k: v[it["rule_id"]] for k, v in raters.items()},
         **({"consensus": cons[it["rule_id"]]} if cons else {})}
        for it in items
    ]
    # Pre-specified interpretation flags (PROTOCOL_Note19.md).
    src = out["primary"] or out["per_rater"]["rater1"]
    allrow = src["strata"]["all"]
    out["interpretation"] = {
        "unresolvable_ge_80pct_confirms_locator_limit": allrow["unresolvable_prop"] is not None and allrow["unresolvable_prop"] >= 0.80,
        "unresolvable_le_60pct_ai_underreported_resolvability": allrow["unresolvable_prop"] is not None and allrow["unresolvable_prop"] <= 0.60,
        "discordance_ci_excludes_ai_7_5pct": (allrow["discordance_ci"][0] is not None and not (allrow["discordance_ci"][0] <= 0.075 <= allrow["discordance_ci"][1])),
        "kappa_reportable_(>=50 double-rated)": len(raters) == 2 and len(ids) >= 50,
    }
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"items {len(ids)}")
    for name, s in out["per_rater"].items():
        r = s["strata"]["all"]
        print(f"{name}: C {r['C']} D {r['D']} U {r['U']}  unresolvable {r['unresolvable_prop']:.3f}  "
              f"discordance among resolvable {r['discordance_among_resolvable']}")
    if out["inter_rater"]:
        k = out["inter_rater"]
        print(f"inter-rater kappa 3-level {k['kappa_3level']:.3f} (SE {k['kappa_3level_se']:.3f}); "
              f"binary {k['kappa_resolvable_binary']:.3f}")
    if out["primary"]:
        r = out["primary"]["strata"]["all"]
        print(f"PRIMARY consensus discordance D/(C+D) = {r['D']}/{r['resolvable_n']} "
              f"CI {r['discordance_ci'][0]:.3f}-{r['discordance_ci'][1]:.3f}; unresolvable {r['U']}/{r['n']}")
    for name, v in out["vs_ai"].items():
        print(f"{name} vs sealed AI: agreement {v['raw_agreement']:.2f} kappa {v['kappa_3level']:.3f}; "
              f"human resolved/AI not {v['human_resolved_ai_unresolved']}, AI resolved/human not {v['ai_resolved_human_unresolved']}")
    print("written", a.out)


if __name__ == "__main__":
    main()
