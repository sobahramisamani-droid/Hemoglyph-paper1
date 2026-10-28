#!/usr/bin/env python3
"""SAP Amendment 15, secondary metric: recall restricted to PANEL-SUPPORTED labels.

An eICU clinician diagnosis string is admission-level; it is often coded from values measured later in the stay or
before the first panel (treated hypokalaemia, hypocalcaemia coded on total calcium with albumin 1.9, pancreatitis with
lipase < 3x ULN). A labs-only engine cannot be expected to recover those. For each label group with a single
guideline-definable laboratory criterion, the label counts only when the criterion is met IN THE INPUT PANEL.
Thresholds are the guideline definitions already used by the engine's syndrome layer (fixed before this script was
run on any file); groups without such a criterion (sepsis, cirrhosis, GI bleeding, malnutrition, alcohol withdrawal)
are excluded from this metric and are reported only under the flat metric.
Usage: python3 eval/realdata/panel_supported_metric.py per_stay_A.json[.gz] [per_stay_B.json[.gz]]
"""
import gzip, json, sys
def ca_c(v):
    ca, alb = v.get("calcium_total"), v.get("albumin")
    return None if ca is None else (ca + 0.8 * (4.0 - alb) if alb is not None else ca)
def egfr_low(v, r):
    cr = v.get("creatinine")
    if cr is None: return None
    f = str(r.get("sex", "")).startswith("f")
    return cr > (1.0 if f else 1.2)  # KDIGO: eGFR < 60 roughly at Cr > 1.0 (F) / 1.2 (M) for adults; conservative
CRIT = {  # group -> function(vals, row) -> True (supported) / False (not) / None (analyte missing)
    "hypokalemia": lambda v, r: None if v.get("potassium") is None else v["potassium"] < 3.5,
    "hyperkalemia": lambda v, r: None if v.get("potassium") is None else v["potassium"] > 5.0,
    "hyponatremia": lambda v, r: None if v.get("sodium") is None else v["sodium"] < 135,
    "hypernatremia": lambda v, r: None if v.get("sodium") is None else v["sodium"] > 145,
    "hypomagnesemia": lambda v, r: None if v.get("magnesium") is None else v["magnesium"] < 1.7,
    "hypocalcemia": lambda v, r: (None if v.get("calcium_ionized") is None else v["calcium_ionized"] < 1.12) if v.get("calcium_ionized") is not None else (None if ca_c(v) is None else ca_c(v) < 8.5),
    "hypercalcemia": lambda v, r: None if ca_c(v) is None else ca_c(v) > 10.5,
    "hypophosphatemia": lambda v, r: None if v.get("phosphate") is None else v["phosphate"] < 2.5,
    "metabolic_acidosis": lambda v, r: None if v.get("bicarbonate") is None else v["bicarbonate"] < 22,
    "lactic_acidosis": lambda v, r: None if v.get("lactate") is None else v["lactate"] > 2.0,
    "anemia": lambda v, r: None if v.get("hemoglobin") is None else v["hemoglobin"] < (12.0 if str(r.get("sex", "")).startswith("f") else 13.0),
    "thrombocytopenia": lambda v, r: None if v.get("platelet_count") is None else v["platelet_count"] < 150,
    "leukocytosis": lambda v, r: None if v.get("white_blood_cell_count") is None else v["white_blood_cell_count"] > 11,
    "acute_kidney_injury": egfr_low, "chronic_kidney_disease": egfr_low, "renal_impairment": egfr_low,
    "diabetes": lambda v, r: True if (v.get("hemoglobin_a1c") or 0) >= 6.5 else (None if v.get("glucose") is None else v["glucose"] >= 200),
    "hyperglycemia": lambda v, r: None if v.get("glucose") is None else v["glucose"] >= 140,
    "diabetic_ketoacidosis": lambda v, r: None if v.get("glucose") is None or v.get("bicarbonate") is None else (v["glucose"] > 250 and v["bicarbonate"] < 18),
    "hypoglycemia": lambda v, r: None if v.get("glucose") is None else v["glucose"] < 70,
    "hypothyroidism": lambda v, r: None if v.get("thyroid_stimulating_hormone") is None else v["thyroid_stimulating_hormone"] > 4.5,
    "acute_pancreatitis": lambda v, r: None if v.get("lipase") is None else v["lipase"] >= 180,
    "acute_myocardial_infarction": lambda v, r: None if v.get("troponin_i") is None and v.get("troponin_t") is None else ((v.get("troponin_i") or 0) > 0.04 or (v.get("troponin_t") or 0) > 0.014),
    "heart_failure": lambda v, r: None if v.get("b_type_natriuretic_peptide") is None and v.get("nt_pro_bnp") is None else ((v.get("b_type_natriuretic_peptide") or 0) > 100 or (v.get("nt_pro_bnp") or 0) > 300),
    "rhabdomyolysis": lambda v, r: None if v.get("creatine_kinase_total") is None else v["creatine_kinase_total"] > 1000,
    "coagulopathy": lambda v, r: None if v.get("inr") is None else v["inr"] > 1.5,
}
def load(p):
    return {str(r["stay"]): r for r in json.load(gzip.open(p) if p.endswith(".gz") else open(p))}
def score(rows, key="gr"):
    out = {k: [0, 0] for k in (1, 3, 5, 10)}; excluded = unsupported = missing = 0
    for r in rows:
        for g in r["coded"]:
            f = CRIT.get(g)
            if f is None: excluded += 1; continue
            s = f(r["vals"], r)
            if s is None: missing += 1; continue
            if not s: unsupported += 1; continue
            rk = r[key].get(g, 999)
            for k in out: out[k][1] += 1; out[k][0] += int(rk <= k)
    return out, excluded, unsupported, missing
if __name__ == "__main__":
    files = [load(p) for p in sys.argv[1:]]; common = sorted(set.intersection(*[set(f) for f in files]))
    print("stays", len(common))
    for p, F in zip(sys.argv[1:], files):
        for key, nm in (("gr", "flat"), ("gr2", "two-tier")):
            out, ex, un, mi = score([F[s] for s in common], key)
            print(p.split("/")[-1], nm, " ".join(f"@{k} {100*h/n:5.1f}" for k, (h, n) in out.items()), f"(n={out[5][1]}; excluded-group {ex}, analyte missing {mi}, not supported by panel {un})")
