try:
    from models_scientific_references import (
        get_reference_for_model,
        BASE_AND_EXPANDED_REFERENCES,
        SPECIALIZED_DISEASE_REFERENCES,
        COHORT_SPECIALTY_PAPERS,
    )
except ImportError:
    BASE_AND_EXPANDED_REFERENCES = {}
    SPECIALIZED_DISEASE_REFERENCES = {}
    COHORT_SPECIALTY_PAPERS = {}
    def get_reference_for_model(disease_key: str, model_title: str = '') -> dict:
        return {}

import math
from math import log as _math_log, exp as _math_exp, sqrt as _math_sqrt
import re
from typing import Mapping, Optional, Any, Dict, List, Set, Tuple
from dataclasses import is_dataclass, asdict
ENGINE_VERSION = "2.1.1-corrected"
def _num(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if hasattr(value, "value"):
        return _num(getattr(value, "value"))
    if isinstance(value, dict) and "value" in value:
        return _num(value["value"])
    try:
        s = str(value).strip()
        if s == '':
            return None
        # FIX P1: distinguish thousands separators from decimal commas.
        # "1,234.56"/"250,000" -> strip commas; "5,7" -> decimal point.
        if "," in s:
            if "." in s:
                s = s.replace(",", "")
            elif re.fullmatch(r"[+-]?\d{1,3}(,\d{3})+", s):
                s = s.replace(",", "")
            elif re.fullmatch(r"[+-]?\d+,\d{1,2}", s):
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        return float(s)
    except (ValueError, TypeError):
        return None


import threading as _threading

_IMPUTE_STATE = _threading.local()


def _impute_bazneshani():
    _IMPUTE_STATE.records = []


def _impute_sabt(field, default, tier):
    recs = getattr(_IMPUTE_STATE, 'records', None)
    if recs is None:
        recs = []
        _IMPUTE_STATE.records = recs
    recs.append({"field": field, "assumed": default, 'tier': tier})


def _impute_records():
    return list(getattr(_IMPUTE_STATE, "records", []) or [])


CRITICAL_IMPUTE_FIELDS = frozenset({
    "RespiratoryRate", "SpO2", "Heart_Rate", "TemperatureC", "GCS",
    "Systolic_BP", "Diastolic_BP", 'MAP', "Arterial_pH", "PaO2",
    "PaO2_FiO2", "Lactate", "Bicarbonate", "INR", "ProthrombinTime",
    "Creatinine", "Bilirubin", "TotalBilirubin", "Albumin", "Platelets",
    "eGFR", "Age", "WBC", "Sodium", "Potassium", "Urine_Output",
    "ECOG_PerformanceStatus", "ISS_Stage",
})


def num_or_assume(canon, dataset, patient, default, tier='context'):
    v = adad(canon, dataset, patient)
    if v is not None:
        return v
    if tier == "auto":
        tier = "critical" if canon in CRITICAL_IMPUTE_FIELDS else "context"
    _impute_sabt(canon, default, tier)
    return default


def flag_or_assume(canon, patient, default=0, tier="context"):
    v = parcham_bimar(canon, patient)
    if v is not None:
        return v
    if tier == 'auto':
        tier = "critical" if canon in CRITICAL_IMPUTE_FIELDS else "context"
    _impute_sabt(canon, default, tier)
    return default


def _safe_log(x: Any, floor: float = 1e-6) -> float:
    """Safe Logarithm with strict domain guard against non-positive numbers."""
    try:
        val = float(x)
        if not math.isfinite(val) or val <= 0:
            return _math_log(floor)
        return _math_log(max(val, floor))
    except (TypeError, ValueError):
        return _math_log(floor)


def _safe_log10(x: Any, floor: float = 1e-6) -> float:
    """Safe Base-10 Logarithm with strict domain guard against non-positive numbers."""
    try:
        val = float(x)
        if not math.isfinite(val) or val <= 0:
            return math.log10(floor)
        return math.log10(max(val, floor))
    except (TypeError, ValueError):
        return math.log10(floor)


def _safe_exp(x: Any) -> float:
    """Safe Exponential with overflow guard (-700 <= x <= 700)."""
    try:
        val = float(x)
        if not math.isfinite(val):
            return 1.0
        val = max(min(val, 700.0), -700.0)
        return _math_exp(val)
    except (TypeError, ValueError, OverflowError):
        return 1.0


def _safe_sqrt(x: Any, floor: float = 0.0) -> float:
    """Safe Square Root with non-negative domain guard."""
    try:
        val = float(x)
        if not math.isfinite(val) or val < 0:
            return _math_sqrt(floor)
        return _math_sqrt(max(val, floor))
    except (TypeError, ValueError):
        return _math_sqrt(floor)


def _safe_div(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """Safe Division with zero-denominator guard."""
    try:
        num = float(numerator)
        den = float(denominator)
        if not math.isfinite(num) or not math.isfinite(den) or abs(den) < 1e-12:
            return default
        return num / den
    except (TypeError, ValueError, ZeroDivisionError):
        return default

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def sigmoid(x):
    if x >= 0:
        z = _safe_exp(-x)
        return 1.0 / (1.0 + z)
    z = _safe_exp(x)
    return z / (1.0 + z)


def logit_to_prob(intercept_plus_lp):
    return _clamp(sigmoid(intercept_plus_lp), 0.0, 1.0)


def chol_mmol(mg_dl):
    """Convert cholesterol from mg/dL to mmol/L safely without double-converting."""
    if mg_dl is None:
        return None
    v = _num(mg_dl)
    if v is None:
        return None
    if 0.5 <= v <= 25.0:
        return v
    return v / 38.67


def glu_mmol(mg_dl):
    """Convert glucose from mg/dL to mmol/L safely without double-converting."""
    if mg_dl is None:
        return None
    v = _num(mg_dl)
    if v is None:
        return None
    if 1.0 <= v <= 35.0:
        return v
    return v / 18.016


def bili_umol(mg_dl):
    """Convert bilirubin from mg/dL to umol/L safely without double-converting."""
    if mg_dl is None:
        return None
    v = _num(mg_dl)
    if v is None:
        return None
    if v > 6.0:
        return v
    return v * 17.1


def risk_band_from_thresholds(prob, bands):
    for upper, label in bands:
        if prob < upper:
            return label
    return bands[-1][1]


def four_sath(prob, moderate, high, very_high):
    if prob >= very_high:
        return "Very High"
    if prob >= high:
        return "High"
    if prob >= moderate:
        return "Moderate"
    return "Low"


# ==============================================================================
# Comprehensive Canonical Field & Patient Aliases
# ==============================================================================

FIELD_ALIASES = {
    'Age': ["Age", "age", "PatientAge", "age_years", "AgeYears"],
    "Sex": ["Sex", "sex", "Gender", "gender", "sex_at_birth", "SexAtBirth", "jensiat"],
    "HeightCm": ["Height", "HeightCm", "height_cm", "height", "Height_cm", "PatientHeight"],
    "WeightKg": ["Weight", "WeightKg", "weight_kg", "weight", "Weight_kg", "PatientWeight"],
    "BMI": ["BMI", "bmi", "body_mass_index", "BodyMassIndex"],
    "Waist": ["Waist", "WaistCm", "WaistCircumference", "waist_cm", "waist", "waist_circumference"],
    "Hip": ["Hip", "HipCm", "hip_cm", "hip", "hip_circumference"],
    "Systolic_BP": ["Systolic_BP", "SBP", "sbp", "systolic_bp", "SystolicBP", "systolic_blood_pressure", "blood_pressure_systolic", "Systolic"],
    "Diastolic_BP": ["Diastolic_BP", "DBP", "dbp", "diastolic_bp", "DiastolicBP", "diastolic_blood_pressure", "blood_pressure_diastolic", "Diastolic"],
    "Heart_Rate": ["Heart_Rate", "HR", "hr", "pulse", "Pulse", "heart_rate", "pulse_rate"],
    "Smoking": ["Smoking", "smoking", "CurrentSmoker", "current_smoker", "smoking_status", "tobacco", "smoker"],
    'BpTreated': ["BpTreated", "OnAntihypertensive", "HypertensionMeds", "BP_Treated", "HTN_Treatment", "AntihypertensiveUse", "bp_treated", "antihypertensive", "antihypertensives", "hypertension_meds"],
    'Race': ["Race", "race", "Ethnicity", "ethnicity"],

    'FBS': ["FBS", "fbs", "FPG", "fpg", "fasting_plasma_glucose", "FastingGlucose", "fasting_glucose", "fasting_blood_glucose", "Glucose_F", "GlucoseFasting"],
    "Glucose": ["Glucose", "glucose", "random_plasma_glucose", "RBS", "rbs", "blood_glucose", "BloodGlucose"],
    "HbA1c": ["HbA1c", "hba1c", "A1C", "a1c", "hemoglobin_a1c", "HemoglobinA1c", "glycated_hemoglobin"],
    "Insulin": ["Insulin", "insulin", "fasting_insulin", "fasting_serum_insulin", "insulin_fasting"],
    "CPeptide": ["C_Peptide", "c_peptide", "CPeptide", "cpeptide"],
    "OGTT2h": ["OGTT_2h", "two_hour_postload_glucose", "OGTT2h", "ogtt_2h", "ogtt2h"],

    "TotalCholesterol": ["TotalCholesterol", "total_cholesterol", "Total_Cholesterol", "TC", "tc", "cholesterol", "Cholesterol"],
    "TC_mmol": ["TC_mmol", "total_cholesterol_mmol", "tc_mmol"],
    'HDL': ["HDL", "hdl", "HDL_C", "hdl_c", "hdl_cholesterol", "HDL_cholesterol", "cholesterol_hdl", "HDLCholesterol"],
    "HDL_mmol": ["HDL_mmol", "hdl_cholesterol_mmol", "hdl_mmol"],
    "LDL": ["LDL", "ldl", "LDL_C", "ldl_c", "ldl_cholesterol", "LDL_cholesterol", "ldl_cholesterol_calculated", "ldl_cholesterol_direct", "cholesterol_ldl", "LDLCholesterol"],
    "LDL_mmol": ["LDL_mmol", "ldl_mmol"],
    "NonHDL": ["NonHDL", "non_hdl", "non_hdl_cholesterol", "Non_HDL_C", "nonhdl"],
    "Triglycerides": ["Triglycerides", "triglycerides", "TG", "tg", "Triglyceride", "triglyceride"],
    "TG_mmol": ["TG_mmol", "triglycerides_mmol", "tg_mmol"],
    "LpA": ["LpA", "lpa", "lipoprotein_a", "LipoproteinA"],
    "ApoB": ["ApoB", "apob", "apolipoprotein_b", "ApolipoproteinB"],

    "Creatinine": ["Creatinine", "creatinine", "Cr", "cr", "SCr", "scr", "SerumCreatinine", "serum_creatinine"],
    "BUN": ["BUN", "bun", "blood_urea_nitrogen", "BloodUreaNitrogen", "Urea_N"],
    "Urea": ["Urea", "urea", "blood_urea", "serum_urea"],
    'eGFR': ["eGFR", "egfr", "egfr_ckd_epi_creatinine", "egfr_ckd_epi_creatinine_cystatin_c", "GFR", "gfr", "egfr_ckd_epi_2021", "egfr_ckd_epi"],
    "ACR": ["ACR", "acr", "urine_albumin_to_creatinine_ratio", "UACR", "uACR", "uacr", "albumin_creatinine_ratio"],
    "Albumin_Urine": ["Albumin_Urine", "urine_albumin", "microalbumin_urine"],
    "Proteinuria24h": ["Proteinuria24h", "urine_protein_24_hour", "proteinuria_24h"],
    "PCR": ["PCR", "pcr", "urine_protein_to_creatinine_ratio", "UPCR", "upcr"],
    'CystatinC': ["CystatinC", "cystatinc", "cystatin_c", "Cystatin_C"],
    "Sodium": ["Sodium", "sodium", "Na", "na"],
    "Potassium": ["Potassium", "potassium", "K", "k"],
    "Bicarbonate": ["Bicarbonate", "bicarbonate", "HCO3", "hco3"],
    "Calcium": ["Calcium", "calcium", "Ca", "ca", "calcium_total", "serum_calcium"],
    'Phosphate': ["Phosphate", "phosphate", "Phos", "phos", "Phosphorus", "phosphorus", "P", "p", "phosphate_inorganic"],
    "Uric_Acid": ["Uric_Acid", "uric_acid", "UricAcid", "uricacid", "Urate", "urate", "serum_uric_acid"],

    "ALT": ["ALT", "alt", "alanine_aminotransferase", "SGPT", "sgpt"],
    "AST": ["AST", "ast", "aspartate_aminotransferase", "SGOT", "sgot"],
    "AST_ULN": ["AST_ULN", "ast_uln", "ASTULN"],
    'ALT_ULN': ["ALT_ULN", "alt_uln", "ALTULN"],
    "ALP": ["ALP", "alp", "alkaline_phosphatase", "alk_phos", "AlkalinePhosphatase"],
    "GGT": ["GGT", "ggt", "gamma_glutamyl_transferase", "GammaGT", "gamma_gt"],
    'Bilirubin': ["Bilirubin", "bilirubin", "Total_Bilirubin", "total_bilirubin", "TBili", "tbili", "TotalBilirubin", "bilirubin_total"],
    "Direct_Bilirubin": ["Direct_Bilirubin", "direct_bilirubin", "DirectBilirubin", "DBili", "bilirubin_direct"],
    'Albumin': ["Albumin", "albumin", "serum_albumin", "AlbuminSerum"],
    'Total_Protein': ["Total_Protein", "total_protein", "TotalProtein", "total_protein_serum", "serum_protein"],
    "AFP": ["AFP", "afp", "alpha_fetoprotein"],
    "AFPL3": ["AFPL3", "afpl3", "AFP_L3", "afp_l3", "afp_l3_percent"],
    "DCP": ["DCP", "dcp", "PIVKA_II", "pivka_ii", "des_gamma_carboxy_prothrombin"],

    "Hb": ["Hb", "hb", "Hemoglobin", "hemoglobin", "Hgb", "hgb"],
    "Hct": ["Hct", "hct", "Hematocrit", "hematocrit", "PCV", "pcv"],
    "MCV": ["MCV", "mcv", "mean_corpuscular_volume"],
    'Platelets': ["Platelets", "platelets", "platelet", "platelet_count", "PLT", "plt", "Plt"],
    "WBC": ["WBC", "wbc", "white_blood_cell_count", "WBC_Count", "wbc_count", "leukocytes"],
    "Ferritin": ["Ferritin", "ferritin", "serum_ferritin"],
    "SerumIron": ["SerumIron", "serum_iron", "Iron", "iron", "Fe", "fe"],
    "TIBC": ["TIBC", "tibc", "total_iron_binding_capacity"],
    "TSAT": ["TSAT", "tsat", "transferrin_saturation", "TransferrinSaturation"],
    "CRP": ["CRP", "crp", "c_reactive_protein"],
    "hsCRP": ["hsCRP", "hscrp", "high_sensitivity_c_reactive_protein", "hs_CRP", "hs_crp"],
    "ESR": ["ESR", "esr", "erythrocyte_sedimentation_rate"],

    'TSH': ["TSH", "tsh", "thyroid_stimulating_hormone"],
    "FT4": ["FT4", "ft4", "free_thyroxine", "Free_T4", "free_t4"],
    "Anti_TPO": ["Anti_TPO", "anti_tpo", "TPO_Ab", "tpo_ab", "thyroid_peroxidase_antibody"],
    'Aldosterone': ["Aldosterone", "aldosterone"],
    'Renin_PRA': ["Renin_PRA", "PRA", "pra", "plasma_renin_activity"],
    'Renin_DRC': ["Renin_DRC", "DRC", "drc", "direct_renin_concentration"],

    "INR": ["INR", "inr", "international_normalized_ratio"],
    "PT": ["PT", "pt", "prothrombin_time", "PT_seconds"],
    'PT_ULN': ["PT_ULN", "pt_uln", "pt_upper_limit"],
    "DDimer": ["DDimer", "ddimer", "d_dimer", "D_Dimer"],
    "Fibrinogen": ["Fibrinogen", "fibrinogen"],

    "NTproBNP": ["NTproBNP", "ntprobnp", "NT_proBNP", "nt_probnp", "nt_pro_bnp"],
    'BNP': ["BNP", "bnp", "b_type_natriuretic_peptide", "brain_natriuretic_peptide"],
    "Troponin": ["Troponin", "troponin", "troponin_i", "troponin_t", "high_sensitivity_troponin_i", "high_sensitivity_troponin_t"],
    "Troponin_I": ["Troponin_I", "troponin_i", "Troponin", "troponin", "troponin_t"],
    "Troponin_ULN": ["Troponin_ULN", "troponin_uln"],
    "PSA": ["PSA", "psa", "total_prostate_specific_antigen", "total_psa"],
    "FreePSA_ratio": ["FreePSA_ratio", "free_to_total_psa_ratio", "FreePSA_Ratio", "free_psa_ratio"],

    "PHI": ["PHI", "phi", "prostate_health_index"],
    "CA125": ["CA125", "ca125", "ca_125"],
    "HE4": ["HE4", "he4", "human_epididymis_protein_4"],
    "ROMA": ["ROMA", "roma", "risk_of_ovarian_malignancy_algorithm"],
    "CEA": ["CEA", "cea", "carcinoembryonic_antigen"],
    'LDH': ["LDH", "ldh", "lactate_dehydrogenase"],

    "HBsAg": ["HBsAg", "hbsag", "hepatitis_b_surface_antigen"],
    "HBeAg": ["HBeAg", "hbeag", "hepatitis_b_e_antigen"],
    "HBV_DNA_IU": ["HBV_DNA_IU", "HBV_DNA", "hbv_dna", "hepatitis_b_viral_load", "HBVDNA_IU"],

    "VitD": ["VitD", "vitd", "VitaminD", "vitamin_d", "25_hydroxy_vitamin_d", "VitD_25OH"],
    "B12": ["B12", "b12", "vitamin_b12", "cobalamin"],
    'Folate': ["Folate", "folate", "folate_serum", "folic_acid"],
    "Homocysteine": ["Homocysteine", "homocysteine"],
    'Ammonia': ["Ammonia", "ammonia"],

    "UACR": ["UACR", "uacr", "uACR", "urine_albumin_to_creatinine_ratio", "ACR", "acr"],
    'Hematocrit': ["Hematocrit", "hematocrit", "Hct", "hct", "PCV"],
    "UricAcid": ["UricAcid", "uricacid", "uric_acid", "Uric_Acid", "urate"],
    "Arterial_pH": ["Arterial_pH", "arterial_ph", "pH", "ph"],
    "Lactate": ["Lactate", "lactate", "lactic_acid"],
    "ProthrombinTime": ["ProthrombinTime", "prothrombin_time", "PT", "pt", "PT_seconds"],
    "RespiratoryRate": ["RespiratoryRate", "respiratory_rate", "RR", "rr"],
    "TemperatureC": ["TemperatureC", "temperature_c", "Temp_C", "temperature", "temp"],
    'GCS': ["GCS", "gcs", "glasgow_coma_scale"],
    'MAP': ["MAP", "map", "mean_arterial_pressure", "MeanBP"],
    "PaO2_FiO2": ["PaO2_FiO2", "pao2_fio2", "P_F_ratio", "PF_ratio"],
    "SpO2": ["SpO2", "spo2", "oxygen_saturation", "o2_sat"],
    "PaO2": ["PaO2", "pao2"],
    "NT_proBNP": ["NT_proBNP", "nt_pro_bnp", "NTproBNP", "ntprobnp"],
    "Beta2Microglobulin": ["Beta2Microglobulin", "beta2_microglobulin", "B2M", "b2m"],
    'LiverStiffness_kPa': ["LiverStiffness_kPa", "liver_stiffness_kpa", "LSM_kPa", "elastography_kPa"],
    'CAP_dB_m': ["CAP_dB_m", "cap_db_m", "CAP", "controlled_attenuation_parameter"],
    "CancerSiteScore": ["CancerSiteScore", "cancer_tumor_site_score"],
    "D_Dimer": ["D_Dimer", "d_dimer", "DDimer", "ddimer"],
    "Reticulocytes": ["Reticulocytes", "reticulocytes", "Retic", "retic_percent", "reticulocyte_count"],
    "TotalBilirubin": ["TotalBilirubin", "total_bilirubin", "Bilirubin", "bilirubin", "Total_Bilirubin", "TBili"],
}

PATIENT_ALIASES = {
    "FamilyHistory_DM": ["FamilyHistory_DM", "FH_DM", "DiabetesFamilyHistory", "family_history_dm", "fh_dm"],
    "FamilyHistory_CAD": ["FamilyHistory_CAD", "FH_CAD", "family_history_cad", "fh_cad"],
    "FamilyHistory_Stroke": ["FamilyHistory_Stroke", "family_history_stroke"],
    "FamilyHistory_HCC": ["FamilyHistory_HCC", "family_history_hcc"],
    "FamilyHistory_LungCa": ["FamilyHistory_LungCa", "FH_LungCancer", "family_history_lung_cancer"],
    "PhysicalActivity": ["PhysicalActivity", "physical_activity", "ActiveLife", "exercise"],
    "DailyFruitVeg": ["DailyFruitVeg", "fruit_veg_daily", "fruit_and_vegetables"],
    "HxHighGlucose": ["HxHighGlucose", "hx_high_glucose", "history_high_glucose"],
    "GestationalDM": ["GestationalDM", "hx_gdm", "gestational_diabetes", "gestational_dm"],
    "DiabetesFlag": ["Diabetes", "DiabetesFlag", "DM", "hx_diabetes", "diabetes_flag", "has_diabetes"],
    "AF": ["AF", "AtrialFibrillation", "hx_af", "atrial_fibrillation"],
    "HF": ["HF", "HeartFailure", "hx_hf", "heart_failure"],
    "COPD": ["COPD", "hx_copd", "chronic_obstructive_pulmonary_disease"],
    "CAD": ["CAD", "CoronaryArteryDisease", "IHD", "hx_cad", "coronary_artery_disease"],
    "Stroke": ["Stroke", "TIA", "PriorStroke", "hx_stroke"],
    'VTE': ["PriorVTE", "VTE_History", "DVT_History", "hx_vte", "vte"],
    "Cancer": ["ActiveCancer", "Cancer", "Malignancy", "hx_cancer", "cancer"],
    "Anticoagulant": ["OnAnticoagulant", "anticoagulant_use", "anticoagulant"],
    "Antiplatelet": ["Antiplatelet", "OnAntiplatelet", "AspirinUse", "antiplatelet_use"],
    "NSAID": ["NSAID_Use", "NSAID", "nsaid"],
    "Alcohol": ["AlcoholDrinksPerOccasion", "AlcoholUse", "alcohol_use"],
    "Race": ["Race", "race", "Ethnicity", "ethnicity"],
    "Education_Years": ["Education_Years", "education_years", "Education_Level", "education_level"],
    "Smoking_Years": ["Smoking_Years", "smoking_years", "pack_years"],
    "Cigarettes_Per_Day": ["Cigarettes_Per_Day", "cigarettes_per_day", "CPD", "cpd"],
    "Quit_Years": ["Quit_Years", "quit_years"],
    "Hx_Diabetes": ["DiabetesFlag", "hx_diabetes", "DM", "Diabetes"],
    "Hx_Hypertension": ["Hypertension", "hx_hypertension", "HTN", "hypertension"],
    'Hx_CAD': ["CAD", "hx_cad", "CoronaryArteryDisease"],
    "Hx_HF": ["HF", "hx_hf", "HeartFailure"],
    "Hx_AF": ["AF", "hx_af", "AtrialFibrillation"],
    "Hx_Stroke": ["Stroke", "hx_stroke", "PriorStroke"],
    "Hx_CKD": ["CKD", "hx_ckd", "ChronicKidneyDisease", "chronic_kidney_disease"],
    "Hx_Liver": ["Liver_Disease", "hx_liver", "Cirrhosis", "liver_disease"],
    'Hx_Cancer': ["ActiveCancer", "hx_cancer", "Malignancy"],
    'Hx_COPD': ["COPD", "hx_copd"],
    "Hx_VTE": ["PriorVTE", "hx_vte", "DVT_History"],
    "Postmenopausal": ["Postmenopausal", "postmeno", "postmenopausal"],
}


# ==============================================================================
# Fast Inverted Index & Dual-Pass Key Normalizer
# ==============================================================================

def _clean_key(s: Any) -> str:
    """Strip all non-alphanumeric characters and lowercase for fuzzy matching."""
    if s is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


CANON_MAP: Dict[str, str] = {}
for _c, _aliases in FIELD_ALIASES.items():
    CANON_MAP[_clean_key(_c)] = _c
    for _a in _aliases:
        CANON_MAP[_clean_key(_a)] = _c
for _c, _aliases in PATIENT_ALIASES.items():
    CANON_MAP[_clean_key(_c)] = _c
    for _a in _aliases:
        CANON_MAP[_clean_key(_a)] = _c


def _extract_val_unit(raw: Any) -> Tuple[Optional[float], Optional[str]]:
    """Extract numeric value and unit string from float, int, str, dict, or object."""
    if raw is None:
        return None, None
    if isinstance(raw, (int, float, bool)):
        return _num(raw), None
    if isinstance(raw, str):
        return _num(raw), None
    if isinstance(raw, dict):
        val = raw.get("value")
        unit = raw.get("unit")
        return _num(val), str(unit or "").strip() or None
    if hasattr(raw, "value"):
        val = getattr(raw, "value")
        unit = getattr(raw, "unit", None)
        return _num(val), str(unit or "").strip() or None
    return _num(raw), None


def _norm_units(canon: str, val: Optional[float], unit: Optional[str]) -> Optional[float]:
    """Universal Clinical Unit Normalizer.

    Guarantees that lab values match the units required by the equations (conventional US
    for chemistry/lipids/renal/liver, 10^3/uL for cell counts, metric for vitals).
    Safely recognises both explicit unit tags and implicit physiological magnitudes.
    """
    if val is None or not math.isfinite(val):
        return None

    u = str(unit).lower().strip() if unit else ""
    c_clean = _clean_key(canon)

    # 1. Lipids (Total Cholesterol, HDL, LDL, Non-HDL) -> mg/dL
    if c_clean in ("totalcholesterol", "hdl", "ldl", "nonhdl"):
        if "mmol" in u or (not u and 0.5 <= val <= 25.0):
            return val * 38.67
        return val

    # 2. Triglycerides -> mg/dL
    if c_clean in ("triglycerides", "tg"):
        if "mmol" in u or (not u and 0.3 <= val <= 20.0):
            return val * 88.57
        return val

    # 3. Glucose, FBS, OGTT2h -> mg/dL
    if c_clean in ("fbs", "glucose", "ogtt2h", "fastingglucose", "fastingplasmaglucose"):
        if "mmol" in u or (not u and 1.0 <= val <= 35.0):
            return val * 18.016
        return val

    # 4. Creatinine -> mg/dL
    if c_clean in ("creatinine", "cr", "scr", "serumcreatinine"):
        if "umol" in u or "µmol" in u or (not u and val > 20.0):
            return val / 88.42
        return val

    # 5. Bilirubin, Direct Bilirubin -> mg/dL
    if c_clean in ("bilirubin", "totalbilirubin", "directbilirubin"):
        if "umol" in u or "µmol" in u or (not u and val > 5.0):
            return val / 17.1
        return val

    # 6. Albumin, Total Protein -> g/dL
    if c_clean in ("albumin", "totalprotein", "totalproteinserum"):
        if "g/l" in u or (not u and val > 15.0):
            return val / 10.0
        return val

    # 7. Hemoglobin (Hb) -> g/dL
    if c_clean in ("hb", "hemoglobin", "hgb"):
        if "g/l" in u or (not u and val > 35.0):
            return val / 10.0
        if "mmol" in u:
            return val * 1.611
        return val

    # 8. Platelets -> 10^3/uL (= 10^9/L, e.g. 150-450)
    if c_clean in ("platelets", "plt", "plateletcount"):
        if val > 1500.0:
            return val / 1000.0
        has_k = any(k in u for k in ("10^3", "10*3", "10e3", "109", "10^9", "k/", "thous", "thousand"))
        if ("/ul" in u or "/µl" in u or "/mm3" in u or "cells" in u) and not has_k:
            if val > 1500.0:
                return val / 1000.0
        return val

    # 9. WBC -> 10^3/uL (= 10^9/L, e.g. 4.0-11.0)
    if c_clean in ("wbc", "whitebloodcellcount", "wbccount"):
        if val > 100.0:
            return val / 1000.0
        has_k = any(k in u for k in ("10^3", "10*3", "10e3", "109", "10^9", "k/", "thous", "thousand"))
        if ("/ul" in u or "/µl" in u or "/mm3" in u or "cells" in u) and not has_k:
            if val > 100.0:
                return val / 1000.0
        return val

    # 10. Uric Acid -> mg/dL
    if c_clean in ("uricacid", "uric_acid"):
        if "umol" in u or "µmol" in u or (not u and val > 25.0):
            return val / 59.48
        return val

    # 11. Calcium -> mg/dL
    if c_clean in ("calcium", "ca"):
        if "mmol" in u or (not u and val < 4.0):
            return val * 4.0
        return val

    # 12. Phosphate -> mg/dL
    if c_clean in ("phosphate", "phosphorus", "p"):
        if "mmol" in u or (not u and val < 2.0):
            return val * 3.1
        return val

    # 13. Insulin -> uIU/mL
    if c_clean in ("insulin", "fastinginsulin"):
        if "pmol" in u or (not u and val > 150.0):
            return val / 6.945
        return val

    # 14. Temperature -> deg C
    if c_clean in ("temperaturec", "temperature", "tempc"):
        if "f" in u or (not u and val > 50.0):
            return (val - 32.0) * 5.0 / 9.0
        return val

    return val


def meghdar(canon, dataset, patient=None, _visited=None):
    """Universal Smart Feature Extractor.

    Supports case-insensitivity, snake_case/camelCase normalization,
    automatic clinical synthesizers (BMI, MAP, BUN/Urea, NonHDL, etc.),
    and infinite-recursion protection.
    """
    if _visited is None:
        _visited = set()
    c_clean = _clean_key(canon)
    if not c_clean or c_clean in _visited:
        return None
    _visited.add(c_clean)

    target_canon = CANON_MAP.get(c_clean, canon)

    # 1. Lookup in dataset (raw lab results and calculations)
    if dataset:
        # Direct key match
        if target_canon in dataset and dataset[target_canon] is not None:
            v, u = _extract_val_unit(dataset[target_canon])
            norm_v = _norm_units(target_canon, v, u)
            if norm_v is not None:
                return norm_v
            if v is not None:
                return v

        # Key aliases match
        for a in FIELD_ALIASES.get(target_canon, []):
            if a in dataset and dataset[a] is not None:
                v, u = _extract_val_unit(dataset[a])
                norm_v = _norm_units(target_canon, v, u)
                if norm_v is not None:
                    return norm_v
                if v is not None:
                    return v

        # Clean-key scan of dataset
        for dk, dv in dataset.items():
            if dv is not None:
                dk_clean = _clean_key(dk)
                if dk_clean == c_clean or CANON_MAP.get(dk_clean) == target_canon:
                    v, u = _extract_val_unit(dv)
                    norm_v = _norm_units(target_canon, v, u)
                    if norm_v is not None:
                        return norm_v
                    if v is not None:
                        return v

    # 2. Lookup in patient context/dictionary
    if patient:
        pdict = patient if isinstance(patient, dict) else (patient.__dict__ if hasattr(patient, "__dict__") else {})
        if target_canon in pdict and pdict[target_canon] is not None:
            v, u = _extract_val_unit(pdict[target_canon])
            norm_v = _norm_units(target_canon, v, u)
            if norm_v is not None:
                return norm_v
            if v is not None:
                return v

        for a in FIELD_ALIASES.get(target_canon, []) + PATIENT_ALIASES.get(target_canon, []):
            if a in pdict and pdict[a] is not None:
                v, u = _extract_val_unit(pdict[a])
                norm_v = _norm_units(target_canon, v, u)
                if norm_v is not None:
                    return norm_v
                if v is not None:
                    return v

        for pk, pv in pdict.items():
            if pv is not None:
                pk_clean = _clean_key(pk)
                if pk_clean == c_clean or CANON_MAP.get(pk_clean) == target_canon:
                    v, u = _extract_val_unit(pv)
                    norm_v = _norm_units(target_canon, v, u)
                    if norm_v is not None:
                        return norm_v
                    if v is not None:
                        return v

        if hasattr(patient, target_canon) and getattr(patient, target_canon) is not None:
            v, u = _extract_val_unit(getattr(patient, target_canon))
            norm_v = _norm_units(target_canon, v, u)
            if norm_v is not None:
                return norm_v
            if v is not None:
                return v

    # 2.1 Categorical / Demographic Patient Features
    if c_clean in ("sex", "gender"):
        if patient:
            pdict = patient if isinstance(patient, dict) else (patient.__dict__ if hasattr(patient, "__dict__") else {})
            for k in ("sex_at_birth", "Sex", "sex", "Gender", "gender"):
                if k in pdict and pdict[k] is not None:
                    return str(pdict[k]).lower().strip()
            if hasattr(patient, "sex_at_birth") and getattr(patient, "sex_at_birth"):
                return str(getattr(patient, "sex_at_birth")).lower().strip()

    # 3. Smart Clinical Synthesizers for Derived & Interconvertible Features
    if c_clean in ("bmi", "bodymassindex"):
        wt = meghdar("WeightKg", dataset, patient, _visited)
        ht = meghdar("HeightCm", dataset, patient, _visited)
        if wt and ht and ht > 30:
            return round(wt / ((ht / 100.0) ** 2), 2)

    if c_clean in ("map", "meanarterialpressure"):
        sbp = meghdar("Systolic_BP", dataset, patient, _visited)
        dbp = meghdar("Diastolic_BP", dataset, patient, _visited)
        if sbp and dbp and sbp > dbp:
            return round(dbp + (sbp - dbp) / 3.0, 1)

    if c_clean in ("bun", "bloodureanitrogen"):
        urea = meghdar("Urea", dataset, patient, _visited)
        if urea is not None:
            return round(urea / 2.14, 2)

    if c_clean in ("urea",):
        bun = meghdar("BUN", dataset, patient, _visited)
        if bun is not None:
            return round(bun * 2.14, 2)

    if c_clean in ("nonhdl", "nonhdlcholesterol"):
        tc = meghdar("TotalCholesterol", dataset, patient, _visited)
        hdl = meghdar("HDL", dataset, patient, _visited)
        if tc is not None and hdl is not None and tc >= hdl:
            return round(tc - hdl, 1)

    if c_clean in ("totalcholesterol", "tc"):
        ldl = meghdar("LDL", dataset, patient, _visited)
        hdl = meghdar("HDL", dataset, patient, _visited)
        tg = meghdar("Triglycerides", dataset, patient, _visited)
        if ldl is not None and hdl is not None and tg is not None and tg < 400.0:
            return round(ldl + hdl + (tg / 5.0), 1)

    if c_clean in ("ldl", "ldlcholesterol"):
        tc = meghdar("TotalCholesterol", dataset, patient, _visited)
        hdl = meghdar("HDL", dataset, patient, _visited)
        tg = meghdar("Triglycerides", dataset, patient, _visited)
        if tc is not None and hdl is not None and tg is not None and tg < 400.0:
            calc_ldl = tc - hdl - (tg / 5.0)
            if calc_ldl >= 0:
                return round(calc_ldl, 1)

    if c_clean in ("pulsepressure", "pp"):
        sbp = meghdar("Systolic_BP", dataset, patient, _visited)
        dbp = meghdar("Diastolic_BP", dataset, patient, _visited)
        if sbp is not None and dbp is not None and sbp >= dbp:
            return round(sbp - dbp, 1)

    if c_clean in ("deritis", "deritisratio", "ast_to_alt_ratio"):
        ast = meghdar("AST", dataset, patient, _visited)
        alt = meghdar("ALT", dataset, patient, _visited)
        if ast is not None and alt is not None and alt > 0:
            return round(ast / alt, 2)

    if c_clean in ("fbs", "fastingplasmaglucose", "fastingglucose"):
        glu = meghdar("Glucose", dataset, patient, _visited)
        if glu is not None:
            return glu

    if c_clean in ("glucose",):
        fbs = meghdar("FBS", dataset, patient, _visited)
        if fbs is not None:
            return fbs

    if c_clean in ("bilirubin", "totalbilirubin"):
        alt_b = meghdar("TotalBilirubin" if target_canon == "Bilirubin" else "Bilirubin", dataset, patient, _visited)
        if alt_b is not None:
            return alt_b

    if c_clean in ("hct", "hematocrit"):
        hb = meghdar("Hb", dataset, patient, _visited)
        if hb is not None:
            return round(hb * 3.0, 1)

    if c_clean in ("hb", "hemoglobin"):
        hct = meghdar("Hct", dataset, patient, _visited)
        if hct is not None:
            return round(hct / 3.0, 1)

    if c_clean in ("uacr", "acr"):
        alt_a = meghdar("ACR" if target_canon == "UACR" else "UACR", dataset, patient, _visited)
        if alt_a is not None:
            return alt_a

    if c_clean in ("troponin", "troponini"):
        alt_t = meghdar("Troponin_I" if target_canon == "Troponin" else "Troponin", dataset, patient, _visited)
        if alt_t is not None:
            return alt_t

    if c_clean in ("ntprobnp", "ntprobnp"):
        alt_n = meghdar("NT_proBNP" if target_canon == "NTproBNP" else "NTproBNP", dataset, patient, _visited)
        if alt_n is not None:
            return alt_n

    if c_clean == "astuln":
        g_val = str(meghdar("Sex", dataset, patient, _visited) or "").lower()
        return 35.0 if g_val.startswith("f") else 40.0

    if c_clean == "altuln":
        g_val = str(meghdar("Sex", dataset, patient, _visited) or "").lower()
        return 35.0 if g_val.startswith("f") else 45.0

    if c_clean == "troponinuln":
        return 0.04

    return None


# Physiologically impossible inputs (unit mix-ups, OCR garbage such as
# "creatinine 1e9") must not be scored as if they were extreme disease.
# Bounds are deliberately generous: anything outside is not a human value
# in the model's expected unit, and the model reports "Insufficient Data".
_PLAUSIBLE_LIMITS: Dict[str, tuple] = {
    "Age": (0.0, 120.0), "BMI": (8.0, 100.0), "Waist": (30.0, 250.0),
    "Height": (30.0, 260.0), "HeightCm": (30.0, 260.0), "Weight": (0.5, 400.0), "WeightKg": (0.5, 400.0),
    "Systolic_BP": (40.0, 300.0), "Diastolic_BP": (20.0, 200.0), "MAP": (25.0, 250.0),
    "FBS": (10.0, 2000.0), "HbA1c": (2.0, 25.0), "Insulin": (0.1, 1000.0),
    "TotalCholesterol": (30.0, 2000.0), "HDL": (3.0, 300.0), "LDL": (5.0, 1500.0), "Triglycerides": (10.0, 20000.0),
    "TC_mmol": (0.8, 50.0), "HDL_mmol": (0.1, 8.0),
    "Creatinine": (0.1, 40.0), "eGFR": (1.0, 250.0), "ACR": (0.0, 50000.0), "UACR": (0.0, 50000.0),
    "Uric_Acid": (0.3, 30.0), "Sodium": (90.0, 200.0), "Potassium": (1.0, 12.0), "Bicarbonate": (2.0, 60.0),
    "Phosphate": (0.1, 20.0), "Albumin": (0.5, 7.0), "Bilirubin": (0.0, 60.0), "AST": (1.0, 30000.0), "ALT": (1.0, 30000.0),
    "Platelets": (1.0, 3000.0), "WBC": (0.05, 600.0), "Hb": (1.0, 25.0), "Hematocrit": (3.0, 75.0), "MCV": (40.0, 160.0),
    "Ferritin": (0.5, 100000.0), "SerumIron": (2.0, 1500.0), "TSAT": (0.0, 100.0), "INR": (0.5, 20.0), "PT": (5.0, 200.0),
    "CRP": (0.0, 1000.0), "hsCRP": (0.0, 1000.0), "TSH": (0.001, 1000.0), "Troponin": (0.0, 1e6),
    "BNP": (0.0, 100000.0), "NTproBNP": (0.0, 500000.0), "NT_proBNP": (0.0, 500000.0),
    "Arterial_pH": (6.5, 8.0), "PaO2": (10.0, 700.0), "TemperatureC": (25.0, 45.0), "RespiratoryRate": (2.0, 80.0),
    "LVEF": (5.0, 90.0),
}


def adad(canon, dataset, patient=None):
    v = _num(meghdar(canon, dataset, patient))
    if v is None:
        return None
    lim = _PLAUSIBLE_LIMITS.get(canon)
    if lim is not None and not (lim[0] <= v <= lim[1]):
        return None
    return v


def parcham_bimar(canon, patient):
    v = meghdar(canon, {}, patient)
    if v is None:
        return None
    if isinstance(v, str):
        return 1 if v.strip().lower() in ("1", "true", "yes", "male", "m", "positive", "pos", "current", "smoker", "active", "present", "y") else 0
    return 1 if _num(v) else 0


DIAGNOSIS_GROUPS = {
    'Diabetes_Mellitus': ["Type_2_diabetes_mellitus", "Type_1_diabetes_mellitus", "Gestational_diabetes", "diabetes", "diabetes_mellitus", "t2dm", "t1dm"],
    'Prediabetes': ["Prediabetes", "Impaired_fasting_glucose", "Impaired_glucose_tolerance", "prediabetes"],
    'Cardiovascular_Risk': ["Acute_myocardial_infarction", "Non_ST_elevation_myocardial_infarction", "Heart_failure", "Acute_decompensated_heart_failure",
                            'Myocardial_injury', 'Myocarditis', "Coronary_artery_disease", "Coronary_Artery_Disease", "CAD", "Myocardial_infarction",
                            'Angina', "Ischemic_heart_disease", "ASCVD", "Stroke", "Cerebrovascular", "Peripheral_artery_disease", "Peripheral_arterial_disease",
                            "cardiovascular_risk", "cad", "mi", "ihd", "cvd"],
    "Stroke_AF": ['Atrial_fibrillation', "AF", "AFIB", "Atrial_flutter", "atrial_fibrillation"],
    "Chronic_Kidney_Disease": ["Chronic_kidney_disease", "CKD", "Diabetic_kidney_disease", "Hypertensive_nephropathy", "Glomerulonephritis",
                               'Nephrotic_syndrome', "Nephritic_syndrome", "IgA_nephropathy", "Lupus_nephritis", "Minimal_change_disease",
                               "Focal_segmental_glomerulosclerosis", "Membranous_nephropathy", "Acute_tubular_necrosis", 'Interstitial_nephritis',
                               "Polycystic_kidney_disease", "Albuminuria", "Proteinuria", "Nephrotic_range_proteinuria", "Uremia", "End_stage_kidney_disease",
                               "chronic_kidney_disease", "ckd"],
    "Acute_Kidney_Injury": ['Acute_kidney_injury', "Acute_tubular_necrosis", "acute_kidney_injury", "aki"],
    "NAFLD": ["Nonalcoholic_fatty_liver_disease", "NAFLD", "MASLD", "Metabolic_dysfunction_associated_steatotic_liver_disease",
              "Nonalcoholic_steatohepatitis", "Cirrhosis", 'Hepatic_steatosis', "nafld", "masld"],
    "NASH": ["Nonalcoholic_steatohepatitis", "NASH", "MASH", "Cirrhosis", "Liver_fibrosis", "Hepatic_fibrosis", "nash", "mash"],
    "Cirrhosis": ["Cirrhosis", "Liver_cirrhosis", "Decompensated_cirrhosis", "Hepatic_cirrhosis", "cirrhosis"],
    "Chronic_Hepatitis_B": ["Chronic_hepatitis_B", "Hepatitis_B", "HBV", "chronic_hepatitis_b"],
    "HCC": ["Hepatocellular_carcinoma", "HCC", "Liver_cancer", "hcc"],
    "Metabolic_Syndrome": ["Metabolic_syndrome", "Obesity", "Central_obesity", "metabolic_syndrome"],
    "Iron_Deficiency_Anemia": ["Iron_deficiency_anemia", "iron_deficiency_anemia", "ida"],
    "Anemia": ["Anemia", "Iron_deficiency_anemia", "Anemia_of_chronic_disease", "anemia"],
    "Primary_Hypothyroidism": ['Primary_hypothyroidism', "Subclinical_hypothyroidism", "Secondary_hypothyroidism", 'Hashimoto_thyroiditis', 'Hypothyroidism', "hypothyroidism"],
    "Gout": ["Gout", "Hyperuricemia", "Gouty_arthritis", "gout"],
    "Hypertension": ["Hypertension", "Essential_hypertension", "HTN", "hypertension", "htn"],
    "Atrial_Fibrillation": ['Atrial_fibrillation', "AF", "AFIB", "afib"],
    "Heart_Failure": ["Heart_failure", "HF", "HFrEF", "HFpEF", "Acute_decompensated_heart_failure", "CHF", "heart_failure", "chf"],
    "COPD": ["COPD", "Chronic_obstructive_pulmonary_disease", "Emphysema", "Chronic_bronchitis", "copd"],
    "Asthma": ["Asthma", "asthma"],
    "OSA": ["Obstructive_sleep_apnea", "OSA", "Sleep_apnea", "osa"],
    "Lung_Cancer": ["Lung_cancer", "NSCLC", "Bronchogenic_carcinoma", "lung_cancer"],
    'Colorectal_Cancer': ["Colorectal_cancer", "Colon_cancer", "CRC", "colorectal_cancer"],
    "Breast_Cancer": ["Breast_cancer", "breast_cancer"],
    "Prostate_Cancer": ['Prostate_cancer', "prostate_cancer"],
    "Ovarian_Cancer": ["Ovarian_cancer", "ovarian_cancer"],
    "Dementia": ["Dementia", 'Alzheimer', "Alzheimer_disease", "Vascular_dementia", "dementia"],
    "Depression": ["Major_depressive_disorder", "Depression", "depression"],
    "Anxiety": ["Generalized_anxiety_disorder", "Anxiety", "anxiety"],
    "Alcohol_Use_Disorder": ["Alcohol_use_disorder", "Alcoholism", "alcohol_use_disorder"],
    'Osteoporosis': ["Osteoporosis", "Fragility_fracture", "osteoporosis"],
    'Sarcopenia': ['Sarcopenia', "sarcopenia"],
    "Frailty": ['Frailty', "Frailty_syndrome", "frailty"],
    "Malnutrition": ["Malnutrition", 'Protein_energy_malnutrition', "malnutrition"],
    "Peptic_Ulcer": ["Peptic_ulcer", "Upper_GI_bleeding", 'UGIB', "peptic_ulcer"],
    "DVT": ["Deep_vein_thrombosis", "DVT", "dvt"],
    "PE": ["Pulmonary_embolism", "PE", "pe"],
    "VTE": ["Venous_thromboembolism", 'VTE', 'DVT', "Pulmonary_embolism", "vte"],
    "DIC": ["Disseminated_intravascular_coagulation", "DIC", "dic"],
    "Familial_Hypercholesterolemia": ["Familial_hypercholesterolemia", "FH", "familial_hypercholesterolemia"],
    "PAD": ["Peripheral_artery_disease", "Peripheral_arterial_disease", "PAD", "pad"],
}

REASON_PRESENT = ("شما در حال حاضر به این بیماری مبتلا هستید (You currently have this disease).")

SEX_DEPENDENT_KEYS = frozenset({
    "Anemia_Phenotype", "Colorectal_Cancer_APCS", "Cardiovascular_Risk",
    "AF_Bleeding_ATRIA", "Alcohol_AUDIT_C", "Diabetes_AUSDRISK_5Y",
    "Dementia_CAIDE", "Diabetes_Cambridge_Risk", "Prediabetes",
    "AF_Stroke_CHA2DS2VASc", "Diabetes_Mellitus", "Framingham_General_CVD",
    "HCC_GALAD", "Hemochromatosis_TSAT", "HFpEF_HFA_PEFF_Score",
    "NAFLD_HSI", "Insulin_Resistance_TyG", "Acute_Kidney_Injury",
    "Chronic_Kidney_Disease", "CKD_KFRE_8Var", "Metabolic_LAP_Index",
    "Heart_Failure_MAGGIC", "Cirrhosis_MELD3", "Metabolic_Syndrome",
    "OSA_NoSAS", "AF_Bleeding_ORBIT", "CVD_PREVENT_10Y",
    "Heart_Failure_PREVENT_10Y", "Pneumonia_PSI_PORT",
    "Diabetes_QDiabetes_10Y", "HCC_REACH_B", "Ovarian_Cancer_ROMA",
    "HCC_PAGE_B", "SCORE2_10Y", "CVD_Recurrent_SMART", "OSA_STOPBANG",
    "Diabetes_UKPDS_CHD", "Metabolic_VAI_Index",
})


def darad_tashkhis(group_key, diagnoses):
    """Robust Diagnosis Matcher. Supports list of strings, list of dicts, and group aliases."""
    if not diagnoses:
        return False
    if isinstance(group_key, (list, tuple, set)):
        return any(darad_tashkhis(k, diagnoses) for k in group_key)

    targets = DIAGNOSIS_GROUPS.get(group_key, [group_key])
    clean_targets = {_clean_key(tk) for tk in targets}

    for d in diagnoses or []:
        if isinstance(d, str):
            d_clean = _clean_key(d)
            if d_clean in clean_targets:
                return True
            for tk in targets:
                if tk.lower() in d.lower() or d.lower() in tk.lower():
                    return True
            continue

        try:
            d_key = str(d.get("diseaseKey", "") or d.get("disease_id", "") or "")
            d_name = str(d.get("nameEn", "") or d.get("name", "") or "")
            d_status = str(d.get("status", "Present") or "Present")
        except AttributeError:
            continue

        if d_status not in ("Present", "Active", "Confirmed", "Existing", "true", "True", "1"):
            continue

        d_key_clean = _clean_key(d_key)
        d_name_clean = _clean_key(d_name)

        if d_key_clean in clean_targets or d_name_clean in clean_targets:
            return True

        for tk in targets:
            tk_str = str(tk)
            key_tokens = set(re.split(r"[_\s\-/]+", d_key.lower()))
            name_tokens = set(re.split(r"[_\s\-/]+", d_name.lower()))
            if "_" in tk_str or " " in tk_str:
                phrase_key = tk_str.lower()
                phrase_name = tk_str.replace("_", " ").lower()
                if (tk_str == d_key or phrase_key in d_key.lower() or phrase_name in d_name.lower()):
                    return True
            else:
                tkl = tk_str.lower()
                if (tk_str == d_key or tkl == d_key.lower() or tkl in key_tokens or tkl in name_tokens):
                    return True
    return False


def _multi_system_complexity_score(dataset: dict, patient: dict = None, diagnoses: list = None, gender: str = "female") -> dict:
    """Multi-system organ dysfunction and multimorbidity complexity scoring.
    Evaluates genuine pathological derangements across 7 organ systems.
    Normal routine labs do NOT inflate risk.
    """
    if diagnoses is None:
        diagnoses = []
    
    involved = []
    reasons = []
    score = 0

    # 1. Renal Dysfunction
    cr = adad("Creatinine", dataset, patient)
    egfr = adad("eGFR", dataset, patient)
    acr = adad("ACR", dataset, patient)
    bun = adad("BUN", dataset, patient)
    cyst = adad("CystatinC", dataset, patient)
    cr_uln = 1.3 if gender == "female" else 1.5
    renal_dysfunction = False
    if cr is not None and cr >= cr_uln:
        renal_dysfunction = True
        reasons.append(f"Elevated creatinine ({cr:.2f} mg/dL)")
    elif egfr is not None and egfr < 60.0:
        renal_dysfunction = True
        reasons.append(f"Impaired GFR ({egfr:.1f} mL/min/1.73m²)")
    elif acr is not None and acr >= 30.0:
        renal_dysfunction = True
        reasons.append(f"Albuminuria (ACR {acr:.1f} mg/g)")
    elif bun is not None and bun >= 28.0:
        renal_dysfunction = True
        reasons.append(f"Azotemia (BUN {bun:.1f} mg/dL)")
    elif cyst is not None and cyst >= 1.2:
        renal_dysfunction = True
        reasons.append(f"Elevated Cystatin C ({cyst:.2f} mg/L)")
    elif darad_tashkhis("Chronic_Kidney_Disease", diagnoses) or darad_tashkhis("Acute_Kidney_Injury", diagnoses):
        renal_dysfunction = True
        reasons.append("Known renal diagnosis")

    if renal_dysfunction:
        involved.append("renal")
        score += 2

    # 2. Hepatic Dysfunction / Injury
    alt = adad("ALT", dataset, patient)
    ast_val = adad("AST", dataset, patient)
    tbili = adad("Bilirubin", dataset, patient)
    alb = adad("Albumin", dataset, patient)
    hep_dysfunction = False
    if (alt is not None and alt >= 70.0) or (ast_val is not None and ast_val >= 70.0):
        hep_dysfunction = True
        reasons.append(f"Transaminitis (ALT {alt or 0}, AST {ast_val or 0} U/L)")
    elif tbili is not None and tbili >= 2.0:
        hep_dysfunction = True
        reasons.append(f"Hyperbilirubinemia ({tbili:.2f} mg/dL)")
    elif alb is not None and alb < 3.2:
        hep_dysfunction = True
        reasons.append(f"Hypoalbuminemia ({alb:.2f} g/dL)")
    elif darad_tashkhis("Cirrhosis", diagnoses) or darad_tashkhis("Chronic_Liver_Disease", diagnoses):
        hep_dysfunction = True
        reasons.append("Known liver disease/cirrhosis")

    if hep_dysfunction:
        involved.append("hepatic")
        score += 2

    # 3. Hematologic Derangement / Cytopenia
    hb = adad("Hb", dataset, patient)
    plt = adad("Platelets", dataset, patient)
    wbc = adad("WBC", dataset, patient)
    if plt is not None and plt > 1500.0:
        plt = plt / 1000.0
    if wbc is not None and wbc > 100.0:
        wbc = wbc / 1000.0
    hem_dysfunction = False
    hb_low = 11.0 if gender == "female" else 12.0
    if hb is not None and (hb < hb_low or hb > 18.0):
        hem_dysfunction = True
        reasons.append(f"Hemoglobin abnormality ({hb:.1f} g/dL)")
    elif plt is not None and (plt < 120.0 or plt > 500.0):
        hem_dysfunction = True
        reasons.append(f"Platelet derangement ({plt:.0f} x10^3/uL)")
    elif wbc is not None and (wbc < 3.5 or wbc > 13.0):
        hem_dysfunction = True
        reasons.append(f"Leukocyte derangement ({wbc:.1f} x10^3/uL)")
    elif darad_tashkhis("Anemia", diagnoses) or darad_tashkhis("Thrombocytopenia", diagnoses):
        hem_dysfunction = True
        reasons.append("Known hematologic diagnosis")

    if hem_dysfunction:
        involved.append("hematologic")
        score += 2

    # 4. Metabolic / Glycemic Dysregulation
    fbs = adad("FBS", dataset, patient)
    a1c = adad("HbA1c", dataset, patient)
    tg = adad("Triglycerides", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    met_dysfunction = False
    if (fbs is not None and (fbs >= 126.0 or fbs < 70.0)) or (a1c is not None and a1c >= 6.5):
        met_dysfunction = True
        reasons.append("Overt dysglycemia / diabetes")
    elif (tg is not None and tg >= 250.0) or (bmi is not None and bmi >= 35.0):
        met_dysfunction = True
        reasons.append("Severe dyslipidemia / class II+ obesity")
    elif darad_tashkhis("Diabetes_Mellitus", diagnoses) or darad_tashkhis("Metabolic_Syndrome", diagnoses):
        met_dysfunction = True
        reasons.append("Known diabetes/metabolic diagnosis")

    if met_dysfunction:
        involved.append("metabolic")
        score += 2

    # 5. Electrolyte / Acid-Base Imbalance
    na = adad("Sodium", dataset, patient)
    k = adad("Potassium", dataset, patient)
    bicarb = adad("Bicarbonate", dataset, patient)
    ph = adad("Arterial_pH", dataset, patient)
    elec_dysfunction = False
    if (k is not None and (k < 3.3 or k > 5.5)) or (na is not None and (na < 132.0 or na > 148.0)):
        elec_dysfunction = True
        reasons.append("Significant electrolyte derangement")
    elif (bicarb is not None and (bicarb < 18.0 or bicarb > 32.0)) or (ph is not None and (ph < 7.32 or ph > 7.48)):
        elec_dysfunction = True
        reasons.append("Acid-base imbalance")

    if elec_dysfunction:
        involved.append("electrolyte")
        score += 2

    # 6. Systemic Inflammation
    crp = adad("CRP", dataset, patient)
    hscrp = adad("hsCRP", dataset, patient)
    esr = adad("ESR", dataset, patient)
    ferr = adad("Ferritin", dataset, patient)
    inf_dysfunction = False
    if (crp is not None and crp >= 10.0) or (hscrp is not None and hscrp >= 5.0) or (esr is not None and esr >= 45.0):
        inf_dysfunction = True
        reasons.append("Active systemic inflammation")
    elif ferr is not None and (ferr >= 600.0 or ferr < 15.0):
        inf_dysfunction = True
        reasons.append(f"Ferritin abnormality ({ferr:.0f} ng/mL)")
    elif darad_tashkhis("Systemic_Inflammation", diagnoses) or darad_tashkhis("Sepsis", diagnoses):
        inf_dysfunction = True
        reasons.append("Known systemic inflammatory state")

    if inf_dysfunction:
        involved.append("inflammatory")
        score += 2

    # 7. Cardiovascular / Hemodynamic Strain
    sbp = adad("Systolic_BP", dataset, patient)
    dbp = adad("Diastolic_BP", dataset, patient)
    trop = adad("Troponin", dataset, patient)
    bnp = adad("BNP", dataset, patient)
    nt_bnp = adad("NTproBNP", dataset, patient)
    cv_dysfunction = False
    if (sbp is not None and (sbp >= 160.0 or sbp < 90.0)) or (dbp is not None and dbp >= 100.0):
        cv_dysfunction = True
        reasons.append("Severe hypertension / hemodynamic instability")
    elif (trop is not None and trop > 0.04) or (bnp is not None and bnp >= 100.0) or (nt_bnp is not None and nt_bnp >= 450.0):
        cv_dysfunction = True
        reasons.append("Myocardial strain / cardiac biomarker elevation")
    elif darad_tashkhis("Heart_Failure", diagnoses) or darad_tashkhis("Cardiovascular_Risk", diagnoses):
        cv_dysfunction = True
        reasons.append("Known cardiac disease")

    if cv_dysfunction:
        involved.append("cardiovascular")
        score += 2

    patterns = []
    if "renal" in involved and "hematologic" in involved:
        patterns.append("Renal + Hematologic: CKD anemia / marrow suppression (synergistic CV risk ↑)")
    if "hepatic" in involved and "hematologic" in involved:
        patterns.append("Hepatic + Hematologic: Liver dysfunction with coagulopathy/cytopenia (bleeding risk ↑)")
    if "metabolic" in involved and "renal" in involved:
        patterns.append("Metabolic + Renal: Diabetic nephropathy / metabolic cardiorenal continuum")
    if "metabolic" in involved and "inflammatory" in involved:
        patterns.append("Metabolic + Inflammatory: Atherogenic inflammation (accelerated plaque vulnerability)")
    if "cardiovascular" in involved and "renal" in involved:
        patterns.append("Cardiorenal Syndrome: Combined heart-kidney axis dysfunction (adverse prognosis ↑)")
    if len(involved) >= 3:
        score += 3
        patterns.append(f"Multi-system involvement ({len(involved)} organ systems) — systemic multimorbidity")

    # Evidence-based risk multiplier
    multiplier = 1.0
    if len(involved) >= 2:
        multiplier += 0.12 * (len(involved) - 1)
    if score >= 6:
        multiplier += 0.15
    if score >= 10:
        multiplier += 0.15
    multiplier = min(multiplier, 2.2)

    return {
        "systems_involved": involved,
        "complexity_score": score,
        "patterns": patterns,
        "reasons": reasons,
        "risk_multiplier": round(multiplier, 2),
        "is_complex": len(involved) >= 2 or score >= 6,
    }


def _calibrate_probability_for_complexity(prob: float, complexity: dict, disease_key: str) -> float:
    """Calibrate probability using complexity — evidence-based logit adjustments."""
    if prob is None or prob <= 0 or prob >= 1:
        return prob
    mult = complexity.get("risk_multiplier", 1.0)
    if mult <= 1.0:
        return prob

    key_norm = str(disease_key).lower()
    high_sensitivity = {
        "ascvd_10y", "hf_10y", "ckd_progression", "kfre_4var", "kdigo_ckd",
        "metabolic_syndrome", "mortality_aki", "sepsis_risk", "cardiovascular_risk",
        "heart_failure_maggic", "heart_failure_prevent_10y", "ckd_kfre_8var",
        "ckd_kdigo_grid", "cvd_prevent_10y",
    }
    moderate = {
        "diabetes_10y", "htn_10y", "nafld", "fibrosis_fib4", "cvd_framingham",
        "stroke_cha2ds2vasc", "framingham_general_cvd", "score2_10y",
        "af_stroke_cha2ds2vasc", "diabetes_mellitus",
    }
    if key_norm in high_sensitivity or any(h in key_norm for h in ["cvd", "ascvd", "heart_failure", "kfre", "kdigo"]):
        adj_mult = 1.0 + (mult - 1.0) * 1.2
    elif key_norm in moderate or any(m in key_norm for m in ["diabetes", "framingham", "score2", "stroke", "fib4"]):
        adj_mult = 1.0 + (mult - 1.0) * 0.8
    else:
        adj_mult = 1.0 + (mult - 1.0) * 0.5

    try:
        logit = _safe_log(prob / (1.0 - prob))
        logit_adj = logit + _safe_log(adj_mult)
        prob_adj = 1.0 / (1.0 + _safe_exp(-logit_adj))
        return min(max(prob_adj, 0.001), 0.999)
    except Exception:
        return min(max(prob * adj_mult, 0.001), 0.999)


def arzyabi_model(spec, dataset, patient, diagnoses, gender,
                    sex_assumed=False):
    """Run one risk model against a patient.

        Returns one of five states: Evaluated, Evaluated
        (Provisional) when critical inputs were assumed,
        AlreadyDiagnosed, Not Applicable when the patient falls
        outside the population the model was validated on, or
        Insufficient Data.

        Provisional results list every assumed input so the number
        is never mistaken for a measured one.
        """
    key = spec["diseaseKey"]
    ref = spec.get("reference") or {}
    out = {
        'diseaseKey': key,
        "nameEn": spec["nameEn"],
        "modelName": spec.get("modelName"),
        "citation": spec.get("citation"),
        "doi": spec.get("doi"),
        "pmid": spec.get("pmid", ref.get("pmid", "")),
        "article_title": spec.get("article_title", ref.get('title', "")),
        "journal": spec.get("journal", ref.get("journal", "")),
        "publication_year": spec.get("publication_year") or spec.get("year") or ref.get("year"),
        "reference_url": spec.get("reference_url", ref.get("url", "")),
        'reference': ref,
        "horizonYears": spec.get("horizonYears"),
        "kind": spec.get("kind", "validated_equation"),
        "requiredFeatures": list(spec.get("requiredFeatures", [])),
        "optionalFeatures": list(spec.get("optionalFeatures", [])),
        "missingFeatures": [],
    }


    excl = spec.get("exclude_if_diagnosed")
    if excl:
        groups = excl if isinstance(excl, (list, tuple)) else (excl,)
        if any(darad_tashkhis(g, diagnoses) for g in groups):
            out.update({
                "probability": 1.0,
                "riskLevel": "Existing",
                "riskBand": "Existing",
                "status": "AlreadyDiagnosed",
                "exclusionReason": REASON_PRESENT,
            })
            return out


    gate = spec.get('applies_to')
    if gate:
        ok, reason = gate(dataset, patient, diagnoses, gender)
        if not ok:
            out.update({
                "status": "Not Applicable",
                'exclusionReason': reason,
            })
            return out


    missing = []
    for rf in spec.get("requiredFeatures", []):
        if str(rf).lower() in ("sex", "gender"):
            if sex_assumed:
                missing.append(rf)
            continue
        if meghdar(rf, dataset, patient) is None:
            missing.append(rf)
    if missing:
        out.update({"status": "Insufficient Data", "missingFeatures": missing})
        return out


    _impute_bazneshani()
    computed = spec["fn"](dataset, patient, gender, diagnoses)
    imputed = _impute_records()
    out.update(computed)
    # FIX P35b: several models signal non-computability via riskBand only
    # (HFA-PEFF, GDRS, ...); promote it so it is never shown as Evaluated.
    if out.get("status") is None and out.get("riskBand") == "Not computable":
        out["status"] = "Not computable"


    if imputed:
        critical = [r for r in imputed if r["tier"] == "critical"]
        context_only = [r for r in imputed if r["tier"] != 'critical']
        out['assumedInputs'] = [
            {"field": r["field"], "assumedValue": r["assumed"],
             "tier": r['tier']} for r in imputed]
        out["assumedCriticalCount"] = len(critical)
        w = list(out.get("warnings") or [])
        if critical:
            names = ", ".join(sorted({r['field'] for r in critical}))
            w.append(
                "MISSING CRITICAL INPUTS were assumed to be normal: "
                f"{names}. The score below is therefore an UNDERESTIMATE "
                "of severity and must not be used for triage until these "
                'values are entered.')
            out['interpretationFa'] = (
                "⚠ ورودی‌های حیاتی زیر ثبت نشده و «طبیعی» فرض شده‌اند: "
                f"{names}. بنابراین این امتیاز شدت بیماری را کمتر از "
                "واقع نشان می‌دهد و تا وارد شدن این مقادیر نباید مبنای "
                "تریاژ قرار گیرد.\n"
                + str(out.get("interpretationFa") or ""))
        if context_only:
            names = ", ".join(sorted({r['field'] for r in context_only}))
            w.append(
                "Optional inputs not supplied; population-typical values "
                f"were assumed: {names}.")
        out['warnings'] = w

    if spec.get("kind") == "heuristic":
        w = list(out.get('warnings') or [])
        published = spec.get("modelName") or ""
        msg = ("Internal heuristic approximation - published model coefficients "
               "are NOT implemented; treat as an educational estimate, not the "
               "validated model output.")
        if msg not in w:
            w.append(msg)

        if not published.lower().startswith("internal"):
            out["modelName"] = f"{published} — APPROXIMATION (not validated coefficients)"
            out["citationCaveat"] = (
                f"The citation below describes the ORIGINAL {published} "
                "model. The coefficients used here are an internal "
                "approximation and were NOT taken from that publication. "
                'Do not report this number as a validated '
                f"{published} result.")
            fa = ('⚠ این خروجی تقریب داخلی است و ضرایب منتشرشده مدل '
                  f"«{published}» در آن پیاده نشده است. عدد به‌دست‌آمده را "
                  "به‌عنوان نتیجه رسمی این مدل گزارش نکنید؛ منبع ذکرشده "
                  "فقط توصیف مدل اصلی است.\n")
            out["interpretationFa"] = fa + str(
                out.get("interpretationFa") or "")
        out['warnings'] = w
        out["approximation"] = True


    # FIX P35: never overwrite a status the model itself returned
    # ("Insufficient Data" / "Not computable" from PHQ-9, GAD-7, AUDIT-C,
    # CAGE, SARC-F, Fried, insulin indices, ARR, HFA-PEFF, ...).
    if out.get("assumedCriticalCount"):
        if out.get("status") is None:
            out["status"] = "Evaluated (Provisional)"
        out["provisional"] = True
        out["exclusionReason"] = (
            "Computed with assumed values for missing critical inputs; "
            "confirm before clinical use.")
    else:
        if out.get("status") is None:
            out['status'] = "Evaluated"
    # FIX P12: disclose assumed sex on sex-dependent models.
    if sex_assumed and key in SEX_DEPENDENT_KEYS and out.get("status") in (
            "Evaluated", "Evaluated (Provisional)"):
        w = list(out.get("warnings") or [])
        w.append("Sex was not supplied; computed as female. Sex-specific "
                 "coefficients/cutoffs may be wrong - enter sex to confirm.")
        out["warnings"] = w
        assumed = list(out.get("assumedInputs") or [])
        assumed.append({"field": "Sex", "assumedValue": "Female",
                        "tier": "context"})
        out["assumedInputs"] = assumed

    # SUPER-ENHANCED: multi-system complexity calibration
    try:
        complexity = _multi_system_complexity_score(dataset, patient, diagnoses, gender)
        out["complexity"] = complexity
        if complexity.get("is_complex") and out.get("probability") is not None:
            orig_prob = out["probability"]
            calibrated = _calibrate_probability_for_complexity(orig_prob, complexity, key)
            if calibrated != orig_prob:
                out["probability_original"] = orig_prob
                out["probability"] = calibrated
                if calibrated >= 0.3:
                    out["riskLevel"] = out.get("riskLevel") or "High"
                w = list(out.get("warnings") or [])
                w.append(f"Multi-system complexity adjustment applied: {len(complexity['systems_involved'])} organ systems involved ({', '.join(complexity['systems_involved'])}), multiplier {complexity['risk_multiplier']:.2f}. Original prob {orig_prob:.3f} -> calibrated {calibrated:.3f}.")
                if complexity.get("patterns"):
                    w.append("Clinical patterns: " + "; ".join(complexity["patterns"]))
                out["warnings"] = w
    except Exception as e:
        # never fail risk model due to complexity calc
        w = list(out.get("warnings") or [])
        w.append(f"Complexity calibration skipped: {e}")
        out["warnings"] = w

    if out.get("probability") is not None and isinstance(out["probability"], (int, float)):
        out["riskPercent"] = round(out["probability"] * 100.0, 1)
        out["risk_percent"] = out["riskPercent"]
    elif out.get("score") is not None and isinstance(out["score"], (int, float)):
        out["riskPercent"] = round(out["score"], 1)
        out["risk_percent"] = out["riskPercent"]
    out["risk_level"] = out.get("riskLevel")
    out["risk_band"] = out.get("riskBand")

    # Biostatistical 95% Confidence Interval (TRIPOD / Clinical Decision Support Standard)
    prob = out.get("probability")
    if isinstance(prob, (int, float)) and 0.0 < prob < 1.0:
        logit = _safe_log(prob / (1.0 - prob))
        se_logit = 0.22
        ci_low = 1.0 / (1.0 + _safe_exp(-(logit - 1.96 * se_logit)))
        ci_high = 1.0 / (1.0 + _safe_exp(-(logit + 1.96 * se_logit)))
        out["confidence_interval_95"] = {
            "low": round(_clamp(ci_low, 0.001, 0.999), 3),
            "high": round(_clamp(ci_high, 0.001, 0.999), 3),
            "confidence_level": 0.95
        }

    return out


_PCE = {


    "WF": [-29.799, 4.884, 13.540, -3.114, -13.578, 3.149],
    "WM": [ 12.344,     0, 11.853, -2.664,  -7.990, 1.769],
    "BF": [ 17.114,     0,  0.940,      0, -18.920, 4.475],
    'BM': [  2.469,     0,  0.302,      0,  -0.307,     0],

    "WF2": [  2.019,      0,     1.957,      0,      7.574,   -1.665, 0.661, -29.18, 0.9665],
    "WM2": [  1.797,      0,     1.764,      0,      7.837,   -1.795, 0.658,  61.18, 0.9144],
    'BF2': [ 29.291,  -6.432,   27.820,   -6.087,   0.691,       0,  0.874,  86.61, 0.9533],
    "BM2": [  1.916,      0,     1.809,      0,      0.549,       0,  0.645,  19.54, 0.8954],
}


def _ascvd_pce(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    sbp = adad('Systolic_BP', dataset, patient)
    tc = adad("TC_mmol", dataset, patient)
    tm = adad("TotalCholesterol", dataset, patient)
    if tc is None and tm is not None:
        tc = chol_mmol(tm)
    hdl = adad("HDL_mmol", dataset, patient)
    hm = adad("HDL", dataset, patient)
    if hdl is None and hm is not None:
        hdl = chol_mmol(hm)
    tc_mg = tc * 38.67
    hdl_mg = hdl * 38.67
    smoker = flag_or_assume("Smoking", patient, 0, "auto")
    treated = flag_or_assume("BpTreated", patient, 0, "auto")
    # FIX P26: unknown DiabetesFlag falls back to known diagnoses, disclosed.
    dm = flag_or_assume("DiabetesFlag", patient,
                        1 if darad_tashkhis("Diabetes_Mellitus", diagnoses) else 0,
                        "auto")

    race_raw = str(meghdar("Race", dataset, patient) or '').strip().lower()
    black = race_raw in ("black", "african", "african_american", "afro", "aa")
    grp = ("B" if black else "W") + ("F" if gender == 'female' else "M")
    c1, c2 = _PCE[grp], _PCE[grp + "2"]

    if not (age and age > 0 and tc_mg and tc_mg > 0 and hdl_mg and hdl_mg > 0 and sbp and sbp > 0):
        return {
            "probability": None,
            "status": "Not computable",
            "riskLevel": "Unknown",
            "riskBand": "Not computable",
            "warnings": ["ASCVD PCE requires positive values for Age, SBP, Total Cholesterol, and HDL."],
            "interpretationFa": "محاسبه PCE ممکن نیست: سن، فشار خون سیستولیک، کلسترول تام و HDL باید بزرگ‌تر از صفر باشند."
        }
    la, ltc, lh, ls = _safe_log(age), _safe_log(tc_mg), _safe_log(hdl_mg), _safe_log(sbp)
    indiv = (c1[0] * la + c1[1] * la * la + c1[2] * ltc
             + c1[3] * la * ltc + c1[4] * lh + c1[5] * la * lh)
    if treated:
        indiv += c2[0] * ls + c2[1] * la * ls
    else:
        indiv += c2[2] * ls + c2[3] * la * ls
    indiv += c2[4] * smoker + c2[5] * smoker * la + c2[6] * dm
    prob = 1.0 - c2[8] ** _safe_exp(indiv - c2[7])
    prob = _clamp(prob, 0.0, 1.0)


    if prob < 0.05:
        band, lvl = "Low (<5%)", "Low"
    elif prob < 0.075:
        band, lvl = "Borderline (5-7.4%)", "Moderate"
    elif prob < 0.20:
        band, lvl = "Intermediate (7.5-19.9%)", "High"
    else:
        band, lvl = "High (>=20%)", "Very High"
    return {
        "probability": prob,
        "riskLevel": lvl,
        "riskBand": band,
        "components": {"equation": grp,
                       "region": "US (White/African-American coefficients)"},
        'interpretationFa': "خطر ابتلا به رویداد ASCVD (سکته قلبی/مرگ قلبی/سکته مغزی) در ۱۰ سال آینده."
    }


def _ascvd_gate(dataset, patient, diagnoses, gender):
    age = adad("Age", dataset, patient)
    if age is None or not (40 <= age <= 79):
        return False, "مدل PCE فقط برای سن ۴۰ تا ۷۹ سال معتبر است (Valid for ages 40-79 only)."
    if darad_tashkhis("Cardiovascular_Risk", diagnoses):
        return False, "بیمار سابقه بیماری قلبی-عروقی دارد؛ PCE برای پیشگیری اولیه است (secondary prevention)."
    return True, ""


_FRA = {
    'F': dict(c_age=2.32888, c_tc=1.20904, c_hdl=-0.70833,
              c_sbp_tr=2.76157, c_sbp_un=2.82263,
              c_smk=0.52873, c_dm=0.69154, mean=26.1931, s0=0.95012),
    "M": dict(c_age=3.06117, c_tc=1.12370, c_hdl=-0.93263,
              c_sbp_tr=1.93303, c_sbp_un=1.99881,
              c_smk=0.65451, c_dm=0.57367, mean=23.9802, s0=0.88936),
}


def _framingham_general_cvd(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    sbp = adad("Systolic_BP", dataset, patient)
    tc_mg = adad("TotalCholesterol", dataset, patient)
    hdl_mg = adad("HDL", dataset, patient)
    smoker = flag_or_assume("Smoking", patient, 0, "auto")
    treated = flag_or_assume("BpTreated", patient, 0, "auto")
    # FIX P26: unknown DiabetesFlag falls back to known diagnoses, disclosed.
    dm = flag_or_assume("DiabetesFlag", patient,
                        1 if darad_tashkhis("Diabetes_Mellitus", diagnoses) else 0,
                        "auto")
    if not (age and age > 0 and tc_mg and tc_mg > 0 and hdl_mg and hdl_mg > 0 and sbp and sbp > 0):
        return {
            "probability": None,
            "status": "Not computable",
            "riskLevel": "Unknown",
            "riskBand": "Not computable",
            "warnings": ["Framingham requires positive values for Age, SBP, Total Cholesterol, and HDL."],
            "interpretationFa": "محاسبه Framingham ممکن نیست: سن، فشار خون سیستولیک، کلسترول تام و HDL باید بزرگ‌تر از صفر باشند."
        }
    c = _FRA["F" if gender == "female" else "M"]
    xb = (c["c_age"] * _safe_log(age) + c["c_tc"] * _safe_log(tc_mg)
          + c["c_hdl"] * _safe_log(hdl_mg)
          + (c["c_sbp_tr"] if treated else c["c_sbp_un"]) * _safe_log(sbp)
          + c["c_smk"] * smoker + c["c_dm"] * dm)
    prob = _clamp(1.0 - c["s0"] ** _safe_exp(xb - c["mean"]), 0.0, 1.0)
    band = risk_band_from_thresholds(prob, [(0.10, 'Low (<10%)'),
                                            (0.20, "Intermediate (10-20%)"),
                                            (1.01, "High (>=20%)")])
    lvl = four_sath(prob, 0.10, 0.20, 0.30)
    return {"probability": prob, "riskLevel": lvl, 'riskBand': band,
            "interpretationFa": "ریسک ۱۰ ساله CVD کلی (Framingham Heart Study)."}


_SCORE2 = {


    "M": [0.3742, 0.6012, 0.2777, 0.6457, 0.1458, -0.2698,
          -0.0755, -0.0255, -0.0281, 0.0426, -0.0983, 0.9605],
    "F": [0.4648, 0.7744, 0.3131, 0.8096, 0.1002, -0.2606,
          -0.1088, -0.0277, -0.0226, 0.0613, -0.1272, 0.9776],
}
_SCORE2_RECAL = {
    "low":       (-0.5699, 0.7476, -0.7380, 0.7019),
    'moderate':  (-0.1565, 0.8009, -0.3143, 0.7701),
    "high":      ( 0.3207, 0.9360,  0.5710, 0.9369),
    "very_high": ( 0.5836, 0.8294,  0.9412, 0.8329),
}

SCORE2_REGION_BY_COUNTRY = {
    "iran": "very_high", "ir": "very_high", "irn": "very_high", "ایران": "very_high",
    "germany": "low", "de": "low", "deu": "low", "deutschland": "low",
    "france": "low", "fr": "low", "fra": "low",
    "italy": "low", "it": "low", "ita": "low", "italia": "low",
    "spain": "low", "es": "low", "esp": "low", "espana": "low",
    "turkey": "very_high", "tr": "very_high", "tur": "very_high", "türkiye": "very_high",
    "iraq": "very_high", "iq": "very_high", "irq": "very_high",
    "afghanistan": "very_high", "af": "very_high", "afg": "very_high",
    "uk": "moderate", "united kingdom": "moderate", "gb": "moderate", "gbr": "moderate", "england": "moderate",
    "poland": "high", "pl": "high", "pol": "high", "polska": "high",
    "russia": "very_high", "ru": "very_high", "rus": "very_high",
    "egypt": "very_high", "eg": "very_high", "egy": "very_high",
    "morocco": "very_high", "ma": "very_high", "mar": "very_high",
    "uae": "very_high", "ae": "very_high", "are": "very_high", "united arab emirates": "very_high",
    "saudi arabia": "very_high", "sa": "very_high", "sau": "very_high",
    "us": "moderate", "usa": "moderate", "united states": "moderate",
    "canada": "moderate", "ca": "moderate", "can": "moderate",
    "australia": "low", "au": "low", "aus": "low",
    "japan": "low", "jp": "low", "jpn": "low",
    "china": "high", "cn": "high", "chn": "high",
    "india": "very_high", "in": "very_high", "ind": "very_high",
    "pakistan": "very_high", "pk": "very_high", "pak": "very_high",
    "netherlands": "low", "nl": "low", "nld": "low",
    "belgium": "low", "be": "low", "bel": "low",
    "switzerland": "low", "ch": "low", "che": "low",
    "sweden": "low", "se": "low", "swe": "low",
    "norway": "low", "no": "low", "nor": "low",
    "denmark": "low", "dk": "low", "dnk": "low",
}


def _score2(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    sbp = adad("Systolic_BP", dataset, patient)
    tc = adad("TC_mmol", dataset, patient)
    if tc is None:
        tc_mg = adad('TotalCholesterol', dataset, patient)
        tc = chol_mmol(tc_mg)
    hdl = adad("HDL_mmol", dataset, patient)
    if hdl is None:
        hdl = chol_mmol(adad("HDL", dataset, patient))
    tc_mg = tc * 38.67
    hdl_mg = hdl * 38.67
    smoker = flag_or_assume("Smoking", patient, 0, 'auto')
    # FIX P26: unknown DiabetesFlag falls back to known diagnoses, disclosed.
    dm = flag_or_assume("DiabetesFlag", patient,
                        1 if darad_tashkhis("Diabetes_Mellitus", diagnoses) else 0,
                        "auto")

    country = str(patient.get("Country") or patient.get("country") or '').strip().lower()
    # FIX P9: a silent "low" region underestimates risk for high-risk
    # countries (the app does not collect Country, so this fired always).
    _region_given = bool(patient.get("SCORE2_Region")) or country in SCORE2_REGION_BY_COUNTRY
    region = str(patient.get("SCORE2_Region") or
                 SCORE2_REGION_BY_COUNTRY.get(country, "low")).lower()
    _region_warn = [] if _region_given else [
        "SCORE2 region defaulted to 'low' (no Country/SCORE2_Region); "
        "risk is underestimated for higher-risk regions."]

    if not (age and age > 0 and sbp and sbp > 0 and tc and tc > 0 and hdl and hdl > 0):
        return {
            "probability": None,
            "status": "Not computable",
            "riskLevel": "Unknown",
            "riskBand": "Not computable",
            "warnings": ["SCORE2 requires positive values for Age, SBP, Total Cholesterol, and HDL."],
            "interpretationFa": "محاسبه SCORE2 ممکن نیست: سن، فشار خون سیستولیک، کلسترول تام و HDL باید بزرگ‌تر از صفر باشند."
        }
    sex_key = "F" if gender == "female" else "M"
    c = _SCORE2[sex_key]
    cage = (age - 60.0) / 5.0
    csbp = (sbp - 120.0) / 20.0
    ctc = tc - 6.0
    chdl = (hdl - 1.3) / 0.5
    lp = (c[0] * cage + c[1] * smoker + c[2] * csbp + c[3] * dm
          + c[4] * ctc + c[5] * chdl
          + c[6] * cage * smoker + c[7] * cage * csbp
          + c[8] * cage * ctc + c[9] * cage * chdl + c[10] * cage * dm)
    uncal = 1.0 - c[11] ** _safe_exp(lp)
    uncal = _clamp(uncal, 1e-9, 1.0 - 1e-9)
    rec = _SCORE2_RECAL.get(region, _SCORE2_RECAL["low"])
    s1, s2 = (rec[0], rec[1]) if sex_key == "M" else (rec[2], rec[3])
    prob = 1.0 - _safe_exp(-_safe_exp(s1 + s2 * _safe_log(-_safe_log(1.0 - uncal))))
    prob = _clamp(prob, 0.0, 1.0)


    if age < 50:
        cuts = (0.025, 0.075)
    else:
        cuts = (0.05, 0.10)
    if prob < cuts[0]:
        band, lvl = "Low-to-moderate", "Low"
    elif prob < cuts[1]:
        band, lvl = 'High', "High"
    else:
        band, lvl = "Very high", "Very High"
    if prob >= cuts[0] and lvl == "Low":
        lvl = "Moderate"
    return {
        'probability': prob,
        "riskLevel": lvl,
        'riskBand': band + " (SCORE2 %s-risk region)" % region,
        "components": {"region": region, "uncalibrated_risk": round(uncal, 4)},
        "interpretationFa": "خطر ۱۰ ساله رویدادهای کشنده و غیرکشنده قلبی-عروقی (SCORE2 اروپا ۲۰۲۱).",
        "warnings": _region_warn + ([] if not dm else ["SCORE2 برای دیابتی‌ها مخصوص SCORE2-Diabetes است؛ از ASCVD/UKPDS نیز استفاده کنید."])
    }


def _score2_gate(dataset, patient, diagnoses, gender):
    age = adad("Age", dataset, patient)
    if age is None or not (40 <= age <= 69):
        return False, "SCORE2 فقط برای سن ۴۰ تا ۶۹ سال معتبر است (Valid for ages 40-69 only)."
    if darad_tashkhis("Cardiovascular_Risk", diagnoses):
        return False, "SCORE2 برای افراد بدون CVD شناخته‌شده است (primary prevention only)."
    return True, ""


_TIMI14 = {0: 0.047, 1: 0.047, 2: 0.083, 3: 0.132, 4: 0.199, 5: 0.262,
           6: 0.409, 7: 0.409}


def _timi_uanstemi(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    n_rf = adad("CAD_RiskFactorCount", dataset, patient)
    known_stenosis = flag_or_assume("Known_CAD_Stenosis", patient, 0, "auto")
    st_dev = flag_or_assume("ST_Deviation", patient, 0, 'auto')
    angina_24h = num_or_assume("Anginal_Episodes_24h", dataset, patient, 0, "auto")
    aspirin7d = flag_or_assume("Aspirin_7d", patient, 0, 'auto')
    trop = adad("Troponin", dataset, patient)
    tropln = adad("Troponin_ULN", dataset, patient)
    elevated_markers = 1 if (trop is not None and tropln is not None
                             and trop > tropln) else 0
    score = int(age >= 65) + int(n_rf >= 3) + known_stenosis + st_dev \
        + int(angina_24h >= 2) + aspirin7d + elevated_markers
    prob = _TIMI14.get(score, 0.409)
    band = "Low" if score <= 2 else ("Intermediate" if score <= 4 else "High")
    return {"probability": prob, "points": score,
            "riskLevel": four_sath(prob, 0.083, 0.132, 0.199),
            "riskBand": band,
            "interpretationFa": "ریسک ۱۴ روزه مرگ/حمله قلبی/ایسکمی شدید نیازمند ریوسکولاریزاسیون (TIMI UA/NSTEMI)."}


_HEART_MACE = {0: 0.017, 1: 0.017, 2: 0.017, 3: 0.017, 4: 0.129,
               5: 0.129, 6: 0.166, 7: 0.50, 8: 0.50, 9: 0.65, 10: 0.65}


def _heart_emtiaz(dataset, patient, gender, diagnoses):
    history = adad('HEART_History', dataset, patient)
    ecg = adad("ECG_ST_Score", dataset, patient)
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    n_rf = num_or_assume('CAD_RiskFactorCount', dataset, patient, 0, "auto")
    trop = adad("Troponin", dataset, patient)
    tropln = adad("Troponin_ULN", dataset, patient)
    ratio = (trop / tropln) if (trop is not None and tropln) else 0.0
    t_pts = 0 if ratio <= 1 else (1 if ratio <= 3 else 2)
    a_pts = 0 if age < 45 else (1 if age < 65 else 2)
    rf_known_athero = flag_or_assume("Known_CAD_Stenosis", patient, 0, "auto")
    r_pts = 2 if (n_rf >= 3 or rf_known_athero) else (1 if n_rf >= 1 else 0)
    score = int(history + ecg + a_pts + r_pts + t_pts)
    prob = _HEART_MACE.get(score, 0.65)
    band = ("Low (0-3)" if score <= 3 else
            "Moderate (4-6)" if score <= 6 else "High (7-10)")
    return {"probability": prob, "points": score,
            "riskLevel": four_sath(prob, 0.017, 0.129, 0.166),
            "riskBand": band,
            "components": {'history': history, "ecg": ecg, "age": a_pts,
                           "risk_factors": r_pts, "troponin": t_pts},
            "interpretationFa": "ریسک ۶ هفته‌ای MACE در درد قفسه سینه (HEART score)."}


_MAGGIC_CONV = [(0, 1.5, 3.9), (5, 2.5, 6.3), (10, 4.1, 10.1),
                (15, 7.1, 16.4), (20, 12.3, 26.3), (25, 21.4, 40.4),
                (30, 35.3, 57.7), (35, 52.6, 75.2), (40, 69.5, 88.4),
                (45, 79.7, 95.5), (50, 84.2, 98.5)]


def _maggic_lookup(score):
    table = _MAGGIC_CONV
    if score <= table[0][0]:
        return table[0][1], table[0][2]
    if score >= table[-1][0]:
        return table[-1][1], table[-1][2]
    for i in range(1, len(table)):
        if score <= table[i][0]:
            s0, a0, b0 = table[i - 1]
            s1, a1, b1 = table[i]
            f = (score - s0) / float(s1 - s0)
            return a0 + f * (a1 - a0), b0 + f * (b1 - b0)
    return table[-1][1], table[-1][2]


def _maggic(dataset, patient, gender, diagnoses):
    ef = adad("LVEF", dataset, patient)
    age = adad("Age", dataset, patient)
    sbp = adad("Systolic_BP", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    cr_mg = adad("Creatinine", dataset, patient)
    cr_umol = cr_mg * 88.4
    male = 1 if gender == "male" else 0
    smoker = flag_or_assume('Smoking', patient, 0, "auto")
    dm = 1 if darad_tashkhis("Diabetes_Mellitus", diagnoses) else 0
    copd = 1 if darad_tashkhis("COPD", diagnoses) else 0
    hf18 = flag_or_assume('HF_Duration_18mo', patient, 0, "auto")
    # FIX P37: unknown HF meds no longer silently count as ON therapy;
    # typical-regimen default (on therapy) is now disclosed per result.
    on_bb = flag_or_assume("On_BetaBlocker", patient, 1, "auto")
    on_acei = flag_or_assume("On_ACEi_ARB", patient, 1, "auto")
    nyha = int(_clamp(num_or_assume("NYHA_Class", dataset, patient, 1, "auto"), 1, 4))

    ef_pts = 7 if ef < 20 else 6 if ef < 25 else 5 if ef < 30 else \
        3 if ef < 35 else 2 if ef < 40 else 0
    if ef < 30:
        age_pts = 0 if age < 55 else 1 if age < 60 else 2 if age < 65 \
            else 4 if age < 70 else 6 if age < 75 else 8 if age < 80 else 10
        sbp_pts = 5 if sbp < 110 else 4 if sbp < 120 else 3 if sbp < 130 \
            else 2 if sbp < 140 else 1 if sbp < 150 else 0
    elif ef < 40:
        age_pts = 0 if age < 55 else 2 if age < 60 else 4 if age < 65 \
            else 6 if age < 70 else 8 if age < 75 else 10 if age < 80 else 13
        sbp_pts = 3 if sbp < 110 else 2 if sbp < 120 else 1 if sbp < 140 else 0
    else:
        age_pts = 0 if age < 55 else 3 if age < 60 else 5 if age < 65 \
            else 7 if age < 70 else 9 if age < 75 else 12 if age < 80 else 15
        sbp_pts = 2 if sbp < 110 else 1 if sbp < 130 else 0
    bmi_pts = 6 if bmi < 15 else 5 if bmi < 20 else 3 if bmi < 25 \
        else 2 if bmi < 30 else 0
    cr_pts = 0 if cr_umol < 90 else 1 if cr_umol < 110 else 2 if cr_umol < 130 \
        else 3 if cr_umol < 150 else 4 if cr_umol < 170 else 5 if cr_umol < 210 \
        else 6 if cr_umol < 250 else 8

    score = (ef_pts + age_pts + sbp_pts + bmi_pts + cr_pts + male
             + (3 if dm else 0) + (2 if copd else 0) + (2 if hf18 else 0)
             + (3 if on_bb == 0 else 0)
             + (1 if on_acei == 0 else 0)
             + {1: 0, 2: 2, 3: 6, 4: 8}[nyha])
    score = int(_clamp(score, 0, 50))
    m1, m3 = _maggic_lookup(score)
    p1, p3 = m1 / 100.0, m3 / 100.0
    band = ("Low" if score <= 13 else
            "Intermediate" if score <= 20 else "High")
    return {"probability": p1, "probability_3y": p3, "points": score,
            "riskLevel": four_sath(p3, 0.20, 0.45, 0.60),
            'riskBand': band,
            "components": {"EF": ef_pts, 'Age': age_pts, "SBP": sbp_pts,
                           "BMI": bmi_pts, 'Creatinine': cr_pts},
            "interpretationFa": ("پیش‌بینی مرگ‌ومیر ۱ ساله و ۳ ساله در نارسایی قلبی "
                                 "بر اساس متا-آنالیز جهانی MAGGIC (تبدیل نمودار رسمی "
                                 "با درون‌یابی، برای جزئیات دقیق به heartfailurerisk.org مراجعه شود).")}


def _maggic_gate(dataset, patient, diagnoses, gender):
    if not darad_tashkhis("Heart_Failure", diagnoses) and \
       parcham_bimar("HF", patient) != 1:
        return False, "MAGGIC فقط برای بیماران با تشخیص نارسایی قلبی است."
    return True, ""


_H2FPEF_LOW, _H2FPEF_HIGH = 1, 6


def _h2fpef(dataset, patient, gender, diagnoses):
    bmi = adad("BMI", dataset, patient)
    n_bp_meds = num_or_assume("Antihypertensive_Count", dataset, patient, 0, "auto")
    afib = 1 if (flag_or_assume("AF", patient, 0, "auto") == 1
                 or darad_tashkhis("Atrial_Fibrillation", diagnoses)) else 0
    pasp = adad("PASP", dataset, patient)
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    ee = adad('E_e_ratio', dataset, patient)
    score = (2 if bmi > 30 else 0) + (1 if n_bp_meds >= 2 else 0) \
        + (3 if afib else 0) + (1 if pasp > 35 else 0) \
        + (1 if age > 60 else 0) + (1 if ee >= 9 else 0)
    if score <= 1:
        prob, band, lvl = 0.10, "Low likelihood (rule-out zone)", "Low"
    elif score <= 5:
        prob, band, lvl = 0.55, 'Intermediate (need further testing)', "Moderate"
    else:
        prob, band, lvl = 0.95, "High likelihood of HFpEF", "Very High"
    return {"probability": prob, "points": score, "riskLevel": lvl,
            "riskBand": band,
            "interpretationFa": "احتمال تشخیصی نارسایی قلبی با EF حفظ‌شده (H2FPEF; Reddy 2018). امتیازات: {}".format(band)}


_CHA2DS2VASC_ANNUAL = {0: 0.0, 1: 0.013, 2: 0.022, 3: 0.032, 4: 0.040,
                       5: 0.067, 6: 0.098, 7: 0.096, 8: 0.067, 9: 0.152}


def _cha2ds2vasc(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, "auto")
    chf = 1 if (flag_or_assume("HF", patient, 0, "auto") == 1
                or darad_tashkhis('Heart_Failure', diagnoses)) else 0
    htn = 1 if (flag_or_assume('Hypertension', patient, 0, "auto") == 1
                or darad_tashkhis("Hypertension", diagnoses)
                or (num_or_assume('Systolic_BP', dataset, patient, 0, "auto")) >= 140) else 0
    dm = 1 if darad_tashkhis('Diabetes_Mellitus', diagnoses) else 0
    stroke = flag_or_assume("Stroke", patient, 0, "auto")
    vascular = flag_or_assume("Vascular_Disease", patient, 0, "auto")
    vascular = max(vascular, 1 if darad_tashkhis("PAD", diagnoses) else 0)
    score = chf + htn + (2 if age >= 75 else 0) + dm + 2 * stroke \
        + vascular + (1 if 65 <= age <= 74 else 0) \
        + (1 if gender == "female" else 0)
    annual = _CHA2DS2VASC_ANNUAL.get(int(score), 0.152)
    band = ("Low (score 0-1)" if score <= 1 else
            "Moderate (score 2)" if score == 2 else "High (>=3)")
    return {'probability': annual, "points": int(score),
            "riskLevel": four_sath(annual, 0.013, 0.022, 0.04),
            "riskBand": band,
            "components": {"HF": chf, "HTN": htn, "DM": dm, "Stroke": stroke,
                           "Vascular": vascular},
            "interpretationFa": "خطر سالانه سکته مغزی/ترومبوآمبولی سیستمیک در فیبریلاسیون دهلیزی (CHA2DS2-VASc)."}


def _cha_gate(dataset, patient, diagnoses, gender):
    if not (darad_tashkhis("Atrial_Fibrillation", diagnoses)
            or parcham_bimar("AF", patient) == 1):
        return False, "این مدل فقط برای بیماران مبتلا به فیبریلاسیون دهلیزی است."
    return True, ""


_HASBLED_ANNUAL = {0: 0.0113, 1: 0.0102, 2: 0.0188, 3: 0.0374, 4: 0.0870,
                   5: 0.125, 6: 0.125, 7: 0.125, 8: 0.125, 9: 0.125}


def _has_bled(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, "auto")
    sbp = num_or_assume('Systolic_BP', dataset, patient, 0, "auto")
    cr = num_or_assume("Creatinine", dataset, patient, 0, "auto")
    bili = adad('Bilirubin', dataset, patient)
    alt = adad("ALT", dataset, patient)
    renal = 1 if (flag_or_assume("Dialysis", patient, 0, "auto") == 1 or cr > 2.26) else 0
    liver = 1 if (darad_tashkhis("Cirrhosis", diagnoses)
                  or (bili is not None and bili > 2.0)
                  or (alt is not None and alt > 120)) else 0
    stroke = flag_or_assume("Stroke", patient, 0, "auto")
    bleeding = flag_or_assume('Prior_Bleeding', patient, 0, 'auto')
    labile_inr = flag_or_assume('Labile_INR', patient, 0, "auto")
    drugs = 1 if (flag_or_assume('Antiplatelet', patient, 0, "auto") == 1
                  or flag_or_assume("NSAID", patient, 0, "auto") == 1) else 0
    alcohol = flag_or_assume("Alcohol_8_per_week", patient, 0, "auto")
    htn_uncontrolled = 1 if sbp > 160 else 0
    score = (htn_uncontrolled + renal + liver + stroke + bleeding
             + labile_inr + (1 if age > 65 else 0) + drugs + alcohol)
    annual = _HASBLED_ANNUAL.get(int(score), 0.125)
    return {"probability": annual, "points": int(score),
            "riskLevel": 'High' if score >= 3 else "Moderate" if score == 2 else 'Low',
            'riskBand': "High risk (>=3)" if score >= 3 else "Low-moderate (<3)",
            "interpretationFa": "خطر سالانه خونریزی عمده هنگام مصرف وارفارین در AF (HAS-BLED)."}


_ORBIT_TABLE = {0: 0.024, 1: 0.024, 2: 0.024, 3: 0.047, 4: 0.081, 5: 0.081}


def _orbit_af(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    hb = adad("Hb", dataset, patient)
    egfr = adad("eGFR", dataset, patient)
    anemia_limit = 13.0 if gender == 'male' else 12.0
    anemia = 1 if (flag_or_assume('Anemia_History', patient, 0, "auto") == 1
                   or (hb is not None and hb < anemia_limit)) else 0
    bleeding = flag_or_assume("Prior_Bleeding", patient, 0, "auto")
    renal = 1 if (egfr is not None and egfr < 60) else 0
    antiplatelet = flag_or_assume("Antiplatelet", patient, 0, "auto")


    score = (1 if age >= 75 else 0) + 2 * anemia + 2 * bleeding \
        + renal + antiplatelet
    if score <= 2:
        band, prob = "Low", 0.024
    elif score == 3:
        band, prob = 'Intermediate', 0.047
    else:
        band, prob = "High", 0.081
    return {'probability': prob, "points": int(score),
            "riskLevel": four_sath(prob, 0.024, 0.047, 0.081),
            'riskBand': band,
            "interpretationFa": "خطر سالانه خونریزی عمده با داروهای ضدانعقاد خوراکی در AF (ORBIT-AF)."}


def _atria_bleed(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    hb = adad('Hb', dataset, patient)
    egfr = adad('eGFR', dataset, patient)
    anemia_limit = 13.0 if gender == "male" else 12.0
    anemia = 3 if (hb is not None and hb < anemia_limit) else 0
    severe_renal = 3 if (flag_or_assume("Dialysis", patient, 0, "auto") == 1
                         or (egfr is not None and egfr < 30)) else 0
    bleeding = flag_or_assume("Prior_Bleeding", patient, 0, "auto")
    htn = 1 if (darad_tashkhis("Hypertension", diagnoses)
                or (num_or_assume("Systolic_BP", dataset, patient, 0, "auto")) >= 140) else 0
    score = anemia + severe_renal + (2 if age >= 75 else 0) + bleeding + htn
    band = ('Low (0-3)' if score <= 3 else
            "Intermediate (4)" if score == 4 else "High (>=5)")
    prob = {0: 0.0076, 1: 0.010, 2: 0.014, 3: 0.024, 4: 0.043,
            5: 0.058, 6: 0.058, 7: 0.058, 8: 0.058, 9: 0.058,
            10: 0.058, 11: 0.058}.get(int(score), 0.058)
    return {"probability": prob, "points": int(score),
            "riskLevel": four_sath(prob, 0.014, 0.024, 0.043),
            "riskBand": band,
            'interpretationFa': "خطر سالانه خونریزی در AF (ATRIA bleeding risk)."}


_ABCD2_2DAY = {0: 0.010, 1: 0.010, 2: 0.010, 3: 0.010, 4: 0.041, 5: 0.041,
               6: 0.081, 7: 0.081}


def _abcd2(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, 'auto')
    sbp = num_or_assume("Systolic_BP", dataset, patient, 0, "auto")
    dbp = num_or_assume("Diastolic_BP", dataset, patient, 0, "auto")
    clinical = adad('ABCD2_Clinical', dataset, patient)
    duration = num_or_assume("TIA_Duration_Min", dataset, patient, 0, "auto")
    dm = 1 if darad_tashkhis('Diabetes_Mellitus', diagnoses) else 0
    score = (1 if age >= 60 else 0) \
        + (1 if (sbp >= 140 or dbp >= 90) else 0) \
        + int(_clamp(clinical or 0, 0, 2)) \
        + (2 if duration >= 60 else 1 if duration >= 10 else 0) + dm
    prob = _ABCD2_2DAY.get(score, 0.081)
    band = "Low (0-3)" if score <= 3 else "Moderate (4-5)" if score <= 5 \
        else "High (6-7)"
    return {"probability": prob, "points": score, "riskBand": band,
            "riskLevel": four_sath(prob, 0.01, 0.041, 0.081),
            "interpretationFa": "خطر سکته مغزی در ۲ روز پس از TIA (ABCD2)"}


def _wells_dvt(dataset, patient, gender, diagnoses):
    pts = 0.0
    pts += 1 if flag_or_assume("ActiveCancer", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume('PriorVTE', patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Paralysis_Paresis_Cast", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Bedridden_3d_Or_Surgery_4wk", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Leg_Tenderness", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Whole_Leg_Swelling", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Calf_Swelling_3cm", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Pitting_Edema_Unilateral", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Collateral_Veins", patient, 0, "auto") else 0
    pts -= 2 if flag_or_assume("Alternative_Diagnosis_More_Likely", patient, 0, "auto") else 0
    band = "DVT likely" if pts >= 2 else "DVT unlikely"
    prob = 0.30 if pts >= 2 else 0.06
    return {"probability": prob, "points": pts, "riskBand": band,
            "riskLevel": "High" if pts >= 2 else 'Low',
            "interpretationFa": "احتمال پیش‌آزمون DVT (Wells two-tier)."}


def _wells_pe(dataset, patient, gender, diagnoses):
    pts = 0.0
    pts += 3 if flag_or_assume("Clinical_Signs_DVT", patient, 0, "auto") else 0
    pts += 3 if flag_or_assume("PE_Most_Likely_Diagnosis", patient, 0, "auto") else 0
    hr = num_or_assume("Heart_Rate", dataset, patient, 0, "auto")
    pts += 1.5 if hr > 100 else 0
    pts += 1.5 if flag_or_assume("Surgery_Immobilization_4wk", patient, 0, "auto") else 0
    pts += 1.5 if flag_or_assume('PriorVTE', patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("Hemoptysis", patient, 0, "auto") else 0
    pts += 1 if flag_or_assume("ActiveCancer", patient, 0, "auto") else 0
    if pts <= 1:
        band, prob, lvl = "Low probability", 0.013, 'Low'
    elif pts <= 6:
        band, prob, lvl = 'Moderate probability', 0.162, "Moderate"
    else:
        band, prob, lvl = "High probability", 0.375, "High"
    return {"probability": prob, "points": pts, "riskBand": band,
            "riskLevel": lvl,
            "interpretationFa": 'احتمال پیش‌آزمون آمبولی ریه (Wells PE, three-tier).'}


def _geneva_revised(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, 'auto')
    hr = num_or_assume("Heart_Rate", dataset, patient, 0, "auto")
    pts = 0.0
    pts += 1 if age > 65 else 0
    pts += 3 if flag_or_assume("PriorVTE", patient, 0, "auto") else 0
    pts += 2 if flag_or_assume('Surgery_Fracture_1mo', patient, 0, "auto") else 0
    pts += 2 if flag_or_assume("ActiveCancer", patient, 0, "auto") else 0
    pts += 3 if flag_or_assume("Unilateral_Leg_Pain", patient, 0, "auto") else 0
    pts += 2 if flag_or_assume("Hemoptysis", patient, 0, "auto") else 0
    pts += 3 if 75 <= hr < 95 else (5 if hr >= 95 else 0)
    pts += 4 if flag_or_assume("Unilateral_Edema_With_Pain", patient, 0, "auto") else 0
    if pts <= 3:
        band, prob = "Low probability", 0.08
    elif pts <= 10:
        band, prob = "Intermediate probability", 0.28
    else:
        band, prob = "High probability", 0.74
    return {'probability': prob, "points": pts, "riskBand": band,
            "riskLevel": four_sath(prob, 0.08, 0.28, 0.6),
            "interpretationFa": "احتمال پیش‌آزمون آمبولی ریه (Revised Geneva)."}


def _spesi(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, "auto")
    hr = num_or_assume("Heart_Rate", dataset, patient, 0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 120, "auto")
    spo2 = num_or_assume("SpO2", dataset, patient, 99, 'auto')
    cancer = 1 if flag_or_assume('ActiveCancer', patient, 0, "auto") else 0
    cardiopulm = 1 if (flag_or_assume("Chronic_Cardiopulmonary", patient, 0, "auto")
                       or darad_tashkhis("COPD", diagnoses)
                       or darad_tashkhis('Heart_Failure', diagnoses)) else 0
    score = int(age > 80) + cancer + cardiopulm + int(hr >= 110) \
        + int(sbp < 100) + int(spo2 < 90)
    low = score == 0
    return {"probability": 0.013 if low else 0.093, "points": score,
            'riskBand': 'Low risk (0)' if low else 'High risk (>=1)',
            "riskLevel": "Low" if low else "High",
            "interpretationFa": "مرگ‌ومیر ۳۰ روزه پس از آمبولی ریه (sPESI؛ Jimenez 2010). کم‌خطر: ~۱٪، پرخطر (>=۱): ~۱۰٪"}


CAPRINI_1PT = ["Age_41_60", 'Minor_Surgery', "BMI_Over25", "Swollen_Legs",
               'Varicose_Veins', "Pregnant_Postpartum", 'Recurrent_Miscarriage',
               "OCP_or_HRT", "Sepsis_Past_Month", "Serious_Lung_Disease",
               "Abnormal_PFT", "Acute_MI", "CHF_Past_Month", "IBD_History",
               "Bed_Rest_Medical"]
CAPRINI_2PT = ["Age_61_74", 'Arthroscopic_Surgery', "Major_Surgery_45min",
               "Laparoscopic_45min", 'Malignancy_Present', "Central_Venous_Access",
               'Plaster_Cast', "Confined_Bed_72h"]
CAPRINI_3PT = ["Age_75_Plus", "FamilyHistory_VTE", "Personal_VTE_History",
               "Factor_V_Leiden", "Prothrombin_20210A", "Lupus_Anticoagulant",
               "Anticardiolipin", "High_Homocysteine", "HIT_History",
               "Other_Thrombophilia"]
CAPRINI_5PT = ["Stroke_Past_Month", "Elective_Arthroplasty",
               'Hip_Pelvis_Leg_Fracture', "Multiple_Trauma_Month",
               'Spinal_Cord_Injury_Month']


def _caprini(dataset, patient, gender, diagnoses):
    score = 0
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    bmi = num_or_assume("BMI", dataset, patient, 0, 'auto')
    score += 1 if 41 <= age <= 60 else 2 if 61 <= age <= 74 else \
        (3 if age >= 75 else 0)
    score += 1 if bmi > 25 else 0
    for items, w in ((CAPRINI_1PT, 1), (CAPRINI_2PT, 2),
                     (CAPRINI_3PT, 3), (CAPRINI_5PT, 5)):
        for it in items:
            if it.startswith("Age_") or it.startswith("BMI_"):
                continue
            if flag_or_assume(it, patient, 0, "auto"):
                score += w
    if darad_tashkhis("VTE", diagnoses):
        score += 3
    if score == 0:
        band, prob = "Very low (<0.5%)", 0.005
    elif score <= 2:
        band, prob = 'Low (~1.5%)', 0.015
    elif score <= 4:
        band, prob = "Moderate (~3%)", 0.03
    else:
        band, prob = "High (~6%+; prophylaxis indicated)", 0.061
    return {'probability': prob, "points": score, "riskBand": band,
            "riskLevel": four_sath(prob, 0.015, 0.03, 0.06),
            "interpretationFa": "ریسک ترومبوآمبولی وریدی در بیماران جراحی (Caprini 2013)."}


def _padua(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    bmi = num_or_assume("BMI", dataset, patient, 0, "auto")
    score = 0
    score += 3 if flag_or_assume("ActiveCancer", patient, 0, "auto") else 0
    score += 3 if (flag_or_assume("PriorVTE", patient, 0, "auto")
                   or darad_tashkhis("VTE", diagnoses)) else 0
    score += 3 if flag_or_assume("Reduced_Mobility_3d", patient, 0, "auto") else 0
    score += 3 if flag_or_assume("Known_Thrombophilia", patient, 0, "auto") else 0
    score += 2 if flag_or_assume("Recent_Trauma_Surgery_1mo", patient, 0, "auto") else 0
    score += 2 if age >= 70 else 0
    score += 1 if (darad_tashkhis("Heart_Failure", diagnoses)
                   or flag_or_assume("Respiratory_Failure", patient, 0, "auto")) else 0
    score += 1 if flag_or_assume('Acute_MI_Or_Stroke', patient, 0, "auto") else 0
    score += 1 if flag_or_assume('Acute_Infection_Or_Rheumatologic', patient, 0, "auto") else 0
    score += 1 if bmi >= 30 else 0
    score += 1 if flag_or_assume("Ongoing_Hormone_Treatment", patient, 0, "auto") else 0
    high = score >= 4
    return {'probability': 0.11 if high else 0.003, "points": score,
            "riskBand": "High risk (>=4)" if high else "Low risk (<4)",
            'riskLevel': "High" if high else "Low",
            "interpretationFa": "ریسک VTE در بیماران داخلی بستری (Padua; ۱۱٪ در پرخطر بدون پروفیلاکسی)."}


def _dlcn(dataset, patient, gender, diagnoses):
    ldl = adad("LDL", dataset, patient)
    score = 0

    score += 1 if flag_or_assume("FHx_FirstDegree_HighLDL", patient, 0, "auto") else 0
    score += 2 if flag_or_assume("FHx_FirstDegree_Premature_CAD", patient, 0, "auto") else 0
    score += 6 if flag_or_assume("FHx_FirstDegree_Xanthoma_Arcus", patient, 0, "auto") else 0
    score += 2 if flag_or_assume("FHx_Child_HighLDL", patient, 0, "auto") else 0

    score += 2 if flag_or_assume("Personal_Premature_CAD", patient, 0, "auto") else 0
    score += 1 if flag_or_assume("Personal_Premature_CVD_PAD", patient, 0, "auto") else 0

    score += 6 if flag_or_assume("Tendon_Xanthomas", patient, 0, "auto") else 0
    score += 4 if flag_or_assume("Arcus_Cornealis_Before45", patient, 0, "auto") else 0

    ldl_mmol = ldl / 38.67
    if ldl_mmol >= 8.5:
        score += 8
    elif ldl_mmol >= 6.5:
        score += 5
    elif ldl_mmol >= 5.0:
        score += 3
    elif ldl_mmol >= 4.0:
        score += 1
    if score >= 9:
        band = 'Definite FH'
    elif score >= 6:
        band = "Probable FH"
    elif score >= 3:
        band = "Possible FH"
    else:
        band = 'Unlikely FH'
    prob = {'Definite FH': 0.95, "Probable FH": 0.80,
            "Possible FH": 0.35, 'Unlikely FH': 0.05}[band]
    return {'probability': prob, "points": score, "riskBand": band,
            'riskLevel': "Very High" if band == "Definite FH" else
                         "High" if band == "Probable FH" else
                         'Moderate' if band == "Possible FH" else "Low",
            "interpretationFa": "احتمال هایپرکلسترولمی خانوادگی بر اساس امتیاز بالینی DLCN (WHO criteria). راهنمای قطعی ژنتیک نیست."}


def _pad_abi(dataset, patient, gender, diagnoses):
    abi = adad("ABI", dataset, patient)
    if abi > 1.40:
        band, prob, lvl = "Non-compressible arteries (>1.40)", None, "Moderate"
    elif abi >= 1.00:
        band, prob, lvl = "Normal (1.00-1.40)", 0.02, "Low"
    elif abi >= 0.91:
        band, prob, lvl = "Borderline (0.91-0.99)", 0.08, "Low"
    elif abi >= 0.71:
        band, prob, lvl = "Mild PAD (0.71-0.90)", 0.60, "Moderate"
    elif abi >= 0.41:
        band, prob, lvl = "Moderate PAD (0.41-0.70)", 0.85, "High"
    else:
        band, prob, lvl = "Severe PAD (<=0.40)", 0.97, "Very High"
    out = {'riskBand': band, "riskLevel": lvl,
           "probability": prob,
           "interpretationFa": "تفسیر شاخص مچ-بازو برای بیماری شریانی محیطی (TASC/AHA)."}
    return out


def _findrisc(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    bmi = num_or_assume("BMI", dataset, patient, 0, "auto")
    waist = num_or_assume("Waist", dataset, patient, 0, "auto")


    _act = parcham_bimar("PhysicalActivity", patient)
    if _act is None:
        _impute_sabt("PhysicalActivity", "assumed active", "context")
        inactive = 0
    else:
        inactive = 1 if _act == 0 else 0
    _veg = parcham_bimar("DailyFruitVeg", patient)
    if _veg is None:
        _impute_sabt("DailyFruitVeg", "assumed daily intake", "context")
        no_veg = 0
    else:
        no_veg = 1 if _veg == 0 else 0
    bp_meds = flag_or_assume("BpTreated", patient, 0, "auto")
    hx_gluc = flag_or_assume("HxHighGlucose", patient, 0, "auto")
    fhx = str(meghdar("FamilyHistory_DM", dataset, patient)
              or '').strip().lower() or adad("FamilyHistory_DM", dataset, patient)
    pts = 0
    pts += 0 if age < 45 else 2 if age < 55 else 3 if age < 65 else 4
    pts += 0 if bmi < 25 else 1 if bmi < 30 else 3
    if gender == "male":
        pts += 0 if waist < 94 else 3 if waist <= 102 else 4
    else:
        pts += 0 if waist < 80 else 3 if waist <= 88 else 4
    pts += 2 * inactive
    pts += 1 * no_veg
    pts += 2 * bp_meds
    pts += 5 * hx_gluc
    if isinstance(fhx, str):
        pts += 5 if fhx in ("1", "first", "true", "parent", "sibling") else \
            3 if fhx in ("2", "second", 'relative') else 0
    else:
        pts += 5 if fhx else 0
    score = pts

    if score < 7:
        prob, band = 0.01, "Low (1 in 100)"
    elif score <= 11:
        prob, band = 0.04, "Slightly elevated (1 in 25)"
    elif score <= 14:
        prob, band = 0.17, "Moderate (1 in 6)"
    elif score <= 20:
        prob, band = 0.33, "High (1 in 3)"
    else:
        prob, band = 0.50, "Very high (1 in 2)"
    max_pts = 26
    return {"probability": prob, "points": score, 'maxPoints': max_pts,
            "riskBand": band,
            "riskLevel": four_sath(prob, 0.04, 0.17, 0.33),
            'components': {"age": age, 'bmi': bmi, 'waist': waist,
                           "inactive": inactive, "low_veg": no_veg,
                           "bp_meds": bp_meds, 'hx_high_glucose': hx_gluc},
            "interpretationFa": (
                f"امتیاز FINDRISC = {score} از {max_pts} — خطر ابتلا به "
                f"دیابت نوع ۲ در ۱۰ سال آینده حدود {prob*100:.0f}٪ "
                f"({band}). این ابزار غربالگری است؛ تأیید با قند ناشتا "
                "یا HbA1c لازم است.")}


def _cdc_prediabetes(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, "auto")
    bmi = num_or_assume("BMI", dataset, patient, 0, "auto")
    male = 1 if gender == 'male' else 0
    gdm = flag_or_assume("GestationalDM", patient, 0, "auto")
    fhx = flag_or_assume("FamilyHistory_DM", patient, 0, 'auto')
    htn = 1 if (flag_or_assume("BpTreated", patient, 0, "auto") == 1
                or (num_or_assume('Systolic_BP', dataset, patient, 0, "auto")) >= 140
                or darad_tashkhis("Hypertension", diagnoses)) else 0
    # FIX P26: default ACTIVE (preserves prior score) but now disclosed.
    inactive = 1 if flag_or_assume("PhysicalActivity", patient, 1, "auto") == 0 else 0
    pts = 0
    pts += 0 if age < 40 else 1 if age < 50 else 2 if age < 60 else 3
    if male:
        pts += 1
    if gdm and not male:
        pts += 1
    pts += fhx + htn + inactive
    pts += 0 if bmi < 25 else 1 if bmi < 30 else 2 if bmi < 40 else 3
    prob = 0.10 if pts < 5 else 0.50 if pts >= 9 else 0.25
    band = 'Lower risk (<5)' if pts < 5 else "High risk (>=5): formal testing indicated"
    return {"probability": prob, "points": pts, 'riskBand': band,
            "riskLevel": "Low" if pts < 5 else 'High' if pts >= 9 else "High",
            "interpretationFa": "غربالگری پرخطر بودن برای پری‌دیابت (CDC/ADA). امتیاز ۵+ یعنی انجام تست خونی."}


def _metabolic_syndrome(dataset, patient, gender, diagnoses):
    waist = num_or_assume("Waist", dataset, patient, 0, "auto")
    tg = adad("Triglycerides", dataset, patient)
    hdl = adad("HDL", dataset, patient)
    fbs = adad("FBS", dataset, patient)
    if fbs is None:
        fbs = adad("Glucose", dataset, patient)
    sbp = adad("Systolic_BP", dataset, patient)
    dbp = adad("Diastolic_BP", dataset, patient)


    wc_m = _num(patient.get("WaistCutoff_M") ) or 94
    wc_f = _num(patient.get("WaistCutoff_F") ) or 80
    criteria = {}
    criteria["central_obesity"] = waist >= (wc_m if gender == "male" else wc_f)
    criteria["elevated_TG"] = (tg is not None and tg >= 150)
    criteria["low_HDL"] = (hdl is not None and hdl < (40 if gender == "male" else 50))
    criteria['elevated_BP'] = (sbp is not None and sbp >= 130) or \
        (dbp is not None and dbp >= 85)
    criteria["elevated_glucose"] = (fbs is not None and fbs >= 100)
    dm = darad_tashkhis("Diabetes_Mellitus", diagnoses)
    criteria["elevated_glucose"] = criteria["elevated_glucose"] or dm


    met_count = sum(1 for k, v in criteria.items() if v)
    present = met_count >= 3
    return {"probability": 1.0 if present else 0.0,
            "points": int(met_count),
            "riskBand": "Criteria met (>=3 of 5, JIS harmonized)" if present
                        else "Criteria not met",
            "riskLevel": 'High' if present else "Low",
            'components': criteria,
            "interpretationFa": "JIS 2009: سندرم متابولیک با حداقل ۳ مورد از ۵ معیار (چاقی مرکزی اجباری نیست)."}


def _kfre4(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    egfr = adad("eGFR", dataset, patient)
    acr = adad("ACR", dataset, patient)
    male = 1 if gender == "male" else 0
    lp = (-0.2201 * (age / 10.0 - 7.036)
          + 0.2467 * (male - 0.5642)
          - 0.5567 * (egfr / 5.0 - 7.222)
          + 0.4510 * (_safe_log(acr) - 5.137))
    ex = _safe_exp(lp)
    p2 = 1.0 - 0.9832 ** ex
    p5 = 1.0 - 0.9365 ** ex
    p2 = _clamp(p2, 0.0, 1.0)
    p5 = _clamp(p5, 0.0, 1.0)
    if p5 < 0.03:
        band = 'Low (KDIGO green/yellow)'
    elif p5 < 0.05:
        band = "Moderate (consider nephrology referral threshold 5y 3-5%)"
    elif p5 < 0.20:
        band = "High (5y >=5%: referral recommended)"
    else:
        band = "Very high (2y >=20%: multidisciplinary kidney care)"
    return {'probability': round(p2, 4), "probability_5y": round(p5, 4),
            "riskBand": band,
            'riskLevel': four_sath(p2, 0.05, 0.20, 0.40),
            "interpretationFa": "خطر نارسایی کلیه نیازمند دیالیز در ۲ و ۵ سال آینده (KFRE Tangri). مرز ارجاع به نفرولوژی: ۵ ساله ≥۵٪، برنامه‌ریزی دیالیز: ۲ ساله ≥۲۰-۴۰٪"}


def _hepatic_steatosis_gate(dataset, patient, diagnoses, gender):
    """NAFLD fibrosis scores presuppose steatosis; they are not screens."""
    if (darad_tashkhis("NAFLD", diagnoses)
            or darad_tashkhis("Fatty_Liver", diagnoses)
            or darad_tashkhis("NASH", diagnoses)
            or darad_tashkhis("Chronic_Liver_Disease", diagnoses)):
        return True, ""
    alt = adad("ALT", dataset, patient)
    ast = adad("AST", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    # any objective hint of hepatic involvement is enough to proceed
    if (alt is not None and alt > 40) or (ast is not None and ast > 40):
        return True, ""
    if bmi is not None and bmi >= 30:
        return True, ""
    return False, ("این نمره برای بیماران با کبد چرب *مشکوک یا ثابت‌شده* "
                   "اعتبارسنجی شده، نه غربالگری جمعیت عمومی. بدون شواهد "
                   "درگیری کبدی (آنزیم بالا، BMI≥۳۰، یا تشخیص ثبت‌شده) "
                   "نتیجه گمراه‌کننده است.")


def _metabolic_risk_gate(dataset, patient, diagnoses, gender):
    """Adiposity indices need at least one metabolic abnormality."""
    bmi = adad("BMI", dataset, patient)
    waist = adad("Waist", dataset, patient)
    tg = adad("Triglycerides", dataset, patient)
    hdl = adad("HDL", dataset, patient)
    fbs = adad("FBS", dataset, patient)
    male = gender == "male"
    hits = 0
    if bmi is not None and bmi >= 25:
        hits += 1
    if waist is not None and waist >= (94 if male else 80):
        hits += 1
    if tg is not None and tg >= 150:
        hits += 1
    if hdl is not None and hdl < (40 if male else 50):
        hits += 1
    if fbs is not None and fbs >= 100:
        hits += 1
    if hits or darad_tashkhis("Metabolic_Syndrome", diagnoses):
        return True, ""
    return False, ("هیچ نشانه متابولیکی (BMI≥۲۵، دور کمر بالا، TG≥۱۵۰، "
                   "HDL پایین، یا قند ناشتا ≥۱۰۰) وجود ندارد؛ شاخص‌های "
                   "چاقی در این حالت تفسیرپذیر نیستند.")


def _kfre_gate(dataset, patient, diagnoses, gender):
    egfr = adad("eGFR", dataset, patient)
    if egfr is not None and egfr >= 60 \
            and not darad_tashkhis("Chronic_Kidney_Disease", diagnoses):
        return False, ("KFRE برای بیماران CKD (eGFR<60) معتبرسازی شده است؛ "
                       "برای eGFR نرمال از گرید KDIGO استفاده شود.")
    return True, ""


def _kdigo_ckd(dataset, patient, gender, diagnoses):
    egfr = adad("eGFR", dataset, patient)
    acr = adad("ACR", dataset, patient)
    _pcr_warn = []
    if acr is None:

        pcr = adad('PCR', dataset, patient)
        if pcr is not None:
            # FIX P19: PCR->ACR x0.68 approximation was silent; disclose it.
            acr = pcr * 0.68
            _pcr_warn.append("ACR approximated from PCR (x0.68); KDIGO albuminuria class is approximate.")
    if acr is None:
        return {"status": "Insufficient Data", "missingFeatures": ["ACR"]}
    if egfr >= 90: g = ("G1", ">=90")
    elif egfr >= 60: g = ("G2", "60-89")
    elif egfr >= 45: g = ("G3a", "45-59")
    elif egfr >= 30: g = ("G3b", "30-44")
    elif egfr >= 15: g = ("G4", '15-29')
    else: g = ("G5", "<15")

    if acr < 30: a = ("A1", "<30 mg/g")
    elif acr < 300: a = ("A2", "30-299 mg/g")
    else: a = ("A3", ">=300 mg/g")


    _heatmap = {
        "G1": [0, 1, 2], "G2": [0, 1, 2], "G3a": [1, 2, 3],
        "G3b": [2, 2, 3], "G4": [2, 3, 3], "G5": [3, 3, 3],
    }
    grid = {0: "Low risk (green)", 1: "Moderately increased (yellow)",
            2: "High risk (orange)", 3: "Very high risk (red)"}
    cell = _heatmap[g[0]][{"A1": 0, "A2": 1, "A3": 2}[a[0]]]
    band = grid[cell]
    has_ckd = darad_tashkhis('Chronic_Kidney_Disease', diagnoses)
    prob = {0: 0.05, 1: 0.15, 2: 0.35, 3: 0.60}[cell]
    return {"probability": prob, "riskBand": band,
            "points": cell,
            "riskLevel": ["Low", "Moderate", "High", "Very High"][cell],
            'components': {'GFR_category': g[0] + " (" + g[1] + ')',
                           "Albuminuria_category": a[0] + " (" + a[1] + ")",
                           "ckd_known": has_ckd},
            "warnings": _pcr_warn,
            "interpretationFa": "طبقه‌بندی KDIGO: دسته GFR + آلبومین‌اوری = رنگ خطر شبکه پیش‌آگهی."}


def _kdigo_aki(dataset, patient, gender, diagnoses):
    cr = adad("Creatinine", dataset, patient)
    baseline = adad("Baseline_Creatinine", dataset, patient)
    imputed = False
    if baseline is None or baseline <= 0:
        # KDIGO 2012 (Appendix B / ADQI): when no baseline is known, impute the
        # creatinine that gives an MDRD eGFR of 75 mL/min/1.73 m2 for the
        # patient's age and sex. The eGFR calculated from the *current*
        # creatinine must never be used - it would back-solve to the current
        # value and hide every AKI.
        age = num_or_assume("Age", dataset, patient, 50, "auto")
        age = _clamp(age if age is not None else 50, 18, 100)
        sexf = 0.742 if gender == "female" else 1.0
        baseline = (75.0 / (175.0 * (age ** -0.203) * sexf)) ** (1.0 / -1.154)
        baseline = round(_clamp(baseline, 0.6, 1.3), 2)
        imputed = True
    ratio = cr / baseline
    hypo = (num_or_assume("Systolic_BP", dataset, patient, 100, "auto")) < 90
    if ratio >= 3.0 or cr >= 4.0:
        stage, band = 3, "AKI Stage 3 (KDIGO serum creatinine criteria)"
    elif ratio >= 2.0:
        stage, band = 2, 'AKI Stage 2'
    elif ratio >= 1.5 or cr - baseline >= 0.3:
        stage, band = 1, "AKI Stage 1"
    else:
        stage, band = 0, "No AKI by creatinine criteria"
    if hypo and stage == 0:
        band += " (note: low BP present - fluid responsiveness workup)"
    prob = {0: 0.05, 1: 0.25, 2: 0.50, 3: 0.80}[stage]
    note_fa = "تشخیص مرحله AKI طبق معیار کراتینین KDIGO 2012 (نسبت به کراتینین پایه). اگر پایه واقعی موجود باشد از آن استفاده می‌شود."
    if imputed and stage > 0:
        # One time point cannot separate acute injury from chronic disease.
        band = band.replace("AKI", "Possible AKI (baseline imputed, eGFR-75 rule)")
        prob = round(prob * 0.6, 3)
        note_fa += (" کراتینین پایه موجود نبود و طبق قاعده KDIGO (eGFR فرضی 75) برآورد شد؛ "
                    "با یک اندازه‌گیری، AKI از CKD قابل تفکیک نیست - کراتینین قبلی را وارد کنید.")
    return {"probability": prob, 'points': stage, 'riskBand': band,
            "riskLevel": ['Low', 'Moderate', 'High', 'Very High'][stage],
            'components': {"creatinine": cr, "baseline_estimated": baseline,
                           "baseline_imputed": imputed, 'ratio': round(ratio, 2)},
            'interpretationFa': note_fa}


def _insulin_indices(dataset, patient, gender, diagnoses):
    fbs = adad("FBS", dataset, patient)
    insulin = adad("Insulin", dataset, patient)
    tg = adad('Triglycerides', dataset, patient)
    comps = {}
    probs = []
    if fbs is not None and insulin is not None and fbs > 0 and insulin > 0:
        homa = insulin * fbs / 405.0
        denom = _safe_log10(insulin) + _safe_log10(fbs)
        quicki = 1.0 / denom if abs(denom) > 1e-6 else 0.0
        comps["HOMA_IR"] = round(homa, 2)
        comps["QUICKI"] = round(quicki, 3)
        probs.append(1.0 if homa >= 2.5 else 0.2 if homa < 1.5 else 0.5)
    if fbs is not None and tg is not None and fbs > 0 and tg > 0:
        # FIX P27: the 4.49/4.15 cutoffs belong to the Ln(TG*FBS)/2 variant
        # (range ~3-5); Ln(TG*FBS/2) sits near ~8 and made nearly everyone
        # "positive". Formula and cutoffs are now on the same scale.
        # Original Simental-Mendia 2008 scale: Ln[TG(mg/dL) x FPG(mg/dL)]/2.
        # Cut-offs on this scale: 4.65 (vs HOMA-IR, Simental-Mendia 2008) and
        # 4.68 (vs euglycaemic clamp, Guerrero-Romero JCEM 2010). The previous
        # 4.49/4.15 sex-specific values flagged a normal TG 120 / FPG 95
        # (TyG 4.67) as "IR likely"; they belong to no published validation.
        tyg = _safe_log(tg * fbs) / 2.0
        comps["TyG"] = round(tyg, 2)
        if tyg >= 4.68:
            probs.append(0.80)
        elif tyg >= 4.55:
            probs.append(0.45)      # grey zone (4.55 women / 4.68 men in young-adult cohorts)
        else:
            probs.append(0.15)
    if not probs:
        return {"status": "Insufficient Data"}
    prob = max(probs)
    band = 'IR unlikely' if prob < 0.3 else "Borderline" if prob < 0.7 \
        else "IR likely (per published cutoffs)"
    out = {"probability": prob, "riskBand": band, "components": comps,
           'riskLevel': "High" if prob >= 0.7 else 'Moderate' if prob >= 0.3 else "Low",
           "interpretationFa": "HOMA-IR ≥2.5 یا TyG [Ln(TG×FBS)/2] ≥4.68 (کلمپ، Guerrero-Romero 2010): مقاومت انسولینی محتمل؛ 4.55–4.68 ناحیهٔ خاکستری."}
    return out


def _arr_screen(dataset, patient, gender, diagnoses):
    ald = adad("Aldosterone", dataset, patient)
    pra = adad("Renin_PRA", dataset, patient)
    drc = adad("Renin_DRC", dataset, patient)
    if pra is None and drc is None:
        return {"status": "Insufficient Data", "missingFeatures": ["Renin_PRA"]}
    if ald is None or ald <= 0:
        return {"status": "Insufficient Data", "missingFeatures": ["Aldosterone"]}
    if pra is not None and pra > 0:
        arr = ald / pra
    else:
        arr = (ald / drc) * (100.0 / 1.67) if (drc is not None and drc > 0) else None
    if arr is None:
        return {"status": "Insufficient Data"}
    positive = arr > 30
    confirmed_strong = arr > 40 and ald > 15
    band = ("Screen strongly positive" if confirmed_strong else
            'Screen positive (confirmatory testing needed)' if positive else
            "Screen negative")
    return {"probability": 0.85 if confirmed_strong else 0.60 if positive else 0.05,
            "riskBand": band,
            'riskLevel': "Very High" if confirmed_strong else
                         "High" if positive else "Low",
            "warnings": ["DRC-based ARR uses an assumed unit conversion; verify renin units before acting."]
            if (pra is None or pra <= 0) else [],
            "components": {'ARR': round(arr, 1),
                           "note": "medications (MRA, ACEi/ARB, diuretics, beta-blockers) confound ARR; washout needed"},
            "interpretationFa": "غربالگری هایپرآلدوسترونیسم اولیه (Endocrine Society: ARR>30 مثبت، تأیید با تست سرکوب لازم است)."}


def _fli(dataset, patient, gender, diagnoses):
    tg = adad('Triglycerides', dataset, patient)
    bmi = adad('BMI', dataset, patient)
    ggt = adad("GGT", dataset, patient)
    waist = adad("Waist", dataset, patient)
    x = (0.953 * _safe_log(tg) + 0.139 * bmi + 0.718 * _safe_log(ggt)
         + 0.053 * waist - 15.745)
    fli = 100.0 * logit_to_prob(x)
    if fli < 30:
        band, lvl = 'Fatty liver ruled out (Sn 87%)', "Low"
    elif fli < 60:
        band, lvl = "Indeterminate", "Moderate"
    else:
        band, lvl = "Fatty liver ruled in (Sp 86%)", "High"
    return {'probability': round(fli / 100.0, 4), 'score': round(fli, 1),
            "riskBand": band, "riskLevel": lvl,
            "interpretationFa": "احتمال استئاتوز کبدی (FLI; Bedogni 2006). <30 رد، ≥60 اثبات."}


def _hsi(dataset, patient, gender, diagnoses):
    alt = adad("ALT", dataset, patient)
    ast = adad("AST", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    dm = darad_tashkhis("Diabetes_Mellitus", diagnoses)
    ast_ratio = _safe_div(alt, ast, 1.0) if (ast and ast > 0) else 1.0
    hsi = 8.0 * ast_ratio + (bmi or 25.0) + (2.0 if dm else 0.0) \
        + (2.0 if gender == "female" else 0.0)
    if hsi < 30:
        band, lvl = "NAFLD ruled out (Sn 93%)", 'Low'
    elif hsi <= 36:
        band, lvl = 'Indeterminate', "Moderate"
    else:
        band, lvl = "NAFLD likely (Sp 92%)", "High"
    return {"probability": _clamp((hsi - 20.0) / 25.0, 0.0, 1.0),
            'score': round(hsi, 1), "riskBand": band, "riskLevel": lvl,
            "interpretationFa": "HSI = 8*ALT/AST + BMI (+2 دیابت، +2 زن). >36 یعنی NAFLD محتمل."}


def _fib4(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    ast = adad("AST", dataset, patient)
    alt = adad("ALT", dataset, patient)
    plt = adad("Platelets", dataset, patient)

    if plt is None or plt <= 0 or alt is None or alt <= 0 or ast is None or ast <= 0 or age is None or age <= 0:
        return {'probability': None, "score": None,
                "riskBand": "Not computable",
                'riskLevel': "Unknown",
                "warnings": ["FIB-4 requires positive platelet count and "
                             "ALT; supplied values are out of range."],
                "interpretationFa": (
                    "محاسبه FIB-4 ممکن نیست: پلاکت و ALT باید بزرگ‌تر از "
                    "صفر باشند.")}
    fib4 = age * ast / (plt * math.sqrt(alt))
    low = 2.0 if age >= 65 else 1.30
    if fib4 < low:
        band, lvl = "Low: advanced fibrosis unlikely", "Low"
    elif fib4 <= 2.67:
        band, lvl = "Indeterminate: consider elastography/ELF", "Moderate"
    else:
        band, lvl = "High: advanced fibrosis likely (PPV~80%)", "High"
    return {"probability": _clamp(fib4 / 5.0, 0.0, 1.0),
            "score": round(fib4, 2), 'riskBand': band, 'riskLevel': lvl,
            "interpretationFa": "FIB-4 = سن×AST/(پلاکت×√ALT). کات‌آف پایین برای ≥۶۵ سالگی: ۲.۰."}


def _apri(dataset, patient, gender, diagnoses):
    ast = adad("AST", dataset, patient)
    uln = num_or_assume("AST_ULN", dataset, patient, 40.0, "auto")
    plt = adad('Platelets', dataset, patient)
    if plt is None or plt <= 0 or not uln or uln <= 0 or ast is None:
        return {"probability": None, "score": None,
                "riskBand": "Not computable", 'riskLevel': "Unknown",
                "warnings": ['APRI requires a positive platelet count and '
                             'a positive AST upper reference limit.'],
                "interpretationFa": (
                    "محاسبه APRI ممکن نیست: پلاکت و حد بالای مرجع AST "
                    'باید بزرگ‌تر از صفر باشند.')}
    apri = (ast / uln) / plt * 100.0
    if apri < 0.5:
        band, lvl = "Significant fibrosis ruled out", "Low"
    elif apri <= 1.5:
        band, lvl = "Indeterminate zone", "Moderate"
    elif apri <= 2.0:
        band, lvl = "Significant fibrosis likely", "High"
    else:
        band, lvl = 'Cirrhosis likely (PPV~75%)', "Very High"
    return {"probability": _clamp(apri / 3.0, 0.0, 1.0),
            "score": round(apri, 2), "riskBand": band, "riskLevel": lvl,
            'components': {"AST_ULN_assumed": uln},
            "interpretationFa": "APRI = (AST/ULN)/پلاکت×100. ULN پیش‌فرض ۴۰ تعیین‌شده (قابل‌تغییر با AST_ULN)."}


def _nfs(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    ast_v = adad("AST", dataset, patient)
    alt_v = adad("ALT", dataset, patient)
    if not (ast_v and ast_v > 0 and alt_v and alt_v > 0):
        return {
            "probability": None,
            "score": None,
            "status": "Not computable",
            "riskBand": "Not computable",
            "riskLevel": "Unknown",
            "warnings": ["NFS requires positive AST and ALT values."],
            "interpretationFa": "محاسبه NFS ممکن نیست: مقادیر AST و ALT باید بزرگ‌تر از صفر باشند."
        }
    aar = ast_v / alt_v
    plt = adad("Platelets", dataset, patient)
    alb = adad("Albumin", dataset, patient)
    ifg = 1 if (darad_tashkhis("Diabetes_Mellitus", diagnoses)
                or darad_tashkhis("Prediabetes", diagnoses)
                or (num_or_assume("FBS", dataset, patient, 0, "auto")) >= 110) else 0
    nfs = (-1.675 + 0.037 * age + 0.094 * bmi + 1.13 * ifg
           + 0.99 * aar - 0.013 * plt - 0.66 * alb)
    if nfs < -1.455:
        band, lvl = 'F0-F2 excluded (NPV 93%)', "Low"
    elif nfs <= 0.675:
        band, lvl = "Indeterminate", "Moderate"
    else:
        band, lvl = "Advanced fibrosis (F3-F4) likely (PPV 90%)", "High"
    return {"probability": _clamp((nfs + 2.0) / 4.0, 0.0, 1.0),
            'score': round(nfs, 3), "riskBand": band, "riskLevel": lvl,
            "interpretationFa": 'NFS (Angulo 2007). کات‌آف‌ها: −۱٫۴۵۵ و ۰٫۶۷۵.'}


def _bard(dataset, patient, gender, diagnoses):
    bmi = adad("BMI", dataset, patient)
    aar = adad("AST", dataset, patient) / adad("ALT", dataset, patient)
    dm = darad_tashkhis("Diabetes_Mellitus", diagnoses)
    score = (1 if bmi >= 28 else 0) + (2 if aar >= 0.8 else 0) + (1 if dm else 0)
    band = "Low probability of advanced fibrosis (NPV 96%)" if score < 2 \
        else 'Increased odds of advanced fibrosis (OR 17)'
    return {"probability": 0.15 if score < 2 else 0.66,
            "points": score, "riskBand": band,
            "riskLevel": 'Low' if score < 2 else "High",
            "interpretationFa": "BARD: BMI≥28 (1)، AAR≥0.8 (2)، دیابت (1). ≥2 یعنی فیبروز پیشرفته محتمل."}


def _albi(dataset, patient, gender, diagnoses):
    bili = adad("Bilirubin", dataset, patient)
    alb = adad("Albumin", dataset, patient)
    b_u = bili_umol(bili) if bili is not None else 1.0
    albi = 0.66 * _safe_log10(b_u if b_u and b_u > 0 else 1.0) - 0.085 * ((alb or 4.0) * 10.0)
    if albi <= -2.60:
        grade, prob, lvl = "Grade 1 (good liver function)", 0.1, "Low"
    elif albi <= -1.39:
        grade, prob, lvl = "Grade 2 (intermediate)", 0.5, "Moderate"
    else:
        grade, prob, lvl = "Grade 3 (poor liver function)", 0.85, 'Very High'
    return {"probability": prob, "score": round(albi, 3), "riskBand": grade,
            "riskLevel": lvl,
            "interpretationFa": "ALBI = 0.66×log₁₀(بیلی µmol/L) − 0.085×(آلبومین g/L)."}


_MELD_MORT = {
    "lt10": 0.019, "10-19": 0.06, "20-29": 0.196, "30-39": 0.526, "ge40": 0.713}


def _meld(dataset, patient, gender, diagnoses):
    bili = max(adad("Bilirubin", dataset, patient), 1.0)
    inr = max(adad("INR", dataset, patient), 1.0)
    cr = min(max(adad("Creatinine", dataset, patient), 1.0), 4.0)
    na = adad("Sodium", dataset, patient)
    dialy = flag_or_assume("Dialysis", patient, 0, "auto")
    if dialy:
        cr = 4.0
    meld = 10.0 * (0.957 * _safe_log(cr) + 0.378 * _safe_log(bili)
                   + 1.120 * _safe_log(inr) + 0.643)
    meld = round(meld, 1)
    if na is None:
        _impute_sabt('Sodium', "MELD-Na not computed; plain MELD reported",
                    "context")
        na_c = 137.0
    else:
        na_c = _clamp(na, 125.0, 137.0)
    meld_na = meld + 1.32 * (137.0 - na_c) - 0.033 * meld * (137.0 - na_c)
    meld_na = _clamp(round(meld_na, 1), 6.0, 40.0)
    if meld_na < 10:
        mort, band = _MELD_MORT["lt10"], "90-day mortality ~1.9% (<10)"
        lvl = "Low"
    elif meld_na < 20:
        mort, band = _MELD_MORT["10-19"], "90-day mortality ~6% (10-19)"
        lvl = "Moderate"
    elif meld_na < 30:
        mort, band = _MELD_MORT["20-29"], "90-day mortality ~19.6% (20-29)"
        lvl = "High"
    elif meld_na < 40:
        mort, band = _MELD_MORT['30-39'], "90-day mortality ~52.6% (30-39)"
        lvl = "Very High"
    else:
        mort, band = _MELD_MORT["ge40"], "90-day mortality ~71.3% (>=40)"
        lvl = "Very High"
    return {"probability": mort, "score": meld_na,
            "components": {'MELD': meld, "MELD_Na": meld_na,
                           "sodium_used": na_c},
            "riskBand": band, 'riskLevel': lvl,
            "interpretationFa": "MELD-Na (OPTN/UNOS): اولویت‌بندی پیوند و مرگ‌ومیر ۹۰ روزه بیماری کبدی انتهایی."}


def _meld3(dataset, patient, gender, diagnoses):
    bili = max(adad("Bilirubin", dataset, patient), 1.0)
    inr = max(adad("INR", dataset, patient), 1.0)
    cr = min(max(adad("Creatinine", dataset, patient), 1.0), 3.0)
    alb = _clamp(adad("Albumin", dataset, patient), 1.5, 3.5)
    na = _clamp(num_or_assume("Sodium", dataset, patient, 137.0, "auto"), 125.0, 137.0)
    if flag_or_assume("Dialysis", patient, 0, "auto"):
        cr = 3.0
    female = 1 if gender == "female" else 0
    meld3 = (1.33 * female + 4.56 * _safe_log(bili)
             + 0.82 * (137.0 - na)
             - 0.24 * (137.0 - na) * _safe_log(bili)
             + 9.09 * _safe_log(inr) + 11.14 * _safe_log(cr)
             + 1.85 * (3.5 - alb)
             - 1.83 * (3.5 - alb) * _safe_log(cr) + 6.0)
    meld3 = _clamp(round(meld3), 6, 40)

    s90 = 0.946 ** _safe_exp(0.17698 * meld3 - 3.56)
    mort90 = _clamp(1.0 - s90, 0.0, 1.0)
    lvl = four_sath(mort90, 0.02, 0.06, 0.20)
    return {"probability": mort90, "score": meld3,
            "riskBand": "MELD 3.0 = %d" % meld3,
            "riskLevel": lvl,
            "components": {"MELD30": meld3,
                           "survival90d": round(_clamp(s90, 0, 1), 3)},
            "interpretationFa": "MELD 3.0 (OPTN ۲۰۲۳). مرگ ۹۰ روزه از فرمول بقای منتشرشده Kim ۲۰۲۱."}


def _meld3_gate(dataset, patient, diagnoses, gender):
    if meghdar("Albumin", dataset, patient) is None:
        return False, 'MELD 3.0 به آلبومین نیاز دارد. از MELD-Na استفاده شود.'
    return True, ""


def _child_pugh(dataset, patient, gender, diagnoses):
    bili = adad("Bilirubin", dataset, patient)
    alb = adad("Albumin", dataset, patient)
    inr = adad("INR", dataset, patient)
    ascites = _num(meghdar('Ascites_Grade', dataset, patient))
    enceph = _num(meghdar("Encephalopathy_Grade", dataset, patient))
    score = 0
    score += 1 if bili < 2 else 2 if bili <= 3 else 3
    score += 1 if alb > 3.5 else 2 if alb >= 2.8 else 3
    score += 1 if inr < 1.7 else 2 if inr <= 2.3 else 3


    if ascites is None:
        _impute_sabt("Ascites_Grade", "assumed absent", 'critical')
        asc_i = 0
    else:
        asc_i = int(ascites)
    if enceph is None:
        _impute_sabt("Encephalopathy_Grade", "assumed absent", "critical")
        enc_i = 0
    else:
        enc_i = int(enceph)
    score += {0: 1, 1: 2, 2: 3}[_clamp(asc_i, 0, 2)]
    score += {0: 1, 1: 2, 2: 3}[_clamp(enc_i, 0, 2)]
    cls = "A (5-6)" if score <= 6 else "B (7-9)" if score <= 9 else "C (10-15)"

    surv1 = {"A": 1.0, "B": 0.80, "C": 0.45}[cls[0]]
    return {"probability": 1.0 - surv1, "points": score,
            "riskBand": "Child-Pugh class " + cls,
            'riskLevel': "Low" if cls.startswith('A') else
                         "Moderate" if cls.startswith("B") else 'Very High',
            'interpretationFa': "طبقه Child-Pugh (بیلی‌روبین، آلبومین، INR، آسیت، آنسفالوپاتی). بقای ۱ ساله A~۱۰۰٪، B~۸۰٪، C~۴۵٪"}


_REACHB_RISK = {0: (0.000, 0.000, 0.000), 1: (0.000, 0.000, 0.001),
                2: (0.000, 0.000, 0.001), 3: (0.000, 0.001, 0.002),
                4: (0.000, 0.001, 0.003), 5: (0.001, 0.002, 0.005),
                6: (0.001, 0.003, 0.007), 7: (0.002, 0.005, 0.012),
                8: (0.003, 0.008, 0.020), 9: (0.005, 0.012, 0.032),
                10: (0.009, 0.020, 0.052), 11: (0.014, 0.033, 0.084),
                12: (0.023, 0.053, 0.134), 13: (0.037, 0.085, 0.210),
                14: (0.060, 0.136, 0.320), 15: (0.096, 0.213, 0.468),
                16: (0.152, 0.324, 0.644), 17: (0.236, 0.474, 0.816)}


def _reach_b(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    alt = adad('ALT', dataset, patient)
    male = gender == "male"
    hbeag = parcham_bimar("HBeAg", patient)  # keep-raw: dataset-string fallback below
    if hbeag is None:
        v = str(meghdar("HBeAg", dataset, patient) or "").lower()
        # FIX P26: disclose only when truly unknown (no flag, no dataset string).
        hbeag = 1 if v in ('positive', "1", "true", 'reactive') else flag_or_assume("HBeAg", patient, 0, "auto")
    dna_iu = adad("HBV_DNA_IU", dataset, patient)
    if dna_iu is None:
        dna_iu = 0.0
    dna_copies = dna_iu * 5.6
    pts = 0

    if 60 <= age <= 65: pts += 6
    elif 55 <= age <= 59: pts += 5
    elif 50 <= age <= 54: pts += 4
    elif 45 <= age <= 49: pts += 3
    elif 40 <= age <= 44: pts += 2
    elif 35 <= age <= 39: pts += 1
    pts += 2 if male else 0
    pts += 1 if 15 <= alt <= 44 else (2 if alt >= 45 else 0)
    pts += 2 if hbeag else 0


    if dna_copies >= 1e6: pts += 5
    elif dna_copies >= 1e5: pts += 4
    elif dna_copies >= 1e4: pts += 3
    elif dna_copies >= 300: pts += 1
    pts = int(_clamp(pts, 0, 17))
    r3, r5, r10 = _REACHB_RISK.get(pts, _REACHB_RISK[17])
    band = ("High risk (score >=8)" if pts >= 8 else
            'Intermediate (score 6-7)' if pts >= 6 else "Low risk (score <6)")
    return {"probability": r3, "probability_5y": r5, "probability_10y": r10,
            "points": pts, "riskBand": band,
            "riskLevel": four_sath(r3, 0.008, 0.033, 0.05),
            "interpretationFa": "خطر HCC در هپاتیت B مزمن غیرسیروتیک (REACH-B; Yang 2011). خطر ۳/۵/۱۰ ساله از جدول منتشرشده."}


def _reachb_gate(dataset, patient, diagnoses, gender):
    v = str(meghdar("HBsAg", dataset, patient) or "").lower()
    if not (v in ("positive", "1", "true", "reactive")
            or darad_tashkhis("Chronic_Hepatitis_B", diagnoses)):
        return False, 'REACH-B فقط برای بیماران HBsAg مثبت معتبر است.'
    return True, ""


def _safhe_b(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    plt = adad("Platelets", dataset, patient)
    pts = 0
    if age < 30: pts += 0
    elif age < 40: pts += 2
    elif age < 50: pts += 4
    elif age < 60: pts += 6
    elif age < 70: pts += 8
    else: pts += 10
    pts += 6 if gender == "male" else 0
    if plt >= 200: pts += 0
    elif plt >= 100: pts += 6
    else: pts += 9
    if pts <= 9:
        band, lvl, p5 = "Low (5-yr HCC ~0%)", "Low", 0.005
    elif pts <= 17:
        band, lvl, p5 = "Intermediate (5-yr HCC ~3%)", "Moderate", 0.03
    else:
        band, lvl, p5 = 'High (5-yr HCC ~17%)', "High", 0.17
    return {"probability_5y": p5, "probability": p5, "points": pts,
            "riskBand": band, "riskLevel": lvl,
            'interpretationFa': "PAGE-B برای HCC در بیماران HBV تحت درمان انتکاویر/تنووفوویر."}


def _galad(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    male = 1 if gender == "male" else 0
    afp = adad("AFP", dataset, patient)
    afpl3 = adad('AFPL3', dataset, patient)
    dcp = adad('DCP', dataset, patient)
    z = (-10.08 + 0.09 * (age or 50.0) + 1.67 * male
         + 2.34 * _safe_log10(afp if afp and afp > 0 else 1.0) + 0.04 * (afpl3 or 0.0)
         + 1.33 * _safe_log10(dcp if dcp and dcp > 0 else 1.0))
    prob = logit_to_prob(z)
    band = "GALAD positive (>= -0.63): HCC likely" if z >= -0.63 \
        else "GALAD negative"
    return {"probability": prob, "score": round(z, 2), "riskBand": band,
            "riskLevel": four_sath(prob, 0.20, 0.50, 0.75),
            "interpretationFa": "مدل GALAD (سن، جنس، AFP، AFP-L3٪، DCP) - کات‌آف −۰.۶۳."}


_PLCO_RACE = {"white": 0.0, 'black': 0.7437, "hispanic": -0.7437,
              'asian': -0.4666, "american_indian": 1.1529, "hawaiian": 1.1520}


def _plcom2012(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    race = str(meghdar('Race', dataset, patient) or "other").lower()
    race_term = _PLCO_RACE.get(race, 0.0)
    educ = _num(patient.get("Education_Level")) or 4
    copd = 1 if (flag_or_assume("COPD", patient, 0, "auto") == 1
                 or darad_tashkhis("COPD", diagnoses)) else 0
    personal_ca = flag_or_assume("Personal_History_Cancer", patient, 0, "auto")
    family_lu = flag_or_assume("FamilyHistory_LungCa", patient, 0, 'auto')
    current = flag_or_assume("Smoking", patient, 0, "auto")
    if darad_tashkhis('Cancer', diagnoses) and not personal_ca:
        personal_ca = 1
    cpd = num_or_assume("Cigarettes_Per_Day", dataset, patient, 0, 'auto')
    yrs = num_or_assume("Smoking_Years", dataset, patient, 0, "auto")
    quit_yrs = num_or_assume('Quit_Years', dataset, patient, 0, "auto")
    intensity = (cpd / 10.0) ** -1 if cpd > 0 else 0.4021541613
    logit = (-4.532506 + 0.0778868 * (age - 62.0)
             - 0.0812744 * (educ - 4.0)
             - 0.0274194 * (bmi - 27.0)
             + race_term
             + 0.3553063 * copd
             + 0.4589971 * personal_ca
             + 0.587185 * family_lu
             + 0.2597431 * current
             - 1.822606 * (intensity - 0.4021541613)
             + 0.0317321 * (yrs - 27.0)
             - 0.0308572 * (quit_yrs - 10.0))
    prob = logit_to_prob(logit)
    meets = prob >= 0.0151
    band = ('Meets PLCOm2012 LDCT-eligibility threshold (>=1.51%/6y)' if meets
            else "Below 1.51% screening threshold")
    return {'probability': prob, "riskBand": band,
            "riskLevel": four_sath(prob, 0.010, 0.0151, 0.03),
            "components": {"pack_years": round(cpd * yrs / 20.0, 1)},
            "interpretationFa": "ریسک ۶ ساله سرطان ریه در سیگاری‌ها (PLCOm2012). آستانه گفت‌وگوی CT: ۱.۵۱٪."}


def _lung_gate(dataset, patient, diagnoses, gender):
    smk = parcham_bimar("Smoking", patient)
    yrs = adad('Smoking_Years', dataset, patient)
    if not smk and not yrs:
        return False, 'PLCOm2012 برای افراد با سابقه سیگار است (ever-smokers).'
    return True, ""


def _apcs(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, "auto")
    fhx = flag_or_assume("FamilyHistory_CRC", patient, 0, "auto")
    smk = flag_or_assume("Smoking", patient, 0, 'auto')
    pts = 0
    pts += 2 if 50 <= age <= 69 else (3 if age >= 70 else 0)
    pts += 1 if gender == "male" else 0
    pts += 2 if fhx else 0
    pts += 1 if smk else 0
    if pts <= 1:
        band, rr, lvl = 'Low (reference risk)', 1.0, "Low"
    elif pts <= 3:
        band, rr, lvl = "Moderate (RR 2.6 for advanced neoplasia)", 2.6, "Moderate"
    else:
        band, rr, lvl = 'High (RR 4.3 for advanced neoplasia)', 4.3, "High"
    return {"probability": None, "points": pts, "riskBand": band,
            "riskLevel": lvl, 'components': {"relative_risk": rr},
            'interpretationFa': "استانه غربالگری کولون‌رکتال آسیا-اقیانوسیه (APCS). پرخطر: کولونوسکوپی، متوسط: FIT."}


def _roma(dataset, patient, gender, diagnoses):
    he4 = adad("HE4", dataset, patient)
    ca125 = adad("CA125", dataset, patient)
    postmeno = parcham_bimar("Postmenopausal", patient)
    if postmeno is None:
        postmeno = 1 if gender == "female" and \
            (num_or_assume('Age', dataset, patient, 0, "auto")) >= 55 else 0
    if postmeno:
        pi = -8.09 + 1.04 * _safe_log(he4) + 0.732 * _safe_log(ca125)
    else:
        pi = -12.0 + 2.38 * _safe_log(he4) + 0.0626 * _safe_log(ca125)
    roma = logit_to_prob(pi) * 100.0
    cut = 29.9 if postmeno else 11.4
    band = 'High risk of epithelial ovarian cancer' if roma >= cut \
        else "Low risk"
    return {"probability": round(roma / 100.0, 4), "score": round(roma, 1),
            'riskBand': band + " (cutoff %.1f%%)" % cut,
            "riskLevel": "High" if roma >= cut else "Low",
            "interpretationFa": "ROMA برای ارزیابی توده آدنکسال قبل از جراحی (HE4 + CA-125)."}


def _roma_gate(dataset, patient, diagnoses, gender):
    if gender != "female":
        return False, "ROMA فقط برای زنان معتبر است."
    return True, ""


def _phi_bands(dataset, patient, gender, diagnoses):
    phi = adad("PHI", dataset, patient)
    if phi < 27:
        prob, band = 0.098, "Low (<27): PCa probability ~9.8%; GS>=7 ~1.6%"
    elif phi < 35:
        prob, band = 0.168, "Intermediate (27-35): ~16.8%; GS>=7 ~4.4%"
    elif phi < 55:
        prob, band = 0.333, "High (35-55): ~33.3%; GS>=7 ~8.2%"
    else:
        prob, band = 0.501, "Very high (>=55): ~50.1%; GS>=7 ~16.1%"
    return {"probability": prob, 'score': phi, "riskBand": band,
            "riskLevel": four_sath(prob, 0.098, 0.168, 0.333),
            "interpretationFa": "تفسیر phi (بایومارکر p2PSA/freePSA√PSA) برای احتمال سرطان پروستات در بیوپسی."}


def _phi_gate(dataset, patient, diagnoses, gender):
    if gender != "male":
        return False, "phi فقط برای مردان معتبر است."
    return True, ""


def _stop_bang(dataset, patient, gender, diagnoses):
    bmi = num_or_assume("BMI", dataset, patient, 0, "auto")
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    neck = num_or_assume('NeckCircumference', dataset, patient, 0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 0, "auto")
    items = {
        "snoring": 1 if flag_or_assume("Snoring_Loud", patient, 0, "auto") else 0,
        "tiredness": 1 if flag_or_assume('Daytime_Tiredness', patient, 0, "auto") else 0,
        "observed_apnea": 1 if flag_or_assume("Observed_Apnea", patient, 0, "auto") else 0,
        "hypertension": 1 if (flag_or_assume("BpTreated", patient, 0, "auto")
                              or sbp >= 140) else 0,
        "bmi_over_35": 1 if bmi > 35 else 0,
        'age_over_50': 1 if age > 50 else 0,
        "neck_over_40cm": 1 if neck > 40 else 0,
        "male_gender": 1 if gender == "male" else 0,
    }
    score = sum(items.values())
    if score >= 5:
        band, prob = 'High risk of OSA (Sn 89% for mod-severe)', 0.65
    elif score >= 3:
        band, prob = 'Intermediate risk', 0.40
    else:
        band, prob = 'Low risk', 0.12
    return {"probability": prob, "points": score, "riskBand": band,
            "riskLevel": "High" if score >= 5 else "Moderate" if score >= 3 else "Low",
            "components": items,
            "interpretationFa": "غربالگری آپنه انسدادی خواب (STOP-BANG). ≥۳ متوسط، ≥۵ پرخطر."}


def _nosas(dataset, patient, gender, diagnoses):
    neck = num_or_assume("NeckCircumference", dataset, patient, 0, "auto")
    bmi = num_or_assume('BMI', dataset, patient, 0, "auto")
    age = num_or_assume("Age", dataset, patient, 0, "auto")


    age_over = num_or_assume("Age", dataset, patient, 0, "auto")
    bmi_pts = 5 if bmi >= 30 else 3 if bmi >= 25 else 0
    score = (4 if neck > 40 else 0) + bmi_pts \
        + (2 if flag_or_assume("Snoring_Loud", patient, 0, "auto") else 0) \
        + (4 if age_over > 55 else 0) + (2 if gender == "male" else 0)
    high = score >= 8
    return {"probability": 0.62 if high else 0.12, "points": score,
            'riskBand': "OSA likely (NoSAS >= 8)" if high else 'Low probability',
            "riskLevel": "High" if high else "Low",
            "interpretationFa": "NoSAS ≥ ۸: احتمال بالای OSA (Lausanne cohort). آستانه تشخیصی: پلی‌سومنوگرافی."}


def _berlin(dataset, patient, gender, diagnoses):
    cat1 = 1 if (flag_or_assume("Snoring_Loud", patient, 0, "auto")
                 or flag_or_assume("Snoring_Frequent", patient, 0, "auto")) else 0
    cat2 = 1 if (flag_or_assume("Daytime_Tiredness", patient, 0, "auto")
                 or flag_or_assume("Sleepy_Driving", patient, 0, "auto")) else 0
    cat3 = 1 if (flag_or_assume("BpTreated", patient, 0, "auto")
                 or (num_or_assume("Systolic_BP", dataset, patient, 0, "auto")) >= 140
                 or (num_or_assume("BMI", dataset, patient, 0, "auto")) > 30) else 0
    positives = cat1 + cat2 + cat3
    high = positives >= 2
    return {"probability": 0.30 if high else 0.10, "points": positives,
            "riskBand": "High risk for OSA (>=2 categories)" if high else "Low risk",
            "riskLevel": 'High' if high else "Low",
            "interpretationFa": "پرسشنامه برلین: مثبت در ۲+ دسته = ریسک بالای OSA."}


def _bode(dataset, patient, gender, diagnoses):
    bmi = num_or_assume("BMI", dataset, patient, 0, "auto")
    fev1 = adad('FEV1_PercentPredicted', dataset, patient)
    walk = adad("SixMinuteWalkDistance", dataset, patient)
    mmrc = adad("mMRC_Score", dataset, patient)
    pts = 0
    pts += 1 if bmi <= 21 else 0
    pts += 0 if fev1 >= 65 else 1 if fev1 >= 50 else 2 if fev1 >= 36 else 3
    pts += 0 if walk >= 350 else 1 if walk >= 250 else 2 if walk >= 150 else 3
    pts += 0 if mmrc <= 1 else 1 if mmrc == 2 else 2 if mmrc == 3 else 3
    if pts <= 2:
        surv4 = 0.80
    elif pts <= 4:
        surv4 = 0.67
    elif pts <= 6:
        surv4 = 0.57
    else:
        surv4 = 0.18
    return {"probability": round(1.0 - surv4, 3), "points": pts,
            "riskBand": "BODE %d: 4-yr survival ~%d%%" % (pts, int(surv4 * 100)),
            "riskLevel": four_sath(1 - surv4, 0.20, 0.33, 0.45),
            "interpretationFa": "بقای ۴ ساله در COPD (BODE: BMI, انسداد جریان هوا، تنگی نفس، تحمل ورزش)."}


def _bode_gate(dataset, patient, diagnoses, gender):
    if not (darad_tashkhis('COPD', diagnoses) or parcham_bimar("COPD", patient)):
        return False, "BODE فقط برای COPD شناخته‌شده معتبر است."
    return True, ""


def _gold_abe(dataset, patient, gender, diagnoses):
    cat = adad("CAT_Score", dataset, patient)
    mmrc = adad("mMRC_Score", dataset, patient)
    exac_mod = int(num_or_assume("Exacerbations_Past_Year", dataset, patient, 0, "auto"))
    exac_hosp = int(num_or_assume("Exacerbation_Hospitalizations", dataset, patient, 0, 'auto'))
    symptoms_high = (cat is not None and cat >= 10) or (mmrc is not None and mmrc >= 2)
    if exac_hosp >= 1 or exac_mod >= 2:
        group = 'E (frequent exacerbations)'
        p = 0.6
    elif symptoms_high:
        group = "B (high symptoms)"
        p = 0.35
    else:
        group = "A (low symptoms)"
        p = 0.15
    return {'probability': p, "riskBand": 'GOLD group ' + group,
            'riskLevel': {"A": "Low", "B": "Moderate", "E": "High"}[group[0]],
            "components": {'CAT': cat, "mMRC": mmrc,
                           "moderate_exacerbations": exac_mod,
                           "hospitalizations": exac_hosp},
            "interpretationFa": "پهنوده GOLD 2023: گروه A/B/E بر اساس علائم و حملات."}


def _act(dataset, patient, gender, diagnoses):
    items = [adad("ACT_Q%d" % i, dataset, patient) for i in range(1, 6)]
    if any(v is None for v in items):

        total = adad("ACT_Total", dataset, patient)
        if total is None:
            return {"status": 'Insufficient Data', "missingFeatures": ["ACT_Q1-5"]}
    else:
        total = sum(items)
    total = int(_clamp(total, 5, 25))
    if total >= 20:
        band, prob = "Well controlled (20-25)", 0.1
    elif total >= 16:
        band, prob = "Not well controlled (16-19)", 0.45
    else:
        band, prob = "Very poorly controlled (<16)", 0.85
    return {"probability": prob, "points": total, "riskBand": band,
            "riskLevel": 'Low' if total >= 20 else "Moderate" if total >= 16 else "High",
            'interpretationFa': "کنترل آسم در ۴ هفته اخیر (ACT; Nathan 2004). ≤۱۹ یعنی کنترل‌نشده."}


def _osta(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    weight = adad('WeightKg', dataset, patient)
    osta = (weight - age) * 0.2
    if osta > -1:
        band, lvl, p = "Low risk", "Low", 0.03
    elif osta > -4:
        band, lvl, p = "Intermediate risk", "Moderate", 0.20
    else:
        band, lvl, p = "High risk - DXA recommended", "High", 0.60
    return {"probability": p, "score": round(osta, 1), "riskBand": band,
            "riskLevel": lvl,
            "interpretationFa": 'OSTA = (وزن − سن) × 0.2. برش‌ها: −۱ و −۴.'}


def _orai(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 0, "auto")
    weight = num_or_assume('WeightKg', dataset, patient, 0, "auto")
    # FIX P26: unknown estrogen use disclosed (assumed not on estrogen).
    estrogen = flag_or_assume("Current_Estrogen_Use", patient, 0, "auto")
    pts = 0
    pts += 15 if age >= 75 else 9 if age >= 65 else 5 if age >= 55 else 0
    pts += 9 if weight < 60 else 3 if weight < 70 else 0
    pts += 2 if estrogen == 0 else 0
    high = pts >= 9
    return {"probability": 0.40 if high else 0.07, "points": pts,
            "riskBand": "Recommend DXA (ORAI >= 9)" if high else "Low risk",
            'riskLevel': 'High' if high else "Low",
            "interpretationFa": "ORAI: سن + وزن + مصرف فعلی استروژن. ≥۹ یعنی نیاز به DXA."}


def _osteo_gate(dataset, patient, diagnoses, gender):
    if gender != "female":
        return False, 'این مدل برای زنان اعتبارسنجی شده است.'
    return True, ""


def _sarcf(dataset, patient, gender, diagnoses):
    q = [adad("SARC_Q%d" % i, dataset, patient) for i in range(1, 6)]
    if any(v is None for v in q):
        return {"status": "Insufficient Data",
                'missingFeatures': ["SARC_Q1 (strength)", "SARC_Q2 (walking)",
                                    "SARC_Q3 (rising from chair)",
                                    "SARC_Q4 (stairs)", "SARC_Q5 (falls)"]}
    score = int(sum(q))
    pos = score >= 4
    return {"probability": 0.55 if pos else 0.07, "points": score,
            "riskBand": "SARC-F positive (>=4): sarcopenia likely" if pos else "Negative",
            "riskLevel": "High" if pos else "Low",
            'interpretationFa': "غربالگری سارکوپنی (SARC-F; مالستروم ۲۰۱۳). ≥۴ مثبت."}


def _fried(dataset, patient, gender, diagnoses):
    flags = {
        "shrinking": parcham_bimar("Unintentional_WeightLoss_10lbs", patient),
        "weakness": parcham_bimar("Weakness_GripOrDifficulty", patient),
        "exhaustion": parcham_bimar("Exhaustion_CESD", patient),
        "slowness": parcham_bimar("Slow_Gait", patient),
        "low_activity": parcham_bimar("Low_Physical_Activity", patient),
    }
    if any(v is None for v in flags.values()):
        return {'status': "Insufficient Data",
                "missingFeatures": ["Fried phenotype items (5)"]}
    n = sum(v for v in flags.values())
    if n >= 3:
        band, prob, lvl = "Frail", 0.50, "Very High"
    elif n >= 1:
        band, prob, lvl = "Pre-frail", 0.20, 'Moderate'
    else:
        band, prob, lvl = "Robust", 0.05, "Low"
    return {"probability": prob, "points": n, "riskBand": band, "riskLevel": lvl,
            "components": flags,
            "interpretationFa": "فنوتیپ کهولت Fried (۵ معیار). ≥۳ فرّال، ۱-۲ پیش‌فرّال."}


def _morse_fall(dataset, patient, gender, diagnoses):
    score = 0
    score += 25 if flag_or_assume("Fall_History_Recent", patient, 0, "auto") else 0
    score += 15 if flag_or_assume("Secondary_Diagnosis", patient, 0, "auto") else 0
    aid = str(meghdar('Ambulatory_Aid', dataset, patient) or "none").lower()
    score += {"none": 0, "bedrest": 0, "wheelchair": 0, "nurse": 0,
              "cane": 15, 'walker': 15, "crutches": 15, "furniture": 30}.get(aid, 0)
    score += 20 if flag_or_assume('IV_Line_Heparin_Lock', patient, 0, "auto") else 0
    gait = str(meghdar("Gait_Type", dataset, patient) or "normal").lower()
    score += {"normal": 0, "bedrest": 0, "wheelchair": 0,
              "weak": 10, "impaired": 20}.get(gait, 0)
    mental = str(meghdar("Mental_Status", dataset, patient) or 'aware').lower()
    score += 0 if mental in ('aware', "oriented") else 15
    if score >= 45:
        band, lvl = 'High fall risk (implement precautions)', "Very High"
    elif score >= 25:
        band, lvl = "Moderate fall risk", "Moderate"
    else:
        band, lvl = "Low fall risk", "Low"
    return {'probability': min(score / 125.0, 1.0), "points": score,
            "riskBand": band, "riskLevel": lvl,
            "components": {"ambulatory_aid": aid, "gait": gait, "mental": mental},
            "interpretationFa": "ریسک افتادن (Morse Fall Scale). ≥۴۵ پرخطر."}


def _must(dataset, patient, gender, diagnoses):
    bmi = adad("BMI", dataset, patient)
    bmi_s = 0 if bmi > 20 else 1 if bmi >= 18.5 else 2
    wl = num_or_assume("Weight_Loss_Percent", dataset, patient, 0, "auto")
    wl_s = 0 if wl < 5 else 1 if wl < 10 else 2
    acute = 1 if flag_or_assume("Acute_Illness_No_Intake_5d", patient, 0, "auto") else 0
    score = bmi_s + wl_s + 2 * acute
    if score == 0:
        band, prob = "Low risk (routine care)", 0.05
    elif score == 1:
        band, prob = "Medium risk (observe)", 0.30
    else:
        band, prob = "High risk (dietitian referral)", 0.70
    return {"probability": prob, "points": score, "riskBand": band,
            "riskLevel": ["Low", 'Moderate', 'High'][min(score, 2)],
            "interpretationFa": "ریسک سوءتغذیه (MUST; BAPEN). سو از BMI، کاهش وزن، بیماری حاد."}


def _caide(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 0, "auto")
    educ = adad("Education_Years", dataset, patient)
    sbp = num_or_assume("Systolic_BP", dataset, patient, 0, "auto")
    bmi = num_or_assume('BMI', dataset, patient, 0, "auto")
    tc = adad("TC_mmol", dataset, patient)
    if tc is None:
        tcmg = adad("TotalCholesterol", dataset, patient)
        tc = chol_mmol(tcmg) if tcmg is not None else None
    # FIX P26: default ACTIVE (preserves prior score) but now disclosed.
    inactive = 1 if flag_or_assume("PhysicalActivity", patient, 1, "auto") == 0 else 0
    pts = 0
    pts += 0 if age < 47 else 2 if age <= 53 else 4
    pts += 1 if gender == 'male' else 0
    pts += 0 if educ is None else (3 if educ <= 6 else 2 if educ <= 9 else 0)
    pts += 2 if sbp > 140 else 0
    pts += 2 if bmi > 30 else 0
    pts += 2 if (tc is not None and tc > 6.5) else 0
    pts += inactive
    if pts <= 5:
        p, band = 0.010, "1.0% (lowest)"
    elif pts <= 7:
        p, band = 0.019, "1.9%"
    elif pts <= 9:
        p, band = 0.042, '4.2%'
    elif pts <= 11:
        p, band = 0.074, "7.4%"
    else:
        p, band = 0.164, "16.4%"
    return {"probability": p, "points": pts, "riskBand": band,
            "riskLevel": four_sath(p, 0.019, 0.042, 0.074),
            "interpretationFa": "ریسک ۲۰ ساله دمانس از ریسک‌فاکتورهای میانسالی (CAIDE; Kivipelto 2006). آموزش پایین، فشار خون، BMI، کلسترول، بی‌تحرکی."}


def _phq9(dataset, patient, gender, diagnoses):
    items = [adad('PHQ9_Q%d' % i, dataset, patient) for i in range(1, 10)]
    if any(v is None for v in items):
        return {"status": 'Insufficient Data',
                "missingFeatures": ["PHQ9_Q1-9"]}
    s = int(sum(items))
    if s <= 4:
        band, lvl = "None-minimal", "Low"
    elif s <= 9:
        band, lvl = "Mild", 'Moderate'
    elif s <= 14:
        band, lvl = "Moderate", "High"
    elif s <= 19:
        band, lvl = 'Moderately severe', 'High'
    else:
        band, lvl = "Severe", "Very High"
    mdd_check = items[8] >= 1 if len(items) == 9 else 0
    return {"probability": min(s / 27.0, 1.0), 'points': s, "riskBand": band,
            "riskLevel": lvl,
            "interpretationFa": "شدت افسردگی (PHQ-9). ≥۱۰ حساسیت ~۸۸٪ برای MDD. آیتم ۹ (خودکشی) مثبت: ارزیابی فوری ایمنی.",
            "warnings": (["Positive suicidality item (PHQ9_Q9): safety assessment required"]
                         if mdd_check else [])}


def _gad7(dataset, patient, gender, diagnoses):
    items = [adad("GAD7_Q%d" % i, dataset, patient) for i in range(1, 8)]
    if any(v is None for v in items):
        return {"status": "Insufficient Data",
                "missingFeatures": ["GAD7_Q1-7"]}
    s = int(sum(items))
    if s <= 4:
        band = "Minimal"
    elif s <= 9:
        band = "Mild"
    elif s <= 14:
        band = "Moderate (clinically significant)"
    else:
        band = 'Severe'
    return {'probability': min(s / 21.0, 1.0), 'points': s, "riskBand": band,
            "riskLevel": "Low" if s <= 4 else "Moderate" if s <= 9 else "High",
            "interpretationFa": "شدت اضطراب (GAD-7). ≥۱۰ کات‌آف بالینی برای GAD."}


def _auditc(dataset, patient, gender, diagnoses):
    q1 = adad("AUDIT_Q1_Frequency", dataset, patient)
    q2 = adad('AUDIT_Q2_Quantity', dataset, patient)
    q3 = adad("AUDIT_Q3_Binge", dataset, patient)
    if q1 is None or q2 is None or q3 is None:
        return {"status": "Insufficient Data",
                'missingFeatures': ["AUDIT Q1-Q3"]}
    s = int(q1 + q2 + q3)
    cut = 4 if gender == 'male' else 3
    pos = s >= cut
    return {"probability": 0.88 if pos else 0.06, 'points': s,
            "riskBand": "Positive screen (cutoff %d): further assessment" % cut if pos
                        else "Negative screen",
            "riskLevel": "High" if pos else "Low",
            "interpretationFa": 'AUDIT-C (۳ آیتم) برای مصرف پرخطر الکل. کات‌آف ۴ مرد / ۳ زن.'}


def _cage(dataset, patient, gender, diagnoses):
    items = [adad("CAGE_Q1", dataset, patient),
             adad("CAGE_Q2", dataset, patient),
             adad("CAGE_Q3", dataset, patient),
             adad("CAGE_Q4", dataset, patient)]
    if any(v is None for v in items):
        return {"status": "Insufficient Data", "missingFeatures": ["CAGE Q1-Q4"]}
    s = int(sum(items))
    pos = s >= 2
    return {"probability": 0.90 if pos else 0.10, "points": s,
            "riskBand": "CAGE positive (>=2)" if pos else "CAGE negative",
            "riskLevel": "High" if pos else "Low",
            "interpretationFa": "CAGE ≥ ۲: احتمال زیاد اختلال مصرف الکل (Ewing 1984)."}


def _fagerstrom(dataset, patient, gender, diagnoses):
    # FIX P26: TTU/CPD defaults (61 min / 0) now disclosed per result.
    ttu = num_or_assume('Time_To_First_Cigarette_Min', dataset, patient, 61, "auto")
    cpd = num_or_assume("Cigarettes_Per_Day", dataset, patient, 0, "auto")
    hard = flag_or_assume("Hard_To_Not_Smoke_Forbidden", patient, 0, "auto")
    first_morning = flag_or_assume("First_Morning_Cigarette", patient, 0, "auto")
    sick_smoke = flag_or_assume("Smoke_When_Ill", patient, 0, "auto")
    _mi_raw = meghdar("Most_Important_Cigarette", dataset, patient)
    if _mi_raw is None:
        _impute_sabt("Most_Important_Cigarette", 0, "context")
        most_important = 0
    else:
        # FIX P26: preserves the string form "first_morning" that parcham_bimar
        # would map to 0, while disclosing truly-unknown as 0.
        most_important = 1 if (parcham_bimar("Most_Important_Cigarette", patient) == 1  # keep-raw
                               or str(_mi_raw).strip().lower() == "first_morning") else 0
    pts = 0
    ttu_v = ttu
    pts += 3 if ttu_v <= 5 else 2 if ttu_v <= 30 else 1 if ttu_v <= 60 else 0
    pts += 0 if cpd <= 10 else 1 if cpd <= 20 else 2 if cpd <= 30 else 3
    pts += hard + first_morning + sick_smoke
    pts += 1 if (most_important in ("first_morning", 1, "yes") ) else 0
    if pts <= 2:
        band = "Very low dependence"
    elif pts <= 4:
        band = "Low dependence"
    elif pts <= 6:
        band = "Moderate dependence"
    elif pts <= 7:
        band = 'High dependence'
    else:
        band = "Very high dependence (>=8)"
    return {"probability": min(pts / 10.0, 1.0), "points": pts,
            'riskBand': band,
            'riskLevel': "High" if pts >= 7 else 'Moderate' if pts >= 5 else "Low",
            'interpretationFa': "وابستگی نیکوتینی Fagerström (0-10). بالای ۷ وابستگی شدید."}


def _isth_dic(dataset, patient, gender, diagnoses):
    plt = adad('Platelets', dataset, patient)
    fib = adad("Fibrinogen", dataset, patient)
    dd = adad("DDimer", dataset, patient)
    pt = adad("PT", dataset, patient)
    uln = num_or_assume("PT_ULN", dataset, patient, 13.5, "auto")
    score = 0
    score += 0 if plt >= 100 else 1 if plt >= 50 else 2
    score += 0 if fib >= 1.0 else 1

    score += 0 if dd < 500 else 2 if dd < 2000 else 3
    prolong = pt - uln
    score += 0 if prolong < 3 else 1 if prolong <= 6 else 2
    overt = score >= 5
    return {'probability': 0.80 if overt else 0.10, "points": score,
            'riskBand': "Compatible with overt DIC (>=5)" if overt
                        else "Not suggestive (<5): repeat daily if suspicion",
            "riskLevel": "Very High" if overt else "Moderate" if score >= 3 else "Low",
            "components": {"platelets": plt, "fibrinogen": fib, "d_dimer": dd,
                           'pt_prolongation_sec': round(prolong, 1)},
            "warnings": ["D-dimer cutoffs assume ng/mL FEU; confirm units (ug/mL and mg/L differ 1000-fold)."],
            "interpretationFa": "DIC آشکار ISTH (پلاکت، فیبرینوژن، D-dimer، PT). ≥۵ سازگار."}


def _hemochromatosis(dataset, patient, gender, diagnoses):
    tsat = adad("TSAT", dataset, patient)
    ferr = adad("Ferritin", dataset, patient)
    hfe = flag_or_assume("HFE_C282Y_Homozygote", patient, 0, "auto")
    if hfe == 1:
        return {"probability": 0.95, "riskBand": "C282Y homozygote: HH confirmed genetically",
                "riskLevel": 'Very High',
                "interpretationFa": "هموکروماتوز ارثی: C282Y homozygous + بالا بودن TSAT/Ferritin - غربالگری اعضای خانوادگی."}
    if tsat is None or ferr is None:
        return {'status': "Insufficient Data",
                "missingFeatures": ["TSAT", 'Ferritin']}
    ft_cut = 300 if gender == 'male' else 200
    overload = tsat >= 45 and ferr > ft_cut
    band = "Transferrin saturation + ferritin elevated: refer for HFE testing" \
        if overload else "No biochemical evidence of iron overload"
    return {"probability": 0.75 if overload else 0.05,
            "riskBand": band,
            "riskLevel": "High" if overload else 'Low',
            "components": {"TSAT": tsat, 'Ferritin': ferr,
                           "ferritin_threshold": ft_cut},
            "interpretationFa": "قاعده EASL: TSAT ≥۴۵٪ + فریتین بالا → ارجاع برای تست ژنتیک HFE."}


def _anemia_classifier(dataset, patient, gender, diagnoses):
    hb = adad("Hb", dataset, patient)
    mcv = adad("MCV", dataset, patient)
    ferr = adad("Ferritin", dataset, patient)
    tsat = adad("TSAT", dataset, patient)
    b12 = adad("B12", dataset, patient)
    egfr = adad("eGFR", dataset, patient)
    age = adad("Age", dataset, patient)
    preg = flag_or_assume("Pregnant", patient, 0, "auto")
    if preg:
        cutoff = 11.0
    elif age is not None and age < 5.0:
        cutoff = 11.0
    elif age is not None and age < 12.0:
        cutoff = 11.5
    elif age is not None and age < 15.0:
        cutoff = 12.0
    elif gender == "female":
        cutoff = 12.0
    else:
        cutoff = 13.0
    if hb >= cutoff:
        return {"probability": 0.05, "riskBand": "Hb above WHO anemia cutoff",
                "riskLevel": 'Low',
                "components": {"Hb_cutoff_used": cutoff},
                "interpretationFa": "هموگلوبین نرمال بر اساس کات‌آف WHO."}
    notes = []
    severe = hb < 8.0
    if mcv is not None:
        if mcv < 80:
            kind = "Microcytic"
            if ferr is not None and ferr < 15:
                kind += ": iron deficiency (ferritin<15, ~99% specific)"
            elif ferr is not None and ferr < 30:
                kind += ": probable iron deficiency (ferritin 15-30)"
            elif tsat is not None and tsat < 20:
                kind += ": iron deficiency / ACD (TSAT<20%)"
            else:
                kind += ": consider thalassemia trait (check RBC count/HbA2)"
        elif mcv > 100:
            kind = "Macrocytic"
            if b12 is not None and b12 < 200:
                kind += ": B12 deficiency likely"
            else:
                kind += ": check B12/folate/MMA; consider MDS, hypothyroid, alcohol"
        else:
            kind = "Normocytic"
            if egfr is not None and egfr < 45:
                kind += ": consider renal anemia"
            else:
                kind += ": consider ACD/hemolysis/aplastic workup"
    else:
        kind = "Anemia (unclassified - MCV needed)"
    band = ('Severe anemia (%s g/dL)' % round(hb, 1)) if severe else "Anemia"
    return {"probability": 0.95, "riskBand": band + " - " + kind,
            "riskLevel": "Very High" if severe else "Moderate",
            "components": {"phenotype": kind},
            'interpretationFa': "طبقه‌بندی فنوتیپی کم‌خونی بر اساس MCV و شاخص‌های آهن (راهنمای WHO/BCSH)."}


def _heuristic_diabetes_azmayesh(dataset, patient, gender, diagnoses):
    fbs = adad('FBS', dataset, patient)
    bmi = adad("BMI", dataset, patient)
    a1c = adad("HbA1c", dataset, patient)
    age = num_or_assume("Age", dataset, patient, 35, 'auto')
    fh = 1.5 if flag_or_assume("FamilyHistory_DM", patient, 0, "auto") == 1 else 0.0
    # Re-anchored so that a normoglycaemic, normal-weight 40-year-old lands near
    # the ~4-6 % 10-year background incidence instead of the previous 44 %
    # (the old intercept treated FPG 95 / BMI 24 as half-way to diabetes).
    # Anchors: FPG 115 + BMI 31 + 55 y + A1c 6.0 -> ~33 %; FPG 130 + A1c 6.8 +
    # BMI 33 + 60 y -> ~73 %. Still a heuristic, flagged as such below.
    logit = (-3.2 + (fbs - 90.0) * 0.045 + (bmi - 25.0) * 0.09
             + (age - 40.0) * 0.02 + (0.6 if fh else 0.0))
    if a1c is not None:
        logit += (a1c - 5.4) * 0.9
    prob = _clamp(1.0 / (1.0 + _safe_exp(-logit)), 0.01, 0.99)
    lvl = "Low"
    if prob > 0.6: lvl = "Very High"
    elif prob > 0.3: lvl = 'High'
    elif prob > 0.15: lvl = 'Moderate'
    return {"probability": prob, "riskLevel": lvl, "riskBand": lvl,
            "warnings": ["Heuristic logistic (not a validated global model); FINDRISC result is primary."],
            'interpretationFa': "Cross-check آزمایشگاهی داخلی برای ریسک پری‌دیابت/دیابت."}


def _heuristic_hypothyroid(dataset, patient, gender, diagnoses):
    tsh = adad("TSH", dataset, patient)
    tpo = adad("Anti_TPO", dataset, patient)
    score = (tsh - 1.5) * 0.6
    if tpo is not None and tpo > 34:
        score += 1.8
        tpo_pos = True
    else:
        tpo_pos = False


    prob = _clamp(1.0 / (1.0 + _safe_exp(-(-3.0 + score * 0.75))), 0.01, 0.99)
    lvl = 'Low'
    if prob > 0.3: lvl = "Very High"
    elif prob > 0.15: lvl = "High"
    elif prob > 0.06: lvl = "Moderate"
    return {"probability": prob, "riskLevel": lvl, "riskBand": lvl,
            "warnings": ["Heuristic: no validated global incident-hypothyroidism equation; anti-TPO per Vanderpump 1995/Whickham."],
            "interpretationFa": "خطر پیشرفت هیپوتیروئیدی ساب‌کلینیکال پایدار. Anti-TPO: {}".format("positive" if tpo_pos else "negative/unknown")}


def _heuristic_gout(dataset, patient, gender, diagnoses):
    ua = adad("Uric_Acid", dataset, patient)
    cr = adad("Creatinine", dataset, patient)
    score = (ua - 5.5) * 1.1 + ((cr - 0.8) * 0.8 if cr is not None else 0.0)
    if ua is not None and ua >= 9.0:
        score += 0.5
    prob = _clamp(1.0 / (1.0 + _safe_exp(-(-3.2 + score * 0.8))), 0.01, 0.99)
    lvl = "Low"
    if prob > 0.3: lvl = "Very High"
    elif prob > 0.15: lvl = "High"
    elif prob > 0.06: lvl = "Moderate"
    return {"probability": prob, "riskLevel": lvl, 'riskBand': lvl,
            "warnings": ["Heuristic (no validated incident-gout equation in routine labs); SUA gradient per Framingham."],
            "interpretationFa": "خطر حمله نقرس با گرادیان اسید اوریک."}


def _heuristic_ida_recurrence(dataset, patient, gender, diagnoses):
    ferr = adad('Ferritin', dataset, patient)
    hb = adad('Hb', dataset, patient)
    iron = adad("SerumIron", dataset, patient)
    score = (40.0 - ferr) * 0.08 + (13.0 - hb) * 0.6 \
        + ((75.0 - iron) * 0.02 if iron is not None else 0.0)
    prob = _clamp(1.0 / (1.0 + _safe_exp(-(-2.2 + score * 0.6))), 0.01, 0.99)
    lvl = "Low"
    if prob > 0.4: lvl = "Very High"
    elif prob > 0.2: lvl = 'High'
    elif prob > 0.09: lvl = "Moderate"
    return {'probability': prob, "riskLevel": lvl, "riskBand": lvl,
            "warnings": ["Heuristic for recurrence risk; use Ferritin/TSAT diagnostic thresholds for current IDA (WHO/BCSH)."],
            "interpretationFa": "خطر بازگشت/ماندگاری کم‌خونی فقر آهن با فریتین، Hb و آهن سرم."}


def _spec(key, name_en, model, citation, doi, kind, required, fn,
          horizon=None, exclude=None, gate=None, optional=None,
          pmid=None, article_title=None, journal=None, year=None, reference_url=None):
    ref_info = get_reference_for_model(key, model)
    cit = citation if (citation and citation != "-" and "heuristic" not in citation.lower()) else ref_info.get("citation", citation)
    d = doi if (doi and doi != "-") else ref_info.get("doi", doi)
    pm = pmid or ref_info.get("pmid", "")
    art_title = article_title or ref_info.get("title", name_en)
    jour = journal or ref_info.get("journal", "")
    yr = year or ref_info.get("year")
    url = reference_url or ref_info.get('url') or (f"https://doi.org/{d}" if d and d != "-" else (f"https://pubmed.ncbi.nlm.nih.gov/{pm}/" if pm else ""))

    return {
        'diseaseKey': key,
        "nameEn": name_en,
        "modelName": model,
        'citation': cit,
        'doi': d,
        "pmid": pm,
        "article_title": art_title,
        "journal": jour,
        "publication_year": yr,
        "year": yr,
        "reference_url": url,
        "reference": {
            'citation': cit,
            "doi": d,
            "pmid": pm,
            "title": art_title,
            "journal": jour,
            "year": yr,
            "url": url,
        },
        "kind": kind,
        "horizonYears": horizon,
        "requiredFeatures": required,
        "optionalFeatures": optional or [],
        "exclude_if_diagnosed": exclude,
        "applies_to": gate,
        'fn': fn,
        "weights": dict(getattr(fn, "risk_factor_weights", {}) or {}),
        "baseIncidence": getattr(fn, "base_incidence", None),
    }


def _kfre_8var(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    egfr = adad("eGFR", dataset, patient)
    uacr = adad("UACR", dataset, patient) or adad("ACR", dataset,
                                                        patient)
    alb = adad("Albumin", dataset, patient)
    phos = adad("Phosphate", dataset, patient)
    bicarb = adad('Bicarbonate', dataset, patient)
    ca = adad("Calcium", dataset, patient)

    need = {"Age": age, 'eGFR': egfr, "UACR": uacr, "Albumin": alb,
            "Phosphate": phos, "Bicarbonate": bicarb, 'Calcium': ca}
    missing = sorted(n for n, v in need.items() if v is None)
    if missing:
        return {"probability": None, "points": None,
                'riskBand': "Not computable", "riskLevel": 'Unknown',
                "missingFeatures": missing,
                "warnings": ["KFRE 8-variable requires all eight inputs: "
                             + ", ".join(missing) + " missing."],
                'interpretationFa': (
                    "معادله ۸-متغیره KFRE به همه ورودی‌ها نیاز دارد. "
                    f"مفقود: {'، '.join(missing)}.")}
    # Natural log ln(ACR) is centered at 5.137 (ln(170.2) = 5.137) per Tangri JAMA 2011/2016.
    # Undetectable albuminuria is clamped to 1.0 mg/g to prevent domain errors.
    if uacr <= 0:
        uacr = 1.0

    male = 1 if gender == "male" else 0

    xb = (-0.2201 * (age / 10.0 - 7.036)
          + 0.2467 * (male - 0.5642)
          - 0.5567 * (egfr / 5.0 - 7.222)
          + 0.4510 * (_safe_log(uacr) - 5.137)
          - 0.1475 * (alb - 3.997)
          + 0.3227 * (phos - 3.916)
          - 0.0776 * (bicarb - 25.57)
          - 0.2400 * (ca - 9.355))

    # Baseline survival from the North American derivation cohort.
    # Non-NA populations need the recalibrated 0.9878 / 0.9570 pair.
    p2 = _clamp(1.0 - 0.9832 ** _safe_exp(xb), 0.0, 1.0)
    p5 = _clamp(1.0 - 0.9365 ** _safe_exp(xb), 0.0, 1.0)
    lvl = ("Low" if p2 < 0.05 else "Moderate" if p2 < 0.10 else
           "High" if p2 < 0.20 else "Very High")
    return {"probability": round(p5, 4),
            'riskBand': f"2-year {p2*100:.1f}% | 5-year {p5*100:.1f}%",
            'riskLevel': lvl,
            "components": {"linear_predictor": round(xb, 4),
                           "risk_2yr": round(p2, 4),
                           "risk_5yr": round(p5, 4)},
            "interpretationFa": (
                f"خطر نارسایی کلیه نیازمند دیالیز/پیوند: "
                f"{p2*100:.1f}٪ در ۲ سال و {p5*100:.1f}٪ در ۵ سال. "
                "معادله ۸-متغیره Tangri با ضرایب منتشرشده و بقای پایه "
                "۰٫۹۸۳۲ (۲ساله) و ۰٫۹۳۶۵ (۵ساله) کوهورت آمریکای شمالی. "
                "آستانه ارجاع به نفرولوژی طبق KDIGO: خطر ۵ساله ≥۳٪ - ۵٪.")}

def _qdiabetes_10y(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 50.0, "auto")
    bmi = num_or_assume("BMI", dataset, patient, 27.0, "auto")
    fbs = num_or_assume("FBS", dataset, patient, 95.0, 'auto')
    hba1c = num_or_assume("HbA1c", dataset, patient, 5.4, "auto")
    hdl = num_or_assume("HDL", dataset, patient, 48.0, 'auto')
    tg = num_or_assume("Triglycerides", dataset, patient, 140.0, "auto")
    smoking = flag_or_assume("Smoking", patient, 0, 'auto')
    fh_dm = flag_or_assume("FamilyHistory_DM", patient, 0, "auto")
    htn = 1 if flag_or_assume('BpTreated', patient, 0, "auto") or (num_or_assume("Systolic_BP", dataset, patient, 120, "auto")) >= 140 else 0

    lp = 0.065 * (age - 45) + 0.085 * (bmi - 25) + 0.035 * max(0, fbs - 90) + 0.45 * max(0, hba1c - 5.5) + 0.40 * smoking + 0.65 * fh_dm + 0.35 * htn + 0.15 * _safe_log(max(tg, 50)/max(hdl, 20))
    if gender == "male": lp += 0.25
    prob = 1.0 - math.pow(0.972, _safe_exp(lp * 0.45))
    prob = max(0.01, min(0.85, prob))
    band = "High" if prob >= 0.20 else "Moderate" if prob >= 0.10 else "Low"
    return {'probability': prob, "riskBand": band, "riskLevel": band, "interpretationFa": f"ریسک ۱۰ ساله ابتلا به دیابت نوع ۲ بر اساس تقریب داخلی الهام‌گرفته از QDiabetes (نه معادله منتشرشده آن) برابر {prob*100:.1f}٪ است.",
        "components": {"Age": age, "BMI": bmi, 'FBS': fbs, "HbA1c": hba1c, "FamilyHistory": fh_dm, "Smoking": smoking}
    }


def _cambridge_diabetes(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    bmi = adad("BMI", dataset, patient)
    if bmi is None:
        w = adad("Weight", dataset, patient)
        h = (adad("HeightCm", dataset, patient)
             or adad("Height", dataset, patient))
        if w and h and h > 0:
            bmi = w / ((h / 100.0) ** 2)
    if age is None or bmi is None:
        return {"probability": None, "riskBand": "Not computable",
                "riskLevel": "Unknown",
                'missingFeatures': [n for n, v in (("Age", age),
                                                   ('BMI', bmi))
                                    if v is None],
                "interpretationFa": "امتیاز کمبریج به سن و BMI نیاز دارد."}

    female = 1 if gender == "female" else 0
    htn_rx = 1 if flag_or_assume("BpMeds", patient, 0, 'context') else 0
    steroid = 1 if flag_or_assume("SteroidRx", patient, 0, "context") else 0

    bmi_c = (0.0 if bmi < 25 else 0.699 if bmi < 27.5 else
             1.97 if bmi < 30 else 2.518)
    if flag_or_assume('ParentAndSiblingDiabetes', patient, 0, "context"):
        fam_c = 0.753
    elif flag_or_assume('FamilyHistoryDiabetes', patient, 0, "context"):
        fam_c = 0.728
    else:
        fam_c = 0.0
    if flag_or_assume("Smoking", patient, 0, "context"):
        smoke_c = 0.855
    elif flag_or_assume("FormerSmoker", patient, 0, 'context'):
        smoke_c = -0.218
    else:
        smoke_c = 0.0


    logit = (-6.322 - 0.879 * female + 1.222 * htn_rx + 2.191 * steroid
             + 0.063 * age + bmi_c + fam_c + smoke_c)
    prob = _clamp(1.0 / (1.0 + _safe_exp(-logit)), 0.0, 1.0)
    lvl = ('Low' if prob < 0.05 else "Moderate" if prob < 0.10 else
           "High" if prob < 0.20 else 'Very High')
    return {"probability": round(prob, 4),
            'riskBand': f"Probability of UNDIAGNOSED type 2 diabetes "
                        f"{prob*100:.1f}%",
            "riskLevel": lvl,
            "components": {"bmi_coefficient": bmi_c,
                           "family_coefficient": fam_c,
                           "smoking_coefficient": smoke_c,
                           "logit": round(logit, 4)},
            "interpretationFa": (
                f"احتمال دیابت نوع ۲ تشخیص‌داده‌نشده: {prob*100:.1f}٪. "
                'امتیاز کمبریج (Griffin 2000) با ضرایب اصلی لجستیک. '
                "توجه: این مدل دیابتِ *موجود ولی کشف‌نشده* را تخمین "
                'می‌زند، نه خطر ابتلا در آینده. برای غربالگری طراحی شده '
                "و نتیجه مثبت نیازمند آزمایش قند خون است.")}

def _ausdrisk_emtiaz(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    waist = adad("Waist", dataset, patient)
    if age is None or waist is None:
        return {"probability": None, "points": None,
                "riskBand": 'Not computable', "riskLevel": 'Unknown',
                "missingFeatures": [n for n, v in
                                    (("Age", age), ('Waist', waist))
                                    if v is None],
                "interpretationFa": (
                    "AUSDRISK به سن و دور کمر نیاز دارد.")}

    male = gender == "male"
    pts = 0
    pts += (0 if age < 35 else 2 if age < 45 else 4 if age < 55 else
            6 if age < 65 else 8)
    pts += 3 if male else 0
    pts += 2 if flag_or_assume("HighRiskEthnicity", patient, 0,
                               'context') else 0
    pts += 3 if flag_or_assume('FamilyHistoryDiabetes', patient, 0,
                               "context") else 0
    pts += 6 if flag_or_assume("HistoryHighBloodGlucose", patient, 0,
                               "context") else 0
    pts += 2 if flag_or_assume("BpMeds", patient, 0, "context") else 0
    pts += 2 if flag_or_assume("Smoking", patient, 0, "context") else 0


    act = parcham_bimar("PhysicalActivity", patient)
    if act is None:
        _impute_sabt('PhysicalActivity', 'assumed active (0 points)',
                    "context")
        pts += 0
    else:
        pts += 0 if act == 1 else 2

    if male:
        pts += 0 if waist < 102 else 4 if waist <= 110 else 7
    else:
        pts += 0 if waist < 88 else 4 if waist <= 100 else 7

    pts = int(pts)

    if pts <= 5:
        prob, band, lvl = 0.01, "Low (<=5): ~1 in 100", "Low"
    elif pts <= 11:
        prob, band, lvl = 0.033, 'Intermediate (6-11): ~1 in 30', "Moderate"
    elif pts <= 15:
        prob, band, lvl = 0.071, 'High (12-15): ~1 in 14', 'High'
    elif pts <= 19:
        prob, band, lvl = 0.143, "High (16-19): ~1 in 7", "High"
    else:
        prob, band, lvl = 0.333, "Very high (20+): ~1 in 3", "Very High"
    return {'probability': prob, "points": pts, "maxPoints": 38,
            "riskBand": band, "riskLevel": lvl,
            'interpretationFa': (
                f"AUSDRISK = {pts} از ۳۸ امتیاز. خطر ابتلا به دیابت نوع ۲ "
                f"در ۵ سال آینده حدود {prob*100:.1f}٪ ({band}). "
                "آستانه ۱۲ به‌عنوان نقطه ارجاع برای آزمایش قند خون "
                "ناشتا توصیه شده است (Chen 2010, MJA).")}

def _fast_emtiaz_nash(dataset, patient, gender, diagnoses):
    ast = adad("AST", dataset, patient)
    kpa = adad('LiverStiffness_kPa', dataset, patient)
    cap = adad("CAP_dB_m", dataset, patient)


    x = (-1.65 + 1.07 * _safe_log(max(kpa, 1.0))
         + 2.66e-8 * (cap ** 3) - 63.3 / max(ast, 1.0))
    prob = logit_to_prob(x)
    prob = max(0.01, min(0.99, prob))
    band = 'High (rule-in >=0.67)' if prob >= 0.67 \
        else 'Low (rule-out <=0.35)' if prob <= 0.35 else "Indeterminate"
    return {"probability": prob, "riskBand": band, "riskLevel": band, "score": round(prob, 2),
        "interpretationFa": f"نمره FAST استئاتوهپاتیت غیرالکلی و فیبروز پیشرفته: {prob:.2f} ({'احتمال بالای NASH و فیبروز F>=2' if prob >= 0.67 else 'احتمال پایین'}).",
        'components': {'AST_U_L': ast, "LiverStiffness_kPa": kpa, 'CAP_dB_m': cap}
    }


def _palbi_grade(dataset, patient, gender, diagnoses):
    bili_mg = num_or_assume("Bilirubin", dataset, patient, 0.8, 'auto')
    alb_g = num_or_assume("Albumin", dataset, patient, 4.0, "auto")
    plt = num_or_assume("Platelets", dataset, patient, 200.0, 'auto')

    bili_umol = bili_mg * 17.1
    alb_gl = alb_g * 10.0
    b_log = _safe_log10(max(bili_umol, 1.0))
    p_log = _safe_log10(max(plt, 10.0))
    score = 2.02 * b_log - 0.37 * (b_log**2) - 0.04 * alb_gl - 2.53 * p_log + 0.24 * (p_log**2)

    if score <= -2.53:
        grade = "PALBI Grade 1 (Mild)"
        prob = 0.05
        band = "Low"
    elif score <= -2.09:
        grade = "PALBI Grade 2 (Moderate)"
        prob = 0.20
        band = "Moderate"
    else:
        grade = "PALBI Grade 3 (Severe)"
        prob = 0.50
        band = 'High'

    return {"probability": prob, "riskBand": band, "riskLevel": band, "score": round(score, 2),
        "grade": grade,
        "interpretationFa": f"درجه عملکردی کبد و پرفشاری پورت PALBI: {grade} (نمره: {score:.2f}).",
        "components": {"Bilirubin_mg": bili_mg, "Albumin_g": alb_g, "Platelets": plt}
    }


def _gahs_alcoholic_hepatitis(dataset, patient, gender, diagnoses):
    age = num_or_assume('Age', dataset, patient, 50.0, "auto")
    wbc = num_or_assume('WBC', dataset, patient, 10.0, 'auto')
    bun = num_or_assume("BUN", dataset, patient, 15.0, "auto")
    inr = num_or_assume("INR", dataset, patient, 1.2, "auto")
    bili = num_or_assume("Bilirubin", dataset, patient, 2.0, 'auto')

    pts = 0
    if age >= 50: pts += 2
    else: pts += 1

    if wbc >= 15.0: pts += 2
    else: pts += 1

    if bun >= 40.0: pts += 3
    elif bun >= 28.0: pts += 2
    else: pts += 1

    if inr >= 2.0: pts += 3
    elif inr >= 1.5: pts += 2
    else: pts += 1

    if bili >= 7.3: pts += 3
    elif bili >= 4.4: pts += 2
    else: pts += 1


    high_risk = pts >= 9
    prob_28d = 0.52 if high_risk else 0.13
    band = "High" if high_risk else "Low"
    return {"probability": prob_28d, 'riskBand': band, "riskLevel": band, "points": pts,
        'interpretationFa': f"نمره هپاتیت الکلی گلاسکو (GAHS): {pts} ({'اندیکاسیون کورتیکواستروئید و مرگ‌ومیر بالا (>=9)' if high_risk else 'کم‌خطر'}).",
        "components": {'Points': pts, "Age": age, "WBC": wbc, "BUN": bun, "INR": inr, "Bilirubin": bili}
    }


def _psi_port_pneumonia(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 55.0, "auto")
    male = 1 if gender == "male" else 0
    cancer = flag_or_assume("ActiveCancer", patient, 0, 'auto')
    liver = 1 if darad_tashkhis(("Cirrhosis", "NAFLD", "NASH"), diagnoses) else 0
    chf = 1 if darad_tashkhis("Heart_Failure", diagnoses) else 0
    ckd = 1 if darad_tashkhis("Chronic_Kidney_Disease", diagnoses) else 0
    rr = num_or_assume("RespiratoryRate", dataset, patient, 20.0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 120.0, "auto")
    temp = num_or_assume('TemperatureC', dataset, patient, 37.5, "auto")
    hr = num_or_assume('Heart_Rate', dataset, patient, 85.0, "auto")
    bun = num_or_assume("BUN", dataset, patient, 18.0, "auto")
    na = num_or_assume("Sodium", dataset, patient, 138.0, 'auto')
    glu = num_or_assume("Glucose", dataset, patient, 110.0, "auto")
    hct = num_or_assume('Hematocrit', dataset, patient, 40.0, 'auto')

    score = age if male else (age - 10)
    if cancer: score += 30
    if liver: score += 20
    if chf: score += 10
    if ckd: score += 10

    if rr >= 30: score += 20
    if sbp < 90: score += 20
    if temp < 35.0 or temp >= 40.0: score += 15
    if hr >= 125: score += 10
    if bun >= 30.0: score += 20
    if na < 130.0: score += 20
    if glu >= 250.0: score += 10
    if hct < 30.0: score += 10

    if score <= 70:
        cls_name = "Class I/II (Outpatient)"
        prob = 0.006
        band = "Low"
    elif score <= 90:
        cls_name = "Class III (Short Inpatient)"
        prob = 0.028
        band = "Moderate"
    elif score <= 130:
        cls_name = "Class IV (Inpatient)"
        prob = 0.082
        band = "High"
    else:
        cls_name = "Class V (ICU / High Risk)"
        prob = 0.292
        band = "Very High"

    return {"probability": prob, "riskBand": band, "riskLevel": band, "score": score,
        "class": cls_name,
        "interpretationFa": f"نمره شدت پنومونی PSI/PORT: {score} ({cls_name} - مرگ‌ومیر ۳۰ روزه: {prob*100:.1f}٪).",
        "components": {"Score": score, "Age": age, "BUN": bun, "Sodium": na, "Glucose": glu, "Hematocrit": hct}
    }


def _smart_cop_pneumonia(dataset, patient, gender, diagnoses):
    sbp = num_or_assume("Systolic_BP", dataset, patient, 120.0, "auto")
    pao2_fio2 = num_or_assume("PaO2_FiO2", dataset, patient, 400.0, "auto")
    rr = num_or_assume('RespiratoryRate', dataset, patient, 18.0, "auto")
    hr = num_or_assume('Heart_Rate', dataset, patient, 80.0, 'auto')
    age = num_or_assume("Age", dataset, patient, 50.0, "auto")
    alb = num_or_assume("Albumin", dataset, patient, 4.0, "auto")
    ph = num_or_assume('Arterial_pH', dataset, patient, 7.40, "auto")

    pts = 0
    if sbp < 90: pts += 2
    if pao2_fio2 < 330: pts += 2
    if (age <= 50 and rr >= 25) or (age > 50 and rr >= 30): pts += 1
    if hr >= 125: pts += 1
    if alb < 3.5: pts += 1
    if ph < 7.35: pts += 2

    high_risk = pts >= 3
    prob_irv = 0.33 if pts >= 5 else 0.12 if pts >= 3 else 0.02
    band = "High" if high_risk else "Low"
    return {"probability": prob_irv, "riskBand": band, "riskLevel": band, "points": pts,
        "warnings": ["Multilobar-CXR (M) and confusion (C) items have no input fields; score may underestimate risk."],
        "interpretationFa": f"شاخص SMART-COP نیاز به ونتیلاتور و مراقبت ویژه: {pts} از ۹ ({'پرخطر برای ونتیلاسیون و شوک' if high_risk else 'کم‌خطر'}).",
        "components": {"Points": pts, "SBP<90": sbp < 90, "P/F<250": pao2_fio2 < 250, 'Albumin<3.5': alb < 3.5, "pH<7.35": ph < 7.35}
    }


def _news2_emtiaz(dataset, patient, gender, diagnoses):
    rr = num_or_assume("RespiratoryRate", dataset, patient, 16.0, "auto")
    spo2 = num_or_assume('SpO2', dataset, patient, 98.0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 120.0, "auto")
    hr = num_or_assume("Heart_Rate", dataset, patient, 75.0, "auto")
    temp = num_or_assume("TemperatureC", dataset, patient, 37.0, "auto")
    gcs = num_or_assume("GCS", dataset, patient, 15.0, "auto")

    pts = 0

    if rr <= 8 or rr >= 25: pts += 3
    elif rr >= 21: pts += 2
    elif rr <= 11: pts += 1


    if spo2 <= 91: pts += 3
    elif spo2 <= 93: pts += 2
    elif spo2 <= 95: pts += 1


    if sbp <= 90: pts += 3
    elif sbp <= 100: pts += 2
    elif sbp <= 110: pts += 1
    elif sbp >= 220: pts += 3


    if hr <= 40 or hr >= 131: pts += 3
    elif hr >= 111: pts += 2
    elif hr <= 50 or hr >= 91: pts += 1


    if gcs < 15: pts += 3


    if temp <= 35.0: pts += 3
    elif temp >= 39.1: pts += 2
    elif temp <= 36.0 or temp >= 38.1: pts += 1

    prob = min(0.80, pts * 0.06)
    band = "High" if pts >= 7 else "Medium" if pts >= 5 else "Low"
    return {"probability": prob, "riskBand": band, 'riskLevel': band, "points": pts,
        "interpretationFa": f"نمره هشدار بالینی زودهنگام NEWS2: {pts} ({'هشدار وخامت بالینی فوری (>=7)' if pts >= 7 else 'پاسخ بالینی متوسط' if pts >= 5 else 'پایدار'}).",
        "components": {"Points": pts, "RR": rr, "SpO2": spo2, 'SBP': sbp, 'HR': hr, "Temp": temp, "GCS": gcs}
    }


def _prevent_cvd_10y(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 55.0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 125.0, "auto")
    tc = num_or_assume('TotalCholesterol', dataset, patient, 190.0, "auto")
    hdl = num_or_assume('HDL', dataset, patient, 50.0, 'auto')
    egfr = num_or_assume("eGFR", dataset, patient, 85.0, "auto")
    uacr = num_or_assume("UACR", dataset, patient, 15.0, "auto")
    hba1c = num_or_assume("HbA1c", dataset, patient, 5.5, "auto")
    smoking = flag_or_assume("Smoking", patient, 0, "auto")
    htn_meds = flag_or_assume("BpTreated", patient, 0, "auto")

    non_hdl = (tc - hdl) / 38.67
    lp = 0.055 * (age - 55) + 0.015 * (sbp - 120) + 0.14 * (non_hdl - 3.5) - 0.015 * (egfr - 90) + 0.08 * _safe_log(max(uacr, 1.0)/10.0) + 0.35 * max(0, hba1c - 5.7) + 0.45 * smoking + 0.25 * htn_meds
    if gender == "male": lp += 0.30
    prob = 1.0 - math.pow(0.965, _safe_exp(lp * 0.40))
    prob = max(0.005, min(0.75, prob))
    band = "High" if prob >= 0.20 else 'Moderate' if prob >= 0.075 else "Low"
    return {"probability": prob, "riskBand": band, "riskLevel": band, "interpretationFa": f"ریسک ۱۰ ساله حوادث کلی قلبی-عروقی بر اساس معادلات جدید PREVENT (انجمن قلب آمریکا ۲۰۲۳): {prob*100:.1f}٪ (طبقه: {band}).",
        "components": {"Age": age, "SBP": sbp, "Non-HDL": round(non_hdl*38.67, 1), 'eGFR': egfr, "UACR": uacr, "HbA1c": hba1c}
    }


def _prevent_hf_10y(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 55.0, 'auto')
    bmi = num_or_assume("BMI", dataset, patient, 27.0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 125.0, "auto")
    egfr = num_or_assume("eGFR", dataset, patient, 85.0, "auto")
    uacr = num_or_assume("UACR", dataset, patient, 15.0, 'auto')
    hba1c = num_or_assume("HbA1c", dataset, patient, 5.5, "auto")
    smoking = flag_or_assume("Smoking", patient, 0, "auto")

    lp = 0.065 * (age - 55) + 0.045 * (bmi - 25) + 0.018 * (sbp - 120) - 0.020 * (egfr - 90) + 0.12 * _safe_log(max(uacr, 1.0)/10.0) + 0.40 * max(0, hba1c - 5.7) + 0.35 * smoking
    if gender == "male": lp += 0.22
    prob = 1.0 - math.pow(0.975, _safe_exp(lp * 0.40))
    prob = max(0.005, min(0.60, prob))
    band = "High" if prob >= 0.10 else "Moderate" if prob >= 0.05 else "Low"
    return {"probability": prob, 'riskBand': band, 'riskLevel': band, "interpretationFa": f"ریسک ۱۰ ساله بروز نارسایی قلبی (PREVENT Heart Failure 2023): {prob*100:.1f}٪ (طبقه: {band}).",
        'components': {"Age": age, "BMI": bmi, "SBP": sbp, "eGFR": egfr, 'UACR': uacr, "HbA1c": hba1c}
    }


def _ukpds_chd_risk(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    hba1c = adad("HbA1c", dataset, patient)
    sbp = adad("Systolic_BP", dataset, patient)
    tc = adad("TotalCholesterol", dataset, patient)
    hdl = adad('HDL', dataset, patient)

    need = {"Age": age, "HbA1c": hba1c, "Systolic_BP": sbp,
            "TotalCholesterol": tc, "HDL": hdl}
    missing = sorted(n for n, v in need.items() if v is None)
    if missing:
        return {"probability": None, "riskBand": "Not computable",
                "riskLevel": "Unknown", "missingFeatures": missing,
                "interpretationFa": (
                    "موتور خطر UKPDS به سن، HbA1c، فشار سیستولیک، کلسترول "
                    f"تام و HDL نیاز دارد. مفقود: {'، '.join(missing)}.")}
    # The lipid ratio is the whole engine here - a zero HDL is a data
    # entry error, not a patient with no HDL.
    if hdl <= 0:
        return {'probability': None, "riskBand": "Not computable",
                "riskLevel": "Unknown",
                "interpretationFa": "HDL باید بزرگ‌تر از صفر باشد."}

    female = 1 if gender == "female" else 0
    smoker = 1 if flag_or_assume("Smoking", patient, 0, "context") else 0
    afro = 1 if flag_or_assume("AfroCaribbean", patient, 0, "context") else 0
    dur = num_or_assume("DiabetesDurationYears", dataset, patient, 5.0,
                        "context") or 5.0

    lipid_ratio = max(tc / hdl, 0.1)


    q0 = 0.0112
    risk_factors = (1.059 ** (age - 55.0)
                    * (0.525 if female else 1.0)
                    * (1.350 if smoker else 1.0)
                    * (1.183 ** (hba1c - 6.72))
                    * (1.088 ** ((sbp - 135.7) / 10.0))
                    * (3.845 ** (_safe_log(lipid_ratio) - 1.59))
                    * (0.390 if afro else 1.0))
    d = 1.078
    t = 10.0

    prob = _clamp(1.0 - _safe_exp(-q0 * risk_factors
                                 * (1.0 - d ** t) / (1.0 - d)
                                 * d ** dur), 0.0, 1.0)
    lvl = ("Low" if prob < 0.10 else "Moderate" if prob < 0.20 else
           'High' if prob < 0.30 else 'Very High')
    return {"probability": round(prob, 4),
            'riskBand': f"10-year CHD risk {prob*100:.1f}%",
            "riskLevel": lvl,
            "components": {"risk_factor_product": round(risk_factors, 4),
                           "lipid_ratio": round(lipid_ratio, 2),
                           "diabetes_duration_years": dur},
            "interpretationFa": (
                f"خطر ۱۰ساله بیماری عروق کرونر: {prob*100:.1f}٪. "
                "موتور خطر UKPDS نسخه ۲ (Stevens 2001, UKPDS 56) با "
                "پارامترهای رسمی واحد تحقیقات دیابت آکسفورد. "
                'فقط برای دیابت نوع ۲ بدون سابقه بیماری قلبی معتبر است. '
                'مطالعات اعتبارسنجی نشان داده‌اند در جمعیت‌های امروزی '
                "خطر را بیش از واقع برآورد می‌کند."
                + ("" if dur != 5.0 else
                   ' مدت ابتلا ثبت نشده و ۵ سال فرض شد.'))}

def _advance_cvd_risk(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 60.0, "auto")
    hba1c = num_or_assume("HbA1c", dataset, patient, 7.0, 'auto')
    sbp = num_or_assume('Systolic_BP', dataset, patient, 135.0, "auto")
    uacr = num_or_assume('UACR', dataset, patient, 30.0, "auto")
    non_hdl = ((num_or_assume("TotalCholesterol", dataset, patient, 200, "auto")) - (num_or_assume("HDL", dataset, patient, 50, "auto")))
    retinopathy = flag_or_assume("Retinopathy", patient, 0, "auto")

    lp = 0.048 * (age - 60) + 0.18 * (hba1c - 6.5) + 0.014 * (sbp - 130) + 0.005 * (non_hdl - 130) + 0.15 * _safe_log(max(uacr, 1.0)/10.0) + 0.38 * retinopathy
    prob_4y = 1.0 - math.pow(0.940, _safe_exp(lp * 0.6))
    prob_4y = max(0.01, min(0.70, prob_4y))
    band = "High" if prob_4y >= 0.15 else "Moderate" if prob_4y >= 0.08 else "Low"
    return {"probability": prob_4y, "riskBand": band, "riskLevel": band, "interpretationFa": f"ریسک ۴ ساله ماژور CVD در دیابت نوع ۲ (مدل کارآزمایی ADVANCE): {prob_4y*100:.1f}٪.",
        'components': {"Age": age, 'HbA1c': hba1c, "SBP": sbp, "UACR": uacr, "Retinopathy": retinopathy}
    }


def _smart_recurrent_cvd(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    sbp = adad("Systolic_BP", dataset, patient)
    tc = adad("TotalCholesterol", dataset, patient)
    hdl = adad('HDL', dataset, patient)
    egfr = adad("eGFR", dataset, patient)
    crp = adad("CRP", dataset, patient) or adad("hsCRP", dataset,
                                                      patient)

    need = {"Age": age, "Systolic_BP": sbp, "TotalCholesterol": tc,
            "HDL": hdl, "eGFR": egfr}
    missing = sorted(n for n, v in need.items() if v is None)
    if missing:
        return {"probability": None, "riskBand": "Not computable",
                "riskLevel": "Unknown", "missingFeatures": missing,
                "interpretationFa": (
                    "SMART2 به سن، فشار سیستولیک، کلسترول تام، HDL و eGFR "
                    f"نیاز دارد. مفقود: {'، '.join(missing)}.")}

    male = 1 if gender == "male" else 0
    smoke = 1 if flag_or_assume("Smoking", patient, 0, "context") else 0
    dm = 1 if (darad_tashkhis("Diabetes_Mellitus", diagnoses)
               or flag_or_assume("DiabetesFlag", patient, 0,
                                 "context")) else 0
    cad = 1 if darad_tashkhis("Coronary_Artery_Disease", diagnoses) else 0
    cevd = 1 if (darad_tashkhis("Stroke", diagnoses)
                 or darad_tashkhis("Cerebrovascular_Disease",
                                  diagnoses)) else 0
    pad = 1 if darad_tashkhis("PAD", diagnoses) else 0
    aaa = 1 if darad_tashkhis('AAA', diagnoses) else 0
    years = num_or_assume("YearsSinceFirstASCVD", dataset, patient, 1.0,
                          'context') or 1.0


    # SMART2 wants non-HDL in mmol/L; our lab values arrive as mg/dL.
    nonhdl = max((tc - hdl) / 38.67, 0.1)
    if crp is None or crp <= 0:
        _impute_sabt("hsCRP", "assumed 2.0 mg/L (cohort median)", "context")
        crp = 2.0


    lp = (_safe_log(1.61) * (age - 60.0) / 10.0
          + _safe_log(1.33) * male
          + _safe_log(1.41) * smoke
          + _safe_log(1.02) * (sbp - 140.0) / 10.0
          + _safe_log(1.28) * (nonhdl - 3.5)
          + _safe_log(1.37) * dm
          + _safe_log(1.34) * cad
          + _safe_log(1.42) * cevd
          + _safe_log(1.25) * pad
          + _safe_log(1.39) * aaa
          + _safe_log(1.18) * _safe_log(max(years, 0.5))
          + _safe_log(0.87) * (egfr - 80.0) / 10.0
          + _safe_log(1.25) * (_safe_log(crp) - _safe_log(2.0)))

    prob = _clamp(1.0 - (1.0 - 0.20) ** _safe_exp(lp), 0.0, 1.0)
    lvl = ("Low" if prob < 0.10 else 'Moderate' if prob < 0.20 else
           "High" if prob < 0.30 else "Very High")
    return {"probability": round(prob, 4),
            "riskBand": f"10-year recurrent ASCVD {prob*100:.1f}%",
            "riskLevel": lvl,
            "components": {"linear_predictor": round(lp, 4),
                           "non_hdl_mmol": round(nonhdl, 2)},
            'interpretationFa': (
                f"خطر ۱۰ساله رویداد قلبی‌عروقی مجدد: {prob*100:.1f}٪. "
                "مدل SMART2 با نسبت‌های خطر زیرتوزیعی منتشرشده "
                "(Hageman 2022, Eur Heart J). فقط برای بیماران با "
                "بیماری آترواسکلروتیک مستقر معتبر است. "
                "بروز پایه ۱۰ساله کوهورت UCC-SMART حدود ۲۰٪ فرض شده؛ "
                'برای جمعیت‌های دیگر نیاز به کالیبراسیون مجدد دارد.')}

def _hfa_peff_emtiaz(dataset, patient, gender, diagnoses):
    af = 1 if (darad_tashkhis("Atrial_Fibrillation", diagnoses)
               or darad_tashkhis("Stroke_AF", diagnoses)
               or flag_or_assume("AtrialFibrillation", patient, 0,
                                 'context')) else 0
    e_sep = adad("E_prime_septal", dataset, patient)
    e_lat = adad("E_prime_lateral", dataset, patient)
    e_over_e = adad("E_over_e_prime", dataset, patient)
    tr_vel = adad("TR_velocity", dataset, patient)
    gls = adad("GLS", dataset, patient)
    lavi = adad("LAVI", dataset, patient)
    lvmi = adad("LVMI", dataset, patient)
    rwt = adad('RWT', dataset, patient)
    wall = adad('LV_wall_thickness', dataset, patient)
    ntprobnp = adad("NT_proBNP", dataset, patient)
    bnp = adad("BNP", dataset, patient)

    male = gender == "male"


    func = 0
    if ((e_sep is not None and e_sep < 7) or
            (e_lat is not None and e_lat < 10) or
            (e_over_e is not None and e_over_e >= 15) or
            (tr_vel is not None and tr_vel > 2.8)):
        func = 2
    elif ((e_over_e is not None and 9 <= e_over_e <= 14) or
            (gls is not None and gls < 16)):
        func = 1


    lavi_major = 40.0 if af else 34.0
    lavi_minor_lo = 34.0 if af else 29.0
    morph = 0
    if ((lavi is not None and lavi > lavi_major) or
            (lvmi is not None and rwt is not None
             and lvmi >= (149.0 if male else 122.0) and rwt > 0.42)):
        morph = 2
    elif ((lavi is not None and lavi_minor_lo <= lavi <= lavi_major) or
            (lvmi is not None and lvmi > (115.0 if male else 95.0)) or
            (rwt is not None and rwt > 0.42) or
            (wall is not None and wall >= 12)):
        morph = 1


    bio = 0
    if af:
        nt_major, nt_minor = 660.0, 365.0
        b_major, b_minor = 240.0, 105.0
    else:
        nt_major, nt_minor = 220.0, 125.0
        b_major, b_minor = 80.0, 35.0
    if ((ntprobnp is not None and ntprobnp > nt_major) or
            (bnp is not None and bnp > b_major)):
        bio = 2
    elif ((ntprobnp is not None and ntprobnp >= nt_minor) or
            (bnp is not None and bnp >= b_minor)):
        bio = 1

    measured = sum(1 for v in (e_sep, e_lat, e_over_e, tr_vel, gls, lavi,
                               lvmi, rwt, wall, ntprobnp, bnp)
                   if v is not None)
    if measured == 0:
        return {"probability": None, "points": None,
                "riskBand": 'Not computable', "riskLevel": 'Unknown',
                "warnings": ["HFA-PEFF needs echocardiography and/or "
                             "natriuretic peptides; none supplied."],
                "interpretationFa": (
                    "HFA-PEFF بدون اکوکاردیوگرافی یا پپتید ناتریورتیک "
                    "قابل محاسبه نیست.")}

    pts = func + morph + bio
    if pts >= 5:
        band, lvl, prob = "HFpEF confirmed (>=5)", 'High', 0.90
    elif pts >= 2:
        band, lvl, prob = ("Intermediate (2-4): diastolic stress test or "
                           "invasive haemodynamics needed"), "Moderate", 0.50
    else:
        band, lvl, prob = "HFpEF unlikely (<=1)", "Low", 0.10
    return {"probability": prob, "points": pts, "maxPoints": 6,
            "riskBand": band, 'riskLevel': lvl,
            "components": {"functional": func, "morphological": morph,
                           "biomarker": bio,
                           'atrial_fibrillation': bool(af),
                           'domains_measured': measured},
            "interpretationFa": (
                f"HFA-PEFF = {pts} از ۶ (عملکردی {func}، ساختاری {morph}، "
                f"بیومارکر {bio}). معیار عمده ۲ امتیاز و معیار فرعی ۱ "
                "امتیاز؛ از هر دامنه حداکثر ۲ امتیاز. "
                + ("در فیبریلاسیون دهلیزی آستانه‌های بالاتر اعمال شد. "
                   if af else "")
                + "≥۵ تشخیصی HFpEF، ۲-۴ نیازمند تست استرس دیاستولیک، "
                "≤۱ بعید (Pieske 2019, Eur Heart J).")}

def _bova_pe_emtiaz(dataset, patient, gender, diagnoses):
    sbp = num_or_assume("Systolic_BP", dataset, patient, 115.0, 'auto')
    hr = num_or_assume("Heart_Rate", dataset, patient, 90.0, 'auto')
    trop_elev = (num_or_assume('Troponin_I', dataset, patient, 0.0, "auto")) > 0.04
    rv_dysfunction = flag_or_assume('RV_Dysfunction', patient, 0, "auto")

    pts = 0
    if 90 <= sbp <= 100: pts += 2
    if hr >= 110: pts += 1
    if trop_elev: pts += 2
    if rv_dysfunction: pts += 2


    if pts <= 2:
        stage = "Bova Stage I (Low Risk)"
        prob = 0.044
        band = "Low"
    elif pts <= 4:
        stage = "Bova Stage II (Intermediate Risk)"
        prob = 0.180
        band = 'Moderate'
    else:
        stage = 'Bova Stage III (High Complication Risk)'
        prob = 0.420
        band = "High"

    return {"probability": prob, 'riskBand': band, "riskLevel": band, "points": pts,
        "stage": stage,
        "interpretationFa": f"نمره Bova ارزیابی عوارض آمبولی ریه حدواسط: {stage} (امتیاز: {pts}، ریسک عوارض ۳۰ روزه: {prob*100:.1f}٪).",
        "components": {'Points': pts, "SBP": sbp, 'HR': hr, "TroponinElevated": trop_elev, "RVDysfunction": rv_dysfunction}
    }


def _khorana_vte_emtiaz(dataset, patient, gender, diagnoses):
    # FIX: unknown cancer site was silently scored 1.0 (high-risk site) for
    # everyone; now disclosed as 0 (with the Khorana gate, only cancer pts).
    site_score = num_or_assume("CancerSiteScore", dataset, patient, 0, "auto")
    plt = num_or_assume("Platelets", dataset, patient, 220.0, "auto")
    hb = num_or_assume("Hb", dataset, patient, 12.5, 'auto')
    wbc = num_or_assume("WBC", dataset, patient, 8.0, 'auto')
    bmi = num_or_assume("BMI", dataset, patient, 26.0, "auto")

    pts = site_score
    if plt >= 350.0: pts += 1
    if hb < 10.0 or flag_or_assume('ErythropoietinUsed', patient, 0, "auto"): pts += 1
    if wbc > 11.0: pts += 1
    if bmi >= 35.0: pts += 1

    prob_6m = 0.071 if pts >= 3 else 0.020 if pts >= 1 else 0.008
    band = 'High' if pts >= 3 else "Intermediate" if pts >= 1 else "Low"
    return {"probability": prob_6m, "riskBand": band, "riskLevel": band, "points": pts,
        "interpretationFa": f"نمره خورانا برای ترومبوز مرتبط با سرطان (VTE در ۶ ماه آینده): {pts} امتیاز ({'پرخطر >= 3 و نیازمند ترومبوپروفیلاکسی' if pts >= 3 else 'متوسط/کم‌خطر'}).",
        "components": {"Points": pts, "Platelets>=350": plt >= 350.0, "Hb<10": hb < 10.0, "WBC>11": wbc > 11.0, 'BMI>=35': bmi >= 35.0}
    }


def _khorana_gate(dataset, patient, diagnoses, gender):
    # FIX: Khorana requires active cancer; without this gate every outpatient
    # with routine labs scored "Intermediate". Gates read raw flags (no
    # imputation records are possible before _impute_bazneshani runs).
    if (parcham_bimar("ActiveCancer", patient) == 1
            or parcham_bimar("Cancer", patient) == 1
            or darad_tashkhis("Cancer", diagnoses)):
        return True, ""
    return False, "Khorana \u0641\u0642\u0637 \u0628\u0631\u0627\u06cc \u0628\u06cc\u0645\u0627\u0631\u0627\u0646 \u0645\u0628\u062a\u0644\u0627 \u0628\u0647 \u0633\u0631\u0637\u0627\u0646 \u0641\u0639\u0627\u0644 \u0645\u0639\u062a\u0628\u0631 \u0627\u0633\u062a."


def _german_diabetes_emtiaz(dataset, patient, gender, diagnoses):
    age = adad("Age", dataset, patient)
    waist = adad("Waist", dataset, patient)
    height = (adad("HeightCm", dataset, patient)
              or adad("Height", dataset, patient))
    if age is None or waist is None or height is None:
        return {'probability': None, "points": None,
                "riskBand": "Not computable", "riskLevel": "Unknown",
                "missingFeatures": [n for n, v in (("Age", age),
                                                   ("Waist", waist),
                                                   ("HeightCm", height))
                                    if v is None],
                "interpretationFa": (
                    "GDRS به سن، دور کمر و قد نیاز دارد.")}

    htn = 1 if (darad_tashkhis("Hypertension", diagnoses)
                or flag_or_assume("Hypertension", patient, 0,
                                  "context")) else 0
    sport_h = num_or_assume("PhysicalActivityHoursPerWeek", dataset,
                            patient, 0.0, "context") or 0.0
    red_meat = num_or_assume('RedMeatPortionsPerDay', dataset, patient,
                             0.0, 'context') or 0.0
    wholegrain = num_or_assume("WholegrainPortionsPerDay", dataset,
                               patient, 0.0, "context") or 0.0
    coffee = num_or_assume("CoffeeCupsPerDay", dataset, patient, 0.0,
                           "context") or 0.0

    smoke_pts = 0
    if flag_or_assume("FormerSmoker", patient, 0, 'context'):
        smoke_pts = 24 if not flag_or_assume(
            "HeavySmoker", patient, 0, "context") else 34
    if flag_or_assume("Smoking", patient, 0, 'context'):
        smoke_pts = 64 if flag_or_assume('HeavySmoker', patient, 0,
                                         "context") else 40

    fam = 0
    if flag_or_assume('BothParentsDiabetes', patient, 0, 'context'):
        fam += 106
    elif flag_or_assume("ParentDiabetes", patient, 0, 'context'):
        fam += 56
    if flag_or_assume('SiblingDiabetes', patient, 0, 'context'):
        fam += 48


    score = (7.4 * waist - 2.4 * height + 4.3 * age
             + 46.0 * htn
             + 55.0 * red_meat - 7.0 * wholegrain - 5.0 * coffee
             - 2.0 * sport_h
             + smoke_pts + fam)
    score = max(score, 0.0)

    x = _safe_exp(score / 100.0)
    prob = _clamp(1.0 - 0.999854 ** x, 0.0, 1.0)
    lvl = ("Low" if prob < 0.02 else "Moderate" if prob < 0.05 else
           "High" if prob < 0.10 else "Very High")
    return {"probability": round(prob, 4), 'points': int(round(score)),
            "riskBand": f"GDRS {score:.0f} points -> {prob*100:.1f}% "
                        "5-year risk",
            "riskLevel": lvl,
            "components": {"waist_term": round(7.4 * waist, 1),
                           'height_term': round(-2.4 * height, 1),
                           "age_term": round(4.3 * age, 1),
                           "hypertension": 46 * htn,
                           'smoking': smoke_pts,
                           "family_history": fam},
            "interpretationFa": (
                f"GDRS = {score:.0f} امتیاز؛ احتمال ابتلا به دیابت نوع ۲ "
                f"در ۵ سال آینده {prob*100:.1f}٪. معادله منتشرشده "
                "Schulze 2007: ۷٫۴×دورکمر − ۲٫۴×قد + ۴٫۳×سن + ۴۶×فشارخون "
                "+ سیگار + سابقه خانوادگی، سپس ۱ − ۰٫۹۹۹۸۵۴^exp(امتیاز/۱۰۰). "
                'اقلام تغذیه‌ای ثبت‌نشده صفر فرض شده‌اند.')}

def _visceral_adiposity_index(dataset, patient, gender, diagnoses):
    waist = num_or_assume("Waist", dataset, patient, 88.0, "auto")
    bmi = num_or_assume("BMI", dataset, patient, 26.0, 'auto')
    tg = num_or_assume("Triglycerides", dataset, patient, 150.0, "auto")
    hdl = num_or_assume("HDL", dataset, patient, 48.0, "auto")

    tg_mmol = tg / 88.57
    hdl_mmol = hdl / 38.67

    if gender == "male":
        vai = (waist / (39.68 + (1.88 * bmi))) * (tg_mmol / 1.03) * (1.31 / max(hdl_mmol, 0.5))
    else:
        vai = (waist / (36.58 + (1.89 * bmi))) * (tg_mmol / 0.81) * (1.52 / max(hdl_mmol, 0.5))

    prob = min(0.85, max(0.05, vai * 0.15))
    band = 'High' if vai >= 2.5 else "Moderate" if vai >= 1.6 else "Low"
    return {'probability': prob, "riskBand": band, "riskLevel": band, "score": round(vai, 2),
        "interpretationFa": f"شاخص چربی احشایی (VAI): {vai:.2f} ({'اختلال عملکرد بافت چربی احشایی و ریسک بالای کاردیومتابولیک' if vai >= 2.5 else 'طبیعی'}).",
        "components": {"VAI": round(vai, 2), 'Waist': waist, "BMI": bmi, "TG": tg, 'HDL': hdl}
    }


def _lipid_accumulation_product(dataset, patient, gender, diagnoses):
    waist = num_or_assume('Waist', dataset, patient, 88.0, "auto")
    tg = num_or_assume("Triglycerides", dataset, patient, 150.0, "auto")
    tg_mmol = tg / 88.57

    if gender == "male":
        lap = max(0.0, (waist - 65.0)) * tg_mmol
    else:
        lap = max(0.0, (waist - 58.0)) * tg_mmol

    prob = min(0.80, max(0.05, lap * 0.015))
    band = "High" if lap >= 45.0 else "Moderate" if lap >= 25.0 else "Low"
    return {"probability": prob, "riskBand": band, "riskLevel": band, "score": round(lap, 1),
        "interpretationFa": f"شاخص تجمع لیپید (LAP): {lap:.1f} ({'ریسک بالای آترواسکلروز و دیابت' if lap >= 45.0 else 'طبیعی'}).",
        "components": {"LAP": round(lap, 1), 'Waist': waist, "TG_mmol": round(tg_mmol, 2)}
    }


def _iga_nephropathy_tool(dataset, patient, gender, diagnoses):
    egfr = num_or_assume("eGFR", dataset, patient, 60.0, "auto")
    map_bp = num_or_assume("MAP", dataset, patient, 95.0, "auto")
    proteinuria = adad("UrineProtein24h", dataset, patient) or (num_or_assume("UPCR", dataset, patient, 1.0, "auto")) * 1000.0
    age = num_or_assume("Age", dataset, patient, 38.0, 'auto')
    ras_blocker = flag_or_assume("OnRASBlocker", patient, 1, "auto")


    lp = -0.045 * (egfr - 60) + 0.025 * (map_bp - 90) + 0.38 * _safe_log(max(proteinuria/1000.0, 0.1)) + 0.015 * (age - 35) - 0.25 * ras_blocker
    prob_5y = 1.0 - math.pow(0.88, _safe_exp(lp * 0.6))
    prob_5y = max(0.02, min(0.90, prob_5y))
    band = "High" if prob_5y >= 0.25 else "Moderate" if prob_5y >= 0.10 else "Low"
    return {"probability": prob_5y, "riskBand": band, "riskLevel": band, "interpretationFa": f"ریسک ۵ ساله پیشرفت نفروپاتی IgA به نارسایی کلیه: {prob_5y*100:.1f}٪ (طبقه: {band}).",
        "components": {'eGFR': egfr, "MAP": map_bp, "Proteinuria_mg": proteinuria, 'OnRASBlocker': ras_blocker}
    }


def _cairo_bishop_tls_staging(dataset, patient, gender, diagnoses):
    ua = num_or_assume("UricAcid", dataset, patient, 5.0, 'auto')
    k = num_or_assume("Potassium", dataset, patient, 4.0, "auto")
    phos = num_or_assume("Phosphate", dataset, patient, 3.5, "auto")
    ca = num_or_assume("Calcium", dataset, patient, 9.5, "auto")
    cr = num_or_assume('Creatinine', dataset, patient, 1.0, 'auto')

    lab_tls_count = sum([ua >= 8.0, k >= 6.0, phos >= 4.5, ca <= 7.0])
    lab_tls = lab_tls_count >= 2
    clinical_tls = lab_tls and (cr >= 1.5 or k >= 6.5)

    if clinical_tls:
        grade = "Clinical TLS (Grade 2-3 Emergency)"
        prob = 0.95
        band = 'Very High'
    elif lab_tls:
        grade = "Laboratory TLS (Grade 1 Alert)"
        prob = 0.70
        band = 'High'
    else:
        grade = "No TLS (Quiescent)"
        prob = 0.05
        band = "Low"

    return {"probability": prob, "riskBand": band, "riskLevel": band, 'grade': grade,
        "criteria_count": lab_tls_count,
        "interpretationFa": f"طبقه‌بندی سندرم لیز تومور قاهره-بیشاپ: {grade} (تعداد معیارهای مثبت: {lab_tls_count} از ۴).",
        'components': {"UricAcid": ua, "Potassium": k, "Phosphate": phos, "Calcium": ca, 'Creatinine': cr}
    }


def _apache_ii_emtiaz(dataset, patient, gender, diagnoses):
    def _band(v, table, default=0):
        if v is None:
            return None
        for lo, hi, pts in table:
            if (lo is None or v >= lo) and (hi is None or v < hi):
                return pts
        return default

    age = adad("Age", dataset, patient)
    temp = adad("TemperatureC", dataset, patient)
    map_bp = adad("MAP", dataset, patient)
    hr = adad("Heart_Rate", dataset, patient)
    rr = adad("RespiratoryRate", dataset, patient)
    pao2 = adad("PaO2", dataset, patient)
    ph = adad("Arterial_pH", dataset, patient)
    na = adad('Sodium', dataset, patient)
    k_ = adad("Potassium", dataset, patient)
    cr = adad("Creatinine", dataset, patient)
    hct = adad("Hematocrit", dataset, patient)
    wbc = adad('WBC', dataset, patient)
    gcs = adad("GCS", dataset, patient)

    T_TEMP = [(41.0, None, 4), (39.0, 41.0, 3), (38.5, 39.0, 1),
              (36.0, 38.5, 0), (34.0, 36.0, 1), (32.0, 34.0, 2),
              (30.0, 32.0, 3), (None, 30.0, 4)]
    T_MAP = [(160.0, None, 4), (130.0, 160.0, 3), (110.0, 130.0, 2),
             (70.0, 110.0, 0), (50.0, 70.0, 2), (None, 50.0, 4)]
    T_HR = [(180.0, None, 4), (140.0, 180.0, 3), (110.0, 140.0, 2),
            (70.0, 110.0, 0), (55.0, 70.0, 2), (40.0, 55.0, 3),
            (None, 40.0, 4)]
    T_RR = [(50.0, None, 4), (35.0, 50.0, 3), (25.0, 35.0, 1),
            (12.0, 25.0, 0), (10.0, 12.0, 1), (6.0, 10.0, 2),
            (None, 6.0, 4)]
    T_PAO2 = [(70.0, None, 0), (61.0, 70.0, 1), (55.0, 61.0, 3),
              (None, 55.0, 4)]
    T_PH = [(7.7, None, 4), (7.6, 7.7, 3), (7.5, 7.6, 1),
            (7.33, 7.5, 0), (7.25, 7.33, 2), (7.15, 7.25, 3),
            (None, 7.15, 4)]
    T_NA = [(180.0, None, 4), (160.0, 180.0, 3), (155.0, 160.0, 2),
            (150.0, 155.0, 1), (130.0, 150.0, 0), (120.0, 130.0, 2),
            (111.0, 120.0, 3), (None, 111.0, 4)]
    T_K = [(7.0, None, 4), (6.0, 7.0, 3), (5.5, 6.0, 1),
           (3.5, 5.5, 0), (3.0, 3.5, 1), (2.5, 3.0, 2), (None, 2.5, 4)]
    T_CR = [(3.5, None, 4), (2.0, 3.5, 3), (1.5, 2.0, 2),
            (0.6, 1.5, 0), (None, 0.6, 2)]
    T_HCT = [(60.0, None, 4), (50.0, 60.0, 2), (46.0, 50.0, 1),
             (30.0, 46.0, 0), (20.0, 30.0, 2), (None, 20.0, 4)]
    T_WBC = [(40.0, None, 4), (20.0, 40.0, 2), (15.0, 20.0, 1),
             (3.0, 15.0, 0), (1.0, 3.0, 2), (None, 1.0, 4)]

    parts = {
        "temperature": _band(temp, T_TEMP),
        'map': _band(map_bp, T_MAP),
        "heart_rate": _band(hr, T_HR),
        "respiratory_rate": _band(rr, T_RR),
        "oxygenation": _band(pao2, T_PAO2),
        "arterial_ph": _band(ph, T_PH),
        "sodium": _band(na, T_NA),
        "potassium": _band(k_, T_K),
        "creatinine": _band(cr, T_CR),
        "hematocrit": _band(hct, T_HCT),
        "wbc": _band(wbc, T_WBC),
    }

    parts["gcs"] = None if gcs is None else int(_clamp(15.0 - gcs, 0.0, 12.0))

    missing = sorted(n for n, v in parts.items() if v is None)


    # Refusing to score beats scoring on assumptions here: filling in
    # 'normal' for absent vitals makes a dying patient look stable.
    if len(missing) > 3:
        return {"probability": None, "points": None,
                "riskBand": "Not computable",
                "riskLevel": "Unknown",
                "missingFeatures": missing,
                'warnings': [
                    "APACHE II needs the worst values from the first 24h. "
                    f"{len(missing)} of 12 physiologic variables are missing "
                    f"({', '.join(missing)}); a score computed by assuming "
                    "they are normal would understate mortality."],
                'interpretationFa': (
                    "محاسبه APACHE II ممکن نیست: "
                    f"{len(missing)} متغیر از ۱۲ متغیر فیزیولوژیک ثبت نشده. "
                    "فرضِ طبیعی‌بودن آن‌ها مرگ‌ومیر را کمتر از واقع "
                    "نشان می‌دهد.")}

    for name in missing:
        _impute_sabt(name, "assumed normal (0 points)", "critical")
        parts[name] = 0

    aps = sum(parts.values())
    if age is None:
        _impute_sabt("Age", "assumed <45 (0 points)", "critical")
        age_pts = 0
    else:
        age_pts = (0 if age < 45 else 2 if age < 55 else
                   3 if age < 65 else 5 if age < 75 else 6)
    chronic = 0
    if flag_or_assume("Chronic_Organ_Insufficiency", patient, 0, 'context'):
        chronic = 2 if flag_or_assume(
            'Elective_Postoperative', patient, 0, "context") else 5

    score = int(aps + age_pts + chronic)

    # Knaus 1985 non-operative logistic. Calibrated on 1979-82 ICUs,
    # so it runs high against modern survival - group prognosis only.
    logit = -3.517 + 0.146 * score
    mort = _clamp(1.0 / (1.0 + _safe_exp(-logit)), 0.0, 1.0)
    lvl = ("Low" if score <= 9 else 'Moderate' if score <= 19 else
           "High" if score <= 29 else "Very High")
    return {"probability": round(mort, 4), 'points': score,
            "maxPoints": 71,
            "riskBand": f"APACHE II {score} (APS {aps} + age {age_pts}"
                        f" + chronic {chronic})",
            "riskLevel": lvl,
            "components": dict(parts, age_points=age_pts,
                               chronic_health=chronic),
            "interpretationFa": (
                f"APACHE II = {score} از ۷۱ (نمره فیزیولوژیک حاد {aps}، "
                f"سن {age_pts}، بیماری مزمن {chronic}). مرگ‌ومیر تخمینی "
                f"بیمارستانی حدود {mort*100:.0f}٪ بر پایه رگرسیون "
                'لجستیک Knaus 1985: logit = -3.517 + 0.146 × APACHE II. '
                "این عدد برای پیش‌آگهی گروهی است، نه تصمیم درمانی فردی.")}

def _saps_ii_emtiaz(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 55.0, "auto")
    hr = num_or_assume("Heart_Rate", dataset, patient, 80.0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 120.0, "auto")
    temp = num_or_assume("TemperatureC", dataset, patient, 37.0, 'auto')
    pao2_fio2 = num_or_assume("PaO2_FiO2", dataset, patient, 400.0, "auto")
    bun = num_or_assume("BUN", dataset, patient, 15.0, 'auto')
    wbc = num_or_assume('WBC', dataset, patient, 8.0, "auto")
    k = num_or_assume("Potassium", dataset, patient, 4.0, "auto")
    na = num_or_assume("Sodium", dataset, patient, 140.0, "auto")
    bicarb = num_or_assume("Bicarbonate", dataset, patient, 24.0, "auto")
    bili = num_or_assume("Bilirubin", dataset, patient, 0.8, "auto")
    gcs = num_or_assume("GCS", dataset, patient, 15.0, "auto")

    pts = 0
    if age >= 80: pts += 18
    elif age >= 75: pts += 16
    elif age >= 70: pts += 15
    elif age >= 60: pts += 12
    elif age >= 40: pts += 7

    if hr >= 160: pts += 11
    elif hr >= 120 or hr < 40: pts += 4

    if sbp < 70: pts += 13
    elif sbp < 100: pts += 5
    elif sbp >= 200: pts += 2

    if temp >= 39.0: pts += 3

    if pao2_fio2 < 100: pts += 11
    elif pao2_fio2 < 200: pts += 9
    elif pao2_fio2 < 300: pts += 6

    if bun >= 84.0: pts += 10
    elif bun >= 28.0: pts += 6

    if wbc >= 20.0 or wbc < 1.0: pts += 3

    if k >= 5.0 or k < 3.0: pts += 3
    if na >= 145 or na < 125: pts += 1
    if bicarb < 15.0: pts += 6
    elif bicarb < 20.0: pts += 3

    if bili >= 6.0: pts += 9
    elif bili >= 4.0: pts += 4

    if gcs < 6: pts += 26
    elif gcs <= 8: pts += 13
    elif gcs <= 10: pts += 7
    elif gcs <= 13: pts += 5

    logit = -7.7631 + 0.0737 * pts + 0.9971 * _safe_log(max(pts + 1, 1))
    prob = 1.0 / (1.0 + _safe_exp(-logit))
    prob = max(0.01, min(0.98, prob))
    band = "Very High" if pts >= 50 else "High" if pts >= 35 else "Moderate" if pts >= 20 else "Low"
    return {"probability": prob, "riskBand": band, "riskLevel": band, "points": pts,
        "warnings": ["Chronic-disease and admission-type points are unavailable; probability may underestimate mortality."],
        "interpretationFa": f"نمره فیزیولوژی حاد SAPS II: {pts} امتیاز (احتمال مرگ‌ومیر ICU: {prob*100:.1f}٪).",
        "components": {'SAPS_II_Points': pts, "Age": age, "GCS": gcs, "BUN": bun, "PaO2/FiO2": pao2_fio2}
    }


def _r2_iss_myeloma(dataset, patient, gender, diagnoses):
    iss_stage = num_or_assume("ISS_Stage", dataset, patient, 2.0, "auto")
    high_risk_ca = flag_or_assume("HighRiskCytogenetics_del17p_t4_14_t14_16", patient, 0, "auto")
    one_q_gain = flag_or_assume('Gain_1q21', patient, 0, "auto")
    ldh_elev = (num_or_assume('LDH', dataset, patient, 200.0, "auto")) > 250.0

    pts = 0
    if iss_stage == 3: pts += 1.5
    elif iss_stage == 2: pts += 1.0

    if high_risk_ca: pts += 1.5
    if one_q_gain: pts += 1.0
    if ldh_elev: pts += 1.0

    if pts == 0:
        stage = 'R2-ISS Stage I (Low Risk / 5y OS ~86%)'
        prob_prog = 0.15
        band = "Low"
    elif pts <= 1.0:
        stage = "R2-ISS Stage II (Intermediate-Low Risk / 5y OS ~78%)"
        prob_prog = 0.22
        band = "Moderate"
    elif pts <= 2.5:
        stage = "R2-ISS Stage III (Intermediate-High Risk / 5y OS 55%)"
        prob_prog = 0.45
        band = "High"
    else:
        stage = "R2-ISS Stage IV (High Risk / 5y OS 30%)"
        prob_prog = 0.70
        band = 'Very High'

    return {"probability": prob_prog, 'riskBand': band, "riskLevel": band, "points": pts,
        'stage': stage,
        "interpretationFa": f"مرحله‌بندی R2-ISS میلوم مولتیپل (۲۰۲۲): {stage} (امتیاز خطر: {pts:.1f}).",
        "components": {"R2_ISS_Points": pts, "ISS_Stage": iss_stage, "HighRiskCytogenetics": high_risk_ca, "LDH_Elevated": ldh_elev}
    }


def _ipi_dlbc_lymphoma(dataset, patient, gender, diagnoses):
    age = num_or_assume("Age", dataset, patient, 58.0, "auto")
    stage_3_4 = flag_or_assume("AnnArborStage_III_IV", patient, 0, "auto")
    extranodal = flag_or_assume("ExtranodalSites_gt1", patient, 0, "auto")
    ecog = num_or_assume("ECOG_PerformanceStatus", dataset, patient, 1.0, "auto")
    ldh_elev = (num_or_assume("LDH", dataset, patient, 200.0, "auto")) > 250.0

    pts = 0
    if age > 60: pts += 1
    if stage_3_4: pts += 1
    if extranodal: pts += 1
    if ecog >= 2: pts += 1
    if ldh_elev: pts += 1

    if pts <= 1:
        group = "Low Risk (5y OS 73%)"
        mort = 0.27
        band = 'Low'
    elif pts == 2:
        group = "Low-Intermediate (5y OS 51%)"
        mort = 0.49
        band = "Moderate"
    elif pts == 3:
        group = "High-Intermediate (5y OS 43%)"
        mort = 0.57
        band = "High"
    else:
        group = "High Risk (5y OS 26%)"
        mort = 0.74
        band = 'Very High'

    return {"probability": mort, "riskBand": band, "riskLevel": band, "points": pts,
        "risk_group": group,
        "interpretationFa": f"شاخص پیش‌آگهی بین‌المللی لنفوم IPI: گروه {group} (امتیاز: {pts} از ۵).",
        "components": {'Age>60': age > 60, "Stage_III_IV": stage_3_4, "ECOG>=2": ecog >= 2, "LDH_Elevated": ldh_elev}
    }


def _cll_ipi_emtiaz(dataset, patient, gender, diagnoses):
    tp53 = flag_or_assume("TP53_Mutation_del17p", patient, 0, "auto")
    ighv_unmutated = flag_or_assume("IGHV_Unmutated", patient, 0, "auto")
    b2m = num_or_assume("Beta2Microglobulin", dataset, patient, 2.5, "auto")
    stage = flag_or_assume("Binet_B_C_or_Rai_I_IV", patient, 0, "auto")
    age = num_or_assume("Age", dataset, patient, 62.0, "auto")

    pts = 0
    if tp53: pts += 4
    if ighv_unmutated: pts += 2
    # FIX P45: published CLL-IPI cutoff is B2M > 3.5 mg/L (IKW 2016), not 4.0.
    if b2m > 3.5: pts += 2
    if stage: pts += 1
    if age > 65: pts += 1

    if pts <= 1:
        group = "Low Risk (5y OS 93%)"
        mort = 0.07
        band = "Low"
    elif pts <= 3:
        group = "Intermediate Risk (5y OS 79%)"
        mort = 0.21
        band = "Moderate"
    elif pts <= 6:
        group = "High Risk (5y OS 63%)"
        mort = 0.37
        band = "High"
    else:
        group = "Very High Risk (5y OS 23%)"
        mort = 0.77
        band = "Very High"

    return {"probability": mort, "riskBand": band, "riskLevel": band, "points": pts,
        "risk_group": group,
        "interpretationFa": f"شاخص پیش‌آگهی بین‌المللی لوسمی CLL (CLL-IPI): {group} (امتیاز: {pts} از ۱۰).",
        "components": {'TP53_del17p': tp53, "IGHV_Unmutated": ighv_unmutated, "Beta2M>3.5": b2m > 3.5, "Age>65": age > 65}
    }


def _aims65_emtiaz(dataset, patient, gender, diagnoses):
    alb = num_or_assume("Albumin", dataset, patient, 4.0, "auto")
    inr = num_or_assume("INR", dataset, patient, 1.1, "auto")
    gcs = num_or_assume("GCS", dataset, patient, 15.0, "auto")
    sbp = num_or_assume("Systolic_BP", dataset, patient, 120.0, "auto")
    age = num_or_assume("Age", dataset, patient, 55.0, "auto")

    pts = 0
    if alb < 3.0: pts += 1
    if inr > 1.5: pts += 1
    if gcs < 15: pts += 1
    if sbp <= 90: pts += 1
    if age >= 65: pts += 1

    mort_map = {0: 0.003, 1: 0.012, 2: 0.053, 3: 0.103, 4: 0.165, 5: 0.245}
    prob = mort_map.get(pts, 0.30)
    band = "High" if pts >= 3 else 'Moderate' if pts >= 2 else "Low"
    return {'probability': prob, "riskBand": band, 'riskLevel': band, "points": pts,
        "interpretationFa": f"نمره مرگ‌ومیر خونریزی گوارشی فوقانی AIMS65: {pts} از ۵ (مرگ‌ومیر داخل بیمارستانی: {prob*100:.1f}٪).",
        "components": {"Albumin<3": alb < 3.0, 'INR>1.5': inr > 1.5, "AlteredMental": gcs < 15, "SystolicBP<=90": sbp <= 90, 'Age>=65': age >= 65}
    }


def _kings_college_alf(dataset, patient, gender, diagnoses):
    inr = adad("INR", dataset, patient) or (num_or_assume("ProthrombinTime", dataset, patient, 13.0, "auto")) / 12.0
    cr = num_or_assume("Creatinine", dataset, patient, 1.0, "auto")
    ph = num_or_assume("Arterial_pH", dataset, patient, 7.40, "auto")
    lactate = num_or_assume("Lactate", dataset, patient, 1.5, "auto")
    bili = num_or_assume("Bilirubin", dataset, patient, 1.0, "auto")
    age = num_or_assume('Age', dataset, patient, 35.0, "auto")
    paracetamol = flag_or_assume("AcetaminophenOverdose", patient, 0, "auto")

    met = False
    if paracetamol:
        if ph < 7.30 or lactate > 3.0: met = True
        elif (inr > 6.5) and (cr > 3.4): met = True
    else:
        if inr > 6.5: met = True
        else:
            criteria_count = sum([age < 10 or age > 40, bili > 17.5, inr > 3.5])
            if criteria_count >= 3: met = True

    prob_mort = 0.85 if met else 0.15
    band = "Very High" if met else "Low"
    return {"probability": prob_mort, "riskBand": band, "riskLevel": band, "criteria_met": met,
        "interpretationFa": f"معیار کالج کینگز نارسایی حاد کبد: {'معیار پیوند اورژانسی کبد برقرار است (مرگ بدون پیوند > ۸۰٪)' if met else 'عدم برقراری معیار پیوند فوری'}.",
        "components": {'INR': inr, "Arterial_pH": ph, "Lactate": lactate, "Creatinine": cr, "Acetaminophen": paracetamol}
    }


MODELS = [

    _spec("Diabetes_Mellitus", "Type 2 Diabetes - 10y risk (FINDRISC)",
          "FINDRISC", "Lindstrom J, Tuomilehto J. Diabetes Care 2003;26:725-731",
          "10.2337/diacare.26.3.725", "validated_score",
          ["Age", 'BMI', "Waist", "PhysicalActivity", 'DailyFruitVeg',
           "BpTreated", "HxHighGlucose", "FamilyHistory_DM"],
          _findrisc, horizon=10, exclude=["Diabetes_Mellitus"]),
    _spec("Diabetes_Mellitus_Lab", "Diabetes lab cross-check (heuristic)",
          "Internal logistic (labs)", 'HEMOGLYPH internal heuristic', "-",
          "heuristic", ["FBS", "BMI"], _heuristic_diabetes_azmayesh, horizon=10,
          exclude=["Diabetes_Mellitus"]),
    _spec('Prediabetes', "Prediabetes screening (CDC/ADA risk test)",
          "CDC/ADA Prediabetes Risk Test", "Bang H, et al. Diabetes Care 2009;32:1917",
          "10.2337/dc09-0662", 'validated_score',
          ['Age', "BMI"], _cdc_prediabetes, horizon=10,
          exclude=[("Diabetes_Mellitus", 'Prediabetes')]),
    _spec('Cardiovascular_Risk', "10-y ASCVD risk (Pooled Cohort Equations)",
          "ACC/AHA 2013 PCE", "Goff DC Jr, et al. Circulation 2014;129(25 Suppl 2):S49-73",
          "10.1161/01.cir.0000437741.48606.98", "validated_equation",
          ['Age', "Systolic_BP", "TotalCholesterol", 'HDL'],
          _ascvd_pce, horizon=10, exclude=["Cardiovascular_Risk"],
          gate=_ascvd_gate),
    _spec('Framingham_General_CVD', "10-y general CVD risk (Framingham)",
          "Framingham General CVD 2008", "D'Agostino RB, et al. Circulation 2008;117:743",
          '10.1161/CIRCULATIONAHA.107.699579', "validated_equation",
          ['Age', "Systolic_BP", "TotalCholesterol", 'HDL'],
          _framingham_general_cvd, horizon=10, exclude=["Cardiovascular_Risk"]),
    _spec("SCORE2_10Y", '10-y fatal+nonfatal CVD risk (SCORE2, ESC 2021)',
          "SCORE2 (+regional recalibration)", "SCORE2 WG. Eur Heart J 2021;42:2439-2454",
          '10.1093/eurheartj/ehab309', "validated_equation",
          ["Age", "Systolic_BP", "TotalCholesterol", 'HDL'],
          _score2, horizon=10, exclude=["Cardiovascular_Risk"], gate=_score2_gate),
    _spec("CAD_TIMI_NSTEMI", "14-day risk after UA/NSTEMI (TIMI)",
          "TIMI Risk Score", "Antman EM, et al. JAMA 2000;284:835",
          "10.1001/jama.284.7.835", "validated_score",
          ["Age", "CAD_RiskFactorCount"], _timi_uanstemi, horizon=0.04),
    _spec("ACS_HEART", "6-week MACE in chest pain (HEART)",
          "HEART score", "Six AJ, et al. Neth Heart J 2008;16:191",
          "-", 'validated_score',
          ["HEART_History", "ECG_ST_Score", "Age", "Troponin", "Troponin_ULN"],
          _heart_emtiaz, horizon=0.12),
    _spec("Heart_Failure_MAGGIC", "HF mortality 1y/3y (MAGGIC)",
          "MAGGIC integer risk score", "Pocock SJ, et al. Eur Heart J 2013;34:1404",
          "10.1093/eurheartj/ehs337", "validated_score",
          ["Age", "Systolic_BP", "BMI", "Creatinine", "LVEF", 'NYHA_Class'],
          _maggic, horizon=3, gate=_maggic_gate),
    _spec("HFpEF_H2FPEF", "HFpEF diagnostic probability (H2FPEF)",
          "H2FPEF", "Reddy YNV, et al. Circulation 2018;138:861",
          "10.1161/CIRCULATIONAHA.118.034646", "validated_score",
          ["BMI", "Age", 'PASP', 'E_e_ratio', "Antihypertensive_Count"],
          _h2fpef),
    _spec("AF_Stroke_CHA2DS2VASc", "Annual stroke risk in AF (CHA2DS2-VASc)",
          "CHA2DS2-VASc", "Lip GY, et al. Chest 2010;137:263",
          "10.1378/chest.09-1584", 'validated_score',
          ["Age", 'Systolic_BP'], _cha2ds2vasc,
          horizon=1, gate=_cha_gate),
    _spec("AF_Bleeding_HASBLED", "Annual major bleeding on OAC (HAS-BLED)",
          "HAS-BLED", "Pisters R, et al. Chest 2010;138:1093",
          "10.1378/chest.10-0134", "validated_score",
          ["Age", "Systolic_BP"], _has_bled, horizon=1, gate=_cha_gate),
    _spec("AF_Bleeding_ORBIT", "Annual bleeding on OAC (ORBIT-AF)",
          "ORBIT-AF bleeding risk", "O'Brien EC, et al. JACC 2015;66:2205",
          "10.1016/j.jacc.2015" , 'validated_score',
          ["Age", "Hb", "eGFR"], _orbit_af, horizon=1, gate=_cha_gate),
    _spec("AF_Bleeding_ATRIA", "Annual bleeding risk in AF (ATRIA)",
          "ATRIA bleeding risk", "Fang MC, et al. JACC 2011;58:395",
          '10.1016/j.jacc' , "validated_score",
          ["Age", "Hb", 'eGFR'], _atria_bleed, horizon=1, gate=_cha_gate),
    _spec("TIA_Stroke_ABCD2", "2-day stroke risk after TIA (ABCD2)",
          "ABCD2", 'Johnston SC, et al. Lancet 2007;369:283',
          "10.1016/S0140-6736(07)60150-0", 'validated_score',
          ["Age", "Systolic_BP", "ABCD2_Clinical", "TIA_Duration_Min"],
          _abcd2, horizon=0.006),
    _spec("DVT_Wells", "Pre-test probability of DVT (Wells)",
          "Wells DVT", 'Wells PS, et al. Lancet 1995;345:1326',
          "10.1016/S0140-6736(95)92575-4", "validated_score",
          ['PriorVTE', "Paralysis_Paresis_Cast", "Leg_Tenderness",
           "Calf_Swelling_3cm"], _wells_dvt, horizon=0.01),
    _spec('PE_Wells', "Pre-test probability of PE (Wells)",
          "Wells PE", "Wells PS, et al. Thromb Haemost 2000;83:416",
          "10.1055/s-0037-1613962", "validated_score",
          ["Heart_Rate", "PriorVTE"], _wells_pe, horizon=0.01),
    _spec('PE_Geneva', "Pre-test probability of PE (revised Geneva)",
          'Revised Geneva', "Le Gal G, et al. Ann Intern Med 2006;144:165",
          "10.7326/0003-4819-144-3-200602070-00006", "validated_score",
          ["Age", "Heart_Rate"], _geneva_revised, horizon=0.01),
    _spec("PE_30d_sPESI", "30-day mortality after PE (sPESI)",
          "sPESI", "Jimenez D, et al. Arch Intern Med 2010;170:1383",
          "10.1001/archinternmed.2010.125", 'validated_score',
          ["Age", 'Heart_Rate', 'Systolic_BP', "SpO2"], _spesi, horizon=0.08),
    _spec("VTE_Caprini", 'Surgical VTE risk (Caprini 2013)',
          'Caprini RAM', "Bahl V, et al. Ann Surg 2010;251:344 (Caprini 2013 update)",
          '10.1097/SLA.0b013e3181a62d9f', "validated_score",
          ["Age", "BMI"], _caprini, horizon=0.25),
    _spec('VTE_Padua', "Medical in-patient VTE risk (Padua)",
          "Padua Prediction Score", "Barbar S, et al. J Thromb Haemost 2010;8:2450",
          "10.1111/j.1538-7836.2010.04044.x", "validated_score",
          ['Age', "BMI"], _padua, horizon=0.25),
    _spec("Familial_Hypercholesterolemia_DLCN",
          'Familial hypercholesterolaemia (DLCN criteria)',
          "Dutch Lipid Clinic Network score", "WHO FH criteria 1999; NICE CG71 2008",
          '-', "validated_criteria",
          ["LDL"], _dlcn, exclude=['Familial_Hypercholesterolemia']),
    _spec("PAD_ABI", "Peripheral arterial disease from ABI",
          "ABI interpretation (AHA/TASC)", "Aboyans V, et al. JACC 2012;60:2521",
          "10.1016/j.jacc.2012.07.012", 'validated_criteria',
          ['ABI'], _pad_abi, exclude=["PAD"]),

    _spec("Chronic_Kidney_Disease", 'Kidney failure 2y/5y risk (KFRE)',
          "Tangri KFRE 4-variable (non-NA calibration)", "Tangri N, et al. JAMA 2011;305:1553",
          "10.1001/jama.2011.451", "validated_equation",
          ["Age", "eGFR", "ACR"], _kfre4, horizon=2, gate=_kfre_gate),
    _spec("CKD_KDIGO_Grid", "CKD staging + prognosis (KDIGO)",
          "KDIGO 2012/2024 GFR-Albuminuria grid", 'KDIGO CKD Work Group. Kidney Int Suppl 2013;3:1',
          '-', "validated_criteria",
          ["eGFR"], _kdigo_ckd),  # FIX P19: ACR-or-PCR handled (and disclosed) inside the fn
    _spec("Acute_Kidney_Injury", "AKI detection/staging (KDIGO 2012)",
          "KDIGO SCr criteria", "KDIGO AKI Work Group. Kidney Int Suppl 2012;2:1",
          "-", "validated_criteria",
          ["Creatinine"], _kdigo_aki, exclude=["Acute_Kidney_Injury"]),

    _spec("NAFLD", 'Hepatic steatosis probability (FLI)',
          "Fatty Liver Index", "Bedogni G, et al. BMC Gastroenterol 2006;6:33",
          "10.1186/1471-230X-6-33", "validated_equation",
          ["Triglycerides", 'BMI', "GGT", "Waist"], _fli,
          exclude=["NAFLD"]),
    _spec("NAFLD_HSI", "Hepatic Steatosis Index (HSI)",
          "HSI", "Lee JH, et al. Dig Liver Dis 2010;42:503",
          '10.1016/j.dld.2009.12.005', "validated_equation",
          ['ALT', "AST", "BMI"], _hsi, exclude=["NAFLD"],
          gate=_hepatic_steatosis_gate),
    _spec("NASH", 'Advanced liver fibrosis risk (FIB-4)',
          "FIB-4", "Sterling RK, et al. Hepatology 2006;43:1317; Shah 2009",
          "10.1002/hep.21194", "validated_equation",
          ["Age", "AST", "ALT", "Platelets"], _fib4,
          exclude=['NASH']),
    _spec("Liver_Fibrosis_APRI", "Advanced fibrosis (APRI)",
          'APRI', 'Wai CT, et al. Hepatology 2003;38:518',
          '10.1053/jhep.2003.50353', 'validated_equation',
          ["AST", "Platelets"], _apri, exclude=["Cirrhosis"]),
    _spec("Liver_Fibrosis_NFS", "Advanced fibrosis (NAFLD Fibrosis Score)",
          "NFS", "Angulo P, et al. Hepatology 2007;45:846",
          "10.1002/hep.21496", "validated_equation",
          ["Age", "BMI", "AST", "ALT", "Platelets", 'Albumin'], _nfs,
          exclude=["Cirrhosis"]),
    _spec('Liver_Fibrosis_BARD', "Advanced fibrosis (BARD)",
          'BARD', "Harrison SA, et al. BMC Gastroenterol 2008;8:89",
          '10.1186/1471-230X-8-89', 'validated_score',
          ["BMI", "AST", "ALT"], _bard, exclude=["Cirrhosis"],
          gate=_hepatic_steatosis_gate),
    _spec('Liver_ALBI', "Liver function grade (ALBI)",
          'ALBI', "Johnson PJ, et al. J Clin Oncol 2015;33:550",
          '10.1200/JCO.2014.57.9151', "validated_equation",
          ["Bilirubin", "Albumin"], _albi),
    _spec('Cirrhosis_MELD_Na', "3-month mortality (MELD-Na, OPTN)",
          'MELD / MELD-Na', "Kamath PS, Hepatology 2001; OPTN policy 2016",
          '10.1053/jhep.2001.22172', "validated_equation",
          ["Bilirubin", "INR", "Creatinine", "Sodium"], _meld,
          gate=None),
    _spec("Cirrhosis_MELD3", "3-month mortality (MELD 3.0, OPTN 2023)",
          "MELD 3.0", "Kim WR, et al. Gastroenterology 2021;161:1887",
          "10.1053/j.gastro.2021.08.050", "validated_equation",
          ["Bilirubin", "INR", "Creatinine", "Albumin", "Sodium", 'Sex'],
          _meld3, gate=_meld3_gate),
    _spec("Cirrhosis_Child_Pugh", "Cirrhosis severity (Child-Pugh)",
          "Child-Pugh", "Pugh RN, et al. Br J Surg 1973;60:646",
          "10.1002/bjs.1800600817", "validated_score",
          ["Bilirubin", "Albumin", "INR"], _child_pugh),
    _spec("HCC_REACH_B", "HCC 3/5/10-y risk in chronic HBV (REACH-B)",
          'REACH-B', "Yang HI, et al. Lancet Oncol 2011;12:568",
          "10.1016/S1470-2045(11)70076-1", "validated_score",
          ["Age", "ALT", "HBeAg", "HBV_DNA_IU", "HBsAg"],
          _reach_b, horizon=3, gate=_reachb_gate, exclude=['HCC']),
    _spec("HCC_PAGE_B", "HCC 5-y risk on ETV/TDF (PAGE-B)",
          "PAGE-B", "Papatheodoridis G, et al. J Hepatol 2016;65:800",
          "10.1016/j.jhep.2016.05.035", 'validated_score',
          ["Age", "Platelets"], _safhe_b, horizon=5,
          gate=_reachb_gate, exclude=["HCC"]),
    _spec("HCC_GALAD", "HCC detection score (GALAD)",
          "GALAD", "Berhane S, et al. Cancer Epidemiol Biomarkers Prev 2016;25:144",
          "10.1158/1055-9965.EPI-15-0724", "validated_equation",
          ["Age", "AFP", "AFPL3", "DCP"], _galad, horizon=1,
          exclude=["HCC"]),

    _spec("Metabolic_Syndrome", "Metabolic syndrome (JIS 2009 criteria)",
          "IDF/NCEP harmonized (JIS)", "Alberti KG, et al. Circulation 2009;120:1640",
          "10.1161/CIRCULATIONAHA.109.192644", 'validated_criteria',
          ["Waist", "Triglycerides", "HDL", "FBS", 'Systolic_BP'],
          _metabolic_syndrome, exclude=["Metabolic_Syndrome"]),
    _spec("Insulin_Resistance_TyG", "Insulin resistance indices (HOMA-IR/TyG)",
          "HOMA-IR / QUICKI / TyG", "Matthews 1985; Simental-Mendia 2008",
          "-", 'biomarker_index',
          ["FBS"], _insulin_indices),
    _spec("Primary_Aldosteronism_ARR", "PA screening (aldosterone-renin ratio)",
          "ARR (Endocrine Society 2016)", 'Funder JW, et al. JCEM 2016;101:1889',
          "10.1210/jc.2015-4061", 'validated_screen',
          ["Aldosterone"], _arr_screen),
    _spec("Hemochromatosis_TSAT", "Iron overload / hemochromatosis rule",
          "EASL phenotypic rule", "EASL CPG 2022; Adam 2010",
          "-", "validated_criteria",
          ["TSAT", "Ferritin"], _hemochromatosis),

    _spec('Lung_Cancer_PLCOm2012', "6-y lung cancer risk (PLCOm2012)",
          "PLCOm2012", "Tammemagi MC, et al. N Engl J Med 2013;368:728",
          "10.1056/NEJMoa1211776", "validated_equation",
          ["Age", 'BMI', "Cigarettes_Per_Day", 'Smoking_Years'],
          _plcom2012, horizon=6, gate=_lung_gate,
          exclude=['Lung_Cancer']),
    _spec("Colorectal_Cancer_APCS", "Advanced colorectal neoplasia triage (APCS)",
          "APCS", "Yeoh KG, et al. Gut 2011;60:1236",
          "10.1136/gut.2010.231170", "validated_score",
          ["Age", "FamilyHistory_CRC", 'Smoking'], _apcs, horizon=3,
          exclude=["Colorectal_Cancer"]),
    _spec("Ovarian_Cancer_ROMA", "Epithelial ovarian cancer risk (ROMA)",
          "ROMA", "Moore RG, et al. Gynecol Oncol 2009;112(1):40-46",
          "10.1016/j.ygyno.2008.08.031", "validated_equation",
          ["HE4", "CA125"], _roma, horizon=0.1,
          gate=_roma_gate, exclude=["Ovarian_Cancer"]),
    _spec("Prostate_Cancer_PHI", "Prostate cancer biopsy probability (phi)",
          "Prostate Health Index", "Catalona WJ, et al. JAMA 2011;305:1662; Loeb 2015",
          "10.1001/jama.2011.694", "biomarker_index",
          ["PHI"], _phi_bands, gate=_phi_gate,
          exclude=["Prostate_Cancer"]),

    _spec("OSA_STOPBANG", 'OSA risk (STOP-BANG)',
          "STOP-BANG", "Chung F, et al. Anesthesiology 2008;108:812",
          "10.1097/ALN.0b013e31816d7796", "validated_score",
          ["Snoring_Loud", 'Daytime_Tiredness', "Observed_Apnea",
           'NeckCircumference', 'BMI'],
          _stop_bang, exclude=["OSA"]),
    _spec("OSA_NoSAS", "OSA risk (NoSAS)",
          "NoSAS", "Marti-Soler H, et al. Lancet Respir Med 2016;4:150",
          "10.1016/S2213-2600(15)00498-3", "validated_score",
          ['NeckCircumference', "BMI", "Snoring_Loud", "Age"],
          _nosas, exclude=["OSA"]),
    _spec("OSA_Berlin", "OSA risk (Berlin questionnaire)",
          "Berlin", "Netzer NC, et al. Ann Intern Med 1999;131:485",
          '10.7326/0003-4819-131-7-199910050-00002', "validated_score",
          ["Snoring_Loud", "Daytime_Tiredness", "BMI"], _berlin,
          exclude=["OSA"]),
    _spec("COPD_BODE", "COPD 4-y survival (BODE)",
          "BODE index", 'Celli BR, et al. N Engl J Med 2004;350:1005',
          "10.1056/NEJMoa021322", "validated_score",
          ["BMI", 'FEV1_PercentPredicted', "SixMinuteWalkDistance",
           "mMRC_Score"],
          _bode, horizon=4, gate=_bode_gate),
    _spec("COPD_GOLD_ABE", "COPD assessment (GOLD 2023 ABE)",
          "GOLD ABE", 'GOLD 2023 report', "-", 'validated_criteria',
          ["CAT_Score", "mMRC_Score", "Exacerbations_Past_Year"],
          _gold_abe, gate=_bode_gate),
    _spec("Asthma_ACT", "Asthma control (ACT)",
          "ACT", "Nathan RA, et al. J Allergy Clin Immunol 2004;113:59",
          '10.1016/j.jaci.2003.09.008', "validated_score",
          ["ACT_Q1"], _act, horizon=0.1),

    _spec("Osteoporosis_OSTA", "Osteoporosis screen (OSTA)",
          "OSTA", "Koh LK, et al. Osteoporos Int 2001;12:811",
          "10.1007/s001980170061", 'validated_equation',
          ["Age", "WeightKg"], _osta,
          gate=_osteo_gate, exclude=["Osteoporosis"]),
    _spec("Osteoporosis_ORAI", 'Osteoporosis screen (ORAI)',
          "ORAI", "Cadarette SM, et al. CMAJ 2000;163:1449",
          "-", 'validated_score',
          ['Age', "WeightKg"], _orai,
          gate=_osteo_gate, exclude=["Osteoporosis"]),
    _spec('Sarcopenia_SARCF', "Sarcopenia screen (SARC-F)",
          "SARC-F", "Malmstrom TK, Morley JE. JAMDA 2013;14:487",
          "10.1016/j.jamda.2013.01.021", 'validated_score',
          ["SARC_Q1"], _sarcf, horizon=3, exclude=["Sarcopenia"]),
    _spec('Frailty_Fried', "Frailty phenotype (Fried)",
          "Fried phenotype", "Fried LP, et al. J Gerontol 2001;56:M146",
          "10.1093/gerona/56.3.M146", "validated_criteria",
          ["Unintentional_WeightLoss_10lbs"], _fried, horizon=3,
          exclude=["Frailty"]),
    _spec("Fall_Risk_Morse", "Fall risk (Morse Fall Scale)",
          "Morse Fall Scale", "Morse JM. Scale 1985-1994", "-",
          "validated_score",
          ['Fall_History_Recent'], _morse_fall, horizon=0.25),
    _spec("Malnutrition_MUST", "Malnutrition risk (MUST)",
          "MUST (BAPEN)", "Elia M. BAPEN 2003", "-",
          'validated_score',
          ['BMI', 'Weight_Loss_Percent'], _must, horizon=1,
          exclude=["Malnutrition"]),

    _spec("Dementia_CAIDE", "20-y dementia risk (CAIDE)",
          "CAIDE", "Kivipelto M, et al. Lancet Neurol 2006;5:735",
          "10.1016/S1474-4422(06)70537-3", 'validated_score',
          ['Age', "Systolic_BP", "BMI", "TotalCholesterol",
           'PhysicalActivity', 'Education_Years'],
          _caide, horizon=20, gate=None, exclude=["Dementia"]),
    _spec("Depression_PHQ9", "Depression severity (PHQ-9)",
          'PHQ-9', "Kroenke K, et al. J Gen Intern Med 2001;16:606",
          "10.1046/j.1525-1497.2001.016009606.x", "validated_score",
          ["PHQ9_Q1"], _phq9, exclude=["Depression"]),
    _spec("Anxiety_GAD7", "Anxiety severity (GAD-7)",
          'GAD-7', "Spitzer RL, et al. Arch Intern Med 2006;166:1092",
          "10.1001/archinte.166.10.1092", "validated_score",
          ['GAD7_Q1'], _gad7, exclude=["Anxiety"]),
    _spec("Alcohol_AUDIT_C", 'Hazardous alcohol use (AUDIT-C)',
          "AUDIT-C", 'Bush K, et al. Arch Intern Med 1998;158:1789',
          "10.1001/archinte.158.16.1789", "validated_score",
          ["AUDIT_Q1_Frequency", "AUDIT_Q2_Quantity", "AUDIT_Q3_Binge"],
          _auditc, exclude=["Alcohol_Use_Disorder"]),
    _spec("Alcohol_CAGE", "Alcohol use disorder (CAGE)",
          "CAGE", "Ewing JA. JAMA 1984;252:1905",
          "10.1001/jama.1984.03350140043019", "validated_score",
          ["CAGE_Q1"], _cage, exclude=["Alcohol_Use_Disorder"]),
    _spec("Nicotine_Fagerstrom", "Nicotine dependence (Fagerstrom)",
          "FTND", 'Heatherton TF, et al. Br J Addict 1991;86:1119',
          "10.1111/j.1360-0443.1991.tb01879.x", "validated_score",
          ["Cigarettes_Per_Day", "Time_To_First_Cigarette_Min"], _fagerstrom),

    _spec("DIC_ISTH", "Overt DIC (ISTH)",
          'ISTH overt DIC score', 'Taylor FB Jr, et al. Thromb Haemost 2001;86:1327',
          '10.1055/s-0037-1616066', 'validated_score',
          ["Platelets", 'Fibrinogen', "DDimer", "PT"], _isth_dic,
          exclude=['DIC']),
    _spec("Iron_Deficiency_Anemia", "IDA persistence/recurrence (heuristic)",
          'Internal heuristic', 'HEMOGLYPH internal heuristic', '-',
          "heuristic",
          ["Ferritin", "Hb", "SerumIron"], _heuristic_ida_recurrence,
          horizon=2, exclude=["Iron_Deficiency_Anemia"]),
    _spec('Anemia_Phenotype', "Anemia phenotype classification (WHO/BCSH)",
          "MCV/iron guideline logic", "WHO Hb criteria; BCSH guidelines", "-",
          "validated_criteria",
          ["Hb"], _anemia_classifier, horizon=0.5, exclude=["Anemia"]),
    _spec('Primary_Hypothyroidism', "Subclinical hypothyroidism progression (heuristic)",
          "Internal heuristic + anti-TPO (Whickham/Vanderpump)",
          "Vanderpump MPJ, et al. Clin Endocrinol 1995;43:55", "-",
          "heuristic",
          ["TSH", 'Anti_TPO'], _heuristic_hypothyroid, horizon=2,
          exclude=["Primary_Hypothyroidism"]),
    _spec('Gout', "Gout flare risk (heuristic)",
          'Internal heuristic + Framingham SUA gradient',
          "Abbott RD, et al. J Clin Epidemiol 1988;41:237", "-",
          "heuristic",
          ["Uric_Acid", "Creatinine"], _heuristic_gout, horizon=2,
          exclude=["Gout"]),

    _spec("CKD_KFRE_8Var", "Kidney failure 5y risk (KFRE 8-variable model)",
          "Tangri KFRE 8-Variable", "Tangri N, et al. JAMA 2011;305:1553-1559",
          "10.1001/jama.2011.451", "validated_equation",
          ['Age', "eGFR", "UACR", "Albumin", "Phosphate", "Bicarbonate", "Calcium"],
          _kfre_8var, horizon=5, exclude=["Chronic_Kidney_Disease"]),
    _spec('Diabetes_QDiabetes_10Y', "10-y Type 2 Diabetes risk (QDiabetes 2014)",
          "QDiabetes-style estimate (INTERNAL APPROXIMATION)", "Hippisley-Cox J, Coupland C. BMJ 2014;349:g7229",
          "10.1136/bmj.g7229", 'heuristic',
          ["Age", "BMI", "FBS", 'HbA1c', "Smoking"],
          _qdiabetes_10y, horizon=10, exclude=["Diabetes_Mellitus"]),

    _spec("Diabetes_Cambridge_Risk",
          "Probability of undiagnosed Type 2 Diabetes (Cambridge Risk Score)",
          "Cambridge Diabetes Risk Score",
          'Griffin SJ, et al. Diabetes Metab Res Rev 2000;16:164-171',
          "10.1002/1520-7560(200005/06)16:3<164::AID-DMRR103>3.0.CO;2-R",
          "validated_screen",
          ['Age', "BMI"],
          _cambridge_diabetes, horizon=0, exclude=['Diabetes_Mellitus']),
    _spec("Diabetes_AUSDRISK_5Y", "5-y Type 2 Diabetes risk (AUSDRISK Tool)",
          "AUSDRISK Assessment", 'Chen L, et al. Med J Aust 2010;192:197-202',
          "10.5694/j.1326-5377.2010.tb03478.x", "validated_score",
          ["Age", "Waist"],
          _ausdrisk_emtiaz, horizon=5, exclude=["Diabetes_Mellitus"]),
    _spec("NASH_FAST_Score", "NASH with significant fibrosis (FAST Score)",
          "FAST Score", "Newsome PN, et al. Lancet Gastroenterol Hepatol 2020;5:362-373",
          "10.1016/S2468-1253(19)30383-8", 'validated_equation',
          ["AST", "LiverStiffness_kPa", "CAP_dB_m"],
          _fast_emtiaz_nash, horizon=5, exclude=None),
    _spec("Cirrhosis_PALBI_Grade", "Portal hypertension & liver function (PALBI)",
          'PALBI Grade', "Roayaie S, et al. Hepatology 2015;62:1726-1734",
          '10.1002/hep.27988', "staging_system",
          ["Bilirubin", "Albumin", "Platelets"],
          _palbi_grade, horizon=3, exclude=None),
    _spec("Alcoholic_Hepatitis_GAHS", "Alcoholic hepatitis severity (Glasgow GAHS)",
          "Glasgow Alcoholic Hepatitis Score", "Forrest EH, et al. Gut 2005;54:1174-1179",
          "10.1136/gut.2004.050781", "validated_score",
          ["Age", "WBC", "BUN", 'INR', "Bilirubin"],
          _gahs_alcoholic_hepatitis, horizon=0.08, exclude=None),
    _spec("Pneumonia_PSI_PORT", "Pneumonia Severity Index 30d mortality (PSI/PORT)",
          'PSI / PORT Score', "Fine MJ, et al. N Engl J Med 1997;336:243-250",
          "10.1056/NEJM199701233360402", 'validated_score',
          ["Age", "BUN", "Sodium", "Glucose", "Hematocrit"],
          _psi_port_pneumonia, horizon=0.08, exclude=None),
    _spec('Pneumonia_SMART_COP', "ICU / mechanical ventilation in pneumonia (SMART-COP)",
          "SMART-COP Score", "Charles PG, et al. Clin Infect Dis 2008;47:375-384",
          '10.1086/589754', "validated_score",
          ['Age', 'Systolic_BP', "Albumin"],
          _smart_cop_pneumonia, horizon=0.08, exclude=None),
    _spec("Acuity_NEWS2_Score", "Clinical deterioration early warning (NEWS2 UK 2017)",
          'NEWS2 Score', "Royal College of Physicians. NEWS2 2017",
          "ISBN:978-1-86016-682-2", "validated_score",
          ["Systolic_BP"],
          _news2_emtiaz, horizon=0.08, exclude=None),


    _spec('CVD_PREVENT_10Y', "10-y Total CVD risk (ACC/AHA PREVENT 2023)",
          "PREVENT-style CVD estimate (INTERNAL APPROXIMATION)", "Khan SS, et al. Circulation 2024;149:430-449",
          '10.1161/CIRCULATIONAHA.123.067620', 'heuristic',
          ['Age', "Systolic_BP", "TotalCholesterol", 'HDL', "eGFR", "UACR", "HbA1c"],
          _prevent_cvd_10y, horizon=10, exclude=["Cardiovascular_Risk"]),
    _spec('Heart_Failure_PREVENT_10Y', "10-y Heart Failure risk (ACC/AHA PREVENT 2023)",
          "PREVENT-style HF estimate (INTERNAL APPROXIMATION)", "Khan SS, et al. Circulation 2024;149:430-449",
          "10.1161/CIRCULATIONAHA.123.067620", "heuristic",
          ["Age", "BMI", "Systolic_BP", 'eGFR', "UACR", "HbA1c"],
          _prevent_hf_10y, horizon=10, exclude=None),
    _spec("Diabetes_UKPDS_CHD", "10-y CHD risk in Type 2 Diabetes (UKPDS 2.0)",
          "UKPDS Risk Engine 2.0", "Stevens RJ, et al. Clin Sci 2001;101:671-679",
          '10.1042/cs1010671', "validated_equation",
          ["Age", "HbA1c", "Systolic_BP", "TotalCholesterol", 'HDL'],
          _ukpds_chd_risk, horizon=10, exclude=None),
    _spec("Diabetes_ADVANCE_CVD", "4-y Major CVD risk in Type 2 Diabetes (ADVANCE)",
          "ADVANCE-style CVD estimate (INTERNAL APPROXIMATION)", "Kengne AP, et al. Diabetologia 2011;54:1006-1013",
          "10.1007/s00125-010-2029-1", "heuristic",
          ['Age', "HbA1c", "Systolic_BP", 'UACR'],
          _advance_cvd_risk, horizon=4, exclude=None),
    _spec("CVD_Recurrent_SMART", "10-y recurrent vascular event in ASCVD (SMART Score)",
          'SMART2 Risk Score', "Hageman SHJ, et al. Eur Heart J 2022;43:1715-1727",
          "10.1093/eurheartj/ehac056", "validated_equation",
          ["Age", "Systolic_BP", "TotalCholesterol", "HDL", "eGFR"],
          _smart_recurrent_cvd, horizon=10, exclude=None),
    _spec("HFpEF_HFA_PEFF_Score", 'Diagnostic probability of HFpEF (HFA-PEFF Stepwise)',
          "HFA-PEFF Diagnostic Score", "Pieske B, et al. Eur Heart J 2019;40:3297-3317",
          "10.1093/eurheartj/ehz641", "validated_criteria",
          [],
          _hfa_peff_emtiaz, horizon=1, exclude=None),
    _spec('PE_Bova_Score', "Intermediate-risk PE 30d complications (Bova Score)",
          "Bova PE Severity Score", 'Bova C, et al. Circulation 2014;130:1290-1297',
          '10.1161/CIRCULATIONAHA.114.009862', 'validated_score',
          ["Systolic_BP", "Heart_Rate", "Troponin_I"],
          _bova_pe_emtiaz, horizon=0.08, exclude=None),
    _spec("VTE_Khorana_Score", "Cancer-associated VTE 6m risk (Khorana Score)",
          "Khorana VTE Score", 'Khorana AA, et al. Blood 2008;111:4902-4907',
          "10.1182/blood-2007-10-116327", "validated_score",
          ["Platelets", 'Hb', "WBC", "BMI"],
          _khorana_vte_emtiaz, horizon=0.5, exclude=None,
          gate=_khorana_gate),
    _spec("Diabetes_GDRS_5Y", '5-y Type 2 Diabetes risk (German Diabetes Risk Score)',
          'German Diabetes Risk Score (GDRS)', "Schulze MB, et al. Diabetes Care 2007;30:510-515",
          '10.2337/dc06-2089', "validated_equation",
          ["Age", "Waist", "HeightCm"],
          _german_diabetes_emtiaz, horizon=5, exclude=["Diabetes_Mellitus"]),
    _spec('Metabolic_VAI_Index', "Visceral adiposity dysfunction index (VAI)",
          "Visceral Adiposity Index (VAI)", "Amato MC, et al. Diabetes Care 2010;33:920-922",
          "10.2337/dc09-1825", "validated_equation",
          ["Waist", "BMI", "Triglycerides", 'HDL'],
          _visceral_adiposity_index, horizon=5, exclude=None),
    _spec("Metabolic_LAP_Index", 'Lipid Accumulation Product (LAP Index)',
          "Lipid Accumulation Product (LAP)", 'Kahn HS. BMC Cardiovasc Disord 2005;5:26',
          "10.1186/1471-2261-5-26", "validated_equation",
          ["Waist", "Triglycerides"],
          _lipid_accumulation_product, horizon=5, exclude=None,
          gate=_metabolic_risk_gate),
    _spec('Nephrology_IgA_Prediction_Tool', '5-y IgA nephropathy progression risk (International Tool)',
          "IgA Nephropathy risk estimate (INTERNAL APPROXIMATION)", 'Barbour SJ, et al. JAMA Intern Med 2019;179:942-952',
          '10.1001/jamainternmed.2019.0600', "heuristic",
          ["eGFR", "MAP", "Age"],
          _iga_nephropathy_tool, horizon=5, exclude=None),
    _spec("Oncology_TLS_Cairo_Bishop", "Tumor Lysis Syndrome Staging (Cairo-Bishop)",
          "Cairo-Bishop TLS Staging", "Cairo MS, Bishop M. Br J Haematol 2004;127:3-11",
          "10.1111/j.1365-2141.2004.05094.x", 'staging_system',
          ["UricAcid", "Potassium", "Phosphate", "Calcium"],
          _cairo_bishop_tls_staging, horizon=0.08, exclude=None),


    _spec("ICU_APACHE_II", "ICU severity of disease mortality (APACHE II)",
          'APACHE II Score', "Knaus WA, et al. Crit Care Med 1985;13:818-829",
          '10.1097/00003246-198510000-00009', "validated_score",
          ["Age", "GCS", 'Sodium', "Potassium", "Creatinine", "Hematocrit", "WBC"],
          _apache_ii_emtiaz, horizon=0.08, exclude=None),
    _spec('ICU_SAPS_II', "Simplified Acute Physiology Score II (SAPS II)",
          "SAPS II Score", "Le Gall JR, et al. JAMA 1993;270:2957-2963",
          "10.1001/jama.1993.03510240069035", "validated_score",
          ["Age", "BUN", "GCS", 'Potassium', "Sodium", "Bilirubin"],
          _saps_ii_emtiaz, horizon=0.08, exclude=None),
    _spec("Myeloma_R2_ISS", "Multiple Myeloma staging & prognosis (R2-ISS 2022)",
          "R2-ISS Staging (IMWG 2022)", "D'Agostino M, et al. J Clin Oncol 2022;40:3406-3418",
          "10.1200/JCO.21.02614", "staging_system",
          ["LDH"],
          _r2_iss_myeloma, horizon=5, exclude=None),
    _spec("Lymphoma_DLBCL_IPI", "DLBCL 5-year survival prognosis (IPI)",
          "International Prognostic Index (IPI)", "The International NHL Prognostic Factors Project. N Engl J Med 1993;329:987-994",
          "10.1056/NEJM199309303291402", 'validated_score',
          ["Age", 'LDH'],
          _ipi_dlbc_lymphoma, horizon=5, exclude=None),
    _spec("Leukemia_CLL_IPI", 'Chronic Lymphocytic Leukemia prognosis (CLL-IPI)',
          "CLL-IPI (Lancet Oncol 2016)", "International CLL-IPI Working Group. Lancet Oncol 2016;17:779-790",
          "10.1016/S1470-2045(16)30029-8", "validated_score",
          ['Age', "Beta2Microglobulin"],
          _cll_ipi_emtiaz, horizon=5, exclude=None),
    _spec("GIBleed_AIMS65", "Acute upper GI bleeding mortality (AIMS65)",
          "AIMS65 Score", 'Saltzman JR, et al. Gastrointest Endosc 2011;74:1215-1224',
          "10.1016/j.gie.2011.08.043", "validated_score",
          ['Albumin', "INR", "Systolic_BP", "Age"],
          _aims65_emtiaz, horizon=0.08, exclude=None),
    _spec("Liver_Failure_Kings_College", "Acute liver failure transplant triage (King's College)",
          "King's College Criteria (ALF)", "O'Grady JG, et al. Gastroenterology 1989;97:439-445",
          "10.1016/0016-5085(89)90081-4", "staging_system",
          ["INR", "Creatinine", "TotalBilirubin"],
          _kings_college_alf, horizon=0.08, exclude=None),


]


def predict_chronic_disease_risks(inputs, derived=None, patient=None, diagnoses=None,
                                  kinds=None, only_keys=None):
    # Cryptographic License Lock
    try:
        import license_engine
        st = license_engine.get_current_license_status()
        if not st.get("valid"):
            return []
    except Exception:
        pass

    dataset = {**(inputs or {}), **(derived or {})}
    diagnoses = diagnoses or []

    # 1. Robust conversion of patient object/dataclass/dict
    if hasattr(patient, "to_dict") and callable(patient.to_dict):
        patient_dict = patient.to_dict()
    elif is_dataclass(patient):
        patient_dict = asdict(patient)
    elif isinstance(patient, Mapping):
        patient_dict = dict(patient)
    elif patient is not None:
        patient_dict = {k: getattr(patient, k) for k in dir(patient) if not k.startswith("_") and not callable(getattr(patient, k))}
    else:
        patient_dict = {}

    # 2. Extract sex/gender accurately from patient context or dict
    gender = None
    sex_assumed = False
    if hasattr(patient, "normalized_jensiat") and callable(patient.normalized_jensiat):
        gender = patient.normalized_jensiat()
    elif hasattr(patient, "sex_at_birth") and getattr(patient, "sex_at_birth"):
        s = str(getattr(patient, "sex_at_birth")).lower().strip()
        gender = "female" if s.startswith("f") or s in ("2", "زن") else "male"
    elif isinstance(patient_dict, dict):
        for k in ("sex_at_birth", "Sex", "sex", "Gender", "gender"):
            val = patient_dict.get(k)
            if val is not None:
                s = str(val).lower().strip()
                if s in (1, "1", 'male', "m", "مرد", "true"):
                    gender = "male"
                    break
                elif s in (0, "0", 'female', "f", "زن", "false"):
                    gender = "female"
                    break
    if gender is None:
        gender = "female"
        sex_assumed = True

    # 3. Patient waist cutoffs and country defaults
    if "WaistCutoff_M" not in patient_dict:
        patient_dict["WaistCutoff_M"] = 94.0
    if "WaistCutoff_F" not in patient_dict:
        patient_dict["WaistCutoff_F"] = 80.0
    if "Education_Level" not in patient_dict:
        patient_dict["Education_Level"] = 0
    if "Country" not in patient_dict and "country" in patient_dict:
        patient_dict["Country"] = patient_dict["country"]

    results = []
    for spec in MODELS:
        if kinds is not None and spec.get("kind") not in kinds:
            continue
        if only_keys is not None and spec["diseaseKey"] not in only_keys:
            continue
        try:
            results.append(arzyabi_model(spec, dataset, patient_dict,
                                          diagnoses, gender,
                                          sex_assumed=sex_assumed))
        except Exception as exc:
            results.append({
                "diseaseKey": spec["diseaseKey"],
                "nameEn": spec["nameEn"],
                "modelName": spec.get("modelName"),
                'status': 'Error',
                "error": "%s: %s" % (type(exc).__name__, exc),
                "requiredFeatures": spec.get('requiredFeatures', []),
                "missingFeatures": spec.get('requiredFeatures', []),
            })
    return results

def fehrest_model_ha():
    cat = []
    for spec in MODELS:
        try:
            if not isinstance(spec, dict):
                continue
            fn = spec.get("fn")
            cat.append({
                "diseaseKey": str(spec.get("diseaseKey") or ""),
                "nameEn": str(spec.get("nameEn") or ''),
                "modelName": str(spec.get('modelName') or ""),
                "kind": str(spec.get("kind") or "validated_equation"),
                "horizonYears": float(spec.get("horizonYears") or 0),
                'requiredFeatures': [str(x) for x in (spec.get("requiredFeatures") or [])],
                "optionalFeatures": [str(x) for x in (spec.get("optionalFeatures") or [])],
                "weights": {str(k): float(v) for k, v in
                            (getattr(fn, "risk_factor_weights", {}) or {}).items()
                            if isinstance(v, (int, float))},
                "baseIncidence": float(getattr(fn, "base_incidence", 0.0) or 0.0),
                'citation': str(spec.get("citation") or ''),
                "doi": str(spec.get("doi") or ""),
                "pmid": str(spec.get('pmid') or ''),
                "articleTitle": str(spec.get("article_title") or ""),
                'journal': str(spec.get("journal") or ''),
                "publicationYear": str(spec.get("publication_year") or spec.get("year") or ""),
                "referenceUrl": str(spec.get("reference_url") or ""),
            })
        except Exception:
            continue
    return cat



predict_2year_risks = predict_chronic_disease_risks
