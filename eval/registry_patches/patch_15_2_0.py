"""Registry 15.2.0 - correction of the defects recorded by the audit study. Protocol: PROTOCOL_15_2_0.md.
Applies C1-C4 exactly as listed there; asserts the expected number of touched rules so nothing else moves."""
import brotli, json, shutil, os, hashlib, collections, sys

ROOT = "/home/user/Hemoglyph"
TODAY = "2026-10-28"
VER = "15.2.0"

C1 = ["elevated_mean_corpuscular_volume_staging_severity_1_v1", "decreased_mean_corpuscular_volume_staging_severity_1_v1",
      "elevated_total_protein_staging_severity_1_v1", "decreased_total_protein_staging_severity_1_v1"]
C2 = ["iron_deficiency_anemia_bsg_2021_ferritin_30_cur13", "iron_deficiency_anemia_bsg_2021_inflammation_adjusted_cur13",
      "hemolytic_anemia_eha_2023_hemolysis_triad_cur13", "autoimmune_hemolytic_anemia_eha_2023_dat_positive_hemolysis_cur13"]
C4A = ["acute_pancreatitis_exclusion_normal_lipase_v1", "acute_pancreatitis_support_pattern_exclusion_normal_pancreatic_enzymes_v1"]
C4B = ["chronic_pancreatitis_screening_1_v1", "chronic_pancreatitis_diagnostic_criterion_1_v1"]

def leaves(e):
    if not isinstance(e, dict): return []
    if "feature_id" in e: return [e]
    out = []
    for k in ("all", "any", "none"):
        for c in e.get(k, []) or []: out += leaves(c)
    if "n_of" in e:
        for c in e["n_of"].get("conditions", []): out += leaves(c)
    return out

def patch(d):
    R = d["rules"]; log = collections.defaultdict(list)
    for rid in C1:
        r = R[rid]; assert r.get("executable"), rid
        r["executable"] = False; r["status"] = "retired_v15_2_0_implausible_tier"
        r["retired_reason"] = "threshold outside the physiological range of the analyte; no source defines this tier (audit study, Part 1)"
        log["C1"].append(rid)
    for rid in C2:
        r = R[rid]; assert "neonate" in r["population"]["age_groups"], rid
        r["population"]["age_groups"] = ["adolescent", "adult", "older_adult"]
        r.setdefault("limitations", []).append("15.2.0: population restricted to >= adolescent; the cited guideline is adult and Hb < 12/13 g/dL is the WHO adult limit (audit study, Part 1)")
        log["C2"].append(rid)
    for rid, r in R.items():
        touched = set()
        for l in leaves(r.get("expression")):
            f, u = l.get("feature_id"), l.get("unit")
            if f == "adrenocorticotropic_hormone" and u == "ng/mL": l["unit"] = "pg/mL"; touched.add("C3a")
            elif f == "intact_parathyroid_hormone" and u == "ng/mL": l["unit"] = "pg/mL"; touched.add("C3b")
            elif f == "morning_cortisol" and u == "ng/mL": l["unit"] = "ug/dL"; l["value"] = round(float(l["value"]) / 10.0, 3); touched.add("C3c")
        for c in touched: log[c].append(rid)
    for rid in C4A:
        assert R[rid]["source_ids"] == ["acg_gerd_2022"], rid; R[rid]["source_ids"] = ["acg_acute_pancreatitis_2024"]; log["C4a"].append(rid)
    for rid in C4B:
        assert R[rid]["source_ids"] == ["acg_gerd_2022"], rid; R[rid]["source_ids"] = ["acg_pancreatitis_2024"]; log["C4b"].append(rid)
    for rid, r in R.items():
        if "nes_sod_guidelines_2024" in (r.get("source_ids") or []):
            new = "reference_interval_convention" if rid.startswith("hypernatremia") else "ese_hyponatremia_2014"
            r["source_ids"] = [new if s == "nes_sod_guidelines_2024" else s for s in r["source_ids"]]; log["C4c"].append(rid)
    for rid in [x for v in log.values() for x in v]:
        R[rid].setdefault("patch_history", []).append({"version": VER, "date": TODAY})
    # disease rule-layer bookkeeping for C1
    for did, dz in d["diseases"].items():
        for layer, ids in (dz.get("layers") or {}).items():
            if any(i in C1 for i in ids): dz["layers"][layer] = [i for i in ids if i not in C1]
    m = d["registry_metadata"]; m["version"] = f"{VER}-CLINICAL-CURATED"; m["last_updated"] = TODAY
    m["executable_rules"] = sum(1 for r in R.values() if r.get("executable"))
    m["retired_rules"] = sum(1 for r in R.values() if str(r.get("status", "")).startswith("retired"))
    m["changelog"] = [c for c in m.get("changelog", []) if c.get("version") != VER]
    m["changelog"].append({"version": VER, "date": TODAY, "protocol": "eval/registry_patches/PROTOCOL_15_2_0.md",
        "change": (f"Audit-study corrections. C1 retired {len(log['C1'])} implausible severity tiers; C2 population gate on {len(log['C2'])} adult anaemia rules; "
                   f"C3 unit labels corrected on {len(log['C3a'])} ACTH, {len(log['C3b'])} PTH and {len(log['C3c'])} cortisol rules (values unchanged except exact ng/mL->ug/dL); "
                   f"C4 sources corrected on {len(log['C4a']) + len(log['C4b']) + len(log['C4c'])} rules. No threshold tuned, no rule added. Executable rules {m['executable_rules']}.")})
    return log

