"""B5 — false-assertion / specificity test on real NHANES 2017-18 adults, LLM vs engine.

prepare : draws 40 guideline-healthy + 30 reference-positive adults (seed), shuffles them, writes
          (a) b5_panels.txt  — de-identified panels for the blind reader (NO labels),
          (b) b5_hidden.json — labels + raw obs, read only by `score`.
score   : takes the blind reader's answers (json {idx: [[name, p], ...]}) and the current engine,
          reports false-assertion rate in healthy subjects and detection of the reference condition.
Uses the same MAP / healthy definition as eval/realdata/eval_nhanes.py (imported).
"""
import os, sys, json, math, argparse, random, logging
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
import eval_nhanes as en
OUT = os.path.join(ROOT, "eval", "results", "nhanes_2017")
AB = {"sodium": "Na", "potassium": "K", "chloride": "Cl", "bicarbonate": "HCO3", "blood_urea_nitrogen": "BUN", "creatinine": "Cr", "glucose": "Glu",
      "calcium_total": "Ca", "phosphate": "Phos", "total_protein": "TP", "albumin": "Alb", "total_bilirubin": "TBil", "alkaline_phosphatase": "ALP",
      "aspartate_aminotransferase": "AST", "alanine_aminotransferase": "ALT", "gamma_glutamyl_transferase": "GGT", "lactate_dehydrogenase": "LDH",
      "creatine_kinase_total": "CK", "uric_acid": "UA", "total_cholesterol": "TC", "triglycerides": "TG", "iron": "Fe", "serum_osmolality": "Osm",
      "white_blood_cell_count": "WBC", "red_blood_cell_count": "RBC", "hemoglobin": "Hb", "hematocrit": "Hct", "mean_corpuscular_volume": "MCV",
      "mean_corpuscular_hemoglobin": "MCH", "mean_corpuscular_hemoglobin_concentration": "MCHC", "red_cell_distribution_width_cv": "RDW",
      "platelet_count": "Plt", "mean_platelet_volume": "MPV", "neutrophils_percent": "Neut%", "lymphocytes_percent": "Lymph%",
      "neutrophil_count_absolute": "ANC", "lymphocyte_count_absolute": "ALC", "hemoglobin_a1c": "A1c", "glucose_fasting": "FPG",
      "urine_albumin_to_creatinine_ratio": "UACR", "ferritin": "Ferritin", "hdl_cholesterol": "HDL", "ldl_cholesterol": "LDL",
      "transferrin_saturation": "TSAT", "total_iron_binding_capacity": "TIBC", "fasting_glucose": "FPG", "insulin": "Insulin",
      "monocytes_percent": "Mono%", "eosinophils_percent": "Eos%", "basophils_percent": "Baso%"}
SKIP = {"mean_corpuscular_hemoglobin", "mean_corpuscular_hemoglobin_concentration", "mean_platelet_volume", "red_blood_cell_count",
        "neutrophil_count_absolute", "lymphocyte_count_absolute", "monocytes_percent", "eosinophils_percent", "basophils_percent", "insulin"}


