"""Pre-specified sampling for the human (clinician) concordance audit — Supplementary Note 19.

Draws, deterministically (seed 20261028), 100 rules from the verification ledger built at
registry 15.2.0 (eval/verification_ledger/LEDGER.json.gz):
  * 50 active-core rules still executable in 15.2.0 (stratified: 25 hot-core, 25 other), and
  * 50 curated anchors that are NOT active-core members.
Writes rater forms WITHOUT any AI verdict (human_audit_sample_100.csv) and a sealed file
with the AI rater's verdicts for the post-hoc agreement analysis (ai_verdicts_sealed.json).
Run once; the outputs are committed and hashed. Re-running must reproduce them byte-for-byte.
"""
import csv, gzip, hashlib, json, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
L = json.load(gzip.open(os.path.join(ROOT, "eval", "verification_ledger", "LEDGER.json.gz")))
rng = random.Random(20261028)
def ids(rows): return sorted(r["rule_id"] for r in rows)
core_exec = [r for r in L if r["sets"]["active_core"] and r["executable_15_2_0"]]
hot = [r for r in core_exec if r["sets"]["hot_core"]]
cold = [r for r in core_exec if not r["sets"]["hot_core"]]
anch = [r for r in L if r["sets"]["curated_anchor"] and not r["sets"]["active_core"]]
pick = lambda rows, n: rng.sample(ids(rows), min(n, len(rows)))
chosen = pick(hot, 25); chosen += pick(cold, 50 - len(chosen)); chosen += pick(anch, 50)
by = {r["rule_id"]: r for r in L}
rows = []
for rid in chosen:
    r = by[rid]
    rows.append({
        "item": len(rows) + 1, "rule_id": rid, "disease_id": r["disease_id"], "rule_type": r["rule_type"],
        "stratum": "active_core_hot" if r["sets"]["hot_core"] else ("active_core" if r["sets"]["active_core"] else "curated_anchor"),
        "logic": " AND ".join(f'{l["feature"]} {l["operator"]} {l["value"]} {l.get("unit") or ""}'.strip() for l in r["leaves"]),
        "source_id": r["first_source_id"], "locator_class": r["locator_class"],
        "verdict (C/D/U)": "", "verbatim_quote_supporting_verdict": "", "page_or_section": "", "comment": "",
    })
with open(os.path.join(HERE, "human_audit_sample_100.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
sealed = {rid: {"status_15_2_0": by[rid]["status_15_2_0"], "verification_status": by[rid]["verification_status"],
                "concordance": by[rid]["concordance"]} for rid in chosen}
json.dump(sealed, open(os.path.join(HERE, "ai_verdicts_sealed.json"), "w"), indent=0, sort_keys=True)
h = hashlib.sha256(open(os.path.join(HERE, "human_audit_sample_100.csv"), "rb").read()).hexdigest()
open(os.path.join(HERE, "SHA256SUMS"), "w").write(f"{h}  human_audit_sample_100.csv\n")
import collections
print(collections.Counter(r["stratum"] for r in rows), "sha256", h[:16], "| pools: hot", len(hot), "cold", len(cold), "anchors-not-core", len(anch))
