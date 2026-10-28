#!/usr/bin/env python3
"""Verification Ledger — one record per rule stating what each of the paper's verification methods established about it.

Scope (union, de-duplicated): the 285 curated rules of registry 14.1.0 (272 anchors + 13 demoted anchors), the 364 rules of
the activity-defined ACTIVE CORE (Supplementary Note 15), and the 335 rules of the CORE arm of the sufficiency study
(Supplementary Note 16; 15.1.0 ids). Every column is read from an existing, frozen artefact; nothing is re-measured and no
registry field is modified.

Columns (per rule)
  identity        rule_id, disease_id, rule_type, expression (feature, operator, value, unit), first source id
  status          status in 14.1.0 and in 15.2.0 (+ retirement reason if retired), executable in 15.2.0
  sets            curated_anchor (14.1.0 status == curated_guideline_anchored), curated_any (status startswith curated),
                  active_core / hot_core (fired, contrib10, contrib5 pooled over 3,814 panels), core_arm_15_1_0,
                  reference_interval_convention
  provenance      locator_class (same classes as Fig. S1, from the rule's first source; for active-core rules taken from
                  core_rules.json.gz), the automated threshold search result of Note 15 (active core only), registry
                  verified_quote (15.0.0 R3)
  concordance     verdicts from the frozen 200-rule sample (Note 8) and the 100-rule active-core sample (Note 15),
                  with the verbatim quote when one was recorded
  detectors       static-detector flags on 14.1.0 and on 15.2.0 (eval/audit/audit.py, frozen)
  invariants      which executable property tests exercise this rule's analyte: monotonicity (tests/test_properties.py MONO),
                  unit invariance (LabPanel-Check P2 analytes), absent-analyte (P5 removed analytes), creatinine ladder (P4)
  releases        patch classes that touched the rule in 15.0.0 / 15.1.0 / 15.2.0
  verification_status  one label per rule, decided by the fixed precedence documented in LEDGER_SUMMARY.md

Outputs: LEDGER.json.gz (records), LEDGER_SUMMARY.md (counts by set and status), ledger_counts.json (for the test).
"""
from __future__ import annotations
import os, sys, json, gzip, csv, collections, hashlib, re
import brotli

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
J = lambda *p: os.path.join(ROOT, *p)
rd_br = lambda p: json.loads(brotli.decompress(open(p, "rb").read()))
rd_gz = lambda p: json.load(gzip.open(p, "rt", encoding="utf-8"))

# ---- registries ------------------------------------------------------------------------------------------------------
R14 = rd_br(J("release/registry_14.1.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"))
R15 = rd_br(J("release/registry_15.2.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"))  # the ledger is a 15.2.0 snapshot
assert R15["registry_metadata"]["version"].startswith("15.2.0"), R15["registry_metadata"]["version"]
R151 = rd_br(J("release/registry_15.1.0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"))
rules14, rules15, rules151 = R14["rules"], R15["rules"], R151["rules"]
ex14 = {k for k, r in rules14.items() if r.get("executable")}
ex151 = {k for k, r in rules151.items() if r.get("executable")}
ex15 = {k for k, r in rules15.items() if r.get("executable")}
srcmeta = R15["guideline_sources"]
srcmeta = {s.get("source_id", i): s for i, s in (srcmeta.items() if isinstance(srcmeta, dict) else enumerate(srcmeta))}

# ---- sets --------------------------------------------------------------------------------------------------------------
anchors = {k for k in ex14 if rules14[k].get("status") == "curated_guideline_anchored"}                    # 272
curated_any = {k for k in ex14 if str(rules14[k].get("status", "")).startswith("curated")}                 # 285
core = rd_gz(J("eval/provenance/core_rules.json.gz"))                                                     # 364 (14.2.0 ids)
hot = {k for k, v in core.items() if v["contrib10"] >= 10}                                                 # 174
core_arm = {k for k in ex151 if str(rules151[k].get("status", "")).startswith("curated")
            or (rules151[k].get("provenance") or {}).get("verified_quote")
            or (rules151[k].get("source_ids") or [""])[0] == "reference_interval_convention"}              # 335
