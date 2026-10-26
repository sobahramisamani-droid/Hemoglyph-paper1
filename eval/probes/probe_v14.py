"""Persistent v14 probes (kept in the workspace because /tmp is wiped hourly). Run: python3 eval/probes/probe_v14.py"""
import sys, os, logging; logging.disable(50); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import analyse_gidlines as ag
E = ag.ClinicalRuleEngine()
U = lambda **k: {a: {'value': v[0], 'unit': v[1]} for a, v in k.items()}
def run(name, vals, ctx, n=5):
    rep = E.interpret(vals, None, ctx).to_dict(); print(f'== {name}')
    for d in rep['differential_diagnosis'][:n]: print(f"   {d['rank']:2d} {d['disease_id']:45s} p={d['probability']:.2f} {d.get('tier')} {d['evidence_state']} {d.get('explained_by')}")
CASES = [
 ('Addison / adrenal crisis', U(cortisol_morning=(1.4,"ug/dL"), sodium=(122,"mmol/L"), potassium=(6.1,"mmol/L"), glucose=(48,"mg/dL"), blood_urea_nitrogen=(48,"mg/dL"), creatinine=(1.8,"mg/dL"), adrenocorticotropic_hormone=(640,"pg/mL"), calcium_total=(10.6,"mg/dL"), eosinophil_count_absolute=(0.9,"10^9/L")), {"age_years":38,"sex_at_birth":"female"}),
 ('single creat 2.0 outpatient', U(creatinine=(2.0,'mg/dL'), hemoglobin=(13.1,'g/dL'), potassium=(4.4,'mmol/L')), {"age_years":60,"sex_at_birth":"male"}),
 ('single creat 2.0 ICU', U(creatinine=(2.0,'mg/dL'), hemoglobin=(13.1,'g/dL'), potassium=(4.4,'mmol/L')), {"age_years":60,"sex_at_birth":"male","encounter":"icu"}),
 ('documented CKD cr 1.6', U(creatinine=(1.6,'mg/dL'), sodium=(139,'mmol/L'), potassium=(4.4,'mmol/L'), glucose=(95,'mg/dL'), hemoglobin=(13.5,'g/dL')), {"age_years":64,"sex_at_birth":"male","known_conditions":["renal insufficiency - creatinine 1-2"]}),
 ('IgG4 620', U(serum_igg4=(620,"mg/dL"), total_immunoglobulin_g=(2400,"mg/dL"), eosinophil_count_absolute=(0.8,"10^9/L"), total_immunoglobulin_e=(480,"IU/mL"), complement_c4=(6,"mg/dL"), alkaline_phosphatase=(310,"U/L"), lipase=(140,"U/L")), {"age_years":70,"sex_at_birth":"male"}),
 ('CKD4 panel', U(creatinine=(3.4,"mg/dL"), egfr_ckd_epi_creatinine=(18,"mL/min/1.73m2"), potassium=(5.6,"mmol/L"), hemoglobin=(9.8,"g/dL"), phosphate=(5.8,"mg/dL"), parathyroid_hormone_intact=(220,"pg/mL"), bicarbonate=(19,"mmol/L")), {"age_years":68,"sex_at_birth":"male"}),
 ('INR 8.5 critical', U(international_normalized_ratio=(8.5,'1'), hemoglobin=(8.7,'g/dL'), white_blood_cell_count=(17.9,'10*3/uL'), platelet_count=(409,'10*3/uL'), sodium=(131,'mmol/L')), {"age_years":60,"sex_at_birth":"male"}),
 ('uraemia + HAGMA', U(glucose=(218,'mg/dL'), bicarbonate=(16.3,'mmol/L'), creatinine=(11.1,'mg/dL'), potassium=(6.0,'mmol/L'), sodium=(131,'mmol/L'), anion_gap=(22,'mmol/L')), {"age_years":71,"sex_at_birth":"male"}),
 ('troponin single ICU', U(troponin_i=(0.5,'ng/mL'), creatinine=(1.1,'mg/dL'), hemoglobin=(10.2,'g/dL'), sodium=(131,'mmol/L')), {"age_years":70,"sex_at_birth":"male","encounter":"icu"}),
 ('sepsis-ish + anemia', U(white_blood_cell_count=(17,'10*3/uL'), lactate=(3.1,'mmol/L'), creatinine=(1.9,'mg/dL'), hemoglobin=(8.9,'g/dL'), platelet_count=(110,'10*3/uL')), {"age_years":66,"sex_at_birth":"female","encounter":"icu"}),
 ('septic panel mm[Hg]', U(lactate=(4.2,'mmol/L'), white_blood_cell_count=(19,'10*3/uL'), systolic_blood_pressure=(85,'mm[Hg]'), heart_rate=(118,'/min'), respiratory_rate=(26,'/min'), body_temperature=(38.9,'Cel'), creatinine=(1.7,'mg/dL')), {"age_years":58,"sex_at_birth":"male","encounter":"icu"}),
 ('healthy', U(hemoglobin=(14.5,'g/dL'), creatinine=(0.9,'mg/dL'), sodium=(140,'mmol/L'), potassium=(4.1,'mmol/L'), glucose=(88,'mg/dL'), alanine_aminotransferase=(22,'U/L')), {"age_years":35,"sex_at_birth":"female"}),
]
for name, vals, ctx in CASES: run(name, vals, ctx)
