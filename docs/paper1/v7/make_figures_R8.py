#!/usr/bin/env python3
"""Main-text figures, R8 (CMPB). Every number is read from a frozen result file or is the number printed in the
manuscript table it illustrates; nothing is re-measured. Output: fig/Figure_1.png … Figure_8.png at 300 dpi."""
import json, re, os, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HG = "/home/user/Hemoglyph"; OUT = os.path.join(HG, "docs/paper1/v7/fig")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "savefig.dpi": 300, "savefig.facecolor": "white"})
ENG, LLM, GB, LR, GREY, OK, BAD, LIGHT = "#1f3b73", "#d9822b", "#c0504d", "#8c8c8c", "#5a5a5a", "#3b8b5a", "#b03a2e", "#dfe6f1"
MM = 1 / 25.4
def save(fig, n):
    fig.savefig(os.path.join(OUT, f"Figure_{n}.png"), bbox_inches="tight", pad_inches=0.05); plt.close(fig)
def label(ax, s, x=-0.08, y=1.06):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")
def box(ax, x, y, w, h, title, body, fc=LIGHT, ec=ENG, fs=7.2, tfs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.015", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h - 0.016, title, ha="center", va="top", fontsize=tfs, fontweight="bold", color="#111")
    ax.text(x + w / 2, y + h / 2 - 0.035 if body.count("\n") >= 2 else y + h / 2 - 0.025, body, ha="center", va="center", fontsize=fs, color="#222", linespacing=1.25)
def arrow(ax, p, q, color=GREY, lw=0.9, style="-|>", ms=7):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, shrinkA=0, shrinkB=0))

