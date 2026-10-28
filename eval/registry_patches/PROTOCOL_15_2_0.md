# Registry 15.2.0 — correction of defects found by the audit study (protocol written 2026-10-28 before the patch ran)

Scope. Only the defects recorded in `eval/audit/RESULTS_AUDIT.md` (Part 1, "defects in curated rules found
incidentally") and nothing else. Every change below is defined by a property of the rule text and the cited
source, not by any benchmark number. No threshold is tuned; no rule is added; the eICU/NHANES gate is run once
afterwards purely as a non-regression check and its result is reported whatever it is. If the gate shows a drop
> 0.5 points in any primary metric the patch is reported and NOT adopted (stop-and-report, no re-tuning).

Frozen v7 / 14.1.0 results are not touched; the paper's tables do not change.

## Changes

| id | class | rules | action | basis |
|---|---|---|---|---|
| C1 | implausible severity tier | `elevated_mean_corpuscular_volume_staging_severity_1_v1` (> 200 fL), `decreased_…` (< 20 fL), `elevated_total_protein_staging_severity_1_v1` (> 16.6 g/dL), `decreased_…` (< 1.5 g/dL) | status `retired_v15_2_0_implausible_tier`, executable = false | values lie outside the physiological range of the analyte (MCV ≈ 50–150 fL; total protein ≈ 3–12 g/dL); cited sources are reference-interval conventions that define no such tier |
| C2 | adult threshold applied to neonates | `iron_deficiency_anemia_bsg_2021_ferritin_30_cur13`, `iron_deficiency_anemia_bsg_2021_inflammation_adjusted_cur13`, `hemolytic_anemia_eha_2023_hemolysis_triad_cur13`, `autoimmune_hemolytic_anemia_eha_2023_dat_positive_hemolysis_cur13` | `population.age_groups` → adolescent, adult, older_adult (neonate/infant/child removed) | BSG 2021 IDA and EHA 2023 haemolysis guidance are adult guidelines; Hb < 12/13 g/dL is the WHO adult/adolescent (≥ 12 y) limit; neonatal lower limit ≈ 14.5 g/dL |
| C3a | unit label | every leaf `adrenocorticotropic_hormone` with unit `ng/mL` (values 0.1–100) | unit → `pg/mL`, value unchanged | the values are plasma ACTH numbers in pg/mL (reference ≈ 7–63 pg/mL, Tietz); the label was wrong by 1000×. Feature registry: canonical/ucum → `pg/mL`, accepted `pg/mL`, `pmol/L` (×0.2202), `ng/L` (×1) |
| C3b | unit label | every leaf `intact_parathyroid_hormone` with unit `ng/mL` (10, 65) | unit → `pg/mL`, value unchanged | reference 15–65 pg/mL; feature registry canonical pg/mL |
| C3c | unit conversion | every leaf `morning_cortisol` with unit `ng/mL` (60, 230) | → `ug/dL`, value ÷ 10 (6.0, 23.0) | exact conversion; feature registry accepts only ug/dL |
| C4a | wrong source | `acute_pancreatitis_exclusion_normal_lipase_v1`, `acute_pancreatitis_support_pattern_exclusion_normal_pancreatic_enzymes_v1` | `source_ids` → `acg_acute_pancreatitis_2024` | rules cited a GERD guideline; ACG 2024 acute pancreatitis guideline is the matching document (lipase/amylase normal-range exclusion) |
| C4b | wrong source | `chronic_pancreatitis_screening_1_v1`, `chronic_pancreatitis_diagnostic_criterion_1_v1` (faecal elastase < 200 / < 100 µg/g) | `source_ids` → `acg_pancreatitis_2024` | GERD guideline replaced by the ACG pancreatitis source already in the registry |
| C4c | wrong source | 10 rules citing `nes_sod_guidelines_2024` (a NASPGHAN paediatric metabolic-liver entry mis-keyed as a sodium guideline): hyponatraemia, SIADH and low-osmolality patterns → `ese_hyponatremia_2014`; hypernatraemia patterns (145/150 mmol/L) → `reference_interval_convention` | `source_ids` replaced | thresholds 135/130/125 mmol/L, urine osmolality > 100 mOsm/kg, urine sodium > 40 mmol/L, serum osmolality < 275 mOsm/kg are the ESE/ERA-EDTA 2014 definitions; 145/150 mmol/L are reference-limit conventions |

## Recorded as NOT a defect after inspection

`rhabdomyolysis_v1` ("CK > 0.0 U/L") carries `context.five_times_upper_reference_limit = true`; the engine replaces
the threshold by 5 × the laboratory's upper reference limit and returns UNKNOWN when none is reported. The static
detector does not read `context`, so this was a false positive of the audit, not a rule defect. RESULTS_AUDIT.md and
Supplementary Note 16 are corrected accordingly. β2-microglobulin: every leaf on `beta_2_microglobulin` uses mg/L,
consistent with that feature; the inconsistency noted in Part 1 is on a *different* feature id,
`beta_2_microglobulin_tumor` (feature registry mg/dL, two rules in mg/L), discovered only when the detectors were
re-run on 15.2.0, and is left open (see below) rather than added to this patch after the fact.

## Remaining after 15.2.0 (detectors re-run on 15.2.0: any 68 of 6,773; was 87 of 6,777)

Open, out of this protocol's scope, for a later release: 6 candidate (non-curated) rules with Hb < 12 g/dL and an
all-ages population; `beta_2_microglobulin_tumor` unit (2 rules); `cortisol_morning` — a second cortisol feature
whose registry unit is ng/mL while three `_p131` rules use µg/dL (3 rules; which side is wrong undetermined);
`irritable_bowel_syndrome_exclusion_criterion_2_v1` CRP ≥ 0; 54 source-scope flags, the majority adjudicated as
heuristic false positives in Part 3.

## Gate

`eval/realdata/eval_eicu.py --encounter icu` and `eval/realdata/eval_nhanes.py --n-max 1000 --encounter community`
with `HEMOGLYPH_REGISTRY_OVERRIDE` = 15.2.0, compared with the 15.1.0 runs on identical counts. Expected: no change
(none of the touched analytes — MCV/TP extreme tiers, ACTH, PTH, cortisol, lipase exclusions, sodium sources — alters
a fired rule on these panels except possibly the four anaemia population gates, which affect no adult stay).
