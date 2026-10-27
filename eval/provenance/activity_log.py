#!/usr/bin/env python3
"""Phase A of eval/provenance/PROTOCOL.md: label-free activity log of executable rules on real panels.

Usage: python3 eval/provenance/activity_log.py --corpus eicu|nhanes_J|nhanes_I [--n N]
Writes eval/provenance/activity_<corpus>.json.gz: {rule_id: [fired, contrib10, contrib5]} plus meta. Resumable.
"""
import argparse, gzip, json, os, sys, time, random, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata"))
POS = {"criterion_met", "possible_pattern", "screening_positive", "compatible_pattern", "urgent_pattern"}

def cases_eicu():
    from eval_eicu import LAB
    unit = {v[0]: v[1] for v in LAB.values() if v}
    rows = json.load(gzip.open(os.path.join(ROOT, "eval/results/eicu_demo/per_stay_v7.json.gz"), "rt"))
    for r in rows:
        vals = json.loads(r["vals"]) if isinstance(r["vals"], str) else r["vals"]
        obs = {k: {"value": float(v), "unit": unit.get(k, "")} for k, v in vals.items() if v is not None}
        yield str(r["stay"]), obs, {"age_years": int(r["age"]), "sex_at_birth": r["sex"], "encounter": "icu"}

def cases_nhanes(cycle, n, seed=20261027):
    import pandas as pd, eval_nhanes as en
    sfx = {"J": "_J", "I": "_I"}[cycle]
    data = os.path.join(ROOT, "eval/realdata", {"J": "nhanes_2017", "I": "nhanes_2015"}[cycle])
    def rd(f):
        p = os.path.join(data, f[:-2] + sfx + ".csv.gz")
        return pd.read_csv(p) if os.path.exists(p) else None
    df = rd("DEMO_J")[["SEQN", "RIAGENDR", "RIDAGEYR", "RIDEXPRG"]]
    for f in ["BIOPRO_J", "CBC_J", "GHB_J", "GLU_J", "ALB_CR_J", "FERTIN_J", "TCHOL_J", "HDL_J", "TRIGLY_J", "FETIB_J"]:
        t = rd(f)
        if t is None: continue
        t = t[[c for c in t.columns if c == "SEQN" or c in en.MAP]]
        df = df.merge(t, on="SEQN", how="left")
    df = df[(df.RIDAGEYR >= 18) & df.LBXSCR.notna() & df.LBXHGB.notna()].copy()
    df = df[df.RIDEXPRG.fillna(0) != 1].reset_index(drop=True)
    idx = list(range(len(df))); random.Random(seed).shuffle(idx)
    for i in idx[:n]:
        row = df.iloc[i]; obs = {}
        for var, (fid, u) in en.MAP.items():
            v = row.get(var)
            if v is None or (isinstance(v, float) and math.isnan(v)) or fid in obs: continue
            obs[fid] = {"value": float(v), "unit": u}
        if len(obs) < 8: continue
        yield str(int(row.SEQN)), obs, {"age_years": int(row.RIDAGEYR), "sex_at_birth": "female" if row.RIAGENDR == 2 else "male", "encounter": "community"}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--corpus", required=True); ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    out = os.path.join(HERE, f"activity_{a.corpus}.json.gz")
    state = json.load(gzip.open(out, "rt")) if os.path.exists(out) else {"meta": {"corpus": a.corpus, "done": [], "n_cases": 0}, "counts": {}}
    done = set(state["meta"]["done"]); counts = collections.defaultdict(lambda: [0, 0, 0], {k: list(v) for k, v in state["counts"].items()})
    import analyse_gidlines as ag
    E = ag.ClinicalRuleEngine()
    gen = cases_eicu() if a.corpus == "eicu" else cases_nhanes(a.corpus.split("_")[1], a.n or (1000 if a.corpus.endswith("J") else 500))
    t0 = time.time(); k = 0
    for cid, obs, patient in gen:
        if cid in done: continue
        try:
            rep = E.interpret(obs, None, patient).to_dict()
        except Exception as ex:
            print("ERR", cid, ex, flush=True); continue
        dd = rep.get("differential_diagnosis") or []
        top10 = {d["disease_id"] for d in dd if d.get("rank", 99) <= 10}; top5 = {d["disease_id"] for d in dd if d.get("rank", 99) <= 5}
        for it in rep.get("interpretations") or []:
            if it.get("status") in POS:
                c = counts[it["rule_id"]]; c[0] += 1
                if it["disease_id"] in top10: c[1] += 1
                if it["disease_id"] in top5: c[2] += 1
        done.add(cid); k += 1
        if k % 50 == 0:
            state = {"meta": {"corpus": a.corpus, "done": sorted(done), "n_cases": len(done)}, "counts": dict(counts)}
            json.dump(state, gzip.open(out, "wt")); print(f"{a.corpus}: {len(done)} cases, {len(counts)} rules fired, {(time.time()-t0)/k:.2f} s/case", flush=True)
    state = {"meta": {"corpus": a.corpus, "done": sorted(done), "n_cases": len(done)}, "counts": dict(counts)}
    json.dump(state, gzip.open(out, "wt")); print("DONE", a.corpus, len(done), len(counts), flush=True)

if __name__ == "__main__":
    main()
