# -*- coding: utf-8 -*-
"""Figures 2–6 and S2 for Paper 1 v5.3, from numbers_v53.json (run numbers.py first).

    python3 docs/paper1/v53/make_figures_v53.py
Writes PNG (300 dpi) + SVG into docs/paper1/figures/. Fig. 1 (architecture) and Fig. S1 (flow) are kept from the earlier build.
"""
import json, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, "..", "figures"); os.makedirs(FIG, exist_ok=True)
N = json.load(open(os.path.join(HERE, "numbers_v53.json"), encoding="utf-8"))
from tables_en import L
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
C_ENG, C_LLM, C_B1, C_B2, C_RAW, C_ISO = "#1f4e79", "#c0504d", "#9bbb59", "#f79646", "#7f7f7f", "#1f4e79"

def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIG, name + ".svg"), bbox_inches="tight"); plt.close(fig); print("saved", name)

# ---------------------------------------------------------------- Fig 2 forest
def fig2():
    rows = []
    g = N["eicu"]["labs"]["groups"]
    for k, v in sorted(g.items(), key=lambda kv: -kv[1]["auroc"]):
        if v["detectable"] == "yes" and v["n"] >= 10 and v.get("auroc_ci"):
            rows.append(("eICU · " + L(k), v["auroc"], float(v["auroc_ci"][0]), float(v["auroc_ci"][1])))
    nh = N["nhanes"].get("2017", {})
    for k, lab in (("diabetes", "diabetes (ADA)"), ("diabetes_selfreport", "diabetes, self-report"), ("ckd", "CKD (KDIGO)"), ("ckd_selfreport", "CKD, self-report"),
                   ("anemia", "anaemia (WHO)"), ("iron_deficiency", "iron deficiency"), ("hypercholesterolemia", "hypercholesterolaemia"), ("hyperuricemia", "hyperuricaemia"), ("alt_elevation", "ALT elevation")):
        if k in nh: rows.append(("NHANES · " + lab, nh[k]["auroc"], float(nh[k]["auroc_ci"][0]), float(nh[k]["auroc_ci"][1])))
    for k, v in N["thyroid"].items():
        rows.append(("Thyroid · " + re.sub(r"^H\d\w? ", "", k).replace(" vs no-comment", "")[:42], v["auroc"], v["ci"][0], v["ci"][1]))
    for k, v in N["hcv"].items():
        rows.append(("HCV · " + re.sub(r"^Task \S+ — ", "", k), v["auroc"], v["ci"][0], v["ci"][1]))
    for k, v in N["ilpd"].items():
        rows.append(("ILPD · " + k, v["auroc"], v["ci"][0], v["ci"][1]))
    fig, ax = plt.subplots(figsize=(7.2, 0.19 * len(rows) + 1))
    y = np.arange(len(rows))[::-1]
    for yi, (lab, a, lo, hi) in zip(y, rows):
        col = C_ENG if lab.startswith("eICU") else "#2e75b6" if lab.startswith("NHANES") else "#548235" if lab.startswith("Thyroid") else "#bf9000" if lab.startswith("HCV") else "#7030a0"
        ax.plot([lo, hi], [yi, yi], color=col, lw=1.2); ax.plot(a, yi, "o", color=col, ms=3.5)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=6.5); ax.axvline(0.5, color="k", lw=0.6, ls=":")
    ax.set_xlim(0.4, 1.0); ax.set_xlabel("AUROC (95 % bootstrap CI), engine v5.3"); ax.set_title("Held-out discrimination across datasets", fontsize=9)
    save(fig, "fig2_auroc_forest")

