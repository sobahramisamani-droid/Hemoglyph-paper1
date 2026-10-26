"""Prompt-sensitivity of the blind LLM arm on the 40-panel test-retest subset: P1 read 1, P1 read 2, P2 (alternative prompt), engine v5.1 (stored) and engine v7."""
import json, os, sys, re, gzip
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "eval", "realdata")); sys.path.insert(0, os.path.dirname(__file__))
from eval_eicu import GROUPS; from llm_zero_shot import SYN
R = os.path.join(ROOT, "eval", "results", "eicu_demo")
def lr(entries):
    gr = {}
    for rank, d in enumerate(entries, 1):
        for g, rx in SYN.items():
            if re.search(rx, str(d.get("name", "")), re.I): gr.setdefault(g, rank)
    return gr
key = {k["case"]: k for k in json.load(open(os.path.join(R, "b8_key_n240.json")))}; panels = {p["case"]: p for p in json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))}
r1 = {c["case"]: lr(c["llm"]) for c in json.load(open(os.path.join(R, "b8_llm_blind_n240.json")))["cases"]}
r2 = {c["case"]: lr(c["llm"]) for c in json.load(open(os.path.join(R, "b8_llm_rerun40.json")))["cases"]}
p2 = {c["case"]: lr(c["llm"]) for c in json.load(open(os.path.join(R, "b8_llm_prompt2_n40.json")))["cases"]}
v7 = {r["stay"]: r for r in json.load(gzip.open(os.path.join(R, "per_stay_v7.json.gz"), "rt"))}
arms = {"LLM P1 read 1": lambda c: r1[c], "LLM P1 read 2": lambda c: r2[c], "LLM P2 (alt prompt)": lambda c: p2[c], "engine v5.1": lambda c: key[c]["engine_gr"], "engine v7": lambda c: v7[key[c]["stay"]]["gr"], "engine v7 two-tier": lambda c: v7[key[c]["stay"]]["gr2"]}
labels = [(c, g) for c in p2 for g in key[c]["coded"] if g in GROUPS and any(k in panels[c]["labs"] for k in GROUPS[g][2])]
L = ["# Prompt sensitivity — 40 B8 panels, %d scorable labels" % len(labels), "", "| arm | recall@1 | recall@3 | recall@5 | recall@10 | absent |", "|---|---|---|---|---|---|"]
hits = {}
for nm, f in arms.items():
    rk = [f(c).get(g) for c, g in labels]; hits[nm] = [x is not None and x <= 5 for x in rk]
    L.append(f"| {nm} | " + " | ".join(f"{100*sum(1 for x in rk if x is not None and x<=k)/len(rk):.1f}%" for k in (1, 3, 5, 10)) + f" | {100*sum(x is None for x in rk)/len(rk):.1f}% |")
def agree(a, b): return sum(x == y for x, y in zip(a, b)) / len(a)
L += ["", f"Label-level recall@5 agreement: P1r1 vs P1r2 {100*agree(hits['LLM P1 read 1'], hits['LLM P1 read 2']):.1f}%; P1r1 vs P2 {100*agree(hits['LLM P1 read 1'], hits['LLM P2 (alt prompt)']):.1f}%; P1r2 vs P2 {100*agree(hits['LLM P1 read 2'], hits['LLM P2 (alt prompt)']):.1f}%.",
      "", "P2 = 'ICU attending writing the admission problem list' framing (b8_llm_prompt2_n40.json); P1 = original laboratory-medicine prompt. Same model class, same blinding, 2026-10-25. n = 40 panels: exploratory, indicates the order of magnitude of prompt-induced variation only."]
open(os.path.join(R, "b8_prompt_sensitivity.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
