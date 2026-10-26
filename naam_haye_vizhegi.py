"""Canonical feature naming for the interpretation chain.

Lab systems, OCR output and hand-typed input all use short names (tsh, alt,
egfr, mcv, fps, fbs) while the registries and the Bayesian/fuzzy layers use the long
canonical ones (thyroid_stimulating_hormone, fasting_plasma_glucose, ...). Without a mapping the
observation is dropped in silence: no warning, no differential, no clue.

resolve() returns the canonical id when it recognises a name, otherwise
None so the caller can warn about a genuinely unknown feature instead of
pretending it was processed.
"""
from typing import Optional

# canonical id -> aliases
_ALIASES: dict[str, tuple[str, ...]] = {
    "thyroid_stimulating_hormone": ("tsh", "thyrotropin", "s_tsh"),
    "free_thyroxine": ("ft4", "free_t4", "t4_free", "freet4"),
    "free_triiodothyronine": ("ft3", "free_t3", "t3_free"),
    "thyroid_peroxidase_antibody": ("anti_tpo_antibody", "anti_tpo", "tpo_ab", "tpoab", "anti_tpo_ab"),

    "alanine_aminotransferase": ("alt", "sgpt", "gpt"),
    "aspartate_aminotransferase": ("ast", "sgot", "got"),
    "alkaline_phosphatase": ("alp", "alk_phos", "alkaline_phos"),
    "gamma_glutamyl_transferase": ("ggt", "gamma_gt", "ggtp"),
    "total_bilirubin": ("bilirubin", "bilirubin_total", "tbil", "t_bil"),
    "albumin": ("alb", "serum_albumin"),
    "international_normalized_ratio": ("inr",),

    "creatinine": ("cr", "scr", "serum_creatinine"),
    "egfr_ckd_epi_creatinine": ("egfr", "gfr", "ckd_epi", "egfr_ckdepi"),
    "urine_albumin_to_creatinine_ratio": ("uacr", "acr", "urine_acr",
                                      "albumin_creatinine_ratio",
                                      "urine_albumin_creatinine_ratio"),
    "cystatin_c": ("cystatin", "cys_c"),
    "blood_urea_nitrogen": ("bun",),
    "urea": ("serum_urea", "blood_urea"),

    "hemoglobin": ("hb", "hgb", "haemoglobin"),
    "hematocrit": ("hct", "pcv", "haematocrit"),
    "mean_corpuscular_volume": ("mcv",),
    "mean_corpuscular_hemoglobin": ("mch",),
    "red_cell_distribution_width_cv": ("rdw", "rdw_cv", "red_cell_distribution_width"),
    "platelet_count": ("platelets", "plt", "plat"),
    "white_blood_cell_count": ("wbc", "leukocytes", "wbcs"),
    "reticulocytes": ("retic", "reticulocyte_count", "retic_percent", "reticulocyte_percentage"),
    "absolute_reticulocyte_count": ("retic_abs", "absolute_retic"),
    "serum_iron": ("iron", "fe"),
    "ferritin": ("ferr", "s_ferritin"),
    "total_iron_binding_capacity": ("tibc",),
    "transferrin_saturation": ("tsat", "transferrin_sat"),
    "vitamin_b12": ("b12", "cobalamin"),
    "folate_serum": ("folate", "folic_acid", "serum_folate"),
    "haptoglobin_serum_quantitative": ("haptoglobin", "hapto", "serum_haptoglobin"),
    "lactate_dehydrogenase": ("ldh",),

    "fasting_plasma_glucose": ("fbs", "fps", "fpg", "fasting_glucose",
                               "fasting_blood_sugar", "fasting_sugar", "fasting_plasma_sugar"),
    "glucose": ("blood_glucose", "random_glucose", "bg"),
    "hemoglobin_a1c": ("hba1c", "a1c", "glycated_hemoglobin"),
    "fasting_serum_insulin": ("insulin", "fasting_insulin", "insulin_fasting"),

    "total_cholesterol": ("cholesterol", "tc", "chol"),
    "hdl_cholesterol": ("hdl", "hdl_c"),
    "ldl_cholesterol_calculated": ("ldl", "ldl_c", "ldl_cholesterol"),
    "triglycerides": ("tg", "trig"),

    "sodium": ("na",),
    "potassium": ("k",),
    "calcium_total": ("calcium", "ca", "total_calcium"),
    "phosphate": ("phosphorus", "po4", "phos"),
    "bicarbonate": ("hco3", "co2", "total_co2"),
    "magnesium": ("mg",),

    "c_reactive_protein": ("crp",),
    "high_sensitivity_c_reactive_protein": ("hscrp", "hs_crp", "hs_crp_cardio"),
    "erythrocyte_sedimentation_rate": ("esr", "sed_rate"),
    "procalcitonin": ("pct",),
    "lactate": ("lactic_acid",),
    "creatine_kinase_total": ("ck", "cpk", "creatine_kinase", "total_ck", "creatine_phosphokinase"),
    "creatine_kinase_mb": ("ck_mb", "ckmb", "ck_mb_mass"),
    "intact_parathyroid_hormone": ("pth", "ipth", "pth_intact", "parathormone"),
    "anti_tissue_transglutaminase_iga": ("ttg_iga", "anti_ttg", "ttg", "anti_ttg_iga", "tissue_transglutaminase_iga", "ttg_iga_antibody"),
    "body_mass_index": ("bmi",),
    "uric_acid": ("ua", "urate"),
    "25_hydroxy_vitamin_d": ("vitamin_d", "vit_d", "25_oh_vitamin_d", "vitamin_d_25oh", "vitd", "25_oh_d", "calcidiol"),
    # --- endocrine ---
    "morning_cortisol": ("cortisol", "am_cortisol", "cortisol_am", "serum_cortisol", "cortisol_8am_serum"),
    "salivary_cortisol_late_night": ("late_night_salivary_cortisol", "midnight_salivary_cortisol", "lnsc"),
    "cortisol_after_dexamethasone": ("dexamethasone_suppression_cortisol", "dst_cortisol", "post_dex_cortisol", "overnight_dst"),
    "urine_free_cortisol_24h": ("urine_free_cortisol", "ufc", "24h_ufc"),
    "adrenocorticotropic_hormone": ("acth", "corticotropin", "plasma_acth"),
    "aldosterone": ("plasma_aldosterone", "pac", "serum_aldosterone"),
    "plasma_renin_activity": ("pra", "renin_activity", "renin"),
    "aldosterone_renin_ratio": ("arr", "aldosterone_to_renin"),
    "prolactin": ("prl", "serum_prolactin"),
    "total_testosterone": ("testosterone", "serum_testosterone", "testosterone_total"),
    "sex_hormone_binding_globulin": ("shbg",),
    "dhea_sulfate": ("dheas", "dhea_s", "dhea_sulphate"),
    "17_hydroxyprogesterone": ("17_ohp", "17ohp", "seventeen_ohp"),
    "luteinizing_hormone": ("lh",),
    "follicle_stimulating_hormone": ("fsh",),
    "estradiol": ("e2", "oestradiol"),
    "growth_hormone": ("gh", "somatotropin"),
    "insulin_like_growth_factor_1": ("igf_1", "igf1", "somatomedin_c"),
    "c_peptide": ("cpeptide", "c_pep"),
    "total_thyroxine": ("t4", "total_t4", "tt4"),
    "total_triiodothyronine": ("t3", "total_t3", "tt3"),
    "thyroglobulin": ("tg_tumor_marker", "serum_thyroglobulin"),
    "thyroglobulin_antibody": ("anti_tg", "tgab", "anti_thyroglobulin"),
    "tsh_receptor_antibody": ("trab", "tsi", "tsh_receptor_ab", "thyrotropin_receptor_antibody"),
    "1_25_dihydroxy_vitamin_d": ("calcitriol", "1_25_oh2_d", "active_vitamin_d"),
    "human_chorionic_gonadotropin_quantitative": ("hcg", "beta_hcg", "b_hcg", "serum_hcg", "quantitative_hcg"),
    "anti_glutamic_acid_decarboxylase_65": ("gad65", "anti_gad", "gad_antibody", "gada"),
    # --- cardiac / muscle ---
    "troponin_i": ("troponin", "tni", "ctni", "trop_i", "cardiac_troponin_i"),
    "troponin_t": ("tnt", "ctnt", "trop_t", "cardiac_troponin_t"),
    "high_sensitivity_troponin_i": ("hs_tni", "hs_troponin_i", "hstni", "hs_ctni"),
    "high_sensitivity_troponin_t": ("hs_tnt", "hs_troponin_t", "hstnt", "hs_ctnt", "hs_troponin"),
    "nt_probnp": ("n_terminal_pro_b_type_natriuretic_peptide", "ntprobnp", "nt_pro_bnp", "pro_bnp"),
    "b_type_natriuretic_peptide": ("bnp", "brain_natriuretic_peptide"),
    "myoglobin": ("serum_myoglobin",),
    # --- haematology ---
    "red_blood_cell_count": ("rbc", "rbc_count", "erythrocytes", "red_cell_count"),
    "mean_corpuscular_hemoglobin_concentration": ("mchc",),
    "mean_platelet_volume": ("mpv",),
    "neutrophils_percent": ("neutrophils", "neut_percent", "neutrophil_percent", "segs", "pmn_percent"),
    "lymphocytes_percent": ("lymphocytes", "lymph_percent", "lymphocyte_percent"),
    "monocytes_percent": ("monocytes", "mono_percent", "monocyte_percent"),
    "eosinophils_percent": ("eosinophils", "eos_percent", "eosinophil_percent"),
    "basophils_percent": ("basophils", "baso_percent", "basophil_percent"),
    "neutrophil_count_absolute": ("anc", "abs_neutrophils", "neutrophils_absolute", "absolute_neutrophils"),
    "lymphocyte_count_absolute": ("alc", "abs_lymphocytes", "lymphocytes_absolute", "absolute_lymphocyte_count"),
    "eosinophil_count_absolute": ("aec", "abs_eosinophils", "absolute_eosinophil_count"),
    "blasts_percent": ("blasts", "blast_percent", "peripheral_blasts"),
    "schistocytes_percent": ("schistocytes", "fragmented_red_cells", "schistocyte_percent"),
    "prothrombin_time": ("pt", "pt_seconds"),
    "activated_partial_thromboplastin_time": ("aptt", "ptt", "apt_time"),
    "fibrinogen": ("fib", "clauss_fibrinogen"),
    "fibrin_degradation_products": ("fdp", "fsp"),
    "d_dimer": ("ddimer", "d_dimer_quantitative"),
    "lactate_dehydrogenase": ("ld",),
    "g6pd_enzyme_activity": ("g6pd", "g6pd_activity"),
    "direct_bilirubin": ("conjugated_bilirubin", "dbil", "d_bil", "bilirubin_direct"),
    "indirect_bilirubin": ("unconjugated_bilirubin", "ibil", "bilirubin_indirect"),
    "serum_free_kappa_light_chains": ("kappa_flc", "free_kappa", "kappa_free_light_chain", "serum_free_kappa", "free_light_chain_kappa"),
    "serum_free_lambda_light_chains": ("lambda_flc", "free_lambda", "lambda_free_light_chain", "serum_free_lambda", "free_light_chain_lambda"),
    "free_light_chain_ratio": ("kappa_lambda_ratio", "flc_ratio", "kappa_to_lambda_ratio", "k_l_ratio"),
    "serum_protein_electrophoresis_m_spike": ("m_spike", "m_protein", "paraprotein", "spep_m_spike", "monoclonal_protein"),
    "total_immunoglobulin_g": ("igg", "immunoglobulin_g"),
    "total_immunoglobulin_a": ("iga", "immunoglobulin_a"),
    "total_immunoglobulin_m": ("igm", "immunoglobulin_m"),
    "total_immunoglobulin_e": ("ige", "immunoglobulin_e", "total_ige"),
    # --- chemistry / renal / gas ---
    "chloride": ("cl",),
    "total_protein": ("tp", "protein_total", "serum_total_protein"),
    "globulin": ("glob", "serum_globulin"),
    "lipase": ("serum_lipase",),
    "amylase": ("serum_amylase",),
    "ammonia": ("nh3", "plasma_ammonia_level"),
    "arterial_ph": ("ph", "blood_ph", "abg_ph"),
    "arterial_pco2": ("pco2", "paco2"),
    "arterial_po2": ("po2", "pao2"),
    "base_excess": ("be", "base_deficit"),
    "calcium_ionized": ("ionized_calcium", "ica", "ca_ion", "free_calcium"),
    "serum_osmolality": ("osmolality", "serum_osm", "osmolality_serum"),
    "urine_osmolality": ("uosm", "urine_osm"),
    "urine_sodium": ("una", "urine_na", "spot_urine_sodium"),
    "urine_albumin": ("microalbumin", "urine_microalbumin", "ualb"),
    "urine_protein_to_creatinine_ratio": ("upcr", "pcr_urine", "protein_creatinine_ratio", "urine_pcr"),
    "urine_protein_24_hour": ("24h_urine_protein", "urine_protein_24h", "proteinuria_24h"),
    "urine_creatinine": ("ucr", "creatinine_urine"),
    "beta_hydroxybutyrate": ("bhb", "ketones_blood", "blood_ketones", "b_hydroxybutyrate", "3_hydroxybutyrate"),
    "urine_ketones_qualitative": ("urine_ketones_dipstick", "ketonuria"),
    "glucose_random": ("rbs", "random_blood_sugar", "random_blood_glucose", "rpg"),
    "glucose_2_hour_postprandial": ("2hpp", "ppbs", "postprandial_glucose", "2h_glucose", "ogtt_2h"),
    "total_carbon_dioxide": ("tco2", "carbon_dioxide"),
    # --- inflammation / immunology / infection ---
    "antinuclear_antibody_screen": ("ana", "ana_screen", "antinuclear_antibody"),
    "double_stranded_dna_antibody": ("anti_dsdna", "dsdna", "ds_dna"),
    "rheumatoid_factor": ("rf", "ra_factor", "rheumatoid_factor_igm"),
    "cyclic_citrullinated_peptide_antibody": ("anti_ccp", "ccp", "accp", "anti_ccp_igg"),
    "complement_c3": ("c3",),
    "complement_c4": ("c4",),
    "anca_screen": ("anca",),
    "hepatitis_b_surface_antigen": ("hbsag", "hbs_ag"),
    "hepatitis_b_surface_antibody": ("anti_hbs", "hbsab"),
    "hepatitis_b_core_total_antibody": ("anti_hbc", "hbcab", "anti_hbc_total"),
    "hepatitis_b_core_igm_antibody": ("anti_hbc_igm", "hbc_igm"),
    "hepatitis_b_e_antigen": ("hbeag",),
    "hepatitis_c_antibody": ("anti_hcv", "hcv_ab", "hcv_antibody"),
    "hepatitis_a_igm_antibody": ("hav_igm", "anti_hav_igm", "hepatitis_a_igm"),
    "hiv_1_and_hiv_2_antigen_antibody": ("hiv", "hiv_ag_ab", "hiv_combo", "hiv_4th_generation", "hiv_screen"),
    "helicobacter_pylori_stool_antigen": ("h_pylori_stool_antigen", "hpsa"),
    "helicobacter_pylori_igg_antibody": ("h_pylori_igg", "h_pylori_antibody"),
    "epstein_barr_vca_igm_antibody": ("ebv_vca_igm", "ebv_igm"),
    "cytomegalovirus_igm_antibody": ("cmv_igm",),
    # --- tumour markers / toxicology / nutrition ---
    "total_prostate_specific_antigen": ("psa", "total_psa", "prostate_specific_antigen"),
    "free_prostate_specific_antigen": ("free_psa", "fpsa"),
    "carcinoembryonic_antigen": ("cea",),
    "alpha_fetoprotein": ("afp",),
    "ca_125": ("ca125", "cancer_antigen_125"),
    "ethanol": ("alcohol", "blood_alcohol", "etoh"),
    "acetaminophen": ("paracetamol", "apap"),
    "salicylate": ("aspirin_level", "asa_level"),
    "valproic_acid_total": ("valproate", "valproic_acid", "vpa"),
    "phenytoin_total": ("phenytoin", "dilantin"),
    "ceruloplasmin": ("serum_ceruloplasmin", "ceruloplasmin_serum"),
    "copper": ("serum_copper", "cu"),
    "zinc": ("zn", "serum_zinc"),
    "lead": ("blood_lead", "pb", "lead_blood"),
    "alpha_1_antitrypsin_serum": ("alpha_1_antitrypsin", "a1at", "aat"),
    "vitamin_b1_thiamine": ("thiamine", "vitamin_b1", "b1"),
    "vitamin_b6_pyridoxal_five_phosphate": ("vitamin_b6", "pyridoxine", "plp", "b6"),
    "vitamin_a_retinol_serum": ("vitamin_a", "retinol"),
    "vitamin_e_alpha_tocopherol_serum": ("vitamin_e", "alpha_tocopherol"),
    "homeostatic_model_assessment_insulin_resistance": ("homa_ir", "homa"),
    "neutrophil_to_lymphocyte_ratio_nlr": ("nlr", "neutrophil_to_lymphocyte_ratio", "neutrophil_lymphocyte_ratio"),
    "blood_urea_nitrogen_to_creatinine_ratio": ("bun_to_creatinine_ratio", "bun_cr_ratio", "bun_creatinine_ratio"),
    "corrected_calcium_for_serum_albumin": ("corrected_calcium", "albumin_corrected_calcium", "adjusted_calcium"),
    "cholesterol_hdl_ratio": ("total_to_hdl_ratio", "tc_hdl_ratio", "chol_hdl_ratio"),
    "non_hdl_cholesterol": ("non_hdl", "nonhdl"),
    "lipoprotein_a": ("lp_a", "lpa", "lipoprotein_little_a"),
    "apolipoprotein_b": ("apob", "apo_b"),
    "apolipoprotein_a1": ("apoa1", "apo_a1"),
}


