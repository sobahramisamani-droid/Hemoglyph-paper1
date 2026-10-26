"""Before/after comparison of the current engine vs a stored per_stay.json on the first N eICU-demo stays (development set).
python3 eval/dev_delta.py --n 500 --base eval/results/eicu_demo/per_stay.json --out eval/results/run_20261022_v4/dev_delta_n500.json"""
import json,sys,argparse,logging,collections,time; logging.disable(logging.CRITICAL); sys.path.insert(0,"."); sys.path.insert(0,"eval/realdata")
import eval_eicu as ee, analyse_gidlines as ag
ap=argparse.ArgumentParser(); ap.add_argument("--n",type=int,default=500); ap.add_argument("--base",default="eval/results/eicu_demo/per_stay.json"); ap.add_argument("--out",required=True); ap.add_argument("--skip",type=int,default=0)
a=ap.parse_args()
rows=json.load(open(a.base))[a.skip:a.skip+a.n]; G=ee.GROUPS; U={t[0]:t[1] for t in ee.LAB.values() if t}
E=ag.ClinicalRuleEngine(); E._reasoner.max_differential=40
SYN=ee.GROUPS  # (name, ids, key_labs)
def group_rank(diff):
    gp,gr={}, {}
    for rank,d in enumerate(diff,1):
        for g,(nm,ids,labs,_det) in G.items():
            if d["disease_id"] in ids:
                gp[g]=max(gp.get(g,0),d["probability"]); gr.setdefault(g,rank)
    return gp,gr
rec={"old":[0,0],"new":[0,0]}; top5_old=collections.Counter(); top5_new=collections.Counter(); per_g=collections.defaultdict(lambda:[0,0,0]); out=[]
t0=time.time()
for i,r in enumerate(rows):
    vals=eval(r["vals"]) if isinstance(r["vals"],str) else r["vals"]
    obs={k:{"value":float(v),"unit":U.get(k)} for k,v in vals.items() if k in U}
    rep=E.interpret(obs,None,{"age_years":int(r["age"]),"sex_at_birth":r["sex"]}).to_dict()
    diff=rep["differential_diagnosis"]; gp,gr=group_rank(diff)
    for d,p in r["top5"]: top5_old[d]+=1
    for d in diff[:5]: top5_new[d["disease_id"]]+=1
    for g in r["coded"]:
        if g not in G or not any(k in r["labs"] for k in G[g][2]): continue
        o=(r["gr"].get(g) or 99)<=5; n=(gr.get(g) or 99)<=5
        rec["old"][1]+=1; rec["new"][1]+=1; rec["old"][0]+=o; rec["new"][0]+=n
        per_g[g][0]+=1; per_g[g][1]+=o; per_g[g][2]+=n
    out.append({"stay":r["stay"],"coded":r["coded"],"gp":gp,"gr":gr,"top5":[(d["disease_id"],round(d["probability"],3)) for d in diff[:5]]})
    if (i+1)%100==0: print(f"  {i+1} stays {time.time()-t0:.0f}s", flush=True)
json.dump(out,open(a.out,"w"))
L=[f"# dev delta on {len(rows)} eICU-demo stays (skip={a.skip})", f"recall@5 old {rec['old'][0]}/{rec['old'][1]} = {100*rec['old'][0]/max(1,rec['old'][1]):.1f}%  new {rec['new'][0]}/{rec['new'][1]} = {100*rec['new'][0]/max(1,rec['new'][1]):.1f}%", "", "| group | n | old@5 | new@5 |", "|---|---|---|---|"]
for g,(n,o,nw) in sorted(per_g.items(), key=lambda x:-x[1][0]): L.append(f"| {g} | {n} | {o} | {nw} |")
L+=["", "top-5 entity frequency (old -> new), biggest changes:"]
ch=sorted(set(top5_old)|set(top5_new), key=lambda d: -abs(top5_new[d]-top5_old[d]))[:30]
for d in ch: L.append(f"  {d:45s} {top5_old[d]:4d} -> {top5_new[d]:4d}")
txt="\n".join(L); print(txt); open(a.out.replace(".json",".md"),"w").write(txt+"\n")
