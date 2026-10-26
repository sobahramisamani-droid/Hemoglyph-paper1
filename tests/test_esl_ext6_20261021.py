# -*- coding: utf-8 -*-
"""Regression tests for ESL extension 6 + clinical-salience re-ranking (engine v3).

Every case is a de-identified constellation from the blind LLM-vs-engine error
analysis on the eICU-CRD demo (2026-10-21).  The knowledge was already present
in v1/v2; these tests pin the *ranking / gating* behaviour that was wrong.
"""
import pytest
from analyse_gidlines import ClinicalRuleEngine


@pytest.fixture(scope="module")
def engine():
    e = ClinicalRuleEngine()
    e._reasoner.max_differential = 40
    return e


def _rep(engine, obs, patient=None):
    return engine.interpret(obs, None, patient or {"age": 55, "sex": "male"}).to_dict()


def _ranks(rep):
    return {d["disease_id"]: int(d["rank"]) for d in rep["differential_diagnosis"]}


def _p(rep, dx):
    return {d["disease_id"]: float(d["probability"]) for d in rep["differential_diagnosis"]}.get(dx, 0.0)


def _syn(rep):
    return {h["syndrome_id"] for h in rep.get("expert_syndromes", [])}


U = lambda v, u: {"value": v, "unit": u}


# 1. HCO3 1.7 mmol/L is a real value in severe DKA, not an implausible entry.
def test_severe_dka_bicarbonate_below_two_is_accepted(engine):
    rep = _rep(engine, {"glucose": U(435, "mg/dL"), "bicarbonate": U(1.7, "mmol/L"), "arterial_ph": U(6.89, "1"),
                        "anion_gap": U(28, "mmol/L"), "potassium": U(5.7, "mmol/L"), "sodium": U(133, "mmol/L"),
                        "total_bilirubin": U(2.3, "mg/dL"), "albumin": U(5.3, "g/dL"), "white_blood_cell_count": U(24, "10*3/uL")})
    r = _ranks(rep)
    assert "dka_ketones_unmeasured" in _syn(rep) or "severe_acidemia" in _syn(rep)
    assert r.get("diabetic_ketoacidosis", 99) <= 5
    assert _p(rep, "gilbert_syndrome") < 0.5           # Gilbert must not lead a pH 6.89 panel
    assert _p(rep, "ethylene_glycol_poisoning") < 0.5  # glucose 435 explains the osmolal gap


# 2. Creatinine 2.5 / BUN 75 can never be absent from the differential.
def test_marked_renal_failure_never_disappears(engine):
    rep = _rep(engine, {"creatinine": U(2.5, "mg/dL"), "blood_urea_nitrogen": U(75, "mg/dL"), "hemoglobin": U(9.0, "g/dL"),
                        "phosphate": U(7.2, "mg/dL"), "white_blood_cell_count": U(41.1, "10*3/uL"), "band_neutrophils_percent": U(30, "%"),
                        "troponin_i": U(0.39, "ng/mL"), "alanine_aminotransferase": U(315, "U/L"), "bicarbonate": U(18.5, "mmol/L"),
                        "arterial_ph": U(7.22, "1"), "albumin": U(2.8, "g/dL"), "platelet_count": U(183, "10*3/uL")})
    r = _ranks(rep)
    assert "renal_failure_marked" in _syn(rep)
    assert min(r.get("acute_kidney_injury", 99), r.get("chronic_kidney_disease", 99)) <= 5
    assert "sepsis_bandemia" in _syn(rep) and r.get("sepsis", 99) <= 5
    assert _p(rep, "nafl_d") < 0.5  # ALT 315 is an acute hepatocellular injury, not fatty liver


# 3. Troponin I 506 ng/mL is myocardial infarction whatever the CK.
def test_massive_troponin_overrides_ck_exclusion(engine):
    rep = _rep(engine, {"troponin_i": U(506.16, "ng/mL"), "creatine_kinase_total": U(5067, "U/L"), "creatine_kinase_mb": U(629, "ng/mL"),
                        "aspartate_aminotransferase": U(1503, "U/L"), "alanine_aminotransferase": U(405, "U/L"), "creatinine": U(2.2, "mg/dL"),
                        "blood_urea_nitrogen": U(33, "mg/dL"), "hemoglobin": U(13, "g/dL"), "potassium": U(4.8, "mmol/L")})
    r = _ranks(rep)
    assert "mi_massive_troponin" in _syn(rep)
    assert r.get("acute_myocardial_infarction", 99) <= 2
    for dx in ("serotonin_syndrome", "neuroleptic_malignant_syndrome", "malignant_catatonia"):
        assert _p(rep, dx) < 0.5, dx  # no drug / temperature context