def patch_features(F):
    u = F["features"]["adrenocorticotropic_hormone"]["units"]
    assert u["canonical"] == "ng/mL"
    u.update({"canonical": "pg/mL", "ucum": "pg/mL", "accepted": ["pg/mL", "ng/L", "pmol/L"],
              "conversions": [{"from": "ng/L", "to": "pg/mL", "factor": 1.0}, {"from": "pmol/L", "to": "pg/mL", "factor": 4.541}],
              "conversion_review_required": False, "note_15_2_0": "canonical unit corrected from ng/mL (1000x error) to pg/mL; Tietz reference 7.2-63.3 pg/mL"})
    F["features"]["adrenocorticotropic_hormone"]["terminology"]["ucum"] = "pg/mL"
    for rr in F["features"]["adrenocorticotropic_hormone"].get("reference_ranges", []):
        if rr.get("unit") == "ng/mL": rr["unit"] = "pg/mL"
    F["registry_metadata"]["last_updated"] = TODAY
    F["registry_metadata"]["patch_15_2_0"] = "adrenocorticotropic_hormone unit canonicalised to pg/mL"

def write(d, path):
    raw = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
    open(path, "wb").write(brotli.compress(raw, quality=11)); return hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    src_path = f"{ROOT}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
    d = json.loads(brotli.decompress(open(src_path, "rb").read()))
    assert d["registry_metadata"]["version"].startswith("15.1.0"), d["registry_metadata"]["version"]
    log = patch(d)
    counts = {k: len(v) for k, v in log.items()}
    assert {k: counts[k] for k in ("C1", "C2", "C4a", "C4b", "C4c")} == {"C1": 4, "C2": 4, "C4a": 2, "C4b": 2, "C4c": 10}, counts
    if "--dry-run" in sys.argv: print(json.dumps(counts, indent=1)); sys.exit(0)
    d["registry_metadata"]["sha256_uncompressed"] = None
    sha = write(d, src_path); d["registry_metadata"]["sha256_uncompressed"] = sha
    for f in ["HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"]:
        write(d, f"{ROOT}/{f}")
        if os.path.exists(f"{ROOT}/tools/{f}"): shutil.copy2(f"{ROOT}/{f}", f"{ROOT}/tools/{f}")
    fp = f"{ROOT}/HEMOGLYPH_FEATURE_REGISTRY.json.br"
    F = json.loads(brotli.decompress(open(fp, "rb").read())); patch_features(F); fsha = write(F, fp)
    if os.path.exists(f"{ROOT}/tools/HEMOGLYPH_FEATURE_REGISTRY.json.br"): shutil.copy2(fp, f"{ROOT}/tools/HEMOGLYPH_FEATURE_REGISTRY.json.br")
    rel = f"{ROOT}/release/registry_{VER}"; os.makedirs(rel, exist_ok=True)
    shutil.copy2(src_path, f"{rel}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    if not os.path.lexists(f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br"):
        os.symlink("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br")
    shutil.copy2(fp, f"{rel}/HEMOGLYPH_FEATURE_REGISTRY.json.br")
    with open(f"{rel}/SHA256SUMS.txt", "w") as fh:
        for n in ["HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_FEATURE_REGISTRY.json.br"]:
            fh.write(f"{hashlib.sha256(open(f'{rel}/{n}', 'rb').read()).hexdigest()}  {n}\n")
    summary = {"counts": counts, "rule_ids": dict(log), "sha256_uncompressed": sha, "feature_registry_sha256_uncompressed": fsha}
    json.dump(summary, open(f"{ROOT}/eval/registry_patches/review_15_2_0.json", "w"), indent=1)
    print(json.dumps(counts, indent=1), "sha", sha, "features", fsha)