# ------------------------------------------------------------------------------------------------ Figure 1 architecture
def fig1():
    fig, ax = plt.subplots(figsize=(300 * MM, 165 * MM)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    box(ax, 0.02, 0.78, 0.20, 0.17, "Input", "laboratory panel + age/sex\noptional context, time series", fc="#fdf3dc", ec="#b8860b")
    box(ax, 0.27, 0.78, 0.30, 0.17, "Normalisation", "alias → analyte (85,828 aliases)\nUCUM unit conversion\nderived indices (eGFR, AG, FIB-4 …)")
    box(ax, 0.62, 0.78, 0.36, 0.17, "Verification surface", "every output cites rule id, source id, feature,\noperator, value and unit — the objects that\nthe four methods of this paper test", fc="#eaf4ec", ec=OK)
    arrow(ax, (0.22, 0.865), (0.27, 0.865)); arrow(ax, (0.57, 0.865), (0.62, 0.865), style="-", lw=0.7)
    ys = 0.50; w = 0.172; xs = [0.02, 0.217, 0.414, 0.611, 0.808]
    comps = [("Rule engine  (w = 0.35)", "33,183 executable rules\n4 layers: screening /\ndiagnostic / exclusion / staging\n99.2 % AI-drafted, 272 anchors"),
             ("Bayesian network  (0.25)", "75 disease nodes\n30 evidence clusters"),
             ("Adaptive fuzzy  (0.20)", "35 rules, 20 patterns\nabstains when no rule covers"),
             ("Knowledge graph  (0.10)", "97 nodes\n112 cause–effect edges"),
             ("Risk models  (0.10)", "100 published scores\nCKD-EPI, FIB-4, MELD …")]
    for x, (t, b) in zip(xs, comps):
        box(ax, x, ys, w, 0.22, t, b, fs=7.2, tfs=7.8); arrow(ax, (0.42, 0.78), (x + w / 2, ys + 0.22), lw=0.6)
    box(ax, 0.02, 0.21, 0.30, 0.20, "Weighted fusion", "fixed weights + 6 domain profiles\ndiscord shrinkage ≤ 45 %; single-source\ndiscount 0.70; no weight fitted to outcomes")
    box(ax, 0.35, 0.21, 0.30, 0.20, "Constrained Theory of Evidence", "binary frame per disease; Yager's rule\n(conflict → ignorance); reliability discounting\nbelief / plausibility → evidence state")
    box(ax, 0.68, 0.21, 0.30, 0.20, "Syndrome layer & ranking hygiene", "~900 expert constellations (anchor .95 … screen .45)\ncausal attribution, chronicity, KDIGO/UDMI guards\ntwo-tier differential (≤ 25)")
    for x in xs: ax.plot([x + w / 2, x + w / 2], [ys, 0.455], color=GREY, lw=0.7)
    ax.plot([xs[0] + w / 2, xs[-1] + w / 2], [0.455, 0.455], color=GREY, lw=0.7); arrow(ax, (0.17, 0.455), (0.17, 0.41))
    arrow(ax, (0.32, 0.31), (0.35, 0.31)); arrow(ax, (0.65, 0.31), (0.68, 0.31))
    box(ax, 0.20, 0.01, 0.60, 0.13, "Output", "ranked differential with evidence state (confirmed / probable / insufficient / conflicting),\nexplained findings, cited sources, suggested next tests — deterministic, offline, ≈1 s per panel", fc="#fdf3dc", ec="#b8860b")
    ax.plot([0.83, 0.83, 0.50], [0.21, 0.175, 0.175], color=GREY, lw=0.9); arrow(ax, (0.50, 0.175), (0.50, 0.14))
    save(fig, 1)

# ------------------------------------------------------------------------------------------------ Figure 2 workflow + ceiling
def fig2():
    fig = plt.figure(figsize=(270 * MM, 150 * MM)); gs = fig.add_gridspec(2, 2, height_ratios=[0.9, 1.25], hspace=0.55, wspace=0.35)
    ax = fig.add_subplot(gs[0, :]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); label(ax, "a", x=-0.02, y=0.98)
    steps = [("SAP + amendments", "pre-specified criteria;\n15 dated amendments", "#e8eef8", ENG),
             ("Development data", "eICU demo, NHANES J,\nsepsis set A, UCI, PMC", "#fdf3dc", "#b8860b"),
             ("FREEZE v14", "SHA-256 manifest\n261 files", "#eaf4ec", OK),
             ("Quarantine 1 (one shot)", "MIMIC-IV demo, NHANES H,\nsepsis set B → 2 primary\ncriteria FAILED", "#f8e3e1", BAD),
             ("Engine v7", "causal attribution,\ncontext guards;\ngate = parity", "#fdf3dc", "#b8860b"),
             ("FREEZE v15", "SHA-256 manifest\n316 files", "#eaf4ec", OK),
             ("Quarantine 2 (one shot)", "NHANES I, sepsis B2 →\nall non-inferiority\ncriteria met", "#eaf4ec", OK)]
    n = len(steps); w = 0.118; gap = (1 - n * w) / (n - 1)
    for i, (t, b, fc, ec) in enumerate(steps):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.12), w, 0.76, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec=ec, lw=1))
        ax.text(x + w / 2, 0.80, t, ha="center", va="top", fontsize=7.2, fontweight="bold")
        ax.text(x + w / 2, 0.42, b, ha="center", va="center", fontsize=6.6, linespacing=1.3)
        if i < n - 1: arrow(ax, (x + w, 0.5), (x + w + gap, 0.5), ms=8)
    ax.text(0, 0.0, "Frozen artefacts are the ones the four verification methods were later applied to; the LLM comparison, the audits and the audit study came after the freezes.", fontsize=6.6, color=GREY)
    # (b) ceiling
    ax = fig.add_subplot(gs[1, 0]); label(ax, "b")
    parts = [("no single laboratory criterion for the group", 541, "#9e9e9e"), ("key analyte absent from the first panel", 275, "#cfcfcf"),
             ("contradicted by the panel values", 431, "#e8a19c"), ("panel-supported", 1460, "#5f9e55")]
    left = 0
    for name, v, c in parts:
        ax.barh([0], [v], left=left, color=c, edgecolor="white", height=0.55)
        ax.text(left + v / 2, 0, f"{v:,}\n({100*v/2707:.0f}%)", ha="center", va="center", fontsize=7, color="white" if c in ("#9e9e9e", "#5f9e55") else "#222")
        left += v
    ax.set_yticks([]); ax.set_xlim(0, 2707); ax.set_xlabel("clinician-coded label targets, eICU-CRD demo (n = 2,707)")
    ax.set_title("Why laboratory-only recall saturates near 60 %", loc="left")
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in parts], [p[0] for p in parts], loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, frameon=False, handlelength=1)
    # (c) panel-supported
    ax = fig.add_subplot(gs[1, 1]); label(ax, "c")
    cols = ["13.4.2\n(product)", "14.1 / v6", "v7\n(frozen)", "registry\nOFF"]
    top5 = [81.6, 78.0, 78.0, 75.3]; top10 = [95.1, 91.8, 91.8, 89.9];     x = np.arange(4); bw = 0.26
    ax.bar(x - bw, top5, bw, color=ENG, label="flat top-5"); ax.bar(x, top10, bw, color="#6f8fc7", label="flat top-10")
    tt = [88.9, 89.2]
    ax.bar([1 + bw, 2 + bw], tt, bw, color="#a9bbdc", label="two-tier @5")
    for xi, v in zip(x - bw, top5): ax.text(xi, v + 1, f"{v:.1f}", ha="center", fontsize=6.3)
    for xi, v in zip(x, top10): ax.text(xi, v + 1, f"{v:.1f}", ha="center", fontsize=6.3)
    for xi, v in zip((1 + bw, 2 + bw), tt): ax.text(xi, v + 1, f"{v:.1f}", ha="center", fontsize=6.3)
    ax.set_xticks(x); ax.set_xticklabels(cols); ax.set_ylim(0, 105); ax.set_ylabel("recall on panel-supported labels (%)")
    ax.set_title("Panel-supported labels (n = 1,460)", loc="left"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3)
    save(fig, 2)

