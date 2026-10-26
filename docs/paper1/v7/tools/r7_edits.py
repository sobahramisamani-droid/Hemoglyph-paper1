"""Round-7 edits (reviewer report on R6). Each anchor must match exactly once. Run once."""
import pathlib, re, sys
D = pathlib.Path("/home/user/Hemoglyph/docs/paper1")
NPJ = D / "v7/Paper1_Hemoglyph_npj_EN_v7_R1.md"; SMP = D / "v7/Paper1_Hemoglyph_SampleStyle_v7_R1.md"; RSP = D / "v7/RESPONSE_TO_REVIEWERS_R1.md"
def sub(t, old, new, label):
    n = t.count(old)
    if n != 1: sys.exit(f"ANCHOR {label}: {n} matches")
    return t.replace(old, new)

WINNER_OLD = "(challenge winner on the full hidden test: 0.36)"
WINNER_NEW = "(for orientation only, not directly comparable: the challenge winner reached 0.36 on the full hidden test with access to all 40,000 training patients, tuned thresholds and ensembles)"
PEEK = " (one disclosed deviation: the boosting hyper-parameters were tightened after a first evaluation on set B had shown over-fitting, so the set-B figures for that model are not strictly one-shot—the logistic model and set B2 are; the re-tune raised set-B hourly AUROC from 0.719 to 0.757)"
MELD_WHY = " The gate exists because MELD was derived in, and is calibrated for, patients with established hepatic dysfunction; computed on a panel with normal bilirubin and INR it reduces to a creatinine term and would mislabel isolated kidney injury as liver prognosis."

# ---------- npj ----------
t = NPJ.read_text(encoding="utf-8")
# 1. move the v8 block from Results (after sepsis) to Discussion, before Limitations
m = re.search(r"\n### Post-freeze development step \(engine v8, registry 14\.2\.0\): what the roadmap did and did not deliver\n\n(.*?)\n\n### Blinded comparison", t, re.S)
assert m, "v8 block not found"
block = m.group(1)
t = t.replace(m.group(0), "\n### Blinded comparison", 1)
block = sub(block, WINNER_OLD, WINNER_NEW, "npj winner")
block = sub(block, "trained once on PhysioNet set A and evaluated on the untouched sets B and B2.", "trained once on PhysioNet set A and evaluated on the held-out sets B and B2" + PEEK + ".", "npj peek")
block = sub(block, "After the frozen v7 results above were complete,", "After the frozen v7 results were complete,", "npj lead")
disc_v8 = "### Post-freeze roadmap (engine v8): what the review-driven proposals did and did not deliver\n\n" + block + " The full twelve-row triage is Supplementary Note 7."
t = sub(t, "\n### Limitations", "\n" + disc_v8 + "\n\n### Limitations", "npj disc insert")
# remove the Discussion one-liner that duplicated it
t = sub(t, "A post-freeze analysis of twelve reviewer-suggested improvements (Supplementary Note 7) found that the two that promised the largest gains—truncating the differential to raise precision, and suppressing covering diagnoses—would have traded recall for precision one-for-one or asserted diagnoses without their guideline criteria; the remaining recall ceiling on eICU is set by panels that lack the defining analyte and by the problem-list reference standard rather than by the reasoning layer, which is why we moved the supervised sepsis component outside the engine instead of training the engine.", "", "npj dup")
# 2. Three -> Five findings
t = sub(t, "Three findings shape how these numbers should be read.", "Five findings shape how these numbers should be read.", "npj five")
# 3. terminology
t = sub(t, "A guideline-derived rule engine with no training data recovered 61%", "A guideline-transcribed rule engine with no training data recovered 61%", "npj disc open")
t = sub(t, "An open, offline, guideline-derived rule engine interpreted structured laboratory panels", "An open, offline, guideline-transcribed rule engine—its rules transcribed from guidelines by one non-clinician author with AI assistance and not yet independently audited—interpreted structured laboratory panels", "npj concl")
# 4. abstract: precision ceiling
t = sub(t, "appeared in the top-5, at precision@5 14.2% against an incomplete problem list;", "appeared in the top-5, at precision@5 14.2% against an incomplete problem list (ceiling ≈ 21% under perfect ranking, because the list carries ~1.05 evaluable labels per stay);", "npj abstract")
# 5. MELD justification (Methods)
t = sub(t, "with sodium clamped to 125–137 mmol/L and creatinine capped at 4 mg/dL)", "with sodium clamped to 125–137 mmol/L and creatinine capped at 4 mg/dL; computed only when bilirubin > 2 mg/dL or INR > 1.5)", "npj meld1")
t = sub(t, "only)—and in registry 14.2.0, which re-sources", "only)." + MELD_WHY + " The remaining difference is registry 14.2.0, which re-sources", "npj meld2")
# 6. ablation emphasis
t = sub(t, "so it is partly redundant with the syndrome layer rather than inert.", "so it is partly redundant with the syndrome layer rather than inert—but even in the most favourable cell of the 2 × 2 ablation, 32,911 AI-drafted rules buy three recall points; registry scale is not a merit of this system and we do not claim it as one.", "npj ablation")
# 7. supplementary list: structured
t = sub(t, "\nSupplementary Note 7 and Table S16 (post-freeze v8 triage and sepsis companion) were added in revision round 6.\n\nNote 1 SAP", "\nNotes: Note 1 SAP", "npj supp a")
t = sub(t, "Table S4 subgroup recall (v7); Data 1 per-stay outputs and LLM prompts/outputs.", "Table S4 subgroup recall (v7); Note 7 evidence triage of the twelve post-review proposals (twelve rows: proposal, evidence, verdict, action); Table S16 sepsis companion risk model; Data 1 per-stay outputs and LLM prompts/outputs.", "npj supp b")
NPJ.write_text(t, encoding="utf-8")

