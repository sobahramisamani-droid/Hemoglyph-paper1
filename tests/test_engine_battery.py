"""pytest wrapper: one test per synthetic textbook case (regression lock)."""
from __future__ import annotations
import os
import sys
import logging
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.disable(logging.CRITICAL)
import engine_battery as B  # noqa: E402


@pytest.fixture(scope="module")
def engines():
    import analyse_gidlines as ag
    import calcu
    return ag.ClinicalRuleEngine(), calcu.DerivedFeatureEngine(os.path.join(B.ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json"))


@pytest.mark.parametrize("case", B.CASES, ids=[c[0] for c in B.CASES])
def test_case(case, engines):
    E, D = engines
    name, obs, pt, exp, max_rank = case
    o = B.mk(obs)
    try:
        der = D.compute(o, pt).to_dict()["results"]
        derived = {k: {"value": v["value"], "unit": v["unit"]} for k, v in der.items()}
    except Exception:
        derived = {}
    diff = E.interpret(o, derived, pt).to_dict()["differential_diagnosis"]
    hits = [(x["rank"], x["disease_id"]) for x in diff if x["disease_id"] in exp]
    assert hits and hits[0][0] <= max_rank, f"{name}: top5={[(x['rank'], x['disease_id']) for x in diff[:5]]}"
