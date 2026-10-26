#!/usr/bin/env python3
"""Assemble the open benchmark package **Hemoglyph-LabBench v1** (C1 of the 2026-10-23 plan).

Produces  eval/results/labbench/Hemoglyph-LabBench-v1.zip  +  MANIFEST.sha256  +  README copy.
Nothing is copied permanently inside the repo (workspace-size rule); the zip is rebuilt on demand and
is the artefact to upload to Zenodo next to the code release.

Contents (licence: repository LICENSE, not yet chosen; eICU-derived panels carry ODbL 1.0; raw third-party data NOT redistributed — fetch scripts are):
  T1  eICU-demo lab-only differential task   : label map (GROUPS regex), cohort filter, scorer, per-stay engine output
                                                for v5.1/v5.2 arms, participant flow. Raw eICU demo is fetched by the user
                                                from PhysioNet (ODbL; open access).
  T2  Blind LLM comparison (B3/B4/B8)        : 400 de-identified lab panels as shown to the LLM, pre-specified key,
                                                LLM answers (n=400 + 40 re-read), scorer, rank metrics.
  T3  Critical-value / fabrication safety    : 200 fabrication-provocation panels, healthy sweep, critical-value set (B7).
  T4  Single-label validations               : NHANES/UCI/ILPD definitions + fetch scripts + summary.json.
  T5  Case-vignette probe (B6)               : PMC-Patients 50 (Bhasuran 2025) pre-specified key, manual structured panels,
                                                both-arm results. The vignette CSV itself is re-derived from the authors' ESM.
  H   Human-validation instruments           : A1 rule-audit form (100 rules), B1 blind-read form (40 panels), scorer.
  Docs: SAP (all amendments), TRIPOD+AI checklist, Bond-2012 checklist, input schema, PROTOCOL.md, reproduce.sh.
"""
import hashlib, io, json, os, sys, time, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "eval", "results", "labbench")
VERSION = "v1"

