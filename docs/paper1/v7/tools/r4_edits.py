"""Round-4 review edits (run-independent part). Every replacement must match exactly once."""
import sys, pathlib
ROOT = pathlib.Path("/home/user/Hemoglyph/docs/paper1/v7")
NPJ = ROOT / "Paper1_Hemoglyph_npj_EN_v7_R1.md"
SMP = ROOT / "Paper1_Hemoglyph_SampleStyle_v7_R1.md"

LLM_ID = ("the LLM was accessed through the Arena.ai agent platform, which routes requests among several "
          "frontier model families (including GPT, Claude and Gemini) and does not expose the specific model or "
          "version to the user; 'GPT-4-class' therefore denotes a capability tier, not a verified identity, and the "
          "comparison cannot be reproduced against a named model version—a limitation stated in the Discussion")

NPJ_EDITS = [
 # 33 title; 1 pre-registered
 ("# An untrained, auditable, locally run guideline-derived rule engine for structured laboratory-panel interpretation: pre-registered multi-dataset evaluation with one-shot quarantine, component ablation and a blinded comparison against a GPT-4-class language model",
  "# An untrained, auditable, locally run, AI-drafted guideline-sourced rule engine for structured laboratory-panel interpretation: pre-specified multi-dataset evaluation with one-shot quarantine, component ablation and a blinded comparison against a GPT-4-class language model"),
 # 32 + COI in Intro; engine identity with product
 ("We frame this as an engineering and retrospective evaluation study of a research prototype, no",
  "The inference engine evaluated here is the same single source file (`analyse_gidlines.py`, engine v7) that ships inside a proprietary desktop product owned by the first author; this financial interest is declared in full under Competing interests and motivated the frozen, one-shot design. We frame this as an engineering and retrospective evaluation study of a research prototype, no"),
 # 1 pre-registration heading/wording
 ("Evaluation followed a statistical analysis plan with 15 dated amendments (Supplementary Note 1).",
  "Evaluation followed an internal statistical analysis plan with 15 dated amendments (Supplementary Note 1). The plan was time-stamped and hash-frozen inside the project repository but was not deposited in a public registry; we therefore use 'pre-specified', not 'pre-registered', throughout."),
 ("Quarantine data had never been run before the freeze and were run once.",
  "Quarantine data had never been run before the freeze and were run once; the only exception is the MIMIC-IV demo, which was re-run post hoc with the frozen v7 for comparability and is labelled as such."),
 # 2 MIMIC labelling
 ("top-5/10 recall was 47.9/61.7% for engine v6 in quarantine round 1 and 47.5/62.1% when re-run with the frozen v7.",
  "top-5/10 recall was 47.9/61.7% for engine v6 in quarantine round 1 and 47.5/62.1% when the same admissions were re-run post hoc with the frozen v7 (no longer a one-shot result)."),
 ("| MIMIC-IV demo (v6, quarantine 1 / v7 re-run) | recall @5 / @10 | 47.9 / 61.7% / 47.5 / 62.1% |",
  "| MIMIC-IV demo (v6, one-shot quarantine 1 / v7 post-hoc re-run) | recall @5 / @10 | 47.9 / 61.7% / 47.5 / 62.1% |"),
 ("| external | 7,743 records (655 / 195 / 6,082) |", "| external | 7,743 records with TSH; 6,932 scored (655 / 195 / 6,082) + 811 other classes |"),
 # 7 thyroid
 ("On the UCI thyroid referral set (7,743 records with TSH; 655 hypothyroid, 195 hyperthyroid, 6,082 controls)",
  "On the UCI thyroid referral set (7,743 records with TSH, of which 6,932 were scored—655 hypothyroid, 195 hyperthyroid, 6,082 controls—and 811 belonged to other diagnostic classes outside the two tasks)"),
 # 8 sepsis CIs + engine version per set
 ("discriminated Sepsis-3 onset with AUROC 0.600, 0.610 and 0.588 (95% CI 0.559–0.616) in sets A, B and B2, versus 0.691, 0.712 and 0.679 for a supervised logistic model on the same features.",
  "discriminated Sepsis-3 onset with AUROC 0.600 (95% CI 0.575–0.625) in development set A and 0.610 (0.583–0.640) in quarantine set B (both engine v6.1/registry 14.1.0), and 0.588 (0.559–0.616) in quarantine set B2 with the frozen v7, versus 0.691, 0.712 and 0.679 for a supervised logistic model on the same features."),
 # 10 LLM identity
 ("the interface exposes no temperature or sampling parameters, so these are the provider defaults; model identity is withheld in the manuscript at the platform's request and disclosed to the editor and reviewers confidentially; blinded to labels,",
  "the interface exposes no temperature or sampling parameters, so these are the provider defaults; " + LLM_ID + "; blinded to labels,"),
 ("Model identity is withheld by design; prompts, outputs and the full protocol are released (Supplementary Note 2).",
  "Prompts, outputs and the full protocol are released (Supplementary Note 2)."),
 ("The LLM comparison is an author-run self-baseline with one model family and two prompts, no retrieval augmentation and no clinician adjudication of either output; the model's training data may include the public eICU demo.",
  "The LLM comparison is an author-run self-baseline accessed through an agent platform that does not disclose the model or version, so the LLM arm is not reproducible against a named model; it used two prompts, no retrieval augmentation and no clinician adjudication of either output, and the model's training data may include the public eICU demo."),
 # 16 expert floor definition
 ("fixed-weight fusion with an expert floor of 0.90 × rule vote;",
  "fixed-weight fusion with an expert floor (the fused score of a diagnosis cannot fall below 0.90 × the rule-layer vote, so that the four learned-style layers can modulate but never veto a guideline rule);"),
 # 17 adjudication -> criterion matching
 ("A laboratory-criterion adjudication of the 10,380 top-5 label-group assertions (fixed single-analyte criteria written before scoring; Supplementary Table S11)",
  "Automated laboratory-criterion matching of the 10,380 top-5 label-group assertions (4.486 assertions per stay × 2,314 stays; fixed single-analyte criteria written before scoring, not clinician adjudication; Supplementary Table S11)"),
 # 6 subgroups
 ("Recall@5 was 65.4% (62.6–68.2) in men and 61.1% (57.1–65.3) in women, 60–67% across age bands and 63–66% across the three largest ethnicity strata; the engine contains no race term.",
  "Recall@5 was 62.3% (59.5–64.9; 1,392 stays) in men and 58.5% (54.4–62.3; 922 stays) in women, 58–64% across age bands and 59–61% across the three largest ethnicity strata (Caucasian 60.9%, African American 60.2%, Hispanic 59.3%; Supplementary Table S14). The engine contains no race or ethnicity term: the registry text has no occurrence of 'race', 'ethnic', 'African', 'Black', 'Caucasian' or 'Hispanic', 'white' appears only in 'white blood cell', and the engine's optional `ethnicity` context field is parsed but never read by any rule or layer."),
 # 21 BH failures
 ("had per-group AUROCs above 0.5 after Benjamini–Hochberg adjustment.",
  "had per-group AUROCs above 0.5 after Benjamini–Hochberg adjustment; the two exceptions were malnutrition (n = 16, AUROC 0.515) and hypocalcaemia (n = 10, 0.627), both small groups without a dedicated single-analyte signal in the first panel."),
 # 25 752/755 phrasing + 45
 ("753/755 perturbation pairs (752/755 in 14.1; the brittle case is thiazide-associated hyponatraemia under 3% noise)",
  "753/755 perturbation pairs (752/755 in release 14.1; all failures, then and now, are replicates of one vignette—thiazide-associated hyponatraemia under 3% noise—of which v7 recovered one replicate and two remain; the full failure list is in Supplementary Note 4)"),
 # 44 'none fitted' support
 ("Engine changes between releases (C1–C16) are listed with dates in Supplementary Table S1; none was fitted to outcome data and no rule was written for a specific missed case.",
  "Engine changes between releases (C1–C16) are listed with dates in Supplementary Table S1; none was fitted to outcome data and no rule was written for a specific missed case. This is supported by the dated change log and by the fact that every change is expressed as a guideline citation plus a synthetic vignette rather than a parameter value; no version-control history exists for the development period, so the statement cannot be audited by commit diff and is offered as a documented process claim, not a verified one."),
 # 19 rule count flow
 ("a rule layer over registry 14.1.0 (33,183 leaves;",
  "a rule layer over registry 14.1.0 (33,183 executable leaves—a count that moved from 34,005 in release 13.1.0 through 33,230 (13.3.0), 33,170 (13.4.2) and 33,178 (14.0.0) as 1,307 rules were retired and 485 guideline-sourced rules were added, Supplementary Table S10;"),
 # 42 Table 5 caption
 ("**Table 5 | Component ablation of the frozen engine v7 (2,314 eICU stays).**",
  "**Table 5 | Component ablation of the frozen engine v7 (2,314 eICU stays; the 28 `unverified_source` rules are a subset of the 33,183 executable rules).**"),
 # 9 code availability
 ("Engine and evaluation scripts (AGPL-3.0-or-later) and the rule registries (CC BY-SA 4.0), together with freeze manifests and `reproduce.sh`, will be deposited on Zenodo with a DOI before publication; a GitHub mirror is available from the corresponding author.",
  "Engine and evaluation scripts (AGPL-3.0-or-later) and the rule registries (CC BY-SA 4.0) are public on GitHub (github.com/sobahramisamani-droid); the frozen v7/14.1.0 snapshot with freeze manifests, per-stay outputs and `reproduce.sh` will be archived on Zenodo with a DOI before publication. Hardware used for all timings: 2 vCPU Intel Xeon 2.60 GHz, 2 GB RAM, Linux 6.1, Python 3.13."),
 # 94 conclusion: non-inferiority + pre-specified
 ("reproduced population-screening performance across independent survey cycles and was indistinguishable from a frontier LLM on a blinded paired primary metric, while remaining auditable.",
  "reproduced population-screening performance across independent survey cycles under internally pre-specified (not publicly registered) criteria that were weakened from superiority to non-inferiority after a failed first quarantine round, and was indistinguishable from a frontier LLM on a blinded paired primary metric, while remaining auditable."),
 # 47 two-tier sentence (LLM paragraph) + 23 footnote
 ("mean reciprocal rank 0.391 vs 0.408 (difference −0.017, −0.043 to +0.008) (Fig. 6; Table 4).",
  "mean reciprocal rank 0.391 vs 0.408 (difference −0.017, −0.043 to +0.008) (Fig. 6; Table 4). Crediting either tier of the engine's output—a secondary, post-hoc metric with no LLM counterpart, since the LLM returns a single flat list that is simply reused—gave 69.8% vs 59.6%."),
 # 46 prevalence baseline subsection
 ("A prevalence-ranking baseline (most frequent groups whose key analyte is present) reached recall@5 51.3% and NDCG@5 39.0%; at k = 10 its recall (76.8%) exceeded the engine's 74.1%, so the engine's advantage lies in ranking, not list coverage (Supplementary Table S11).",
  "\n\n### Prevalence baseline\n\nA prevalence-ranking baseline (most frequent groups whose key analyte is present) reached recall@5 51.3% and NDCG@5 39.0%; at k = 10 its recall (76.8%) exceeded the engine's 74.1%, so the engine's advantage lies in ranking, not list coverage (Supplementary Table S11)."),
 # 20/24 CAP
 ("Both flagged 39/39 CAP critical values in 50 stays.",
  "Both flagged 39/39 CAP critical values in 50 stays (thresholds listed in Supplementary Note 2)."),
 # 22 healthy adult definition
 ("Among adults with all indices normal, the engine asserted a disease in",
  "Among guideline-healthy adults (all of: HbA1c < 5.7%, fasting glucose < 100 mg/dL, eGFR ≥ 90, ACR < 30 mg/g, haemoglobin ≥ 12/13 g/dL, MCV 80–100 fL, ferritin ≥ 30 µg/L where measured, total cholesterol < 200 and triglycerides < 150 mg/dL, urate ≤ 6/7 mg/dL and ALT ≤ 25/33 U/L for women/men, sodium 135–145 mmol/L; full list in Supplementary Note 1—not all 2,045 analytes), the engine asserted a disease in"),
 # 3 six-target criterion ALT
 ("NHANES AUROC within 0.03 of the prior release on six targets with ≤ 1% healthy false assertions;",
  "NHANES AUROC within 0.03 of the prior release on six targets—diabetes, CKD, anaemia, iron deficiency, hypercholesterolaemia, hyperuricaemia; ALT elevation was excluded a priori because its label was known to be definition-sensitive, and its non-inferiority is reported post hoc (0.877 vs 0.880, within 0.03)—with ≤ 1% healthy false assertions;"),
 # 35 qualify 33,183 in results system paragraph
 ("a rule layer evaluates 33,183 executable rules (registry 14.1.0) derived from 785 guideline sources;",
  "a rule layer evaluates 33,183 executable rules (registry 14.1.0; 272 curated anchors and 32,911 AI-drafted, unaudited candidates) derived from 785 guideline sources;"),
 # 15 sic for filename
 ("Hemoglyph (`analyse_gidlines.py`, v7) processes a panel", "Hemoglyph (`analyse_gidlines.py` [sic—historical file name], v7) processes a panel"),
]

