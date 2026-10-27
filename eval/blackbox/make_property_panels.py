#!/usr/bin/env python3
"""Black-box property-conformance benchmark — panel generator (declared 2026-10-27, before any LLM read).

The paper's executable invariants (Section 2.3) are applied to BOTH systems as black boxes on the same panels:
  P2 unit invariance      : 40 eICU panels re-expressed in SI units (creatinine µmol/L, glucose mmol/L, urea mmol/L,
                            bilirubin µmol/L, calcium mmol/L, haemoglobin g/L, albumin g/L, cholesterol mmol/L, ...)
  P3 presentation invariance : the same 40 panels with analyte order shuffled (seed) and five normal-valued distractor
                            analytes appended
  P4 monotonicity         : 20 panels × 3 creatinine values (observed, ×1.5, ×2.0); the renal rank must not fall
  P5 absent-analyte       : 40 panels with the single defining analyte of the engine's top-ranked, criterion-met
                            label removed; a diagnosis asserted at rank ≤ 5 without its defining analyte is an
                            unsupported assertion
  P6 healthy panels       : 50 guideline-healthy NHANES adults (engine: 2/485 false assertions); any disease asserted
                            at probability ≥ 0.5 / rank ≤ 3 is a false alarm
Base panels are drawn from the 400 stays already read blind by the LLM (B3/B4/B8) so the conventional-unit reading
exists and no new label exposure occurs. Outputs are written to eval/blackbox/panels_*.json (small). The reader
(engine or LLM) never sees labels. Scoring script: score_property_panels.py (written before reads are collected).
"""
from __future__ import annotations
import os, sys, json, gzip, ast, random
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from panel_supported_metric import CRIT  # noqa: E402
from eval_eicu import GROUPS  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
P = lambda x: ast.literal_eval(x) if isinstance(x, str) else x
rows = {str(r["stay"]): r for r in json.load(gzip.open(os.path.join(ROOT, "eval/results/eicu_demo/per_stay_v7.json.gz"), "rt"))}
for r in rows.values():
    for k in ("vals", "labs", "coded", "gp", "gr"):
        r[k] = P(r[k])

# the 400 stays read blind by the LLM
R = os.path.join(ROOT, "eval/results/eicu_demo")
key = json.load(open(os.path.join(R, "b8_key_n240.json")))
b3 = json.load(open(os.path.join(R, "llm_agent_b3_n100.json")))
b4 = json.load(open(os.path.join(R, "b4_oos_n60_vs_v3.json")))
read_stays = [str(k["stay"]) for k in key] + [str(r["stay"]) for r in b3] + [str(r["stay"]) for r in b4]
read_stays = [s for s in read_stays if s in rows]
assert len(read_stays) == 400, len(read_stays)

UNITS = {  # analyte: (conventional unit, SI unit, factor conv→SI)
    "creatinine": ("mg/dL", "µmol/L", 88.4), "glucose": ("mg/dL", "mmol/L", 0.0555), "blood_urea_nitrogen": ("mg/dL", "mmol/L", 0.357),
    "total_bilirubin": ("mg/dL", "µmol/L", 17.1), "direct_bilirubin": ("mg/dL", "µmol/L", 17.1), "calcium_total": ("mg/dL", "mmol/L", 0.2495),
    "hemoglobin": ("g/dL", "g/L", 10.0), "albumin": ("g/dL", "g/L", 10.0), "total_protein": ("g/dL", "g/L", 10.0),
    "total_cholesterol": ("mg/dL", "mmol/L", 0.02586), "ldl_cholesterol": ("mg/dL", "mmol/L", 0.02586), "hdl_cholesterol": ("mg/dL", "mmol/L", 0.02586),
    "triglycerides": ("mg/dL", "mmol/L", 0.01129), "uric_acid": ("mg/dL", "µmol/L", 59.48), "magnesium": ("mg/dL", "mmol/L", 0.4114),
    "phosphate": ("mg/dL", "mmol/L", 0.3229), "iron": ("µg/dL", "µmol/L", 0.1791), "lactate": ("mmol/L", "mg/dL", 9.01),
}
DEFAULT_UNIT = {"sodium": "mmol/L", "potassium": "mmol/L", "chloride": "mmol/L", "bicarbonate": "mmol/L", "anion_gap": "mmol/L",
                "wbc": "10^3/µL", "platelet_count": "10^3/µL", "hematocrit": "%", "mcv": "fL", "alt": "U/L", "ast": "U/L",
                "alkaline_phosphatase": "U/L", "inr": "ratio", "ph": "", "pco2": "mmHg", "po2": "mmHg", "troponin_i": "ng/mL", "bnp": "pg/mL",
                "lipase": "U/L", "ck": "U/L", "lactate_dehydrogenase": "U/L", "ferritin": "ng/mL", "tsh": "mIU/L"}
