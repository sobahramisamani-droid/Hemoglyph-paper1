# -*- coding: utf-8 -*-
"""Registry patch 13.1.0 (2026-10-21): add clinical entities that the analysis
layers (ESL / hard batteries) needed but the shipped registry lacked.

Every entity gets: identity (EN/FA, ICD-10), classification, population,
feature_links, 2–4 executable rules (screening / diagnostic_criterion /
exclusion_criterion / staging_severity) referencing ONLY existing feature ids,
and a guideline source record. Thresholds are cited inline (src=).

Run:  python registry_patch_20261021.py            (dry-run: validates only)
      python registry_patch_20261021.py --apply    (writes both .json.br files,
                                                    keeps .bak copies)
"""
from __future__ import annotations
import sys, json, copy, shutil, hashlib, datetime, re
from pathlib import Path
import brotli

ROOT = Path(__file__).resolve().parent
REG = ROOT / "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
REG2 = ROOT / "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"
FEAT = ROOT / "HEMOGLYPH_FEATURE_REGISTRY.json.br"
TODAY = "2026-10-21"
ALL_AGES = ["neonate", "infant", "child", "adolescent", "adult", "older_adult"]
LABELS = ["criterion_met", "compatible_pattern", "possible_pattern", "screening_positive", "urgent_pattern",
          "excluded", "insufficient_data", "conflicting_data", "criterion_not_met", "not_applicable"]

# ------------------------------------------------------------------ sources
SOURCES = {
 "ats_2014_thyroid_tsh_secreting": ("European Thyroid Association", "2013 ETA Guidelines for the Diagnosis and Treatment of Thyrotropin-Secreting Pituitary Tumors (Beck-Peccoz)", 2013, "https://doi.org/10.1159/000351007", ["endocrine"]),
 "endo_fhh_2022": ("Endocrine Society / Fifth International Workshop", "Evaluation and Management of Asymptomatic Primary Hyperparathyroidism (Bilezikian 2022) — FHH differentiation (CCCR <0.01)", 2022, "https://doi.org/10.1002/jbmr.4677", ["endocrine", "renal"]),
 "clsi_pseudohyponatremia_2020": ("Clinical Chemistry (Tietz / Fortgens 2011)", "Pseudohyponatremia revisited: indirect ISE electrolyte-exclusion effect", 2011, "https://doi.org/10.5858/arpa.2010-0018-RS", ["renal", "laboratory"]),
 "aha_renovascular_2024": ("AHA/ACC", "2024 ACC/AHA Guideline on Peripheral Artery Disease / Renovascular hypertension screening (ARR, hypokalaemia)", 2024, "https://doi.org/10.1161/CIR.0000000000001251", ["cardiovascular", "renal"]),
 "ish_heparin_effect_2021": ("ISTH SSC", "Laboratory assessment of heparin effect: aPTT/TT prolongation with normal reptilase time", 2021, "https://www.isth.org/", ["hematology"]),
 "naspghan_biliary_atresia_2017": ("NASPGHAN/ESPGHAN", "Guideline for the Evaluation of Cholestatic Jaundice in Infants (Fawaz 2017)", 2017, "https://doi.org/10.1097/MPG.0000000000001334", ["gastroenterology", "pediatric"]),
 "aga_ple_2022": ("AGA / Umar & DiBaise", "Protein-losing enteropathy: faecal α1-antitrypsin clearance >27 mL/day (>56 with diarrhoea)", 2010, "https://doi.org/10.1038/ajg.2009.558", ["gastroenterology"]),
 "isa_amyloid_2020": ("International Society of Amyloidosis", "AA amyloidosis: nephrotic proteinuria with chronic inflammation (SAA/CRP) — Lachmann NEJM 2007", 2007, "https://doi.org/10.1056/NEJMoa070265", ["nephrology", "rheumatology"]),
 "acmt_cyanide_2021": ("ACMT / AHA", "Cyanide poisoning: lactate ≥8–10 mmol/L in smoke inhalation predicts toxic cyanide levels (Baud 2002)", 2002, "https://doi.org/10.1097/00003246-200209000-00005", ["toxicology_tdm"]),
 "aha_asa_sah_2023": ("AHA/ASA", "2023 Guideline for the Management of Patients With Aneurysmal Subarachnoid Hemorrhage", 2023, "https://doi.org/10.1161/STR.0000000000000436", ["neurology"]),
 "idsa_encephalitis_2008": ("IDSA", "Management of Encephalitis: Clinical Practice Guidelines (Tunkel 2008)", 2008, "https://doi.org/10.1086/589747", ["infectious_disease", "neurology"]),
 "dmd_care_2018": ("DMD Care Considerations Working Group", "Diagnosis and management of Duchenne muscular dystrophy, part 1 (Birnkrant 2018)", 2018, "https://doi.org/10.1016/S1474-4422(18)30024-3", ["neurology", "pediatric"]),
 "mhaus_2020": ("MHAUS / Larach 2010 clinical grading scale", "Malignant hyperthermia: hypercapnia, hyperkalaemia, CK rise, acidosis", 2010, "https://www.mhaus.org/", ["anesthesia", "toxicology_tdm"]),
 "acmt_isopropanol_2019": ("Goldfrank's Toxicologic Emergencies 11e", "Isopropanol: ketosis without acidosis, elevated osmolal gap", 2019, "https://accessmedicine.mhmedical.com/", ["toxicology_tdm"]),
 "easl_amatoxin_2017": ("EASL / Ye & Liu 2018", "Amatoxin poisoning: delayed hepatocellular injury, coagulopathy", 2018, "https://doi.org/10.1016/j.jhep.2017.11.023", ["toxicology_tdm", "hepatology"]),
 "ats_isoniazid_hepatotoxicity_2006": ("ATS", "Hepatotoxicity of Antituberculosis Therapy (Saukkonen 2006)", 2006, "https://doi.org/10.1164/rccm.200510-1666ST", ["toxicology_tdm", "hepatology"]),
 "who_snakebite_2016": ("WHO SEARO", "Guidelines for the Management of Snakebites, 2nd ed. (20WBCT, VICC)", 2016, "https://www.who.int/publications/i/item/9789290225300", ["toxicology_tdm", "hematology"]),
 "nait_consensus_2019": ("ICTMG / Lieberman 2019", "Fetal and neonatal alloimmune thrombocytopenia: recommendations for evidence-based practice", 2019, "https://doi.org/10.1111/bjh.15813", ["hematology", "pediatric"]),
 "esid_2019": ("ESID", "ESID Registry — Working Definitions for Clinical Diagnosis of Inborn Errors of Immunity (Seidel 2019)", 2019, "https://doi.org/10.1016/j.jaip.2019.02.004", ["immunology"]),
 "pes_precocious_puberty_2009": ("Pediatric Endocrine Society / Carel & Léger NEJM", "Precocious puberty: basal LH ≥0.3 IU/L (ICMA) supports central activation", 2008, "https://doi.org/10.1056/NEJMcp0800459", ["endocrine", "pediatric"]),
 "ata_pregnancy_2017": ("ATA", "2017 Guidelines for the Diagnosis and Management of Thyroid Disease During Pregnancy and the Postpartum (Alexander)", 2017, "https://doi.org/10.1089/thy.2016.0457", ["endocrine", "obstetrics"]),
 "endo_hypopituitarism_2016": ("Endocrine Society", "Hormonal Replacement in Hypopituitarism in Adults (Fleseriu 2016) — Sheehan syndrome", 2016, "https://doi.org/10.1210/jc.2016-2118", ["endocrine", "obstetrics"]),
 "acog_thrombocytopenia_2019": ("ACOG", "Practice Bulletin 207: Thrombocytopenia in Pregnancy", 2019, "https://doi.org/10.1097/AOG.0000000000003100", ["hematology", "obstetrics"]),
 "isth_aps_2006": ("ISTH / Miyakis 2006 (Sydney criteria); ACR/EULAR 2023", "Classification criteria for antiphospholipid syndrome incl. obstetric APS", 2023, "https://doi.org/10.1002/art.42624", ["hematology", "obstetrics", "rheumatology"]),
 "bsh_hyperviscosity_2014": ("BSH / Gertz 2018", "Hyperviscosity syndrome: IgM paraprotein, serum viscosity >4 cP", 2018, "https://doi.org/10.1182/blood-2018-06-846816", ["hematology"]),
 "endo_hypoglycemia_2009": ("Endocrine Society", "Evaluation and Management of Adult Hypoglycemic Disorders (Cryer 2009)", 2009, "https://doi.org/10.1210/jc.2008-1410", ["endocrine", "toxicology_tdm"]),
 "acmt_beta_blocker_2017": ("Goldfrank's / Kerns 2007", "Beta-blocker toxicity: bradycardia, hypoglycaemia, hyperkalaemia", 2007, "https://doi.org/10.1016/j.emc.2007.02.007", ["toxicology_tdm", "cardiovascular"]),
 "endo_adrenal_insufficiency_2016": ("Endocrine Society", "Diagnosis and Treatment of Primary Adrenal Insufficiency (Bornstein 2016) — adrenal crisis", 2016, "https://doi.org/10.1210/jc.2015-1710", ["endocrine", "critical_care"]),
 "wms_hypothermia_2019": ("Wilderness Medical Society", "Clinical Practice Guidelines for the Prevention and Treatment of Accidental Hypothermia (Dow 2019)", 2019, "https://doi.org/10.1016/j.wem.2019.10.002", ["critical_care"]),
 "wms_heat_illness_2019": ("Wilderness Medical Society", "Clinical Practice Guidelines for the Prevention and Treatment of Heat Illness (Lipman 2019)", 2019, "https://doi.org/10.1016/j.wem.2018.10.004", ["critical_care"]),
 "nhsn_taco_2021": ("CDC NHSN Hemovigilance / ISBT 2018", "Transfusion-associated circulatory overload: revised reporting criteria (BNP/NT-proBNP rise)", 2018, "https://doi.org/10.1111/vox.12700", ["hematology", "transfusion"]),
 "aabb_htr_2019": ("AABB Technical Manual 20e", "Acute haemolytic transfusion reaction: haemoglobinuria, LDH rise, haptoglobin fall, DAT positive", 2020, "https://www.aabb.org/", ["hematology", "transfusion"]),
 "acmg_organic_acidemia_2012": ("ACMG / Baumgartner 2014 Orphanet", "Proposed guidelines for the diagnosis and management of methylmalonic and propionic acidemia", 2014, "https://doi.org/10.1186/s13023-014-0130-8", ["metabolic", "pediatric"]),
 "bsh_thrombophilia_2022": ("BSH", "Guideline on thrombophilia testing (Arachchillage 2022)", 2022, "https://doi.org/10.1111/bjh.18239", ["hematology"]),
 "ecco_2019_ibd": ("ECCO", "ECCO Guidelines on Therapeutics / Diagnosis in Crohn's disease and ulcerative colitis", 2019, "https://doi.org/10.1093/ecco-jcc/jjy113", ["gastroenterology"]),
 "ats_pleural_tb_2017": ("ATS/IDSA/CDC; Aggarwal 2019 meta-analysis", "Pleural fluid ADA ≥40 U/L for tuberculous pleural effusion", 2019, "https://doi.org/10.1371/journal.pone.0213728", ["infectious_disease", "pulmonology"]),
 "vpa_hyperammonemia_2020": ("Baddour 2018 Epilepsia Open / Segura-Bruna 2006", "Valproate-induced hyperammonaemic encephalopathy: ammonia >80 µmol/L with normal transaminases", 2018, "https://doi.org/10.1002/epi4.12188", ["toxicology_tdm", "neurology"]),
 "aap_reye_2017": ("CDC case definition / AAP", "Reye syndrome: microvesicular steatosis, hyperammonaemia, transaminase ≥3× ULN, bilirubin ≤3 mg/dL", 2017, "https://www.cdc.gov/", ["pediatric", "hepatology"]),
 "cdc_tss_2011": ("CDC", "Toxic Shock Syndrome (Other Than Streptococcal) 2011 Case Definition", 2011, "https://ndc.services.cdc.gov/case-definitions/toxic-shock-syndrome-2011/", ["infectious_disease", "critical_care"]),
 "pes_ketotic_hypoglycemia_2015": ("Pediatric Endocrine Society (Thornton 2015)", "Recommendations for evaluation and management of persistent hypoglycemia in neonates, infants and children", 2015, "https://doi.org/10.1016/j.jpeds.2015.03.057", ["pediatric", "endocrine"]),
 "acg_pancreatitis_2024": ("ACG", "ACG Clinical Guideline: Management of Acute Pancreatitis (Tenner 2024)", 2024, "https://doi.org/10.14309/ajg.0000000000002645", ["gastroenterology"]),
 "bts_pleural_2023": ("BTS", "BTS Guideline for Pleural Disease (Roberts 2023) — Light criteria, malignant effusion", 2023, "https://doi.org/10.1136/thorax-2022-219784", ["pulmonology"]),
 "bsh_pancytopenia_2016": ("BSH / Camitta criteria", "Guidelines for the diagnosis and management of adult aplastic anaemia (Killick 2016) — pancytopenia work-up", 2016, "https://doi.org/10.1111/bjh.13853", ["hematology"]),
 "aasld_acute_hepatitis_2023": ("AASLD / EASL", "Acute hepatitis and acute liver failure work-up: ALT ≥5× ULN with/without INR ≥1.5 (Wendon 2017)", 2017, "https://doi.org/10.1016/j.jhep.2016.12.003", ["hepatology"]),
 "esc_hf_2021_pericarditis": ("ESC", "2015 ESC Guidelines for the diagnosis and management of pericardial diseases (Adler)", 2015, "https://doi.org/10.1093/eurheartj/ehv318", ["cardiovascular"]),
 "aha_hypothyroid_myopathy_2019": ("Endocrine Reviews / Sindoni 2016", "Hypothyroid myopathy: CK elevation reversible with levothyroxine", 2016, "https://doi.org/10.1007/s11154-016-9357-0", ["endocrine", "neurology"]),
}

