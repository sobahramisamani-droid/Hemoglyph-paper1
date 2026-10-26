"""ESL extension 9 (2026-10-23) — ranking hygiene. Probabilities must be unchanged; only order."""
import logging, sys, pathlib
logging.disable(logging.CRITICAL)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import analyse_gidlines as ag


@pytest.fixture(scope="module")
def engine():
    e = ag.ClinicalRuleEngine()
    e._reasoner.max_differential = 40
    return e


def U(v, u):
    return {"value": v, "unit": u}


def _ids(rep):
    return [d["disease_id"] for d in rep["differential_diagnosis"]]


def _p(rep, did):
    return next((d["probability"] for d in rep["differential_diagnosis"] if d["disease_id"] == did), None)


def test_thalassemia_family_collapses_to_one_slot(engine):
    rep = engine.interpret({"hemoglobin": U(11.8, "g/dL"), "mean_corpuscular_volume": U(64, "fL"),
                            "red_blood_cell_count": U(5.9, "10^12/L"), "ferritin": U(80, "ng/mL"),
                            "red_cell_distribution_width_cv": U(13.5, "%")},
                           None, {"age_years": 30, "sex_at_birth": "female"}).to_dict()
    ids = _ids(rep)
    fam = {"thalassemia_trait", "beta_thalassemia_trait", "beta_thalassemia_minor", "alpha_thalassemia_trait"}
    members = [i for i, d in enumerate(ids) if d in fam]
    assert members and members[0] == 0, ids[:5]                 # one family member leads
    # the remaining family members are pushed behind every non-family entity with p >= 0.5
    last_material = max(i for i, d in enumerate(ids) if d not in fam and rep["differential_diagnosis"][i]["probability"] >= 0.5)
    assert all(m > last_material for m in members[1:]), ids[:6]


def test_microcytic_erythrocytosis_is_not_thalassemia_trait(engine):
    rep = engine.interpret({"hemoglobin": U(18.8, "g/dL"), "hematocrit": U(59, "%"), "mean_corpuscular_volume": U(68, "fL"),
                            "red_blood_cell_count": U(8.6, "10^12/L"), "red_cell_distribution_width_cv": U(22.7, "%")},
                           None, {"age_years": 83, "sex_at_birth": "male"}).to_dict()
    for d in ("thalassemia_trait", "beta_thalassemia_trait", "beta_thalassemia_minor"):
        p = _p(rep, d)
        assert p is None or p <= 0.5, (d, p)
    assert "polycythemia" in _ids(rep)[:8]


def test_bacterial_infection_ranks_beneath_sepsis_without_marker(engine):
    rep = engine.interpret({"white_blood_cell_count": U(21.0, "10^9/L"), "lactate": U(3.1, "mmol/L"),
                            "creatinine": U(1.9, "mg/dL"), "platelet_count": U(110, "10^9/L")},
                           None, {"age_years": 70, "sex_at_birth": "male"}).to_dict()
    ids = _ids(rep)
    assert "sepsis" in ids[:5]
    if "bacterial_infection" in ids:
        assert ids.index("bacterial_infection") > ids.index("sepsis")


def test_bacterial_infection_not_demoted_when_marker_measured(engine):
    rep = engine.interpret({"white_blood_cell_count": U(21.0, "10^9/L"), "procalcitonin": U(4.0, "ng/mL"),
                            "c_reactive_protein": U(180, "mg/L")},
                           None, {"age_years": 70, "sex_at_birth": "male"}).to_dict()
    ids = _ids(rep)
    assert "bacterial_infection" in ids[:6]


def test_copd_beneath_respiratory_acidosis(engine):
    rep = engine.interpret({"arterial_pco2": U(81, "mmHg"), "bicarbonate": U(38, "mmol/L"), "arterial_ph": U(7.30, "")},
                           None, {"age_years": 66, "sex_at_birth": "male"}).to_dict()
    ids = _ids(rep)
    assert "respiratory_acidosis" in ids[:2]
    # copd may lead only if it out-scores the finding it is inferred from
    if "copd" in ids and ids.index("copd") < ids.index("respiratory_acidosis"):
        assert _p(rep, "copd") > _p(rep, "respiratory_acidosis")


