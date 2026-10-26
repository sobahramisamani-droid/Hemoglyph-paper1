# -*- coding: utf-8 -*-
"""
Secondary (multi-label) retrospective analysis on MIMIC-IV hosp data.

Unlike build_cohort.py (primary discharge diagnosis only, ICD-10 only), this
script uses EVERY coded diagnosis of an admission (ICD-9 and ICD-10, any
seq_num) mapped to the groups of icd10_map.csv / icd9_map.csv, and asks two
questions that match how a lab-interpretation CDSS is actually used:

  1. Recall@k  — for each coded *lab-detectable* group of the admission, is one
     of its accepted disease ids in Hemoglyph's top-k?  (k = 3, 5, 10)
  2. Per-group discrimination — across all admissions, AUROC of the maximum
     probability Hemoglyph assigns to the group's disease ids vs. the coded
     presence/absence of the group (admissions with ≥ 1 analyte relevant to
     the group only are not filtered; this is the conservative all-comers view).
     Also sensitivity/specificity at p ≥ 0.5 and p ≥ 0.7.
  3. Chart-support rate — among Hemoglyph outputs with p ≥ 0.7 that belong to a
     mapped group, the proportion whose group is coded in the chart.

Caveats written into the report: ICD coding under-records laboratory
abnormalities (electrolyte disorders, anaemia), so specificity and chart
support are LOWER bounds; the first-24 h window may precede the event that
was coded; ICU patients have many concurrent conditions.

Usage:
  python eval/mimic/multilabel_eval.py --mimic-dir eval/realdata/mimic_demo \
         --out eval/results/mimic_demo/multilabel  [--min-analytes 8] [--max-adm 0]
"""
from __future__ import annotations
import argparse, csv, gzip, json, os, sys, math, time, logging, collections, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); os.chdir(ROOT)
logging.disable(logging.CRITICAL)

def read_csv_gz(path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)

def wilson(k, n, z=1.96):
    if n == 0: return float("nan"), float("nan"), float("nan")
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d
def pct(k, n):
    p, lo, hi = wilson(k, n); return f"{100*p:.1f}% ({100*lo:.1f}–{100*hi:.1f})" if n else "—"

