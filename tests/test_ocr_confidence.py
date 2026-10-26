"""Evidence model for OCR row confidence: coherence, monotonicity, thresholds, fit."""
from __future__ import annotations
import os, sys, random, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ocr_confidence as oc  # noqa: E402
import pytest  # noqa: E402


def test_decision_thresholds_keep_their_meaning():
    assert oc.composite(1.0, 0.92, True, True, True) >= 0.98           # perfect row
    assert oc.composite(0.9, 0.85, True, True, True) >= 0.90           # good row
    assert oc.composite(0.7, 0.85, True, True, True) < 0.86            # weak name match alone -> review
    assert oc.composite(1.0, 0.92, False, True, True) < 0.86           # unit mismatch alone -> review
    assert oc.composite(1.0, 0.92, True, True, False) < 0.86           # ambiguous alias alone -> review
    assert oc.composite(1.0, 0.92, True, False, True) < 0.86           # no value -> review


@pytest.mark.parametrize("seed", range(40))
def test_monotone_in_every_term(seed):
    r = random.Random(seed)
    n, e = r.random(), r.uniform(0.05, 0.99)
    base = oc.composite(n, e, True, True, True)
    assert oc.composite(min(1.0, n + 0.05), e, True, True, True) >= base
    assert oc.composite(n, min(0.99, e + 0.05), True, True, True) >= base
    assert oc.composite(n, e, False, True, True) <= base
    assert oc.composite(n, e, True, False, True) <= base
    assert oc.composite(n, e, True, True, False) <= base


def test_evidence_is_order_independent_and_bounded():
    rec = {"confidence_evidence": oc.base_evidence(0.95, 0.9, True, True, True)}
    rec["confidence"] = oc.combine(rec["confidence_evidence"])
    a = dict(rec, confidence_evidence=list(rec["confidence_evidence"]))
    b = dict(rec, confidence_evidence=list(rec["confidence_evidence"]))
    oc.add_evidence(a, "identity_corroborated", note="x"); oc.add_evidence(a, "flag_mismatch")
    oc.add_evidence(b, "flag_mismatch"); oc.add_evidence(b, "identity_corroborated", note="x")
    assert a["confidence"] == b["confidence"]
    assert 0.0 < a["confidence"] < 1.0


def test_corroboration_is_capped():
    rec = {"confidence_evidence": oc.base_evidence(0.6, 0.6, True, True, True)}
    for i in range(6):
        oc.add_evidence(rec, "identity_corroborated", note=f"id{i}")
    total = sum(e["llr"] for e in rec["confidence_evidence"] if e["term"] == "identity_corroborated")
    assert total > oc.CORROBORATION_CAP
    capped = oc.combine(rec["confidence_evidence"])
    rec2 = {"confidence_evidence": oc.base_evidence(0.6, 0.6, True, True, True)}
    oc.add_evidence(rec2, "identity_corroborated", note="a"); oc.add_evidence(rec2, "identity_corroborated", note="b")
    assert math.isclose(capped, oc.combine(rec2["confidence_evidence"]), abs_tol=1e-9)


def test_culprit_is_strong_negative_evidence():
    rec = {"confidence_evidence": oc.base_evidence(1.0, 0.92, True, True, True)}
    oc.add_evidence(rec, "identity_culprit")
    assert rec["confidence"] < 0.5


def test_legacy_record_without_evidence_is_seeded():
    rec = {"confidence": 0.9}
    oc.add_evidence(rec, "flag_mismatch")
    assert rec["confidence"] < 0.9 and rec["confidence_evidence"][0]["term"] == "legacy_confidence"


def test_fit_recovers_planted_weights_direction():
    """Synthetic labels generated from a table where unit mismatch is MUCH
    worse than the prior says: the fit must move that weight down, and leave
    terms that never occur at their prior."""
    rng = random.Random(0)
    rows, labels = [], []
    planted = dict(oc.LLR); planted["unit_inconsistent"] = -6.0
    for _ in range(1500):
        n = rng.uniform(0.6, 1.0); e = rng.uniform(0.6, 0.99); unit_ok = rng.random() < 0.6
        ev = oc.base_evidence(n, e, unit_ok, True, True)
        z = oc._logit(oc.PRIOR) + sum(planted.get(x["term"], x["llr"]) if x["term"] in planted else x["llr"] for x in ev)
        labels.append(1 if rng.random() < oc._sigmoid(z) else 0)
        rows.append({"confidence_evidence": ev})
    table = oc.fit_llr_weights(rows, labels, iterations=400, lr=0.3)
    assert table["unit_inconsistent"] < oc.LLR["unit_inconsistent"] - 0.5
    assert math.isclose(table["vision_disagree"], oc.LLR["vision_disagree"], abs_tol=1e-6)
