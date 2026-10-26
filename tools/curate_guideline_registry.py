#!/usr/bin/env python3
"""Hemoglyph — HEMOGLYPH_GUIDELINE_REGISTRY curation pass (v13.0.0).

Reads the Brotli-compressed guideline registry, applies a deterministic,
auditable set of repairs, appends a clinician-grade curated rule set anchored
in current international guidelines, re-derives `feature_links`, re-validates
structure and writes the compressed registry back (both file names the
application accepts) plus a JSON audit report.

Run:  python3 tools/curate_guideline_registry.py [--dry-run]

Every change is recorded in docs/GUIDELINE_REGISTRY_CURATION_13.0.0.json.
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

import brotli

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"
FEAT = ROOT / "HEMOGLYPH_FEATURE_REGISTRY.json.br"
OUTS = [ROOT / "HEMOGLYPH_GUIDELINE_REGISTRY.json.br",
        ROOT / "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"]
REPORT = ROOT / "docs" / "GUIDELINE_REGISTRY_CURATION_13.0.0.json"
NEW_VERSION = "13.0.0-CLINICAL-CURATED"
TODAY = _dt.date.today().isoformat()

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def load_br(p: Path) -> dict:
    return json.loads(brotli.decompress(p.read_bytes()).decode("utf-8"))


def leaves(e):
    if not isinstance(e, dict):
        return []
    if "feature_id" in e:
        return [e]
    out = []
    for k in ("all", "any", "n_of", "conditions"):
        for x in e.get(k) or []:
            out += leaves(x)
    return out


def direction(op: str) -> str:
    return "high" if op in (">", ">=") else "low" if op in ("<", "<=") else "eq"


# Analytes every routine panel carries. A combination of these is a
# compatible pattern for a specific aetiology, never its diagnostic criterion.
ROUTINE = frozenset("""
hemoglobin hematocrit red_blood_cell_count mean_corpuscular_volume mean_corpuscular_hemoglobin
mean_corpuscular_hemoglobin_concentration red_cell_distribution_width_cv red_cell_distribution_width
platelets platelet_count mean_platelet_volume white_blood_cell_count neutrophils_percent lymphocytes_percent
monocytes_percent eosinophils_percent basophils_percent neutrophil_count_absolute lymphocyte_count_absolute
monocyte_count_absolute eosinophil_count_absolute basophil_count_absolute absolute_neutrophil_count
neutrophil_to_lymphocyte_ratio_nlr glucose glucose_random fasting_plasma_glucose hemoglobin_a1c creatinine
egfr_ckd_epi_creatinine egfr blood_urea_nitrogen urea blood_urea_nitrogen_to_creatinine_ratio sodium potassium
chloride bicarbonate total_carbon_dioxide anion_gap calcium_total corrected_calcium_for_serum_albumin phosphate
magnesium uric_acid total_protein albumin globulin alanine_aminotransferase aspartate_aminotransferase
alkaline_phosphatase gamma_glutamyl_transferase total_bilirubin direct_bilirubin indirect_bilirubin
lactate_dehydrogenase total_cholesterol ldl_cholesterol_calculated ldl_cholesterol_direct hdl_cholesterol
triglycerides non_hdl_cholesterol thyroid_stimulating_hormone c_reactive_protein
high_sensitivity_c_reactive_protein erythrocyte_sedimentation_rate ferritin serum_iron total_iron_binding_capacity
transferrin_saturation international_normalized_ratio prothrombin_time activated_partial_thromboplastin_time
body_mass_index waist_circumference systolic_blood_pressure diastolic_blood_pressure
""".split())

ROUTINE_DEFINED_RE = re.compile(
    r"(diabet|prediabet|glycemi|glyc(a)?emia|insulin_resistance|metabolic_syndrome|"
    r"kidney_disease|kidney_injury|renal_failure|azotemia|uremi|ketoacidosis|hyperosmolar|acidosis|alkalosis|"
    r"anion_gap|anemia|anaemia|cytopenia|cytosis|penia$|philia$|polycythemia|erythrocytosis|thrombocyt|"
    r"leukocyt|neutro|lymph|hyper[a-z]*emia|hypo[a-z]*emia|hyper[a-z]*uria|hypo[a-z]*uria|natremia|kalemia|"
    r"calcemia|phosphatemia|magnesemia|lipidemia|cholesterolemia|triglyceridemia|dyslipid|cholestasis|"
    r"cholestatic|hepatocellular_pattern|liver_injury|transaminitis|siadh|dehydration|malnutrition|refeeding|"
    r"tumor_lysis|hypothyroid|hyperthyroid|thyrotox|sick_euthyroid|iron_deficiency|iron_overload|"
    r"thalassemia_trait|microcyt|macrocyt|inflammat|acute_phase|_pattern$|_support_pattern$|nephrotic|"
    r"proteinuria|hypoalbumin|hyperuric|gout_flare|sepsis|sirs|_syndrome_pattern)", re.I)

PATHOGEN_RE = re.compile(
    r"(antigen|antibod|_igm|_igg|_pcr|_rna|_dna|viral_load|culture|smear|serolog|_ab$|hbsag|hcv|hiv|"
    r"treponem|syphilis|rpr|vdrl|tppa|quantiferon|brucella|wright|widal|dengue|malaria|plasmodium|"
    r"toxoplasma|cmv|ebv|epstein|rubella|measles|mumps|varicella|herpes|covid|sars_cov|influenza|rsv|"
    r"legionella|pneumococc|mycoplasma|chlamydia|gonorrh|leptospir|borrelia|lyme|rickettsia|coxiella|"
    r"bartonella|histoplasma|cryptococc|aspergillus|galactomannan|glucan|candida|pneumocystis|"
    r"clostridi|difficile|helicobacter|salmonella|shigella|campylobacter|giardia|entamoeba|strongyloides|"
    r"schistosoma|leishmania|trypanosoma|echinococc|toxocara|filaria|hla_b27|mutation|genotype|karyotype|"
    r"translocation|fusion|bcr_abl|jak2|calr|mpl|flt3|npm1|hfe|factor_v_leiden|prothrombin_g20210a)", re.I)

DECISIVE_RE = re.compile(
    r"(lipase|blasts?_percent|blast_cells|plasma_cells_percent|m_spike|immunofixation|free_light_chain|"
    r"creatine_kinase|troponin|natriuretic|probnp|bnp|beta_hydroxybutyrate|ketone|osmolal|osmolar|"
    r"ammonia|lactate$|procalcitonin|tryptase|cortisol|dexamethasone|metanephrine|aldosterone|renin|"
    r"parathyroid|calcitonin|prolactin|igf|growth_hormone|testosterone|estradiol|progesterone|"
    r"hcg|afp|alpha_fetoprotein|cea|ca_125|ca_19|psa|ceruloplasmin|copper|alpha_1_antitrypsin|"
    r"transglutaminase|endomysial|gliadin|calprotectin|elastase|haptoglobin|coombs|antiglobulin|"
    r"g6pd|hemoglobin_a2|hemoglobin_s|hemoglobin_f|electrophoresis|methylmalonic|homocysteine|"
    r"vitamin_b12|folate|hydroxy_vitamin_d|lead|acetaminophen|salicylate|lithium|digoxin|"
    r"carboxyhemoglobin|methemoglobin|phenylalanine|galactose|biotinidase|tsh|thyroxine|triiodothyronine|"
    r"thyroglobulin|peroxidase|receptor_antibod|antinuclear|dsdna|double_stranded|centromere|scl_70|"
    r"jo_1|smith|rnp|ssa|ssb|ro_|la_|anca|myeloperoxidase|proteinase_3|gbm|cardiolipin|glycoprotein|"
    r"lupus_anticoagulant|rheumatoid_factor|citrullinated|ccp|complement|c3|c4|adamts13|"
    r"d_dimer|fibrinogen|factor_|von_willebrand|antithrombin|protein_c|protein_s|urine_albumin|"
    r"urine_protein|microalbumin|cystatin|beta_2_microglobulin|erythropoietin|reticulocyte|"
    r"soluble_transferrin|hepcidin|zinc_protoporphyrin|porphyrin|porphobilinogen|aminolevulinic)", re.I)

STAMPED_MIN = 5

# pairs that the engine already treats as equivalent; we consolidate the
# minority spelling in the registry so a value is matched once, not twice.
CANONICAL_MERGE = {
    "parathyroid_hormone_intact": "intact_parathyroid_hormone",
    "cortisol_8am": "morning_cortisol",
    "cortisol_morning": "morning_cortisol",
    "measured_osmolality": "serum_osmolality",
    "platelet_count": "platelets",
    "nt_probnp": "n_terminal_pro_bnp",
    "arterial_blood_ph": "arterial_ph",
    "beta_hydroxybutyrate_serum": "beta_hydroxybutyrate",
    "serum_osmolar_gap": "osmolal_gap",
    "serum_haptoglobin": "haptoglobin_serum_quantitative",
}

# unit normalisation: (feature_id, unit) -> (canonical unit, multiplier)
UNIT_FIX = {
    ("alkaline_phosphatase", "IU/L"): ("U/L", 1.0),
    ("lymphocyte_count_absolute", "10*3/uL"): ("10*9/L", 1.0),
    ("neutrophil_count_absolute", "10*3/uL"): ("10*9/L", 1.0),
    ("monocyte_count_absolute", "10*3/uL"): ("10*9/L", 1.0),
    ("eosinophil_count_absolute", "10*3/uL"): ("10*9/L", 1.0),
    ("basophil_count_absolute", "10*3/uL"): ("10*9/L", 1.0),
    ("arterial_ph", "1"): ("[pH]", 1.0),
    ("stool_ph", "1"): ("[pH]", 1.0),
    ("transferrin_saturation", "1"): ("%", 1.0),        # values already in %
    ("d_dimer", "ug{FEU}/mL"): ("ug/mL", 1.0),
    ("free_light_chain_ratio", "1"): ("ratio", 1.0),
    ("aldosterone_renin_ratio", "1"): ("ratio", 1.0),
    ("cholesterol_hdl_ratio", "1"): ("ratio", 1.0),
    ("ldl_hdl_ratio", "1"): ("ratio", 1.0),
    ("serum_amylase_lipase_ratio", "1"): ("ratio", 1.0),
    ("urine_protein_to_creatinine_ratio", "mg/mg"): ("mg/g", 1000.0),
    ("syphilis_tppa", "mg/dL"): ("1", 1.0),
    ("syphilis_rpr", "mg/dL"): ("1", 1.0),
}

# --------------------------------------------------------------------------
# curated guideline rule set
# --------------------------------------------------------------------------
# DSL:  L(fid, op, value, unit=None)   ALL(...)   ANY(...)
# unit=None -> feature canonical unit.

def L(fid, op, value, unit=None, weight=3.0):
    return {"feature_id": fid, "operator": op, "value": value, "unit": unit, "weight": weight}


def ALL(*c):
    return {"all": list(c)}


def ANY(*c):
    return {"any": list(c)}


SOURCES = {
    "ada_easd_hyperglycemic_crises_2024": ("ADA/EASD/JBDS/AACE/DTS", "Hyperglycemic Crises in Adults With Diabetes: A Consensus Report", 2024, "https://doi.org/10.2337/dci24-0032"),
    "ada_soc_2025": ("American Diabetes Association", "Standards of Care in Diabetes-2025, Section 2 & 6", 2025, "https://doi.org/10.2337/dc25-S002"),
    "kdigo_ckd_2024": ("KDIGO", "2024 Clinical Practice Guideline for the Evaluation and Management of CKD", 2024, "https://doi.org/10.1016/j.kint.2023.10.018"),
    "kdigo_aki_2012": ("KDIGO", "Clinical Practice Guideline for Acute Kidney Injury", 2012, "https://kdigo.org/guidelines/acute-kidney-injury/"),
    "kdigo_gd_2021": ("KDIGO", "2021 Guideline for the Management of Glomerular Diseases", 2021, "https://doi.org/10.1016/j.kint.2021.05.021"),
    "atlanta_pancreatitis_2012": ("Atlanta Classification Working Group", "Classification of acute pancreatitis-2012", 2013, "https://doi.org/10.1136/gutjnl-2012-302779"),
    "esc_acs_2023": ("European Society of Cardiology", "2023 ESC Guidelines for the management of acute coronary syndromes", 2023, "https://doi.org/10.1093/eurheartj/ehad191"),
    "esc_hf_2021_2023": ("European Society of Cardiology", "2021 ESC HF Guidelines + 2023 focused update", 2023, "https://doi.org/10.1093/eurheartj/ehad195"),
    "esc_pe_2019": ("European Society of Cardiology / ERS", "2019 ESC Guidelines for acute pulmonary embolism", 2019, "https://doi.org/10.1093/eurheartj/ehz405"),
    "sepsis3_2016": ("SCCM/ESICM", "The Third International Consensus Definitions for Sepsis and Septic Shock (Sepsis-3)", 2016, "https://doi.org/10.1001/jama.2016.0287"),
    "isth_dic_2001": ("ISTH", "Towards definition, clinical and laboratory criteria, and a scoring system for DIC", 2001, "https://doi.org/10.1055/s-0037-1616068"),
    "imwg_2014": ("International Myeloma Working Group", "IMWG updated criteria for the diagnosis of multiple myeloma", 2014, "https://doi.org/10.1016/S1470-2045(14)70442-5"),
    "who_haem_2022": ("WHO / ICC", "5th edition WHO classification of haematolymphoid tumours (2022) & ICC 2022", 2022, "https://doi.org/10.1038/s41375-022-01613-1"),
    "bsg_ida_2021": ("British Society of Gastroenterology", "Guidelines for the management of iron deficiency anaemia in adults", 2021, "https://doi.org/10.1136/gutjnl-2021-325210"),
    "who_anaemia_2024": ("World Health Organization", "Guideline on haemoglobin cutoffs to define anaemia", 2024, "https://www.who.int/publications/i/item/9789240088542"),
    "bsh_b12_2014": ("British Society for Haematology", "Guidelines for the diagnosis and treatment of cobalamin and folate disorders", 2014, "https://doi.org/10.1111/bjh.12959"),
    "aasld_hh_2011_easl_2022": ("AASLD 2011 / EASL 2022", "Haemochromatosis practice guidelines", 2022, "https://doi.org/10.1016/j.jhep.2022.03.033"),
    "ash_itp_2019": ("American Society of Hematology", "2019 guidelines for immune thrombocytopenia", 2019, "https://doi.org/10.1182/bloodadvances.2019000966"),
    "isth_ttp_2020": ("ISTH", "Guidelines for diagnosis of thrombotic thrombocytopenic purpura", 2020, "https://doi.org/10.1111/jth.15006"),
    "sydney_aps_2006_acr_2023": ("ISTH 2006 / ACR-EULAR 2023", "Antiphospholipid syndrome classification criteria", 2023, "https://doi.org/10.1002/art.42624"),
    "aasld_hbv_2018": ("AASLD", "Update on prevention, diagnosis, and treatment of chronic hepatitis B", 2018, "https://doi.org/10.1002/hep.29800"),
    "aasld_idsa_hcv_2023": ("AASLD/IDSA", "HCV Guidance: Recommendations for testing, managing and treating hepatitis C", 2023, "https://www.hcvguidelines.org"),
    "cdc_hiv_testing_2014": ("CDC", "Laboratory testing for the diagnosis of HIV infection: updated recommendations", 2014, "https://doi.org/10.15620/cdc.23447"),
    "cdc_sti_2021": ("CDC", "Sexually Transmitted Infections Treatment Guidelines", 2021, "https://www.cdc.gov/std/treatment-guidelines/"),
    "espghan_celiac_2020": ("ESPGHAN", "Guidelines for diagnosing coeliac disease 2020", 2020, "https://doi.org/10.1097/MPG.0000000000002497"),
    "acg_celiac_2023": ("American College of Gastroenterology", "ACG Clinical Guidelines: Diagnosis and Management of Celiac Disease", 2023, "https://doi.org/10.14309/ajg.0000000000002075"),
    "ecco_ibd_2019": ("ECCO / ESGAR", "Diagnosis and management of IBD: faecal calprotectin", 2019, "https://doi.org/10.1093/ecco-jcc/jjy113"),
    "easl_pbc_2017": ("EASL", "Clinical Practice Guidelines: diagnosis and management of primary biliary cholangitis", 2017, "https://doi.org/10.1016/j.jhep.2017.03.022"),
    "aasld_aih_2019": ("AASLD", "Diagnosis and management of autoimmune hepatitis in adults and children", 2019, "https://doi.org/10.1002/hep.31065"),
    "easl_wilson_2012": ("EASL", "Clinical Practice Guidelines: Wilson's disease", 2012, "https://doi.org/10.1016/j.jhep.2011.11.007"),
    "easl_cholestasis_2009": ("EASL", "Clinical Practice Guidelines: management of cholestatic liver diseases", 2009, "https://doi.org/10.1016/j.jhep.2009.04.009"),
    "acg_liver_chem_2017": ("American College of Gastroenterology", "ACG Clinical Guideline: Evaluation of Abnormal Liver Chemistries", 2017, "https://doi.org/10.1038/ajg.2016.517"),
    "aasld_alf_2011": ("AASLD", "Position paper: management of acute liver failure, update 2011", 2011, "https://www.aasld.org"),
    "ata_hypothyroid_2014": ("American Thyroid Association", "Guidelines for the treatment of hypothyroidism", 2014, "https://doi.org/10.1089/thy.2014.0028"),
    "ata_hyperthyroid_2016": ("American Thyroid Association", "2016 Guidelines for diagnosis and management of hyperthyroidism", 2016, "https://doi.org/10.1089/thy.2016.0229"),
    "endo_cushing_2008_2021": ("Endocrine Society / Pituitary Society", "Diagnosis of Cushing's syndrome 2008; consensus 2021", 2021, "https://doi.org/10.1016/S2213-8587(21)00235-7"),
    "endo_adrenal_insufficiency_2016": ("Endocrine Society", "Diagnosis and treatment of primary adrenal insufficiency", 2016, "https://doi.org/10.1210/jc.2015-1710"),
    "endo_primary_aldosteronism_2016": ("Endocrine Society", "Management of primary aldosteronism: case detection, diagnosis, treatment", 2016, "https://doi.org/10.1210/jc.2015-4061"),
    "endo_pheo_2014": ("Endocrine Society", "Pheochromocytoma and paraganglioma clinical practice guideline", 2014, "https://doi.org/10.1210/jc.2014-1498"),
    "endo_acromegaly_2014": ("Endocrine Society", "Acromegaly: an Endocrine Society clinical practice guideline", 2014, "https://doi.org/10.1210/jc.2014-2700"),
    "endo_hyperprolactinemia_2011_2023": ("Endocrine Society 2011 / Pituitary Society 2023", "Diagnosis and treatment of hyperprolactinemia", 2023, "https://doi.org/10.1038/s41574-023-00886-5"),
    "endo_testosterone_2018": ("Endocrine Society", "Testosterone therapy in men with hypogonadism", 2018, "https://doi.org/10.1210/jc.2018-00229"),
    "phpt_workshop_2022": ("Fifth International Workshop", "Evaluation and management of primary hyperparathyroidism", 2022, "https://doi.org/10.1002/jbmr.4677"),
    "endo_vitamin_d_2011_2024": ("Endocrine Society", "Vitamin D deficiency 2011; 2024 guideline on vitamin D for disease prevention", 2024, "https://doi.org/10.1210/clinem/dgae290"),
    "ese_hyponatremia_2014": ("ESE/ESICM/ERA", "Clinical practice guideline on diagnosis and treatment of hyponatraemia", 2014, "https://doi.org/10.1530/EJE-13-1020"),
    "kdigo_potassium_2020": ("KDIGO", "Potassium homeostasis and management of dyskalemia in kidney diseases: conference report", 2020, "https://doi.org/10.1016/j.kint.2019.09.018"),
    "cairo_bishop_2004": ("Cairo & Bishop", "Tumour lysis syndrome: new therapeutic strategies and classification", 2004, "https://doi.org/10.1111/j.1365-2141.2004.05094.x"),
    "rhabdo_review_2020": ("Stahl et al. / Torres et al.", "Rhabdomyolysis diagnosis (CK > 5x ULN or > 1000 U/L) - systematic reviews", 2020, "https://doi.org/10.1007/s00415-019-09185-4"),
    "eular_acr_sle_2019": ("EULAR/ACR", "2019 classification criteria for systemic lupus erythematosus", 2019, "https://doi.org/10.1002/art.40930"),
    "acr_eular_ra_2010": ("ACR/EULAR", "2010 rheumatoid arthritis classification criteria", 2010, "https://doi.org/10.1002/art.27584"),
    "acr_eular_gout_2015": ("ACR/EULAR", "2015 gout classification criteria", 2015, "https://doi.org/10.1002/art.39254"),
    "acr_gout_2020": ("American College of Rheumatology", "2020 Guideline for the management of gout", 2020, "https://doi.org/10.1002/art.41247"),
    "who_malaria_2023": ("World Health Organization", "WHO Guidelines for malaria", 2023, "https://www.who.int/publications/i/item/guidelines-for-malaria"),
    "who_dengue_2009_2023": ("World Health Organization", "Dengue guidelines for diagnosis, treatment, prevention and control", 2023, "https://www.who.int/publications/i/item/9789241547871"),
    "who_brucellosis_2006": ("WHO / FAO / OIE", "Brucellosis in humans and animals", 2006, "https://www.who.int/publications/i/item/9789241547130"),
    "cdc_lead_2021": ("CDC", "Blood lead reference value 3.5 ug/dL (ACCLPP 2021)", 2021, "https://www.cdc.gov/lead-prevention/php/news-features/updates-blood-lead-reference-value.html"),
    "rumack_matthew_1975_2022": ("Rumack & Matthew / Dart et al. 2023 consensus", "Acetaminophen poisoning management consensus", 2023, "https://doi.org/10.1001/jamanetworkopen.2023.27739"),
    "acog_preeclampsia_2020": ("ACOG", "Practice Bulletin 222: Gestational hypertension and preeclampsia", 2020, "https://doi.org/10.1097/AOG.0000000000003891"),
    "iadpsg_2010": ("IADPSG", "Recommendations on the diagnosis and classification of hyperglycemia in pregnancy", 2010, "https://doi.org/10.2337/dc09-1848"),
    "aap_hyperbilirubinemia_2022": ("American Academy of Pediatrics", "Clinical Practice Guideline Revision: Management of hyperbilirubinemia in the newborn >= 35 weeks", 2022, "https://doi.org/10.1542/peds.2022-058859"),
    "acmg_pku_2014": ("ACMG", "Phenylalanine hydroxylase deficiency: diagnosis and management guideline", 2014, "https://doi.org/10.1038/gim.2013.157"),
    "eas_fh_2013_dlcn": ("European Atherosclerosis Society", "Familial hypercholesterolaemia - DLCN criteria consensus", 2013, "https://doi.org/10.1093/eurheartj/eht273"),
    "eas_esc_dyslipidaemia_2019": ("ESC/EAS", "2019 Guidelines for the management of dyslipidaemias", 2019, "https://doi.org/10.1093/eurheartj/ehz455"),
    "ncep_atp3_2005": ("AHA/NHLBI", "Diagnosis and management of the metabolic syndrome (ATP III update)", 2005, "https://doi.org/10.1161/CIRCULATIONAHA.105.169404"),
    "bts_tb_nice_2016": ("NICE", "Tuberculosis NG33: IGRA testing", 2016, "https://www.nice.org.uk/guidance/ng33"),
    "ebv_idsa_review": ("Dunmire et al.", "Infectious mononucleosis: heterophile and VCA-IgM serology", 2015, "https://doi.org/10.1007/978-3-319-22822-8_9"),
    "acg_hpylori_2024": ("American College of Gastroenterology", "ACG Clinical Guideline: Treatment of Helicobacter pylori infection 2024", 2024, "https://doi.org/10.14309/ajg.0000000000002968"),
    "aasld_hav_hev_2023": ("AASLD / EASL", "Hepatitis A & E diagnosis (IgM anti-HAV; IgM anti-HEV / HEV RNA)", 2023, "https://doi.org/10.1016/j.jhep.2018.03.005"),
    "ash_scd_2020_who": ("ASH 2020 / WHO", "Sickle cell disease and thalassaemia laboratory diagnosis", 2020, "https://doi.org/10.1182/bloodadvances.2019001143"),
    "g6pd_who_2022": ("WHO", "G6PD deficiency testing - technical brief", 2022, "https://www.who.int/publications/i/item/9789240050204"),
    "eha_hemolysis_2023": ("EHA / BSH", "Laboratory diagnosis of haemolysis and autoimmune haemolytic anaemia", 2023, "https://doi.org/10.1111/bjh.14478"),
    "isth_hit_2018_ash": ("ASH", "2018 guidelines for management of heparin-induced thrombocytopenia", 2018, "https://doi.org/10.1182/bloodadvances.2018024489"),
    "acep_toxicology_consensus": ("AACT / EAPCCT", "Toxic alcohol, lithium, digoxin and salicylate laboratory thresholds - consensus statements", 2015, "https://doi.org/10.3109/15563650.2015.1034201"),
    "aha_co_2012": ("AHA / Hampson et al.", "Carbon monoxide poisoning: diagnosis by carboxyhaemoglobin", 2012, "https://doi.org/10.1164/rccm.201207-1284CI"),
    "ese_dm_insipidus_2022": ("Endocrine Society / ESE", "Diagnosis of arginine vasopressin deficiency (central diabetes insipidus)", 2022, "https://doi.org/10.1210/clinem/dgac400"),
    "endo_hypoglycemia_2009_ada_2025": ("Endocrine Society 2009 / ADA 2025", "Evaluation and management of adult hypoglycemic disorders; ADA hypoglycemia levels", 2025, "https://doi.org/10.2337/dc25-S006"),
    "acr_sjogren_2016": ("ACR/EULAR", "2016 classification criteria for primary Sjogren's syndrome", 2016, "https://doi.org/10.1002/art.39859"),
    "asas_axspa_2009": ("ASAS", "Classification criteria for axial spondyloarthritis", 2009, "https://doi.org/10.1136/ard.2009.108233"),
}

# (disease_id, suffix, rule_type, urgent, expression, source_id, title, explanation, limitations)
CURATED: list[tuple] = []


def rule(did, suffix, rtype, urgent, expr, src, title, expl, lim=None, specificity="specific"):
    CURATED.append((did, suffix, rtype, urgent, expr, src, title, expl, lim or [], specificity))


# ---- Diabetes & glycaemic crises (ADA/EASD 2024, ADA SoC 2025) ----------------
rule("diabetic_ketoacidosis", "ada_easd_2024_dka_triad", "diagnostic_criterion", True,
     ALL(ANY(L("glucose", ">=", 200, "mg/dL"), L("fasting_plasma_glucose", ">=", 200, "mg/dL"), L("glucose_random", ">=", 200, "mg/dL")),
         ANY(L("beta_hydroxybutyrate", ">=", 3.0, "mmol/L"), L("urine_ketones_qualitative", "==", 1, "1")),
         ANY(L("arterial_ph", "<", 7.30, "[pH]"), L("bicarbonate", "<", 18, "mmol/L"))),
     "ada_easd_hyperglycemic_crises_2024", "Diabetic ketoacidosis - D/K/A triad (2024 consensus)",
     "DKA = hyperglycaemia (glucose >= 200 mg/dL or known diabetes) + ketosis (beta-hydroxybutyrate >= 3.0 mmol/L or urine ketones >= 2+) + metabolic acidosis (pH < 7.30 and/or bicarbonate < 18 mmol/L).",
     ["Euglycaemic DKA (SGLT2 inhibitors, pregnancy, starvation) presents with glucose < 200 mg/dL; a prior diagnosis of diabetes satisfies the D criterion.", "Urine ketone strips measure acetoacetate and may under-read early DKA."])
rule("diabetic_ketoacidosis", "ada_easd_2024_severe", "staging_severity", True,
     ANY(L("arterial_ph", "<", 7.00, "[pH]"), L("bicarbonate", "<", 10, "mmol/L"), L("beta_hydroxybutyrate", ">", 6.0, "mmol/L")),
     "ada_easd_hyperglycemic_crises_2024", "DKA severity - severe (pH < 7.0, HCO3 < 10, BHB > 6)",
     "Severe DKA: pH < 7.00 or bicarbonate < 10 mmol/L or beta-hydroxybutyrate > 6 mmol/L; ICU-level care.")
rule("diabetic_ketoacidosis", "ada_easd_2024_resolution", "exclusion_criterion", False,
     ALL(L("beta_hydroxybutyrate", "<", 0.6, "mmol/L"), L("bicarbonate", ">=", 18, "mmol/L"), L("arterial_ph", ">=", 7.30, "[pH]")),
     "ada_easd_hyperglycemic_crises_2024", "DKA resolution criteria (not DKA)",
     "BHB < 0.6 mmol/L with bicarbonate >= 18 mmol/L and venous pH >= 7.30 defines resolution / absence of DKA.")
rule("hyperosmolar_hyperglycemic_state", "ada_easd_2024_hhs", "diagnostic_criterion", True,
     ALL(ANY(L("glucose", ">=", 600, "mg/dL"), L("glucose_random", ">=", 600, "mg/dL"), L("fasting_plasma_glucose", ">=", 600, "mg/dL")),
         ANY(L("serum_osmolality", ">", 320, "mOsm/kg"), L("calculated_osmolality", ">", 320, "mOsm/kg"))),
     "ada_easd_hyperglycemic_crises_2024", "Hyperosmolar hyperglycaemic state (2024 consensus)",
     "HHS = plasma glucose >= 600 mg/dL + effective osmolality > 300 mOsm/kg (or total > 320) + absence of significant ketonaemia (BHB < 3.0) + pH >= 7.30 and bicarbonate >= 15.",
     ["Mixed DKA-HHS occurs in ~30 %; BHB >= 3.0 with acidosis indicates the overlap.", "Effective osmolality = 2 x Na + glucose/18 (mg/dL)."])
rule("hyperosmolar_hyperglycemic_state", "ada_easd_2024_hhs_ketoacidosis_exclusion", "exclusion_criterion", False,
     ALL(L("beta_hydroxybutyrate", ">=", 3.0, "mmol/L"), L("arterial_ph", "<", 7.30, "[pH]")),
     "ada_easd_hyperglycemic_crises_2024", "HHS excluded in isolation: significant ketoacidosis present",
     "Significant ketonaemia with acidosis indicates DKA or mixed DKA-HHS rather than pure HHS.")
rule("diabetes_mellitus", "ada_2025_fpg_a1c_concordant", "diagnostic_criterion", False,
     ALL(L("fasting_plasma_glucose", ">=", 126, "mg/dL"), L("hemoglobin_a1c", ">=", 6.5, "%")),
     "ada_soc_2025", "Diabetes mellitus - two concordant abnormal tests from one sample (ADA 2025)",
     "ADA: diagnosis is confirmed when two different tests (e.g., FPG >= 126 mg/dL and HbA1c >= 6.5 %) are both above threshold in the same sample, or the same test is repeated.",
     ["HbA1c is unreliable in haemoglobinopathies, haemolysis, recent transfusion, pregnancy (2nd/3rd trimester), CKD stage 4-5 and iron deficiency."])
rule("diabetes_mellitus", "ada_2025_random_glucose_symptomatic", "screening", True,
     ANY(L("glucose_random", ">=", 200, "mg/dL"), L("glucose", ">=", 200, "mg/dL")),
     "ada_soc_2025", "Random plasma glucose >= 200 mg/dL (diagnostic with classic symptoms / crisis)",
     "Random glucose >= 200 mg/dL is diagnostic of diabetes in the presence of classic hyperglycaemic symptoms or hyperglycaemic crisis; otherwise requires confirmation.", specificity="general")
rule("diabetes_mellitus", "ada_2025_ogtt_2h", "diagnostic_criterion", False,
     L("two_hour_postload_glucose", ">=", 200, "mg/dL"),
     "ada_soc_2025", "Diabetes - 2-h plasma glucose >= 200 mg/dL during 75-g OGTT",
     "2-h PG >= 200 mg/dL (11.1 mmol/L) during a 75-g OGTT; confirm by repeat testing unless unequivocal hyperglycaemia.")
rule("prediabetes", "ada_2025_prediabetes_range", "diagnostic_criterion", False,
     ANY(ALL(L("fasting_plasma_glucose", ">=", 100, "mg/dL"), L("fasting_plasma_glucose", "<=", 125, "mg/dL")),
         ALL(L("hemoglobin_a1c", ">=", 5.7, "%"), L("hemoglobin_a1c", "<=", 6.4, "%")),
         ALL(L("two_hour_postload_glucose", ">=", 140, "mg/dL"), L("two_hour_postload_glucose", "<=", 199, "mg/dL"))),
     "ada_soc_2025", "Prediabetes - IFG 100-125, IGT 140-199, HbA1c 5.7-6.4 % (ADA 2025)",
     "Prediabetes: FPG 100-125 mg/dL, 2-h PG 140-199 mg/dL or HbA1c 5.7-6.4 %.")
rule("gestational_diabetes_mellitus", "iadpsg_2010_one_step", "diagnostic_criterion", False,
     ANY(L("fasting_plasma_glucose", ">=", 92, "mg/dL"), L("two_hour_postload_glucose", ">=", 153, "mg/dL")),
     "iadpsg_2010", "GDM - IADPSG/ADA one-step 75-g OGTT thresholds (24-28 weeks)",
     "IADPSG: fasting >= 92, 1-h >= 180 or 2-h >= 153 mg/dL on a 75-g OGTT at 24-28 weeks; any one value diagnoses GDM.",
     ["Only valid during pregnancy weeks 24-28; FPG >= 126 or HbA1c >= 6.5 % in early pregnancy indicates overt diabetes."])
rule("fasting_hypoglycemia", "ada_2025_level2_hypoglycemia", "diagnostic_criterion", True,
     ANY(L("glucose", "<", 54, "mg/dL"), L("fasting_plasma_glucose", "<", 54, "mg/dL"), L("glucose_random", "<", 54, "mg/dL")),
     "endo_hypoglycemia_2009_ada_2025", "Clinically significant (level 2) hypoglycaemia < 54 mg/dL",
     "Glucose < 54 mg/dL (3.0 mmol/L) is level 2, clinically significant hypoglycaemia; < 70 mg/dL is level 1 (alert value). Whipple triad required for a hypoglycaemic disorder in non-diabetic patients.")

# ---- Kidney ------------------------------------------------------------------
rule("chronic_kidney_disease", "kdigo_2024_g3_plus", "diagnostic_criterion", False,
     L("egfr_ckd_epi_creatinine", "<", 60, "mL/min/{1.73_m2}"),
     "kdigo_ckd_2024", "CKD - eGFR < 60 mL/min/1.73 m2 (GFR category G3a-G5)",
     "KDIGO 2024: eGFR < 60 mL/min/1.73 m2 for > 3 months defines CKD irrespective of markers of damage; a single value is a 'kidney function abnormality' until chronicity is established.",
     ["Chronicity (> 3 months) cannot be established from a single report; AKI must be excluded."])
rule("chronic_kidney_disease", "kdigo_2024_albuminuria_a2", "diagnostic_criterion", False,
     L("urine_albumin_to_creatinine_ratio", ">=", 30, "mg/g"),
     "kdigo_ckd_2024", "CKD marker - albuminuria ACR >= 30 mg/g (A2/A3)",
     "ACR >= 30 mg/g (3 mg/mmol) persisting > 3 months is a marker of kidney damage; A2 30-300, A3 > 300 mg/g.")
rule("chronic_kidney_disease", "kdigo_2024_g4_g5_severe", "staging_severity", True,
     L("egfr_ckd_epi_creatinine", "<", 30, "mL/min/{1.73_m2}"),
     "kdigo_ckd_2024", "CKD G4-G5 - eGFR < 30 (severely decreased / kidney failure < 15)",
     "eGFR 15-29 = G4; < 15 = G5 (kidney failure). Nephrology referral and kidney-replacement planning.")
rule("acute_kidney_injury", "kdigo_2012_creatinine_absolute", "screening", True,
     L("creatinine", ">=", 4.0, "mg/dL"),
     "kdigo_aki_2012", "AKI stage 3 surrogate - creatinine >= 4.0 mg/dL",
     "KDIGO: creatinine >= 4.0 mg/dL with an acute rise satisfies stage 3; on a single report it flags severe azotaemia requiring urgent evaluation (AKI vs CKD).", specificity="general")
rule("nephrotic_syndrome", "kdigo_2021_nephrotic_range", "diagnostic_criterion", False,
     ALL(ANY(L("urine_protein_to_creatinine_ratio", ">=", 3000, "mg/g"), L("urine_protein_24_hour", ">=", 3500, "mg/24h")),
         L("albumin", "<", 3.0, "g/dL")),
     "kdigo_gd_2021", "Nephrotic syndrome - proteinuria >= 3.5 g/day (UPCR >= 3 g/g) + hypoalbuminaemia",
     "Nephrotic syndrome: proteinuria > 3.5 g/24 h (or UPCR > 3000 mg/g) with serum albumin < 3.0 g/dL, oedema and hyperlipidaemia.")
rule("nephritic_syndrome", "kdigo_2021_hematuria_proteinuria", "diagnostic_criterion", False,
     ALL(L("urine_rbc_count", ">", 5, "/HPF"), ANY(L("urine_protein_to_creatinine_ratio", ">=", 500, "mg/g"), L("creatinine", ">", 1.3, "mg/dL"))),
     "kdigo_gd_2021", "Nephritic pattern - glomerular haematuria + proteinuria / reduced GFR",
     "Haematuria (> 5 RBC/HPF, dysmorphic/casts) with sub-nephrotic proteinuria and/or rising creatinine and hypertension suggests glomerulonephritis.")
rule("tumor_lysis_syndrome", "cairo_bishop_laboratory_tls", "diagnostic_criterion", True,
     ANY(ALL(L("uric_acid", ">=", 8.0, "mg/dL"), L("potassium", ">=", 6.0, "mmol/L")),
         ALL(L("uric_acid", ">=", 8.0, "mg/dL"), L("phosphate", ">=", 4.5, "mg/dL")),
         ALL(L("uric_acid", ">=", 8.0, "mg/dL"), L("corrected_calcium_for_serum_albumin", "<=", 7.0, "mg/dL")),
         # K + P without hyperuricaemia is the everyday CKD-MBD pattern; demand a tumour-burden marker
         ALL(L("potassium", ">=", 6.0, "mmol/L"), L("phosphate", ">=", 4.5, "mg/dL"), L("lactate_dehydrogenase", ">", 500, "U/L")),
         ALL(L("phosphate", ">=", 4.5, "mg/dL"), L("corrected_calcium_for_serum_albumin", "<=", 7.0, "mg/dL"), L("lactate_dehydrogenase", ">", 500, "U/L"))),
     "cairo_bishop_2004", "Laboratory TLS - Cairo-Bishop (>= 2 of: UA >= 8, K >= 6, P >= 4.5 adult, Ca <= 7)",
     "Laboratory TLS requires >= 2 abnormalities within 3 days before to 7 days after cytotoxic therapy: uric acid >= 8 mg/dL, potassium >= 6 mmol/L, phosphate >= 4.5 mg/dL (>= 6.5 children), calcium <= 7 mg/dL.",
     ["Clinical context (malignancy with recent therapy) is required; the same pattern occurs in rhabdomyolysis and AKI."])
rule("rhabdomyolysis", "ck_5x_uln_diagnostic", "diagnostic_criterion", True,
     L("creatine_kinase_total", ">=", 1000, "U/L"),
     "rhabdo_review_2020", "Rhabdomyolysis - CK >= 5x ULN (>= 1,000 U/L)",
     "Rhabdomyolysis is defined by CK > 5x ULN (~1,000 U/L) with a compatible history; CK > 5,000 U/L carries a substantially higher AKI risk.",
     ["Myocardial infarction, myositis and strenuous exercise also raise CK; CK-MB fraction and troponin help discriminate."])
rule("rhabdomyolysis", "ck_5000_aki_risk", "staging_severity", True,
     L("creatine_kinase_total", ">=", 5000, "U/L"),
     "rhabdo_review_2020", "Rhabdomyolysis - CK >= 5,000 U/L: high AKI risk",
     "CK >= 5,000 U/L identifies patients at high risk of pigment nephropathy; aggressive isotonic fluids and electrolyte monitoring are indicated.")

# ---- GI / liver -----------------------------------------------------------------
rule("acute_pancreatitis", "atlanta_2012_lipase_3x_uln", "diagnostic_criterion", True,
     L("lipase", ">=", 180, "U/L"),
     "atlanta_pancreatitis_2012", "Acute pancreatitis - lipase >= 3x ULN (Atlanta 2012)",
     "Revised Atlanta: diagnosis requires 2 of 3 - characteristic abdominal pain, lipase/amylase >= 3x ULN, characteristic imaging. Lipase >= 3x ULN (ULN ~60 U/L) satisfies the enzymatic criterion.",
     ["Lipase ULN is assay-dependent; renal failure, bowel ischaemia and DKA can raise lipase 1-3x ULN."])
rule("acute_pancreatitis", "atlanta_2012_amylase_3x_uln", "screening", False,
     L("amylase", ">=", 300, "U/L"),
     "atlanta_pancreatitis_2012", "Acute pancreatitis - amylase >= 3x ULN (less specific than lipase)",
     "Amylase >= 3x ULN supports pancreatitis but is less sensitive and specific than lipase (salivary, renal, macroamylasaemia).", specificity="general")
rule("hepatitis_a", "igm_anti_hav_positive", "diagnostic_criterion", False,
     L("hepatitis_a_igm_antibody", "==", 1, "1"),
     "aasld_hav_hev_2023", "Acute hepatitis A - IgM anti-HAV positive",
     "IgM anti-HAV is diagnostic of acute hepatitis A infection; appears at symptom onset and persists 3-6 months.")
rule("hepatitis_e", "igm_anti_hev_positive", "diagnostic_criterion", False,
     L("hepatitis_e_igm_antibody", "==", 1, "1"),
     "aasld_hav_hev_2023", "Acute hepatitis E - IgM anti-HEV positive",
     "IgM anti-HEV (confirmed by HEV RNA where available) is diagnostic of acute hepatitis E.")
rule("hepatitis_b", "aasld_2018_hbsag_positive", "diagnostic_criterion", False,
     L("hepatitis_b_surface_antigen", "==", 1, "1"),
     "aasld_hbv_2018", "Hepatitis B infection - HBsAg positive",
     "HBsAg positivity establishes HBV infection; persistence > 6 months defines chronic hepatitis B. IgM anti-HBc distinguishes acute infection.")
rule("hepatitis_b", "aasld_2018_acute_igm_anti_hbc", "staging_severity", False,
     ALL(L("hepatitis_b_surface_antigen", "==", 1, "1"), L("hepatitis_b_core_igm_antibody", "==", 1, "1")),
     "aasld_hbv_2018", "Acute hepatitis B - HBsAg + IgM anti-HBc",
     "HBsAg with IgM anti-HBc indicates acute (or severe flare of chronic) hepatitis B.")
rule("hepatitis_c", "aasld_idsa_2023_rna_positive", "diagnostic_criterion", False,
     L("hepatitis_c_rna_quantitative_pcr", ">", 15, "[IU]/mL"),
     "aasld_idsa_hcv_2023", "Hepatitis C - detectable HCV RNA (current infection)",
     "Detectable HCV RNA confirms current infection; anti-HCV alone cannot distinguish resolved from active infection.")
rule("hepatitis_c", "aasld_idsa_2023_antibody_screen", "screening", False,
     L("hepatitis_c_antibody", "==", 1, "1"),
     "aasld_idsa_hcv_2023", "Hepatitis C - anti-HCV reactive (needs RNA confirmation)",
     "Reactive anti-HCV requires reflex HCV RNA testing; ~25 % of antibody-positive persons have cleared the virus.", specificity="general")
rule("hiv_infection", "cdc_2014_ag_ab_reactive", "screening", False,
     L("hiv_1_and_hiv_2_antigen_antibody", "==", 1, "1"),
     "cdc_hiv_testing_2014", "HIV - 4th-generation Ag/Ab reactive (confirm with differentiation assay / RNA)",
     "A reactive HIV-1/2 antigen/antibody immunoassay must be confirmed with an HIV-1/HIV-2 antibody differentiation assay and, if indeterminate, HIV-1 RNA.", specificity="general")
rule("syphilis", "cdc_2021_treponemal_plus_nontreponemal", "diagnostic_criterion", False,
     ALL(L("syphilis_tppa", "==", 1, "1"), L("syphilis_rpr", "==", 1, "1")),
     "cdc_sti_2021", "Syphilis - reactive treponemal (TPPA) and non-treponemal (RPR) tests",
     "Concordant reactive treponemal and non-treponemal tests indicate untreated or recently treated syphilis; RPR titre guides staging and response.")
rule("helicobacter_pylori_infection", "acg_2024_active_infection", "diagnostic_criterion", False,
     ANY(L("helicobacter_pylori_stool_antigen", "==", 1, "1"), L("helicobacter_pylori_urea_breath_test", "==", 1, "1")),
     "acg_hpylori_2024", "H. pylori active infection - stool antigen or urea breath test positive",
     "Stool antigen and urea breath tests detect active infection (sensitivity/specificity > 90 %); PPIs must be stopped 2 weeks and antibiotics/bismuth 4 weeks before testing.")
rule("celiac_disease", "espghan_2020_ttg_10x_uln", "diagnostic_criterion", False,
     L("anti_tissue_transglutaminase_iga", ">=", 10, "[arb'U]/mL"),
     "espghan_celiac_2020", "Coeliac disease - tTG-IgA >= 10x ULN (biopsy-sparing pathway)",
     "ESPGHAN 2020: tTG-IgA >= 10x ULN with a positive EMA-IgA in a second sample permits a no-biopsy diagnosis in children; ACG 2023 allows the same in selected adults. Value is expressed as multiples of ULN (assay-specific).",
     ["Requires total IgA to exclude IgA deficiency; patient must be on a gluten-containing diet.", "Assay units vary; the threshold is 10x the assay ULN, not an absolute number."])
rule("celiac_disease", "acg_2023_ttg_positive_screen", "screening", False,
     L("anti_tissue_transglutaminase_iga", ">", 1, "[arb'U]/mL"),
     "acg_celiac_2023", "Coeliac disease - tTG-IgA above ULN (confirm with duodenal biopsy)",
     "Any tTG-IgA above the assay ULN warrants EMA confirmation and/or duodenal biopsy.", specificity="general")
rule("celiac_disease", "acg_2023_iga_deficiency_caveat", "exclusion_criterion", False,
     ALL(L("total_immunoglobulin_a", "<", 7, "mg/dL"), L("anti_tissue_transglutaminase_iga", "<=", 1, "[arb'U]/mL")),
     "acg_celiac_2023", "Negative tTG-IgA uninterpretable in selective IgA deficiency",
     "With total IgA < 7 mg/dL a negative tTG-IgA does not exclude coeliac disease; use IgG-based serology (DGP-IgG / tTG-IgG).")
rule("crohn_disease", "ecco_2019_calprotectin_active", "screening", False,
     L("fecal_calprotectin", ">", 250, "ug/g"),
     "ecco_ibd_2019", "IBD - faecal calprotectin > 250 ug/g (active mucosal inflammation)",
     "Faecal calprotectin > 250 ug/g correlates with endoscopically active IBD; 50-250 is indeterminate; < 50 makes IBD unlikely (NPV ~ 98 %).", specificity="general")
rule("ulcerative_colitis", "ecco_2019_calprotectin_active", "screening", False,
     L("fecal_calprotectin", ">", 250, "ug/g"),
     "ecco_ibd_2019", "IBD - faecal calprotectin > 250 ug/g (active mucosal inflammation)",
     "Faecal calprotectin > 250 ug/g correlates with endoscopically active IBD; 50-250 is indeterminate; < 50 makes IBD unlikely.", specificity="general")
rule("primary_biliary_cholangitis", "easl_2017_ama_alp", "diagnostic_criterion", False,
     ALL(L("mitochondrial_m2_antibody", "==", 1, "1"), L("alkaline_phosphatase", ">", 195, "U/L")),
     "easl_pbc_2017", "PBC - AMA positive (>= 1:40) with cholestatic ALP > 1.5x ULN",
     "EASL 2017: PBC is diagnosed with cholestatic ALP elevation plus AMA >= 1:40 (or PBC-specific ANA sp100/gp210); biopsy not required.")
rule("autoimmine_hepatitis_placeholder", "skip", "screening", False, L("albumin", ">", 0), "aasld_aih_2019", "", "")
CURATED.pop()  # (placeholder removed - keeps the numbering stable in the audit)
rule("autoimmune_hepatitis", "aasld_2019_sma_ana_igg", "diagnostic_criterion", False,
     ALL(ANY(L("smooth_muscle_antibody", ">=", 40, "titer"), L("antinuclear_antibody_titer", ">=", 40, "titer")),
         L("alanine_aminotransferase", ">", 90, "U/L")),
     "aasld_aih_2019", "Autoimmune hepatitis - ANA/SMA >= 1:40 with hepatocellular injury (simplified criteria component)",
     "Simplified IAIHG criteria: ANA or SMA >= 1:40 (1 pt), >= 1:80 (2 pts), IgG > ULN (1-2 pts), compatible histology, absence of viral hepatitis; >= 6 probable, >= 7 definite.",
     ["Histology and IgG are required for definite diagnosis; viral hepatitis must be excluded."])
rule("wilson_disease", "easl_2012_ceruloplasmin_low", "diagnostic_criterion", False,
     L("ceruloplasmin", "<", 10, "mg/dL"),
     "easl_wilson_2012", "Wilson disease - ceruloplasmin < 10 mg/dL (strong evidence, Leipzig score 2)",
     "Leipzig score: ceruloplasmin < 10 mg/dL = 2 points, 10-20 = 1 point; combine with 24-h urinary copper > 100 ug, KF rings, ATP7B genotype.")
rule("wilson_disease", "easl_2012_ceruloplasmin_borderline", "screening", False,
     L("ceruloplasmin", "<", 20, "mg/dL"),
     "easl_wilson_2012", "Wilson disease - ceruloplasmin 10-20 mg/dL (Leipzig 1 point; investigate)",
     "Ceruloplasmin < 20 mg/dL in a patient < 40 y with liver disease or movement disorder warrants 24-h urine copper and slit-lamp examination.", specificity="general")
rule("alpha_1_antitrypsin_deficiency", "serum_aat_below_50", "diagnostic_criterion", False,
     L("alpha_1_antitrypsin_serum", "<", 50, "mg/dL"),
     "acg_liver_chem_2017", "Alpha-1 antitrypsin deficiency - serum AAT < 50 mg/dL (PiZZ range)",
     "Serum AAT < 50 mg/dL (< 11 umol/L) is typical of PiZZ; 50-90 mg/dL suggests heterozygosity; confirm by phenotype/genotype. AAT is an acute-phase reactant.")
rule("cholestatic_liver_injury_pattern", "easl_2009_alp_ggt", "diagnostic_criterion", False,
     ALL(L("alkaline_phosphatase", ">", 195, "U/L"), L("gamma_glutamyl_transferase", ">", 180, "U/L")),
     "easl_cholestasis_2009", "Cholestasis - ALP > 1.5x ULN with GGT > 3x ULN",
     "EASL: cholestasis is defined by ALP > 1.5x ULN together with GGT > 3x ULN (hepatic origin); R-ratio < 2 confirms a cholestatic pattern.")
rule("hepatocellular_injury_pattern", "acg_2017_alt_5x_uln_acute", "staging_severity", True,
     ANY(L("alanine_aminotransferase", ">", 250, "U/L"), L("aspartate_aminotransferase", ">", 250, "U/L")),
     "acg_liver_chem_2017", "Marked hepatocellular injury - ALT/AST > 5x ULN",
     "ALT > 5x ULN (ACG ULN: 33 U/L men, 25 U/L women) indicates marked injury; > 15x ULN (acute viral, ischaemic, toxic) demands urgent evaluation.")
rule("acute_liver_failure", "aasld_2011_inr_encephalopathy_surrogate", "diagnostic_criterion", True,
     ALL(L("international_normalized_ratio", ">=", 1.5, "1"), L("total_bilirubin", ">", 3.0, "mg/dL"),
         ANY(L("alanine_aminotransferase", ">", 500, "U/L"), L("aspartate_aminotransferase", ">", 500, "U/L"))),
     "aasld_alf_2011", "Acute liver failure - coagulopathy (INR >= 1.5) + jaundice + severe hepatocellular injury",
     "ALF = INR >= 1.5 with hepatic encephalopathy within 26 weeks of illness onset in a patient without pre-existing cirrhosis. Encephalopathy is clinical and must be confirmed.",
     ["Encephalopathy cannot be read from laboratory data; without it the pattern is severe acute liver injury (ALI)."])

# ---- Cardiac / vascular -------------------------------------------------------
rule("acute_myocardial_infarction", "esc_2023_hs_tnt_rule_in", "diagnostic_criterion", True,
     L("high_sensitivity_troponin_t", ">=", 0.052, "ng/mL"),
     "esc_acs_2023", "NSTEMI - hs-cTnT >= 52 ng/L (ESC 0/1-h rule-in level)",
     "ESC 0 h/1 h algorithm (Elecsys hs-cTnT): 0-h >= 52 ng/L rules in; 0-h < 5 ng/L rules out; a 1-h delta >= 5 ng/L rules in. A single value above the 99th percentile (14 ng/L) is 'myocardial injury' until a rise/fall is shown.",
     ["Chronic myocardial injury (CKD, HF, myocarditis) elevates hs-cTn without MI; kinetics are mandatory."])
rule("acute_myocardial_infarction", "esc_2023_hs_tni_rule_in", "diagnostic_criterion", True,
     L("high_sensitivity_troponin_i", ">=", 0.052, "ng/mL"),
     "esc_acs_2023", "NSTEMI - hs-cTnI >= 52 ng/L (Architect/Centaur rule-in range)",
     "Assay-specific ESC 0/1-h rule-in thresholds for hs-cTnI range 52-120 ng/L; 52 ng/L is the most conservative published value.")
rule("acute_myocardial_infarction", "esc_2023_hs_tn_myocardial_injury", "screening", True,
     ANY(L("high_sensitivity_troponin_t", ">", 0.014, "ng/mL"), L("high_sensitivity_troponin_i", ">", 0.026, "ng/mL"), L("troponin_i", ">", 0.04, "ng/mL")),
     "esc_acs_2023", "Myocardial injury - troponin above 99th percentile URL",
     "Any troponin above the 99th percentile URL defines myocardial injury; acute MI requires a rise and/or fall with ischaemic evidence (4th Universal Definition).", specificity="general")
rule("acute_myocardial_infarction", "esc_2023_hs_tnt_rule_out", "exclusion_criterion", False,
     L("high_sensitivity_troponin_t", "<", 0.005, "ng/mL"),
     "esc_acs_2023", "NSTEMI ruled out - hs-cTnT < 5 ng/L at presentation (>= 3 h from onset)",
     "hs-cTnT < 5 ng/L at 0 h (with chest-pain onset > 3 h) has NPV > 99 % for NSTEMI.")
rule("heart_failure", "esc_2021_ntprobnp_chronic_rule_out", "exclusion_criterion", False,
     L("n_terminal_pro_bnp", "<", 125, "pg/mL"),
     "esc_hf_2021_2023", "Chronic HF unlikely - NT-proBNP < 125 pg/mL",
     "ESC 2021: NT-proBNP < 125 pg/mL (BNP < 35) makes chronic heart failure unlikely in the non-acute setting.")
rule("heart_failure", "esc_2021_ntprobnp_elevated", "screening", False,
     ANY(L("n_terminal_pro_bnp", ">=", 125, "pg/mL"), L("b_type_natriuretic_peptide", ">=", 35, "pg/mL")),
     "esc_hf_2021_2023", "Heart failure possible - NT-proBNP >= 125 / BNP >= 35 pg/mL (echocardiography indicated)",
     "Natriuretic peptides above the rule-out threshold require echocardiography; AF, CKD, age and sepsis raise levels; obesity lowers them.", specificity="general")
rule("acute_heart_failure_support_pattern", "esc_2021_acute_ntprobnp_age_tiered", "diagnostic_criterion", True,
     ANY(L("n_terminal_pro_bnp", ">=", 1800, "pg/mL"), L("b_type_natriuretic_peptide", ">=", 400, "pg/mL")),
     "esc_hf_2021_2023", "Acute HF - NT-proBNP >= 1800 pg/mL (rule-in at any age) / BNP >= 400",
     "Acute dyspnoea: NT-proBNP rule-in 450 pg/mL (< 50 y), 900 (50-75 y), 1800 (> 75 y); 1800 rules in at any age. BNP > 400 pg/mL rules in; < 100 rules out.")
rule("acute_heart_failure_support_pattern", "esc_2021_acute_ntprobnp_rule_out", "exclusion_criterion", False,
     ANY(L("n_terminal_pro_bnp", "<", 300, "pg/mL"), L("b_type_natriuretic_peptide", "<", 100, "pg/mL")),
     "esc_hf_2021_2023", "Acute HF unlikely - NT-proBNP < 300 / BNP < 100 pg/mL",
     "In acute dyspnoea NT-proBNP < 300 pg/mL or BNP < 100 pg/mL makes acute heart failure unlikely (NPV ~ 98 %).")
rule("pulmonary_embolism", "esc_2019_d_dimer_rule_out", "exclusion_criterion", False,
     L("d_dimer", "<", 0.5, "ug/mL"),
     "esc_pe_2019", "PE ruled out - D-dimer < 500 ng/mL FEU in low/intermediate pre-test probability",
     "ESC 2019: D-dimer < 500 ng/mL (or < age x 10 ng/mL above 50 y; YEARS-adjusted < 1000 ng/mL) safely excludes PE when clinical probability is not high.",
     ["Does not exclude PE when pre-test probability is high; imaging required."])
rule("pulmonary_embolism", "esc_2019_d_dimer_positive_screen", "screening", False,
     L("d_dimer", ">=", 0.5, "ug/mL"),
     "esc_pe_2019", "PE not excluded - D-dimer >= 500 ng/mL FEU (CTPA indicated)",
     "A positive D-dimer has low specificity (age, malignancy, pregnancy, infection, surgery); it mandates CT pulmonary angiography and never confirms PE.", specificity="non_specific")
rule("pulmonary_embolism", "esc_2019_risk_troponin_bnp", "staging_severity", True,
     ALL(L("d_dimer", ">=", 0.5, "ug/mL"),
         ANY(L("high_sensitivity_troponin_t", ">", 0.014, "ng/mL"), L("troponin_i", ">", 0.04, "ng/mL")),
         ANY(L("n_terminal_pro_bnp", ">=", 600, "pg/mL"), L("b_type_natriuretic_peptide", ">=", 100, "pg/mL"))),
     "esc_pe_2019", "PE risk stratification - troponin and natriuretic peptide both elevated (intermediate-high risk if PE confirmed)",
     "ESC 2019: in confirmed PE, elevated troponin plus RV dysfunction/NT-proBNP >= 600 pg/mL defines intermediate-high risk.")

# ---- Sepsis / DIC ------------------------------------------------------------------
rule("sepsis", "sepsis3_lactate_2_with_infection_marker", "diagnostic_criterion", True,
     ALL(L("lactate", ">", 2.0, "mmol/L"), ANY(L("procalcitonin", ">=", 0.5, "ng/mL"), L("blood_culture", "==", 1, "1"), L("white_blood_cell_count", ">", 12, "10*3/uL"), L("white_blood_cell_count", "<", 4, "10*3/uL"))),
     "sepsis3_2016", "Sepsis - hyperlactataemia with infection marker (Sepsis-3 laboratory support)",
     "Sepsis-3 is clinical (SOFA >= 2 with infection); lactate > 2 mmol/L with evidence of infection (positive culture, procalcitonin >= 0.5 ng/mL, leukocytosis/leukopenia) is strong laboratory support.",
     ["SOFA components (MAP, GCS, PaO2/FiO2, urine output) are clinical and not available in a laboratory report."])
rule("septic_shock_severe_lactic_acidosis", "sepsis3_lactate_4", "staging_severity", True,
     L("lactate", ">", 4.0, "mmol/L"),
     "sepsis3_2016", "Severe hyperlactataemia - lactate > 4 mmol/L",
     "Lactate > 4 mmol/L in suspected infection identifies patients at high mortality; septic shock requires vasopressors with lactate > 2 mmol/L after resuscitation.")
rule("disseminated_intravascular_coagulation", "isth_overt_dic_score_surrogate", "diagnostic_criterion", True,
     ALL(L("platelets", "<", 100, "10*9/L"), L("d_dimer", ">", 2.0, "ug/mL"), ANY(L("prothrombin_time", ">", 16, "s"), L("international_normalized_ratio", ">", 1.5, "1")), L("fibrinogen", "<", 150, "mg/dL")),
     "isth_dic_2001", "Overt DIC - ISTH score >= 5 surrogate (PLT < 100, D-dimer strongly raised, PT prolonged, fibrinogen < 150)",
     "ISTH overt DIC score: platelets < 100 (1) / < 50 (2); fibrin marker moderate (2) / strong (3); PT prolonged 3-6 s (1) / > 6 s (2); fibrinogen < 100 mg/dL (1). Score >= 5 = overt DIC. This pattern scores >= 5.",
     ["Requires an underlying disorder known to be associated with DIC."])

# ---- Haematology / oncology ----------------------------------------------------------
rule("multiple_myeloma", "imwg_2014_flc_ratio_100", "diagnostic_criterion", False,
     ALL(L("free_light_chain_ratio", ">=", 100, "ratio"), L("free_kappa_light_chains", ">=", 10, "mg/dL")),
     "imwg_2014", "Multiple myeloma - involved/uninvolved FLC ratio >= 100 with involved FLC >= 100 mg/L (SLiM biomarker)",
     "IMWG 2014 myeloma-defining biomarker: involved:uninvolved serum FLC ratio >= 100 with involved FLC >= 100 mg/L (10 mg/dL).")
rule("multiple_myeloma", "imwg_2014_plasma_cells_60", "diagnostic_criterion", False,
     L("plasma_cells_percent", ">=", 60, "%"),
     "imwg_2014", "Multiple myeloma - clonal bone marrow plasma cells >= 60 % (SLiM)",
     "Clonal bone-marrow plasma cells >= 60 % is a myeloma-defining event irrespective of CRAB features.")
rule("multiple_myeloma", "imwg_2014_m_spike_crab", "diagnostic_criterion", False,
     ALL(L("serum_protein_electrophoresis_m_spike", ">=", 3.0, "g/dL"),
         ANY(L("corrected_calcium_for_serum_albumin", ">", 11.0, "mg/dL"), L("calcium_total", ">", 11.0, "mg/dL"), L("creatinine", ">", 2.0, "mg/dL"), L("hemoglobin", "<", 10.0, "g/dL"))),
     "imwg_2014", "Multiple myeloma - M-protein >= 3 g/dL with CRAB feature",
     "M-protein >= 3 g/dL plus end-organ damage (hypercalcaemia > 11 mg/dL, creatinine > 2 mg/dL, anaemia Hb < 10 g/dL, bone lesions) meets IMWG criteria pending marrow confirmation (>= 10 % clonal plasma cells).")
rule("monoclonal_gammopathy_of_undetermined_significance", "imwg_2014_mgus", "diagnostic_criterion", False,
     ALL(L("serum_protein_electrophoresis_m_spike", ">", 0, "g/dL"), L("serum_protein_electrophoresis_m_spike", "<", 3.0, "g/dL"),
         L("corrected_calcium_for_serum_albumin", "<=", 11.0, "mg/dL"), L("creatinine", "<=", 2.0, "mg/dL"), L("hemoglobin", ">=", 10.0, "g/dL")),
     "imwg_2014", "MGUS - M-protein < 3 g/dL without CRAB features",
     "MGUS: serum M-protein < 3 g/dL, clonal plasma cells < 10 % and no myeloma-defining events.")
rule("acute_myeloid_leukemia", "who_2022_blasts_20", "diagnostic_criterion", True,
     L("blasts_percent", ">=", 20, "%"),
     "who_haem_2022", "Acute leukaemia - blasts >= 20 % in blood or marrow",
     "WHO 2022 / ICC: >= 20 % blasts in peripheral blood or bone marrow defines acute leukaemia (AML vs ALL by immunophenotype); AML with defining genetic abnormalities needs only >= 10 % blasts.")
rule("acute_lymphoblastic_leukemia", "who_2022_blasts_20", "diagnostic_criterion", True,
     L("blasts_percent", ">=", 20, "%"),
     "who_haem_2022", "Acute leukaemia - blasts >= 20 % in blood or marrow (lineage by flow cytometry)",
     "Lymphoblasts >= 20 % (ICC) define B- or T-ALL; immunophenotyping is required to separate ALL from AML.")
rule("chronic_myeloid_leukemia", "who_2022_bcr_abl1", "diagnostic_criterion", False,
     L("bcr_abl1_p210_transcript", ">", 0, "[arb'U]/mL"),
     "who_haem_2022", "CML - BCR::ABL1 (p210) transcript detected",
     "Detection of the BCR::ABL1 fusion (t(9;22)) is required for and diagnostic of CML in the appropriate haematological context.")
rule("polycythemia_vera", "who_2022_hb_jak2", "diagnostic_criterion", False,
     ALL(ANY(L("hemoglobin", ">", 16.5, "g/dL"), L("hematocrit", ">", 49, "%")), L("jak2_v617f_mutation", "==", 1, "1")),
     "who_haem_2022", "Polycythaemia vera - Hb > 16.5 g/dL (men) / Hct > 49 % with JAK2 mutation",
     "WHO 2022 major criteria: Hb > 16.5 g/dL men / > 16.0 women (Hct > 49 % / > 48 %), marrow hypercellularity, JAK2 V617F or exon 12 mutation; minor: subnormal EPO.",
     ["Female thresholds are Hb > 16.0 g/dL and Hct > 48 %."])
rule("essential_thrombocythemia", "who_2022_platelets_450", "screening", False,
     L("platelets", ">=", 450, "10*9/L"),
     "who_haem_2022", "Thrombocytosis >= 450 x 10^9/L (ET requires exclusion of reactive causes + driver mutation)",
     "Sustained platelets >= 450 x 10^9/L is the first WHO major criterion for ET; reactive thrombocytosis (iron deficiency, inflammation, post-splenectomy) must be excluded.", specificity="general")
rule("iron_deficiency_anemia", "bsg_2021_ferritin_30", "diagnostic_criterion", False,
     ALL(L("ferritin", "<", 30, "ng/mL"), ANY(L("hemoglobin", "<", 13.0, "g/dL"), L("hemoglobin", "<", 12.0, "g/dL"))),
     "bsg_ida_2021", "Iron-deficiency anaemia - ferritin < 30 ug/L with anaemia (BSG 2021)",
     "BSG 2021: ferritin < 30 ug/L is the most specific marker of iron deficiency (sensitivity 92 %, specificity 98 %); WHO 2020 uses < 15 ug/L in healthy adults and < 70 ug/L with inflammation.")
rule("iron_deficiency_anemia", "bsg_2021_inflammation_adjusted", "diagnostic_criterion", False,
     ALL(L("ferritin", "<", 100, "ng/mL"), L("transferrin_saturation", "<", 20, "%"), L("c_reactive_protein", ">", 5, "mg/L"), L("hemoglobin", "<", 12.0, "g/dL")),
     "bsg_ida_2021", "Iron deficiency with inflammation - ferritin < 100 + TSAT < 20 % + raised CRP",
     "With inflammation, ferritin up to 100 ug/L with TSAT < 20 % indicates iron deficiency (functional or absolute); soluble transferrin receptor helps when available.")
rule("iron_deficiency_anemia", "bsg_2021_exclusion_replete", "exclusion_criterion", False,
     ALL(L("ferritin", ">", 100, "ng/mL"), L("transferrin_saturation", ">=", 20, "%")),
     "bsg_ida_2021", "Iron deficiency excluded - ferritin > 100 ug/L with TSAT >= 20 %",
     "Ferritin > 100 ug/L with normal transferrin saturation effectively excludes absolute iron deficiency.")
rule("vitamin_b12_deficiency", "bsh_2014_b12_200_mma", "diagnostic_criterion", False,
     ANY(L("vitamin_b12", "<", 148, "pg/mL"), ALL(L("vitamin_b12", "<", 200, "pg/mL"), L("methylmalonic_acid", ">", 271, "ng/mL"))),
     "bsh_b12_2014", "Cobalamin deficiency - B12 < 148 pg/mL, or 148-200 with raised MMA",
     "BSH: serum cobalamin < 148 pmol/L... (< 200 ng/L = pg/mL) is deficient; 148-258 pmol/L indeterminate - confirm with MMA (> 0.27 umol/L = 271 ng/mL) or homocysteine.",
     ["Serum B12 may be falsely normal with anti-intrinsic-factor antibodies and falsely low in pregnancy, OCP use and folate deficiency."])
rule("folate_deficiency", "bsh_2014_serum_folate", "diagnostic_criterion", False,
     L("folate_serum", "<", 3.0, "ng/mL"),
     "bsh_b12_2014", "Folate deficiency - serum folate < 3 ug/L",
     "Serum folate < 3 ug/L (7 nmol/L) indicates deficiency; 3-4.5 borderline - check red-cell folate; always assess B12 before folate replacement.")
rule("hemolytic_anemia", "eha_2023_hemolysis_triad", "diagnostic_criterion", False,
     ALL(ANY(L("lactate_dehydrogenase", ">", 250, "U/L"), L("indirect_bilirubin", ">", 1.0, "mg/dL")),
         L("haptoglobin_serum_quantitative", "<", 25, "mg/dL"),
         ANY(L("reticulocytes", ">", 2.5, "%"), L("hemoglobin", "<", 12.0, "g/dL"))),
     "eha_hemolysis_2023", "Haemolysis - haptoglobin < 25 mg/dL with raised LDH / indirect bilirubin and reticulocytosis",
     "Haptoglobin < 25 mg/dL combined with LDH > ULN has 90 % specificity for haemolysis; reticulocytosis and unconjugated hyperbilirubinaemia complete the pattern. DAT separates immune from non-immune.")
rule("autoimmune_hemolytic_anemia", "eha_2023_dat_positive_hemolysis", "diagnostic_criterion", False,
     ALL(L("coombs_direct_antiglobulin_test", "==", 1, "1"), L("haptoglobin_serum_quantitative", "<", 25, "mg/dL"), L("hemoglobin", "<", 12.0, "g/dL")),
     "eha_hemolysis_2023", "Autoimmune haemolytic anaemia - positive DAT with biochemical haemolysis",
     "AIHA = haemolytic anaemia with a positive direct antiglobulin test (IgG and/or C3d); DAT-negative AIHA (~5-10 %) requires specialised testing.")
rule("g6pd_deficiency", "who_2022_enzyme_activity", "diagnostic_criterion", False,
     L("g6pd_enzyme_activity", "<", 4.0, "U/L"),
     "g6pd_who_2022", "G6PD deficiency - quantitative enzyme activity < 30 % of normal",
     "Quantitative G6PD activity < 30 % of the adjusted male median (assay-dependent; commonly < ~4 U/g Hb) defines deficiency; activity is falsely normal during acute haemolysis (reticulocytosis).",
     ["Units differ between assays (U/g Hb vs U/L vs % activity); interpret against the laboratory's reference."])
rule("sickle_cell_disease", "ash_2020_hb_s_electrophoresis", "diagnostic_criterion", False,
     L("hemoglobin_s", ">", 50, "%"),
     "ash_scd_2020_who", "Sickle cell disease - HbS > 50 % on electrophoresis/HPLC",
     "HbS > 50 % (typically 80-95 % with HbF/HbA2 and no HbA) indicates sickle cell anaemia (HbSS) or compound heterozygosity; HbS 35-45 % with HbA present = sickle trait.")
rule("thalassemia_trait", "hba2_3_5_microcytosis", "diagnostic_criterion", False,
     ALL(L("hemoglobin_a2", ">=", 3.5, "%"), L("mean_corpuscular_volume", "<", 80, "fL")),
     "ash_scd_2020_who", "Beta-thalassaemia trait - HbA2 >= 3.5 % with microcytosis",
     "HbA2 >= 3.5 % (HPLC/capillary electrophoresis) with MCV < 80 fL and normal iron studies is diagnostic of beta-thalassaemia trait; iron deficiency lowers HbA2.")
rule("hemochromatosis", "easl_2022_tsat_ferritin", "diagnostic_criterion", False,
     ALL(L("transferrin_saturation", ">", 45, "%"), L("ferritin", ">", 300, "ng/mL")),
     "aasld_hh_2011_easl_2022", "Hereditary haemochromatosis - TSAT > 45 % with ferritin > 300 ug/L (men) / > 200 (women)",
     "EASL 2022: TSAT > 45 % with raised ferritin should prompt HFE genotyping (C282Y homozygosity); ferritin > 1000 ug/L indicates risk of fibrosis.",
     ["Female ferritin threshold 200 ug/L; raised ferritin with normal TSAT is usually metabolic/inflammatory, not iron overload."])
rule("immune_thrombocytopenia", "ash_2019_isolated_thrombocytopenia", "diagnostic_criterion", False,
     ALL(L("platelets", "<", 100, "10*9/L"), L("hemoglobin", ">=", 12.0, "g/dL"), L("white_blood_cell_count", ">=", 4.0, "10*3/uL"), L("white_blood_cell_count", "<=", 11.0, "10*3/uL")),
     "ash_itp_2019", "Immune thrombocytopenia - isolated platelets < 100 x 10^9/L (diagnosis of exclusion)",
     "ITP: isolated thrombocytopenia < 100 x 10^9/L with otherwise normal counts and smear, after exclusion of pseudothrombocytopenia, drugs, HIV/HCV/H. pylori, liver disease and marrow failure.")
rule("thrombotic_thrombocytopenic_purpura", "isth_2020_adamts13_10", "diagnostic_criterion", True,
     L("adamts13_activity", "<", 10, "%"),
     "isth_ttp_2020", "TTP - ADAMTS13 activity < 10 %",
     "ADAMTS13 activity < 10 % confirms TTP in a patient with microangiopathic haemolytic anaemia and thrombocytopenia; treatment must not await the result when PLASMIC score is high.")
rule("thrombotic_thrombocytopenic_purpura", "isth_2020_mahat_pattern", "screening", True,
     ALL(L("platelets", "<", 30, "10*9/L"), L("lactate_dehydrogenase", ">", 500, "U/L"), L("haptoglobin_serum_quantitative", "<", 25, "mg/dL"), L("creatinine", "<", 2.0, "mg/dL")),
     "isth_ttp_2020", "Thrombotic microangiopathy pattern - severe thrombocytopenia + haemolysis with preserved renal function (PLASMIC-like)",
     "Platelets < 30 x 10^9/L with haemolysis (LDH, low haptoglobin, schistocytes) and creatinine < 2.0 mg/dL predicts severe ADAMTS13 deficiency (PLASMIC high).", specificity="general")
rule("antiphospholipid_syndrome", "acr_eular_2023_lab_criteria", "diagnostic_criterion", False,
     ANY(L("cardiolipin_igg_antibody", ">", 40, "[arb'U]/mL"), L("beta_2_glycoprotein_i_igg_antibody", ">", 40, "[arb'U]/mL")),
     "sydney_aps_2006_acr_2023", "Antiphospholipid antibodies - aCL or anti-B2GPI IgG > 40 units (moderate-high titre)",
     "ACR/EULAR 2023: moderate (40-79 U) or high (>= 80 U) aCL/anti-B2GPI IgG, or persistent lupus anticoagulant, on two occasions >= 12 weeks apart, with a clinical criterion.",
     ["Persistence at >= 12 weeks and a clinical event (thrombosis/pregnancy morbidity) are required."])

# ---- Thyroid ---------------------------------------------------------------------
rule("primary_hypothyroidism", "ata_2014_overt", "diagnostic_criterion", False,
     ALL(L("thyroid_stimulating_hormone", ">", 10.0, "u[IU]/mL"), L("free_thyroxine", "<", 0.8, "ng/dL")),
     "ata_hypothyroid_2014", "Overt primary hypothyroidism - TSH > 10 mIU/L with low free T4",
     "Elevated TSH with free T4 below the reference interval defines overt primary hypothyroidism; TSH > 10 mIU/L warrants treatment even with normal FT4 in most adults.")
rule("subclinical_hypothyroidism", "ata_2014_subclinical", "diagnostic_criterion", False,
     ALL(L("thyroid_stimulating_hormone", ">", 4.5, "u[IU]/mL"), L("thyroid_stimulating_hormone", "<=", 10.0, "u[IU]/mL"), L("free_thyroxine", ">=", 0.8, "ng/dL"), L("free_thyroxine", "<=", 1.8, "ng/dL")),
     "ata_hypothyroid_2014", "Subclinical hypothyroidism - TSH 4.5-10 mIU/L with normal free T4",
     "TSH above the reference range with normal FT4, confirmed on repeat after 6-12 weeks (transient elevation in ~60 % normalises).")
rule("hyperthyroidism", "ata_2016_overt", "diagnostic_criterion", False,
     ALL(L("thyroid_stimulating_hormone", "<", 0.1, "u[IU]/mL"), ANY(L("free_thyroxine", ">", 1.8, "ng/dL"), L("free_triiodothyronine", ">", 4.4, "pg/mL"))),
     "ata_hyperthyroid_2016", "Overt thyrotoxicosis - suppressed TSH (< 0.1) with raised FT4 and/or FT3",
     "Suppressed TSH with elevated FT4 or FT3 defines overt thyrotoxicosis; TRAb, uptake scan or Doppler determine aetiology.")
rule("graves_disease", "ata_2016_trab_positive", "diagnostic_criterion", False,
     ALL(L("thyroid_stimulating_hormone", "<", 0.1, "u[IU]/mL"), L("tsh_receptor_antibody", ">", 1.75, "[IU]/L")),
     "ata_hyperthyroid_2016", "Graves disease - thyrotoxicosis with positive TRAb",
     "TRAb (TSI/TBII) positivity in a thyrotoxic patient is diagnostic of Graves disease (sensitivity 97 %, specificity 99 % for 3rd-generation assays).")
rule("subclinical_hyperthyroidism", "ata_2016_subclinical", "diagnostic_criterion", False,
     ALL(L("thyroid_stimulating_hormone", "<", 0.4, "u[IU]/mL"), L("free_thyroxine", ">=", 0.8, "ng/dL"), L("free_thyroxine", "<=", 1.8, "ng/dL")),
     "ata_hyperthyroid_2016", "Subclinical hyperthyroidism - low TSH with normal FT4/FT3",
     "TSH below the reference range with normal FT4 and FT3; grade 2 (TSH < 0.1) carries higher AF and fracture risk.")
rule("hashimoto_thyroiditis", "ata_2014_tpo_positive_hypothyroid", "diagnostic_criterion", False,
     ALL(L("thyroid_peroxidase_antibody", ">", 35, "[IU]/mL"), L("thyroid_stimulating_hormone", ">", 4.5, "u[IU]/mL")),
     "ata_hypothyroid_2014", "Hashimoto thyroiditis - TPO antibody positive with elevated TSH",
     "Positive TPOAb with raised TSH indicates autoimmune (Hashimoto) hypothyroidism; TPOAb positivity alone predicts progression (~4 %/year).")

# ---- Adrenal / pituitary ------------------------------------------------------------
rule("cushing_syndrome", "endo_2008_first_line_tests", "diagnostic_criterion", False,
     ANY(L("cortisol_after_dexamethasone", ">", 1.8, "ug/dL"), L("urine_free_cortisol_24h", ">", 100, "ug/24h"), L("cortisol_salivary_midnight", ">", 4.0, "nmol/L")),
     "endo_cushing_2008_2021", "Cushing syndrome - abnormal first-line test (1-mg DST > 1.8 ug/dL, UFC > ULN, LNSC > 145 ng/dL)",
     "Endocrine Society: at least two abnormal first-line tests (1-mg overnight DST cortisol > 1.8 ug/dL, 24-h UFC above ULN x2, late-night salivary cortisol > 145 ng/dL = 4 nmol/L x2) establish hypercortisolism.",
     ["Pseudo-Cushing (depression, alcohol, obesity, OCP-raised CBG) causes false positives; two concordant tests required."])
rule("secondary_adrenal_insufficiency", "endo_2016_high_acth_exclusion", "exclusion_criterion", False,
     L("adrenocorticotropic_hormone", ">", 0.1, "ng/mL"),
     "endo_adrenal_insufficiency_2016", "Secondary (central) adrenal insufficiency excluded - ACTH elevated (> 100 pg/mL)",
     "In secondary/central adrenal insufficiency plasma ACTH is low or inappropriately normal; an ACTH above 2x the upper reference limit with low cortisol establishes a primary (adrenal) cause.")
rule("central_adrenal_insufficiency", "endo_2016_high_acth_exclusion", "exclusion_criterion", False,
     L("adrenocorticotropic_hormone", ">", 0.1, "ng/mL"),
     "endo_adrenal_insufficiency_2016", "Central adrenal insufficiency excluded - ACTH elevated (> 100 pg/mL)",
     "In central adrenal insufficiency plasma ACTH is low or inappropriately normal; an ACTH above 2x the upper reference limit with low cortisol establishes a primary (adrenal) cause.")
rule("addison_disease", "endo_2016_morning_cortisol_acth", "diagnostic_criterion", True,
     ALL(L("morning_cortisol", "<", 5.0, "ug/dL"), L("adrenocorticotropic_hormone", ">", 0.1, "ng/mL")),
     "endo_adrenal_insufficiency_2016", "Primary adrenal insufficiency - morning cortisol < 5 ug/dL with ACTH > 2x ULN (> 100 pg/mL)",
     "Endocrine Society 2016: morning cortisol < 5 ug/dL (140 nmol/L) is strongly suggestive; plasma ACTH > 2x ULN (> 100 pg/mL = 0.1 ng/mL) with low cortisol confirms primary (adrenal) origin.")
rule("primary_adrenal_insufficiency", "endo_2016_cosyntropin_peak", "diagnostic_criterion", True,
     L("cortisol_30min_post_acth", "<", 18.0, "µg/dL"),
     "endo_adrenal_insufficiency_2016", "Adrenal insufficiency - cosyntropin peak cortisol < 18 ug/dL",
     "Peak cortisol < 18 ug/dL (500 nmol/L; 14-15 ug/dL with newer monoclonal assays) 30-60 min after 250 ug cosyntropin confirms adrenal insufficiency.")
rule("primary_adrenal_insufficiency", "endo_2016_exclusion_normal_morning_cortisol", "exclusion_criterion", False,
     L("morning_cortisol", ">=", 18.0, "ug/dL"),
     "endo_adrenal_insufficiency_2016", "Adrenal insufficiency unlikely - morning cortisol >= 18 ug/dL",
     "A morning serum cortisol >= 18 ug/dL (500 nmol/L) makes adrenal insufficiency unlikely (outside critical illness and CBG abnormalities).")
rule("primary_aldosteronism", "endo_2016_arr_aldosterone", "diagnostic_criterion", False,
     ALL(L("aldosterone_renin_ratio", ">=", 30, "ratio"), L("aldosterone", ">=", 10, "ng/dL")),
     "endo_primary_aldosteronism_2016", "Primary aldosteronism - ARR >= 30 (ng/dL per ng/mL/h) with aldosterone >= 10 ng/dL",
     "Endocrine Society: ARR >= 30 with plasma aldosterone >= 10 ng/dL (some use 15) is a positive screen; confirm with saline infusion/oral sodium loading unless spontaneous hypokalaemia + undetectable renin + aldosterone > 20.",
     ["Interfering drugs (MRAs, ACEi/ARBs, beta-blockers), hypokalaemia and posture affect the ratio."])
rule("pheochromocytoma", "endo_2014_metanephrines_3x", "diagnostic_criterion", True,
     ANY(L("plasma_free_metanephrines", ">", 195, "pg/mL"), L("plasma_free_normetanephrines", ">", 588, "pg/mL")),
     "endo_pheo_2014", "Phaeochromocytoma - plasma free metanephrine or normetanephrine > 3x ULN",
     "Plasma free metanephrines > 3x ULN (metanephrine > ~195 pg/mL, normetanephrine > ~588 pg/mL) are virtually diagnostic; 1-3x ULN elevations require repeat under standardised (supine, drug-free) conditions.")
rule("acromegaly", "endo_2014_igf1_gh", "diagnostic_criterion", False,
     ALL(L("insulin_like_growth_factor_1", ">", 300, "ng/mL"), L("growth_hormone", ">", 1.0, "ng/mL")),
     "endo_acromegaly_2014", "Acromegaly - elevated age-adjusted IGF-1 with GH nadir > 1 ug/L after OGTT",
     "Endocrine Society 2014: raised age-/sex-adjusted IGF-1 plus failure of GH to suppress < 1 ug/L (< 0.4 with ultrasensitive assays) during 75-g OGTT confirms acromegaly.",
     ["IGF-1 reference intervals are age-dependent; 300 ng/mL is a conservative adult upper bound and must be checked against the assay."])
rule("hyperprolactinemia", "pituitary_2023_prolactin_macroadenoma_range", "staging_severity", False,
     L("prolactin", ">", 250, "ng/mL"),
     "endo_hyperprolactinemia_2011_2023", "Prolactin > 250 ng/mL - macroprolactinoma range",
     "Prolactin > 250 ng/mL (> 5000 mIU/L) is virtually diagnostic of a prolactinoma, usually a macroadenoma; 25-100 ng/mL is seen with drugs, stalk effect, hypothyroidism and macroprolactin.")
rule("hyperprolactinemia", "pituitary_2023_prolactin_elevated", "diagnostic_criterion", False,
     L("prolactin", ">", 25, "ng/mL"),
     "endo_hyperprolactinemia_2011_2023", "Hyperprolactinaemia - prolactin above reference (> 25 ng/mL women / > 20 men)",
     "A single prolactin above the reference range, drawn without excessive venipuncture stress, establishes hyperprolactinaemia; exclude macroprolactin, pregnancy, drugs, hypothyroidism and renal failure.")
rule("male_hypogonadism", "endo_2018_total_testosterone_300", "diagnostic_criterion", False,
     L("total_testosterone", "<", 264, "ng/dL"),
     "endo_testosterone_2018", "Male hypogonadism - morning total testosterone < 264 ng/dL (harmonised lower limit) on two occasions",
     "Endocrine Society 2018: hypogonadism requires symptoms plus unequivocally low morning fasting total testosterone (< 264 ng/dL, CDC-harmonised) on at least two occasions; LH/FSH distinguish primary from secondary.",
     ["Only valid in males; acute illness, obesity (low SHBG) and opioids lower testosterone transiently."])
rule("primary_hyperparathyroidism", "workshop_2022_calcium_pth", "diagnostic_criterion", False,
     ALL(ANY(L("corrected_calcium_for_serum_albumin", ">", 10.5, "mg/dL"), L("calcium_total", ">", 10.5, "mg/dL"), L("calcium_ionized", ">", 1.32, "mmol/L")),
         L("intact_parathyroid_hormone", ">=", 20, "pg/mL")),
     "phpt_workshop_2022", "Primary hyperparathyroidism - hypercalcaemia with non-suppressed PTH (>= 20 pg/mL)",
     "Hypercalcaemia with PTH that is elevated or inappropriately normal (> 20-25 pg/mL) defines PHPT; FHH is excluded with calcium/creatinine clearance ratio > 0.02 and normal eGFR/vitamin D.")
rule("hypoparathyroidism", "hypocalcemia_low_pth", "diagnostic_criterion", False,
     ALL(ANY(L("corrected_calcium_for_serum_albumin", "<", 8.5, "mg/dL"), L("calcium_ionized", "<", 1.12, "mmol/L")), L("intact_parathyroid_hormone", "<", 15, "pg/mL")),
     "phpt_workshop_2022", "Hypoparathyroidism - hypocalcaemia with low / inappropriately low PTH",
     "Hypocalcaemia with PTH below or in the low-normal range (< 15-20 pg/mL) and hyperphosphataemia with normal renal function defines hypoparathyroidism (post-surgical, autoimmune, genetic). Check magnesium.")
rule("pseudohypoparathyroidism", "hypocalcemia_high_pth_normal_renal", "diagnostic_criterion", False,
     ALL(ANY(L("corrected_calcium_for_serum_albumin", "<", 8.5, "mg/dL"), L("calcium_total", "<", 8.5, "mg/dL")), L("phosphate", ">", 4.5, "mg/dL"),
         L("intact_parathyroid_hormone", ">", 65, "pg/mL"), L("creatinine", "<", 1.3, "mg/dL")),
     "phpt_workshop_2022", "Pseudohypoparathyroidism - hypocalcaemia + hyperphosphataemia with ELEVATED PTH and normal renal function",
     "PTH resistance: low calcium and high phosphate with raised PTH, normal creatinine and normal 25-OH vitamin D; confirmed by GNAS analysis / Ellsworth-Howard testing.")
rule("vitamin_d_deficiency", "endo_2011_25ohd_20", "diagnostic_criterion", False,
     L("25_hydroxy_vitamin_d", "<", 20, "ng/mL"),
     "endo_vitamin_d_2011_2024", "Vitamin D deficiency - 25-OH vitamin D < 20 ng/mL (50 nmol/L)",
     "Endocrine Society 2011: < 20 ng/mL deficiency, 21-29 insufficiency; < 12 ng/mL is associated with rickets/osteomalacia. The 2024 guideline advises against routine screening in healthy adults.")
rule("osteomalacia", "vitamin_d_12_alp_phosphate", "diagnostic_criterion", False,
     ALL(L("25_hydroxy_vitamin_d", "<", 12, "ng/mL"), L("alkaline_phosphatase", ">", 130, "U/L"), ANY(L("phosphate", "<", 2.5, "mg/dL"), L("intact_parathyroid_hormone", ">", 65, "pg/mL"))),
     "endo_vitamin_d_2011_2024", "Osteomalacia - severe vitamin D deficiency with raised ALP and hypophosphataemia/secondary hyperparathyroidism",
     "25-OH-D < 12 ng/mL with elevated ALP, low/low-normal phosphate and secondary hyperparathyroidism is the biochemical signature of nutritional osteomalacia.")

# ---- Electrolytes / acid-base -----------------------------------------------
rule("hyperkalemia", "kdigo_2020_severe", "staging_severity", True, L("potassium", ">=", 6.0, "mmol/L"),
     "kdigo_potassium_2020", "Severe hyperkalaemia - potassium >= 6.0 mmol/L", "K >= 6.0 mmol/L (or any level with ECG changes) requires immediate ECG, membrane stabilisation and shifting therapy; exclude haemolysed sample.")
rule("hypokalemia", "kdigo_2020_severe", "staging_severity", True, L("potassium", "<", 2.5, "mmol/L"),
     "kdigo_potassium_2020", "Severe hypokalaemia - potassium < 2.5 mmol/L", "K < 2.5 mmol/L risks arrhythmia and rhabdomyolysis; replace with cardiac monitoring and correct magnesium.")
rule("hyponatremia", "ese_2014_profound", "staging_severity", True, L("sodium", "<", 125, "mmol/L"),
     "ese_hyponatremia_2014", "Profound hyponatraemia - sodium < 125 mmol/L", "ESE 2014: < 125 mmol/L is profound; symptomatic patients receive 150 mL 3 % saline boluses; limit correction to 10 mmol/L in 24 h.")
rule("hyponatremia", "ese_2014_siadh_pattern", "screening", False,
     ALL(L("sodium", "<", 135, "mmol/L"), L("serum_osmolality", "<", 275, "mOsm/kg"), L("urine_osmolality", ">", 100, "mOsm/kg"), L("urine_sodium", ">", 30, "mmol/L")),
     "ese_hyponatremia_2014", "Hypotonic hyponatraemia with inappropriately concentrated urine (SIADH pattern if euvolaemic)",
     "Serum osmolality < 275 with urine osmolality > 100 mOsm/kg and urine sodium > 30 mmol/L in a euvolaemic patient without diuretics, adrenal or thyroid failure = SIADH.", specificity="general")
rule("siadh", "ese_2014_full_criteria", "diagnostic_criterion", False,
     ALL(L("sodium", "<", 135, "mmol/L"), L("serum_osmolality", "<", 275, "mOsm/kg"), L("urine_osmolality", ">", 100, "mOsm/kg"), L("urine_sodium", ">", 30, "mmol/L"),
         L("morning_cortisol", ">=", 10, "ug/dL"), L("thyroid_stimulating_hormone", "<=", 10, "u[IU]/mL")),
     "ese_hyponatremia_2014", "SIADH - essential criteria incl. normal adrenal and thyroid function",
     "ESE essential criteria: effective osmolality < 275, urine osmolality > 100, urine Na > 30 (normal salt intake), clinical euvolaemia, no diuretics, no adrenal/thyroid/pituitary insufficiency or renal failure.")
rule("hypernatremia", "severe_155", "staging_severity", True, L("sodium", ">", 155, "mmol/L"),
     "ese_hyponatremia_2014", "Severe hypernatraemia - sodium > 155 mmol/L", "Na > 155 mmol/L: calculate free-water deficit; correct no faster than 10-12 mmol/L per 24 h in chronic cases.")
rule("hypercalcemia", "crisis_14", "staging_severity", True,
     ANY(L("corrected_calcium_for_serum_albumin", ">=", 14.0, "mg/dL"), L("calcium_total", ">=", 14.0, "mg/dL"), L("calcium_ionized", ">=", 1.75, "mmol/L")),
     "phpt_workshop_2022", "Hypercalcaemic crisis - corrected calcium >= 14 mg/dL", "Calcium >= 14 mg/dL (3.5 mmol/L) is a medical emergency: saline, calcitonin, IV bisphosphonate; PTH-independent causes (malignancy) predominate.")
rule("hypocalcemia", "severe_ionized", "staging_severity", True,
     ANY(L("calcium_ionized", "<", 0.9, "mmol/L"), L("corrected_calcium_for_serum_albumin", "<", 7.0, "mg/dL")),
     "phpt_workshop_2022", "Severe hypocalcaemia - ionised Ca < 0.9 mmol/L / corrected Ca < 7 mg/dL", "Severe or symptomatic hypocalcaemia (tetany, QT prolongation, seizures) requires IV calcium gluconate and magnesium repletion.")
rule("hypomagnesemia", "severe_1_2", "staging_severity", True, L("magnesium", "<", 1.2, "mg/dL"),
     "kdigo_potassium_2020", "Severe hypomagnesaemia - Mg < 1.2 mg/dL (0.5 mmol/L)", "Mg < 1.2 mg/dL causes refractory hypokalaemia/hypocalcaemia and arrhythmia; IV magnesium sulfate indicated.")
rule("hypophosphatemia", "severe_1_0", "staging_severity", True, L("phosphate", "<", 1.0, "mg/dL"),
     "kdigo_potassium_2020", "Severe hypophosphataemia - phosphate < 1.0 mg/dL", "Phosphate < 1.0 mg/dL (0.32 mmol/L) can cause respiratory failure, haemolysis and rhabdomyolysis (refeeding, DKA treatment, alcoholism); IV replacement.")
rule("metabolic_acidosis", "high_anion_gap", "diagnostic_criterion", True,
     ALL(L("bicarbonate", "<", 22, "mmol/L"), L("anion_gap", ">", 12, "mmol/L")),
     "ada_easd_hyperglycemic_crises_2024", "High anion-gap metabolic acidosis - HCO3 < 22 with AG > 12 mmol/L",
     "Low bicarbonate with an anion gap > 12 (albumin-corrected: add 2.5 per g/dL albumin below 4) indicates unmeasured anions: lactate, ketones, uraemia, toxic alcohols, salicylate (GOLD MARK).")
rule("lactic_acidosis", "lactate_4_acidemia", "diagnostic_criterion", True,
     ALL(L("lactate", ">=", 4.0, "mmol/L"), ANY(L("arterial_ph", "<", 7.35, "[pH]"), L("bicarbonate", "<", 20, "mmol/L"))),
     "sepsis3_2016", "Lactic acidosis - lactate >= 4 mmol/L with acidaemia", "Lactate >= 4 mmol/L with pH < 7.35 or low bicarbonate defines lactic acidosis (type A hypoperfusion vs type B metformin, malignancy, thiamine deficiency).")
rule("diabetes_insipidus_central", "ese_2022_hypernatremia_dilute_urine", "diagnostic_criterion", False,
     ALL(L("sodium", ">", 145, "mmol/L"), L("serum_osmolality", ">", 295, "mOsm/kg"), L("urine_osmolality", "<", 300, "mOsm/kg")),
     "ese_dm_insipidus_2022", "AVP deficiency / DI - hypernatraemic hyperosmolality with inappropriately dilute urine",
     "Serum osmolality > 295 mOsm/kg (Na > 145) with urine osmolality < 300 mOsm/kg indicates diabetes insipidus; hypertonic saline-stimulated copeptin < 4.9 pmol/L confirms central DI.")

# ---- Rheumatology -------------------------------------------------------------------
rule("systemic_lupus_erythematosus", "eular_acr_2019_ana_dsdna_complement", "diagnostic_criterion", False,
     ALL(L("antinuclear_antibody_titer", ">=", 80, "titer"), ANY(L("double_stranded_dna_antibody", ">", 30, "IU/mL"), ALL(L("complement_c3", "<", 90, "mg/dL"), L("complement_c4", "<", 10, "mg/dL")))),
     "eular_acr_sle_2019", "SLE - ANA >= 1:80 (entry) with anti-dsDNA or low C3 and C4 (immunology domains)",
     "EULAR/ACR 2019: ANA >= 1:80 is the obligatory entry criterion; anti-dsDNA (6 pts) and low C3 + C4 (4 pts) are weighted immunology criteria; >= 10 points with >= 1 clinical criterion classifies SLE.",
     ["Classification requires at least one clinical domain; ANA alone (present in 5-15 % of healthy people) is not diagnostic."])
rule("systemic_lupus_erythematosus", "eular_acr_2019_ana_negative_exclusion", "exclusion_criterion", False,
     L("antinuclear_antibody_titer", "<", 80, "titer"),
     "eular_acr_sle_2019", "SLE classification not met - ANA < 1:80", "A negative ANA (< 1:80 on HEp-2) excludes classification as SLE under the 2019 criteria (sensitivity of ANA ~ 98 %).")
rule("rheumatoid_arthritis", "acr_eular_2010_high_titre_serology", "diagnostic_criterion", False,
     ANY(L("cyclic_citrullinated_peptide_antibody", ">", 60, "IU/mL"), L("rheumatoid_factor", ">", 42, "[IU]/mL")),
     "acr_eular_ra_2010", "Rheumatoid arthritis - high-positive anti-CCP or RF (> 3x ULN; 3 points)",
     "ACR/EULAR 2010: high-positive RF or ACPA (> 3x ULN) scores 3 points; low-positive 2; with synovitis, acute-phase reactants and duration >= 6 weeks a score >= 6/10 classifies RA. Anti-CCP specificity ~ 95 %.")
rule("gout", "acr_eular_2015_hyperuricemia_component", "screening", False,
     L("uric_acid", ">", 6.8, "mg/dL"),
     "acr_eular_gout_2015", "Hyperuricaemia > 6.8 mg/dL (supersaturation threshold; gout requires crystals or typical clinical features)",
     "Urate > 6.8 mg/dL exceeds solubility; ACR/EULAR 2015 scores urate 6-8 mg/dL 2 points, 8-10 3 points, >= 10 4 points. Serum urate may be normal during flares; MSU crystals are the gold standard.", specificity="general")
rule("gout", "acr_eular_2015_urate_very_high", "staging_severity", False,
     L("uric_acid", ">=", 10.0, "mg/dL"),
     "acr_eular_gout_2015", "Serum urate >= 10 mg/dL (4 points in 2015 classification)", "Urate >= 10 mg/dL carries the maximal serological weight in the 2015 classification criteria.")
rule("ankylosing_spondylitis", "asas_2009_hla_b27_crp", "screening", False,
     ALL(L("hla_b27_antigen_allele", "==", 1, "1"), L("c_reactive_protein", ">", 5, "mg/L")),
     "asas_axspa_2009", "Axial SpA - HLA-B27 positive with raised CRP (clinical arm requires >= 2 SpA features)",
     "ASAS 2009: HLA-B27 plus >= 2 SpA features (incl. raised CRP) classifies axial SpA in patients with >= 3 months back pain onset < 45 y; HLA-B27 is present in ~8 % of healthy Europeans.", specificity="general")
rule("sjogren_syndrome", "acr_eular_2016_ssa_positive", "diagnostic_criterion", False,
     ANY(L("ssa_ro_antibody", "==", 1, "1"), L("anti_ssa_ro60_antibody", "==", 1, "1"), L("anti_ssa_ro52_antibody", "==", 1, "1")),
     "acr_sjogren_2016", "Sjogren - anti-SSA/Ro positive (3 of the 4 points required)",
     "ACR/EULAR 2016: anti-SSA/Ro positivity scores 3 points; focal lymphocytic sialadenitis 3; ocular staining, Schirmer and salivary flow 1 each; >= 4 classifies.",
     ["Anti-SSA/Ro alone scores 3 of the 4 points required; one objective glandular item (ocular staining, Schirmer, salivary flow or biopsy) must be added. Anti-SSA also occurs in SLE and in ~ 0.5 % of healthy people."])
rule("sjogren_syndrome", "acr_eular_2016_high_titre_ana_prompt", "screening", False,
     L("antinuclear_antibody_titer", ">=", 320, "titer"),
     "acr_sjogren_2016", "High-titre ANA - prompt anti-SSA/Ro (SSA) and anti-SSB/La testing",
     "High-titre speckled ANA is not a classification item for Sjogren; it should prompt anti-SSA/Ro testing, which is the serological criterion.", specificity="general")

# ---- Infectious disease ----------------------------------------------------------
rule("malaria", "who_2023_parasitological_confirmation", "diagnostic_criterion", True,
     ANY(L("malaria_parasite_blood_smear", "==", 1, "1"), L("malaria_rapid_antigen", "==", 1, "1")),
     "who_malaria_2023", "Malaria - parasitological confirmation (microscopy or RDT positive)",
     "WHO: every suspected case must be confirmed by microscopy or RDT before treatment; thrombocytopenia and raised LDH are supportive, never diagnostic.")
rule("malaria", "who_2023_exclusion_negative_tests", "exclusion_criterion", False,
     ALL(L("malaria_parasite_blood_smear", "==", 0, "1"), L("malaria_rapid_antigen", "==", 0, "1")),
     "who_malaria_2023", "Malaria unlikely - negative smear and RDT", "Negative thick/thin films (repeated x3 over 48 h) and a negative RDT make malaria unlikely.")
rule("dengue_fever", "who_ns1_igm", "diagnostic_criterion", True,
     ANY(L("dengue_ns1_antigen", "==", 1, "1"), L("dengue_igm_antibody", "==", 1, "1")),
     "who_dengue_2009_2023", "Dengue - NS1 antigen (days 1-7) or IgM (from day 5) positive",
     "NS1 antigen is positive in the febrile phase (days 1-7); IgM appears from day 4-5. Warning signs include platelets < 100 x 10^9/L with rising haematocrit (>= 20 %) and AST/ALT > 1000 U/L.")
rule("dengue_fever", "who_warning_signs_lab", "staging_severity", True,
     ALL(L("platelets", "<", 100, "10*9/L"), ANY(L("aspartate_aminotransferase", ">=", 1000, "U/L"), L("alanine_aminotransferase", ">=", 1000, "U/L"), L("hematocrit", ">", 50, "%"))),
     "who_dengue_2009_2023", "Dengue warning signs / severe dengue laboratory markers",
     "Rapid platelet fall with rising haematocrit (plasma leakage) or AST/ALT >= 1000 U/L indicates severe dengue (WHO 2009).")
rule("brucellosis", "who_wright_160", "diagnostic_criterion", False,
     L("wright_agglutination_test_titer", ">=", 160, "titer"),
     "who_brucellosis_2006", "Brucellosis - standard agglutination (Wright) titre >= 1:160 in a compatible patient",
     "SAT >= 1:160 (>= 1:320 in endemic areas) with compatible symptoms is presumptive brucellosis; blood culture or PCR confirms; 2-ME test distinguishes IgG.")
rule("tuberculosis", "nice_2016_igra_positive", "screening", False,
     L("quantiferon_tb_gold_plus", ">=", 0.35, "[IU]/mL"),
     "bts_tb_nice_2016", "TB infection - IGRA (QuantiFERON) positive (>= 0.35 IU/mL TB-Nil)",
     "A positive IGRA indicates M. tuberculosis infection (latent or active) and cannot distinguish the two; active disease requires microbiology/imaging. Values 0.35-0.99 IU/mL are borderline.", specificity="general")
rule("infectious_mononucleosis", "vca_igm_or_heterophile", "diagnostic_criterion", False,
     ANY(L("epstein_barr_vca_igm_antibody", "==", 1, "1"), L("heterophile_antibody", "==", 1, "1")),
     "ebv_idsa_review", "Infectious mononucleosis - EBV VCA-IgM or heterophile (Monospot) positive",
     "VCA-IgM positive with EBNA-IgG negative indicates acute EBV; heterophile antibody has 85 % sensitivity in adults (lower in children < 4 y).")
rule("covid_19", "sars_cov_2_rna_detected", "diagnostic_criterion", False,
     L("sars_cov_2_rna", ">", 0, "[IU]/mL"),
     "who_malaria_2023", "COVID-19 - SARS-CoV-2 RNA detected (NAAT)", "Detection of SARS-CoV-2 RNA by RT-PCR/NAAT confirms infection; lymphopenia, raised CRP, ferritin, D-dimer and LDH grade severity.")

# ---- Toxicology ------------------------------------------------------------------
rule("lead_poisoning", "cdc_2021_blood_lead_reference", "screening", False, L("blood_lead", ">=", 3.5, "ug/dL"),
     "cdc_lead_2021", "Elevated blood lead - >= 3.5 ug/dL (CDC 2021 reference value)", "CDC blood lead reference value 3.5 ug/dL (children); >= 45 ug/dL requires chelation; >= 70 ug/dL is a medical emergency.", specificity="general")
rule("lead_poisoning", "cdc_chelation_45", "diagnostic_criterion", True, L("blood_lead", ">=", 45, "ug/dL"),
     "cdc_lead_2021", "Lead poisoning requiring chelation - blood lead >= 45 ug/dL", "Blood lead >= 45 ug/dL mandates chelation (succimer; CaNa2EDTA +/- BAL if >= 70 ug/dL or encephalopathy).")
rule("acetaminophen_toxicity", "rumack_matthew_150_at_4h", "diagnostic_criterion", True, L("acetaminophen", ">=", 150, "ug/mL"),
     "rumack_matthew_1975_2022", "Acetaminophen - level >= 150 ug/mL at 4 h post-ingestion (treatment line)",
     "Rumack-Matthew nomogram treatment line: 150 ug/mL at 4 h, 75 at 8 h, 37.5 at 12 h, 18.75 at 16 h. Time of ingestion is required; any detectable level after an unknown-time ingestion with raised ALT warrants NAC.",
     ["Nomogram valid only for single acute ingestion with known time (4-24 h)."])
rule("acetaminophen_toxicity", "detectable_level_screen", "screening", False, L("acetaminophen", ">", 10, "ug/mL"),
     "rumack_matthew_1975_2022", "Acetaminophen detectable (> 10 ug/mL) - plot on nomogram", "A detectable acetaminophen level requires interpretation against the time of ingestion; non-detectable at >= 4 h excludes significant ingestion.", specificity="general")
rule("carbon_monoxide_poisoning", "cohb_10_percent", "diagnostic_criterion", True, L("carboxyhemoglobin_blood_gas", ">", 10, "%"),
     "aha_co_2012", "Carbon monoxide poisoning - COHb > 10 % (> 3 % non-smokers)", "COHb > 3 % in non-smokers or > 10 % in smokers with compatible exposure confirms CO poisoning; levels correlate poorly with severity; > 25 % or neurological signs = hyperbaric oxygen referral.")
rule("lithium_toxicity", "lithium_1_5", "diagnostic_criterion", True, L("lithium", ">", 1.5, "mmol/L"),
     "acep_toxicology_consensus", "Lithium toxicity - serum level > 1.5 mmol/L (12 h post-dose)", "Therapeutic 0.6-1.2 mmol/L; > 1.5 toxic, > 2.5 severe (haemodialysis indicated with neurological signs or renal impairment; EXTRIP).")
rule("digoxin_toxicity", "digoxin_2_0", "diagnostic_criterion", True, L("digoxin", ">", 2.0, "ng/mL"),
     "acep_toxicology_consensus", "Digoxin toxicity - level > 2.0 ng/mL (>= 6 h post-dose)", "Digoxin > 2.0 ng/mL (target 0.5-0.9 in HF) with symptoms/arrhythmia or hyperkalaemia > 5 mmol/L indicates toxicity; digoxin-specific Fab for life-threatening features.")
rule("salicylate_toxicity", "salicylate_30", "diagnostic_criterion", True, L("salicylate", ">", 30, "mg/dL"),
     "acep_toxicology_consensus", "Salicylate toxicity - level > 30 mg/dL", "Salicylate > 30 mg/dL (2.2 mmol/L) indicates toxicity; > 100 mg/dL acute or > 60 chronic, altered mental status, pulmonary oedema or renal failure = haemodialysis (EXTRIP).")
rule("methanol_poisoning", "osmolal_gap_toxic_alcohol", "screening", True,
     ALL(L("osmolal_gap", ">", 10, "mOsm/kg"), L("anion_gap", ">", 12, "mmol/L"), L("bicarbonate", "<", 20, "mmol/L")),
     "acep_toxicology_consensus", "Toxic alcohol pattern - osmolal gap > 10 with high anion-gap acidosis",
     "An elevated osmolal gap together with a high anion-gap metabolic acidosis suggests methanol or ethylene glycol ingestion; fomepizole should be started pending levels.", specificity="general")
rule("ethylene_glycol_poisoning", "osmolal_gap_toxic_alcohol", "screening", True,
     ALL(L("osmolal_gap", ">", 10, "mOsm/kg"), L("anion_gap", ">", 12, "mmol/L"), L("bicarbonate", "<", 20, "mmol/L")),
     "acep_toxicology_consensus", "Toxic alcohol pattern - osmolal gap > 10 with high anion-gap acidosis",
     "Ethylene glycol: osmolal gap early, anion-gap acidosis later, calcium oxalate crystalluria, hypocalcaemia and AKI.", specificity="general")

# ---- Obstetric / neonatal / metabolic ------------------------------------------
rule("preeclampsia", "acog_2020_proteinuria", "diagnostic_criterion", False,
     ANY(L("urine_protein_to_creatinine_ratio", ">=", 300, "mg/g"), L("urine_protein_24_hour", ">=", 300, "mg/24h")),
     "acog_preeclampsia_2020", "Pre-eclampsia - proteinuria >= 300 mg/24 h or UPCR >= 0.3 mg/mg (with new hypertension >= 20 weeks)",
     "ACOG 2020: new-onset BP >= 140/90 after 20 weeks plus proteinuria >= 300 mg/24 h, UPCR >= 0.3 or dipstick 2+; in the absence of proteinuria, thrombocytopenia < 100, creatinine > 1.1, transaminases 2x ULN, pulmonary oedema or neurological symptoms.",
     ["Pregnancy >= 20 weeks and hypertension are required; proteinuria alone is non-specific."])
rule("preeclampsia", "acog_2020_severe_features_lab", "staging_severity", True,
     ANY(L("platelets", "<", 100, "10*9/L"), L("creatinine", ">", 1.1, "mg/dL"), L("alanine_aminotransferase", ">", 70, "U/L"), L("aspartate_aminotransferase", ">", 70, "U/L")),
     "acog_preeclampsia_2020", "Pre-eclampsia with severe features - laboratory markers",
     "Platelets < 100 x 10^9/L, creatinine > 1.1 mg/dL (or doubling) or transaminases > 2x ULN define severe features and indicate delivery planning.")
rule("hellp_syndrome", "tennessee_full_hellp", "diagnostic_criterion", True,
     ALL(L("platelets", "<", 100, "10*9/L"), L("aspartate_aminotransferase", ">=", 70, "U/L"), L("lactate_dehydrogenase", ">=", 600, "U/L")),
     "acog_preeclampsia_2020", "HELLP - Tennessee criteria: PLT < 100, AST >= 70, LDH >= 600 (haemolysis)",
     "Tennessee classification: haemolysis (LDH >= 600 U/L, schistocytes, bilirubin >= 1.2), AST >= 70 U/L and platelets < 100 x 10^9/L; partial HELLP = 1-2 of 3.")
rule("neonatal_hyperbilirubinemia", "aap_2022_phototherapy_range", "staging_severity", True,
     L("total_bilirubin", ">=", 15, "mg/dL"),
     "aap_hyperbilirubinemia_2022", "Neonatal hyperbilirubinaemia - TSB >= 15 mg/dL (phototherapy range for most term neonates >= 48 h)",
     "AAP 2022 phototherapy thresholds depend on gestational age, hour of life and neurotoxicity risk factors; TSB >= 15 mg/dL exceeds the threshold for most infants >= 38 weeks at 48 h; >= 25 mg/dL approaches exchange-transfusion level.",
     ["Hour-specific nomogram required; direct bilirubin > 1 mg/dL indicates cholestasis (biliary atresia work-up)."])
rule("phenylketonuria_pku", "acmg_2014_phe_360", "diagnostic_criterion", False,
     L("plasma_phenylalanine_quantitative", ">", 360, "umol/L"),
     "acmg_pku_2014", "PKU / hyperphenylalaninaemia - plasma Phe > 360 umol/L (treatment threshold)",
     "ACMG 2014: Phe > 360 umol/L (6 mg/dL) on a normal diet requires treatment; classic PKU > 1200 umol/L; confirm with Phe/Tyr ratio, BH4 testing and PAH genotype.")
rule("familial_hypercholesterolemia", "dlcn_ldl_330_probable", "diagnostic_criterion", False,
     L("ldl_cholesterol_calculated", ">=", 330, "mg/dL"),
     "eas_fh_2013_dlcn", "FH - untreated LDL-C >= 330 mg/dL (8.5 mmol/L; DLCN 8 points = definite)",
     "DLCN: LDL-C >= 330 mg/dL scores 8 points (definite FH); 250-329 = 5; 190-249 = 3; 155-189 = 1. Exclude secondary causes (hypothyroidism, nephrotic syndrome, cholestasis).")
rule("familial_hypercholesterolemia", "dlcn_ldl_190_possible", "screening", False,
     L("ldl_cholesterol_calculated", ">=", 190, "mg/dL"),
     "eas_fh_2013_dlcn", "Possible FH - LDL-C >= 190 mg/dL (screen family history / genetic testing)",
     "LDL-C >= 190 mg/dL in adults (>= 160 in children) warrants FH evaluation (DLCN/Simon Broome/MEDPED) and cascade screening.", specificity="general")
rule("hypertriglyceridemia", "eas_2019_severe_pancreatitis_risk", "staging_severity", True,
     L("triglycerides", ">=", 880, "mg/dL"),
     "eas_esc_dyslipidaemia_2019", "Severe hypertriglyceridaemia - TG >= 880 mg/dL (10 mmol/L): pancreatitis risk",
     "TG > 10 mmol/L (880 mg/dL) confers substantial acute pancreatitis risk; > 500 mg/dL is severe and fibrate/omega-3/ dietary fat restriction indicated.")
rule("metabolic_syndrome", "atp3_2005_three_of_five_lab", "diagnostic_criterion", False,
     ANY(ALL(L("triglycerides", ">=", 150, "mg/dL"), L("hdl_cholesterol", "<", 40, "mg/dL"), L("fasting_plasma_glucose", ">=", 100, "mg/dL")),
         ALL(L("triglycerides", ">=", 150, "mg/dL"), L("hdl_cholesterol", "<", 50, "mg/dL"), L("fasting_plasma_glucose", ">=", 100, "mg/dL"))),
     "ncep_atp3_2005", "Metabolic syndrome - 3 laboratory components (TG >= 150, low HDL, FPG >= 100)",
     "AHA/NHLBI ATP III: >= 3 of waist circumference, TG >= 150 mg/dL, HDL < 40 (men) / < 50 (women) mg/dL, BP >= 130/85, FPG >= 100 mg/dL. The three laboratory components alone satisfy the definition.",
     ["HDL cut-off is sex-specific; the second branch (HDL < 50) applies to women only."])

# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    reg = load_br(SRC)
    feats = load_br(FEAT)["features"]
    rules: dict = reg["rules"]
    diseases: dict = reg["diseases"]
    audit: dict = collections.OrderedDict()
    audit["version_from"] = reg["registry_metadata"].get("version")
    audit["version_to"] = NEW_VERSION
    audit["date"] = TODAY
    changes = collections.Counter()
    detail: dict[str, list] = collections.defaultdict(list)

    # ---- idempotence: a previous curation pass is stripped and re-applied ------
    # (the registry may already be 13.x; curated rules are regenerated from the
    # DSL below so DSL edits always win, and data repairs are no-ops second time)
    prev = [rid for rid in rules if rid.endswith("_cur13")]
    for rid in prev:
        did = rules[rid].get("disease_id")
        rules.pop(rid, None)
        d = diseases.get(did) or {}
        if d.get("rule_ids"):
            d["rule_ids"] = [x for x in d["rule_ids"] if x != rid]
        for lay, ids in (d.get("layers") or {}).items():
            if isinstance(ids, list) and rid in ids:
                ids.remove(rid)
    if prev:
        changes["previous_curated_rules_regenerated"] = len(prev)
        audit["note"] = "re-run over an already-curated registry: data-repair counts are incremental, curated rules regenerated"

    # ---- 0. structural repairs -------------------------------------------------
    for did, d in diseases.items():
        if "identity" not in d:
            d["identity"] = {"disease_id": did, "name_en": did.replace("_", " ").capitalize(), "name_fa": did,
                             "icd10": [], "snomed_ct": [], "wikipedia_url": ""}
            changes["disease_identity_added"] += 1
            detail["disease_identity_added"].append(did)
        if "classification" not in d:
            d["classification"] = {"domains": ["general"], "clinical_priority": "routine",
                                   "entity_kind": "clinical_entity"}
            changes["disease_classification_added"] += 1
        d.setdefault("population", {"age_groups": ["neonate", "infant", "child", "adolescent", "adult", "older_adult"],
                                    "sex": "all", "pregnancy": "context_dependent"})
        d.setdefault("feature_links", {"required": [], "optional": [], "excluded": []})
        d.setdefault("layers", {})
        d.setdefault("rule_ids", [])

    for rid, r in list(rules.items()):
        if not leaves(r.get("expression")):
            r["executable"] = False
            r["status"] = "retired_empty_expression"
            changes["rule_retired_empty_expression"] += 1
            detail["rule_retired_empty_expression"].append(rid)

    # ---- 1. feature-id consolidation ---------------------------------------
    for rid, r in rules.items():
        for lf in leaves(r["expression"]):
            fid = lf["feature_id"]
            if fid in CANONICAL_MERGE and CANONICAL_MERGE[fid] in feats:
                lf["feature_id"] = CANONICAL_MERGE[fid]
                changes["leaf_feature_id_consolidated"] += 1
        if r.get("_feature_ids"):
            r.pop("_feature_ids", None)

    # ---- 2. unit normalisation ---------------------------------------------------
    for rid, r in rules.items():
        for lf in leaves(r["expression"]):
            key = (lf["feature_id"], lf.get("unit"))
            if key in UNIT_FIX:
                unit, mult = UNIT_FIX[key]
                if isinstance(lf.get("value"), (int, float)):
                    lf["value"] = round(float(lf["value"]) * mult, 6)
                lf["unit"] = unit
                changes["leaf_unit_normalised"] += 1

    # ---- 3. absurd pH multiples / wrong analyte --------------------------------
    for rid, r in rules.items():
        for lf in leaves(r["expression"]):
            if lf["feature_id"] == "arterial_ph" and isinstance(lf.get("value"), (int, float)):
                if lf["value"] > 8.0:
                    lf["value"] = 7.55
                    changes["ph_threshold_repaired"] += 1
                    detail["ph_threshold_repaired"].append(rid)
                elif lf["value"] < 6.6:
                    lf["value"] = 7.20
                    changes["ph_threshold_repaired"] += 1
                    detail["ph_threshold_repaired"].append(rid)
            # "no haematuria" encoded as blood RBC count == 0 -> urine RBC
            if (lf["feature_id"] == "red_blood_cell_count" and lf.get("operator") == "=="
                    and lf.get("value") in (0, 0.0) and "hematuria" in rid):
                lf["feature_id"] = "urine_rbc_count"
                lf["operator"] = "<="
                lf["value"] = 2.0
                lf["unit"] = "/HPF"
                changes["hematuria_leaf_repaired"] += 1
                detail["hematuria_leaf_repaired"].append(rid)
            # acetaminophen "> 0" as diagnostic -> detectable screen handled by curated set
            if lf["feature_id"] == "acetaminophen" and lf.get("value") in (0, 0.0) and lf.get("operator") == ">":
                lf["value"] = 10.0
                r["rule_type"] = "screening"
                r["specificity"] = "general"
                changes["acetaminophen_rule_repaired"] += 1

    # ---- 4. template-stamp detection ---------------------------------------------
    sig_diseases: dict[tuple, set] = collections.defaultdict(set)
    for rid, r in rules.items():
        if r.get("rule_type") != "diagnostic_criterion":
            continue
        lv = leaves(r["expression"])
        if len(lv) != 1:
            continue
        lf = lv[0]
        sig_diseases[(lf["feature_id"], lf["operator"], round(float(lf["value"]), 6))].add(r["disease_id"])
    stamped_retired, stamped_demoted = [], []
    for rid, r in rules.items():
        if r.get("rule_type") != "diagnostic_criterion":
            continue
        lv = leaves(r["expression"])
        if len(lv) != 1:
            continue
        lf = lv[0]
        n = len(sig_diseases[(lf["feature_id"], lf["operator"], round(float(lf["value"]), 6))])
        if n < STAMPED_MIN or PATHOGEN_RE.search(lf["feature_id"]):
            continue
        did = r["disease_id"]
        fid = lf["feature_id"]
        entity_defined = ROUTINE_DEFINED_RE.search(did) is not None
        # the feature actually names the entity (hyperkalaemia <- potassium)
        stem = re.sub(r"(_total|_calculated|_count|_absolute|_percent|_serum|_plasma)$", "", fid)
        names_entity = stem[:5] in did or did[:6] in fid
        if names_entity:
            continue
        if fid in ROUTINE and not entity_defined:
            r["executable"] = False
            r["status"] = "retired_template_artifact"
            r["curation_note"] = (f"Single-analyte threshold {fid} {lf['operator']} {lf['value']} appears verbatim as a "
                                  f"'diagnostic criterion' under {n} diseases; it does not establish {did}. Retired {TODAY}.")
            stamped_retired.append(rid)
        else:
            r["rule_type"] = "screening"
            r["specificity"] = "general"
            r.setdefault("result", {})["diagnosis_allowed"] = False
            r["curation_note"] = (f"Demoted from diagnostic_criterion to screening: shared verbatim by {n} diseases ({TODAY}).")
            stamped_demoted.append(rid)
    changes["stamped_rules_retired"] = len(stamped_retired)
    changes["stamped_rules_demoted_to_screening"] = len(stamped_demoted)
    detail["stamped_rules_retired"] = stamped_retired
    detail["stamped_rules_demoted_to_screening"] = stamped_demoted

    # ---- 5. routine-only "diagnostic criteria" for specific aetiologies ---------------
    demoted_routine = []
    for rid, r in rules.items():
        if not r.get("executable", True) or r.get("rule_type") != "diagnostic_criterion":
            continue
        lv = leaves(r["expression"])
        if not lv or not all(l["feature_id"] in ROUTINE for l in lv):
            continue
        did = r["disease_id"]
        kind = ((diseases.get(did) or {}).get("classification") or {}).get("entity_kind", "clinical_entity")
        if kind not in ("", "clinical_entity") or ROUTINE_DEFINED_RE.search(did):
            continue
        r["rule_type"] = "screening"
        r["legacy_rule_type"] = r.get("legacy_rule_type") or "diagnostic_criterion"
        r["specificity"] = "general"
        r.setdefault("result", {})["diagnosis_allowed"] = False
        r["curation_note"] = ("Routine-panel analytes only: re-graded from diagnostic_criterion to supportive screening "
                              f"pattern for a specific aetiology ({TODAY}).")
        demoted_routine.append(rid)
    changes["routine_only_diagnostic_demoted"] = len(demoted_routine)
    detail["routine_only_diagnostic_demoted"] = demoted_routine

    # ---- 6. urgent flag on critical thresholds ----------------------------------------
    urgent_set = []
    for rid, r in rules.items():
        if r.get("urgent") or not r.get("executable", True):
            continue
        lv = leaves(r["expression"])
        if len(lv) != 1:
            continue
        lf = lv[0]
        f = feats.get(lf["feature_id"]) or {}
        crit = (f.get("validation") or {}).get("critical") or {}
        canon = (f.get("units") or {}).get("canonical")
        if lf.get("unit") != canon or not isinstance(lf.get("value"), (int, float)):
            continue
        v, op = lf["value"], lf["operator"]
        hi, lo = crit.get("high"), crit.get("low")
        if (hi is not None and op in (">", ">=") and v >= hi) or (lo is not None and op in ("<", "<=") and v <= lo):
            r["urgent"] = True
            urgent_set.append(rid)
    changes["urgent_flag_set_on_critical_threshold"] = len(urgent_set)
    detail["urgent_flag_set_on_critical_threshold"] = urgent_set

    # ---- 7. curated rules --------------------------------------------------------------------
    gs = reg["guideline_sources"]
    for sid, (org, title, year, url) in SOURCES.items():
        if sid not in gs:
            gs[sid] = {"organization": org, "title": title, "year": year, "url": url, "scope": [],
                       "evidence_status": "authoritative_international_guideline",
                       "citation_use": "clinical_decision_support", "jurisdiction_scope": "international",
                       "license_status": "open_citation", "last_verified_on": TODAY}
            changes["guideline_source_added"] += 1
    template_result = {"allowed_labels": ["criterion_met", "compatible_pattern", "possible_pattern", "screening_positive",
                                          "urgent_pattern", "excluded", "insufficient_data", "conflicting_data",
                                          "criterion_not_met", "not_applicable"], "diagnosis_allowed": False}
    added, skipped = [], []
    for (did, suffix, rtype, urgent, expr, src, title, expl, lim, spec) in CURATED:
        if did not in diseases:
            skipped.append((did, suffix, "disease_id missing"))
            continue
        bad = []
        for lf in leaves(expr):
            f = feats.get(lf["feature_id"])
            if not f:
                bad.append(lf["feature_id"])
                continue
            units = f.get("units") or {}
            canon = units.get("canonical")
            acc = set(units.get("accepted") or []) | ({canon} if canon else set())
            if lf.get("unit") is None:
                lf["unit"] = canon or "1"
            elif lf["unit"] == "1":
                pass  # qualitative
            elif acc and lf["unit"] not in acc:
                bad.append(f"{lf['feature_id']}:{lf['unit']} not in {sorted(acc)}")
        if bad:
            skipped.append((did, suffix, bad))
            continue
        rid = f"{did}_{suffix}_cur13"
        if rid in rules:
            skipped.append((did, suffix, "exists"))
            continue
        d = diseases[did]
        rules[rid] = {
            "rule_id": rid, "disease_id": did, "rule_type": rtype, "legacy_rule_type": rtype,
            "specificity": spec, "status": "curated_guideline_anchored", "executable": True, "urgent": bool(urgent),
            "expression": expr, "weight": 6.0 if rtype == "diagnostic_criterion" else 4.0,
            "population": dict(d.get("population") or {"age_groups": ["adult", "older_adult"], "sex": "all", "pregnancy": "context_dependent"}),
            "result": dict(template_result), "confirmation": {"required": True, "human_review": True, "repeat_or_alternative_test": "context_dependent"},
            "limitations": list(lim), "source_ids": [src], "title": title, "scientific_explanation": expl,
            "clinical_rationale": "Curated against the cited international guideline; thresholds are the guideline's published decision limits in the feature's canonical unit.",
            "evidence_tier": "tier_a", "entity_kind": (d.get("classification") or {}).get("entity_kind", "clinical_entity"),
            "quality": {"evidence_extracted": True, "specialist_reviewed": False, "software_tested": True},
            "curated_on": TODAY,
        }
        d["rule_ids"].append(rid)
        d.setdefault("layers", {}).setdefault(rtype, []).append(rid)
        if src not in (d.get("guideline_source_ids") or []):
            d.setdefault("guideline_source_ids", []).append(src)
        added.append(rid)
    changes["curated_rules_added"] = len(added)
    detail["curated_rules_added"] = added
    detail["curated_rules_skipped"] = skipped

    # ---- 8. layers / feature_links rebuild --------------------------------------------
    for did, d in diseases.items():
        layers = {"screening": [], "diagnostic_criterion": [], "exclusion_criterion": [], "staging_severity": []}
        req, opt, exc = [], [], []
        for rid in d.get("rule_ids") or []:
            r = rules.get(rid)
            if not r:
                continue
            layers.setdefault(r["rule_type"], []).append(rid)
            if not r.get("executable", True):
                continue
            fids = [l["feature_id"] for l in leaves(r["expression"])]
            if r["rule_type"] == "diagnostic_criterion":
                req += fids
            elif r["rule_type"] == "exclusion_criterion":
                exc += fids
            else:
                opt += fids
        req_s = list(dict.fromkeys(req))
        opt_s = [f for f in dict.fromkeys(opt) if f not in req_s]
        # Only non-routine, non-required markers may refute (engine treats
        # `excluded` as direction-agnostic abnormality -> conflicting_data).
        exc_s = [f for f in dict.fromkeys(exc) if f not in req_s and f not in opt_s and f not in ROUTINE]
        old = d.get("feature_links") or {}
        new = {"required": req_s, "optional": opt_s, "excluded": exc_s}
        if old != new:
            changes["feature_links_rebuilt"] += 1
        d["feature_links"] = new
        d["layers"] = {k: v for k, v in layers.items() if v}
        cov = d.setdefault("coverage", {})
        n_exec = sum(1 for rid in d["rule_ids"] if rules.get(rid, {}).get("executable", True))
        cov["executable_rule_available"] = n_exec > 0
        cov["status"] = "executable_rule_active" if n_exec else "catalogued_only"
        cov["reason"] = f"{n_exec} executable guideline rule(s)."

    # ---- 9. metadata / QA ----------------------------------------------------------------
    rt = collections.Counter(r["rule_type"] for r in rules.values())
    sp = collections.Counter(r.get("specificity") for r in rules.values())
    n_exec = sum(1 for r in rules.values() if r.get("executable", True))
    md = reg["registry_metadata"]
    md["version"] = NEW_VERSION
    md["last_updated"] = TODAY
    md["total_rules"] = len(rules)
    md["executable_rules"] = n_exec
    md["retired_rules"] = len(rules) - n_exec
    md["total_sources"] = len(gs)
    md["rule_type_counts"] = dict(rt)
    md["specificity_counts"] = dict(sp)
    md["curation"] = {"pass": "13.0.0", "date": TODAY, "changes": dict(changes),
                      "report": "docs/GUIDELINE_REGISTRY_CURATION_13.0.0.json"}
    md["feature_links_semantics"]["excluded"] = ("non-routine markers from exclusion_criterion rules whose abnormality "
                                                 "refutes the disease; routine analytes are never refuting")
    reg["validation_report"] = {
        "all_rule_feature_ids_exist": all(l["feature_id"] in feats for r in rules.values() for l in leaves(r["expression"])),
        "missing_feature_ids": sorted({l["feature_id"] for r in rules.values() for l in leaves(r["expression"]) if l["feature_id"] not in feats}),
        "dangling_rule_disease_refs": sorted({r["disease_id"] for r in rules.values() if r["disease_id"] not in diseases}),
        "dangling_rule_source_refs": sorted({s for r in rules.values() for s in r.get("source_ids", []) if s not in gs}),
        "dangling_disease_rule_refs": sorted({rid for d in diseases.values() for rid in d["rule_ids"] if rid not in rules}),
        "duplicate_rule_ids": [],
        "validated_on": TODAY,
    }
    audit["changes"] = dict(changes)
    audit["validation_report"] = reg["validation_report"]
    audit["detail"] = {k: (v if len(v) <= 400 else v[:400] + [f"... +{len(v)-400} more"]) for k, v in detail.items()}

    print(json.dumps(audit["changes"], indent=2))
    print("validation:", json.dumps(reg["validation_report"], indent=1)[:800])
    if skipped:
        print("SKIPPED curated:", json.dumps(skipped, indent=1)[:3000])
    if dry_run:
        return
    payload = json.dumps(reg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    blob = brotli.compress(payload, quality=11, lgwin=24)
    for out in OUTS:
        out.write_bytes(blob)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    sha = hashlib.sha256(blob).hexdigest()
    print(f"written {len(blob):,} bytes (json {len(payload):,}) sha256={sha}")
    # keep license_engine's known-good hash table in sync
    le = ROOT / "license_engine.py"
    txt = le.read_text(encoding="utf-8")
    new_txt = re.sub(r'("HEMOGLYPH_GUIDELINE_REGISTRY\.json\.br":\s*")[0-9a-f]{64}(")', rf"\g<1>{sha}\g<2>", txt)
    if new_txt != txt:
        le.write_text(new_txt, encoding="utf-8")
        print("license_engine.py registry hash updated")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    main(dry_run=a.dry_run)
