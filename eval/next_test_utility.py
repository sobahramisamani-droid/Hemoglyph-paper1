"""Next-test utility (ESL extension 8 metric).

For misses in category A of the structured error audit (clinician-listed condition with NO laboratory signature in the
measured panel), a laboratory-only system cannot honestly assert the diagnosis; the useful output is the test that would
settle it. This script re-runs the engine on those stays and asks: did `next_tests` (or any entity's recommended_tests)
name the discriminating test for the listed condition?

Only groups whose discriminating test is distinct from the already-measured key analyte are scored (a normal TSH cannot be
'rescued' by ordering TSH).

python3 eval/next_test_utility.py --per-stay eval/results/eicu_demo/per_stay.json --audit eval/results/eicu_demo/error_audit_v4.json \
        --out eval/results/eicu_demo/next_test_utility_v4.md
"""
import json, argparse, random, sys, logging, collections, re
sys.path.insert(0, "eval")
logging.disable(logging.CRITICAL); sys.path.insert(0, "."); sys.path.insert(0, "eval/realdata")
import eval_eicu as ee
import analyse_gidlines as ag
from error_audit_lib import SIG  # shared signature table

ap = argparse.ArgumentParser(); ap.add_argument("--per-stay", required=True); ap.add_argument("--n", type=int, default=200)
ap.add_argument("--seed", type=int, default=20261022); ap.add_argument("--out", required=True); a = ap.parse_args()
rows = json.load(open(a.per_stay)); U = {t[0]: t[1] for t in ee.LAB.values() if t}

# group -> regex over recommended test names that would discriminate the condition
DISC = {
    "heart_failure": re.compile(r"BNP|natriuretic", re.I),
    "diabetes": re.compile(r"HbA1c", re.I),
    "hyperglycemia": re.compile(r"HbA1c", re.I),
    "sepsis": re.compile(r"lactate|procalcitonin|blood cultures", re.I),
    "chronic_kidney_disease": re.compile(r"prior creatinine|baseline|albumin-creatinine|cystatin", re.I),
    "acute_kidney_injury": re.compile(r"prior creatinine|baseline|urine sodium|urinalysis", re.I),
    "renal_impairment": re.compile(r"prior creatinine|baseline|albumin-creatinine|cystatin|urinalysis|urine sodium", re.I),
    "alcohol_withdrawal": re.compile(r"ethanol|GGT|carbohydrate-deficient", re.I),
    "hypocalcemia": re.compile(r"ionised calcium|ionized calcium", re.I),
    "coagulopathy": re.compile(r"fibrinogen|D-dimer|INR", re.I),
    "malnutrition": re.compile(r"prealbumin|C-reactive", re.I),
}

# rebuild the same miss sample as error_audit.py (same seed, same population)
misses = []
for r in rows:
    for g in r["coded"]:
        if g not in SIG: continue
        rank = r["gr"].get(g)
        if rank is not None and rank <= 5: continue
        misses.append((r, g, rank))
random.Random(a.seed).shuffle(misses); sample = misses[: a.n]
A = [(r, g) for r, g, rank in sample if not SIG[g](r["vals"], r["age"], r["sex"]) and g in DISC]

E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
hit = collections.Counter(); tot = collections.Counter(); n_next = []; ex = []
cache = {}
for r, g in A:
    if r["stay"] not in cache:
        obs = {k: {"value": float(v), "unit": U.get(k)} for k, v in r["vals"].items() if k in U}
        rep = E.interpret(obs, None, {"age_years": int(r["age"]), "sex_at_birth": r["sex"]}).to_dict()
        names = [t["test"] for t in rep.get("next_tests", [])]
        for d in rep["differential_diagnosis"][:10]:
            names += list(d.get("recommended_tests") or [])
        cache[r["stay"]] = names; n_next.append(len(rep.get("next_tests", [])))
    names = cache[r["stay"]]; ok = any(DISC[g].search(n) for n in names)
    tot[g] += 1; hit[g] += ok
    if len(ex) < 8: ex.append(f"stay {r['stay']} listed **{g}** (no lab signature) → next tests: {names[:5]} → {'✓' if ok else '✗'}")

L = [f"# Next-test utility on category-A misses (eICU-CRD demo)", "",
     f"Category-A misses in the fixed-seed audit sample with a scorable discriminating test: {len(A)}. For each, the engine was re-run and its "
     f"`next_tests` / per-entity `recommended_tests` were searched for the test that would establish the listed condition "
     f"(e.g. BNP for heart failure, HbA1c for diabetes, lactate/procalcitonin/cultures for sepsis, prior creatinine/ACR/cystatin C for CKD).", "",
     "| listed condition (no lab signature) | n | discriminating test recommended | % |", "|---|---:|---:|---:|"]
for g in sorted(tot, key=lambda k: -tot[k]):
    L.append(f"| {g.replace('_',' ')} | {tot[g]} | {hit[g]} | {100*hit[g]/tot[g]:.0f}% |")
T, H = sum(tot.values()), sum(hit.values())
L += [f"| **all** | **{T}** | **{H}** | **{100*H/max(T,1):.0f}%** |", "",
      f"Median number of next-test recommendations per stay: {sorted(n_next)[len(n_next)//2] if n_next else 0}.", "", "## Examples", ""] + [f"- {e}" for e in ex]
open(a.out, "w").write("\n".join(L) + "\n"); print("\n".join(L[:14]))
json.dump({"n": T, "hit": H, "by_group": {g: [hit[g], tot[g]] for g in tot}}, open(a.out.replace(".md", ".json"), "w"))
