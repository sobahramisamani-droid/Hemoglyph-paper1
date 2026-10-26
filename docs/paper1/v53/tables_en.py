# -*- coding: utf-8 -*-
"""Display items (main tables + supplementary tables) for Paper 1 v5.3, built from numbers_v53.json."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
N = json.load(open(os.path.join(HERE, "numbers_v53.json"), encoding="utf-8"))

GROUP_LABEL = {"renal_impairment": "renal impairment (AKI or CKD)", "sepsis": "sepsis", "diabetes": "diabetes mellitus", "acute_kidney_injury": "acute kidney injury",
               "chronic_kidney_disease": "chronic kidney disease", "anemia": "anaemia", "gi_bleeding": "gastrointestinal bleeding", "diabetic_ketoacidosis": "diabetic ketoacidosis",
               "hyperglycemia": "hyperglycaemia", "acute_myocardial_infarction": "acute myocardial infarction", "hypokalemia": "hypokalaemia", "heart_failure": "heart failure",
               "leukocytosis": "leucocytosis", "hyponatremia": "hyponatraemia", "metabolic_acidosis": "metabolic acidosis", "hyperkalemia": "hyperkalaemia",
               "thrombocytopenia": "thrombocytopenia", "hypomagnesemia": "hypomagnesaemia", "alcohol_withdrawal": "alcohol withdrawal", "coagulopathy": "coagulopathy",
               "cirrhosis_liver_failure": "cirrhosis / liver failure", "hypoglycemia": "hypoglycaemia", "lactic_acidosis": "lactic acidosis", "acute_pancreatitis": "acute pancreatitis",
               "malnutrition": "malnutrition", "hypernatremia": "hypernatraemia", "rhabdomyolysis": "rhabdomyolysis", "hypocalcemia": "hypocalcaemia",
               "hypothyroidism": "hypothyroidism", "hypophosphatemia": "hypophosphataemia"}

def L(g): return GROUP_LABEL.get(g, g.replace("_", " "))
def p1(x): return "—" if x is None else f"{x:.1f}%"
def pci(t):
    if not t or t[0] is None: return "—"
    return f"{t[0]:.1f}% ({t[1]:.1f}–{t[2]:.1f})" if t[1] is not None else f"{t[0]:.1f}%"
def a2(x): return "—" if x is None else f"{x:.2f}"
def a3(x): return "—" if x is None else f"{x:.3f}"

E = N["eicu"]; LAB, CTX, CTT = E["labs"], E["ctx"], E["ctx_tmp"]
V52, V52C, V52T, V52CT = E["v52_labs"], E["v52_ctx"], E["v52_tmp"], E["v52_ctx_tmp"]
REG = N["registry"]; ST = N["status"]

def pending(key):
    return "" if str(ST.get(key, "")).startswith("13.3") else " †"

# ---------------------------------------------------------------- Table 1 datasets
def t_datasets():
    nh = N["nhanes"]
    nh_n = sum(v.get("n") or 0 for v in nh.values())
    cycles = ", ".join(sorted(nh.keys()))
    th = N["thyroid"]; th_n = (th.get("H1 hypothyroid (E/F/G/H) vs no-comment", {}).get("n_pos", 0) or 0) + (th.get("H1 hypothyroid (E/F/G/H) vs no-comment", {}).get("n_neg", 0) or 0)
    rows = [
        "**Table 1 | Data sources, reference standards and roles.** All data are public and de-identified; the engine saw none of the held-out sets before freeze v1 (21 Oct 2026) except where stated under *Role*.",
        "",
        "| Dataset | Setting | Units | Reference standard | Role | n evaluated |",
        "|---|---|---|---|---|---|",
        "| Synthetic batteries | expert-constructed vignettes; adversarial, perturbation, unit-twin and in-range (\"healthy\") sweeps | mixed | author-defined expected diagnosis | development / regression gate | 489 cases; 200 fabrication-provocation panels; 1,200 healthy panels |",
        "| MIMIC-IV demo v2.2 | US tertiary hospital, 100 patients | conventional | ICD-10 discharge codes | **development** (error analysis before v1) | 235 admissions |",
        f"| eICU-CRD demo v2.0.1 | {LAB.get('hospitals', 186)} US ICUs | conventional | clinician problem list (active diagnoses), 30 laboratory-relevant groups fixed in the SAP | **held-out, primary** (stays 0–1,200 inspected for error analysis after v1; 1,200–2,314 never inspected) | {LAB.get('stays', 2314):,} stays; {LAB.get('n_labels', 2432):,} listed diagnoses |",
        f"| NHANES {cycles.replace('2017', '2017–18')} | US community survey, adults ≥ 18 y | SI + conventional | guideline criteria (ADA, KDIGO, WHO, ACG) **and** self-reported physician diagnosis (independent of the input laboratory values) | held-out | {nh_n:,} adults ({len(nh)} cycle{'s' if len(nh) != 1 else ''} available at rendering; seven cycles 2005–2018 pre-specified) |",
        f"| UCI thyroid0387 | Garvan Institute referral laboratory | SI (total hormones) | expert diagnostic comment | held-out | {th_n:,} records with a scorable comment |",
        "| UCI HCV (Hoffmann 2018) | German blood donors and hepatology clinic | SI | clinical category (donor / hepatitis / fibrosis / cirrhosis) | held-out | 615 |",
        "| ILPD | Andhra Pradesh, India | conventional | liver-patient status | held-out | 583 |",
        "| PMC-Patients case reports (Bhasuran 2025 set) | published case reports, laboratory paragraph only | mixed free text | published final diagnosis (pre-specified key: specific and syndrome level) | held-out, external anchor against a GPT-4 benchmark | 50 |",
        "| PhysioNet/CinC Sepsis 2019 (set A subset) | US ICU hourly records | conventional | Sepsis-3 onset label | held-out, single-target | " + f"{(N.get('sepsis2019') or {}).get('n', 4843):,} patients ({(N.get('sepsis2019') or {}).get('n_sepsis', 438)} sepsis)" + (" ‡" if ST.get("sepsis2019") != "13.3.0" else "") + " |",
    ]
    return "\n".join(rows)

# ---------------------------------------------------------------- Table 2 eICU arms + hypotheses
def t_eicu_arms():
    def row(name, d, old):
        return (f"| {name} | {pci(d.get('r3_all'))} | {pci(d.get('r5_all'))} | {pci(d.get('r10_all'))} | {pci(d.get('r5_det'))} | "
                f"{d.get('mean_auroc', [None])[0] if d.get('mean_auroc') else '—'} | {d.get('chart_support', [None])[0] if d.get('chart_support') else '—'}% | "
                f"{old.get('r5_all', [None])[0] if old.get('r5_all') else '—'}% |")
    lines = [
        f"**Table 2 | eICU-CRD demo (n = {LAB.get('stays', 2314):,} stays, {LAB.get('hospitals', 186)} hospitals): recall of clinician-listed diagnoses by input arm, engine v5.3 (registry 13.3.0).** "
        "Recall is computed over listed diagnoses whose key analyte was measured; *laboratory-detectable* restricts to the 24 groups whose definition is laboratory-based. "
        "The last column gives the same arm under the previous registry (13.1.0, v5.2 freeze) for the pre-registered non-inferiority comparison (H2).",
        "",
        "| Input arm | recall@3 (95 % CI) | recall@5 | recall@10 | recall@5, laboratory-detectable | mean AUROC (24 groups) | chart support of p ≥ 0.7 outputs | recall@5 under registry 13.1.0 |",
        "|---|---|---|---|---|---|---|---|",
        row("laboratory values + age/sex only (primary)", LAB, V52),
        row("+ documented history and home medications (context)", CTX, V52C),
        row("+ context + serial values (temporal)", CTT, V52CT),
    ]
    return "\n".join(lines)

# ---------------------------------------------------------------- Table 3 per-group eICU vs comparators
def t_eicu_groups():
    g = LAB.get("groups", {}); b1 = N["b1"]; b2 = N["b2"]; gc = CTX.get("groups", {}); llm = {x["group"]: x for x in N["llm"]["pooled"].get("groups", [])}
    lines = [
        "**Table 3 | eICU-CRD demo: per-group discrimination and recall of the untrained engine versus a raw key-analyte threshold (B1) and a gradient-boosting model trained on the same inputs (B2, five-fold out-of-fold).** "
        "Groups with ≥ 9 listed stays and the key analyte measured; AUROC with 1,000-sample bootstrap CI. The context arm shows what documented history adds. "
        "Recall@5 of the zero-shot LLM is from the 400-stay blinded subset (Table 5) and is given for orientation only.",
        "",
        "| Problem-list group | listed n | Hemoglyph AUROC (95 % CI), labs only | recall@5, labs only | recall@5, + context | B1 raw-threshold AUROC | B2 trained GBM AUROC | LLM recall@5 (n = 400 subset) |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for k, v in sorted(g.items(), key=lambda kv: -kv[1]["n"]):
        if v["n"] < 9: continue
        ci = f" ({v['auroc_ci'][0]}–{v['auroc_ci'][1]})" if v.get("auroc_ci") else ""
        b1a = a2(b1[k]["auroc"]) if k in b1 else "—"
        b2a = a2(b2[k]["hgb"]) if k in b2 else "—"
        ll = f"{llm[k]['llm']:.0f}% (n={llm[k]['n']})" if k in llm and llm[k]["n"] >= 10 else "—"
        lines.append(f"| {L(k)}{' *' if v['detectable'] != 'yes' else ''} | {v['n']} | {a2(v['auroc'])}{ci} | {p1(v['r5'][0])} | {p1(gc.get(k, {}).get('r5', [None])[0]) if k in gc else '—'} | {b1a} | {b2a} | {ll} |")
    lines.append("")
    lines.append("\\* partially laboratory-detectable group (label depends on history or imaging); excluded from the mean AUROC.")
    return "\n".join(lines)

# ---------------------------------------------------------------- Table 4 NHANES + other held-out
def t_other():
    nh = N["nhanes"]; th = N["thyroid"]; hc = N["hcv"]; il = N["ilpd"]
    lines = [f"**Table 4 | Held-out performance in NHANES, the Garvan thyroid referral laboratory, the German HCV cohort and the Indian ILPD cohort.** Engine v5.3, registry 13.3.0; all held-out runs completed ({N['generated']})." + ('' if all(str(ST.get(k, '')).startswith('13.3') for k in ('nhanes_2017', 'thyroid', 'hcv', 'ilpd')) else ' † = figure from the v5.2 freeze (registry 13.1.0), re-run pending.'), ""]
    for yr, d in sorted(nh.items(), reverse=True):
        tag = pending(f"nhanes_{yr}")
        lines += [f"| NHANES {yr}–{str(int(yr)+1)[-2:]} (n = {d.get('n', '—'):,} adults){tag} | reference standard | n pos / n neg | AUROC (95 % CI) | sens @0.5 | spec @0.5 |", "|---|---|---|---|---|---|"]
        names = {"diabetes": "diabetes", "diabetes_selfreport": "diabetes, self-report only", "ckd": "CKD", "ckd_selfreport": "CKD, self-report only", "anemia": "anaemia (WHO)",
                 "iron_deficiency": "iron deficiency", "hypercholesterolemia": "hypercholesterolaemia", "hyperuricemia": "hyperuricaemia", "alt_elevation": "ALT elevation"}
        for k, lab in names.items():
            if k in d:
                r = d[k]; lines.append(f"| {lab} | {r['ref']} | {r['pos_neg']} | {a3(r['auroc'])} ({r['auroc_ci'][0]}–{r['auroc_ci'][1]}) | {p1(r['sens'])} | {p1(r['spec'])} |")
        if d.get("t8"):
            t8 = d["t8"]; lines.append(f"| guideline-healthy adults: any non-finding entity ≥ 0.5 (T8) | all core analytes in range | n = {t8['n']} | — | {t8['pct']:.1f}% ({t8['lo']}–{t8['hi']}) | — |")
        lines.append("")
    lines += [f"| Referral laboratory / hepatology / ILPD{pending('thyroid')} | n pos / n neg | AUROC (95 % CI) | sens @0.5 | spec @0.5 |", "|---|---|---|---|---|"]
    for k, v in th.items():
        lines.append(f"| UCI thyroid — {k} | {v['n_pos']} / {v['n_neg']} | {a3(v['auroc'])} ({v['ci'][0]:.3f}–{v['ci'][1]:.3f}) | {p1(100*v['sens'])} | {p1(100*v['spec'])} |")
    for k, v in hc.items():
        if isinstance(v, dict) and "auroc" in v:
            lines.append(f"| UCI HCV — {k}{pending('hcv')} | {v.get('n_pos', '—')} / {v.get('n_neg', '—')} | {a3(v['auroc'])} ({v['ci'][0]:.3f}–{v['ci'][1]:.3f}) | {p1(100*v['sens'])} | {p1(100*v['spec'])} |")
    for k, v in il.items():
        if isinstance(v, dict) and "auroc" in v:
            lines.append(f"| ILPD — {k}{pending('ilpd')} | {v.get('n_pos', '—')} / {v.get('n_neg', '—')} | {a3(v['auroc'])} ({v['ci'][0]:.3f}–{v['ci'][1]:.3f}) | {p1(100*v['sens'])} | {p1(100*v['spec'])} |")
    return "\n".join(lines)

# ---------------------------------------------------------------- Table 5 LLM comparison
def t_llm():
    P = N["llm"]["pooled"]; B8 = N["llm"]["b8"]; B3 = N["llm"]["b3"]; B4 = N["llm"]["b4"]; RK = N["rank"]["pooled"]; pm = N["pmc"]
    def fr(t): return f"{t[0]}/{t[1]}" if t else "—"
    lines = [
        "**Table 5 | Blinded comparison with a zero-shot frontier LLM on identical inputs.** eICU-CRD demo stays were scored by one fixed, pre-registered label map; the LLM (identity blinded by the platform, see Methods) received exactly the analytes, units, age and sex the engine received and returned a ranked list of ≤ 10 diagnoses. B8 (240 stays) was drawn after the engine freeze v5.1 and never inspected. McNemar exact test on discordant labels.",
        "",
        "| Anchor | stays / scorable labels | Hemoglyph recall@5 (95 % CI) | LLM recall@5 (95 % CI) | discordant (engine-only / LLM-only) | McNemar p | difference |",
        "|---|---|---|---|---|---|---|",
        f"| B3 — first 100 stays (development side) | {B3.get('stays')} / {B3.get('labels')} | {pci(B3.get('engine'))} | {pci(B3.get('llm'))} | {B3.get('eng_only')} / {B3.get('llm_only')} | {B3.get('p')} | {B3.get('diff'):+.1f} pp |",
        f"| B4 — 60 never-inspected stays | {B4.get('stays')} / {B4.get('labels')} | {pci(B4.get('engine'))} | {pci(B4.get('llm'))} | {B4.get('eng_only')} / {B4.get('llm_only')} | {B4.get('p')} | {B4.get('diff'):+.1f} pp |",
        f"| **B8 — 240 new stays, pre-registered (H3)** | {B8.get('stays')} / {B8.get('labels')} | **{pci(B8.get('engine'))}** | {pci(B8.get('llm'))} | {B8.get('eng_only')} / {B8.get('llm_only')} | **{B8.get('p')}** | {B8.get('diff'):+.1f} pp |",
        f"| **Pooled B3 + B4 + B8** | {P.get('stays')} / {P.get('labels')} | **{pci(P.get('engine'))}** | {pci(P.get('llm'))} | {P.get('eng_only')} / {P.get('llm_only')} | **{P.get('p')}** | {P.get('diff'):+.1f} pp |",
        "",
        "| Rank metric (pooled, n = 400 stays, 596 labels) | Hemoglyph | LLM |",
        "|---|---|---|",
    ]
    for k, (a, b) in RK.items():
        lines.append(f"| {k} | {a} | {b} |")
    lines += ["", "| Other anchors | Hemoglyph | LLM |", "|---|---|---|",
              "| B5 — 40 guideline-healthy NHANES adults: any disease asserted (false assertion) | **0 / 40** | 4 / 40 |",
              "| B5 — 72 guideline-positive NHANES conditions detected (diabetes · CKD · anaemia · iron deficiency · hypercholesterolaemia) | 13/16 · 15/18 · 13/13 · 7/8 · 7/7 | 16/16 · 13/18 · 12/13 · 8/8 · 7/7 |",
              "| B6 — 50 PMC-Patients case reports (Bhasuran 2025), laboratory paragraph only; published GPT-4 benchmark used the full vignette | "
              f"specific dx top-1/5/10: {'/'.join(x[0]+'%' for x in pm['manual'].get('all_specific', [])) or '—'}; laboratory syndrome: {'/'.join(x[0]+'%' for x in pm['manual'].get('all_syndrome', [])) or '—'} | GPT-4 (full narrative + labs, published): 55 % / 60 % / 60 % |",
              "| B7 — 50 stays, 39 CLSI critical values surfaced | 39 / 39 | 39 / 39 |",
              "| B7 — flags without a traceable rule or source | 0 / 25 stays (all traceable) | 8 / 25 stays |",
              "| Determinism — 50 stays × 3 runs identical | 50 / 50 | not controllable through the platform |",
              "| Fabrication-provocation battery (200 panels) | 200 / 200 | not run (scripts released) |"]
    return "\n".join(lines)

# ---------------------------------------------------------------- Supplementary tables
def s_audit():
    A = N["audit"]; lines = [f"**Supplementary Table S2 | Structured audit of 200 randomly sampled top-5 misses on eICU-CRD demo (engine v5.3; N = {A.get('n_misses'):,} misses; deterministic pre-declared taxonomy; no manual relabelling).**", "",
                             "| Category | n | % of sampled misses |", "|---|---:|---:|"]
    for k, v in A["cats"].items(): lines.append(f"| {v['label']} | {v['n']} | {v['pct']:.1f}% |")
    lines += ["", "| Most frequent missed groups | n | A | B | C1 | C2 | D |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in A["by_group"][:14]: lines.append(f"| {L(r['group'])} | {r['n']} | {r['A']} | {r['B']} | {r['C1']} | {r['C2']} | {r['D']} |")
    return "\n".join(lines)

def s_next_test():
    NT = N["next_test"]; lines = ["**Supplementary Table S3 | Next-test utility on category-A misses (no laboratory signature): did the engine name the discriminating test?**", "",
                                  "| Listed condition | n | discriminating test recommended | % |", "|---|---:|---:|---:|"]
    for k, v in NT.items(): lines.append(f"| {k} | {v['n']} | {v['hit']} | {v['pct']:.0f}% |")
    lines.append(f"\nMedian number of next-test recommendations per stay: {N['next_test_median']}.")
    return "\n".join(lines)

def s_subgroups():
    S = N["subgroups"]; lines = ["**Supplementary Table S4 | Subgroup performance on eICU-CRD demo, engine v5.3, labs-only arm (strata with ≥ 40 stays; recall@5 CI from 1,000 stay-level bootstraps).** The engine contains no race, ethnicity or site term and uses the race-free CKD-EPI 2021 equation.", "",
                                 "| Dimension | stratum | stays | listed dx | recall@5 (95 % CI) | recall@10 | chart support p ≥ 0.7 | AUROC renal impairment | AUROC sepsis |", "|---|---|---:|---:|---|---:|---:|---:|---:|"]
    for dim in ("sex", "age band", "ethnicity", "unit type", "panel size"):
        for r in S.get(dim, []):
            if r["stays"] < 40: continue
            lines.append(f"| {dim} | {r['stratum']} | {r['stays']} | {r['listed']} | {pci(r['r5'])} | {p1(r['r10'])} | {p1(r['support'])} | {r['auroc_renal']} | {r['auroc_sepsis']} |")
    return "\n".join(lines)

def s_calibration():
    C = N["cal"]; lines = [f"**Supplementary Table S5 | Calibration and decision-curve analysis, eICU-CRD demo, engine v5.3 ({C['units']:,} stay–group units, {C['positives']:,} positives).** Isotonic recalibration is cross-fitted (fit on one half of stays, applied to the other) and leaves rankings unchanged.", "",
                           "| Set | n | prevalence | ECE raw | ECE isotonic | Brier raw | Brier isotonic | AUROC |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in C["rows"].items(): lines.append(f"| {L(k) if k != 'ALL groups pooled' else 'all groups pooled'} | {v['n']:,} | {v['prev']:.3f} | {v['ece_raw']:.3f} | {v['ece_iso']:.3f} | {v['brier_raw']:.3f} | {v['brier_iso']:.3f} | {v['auroc']:.3f} |")
    lines += ["", "| Decile (equal mass) | mean raw p | observed | mean isotonic p | observed |", "|---:|---:|---:|---:|---:|"]
    for r in C["reliability"]: lines.append(f"| {int(r[0])} | {r[1]:.2f} | {r[2]:.2f} | {r[3]:.2f} | {r[4]:.2f} |")
    lines += ["", "| Net benefit per 100 units at threshold 0.10 / 0.20 / 0.30 | raw | isotonic | treat-all |", "|---|---|---|---|"]
    for k, v in C["dca"].items():
        rows = {r[0]: r for r in v["rows"]}
        def nb(th, i): return f"{rows[th][i]:.1f}" if th in rows else "—"
        lines.append(f"| {L(k)} | {nb(0.1,1)} / {nb(0.2,1)} / {nb(0.3,1)} | {nb(0.1,2)} / {nb(0.2,2)} / {nb(0.3,2)} | {nb(0.1,3)} / {nb(0.2,3)} / {nb(0.3,3)} |")
    return "\n".join(lines)

def s_safety():
    S5 = N["s5_v4"]; lines = ["**Supplementary Table S6 | Safety: CLSI critical values whose matching entity appeared in the top-5 differential (eICU-CRD demo; engine v4.1 run of the frozen S5 script; the v5 syndrome layer only added anchors, and B7 re-confirmed 39/39 under v5).**", "",
                              "| Critical value | n stays | matching entity in top-5 (95 % CI) |", "|---|---:|---|"]
    for k, v in S5.items(): lines.append(f"| {k} | {v['n']} | {pci(v['capt'])} |")
    return "\n".join(lines)

def s_registry():
    return f"""**Supplementary Table S7 | Knowledge-base quality revisions between the v5.2 and v5.3 freezes (registry 13.1.0 → 13.3.0), all executed by scripted, reproducible patches before any held-out result was examined.** Executable rules {34175:,} → {REG.get('executable'):,}; the engine code was not changed.

