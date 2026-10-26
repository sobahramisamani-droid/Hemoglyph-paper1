"""Healthy-panel false-positive sweep (wide panel incl. ESL-extension analytes).

Generates N random in-range panels (adult + paediatric + pregnant) across ~110
analytes and asserts: no expert syndrome fires (except explicit *_guard), and
no disease reaches probability >= 0.5.

Usage: python tests/healthy_sweep.py [--n 200] [--seed 1] [--verbose]
"""
from __future__ import annotations
import os, sys, random, argparse, logging
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)

# adult reference intervals (Tietz / UpToDate); value = (lo, hi, unit)
REF = {
 "hemoglobin": (12.5, 15.5, "g/dL"), "hematocrit": (37, 46, "%"), "mean_corpuscular_volume": (82, 96, "fL"), "red_cell_distribution_width_cv": (11.5, 14.0, "%"),
 "white_blood_cell_count": (4.5, 10.0, "10^9/L"), "platelets": (160, 380, "10^9/L"), "neutrophil_count_absolute": (2.0, 6.5, "10^9/L"), "lymphocyte_count_absolute": (1.2, 3.2, "10^9/L"),
 "eosinophil_count_absolute": (0.05, 0.4, "10^9/L"), "monocyte_count_absolute": (0.2, 0.8, "10^9/L"), "reticulocyte_percent": (0.6, 1.8, "%"),
 "glucose": (74, 98, "mg/dL"), "hemoglobin_a1c": (4.8, 5.5, "%"), "creatinine": (0.65, 1.05, "mg/dL"), "blood_urea_nitrogen": (8, 19, "mg/dL"), "cystatin_c": (0.6, 0.95, "mg/L"),
 "sodium": (137, 143, "mmol/L"), "potassium": (3.7, 4.9, "mmol/L"), "chloride": (99, 106, "mmol/L"), "bicarbonate": (23, 27, "mmol/L"), "magnesium": (1.8, 2.3, "mg/dL"), "phosphate": (2.7, 4.3, "mg/dL"),
 "calcium_total": (8.9, 10.1, "mg/dL"), "albumin": (3.9, 4.8, "g/dL"), "total_protein": (6.4, 8.0, "g/dL"), "uric_acid": (3.0, 6.5, "mg/dL"),
 "alanine_aminotransferase": (10, 35, "U/L"), "aspartate_aminotransferase": (12, 32, "U/L"), "alkaline_phosphatase": (45, 115, "U/L"), "gamma_glutamyl_transferase": (10, 45, "U/L"),
 "total_bilirubin": (0.3, 1.0, "mg/dL"), "direct_bilirubin": (0.05, 0.25, "mg/dL"), "lactate_dehydrogenase": (130, 230, "U/L"), "creatine_kinase_total": (40, 180, "U/L"),
 "amylase": (30, 100, "U/L"), "lipase": (10, 50, "U/L"), "ammonia": (12, 40, "umol/L"), "lactate": (0.6, 1.8, "mmol/L"),
 "total_cholesterol": (140, 195, "mg/dL"), "triglycerides": (60, 145, "mg/dL"), "hdl_cholesterol": (42, 75, "mg/dL"), "ldl_cholesterol_calculated": (70, 125, "mg/dL"),
 "ferritin": (30, 200, "ng/mL"), "serum_iron": (60, 150, "ug/dL"), "transferrin_saturation": (22, 42, "%"), "vitamin_b12": (300, 800, "pg/mL"), "folate_serum": (6, 18, "ng/mL"),
 "25_hydroxy_vitamin_d": (32, 60, "ng/mL"), "parathyroid_hormone": (18, 60, "pg/mL"), "zinc": (70, 115, "ug/dL"), "copper": (80, 140, "ug/dL"), "vitamin_c": (0.6, 1.6, "mg/dL"),
 "thyroid_stimulating_hormone": (0.6, 3.8, "mIU/L"), "free_thyroxine": (0.9, 1.6, "ng/dL"), "thyroid_peroxidase_antibody": (2, 25, "IU/mL"), "cortisol_morning": (8, 18, "ug/dL"),
 "prolactin": (4, 20, "ng/mL"), "insulin_like_growth_factor_1": (110, 250, "ng/mL"), "c_reactive_protein": (0.3, 4.5, "mg/L"), "erythrocyte_sedimentation_rate": (2, 18, "mm/h"), "procalcitonin": (0.02, 0.08, "ng/mL"),
 "prothrombin_time": (11, 13.5, "s"), "international_normalized_ratio": (0.9, 1.15, "1"), "activated_partial_thromboplastin_time": (25, 34, "s"), "fibrinogen": (210, 380, "mg/dL"), "d_dimer": (0.1, 0.45, "ug/mL"),
 "factor_viii_activity": (60, 140, "%"), "factor_ix_activity": (60, 140, "%"), "factor_xi_activity": (65, 140, "%"), "protein_c_activity": (75, 140, "%"), "protein_s_activity": (65, 135, "%"),
 "high_sensitivity_troponin_i": (1, 12, "ng/L"), "n_terminal_pro_bnp": (10, 110, "pg/mL"), "digoxin": (0.6, 1.1, "ng/mL"), "lithium": (0.5, 0.9, "mmol/L"), "valproic_acid_total": (55, 95, "ug/mL"),
 "theophylline": (6, 14, "ug/mL"), "carbamazepine": (5, 10, "ug/mL"), "phenytoin_total": (10, 18, "ug/mL"), "ethanol": (0, 0, "mg/dL"), "carboxyhemoglobin_fraction": (0.3, 1.8, "%"), "cholinesterase": (5500, 11000, "U/L"),
 "total_immunoglobulin_g": (750, 1500, "mg/dL"), "total_immunoglobulin_a": (90, 320, "mg/dL"), "total_immunoglobulin_m": (50, 220, "mg/dL"), "total_immunoglobulin_e": (5, 90, "IU/mL"), "serum_igg4": (10, 110, "mg/dL"),
 "complement_c3": (92, 160, "mg/dL"), "complement_c4": (16, 38, "mg/dL"), "rheumatoid_factor": (2, 12, "IU/mL"), "antinuclear_antibody_titer": (0, 0, "{titer}"),
 "tryptase_serum": (2, 9, "ng/mL"), "beta_2_microglobulin": (1.0, 2.2, "mg/L"), "carcinoembryonic_antigen": (0.5, 2.8, "ng/mL"), "ca_19_9": (2, 30, "U/mL"), "alpha_fetoprotein": (1, 7, "ng/mL"),
 "hemoglobin_a2": (2.2, 3.2, "%"), "hemoglobin_f": (0.1, 0.9, "%"), "hemoglobin_s": (0, 0, "%"), "blood_lead": (0.3, 2.5, "ug/dL"), "fgf23": (30, 90, "RU/mL"),
 "fecal_calprotectin": (5, 45, "ug/g"), "fecal_elastase_1": (250, 500, "ug/g"), "urine_protein_to_creatinine_ratio": (0.02, 0.12, "g/g"), "urine_red_blood_cells_per_hpf": (0, 2, "/[HPF]"),
 "coombs_direct_antiglobulin_test": (0, 0, "1"), "blood_culture": (0, 0, "1"), "hepatitis_c_antibody": (0, 0, "1"), "hepatitis_b_surface_antigen": (0, 0, "1"), "cryoglobulin": (0, 0, "1"),
 "glomerular_basement_membrane_antibody": (0, 0, "1"), "rnp_antibody": (0, 0, "1"), "anti_histone_antibody": (0, 0, "1"), "anti_intrinsic_factor_antibody_igg": (0, 0, "1"), "hla_b27_antigen_allele": (0, 0, "1"),
 "glucagon": (50, 140, "pg/mL"), "vasoactive_intestinal_peptide": (10, 55, "pg/mL"), "plasma_phenylalanine_quantitative": (0.6, 1.8, "mg/dL"), "leucine_plasma": (70, 170, "umol/L"),
 "vitamin_b6_pyridoxal_five_phosphate": (25, 90, "nmol/L"), "vitamin_b1_thiamine_whole_blood": (80, 180, "nmol/L"), "osmolal_gap": (-4, 7, "mOsm/kg"), "anion_gap": (7, 13, "mmol/L"),
}
SEX_ADJ = {"male": {"hemoglobin": (13.8, 17.0), "hematocrit": (41, 50), "ferritin": (40, 280), "uric_acid": (3.8, 7.0), "creatinine": (0.8, 1.2)}}
PED_ADJ = {"alkaline_phosphatase": (150, 380), "phosphate": (4.0, 5.8), "lymphocyte_count_absolute": (2.5, 7.0), "insulin_like_growth_factor_1": (60, 220), "hemoglobin": (12.0, 14.0), "creatinine": (0.3, 0.6), "blood_urea_nitrogen": (6, 16), "white_blood_cell_count": (5.5, 13.0)}
PREG_ADJ = {"hemoglobin": (10.8, 13.0), "albumin": (3.0, 3.6), "alkaline_phosphatase": (120, 300), "creatinine": (0.45, 0.75), "d_dimer": (0.5, 1.6), "bicarbonate": (19, 23), "sodium": (133, 138), "blood_urea_nitrogen": (4, 11), "thyroid_stimulating_hormone": (0.2, 2.8), "fibrinogen": (380, 560), "white_blood_cell_count": (7, 14), "uric_acid": (2.5, 4.5), "total_cholesterol": (180, 280), "triglycerides": (120, 260), "cortisol_morning": (15, 35), "prolactin": (40, 180)}


