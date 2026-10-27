"""Minimal end-to-end example: one laboratory panel in, a cited differential out (engine v7, registry 14.1.0)."""
import json, logging
logging.disable(logging.CRITICAL)
import analyse_gidlines as ag

engine = ag.ClinicalRuleEngine()
panel = {
    "creatinine": {"value": 3.1, "unit": "mg/dL"},
    "bun": {"value": 58, "unit": "mg/dL"},
    "potassium": {"value": 6.2, "unit": "mmol/L"},
    "bicarbonate": {"value": 16, "unit": "mmol/L"},
    "sodium": {"value": 136, "unit": "mmol/L"},
    "glucose": {"value": 110, "unit": "mg/dL"},
    "hemoglobin": {"value": 9.1, "unit": "g/dL"},
    "wbc": {"value": 8.2, "unit": "10^3/uL"},
}
report = engine.interpret(panel, None, {"age_years": 64, "sex_at_birth": "female"}).to_dict()
for d in report["differential_diagnosis"][:8]:
    print(f'{d["probability"]:.2f}  {d["disease_id"]}')
json.dump(report, open("example_report.json", "w"), indent=1, default=str)
print("full report with rule identifiers and sources -> example_report.json")
