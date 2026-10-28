#!/usr/bin/env python3
"""Held-out evaluation: eICU Collaborative Research Database DEMO v2.0.1 (PhysioNet, open access).

Pre-specified 2026-10-21, engine frozen before the run.  2,520 ICU stays from 186 US hospitals
(2014-2015).  Reference standard = the ICU clinicians' structured problem list
(`diagnosis.diagnosisstring`, entered during the stay; APACHE-style hierarchy), which is a
stronger label than billing ICD codes.  Inputs = first value of each laboratory analyte
between -6 h and +24 h of ICU admission (routine chemistry, CBC, LFTs, ABG, lactate, troponin,
BNP, TSH, lipase, CK, magnesium, phosphate), in eICU native units.

Design mirrors eval/mimic/multilabel_eval.py: per-stay multi-label; a labelled group counts
only when its key analyte was measured; metrics = Recall@k of coded groups, chart support of
p >= 0.7 outputs, per-group AUROC (coded vs. not coded) with 95% bootstrap CI.
Stays with < 8 analytes or age < 18 are excluded.
"""
from __future__ import annotations
import os, sys, json, time, re, collections, argparse
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from eval_nhanes import auroc, boot_ci, fmt  # noqa: E402
DATA = os.path.join(HERE, "eicu_demo"); OUT = os.path.join(ROOT, "eval", "results", "eicu_demo")

LAB = {  # eICU labname -> (feature_id, unit)
    "sodium": ("sodium", "mmol/L"), "potassium": ("potassium", "mmol/L"), "chloride": ("chloride", "mmol/L"),
    "bicarbonate": ("bicarbonate", "mmol/L"), "BUN": ("blood_urea_nitrogen", "mg/dL"), "creatinine": ("creatinine", "mg/dL"),
    "glucose": ("glucose", "mg/dL"), "calcium": ("calcium_total", "mg/dL"), "magnesium": ("magnesium", "mg/dL"),
    "phosphate": ("phosphate", "mg/dL"), "albumin": ("albumin", "g/dL"), "total protein": ("total_protein", "g/dL"),
    "AST (SGOT)": ("aspartate_aminotransferase", "U/L"), "ALT (SGPT)": ("alanine_aminotransferase", "U/L"),
    "alkaline phos.": ("alkaline_phosphatase", "U/L"), "total bilirubin": ("total_bilirubin", "mg/dL"),
    "direct bilirubin": ("direct_bilirubin", "mg/dL"), "anion gap": ("anion_gap", "mmol/L"),
    "Hgb": ("hemoglobin", "g/dL"), "Hct": ("hematocrit", "%"), "WBC x 1000": ("white_blood_cell_count", "10*3/uL"),
    "platelets x 1000": ("platelet_count", "10*3/uL"), "RBC": ("red_blood_cell_count", "10*6/uL"), "MCV": ("mean_corpuscular_volume", "fL"),
    "MCH": ("mean_corpuscular_hemoglobin", "pg"), "MCHC": ("mean_corpuscular_hemoglobin_concentration", "g/dL"),
    "RDW": ("red_cell_distribution_width_cv", "%"), "MPV": ("mean_platelet_volume", "fL"),
    "-lymphs": ("lymphocytes_percent", "%"), "-polys": ("neutrophils_percent", "%"), "-bands": ("band_neutrophils_percent", "%"),
    "-eos": ("eosinophils_percent", "%"), "-monos": ("monocytes_percent", "%"), "-basos": ("basophils_percent", "%"),
    "PT - INR": ("international_normalized_ratio", "1"), "PT": ("prothrombin_time", "s"), "PTT": ("activated_partial_thromboplastin_time", "s"),
    "pH": ("arterial_ph", "1"), "paCO2": ("arterial_pco2", "mmHg"), "paO2": ("arterial_po2", "mmHg"), "HCO3": ("bicarbonate", "mmol/L"), "Base Excess": ("base_excess", "mmol/L"),
    "lactate": ("lactate", "mmol/L"), "troponin - I": ("troponin_i", "ng/mL"), "troponin - T": ("troponin_t", "ng/mL"),
    "CPK": ("creatine_kinase_total", "U/L"), "CPK-MB": ("creatine_kinase_mb", "ng/mL"), "BNP": ("b_type_natriuretic_peptide", "pg/mL"),
    "TSH": ("thyroid_stimulating_hormone", "mIU/L"), "lipase": ("lipase", "U/L"), "amylase": ("amylase", "U/L"),
    "ionized calcium": ("calcium_ionized", "mmol/L"), "serum osmolality": ("serum_osmolality", "mOsm/kg"),
    "triglycerides": ("triglycerides", "mg/dL"), "total cholesterol": ("total_cholesterol", "mg/dL"), "ammonia": ("ammonia", "umol/L"),
    "fibrinogen": ("fibrinogen", "mg/dL"), "ferritin": ("ferritin", "ng/mL"), "uric acid": ("uric_acid", "mg/dL"),
    "free T4": ("free_thyroxine", "ng/dL"), "LDH": ("lactate_dehydrogenase", "U/L"), "procalcitonin": ("procalcitonin", "ng/mL"),
    "CRP": ("c_reactive_protein", "mg/L"), "Hemoglobin A1C": ("hemoglobin_a1c", "%"), "bedside glucose": None,
}