# ------------------------------------------------------------------------------------------------ Figure 3 verification results (new)
def fig3():
    fig = plt.figure(figsize=(270 * MM, 165 * MM)); gs = fig.add_gridspec(2, 2, hspace=0.6, wspace=0.42)
    # (a) activity + provenance
    ax = fig.add_subplot(gs[0, 0]); label(ax, "a")
    sets = [("dormant (never fired)", 31192), ("fired, never in a top-10", 1627), ("active core (≥1 top-10 contribution)", 364), ("hot core (≥10)", 174)]
    cols = ["#d0d0d0", "#9fb3d9", ENG, "#0d1f45"]
    y = np.arange(3)[::-1]; vals = [31192, 1627, 364]
    ax.barh(y, vals, color=cols[:3], height=0.6)
    for yi, v, s in zip(y, vals, [f"{v:,}  ({100*v/33183:.1f} %)" for v in vals]): ax.text(v * 1.15, yi, s, va="center", fontsize=7)
    ax.barh([0], [174], color=cols[3], height=0.6); ax.text(0.98, 0.04, "dark segment of the active core:\n174 hot-core rules (≥ 10 contributions)", transform=ax.transAxes, fontsize=6.3, color=GREY, va="bottom", ha="right")
    ax.set_yticks(y); ax.set_yticklabels(["dormant", "fired only", "active core"]); ax.set_xscale("log"); ax.set_xlim(50, 2e5)
    ax.set_xlabel("executable rules of registry 14.1.0 (n = 33,183; log scale)"); ax.set_title("Activity log over 3,814 real panels", loc="left")
    # (b) source concordance
    ax = fig.add_subplot(gs[0, 1]); label(ax, "b")
    rows = [("200 sampled rules\n(Note 8, three strata)", 1, 15, 184), ("100 active-core rules\n(Note 15, after re-sourcing)", 6, 2, 92)]
    for i, (nm, c, d, u) in enumerate(rows):
        n = c + d + u; left = 0
        for v, col, lab in ((c, OK, "concordant"), (d, BAD, "discordant"), (u, "#c9c9c9", "unresolvable")):
            ax.barh([1 - i], [100 * v / n], left=left, color=col, height=0.55, label=lab if i == 0 else None)
            if v / n > 0.04: ax.text(left + 50 * v / n, 1 - i, f"{v}", ha="center", va="center", fontsize=7, color="white" if col != "#c9c9c9" else "#222")
            left += 100 * v / n
        ax.text(50, 1 - i - 0.40, f"{c} concordant · {d} discordant · {u} unresolvable  (n = {n})", fontsize=6.4, color=GREY, ha="center", va="top")
    ax.set_yticks([1, 0]); ax.set_yticklabels([r[0] for r in rows]); ax.set_xlim(0, 100); ax.set_xlabel("% of sampled rules (single declared AI rater)")
    ax.set_title("Source concordance against the cited locator", loc="left"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=3)
    # (c) mutation recall
    ax = fig.add_subplot(gs[1, 0]); label(ax, "c")
    mut = [("M7 tier order impossible", 1.000, 301), ("M6 ubiquitous single analyte", 0.979, 141), ("M4 wrong unit", 0.743, 152),
           ("M1 threshold beyond physiology", 0.548, 73), ("M8 source from other domain", 0.455, 88), ("M3 operator flipped", 0.131, 274), ("M2 plausible wrong threshold", 0.003, 303)]
    y = np.arange(len(mut))[::-1]
    ax.barh(y, [m[1] for m in mut], color=[OK if m[1] >= 0.7 else ("#d9a441" if m[1] >= 0.4 else BAD) for m in mut], height=0.62)
    for yi, m in zip(y, mut): ax.text(min(m[1], 0.97) + 0.02 if m[1] < 0.9 else 0.5, yi, f"{m[1]:.2f}  (n = {m[2]})", va="center", fontsize=6.6, color="#222" if m[1] < 0.9 else "white")
    ax.set_yticks(y); ax.set_yticklabels([m[0] for m in mut]); ax.set_xlim(0, 1); ax.set_xlabel("recall of seeded defects by the static detectors")
    ax.set_title("Mutation testing of the detectors", loc="left")
    # (d) ledger
    ax = fig.add_subplot(gs[1, 1]); label(ax, "d")
    C = json.load(open(os.path.join(HG, "eval/verification_ledger/ledger_counts.json")))["by_set"]
    order = ["quote_verified", "discordant_corrected", "discordant_open", "flagged_open", "source_reachable_unverified", "unresolvable", "retired"]
    colr = [OK, "#8fc39a", BAD, "#d9a441", "#9fb3d9", "#c9c9c9", "#6a6a6a"]
    names = {"quote_verified": "quote-verified", "discordant_corrected": "discordant, corrected", "discordant_open": "discordant, open", "flagged_open": "detector flag open",
             "source_reachable_unverified": "source reachable, unverified", "unresolvable": "unresolvable", "retired": "retired (15.0.0)"}
    rows = [("curated anchors (272)", C["curated anchors (272, 14.1.0)"]), ("active core (364)", C["active core (364)"]), ("sufficiency-arm rules (335)", C["CORE arm of the sufficiency study (335, 15.1.0)"])]
    for i, (nm, c) in enumerate(rows):
        n = sum(c.values()); left = 0
        for k, col in zip(order, colr):
            v = c.get(k, 0); ax.barh([2 - i], [100 * v / n], left=left, color=col, height=0.6, label=names[k] if i == 0 else None)
            if v / n >= 0.06: ax.text(left + 50 * v / n, 2 - i, str(v), ha="center", va="center", fontsize=6.6, color="white" if col in (OK, BAD, "#6a6a6a", "#9fb3d9") else "#222")
            left += 100 * v / n
    ax.set_yticks([2, 1, 0]); ax.set_yticklabels([r[0] for r in rows]); ax.set_xlim(0, 100); ax.set_xlabel("% of rules (verification ledger, registry 15.2.0)")
    ax.set_title("What is known per rule", loc="left"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=3, handlelength=1)
    save(fig, 3)

