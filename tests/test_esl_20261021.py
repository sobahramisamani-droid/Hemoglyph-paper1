"""Regression tests for the Expert Syndrome Layer (ESL) and the 2026-10-21
fusion/pattern fixes.  All cases are developer-authored constellations
(not clinical validation)."""
from __future__ import annotations

import logging
import random

import pytest

import analyse_gidlines as ag

logging.disable(logging.CRITICAL)


@pytest.fixture(scope="module")
def engine():
    return ag.ClinicalRuleEngine()


def _run(engine, obs, patient):
    payload = {f: {"value": v, "unit": u} for f, (v, u) in obs.items()}
    return engine.interpret(payload, None, patient).to_dict()


def _rank(rep, dx_ids):
    for x in rep["differential_diagnosis"]:
        if x["disease_id"] in dx_ids:
            return x["rank"]
    return None


# --------------------------------------------------------------------- #
# 1. layer wiring
# --------------------------------------------------------------------- #
def test_report_has_expert_syndromes_field(engine):
    rep = _run(engine, {"hemoglobin": (14, "g/dL")},
               {"age_years": 40, "sex_at_birth": "male"})
    assert "expert_syndromes" in rep
    assert rep["expert_syndromes"] == []


def test_library_filtered_to_registry(engine):
    active = engine._esl._lib
    assert len(active) >= 150
    known = engine.registry.diseases
    for syn in active:
        if syn.get("guard"):
            assert not syn["dx"] or syn["dx"][0] in known, syn["id"]
            continue
        assert syn["dx"][0] in known, syn["id"]


# --------------------------------------------------------------------- #
# 2. constellations that must win
# --------------------------------------------------------------------- #
HELLP = ({"platelets": (58, "10^9/L"), "aspartate_aminotransferase": (410, "U/L"),
          "alanine_aminotransferase": (360, "U/L"), "lactate_dehydrogenase": (1500, "U/L"),
          "total_bilirubin": (2.1, "mg/dL"), "indirect_bilirubin": (1.6, "mg/dL"),
          "serum_haptoglobin": (8, "mg/dL"), "schistocytes_percent": (2, "%"),
          "creatinine": (1.3, "mg/dL"), "uric_acid": (8.1, "mg/dL"),
          "urine_protein_to_creatinine_ratio": (1.4, "g/g")},
         {"age_years": 31, "sex_at_birth": "female", "pregnant": True})


def test_hellp_outranks_preeclampsia(engine):
    rep = _run(engine, *HELLP)
    ids = [h["syndrome_id"] for h in rep["expert_syndromes"]]
    assert "hellp" in ids
    assert _rank(rep, {"hellp_syndrome"}) == 1
    top = rep["differential_diagnosis"][0]
    assert top["evidence_state"] == "supported"
    # secondary dx of the same syndrome must not outrank the primary
    sec = _rank(rep, {"hellp_associated_liver_injury"})
    assert sec is None or sec > 1


def test_hcc_floor_beats_bayesian_dissent(engine):
    obs = {"alpha_fetoprotein": (1800, "ng/mL"), "platelets": (70, "10^9/L"),
           "albumin": (2.8, "g/dL"), "total_bilirubin": (2.4, "mg/dL"),
           "international_normalized_ratio": (1.5, "1"),
           "aspartate_aminotransferase": (110, "U/L"),
           "alanine_aminotransferase": (60, "U/L"),
           "hepatitis_b_surface_antigen": (1, "1")}
    rep = _run(engine, obs, {"age_years": 70, "sex_at_birth": "male"})
    assert _rank(rep, {"hepatocellular_carcinoma"}) == 1
    top = rep["differential_diagnosis"][0]
    assert top["probability"] >= 0.85
    assert top["evidence_state"] == "supported"