SMP_EDITS = [
 ("# Hemoglyph: A Knowledge-Driven Hybrid Reasoning System for Interpreting Structured Laboratory Panels — Design, Pre-Registered Multi-Dataset Evaluation",
  "# Hemoglyph: A Knowledge-Driven Hybrid Reasoning System with an AI-Drafted, Guideline-Sourced Rule Base for Interpreting Structured Laboratory Panels — Design, Pre-Specified Multi-Dataset Evaluation"),
 ("Under a pre-registered analysis plan with cryptographic freezes", "Under an internally pre-specified analysis plan (time-stamped and hash-frozen, not publicly registered) with cryptographic freezes"),
 ("Keywords: clinical decision support system; laboratory medicine; Theory of Evidence; Yager combination rule; abstention; knowledge-based reasoning; pre-registration;",
  "Keywords: clinical decision support system; laboratory medicine; Theory of Evidence; Yager combination rule; abstention; knowledge-based reasoning; pre-specified analysis plan;"),
 ("All analyses follow a statistical analysis plan (SAP) that fixed metrics, label maps, thresholds and comparators; fifteen dated amendments record every subsequent change with justification (Supplementary Note 1).",
  "All analyses follow an internal statistical analysis plan (SAP) that fixed metrics, label maps, thresholds and comparators; fifteen dated amendments record every subsequent change with justification (Supplementary Note 1). The SAP was time-stamped and hash-frozen in the project repository but not deposited in a public registry, so we write 'pre-specified' rather than 'pre-registered'."),
 ("Quarantine datasets had never been run before the freeze and were run exactly once (Fig. 3a).",
  "Quarantine datasets had never been run before the freeze and were run exactly once (Fig. 3a); the only exception is the MIMIC-IV demo, re-run post hoc with the frozen v7 for comparability and labelled as such."),
 ("NHANES AUROC within 0.03 of the previous release for each of six laboratory-defined targets with ≤ 1% false assertions in healthy adults;",
  "NHANES AUROC within 0.03 of the previous release for each of six laboratory-defined targets (diabetes, CKD, anaemia, iron deficiency, hypercholesterolaemia, hyperuricaemia; ALT elevation was excluded a priori as definition-sensitive and its non-inferiority—0.877 vs 0.880—is reported post hoc) with ≤ 1% false assertions in healthy adults;"),
 ("model identity withheld at the platform's request and disclosed confidentially to the editor and reviewers), blinded to labels,",
  LLM_ID + "), blinded to labels,"),
 ("Model identity is withheld in the manuscript at the platform's request and is disclosed to the editor; the full protocol,", "The full protocol,"),
 ("with AUROC 0.600, 0.610 and 0.588 (95% CI 0.559–0.616) in sets A, B and B2, versus",
  "with AUROC 0.600 (95% CI 0.575–0.625) in development set A and 0.610 (0.583–0.640) in quarantine set B (both engine v6.1/registry 14.1.0) and 0.588 (0.559–0.616) in quarantine set B2 with the frozen v7, versus"),
 ("Crediting either tier of the engine's output (secondary, post hoc) gave 69.8% vs 59.6% (p < 0.0001).",
  "Crediting either tier of the engine's output (secondary, post hoc; the LLM has no second tier, so its flat list is reused) gave 69.8% vs 59.6% (p < 0.0001)."),
 ("Recall@5 was 65.4%", "Recall@5 was 62.3% (59.5–64.9; 1,392 stays) in men and 58.5% (54.4–62.3; 922 stays) in women, 58–64% across age bands and 59–61% across the three largest ethnicity strata (Supplementary Table S14)__R4CUT__"),
 ("7,743 records with TSH (655 hypothyroid, 195 hyperthyroid, 6,082 no-comment controls) |",
  "7,743 records with TSH, of which 6,932 scored (655 hypothyroid, 195 hyperthyroid, 6,082 no-comment controls) and 811 in other diagnostic classes |"),
 ("7,743 scorable; 811 other-class records not in either task,", "7,743 with TSH, of which 6,932 scored and 811 other-class records not in either task,"),
 ("laboratory-criterion adjudication", "automated laboratory-criterion matching (not clinician adjudication)"),
 ("Twenty-seven of the 29 groups", "Twenty-seven of the 29 groups (exceptions: malnutrition, n = 16, AUROC 0.515; hypocalcaemia, n = 10, 0.627)"),
 ("752/755 in 14.1", "752/755 in release 14.1; all failures are replicates of the same thiazide-hyponatraemia vignette, Supplementary Note 4"),
 ("will be deposited on Zenodo with a DOI before publication.", "are public on GitHub (github.com/sobahramisamani-droid); the frozen v7/14.1.0 snapshot will be archived on Zenodo with a DOI before publication. Timings: 2 vCPU Intel Xeon 2.60 GHz, 2 GB RAM, Linux 6.1, Python 3.13."),
 ("and perform on a par with a frontier LLM in a blinded paired test while remaining deterministic, abstention-aware and auditable.",
  "and perform on a par with a frontier LLM in a blinded paired test while remaining deterministic, abstention-aware and auditable—under internally pre-specified criteria that were weakened from superiority to non-inferiority after a failed first quarantine round."),
]

def apply(path, edits):
    t = path.read_text(encoding="utf-8")
    for old, new in edits:
        c = t.count(old)
        assert c == 1, f"{path.name}: count={c} for: {old[:90]!r}"
        t = t.replace(old, new)
    return t

tn = apply(NPJ, NPJ_EDITS)
ts = apply(SMP, SMP_EDITS)
# sample subgroup sentence: cut the rest of the old sentence after the marker
import re
m = re.search(r"__R4CUT__.*?ethnicity strata", ts, flags=re.S)
assert m, "R4CUT"
ts = ts[:m.start()] + ts[m.end():]
assert "__R4CUT__" not in ts
def glob(t):
    keep="a pre-registered crossover reader study"
    t=t.replace(keep,"@@KEEP@@")
    for a,b in [("pre-registered","pre-specified"),("Pre-registered","Pre-specified"),("Pre-Registered","Pre-Specified"),("pre-registration","pre-specification"),("Pre-registration","Pre-specification")]:
        t=t.replace(a,b)
    return t.replace("@@KEEP@@",keep)
tn=glob(tn); ts=glob(ts)
NPJ.write_text(tn, encoding="utf-8"); SMP.write_text(ts, encoding="utf-8")
print("OK r4 part A applied")
