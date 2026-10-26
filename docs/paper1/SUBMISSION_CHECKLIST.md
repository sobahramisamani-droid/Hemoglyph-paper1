# Paper 1 (npj Digital Medicine) — submission checklist
Updated 2026-10-24. Owner: S.B. (user) unless marked AGENT. Status: ☐ open · ☑ done · ◐ in progress · ⏸ parked (needs user).

## A. Evaluation chain (v5.3, registry 13.3.0)
- ☑ Gate v5.3 (pytest 689, engine 50/50, hard 151/151, hard2 124/124, hard3 77/78, adversarial 86/86, healthy 0/200, fabrication 200/200)
- ☑ eICU-CRD demo labs-only / +ctx / +ctx+tmp; error audit; subgroup; next-test; calibration/DCA; registry-off ablation
- ☑ UCI thyroid, UCI HCV, ILPD, PMC cases
- ☑ NHANES 2017–18 (cycle J) full re-run under 13.3.0 (n = 5,103; diabetes 0.941, CKD 0.959, anaemia 0.971, iron def. 0.989)
- ☑ **User decision 2026-10-24: option 2** — cycles I–D NOT re-run under 13.3.0; they keep v5-era (13.1.0) values and are marked † in Table S1/S4/Disclosure
- ☑ Sepsis-2019 (n = 4,843; AUROC 0.593 vs logistic 0.689 — now reported in Results + Table 1/S1), healthy 0/1000, perturbation 755/755, unit-twin 149/149 — **V53_ALLDONE 2026-10-24**
- ☑ extract_numbers (pinned to 13.3.0 copy; feature registry 12.1.0 fixed) → render EN/FA (no † left) → figures → `FREEZE_v5.3_addendum_20261024_*`

- ☑ 2026-10-24 Amendment 13: Sepsis-2019 concurrent re-analysis (post-hoc) → 0.534, did not rescue; S12 + Results/Limitations updated; no engine change
- ⏸ `MANUAL_DOI_VERIFICATION_worksheet_13.4.1.xlsx` (50 rows; A = 9 removed DOIs) — USER / reviewer fills by hand → 13.4.3

## B. Registry
- ☑ 13.3.0 frozen (paper); ☑ 13.4.0 release candidate built, gated, delivered in `release/registry_13.4.0/` (CHANGELOG, GATE, SHA256SUMS)
- ☑ 13.4.1 built (provenance-only; 9 fabricated DOIs removed; 28 rules flagged) in `release/registry_13.4.1/` — gate 13.4.0 carried over (rule logic identical)
- ☑ **13.4.1 applied live 2026-10-24**, then **13.4.2** (regression fix: eICU 13.4.1 recall@5 61.7 vs 63.8 → 9 D19 finding rules demoted; hard 151/151 restored; full gate green: pytest 689/689, hard 151/151, hard2 124/124, hard3 77/78; eICU 13.4.2 = 49.3/63.7/76.9, AUROC .767 — Disclosure A6 updated) (backups `*.bak_v13_3_0`; probe OK; gate: pytest 689/689, hard 151/151, hard3 77/78; README/QML counts → 33,170 / 781) — **USER APPROVED 2026-10-24** — AGENT
- ☑ Disclosure A5 (provenance audit + 13.4.1) written; ☐ paragraph on 13.3.0 → 13.4.0 rule diff (D21 171 artefact rules retired; 111 anchored rules; 48 duplicates; 84 catalogued-only) — AGENT
- ☐ Disclosure: one sentence explaining engine log count (34,557 = 34,548 file − 9 quarantined + 18 code-level supplemental) vs 33,230 executable — AGENT
- ☐ Fix feature-registry version wording in papers (12.1.0, not "5.7.1") — AGENT

