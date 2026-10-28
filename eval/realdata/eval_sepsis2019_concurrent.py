# -*- coding: utf-8 -*-
"""
PhysioNet/CinC 2019 — CONCURRENT-DIAGNOSIS analysis (SAP Amendment 13, 2026-10-24, POST-HOC).

Why this exists.  The pre-registered Sepsis-2019 analysis (eval_sepsis2019.py) asks the engine to PREDICT a later
Sepsis-3 onset from the first 24 h of laboratory values and gave AUROC 0.593 (supervised logistic 0.689).  That result
stands and is reported unchanged in Paper 1.  This script asks the question the engine was built for — does the
laboratory panel *around the time of onset* look like sepsis to the engine? — i.e. the same task type as the eICU
evaluation (recognition of a concurrent diagnosis), and additionally tests the optional vital-signs context.

Design (fixed before running; the engine and registry are NOT modified in response to any result):
  Cases     every sepsis patient (SepsisLabel == 1 at any hour).  t_L = first labelled hour (the challenge shifts the
            label 6 h before clinical onset, so clinical onset ≈ t_L + 6).  Window = ICULOS in [t_L, t_L + 12]
            (≈ onset − 6 h … onset + 6 h).  Last value of each analyte in the window.
  Controls  non-sepsis patients, seeded random subsample (n = 1,500, seed 20261024) to bound run time; each control
            gets a 12-h window whose start hour is drawn (same seed) from the empirical distribution of case t_L,
            clipped to that patient's stay, so that ICU dwell time is matched and does not leak the label.
  Inclusion ≥ 3 laboratory analytes in the window (temperature and vitals do not count).
  Arms      A  labs only (+ temperature, exactly as the pre-registered run)
            B  labs + vital signs (HR, SBP, MAP, respiratory rate, SpO2/SaO2, temperature) passed as observations
               and as patient context — the optional context module of the engine.
  Score     sepsis-group probability = max probability over differential ids in eval_eicu.GROUPS['sepsis'] (unchanged).
  Metrics   AUROC (bootstrap 2000), recall@5 among cases, flag rate among controls, sens/spec at 0.5; supervised
            logistic baseline per arm, 5-fold CV on the same windows/features.
  Reporting both arms AND the pre-registered prediction result in one table; labelled post-hoc / exploratory.
Usage: python3 eval/realdata/eval_sepsis2019_concurrent.py [--n-controls 1500]
"""
from __future__ import annotations
import os, sys, json, time, random, logging, collections, argparse
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); os.chdir(ROOT); logging.disable(logging.CRITICAL)
from eval_sepsis2019 import LAB, BASE_FEATS, SRC, wilson, pct, auroc, boot_auc
OUT = "eval/results/sepsis2019"; os.makedirs(OUT, exist_ok=True)
# v14 note: the Amendment-13 run passed blood pressure as UCUM "mm[Hg]", which the 13.3.0 unit normaliser did not map to mmHg,
# so SBP/MAP were silently dropped in arm B (HR/RR with "/min" were accepted). Fixed in calcu.normalize_unit (v6) and here.
VIT = {"HR": ("heart_rate", "beats/min"), "SBP": ("systolic_blood_pressure", "mmHg"), "MAP": ("mean_arterial_pressure", "mmHg"),
       "Resp": ("respiratory_rate", "breaths/min"), "O2Sat": ("oxygen_saturation", "%"), "SaO2": ("oxygen_saturation", "%")}
SEED = 20261024

