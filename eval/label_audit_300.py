"""Reviewer item B7: extend the label-map audit from 100 to 300 additional stays (disjoint; seed 11).
Step 1 (this script, --list): liberal keyword coder vs study regex (eval_eicu.GROUPS) on the raw diagnosis strings;
prints every disagreeing stay×group cell with the full strings for adjudication.
Step 2 (--score adjudications.json): computes per-group precision / sensitivity of the regex map vs adjudicated truth.
Adjudication is performed by the first author (reading the strings) and is labelled an author audit, not an independent one.
"""
import os, sys, re, json, gzip, random, collections
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
from eval_eicu import GROUPS
R = os.path.join(ROOT, "eval", "results", "eicu_demo")
LIB = {  # deliberately over-inclusive second coder
 "acute_kidney_injury": r"acute renal|AKI|acute kidney|ATN|tubular necrosis", "chronic_kidney_disease": r"chronic renal|chronic kidney|CKD|ESRD|end.stage renal|dialysis",
 "renal_impairment": r"renal|kidney|ESRD|dialysis|azotemia|uremia", "diabetes": r"diabet|DM\b|insulin", "hyperglycemia": r"hyperglyc|glucose", "diabetic_ketoacidosis": r"DKA|ketoacid|ketosis",
 "hypoglycemia": r"hypoglyc", "hypokalemia": r"hypokal|low potassium|potassium", "hyperkalemia": r"hyperkal|potassium", "hyponatremia": r"hyponat|sodium", "hypernatremia": r"hypernat|sodium",
 "hypomagnesemia": r"magnes", "hypocalcemia": r"hypocalc|calcium", "hypercalcemia": r"hypercalc|calcium", "hypophosphatemia": r"phosph", "metabolic_acidosis": r"acidosis|acid.base",
 "lactic_acidosis": r"lactic|lactate", "anemia": r"anemi|anaemi|red blood|hemoglobin|blood loss|hemorrhag", "thrombocytopenia": r"thrombocyt|platelet|HIT\b|ITP", "leukocytosis": r"leukocyt|white blood|WBC|leukemoid",
 "sepsis": r"sepsis|septic|bacteremia|infection|SIRS", "hypothyroidism": r"thyroid|myxedema", "cirrhosis_liver_failure": r"cirrho|hepatic|liver|varice|ascites|portal", "acute_pancreatitis": r"pancrea",
 "acute_myocardial_infarction": r"myocardial|MI\b|STEMI|NSTEMI|coronary syndrome|ACS\b|infarct", "heart_failure": r"heart failure|CHF|cardiomyopathy|pulmonary edema|cardiogenic", "rhabdomyolysis": r"rhabdo|myoglobin|CK\b",
 "coagulopathy": r"coagul|DIC|INR|bleeding disorder|anticoag", "malnutrition": r"malnutr|nutrition|cachexia|failure to thrive", "gi_bleeding": r"GI bleed|gastrointestinal|melena|hematemesis|upper GI|lower GI|varice|ulcer", "alcohol_withdrawal": r"alcohol|withdrawal|ETOH|delirium tremens",
}
def main():
    dx = pd.read_csv(os.path.join(ROOT, "eval/realdata/eicu_demo/diagnosis.csv.gz"))
    rows = json.load(gzip.open(os.path.join(R, "per_stay_v7.json.gz"), "rt")); stays = [r["stay"] for r in rows]
    prev = set(json.load(open(os.path.join(R, "label_audit_stays100.json"))))
    pool = sorted(s for s in stays if s not in prev); random.Random(11).shuffle(pool); S = pool[:300]
    strings = dx[dx.patientunitstayid.isin(S)].groupby("patientunitstayid").diagnosisstring.apply(lambda s: sorted(set(s.astype(str)))).to_dict()
    if sys.argv[1] == "--list":
        json.dump(S, open(os.path.join(R, "label_audit_stays300.json"), "w"))
        dis = []; n_str = 0; n_pos = 0
        for s in S:
            strs = strings.get(s, []); n_str += len(strs); txt = " ;; ".join(strs)
            for g, (rx, _, _, _) in GROUPS.items():
                a = bool(re.search(rx, txt, re.I)); b = bool(re.search(LIB[g], txt, re.I)); n_pos += a
                if a != b: dis.append((s, g, a, [x for x in strs if re.search(LIB[g], x, re.I) or re.search(rx, x, re.I)]))
        print(f"stays {len(S)} strings {n_str} regex-positive cells {n_pos} disagreements {len(dis)}")
        for s, g, a, ev in dis: print(f"{s}\t{g}\tregex={'POS' if a else 'neg'}\t" + " || ".join(ev)[:300])
    else:
        adj = json.load(open(sys.argv[2]))  # {"stay|group": "miss" | "fp" | "ok_regex" | "ambiguous"}
        tp = fp = fn = amb = 0; pg = collections.defaultdict(lambda: [0, 0, 0])
        for s in S:
            txt = " ;; ".join(strings.get(s, []))
            for g, (rx, _, _, _) in GROUPS.items():
                a = bool(re.search(rx, txt, re.I)); v = adj.get(f"{s}|{g}", "ok_regex")
                if v == "ambiguous": amb += 1; continue
                if a and v == "fp": fp += 1; pg[g][1] += 1
                elif a: tp += 1; pg[g][0] += 1
                elif v == "miss": fn += 1; pg[g][2] += 1
        L = [f"# Label-mapping audit, extension to 300 further stays (seed 11; disjoint from the first 100) — author adjudication", "",
             f"| item | value |", "|---|---|", f"| stays / diagnosis strings | 300 / {sum(len(v) for v in strings.values())} |", f"| regex-positive labels | {tp+fp} |",
             f"| regex false positives | **{fp}** |", f"| definite misses | **{fn}** |", f"| ambiguous (excluded) | {amb} |",
             f"| precision | {100*tp/max(1,tp+fp):.1f}% | ", f"| sensitivity | {100*tp/max(1,tp+fn):.1f}% |", "", "| group | TP | FP | FN | precision | sensitivity |", "|---|---:|---:|---:|---:|---:|"]
        for g, (a, b, c) in sorted(pg.items(), key=lambda x: -sum(x[1])):
            L.append(f"| {g} | {a} | {b} | {c} | {100*a/max(1,a+b):.0f}% | {100*a/max(1,a+c):.0f}% |")
        L += ["", "Pooled with the first 100-stay audit (150 TP, 0 FP, 2 FN): precision " + f"{100*(tp+150)/(tp+150+fp):.1f}%, sensitivity {100*(tp+150)/(tp+150+fn+2):.1f}% over 400 stays.", "",
              "Disagreement cells were generated by a deliberately over-inclusive keyword coder; only disagreeing cells were read (agreement on negatives assumed). Adjudicator: first author; not an independent clinical audit."]
        open(os.path.join(R, "label_audit_n300.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
if __name__ == "__main__": main()
