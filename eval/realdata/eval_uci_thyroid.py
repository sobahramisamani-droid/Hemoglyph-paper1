#!/usr/bin/env python3
"""Held-out evaluation: UCI Thyroid Disease (Garavan Institute / Quinlan 1987, thyroid0387).

Pre-specified 2026-10-21, engine frozen before the run.
Records: 9,172 with clinician-assigned diagnosis letters.  Inputs available: TSH (mU/L),
T3 (nmol/L), TT4 (nmol/L), T4U, FTI, TBG; plus age/sex, pregnancy, thyroxine / antithyroid
medication flags.  FTI/T4U are index values without a registry feature and are not given.

Tasks (records with TSH measured, excluding "discordant assay" R and TBG-related I/J/S):
  H1  hypothyroid (E, F, G, H)        vs  "-" (no comment)
  H2  hyperthyroid (A, B, C, D)       vs  "-"
  H3  primary/overt hypothyroid (F)   vs  "-"
  H4  compensated/subclinical (G)     vs  "-"
Score = max probability in the task's entity group (ranked list, 40 entries).
Patients on thyroxine (letters L/M/N or flag) are kept in the negative set only when
labelled "-"; the thyroxine flag is passed to the engine as a medication.
"""
from __future__ import annotations
import os, sys, json, time, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from eval_nhanes import auroc, boot_ci, fmt  # noqa: E402
OUT = os.path.join(ROOT, "eval", "results", "uci_thyroid"); os.makedirs(OUT, exist_ok=True)

HYPO = lambda d: ("hypothyroid" in d) or d.startswith("hashimoto") or d in ("autoimmune_thyroid_disease",)
HYPER = lambda d: ("hyperthyroid" in d) or ("graves" in d) or ("thyrotoxic" in d) or d.startswith("toxic_") or ("thyroid_storm" in d)


