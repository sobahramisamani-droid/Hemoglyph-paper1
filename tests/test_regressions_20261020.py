"""Regression tests for defects found by the retrospective-pipeline dry run
(2026-10-20) and for the solver's transposition / row-swap edit candidates.

1. A sub-type carried by *insufficient* evidence must not demote a strongly
   supported parent term (overt hyperthyroidism vs Graves' without TRAb).
2. An 'acute cause' candidate that is itself *insufficient* must not cap a
   supported AKI entry.
3. The consistency solver repairs an adjacent-digit transposition and does
   not touch a clean panel.
"""
from __future__ import annotations
import os, sys, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.disable(logging.CRITICAL)
import pytest
import analyse_gidlines as ag
from ocr_consistency import validate_results


@pytest.fixture(scope="module")
def engine():
    return ag.ClinicalRuleEngine()


def _rank(rep, disease_id):
    for d in rep["differential_diagnosis"]:
        if d["disease_id"] == disease_id:
            return d["rank"], d
    return None, None


def test_overt_hyperthyroidism_not_demoted_by_insufficient_graves(engine):
    obs = {"thyroid_stimulating_hormone": {"value": 0.01, "unit": "uIU/mL"},
           "free_thyroxine": {"value": 4.1, "unit": "ng/dL"},
           "sodium": {"value": 142, "unit": "mmol/L"}, "potassium": {"value": 3.7, "unit": "mmol/L"},
           "creatinine": {"value": 0.8, "unit": "mg/dL"}, "glucose": {"value": 101, "unit": "mg/dL"},
           "hemoglobin": {"value": 12.2, "unit": "g/dL"}, "white_blood_cell_count": {"value": 6.4, "unit": "10*3/uL"},
           "platelets": {"value": 257, "unit": "10*3/uL"}, "calcium_total": {"value": 11.0, "unit": "mg/dL"},
           "alkaline_phosphatase": {"value": 149, "unit": "U/L"}, "alanine_aminotransferase": {"value": 30, "unit": "U/L"}}
    rep = engine.interpret(obs, None, {"age_years": 60, "sex_at_birth": "female"}).to_dict()
    rank, d = _rank(rep, "hyperthyroidism")
    assert rank == 1, rep["differential_diagnosis"][:5]
    assert d["evidence_state"] == "supported" and d["probability"] >= 0.80
    g_rank, g = _rank(rep, "graves_disease")
    if g is not None and g["evidence_state"] != "supported":
        assert g_rank > rank


def test_supported_aki_not_capped_by_insufficient_sepsis(engine):
    obs = {"creatinine": {"value": 4.4, "unit": "mg/dL"}, "blood_urea_nitrogen": {"value": 71, "unit": "mg/dL"},
           "potassium": {"value": 5.9, "unit": "mmol/L"}, "sodium": {"value": 147, "unit": "mmol/L"},
           "bicarbonate": {"value": 17.9, "unit": "mmol/L"}, "chloride": {"value": 112, "unit": "mmol/L"},
           "glucose": {"value": 109, "unit": "mg/dL"}, "hemoglobin": {"value": 11.7, "unit": "g/dL"},
           "white_blood_cell_count": {"value": 8.6, "unit": "10*3/uL"}, "platelets": {"value": 200, "unit": "10*3/uL"},
           "calcium_total": {"value": 8.1, "unit": "mg/dL"}, "phosphate": {"value": 5.7, "unit": "mg/dL"}}
    rep = engine.interpret(obs, None, {"age_years": 60, "sex_at_birth": "male"}).to_dict()
    rank, d = _rank(rep, "acute_kidney_injury")
    assert rank is not None and rank <= 3, rep["differential_diagnosis"][:5]
    assert d["probability"] >= 0.70
    # nothing 'insufficient' may sit above a supported renal entry here
    for x in rep["differential_diagnosis"][: rank - 1]:
        assert x["evidence_state"] != "insufficient", x


