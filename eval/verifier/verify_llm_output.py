#!/usr/bin/env python3
"""Executable verifier for LLM differentials (protocol: eval/verifier/PROTOCOL.md, committed before this script ran).

Each LLM entry of the 400 blind readings is mapped to a label group (SYN) and checked against the same panel with the
guideline criterion already used by the panel-supported metric (CRIT): supported / contradicted / absent /
not_verifiable. Unsupported entries are demoted (arm B) or removed (arm C); recall against clinician labels and the
unsupported-assertion rate are reported for LLM raw (A), B, C, engine v7 (D) and engine-through-verifier (E).
No LLM call, no threshold change, frozen v7 untouched. Output: eval/verifier/RESULTS.md, results.json
"""
import json, os, sys, gzip, math, random, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.join(ROOT, "eval", "baselines"))
from eval_eicu import GROUPS
from llm_zero_shot import SYN
from panel_supported_metric import CRIT
R = os.path.join(ROOT, "eval", "results", "eicu_demo")

def P(x):
    return json.loads(x) if isinstance(x, str) else x

rows = {str(r["stay"]): r for r in json.load(gzip.open(os.path.join(R, "per_stay_v7.json.gz"), "rt"))}
for r in rows.values():
    for k in ("gr", "gp", "coded", "labs", "vals"): r[k] = P(r[k])

# the 400 blind LLM readings, loaded exactly as in b8_v7_cluster.py
key = json.load(open(os.path.join(R, "b8_key_n240.json")))
llm8 = {c["case"]: c["llm"] for c in json.load(open(os.path.join(R, "b8_llm_blind_n240.json")))["cases"]}
b3 = json.load(open(os.path.join(R, "llm_agent_b3_n100.json")))
b4s = json.load(open(os.path.join(R, "b4_oos_n60_vs_v3.json"))); b4l = json.load(open(os.path.join(R, "b4_llm_blind_n60.json")))
reads = {}
for k in key: reads[str(k["stay"])] = llm8[k["case"]]
for r in b3: reads[str(r["stay"])] = r["llm"]
for r in b4s: reads[str(r["stay"])] = [{"name": n, "probability": p} for n, p in b4l[str(r["stay"])]]
assert len(reads) == 400 and all(s in rows for s in reads)

def groups_of(name):
    return [g for g, rx in SYN.items() if re.search(rx, str(name), re.I)]

def crit_vals(v):
    # key alias only: CRIT's coagulopathy function reads "inr"; the panel stores "international_normalized_ratio".
    # Threshold unchanged. (The same alias gap makes the published panel-supported metric treat every coagulopathy
    # label as "analyte missing"; recorded in RESULTS.md, frozen numbers not re-run.)
    v = dict(v)
    if "inr" not in v and "international_normalized_ratio" in v: v["inr"] = v["international_normalized_ratio"]
    return v

def verdict(g, row):
    f = CRIT.get(g)
    if f is None: return "not_verifiable"
    s = f(crit_vals(row["vals"]), row)
    return "absent" if s is None else ("supported" if s else "contradicted")

def entry_verdict(name, row):
    """worst-case over the groups an entry maps to is NOT used; an entry is unsupported only if EVERY verifiable group
    it maps to is unsupported (conservative towards the LLM)."""
    gs = groups_of(name)
    if not gs: return "out_of_vocabulary", gs
    vs = [verdict(g, row) for g in gs]
    if "supported" in vs: return "supported", gs
    if all(v == "not_verifiable" for v in vs): return "not_verifiable", gs
    ver = [v for v in vs if v != "not_verifiable"]
    return ("contradicted" if "contradicted" in ver else "absent"), gs

def engine_has(g, row):
    return g in row["gr"]

def ranks_from_entries(entries):
    gr = {}
    for rank, d in enumerate(entries, 1):
        for g in groups_of(d.get("name", "")): gr.setdefault(g, rank)
    return gr

def labels(row):
    return [g for g in row["coded"] if g in GROUPS and any(k in row["labs"] for k in GROUPS[g][2])]

