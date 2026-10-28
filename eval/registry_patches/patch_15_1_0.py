"""Registry 15.1.0 - second provenance/fidelity patch (same closed protocol as 15.0.0: PROTOCOL_15_0_0.md).

Nothing in this patch is driven by benchmark numbers. Every class below is defined by a property of the
rule text itself that can be re-checked by anyone with the registry file:

  R7  arithmetic-tier artefacts  -> status retired_v15_1_0_arithmetic_tier
      candidate 'staging_severity' / 'diagnostic_criterion' rules whose EVERY threshold equals 1.5x or 0.5x of
      the SAME entity's screening threshold for the SAME analyte (e.g. CRP >10 -> ">15", WBC >11 -> ">16.5",
      Ca >10.5 -> ">15.75", K <3.5 -> "<1.75"). No guideline defines tiers this way; the numbers were produced
      by a multiplier. A short allow-list protects transformations that coincide with real published cut-offs
      (eGFR 45/30/15, faecal elastase 100, UPCR 0.3, Hb 8/7, platelets 50/20, ANC 1.0/0.5, lactate 4, ...).
  R2a-wide  nonspecific single-marker rules -> status retired_v15_1_0_nonspecific_single_marker
      candidate rules on a *clinical entity* whose whole expression is ONE ubiquitous analyte (CRP, WBC, ESR,
      PCT, AST/ALT/LDH/ALP/bilirubin, albumin, Hb, platelets, electrolytes, creatinine, glucose, lipids, TSH,
      ferritin/TSAT, differential counts ...). Finding entities (hyper-/hypo-, -penia, -cytosis, *_pattern,
      CKD stages, anaemia, iron deficiency ...) are excluded by name, and a short keep-list protects
      single-analyte rules whose threshold really is entity-defining in the literature
      (TSAT >45 % for haemochromatosis, TG >880 mg/dL for FCS, HDL <10/<5 for Tangier/LCAT, CK >20,000 for
      malignant hyperthermia, ALT >200 for acute hepatitis, PCT >0.5 for sepsis screening, PT >30 s for
      warfarin over-anticoagulation).
  R8  placeholder entities -> status retired_v15_1_0_placeholder_entity
      'uptodate_condition_01..30' are not diseases; each carries one rule 'CRP > n' with n = 11..40.
  R9  impossible thresholds (e.g. 'c_reactive_protein < 0') -> retired_v15_1_0_clinically_incorrect

Deliberately NOT changed (documented as open): the 139 '_f13_3' sex-specific variants derived in 13.3.0 from
female reference limits (a documented derivation, not an invented tier) and all curated / text-verified rules.
"""
import brotli, json, shutil, os, hashlib, collections, re, sys

ROOT = "/home/user/Hemoglyph"
TODAY = "2026-10-28"
VER = "15.1.0"

UBIQUITOUS = {
 "c_reactive_protein","white_blood_cell_count","erythrocyte_sedimentation_rate","procalcitonin",
 "aspartate_aminotransferase","alanine_aminotransferase","lactate_dehydrogenase","albumin","total_protein",
 "platelets","platelet_count","hemoglobin","mean_corpuscular_volume","creatinine","urea","blood_urea_nitrogen",
 "sodium","potassium","chloride","bicarbonate","calcium_total","phosphate","magnesium","glucose","lactate",
 "creatine_kinase_total","total_bilirubin","alkaline_phosphatase","gamma_glutamyl_transferase","uric_acid",
 "thyroid_stimulating_hormone","free_thyroxine","ferritin","transferrin_saturation","lymphocyte_count_absolute",
 "eosinophil_count_absolute","neutrophil_count_absolute","amylase","lipase","fasting_plasma_glucose",
 "hemoglobin_a1c","triglycerides","total_cholesterol","hdl_cholesterol","international_normalized_ratio",
 "prothrombin_time","fibrinogen","serum_osmolality","red_cell_distribution_width_cv","red_blood_cell_count",
 "hematocrit","monocytes_percent","neutrophils_percent","lymphocytes_percent","eosinophils_percent"}

FINDING_ENTITY = re.compile(
 r"_pattern$|^ckd_stage|^hyper|^hypo|agranulocytosis|penia$|cytosis$|philia$|anemia$|^iron_deficiency|azotemia$|"
 r"acidosis|alkalosis|^elevated_|^decreased_|^low_|^high_|^prolonged_|^severe_|uremia$|emia$|^anemia|^polycythemia|"
 r"dyslipidemia|hyperlipidemia|^diabetes_mellitus$|^prediabetes|^type_2_diabetes|^metabolic_syndrome|coagulopathy|"
 r"^thrombocyt|^leukocyt|^neutro|^lympho|^eosino|^pancytopenia|^bicytopenia|syndrome_of_inappropriate|^dehydration|"
 r"^malnutrition|^refeeding|^rhabdomyolysis$|^gout$|^tumor_lysis")