def _src(org, title, year, url, scope):
    return {"organization": org, "title": title, "year": year, "url": url, "scope": scope, "accessed_at": TODAY,
            "evidence_status": "source_record_added_patch_13_1_0__content_and_currentness_require_verification",
            "citation_use": "provenance pointer only; not authorization to reproduce proprietary guideline content",
            "jurisdiction_scope": "international_or_organization_specific__local_adaptation_required",
            "license_status": "not_assessed", "last_verified_on": None}

# ------------------------------------------------------------------ helpers
def C(fid, op, val, unit, w=2.0):
    return {"feature_id": fid, "operator": op, "value": val, "unit": unit, "weight": w}

def ALL(*c): return {"all": list(c)}
def ANY(*c): return {"any": list(c)}

# Each entity: id, en, fa, icd10, domains, priority, ages, pregnancy, rules[(suffix, type, urgent, expr, weight, rationale)], sources
# Rules are expressed only over feature ids verified to exist in the feature registry (checked at run time).
E = []
def D(did, en, fa, icd, domains, priority, rules, sources, ages=None, sex="all", pregnancy="context_dependent", subtype_of=None):
    E.append(dict(id=did, en=en, fa=fa, icd=icd, domains=domains, priority=priority, rules=rules, sources=sources,
                  ages=ages or ALL_AGES, sex=sex, pregnancy=pregnancy, subtype_of=subtype_of))

TSH = "thyroid_stimulating_hormone"; FT4 = "free_thyroxine"

D("tsh_secreting_adenoma_or_rth", "Inappropriate TSH secretion (TSH-oma / resistance to thyroid hormone)", "ترشح نامتناسب TSH (آدنوم ترشح‌کنندهٔ TSH / مقاومت به هورمون تیروئید)", ["E05.8", "E07.89"], ["endocrine"], "routine", [
    ("screen", "screening", False, ALL(C(FT4, ">", 1.8, "ng/dL"), C(TSH, ">=", 0.4, "mIU/L")), 4.0, "Non-suppressed TSH with high free T4 = inappropriate TSH secretion; exclude assay interference (ETA 2013)."),
    ("dx", "diagnostic_criterion", False, ALL(C(FT4, ">", 1.8, "ng/dL"), C(TSH, ">", 1.0, "mIU/L")), 7.0, "Frankly elevated/normal TSH with hyperthyroxinaemia after interference excluded (ETA 2013)."),
    ("excl", "exclusion_criterion", False, C(TSH, "<", 0.1, "mIU/L"), 6.0, "Suppressed TSH indicates primary hyperthyroidism, not TSH-oma/RTH."),
], ["ats_2014_thyroid_tsh_secreting"])

D("hypothyroid_myopathy", "Hypothyroid myopathy", "میوپاتی هیپوتیروئیدی", ["E03.9", "G73.7"], ["endocrine", "neurology"], "routine", [
    ("screen", "screening", False, ALL(C(TSH, ">", 10, "mIU/L"), C("creatine_kinase_total", ">", 300, "U/L")), 4.0, "Overt hypothyroidism with CK elevation (Sindoni 2016)."),
    ("dx", "diagnostic_criterion", False, ALL(C(TSH, ">", 10, "mIU/L"), C(FT4, "<", 0.8, "ng/dL"), C("creatine_kinase_total", ">", 500, "U/L")), 7.0, "Overt hypothyroidism + CK >2.5× ULN; CK normalises with replacement."),
    ("excl", "exclusion_criterion", False, C("creatine_kinase_total", ">", 10000, "U/L"), 5.0, "CK >10 000 U/L points to rhabdomyolysis rather than hypothyroid myopathy."),
], ["aha_hypothyroid_myopathy_2019"])

D("familial_hypocalciuric_hypercalcemia", "Familial hypocalciuric hypercalcaemia", "هیپرکلسمی هیپوکلسیوریک خانوادگی", ["E83.52"], ["endocrine", "renal"], "routine", [
    ("screen", "screening", False, ALL(C("calcium_total", ">", 10.3, "mg/dL"), C("parathyroid_hormone", ">=", 15, "pg/mL")), 3.0, "PTH-dependent hypercalcaemia — differentiate from PHPT by urinary calcium (Bilezikian 2022)."),
    ("dx", "diagnostic_criterion", False, ALL(C("calcium_total", ">", 10.3, "mg/dL"), C("parathyroid_hormone", ">=", 15, "pg/mL"), C("urine_calcium_to_creatinine_clearance_ratio", "<", 0.01, "1")), 8.0, "CCCR <0.01 with mild hypercalcaemia and non-suppressed PTH (Fifth Workshop 2022)."),
    ("excl", "exclusion_criterion", False, C("urine_calcium_to_creatinine_clearance_ratio", ">", 0.02, "1"), 6.0, "CCCR >0.02 favours primary hyperparathyroidism."),
], ["endo_fhh_2022"])

