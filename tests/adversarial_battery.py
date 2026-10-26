"""Hemoglyph ADVERSARIAL battery — false-positive pressure on the Expert
Syndrome Layer and the fusion.

HONEST SCOPE: developer-authored near-miss / mimic / unit-twin cases. This
measures *restraint*, the complement of the HARD battery's recall. It is not
a clinical validation.

Four case kinds:
  NEG   : the named syndrome must NOT appear in expert_syndromes AND the named
          disease ids must not be ranked #1 with state 'supported'.
  SI    : an SI-unit twin of a conventional-unit case; top-1 id must match and
          |delta p| <= 0.05.
  POS   : sanity anchor — syndrome must fire (so NEG failures are not just a
          dead layer).
  NOCRASH: malformed / partial input must return a report.

Usage: python tests/adversarial_battery.py [--verbose] [--only SUBSTR]
"""
from __future__ import annotations
import os, sys, time, argparse, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)

M45 = {"age_years": 45, "sex_at_birth": "male"}
F38 = {"age_years": 38, "sex_at_birth": "female"}
M70 = {"age_years": 70, "sex_at_birth": "male"}
F26 = {"age_years": 26, "sex_at_birth": "female"}
CH6 = {"age_years": 6, "sex_at_birth": "male"}
PREG = {"age_years": 30, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 30}

def U(**kw): return kw

