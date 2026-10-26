"""ESL extension 11 (2026-10-23): temporal module (11-T) and clinical-context layer (11-C).

Every test also asserts the OFF-state: without a series / without context the
engine output is the pre-existing labs-only behaviour (no hallucinated
trajectory, no prior-driven comorbidity)."""
import os, sys, logging
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)
import analyse_gidlines as ag  # noqa: E402


@pytest.fixture(scope="module")
def E():
    e = ag.ClinicalRuleEngine(); e._reasoner.max_differential = 40
    return e


BASE = {"sodium": {"value": 138, "unit": "mmol/L"}, "potassium": {"value": 4.4, "unit": "mmol/L"}, "chloride": {"value": 102, "unit": "mmol/L"},
        "bicarbonate": {"value": 22, "unit": "mmol/L"}, "blood_urea_nitrogen": {"value": 28, "unit": "mg/dL"}, "glucose": {"value": 110, "unit": "mg/dL"},
        "hemoglobin": {"value": 13.1, "unit": "g/dL"}, "white_blood_cell_count": {"value": 8.1, "unit": "10^9/L"}, "platelet_count": {"value": 230, "unit": "10^9/L"},
        "creatinine": {"value": 1.0, "unit": "mg/dL"}}
CTX = {"age_years": 64, "sex_at_birth": "male"}


def run(E, obs, ctx=CTX):
    return E.interpret(obs, None, ctx).to_dict()


def prob(rep, did):
    return max([d["probability"] for d in rep["differential_diagnosis"] if d["disease_id"] == did] or [0.0])


def fired(rep, sid):
    return any(h["syndrome_id"] == sid for h in rep["expert_syndromes"])


# ----------------------------------------------------------------- 11-T
def test_series_normaliser_accepts_dicts_and_pairs():
    s = ag._normalise_series([{"t_hours": 5, "value": 1.2}, [0, 0.9], {"offset_minutes": 120, "value": 1.0}])
    assert [p["t_hours"] for p in s] == [0.0, 2.0, 5.0]
    assert ag._normalise_series("junk") == []


def test_temporal_reducer_keys():
    out = ag._esl_temporal({"cr": [(0.0, 0.9), (14.0, 1.2), (30.0, 1.6)]})
    assert out["cr_rise48"] == pytest.approx(0.7) and out["cr_ratio_max"] == pytest.approx(1.6 / 0.9)
    assert out["cr_first"] == 0.9 and out["cr_last"] == 1.6 and out["cr_span_h"] == 30.0


def test_kdigo_rise_vs_static_creatinine(E):
    static = run(E, {**BASE, "creatinine": {"value": 1.6, "unit": "mg/dL"}})
    dyn = run(E, {**BASE, "creatinine": {"value": 0.9, "unit": "mg/dL", "series": [[0, 0.9], [14, 1.2], [30, 1.6]]}})
    assert not fired(static, "aki_kdigo_creatinine_rise") and prob(static, "acute_kidney_injury") <= 0.62  # undetermined chronicity
    assert fired(dyn, "aki_kdigo_creatinine_rise") and prob(dyn, "acute_kidney_injury") >= 0.80
    assert prob(dyn, "chronic_kidney_disease") < prob(dyn, "acute_kidney_injury")
    assert dyn["temporal_findings"][0]["id"] == "aki_kdigo_creatinine_rise"


def test_kdigo_small_rise_at_low_creatinine_does_not_fire(E):
    rep = run(E, {**BASE, "creatinine": {"value": 0.5, "unit": "mg/dL", "series": [[0, 0.5], [20, 0.8]]}})
    assert not fired(rep, "aki_kdigo_creatinine_rise")


def test_troponin_dynamic_vs_flat(E):
    rise = run(E, {**BASE, "high_sensitivity_troponin_t": {"value": 9, "unit": "ng/L", "series": [[0, 9], [3, 48], [6, 160]]}})
    assert fired(rise, "acute_myocardial_injury_dynamic_troponin") and prob(rise, "acute_myocardial_injury") >= 0.9
    flat = run(E, {**BASE, "creatinine": {"value": 2.4, "unit": "mg/dL"}, "high_sensitivity_troponin_t": {"value": 38, "unit": "ng/L", "series": [[0, 38], [3, 41], [6, 39]]}})
    assert fired(flat, "chronic_myocardial_injury_flat_troponin")
    assert prob(flat, "chronic_myocardial_injury") > prob(flat, "acute_myocardial_injury")
    assert not fired(flat, "myocardial_injury_single")  # static single-value rule yields to the trajectory


def test_troponin_conventional_units_series(E):
    rep = run(E, {**BASE, "troponin_i": {"value": 0.01, "unit": "ng/mL", "series": [[0, 0.01], [3, 0.08], [6, 0.35]]}})
    assert fired(rep, "acute_myocardial_injury_dynamic_troponin")


