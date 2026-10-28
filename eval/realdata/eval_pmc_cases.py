"""B6 — Hemoglyph on the 50 PMC-Patients case-report vignettes of Bhasuran et al., npj Digit Med 2025 (8:166),
Supplementary Data 1 (open access; eval/realdata/pmc_cases/bhasuran_50_vignettes.csv).

Protocol (pre-specified in pmc_cases/scoring_key_prespecified.json BEFORE the first run):
  * Input to the engine = ONLY the "Lab Tests" free text of each vignette, parsed into structured analytes by the
    application's own OCR text parser (ocr.BloodLabPipeline on raw text; items with confidence >= 0.70 and a mapped
    feature id), plus age and sex. Symptoms and the case narrative are NOT given (labs-only arm) — the published LLM
    numbers (GPT-4 with labs: top-10 83 %, top-5 81 %, top-1 60 %, lenient) were obtained with the FULL vignette, so the
    two are not head-to-head; they bound what the laboratory component alone can achieve.
  * Scoring: specific (etiology named) and syndrome (laboratory syndrome named) at top-1/5/10, per the key; cases whose
    final diagnosis has no laboratory signature are reported separately.
  * Optional manual overrides for parser errors live in pmc_cases/panel_overrides.json (logged, with reason).

python3 eval/realdata/eval_pmc_cases.py  ->  eval/results/pmc_cases/{panels.json, per_case.json, report.md}
"""
import os, sys, re, json, math, logging
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
import pandas as pd
D = os.path.join(ROOT, "eval", "realdata", "pmc_cases"); O = os.path.join(ROOT, "eval", "results", "pmc_cases"); os.makedirs(O, exist_ok=True)
logging.disable(logging.CRITICAL)


def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def parse_age(a):
    s = str(a).lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(month|mo)", s)
    if m: return round(float(m.group(1)) / 12.0, 2)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(day)", s)
    if m: return round(float(m.group(1)) / 365.0, 3)
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def split_prose(txt):
    t = re.sub(r"\s+", " ", str(txt))
    parts = re.split(r"(?<=[\)\w%])[;,.]\s+(?=[A-Za-z])|\s+and\s+(?=[a-z])|\s+with\s+(?=[a-z])|\s+while\s+", t)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def build_panels(arm="parser"):
    strict = arm == "manual_strict"
    """arm='parser': end-to-end prose parser (overrides ignored). arm='manual': author-structured panels from panel_overrides.json
    ('replace': true -> parser output discarded; otherwise set/drop applied on top of parser output)."""
    from ocr import BloodLabPipeline
    pipe = BloodLabPipeline(language="en")
    df = pd.read_csv(os.path.join(D, "bhasuran_50_vignettes.csv"), header=None, skiprows=1)
    df.columns = ["pmid", "age", "sex", "labs", "symptoms", "report", "dx", "pubs"]
    ov = json.load(open(os.path.join(D, "panel_overrides.json"))) if (arm in ("manual", "manual_strict") and os.path.exists(os.path.join(D, "panel_overrides.json"))) else {}
    panels = []
    for _, r in df.iterrows():
        if not str(r.pmid).strip().isdigit(): continue
        res = pipe.process("\n".join(split_prose(r.labs)))
        obs, dropped = {}, []
        for it in res.get("results") or []:
            fid = it.get("feature_id"); v = it.get("value")
            if not fid or it.get("confidence", 0) < 0.70 or v is None: 
                if fid: dropped.append((fid, v, round(it.get("confidence", 0), 2)))
                continue
            if fid in obs: continue
            obs[fid] = {"value": v, "unit": it.get("unit")} if isinstance(v, (int, float)) else {"value": str(v)}
            if it.get("reported_reference"): obs[fid]["reported_reference"] = it["reported_reference"]
        o = ov.get(str(r.pmid), {})
        if o.get("replace"): obs = {}
        for fid, spec in (o.get("set") or {}).items(): obs[fid] = spec
        for fid in (o.get("drop") or []): obs.pop(fid, None)
        if strict:
            for fid in (o.get("imputed") or []): obs.pop(fid, None)
        panels.append({"pmid": str(r.pmid), "age_years": parse_age(r.age), "sex": "female" if str(r.sex).lower().startswith("f") else "male",
                       "dx": str(r.dx).strip(), "obs": obs, "n_obs": len(obs), "dropped_low_confidence": dropped[:20], "override": bool(o), "arm": arm, "note": o.get("_note")})
    json.dump(panels, open(os.path.join(O, f"panels_{arm}.json"), "w"), indent=1, ensure_ascii=False)
    return panels


