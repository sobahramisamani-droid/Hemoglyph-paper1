"""Unit tests for the decision-fusion layer (pure maths, no registry needed).

Run:  python test_fusion_math.py
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analyse_gidlines as ag


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_pairwise_conflict_distinguishes_minority_from_split():
    w = {"a": .35, "b": .25, "c": .20, "d": .10, "e": .10}
    one_vs_four = {"a": .8, "b": .05, "c": .8, "d": .8, "e": .8}
    split = {"a": .9, "b": .1, "c": .1, "d": .9, "e": .9}
    k1 = ag._pairwise_conflict(one_vs_four, w)
    k2 = ag._pairwise_conflict(split, w)
    assert k1 < k2, (k1, k2)
    # the old std-based metric could not separate these two shapes well
    print(f"  conflict 1-vs-4 = {k1:.3f} | 50/50-ish split = {k2:.3f}")


def test_yager_has_no_zadeh_paradox():
    """Zadeh: two sources, each 0.99 on a different disease, 0.01 on a third.
    Dempster's normalised rule gives the third disease probability 1.0.
    On our binary frame per disease with Yager's rule the third disease
    must receive LOW belief and HIGH ignorance, never certainty."""
    # evidence for disease C from two layers, each believing C at 0.01
    masses = [(0.95 * 0.01, 0.95 * 0.99, 0.05),
              (0.95 * 0.01, 0.95 * 0.99, 0.05)]
    bel, pl, ign, k = ag._yager_binary_combine(masses)
    assert bel < 0.05, bel
    assert pl < 0.2, pl
    # and a flat contradiction (0.95 for vs 0.95 against) becomes ignorance
    bel2, pl2, ign2, k2 = ag._yager_binary_combine(
        [(0.95, 0.0, 0.05), (0.0, 0.95, 0.05)])
    assert ign2 > 0.85, ign2
    assert 0.0 <= bel2 <= 0.1 and 0.9 <= pl2 <= 1.0
    print(f"  Zadeh case: Bel={bel:.3f} Pl={pl:.3f} | contradiction -> ignorance={ign2:.3f}")


def test_ensemble_conflict_state_and_floor():
    # Fuzzy enthusiastic, Bayes sceptical, rules silent: must not average
    res = ag.tarkib_ensemble(
        rule_scores={}, bayesian_scores={"x": 0.02},
        fuzzy_scores={"x": 0.70}, graph_boosts={}, risk_scores={})
    r = res[0]
    assert r.final_score < 0.35, r.final_score
    assert r.evidence_state in ("conflicting", "insufficient", "weak"), r.evidence_state
    print(f"  fuzzy .70 vs bayes .02 -> score={r.final_score:.2f} "
          f"Bel={r.belief:.2f} Pl={r.plausibility:.2f} K={r.conflict:.2f} state={r.evidence_state}")

    # Explicit guideline criterion met (rule .9) but rare disease (bayes .03):
    # the red-flag floor must keep it visible.
    res = ag.tarkib_ensemble(
        rule_scores={"y": 0.90}, bayesian_scores={"y": 0.03},
        fuzzy_scores={}, graph_boosts={}, risk_scores={})
    r = res[0]
    assert r.final_score >= ag.RED_FLAG_FLOOR_FRACTION * 0.90 - 1e-9, r.final_score
    assert r.evidence_state == "conflicting"
    print(f"  rule .90 vs bayes .03 -> score={r.final_score:.2f} (floor) state={r.evidence_state}")


def test_single_weak_layer_is_mostly_ignorance():
    res = ag.tarkib_ensemble(
        rule_scores={}, bayesian_scores={},
        fuzzy_scores={"z": 0.60}, graph_boosts={}, risk_scores={})
    r = res[0]
    assert r.plausibility - r.belief >= 0.35, (r.belief, r.plausibility)
    assert r.evidence_state in ("insufficient", "weak")
    print(f"  single fuzzy .60 -> Bel={r.belief:.2f} Pl={r.plausibility:.2f} state={r.evidence_state}")


def test_input_reliability_lowers_confidence_not_direction():
    hi = ag.tarkib_ensemble({"q": .8}, {"q": .7}, {"q": .75}, {}, {},
                            input_reliability={"q": 1.0})[0]
    lo = ag.tarkib_ensemble({"q": .8}, {"q": .7}, {"q": .75}, {}, {},
                            input_reliability={"q": 0.4})[0]
    assert lo.confidence < hi.confidence
    # Shafer discounting before an n-ary Yager combination lowers the
    # committed belief; it also softens inter-layer conflict, so the
    # ignorance mass is not required to grow - the direction must not flip.
    assert lo.belief < hi.belief
    assert lo.final_score <= hi.final_score + 1e-9
    assert lo.evidence_state == hi.evidence_state
    print(f"  reliability 1.0 -> conf={hi.confidence:.2f} Bel={hi.belief:.2f}; "
          f"0.4 -> conf={lo.confidence:.2f} Bel={lo.belief:.2f}")


def test_domain_profiles():
    assert ag._profile_for_domains(["toxicology"]) == "toxicology"
    assert ag._profile_for_domains(["rheumatology"]) == "autoimmune"
    assert ag._profile_for_domains(["hematology"]) == "default"
    for name, prof in ag.WEIGHT_PROFILES.items():
        assert approx(sum(prof.values()), 1.0, 1e-9), name
    print("  all weight profiles sum to 1.0")


def test_reference_policy():
    assert ag.reference_policy("fasting_plasma_glucose") == "cdl_locked"
    assert ag.reference_policy("alanine_aminotransferase") == "method_dependent"
    rec = ag.ObservationRecord("alanine_aminotransferase", 48, "U/L",
                               reference_low=7, reference_high=70)
    ref, src, note = ag.apply_local_reference(
        "alanine_aminotransferase", dict(ag.REFERENCE_RANGES["alanine_aminotransferase"]), rec)
    assert src == "laboratory_reported" and ref["high"] == 70
    rec2 = ag.ObservationRecord("fasting_plasma_glucose", 128, "mg/dL",
                                reference_low=70, reference_high=135)
    ref2, src2, note2 = ag.apply_local_reference(
        "fasting_plasma_glucose", {"low": 70, "high": 99}, rec2)
    assert src2 == "registry_locked" and ref2["high"] == 99 and note2
    # implausible printed interval (OCR column error) is ignored
    rec3 = ag.ObservationRecord("alanine_aminotransferase", 48, "U/L",
                                reference_low=0, reference_high=550)
    _, src3, _ = ag.apply_local_reference(
        "alanine_aminotransferase", dict(ag.REFERENCE_RANGES["alanine_aminotransferase"]), rec3)
    assert src3 == "registry"
    print("  CDL lock / method-dependent / implausible-interval paths OK")


def test_reliability_is_continuous():
    def rel(conf):
        return ag._arzyabi_reliability(
            ag.ObservationRecord("x", 1, metadata={"ocr_confidence": conf}))
    assert rel(0.99) == 1.0
    assert rel(0.90) > rel(0.85) > rel(0.70) > rel(0.50)
    print(f"  reliability(0.95)={rel(.95):.2f} (0.85)={rel(.85):.2f} (0.70)={rel(.70):.2f} (0.50)={rel(.50):.2f}")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            print(f"[ {t.__name__} ]")
            t()
        except AssertionError as exc:
            failed += 1
            print(f"  FAILED: {exc!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