KEEP_SINGLE = {
 "hereditary_hemochromatosis_c282y_screening_1_v1",            # TSAT >45 % (AASLD 2011 / EASL 2022 screening cut-off)
 "familial_chylomicronemia_syndrome_existing_screening_1_v1",   # TG >880 mg/dL (10 mmol/L), ESC/EAS
 "familial_chylomicronemia_syndrome_existing_diagnostic_criterion_1_v1",
 "tangier_disease_screening_1_v1","tangier_disease_diagnostic_criterion_1_v1",      # HDL-C <10 / <5 mg/dL
 "lcat_deficiency_screening_1_v1","lcat_deficiency_diagnostic_criterion_1_v1",
 "malignant_hyperthermia_stage_p131",                           # CK >20,000 U/L
 "acute_hepatitis_screen_p131",                                 # ALT >200 U/L
 "warfarin_over_anticoagulation_authentic_criterion_v1",        # PT >30 s
 "sepsis_screening_1_v1",                                       # PCT >0.5 ng/mL
}

# (feature, value) pairs that are real published cut-offs even though they equal 1.5x/0.5x of a screening limit
ALLOW_TIER = {
 ("egfr_ckd_epi_creatinine",45.0),("egfr_ckd_epi_creatinine",30.0),("egfr_ckd_epi_creatinine",15.0),
 ("fecal_elastase_1",100.0),("urine_protein_to_creatinine_ratio",0.3),("urine_albumin_to_creatinine_ratio",300.0),
 ("hemoglobin",8.0),("hemoglobin",7.0),("platelets",50.0),("platelets",20.0),("platelets",100.0),
 ("neutrophil_count_absolute",1.0),("neutrophil_count_absolute",0.5),("lactate",4.0),("lactate",2.0),
 ("potassium",6.0),("potassium",2.5),("sodium",120.0),("sodium",125.0),("calcium_total",14.0),("calcium_total",7.0),
 ("glucose",250.0),("glucose",54.0),("total_bilirubin",2.0),("total_bilirubin",3.0),("international_normalized_ratio",1.5),
 ("international_normalized_ratio",5.0),("albumin",2.5),("albumin",3.0),("creatine_kinase_total",5000.0),
 ("ammonia",100.0),("thyroid_stimulating_hormone",10.0),("thyroid_stimulating_hormone",0.1),("c_reactive_protein",100.0),
 ("procalcitonin",2.0),("procalcitonin",0.25),("procalcitonin",10.0),("white_blood_cell_count",25.0),
 ("eosinophil_count_absolute",1.5),("triglycerides",500.0),("triglycerides",880.0),("ldl_cholesterol_calculated",190.0),
 ("bicarbonate",18.0),("bicarbonate",15.0),("phosphate",1.0),("magnesium",1.0),("uric_acid",10.0),("hematocrit",65.0),
 ("mean_corpuscular_volume",120.0),("fibrinogen",100.0),("fibrinogen",150.0),("arterial_ph",7.2),("arterial_ph",7.1),
}

def leaves(e):
    if not isinstance(e, dict): return []
    if "feature_id" in e: return [e]
    for k in ("all","any","none"):
        if k in e: return [l for c in e[k] for l in leaves(c)]
    if "n_of" in e: return [l for c in e["n_of"].get("conditions", []) for l in leaves(c)]
    return []

def retire(r, status, reason, cls):
    r["status"] = status; r["executable"] = False; r["retired_reason"] = f"v{VER} {cls}: {reason}"
    r["curated_on"] = TODAY; r["curation_version"] = VER

def classify(d):
    rules, D = d["rules"], d["diseases"]
    kind = {k: (v.get("classification") or {}).get("entity_kind") for k, v in D.items()}
    ex = {k: v for k, v in rules.items() if v.get("executable") and not k.startswith("co_")}
    scr = collections.defaultdict(set)
    for r in ex.values():
        if r.get("rule_type") == "screening":
            for l in leaves(r["expression"]):
                try: scr[(r["disease_id"], l["feature_id"])].add(float(l["value"]))
                except (TypeError, ValueError): pass
    def arith(dis, l):
        try: v = float(l["value"])
        except (TypeError, ValueError): return None
        if (l["feature_id"], v) in ALLOW_TIER: return None
        for s in scr.get((dis, l["feature_id"]), ()):
            for f in (1.5, 0.5):
                if s != v and abs(v - s * f) < 1e-6: return (s, f)
        return None
    out = {}
    for rid, r in ex.items():
        st = str(r.get("status", ""))
        if not st.startswith("candidate"): continue
        if (r.get("provenance") or {}).get("verified_quote"): continue
        if rid in KEEP_SINGLE: continue
        L = leaves(r["expression"]); dis = r["disease_id"]
        if dis.startswith("uptodate_condition_"):
            out[rid] = ("R8", "placeholder entity 'uptodate_condition_NN' with a CRP ladder rule; not a disease."); continue
        bad = [l for l in L if l.get("operator") in ("<", "<=") and isinstance(l.get("value"), (int, float)) and l["value"] <= 0
               and "base_excess" not in l["feature_id"] and "anion_gap" not in l["feature_id"]]
        if bad:
            out[rid] = ("R9", f"impossible threshold {bad[0]['feature_id']} {bad[0]['operator']} {bad[0]['value']}."); continue
        if r.get("rule_type") in ("staging_severity", "diagnostic_criterion") and L:
            A = [arith(dis, l) for l in L]
            if all(A):
                desc = "; ".join(f"{l['feature_id']} {l['operator']} {l['value']} = {a[1]}x screening {a[0]:g}" for l, a in zip(L, A))
                out[rid] = ("R7", f"threshold(s) are a fixed multiple of this entity's own screening threshold, not a published tier ({desc})."); continue
        if (kind.get(dis) == "clinical_entity" and len(L) == 1 and L[0]["feature_id"] in UBIQUITOUS
                and not FINDING_ENTITY.search(dis) and r.get("rule_type") != "exclusion_criterion"):
            out[rid] = ("R2a", f"single ubiquitous analyte ({L[0]['feature_id']} {L[0]['operator']} {L[0]['value']}) voting for a specific clinical entity; the cited source does not define the entity by this analyte alone.")
    return out

