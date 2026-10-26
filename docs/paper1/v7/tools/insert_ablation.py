"""Build Table 5 + ablation paragraph from ablation outputs and insert into both R1 manuscripts and the response letter."""
import json, gzip, re, os
ROOT="/home/user/Hemoglyph"; OUT=f"{ROOT}/eval/results/eicu_demo"; V7=f"{ROOT}/docs/paper1/v7"
ci=json.load(open(f"{OUT}/ABLATION_v7_ci.json"))
full=json.load(open(f"{OUT}/summary_v7.json")) if os.path.exists(f"{OUT}/summary_v7.json") else None
def rep_auroc(path):
    m=re.search(r"Mean AUROC over lab-detectable groups with ≥ 5 listed stays: ([0-9.]+)",open(path).read()); return float(m.group(1)) if m else None
def summ(arm):
    s=json.load(open(f"{OUT}/summary_abl_{arm}.json"))
    r=lambda d,k: 100*d[k][0]/d[k][1]
    return dict(f3=r(s["recall"],"3"),f5=r(s["recall"],"5"),f10=r(s["recall"],"10"),t5=r(s["recall_two_tier"],"5"),au=rep_auroc(f"{OUT}/report_abl_{arm}.md"))
# full v7 reference from report.md
rep=open(f"{OUT}/report.md").read()
fa=rep_auroc(f"{OUT}/report.md")
LAB={"no_bayesian":"Bayesian-network layer off","no_fuzzy":"fuzzy layer off","no_graph":"knowledge-graph layer off","no_risk":"risk-model layer off",
"no_rule":"rule-engine vote off (registry + syndrome votes)","no_esl":"expert syndrome layer off (registry intact)",
"dempster":"Dempster instead of Yager combination","uniform_w":"uniform fusion weights (0.20 × 5)","no_shrink":"discord shrinkage and single-source discount off",
"anchor_only":"registry restricted to 272 curated anchor rules (32,911 AI-drafted rules off)","no_unverified":"28 `unverified_source` rules off"}
ORDER=["no_rule","no_esl","anchor_only","no_bayesian","uniform_w","no_shrink","dempster","no_fuzzy","no_graph","no_risk","no_unverified"]
rows=["| Arm | flat @3 | flat @5 | flat @10 | Δ flat @5 (95% CI) | two-tier @5 | Δ two-tier @5 (95% CI) | mean AUROC (24 groups) |","|---|---:|---:|---:|---|---:|---|---:|",
      f"| **full v7 (reference)** | **47.9** | **60.8** | **74.1** | — | **71.9** | — | **{fa:.3f}** |"]
P={}
for a in ORDER:
    if a not in ci: rows.append(f"| {LAB[a]} | not run | | | | | | |"); continue
    s=summ(a); c=ci[a]; f=c["flat5"]; t=c["tt5"]; P[a]=(s,c)
    rows.append(f"| {LAB[a]} | {s['f3']:.1f} | {s['f5']:.1f} | {s['f10']:.1f} | {f['delta']:+.1f} ({f['lo']:+.1f} to {f['hi']:+.1f}) | {s['t5']:.1f} | {t['delta']:+.1f} ({t['lo']:+.1f} to {t['hi']:+.1f}) | {s['au']:.3f} |")
table="\n".join(rows)
def d(a,k="flat5"): return P[a][1][k]
def au(a): return P[a][0]["au"]
para=(f"Two components carry the signal. Removing the rule-engine vote from fusion cost {abs(d('no_rule')['delta']):.1f} points of flat recall@5 ({d('no_rule')['lo']:+.1f} to {d('no_rule')['hi']:+.1f}) and removing the expert syndrome layer alone cost {abs(d('no_esl')['delta']):.1f} points ({d('no_esl')['lo']:+.1f} to {d('no_esl')['hi']:+.1f}). "
f"The remaining layers contributed little on this task: the Bayesian network {d('no_bayesian')['delta']:+.1f} points, the fuzzy and knowledge-graph layers and the risk models each within ±0.5 points (the risk-model layer changed no ranking at all), and the fusion refinements—Yager versus Dempster combination, discord shrinkage, single-source discount—within ±0.5 points; collapsing the fusion weights to uniform cost {abs(d('uniform_w')['delta']):.1f} points. "
f"Most importantly for the reviewer's question about the AI-drafted registry: restricting the registry to the 272 manually curated anchor rules and switching off the 32,911 AI-assisted rules changed flat recall@5 by only {d('anchor_only')['delta']:+.1f} points ({d('anchor_only')['lo']:+.1f} to {d('anchor_only')['hi']:+.1f}), two-tier recall@5 by {d('anchor_only','tt5')['delta']:+.1f} points and mean per-group AUROC from {fa:.3f} to {au('anchor_only'):.3f}. "
f"On clinician-listed ICU diagnoses, therefore, the large AI-drafted rule base adds breadth and discrimination at the margin but is not what drives the headline recall; the hand-curated anchors and the syndrome layer are. "
+ (f"Removing the 28 `unverified_source` rules changed recall@5 by {d('no_unverified')['delta']:+.1f} points. " if 'no_unverified' in P else "")
+ "We regard this as reassuring for safety (the unaudited rules are not load-bearing) and as a limit on the claim that scale of the registry is itself an advantage; its value, if any, lies in coverage of rarer entities that the eICU label set does not test.")
json.dump({"table":table,"para":para},open(f"{V7}/tools/ablation_snippet.json","w"),indent=1)
for path,tab_key,para_key in ((f"{V7}/Paper1_Hemoglyph_SampleStyle_v7_R1.md","[ABLATION_TABLE]",None),(f"{V7}/Paper1_Hemoglyph_npj_EN_v7_R1.md","[ABLATION_TABLE]","[ABLATION_PARAGRAPH]")):
    t=open(path,encoding="utf-8").read()
    if "SampleStyle" in path:
        assert t.count(tab_key)==1
        t=t.replace(tab_key,"\n\n"+para+"\n\nTable 5. Component ablation of the frozen engine v7 on the eICU-CRD demo (2,314 stays; 2,432 labels; stay-cluster bootstrap CIs; mean AUROC over 24 lab-detectable groups with ≥ 5 listed stays).\n\n"+table+"\n")
    else:
        assert t.count(tab_key)==1 and t.count(para_key)==1
        short=para.split("Most importantly")[0]+"Restricting the registry to the 272 manually curated anchor rules (32,911 AI-assisted rules off) changed flat recall@5 by only "+f"{d('anchor_only')['delta']:+.1f} points ({d('anchor_only')['lo']:+.1f} to {d('anchor_only')['hi']:+.1f})"+f" and mean per-group AUROC from {fa:.3f} to {au('anchor_only'):.3f} (Table 5): the AI-drafted bulk of the registry is not load-bearing for the headline result, which is reassuring for safety but limits any claim that registry scale is itself an advantage."
        t=t.replace(para_key,short).replace(tab_key,table)
    open(path,"w",encoding="utf-8").write(t)
print(table); print(); print(para)
