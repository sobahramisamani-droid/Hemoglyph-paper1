"""Post-OCR self-consistency solver for laboratory reports.

Purely structural (no dataset, no model): a laboratory panel carries its own
redundancy - red-cell indices are arithmetic functions of Hb/Hct/RBC, the
leukocyte differential sums to 100 %, direct bilirubin cannot exceed total,
Friedewald ties the lipid panel together, urea = BUN x 2.14, and every analyte
has a physiological ceiling. An OCR digit error (dropped decimal point, 1<->7,
0<->8, 5<->6, an extra zero) almost always breaks one of these identities.

Given the mapped OCR records this module

1. converts each value to the analyte's canonical unit,
2. checks hard physiological plausibility,
3. checks the flag printed on the report (H / L / N) against the value and
   the printed reference interval,
4. evaluates every cross-field identity that is computable from the panel,
5. for every failed identity searches single-field repairs (decimal shifts,
   classic glyph confusions) and keeps a repair only if it makes *all*
   identities that involve that field pass - the field that can be repaired
   that way is named as the probable culprit and the repaired value is
   offered as `suggested_value`,
6. lowers the confidence of culprits / unresolved participants, raises it a
   little for values that an independent identity corroborates, and reports
   a summary block for the UI.

Nothing here changes a value silently: suggestions are surfaced for the
human to accept; `requires_confirmation` is forced on for every suspect.
"""
from __future__ import annotations

import itertools
import math

import ocr_confidence as _conf
from typing import Any, Callable, Iterable, Mapping, Optional

__all__ = ["validate_results", "canonical_value", "HARD_LIMITS", "ConsistencyReport"]

# --------------------------------------------------------------------------- #
# Canonical units and conversions for the analytes the identities use.
# Values are (canonical_unit, {unit_alias: factor_to_canonical}).
# --------------------------------------------------------------------------- #
_CONV: dict[str, tuple[str, dict[str, float]]] = {
    "hemoglobin": ("g/dL", {"g/dl": 1.0, "g/l": 0.1, "mmol/l": 1.6114, "g%": 1.0, "gm/dl": 1.0, "gr/dl": 1.0}),
    "hematocrit": ("%", {"%": 1.0, "l/l": 100.0, "fraction": 100.0, "ratio": 100.0}),
    "red_blood_cell_count": ("10^6/uL", {"10^6/ul": 1.0, "10*6/ul": 1.0, "10^12/l": 1.0, "10*12/l": 1.0, "m/ul": 1.0, "mil/ul": 1.0, "x10^6/ul": 1.0, "x10^12/l": 1.0, "/ul": 1e-6, "/pl": 1.0}),
    "white_blood_cell_count": ("10^9/L", {"10^9/l": 1.0, "10*9/l": 1.0, "10^3/ul": 1.0, "10*3/ul": 1.0, "k/ul": 1.0, "x10^3/ul": 1.0, "x10^9/l": 1.0, "/ul": 1e-3, "/mm3": 1e-3, "cells/ul": 1e-3}),
    "platelets": ("10^9/L", {"10^9/l": 1.0, "10*9/l": 1.0, "10^3/ul": 1.0, "10*3/ul": 1.0, "k/ul": 1.0, "x10^3/ul": 1.0, "x10^9/l": 1.0, "/ul": 1e-3, "/mm3": 1e-3}),
    "mean_corpuscular_volume": ("fL", {"fl": 1.0, "um3": 1.0, "µm3": 1.0}),
    "mean_corpuscular_hemoglobin": ("pg", {"pg": 1.0}),
    "mean_corpuscular_hemoglobin_concentration": ("g/dL", {"g/dl": 1.0, "g/l": 0.1, "%": 1.0}),
    "neutrophils_percent": ("%", {"%": 1.0}), "lymphocytes_percent": ("%", {"%": 1.0}),
    "monocytes_percent": ("%", {"%": 1.0}), "eosinophils_percent": ("%", {"%": 1.0}),
    "basophils_percent": ("%", {"%": 1.0}),
    "neutrophil_count_absolute": ("10^9/L", {"10^9/l": 1.0, "10*9/l": 1.0, "10^3/ul": 1.0, "10*3/ul": 1.0, "k/ul": 1.0, "/ul": 1e-3}),
    "lymphocyte_count_absolute": ("10^9/L", {"10^9/l": 1.0, "10*9/l": 1.0, "10^3/ul": 1.0, "10*3/ul": 1.0, "k/ul": 1.0, "/ul": 1e-3}),
    "glucose": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 18.016, "g/l": 100.0}),
    "fasting_plasma_glucose": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 18.016, "g/l": 100.0}),
    "hemoglobin_a1c": ("%", {"%": 1.0, "mmol/mol": 0.0915}),  # IFCC -> NGSP approx (0.0915x + 2.15) handled below
    "creatinine": ("mg/dL", {"mg/dl": 1.0, "umol/l": 1 / 88.42, "µmol/l": 1 / 88.42, "mg/l": 0.1}),
    "blood_urea_nitrogen": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 2.801}),
    "urea": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 6.006, "g/l": 100.0}),
    "sodium": ("mmol/L", {"mmol/l": 1.0, "meq/l": 1.0}), "potassium": ("mmol/L", {"mmol/l": 1.0, "meq/l": 1.0}),
    "chloride": ("mmol/L", {"mmol/l": 1.0, "meq/l": 1.0}), "bicarbonate": ("mmol/L", {"mmol/l": 1.0, "meq/l": 1.0}),
    "calcium_total": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 4.008, "meq/l": 2.004}),
    "phosphate": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 3.097}),
    "magnesium": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 2.431, "meq/l": 1.215}),
    "albumin": ("g/dL", {"g/dl": 1.0, "g/l": 0.1}), "total_protein": ("g/dL", {"g/dl": 1.0, "g/l": 0.1}),
    "globulin": ("g/dL", {"g/dl": 1.0, "g/l": 0.1}),
    "albumin_to_globulin_ratio": ("ratio", {"ratio": 1.0, "": 1.0}),
    "monocyte_count_absolute": ("10^3/uL", {"10^3/ul": 1.0, "10^9/l": 1.0, "k/ul": 1.0, "/ul": 0.001, "cells/ul": 0.001}),
    "eosinophil_count_absolute": ("10^3/uL", {"10^3/ul": 1.0, "10^9/l": 1.0, "k/ul": 1.0, "/ul": 0.001, "cells/ul": 0.001}),
    "basophil_count_absolute": ("10^3/uL", {"10^3/ul": 1.0, "10^9/l": 1.0, "k/ul": 1.0, "/ul": 0.001, "cells/ul": 0.001}),
    "vldl_cholesterol": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 38.67}),
    "estimated_average_glucose": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 18.016}),
    "corrected_calcium_for_serum_albumin": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 4.008}),
    "transferrin": ("mg/dL", {"mg/dl": 1.0, "g/l": 100.0}),
    "total_bilirubin": ("mg/dL", {"mg/dl": 1.0, "umol/l": 1 / 17.104, "µmol/l": 1 / 17.104}),
    "direct_bilirubin": ("mg/dL", {"mg/dl": 1.0, "umol/l": 1 / 17.104, "µmol/l": 1 / 17.104}),
    "indirect_bilirubin": ("mg/dL", {"mg/dl": 1.0, "umol/l": 1 / 17.104, "µmol/l": 1 / 17.104}),
    "total_cholesterol": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 38.67}),
    "hdl_cholesterol": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 38.67}),
    "ldl_cholesterol_calculated": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 38.67}),
    "ldl_cholesterol_direct": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 38.67}),
    "non_hdl_cholesterol": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 38.67}),
    "triglycerides": ("mg/dL", {"mg/dl": 1.0, "mmol/l": 88.57}),
    "uric_acid": ("mg/dL", {"mg/dl": 1.0, "umol/l": 1 / 59.48, "µmol/l": 1 / 59.48, "mmol/l": 16.81}),
    "alanine_aminotransferase": ("U/L", {"u/l": 1.0, "iu/l": 1.0, "ukat/l": 60.0, "µkat/l": 60.0}),
    "aspartate_aminotransferase": ("U/L", {"u/l": 1.0, "iu/l": 1.0, "ukat/l": 60.0, "µkat/l": 60.0}),
    "alkaline_phosphatase": ("U/L", {"u/l": 1.0, "iu/l": 1.0, "ukat/l": 60.0}),
    "gamma_glutamyl_transferase": ("U/L", {"u/l": 1.0, "iu/l": 1.0}),
    "lactate_dehydrogenase": ("U/L", {"u/l": 1.0, "iu/l": 1.0}),
    "thyroid_stimulating_hormone": ("uIU/mL", {"uiu/ml": 1.0, "µiu/ml": 1.0, "miu/l": 1.0, "mu/l": 1.0}),
    "free_thyroxine": ("ng/dL", {"ng/dl": 1.0, "pmol/l": 0.0777}),
    "ferritin": ("ng/mL", {"ng/ml": 1.0, "ug/l": 1.0, "µg/l": 1.0, "pmol/l": 0.445}),
    "serum_iron": ("ug/dL", {"ug/dl": 1.0, "µg/dl": 1.0, "umol/l": 5.585, "µmol/l": 5.585}),
    "total_iron_binding_capacity": ("ug/dL", {"ug/dl": 1.0, "µg/dl": 1.0, "umol/l": 5.585, "µmol/l": 5.585}),
    "transferrin_saturation": ("%", {"%": 1.0}),
    "vitamin_b12": ("pg/mL", {"pg/ml": 1.0, "pmol/l": 1.355, "ng/l": 1.0}),
    "25_hydroxy_vitamin_d": ("ng/mL", {"ng/ml": 1.0, "nmol/l": 0.4006, "ug/l": 1.0}),
    "c_reactive_protein": ("mg/L", {"mg/l": 1.0, "mg/dl": 10.0}),
    "erythrocyte_sedimentation_rate": ("mm/h", {"mm/h": 1.0, "mm/hr": 1.0, "mm/1h": 1.0}),
    "egfr_ckd_epi_creatinine": ("mL/min/1.73m2", {"ml/min/1.73m2": 1.0, "ml/min/1.73 m2": 1.0, "ml/min": 1.0}),
    "international_normalized_ratio": ("ratio", {"ratio": 1.0, "": 1.0}),
    "prothrombin_time": ("s", {"s": 1.0, "sec": 1.0, "seconds": 1.0}),
    "anion_gap": ("mmol/L", {"mmol/l": 1.0, "meq/l": 1.0}),
}

