"""Joint minimal-edit repair + randomized no-false-repair / recovery tests
for the OCR consistency solver."""
from __future__ import annotations
import os, sys, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ocr_consistency import validate_results  # noqa: E402


def rec(fid, value, unit):
    return {"feature_id": fid, "value": value, "unit": unit, "flag": None, "report_range_low": None,
            "report_range_high": None, "confidence": 0.9, "requires_confirmation": False,
            "suggested_action": "accept", "warnings": [], "original_value": value}


def cbc(hb, hct, rbc):
    return [rec("hemoglobin", round(hb, 1), "g/dL"), rec("hematocrit", round(hct, 1), "%"),
            rec("red_blood_cell_count", round(rbc, 2), "10^6/uL"),
            rec("mean_corpuscular_volume", round(hct / rbc * 10, 1), "fL"),
            rec("mean_corpuscular_hemoglobin", round(hb / rbc * 10, 1), "pg"),
            rec("mean_corpuscular_hemoglobin_concentration", round(hb / hct * 100, 1), "g/dL")]


def test_two_glyph_misreads_repaired_jointly():
    panel = cbc(13.5, 40.5, 4.5)
    panel[0]["value"] = panel[0]["original_value"] = 18.5   # 3 -> 8
    panel[1]["value"] = panel[1]["original_value"] = 48.5   # 0 -> 8
    s = validate_results(panel)
    assert sorted(s["joint_repairs"]) == ["hematocrit", "hemoglobin"]
    assert panel[0]["suggested_value"] == 13.5 and panel[1]["suggested_value"] == 40.5
    assert all(r["suggested_value"] is None for r in panel[2:])
    assert set(s["exonerated"]) >= {"mean_corpuscular_volume", "mean_corpuscular_hemoglobin"}


def test_single_misread_still_single_culprit():
    panel = cbc(13.5, 40.5, 4.5)
    panel[1]["value"] = panel[1]["original_value"] = 48.5
    s = validate_results(panel)
    assert s["suspects"] == ["hematocrit"] and s["joint_repairs"] == []
    assert panel[1]["suggested_value"] == 40.5


def test_random_consistent_panels_never_repaired():
    rng = random.Random(3)
    for _ in range(300):
        hb = rng.uniform(6.0, 18.5); mchc = rng.uniform(31.0, 36.0); mcv = rng.uniform(60.0, 110.0)
        hct = hb / mchc * 100.0; rbc = hct / mcv * 10.0
        panel = cbc(hb, hct, rbc)
        s = validate_results(panel)
        assert s["suspects"] == [] and s["repairs_suggested"] == 0, (hb, hct, rbc, s["failed"])


def test_random_single_decimal_shift_recovered():
    rng = random.Random(5)
    hits = total = 0
    for _ in range(200):
        hb = rng.uniform(7.0, 17.0); mchc = rng.uniform(31.5, 35.5); mcv = rng.uniform(65.0, 105.0)
        hct = hb / mchc * 100.0; rbc = hct / mcv * 10.0
        panel = cbc(hb, hct, rbc)
        i = rng.randrange(len(panel))
        truth = panel[i]["value"]
        bad = round(truth * rng.choice([10.0, 0.1]), 3)
        panel[i]["value"] = panel[i]["original_value"] = bad
        validate_results(panel)
        total += 1
        sv = panel[i].get("suggested_value")
        if sv is not None and abs(sv - truth) <= 0.02 * truth + 0.05:
            hits += 1
        # no innocent field may receive a repair
        assert all(panel[j].get("suggested_value") is None for j in range(len(panel)) if j != i)
    assert hits / total >= 0.97, hits / total


def test_idempotent_on_repaired_output():
    panel = cbc(13.5, 40.5, 4.5)
    panel[1]["value"] = panel[1]["original_value"] = 48.5
    validate_results(panel)
    snap = copy.deepcopy(panel)
    validate_results(panel)
    for a, b in zip(snap, panel):
        assert a["suggested_value"] == b["suggested_value"] and a["warnings"] == b["warnings"]


def test_new_identities_fire_and_repair():
    panel = [rec("hemoglobin_a1c", 6.5, "%"), rec("estimated_average_glucose", 14.0, "mg/dL"),
             rec("triglycerides", 150, "mg/dL"), rec("vldl_cholesterol", 30, "mg/dL"),
             rec("albumin", 4.0, "g/dL"), rec("globulin", 2.5, "g/dL"), rec("albumin_to_globulin_ratio", 1.6, "ratio"),
             rec("calcium_total", 8.0, "mg/dL"), rec("corrected_calcium_for_serum_albumin", 8.0, "mg/dL"),
             rec("white_blood_cell_count", 7.0, "10^3/uL"), rec("monocytes_percent", 6, "%"),
             rec("monocyte_count_absolute", 0.42, "10^3/uL"), rec("transferrin", 250, "mg/dL"),
             rec("total_iron_binding_capacity", 347, "ug/dL")]
    s = validate_results(panel)
    assert s["checks_run"] >= 6
    assert [f["check"] for f in s["failed"]] == ["eag_identity"]
    assert panel[1]["suggested_value"] == 140.0
    assert s["suspects"] == ["estimated_average_glucose"]


def test_three_misreads_in_small_panel():
    # Hb, Hct and RBC all shifted by a decimal while the indices are right:
    # the indices are the majority story, so the three counts are the culprits.
    panel = cbc(13.5, 40.5, 4.5)
    for i in range(3):
        panel[i]["value"] = panel[i]["original_value"] = round(panel[i]["value"] * 10, 2)
    s = validate_results(panel)
    repaired = {r["feature_id"]: r.get("suggested_value") for r in panel if r.get("suggested_value") is not None}
    assert set(repaired) == {"hemoglobin", "hematocrit", "red_blood_cell_count"}, (repaired, s["failed"], s["plausibility_violations"])
