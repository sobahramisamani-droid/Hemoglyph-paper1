"""Registry 15.0.0 - provenance/fidelity release (protocol: PROTOCOL_15_0_0.md).

Classes applied, in this order:
  R1  template biomarker-pair rules (co_*) re-attributed to the synthetic source 'generated_pair_pattern'
  R2a nonspecific single-marker rules retired            -> status retired_v15_0_0_nonspecific_single_marker
  R2b clinically incorrect rules retired                  -> status retired_v15_0_0_clinically_incorrect
  R2c unsourced / duplicate-threshold rules retired       -> status retired_v15_0_0_unsourced_threshold
  R3  re-sourcing; provenance.verified_* written ONLY where the threshold + analyte were found in text
      retrieved on 2026-10-27 (quotes in VERIFIED below; the retrieval log is in review_15_0_0.json)
  R4  reference-limit rules re-attributed to 'reference_interval_convention' (+ topical locator when one exists)
  R5  closed list of logic corrections, each tied to a verified quote
  R6  source-record repairs (wrong URL / empty stub / missing DOI)
Every edit is recorded on the rule (curation_note, curated_on, curation_version) and in the changelog.
Applies to BOTH registry files; 15.0.0 artefacts archived under release/registry_15.0.0/.
"""
import brotli, json, shutil, os, hashlib, copy, collections, datetime

ROOT = "/home/user/Hemoglyph"
TODAY = "2026-10-27"
VER = "15.0.0"

# ----------------------------------------------------------------------------------------------
# Verified statements (verbatim, retrieved 2026-10-27). key -> (source_id, locator, quote)
# ----------------------------------------------------------------------------------------------
VERIFIED = {
 "who24_tab2": ("who_anaemia_2024", "https://iris.who.int/server/api/core/bitstreams/f9f74397-1440-478d-a63c-26f29a01552f/content (Table 2)",
    "Haemoglobin cut-offs (g/L) to define anaemia: children 6-23 months <105; 24-59 months <110; 5-11 years <115; 12-14 years <120; non-pregnant women 15-65 years <120; men 15-65 years <130; pregnancy first trimester <110, second trimester <105, third trimester <110."),
 "who24_tab3": ("who_anaemia_2024", "same bitstream (Table 3)",
    "Severity in adults: mild 110-119 (women) / 110-129 (men); moderate 80-109; severe <80 g/L."),
 "who20_ferritin": ("who_ferritin_2020", "https://cdn.who.int/media/docs/default-source/micronutrients/ferritin-guideline/ferritin-guidelines-executivesummary.pdf (Table)",
    "Thresholds for iron deficiency (ferritin, ug/L) in apparently healthy individuals: infants and young children (0-23 months) <12; children under 5 years (24-59 months) <12; children (5 to less than 10 years) <15; adolescents <15; adults (20-59 years) <15; older persons (60+) <15; pregnant women <15 (first trimester). With infection or inflammation: <30 (under 5 years) and <70 (5 years and older)."),
 "bsg21_tsat": ("bsg_ida_2021", "PMC8515119",
    "A transferrin saturation of <20% is indicative of iron restriction, particularly in thalassaemia carriers."),
 "ada26_s6_hypo": ("ada_2026_s6_glycemic_goals", "PMC12690178 (Table 6.4)",
    "Level 1 hypoglycemia is defined as a measurable glucose concentration <70 mg/dL (<3.9 mmol/L) and >=54 mg/dL (>=3.0 mmol/L). Level 2 hypoglycemia (defined as a blood glucose concentration <54 mg/dL [<3.0 mmol/L]) is the threshold at which neuroglycopenic symptoms begin to occur."),
 "ada26_s2_dx": ("ada_2026", "PMC12690183 (Table 2.1)",
    "Criteria for the diagnosis of diabetes: FPG >=126 mg/dL (7.0 mmol/L) OR 2-h PG >=200 mg/dL (11.1 mmol/L) during OGTT OR A1C >=6.5% (48 mmol/mol) OR, in an individual with classic symptoms of hyperglycemia or hyperglycemic crisis, a random plasma glucose >=200 mg/dL."),
 "ada26_s2_prediab": ("ada_2026", "PMC12690183 (Table 2.2)",
    "Prediabetes: FPG 100-125 mg/dL (impaired fasting glucose) OR 2-h PG 140-199 mg/dL (impaired glucose tolerance) OR A1C 5.7-6.4% (39-47 mmol/mol)."),
 "adaeasd24_ag": ("ada_easd_hyperglycemic_crises_2024", "PMC11272983",
    "An anion gap >12 mmol/L indicates the presence of a high anion gap metabolic acidosis consistent with DKA."),
 "adaeasd24_edka": ("ada_easd_hyperglycemic_crises_2024", "PMC11272983",
    "Approximately 10% of patients with DKA present with euglycemic DKA, which is defined as plasma glucose levels <200 mg/dL [11.1 mmol/L] in the presence of ketosis and metabolic acidosis criteria of DKA."),
 "adaeasd24_hhs": ("ada_easd_hyperglycemic_crises_2024", "PMC11272983 (Fig. 2)",
    "HHS: plasma glucose >=600 mg/dL, calculated effective osmolality >300 or total osmolality >320 mOsm/kg, absence of significant ketonaemia/acidosis."),
 "sepsis3_shock": ("sepsis3_2016", "PMC4968574",
    "Patients with septic shock can be clinically identified by a vasopressor requirement to maintain a mean arterial pressure of 65 mm Hg or greater and serum lactate level greater than 2 mmol/L (>18 mg/dL) in the absence of hypovolemia."),
 "sepsis3_sirs": ("sepsis3_2016", "PMC4968574 (Box 1, SIRS criteria reproduced)",
    "SIRS: temperature >38 C or <36 C; heart rate >90/min; respiratory rate >20/min or PaCO2 <32 mm Hg; white blood cell count >12 000/mm3 or <4000/mm3 or >10% immature bands."),
 "aha18_ldl190": ("acc_aha_cholesterol_2018", "PMC7403606 (section 4.2)",
    "Severe Hypercholesterolemia (LDL-C >=190 mg/dL [>=4.9 mmol/L]). In patients with severe primary hypercholesterolemia (LDL-C level >=190 mg/dL), without calculating 10-year ASCVD risk, begin high-intensity statin therapy."),
 "aha18_metsyn": ("acc_aha_cholesterol_2018", "PMC7403606 (risk-enhancing factors table)",
    "Metabolic syndrome (increased waist circumference, elevated triglycerides [>175 mg/dL], elevated blood pressure, elevated glucose, and low HDL-C [<40 mg/dL in men; <50 in women mg/dL] are factors; tally of 3 makes the diagnosis)."),
 "atp3_tab2": ("ncep_atp3_2001", "https://www.nhlbi.nih.gov/files/docs/guidelines/atp3xsum.pdf (Table 2)",
    "ATP III Classification of LDL, Total, and HDL Cholesterol (mg/dL): LDL <100 optimal; 100-129 near optimal; 130-159 borderline high; 160-189 high; >=190 very high. Total cholesterol <200 desirable; 200-239 borderline high; >=240 high. HDL <40 low; >=60 high."),
 "atp3_tg": ("ncep_atp3_2001", "same PDF",
    "ATP III classification of serum triglycerides: normal <150 mg/dL; borderline-high 150-199 mg/dL; high 200-499 mg/dL; very high >=500 mg/dL."),
 "atp3_metsyn": ("ncep_atp3_2001", "same PDF (clinical identification of the metabolic syndrome)",
    "Triglycerides >=150 mg/dL; HDL cholesterol men <40 mg/dL, women <50 mg/dL; blood pressure >=130/>=85 mmHg; fasting glucose >=110 mg/dL (lowered to >=100 mg/dL in the 2005 AHA/NHLBI update, 10.1161/CIRCULATIONAHA.105.169404 - update text not retrieved)."),
 "gout15_urate": ("acr_eular_gout_2015", "PMC4602275 (classification criteria, item 5)",
    "Serum urate level, off-treatment. Categories are defined as <4 mg/dL (0.24 mmol/L); 4-<6; 6-<8; 8-<10 mg/dL; >=10 mg/dL (>=0.60 mmol/L). If the serum urate level is <4 mg/dL, 4 points are subtracted from the total score."),
 "masld23_alt": ("aasld_masld_2023", "PMC10735173",
    "A true normal alanine aminotransferase (ALT) ranges from 29 to 33 U/L in men and from 19 to 25 U/L in women."),
 "acg17_alt": ("acg_liver_chemistries_2017", "PubMed abstract 10.1038/ajg.2016.517",
    "A true healthy normal ALT level ranges from 29 to 33 IU/l for males, 19 to 25 IU/l for females and levels above this should be assessed."),
 "kdigo24_gfr": ("kdigo_ckd_2024", "https://kdigo.org/wp-content/uploads/2024/03/KDIGO-2024-CKD-Guideline.pdf (Table 1/2)",
    "Decreased GFR: GFR <60 ml/min per 1.73 m2 (GFR categories G3a-G5) ... for >3 months to indicate a diagnosis of CKD."),
 "kdigo24_acr": ("kdigo_ckd_2024", "same PDF (albuminuria categories)",
    "A1 normal to mildly increased <30 mg/g (<3 mg/mmol); A2 moderately increased 30-300 mg/g (3-30 mg/mmol); A3 severely increased >300 mg/g (>30 mg/mmol)."),
 "kdigo12_aki": ("kdigo_aki_2012", "https://kdigo.org/wp-content/uploads/2016/10/KDIGO-2012-AKI-Guideline-English.pdf (2.1.1)",
    "AKI is defined as any of the following: increase in SCr by >=0.3 mg/dl (>=26.5 umol/l) within 48 hours; or increase in SCr to >=1.5 times baseline, which is known or presumed to have occurred within the prior 7 days; or urine volume <0.5 ml/kg/h for 6 hours."),
 "aspen20_rs": ("aspen_refeeding_2020", "PubMed abstract 10.1002/ncp.10474",
    "A decrease in any 1, 2, or 3 of serum phosphorus, potassium, and/or magnesium levels by 10%-20% (mild), 20%-30% (moderate), or >30% and/or organ dysfunction resulting from a decrease in any of these."),
}

