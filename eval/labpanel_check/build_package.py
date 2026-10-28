#!/usr/bin/env python3
"""Build the LabPanel-Check conformance package from the frozen black-box benchmark (one-off, repository-dependent).

Everything the *scorer* needs is written to this directory as self-contained files; `score.py` has no dependency on the
engine or on the rest of the repository.

Outputs
  panels.json.gz                 all panels, one record per panel id (see README for the id scheme)
  label_map.json                 31 diagnosis groups -> {entity ids (engine vocabulary), regex (free-text vocabulary)},
                                 the renal union, the P5 redundant-analyte table and the P6 benign-word list
  reads_reference_llm.json.gz    the stored blind readings of the unnamed frontier LLM (2026-10-21..27), re-keyed by panel id
  reads_reference_engine.json.gz Hemoglyph working-tree engine readings on the identical panels (live run)
  MANIFEST.sha256                hashes of the above

No label, no outcome and no new LLM call is involved; panels come from the eICU-CRD demo and NHANES 2017-18 public files.
"""
from __future__ import annotations
import os, sys, json, gzip, ast, hashlib, logging
logging.disable(logging.CRITICAL)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT, os.path.join(ROOT, "eval", "realdata"), os.path.join(ROOT, "eval", "baselines"), os.path.join(ROOT, "eval", "blackbox")):
    sys.path.insert(0, p)
from eval_eicu import GROUPS  # noqa: E402
from llm_zero_shot import SYN  # noqa: E402
BB = os.path.join(ROOT, "eval", "blackbox")
P = lambda x: ast.literal_eval(x) if isinstance(x, str) else x

# ---- conventional-unit twin builder from the frozen generator (same code path as score_property_panels.py)
_gen = open(os.path.join(BB, "make_property_panels.py")).read()
_gns = {"__file__": os.path.join(BB, "make_property_panels.py")}
exec(compile(_gen[:_gen.index("# P2 unit invariance")], "gen", "exec"), _gns)
conv_panel = lambda stay: _gns["panel"](stay)

# ---- original blind LLM readings (b8 / b3 / b4) exactly as the frozen scorer loads them
_src = open(os.path.join(ROOT, "eval/baselines/b8_v7_cluster.py")).read()
_b = _src.split("def main():")[0].replace('json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))',
                                            'json.load(gzip.open(os.path.join(R, "b8_blind_panels_n240.json.gz"),"rt"))')
_ns = {"__file__": os.path.join(ROOT, "eval/baselines/b8_v7_cluster.py")}
exec(compile(_b, "b8", "exec"), _ns)
llm_orig = {str(s[0]): s[3] for s in _ns["stays"]}

panels, llm = {}, {}

def put(pid, rec, **meta):
    rec = dict(rec); rec.update(meta); rec["id"] = pid
    assert pid not in panels, pid
    panels[pid] = rec

def entries(x):
    return [{"name": str(d.get("name", "")), "probability": float(d.get("probability", 0.0))} for d in x]

# P2 / P3 and their shared conventional reference
p2 = json.load(open(os.path.join(BB, "panels_P2_units.json")))
p3 = json.load(open(os.path.join(BB, "panels_P3_presentation.json")))
r2 = json.load(open(os.path.join(BB, "reads_llm_P2_units.json")))
r3 = json.load(open(os.path.join(BB, "reads_llm_P3_presentation.json")))
for p in p2:
    s = p["stay"]
    put(f"REF:{s}", conv_panel(s), property="REF", source="eICU-CRD demo v2.0.1", role="conventional-unit original (reference for P2 and P3)")
    put(f"P2:{s}", p, property="P2", source="eICU-CRD demo v2.0.1", reference=f"REF:{s}")
    llm[f"REF:{s}"] = entries(llm_orig[s]); llm[f"P2:{s}"] = entries(r2[s])
for p in p3:
    s = p["stay"]; put(f"P3:{s}", p, property="P3", source="eICU-CRD demo v2.0.1", reference=f"REF:{s}"); llm[f"P3:{s}"] = entries(r3[s])

# P4 ladders
p4 = json.load(open(os.path.join(BB, "panels_P4_monotonic.json"))); r4 = json.load(open(os.path.join(BB, "reads_llm_P4_monotonic.json")))
for p in p4:
    s, lad = p["stay"], p["ladder"]; pid = f"P4:{s}:{lad:.1f}"
    put(pid, {k: v for k, v in p.items() if k != "ladder"}, property="P4", source="eICU-CRD demo v2.0.1", ladder=lad, ladder_id=f"P4:{s}")
    llm[pid] = entries(r4[f"{s}@{lad}"])