UNSUP = ("contradicted", "absent")
arms = {"A_llm_raw": {}, "B_llm_demoted": {}, "C_llm_removed": {}, "D_engine_v7": {}}
stats = collections.Counter(); demoted_labels = []; agree = collections.Counter(); top5_unsup = {"llm": [0, 0], "engine": [0, 0]}
per_entry = []
for s, ents in reads.items():
    row = rows[s]; lab = labels(row)
    ann = []
    for i, d in enumerate(ents, 1):
        v, gs = entry_verdict(d.get("name", ""), row)
        ann.append((d, v, gs)); stats[v] += 1
        if i <= 5 and v != "out_of_vocabulary":
            top5_unsup["llm"][1] += 1; top5_unsup["llm"][0] += v in UNSUP
        for g in gs:
            if CRIT.get(g): agree[(verdict(g, row) == "supported", engine_has(g, row))] += 1
        per_entry.append({"stay": s, "rank": i, "name": d.get("name"), "p": d.get("probability"), "verdict": v, "groups": gs})
    keep = [a for a in ann if a[1] not in UNSUP]; dem = [a for a in ann if a[1] in UNSUP]
    for d, v, gs in dem:
        hit = [g for g in gs if g in lab]
        if hit: demoted_labels.append({"stay": s, "name": d.get("name"), "verdict": v, "labels": hit, "vals": {k: row["vals"].get(k) for g in hit for k in GROUPS[g][2]}})
    arms["A_llm_raw"][s] = ranks_from_entries([a[0] for a in ann])
    arms["B_llm_demoted"][s] = ranks_from_entries([a[0] for a in keep + dem])
    arms["C_llm_removed"][s] = ranks_from_entries([a[0] for a in keep])
    arms["D_engine_v7"][s] = row["gr"]
    # E: engine's own top-5 through the verifier (groups with a criterion only)
    for g, rk in row["gr"].items():
        if rk <= 5 and CRIT.get(g):
            top5_unsup["engine"][1] += 1; top5_unsup["engine"][0] += verdict(g, row) in UNSUP

def recall(arm, k, S=None):
    S = S or list(reads); n = h = 0
    for s in S:
        for g in labels(rows[s]): n += 1; h += arm[s].get(g, 99) <= k
    return h / n

def boot_diff(a, b, k, B=4000, seed=7):
    rnd = random.Random(seed); S = list(reads); d = []
    for _ in range(B):
        smp = [S[rnd.randrange(len(S))] for _ in S]; d.append(recall(a, k, smp) - recall(b, k, smp))
    d.sort(); p = 2 * min(sum(x <= 0 for x in d), sum(x >= 0 for x in d)) / B
    return d[int(0.025 * B)], d[int(0.975 * B)], min(1.0, p)

nlab = sum(len(labels(rows[s])) for s in reads)
res = {"n_stays": 400, "n_labels": nlab, "entry_verdicts": dict(stats), "top5_unsupported": top5_unsup,
       "recall": {a: {k: recall(arm, k) for k in (1, 3, 5, 10)} for a, arm in arms.items()},
       "paired_B_minus_A": {k: boot_diff(arms["B_llm_demoted"], arms["A_llm_raw"], k) for k in (1, 3, 5, 10)},
       "paired_C_minus_A": {k: boot_diff(arms["C_llm_removed"], arms["A_llm_raw"], k) for k in (1, 3, 5, 10)},
       "demoted_label_entries": demoted_labels, "n_demoted_entries": stats["contradicted"] + stats["absent"],
       "verdict_agreement_criterion_vs_engine": {f"crit_{a}_engine_{b}": n for (a, b), n in agree.items()}}
# unsupported rate after demotion (top-5 of arm B)
u = [0, 0]
for s, ents in reads.items():
    ann = [(d, entry_verdict(d.get("name", ""), rows[s])[0]) for d in ents]
    order = [a for a in ann if a[1] not in UNSUP] + [a for a in ann if a[1] in UNSUP]
    for d, v in order[:5]:
        if v != "out_of_vocabulary": u[1] += 1; u[0] += v in UNSUP
res["top5_unsupported"]["llm_after_demotion"] = u
# post-hoc sensitivity (declared after the first run, 2026-10-27): the frozen synonym map sends any "acidosis" to the
# metabolic-acidosis group, so respiratory-acidosis entries are scored "contradicted" by the bicarbonate criterion.
# Count LLM top-5 unsupported entries whose name contains "respiratory"; they are mapping artefacts, not LLM errors.
resp = sum(1 for e in per_entry if e["rank"] <= 5 and e["verdict"] in UNSUP and "respiratory" in str(e["name"]).lower())
res["top5_unsupported"]["llm_excluding_respiratory_names"] = [top5_unsup["llm"][0] - resp, top5_unsup["llm"][1]]
# engine top-5 unsupported by group (why the engine fails its own proxy criteria)
eg = collections.Counter(); et = collections.Counter()
for s in reads:
    row = rows[s]
    for g, rk in row["gr"].items():
        if rk <= 5 and CRIT.get(g):
            et[g] += 1; v = verdict(g, row); eg[(g, v)] += 1