# --------------------------------------------------------------------------- #
# Physiologically possible ranges in canonical units (not reference ranges:
# anything outside is a transcription / unit / OCR error, never biology).
# Tietz Textbook of Clinical Chemistry; extreme published survivals used as
# the outer bound.
# --------------------------------------------------------------------------- #
HARD_LIMITS: dict[str, tuple[float, float]] = {
    "hemoglobin": (1.5, 25.0), "hematocrit": (5.0, 75.0), "red_blood_cell_count": (0.5, 9.5),
    "white_blood_cell_count": (0.05, 600.0), "platelets": (1.0, 3000.0),
    "mean_corpuscular_volume": (45.0, 150.0), "mean_corpuscular_hemoglobin": (12.0, 50.0),
    "mean_corpuscular_hemoglobin_concentration": (22.0, 40.0),
    "neutrophils_percent": (0.0, 100.0), "lymphocytes_percent": (0.0, 100.0), "monocytes_percent": (0.0, 60.0),
    "eosinophils_percent": (0.0, 90.0), "basophils_percent": (0.0, 30.0),
    "neutrophil_count_absolute": (0.0, 400.0), "lymphocyte_count_absolute": (0.0, 500.0),
    "glucose": (10.0, 2500.0), "fasting_plasma_glucose": (10.0, 2500.0), "hemoglobin_a1c": (3.0, 20.0),
    "creatinine": (0.1, 40.0), "blood_urea_nitrogen": (1.0, 300.0), "urea": (2.0, 650.0),
    "sodium": (95.0, 195.0), "potassium": (1.2, 12.0), "chloride": (55.0, 160.0), "bicarbonate": (2.0, 60.0),
    "calcium_total": (3.0, 20.0), "phosphate": (0.3, 20.0), "magnesium": (0.3, 12.0),
    "albumin": (0.5, 7.0), "total_protein": (2.0, 15.0), "globulin": (0.3, 12.0),
    "total_bilirubin": (0.05, 70.0), "direct_bilirubin": (0.0, 50.0), "indirect_bilirubin": (0.0, 50.0),
    "total_cholesterol": (30.0, 1500.0), "hdl_cholesterol": (3.0, 250.0), "ldl_cholesterol_calculated": (5.0, 1200.0),
    "ldl_cholesterol_direct": (5.0, 1200.0), "non_hdl_cholesterol": (10.0, 1400.0), "triglycerides": (10.0, 15000.0),
    "uric_acid": (0.3, 30.0),
    "alanine_aminotransferase": (1.0, 20000.0), "aspartate_aminotransferase": (1.0, 30000.0),
    "alkaline_phosphatase": (5.0, 10000.0), "gamma_glutamyl_transferase": (1.0, 10000.0),
    "lactate_dehydrogenase": (30.0, 50000.0),
    "thyroid_stimulating_hormone": (0.001, 1000.0), "free_thyroxine": (0.05, 15.0),
    "ferritin": (0.5, 100000.0), "serum_iron": (2.0, 1500.0), "total_iron_binding_capacity": (50.0, 900.0),
    "transferrin_saturation": (0.5, 100.0), "vitamin_b12": (20.0, 20000.0), "25_hydroxy_vitamin_d": (1.0, 400.0),
    "c_reactive_protein": (0.0, 1000.0), "erythrocyte_sedimentation_rate": (0.0, 160.0),
    "egfr_ckd_epi_creatinine": (1.0, 250.0), "international_normalized_ratio": (0.5, 20.0), "prothrombin_time": (6.0, 200.0),
    "anion_gap": (-5.0, 60.0),
}

# OCR glyph confusions seen on printed reports (both directions).
_GLYPH_SWAPS = (("1", "7"), ("0", "8"), ("5", "6"), ("3", "8"), ("6", "8"), ("2", "7"), ("4", "9"), ("0", "6"), ("1", "4"), ("6", "9"))

# Median adult value in canonical units - used only to rank competing
# repairs (the reading closer, in log space, to a typical result is the
# more probable one), never to accept or reject a value.
TYPICAL: dict[str, float] = {
    "hemoglobin": 14.0, "hematocrit": 42.0, "red_blood_cell_count": 4.7, "white_blood_cell_count": 7.0,
    "platelets": 250.0, "mean_corpuscular_volume": 90.0, "mean_corpuscular_hemoglobin": 30.0,
    "mean_corpuscular_hemoglobin_concentration": 33.5, "neutrophils_percent": 58.0, "lymphocytes_percent": 32.0,
    "monocytes_percent": 6.0, "eosinophils_percent": 2.5, "basophils_percent": 0.6,
    "neutrophil_count_absolute": 4.0, "lymphocyte_count_absolute": 2.2,
    "glucose": 95.0, "fasting_plasma_glucose": 92.0, "hemoglobin_a1c": 5.5, "creatinine": 0.9,
    "blood_urea_nitrogen": 14.0, "urea": 30.0, "sodium": 140.0, "potassium": 4.2, "chloride": 103.0,
    "bicarbonate": 24.0, "calcium_total": 9.4, "phosphate": 3.5, "magnesium": 2.0, "albumin": 4.2,
    "total_protein": 7.0, "globulin": 2.8, "total_bilirubin": 0.8, "direct_bilirubin": 0.2, "indirect_bilirubin": 0.6,
    "total_cholesterol": 190.0, "hdl_cholesterol": 50.0, "ldl_cholesterol_calculated": 115.0,
    "ldl_cholesterol_direct": 115.0, "non_hdl_cholesterol": 140.0, "triglycerides": 130.0, "uric_acid": 5.5,
    "alanine_aminotransferase": 25.0, "aspartate_aminotransferase": 25.0, "alkaline_phosphatase": 80.0,
    "gamma_glutamyl_transferase": 30.0, "lactate_dehydrogenase": 180.0, "thyroid_stimulating_hormone": 1.8,
    "free_thyroxine": 1.2, "ferritin": 80.0, "serum_iron": 90.0, "total_iron_binding_capacity": 320.0,
    "transferrin_saturation": 28.0, "vitamin_b12": 450.0, "25_hydroxy_vitamin_d": 28.0, "c_reactive_protein": 2.0,
    "erythrocyte_sedimentation_rate": 12.0, "egfr_ckd_epi_creatinine": 95.0, "international_normalized_ratio": 1.0,
    "prothrombin_time": 12.5, "anion_gap": 10.0,
    "albumin_to_globulin_ratio": 1.5, "monocyte_count_absolute": 0.45, "eosinophil_count_absolute": 0.15,
    "basophil_count_absolute": 0.04, "vldl_cholesterol": 26.0, "estimated_average_glucose": 111.0,
    "corrected_calcium_for_serum_albumin": 9.4, "transferrin": 250.0,
}

