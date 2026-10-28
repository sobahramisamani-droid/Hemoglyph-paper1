#!/usr/bin/env python3
"""Post-hoc analyses on a multi-label per-stay file (eICU demo `per_stay.json`):

1. Calibration of Hemoglyph group-level probabilities: ECE (10 equal-mass bins), reliability
   table, logistic recalibration slope/intercept (fitted on the same data = apparent; a
   split-half estimate is also reported: fit on odd stays, test on even stays).
2. Baseline B1 — single-analyte reference-range rule: for groups defined by one analyte the
   baseline score is the raw analyte value oriented toward the abnormality (AUROC of the value
   itself; sensitivity/specificity at the textbook cut-off). This is the strongest "no-model"
   comparator for electrolyte / haematology groups and shows whether the engine adds anything
   beyond flagging.
3. Safety S5 — critical-value capture: stays with a critical analyte value; was the
   corresponding entity in the top-5?
"""
from __future__ import annotations
import os, sys, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from eval_nhanes import auroc, boot_ci, fmt  # noqa: E402

# group -> (analyte, direction, cut-off, engine ids for S5)
B1 = {
    "hyperkalemia": ("potassium", +1, 5.1), "hypokalemia": ("potassium", -1, 3.5), "hyponatremia": ("sodium", -1, 135),
    "hypernatremia": ("sodium", +1, 145), "hypomagnesemia": ("magnesium", -1, 1.7), "hypocalcemia": ("calcium_total", -1, 8.5),
    "hypophosphatemia": ("phosphate", -1, 2.5), "anemia": ("hemoglobin", -1, 12.0), "thrombocytopenia": ("platelet_count", -1, 150),
    "leukocytosis": ("white_blood_cell_count", +1, 11.0), "metabolic_acidosis": ("bicarbonate", -1, 22), "lactic_acidosis": ("lactate", +1, 2.0),
    "acute_kidney_injury": ("creatinine", +1, 1.3), "renal_impairment": ("creatinine", +1, 1.3), "hyperglycemia": ("glucose", +1, 180),
    "diabetes": ("glucose", +1, 200), "hypothyroidism": ("thyroid_stimulating_hormone", +1, 4.5), "acute_pancreatitis": ("lipase", +1, 180),
    "acute_myocardial_infarction": ("troponin_i", +1, 0.04), "heart_failure": ("b_type_natriuretic_peptide", +1, 100),
    "rhabdomyolysis": ("creatine_kinase_total", +1, 1000), "coagulopathy": ("international_normalized_ratio", +1, 1.5),
}
CRIT = [  # analyte, op, threshold, accepted ids in top-5 or critical alerts
    ("potassium", ">=", 6.5, {"hyperkalemia", "severe_hyperkalemia"}), ("potassium", "<=", 2.5, {"hypokalemia", "severe_hypokalemia"}),
    ("sodium", "<=", 120, {"hyponatremia", "severe_hyponatremia"}), ("sodium", ">=", 160, {"hypernatremia", "severe_hypernatremia"}),
    ("glucose", "<=", 50, {"hypoglycemia", "fasting_hypoglycemia", "hyperinsulinemic_hypoglycemia", "sulfonylurea_induced_hypoglycemia", "severe_hypoglycemia"}),
    ("glucose", ">=", 500, {"hyperglycemia", "diabetic_ketoacidosis", "hyperosmolar_hyperglycemic_state", "severe_hyperglycemia", "type_2_diabetes", "diabetes_mellitus"}),
    ("calcium_total", ">=", 14, {"hypercalcemia", "hypercalcemic_crisis", "severe_hypercalcemia"}), ("lactate", ">=", 4, {"lactic_acidosis", "sepsis", "septic_shock", "shock"}),
    ("arterial_ph", "<=", 7.20, {"metabolic_acidosis", "lactic_acidosis", "diabetic_ketoacidosis", "respiratory_acidosis", "severe_acidemia", "acidemia", "high_anion_gap_metabolic_acidosis", "mixed_acid_base_disorder"}),
    ("hemoglobin", "<=", 6, {"anemia", "acute_blood_loss_anemia", "severe_anemia", "pancytopenia"}), ("platelet_count", "<=", 20, {"thrombocytopenia", "severe_thrombocytopenia", "immune_thrombocytopenia", "disseminated_intravascular_coagulation", "pancytopenia"}),
    ("white_blood_cell_count", ">=", 100, {"leukocytosis", "acute_myeloid_leukemia", "chronic_myeloid_leukemia", "leukemoid_reaction", "chronic_lymphocytic_leukemia", "hyperleukocytosis", "leukocytosis_pattern", "acute_leukemia_support_pattern", "chronic_leukemia_support_pattern"}),
]


def ece(y, p, bins=10):
    y = np.asarray(y); p = np.asarray(p); order = np.argsort(p); y, p = y[order], p[order]
    edges = np.linspace(0, len(p), bins + 1).astype(int); tot = 0.0; rows = []
    for i in range(bins):
        sl = slice(edges[i], edges[i + 1])
        if edges[i + 1] <= edges[i]:
            continue
        conf, acc = p[sl].mean(), y[sl].mean(); tot += abs(conf - acc) * (edges[i + 1] - edges[i]) / len(p)
        rows.append((conf, acc, edges[i + 1] - edges[i]))
    return tot, rows


