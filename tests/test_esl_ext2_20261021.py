# -*- coding: utf-8 -*-
"""Regression tests for the ESL extension 2 round (2026-10-21):
dx-less physiological guards, fuzzy defining-feature gate, GDM fasting fix,
pernicious/B12 split, HDN vs neonatal jaundice, SCID vs XLA, MIS-C context."""
import os, sys, logging
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)


@pytest.fixture(scope="module")
def engine():
    import analyse_gidlines as ag
    return ag.ClinicalRuleEngine()


def _run(engine, obs, pt):
    return engine.interpret({f: {"value": v, "unit": u} for f, (v, u) in obs.items()}, None, pt).to_dict()


def _p(rep, did):
    return next((x["probability"] for x in rep["differential_diagnosis"] if x["disease_id"] == did), 0.0)


def _top(rep):
    d = rep["differential_diagnosis"]
    return d[0]["disease_id"] if d else None


def _syn(rep):
    return {h["syndrome_id"] for h in rep["expert_syndromes"]}


PREG = {"age_years": 31, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 30}


def test_library_size_after_extension(engine):
    import analyse_gidlines as ag
    assert len(ag._ESL_LIBRARY) >= 320
    assert len(engine._esl._lib) >= 315
    ids = [s["id"] for s in ag._ESL_LIBRARY]
    assert len(ids) == len(set(ids)), "duplicate syndrome ids"


def test_guard_entries_are_dxless_and_flagged(engine):
    guards = [s for s in engine._esl._lib if s.get("guard")]
    assert len(guards) >= 8
    for g in guards:
        assert g["dx"] == []
        # ESL ext 11 (2026-10-23): informational guards (temporal warnings such as sodium
        # over-correction, lactate clearing) carry a `note` instead of competitor caps.
        assert g.get("cap") or g.get("note")


def test_pregnancy_prolactin_guard(engine):
    rep = _run(engine, {"prolactin": (150, "ng/mL")}, PREG)
    assert "pregnancy_prolactin_guard" in _syn(rep)
    assert _p(rep, "hyperprolactinemia") <= 0.3
    # same value outside pregnancy must still be called
    rep2 = _run(engine, {"prolactin": (150, "ng/mL")}, {"age_years": 31, "sex_at_birth": "female"})
    assert _p(rep2, "hyperprolactinemia") > 0.5 or _p(rep2, "prolactinoma") > 0.5


def test_pregnancy_ddimer_guard_but_not_when_trop_high(engine):
    rep = _run(engine, {"d_dimer": (1.3, "ug/mL"), "high_sensitivity_troponin_i": (4, "ng/L")}, PREG)
    assert "pregnancy_ddimer_guard" in _syn(rep)
    assert all(x["probability"] < 0.5 for x in rep["differential_diagnosis"])
    rep2 = _run(engine, {"d_dimer": (1.3, "ug/mL"), "high_sensitivity_troponin_i": (90, "ng/L")}, PREG)
    assert "pregnancy_ddimer_guard" not in _syn(rep2)


def test_pregnancy_physiologic_guard_keeps_panel_quiet(engine):
    obs = {"albumin": (3.1, "g/dL"), "creatinine": (0.5, "mg/dL"), "alkaline_phosphatase": (240, "U/L"), "hemoglobin": (10.8, "g/dL"),
           "blood_urea_nitrogen": (6, "mg/dL"), "sodium": (134, "mmol/L"), "bicarbonate": (20, "mmol/L"), "d_dimer": (1.1, "ug/mL"),
           "platelets": (190, "10^9/L"), "uric_acid": (3.8, "mg/dL"), "alanine_aminotransferase": (18, "U/L"), "ferritin": (40, "ng/mL")}
    rep = _run(engine, obs, PREG)
    assert "pregnancy_physiologic_guard" in _syn(rep)
    assert all(x["probability"] < 0.5 for x in rep["differential_diagnosis"]), rep["differential_diagnosis"][:3]


def test_pregnancy_guard_does_not_mask_preeclampsia(engine):
    obs = {"albumin": (3.0, "g/dL"), "creatinine": (0.7, "mg/dL"), "alkaline_phosphatase": (260, "U/L"), "hemoglobin": (11.0, "g/dL"),
           "platelets": (88, "10^9/L"), "alanine_aminotransferase": (140, "U/L"), "uric_acid": (7.2, "mg/dL"),
           "urine_protein_to_creatinine_ratio": (1.4, "g/g"), "lactate_dehydrogenase": (720, "U/L")}
    rep = _run(engine, obs, PREG)
    assert "pregnancy_physiologic_guard" not in _syn(rep)
    top3 = [x["disease_id"] for x in rep["differential_diagnosis"][:3]]
    assert any(d in top3 for d in ("hellp_syndrome", "preeclampsia", "preeclampsia_with_severe_features", "severe_preeclampsia")), top3


def test_pediatric_lymphocyte_guard(engine):
    rep = _run(engine, {"lymphocyte_count_absolute": (5.0, "10^9/L"), "hemoglobin": (12.2, "g/dL")}, {"age_years": 4, "sex_at_birth": "male"})
    assert _p(rep, "lymphocytosis") <= 0.3
    rep2 = _run(engine, {"lymphocyte_count_absolute": (5.0, "10^9/L")}, {"age_years": 40, "sex_at_birth": "male"})
    assert _p(rep2, "lymphocytosis") > 0.5