# (name, kind, obs, patient, syndromes_forbidden_or_required, dx_ids_watch)
CASES = [
 # ---------------- NEG: near-miss thresholds ---------------------------------
 ("NEG DKA: glucose 240 + BHB 2.9 (both just under)", "NEG",
  U(glucose=(240,"mg/dL"), beta_hydroxybutyrate=(2.9,"mmol/L"), bicarbonate=(21,"mmol/L"), sodium=(139,"mmol/L"), chloride=(104,"mmol/L")),
  M45, ["dka","euglycemic_dka","aka"], ["diabetic_ketoacidosis"]),
 ("NEG HHS: glucose 580 + osm 318", "NEG",
  U(glucose=(580,"mg/dL"), serum_osmolality=(318,"mOsm/kg"), sodium=(141,"mmol/L"), bicarbonate=(22,"mmol/L")),
  M70, ["hhs","dka"], ["hyperosmolar_hyperglycemic_state"]),
 ("NEG toxic alcohol: AG 15, osm gap 18", "NEG",
  U(anion_gap=(15,"mmol/L"), osmolal_gap=(18,"mOsm/kg"), bicarbonate=(17,"mmol/L"), sodium=(140,"mmol/L"), chloride=(108,"mmol/L"), glucose=(95,"mg/dL")),
  M45, ["toxic_alcohol"], ["ethylene_glycol_poisoning","methanol_poisoning","toxic_alcohol_ingestion"]),
 ("NEG lactic acidosis: lactate 3.9", "NEG",
  U(lactate=(3.9,"mmol/L"), bicarbonate=(21,"mmol/L"), white_blood_cell_count=(9,"10^9/L"), c_reactive_protein=(8,"mg/L")),
  M45, ["lactic_acidosis_sepsis","sepsis_bacterial"], ["sepsis","septic_shock_severe_lactic_acidosis"]),
 ("NEG TLS: urate 7.9 / phos 4.4 / K 5.9", "NEG",
  U(uric_acid=(7.9,"mg/dL"), phosphate=(4.4,"mg/dL"), potassium=(5.9,"mmol/L"), creatinine=(1.0,"mg/dL"), lactate_dehydrogenase=(240,"U/L")),
  M45, ["tls"], ["tumor_lysis_syndrome"]),
 ("NEG prerenal: Cr 1.3 (not >) + BUN/Cr 25", "NEG",
  U(creatinine=(1.3,"mg/dL"), blood_urea_nitrogen=(32,"mg/dL"), sodium=(140,"mmol/L")),
  M70, ["prerenal","atn"], []),
 ("NEG thyroid storm: TSH 0.12, FT4 3.9", "NEG",
  U(thyroid_stimulating_hormone=(0.12,"mIU/L"), free_thyroxine=(3.9,"ng/dL"), total_bilirubin=(0.8,"mg/dL"), white_blood_cell_count=(8,"10^9/L")),
  F38, ["thyroid_storm","graves","painless_thyroiditis"], ["thyroid_storm"]),
 ("NEG myxedema: TSH 29, FT4 0.55", "NEG",
  U(thyroid_stimulating_hormone=(29,"mIU/L"), free_thyroxine=(0.55,"ng/dL"), sodium=(134,"mmol/L")),
  F38, ["myxedema"], ["myxedema_coma"]),
 ("NEG Addison: AM cortisol 5.2", "NEG",
  U(cortisol_morning=(5.2,"ug/dL"), sodium=(137,"mmol/L"), potassium=(4.6,"mmol/L")),
  F38, ["addison","secondary_ai"], ["adrenal_insufficiency_primary","addison_disease","adrenal_insufficiency"]),
 ("NEG PHPT: corrected Ca 10.4, PTH 70", "NEG",
  U(calcium_total=(10.4,"mg/dL"), albumin=(4.0,"g/dL"), parathyroid_hormone=(70,"pg/mL"), creatinine=(0.9,"mg/dL")),
  F38, ["phpt","hhm"], ["primary_hyperparathyroidism"]),
 ("NEG prolactinoma: PRL 95 on hypothyroid", "NEG",
  U(prolactin=(95,"ng/mL"), thyroid_stimulating_hormone=(14,"mIU/L"), free_thyroxine=(0.7,"ng/dL")),
  F26, ["prolactinoma"], ["prolactinoma","hyperprolactinemia_prolactinoma"]),
 ("NEG insulinoma: glucose 56", "NEG",
  U(glucose=(56,"mg/dL"), insulin=(8,"uIU/mL"), c_peptide=(1.2,"ng/mL")),
  F38, ["insulinoma","factitious_insulin"], ["insulinoma"]),
 ("NEG ALF: ALT 980, INR 1.45", "NEG",
  U(alanine_aminotransferase=(980,"U/L"), aspartate_aminotransferase=(700,"U/L"), international_normalized_ratio=(1.45,"1"), total_bilirubin=(2.0,"mg/dL")),
  M45, ["alf_generic","apap_alf","ischemic_hepatitis"], ["acute_liver_failure"]),
 ("NEG HCC: AFP 380 on cirrhosis", "NEG",
  U(alpha_fetoprotein=(380,"ng/mL"), platelets=(90,"10^9/L"), albumin=(3.1,"g/dL"), total_bilirubin=(1.8,"mg/dL"), international_normalized_ratio=(1.3,"1")),
  M70, ["hcc"], []),
 ("NEG HH: TSAT 44, ferritin 290", "NEG",
  U(transferrin_saturation=(44,"%"), ferritin=(290,"ng/mL"), alanine_aminotransferase=(30,"U/L")),
  M45, ["hh"], ["hereditary_hemochromatosis"]),
 ("NEG PBC: ALP 175 + AMA 18", "NEG",
  U(alkaline_phosphatase=(175,"U/L"), anti_mitochondrial_antibody_m2=(18,"U/mL"), gamma_glutamyl_transferase=(70,"U/L")),
  F38, ["pbc","psc","cholangitis"], ["primary_biliary_cholangitis"]),
 ("NEG TTP: plt 32 + schisto 1%", "NEG",
  U(platelets=(32,"10^9/L"), schistocytes_percent=(1,"%"), hemoglobin=(11,"g/dL"), lactate_dehydrogenase=(300,"U/L"), creatinine=(1.0,"mg/dL")),
  F38, ["ttp","hus"], ["thrombotic_thrombocytopenic_purpura"]),
 ("NEG DIC: plt 110, D-dimer 1.9, fib 155", "NEG",
  U(platelets=(110,"10^9/L"), d_dimer=(1.9,"ug/mL"), fibrinogen=(155,"mg/dL"), international_normalized_ratio=(1.2,"1")),
  M45, ["dic"], ["disseminated_intravascular_coagulation"]),
 ("NEG aplastic: ANC 0.6, plt 25, Hb 10.5", "NEG",
  U(absolute_neutrophil_count=(0.6,"10^9/L"), platelets=(25,"10^9/L"), hemoglobin=(10.5,"g/dL"), reticulocyte_percent=(1.2,"%")),
  F26, ["aplastic"], ["aplastic_anemia"]),
 ("NEG AML: blasts 19%", "NEG",
  U(blasts_percent=(19,"%"), white_blood_cell_count=(30,"10^9/L"), hemoglobin=(9,"g/dL"), platelets=(60,"10^9/L")),
  M45, ["aml","all","apl"], []),
 ("NEG PV: Hb 16.4 + JAK2 neg", "NEG",
  U(hemoglobin=(16.4,"g/dL"), hematocrit=(48,"%"), jak2_v617f_mutation=(0,"1"), erythropoietin=(12,"mIU/mL")),
  M45, ["pv","secondary_polycythemia"], ["polycythemia_vera"]),
 ("NEG myeloma: M-spike 2.9", "NEG",
  U(serum_m_protein=(2.9,"g/dL"), hemoglobin=(13,"g/dL"), calcium_total=(9.4,"mg/dL"), creatinine=(0.9,"mg/dL"), free_light_chain_ratio=(5,"1")),
  M70, ["myeloma","lc_myeloma"], ["multiple_myeloma"]),
 ("NEG HLH: ferritin 480", "NEG",
  U(ferritin=(480,"ng/mL"), triglycerides=(280,"mg/dL"), fibrinogen=(140,"mg/dL"), hemoglobin=(8.5,"g/dL"), platelets=(80,"10^9/L")),
  CH6, ["hlh"], ["hemophagocytic_lymphohistiocytosis"]),
 ("NEG MI: hs-cTn 99 ng/L", "NEG",
  U(high_sensitivity_troponin_i=(99,"ng/L"), creatine_kinase_total=(180,"U/L")),
  M70, ["mi"], ["acute_myocardial_infarction","myocardial_infarction"]),
 ("NEG FH: LDL 189", "NEG",
  U(ldl_cholesterol_calculated=(189,"mg/dL"), total_cholesterol=(270,"mg/dL"), triglycerides=(120,"mg/dL"), thyroid_stimulating_hormone=(2,"mIU/L")),
  M45, ["fh"], ["familial_hypercholesterolemia"]),
 ("NEG MTC: calcitonin 99", "NEG",
  U(calcitonin=(99,"pg/mL"), carcinoembryonic_antigen=(4,"ng/mL"), calcium_total=(9.5,"mg/dL")),
  M45, ["mtc_men2"], ["thyroid_cancer_medullary"]),
 ("NEG pheo: normetanephrine 2.6, metanephrine 1.4", "NEG",
  U(plasma_normetanephrine=(2.6,"nmol/L"), plasma_metanephrine=(1.4,"nmol/L")),
  M45, ["pheo"], ["pheochromocytoma"]),
 ("NEG Cushing: DST cortisol 1.7", "NEG",
  U(cortisol_after_dexamethasone=(1.7,"ug/dL"), potassium=(4.0,"mmol/L"), glucose=(98,"mg/dL")),
  F38, ["cushing","cushing_ufc"], ["cushing_syndrome"]),
 ("NEG CO: COHb 9.5", "NEG",
  U(carboxyhemoglobin_fraction=(9.5,"%"), lactate=(1.8,"mmol/L")),
  M45, ["co_poisoning"], ["carbon_monoxide_poisoning"]),
 ("NEG GDM: 1h 179 / 2h 152", "NEG",
  U(glucose_1_hour_ogtt=(179,"mg/dL"), glucose_2_hour_ogtt=(152,"mg/dL"), glucose=(90,"mg/dL")),
  PREG, ["gdm"], ["gestational_diabetes","gestational_diabetes_mellitus"]),
 ("NEG SIADH: hyponatraemia with high BUN/Cr (hypovolaemic)", "NEG",
  U(sodium=(126,"mmol/L"), serum_osmolality=(262,"mOsm/kg"), urine_osmolality=(480,"mOsm/kg"), urine_sodium=(45,"mmol/L"), blood_urea_nitrogen=(38,"mg/dL"), creatinine=(1.2,"mg/dL"), potassium=(4.1,"mmol/L")),
  M70, ["siadh"], ["siadh","syndrome_of_inappropriate_antidiuretic_hormone"]),
 ("NEG SIADH: hyponatraemia + K 5.6 (adrenal must be excluded)", "NEG",
  U(sodium=(128,"mmol/L"), serum_osmolality=(265,"mOsm/kg"), urine_osmolality=(400,"mOsm/kg"), urine_sodium=(60,"mmol/L"), potassium=(5.6,"mmol/L")),
  F38, ["siadh"], ["siadh"]),
 ("NEG HELLP: non-pregnant TMA picture must not be HELLP", "NEG",
  U(platelets=(58,"10^9/L"), aspartate_aminotransferase=(410,"U/L"), alanine_aminotransferase=(360,"U/L"), lactate_dehydrogenase=(1500,"U/L"),
    total_bilirubin=(2.1,"mg/dL"), serum_haptoglobin=(8,"mg/dL"), schistocytes_percent=(2,"%"), creatinine=(1.3,"mg/dL")),
  M45, ["hellp","preeclampsia_lab"], ["hellp_syndrome","preeclampsia"]),
 ("NEG PCOS in a male: testosterone 60 ng/dL", "NEG",
  U(testosterone_total=(60,"ng/dL"), luteinizing_hormone=(9,"IU/L"), follicle_stimulating_hormone=(5,"IU/L")),
  M45, ["pcos"], ["polycystic_ovary_syndrome"]),
 ("NEG Klinefelter in a 60-year-old", "NEG",
  U(testosterone_total=(250,"ng/dL"), follicle_stimulating_hormone=(24,"IU/L"), luteinizing_hormone=(12,"IU/L")),
  {"age_years": 60, "sex_at_birth": "male"}, ["klinefelter_young"], ["klinefelter_syndrome"]),
 ("NEG POI in a 45-year-old (menopause)", "NEG",
  U(follicle_stimulating_hormone=(60,"IU/L"), estradiol=(12,"pg/mL")),
  {"age_years": 45, "sex_at_birth": "female"}, ["poi"], ["premature_ovarian_insufficiency"]),
 ("NEG Wilson at 60: ceruloplasmin 18", "NEG",
  U(ceruloplasmin=(18,"mg/dL"), alanine_aminotransferase=(55,"U/L")),
  {"age_years": 60, "sex_at_birth": "male"}, ["wilson"], ["wilson_disease"]),
 ("NEG Kawasaki in adult: CRP 80 ESR 60", "NEG",
  U(c_reactive_protein=(80,"mg/L"), erythrocyte_sedimentation_rate=(60,"mm/h"), platelets=(520,"10^9/L"), albumin=(3.0,"g/dL")),
  M45, ["kawasaki"], ["kawasaki_disease"]),
 ("NEG IM at 55: atypical lymphocytes 15%", "NEG",
  U(atypical_lymphocytes_percent=(15,"%"), white_blood_cell_count=(14,"10^9/L"), alanine_aminotransferase=(90,"U/L")),
  {"age_years": 55, "sex_at_birth": "male"}, ["imn"], ["infectious_mononucleosis"]),
 ("NEG MDS at 30: macrocytic anaemia", "NEG",
  U(hemoglobin=(10,"g/dL"), mean_corpuscular_volume=(104,"fL"), platelets=(120,"10^9/L"), vitamin_b12=(450,"pg/mL")),
  {"age_years": 30, "sex_at_birth": "female"}, ["mds"], ["myelodysplastic_syndrome"]),
 ("NEG MDS: macrocytosis with B12 150 (deficiency, not MDS)", "NEG",
  U(hemoglobin=(10,"g/dL"), mean_corpuscular_volume=(108,"fL"), platelets=(130,"10^9/L"), vitamin_b12=(150,"pg/mL")),
  M70, ["mds"], ["myelodysplastic_syndrome"]),
 ("NEG ITP: thrombocytopenia with schistocytes", "NEG",
  U(platelets=(40,"10^9/L"), hemoglobin=(13,"g/dL"), white_blood_cell_count=(7,"10^9/L"), schistocytes_percent=(3,"%")),
  F38, ["itp"], ["immune_thrombocytopenia"]),
 ("NEG ET: thrombocytosis with ferritin 10 (iron deficiency)", "NEG",
  U(platelets=(620,"10^9/L"), ferritin=(10,"ng/mL"), hemoglobin=(10.5,"g/dL"), mean_corpuscular_volume=(72,"fL")),
  F38, ["et"], ["essential_thrombocythemia"]),
 ("NEG ET: thrombocytosis with CRP 120 (reactive)", "NEG",
  U(platelets=(700,"10^9/L"), c_reactive_protein=(120,"mg/L"), hemoglobin=(12.5,"g/dL")),
  M45, ["et"], ["essential_thrombocythemia"]),
 ("NEG LADA: GAD+ A1c 7 but BHB 4 (that is DKA/T1)", "NEG",
  U(glutamic_acid_decarboxylase_antibody=(40,"IU/mL"), hemoglobin_a1c=(7.0,"%"), beta_hydroxybutyrate=(4,"mmol/L"), glucose=(420,"mg/dL")),
  M45, ["lada"], []),
 ("NEG T2DM: A1c 6.5 in pregnancy (exclusion)", "NEG",
  U(hemoglobin_a1c=(6.5,"%"), glucose=(110,"mg/dL")),
  PREG, ["t2dm","prediabetes"], ["type_2_diabetes"]),
 ("NEG hemolysis: LDH/hapto with B12 120 (ineffective erythropoiesis)", "NEG",
  U(hemoglobin=(8,"g/dL"), lactate_dehydrogenase=(1800,"U/L"), serum_haptoglobin=(10,"mg/dL"), vitamin_b12=(120,"pg/mL"), mean_corpuscular_volume=(112,"fL")),
  M70, ["hemolysis_generic","waiha"], ["hemolytic_anemia"]),
 ("NEG paget: ALP 250 but GGT 150 (hepatic)", "NEG",
  U(alkaline_phosphatase=(250,"U/L"), gamma_glutamyl_transferase=(150,"U/L"), calcium_total=(9.4,"mg/dL")),
  M70, ["paget"], ["paget_disease_of_bone"]),
 ("NEG vitK: INR 1.8 with ALT 450 (hepatic)", "NEG",
  U(international_normalized_ratio=(1.8,"1"), fibrinogen=(260,"mg/dL"), platelets=(220,"10^9/L"), alanine_aminotransferase=(450,"U/L")),
  M45, ["vitk_def"], ["vitamin_k_deficiency"]),
 ("NEG sarcoid: ACE 90 with IGRA+", "NEG",
  U(angiotensin_converting_enzyme=(90,"U/L"), interferon_gamma_release_assay=(1,"1"), calcium_total=(10.1,"mg/dL")),
  M45, ["sarcoid_generic"], ["sarcoidosis"]),
 ("NEG GCA: ESR 70 with WBC 18 / PCT 1.2", "NEG",
  U(erythrocyte_sedimentation_rate=(70,"mm/h"), c_reactive_protein=(90,"mg/L"), white_blood_cell_count=(18,"10^9/L"), procalcitonin=(1.2,"ng/mL"), hemoglobin=(11,"g/dL")),
  M70, ["gca_pmr"], ["giant_cell_arteritis"]),
 ("NEG PE: D-dimer 0.6 + pO2 74 only", "NEG",
  U(d_dimer=(0.6,"ug/mL"), arterial_po2=(74,"mm[Hg]")),
  M45, ["pe"], ["pulmonary_embolism"]),
 ("NEG nephrotic: albumin 2.8 with FLC ratio 40 (myeloma)", "NEG",
  U(albumin=(2.8,"g/dL"), urine_protein_to_creatinine_ratio=(4,"g/g"), free_light_chain_ratio=(40,"1"), creatinine=(2.2,"mg/dL")),
  M70, ["nephrotic"], ["nephrotic_syndrome"]),
 ("NEG hypopara: Ca 7.9 PTH 10 with Mg 0.9", "NEG",
  U(calcium_total=(7.9,"mg/dL"), albumin=(4.0,"g/dL"), parathyroid_hormone=(10,"pg/mL"), magnesium=(0.9,"mg/dL")),
  M45, ["hypopara"], ["hypoparathyroidism"]),
 ("NEG refeeding: phos 1.6 with PTH 120 / Ca 11.2", "NEG",
  U(phosphate=(1.6,"mg/dL"), parathyroid_hormone=(120,"pg/mL"), calcium_total=(11.2,"mg/dL"), albumin=(4.0,"g/dL")),
  F38, ["refeeding"], ["refeeding_syndrome"]),

 # ---------------- NEG: single isolated abnormality must not trigger a syndrome -
 ("ISO ferritin 600 alone", "NEG", U(ferritin=(600,"ng/mL")), M45, ["hlh","hh","aosd"], ["hemophagocytic_lymphohistiocytosis","adult_onset_still_disease"]),
 ("ISO platelets 140 alone", "NEG", U(platelets=(140,"10^9/L")), M45, ["hit","itp","dic","ttp"], ["heparin_induced_thrombocytopenia"]),
 ("ISO albumin 2.9 alone", "NEG", U(albumin=(2.9,"g/dL")), M45, ["nephrotic","sam_child"], ["nephrotic_syndrome"]),
 ("ISO CK 5500 alone", "NEG", U(creatine_kinase_total=(5500,"U/L")), M45, ["rhabdo"], []),
 ("ISO eGFR 28 alone", "NEG", U(estimated_gfr=(28,"mL/min/1.73m2")), M70, ["ckd_advanced","ckd_anemia"], []),
 ("ISO TSH 0.3 alone", "NEG", U(thyroid_stimulating_hormone=(0.3,"mIU/L")), F38, ["subclin_hyperthyroid","graves","thyroid_storm","thyrotox_overt"], ["thyroid_storm","graves_disease"]),
 ("ISO Hb 16.8 male alone", "NEG", U(hemoglobin=(16.8,"g/dL")), M45, ["pv","secondary_polycythemia"], ["polycythemia_vera"]),
 ("ISO ANA 1:160 alone", "NEG", U(antinuclear_antibody_titer=(160,"{titer}")), F38, ["sle","sjogren","lupus_nephritis"], ["systemic_lupus_erythematosus"]),
 ("ISO ESR 55 at 60 alone", "NEG", U(erythrocyte_sedimentation_rate=(55,"mm/h")), {"age_years":60,"sex_at_birth":"female"}, ["gca_pmr"], ["giant_cell_arteritis","polymyalgia_rheumatica"]),
 ("ISO PCT 2.5 alone", "NEG", U(procalcitonin=(2.5,"ng/mL")), M45, ["sepsis_bacterial"], []),
 ("ISO IGRA positive alone", "NEG", U(interferon_gamma_release_assay=(1,"1")), M45, ["tb_disseminated"], ["disseminated_tuberculosis"]),
 ("ISO ALP 210 at 50 alone", "NEG", U(alkaline_phosphatase=(210,"U/L")), {"age_years":50,"sex_at_birth":"male"}, ["paget","psc","pbc"], ["paget_disease_of_bone"]),

 # ---------------- NEG: key analyte missing ------------------------------------
 ("MISSING DKA without ketones (only hyperglycaemia + low HCO3)", "NEG",
  U(glucose=(420,"mg/dL"), bicarbonate=(12,"mmol/L"), anion_gap=(26,"mmol/L"), sodium=(136,"mmol/L"), chloride=(98,"mmol/L")),
  M45, ["dka","euglycemic_dka","aka"], []),
 ("MISSING TTP without a smear (plt 15, LDH 1200)", "NEG",
  U(platelets=(15,"10^9/L"), lactate_dehydrogenase=(1200,"U/L"), hemoglobin=(7.8,"g/dL"), creatinine=(1.1,"mg/dL")),
  F38, ["ttp","hus"], []),
 ("MISSING PHPT without PTH (Ca 11.6 alone)", "NEG",
  U(calcium_total=(11.6,"mg/dL"), albumin=(4.1,"g/dL")),
  F38, ["phpt","hhm","granulomatous_hyperca","calcium_alkali"], []),
 ("MISSING cholangitis without bilirubin fraction", "NEG",
  U(alkaline_phosphatase=(400,"U/L"), total_bilirubin=(4,"mg/dL"), white_blood_cell_count=(17,"10^9/L")),
  M70, ["cholangitis","choledocholithiasis"], []),

 # ---------------- POS anchors (layer alive) -----------------------------------
 ("POS DKA", "POS", U(glucose=(480,"mg/dL"), beta_hydroxybutyrate=(6,"mmol/L"), bicarbonate=(10,"mmol/L"), anion_gap=(28,"mmol/L"), sodium=(136,"mmol/L"), chloride=(98,"mmol/L")), M45, ["dka"], ["diabetic_ketoacidosis"]),
 ("POS thyroid storm", "POS", U(thyroid_stimulating_hormone=(0.01,"mIU/L"), free_thyroxine=(6.2,"ng/dL"), total_bilirubin=(2.0,"mg/dL"), white_blood_cell_count=(14,"10^9/L"), alanine_aminotransferase=(90,"U/L")), F38, ["thyroid_storm"], ["thyroid_storm"]),
 ("POS TTP", "POS", U(platelets=(12,"10^9/L"), schistocytes_percent=(4,"%"), hemoglobin=(7.5,"g/dL"), lactate_dehydrogenase=(1400,"U/L"), serum_haptoglobin=(5,"mg/dL"), creatinine=(1.1,"mg/dL"), adamts13_activity=(4,"%")), F38, ["ttp"], ["thrombotic_thrombocytopenic_purpura"]),
 ("POS PHPT", "POS", U(calcium_total=(11.4,"mg/dL"), albumin=(4.0,"g/dL"), parathyroid_hormone=(140,"pg/mL"), phosphate=(2.2,"mg/dL"), creatinine=(0.9,"mg/dL")), F38, ["phpt"], ["primary_hyperparathyroidism"]),

 # ---------------- SI twins ----------------------------------------------------
 ("SI DKA", "SI",
  (U(glucose=(480,"mg/dL"), beta_hydroxybutyrate=(6,"mmol/L"), bicarbonate=(10,"mmol/L"), anion_gap=(28,"mmol/L"), sodium=(136,"mmol/L"), chloride=(98,"mmol/L"), creatinine=(1.4,"mg/dL")),
   U(glucose=(26.6,"mmol/L"), beta_hydroxybutyrate=(6,"mmol/L"), bicarbonate=(10,"mmol/L"), anion_gap=(28,"mmol/L"), sodium=(136,"mmol/L"), chloride=(98,"mmol/L"), creatinine=(124,"umol/L"))),
  M45, [], []),
 ("SI PHPT", "SI",
  (U(calcium_total=(11.4,"mg/dL"), albumin=(4.0,"g/dL"), parathyroid_hormone=(140,"pg/mL"), phosphate=(2.2,"mg/dL"), creatinine=(0.9,"mg/dL")),
   U(calcium_total=(2.85,"mmol/L"), albumin=(40,"g/L"), parathyroid_hormone=(14.8,"pmol/L"), phosphate=(0.71,"mmol/L"), creatinine=(80,"umol/L"))),
  F38, [], []),
 ("SI HELLP", "SI",
  (U(platelets=(58,"10^9/L"), aspartate_aminotransferase=(410,"U/L"), alanine_aminotransferase=(360,"U/L"), lactate_dehydrogenase=(1500,"U/L"), total_bilirubin=(2.1,"mg/dL"), serum_haptoglobin=(8,"mg/dL"), schistocytes_percent=(2,"%"), creatinine=(1.3,"mg/dL"), uric_acid=(8.1,"mg/dL")),
   U(platelets=(58,"10^9/L"), aspartate_aminotransferase=(410,"U/L"), alanine_aminotransferase=(360,"U/L"), lactate_dehydrogenase=(1500,"U/L"), total_bilirubin=(35.9,"umol/L"), serum_haptoglobin=(0.08,"g/L"), schistocytes_percent=(2,"%"), creatinine=(115,"umol/L"), uric_acid=(482,"umol/L"))),
  PREG, [], []),
 ("SI IDA", "SI",
  (U(hemoglobin=(9.2,"g/dL"), mean_corpuscular_volume=(68,"fL"), ferritin=(6,"ng/mL"), transferrin_saturation=(7,"%")),
   U(hemoglobin=(92,"g/L"), mean_corpuscular_volume=(68,"fL"), ferritin=(6,"ug/L"), transferrin_saturation=(7,"%"))),
  F38, [], []),
 ("SI hyperbilirubinaemia/cholestasis", "SI",
  (U(alkaline_phosphatase=(640,"U/L"), total_bilirubin=(4.4,"mg/dL"), direct_bilirubin=(3.5,"mg/dL"), gamma_glutamyl_transferase=(420,"U/L"), white_blood_cell_count=(16,"10^9/L"), c_reactive_protein=(120,"mg/L")),
   U(alkaline_phosphatase=(640,"U/L"), total_bilirubin=(75.2,"umol/L"), direct_bilirubin=(59.9,"umol/L"), gamma_glutamyl_transferase=(420,"U/L"), white_blood_cell_count=(16,"10^9/L"), c_reactive_protein=(120,"mg/L"))),
  M70, [], []),
 ("SI AKI prerenal", "SI",
  (U(creatinine=(2.6,"mg/dL"), blood_urea_nitrogen=(78,"mg/dL"), sodium=(142,"mmol/L"), potassium=(5.1,"mmol/L"), bicarbonate=(19,"mmol/L")),
   U(creatinine=(230,"umol/L"), blood_urea_nitrogen=(27.8,"mmol/L"), sodium=(142,"mmol/L"), potassium=(5.1,"mmol/L"), bicarbonate=(19,"mmol/L"))),
  M70, [], []),

 # ---------------- NOCRASH -----------------------------------------------------
 ("NOCRASH zero/negative values", "NOCRASH", U(platelets=(0,"10^9/L"), alanine_aminotransferase=(-5,"U/L"), creatinine=(0,"mg/dL"), hemoglobin=(0.0,"g/dL")), M45, [], []),
 ("NOCRASH absurd magnitudes", "NOCRASH", U(glucose=(99999,"mg/dL"), ferritin=(1e9,"ng/mL"), calcium_total=(1e-6,"mg/dL")), M45, [], []),
 ("NOCRASH no patient", "NOCRASH", U(hemoglobin=(9,"g/dL"), ferritin=(5,"ng/mL")), None, [], []),
 ("NOCRASH age 0 / unknown sex", "NOCRASH", U(total_bilirubin=(14,"mg/dL"), direct_bilirubin=(0.4,"mg/dL")), {"age_years": 0, "sex_at_birth": "unknown"}, [], []),
 ("NOCRASH strings", "NOCRASH", {"sodium": {"value": "abc", "unit": "mmol/L"}, "potassium": {"value": None, "unit": "mmol/L"}}, M45, [], []),
]


