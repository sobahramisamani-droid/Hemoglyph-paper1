# -*- coding: utf-8 -*-
"""
Build the retrospective evaluation cohort from MIMIC-IV (hosp module).

Pre-specified cohort definition (see eval/PROTOCOL.md):
  * one record per hospital admission (hadm_id)
  * laboratory values: the FIRST result of each mapped analyte within the
    first 24 h after admission (admittime .. admittime + 24 h)
  * inclusion: >= 8 distinct mapped analytes AND a primary discharge
    diagnosis (diagnoses_icd.seq_num == 1, icd_version == 10) that maps to
    one of the groups in icd10_map.csv
  * exclusion: age < 18; itemids whose d_labitems label does not match the
    expected regex (hard failure - the mapping must be verified first)

Input files (gzip CSV from PhysioNet, MIMIC-IV v2.2 or later; hosp/):
  patients.csv.gz, admissions.csv.gz, diagnoses_icd.csv.gz,
  d_labitems.csv.gz, labevents.csv.gz
labevents is streamed (it is ~ 13 GB uncompressed); nothing is loaded into
memory except the admissions index and the per-admission first values.

Usage:
  python eval/mimic/build_cohort.py --mimic-dir /data/mimiciv/2.2/hosp \
         --out eval/results/cohort.jsonl [--max-per-group 200] [--seed 20261020]
Outputs:
  cohort.jsonl         one JSON per admission: hadm_id, age, sex, group,
                       icd_code, labs {feature_id: [value, unit]}
  cohort_summary.md    descriptive statistics (n per group, analyte coverage)
  cohort_panels.csv    canonical-id pivot usable by eval/solver_simulation.py --real-csv
"""
from __future__ import annotations
import argparse, csv, gzip, json, os, re, sys, random, collections, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))