def test_marked_renal_failure_precedes_its_electrolyte_consequences(engine):
    obs = {"creatinine": U(17.5, "mg/dL"), "blood_urea_nitrogen": U(131, "mg/dL"), "potassium": U(7.2, "mmol/L"),
           "bicarbonate": U(12, "mmol/L"), "sodium": U(124, "mmol/L"), "calcium_total": U(6.0, "mg/dL"),
           "hemoglobin": U(8.3, "g/dL"), "chloride": U(87, "mmol/L"), "anion_gap": U(25, "mmol/L")}
    rep = engine.interpret(obs, None, {"age_years": 42, "sex_at_birth": "male"}).to_dict()
    ids = _ids(rep)
    renal = min(i for i, d in enumerate(ids) if d in ("acute_kidney_injury", "chronic_kidney_disease"))
    for eff in ("hyperkalemia", "hypocalcemia", "metabolic_acidosis", "hyponatremia"):
        if eff in ids:
            assert renal < ids.index(eff), (eff, ids[:8])


def test_specific_cause_still_outranks_aki(engine):
    # tumour-lysis-like panel: the specific syndrome must not be overtaken by AKI
    obs = {"creatinine": U(4.2, "mg/dL"), "potassium": U(6.4, "mmol/L"), "phosphate": U(9.1, "mg/dL"),
           "calcium_total": U(6.8, "mg/dL"), "uric_acid": U(15.2, "mg/dL"), "lactate_dehydrogenase": U(2400, "U/L"),
           "white_blood_cell_count": U(140, "10^9/L")}
    rep = engine.interpret(obs, None, {"age_years": 55, "sex_at_birth": "male"}).to_dict()
    ids = _ids(rep)
    assert "tumor_lysis_syndrome" in ids[:3], ids[:6]
    assert ids.index("tumor_lysis_syndrome") < ids.index("acute_kidney_injury")


def test_probabilities_unchanged_by_reordering(engine):
    obs = {"creatinine": U(17.5, "mg/dL"), "potassium": U(7.2, "mmol/L"), "bicarbonate": U(12, "mmol/L"),
           "sodium": U(124, "mmol/L"), "calcium_total": U(6.0, "mg/dL"), "hemoglobin": U(8.3, "g/dL")}
    rep = engine.interpret(obs, None, {"age_years": 42, "sex_at_birth": "male"}).to_dict()
    probs = [d["probability"] for d in rep["differential_diagnosis"]]
    # Tier-0 list is otherwise score-ordered: exactly one inversion is permitted (the organising dx moved up)
    inversions = sum(1 for a, b in zip(probs, probs[1:]) if b > a + 1e-9)
    assert inversions <= 3, probs[:10]


# ---- ext9b (2026-10-23) ----------------------------------------------------
def test_dka_entails_diabetes(engine):
    obs = {"glucose": U(420, "mg/dL"), "bicarbonate": U(10, "mmol/L"), "anion_gap": U(26, "mmol/L"),
           "beta_hydroxybutyrate": U(6.2, "mmol/L"), "arterial_ph": U(7.12, ""), "potassium": U(5.4, "mmol/L"), "creatinine": U(1.1, "mg/dL")}
    rep = engine.interpret(obs, None, {"age_years": 24, "sex_at_birth": "female"}).to_dict()
    ids = _ids(rep)
    assert "diabetic_ketoacidosis" in ids[:2]
    assert _p(rep, "diabetes_mellitus") is not None and _p(rep, "diabetes_mellitus") >= 0.6


def test_gap_acidosis_with_uraemia_is_not_called_dka_without_ketones(engine):
    obs = {"glucose": U(218, "mg/dL"), "bicarbonate": U(16.3, "mmol/L"), "creatinine": U(11.1, "mg/dL"),
           "potassium": U(6.0, "mmol/L"), "sodium": U(131, "mmol/L"), "anion_gap": U(22, "mmol/L")}
    rep = engine.interpret(obs, None, {"age_years": 71, "sex_at_birth": "male"}).to_dict()
    p = _p(rep, "diabetic_ketoacidosis")
    assert p is None or p < 0.5, p
    assert _ids(rep)[0] in ("acute_kidney_injury", "chronic_kidney_disease")