# group -> (regex on diagnosisstring, accepted engine ids, key analytes, lab-detectable)
# SAP Amendment 7 (2026-10-23): synonym ids added after the D-category audit (alcoholic_liver_disease/_pattern, septic_shock_* patterns).
# Frozen v1/v3/v4 result files were scored with the earlier map and are not re-scored.
GROUPS = {
    "acute_kidney_injury": (r"acute renal failure", {"acute_kidney_injury"}, ["creatinine"], "yes"),
    "chronic_kidney_disease": (r"chronic renal insufficiency|chronic kidney disease|ESRD", {"chronic_kidney_disease"}, ["creatinine"], "yes"),
    # v14: `reduced_gfr_chronicity_undetermined` (KDIGO single-panel finding) counts for the AKI/CKD UNION only — never for the strict AKI or CKD groups
    "renal_impairment": (r"acute renal failure|chronic renal insufficiency|chronic kidney disease|ESRD", {"acute_kidney_injury", "chronic_kidney_disease", "prerenal_azotemia", "cardiorenal_syndrome", "hepatorenal_syndrome", "renal_failure_unspecified", "reduced_gfr_chronicity_undetermined"}, ["creatinine"], "yes"),
    "diabetes": (r"glucose metabolism\|diabetes mellitus", {"type_2_diabetes", "type_1_diabetes", "diabetes_mellitus", "hyperglycemia"}, ["glucose"], "partial"),
    "hyperglycemia": (r"glucose metabolism\|hyperglycemia", {"hyperglycemia", "type_2_diabetes", "diabetes_mellitus", "stress_hyperglycemia"}, ["glucose"], "yes"),
    "diabetic_ketoacidosis": (r"\|DKA", {"diabetic_ketoacidosis", "euglycemic_diabetic_ketoacidosis"}, ["glucose", "bicarbonate"], "yes"),
    "hypoglycemia": (r"hypoglycemia", {"hypoglycemia", "fasting_hypoglycemia", "hyperinsulinemic_hypoglycemia", "sulfonylurea_induced_hypoglycemia"}, ["glucose"], "yes"),
    "hypokalemia": (r"\|hypokalemia", {"hypokalemia"}, ["potassium"], "yes"),
    "hyperkalemia": (r"\|hyperkalemia", {"hyperkalemia"}, ["potassium"], "yes"),
    "hyponatremia": (r"\|hyponatremia", {"hyponatremia", "severe_hyponatremia", "siadh"}, ["sodium"], "yes"),
    "hypernatremia": (r"\|hypernatremia", {"hypernatremia"}, ["sodium"], "yes"),
    "hypomagnesemia": (r"\|hypomagnesemia", {"hypomagnesemia"}, ["magnesium"], "yes"),
    "hypocalcemia": (r"\|hypocalcemia", {"hypocalcemia"}, ["calcium_total", "calcium_ionized"], "yes"),
    "hypercalcemia": (r"\|hypercalcemia", {"hypercalcemia"}, ["calcium_total", "calcium_ionized"], "yes"),
    "hypophosphatemia": (r"\|hypophosphatemia", {"hypophosphatemia"}, ["phosphate"], "yes"),
    "metabolic_acidosis": (r"\|metabolic acidosis", {"metabolic_acidosis", "lactic_acidosis", "high_anion_gap_metabolic_acidosis", "diabetic_ketoacidosis"}, ["bicarbonate"], "yes"),
    "lactic_acidosis": (r"lactic acidosis", {"lactic_acidosis"}, ["lactate"], "yes"),
    "anemia": (r"red blood cell disorders\|anemia", {"anemia", "acute_blood_loss_anemia", "iron_deficiency_anemia", "anemia_of_chronic_disease", "normocytic_anemia_pattern", "microcytic_anemia_pattern", "macrocytic_anemia_pattern", "pancytopenia"}, ["hemoglobin"], "yes"),
    "thrombocytopenia": (r"platelet disorders\|thrombocytopenia", {"thrombocytopenia", "immune_thrombocytopenia", "immune_thrombocytopenia_itp", "pancytopenia"}, ["platelet_count"], "yes"),
    "leukocytosis": (r"white blood cell disorders\|leukocytosis", {"leukocytosis", "leukocytosis_pattern", "neutrophilia_pattern", "leukemoid_reaction"}, ["white_blood_cell_count"], "yes"),
    "sepsis": (r"\|sepsis|septic shock", {"sepsis", "sepsis_support_pattern", "septic_shock", "septic_shock_support_pattern", "septic_shock_severe_lactic_acidosis"}, ["white_blood_cell_count"], "partial"),
    "hypothyroidism": (r"thyroid\|hypothyroidism", {"hypothyroidism", "primary_hypothyroidism", "subclinical_hypothyroidism"}, ["thyroid_stimulating_hormone"], "yes"),
    "cirrhosis_liver_failure": (r"cirrhosis|hepatic failure|liver failure|hepatic encephalopathy", {"liver_cirrhosis", "decompensated_cirrhosis_pattern", "cirrhosis_laboratory_pattern", "acute_liver_failure", "hepatic_encephalopathy", "alcohol_associated_liver_disease", "alcoholic_liver_disease", "alcoholic_liver_pattern"}, ["albumin", "total_bilirubin"], "partial"),
    "acute_pancreatitis": (r"pancreatitis", {"acute_pancreatitis", "acute_pancreatitis_support_pattern", "severe_acute_pancreatitis_support_pattern", "gallstone_pancreatitis_support_pattern", "alcoholic_pancreatitis"}, ["lipase"], "yes"),
    "acute_myocardial_infarction": (r"acute myocardial infarction", {"acute_myocardial_infarction", "acute_myocardial_injury", "myocardial_injury_acuity_undetermined", "acute_myocardial_infarction_support_pattern"}, ["troponin_i", "troponin_t"], "yes"),
    "heart_failure": (r"congestive heart failure", {"heart_failure", "acute_heart_failure", "chronic_heart_failure", "cardiorenal_syndrome", "heart_failure_decompensated", "heart_failure_bnp_pattern", "heart_failure_ntprobnp_pattern", "acute_heart_failure_support_pattern", "chronic_heart_failure_support_pattern"}, ["b_type_natriuretic_peptide"], "yes"),
    "rhabdomyolysis": (r"rhabdomyolysis", {"rhabdomyolysis"}, ["creatine_kinase_total"], "yes"),
    "coagulopathy": (r"coagulopathy|\|DIC", {"coagulopathy", "elevated_inr_pattern", "disseminated_intravascular_coagulation", "vitamin_k_deficiency", "vitamin_k_deficiency_coagulopathy", "liver_related_coagulopathy", "consumptive_coagulopathy", "warfarin_over_anticoagulation"}, ["international_normalized_ratio"], "yes"),
    "malnutrition": (r"malnutrition\|nutritional deficiency", {"protein_energy_malnutrition", "malnutrition", "hypoalbuminemia"}, ["albumin"], "partial"),
    "gi_bleeding": (r"GI bleeding", {"acute_blood_loss_anemia", "upper_gastrointestinal_bleeding_pattern", "anemia"}, ["hemoglobin"], "partial"),
    "alcohol_withdrawal": (r"drug withdrawal syndrome\|alcohol", {"alcohol_associated_liver_disease", "alcoholic_hepatitis_pattern", "alcohol_use_disorder_biomarker_pattern", "alcoholic_ketoacidosis", "alcoholic_liver_disease", "alcoholic_liver_pattern", "alcohol_use_disorder"}, ["aspartate_aminotransferase"], "partial"),
}


