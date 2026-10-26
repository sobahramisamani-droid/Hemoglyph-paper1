#!/usr/bin/env python3
"""Systematic defect-class scan of the guideline registry (read-only). Writes eval/results/registry_defect_scan_<ver>.md + .json
Classes:
 D1 sex-blind threshold on a sex-dimorphic analyte (threshold lies between female and male limits, population sex=all)
 D2 unit/scale inconsistency: same feature, same declared unit, thresholds spanning >= 100x
 D3 risk-factor / chronic-marker features used as screening/diagnostic for ACUTE entities
 D4 physiologically impossible thresholds
 D5 etiologic (non-syndromic) clinical entity proposable from ROUTINE analytes only (whole registry, not just infectious)
 D6 rule feature_id absent from the feature registry
 D7 paediatric/neonatal population attached to adult-only thresholds (creatinine, Hb, ALP, bilirubin)
 D8 'specific' specificity claimed for a single routine analyte diagnostic_criterion
 D9 source_ids not present in guideline_sources
 D10 single-analyte diagnostic_criterion with diagnosis_allowed true on a routine analyte
"""
import brotli, json, collections, os, re, sys
R0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(R0, "HEMOGLYPH_GUIDELINE_REGISTRY.json.br")
R = json.loads(brotli.decompress(open(path, "rb").read()))
F = json.loads(brotli.decompress(open(os.path.join(R0, "HEMOGLYPH_FEATURE_REGISTRY.json.br"), "rb").read()))
feats = F.get("features") or F
D, RU, SRC = R["diseases"], R["rules"], R.get("guideline_sources") or {}
ver = R["registry_metadata"]["version"].split("-")[0]
sys.path.insert(0, os.path.join(R0, "eval", "patches"))
from registry_v13_2_0_exposure_gate import ROUTINE

def leaves(e):
    if not isinstance(e, dict): return
    if "feature_id" in e: yield e
    for k in ("all", "any", "operands"):
        for x in e.get(k) or []: yield from leaves(x)
def fnum(v):
    try: return float(v)
    except Exception: return None
def sexlimits(fid):
    rr = (feats.get(fid) or {}).get("reference_ranges") or []
    m = next((r for r in rr if r.get("sex") == "male" and r.get("age_min", 18) >= 18), None)
    f = next((r for r in rr if r.get("sex") == "female" and r.get("age_min", 18) >= 18 and "pregnan" not in str(r.get("population"))), None)
    return (m, f) if m and f else None

out = collections.defaultdict(list)
ex_rules = {k: v for k, v in RU.items() if v.get("executable")}
prop = lambda r: r["rule_type"] in ("screening", "diagnostic_criterion")

# D1
for rid, r in ex_rules.items():
    if r["population"].get("sex") != "all": continue
    for l in leaves(r["expression"]):
        sl = sexlimits(l["feature_id"]); v = fnum(l.get("value"))
        if not sl or v is None: continue
        m, f = sl
        if l.get("unit") not in (m.get("unit"), None): continue
        op = l.get("operator")
        if op in (">", ">=") and f["high"] is not None and m["high"] is not None and f["high"] < v <= m["high"] * 1.0001:
            out["D1"].append((rid, l["feature_id"], op, v, f"F ULN {f['high']} / M ULN {m['high']}"))
        if op in ("<", "<=") and f["low"] is not None and m["low"] is not None and f["low"] * 0.9999 <= v < m["low"]:
            out["D1"].append((rid, l["feature_id"], op, v, f"F LLN {f['low']} / M LLN {m['low']}"))
# D2
byf = collections.defaultdict(list)
for rid, r in ex_rules.items():
    for l in leaves(r["expression"]):
        v = fnum(l.get("value"))
        if v and v > 0: byf[(l["feature_id"], l.get("unit"))].append((v, rid))
