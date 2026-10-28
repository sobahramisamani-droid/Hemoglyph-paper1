"""Registry 15.3.0 - closes the open items of the verification ledger. Protocol: PROTOCOL_15_3_0.md (frozen a68a1f6).
Applies D1, D2 and L exactly as listed there; asserts the touched counts so nothing else moves. `--dry-run` prints counts."""
import brotli, json, shutil, os, hashlib, collections, sys, gzip

ROOT = "/home/user/Hemoglyph"
TODAY = "2026-10-28"
VER = "15.3.0"

NEW_SOURCES = {
 "php_consensus_2018": {
  "organization": "International consensus (Mantovani G et al.)", "title": "Diagnosis and management of pseudohypoparathyroidism and related disorders: first international Consensus Statement",
  "year": 2018, "journal": "Nat Rev Endocrinol 2018;14:476-500", "doi": "10.1038/s41574-018-0042-0", "pmcid": "PMC6541219",
  "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6541219/", "scope": ["endocrine", "calcium", "parathyroid"],
  "evidence_status": "international_consensus__threshold_text_verified", "citation_use": "clinical_decision_support",
  "jurisdiction_scope": "international", "license_status": "open_citation", "last_verified_on": TODAY,
  "verified_quote": "The definition of PTH resistance is as follows: The association of hypocalcaemia, hyperphosphataemia and elevated serum levels of PTH in the absence of vitamin D deficiency and when magnesium levels and renal function are normal."},
 "cdc_hav_case_definition_2019": {
  "organization": "CDC / CSTE", "title": "Hepatitis A, Acute - 2019 Case Definition", "year": 2019,
  "url": "https://ndc.services.cdc.gov/case-definitions/hepatitis-a-acute-2019/", "scope": ["infectious", "liver", "hepatitis"],
  "evidence_status": "surveillance_case_definition__criterion_text_verified", "citation_use": "clinical_decision_support",
  "jurisdiction_scope": "US", "license_status": "public_domain_us_government", "last_verified_on": TODAY,
  "verified_quote": "Confirmatory laboratory evidence: Immunoglobulin M (IgM) antibody to hepatitis A virus (anti-HAV) positive, OR Nucleic acid amplification test (NAAT; such as Polymerase Chain Reaction [PCR] or genotyping) for hepatitis A virus RNA positive"},
}
D1_RESOURCE = {"pseudohypoparathyroidism_hypocalcemia_high_pth_normal_renal_cur13": ("phpt_workshop_2022", "php_consensus_2018"),
               "hepatitis_a_igm_anti_hav_positive_cur13": ("aasld_hav_hev_2023", "cdc_hav_case_definition_2019")}
D1_CONVENTION = {"hypomagnesemia_severe_1_2_cur13": ("kdigo_potassium_2020", "severe hypomagnesaemia < 1.2 mg/dL is a severity convention; the KDIGO potassium conference report cited before 15.3.0 does not define it (Note 8)"),
                 "hyperprolactinemia_pituitary_2023_prolactin_elevated_cur13": ("endo_hyperprolactinemia_2011_2023", "25 ng/mL is the usual female upper reference limit; the Pituitary Society 2023 consensus cited before 15.3.0 defers to assay-specific ranges (Note 8)")}
D1_RETIRE = {"septic_shock_severe_lactic_acidosis_sepsis3_lactate_4_cur13": "single-analyte assertion of septic shock from lactate > 4 mmol/L; Sepsis-3 (the cited source) defines shock with lactate > 2 mmol/L; no verifiable replacement source retrieved (Note 8, ledger D1)",
             "acquired_hemophilia_a_reanchor_scre_v13_4": "FVIII < 40 % alone does not distinguish acquired from congenital haemophilia A or VWD; the cited BSH rare-factor guideline excludes FVIII deficiency; the matching guideline was not retrievable, no source attached from memory (Note 8, ledger D1)"}
D2 = "prediabetes_hba1c_pattern_screening_1_v1"
LEDGER_RELABEL = {"pseudohypoparathyroidism_hypocalcemia_high_pth_normal_renal_cur13": "quote_verified", "hepatitis_a_igm_anti_hav_positive_cur13": "quote_verified",
                  "hypomagnesemia_severe_1_2_cur13": "convention_unverified", "hyperprolactinemia_pituitary_2023_prolactin_elevated_cur13": "convention_unverified",
                  "septic_shock_severe_lactic_acidosis_sepsis3_lactate_4_cur13": "retired", "acquired_hemophilia_a_reanchor_scre_v13_4": "retired",
                  D2: "discordant_corrected", "rhabdomyolysis_ck_5x_uln_diagnostic_cur13": "discordant_corrected"}

