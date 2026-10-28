"""The verification ledger must reconcile with the frozen Notes (8, 15, 16) and never invent a verdict."""
import gzip, json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "eval", "verification_ledger")
L = json.load(gzip.open(os.path.join(D, "LEDGER.json.gz"), "rt", encoding="utf-8"))
C = json.load(open(os.path.join(D, "ledger_counts.json")))

def test_set_sizes_match_notes():
    s = lambda k: sum(r["sets"][k] for r in L)
    assert (s("curated_anchor"), s("curated_any"), s("active_core"), s("hot_core"), s("core_arm_15_1_0")) == (272, 285, 364, 174, 335)
    assert len(L) == len({r["rule_id"] for r in L}) == C["scope"]

def test_core_arm_is_not_the_active_core():
    assert C["core_arm_composition"] == {"curated_any": 284, "verified_quote_not_curated": 19, "convention_only": 32}
    assert C["active_core_in_core_arm"] == 94 and C["active_core_executable_15_2_0"] == 219

def test_quote_verified_rules_match_registry():
    vq = [r for r in L if r["registry_verified_quote"]]
    assert len(vq) == 37 and all(r["sets"]["active_core"] for r in vq)

def test_concordance_verdicts_are_copied_not_invented():
    n8 = collections.Counter(c["label"] for r in L for c in r["concordance"] if c["sample"].startswith("Note 8") and c["stratum"] == "A")
    assert n8 == {"UNRESOLVABLE": 92, "DISCORDANT": 7, "CONCORDANT": 1}
    n15 = collections.Counter(c["label"] for r in L for c in r["concordance"] if c["sample"].startswith("Note 15"))
    assert n15 == {"UNRESOLVABLE": 92, "CONCORDANT": 6, "DISCORDANT": 2}

def test_locator_classes_match_phase_a():
    assert C["active_core_locator_classes"] == {"generic_landing_page": 199, "landing_page": 69, "doi_resolved": 38, "unreachable": 44, "no_locator": 10, "other": 4}

def test_status_precedence_is_total():
    allowed = {"retired", "discordant_open", "discordant_corrected", "quote_verified", "flagged_open", "source_reachable_unverified", "unresolvable"}
    assert all(r["verification_status"] in allowed for r in L)
    for r in L:
        if r["verification_status"] == "quote_verified":
            assert r["registry_verified_quote"] or any(c["label"] == "CONCORDANT" and c.get("quote") for c in r["concordance"])