convention = {k for k in ex15 if (rules15[k].get("source_ids") or [""])[0] == "reference_interval_convention"}
assert len(anchors) == 272 and len(curated_any) == 285 and len(core) == 364 and len(hot) == 174 and len(core_arm) == 335, \
    (len(anchors), len(curated_any), len(core), len(hot), len(core_arm))
scope = sorted(curated_any | set(core) | core_arm)

# ---- activity (pooled over eICU + NHANES I + NHANES J, as in core_analysis.py) --------------------------------------------
pooled = collections.defaultdict(lambda: [0, 0, 0])
for p in ("activity_eicu.json.gz", "activity_nhanes_I.json.gz", "activity_nhanes_J.json.gz"):
    a = rd_gz(J("eval/provenance", p))
    for rid, (f, c10, c5) in a["counts"].items():
        q = pooled[rid]; q[0] += f; q[1] += c10; q[2] += c5
for rid, v in core.items():
    assert pooled[rid][0] == v["fired"] and pooled[rid][1] == v["contrib10"], rid

# ---- locator class (Fig. S1 classes; identical logic to eval/provenance/core_analysis.py) ---------------------------------
srcver = {s["source_id"]: s for s in rd_gz(J("eval/results/source_verification_13.4.1.json.gz"))["sources"]}
def loc_class(rule):
    sid = (rule.get("source_ids") or [None])[0]
    if sid is None: return "no_locator"
    v = srcver.get(sid, {}).get("verification_status", "")
    m = srcmeta.get(sid, {}); url = (m.get("url") or "")
    if v in ("verified", "doi_verified"): return "doi_resolved"
    if v == "generic_landing_page": return "generic_landing_page"
    if v in ("title_mismatch", "unresolved"): return "doi_unresolved_or_mismatch"
    if v in ("url_only", "landing_page_reached", "reachable"): return "landing_page"
    if v == "url_unreachable": return "unreachable"
    if v == "no_locator" or not url: return "no_locator"
    return v or "other"
core_loc = json.load(open(J("eval/provenance/core_locators.json")))

# ---- concordance verdicts -------------------------------------------------------------------------------------------------
n8 = {r["rule_id"]: r for r in csv.DictReader(open(J("eval/source_audit/sample_200.csv"), encoding="utf-8"))}
n15 = {r["rule_id"]: r for r in csv.DictReader(open(J("eval/provenance/phase_c_sample_100.csv"), encoding="utf-8"))}
assert len(n8) == 200 and len(n15) == 100

# ---- static detectors -----------------------------------------------------------------------------------------------------
sys.path.insert(0, J("eval/audit"))
import audit as AUD  # noqa: E402
feats = rd_br(J("HEMOGLYPH_FEATURE_REGISTRY.json.br"))["features"]
flags14 = AUD.Audit(R14, feats).run(only=set(scope))
flags15 = AUD.Audit(R15, feats).run(only=set(scope))

# ---- invariant coverage -------------------------------------------------------------------------------------------------
sys.path.insert(0, J("tests"))
_tp = open(J("tests/test_properties.py"), encoding="utf-8").read()
MONO = {}
for m in re.finditer(r'\(\s*"([a-z_]+)",\s*"[^"]*",\s*\[([^\]]*)\],\s*\(([^)]*)\)', _tp):
    feat, steps, ids = m.group(1), [float(x) for x in m.group(2).split(",")], [s.strip().strip('"') for s in m.group(3).split(",") if s.strip()]
    MONO.setdefault(feat, []).append({"direction": "up" if steps[-1] > steps[0] else "down", "entities": ids})
assert len(MONO) >= 8, MONO.keys()
lpc_panels = rd_gz(J("eval/labpanel_check/panels.json.gz"))
_bb = open(J("eval/blackbox/make_property_panels.py"), encoding="utf-8").read()
UNITS = set(re.findall(r'"([a-z_]+)":\s*\("[^"]*",\s*"[^"]*",\s*[\d.]+\)', _bb))
P5_REMOVED = {rec["removed_analyte"] for rec in lpc_panels.values() if rec["property"] == "P5"}

def expr_leaves(e):
    """flatten a rule expression to (feature, operator, value, unit) leaves"""
    out = []
    if isinstance(e, dict):
        if "feature_id" in e: out.append((e.get("feature_id"), e.get("operator"), e.get("value"), e.get("unit")))
        for v in e.values():
            if isinstance(v, (dict, list)): out += expr_leaves(v)
    elif isinstance(e, list):
        for v in e: out += expr_leaves(v)
    return out

