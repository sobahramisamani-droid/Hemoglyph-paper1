"""v8: MELD-Na / PLR derived patterns and confidence-band presentation field."""
import analyse_gidlines as ag

CTX = {"age_years": 58, "sex_at_birth": "male", "encounter": "icu"}
LIVER = {"bilirubin_total": {"value": 4.2, "unit": "mg/dL"}, "inr": {"value": 2.1, "unit": "ratio"},
         "creatinine": {"value": 1.8, "unit": "mg/dL"}, "sodium": {"value": 128, "unit": "mmol/L"}}

def _pat(report, pid):
    return next((p for p in report["derived_patterns"] if p["pattern_id"] == pid), None)

def test_meld_na_value_and_prognostic_only():
    r = ag.ClinicalRuleEngine().interpret(LIVER, None, CTX).to_dict()
    p = _pat(r, "meld_na")
    assert p is not None and p["value"] == 30 and p["significance"] == "high" and p["supports"] == []

def test_meld_not_computed_on_normal_liver():
    obs = dict(LIVER); obs["bilirubin_total"] = {"value": 0.8, "unit": "mg/dL"}; obs["inr"] = {"value": 1.1, "unit": "ratio"}
    r = ag.ClinicalRuleEngine().interpret(obs, None, CTX).to_dict()
    assert _pat(r, "meld_na") is None

def test_plr_only_above_200_and_low_significance():
    obs = {"platelet_count": {"value": 400, "unit": "10^9/L"}, "white_blood_cell_count": {"value": 10, "unit": "10^9/L"},
           "lymphocytes": {"value": 8, "unit": "%"}, "neutrophils": {"value": 85, "unit": "%"}}
    r = ag.ClinicalRuleEngine().interpret(obs, None, CTX).to_dict()
    p = _pat(r, "plr_high")
    assert p is not None and p["value"] == 500 and p["significance"] == "low" and p["supports"] == []

def test_confidence_band_present_and_monotone():
    r = ag.ClinicalRuleEngine().interpret(LIVER, None, CTX).to_dict()
    order = {"high": 3, "moderate": 2, "low": 1, "consider": 0}
    dx = r["differential_diagnosis"]
    assert dx and all("confidence_band" in d and "concise" in d for d in dx)
    for d in dx:
        p = d["probability"]
        exp = "high" if p >= .7 else "moderate" if p >= .6 else "low" if p >= .5 else "consider"
        if d.get("evidence_state") != "refuted":
            assert d["confidence_band"] == exp
