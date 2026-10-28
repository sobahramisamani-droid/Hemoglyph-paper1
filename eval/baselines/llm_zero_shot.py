#!/usr/bin/env python3
"""Baseline B3 — general LLM zero-shot interpretation of the SAME panels (OpenRouter / OpenAI-compatible API).

Run on the user's machine (needs an API key; the sandbox has none):
    set OPENROUTER_API_KEY=...   (Windows)   /  export OPENROUTER_API_KEY=... (Linux)
    python eval/baselines/llm_zero_shot.py --per-stay eval/results/eicu_demo/per_stay.json \
        --model openai/gpt-4o --n 300 --out eval/results/eicu_demo/llm_gpt4o.json
    python eval/baselines/llm_zero_shot.py ... --model google/gemini-2.5-pro --out eval/results/eicu_demo/llm_gemini.json
    python eval/baselines/llm_zero_shot.py --score eval/results/eicu_demo/llm_gpt4o.json

Protocol (fixed, pre-specified):
  * identical inputs (analyte, value, unit, age, sex); temperature 0; one call per stay;
  * the model must return JSON: {"diagnoses":[{"name":..., "probability":0-1}], ...} — at most 10 entries;
  * names are mapped to Hemoglyph groups by a fixed synonym table (below); unmapped names are counted
    as "hallucinated/unscorable" and reported;
  * metrics identical to eval_eicu.py (Recall@5 of listed groups, per-group AUROC, chart support);
  * a random subsample of n stays (seed 20261021) to bound cost; the same subsample is used for Hemoglyph.
"""
from __future__ import annotations
import os, sys, json, time, random, argparse, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))

SYN = {
    "acute_kidney_injury": r"acute kidney|acute renal|\bAKI\b", "chronic_kidney_disease": r"chronic kidney|\bCKD\b|end.stage renal|ESRD",
    "renal_impairment": r"kidney|renal|azotemia|uremia", "diabetes": r"diabetes(?! insipidus)", "hyperglycemia": r"hyperglyc",
    "diabetic_ketoacidosis": r"ketoacidosis|\bDKA\b", "hypoglycemia": r"hypoglyc", "hypokalemia": r"hypokal", "hyperkalemia": r"hyperkal",
    "hyponatremia": r"hyponatr|SIADH", "hypernatremia": r"hypernatr", "hypomagnesemia": r"hypomagnes", "hypocalcemia": r"hypocalc",
    "hypercalcemia": r"hypercalc", "hypophosphatemia": r"hypophosph", "metabolic_acidosis": r"metabolic acidosis|acidosis",
    "lactic_acidosis": r"lactic", "anemia": r"an(a)?emia", "thrombocytopenia": r"thrombocytop", "leukocytosis": r"leukocytosis|leucocytosis",
    "sepsis": r"sepsis|septic", "hypothyroidism": r"hypothyroid", "cirrhosis_liver_failure": r"cirrhosis|liver failure|hepatic failure|hepatic encephalopathy|liver disease",
    "acute_pancreatitis": r"pancreatitis", "acute_myocardial_infarction": r"myocardial infarction|\bMI\b|NSTEMI|STEMI|myocardial injury",
    "heart_failure": r"heart failure|\bCHF\b", "rhabdomyolysis": r"rhabdo", "coagulopathy": r"coagulopathy|\bDIC\b",
    "malnutrition": r"malnutrition|hypoalbumin", "gi_bleeding": r"bleed|hemorrhage|haemorrhage", "alcohol_withdrawal": r"alcohol",
}
PROMPT = ("You are a clinical laboratory medicine expert. Given the following laboratory panel of an adult ICU patient "
          "(first 24 h of admission), list the most likely diagnoses or clinically important laboratory syndromes this panel supports. "
          "Return ONLY JSON of the form {\"diagnoses\":[{\"name\":\"...\",\"probability\":0.0-1.0}]} with at most 10 entries, "
          "ordered by probability. Do not include explanations.\n\nPatient: {age}-year-old {sex}.\nPanel:\n{panel}")


