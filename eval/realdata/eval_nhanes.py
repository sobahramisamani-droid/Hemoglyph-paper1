#!/usr/bin/env python3
"""Hemoglyph held-out evaluation on NHANES 2017-2018 (CDC/NCHS public use).

PRE-SPECIFIED before the first run (2026-10-21); the engine is not modified
afterwards.  NHANES is a population survey, not a patient cohort, so the
reference standards are (a) laboratory case definitions from international
guidelines computed independently of the engine and (b) self-reported
physician diagnoses (independent of the laboratory values).

Tasks (adults >= 18 y with the standard biochemistry profile and CBC):
  T1 diabetes      ref: HbA1c >= 6.5 % or FPG >= 126 mg/dL (ADA 2024) or DIQ010 == 1 (told by doctor)
  T1b diabetes-SR  ref: DIQ010 == 1 only (self-report; independent of labs)
  T2 CKD           ref: eGFR(CKD-EPI 2021) < 60 or ACR >= 30 mg/g (KDIGO 2024)
  T2b CKD-SR       ref: KIQ022 == 1 (told of weak/failing kidneys)
  T3 anaemia       ref: Hb < 13 g/dL men, < 12 g/dL non-pregnant women (WHO 2024)
  T4 iron def.     ref: ferritin < 15 ng/mL (WHO 2020)                     [women & men]
  T5 hyperchol.    ref: total cholesterol >= 240 mg/dL (NCEP ATP III "high")
  T6 hyperuric.    ref: urate > 7.0 mg/dL men, > 6.0 mg/dL women
  T7 ALT elevation ref: ALT > 33 U/L men, > 25 U/L women (ACG 2017)
  T8 "healthy"     all core analytes inside reference -> share of participants with any
                   disease-level output >= 0.5 (false-assertion rate)

Engine input: the complete NHANES standard biochemistry profile, CBC with differential,
iron panel, ferritin, HbA1c, lipids, urine albumin/creatinine; fasting glucose, TG and
LDL only in the fasting subsample.  Conventional US units as reported by NHANES.
Score for a task = max probability over the task's entity group in the ranked
differential (list length 40).  Metrics: AUROC with 2000-draw bootstrap 95 % CI,
sensitivity/specificity at 0.5.  Unweighted (no survey weights; this is a
diagnostic-accuracy analysis, not a prevalence estimate).

Sample: all eligible adults, random subsample of N_MAX (seed 20261021) for runtime.
"""
from __future__ import annotations
import os, sys, json, time, math, random, argparse
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
_CYC = {"J": "2017", "I": "2015", "H": "2013", "G": "2011", "F": "2009", "E": "2007", "D": "2005"}
_cyc = next((a.split("=")[1] for a in sys.argv if a.startswith("--cycle=")), (sys.argv[sys.argv.index("--cycle") + 1] if "--cycle" in sys.argv else "J"))
DATA = os.path.join(HERE, f"nhanes_{_CYC[_cyc]}")
OUT = os.path.join(ROOT, "eval", "results", f"nhanes_{_CYC[_cyc]}")
_SFX = "_" + _cyc

