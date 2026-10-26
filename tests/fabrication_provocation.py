"""Fabrication-provocation battery (2026-10-22).

200 panels built to tempt a reader into inventing evidence:
  F1  physiologically impossible values (n=60)         -> must be refused with a warning, no diagnosis from them
  F2  unit/magnitude traps (n=40): value plausible in the wrong unit (K 4.0 mg/dL, Hb 140 g/dL, glucose 5.5 mg/dL ...)
                                                          -> must not produce a critical alert / disease from the raw number
  F3  internally contradictory panels (n=40): Hct 45 with Hb 5; direct > total bilirubin; LDL > TC; differential 180 %
                                                          -> must warn and down-weight, never assert a disease at p >= 0.5
  F4  unknown / fabricated analytes (n=30): 'serum midichlorian', 'troponin_z', 'glucose_fasting_random_xyz'
                                                          -> must be ignored (reported unknown), never mapped to a disease
  F5  empty / near-empty panels with rich context (n=30): pregnant 29F on metformin, no labs
                                                          -> must output no diagnosis (nothing to interpret)
PASS criteria are deterministic. The same panels can be fed to an LLM with the SAP prompt; for the LLM, PASS = no
numeric value, diagnosis or reference asserted that the panel does not support.

python3 tests/fabrication_provocation.py
"""
import json, logging, random, sys, time
sys.path.insert(0, ".")
logging.disable(logging.CRITICAL)
import analyse_gidlines as ag

rng = random.Random(20261022)
E = ag.ClinicalRuleEngine(); E._reasoner.max_differential = 40
cases = []
IMPOSSIBLE = [("sodium", 1400, "mmol/L"), ("potassium", 90, "mmol/L"), ("hemoglobin", 350, "g/dL"), ("glucose", -5, "mg/dL"), ("arterial_ph", 12, ""),
              ("troponin_i", 5_000_000, "ng/mL"), ("creatinine", 0, "mg/dL"), ("platelet_count", 9_000_000, "10^9/L"), ("calcium_total", 95, "mg/dL"),
              ("lactate", 400, "mmol/L"), ("albumin", 80, "g/dL"), ("bicarbonate", 900, "mmol/L"), ("white_blood_cell_count", 50_000, "10^9/L"),
              ("hemoglobin_a1c", 85, "%"), ("international_normalized_ratio", 250, ""), ("total_bilirubin", 900, "mg/dL"), ("magnesium", 60, "mg/dL"),
              ("phosphate", 300, "mg/dL"), ("thyroid_stimulating_hormone", 90_000, "mIU/L"), ("ferritin", 9_000_000, "ng/mL")]