D("pseudohyponatremia", "Pseudohyponatraemia (indirect ISE artefact)", "هیپوناترمی کاذب (آرتیفکت ISE غیرمستقیم)", ["E87.1"], ["renal", "laboratory_medicine"], "routine", [
    ("screen", "screening", False, ALL(C("sodium", "<", 135, "mmol/L"), ANY(C("triglycerides", ">", 1000, "mg/dL"), C("total_protein", ">", 10, "g/dL"))), 4.0, "Low measured Na with severe hypertriglyceridaemia or paraproteinaemia (Fortgens 2011)."),
    ("dx", "diagnostic_criterion", False, ALL(C("sodium", "<", 135, "mmol/L"), ANY(C("triglycerides", ">", 1500, "mg/dL"), C("total_protein", ">", 10, "g/dL")), C("serum_osmolality", ">=", 275, "mOsm/kg")), 8.0, "Iso-osmolar hyponatraemia with lipid/protein excess; confirm with direct ISE."),
    ("excl", "exclusion_criterion", False, C("serum_osmolality", "<", 270, "mOsm/kg"), 6.0, "Hypo-osmolar hyponatraemia is true hyponatraemia."),
], ["clsi_pseudohyponatremia_2020"])

D("renovascular_hypertension", "Renovascular hypertension (renal artery stenosis)", "هیپرتانسیون رنوواسکولار (تنگی شریان کلیه)", ["I15.0", "I70.1"], ["cardiovascular", "renal"], "routine", [
    ("screen", "screening", False, ALL(C("plasma_renin_activity", ">", 3.0, "ng/mL/h"), C("aldosterone", ">", 15, "ng/dL")), 3.0, "Secondary hyperaldosteronism: high renin + high aldosterone (ACC/AHA 2024)."),
    ("dx", "diagnostic_criterion", False, ALL(C("plasma_renin_activity", ">", 3.0, "ng/mL/h"), C("aldosterone", ">", 15, "ng/dL"), C("potassium", "<", 3.5, "mmol/L")), 6.0, "Renin-driven hyperaldosteronism with hypokalaemia; imaging required for confirmation."),
    ("excl", "exclusion_criterion", False, C("plasma_renin_activity", "<", 0.5, "ng/mL/h"), 6.0, "Suppressed renin excludes renovascular origin (favours primary aldosteronism)."),
], ["aha_renovascular_2024"])

D("heparin_effect_coagulation", "Heparin effect on coagulation tests", "اثر هپارین بر تست‌های انعقادی", ["Z79.01", "D68.32"], ["hematology", "toxicology_tdm"], "routine", [
    ("screen", "screening", False, ALL(C("activated_partial_thromboplastin_time", ">", 45, "s"), C("thrombin_time", ">", 25, "s")), 4.0, "Prolonged aPTT and TT (ISTH)."),
    ("dx", "diagnostic_criterion", False, ALL(C("activated_partial_thromboplastin_time", ">", 45, "s"), C("thrombin_time", ">", 25, "s"), C("reptilase_time", "<=", 22, "s")), 8.0, "Prolonged TT with normal reptilase time is pathognomonic for heparin contamination/effect."),
    ("alt", "diagnostic_criterion", False, ALL(C("anti_xa_activity_unfractionated_heparin", ">", 0.1, "IU/mL"), C("activated_partial_thromboplastin_time", ">", 45, "s")), 8.0, "Measurable anti-Xa with prolonged aPTT."),
    ("excl", "exclusion_criterion", False, C("reptilase_time", ">", 25, "s"), 6.0, "Prolonged reptilase time indicates fibrinogen abnormality/FDPs, not heparin."),
], ["ish_heparin_effect_2021"])

D("biliary_atresia", "Biliary atresia", "آترزی صفراوی", ["Q44.2"], ["gastroenterology", "pediatric", "hepatology"], "urgent", [
    ("screen", "screening", True, ALL(C("direct_bilirubin", ">", 1.0, "mg/dL"), C("gamma_glutamyl_transferase", ">", 200, "U/L")), 5.0, "Conjugated hyperbilirubinaemia >1 mg/dL in an infant is always pathological; high GGT favours obstruction (NASPGHAN 2017)."),
    ("dx", "diagnostic_criterion", True, ALL(C("direct_bilirubin", ">", 2.0, "mg/dL"), C("gamma_glutamyl_transferase", ">", 300, "U/L"), C("alkaline_phosphatase", ">", 400, "U/L")), 7.0, "Obstructive cholestasis pattern in infancy; confirmation by imaging/cholangiography (NASPGHAN 2017)."),
    ("excl", "exclusion_criterion", False, C("gamma_glutamyl_transferase", "<", 100, "U/L"), 6.0, "Low-GGT cholestasis points to PFIC/bile-acid synthesis defects, not biliary atresia."),
], ["naspghan_biliary_atresia_2017"], ages=["neonate", "infant"])

D("protein_losing_enteropathy", "Protein-losing enteropathy", "انتروپاتی با اتلاف پروتئین", ["K90.4"], ["gastroenterology"], "routine", [
    ("screen", "screening", False, ALL(C("albumin", "<", 3.0, "g/dL"), C("total_immunoglobulin_g", "<", 600, "mg/dL")), 4.0, "Hypoalbuminaemia with panhypoproteinaemia (low IgG) suggests enteric loss."),
    ("dx", "diagnostic_criterion", False, ALL(C("albumin", "<", 3.0, "g/dL"), C("fecal_alpha1_antitrypsin_clearance", ">", 27, "mL/d")), 8.0, "Faecal α1-antitrypsin clearance >27 mL/day (Umar & DiBaise 2010)."),
    ("excl", "exclusion_criterion", False, C("urine_protein_to_creatinine_ratio", ">", 3.5, "g/g"), 6.0, "Nephrotic-range proteinuria explains hypoalbuminaemia renally."),
], ["aga_ple_2022"])

D("aa_amyloidosis", "AA (secondary) amyloidosis", "آمیلوئیدوز AA (ثانویه)", ["E85.3"], ["nephrology", "rheumatology"], "routine", [
    ("screen", "screening", False, ALL(C("urine_protein_to_creatinine_ratio", ">", 1.0, "g/g"), C("c_reactive_protein", ">", 20, "mg/L")), 3.0, "Proteinuria in the setting of chronic inflammation (Lachmann 2007)."),
    ("dx", "diagnostic_criterion", False, ALL(C("urine_protein_to_creatinine_ratio", ">", 3.0, "g/g"), C("serum_amyloid_a", ">", 10, "mg/L"), C("albumin", "<", 3.5, "g/dL")), 7.0, "Nephrotic proteinuria with persistently raised SAA; tissue confirmation required."),
    ("excl", "exclusion_criterion", False, C("serum_free_kappa_to_lambda_ratio_flc", ">", 8, "1"), 5.0, "Markedly abnormal FLC ratio favours AL amyloidosis."),
], ["isa_amyloid_2020"])

D("cyanide_poisoning", "Cyanide poisoning", "مسمومیت با سیانید", ["T65.0X"], ["toxicology_tdm", "critical_care"], "critical", [
    ("screen", "screening", True, ALL(C("lactate", ">=", 8, "mmol/L"), C("bicarbonate", "<", 18, "mmol/L")), 5.0, "Lactate ≥8 mmol/L in smoke inhalation/suspected exposure predicts toxic cyanide levels (Baud 2002)."),
    ("dx", "diagnostic_criterion", True, C("cyanide_blood", ">", 0.5, "mg/L"), 9.0, "Blood cyanide >0.5 mg/L toxic; >3 mg/L potentially lethal."),
    ("dx2", "diagnostic_criterion", True, ALL(C("lactate", ">=", 10, "mmol/L"), C("anion_gap", ">", 16, "mmol/L"), C("carboxyhemoglobin_fraction", ">", 10, "%")), 7.0, "Severe lactic acidosis with concurrent CO exposure (fire victims) — treat empirically."),
    ("excl", "exclusion_criterion", False, C("lactate", "<", 4, "mmol/L"), 6.0, "Lactate <4 mmol/L makes significant cyanide toxicity unlikely."),
], ["acmt_cyanide_2021"])

D("subarachnoid_hemorrhage", "Subarachnoid haemorrhage", "خونریزی ساب‌آراکنوئید", ["I60.9"], ["neurology", "critical_care"], "critical", [
    ("screen", "screening", True, C("csf_xanthochromia", "==", 1, "1"), 6.0, "CSF xanthochromia ≥12 h after ictus supports SAH when CT is negative (AHA/ASA 2023)."),
    ("dx", "diagnostic_criterion", True, ALL(C("csf_xanthochromia", "==", 1, "1"), C("sodium", "<", 135, "mmol/L")), 7.0, "Xanthochromia with hyponatraemia (cerebral salt wasting/SIADH) in the appropriate clinical setting."),
    ("stage", "staging_severity", True, ALL(C("csf_xanthochromia", "==", 1, "1"), C("high_sensitivity_troponin_i", ">", 50, "ng/L")), 5.0, "Neurogenic myocardial injury accompanies severe SAH."),
], ["aha_asa_sah_2023"])

D("hsv_encephalitis", "Herpes simplex encephalitis", "انسفالیت هرپس سیمپلکس", ["B00.4"], ["infectious_disease", "neurology"], "critical", [
    ("screen", "screening", True, ALL(C("cerebrospinal_fluid_total_protein", ">", 45, "mg/dL"), C("cerebrospinal_fluid_glucose", ">=", 40, "mg/dL")), 4.0, "Lymphocytic-type CSF with raised protein and normal glucose (IDSA 2008)."),
    ("dx", "diagnostic_criterion", True, ALL(C("cerebrospinal_fluid_total_protein", ">", 45, "mg/dL"), C("sodium", "<", 135, "mmol/L"), C("cerebrospinal_fluid_glucose", ">=", 40, "mg/dL")), 6.0, "CSF profile plus hyponatraemia; HSV PCR is confirmatory."),
    ("excl", "exclusion_criterion", False, C("cerebrospinal_fluid_glucose", "<", 30, "mg/dL"), 6.0, "Marked CSF hypoglycorrhachia favours bacterial/TB/fungal meningitis."),
], ["idsa_encephalitis_2008"])