# NHANES variable -> (feature_id, unit)
MAP = {
    "LBXSNASI": ("sodium", "mmol/L"), "LBXSKSI": ("potassium", "mmol/L"), "LBXSCLSI": ("chloride", "mmol/L"),
    "LBXSC3SI": ("bicarbonate", "mmol/L"), "LBXSBU": ("blood_urea_nitrogen", "mg/dL"), "LBXSCR": ("creatinine", "mg/dL"),
    "LBXSGL": ("glucose", "mg/dL"), "LBXSCA": ("calcium_total", "mg/dL"), "LBXSPH": ("phosphate", "mg/dL"),
    "LBXSTP": ("total_protein", "g/dL"), "LBXSAL": ("albumin", "g/dL"), "LBXSTB": ("total_bilirubin", "mg/dL"),
    "LBXSAPSI": ("alkaline_phosphatase", "U/L"), "LBXSASSI": ("aspartate_aminotransferase", "U/L"),
    "LBXSATSI": ("alanine_aminotransferase", "U/L"), "LBXSGTSI": ("gamma_glutamyl_transferase", "U/L"),
    "LBXSLDSI": ("lactate_dehydrogenase", "U/L"), "LBXSCK": ("creatine_kinase_total", "U/L"),
    "LBXSUA": ("uric_acid", "mg/dL"), "LBXSCH": ("total_cholesterol", "mg/dL"), "LBXSTR": ("triglycerides", "mg/dL"),
    "LBXSIR": ("iron", "ug/dL"), "LBXSOSSI": ("serum_osmolality", "mOsm/kg"),
    "LBXWBCSI": ("white_blood_cell_count", "10*3/uL"), "LBXRBCSI": ("red_blood_cell_count", "10*6/uL"),
    "LBXHGB": ("hemoglobin", "g/dL"), "LBXHCT": ("hematocrit", "%"), "LBXMCVSI": ("mean_corpuscular_volume", "fL"),
    "LBXMCHSI": ("mean_corpuscular_hemoglobin", "pg"), "LBXMC": ("mean_corpuscular_hemoglobin_concentration", "g/dL"),
    "LBXRDW": ("red_cell_distribution_width_cv", "%"), "LBXPLTSI": ("platelet_count", "10*3/uL"),
    "LBXMPSI": ("mean_platelet_volume", "fL"),
    "LBXNEPCT": ("neutrophils_percent", "%"), "LBXLYPCT": ("lymphocytes_percent", "%"),
    "LBDNENO": ("neutrophil_count_absolute", "10*3/uL"), "LBDLYMNO": ("lymphocyte_count_absolute", "10*3/uL"),
    "LBXFER": ("ferritin", "ng/mL"), "LBDTIB": ("total_iron_binding_capacity", "ug/dL"), "LBDPCT": ("transferrin_saturation", "%"),
    "LBXGH": ("hemoglobin_a1c", "%"), "LBXTC": ("total_cholesterol", "mg/dL"), "LBDHDD": ("hdl_cholesterol", "mg/dL"),
    "URXUMA": ("urine_albumin", "mg/L"), "URXUCR": ("urine_creatinine", "mg/dL"), "URDACT": ("urine_albumin_to_creatinine_ratio", "mg/g"),
    # fasting subsample
    "LBXGLU": ("fasting_plasma_glucose", "mg/dL"), "LBXTR": ("triglycerides", "mg/dL"), "LBDLDL": ("ldl_cholesterol_calculated", "mg/dL"),
}

GROUPS = {
    "diabetes": lambda d: d in ("type_2_diabetes_mellitus", "type_2_diabetes", "type_1_diabetes_mellitus", "type_1_diabetes",
                                "diabetes_mellitus", "latent_autoimmune_diabetes_in_adults", "dyslipidemia_of_diabetes",
                                "diabetic_kidney_disease", "hyperglycemia", "hyperglycemia_pattern"),
    "ckd": lambda d: d.startswith("ckd_g") or d in ("chronic_kidney_disease", "diabetic_kidney_disease", "albuminuria",
                                                   "moderately_increased_albuminuria", "severely_increased_albuminuria",
                                                   "microalbuminuria", "macroalbuminuria", "renal_impairment",
                                                   "acute_kidney_injury", "renal_insufficiency", "elevated_creatinine", "reduced_gfr_chronicity_undetermined",  # v14: NHANES CKD label is itself single-visit
                                                   "elevated_urine_albumin_to_creatinine_ratio", "kidney_disease"),
    "anemia": lambda d: d.endswith("anemia") or d.endswith("anaemia") or d in ("anemia", "anemia_of_chronic_disease",
                                                                              "anemia_of_chronic_inflammation",
                                                                              "anemia_of_chronic_disease_pattern",
                                                                              "thalassemia_trait", "beta_thalassemia_trait",
                                                                              "alpha_thalassemia_trait", "thalassemia_minor",
                                                                              "microcytic_anemia_pattern", "macrocytic_anemia_pattern",
                                                                              "normocytic_anemia_pattern"),
    "iron_deficiency": lambda d: d.startswith("iron_deficiency") or d in ("absolute_iron_deficiency", "iron_deficiency_pattern",
                                                                          "pregnancy_related_iron_deficiency_anemia"),
    "hypercholesterolemia": lambda d: d in ("hypercholesterolemia", "hypercholesterolemia_pattern", "hyperlipidemia",
                                            "mixed_dyslipidemia", "familial_hypercholesterolemia",
                                            "familial_combined_hyperlipidemia", "dyslipidemia", "elevated_total_cholesterol"),
    "hyperuricemia": lambda d: d in ("hyperuricemia", "gout", "gout_biochemical_risk", "elevated_uric_acid"),
    "alt_elevation": lambda d: d in ("hepatocellular_injury_pattern", "nafl_d", "nonalcoholic_fatty_liver_disease",
                                     "metabolic_dysfunction_associated_steatotic_liver_disease",
                                     "metabolic_dysfunction_associated_steatohepatitis", "nonalcoholic_steatohepatitis",
                                     "alcoholic_liver_disease", "alcoholic_hepatitis_pattern", "transaminitis",
                                     "elevated_alanine_aminotransferase", "elevated_aminotransferases",
                                     "acute_viral_hepatitis_pattern", "chronic_hepatitis_b", "chronic_hepatitis_c",
                                     "autoimmune_hepatitis", "drug_induced_liver_injury", "liver_cirrhosis",
                                     "hemochromatosis", "hereditary_hemochromatosis", "wilson_disease", "liver_disease"),
}


