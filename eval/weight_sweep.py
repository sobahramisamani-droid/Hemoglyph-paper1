"""Fusion-weight sweep on an eICU-demo development subset. Weights are patched in place; the engine is otherwise frozen.
python3 eval/weight_sweep.py --n 300 --out eval/results/run_20261022_v4/weight_sweep.md"""
import json,sys,argparse,logging,collections,time; logging.disable(logging.CRITICAL); sys.path.insert(0,"."); sys.path.insert(0,"eval/realdata")
import eval_eicu as ee, analyse_gidlines as ag, numpy as np
from eval_nhanes import auroc
ap=argparse.ArgumentParser(); ap.add_argument("--n",type=int,default=300); ap.add_argument("--skip",type=int,default=0); ap.add_argument("--out",required=True); a=ap.parse_args()
rows=json.load(open("eval/results/eicu_demo/per_stay.json"))[a.skip:a.skip+a.n]; G=ee.GROUPS; U={t[0]:t[1] for t in ee.LAB.values() if t}
CONFIGS={
 "A default .35/.25/.20/.10/.10": dict(rule_engine=.35,bayesian=.25,fuzzy=.20,knowledge_graph=.10,risk_models=.10),
 "B rule-heavy .45/.15/.15/.10/.15": dict(rule_engine=.45,bayesian=.15,fuzzy=.15,knowledge_graph=.10,risk_models=.15),
 "C bayes-light .40/.15/.25/.10/.10": dict(rule_engine=.40,bayesian=.15,fuzzy=.25,knowledge_graph=.10,risk_models=.10),
 "D fuzzy-light .40/.25/.10/.10/.15": dict(rule_engine=.40,bayesian=.25,fuzzy=.10,knowledge_graph=.10,risk_models=.15),
 "E balanced-prior .30/.30/.20/.10/.10": dict(rule_engine=.30,bayesian=.30,fuzzy=.20,knowledge_graph=.10,risk_models=.10),
}
E=ag.ClinicalRuleEngine(); E._reasoner.max_differential=40
base=dict(ag.MODEL_WEIGHTS)
L=[f"# fusion-weight sweep on {len(rows)} eICU-demo stays (skip={a.skip}); engine otherwise frozen (v4)","","| config | recall@5 | recall@10 | mean AUROC (groups n>=5) | mean #entities p>=0.5 | sec/stay |","|---|---|---|---|---|---|"]
for name,w in CONFIGS.items():
    ag.MODEL_WEIGHTS.clear(); ag.MODEL_WEIGHTS.update(w); ag.WEIGHT_PROFILES["default"]=ag.MODEL_WEIGHTS
    rec5=[0,0]; rec10=[0,0]; nconf=[]; pg=collections.defaultdict(lambda:[[],[]]); t0=time.time()
    for r in rows:
        vals=eval(r["vals"]) if isinstance(r["vals"],str) else r["vals"]
        obs={k:{"value":float(v),"unit":U.get(k)} for k,v in vals.items() if k in U}
        diff=E.interpret(obs,None,{"age_years":int(r["age"]),"sex_at_birth":r["sex"]}).to_dict()["differential_diagnosis"]
        nconf.append(sum(1 for d in diff if d["probability"]>=.5))
        gp,gr={},{}
        for rank,d in enumerate(diff,1):
            for g,(nm,ids,labs,_x) in G.items():
                if d["disease_id"] in ids: gp[g]=max(gp.get(g,0),d["probability"]); gr.setdefault(g,rank)
        for g in G:
            if not any(k in r["labs"] for k in G[g][2]): continue
            y=g in r["coded"]; pg[g][0 if y else 1].append(gp.get(g,0.0))
            if y:
                rec5[1]+=1; rec10[1]+=1; rec5[0]+=(gr.get(g) or 99)<=5; rec10[0]+=(gr.get(g) or 99)<=10
    aus=[auroc(np.array([1]*len(p)+[0]*len(n)),np.array(p+n)) for g,(p,n) in pg.items() if len(p)>=5 and len(n)>=5]
    L.append(f"| {name} | {100*rec5[0]/rec5[1]:.1f}% | {100*rec10[0]/rec10[1]:.1f}% | {np.mean(aus):.3f} (k={len(aus)}) | {np.mean(nconf):.2f} | {(time.time()-t0)/len(rows):.2f} |")
    print(L[-1], flush=True)
ag.MODEL_WEIGHTS.clear(); ag.MODEL_WEIGHTS.update(base)
open(a.out,"w").write("\n".join(L)+"\n")
