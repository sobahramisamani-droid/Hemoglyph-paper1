"""ESL extension 6d — regression tests from the blind NHANES specificity test (B5)."""
import logging, pytest
import analyse_gidlines as ag

logging.disable(logging.CRITICAL)


@pytest.fixture(scope="module")
def engine():
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40; return E


def _run(E, obs, pt):
    o = {k: {"value": v, "unit": u} for k, (v, u) in obs.items()}
    return E.interpret(o, None, pt).to_dict()


def _p(rep, dx):
    return max([d["probability"] for d in rep["differential_diagnosis"] if d["disease_id"] == dx] or [0.0])


def test_mets_not_asserted_from_random_glucose(engine):
    # NHANES SEQN 95321-like: TG 156, HDL 32, random glucose 101, A1c 5.3 -> only two harmonised criteria
    rep = _run(engine, {"triglycerides": (156, "mg/dL"), "hdl_cholesterol": (32, "mg/dL"), "glucose": (101, "mg/dL"),
                        "hemoglobin_a1c": (5.3, "%"), "uric_acid": (5.3, "mg/dL")}, {"age_years": 65, "sex_at_birth": "male"})
    assert _p(rep, "metabolic_syndrome") < 0.5
    assert "metabolic_syndrome" not in [s["syndrome_id"] for s in rep["expert_syndromes"]]


def test_mets_asserted_with_fasting_glucose(engine):
    rep = _run(engine, {"triglycerides": (190, "mg/dL"), "hdl_cholesterol": (34, "mg/dL"), "fasting_plasma_glucose": (108, "mg/dL"),
                        "hemoglobin_a1c": (5.9, "%")}, {"age_years": 55, "sex_at_birth": "male"})
    assert _p(rep, "metabolic_syndrome") >= 0.6


def test_ckd_from_computed_egfr_plus_albuminuria(engine):
    # 75 y woman, Cr 1.36 (CKD-EPI 2021 eGFR ~40), UACR 64 -> KDIGO G3b A2
    rep = _run(engine, {"creatinine": (1.36, "mg/dL"), "urine_albumin_to_creatinine_ratio": (64, "mg/g"), "hemoglobin": (13.1, "g/dL"),
                        "blood_urea_nitrogen": (22, "mg/dL"), "potassium": (4.3, "mmol/L")}, {"age_years": 75, "sex_at_birth": "female"})
    assert _p(rep, "chronic_kidney_disease") >= 0.7
    assert _p(rep, "chronic_kidney_disease") > _p(rep, "acute_kidney_injury")


def test_elderly_g3a_alone_stays_silent(engine):
    # 85 y woman, Cr 1.1 (eGFR ~50), no albuminuria / anaemia / mineral markers -> no CKD assertion from one value
    rep = _run(engine, {"creatinine": (1.1, "mg/dL"), "hemoglobin": (13.5, "g/dL"), "phosphate": (3.4, "mg/dL"), "bicarbonate": (25, "mmol/L"),
                        "blood_urea_nitrogen": (18, "mg/dL")}, {"age_years": 85, "sex_at_birth": "female"})
    assert _p(rep, "chronic_kidney_disease") < 0.5
    assert rep["expert_syndromes"] == []


def test_egfr_not_computed_for_children(engine):
    rep = _run(engine, {"creatinine": (0.9, "mg/dL"), "hemoglobin": (12.8, "g/dL")}, {"age_years": 9, "sex_at_birth": "female"})
    assert "ckd_egfr_g3b" not in [s["syndrome_id"] for s in rep["expert_syndromes"]]
