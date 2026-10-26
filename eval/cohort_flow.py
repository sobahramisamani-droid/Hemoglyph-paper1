"""Participant flow (TRIPOD+AI item 14a/b) for every cohort used in Paper 1, from the raw public files.

python3 eval/cohort_flow.py
  -> docs/paper1/supplement/TABLE_S1_cohort_flow.md   (counts at each inclusion step + baseline characteristics)
  -> docs/paper1/figures/figS1_participant_flow.png   (flow diagram)
Light-weight: pandas only, no engine run.
"""
import os, json, glob, re
import pandas as pd, numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "eval", "realdata"); S = os.path.join(ROOT, "docs", "paper1", "supplement"); F = os.path.join(ROOT, "docs", "paper1", "figures")
os.makedirs(S, exist_ok=True); os.makedirs(F, exist_ok=True)
rows = []; boxes = []


def eicu():
    import sys; sys.path.insert(0, os.path.join(D)); from eval_eicu import LAB, GROUPS
    pt = pd.read_csv(os.path.join(D, "eicu_demo", "patient.csv.gz")); n0 = len(pt)
    pt["age_n"] = pd.to_numeric(pt.age.replace("> 89", "90"), errors="coerce"); ad = pt[pt.age_n >= 18]; n1 = len(ad)
    lab = pd.read_csv(os.path.join(D, "eicu_demo", "lab.csv.gz"))
    lab = lab[lab.labname.isin([k for k, v in LAB.items() if v]) & (lab.labresultoffset >= -360) & (lab.labresultoffset <= 1440) & lab.labresult.notna()]
    nlab = lab.drop_duplicates(["patientunitstayid", "labname"]).groupby("patientunitstayid").size()
    ok = ad[ad.patientunitstayid.map(nlab).fillna(0) >= 8]; n2 = len(ok)
    ps = json.load(open(os.path.join(ROOT, "eval/results/run_20261023_v5/eicu_per_stay_v5_1.json")))
    n_eval = len(ps); n_lab = sum(len(r["coded"]) for r in ps); n_hosp = ok.hospitalid.nunique()
    age = ok.age_n; fem = (ok.gender.str.lower().str.startswith("f")).mean()
    dx = pd.read_csv(os.path.join(D, "eicu_demo", "diagnosis.csv.gz"))
    n_dx = dx[dx.patientunitstayid.isin(ok.patientunitstayid)].diagnosisstring.nunique()
    rows.append(dict(cohort="eICU-CRD demo v2.0.1 (PhysioNet, open)", source="186 US hospitals, ICU stays 2014–15", step1=f"ICU stays in demo: {n0}", step2=f"age ≥18: {n1}", step3=f"≥8 mapped analytes in −6…+24 h: {n2}", analysed=f"{n_eval} stays; {n_lab} coded target labels (31 groups), {sum(1 for r in ps for g in r['coded'] if g in GROUPS and any(k in r['labs'] for k in GROUPS[g][2]))} scorable (key analyte measured)",
                     age=f"median {age.median():.0f} (IQR {age.quantile(.25):.0f}–{age.quantile(.75):.0f})", female=f"{100*fem:.1f}%", inputs="median 31 analytes/stay", labels=f"clinician problem-list diagnoses ({n_dx} distinct strings) → regex map", split="dev: first 1200 stays by id order (ext tuning); held-out: all 2314 reported with amendments logged"))
    boxes.append(("eICU demo", [f"{n0} stays", f"{n1} adults", f"{n2} with ≥8 analytes", f"{n_eval} analysed / {n_lab} labels"]))


def nhanes():
    tot = 0
    for d in sorted(glob.glob(os.path.join(D, "nhanes_*"))):
        yr = os.path.basename(d).split("_")[1]
        demo = glob.glob(os.path.join(d, "DEMO_*.csv.gz"))
        if not demo: continue
        dm = pd.read_csv(demo[0]); n0 = len(dm); ad = dm[dm.RIDAGEYR >= 18]; n1 = len(ad)
        bp = glob.glob(os.path.join(d, "BIOPRO_*.csv.gz")); cbc = glob.glob(os.path.join(d, "CBC_*.csv.gz"))
        ids = set(ad.SEQN)
        if bp: ids &= set(pd.read_csv(bp[0]).SEQN)
        if cbc: ids &= set(pd.read_csv(cbc[0]).SEQN)
        n2 = len(ids); tot += n2
        res = glob.glob(os.path.join(ROOT, "eval/results", f"nhanes_{yr}*", "summary.json"))
        nev = ""
        if res:
            try: nev = json.load(open(res[0])).get("n", json.load(open(res[0])).get("n_subjects", ""))
            except Exception: pass
        fem = (ad[ad.SEQN.isin(ids)].RIAGENDR == 2).mean(); age = ad[ad.SEQN.isin(ids)].RIDAGEYR
        rows.append(dict(cohort=f"NHANES {yr}–{int(yr)+1}", source="US civilian non-institutionalised population, mobile exam centre", step1=f"examined: {n0}", step2=f"age ≥18: {n1}", step3=f"with biochemistry + CBC: {n2}", analysed=f"{nev or 'see run log'} participants",
                         age=f"median {age.median():.0f} (IQR {age.quantile(.25):.0f}–{age.quantile(.75):.0f})", female=f"{100*fem:.1f}%", inputs="≈18–25 analytes (BIOPRO, CBC, GHB, GLU, FERTIN/FETIB, HDL/TRIGLY, ALB_CR)", labels="self-report (DIQ/MCQ/KIQ) + measured HbA1c/eGFR/Hb criteria", split="held-out (no tuning on any cycle); 2017–18 used first, 2005–16 added as temporal external validation"))
        boxes.append((f"NHANES {yr}", [f"{n0} examined", f"{n1} adults", f"{n2} with labs"]))
    return tot