for (fid, u), vals in byf.items():
    vs = sorted(v for v, _ in vals)
    if len(vs) >= 3 and vs[-1] / vs[0] >= 100:
        out["D2"].append((fid, u, vs[0], vs[-1], len(vs)))
# D3
RISK = {"total_cholesterol", "ldl_cholesterol_direct", "hdl_cholesterol", "triglycerides", "lipoprotein_a", "apolipoprotein_b", "high_sensitivity_c_reactive_protein", "hemoglobin_a1c", "homocysteine", "body_mass_index"}
ACUTE_RX = re.compile(r"^acute_|infarction|_embolism|stroke|_crisis|_storm|shock|ketoacidosis|rhabdomyolysis|_rupture|dissection")
for rid, r in ex_rules.items():
    if prop(r) and ACUTE_RX.search(r["disease_id"]) and any(l["feature_id"] in RISK for l in leaves(r["expression"])):
        out["D3"].append((rid, r["disease_id"], [l["feature_id"] for l in leaves(r["expression"])]))
# D4
LIM = {"potassium": (1.0, 12), "sodium": (90, 200), "arterial_blood_ph": (6.5, 8.0), "arterial_ph": (6.5, 8.0), "hemoglobin": (1.0, 25), "glucose": (5, 2500),
       "creatinine": (0.05, 40), "calcium_total": (3, 20), "platelet_count": (0.5, 3000), "platelets": (0.5, 3000), "white_blood_cell_count": (0.05, 600),
       "total_bilirubin": (0.01, 80), "albumin": (0.5, 7), "hemoglobin_a1c": (2.5, 25), "magnesium": (0.2, 12), "phosphate": (0.2, 20), "bicarbonate": (2, 60), "lactate": (0.1, 40)}
for rid, r in ex_rules.items():
    for l in leaves(r["expression"]):
        v = fnum(l.get("value")); lim = LIM.get(l["feature_id"])
        if lim and v is not None and not (lim[0] <= v <= lim[1]): out["D4"].append((rid, l["feature_id"], v, l.get("unit")))
# D5
SYNDROMIC_RX = re.compile(r"pattern$|_syndrome$|anemia|acidosis|alkalosis|emia$|penia$|cytosis$|philia$|injury|failure|insufficiency|impairment|sepsis|infection$|pneumonia|cellulitis|osteomyelitis|cholangitis|gastroenteritis|tuberculosis|hepatitis$|cirrhosis|ckd|kidney_disease|diabetes|prediabetes|hyperglycemia|hypoglycemia|dehydration|malnutrition|obesity|metabolic|dyslipidemia|hyperlipidemia|hypercholesterolemia|hypertriglyceridemia|cholestasis|jaundice|hyperbilirubinemia|coagulopathy|bleeding|hemolysis|inflammation|hypothyroid|hyperthyroid|thyroid|pancreatitis|rhabdomyolysis|withdrawal|intoxication$|toxicity$|overdose|pregnan|neonatal|_state$|dic$|hypertension|hypotension|shock|ketoacidosis|hyperosmolar|_deficiency|_excess|_overload|hypoalbuminemia|azotemia|uremia|nephrotic|nephritic|proteinuria|hematuria|_disorder$|_disease$|myocardial|heart|cardiac|liver|renal|hepatic|pulmonary|gout|iron|b12|folate|vitamin|_risk|surveillance|screening|monitoring|response|effect|_level|_status")
for did, d in D.items():
    if d["classification"].get("entity_kind") != "clinical_entity": continue
    if SYNDROMIC_RX.search(did): continue
    rs = [RU[x] for x in d["rule_ids"] if x in ex_rules and prop(RU[x])
          and not any((l.get("context") or {}).get("exposure_history") or (l.get("context") or {}).get("clinical_suspicion") for l in leaves(RU[x]["expression"]))]
    if not rs: continue
    fs = set().union(*[{l["feature_id"] for l in leaves(r["expression"])} for r in rs])
    if fs and fs <= ROUTINE:
        out["D5"].append((did, d["classification"].get("domains"), sorted(fs)[:5], len(rs), max(r.get("weight", 0) for r in rs)))
