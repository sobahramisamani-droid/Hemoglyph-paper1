"""Extension 7 — regression tests from the eICU-demo development-set error analysis (2026-10-22)."""
import logging, pytest
import analyse_gidlines as ag

logging.disable(logging.CRITICAL)


@pytest.fixture(scope="module")
def engine():
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40; return E


def _run(E, obs, pt):
    return E.interpret({k: {"value": v, "unit": u} for k, (v, u) in obs.items()}, None, pt).to_dict()


def _p(rep, dx):
    return max([d["probability"] for d in rep["differential_diagnosis"] if d["disease_id"] == dx] or [0.0])


def test_isolated_alt_is_not_cholestasis(engine):
    # eICU 144815: ALT 51, ALP 78 -> R 1.96 used to read "cholestatic" -> PBC 0.49
    rep = _run(engine, {"alanine_aminotransferase": (51, "U/L"), "aspartate_aminotransferase": (52, "U/L"), "alkaline_phosphatase": (78, "U/L"),
                        "total_bilirubin": (0.5, "mg/dL"), "albumin": (4.2, "g/dL")}, {"age_years": 34, "sex_at_birth": "female"})
    assert _p(rep, "primary_biliary_cholangitis") < 0.3 and _p(rep, "cholestasis") < 0.3


def test_true_cholestasis_still_fires(engine):
    rep = _run(engine, {"alanine_aminotransferase": (45, "U/L"), "alkaline_phosphatase": (420, "U/L"), "gamma_glutamyl_transferase": (310, "U/L"),
                        "total_bilirubin": (2.4, "mg/dL")}, {"age_years": 55, "sex_at_birth": "female"})
    assert _p(rep, "cholestasis") >= 0.5


def test_nephrotic_needs_proteinuria(engine):
    rep = _run(engine, {"albumin": (2.9, "g/dL"), "calcium_total": (7.8, "mg/dL"), "creatinine": (0.8, "mg/dL"), "hemoglobin": (10.9, "g/dL")},
               {"age_years": 57, "sex_at_birth": "female"})
    assert _p(rep, "nephrotic_syndrome") < 0.5
    rep2 = _run(engine, {"albumin": (2.4, "g/dL"), "urine_protein_to_creatinine_ratio": (5200, "mg/g"), "total_cholesterol": (310, "mg/dL")},
                {"age_years": 40, "sex_at_birth": "male"})
    assert _p(rep2, "nephrotic_syndrome") >= 0.7


def test_dka_with_lactic_acidosis(engine):
    # eICU 249805: glucose 665, HCO3 4, pH 6.94, lactate 11.5, Na 130, Cl 100 -> DKA was rank 9
    rep = _run(engine, {"glucose": (665, "mg/dL"), "bicarbonate": (4, "mmol/L"), "arterial_ph": (6.94, ""), "lactate": (11.5, "mmol/L"),
                        "sodium": (130, "mmol/L"), "chloride": (100, "mmol/L"), "potassium": (3.6, "mmol/L"), "creatinine": (1.5, "mg/dL")},
               {"age_years": 29, "sex_at_birth": "female"})
    assert _p(rep, "diabetic_ketoacidosis") >= 0.7
    assert _p(rep, "lactic_acidosis") >= 0.7


def test_dka_glucose_200_threshold_and_no_gas(engine):
    # eICU 374770: glucose 239, HCO3 8, no blood gas, Na 135 / Cl 106 (AG 21)
    rep = _run(engine, {"glucose": (239, "mg/dL"), "bicarbonate": (8, "mmol/L"), "sodium": (135, "mmol/L"), "chloride": (106, "mmol/L"),
                        "potassium": (4.3, "mmol/L"), "lactate": (0.7, "mmol/L")}, {"age_years": 26, "sex_at_birth": "male"})
    assert _p(rep, "diabetic_ketoacidosis") >= 0.7
    assert _p(rep, "metabolic_acidosis") >= 0.6


def test_pure_lactic_acidosis_not_called_dka(engine):
    # gap fully explained by lactate: glucose 260 (stress), HCO3 12, AG 22, lactate 14
    rep = _run(engine, {"glucose": (260, "mg/dL"), "bicarbonate": (12, "mmol/L"), "sodium": (138, "mmol/L"), "chloride": (104, "mmol/L"),
                        "lactate": (14, "mmol/L"), "arterial_ph": (7.15, "")}, {"age_years": 60, "sex_at_birth": "male"})
    assert _p(rep, "lactic_acidosis") >= 0.7
    assert _p(rep, "diabetic_ketoacidosis") < 0.6


