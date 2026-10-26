import re,sys
p='Paper1_Hemoglyph_SampleStyle_v7_R1.md'; s=open(p).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt, (s.count(old), old[:80])
    s=s.replace(old,new)
# --- abstract: healthy total, PMC parser, precision/alert burden
rep("reproduced across cycles with at most one false assertion among 246 healthy adults.",
    "reproduced across cycles; among 485 guideline-healthy adults the engine asserted disease twice (2/485). Label-group precision@5 against the ICU problem list was 14.2% (F1 23.1%, NDCG@5 56.5%; a prevalence-ranking baseline reached recall@5 51.3% and NDCG@5 39.0%). On 50 published case reports the end-to-end parser placed the final diagnosis in the top-5 in 10% of cases (44% with the syndrome layer only), showing that free-text extraction, not reasoning, is the bottleneck.")
# --- 2.2 registry reconciliation
rep("Of 34,673 rule records, 1,474 were retired across releases 13.3–14.1 (superseded, domain artefacts or template artefacts), leaving 33,183 executable rules. Of these, 272 (0.8%) are manually curated guideline anchors and 32,901 (99.2%) carry the status `candidate_requires_specialist_validation`, which the engine exposes in every output so that the origin of knowledge is transparent. A provenance audit of the 781 sources in release 13.4.1 resolved",
    "Of 34,673 rule records in release 14.1.0, 1,487 are retired (1,139 at 13.3.0, 171 domain artefacts and 164 template artefacts at 13.4.0, 9 non-specific single-marker rules, 3 empty expressions, 1 at 14.0) and 3 candidates lack an executable expression, leaving 33,183 executable rules (Supplementary Table S10 reconciles every count against the live file). Of these, 272 (0.8%) are manually curated guideline anchors, 13 are former anchors demoted to candidate status at 13.4.2/14.0, and 32,898 (99.1%) carry the status `candidate_requires_specialist_validation`, which the engine exposes in every output so that the origin of knowledge is transparent; 55 executable rules carry no evidence-tier field. Earlier drafts quoted 1,474 retired and 32,901 candidates (the latter counted the 3 non-executable candidates; the former omitted the 13 demotions); the figures here are computed from the shipped file. The source table lists 785 sources (781 at 13.4.1; four added at 14.0–14.1); 388 of them are cited by at least one executable rule, the remainder only by retired rules or disease records. A provenance audit of the 781 sources in release 13.4.1 resolved")
rep("rules were flagged `unverified_source`.",
    "rules were flagged `unverified_source`. In the desktop interface every differential entry shows its evidence tier and status (anchor / candidate / unverified source) next to the score, and the validation status of each rule is machine-readable in the registry (`status`, `evidence_tier`, `executable`).")
# --- 2.4 "calibrated point score" wording
rep("Fourth, the final ranking is determined by the calibrated point score of Section 2.4,",
    "Fourth, the final ranking is determined by the fused point score of Section 2.4 (a rank score with a confidence shrinkage step; it is not a calibrated probability, see Section 4.7),")
rep("explicit abstention and a calibrated rank score.","explicit abstention and a confidence-shrunk rank score.")
# --- 2.1 hardware
rep("The system runs entirely on the local CPU in about one second per panel.",
    "The system runs entirely on the local CPU in about one second per panel (median 380–480 ms, p95 ≈ 0.9 s, on a single core of a 2019 laptop-class x86-64 CPU; the evaluation sandbox, 2 GB RAM, processed one eICU stay per second including I/O).")
rep("the optional multimodal OCR back-end is the only component that may contact a server when the user enables it, and no medical data are transmitted by any other component.",
    "the optional multimodal OCR back-end is a remote service: when the user enables it, the report image leaves the device, so the release makes no offline claim for that path and \"fully offline\" applies to the structured-input engine evaluated here. The desktop application is distributed under a proprietary licence with node-locked activation; the engine source, registries and evaluation scripts are the open components.")