D("duchenne_muscular_dystrophy", "Duchenne muscular dystrophy", "دیستروفی عضلانی دوشن", ["G71.01"], ["neurology", "pediatric"], "routine", [
    ("screen", "screening", False, ALL(C("creatine_kinase_total", ">", 2000, "U/L"), C("aspartate_aminotransferase", ">", 60, "U/L")), 4.0, "CK >10× ULN in a young boy with 'transaminitis' of muscle origin (Birnkrant 2018)."),
    ("dx", "diagnostic_criterion", False, ALL(C("creatine_kinase_total", ">", 5000, "U/L"), C("aspartate_aminotransferase", ">", 60, "U/L"), C("gamma_glutamyl_transferase", "<", 60, "U/L")), 7.0, "Very high CK with AST/ALT rise and normal GGT = muscle, not liver; genetic confirmation required."),
    ("excl", "exclusion_criterion", False, C("creatine_kinase_total", "<", 500, "U/L"), 6.0, "Near-normal CK excludes Duchenne in a symptomatic young child."),
], ["dmd_care_2018"], ages=["infant", "child", "adolescent"], sex="male")

D("malignant_hyperthermia", "Malignant hyperthermia", "هیپرترمی بدخیم", ["T88.3"], ["anesthesia", "critical_care", "toxicology_tdm"], "critical", [
    ("screen", "screening", True, ALL(C("arterial_pco2", ">", 55, "mm[Hg]"), C("potassium", ">", 5.5, "mmol/L")), 6.0, "Unexplained hypercapnia with hyperkalaemia under anaesthesia (Larach 2010)."),
    ("dx", "diagnostic_criterion", True, ALL(C("arterial_pco2", ">", 55, "mm[Hg]"), C("arterial_ph", "<", 7.25, "pH"), C("creatine_kinase_total", ">", 1000, "U/L"), C("potassium", ">", 5.5, "mmol/L")), 9.0, "Mixed acidosis, hyperkalaemia, rhabdomyolysis — Larach clinical grading ≥ rank 5."),
    ("stage", "staging_severity", True, C("creatine_kinase_total", ">", 20000, "U/L"), 5.0, "CK >20 000 U/L: severe rhabdomyolysis; renal protection required."),
], ["mhaus_2020"])

D("isopropanol_poisoning", "Isopropanol poisoning", "مسمومیت با ایزوپروپانول", ["T51.2X"], ["toxicology_tdm"], "urgent", [
    ("screen", "screening", True, ALL(C("osmolal_gap", ">", 10, "mOsm/kg"), C("bicarbonate", ">=", 20, "mmol/L")), 4.0, "Elevated osmolal gap WITHOUT metabolic acidosis (Goldfrank's)."),
    ("dx", "diagnostic_criterion", True, ANY(C("isopropanol", ">", 10, "mg/dL"), ALL(C("osmolal_gap", ">", 10, "mOsm/kg"), C("acetone_serum", ">", 5, "mg/dL"), C("bicarbonate", ">=", 20, "mmol/L"))), 8.0, "Measured isopropanol, or osmolal gap + ketonaemia (acetone) with preserved bicarbonate."),
    ("excl", "exclusion_criterion", False, ALL(C("bicarbonate", "<", 15, "mmol/L"), C("anion_gap", ">", 16, "mmol/L")), 6.0, "High-AG acidosis points to methanol/ethylene glycol instead."),
], ["acmt_isopropanol_2019"])

D("amatoxin_poisoning", "Amatoxin (Amanita) mushroom poisoning", "مسمومیت با آماتوکسین (قارچ آمانیتا)", ["T62.0X"], ["toxicology_tdm", "hepatology"], "critical", [
    ("screen", "screening", True, ALL(C("alanine_aminotransferase", ">", 1000, "U/L"), C("international_normalized_ratio", ">", 1.5, "1")), 5.0, "Delayed (24–48 h) hepatocellular injury with coagulopathy after mushroom ingestion (Ye & Liu 2018)."),
    ("dx", "diagnostic_criterion", True, ALL(C("alanine_aminotransferase", ">", 2000, "U/L"), C("international_normalized_ratio", ">", 2.0, "1"), C("acetaminophen", "<", 10, "ug/mL")), 8.0, "Massive transaminase rise and INR >2 with paracetamol excluded; history of foraged mushrooms."),
    ("stage", "staging_severity", True, ALL(C("international_normalized_ratio", ">", 4, "1"), C("creatinine", ">", 1.5, "mg/dL")), 6.0, "INR >4 and renal failure predict need for transplant (Escudié criteria)."),
], ["easl_amatoxin_2017"])

D("isoniazid_hepatotoxicity", "Isoniazid hepatotoxicity", "هپاتوتوکسیسیتی ایزونیازید", ["T37.1X", "K71.6"], ["toxicology_tdm", "hepatology"], "urgent", [
    ("screen", "screening", False, C("alanine_aminotransferase", ">", 120, "U/L"), 3.0, "ALT >3× ULN on anti-TB therapy with symptoms (ATS 2006)."),
    ("dx", "diagnostic_criterion", True, ANY(C("alanine_aminotransferase", ">", 200, "U/L"), ALL(C("alanine_aminotransferase", ">", 120, "U/L"), C("total_bilirubin", ">", 2.0, "mg/dL"))), 7.0, "ALT >5× ULN, or >3× ULN with jaundice: stop hepatotoxic drugs (ATS 2006; Hy's law)."),
    ("excl", "exclusion_criterion", False, C("hepatitis_a_igm_antibody", "==", 1, "1"), 5.0, "Acute viral hepatitis A explains the injury."),
], ["ats_isoniazid_hepatotoxicity_2006"])

D("snake_envenomation_coagulopathy", "Snake envenomation with venom-induced consumption coagulopathy", "مارگزیدگی با کوآگولوپاتی مصرفی ناشی از زهر", ["T63.0X"], ["toxicology_tdm", "hematology"], "critical", [
    ("screen", "screening", True, ALL(C("international_normalized_ratio", ">", 1.5, "1"), C("fibrinogen", "<", 150, "mg/dL")), 5.0, "Coagulopathy with hypofibrinogenaemia after snakebite = VICC (WHO 2016)."),
    ("dx", "diagnostic_criterion", True, ALL(C("international_normalized_ratio", ">", 1.5, "1"), C("fibrinogen", "<", 100, "mg/dL"), C("d_dimer", ">", 2.0, "ug/mL")), 8.0, "Incoagulable blood/INR >1.5, fibrinogen <1 g/L and very high D-dimer — antivenom indicated."),
    ("stage", "staging_severity", True, ANY(C("creatinine", ">", 1.5, "mg/dL"), C("creatine_kinase_total", ">", 5000, "U/L"), C("platelets", "<", 50, "10^9/L")), 5.0, "AKI, myotoxicity or thrombocytopenia mark severe envenomation."),
], ["who_snakebite_2016"])

D("neonatal_alloimmune_thrombocytopenia", "Fetal/neonatal alloimmune thrombocytopenia", "ترومبوسیتوپنی آلوایمیون نوزادی", ["P61.0"], ["hematology", "pediatric"], "urgent", [
    ("screen", "screening", True, C("platelets", "<", 50, "10^9/L"), 4.0, "Severe isolated thrombocytopenia in a well term neonate (Lieberman 2019)."),
    ("dx", "diagnostic_criterion", True, ALL(C("platelets", "<", 50, "10^9/L"), C("hemoglobin", ">=", 13, "g/dL"), C("c_reactive_protein", "<", 10, "mg/L"), C("white_blood_cell_count", ">=", 5, "10^9/L")), 7.0, "Isolated severe thrombocytopenia without anaemia, infection or leukopenia; HPA antibody confirms."),
    ("excl", "exclusion_criterion", False, ANY(C("procalcitonin", ">", 2, "ng/mL"), C("blood_culture", "==", 1, "1")), 6.0, "Sepsis-associated thrombocytopenia."),
], ["nait_consensus_2019"], ages=["neonate"])

D("digeorge_syndrome", "DiGeorge (22q11.2 deletion) syndrome", "سندرم دی‌جورج (حذف 22q11.2)", ["D82.1"], ["immunology", "pediatric", "endocrine"], "routine", [
    ("screen", "screening", False, ALL(C("calcium_total", "<", 8.0, "mg/dL"), C("parathyroid_hormone", "<", 20, "pg/mL")), 4.0, "Neonatal/infantile hypoparathyroid hypocalcaemia (ESID 2019)."),
    ("dx", "diagnostic_criterion", False, ALL(C("calcium_total", "<", 8.0, "mg/dL"), C("parathyroid_hormone", "<", 20, "pg/mL"), C("cd3_t_cells_absolute", "<", 1500, "cells/uL")), 8.0, "Hypoparathyroidism with T-cell lymphopenia — FISH/array confirms 22q11.2 deletion."),
    ("excl", "exclusion_criterion", False, C("parathyroid_hormone", ">", 65, "pg/mL"), 6.0, "High PTH indicates non-parathyroid hypocalcaemia."),
], ["esid_2019"], ages=["neonate", "infant", "child"])