def load():
    rd = lambda f: pd.read_sas(os.path.join(en.DATA, f + ".xpt"))
    df = rd("DEMO_J")[["SEQN", "RIAGENDR", "RIDAGEYR", "RIDEXPRG"]]
    for f in ["BIOPRO_J", "CBC_J", "GHB_J", "GLU_J", "ALB_CR_J", "FERTIN_J", "TCHOL_J", "HDL_J", "TRIGLY_J", "FETIB_J"]:
        t = rd(f); t = t[[c for c in t.columns if c == "SEQN" or c in en.MAP]]
        df = df.merge(t, on="SEQN", how="left")
    diq = rd("DIQ_J")[["SEQN", "DIQ010"]]; kiq = rd("KIQ_U_J")[["SEQN", "KIQ022"]]
    df = df.merge(diq, on="SEQN", how="left").merge(kiq, on="SEQN", how="left")
    df = df[(df.RIDAGEYR >= 18) & df.LBXSCR.notna() & df.LBXHGB.notna() & df.LBXSATSI.notna()].copy()
    df = df[df.RIDEXPRG.fillna(0) != 1].reset_index(drop=True)
    female = df.RIAGENDR == 2
    egfr = np.array([en.egfr_ckdepi2021(c, ag_, f) for c, ag_, f in zip(df.LBXSCR, df.RIDAGEYR, female)])
    ref = {"diabetes": ((df.LBXGH >= 6.5) | (df.LBXGLU >= 126)), "ckd": ((egfr < 60) | (df.URDACT >= 30)),
           "anemia": np.where(female, df.LBXHGB < 12, df.LBXHGB < 13), "iron_deficiency": (df.LBXFER < 15),
           "hypercholesterolemia": (df.LBXTC >= 240)}
    healthy = ((df.LBXGH < 5.7) & ~(df.LBXGLU >= 100) & (df.LBXSGL < 140) & (egfr >= 90) & (df.URDACT < 30)
               & np.where(female, df.LBXHGB >= 12, df.LBXHGB >= 13) & (df.LBXMCVSI.between(80, 100))
               & (df.LBXFER >= 30) & (df.LBXTC < 200) & ~(df.LBXTR >= 150) & (df.LBXSTR < 200)
               & np.where(female, df.LBXSUA <= 6, df.LBXSUA <= 7)
               & np.where(female, df.LBXSATSI <= 25, df.LBXSATSI <= 33) & (df.LBXSNASI.between(135, 145))
               & (df.LBXSKSI.between(3.5, 5.1)) & (df.LBXSCLSI.between(98, 107)) & (df.LBXSCA.between(8.6, 10.3))
               & (df.LBXSPH.between(2.5, 4.5)) & (df.LBXPLTSI.between(150, 450)) & (df.LBXWBCSI.between(4, 11))
               & (df.LBXNEPCT.between(40, 75)) & (df.LBXLYPCT.between(20, 45)) & np.where(female, df.LBXSCK <= 200, df.LBXSCK <= 300)
               & (df.LBXSTB <= 1.2) & (df.LBXSAPSI <= 130) & (df.LBXSGTSI <= 60) & (df.LBXSAL >= 3.5) & (df.LBDPCT.between(15, 50)))
    return df, ref, np.asarray(healthy, bool)


def obs_of(row):
    obs = {}
    for var, (fid, unit) in en.MAP.items():
        v = row.get(var)
        if v is None or (isinstance(v, float) and math.isnan(v)) or fid in obs:
            continue
        obs[fid] = {"value": float(v), "unit": unit}
    return obs


def prepare(a):
    df, ref, healthy = load()
    rng = random.Random(a.seed)
    H = [i for i in range(len(df)) if healthy[i]]
    pos = {k: [i for i in range(len(df)) if bool(np.asarray(ref[k])[i]) and not healthy[i]] for k in ref}
    pick = rng.sample(H, 40)
    quota = {"diabetes": 8, "ckd": 7, "anemia": 6, "iron_deficiency": 4, "hypercholesterolemia": 5}
    used = set(pick)
    for k, q in quota.items():
        cand = [i for i in pos[k] if i not in used]; sel = rng.sample(cand, q); used.update(sel); pick += sel
    rng.shuffle(pick)
    hidden, lines = [], []
    for j, i in enumerate(pick):
        row = df.iloc[i]; obs = obs_of(row)
        labs = {k: bool(np.asarray(ref[k])[i]) for k in ref}
        hidden.append({"idx": j, "seqn": int(row.SEQN), "age": int(row.RIDAGEYR), "sex": "female" if row.RIAGENDR == 2 else "male",
                       "healthy": bool(healthy[i]), "ref": labs, "obs": obs})
        parts = [f"{AB.get(k, k)}={v['value']:g}" for k, v in obs.items() if k not in SKIP]
        lines.append(f"#{j} {int(row.RIDAGEYR)}{'f' if row.RIAGENDR == 2 else 'm'}: " + " ".join(parts))
    json.dump(hidden, open(os.path.join(OUT, "b5_hidden.json"), "w"))
    open(os.path.join(OUT, "b5_panels.txt"), "w").write("\n".join(lines) + "\n")
    print(f"prepared {len(pick)} panels -> {OUT}/b5_panels.txt (labels hidden in b5_hidden.json)")


