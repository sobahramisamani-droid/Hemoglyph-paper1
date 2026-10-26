import re
def run(p, edits):
    s=open(p).read()
    for old,new in edits:
        c=s.count(old); assert c==1,(p[-20:],c,old[:70]); s=s.replace(old,new)
    open(p,'w').write(s)
PREC=(" A laboratory-criterion adjudication of the 10,380 top-5 label-group assertions (fixed single-analyte criteria written before scoring; Supplementary Table S11) found 14.2% on the problem list, a further 54.8% not coded but satisfying the group's laboratory criterion in the same panel (e.g. hypokalaemia with potassium < 3.5 mmol/L), 12.6% criterion-negative — the closest available estimate of true false positives — and 18.4% in groups without a single-analyte criterion. Precision@5 therefore lies between 14.2% (problem list) and 69.0% (problem list or laboratory criterion); the criterion-positive assertions are laboratory findings that were real but not charted as diagnoses, and whether they were clinically useful cannot be judged without a clinician.")
ARMNOTE="\nArm definitions (full definitions and environment switches in Supplementary Note 3 / `eval/ablation/run_ablation.py`): *rule-engine vote off* removes the rule_engine channel from fusion, through which both registry rules and expert-syndrome constellations vote, so it is a superset of *syndrome layer off*, which silences only the ~900 constellations while registry rules remain; *anchor-only* keeps the 272 curated rules and the syndrome layer. The mean AUROC column covers the 24 laboratory-detectable groups with ≥ 5 listed stays and a group score; the multiplicity analysis covers all 29 groups with ≥ 10 coded labels, including five without a single-analyte criterion.\n"
# ---------------- npj ----------------
run('Paper1_Hemoglyph_npj_EN_v7_R1.md',[
("# An untrained, auditable, locally run guideline-rule engine for structured laboratory-panel interpretation",
 "# An untrained, auditable, locally run guideline-derived rule engine for structured laboratory-panel interpretation"),
("survey-weighted screening AUROCs of 0.89–0.98 reproduced across cycles with 2 false assertions among 485 healthy adults.",
 "screening AUROCs reproduced across three cycles (0.89–0.99 for six laboratory-defined targets, 0.71–0.88 for ALT elevation) with 2 false assertions among 485 healthy adults."),
("and reproduced screening AUROCs of 0.89–0.98 across three NHANES cycles,",
 "and reproduced screening AUROCs across three NHANES cycles (0.89–0.99 for six targets; lower, 0.71–0.88, for ALT elevation),"),
("A guideline-rule engine with no training data recovered 61%",
 "A guideline-derived rule engine with no training data recovered 61%"),
("Here we report the design and a pre-registered, multi-dataset retrospective evaluation of Hemoglyph.",
 "Here we report the design and a pre-registered, multi-dataset retrospective evaluation of Hemoglyph. Every result concerns the inference engine fed with structured analyte–value pairs; the optical-character-recognition front end of the desktop product was not evaluated, and a free-text parser tested on case reports performed poorly, so the figures below should not be read as end-to-end performance from a scanned report."),
# NHANES ALT
("hyperuricaemia 0.943/0.958/0.955 and hypercholesterolaemia 0.902/0.883/0.886 (Fig. 4; Table 3).",
 "hyperuricaemia 0.943/0.958/0.955, hypercholesterolaemia 0.902/0.883/0.886 and ALT elevation 0.721/0.880/0.877 (Fig. 4; Table 3). ALT elevation is the seventh pre-specified target and the weakest: the engine grades ALT against sex-specific ACG limits whereas the 2017–18 development label used a higher threshold that was corrected under Amendment 14, which is why that cycle is lower; it is reported in full rather than omitted (weighted 0.710/0.869/0.866, Supplementary Table S7)."),
("| NHANES I: diabetes / CKD / anaemia / iron deficiency / hyperuricaemia / hypercholesterolaemia | AUROC | 0.924 / 0.962 / 0.983 / 0.972 / 0.955 / 0.886 |",
 "| NHANES J / H / I: diabetes | AUROC | 0.945 / 0.938 / 0.924 |\n| NHANES J / H / I: CKD | AUROC | 0.958 / 0.968 / 0.962 |\n| NHANES J / H / I: anaemia | AUROC | 0.973 / 0.994 / 0.983 |\n| NHANES J / H / I: iron deficiency | AUROC | 0.990 / – / 0.972 |\n| NHANES J / H / I: hyperuricaemia | AUROC | 0.943 / 0.958 / 0.955 |\n| NHANES J / H / I: hypercholesterolaemia | AUROC | 0.902 / 0.883 / 0.886 |\n| NHANES J / H / I: ALT elevation (ACG sex-specific) | AUROC | 0.721 / 0.880 / 0.877 |"),
("| NHANES I: self-reported diabetes / kidney disease | AUROC | 0.898 / 0.799 |",
 "| NHANES J / H / I: self-reported diabetes | AUROC | 0.918 / 0.914 / 0.898 |\n| NHANES J / H / I: self-reported kidney disease | AUROC | 0.816 / 0.748 / 0.799 |"),
("| UCI thyroid: hypothyroidism (655 vs 6,082) / hyperthyroidism (195 vs 6,082) | AUROC | 0.979 (0.974–0.983) / 0.798 (0.783–0.814) |",
 "| UCI thyroid0387 (9,172 records → 7,743 with TSH and non-excluded class; 811 in other classes not scored, Supplementary Table S13): hypothyroidism 655 vs 6,082 / hyperthyroidism 195 vs 6,082 | AUROC | 0.979 (0.974–0.983) / 0.798 (0.783–0.814) |"),
("| UCI HCV: any liver disease (75 vs 533) / cirrhosis (30 vs 578) | AUROC | 0.925 (0.881–0.962) / 0.909 (0.837–0.969) |",
 "| UCI HCV (615 = 533 donors, 7 suspect donors excluded from both tasks, 75 with liver disease): any liver disease 75 vs 533 / cirrhosis 30 vs 578 | AUROC | 0.925 (0.881–0.962) / 0.909 (0.837–0.969) |"),
("| historical: engine v5.1 (first submission) | 64.4% (60.5–68.2) | 59.6% | +4.9 pp | 0.009 (naive McNemar) |",
 "| historical: engine v5.1 (first submission; superseded — naive McNemar ignored stay clustering; the v7 row with cluster-adjusted p = 0.54 is the result) | 64.4% (60.5–68.2) | 59.6% | +4.9 pp | 0.009 (naive) |"),
("LLM: a general-purpose GPT-4-class model (October 2026) run by the authors, blinded to labels, with a fixed prompt",
 "LLM: a general-purpose GPT-4-class model run by the authors through a chat interface on 2026-10-21 (n = 60), 2026-10-22 (n = 100) and 2026-10-23 (n = 240), re-read 2026-10-24 and alternative prompt 2026-10-25; the interface exposes no temperature or sampling parameters, so these are the provider defaults; model identity is withheld in the manuscript at the platform's request and disclosed to the editor and reviewers confidentially; blinded to labels, with a fixed prompt"),
("so the engine's advantage lies in ranking, not list coverage (Supplementary Table S11).",
 "so the engine's advantage lies in ranking, not list coverage (Supplementary Table S11)."+PREC),
("Twenty-seven of 29 per-group AUROCs exceeded 0.5 after Benjamini–Hochberg adjustment.",
 "Twenty-seven of the 29 groups with ≥ 10 coded labels (five of them without a single-analyte criterion, hence absent from the 24-group mean AUROC of Table 5) had per-group AUROCs above 0.5 after Benjamini–Hochberg adjustment."),
("The release passed the non-regression gate (no vignette, perturbation pair or healthy panel that passed in the prior release may fail):",
 "The release passed the non-regression gate (defined in Supplementary Note 4: no vignette, perturbation pair or healthy panel that passed in the prior release may fail; both residual failures below pre-date v7):"),
("(written by the first author from guideline criteria and, like the registry, not independently validated), not in the 33,000-rule registry",
 "(written by the first author from guideline criteria and, like the registry, not independently validated), not in the 33,000-rule registry. We therefore describe Hemoglyph as a guideline-*derived* engine: its knowledge was transcribed from guidelines by one non-clinician author with AI assistance, and the components that carry the result are exactly the ones that an independent audit has not yet examined; the result should be read as what such a transcription achieves, not as what the guidelines themselves would achieve"),
("7. Machine learning-based models for screening of anemia and leukemia using features of complete blood count reports. *Sci Rep* 2025. https://doi.org/10.1038/s41598-025-21279-w",
 "7. Amjad H, Hussain Z, Hasan M, Ul Hassan M. Machine learning-based models for screening of anemia and leukemia using features of complete blood count reports. *Sci Rep* 2025;15:33333."),
("18. The evaluation illusion: benchmark instability in clinical large-language-model studies. *npj Digit Med* 2025 (s41746-025-01963-x).",
 "18. Agrawal M, Chen IY, Gulamali F, Joshi S. The evaluation illusion of large language models in medicine. *npj Digit Med* 2025;8:600."),
("Table S12 fusion-weight sensitivity;","Table S12 fusion-weight sensitivity; Table S13 participant flow for the UCI thyroid and HCV cohorts; Note 4 regression-gate definition and residual failures;"),
])
s=open('Paper1_Hemoglyph_npj_EN_v7_R1.md').read()
# Table 2 footnote and Table 5 note
s=s.replace("CIs for the v7 row are stay-clustered (top-3 45.8–50.0; top-5 58.7–62.9; top-10 72.2–76.0).",
 "CIs for the v7 row are stay-clustered (top-3 45.8–50.0; top-5 58.7–62.9; top-10 72.2–76.0). The last row is a historical ablation performed on engine v5.3 before the registry revisions and is kept only for continuity with the first submission; the ablations that belong to the evaluated release are those of Table 5.",1)
