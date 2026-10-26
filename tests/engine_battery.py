"""Hemoglyph engine regression battery (synthetic textbook presentations).

HONEST SCOPE: these are textbook cases written by the development team and
the engine has been tuned against them. They are a regression/ranking
safety net, NOT a clinical validation and yield no sensitivity/specificity
claim.

Usage:
    python tests/engine_battery.py            # run all, print ranks
    python tests/engine_battery.py --verbose  # show top-5 per case
Exit code 0 when every case meets its expectation.
"""
from __future__ import annotations
import os
import sys
import time
import argparse
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)

# (name, inputs{fid: (value, unit)}, patient, expected ids (any), max_rank)
A = {"age_years": 45, "sex_at_birth": "male"}
F = {"age_years": 38, "sex_at_birth": "female"}
PREG = {"age_years": 29, "sex_at_birth": "female", "pregnant": True}

CASES = [
    # ----- haematology --------------------------------------------------
    ("IDA", {"hemoglobin": (9.8, "g/dL"), "mean_corpuscular_volume": (68, "fL"),
             "ferritin": (6, "ng/mL"), "transferrin_saturation": (8, "%"),
             "red_cell_distribution_width_cv": (19, "%")}, F,
     ["iron_deficiency_anemia"], 1),
    ("Thal trait", {"hemoglobin": (10.9, "g/dL"), "mean_corpuscular_volume": (63, "fL"),
                    "red_blood_cell_count": (6.1, "10^6/uL"), "ferritin": (80, "ng/mL"),
                    "hemoglobin_a2": (5.1, "%")}, A,
     ["thalassemia_trait", "beta_thalassemia_trait", "beta_thalassemia_minor"], 1),
    ("B12 def", {"hemoglobin": (8.9, "g/dL"), "mean_corpuscular_volume": (114, "fL"),
                 "vitamin_b12": (110, "pg/mL"), "lactate_dehydrogenase": (900, "U/L")}, A,
     ["vitamin_b12_deficiency", "megaloblastic_anemia", "pernicious_anemia"], 2),
    ("PV", {"hemoglobin": (18.9, "g/dL"), "hematocrit": (57, "%"), "white_blood_cell_count": (13.2, "10^9/L"),
            "platelets": (520, "10^9/L"), "jak2_v617f_mutation": (1, "1")}, A,
     ["polycythemia_vera"], 1),
    ("CML", {"white_blood_cell_count": (142, "10^9/L"), "platelets": (610, "10^9/L"),
             "basophils_percent": (6, "%"), "bcr_abl1_p210_transcript": (45, "[arb'U]/mL")}, A,
     ["chronic_myeloid_leukemia"], 1),
    ("AML", {"white_blood_cell_count": (38, "10^9/L"), "hemoglobin": (7.9, "g/dL"),
             "platelets": (32, "10^9/L"), "blasts_percent": (46, "%")}, A,
     ["acute_myeloid_leukemia", "acute_leukemia"], 2),
    ("ITP", {"platelets": (18, "10^9/L"), "hemoglobin": (13.6, "g/dL"),
             "white_blood_cell_count": (7.1, "10^9/L")}, F,
     ["immune_thrombocytopenia", "thrombocytopenia"], 2),
    ("Hemochromatosis", {"transferrin_saturation": (78, "%"), "ferritin": (1250, "ng/mL"),
                         "alanine_aminotransferase": (62, "U/L")}, A,
     ["hemochromatosis", "hereditary_hemochromatosis"], 1),
    ("Myeloma", {"serum_protein_electrophoresis_m_spike": (4.2, "g/dL"), "calcium_total": (11.8, "mg/dL"),
                 "creatinine": (2.3, "mg/dL"), "hemoglobin": (8.4, "g/dL"), "albumin": (3.1, "g/dL")}, {"age_years": 68, "sex_at_birth": "male"},
     ["multiple_myeloma"], 1),
    ("DIC", {"platelets": (42, "10^9/L"), "d_dimer": (8.5, "ug/mL"), "prothrombin_time": (22, "s"),
             "fibrinogen": (110, "mg/dL")}, A,
     ["disseminated_intravascular_coagulation"], 1),
    ("Hemolysis", {"hemoglobin": (7.8, "g/dL"), "lactate_dehydrogenase": (1100, "U/L"),
                   "serum_haptoglobin": (5, "mg/dL"), "indirect_bilirubin": (3.1, "mg/dL"),
                   "reticulocyte_percent": (9, "%")}, A,
     ["hemolytic_anemia", "autoimmune_hemolytic_anemia", "hemolysis"], 2),
    # ----- endocrine ----------------------------------------------------
    ("T2DM", {"hemoglobin_a1c": (8.4, "%"), "glucose": (178, "mg/dL"), "triglycerides": (240, "mg/dL")}, A,
     ["type_2_diabetes", "diabetes_mellitus", "type_2_diabetes_mellitus"], 1),
    ("DKA", {"glucose": (486, "mg/dL"), "bicarbonate": (9, "mmol/L"), "arterial_ph": (7.12, "[pH]"),
             "beta_hydroxybutyrate": (6.2, "mmol/L"), "anion_gap": (26, "mmol/L"), "potassium": (5.4, "mmol/L")}, {"age_years": 22, "sex_at_birth": "male"},
     ["diabetic_ketoacidosis"], 1),
    ("HHS", {"glucose": (940, "mg/dL"), "serum_osmolality": (345, "mOsm/kg"), "bicarbonate": (20, "mmol/L"),
             "arterial_ph": (7.36, "[pH]"), "beta_hydroxybutyrate": (0.8, "mmol/L"), "sodium": (150, "mmol/L")}, {"age_years": 74, "sex_at_birth": "female"},
     ["hyperosmolar_hyperglycemic_state"], 2),
    ("Overt hypothyroid", {"thyroid_stimulating_hormone": (38, "uIU/mL"), "free_thyroxine": (0.5, "ng/dL"),
                           "thyroid_peroxidase_antibody": (420, "IU/mL")}, F,
     ["primary_hypothyroidism", "hypothyroidism", "hashimoto_thyroiditis"], 1),
    ("Graves", {"thyroid_stimulating_hormone": (0.01, "uIU/mL"), "free_thyroxine": (3.4, "ng/dL"),
                "tsh_receptor_antibody": (9.8, "IU/L")}, F,
     ["graves_disease", "hyperthyroidism"], 1),
    ("Addison", {"morning_cortisol": (1.8, "ug/dL"), "adrenocorticotropic_hormone": (0.45, "ng/mL"),
                 "sodium": (127, "mmol/L"), "potassium": (5.9, "mmol/L")}, A,
     ["addison_disease", "primary_adrenal_insufficiency", "adrenal_crisis"], 1),
    ("Cushing", {"cortisol_after_dexamethasone": (9.1, "ug/dL"), "urine_free_cortisol_24h": (380, "ug/24h"),
                 "glucose": (168, "mg/dL"), "potassium": (3.1, "mmol/L")}, F,
     ["cushing_syndrome"], 1),
    ("PHPT", {"calcium_total": (11.6, "mg/dL"), "intact_parathyroid_hormone": (142, "pg/mL"),
              "phosphate": (2.1, "mg/dL"), "albumin": (4.1, "g/dL")}, F,
     ["primary_hyperparathyroidism"], 1),
    ("Primary aldosteronism", {"aldosterone": (28, "ng/dL"), "aldosterone_renin_ratio": (62, "ratio"),
                               "potassium": (3.0, "mmol/L"), "sodium": (144, "mmol/L")}, A,
     ["primary_aldosteronism", "primary_hyperaldosteronism"], 1),
    ("Pheo", {"plasma_free_metanephrines": (890, "pg/mL"), "plasma_free_normetanephrines": (2400, "pg/mL"),
              "glucose": (140, "mg/dL")}, A,
     ["pheochromocytoma"], 1),
    ("Prolactinoma", {"prolactin": (410, "ng/mL"), "thyroid_stimulating_hormone": (1.8, "uIU/mL")}, F,
     ["hyperprolactinemia", "prolactinoma"], 1),
    ("Vit D def", {"25_hydroxy_vitamin_d": (7, "ng/mL"), "alkaline_phosphatase": (210, "U/L"),
                   "phosphate": (2.2, "mg/dL"), "calcium_total": (8.6, "mg/dL")}, F,
     ["vitamin_d_deficiency", "osteomalacia"], 1),
    # ----- renal / electrolytes ----------------------------------------
    ("CKD4", {"creatinine": (3.4, "mg/dL"), "egfr_ckd_epi_creatinine": (18, "mL/min/1.73m2"),
              "hemoglobin": (9.6, "g/dL"), "phosphate": (5.8, "mg/dL"), "intact_parathyroid_hormone": (310, "pg/mL"),
              "urine_albumin_to_creatinine_ratio": (650, "mg/g"), "potassium": (5.3, "mmol/L")}, {"age_years": 66, "sex_at_birth": "male"},
     ["chronic_kidney_disease"], 1),
    ("AKI rhabdo", {"creatinine": (4.6, "mg/dL"), "creatine_kinase_total": (48000, "U/L"), "potassium": (6.3, "mmol/L"),
                    "phosphate": (6.9, "mg/dL"), "myoglobin": (9000, "ng/mL")}, {"age_years": 31, "sex_at_birth": "male"},
     ["rhabdomyolysis", "acute_kidney_injury"], 1),
    ("Nephrotic", {"urine_protein_to_creatinine_ratio": (6800, "mg/g"), "albumin": (1.9, "g/dL"),
                   "total_cholesterol": (390, "mg/dL"), "creatinine": (1.0, "mg/dL")}, A,
     ["nephrotic_syndrome"], 1),
    ("SIADH", {"sodium": (119, "mmol/L"), "serum_osmolality": (248, "mOsm/kg"), "urine_osmolality": (520, "mOsm/kg"),
               "urine_sodium": (68, "mmol/L"), "thyroid_stimulating_hormone": (1.5, "uIU/mL"), "morning_cortisol": (16, "ug/dL")}, {"age_years": 70, "sex_at_birth": "female"},
     ["siadh", "hyponatremia"], 1),
    ("TLS", {"uric_acid": (14.2, "mg/dL"), "potassium": (6.4, "mmol/L"), "phosphate": (8.1, "mg/dL"),
             "calcium_total": (6.9, "mg/dL"), "lactate_dehydrogenase": (2800, "U/L"), "creatinine": (2.9, "mg/dL")}, {"age_years": 19, "sex_at_birth": "male"},
     ["tumor_lysis_syndrome"], 1),
    ("Gout", {"uric_acid": (10.8, "mg/dL"), "c_reactive_protein": (48, "mg/L"), "creatinine": (1.1, "mg/dL")}, A,
     ["gout", "hyperuricemia"], 1),
    # ----- hepatic / GI -------------------------------------------------
    ("Acute HBV", {"hepatitis_b_surface_antigen": (1, "1"), "hepatitis_b_core_igm_antibody": (1, "1"),
                   "alanine_aminotransferase": (1450, "U/L"), "total_bilirubin": (6.2, "mg/dL")}, A,
     ["hepatitis_b", "acute_hepatitis_b"], 1),
    ("HAV", {"hepatitis_a_igm_antibody": (1, "1"), "alanine_aminotransferase": (2100, "U/L"),
             "total_bilirubin": (4.8, "mg/dL")}, {"age_years": 12, "sex_at_birth": "male"},
     ["hepatitis_a"], 1),
    ("HCV", {"hepatitis_c_antibody": (1, "1"), "hepatitis_c_rna_quantitative_pcr": (2400000, "IU/mL"),
             "alanine_aminotransferase": (88, "U/L")}, A,
     ["hepatitis_c", "chronic_hepatitis_c"], 1),
    ("Wilson", {"ceruloplasmin": (7, "mg/dL"), "alanine_aminotransferase": (140, "U/L"),
                "urine_copper_24h": (320, "ug/24h"), "total_bilirubin": (2.1, "mg/dL")}, {"age_years": 19, "sex_at_birth": "male"},
     ["wilson_disease"], 1),
    ("Pancreatitis", {"lipase": (1900, "U/L"), "amylase": (820, "U/L"), "white_blood_cell_count": (15, "10^9/L"),
                      "calcium_total": (7.9, "mg/dL")}, A,
     ["acute_pancreatitis"], 1),
    ("Celiac", {"anti_tissue_transglutaminase_iga": (128, "[arb'U]/mL"), "hemoglobin": (10.4, "g/dL"),
                "ferritin": (9, "ng/mL")}, F,
     ["celiac_disease"], 1),
    ("AIH", {"smooth_muscle_antibody": (160, "titer"), "antinuclear_antibody_titer": (320, "titer"),
             "total_immunoglobulin_g": (2900, "mg/dL"), "alanine_aminotransferase": (410, "U/L")}, F,
     ["autoimmune_hepatitis"], 1),
    ("Cirrhosis", {"albumin": (2.4, "g/dL"), "international_normalized_ratio": (1.9, "ratio"), "total_bilirubin": (3.4, "mg/dL"),
                   "platelets": (68, "10^9/L"), "aspartate_aminotransferase": (74, "U/L"), "alanine_aminotransferase": (38, "U/L")}, {"age_years": 58, "sex_at_birth": "male"},
     ["liver_cirrhosis", "cirrhosis"], 1),
    # ----- cardio / resp / infection -----------------------------------
    ("HF", {"n_terminal_pro_bnp": (4800, "pg/mL"), "creatinine": (1.4, "mg/dL"), "sodium": (133, "mmol/L")}, {"age_years": 72, "sex_at_birth": "male"},
     ["heart_failure", "acute_heart_failure_support_pattern"], 1),
    ("PE", {"d_dimer": (4.2, "ug/mL"), "troponin_i": (0.09, "ng/mL"), "n_terminal_pro_bnp": (900, "pg/mL")}, A,
     ["pulmonary_embolism"], 6),
    ("Sepsis", {"lactate": (5.1, "mmol/L"), "procalcitonin": (12, "ng/mL"), "white_blood_cell_count": (21, "10^9/L"),
                "c_reactive_protein": (210, "mg/L"), "creatinine": (2.0, "mg/dL"), "platelets": (90, "10^9/L")}, {"age_years": 64, "sex_at_birth": "female"},
     ["sepsis", "septic_shock"], 1),
    ("Malaria", {"malaria_parasite_blood_smear": (1, "1"), "malaria_thick_smear_parasitemia_percentage": (3.5, "%"),
                 "platelets": (62, "10^9/L"), "hemoglobin": (9.1, "g/dL"), "total_bilirubin": (2.8, "mg/dL")}, A,
     ["malaria"], 1),
    ("HIV", {"hiv_1_and_hiv_2_antigen_antibody": (1, "1"), "lymphocyte_count_absolute": (0.7, "10^9/L")}, A,
     ["hiv_infection", "hiv", "hiv_screening_reactive"], 2),
    # ----- rheum / tox / lipids / pregnancy ----------------------------
    ("SLE", {"antinuclear_antibody_titer": (1280, "titer"), "double_stranded_dna_antibody": (280, "IU/mL"),
             "complement_c3": (42, "mg/dL"), "platelets": (88, "10^9/L"), "urine_protein_to_creatinine_ratio": (900, "mg/g")}, F,
     ["systemic_lupus_erythematosus"], 1),
    ("RA", {"anti_cyclic_citrullinated_peptide_igg": (210, "U/mL"), "rheumatoid_factor": (160, "IU/mL"),
            "c_reactive_protein": (34, "mg/L"), "erythrocyte_sedimentation_rate": (58, "mm/h")}, F,
     ["rheumatoid_arthritis"], 1),
    ("Lead", {"blood_lead": (52, "ug/dL"), "hemoglobin": (10.2, "g/dL"), "mean_corpuscular_volume": (74, "fL")}, {"age_years": 6, "sex_at_birth": "male"},
     ["lead_poisoning"], 1),
    ("FH", {"ldl_cholesterol_calculated": (345, "mg/dL"), "total_cholesterol": (430, "mg/dL"),
            "hdl_cholesterol": (48, "mg/dL"), "triglycerides": (150, "mg/dL")}, {"age_years": 34, "sex_at_birth": "male"},
     ["familial_hypercholesterolemia"], 1),
    ("Severe HTG", {"triglycerides": (2100, "mg/dL"), "total_cholesterol": (310, "mg/dL"), "glucose": (150, "mg/dL")}, A,
     ["hypertriglyceridemia", "severe_hypertriglyceridemia"], 1),
    ("HELLP", {"platelets": (61, "10^9/L"), "aspartate_aminotransferase": (260, "U/L"), "alanine_aminotransferase": (210, "U/L"),
               "lactate_dehydrogenase": (1150, "U/L"), "total_bilirubin": (1.8, "mg/dL"), "creatinine": (1.2, "mg/dL")}, {**PREG, "gestational_weeks": 34},
     ["hellp_syndrome"], 1),
    ("Preeclampsia", {"urine_protein_to_creatinine_ratio": (900, "mg/g"), "creatinine": (1.3, "mg/dL"), "platelets": (140, "10^9/L"),
                      "uric_acid": (7.1, "mg/dL")}, {**PREG, "gestational_weeks": 33},
     ["preeclampsia"], 1),
    ("GDM", {"fasting_plasma_glucose": (98, "mg/dL"), "two_hour_postload_glucose": (171, "mg/dL")}, {**PREG, "gestational_weeks": 26},
     ["gestational_diabetes_mellitus", "gestational_diabetes"], 1),
]