def logit_fit(y, p, iters=500, lr=0.1):
    """Platt-style logistic recalibration: sigmoid(a*logit(p)+b)."""
    y = np.asarray(y, float); z = np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
    a, b = 1.0, 0.0
    for _ in range(iters):
        q = 1 / (1 + np.exp(-(a * z + b))); ga = ((q - y) * z).mean(); gb = (q - y).mean(); a -= lr * ga; b -= lr * gb
    return a, b


def main(path):
    rows = json.load(open(path)); out = []
    # 1. calibration pooled over all evaluable (group, stay) pairs
    ys, ps, ys_odd, ps_odd, ys_even, ps_even = [], [], [], [], [], []
    for i, r in enumerate(rows):
        for g, p in r["gp"].items():
            y = int(g in r["coded"]); ys.append(y); ps.append(p)
            (ys_odd if i % 2 else ys_even).append(y); (ps_odd if i % 2 else ps_even).append(p)
    e, tab = ece(ys, ps)
    a, b = logit_fit(ys, ps)
    a_o, b_o = logit_fit(ys_odd, ps_odd)
    pe = np.asarray(ps_even); ze = np.log(np.clip(pe, 1e-4, 1 - 1e-4) / (1 - np.clip(pe, 1e-4, 1 - 1e-4)))
    pe_cal = 1 / (1 + np.exp(-(a_o * ze + b_o)))
    e_even_raw, _ = ece(ys_even, pe); e_even_cal, _ = ece(ys_even, pe_cal)
    out += ["## Calibration of group-level probabilities (entity present in differential)", "",
            f"Pairs: {len(ys)}; label prevalence {np.mean(ys):.3f}; mean probability {np.mean(ps):.3f}; **ECE {e:.3f}**; "
            f"logistic recalibration slope {a:.2f}, intercept {b:.2f} (slope < 1 and negative intercept = over-confidence).",
            f"Split-half: recalibration fitted on odd stays, applied to even stays: ECE {e_even_raw:.3f} → {e_even_cal:.3f}.", "",
            "| bin mean p | observed rate | n |", "|---|---|---|"] + [f"| {c:.2f} | {o:.2f} | {n} |" for c, o, n in tab]
    # 2. baseline B1
    out += ["", "## Baseline B1 — raw analyte value vs. Hemoglyph group probability (same stays)", "",
            "| group | n listed / not | B1 analyte (cut-off) | B1 AUROC | B1 sens/spec | Hemoglyph AUROC | Hemoglyph sens/spec @0.5 |", "|---|---|---|---|---|---|---|"]
    for g, (an, sign, cut) in B1.items():
        pos_b, neg_b, pos_h, neg_h = [], [], [], []
        for r in rows:
            if an not in r["vals"]:
                continue
            v = r["vals"][an] * sign; h = r["gp"].get(g, 0.0)
            (pos_b if g in r["coded"] else neg_b).append(v); (pos_h if g in r["coded"] else neg_h).append(h)
        if len(pos_b) < 5:
            continue
        y = np.array([1] * len(pos_b) + [0] * len(neg_b))
        au_b = auroc(y, np.array(pos_b + neg_b)); au_h = auroc(y, np.array(pos_h + neg_h))
        thr = cut * sign
        sb = sum(v >= thr for v in pos_b) if sign > 0 else sum(v > thr for v in pos_b)  # oriented
        spb = sum(v < thr for v in neg_b) if sign > 0 else sum(v <= thr for v in neg_b)
        sh = sum(h >= .5 for h in pos_h); sph = sum(h < .5 for h in neg_h)
        out.append(f"| {g} | {len(pos_b)} / {len(neg_b)} | {an} ({'>' if sign>0 else '<'}{cut}) | {au_b:.2f} | {100*sb/len(pos_b):.0f}% / {100*spb/max(1,len(neg_b)):.0f}% | {au_h:.2f} | {100*sh/len(pos_h):.0f}% / {100*sph/max(1,len(neg_h)):.0f}% |")
    # 3. safety
    out += ["", "## Safety S5 — critical values captured in top-5", "", "| critical value | n stays | entity in top-5 |", "|---|---|---|"]
    tot_n = tot_hit = 0
    for an, op, thr, ids in CRIT:
        n = hit = 0
        for r in rows:
            v = r["vals"].get(an)
            if v is None:
                continue
            if (op == ">=" and v >= thr) or (op == "<=" and v <= thr):
                n += 1; hit += any(d in ids for d, _ in r["top5"])
        if n:
            out.append(f"| {an} {op} {thr} | {n} | {fmt(hit, n)} |"); tot_n += n; tot_hit += hit
    out.append(f"| **all** | {tot_n} | {fmt(tot_hit, tot_n)} |")
    txt = "\n".join(out); print(txt)
    open(os.path.join(os.path.dirname(path), "calibration_baseline_safety.md"), "w").write(txt + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "eval", "results", "eicu_demo", "per_stay.json"))