m=re.search(r"(\*\*Table 5 \|[^\n]*\n\n(?:\|[^\n]*\n)+)",s); assert m; s=s.replace(m.group(1),m.group(1)+ARMNOTE,1)
open('Paper1_Hemoglyph_npj_EN_v7_R1.md','w').write(s)
# ---------------- Sample ----------------
run('Paper1_Hemoglyph_SampleStyle_v7_R1.md',[
("Screening AUROCs were 0.72–0.99 depending on target and reproduced across cycles;",
 "Screening AUROCs were 0.89–0.99 for six laboratory-defined targets and 0.72–0.88 for ALT elevation, and reproduced across cycles;"),
("The paper is organised as follows.",
 "All reported results concern the inference engine fed with structured analyte–value pairs; the OCR front end of the desktop product was not evaluated, and the free-text parser tested on case reports performed poorly (Section 4.5), so none of the figures should be read as end-to-end performance from a scanned report. The paper is organised as follows."),
("| registry off, engine v5.3 (historical ablation; v7 ablations in Table 5) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |",
 "| registry off, engine v5.3 (historical ablation from the first submission, kept for continuity; the ablations of the evaluated release are in Table 5) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |"),
("| UCI thyroid0387: hypothyroidism (655 vs 6,082) / hyperthyroidism (195 vs 6,082) |",
 "| UCI thyroid0387 (9,172 → 7,743 scorable; 811 other-class records not in either task, Supplementary Table S13): hypothyroidism 655 vs 6,082 / hyperthyroidism 195 vs 6,082 |"),
("| UCI HCV: any liver disease (75 vs 533) / cirrhosis (30 vs 578) |",
 "| UCI HCV (615 = 533 donors + 7 suspect donors excluded from both tasks + 75 liver disease): any liver disease 75 vs 533 / cirrhosis 30 vs 578 |"),
("| historical: engine v5.1 recall@5 | 64.4% (60.5–68.2) | 59.6% | +4.9 pp | 0.009 (na",
 "| historical: engine v5.1 recall@5 (superseded; naive McNemar ignored stay clustering — the v7 row is the result) | 64.4% (60.5–68.2) | 59.6% | +4.9 pp | 0.009 (na"),
("a general-purpose GPT-4-class LLM (October 2026) run by the authors, blinded to labels, with a fixed prompt",
 "a general-purpose GPT-4-class LLM run by the authors through a chat interface (runs on 2026-10-21, -22 and -23 for n = 60/100/240; re-read 2026-10-24; alternative prompt 2026-10-25; no temperature or sampling parameters are exposed by the interface, so provider defaults apply; model identity withheld at the platform's request and disclosed confidentially to the editor and reviewers), blinded to labels, with a fixed prompt"),
("a lower bound given problem-list incompleteness (Supplementary Table S11).",
 "a lower bound given problem-list incompleteness (Supplementary Table S11)."+PREC),
("Twenty-seven of 29 per-group AUROCs remained above 0.5 after Benjamini–Hochberg ",
 "Twenty-seven of the 29 groups with ≥ 10 coded labels (five without a single-analyte criterion, hence absent from the 24-group mean AUROC of Table 5) had AUROCs above 0.5 after Benjamini–Hochberg "),
("the ~900 hand-curated syndrome constellations (−9.5 points; these were written by the first author from guideline criteria and, like the registry, have not been independently validated)",
 "the ~900 hand-curated syndrome constellations (−9.5 points; these were written by the first author from guideline criteria and, like the registry, have not been independently validated). The system is therefore best described as guideline-*derived*: its knowledge was transcribed from guidelines by a non-clinician author with AI assistance, the components that carry the result are precisely those no independent audit has examined, and the result measures what that transcription achieves rather than what the guidelines would achieve in expert hands"),
("8. Scoping review of rule-based systems in clinical decision-making. (2025). *PMC* 12482788.",
 "8. Scoping review of rule-based systems in clinical decision-making. (2025). PMC 12482788 [author list to be completed from the record]."),
("10. Machine learning-based models for screening of anemia and leukemia using features of complete blood count reports. (2025). *Scientific Reports*. https://doi.org/10.1038/s41598-025-21279-w",
 "10. Amjad, H., Hussain, Z., Hasan, M., & Ul Hassan, M. (2025). Machine learning-based models for screening of anemia and leukemia using features of complete blood count reports. *Scientific Reports*, 15, 33333. https://doi.org/10.1038/s41598-025-21279-w"),
("Table S12 fusion-weight sensitivity;","Table S12 fusion-weight sensitivity; Table S13 participant flow for the UCI thyroid and HCV cohorts; Note 4 regression-gate definition and residual failures;"),
])
s=open('Paper1_Hemoglyph_SampleStyle_v7_R1.md').read()
m=re.search(r"(Table 5\. Component ablation[^\n]*\n\n(?:\|[^\n]*\n)+)",s); assert m; s=s.replace(m.group(1),m.group(1)+ARMNOTE,1)
open('Paper1_Hemoglyph_SampleStyle_v7_R1.md','w').write(s)
print('ok')