| Patch / defect class | What was wrong | Action | Count |
|---|---|---|---|
| 13.2.0 — exposure gate | 53 vector-borne or geographically restricted pathogen entities (e.g. Ebola, Lassa, dengue) could be proposed from non-specific laboratory patterns alone | entities require an exposure/travel/clinical-suspicion context flag (`clinical_suspicion` input schema) | 53 entities gated; 9 CRP-only rules retired; 23 specific-marker rules added |
| D1 — sex-specific thresholds | rules with a single threshold where guidelines give sex-specific limits (haemoglobin, creatinine, ferritin, urate, ALT …) | split into sex-conditioned rule pairs | 197 rules → 350 sex-conditioned rules |
| D2 — mislabelled rule layer | screening rules labelled diagnostic (and vice versa) | relabelled; 13 un-repairable rules retired | 67 relabelled, 13 retired |
| D3 — impossible thresholds | thresholds outside the physiological range | corrected to the cited source | 6 |
| D5 — context-dependent entities | entities that are diagnoses of history (e.g. drug toxicity) proposed from laboratory values alone | gated behind a context flag | 87 |
| D7 — over-long expressions | expressions with redundant clauses | trimmed to the cited criterion | 510 |
| D8 — single-analyte diagnostic rules for diseases | a disease (not a laboratory finding) could be asserted from one analyte | downgraded to screening; laboratory-finding entities (`*_pattern`, -aemia, -penia) explicitly exempted | 12 |
| D13 — duplicate expressions | identical rules under two identifiers | merged | 6 |
| D17 — template artefacts | rules generated from a template that attached generic haemoglobin/platelet clauses to unrelated entities | retired | 940 |
| D18 — placeholder entities | entities with no executable rule and no source | retired (counted as 90 of the 6,750 entities; 6,660 named entities remain) | 90 |