def auroc(scores_pos, scores_neg):
    if not scores_pos or not scores_neg: return float("nan")
    # Mann-Whitney with ties = 0.5
    allv = sorted(set(scores_pos + scores_neg)); rank = {}
    pts = sorted([(s, 1) for s in scores_pos] + [(s, 0) for s in scores_neg])
    i = 0; r = 0.0; n = len(pts); ranks = [0.0] * n
    while i < n:
        j = i
        while j + 1 < n and pts[j + 1][0] == pts[i][0]: j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1): ranks[k] = avg
        i = j + 1
    rpos = sum(rk for rk, (s, y) in zip(ranks, pts) if y == 1)
    n1, n0 = len(scores_pos), len(scores_neg)
    return (rpos - n1 * (n1 + 1) / 2) / (n1 * n0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mimic-dir", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--min-analytes", type=int, default=8); ap.add_argument("--max-adm", type=int, default=0)
    ap.add_argument("--window-hours", type=float, default=24.0); ap.add_argument("--pre-hours", type=float, default=6.0)
    ap.add_argument("--encounter", default=None, help="v14: ClinicalContext.encounter ('inpatient' for MIMIC-IV hosp admissions)")
    ap.add_argument("--registry", default=None, help="disease registry path (default: live file); e.g. eval/frozen_registry_13_3_0/... for the control arm")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)

    imap = {int(r["itemid"]): r for r in csv.DictReader(open(os.path.join(HERE, "itemid_map.csv"), encoding="utf-8"))}
    groups = {}
    for r in csv.DictReader(open(os.path.join(HERE, "icd10_map.csv"), encoding="utf-8")):
        groups[r["group"]] = dict(icd10=[p.upper() for p in r["icd10_prefixes"].split("|")], icd9=[], ids=set(r["accepted_disease_ids"].split("|")), det=r["lab_detectable"])
    for r in csv.DictReader(open(os.path.join(HERE, "icd9_map.csv"), encoding="utf-8")):
        if r["group"] in groups: groups[r["group"]]["icd9"] = r["icd9_prefixes"].split("|")
    id2group = collections.defaultdict(set)
    for g, d in groups.items():
        for i in d["ids"]: id2group[i].add(g)

    def code_groups(code, ver):
        code = code.strip().upper().replace(".", ""); out = set()
        for g, d in groups.items():
            for p in (d["icd10"] if ver == "10" else d["icd9"]):
                if code.startswith(p.upper()): out.add(g)
        return out

    # admissions / patients
    pats = {r["subject_id"]: r for r in read_csv_gz(os.path.join(a.mimic_dir, "patients.csv.gz"))}
    adms = {}
    for r in read_csv_gz(os.path.join(a.mimic_dir, "admissions.csv.gz")):
        p = pats.get(r["subject_id"]);
        if not p: continue
        t0 = dt.datetime.strptime(r["admittime"], "%Y-%m-%d %H:%M:%S")
        age = int(p["anchor_age"]) + (t0.year - int(p["anchor_year"]))
        if age < 18: continue
        adms[r["hadm_id"]] = dict(hadm_id=r["hadm_id"], subject_id=r["subject_id"], age=min(age, 90), sex="male" if p["gender"] == "M" else "female", t0=t0, coded=set(), labs={})
    for r in read_csv_gz(os.path.join(a.mimic_dir, "diagnoses_icd.csv.gz")):
        if r["hadm_id"] in adms: adms[r["hadm_id"]]["coded"] |= code_groups(r["icd_code"], r["icd_version"])
    # labs: first value per analyte within window
    first = collections.defaultdict(dict)
    for r in read_csv_gz(os.path.join(a.mimic_dir, "labevents.csv.gz")):
        h = r["hadm_id"]; iid = int(r["itemid"])
        if h not in adms or iid not in imap or not r["valuenum"]: continue
        t = dt.datetime.strptime(r["charttime"], "%Y-%m-%d %H:%M:%S"); t0 = adms[h]["t0"]
        if not (t0 - dt.timedelta(hours=a.pre_hours) <= t <= t0 + dt.timedelta(hours=a.window_hours)): continue
        fid = imap[iid]["feature_id"]
        if fid not in first[h] or t < first[h][fid][0]:
            first[h][fid] = (t, float(r["valuenum"]), imap[iid]["unit"])
    cohort = []
    for h, ad in adms.items():
        labs = {f: [v, u] for f, (t, v, u) in first.get(h, {}).items()}
        if len(labs) >= a.min_analytes: ad["labs"] = labs; cohort.append(ad)
    cohort.sort(key=lambda x: x["hadm_id"])
    if a.max_adm: cohort = cohort[:a.max_adm]
    print(f"admissions with >= {a.min_analytes} analytes: {len(cohort)}")

    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(disease_registry_path=a.registry) if a.registry else ag.ClinicalRuleEngine()
    print("registry:", getattr(E.registry, "metadata", {}).get("version"), flush=True)
    E._reasoner.max_differential = 40  # evaluation: do not truncate the ranked list
    out_rows = []; t_start = time.time()
    for i, ad in enumerate(cohort):
        payload = {f: {"value": v, "unit": u} for f, (v, u) in ad["labs"].items()}
        pt = {"age_years": ad["age"], "sex_at_birth": ad["sex"]}
        if a.encounter: pt["encounter"] = a.encounter
        t1 = time.perf_counter()
        try:
            rep = E.interpret(payload, None, pt).to_dict(); diff = rep["differential_diagnosis"]
        except Exception as e:
            diff = []; print("ERR", ad["hadm_id"], e)
        ms = (time.perf_counter() - t1) * 1000
        gp = collections.defaultdict(float); grank = {}
        for d in diff:
            for g in id2group.get(d["disease_id"], ()):
                gp[g] = max(gp[g], d["probability"])
                if g not in grank: grank[g] = d["rank"]
        out_rows.append(dict(hadm_id=ad["hadm_id"], age=ad["age"], sex=ad["sex"], n_analytes=len(ad["labs"]), labs=ad["labs"], coded=sorted(ad["coded"]), group_prob=dict(gp), group_rank=grank,
                             top10=[(d["disease_id"], round(d["probability"], 3), d["evidence_state"]) for d in diff[:10]], ms=round(ms)))
        if (i + 1) % 25 == 0: print(f"  {i+1}/{len(cohort)}  {time.time()-t_start:.0f}s")
    json.dump(out_rows, open(os.path.join(a.out, "per_admission.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)

    # ---- key analytes: a group is only evaluable in an admission where at least
    # one of its key analytes was measured (a lab CDSS cannot see hypothyroidism without a TSH)
    KEY = {"type_2_diabetes": ["hemoglobin_a1c", "glucose"], "type_1_diabetes": ["hemoglobin_a1c", "glucose"], "diabetic_ketoacidosis": ["beta_hydroxybutyrate", "bicarbonate"],
           "hyperosmolar_hyperglycemic_state": ["glucose"], "acute_kidney_injury": ["creatinine"], "renal_impairment": ["creatinine"], "chronic_kidney_disease": ["creatinine"], "hypothyroidism": ["thyroid_stimulating_hormone"],
           "hyperthyroidism": ["thyroid_stimulating_hormone"], "heart_failure": ["n_terminal_pro_bnp", "b_type_natriuretic_peptide"], "hyponatremia": ["sodium"], "hypernatremia": ["sodium"],
           "hyperkalemia": ["potassium"], "hypokalemia": ["potassium"], "hypercalcemia": ["calcium_total"], "metabolic_acidosis": ["bicarbonate"], "lactic_acidosis": ["lactate"],
           "hypercholesterolemia": ["total_cholesterol", "ldl_cholesterol_calculated", "ldl_cholesterol_direct"], "hypertriglyceridemia": ["triglycerides"],
           "cirrhosis": ["platelets", "albumin", "international_normalized_ratio"], "alcoholic_liver_disease": ["aspartate_aminotransferase"], "acute_liver_failure": ["international_normalized_ratio"],
           "chronic_hepatitis_b": ["hepatitis_b_surface_antigen"], "chronic_hepatitis_c": ["hepatitis_c_antibody"], "acute_pancreatitis": ["lipase", "amylase"],
           "sepsis": ["lactate", "white_blood_cell_count"], "acute_myocardial_infarction": ["troponin_t", "high_sensitivity_troponin_t", "troponin_i", "high_sensitivity_troponin_i", "creatine_kinase_mb"],
           "rhabdomyolysis": ["creatine_kinase_total"], "iron_deficiency_anemia": ["ferritin", "serum_iron", "transferrin_saturation"], "vitamin_b12_deficiency": ["vitamin_b12"], "folate_deficiency": ["folate_serum"],
           "anemia_of_chronic_disease": ["ferritin"], "thalassemia": ["mean_corpuscular_volume"], "hemolytic_anemia": ["lactate_dehydrogenase", "serum_haptoglobin"], "immune_thrombocytopenia": ["platelets"],
           "acute_myeloid_leukemia": ["white_blood_cell_count"], "chronic_lymphocytic_leukemia": ["lymphocyte_count_absolute", "lymphocytes_percent"], "multiple_myeloma": ["total_protein", "serum_free_kappa_to_lambda_ratio_flc"],
           "polycythemia_vera": ["hemoglobin"], "neutropenia": ["neutrophil_count_absolute", "neutrophils_percent"], "tumor_lysis_syndrome": ["uric_acid"], "disseminated_intravascular_coagulation": ["fibrinogen", "d_dimer"],
           "hypoglycemia": ["glucose"], "siadh": ["sodium"], "nephrotic_syndrome": ["albumin"], "gout": ["uric_acid"], "adrenal_insufficiency": ["cortisol_morning", "cortisol_random"],
           "primary_hyperparathyroidism": ["parathyroid_hormone"], "secondary_hyperparathyroidism": ["parathyroid_hormone"], "vitamin_d_deficiency": ["25_hydroxy_vitamin_d"], "hemochromatosis": ["ferritin", "transferrin_saturation"],
           "hepatic_encephalopathy": ["ammonia"], "protein_energy_malnutrition": ["albumin", "prealbumin"], "urinary_tract_infection": ["urine_leukocyte_esterase", "urine_nitrite", "urine_white_blood_cells_per_hpf"],
           "community_acquired_pneumonia": ["procalcitonin"], "pulmonary_embolism": ["d_dimer"], "gilbert_syndrome": ["total_bilirubin"], "cushing_syndrome": ["cortisol_morning"], "celiac_disease": ["tissue_transglutaminase_iga"],
           "systemic_lupus_erythematosus": ["antinuclear_antibody_titer"], "rheumatoid_arthritis": ["rheumatoid_factor"], "hiv_infection": ["cd4_t_cells_absolute"], "wilson_disease": ["ceruloplasmin"], "preeclampsia": ["urine_protein_to_creatinine_ratio"], "gestational_diabetes": ["glucose"], "acute_cholangitis": ["alkaline_phosphatase"]}
    def evaluable(r, g):
        ks = KEY.get(g); return True if not ks else any(k in r["labs"] for k in ks)
    # ---- metrics
    det_groups = {g for g, d in groups.items() if d["det"] == "yes"}
    rec = {3: [0, 0], 5: [0, 0], 10: [0, 0]}; rec_det = {3: [0, 0], 5: [0, 0], 10: [0, 0]}
    per_group = collections.defaultdict(lambda: dict(coded=0, hit3=0, hit5=0, hit10=0, pos=[], neg=[]))
    support_n = support_hit = 0; support_det_n = support_det_hit = 0; n_unevaluable = [0]
    for r in out_rows:
        coded = set(r["coded"])
        for g in groups:
            if not evaluable(r, g): continue
            p = r["group_prob"].get(g, 0.0)
            (per_group[g]["pos"] if g in coded else per_group[g]["neg"]).append(p)
        for g in coded:
            if not evaluable(r, g): n_unevaluable[0] += 1; continue
            rk = r["group_rank"].get(g)
            per_group[g]["coded"] += 1
            for k in (3, 5, 10):
                hit = rk is not None and rk <= k
                rec[k][1] += 1; rec[k][0] += hit
                if g in det_groups: rec_det[k][1] += 1; rec_det[k][0] += hit
                per_group[g][f"hit{k}"] += hit
        seen = set()
        for did, p, st in r["top10"]:
            if p < 0.7: continue
            for g in id2group.get(did, ()):
                if g in seen: continue
                seen.add(g); support_n += 1; support_hit += g in coded
                if g in det_groups: support_det_n += 1; support_det_hit += g in coded
    md = [f"# MIMIC-IV multi-label retrospective analysis", "",
          f"Source: `{a.mimic_dir}` — {len(out_rows)} adult admissions with ≥ {a.min_analytes} mapped analytes in −{a.pre_hours:g} h .. +{a.window_hours:g} h; "
          f"labels = all coded ICD-9/10 diagnoses mapped to {len(groups)} groups ({len(det_groups)} lab-detectable). Engine: registry {E.registry.metadata.get('version') if hasattr(E.registry,'metadata') and isinstance(E.registry.metadata, dict) else ''}.", "",
          "**Caveats (pre-specified):** ICD coding under-records laboratory abnormalities, so specificity and chart-support are lower bounds; "
          "the first-24 h panel may precede the coded event; no tuning was done on this data.", "",
          f"Coded group-admission pairs whose key analyte was NOT measured in the window (excluded as not evaluable): {n_unevaluable[0]}.", "",
          "## Recall of coded diagnoses — key analyte measured (all groups / lab-detectable groups)", "", "| k | all coded | lab-detectable coded |", "|---|---|---|"]
    for k in (3, 5, 10): md.append(f"| top-{k} | {pct(*rec[k])} (n={rec[k][1]}) | {pct(*rec_det[k])} (n={rec_det[k][1]}) |")
    md += ["", "## Chart support of confident outputs (p ≥ 0.7, mapped groups only)", "",
           f"- all groups: {pct(support_hit, support_n)} of {support_n} confident group-level outputs were coded in the chart",
           f"- lab-detectable groups: {pct(support_det_hit, support_det_n)} of {support_det_n}", "",
           "## Per-group discrimination (admission-level; coded presence vs. max probability)", "",
           "| Group | detectable | coded n | recall@5 | AUROC | sens p≥0.5 | spec p≥0.5 | sens p≥0.7 | spec p≥0.7 |", "|---|---|---:|---|---|---|---|---|---|"]
    rows_csv = []
    for g, d in sorted(per_group.items(), key=lambda x: -x[1]["coded"]):
        if d["coded"] == 0: continue
        au = auroc(d["pos"], d["neg"])
        s5 = sum(p >= 0.5 for p in d["pos"]); sp5 = sum(p < 0.5 for p in d["neg"]); s7 = sum(p >= 0.7 for p in d["pos"]); sp7 = sum(p < 0.7 for p in d["neg"])
        md.append(f"| {g} | {groups[g]['det']} | {d['coded']} | {pct(d['hit5'], d['coded'])} | {au:.2f} | {pct(s5, len(d['pos']))} | {pct(sp5, len(d['neg']))} | {pct(s7, len(d['pos']))} | {pct(sp7, len(d['neg']))} |")
        rows_csv.append(dict(group=g, detectable=groups[g]["det"], coded_n=d["coded"], recall5=d["hit5"] / d["coded"], auroc=au, sens50=s5 / len(d["pos"]), spec50=sp5 / max(1, len(d["neg"])), sens70=s7 / len(d["pos"]), spec70=sp7 / max(1, len(d["neg"])), n_neg=len(d["neg"])))
    aus = [r["auroc"] for r in rows_csv if r["detectable"] == "yes" and r["coded_n"] >= 5 and not math.isnan(r["auroc"])]
    if aus: md += ["", f"Mean AUROC over lab-detectable groups with ≥ 5 coded admissions: {sum(aus)/len(aus):.3f} (k={len(aus)})"]
    lat = sorted(r["ms"] for r in out_rows); md += ["", f"Latency: median {lat[len(lat)//2]} ms, p95 {lat[int(len(lat)*0.95)-1]} ms per admission (CPU sandbox)."]
    open(os.path.join(a.out, "multilabel_report.md"), "w", encoding="utf-8").write("\n".join(md))
    with open(os.path.join(a.out, "per_group.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys())); w.writeheader(); w.writerows(rows_csv)
    print("\n".join(md))

if __name__ == "__main__":
    main()
