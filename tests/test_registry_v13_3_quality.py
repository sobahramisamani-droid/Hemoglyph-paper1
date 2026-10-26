"""Structural tests for registry patch 13.3.0 (systematic defect-class repair).
Runs against eval/patches/cand/HEMOGLYPH_GUIDELINE_REGISTRY_v13_3_0_candidate.json.br if present, else skips.
"""
import json, os, re, subprocess, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, "eval", "patches", "cand", "HEMOGLYPH_GUIDELINE_REGISTRY_v13_3_0_candidate.json.br")
pytestmark = pytest.mark.skipif(not os.path.exists(CAND), reason="13.3.0 candidate not built")


@pytest.fixture(scope="module")
def reg():
    import brotli
    return json.loads(brotli.decompress(open(CAND, "rb").read()))


@pytest.fixture(scope="module")
def scan():
    subprocess.run([sys.executable, os.path.join(ROOT, "eval", "registry_defect_scan.py"), CAND], check=True, capture_output=True)
    return json.load(open(os.path.join(ROOT, "eval", "results", "registry_defect_scan_13.3.0.json")))


def leaves(e):
    if not isinstance(e, dict): return
    if "feature_id" in e: yield e
    for k in ("all", "any", "operands"):
        for x in e.get(k) or []: yield from leaves(x)


def test_version(reg):
    assert reg["registry_metadata"]["version"].startswith("13.3.0")
    assert any(p["patch"] == "13.3.0" for p in reg["registry_metadata"]["patches"])


def test_mechanical_classes_zero(scan):
    for k in ("D3", "D4", "D6", "D7", "D8", "D9", "D10"):
        assert scan.get(k, []) == [], (k, scan.get(k)[:3])


def test_d1_residue_is_documented_exception(scan):
    # ferritin / serum iron: WHO cut-offs are sex-independent (documented); staging rules are not proposing rules
    for x in scan.get("D1", []):
        # dengue warning sign: WHO defines haemoconcentration as a rise, the absolute Hct cut-off is a supportive non-proposing rule
        assert x[1] in ("ferritin", "serum_iron") or "staging" in x[0] or "component" in x[0] or x[0] == "dengue_fever_who_warning_signs_lab_cur13", x


def test_d5_residue_is_keep_list(scan):
    sys.path.insert(0, os.path.join(ROOT, "eval", "patches"))
    from registry_v13_3_0_quality import D5_KEEP
    assert {x[0] for x in scan.get("D5", [])} <= D5_KEEP


def test_troponin_units(reg):
    for r in reg["rules"].values():
        if not r.get("executable"): continue
        for l in leaves(r["expression"]):
            if l["feature_id"].startswith("high_sensitivity_troponin") and l.get("unit") == "ng/mL":
                assert float(l["value"]) < 1, (r["rule_id"], l)


def test_female_variants(reg):
    RU = reg["rules"]
    fem = [r for k, r in RU.items() if k.endswith("_f13_3")]
    assert len(fem) >= 300
    for f in fem[:400]:
        m = RU[f["rule_id"][:-len("_f13_3")]]
        assert f["population"]["sex"] == "female" and m["population"]["sex"] == "male"
        for lf, lm in zip(leaves(f["expression"]), leaves(m["expression"])):
            if lf["value"] != lm["value"]:
                if lf["operator"] in (">", ">="): assert float(lf["value"]) < float(lm["value"])
                else: assert float(lf["value"]) < float(lm["value"])  # LLN-type thresholds are lower for females too


def test_named_sex_rules(reg):
    for k, r in reg["rules"].items():
        if not r.get("executable"): continue
        if re.search(r"(^|_)female(_|$)", k): assert r["population"]["sex"] == "female", k
        elif re.search(r"(^|_)male(_|$)", k): assert r["population"]["sex"] == "male", k


def test_risk_rules_rehomed(reg):
    RU = reg["rules"]
    for rid in ("acute_myocardial_infarction_total_cholesterol_screen_v1", "acute_myocardial_infarction_ldl_direct_target_v1",
                "acute_myocardial_infarction_hs_crp_cardiovascular_risk_v1"):
        assert RU[rid]["disease_id"] == "atherosclerotic_cardiovascular_risk_lipid_pattern"
        assert rid not in reg["diseases"]["acute_myocardial_infarction"]["rule_ids"]


def test_etiologic_gated(reg):
    RU, D = reg["rules"], reg["diseases"]
    for did in ("melanoma", "osteosarcoma", "amyotrophic_lateral_sclerosis", "aortic_dissection"):
        for rid in D[did]["rule_ids"]:
            r = RU[rid]
            if r.get("executable") and r["rule_type"] in ("screening", "diagnostic_criterion"):
                assert all((l.get("context") or {}).get("clinical_suspicion") for l in leaves(r["expression"])), rid
