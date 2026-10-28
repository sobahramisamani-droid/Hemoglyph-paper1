# -*- coding: utf-8 -*-
"""
Held-out real-patient evaluation: PhysioNet/Computing in Cardiology Challenge 2019 (Reyna MA et al., Crit Care Med 2020;
open access, ODC-By 1.0).  Hospital-A training set, every 4th record (n≈5000 ICU patients, hourly rows).

PRE-SPECIFIED analysis (written 2026-10-23 before the engine was run on this file; the engine is NOT modified after
seeing any result from this dataset):
  Input   per patient: the LAST available value of each laboratory analyte within ICU hours 1–24 (ICULOS <= 24),
          plus age/sex; vital signs are passed only as body temperature (Temp) — no HR/BP/Resp (Hemoglyph is a
          laboratory interpreter).  Patients with < 3 laboratory analytes in the first 24 h are excluded (reported).
  Label   SepsisLabel == 1 at any hour of the whole stay (Sepsis-3 onset, label shifted 6 h early by the challenge).
          NOTE: this is a PREDICTION task (labs of the first 24 h vs onset at any later time), harder than the
          eICU diagnosis task; results are reported as such.
  Score   sepsis group probability = max probability over differential entries whose id is in the eICU 'sepsis'
          group set (eval_eicu.GROUPS['sepsis'][1]) — identical to the eICU definition.
  Metrics AUROC (bootstrap 2000, seed 20261023); recall@5 of the sepsis group among sepsis patients; flag rate
          (sepsis group in top-5) among non-sepsis patients; sensitivity/specificity at p>=0.5.
  Baseline logistic regression (sklearn, default L2) on the same first-24-h features (WBC, lactate, temperature,
          platelets, creatinine, bilirubin, HCO3, BUN, glucose, age) with median imputation + missing indicators,
          5-fold cross-validated AUROC on the same patients — an honest, cheap supervised comparator.
  Secondary (descriptive) distribution of top-1 disease ids in sepsis vs non-sepsis patients.
Usage: python3 eval/realdata/eval_sepsis2019.py [--n-max N]
"""
from __future__ import annotations
import os, sys, json, math, time, random, logging, collections, argparse
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); os.chdir(ROOT); logging.disable(logging.CRITICAL)
SRC = "eval/realdata/sepsis2019/training_setA_sub5000.csv.gz"; OUT = "eval/results/sepsis2019"; os.makedirs(OUT, exist_ok=True)

LAB = {"BaseExcess": ("base_excess", "mmol/L"), "HCO3": ("bicarbonate", "mmol/L"), "pH": ("arterial_ph", "1"), "PaCO2": ("arterial_pco2", "mmHg"),
       "SaO2": ("oxygen_saturation_arterial", "%"), "AST": ("aspartate_aminotransferase", "U/L"), "BUN": ("blood_urea_nitrogen", "mg/dL"),
       "Alkalinephos": ("alkaline_phosphatase", "U/L"), "Calcium": ("calcium_total", "mg/dL"), "Chloride": ("chloride", "mmol/L"),
       "Creatinine": ("creatinine", "mg/dL"), "Bilirubin_direct": ("direct_bilirubin", "mg/dL"), "Glucose": ("glucose", "mg/dL"),
       "Lactate": ("lactate", "mmol/L"), "Magnesium": ("magnesium", "mg/dL"), "Phosphate": ("phosphate", "mg/dL"), "Potassium": ("potassium", "mmol/L"),
       "Bilirubin_total": ("total_bilirubin", "mg/dL"), "TroponinI": ("troponin_i", "ng/mL"), "Hct": ("hematocrit", "%"), "Hgb": ("hemoglobin", "g/dL"),
       "PTT": ("activated_partial_thromboplastin_time", "s"), "WBC": ("white_blood_cell_count", "10*3/uL"), "Fibrinogen": ("fibrinogen", "mg/dL"),
       "Platelets": ("platelet_count", "10*3/uL"), "Temp": ("body_temperature", "Cel")}