# D6
for rid, r in ex_rules.items():
    for l in leaves(r["expression"]):
        if l["feature_id"] not in feats: out["D6"].append((rid, l["feature_id"]))
# D7
PED = {"creatinine": (">", 1.0), "hemoglobin": ("<", 11.0), "alkaline_phosphatase": (">", 130.0), "total_bilirubin": (">", 1.2), "egfr_ckd_epi_creatinine": ("<", 60), "uric_acid": (">", 6.0)}
for rid, r in ex_rules.items():
    ag = set(r["population"].get("age_groups") or [])
    if not ({"neonate", "infant", "child"} & ag) or "neonat" in r["disease_id"] or "infant" in r["disease_id"] or "pediatric" in r["disease_id"]: continue
    for l in leaves(r["expression"]):
        spec = PED.get(l["feature_id"]); v = fnum(l.get("value"))
        if not ({"neonate", "infant"} & ag) and l["feature_id"] not in ("creatinine", "egfr_ckd_epi_creatinine", "alkaline_phosphatase"): continue
        if spec and v is not None and l.get("operator", "").startswith(spec[0]) and (v >= spec[1] if spec[0] == ">" else v <= spec[1]):
            out["D7"].append((rid, l["feature_id"], l.get("operator"), v, sorted(ag)[:3]))
            break
# D8 / D10
for rid, r in ex_rules.items():
    ls = list(leaves(r["expression"]))
    if r["rule_type"] == "diagnostic_criterion" and len(ls) == 1 and ls[0]["feature_id"] in ROUTINE \
            and not r["disease_id"].startswith(("elevated_", "decreased_", "co_", "low_", "high_")) and not re.search(r"_pattern$|emia$|penia$|cytosis$|uria$|philia$|osis$", r["disease_id"]) \
            and (D.get(r["disease_id"]) or {}).get("classification", {}).get("entity_kind") == "clinical_entity":
        if (r.get("specificity") or "") == "specific": out["D8"].append((rid, r["disease_id"], ls[0]["feature_id"]))
        if (r.get("result") or {}).get("diagnosis_allowed"): out["D10"].append((rid, r["disease_id"], ls[0]["feature_id"]))
# D9
for rid, r in ex_rules.items():
    for s in r.get("source_ids") or []:
        if s not in SRC: out["D9"].append((rid, s))

names = {"D1": "sex-blind threshold on sex-dimorphic analyte", "D2": "unit/scale inconsistency (>=100x, same declared unit)",
         "D3": "risk-factor feature used for an acute entity", "D4": "physiologically impossible threshold",
         "D5": "etiologic (non-syndromic) entity proposable from routine analytes only", "D6": "feature_id missing from feature registry",
         "D7": "neonate/infant population on adult threshold", "D8": "specific claimed for single routine-analyte diagnostic rule",
         "D9": "source_id not in guideline_sources", "D10": "single routine analyte with diagnosis_allowed"}
L = [f"# Registry defect scan - {ver} ({len(ex_rules)} executable rules, {len(D)} entities)", "", "| class | description | count | examples |", "|---|---|---:|---|"]
for k in names:
    v = out.get(k, [])
    desc = names[k]
    L.append("| %s | %s | %d | %s |" % (k, desc, len(v), str(v[:3])[:220].replace("|", "/")))
L.append("")
txt = "\n".join(L)
print(txt)
od = os.path.join(R0, "eval", "results")
open(os.path.join(od, "registry_defect_scan_%s.md" % ver), "w").write(txt + "\n")
json.dump(out, open(os.path.join(od, "registry_defect_scan_%s.json" % ver), "w"), indent=0, default=str)