def run(panels, arm="parser"):
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
    key = json.load(open(os.path.join(D, "scoring_key_prespecified.json")))["cases"]
    rows = []
    for p in panels:
        ctx = {"age_years": p["age_years"], "sex_at_birth": p["sex"]}
        rep = E.interpret(p["obs"], None, ctx).to_dict() if p["obs"] else {"differential_diagnosis": []}
        dd = [(d["disease_id"], round(float(d["probability"]), 3)) for d in rep.get("differential_diagnosis", [])][:10]
        k = key[p["pmid"]]
        def first_rank(rx):
            for i, (did, _) in enumerate(dd, 1):
                if re.search(rx, did): return i
            return None
        rs = first_rank(k["specific"]); ry = first_rank(k["specific"] + "|" + k["syndrome"])
        rows.append({**{x: p[x] for x in ("pmid", "age_years", "sex", "dx", "n_obs")}, "lab_detectable": k["lab_detectable"], "top10": dd,
                     "rank_specific": rs, "rank_syndrome": ry, "n_warnings": len(rep.get("input_warnings", []))})
    json.dump(rows, open(os.path.join(O, f"per_case_{arm}.json"), "w"), indent=1, ensure_ascii=False)
    return rows


def arm_block(rows, arm):
    desc = {"parser": "end-to-end: free-text 'Lab Tests' paragraph -> Hemoglyph prose parser -> engine (no human in the loop)",
            "manual": "author-structured panels (manual transcription of the same paragraph into analyte/value/unit, done before seeing engine output; narrative/symptoms never used)",
            "manual_strict": "sensitivity: manual panels with every imputed / typo-corrected value removed (4 cases, 9 values; see 'imputed' in panel_overrides.json)"}
    L = [f"## Arm `{arm}` — " + desc[arm], "",
         f"cases {len(rows)}; median analytes {sorted(r['n_obs'] for r in rows)[len(rows)//2]}; cases with 0 analytes {sum(1 for r in rows if r['n_obs']==0)}", ""]
    for title, sub in (("All 50 cases", rows), ("Lab-detectable final diagnoses", [r for r in rows if r["lab_detectable"]])):
        n = len(sub)
        L += [f"## {title} (n={n})", "", "| level | top-1 | top-5 | top-10 |", "|---|---|---|---|"]
        for lvl in ("specific", "syndrome"):
            cells = []
            for k in (1, 5, 10):
                h = sum(1 for r in sub if r[f"rank_{lvl}"] and r[f"rank_{lvl}"] <= k); p, lo, hi = wilson(h, n)
                cells.append(f"{100*p:.0f}% ({100*lo:.0f}–{100*hi:.0f}; {h}/{n})")
            L.append(f"| {lvl} | " + " | ".join(cells) + " |")
        L.append("")
    return L


def report(arms):
    rows = arms["manual"]
    L = ["# B6 — Hemoglyph (labs + age/sex only) on the 50 PMC-Patients vignettes of Bhasuran et al. 2025 (npj Digit Med 2025;8:159)", "",
         "Scoring key pre-specified in `scoring_key_prespecified.json` before any run (specific = the published final diagnosis; syndrome = the laboratory syndrome that contains it). Two arms, same engine, same key.", ""]
    for arm in ("parser", "manual", "manual_strict"): L += arm_block(arms[arm], arm)
    L += ["Published comparators on the SAME 50 vignettes but with the FULL vignette (demographics + symptoms + narrative + labs), lenient scoring (Bhasuran et al. 2025, Table 2): GPT-4 top-1 60 %, top-5 81 %, top-10 83 %; GPT-3.5 / Claude-2 / Llama-2 / Mixtral lower; adding labs improved accuracy by up to 30 points. Hemoglyph here sees labs + age/sex only and no narrative — the comparison bounds the laboratory contribution, it is not head-to-head.", "",
          "Per-case (manual arm; parser-arm ranks in brackets):", "",
          "| pmid | final diagnosis | n obs | rank specific | rank syndrome | top-3 |", "|---|---|---:|---|---|---|"]
    pr = {r["pmid"]: r for r in arms["parser"]}
    for r in rows:
        q = pr[r["pmid"]]
        L.append(f"| {r['pmid']} | {r['dx'][:60]} | {r['n_obs']} ({q['n_obs']}) | {r['rank_specific'] or '—'} ({q['rank_specific'] or '—'}) | {r['rank_syndrome'] or '—'} ({q['rank_syndrome'] or '—'}) | {', '.join(d for d, _ in r['top10'][:3])} |")
    open(os.path.join(O, "report.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L[:24]))


if __name__ == "__main__":
    arms = {}
    for arm in ("parser", "manual", "manual_strict"):
        arms[arm] = run(build_panels(arm), arm)
    report(arms)