def patch(d, ledger):
    R = d["rules"]; log = collections.defaultdict(list); S = d["guideline_sources"]
    for sid, meta in NEW_SOURCES.items():
        assert sid not in S, sid; S[sid] = dict(meta, source_id=sid)
    for rid, (old, new) in D1_RESOURCE.items():
        r = R[rid]; assert r["source_ids"] == [old], (rid, r["source_ids"])
        r["source_ids"] = [new]
        p = r.setdefault("provenance", None) or {}; r["provenance"] = p
        p.update({"source_ids": [new], "resourced_in": VER, "verified_quote": NEW_SOURCES[new]["verified_quote"], "verification": "quote_verified_15_3_0"})
        log["D1_resourced"].append(rid)
    for rid, (old, note) in D1_CONVENTION.items():
        r = R[rid]; assert r["source_ids"] == [old], (rid, r["source_ids"])
        r["source_ids"] = ["reference_interval_convention"]
        r["provenance"] = {"source_ids": ["reference_interval_convention"], "resourced_in": VER, "verification": "reference_interval_convention"}
        r.setdefault("limitations", []).append(f"{VER}: {note}")
        log["D1_convention"].append(rid)
    for rid, why in D1_RETIRE.items():
        r = R[rid]; assert r.get("executable"), rid
        r["executable"] = False; r["status"] = "retired_v15_3_0_discordant_source"; r["retired_reason"] = why
        log["D1_retired"].append(rid)
    r = R[D2]; e = r["expression"]
    assert e == {"feature_id": "hemoglobin_a1c", "operator": ">=", "value": 5.7, "unit": "%", "weight": 3.0}, e
    r["expression"] = {"all": [dict(e), {"feature_id": "hemoglobin_a1c", "operator": "<=", "value": 6.4, "unit": "%", "weight": 3.0}]}
    r.setdefault("limitations", []).append(f"{VER}: upper bound 6.4 % added as promised by PROTOCOL_15_0_0 R5 but not written by patch_15_0_0.py (ledger D2)")
    log["D2_changed"].append(D2)
    for rid in [x for v in log.values() for x in v]:
        R[rid].setdefault("patch_history", None); R[rid]["patch_history"] = (R[rid]["patch_history"] or []) + [{"version": VER, "date": TODAY}]
    retired = set(D1_RETIRE)
    for did, dz in d["diseases"].items():
        for layer, ids in (dz.get("layers") or {}).items():
            if any(i in retired for i in ids): dz["layers"][layer] = [i for i in ids if i not in retired]
    for rec in ledger:
        rid = rec["rule_id"]
        if rid not in R: continue
        lab = LEDGER_RELABEL.get(rid, rec["verification_status"])
        p = R[rid].get("provenance") or {}; R[rid]["provenance"] = p
        p["ledger_15_3_0"] = {"status": lab, "built_from": "registry 15.2.0 ledger (eval/verification_ledger)"}
        log["L_labelled"].append(rid)
    m = d["registry_metadata"]; m["version"] = f"{VER}-CLINICAL-CURATED"; m["last_updated"] = TODAY
    m["executable_rules"] = sum(1 for r in R.values() if r.get("executable"))
    m["retired_rules"] = sum(1 for r in R.values() if str(r.get("status", "")).startswith("retired"))
    m["changelog"] = [c for c in m.get("changelog", []) if c.get("version") != VER]
    m["changelog"].append({"version": VER, "date": TODAY, "protocol": "eval/registry_patches/PROTOCOL_15_3_0.md",
        "change": (f"Ledger closure. D1: {len(log['D1_resourced'])} rules re-sourced with retrieved quotes, {len(log['D1_convention'])} moved to reference_interval_convention, "
                   f"{len(log['D1_retired'])} retired (discordant source, no verifiable replacement); D2: prediabetes HbA1c upper bound 6.4 % written (15.0.0 R5 gap); "
                   f"L: provenance.ledger_15_3_0 on {len(log['L_labelled'])} rules. No threshold tuned, no rule added. Executable rules {m['executable_rules']}.")})
    return log

def write(d, path):
    raw = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
    open(path, "wb").write(brotli.compress(raw, quality=11)); return hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    src_path = f"{ROOT}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
    d = json.loads(brotli.decompress(open(src_path, "rb").read()))
    assert d["registry_metadata"]["version"].startswith("15.2.0"), d["registry_metadata"]["version"]
    ledger = json.load(gzip.open(f"{ROOT}/eval/verification_ledger/LEDGER.json.gz", "rt", encoding="utf-8"))
    log = patch(d, ledger)
    counts = {k: len(v) for k, v in log.items()}
    assert counts == {"D1_resourced": 2, "D1_convention": 2, "D1_retired": 2, "D2_changed": 1, "L_labelled": 605}, counts
    if "--dry-run" in sys.argv: print(json.dumps(counts, indent=1)); sys.exit(0)
    d["registry_metadata"]["sha256_uncompressed"] = None
    sha = write(d, src_path); d["registry_metadata"]["sha256_uncompressed"] = sha
    for f in ["HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"]:
        write(d, f"{ROOT}/{f}")
        if os.path.exists(f"{ROOT}/tools/{f}"): shutil.copy2(f"{ROOT}/{f}", f"{ROOT}/tools/{f}")
    rel = f"{ROOT}/release/registry_{VER}"; os.makedirs(rel, exist_ok=True)
    shutil.copy2(src_path, f"{rel}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    if not os.path.lexists(f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br"):
        os.symlink("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br")
    with open(f"{rel}/SHA256SUMS.txt", "w") as fh:
        fh.write(f"{hashlib.sha256(open(f'{rel}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br', 'rb').read()).hexdigest()}  HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br\n")
        fh.write("feature registry unchanged from 15.2.0 (release/registry_15.2.0/HEMOGLYPH_FEATURE_REGISTRY.json.br)\n")
    summary = {"counts": counts, "rule_ids": dict(log), "retired_reason": {k: v for k, v in D1_RETIRE.items()}, "sha256_uncompressed": sha,
               "implementation_gap_15_0_0": "PROTOCOL_15_0_0 R5 specified HbA1c >= 5.7 and <= 6.4 for prediabetes_hba1c_pattern_screening_1_v1; patch_15_0_0.py line 351 changed only the operator. Found by the ledger (Note 15 verdict), closed here."}
    json.dump(summary, open(f"{ROOT}/eval/registry_patches/review_15_3_0.json", "w"), indent=1)
    print(json.dumps(counts, indent=1), "sha", sha)