def _payload(obs):
    out = {}
    for f, v in obs.items():
        if isinstance(v, dict):
            out[f] = v
        else:
            out[f] = {"value": v[0], "unit": v[1]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine()
    known = set(E.registry.features)
    passed = 0; fails = []; times = []
    for name, kind, obs, pt, syns, dxs in CASES:
        if a.only and a.only.lower() not in name.lower():
            continue
        t0 = time.perf_counter()
        try:
            if kind == "SI":
                r1 = E.interpret(_payload(obs[0]), None, pt).to_dict()
                r2 = E.interpret(_payload(obs[1]), None, pt).to_dict()
                d1, d2 = r1["differential_diagnosis"], r2["differential_diagnosis"]
                ok = bool(d1) and bool(d2) and d1[0]["disease_id"] == d2[0]["disease_id"] and abs(d1[0]["probability"] - d2[0]["probability"]) <= 0.05
                s1 = {h["syndrome_id"] for h in r1["expert_syndromes"]}; s2 = {h["syndrome_id"] for h in r2["expert_syndromes"]}
                ok = ok and s1 == s2
                detail = f"conv={d1[0]['disease_id'] if d1 else None}:{d1[0]['probability'] if d1 else None} si={d2[0]['disease_id'] if d2 else None}:{d2[0]['probability'] if d2 else None} syn {s1} vs {s2}"
            else:
                rep = E.interpret(_payload(obs), None, pt).to_dict()
                fired = {h["syndrome_id"] for h in rep["expert_syndromes"]}
                diff = rep["differential_diagnosis"]
                unknown = [k for k in obs if k not in known]
                if kind == "NEG":
                    bad_syn = fired & set(syns)
                    bad_top = diff and diff[0]["disease_id"] in set(dxs) and diff[0]["evidence_state"] == "supported" and diff[0]["probability"] >= 0.8
                    ok = not bad_syn and not bad_top
                    detail = f"fired={sorted(fired)} top={[(x['disease_id'], round(x['probability'],2), x['evidence_state']) for x in diff[:3]]}" + (f" unknown={unknown}" if unknown else "")
                elif kind == "POS":
                    ok = bool(fired & set(syns)) and bool(diff) and diff[0]["disease_id"] in set(dxs)
                    detail = f"fired={sorted(fired)} top={[(x['disease_id'], round(x['probability'],2)) for x in diff[:3]]}"
                else:
                    ok = isinstance(diff, list)
                    detail = f"n={len(diff)} fired={sorted(fired)}"
        except Exception as e:  # noqa
            ok = False; detail = f"EXCEPTION {type(e).__name__}: {e}"
        times.append((time.perf_counter() - t0) * 1000)
        if ok:
            passed += 1
            if a.verbose: print(f"[ OK ] {name}\n        {detail}")
        else:
            fails.append(name); print(f"[FAIL] {name}\n        {detail}")
    n = passed + len(fails)
    times.sort()
    print(f"\nADVERSARIAL SCORE {passed}/{n} ({100*passed/max(n,1):.1f}%)  median {times[len(times)//2]:.0f} ms")
    if fails: print("FAILS:", fails)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
