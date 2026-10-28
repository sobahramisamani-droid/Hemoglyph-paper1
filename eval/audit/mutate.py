"""Part 1 (PROTOCOL_AUDIT.md): seeded-defect validation of the static audit.

Seeds = executable rules with provenance.verified_quote or status curated_* that have >= 1 numeric leaf.
For every seed and every operator M1..M8 one mutant is produced (when the operator applies); detectors from
audit.py (frozen at commit 9c87645) are run on a registry copy in which ONLY that one rule is mutated, so that
entity-level context (sibling rules) is the real one. Specificity: detectors run on the unmutated seeds.
Writes mutation_results.json (compact) and prints the recall table.
"""
import json, copy, collections, random, sys, os, brotli
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import Audit, leaves, num, load_br, UBIQUITOUS, FINDING_ENTITY, HG, CONV, SIGNED

RNG = random.Random(20261028)
MASS_MOLAR = {"mg/dL": "mmol/L", "mmol/L": "mg/dL", "umol/L": "mg/dL", "µmol/L": "mg/dL", "g/dL": "g/L", "g/L": "g/dL", "ng/mL": "nmol/L", "nmol/L": "ng/mL", "ug/dL": "ng/mL", "pg/mL": "pmol/L", "pmol/L": "pg/mL"}

def numeric_leaf_paths(e, path=()):
    if not isinstance(e, dict): return []
    if "feature_id" in e: return [path] if num(e.get("value")) is not None else []
    out = []
    for k in ("all", "any", "none"):
        if k in e:
            for i, c in enumerate(e[k]): out += numeric_leaf_paths(c, path + (k, i))
    if "n_of" in e:
        for i, c in enumerate(e["n_of"].get("conditions", [])): out += numeric_leaf_paths(c, path + ("n_of", "conditions", i))
    return out

def get(e, path):
    for p in path: e = e[p]
    return e

sources_meta = {}
def apply(op, rule, leaf, aud, sources):
    """return (mutant_rule, expected_detector or None, note) or None if operator not applicable"""
    r = copy.deepcopy(rule); l = get(r["expression"], leaf); v = float(l["value"]); fid = l["feature_id"]; dis = r["disease_id"]
    if op == "M1":
        if r.get("rule_type") not in ("staging_severity", "diagnostic_criterion"):
            r["rule_type"] = "diagnostic_criterion"
        f = 1.5 if l.get("operator", ">").startswith(">") else 0.5
        scr = aud.scr.get((dis, fid), set())
        if not scr: return None
        s = sorted(scr)[0]; l["value"] = round(s * f, 6)
        # any other numeric leaves must also be arithmetic for R7 to fire; keep single-leaf seeds only
        if len(numeric_leaf_paths(r["expression"])) > 1: return None
        return r, "r7", f"{fid} {s}->{l['value']}"
    if op == "M2":
        l["value"] = round(v * (1.1 if RNG.random() < 0.5 else 0.9), 6); return r, None, f"{fid} {v}->{l['value']}"
    if op == "M3":
        o = l.get("operator")
        if o not in ("<", "<=", ">", ">="): return None
        l["operator"] = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[o]; return r, "dir", f"{fid} {o}->{l['operator']}"
    if op == "M4":
        u = l.get("unit")
        if not u or u not in MASS_MOLAR: return None
        nu = MASS_MOLAR[u]
        if (fid, nu) not in CONV and (fid, nu.replace("u", "µ")) not in CONV and nu == aud.units_ok(fid)[1]: return None
        l["unit"] = nu; return r, "unit", f"{fid} {u}->{nu}"
    if op == "M5":
        ages = set((r.get("population") or {}).get("age_groups") or [])
        if ages & {"neonate", "infant"}: return None
        nlo, nhi, _ = aud.ref(fid, "neonate")
        if nlo is None: return None
        r.setdefault("population", {})["age_groups"] = sorted(ages | {"neonate", "infant"}); return r, "pop", f"{fid} +neonate"
    if op == "M6":
        if aud.kind.get(dis) != "clinical_entity" or FINDING_ENTITY.search(dis) or r.get("rule_type") == "exclusion_criterion": return None
        r["expression"] = {"feature_id": "c_reactive_protein", "operator": ">", "value": 10.0, "unit": "mg/L", "weight": l.get("weight", 2.0)}
        return r, "r2a", f"{fid}->c_reactive_protein"
    if op == "M7":
        if any(s in fid for s in SIGNED): return None
        l["value"] = -abs(v) if v else -1.0; return r, "r9", f"{fid} {v}->{l['value']}"
    if op == "M8":
        # non-circular: pick a source uniformly at random whose own scope maps to a different domain set than the
        # original source's scope (mapping only, no entity logic); the detector is NOT consulted here
        from audit import SCOPE2DOM
        def doms(sid):
            sc = sources_meta.get(sid) or {}; return frozenset(SCOPE2DOM[w] for w in [str(x).lower().replace(" ", "_") for x in (sc.get("scope") or [])] if w in SCOPE2DOM) - {"*"}
        own = doms((rule.get("source_ids") or [None])[0])
        cands = [s for s in sources if doms(s) and own and not (doms(s) & own)]
        if not cands: return None
        r["source_ids"] = [RNG.choice(sorted(cands))]; return r, "src", f"source->{r['source_ids'][0]}"
    return None

