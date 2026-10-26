#!/usr/bin/env python3
"""4-way eICU comparison (SAP Amendment 14 attribution analysis):
  13.4.2 original (legacy units, blood gases dropped)      -> summary_v1342.json
  v14 logic+registry, legacy units  (control A)            -> summary_v1400_legacyunits.json
  v6 engine + registry 13.4.2, fixed units (control B)     -> summary_v1342_v6engine.json
  v14 logic+registry, fixed units                          -> summary_v1400.json
"""
import json, os, gzip, collections
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eicu_demo")
ARMS = [("13.4.2 original (legacy units)", "_v1342"), ("v14, legacy units (ctrl A)", "_v1400_legacyunits"),
        ("v6 engine + reg 13.4.2, fixed units (ctrl B)", "_v1342_v6engine"), ("v14, fixed units", "_v1400")]
def load(sfx):
    p = os.path.join(OUT, f"summary{sfx}.json")
    return json.load(open(p)) if os.path.exists(p) else None
rows = []
for name, sfx in ARMS:
    s = load(sfx)
    if not s: rows.append((name, None)); continue
    rec = s["recall"]; rec2 = s.get("recall_two_tier") or {}
    g = s["groups"]
    def r5(k):
        x = g.get(k) or {}
        return x.get("recall5") or x.get("recall@5") or x.get("r5")
    pc = lambda v: (v[0] / v[1]) if isinstance(v, list) and v[1] else v
    rows.append((name, dict(top3=pc(rec.get("3")), top5=pc(rec.get("5")), top10=pc(rec.get("10")),
                            tt5=pc(rec2.get("5")), support=s.get("support"),
                            ckd=r5("chronic_kidney_disease"), renal=r5("renal_impairment"), anemia=r5("anemia"), sepsis=r5("sepsis"))))
print("| arm | top-3 | top-5 | top-10 | two-tier top-5 | CKD r@5 | renal r@5 | anemia r@5 | sepsis r@5 |")
print("|---|---|---|---|---|---|---|---|---|")
for name, d in rows:
    if d is None: print(f"| {name} | (missing) |"); continue
    f = lambda v: "—" if v is None else (f"{100*v:.1f}%" if isinstance(v, float) and v <= 1 else str(v))
    print(f"| {name} | {f(d['top3'])} | {f(d['top5'])} | {f(d['top10'])} | {f(d['tt5'])} | {f(d['ckd'])} | {f(d['renal'])} | {f(d['anemia'])} | {f(d['sepsis'])} |")