D("hyper_ige_syndrome", "Hyper-IgE syndrome", "سندرم هایپر-IgE", ["D82.4"], ["immunology", "pediatric"], "routine", [
    ("screen", "screening", False, C("total_immunoglobulin_e", ">", 2000, "IU/mL"), 4.0, "IgE >2000 IU/mL (ESID 2019 working definition)."),
    ("dx", "diagnostic_criterion", False, ALL(C("total_immunoglobulin_e", ">", 2000, "IU/mL"), C("eosinophil_count_absolute", ">", 0.7, "10^9/L")), 7.0, "Very high IgE with eosinophilia in recurrent staphylococcal abscess/pneumonia phenotype; STAT3/DOCK8 confirms."),
    ("excl", "exclusion_criterion", False, C("total_immunoglobulin_e", "<", 500, "IU/mL"), 6.0, "IgE <500 IU/mL argues against hyper-IgE syndrome."),
], ["esid_2019"], ages=["infant", "child", "adolescent", "adult"])

D("central_precocious_puberty", "Central precocious puberty", "بلوغ زودرس مرکزی", ["E30.1"], ["endocrine", "pediatric"], "routine", [
    ("screen", "screening", False, C("luteinizing_hormone", ">=", 0.3, "IU/L"), 3.0, "Basal LH ≥0.3 IU/L (ICMA) in a child <8 y (girls) / <9 y (boys) (Carel & Léger 2008)."),
    ("dx", "diagnostic_criterion", False, ALL(C("luteinizing_hormone", ">=", 0.3, "IU/L"), ANY(C("estradiol", ">", 20, "pg/mL"), C("total_testosterone", ">", 30, "ng/dL"))), 7.0, "Pubertal LH with sex-steroid rise; GnRH-stimulated LH ≥5 IU/L confirms."),
    ("excl", "exclusion_criterion", False, ALL(C("luteinizing_hormone", "<", 0.1, "IU/L"), C("follicle_stimulating_hormone", "<", 1.0, "IU/L")), 6.0, "Prepubertal gonadotrophins favour peripheral precocity or premature thelarche/adrenarche."),
], ["pes_precocious_puberty_2009"], ages=["child"])

D("gestational_transient_thyrotoxicosis", "Gestational transient thyrotoxicosis (hCG-mediated)", "تیروتوکسیکوز گذرای بارداری (وابسته به hCG)", ["O99.28", "E05.8"], ["endocrine", "obstetrics"], "routine", [
    ("screen", "screening", False, ALL(C(TSH, "<", 0.1, "mIU/L"), C("tsh_receptor_antibody", "<", 1.75, "IU/L")), 4.0, "Suppressed TSH in first trimester with negative TRAb (ATA 2017)."),
    ("dx", "diagnostic_criterion", False, ALL(C(TSH, "<", 0.1, "mIU/L"), C(FT4, ">", 1.8, "ng/dL"), C("tsh_receptor_antibody", "<", 1.75, "IU/L"), C("thyroid_peroxidase_antibody", "<", 35, "IU/mL")), 7.0, "Biochemical hyperthyroidism with negative TRAb/TPO, typically with hyperemesis; resolves by 14–18 wk."),
    ("excl", "exclusion_criterion", False, C("tsh_receptor_antibody", ">=", 1.75, "IU/L"), 7.0, "Positive TRAb = Graves disease."),
], ["ata_pregnancy_2017"], ages=["adolescent", "adult"], sex="female", pregnancy="required")

D("sheehan_syndrome", "Sheehan syndrome (postpartum pituitary necrosis)", "سندرم شیهان (نکروز هیپوفیز پس از زایمان)", ["E23.0"], ["endocrine", "obstetrics"], "urgent", [
    ("screen", "screening", False, ALL(C("prolactin", "<", 5, "ng/mL"), C(FT4, "<", 0.8, "ng/dL")), 4.0, "Low prolactin (failure to lactate) with central hypothyroidism postpartum (Fleseriu 2016)."),
    ("dx", "diagnostic_criterion", True, ALL(C(FT4, "<", 0.8, "ng/dL"), C(TSH, "<", 5, "mIU/L"), C("cortisol_morning", "<", 5, "ug/dL"), C("prolactin", "<", 5, "ng/mL")), 8.0, "Central hypothyroidism + secondary adrenal insufficiency + hypoprolactinaemia after obstetric haemorrhage."),
    ("excl", "exclusion_criterion", False, C(TSH, ">", 10, "mIU/L"), 6.0, "High TSH = primary hypothyroidism."),
], ["endo_hypopituitarism_2016"], ages=["adolescent", "adult"], sex="female")

D("gestational_thrombocytopenia", "Gestational thrombocytopenia", "ترومبوسیتوپنی بارداری", ["O99.11"], ["hematology", "obstetrics"], "routine", [
    ("screen", "screening", False, C("platelets", "<", 150, "10^9/L"), 2.0, "Mild thrombocytopenia in late pregnancy (ACOG PB 207)."),
    ("dx", "diagnostic_criterion", False, ALL(C("platelets", "<", 150, "10^9/L"), C("platelets", ">=", 75, "10^9/L"), C("alanine_aminotransferase", "<", 40, "U/L"), C("lactate_dehydrogenase", "<", 250, "U/L"), C("urine_protein_to_creatinine_ratio", "<", 0.3, "g/g")), 6.0, "Platelets 75–150 ×10⁹/L, no haemolysis, normal transaminases and no proteinuria (ACOG 2019)."),
    ("excl", "exclusion_criterion", False, ANY(C("platelets", "<", 70, "10^9/L"), C("lactate_dehydrogenase", ">", 600, "U/L"), C("alanine_aminotransferase", ">", 70, "U/L")), 7.0, "Platelets <70, haemolysis or transaminitis → consider ITP, HELLP, TTP."),
], ["acog_thrombocytopenia_2019"], ages=["adolescent", "adult"], sex="female", pregnancy="required")

D("obstetric_antiphospholipid_syndrome", "Obstetric antiphospholipid syndrome", "سندرم آنتی‌فسفولیپید مامایی", ["D68.61", "O26.89"], ["hematology", "obstetrics", "rheumatology"], "routine", [
    ("screen", "screening", False, ANY(C("lupus_anticoagulant_screen", "==", 1, "1"), C("cardiolipin_igg_antibody", ">", 40, "GPL"), C("beta_2_glycoprotein_i_igg_antibody", ">", 40, "U/mL")), 4.0, "Persistent aPL positivity (Sydney/ACR-EULAR 2023)."),
    ("dx", "diagnostic_criterion", False, ALL(ANY(C("lupus_anticoagulant_screen", "==", 1, "1"), C("cardiolipin_igg_antibody", ">", 40, "GPL"), C("beta_2_glycoprotein_i_igg_antibody", ">", 40, "U/mL")), C("activated_partial_thromboplastin_time", ">", 38, "s")), 6.0, "Laboratory aPL criterion with LA-type aPTT prolongation; obstetric morbidity criterion supplied clinically."),
    ("excl", "exclusion_criterion", False, ALL(C("lupus_anticoagulant_screen", "==", 0, "1"), C("cardiolipin_igg_antibody", "<", 20, "GPL"), C("beta_2_glycoprotein_i_igg_antibody", "<", 20, "U/mL")), 7.0, "Triple-negative aPL excludes APS."),
], ["isth_aps_2006"], ages=["adolescent", "adult"], sex="female")

D("hyperviscosity_syndrome", "Hyperviscosity syndrome", "سندرم هیپرویسکوزیته", ["D89.1", "C88.0"], ["hematology"], "urgent", [
    ("screen", "screening", True, ANY(C("total_immunoglobulin_m", ">", 3000, "mg/dL"), C("total_protein", ">", 10, "g/dL")), 4.0, "IgM >30 g/L or total protein >100 g/L (Gertz 2018)."),
    ("dx", "diagnostic_criterion", True, ANY(C("plasma_viscosity", ">", 4, "cP"), ALL(C("total_immunoglobulin_m", ">", 4000, "mg/dL"), C("hemoglobin", "<", 11, "g/dL"))), 8.0, "Serum viscosity >4 cP, or IgM >40 g/L with symptoms — urgent plasmapheresis."),
    ("stage", "staging_severity", True, C("plasma_viscosity", ">", 6, "cP"), 5.0, "Viscosity >6 cP: retinal/CNS complications likely."),
], ["bsh_hyperviscosity_2014"])

D("sulfonylurea_induced_hypoglycemia", "Sulfonylurea-induced hypoglycaemia", "هیپوگلیسمی ناشی از سولفونیل‌اوره", ["T38.3X", "E16.0"], ["endocrine", "toxicology_tdm"], "urgent", [
    ("screen", "screening", True, ALL(C("glucose", "<", 55, "mg/dL"), C("insulin", ">=", 3, "uIU/mL")), 4.0, "Hyperinsulinaemic hypoglycaemia (Cryer 2009)."),
    ("dx", "diagnostic_criterion", True, ALL(C("glucose", "<", 55, "mg/dL"), C("insulin", ">=", 3, "uIU/mL"), C("c_peptide", ">=", 0.6, "ng/mL"), C("beta_hydroxybutyrate", "<", 2.7, "mmol/L")), 7.0, "Endogenous hyperinsulinism pattern (C-peptide ≥0.6 ng/mL, suppressed ketones) — sulfonylurea screen distinguishes from insulinoma."),
    ("excl", "exclusion_criterion", False, C("c_peptide", "<", 0.2, "ng/mL"), 7.0, "Suppressed C-peptide with high insulin = exogenous insulin."),
], ["endo_hypoglycemia_2009"])

