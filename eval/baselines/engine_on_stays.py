"""Re-run the current engine on a list of eICU-demo stays taken from a frozen per_stay.json.

python3 eval/baselines/engine_on_stays.py --stays eval/results/eicu_demo/llm_agent_b3_n100.json \
    --per-stay eval/results/eicu_demo_v1_frozen_origmap/per_stay.json --out eval/results/eicu_demo/b3_stays_engine_v3_n100.json
`--stays` may be a B3 json (list of {stay,...}) or a plain json list of ints.  Prints recall@5 of the stored
(v1) ranks and of the current engine on the same coded labels.
"""
import argparse, json, sys, time, logging, pathlib
logging.disable(logging.CRITICAL)
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "eval/realdata"))
import eval_eicu as ee, analyse_gidlines as ag

a = argparse.ArgumentParser()
a.add_argument("--stays", required=True); a.add_argument("--per-stay", required=True); a.add_argument("--out", required=True)
a = a.parse_args()
st = json.load(open(a.stays))
stays = [int(x["stay"]) if isinstance(x, dict) else int(x) for x in (st if isinstance(st, list) else st.get("rows", st.get("stays")))]
rows = {r["stay"]: r for r in json.load(open(a.per_stay))}
U = {t[0]: t[1] for t in ee.LAB.values() if t}
E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
out = []; hit = tot = hit_old = 0; t0 = time.time()
for sid in stays:
    r = rows[sid]
    obs = {k: {"value": float(v), "unit": U.get(k)} for k, v in r["vals"].items() if k in U}
    rep = E.interpret(obs, None, {"age_years": int(r["age"]), "sex_at_birth": r["sex"]}).to_dict()
    dd = rep["differential_diagnosis"]; gp, gr = {}, {}
    for g, (_, ids, _, _) in ee.GROUPS.items():
        for d in dd:
            if d["disease_id"] in ids:
                pr = float(d["probability"]); gp[g] = max(gp.get(g, 0), pr); gr.setdefault(g, int(d["rank"]))
    for g in r["coded"]:
        if g not in ee.GROUPS: continue
        tot += 1; hit += gr.get(g, 99) <= 5; hit_old += r["gr"].get(g, 99) <= 5
    out.append({"stay": sid, "age": r["age"], "sex": r["sex"], "vals": r["vals"], "labs": r["labs"], "coded": r["coded"], "gp": gp, "gr": gr,
                "top5": [(d["disease_id"], round(float(d["probability"]), 3)) for d in dd[:5]]})
print(f"n_stays={len(stays)} n_labels={tot}  recall@5 stored(v1)={hit_old/tot:.3f}  current={hit/tot:.3f}  ({time.time()-t0:.0f}s)")
json.dump(out, open(a.out, "w"))