# ------------------------------------------------------------------------------------------------ Figure 4 supervised comparison
def fig4():
    m = json.load(open(os.path.join(HG, "eval/results/eicu_demo/ml_baseline.json")))
    nice = {"acute_kidney_injury": "AKI", "chronic_kidney_disease": "CKD", "renal_impairment": "renal impairment", "diabetic_ketoacidosis": "DKA", "acute_myocardial_infarction": "AMI",
            "cirrhosis_liver_failure": "cirrhosis / liver failure", "gi_bleeding": "GI bleeding"}
    items = [(nice.get(k, k.replace("_", " ")), v) for k, v in m.items() if v["n"] >= 25]
    items.sort(key=lambda kv: kv[1]["hemoglyph"])
    fig, ax = plt.subplots(figsize=(230 * MM, 125 * MM)); y = np.arange(len(items))
    for yi, (nm, v) in zip(y, items):
        lo, hi = sorted([v["hgb"], v["logreg"]]); ax.plot([lo, hi], [yi, yi], color="#dddddd", lw=3, zorder=1)
        ax.scatter(v["hgb"], yi, color=GB, s=22, zorder=3, marker="s"); ax.scatter(v["logreg"], yi, color=LR, s=22, zorder=3, marker="^")
        ax.scatter(v["hemoglyph"], yi, color=ENG, s=34, zorder=4)
        ax.text(1.005, yi, f"n = {v['n']}", va="center", fontsize=6.3, color=GREY)
    ax.set_yticks(y); ax.set_yticklabels([i[0] for i in items]); ax.set_xlim(0.45, 1.0); ax.axvline(0.5, color="#bbbbbb", lw=0.6, ls=":")
    ax.set_xlabel("AUROC of the group probability against the clinician label (eICU-CRD demo, 2,314 stays)")
    ax.scatter([], [], color=ENG, s=34, label="Hemoglyph v7 (untrained, no parameter fitted to this cohort)")
    ax.scatter([], [], color=GB, s=22, marker="s", label="gradient boosting, 5-fold out-of-fold, trained on the labels")
    ax.scatter([], [], color=LR, s=22, marker="^", label="logistic regression, 5-fold out-of-fold")
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=1); ax.grid(axis="x", color="#eeeeee", lw=0.5)
    ax.set_title("Groups with ≥ 25 labelled stays; ordered by engine AUROC", loc="right", fontsize=7.5, color=GREY)
    save(fig, 4)

