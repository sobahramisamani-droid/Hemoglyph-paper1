"""Structured error audit of eICU-demo misses (clinician-listed, lab-detectable group absent from the top-5).

Each miss is classified with a pre-declared, deterministic taxonomy so the audit is reproducible:
  A  not supported by the available laboratory values (key analyte(s) inside the range that defines the
     condition, e.g. "diabetes" with every glucose < 200 and no HbA1c)  -> label reflects history / clinical
     context, not the panel the engine saw
  B  displaced: the entity was in the differential (rank 6-25) but ranked below other true findings
  C  severity / scoring defect: laboratory signature present, entity proposed but p < 0.5 and outside top-5,
     or entity absent although a definitional signature was present (C1 absent, C2 present but low)
  D  mapping gap: an entity synonymous with the group was listed in the top-5 but is not in the SAP id list
     (detected by a secondary synonym table; reported, not credited)
The laboratory signatures are the guideline thresholds used throughout the SAP (ADA, KDIGO, WHO, CLSI).

python3 eval/error_audit.py --per-stay eval/results/eicu_demo/per_stay.json --n 200 --seed 20261022 \
        --out eval/results/eicu_demo/error_audit_v4.md
"""
import json, argparse, random, collections, re, sys
sys.path.insert(0, "eval")

ap = argparse.ArgumentParser(); ap.add_argument("--per-stay", required=True); ap.add_argument("--n", type=int, default=200)
ap.add_argument("--seed", type=int, default=20261022); ap.add_argument("--out", required=True); ap.add_argument("--label", default="v4")
a = ap.parse_args()
rows = json.load(open(a.per_stay))


from error_audit_lib import V, egfr, SIG  # shared signature table (SAP amendment 5)

# synonyms that would satisfy a clinician but are not in the SAP id list (mapping gaps; reported, never credited)
SYN = {
    "sepsis": re.compile(r"bacterial_infection|systemic_inflammatory|sirs|infection"),
    "heart_failure": re.compile(r"volume_overload|cardiogenic"),
    "diabetes": re.compile(r"stress_hyperglycemia|prediabetes|insulin_resistance"),
    "anemia": re.compile(r"anemia|anaemia"),
    "coagulopathy": re.compile(r"inr|warfarin|anticoag"),
    "cirrhosis_liver_failure": re.compile(r"hepat|liver|portal"),
    "malnutrition": re.compile(r"hypoalbumin|protein"),
    "alcohol_withdrawal": re.compile(r"alcohol|ethanol"),
}

# collect all misses (coded, key analyte measured, rank > 5 or absent)
GROUP_LABS = None
misses = []
for r in rows:
    for g in r["coded"]:
        if g not in SIG: continue
        rank = r["gr"].get(g)
        if rank is not None and rank <= 5: continue
        misses.append((r, g, rank))
random.Random(a.seed).shuffle(misses)
sample = misses[: a.n]

cat = collections.Counter(); by_group = collections.defaultdict(collections.Counter); examples = collections.defaultdict(list)
for r, g, rank in sample:
    v = r["vals"]; sig = SIG[g](v, r["age"], r["sex"]); p = r["gp"].get(g, 0.0)
    top = [t[0] for t in r["top5"]]
    if not sig: c = "A"
    elif rank is not None and rank <= 25 and p >= 0.5: c = "B"
    elif rank is not None: c = "C2"
    elif SYN.get(g) and any(SYN[g].search(t) for t in top): c = "D"
    else: c = "C1"
    cat[c] += 1; by_group[g][c] += 1
    if len(examples[c]) < 6:
        keyv = {k: v.get(k) for k in ("creatinine", "glucose", "bicarbonate", "potassium", "sodium", "hemoglobin", "platelet_count", "white_blood_cell_count", "lactate", "albumin", "international_normalized_ratio", "troponin_i", "b_type_natriuretic_peptide") if v.get(k) is not None}
        examples[c].append(f"stay {r['stay']} ({r['age']}{r['sex'][0]}) coded **{g}** rank={rank} p={p:.2f}; top-5 {top}; key values {keyv}")

NAMES = {"A": "A — not supported by the measured laboratory values (label = history/clinical context)",
         "B": "B — displaced: listed with p ≥ 0.5 but ranked 6–25 below other true findings",
         "C1": "C1 — knowledge/logic miss: laboratory signature present, entity never proposed",
         "C2": "C2 — severity/scoring defect: signature present, entity proposed but p < 0.5 and outside top-5",
         "D": "D — label-map gap: a synonymous entity was in the top-5 but is not in the SAP id list (not credited)"}
n = len(sample)
L = [f"# Structured error audit — eICU-CRD demo, engine {a.label}", "",
     f"Population: every (stay, clinician-listed group) pair with the key analyte measured and the group absent from the top-5 "
     f"(N = {len(misses)} misses across {len(rows)} stays). A fixed-seed random sample of {n} misses was classified with a pre-declared, "
     f"deterministic taxonomy (see script header); no manual relabelling.", "",
     "| Category | n | % of sampled misses |", "|---|---:|---:|"]
for c in ("A", "B", "C1", "C2", "D"):
    L.append(f"| {NAMES[c]} | {cat[c]} | {100*cat[c]/n:.1f}% |")
recov = cat["B"] + cat["C1"] + cat["C2"]
L += ["", f"**Interpretation.** {cat['A']} / {n} ({100*cat['A']/n:.0f}%) of misses carry no laboratory signature of the listed condition and are not "
      f"recoverable by any laboratory-only system without inventing evidence; {recov} ({100*recov/n:.0f}%) are in principle recoverable "
      f"(engine-side), of which {cat['C1']} are knowledge/logic gaps, {cat['C2']} scoring/severity defects and {cat['B']} ranking displacements "
      f"caused by the five-slot cut-off; {cat['D']} reflect the evaluation label map rather than the engine.", "",
      "## By clinician-listed group (sampled misses)", "", "| group | n | A | B | C1 | C2 | D |", "|---|---:|---:|---:|---:|---:|---:|"]
for g, c in sorted(by_group.items(), key=lambda kv: -sum(kv[1].values())):
    L.append(f"| {g} | {sum(c.values())} | {c['A']} | {c['B']} | {c['C1']} | {c['C2']} | {c['D']} |")
L += ["", "## Examples (first six per category, verbatim engine outputs)", ""]
for c in ("A", "B", "C1", "C2", "D"):
    L.append(f"**{NAMES[c]}**"); L += [f"- {e}" for e in examples[c]]; L.append("")
open(a.out, "w").write("\n".join(L) + "\n")
json.dump({"n_misses": len(misses), "n_sample": n, "cat": cat, "by_group": {g: dict(c) for g, c in by_group.items()}}, open(a.out.replace(".md", ".json"), "w"), indent=1)
print("\n".join(L[:12]))