def invariant_coverage(rule):
    cov = set()
    for feat, op, val, unit in expr_leaves(rule.get("expression")):
        if feat in MONO:
            for m in MONO[feat]:
                if (m["direction"] == "up" and op in (">", ">=")) or (m["direction"] == "down" and op in ("<", "<=")):
                    cov.add(f"monotonicity:{feat}:{m['direction']}")
        if feat in UNITS: cov.add(f"unit_invariance:{feat}")
        if feat in P5_REMOVED: cov.add(f"absent_analyte:{feat}")
        if feat == "creatinine": cov.add("creatinine_ladder")
    return sorted(cov)

# ---- release patches ------------------------------------------------------------------------------------------------------
touched = collections.defaultdict(list)
for ver in ("15_0_0", "15_1_0", "15_2_0"):
    rv = json.load(open(J(f"eval/registry_patches/review_{ver}.json")))
    for cls, ids in (rv.get("rule_ids") or {}).items():
        if isinstance(ids, list):
            for rid in ids:
                if isinstance(rid, str): touched[rid].append(f"{ver.replace('_', '.')}:{cls}")
    for rid, why in (rv.get("retired_reason") or {}).items():
        touched[rid].append(f"{ver.replace('_', '.')}:retired")

# ---- status precedence ----------------------------------------------------------------------------------------------------
# verified by reading the 15.2.0 text against the recorded finding: the prediabetes rule got '>=' but never the 6.4 % upper bound
STILL_OPEN_AFTER_PATCH = {"prediabetes_hba1c_pattern_screening_1_v1"}
PRECEDENCE = ["retired", "discordant_open", "discordant_corrected", "quote_verified", "flagged_open", "source_reachable_unverified", "unresolvable"]
def decide(rec):
    if not rec["executable_15_2_0"] and str(rec["status_15_2_0"]).startswith("retired"): return "retired"
    verdicts = [v["label"] for v in rec["concordance"]]
    disc = [v for v in rec["concordance"] if v["label"] == "DISCORDANT"]
    if disc:
        # both frozen samples were rated against the pre-15.0.0 rule text (Note 8 on 14.1.0, Note 15 on 14.2.0), so a
        # 15.x patch that touched the rule counts as a correction only if the rule text or source actually changed AND
        # the specific finding is no longer present (checked by hand for the 15.2.0 ledger: see PROTOCOL_15_3_0 D2)
        changed = rec["status_15_2_0"] != rec["status_14_1_0"] or rec["leaves"] != rec["leaves_14_1_0"] or rec["first_source_id"] != rec["first_source_id_14_1_0"]
        still_open = rec["rule_id"] in STILL_OPEN_AFTER_PATCH
        return "discordant_corrected" if (changed and not still_open) else "discordant_open"
    if rec["registry_verified_quote"] or "CONCORDANT" in verdicts: return "quote_verified"
    if rec["detector_flags_15_2_0"]: return "flagged_open"
    if "UNRESOLVABLE" in verdicts: return "unresolvable"
    if rec["locator_class"] in ("doi_resolved", "landing_page"): return "source_reachable_unverified"
    return "unresolvable"

