"""LabPanel-Check: the standalone scorer must reproduce the frozen black-box benchmark numbers exactly
(manuscript Table 6 / Supplementary Note 13; eval/blackbox/results.json; eval/results/nhanes_2017/b5_blind_specificity.md)."""
import os, sys, json, gzip, hashlib
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LPC = os.path.join(HERE, "..", "eval", "labpanel_check")
sys.path.insert(0, LPC)
import score as lpc  # noqa: E402

REQ = ["panels.json.gz", "label_map.json", "reads_reference_engine.json.gz", "reads_reference_llm.json.gz", "spec.json"]
pytestmark = pytest.mark.skipif(not all(os.path.exists(os.path.join(LPC, f)) for f in REQ), reason="package not built")


@pytest.fixture(scope="module")
def sc():
    return lpc.Scorer(lpc.load_json(os.path.join(LPC, "panels.json.gz")), lpc.load_json(os.path.join(LPC, "label_map.json")))


def test_package_shape(sc):
    props = {}
    for rec in sc.panels.values():
        props[rec["property"]] = props.get(rec["property"], 0) + 1
    assert props == {"REF": 40, "P2": 40, "P3": 40, "P4": 60, "P5": 40, "P6": 70}
    assert len(sc.groups) == 31
    for rec in sc.panels.values():
        assert {"age", "sex", "panel", "property", "id"} <= set(rec)


def test_engine_reference_card(sc):
    reads = lpc.load_json(os.path.join(LPC, "reads_reference_engine.json.gz"))
    c = sc.score(reads, reads)
    assert c["missing_panel_ids"] == []
    assert c["P1_determinism"] == {"identical": 290, "n": 290}
    assert (c["P2_unit_invariance"]["identical"], c["P2_unit_invariance"]["n"]) == (39, 40)
    assert round(c["P2_unit_invariance"]["mean_jaccard"], 2) == 0.99
    assert [d["id"] for d in c["P2_unit_invariance"]["non_identical_pairs"]] == ["P2:508973"]
    assert (c["P3_presentation_invariance"]["identical"], c["P3_presentation_invariance"]["n"]) == (35, 40)
    assert round(c["P3_presentation_invariance"]["mean_jaccard"], 2) == 0.95
    assert (c["P4_monotonicity"]["violations"], c["P4_monotonicity"]["n"]) == (2, 20)
    p5 = c["P5_absent_analyte"]
    assert (p5["unsupported"], p5["n"], p5["strict_unsupported"], p5["strict_n"]) == (3, 40, 1, 29)
    p6 = c["P6_healthy"]
    assert (p6["false_assertions"], p6["n_healthy"]) == (0, 40)
    det = {k: (v["detected"], v["n"]) for k, v in p6["detection"].items()}
    # registry 15.x caps single-panel CKD assertions below 0.5 (KDIGO chronicity), hence 10/18 here versus 15/18 in the
    assert det == {"diabetes": (13, 16), "ckd": (10, 18), "anemia": (13, 13), "iron_deficiency": (7, 8), "hypercholesterolemia": (7, 7)}


def test_llm_reference_card(sc):
    reads = lpc.load_json(os.path.join(LPC, "reads_reference_llm.json.gz"))
    c = sc.score(reads)
    assert c["missing_panel_ids"] == []
    assert (c["P2_unit_invariance"]["identical"], c["P2_unit_invariance"]["n"]) == (8, 40)
    assert round(c["P2_unit_invariance"]["mean_jaccard"], 2) == 0.72
    assert (c["P3_presentation_invariance"]["identical"], c["P3_presentation_invariance"]["n"]) == (10, 40)
    assert round(c["P3_presentation_invariance"]["mean_jaccard"], 2) == 0.73
    assert (c["P4_monotonicity"]["violations"], c["P4_monotonicity"]["n"]) == (0, 20)
    p5 = c["P5_absent_analyte"]
    assert (p5["unsupported"], p5["n"], p5["strict_unsupported"], p5["strict_n"]) == (14, 40, 4, 29)
    p6 = c["P6_healthy"]
    assert (p6["false_assertions"], p6["n_healthy"]) == (4, 40)
    det = {k: (v["detected"], v["n"]) for k, v in p6["detection"].items()}
    assert det == {"diabetes": (16, 16), "ckd": (13, 18), "anemia": (12, 13), "iron_deficiency": (7, 8), "hypercholesterolemia": (7, 7)}


def test_manifest_matches_files():
    man = dict(line.split()[::-1] for line in open(os.path.join(LPC, "MANIFEST.sha256")) if line.strip())
    for name, sha in man.items():
        assert hashlib.sha256(open(os.path.join(LPC, name), "rb").read()).hexdigest() == sha, name


def test_missing_ids_are_reported(sc):
    c = sc.score({})
    assert len(c["missing_panel_ids"]) == 290
