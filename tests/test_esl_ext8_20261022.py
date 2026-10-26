"""Extension 8 — next-test layer (2026-10-22)."""
import logging, pytest
import analyse_gidlines as ag
logging.disable(logging.CRITICAL)


@pytest.fixture(scope="module")
def engine():
    return ag.ClinicalRuleEngine()


def _run(E, obs, age=60, sex="male"):
    return E.interpret({k: {"value": v, "unit": u} for k, (v, u) in obs.items()}, None, {"age_years": age, "sex_at_birth": sex}).to_dict()


def test_leukocytosis_asks_for_sepsis_bundle(engine):
    rep = _run(engine, {"white_blood_cell_count": (16.7, "10^9/L"), "creatinine": (1.0, "mg/dL")})
    names = " ".join(t["test"] for t in rep["next_tests"]).lower()
    assert "lactate" in names and "blood cultures" in names and "procalcitonin" in names


def test_measured_test_is_not_recommended_again(engine):
    rep = _run(engine, {"white_blood_cell_count": (16.7, "10^9/L"), "lactate": (1.1, "mmol/L"), "procalcitonin": (0.1, "ng/mL")})
    names = " ".join(t["test"] for t in rep["next_tests"]).lower()
    assert "lactate" not in names and "procalcitonin" not in names


def test_random_glucose_140_199_triggers_hba1c_in_both_units(engine):
    for g, u in ((165, "mg/dL"), (9.2, "mmol/L")):
        rep = _run(engine, {"glucose": (g, u)})
        assert any(t["test"] == "HbA1c" for t in rep["next_tests"]), (g, u)
    rep = _run(engine, {"glucose": (95, "mg/dL")})
    assert not any(t["test"] == "HbA1c" for t in rep["next_tests"])


def test_single_creatinine_asks_for_chronicity_evidence(engine):
    rep = _run(engine, {"creatinine": (2.3, "mg/dL")}, age=70)
    assert any("prior creatinine" in t["test"].lower() for t in rep["next_tests"])


def test_every_recommendation_carries_a_source(engine):
    rep = _run(engine, {"white_blood_cell_count": (16.7, "10^9/L"), "creatinine": (2.3, "mg/dL"), "sodium": (128, "mmol/L"), "platelet_count": (90, "10^9/L")})
    assert rep["next_tests"] and all(t["source"] and t["rationale"] for t in rep["next_tests"])


def test_healthy_panel_recommends_nothing(engine):
    rep = _run(engine, {"hemoglobin": (14.5, "g/dL"), "glucose": (90, "mg/dL"), "creatinine": (0.9, "mg/dL"), "sodium": (140, "mmol/L"),
                        "potassium": (4.1, "mmol/L"), "white_blood_cell_count": (6.5, "10^9/L"), "platelet_count": (250, "10^9/L")})
    assert rep["next_tests"] == []