def test_acute_hbv_not_called_chronic(engine):
    obs = {"hepatitis_b_surface_antigen": (1, "1"), "hepatitis_b_core_igm_antibody": (1, "1"),
           "alanine_aminotransferase": (1450, "U/L"), "total_bilirubin": (6.2, "mg/dL")}
    rep = _run(engine, obs, {"age_years": 34, "sex_at_birth": "male"})
    ids = [h["syndrome_id"] for h in rep["expert_syndromes"]]
    assert "hbv_acute" in ids and "hbv_chronic_flare" not in ids
    assert _rank(rep, {"hepatitis_b", "acute_hepatitis_b"}) == 1


def test_iga_deficient_coeliac_via_alias(engine):
    obs = {"anti_tissue_transglutaminase_iga": (1, "U/mL"), "immunoglobulin_a": (3, "mg/dL"),
           "anti_tissue_transglutaminase_igg": (120, "U/mL"),
           "hemoglobin": (10.8, "g/dL"), "ferritin": (7, "ng/mL")}
    rep = _run(engine, obs, {"age_years": 9, "sex_at_birth": "female"})
    ids = [h["syndrome_id"] for h in rep["expert_syndromes"]]
    assert any("coeliac" in i or "celiac" in i for i in ids), ids
    assert _rank(rep, {"celiac_disease", "coeliac_disease"}) in (1, 2)


def test_alcoholic_hepatitis_needs_alcohol_signal(engine):
    # decompensated cirrhosis panel with no GGT/MCV/WBC alcohol signal
    obs = {"albumin": (2.4, "g/dL"), "international_normalized_ratio": (1.9, "ratio"),
           "total_bilirubin": (3.4, "mg/dL"), "platelets": (68, "10^9/L"),
           "aspartate_aminotransferase": (74, "U/L"), "alanine_aminotransferase": (38, "U/L")}
    rep = _run(engine, obs, {"age_years": 58, "sex_at_birth": "male"})
    ids = [h["syndrome_id"] for h in rep["expert_syndromes"]]
    assert "alcoholic_hepatitis" not in ids
    assert _rank(rep, {"liver_cirrhosis"}) == 1


def test_cholangitis_requires_inflammation(engine):
    obs = {"alkaline_phosphatase": (640, "U/L"), "total_bilirubin": (2.2, "mg/dL"),
           "direct_bilirubin": (1.6, "mg/dL"), "gamma_glutamyl_transferase": (420, "U/L"),
           "alanine_aminotransferase": (95, "U/L")}
    rep = _run(engine, obs, {"age_years": 38, "sex_at_birth": "male"})
    ids = [h["syndrome_id"] for h in rep["expert_syndromes"]]
    assert "cholangitis" not in ids
    obs["white_blood_cell_count"] = (16, "10^9/L")
    rep = _run(engine, obs, {"age_years": 38, "sex_at_birth": "male"})
    assert "cholangitis" in [h["syndrome_id"] for h in rep["expert_syndromes"]]


def test_cap_is_applied_to_rivals(engine):
    rep = _run(engine, *HELLP)
    hit = next(h for h in rep["expert_syndromes"] if h["syndrome_id"] == "hellp")
    by_id = {x["disease_id"]: x for x in rep["differential_diagnosis"]}
    primary = by_id["hellp_syndrome"]["probability"]
    for rival, factor in hit.get("cap", {}).items():
        if rival in by_id:
            assert by_id[rival]["probability"] <= primary * factor + 1e-6, rival