# ---------- sample style ----------
t = SMP.read_text(encoding="utf-8")
m = re.search(r"\n### 4\.5b Post-freeze development step \(engine v8, registry 14\.2\.0\): what the roadmap did and did not deliver\n\n(.*?)\n\n### 4\.6 Blinded comparison", t, re.S)
assert m, "smp v8 block not found"
block = m.group(1)
t = t.replace(m.group(0), "\n### 4.6 Blinded comparison", 1)
block = sub(block, WINNER_OLD, WINNER_NEW, "smp winner")
block = sub(block, "trained once on PhysioNet set A and evaluated on the untouched sets B and B2.", "trained once on PhysioNet set A and evaluated on the held-out sets B and B2" + PEEK + ".", "smp peek")
block = sub(block, "After the frozen v7 results above were complete,", "After the frozen v7 results were complete,", "smp lead")
t = sub(t, "\n### 5.5 Limitations", "\n### 5.4b Post-freeze roadmap (engine v8): what the review-driven proposals did and did not deliver\n\n" + block + " The full twelve-row triage is Supplementary Note 7.\n\n### 5.5 Limitations", "smp disc insert")
t = sub(t, "A post-freeze analysis of twelve reviewer-suggested improvements (Supplementary Note 7) found that the two that promised the largest gains—truncating the differential to raise precision, and suppressing covering diagnoses—would have traded recall for precision one-for-one or asserted diagnoses without their guideline criteria; the remaining recall ceiling on eICU is set by panels that lack the defining analyte and by the problem-list reference standard rather than by the reasoning layer, which is why we moved the supervised sepsis component outside the engine instead of training the engine.", "", "smp dup")
t = sub(t, "Three findings govern how these numbers should be read.", "Five findings govern how these numbers should be read.", "smp five")
t = sub(t, "rather than what the guidelines would achieve in expert hands, not in the 33,183-rule registry: with the 32,911 AI-drafted rules switched off, flat recall@5 moved by 0.9 points.", "rather than what the guidelines would achieve in expert hands. The result does not rest on the 33,183-rule registry: with the 32,911 AI-drafted rules switched off, flat recall@5 moved by 0.9 points (3.1 points without the syndrome layer)—even in the most favourable ablation cell, the AI-drafted bulk buys three recall points, so registry scale is not a merit of this system.", "smp splice")
t = sub(t, "with sodium clamped to 125–137 mmol/L and creatinine capped at 4 mg/dL)", "with sodium clamped to 125–137 mmol/L and creatinine capped at 4 mg/dL; computed only when bilirubin > 2 mg/dL or INR > 1.5)", "smp meld1")
t = sub(t, "only)—and in registry 14.2.0, which re-sources", "only)." + MELD_WHY + " The remaining difference is registry 14.2.0, which re-sources", "smp meld2")
SMP.write_text(t, encoding="utf-8")

r = RSP.read_text(encoding="utf-8")
r += """

# Round 7 — presentation and structure (added 2026-10-26)

| item | action |
|---|---|
| "1.0% vs 59.6%", "2.0% vs 65.1%", "(k 0.69)", "elCU", "oaof048", "igure 1.1.1…", "1 1 1 …" block, orphaned page numbers, "stay outputs and reproduce.sh" | None of these strings exists in the manuscript source or in the .docx (verified by text extraction of the rebuilt files: "60.7% vs 59.6%", "72.0% vs 65.1%", "κ 0.69", "eICU", "oaf048", "Per-stay outputs"). They are artefacts of the PDF→text extraction used for review (ligature "fi", kerning of "6"/"7", table-border glyphs). We will supply the .docx and a PDF rendered by the journal's own pipeline; if a reviewer's PDF reader reproduces these, we will add a plain-text version. |
| Fig. 6 legend still read "GPT-4-class LLM" | Legend text replaced in the figure ("frontier LLM (unnamed)"); data unchanged. |
| v8 section interrupted the frozen Results | Moved out of Results into a Discussion subsection "Post-freeze roadmap (engine v8)"; Results now contain frozen v7 numbers only. |
| "Three findings" with five items | Now "Five findings" (both manuscripts); a broken splice in the sample-style Fourth finding repaired. |
| guideline-derived vs guideline-transcribed | Discussion opening and Conclusion now say "guideline-transcribed", Conclusion carries the explanatory clause. |
| Twelve proposals, five discussed | Supplementary Note 7 has the twelve-row table (proposal, evidence, verdict, action); the Discussion subsection now points to it explicitly. |
| Challenge-winner comparison | Kept for orientation with an explicit "not directly comparable" qualifier (data access, threshold tuning, ensembles). |
| Set-B re-tune is peeking | Now stated in the Discussion subsection with its effect (set-B hourly AUROC 0.719 → 0.757 for the boosting model); logistic model and set B2 remain one-shot. |
| MELD gate | Justification added in Methods (MELD is calibrated for established hepatic dysfunction; on normal bilirubin/INR it degenerates to a creatinine term). |
| 2 × 2 ablation | Discussion now states plainly that even in the most favourable cell the 32,911 AI-drafted rules buy three recall points and that registry scale is not claimed as a merit. |
| Precision ceiling in Abstract | Added ("ceiling ≈ 21% under perfect ranking"). |
| Supplementary information list | Rewritten as a structured list including Note 7 and Table S16. |
"""
RSP.write_text(r, encoding="utf-8")
print("R7 applied")