def test_lactate_clearance_and_persistence(E):
    pers = run(E, {**BASE, "creatinine": {"value": 1.9, "unit": "mg/dL"}, "lactate": {"value": 5.1, "unit": "mmol/L", "series": [[0, 5.1], [3, 5.4], [6, 4.9]]}})
    assert fired(pers, "lactate_non_clearance") and prob(pers, "lactic_acidosis") >= 0.75
    clr = run(E, {**BASE, "lactate": {"value": 5.1, "unit": "mmol/L", "series": [[0, 5.1], [3, 3.6], [6, 2.4]]}})
    assert fired(clr, "lactate_clearing") and not fired(clr, "lactate_non_clearance")


def test_acute_blood_loss_hb_fall(E):
    rep = run(E, {**BASE, "blood_urea_nitrogen": {"value": 45, "unit": "mg/dL"}, "hemoglobin": {"value": 12.5, "unit": "g/dL", "series": [[0, 12.5], [10, 10.1], [20, 9.2]]}})
    assert fired(rep, "acute_blood_loss_hb_fall") and prob(rep, "acute_blood_loss_anemia") >= 0.65
    slow = run(E, {**BASE, "hemoglobin": {"value": 12.5, "unit": "g/dL", "series": [[0, 12.5], [10, 12.0], [20, 11.6]]}})
    assert not fired(slow, "acute_blood_loss_hb_fall")


def test_hit_requires_heparin_context(E):
    obs = {**BASE, "platelet_count": {"value": 240, "unit": "10^9/L", "series": [[0, 240], [72, 150], [120, 85]]}}
    no_ctx = run(E, obs)
    assert not fired(no_ctx, "hit_platelet_fall_on_heparin")
    hep = run(E, obs, {**CTX, "current_medications": ["heparin 5000 units sq"]})
    assert fired(hep, "hit_platelet_fall_on_heparin") and prob(hep, "heparin_induced_thrombocytopenia") >= 0.8


def test_dic_consumptive_fall(E):
    rep = run(E, {**BASE, "international_normalized_ratio": {"value": 1.9, "unit": "1"}, "platelet_count": {"value": 210, "unit": "10^9/L", "series": [[0, 210], [24, 120], [40, 70]]}})
    assert fired(rep, "consumptive_platelet_fall_dic")


def test_sodium_overcorrection_warning_is_guard(E):
    rep = run(E, {**BASE, "sodium": {"value": 118, "unit": "mmol/L", "series": [[0, 118], [12, 126], [20, 129]]}})
    h = [x for x in rep["expert_syndromes"] if x["syndrome_id"] == "hyponatremia_overcorrection"]
    assert h and h[0]["guard"] and h[0]["dx"] == [] and "osmotic demyelination" in h[0]["note"]
    assert rep["temporal_findings"]
    safe = run(E, {**BASE, "sodium": {"value": 118, "unit": "mmol/L", "series": [[0, 118], [12, 121], [24, 124]]}})
    assert not fired(safe, "hyponatremia_overcorrection")


def test_series_in_unconvertible_unit_is_ignored(E):
    rep = run(E, {**BASE, "creatinine": {"value": 0.9, "unit": "mg/dL", "series": [{"t_hours": 0, "value": 80, "unit": "furlongs"}, {"t_hours": 30, "value": 140, "unit": "furlongs"}]}})
    assert not fired(rep, "aki_kdigo_creatinine_rise")


def test_series_umol_converted(E):
    rep = run(E, {**BASE, "creatinine": {"value": 80, "unit": "umol/L", "series": [{"t_hours": 0, "value": 80}, {"t_hours": 30, "value": 150}]}})
    assert fired(rep, "aki_kdigo_creatinine_rise")


# ----------------------------------------------------------------- 11-C
def test_documented_entities_mapping():
    ctx = ag.ClinicalContext.from_any({"age_years": 70, "sex_at_birth": "female", "known_conditions": ["Diabetes insulin dependent diabetes", "renal failure - hemodialysis", "No Health Problems"],
                                        "current_medications": ["levothyroxine 50 mcg", "metformin"]})
    doc = ag._documented_entities(ctx)
    assert set(doc) == {"diabetes_mellitus", "chronic_kidney_disease", "hypothyroidism"}
    assert ag._documented_entities(None) == {}


def test_documented_diabetes_confirmed_by_glucose(E):
    obs = {**BASE, "glucose": {"value": 152, "unit": "mg/dL"}}
    off = run(E, obs)
    assert prob(off, "diabetes_mellitus") < 0.5 and not off["clinical_context_applied"]
    on = run(E, obs, {**CTX, "known_conditions": ["insulin dependent diabetes"]})
    assert prob(on, "diabetes_mellitus") >= 0.80
    assert on["clinical_context_applied"][0]["action"] == "confirmed"