# ---------------------------------------------------------------- Fig 3 comparators
def fig3():
    g = N["eicu"]["labs"]["groups"]; b1 = N["b1"]; b2 = N["b2"]
    keys = [k for k, v in sorted(g.items(), key=lambda kv: -kv[1]["n"]) if v["n"] >= 10 and (k in b1 or k in b2)]
    x = np.arange(len(keys)); w = 0.27
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.bar(x - w, [g[k]["auroc"] for k in keys], w, color=C_ENG, label="Hemoglyph (untrained, labs only)")
    ax.bar(x, [b1[k]["auroc"] if k in b1 else np.nan for k in keys], w, color=C_B1, label="B1 raw key-analyte threshold")
    ax.bar(x + w, [b2[k]["hgb"] if k in b2 else np.nan for k in keys], w, color=C_B2, label="B2 gradient boosting (trained, 5-fold OOF)")
    ax.set_xticks(x); ax.set_xticklabels([L(k) for k in keys], rotation=60, ha="right", fontsize=6.5); ax.set_ylim(0.4, 1.0); ax.set_ylabel("AUROC")
    ax.axhline(0.5, color="k", lw=0.5, ls=":"); ax.legend(fontsize=6.5, frameon=False, loc="upper right", ncol=1)
    ax.set_title("eICU-CRD demo: untrained engine versus a raw threshold and a trained model", fontsize=9)
    save(fig, "fig3_eicu_baselines")

# ---------------------------------------------------------------- Fig 4 calibration + DCA
def fig4():
    C = N["cal"]; rel = np.array(C["reliability"])
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.6))
    ax = axes[0]; ax.plot([0, 1], [0, 1], "k:", lw=0.7)
    ax.plot(rel[:, 1], rel[:, 2], "o-", color=C_RAW, ms=3.5, label=f"raw (ECE {C['rows']['ALL groups pooled']['ece_raw']:.3f})")
    ax.plot(rel[:, 3], rel[:, 4], "s-", color=C_ISO, ms=3.5, label=f"isotonic, cross-fitted (ECE {C['rows']['ALL groups pooled']['ece_iso']:.3f})")
    ax.set_xlabel("mean predicted probability (equal-mass deciles)"); ax.set_ylabel("observed frequency"); ax.set_title("a  Reliability, all groups pooled", fontsize=8, loc="left"); ax.legend(fontsize=6, frameon=False)
    for ax, k, t in ((axes[1], "renal_impairment", "b  Net benefit: renal impairment"), (axes[2], "sepsis", "c  Net benefit: sepsis")):
        rows = np.array(C["dca"][k]["rows"])
        ax.plot(rows[:, 0], rows[:, 2], "-", color=C_ISO, lw=1.4, label="engine, isotonic")
        ax.plot(rows[:, 0], rows[:, 1], "--", color=C_RAW, lw=1.1, label="engine, raw")
        ax.plot(rows[:, 0], rows[:, 3], "-", color="#bbbbbb", lw=1, label="treat all"); ax.axhline(0, color="k", lw=0.6, label="treat none")
        ax.set_ylim(-5, max(rows[:, 2].max(), rows[:, 3].max()) + 2); ax.set_xlabel("threshold probability"); ax.set_ylabel("net benefit per 100"); ax.set_title(t, fontsize=8, loc="left")
        ax.legend(fontsize=5.5, frameon=False)
    fig.tight_layout(); save(fig, "fig4_calibration_dca")

# ---------------------------------------------------------------- Fig 5 LLM comparison
def fig5():
    P = N["llm"]["pooled"]; rows = [r for r in P["groups"] if r["n"] >= 10]
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [2.4, 1]})
    ax = axes[0]; x = np.arange(len(rows)); w = 0.38
    ax.bar(x - w / 2, [r["engine"] for r in rows], w, color=C_ENG, label=f"Hemoglyph  (recall@5 {P['engine'][0]:.1f} %)")
    ax.bar(x + w / 2, [r["llm"] for r in rows], w, color=C_LLM, label=f"frontier LLM, zero-shot  ({P['llm'][0]:.1f} %)")
    ax.set_xticks(x); ax.set_xticklabels([f"{L(r['group'])} (n={r['n']})" for r in rows], rotation=60, ha="right", fontsize=6.3)
    ax.set_ylabel("recall@5 (%)"); ax.set_ylim(0, 118); ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_title(f"a  Per-group recall@5, {P['stays']} blinded stays, identical inputs (McNemar p = {P['p']})", fontsize=8, loc="left")
    ax.legend(fontsize=6.5, frameon=False, loc="upper left", ncol=2)
    ax = axes[1]; bins = N["rank"]["pooled_bins"]; labs = list(bins.keys()); e = [bins[k][0] for k in labs]; l = [bins[k][1] for k in labs]
    y = np.arange(len(labs)); ax.barh(y + 0.2, e, 0.4, color=C_ENG); ax.barh(y - 0.2, l, 0.4, color=C_LLM)
    ax.set_yticks(y); ax.set_yticklabels(["rank " + k if k != "absent" else "not listed" for k in labs], fontsize=6.5); ax.invert_yaxis()
    ax.legend(["Hemoglyph", "LLM"], fontsize=6, frameon=False, loc="lower right")
    ax.set_xlabel("clinician-listed labels (n = 596)"); ax.set_title("b  Where the true label sits", fontsize=8, loc="left")
    fig.tight_layout(); save(fig, "fig5_llm_comparison")