DISTRACTORS = [("mcv", 89.0), ("alkaline_phosphatase", 72.0), ("total_protein", 6.9), ("chloride", 102.0), ("tsh", 1.8)]

rng = random.Random(20261027)
stays40 = rng.sample(read_stays, 40)


def panel(stay, vals=None, order=None, si=False):
    r = rows[stay]; vals = vals or r["vals"]
    items = []
    for a in (order or list(vals)):
        v = vals[a]
        if si and a in UNITS:
            items.append({"analyte": a, "value": round(v * UNITS[a][2], 2 if UNITS[a][2] < 1 else 0), "unit": UNITS[a][1]})
        else:
            items.append({"analyte": a, "value": v, "unit": UNITS.get(a, (DEFAULT_UNIT.get(a, ""),))[0]})
    return {"stay": stay, "age": r["age"], "sex": r["sex"], "panel": items}


# P2 unit invariance
p2 = [panel(s, si=True) for s in stays40]
# P3 presentation invariance
p3 = []
for s in stays40:
    vals = dict(rows[s]["vals"]); order = list(vals); rng.shuffle(order)
    for a, v in DISTRACTORS:
        if a not in vals:
            vals[a] = v; order.append(a)
    rng.shuffle(order); p3.append(panel(s, vals=vals, order=order))
# P4 monotonicity (creatinine ladder) — panels with creatinine present and no AKI/CKD already at rank 1
cands = [s for s in read_stays if "creatinine" in rows[s]["vals"] and 0.6 <= rows[s]["vals"]["creatinine"] <= 1.3]
rng.shuffle(cands); stays20 = cands[:20]
p4 = []
for s in stays20:
    for f in (1.0, 1.5, 2.0):
        vals = dict(rows[s]["vals"]); vals["creatinine"] = round(vals["creatinine"] * f, 2)
        d = panel(s, vals=vals); d["ladder"] = f; p4.append(d)
# P5 absent-analyte: remove defining analyte of a criterion-met label group that the engine ranked ≤ 3
p5 = []
for s in read_stays:
    r = rows[s]
    for g, rk in sorted(r["gr"].items(), key=lambda x: x[1]):
        if rk > 3 or g not in CRIT or GROUPS[g][3] != "yes":
            continue
        met = CRIT[g](r["vals"], r)
        ka = GROUPS[g][2][0]
        if met and ka in r["vals"]:
            vals = {k: v for k, v in r["vals"].items() if k != ka and not (ka == "creatinine" and k == "blood_urea_nitrogen")}
            if len(vals) >= 8:
                d = panel(s, vals=vals); d["removed_analyte"] = ka; d["target_group"] = g; p5.append(d)
            break
    if len(p5) == 40:
        break
# P6 healthy NHANES adults: taken from the engine's healthy sweep file if available, else left for the NHANES script
p6_src = os.path.join(ROOT, "eval/results/nhanes_2015/healthy_panels.json")
p6 = json.load(open(p6_src))[:50] if os.path.exists(p6_src) else []

for name, obj in [("P2_units", p2), ("P3_presentation", p3), ("P4_monotonic", p4), ("P5_absent", p5), ("P6_healthy", p6)]:
    json.dump(obj, open(os.path.join(OUT, f"panels_{name}.json"), "w"), separators=(",", ":"))
    print(name, len(obj))
json.dump({"seed": 20261027, "stays40": stays40, "stays20": stays20, "p5_stays": [d["stay"] for d in p5]}, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