def _rec(fid, value, unit):
    return {"feature_id": fid, "value": value, "unit": unit, "flag": None, "report_range_low": None,
            "report_range_high": None, "confidence": 0.9, "requires_confirmation": False,
            "suggested_action": "accept", "warnings": [], "original_value": value}


def _cbc(hb, hct, rbc):
    return [_rec("hemoglobin", round(hb, 1), "g/dL"), _rec("hematocrit", round(hct, 1), "%"),
            _rec("red_blood_cell_count", round(rbc, 2), "10^6/uL"),
            _rec("mean_corpuscular_volume", round(hct / rbc * 10, 1), "fL"),
            _rec("mean_corpuscular_hemoglobin", round(hb / rbc * 10, 1), "pg"),
            _rec("mean_corpuscular_hemoglobin_concentration", round(hb / hct * 100, 1), "g/dL")]


def test_solver_repairs_adjacent_digit_transposition():
    panel = _cbc(14.2, 42.6, 4.73)
    panel[0]["value"] = panel[0]["original_value"] = 41.2          # 14.2 -> 41.2 (out of hard limits? no: Hb max is higher) 
    s = validate_results(panel)
    hb = panel[0]
    assert "hemoglobin" in s["suspects"] or hb.get("suggested_value") is not None
    assert hb.get("suggested_value") == 14.2, hb
    assert hb["requires_confirmation"] is True
    assert all(r.get("suggested_value") is None for r in panel[1:])


def test_solver_leaves_clean_panel_alone():
    panel = _cbc(13.5, 40.5, 4.5)
    s = validate_results(panel)
    assert s["suspects"] == [] and not s["repairs_suggested"]
    assert all(r.get("suggested_value") is None for r in panel)


# ---------------------------------------------------------------- healthy-panel behaviour
# Found by eval/deep_audit.py: before the pattern gates below, 200/200 fully
# normal routine panels returned a top candidate with p >= 0.5 (AKI 55 % in
# 138, cholestasis in 55), driven by ratios computed on normal values
# (R ratio, BUN/Cr, anion gap without acidosis, delta ratio, De Ritis).

_HEALTHY_F = {"hemoglobin": (13.4, "g/dL"), "hematocrit": (40.5, "%"), "red_blood_cell_count": (4.6, "10^6/uL"),
              "mean_corpuscular_volume": (88, "fL"), "white_blood_cell_count": (6.8, "10*3/uL"), "platelets": (255, "10*3/uL"),
              "glucose": (88, "mg/dL"), "creatinine": (0.72, "mg/dL"), "blood_urea_nitrogen": (18.5, "mg/dL"),
              "sodium": (141, "mmol/L"), "potassium": (4.2, "mmol/L"), "chloride": (102, "mmol/L"), "bicarbonate": (25, "mmol/L"),
              "calcium_total": (9.4, "mg/dL"), "alanine_aminotransferase": (14, "U/L"), "aspartate_aminotransferase": (31, "U/L"),
              "alkaline_phosphatase": (70, "U/L"), "bilirubin_total": (0.6, "mg/dL"), "albumin": (4.4, "g/dL"), "total_cholesterol": (170, "mg/dL")}


def test_normal_routine_panel_yields_no_supported_candidate(engine):
    obs = {k: {"value": v, "unit": u} for k, (v, u) in _HEALTHY_F.items()}
    rep = engine.interpret(obs, None, {"age_years": 40, "sex_at_birth": "female"}).to_dict()
    d = rep["differential_diagnosis"]
    assert all(x["evidence_state"] != "supported" for x in d), d[:5]
    assert all(x["probability"] < 0.40 for x in d), d[:5]
    pats = {p["pattern_id"] for p in rep["derived_patterns"]}
    for forbidden in ("liver_cholestatic", "liver_hepatocellular", "liver_mixed", "bun_cr_prerenal", "bun_cr_intrinsic",
                      "high_anion_gap", "hagma_plus_met_alkalosis", "nagd_plus_hagma", "de_ritis_high"):
        assert forbidden not in pats, forbidden


