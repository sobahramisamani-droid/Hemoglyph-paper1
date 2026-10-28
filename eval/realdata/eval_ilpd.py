#!/usr/bin/env python3
"""Held-out evaluation: Indian Liver Patient Dataset (ILPD, UCI #225; Ramana et al.).

Pre-specified 2026-10-21, engine frozen before the run.  583 records from Andhra Pradesh:
416 liver patients, 167 non-patients; inputs age, sex, total/direct bilirubin (mg/dL),
ALP, ALT, AST (U/L), total protein, albumin (g/dL), A/G ratio.
Task L1: liver patient vs non-patient; score = max probability over liver-disease entities.
Known limitation of the source: "liver patient" is a clinic label, many with normal enzymes;
this dataset is therefore a *stress test for specificity-sensitivity trade-off*, not a gold
standard. Published supervised classifiers reach AUROC ≈ 0.70–0.76 on it.
"""
from __future__ import annotations
import os, sys, json, time, csv
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from eval_nhanes import auroc, boot_ci, fmt  # noqa: E402
OUT = os.path.join(ROOT, "eval", "results", "ilpd"); os.makedirs(OUT, exist_ok=True)

LIVER_WORDS = ("hepat", "liver", "cirrho", "cholesta", "biliary", "nafl", "steato", "jaundice", "hyperbilirubin",
               "alcoholic", "transamin", "aminotransferase", "wilson", "hemochromat", "gilbert", "budd", "portal")
NON_LIVER = ("hepatorenal",)


def is_liver(d):
    return any(w in d for w in LIVER_WORDS) and not any(w in d for w in NON_LIVER) and not d.startswith("co_")


def main():
    rows = list(csv.reader(open(os.path.join(HERE, "ilpd", "Indian Liver Patient Dataset (ILPD).csv"))))
    import logging; logging.disable(logging.CRITICAL)
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    recs = []; lat = []
    for r in rows:
        if len(r) < 11:
            continue
        try:
            age = int(float(r[0]))
        except ValueError:
            continue
        f = lambda x: float(x) if x not in ("", "NA") else None
        vals = {"total_bilirubin": (f(r[2]), "mg/dL"), "direct_bilirubin": (f(r[3]), "mg/dL"), "alkaline_phosphatase": (f(r[4]), "U/L"),
                "alanine_aminotransferase": (f(r[5]), "U/L"), "aspartate_aminotransferase": (f(r[6]), "U/L"),
                "total_protein": (f(r[7]), "g/dL"), "albumin": (f(r[8]), "g/dL")}
        obs = {k: {"value": v, "unit": u} for k, (v, u) in vals.items() if v is not None}
        patient = {"age_years": age, "sex_at_birth": "female" if r[1].strip().lower().startswith("f") else "male"}
        t1 = time.time(); rep = E.interpret(obs, None, patient).to_dict(); lat.append(time.time() - t1)
        dd = rep.get("differential_diagnosis", [])
        s = max([float(d["probability"]) for d in dd if is_liver(d["disease_id"])] or [0.0])
        recs.append({"y": 1 if r[10].strip() == "1" else 0, "score": s, "top3": [(d["disease_id"], round(float(d["probability"]), 3)) for d in dd[:3]]})
    y = np.array([r["y"] for r in recs]); s = np.array([r["score"] for r in recs])
    au = auroc(y, s); lo, hi = boot_ci(y, s)
    tp = int(((s >= .5) & (y == 1)).sum()); tn = int(((s < .5) & (y == 0)).sum())
    lines = ["# Hemoglyph — ILPD held-out evaluation", "",
             f"n = {len(recs)} ({int(y.sum())} liver patients / {int((y==0).sum())} non-patients); median latency {1000*np.median(lat):.0f} ms.", "",
             "| Task | AUROC (95% CI) | sens @0.5 | spec @0.5 |", "|---|---|---|---|",
             f"| L1 liver patient vs non-patient | **{au:.3f}** ({lo:.3f}–{hi:.3f}) | {fmt(tp, int(y.sum()))} | {fmt(tn, int((y==0).sum()))} |", "",
             "Reference: published supervised models on ILPD report AUROC ≈ 0.70–0.76 (trained on the data); Hemoglyph is untrained."]
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines) + "\n")
    json.dump({"n": len(recs), "auroc": au, "ci": [lo, hi], "sens": tp / max(1, int(y.sum())), "spec": tn / max(1, int((y == 0).sum()))}, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    json.dump(recs, open(os.path.join(OUT, "per_record.json"), "w"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
