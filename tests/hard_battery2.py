"""Hemoglyph HARD battery 2 — rare / multi-system presentations covered by the
ESL extension (2026-10-21). Same honest scope as hard_battery.py: synthetic,
developer-authored, textbook-derived; a ranking safety-net, not validation.

Usage:  python tests/hard_battery2.py [--verbose] [--only SUBSTR]
"""
from __future__ import annotations
import os, sys, time, argparse, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)

M45 = {"age_years": 45, "sex_at_birth": "male"}
F38 = {"age_years": 38, "sex_at_birth": "female"}
M70 = {"age_years": 70, "sex_at_birth": "male"}
F72 = {"age_years": 72, "sex_at_birth": "female"}
M24 = {"age_years": 24, "sex_at_birth": "male"}
F26 = {"age_years": 26, "sex_at_birth": "female"}
CH4 = {"age_years": 4, "sex_at_birth": "male"}
CH9 = {"age_years": 9, "sex_at_birth": "female"}
NEO = {"age_years": 0.01, "sex_at_birth": "male"}
INF = {"age_years": 0.5, "sex_at_birth": "male"}
TEEN = {"age_years": 15, "sex_at_birth": "female"}
PREG = {"age_years": 31, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 34}

def U(**kw): return kw

CASES = [
 # ---------------- endocrine ----------------
 ("Subacute thyroiditis", U(thyroid_stimulating_hormone=(0.02,"mIU/L"), free_thyroxine=(3.1,"ng/dL"), erythrocyte_sedimentation_rate=(88,"mm/h"), c_reactive_protein=(60,"mg/L"), tsh_receptor_antibody=(0.5,"IU/L"), thyroid_peroxidase_antibody=(12,"IU/mL")), F38, ["subacute_thyroiditis","subacute_thyroiditis_de_quervain"], 1),
 ("Panhypopituitarism", U(free_thyroxine=(0.5,"ng/dL"), thyroid_stimulating_hormone=(1.1,"mIU/L"), cortisol_morning=(2.1,"ug/dL"), adrenocorticotropic_hormone=(8,"pg/mL"), luteinizing_hormone=(0.4,"IU/L"), follicle_stimulating_hormone=(0.9,"IU/L"), insulin_like_growth_factor_1=(40,"ng/mL"), sodium=(129,"mmol/L")), M45, ["hypopituitarism_panhypopituitarism"], 1),
 ("Liddle syndrome", U(potassium=(2.8,"mmol/L"), bicarbonate=(33,"mmol/L"), aldosterone=(2,"ng/dL"), plasma_renin_activity=(0.2,"ng/mL/h"), urine_chloride=(45,"mmol/L"), sodium=(144,"mmol/L")), M24, ["liddle_syndrome","apparent_mineralocorticoid_excess"], 1),
 ("Classic CAH neonate salt-wasting", {"17_hydroxyprogesterone":(18000,"ng/dL"), "sodium":(124,"mmol/L"), "potassium":(6.8,"mmol/L"), "glucose":(48,"mg/dL"), "cortisol_morning":(2,"ug/dL"), "plasma_renin_activity":(25,"ng/mL/h")}, {"age_years":0.03,"sex_at_birth":"female"}, ["congenital_adrenal_hyperplasia_classic","congenital_adrenal_hyperplasia"], 1),
 ("MEN1 (PHPT + prolactinoma)", U(calcium_total=(11.6,"mg/dL"), albumin=(4.1,"g/dL"), parathyroid_hormone=(130,"pg/mL"), prolactin=(240,"ng/mL")), F38, ["multiple_endocrine_neoplasia_type_1"], 1),
 ("VIPoma (WDHA)", U(vasoactive_intestinal_peptide=(420,"pg/mL"), potassium=(2.6,"mmol/L"), bicarbonate=(16,"mmol/L"), chloride=(112,"mmol/L"), calcium_total=(11.0,"mg/dL"), albumin=(4.0,"g/dL"), glucose=(160,"mg/dL")), M45, ["vipoma_support_pattern"], 1),
 ("Glucagonoma", U(glucagon=(1400,"pg/mL"), glucose=(190,"mg/dL"), hemoglobin_a1c=(7.4,"%"), hemoglobin=(10.5,"g/dL"), albumin=(3.1,"g/dL"), zinc=(55,"ug/dL")), M70, ["glucagonoma_support_pattern"], 1),
 ("Hypophosphatasia (adult)", U(alkaline_phosphatase=(18,"U/L"), calcium_total=(10.4,"mg/dL"), albumin=(4.2,"g/dL"), phosphate=(5.1,"mg/dL"), parathyroid_hormone=(14,"pg/mL"), vitamin_b6_pyridoxal_five_phosphate=(180,"nmol/L")), F38, ["hypophosphatasia"], 1),
 ("Tumour-induced osteomalacia (FGF23)", U(phosphate=(1.4,"mg/dL"), fgf23=(480,"RU/mL"), calcium_total=(9.2,"mg/dL"), albumin=(4.0,"g/dL"), alkaline_phosphatase=(260,"U/L"), parathyroid_hormone=(60,"pg/mL"), **{"1_25_dihydroxy_vitamin_d":(12,"pg/mL")}), M45, ["tumor_induced_osteomalacia"], 1),
 ("Vitamin D toxicity", {"25_hydroxy_vitamin_d":(260,"ng/mL"), "calcium_total":(12.8,"mg/dL"), "albumin":(4.0,"g/dL"), "parathyroid_hormone":(6,"pg/mL"), "phosphate":(5.0,"mg/dL"), "creatinine":(1.9,"mg/dL")}, F72, ["hypervitaminosis_d","hypervitaminosis_d_support_pattern"], 1),
 ("Pseudohyperkalaemia (thrombocytosis)", U(potassium=(6.4,"mmol/L"), platelets=(1150,"10^9/L"), creatinine=(0.9,"mg/dL"), bicarbonate=(25,"mmol/L"), sodium=(140,"mmol/L")), M70, ["pseudohyperkalemia"], 1),
 ("Hypomagnesaemic hypocalcaemia", U(magnesium=(0.8,"mg/dL"), calcium_total=(7.1,"mg/dL"), albumin=(4.0,"g/dL"), parathyroid_hormone=(18,"pg/mL"), potassium=(3.0,"mmol/L")), M45, ["hypomagnesemia","hypomagnesemia_pattern"], 1),
 ("Hashimoto overt (serology)", U(thyroid_stimulating_hormone=(14,"mIU/L"), thyroid_peroxidase_antibody=(820,"IU/mL"), free_thyroxine=(0.6,"ng/dL"), total_cholesterol=(262,"mg/dL")), F38, ["hashimoto_thyroiditis","primary_hypothyroidism","hypothyroidism"], 1),
 # ---------------- renal ----------------
 ("IgA nephropathy", U(urine_red_blood_cells_per_hpf=(40,"/[HPF]"), total_immunoglobulin_a=(520,"mg/dL"), urine_protein_to_creatinine_ratio=(1.2,"g/g"), creatinine=(1.4,"mg/dL"), complement_c3=(110,"mg/dL")), M24, ["iga_nephropathy","iga_nephropathy_berger"], 1),
 ("IgA vasculitis (HSP) child", U(urine_red_blood_cells_per_hpf=(25,"/[HPF]"), platelets=(380,"10^9/L"), total_immunoglobulin_a=(340,"mg/dL"), urine_protein_to_creatinine_ratio=(0.8,"g/g"), c_reactive_protein=(25,"mg/L")), CH4, ["iga_vasculitis"], 1),
 ("Cryoglobulinaemic vasculitis (HCV)", U(cryoglobulin=(1,"1"), complement_c4=(4,"mg/dL"), rheumatoid_factor=(180,"IU/mL"), hepatitis_c_antibody=(1,"1"), urine_red_blood_cells_per_hpf=(15,"/[HPF]"), creatinine=(1.6,"mg/dL")), M70, ["cryoglobulinemia"], 1),
 ("Anti-GBM disease", U(glomerular_basement_membrane_antibody=(1,"1"), creatinine=(4.2,"mg/dL"), urine_red_blood_cells_per_hpf=(60,"/[HPF]"), hemoglobin=(8.9,"g/dL"), urine_protein_to_creatinine_ratio=(1.5,"g/g")), M24, ["anti_gbm_disease_goodpasture","goodpasture_syndrome"], 1),
 ("Fanconi syndrome", U(phosphate=(1.8,"mg/dL"), bicarbonate=(16,"mmol/L"), urine_glucose_qualitative=(1,"1"), glucose=(92,"mg/dL"), uric_acid=(1.9,"mg/dL"), potassium=(3.1,"mmol/L"), sodium=(138,"mmol/L"), chloride=(112,"mmol/L"), urine_ph=(6.0,"[pH]")), F38, ["fanconi_syndrome"], 1),
 # ---------------- haematology ----------------
 ("Sickle cell disease (HbSS)", U(hemoglobin_s=(88,"%"), hemoglobin=(7.8,"g/dL"), reticulocyte_percent=(12,"%"), lactate_dehydrogenase=(520,"U/L"), total_bilirubin=(3.1,"mg/dL"), hemoglobin_f=(6,"%"), hemoglobin_a2=(3.0,"%")), M24, ["sickle_cell_disease"], 1),
 ("Sickle cell trait", U(hemoglobin_s=(38,"%"), hemoglobin=(14.2,"g/dL"), mean_corpuscular_volume=(84,"fL"), reticulocyte_percent=(1.1,"%")), M24, ["sickle_cell_trait","sickle_cell_trait_hbas"], 1),
 ("Beta-thalassaemia major", U(hemoglobin_f=(92,"%"), hemoglobin=(6.2,"g/dL"), mean_corpuscular_volume=(62,"fL"), nucleated_red_blood_cells_percent=(15,"%"), ferritin=(3200,"ng/mL"), total_bilirubin=(2.4,"mg/dL"), lactate_dehydrogenase=(480,"U/L")), CH4, ["beta_thalassemia_major","beta_thalassemia_major_cooley"], 1),
 ("Alpha-thalassaemia trait", U(mean_corpuscular_volume=(68,"fL"), hemoglobin_a2=(2.4,"%"), hemoglobin_f=(0.8,"%"), ferritin=(85,"ng/mL"), red_blood_cell_count=(5.9,"10^6/uL"), hemoglobin=(11.8,"g/dL"), red_cell_distribution_width_cv=(13.5,"%")), F26, ["alpha_thalassemia_trait","alpha_thalassemia","thalassemia_trait"], 1),
 ("Lead poisoning (child)", U(blood_lead=(42,"ug/dL"), basophilic_stippling_presence=(1,"1"), zinc_protoporphyrin=(180,"ug/dL"), hemoglobin=(9.4,"g/dL"), mean_corpuscular_volume=(70,"fL")), CH4, ["lead_poisoning","lead_poisoning_plumbism"], 1),
 ("Sideroblastic anaemia", U(hemoglobin=(8.6,"g/dL"), ferritin=(900,"ng/mL"), transferrin_saturation=(72,"%"), mean_corpuscular_volume=(74,"fL"), red_cell_distribution_width_cv=(22,"%"), basophilic_stippling_presence=(1,"1"), reticulocyte_percent=(0.8,"%"), blood_lead=(1,"ug/dL")), M70, ["sideroblastic_anemia"], 1),
 ("B12 deficiency megaloblastic", U(vitamin_b12=(95,"pg/mL"), mean_corpuscular_volume=(118,"fL"), hemoglobin=(7.9,"g/dL"), lactate_dehydrogenase=(1400,"U/L"), methylmalonic_acid=(1800,"nmol/L"), homocysteine=(38,"umol/L"), platelets=(110,"10^9/L"), reticulocyte_percent=(0.6,"%")), F72, ["vitamin_b12_deficiency","megaloblastic_anemia","vitamin_b12_deficiency_anemia"], 1),
 ("Pernicious anaemia", U(vitamin_b12=(110,"pg/mL"), anti_intrinsic_factor_antibody_igg=(1,"1"), mean_corpuscular_volume=(112,"fL"), hemoglobin=(9.1,"g/dL"), thyroid_peroxidase_antibody=(300,"IU/mL")), F72, ["pernicious_anemia","pernicious_anemia_serologic_pattern"], 1),
 ("Folate deficiency", U(folate_serum=(1.4,"ng/mL"), mean_corpuscular_volume=(108,"fL"), hemoglobin=(9.8,"g/dL"), homocysteine=(24,"umol/L"), vitamin_b12=(520,"pg/mL")), M45, ["folate_deficiency","folate_deficiency_anemia"], 1),
 ("Haemophilia B", U(factor_ix_activity=(3,"%"), prothrombin_time=(12,"s"), activated_partial_thromboplastin_time=(78,"s"), factor_viii_activity=(110,"%")), {"age_years":6,"sex_at_birth":"male"}, ["hemophilia_b","hemophilia_b_christmas"], 1),
 ("Factor XI deficiency", U(factor_xi_activity=(8,"%"), prothrombin_time=(12,"s"), activated_partial_thromboplastin_time=(62,"s"), factor_viii_activity=(95,"%"), factor_ix_activity=(90,"%")), F26, ["factor_xi_deficiency"], 1),
 ("Acquired haemophilia A", U(factor_viii_activity=(4,"%"), factor_viii_inhibitor_titer=(18,"{BU}"), activated_partial_thromboplastin_time=(88,"s"), prothrombin_time=(12,"s"), hemoglobin=(8.2,"g/dL")), F72, ["acquired_hemophilia_a"], 1),
 ("Warfarin over-anticoagulation", U(international_normalized_ratio=(8.4,"1"), fibrinogen=(320,"mg/dL"), platelets=(240,"10^9/L"), alanine_aminotransferase=(22,"U/L"), albumin=(4.1,"g/dL")), {"age_years":76,"sex_at_birth":"male","medications":["warfarin"]}, ["warfarin_over_anticoagulation"], 1),
 ("Hairy cell leukaemia", U(monocyte_count_absolute=(0.05,"10^9/L"), platelets=(62,"10^9/L"), hemoglobin=(9.4,"g/dL"), neutrophil_count_absolute=(0.9,"10^9/L"), white_blood_cell_count=(2.1,"10^9/L")), M70, ["hairy_cell_leukemia"], 1),
 ("Systemic mastocytosis", U(tryptase_serum=(96,"ng/mL"), alkaline_phosphatase=(180,"U/L"), hemoglobin=(11.2,"g/dL"), eosinophil_count_absolute=(0.9,"10^9/L")), M45, ["systemic_mastocytosis","mastocytosis"], 1),
 ("Hypereosinophilic syndrome", U(eosinophil_count_absolute=(6.8,"10^9/L"), high_sensitivity_troponin_i=(85,"ng/L"), tryptase_serum=(14,"ng/mL"), vitamin_b12=(1600,"pg/mL"), lactate_dehydrogenase=(380,"U/L"), total_immunoglobulin_e=(60,"IU/mL")), M45, ["hypereosinophilic_syndrome"], 1),
 ("Cold agglutinin disease", U(coombs_direct_antiglobulin_test=(1,"1"), cold_agglutinins_titer=(512,"{titer}"), hemoglobin=(8.4,"g/dL"), reticulocyte_percent=(7,"%"), total_bilirubin=(2.2,"mg/dL"), total_immunoglobulin_m=(640,"mg/dL"), mean_corpuscular_hemoglobin_concentration=(38.5,"g/dL")), F72, ["cold_agglutinin_disease"], 1),
 ("Diamond-Blackfan anaemia", U(hemoglobin=(5.2,"g/dL"), reticulocyte_percent=(0.1,"%"), mean_corpuscular_volume=(104,"fL"), white_blood_cell_count=(8,"10^9/L"), platelets=(320,"10^9/L"), hemoglobin_f=(8,"%")), INF, ["diamond_blackfan_anemia"], 1),
 ("Fanconi anaemia", U(platelets=(38,"10^9/L"), hemoglobin=(7.4,"g/dL"), mean_corpuscular_volume=(103,"fL"), neutrophil_count_absolute=(0.6,"10^9/L"), hemoglobin_f=(9,"%"), reticulocyte_percent=(0.4,"%")), {"age_years":7,"sex_at_birth":"male"}, ["fanconi_anemia"], 1),
 ("Drug agranulocytosis (clozapine)", U(neutrophil_count_absolute=(0.1,"10^9/L"), hemoglobin=(13.2,"g/dL"), platelets=(240,"10^9/L"), white_blood_cell_count=(1.4,"10^9/L"), c_reactive_protein=(48,"mg/L")), {"age_years":34,"sex_at_birth":"male","medications":["clozapine"]}, ["agranulocytosis","clozapine_agranulocytosis"], 1),
 ("Leukemoid reaction", U(white_blood_cell_count=(68,"10^9/L"), blasts_percent=(0,"%"), leukocyte_alkaline_phosphatase_score=(180,"1"), c_reactive_protein=(240,"mg/L"), band_neutrophils_percent=(22,"%"), basophils_percent=(0.3,"%"), procalcitonin=(9,"ng/mL")), M70, ["leukemoid_reaction","sepsis"], 2),
 ("Pyruvate kinase deficiency", U(hemoglobin=(8.8,"g/dL"), lactate_dehydrogenase=(560,"U/L"), serum_haptoglobin=(5,"mg/dL"), coombs_direct_antiglobulin_test=(0,"1"), spherocytes_percent=(0,"%"), g6pd_enzyme_activity=(9.5,"U/g{Hb}"), reticulocyte_percent=(14,"%"), total_bilirubin=(3.2,"mg/dL"), ferritin=(650,"ng/mL")), {"age_years":12,"sex_at_birth":"male"}, ["pyruvate_kinase_deficiency"], 1),
 ("Copper deficiency (post-bariatric)", U(copper=(28,"ug/dL"), hemoglobin=(9.2,"g/dL"), neutrophil_count_absolute=(0.9,"10^9/L"), ceruloplasmin=(9,"mg/dL"), mean_corpuscular_volume=(101,"fL"), zinc=(160,"ug/dL")), F38, ["copper_deficiency"], 1),
 ("Scurvy", U(vitamin_c=(0.05,"mg/dL"), hemoglobin=(10.4,"g/dL"), ferritin=(18,"ng/mL")), M70, ["scurvy","vitamin_c_deficiency"], 1),
 ("Thiamine deficiency (Wernicke)", U(vitamin_b1_thiamine_whole_blood=(28,"nmol/L"), lactate=(3.4,"mmol/L"), magnesium=(1.4,"mg/dL"), albumin=(3.0,"g/dL")), M45, ["thiamine_deficiency","wernicke_encephalopathy","beriberi"], 1),
 ("Hereditary protein C deficiency", U(protein_c_activity=(38,"%"), d_dimer=(1.2,"ug/mL"), international_normalized_ratio=(1.0,"1"), alanine_aminotransferase=(24,"U/L"), albumin=(4.3,"g/dL")), M24, ["protein_c_deficiency","hereditary_thrombophilia"], 1),
 ("Massive transfusion coagulopathy", U(fibrinogen=(90,"mg/dL"), platelets=(55,"10^9/L"), calcium_ionized=(0.82,"mmol/L"), international_normalized_ratio=(2.1,"1"), potassium=(6.1,"mmol/L"), hemoglobin=(7.2,"g/dL"), lactate=(5,"mmol/L")), {"age_years":30,"sex_at_birth":"male","conditions":["massive transfusion after trauma"]}, ["massive_transfusion_coagulopathy","disseminated_intravascular_coagulation"], 1),
 # ---------------- GI / liver ----------------
 ("Crigler-Najjar (infant)", U(total_bilirubin=(24,"mg/dL"), direct_bilirubin=(0.4,"mg/dL"), alanine_aminotransferase=(22,"U/L"), hemoglobin=(13,"g/dL"), coombs_direct_antiglobulin_test=(0,"1"), reticulocyte_percent=(1.5,"%"), lactate_dehydrogenase=(220,"U/L")), {"age_years":0.1,"sex_at_birth":"male"}, ["crigler_najjar_syndrome"], 1),
 ("Hepatitis E acute", U(hepatitis_e_igm_antibody=(1,"1"), alanine_aminotransferase=(1850,"U/L"), total_bilirubin=(6.1,"mg/dL"), hepatitis_a_igm_antibody=(0,"1"), hepatitis_b_surface_antigen=(0,"1")), M45, ["hepatitis_e","hepatitis_e_infection","hepatitis_e_infection_pattern"], 1),
 ("Chronic hepatitis C", U(hepatitis_c_rna_quantitative_pcr=(2400000,"IU/mL"), hepatitis_c_antibody=(1,"1"), alanine_aminotransferase=(88,"U/L"), platelets=(130,"10^9/L")), M45, ["chronic_hepatitis_c","hepatitis_c"], 1),
 ("Hepatitis D superinfection", U(hepatitis_b_surface_antigen=(1,"1"), hepatitis_d_antibody=(1,"1"), alanine_aminotransferase=(420,"U/L"), hepatitis_b_dna_quantitative_pcr=(400,"IU/mL")), M45, ["hepatitis_d","hepatitis_d_infection","hepatitis_d_infection_pattern"], 1),
 ("DILI hepatocellular (isoniazid)", U(alanine_aminotransferase=(960,"U/L"), alkaline_phosphatase=(140,"U/L"), total_bilirubin=(3.4,"mg/dL"), eosinophil_count_absolute=(0.9,"10^9/L"), antinuclear_antibody_titer=(0,"{titer}"), hepatitis_a_igm_antibody=(0,"1"), hepatitis_b_surface_antigen=(0,"1"), acetaminophen=(0,"ug/mL")), {"age_years":40,"sex_at_birth":"female","medications":["isoniazid","rifampin"]}, ["drug_induced_liver_injury","isoniazid_hepatotoxicity"], 1),
 ("Hepatic encephalopathy", U(ammonia=(186,"umol/L"), albumin=(2.4,"g/dL"), international_normalized_ratio=(2.0,"1"), platelets=(70,"10^9/L"), total_bilirubin=(4.2,"mg/dL"), sodium=(127,"mmol/L")), M70, ["hepatic_encephalopathy","hepatic_encephalopathy_support_pattern"], 1),
 ("Spontaneous bacterial peritonitis", U(ascitic_fluid_cell_count=(900,"/uL"), serum_ascites_albumin_gradient=(1.8,"g/dL"), ascitic_fluid_protein=(0.9,"g/dL"), c_reactive_protein=(70,"mg/L"), creatinine=(1.7,"mg/dL"), white_blood_cell_count=(13,"10^9/L")), M70, ["spontaneous_bacterial_peritonitis"], 1),
 ("Budd-Chiari (PV)", U(serum_ascites_albumin_gradient=(1.6,"g/dL"), ascitic_fluid_protein=(3.2,"g/dL"), alanine_aminotransferase=(160,"U/L"), jak2_v617f_mutation=(1,"1"), platelets=(520,"10^9/L"), hemoglobin=(17.8,"g/dL"), n_terminal_pro_bnp=(120,"pg/mL")), F38, ["budd_chiari_syndrome_support_pattern","polycythemia_vera"], 2),
 ("Active Crohn disease", U(fecal_calprotectin=(1400,"ug/g"), c_reactive_protein=(58,"mg/L"), hemoglobin=(10.2,"g/dL"), albumin=(2.9,"g/dL"), platelets=(560,"10^9/L"), ferritin=(12,"ng/mL")), M24, ["crohn_disease","ulcerative_colitis","inflammatory_bowel_disease"], 1),
 ("C. difficile severe", U(clostridioides_difficile_toxin_a_b=(1,"1"), white_blood_cell_count=(27,"10^9/L"), creatinine=(2.1,"mg/dL"), albumin=(2.4,"g/dL"), lactate=(3.1,"mmol/L")), F72, ["clostridioides_difficile_infection","clostridioides_difficile_support_pattern"], 1),
 ("H. pylori with IDA", U(helicobacter_pylori_stool_antigen=(1,"1"), hemoglobin=(10.6,"g/dL"), ferritin=(8,"ng/mL")), F38, ["helicobacter_pylori_infection","iron_deficiency_anemia"], 2),
 ("Colorectal cancer pattern", U(carcinoembryonic_antigen=(48,"ng/mL"), stool_occult_blood_fit=(1,"1"), hemoglobin=(9.6,"g/dL"), ferritin=(7,"ng/mL"), mean_corpuscular_volume=(71,"fL"), alkaline_phosphatase=(160,"U/L")), M70, ["colorectal_cancer","colorectal_cancer_marker_abnormality"], 1),
 ("Pancreatic cancer with obstruction", U(ca_19_9=(4800,"U/mL"), alkaline_phosphatase=(620,"U/L"), total_bilirubin=(9.8,"mg/dL"), direct_bilirubin=(8.1,"mg/dL"), hemoglobin_a1c=(7.1,"%"), albumin=(3.0,"g/dL"), carcinoembryonic_antigen=(12,"ng/mL")), M70, ["pancreatic_cancer","pancreatic_adenocarcinoma_marker_pattern","pancreatic_cancer_marker_abnormality"], 1),
 ("Molar pregnancy with hyperthyroidism", U(human_chorionic_gonadotropin_quantitative=(820000,"mIU/mL"), thyroid_stimulating_hormone=(0.02,"mIU/L"), free_thyroxine=(2.6,"ng/dL"), hemoglobin=(10.1,"g/dL")), F26, ["molar_pregnancy","gestational_trophoblastic_disease_marker_pattern"], 1),
 ("Lymphoma tumour burden", U(lactate_dehydrogenase=(980,"U/L"), beta_2_microglobulin=(6.4,"mg/L"), hemoglobin=(10.2,"g/dL"), erythrocyte_sedimentation_rate=(78,"mm/h"), uric_acid=(9.1,"mg/dL"), albumin=(3.1,"g/dL"), blasts_percent=(0,"%")), M70, ["lymphoma_support_pattern","non_hodgkin_lymphoma","hodgkin_lymphoma"], 1),
 ("Neuroblastoma", U(urine_vanillylmandelic_acid_24h=(45,"mg/24h"), urine_homovanillic_acid_24h=(60,"mg/24h"), lactate_dehydrogenase=(1800,"U/L"), ferritin=(420,"ng/mL"), neuron_specific_enolase=(120,"ng/mL"), hemoglobin=(9.4,"g/dL")), {"age_years":2,"sex_at_birth":"female"}, ["neuroblastoma"], 1),
 # ---------------- infection ----------------
 ("Brucellosis", U(wright_agglutination_test_titer=(640,"{titer}"), alanine_aminotransferase=(88,"U/L"), platelets=(120,"10^9/L"), white_blood_cell_count=(3.6,"10^9/L"), c_reactive_protein=(45,"mg/L")), M45, ["brucellosis","brucellosis_serologic_support_pattern"], 1),
 ("Typhoid fever", U(widal_to_antigen_titer=(320,"{titer}"), white_blood_cell_count=(3.2,"10^9/L"), alanine_aminotransferase=(96,"U/L"), eosinophil_count_absolute=(0.0,"10^9/L"), platelets=(130,"10^9/L"), c_reactive_protein=(80,"mg/L")), M24, ["typhoid_fever"], 1),
 ("Leptospirosis (Weil)", U(total_bilirubin=(14,"mg/dL"), direct_bilirubin=(10,"mg/dL"), creatinine=(3.8,"mg/dL"), platelets=(48,"10^9/L"), alanine_aminotransferase=(110,"U/L"), creatine_kinase_total=(1800,"U/L"), white_blood_cell_count=(15,"10^9/L"), potassium=(3.0,"mmol/L"), c_reactive_protein=(180,"mg/L")), {"age_years":35,"sex_at_birth":"male","conditions":["fever after flood water exposure"]}, ["leptospirosis"], 1),
 ("Severe COVID-19", U(sars_cov_2_rt_pcr_qualitative=(1,"1"), lymphocyte_count_absolute=(0.5,"10^9/L"), ferritin=(1800,"ng/mL"), d_dimer=(3.2,"ug/mL"), lactate_dehydrogenase=(620,"U/L"), c_reactive_protein=(160,"mg/L"), procalcitonin=(0.2,"ng/mL")), M70, ["covid_19","sars_cov_2_infection"], 1),
 ("Infective endocarditis", U(blood_culture=(1,"1"), c_reactive_protein=(140,"mg/L"), rheumatoid_factor=(60,"IU/mL"), urine_red_blood_cells_per_hpf=(20,"/[HPF]"), hemoglobin=(10.1,"g/dL"), erythrocyte_sedimentation_rate=(90,"mm/h"), complement_c3=(70,"mg/dL")), M70, ["infective_endocarditis","endocarditis_support_pattern"], 1),
 ("Secondary syphilis", U(treponema_pallidum_hemagglutination_tpha=(1,"1"), rapid_plasma_reagin_titer=(128,"{titer}"), alkaline_phosphatase=(260,"U/L"), alanine_aminotransferase=(70,"U/L")), M24, ["syphilis","syphilis_serologic_pattern"], 1),
 ("CMV mononucleosis", U(cytomegalovirus_igm_antibody=(1,"1"), atypical_lymphocytes_percent=(18,"%"), heterophile_antibody=(0,"1"), alanine_aminotransferase=(140,"U/L"), lymphocyte_count_absolute=(5.2,"10^9/L")), M24, ["acute_cmv_infection","cmv_infection"], 1),
 ("Acute toxoplasmosis", U(toxoplasma_igm_antibody=(1,"1"), atypical_lymphocytes_percent=(8,"%"), lactate_dehydrogenase=(300,"U/L")), F26, ["toxoplasmosis","toxoplasmosis_serologic_pattern"], 1),
 ("Visceral leishmaniasis", U(leishmania_antibody=(1,"1"), hemoglobin=(7.2,"g/dL"), platelets=(60,"10^9/L"), neutrophil_count_absolute=(0.8,"10^9/L"), total_immunoglobulin_g=(3400,"mg/dL"), albumin=(2.4,"g/dL"), ferritin=(900,"ng/mL")), CH4, ["visceral_leishmaniasis"], 1),
 ("Scrub typhus triad", U(platelets=(70,"10^9/L"), sodium=(128,"mmol/L"), alanine_aminotransferase=(140,"U/L"), c_reactive_protein=(90,"mg/L"), lactate_dehydrogenase=(520,"U/L"), albumin=(2.9,"g/dL"), white_blood_cell_count=(7,"10^9/L"), dengue_ns1_antigen=(0,"1")), {"age_years":40,"sex_at_birth":"male","conditions":["fever with eschar after rural travel"]}, ["rickettsial_infection","scrub_typhus"], 1),
 ("MIS-C", U(c_reactive_protein=(210,"mg/L"), high_sensitivity_troponin_i=(180,"ng/L"), ferritin=(900,"ng/mL"), lymphocyte_count_absolute=(0.6,"10^9/L"), platelets=(95,"10^9/L"), d_dimer=(4.1,"ug/mL"), sodium=(130,"mmol/L"), albumin=(2.5,"g/dL"), n_terminal_pro_bnp=(6000,"pg/mL")), {"age_years":9,"sex_at_birth":"male","conditions":["COVID exposure 4 weeks ago"]}, ["multisystem_inflammatory_syndrome_cardiac_pattern"], 1),
 ("PCP in advanced HIV", U(lactate_dehydrogenase=(680,"U/L"), cd4_t_cells_absolute=(45,"cells/uL"), hiv_1_and_hiv_2_antigen_antibody=(1,"1"), arterial_po2=(52,"mm[Hg]"), albumin=(2.8,"g/dL")), M45, ["pneumocystis_pneumonia","hiv_infection"], 2),
 ("Invasive aspergillosis (neutropenic)", U(serum_galactomannan_index=(2.4,"1"), neutrophil_count_absolute=(0.1,"10^9/L"), c_reactive_protein=(160,"mg/L"), procalcitonin=(0.4,"ng/mL")), M45, ["invasive_aspergillosis_marker_pattern"], 1),
 ("TB pleuritis (ADA)", U(pleural_fluid_adenosine_deaminase=(78,"U/L"), quantiferon_tb_gold_plus=(1,"1"), pleural_fluid_lactate_dehydrogenase=(480,"U/L"), albumin=(3.1,"g/dL")), M24, ["tuberculosis","pulmonary_tuberculosis","exudative_pleural_effusion"], 2),
 # ---------------- rheumatology ----------------
 ("MCTD", U(rnp_antibody=(1,"1"), antinuclear_antibody_titer=(1280,"{titer}"), creatine_kinase_total=(800,"U/L"), rheumatoid_factor=(60,"IU/mL"), double_stranded_dna_antibody=(5,"IU/mL")), F38, ["mixed_connective_tissue_disease","mixed_connective_tissue_disease_serologic_pattern"], 1),
 ("Septic arthritis", U(synovial_fluid_wbc=(92000,"/uL"), c_reactive_protein=(210,"mg/L"), white_blood_cell_count=(15,"10^9/L"), procalcitonin=(1.1,"ng/mL")), M70, ["septic_arthritis"], 1),
 ("Pseudogout (HH-associated)", U(synovial_fluid_crystals_calcium_pyrophosphate=(1,"1"), c_reactive_protein=(45,"mg/L"), ferritin=(1100,"ng/mL"), calcium_total=(9.6,"mg/dL")), M70, ["pseudogout","pseudogout_cppd_disease"], 1),
 ("IgG4-related disease", U(serum_igg4=(620,"mg/dL"), total_immunoglobulin_g=(2400,"mg/dL"), eosinophil_count_absolute=(0.8,"10^9/L"), total_immunoglobulin_e=(480,"IU/mL"), complement_c4=(6,"mg/dL"), alkaline_phosphatase=(310,"U/L"), lipase=(140,"U/L")), M70, ["igg4_related_disease","igg4_related_disease_support_pattern","elevated_serum_igg4"], 1),
 ("Drug-induced lupus (hydralazine)", U(anti_histone_antibody=(1,"1"), antinuclear_antibody_titer=(640,"{titer}"), double_stranded_dna_antibody=(4,"IU/mL"), complement_c3=(120,"mg/dL"), complement_c4=(28,"mg/dL"), c_reactive_protein=(30,"mg/L")), {"age_years":68,"sex_at_birth":"female","medications":["hydralazine"]}, ["drug_induced_lupus"], 1),
 ("Axial spondyloarthritis", U(hla_b27_antigen_allele=(1,"1"), c_reactive_protein=(28,"mg/L"), erythrocyte_sedimentation_rate=(40,"mm/h"), rheumatoid_factor=(5,"IU/mL"), cyclic_citrullinated_peptide_antibody=(2,"U/mL")), M24, ["ankylosing_spondylitis"], 1),
 # ---------------- cardio / pulm ----------------
 ("Pericarditis", U(c_reactive_protein=(85,"mg/L"), high_sensitivity_troponin_i=(22,"ng/L"), erythrocyte_sedimentation_rate=(48,"mm/h"), white_blood_cell_count=(12,"10^9/L")), {"age_years":30,"sex_at_birth":"male","conditions":["pleuritic chest pain after viral illness"]}, ["acute_pericarditis","pericarditis_support_pattern"], 1),
 ("Takotsubo", U(high_sensitivity_troponin_i=(420,"ng/L"), n_terminal_pro_bnp=(9800,"pg/mL"), glucose=(170,"mg/dL"), creatine_kinase_total=(160,"U/L")), {"age_years":68,"sex_at_birth":"female","conditions":["acute emotional stress after bereavement"]}, ["takotsubo_cardiomyopathy"], 1),
 ("Digoxin toxicity", U(digoxin=(3.6,"ng/mL"), potassium=(5.9,"mmol/L"), creatinine=(2.2,"mg/dL"), magnesium=(1.5,"mg/dL")), F72, ["digoxin_toxicity","digoxin_toxicity_cardiac_risk"], 1),
 ("Statin myopathy", U(creatine_kinase_total=(4800,"U/L"), alanine_aminotransferase=(70,"U/L"), thyroid_stimulating_hormone=(2.1,"mIU/L"), creatinine=(1.1,"mg/dL")), {"age_years":66,"sex_at_birth":"male","medications":["atorvastatin 80 mg"]}, ["statin_associated_muscle_injury"], 1),
 ("ARDS (pneumonia)", U(arterial_po2=(52,"mm[Hg]"), arterial_pco2=(38,"mm[Hg]"), lactate=(3,"mmol/L"), c_reactive_protein=(240,"mg/L"), procalcitonin=(6,"ng/mL"), n_terminal_pro_bnp=(300,"pg/mL"), albumin=(2.6,"g/dL"), d_dimer=(2.2,"ug/mL")), {"age_years":55,"sex_at_birth":"male","conditions":["pneumonia with respiratory failure on ventilator"]}, ["acute_respiratory_distress_syndrome","sepsis","community_acquired_pneumonia"], 2),
 ("Severe CO poisoning", U(carboxyhemoglobin_fraction=(38,"%"), lactate=(6.2,"mmol/L"), high_sensitivity_troponin_i=(90,"ng/L"), creatine_kinase_total=(2400,"U/L"), bicarbonate=(15,"mmol/L")), M45, ["carbon_monoxide_poisoning"], 1),
 # ---------------- neuro ----------------
 ("Myasthenia gravis", U(anti_acetylcholine_receptor_binding_ab=(12.4,"nmol/L"), thyroid_stimulating_hormone=(0.2,"mIU/L"), creatine_kinase_total=(80,"U/L")), F38, ["myasthenia_gravis","myasthenia_gravis_antibody_pattern"], 1),
 ("Anti-NMDAR encephalitis", U(anti_nmda_receptor_nr1_antibody=(1,"1"), cerebrospinal_fluid_oligoclonal_bands=(1,"1"), sodium=(132,"mmol/L")), F26, ["anti_nmdar_encephalitis"], 1),
 ("MS (CSF OCB)", U(cerebrospinal_fluid_oligoclonal_bands=(1,"1"), vitamin_b12=(480,"pg/mL"), antinuclear_antibody_titer=(0,"{titer}"), erythrocyte_sedimentation_rate=(8,"mm/h"), total_immunoglobulin_g=(1100,"mg/dL")), F26, ["multiple_sclerosis"], 1),
 ("McArdle disease", U(creatine_kinase_total=(14000,"U/L"), uric_acid=(10.2,"mg/dL"), urine_myoglobin=(1,"1"), creatinine=(1.5,"mg/dL"), lactate=(0.9,"mmol/L"), thyroid_stimulating_hormone=(1.8,"mIU/L")), {"age_years":22,"sex_at_birth":"male","conditions":["recurrent exercise-induced cramps and myoglobinuria"]}, ["mcardle_disease","rhabdomyolysis"], 1),
 # ---------------- tox ----------------
 ("Lithium toxicity", U(lithium=(2.9,"mmol/L"), creatinine=(2.0,"mg/dL"), sodium=(149,"mmol/L"), urine_osmolality=(180,"mOsm/kg"), thyroid_stimulating_hormone=(7,"mIU/L")), F38, ["lithium_toxicity"], 1),
 ("Valproate toxicity", U(valproic_acid_total=(210,"ug/mL"), ammonia=(140,"umol/L"), platelets=(90,"10^9/L"), sodium=(131,"mmol/L")), M24, ["valproate_toxicity","valproic_acid_toxicity"], 1),
 ("Valproate hyperammonaemic encephalopathy", U(ammonia=(160,"umol/L"), alanine_aminotransferase=(30,"U/L"), albumin=(4.1,"g/dL"), platelets=(130,"10^9/L")), {"age_years":30,"sex_at_birth":"female","medications":["divalproex"]}, ["valproate_toxicity","valproic_acid_toxicity","valproate_induced_hyperammonemic_encephalopathy"], 1),
 ("Theophylline toxicity", U(theophylline=(48,"ug/mL"), potassium=(2.6,"mmol/L"), glucose=(260,"mg/dL"), lactate=(5,"mmol/L"), bicarbonate=(16,"mmol/L")), M70, ["theophylline_toxicity"], 1),
 ("Iron poisoning (child)", U(serum_iron=(820,"ug/dL"), anion_gap=(24,"mmol/L"), bicarbonate=(12,"mmol/L"), glucose=(190,"mg/dL"), white_blood_cell_count=(22,"10^9/L"), transferrin_saturation=(120,"%")), CH4, ["iron_poisoning"], 1),
 ("Organophosphate poisoning", U(cholinesterase=(900,"U/L"), glucose=(180,"mg/dL"), lactate=(3.1,"mmol/L"), amylase=(220,"U/L"), white_blood_cell_count=(15,"10^9/L")), M45, ["organophosphate_poisoning"], 1),
 ("NMS", U(creatine_kinase_total=(18000,"U/L"), white_blood_cell_count=(17,"10^9/L"), body_temperature=(40.1,"Cel"), serum_iron=(22,"ug/dL"), creatinine=(1.9,"mg/dL"), urine_myoglobin=(1,"1")), {"age_years":28,"sex_at_birth":"male","medications":["haloperidol"]}, ["neuroleptic_malignant_syndrome"], 1),
 ("Ethanol intoxication", U(ethanol=(310,"mg/dL"), osmolal_gap=(68,"mOsm/kg"), glucose=(62,"mg/dL"), potassium=(3.2,"mmol/L"), magnesium=(1.4,"mg/dL"), bicarbonate=(23,"mmol/L"), anion_gap=(12,"mmol/L")), M45, ["alcohol_intoxication"], 1),
 ("Methanol (measured)", U(methanol=(85,"mg/dL"), anion_gap=(30,"mmol/L"), bicarbonate=(8,"mmol/L"), osmolal_gap=(40,"mOsm/kg"), lactate=(3,"mmol/L"), sodium=(140,"mmol/L"), chloride=(102,"mmol/L")), M45, ["methanol_poisoning","methanol_poisoning_pattern"], 1),
 ("Metformin-associated lactic acidosis", U(lactate=(14,"mmol/L"), bicarbonate=(9,"mmol/L"), creatinine=(4.6,"mg/dL"), anion_gap=(30,"mmol/L"), potassium=(5.8,"mmol/L"), glucose=(140,"mg/dL"), procalcitonin=(0.2,"ng/mL"), sodium=(138,"mmol/L"), chloride=(99,"mmol/L")), {"age_years":72,"sex_at_birth":"female","medications":["metformin"]}, ["lactic_acidosis_metformin_associated"], 1),
 # ---------------- inborn errors / neonatal ----------------
 ("Classic galactosemia", U(galactose_one_phosphate_uridyltransferase_galt=(0.4,"U/g{Hb}"), direct_bilirubin=(3.2,"mg/dL"), alanine_aminotransferase=(140,"U/L"), glucose=(38,"mg/dL"), international_normalized_ratio=(2.0,"1"), blood_culture=(1,"1")), {"age_years":0.02,"sex_at_birth":"female"}, ["classic_galactosemia","galactosemia"], 1),
 ("PKU", U(plasma_phenylalanine_quantitative=(22,"mg/dL"), plasma_tyrosine_quantitative=(25,"umol/L")), {"age_years":0.05,"sex_at_birth":"male"}, ["phenylketonuria_pku"], 1),
 ("MSUD", U(leucine_plasma=(2400,"umol/L"), urine_ketones_qualitative=(1,"1"), glucose=(52,"mg/dL"), bicarbonate=(15,"mmol/L"), ammonia=(90,"umol/L")), {"age_years":0.02,"sex_at_birth":"male"}, ["maple_syrup_urine_disease"], 1),
 ("OTC deficiency (urea cycle)", U(ammonia=(680,"umol/L"), alanine_aminotransferase=(40,"U/L"), bicarbonate=(26,"mmol/L"), arterial_pco2=(26,"mm[Hg]"), arterial_ph=(7.52,"[pH]"), orotic_acid_urine=(380,"mmol/mol"), glucose=(80,"mg/dL"), blood_urea_nitrogen=(3,"mg/dL")), {"age_years":0.01,"sex_at_birth":"male"}, ["urea_cycle_disorder","ornithine_transcarbamylase_deficiency","urea_cycle_disorder_otc_deficiency"], 1),
 ("Propionic acidaemia", U(ammonia=(320,"umol/L"), anion_gap=(28,"mmol/L"), bicarbonate=(9,"mmol/L"), glucose=(70,"mg/dL"), urine_ketones_qualitative=(1,"1"), neutrophil_count_absolute=(0.8,"10^9/L"), platelets=(90,"10^9/L"), lactate=(4,"mmol/L"), sodium=(138,"mmol/L"), chloride=(101,"mmol/L")), {"age_years":0.02,"sex_at_birth":"female"}, ["propionic_acidemia","methylmalonic_acidemia","organic_acidemia"], 1),
 ("MCAD deficiency", U(glucose=(28,"mg/dL"), beta_hydroxybutyrate=(0.2,"mmol/L"), urine_ketones_qualitative=(0,"1"), ammonia=(110,"umol/L"), alanine_aminotransferase=(140,"U/L"), uric_acid=(9,"mg/dL"), insulin=(1,"uIU/mL")), {"age_years":1.5,"sex_at_birth":"male"}, ["medium_chain_acyl_coa_dehydrogenase_deficiency"], 1),
 ("GSD Ia (von Gierke)", U(glucose=(38,"mg/dL"), lactate=(7,"mmol/L"), uric_acid=(11,"mg/dL"), triglycerides=(900,"mg/dL"), beta_hydroxybutyrate=(2.0,"mmol/L"), alanine_aminotransferase=(110,"U/L"), total_cholesterol=(300,"mg/dL"), bicarbonate=(16,"mmol/L")), {"age_years":1,"sex_at_birth":"male"}, ["glycogen_storage_disease_type_1","von_gierke_disease"], 1),
 ("Tyrosinaemia type 1", U(succinylacetone_blood_spot_quantitative=(14,"umol/L"), alpha_fetoprotein=(180000,"ng/mL"), international_normalized_ratio=(2.4,"1"), plasma_tyrosine_quantitative=(420,"umol/L"), phosphate=(2.6,"mg/dL")), {"age_years":0.4,"sex_at_birth":"male"}, ["tyrosinemia_type_1"], 1),
 ("Early-onset neonatal sepsis", U(c_reactive_protein=(62,"mg/L"), procalcitonin=(18,"ng/mL"), white_blood_cell_count=(3.1,"10^9/L"), band_neutrophils_percent=(24,"%"), platelets=(88,"10^9/L"), glucose=(36,"mg/dL"), lactate=(5,"mmol/L")), NEO, ["neonatal_sepsis","neonatal_sepsis_support_pattern","sepsis"], 1),
 ("ABO haemolytic disease of newborn", U(coombs_direct_antiglobulin_test=(1,"1"), total_bilirubin=(19,"mg/dL"), direct_bilirubin=(0.6,"mg/dL"), hemoglobin=(11.2,"g/dL"), reticulocyte_percent=(12,"%"), nucleated_red_blood_cells_percent=(25,"%"), lactate_dehydrogenase=(900,"U/L"), spherocytes_percent=(8,"%")), NEO, ["hemolytic_disease_of_the_newborn"], 1),
 ("Neonatal polycythaemia", U(hematocrit=(72,"%"), glucose=(38,"mg/dL"), total_bilirubin=(13,"mg/dL"), platelets=(120,"10^9/L")), NEO, ["neonatal_polycythemia"], 1),
 ("Neonatal hypoglycaemia (hyperinsulinism)", U(glucose=(22,"mg/dL"), insulin=(14,"uIU/mL"), beta_hydroxybutyrate=(0.1,"mmol/L"), cortisol_morning=(18,"ug/dL")), NEO, ["neonatal_hypoglycemia","hyperinsulinemic_hypoglycemia"], 1),
 ("SCID infant", U(lymphocyte_count_absolute=(0.6,"10^9/L"), total_immunoglobulin_g=(120,"mg/dL"), total_immunoglobulin_a=(3,"mg/dL"), total_immunoglobulin_m=(8,"mg/dL"), cd4_t_cells_absolute=(150,"cells/uL")), {"age_years":0.4,"sex_at_birth":"male"}, ["severe_combined_immunodeficiency_scid"], 1),
 ("X-linked agammaglobulinaemia", U(total_immunoglobulin_g=(90,"mg/dL"), total_immunoglobulin_a=(2,"mg/dL"), total_immunoglobulin_m=(6,"mg/dL"), lymphocyte_count_absolute=(3.8,"10^9/L")), {"age_years":2,"sex_at_birth":"male"}, ["x_linked_agammaglobulinemia"], 1),
 ("CVID", U(total_immunoglobulin_g=(280,"mg/dL"), total_immunoglobulin_a=(12,"mg/dL"), total_immunoglobulin_m=(22,"mg/dL"), lymphocyte_count_absolute=(1.6,"10^9/L"), platelets=(80,"10^9/L"), albumin=(3.9,"g/dL")), F26, ["common_variable_immunodeficiency"], 1),
 ("Selective IgA deficiency", U(total_immunoglobulin_a=(2,"mg/dL"), total_immunoglobulin_g=(1100,"mg/dL"), total_immunoglobulin_m=(120,"mg/dL")), CH9, ["selective_iga_deficiency"], 1),
 ("Nutritional rickets", {"alkaline_phosphatase":(980,"U/L"), "phosphate":(2.6,"mg/dL"), "25_hydroxy_vitamin_d":(6,"ng/mL"), "parathyroid_hormone":(210,"pg/mL"), "calcium_total":(8.4,"mg/dL"), "albumin":(4.0,"g/dL")}, {"age_years":1.5,"sex_at_birth":"female"}, ["rickets","rickets_in_children","rickets_support_pattern"], 1),
 ("Turner syndrome (girl)", U(follicle_stimulating_hormone=(88,"IU/L"), estradiol=(8,"pg/mL"), luteinizing_hormone=(32,"IU/L"), anti_mullerian_hormone=(0.05,"ng/mL"), thyroid_stimulating_hormone=(6.2,"mIU/L")), {"age_years":14,"sex_at_birth":"female"}, ["turner_syndrome","turner_syndrome_45x"], 1),
 ("GH deficiency child", U(insulin_like_growth_factor_1=(32,"ng/mL"), growth_hormone=(2.1,"ng/mL"), glucose=(55,"mg/dL"), free_thyroxine=(1.1,"ng/dL"), thyroid_stimulating_hormone=(2.0,"mIU/L"), anti_tissue_transglutaminase_iga=(2,"U/mL"), albumin=(4.2,"g/dL")), {"age_years":7,"sex_at_birth":"male"}, ["growth_hormone_deficiency","growth_hormone_deficiency_pattern","isolated_growth_hormone_deficiency"], 1),
 # ---------------- pregnancy ----------------
 ("Hyperemesis gravidarum", U(urine_ketones_qualitative=(1,"1"), potassium=(2.9,"mmol/L"), bicarbonate=(32,"mmol/L"), thyroid_stimulating_hormone=(0.08,"mIU/L"), free_thyroxine=(2.1,"ng/dL"), alanine_aminotransferase=(78,"U/L"), sodium=(131,"mmol/L"), tsh_receptor_antibody=(0.3,"IU/L")), {"age_years":27,"sex_at_birth":"female","pregnant":True,"gestational_weeks":9}, ["hyperemesis_gravidarum","hyperemesis_gravidarum_metabolic_pattern","gestational_transient_thyrotoxicosis"], 1),
 ("Postpartum thyroiditis", U(thyroid_stimulating_hormone=(0.05,"mIU/L"), thyroid_peroxidase_antibody=(540,"IU/mL"), tsh_receptor_antibody=(0.4,"IU/L"), free_thyroxine=(2.4,"ng/dL"), erythrocyte_sedimentation_rate=(12,"mm/h")), {"age_years":30,"sex_at_birth":"female","conditions":["postpartum 3 months"]}, ["postpartum_thyroiditis","postpartum_thyroiditis_support_pattern"], 1),
 ("Peripartum cardiomyopathy", U(n_terminal_pro_bnp=(5600,"pg/mL"), high_sensitivity_troponin_i=(40,"ng/L"), sodium=(132,"mmol/L"), creatinine=(1.1,"mg/dL"), platelets=(230,"10^9/L"), urine_protein_to_creatinine_ratio=(0.1,"g/g")), {"age_years":33,"sex_at_birth":"female","conditions":["postpartum 2 weeks, dyspnoea"]}, ["peripartum_cardiomyopathy_support_pattern","heart_failure"], 1),
 ("Pregnancy physiological panel (must stay quiet)", U(albumin=(3.1,"g/dL"), creatinine=(0.5,"mg/dL"), alkaline_phosphatase=(240,"U/L"), hemoglobin=(10.8,"g/dL"), blood_urea_nitrogen=(6,"mg/dL"), sodium=(134,"mmol/L"), bicarbonate=(20,"mmol/L"), d_dimer=(1.1,"ug/mL"), platelets=(190,"10^9/L"), uric_acid=(3.8,"mg/dL"), alanine_aminotransferase=(18,"U/L"), ferritin=(40,"ng/mL")), PREG, ["__QUIET__"], 1),  # guard case: no dx may reach p>=0.5
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
            rep = E.interpret(payload, None, pt).to_dict()
            diff = rep["differential_diagnosis"]
            if accept == ["__QUIET__"]:
                rank = 0 if all(x["probability"] < 0.5 for x in diff) else None
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
    print(f"\nHARD2 SCORE {passed}/{n} ({100*passed/max(n,1):.1f}%)  median {times[len(times)//2]:.0f} ms  p95 {times[int(len(times)*0.95)-1]:.0f} ms")
    if fails: print("FAILS:", fails)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
