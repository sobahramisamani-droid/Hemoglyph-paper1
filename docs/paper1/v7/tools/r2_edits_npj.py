import re
p='Paper1_Hemoglyph_npj_EN_v7_R1.md'; s=open(p).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt, (s.count(old), old[:80]); s=s.replace(old,new)
# abstract
rep("reproduced across cycles with ≤1 false assertion per healthy cohort.",
    "reproduced across cycles with 2 false assertions among 485 healthy adults. Label-group precision@5 against the ICU problem list was 14.2% (NDCG@5 56.5% vs 39.0% for a prevalence-ranking baseline). On 50 published case reports the end-to-end text parser placed the diagnosis in the top-5 in 10% of cases, versus 26% from manually structured values.")
rep("runs on CPU in ~1 s per panel and makes no network calls.",
    "runs on a single CPU core without GPU in ~1 s per panel (median 0.4–0.5 s, p95 0.9 s in a 2-GB sandbox) and makes no network calls. The desktop product around it is proprietary and node-locked; its optional cloud OCR path transmits report images and is outside the offline claim, which applies to the engine evaluated here.")
# registry counts
rep("it has not been audited rule-by-rule by clinicians, and the per-rule error rate is therefore unknown.",
    "it has not been audited rule-by-rule by clinicians, and the per-rule error rate is therefore unknown. Of 34,673 records, 1,487 are retired and 3 lack an executable expression; the 33,183 executable rules comprise 272 curated anchors, 13 demoted former anchors and 32,898 candidates (Supplementary Table S10 reconciles all counts against the live file; 388 of the 785 listed sources are cited by an executable rule). Each output entry displays its rule's status and evidence tier, and both are machine-readable fields in the registry.")
# quarantine timing + margins
rep("re-specified the criteria as non-inferiority with dated justification,",
    "re-specified the criteria as non-inferiority with dated justification (Amendment 15, written after Round 1 was known and before any Round-2 file was opened: NHANES AUROC within 0.03 of the prior release on six targets with ≤ 1% healthy false assertions; sepsis AUROC not more than 0.02 below; no new safety-battery failure),")
# eICU: precision paragraph
rep("Counting either tier, top-5 recall was 71.9%.",
    "Counting either tier, top-5 recall was 71.9%. The engine asserted a mean of 4.5 label groups per stay in its top-5; precision@5 was 14.2% (13.3–15.2), F1@5 23.1% and NDCG@5 56.5% (54.1–58.8) against an incomplete problem list (lower bounds). A prevalence-ranking baseline (most frequent groups whose key analyte is present) reached recall@5 51.3% and NDCG@5 39.0%; at k = 10 its recall (76.8%) exceeded the engine's 74.1%, so the engine's advantage lies in ranking, not list coverage (Supplementary Table S11).")
# healthy total
rep("the engine asserted a disease in 1/160, 1/246 and 0/79 (and in 0/1,000 synthetic healthy panels).",
    "the engine asserted a disease in 1/160, 1/246 and 0/79 (2/485, 0.4%; and in 0/1,000 synthetic healthy panels).")
# external cohorts n
rep("On the UCI thyroid referral set (3,162 records) AUROC was 0.979 for hypothyroidism (sensitivity 0.969, specificity 0.951) and 0.798 for hyperthyroidism; on the HCV cohort (n = 615) 0.925 (0.881–0.962) for any liver disease and 0.909 for cirrhosis; on ILPD (n = 583) 0.704",
    "On the UCI thyroid referral set (7,743 records with TSH; 655 hypothyroid, 195 hyperthyroid, 6,082 controls) AUROC was 0.979 (0.974–0.983) for hypothyroidism (sensitivity 0.969, specificity 0.951) and 0.798 (0.783–0.814) for hyperthyroidism; on the HCV cohort (n = 615; 75 with liver disease, 30 cirrhosis) 0.925 (0.881–0.962) for any liver disease and 0.909 (0.837–0.969) for cirrhosis; on ILPD (n = 583; 416 patients) 0.704")