# ---- second-wave classes (added 2026-10-23 evening) ----
out2 = collections.defaultdict(list)
# D13 duplicate executable rules: same disease, same rule_type, identical expression
sig = collections.defaultdict(list)
for rid, r in ex_rules.items():
    sig[(r["disease_id"], r["rule_type"], json.dumps(r["expression"], sort_keys=True))].append(rid)
for k, v in sig.items():
    if len(v) > 1: out2["D13"].append((k[0], v))
# D14 self-defeating pairs: proposing rule on X op a and exclusion rule on X same-direction op b with b <= a (exclusion always co-fires)
for did, d in D.items():
    rs = [RU[x] for x in d["rule_ids"] if x in ex_rules]
    props = [(l["feature_id"], l["operator"], fnum(l["value"])) for r in rs if prop(r) for l in leaves(r["expression"]) if len(list(leaves(r["expression"]))) == 1]
    excl = [(l["feature_id"], l["operator"], fnum(l["value"]), r["rule_id"]) for r in rs if r["rule_type"] == "exclusion_criterion" for l in leaves(r["expression"]) if len(list(leaves(r["expression"]))) == 1]
    for pf, po, pv in props:
        for ef, eo, ev, erid in excl:
            if pf != ef or pv is None or ev is None: continue
            if po in (">", ">=") and eo in (">", ">=") and ev <= pv: out2["D14"].append((did, pf, po, pv, erid, eo, ev))
            if po in ("<", "<=") and eo in ("<", "<=") and ev >= pv: out2["D14"].append((did, pf, po, pv, erid, eo, ev))
# D15 screening weight exceeding the entity's strongest diagnostic weight (inverted evidence hierarchy)
for did, d in D.items():
    rs = [RU[x] for x in d["rule_ids"] if x in ex_rules]
    dw = [r.get("weight", 0) for r in rs if r["rule_type"] == "diagnostic_criterion"]
    sw = [(r["rule_id"], r.get("weight", 0)) for r in rs if r["rule_type"] == "screening"]
    if dw and sw:
        mx = max(dw)
        for rid, w in sw:
            if w > mx: out2["D15"].append((did, rid, w, mx))
# D16 exclusion rules whose single-leaf threshold lies INSIDE the adult reference range (excludes on a normal value)
for rid, r in ex_rules.items():
    if r["rule_type"] != "exclusion_criterion": continue
    ls = list(leaves(r["expression"]))
    if len(ls) != 1: continue
    l = ls[0]; rr = (feats.get(l["feature_id"]) or {}).get("reference_ranges") or []
    g = next((x for x in rr if x.get("sex") in (None, "all") and x.get("low") is not None and x.get("high") is not None), None)
    v = fnum(l.get("value"))
    if g and v is not None and l.get("operator") in (">", ">=") and v < g["high"] * 0.999 and v > g["low"]:
        out2["D16"].append((rid, l["feature_id"], l["operator"], v, (g["low"], g["high"])))
    if g and v is not None and l.get("operator") in ("<", "<=") and v > g["low"] * 1.001 and v < g["high"]:
        out2["D16"].append((rid, l["feature_id"], l["operator"], v, (g["low"], g["high"])))
names2 = {"D13": "duplicate executable rules (same entity/type/expression)", "D14": "exclusion co-fires with its own proposing rule",
          "D15": "screening weight above strongest diagnostic weight", "D16": "single-leaf exclusion threshold inside reference range"}
L2 = ["", "## Second-wave classes", "", "| class | description | count | examples |", "|---|---|---:|---|"]
for k in names2:
    v = out2.get(k, [])
    L2.append("| %s | %s | %d | %s |" % (k, names2[k], len(v), str(v[:3])[:220].replace("|", "/")))
txt2 = "\n".join(L2); print(txt2)
open(os.path.join(od, "registry_defect_scan_%s.md" % ver), "a").write(txt2 + "\n")
out.update(out2); json.dump(out, open(os.path.join(od, "registry_defect_scan_%s.json" % ver), "w"), indent=0, default=str)
