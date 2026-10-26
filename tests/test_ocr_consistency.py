"""Structural tests for ocr_consistency (no dataset: synthetic panels with a
known, deliberately injected OCR error). Each case states which field was
corrupted and how; the solver must (a) flag that field, (b) propose the
original reading, (c) leave the innocent fields un-penalised.

Run:  python tests/test_ocr_consistency.py
"""
from __future__ import annotations
import os
import sys
import copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ocr_consistency import validate_results, canonical_value  # noqa: E402


def rec(fid, value, unit, flag=None, lo=None, hi=None, conf=0.9):
    return {"feature_id": fid, "value": value, "unit": unit, "flag": flag,
            "report_range_low": lo, "report_range_high": hi, "confidence": conf,
            "requires_confirmation": False, "suggested_action": "accept", "warnings": [],
            "original_value": value}


CLEAN_CBC = [
    rec("hemoglobin", 13.5, "g/dL", lo=12, hi=16), rec("hematocrit", 40.5, "%", lo=36, hi=46),
    rec("red_blood_cell_count", 4.5, "10^6/uL"), rec("mean_corpuscular_volume", 90, "fL"),
    rec("mean_corpuscular_hemoglobin", 30, "pg"), rec("mean_corpuscular_hemoglobin_concentration", 33.3, "g/dL"),
    rec("white_blood_cell_count", 7.0, "10^9/L"), rec("neutrophils_percent", 60, "%"),
    rec("lymphocytes_percent", 30, "%"), rec("monocytes_percent", 6, "%"), rec("eosinophils_percent", 3, "%"),
    rec("basophils_percent", 1, "%"), rec("neutrophil_count_absolute", 4.2, "10^9/L"),
    rec("platelets", 250, "10^9/L"),
]
CLEAN_CHEM = [
    rec("total_cholesterol", 200, "mg/dL"), rec("hdl_cholesterol", 50, "mg/dL"),
    rec("triglycerides", 150, "mg/dL"), rec("ldl_cholesterol_calculated", 120, "mg/dL"),
    rec("total_bilirubin", 1.0, "mg/dL"), rec("direct_bilirubin", 0.3, "mg/dL"),
    rec("albumin", 4.2, "g/dL"), rec("total_protein", 7.0, "g/dL"),
    rec("blood_urea_nitrogen", 14, "mg/dL"), rec("urea", 30, "mg/dL"),
    rec("sodium", 140, "mmol/L"), rec("chloride", 104, "mmol/L"), rec("bicarbonate", 24, "mmol/L"),
    rec("creatinine", 0.9, "mg/dL"), rec("egfr_ckd_epi_creatinine", 95, "mL/min/1.73m2"),
]


def corrupt(panel, fid, new_value):
    p = copy.deepcopy(panel)
    for r in p:
        if r["feature_id"] == fid:
            r["value"] = new_value
            r["original_value"] = new_value
    return p


def get(panel, fid):
    return next(r for r in panel if r["feature_id"] == fid)


CASES = [
    # (name, panel, corrupted fid, expected suggested value or None)
    ("clean CBC: nothing flagged", CLEAN_CBC, None, None),
    ("clean chem: nothing flagged", CLEAN_CHEM, None, None),
    ("Hb 135 (dropped decimal)", corrupt(CLEAN_CBC, "hemoglobin", 135), "hemoglobin", 13.5),
    ("Hct 4.05 (shifted decimal)", corrupt(CLEAN_CBC, "hematocrit", 4.05), "hematocrit", 40.5),
    ("RBC 45 (x10)", corrupt(CLEAN_CBC, "red_blood_cell_count", 45), "red_blood_cell_count", 4.5),
    ("MCV 150 (odd one out, no glyph story)", corrupt(CLEAN_CBC, "mean_corpuscular_volume", 150), "mean_corpuscular_volume", 90),
    ("neutrophils 80 (glyph 6->8)", corrupt(CLEAN_CBC, "neutrophils_percent", 80), "neutrophils_percent", 60),
    ("platelets 25000 (x100) - plausibility only", corrupt(CLEAN_CBC, "platelets", 25000), "platelets", 250),
    ("direct bili 3.0 > total", corrupt(CLEAN_CHEM, "direct_bilirubin", 3.0), "direct_bilirubin", 0.3),
    ("LDL 12 (dropped zero)", corrupt(CLEAN_CHEM, "ldl_cholesterol_calculated", 12), "ldl_cholesterol_calculated", 120),
    ("TC 2000 (extra zero)", corrupt(CLEAN_CHEM, "total_cholesterol", 2000), "total_cholesterol", 200),
    ("albumin 42 g/dL (unit-scale)", corrupt(CLEAN_CHEM, "albumin", 42), "albumin", 4.2),
    ("urea 300 vs BUN 14", corrupt(CLEAN_CHEM, "urea", 300), "urea", 30),
    ("chloride 164 (glyph 0->6)", corrupt(CLEAN_CHEM, "chloride", 164), "chloride", 104),
    ("creatinine 9.0 vs eGFR 95", corrupt(CLEAN_CHEM, "creatinine", 9.0), "creatinine", 0.9),
    # genuinely abnormal but internally consistent panels must NOT be touched
    ("true microcytic anaemia (consistent)", [
        rec("hemoglobin", 8.1, "g/dL"), rec("hematocrit", 27.0, "%"), rec("red_blood_cell_count", 4.5, "10^6/uL"),
        rec("mean_corpuscular_volume", 60, "fL"), rec("mean_corpuscular_hemoglobin", 18, "pg"),
        rec("mean_corpuscular_hemoglobin_concentration", 30, "g/dL")], None, None),
    ("true leukaemia (WBC 142, consistent)", [
        rec("white_blood_cell_count", 142, "10^9/L"), rec("neutrophils_percent", 70, "%"),
        rec("lymphocytes_percent", 10, "%"), rec("monocytes_percent", 5, "%"), rec("eosinophils_percent", 5, "%"),
        rec("basophils_percent", 10, "%"), rec("neutrophil_count_absolute", 99.4, "10^9/L")], None, None),
    ("SI-unit report (mmol/L, g/L) consistent", [
        rec("hemoglobin", 135, "g/L"), rec("hematocrit", 0.405, "L/L"), rec("red_blood_cell_count", 4.5, "10^12/L"),
        rec("mean_corpuscular_volume", 90, "fL"), rec("mean_corpuscular_hemoglobin_concentration", 333, "g/L"),
        rec("total_cholesterol", 5.17, "mmol/L"), rec("hdl_cholesterol", 1.29, "mmol/L"),
        rec("triglycerides", 1.69, "mmol/L"), rec("ldl_cholesterol_calculated", 3.1, "mmol/L")], None, None),
    ("cholestasis: direct 4.0 of total 5.0 (consistent)", [
        rec("total_bilirubin", 5.0, "mg/dL"), rec("direct_bilirubin", 4.0, "mg/dL"), rec("indirect_bilirubin", 1.0, "mg/dL")],
     None, None),
]

