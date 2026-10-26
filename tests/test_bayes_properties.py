"""Property tests for the Bayesian layer: order independence, monotonicity,
cluster-aware correlated-evidence handling, bounded output."""
from __future__ import annotations
import os, sys, math, random, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.disable(logging.CRITICAL)
import analyse_gidlines as ag  # noqa: E402

NET = ag.ClinicalBayesianNetwork()


def _post(node, keys, present=True, **extra):
    f = {k: {"present": present, "measured": True, **extra} for k in keys}
    return NET._mohasebe_posterior(node, f)


def test_order_independence_random():
    rng = random.Random(7)
    for did, node in list(NET.nodes.items())[:60]:
        keys = list(node.likelihood_ratios)
        if len(keys) < 2:
            continue
        sub = rng.sample(keys, min(len(keys), 4))
        f1 = {k: {"present": rng.random() < 0.6, "measured": True} for k in sub}
        items = list(f1.items()); rng.shuffle(items)
        f2 = dict(items)
        assert math.isclose(NET._mohasebe_posterior(node, f1), NET._mohasebe_posterior(node, f2), rel_tol=1e-12)


def test_adding_positive_finding_never_lowers_posterior():
    rng = random.Random(11)
    for did, node in NET.nodes.items():
        pos = [k for k, lr in node.likelihood_ratios.items() if lr > 1.0]
        if len(pos) < 2:
            continue
        for _ in range(5):
            base = rng.sample(pos, rng.randint(1, len(pos) - 1))
            extra = rng.choice([k for k in pos if k not in base])
            assert _post(node, base + [extra]) >= _post(node, base) - 1e-12, (did, base, extra)


def test_bounded_and_never_hard_zero_or_one():
    for did, node in NET.nodes.items():
        keys = list(node.likelihood_ratios)
        p_all = _post(node, keys)
        p_none = _post(node, keys, present=False)
        prior = NET._mohasebe_posterior(node, {})
        assert 0.0 < p_none <= prior < 1.0 and 0.0 < p_all < 1.0, did


def test_same_cluster_adds_less_than_independent_cluster():
    """Two graded cut-offs of one analyte must add far less than two
    physiologically independent findings of comparable LR."""
    node = NET.nodes["rhabdomyolysis"]
    base = _post(node, ["ck_high"])
    same = _post(node, ["ck_high", "ck_very_high"])           # same cluster
    indep = _post(node, ["ck_high", "potassium_high"])        # other cluster, LR 2.5
    # ck_very_high LR 40 would dominate if treated as independent
    naive = _post(node, ["ck_very_high"])
    assert same > base
    assert same < 0.5 * (naive + 1.0)  # not pushed to near-certainty by a correlated duplicate
    assert indep > base


def test_cluster_registry_covers_declared_keys():
    seen = set()
    for grp in ag.ClinicalBayesianNetwork.EVIDENCE_CLUSTERS:
        assert not (grp & seen), "a finding may belong to one cluster only"
        seen |= grp
    assert ag.ClinicalBayesianNetwork.cluster_of("lipase_high") == "lipase_high"
    assert ag.ClinicalBayesianNetwork.cluster_of("ck_high") == ag.ClinicalBayesianNetwork.cluster_of("ck_very_high")


def test_reliability_shrinks_update_toward_prior():
    node = NET.nodes["acute_pancreatitis"]
    prior = NET._mohasebe_posterior(node, {})
    full = _post(node, ["lipase_high"], reliability=1.0)
    half = _post(node, ["lipase_high"], reliability=0.5)
    assert prior < half < full


def test_dependency_boost_is_odds_coherent():
    r = ag.BayesianResult(disease_id="x", posterior_probability=0.9, evidence_count=1, measured_count=1,
                          contributing_factors=[], confidence=0.5, explanation="")
    dep = ag.BayesianResult(disease_id="dep", posterior_probability=0.95, evidence_count=1, measured_count=1,
                            contributing_factors=[], confidence=0.5, explanation="")
    net = ag.ClinicalBayesianNetwork()
    net.nodes["x"] = ag.BayesiNode(disease_id="x", dependencies=["dep"])
    out = {o.disease_id: o for o in net._emal_dependencies([r, dep])}
    assert 0.9 < out["x"].posterior_probability <= 0.99
