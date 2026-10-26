# OSF Registration — ready-to-paste text (template: "OSF Preregistration")

Upload by the corresponding author (free account at https://osf.io → "Create new project" → "Registrations" → "New registration" → template *OSF Preregistration*). Nothing below needs an institution or payment. Attach `SAP_Hemoglyph_v1.md` (with Amendments 1–8) and the `FREEZE_v5.2_*_sha256.txt` file as registration files, so the engine state is hash-locked at registration time.

**Status honesty note (must stay in the registration):** this is a *retrospective, post-hoc* registration of an analysis plan whose SAP was written and time-stamped in the public git history before each dataset was first run (see dates in SAP §0 and script docstrings), but *after* several datasets had already been evaluated and the engine amended (SAP Amendments 1–8 list every engine change and the data that motivated it). The registration therefore fixes (i) the frozen engine version (sha256 list) and (ii) the analyses that have **not yet** been run at registration time — these are the confirmatory part. Everything run before registration is labelled exploratory/developmental in the paper.

---

## Title
Hemoglyph: a knowledge-based, untrained laboratory-interpretation engine — frozen-version confirmatory evaluation on public cohorts

## Authors
Sobhan Bahrami (corresponding; sole developer of Hemoglyph). Co-authors to be added by the author.

## Description
Hemoglyph is a deterministic, rule- and syndrome-based clinical decision support engine that ranks a differential diagnosis from a routine laboratory panel plus age/sex (optionally clinical context and lab trajectories). It contains no trained parameters; its knowledge base (≈6,750 disease entities, ≈34,000 rules, ≈450 lab-syndrome patterns, 747 cited sources) was built with AI-assisted curation and is published in full. This registration fixes the engine version (v5.2, sha256 list attached) and pre-specifies the remaining confirmatory analyses on public datasets.

## Hypotheses (confirmatory, frozen engine v5.2)
H1. On the eICU-CRD demo cohort (n = 2,314 adult ICU stays, first-24-h labs, 2,432 coded diagnoses in 30 pre-defined groups) recall@5 of the frozen engine is ≥ 60% (95% CI excludes 55%). Already observed on v5.1: 63.7% (61.8–65.6) — H1 is a *non-regression* hypothesis for v5.2 in the labs-only arm.
H2. Adding structured clinical context (past-history + home medications, ext11 "context arm") improves recall@5 by ≥ 2 percentage points versus labs-only on the same stays (paired, McNemar p < 0.05), **without** increasing the fabrication-provocation failure count above 0/200 or the healthy-sweep false-positive count above 0/1000.
H3. Adding within-24-h lab trajectories (ext11 "temporal arm") does not reduce recall@5 (non-inferiority margin 1 pp) and increases recall@5 for AKI and acute MI by ≥ 3 pp each.
H4. On NHANES cycles 2005–2012 (four cycles never seen by any engine version; adults, non-pregnant) AUROC for laboratory-defined diabetes (HbA1c ≥ 6.5% or FPG ≥ 126 or self-report), CKD (eGFR < 60 or ACR ≥ 30), anaemia (WHO) and hypercholesterolaemia (TC ≥ 240) are each ≥ 0.90, and self-reported CKD AUROC ≥ 0.75 — i.e. no decline of more than 0.02 versus the 2013–2018 cycles already evaluated.
H5. On the PhysioNet/CinC 2019 hospital-A subsample (every 4th record, n ≈ 5,000), the sepsis-group probability from first-24-h labs predicts Sepsis-3 onset at any hour with AUROC ≥ 0.65, and is not worse than a 5-fold cross-validated logistic regression on the same features by more than 0.05 AUROC (this is a prediction task outside the engine's design; we expect the supervised model to win and report the gap).
H6. Blind GPT-4-class LLM comparison (B8, 240 new stays, pooled with B3/B4 → n = 400 stays / 596 labels): engine recall@5 exceeds the LLM's by ≥ 3 pp (McNemar). *Already run on 2026-10-23 before this registration* (engine 64.4% vs LLM 59.6%, p = 0.009) — reported as exploratory; it is listed here only so that the protocol is fixed if an independent LLM baseline is later added.

## Design
Retrospective, held-out, multi-cohort evaluation of a fixed software artefact. No training, tuning or threshold selection on any evaluation dataset after the freeze. One pass of the frozen engine per record; all outputs saved (per-stay JSON) and published.

## Sampling plan
Existing public data only: eICU-CRD demo v2.0.1, NHANES 2005–2018 (CDC), PhysioNet/CinC Challenge 2019 training set A (ODC-By), UCI HCV (#571), ILPD (#225), UCI thyroid, MIMIC-IV demo v2.2. Eligibility per SAP §6. No new data collection. Sample sizes are fixed by the datasets; groups with < 20 events are labelled exploratory.

## Variables
Inputs: laboratory analyte values with units (map tables in `eval/realdata/*.py`), age, sex; context arm adds eICU `pastHistory` and `medication` (start offset ≤ 0); temporal arm adds all first-24-h values as series. Outcomes: coded diagnoses (eICU `diagnosis` table mapped to 30 groups by the regex table in `eval_eicu.py`, frozen since SAP Amendment 7), laboratory- or questionnaire-defined conditions (NHANES), Sepsis-3 label (CinC 2019), dataset class labels (UCI/ILPD).

## Analysis plan
Primary metric: recall@5 (label-level, key analyte measured) with Wilson 95% CI; secondary: recall@3/10, AUROC of group probability (bootstrap 2,000), cross-fitted isotonic calibration (ECE, Brier, reliability), decision curves for the five largest groups, subgroup fairness (sex, age band, hospital, panel size), error taxonomy on 200 random misses, safety batteries (fabrication provocation 200 cases, healthy sweep 1,000, perturbation and unit-twin fuzz). Paired comparisons by exact McNemar on discordant label pairs. All code in `eval/`; one-command reproduction in `README_REPRODUCE.md`.

## Exclusions / missing data
No imputation; a label is scored only if its key analyte was measured. Pregnant participants excluded in NHANES. Patients with < 3 lab analytes excluded in CinC 2019 (count reported).

## What is already known (exploratory, before registration)
All results in `eval/results/` dated ≤ 2026-10-23, including engine versions v1–v5.1 and the B3/B4/B8 LLM comparisons. Engine changes after each dataset are listed in SAP Amendments 1–8 and `FREEZE_*` files.
