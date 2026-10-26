"""Hemoglyph HARD battery 3 — entities added by registry patch 13.1.0
(2026-10-21) and their ESL extension-3 constellations, plus matched
NEGATIVE controls (look-alike panels that must NOT trigger the new entity).

Synthetic, developer-authored, textbook-derived; not clinical validation.
Usage:  python tests/hard_battery3.py [--verbose] [--only SUBSTR]
"""
from __future__ import annotations
import os, sys, time, argparse, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)

M45 = {"age_years": 45, "sex_at_birth": "male"}
F38 = {"age_years": 38, "sex_at_birth": "female"}
M70 = {"age_years": 70, "sex_at_birth": "male"}
NEO = {"age_years": 0.01, "sex_at_birth": "male"}
INF = {"age_years": 0.15, "sex_at_birth": "male"}
TOD = {"age_years": 2, "sex_at_birth": "male"}
PREG9 = {"age_years": 28, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 9}
PREG34 = {"age_years": 31, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 34}

def U(**kw): return kw

# (name, obs, patient, accept_ids, max_rank)   accept == ["!id"] → id must NOT be in top-3 with p>=0.5
CASES = [
 ("TSH-oma / RTH", U(thyroid_stimulating_hormone=(4.2,"mIU/L"), free_thyroxine=(2.9,"ng/dL"), tsh_receptor_antibody=(0.3,"IU/L"), prolactin=(38,"ng/mL")), F38, ["tsh_secreting_adenoma_or_rth"], 1),
 ("NEG: Graves must not be TSH-oma", U(thyroid_stimulating_hormone=(0.01,"mIU/L"), free_thyroxine=(3.2,"ng/dL"), tsh_receptor_antibody=(8.5,"IU/L")), F38, ["!tsh_secreting_adenoma_or_rth"], 3),
 ("Hypothyroid myopathy", U(thyroid_stimulating_hormone=(68,"mIU/L"), free_thyroxine=(0.3,"ng/dL"), creatine_kinase_total=(1850,"U/L"), aspartate_aminotransferase=(58,"U/L"), lactate_dehydrogenase=(310,"U/L"), total_cholesterol=(310,"mg/dL")), F38, ["hypothyroid_myopathy"], 1),
 ("FHH", U(calcium_total=(10.9,"mg/dL"), albumin=(4.2,"g/dL"), parathyroid_hormone=(52,"pg/mL"), urine_calcium_to_creatinine_clearance_ratio=(0.006,"1"), magnesium=(2.5,"mg/dL")), M45, ["familial_hypocalciuric_hypercalcemia"], 1),
 ("NEG: PHPT (CCCR 0.03) must not be FHH", U(calcium_total=(11.4,"mg/dL"), albumin=(4.1,"g/dL"), parathyroid_hormone=(140,"pg/mL"), urine_calcium_to_creatinine_clearance_ratio=(0.03,"1")), F38, ["!familial_hypocalciuric_hypercalcemia"], 3),
 ("Pseudohyponatraemia (TG)", U(sodium=(126,"mmol/L"), triglycerides=(3200,"mg/dL"), serum_osmolality=(288,"mOsm/kg"), glucose=(140,"mg/dL")), M45, ["pseudohyponatremia"], 1),
 ("NEG: true hypo-osmolar hyponatraemia", U(sodium=(124,"mmol/L"), serum_osmolality=(255,"mOsm/kg"), urine_osmolality=(480,"mOsm/kg"), urine_sodium=(70,"mmol/L"), uric_acid=(2.4,"mg/dL")), M70, ["!pseudohyponatremia"], 3),
 ("Renovascular hypertension", U(plasma_renin_activity=(9.5,"ng/mL/h"), aldosterone=(28,"ng/dL"), potassium=(3.1,"mmol/L"), creatinine=(1.5,"mg/dL"), bicarbonate=(30,"mmol/L")), M70, ["renovascular_hypertension"], 1),
 ("NEG: primary aldosteronism (renin suppressed)", U(plasma_renin_activity=(0.2,"ng/mL/h"), aldosterone=(28,"ng/dL"), potassium=(3.0,"mmol/L"), bicarbonate=(31,"mmol/L")), M45, ["!renovascular_hypertension"], 3),
 ("Heparin contamination", U(activated_partial_thromboplastin_time=(110,"s"), thrombin_time=(60,"s"), reptilase_time=(18,"s"), prothrombin_time=(13,"s"), fibrinogen=(320,"mg/dL"), platelets=(230,"10^9/L")), M70, ["heparin_effect_coagulation"], 1),
 ("NEG: hypofibrinogenaemia (reptilase long)", U(activated_partial_thromboplastin_time=(60,"s"), thrombin_time=(45,"s"), reptilase_time=(40,"s"), fibrinogen=(70,"mg/dL"), prothrombin_time=(22,"s")), M70, ["!heparin_effect_coagulation"], 3),
 ("Biliary atresia", U(direct_bilirubin=(5.8,"mg/dL"), total_bilirubin=(8.2,"mg/dL"), gamma_glutamyl_transferase=(720,"U/L"), alkaline_phosphatase=(640,"U/L"), alanine_aminotransferase=(110,"U/L")), INF, ["biliary_atresia"], 1),
 ("Neonatal cholestasis (low GGT, PFIC-like)", U(direct_bilirubin=(3.1,"mg/dL"), total_bilirubin=(5.0,"mg/dL"), gamma_glutamyl_transferase=(40,"U/L"), alanine_aminotransferase=(90,"U/L")), INF, ["neonatal_cholestasis"], 1),
 ("NEG: physiological unconjugated jaundice", U(direct_bilirubin=(0.3,"mg/dL"), total_bilirubin=(11,"mg/dL"), hemoglobin=(16,"g/dL")), {"age_years":0.01,"sex_at_birth":"female"}, ["!biliary_atresia","!neonatal_cholestasis"], 3),
 ("Protein-losing enteropathy", U(albumin=(2.1,"g/dL"), fecal_alpha1_antitrypsin_clearance=(85,"mL/d"), total_protein=(4.4,"g/dL"), total_immunoglobulin_g=(380,"mg/dL"), urine_protein_to_creatinine_ratio=(0.1,"g/g"), total_cholesterol=(120,"mg/dL"), lymphocyte_count_absolute=(0.7,"10^9/L")), TOD, ["protein_losing_enteropathy"], 1),
 ("NEG: nephrotic syndrome not PLE", U(albumin=(2.0,"g/dL"), urine_protein_to_creatinine_ratio=(6.2,"g/g"), total_cholesterol=(340,"mg/dL"), total_immunoglobulin_g=(400,"mg/dL")), TOD, ["!protein_losing_enteropathy"], 3),
 ("AA amyloidosis (RA)", U(urine_protein_to_creatinine_ratio=(5.1,"g/g"), serum_amyloid_a=(180,"mg/L"), albumin=(2.6,"g/dL"), creatinine=(1.8,"mg/dL"), c_reactive_protein=(60,"mg/L"), serum_free_kappa_to_lambda_ratio_flc=(1.2,"1")), {"age_years":60,"sex_at_birth":"female","conditions":["rheumatoid arthritis 25 years"]}, ["aa_amyloidosis"], 1),
 ("Cyanide (fire victim)", U(lactate=(14,"mmol/L"), bicarbonate=(11,"mmol/L"), anion_gap=(28,"mmol/L"), carboxyhemoglobin_fraction=(18,"%"), arterial_ph=(7.12,"[pH]"), sodium=(140,"mmol/L"), chloride=(101,"mmol/L")), M45, ["cyanide_poisoning"], 1),
 ("Cyanide (measured)", U(cyanide_blood=(2.4,"mg/L"), lactate=(9,"mmol/L")), M45, ["cyanide_poisoning"], 1),
 ("NEG: CO only, lactate 3", U(carboxyhemoglobin_fraction=(22,"%"), lactate=(3.0,"mmol/L"), bicarbonate=(21,"mmol/L")), M45, ["!cyanide_poisoning"], 3),
 ("SAH (xanthochromia)", U(csf_xanthochromia=(1,"1"), sodium=(131,"mmol/L"), high_sensitivity_troponin_i=(90,"ng/L"), glucose=(160,"mg/dL")), F38, ["subarachnoid_hemorrhage"], 1),
 ("HSV encephalitis CSF", U(cerebrospinal_fluid_total_protein=(95,"mg/dL"), cerebrospinal_fluid_glucose=(62,"mg/dL"), glucose=(100,"mg/dL"), sodium=(131,"mmol/L"), c_reactive_protein=(12,"mg/L"), procalcitonin=(0.1,"ng/mL")), {"age_years":40,"sex_at_birth":"male","conditions":["fever, confusion and seizure"]}, ["hsv_encephalitis"], 1),
 ("NEG: bacterial meningitis (low CSF glucose)", U(cerebrospinal_fluid_total_protein=(280,"mg/dL"), cerebrospinal_fluid_glucose=(18,"mg/dL"), glucose=(110,"mg/dL"), procalcitonin=(6,"ng/mL"), c_reactive_protein=(220,"mg/L")), {"age_years":40,"sex_at_birth":"male","conditions":["fever, confusion"]}, ["!hsv_encephalitis"], 3),
 ("Duchenne (boy, 'transaminitis')", U(creatine_kinase_total=(18500,"U/L"), aspartate_aminotransferase=(210,"U/L"), alanine_aminotransferase=(160,"U/L"), gamma_glutamyl_transferase=(14,"U/L"), lactate_dehydrogenase=(720,"U/L"), total_bilirubin=(0.4,"mg/dL")), {"age_years":4,"sex_at_birth":"male"}, ["duchenne_muscular_dystrophy"], 1),
 ("NEG: hepatitis A in a boy (GGT high, CK normal)", U(alanine_aminotransferase=(1400,"U/L"), aspartate_aminotransferase=(1100,"U/L"), gamma_glutamyl_transferase=(180,"U/L"), creatine_kinase_total=(120,"U/L"), hepatitis_a_igm_antibody=(1,"1"), total_bilirubin=(4,"mg/dL")), {"age_years":6,"sex_at_birth":"male"}, ["!duchenne_muscular_dystrophy"], 3),
 ("Malignant hyperthermia", U(arterial_pco2=(78,"mm[Hg]"), arterial_ph=(7.08,"[pH]"), potassium=(6.4,"mmol/L"), creatine_kinase_total=(9000,"U/L"), body_temperature=(40.2,"Cel"), lactate=(7,"mmol/L"), bicarbonate=(16,"mmol/L")), {"age_years":22,"sex_at_birth":"male","conditions":["under general anaesthesia with sevoflurane"]}, ["malignant_hyperthermia"], 1),
 ("Isopropanol", U(osmolal_gap=(45,"mOsm/kg"), acetone_serum=(60,"mg/dL"), bicarbonate=(24,"mmol/L"), anion_gap=(11,"mmol/L"), glucose=(95,"mg/dL"), beta_hydroxybutyrate=(0.3,"mmol/L"), ethanol=(0,"mg/dL")), M45, ["isopropanol_poisoning"], 1),
 ("NEG: methanol (acidotic) not isopropanol", U(osmolal_gap=(40,"mOsm/kg"), bicarbonate=(8,"mmol/L"), anion_gap=(30,"mmol/L"), methanol=(80,"mg/dL")), M45, ["!isopropanol_poisoning"], 3),
 ("Amatoxin", U(alanine_aminotransferase=(5600,"U/L"), aspartate_aminotransferase=(4800,"U/L"), international_normalized_ratio=(3.4,"1"), creatinine=(2.1,"mg/dL"), glucose=(58,"mg/dL"), acetaminophen=(0,"ug/mL"), hepatitis_a_igm_antibody=(0,"1"), hepatitis_b_surface_antigen=(0,"1"), total_bilirubin=(3.2,"mg/dL")), {"age_years":50,"sex_at_birth":"female","conditions":["ate foraged wild mushrooms 36 h ago"]}, ["amatoxin_poisoning"], 1),
 ("Isoniazid hepatotoxicity", U(alanine_aminotransferase=(640,"U/L"), aspartate_aminotransferase=(520,"U/L"), total_bilirubin=(2.8,"mg/dL"), alkaline_phosphatase=(130,"U/L"), hepatitis_a_igm_antibody=(0,"1"), acetaminophen=(0,"ug/mL")), {"age_years":45,"sex_at_birth":"female","medications":["isoniazid","rifampicin","pyrazinamide","ethambutol"]}, ["isoniazid_hepatotoxicity","drug_induced_liver_injury"], 1),
 ("Snakebite VICC", U(international_normalized_ratio=(9,"1"), fibrinogen=(40,"mg/dL"), d_dimer=(18,"ug/mL"), platelets=(85,"10^9/L"), creatinine=(1.9,"mg/dL"), creatine_kinase_total=(2400,"U/L"), hemoglobin=(9.8,"g/dL")), {"age_years":30,"sex_at_birth":"male","conditions":["viper bite 6 h ago"]}, ["snake_envenomation_coagulopathy"], 1),
 ("NAIT", U(platelets=(18,"10^9/L"), hemoglobin=(16.5,"g/dL"), white_blood_cell_count=(12,"10^9/L"), c_reactive_protein=(2,"mg/L"), procalcitonin=(0.1,"ng/mL"), total_bilirubin=(6,"mg/dL"), coombs_direct_antiglobulin_test=(0,"1")), NEO, ["neonatal_alloimmune_thrombocytopenia"], 1),
 ("NEG: neonatal sepsis thrombocytopenia", U(platelets=(40,"10^9/L"), hemoglobin=(14,"g/dL"), white_blood_cell_count=(3,"10^9/L"), c_reactive_protein=(80,"mg/L"), procalcitonin=(20,"ng/mL"), blood_culture=(1,"1")), NEO, ["!neonatal_alloimmune_thrombocytopenia"], 3),
 ("DiGeorge", U(calcium_total=(6.9,"mg/dL"), albumin=(3.8,"g/dL"), parathyroid_hormone=(8,"pg/mL"), cd3_t_cells_absolute=(700,"cells/uL"), phosphate=(7.2,"mg/dL"), magnesium=(1.9,"mg/dL"), lymphocyte_count_absolute=(1.8,"10^9/L")), {"age_years":0.05,"sex_at_birth":"female"}, ["digeorge_syndrome"], 1),
 ("Hyper-IgE syndrome", U(total_immunoglobulin_e=(12000,"IU/mL"), eosinophil_count_absolute=(1.6,"10^9/L"), total_immunoglobulin_g=(1300,"mg/dL"), c_reactive_protein=(30,"mg/L")), {"age_years":6,"sex_at_birth":"male"}, ["hyper_ige_syndrome"], 1),
 ("NEG: atopy IgE 800", U(total_immunoglobulin_e=(800,"IU/mL"), eosinophil_count_absolute=(0.6,"10^9/L")), {"age_years":6,"sex_at_birth":"male"}, ["!hyper_ige_syndrome"], 3),
 ("Central precocious puberty (girl 6)", U(luteinizing_hormone=(1.8,"IU/L"), follicle_stimulating_hormone=(4.1,"IU/L"), estradiol=(45,"pg/mL")), {"age_years":6,"sex_at_birth":"female"}, ["central_precocious_puberty"], 1),
 ("NEG: premature thelarche (prepubertal LH)", U(luteinizing_hormone=(0.05,"IU/L"), follicle_stimulating_hormone=(0.8,"IU/L"), estradiol=(8,"pg/mL")), {"age_years":2,"sex_at_birth":"female"}, ["!central_precocious_puberty"], 3),
 ("Gestational transient thyrotoxicosis", U(thyroid_stimulating_hormone=(0.02,"mIU/L"), free_thyroxine=(2.3,"ng/dL"), tsh_receptor_antibody=(0.4,"IU/L"), thyroid_peroxidase_antibody=(10,"IU/mL"), potassium=(3.2,"mmol/L"), urine_ketones_qualitative=(1,"1")), PREG9, ["gestational_transient_thyrotoxicosis","hyperemesis_gravidarum"], 1),
 ("NEG: Graves in pregnancy (TRAb+)", U(thyroid_stimulating_hormone=(0.01,"mIU/L"), free_thyroxine=(2.8,"ng/dL"), tsh_receptor_antibody=(6,"IU/L")), PREG9, ["!gestational_transient_thyrotoxicosis"], 3),
 ("Sheehan syndrome", U(free_thyroxine=(0.5,"ng/dL"), thyroid_stimulating_hormone=(1.2,"mIU/L"), prolactin=(1.5,"ng/mL"), cortisol_morning=(2.0,"ug/dL"), sodium=(128,"mmol/L"), glucose=(62,"mg/dL"), luteinizing_hormone=(0.3,"IU/L"), follicle_stimulating_hormone=(0.6,"IU/L")), {"age_years":32,"sex_at_birth":"female","conditions":["postpartum haemorrhage 6 months ago, failure to lactate, amenorrhoea"]}, ["sheehan_syndrome","hypopituitarism_panhypopituitarism"], 1),
 ("Gestational thrombocytopenia", U(platelets=(112,"10^9/L"), alanine_aminotransferase=(18,"U/L"), aspartate_aminotransferase=(22,"U/L"), lactate_dehydrogenase=(190,"U/L"), urine_protein_to_creatinine_ratio=(0.08,"g/g"), creatinine=(0.5,"mg/dL"), hemoglobin=(11.2,"g/dL"), uric_acid=(3.6,"mg/dL")), PREG34, ["gestational_thrombocytopenia"], 1),
 ("NEG: HELLP not gestational thrombocytopenia", U(platelets=(62,"10^9/L"), alanine_aminotransferase=(210,"U/L"), aspartate_aminotransferase=(260,"U/L"), lactate_dehydrogenase=(900,"U/L"), urine_protein_to_creatinine_ratio=(1.8,"g/g"), uric_acid=(7.5,"mg/dL")), PREG34, ["!gestational_thrombocytopenia"], 3),
 ("Obstetric APS", U(lupus_anticoagulant_screen=(1,"1"), cardiolipin_igg_antibody=(85,"GPL"), beta_2_glycoprotein_i_igg_antibody=(60,"U/mL"), activated_partial_thromboplastin_time=(48,"s"), platelets=(120,"10^9/L")), {"age_years":33,"sex_at_birth":"female","conditions":["three consecutive early pregnancy losses"]}, ["obstetric_antiphospholipid_syndrome","antiphospholipid_syndrome"], 1),
 ("Hyperviscosity (IgM)", U(plasma_viscosity=(6.1,"cP"), total_immunoglobulin_m=(5200,"mg/dL"), hemoglobin=(9.1,"g/dL"), total_protein=(11.2,"g/dL"), erythrocyte_sedimentation_rate=(130,"mm/h"), sodium=(131,"mmol/L")), M70, ["hyperviscosity_syndrome","waldenstrom_macroglobulinemia"], 1),
 ("Sulfonylurea hypoglycaemia", U(glucose=(34,"mg/dL"), insulin=(22,"uIU/mL"), c_peptide=(3.4,"ng/mL"), beta_hydroxybutyrate=(0.2,"mmol/L"), creatinine=(1.9,"mg/dL")), {"age_years":78,"sex_at_birth":"female","medications":["glibenclamide","metformin"]}, ["sulfonylurea_induced_hypoglycemia","hyperinsulinemic_hypoglycemia"], 1),
 ("NEG: exogenous insulin (C-peptide suppressed)", U(glucose=(30,"mg/dL"), insulin=(180,"uIU/mL"), c_peptide=(0.05,"ng/mL"), beta_hydroxybutyrate=(0.1,"mmol/L")), {"age_years":40,"sex_at_birth":"female","medications":["glibenclamide"]}, ["!sulfonylurea_induced_hypoglycemia"], 3),
 ("Beta-blocker overdose", U(heart_rate=(34,"/min"), glucose=(52,"mg/dL"), potassium=(5.4,"mmol/L"), lactate=(4.2,"mmol/L"), arterial_ph=(7.26,"[pH]")), {"age_years":35,"sex_at_birth":"female","medications":["propranolol"],"conditions":["intentional overdose"]}, ["beta_blocker_toxicity"], 1),
 ("NEG: CCB overdose (hyperglycaemic)", U(heart_rate=(38,"/min"), glucose=(320,"mg/dL"), lactate=(5,"mmol/L")), {"age_years":35,"sex_at_birth":"female","medications":["amlodipine"],"conditions":["overdose"]}, ["!beta_blocker_toxicity"], 3),
 ("Adrenal crisis", U(cortisol_morning=(1.4,"ug/dL"), sodium=(122,"mmol/L"), potassium=(6.1,"mmol/L"), glucose=(48,"mg/dL"), blood_urea_nitrogen=(48,"mg/dL"), creatinine=(1.8,"mg/dL"), adrenocorticotropic_hormone=(640,"pg/mL"), calcium_total=(10.6,"mg/dL"), eosinophil_count_absolute=(0.9,"10^9/L")), F38, ["adrenal_crisis","addison_disease","primary_adrenal_insufficiency"], 1),
 ("NEG: stress cortisol 28 — not adrenal crisis", U(cortisol_morning=(28,"ug/dL"), sodium=(128,"mmol/L"), potassium=(5.3,"mmol/L"), glucose=(65,"mg/dL")), F38, ["!adrenal_crisis"], 3),
 ("Accidental hypothermia", U(body_temperature=(27.5,"Cel"), potassium=(5.6,"mmol/L"), lactate=(4.1,"mmol/L"), glucose=(190,"mg/dL"), arterial_ph=(7.21,"[pH]"), platelets=(110,"10^9/L"), amylase=(220,"U/L")), M70, ["accidental_hypothermia"], 1),
 ("Exertional heat stroke", U(body_temperature=(41.2,"Cel"), creatine_kinase_total=(24000,"U/L"), alanine_aminotransferase=(380,"U/L"), creatinine=(2.4,"mg/dL"), international_normalized_ratio=(1.9,"1"), platelets=(70,"10^9/L"), lactate=(5,"mmol/L"), potassium=(3.1,"mmol/L")), {"age_years":24,"sex_at_birth":"male","conditions":["collapsed during marathon in hot weather"]}, ["heat_stroke"], 1),
 ("NEG: NMS (haloperidol) not heat stroke", U(body_temperature=(40.1,"Cel"), creatine_kinase_total=(18000,"U/L"), white_blood_cell_count=(17,"10^9/L"), creatinine=(1.9,"mg/dL"), serum_iron=(22,"ug/dL")), {"age_years":28,"sex_at_birth":"male","medications":["haloperidol"]}, ["!heat_stroke"], 3),
 ("TACO", U(n_terminal_pro_bnp=(6800,"pg/mL"), arterial_po2=(55,"mm[Hg]"), creatinine=(1.6,"mg/dL"), high_sensitivity_troponin_i=(30,"ng/L")), {"age_years":80,"sex_at_birth":"female","conditions":["dyspnoea 2 h after 2 units packed red cells"]}, ["transfusion_associated_circulatory_overload"], 1),
 ("NEG: TRALI (NT-proBNP normal)", U(n_terminal_pro_bnp=(120,"pg/mL"), arterial_po2=(52,"mm[Hg]"), white_blood_cell_count=(2.8,"10^9/L")), {"age_years":40,"sex_at_birth":"female","conditions":["hypoxaemia 3 h after plasma transfusion"]}, ["!transfusion_associated_circulatory_overload"], 3),
 ("Acute haemolytic transfusion reaction", U(coombs_direct_antiglobulin_test=(1,"1"), lactate_dehydrogenase=(1400,"U/L"), serum_haptoglobin=(2,"mg/dL"), total_bilirubin=(3.8,"mg/dL"), hemoglobin=(6.9,"g/dL"), creatinine=(2.0,"mg/dL"), potassium=(5.6,"mmol/L"), urine_myoglobin=(0,"1"), fibrinogen=(130,"mg/dL")), {"age_years":55,"sex_at_birth":"male","conditions":["rigors and flank pain 20 min into red cell transfusion"]}, ["acute_hemolytic_transfusion_reaction"], 1),
 ("Methylmalonic acidaemia", U(anion_gap=(30,"mmol/L"), bicarbonate=(7,"mmol/L"), ammonia=(420,"umol/L"), glucose=(55,"mg/dL"), urine_ketones_qualitative=(1,"1"), neutrophil_count_absolute=(0.7,"10^9/L"), platelets=(80,"10^9/L"), lactate=(4.5,"mmol/L"), sodium=(139,"mmol/L"), chloride=(102,"mmol/L")), {"age_years":0.02,"sex_at_birth":"male"}, ["organic_acidemia","methylmalonic_acidemia","propionic_acidemia"], 1),
 ("NEG: urea cycle (no acidosis) not organic acidaemia", U(ammonia=(900,"umol/L"), bicarbonate=(27,"mmol/L"), anion_gap=(10,"mmol/L"), arterial_ph=(7.5,"[pH]"), blood_urea_nitrogen=(2,"mg/dL")), NEO, ["!organic_acidemia"], 3),
 ("Hereditary thrombophilia (FVL)", U(factor_v_leiden_mutation=(1,"1"), d_dimer=(0.9,"ug/mL"), protein_c_activity=(95,"%"), protein_s_activity=(80,"%"), antithrombin_activity=(100,"%")), {"age_years":29,"sex_at_birth":"female","conditions":["unprovoked DVT"]}, ["hereditary_thrombophilia","factor_v_leiden_thrombophilia"], 1),
 ("NEG: low protein C on warfarin — not thrombophilia", U(protein_c_activity=(35,"%"), protein_s_activity=(40,"%"), international_normalized_ratio=(2.8,"1")), {"age_years":60,"sex_at_birth":"male","medications":["warfarin"]}, ["!hereditary_thrombophilia"], 3),
 ("IBD (calprotectin + CRP)", U(fecal_calprotectin=(900,"ug/g"), c_reactive_protein=(45,"mg/L"), hemoglobin=(10.8,"g/dL"), albumin=(3.1,"g/dL"), platelets=(520,"10^9/L"), clostridioides_difficile_toxin_a_b=(0,"1")), {"age_years":22,"sex_at_birth":"female"}, ["inflammatory_bowel_disease","crohn_disease","ulcerative_colitis"], 1),
 ("NEG: C. difficile colitis not IBD", U(fecal_calprotectin=(800,"ug/g"), c_reactive_protein=(90,"mg/L"), white_blood_cell_count=(24,"10^9/L"), clostridioides_difficile_toxin_a_b=(1,"1"), albumin=(2.6,"g/dL")), M70, ["!inflammatory_bowel_disease"], 3),
 ("TB pleuritis", U(pleural_fluid_adenosine_deaminase=(82,"U/L"), pleural_fluid_lactate_dehydrogenase=(520,"U/L"), pleural_fluid_total_protein=(5.1,"g/dL"), pleural_fluid_glucose=(70,"mg/dL"), albumin=(3.2,"g/dL")), {"age_years":28,"sex_at_birth":"male"}, ["tuberculous_pleuritis","tuberculosis"], 1),
 ("Malignant pleural effusion", U(pleural_fluid_adenosine_deaminase=(12,"U/L"), pleural_fluid_lactate_dehydrogenase=(680,"U/L"), pleural_fluid_total_protein=(4.6,"g/dL"), pleural_fluid_glucose=(38,"mg/dL"), carcinoembryonic_antigen=(45,"ng/mL"), albumin=(3.0,"g/dL"), hemoglobin=(10.5,"g/dL")), {"age_years":68,"sex_at_birth":"male","conditions":["heavy smoker, weight loss"]}, ["malignant_pleural_effusion","exudative_pleural_effusion"], 1),
 ("NEG: TB effusion (ADA 70) not malignant", U(pleural_fluid_adenosine_deaminase=(70,"U/L"), pleural_fluid_lactate_dehydrogenase=(500,"U/L"), pleural_fluid_total_protein=(5.0,"g/dL"), pleural_fluid_glucose=(55,"mg/dL")), {"age_years":68,"sex_at_birth":"male","conditions":["smoker"]}, ["!malignant_pleural_effusion"], 3),
 ("Valproate hyperammonaemic encephalopathy", U(ammonia=(180,"umol/L"), alanine_aminotransferase=(28,"U/L"), valproic_acid_total=(96,"ug/mL"), albumin=(4.0,"g/dL"), international_normalized_ratio=(1.0,"1")), {"age_years":30,"sex_at_birth":"female","medications":["divalproex"]}, ["valproate_induced_hyperammonemic_encephalopathy","valproate_toxicity"], 1),
 ("Reye syndrome", U(ammonia=(260,"umol/L"), alanine_aminotransferase=(480,"U/L"), aspartate_aminotransferase=(520,"U/L"), total_bilirubin=(1.1,"mg/dL"), international_normalized_ratio=(2.1,"1"), glucose=(50,"mg/dL"), acetaminophen=(0,"ug/mL")), {"age_years":7,"sex_at_birth":"male","conditions":["influenza last week, treated with aspirin; vomiting and encephalopathy"]}, ["reye_syndrome"], 1),
 ("NEG: hepatitis A in child (jaundiced) not Reye", U(ammonia=(60,"umol/L"), alanine_aminotransferase=(1800,"U/L"), total_bilirubin=(7,"mg/dL"), hepatitis_a_igm_antibody=(1,"1"), international_normalized_ratio=(1.2,"1")), {"age_years":7,"sex_at_birth":"male","conditions":["vomiting"]}, ["!reye_syndrome"], 3),
 ("Toxic shock syndrome", U(body_temperature=(39.8,"Cel"), platelets=(60,"10^9/L"), creatinine=(2.4,"mg/dL"), creatine_kinase_total=(900,"U/L"), total_bilirubin=(3.0,"mg/dL"), alanine_aminotransferase=(140,"U/L"), blood_culture=(0,"1"), c_reactive_protein=(260,"mg/L"), lactate=(4,"mmol/L"), albumin=(2.4,"g/dL")), {"age_years":24,"sex_at_birth":"female","conditions":["menstruating, tampon use, diffuse rash, hypotension"]}, ["toxic_shock_syndrome","septic_shock"], 1),
 ("Ketotic hypoglycaemia (toddler)", U(glucose=(42,"mg/dL"), beta_hydroxybutyrate=(4.2,"mmol/L"), insulin=(0.8,"uIU/mL"), lactate=(1.4,"mmol/L"), ammonia=(35,"umol/L"), cortisol_morning=(24,"ug/dL")), TOD, ["ketotic_hypoglycemia_of_childhood"], 1),
 ("NEG: GSD I (lactate 7) not ketotic hypoglycaemia", U(glucose=(38,"mg/dL"), beta_hydroxybutyrate=(2.5,"mmol/L"), insulin=(0.5,"uIU/mL"), lactate=(7.5,"mmol/L"), uric_acid=(10,"mg/dL"), triglycerides=(800,"mg/dL")), TOD, ["!ketotic_hypoglycemia_of_childhood"], 3),
 ("HTG pancreatitis", U(lipase=(2400,"U/L"), triglycerides=(4800,"mg/dL"), glucose=(280,"mg/dL"), sodium=(128,"mmol/L"), calcium_total=(7.9,"mg/dL"), albumin=(3.8,"g/dL"), alanine_aminotransferase=(40,"U/L"), c_reactive_protein=(180,"mg/L")), M45, ["hypertriglyceridemia_induced_pancreatitis","acute_pancreatitis"], 1),
 ("Alcoholic pancreatitis", U(lipase=(1900,"U/L"), gamma_glutamyl_transferase=(380,"U/L"), mean_corpuscular_volume=(104,"fL"), aspartate_aminotransferase=(95,"U/L"), alanine_aminotransferase=(42,"U/L"), triglycerides=(220,"mg/dL"), magnesium=(1.3,"mg/dL"), total_bilirubin=(1.4,"mg/dL")), {"age_years":48,"sex_at_birth":"male","conditions":["heavy alcohol use"]}, ["alcoholic_pancreatitis","acute_pancreatitis"], 1),
 ("NEG: biliary pancreatitis (ALT 300) not alcoholic", U(lipase=(2100,"U/L"), gamma_glutamyl_transferase=(300,"U/L"), alanine_aminotransferase=(310,"U/L"), total_bilirubin=(3.2,"mg/dL"), alkaline_phosphatase=(280,"U/L"), triglycerides=(150,"mg/dL")), {"age_years":48,"sex_at_birth":"male","conditions":["alcohol use"]}, ["!alcoholic_pancreatitis"], 3),
 ("Pancytopenia", U(hemoglobin=(7.8,"g/dL"), platelets=(32,"10^9/L"), neutrophil_count_absolute=(0.6,"10^9/L"), white_blood_cell_count=(1.9,"10^9/L"), reticulocyte_percent=(0.3,"%"), mean_corpuscular_volume=(102,"fL")), M70, ["pancytopenia","aplastic_anemia","myelodysplastic_syndrome"], 1),
 ("Acute hepatitis (undiff.)", U(alanine_aminotransferase=(1650,"U/L"), aspartate_aminotransferase=(1200,"U/L"), alkaline_phosphatase=(160,"U/L"), total_bilirubin=(4.5,"mg/dL"), international_normalized_ratio=(1.2,"1"), creatine_kinase_total=(90,"U/L")), M45, ["acute_hepatitis","acute_viral_hepatitis_pattern","hepatocellular_injury_pattern"], 1),
 ("NEG: ischaemic hepatitis/rhabdo (CK 30k) not 'acute hepatitis'", U(alanine_aminotransferase=(900,"U/L"), aspartate_aminotransferase=(2800,"U/L"), creatine_kinase_total=(30000,"U/L"), lactate_dehydrogenase=(3000,"U/L"), creatinine=(2.5,"mg/dL")), M45, ["!acute_hepatitis"], 3),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verbose", action="store_true"); ap.add_argument("--only", default=None); a = ap.parse_args()
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(); known = set(E.registry.features)
    passed = 0; fails = []; times = []
    for name, obs, pt, accept, max_rank in CASES:
        if a.only and a.only.lower() not in name.lower(): continue
        payload = {f: {"value": v, "unit": u} for f, (v, u) in obs.items()}
        t0 = time.perf_counter()
        try:
            rep = E.interpret(payload, None, pt).to_dict(); diff = rep["differential_diagnosis"]
            neg = [x[1:] for x in accept if x.startswith("!")]
            if neg:
                bad = [x["disease_id"] for x in diff[:max_rank] if x["disease_id"] in neg and x["probability"] >= 0.5]
                ok = not bad; rank = "neg-ok" if ok else f"neg-FAIL {bad}"
            else:
                rank = next((x["rank"] for x in diff if x["disease_id"] in set(accept)), None)
                ok = rank is not None and rank <= max_rank
            detail = f"rank={rank} (max {max_rank})\n        {[(x['disease_id'], round(x['probability'],2), x['evidence_state']) for x in diff[:5]]}\n        syn={[h['syndrome_id'] for h in rep['expert_syndromes']]}"
            unk = [k for k in obs if k not in known]
            if unk: detail += f"\n        unknown analytes: {unk}"
        except Exception as e:
            ok = False; detail = f"EXCEPTION {type(e).__name__}: {e}"
        times.append((time.perf_counter() - t0) * 1000)
        if ok:
            passed += 1
            if a.verbose: print(f"[ OK ] {name}: {detail}")
        else:
            fails.append(name); print(f"[FAIL] {name}: {detail}")
    n = passed + len(fails); times.sort()
    print(f"\nHARD3 SCORE {passed}/{n} ({100*passed/max(n,1):.1f}%)  median {times[len(times)//2]:.0f} ms  p95 {times[int(len(times)*0.95)-1]:.0f} ms")
    if fails: print("FAILS:", fails)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
