"""Vision multi-pass agreement merge (pure function, no network)."""
from __future__ import annotations
import os, sys, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.disable(logging.CRITICAL)
import ocr  # noqa: E402

P1 = [{"test_name": "Hb", "value": 13.5, "unit": "g/dL", "flag": None},
      {"test_name": "WBC", "value": 7.1, "unit": "10^3/uL", "flag": None},
      {"test_name": "PLT", "value": 250, "unit": "10^3/uL"}]
P2 = [{"test_name": "Hb", "value": 13.5, "unit": "g/dL", "flag": None},
      {"test_name": "W.B.C", "value": 7.7, "unit": "10^3/uL", "flag": None},
      {"test_name": "Glucose", "value": 95, "unit": "mg/dL"}]


def test_merge_tags():
    m = {r["test_name"]: r for r in ocr.merge_vision_passes([P1, P2])}
    assert m["Hb"]["_agreement"] == "agree" and m["Hb"]["_passes"] == 2
    assert m["WBC"]["_agreement"] == "disagree" and m["WBC"]["_alternatives"][0]["value"] == 7.7
    assert m["PLT"]["_agreement"] == "single" and m["Glucose"]["_agreement"] == "single"


def test_majority_wins_with_three_passes():
    p3 = [{"test_name": "WBC", "value": 7.7, "unit": "10^3/uL", "flag": None}]
    m = {ocr._row_key(r): r for r in ocr.merge_vision_passes([P1, P2, p3])}
    assert m["wbc"]["value"] == 7.7 and m["wbc"]["_agreement"] == "disagree" and m["wbc"]["_passes"] == 3


def test_single_pass_is_untagged():
    m = ocr.merge_vision_passes([P1])
    assert all(r["_agreement"] == "agree" for r in m)


def test_pipeline_forces_review_on_disagreement():
    pipe = ocr.BloodLabPipeline(registry_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                          "HEMOGLYPH_FEATURE_REGISTRY.json"))
    out = pipe.process(json.dumps(ocr.merge_vision_passes([P1, P2])))
    by = {r["feature_id"]: r for r in out["results"]}
    assert by["white_blood_cell_count"]["requires_confirmation"] is True
    assert by["white_blood_cell_count"]["vision_agreement"] == "disagree"
    assert by["hemoglobin"]["requires_confirmation"] is False
    assert by["hemoglobin"]["confidence"] > by["glucose"]["confidence"]


def test_rbc_10e6_per_ul_is_not_relabelled_as_10e9_per_l():
    """Regression: '10^6/uL' (ASCII u) fell through to a regex fallback that
    mapped every 10^N count unit to 10^9/L, silently breaking the RBC identities."""
    pipe = ocr.BloodLabPipeline(registry_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                          "HEMOGLYPH_FEATURE_REGISTRY.json"))
    out = pipe.process(json.dumps([{"test_name": "RBC", "value": 4.5, "unit": "10^6/uL"},
                                   {"test_name": "WBC", "value": 7.0, "unit": "10^3/uL"}]))
    by = {r["feature_id"]: r for r in out["results"]}
    assert by["red_blood_cell_count"]["unit"].lower().replace("µ", "u") in ("10^6/ul", "10^12/l")
    assert by["white_blood_cell_count"]["unit"] == "10^9/L" and by["white_blood_cell_count"]["value"] == 7.0


def test_end_to_end_joint_repair_through_pipeline():
    pipe = ocr.BloodLabPipeline(registry_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                          "HEMOGLYPH_FEATURE_REGISTRY.json"))
    rows = [{"test_name": "Hb", "value": 18.5, "unit": "g/dL"}, {"test_name": "Hct", "value": 48.5, "unit": "%"},
            {"test_name": "RBC", "value": 4.5, "unit": "10^6/uL"}, {"test_name": "MCV", "value": 90, "unit": "fL"},
            {"test_name": "MCH", "value": 30, "unit": "pg"}, {"test_name": "MCHC", "value": 33.3, "unit": "g/dL"}]
    out = pipe.process(json.dumps(rows))
    assert out["consistency"]["checks_run"] >= 4
    assert sorted(out["consistency"]["joint_repairs"]) == ["hematocrit", "hemoglobin"]