FILES = {
    "T1_eicu_task": [
        "eval/realdata/eval_eicu.py", "eval/cohort_flow.py", "eval/error_audit.py", "eval/error_audit_lib.py",
        "eval/subgroup_fairness.py", "eval/calibration_dca.py", "eval/next_test_utility.py",
        "eval/results/run_20261023_v5/eicu_report_v5_1.md", "eval/results/run_20261023_v5/eicu_per_stay_v5_1.json",
        "eval/results/run_20261023_v5/eicu_report_v5_2_ctx.md", "eval/results/run_20261023_v5/eicu_per_stay_v5_2_ctx.json",
        "eval/results/run_20261023_v5/eicu_report_v5_2_tmp.md", "eval/results/run_20261023_v5/eicu_per_stay_v5_2_tmp.json.gz",
        "eval/results/eicu_demo/label_audit_n100.md", "eval/results/eicu_demo/label_audit_stays100.json",
        "eval/results/eicu_demo/calibration_dca_v5_1.md", "eval/results/eicu_demo/error_audit_v5_1.md",
        "docs/paper1/supplement/TABLE_S1_cohort_flow.md", "docs/paper1/figures/figS1_participant_flow.png",
    ],
    "T2_blind_llm_comparison": [
        "eval/baselines/llm_zero_shot.py", "eval/baselines/b8_score.py", "eval/baselines/labbench_score.py", "eval/baselines/b8_rank_metrics.py",
        "eval/baselines/engine_on_stays.py", "eval/baselines/ml_baseline_eicu.py",
        "eval/results/eicu_demo/b8_blind_panels_n240.json", "eval/results/eicu_demo/b8_key_n240.json",
        "eval/results/eicu_demo/b8_llm_blind_n240.json", "eval/results/eicu_demo/b8_rerun40_cases.json",
        "eval/results/eicu_demo/b8_llm_rerun40.json", "eval/results/eicu_demo/b8_score_n240.md",
        "eval/results/eicu_demo/b3b4b8_pooled_n400.json", "eval/results/eicu_demo/b3b4b8_pooled_n400.md",
        "eval/results/eicu_demo/rank_metrics_n400.md", "eval/results/eicu_demo/rank_metrics_n400.json",
        "eval/results/eicu_demo/llm_agent_b3_n100.json", "eval/results/eicu_demo/b4_llm_blind_n60.json",
        "eval/results/eicu_demo/b4_oos_stays_n60.json", "eval/results/eicu_demo/b3_stays_engine_v3_n100.json",
    ],
    "T3_safety": [
        "tests/fabrication_provocation.py", "tests/healthy_sweep.py", "tests/adversarial_battery.py",
        "tests/engine_battery.py", "tests/hard_battery.py", "tests/hard_battery2.py", "tests/hard_battery3.py",
        "eval/baselines/b7_critical_values.py", "eval/results/eicu_demo/b7_critical_values.md",
        "eval/results/eicu_demo/b7_hidden.json", "eval/results/eicu_demo/b7_llm_blind.json", "eval/results/eicu_demo/b7_panels.txt",
    ],
    "T4_single_label": [
        "eval/realdata/eval_nhanes.py", "eval/realdata/fetch_nhanes_cycle.py", "eval/baselines/b5_nhanes_blind.py",
        "eval/realdata/eval_uci_thyroid.py", "eval/realdata/eval_uci_hcv.py", "eval/realdata/eval_ilpd.py",
        "eval/realdata/eval_sepsis2019.py", "eval/realdata/sepsis2019/fetch_sepsis2019.sh",
        "eval/results/nhanes_2017/summary.json", "eval/results/ilpd/summary.json",
        "eval/results/uci_hcv/summary.json", "eval/results/uci_thyroid/summary.json",
    ],
    "T5_case_vignettes": [
        "eval/realdata/eval_pmc_cases.py", "eval/realdata/pmc_cases/scoring_key_prespecified.json",
        "eval/realdata/pmc_cases/panel_overrides.json", "eval/realdata/pmc_cases/bhasuran_prompt.txt",
        "eval/results/pmc_cases/report.md", "eval/results/pmc_cases/per_case_parser.json",
        "eval/results/pmc_cases/per_case_manual.json", "eval/results/pmc_cases/panels_manual.json", "eval/results/pmc_cases/per_case_manual_strict.json",
    ],
    "H_human_instruments": [
        "eval/human/make_forms.py", "eval/human/score_forms.py", "eval/human/A1_rule_audit_form.csv",
        "eval/human/A1_rule_audit_form.docx", "eval/human/A1_rule_audit_sample.json",
        "eval/human/B1_blind_panel_form.csv", "eval/human/B1_blind_panel_form.docx",
    ],
    "docs": [
        "eval/PROTOCOL.md", "reproduce.sh", "README_REPRODUCE.md", "CITATION.cff", ".zenodo.json",
        "docs/paper1/supplement/SAP_Hemoglyph_v1.md", "docs/paper1/supplement/TRIPOD_AI_checklist_Hemoglyph.md",
        "docs/paper1/supplement/INPUT_SCHEMA_v1.md",
        "docs/paper1/COMPARISON_TABLE_DRAFT_20261022.md",
        "docs/paper1/supplement/DISCLOSURE_AND_LIMITATIONS_v53.md", "eval/patches/registry_v13_2_0_exposure_gate.py",
        "eval/patches/test_registry_v13_2_0.py", "eval/patches/cand/test_registry_v13_2_0.md", "tests/test_registry_v13_2_exposure_gate.py",
        "eval/patches/registry_v13_3_0_quality.py", "eval/patches/test_registry_v13_3_0.py", "eval/patches/cand/test_registry_v13_3_0.md", "eval/registry_defect_scan.py",
        "eval/results/registry_defect_scan_13.1.0.md", "eval/results/registry_defect_scan_13.3.0.md", "tests/test_registry_v13_3_quality.py",
    ],
}

