"""Structured-row value/unit parsing (vision path) and dimensional count units."""
from __future__ import annotations
import os, sys, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.disable(logging.CRITICAL)
import ocr  # noqa: E402
import pytest  # noqa: E402

REG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "HEMOGLYPH_FEATURE_REGISTRY.json")


@pytest.mark.parametrize("cell,unit,expect", [
    ("7,1", None, (7.1, None, None)), ("1,250", None, (1250.0, None, None)), ("1,234.5", None, (1234.5, None, None)),
    ("1.250.000", None, (1250000.0, None, None)), ("<0.5", None, (0.5, None, "<")), ("> 150", None, (150.0, None, ">")),
    ("≥ 60", "mL/min", (60.0, "mL/min", ">=")), ("13.5 g/dL", None, (13.5, "g/dL", None)), ("5.7%", None, (5.7, "%", None)),
    ("۱۳٫۵", None, (13.5, None, None)), ("12,5 mg/dL", None, (12.5, "mg/dL", None)), (4.5, "10^6/uL", (4.5, "10^6/uL", None)),
])
def test_parse_value_cell(cell, unit, expect):
    num, u, q, _ = ocr._parse_value_cell(cell, unit)
    assert (num, u, q) == expect


def test_qualitative_passes_through():
    num, _, _, rest = ocr._parse_value_cell("Negative", None)
    assert num is None and rest == "Negative"


@pytest.mark.parametrize("unit,expect", [
    ("x10^3/µL", ("10^9/L", 1.0)), ("10^3/uL", ("10^9/L", 1.0)), ("10^3/mm3", ("10^9/L", 1.0)), ("10e3/uL", ("10^9/L", 1.0)),
    ("10³/µL", ("10^9/L", 1.0)), ("10⁹/L", ("10^9/L", 1.0)), ("K/uL", ("10^9/L", 1.0)), ("thou/mm3", ("10^9/L", 1.0)),
    ("10^6/uL", ("10^12/L", 1.0)), ("M/uL", ("10^12/L", 1.0)), ("mil/cumm", ("10^12/L", 1.0)), ("T/L", ("10^12/L", 1.0)),
    ("G/L", ("10^9/L", 1.0)), ("/uL", ("10^9/L", 0.001)), ("/mm3", ("10^9/L", 0.001)), ("cells/µL", ("10^9/L", 0.001)),
    ("10^3/mL", ("10^9/L", 0.001)), ("lakh/cumm", ("10^9/L", 100.0)),
    ("g/dL", None), ("g/L", None), ("mg/dL", None), ("mmol/L", None), ("mL/min", None), ("IU/L", None), ("%", None),
])
def test_parse_count_unit(unit, expect):
    assert ocr._parse_count_unit(unit) == expect


def test_pipeline_mass_units_untouched_and_counts_canonical():
    pipe = ocr.BloodLabPipeline(registry_path=REG)
    rows = [{"test_name": "Hb", "value": "13.5 g/dL", "unit": None}, {"test_name": "WBC", "value": "7,1", "unit": "G/L"},
            {"test_name": "Platelets", "value": "250", "unit": "x10^3/µL"}, {"test_name": "CRP", "value": "<0.5", "unit": "mg/L"}]
    by = {r["feature_id"]: r for r in pipe.process(json.dumps(rows))["results"]}
    assert (by["hemoglobin"]["value"], by["hemoglobin"]["unit"]) == (13.5, "g/dL")
    assert (by["white_blood_cell_count"]["value"], by["white_blood_cell_count"]["unit"]) == (7.1, "10^9/L")
    assert (by["platelet_count"]["value"], by["platelet_count"]["unit"]) == (250.0, "10^9/L")
    assert by["c_reactive_protein"]["value"] == 0.5 and by["c_reactive_protein"]["value_qualifier"] == "<"


def test_structured_json_repair_and_wrappers():
    S = ocr.BloodLabPipeline._try_tafsir_structured
    rows = S("""```json
{"results": [{'test_name': 'WBC', 'value': 7.1, 'unit': '10^3/uL', 'flag': None, 'reference_range': '4.0-10.0'},
 {test_name: "Hb", value: "12-16", unit: "g/dL", reference_range: "13.5",},  // comment
 {"Test": "PLT", "Result": "g/dL", "Units": 250, "Range": "150-450"},
 {"test_name": "Glucose", "value": NaN, "unit": "mg/dL"}
]}
```""")
    by = {r["test_name"]: r for r in rows}
    assert by["WBC"]["value"] == 7.1
    assert by["Hb"]["value"] == "13.5" and by["Hb"]["reference_range"] == "12-16" and by["Hb"]["_column_shift"]
    assert by["PLT"]["value"] == 250 and by["PLT"]["unit"] == "g/dL" and "Result" not in by["PLT"]
    assert by["Glucose"].get("value") is None


def test_truncated_array_salvaged():
    S = ocr.BloodLabPipeline._try_tafsir_structured
    rows = S('[{"test_name":"WBC","value":7.1,"unit":"10^3/uL"},{"test_name":"Hb","value":13.5,"unit":"g/dL"},{"test_name":"PLT","val')
    assert [r["test_name"] for r in rows] == ["WBC", "Hb"]


def test_scale_mismatch_against_printed_interval():
    assert ocr._scale_mismatch_against_reference(950, 70, 99) == 95.0
    assert ocr._scale_mismatch_against_reference(1.35, 12, 16) == 13.5
    assert ocr._scale_mismatch_against_reference(95, 70, 99) is None
    assert ocr._scale_mismatch_against_reference(250, 70, 99) is None     # merely abnormal, not a decimal slip
    pipe = ocr.BloodLabPipeline(registry_path=REG)
    out = pipe.process(json.dumps([{"test_name": "Glucose", "value": 950, "unit": "mg/dL", "reference_range": "70-99"}]))
    r = out["results"][0]
    assert r["suggested_value"] == 95.0 and r["requires_confirmation"] and r["confidence"] < 0.9
