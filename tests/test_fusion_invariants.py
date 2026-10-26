"""Property / invariant tests for the decision-fusion layer (pytest).

These do not need patient data: they assert mathematical properties the
fusion must satisfy for *any* input - bounds, monotonicity, order
independence, belief <= plausibility, anchoring semantics, subsumption.
"""
from __future__ import annotations
import os
import sys
import random
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
logging.disable(logging.CRITICAL)

import pytest  # noqa: E402
import analyse_gidlines as ag  # noqa: E402

rng = random.Random(1234)


def _fuse(rule=None, bayes=None, fuzzy=None, graph=None, risk=None, anchored=()):
    d = "x"
    res = ag.tarkib_ensemble(
        rule_scores={d: rule} if rule is not None else {},
        bayesian_scores={d: bayes} if bayes is not None else {},
        fuzzy_scores={d: fuzzy} if fuzzy is not None else {},
        graph_boosts={d: graph} if graph is not None else {},
        risk_scores={d: risk} if risk is not None else {},
        guideline_anchored=anchored,
    )
    return res[0] if res else None


@pytest.mark.parametrize("seed", range(200))
def test_bounds_and_belief_plausibility(seed):
    r = random.Random(seed)
    votes = [r.random() if r.random() < 0.8 else None for _ in range(5)]
    out = _fuse(*votes)
    if out is None:
        return
    assert 0.0 <= out.final_score <= 1.0
    assert 0.0 <= out.confidence <= 1.0
    assert 0.0 <= out.belief <= out.plausibility <= 1.0 + 1e-9
    assert abs(out.belief + out.ignorance + (1 - out.plausibility) - 1.0) < 1e-6
    assert out.evidence_state in ("supported", "weak", "insufficient", "refuted", "conflicting")


@pytest.mark.parametrize("seed", range(100))
def test_rule_vote_monotone(seed):
    """Raising the rule vote with the other layers fixed never lowers the score."""
    r = random.Random(seed)
    bayes, fuzzy = r.random(), r.random()
    prev = None
    for rv in [0.1, 0.3, 0.5, 0.7, 0.9]:
        out = _fuse(rv, bayes, fuzzy)
        if prev is not None:
            assert out.final_score >= prev - 1e-9, (rv, bayes, fuzzy)
        prev = out.final_score


def test_corroboration_beats_single_source():
    one = _fuse(0.9)
    two = _fuse(0.9, 0.9)
    assert two.final_score > one.final_score
    assert two.belief > one.belief


def test_anchor_lifts_single_source_without_exceeding_full_corroboration():
    plain = _fuse(0.92)
    anchored = _fuse(0.92, anchored={"x"})
    full = _fuse(0.92, 0.92, 0.92, 0.92, 0.92)
    assert anchored.final_score > plain.final_score
    assert anchored.final_score <= full.final_score + 1e-9
    assert anchored.belief > plain.belief


def test_dissent_lowers_score_and_confidence():
    agree = _fuse(0.9, 0.9, 0.9)
    dissent = _fuse(0.9, 0.1, 0.9)
    assert dissent.final_score < agree.final_score
    assert dissent.confidence < agree.confidence
    assert dissent.conflict > agree.conflict


def test_layer_order_independence():
    """The DST combination must not depend on the order masses arrive in."""
    masses = [(0.5, 0.1, 0.4), (0.2, 0.3, 0.5), (0.6, 0.0, 0.4)]
    a = ag._yager_binary_combine(masses)
    for _ in range(5):
        rng.shuffle(masses)
        b = ag._yager_binary_combine(list(masses))
        assert all(abs(x - y) < 1e-9 for x, y in zip(a, b))


def test_abstention_is_not_refutation():
    """A vanishing rule vote is treated as silence, not as a vote against."""
    silent = _fuse(None, 0.8, 0.8)
    tiny = _fuse(0.01, 0.8, 0.8)
    assert abs(silent.final_score - tiny.final_score) < 1e-9


# ---------------------------------------------------------------- reasoner --
class _R:
    def __init__(self, did, score, votes=None, state="supported"):
        self.disease_id = did
        self.final_score = score
        self.votes = votes or {"rule_engine": score}
        self.evidence_state = state
        self.confidence = 0.8
        self.participating_models = list(self.votes)
        self.belief, self.plausibility, self.conflict = score * 0.8, 1.0, 0.0
        self.weight_profile = "default"
        self.calibrated_score = score
        self.ignorance = 0.2
        self.input_reliability = 1.0
        self.interpretation = ""


@pytest.fixture(scope="module")
def reasoner():
    eng = ag.ClinicalRuleEngine()
    return eng._reasoner


def test_subsumption_demotes_subset_entity(reasoner):
    reasoner._guideline_anchored = {"diabetic_ketoacidosis"}
    reasoner._disease_true_feats = {
        "diabetic_ketoacidosis": {"glucose", "bicarbonate", "beta_hydroxybutyrate"},
        "metabolic_acidosis": {"bicarbonate"},
        "hyperkalemia": {"potassium"},
    }
    ens = [_R("metabolic_acidosis", 0.9), _R("diabetic_ketoacidosis", 0.8), _R("hyperkalemia", 0.85)]
    out = reasoner.differential_diagnosis(ens, {}, ag.ClinicalContext.from_any({"age_years": 30, "sex_at_birth": "male"}))
    ranks = {d.disease_id: d.rank for d in out}
    by = {d.disease_id: d for d in out}
    assert ranks["diabetic_ketoacidosis"] < ranks["metabolic_acidosis"]
    assert by["metabolic_acidosis"].explained_by == "diabetic_ketoacidosis"
    # an entity with evidence of its own (potassium) is never subsumed
    assert by["hyperkalemia"].explained_by is None
    assert by["hyperkalemia"].probability == pytest.approx(0.85)


def test_subsumption_requires_strict_subset_between_anchors(reasoner):
    reasoner._guideline_anchored = {"a", "b"}
    reasoner._disease_true_feats = {"a": {"f1", "f2"}, "b": {"f1", "f2"}}
    out = reasoner.differential_diagnosis([_R("a", 0.8), _R("b", 0.9)], {},
                                          ag.ClinicalContext.from_any({"age_years": 30}))
    by = {d.disease_id: d for d in out}
    assert by["a"].explained_by is None and by["b"].explained_by is None
    assert by["b"].probability == pytest.approx(0.9)


def test_prior_only_umbrella_cannot_cap_rule_established_finding(reasoner):
    reasoner._guideline_anchored = set()
    reasoner._disease_true_feats = {"hypertriglyceridemia": {"triglycerides"}}
    umbrella = _R("hyperlipidemia", 0.6, votes={"bayesian": 0.9, "fuzzy": 0.8, "rule_engine": 0.0})
    finding = _R("hypertriglyceridemia", 0.7)
    out = reasoner.differential_diagnosis([umbrella, finding], {}, ag.ClinicalContext.from_any({"age_years": 30}))
    ranks = {d.disease_id: d.rank for d in out}
    assert ranks["hypertriglyceridemia"] < ranks["hyperlipidemia"]


@pytest.mark.parametrize("seed", range(60))
def test_score_is_lipschitz_continuous_in_votes(seed):
    """A 0.01 change in any single vote (above the rule-abstain threshold)
    moves the point score by less than 0.05 - no hidden cliffs in the fusion."""
    r = random.Random(seed)
    v = [r.uniform(0.1, 0.99), r.random(), r.random()]
    base = _fuse(*v).final_score
    for i in range(3):
        w = list(v)
        w[i] = min(1.0, w[i] + 0.01)
        assert abs(_fuse(*w).final_score - base) < 0.05, (i, v)