README = """# Hemoglyph-LabBench {v} — an open benchmark for laboratory-only differential diagnosis

Author: Sobhan Bahrami (sobahramisamani@gmail.com). Licence: code and documents/keys as stated in the repository LICENSE file (**to be chosen and committed by the author before release — none exists yet**); eICU-derived panels inherit the eICU-CRD demo ODbL 1.0 terms (attribution, share-alike).
Built {date} from the Hemoglyph repository at commit/freeze listed in MANIFEST.sha256.

## Why
Language models cannot reliably classify laboratory values as high or low even when reference ranges are
supplied (Hager et al., Nat Med 2024, Ext. Fig. 4), and most diagnostic benchmarks hand the model the whole
narrative. LabBench isolates the question *what can be inferred from the numbers alone* (labs + age + sex),
with pre-specified keys, blinded comparison material and safety batteries, so that any engine, LLM or
clinician can be scored the same way.

## Tasks
| id | task | n | input | primary metric | key |
|---|---|---:|---|---|---|
| T1 | eICU-CRD demo lab-only differential | 2,314 ICU stays, 186 hospitals | labs (+ optional context / trajectory arms) | recall@5 of clinician problem-list groups (62-group regex map) | `eval_eicu.py: GROUPS` |
| T2 | blinded LLM-vs-engine comparison | 400 panels (596 labels) | labs + age/sex, de-identified text | recall@5, MRR, rank bins, test–retest | `b8_key_n240.json` |
| T3 | safety | 200 fabrication panels, 200 healthy panels, critical values | labs | unsupported-assertion rate; false-alarm rate | scripts |
| T4 | single-label validations | NHANES 7 cycles, UCI HCV 615, UCI thyroid 3,162, ILPD 583 | labs | AUROC | scripts |
| T5 | PMC-Patients case vignettes (Bhasuran 2025) | 50 | lab paragraph only (parser arm / manual arm) | top-1/5/10 specific & syndrome | `scoring_key_prespecified.json` |
| H  | human validation instruments | 100 rules; 40 panels | — | error rate; 3-arm recall@5 | forms + `score_forms.py` |

## Data access (not redistributed here)
* eICU-CRD demo 2.0.1 — PhysioNet, open access (ODbL): https://physionet.org/content/eicu-crd-demo/2.0.1/
* NHANES — CDC public files (fetch_nhanes_cycle.py)
* UCI HCV / thyroid, ILPD — UCI ML repository (fetch inside the eval scripts)
* PMC-Patients 50 vignettes — ESM of Bhasuran et al. 2025 (`sd_1.xlsx`) and https://github.com/balubhasuran/DDx_CaseReports
* PhysioNet/CinC 2019 sepsis — https://physionet.org/content/challenge-2019/1.0.0/

## How to score your own system on T2 (the easiest entry point)
1. Read `T2_blind_llm_comparison/b8_blind_panels_n240.json` (field `panel_text`; also `b4_oos_stays_n60.json`, `b3_stays_engine_v3_n100.json`).
2. Produce ≤10 ranked diagnoses per panel, save as `{{stay_id: [dx, ...]}}`.
3. `python labbench_score.py --answers your.json --key b8_key_n240.json` → recall@1/3/5/10, MRR, "not listed" rate; the synonym
   map (`SYN` in llm_zero_shot.py) is the one used for all published arms. Report the scoring-map version with your result.

## Pre-registration and reporting
SAP with all amendments (`docs/SAP_Hemoglyph_v1.md`), TRIPOD+AI checklist, Bond-2012 DDx-generator checklist, cohort flow.
Nothing in the keys was changed after seeing results; where a map was found imperfect (label audit, 2 misses /
150 positives) the change is deferred to the next protocol version and documented.

## Known limitations of the benchmark itself
Reference standard of T1 is the routine clinician problem list (not adjudicated); T2 LLM arm is a single
GPT-4-class model run by the author (exploratory); T5 keys were written by the author; the human-validation
forms (H) are instruments, their results are added when returned.
"""


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    zpath = os.path.join(OUT, f"Hemoglyph-LabBench-{VERSION}.zip")
    manifest, missing = [], []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, items in FILES.items():
            for rel in items:
                src = os.path.join(ROOT, rel)
                if not os.path.exists(src): missing.append(rel); continue
                arc = f"{folder}/{os.path.basename(rel)}"
                if os.path.basename(rel) == "summary.json": arc = f"{folder}/{os.path.basename(os.path.dirname(rel))}_summary.json"
                z.write(src, arc); manifest.append((sha(src), os.path.getsize(src), arc, rel))
        readme = README.format(v=VERSION, date=time.strftime("%Y-%m-%d"))
        z.writestr("README.md", readme)
        z.writestr("MANIFEST.sha256", "\n".join(f"{h}  {n:>9}  {a}    <- {r}" for h, n, a, r in manifest) + "\n")
    open(os.path.join(OUT, "README.md"), "w").write(readme)
    open(os.path.join(OUT, "MANIFEST.sha256"), "w").write("\n".join(f"{h}  {a}" for h, _, a, _ in manifest) + "\n")
    print(f"{zpath}: {len(manifest)} files, {os.path.getsize(zpath)/1e6:.1f} MB; missing {len(missing)}: {missing}")


if __name__ == "__main__":
    main()