# phrases in pastHistory / home medications that already NAME a label group (used only to stratify recall, never as input)
_HIST_RX = {
    "diabetes": r"diabet|insulin|metformin|glipizide|glyburide|lantus|novolog|humalog|glargine",
    "renal": r"renal|dialysis|ckd|kidney", "ckd": r"renal|dialysis|ckd|kidney", "aki": r"renal|dialysis|ckd|kidney",
    "hf": r"chf|heart failure|cardiomyopathy|entresto|carvedilol|digoxin", "hypothyroid": r"hypothyroid|levothyroxine|synthroid",
    "cirrhosis": r"cirrhosis|lactulose|rifaximin", "anemia": r"anemia", "alcohol_withdrawal": r"alcohol|etoh",
    "coagulopathy": r"warfarin|coumadin|anticoag", "gout": r"gout|allopurinol", "copd": r"copd|emphysema|tiotropium|spiriva",
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n-max", type=int, default=100000)
    ap.add_argument("--context", action="store_true", help="arm B: labs + documented past history (pastHistory) + home medications (started before ICU admission). admissionDx is NEVER used (label leakage).")
    ap.add_argument("--temporal", action="store_true", help="arm C: pass every value of each analyte in the window as a time series (ESL ext 11-T); the scalar stays the FIRST value.")
    ap.add_argument("--suffix", default="", help="output file suffix (e.g. _ctx)")
    ap.add_argument("--encounter", default="unknown", help="v14: ClinicalContext.encounter ('icu' for eICU — true for every stay; enables KDIGO imputed-baseline AKI logic)")
    ap.add_argument("--engine-dir", default=None, help="load analyse_gidlines + registries from this directory (control arm)")
    a = ap.parse_args()
    suffix = a.suffix or ("_ctx" if a.context else "") + ("_tmp" if a.temporal else "")
    os.makedirs(OUT, exist_ok=True)
    pt = pd.read_csv(os.path.join(DATA, "patient.csv.gz"))
    lab = pd.read_csv(os.path.join(DATA, "lab.csv.gz"))
    dx = pd.read_csv(os.path.join(DATA, "diagnosis.csv.gz"))
    lab = lab[lab.labname.isin([k for k, v in LAB.items() if v])]
    lab = lab[(lab.labresultoffset >= -360) & (lab.labresultoffset <= 1440) & lab.labresult.notna()]
    lab = lab.sort_values(["patientunitstayid", "labresultoffset"])
    lab_all = lab if a.temporal else None
    lab = lab.drop_duplicates(["patientunitstayid", "labname"], keep="first")
    hist, meds = {}, {}
    if a.context:
        ph = pd.read_csv(os.path.join(DATA, "pastHistory.csv.gz"))
        ph = ph[~ph.pasthistoryvalue.isin(["Performed", "Not Obtainable", "No Health Problems"]) & ph.pasthistoryvalue.notna()]
        # keep the organ-system path so "medication dependent" reads as "Diabetes/medication dependent"
        ph["txt"] = ph.pasthistorypath.str.split("/").str[-2:].str.join(": ").fillna("") + " | " + ph.pasthistoryvalue.astype(str)
        hist = ph.groupby("patientunitstayid").txt.apply(lambda s_: sorted(set(s_))).to_dict()
        md = pd.read_csv(os.path.join(DATA, "medication.csv.gz"), low_memory=False)
        md = md[(md.drugstartoffset <= 0) & md.drugname.notna() & (md.drugordercancelled != "Yes")]
        meds = md.groupby("patientunitstayid").drugname.apply(lambda s_: sorted({str(x).lower()[:60] for x in s_})).to_dict()
    pt["age_n"] = pd.to_numeric(pt.age.replace("> 89", "90"), errors="coerce")
    pt = pt[pt.age_n >= 18]
    dxs = dx.groupby("patientunitstayid").diagnosisstring.apply(lambda s: " ;; ".join(s.astype(str))).to_dict()
    import logging; logging.disable(logging.CRITICAL)
    if a.engine_dir:
        _ed = os.path.abspath(a.engine_dir); sys.path.insert(0, _ed)
        for _m in ("analyse_gidlines", "cache_registry", "calcu"): sys.modules.pop(_m, None)
    import analyse_gidlines as ag
    if a.engine_dir: assert os.path.dirname(os.path.abspath(ag.__file__)) == _ed, ag.__file__
    print("engine:", ag.__file__, flush=True)
    _reg = os.environ.get("HEMOGLYPH_REGISTRY_OVERRIDE")   # ablation runs only (e.g. registry-off); default = live registry
    E = ag.ClinicalRuleEngine(disease_registry_path=_reg) if _reg else ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    rows = []; t0 = time.time(); lat = []
    # checkpoint/resume (sandbox resets): partial rows are flushed every 50 stays and reloaded on restart.
    # Results are byte-identical to a single pass because the engine is deterministic and stays are processed in order.
    ckpt = os.path.join(OUT, f"per_stay{suffix}.partial.json"); done_ids = set()
    if os.path.exists(ckpt) and a.n_max >= 1000:
        try:
            rows = json.load(open(ckpt)); done_ids = {r["stay"] for r in rows}
            print(f"  resume: {len(rows)} stays from checkpoint", flush=True)
        except Exception:
            rows = []
    for _, p in pt.iterrows():
        sid = p.patientunitstayid
        if int(sid) in done_ids:
            continue
        L = lab[lab.patientunitstayid == sid]
        obs = {}
        for _, r in L.iterrows():
            fid, unit = LAB[r.labname]
            if fid in obs:
                continue
            obs[fid] = {"value": float(r.labresult), "unit": unit}
        if len(obs) < 8:
            continue
        if lab_all is not None:
            LA = lab_all[lab_all.patientunitstayid == sid]
            for name, grp in LA.groupby("labname"):
                fid, unit = LAB[name]
                if fid in obs and len(grp) >= 2:
                    obs[fid]["series"] = [{"t_hours": float(o) / 60.0, "value": float(v)} for o, v in zip(grp.labresultoffset, grp.labresult)]
        labels = dxs.get(sid, "")
        coded = {g for g, (rx, _, _, _) in GROUPS.items() if re.search(rx, labels, flags=re.I)}
        patient = {"age_years": int(p.age_n), "sex_at_birth": "female" if str(p.gender).lower().startswith("f") else "male"}
        if a.encounter != "unknown":
            patient["encounter"] = a.encounter
        hist_txt = ""
        if a.context:
            kc = [h.split(" | ", 1)[0].replace(": ", " ") + " " + h.split(" | ", 1)[-1] for h in hist.get(sid, [])]
            if kc:
                patient["known_conditions"] = kc
            if meds.get(sid):
                patient["current_medications"] = meds[sid]
            hist_txt = " ;; ".join(kc + list(meds.get(sid, []))).lower()
        t1 = time.time(); rep = E.interpret(obs, None, patient).to_dict(); lat.append(time.time() - t1)
        dd = rep.get("differential_diagnosis", [])
        gp, gr, gr2 = {}, {}, {}
        # v14 two-tier rank: position counting only items of the same tier as the matched entity
        # (diagnosis groups are ranked among diagnoses; finding groups among findings/syndromes)
        tier_rank = {}; cnt = {}
        for d in dd:
            t = "diagnosis" if d.get("tier", "diagnosis") == "diagnosis" else "finding"
            cnt[t] = cnt.get(t, 0) + 1; tier_rank[d["disease_id"]] = cnt[t]
        # v14 grouped rank: an entry listed beneath the diagnosis that explains it (explained_by)
        # is nested under that diagnosis and inherits its position; only unexplained entries
        # (and entries whose explainer is not itself listed above them) consume a position.
        grouped_rank = {}; pos = 0; seen = set()
        for d in dd:
            ex = d.get("explained_by")
            if ex and ex in grouped_rank:
                grouped_rank[d["disease_id"]] = grouped_rank[ex]
            else:
                pos += 1; grouped_rank[d["disease_id"]] = pos
        gr3 = {}
        for g, (_, ids, _, _) in GROUPS.items():
            for d in dd:
                if d["disease_id"] in ids:
                    pr = float(d["probability"])
                    if pr > gp.get(g, 0.0):
                        gp[g] = pr
                    gr.setdefault(g, int(d["rank"]))
                    gr2.setdefault(g, tier_rank[d["disease_id"]])
                    gr3[g] = min(gr3.get(g, 999), grouped_rank[d["disease_id"]])
        # which coded groups are already named in the documented history (context-echo audit)
        in_hist = {g for g in coded if a.context and re.search(_HIST_RX.get(g, r"(?!x)x"), hist_txt)}
        n_series = sum(1 for v in obs.values() if v.get("series"))
        rows.append({"stay": int(sid), "hospital": int(p.hospitalid), "age": int(p.age_n), "sex": patient["sex_at_birth"], "n_in": len(obs), "labs": list(obs), "vals": {k: v["value"] for k, v in obs.items()},
                     "in_hist": sorted(in_hist), "n_series": n_series, "temporal": [t["id"] for t in rep.get("temporal_findings", [])],
                     "ctx_applied": [(c["disease_id"], c["action"]) for c in rep.get("clinical_context_applied", [])], "coded": sorted(coded), "gp": gp, "gr": gr, "gr2": gr2, "gr3": gr3,
                     "top5": [(d["disease_id"], round(float(d["probability"]), 3)) for d in dd[:5]]})
        if len(rows) % 50 == 0:
            print(f"  {len(rows)} stays  {time.time()-t0:.0f}s", flush=True)
            if a.n_max >= 1000:
                json.dump(rows, open(ckpt + ".tmp", "w")); os.replace(ckpt + ".tmp", ckpt)
        if len(rows) >= a.n_max:
            break
    # metrics
    evaluable = lambda r, g: any(k in r["labs"] for k in GROUPS[g][2])
    rec = {k: [0, 0] for k in (3, 5, 10)}; rec_det = {k: [0, 0] for k in (3, 5, 10)}; rec2 = {k: [0, 0] for k in (1, 3, 5)}; rec3 = {k: [0, 0] for k in (1, 3, 5, 10)}
    pg = collections.defaultdict(lambda: dict(coded=0, hit5=0, pos=[], neg=[]))
    sup_n = sup_hit = 0
    for r in rows:
        for g in GROUPS:
            if not evaluable(r, g):
                continue
            (pg[g]["pos"] if g in r["coded"] else pg[g]["neg"]).append(r["gp"].get(g, 0.0))
            if r["gp"].get(g, 0.0) >= 0.7:
                sup_n += 1; sup_hit += g in r["coded"]
        for g in r["coded"]:
            if not evaluable(r, g):
                continue
            rk = r["gr"].get(g); pg[g]["coded"] += 1
            rk2 = (r.get("gr2") or {}).get(g)
            for k in rec2:
                rec2[k][1] += 1; rec2[k][0] += (rk2 is not None and rk2 <= k)
            rk3 = (r.get("gr3") or {}).get(g)
            for k in rec3:
                rec3[k][1] += 1; rec3[k][0] += (rk3 is not None and rk3 <= k)
            for k in rec:
                rec[k][1] += 1; rec[k][0] += (rk is not None and rk <= k)
                if GROUPS[g][3] == "yes":
                    rec_det[k][1] += 1; rec_det[k][0] += (rk is not None and rk <= k)
            pg[g]["hit5"] += (rk is not None and rk <= 5)
    arm = "labs only" + (" + documented history/home medications (pastHistory + medication≤0 min; admissionDx excluded)" if a.context else "") + (" + within-window time series (ESL ext 11-T)" if a.temporal else "")
    lines = ["# Hemoglyph — eICU-CRD demo v2.0.1 held-out evaluation (multi-centre ICU, clinician problem-list labels)", "", f"**Input arm:** {arm}", "",
             f"Stays evaluated: {len(rows)} from {len({r['hospital'] for r in rows})} hospitals; median inputs {int(np.median([r['n_in'] for r in rows]))}; "
             f"latency median {1000*np.median(lat):.0f} ms, p95 {1000*np.percentile(lat,95):.0f} ms.", "",
             "## Recall of clinician-listed diagnoses (key analyte measured)", "", "| k | all groups | lab-detectable groups |", "|---|---|---|"]
    for k in rec:
        lines.append(f"| top-{k} | {fmt(*rec[k])} (n={rec[k][1]}) | {fmt(*rec_det[k])} (n={rec_det[k][1]}) |")
    lines += ["", "## Two-tier rank (v14, SAP Amendment 14 C1): position counted within the matched entity's tier (diagnoses among diagnoses; findings among findings/syndromes)", "",
              "| k | all groups |", "|---|---|"] + [f"| top-{k} | {fmt(*rec2[k])} (n={rec2[k][1]}) |" for k in rec2]
    lines += ["", "## Grouped rank (v14 output structure): entries nested beneath the diagnosis that explains them (`explained_by`) inherit its position; only independent entries consume a position", "",
              "| k | all groups |", "|---|---|"] + [f"| top-{k} | {fmt(*rec3[k])} (n={rec3[k][1]}) |" for k in rec3]
    if a.context:
        rh = {k: [0, 0] for k in (3, 5, 10)}; rn = {k: [0, 0] for k in (3, 5, 10)}
        for r in rows:
            for g in r["coded"]:
                if not evaluable(r, g):
                    continue
                rk = r["gr"].get(g); tgt = rh if g in r["in_hist"] else rn
                for k in tgt:
                    tgt[k][1] += 1; tgt[k][0] += (rk is not None and rk <= k)
        lines += ["", "## Context-echo audit (labels whose group is already NAMED in the documented history vs not)", "",
                  "| k | label named in history | label NOT named in history |", "|---|---|---|"]
        for k in rh:
            lines.append(f"| top-{k} | {fmt(*rh[k])} (n={rh[k][1]}) | {fmt(*rn[k])} (n={rn[k][1]}) |")
        n_ctx = sum(1 for r in rows if r["ctx_applied"]); n_conf = sum(1 for r in rows for c in r["ctx_applied"] if c[1] == "confirmed")
        lines += ["", f"Stays with any context action: {n_ctx}/{len(rows)}; documented entities confirmed by labs: {n_conf}; listed as documented-only: {sum(1 for r in rows for c in r['ctx_applied'] if c[1] == 'listed_documented')}."]
    if a.temporal:
        cnt = collections.Counter(t for r in rows for t in r["temporal"])
        lines += ["", f"## Temporal module: stays with ≥ 1 analyte series {sum(1 for r in rows if r['n_series'])}/{len(rows)}; median series per stay {int(np.median([r['n_series'] for r in rows]))}", "",
                  "| temporal constellation | fired (stays) |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in cnt.most_common()]
    lines += ["", f"## Chart support of confident outputs (p ≥ 0.7): {fmt(sup_hit, sup_n)} of {sup_n}", "",
              "## Per-group (stays with key analyte measured)", "", "| group | detectable | listed n | recall@5 | AUROC (95% CI) | sens @0.5 | spec @0.5 |", "|---|---|---:|---|---|---|---|"]
    summ = {}
    aus = []
    for g in sorted(pg, key=lambda g: -pg[g]["coded"]):
        d = pg[g]
        if d["coded"] < 5:
            continue
        y = np.array([1] * len(d["pos"]) + [0] * len(d["neg"])); s = np.array(d["pos"] + d["neg"])
        au = auroc(y, s); lo, hi = boot_ci(y, s, n=500)
        tp = int((np.array(d["pos"]) >= .5).sum()); tn = int((np.array(d["neg"]) < .5).sum())
        lines.append(f"| {g} | {GROUPS[g][3]} | {d['coded']} | {fmt(d['hit5'], d['coded'])} | **{au:.2f}** ({lo:.2f}–{hi:.2f}) | {fmt(tp, len(d['pos']))} | {fmt(tn, len(d['neg']))} |")
        summ[g] = {"coded": d["coded"], "recall5": d["hit5"] / d["coded"], "auroc": au, "ci": [lo, hi], "sens": tp / max(1, len(d["pos"])), "spec": tn / max(1, len(d["neg"]))}
        if GROUPS[g][3] == "yes":
            aus.append(au)
    lines += ["", f"Mean AUROC over lab-detectable groups with ≥ 5 listed stays: {np.mean(aus):.3f} (k={len(aus)})"]
    open(os.path.join(OUT, f"report{suffix}.md"), "w").write("\n".join(lines) + "\n")
    json.dump({"n_stays": len(rows), "arm": arm, "recall": rec, "recall_det": rec_det, "recall_two_tier": rec2, "recall_grouped": rec3, "encounter": a.encounter, "support": [sup_hit, sup_n], "groups": summ}, open(os.path.join(OUT, f"summary{suffix}.json"), "w"), indent=1)
    json.dump(rows, open(os.path.join(OUT, f"per_stay{suffix}.json"), "w"))
    if os.path.exists(ckpt):
        os.remove(ckpt)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