def main():
    rows = []
    for line in open(os.path.join(HERE, "uci_thyroid", "thyroid0387.data")):
        parts = line.strip().split(",")
        if len(parts) < 30:
            continue
        dx = parts[29].split("[")[0]
        rows.append((parts, dx))
    import logging; logging.disable(logging.CRITICAL)
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    recs = []; lat = []; t0 = time.time()
    for i, (p, dx) in enumerate(rows):
        if p[16] != "t" or p[17] in ("?", ""):
            continue
        if any(ch in dx for ch in "RIJS"):
            continue
        obs = {"thyroid_stimulating_hormone": {"value": float(p[17]), "unit": "mIU/L"}}
        if p[18] == "t" and p[19] not in ("?", ""):
            obs["total_triiodothyronine"] = {"value": float(p[19]), "unit": "nmol/L"}
        if p[20] == "t" and p[21] not in ("?", ""):
            obs["total_thyroxine"] = {"value": float(p[21]), "unit": "nmol/L"}
        if p[26] == "t" and p[27] not in ("?", ""):
            obs["thyroxine_binding_globulin_serum"] = {"value": float(p[27]), "unit": "mg/L"}
        age = int(float(p[0])) if p[0] not in ("?", "") else 50
        if age > 110:
            age = 50
        patient = {"age_years": age, "sex_at_birth": "female" if p[1] == "F" else "male"}
        meds = []
        if p[2] == "t":
            meds.append("levothyroxine")
        if p[4] == "t":
            meds.append("methimazole")
        if p[11] == "t":
            meds.append("lithium")
        if meds:
            patient["medications"] = meds
        if p[6] == "t":
            patient["pregnant"] = True
        t1 = time.time()
        rep = E.interpret(obs, None, patient).to_dict(); lat.append(time.time() - t1)
        dd = rep.get("differential_diagnosis", [])
        hypo = max([float(d["probability"]) for d in dd if HYPO(d["disease_id"])] or [0.0])
        hyper = max([float(d["probability"]) for d in dd if HYPER(d["disease_id"])] or [0.0])
        # SAP amendment 4 (2026-10-22): overt-only mapping - subclinical hyperthyroidism (low TSH, normal FT4/T3) is a
        # biochemical state the dataset never labels (classes A-D are overt); reported as an additional row, H2 unchanged.
        hyper_overt = max([float(d["probability"]) for d in dd if HYPER(d["disease_id"]) and not d["disease_id"].startswith("subclinical")] or [0.0])
        recs.append({"dx": dx, "hypo": hypo, "hyper": hyper, "hyper_overt": hyper_overt, "tsh": float(p[17]), "n_in": len(obs),
                     "top3": [(d["disease_id"], round(float(d["probability"]), 3)) for d in dd[:3]], "on_t4": p[2] == "t"})
        if len(recs) % 500 == 0:
            print(f"  {len(recs)} evaluated  {time.time()-t0:.0f}s", flush=True)
    neg = [r for r in recs if r["dx"] == "-"]
    tasks = {
        "H1 hypothyroid (E/F/G/H) vs no-comment": ([r for r in recs if any(c in r["dx"] for c in "EFGH")], neg, "hypo"),
        "H2 hyperthyroid (A/B/C/D) vs no-comment": ([r for r in recs if any(c in r["dx"] for c in "ABCD")], neg, "hyper"),
        "H3 primary hypothyroid (F) vs no-comment": ([r for r in recs if "F" in r["dx"]], neg, "hypo"),
        "H4 compensated hypothyroid (G) vs no-comment": ([r for r in recs if "G" in r["dx"]], neg, "hypo"),
        "H2b hyperthyroid vs no-comment, not on thyroxine": ([r for r in recs if any(c in r["dx"] for c in "ABCD") and not r["on_t4"]], [r for r in neg if not r["on_t4"]], "hyper"),
        "H2c hyperthyroid (A/B/C/D) vs no-comment, overt entities only (amendment 4)": ([r for r in recs if any(c in r["dx"] for c in "ABCD")], neg, "hyper_overt"),
    }
    lines = ["# Hemoglyph — UCI Thyroid (thyroid0387) held-out evaluation", "",
             f"Records with TSH measured and non-TBG/non-discordant labels: {len(recs)}; no-comment controls: {len(neg)}; "
             f"median latency {1000*np.median(lat):.0f} ms.", "",
             "| Task | n pos / n neg | AUROC (95% CI) | sens @0.5 | spec @0.5 |", "|---|---|---|---|---|"]
    summ = {}
    for name, (pos, ng, key) in tasks.items():
        y = np.array([1] * len(pos) + [0] * len(ng)); s = np.array([r[key] for r in pos] + [r[key] for r in ng])
        au = auroc(y, s); lo, hi = boot_ci(y, s, n=1000)
        tp = int((s[: len(pos)] >= .5).sum()); tn = int((s[len(pos):] < .5).sum())
        lines.append(f"| {name} | {len(pos)} / {len(ng)} | **{au:.3f}** ({lo:.3f}–{hi:.3f}) | {fmt(tp, len(pos))} | {fmt(tn, len(ng))} |")
        summ[name] = {"n_pos": len(pos), "n_neg": len(ng), "auroc": au, "ci": [lo, hi], "sens": tp / max(1, len(pos)), "spec": tn / max(1, len(ng))}
    from collections import Counter
    c = Counter(r["top3"][0][0] if r["top3"] else None for r in neg)
    lines += ["", "Most frequent top-1 in no-comment controls: " + ", ".join(f"{a} ({b})" for a, b in c.most_common(8)),
              "", "Note: the 'no comment' class includes patients on thyroxine replacement with abnormal TSH; the engine is not told the "
              "clinician's judgement that replacement is adequate, so part of the false-positive rate reflects label semantics."]
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines) + "\n")
    json.dump(summ, open(os.path.join(OUT, "summary.json"), "w"), indent=1); json.dump(recs, open(os.path.join(OUT, "per_record.json"), "w"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