STATUS = {"R7": "retired_v15_1_0_arithmetic_tier", "R2a": "retired_v15_1_0_nonspecific_single_marker",
          "R8": "retired_v15_1_0_placeholder_entity", "R9": "retired_v15_1_0_clinically_incorrect"}

def patch(d):
    rules = d["rules"]; cls = classify(d); log = collections.defaultdict(list)
    for rid, (c, why) in cls.items():
        retire(rules[rid], STATUS[c], why, c); log[c].append(rid)
    for did, dz in d["diseases"].items():
        if did.startswith("uptodate_condition_"):
            cov = dz.setdefault("coverage", {}); cov["executable_rule_available"] = False
            cov["status"] = "retired_placeholder_v15_1_0"; cov["reason"] = "placeholder entity; rule retired in 15.1.0 (R8)"
    m = d["registry_metadata"]; m["version"] = f"{VER}-CLINICAL-CURATED"; m["last_updated"] = TODAY
    m["executable_rules"] = sum(1 for r in rules.values() if r.get("executable"))
    m["retired_rules"] = sum(1 for r in rules.values() if str(r.get("status", "")).startswith("retired"))
    m["evidence_tier_counts"] = dict(collections.Counter(r.get("evidence_tier") for r in rules.values()))
    m["changelog"] = [c for c in m.get("changelog", []) if c.get("version") != VER]
    m["changelog"].append({"version": VER, "date": TODAY, "protocol": "eval/registry_patches/PROTOCOL_15_0_0.md (applied unchanged)",
        "change": (f"Second fidelity patch. Retired: R7 {len(log['R7'])} arithmetic-tier artefacts (threshold = 1.5x/0.5x of the entity's own screening limit); "
                   f"R2a-wide {len(log['R2a'])} nonspecific single-analyte rules on clinical entities; R8 {len(log['R8'])} placeholder-entity rules; "
                   f"R9 {len(log['R9'])} impossible thresholds. No thresholds changed, no rules added. Executable rules {m['executable_rules']}.")})
    return log

def write(d, path):
    raw = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
    open(path, "wb").write(brotli.compress(raw, quality=11)); return hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    src_path = f"{ROOT}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
    d = json.loads(brotli.decompress(open(src_path, "rb").read()))
    assert d["registry_metadata"]["version"].startswith("15.0.0"), d["registry_metadata"]["version"]
    if "--dry-run" in sys.argv:
        cls = classify(d); print(collections.Counter(c for c, _ in cls.values()), len(cls))
        json.dump({rid: list(v) for rid, v in cls.items()}, open(f"{ROOT}/eval/registry_patches/review_15_1_0.json", "w"), indent=1)
        sys.exit(0)
    log = patch(d)
    d["registry_metadata"]["sha256_uncompressed"] = None
    sha = write(d, src_path)
    d["registry_metadata"]["sha256_uncompressed"] = sha
    for f in ["HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"]:
        write(d, f"{ROOT}/{f}")
        if os.path.exists(f"{ROOT}/tools/{f}"): shutil.copy2(f"{ROOT}/{f}", f"{ROOT}/tools/{f}")
    rel = f"{ROOT}/release/registry_{VER}"; os.makedirs(rel, exist_ok=True)
    shutil.copy2(src_path, f"{rel}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    if not os.path.lexists(f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br"):
        os.symlink("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br")
    h = hashlib.sha256(open(src_path, "rb").read()).hexdigest()
    open(f"{rel}/SHA256SUMS.txt", "w").write(f"{h}  HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br\n")
    summary = {k: len(v) for k, v in log.items()}; summary["rule_ids"] = dict(log)
    summary["retired_reason"] = {rid: d["rules"][rid]["retired_reason"] for v in log.values() for rid in v}
    json.dump(summary, open(f"{ROOT}/eval/registry_patches/review_15_1_0.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("rule_ids", "retired_reason")}, indent=1), "sha", sha)
