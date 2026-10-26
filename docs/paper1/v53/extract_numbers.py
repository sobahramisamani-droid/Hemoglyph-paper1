# -*- coding: utf-8 -*-
"""Extract every number used by the Paper-1 v5.3 manuscript from eval/results into one JSON.

    python3 docs/paper1/v53/extract_numbers.py            -> docs/paper1/v53/numbers_v53.json

Nothing is typed by hand here: each value is parsed from the report that the evaluation scripts
wrote, so the manuscript can be re-rendered (render.py) whenever a chain step finishes.
Status flags record which held-out arms have already been re-run on registry 13.3.0.
"""
import re, json, os, re, sys, glob, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
R = os.path.join(ROOT, "eval", "results"); V53 = os.path.join(R, "run_20261023_v53"); ED = os.path.join(R, "eicu_demo")

def rd(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

def J(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def tables(md):
    """Return list of tables; each table = list of rows (list of cell strings), header first."""
    out, cur = [], []
    for ln in md.splitlines():
        if ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            cur.append(cells)
        else:
            if cur: out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def table_after(md, heading_regex):
    m = re.search(heading_regex, md)
    if not m: return []
    t = tables(md[m.end():])
    return t[0] if t else []

def pct(s):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", s); return float(m.group(1)) if m else None

def pct_ci(s):
    m = re.search(r"(\d+(?:\.\d+)?)%\s*\((\d+(?:\.\d+)?)[–-](\d+(?:\.\d+)?)\)", s)
    return (float(m.group(1)), float(m.group(2)), float(m.group(3))) if m else (pct(s), None, None)

def fnum(s):
    m = re.search(r"(-?\d+(?:\.\d+)?)", s.replace("**", "")); return float(m.group(1)) if m else None

N = {"generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "status": {}}
done = {os.path.basename(p)[6:] for p in glob.glob(os.path.join(V53, ".done_*"))}
N["status"]["done_markers"] = sorted(done)

# ---------------------------------------------------------------- gate
g = rd(os.path.join(V53, "gate_v53.txt"))
N["gate"] = {k: v.strip() for k, v in re.findall(r"^(\w+): (.*)$", g, re.M)}

# ---------------------------------------------------------------- eICU arms
def eicu_arm(path):
    md = rd(path); d = {}
    if not md: return d
    m = re.search(r"Stays evaluated: (\d+) from (\d+) hospitals; median inputs (\d+); latency median (\d+) ms, p95 (\d+) ms", md)
    if m: d.update(stays=int(m.group(1)), hospitals=int(m.group(2)), median_inputs=int(m.group(3)), lat_med=int(m.group(4)), lat_p95=int(m.group(5)))
    t = table_after(md, r"## Recall of clinician-listed diagnoses")
    for row in t[1:]:
        k = row[0].replace("top-", "")
        d[f"r{k}_all"] = pct_ci(row[1]); d[f"r{k}_det"] = pct_ci(row[2])
        mm = re.search(r"n=(\d+)", row[1]); d["n_labels"] = int(mm.group(1)) if mm else None
        mm = re.search(r"n=(\d+)", row[2]); d["n_labels_det"] = int(mm.group(1)) if mm else None
    m = re.search(r"Chart support of confident outputs \(p ≥ 0\.7\): ([\d.]+)% \(([\d.]+)–([\d.]+)\) of (\d+)", md)
    if m: d["chart_support"] = (float(m.group(1)), float(m.group(2)), float(m.group(3)), int(m.group(4)))
    t = table_after(md, r"## Context-echo audit")
    if t:
        d["ctx_echo"] = {row[0].replace("top-", ""): (pct_ci(row[1]), pct_ci(row[2])) for row in t[1:]}
        mm = re.search(r"n=(\d+)\)", t[1][1]); d["ctx_named_n"] = int(mm.group(1)) if mm else None
        mm = re.search(r"n=(\d+)\)", t[1][2]); d["ctx_notnamed_n"] = int(mm.group(1)) if mm else None
    m = re.search(r"Stays with any context action: (\d+)/(\d+); documented entities confirmed by labs: (\d+); listed as documented-only: (\d+)", md)
    if m: d["ctx_actions"] = tuple(int(x) for x in m.groups())
    t = table_after(md, r"## Per-group")
    groups = {}
    for row in t[1:]:
        if len(row) < 7: continue
        groups[row[0]] = dict(detectable=row[1], n=int(row[2]), r5=pct_ci(row[3]), auroc=fnum(row[4]),
                              auroc_ci=re.search(r"\(([\d.]+)–([\d.]+)\)", row[4]).groups() if "(" in row[4] else None,
                              sens=pct(row[5]), spec=pct(row[6]))
    d["groups"] = groups
    m = re.search(r"Mean AUROC over lab-detectable groups with ≥ 5 listed stays: ([\d.]+) \(k=(\d+)\)", md)
    if m: d["mean_auroc"] = (float(m.group(1)), int(m.group(2)))
    return d

N["eicu"] = {"labs": eicu_arm(os.path.join(V53, "eicu_report_v5_3.md")),
             "ctx": eicu_arm(os.path.join(V53, "eicu_report_v5_3_ctx.md")),
             "ctx_tmp": eicu_arm(os.path.join(V53, "eicu_report_v5_3_ctx_tmp.md")),
             "v52_labs": eicu_arm(os.path.join(R, "run_20261023_v5", "eicu_report_v5_1.md")),
             "v52_ctx": eicu_arm(os.path.join(R, "run_20261023_v5", "eicu_report_v5_2_ctx.md")),
             "v52_tmp": eicu_arm(os.path.join(R, "run_20261023_v5", "eicu_report_v5_2_tmp.md")),
             "v52_ctx_tmp": eicu_arm(os.path.join(R, "run_20261023_v5", "eicu_report_v5_2_ctx_tmp.md"))}
for k in ("labs", "ctx", "ctx_tmp"):
    N["status"][f"eicu_{k}"] = "13.3.0" if N["eicu"][k] else "missing"

# ---------------------------------------------------------------- baselines B1 / B2 (inputs unchanged across engine versions)
cb = rd(os.path.join(ED, "calibration_baseline_safety.md"))
t = table_after(cb, r"## Baseline B1")
N["b1"] = {row[0]: dict(analyte=row[2], auroc=fnum(row[3]), sens_spec=row[4]) for row in t[1:]}
t = table_after(cb, r"## Safety S5")
N["s5_v4"] = {row[0].replace("**", ""): dict(n=int(row[1]), capt=pct_ci(row[2])) for row in t[1:]}
ml = rd(os.path.join(ED, "ml_baseline.md")); t = tables(ml)[0] if ml else []
N["b2"] = {row[0]: dict(n=int(row[1]), hgb=fnum(row[2]), hgb_ci=row[2], logreg=fnum(row[3])) for row in t[1:]}

# ---------------------------------------------------------------- calibration / DCA (v5.3)
cal = rd(os.path.join(ED, "calibration_dca_v5_3.md"))
m = re.search(r"stays (\d+); \(stay, group\) units (\d+); positives (\d+)", cal)
N["cal"] = {"units": int(m.group(2)) if m else None, "positives": int(m.group(3)) if m else None}
t = tables(cal)[0] if cal else []
N["cal"]["rows"] = {row[0]: dict(n=int(row[1]), prev=float(row[2]), ece_raw=float(row[3]), ece_iso=float(row[4]),
                                 brier_raw=float(row[5]), brier_iso=float(row[6]), auroc=float(row[7])) for row in t[1:]}
N["cal"]["reliability"] = [[float(x) for x in row] for row in (tables(cal)[1][1:] if len(tables(cal)) > 1 else [])]
dca = {}
for sec in re.split(r"\n### ", cal)[1:]:
    name = sec.split(" ", 1)[0]
    rows = tables(sec)[0][1:] if tables(sec) else []
    beats = re.search(r"beats both default strategies at thresholds: (.*)", sec)
    dca[name] = dict(rows=[[float(x) for x in r] for r in rows], beats=beats.group(1).strip() if beats else "")
N["cal"]["dca"] = dca

# ---------------------------------------------------------------- error audit, next-test (v5.3)
ea = rd(os.path.join(ED, "error_audit_v5_3.md"))
m = re.search(r"\(N = (\d+) misses across (\d+) stays\)", ea)
N["audit"] = {"n_misses": int(m.group(1)) if m else None}
t = tables(ea)[0] if ea else []
N["audit"]["cats"] = {row[0][:2].strip(" —"): dict(label=row[0], n=int(row[1]), pct=pct(row[2])) for row in t[1:]}
t = tables(ea)[1] if len(tables(ea)) > 1 else []
N["audit"]["by_group"] = [dict(group=r[0], n=int(r[1]), A=int(r[2]), B=int(r[3]), C1=int(r[4]), C2=int(r[5]), D=int(r[6])) for r in t[1:]]
nt = rd(os.path.join(ED, "next_test_utility_v5_3.md"))
t = tables(nt)[0] if nt else []
N["next_test"] = {r[0].replace("**", ""): dict(n=int(r[1].replace("**", "")), hit=int(r[2].replace("**", "")), pct=pct(r[3])) for r in t[1:]}
m = re.search(r"Median number of next-test recommendations per stay: (\d+)", nt)
N["next_test_median"] = int(m.group(1)) if m else None

# ---------------------------------------------------------------- subgroups (v5.3)
sg = rd(os.path.join(ED, "subgroup_fairness_v5_3.md"))
subg = {}
for sec in re.split(r"\n## By ", sg)[1:]:
    dim = sec.split("\n", 1)[0].strip(); t = tables(sec)[0] if tables(sec) else []
    subg[dim] = [dict(stratum=r[0], stays=int(r[1]), listed=int(r[2]), r5=pct_ci(r[3]), r10=pct(r[4]), support=pct(r[5]),
                      auroc_renal=r[6] if len(r) > 6 else "", auroc_sepsis=r[7] if len(r) > 7 else "") for r in t[1:]]
N["subgroups"] = subg
m = re.search(r"Overall: recall@5 ([\d.]+)%, recall@10 ([\d.]+)%, chart support ([\d.]+)% \(n = (\d+)\), false-assertion proxy in stays with empty problem list ([\d.]+)% \(n = (\d+)\)", sg)
N["subg_overall"] = [float(x) for x in m.groups()] if m else None
flags = re.search(r"## Strata deviating.*?\n(.*)", sg, re.S)
N["subg_flags"] = [ln.strip("- ").strip() for ln in flags.group(1).splitlines() if ln.strip().startswith(("-", "|"))][:12] if flags else []

# ---------------------------------------------------------------- LLM comparison B3/B4/B8 (n=400) and rank metrics
pool = rd(os.path.join(ED, "b3b4b8_pooled_n400.md"))
def llm_block(md, title_regex):
    sec = re.split(r"\n# ", md); d = {}
    for s in sec:
        if re.match(title_regex, s):
            m = re.search(r"stays (\d+); scorable labels (\d+)", s); d["stays"], d["labels"] = int(m.group(1)), int(m.group(2))
            t = tables(s)
            d["engine"] = pct_ci(t[0][1][1]); d["llm"] = pct_ci(t[0][2][1])
            m = re.search(r"\| (\d+)/(\d+)\)", t[0][1][1]); d["engine_frac"] = (int(m.group(1)), int(m.group(2))) if m else None
            m = re.search(r"(\d+)/(\d+)\)", t[0][2][1]); d["llm_frac"] = (int(m.group(1)), int(m.group(2))) if m else None
            m = re.search(r"Discordant: engine-only (\d+), LLM-only (\d+); McNemar exact p = ([\d.]+); difference ([+-][\d.]+) pp", s)
            if m: d.update(eng_only=int(m.group(1)), llm_only=int(m.group(2)), p=float(m.group(3)), diff=float(m.group(4)))
            d["groups"] = [dict(group=r[0], n=int(r[1]), engine=pct(r[2]), llm=pct(r[3])) for r in t[1][1:]] if len(t) > 1 else []
    return d
N["llm"] = {"pooled": llm_block(pool, r"POOLED"), "b8": llm_block(pool, r"B8 "), "b3": llm_block(pool, r"B3 "), "b4": llm_block(pool, r"B4 ")}
rk = rd(os.path.join(ED, "rank_metrics_n400.md")); t = tables(rk)
N["rank"] = {"pooled": {r[0]: (r[1], r[2]) for r in t[0][1:]} if t else {}, "pooled_bins": {r[0]: (int(r[1]), int(r[2])) for r in t[1][1:]} if len(t) > 1 else {}}

# ---------------------------------------------------------------- B5/B7 anchors (unchanged from earlier versions; engine side re-run under v5 in B7)
N["b5"] = rd(os.path.join(R, "nhanes_2017", "b5_blind_specificity.md"))[:3000]
N["b7"] = rd(os.path.join(ED, "b7_critical_values.md"))[:3000]

# ---------------------------------------------------------------- PMC-Patients B6
pmc = rd(os.path.join(R, "pmc_cases", "report.md"))
def pmc_arm(md, arm):
    sec = re.split(r"\n## Arm `", md)
    for s in sec:
        if s.startswith(arm):
            t = tables(s); d = {}
            m = re.search(r"cases (\d+); median analytes (\d+); cases with 0 analytes (\d+)", s)
            if m: d.update(cases=int(m.group(1)), median_analytes=int(m.group(2)), zero=int(m.group(3)))
            for lab, tb in (("all", t[0]), ("det", t[1] if len(t) > 1 else [])):
                for r in tb[1:]:
                    d[f"{lab}_{r[0]}"] = [re.search(r"(\d+)%.*?(\d+)/(\d+)", c).groups() for c in r[1:]]
            return d
    return {}
N["pmc"] = {"parser": pmc_arm(pmc, "parser"), "manual": pmc_arm(pmc, "manual"), "strict": pmc_arm(pmc, "manual_strict")}
N["status"]["pmc"] = "13.3.0" if "pmc53" in done else "13.1.0 (v5.2 frozen; re-run pending)"

# ---------------------------------------------------------------- NHANES (all cycles), thyroid, HCV, ILPD
def nh(cyc_dir):
    md = rd(os.path.join(cyc_dir, "report.md")); d = {}
    if not md: return d
    m = re.search(r"evaluated random subsample n=(\d+)", md) or re.search(r"(\d+) adults", md); d["n"] = int(m.group(1)) if m else None
    t = tables(md)[0] if tables(md) else []
    for r in t[1:]:
        if len(r) < 6: continue
        d[r[0]] = dict(ref=r[1], pos_neg=r[2], auroc=fnum(r[3]), auroc_ci=re.search(r"\(([\d.]+)–([\d.]+)\)", r[3]).groups(), sens=pct(r[4]), spec=pct(r[5]))
    m = re.search(r"(\d+) participants had every core analyte inside its reference interval; (\d+) \(([\d.]+)% \(([\d.]+)–([\d.]+)\)\)", md)
    if m: d["t8"] = dict(n=int(m.group(1)), k=int(m.group(2)), pct=float(m.group(3)), lo=float(m.group(4)), hi=float(m.group(5)))
    return d
N["nhanes"] = {}
for cyc, yr in (("J", "2017"), ("I", "2015"), ("H", "2013"), ("G", "2011"), ("F", "2009"), ("E", "2007"), ("D", "2005")):
    d = nh(os.path.join(R, f"nhanes_{yr}"))
    if d:
        N["nhanes"][yr] = d
        N["status"][f"nhanes_{yr}"] = "13.3.0" if f"nhfull_{cyc}" in done else "13.1.0 (v5.2; re-run pending)"
th = J(os.path.join(R, "uci_thyroid", "summary.json")); N["thyroid"] = th
N["status"]["thyroid"] = "13.3.0" if "thyroid53" in done else "13.1.0 (v5.2; re-run pending)"
hc = J(os.path.join(R, "uci_hcv", "summary.json"))
N["hcv"] = {x["task"]: dict(auroc=x["auroc"], ci=x["ci"], n_pos=x["n_pos"], n_neg=x["n_neg"], sens=x["sens50"], spec=x["spec50"]) for x in hc} if isinstance(hc, list) else hc
N["status"]["hcv"] = "13.3.0" if "hcv53" in done else "13.1.0 (v5.2; re-run pending)"
il = J(os.path.join(R, "ilpd", "summary.json"))
N["ilpd"] = {"liver patient vs non-patient": dict(auroc=il["auroc"], ci=il["ci"], n_pos=416, n_neg=167, sens=il["sens"], spec=il["spec"])} if "auroc" in il else il
N["status"]["ilpd"] = "13.3.0" if "ilpd53" in done else "13.1.0 (v5.2; re-run pending)"
sep = rd(os.path.join(R, "sepsis2019", "report.md")); N["sepsis2019_md"] = sep[:6000]
def _sp(label):
    m = re.search(re.escape(label) + r"[^|]*\|\s*([0-9.]+)%?\s*\(([0-9.]+)[–-]([0-9.]+)", sep)
    return [float(m.group(1)), float(m.group(2)), float(m.group(3))] if m else None
_m = re.search(r"evaluated (\d+); sepsis \(Sepsis-3, any hour\) (\d+)", sep)
N["sepsis2019"] = {"n": int(_m.group(1)) if _m else None, "n_sepsis": int(_m.group(2)) if _m else None,
                   "auroc": _sp("AUROC sepsis-group probability"), "auroc_logit": _sp("Supervised logistic baseline"),
                   "recall5": _sp("recall@5 of sepsis group among sepsis patients"), "flag_rate": _sp("sepsis group in top-5 among NON-sepsis"),
                   "sens": _sp("sensitivity at p>=0.5"), "spec": _sp("specificity at p>=0.5")}
N["status"]["sepsis2019"] = "13.3.0" if "sepsis19" in done else "pending"
for k in ("healthy_1000_s7.txt", "pert3_hard.txt", "twin_hard.txt"):
    N[k] = rd(os.path.join(V53, k))[-1500:]
N["status"]["fuzz"] = "done" if all(x in done for x in ("healthy1k", "pert3", "twin")) else "pending"

# ---------------------------------------------------------------- registry / engine constants (from live files)
try:
    sys.path.insert(0, ROOT)
    import cache_registry
    # Paper 1 is pinned to registry 13.3.0. The live file may be newer (13.4.x shipped), so prefer the frozen 13.3.0 copy.
    _p133 = os.path.join(ROOT, "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br.bak_v13_3_0")
    reg = cache_registry.bargozari_registry(_p133 if os.path.exists(_p133) else os.path.join(ROOT, "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"))
    assert str(reg["registry_metadata"].get("version", "")).startswith("13.3.0"), "Paper 1 numbers must come from registry 13.3.0"
    md = reg["registry_metadata"]; rl = list(reg["rules"].values()); dl = list(reg["diseases"].values())
    import collections
    kinds = collections.Counter(str(r.get("rule_type")) for r in rl if r.get("executable", True) and not str(r.get("status", "")).startswith("retired"))
    placeholders = sum(1 for d in dl if str((d.get("identity") or {}).get("lifecycle", "")).startswith("retired") or (d.get("identity") or {}).get("placeholder"))
    N["registry"] = {"version": md.get("version"), "entities": md.get("total_diseases"), "rules_total": md.get("total_rules"),
                     "executable": md.get("executable_rules") or sum(kinds.values()), "retired": md.get("retired_rules"),
                     "sources": md.get("total_sources"), "feature_registry": md.get("feature_registry_version"),
                     "rule_types": dict(kinds), "placeholder_entities": placeholders, "last_updated": md.get("last_updated")}
    fr = cache_registry.bargozari_registry(os.path.join(ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json.br"))
    feats = fr.get("features") or fr.get("parameters") or {}
    N["registry"]["features"] = len(feats)
    _fmd = fr.get("registry_metadata") or fr.get("metadata") or {}
    N["registry"]["feature_registry"] = _fmd.get("version") or N["registry"]["feature_registry"]  # the feature file's own version (12.1.0), not the compatibility tag
except Exception as e:
    N["registry"] = {"error": repr(e)}

out = os.path.join(HERE, "numbers_v53.json")
json.dump(N, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("wrote", out)
print(json.dumps(N["status"], indent=1))
print("eICU labs", N["eicu"]["labs"].get("r5_all"), "ctx", N["eicu"]["ctx"].get("r5_all"), "registry", N["registry"])