# ---------------------------------------------------------------- Fig 6 audit + next test
def fig6():
    A = N["audit"]; NT = N["next_test"]
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]; grp = A["by_group"][:12]; y = np.arange(len(grp)); left = np.zeros(len(grp))
    for cat, col, lab in (("A", "#bdbdbd", "A  no laboratory signature"), ("B", "#9bbb59", "B  displaced by other true findings"), ("C1", "#c0504d", "C1 knowledge/logic gap"), ("C2", "#f79646", "C2 scoring defect"), ("D", "#4f81bd", "D  label-map gap")):
        vals = np.array([r[cat] for r in grp]); ax.barh(y, vals, left=left, color=col, label=lab); left += vals
    ax.set_yticks(y); ax.set_yticklabels([L(r["group"]) for r in grp], fontsize=6.5); ax.invert_yaxis(); ax.set_xlabel("sampled misses (n = 200)")
    ax.set_title("a  Why the engine misses (pre-declared taxonomy)", fontsize=8, loc="left"); ax.legend(fontsize=5.5, frameon=False, loc="lower right")
    ax = axes[1]; items = [(k, v) for k, v in NT.items() if k != "all"]; y = np.arange(len(items))
    ax.barh(y, [v["n"] for k, v in items], color="#dddddd", label="category-A misses with a scorable test")
    ax.barh(y, [v["hit"] for k, v in items], color=C_ENG, label="discriminating test named by the engine")
    ax.set_yticks(y); ax.set_yticklabels([k for k, v in items], fontsize=6.5); ax.invert_yaxis(); ax.set_xlabel("misses")
    ax.set_title(f"b  Next-test utility ({NT['all']['hit']}/{NT['all']['n']} = {NT['all']['pct']:.0f} %)", fontsize=8, loc="left"); ax.legend(fontsize=5.5, frameon=False, loc="lower right")
    fig.tight_layout(); save(fig, "fig6_audit_nexttest")

# ---------------------------------------------------------------- Fig S2 gate
def figS2():
    G = N["gate"]; items = []
    for k, v in G.items():
        m = re.search(r"(\d+)/(\d+)", v)
        if m: items.append((k.replace("_", " "), int(m.group(1)), int(m.group(2))))
        elif "passed" in v:
            m2 = re.search(r"(\d+) passed", v); items.append((k, int(m2.group(1)), int(m2.group(1)) + int((re.search(r"(\d+) failed", v) or [0, 0])[1] or 0)))
    fig, ax = plt.subplots(figsize=(5, 2.2)); y = np.arange(len(items))
    ax.barh(y, [1] * len(items), color="#eeeeee"); ax.barh(y, [a / b for _, a, b in items], color=C_ENG)
    for yi, (k, a, b) in zip(y, items): ax.text(1.01, yi, f"{a}/{b}", va="center", fontsize=7)
    ax.set_yticks(y); ax.set_yticklabels([k for k, _, _ in items], fontsize=7); ax.invert_yaxis(); ax.set_xlim(0, 1.15); ax.set_xticks([])
    ax.set_title("Regression gate at the v5.3 freeze", fontsize=8); save(fig, "figS2_synthetic")

if __name__ == "__main__":
    fig2(); fig3(); fig4(); fig5(); fig6(); figS2()