# 4. Hyperkalaemic NAGMA with creatinine 1.93 / BUN 52 is renal failure, not RTA type 4 x3.
def test_rta4_does_not_outrank_renal_failure(engine):
    rep = _rep(engine, {"potassium": U(5.6, "mmol/L"), "bicarbonate": U(14, "mmol/L"), "chloride": U(112, "mmol/L"), "sodium": U(133, "mmol/L"),
                        "creatinine": U(1.93, "mg/dL"), "blood_urea_nitrogen": U(52, "mg/dL"), "glucose": U(180, "mg/dL"), "hemoglobin": U(8.9, "g/dL")})
    r = _ranks(rep)
    assert min(r.get("acute_kidney_injury", 99), r.get("chronic_kidney_disease", 99)) <= 3
    rta = [k for k in r if k.startswith("renal_tubular_acidosis")]
    assert sum(1 for k in rta if r[k] <= 5) <= 1  # at most one family member in the top-5


# 5. Chronicity markers transfer the renal signal to CKD instead of erasing it.
def test_chronicity_markers_do_not_erase_renal_entry(engine):
    rep = _rep(engine, {"creatinine": U(3.1, "mg/dL"), "blood_urea_nitrogen": U(60, "mg/dL"), "hemoglobin": U(9.2, "g/dL"),
                        "phosphate": U(5.8, "mg/dL"), "potassium": U(5.1, "mmol/L"), "bicarbonate": U(19, "mmol/L")})
    assert max(_p(rep, "chronic_kidney_disease"), _p(rep, "acute_kidney_injury")) >= 0.6
    assert _p(rep, "chronic_kidney_disease") >= _p(rep, "acute_kidney_injury")


# 6. Salience re-ranking: co_* pairs and non-severe electrolyte findings sit below diseases of p >= 0.5.
def test_salience_reranking_demotes_pairs_and_low_salience_findings(engine):
    rep = _rep(engine, {"glucose": U(380, "mg/dL"), "bicarbonate": U(12, "mmol/L"), "anion_gap": U(24, "mmol/L"), "chloride": U(96, "mmol/L"),
                        "sodium": U(134, "mmol/L"), "phosphate": U(5.2, "mg/dL"), "potassium": U(5.3, "mmol/L"), "creatinine": U(1.4, "mg/dL")})
    dd = rep["differential_diagnosis"]
    ids = [d["disease_id"] for d in dd]
    first_co = next((i for i, x in enumerate(ids) if x.startswith("co_")), None)
    last_disease = max(i for i, d in enumerate(dd) if d["probability"] >= 0.5 and not d["disease_id"].startswith("co_"))
    assert first_co is None or first_co > last_disease
    r = _ranks(rep)
    for low in ("hypochloremia", "hyperphosphatemia"):
        if low in r and r["diabetic_ketoacidosis" if "diabetic_ketoacidosis" in r else "metabolic_acidosis"] > 0:
            assert r[low] > r.get("diabetic_ketoacidosis", r.get("metabolic_acidosis", 0)), low
    # probabilities themselves are untouched by the re-ranking
    assert all(0.0 <= d["probability"] <= 1.0 for d in dd)


# 7. Albumin-corrected calcium normal -> hypocalcaemia is not asserted.
def test_pseudohypocalcemia_guard(engine):
    rep = _rep(engine, {"calcium_total": U(7.9, "mg/dL"), "albumin": U(2.4, "g/dL"), "creatinine": U(0.9, "mg/dL"), "sodium": U(138, "mmol/L")})
    assert "pseudohypocalcemia_guard" in _syn(rep)
    assert _p(rep, "hypocalcemia") < 0.5


def test_true_hypocalcemia_still_fires_with_ionised(engine):
    rep = _rep(engine, {"calcium_total": U(6.8, "mg/dL"), "albumin": U(2.4, "g/dL"), "calcium_ionized": U(0.92, "mmol/L")})
    assert "pseudohypocalcemia_guard" not in _syn(rep)
    assert _p(rep, "hypocalcemia") >= 0.5


