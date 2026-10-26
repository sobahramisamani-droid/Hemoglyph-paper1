# -*- coding: utf-8 -*-
"""Regression tests for ESL extension 5 (critical haematology / coagulation /
acid-base / total-thyroid / urate anchors).  Each case is a de-identified
pattern taken from the eICU-CRD demo, UCI thyroid0387 or NHANES 2017-18
error analysis of the frozen v1 engine (2026-10-21)."""
import pytest
from analyse_gidlines import ClinicalRuleEngine


@pytest.fixture(scope="module")
def engine():
    e = ClinicalRuleEngine()
    e._reasoner.max_differential = 40
    return e


def _top(engine, obs, patient=None, k=5):
    rep = engine.interpret(obs, None, patient or {"age": 50, "sex": "male"}).to_dict()
    return [(d["disease_id"], float(d["probability"])) for d in rep["differential_diagnosis"][:k]]


def _p(top, dx):
    return dict(top).get(dx, 0.0)


def test_critical_platelets_in_top5(engine):
    top = _top(engine, {"platelet_count": 16, "white_blood_cell_count": 0.7, "hemoglobin": 6.2, "sodium": 122})
    assert _p(top, "thrombocytopenia") >= 0.8 or _p(top, "pancytopenia") >= 0.7
    assert "thrombocytopenia" in dict(top)


def test_hyperleukocytosis_not_nephrotic(engine):
    top = _top(engine, {"white_blood_cell_count": 469.8, "platelet_count": 127, "hemoglobin": 8.2, "albumin": 2.1, "creatinine": 1.1})
    ids = [d for d, _ in top]
    assert ids[0] in ("chronic_leukemia_support_pattern", "acute_leukemia_support_pattern", "leukocytosis_pattern")
    assert "nephrotic_syndrome" not in ids[:3]


def test_critical_anemia_in_top5(engine):
    top = _top(engine, {"hemoglobin": 4.1, "lactate": 6.1, "white_blood_cell_count": 13.1, "platelet_count": 188,
                        "international_normalized_ratio": 1.62, "troponin_i": 0.3})
    assert _p(top, "anemia") >= 0.8


def test_critical_inr_in_top5(engine):
    top = _top(engine, {"international_normalized_ratio": 8.5, "hemoglobin": 8.7, "white_blood_cell_count": 17.9, "platelet_count": 409, "sodium": 131})
    assert top[0][0] == "elevated_inr_pattern" and top[0][1] >= 0.9


def test_hypercapnic_acidemia(engine):
    top = _top(engine, {"arterial_ph": 7.18, "arterial_pco2": 80, "bicarbonate": 34, "white_blood_cell_count": 14})
    assert top[0][0] == "respiratory_acidosis" and top[0][1] >= 0.9
    assert _p(top, "metabolic_acidosis") < 0.5


def test_overt_hyperthyroidism_total_t4(engine):
    top = _top(engine, {"thyroid_stimulating_hormone": 0.05, "total_thyroxine": {"value": 190, "unit": "nmol/L"},
                        "total_triiodothyronine": {"value": 3.5, "unit": "nmol/L"}})
    assert top[0][0] == "hyperthyroidism" and top[0][1] >= 0.75


def test_hyperuricemia_definitional(engine):
    top = _top(engine, {"uric_acid": 8.2, "creatinine": 1.0, "glucose": 95})
    assert top[0][0] == "hyperuricemia" and top[0][1] >= 0.8


def test_female_borderline_urate_sex_specific(engine):
    # v3 (ESL ext 6): 6.0-7.0 mg/dL overlaps the healthy female interval, so the
    # female tier now needs one metabolic/renal co-finding (healthy_sweep false-fires).
    top = _top(engine, {"uric_acid": 6.4, "creatinine": 0.8}, {"age": 40, "sex": "female"})
    assert _p(top, "hyperuricemia") < 0.6
    top = _top(engine, {"uric_acid": 6.4, "creatinine": 0.8, "triglycerides": 230}, {"age": 40, "sex": "female"})
    assert 0.6 <= _p(top, "hyperuricemia") <= 0.85   # pattern tier, below the > 7 mg/dL 'strong' tier
    top_m = _top(engine, {"uric_acid": 6.4, "creatinine": 0.8}, {"age": 40, "sex": "male"})
    assert _p(top_m, "hyperuricemia") < 0.5


def test_ext5_silent_on_normal_panel(engine):
    top = _top(engine, {"hemoglobin": 14, "platelet_count": 250, "white_blood_cell_count": 6, "international_normalized_ratio": 1.0,
                        "uric_acid": 5.0, "thyroid_stimulating_hormone": 2.0, "total_thyroxine": 8.0, "arterial_ph": 7.40,
                        "arterial_pco2": 40, "bicarbonate": 24})
    assert all(p < 0.5 for _, p in top)
