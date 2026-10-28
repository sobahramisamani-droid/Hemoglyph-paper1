"""Reviewer round-2 metrics on the frozen v7 eICU run (labs-only, 2,314 stays):
precision@k / F1@k / NDCG@k at the label-group level, alert burden, per-group PPV vs problem list,
prevalence-ranking baseline, and stay-cluster bootstrap CIs. Reads per_stay_v7.json.gz only (no engine)."""
import json, gzip, re, ast, math, numpy as np, collections as C
ROOT="/home/user/Hemoglyph"; OUT=f"{ROOT}/eval/results/eicu_demo"
src=open(f"{ROOT}/eval/realdata/eval_eicu.py").read()
GROUPS=ast.literal_eval(re.search(r"^GROUPS\s*=\s*(\{.*?^\})",src,re.S|re.M).group(1))
B=json.load(gzip.open(f"{OUT}/per_stay_v7.json.gz","rt"))
def evaluable(r,g): return g in GROUPS and any(k in r["labs"] for k in GROUPS[g][2])
prev=C.Counter(g for r in B for g in r["coded"] if evaluable(r,g)); order=[g for g,_ in prev.most_common()]
K=(3,5,10); rng=np.random.default_rng(7); NB=2000
def per_stay(r, ranks):
    """ranks: dict group->rank (1-based) for the engine's flat list. returns dict of per-stay numerators for each k"""
    coded=set(g for g in r["coded"] if evaluable(r,g))
    out={}
    for k in K:
        pred=[g for g,rk in ranks.items() if rk<=k and evaluable(r,g)]
        hits=sum(1 for g in pred if g in coded)
        dcg=sum(1/math.log2(rk+1) for g,rk in ranks.items() if rk<=k and g in coded)
        idcg=sum(1/math.log2(i+2) for i in range(min(k,len(coded))))
        out[k]=dict(pred=len(pred),hits=hits,coded=len(coded),ndcg=(dcg/idcg if idcg>0 else None))
    return out
def agg(rows):
    res={}
    for k in K:
        P=sum(x[k]["pred"] for x in rows); H=sum(x[k]["hits"] for x in rows); Cn=sum(x[k]["coded"] for x in rows)
        nd=[x[k]["ndcg"] for x in rows if x[k]["ndcg"] is not None]
        prec=H/P if P else float("nan"); rec=H/Cn if Cn else float("nan"); f1=2*prec*rec/(prec+rec) if prec+rec>0 else 0
        res[k]=dict(precision=100*prec,recall=100*rec,f1=100*f1,ndcg=100*np.mean(nd) if nd else float("nan"),asserted_per_stay=P/len(rows))
    return res
def boot(rows,key,k):
    idx=rng.integers(0,len(rows),(NB,len(rows))); vals=[]
    arr=np.array([[x[k]["pred"],x[k]["hits"],x[k]["coded"],(x[k]["ndcg"] if x[k]["ndcg"] is not None else np.nan)] for x in rows])
    for i in idx:
        a=arr[i]; P,H,Cn=a[:,0].sum(),a[:,1].sum(),a[:,2].sum()
        if key=="precision": vals.append(100*H/P)
        elif key=="recall": vals.append(100*H/Cn)
        elif key=="f1": p,r_=H/P,H/Cn; vals.append(100*2*p*r_/(p+r_))
        elif key=="ndcg": vals.append(100*np.nanmean(a[:,3]))
    return np.percentile(vals,[2.5,97.5])
eng=[per_stay(r,r["gr"]) for r in B]
def prev_ranks(r):
    rk={}; i=0
    for g in order:
        if evaluable(r,g): i+=1; rk[g]=i
    return rk
base=[per_stay(r,prev_ranks(r)) for r in B]
L=[len(r["gr"]) for r in B]
E=agg(eng); Pb=agg(base)
lines=["# Reviewer round-2 metrics — engine v7, eICU-CRD demo (2,314 stays, labs only), label-group level","",
"Prediction set at k = label groups whose best flat-list entry has rank ≤ k and whose key analyte is present (the same evaluability rule used for recall). Reference = clinician problem list mapped to 31 groups (admission-level; incompleteness means 'false positives' are an upper bound on true false positives). CIs: stay-cluster bootstrap, 2,000 resamples.","",
"| metric | k=3 | k=5 | k=10 |","|---|---:|---:|---:|"]
for key in ("precision","recall","f1","ndcg"):
    cells=[]
    for k in K:
        lo,hi=boot(eng,key,k); cells.append(f"{E[k][key]:.1f} ({lo:.1f}–{hi:.1f})")
    lines.append(f"| engine v7 {key}@k (%) | "+" | ".join(cells)+" |")
