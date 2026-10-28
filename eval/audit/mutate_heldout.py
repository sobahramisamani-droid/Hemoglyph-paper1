"""Supplementary Note 20 (PROTOCOL_HELDOUT.md): held-out mutation test of the frozen static audit detectors.

Pools: P1 = 300 AI-drafted (non-curated, non-quote-verified) executable rules of registry 15.3.0, seed 20261028;
       P2 = the external LLM corpus (Note 17) rebuilt by convert_llm_corpus.py.
Families H1..H8 are defined in the protocol and were NOT used while the detectors were written.
Usage: python3 mutate_heldout.py [--p1 release/registry_15.3.0/....br] [--p2 /tmp/llm_corpus_part3.json.gz]
Writes heldout_results.json.gz and RESULTS_HELDOUT.md next to this file (or --out-dir).
"""
import json, copy, collections, random, sys, os, gzip, math, brotli
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import Audit, leaves, num, load_br, HG, CONV, SCOPE2DOM
from mutate import numeric_leaf_paths, get, MASS_MOLAR

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")
EXPECTED = {"H1": None, "H2": None, "H3": None, "H4": None, "H5": None, "H6": "r9|unit", "H7": "unit", "H8": "dir"}
ALL_AGES = ["neonate", "infant", "child", "adolescent", "adult", "elderly"]
FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}

def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 3), round((c + h) / d, 3))

def source_domains(s):
    sc = [str(x).lower().replace(" ", "_") for x in (s.get("scope") or [])]
    return frozenset(SCOPE2DOM[w] for w in sc if w in SCOPE2DOM) - {"*"}

def apply(fam, rule, leaf, aud, reg, rng):
    """return (mutant, note) or None when the family is not applicable to this seed."""
    r = copy.deepcopy(rule); l = get(r["expression"], leaf); v = float(l["value"]); fid = l["feature_id"]; op = l.get("operator")
    if fam == "H1":
        ages = set((r.get("population") or {}).get("age_groups") or [])
        if not ages or ages >= set(ALL_AGES): return None
        r.setdefault("population", {})["age_groups"] = list(ALL_AGES); return r, f"age gate {sorted(ages)} -> all"
    if fam == "H2":
        sid = (r.get("source_ids") or [None])[0]; S = reg["guideline_sources"]
        if not sid or sid not in S: return None
        own = source_domains(S[sid])
        if not own: return None
        cands = [s for s in sorted(S) if s != sid and source_domains(S[s]) & own]
        if not cands: return None
        r["source_ids"] = [rng.choice(cands)]; return r, f"source {sid} -> {r['source_ids'][0]} (same domain)"
    if fam == "H3":
        if op not in FLIP: return None
        dup = copy.deepcopy(l); dup["operator"] = FLIP[op]
        parent = get(r["expression"], leaf[:-1]) if leaf else None
        if leaf and isinstance(parent, list):
            parent[leaf[-1]] = {"all": [l, dup]}
        else:
            r["expression"] = {"all": [l, dup]}
        return r, f"{fid} {op} {v} AND {FLIP[op]} {v}"
    if fam == "H4":
        u = l.get("unit")
        if not u: return None
        ok, canon = aud.units_ok(fid)
        fac = CONV.get((fid, u), CONV.get((fid, u.replace("u", "µ"))))
        if fac not in (None, 1.0) and canon in ok:          # seed in a non-canonical unit: convert TO canonical
            l["unit"] = canon; l["value"] = round(v * fac, 6); return r, f"{fid} {v} {u} -> {l['value']} {canon} (consistent)"
        if u.replace("µ", "u") == (canon or "").replace("µ", "u"):   # seed canonical: convert to an accepted alternative unit
            alts = sorted(a for (f, a), fc in CONV.items() if f == fid and fc not in (None, 1.0) and a in ok)
            if not alts: return None
            nu = alts[0]; fc = CONV[(fid, nu)]
            l["unit"] = nu; l["value"] = round(v / fc, 6); return r, f"{fid} {v} {u} -> {l['value']} {nu} (consistent)"
        return None
    if fam == "H5":
        f = 1.2 if rng.random() < 0.5 else 0.8
        l["value"] = round(v * f, 6); return r, f"{fid} {v} -> {l['value']} (x{f})"
    if fam == "H6":
        f = 10.0 if rng.random() < 0.5 else 0.1
        l["value"] = round(v * f, 6); return r, f"{fid} {v} -> {l['value']} (x{f})"
    if fam == "H7":
        u = l.get("unit")
        if not u or u not in MASS_MOLAR: return None
        nu = MASS_MOLAR[u]
        if (fid, nu) not in CONV and (fid, nu.replace("u", "µ")) not in CONV and nu == aud.units_ok(fid)[1]: return None
        l["unit"] = nu; return r, f"{fid} {u} -> {nu} (value unchanged)"
    if fam == "H8":
        if op not in FLIP: return None
        l["operator"] = FLIP[op]; return r, f"{fid} {op} -> {FLIP[op]}"
    return None

