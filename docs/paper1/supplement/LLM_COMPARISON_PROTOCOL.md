# Supplementary Note — Protocol of the blinded LLM comparison (B3 / B4 / B8) and reviewer additions

## 1. Design
Paired, blinded comparison of Hemoglyph with a general-purpose large language model on identical inputs: the first laboratory panel (≥ 8 analytes) of adult eICU-CRD demo stays, with age and sex. No clinical text, history, vitals or admission diagnosis was shown to either system.

| item | value |
|---|---|
| stays | 400 (B3 n = 100, seed 20261021; B4 n = 60 out-of-sample, seed 20261022; B8 n = 240 disjoint, seed 20261023) |
| scorable labels | 596 (clinician diagnosis strings → 31 groups via the frozen regex map `eval_eicu.GROUPS`; label counted only when the group's key analyte was in the panel) |
| LLM | GPT-4-class general-purpose model accessed through the Arena.ai Agent Mode interface; model identity withheld in the manuscript at the platform's request and **disclosed to the editor on request** |
| dates | B3 2026-10-21; B4 2026-10-22; B8 2026-10-23; test–retest 2026-10-24; prompt-sensitivity arm 2026-10-25 |
| decoding | interface default; temperature not user-controllable (hence the test–retest arm) |
| prompt P1 | "You are a clinical laboratory medicine expert. Given the following laboratory panel of an adult ICU patient (first 24 h of admission), list the most likely diagnoses or clinically important laboratory syndromes this panel supports. Return ONLY JSON of the form {"diagnoses":[{"name":"...","probability":0.0-1.0}]} with at most 10 entries, ordered by probability. Do not include explanations. Patient: {age}-year-old {sex}. Panel: {analyte value unit …}" |
| prompt P2 (sensitivity arm, 40 panels) | "You are an ICU attending physician writing the admission problem list. From the first-24-hour laboratory panel of this adult ICU patient (age, sex and values only), list up to 10 diagnoses or clinically important laboratory syndromes you would record, ranked from most to least likely, using standard ICU diagnosis names. Output JSON {diagnoses:[{name, probability}]}, no explanations." |
| batching | panels presented in batches of 40 (B8) / 20 (B3, B4), each identified only by a case number |
| blinding | the panel file (`b8_blind_panels_n240.json`) contains no labels and no engine output; the key file (`b8_key_n240.json`) was generated separately and opened only by the scoring script after all read-outs were stored |
| scoring | free-text names mapped to the 31 groups by a fixed synonym regex map (`llm_zero_shot.SYN`), written before B3 and unchanged since; same recall@k definition as the engine |
| engine arm | original analysis: engine v5.1 ranks (historical); **re-scored for the revision with the frozen engine v7 / registry 14.1.0** (`llm_vs_v7_cluster_n400.md`) |
| statistics | original: label-level Wilson CI and exact McNemar. Revision: stay-cluster bootstrap (4,000 resamples) and Durkalski cluster-adjusted McNemar; ICC and design effect reported |
| reproducibility | LLM: 40 B8 panels re-read blind one day later (P1 read 2) and with prompt P2; engine: deterministic (byte-identical outputs across runs and freezes) |
| outputs released | `llm_agent_b3_n100.json`, `b4_llm_blind_n60.json`, `b8_llm_blind_n240.json`, `b8_llm_rerun40.json`, `b8_llm_prompt2_n40.json`, keys, panels, scoring scripts |

## 2. Results after re-scoring with engine v7 (n = 400, 596 labels; stay-clustered inference)

| metric | Hemoglyph v7 (flat) | LLM (P1) | difference | Durkalski p |
|---|---|---|---|---|
| recall@1 | 24.0% (20.6–27.7) | 28.2% (24.6–32.0) | −4.2 pp (−7.5 to −0.9) | 0.013 |
| recall@3 | 47.0% (42.6–51.5) | 50.8% (46.5–55.1) | −3.9 pp (−7.4 to −0.3) | 0.041 |
| **recall@5 (primary)** | **60.7% (56.5–65.0)** | **59.6% (55.3–63.6)** | **+1.2 pp (−2.5 to +5.1)** | **0.54** |
| recall@10 | 72.0% (67.9–75.8) | 65.1% (60.8–69.3) | +6.9 pp (+3.3 to +10.5) | 0.0002 |
| MRR | 0.391 | 0.408 | −0.017 (−0.043 to +0.008) | — |
| absent from list | 21.8% | 34.9% | | |
| two-tier recall@5 (secondary, post hoc) | 69.8% (65.7–73.7) | 59.6% | +10.2 pp (+6.7 to +13.9) | < 0.0001 |

ICC of the paired recall@5 difference = 0.04 (design effect 1.04); clustering therefore changes the inference little, but the **engine version does**: with the historical v5.1 engine the primary comparison favoured Hemoglyph (64.4 vs 59.6%, p = 0.009); with the frozen v7 engine — which trades flat recall for guideline-correct semantics (CKD, troponin) — the primary comparison is **equivalent** (p = 0.54). The LLM is better at ranks 1–3; the engine lists more diagnoses overall (recall@10, absent rate) and is better when umbrella syndromes are credited. The manuscript reports the v7 result as primary and the v5.1 result as historical.

## 3. Prompt sensitivity and test–retest (40 panels, 91 labels)

| arm | r@1 | r@3 | r@5 | r@10 | absent |
|---|---|---|---|---|---|
| LLM P1 read 1 | 26.4 | 51.6 | 61.5 | 69.2 | 30.8 |
| LLM P1 read 2 | 28.6 | 54.9 | 67.0 | 71.4 | 28.6 |
| LLM P2 | 25.3 | 48.4 | 61.5 | 74.7 | 25.3 |
| engine v7 (flat / two-tier) | 19.8 / 29.7 | 45.1 / 65.9 | 64.8 / 72.5 | 73.6 / 83.5 | 16.5 |

Label-level recall@5 agreement between LLM reads: 83.5–89.0% (κ 0.69 for P1 read 1 vs read 2). Prompt-induced variation (±5 pp at k = 5) is of the same size as run-to-run variation, and both are larger than the v7–LLM difference on the primary metric.

## 4. Training-data contamination
The eICU-CRD demo is public (PhysioNet) and may be present in the LLM's pre-training corpus. The LLM received only the numerical panel, age and sex, never a stay identifier; recovering admission-level diagnosis strings from ~30 numerical values by memorisation is implausible, but cannot be excluded, and would bias the comparison **in favour of the LLM**. Hemoglyph has no training phase and cannot be contaminated.

## 5. Limitations of this arm
One model class, two prompts, one run per prompt (plus one re-read), no retrieval augmentation or chain-of-thought prompting, scoring by regex rather than clinician adjudication, admission-level labels. The arm is an author-run self-baseline, not a vendor benchmark.