def test_pattern_gates_still_fire_on_true_abnormality():
    """The gates must not silence the ratios when they are indicated."""
    import analyse_gidlines as ag
    ctx = ag.ClinicalContext(age_years=50, sex_at_birth="male")
    p = {x.pattern_id for x in ag.tahlil_olgoo_haye_moshtagh({"alanine_aminotransferase": 30, "alkaline_phosphatase": 480, "bilirubin_total": 2.4}, ctx)}
    assert "liver_cholestatic" in p
    p = {x.pattern_id for x in ag.tahlil_olgoo_haye_moshtagh({"blood_urea_nitrogen": 62, "creatinine": 2.1}, ctx)}
    assert "bun_cr_prerenal" in p
    p = {x.pattern_id for x in ag.tahlil_olgoo_haye_moshtagh({"sodium": 138, "chloride": 100, "bicarbonate": 12}, ctx)}
    assert "high_anion_gap" in p
    p = {x.pattern_id for x in ag.tahlil_olgoo_haye_moshtagh({"aspartate_aminotransferase": 180, "alanine_aminotransferase": 60}, ctx)}
    assert "de_ritis_high" in p


# ---------------------------------------------------------------- unit invariance
def test_unit_invariance_si_vs_conventional(engine):
    """Same panel in SI and conventional units must give the same differential
    (audit 2026-10-20: Bayesian/fuzzy/pattern layers received raw values)."""
    pt = {"age_years": 45, "sex_at_birth": "female"}
    conv = {"hemoglobin": (9.1, "g/dL"), "mean_corpuscular_volume": (68, "fL"), "ferritin": (6, "ng/mL"),
            "serum_iron": (25, "ug/dL"), "total_iron_binding_capacity": (460, "ug/dL"), "platelets": (410, "10*3/uL"),
            "glucose": (312, "mg/dL"), "hemoglobin_a1c": (10.4, "%"), "creatinine": (1.1, "mg/dL")}
    si = {"hemoglobin": (91, "g/L"), "mean_corpuscular_volume": (68, "fL"), "ferritin": (6, "ug/L"),
          "serum_iron": (4.48, "umol/L"), "total_iron_binding_capacity": (82.3, "umol/L"), "platelets": (410, "10^9/L"),
          "glucose": (17.3, "mmol/L"), "hemoglobin_a1c": (90, "mmol/mol"), "creatinine": (97, "umol/L")}
    a = engine.interpret({f: {"value": v, "unit": u} for f, (v, u) in conv.items()}, None, pt).to_dict()["differential_diagnosis"]
    b = engine.interpret({f: {"value": v, "unit": u} for f, (v, u) in si.items()}, None, pt).to_dict()["differential_diagnosis"]
    assert [x["disease_id"] for x in a[:5]] == [x["disease_id"] for x in b[:5]], (a[:5], b[:5])
    pa = {x["disease_id"]: x["probability"] for x in a}; pb = {x["disease_id"]: x["probability"] for x in b}
    assert max(abs(pa[d] - pb.get(d, 0.0)) for d in pa) < 0.03


def test_normal_pregnancy_panel_not_called_septic(engine):
    obs = {"hemoglobin": (11.2, "g/dL"), "white_blood_cell_count": (11.8, "10*3/uL"), "platelets": (190, "10*3/uL"),
           "glucose": (84, "mg/dL"), "creatinine": (0.55, "mg/dL"), "blood_urea_nitrogen": (8, "mg/dL"),
           "alkaline_phosphatase": (190, "U/L"), "alanine_aminotransferase": (15, "U/L"), "albumin": (3.3, "g/dL"),
           "sodium": (136, "mmol/L"), "potassium": (3.9, "mmol/L"), "bicarbonate": (21, "mmol/L"), "chloride": (104, "mmol/L")}
    rep = engine.interpret({f: {"value": v, "unit": u} for f, (v, u) in obs.items()}, None,
                           {"age_years": 29, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 28}).to_dict()
    assert "high_anion_gap" not in {p["pattern_id"] for p in rep["derived_patterns"]}
    assert all(x["probability"] < 0.5 for x in rep["differential_diagnosis"]), rep["differential_diagnosis"][:4]