## B2. Decisions recorded 2026-10-24 (user)
- ☑ (a) apply registry 13.4.0 to live files after ALLDONE: YES
- ☑ (b) one eICU labs-only run with 13.4.1 (=13.4.0 logic), reported in Disclosure/Supplement only: DONE 2026-10-24 for 13.4.1 (61.7 % — regression) and 13.4.2 (63.7 %); table in Disclosure A6
- ☑ (c) LLM comparison stays in main text, middle-ground wording (explicit exploratory / blinded-identity / author-run labels; no superiority claim in title/abstract) — applied to text_en/text_fa abstracts
- ☑ Licence: code GNU AGPL-3.0-or-later (`LICENSE`, `NOTICE`, dual-licensing reserved); registries + aggregated outputs **CC BY-SA 4.0** (`LICENSE-DATA.md`; changed from CC BY on user request — copyleft for the knowledge base); desktop build proprietary. README/README_FA/CITATION.cff/.zenodo.json/Code availability (EN+FA) updated

## C. Source attribution (decided 2026-10-24 — three-layer method)
- ☐ **Layer 1 – main text references (≤ ~50):** only sources actually read; plus the 10–15 most-cited registry guidelines (KDIGO, ADA, WHO anaemia, EASL, ATA, ISTH, Tietz…). Methods sentence: "Full provenance of all knowledge sources is provided in Supplementary Data 1 and in the released registry." — AGENT drafts, USER approves
- ☑ **Layer 2 – Supplementary Data 1 (XLSX):** DONE 2026-10-24 → `docs/paper1/supplement/Supplementary_Data_1_sources_13.4.1.xlsx` (781 rows; 112 DOI-verified, 9 fabricated DOIs found → 13.4.1); Methods + Limitations + Disclosure A5 updated — `source_id, organization, title, year, DOI/URL, n_rules_citing, n_executable_rules, verification_status` for all 781 sources (13.4.0) / 747 (13.3.0) — AGENT
- ☐ **Layer 3 – registry itself (Zenodo DOI):** rule-level `source_ids`; Data Availability sentence pointing to it — AGENT text, USER deposits
- ☐ **Automated source verification script** (`eval/registry_source_verify.py`): resolve DOI/URL, compare returned title, write `verification_status ∈ {verified, title_mismatch, unresolved}`; unresolved/mismatched sources are corrected or left labelled "unverified" — never labelled verified without a check — AGENT (after chain)
- ☐ Never list all sources in the main reference list; never imply the authors read every source — standing rule

## D. Manuscript
- ☑ EN main (≈2,840 words, Methods ≈1,738, abstract 145), Supplement S1–S10, figures 1–6 + S1–S2, cover letter; ☑ FA version
- ☑ Authors: Sobhan Bahrami¹*, Zhaleh Tahmasebinejad², Ehsan Bahrami Samani² (contribution statements inserted)
- ⏸ Z.T. and E.B.S. confirm authorship, contribution statements, and affiliations in writing — USER
- ⏸ Verify reference 15 — USER (or AGENT with DOI check)
- ☐ Final read-through of EN/FA after numbers refresh — AGENT then USER
- ☐ Re-check npj limits after refresh: main text ≤ 4,000 words (excl. abstract/Methods/refs/legends), ≤ 10 display items, abstract ≤ 150 words unreferenced

## E. Compliance / open science
- ⏸ A1/B1 expert fidelity-review forms (now lighter: "does rule match cited recommendation?") — USER to recruit reviewers; AGENT prepared forms
- ⏸ OSF registration (text ready: `supplement/OSF_REGISTRATION_TEXT.md`) — USER
- ⏸ Zenodo deposit of code + registries 13.3.0 and 13.4.0 + FREEZE manifests (`.zenodo.json` ready) — USER
- ☑ LICENSE files written (AGPL-3.0 code / CC BY-SA 4.0 data / NOTICE open-core boundary)
- ☑ TRIPOD-AI checklist; ☑ Disclosure & Limitations v5.3; ☑ SAP v1 + amendments
- ☐ Data-availability statement lists: eICU demo (PhysioNet open), NHANES (CDC), UCI, ILPD, PMC cases, Sepsis-2019 (PhysioNet open) with URLs — AGENT

## F. Submission
- ⏸ Create npj Digital Medicine account, ORCID for all authors — USER
- ⏸ Upload: main docx, supplement docx, figures, Supplementary Data 1, cover letter, TRIPOD-AI — USER
- ⏸ Suggested reviewers / excluded reviewers — USER