rep("| UCI thyroid0387 | referral laboratory | expert comment | external | 3,162 records |",
    "| UCI thyroid0387 | referral laboratory | expert comment | external | 7,743 records (655 / 195 / 6,082) |")
rep("| UCI thyroid: hypothyroidism / hyperthyroidism | AUROC | 0.979 / 0.798 |",
    "| UCI thyroid: hypothyroidism (655 vs 6,082) / hyperthyroidism (195 vs 6,082) | AUROC | 0.979 (0.974–0.983) / 0.798 (0.783–0.814) |")
rep("| UCI HCV: any liver disease / cirrhosis | AUROC | 0.925 (0.881–0.962) / 0.909 |",
    "| UCI HCV: any liver disease (75 vs 533) / cirrhosis (30 vs 578) | AUROC | 0.925 (0.881–0.962) / 0.909 (0.837–0.969) |")
rep("| ILPD | AUROC | 0.704 (0.661–0.747) |","| ILPD: liver patient (416 vs 167) | AUROC | 0.704 (0.661–0.747) |")
rep("| NHANES H/I/J healthy adults | false assertions | 1/246, 0/79, 1/160 |","| NHANES H/I/J healthy adults | false assertions | 1/246, 0/79, 1/160 (2/485) |")
# calibration
rep("Cross-fitted isotonic recalibration reduced ECE to 0.003 (Brier 0.040)",
    "Split-half cross-fitted isotonic recalibration (fitted on odd-indexed stays, applied to even-indexed and vice versa) reduced ECE to 0.003 (Brier 0.040) within eICU—evidence that the ranks are recalibrable, not a transferable calibration")
# robustness: gate criterion
rep("The release passed 689/689 unit tests, 352/353 adversarial vignettes (the one failure, alcoholic pancreatitis, was deliberately not patched with a case-specific rule), 753/755 perturbation pairs and the SI/conventional unit-twin battery.",
    "The release passed the non-regression gate (no vignette, perturbation pair or healthy panel that passed in the prior release may fail): 689/689 unit tests, 352/353 adversarial vignettes (the one failure, alcoholic pancreatitis ranked second behind alcohol-use disorder, was deliberately not patched with a case-specific rule), 753/755 perturbation pairs (752/755 in 14.1; the brittle case is thiazide-associated hyponatraemia under 3% noise) and the SI/conventional unit-twin battery.")
# discussion ~900
rep("the ~900 curated syndrome constellations, not in the 33,000-rule registry",
    "the ~900 curated syndrome constellations (written by the first author from guideline criteria and, like the registry, not independently validated), not in the 33,000-rule registry")
# COI
rep("S.B. is the sole developer of Hemoglyph, whose desktop application is distributed under a proprietary licence; the engine and registries are open.",
    "S.B. designed and wrote the Hemoglyph software, owns the proprietary desktop application and would benefit from its commercial distribution; this is a financial interest in a favourable evaluation, which the pre-registered one-shot design and released evaluation scripts are intended to constrain. The engine source, registries and evaluation code are open.")
# ref 15
m=re.search(r"15\. Massachusetts General Brigham Laboratory of Computer Science\. DXplain[^\n]*",s); assert m
s=s.replace(m.group(0),"15. Feldman MJ, Hoffer EP, Conley JJ, et al. Dedicated AI expert system vs generative AI with large language model for clinical diagnoses. *JAMA Netw Open* 8, e2512994 (2025).")
# supplementary list
rep("Note 2 LLM comparison protocol;","Note 2 LLM comparison protocol; Note 3 formal fusion/Theory-of-Evidence algorithm, weight profiles and the 27 consistency identities; Fig. S2 historical LLM comparison vs engine v5.1; Table S10 registry count reconciliation; Table S11 precision/F1/NDCG, alert burden, per-group PPV and prevalence baseline; Table S12 fusion-weight sensitivity;")
open(p,'w').write(s); print('npj ok')
