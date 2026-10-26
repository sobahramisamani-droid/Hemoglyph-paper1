"""Property-based invariants for the rule engine (seeded random panels; no external dependency).

P1 determinism            identical input -> identical differential (ids, order, probabilities)
P2 unit invariance        glucose/creatinine/bilirubin in SI vs conventional -> identical differential
P3 directional monotonicity  moving a defining analyte further past its own threshold never lowers the
                           probability of the entity it defines (K -> hyperkalaemia, creatinine -> renal,
                           Hb -> anaemia, glucose -> hyperglycaemia, platelets -> thrombocytopenia)
P4 absent-key analyte     removing the defining analyte never *raises* the entity's probability
Run alone (engine ~0.4 s per call): python -m pytest tests/test_properties.py -q
"""
import random, pytest
import analyse_gidlines as ag

E = ag.ClinicalRuleEngine()
CTX = {"age_years": 55, "sex_at_birth": "male", "encounter": "inpatient"}
BASE = {"sodium": (140, "mmol/L"), "potassium": (4.2, "mmol/L"), "chloride": (103, "mmol/L"), "bicarbonate": (25, "mmol/L"),
        "creatinine": (0.9, "mg/dL"), "blood_urea_nitrogen": (14, "mg/dL"), "glucose": (95, "mg/dL"), "hemoglobin": (14.5, "g/dL"),
        "platelet_count": (240, "10^9/L"), "white_blood_cell_count": (7.0, "10^9/L"), "albumin": (4.1, "g/dL")}

def panel(over=None, drop=()):
    p = {k: {"value": v, "unit": u} for k, (v, u) in BASE.items() if k not in drop}
    for k, (v, u) in (over or {}).items(): p[k] = {"value": v, "unit": u}
    return p

def diff(p):
    return E.interpret(p, None, CTX).to_dict()["differential_diagnosis"]

def prob(d, *ids):
    return max([x["probability"] for x in d if x["disease_id"] in ids] or [0.0])

def jitter(rng):
    return {k: (round(v * rng.uniform(0.97, 1.03), 2), u) for k, (v, u) in BASE.items()}

# ---- P1 ----
def test_p1_determinism():
    rng = random.Random(1)
    for _ in range(5):
        p = panel(jitter(rng)); a = diff(p); b = diff(p)
        assert [(x["disease_id"], round(x["probability"], 6)) for x in a] == [(x["disease_id"], round(x["probability"], 6)) for x in b]

# ---- P2 ----
@pytest.mark.parametrize("feat,conv,si,unit_si", [("glucose", 300, 16.65, "mmol/L"), ("creatinine", 2.7, 238.7, "umol/L")])
def test_p2_unit_invariance(feat, conv, si, unit_si):
    a = diff(panel({feat: (conv, BASE[feat][1])})); b = diff(panel({feat: (si, unit_si)}))
    assert [x["disease_id"] for x in a[:10]] == [x["disease_id"] for x in b[:10]]
    assert all(abs(x["probability"] - y["probability"]) < 1e-3 for x, y in zip(a[:10], b[:10]))  # 16.65 mmol/L = 299.97 mg/dL; fuzzy memberships are continuous