def run_pool(name, reg, feats, seeds, rng):
    aud = Audit(reg, feats); R = reg["rules"]
    base = {rid: aud.run_rule(rid, R[rid]) for rid in seeds}
    fp = {rid: f for rid, f in base.items() if f}
    tab = {f: [0, 0, collections.Counter()] for f in FAMILIES}; mutants = []
    for rid in seeds:
        rule = R[rid]; leaf = numeric_leaf_paths(rule["expression"])[0]
        for fam in FAMILIES:
            m = apply(fam, rule, leaf, aud, reg, rng)
            if m is None: continue
            mr, note = m; R[rid] = mr
            a2 = aud if fam not in ("H3", "H8") else Audit(reg, feats)
            flags = a2.run_rule(rid, mr); R[rid] = rule
            new = {d: w for d, w in flags.items() if d not in base[rid]}
            t = tab[fam]; t[0] += 1; t[1] += bool(new)
            for d in new: t[2][d] += 1
            mutants.append({"rule": rid, "fam": fam, "note": note, "new_flags": sorted(new)})
    rows = []
    for fam in FAMILIES:
        n, da, by = tab[fam]; lo, hi = wilson(da, n)
        if fam == "H4":   # specificity probe: report fraction NOT flagged
            k = n - da; lo, hi = wilson(k, n)
            rows.append({"fam": fam, "n": n, "unflagged": k, "specificity": round(k / n, 3) if n else None, "ci": [lo, hi], "by_detector": dict(by)})
        else:
            rows.append({"fam": fam, "n": n, "detected_any": da, "recall_any": round(da / n, 3) if n else None, "ci": [lo, hi],
                         "expected_detector": EXPECTED[fam], "by_detector": dict(by)})
    k = len(seeds) - len(fp)
    spec = {"seeds": len(seeds), "flagged_unmutated": len(fp), "specificity": round(k / len(seeds), 4), "ci": list(wilson(k, len(seeds)))}
    return {"pool": name, "seeds": len(seeds), "specificity_unmutated": spec, "table": rows, "mutants": mutants,
            "baseline_flags": {rid: sorted(f) for rid, f in fp.items()}}

def md_table(res):
    out = [f"**{res['pool']}** — seeds {res['seeds']}; unmutated seeds unflagged {res['specificity_unmutated']['specificity']:.3f} "
           f"(95% CI {res['specificity_unmutated']['ci'][0]}–{res['specificity_unmutated']['ci'][1]})", "",
           "| family | applicable n | detected (any) | recall-any | 95% Wilson CI | detector(s) that fired |", "|---|---|---|---|---|---|"]
    for r in res["table"]:
        by = ", ".join(f"{d} {c}" for d, c in sorted(r["by_detector"].items())) or "—"
        if r["fam"] == "H4":
            out.append(f"| H4 (benign conversion; must NOT flag) | {r['n']} | {r['n'] - r['unflagged']} | specificity {r['specificity']} | {r['ci'][0]}–{r['ci'][1]} | {by} |")
        else:
            out.append(f"| {r['fam']} | {r['n']} | {r['detected_any']} | {r['recall_any']} | {r['ci'][0]}–{r['ci'][1]} | {by} |")
    return "\n".join(out)

def main():
    a = sys.argv
    p1 = a[a.index("--p1") + 1] if "--p1" in a else os.path.join(HG, "release/registry_15.3.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    p2 = a[a.index("--p2") + 1] if "--p2" in a else "/tmp/llm_corpus_part3.json.gz"
    out_dir = a[a.index("--out-dir") + 1] if "--out-dir" in a else HERE
    feats = load_br(os.path.join(HG, "HEMOGLYPH_FEATURE_REGISTRY.json.br"))["features"]
    results = []
    # P1
    reg = load_br(p1); R = reg["rules"]
    pool = sorted(rid for rid, r in R.items() if r.get("executable") and not rid.startswith("co_")
                  and not str(r.get("status", "")).startswith("curated") and not (r.get("provenance") or {}).get("verified_quote")
                  and numeric_leaf_paths(r.get("expression")))
    rng = random.Random(20261028); seeds = sorted(rng.sample(pool, 300))
    print("P1 eligible", len(pool), "sampled", len(seeds)); results.append(run_pool("P1 registry 15.3.0, AI-drafted non-curated rules", reg, feats, seeds, rng))
    del reg, R
    # P2
    reg = json.load(gzip.open(p2, "rt")); R = reg["rules"]
    seeds = sorted(rid for rid, r in R.items() if r.get("executable") and numeric_leaf_paths(r.get("expression")))
    print("P2 seeds", len(seeds)); results.append(run_pool("P2 external LLM corpus (Note 17)", reg, feats, seeds, random.Random(20261028)))
    with gzip.GzipFile(os.path.join(out_dir, "heldout_results.json.gz"), "wb", mtime=0) as f:
        f.write(json.dumps({"protocol": "PROTOCOL_HELDOUT.md", "p1_registry": os.path.basename(os.path.dirname(p1)), "results": results}, indent=0).encode())
    md = ["# Held-out mutation test — results (Note 20)", "", "Protocol: `PROTOCOL_HELDOUT.md` (committed before this run). Detectors frozen (audit.py @ 9c87645).", ""]
    for r in results: md += [md_table(r), ""]
    open(os.path.join(out_dir, "RESULTS_HELDOUT.md"), "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md))

if __name__ == "__main__": main()