def mk(obs):
    return {k: {"value": v, "unit": u} for k, (v, u) in obs.items()}


def run(verbose=False, only=None):
    import analyse_gidlines as ag
    import calcu
    E = ag.ClinicalRuleEngine()
    D = calcu.DerivedFeatureEngine(os.path.join(ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json"))
    tot = ok = 0
    failures = []
    for name, obs, pt, exp, max_rank in CASES:
        if only and only.lower() not in name.lower():
            continue
        tot += 1
        o = mk(obs)
        try:
            der = D.compute(o, pt).to_dict()["results"]
            derived = {k: {"value": v["value"], "unit": v["unit"]} for k, v in der.items()}
        except Exception:
            derived = {}
        t = time.time()
        d = E.interpret(o, derived, pt).to_dict()
        ms = (time.time() - t) * 1000
        diff = d["differential_diagnosis"]
        hits = [(x["rank"], x["disease_id"]) for x in diff if x["disease_id"] in exp]
        good = bool(hits) and hits[0][0] <= max_rank
        ok += good
        if not good:
            failures.append(name)
        print(f"### {name:<18} ({ms:.0f}ms) ndiff={len(diff):<2} -> {'OK  ' if good else 'MISS'} {hits[:2]}")
        if verbose or not good:
            for x in diff[:5]:
                eb = f"  <- {x.get('explained_by')}" if x.get("explained_by") else ""
                print(f"   #{x['rank']} {x['disease_id']:<46} p={x['probability']:.2f} {x['evidence_state']}{eb}")
    print(f"SCORE {ok}/{tot}" + (f"  failures: {failures}" if failures else ""))
    return ok == tot


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.exit(0 if run(a.verbose, a.only) else 1)