def main():
    reg_path = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".br") else os.path.join(HG, "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    print("registry:", reg_path); reg = load_br(reg_path); feats = load_br(os.path.join(HG, "HEMOGLYPH_FEATURE_REGISTRY.json.br"))["features"]
    aud = Audit(reg, feats); R = reg["rules"]; sources = list(reg["guideline_sources"]); sources_meta.update(reg["guideline_sources"])
    seeds = [rid for rid, r in R.items() if r.get("executable") and not rid.startswith("co_") and
             (str(r.get("status", "")).startswith("curated") or (r.get("provenance") or {}).get("verified_quote")) and numeric_leaf_paths(r.get("expression"))]
    print("seeds", len(seeds))
    # specificity on unmutated seeds
    base = {rid: aud.run_rule(rid, R[rid]) for rid in seeds}
    fp = {rid: f for rid, f in base.items() if f}
    res = {"seeds": len(seeds), "baseline_flags": fp, "mutants": []}
    tab = collections.defaultdict(lambda: [0, 0, 0, collections.Counter()])  # applicable, detected_expected, detected_any
    for rid in seeds:
        rule = R[rid]; paths = numeric_leaf_paths(rule["expression"]); leaf = paths[0]
        for op in ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"):
            m = apply(op, rule, leaf, aud, sources)
            if m is None: continue
            mr, expected, note = m
            orig = R[rid]; R[rid] = mr
            # rebuild cached entity context for this rule's entity only if the mutation changed it (M1/M3 touch dirs/scr)
            a2 = aud if op not in ("M1", "M3") else Audit(reg, feats)
            flags = a2.run_rule(rid, mr); R[rid] = orig
            new = {d: w for d, w in flags.items() if d not in base[rid]}   # only flags not already present on the seed
            t = tab[op]; t[0] += 1
            det_exp = expected is not None and expected in new; det_any = bool(new)
            t[1] += det_exp; t[2] += det_any
            for d in new: t[3][d] += 1
            res["mutants"].append({"rule": rid, "op": op, "note": note, "expected": expected, "new_flags": list(new)})
    rows = []
    for op in ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"):
        n, de, da, by = tab[op]
        rows.append({"op": op, "mutants": n, "detected_expected": de, "detected_any": da, "recall_any": round(da / n, 3) if n else None, "by_detector": dict(by)})
    res["table"] = rows; res["specificity"] = {"seeds": len(seeds), "flagged_unmutated": len(fp), "specificity": round(1 - len(fp) / len(seeds), 4)}
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "mutation_results.json")
    json.dump(res, open(out, "w"), indent=0)
    print(json.dumps(rows, indent=1)); print(res["specificity"]); print("unmutated seeds flagged:", {k: list(v) for k, v in fp.items()})

if __name__ == "__main__": main()
