"""Dev-only error audit (eICU per_stay) for engine v7 design: re-run stays whose coded group sits at rank 6-10 and
describe what occupies the top-5 (tier, finding?, explained?, critical?, p). No labels are fed to the engine."""
import json, gzip, sys, os, collections, logging, random
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); sys.path.insert(0,os.path.join(ROOT,'eval','realdata'))
logging.disable(50)
import analyse_gidlines as ag, eval_eicu as ee
UNIT={v[0]:v[1] for v in ee.LAB.values() if v}
d=json.load(gzip.open(os.path.join(ROOT,'eval/results/eicu_demo/per_stay_v1410.json.gz')))
sel=[r for r in d if any(6<=r['gr'].get(g,99)<=10 for g in r['coded'])]
random.Random(1).shuffle(sel); sel=sel[:int(sys.argv[1]) if len(sys.argv)>1 else 120]
E=ag.ClinicalRuleEngine(); E._reasoner.max_differential=40
occ=collections.Counter(); kinds=collections.Counter(); gap=[]; rows=[]
for r in sel:
    obs={f:{'value':v,'unit':UNIT.get(f,'')} for f,v in r['vals'].items() if f in UNIT}
    pt={'age_years':int(r['age']),'sex_at_birth':r['sex'],'encounter':'icu'}
    rep=E.interpret(obs,None,pt).to_dict(); diff=rep['differential_diagnosis']
    ids=[x['disease_id'] for x in diff]
    for g in r['coded']:
        rk=r['gr'].get(g,99)
        if not 6<=rk<=10: continue
        acc=ee.GROUPS[g][1]
        tgt=next((x for x in diff if x['disease_id'] in acc),None)
        if not tgt: continue
        for x in diff[:5]:
            k=('F' if E._reasoner._is_finding(x['disease_id']) else 'D')+('/expl' if x.get('explained_by') else '')+('/crit' if x.get('critical') else '')
            occ[x['disease_id']]+=1; kinds[k]+=1
        gap.append(diff[4]['probability']-tgt['probability'])
        rows.append((r['stay'],g,tgt['disease_id'],round(tgt['probability'],2),tgt.get('tier'),tgt.get('evidence_state'),[(x['disease_id'],round(x['probability'],2),x.get('tier'),x.get('explained_by')) for x in diff[:5]]))
print('n cases',len(rows)); print('top5 kinds',kinds.most_common())
print('occupants',occ.most_common(25))
import statistics; print('gap p5-target median',statistics.median(gap))
print('target tier/state', collections.Counter((x[4],x[5]) for x in rows).most_common(8))
for x in rows[:40]: print(x)