D("beta_blocker_toxicity", "Beta-blocker toxicity", "مسمومیت با بتابلوکر", ["T44.7X"], ["toxicology_tdm", "cardiovascular"], "critical", [
    ("screen", "screening", True, ALL(C("heart_rate", "<", 50, "/min"), C("glucose", "<", 70, "mg/dL")), 4.0, "Bradycardia with hypoglycaemia (Kerns 2007)."),
    ("dx", "diagnostic_criterion", True, ALL(C("heart_rate", "<", 50, "/min"), ANY(C("glucose", "<", 70, "mg/dL"), C("potassium", ">", 5.0, "mmol/L")), C("lactate", ">", 2, "mmol/L")), 7.0, "Bradycardic shock with hypoglycaemia/hyperkalaemia and hypoperfusion in known/declared ingestion."),
    ("excl", "exclusion_criterion", False, C("glucose", ">", 250, "mg/dL"), 5.0, "Hyperglycaemia favours calcium-channel-blocker toxicity."),
], ["acmt_beta_blocker_2017"])

D("adrenal_crisis", "Adrenal crisis", "بحران آدرنال", ["E27.2"], ["endocrine", "critical_care"], "critical", [
    ("screen", "screening", True, ALL(C("sodium", "<", 130, "mmol/L"), C("potassium", ">", 5.0, "mmol/L"), C("glucose", "<", 70, "mg/dL")), 5.0, "Hyponatraemia + hyperkalaemia + hypoglycaemia (Bornstein 2016)."),
    ("dx", "diagnostic_criterion", True, ALL(C("cortisol_morning", "<", 5, "ug/dL"), C("sodium", "<", 130, "mmol/L"), ANY(C("potassium", ">", 5.0, "mmol/L"), C("glucose", "<", 70, "mg/dL"))), 9.0, "Random cortisol <5 µg/dL during haemodynamic instability with the electrolyte triad — treat before confirmation."),
    ("alt", "diagnostic_criterion", True, ALL(C("random_cortisol", "<", 5, "ug/dL"), C("sodium", "<", 130, "mmol/L")), 8.0, "Random cortisol <5 µg/dL with hyponatraemia under stress."),
    ("excl", "exclusion_criterion", False, C("cortisol_morning", ">", 18, "ug/dL"), 7.0, "Stress cortisol >18 µg/dL excludes adrenal insufficiency."),
], ["endo_adrenal_insufficiency_2016"])

D("accidental_hypothermia", "Accidental hypothermia", "هیپوترمی اتفاقی", ["T68"], ["critical_care"], "critical", [
    ("screen", "screening", True, C("body_temperature", "<", 35, "Cel"), 5.0, "Core temperature <35 °C (WMS 2019)."),
    ("dx", "diagnostic_criterion", True, ALL(C("body_temperature", "<", 32, "Cel"), ANY(C("potassium", ">", 5.0, "mmol/L"), C("lactate", ">", 2, "mmol/L"), C("glucose", ">", 140, "mg/dL"))), 7.0, "Moderate/severe hypothermia (<32 °C) with metabolic derangement; K >12 mmol/L indicates non-survivable."),
    ("stage", "staging_severity", True, ALL(C("body_temperature", "<", 28, "Cel"), C("potassium", ">", 8, "mmol/L")), 6.0, "Severe hypothermia with hyperkalaemia >8 — poor prognosis."),
], ["wms_hypothermia_2019"])

D("heat_stroke", "Heat stroke", "گرمازدگی شدید", ["T67.0"], ["critical_care"], "critical", [
    ("screen", "screening", True, ALL(C("body_temperature", ">", 40, "Cel"), C("creatine_kinase_total", ">", 1000, "U/L")), 5.0, "Core temperature >40 °C with rhabdomyolysis (WMS 2019)."),
    ("dx", "diagnostic_criterion", True, ALL(C("body_temperature", ">", 40, "Cel"), C("creatine_kinase_total", ">", 1000, "U/L"), ANY(C("alanine_aminotransferase", ">", 120, "U/L"), C("creatinine", ">", 1.5, "mg/dL"), C("international_normalized_ratio", ">", 1.5, "1"))), 8.0, "Hyperthermia with multi-organ injury (liver, kidney, coagulopathy)."),
    ("stage", "staging_severity", True, ALL(C("alanine_aminotransferase", ">", 1000, "U/L"), C("international_normalized_ratio", ">", 2, "1")), 6.0, "Heat-stroke liver failure."),
], ["wms_heat_illness_2019"])

D("transfusion_associated_circulatory_overload", "Transfusion-associated circulatory overload (TACO)", "اضافه‌بار گردش خون ناشی از تزریق (TACO)", ["E87.71", "T80.89"], ["hematology", "transfusion", "cardiovascular"], "urgent", [
    ("screen", "screening", True, C("n_terminal_pro_bnp", ">", 1500, "pg/mL"), 4.0, "NT-proBNP >1500 pg/mL within 12 h of transfusion supports TACO (ISBT 2018)."),
    ("dx", "diagnostic_criterion", True, ALL(C("n_terminal_pro_bnp", ">", 1500, "pg/mL"), C("arterial_po2", "<", 70, "mm[Hg]")), 7.0, "Hypoxaemia with natriuretic peptide rise after transfusion; TRALI shows no BNP rise."),
    ("excl", "exclusion_criterion", False, C("n_terminal_pro_bnp", "<", 300, "pg/mL"), 6.0, "Normal NT-proBNP favours TRALI/other causes."),
], ["nhsn_taco_2021"])

D("acute_hemolytic_transfusion_reaction", "Acute haemolytic transfusion reaction", "واکنش همولیتیک حاد تزریق خون", ["T80.31"], ["hematology", "transfusion"], "critical", [
    ("screen", "screening", True, ALL(C("lactate_dehydrogenase", ">", 400, "U/L"), C("serum_haptoglobin", "<", 30, "mg/dL")), 4.0, "Intravascular haemolysis markers within 24 h of transfusion (AABB)."),
    ("dx", "diagnostic_criterion", True, ALL(C("coombs_direct_antiglobulin_test", "==", 1, "1"), C("lactate_dehydrogenase", ">", 400, "U/L"), C("serum_haptoglobin", "<", 30, "mg/dL"), C("total_bilirubin", ">", 1.5, "mg/dL")), 9.0, "Positive DAT with haemolysis and hyperbilirubinaemia post-transfusion; repeat crossmatch."),
    ("stage", "staging_severity", True, ANY(C("creatinine", ">", 1.5, "mg/dL"), C("fibrinogen", "<", 150, "mg/dL")), 6.0, "AKI or DIC complicates severe reactions."),
], ["aabb_htr_2019"])

D("organic_acidemia", "Organic acidaemia (methylmalonic / propionic / isovaleric)", "اسیدمی ارگانیک (متیل‌مالونیک / پروپیونیک / ایزووالریک)", ["E71.120", "E71.121", "E71.110"], ["metabolic", "pediatric"], "critical", [
    ("screen", "screening", True, ALL(C("anion_gap", ">", 16, "mmol/L"), C("ammonia", ">", 100, "umol/L")), 5.0, "High-AG acidosis with hyperammonaemia in a neonate/infant (Baumgartner 2014)."),
    ("dx", "diagnostic_criterion", True, ALL(C("anion_gap", ">", 20, "mmol/L"), C("bicarbonate", "<", 15, "mmol/L"), C("ammonia", ">", 150, "umol/L"), ANY(C("urine_ketones_qualitative", "==", 1, "1"), C("neutrophil_count_absolute", "<", 1.5, "10^9/L"), C("platelets", "<", 150, "10^9/L"))), 8.0, "Ketoacidosis + hyperammonaemia ± cytopenias; acylcarnitine profile/urine organic acids confirm."),
    ("excl", "exclusion_criterion", False, ALL(C("bicarbonate", ">=", 22, "mmol/L"), C("ammonia", ">", 300, "umol/L")), 6.0, "Hyperammonaemia without acidosis points to a urea-cycle disorder."),
], ["acmg_organic_acidemia_2012"], ages=["neonate", "infant", "child"])

D("hereditary_thrombophilia", "Hereditary thrombophilia", "ترومبوفیلی ارثی", ["D68.59"], ["hematology"], "routine", [
    ("screen", "screening", False, ANY(C("protein_c_activity", "<", 65, "%"), C("protein_s_activity", "<", 60, "%"), C("antithrombin_activity", "<", 80, "%")), 4.0, "Natural anticoagulant deficiency (BSH 2022) — confirm on repeat, off anticoagulants, outside acute thrombosis."),
    ("dx", "diagnostic_criterion", False, ANY(C("factor_v_leiden_mutation", "==", 1, "1"), C("prothrombin_g20210a_mutation", "==", 1, "1"), ALL(C("protein_c_activity", "<", 50, "%"), C("international_normalized_ratio", "<", 1.3, "1"))), 7.0, "Genetic confirmation, or protein C <50 % off vitamin-K antagonists."),
    ("excl", "exclusion_criterion", False, C("international_normalized_ratio", ">", 2.0, "1"), 6.0, "Warfarin lowers protein C/S — deficiency cannot be diagnosed."),
], ["bsh_thrombophilia_2022"])