def panel(rng, kind, sex, n_analytes, age=30):
    ref = dict(REF)
    if sex == "male": ref.update({k: (lo, hi, REF[k][2]) for k, (lo, hi) in SEX_ADJ["male"].items()})
    if kind == "child":
        ref.update({k: (lo, hi, REF[k][2]) for k, (lo, hi) in PED_ADJ.items()})
        if age >= 12: ref["lymphocyte_count_absolute"] = (1.5, 4.5, "10^9/L"); ref["hemoglobin"] = (12.5, 15.0, "g/dL"); ref["phosphate"] = (3.2, 5.2, "mg/dL")
        elif age >= 6: ref["lymphocyte_count_absolute"] = (1.8, 6.0, "10^9/L")
    if kind == "preg": ref.update({k: (lo, hi, REF[k][2]) for k, (lo, hi) in PREG_ADJ.items()})
    keys = list(ref); rng.shuffle(keys); keys = keys[:n_analytes]
    obs = {}
    for k in keys:
        lo, hi, u = ref[k]; w = hi - lo
        v = rng.uniform(lo + 0.1 * w, hi - 0.1 * w) if w > 0 else lo
        obs[k] = {"value": round(v, 3), "unit": u}
    return obs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=200); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--verbose", action="store_true"); a = ap.parse_args()
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(); rng = random.Random(a.seed)
    syn_hits = 0; dx_hits = 0; worst = (0.0, None, None); unknown = set(REF) - set(E.registry.features)
    if unknown: print("WARNING unknown analytes ignored:", sorted(unknown))
    for i in range(a.n):
        kind = rng.choice(["adult", "adult", "adult", "child", "preg"])
        if kind == "child": pt = {"age_years": rng.choice([2, 5, 9, 13]), "sex_at_birth": rng.choice(["male", "female"])}
        elif kind == "preg": pt = {"age_years": rng.randint(22, 38), "sex_at_birth": "female", "pregnant": True, "gestational_weeks": rng.randint(12, 38)}
        else: pt = {"age_years": rng.randint(18, 85), "sex_at_birth": rng.choice(["male", "female"])}
        sex = pt["sex_at_birth"]
        obs = panel(rng, kind, sex, rng.choice([8, 15, 25, 40, 60, len(REF)]), age=pt["age_years"])
        rep = E.interpret(obs, None, pt).to_dict()
        syns = [h["syndrome_id"] for h in rep["expert_syndromes"] if not h.get("guard")]
        top = rep["differential_diagnosis"][:1]
        p = top[0]["probability"] if top else 0.0
        if syns: syn_hits += 1; print(f"[SYN] #{i} {kind}/{sex} {syns}")
        if p >= 0.5: dx_hits += 1; print(f"[DX ] #{i} {kind}/{sex} {top[0]['disease_id']} p={p}")
        if p > worst[0]: worst = (p, top[0]["disease_id"], i)
        if a.verbose: print(f"#{i} {kind}/{sex} n={len(obs)} top={top[0]['disease_id'] if top else None} p={p}")
    print(f"\nHEALTHY SWEEP n={a.n}: syndrome false-fires={syn_hits}  dx>=0.5={dx_hits}  worst p={worst[0]:.2f} ({worst[1]} #{worst[2]})")
    return 0 if (syn_hits == 0 and dx_hits == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