# ---- build ---------------------------------------------------------------------------------------------------------------
ledger = []
for rid in scope:
    r14 = rules14.get(rid) or {}; r15 = rules15.get(rid) or rules151.get(rid) or r14
    r_any = r15 or r14
    leaves = expr_leaves(r_any.get("expression"))
    conc = []
    if rid in n8:
        x = n8[rid]; conc.append({"sample": "Note 8 (200, seed 20261026)", "stratum": x["stratum"], "label": x["rater1_label"], "note": x["rater1_note"], "quote": ""})
    if rid in n15:
        x = n15[rid]; conc.append({"sample": "Note 15 (100 active-core, seed 20261028)", "label": x["label"], "quote": x["quote"], "locator": x["locator"], "note": x["note"]})
    rec = {
        "rule_id": rid, "disease_id": r_any.get("disease_id"), "rule_type": r_any.get("rule_type"),
        "leaves": [{"feature": f, "operator": o, "value": v, "unit": u} for f, o, v, u in leaves],
        "first_source_id": (r_any.get("source_ids") or [None])[0],
        "leaves_14_1_0": [{"feature": f, "operator": o, "value": v, "unit": u} for f, o, v, u in expr_leaves(r14.get("expression"))],
        "first_source_id_14_1_0": (r14.get("source_ids") or [None])[0],
        "status_14_1_0": r14.get("status") if r14 else None, "executable_14_1_0": rid in ex14,
        "status_15_2_0": (rules15.get(rid) or {}).get("status"), "executable_15_2_0": rid in ex15,
        "sets": {"curated_anchor": rid in anchors, "curated_any": rid in curated_any, "active_core": rid in core, "hot_core": rid in hot,
                 "core_arm_15_1_0": rid in core_arm, "reference_interval_convention": rid in convention},
        "activity": {"fired": pooled[rid][0], "contrib10": pooled[rid][1], "contrib5": pooled[rid][2]} if rid in pooled else {"fired": 0, "contrib10": 0, "contrib5": 0},
        "locator_class": core[rid]["loc_class"] if rid in core else loc_class(r_any),
        "auto_locator_match_note15": core_loc[rid]["match"] if rid in core_loc else None,
        "registry_verified_quote": ((rules15.get(rid) or {}).get("provenance") or {}).get("verified_quote") or None,
        "concordance": conc,
        "detector_flags_14_1_0": flags14.get(rid, {}), "detector_flags_15_2_0": flags15.get(rid, {}),
        "invariant_coverage": invariant_coverage(r_any),
        "releases_touched": sorted(set(touched.get(rid, []))),
    }
    rec["verification_status"] = decide(rec)
    ledger.append(rec)

# ---- summary ---------------------------------------------------------------------------------------------------------------
def count(pred):
    return collections.Counter(r["verification_status"] for r in ledger if pred(r))
SETS = [("curated anchors (272, 14.1.0)", lambda r: r["sets"]["curated_anchor"]),
        ("active core (364)", lambda r: r["sets"]["active_core"]),
        ("hot core (174)", lambda r: r["sets"]["hot_core"]),
        ("CORE arm of the sufficiency study (335, 15.1.0)", lambda r: r["sets"]["core_arm_15_1_0"]),
        ("union (all ledger rows)", lambda r: True)]
rows = []
for name, pred in SETS:
    c = count(pred); n = sum(c.values())
    rows.append(f"| {name} | {n} | " + " | ".join(f"{c.get(s, 0)} ({100*c.get(s,0)/n:.0f}%)" for s in PRECEDENCE) + " |")
inv_cov = collections.Counter()
for r in ledger:
    if r["sets"]["active_core"] and r["executable_15_2_0"]:
        inv_cov["covered" if r["invariant_coverage"] else "not_covered"] += 1
loc = collections.Counter(r["locator_class"] for r in ledger if r["sets"]["active_core"])
counts = {"scope": len(ledger), "anchors": len(anchors), "curated_any": len(curated_any), "active_core": len(core), "hot_core": len(hot), "core_arm": len(core_arm),
          "by_set": {name: dict(count(pred)) for name, pred in SETS}, "active_core_executable_15_2_0": sum(r["sets"]["active_core"] and r["executable_15_2_0"] for r in ledger),
          "active_core_in_core_arm": sum(r["sets"]["active_core"] and r["sets"]["core_arm_15_1_0"] for r in ledger),
          "core_arm_composition": {"curated_any": sum(r["sets"]["core_arm_15_1_0"] and r["sets"]["curated_any"] for r in ledger),
                                   "verified_quote_not_curated": sum(r["sets"]["core_arm_15_1_0"] and not r["sets"]["curated_any"] and bool(r["registry_verified_quote"]) for r in ledger),
                                   "convention_only": sum(r["sets"]["core_arm_15_1_0"] and not r["sets"]["curated_any"] and not r["registry_verified_quote"] for r in ledger)},
          "invariant_coverage_active_core_executable": dict(inv_cov), "active_core_locator_classes": dict(loc),
          "concordance_rows": {"note8": sum(any(c["sample"].startswith("Note 8") for c in r["concordance"]) for r in ledger),
                               "note15": sum(any(c["sample"].startswith("Note 15") for c in r["concordance"]) for r in ledger)},
          "detector_flags_15_2_0_rows": sum(bool(r["detector_flags_15_2_0"]) for r in ledger),
          "detector_flags_14_1_0_rows": sum(bool(r["detector_flags_14_1_0"]) for r in ledger)}

