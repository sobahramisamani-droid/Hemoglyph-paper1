"""Convert the pipe-separated LLM corpus (eval/audit/llm_corpus.tsv) into the Hemoglyph disease-registry schema
so that eval/audit/audit.py can run on it unchanged.  Guideline sources are borrowed from registry 15.1.0 (the
corpus cites only identifiers from that list).  Feature identifiers are normalised to registry identifiers where
an unambiguous equivalent exists (FEATURE_ALIASES); leaves on features absent from the feature registry are kept
verbatim and counted as not unit-checkable.  Population defaults to all age groups unless the entity is explicitly
neonatal, mirroring the default used by the Hemoglyph generator."""
import hashlib, json, os, re, sys
import brotli

HG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(HG, "eval", "audit", "llm_corpus.tsv")
OUT = os.path.join(HG, "eval", "audit", "llm_corpus_registry.json.gz")

FEATURE_ALIASES = {
    "25_hydroxyvitamin_d": "25_hydroxy_vitamin_d", "anti_cyclic_citrullinated_peptide": "cyclic_citrullinated_peptide_antibody",
    "anti_double_stranded_dna": "double_stranded_dna_antibody", "anti_jo1_antibody": "jo_1_antibody",
    "anti_mpo_antibody": "myeloperoxidase_antibody", "anti_smooth_muscle_antibody": "smooth_muscle_antibody",
    "anticardiolipin_igg": "cardiolipin_igg_antibody", "antimitochondrial_antibody": "mitochondrial_m2_antibody",
    "bone_marrow_blasts_percent": "blasts_percent", "bone_marrow_plasma_cells_percent": "plasma_cells_percent",
    "carboxyhemoglobin_percent": "carboxyhemoglobin_fraction", "methemoglobin_percent": "methemoglobin_fraction",
    "cd4_t_cell_count_absolute": "cd4_t_cells_absolute", "cold_agglutinin_titer": "cold_agglutinins_titer",
    "erythropoietin": "erythropoietin_serum_quantitative", "fractional_excretion_sodium": "fractional_excretion_of_sodium",
    "galactomannan_index": "serum_galactomannan_index", "beta_d_glucan": "one_three_beta_d_glucan_serum",
    "glucose_1h_ogtt": "glucose_1_hour_ogtt", "haptoglobin_serum": "serum_haptoglobin",
    "hemoglobin_a2_percent": "hemoglobin_a2", "hemoglobin_s_percent": "hemoglobin_s",
    "hepatitis_b_dna_quantitative": "hepatitis_b_dna_quantitative_pcr", "hepatitis_c_rna_quantitative": "hepatitis_c_rna_quantitative_pcr",
    "late_night_salivary_cortisol": "salivary_cortisol_late_night", "lupus_anticoagulant": "lupus_anticoagulant_screen",
    "lyme_western_blot_igg": "borrelia_burgdorferi_igg_western_blot", "lyme_antibody_screen": "borrelia_burgdorferi_igg_antibody",
    "rpr_titer": "syphilis_rpr", "treponemal_antibody": "treponema_pallidum_hemagglutination_tpha",
    "schistocytes": "schistocytes_percent", "serum_free_light_chain_ratio": "free_light_chain_ratio",
    "urine_uric_acid_24h": "uric_acid_24h_urine",
}
NEONATAL = {"neonatal_sepsis", "hemolytic_disease_of_newborn", "congenital_toxoplasmosis"}
ALL_AGES = ["neonate", "infant", "child", "adolescent", "adult", "older_adult"]

def leaf(txt):
    m = re.match(r"^\s*([a-z0-9_]+)\s*(<=|>=|<|>|=)\s*([0-9.]+)\s*(\S*)\s*$", txt)
    if not m: raise ValueError(txt)
    fid, op, val, unit = m.groups()
    fid = FEATURE_ALIASES.get(fid, fid)
    d = {"feature_id": fid, "operator": op, "value": float(val), "weight": 1.0}
    if unit: d["unit"] = unit
    return d

def expression(txt):
    m = re.match(r"^(all|any):\s*(.*)$", txt)
    if m: return {m.group(1): [leaf(x) for x in m.group(2).split(";") if x.strip()]}
    return leaf(txt)

def main():
    raw = open(SRC, "rb").read(); sha = hashlib.sha256(raw).hexdigest()
    base = json.loads(brotli.decompress(open(os.path.join(HG, "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"), "rb").read()))
    reg = {"registry_metadata": {"registry_version": "llm_corpus_part3", "source_sha256": sha},
           "guideline_sources": base["guideline_sources"], "diseases": {}, "rules": {}}
    n = {}
    for line in raw.decode().splitlines():
        if not line.strip(): continue
        eid, name, dom, kind, rtype, expr, sid = [x.strip() for x in line.split("|")]
        ages = ["neonate", "infant"] if eid in NEONATAL else ALL_AGES
        reg["diseases"].setdefault(eid, {"identity": {"disease_id": eid, "name_en": name},
            "classification": {"domains": [dom], "entity_kind": kind}, "population": {"age_groups": ages, "sex": "all"}, "rule_ids": []})
        n[eid] = n.get(eid, 0) + 1
        rid = f"{eid}_{rtype}_v{n[eid]}"
        reg["rules"][rid] = {"rule_id": rid, "disease_id": eid, "rule_type": rtype, "status": "candidate", "executable": True,
            "expression": expression(expr), "population": {"age_groups": ages, "sex": "all"}, "source_ids": [sid], "entity_kind": kind}
        reg["diseases"][eid]["rule_ids"].append(rid)
    import gzip
    with gzip.open(OUT, "wt") as f: json.dump(reg, f)
    print(json.dumps({"corpus_sha256": sha, "entities": len(reg["diseases"]), "rules": len(reg["rules"]), "out": OUT}))

if __name__ == "__main__":
    main()