rep("We present Hemoglyph, a desktop, fully offline, deterministic CDSS","We present Hemoglyph, a research-prototype desktop CDSS whose deterministic inference engine runs fully offline and")
# --- 2.7 regression gate threshold + failures
rep("and an SI/conventional unit-twin battery. The evaluated release",
    "and an SI/conventional unit-twin battery. The pass criterion is non-regression: no vignette, perturbation pair or healthy panel that passed in the previous release may fail, and the healthy sweep must stay at zero assertions. The two residual failures are longstanding and documented: in the third vignette battery the engine ranks alcoholic pancreatitis second behind alcohol-use disorder (77/78), and in the perturbation battery thiazide-associated hypovolaemic hyponatraemia is brittle in 2 of 5 noisy replicates (753/755; 752/755 in 14.1). The evaluated release")
# --- 3.1 non-inferiority margins
rep("The criteria were then re-specified as non-inferiority with dated justification (Amendment 15, 2026-10-25, written before any Round-2 data were downloaded)",
    "The criteria were then re-specified as non-inferiority with dated justification (Amendment 15, 2026-10-25, written after the Round-1 result was known but before any Round-2 file was opened; the Round-2 archive had been downloaded unread beforehand): NHANES AUROC within 0.03 of the previous release for each of six laboratory-defined targets with ≤ 1% false assertions in healthy adults; sepsis AUROC not more than 0.02 below the previous release with a control flag rate ≤ 20%; and no new failure in the safety batteries")
rep("were corrected before scoring without touching the engine and are documented.",
    "were corrected before scoring without touching the engine and are documented; the first NHANES run without the dropped variable is kept (`report_v7_run1_noACR.md`) and differs only in the CKD task, which could not be scored without it.")
# --- 3.3 metrics: add precision etc.
rep("The primary metric in eICU is flat recall@k (k = 3, 5, 10)",
    "In response to review we also report label-group precision@k, F1@k and NDCG@k (binary relevance, ideal DCG over the coded labels), the mean number of label-group assertions per stay (alert burden), per-group positive predictive value against the problem list, and a prevalence-ranking baseline that lists the groups in order of cohort frequency among those whose key analyte is present (Supplementary Table S11). Because the problem list is incomplete, precision and PPV are lower bounds. The primary metric in eICU is flat recall@k (k = 3, 5, 10)")
# --- Table 2 registry-off row
rep("| registry off (ablation) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |",
    "| registry off, engine v5.3 (historical ablation; v7 ablations in Table 5) | 47.6 | 62.0 | 75.4 | — | 75.3 / 89.9 | — |")
# --- Table 3 n / prevalence
rep("| UCI thyroid0387 | Garvan Institute referral laboratory | SI | expert diagnostic comment | external | 3,162 records |",
    "| UCI thyroid0387 | Garvan Institute referral laboratory | SI | expert diagnostic comment | external | 7,743 records with TSH (655 hypothyroid, 195 hyperthyroid, 6,082 no-comment controls) |")
rep("| UCI HCV (Hoffmann 2018) | German donors and hepatology clinic | SI | clinical category | external | 615 |",
    "| UCI HCV (Hoffmann 2018) | German donors and hepatology clinic | SI | clinical category | external | 615 (533 donors, 7 suspect, 24 hepatitis, 21 fibrosis, 30 cirrhosis) |")
rep("| ILPD | Andhra Pradesh, India | conventional | liver-patient status | external | 583 |",
    "| ILPD | Andhra Pradesh, India | conventional | liver-patient status | external | 583 (416 liver patients, 167 non-patients) |")
rep("| UCI thyroid0387: hypothyroidism / hyperthyroidism | AUROC 0.979 (sens 0.969, spec 0.951) / 0.798 | | |",
    "| UCI thyroid0387: hypothyroidism (655 vs 6,082) / hyperthyroidism (195 vs 6,082) | AUROC 0.979 (0.974–0.983; sens 0.969, spec 0.951) / 0.798 (0.783–0.814) | | |")
rep("| UCI HCV: any liver disease / cirrhosis | AUROC 0.925 (0.881–0.962) / 0.909 | | |",
    "| UCI HCV: any liver disease (75 vs 533) / cirrhosis (30 vs 578) | AUROC 0.925 (0.881–0.962) / 0.909 (0.837–0.969) | | |")
rep("| ILPD: liver patient | AUROC 0.704 (0.661–0.747) | | |",
    "| ILPD: liver patient (416 vs 167) | AUROC 0.704 (0.661–0.747) | | |")
