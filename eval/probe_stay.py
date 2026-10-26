"""Probe the current engine on eICU-demo stays: python3 eval/probe_stay.py STAY [STAY...] [--why DX]"""
import json,sys,logging; logging.disable(logging.CRITICAL); sys.path.insert(0,"."); sys.path.insert(0,"eval/realdata")
import eval_eicu as ee, analyse_gidlines as ag
args=[a for a in sys.argv[1:] if not a.startswith("--")]; why=sys.argv[sys.argv.index("--why")+1] if "--why" in sys.argv else None
rows={str(r["stay"]):r for r in json.load(open("eval/results/eicu_demo/per_stay.json"))}
U={t[0]:t[1] for t in ee.LAB.values() if t}; E=ag.ClinicalRuleEngine(); E._reasoner.max_differential=40
for s in args:
    r=rows[s]; vals=eval(r["vals"]) if isinstance(r["vals"],str) else r["vals"]
    obs={k:{"value":float(v),"unit":U.get(k)} for k,v in vals.items() if k in U}
    rep=E.interpret(obs,None,{"age_years":int(r["age"]),"sex_at_birth":r["sex"]}).to_dict()
    print(f"\n== {s} {r['age']}{r['sex'][0]} coded={r['coded']}\n   vals:", {k:v for k,v in vals.items()})
    print("   top12:", [(d["disease_id"],round(d["probability"],2)) for d in rep["differential_diagnosis"][:12]])
    print("   ESL:", [(x["syndrome_id"]) for x in rep["expert_syndromes"]])
    if why:
        for d in rep["differential_diagnosis"]:
            if d["disease_id"]==why: print("   WHY", json.dumps({k:v for k,v in d.items() if k not in("disease_id",)}, ensure_ascii=False, default=str)[:1500])
