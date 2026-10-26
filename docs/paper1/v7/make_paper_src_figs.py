import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
def save(n): plt.tight_layout(); plt.savefig(f"/home/user/Hemoglyph/docs/paper1/v7/fig/src_{n}.png",dpi=170); plt.close()
# 1 architecture
fig,ax=plt.subplots(figsize=(10,3.6)); ax.axis("off")
boxes=[("Input\nlab panel + age/sex\n(+ optional context,\n+ optional time series)",0),("Normalisation\nUCUM units, aliases,\nderived indices\n(eGFR, corrected Ca,\nanion gap, FIB-4...)",1),("Rule layer\n33,183 executable\nguideline rules\n(registry 14.1.0)",2),("Expert syndrome layer\n~900 curated constellations\nanchor/strong/pattern/\nsupportive/screen",3),("Ensemble fusion\nBayesian prior, fuzzy,\nrule votes, ESL floors,\ncontext guards",4),("Ranking hygiene\ncausal attribution (v7),\nsubsumption, chronicity,\nUDMI, two-tier output",5),("Output\nranked differential,\nfindings explained_by,\nevidence state,\nnext tests",6)]
for t,i in boxes:
    ax.add_patch(plt.Rectangle((i*1.45,0),1.3,1,fc="#e8eef7",ec="#2b4c7e")); ax.text(i*1.45+0.65,0.5,t,ha="center",va="center",fontsize=7.6)
    if i<6: ax.annotate("",xy=((i+1)*1.45,0.5),xytext=(i*1.45+1.3,0.5),arrowprops=dict(arrowstyle="->",color="#2b4c7e"))
ax.set_xlim(-0.1,10.2); ax.set_ylim(-0.1,1.1); ax.set_title("Hemoglyph interpretation pipeline (single file analyse_gidlines.py, engine v7)")
save("fig01_architecture")
# 2 eICU engine versions
labels=["13.3.0","13.4.2","14.1 / v6","v7"]
flat3=[49.3,49.3,48.5,47.9]; flat5=[63.8,63.7,60.8,60.8]; flat10=[77.2,76.9,74.1,74.1]; tt3=[np.nan,np.nan,62.3,62.0]; tt5=[np.nan,np.nan,71.7,71.9]
x=np.arange(4); w=0.16
fig,ax=plt.subplots(figsize=(8,4))
for k,(v,n) in enumerate([(flat3,"flat top-3"),(flat5,"flat top-5"),(flat10,"flat top-10"),(tt3,"two-tier @3"),(tt5,"two-tier @5")]):
    b=ax.bar(x+(k-2)*w,v,w,label=n)
    for xi,vi in zip(x+(k-2)*w,v):
        if not np.isnan(vi): ax.text(xi,vi+0.6,f"{vi:.1f}",ha="center",fontsize=6.5)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel("recall of clinician-coded label (%)"); ax.set_ylim(0,90); ax.legend(ncol=3,fontsize=8)
ax.set_title("eICU-CRD demo, 2,314 ICU stays, labs only — engine/registry versions")
save("fig02_eicu_versions")
# 3 decomposition
fig,axs=plt.subplots(1,2,figsize=(10,3.8))
parts=[("group without single lab criterion",541),("key analyte absent in first panel",275),("contradicted by panel values",431),("panel-supported",1460)]
cols=["#bbbbbb","#dddddd","#e39b9b","#6aa84f"]; left=0
for (n,v),c in zip(parts,cols):
    axs[0].barh([0],[v],left=left,color=c,label=f"{n} ({v})"); axs[0].text(left+v/2,0,str(v),ha="center",va="center",fontsize=8); left+=v