def test_fuzzy_defining_feature_gate_thalassemia(engine):
    # ferritin + RDW alone (MCV never measured) must not yield thalassemia trait >= 0.5
    rep = _run(engine, {"ferritin": (52, "ng/mL"), "red_cell_distribution_width_cv": (12.8, "%"), "hemoglobin": (12.9, "g/dL")}, {"age_years": 41, "sex_at_birth": "female"})
    assert _p(rep, "thalassemia_trait") < 0.5
    # with the defining microcytosis the call must still be made
    rep2 = _run(engine, {"ferritin": (52, "ng/mL"), "mean_corpuscular_volume": (66, "fL"), "red_blood_cell_count": (5.9, "10^6/uL"), "hemoglobin": (11.6, "g/dL"), "hemoglobin_a2": (5.1, "%")}, {"age_years": 41, "sex_at_birth": "female"})
    assert _top(rep2) in ("thalassemia_trait", "beta_thalassemia_trait", "beta_thalassemia_minor")


def test_gdm_requires_fasting_evidence(engine):
    rep = _run(engine, {"glucose": (95, "mg/dL")}, PREG)
    assert "gdm" not in _syn(rep)
    rep2 = _run(engine, {"glucose": (95, "mg/dL"), "hemoglobin_a1c": (5.8, "%")}, PREG)
    assert "gdm" in _syn(rep2)
    rep3 = _run(engine, {"glucose_2h_ogtt_75g": (170, "mg/dL")} if "glucose_2h_ogtt_75g" in engine.registry.features else {"glucose": (130, "mg/dL")}, PREG)
    assert "gdm" in _syn(rep3)


def test_b12_without_if_antibody_is_not_pernicious(engine):
    obs = {"vitamin_b12": (95, "pg/mL"), "mean_corpuscular_volume": (118, "fL"), "hemoglobin": (7.9, "g/dL"), "lactate_dehydrogenase": (1400, "U/L"), "methylmalonic_acid": (1800, "nmol/L")}
    rep = _run(engine, obs, {"age_years": 72, "sex_at_birth": "female"})
    assert _top(rep) in ("vitamin_b12_deficiency", "megaloblastic_anemia", "vitamin_b12_deficiency_anemia")
    obs["anti_intrinsic_factor_antibody_igg"] = (1, "1")
    rep2 = _run(engine, obs, {"age_years": 72, "sex_at_birth": "female"})
    assert _top(rep2) == "pernicious_anemia"


def test_dat_positive_newborn_is_hdn(engine):
    obs = {"coombs_direct_antiglobulin_test": (1, "1"), "total_bilirubin": (19, "mg/dL"), "direct_bilirubin": (0.6, "mg/dL"), "hemoglobin": (11.2, "g/dL"), "reticulocyte_percent": (12, "%")}
    rep = _run(engine, obs, {"age_years": 0.01, "sex_at_birth": "male"})
    assert _top(rep) in ("hemolytic_disease_of_the_newborn", "abo_hemolytic_disease_of_the_newborn")


def test_lymphopenic_infant_is_scid_not_xla(engine):
    obs = {"lymphocyte_count_absolute": (0.6, "10^9/L"), "total_immunoglobulin_g": (120, "mg/dL"), "total_immunoglobulin_a": (3, "mg/dL"), "total_immunoglobulin_m": (8, "mg/dL")}
    rep = _run(engine, obs, {"age_years": 0.4, "sex_at_birth": "male"})
    assert _top(rep) == "severe_combined_immunodeficiency_scid"
    assert "xla" not in _syn(rep)


def test_misc_needs_covid_context_and_not_thrombocytosis(engine):
    obs = {"c_reactive_protein": (140, "mg/L"), "n_terminal_pro_bnp": (1800, "pg/mL"), "platelets": (820, "10^9/L"), "albumin": (2.6, "g/dL"), "sodium": (131, "mmol/L")}
    rep = _run(engine, obs, {"age_years": 4, "sex_at_birth": "male"})
    assert "mis_c" not in _syn(rep)
    obs["platelets"] = (95, "10^9/L")
    rep2 = _run(engine, obs, {"age_years": 9, "sex_at_birth": "male", "conditions": ["COVID exposure 4 weeks ago"]})
    assert "mis_c" in _syn(rep2)


def test_healthy_wide_panel_stays_silent(engine):
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import random
    import healthy_sweep as hs
    rng = random.Random(20261021)
    for i in range(12):
        kind = ["adult", "child", "preg"][i % 3]
        if kind == "child": pt = {"age_years": rng.choice([2, 5, 9, 13]), "sex_at_birth": "female"}
        elif kind == "preg": pt = {"age_years": 30, "sex_at_birth": "female", "pregnant": True, "gestational_weeks": 30}
        else: pt = {"age_years": rng.randint(18, 80), "sex_at_birth": rng.choice(["male", "female"])}
        obs = hs.panel(rng, kind, pt["sex_at_birth"], rng.choice([15, 40, len(hs.REF)]), age=pt["age_years"])
        rep = engine.interpret(obs, None, pt).to_dict()
        assert not [h for h in rep["expert_syndromes"] if not h.get("guard")], (i, kind)
        assert all(x["probability"] < 0.5 for x in rep["differential_diagnosis"]), (i, kind, rep["differential_diagnosis"][:2])
