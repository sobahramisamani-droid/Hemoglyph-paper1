# -*- coding: utf-8 -*-
"""Registry v13.2.0 — pathogen-specific infectious entities must not be proposed from routine analytes alone.

Runs against the LIVE registry when its version is >= 13.2.0; otherwise (pre-activation) runs against the candidate file
in eval/patches/cand/ if present, else skips. Engine code is not modified by the patch; only registry content.
"""
import json, os, sys
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval", "patches"))
import brotli
import analyse_gidlines as ag

LIVE = os.path.join(ROOT, "HEMOGLYPH_GUIDELINE_REGISTRY.json.br")
CAND = os.path.join(ROOT, "eval", "patches", "cand", "HEMOGLYPH_GUIDELINE_REGISTRY_v13_2_0_candidate.json.br")


def _version(p):
    return json.loads(brotli.decompress(open(p, "rb").read()))["registry_metadata"]["version"]


def _tuple(v):
    return tuple(int(x) for x in v.split("-")[0].split("."))


@pytest.fixture(scope="module")
def engine():
    path = LIVE if _tuple(_version(LIVE)) >= (13, 2, 0) else (CAND if os.path.exists(CAND) else None)
    if path is None:
        pytest.skip("registry < 13.2.0 and no candidate file")
    E = ag.ClinicalRuleEngine(disease_registry_path=path); E._reasoner.max_differential = 40
    return E


def _dd(E, obs, ctx):
    rep = E.interpret(obs, None, ctx).to_dict()
    return [d["disease_id"] for d in rep.get("differential_diagnosis", [])]


MILD_TRANSAMINITIS = {"aspartate_aminotransferase": {"value": 73, "unit": "U/L"}, "alanine_aminotransferase": {"value": 113, "unit": "U/L"},
                      "total_bilirubin": {"value": 0.8, "unit": "mg/dL"}, "alkaline_phosphatase": {"value": 90, "unit": "U/L"},
                      "platelet_count": {"value": 250, "unit": "10^9/L"}, "hemoglobin": {"value": 13, "unit": "g/dL"},
                      "hepatitis_b_surface_antigen": {"value": "negative"}, "hepatitis_c_antibody": {"value": "negative"},
                      "hepatitis_a_igm_antibody": {"value": "negative"}}
VHF = {"ebola", "marburg", "lassa_fever", "hantavirus", "epidemic_typhus", "endemic_typhus", "ehrlichiosis", "anaplasmosis"}


def test_vhf_absent_from_isolated_transaminitis(engine):
    dd = _dd(engine, MILD_TRANSAMINITIS, {"age_years": 45, "sex_at_birth": "female"})
    assert not (set(dd) & VHF), dd


def test_gate_opens_with_exposure_history(engine):
    dd = _dd(engine, MILD_TRANSAMINITIS, {"age_years": 45, "sex_at_birth": "female", "exposure_history": True})
    assert set(dd) & {"ebola", "lassa_fever", "marburg"}, dd


def test_specific_marker_still_proposes_pathogen(engine):
    obs = dict(MILD_TRANSAMINITIS); obs["hantavirus_igm_antibody"] = {"value": "positive"}
    dd = _dd(engine, obs, {"age_years": 45, "sex_at_birth": "female"})
    assert "hantavirus" in dd[:5], dd


def test_crp_alone_does_not_make_pathogen_pattern(engine):
    obs = {"c_reactive_protein": {"value": 60, "unit": "mg/L"}, "white_blood_cell_count": {"value": 12, "unit": "10^9/L"}}
    dd = _dd(engine, obs, {"age_years": 30, "sex_at_birth": "male"})
    bad = {"toxoplasmosis_serologic_pattern", "dengue_infection_support_pattern", "brucellosis_serologic_support_pattern",
           "invasive_aspergillosis_marker_pattern", "clostridioides_difficile_support_pattern", "congenital_infection_screening_pattern"}
    assert not (set(dd) & bad), dd


def test_syndromic_infection_entities_untouched(engine):
    obs = {"c_reactive_protein": {"value": 180, "unit": "mg/L"}, "procalcitonin": {"value": 6.5, "unit": "ng/mL"},
           "lactate": {"value": 5.2, "unit": "mmol/L"}, "white_blood_cell_count": {"value": 19, "unit": "10^9/L"}}
    dd = _dd(engine, obs, {"age_years": 60, "sex_at_birth": "male"})
    assert any(d in ("sepsis", "sepsis_support_pattern", "septic_shock_support_pattern", "bacterial_infection", "acute_bacterial_infection_pattern") for d in dd[:5]), dd