for key in ("precision","recall","f1","ndcg"):
    lines.append(f"| prevalence-ranking baseline {key}@k (%) | "+" | ".join(f"{Pb[k][key]:.1f}" for k in K)+" |")
lines.append("| engine: label-group assertions per stay | "+" | ".join(f"{E[k]['asserted_per_stay']:.2f}" for k in K)+" |")
lines+=["",f"Alert burden: mean {np.mean(L):.1f} (median {np.median(L):.0f}, IQR {np.percentile(L,25):.0f}–{np.percentile(L,75):.0f}) label-group entries in the full flat differential (max list length 25); mean flat list carries {np.mean([len(r['top5']) for r in B]):.1f} entries in the top-5.", ""]
lines+=["## Per-group PPV and sensitivity at k = 5 (problem-list reference)","","| group | coded (evaluable) | asserted@5 | PPV@5 (%) | sensitivity@5 (%) | prevalence baseline sens@5 (%) |","|---|---:|---:|---:|---:|---:|"]
pg={}
for r,rk in zip(B,[x["gr"] for x in B]):
    coded=set(g for g in r["coded"] if evaluable(r,g))
    for g in GROUPS:
        if not evaluable(r,g): continue
        a=pg.setdefault(g,[0,0,0,0]); p=rk.get(g,999)<=5; c=g in coded
        a[0]+=c; a[1]+=p; a[2]+=p and c; a[3]+=(prev_ranks(r).get(g,999)<=5) and c
for g,(c,p,tp,bp) in sorted(pg.items(),key=lambda x:-x[1][0]):
    if c<10: continue
    lines.append(f"| {g} | {c} | {p} | {100*tp/p if p else float('nan'):.0f} | {100*tp/c:.0f} | {100*bp/c:.0f} |")
lines+=["","Interpretation: PPV against an admission problem list is a lower bound (uncoded but present conditions count as false positives); it is reported to quantify alert burden, not accuracy."]
open(f"{OUT}/reviewer_r2_metrics_v7.md","w").write("\n".join(lines)+"\n"); print("\n".join(lines))

# the problem list nevertheless satisfy a fixed guideline laboratory criterion in the same panel; panel_supported_metric.CRIT,
import sys; sys.path.insert(0, f"{ROOT}/eval/realdata")
from panel_supported_metric import CRIT
tot=hit=crit_pos=crit_neg=crit_na=0; pg2={}
for r in B:
    coded=set(g for g in r["coded"] if evaluable(r,g))
    for g,rk in r["gr"].items():
        if rk>5 or not evaluable(r,g): continue
        tot+=1; a=pg2.setdefault(g,[0,0,0,0,0]); a[0]+=1
        if g in coded: hit+=1; a[1]+=1; continue
        f=CRIT.get(g); res=None if f is None else f(r["vals"], r)
        if res is True: crit_pos+=1; a[2]+=1
        elif res is False: crit_neg+=1; a[3]+=1
        else: crit_na+=1; a[4]+=1
L2=["","## Criterion-supported precision at k = 5 (addendum 2026-10-26)","",
f"Of {tot:,} label-group assertions in the top-5, {hit:,} ({100*hit/tot:.1f}%) are on the problem list (= precision@5). Of the remaining {tot-hit:,}: {crit_pos:,} ({100*crit_pos/tot:.1f}% of all assertions) satisfy the group's fixed laboratory criterion in the same panel (laboratory-supported but uncoded), {crit_neg:,} ({100*crit_neg/tot:.1f}%) do not satisfy it (criterion-negative: the closest thing to a verified false positive without a clinician), and {crit_na:,} ({100*crit_na/tot:.1f}%) belong to groups without a single-analyte criterion or lack the criterion analyte.",
f"Upper-bound precision (coded OR criterion-positive) = {100*(hit+crit_pos)/tot:.1f}%; lower bound = {100*hit/tot:.1f}%; criterion-negative share = {100*crit_neg/tot:.1f}%.","",
"| group | asserted@5 | coded | uncoded, criterion-positive | uncoded, criterion-negative | no criterion / analyte |","|---|---:|---:|---:|---:|---:|"]
for g,a in sorted(pg2.items(),key=lambda x:-x[1][0]):
    if a[0]>=30: L2.append(f"| {g} | {a[0]} | {a[1]} | {a[2]} | {a[3]} | {a[4]} |")
open(f"{OUT}/reviewer_r2_metrics_v7.md","a").write("\n".join(L2)+"\n"); print("\n".join(L2[:6]))