D("inflammatory_bowel_disease", "Inflammatory bowel disease (unspecified)", "بیماری التهابی روده (نامشخص)", ["K50.9", "K51.9"], ["gastroenterology"], "routine", [
    ("screen", "screening", False, C("fecal_calprotectin", ">", 150, "ug/g"), 4.0, "Faecal calprotectin >150 µg/g discriminates IBD from IBS (ECCO)."),
    ("dx", "diagnostic_criterion", False, ALL(C("fecal_calprotectin", ">", 250, "ug/g"), ANY(C("c_reactive_protein", ">", 10, "mg/L"), C("hemoglobin", "<", 12, "g/dL"), C("albumin", "<", 3.5, "g/dL"), C("platelets", ">", 400, "10^9/L"))), 6.0, "Calprotectin >250 µg/g with systemic inflammation/anaemia; endoscopy confirms."),
    ("excl", "exclusion_criterion", False, C("clostridioides_difficile_toxin_a_b", "==", 1, "1"), 5.0, "C. difficile colitis explains the calprotectin rise (must be excluded before attributing to IBD)."),
], ["ecco_2019_ibd"])

D("tuberculous_pleuritis", "Tuberculous pleural effusion", "پلورزی سلی", ["A15.6"], ["infectious_disease", "pulmonology"], "urgent", [
    ("screen", "screening", False, C("pleural_fluid_adenosine_deaminase", ">=", 40, "U/L"), 5.0, "Pleural ADA ≥40 U/L: sensitivity 92 %, specificity 90 % (Aggarwal 2019)."),
    ("dx", "diagnostic_criterion", False, ALL(C("pleural_fluid_adenosine_deaminase", ">=", 40, "U/L"), C("pleural_fluid_lactate_dehydrogenase", ">", 200, "U/L"), C("pleural_fluid_total_protein", ">", 3.0, "g/dL")), 7.0, "Lymphocytic exudate (Light criteria) with ADA ≥40 U/L; culture/PCR confirms."),
    ("excl", "exclusion_criterion", False, C("pleural_fluid_adenosine_deaminase", "<", 20, "U/L"), 7.0, "ADA <20 U/L essentially excludes TB pleuritis in immunocompetent adults."),
], ["ats_pleural_tb_2017"])

D("valproate_induced_hyperammonemic_encephalopathy", "Valproate-induced hyperammonaemic encephalopathy", "انسفالوپاتی هیپرآمونمیک ناشی از والپروات", ["T42.6X", "G92.8"], ["toxicology_tdm", "neurology"], "urgent", [
    ("screen", "screening", True, C("ammonia", ">", 80, "umol/L"), 4.0, "Ammonia >80 µmol/L on valproate (Baddour 2018)."),
    ("dx", "diagnostic_criterion", True, ALL(C("ammonia", ">", 100, "umol/L"), C("alanine_aminotransferase", "<", 80, "U/L"), C("valproic_acid_total", ">=", 50, "ug/mL")), 8.0, "Hyperammonaemia with normal transaminases and therapeutic/high valproate level — carnitine deficiency mechanism."),
    ("excl", "exclusion_criterion", False, ALL(C("alanine_aminotransferase", ">", 200, "U/L"), C("international_normalized_ratio", ">", 1.5, "1")), 6.0, "Hepatic failure pattern = valproate hepatotoxicity rather than isolated hyperammonaemia."),
], ["vpa_hyperammonemia_2020"])

D("reye_syndrome", "Reye syndrome", "سندرم ری", ["G93.7"], ["pediatric", "hepatology", "neurology"], "critical", [
    ("screen", "screening", True, ALL(C("ammonia", ">", 100, "umol/L"), C("alanine_aminotransferase", ">", 120, "U/L")), 5.0, "Hyperammonaemia with transaminases ≥3× ULN after viral illness/aspirin (CDC case definition)."),
    ("dx", "diagnostic_criterion", True, ALL(C("ammonia", ">", 100, "umol/L"), C("alanine_aminotransferase", ">", 120, "U/L"), C("total_bilirubin", "<=", 3.0, "mg/dL"), C("international_normalized_ratio", ">", 1.5, "1")), 8.0, "Hyperammonaemia + transaminitis + coagulopathy with bilirubin ≤3 mg/dL (anicteric) — CDC definition."),
    ("excl", "exclusion_criterion", False, C("total_bilirubin", ">", 5, "mg/dL"), 6.0, "Marked jaundice argues against Reye syndrome."),
], ["aap_reye_2017"], ages=["infant", "child", "adolescent"])

D("toxic_shock_syndrome", "Toxic shock syndrome", "سندرم شوک توکسیک", ["A48.3"], ["infectious_disease", "critical_care"], "critical", [
    ("screen", "screening", True, ALL(C("body_temperature", ">=", 38.9, "Cel"), C("creatinine", ">", 1.5, "mg/dL"), C("platelets", "<", 100, "10^9/L")), 5.0, "Fever ≥38.9 °C with renal and haematological involvement (CDC 2011)."),
    ("dx", "diagnostic_criterion", True, ALL(C("body_temperature", ">=", 38.9, "Cel"), ANY(C("creatinine", ">", 2.0, "mg/dL"), C("platelets", "<", 100, "10^9/L"), C("creatine_kinase_total", ">", 400, "U/L"), C("total_bilirubin", ">", 2.4, "mg/dL"), C("alanine_aminotransferase", ">", 80, "U/L")), C("blood_culture", "==", 0, "1")), 7.0, "CDC multisystem criteria (≥3 organ systems) with negative blood cultures (except S. aureus)."),
    ("excl", "exclusion_criterion", False, C("body_temperature", "<", 38, "Cel"), 6.0, "Afebrile presentation does not meet the CDC case definition."),
], ["cdc_tss_2011"])

D("ketotic_hypoglycemia_of_childhood", "Ketotic hypoglycaemia of childhood", "هیپوگلیسمی کتوتیک کودکی", ["E16.2"], ["pediatric", "endocrine"], "routine", [
    ("screen", "screening", False, ALL(C("glucose", "<", 55, "mg/dL"), C("beta_hydroxybutyrate", ">", 2.0, "mmol/L")), 4.0, "Hypoglycaemia with appropriate ketosis in a toddler after fasting (Thornton 2015)."),
    ("dx", "diagnostic_criterion", False, ALL(C("glucose", "<", 55, "mg/dL"), C("beta_hydroxybutyrate", ">", 2.0, "mmol/L"), C("insulin", "<", 2, "uIU/mL"), C("lactate", "<", 2.5, "mmol/L"), C("ammonia", "<", 80, "umol/L")), 7.0, "Ketotic, hypoinsulinaemic hypoglycaemia with normal lactate and ammonia — diagnosis of exclusion."),
    ("excl", "exclusion_criterion", False, ANY(C("insulin", ">=", 3, "uIU/mL"), C("lactate", ">", 5, "mmol/L")), 7.0, "Hyperinsulinism or lactic acidosis (GSD) are alternative diagnoses."),
], ["pes_ketotic_hypoglycemia_2015"], ages=["infant", "child"])

D("hypertriglyceridemia_induced_pancreatitis", "Hypertriglyceridaemia-induced acute pancreatitis", "پانکراتیت حاد ناشی از هیپرتری‌گلیسریدمی", ["K85.9", "E78.1"], ["gastroenterology"], "urgent", [
    ("screen", "screening", True, ALL(C("lipase", ">", 180, "U/L"), C("triglycerides", ">", 500, "mg/dL")), 4.0, "Pancreatitis with TG >500 mg/dL (ACG 2024)."),
    ("dx", "diagnostic_criterion", True, ALL(C("lipase", ">", 180, "U/L"), C("triglycerides", ">", 1000, "mg/dL")), 8.0, "Lipase ≥3× ULN with TG >1000 mg/dL — hypertriglyceridaemia is the cause (ACG 2024)."),
    ("excl", "exclusion_criterion", False, C("triglycerides", "<", 300, "mg/dL"), 6.0, "TG <300 mg/dL does not cause pancreatitis."),
], ["acg_pancreatitis_2024"], subtype_of="acute_pancreatitis")

D("alcoholic_pancreatitis", "Alcohol-induced acute pancreatitis", "پانکراتیت حاد الکلی", ["K85.2"], ["gastroenterology"], "urgent", [
    ("screen", "screening", True, ALL(C("lipase", ">", 180, "U/L"), C("gamma_glutamyl_transferase", ">", 100, "U/L")), 3.0, "Pancreatitis with GGT elevation suggesting alcohol exposure."),
    ("dx", "diagnostic_criterion", True, ALL(C("lipase", ">", 180, "U/L"), C("gamma_glutamyl_transferase", ">", 100, "U/L"), C("mean_corpuscular_volume", ">", 98, "fL"), C("triglycerides", "<", 500, "mg/dL")), 6.0, "Lipase ≥3× ULN with GGT and macrocytosis (alcohol markers) after TG and biliary causes excluded."),
    ("excl", "exclusion_criterion", False, C("alanine_aminotransferase", ">", 150, "U/L"), 5.0, "ALT >150 U/L has 95 % PPV for biliary pancreatitis (Tenner 1994)."),
], ["acg_pancreatitis_2024"], subtype_of="acute_pancreatitis")

D("malignant_pleural_effusion", "Malignant pleural effusion", "افیوژن پلور بدخیم", ["J91.0"], ["pulmonology", "oncology"], "urgent", [
    ("screen", "screening", False, ALL(C("pleural_fluid_total_protein", ">", 3.0, "g/dL"), C("pleural_fluid_lactate_dehydrogenase", ">", 200, "U/L"), C("pleural_fluid_adenosine_deaminase", "<", 40, "U/L")), 4.0, "Exudate (Light criteria) with low ADA (BTS 2023)."),
    ("dx", "diagnostic_criterion", False, ALL(C("pleural_fluid_total_protein", ">", 3.0, "g/dL"), C("pleural_fluid_lactate_dehydrogenase", ">", 200, "U/L"), C("pleural_fluid_adenosine_deaminase", "<", 40, "U/L"), C("pleural_fluid_glucose", "<", 60, "mg/dL")), 6.0, "Low-glucose exudate with low ADA; cytology confirms."),
    ("excl", "exclusion_criterion", False, C("pleural_fluid_adenosine_deaminase", ">=", 40, "U/L"), 6.0, "High ADA favours tuberculous pleuritis."),
], ["bts_pleural_2023"])