md = ["# Verification Ledger — summary (registry 15.2.0; built from frozen artefacts, nothing re-measured)", "",
      f"Rows: {len(ledger)} rules = union of the 285 curated rules of 14.1.0 (272 anchors + 13 demoted), the 364-rule active core and the 335-rule CORE arm.", "",
      "## Status precedence (first matching label wins)", "",
      "1. `retired` — non-executable in 15.2.0 with a `retired_*` status (15.0.0/15.1.0 patches under written protocol).",
      "2. `discordant_open` — a frozen-sample verdict of DISCORDANT and no change to the rule since (status unchanged, no patch touched it).",
      "3. `discordant_corrected` — DISCORDANT verdict (both samples were rated on the pre-15.0.0 rule text), and the rule's text or source changed in 15.x so that the recorded finding no longer holds.",
      "4. `quote_verified` — the registry carries a verbatim source quote for the rule (15.0.0 R3) or a frozen-sample verdict of CONCORDANT with quote.",
      "5. `flagged_open` — at least one static-detector flag on 15.2.0 (calibrated detectors; a flag is a candidate defect, not a verdict).",
      "6. `source_reachable_unverified` — first source resolves to a DOI or a specific document page, but no one has checked the rule against it.",
      "7. `unresolvable` — first source is a generic standards page, an organisation landing page, unreachable, or absent; or the sampled verdict was UNRESOLVABLE.",
      "", "`quote_verified` means transcription concordance by a single declared AI rater; it is not clinical validation.", "",
      "## Counts", "", "| set | n | " + " | ".join(PRECEDENCE) + " |", "|---|---|" + "---|" * len(PRECEDENCE)] + rows + [
      "", "## Facts the ledger makes explicit", "",
      f"- The CORE arm (335) is **not** the active core: it is {counts['core_arm_composition']['curated_any']} curated rules + {counts['core_arm_composition']['verified_quote_not_curated']} quote-verified non-curated rules + {counts['core_arm_composition']['convention_only']} reference-interval conventions; only {counts['active_core_in_core_arm']} of the 364 active-core rules are in it.",
      f"- Of the 364 active-core rules, {counts['active_core_executable_15_2_0']} are still executable in 15.2.0 ({364 - counts['active_core_executable_15_2_0']} retired under the 15.0.0 protocol).",
      f"- Invariant tests reach the analyte of {inv_cov['covered']} of the {sum(inv_cov.values())} executable active-core rules; the rest are untouched by any executable property.",
      f"- Static detectors flag {counts['detector_flags_15_2_0_rows']} ledger rules on 15.2.0 (was {counts['detector_flags_14_1_0_rows']} on 14.1.0).",
      f"- Concordance verdicts exist for {counts['concordance_rows']['note8']} ledger rules from the 200-rule sample and {counts['concordance_rows']['note15']} from the active-core sample.",
      "", "## Open items (input to the next registry protocol; nothing patched here)", ""] + \
     [f"- `{r['rule_id']}` — {r['verification_status']}: " + "; ".join(f"{c['sample'].split(' (')[0]}: {c.get('note') or c.get('quote') or ''}".strip()[:220] for c in r["concordance"] if c["label"] == "DISCORDANT")
      + ("; " + "; ".join(f"{k}: {v}" for k, v in r["detector_flags_15_2_0"].items()) if r["detector_flags_15_2_0"] else "")
      for r in ledger if r["verification_status"] in ("discordant_open", "flagged_open")] + [
      "", "Files: `LEDGER.json.gz` (records), `ledger_counts.json`, `build_ledger.py` (reproducible definition)."]

with gzip.GzipFile(os.path.join(HERE, "LEDGER.json.gz"), "wb", mtime=0) as f:
    f.write(json.dumps(ledger, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"))
json.dump(counts, open(os.path.join(HERE, "ledger_counts.json"), "w"), indent=1, sort_keys=True)
open(os.path.join(HERE, "LEDGER_SUMMARY.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