SYN = {"diabetes": ("diabetes", "hyperglycemia", "prediabetes"), "ckd": ("chronic kidney", "ckd", "renal", "kidney", "albuminuria"),
       "anemia": ("anemia", "anaemia"), "iron_deficiency": ("iron",), "hypercholesterolemia": ("cholesterol", "hyperlipid", "dyslipid", "lipid")}
ENG = {"diabetes": lambda d: "diabetes" in d or "hyperglycemia" in d or d.startswith("prediabetes"),
       "ckd": lambda d: "kidney" in d or "renal" in d or "albuminuria" in d, "anemia": lambda d: "anemia" in d,
       "iron_deficiency": lambda d: "iron_deficiency" in d, "hypercholesterolemia": lambda d: "cholesterol" in d or "hyperlipid" in d or "dyslipid" in d}
BENIGN = ("normal", "healthy", "no significant", "unremarkable", "prediabetes", "borderline", "mild", "low risk")


def score(a):
    logging.disable(logging.CRITICAL)
    import analyse_gidlines as ag
    hidden = json.load(open(os.path.join(OUT, "b5_hidden.json")))
    llm = json.load(open(a.llm))
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    R = {"llm": {"fa": 0, "fa_list": [], "det": {k: [0, 0] for k in SYN}}, "eng": {"fa": 0, "fa_list": [], "det": {k: [0, 0] for k in SYN}}}
    nh = 0
    for h in hidden:
        j = str(h["idx"]); ans = [(str(n).lower(), float(p)) for n, p in llm.get(j, [])]
        rep = E.interpret(h["obs"], None, {"age_years": h["age"], "sex_at_birth": h["sex"]}).to_dict()
        dd = [(d["disease_id"], float(d["probability"])) for d in rep["differential_diagnosis"]]
        if h["healthy"]:
            nh += 1
            la = [n for n, p in ans if p >= 0.5 and not any(b in n for b in BENIGN)]
            ea = [d for d, p in dd if p >= 0.5 and not E._reasoner._is_finding(d)]
            if la: R["llm"]["fa"] += 1; R["llm"]["fa_list"].append((h["seqn"], la[:3]))
            if ea: R["eng"]["fa"] += 1; R["eng"]["fa_list"].append((h["seqn"], ea[:3]))
        for k in SYN:
            if h["ref"].get(k):
                R["llm"]["det"][k][1] += 1; R["eng"]["det"][k][1] += 1
                R["llm"]["det"][k][0] += any(any(s in n for s in SYN[k]) and p >= 0.5 for n, p in ans)
                R["eng"]["det"][k][0] += any(ENG[k](d) and p >= 0.5 for d, p in dd)
    lines = ["# B5 — NHANES 2017-18 blind specificity / detection, LLM (Arena agent, blind) vs Hemoglyph (current engine)", "",
             f"{len(hidden)} adults: {nh} guideline-healthy + {len(hidden)-nh} reference-positive, shuffled; reader saw labs + age/sex only.", "",
             "| | LLM | Hemoglyph |", "|---|---|---|",
             f"| False assertions in healthy (any disease p ≥ 0.5) | {R['llm']['fa']}/{nh} ({100*R['llm']['fa']/nh:.0f}%) | {R['eng']['fa']}/{nh} ({100*R['eng']['fa']/nh:.0f}%) |"]
    for k in SYN:
        l, e = R["llm"]["det"][k], R["eng"]["det"][k]
        lines.append(f"| Detected {k} (p ≥ 0.5) | {l[0]}/{l[1]} | {e[0]}/{e[1]} |")
    lines += ["", "LLM false assertions: " + "; ".join(f"{s}: {', '.join(x)}" for s, x in R["llm"]["fa_list"]),
              "", "Engine false assertions: " + "; ".join(f"{s}: {', '.join(x)}" for s, x in R["eng"]["fa_list"]),
              "", "Limitations: the blind reader is the same agent that developed the engine; n small; 'finding' entities (e.g. isolated mild hypochloraemia) are not counted as disease assertions for either system."]
    open(os.path.join(OUT, "b5_blind_specificity.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["prepare", "score"]); ap.add_argument("--seed", type=int, default=20261021); ap.add_argument("--llm")
    a = ap.parse_args(); prepare(a) if a.cmd == "prepare" else score(a)