D("pancytopenia", "Pancytopenia", "پان‌سیتوپنی", ["D61.818"], ["hematology"], "urgent", [
    ("screen", "screening", True, ALL(C("hemoglobin", "<", 10, "g/dL"), C("platelets", "<", 100, "10^9/L"), C("white_blood_cell_count", "<", 4, "10^9/L")), 5.0, "Reduction of all three lineages (Killick 2016)."),
    ("dx", "diagnostic_criterion", True, ALL(C("hemoglobin", "<", 10, "g/dL"), C("platelets", "<", 100, "10^9/L"), C("neutrophil_count_absolute", "<", 1.5, "10^9/L")), 7.0, "Anaemia + thrombocytopenia + neutropenia — marrow examination indicated."),
    ("stage", "staging_severity", True, ALL(C("neutrophil_count_absolute", "<", 0.5, "10^9/L"), C("platelets", "<", 20, "10^9/L")), 6.0, "Severe (Camitta) cytopenias."),
], ["bsh_pancytopenia_2016"])

D("acute_hepatitis", "Acute hepatitis (unspecified aetiology)", "هپاتیت حاد (علت نامشخص)", ["K72.00", "B17.9"], ["hepatology"], "urgent", [
    ("screen", "screening", False, C("alanine_aminotransferase", ">", 200, "U/L"), 3.0, "ALT >5× ULN (Wendon 2017)."),
    ("dx", "diagnostic_criterion", False, ALL(C("alanine_aminotransferase", ">", 400, "U/L"), C("alkaline_phosphatase", "<", 300, "U/L")), 6.0, "Hepatocellular pattern (R ratio >5) with ALT ≥10× ULN; aetiology work-up required."),
    ("stage", "staging_severity", True, ALL(C("alanine_aminotransferase", ">", 400, "U/L"), C("international_normalized_ratio", ">=", 1.5, "1")), 7.0, "INR ≥1.5 marks acute liver failure risk."),
], ["aasld_acute_hepatitis_2023"])

D("neonatal_cholestasis", "Neonatal cholestasis", "کلستاز نوزادی", ["P59.1", "K83.1"], ["gastroenterology", "pediatric", "hepatology"], "urgent", [
    ("screen", "screening", True, C("direct_bilirubin", ">", 1.0, "mg/dL"), 5.0, "Direct bilirubin >1.0 mg/dL in an infant is always abnormal (NASPGHAN 2017)."),
    ("dx", "diagnostic_criterion", True, ALL(C("direct_bilirubin", ">", 1.0, "mg/dL"), C("total_bilirubin", ">", 2.0, "mg/dL")), 7.0, "Conjugated hyperbilirubinaemia; urgent evaluation for biliary atresia within 60 days of life."),
    ("excl", "exclusion_criterion", False, C("direct_bilirubin", "<", 0.5, "mg/dL"), 6.0, "Unconjugated jaundice is not cholestasis."),
], ["naspghan_biliary_atresia_2017"], ages=["neonate", "infant"])

# ------------------------------------------------------------------ build
def build(reg, feats):
    added_d = added_r = added_s = 0; skipped = []
    diseases, rules, sources = reg["diseases"], reg["rules"], reg["guideline_sources"]
    def fids(expr):
        out = []
        if "feature_id" in expr: out.append(expr["feature_id"])
        for k in ("all", "any"):
            for sub in expr.get(k, []): out += fids(sub)
        return out
    for sid, (org, title, year, url, scope) in SOURCES.items():
        if sid not in sources:
            sources[sid] = _src(org, title, year, url, scope); added_s += 1
    for e in E:
        if e["id"] in diseases:
            skipped.append((e["id"], "exists")); continue
        for s in e["sources"]:
            assert s in sources, s
        rule_recs = []
        for suffix, rtype, urgent, expr, w, rationale in e["rules"]:
            missing = [f for f in fids(expr) if f not in feats]
            if missing:
                skipped.append((e["id"] + ":" + suffix, f"missing features {missing}")); continue
            rid = f"{e['id']}_{suffix}_p131"
            rule_recs.append({
                "rule_id": rid, "disease_id": e["id"], "rule_type": rtype, "legacy_rule_type": rtype,
                "specificity": "specific", "status": "candidate_requires_specialist_validation", "executable": True,
                "urgent": bool(urgent), "expression": expr, "weight": float(w),
                "population": {"age_groups": e["ages"], "sex": e["sex"], "pregnancy": e["pregnancy"]},
                "result": {"allowed_labels": list(LABELS), "diagnosis_allowed": False},
                "confirmation": {"required": True, "human_review": True, "repeat_or_alternative_test": "context_dependent"},
                "limitations": [rationale, "Added in registry patch 13.1.0 (2026-10-21) to support analysis-layer coverage; requires specialist validation."],
                "source_ids": list(e["sources"]), "title": f"{e['id']} — {rtype.replace('_', ' ').title()}",
                "scientific_explanation": rationale, "clinical_rationale": rationale,
                "evidence_tier": "tier_a", "entity_kind": "clinical_entity",
            })
        if not any(r["rule_type"] in ("screening", "diagnostic_criterion") for r in rule_recs):
            skipped.append((e["id"], "no executable screening/diagnostic rule after feature check")); continue
        layers = {}
        req, opt = [], []
        for r in rule_recs:
            layers.setdefault(r["rule_type"], []).append(r["rule_id"])
            tgt = req if r["rule_type"] == "diagnostic_criterion" else opt
            for f in fids(r["expression"]):
                if f not in tgt: tgt.append(f)
            rules[r["rule_id"]] = r; added_r += 1
        diseases[e["id"]] = {
            "identity": {"disease_id": e["id"], "name_en": e["en"], "name_fa": e["fa"], "icd10": e["icd"], "snomed_ct": [],
                         "wikipedia_url": "https://en.wikipedia.org/wiki/" + re.sub(r"\s+", "_", e["en"].split(" (")[0])},
            "classification": {"domains": e["domains"], "clinical_priority": e["priority"], "entity_kind": "clinical_entity"},
            "population": {"age_groups": e["ages"], "sex": e["sex"], "pregnancy": e["pregnancy"]},
            "feature_links": {"required": req, "optional": [f for f in opt if f not in req], "excluded": []},
            "layers": layers, "rule_ids": [r["rule_id"] for r in rule_recs], "guideline_source_ids": list(e["sources"]),
            "coverage": {"catalogued": True, "executable_rule_available": True, "status": "executable_rule_active",
                         "reason": f"{len(rule_recs)} executable guideline rule(s) (patch 13.1.0)."},
            "provenance": {"added_by": "registry_patch_20261021.py", "added_on": TODAY,
                           "note": "AI-assisted curation from cited guideline thresholds; not expert-committee reviewed."},
        }
        if e["subtype_of"] and e["subtype_of"] in diseases:
            reg.setdefault("subtype_index", {})[e["id"]] = e["subtype_of"]
        added_d += 1
    md = reg["registry_metadata"]
    md["version"] = "13.1.0-CLINICAL-CURATED"; md["last_updated"] = TODAY
    md["total_diseases"] = len(diseases); md["total_rules"] = len(rules); md["total_sources"] = len(sources)
    md["executable_rules"] = sum(1 for r in rules.values() if r.get("executable"))
    md.setdefault("patches", []).append({"patch": "13.1.0", "date": TODAY, "diseases_added": added_d, "rules_added": added_r, "sources_added": added_s,
                                         "script": "registry_patch_20261021.py", "reason": "entities required by ESL/analysis layers lacked registry ids"})
    qa = reg.get("quality_assurance", {}); qa["disease_count"] = len(diseases); qa["rule_count"] = len(rules); qa["source_count"] = len(sources)
    vr = reg.get("validation_report", {}); vr["validated_on"] = TODAY
    return added_d, added_r, added_s, skipped


def main():
    apply = "--apply" in sys.argv
    reg = json.loads(brotli.decompress(REG.read_bytes()))
    feats = json.loads(brotli.decompress(FEAT.read_bytes()))["features"]
    before = (len(reg["diseases"]), len(reg["rules"]), len(reg["guideline_sources"]))
    d, r, s, skipped = build(reg, feats)
    print(f"before diseases/rules/sources = {before}")
    print(f"added  diseases={d} rules={r} sources={s}")
    for sk in skipped: print("  skipped:", sk)
    # integrity
    for rid, rule in reg["rules"].items():
        assert rule["disease_id"] in reg["diseases"], rid
        for sid in rule["source_ids"]: assert sid in reg["guideline_sources"], (rid, sid)
    raw = json.dumps(reg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    reg["registry_metadata"]["sha256_uncompressed"] = hashlib.sha256(raw).hexdigest()
    raw = json.dumps(reg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if apply:
        for p in (REG, REG2):
            bak = p.with_suffix(p.suffix + ".bak_13_0_0")
            if not bak.exists(): shutil.copy2(p, bak)
        blob = brotli.compress(raw, quality=11)
        REG.write_bytes(blob); REG2.write_bytes(blob)
        print(f"written {REG.name} and {REG2.name}: {len(blob)/1e6:.2f} MB (backups *.bak_13_0_0)")
    else:
        print("dry-run only; pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