# 8. Mild DKA tier (ADA/EASD 2024) when ketones are unmeasured.
def test_mild_dka_tier(engine):
    rep = _rep(engine, {"glucose": U(304, "mg/dL"), "bicarbonate": U(17, "mmol/L"), "anion_gap": U(17, "mmol/L"), "sodium": U(136, "mmol/L"),
                        "potassium": U(4.9, "mmol/L"), "creatinine": U(1.1, "mg/dL")})
    assert "dka_mild_ketones_unmeasured" in _syn(rep)
    assert _ranks(rep).get("diabetic_ketoacidosis", 99) <= 5


def test_mild_dka_tier_vetoed_by_negative_ketones(engine):
    rep = _rep(engine, {"glucose": U(304, "mg/dL"), "bicarbonate": U(17, "mmol/L"), "anion_gap": U(17, "mmol/L"),
                        "beta_hydroxybutyrate": U(0.4, "mmol/L"), "lactate": U(4.5, "mmol/L")})
    assert "dka_mild_ketones_unmeasured" not in _syn(rep)


# 9. Chronic HBV flare keeps its specific diagnosis above the generic hepatocellular pattern.
def test_specific_hepatitis_serology_beats_generic_pattern(engine):
    rep = _rep(engine, {"alanine_aminotransferase": U(620, "U/L"), "aspartate_aminotransferase": U(410, "U/L"),
                        "hepatitis_b_surface_antigen": U(1, "1"), "hepatitis_b_dna_quantitative": U(2.5e6, "IU/mL"), "total_bilirubin": U(2.1, "mg/dL")})
    assert "acute_hepatocellular_injury" not in _syn(rep)
    r = _ranks(rep)
    assert min(r.get("chronic_hepatitis_b", 99), r.get("hepatitis_b", 99)) <= 2


# 10. Female urate 6.3 mg/dL in an otherwise healthy adult is not asserted as a pattern.
def test_female_urate_borderline_needs_cofinding(engine):
    rep = _rep(engine, {"uric_acid": U(6.3, "mg/dL"), "creatinine": U(0.7, "mg/dL"), "triglycerides": U(90, "mg/dL"), "glucose": U(88, "mg/dL")},
               {"age": 40, "sex": "female"})
    assert "hyperuricemia_female" not in _syn(rep)
    rep2 = _rep(engine, {"uric_acid": U(6.3, "mg/dL"), "creatinine": U(0.7, "mg/dL"), "triglycerides": U(240, "mg/dL")}, {"age": 40, "sex": "female"})
    assert "hyperuricemia_female" in _syn(rep2)


# ---- extension 6c: clinical-confirmation ceilings -------------------------
def test_thyroid_storm_needs_systemic_markers(engine):
    rep = _rep(engine, {"thyroid_stimulating_hormone": U(0.01, "mIU/L"), "free_thyroxine": U(3.1, "ng/dL")}, {"age": 40, "sex": "female"})
    assert _p(rep, "hyperthyroidism") >= 0.8
    assert _p(rep, "thyroid_storm") < 0.5 and _p(rep, "atrial_fibrillation_hyperthyroid") < 0.5
    rep2 = _rep(engine, {"thyroid_stimulating_hormone": U(0.01, "mIU/L"), "free_thyroxine": U(3.1, "ng/dL")}, {"age": 40, "sex": "female", "heart_rate": 140})
    assert "thyrotox_no_systemic_guard" not in _syn(rep2)


def test_shock_label_requires_hemodynamics(engine):
    obs = {"lactate": U(5.0, "mmol/L"), "white_blood_cell_count": U(19, "10*3/uL"), "creatinine": U(2.0, "mg/dL"), "platelet_count": U(90, "10*3/uL"), "procalcitonin": U(8, "ng/mL")}
    rep = _rep(engine, obs)
    assert _p(rep, "sepsis") >= 0.8
    assert max(_p(rep, "septic_shock"), _p(rep, "septic_shock_severe_lactic_acidosis")) < 0.5
    rep2 = _rep(engine, obs, {"age": 55, "sex": "male", "vasopressor_required": True})
    assert max(_p(rep2, "septic_shock"), _p(rep2, "septic_shock_severe_lactic_acidosis")) >= 0.5


def test_isolated_ddimer_does_not_assert_pe(engine):
    rep = _rep(engine, {"d_dimer": U(1.8, "mg/L FEU")})
    assert _p(rep, "pulmonary_embolism") < 0.5 and _p(rep, "aortic_dissection") < 0.5