axs[0].set_yticks([]); axs[0].set_xlabel("clinician-coded label targets (n = 2,707)"); axs[0].legend(fontsize=7,loc="upper center",bbox_to_anchor=(0.5,-0.25),ncol=2); axs[0].set_title("Why the flat metric saturates ~60 %",fontsize=10)
arms=["13.4.2","14.1 / v6","v7","registry OFF"]; ps5=[81.6,78.0,78.0,75.3]; ps10=[95.1,91.8,91.8,89.9]; tt5=[np.nan,88.9,89.2,np.nan]
x=np.arange(4); axs[1].bar(x-0.25,ps5,0.25,label="flat top-5"); axs[1].bar(x,ps10,0.25,label="flat top-10"); axs[1].bar(x+0.25,tt5,0.25,label="two-tier @5")
for xi,v in zip(x-0.25,ps5): axs[1].text(xi,v+0.5,f"{v:.1f}",ha="center",fontsize=7)
for xi,v in zip(x,ps10): axs[1].text(xi,v+0.5,f"{v:.1f}",ha="center",fontsize=7)
axs[1].set_xticks(x); axs[1].set_xticklabels(arms); axs[1].set_ylim(0,105); axs[1].set_ylabel("recall on panel-supported labels (%)"); axs[1].legend(fontsize=7); axs[1].set_title("Panel-supported labels (n = 1,460)",fontsize=10)
fig.suptitle("Reference-standard ceiling on eICU and the panel-supported secondary metric")
save("fig03_ceiling")
# 4 per group (verified via panel_supported_metric CRIT, recall@5, n>=12)
g=["renal impairment","AKI","anemia","CKD","diabetes","AMI","DKA","hyperglycemia","heart failure","leukocytosis","hyponatremia","hyperkalemia","thrombocytopenia","hypokalemia","metabolic acidosis","hypomagnesemia","lactic acidosis","hypernatremia","acute pancreatitis"]
n=[284,193,137,129,113,77,67,66,54,49,46,43,37,36,36,21,18,12,12]
l=[88.0,82.4,89.8,74.4,81.4,93.5,97.0,60.6,90.7,67.3,73.9,55.8,75.7,83.3,75.0,66.7,66.7,75.0,100]
v7=[89.8,85.5,88.3,41.1,80.5,92.2,97.0,63.6,88.9,46.9,71.7,55.8,70.3,91.7,72.2,61.9,66.7,66.7,100]
y=np.arange(len(g)); fig,ax=plt.subplots(figsize=(8,6))
ax.barh(y-0.2,l,0.4,label="13.4.2 legacy",color="#999"); ax.barh(y+0.2,v7,0.4,label="v7",color="#2b4c7e")
ax.set_yticks(y); ax.set_yticklabels([f"{a} (n={b})" for a,b in zip(g,n)],fontsize=8); ax.invert_yaxis(); ax.set_xlabel("recall@5 on panel-supported labels (%)"); ax.legend(loc="lower right"); ax.set_title("Per-group recall@5, panel-supported labels (n >= 12) — losses concentrated in CKD and leukocytosis",fontsize=9.5)
save("fig04_groups")
# 5 NHANES
tasks=["diabetes","CKD (KDIGO)","anemia","iron deficiency","hypercholesterolemia","hyperuricemia","ALT elevation"]
J=[0.946,0.959,0.972,0.989,0.905,0.943,0.872]; H=[0.938,0.968,0.994,np.nan,0.883,0.958,0.880]; I=[0.924,0.962,0.983,0.972,0.886,0.955,0.877]
x=np.arange(len(tasks)); fig,ax=plt.subplots(figsize=(9,3.8))
ax.bar(x-0.27,J,0.27,label="2017–18 (J, development; v7 re-run)"); ax.bar(x,H,0.27,label="2013–14 (H, quarantine 1)"); ax.bar(x+0.27,I,0.27,label="2015–16 (I, quarantine 2)")
ax.set_xticks(x); ax.set_xticklabels(tasks,fontsize=8,rotation=15); ax.set_ylim(0.5,1.0); ax.set_ylabel("AUROC (axis truncated at 0.5)"); ax.legend(fontsize=8,loc="lower center",ncol=3,bbox_to_anchor=(0.5,-0.42),frameon=False); ax.set_title("NHANES population screening — AUROC reproduced across three independent cycles (n = 3,000 each)")
save("fig05_nhanes")
# 6 sepsis
frames=["set A prediction\n(labs 24 h)","set A concurrent\nlabs+vitals","set B prediction","set B concurrent\nlabs+vitals","set B2 prediction","set B2 concurrent\nlabs+vitals"]
eng=[0.600,0.592,0.610,0.638,0.588,0.635]; log=[0.691,0.687,0.712,0.744,0.679,0.726]
x=np.arange(6); fig,ax=plt.subplots(figsize=(9,3.8)); ax.bar(x-0.2,eng,0.4,label="Hemoglyph (unsupervised)"); ax.bar(x+0.2,log,0.4,label="supervised logistic reference (5-fold CV)",color="#999")
for xi,v in zip(x-0.2,eng): ax.text(xi,v+0.005,f"{v:.3f}",ha="center",fontsize=7)
ax.axhline(0.5,ls="--",c="k",lw=0.7); ax.set_xticks(x); ax.set_xticklabels(frames,fontsize=7.5); ax.set_ylim(0.4,0.8); ax.set_ylabel("AUROC (Sepsis-3 label)"); ax.legend(fontsize=8); ax.set_title("PhysioNet/CinC 2019 sepsis — Hemoglyph is not a sepsis predictor; a supervised model wins on every frame")
save("fig06_sepsis")
# 7 LLM
g=["renal impairment","sepsis","diabetes","AKI","GI bleeding","anemia","CKD","DKA","AMI","hyperglycemia","heart failure","hypokalemia","metabolic acidosis","thrombocytopenia"]
n=[75,71,62,49,38,36,35,30,27,22,17,17,14,12]; he=[81,38,55,80,87,86,51,73,89,55,94,53,57,75]; ll=[75,42,37,76,50,83,20,83,81,64,94,41,79,75]
y=np.arange(len(g)); fig,ax=plt.subplots(figsize=(8,5))
ax.barh(y-0.2,he,0.4,label="Hemoglyph v5.1 (64.4 % pooled)",color="#2b4c7e"); ax.barh(y+0.2,ll,0.4,label="GPT-4-class LLM, blind (59.6 % pooled)",color="#c9752d")
ax.set_yticks(y); ax.set_yticklabels([f"{a} (n={b})" for a,b in zip(g,n)],fontsize=8); ax.invert_yaxis(); ax.set_xlabel("recall@5 (%)"); ax.legend(fontsize=8); ax.set_title("Blind LLM comparison, 400 eICU stays, 596 labels (engine v5.1 arm; see Table 4 for v7)")
save("fig07_llm")
# 8 provenance
fig,ax=plt.subplots(figsize=(7,3.3)); cats=["DOI resolved (Crossref)","landing page reached","URL only","unreachable from sandbox","no locator"]; v=[112,533,63,39,34]
ax.barh(cats,v,color=["#2e7d32","#6aa84f","#c9b458","#e39b9b","#999"]); [ax.text(x+5,i,str(x),va="center",fontsize=8) for i,x in enumerate(v)]; ax.invert_yaxis(); ax.set_xlabel("guideline sources (n = 781)"); ax.set_title("Source-provenance audit of the registry (13.4.1); 9 invalid DOIs removed, 28 rules flagged unverified_source")
save("fig08_provenance")
# 9 calibration
grp=["all pooled","renal impairment","sepsis","diabetes","AKI","anemia"]; raw=[0.161,0.253,0.186,0.201,0.258,0.346]; iso=[0.002,0.028,0.027,0.026,0.025,0.015]; au=[0.801,0.798,0.685,0.693,0.797,0.782]
x=np.arange(6); fig,ax=plt.subplots(figsize=(8,3.6)); ax.bar(x-0.2,raw,0.4,label="ECE raw score"); ax.bar(x+0.2,iso,0.4,label="ECE after cross-fitted isotonic")
for xi,a in zip(x,au): ax.text(xi,0.37,f"AUROC {a:.2f}",ha="center",fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(grp,fontsize=8); ax.set_ylabel("expected calibration error"); ax.set_ylim(0,0.42); ax.legend(fontsize=8); ax.set_title("Scores are ranks, not probabilities: raw ECE 0.16–0.35, recoverable by isotonic recalibration")
save("fig09_calibration")
# 10 validation flow
fig,ax=plt.subplots(figsize=(10,3.2)); ax.axis("off")
steps=[("SAP + amendments\n(pre-registered\ncriteria)",0,"#e8eef7"),("Development data\neICU demo, NHANES J,\nSepsis set A, UCI, PMC",1,"#fff2cc"),("FREEZE v14\nSHA-256 manifest\n261 files",2,"#d9ead3"),("Quarantine 1 (one shot)\nMIMIC-IV demo, NHANES H,\nSepsis set B\n→ 2 primary criteria FAILED",3,"#f4cccc"),("Engine v7\n(causal attribution,\ncontext guards)\ngate = parity",4,"#fff2cc"),("FREEZE v15\n316 files",5,"#d9ead3"),("Quarantine 2 (one shot)\nNHANES I, Sepsis set B2\n→ all non-inferiority\ncriteria MET",6,"#d9ead3")]
for t,i,c in steps:
    ax.add_patch(plt.Rectangle((i*1.45,0),1.3,1,fc=c,ec="#333")); ax.text(i*1.45+0.65,0.5,t,ha="center",va="center",fontsize=7.4)
    if i<6: ax.annotate("",xy=((i+1)*1.45,0.5),xytext=(i*1.45+1.3,0.5),arrowprops=dict(arrowstyle="->"))
ax.set_xlim(-0.1,10.2); ax.set_ylim(-0.1,1.1); ax.set_title("Pre-registration, freeze and one-shot quarantine workflow (SAP Amendments 1–15)")
save("fig10_flow")
# 11 MIMIC + PMC + UCI summary
fig,axs=plt.subplots(1,3,figsize=(11,3.4))
axs[0].bar(["top-3","top-5","top-10"],[35.3,47.5,62.1],color="#2b4c7e"); axs[0].bar(["top-3","top-5","top-10"],[37.1,50.1,63.5],color="#999",alpha=0.5,width=0.5)
axs[0].set_title("MIMIC-IV demo (235 adm., 507 pairs)\nv7 (blue) vs 13.3.0 control (grey)",fontsize=9); axs[0].set_ylim(0,80); axs[0].set_ylabel("%")
axs[1].bar(["parser\nspecific","parser\nsyndrome","manual\nspecific","manual\nsyndrome"],[10,44,26,68],color=["#c9752d","#c9752d","#2b4c7e","#2b4c7e"]); axs[1].set_title("PMC-Patients 50 vignettes (Bhasuran 2025)\ntop-5, labs + age/sex only",fontsize=9); axs[1].set_ylim(0,100)
axs[2].bar(["Thyroid\nhypo","Thyroid\nhyper","HCV\nany liver","HCV\ncirrhosis","ILPD"],[0.979,0.798,0.925,0.909,0.704],color="#6aa84f"); axs[2].set_ylim(0.5,1.0); axs[2].set_title("UCI / ILPD held-out AUROC",fontsize=9)
fig.suptitle("Other external sets"); save("fig11_other")
print("figs done")
# 12 ML baseline (ml_baseline.md, v5.x eICU)
g=["AKI","CKD","renal impairment","diabetes","hyperglycemia","DKA","hypokalemia","hyperkalemia","hyponatremia","metabolic acidosis","anemia","thrombocytopenia","leukocytosis","sepsis","cirrhosis","AMI","heart failure","coagulopathy","GI bleeding","alcohol withdrawal"]
hg=[0.80,0.81,0.80,0.69,0.70,0.86,0.72,0.92,0.89,0.76,0.78,0.89,0.73,0.68,0.87,0.70,0.66,0.75,0.75,0.54]
gb=[0.83,0.79,0.83,0.75,0.78,0.96,0.76,0.91,0.85,0.75,0.79,0.85,0.71,0.82,0.83,0.73,0.58,0.81,0.85,0.80]
lr=[0.72,0.77,0.77,0.67,0.64,0.95,0.79,0.93,0.85,0.69,0.79,0.84,0.62,0.73,0.75,0.63,0.64,0.74,0.84,0.80]
y=np.arange(len(g)); fig,ax=plt.subplots(figsize=(8,6.5))
ax.barh(y-0.27,hg,0.27,label="Hemoglyph (untrained)",color="#2b4c7e"); ax.barh(y,gb,0.27,label="gradient boosting (5-fold OOF, trained on labels)",color="#c9752d"); ax.barh(y+0.27,lr,0.27,label="logistic regression (5-fold OOF)",color="#999")
ax.set_yticks(y); ax.set_yticklabels(g,fontsize=8); ax.invert_yaxis(); ax.set_xlim(0.4,1.0); ax.set_xlabel("AUROC (group probability vs clinician label)"); ax.legend(fontsize=7.5,loc="lower right")
ax.set_title("eICU: untrained Hemoglyph vs supervised models on identical inputs",fontsize=10); save("fig12_ml_baseline")
# 13 context echo
fig,ax=plt.subplots(figsize=(7,3.3))
ax.bar([0,1],[58.2,49.6],0.38,label="labs only",color="#2b4c7e"); ax.bar([0.38,1.38],[59.1,72.9],0.38,label="labs + clinical context",color="#6aa84f")
ax.set_xticks([0.19,1.19]); ax.set_xticklabels(["label NOT named in history (n=2,467)","label already named in history (n=240)"],fontsize=8); ax.set_ylabel("recall@5 (%)"); ax.legend(fontsize=8)
for x,v in [(0,58.2),(0.38,59.1),(1,49.6),(1.38,72.9)]: ax.text(x,v+1,f"{v}",ha="center",fontsize=8)
ax.set_title("Context arm gains come almost entirely from 'echoing' documented history",fontsize=9.5); save("fig13_context_echo")
# 14 LLM rank bins
fig,ax=plt.subplots(figsize=(7,3.3)); bins=["rank 1","2–3","4–5","6–10","absent"]; h=[139,156,89,60,152]; l=[168,135,52,33,208]; x=np.arange(5)
ax.bar(x-0.2,h,0.4,label="Hemoglyph",color="#2b4c7e"); ax.bar(x+0.2,l,0.4,label="LLM",color="#c9752d"); ax.set_xticks(x); ax.set_xticklabels(bins); ax.set_ylabel("labels (n=596)"); ax.legend()
ax.set_title("Rank distribution of the 596 labels: LLM more often rank-1, Hemoglyph less often absent",fontsize=9.5); save("fig14_llm_ranks")
print("extra figs")