# For a failed identity, the value of one field implied by the others
# (used as a repair candidate when no digit-level repair reproduces it).
DERIVE: dict[str, dict[str, Callable[[dict[str, float]], Optional[float]]]] = {
    "mchc_identity": {"mean_corpuscular_hemoglobin_concentration": lambda v: v["hemoglobin"] / v["hematocrit"] * 100.0,
                      "hematocrit": lambda v: v["hemoglobin"] / v["mean_corpuscular_hemoglobin_concentration"] * 100.0,
                      "hemoglobin": lambda v: v["hematocrit"] * v["mean_corpuscular_hemoglobin_concentration"] / 100.0},
    "mcv_identity": {"mean_corpuscular_volume": lambda v: v["hematocrit"] / v["red_blood_cell_count"] * 10.0,
                     "hematocrit": lambda v: v["mean_corpuscular_volume"] * v["red_blood_cell_count"] / 10.0,
                     "red_blood_cell_count": lambda v: v["hematocrit"] / v["mean_corpuscular_volume"] * 10.0},
    "mch_identity": {"mean_corpuscular_hemoglobin": lambda v: v["hemoglobin"] / v["red_blood_cell_count"] * 10.0,
                     "hemoglobin": lambda v: v["mean_corpuscular_hemoglobin"] * v["red_blood_cell_count"] / 10.0,
                     "red_blood_cell_count": lambda v: v["hemoglobin"] / v["mean_corpuscular_hemoglobin"] * 10.0},
    "anc_identity": {"neutrophil_count_absolute": lambda v: v["white_blood_cell_count"] * v["neutrophils_percent"] / 100.0,
                     "neutrophils_percent": lambda v: v["neutrophil_count_absolute"] / v["white_blood_cell_count"] * 100.0,
                     "white_blood_cell_count": lambda v: v["neutrophil_count_absolute"] / v["neutrophils_percent"] * 100.0},
    "alc_identity": {"lymphocyte_count_absolute": lambda v: v["white_blood_cell_count"] * v["lymphocytes_percent"] / 100.0,
                     "lymphocytes_percent": lambda v: v["lymphocyte_count_absolute"] / v["white_blood_cell_count"] * 100.0},
    "bilirubin_sum": {"total_bilirubin": lambda v: v["direct_bilirubin"] + v["indirect_bilirubin"],
                      "direct_bilirubin": lambda v: v["total_bilirubin"] - v["indirect_bilirubin"],
                      "indirect_bilirubin": lambda v: v["total_bilirubin"] - v["direct_bilirubin"]},
    "globulin_identity": {"globulin": lambda v: v["total_protein"] - v["albumin"],
                          "albumin": lambda v: v["total_protein"] - v["globulin"],
                          "total_protein": lambda v: v["albumin"] + v["globulin"]},
    "friedewald": {"ldl_cholesterol_calculated": lambda v: v["total_cholesterol"] - v["hdl_cholesterol"] - v["triglycerides"] / 5.0,
                   "ldl_cholesterol_direct": lambda v: v["total_cholesterol"] - v["hdl_cholesterol"] - v["triglycerides"] / 5.0,
                   "total_cholesterol": lambda v: v["ldl_cholesterol_calculated"] + v["hdl_cholesterol"] + v["triglycerides"] / 5.0,
                   "hdl_cholesterol": lambda v: v["total_cholesterol"] - v["ldl_cholesterol_calculated"] - v["triglycerides"] / 5.0},
    "non_hdl_identity": {"non_hdl_cholesterol": lambda v: v["total_cholesterol"] - v["hdl_cholesterol"]},
    "urea_bun_ratio": {"urea": lambda v: v["blood_urea_nitrogen"] * 2.14, "blood_urea_nitrogen": lambda v: v["urea"] / 2.14},
    "anion_gap": {"anion_gap": lambda v: v["sodium"] - v["chloride"] - v["bicarbonate"],
                  "chloride": lambda v: v["sodium"] - v["bicarbonate"] - (v["anion_gap"] if v.get("anion_gap") is not None else 10.0),
                  "sodium": lambda v: v["chloride"] + v["bicarbonate"] + (v["anion_gap"] if v.get("anion_gap") is not None else 10.0)},
    "amc_identity": {"monocyte_count_absolute": lambda v: v["white_blood_cell_count"] * v["monocytes_percent"] / 100.0,
                     "monocytes_percent": lambda v: v["monocyte_count_absolute"] / v["white_blood_cell_count"] * 100.0},
    "aec_identity": {"eosinophil_count_absolute": lambda v: v["white_blood_cell_count"] * v["eosinophils_percent"] / 100.0,
                     "eosinophils_percent": lambda v: v["eosinophil_count_absolute"] / v["white_blood_cell_count"] * 100.0},
    "abc_identity": {"basophil_count_absolute": lambda v: v["white_blood_cell_count"] * v["basophils_percent"] / 100.0,
                     "basophils_percent": lambda v: v["basophil_count_absolute"] / v["white_blood_cell_count"] * 100.0},
    "ag_ratio_identity": {"albumin_to_globulin_ratio": lambda v: v["albumin"] / v["globulin"],
                          "globulin": lambda v: v["albumin"] / v["albumin_to_globulin_ratio"],
                          "albumin": lambda v: v["globulin"] * v["albumin_to_globulin_ratio"]},
    "vldl_identity": {"vldl_cholesterol": lambda v: v["triglycerides"] / 5.0,
                      "triglycerides": lambda v: v["vldl_cholesterol"] * 5.0},
    "eag_identity": {"estimated_average_glucose": lambda v: 28.7 * v["hemoglobin_a1c"] - 46.7,
                     "hemoglobin_a1c": lambda v: (v["estimated_average_glucose"] + 46.7) / 28.7},
    "corrected_calcium_identity": {
        "corrected_calcium_for_serum_albumin": lambda v: v["calcium_total"] + 0.8 * (4.0 - v["albumin"]),
        "calcium_total": lambda v: v["corrected_calcium_for_serum_albumin"] - 0.8 * (4.0 - v["albumin"]),
        "albumin": lambda v: 4.0 - (v["corrected_calcium_for_serum_albumin"] - v["calcium_total"]) / 0.8},
    "transferrin_tibc": {"total_iron_binding_capacity": lambda v: v["transferrin"] * 1.389,
                         "transferrin": lambda v: v["total_iron_binding_capacity"] / 1.389},
    "tsat_identity": {"transferrin_saturation": lambda v: 100.0 * v["serum_iron"] / v["total_iron_binding_capacity"],
                      "serum_iron": lambda v: v["transferrin_saturation"] * v["total_iron_binding_capacity"] / 100.0},
    "differential_sum": {},
}


def _typ_dist(fid: str, canon_val: float) -> float:
    t = TYPICAL.get(fid)
    if t is None or t <= 0 or canon_val <= 0:
        return 1.0
    return abs(math.log(canon_val / t))

_SCALE_REPAIRS = (0.1, 10.0, 0.01, 100.0, 0.001, 1000.0)