rep("| UCI / ILPD / MIMIC rows: n = 3,162 / 615 / 583 / 235 admissions; 95% CI in Supplementary Table S3b | | | |",
    "| UCI thyroid / HCV / ILPD / MIMIC rows: n = 7,743 / 615 / 583 / 235 admissions; 95% CI in Supplementary Table S3b | | | |")
# --- Results 4.1 add precision paragraph after cohort-flow paragraph (line 119 starts "The reference standard bounds")
rep("The reference standard bounds this metric (Fig. 3b;",
    "Recall is only one side of the list. At the label-group level the engine asserted a mean of 4.5 groups per stay within its top-5 and 8.0 across the full differential; precision@5 was 14.2% (95% CI 13.3–15.2), F1@5 23.1% and NDCG@5 56.5% (54.1–58.8). A prevalence-ranking baseline that simply lists the most frequent groups whose key analyte is present reached recall@5 51.3% and NDCG@5 39.0%, and at k = 10 its recall (76.8%) exceeded the engine's (74.1%), because ten slots cover almost every frequent group; the engine's advantage is therefore in ranking (NDCG, recall@3 47.9% vs 36.1%), not in list coverage at k = 10. Per-group PPV against the problem list ranged from 69% (diabetic ketoacidosis) to below 10% for findings that are rarely coded as diagnoses (hypocalcaemia, leukocytosis, metabolic acidosis), a lower bound given problem-list incompleteness (Supplementary Table S11). The reference standard bounds this metric (Fig. 3b;")
# --- Results 4.6 healthy total
rep("Among guideline-healthy adults the engine asserted disease in 1/160, 1/246 and 0/79.",
    "Among guideline-healthy adults the engine asserted disease in 1/160, 1/246 and 0/79 (2/485 overall; 95% CI 0.1–1.5%).")
# --- Discussion: ~900 syndromes not independently validated; matches or exceeds
rep("and the ~900 hand-curated syndrome constellations (−9.5 points)",
    "and the ~900 hand-curated syndrome constellations (−9.5 points; these were written by the first author from guideline criteria and, like the registry, have not been independently validated)")
# --- COI
rep("Competing interests. S.B. is the sole developer of Hemoglyph, whose desktop application is distributed under a proprietary licence; the engine and registries are open.",
    "Competing interests. S.B. designed and wrote the Hemoglyph software, owns the proprietary desktop application and would benefit from its commercial distribution; this constitutes a financial interest in a favourable evaluation, which the pre-registered one-shot design and the released evaluation scripts are intended to constrain. The engine source, registries and evaluation code are open.")
# --- ref 20 + move 36/37 to end
rep("20. Massachusetts General Brigham Laboratory of Computer Science. (2025). DXplain versus GPT-4 and Gemini on 36 clinical cases with and without laboratory data. [Preprint record to be supplied by co-authors before submission; cited claim limited to the published percentages.]",
    "20. Feldman, M. J., Hoffer, E. P., Conley, J. J., et al. (2025). Dedicated AI expert system vs generative AI with large language model for clinical diagnoses. *JAMA Network Open*, 8(5), e2512994.")
m36=re.search(r"\n36\. Durkalski[^\n]*\n37\. Obuchowski[^\n]*\n",s); assert m36
block=m36.group(0); s=s.replace(block,"\n")
lastref=re.findall(r"\n(\d+)\. [^\n]+",s); n=max(int(x) for x in lastref); assert n==35, n
# append after ref 35
m35=re.search(r"\n35\. [^\n]+\n",s); s=s[:m35.end()]+block.strip("\n")+"\n"+s[m35.end():]
# --- supplementary list
rep("Note 1 SAP and amendments 1–15 (dated, with before/after-observation flag); Note 2 LLM comparison protocol, prompts, contamination analysis and outputs;",
    "Note 1 SAP and amendments 1–15 (dated, with before/after-observation flag); Note 2 LLM comparison protocol, prompts, contamination analysis and outputs; Note 3 formal statement of the fusion and Theory-of-Evidence layer (mass assignment, reliability discounting, closed-form Yager combination, evidence states) with the weight profiles and the 27 cross-field consistency identities; Supplementary Fig. S1 historical LLM comparison against engine v5.1; Table S10 registry count reconciliation (14.1.0 live file); Table S11 precision / F1 / NDCG / alert burden / per-group PPV and prevalence baseline; Table S12 fusion-weight sensitivity;")
open(p,'w').write(s); print('sample ok')