def egfr_ckdepi2021(scr, age, female):
    k = 0.7 if female else 0.9
    a = -0.241 if female else -0.302
    r = scr / k
    return 142 * min(r, 1) ** a * max(r, 1) ** -1.200 * 0.9938 ** age * (1.012 if female else 1.0)


def auroc(y, s):
    y = np.asarray(y); s = np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order)); ranks[order] = np.arange(1, len(order) + 1)
    allv = np.concatenate([pos, neg])
    # average ranks for ties
    _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.zeros(len(cnt)); np.add.at(sums, inv, ranks); ranks = sums[inv] / cnt[inv]
    return (ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def boot_ci(y, s, n=2000, seed=1):
    rng = np.random.default_rng(seed); y = np.asarray(y); s = np.asarray(s, float); vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].sum() in (0, len(y)):
            continue
        vals.append(auroc(y[i], s[i]))
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def fmt(k, n):
    p, lo, hi = wilson(k, n)
    return f"{100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f})"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n-max", type=int, default=3000); ap.add_argument("--seed", type=int, default=20261021); ap.add_argument("--cycle", default="J")
    ap.add_argument("--encounter", default=None, help="v14: ClinicalContext.encounter ('community' for NHANES)"); ap.add_argument("--registry", default=None, help="disease registry path (control arm)"); ap.add_argument("--data-dir", default=None, help="override data directory (e.g. eval/quarantine/nhanes_2013_H)"); ap.add_argument("--suffix", default=""); ap.add_argument("--engine-dir", default=None, help="load analyse_gidlines + registries from this directory (frozen v7 reproduction; see tools/make_frozen_engine_dir.py)")
    a = ap.parse_args()
    global DATA
    if a.data_dir: DATA = a.data_dir
    os.makedirs(OUT, exist_ok=True)
    def rd(f):
        f = f[:-2] + _SFX
        fp = os.path.join(DATA, f + ".xpt"); fc = os.path.join(DATA, f + ".csv.gz")  # column-trimmed copy (workspace size)
        if os.path.exists(fc):
            return pd.read_csv(fc)
        if not os.path.exists(fp):
            print("  (missing in this cycle:", f + ")"); return None
        return pd.read_sas(fp)
    df = rd("DEMO_J")[["SEQN", "RIAGENDR", "RIDAGEYR", "RIDEXPRG"]]
    for f in ["BIOPRO_J", "CBC_J", "GHB_J", "GLU_J", "ALB_CR_J", "FERTIN_J", "TCHOL_J", "HDL_J", "TRIGLY_J", "FETIB_J"]:
        t = rd(f)
        if t is None:
            continue
        t = t[[c for c in t.columns if c == "SEQN" or c in MAP]]
        df = df.merge(t, on="SEQN", how="left")
    for c in MAP:
        if c not in df.columns:
            df[c] = np.nan
    diq = rd("DIQ_J")[["SEQN", "DIQ010"]]; kiq = rd("KIQ_U_J")[["SEQN", "KIQ022"]]
    df = df.merge(diq, on="SEQN", how="left").merge(kiq, on="SEQN", how="left")
    df = df[(df.RIDAGEYR >= 18) & df.LBXSCR.notna() & df.LBXHGB.notna() & df.LBXSATSI.notna()].copy()
    df = df[df.RIDEXPRG.fillna(0) != 1]  # exclude pregnant
    n_elig = len(df)
    if len(df) > a.n_max:
        df = df.sample(n=a.n_max, random_state=a.seed)
    df = df.reset_index(drop=True)
    female = df.RIAGENDR == 2
    # reference standards
    egfr = np.array([egfr_ckdepi2021(c, ag_, f) for c, ag_, f in zip(df.LBXSCR, df.RIDAGEYR, female)])
    ref = {
        "diabetes": ((df.LBXGH >= 6.5) | (df.LBXGLU >= 126) | (df.DIQ010 == 1)).astype(int),
        "diabetes_selfreport": (df.DIQ010 == 1).astype(int),
        "ckd": ((egfr < 60) | (df.URDACT >= 30)).astype(int),
        "ckd_selfreport": (df.KIQ022 == 1).astype(int),
        "anemia": np.where(female, df.LBXHGB < 12, df.LBXHGB < 13).astype(int),
        "iron_deficiency": (df.LBXFER < 15).astype(int),
        "hypercholesterolemia": (df.LBXTC >= 240).astype(int),
        "hyperuricemia": np.where(female, df.LBXSUA > 6.0, df.LBXSUA > 7.0).astype(int),
        "alt_elevation": np.where(female, df.LBXSATSI > 25, df.LBXSATSI > 33).astype(int),
    }
    avail = {  # whether the reference analyte was measured
        "diabetes": df.LBXGH.notna(), "diabetes_selfreport": df.DIQ010.isin([1, 2]), "ckd": df.URDACT.notna(),
        "ckd_selfreport": df.KIQ022.isin([1, 2]), "anemia": df.LBXHGB.notna(), "iron_deficiency": df.LBXFER.notna(),
        "hypercholesterolemia": df.LBXTC.notna(), "hyperuricemia": df.LBXSUA.notna(), "alt_elevation": df.LBXSATSI.notna(),
    }
    task_group = {"diabetes": "diabetes", "diabetes_selfreport": "diabetes", "ckd": "ckd", "ckd_selfreport": "ckd",
                  "anemia": "anemia", "iron_deficiency": "iron_deficiency", "hypercholesterolemia": "hypercholesterolemia",
                  "hyperuricemia": "hyperuricemia", "alt_elevation": "alt_elevation"}
    # healthy definition (core analytes within reference)
    # Amendment 2026-10-21 (after first run, before re-run): the first definition let
    # participants with FPG 100-125, phosphate > 4.5, TG >= 150, CK > ULN, MCV < 80 or
    # lymphocytes > 45 % through, so true guideline findings (prediabetes by FPG, mild
    # hyperphosphataemia, microcytosis) were counted as "false" assertions.
    _dfh = df.copy()
    for _c, _neutral in (("LBXFER", 100.0), ("LBDPCT", 30.0)):
        if _dfh[_c].isna().all():  # analyte not collected in this cycle: do not let it veto 'healthy'
            _dfh[_c] = _neutral
    healthy = ((df.LBXGH < 5.7) & ~(df.LBXGLU >= 100) & (df.LBXSGL < 140) & (egfr >= 90) & (df.URDACT < 30)
               & np.where(female, df.LBXHGB >= 12, df.LBXHGB >= 13) & (df.LBXMCVSI.between(80, 100))
               & (_dfh.LBXFER >= 30) & (df.LBXTC < 200) & ~(df.LBXTR >= 150) & (df.LBXSTR < 200)
               & np.where(female, df.LBXSUA <= 6, df.LBXSUA <= 7)
               & np.where(female, df.LBXSATSI <= 25, df.LBXSATSI <= 33) & (df.LBXSNASI.between(135, 145))
               & (df.LBXSKSI.between(3.5, 5.1)) & (df.LBXSCLSI.between(98, 107)) & (df.LBXSCA.between(8.6, 10.3))
               & (df.LBXSPH.between(2.5, 4.5)) & (df.LBXPLTSI.between(150, 450)) & (df.LBXWBCSI.between(4, 11))
               & (df.LBXNEPCT.between(40, 75)) & (df.LBXLYPCT.between(20, 45)) & np.where(female, df.LBXSCK <= 200, df.LBXSCK <= 300)
               & (df.LBXSTB <= 1.2) & (df.LBXSAPSI <= 130) & (df.LBXSGTSI <= 60) & (df.LBXSAL >= 3.5) & (_dfh.LBDPCT.between(15, 50)))

    import logging; logging.disable(logging.CRITICAL)
    if getattr(a, "engine_dir", None):
        _ed = os.path.abspath(a.engine_dir); sys.path.insert(0, _ed)
        for _m in ("analyse_gidlines", "cache_registry", "calcu"): sys.modules.pop(_m, None)
    import analyse_gidlines as ag
    if getattr(a, "engine_dir", None): assert os.path.dirname(os.path.abspath(ag.__file__)) == _ed, ag.__file__
    print("engine:", ag.__file__, flush=True)
    E = ag.ClinicalRuleEngine(disease_registry_path=a.registry) if getattr(a, "registry", None) else ag.ClinicalRuleEngine()
    print("registry:", getattr(E.registry, "metadata", {}).get("version"), flush=True)
    E._reasoner.max_differential = 40  # evaluation: do not truncate the ranked list
    scores = {g: np.zeros(len(df)) for g in GROUPS}
    any_dx50 = np.zeros(len(df), bool); n_in = []; lat = []; top1 = []
    per_subject = []
    t_start = time.time()
    # checkpoint/resume (sandbox resets): per_subject rows are flushed every 50 participants and restored on restart;
    # df order is deterministic (seeded sample), so positional alignment holds.
    _ckpt = os.path.join(OUT, f"per_subject{a.suffix}.partial_n{a.n_max}.json")
    _done = json.load(open(_ckpt)) if os.path.exists(_ckpt) else []
    if _done: print(f"  resume: {len(_done)} participants from checkpoint", flush=True)
    for i, row in df.iterrows():
        if i < len(_done):
            r0 = _done[i]; per_subject.append(r0); n_in.append(r0["n_inputs"]); lat.append(r0.get("ms", 0) / 1000.0)
            top1.append(r0["top5"][0][0] if r0["top5"] else None); any_dx50[i] = bool(r0.get("any50", False))
            for g in GROUPS: scores[g][i] = r0.get(g, 0.0)
            continue
        obs = {}
        for var, (fid, unit) in MAP.items():
            v = row.get(var)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            if fid in obs:  # LBXTC preferred over LBXSCH; fasting TG over random TG
                continue
            obs[fid] = {"value": float(v), "unit": unit}
        n_in.append(len(obs))
        patient = {"age_years": int(row.RIDAGEYR), "sex_at_birth": "female" if row.RIAGENDR == 2 else "male"}
        if a.encounter: patient["encounter"] = a.encounter
        t0 = time.time()
        try:
            rep = E.interpret(obs, None, patient).to_dict()
        except Exception as ex:  # pragma: no cover
            rep = {"differential_diagnosis": [], "error": str(ex)}
        lat.append(time.time() - t0)
        dd = rep.get("differential_diagnosis", [])
        top1.append(dd[0]["disease_id"] if dd else None)
        for d in dd:
            p = float(d["probability"])
            if p >= 0.5 and not E._reasoner._is_finding(d["disease_id"]):
                any_dx50[i] = True
            for g, fn in GROUPS.items():
                if fn(d["disease_id"]) and p > scores[g][i]:
                    scores[g][i] = p
        per_subject.append({"SEQN": int(row.SEQN), "n_inputs": len(obs), "top5": [(d["disease_id"], round(float(d["probability"]), 3)) for d in dd[:5]],
                            "ge50": [d["disease_id"] for d in dd if float(d["probability"]) >= 0.5], "healthy": bool(healthy.iloc[i]),
                            "any50": bool(any_dx50[i]), "ms": round(1000 * lat[-1]),
                            **{g: round(float(scores[g][i]), 3) for g in GROUPS}})
        if (i + 1) % 50 == 0:
            json.dump(per_subject, open(_ckpt, "w"))
        if (i + 1) % 250 == 0:
            print(f"  {i+1}/{len(df)}  {time.time()-t_start:.0f}s", flush=True)

    lines = [f"# Hemoglyph — NHANES {_CYC[_cyc]}–{int(_CYC[_cyc])+1} held-out evaluation (cycle {_cyc})", "",
             f"Eligible adults (≥18 y, non-pregnant, biochemistry + CBC): {n_elig}; evaluated random subsample n={len(df)} (seed {a.seed}).",
             f"Median inputs per participant {int(np.median(n_in))} (IQR {int(np.percentile(n_in,25))}–{int(np.percentile(n_in,75))}); "
             f"latency median {1000*np.median(lat):.0f} ms, p95 {1000*np.percentile(lat,95):.0f} ms.", "",
             "| Task | reference standard | n (pos/neg) | AUROC (95% CI) | sens @0.5 | spec @0.5 |", "|---|---|---|---|---|---|"]
    summary = {}
    refdesc = {"diabetes": "HbA1c ≥6.5 / FPG ≥126 / told by doctor", "diabetes_selfreport": "told by doctor only (independent of labs)",
               "ckd": "eGFR <60 or ACR ≥30 (KDIGO)", "ckd_selfreport": "told of weak/failing kidneys (independent of labs)",
               "anemia": "WHO Hb cut-offs", "iron_deficiency": "ferritin <15 ng/mL (WHO)", "hypercholesterolemia": "TC ≥240 mg/dL",
               "hyperuricemia": "urate >7.0 M / >6.0 F", "alt_elevation": "ALT >33 M / >25 F (ACG)"}
    for t, y in ref.items():
        m = avail[t].values
        yy = np.asarray(y)[m]; ss = scores[task_group[t]][m]
        if yy.sum() < 5:
            continue
        au = auroc(yy, ss); lo, hi = boot_ci(yy, ss)
        tp = int(((ss >= .5) & (yy == 1)).sum()); fn = int(((ss < .5) & (yy == 1)).sum())
        tn = int(((ss < .5) & (yy == 0)).sum()); fp = int(((ss >= .5) & (yy == 0)).sum())
        lines.append(f"| {t} | {refdesc[t]} | {int(yy.sum())}/{int((yy==0).sum())} | **{au:.3f}** ({lo:.3f}–{hi:.3f}) | {fmt(tp, tp+fn)} | {fmt(tn, tn+fp)} |")
        summary[t] = {"n_pos": int(yy.sum()), "n_neg": int((yy == 0).sum()), "auroc": au, "ci": [lo, hi], "sens": tp / max(1, tp + fn), "spec": tn / max(1, tn + fp)}
    hm = healthy.values & np.isfinite(egfr)
    k = int(any_dx50[hm].sum()); n = int(hm.sum())
    lines += ["", f"## T8 false-assertion rate in guideline-healthy adults", "",
              f"{n} participants had every core analyte inside its reference interval; {k} ({fmt(k, n)}) received at least one non-finding entity with p ≥ 0.5.",
              ""]
    from collections import Counter
    c = Counter(t for t, h in zip(top1, hm) if h)
    lines.append("Most frequent top-1 outputs among healthy participants: " + ", ".join(f"{a_} ({b})" for a_, b in c.most_common(8)))
    summary["healthy"] = {"n": n, "false_assert": k}
    open(os.path.join(OUT, f"report{a.suffix}.md"), "w").write("\n".join(lines) + "\n")
    json.dump(summary, open(os.path.join(OUT, f"summary{a.suffix}.json"), "w"), indent=1)
    json.dump(per_subject, open(os.path.join(OUT, f"per_subject{a.suffix}.json"), "w"))
    if os.path.exists(_ckpt): os.remove(_ckpt)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