# flat alias -> canonical, built once
_LOOKUP: dict[str, str] = {}
for _canon, _alts in _ALIASES.items():
    _LOOKUP[_canon] = _canon
    for _a in _alts:
        # a collision would silently reroute a feature, so fail loudly here
        if _a in _LOOKUP and _LOOKUP[_a] != _canon:
            raise ValueError(f"alias {_a!r} claimed by two features")
        _LOOKUP[_a] = _canon


def _key(name: str) -> str:
    out = []
    for ch in str(name).strip().lower():
        out.append(ch if ch.isalnum() else "_")
    k = "".join(out)
    while "__" in k:
        k = k.replace("__", "_")
    return k.strip("_")


_REGISTRY_LOOKUP: Optional[dict[str, str]] = None
_MIN_REGISTRY_TOKEN = 5  # short tokens (hb, ca, k) are too ambiguous in the AI-built synonym lists


def _registry_lookup() -> dict[str, str]:
    """Unambiguous synonyms harvested from the feature registry (lazy, cached).

    The registry's terminology blocks were AI-generated and are noisy (the
    token "hb" is claimed by carboxyhaemoglobin, fetal haemoglobin, ...), so
    only tokens that map to exactly ONE feature and are at least
    `_MIN_REGISTRY_TOKEN` characters long are accepted. Curated aliases above
    always win.
    """
    global _REGISTRY_LOOKUP
    if _REGISTRY_LOOKUP is not None:
        return _REGISTRY_LOOKUP
    table: dict[str, set] = {}
    try:
        import os
        import cache_registry
        here = os.path.dirname(os.path.abspath(__file__))
        reg = cache_registry.bargozari_registry(
            os.path.join(here, "HEMOGLYPH_FEATURE_REGISTRY.json.br"))
        features = reg.get("features") or {}
        for fid, feat in features.items():
            if not isinstance(feat, dict):
                continue
            term = feat.get("terminology") or {}
            ident = feat.get("identity") or {}
            names: set = set()
            syn = term.get("synonyms") or {}
            if isinstance(syn, dict):
                for lst in syn.values():
                    names.update(str(x) for x in (lst or []))
            pref = term.get("preferred") or {}
            if isinstance(pref, dict):
                names.update(str(x) for x in pref.values() if x)
            names.update(str(x) for x in (term.get("abbreviations") or []))
            names.update(str(x).lstrip("#") for x in (term.get("ocr_variants") or []))
            for k in ("short_name", "canonical_name", "display_name"):
                if ident.get(k):
                    names.add(str(ident[k]))
            for n in names:
                k = _key(n)
                if len(k) >= _MIN_REGISTRY_TOKEN:
                    table.setdefault(k, set()).add(fid)
    except Exception:
        table = {}
    _REGISTRY_LOOKUP = {k: next(iter(v)) for k, v in table.items()
                        if len(v) == 1 and k not in _LOOKUP}
    return _REGISTRY_LOOKUP


def resolve(name: str, known: Optional[set] = None) -> Optional[str]:
    """Canonical id for `name`, or None if unrecognised.

    `known` is the set of ids the caller can actually act on (registry
    features plus whatever the inner layers understand). When supplied, a
    canonical name is only returned if it is in that set, so we never
    rename an observation into something nothing consumes.
    """
    k = _key(name)
    if known and k in known:
        return k
    hit = _LOOKUP.get(k)
    if hit is None:
        hit = _registry_lookup().get(k)
    if hit is None:
        return None
    if known and hit not in known:
        return None
    return hit


def all_known() -> set:
    return set(_LOOKUP)
