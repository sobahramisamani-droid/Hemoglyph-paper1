"""OCR-side specimen provenance (HIL flags, specimen type, collection time, morphology comments)
and its hand-off to the engine's preanalytical gate (2026-10-23)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from ocr import detect_preanalytical


def test_hemolysis_english_flag_detected():
    r = detect_preanalytical("Potassium 6.1 mmol/L H (3.5-5.1)\nComment: sample hemolyzed, recollect advised")
    assert r["flags"].get("hemolysis") is True and r["flags"].get("recollect") is True
    assert "hemoly" in r["evidence"]["hemolysis"].lower()


def test_hemolysis_persian_flag_detected():
    r = detect_preanalytical("پتاسیم 6.2\nتوضیحات: نمونه همولیز می‌باشد")
    assert r["flags"].get("hemolysis") is True


def test_negated_mention_does_not_flag():
    r = detect_preanalytical("Serum indices: non-hemolyzed, no lipemia, not icteric. K 4.1")
    assert not r["flags"]


def test_hil_index_grades():
    assert detect_preanalytical("HIL: H=3 L=0 I=0")["flags"].get("hemolysis") is True
    assert detect_preanalytical("H-index: 0  L-index: 0")["flags"] == {}
    assert detect_preanalytical("Lipemic index ++ (turbid serum)")["flags"].get("lipemia") is True


def test_specimen_and_collection_time():
    r = detect_preanalytical("Arterial blood gas\nCollected: 2026-03-14 08:15\npH 7.21")
    assert r["specimen"] == "arterial_blood" and r["collected_at"].startswith("2026-03-14")


def test_morphology_terms_collected():
    r = detect_preanalytical("Smear: toxic granulation, left shift, blasts seen 4%")
    assert "toxic granulation" in r["morphology"] and any(m.startswith("blasts") for m in r["morphology"])


def test_empty_text_safe():
    assert detect_preanalytical("")["flags"] == {}


def test_engine_downweights_potassium_when_flag_passed():
    import logging; logging.disable(logging.CRITICAL)
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine()
    obs = {"potassium": {"value": 6.3, "unit": "mmol/L"}, "sodium": {"value": 139, "unit": "mmol/L"},
           "creatinine": {"value": 0.9, "unit": "mg/dL"}, "lactate_dehydrogenase": {"value": 420, "unit": "U/L"}}
    plain = E.interpret(obs, None, {"age_years": 50, "sex_at_birth": "male"}).to_dict()
    flagged = E.interpret(obs, None, {"age_years": 50, "sex_at_birth": "male", "hemolysis": True}).to_dict()
    w = " ".join(flagged.get("input_warnings", []) + flagged.get("warnings", [])).lower()
    assert "haemolys" in w or "hemolys" in w, "engine must surface the pseudohyperkalaemia caution"
    def p(rep, key="hyperkalemia"):
        for d in rep.get("differential_diagnosis", []):
            if d["disease_id"] == key:
                return float(d["probability"])
        return 0.0
    assert p(flagged) <= p(plain), "flagged sample must never raise hyperkalaemia confidence"


def test_service_merges_ocr_flags_into_context():
    from sarvis_tahlil import AnalysisService as LabAnalysisService  # noqa
    svc = LabAnalysisService.__new__(LabAnalysisService)
    svc._last_preanalytical = {"flags": {"hemolysis": True, "clotted": True}, "specimen": "serum", "collected_at": "2026-01-01 07:00"}
    ctx = svc._merge_preanalytical({"age_years": 40})
    assert ctx["hemolysis"] is True and "clotted" not in ctx and ctx["specimen_type"] == "serum"
    assert svc._merge_preanalytical({"age_years": 40, "hemolysis": False})["hemolysis"] is False, "clinician override wins"