def test_documented_without_lab_support_stays_below_operating_point(E):
    on = run(E, BASE, {**CTX, "known_conditions": ["CHF", "COPD  - moderate"]})
    for did in ("heart_failure", "copd"):
        assert prob(on, did) == pytest.approx(0.49, abs=1e-6)
        e = [d for d in on["differential_diagnosis"] if d["disease_id"] == did][0]
        assert e["evidence_state"] == "documented_history"
    assert {c["action"] for c in on["clinical_context_applied"]} == {"listed_documented"}


def test_documented_ckd_resolves_chronicity(E):
    obs = {**BASE, "creatinine": {"value": 1.6, "unit": "mg/dL"}}
    on = run(E, obs, {**CTX, "known_conditions": ["renal insufficiency - creatinine 1-2"]})
    assert prob(on, "chronic_kidney_disease") >= 0.80 and prob(on, "acute_kidney_injury") < prob(on, "chronic_kidney_disease")
    # documented CKD + KDIGO rise = AKI on CKD: both stay established
    both = run(E, {**BASE, "creatinine": {"value": 1.6, "unit": "mg/dL", "series": [[0, 1.6], [30, 2.6]]}}, {**CTX, "known_conditions": ["renal insufficiency - creatinine 1-2"]})
    assert prob(both, "acute_kidney_injury") >= 0.80 and prob(both, "chronic_kidney_disease") >= 0.75


def test_negated_history_is_ignored(E):
    on = run(E, BASE, {**CTX, "known_conditions": ["No Health Problems", "denies diabetes"]})
    assert not on["clinical_context_applied"]


def test_warfarin_explains_inr(E):
    obs = {**BASE, "international_normalized_ratio": {"value": 2.6, "unit": "1"}}
    off = run(E, obs); on = run(E, obs, {**CTX, "current_medications": ["warfarin 5 mg"]})
    assert prob(off, "elevated_inr_pattern") >= 0.75 and prob(on, "elevated_inr_pattern") <= 0.6
    assert fired(on, "warfarin_inr_explained")
    high = run(E, {**BASE, "international_normalized_ratio": {"value": 5.2, "unit": "1"}}, {**CTX, "current_medications": ["coumadin"]})
    assert prob(high, "warfarin_over_anticoagulation") >= 0.85


def test_metformin_lactic_acidosis(E):
    obs = {**BASE, "creatinine": {"value": 2.8, "unit": "mg/dL"}, "lactate": {"value": 7.2, "unit": "mmol/L"}, "bicarbonate": {"value": 12, "unit": "mmol/L"}}
    off = run(E, obs); on = run(E, obs, {**CTX, "current_medications": ["metformin 1000 mg"]})
    assert prob(off, "lactic_acidosis_metformin_associated") < 0.5 and prob(on, "lactic_acidosis_metformin_associated") >= 0.85


def test_statin_muscle_injury(E):
    obs = {**BASE, "creatine_kinase_total": {"value": 4800, "unit": "U/L"}}
    on = run(E, obs, {**CTX, "current_medications": ["atorvastatin 40 mg"]})
    assert fired(on, "statin_associated_muscle_injury_ctx") and prob(on, "statin_associated_muscle_injury") >= 0.7


def test_medication_only_implication_not_listed_without_labs(E):
    on = run(E, BASE, {**CTX, "current_medications": ["metformin"]})
    assert prob(on, "diabetes_mellitus") == 0.0
    assert on["clinical_context_applied"][0]["action"] == "not_listed_unsupported"
    empty = run(E, {}, {"age_years": 29, "sex_at_birth": "female", "pregnant": True, "known_conditions": ["asthma"]})
    assert not empty["differential_diagnosis"]


def test_healthy_panel_with_context_adds_nothing_above_operating_point(E):
    on = run(E, BASE, {**CTX, "known_conditions": ["hypertension requiring treatment", "CHF"], "current_medications": ["warfarin", "metformin", "heparin"]})
    assert all(d["probability"] < 0.5 for d in on["differential_diagnosis"] if d["disease_id"] in ("hypertension", "heart_failure", "diabetes_mellitus",
                                                                                                "heparin_induced_thrombocytopenia", "lactic_acidosis_metformin_associated", "warfarin_over_anticoagulation"))


def test_documented_dialysis_does_not_bury_hyperkalemia(E):
    obs = {**BASE, "creatinine": {"value": 6.8, "unit": "mg/dL"}, "potassium": {"value": 6.6, "unit": "mmol/L"}, "bicarbonate": {"value": 18, "unit": "mmol/L"}}
    on = run(E, obs, {**CTX, "known_conditions": ["renal failure - hemodialysis", "CHF"]})
    ranks = {d["disease_id"]: d["rank"] for d in on["differential_diagnosis"]}
    assert prob(on, "hyperkalemia") >= 0.7 and ranks["hyperkalemia"] <= 5
    assert prob(on, "chronic_kidney_disease") > prob(on, "acute_kidney_injury")
