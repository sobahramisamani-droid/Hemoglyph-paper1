#!/usr/bin/env python3
"""Phase A summary (eval/provenance/PROTOCOL.md): ACTIVE CORE / HOT CORE / DORMANT and their provenance classes.
Reads activity_*.json.gz, the shipped registry and the source-verification table. Writes core_rules.json.gz,
PHASE_A_RESULTS.md. No registry field is modified.
"""
import gzip, json, os, sys, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import brotli
reg = json.loads(brotli.decompress(open(os.path.join(ROOT, "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"), "rb").read()))
rules = {k: v for k, v in reg["rules"].items() if v.get("executable")}
src = {s["source_id"]: s for s in json.load(gzip.open(os.path.join(ROOT, "eval/results/source_verification_13.4.1.json.gz"), "rt"))["sources"]}
srcmeta = reg["guideline_sources"]; srcmeta = {s.get("source_id", i): s for i, s in (srcmeta.items() if isinstance(srcmeta, dict) else enumerate(srcmeta))}

def loc_class(rule):
    """same classes as Fig. S1, decided per rule from its first source"""
    sid = (rule.get("source_ids") or [None])[0]
    if sid is None: return "no_locator"
    v = src.get(sid, {}).get("verification_status", "")
    m = srcmeta.get(sid, {}); url = (m.get("url") or ""); doi = m.get("doi") or ("doi.org" in url)
    if v in ("verified", "doi_verified"): return "doi_resolved"
    if v in ("generic_landing_page",): return "generic_landing_page"
    if v in ("title_mismatch", "unresolved"): return "doi_unresolved_or_mismatch"
    if v in ("url_only", "landing_page_reached", "reachable"): return "landing_page"
    if v in ("url_unreachable",): return "unreachable"
    if v in ("no_locator",) or not url: return "no_locator"
    return v or "other"

acts = {}
for p in sorted(glob.glob(os.path.join(HERE, "activity_*.json.gz"))):
    a = json.load(gzip.open(p, "rt")); acts[a["meta"]["corpus"]] = a
pooled = collections.defaultdict(lambda: [0, 0, 0]); fired_any = set()
for c, a in acts.items():
    for rid, (f, c10, c5) in a["counts"].items():
        if rid not in rules: continue
        p = pooled[rid]; p[0] += f; p[1] += c10; p[2] += c5; fired_any.add(rid)
core = {rid for rid, p in pooled.items() if p[1] >= 1}
hot = {rid for rid, p in pooled.items() if p[1] >= 10}
dormant = set(rules) - fired_any
fired_only = fired_any - core
anchors = {rid for rid, r in rules.items() if r.get("status") == "curated_guideline_anchored"}

def prov(S):
    return collections.Counter(loc_class(rules[r]) for r in S)
def srcs(S):
    return collections.Counter((rules[r].get("source_ids") or ["(none)"])[0] for r in S)

out = {"n_cases": {c: a["meta"]["n_cases"] for c, a in acts.items()}, "n_exec": len(rules),
       "sets": {"active_core": len(core), "hot_core": len(hot), "fired_not_contributing": len(fired_only), "dormant": len(dormant)},
       "anchors": {"total": len(anchors), "in_core": len(anchors & core), "in_hot": len(anchors & hot), "dormant": len(anchors & dormant)},
       "provenance": {"active_core": dict(prov(core)), "hot_core": dict(prov(hot)), "dormant": dict(prov(dormant)), "all_exec": dict(prov(set(rules)))},
       "top_sources_core": srcs(core).most_common(15), "top_sources_hot": srcs(hot).most_common(15),
       "rule_types_core": dict(collections.Counter(rules[r].get("rule_type") for r in core)),
       "diseases_core": len({rules[r]["disease_id"] for r in core})}
json.dump(out, open(os.path.join(HERE, "phase_a_summary.json"), "w"), indent=1)
json.dump({rid: {"fired": pooled[rid][0], "contrib10": pooled[rid][1], "contrib5": pooled[rid][2], "disease_id": rules[rid]["disease_id"],
                 "status": rules[rid]["status"], "rule_type": rules[rid].get("rule_type"), "expression": rules[rid].get("expression"),
                 "source_ids": rules[rid].get("source_ids"), "loc_class": loc_class(rules[rid])} for rid in sorted(core, key=lambda r: -pooled[r][1])},
          gzip.open(os.path.join(HERE, "core_rules.json.gz"), "wt"))

L = ["# Phase A — activity log of the shipped registry (14.2.0, engine v8.2), label-free", "",
     "Cases: " + ", ".join(f"{c} {n}" for c, n in out["n_cases"].items()), "",
     "| Set | rules | share of 33,183 | anchors in set |", "|---|---|---|---|"]
for k, n in out["sets"].items():
    S = {"active_core": core, "hot_core": hot, "fired_not_contributing": fired_only, "dormant": dormant}[k]
    L.append(f"| {k} | {n} | {100*n/len(rules):.1f} % | {len(S & anchors)} |")
L += ["", f"Anchors: {len(anchors)} total; {len(anchors & core)} in active core; {len(anchors & hot)} in hot core; {len(anchors & dormant)} dormant.",
      f"Active core spans {out['diseases_core']} disease ids; rule types: {out['rule_types_core']}", "",
      "Provenance class (first cited source) by set:", "| class | all executable | active core | hot core | dormant |", "|---|---|---|---|---|"]
classes = sorted(set(out["provenance"]["all_exec"]) | set(out["provenance"]["active_core"]))
for c in classes:
    L.append(f"| {c} | " + " | ".join(f"{out['provenance'][s].get(c, 0)} ({100*out['provenance'][s].get(c, 0)/max(1, {'all_exec': len(rules), 'active_core': len(core), 'hot_core': len(hot), 'dormant': len(dormant)}[s]):.1f} %)" for s in ("all_exec", "active_core", "hot_core", "dormant")) + " |")
L += ["", "Most-cited sources in the active core: " + "; ".join(f"{s} ({n})" for s, n in out["top_sources_core"]),
      "", "Most-cited sources in the hot core: " + "; ".join(f"{s} ({n})" for s, n in out["top_sources_hot"]),
      "", "Registered expectations: core 800-4,000; anchors >= 30 % of hot core; see PROTOCOL.md."]
open(os.path.join(HERE, "PHASE_A_RESULTS.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