def call(model, prompt, key, base):
    body = json.dumps({"model": model, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def run(a):
    rows = json.load(open(a.per_stay)); random.Random(20261021).shuffle(rows); rows = rows[: a.n]
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    out = []
    for i, r in enumerate(rows):
        panel = "\n".join(f"- {k.replace('_', ' ')}: {v}" for k, v in r["vals"].items())
        p = PROMPT.format(age=r["age"], sex=r["sex"], panel=panel)
        t0 = time.time()
        try:
            txt = call(a.model, p, key, base); err = None
        except Exception as ex:
            txt, err = "", str(ex)
        m = re.search(r"\{.*\}", txt, re.S); dx = []
        if m:
            try:
                dx = json.loads(m.group(0)).get("diagnoses", [])
            except Exception:
                err = (err or "") + " bad-json"
        out.append({"stay": r["stay"], "coded": r["coded"], "labs": r["labs"], "gp": r["gp"], "gr": r["gr"], "llm": dx, "raw": txt, "err": err, "latency": time.time() - t0})
        if (i + 1) % 20 == 0:
            print(f"{i+1}/{len(rows)}", flush=True); json.dump(out, open(a.out, "w"))
    json.dump(out, open(a.out, "w")); print("saved", a.out)


def score(a):
    from eval_nhanes import auroc, boot_ci, fmt
    from eval_eicu import GROUPS
    rows = json.load(open(a.score)); import collections, numpy as np
    unmapped = 0; total = 0; rec = {5: [0, 0]}; rec_h = {5: [0, 0]}; pg = collections.defaultdict(lambda: dict(pos=[], neg=[], hpos=[], hneg=[]))
    for r in rows:
        names = [(str(d.get("name", "")), float(d.get("probability", 0) or 0)) for d in r["llm"]]
        gp, gr = {}, {}
        for rank, (nm, pr) in enumerate(names, 1):
            hit = False
            for g, rx in SYN.items():
                if re.search(rx, nm, re.I):
                    hit = True; gp[g] = max(gp.get(g, 0.0), pr); gr.setdefault(g, rank)
            total += 1; unmapped += not hit
        for g in GROUPS:
            if not any(k in r["labs"] for k in GROUPS[g][2]):
                continue
            y = g in r["coded"]
            (pg[g]["pos"] if y else pg[g]["neg"]).append(gp.get(g, 0.0)); (pg[g]["hpos"] if y else pg[g]["hneg"]).append(r["gp"].get(g, 0.0))
            if y:
                rec[5][1] += 1; rec[5][0] += (gr.get(g) is not None and gr[g] <= 5)
                rec_h[5][1] += 1; rec_h[5][0] += (r["gr"].get(g) is not None and r["gr"][g] <= 5)
    lines = [f"# LLM baseline — {a.score}", "", f"stays {len(rows)}; LLM entries {total}, unmapped to any group {unmapped} ({100*unmapped/max(1,total):.0f}%)",
             f"Recall@5 (listed groups, key analyte measured): LLM {fmt(*rec[5])} vs Hemoglyph {fmt(*rec_h[5])} on the same stays", "",
             "| group | n | LLM AUROC | Hemoglyph AUROC |", "|---|---:|---|---|"]
    for g, d in pg.items():
        if len(d["pos"]) < 5:
            continue
        y = np.array([1] * len(d["pos"]) + [0] * len(d["neg"]))
        lines.append(f"| {g} | {len(d['pos'])} | {auroc(y, np.array(d['pos']+d['neg'])):.2f} | {auroc(y, np.array(d['hpos']+d['hneg'])):.2f} |")
    txt = "\n".join(lines); print(txt); open(a.score.replace(".json", "_score.md"), "w").write(txt + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--per-stay"); ap.add_argument("--model", default="openai/gpt-4o"); ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out"); ap.add_argument("--score")
    a = ap.parse_args()
    score(a) if a.score else run(a)