# ------------------------------------------------------------------------------------------------ Figure 5 NHANES cycles
def fig5():
    J = {"diabetes": .946, "ckd": .959, "anemia": .972, "iron_deficiency": .989, "hyperuricemia": .943, "hypercholesterolemia": .905, "alt_elevation": .872, "diabetes_selfreport": .919, "ckd_selfreport": .816}
    H = {"diabetes": .938, "ckd": .968, "anemia": .994, "iron_deficiency": None, "hyperuricemia": .958, "hypercholesterolemia": .883, "alt_elevation": .880, "diabetes_selfreport": .914, "ckd_selfreport": .748}
    I = {"diabetes": .924, "ckd": .962, "anemia": .983, "iron_deficiency": .972, "hyperuricemia": .955, "hypercholesterolemia": .886, "alt_elevation": .877, "diabetes_selfreport": .898, "ckd_selfreport": .799}
    names = [("diabetes", "diabetes\n(HbA1c/FPG/told)"), ("ckd", "CKD\n(eGFR/ACR)"), ("anemia", "anaemia\n(WHO Hb)"), ("iron_deficiency", "iron deficiency\n(ferritin < 15)"), ("hyperuricemia", "hyperuricaemia"),
             ("hypercholesterolemia", "hypercholesterol-\naemia (TC ≥ 240)"), ("alt_elevation", "ALT elevation\n(ACG)"), ("diabetes_selfreport", "self-reported\ndiabetes"), ("ckd_selfreport", "self-reported\nkidney disease")]
    fig, ax = plt.subplots(figsize=(250 * MM, 95 * MM)); x = np.arange(len(names)); bw = 0.26
    for off, D, col, lab in ((-bw, J, ENG, "2017–18 (J, development; frozen-v7 re-run)"), (0, H, "#6f8fc7", "2013–14 (H, quarantine 1)"), (bw, I, "#a9bbdc", "2015–16 (I, quarantine 2)")):
        vals = [D[k] for k, _ in names]
        ax.bar(x + off, [v if v else 0 for v in vals], bw, color=col, label=lab)
        for xi, v in zip(x + off, vals):
            ax.text(xi, (v + 0.004) if v else 0.505, f"{v:.3f}" if v else "n/a", ha="center", va="bottom", fontsize=5.6, rotation=90, color="#222" if v else GREY)
    ax.set_xticks(x); ax.set_xticklabels([n for _, n in names], fontsize=6.6); ax.set_ylim(0.5, 1.04); ax.set_ylabel("AUROC (n = 3,000 adults per cycle)")
    ax.axhline(0.5, color="#bbbbbb", lw=0.6); ax.legend(frameon=False, loc="lower left", ncol=3, bbox_to_anchor=(0, 1.0))
    ax.text(1.0, -0.2, "y-axis starts at chance (0.5). Self-reported outcomes are independent of the laboratory values. Healthy adults asserted with a disease at p ≥ 0.5: 2/485.", transform=ax.transAxes, ha="right", fontsize=6.3, color=GREY)
    save(fig, 5)