def small(name, path, idcol=None):
    fs = glob.glob(os.path.join(D, path, "*.csv*")) + glob.glob(os.path.join(D, path, "*.data"))
    n = ""
    for f in fs:
        try: n = len(pd.read_csv(f, sep=None, engine="python")); break
        except Exception: continue
    return n


def others():
    for cohort, path, src, lab in (("UCI HCV (Hoffmann 2018)", "uci_hcv", "615 blood donors / hepatitis C patients, Germany", "clinical category (donor / hepatitis / fibrosis / cirrhosis)"),
                                   ("ILPD Indian Liver Patient Dataset", "ilpd", "583 patients, Andhra Pradesh", "liver patient yes/no"),
                                   ("UCI Thyroid (Garavan)", "uci_thyroid", "Garvan Institute, 1980s", "hypo/hyper-thyroid classes")):
        sm = glob.glob(os.path.join(ROOT, "eval/results", path, "summary.json")); n = ""
        if sm:
            try: j = json.load(open(sm[0])); n = j.get("n", j.get("n_subjects", j.get("n_records", "")))
            except Exception: pass
        rows.append(dict(cohort=cohort, source=src, step1="all records", step2="complete key analytes", step3="—", analysed=f"{n or small(cohort, path)} records", age="see dataset", female="see dataset", inputs="4–10 analytes", labels=lab, split="held-out, single pass"))
        boxes.append((cohort.split(" (")[0], [f"{n or '?'} analysed"]))
    sp = os.path.join(D, "sepsis2019", "training_setA_sub5000.csv.gz")
    if os.path.exists(sp):
        s = pd.read_csv(sp); npat = s.pid.nunique(); nsep = s.groupby("pid").SepsisLabel.max().sum()
        rows.append(dict(cohort="PhysioNet/CinC Challenge 2019, training set A", source="ICU, hospital system A (open access)", step1="20,336 patients in set A", step2=f"every 4th record: {npat}", step3="hourly rows with ≥1 lab", analysed=f"{npat} patients ({nsep} sepsis-labelled)", age="see dataset", female="see dataset", inputs="≤26 analytes + vitals, hourly", labels="Sepsis-3 onset label (t_sepsis − 6 h)", split="held-out, single pass"))
        boxes.append(("Sepsis-2019 A", [f"{npat} patients", f"{nsep} sepsis"]))


def write():
    cols = ["cohort", "source", "step1", "step2", "step3", "analysed", "age", "female", "inputs", "labels", "split"]
    L = ["# Table S1 — Participant flow and baseline characteristics of all evaluation cohorts (TRIPOD+AI 14a/b, 13a)", "",
         "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows: L.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    L += ["", "All cohorts are public; no participant was contacted. eICU: exclusion for <8 mapped analytes is the only data-driven exclusion (stays with sparse panels are not interpretable by any lab-only system). NHANES: participants without biochemistry/CBC subsample were not included. No imputation of missing analytes anywhere: absent analytes are treated as 'not measured' by the engine.", ""]
    open(os.path.join(S, "TABLE_S1_cohort_flow.md"), "w").write("\n".join(L) + "\n")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 1.6 + 0.9 * max(len(b[1]) for b in boxes))); ax.axis("off")
    w = 1.0 / len(boxes)
    for i, (title, steps) in enumerate(boxes):
        x = i * w + w / 2
        ax.text(x, 0.97, title, ha="center", va="top", fontsize=9, weight="bold", transform=ax.transAxes)
        for j, s in enumerate(steps):
            y = 0.85 - j * 0.22
            ax.text(x, y, s, ha="center", va="center", fontsize=8, transform=ax.transAxes, bbox=dict(boxstyle="round,pad=0.35", fc="#eef3fb" if j < len(steps) - 1 else "#dff0d8", ec="#5b7fb5"))
            if j < len(steps) - 1: ax.annotate("", xy=(x, y - 0.14), xytext=(x, y - 0.06), xycoords="axes fraction", arrowprops=dict(arrowstyle="->", color="#5b7fb5"))
    fig.suptitle("Figure S1 — Participant flow per evaluation cohort (Hemoglyph Paper 1)", fontsize=11)
    fig.savefig(os.path.join(F, "figS1_participant_flow.png"), dpi=160, bbox_inches="tight")
    print("\n".join(L))


if __name__ == "__main__":
    eicu(); nhanes(); others(); write()