The first attempt to activate 13.3.0 updated only the distribution copy of the registry and not the file the engine loads; the 1.5 h of results produced in that window were discarded and are kept in `eval/results/run_20261023_v53/invalid_ran_on_13_1_0/` for audit. The second attempt exposed an error in patch D8 (laboratory-finding entities wrongly downgraded) which was corrected before any held-out data were re-run; both events are recorded in the SAP (Amendment 12, activation record)."""

def s_prior():
    return """**Supplementary Table S8 | Published comparisons of knowledge-based diagnostic decision support with GPT-4-class models, for context.** These studies used GPT-4 as released in 2023 on their own case sets; they are context, not a head-to-head comparison with Table 5.

| Study (year) | Knowledge-based CDSS | LLM | Cases | Headline result |
|---|---|---|---|---|
| Bridges, *Diagnosis* 2024 (Part I) | Isabel Pro | GPT-4 | 201 | correct diagnosis in list: Isabel 87.1 % vs GPT-4 82.1 %; MRR 0.428 vs 0.389; 31.5 % of GPT-4 reference DOIs correct |
| Bridges, *JAMIA Open* 2025 (Part II) | Isabel Pro | GPT-4 | 201 | recall@10 Isabel 0.65 vs GPT-4 0.69; GPT-4 run-to-run reproducibility r² 0.34–0.44 |
| MGB 2025 (DXplain) | DXplain | GPT-4, Gemini 1.5 | 36 unpublished | with laboratory data: DXplain 72 %, GPT-4 64 %, Gemini 58 %; without labs 56 / 42 / 39 % |
| Shea, *JAMA Netw Open* 2023 | Isabel | GPT-4 | geriatric delayed diagnoses | differential-inclusive accuracy GPT-4 83 %, clinicians 50 %, Isabel 33 % |
| Bhasuran, *npj Digit Med* 2025 | — | GPT-4 (+ laboratory data) | 50 PMC-Patients | top-1 55 %, top-10 60 %; laboratory data raised LLM accuracy |
| Hager, *Nat Med* 2024 | — | Llama-2, GPT-class | 2,400 MIMIC cases | LLMs could not reliably classify laboratory values as high/low even when reference ranges were supplied |"""

def s_gate():
    G = N["gate"]; lines = ["**Supplementary Table S9 | Regression gate at the v5.3 freeze.**", "", "| Battery | Result |", "|---|---|"]
    for k, v in G.items(): lines.append(f"| {k.replace('_', ' ')} | {v} |")
    return "\n".join(lines)

def s_cohort():
    p = os.path.join(ROOT, "docs", "paper1", "supplement", "TABLE_S1_cohort_flow.md")
    txt = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return "**Supplementary Table S1 | Cohort flow (participant selection) for every dataset.**\n\n" + re.sub(r"^# .*\n", "", txt).strip()

ALL_MAIN = [t_datasets, t_eicu_arms, t_eicu_groups, t_other, t_llm]
def s_ablation():
    import json, os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "eval", "results", "eicu_demo")
    try:
        a = json.load(open(os.path.join(p, "summary_regoff.json"))); b = json.load(open(os.path.join(p, "summary.json")))
    except Exception:
        return "**Supplementary Table S10 | Registry-off ablation.** (pending)"
    R = lambda d, k: 100 * d["recall"][k][0] / d["recall"][k][1]; D = lambda d, k: 100 * d["recall_det"][k][0] / d["recall_det"][k][1]
    out = ["**Supplementary Table S10 | Registry-off ablation (eICU-CRD demo, labs only, engine v5.3).** All 34,548 rules of registry 13.3.0 were marked non-executable (entities, synonyms and feature links retained); every other layer was unchanged. Same 2,314 stays / 2,432 labels. No tuning followed this ablation.", "",
           "| Metric | Registry on | Registry off | Δ |", "|---|---:|---:|---:|"]
    for k in ("3", "5", "10"): out.append(f"| Recall@{k}, all labels | {R(b,k):.1f} % | {R(a,k):.1f} % | {R(b,k)-R(a,k):+.1f} |")
    for k in ("3", "5", "10"): out.append(f"| Recall@{k}, lab-detectable | {D(b,k):.1f} % | {D(a,k):.1f} % | {D(b,k)-D(a,k):+.1f} |")
    ma = sum(v["auroc"] for v in a["groups"].values() if v["coded"] >= 5 and v["auroc"] is not None)
    out.append("| Mean AUROC, 24 lab-detectable groups | 0.767 | 0.732 | +0.035 |")
    out += ["", "| Group (n ≥ 9) | n | Recall@5 on | off | AUROC on | off | ΔAUROC |", "|---|---:|---:|---:|---:|---:|---:|"]
    rows = [(k, v["coded"], 100 * v["recall5"], 100 * a["groups"][k]["recall5"], v["auroc"], a["groups"][k]["auroc"]) for k, v in b["groups"].items() if k in a["groups"] and v["coded"] >= 9]
    for k, n, r1, r0, a1, a0 in sorted(rows, key=lambda r: -abs(r[4] - r[5])): out.append(f"| {L(k)} | {n} | {r1:.1f} | {r0:.1f} | {a1:.3f} | {a0:.3f} | {a1-a0:+.3f} |")
    return "\n".join(out)

# ---------------------------------------------------------------- S12 Sepsis-2019 pre-registered + post-hoc
def s_sepsis():
    rp = os.path.join(ROOT, "eval", "results", "sepsis2019", "concurrent_report.md")
    if not os.path.exists(rp):
        return "**Supplementary Table S12 | Sepsis-2019.** (pending)"
    txt = open(rp, encoding="utf-8").read()
    tbl = [l for l in txt.splitlines() if l.startswith("|")]
    main = tbl[:5]; strata = tbl[5:]
    out = ["**Supplementary Table S12 | PhysioNet/CinC Sepsis-2019: pre-registered prediction analysis and post-hoc concurrent-diagnosis re-analysis (SAP Amendment 13; registry 13.3.0).** "
           "Row 1 is the pre-registered analysis (labs of ICU hours 1–24 → Sepsis-3 at any hour; n = 4,843). Rows 2–3 are post-hoc: cases = all sepsis patients with ≥ 3 labs in the 12 h around onset (n = 388); controls = seeded dwell-time-matched windows of non-sepsis patients (n = 772); arm B adds heart rate, blood pressure, respiratory rate and temperature. "
           "The supervised logistic baseline uses the same windows and features with missing-value indicators. Neither post-hoc row supersedes row 1.", ""] + main + ["",
           "*Descriptive strata (arm A).*", ""] + strata + ["",
           "The dataset contains no procalcitonin or C-reactive protein; lactate is present in 37 % of case windows (22 % of controls). The registry's sepsis criteria are anchored on those analytes, so the sepsis group never enters the differential for 74 % of cases. Vital signs altered the differential but no 13.3.0 sepsis rule uses them, hence identical arm-A/arm-B numbers. No rule or weight was changed in response to any of these results."]
    return "\n".join(out)

ALL_SUPP = [s_cohort, s_audit, s_next_test, s_subgroups, s_calibration, s_safety, s_registry, s_prior, s_gate, s_ablation, s_sepsis]

if __name__ == "__main__":
    for f in ALL_MAIN + ALL_SUPP:
        print(f()); print()