# ------------------------------------------------------------------------------------------------ Figure 6 sepsis
def fig6():
    sets = ["set A\n(development)", "set B\n(quarantine 1)", "set B2\n(quarantine 2)"]
    pred_e = [(.600, .575, .625), (.610, .583, .640), (.588, .559, .616)]; pred_l = [.691, .712, .679]
    conc_e = [(.592, .563, .621), (.638, .601, .675), (.635, .597, .673)]; conc_l = [.687, .744, .726]
    fig, axes = plt.subplots(1, 2, figsize=(250 * MM, 85 * MM), sharey=True)
    for ax, E, L, ttl in ((axes[0], pred_e, pred_l, "Prediction frame: first-24-h laboratory panel → Sepsis-3 onset at any hour"),
                          (axes[1], conc_e, conc_l, "Concurrent frame (labs + vitals), as recorded at each round: A development, B freeze-v14 one shot, B2 v7 one shot")):
        x = np.arange(3)
        for xi, (v, lo, hi), l in zip(x, E, L):
            ax.plot([xi, xi], [v, l], color="#dddddd", lw=3, zorder=1)
            ax.errorbar(xi, v, yerr=[[v - lo], [hi - v]], fmt="o", color=ENG, ms=6, capsize=3, lw=0.8, zorder=3)
            ax.scatter(xi, l, color=LR, marker="^", s=40, zorder=3)
            ax.text(xi + 0.08, v, f"{v:.3f}", fontsize=6.6, va="center", color=ENG); ax.text(xi + 0.08, l, f"{l:.3f}", fontsize=6.6, va="center", color=LR)
        ax.set_xticks(x); ax.set_xticklabels(sets); ax.set_ylim(0.5, 0.8); ax.axhline(0.5, color="#bbbbbb", lw=0.6)
        ax.set_title(ttl, loc="left", fontsize=7.4)
    axes[0].set_ylabel("AUROC (95 % CI)")
    axes[0].scatter([], [], color=ENG, s=30, label="Hemoglyph v7 sepsis score (untrained)"); axes[0].scatter([], [], color=LR, marker="^", s=30, label="supervised logistic regression (trained on the set's labels)")
    axes[0].legend(frameon=False, loc="upper left"); label(axes[0], "a"); label(axes[1], "b", x=-0.04)
    fig.text(0.01, -0.04, "PhysioNet/CinC 2019; the pre-specified criterion (AUROC ≥ 0.65 in set B, concurrent frame) was not met: a negative result reported as such.", fontsize=6.5, color=GREY)
    save(fig, 6)