def _norm_unit(u: Optional[str]) -> str:
    if not u:
        return ""
    t = str(u).strip().lower().replace(" ", "")
    t = t.replace("μ", "u").replace("µ", "u").replace("×", "x").replace("·", "")
    t = t.replace("10e9", "10^9").replace("10e3", "10^3").replace("10e6", "10^6").replace("10e12", "10^12")
    t = t.replace("10⁹", "10^9").replace("10³", "10^3").replace("10⁶", "10^6").replace("10¹²", "10^12")
    t = t.replace("mm³", "mm3").replace("cumm", "mm3").replace("cmm", "mm3")
    if t.startswith("x"):
        t = t[1:]
    return t


def canonical_value(feature_id: str, value: Any, unit: Optional[str]) -> Optional[float]:
    """Return `value` in the analyte's canonical unit, or None if unknown."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    spec = _CONV.get(feature_id)
    if spec is None:
        return None
    canon, table = spec
    u = _norm_unit(unit)
    if not u or u == _norm_unit(canon):
        return v
    if feature_id == "hemoglobin_a1c" and u == "mmol/mol":
        return 0.0915 * v + 2.15
    f = table.get(u)
    if f is None:
        return None
    return v * f


# --------------------------------------------------------------------------- #
# Identities. Each returns None when not computable, else (ok, message).
# `fields` lists the analytes the identity touches (used for culprit search).
# --------------------------------------------------------------------------- #
class _Check:
    __slots__ = ("name", "fields", "fn", "corroborates")

    def __init__(self, name: str, fields: tuple[str, ...], fn: Callable[[dict[str, float]], Optional[tuple[bool, str]]],
                 corroborates: bool = True):
        self.name, self.fields, self.fn, self.corroborates = name, fields, fn, corroborates


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-9)


def _c_mchc(v):
    hb, hct = v.get("hemoglobin"), v.get("hematocrit")
    if hb is None or hct is None or hct <= 0:
        return None
    calc = hb / hct * 100.0
    mchc = v.get("mean_corpuscular_hemoglobin_concentration")
    if mchc is not None:
        ok = abs(mchc - calc) <= 2.5
        return ok, f"MCHC printed {mchc:.1f} g/dL vs Hb/Hct x100 = {calc:.1f} g/dL"
    ok = 24.0 <= calc <= 38.5
    return ok, f"Hb/Hct imply MCHC {calc:.1f} g/dL (possible 24-38.5)"


def _c_mcv(v):
    hct, rbc, mcv = v.get("hematocrit"), v.get("red_blood_cell_count"), v.get("mean_corpuscular_volume")
    if hct is None or rbc is None or mcv is None or rbc <= 0:
        return None
    calc = hct / rbc * 10.0
    return abs(mcv - calc) <= max(6.0, 0.07 * calc), f"MCV printed {mcv:.0f} fL vs Hct/RBC x10 = {calc:.0f} fL"


def _c_mch(v):
    hb, rbc, mch = v.get("hemoglobin"), v.get("red_blood_cell_count"), v.get("mean_corpuscular_hemoglobin")
    if hb is None or rbc is None or mch is None or rbc <= 0:
        return None
    calc = hb / rbc * 10.0
    return abs(mch - calc) <= max(2.5, 0.08 * calc), f"MCH printed {mch:.1f} pg vs Hb/RBC x10 = {calc:.1f} pg"


def _c_rule_of_three(v):
    hb, hct = v.get("hemoglobin"), v.get("hematocrit")
    if hb is None or hct is None:
        return None
    # Hct ~ 3 x Hb holds within ~15 % except in marked hypo/hyperchromia,
    # which the MCHC check already covers; keep this tolerant.
    return 2.4 <= hct / max(hb, 1e-9) <= 3.7, f"Hct/Hb = {hct / max(hb, 1e-9):.2f} (expected ~3)"


def _c_diff_sum(v):
    parts = [v.get(f) for f in ("neutrophils_percent", "lymphocytes_percent", "monocytes_percent",
                                "eosinophils_percent", "basophils_percent")]
    present = [p for p in parts if p is not None]
    if len(present) < 4:
        return None
    total = sum(present)
    return 94.0 <= total <= 106.0, f"differential sums to {total:.0f} %"


def _c_anc(v):
    wbc, pct, anc = v.get("white_blood_cell_count"), v.get("neutrophils_percent"), v.get("neutrophil_count_absolute")
    if wbc is None or pct is None or anc is None:
        return None
    calc = wbc * pct / 100.0
    return _rel(anc, calc) <= 0.15 or abs(anc - calc) <= 0.3, f"ANC printed {anc:.2f} vs WBC x N% = {calc:.2f} x10^9/L"


def _c_alc(v):
    wbc, pct, alc = v.get("white_blood_cell_count"), v.get("lymphocytes_percent"), v.get("lymphocyte_count_absolute")
    if wbc is None or pct is None or alc is None:
        return None
    calc = wbc * pct / 100.0
    return _rel(alc, calc) <= 0.15 or abs(alc - calc) <= 0.3, f"ALC printed {alc:.2f} vs WBC x L% = {calc:.2f} x10^9/L"


def _c_bili(v):
    t, d = v.get("total_bilirubin"), v.get("direct_bilirubin")
    if t is None or d is None:
        return None
    return d <= t * 1.05 + 0.1, f"direct bilirubin {d:.2f} vs total {t:.2f} mg/dL"


def _c_bili_sum(v):
    t, d, i = v.get("total_bilirubin"), v.get("direct_bilirubin"), v.get("indirect_bilirubin")
    if t is None or d is None or i is None:
        return None
    return abs((d + i) - t) <= max(0.2, 0.1 * t), f"direct + indirect = {d + i:.2f} vs total {t:.2f} mg/dL"


def _c_albumin(v):
    a, tp = v.get("albumin"), v.get("total_protein")
    if a is None or tp is None:
        return None
    return a <= tp * 1.02 + 0.1, f"albumin {a:.1f} vs total protein {tp:.1f} g/dL"


def _c_globulin(v):
    a, tp, g = v.get("albumin"), v.get("total_protein"), v.get("globulin")
    if a is None or tp is None or g is None:
        return None
    return abs((tp - a) - g) <= 0.4, f"globulin printed {g:.1f} vs TP - albumin = {tp - a:.1f} g/dL"


def _c_ldl_tc(v):
    tc = v.get("total_cholesterol")
    ldl = v.get("ldl_cholesterol_direct") if v.get("ldl_cholesterol_direct") is not None else v.get("ldl_cholesterol_calculated")
    hdl = v.get("hdl_cholesterol")
    if tc is None or (ldl is None and hdl is None):
        return None
    parts = (ldl or 0.0) + (hdl or 0.0)
    return parts <= tc * 1.05 + 5.0, f"LDL + HDL = {parts:.0f} vs total cholesterol {tc:.0f} mg/dL"


def _c_friedewald(v):
    tc, hdl, tg = v.get("total_cholesterol"), v.get("hdl_cholesterol"), v.get("triglycerides")
    ldl, direct = v.get("ldl_cholesterol_calculated"), v.get("ldl_cholesterol_direct")
    if tc is None or hdl is None or tg is None or tg >= 400:
        return None
    calc = tc - hdl - tg / 5.0
    if ldl is not None:
        return abs(ldl - calc) <= max(12.0, 0.12 * max(calc, 1.0)), f"LDL printed {ldl:.0f} vs Friedewald {calc:.0f} mg/dL"
    if direct is not None:
        # a directly measured LDL tracks Friedewald within ~20 % below TG 400
        return abs(direct - calc) <= max(20.0, 0.20 * max(calc, 1.0)), f"direct LDL {direct:.0f} vs Friedewald {calc:.0f} mg/dL"
    return None


def _c_non_hdl(v):
    tc, hdl, nh = v.get("total_cholesterol"), v.get("hdl_cholesterol"), v.get("non_hdl_cholesterol")
    if tc is None or hdl is None or nh is None:
        return None
    return abs((tc - hdl) - nh) <= max(6.0, 0.05 * tc), f"non-HDL printed {nh:.0f} vs TC - HDL = {tc - hdl:.0f} mg/dL"


def _c_urea_bun(v):
    bun, urea = v.get("blood_urea_nitrogen"), v.get("urea")
    if bun is None or urea is None or bun <= 0:
        return None
    r = urea / bun
    return 1.9 <= r <= 2.4, f"urea/BUN = {r:.2f} (expected 2.14)"


def _c_anion_gap(v):
    na, cl, hco3 = v.get("sodium"), v.get("chloride"), v.get("bicarbonate")
    if na is None or cl is None or hco3 is None:
        return None
    ag = na - cl - hco3
    printed = v.get("anion_gap")
    if printed is not None:
        return abs(printed - ag) <= 4.0 or abs(printed - (ag + (v.get("potassium") or 0.0))) <= 4.0, \
            f"anion gap printed {printed:.0f} vs Na-(Cl+HCO3) = {ag:.0f} mmol/L"
    return -2.0 <= ag <= 40.0, f"Na-(Cl+HCO3) = {ag:.0f} mmol/L (possible -2..40)"


def _abs_count_check(label, pct_key, abs_key):
    def fn(v):
        wbc, pct, ab = v.get("white_blood_cell_count"), v.get(pct_key), v.get(abs_key)
        if wbc is None or pct is None or ab is None or wbc <= 0:
            return None
        calc = wbc * pct / 100.0
        tol = max(0.08, 0.12 * calc)           # rounding of small absolute counts
        return abs(ab - calc) <= tol, f"{label} printed {ab:.2f} vs WBC x % = {calc:.2f}"
    return fn


def _c_ag_ratio(v):
    alb, glob, ag = v.get("albumin"), v.get("globulin"), v.get("albumin_to_globulin_ratio")
    if alb is None or glob is None or ag is None or glob <= 0:
        return None
    calc = alb / glob
    return abs(ag - calc) <= max(0.12, 0.08 * calc), f"A/G printed {ag:.2f} vs albumin/globulin = {calc:.2f}"


def _c_vldl(v):
    tg, vldl = v.get("triglycerides"), v.get("vldl_cholesterol")
    if tg is None or vldl is None or tg > 400.0:        # TG/5 invalid above 400 mg/dL
        return None
    calc = tg / 5.0
    return abs(vldl - calc) <= max(3.0, 0.12 * calc), f"VLDL printed {vldl:.0f} vs TG/5 = {calc:.0f} mg/dL"


def _c_eag(v):
    a1c, eag = v.get("hemoglobin_a1c"), v.get("estimated_average_glucose")
    if a1c is None or eag is None:
        return None
    calc = 28.7 * a1c - 46.7                              # ADAG (Nathan 2008)
    return abs(eag - calc) <= max(4.0, 0.04 * calc), f"eAG printed {eag:.0f} vs 28.7 x A1c - 46.7 = {calc:.0f} mg/dL"


def _c_corrected_ca(v):
    ca, alb, cc = v.get("calcium_total"), v.get("albumin"), v.get("corrected_calcium_for_serum_albumin")
    if ca is None or alb is None or cc is None:
        return None
    calc = ca + 0.8 * (4.0 - alb)
    return abs(cc - calc) <= 0.35, f"corrected Ca printed {cc:.2f} vs Ca + 0.8(4 - albumin) = {calc:.2f} mg/dL"


def _c_transferrin_tibc(v):
    tf, tibc = v.get("transferrin"), v.get("total_iron_binding_capacity")
    if tf is None or tibc is None:
        return None
    calc = tf * 1.389                                      # TIBC(ug/dL) ~ 1.389 x transferrin(mg/dL)
    return abs(tibc - calc) <= 0.15 * calc, f"TIBC printed {tibc:.0f} vs 1.389 x transferrin = {calc:.0f} ug/dL"


def _c_ldl_direct_vs_calc(v):
    d, c, tg = v.get("ldl_cholesterol_direct"), v.get("ldl_cholesterol_calculated"), v.get("triglycerides")
    if d is None or c is None or (tg is not None and tg > 400.0):
        return None
    return abs(d - c) <= max(15.0, 0.20 * d), f"direct LDL {d:.0f} vs calculated LDL {c:.0f} mg/dL"


def _c_tsat(v):
    fe, tibc, ts = v.get("serum_iron"), v.get("total_iron_binding_capacity"), v.get("transferrin_saturation")
    if fe is None or tibc is None or ts is None or tibc <= 0:
        return None
    calc = 100.0 * fe / tibc
    return abs(ts - calc) <= max(5.0, 0.12 * calc), f"TSAT printed {ts:.0f} % vs Fe/TIBC = {calc:.0f} %"


def _c_egfr_cr(v):
    cr, egfr = v.get("creatinine"), v.get("egfr_ckd_epi_creatinine")
    if cr is None or egfr is None:
        return None
    # Monotonic sanity only (no age/sex here): Cr >= 2.0 cannot give eGFR >= 60;
    # Cr <= 0.7 cannot give eGFR < 45 in an adult.
    if cr >= 2.0 and egfr >= 60:
        return False, f"creatinine {cr:.1f} mg/dL is incompatible with eGFR {egfr:.0f}"
    if cr <= 0.7 and egfr < 45:
        return False, f"creatinine {cr:.1f} mg/dL is incompatible with eGFR {egfr:.0f}"
    return True, f"creatinine {cr:.1f} / eGFR {egfr:.0f} coherent"


CHECKS: tuple[_Check, ...] = (
    _Check("mchc_identity", ("hemoglobin", "hematocrit", "mean_corpuscular_hemoglobin_concentration"), _c_mchc),
    _Check("mcv_identity", ("hematocrit", "red_blood_cell_count", "mean_corpuscular_volume"), _c_mcv),
    _Check("mch_identity", ("hemoglobin", "red_blood_cell_count", "mean_corpuscular_hemoglobin"), _c_mch),
    _Check("rule_of_three", ("hemoglobin", "hematocrit"), _c_rule_of_three, corroborates=False),
    _Check("differential_sum", ("neutrophils_percent", "lymphocytes_percent", "monocytes_percent",
                                "eosinophils_percent", "basophils_percent"), _c_diff_sum),
    _Check("anc_identity", ("white_blood_cell_count", "neutrophils_percent", "neutrophil_count_absolute"), _c_anc),
    _Check("alc_identity", ("white_blood_cell_count", "lymphocytes_percent", "lymphocyte_count_absolute"), _c_alc),
    _Check("direct_le_total_bilirubin", ("total_bilirubin", "direct_bilirubin"), _c_bili),
    _Check("bilirubin_sum", ("total_bilirubin", "direct_bilirubin", "indirect_bilirubin"), _c_bili_sum),
    _Check("albumin_le_total_protein", ("albumin", "total_protein"), _c_albumin),
    _Check("globulin_identity", ("albumin", "total_protein", "globulin"), _c_globulin),
    _Check("ldl_hdl_le_tc", ("total_cholesterol", "ldl_cholesterol_calculated", "ldl_cholesterol_direct", "hdl_cholesterol"), _c_ldl_tc),
    _Check("friedewald", ("total_cholesterol", "hdl_cholesterol", "triglycerides", "ldl_cholesterol_calculated", "ldl_cholesterol_direct"), _c_friedewald),
    _Check("non_hdl_identity", ("total_cholesterol", "hdl_cholesterol", "non_hdl_cholesterol"), _c_non_hdl),
    _Check("urea_bun_ratio", ("blood_urea_nitrogen", "urea"), _c_urea_bun),
    _Check("anion_gap", ("sodium", "chloride", "bicarbonate", "anion_gap", "potassium"), _c_anion_gap),
    _Check("tsat_identity", ("serum_iron", "total_iron_binding_capacity", "transferrin_saturation"), _c_tsat),
    _Check("egfr_creatinine_monotonic", ("creatinine", "egfr_ckd_epi_creatinine"), _c_egfr_cr, corroborates=False),
    _Check("amc_identity", ("white_blood_cell_count", "monocytes_percent", "monocyte_count_absolute"),
           _abs_count_check("AMC", "monocytes_percent", "monocyte_count_absolute")),
    _Check("aec_identity", ("white_blood_cell_count", "eosinophils_percent", "eosinophil_count_absolute"),
           _abs_count_check("AEC", "eosinophils_percent", "eosinophil_count_absolute")),
    _Check("abc_identity", ("white_blood_cell_count", "basophils_percent", "basophil_count_absolute"),
           _abs_count_check("ABC", "basophils_percent", "basophil_count_absolute")),
    _Check("ag_ratio_identity", ("albumin", "globulin", "albumin_to_globulin_ratio"), _c_ag_ratio),
    _Check("vldl_identity", ("triglycerides", "vldl_cholesterol"), _c_vldl),
    _Check("eag_identity", ("hemoglobin_a1c", "estimated_average_glucose"), _c_eag),
    _Check("corrected_calcium_identity", ("calcium_total", "albumin", "corrected_calcium_for_serum_albumin"), _c_corrected_ca),
    _Check("transferrin_tibc", ("transferrin", "total_iron_binding_capacity"), _c_transferrin_tibc),
    _Check("ldl_direct_vs_calculated", ("ldl_cholesterol_direct", "ldl_cholesterol_calculated", "triglycerides"),
           _c_ldl_direct_vs_calc, corroborates=False),
)


# --------------------------------------------------------------------------- #
# Repair candidates for a single field.
# --------------------------------------------------------------------------- #
def _repair_candidates(raw_value: Any) -> list[tuple[float, str]]:
    """Alternative readings of one printed number, most likely first."""
    out: list[tuple[float, str]] = []
    try:
        v = float(raw_value)
    except (TypeError, ValueError):
        return out
    if not math.isfinite(v):
        return out
    for f in _SCALE_REPAIRS:
        out.append((v * f, f"decimal shift x{f:g}"))
    txt = repr(raw_value) if isinstance(raw_value, str) else (f"{v:g}")
    txt = txt.strip("'\"")
    for a, b in _GLYPH_SWAPS:
        for x, y in ((a, b), (b, a)):
            if x in txt:
                for i, ch in enumerate(txt):
                    if ch == x:
                        cand = txt[:i] + y + txt[i + 1:]
                        try:
                            cv = float(cand)
                        except ValueError:
                            continue
                        if cv != v:
                            out.append((cv, f"glyph {x}->{y}"))
    # two adjacent digits transposed by the reader or the typist (14.2 -> 41.2,
    # 12.4). The decimal point is skipped so that the swap acts on digits.
    digit_pos = [i for i, ch in enumerate(txt) if ch.isdigit()]
    for i, j in zip(digit_pos, digit_pos[1:]):
        if txt[i] == txt[j]:
            continue
        lst = list(txt)
        lst[i], lst[j] = lst[j], lst[i]
        try:
            cv = float("".join(lst))
        except ValueError:
            continue
        if cv != v:
            out.append((cv, f"transposition {txt[i]}{txt[j]}->{txt[j]}{txt[i]}"))
    # dropped / misplaced decimal point in an integer reading (135 -> 13.5)
    if "." not in txt and len(txt.lstrip("-")) >= 2:
        for pos in range(1, len(txt)):
            cand = txt[:pos] + "." + txt[pos:]
            try:
                cv = float(cand)
            except ValueError:
                continue
            if cv != v and all(abs(cv - o) > 1e-9 for o, _ in out):
                out.append((cv, "missing decimal point"))
    # de-duplicate preserving order
    seen: set[float] = set()
    uniq: list[tuple[float, str]] = []
    for cv, why in out:
        key = round(cv, 6)
        if key in seen or cv <= 0:
            continue
        seen.add(key)
        uniq.append((cv, why))
    return uniq


class ConsistencyReport(dict):
    """Plain dict subclass so it serialises; attributes for convenience."""


def _flag_check(rec: Mapping[str, Any], canon: Optional[float]) -> Optional[str]:
    """Report flag (H/L/N) vs value and printed interval. Uses raw units
    because the printed interval is in the same unit as the printed value."""
    flag = rec.get("flag")
    lo, hi = rec.get("report_range_low"), rec.get("report_range_high")
    try:
        v = float(rec.get("value"))
    except (TypeError, ValueError):
        return None
    if lo is None and hi is None:
        return None
    f = str(flag or "").upper()
    inside = (lo is None or v >= lo) and (hi is None or v <= hi)
    if f in ("H", "CRIT") and hi is not None and v <= hi and (lo is None or v >= lo):
        return f"flag '{flag}' but value {v:g} lies inside the printed interval {lo}-{hi}"
    if f == "L" and lo is not None and v >= lo and (hi is None or v <= hi):
        return f"flag '{flag}' but value {v:g} lies inside the printed interval {lo}-{hi}"
    if f == "N" and not inside:
        return f"flag 'N' but value {v:g} lies outside the printed interval {lo}-{hi}"
    if not f and lo is not None and hi is not None and hi > lo:
        if v > hi * 10 or (lo > 0 and v < lo / 10):
            return f"value {v:g} is >10x outside the printed interval {lo}-{hi} with no flag"
    return None


def _fmt(x: float) -> float:
    """Round a proposed value to a sensible number of significant digits."""
    if x == 0:
        return 0.0
    mag = int(math.floor(math.log10(abs(x))))
    return round(x, max(0, 2 - mag))


def validate_results(results: list[dict[str, Any]], *,
                     registry_features: Optional[Mapping[str, Any]] = None) -> ConsistencyReport:
    """Mutates `results` in place (confidence, warnings, suggested_value,
    requires_confirmation, consistency fields) and returns a summary."""
    by_fid: dict[str, dict[str, Any]] = {}
    for r in results:
        fid = r.get("feature_id")
        if not fid or not isinstance(r.get("value"), (int, float)) or isinstance(r.get("value"), bool):
            continue
        by_fid.setdefault(fid, r)

    canon: dict[str, float] = {}
    for fid, r in by_fid.items():
        cv = canonical_value(fid, r.get("value"), r.get("unit"))
        if cv is None and registry_features and fid in registry_features:
            units = (registry_features[fid].get("units") or {})
            cu = _norm_unit(units.get("canonical"))
            if not r.get("unit") or _norm_unit(r.get("unit")) == cu:
                try:
                    cv = float(r.get("value"))
                except (TypeError, ValueError):
                    cv = None
        if cv is not None:
            canon[fid] = cv

    summary = ConsistencyReport(checks_run=0, checks_passed=0, failed=[], suspects=[], repairs_suggested=0,
                                plausibility_violations=[], flag_mismatches=[], corroborated=[], exonerated=[])
    check_by_name = {c.name: c for c in CHECKS}

    # legacy multiplicative factors -> evidence terms of the log-odds model
    _FACTOR_TERM = {0.45: "identity_culprit", 0.7: "identity_unresolved", 0.35: "implausible_value",
                    0.4: "implausible_value", 0.75: "flag_mismatch"}

    def note(r: dict[str, Any], msg: str, *, factor: float = 1.0, force_review: bool = False,
             term: Optional[str] = None) -> None:
        r.setdefault("warnings", [])
        if msg not in r["warnings"]:
            r["warnings"].append(msg)
        term = term or _FACTOR_TERM.get(factor)
        if term:
            _conf.add_evidence(r, term, note=msg[:60])
        elif factor != 1.0:
            _conf.add_evidence(r, "legacy_factor", llr=math.log(max(1e-6, factor)), note=msg[:60])
        if force_review:
            r["requires_confirmation"] = True
            if r.get("suggested_action") == "accept":
                r["suggested_action"] = "review"

    def suggest(r: dict[str, Any], fid: str, cand: float, why: str) -> None:
        if r.get("suggested_value") is None:
            r["suggested_value"] = _fmt(cand)
            r["repair_reason"] = why
            summary["repairs_suggested"] += 1
            if fid not in summary["suspects"]:
                summary["suspects"].append(fid)

    def limits_for(fid: str) -> Optional[tuple[float, float]]:
        lim = HARD_LIMITS.get(fid)
        if lim:
            return lim
        if registry_features and fid in registry_features:
            val = (registry_features[fid].get("validation") or {})
            pl = val.get("physiological_limits") or {}
            lo, hi = pl.get("min"), pl.get("max")
            if lo is None or hi is None or (lo, hi) == (4.5, 9.0) or (hi >= 1000.0 and lo == 0.0):
                return None
            if val.get("confidence") == "high":
                return float(lo), float(hi)
        return None

    def evaluate(values: Mapping[str, float]) -> dict[str, tuple[bool, str]]:
        out = {}
        for chk in CHECKS:
            res = chk.fn(values)
            if res is not None:
                out[chk.name] = res
        return out

    def candidates_for(fid: str, r: dict[str, Any]) -> list[tuple[float, float, str]]:
        """(canonical_value, printed_value, reason) within hard limits."""
        lim = limits_for(fid)
        out = []
        for cand, why in _repair_candidates(r.get("original_value", r.get("value"))):
            ccv = canonical_value(fid, cand, r.get("unit"))
            if ccv is None:
                continue
            if lim and not (lim[0] <= ccv <= lim[1]):
                continue
            out.append((ccv, cand, why))
        return out

    def printed_from_canonical(fid: str, r: dict[str, Any], ccv: float) -> float:
        one = canonical_value(fid, 1.0, r.get("unit"))
        return ccv / one if one else ccv

    def swap_candidates(fid: str, r: dict[str, Any], my_failed: Iterable[str]) -> list[tuple[float, float, str]]:
        """Row-swap story: the printed number of a NEIGHBOURING analyte in a
        failing identity was read into this row (or the rows were exchanged).
        Only fields sharing a failed identity are tried, so the candidate set
        stays small and a clean panel (no failures) never sees these."""
        lim = limits_for(fid)
        out: list[tuple[float, float, str]] = []
        seen: set[float] = set()
        for n in my_failed:
            for g in check_by_name[n].fields:
                if g == fid or g not in by_fid:
                    continue
                try:
                    pv = float(by_fid[g].get("original_value", by_fid[g].get("value")))
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(pv) or pv <= 0:
                    continue
                ccv = canonical_value(fid, pv, r.get("unit"))
                if ccv is None or round(ccv, 6) in seen:
                    continue
                if lim and not (lim[0] <= ccv <= lim[1]):
                    continue
                seen.add(round(ccv, 6))
                out.append((ccv, pv, f"row swap with {g}"))
        return out

    # ---- 1. hard plausibility: implausible values leave the identity pool --- #
    implausible: set[str] = set()
    for fid, r in by_fid.items():
        cv = canon.get(fid)
        lim = limits_for(fid)
        if cv is None or lim is None:
            continue
        if cv < 0 and fid != "anion_gap":
            implausible.add(fid)
            note(r, f"negative value is impossible for {fid}", factor=0.4, force_review=True)
            summary["plausibility_violations"].append(fid)
        elif not (lim[0] <= cv <= lim[1]):
            implausible.add(fid)
            summary["plausibility_violations"].append(fid)
    pool = {f: v for f, v in canon.items() if f not in implausible}

    # ---- 2. flag vs value vs printed interval ------------------------------ #
    for fid, r in by_fid.items():
        m = _flag_check(r, canon.get(fid))
        if m:
            summary["flag_mismatches"].append(fid)
            note(r, "report flag mismatch: " + m, factor=0.75, force_review=True)

    # ---- 3. identities on the plausible pool -------------------------------- #
    base = evaluate(pool)
    summary["checks_run"] = len(base)
    failed = {n: m for n, (ok, m) in base.items() if not ok}
    passing = {n for n, (ok, _) in base.items() if ok}
    summary["checks_passed"] = len(passing)

    def repair_ok(fid: str, ccv: float, must_fix: Iterable[str]) -> bool:
        trial = dict(pool)
        trial[fid] = ccv
        res = evaluate(trial)
        for n in must_fix:
            if n not in res or not res[n][0]:      # must be computable AND pass
                return False
        return all(res.get(n, (True, ""))[0] for n in passing)

    # ---- 4. culprit search ---------------------------------------------------- #
    involved: set[str] = set()
    for n in failed:
        involved.update(f for f in check_by_name[n].fields if f in pool)
    # (fid) -> (canonical, printed, reason, n_failed_fixed, typical_distance)
    fixers: dict[str, tuple[float, float, str, int, float]] = {}
    for fid in sorted(involved):
        r = by_fid[fid]
        my_failed = [n for n in failed if fid in check_by_name[n].fields]
        if not my_failed:
            continue
        cands = candidates_for(fid, r)
        cands.extend(swap_candidates(fid, r, my_failed))
        # derived value implied by the failed identity (odd-one-out repair)
        for n in my_failed:
            fn = DERIVE.get(n, {}).get(fid)
            if fn is None:
                continue
            try:
                dv = float(fn(pool))
            except Exception:
                continue
            if not math.isfinite(dv) or dv <= 0:
                continue
            lim = limits_for(fid)
            if lim and not (lim[0] <= dv <= lim[1]):
                continue
            # a digit-level candidate within 6 % of the derived value is the
            # better story (it names the misread glyph); else use derived
            near = [c for c in cands if abs(c[0] - dv) <= 0.06 * dv]
            if near:
                cands = near + [c for c in cands if c not in near]
            else:
                cands.append((dv, printed_from_canonical(fid, r, dv), f"value implied by {n.replace('_', ' ')}"))
        for ccv, printed, why in cands:
            if repair_ok(fid, ccv, my_failed):
                fixers[fid] = (ccv, printed, why, len(my_failed), _typ_dist(fid, ccv))
                break

    # resolve each failed check: a unique fixer, or a clearly more plausible one
    culprit_of: dict[str, str] = {}
    for n in failed:
        fields_here = [f for f in check_by_name[n].fields if f in pool]
        here = [f for f in fields_here if f in fixers]
        chosen = None
        if len(here) == 1:
            chosen = here[0]
        elif len(here) > 1:
            ranked = sorted(here, key=lambda f: (-fixers[f][3], fixers[f][4]))
            a, b = ranked[0], ranked[1]
            fa, fb = fixers[a], fixers[b]
            if fa[3] > fb[3] or fa[4] <= 0.5 * fb[4] or (fa[4] < 0.35 and fb[4] > 1.0):
                chosen = a
        culprit_of[n] = chosen

    # ---- 4b. joint minimal-cost repair ------------------------------------- #
    # When no single value explains the failures (two misreads in one panel,
    # or one misread that breaks identities a second value also shares) search
    # pairs of fields for the cheapest combined edit that restores EVERY
    # identity. Cost = edit-type prior (decimal shift < missing point < glyph
    # < derived) + a small distance-from-typical term. The answer is accepted
    # only when it is unique (second-best costs >= 0.5 more); otherwise the
    # alternatives are reported and the fields stay suspects.
    _EDIT_COST = (("decimal shift", 1.0), ("missing decimal", 1.2), ("transposition", 2.0), ("glyph", 1.5), ("row swap", 2.0), ("implied by", 2.5))

    def edit_cost(why: str) -> float:
        for key, c in _EDIT_COST:
            if key in why:
                return c
        return 3.0

    summary["joint_repairs"] = []
    summary["ambiguous"] = []
    joint_fields: set[str] = set()
    unresolved = [n for n, c in culprit_of.items() if c is None]
    # cost of the greedy per-identity assignment, if it is jointly valid
    greedy = {c: fixers[c] for c in culprit_of.values() if c}
    greedy_cost = float("inf")
    if greedy and not unresolved:
        trial = dict(pool)
        trial.update({f: fx[0] for f, fx in greedy.items()})
        res = evaluate(trial)
        if all(res.get(n, (False, ""))[0] for n in failed) and all(res.get(n, (True, ""))[0] for n in passing):
            greedy_cost = sum(edit_cost(fx[2]) + 0.1 * fx[4] for fx in greedy.values())
    if failed and len(involved) >= 2 and (unresolved or len(greedy) >= 2):
        fields_u = sorted(involved)
        cand_map: dict[str, list[tuple[float, float, str]]] = {}
        for f in fields_u:
            cs = list(candidates_for(f, by_fid[f])[:8])
            cs.extend(swap_candidates(f, by_fid[f], [n for n in failed if f in check_by_name[n].fields])[:4])
            for n in failed:
                fn = DERIVE.get(n, {}).get(f)
                if fn is None:
                    continue
                try:
                    dv = float(fn(pool))
                except Exception:
                    continue
                if not math.isfinite(dv) or dv <= 0:
                    continue
                lim = limits_for(f)
                if lim and not (lim[0] <= dv <= lim[1]):
                    continue
                cs.append((dv, printed_from_canonical(f, by_fid[f], dv), f"value implied by {n.replace('_', ' ')}"))
            cand_map[f] = cs
        solutions: list[tuple[float, tuple]] = []

        def try_combo(combo: tuple) -> None:
            trial = dict(pool)
            for f, cand in combo:
                trial[f] = cand[0]
            res = evaluate(trial)
            if not all(res.get(n, (False, ""))[0] for n in failed):
                return
            if not all(res.get(n, (True, ""))[0] for n in passing):
                return
            # residual: how far each edited value sits from what the
            # (now-consistent) panel derives for it - separates the exact
            # repair from one that merely squeaks inside tolerance
            resid = 0.0
            n_res = 0
            for f, cand in combo:
                for n in failed:
                    fn = DERIVE.get(n, {}).get(f)
                    if fn is None:
                        continue
                    try:
                        dv = float(fn(trial))
                    except Exception:
                        continue
                    if math.isfinite(dv) and dv > 0:
                        resid += abs(dv - cand[0]) / dv
                        n_res += 1
            resid = resid / n_res if n_res else 0.0
            cost = (sum(edit_cost(c[2]) for _, c in combo)
                    + 0.1 * sum(_typ_dist(f, c[0]) for f, c in combo)
                    + 6.0 * resid)
            solutions.append((cost, combo))

        for a, b in itertools.combinations(fields_u, 2):
            for ca in cand_map[a]:
                for cb in cand_map[b]:
                    try_combo(((a, ca), (b, cb)))
        # three simultaneous misreads: only when the search stays small and
        # no pair explains the panel (a triple is never preferred over a pair
        # of equal story because it costs one more edit)
        if not solutions and len(fields_u) <= 6 and len(failed) >= 2:
            for a, b, c in itertools.combinations(fields_u, 3):
                for ca in cand_map[a][:5]:
                    for cb in cand_map[b][:5]:
                        for cc in cand_map[c][:5]:
                            try_combo(((a, ca), (b, cb), (c, cc)))
        solutions.sort(key=lambda t: (t[0], t[1][0][0], t[1][1][0]))
        if solutions:
            best_cost, best = solutions[0]
            second = solutions[1][0] if len(solutions) > 1 else float("inf")
            tied = [sol for c, sol in solutions if c - best_cost < 0.5]
            best_fields = frozenset(f for f, _ in best)
            # near-ties that name the SAME two fields are one story (which
            # two values are wrong) with alternative readings; different
            # field sets are a genuine ambiguity.
            unique = all(frozenset(f for f, _ in sol) == best_fields for sol in tied)
            beats_greedy = best_cost + 0.5 <= greedy_cost
            if unique and (unresolved or beats_greedy):
                for n in list(culprit_of):
                    culprit_of[n] = None          # joint story replaces the greedy one
                unresolved = list(culprit_of)
                for f, (ccv, printed, why) in best:
                    joint_fields.add(f)
                    alts = []
                    for sol in tied[1:]:
                        for g, (_, pr, _w) in sol:
                            if g == f and abs(pr - printed) > 1e-9 and _fmt(pr) not in alts:
                                alts.append(_fmt(pr))
                    suggest(by_fid[f], f, printed, why)
                    if alts:
                        by_fid[f]["alternative_values"] = alts
                    note(by_fid[f], f"inconsistent with the panel; together with {len(best) - 1} other value(s), reading "
                                    f"{_fmt(printed):g} instead of {by_fid[f].get('value')} ({why}) restores every "
                                    f"identity in the panel (joint minimal-edit repair"
                                    + (f"; also admissible: {', '.join(f'{x:g}' for x in alts)}" if alts else "")
                                    + ")",
                         factor=0.45, force_review=True)
                    if f not in summary["joint_repairs"]:
                        summary["joint_repairs"].append(f)
                for n in unresolved:
                    culprit_of[n] = "__joint__"
            elif unresolved:
                summary["ambiguous"].append({
                    "checks": unresolved,
                    "fields": fields_u,
                    "alternatives": [
                        {"cost": round(c, 2),
                         "edits": {f: {"value": _fmt(pr), "reason": why} for f, (_, pr, why) in sol}}
                        for c, sol in solutions[:3]],
                })

    for n, msg in failed.items():
        fields_here = [f for f in check_by_name[n].fields if f in pool]
        chosen = culprit_of[n]
        if chosen == "__joint__":
            for f in fields_here:
                if f not in joint_fields:
                    note(by_fid[f], f"took part in a failed identity ({n}) that is explained by a joint repair of "
                                    f"{', '.join(sorted(joint_fields))}; this value itself is not implicated",
                         term="identity_exonerated")
                    if f not in summary["exonerated"]:
                        summary["exonerated"].append(f)
            summary["failed"].append({"check": n, "message": msg, "fields": fields_here,
                                      "culprit": sorted(joint_fields), "repairable_by": sorted(joint_fields)})
            continue
        summary["failed"].append({"check": n, "message": msg, "fields": fields_here,
                                  "culprit": chosen, "repairable_by": [f for f in fields_here if f in fixers]})
        for f in fields_here:
            r = by_fid[f]
            if chosen == f:
                ccv, printed, why, _, _ = fixers[f]
                suggest(r, f, printed, why)
                note(r, f"inconsistent with the panel ({msg}); reading {_fmt(printed):g} instead of "
                        f"{r.get('value')} ({why}) restores every identity this value takes part in",
                     factor=0.45, force_review=True)
            elif chosen is not None:
                note(r, f"took part in a failed identity ({n}) that is explained by {chosen}; "
                        f"this value itself is not implicated", term="identity_exonerated")
                if f not in summary["exonerated"]:
                    summary["exonerated"].append(f)
            else:
                note(r, f"inconsistent with the panel ({msg}); no single value explains it - verify "
                        f"{', '.join(fields_here)}", factor=0.7, force_review=True)
                if f not in summary["suspects"]:
                    summary["suspects"].append(f)

    # ---- 5. implausible values: propose the reading the panel supports ------- #
    for fid in sorted(implausible):
        r = by_fid[fid]
        lim = limits_for(fid)
        cands = candidates_for(fid, r)
        my_checks = [c.name for c in CHECKS if fid in c.fields]
        best = None
        scored = []
        for ccv, printed, why in cands:
            trial = dict(pool)
            trial[fid] = ccv
            res = evaluate(trial)
            computable = [n for n in my_checks if n in res]
            agree = all(res[n][0] for n in computable)
            if computable and not agree:
                continue
            lo, hi = r.get("report_range_low"), r.get("report_range_high")
            if lo is not None and hi is not None and hi > lo and not (lo / 3.0 <= printed <= hi * 3.0):
                continue
            scored.append((0 if computable else 1, _typ_dist(fid, ccv), ccv, printed, why, bool(computable)))
        if scored:
            scored.sort()
            _, _, ccv, printed, why, confirmed = scored[0]
            best = (printed, why + (" - confirmed by the panel's own arithmetic" if confirmed else ""))
        msg = (f"{fid} = {r.get('value')} {r.get('unit') or ''} is outside the physiologically possible "
               f"range {lim[0]:g}-{lim[1]:g} (canonical units)")
        if best:
            suggest(r, fid, best[0], best[1])
            msg += f"; {_fmt(best[0]):g} ({best[1]}) would be plausible - confirm against the original"
        elif fid not in summary["suspects"]:
            summary["suspects"].append(fid)
        note(r, msg, factor=0.35, force_review=True)

    # ---- 6. corroboration ---------------------------------------------------- #
    for n in passing:
        chk = check_by_name[n]
        if not chk.corroborates:
            continue
        for f in chk.fields:
            r = by_fid.get(f)
            if r is None or f not in pool or f in involved:
                continue
            r.setdefault("corroborated_by", [])
            if n not in r["corroborated_by"]:
                r["corroborated_by"].append(n)
                _conf.add_evidence(r, "identity_corroborated", note=n)
            if f not in summary["corroborated"]:
                summary["corroborated"].append(f)

    for r in results:
        r.setdefault("corroborated_by", [])
        r.setdefault("suggested_value", None)
    return summary