# ---- P3 ----
MONO = [  # feature, unit, start, steps (further past threshold), entity ids
    ("potassium", "mmol/L", [5.6, 6.0, 6.5, 7.0], ("hyperkalemia",)),
    ("creatinine", "mg/dL", [1.6, 2.2, 3.0, 4.5], ("acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "chronic_kidney_disease", "renal_impairment")),
    ("hemoglobin", "g/dL", [11.5, 10.0, 8.5, 7.0], ("anemia", "anemia_pattern")),
    ("glucose", "mg/dL", [220, 300, 400, 550], ("hyperglycemia", "hyperglycemia_pattern", "diabetes_mellitus", "type_2_diabetes")),
    ("platelet_count", "10^9/L", [120, 90, 60, 30], ("thrombocytopenia", "thrombocytopenia_pattern")),
]
MONO += [
    ("sodium", "mmol/L", [133, 129, 124, 118], ("hyponatremia", "severe_hyponatremia")),
    ("sodium", "mmol/L", [147, 152, 158, 165], ("hypernatremia", "severe_hypernatremia")),
    ("potassium", "mmol/L", [3.3, 3.0, 2.6, 2.2], ("hypokalemia", "severe_hypokalemia")),
    ("bicarbonate", "mmol/L", [20, 17, 13, 9], ("metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "normal_anion_gap_metabolic_acidosis")),
    ("white_blood_cell_count", "10^9/L", [12.5, 16, 22, 30], ("leukocytosis", "leukocytosis_pattern")),
    ("white_blood_cell_count", "10^9/L", [3.5, 2.8, 2.0, 1.2], ("leukopenia", "leukopenia_pattern")),
    ("glucose", "mg/dL", [65, 55, 45, 35], ("fasting_hypoglycemia", "hypoglycemia", "severe_hypoglycemia")),
    ("platelet_count", "10^9/L", [460, 550, 700, 900], ("thrombocytosis", "thrombocytosis_pattern")),
    # albumin: no `hypoalbuminemia` finding entity exists in registry 14.2 (isolated albumin 1.8 g/dL lists only
    # cirrhosis 0.30 / malnutrition 0.27) - recorded as an open registry gap in docs/V8_LOGIC_ALGORITHM_FACTCHECK.md
]
# v8.1 (2026-10-26): the creatinine inversion found by this test (renal lead 0.828 -> 0.792) was traced to the
# finding-demotion passes capping a strong finding to 95 % of a presumptive (< 0.80) AKI; fixed by applying the
# existing "a weak explainer organises but does not lower a better-established finding" rule uniformly.
@pytest.mark.parametrize("feat,unit,steps,ids", MONO, ids=[f"{m[0]}-{m[3][0]}" for m in MONO])
def test_p3_directional_monotonicity(feat, unit, steps, ids):
    rng = random.Random(hash(feat) & 0xffff)
    viol = []
    for rep in range(3):
        base = jitter(rng); prev = -1.0
        for v in steps:
            base[feat] = (v, unit); pr = prob(diff(panel(base)), *ids)
            if pr + 1e-9 < prev - 0.02:  # tolerate 2-point jitter from covering logic
                viol.append((rep, v, round(prev, 3), round(pr, 3)))
            prev = max(prev, pr)
        assert prev >= 0.5, f"{feat}: entity {ids} never asserted (>= 0.5) even at {steps[-1]} {unit} - stale id or missing rule"
    assert not viol, f"{feat}: probability fell when moving further past threshold: {viol}"

# ---- P4 ----
@pytest.mark.parametrize("feat,unit,val,ids", [("potassium", "mmol/L", 6.4, ("hyperkalemia",)), ("hemoglobin", "g/dL", 8.0, ("anemia", "anemia_pattern")),
                                                ("platelet_count", "10^9/L", 45, ("thrombocytopenia", "thrombocytopenia_pattern"))])
def test_p4_absent_key_analyte_never_raises(feat, unit, val, ids):
    with_key = prob(diff(panel({feat: (val, unit)})), *ids)
    without = prob(diff(panel(drop=(feat,))), *ids)
    assert without <= with_key + 1e-9 and without < 0.5


# ---- P5 context invariants ----
def test_p5_documented_ckd_never_raises_aki():
    obs = panel({"creatinine": (2.2, "mg/dL")})
    plain = prob(diff(obs), "acute_kidney_injury")
    ctx_ckd = dict(CTX, conditions=["chronic kidney disease"])
    with_ckd = max([x["probability"] for x in E.interpret(obs, None, ctx_ckd).to_dict()["differential_diagnosis"] if x["disease_id"] == "acute_kidney_injury"] or [0.0])
    assert with_ckd <= plain + 1e-9

def test_p6_borderline_flags_are_consistent():
    r = E.interpret(panel({"sodium": (136, "mmol/L"), "potassium": (5.1, "mmol/L")}), None, CTX).to_dict()
    b = {x["feature_id"]: x for x in r["borderline_values"]}
    assert "sodium" in b and 0.10 < b["sodium"]["p_below_low"] < 0.90
    assert "potassium" in b and 0.10 < b["potassium"]["p_above_high"] < 0.90
    r2 = E.interpret(panel({"sodium": (120, "mmol/L")}), None, CTX).to_dict()
    assert all(x["feature_id"] != "sodium" for x in r2["borderline_values"])  # 7 sigma below: not borderline
