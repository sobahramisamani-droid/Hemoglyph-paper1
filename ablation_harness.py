"""Layer-ablation harness for the Hemoglyph decision-fusion engine.

For every case in the case set the engine is run with the full ensemble
and with each reasoning layer switched off (HEMOGLYPH_DISABLE_LAYERS).
The rank of the expected diagnosis and the top-ranked disease are
reported per configuration.

HONEST SCOPE: the bundled cases are *synthetic textbook presentations*,
not patient data. This harness measures layer CONTRIBUTION and
regression safety; it is NOT a clinical validation and yields no
sensitivity/specificity claim. Replace `CASES` (or pass --cases file.json)
with physician-adjudicated local cases to turn it into one.

Usage:
    python ablation_harness.py
    python ablation_harness.py --cases my_cases.json --region IR
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

LAYERS = ["rule_engine", "bayesian", "fuzzy", "knowledge_graph"]

CASES = [
    {
        "name": "Beta-thalassaemia trait (Mentzer < 13, normal ferritin)",
        "expect": "thalassemia_trait",
        "patient": {"age_years": 30, "sex_at_birth": "female"},
        "inputs": {
            "hemoglobin": {"value": 9.1, "unit": "g/dL"},
            "mean_corpuscular_volume": {"value": 64, "unit": "fL"},
            "red_blood_cell_count": {"value": 5.9, "unit": "10^6/uL"},
            "red_cell_distribution_width": {"value": 13.2, "unit": "%"},
            "ferritin": {"value": 95, "unit": "ng/mL"},
        },
    },
    {
        "name": "Iron-deficiency anaemia (classic panel)",
        "expect": "iron_deficiency_anemia",
        "patient": {"age_years": 30, "sex_at_birth": "female"},
        "inputs": {
            "hemoglobin": {"value": 9.5, "unit": "g/dL"},
            "mean_corpuscular_volume": {"value": 70, "unit": "fL"},
            "red_blood_cell_count": {"value": 3.9, "unit": "10^6/uL"},
            "red_cell_distribution_width": {"value": 18.5, "unit": "%"},
            "ferritin": {"value": 6, "unit": "ng/mL"},
            "transferrin_saturation": {"value": 8, "unit": "%"},
        },
    },
    {
        "name": "Iron-deficiency anaemia, ferritin read at OCR confidence 0.55",
        "expect": "iron_deficiency_anemia",
        "patient": {"age_years": 30, "sex_at_birth": "female"},
        "inputs": {
            "hemoglobin": {"value": 9.5, "unit": "g/dL"},
            "mean_corpuscular_volume": {"value": 70, "unit": "fL"},
            "red_cell_distribution_width": {"value": 18.5, "unit": "%"},
            "ferritin": {"value": 6, "unit": "ng/mL",
                         "metadata": {"ocr_confidence": 0.55}},
            "transferrin_saturation": {"value": 8, "unit": "%"},
        },
    },
    {
        "name": "Overt hypothyroidism",
        "expect": "primary_hypothyroidism",
        "alt_expect": ["hypothyroidism", "overt_hypothyroidism"],
        "patient": {"age_years": 45, "sex_at_birth": "female"},
        "inputs": {
            "thyroid_stimulating_hormone": {"value": 18.5, "unit": "mIU/L"},
            "free_thyroxine": {"value": 0.6, "unit": "ng/dL"},
        },
    },
    {
        "name": "Hyperkalaemia with AKI pattern",
        "expect": "hyperkalemia",
        "alt_expect": ["acute_kidney_injury"],
        "patient": {"age_years": 68, "sex_at_birth": "male"},
        "inputs": {
            "potassium": {"value": 6.4, "unit": "mmol/L"},
            "creatinine": {"value": 3.1, "unit": "mg/dL"},
            "urea": {"value": 95, "unit": "mg/dL"},
            "bicarbonate": {"value": 17, "unit": "mmol/L"},
        },
    },
    {
        "name": "Type 2 diabetes (ADA: FPG >= 126 and HbA1c >= 6.5)",
        "expect": "type_2_diabetes_mellitus",
        "alt_expect": ["diabetes_mellitus"],
        "patient": {"age_years": 55, "sex_at_birth": "male"},
        "inputs": {
            "fasting_plasma_glucose": {"value": 141, "unit": "mg/dL"},
            "hba1c": {"value": 7.2, "unit": "%"},
            "triglycerides": {"value": 210, "unit": "mg/dL"},
        },
    },
    {
        "name": "Hepatocellular injury, ALT 3x ULN with local lab interval",
        "expect": "hepatocellular_injury_pattern",
        "alt_expect": ["nafl_d", "autoimmune_hepatitis", "drug_induced_liver_injury",
                       "acute_hepatitis", "viral_hepatitis"],
        "patient": {"age_years": 35, "sex_at_birth": "male"},
        "inputs": {
            "alanine_aminotransferase": {"value": 165, "unit": "U/L",
                                         "reported_reference": {"low": 7, "high": 55}},
            "aspartate_aminotransferase": {"value": 120, "unit": "U/L",
                                           "reported_reference": {"low": 8, "high": 48}},
            "alkaline_phosphatase": {"value": 90, "unit": "U/L",
                                     "reported_reference": {"low": 40, "high": 130}},
            "bilirubin_total": {"value": 1.1, "unit": "mg/dL"},
        },
    },
]


def _rank_of(diff, expect, alts):
    targets = [expect] + list(alts or [])
    for d in diff:
        if d["disease_id"] in targets:
            return d["rank"], d
    return None, None


def run(cases, region=None, top=3):
    import analyse_gidlines as ag
    engine = ag.ClinicalRuleEngine()
    configs = [("FULL", "")] + [(f"-{l}", l) for l in LAYERS]
    print(f"{'case':<62} " + " ".join(f"{c[0]:>16}" for c in configs))
    print("-" * (63 + 17 * len(configs)))
    summary = {c[0]: [] for c in configs}
    for case in cases:
        row = []
        patient = dict(case["patient"])
        if region:
            patient["region"] = region
        for label, disabled in configs:
            os.environ["HEMOGLYPH_DISABLE_LAYERS"] = disabled
            t = time.time()
            rep = engine.interpret(case["inputs"], patient=patient)
            ms = (time.time() - t) * 1000
            diff = rep.to_dict()["differential_diagnosis"]
            rank, hit = _rank_of(diff, case["expect"], case.get("alt_expect"))
            summary[label].append(rank)
            if rank is None:
                cell = f"miss ({ms:.0f}ms)"
            else:
                cell = f"#{rank} p={hit['probability']:.2f} {hit['evidence_state'][:4]}"
            row.append(f"{cell:>16}")
        print(f"{case['name'][:61]:<62} " + " ".join(row))
    os.environ.pop("HEMOGLYPH_DISABLE_LAYERS", None)
    print("\nMean rank of expected diagnosis (missing counted as 10):")
    for label, ranks in summary.items():
        vals = [r if r is not None else 10 for r in ranks]
        top1 = sum(1 for r in ranks if r == 1)
        print(f"  {label:<18} mean rank {sum(vals)/len(vals):.2f}   top-1 {top1}/{len(ranks)}")
    print("\nNOTE: synthetic textbook cases - contribution analysis only, "
          "not clinical validation.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", help="JSON file with a list of cases")
    ap.add_argument("--region", help="Regional prior profile, e.g. IR")
    a = ap.parse_args()
    cases = CASES
    if a.cases:
        with open(a.cases, encoding="utf-8") as fh:
            cases = json.load(fh)
    run(cases, region=a.region)