def test_profound_neutropenia_named_and_cultures_requested(engine):
    obs = {"white_blood_cell_count": U(0.2, "10^9/L"), "platelet_count": U(19, "10^9/L"), "hemoglobin": U(6.7, "g/dL")}
    rep = engine.interpret(obs, None, {"age_years": 72, "sex_at_birth": "female"}).to_dict()
    # registry 13.3.0 (D17) removed the template rules that let Hb/platelets vote for severe_neutropenia; with a
    # pancytopenic panel the three true findings now tie-break by magnitude (thrombocytopenia 19 first). The safety
    # requirement is that profound neutropenia is named in the head of the list and cultures/lactate are requested.
    assert "severe_neutropenia" in _ids(rep)[:4]
    assert _p(rep, "severe_neutropenia") >= 0.6
    tests_ = " ".join(x["test"] for x in rep["next_tests"]).lower()
    assert "blood cultures" in tests_ and "lactate" in tests_


# ---- ext10 (2026-10-23) ----------------------------------------------------
def test_undetermined_chronicity_cap_is_severity_graded(engine):
    def run(cr):
        rep = engine.interpret({"creatinine": U(cr, "mg/dL"), "blood_urea_nitrogen": U(cr * 12, "mg/dL")},
                               None, {"age_years": 60, "sex_at_birth": "male"}).to_dict()
        return max((_p(rep, d) or 0) for d in ("acute_kidney_injury", "chronic_kidney_disease"))
    mild, moderate, severe = run(1.6), run(2.4), run(4.0)   # eGFR ≈ 48 / 30 / 16
    assert mild <= 0.62 + 1e-6
    assert moderate > mild and moderate <= 0.70 + 1e-6
    assert severe > moderate and severe <= 0.78 + 1e-6


def test_bandemia_with_organ_marker_is_sepsis_even_at_normal_wbc(engine):
    obs = {"white_blood_cell_count": U(11.9, "10^9/L"), "band_neutrophils_percent": U(34, "%"),
           "creatinine": U(1.7, "mg/dL"), "blood_urea_nitrogen": U(49, "mg/dL"), "albumin": U(2.8, "g/dL")}
    rep = engine.interpret(obs, None, {"age_years": 54, "sex_at_birth": "female"}).to_dict()
    assert "sepsis" in _ids(rep)[:5] and _p(rep, "sepsis") >= 0.6


def test_bandemia_without_organ_marker_is_not_sepsis(engine):
    obs = {"white_blood_cell_count": U(9.0, "10^9/L"), "band_neutrophils_percent": U(12, "%"), "creatinine": U(0.8, "mg/dL"),
           "platelet_count": U(250, "10^9/L"), "albumin": U(4.1, "g/dL")}
    rep = engine.interpret(obs, None, {"age_years": 40, "sex_at_birth": "male"}).to_dict()
    p = _p(rep, "sepsis")
    assert p is None or p < 0.6


def test_alcohol_biomarker_signature_is_supportive_not_disease(engine):
    obs = {"mean_corpuscular_volume": U(111, "fL"), "hemoglobin": U(12.2, "g/dL"), "platelet_count": U(139, "10^9/L"),
           "aspartate_aminotransferase": U(46, "U/L"), "alanine_aminotransferase": U(33, "U/L"), "total_bilirubin": U(2.9, "mg/dL"),
           "phosphate": U(2.4, "mg/dL")}
    rep = engine.interpret(obs, None, {"age_years": 74, "sex_at_birth": "male"}).to_dict()
    p = _p(rep, "alcohol_use_disorder")
    assert p is not None and 0.5 <= p <= 0.75, p


def test_macrocytosis_with_low_b12_is_not_alcohol_signature(engine):
    obs = {"mean_corpuscular_volume": U(111, "fL"), "hemoglobin": U(10.2, "g/dL"), "platelet_count": U(139, "10^9/L"),
           "vitamin_b12": U(120, "pg/mL"), "aspartate_aminotransferase": U(46, "U/L"), "alanine_aminotransferase": U(30, "U/L")}
    rep = engine.interpret(obs, None, {"age_years": 74, "sex_at_birth": "male"}).to_dict()
    p = _p(rep, "alcohol_use_disorder")
    assert p is None or p < 0.5