def read_csv_gz(path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mimic-dir", required=True)
    ap.add_argument("--out", default="eval/results/cohort.jsonl")
    ap.add_argument("--min-analytes", type=int, default=8)
    ap.add_argument("--max-per-group", type=int, default=0, help="0 = no cap; otherwise random cap per group")
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--window-hours", type=float, default=24.0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)

    # ---------------- mappings
    imap = {}
    for r in csv.DictReader(open(os.path.join(HERE, "itemid_map.csv"), encoding="utf-8")):
        imap[int(r["itemid"])] = r
    groups = []
    for r in csv.DictReader(open(os.path.join(HERE, "icd10_map.csv"), encoding="utf-8")):
        groups.append((r["group"], [p.upper() for p in r["icd10_prefixes"].split("|")], r["accepted_disease_ids"].split("|"), r["lab_detectable"]))
    # longest prefix wins (E101 before E10)
    prefix_index = sorted(((p, g) for g, ps, _, _ in groups for p in ps), key=lambda x: -len(x[0]))

    # ---------------- verify itemid labels (hard failure on mismatch)
    labels = {int(r["itemid"]): (r["label"], r.get("fluid", "")) for r in read_csv_gz(os.path.join(a.mimic_dir, "d_labitems.csv.gz"))}
    bad = []
    for iid, r in imap.items():
        if iid not in labels:
            bad.append((iid, r["feature_id"], "itemid absent")); continue
        lab, fluid = labels[iid]
        if not re.search(r["expected_label_regex"], lab.strip().lower()):
            bad.append((iid, r["feature_id"], f"label '{lab}' !~ /{r['expected_label_regex']}/"))
        elif r["fluid"] and fluid and fluid.lower() != r["fluid"].lower():
            bad.append((iid, r["feature_id"], f"fluid '{fluid}' != {r['fluid']}"))
    if bad:
        print("ITEMID MAPPING FAILED VERIFICATION — fix itemid_map.csv before building the cohort:")
        for b in bad: print("  ", b)
        sys.exit(2)
    print(f"itemid map verified: {len(imap)} analytes")

    # ---------------- patients / admissions
    pat = {}
    for r in read_csv_gz(os.path.join(a.mimic_dir, "patients.csv.gz")):
        pat[r["subject_id"]] = (r["gender"], int(r["anchor_age"]), int(r["anchor_year"]))
    adm = {}
    for r in read_csv_gz(os.path.join(a.mimic_dir, "admissions.csv.gz")):
        t = dt.datetime.fromisoformat(r["admittime"])
        g, aage, ayear = pat.get(r["subject_id"], ("", 0, 0))
        age = aage + (t.year - ayear)
        if age < 18: continue
        adm[r["hadm_id"]] = {"subject_id": r["subject_id"], "admittime": t, "age": age, "sex": "female" if g == "F" else "male"}
    print(f"adult admissions: {len(adm):,}")

    # ---------------- primary diagnosis -> group
    target = {}
    for r in read_csv_gz(os.path.join(a.mimic_dir, "diagnoses_icd.csv.gz")):
        if r["seq_num"] != "1" or r["icd_version"] != "10" or r["hadm_id"] not in adm: continue
        code = r["icd_code"].replace(".", "").upper()
        for p, g in prefix_index:
            if code.startswith(p):
                target[r["hadm_id"]] = (g, code); break
    print(f"admissions with mapped primary ICD-10: {len(target):,}")
    # optional per-group cap (random, seeded) BEFORE reading labs to save time
    if a.max_per_group:
        by_g = collections.defaultdict(list)
        for h, (g, c) in target.items(): by_g[g].append(h)
        keep = set()
        for g, hs in by_g.items():
            rng.shuffle(hs); keep.update(hs[: a.max_per_group * 3])   # x3 because the analyte filter will drop some
        target = {h: v for h, v in target.items() if h in keep}

    # ---------------- stream labevents: first value per (hadm, feature) in window
    first = collections.defaultdict(dict)
    n_rows = 0
    for r in read_csv_gz(os.path.join(a.mimic_dir, "labevents.csv.gz")):
        n_rows += 1
        h = r["hadm_id"]
        if not h or h not in target: continue
        iid = int(r["itemid"])
        if iid not in imap: continue
        v = r.get("valuenum")
        if v in ("", None): continue
        t = dt.datetime.fromisoformat(r["charttime"])
        t0 = adm[h]["admittime"]
        if not (t0 - dt.timedelta(hours=6) <= t <= t0 + dt.timedelta(hours=a.window_hours)):   # ED labs up to 6 h before admit allowed
            continue
        fid = imap[iid]["feature_id"]
        cur = first[h].get(fid)
        if cur is None or t < cur[2]:
            first[h][fid] = (float(v), imap[iid]["unit"], t)
        if n_rows % 5_000_000 == 0: print(f"  labevents rows read: {n_rows:,}")

    # ---------------- assemble
    rows = []
    for h, (g, code) in target.items():
        labs = first.get(h, {})
        if len(labs) < a.min_analytes: continue
        rows.append({"hadm_id": h, "age": adm[h]["age"], "sex": adm[h]["sex"], "group": g, "icd_code": code,
                     "labs": {k: [v[0], v[1]] for k, v in labs.items()}})
    if a.max_per_group:
        by_g = collections.defaultdict(list)
        for r in rows: by_g[r["group"]].append(r)
        rows = []
        for g, rs in by_g.items():
            rng.shuffle(rs); rows.extend(rs[: a.max_per_group])
    rng.shuffle(rows)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in rows: fh.write(json.dumps(r) + "\n")

    # ---------------- summary + panels csv
    cnt = collections.Counter(r["group"] for r in rows)
    cov = collections.Counter(f for r in rows for f in r["labs"])
    L = [f"# Cohort summary\n\nAdmissions: {len(rows)}; groups: {len(cnt)}; min analytes: {a.min_analytes}; window: −6 h .. +{a.window_hours:g} h.\n",
         "| Group | n | lab-detectable |", "|---|---|---|"]
    det = {g: d for g, _, _, d in groups}
    for g, n in cnt.most_common(): L.append(f"| {g} | {n} | {det[g]} |")
    L += ["", "| Analyte | coverage |", "|---|---|"]
    for f, n in cov.most_common(): L.append(f"| {f} | {100*n/len(rows):.1f}% |")
    open(a.out.replace(".jsonl", "_summary.md"), "w", encoding="utf-8").write("\n".join(L))
    fids = sorted(cov)
    with open(a.out.replace(".jsonl", "_panels.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(fids)
        for r in rows: w.writerow([r["labs"].get(f, [""])[0] for f in fids])
    print("\n".join(L[:20])); print("saved", a.out)

if __name__ == "__main__":
    main()
