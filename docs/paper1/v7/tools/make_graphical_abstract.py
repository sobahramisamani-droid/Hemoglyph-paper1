"""Graphical abstract for JBI (Elsevier spec: horizontal, >= 1328 px wide, legible at 13 cm). Pure matplotlib, numbers from R4."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

W, H = 13.0, 6.5                         # cm-ish proportions; saved at 300 dpi -> 3900 x 1950 px
fig = plt.figure(figsize=(W, H), dpi=300)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
INK, ACC, GREY, RED = "#1f2a44", "#2b6cb0", "#6b7280", "#b91c1c"


def box(x, y, w, h, title, lines, fc="#f5f7fb", ec=INK, ts=8.2, ls=6.4, tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top", fontsize=ts, fontweight="bold", color=tc)
    for k, t in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.62 - 0.30 * k, t, ha="center", va="top", fontsize=ls, color=INK)


def arrow(x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, lw=1.0, color=INK))


ax.text(W / 2, H - 0.22, "Hemoglyph: a verifiable, auditable, offline rule engine for laboratory-panel interpretation",
        ha="center", va="top", fontsize=9.6, fontweight="bold", color=INK)
ax.text(W / 2, H - 0.62, "Research prototype · 33,183 guideline-transcribed rules (99.2% AI-drafted, not clinically audited) · no outcome training",
        ha="center", va="top", fontsize=6.6, color=GREY)

# pipeline row
y, h = 3.55, 1.75
box(0.35, y, 2.45, h, "Structured lab panel", ["analyte–value–unit", "age · sex · encounter", "context optional"])
arrow(2.85, y + h / 2, 3.35, y + h / 2)
box(3.4, y, 3.6, h, "Engine (single Python process)",
    ["UCUM normalisation · 100 derived indices", "rule layer 33,183 leaves · ~900 syndromes", "fixed-weight fusion · covering logic"], fc="#e8f0fa", ec=ACC, tc=ACC)
arrow(7.05, y + h / 2, 7.55, y + h / 2)
box(7.6, y, 2.6, h, "Ranked, cited differential", ["≤ 25 entries, each with", "rule id · evidence role · source", "deterministic, offline"])
arrow(10.25, y + h / 2, 10.75, y + h / 2)
box(10.8, y, 1.9, h, "Verification", ["property-based tests", "on every release", "1 defect 353 vignettes missed"], fc="#fff7e6", ec="#b7791f", tc="#92400e")

# evaluation row
ax.text(0.35, 3.15, "Pre-specified, hash-frozen, one-shot evaluation (first quarantine round failed — reported)", fontsize=7.2, fontweight="bold", color=INK, va="top")
y2, h2 = 0.55, 2.15
box(0.35, y2, 2.95, h2, "eICU-CRD demo · 2,314 ICU stays", ["recall@5 60.8% (95% CI 58.7–62.9)", "precision@5 14.2%", "prevalence baseline 51.3%", "ceiling ≈ 60%: labels not in first panel"])
box(3.5, y2, 2.95, h2, "NHANES · 9,000 adults, 3 cycles", ["AUROC 0.88–0.99, reproduced", "2 false assertions / 485 healthy", "sepsis (14,420 pts): failed", "as pre-specified"])
box(6.65, y2, 2.95, h2, "Blinded vs unnamed frontier LLM", ["400 stays, identical inputs", "recall@5 60.7% vs 59.6%, p = 0.54", "LLM leads at rank 1;", "self-consistency κ 0.69"])
box(9.8, y2, 2.9, h2, "Source-concordance audit", ["200 sampled rules, frozen protocol", "92% not verifiable from locator", "≥ 7.5% demonstrably discordant", "single rater — stated limitation"], fc="#fdf2f2", ec=RED, tc=RED)

ax.text(W / 2, 0.22, "Conclusion: traceability is achievable at LLM-parity performance, but provenance granularity — not rule count — limits auditability of AI-drafted knowledge bases.",
        ha="center", va="center", fontsize=6.6, color=INK, style="italic")
fig.savefig("fig/Graphical_abstract.png", dpi=300)
fig.savefig("fig/Graphical_abstract.pdf")
print("ok")