res["engine_top5_by_group"] = {f"{g}|{v}": n for (g, v), n in eg.items()}; res["engine_top5_total_by_group"] = dict(et)
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
json.dump(per_entry, open(os.path.join(HERE, "entry_verdicts.json"), "w"))

L = ["# Executable verifier behind the LLM — 400 blind eICU stays, no new LLM call", "",
     f"Labels: {nlab} (b8 rule). Entry verdicts over {sum(stats.values())} LLM entries: " + ", ".join(f"{k} {v}" for k, v in sorted(stats.items())), "",
     "| Arm | recall@1 | @3 | @5 | @10 |", "|---|---|---|---|---|"]
for a, rr in res["recall"].items():
    L.append(f"| {a} | " + " | ".join(f"{100*rr[k]:.1f}" for k in (1, 3, 5, 10)) + " |")
L += ["", "Paired difference (stay-clustered bootstrap, 4000 reps), points:"]
for nm in ("paired_B_minus_A", "paired_C_minus_A"):
    L.append(f"- {nm}: " + "; ".join(f"@{k} {100*recall(arms['B_llm_demoted' if 'B' in nm else 'C_llm_removed'], k)-100*recall(arms['A_llm_raw'], k):+.1f} ({100*lo:+.1f} to {100*hi:+.1f}, p={p:.3f})" for k, (lo, hi, p) in res[nm].items()))
t = res["top5_unsupported"]
L += ["", f"Unsupported assertions among mapped top-5 entries: LLM raw {t['llm'][0]}/{t['llm'][1]} ({100*t['llm'][0]/t['llm'][1]:.1f} %); "
      f"LLM after demotion {t['llm_after_demotion'][0]}/{t['llm_after_demotion'][1]} ({100*t['llm_after_demotion'][0]/t['llm_after_demotion'][1]:.1f} %); "
      f"engine v7 top-5 (criterion groups) {t['engine'][0]}/{t['engine'][1]} ({100*t['engine'][0]/t['engine'][1]:.1f} %).",
      f"Verifier cost: {len(demoted_labels)} of {res['n_demoted_entries']} demoted entries were clinician labels ({100*len(demoted_labels)/max(1,res['n_demoted_entries']):.1f} %):"]
for d in demoted_labels: L.append(f"  - stay {d['stay']}: '{d['name']}' [{d['verdict']}] labels {d['labels']} vals {d['vals']}")
x = res["top5_unsupported"]["llm_excluding_respiratory_names"]
L += ["", f"Sensitivity (post hoc): {resp} of the LLM's unsupported top-5 entries are respiratory-acidosis names mapped to the metabolic-acidosis group by the frozen synonym map; excluding them, {x[0]}/{x[1]} ({100*x[0]/x[1]:.1f} %).",
      "Engine top-5 unsupported by group (criterion is a proxy stricter than some engine rules; e.g. the diabetes label group also contains hyperglycaemia ids while its criterion is glucose >= 200 mg/dL or HbA1c >= 6.5 %):"]
for (g, v), n in sorted(eg.items(), key=lambda kv: -kv[1]):
    if v in UNSUP: L.append(f"  - {g} {v}: {n}/{et[g]}")
L += ["", "Criterion verdict vs engine differential (per mapped group with a criterion): " + ", ".join(f"{k} {v}" for k, v in res["verdict_agreement_criterion_vs_engine"].items()),
      "", "Notes: CRIT's coagulopathy function reads key 'inr' while panels store 'international_normalized_ratio'; aliased here (threshold unchanged). "
      "The same gap means the published panel-supported metric treated every coagulopathy label as analyte-missing (excluded); frozen results were not re-run.",
      "Registered predictions (PROTOCOL.md): LLM top-5 unsupported 15-30 %; after demotion < 5 %; recall@5 change -2..+1; demoted-that-were-labels <= 10 %; engine top-5 unsupported 5-15 %."]
open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