# --------------------------------------------------------------------- #
# 3. silence on normals
# --------------------------------------------------------------------- #
_NORMAL = {
    "hemoglobin": (13.5, 16.5, "g/dL"), "mean_corpuscular_volume": (82, 96, "fL"),
    "platelets": (160, 380, "10^9/L"), "white_blood_cell_count": (4.5, 10, "10^9/L"),
    "sodium": (136, 144, "mmol/L"), "potassium": (3.6, 5.0, "mmol/L"),
    "chloride": (98, 106, "mmol/L"), "bicarbonate": (23, 28, "mmol/L"),
    "blood_urea_nitrogen": (8, 20, "mg/dL"), "creatinine": (0.7, 1.1, "mg/dL"),
    "albumin": (3.8, 4.8, "g/dL"), "total_bilirubin": (0.3, 1.0, "mg/dL"),
    "direct_bilirubin": (0.05, 0.25, "mg/dL"), "aspartate_aminotransferase": (14, 34, "U/L"),
    "alanine_aminotransferase": (10, 38, "U/L"), "alkaline_phosphatase": (45, 115, "U/L"),
    "gamma_glutamyl_transferase": (10, 45, "U/L"), "lactate_dehydrogenase": (130, 220, "U/L"),
    "thyroid_stimulating_hormone": (0.6, 3.8, "mIU/L"), "free_thyroxine": (0.9, 1.6, "ng/dL"),
    "ferritin": (40, 200, "ng/mL"), "c_reactive_protein": (0.2, 4, "mg/L"),
    "international_normalized_ratio": (0.9, 1.1, "1"), "uric_acid": (3.5, 5.9, "mg/dL"),
    "serum_haptoglobin": (50, 180, "mg/dL"), "reticulocyte_percent": (0.6, 1.8, "%"),
    "hemoglobin_a1c": (4.8, 5.5, "%"), "triglycerides": (60, 140, "mg/dL"),
    "total_immunoglobulin_a": (90, 300, "mg/dL"), "alpha_fetoprotein": (1, 6, "ng/mL"),
    "lipase": (15, 50, "U/L"), "parathyroid_hormone": (20, 60, "pg/mL"),
    "troponin_i": (0.001, 0.02, "ng/mL"),
}


def test_esl_silent_on_healthy_panels(engine):
    rng = random.Random(20261021)
    for _ in range(40):
        sex = rng.choice(["male", "female"])
        obs = {k: (round(rng.uniform(lo, hi), 3), u) for k, (lo, hi, u) in _NORMAL.items()}
        if sex == "female":
            obs["hemoglobin"] = (round(rng.uniform(12.2, 15.2), 2), "g/dL")
        rep = _run(engine, obs, {"age_years": rng.randint(18, 85), "sex_at_birth": sex})
        assert rep["expert_syndromes"] == [], rep["expert_syndromes"]
        for x in rep["differential_diagnosis"]:
            assert x["evidence_state"] != "supported", x


def test_fib4_age_artifact_not_cirrhosis(engine):
    obs = {"aspartate_aminotransferase": (33, "U/L"), "alanine_aminotransferase": (11, "U/L"),
           "platelets": (175, "10^9/L"), "albumin": (4.2, "g/dL"),
           "total_bilirubin": (0.3, "mg/dL"), "international_normalized_ratio": (1.0, "1")}
    rep = _run(engine, obs, {"age_years": 79, "sex_at_birth": "male"})
    pats = {p["pattern_id"]: p for p in rep["derived_patterns"]}
    assert "fib4_high" not in pats
    assert pats["fib4_high_age_artifact"]["significance"] == "low"
    for x in rep["differential_diagnosis"]:
        if x["disease_id"] in ("liver_cirrhosis", "nash"):
            assert x["probability"] < 0.4