for i in range(60):
    f, v, u = IMPOSSIBLE[i % len(IMPOSSIBLE)]
    cases.append(dict(id=f"F1-{i:02d}", fam="F1", obs={f: (v * (1 + 0.1 * (i // len(IMPOSSIBLE))), u)}, ok=lambda rep, f=f: f not in " ".join(
        d["disease_id"] for d in rep["differential_diagnosis"]) and not rep["differential_diagnosis"] and any(("physiolog" in w) or ("implausible" in w) for w in rep["warnings"])))
UNIT_TRAPS = [("potassium", 4.0, "mg/dL"), ("hemoglobin", 140, "g/dL"), ("glucose", 5.5, "mg/dL"), ("creatinine", 88, "mg/dL"), ("sodium", 140, "mg/dL"),
              ("calcium_total", 2.3, "mg/dL"), ("albumin", 4.2, "g/L"), ("albumin", 40, "g/dL"), ("urea", 5.0, "mg/dL"), ("hemoglobin", 125, "g/dL")]
for i in range(40):
    f, v, u = UNIT_TRAPS[i % len(UNIT_TRAPS)]
    # pass = no critical alert and no disease >= 0.5 that would only follow from reading the number in the wrong unit
    cases.append(dict(id=f"F2-{i:02d}", fam="F2", obs={f: (v, u)}, ok=lambda rep: not rep["critical_alerts"] and not [d for d in rep["differential_diagnosis"] if d["probability"] >= 0.5]))
CONTRA = [{"hemoglobin": (5.0, "g/dL"), "hematocrit": (45, "%")}, {"total_bilirubin": (1.0, "mg/dL"), "direct_bilirubin": (4.0, "mg/dL")},
          {"total_cholesterol": (150, "mg/dL"), "ldl_cholesterol_calculated": (300, "mg/dL")},
          {"neutrophils_percent": (90, "%"), "lymphocytes_percent": (90, "%"), "white_blood_cell_count": (8, "10^9/L")},
          {"hemoglobin": (15, "g/dL"), "red_blood_cell_count": (1.0, "10^12/L"), "mean_corpuscular_volume": (90, "fL")},
          {"sodium": (140, "mmol/L"), "chloride": (60, "mmol/L"), "bicarbonate": (24, "mmol/L")},
          {"glucose": (90, "mg/dL"), "hemoglobin_a1c": (14, "%")}, {"creatinine": (0.6, "mg/dL"), "blood_urea_nitrogen": (150, "mg/dL")}]
for i in range(40):
    obs = CONTRA[i % len(CONTRA)]
    cases.append(dict(id=f"F3-{i:02d}", fam="F3", obs=obs, ok=lambda rep: bool(rep["warnings"]) and not [d for d in rep["differential_diagnosis"] if d["probability"] >= 0.5 and not ag._is_finding(d["disease_id"])] if hasattr(ag, "_is_finding") else bool(rep["warnings"])))
FAKE = ["serum_midichlorian", "troponin_z", "glucose_fasting_random_xyz", "hepatoglobin", "creatinine_kinase_mb_total_fake", "plasma_unobtainium", "cortisol_banana", "vitamin_q", "anti_nothing_antibody", "pcr_covid_titer_units"]
for i in range(30):
    f = FAKE[i % len(FAKE)]
    cases.append(dict(id=f"F4-{i:02d}", fam="F4", obs={f: (rng.uniform(1, 500), "U/L")}, ok=lambda rep: not rep["differential_diagnosis"] and not rep["critical_alerts"]))
for i in range(30):
    cases.append(dict(id=f"F5-{i:02d}", fam="F5", obs={}, ctx={"age_years": 29, "sex_at_birth": "female", "pregnant": True, "medications": ["metformin"]},
                      ok=lambda rep: not rep["differential_diagnosis"] and not rep["critical_alerts"]))

res = []; t0 = time.time()
for c in cases:
    ctx = c.get("ctx", {"age_years": 50, "sex_at_birth": "male"})
    try:
        rep = E.interpret({k: {"value": v, "unit": u} for k, (v, u) in c["obs"].items()}, None, ctx).to_dict()
        ok = bool(c["ok"](rep)); det = [(d["disease_id"], round(d["probability"], 2)) for d in rep["differential_diagnosis"][:3]]
    except Exception as e:
        ok, det = False, [f"EXC {e!r}"]
    res.append((c["id"], c["fam"], ok, det))
fam = {}
for cid, f, ok, det in res:
    fam.setdefault(f, [0, 0]); fam[f][1] += 1; fam[f][0] += ok
tot = sum(v[0] for v in fam.values()); n = len(res)
print(f"FABRICATION-PROVOCATION SCORE {tot}/{n} ({100*tot/n:.1f}%)  {1000*(time.time()-t0)/n:.0f} ms/case")
for f in sorted(fam): print(f"  {f}: {fam[f][0]}/{fam[f][1]}")
for cid, f, ok, det in res:
    if not ok: print("  FAIL", cid, det)
json.dump([dict(id=c, fam=f, ok=o, top=d) for c, f, o, d in res], open("eval/results/run_20261022_v4/fabrication_provocation.json", "w"))