# ------------------------------------------------------------------------------------------------ Figure 7 LLM + properties
def fig7():
    L = json.load(open(os.path.join(HG, "eval/results/eicu_demo/llm_vs_v7_cluster_n400.json")))["gr"]
    pg = {k: v for k, v in L["per_group"].items() if v[0] >= 10}
    nice = {"acute_kidney_injury": "AKI", "chronic_kidney_disease": "CKD", "renal_impairment": "renal impairment", "diabetic_ketoacidosis": "DKA", "acute_myocardial_infarction": "AMI", "gi_bleeding": "GI bleeding"}
    items = sorted(pg.items(), key=lambda kv: kv[1][0])
    fig = plt.figure(figsize=(270 * MM, 150 * MM)); gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], hspace=0.5, wspace=0.35)
    ax = fig.add_subplot(gs[:, 0]); label(ax, "a", x=-0.3)
    y = np.arange(len(items))
    for yi, (k, (n, e, l)) in zip(y, items):
        ax.plot([100 * l / n, 100 * e / n], [yi, yi], color="#dddddd", lw=3, zorder=1)
        ax.scatter(100 * e / n, yi, color=ENG, s=30, zorder=3); ax.scatter(100 * l / n, yi, color=LLM, s=30, zorder=3, marker="D")
        pass
    ax.set_yticks(y); ax.set_yticklabels([f"{nice.get(k, k.replace('_', ' '))}  (n = {v[0]})" for k, v in items]); ax.set_xlim(0, 100); ax.set_xlabel("recall@5 per label group (%)")
    ax.scatter([], [], color=ENG, s=30, label="Hemoglyph v7"); ax.scatter([], [], color=LLM, s=30, marker="D", label="frontier LLM (blind, same panels)")
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2); ax.set_title("Per-group recall@5 (groups with ≥ 10 labels)", loc="left", pad=22)
    ax = fig.add_subplot(gs[0, 1]); label(ax, "b", x=-0.2)
    ks = [1, 3, 5, 10]; eng = [28.2, 50.8, 59.6, 65.1]; llm = [24.0, 47.0, 60.7, 72.0]
    ax.plot(ks, eng, "-o", color=ENG, ms=5, label="Hemoglyph v7"); ax.plot(ks, llm, "-D", color=LLM, ms=4.5, label="frontier LLM")
    for k, e, l in zip(ks, eng, llm):
        up, dn = (e, l) if e >= l else (l, e); cu, cd = (ENG, LLM) if e >= l else (LLM, ENG)
        ax.text(k, up + 2.5, f"{up:.1f}", ha="center", fontsize=6.2, color=cu); ax.text(k, dn - 5.5, f"{dn:.1f}", ha="center", fontsize=6.2, color=cd)
    ax.set_xticks(ks); ax.set_xlabel("k"); ax.set_ylabel("recall@k (%)"); ax.set_ylim(10, 85); ax.legend(frameon=False, loc="lower right")
    ax.set_title("Recall@k, 400 stays / 596 labels\n(p: @1 0.013, @3 0.041, @5 0.54, @10 0.0002)", loc="left", fontsize=7.4)
    ax = fig.add_subplot(gs[1, 1]); label(ax, "c", x=-0.2)
    props = [("SI-unit invariance\n(top-5 identical, n = 40)", 40, 8, 40), ("order + distractor\ninvariance (n = 40)", 35, 10, 40), ("healthy adults with no\ndisease asserted (n = 40)", 40, 36, 40)]
    y = np.arange(3)[::-1]; bw = 0.36
    ax.barh(y + bw / 2, [100 * p[1] / p[3] for p in props], bw, color=ENG, label="engine (v8.2)"); ax.barh(y - bw / 2, [100 * p[2] / p[3] for p in props], bw, color=LLM, label="frontier LLM")
    for yi, p in zip(y, props):
        ax.text(100 * p[1] / p[3] + 1.5, yi + bw / 2, f"{p[1]}/{p[3]}", va="center", fontsize=6.4); ax.text(100 * p[2] / p[3] + 1.5, yi - bw / 2, f"{p[2]}/{p[3]}", va="center", fontsize=6.4)
    ax.set_yticks(y); ax.set_yticklabels([p[0] for p in props], fontsize=6.6); ax.set_xlim(0, 118); ax.set_xlabel("% of identical perturbed panels conforming")
    ax.set_title("Black-box property conformance (Table 6)", loc="left"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2, fontsize=6.4)
    save(fig, 7)