TWO_ERRORS = corrupt(corrupt(CLEAN_CBC, "hemoglobin", 135), "neutrophils_percent", 80)
FLAG_CASE = [rec("hemoglobin", 13.5, "g/dL", flag="L", lo=12, hi=16), rec("glucose", 95, "mg/dL", flag="H", lo=70, hi=100)]


def run() -> bool:
    ok_all = True
    for name, panel, culprit, expect in CASES:
        panel = copy.deepcopy(panel)
        summary = validate_results(panel)
        suspects = set(summary["suspects"]) | set(summary["plausibility_violations"])
        innocents_hit = [r["feature_id"] for r in panel
                         if r["feature_id"] != culprit and (r["requires_confirmation"] or r["confidence"] < 0.85)]
        if culprit is None:
            good = not suspects and not innocents_hit and not summary["failed"]
            detail = f"failed={summary['failed']} innocents={innocents_hit}"
        else:
            r = get(panel, culprit)
            sugg = r.get("suggested_value")
            good = (culprit in suspects and r["requires_confirmation"]
                    and sugg is not None and abs(float(sugg) - expect) <= 0.06 * max(abs(expect), 1.0)
                    and not innocents_hit)
            detail = (f"suspects={sorted(suspects)} suggested={sugg} ({r.get('repair_reason')}) "
                      f"innocents_hit={innocents_hit}")
        ok_all &= good
        print(f"{'PASS' if good else 'FAIL'}  {name:<46} {detail}")
    # two independent errors in one panel: both localised, nobody else blamed
    panel = copy.deepcopy(TWO_ERRORS)
    summary = validate_results(panel)
    hb, nt = get(panel, "hemoglobin"), get(panel, "neutrophils_percent")
    others = [r["feature_id"] for r in panel if r["feature_id"] not in ("hemoglobin", "neutrophils_percent")
              and (r["requires_confirmation"] or r["confidence"] < 0.85)]
    good = (hb.get("suggested_value") == 13.5 and nt.get("suggested_value") == 60 and not others)
    ok_all &= good
    print(f"{'PASS' if good else 'FAIL'}  two simultaneous errors (Hb 135 + N% 80)        hb={hb.get('suggested_value')} n%={nt.get('suggested_value')} others={others}")
    # printed flag contradicts the value
    panel = copy.deepcopy(FLAG_CASE)
    summary = validate_results(panel)
    good = set(summary["flag_mismatches"]) == {"hemoglobin", "glucose"} and all(r["requires_confirmation"] for r in panel)
    ok_all &= good
    print(f"{'PASS' if good else 'FAIL'}  flag/value contradiction detected                 {summary['flag_mismatches']}")
    # unit conversion spot checks
    conv = [
        ("hemoglobin", 135, "g/L", 13.5), ("hematocrit", 0.405, "L/L", 40.5), ("glucose", 5.5, "mmol/L", 99.1),
        ("creatinine", 88.4, "umol/L", 1.0), ("total_cholesterol", 5.17, "mmol/L", 199.9),
        ("white_blood_cell_count", 7000, "/uL", 7.0), ("hemoglobin_a1c", 53, "mmol/mol", 7.0),
    ]
    for fid, v, u, exp in conv:
        got = canonical_value(fid, v, u)
        good = got is not None and abs(got - exp) <= 0.02 * exp
        ok_all &= good
        print(f"{'PASS' if good else 'FAIL'}  convert {fid} {v} {u} -> {got}")
    print("ALL PASS" if ok_all else "SOME FAILED")
    return ok_all


if __name__ == "__main__":
    sys.exit(0 if run() else 1)


def test_ocr_consistency_suite():
    assert run()