# Locators that resolve (checked 2026-10-27) but whose threshold text could NOT be retrieved (abstract only /
# publisher blocked). Rules citing them keep the source; evidence_tier is left unchanged and a note is written.
LOCATOR_ONLY = {
 "ese_hyponatremia_2014": "10.1530/EJE-13-1020", "kdigo_potassium_2020": "10.1016/j.kint.2019.09.018",
 "esc_hf_2021_2023": "10.1093/eurheartj/ehab368", "udmi4_2018": "10.1093/eurheartj/ehy462",
 "atlanta_pancreatitis_2012": "10.1136/gutjnl-2012-302779", "cairo_bishop_2004": "10.1111/j.1365-2141.2004.05094.x",
 "rodeghiero_itp_2009": "10.1182/blood-2008-07-162503", "sccm_sepsis_2021": "10.1097/CCM.0000000000005337",
 "ncep_atp3_2005": "10.1161/CIRCULATIONAHA.105.169404", "ata_hypothyroid_2012": "10.1089/thy.2012.0205",
}

# ----------------------------------------------------------------------------------------------
# Source records (new or repaired)
# ----------------------------------------------------------------------------------------------
NEW_SOURCES = {
 "generated_pair_pattern": dict(
    organization="Hemoglyph registry build pipeline (synthetic)", year=2025,
    title="Template-generated two-analyte co-abnormality pattern (no external guideline). Generated from disease->feature links; thresholds are reference-limit conventions.",
    url="", doi=None, authors="", journal="",
    evidence_status="synthetic_template__not_a_literature_source", verified_at=TODAY,
    note="Introduced in 15.0.0 to replace the misattribution of the template co_* rules to 'who_essential_lab_2024'. These rules carry no guideline provenance and are labelled as such in the application."),
 "reference_interval_convention": dict(
    organization="Hemoglyph curation (reference-limit convention)", year=2025,
    title="Conventional adult reference limits used as screening cut-points (sodium 135-145 mmol/L, potassium 3.5-5.0 mmol/L, chloride 98-107 mmol/L, magnesium 1.7 mg/dL, phosphate 2.5-4.5 mg/dL, WBC 4-11 x10^9/L, ANC 7.7 x10^9/L, platelets 150-450 x10^9/L, total bilirubin 1.2 mg/dL, INR 1.5, TSH 0.4-4.5 mIU/L, PaCO2 35-45 mmHg, pH 7.35-7.45, bicarbonate 22-26 mmol/L, anion gap 12). Laboratory-specific intervals supersede these values.",
    url="", doi=None, authors="", journal="",
    evidence_status="convention__laboratory_specific_intervals_supersede", verified_at=TODAY,
    note="Introduced in 15.0.0. Replaces topic-mismatched citations (e.g. an Endocrine Society collection page for hyponatraemia) with an explicit statement that the threshold is a reference-limit convention, not a guideline criterion."),
 "who_ferritin_2020": dict(
    organization="World Health Organization", year=2020,
    title="WHO guideline on use of ferritin concentrations to assess iron status in individuals and populations",
    url="https://www.who.int/publications/i/item/9789240000124", doi=None, isbn="978-92-4-000012-4",
    locator="https://cdn.who.int/media/docs/default-source/micronutrients/ferritin-guideline/ferritin-guidelines-executivesummary.pdf",
    authors="WHO", journal="", evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "ncep_atp3_2001": dict(
    organization="NCEP / NHLBI", year=2001,
    title="Executive Summary of the Third Report of the National Cholesterol Education Program (NCEP) Expert Panel on Detection, Evaluation, and Treatment of High Blood Cholesterol in Adults (Adult Treatment Panel III)",
    url="https://www.nhlbi.nih.gov/files/docs/guidelines/atp3xsum.pdf", doi="10.1001/jama.285.19.2486",
    authors="Expert Panel on Detection, Evaluation, and Treatment of High Blood Cholesterol in Adults", journal="JAMA 2001;285:2486-2497",
    evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "ada_2026_s6_glycemic_goals": dict(
    organization="American Diabetes Association", year=2026,
    title="6. Glycemic Goals and Hypoglycemia: Standards of Care in Diabetes-2026",
    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC12690178/", doi="10.2337/dc26-S006", pmcid="PMC12690178",
    authors="ADA Professional Practice Committee", journal="Diabetes Care 2026;49(Suppl 1):S128-S145",
    evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "rodeghiero_itp_2009": dict(
    organization="International Working Group (ITP)", year=2009,
    title="Standardization of terminology, definitions and outcome criteria in immune thrombocytopenic purpura of adults and children: report from an international working group",
    url="https://doi.org/10.1182/blood-2008-07-162503", doi="10.1182/blood-2008-07-162503",
    authors="Rodeghiero F et al.", journal="Blood 2009;113:2386-2393",
    evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
 "ata_hypothyroid_2012": dict(
    organization="American Thyroid Association / AACE", year=2012,
    title="Clinical practice guidelines for hypothyroidism in adults: cosponsored by the American Association of Clinical Endocrinologists and the American Thyroid Association",
    url="https://doi.org/10.1089/thy.2012.0205", doi="10.1089/thy.2012.0205",
    authors="Garber JR et al.", journal="Thyroid 2012;22:1200-1235",
    evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
}
REPAIR_SOURCES = {
 "who_anaemia_2024": dict(url="https://www.who.int/publications/i/item/9789240088542", isbn="978-92-4-008854-2",
    locator="https://iris.who.int/server/api/core/bitstreams/f9f74397-1440-478d-a63c-26f29a01552f/content",
    evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY,
    note="15.0.0: URL corrected (previous item id 9789240090446 did not correspond to this guideline); Table 2/3 cut-offs verified from the IRIS PDF."),
 "who_2024": dict(evidence_status="retired_stub__alias_of_who_anaemia_2024", verified_at=TODAY,
    note="15.0.0: empty placeholder record ('Who 2024', no URL). The only rule that cited it now cites who_anaemia_2024."),
 "kdigo_aki_2012": dict(doi="10.1038/kisup.2012.1", locator="https://kdigo.org/wp-content/uploads/2016/10/KDIGO-2012-AKI-Guideline-English.pdf",
    evidence_status="authoritative_international_guideline__definition_text_verified", verified_at=TODAY),
 "kdigo_ckd_2024": dict(doi="10.1016/j.kint.2023.10.018", locator="https://kdigo.org/wp-content/uploads/2024/03/KDIGO-2024-CKD-Guideline.pdf",
    evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "acc_aha_cholesterol_2018": dict(doi="10.1161/CIR.0000000000000625", pmcid="PMC7403606",
    evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "acr_eular_gout_2015": dict(doi="10.1002/art.39254", pmcid="PMC4602275",
    evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "aasld_masld_2023": dict(pmcid="PMC10735173", evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "acg_liver_chemistries_2017": dict(evidence_status="authoritative_international_guideline__threshold_text_verified_abstract", verified_at=TODAY),
 "sepsis3_2016": dict(doi="10.1001/jama.2016.0287", pmcid="PMC4968574", evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "bsg_ida_2021": dict(doi="10.1136/gutjnl-2021-325210", pmcid="PMC8515119", evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "ada_2026": dict(doi="10.2337/dc26-S002", pmcid="PMC12690183", evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "ada_easd_hyperglycemic_crises_2024": dict(doi="10.2337/dci24-0032", pmcid="PMC11272983", evidence_status="authoritative_international_guideline__threshold_text_verified", verified_at=TODAY),
 "aspen_refeeding_2020": dict(doi="10.1002/ncp.10474", evidence_status="authoritative_international_guideline__threshold_text_verified_abstract", verified_at=TODAY),
 "ese_hyponatremia_2014": dict(doi="10.1530/EJE-13-1020", evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
 "kdigo_potassium_2020": dict(doi="10.1016/j.kint.2019.09.018", evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
 "cairo_bishop_2004": dict(doi="10.1111/j.1365-2141.2004.05094.x", evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
 "atlanta_pancreatitis_2012": dict(doi="10.1136/gutjnl-2012-302779", evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
 "ncep_atp3_2005": dict(doi="10.1161/CIRCULATIONAHA.105.169404", evidence_status="locator_verified_pubmed__threshold_text_not_retrieved", verified_at=TODAY),
}

# ----------------------------------------------------------------------------------------------
# R2a - nonspecific single-marker rules (entity cannot be supported by this analyte alone)
# ----------------------------------------------------------------------------------------------
R2A_IDS = """
mcardle_disease_screening_1_v1 mcardle_disease_staging_severity_1_v1 serotonin_syndrome_screening_1_v1
serotonin_syndrome_diagnostic_criterion_1_v1 pompe_disease_ck_pattern_v1 pompe_disease_ck_urgent_v1
amyotrophic_lateral_sclerosis_staging_severity_1_v1 tetanus_staging_severity_1_v1 trichinellosis_staging_severity_2_v1
polymyositis_staging_severity_1_v1 rhabdomyosarcoma_staging_severity_2_v1 neuroleptic_malignant_syndrome_screening_1_v1
neuroleptic_malignant_syndrome_diagnostic_criterion_1_v1 neuroleptic_malignant_syndrome_staging_severity_1_v1
siadh_screening_2_v1 siadh_staging_severity_1_v1 addison_disease_staging_severity_3_v1 cystic_fibrosis_staging_severity_1_v1
cystic_fibrosis_screening_2_v1 pyloric_stenosis_screening_1_v1 pyloric_stenosis_screening_2_v1 pyloric_stenosis_staging_severity_3_v1
pyloric_stenosis_staging_severity_4_v1 acute_gastroenteritis_diagnostic_criterion_1_v1 acute_gastroenteritis_screening_1_v1
sepsis_screening_3_v1 hepatic_abscess_screening_1_v1 hepatic_abscess_screening_2_v1 hepatic_abscess_staging_severity_1_v1
hepatic_abscess_staging_severity_4_v1 ascending_cholangitis_staging_severity_1_v1 ascending_cholangitis_screening_1_v1
acute_cholangitis_screening_1_v1 gilbert_syndrome_screening_1_v1 gilbert_syndrome_staging_severity_1_v1
paget_disease_screening_1_v1 gaucher_disease_screening_1_v1 gaucher_disease_staging_severity_1_v1
necrotizing_enterocolitis_screening_1_v1 visceral_leishmaniasis_screening_2_v1 visceral_leishmaniasis_staging_severity_2_v1
down_syndrome_screening_1_v1 galactosemia_screening_1_v1 renal_cell_carcinoma_screening_2_v1 mumps_staging_severity_2_v1
mumps_screening_3_v1 mumps_staging_severity_1_v1 salivary_gland_tumor_staging_severity_1_v1 pancreatic_cancer_staging_severity_4_v1
pancreatic_cancer_screening_4_v1 protein_energy_malnutrition_screening_1_v1 protein_energy_malnutrition_screening_2_v1
protein_energy_malnutrition_staging_severity_1_v1 kwashiorkor_screening_1_v1 kwashiorkor_staging_severity_1_v1
pellagra_staging_severity_1_v1 pellagra_staging_severity_2_v1 hepatic_encephalopathy_screening_2_v1
hepatic_encephalopathy_staging_severity_3_v1 celiac_disease_alt_hepatitis_screen_v1 acute_pancreatitis_alt_hepatitis_screen_v1
heart_failure_decompensated_total_cholesterol_screen_v1 urinary_tract_infection_screening_4_v1 cellulitis_screening_1_v1
community_acquired_pneumonia_screening_1_v1 peripheral_arterial_disease_screening_2_v1 peripheral_arterial_disease_staging_severity_1_v1
alcohol_use_disorder_screening_1_v1 alcohol_use_disorder_screening_2_v1 alcohol_use_disorder_staging_severity_1_v1
alcohol_use_disorder_staging_severity_3_v1 alcohol_use_disorder_staging_severity_4_v1 alcoholic_hepatitis_pattern_guideline_criterion_v1
adult_onset_still_disease_screening_1_v1 adult_onset_still_disease_staging_severity_1_v1 hypophosphatasia_screening_1_v1
carbon_monoxide_poisoning_screening_2_v1 carbon_monoxide_poisoning_staging_severity_2_v1 leigh_syndrome_screening_1_v1
melas_syndrome_screening_1_v1 melas_syndrome_diagnostic_criterion_1_v1 beriberi_staging_severity_1_v1
cerebral_malaria_screening_4_v1 cerebral_malaria_staging_severity_3_v1 chronic_pancreatitis_staging_severity_1_v1
acute_pericarditis_staging_severity_1_v1 takotsubo_cardiomyopathy_screening_1_v1 cardiorenal_syndrome_guideline_criterion_v1
medium_chain_acyl_coa_dehydrogenase_deficiency_nh3_pattern_v1 euthyroid_sick_syndrome_nontr_free_t4_low_target
diabetes_insipidus_screening_1_v1 diabetes_insipidus_screening_2_v1 renal_tubular_acidosis_screening_1_v1
copd_staging_severity_1_v1 burkitt_lymphoma_diagnostic_criterion_1_v1_f13_3 acute_chest_syndrome_diagnostic_criterion_1_v1
immune_thrombocytopenia_thrombocytopenia_bleeding_risk_v1 acute_myocardial_infarction_hs_crp_cardiovascular_risk_v1
anemia_of_chronic_disease_hb_male_anemia anemia_of_chronic_disease_transferrin_saturation_low
""".split()
# Diseases whose remaining non-core single-leaf rules on ubiquitous analytes are retired under the same class
R2A_DISEASES = {"mcardle_disease","serotonin_syndrome","pompe_disease","amyotrophic_lateral_sclerosis","tetanus","trichinellosis",
 "polymyositis","rhabdomyosarcoma","neuroleptic_malignant_syndrome","siadh","addison_disease","cystic_fibrosis","pyloric_stenosis",
 "acute_gastroenteritis","hepatic_abscess","ascending_cholangitis","acute_cholangitis","gilbert_syndrome","paget_disease",
 "gaucher_disease","necrotizing_enterocolitis","visceral_leishmaniasis","down_syndrome","galactosemia","renal_cell_carcinoma",
 "mumps","salivary_gland_tumor","pancreatic_cancer","protein_energy_malnutrition","kwashiorkor","pellagra","scurvy","beriberi",
 "hepatic_encephalopathy","celiac_disease","urinary_tract_infection","cellulitis","community_acquired_pneumonia",
 "peripheral_arterial_disease","alcohol_use_disorder","adult_onset_still_disease","hypophosphatasia","carbon_monoxide_poisoning",
 "leigh_syndrome","melas_syndrome","cerebral_malaria","chronic_pancreatitis","acute_pericarditis","takotsubo_cardiomyopathy",
 "cardiorenal_syndrome","medium_chain_acyl_coa_dehydrogenase_deficiency","diabetes_insipidus","renal_tubular_acidosis","copd",
 "burkitt_lymphoma","acute_chest_syndrome","frailty","clozapine_agranulocytosis","latent_autoimmune_diabetes","type_1_diabetes"}
UBIQUITOUS = {"creatine_kinase_total","lactate","white_blood_cell_count","c_reactive_protein","alkaline_phosphatase","albumin",
 "total_protein","sodium","potassium","chloride","bicarbonate","magnesium","phosphate","calcium_total","platelets","platelet_count",
 "thyroid_stimulating_hormone","free_thyroxine","glucose","fasting_plasma_glucose","hemoglobin_a1c","lipase","amylase",
 "alanine_aminotransferase","aspartate_aminotransferase","gamma_glutamyl_transferase","total_bilirubin","hemoglobin",
 "total_cholesterol","hdl_cholesterol","triglycerides","troponin_i","mean_corpuscular_volume","ferritin","serum_osmolality",
 "international_normalized_ratio","uric_acid","lactate_dehydrogenase","neutrophil_count_absolute","high_sensitivity_c_reactive_protein"}

# R2b - clinically incorrect (contradicts the cited or a retrieved source)
R2B = {
 "prediabetes_hba1c_pattern_diagnostic_criterion_1_v1": "A1c <6.5 % labelled 'diagnostic' of prediabetes: includes every normal value; ADA 2026 Table 2.2 defines prediabetes as A1c 5.7-6.4 %.",
 "hyperosmolar_hyperglycemic_state_fasting_glucose_diabetes": "FPG >=126 is the diabetes diagnostic threshold; HHS requires glucose >=600 mg/dL with hyperosmolality (ADA/EASD 2024).",
 "hyperosmolar_hyperglycemic_state_hba1c_diagnostic": "A1c >=6.5 % is a diabetes diagnostic criterion, not HHS.",
 "type_1_diabetes_diagnostic_criterion_1_v1": "glucose >100 and A1c >5.7 cannot discriminate type 1 from type 2 diabetes or prediabetes.",
 "type_1_diabetes_staging_severity_1_v1": "glucose >150 is not a type 1 diabetes severity criterion.",
 "type_1_diabetes_staging_severity_2_v1": "A1c >8.55 is not a type-specific criterion.",
 "type_1_diabetes_screening_2_v1": "A1c >5.7 is the prediabetes threshold, not a type 1 diabetes screen.",
 "latent_autoimmune_diabetes_screening_3_v1": "A1c >5.7 is the prediabetes threshold; LADA requires islet autoantibodies.",
 "latent_autoimmune_diabetes_staging_severity_2_v1": "A1c >8.55 is not a LADA-specific criterion.",
 "iron_deficiency_anemia_thrombocytosis_mpn_screen_v1": "platelets >=450 cites WHO myeloid classification (MPN); reactive thrombocytosis is not an IDA criterion.",
 "hemochromatosis_hereditary_hemochromatosis_thrombocytosis_mpn_screen_v1": "platelets >=450 has no relation to haemochromatosis.",
 "thalassemia_trait_beta_thalassemia_trait_thrombocytosis_mpn_screen_v1": "platelets >=450 has no relation to thalassaemia trait.",
 "thalassemia_trait_beta_thalassemia_trait_transferrin_saturation_low_v1": "BSG 2021: TSAT <20 % 'is indicative of iron restriction, particularly in thalassaemia carriers' - it indicates iron deficiency, not the trait itself.",
 "frailty_older_v2": "albumin <3.5 and Hb <12 are not frailty criteria (Fried phenotype is clinical).",
 "frailty_older_v2_f13_3": "same as frailty_older_v2 with a non-source threshold (10.67).",
 "takotsubo_cardiomyopathy_staging_severity_1_v1": "troponin >0.06 cannot stage or identify Takotsubo; source is the ESC HF/dyslipidaemia guideline.",
 "alcoholic_liver_pattern_diagnostic_criterion_1_v1": "MCV >100 alone labelled 'diagnostic' of an alcoholic liver pattern.",
 "clozapine_agranulocytosis_diagnostic_criterion_1_v1": "WBC <4 and ANC <1.8 is leukopenia/mild neutropenia; agranulocytosis is ANC <0.5 x10^9/L; cited source is a lithium teratology record.",
 "acute_kidney_injury_v1_f13_3": "same with non-source thresholds (1.1 / 1.02).",
 "copd_diagnostic_criterion_1_v1": "COPD is diagnosed by spirometry; PaO2 <60 with PaCO2 >50 is hypercapnic respiratory failure of any cause.",
 "acute_myocardial_infarction_urgent_v1": "assay-specific troponin cut-offs without rise/fall duplicate the curated myocardial-injury rule; MI is not a labs-only diagnosis.",
 "pellagra_diagnostic_criterion_1_v1_f13_3": "albumin <3.5 and Hb <11.56 do not identify pellagra; non-source threshold.",
 "pellagra_screening_2_v1_f13_3": "Hb <11.56 alone; non-source threshold; not a pellagra criterion.",
 "scurvy_diagnostic_criterion_1_v1_f13_3": "Hb <11.56 and CRP >10 do not identify scurvy.",
 "scurvy_screening_1_v1_f13_3": "Hb <11.56 alone; non-source threshold.",
}
# R2c - unsourced / duplicate thresholds (a curated or convention rule for the same entity remains)
R2C = {
 "sepsis_staging_severity_3_v1": "WBC >16.5 - no source threshold; SIRS/Sepsis-3 rules remain.",
 "sepsis_staging_severity_2_v1": "lactate >3.3 - no source threshold; Sepsis-3 lactate >2 / >=4 rules remain.",
 "sepsis_screening_2_v1": "lactate >2.2 - no source threshold.",
 "sepsis_staging_severity_4_v1": "CRP >15 - no source threshold.",
 "heart_failure_staging_severity_2_v1": "BNP >150 - no source threshold; ESC rules remain.",
 "hyperlipidemia_staging_severity_3_v1": "TG >225 - no source threshold; ATP III classes remain.",
 "hyperlipidemia_staging_severity_1_v1": "TC >300 - no source threshold.",
 "hyperlipidemia_screening_3_v1": "duplicate of hypertriglyceridemia_v1 (TG >=150).",
 "hyperlipidemia_screening_1_v1": "duplicate of hypercholesterolemia_v1 (TC >=200).",
 "hypercapnia_pattern_diagnostic_criterion_1_v1": "PaCO2 >50 - no source threshold; convention rule (>45) remains.",
 "gout_screening_1_v1": "urate >7.2 - no source threshold; ACR/EULAR 2015 scoring bands remain.",
 "gout_staging_severity_1_v1": "urate >10.8 - no source threshold; >=10 band remains.",
 "iron_deficiency_anemia_bsg_2021_ferritin_30_cur13_f13_3": "non-source Hb thresholds (11.56 / 10.67); the parent curated rule remains.",
 "iron_deficiency_anemia_v1_f13_3": "non-source Hb threshold (10.67).",
 "acute_hepatitis_dx_p131": "ALT >400 with ALP <300 - thresholds not traceable to the cited AASLD record; hepatocellular-injury pattern rule remains.",
 "heart_failure_bnp_pattern_diagnostic_criterion_1_v1": "BNP >400 labelled diagnostic; acute-HF curated rule (ESC) remains.",
 "heart_failure_bnp_pattern_screening_1_v1": "duplicate of heart_failure_screening_2_v1 (BNP >100).",
 "hypothyroidism_staging_severity_1_v1": "TSH >6.0 - no source threshold; screening (>4.0) and overt (>10 + low FT4) rules remain.",
 "elevated_hba1c_pattern_screening_1_v1": "duplicate of prediabetes_hba1c_pattern_screening_1_v1 (A1c >5.7).",
}

# R3 - re-sourcing (rule -> new source list, verified keys)
R3 = {
 "child_anemia_who_2024_v2": (["who_anaemia_2024"], ["who24_tab2"]),
 "iron_deficiency_anemia_ferritin_iron_depletion_v1": (["who_ferritin_2020"], ["who20_ferritin"]),
 "iron_deficiency_without_anemia_v1": (["who_ferritin_2020", "who_anaemia_2024"], ["who20_ferritin", "who24_tab2"]),
 "iron_deficiency_anemia_v1": (["who_ferritin_2020", "who_anaemia_2024"], ["who20_ferritin", "who24_tab2"]),
 "iron_deficiency_anemia_hb_male_anemia_v1": (["who_anaemia_2024"], ["who24_tab2"]),
 "iron_deficiency_anemia_transferrin_saturation_low_v1": (["bsg_ida_2021"], ["bsg21_tsat"]),
 "iron_deficiency_anemia_bsg_2021_ferritin_30_cur13": (["bsg_ida_2021", "who_anaemia_2024"], ["who24_tab2"]),
 "fasting_hypoglycemia_authentic_criterion_v1": (["ada_2026_s6_glycemic_goals"], ["ada26_s6_hypo"]),
 "prediabetes_v1": (["ada_2026"], ["ada26_s2_prediab"]),
 "prediabetes_ada_2025_prediabetes_range_cur13": (["ada_2026"], ["ada26_s2_prediab"]),
 "prediabetes_hba1c_pattern_screening_1_v1": (["ada_2026"], ["ada26_s2_prediab"]),
 "diabetes_ada_2024_all_ages_v2": (["ada_2026"], ["ada26_s2_dx"]),
 "type_2_diabetes_type_2_diabetes_mellitus_v1": (["ada_2026"], ["ada26_s2_dx"]),
 "type_2_diabetes_mellitus_v1": (["ada_2026"], ["ada26_s2_dx"]),
 "metabolic_acidosis_high_anion_gap_cur13": (["ada_easd_hyperglycemic_crises_2024", "reference_interval_convention"], ["adaeasd24_ag"]),
 "euglycemic_diabetic_ketoacidosis_authentic_criterion_v1": (["ada_easd_hyperglycemic_crises_2024"], ["adaeasd24_edka"]),
 "hyperosmolar_hyperglycemic_state_ada_easd_2024_hhs_cur13": (["ada_easd_hyperglycemic_crises_2024"], ["adaeasd24_hhs"]),
 "sepsis_sepsis3_lactate_2_with_infection_marker_cur13": (["sepsis3_2016"], ["sepsis3_shock"]),
 "sirs_accp_sccm_1992_2_of_4_v14": (["accp_sccm_sirs_1992", "sepsis3_2016"], ["sepsis3_sirs"]),
 "sepsis_sirs_with_laboratory_support_v14": (["sepsis3_2016", "accp_sccm_sirs_1992"], ["sepsis3_sirs", "sepsis3_shock"]),
 "familial_hypercholesterolemia_v1": (["acc_aha_cholesterol_2018"], ["aha18_ldl190"]),
 "hypercholesterolemia_v1": (["ncep_atp3_2001"], ["atp3_tab2"]),
 "hypertriglyceridemia_v1": (["ncep_atp3_2001"], ["atp3_tg"]),
 "severe_hypertriglyceridemia_v1": (["ncep_atp3_2001"], ["atp3_tg"]),
 "hyperlipidemia_diagnostic_criterion_1_v1": (["ncep_atp3_2001"], ["atp3_tab2"]),
 "atherogenic_dyslipidemia_reanchor_scre_v13_4": (["ncep_atp3_2001", "acc_aha_cholesterol_2018"], ["atp3_metsyn", "aha18_metsyn"]),
 "mixed_dyslipidemia_reanchor_scre_v13_4": (["ncep_atp3_2001"], ["atp3_tab2", "atp3_tg"]),
 "metabolic_syndrome_atp3_2005_three_of_five_lab_cur13": (["ncep_atp3_2005", "ncep_atp3_2001"], ["atp3_metsyn"]),
 "gout_acr_eular_2015_hyperuricemia_component_cur13": (["acr_eular_gout_2015"], ["gout15_urate"]),
 "gout_acr_eular_2015_urate_very_high_cur13": (["acr_eular_gout_2015"], ["gout15_urate"]),
 "masld_alt_above_acg_uln_male_with_cardiometabolic_v14": (["aasld_masld_2023", "acg_liver_chemistries_2017", "ncep_atp3_2001"], ["masld23_alt", "acg17_alt", "atp3_metsyn"]),
 "masld_alt_above_acg_uln_female_with_cardiometabolic_v14": (["aasld_masld_2023", "acg_liver_chemistries_2017", "ncep_atp3_2001"], ["masld23_alt", "acg17_alt", "atp3_metsyn"]),
 "reduced_gfr_single_panel_v14": (["kdigo_ckd_2024"], ["kdigo24_gfr"]),
 "acute_kidney_injury_v1": (["kdigo_aki_2012"], ["kdigo12_aki"]),
 "chronic_kidney_disease_kdigo_2024_albuminuria_a2_cur13": (["kdigo_ckd_2024"], ["kdigo24_acr"]),
 "albuminuria_a2_v1": (["kdigo_ckd_2024"], ["kdigo24_acr"]),
 "refeeding_endocrine_electrolyte_pattern_reanchor_scre_v13_4": (["aspen_refeeding_2020", "reference_interval_convention"], ["aspen20_rs"]),
 "tumor_lysis_pattern_screening_1_v1": (["cairo_bishop_2004"], []),
 "tumor_lysis_syndrome_cairo_bishop_laboratory_tls_cur13": (["cairo_bishop_2004"], []),
 "immune_thrombocytopenia_ash_2019_isolated_thrombocytopenia_cur13": (["rodeghiero_itp_2009", "ash_itp_2019"], []),
 "hypothyroidism_screening_1_v1": (["reference_interval_convention", "ata_hypothyroid_2012"], []),
 "hypothyroidism_diagnostic_criterion_1_v1": (["reference_interval_convention", "ata_hypothyroid_2012"], []),
 "isolated_hyperbilirubinemia_pattern_screening_1_v1": (["reference_interval_convention"], []),
 "isolated_hyperbilirubinemia_pattern_diagnostic_criterion_1_v1": (["reference_interval_convention"], []),
 "elevated_inr_pattern_diagnostic_criterion_1_v1": (["reference_interval_convention"], []),
 "hypernatremia_severe_155_cur13": (["reference_interval_convention"], []),
 "thrombocytopenia_thrombocytopenia_bleeding_risk_v1": (["reference_interval_convention"], []),
 "hyperphosphatemia_v1": (["reference_interval_convention"], []),
 "leukocytosis_pattern_screening_1_v1": (["reference_interval_convention"], []),
 "leukocytosis_pattern_diagnostic_criterion_1_v1": (["reference_interval_convention"], []),
 "neutrophilia_pattern_screening_1_v1": (["reference_interval_convention"], []),
 "neutrophilia_pattern_diagnostic_criterion_1_v1": (["reference_interval_convention"], []),
 "respiratory_acidosis_v1": (["reference_interval_convention"], []),
 "respiratory_alkalosis_v1": (["reference_interval_convention"], []),
 "metabolic_acidosis_v1": (["reference_interval_convention"], []),
 "metabolic_alkalosis_v1": (["reference_interval_convention"], []),
 "hypercapnia_pattern_screening_1_v1": (["reference_interval_convention"], []),
}
# R4 - 'endocrine_guidelines' collection page -> convention (+ topical locator)
R4_TOPICAL = {"hyponatremia_v1": "ese_hyponatremia_2014", "severe_hyponatremia_v1": "ese_hyponatremia_2014",
 "hyperkalemia_v1": "kdigo_potassium_2020", "severe_hyperkalemia_v1": "kdigo_potassium_2020",
 "hypokalemia_v1": "kdigo_potassium_2020", "severe_hypokalemia_v1": "kdigo_potassium_2020"}

# R5 - logic corrections (closed list)
def r5(rules, log):
    def note(rid, text, keys):
        r = rules[rid]; r["curation_note"] = f"15.0.0 R5: {text}"; r["curated_on"] = TODAY; r["curation_version"] = VER
        prov = r.setdefault("provenance", {})
        if keys:
            prov["verified_quote"] = [VERIFIED[k][2] for k in keys]
            prov["verified_locator"] = [VERIFIED[k][1] for k in keys]; prov["verified_on"] = TODAY
        log.append(rid)
    r = rules["child_anemia_who_2024_v2"]
    r["population"]["age_groups"] = ["child"]; r["expression"]["value"] = 11.5
    r["title"] = "Anaemia, children 5-11 years (WHO 2024, Hb <115 g/L)"
    note("child_anemia_who_2024_v2", "population restricted to 'child' (engine 6-<12 y; 1-5 y fall back to this group, WHO cut-off there is 110 g/L - documented 0.5 g/dL over-sensitivity). Previously applied Hb <11.5 to all ages and sexes, including men (WHO <130).", ["who24_tab2"])
    r = rules["iron_deficiency_anemia_v1"]  # sex male, Hb<12 -> WHO men <130
    assert r["population"]["sex"] == "male" and r["expression"]["all"][0]["feature_id"] == "hemoglobin"
    r["expression"]["all"][0]["value"] = 13.0
    note("iron_deficiency_anemia_v1", "male rule used the female cut-off (Hb <12.0); WHO 2024 men <130 g/L.", ["who24_tab2", "who20_ferritin"])
    r = rules["prediabetes_hba1c_pattern_screening_1_v1"]; r["expression"]["operator"] = ">="
    note("prediabetes_hba1c_pattern_screening_1_v1", "A1c >5.7 -> >=5.7 (ADA range 5.7-6.4 % is inclusive).", ["ada26_s2_prediab"])
    r = rules["fasting_hypoglycemia_authentic_criterion_v1"]; r["expression"]["value"] = 54.0
    r["title"] = "Clinically significant hypoglycaemia (ADA level 2, glucose <54 mg/dL)"
    note("fasting_hypoglycemia_authentic_criterion_v1", "threshold 55 -> 54 mg/dL (ADA level 2; 55 is not an ADA threshold).", ["ada26_s6_hypo"])
    r = rules["rhabdomyolysis_ck_5x_uln_diagnostic_cur13"]; r["expression"]["operator"] = ">"
    note("rhabdomyolysis_ck_5x_uln_diagnostic_cur13", "CK >=1000 -> >1000 U/L, matching the source wording (CK >5x ULN or >1000 U/L).", [])
    r = rules["euglycemic_diabetic_ketoacidosis_authentic_criterion_v1"]
    r["expression"]["all"].append({"feature_id": "beta_hydroxybutyrate", "operator": ">=", "value": 3.0, "unit": "mmol/L", "weight": 1.0})
    note("euglycemic_diabetic_ketoacidosis_authentic_criterion_v1", "ketosis leaf added (beta-hydroxybutyrate >=3.0 mmol/L); the previous expression (bicarbonate <18 and glucose <200) fired on any non-ketotic acidosis with normal glucose.", ["adaeasd24_edka"])
    r = rules["hyponatremia_v1"]; r["curation_note"] = "15.0.0 R4: sodium <135 is the conventional lower reference limit; ESE 2014 locator attached (threshold text not retrieved)."

def is_single_leaf(e):
    return isinstance(e, dict) and "feature_id" in e

def set_sources(r, sids):
    r["source_ids"] = list(sids); r.setdefault("provenance", {})["source_ids"] = list(sids); r["provenance"]["resourced_in"] = VER

def retire(r, status, reason, cls):
    r["status"] = status; r["executable"] = False; r["retired_reason"] = f"v{VER} {cls}: {reason}"
    r["curated_on"] = TODAY; r["curation_version"] = VER

def patch(d):
    rules = d["rules"]; src = d["guideline_sources"]; log = collections.defaultdict(list)
    for sid, rec in NEW_SOURCES.items():
        if sid not in src: src[sid] = {"id": sid, **rec}; log["sources_added"].append(sid)
    for sid, upd in REPAIR_SOURCES.items():
        if sid in src: src[sid].update(upd); log["sources_repaired"].append(sid)
    for sid, doi in LOCATOR_ONLY.items():
        if sid in src and not src[sid].get("doi"): src[sid]["doi"] = doi
    # R1
    for rid, r in rules.items():
        if rid.startswith("co_") and r["disease_id"].startswith("co_") and (r.get("source_ids") or [None])[0] == "who_essential_lab_2024":
            set_sources(r, ["generated_pair_pattern"]); r["evidence_tier"] = "generated_template"
            r["curation_note"] = "15.0.0 R1: template-generated co-abnormality pattern; no guideline provenance."
            log["R1"].append(rid)
    # R2a explicit + disease extension
    for rid in R2A_IDS:
        r = rules.get(rid)
        if r and r.get("executable"):
            retire(r, "retired_v15_0_0_nonspecific_single_marker", "single ubiquitous analyte voting for a specific entity; the cited source does not define the entity by this analyte.", "R2a"); log["R2a"].append(rid)
    for rid, why in R2B.items():
        r = rules.get(rid)
        if r and r.get("executable"): retire(r, "retired_v15_0_0_clinically_incorrect", why, "R2b"); log["R2b"].append(rid)
    for rid, why in R2C.items():
        r = rules.get(rid)
        if r and r.get("executable"): retire(r, "retired_v15_0_0_unsourced_threshold", why, "R2c"); log["R2c"].append(rid)
    for rid, r in rules.items():
        if rid.startswith("co_") or not r.get("executable") or r["disease_id"] not in R2A_DISEASES: continue
        if r.get("rule_type") == "exclusion_criterion": continue
        e = r.get("expression") or {}
        leaves = [e] if is_single_leaf(e) else [c for c in (e.get("all") or e.get("any") or []) if is_single_leaf(c)]
        if leaves and all(l["feature_id"] in UBIQUITOUS for l in leaves) and len(leaves) <= 2 and not r["status"].startswith("curated"):
            retire(r, "retired_v15_0_0_nonspecific_single_marker", "same class as the core R2a rules of this entity (ubiquitous analyte(s) only).", "R2a-ext"); log["R2a_ext"].append(rid)
    # R3 / R4
    for rid, (sids, keys) in R3.items():
        r = rules.get(rid)
        if not r: log["missing"].append(rid); continue
        set_sources(r, sids); prov = r["provenance"]
        if keys:
            prov["verified_quote"] = [VERIFIED[k][2] for k in keys]; prov["verified_locator"] = [VERIFIED[k][1] for k in keys]
            prov["verified_on"] = TODAY; r["evidence_tier"] = "tier_a_text_verified"; log["R3_verified"].append(rid)
        else:
            prov["verification"] = "locator_only__threshold_text_not_retrieved" if sids[0] != "reference_interval_convention" else "reference_interval_convention"
            log["R3_locator_only" if sids[0] != "reference_interval_convention" else "R4"].append(rid)
        r["curated_on"] = TODAY; r["curation_version"] = VER
        r.setdefault("curation_note", ""); r["curation_note"] = (r["curation_note"] + " | " if r["curation_note"] else "") + f"15.0.0 R3/R4: sources -> {sids}"
    for rid, r in rules.items():
        if r.get("executable") and r.get("source_ids") == ["endocrine_guidelines"] and not rid.startswith("co_"):
            sids = ["reference_interval_convention"] + ([R4_TOPICAL[rid]] if rid in R4_TOPICAL else [])
            set_sources(r, sids); r["provenance"]["verification"] = "reference_interval_convention"
            r["curation_note"] = f"15.0.0 R4: 'endocrine_guidelines' (collection page, no threshold) -> {sids}"; r["curated_on"] = TODAY; r["curation_version"] = VER
            log["R4"].append(rid)
    aki = rules["acute_kidney_injury_v1"]; aki["evidence_tier"] = "single_panel_surrogate"
    aki["curation_note"] = ("15.0.0 R3 (protocol deviation, recorded): KDIGO 2012 defines AKI by creatinine CHANGE; this fixed-threshold rule is a single-panel "
        "surrogate that the engine grades as 'chronicity undetermined' with a probability cap. Planned retirement (R2b) was reversed because the test gate "
        "showed the ESL layer depends on it (6 regressions, e.g. creatinine 4.4 mg/dL + BUN 71 + K 5.9 no longer ranked). Its sibling with non-source thresholds (_f13_3) is retired.")
    r5(rules, log["R5"])
    # metadata
    m = d["registry_metadata"]; m["version"] = f"{VER}-CLINICAL-CURATED"; m["last_updated"] = TODAY
    m["executable_rules"] = sum(1 for r in rules.values() if r.get("executable"))
    m["retired_rules"] = sum(1 for r in rules.values() if str(r.get("status", "")).startswith("retired"))
    m["total_sources"] = m["total_guideline_sources"] = len(src)
    m["evidence_tier_counts"] = dict(collections.Counter(r.get("evidence_tier") for r in rules.values()))
    m["changelog"] = [c for c in m.get("changelog", []) if c.get("version") != VER]
    m["changelog"].append({"version": VER, "date": TODAY, "protocol": "eval/registry_patches/PROTOCOL_15_0_0.md",
        "change": (f"Provenance/fidelity release. R1 {len(log['R1'])} template rules re-attributed to 'generated_pair_pattern'; "
                   f"retired: R2a {len(log['R2a'])}+{len(log['R2a_ext'])} nonspecific single-marker, R2b {len(log['R2b'])} clinically incorrect, R2c {len(log['R2c'])} unsourced/duplicate thresholds; "
                   f"R3 {len(log['R3_verified'])} rules with text-verified quotes, {len(log['R3_locator_only'])} locator-only; R4 {len(log['R4'])} reference-limit rules re-attributed; "
                   f"R5 {len(log['R5'])} logic corrections (child anaemia age gate, male IDA Hb 13, prediabetes >=5.7, hypoglycaemia <54, rhabdomyolysis >1000, euglycaemic DKA ketone leaf); "
                   f"R6 {len(log['sources_repaired'])} source records repaired, {len(log['sources_added'])} added. Executable rules {m['executable_rules']}.")})
    return log

def write(d, path):
    raw = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
    open(path, "wb").write(brotli.compress(raw, quality=11)); return hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    src_path = f"{ROOT}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
    d = json.loads(brotli.decompress(open(src_path, "rb").read()))
    assert d["registry_metadata"]["version"].startswith("14.2.0"), d["registry_metadata"]["version"]
    log = patch(d)
    d["registry_metadata"]["sha256_uncompressed"] = None
    sha = write(d, src_path)
    d["registry_metadata"]["sha256_uncompressed"] = sha
    for f in ["HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"]:
        write(d, f"{ROOT}/{f}")
        for extra in (f"{ROOT}/tools/{f}",):
            if os.path.exists(extra): shutil.copy2(f"{ROOT}/{f}", extra)
    rel = f"{ROOT}/release/registry_{VER}"; os.makedirs(rel, exist_ok=True)
    shutil.copy2(src_path, f"{rel}/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    if not os.path.lexists(f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br"):
        os.symlink("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", f"{rel}/HEMOGLYPH_GUIDELINE_REGISTRY.json.br")
    h = hashlib.sha256(open(src_path, "rb").read()).hexdigest()
    open(f"{rel}/SHA256SUMS.txt", "w").write(f"{h}  HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br\n")
    summary = {k: (len(v) if k not in ("R5", "missing", "sources_added", "sources_repaired") else v) for k, v in log.items()}
    summary["rule_ids"] = {k: v for k, v in log.items()}
    json.dump(summary, open(f"{ROOT}/eval/registry_patches/review_15_0_0.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "rule_ids"}, indent=1))