def test_nonspecific_only_entities_capped(engine):
    rep = _run(engine, {"albumin": (2.0, "g/dL"), "hemoglobin": (8.1, "g/dL"), "mean_corpuscular_volume": (76.5, "fL"), "platelet_count": (388, "10^9/L")},
               {"age_years": 23, "sex_at_birth": "female"})
    assert _p(rep, "pellagra") <= 0.35 and _p(rep, "frailty") <= 0.35
    assert _p(rep, "anemia") >= 0.5  # findings are exempt


def test_hypertriglyceridemia_not_capped(engine):
    rep = _run(engine, {"triglycerides": (2100, "mg/dL"), "total_cholesterol": (310, "mg/dL")}, {"age_years": 45, "sex_at_birth": "male"})
    assert _p(rep, "hypertriglyceridemia") >= 0.6 or _p(rep, "severe_hypertriglyceridemia") >= 0.6


def test_co_self_pairs_dropped(engine):
    rep = _run(engine, {"glucose": (280, "mg/dL"), "glucose_random": (285, "mg/dL")}, {"age_years": 50, "sex_at_birth": "male"})
    assert not any(d["disease_id"] == "co_elevated_glucose_with_elevated_glucose_random" for d in rep["differential_diagnosis"])


def test_hhs_by_effective_osmolality(engine):
    # glucose 900, Na 150 -> effective osm 350 (no measured osmolality)
    rep = _run(engine, {"glucose": (900, "mg/dL"), "sodium": (150, "mmol/L"), "bicarbonate": (22, "mmol/L"), "creatinine": (2.0, "mg/dL"),
                        "blood_urea_nitrogen": (45, "mg/dL"), "chloride": (108, "mmol/L")}, {"age_years": 70, "sex_at_birth": "female"})
    assert _p(rep, "hyperosmolar_hyperglycemic_state") >= 0.7


# --- round 2 / 7b additions (2026-10-22) -------------------------------------
def _probs(obs, age=60, sex="female"):
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    rep = E.interpret({k: {"value": v, "unit": u} for k, (v, u) in obs.items()}, None,
                      {"age_years": age, "sex_at_birth": sex}).to_dict()
    return {d["disease_id"]: float(d["probability"]) for d in rep["differential_diagnosis"]}


def test_ckd_elderly_cr_bun_anemia_scores_ckd():
    p = _probs({"creatinine": (2.34, "mg/dL"), "blood_urea_nitrogen": (65, "mg/dL"), "hemoglobin": (10.4, "g/dL"),
              "mean_corpuscular_volume": (90, "fL"), "potassium": (4.6, "mmol/L")}, age=84)
    assert p.get("chronic_kidney_disease", 0) >= 0.6
    assert p.get("acute_kidney_injury", 0) >= 0.4  # chronicity undetermined: both listed


def test_rhabdo_aki_is_not_called_ckd():
    p = _probs({"creatinine": (3.0, "mg/dL"), "creatine_kinase": (20000, "U/L"), "potassium": (5.6, "mmol/L"),
              "blood_urea_nitrogen": (40, "mg/dL")}, age=28, sex="male")
    assert p.get("acute_kidney_injury", 0) > p.get("chronic_kidney_disease", 0)
    assert p.get("chronic_kidney_disease", 0) < 0.5


def test_normal_mcv_panel_has_no_thalassemia_trait_vote():
    p = _probs({"hemoglobin": (14.2, "g/dL"), "mean_corpuscular_volume": (88, "fL"), "red_blood_cell_count": (4.8, "10^12/L"),
              "red_cell_distribution_width_cv": (12.8, "%"), "ferritin": (80, "ng/mL"), "platelet_count": (240, "10^9/L")}, age=40, sex="male")
    assert p.get("thalassemia_trait", 0) < 0.2


def test_true_microcytosis_still_scores_thalassemia_trait():
    p = _probs({"hemoglobin": (12.1, "g/dL"), "mean_corpuscular_volume": (66, "fL"), "red_blood_cell_count": (5.9, "10^12/L"),
              "red_cell_distribution_width_cv": (12.8, "%"), "ferritin": (80, "ng/mL")}, age=40, sex="male")
    assert p.get("thalassemia_trait", 0) >= 0.7