# P5 absent analyte
p5 = json.load(open(os.path.join(BB, "panels_P5_absent.json"))); r5 = json.load(open(os.path.join(BB, "reads_llm_P5_absent.json")))
for p in p5:
    s = p["stay"]; put(f"P5:{s}", p, property="P5", source="eICU-CRD demo v2.0.1"); llm[f"P5:{s}"] = entries(r5[s])

# P6 healthy / reference-positive NHANES adults (B5 blind test)
hid = json.load(gzip.open(os.path.join(ROOT, "eval/results/nhanes_2017/b5_hidden.json.gz"), "rt"))
r6 = json.load(open(os.path.join(ROOT, "eval/results/nhanes_2017/b5_llm_blind.json")))
for h in hid:
    pid = f"P6:{h['idx']:02d}"
    rec = {"stay": str(h["seqn"]), "age": h["age"], "sex": h["sex"],
           "panel": [{"analyte": a, "value": float(v["value"]), "unit": v["unit"]} for a, v in h["obs"].items()]}
    pos = [k for k, v in h["ref"].items() if v]
    put(pid, rec, property="P6", source="NHANES 2017-18", healthy=bool(h["healthy"]), reference_positive=pos)
    llm[pid] = [{"name": str(n), "probability": float(p)} for n, p in r6.get(str(h["idx"]), [])]

# ---- label map (black-box vocabulary)
label_map = {
    "groups": {g: {"entities": sorted(ents), "regex": SYN.get(g, "(?!)")} for g, (_, ents, _, _) in GROUPS.items()},
    "renal_union": ["acute_kidney_injury", "renal_impairment", "chronic_kidney_disease"],
    "p5_redundant": {"hemoglobin": ["hematocrit"], "troponin_i": ["creatine_kinase_mb", "troponin_t"], "bicarbonate": ["anion_gap", "arterial_ph", "base_excess"]},
    "p6_benign_words": ["normal", "healthy", "no significant", "unremarkable", "prediabetes", "borderline", "mild", "low risk"],
    "p6_detection": {"diabetes": ["diabetes", "hyperglycemia", "prediabetes"], "ckd": ["chronic kidney", "ckd", "renal", "kidney", "albuminuria"],
                     "anemia": ["anemia", "anaemia"], "iron_deficiency": ["iron"], "hypercholesterolemia": ["cholesterol", "hyperlipid", "dyslipid", "lipid"]},
}
assert all(g in SYN for g in GROUPS), [g for g in GROUPS if g not in SYN]

# ---- engine reference readings (live, working-tree engine)
import analyse_gidlines as ag  # noqa: E402
E = ag.ClinicalRuleEngine()
eng = {}
for pid, rec in panels.items():
    E._reasoner.max_differential = 40 if rec["property"] == "P6" else 15
    obs = {it["analyte"]: {"value": float(it["value"]), "unit": it["unit"]} for it in rec["panel"]}
    rep = E.interpret(obs, None, {"age_years": int(float(rec["age"])), "sex_at_birth": rec["sex"]}).to_dict()
    eng[pid] = [{"id": d["disease_id"], "name": d["disease_id"], "probability": float(d["probability"]), "tier": E._reasoner.tier_of(d["disease_id"])}
                for d in rep["differential_diagnosis"]]
    print(pid, len(eng[pid]), flush=True)

def dump(name, obj):
    path = os.path.join(HERE, name)
    if name.endswith(".gz"):
        with gzip.GzipFile(path, "wb", mtime=0) as f:  # mtime=0 -> byte-reproducible archive
            f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    else:
        json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

dump("panels.json.gz", panels); dump("label_map.json", label_map)
dump("reads_reference_llm.json.gz", llm); dump("reads_reference_engine.json.gz", eng)
man = []
for name in ("panels.json.gz", "label_map.json", "reads_reference_llm.json.gz", "reads_reference_engine.json.gz", "score.py", "spec.json"):
    p = os.path.join(HERE, name)
    if os.path.exists(p):
        man.append(f"{hashlib.sha256(open(p, 'rb').read()).hexdigest()}  {name}")
open(os.path.join(HERE, "MANIFEST.sha256"), "w").write("\n".join(man) + "\n")
print(f"panels {len(panels)}  llm reads {len(llm)}  engine reads {len(eng)}")
