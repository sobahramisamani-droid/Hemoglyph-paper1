"""Shared guideline laboratory-signature table for the structured error audit (SAP amendment 5)."""

def V(v, k):
    x = v.get(k); return None if x is None else float(x)


def egfr(cr, age, sex):  # CKD-EPI 2021, race-free
    if cr is None or cr <= 0: return None
    k, al = (0.7, -0.241) if sex == "female" else (0.9, -0.302)
    f = 1.012 if sex == "female" else 1.0
    return 142 * min(cr / k, 1) ** al * max(cr / k, 1) ** -1.2 * 0.9938 ** age * f


# group -> function(vals, age, sex) -> True if the panel carries the guideline signature of the condition
SIG = {
    "acute_kidney_injury": lambda v, ag, sx: (V(v, "creatinine") or 0) > (1.1 if sx == "female" else 1.3),
    "chronic_kidney_disease": lambda v, ag, sx: (egfr(V(v, "creatinine"), ag, sx) or 999) < 60,
    "renal_impairment": lambda v, ag, sx: (V(v, "creatinine") or 0) > (1.1 if sx == "female" else 1.3),
    "diabetes": lambda v, ag, sx: (V(v, "glucose") or 0) >= 200 or (V(v, "hemoglobin_a1c") or 0) >= 6.5,
    "hyperglycemia": lambda v, ag, sx: (V(v, "glucose") or 0) >= 200,
    "diabetic_ketoacidosis": lambda v, ag, sx: (V(v, "glucose") or 0) > 250 and (V(v, "bicarbonate") or 99) < 18,
    "hypoglycemia": lambda v, ag, sx: (V(v, "glucose") or 999) < 70,
    "hypokalemia": lambda v, ag, sx: (V(v, "potassium") or 9) < 3.5,
    "hyperkalemia": lambda v, ag, sx: (V(v, "potassium") or 0) > 5.0,
    "hyponatremia": lambda v, ag, sx: (V(v, "sodium") or 999) < 135,
    "hypernatremia": lambda v, ag, sx: (V(v, "sodium") or 0) > 145,
    "hypomagnesemia": lambda v, ag, sx: (V(v, "magnesium") or 9) < 1.7,
    "hypocalcemia": lambda v, ag, sx: (V(v, "calcium_total") or 99) < 8.5 or (V(v, "calcium_ionized") or 99) < 1.12,
    "hypercalcemia": lambda v, ag, sx: (V(v, "calcium_total") or 0) > 10.5 or (V(v, "calcium_ionized") or 0) > 1.32,
    "hypophosphatemia": lambda v, ag, sx: (V(v, "phosphate") or 9) < 2.5,
    "metabolic_acidosis": lambda v, ag, sx: (V(v, "bicarbonate") or 99) < 22,
    "lactic_acidosis": lambda v, ag, sx: (V(v, "lactate") or 0) > 2.0,
    "anemia": lambda v, ag, sx: (V(v, "hemoglobin") or 99) < (12 if sx == "female" else 13),
    "thrombocytopenia": lambda v, ag, sx: (V(v, "platelet_count") or 999) < 150,
    "leukocytosis": lambda v, ag, sx: (V(v, "white_blood_cell_count") or 0) > 11,
    "sepsis": lambda v, ag, sx: (V(v, "white_blood_cell_count") or 8) > 12 or (V(v, "white_blood_cell_count") or 8) < 4
                                or (V(v, "lactate") or 0) > 2 or (V(v, "procalcitonin") or 0) > 0.5 or (V(v, "band_neutrophils_percent") or 0) > 10,
    "hypothyroidism": lambda v, ag, sx: (V(v, "thyroid_stimulating_hormone") or 0) > 4.5,
    "cirrhosis_liver_failure": lambda v, ag, sx: ((V(v, "platelet_count") or 999) < 150 and ((V(v, "albumin") or 9) < 3.5 or (V(v, "international_normalized_ratio") or 0) > 1.3
                                                  or (V(v, "total_bilirubin") or 0) > 1.2)) or (V(v, "ammonia") or 0) > 60,
    "acute_pancreatitis": lambda v, ag, sx: (V(v, "lipase") or 0) > 180 or (V(v, "amylase") or 0) > 300,
    "acute_myocardial_infarction": lambda v, ag, sx: (V(v, "troponin_i") or 0) > 0.04 or (V(v, "troponin_t") or 0) > 0.014,
    "heart_failure": lambda v, ag, sx: (V(v, "b_type_natriuretic_peptide") or 0) > 100,
    "rhabdomyolysis": lambda v, ag, sx: (V(v, "creatine_kinase_total") or 0) > 1000,
    "coagulopathy": lambda v, ag, sx: (V(v, "international_normalized_ratio") or 0) > 1.5 or (V(v, "platelet_count") or 999) < 100
                                      or (V(v, "fibrinogen") or 999) < 150,
    "malnutrition": lambda v, ag, sx: (V(v, "albumin") or 9) < 3.0,
    "gi_bleeding": lambda v, ag, sx: (V(v, "hemoglobin") or 99) < 10 or ((V(v, "blood_urea_nitrogen") or 0) / max(V(v, "creatinine") or 1, 0.1)) > 30,
    "alcohol_withdrawal": lambda v, ag, sx: ((V(v, "aspartate_aminotransferase") or 0) > 40 and (V(v, "aspartate_aminotransferase") or 0) > 2 * (V(v, "alanine_aminotransferase") or 1))
                                             or (V(v, "mean_corpuscular_volume") or 0) > 100,
}
