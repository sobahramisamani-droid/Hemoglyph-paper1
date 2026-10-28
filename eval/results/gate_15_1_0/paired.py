import json,gzip,os,collections,sys
from scipy.stats import binomtest
O="eval/results/eicu_demo"
def load(s):
    p=f"{O}/per_stay{s}.json"; return json.load(open(p)) if os.path.exists(p) else json.load(gzip.open(p+".gz"))
A=load("_r1500_icu"); B=load("_r1510_icu")
sa=json.load(open(f"{O}/summary_r1500_icu.json")); sb=json.load(open(f"{O}/summary_r1510_icu.json"))
print("n",sa["n_stays"],sb["n_stays"])
for key in ("recall","recall_two_tier","recall_grouped"):
    print(key, {k:(round(sa[key][k]*100,1) if isinstance(sa[key][k],float) else sa[key][k], round(sb[key][k]*100,1) if isinstance(sb[key][k],float) else sb[key][k]) for k in sa[key]})
Bm={r["stay"]:r for r in B}
for field,name in (("gr","flat"),("gr3","grouped")):
    for k in (1,3,5,10):
        g=l=0; drv=collections.Counter()
        for ra in A:
            rb=Bm[ra["stay"]]
            for lab in ra["coded"]:
                a=ra[field].get(lab); b=rb[field].get(lab)
                ha=a is not None and a<=k; hb=b is not None and b<=k
                if hb and not ha: g+=1; drv[lab]+=1
                if ha and not hb: l+=1; drv[lab]-=1
        p=binomtest(g,g+l).pvalue if g+l else 1.0
        print(f"{name}@{k}: +{g} -{l} p={p:.3g} drivers={drv.most_common(3)} {drv.most_common()[-3:]}")
def co(rows): 
    t=sum(len(r["top5"]) for r in rows); c=sum(1 for r in rows for e in r["top5"] if e[0].startswith("co_")); return c,t
print("co_ top5",co(A),co(B)); print("distinct top5",len({e[0] for r in A for e in r["top5"]}),len({e[0] for r in B for e in r["top5"]}))