def window_last(df_p, lo, hi, cols):
    w = df_p[(df_p.ICULOS >= lo) & (df_p.ICULOS <= hi)]
    return w[cols].ffill().iloc[-1] if len(w) else pd.Series({c: np.nan for c in cols})

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n-controls", type=int, default=1500)
    ap.add_argument("--registry", default=os.path.join(ROOT, "eval/frozen_registry_13_3_0/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"), help="Paper 1 is pinned to 13.3.0; the live file may be newer")
    ap.add_argument("--encounter", default="unknown", help="v14: ClinicalContext.encounter ('icu' — true for every record)")
    ap.add_argument("--suffix", default="", help="output suffix, e.g. _v1400")
    ap.add_argument("--data", default=None, help="alternative compacted file (e.g. quarantined set B after FREEZE_v14)")
    a = ap.parse_args()
    import analyse_gidlines as ag, eval_eicu as ee
    global OUT
    sfx = a.suffix
    SEP_IDS = ee.GROUPS["sepsis"][1]
    E = ag.ClinicalRuleEngine(disease_registry_path=a.registry); E._reasoner.max_differential = 40
    print("registry:", E.registry.metadata.get("version") if hasattr(E.registry, "metadata") else "?", flush=True)
    df = pd.read_csv(a.data or SRC).sort_values(["pid", "ICULOS"])
    labcols = [c for c in LAB if c in df.columns]; vitcols = [c for c in VIT if c in df.columns and c not in LAB]  # SaO2 is in both maps (v14 unit pass) — keep it once
    g = df.groupby("pid")
    demo = g.agg(Age=("Age", "first"), Gender=("Gender", "first"), y=("SepsisLabel", "max"), hours=("ICULOS", "max"))
    tL = df[df.SepsisLabel == 1].groupby("pid").ICULOS.min()
    cases = demo[demo.y == 1].copy(); cases["t0"] = tL.reindex(cases.index).values
    ctrl_all = demo[demo.y == 0]
    rng = random.Random(SEED)
    ctrl = ctrl_all.sample(min(a.n_controls, len(ctrl_all)), random_state=SEED).copy()
    starts = [int(x) for x in cases.t0.values]
    ctrl["t0"] = [min(rng.choice(starts), max(int(h) - 1, 1)) for h in ctrl.hours.values]
    tab = pd.concat([cases, ctrl]); tab["y"] = tab["y"].astype(int)
    rows = []
    for pid, r in tab.iterrows():
        dp = g.get_group(pid); last = window_last(dp, r.t0, r.t0 + 12, labcols + vitcols)
        rows.append(dict(pid=int(pid), y=int(r.y), t0=int(r.t0), Age=r.Age, Gender=r.Gender, **{c: last[c] for c in labcols + vitcols}))
    T = pd.DataFrame(rows).set_index("pid")
    nlab = T[[c for c in labcols if c != "Temp"]].notna().sum(axis=1); n_before = len(T); T = T[nlab >= 3].copy()
    print(f"cases {int(T.y.sum())} / controls {int((T.y==0).sum())} after >=3-lab filter (from {n_before})", flush=True)
    ck = f"{OUT}/concurrent{sfx}.partial.json"; done = {x["pid"]: x for x in json.load(open(ck))} if os.path.exists(ck) else {}
    res = []; t0 = time.time()
    for n, (pid, r) in enumerate(T.iterrows()):
        if int(pid) in done: res.append(done[int(pid)]); continue
        obs = {fid: {"value": float(r[c]), "unit": u} for c, (fid, u) in LAB.items() if c in T.columns and pd.notna(r[c])}
        pt = {"age_years": int(min(max(r.Age, 18), 100)), "sex_at_birth": "male" if r.Gender == 1 else "female"}
        if a.encounter != "unknown": pt["encounter"] = a.encounter
        out = dict(pid=int(pid), y=int(r.y), t0=int(r.t0), n_labs=int(sum(1 for c in labcols if c != "Temp" and pd.notna(r[c]))),
                   # v14 `not_assessable`: none of the sepsis anchor analytes (lactate, WBC) measured in the window
                   anchor_labs=int(sum(1 for c in ("Lactate", "WBC") if c in T.columns and pd.notna(r[c]))))
        for arm in ("A", "B"):
            o = dict(obs); p = dict(pt)
            if arm == "B":
                for c, (fid, u) in VIT.items():
                    if c in T.columns and pd.notna(r[c]): o[fid] = {"value": float(r[c]), "unit": u}
                if pd.notna(r.get("HR", np.nan)): p["heart_rate"] = float(r.HR)
                if pd.notna(r.get("SBP", np.nan)): p["systolic_bp"] = float(r.SBP)
            try:
                diff = E.interpret(o, None, p).to_dict()["differential_diagnosis"]
            except Exception:
                diff = []
            sp = 0.0; rank = None
            for d in diff:
                if d["disease_id"] in SEP_IDS:
                    sp = max(sp, float(d["probability"]))
                    if rank is None: rank = int(d["rank"])
            out[f"sp_{arm}"] = round(sp, 4); out[f"rank_{arm}"] = rank; out[f"top3_{arm}"] = [(d["disease_id"], round(float(d["probability"]), 3)) for d in diff[:3]]
        res.append(out)
        if (n + 1) % 50 == 0: json.dump(res, open(ck, "w"))
        if (n + 1) % 100 == 0: print(f"  {n+1}/{len(T)} {time.time()-t0:.0f}s", flush=True)
    json.dump(res, open(f"{OUT}/concurrent_per_patient{sfx}.json", "w"))
    if os.path.exists(ck): os.remove(ck)
    # baselines
    base = {}
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_predict, StratifiedKFold
        for arm, feats in (("A", BASE_FEATS), ("B", BASE_FEATS + vitcols)):
            X = T[feats + ["Age"]].copy()
            for c in feats: X[c + "_miss"] = X[c].isna().astype(int)
            X = X.fillna(X.median()); yb = T.y.values
            pr = cross_val_predict(LogisticRegression(max_iter=3000), X.values, yb, cv=StratifiedKFold(5, shuffle=True, random_state=SEED), method="predict_proba")[:, 1]
            ab = auroc(list(pr[yb == 1]), list(pr[yb == 0])); lo, hi = boot_auc(list(pr[yb == 1]), list(pr[yb == 0]))
            # v14: same model WITHOUT missing-value indicators — how much of the baseline is measurement pattern rather than values
            Xv = T[feats + ["Age"]].copy(); Xv = Xv.fillna(Xv.median())
            prv = cross_val_predict(LogisticRegression(max_iter=3000), Xv.values, yb, cv=StratifiedKFold(5, shuffle=True, random_state=SEED), method="predict_proba")[:, 1]
            abv = auroc(list(prv[yb == 1]), list(prv[yb == 0]))
            base[arm] = f"{ab:.3f} ({lo:.3f}–{hi:.3f}); values only, no missing-indicators: {abv:.3f}"
    except Exception as ex:
        base = {"A": f"n/a ({ex})", "B": "n/a"}
    pre = json.load(open(f"{OUT}/per_patient.json")) if os.path.exists(f"{OUT}/per_patient.json") else None
    L = ["# Hemoglyph — Sepsis-2019 CONCURRENT-diagnosis analysis (SAP Amendment 13; post-hoc, exploratory)", "",
         f"Cases: all sepsis patients, window ICULOS [t_L, t_L+12] ≈ onset −6…+6 h; controls: {a.n_controls} seeded non-sepsis patients with dwell-time-matched 12-h windows; ≥3 labs required. "
         f"Analysed: cases {int(T.y.sum())}, controls {int((T.y==0).sum())}. Pre-registered PREDICTION result (first-24-h labs → onset at any time) is repeated in the first row for contrast and is NOT superseded.", "",
         "| analysis | engine AUROC (95 % CI) | supervised logistic, same features | recall@5 (cases) | flag rate (controls) | sens / spec @0.5 |", "|---|---|---|---|---|---|"]
    if pre:
        pp = [x["sp"] for x in pre if x["y"]]; pn = [x["sp"] for x in pre if not x["y"]]
        L.append(f"| pre-registered: prediction, labs first 24 h | {auroc(pp, pn):.3f} | 0.689 (from report.md) | {pct(sum(1 for x in pre if x['y'] and x['rank'] and x['rank']<=5), len(pp))} | {pct(sum(1 for x in pre if not x['y'] and x['rank'] and x['rank']<=5), len(pn))} | — |")
    summ = {"encounter": a.encounter, "registry": str(a.registry), "data": a.data}
    for arm, name in (("A", "concurrent, labs only (+temperature)"), ("B", "concurrent, labs + vital signs (optional context module)")):
        pos = [x[f"sp_{arm}"] for x in res if x["y"]]; neg = [x[f"sp_{arm}"] for x in res if not x["y"]]
        au = auroc(pos, neg); lo, hi = boot_auc(pos, neg)
        r5p = sum(1 for x in res if x["y"] and x[f"rank_{arm}"] and x[f"rank_{arm}"] <= 5); r5n = sum(1 for x in res if not x["y"] and x[f"rank_{arm}"] and x[f"rank_{arm}"] <= 5)
        se = sum(1 for s in pos if s >= 0.5); spc = sum(1 for s in neg if s < 0.5)
        L.append(f"| {name} | **{au:.3f}** ({lo:.3f}–{hi:.3f}) | {base.get(arm)} | {pct(r5p, len(pos))} | {pct(r5n, len(neg))} | {100*se/len(pos):.1f} % / {100*spc/len(neg):.1f} % |")
        summ[arm] = dict(auroc=round(au, 3), ci=[round(lo, 3), round(hi, 3)], baseline=base.get(arm), recall5=[r5p, len(pos)], flag=[r5n, len(neg)], sens=round(se/len(pos), 3), spec=round(spc/len(neg), 3))
    na_c = sum(1 for x in res if x["y"] and x.get("anchor_labs", 1) == 0); na_n = sum(1 for x in res if not x["y"] and x.get("anchor_labs", 1) == 0)
    L += ["", f"Not assessable from laboratory values alone (neither lactate nor WBC in the window): cases {na_c}/{sum(1 for x in res if x['y'])}, controls {na_n}/{sum(1 for x in res if not x['y'])}. "
          "In arm B the SIRS/qSOFA syndrome layer can still assess these windows from vital signs."]
    summ["not_assessable"] = {"cases": na_c, "controls": na_n}
    tp = collections.Counter(x["top3_B"][0][0] for x in res if x["y"] and x["top3_B"]).most_common(8)
    tn = collections.Counter(x["top3_B"][0][0] for x in res if not x["y"] and x["top3_B"]).most_common(8)
    L += ["", "Top-1 (arm B) among cases: " + ", ".join(f"{k} {v}" for k, v in tp), "", "Top-1 (arm B) among controls: " + ", ".join(f"{k} {v}" for k, v in tn), "",
          "Caveats: post-hoc analysis added after the pre-registered result was known (Amendment 13, dated); the window is anchored on the label and therefore "
          "cannot be used operationally; controls are a seeded subsample; Sepsis-3 labels are themselves derived from SOFA/antibiotic/culture timing and are noisy."]
    open(f"{OUT}/concurrent_report{sfx}.md", "w").write("\n".join(L) + "\n"); json.dump(summ, open(f"{OUT}/concurrent_summary{sfx}.json", "w"), indent=1)
    print("\n".join(L))

if __name__ == "__main__":
    main()