# ------------------------------------------------------------------------------------------------ Figure 8 calibration + DCA
def fig8():
    md = open(os.path.join(HG, "eval/results/eicu_demo/calibration_dca_v7.md"), encoding="utf-8").read()
    dec = re.findall(r"^\| (\d+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|$", md, flags=re.M)
    raw_p = [float(d[1]) for d in dec]; raw_o = [float(d[2]) for d in dec]; iso_p = [float(d[3]) for d in dec]; iso_o = [float(d[4]) for d in dec]
    blocks = re.findall(r"### (\w+) \(n=(\d+), prevalence ([\d.]+)\)\n\n\| threshold.*?\n\|[-|: ]+\n((?:\| -?[\d.]+ \| .*?\n)+)", md)
    fig = plt.figure(figsize=(300 * MM, 130 * MM)); gs = fig.add_gridspec(2, 5, hspace=0.75, wspace=0.55, width_ratios=[1.1, 1.1, 1, 1, 1])
    ax = fig.add_subplot(gs[:, 0:2]); label(ax, "a", x=-0.15)
    ax.plot([0, 1], [0, 1], color="#bbbbbb", lw=0.7, ls="--")
    ax.plot(raw_p, raw_o, "o-", color=BAD, ms=4, label="raw engine probability (ECE 0.162)"); ax.plot(iso_p, iso_o, "s-", color=OK, ms=4, label="cross-fitted isotonic (ECE 0.003)")
    ax.set_xlabel("mean predicted probability (decile)"); ax.set_ylabel("observed frequency"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(frameon=False, loc="upper left")
    ax.set_title("Reliability, all groups pooled (52,689 stay–group pairs; AUROC 0.797)", loc="left", fontsize=7.4)
    nice = {"renal_impairment": "renal impairment", "sepsis": "sepsis", "diabetes": "diabetes", "acute_kidney_injury": "AKI", "anemia": "anaemia"}
    pos = [gs[0, 2], gs[0, 3], gs[0, 4], gs[1, 2], gs[1, 3]]
    use = [b for b in blocks if b[0] in nice][:5]
    for i, (nm, n, prev, tbl) in enumerate(use):
        ax = fig.add_subplot(pos[i]); rows = [[float(x) for x in r.strip().strip("|").split("|")] for r in tbl.strip().split("\n")]
        t = [r[0] for r in rows]
        ax.plot(t, [r[3] for r in rows], color="#bbbbbb", lw=0.8, label="treat all"); ax.axhline(0, color="#bbbbbb", lw=0.8, ls=":")
        ax.plot(t, [r[1] for r in rows], color=BAD, lw=1, label="raw"); ax.plot(t, [r[2] for r in rows], color=OK, lw=1.2, label="isotonic")
        ax.set_ylim(-12, max(12, max(r[1] for r in rows) + 2)); ax.set_xlim(0.05, 0.5); ax.set_title(f"{nice[nm]} (n = {int(n):,}, prev {float(prev):.2f})", fontsize=7)
        if i == 0: label(ax, "b", x=-0.3)
        if i >= 2: ax.set_xlabel("threshold probability")
        if i in (0, 3): ax.set_ylabel("net benefit / 100")
        if i == 0: ax.legend(frameon=False, fontsize=5.8, loc="upper right")
    save(fig, 8)

if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8): f()
    print("figures ok")