# --------------------------------------------------------------------- #
# 4. robustness
# --------------------------------------------------------------------- #
def test_esl_failure_never_breaks_interpret(engine, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("synthetic ESL failure")
    monkeypatch.setattr(engine._esl, "evaluate", boom)
    rep = _run(engine, *HELLP)
    assert rep["differential_diagnosis"]
    assert rep["expert_syndromes"] == []


def test_esl_deterministic(engine):
    a = _run(engine, *HELLP)
    b = _run(engine, *HELLP)
    assert [(x["disease_id"], round(x["probability"], 6)) for x in a["differential_diagnosis"]] == \
           [(x["disease_id"], round(x["probability"], 6)) for x in b["differential_diagnosis"]]


# --------------------------------------------------------------------- #
# 5. adversarial-battery findings (2026-10-21, phase 2)
# --------------------------------------------------------------------- #
def test_pth_pmol_conversion_and_si_twin(engine):
    from calcu import convert_unit
    assert abs(convert_unit(14.8, "pmol/L", "pg/mL", "parathyroid_hormone") - 139.5) < 1.0
    assert abs(convert_unit(14.8, "pmol/L", "pg/mL", "intact_parathyroid_hormone") - 139.5) < 1.0
    conv = {"calcium_total": (11.4, "mg/dL"), "albumin": (4.0, "g/dL"), "parathyroid_hormone": (140, "pg/mL"),
            "phosphate": (2.2, "mg/dL"), "creatinine": (0.9, "mg/dL")}
    si = {"calcium_total": (2.85, "mmol/L"), "albumin": (40, "g/L"), "parathyroid_hormone": (14.8, "pmol/L"),
          "phosphate": (0.71, "mmol/L"), "creatinine": (80, "umol/L")}
    a = _run(engine, conv, {"age_years": 38, "sex_at_birth": "female"})
    b = _run(engine, si, {"age_years": 38, "sex_at_birth": "female"})
    assert {h["syndrome_id"] for h in a["expert_syndromes"]} == {h["syndrome_id"] for h in b["expert_syndromes"]}
    assert a["differential_diagnosis"][0]["disease_id"] == b["differential_diagnosis"][0]["disease_id"] == "primary_hyperparathyroidism"
    assert abs(a["differential_diagnosis"][0]["probability"] - b["differential_diagnosis"][0]["probability"]) <= 0.05


def test_esl_skips_unconvertible_unit_instead_of_misreading(engine):
    ctx = ag.ClinicalContext(age_years=38, sex_at_birth="female")
    obs, _ = ag.normalize_observations(
        {"parathyroid_hormone": {"value": 140, "unit": "furlongs"}}, None, engine._vizhegi_ghabel_ghabool())
    v = engine._esl._values(obs, ctx)
    assert v.get("pth") is None


def test_esl_unit_label_variants_are_equal():
    assert ag._esl_unit_eq("U/L", "IU/L")
    assert ag._esl_unit_eq("µIU/mL", "uIU/mL")
    assert ag._esl_unit_eq("x10^9/L", "10^9/L")
    assert not ag._esl_unit_eq("pmol/L", "pg/mL")


def test_tma_guard_caps_itp(engine):
    obs = {"platelets": (40, "10^9/L"), "hemoglobin": (13, "g/dL"),
           "white_blood_cell_count": (7, "10^9/L"), "schistocytes_percent": (3, "%")}
    rep = _run(engine, obs, {"age_years": 38, "sex_at_birth": "female"})
    ids = {h["syndrome_id"] for h in rep["expert_syndromes"]}
    assert "tma_pattern" in ids and "itp" not in ids
    by = {x["disease_id"]: x for x in rep["differential_diagnosis"]}
    assert by["thrombotic_microangiopathy"]["probability"] > by.get("immune_thrombocytopenia", {"probability": 0})["probability"]


def test_single_troponin_is_injury_not_mi(engine):
    rep = _run(engine, {"high_sensitivity_troponin_i": (99, "ng/L"), "creatine_kinase_total": (180, "U/L")},
               {"age_years": 70, "sex_at_birth": "male"})
    top = rep["differential_diagnosis"][0]
    assert top["disease_id"] in ("acute_myocardial_injury", "chronic_myocardial_injury", "myocardial_injury_acuity_undetermined")  # 14.1 C10
    by = {x["disease_id"]: x for x in rep["differential_diagnosis"]}
    if "acute_myocardial_infarction" in by:
        assert by["acute_myocardial_infarction"]["probability"] < 0.7


def test_injury_guard_silent_when_pe_picture(engine):
    rep = _run(engine, {"d_dimer": (4.2, "ug/mL"), "troponin_i": (0.09, "ng/mL"), "n_terminal_pro_bnp": (900, "pg/mL")},
               {"age_years": 45, "sex_at_birth": "male"})
    assert "myocardial_injury_single" not in {h["syndrome_id"] for h in rep["expert_syndromes"]}
    assert _rank(rep, {"pulmonary_embolism"}) is not None and _rank(rep, {"pulmonary_embolism"}) <= 6


def test_adversarial_battery_script_passes():
    import subprocess, sys, os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    r = subprocess.run([sys.executable, os.path.join(root, "tests", "adversarial_battery.py")],
                       capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stdout[-2000:]
