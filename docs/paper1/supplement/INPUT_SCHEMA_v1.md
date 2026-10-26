# Supplementary Note S5 — Hemoglyph engine input schema v1 (what the engine can see, with provenance)

The same JSON structure is consumed by the desktop application (after OCR + clinician review) and by every evaluation script in `eval/` (`E.interpret(observations, derived=None, context)`), so the evaluated system and the shipped system receive identical inputs. All fields except `observations[*].value` are optional. Evidence tiers in the last column are the maximum weight an input can contribute on its own (CONTEXT_DOCUMENTED 0.49 / CONFIRMED 0.80; laboratory evidence up to 0.95); non-laboratory inputs can never place a diagnosis in the differential without laboratory support (fabrication rule F5, tested in `tests/fabrication_provocation.py`).

## 1. `observations` — one entry per analyte (keyed by registry feature id, 2,045 ids)

| field | type | source in app | used by engine | tier / effect |
|---|---|---|---|---|
| `value` | number or qualitative string | OCR → review | yes | primary evidence |
| `unit` | string (UCUM-like, 300+ aliases) | OCR → review | yes — converted to canonical unit | — |
| `reported_reference.low/high` | numbers | OCR (printed interval) | yes — `reference_policy`: lab interval replaces registry interval except for guideline decision limits (`cdl_locked`, e.g. HbA1c 6.5 %, LDL targets); conflicts produce a note | — |
| `flag` | H/L/HH/LL/A | OCR | display + consistency check only | — |
| `confirmed` | bool | review screen | unconfirmed items excluded | — |
| `timestamp` | ISO datetime | OCR `collected_at` / manual | ordering of series | — |
| `series[]` | `{t_hours, value}` | multiple reports or EHR | yes — 24-h trajectory module (ext11-T): first/last/min/max/delta/rise/fall per analyte | trajectory findings, e.g. KDIGO Δcreatinine, troponin dynamics |
| `metadata.hemolysis / lipemia / icterus` | bool or HIL index | OCR text (`detect_preanalytical`) or manual | yes — `preanalytical_gate` penalises K, LDH, AST, phosphate, Mg (haemolysis); Na, Hb/MCHC (lipaemia); creatinine (Jaffe), etc. | reliability ×0.5–0.7, warning |
| `source` | `input` / `derived` | — | measured outranks derived (direct LDL vs Friedewald) | — |

## 2. `context` — patient-level inputs (`ClinicalContext.from_any`)

| field | type | source | used by engine | tier |
|---|---|---|---|---|
| `age_years`, `sex_at_birth` | number / `male|female` | questionnaire | age- and sex-specific intervals, eGFR, paediatric rules | prerequisite |
| `pregnant`, `pregnancy_trimester` | bool / 1–3 | questionnaire | trimester intervals; excludes HbA1c diagnosis of diabetes | prerequisite |
| `weight_kg`, `height_cm` | numbers | questionnaire | BMI, Cockcroft-Gault, TyG | derived values |
| `fasting` | bool | questionnaire | fasting glucose / TG rules enabled only when true | gate |
| `known_conditions[]` | strings (free text, synonym-mapped) | questionnaire / EHR past history | **documented-history tier**: raises prior of the named disease only when a laboratory finding supports it; chronic disease gating (CKD vs AKI) | ≤ 0.49 documented, ≤ 0.80 confirmed |
| `current_medications[]` | strings | questionnaire / EHR | medication-induced explanations as competing hypotheses (diuretic → hypokalaemia, metformin → lactate, ACE-i → K); metformin never implies diabetes without HbA1c/glucose support | ≤ 0.49 |
| `family_history[]` | strings | questionnaire | hereditary patterns (haemochromatosis, thalassaemia trait) | ≤ 0.49 |
| `hemolysis` / `lipemia` / `icterus` | bool | **OCR-detected (new, 2026-10-23) or clinician** | same as observation-level flags, applied panel-wide | reliability |
| `specimen_type`, `specimen_collected_at` | string | OCR-detected (new) | provenance only (reported in trace); venous vs arterial handled where analyte ids differ | — |
| `ethnicity`, `altitude_m` | string / number | questionnaire | Hb altitude correction; ethnicity **not** used in eGFR (CKD-EPI 2021) | — |
| `symptoms_present`, `vasopressor_required`, `after_adequate_resuscitation` | bool | questionnaire (advanced) | Sepsis-3 septic-shock criteria; symptomatic hyperglycaemia | gate |

## 3. Not yet accepted (roadmap, in priority order)

1. **Symptoms / chief complaint** (chips) — planned as a separate evidence tier with its own ablation; not in Paper 1.
2. **Vital signs** (temperature, HR, RR, BP, SpO₂) — SIRS/qSOFA; Sepsis-2019 cohort will be used to evaluate.
3. **Baseline creatinine** (value + date) — KDIGO AKI staging against baseline rather than within-24-h delta.
4. **Smear morphology comments** — now detected by OCR (`morphology[]`) and shown as a warning, not yet consumed by rules.
5. **Care setting** (outpatient / ward / ICU) as a prior modifier.
6. **Geography / endemic exposure**.

## 4. Provenance guarantee

Every rule vote in the output trace records `(feature_id, value, unit, source, reference_used, penalty)` so that a reader can tell whether a conclusion rests on a measured value, a printed interval, a derived estimate, a documented history item or a specimen flag. This is the mechanism that makes the AI-assisted knowledge base auditable rule-by-rule (Form A1).

### Addendum (2026-10-23, registry 13.2.0) — `exposure_history`
Optional boolean context field. `true` = the clinician documents relevant travel, vector/animal contact, outbreak or occupational exposure. When absent or false, pathogen-specific infectious entities whose only laboratory evidence is routine chemistry/CBC (e.g., viral haemorrhagic fevers, rickettsioses, helminthiases) are **not** proposed; a positive pathogen-specific test (PCR, antigen, IgM, culture) proposes them regardless. See SAP Amendment 10.


### Addendum (2026-10-23, registry 13.3.0) — `clinical_suspicion`
`context.clinical_suspicion: true` (optional boolean, default absent). Analogous to `exposure_history`: 48 non-infectious etiologic entities (sarcomas, lymphomas, vasculitides, ALS, aortic dissection, inflammatory/rheumatic entities, nutritional deficiencies) whose only executable rules rest on routine analytes are evaluated **only** when the clinician states that the entity is clinically suspected. Without the flag these entities are never proposed from a panel. Rule population `sex` is now honoured for 350 split rules (creatinine, haemoglobin, haematocrit, RBC, ALT, AST, urate); if `sex_at_birth` is absent both sex variants are evaluated and the more sensitive one governs — supply sex whenever available.