BASE_FEATS = ["WBC", "Lactate", "Temp", "Platelets", "Creatinine", "Bilirubin_total", "HCO3", "BUN", "Glucose"]

def wilson(k, n, z=1.96):
    if n == 0: return float("nan"), float("nan"), float("nan")
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d
def pct(k, n):
    p, lo, hi = wilson(k, n); return f"{100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f}; {k}/{n})"
def auroc(pos, neg):
    if not len(pos) or not len(neg): return float("nan")
    pts = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg]); n = len(pts); ranks = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and pts[j + 1][0] == pts[i][0]: j += 1
        for k in range(i, j + 1): ranks[k] = (i + j) / 2 + 1
        i = j + 1
    rpos = sum(r for r, (s, y) in zip(ranks, pts) if y == 1)
    return (rpos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
def boot_auc(pos, neg, B=2000, seed=20261023):
    rng = random.Random(seed); vals = []
    for _ in range(B): vals.append(auroc([rng.choice(pos) for _ in pos], [rng.choice(neg) for _ in neg]))
    vals.sort(); return vals[int(0.025 * B)], vals[int(0.975 * B)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n-max", type=int, default=100000); ap.add_argument("--encounter", default=None); ap.add_argument("--suffix", default=""); ap.add_argument("--data", default=None); ap.add_argument("--registry", default=None, help="disease registry path (control arm)"); a = ap.parse_args()
    src = a.data or SRC; sfx = a.suffix
    import analyse_gidlines as ag, eval_eicu as ee
    SEP_IDS = ee.GROUPS["sepsis"][1]
    E = ag.ClinicalRuleEngine(disease_registry_path=a.registry) if a.registry else ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    print("registry:", getattr(E.registry, "metadata", {}).get("version"), flush=True)
    df = pd.read_csv(src)
    lab = df[df.ICULOS <= 24].sort_values(["pid", "ICULOS"])
    last = lab.groupby("pid")[[c for c in LAB if c in lab.columns]].last()
    demo = df.groupby("pid").agg(Age=("Age", "first"), Gender=("Gender", "first"), y=("SepsisLabel", "max"), hours=("ICULOS", "max"))
    tab = demo.join(last, how="left")
    n_all = len(tab)
    nlab = tab[[c for c in LAB if c != "Temp" and c in tab.columns]].notna().sum(axis=1)
    tab = tab[nlab >= 3].copy(); n_el = len(tab)
    if len(tab) > a.n_max: tab = tab.sample(a.n_max, random_state=20261023)
    res = []; t0 = time.time()
    _ckpt = f"{OUT}/per_patient{sfx}.partial.json"
    _done = {x["pid"]: x for x in json.load(open(_ckpt))} if os.path.exists(_ckpt) else {}
    if _done: print(f"  resume: {len(_done)} patients from checkpoint", flush=True)
    for n, (pid, r) in enumerate(tab.iterrows()):
        if int(pid) in _done:
            res.append(_done[int(pid)]); continue
        obs = {fid: {"value": float(r[c]), "unit": u} for c, (fid, u) in LAB.items() if c in tab.columns and pd.notna(r[c])}
        pt = {"age_years": int(min(max(r.Age, 18), 100)), "sex_at_birth": "male" if r.Gender == 1 else "female"}
        if a.encounter: pt["encounter"] = a.encounter
        t1 = time.perf_counter()
        try:
            rep = E.interpret(obs, None, pt).to_dict(); diff = rep["differential_diagnosis"]
        except Exception as ex:
            diff = []; 
        sp = 0.0; rank = None
        for d in diff:
            if d["disease_id"] in SEP_IDS:
                sp = max(sp, float(d["probability"]))
                if rank is None: rank = int(d["rank"])
        res.append(dict(pid=int(pid), y=int(r.y), n_labs=int(nlab.loc[pid]), sp=round(sp, 4), rank=rank,
                        top3=[(d["disease_id"], round(float(d["probability"]), 3)) for d in diff[:3]], ms=round((time.perf_counter() - t1) * 1000)))
        if (n + 1) % 50 == 0: json.dump(res, open(_ckpt, "w"))
        if (n + 1) % 200 == 0: print(f"  {n+1}/{len(tab)} {time.time()-t0:.0f}s", flush=True)
    json.dump(res, open(f"{OUT}/per_patient{sfx}.json", "w"))
    if os.path.exists(_ckpt): os.remove(_ckpt)
    pos = [x["sp"] for x in res if x["y"]]; neg = [x["sp"] for x in res if not x["y"]]
    auc = auroc(pos, neg); lo, hi = boot_auc(pos, neg)
    r5p = sum(1 for x in res if x["y"] and x["rank"] and x["rank"] <= 5); r5n = sum(1 for x in res if not x["y"] and x["rank"] and x["rank"] <= 5)
    se = sum(1 for s in pos if s >= 0.5); spc = sum(1 for s in neg if s < 0.5)
    # supervised baseline on the same patients
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_predict, StratifiedKFold
        X = tab[BASE_FEATS + ["Age"]].copy()
        for c in BASE_FEATS: X[c + "_miss"] = X[c].isna().astype(int)
        X = X.fillna(X.median())
        yb = tab.y.values
        pr = cross_val_predict(LogisticRegression(max_iter=2000), X.values, yb, cv=StratifiedKFold(5, shuffle=True, random_state=20261023), method="predict_proba")[:, 1]
        auc_b = auroc(list(pr[yb == 1]), list(pr[yb == 0])); blo, bhi = boot_auc(list(pr[yb == 1]), list(pr[yb == 0]))
        base_txt = f"{auc_b:.3f} ({blo:.3f}–{bhi:.3f})"
    except Exception as ex:
        base_txt = f"n/a ({ex})"
    top_pos = collections.Counter(x["top3"][0][0] for x in res if x["y"] and x["top3"]).most_common(8)
    top_neg = collections.Counter(x["top3"][0][0] for x in res if not x["y"] and x["top3"]).most_common(8)
    ms = sorted(x["ms"] for x in res)
    L = ["# Hemoglyph — PhysioNet/CinC Challenge 2019 (hospital A subsample) held-out evaluation", "",
         f"patients in file {n_all}; with >=3 lab analytes in ICU h 1–24: {n_el}; evaluated {len(res)}; sepsis (Sepsis-3, any hour) {len(pos)} ({100*len(pos)/len(res):.1f}%)", "",
         "Task: PREDICTION of Sepsis-3 onset at any time during the ICU stay from the laboratory values of the first 24 h (labs only + temperature). "
         "This is deliberately harder than the eICU diagnosis task; labels are not visible to the engine.", "",
         "| metric | value |", "|---|---|",
         f"| AUROC sepsis-group probability (labs first 24 h) | {auc:.3f} ({lo:.3f}–{hi:.3f}) |",
         f"| Supervised logistic baseline, 5-fold CV, same patients/features | {base_txt} |",
         f"| recall@5 of sepsis group among sepsis patients | {pct(r5p, len(pos))} |",
         f"| sepsis group in top-5 among NON-sepsis patients (flag rate) | {pct(r5n, len(neg))} |",
         f"| sensitivity at p>=0.5 | {pct(se, len(pos))} |", f"| specificity at p>=0.5 | {pct(spc, len(neg))} |",
         f"| latency ms median / p95 | {ms[len(ms)//2]} / {ms[int(0.95*len(ms))]} |", "",
         "Top-1 disease among sepsis patients: " + ", ".join(f"{k} {v}" for k, v in top_pos), "",
         "Top-1 disease among non-sepsis patients: " + ", ".join(f"{k} {v}" for k, v in top_neg), "",
         "Source: https://physionet.org/content/challenge-2019/1.0.0/ (Reyna et al. 2020). Subsample: every 4th file of training_setA; labs-only columns kept."]
    open(f"{OUT}/report{sfx}.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
