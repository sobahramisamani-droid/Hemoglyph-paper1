"""Static audit of an executable clinical rule base (Hemoglyph rule schema).

Frozen before the mutation study (PROTOCOL_AUDIT.md, Part 1). Pure functions over the rule dicts, the disease
dicts, the feature registry and the source table; no engine, no benchmark data.

Detectors (each returns a short reason or None):
  R2A  nonspecific single ubiquitous analyte voting for a clinical entity
  R7   arithmetic tier: every threshold = 1.5x / 0.5x of the same entity's screening threshold (same analyte)
  R9   impossible value: <= 0 for a non-negative analyte, or outside the feature's physiological limits
  DIR  direction conflict: finding-entity name says high/low but operator points the other way; or the entity's
       other rules on the same analyte point the other way; or a "<" threshold above the upper reference limit
       (resp. ">" below the lower) by more than the DIR_MARGIN
  UNIT unit not accepted for the feature, or value implausible after converting the stated unit to canonical
  POP  population includes neonate/infant while the threshold lies outside the feature's neonate reference range
  SRC  first cited source's scope has no overlap with the entity's domain (both known)
Usage: python audit.py <registry.json.br> [--out report.json]   (prints densities per class)
"""
import json, re, sys, collections, brotli, os

ROOT = os.path.dirname(os.path.abspath(__file__))
HG = os.path.abspath(os.path.join(ROOT, "..", ".."))

UBIQUITOUS = {
 "c_reactive_protein","white_blood_cell_count","erythrocyte_sedimentation_rate","procalcitonin",
 "aspartate_aminotransferase","alanine_aminotransferase","lactate_dehydrogenase","albumin","total_protein",
 "platelets","platelet_count","hemoglobin","mean_corpuscular_volume","creatinine","urea","blood_urea_nitrogen",
 "sodium","potassium","chloride","bicarbonate","calcium_total","phosphate","magnesium","glucose","lactate",
 "creatine_kinase_total","total_bilirubin","alkaline_phosphatase","gamma_glutamyl_transferase","uric_acid",
 "thyroid_stimulating_hormone","free_thyroxine","ferritin","transferrin_saturation","lymphocyte_count_absolute",
 "eosinophil_count_absolute","neutrophil_count_absolute","amylase","lipase","fasting_plasma_glucose",
 "hemoglobin_a1c","triglycerides","total_cholesterol","hdl_cholesterol","international_normalized_ratio",
 "prothrombin_time","fibrinogen","serum_osmolality","red_cell_distribution_width_cv","red_blood_cell_count",
 "hematocrit","monocytes_percent","neutrophils_percent","lymphocytes_percent","eosinophils_percent"}
FINDING_ENTITY = re.compile(
 r"_pattern$|^ckd_stage|^hyper|^hypo|agranulocytosis|penia$|cytosis$|philia$|anemia$|^iron_deficiency|azotemia$|"
 r"acidosis|alkalosis|^elevated_|^decreased_|^low_|^high_|^prolonged_|^severe_|uremia$|emia$|^anemia|^polycythemia|"
 r"dyslipidemia|hyperlipidemia|^diabetes_mellitus$|^prediabetes|^type_2_diabetes|^metabolic_syndrome|coagulopathy|"
 r"^thrombocyt|^leukocyt|^neutro|^lympho|^eosino|^pancytopenia|^bicytopenia|syndrome_of_inappropriate|^dehydration|"
 r"^malnutrition|^refeeding|^rhabdomyolysis$|^gout$|^tumor_lysis")
ALLOW_TIER = {
 ("egfr_ckd_epi_creatinine",45.0),("egfr_ckd_epi_creatinine",30.0),("egfr_ckd_epi_creatinine",15.0),
 ("fecal_elastase_1",100.0),("urine_protein_to_creatinine_ratio",0.3),("urine_albumin_to_creatinine_ratio",300.0),
 ("hemoglobin",8.0),("hemoglobin",7.0),("platelets",50.0),("platelets",20.0),("platelets",100.0),
 ("neutrophil_count_absolute",1.0),("neutrophil_count_absolute",0.5),("lactate",4.0),("lactate",2.0),
 ("potassium",6.0),("potassium",2.5),("sodium",120.0),("sodium",125.0),("calcium_total",14.0),("calcium_total",7.0),
 ("glucose",250.0),("glucose",54.0),("total_bilirubin",2.0),("total_bilirubin",3.0),("international_normalized_ratio",1.5),
 ("international_normalized_ratio",5.0),("albumin",2.5),("albumin",3.0),("creatine_kinase_total",5000.0),
 ("ammonia",100.0),("thyroid_stimulating_hormone",10.0),("thyroid_stimulating_hormone",0.1),("c_reactive_protein",100.0),
 ("procalcitonin",2.0),("procalcitonin",0.25),("procalcitonin",10.0),("white_blood_cell_count",25.0),
 ("eosinophil_count_absolute",1.5),("triglycerides",500.0),("triglycerides",880.0),("ldl_cholesterol_calculated",190.0),
 ("bicarbonate",18.0),("bicarbonate",15.0),("phosphate",1.0),("magnesium",1.0),("uric_acid",10.0),("hematocrit",65.0),
 ("mean_corpuscular_volume",120.0),("fibrinogen",100.0),("fibrinogen",150.0),("arterial_ph",7.2),("arterial_ph",7.1),
 ("ceruloplasmin",10.0),("folate_serum",3.0)}
SIGNED = ("base_excess", "anion_gap", "standard_base")
PHYS = {"hemoglobin":(1,25),"hematocrit":(5,75),"sodium":(100,200),"potassium":(1,12),"chloride":(60,140),"bicarbonate":(2,60),
 "glucose":(5,3000),"fasting_plasma_glucose":(5,1000),"creatinine":(0.1,40),"urea":(1,400),"blood_urea_nitrogen":(1,300),"calcium_total":(3,20),
 "phosphate":(0.2,20),"magnesium":(0.2,10),"albumin":(0.5,6.5),"total_protein":(2,14),"total_bilirubin":(0.05,60),"alanine_aminotransferase":(1,20000),
 "aspartate_aminotransferase":(1,20000),"alkaline_phosphatase":(5,5000),"lactate_dehydrogenase":(20,20000),"c_reactive_protein":(0.05,800),
 "white_blood_cell_count":(0.05,600),"platelets":(1,3000),"neutrophil_count_absolute":(0,300),"lymphocyte_count_absolute":(0,300),"eosinophil_count_absolute":(0,100),
 "lactate":(0.2,40),"uric_acid":(0.3,30),"thyroid_stimulating_hormone":(0.001,600),"free_thyroxine":(0.05,15),"ferritin":(1,60000),"transferrin_saturation":(1,100),
 "hemoglobin_a1c":(3,25),"triglycerides":(10,15000),"total_cholesterol":(30,1500),"hdl_cholesterol":(1,200),"ldl_cholesterol_calculated":(5,1000),
 "international_normalized_ratio":(0.5,20),"prothrombin_time":(5,200),"fibrinogen":(10,1500),"egfr_ckd_epi_creatinine":(1,200),"creatine_kinase_total":(5,1000000),
 "procalcitonin":(0.01,1000),"erythrocyte_sedimentation_rate":(0,200),"mean_corpuscular_volume":(40,160),"amylase":(1,10000),"lipase":(1,20000),"ammonia":(1,2000),"arterial_ph":(6.5,8.0)}
QUANT_UNITS = {"mg/dL","mmol/L","umol/L","µmol/L","g/dL","g/L","ng/mL","ug/dL","µg/dL","nmol/L","pmol/L","mg/L","ug/L","µg/L","ng/dL","pg/mL","mmol/mol","mEq/L"}
ENTITY_DOM_SYN = {"rheumatology":"autoimmune","pediatric":"pediatric_neonatal","nephrology":"renal","hepatology":"liver","metabolic":"diabetes_metabolic",
 "diabetes":"diabetes_metabolic","haematology":"hematology","hematology_oncology":"hematology","infection":"infectious","cardiology":"cardiovascular","obstetrics":"pregnancy"}
KEEP_SINGLE = {"hereditary_hemochromatosis_c282y_screening_1_v1","familial_chylomicronemia_syndrome_existing_screening_1_v1",
 "familial_chylomicronemia_syndrome_existing_diagnostic_criterion_1_v1","tangier_disease_screening_1_v1","tangier_disease_diagnostic_criterion_1_v1",
 "lcat_deficiency_screening_1_v1","lcat_deficiency_diagnostic_criterion_1_v1","malignant_hyperthermia_stage_p131","acute_hepatitis_screen_p131",
 "warfarin_over_anticoagulation_authentic_criterion_v1","sepsis_screening_1_v1",
 "acute_pancreatitis_atlanta_2012_lipase_3x_uln_cur13","acute_pancreatitis_atlanta_2012_amylase_3x_uln_cur13"}
DIR_MARGIN = 1.15
HIGH_WORDS = re.compile(r"^elevated_|^high_|^hyper|cytosis$|philia$|^prolonged_|uremia$|^leukocytosis|^thrombocytosis|^polycythemia|^erythrocytosis")
LOW_WORDS = re.compile(r"^decreased_|^low_|^hypo|penia$|^anemia|anemia$|deficiency$|^short_")
CONV = {
 ("glucose","mmol/L"):18.0, ("fasting_plasma_glucose","mmol/L"):18.0, ("creatinine","umol/L"):1/88.4, ("creatinine","µmol/L"):1/88.4,
 ("total_cholesterol","mmol/L"):38.67, ("ldl_cholesterol_calculated","mmol/L"):38.67, ("hdl_cholesterol","mmol/L"):38.67,
 ("triglycerides","mmol/L"):88.57, ("calcium_total","mmol/L"):4.0, ("total_bilirubin","umol/L"):1/17.1, ("total_bilirubin","µmol/L"):1/17.1,
 ("urea","mmol/L"):6.006, ("blood_urea_nitrogen","mmol/L"):2.8, ("uric_acid","umol/L"):1/59.48, ("uric_acid","mmol/L"):16.81,
 ("hemoglobin","g/L"):0.1, ("hemoglobin","mmol/L"):1.611, ("albumin","g/L"):0.1, ("phosphate","mmol/L"):3.1, ("magnesium","mmol/L"):2.43,
 ("ferritin","pmol/L"):1/2.247, ("c_reactive_protein","mg/dL"):10.0, ("lactate","mg/dL"):1/9.01, ("iron","umol/L"):1/0.179,
 ("vitamin_b12","pmol/L"):1.355, ("folate","nmol/L"):1/2.266, ("vitamin_d_25_hydroxy","nmol/L"):1/2.496,
 ("hemoglobin_a1c","mmol/mol"):None, ("morning_cortisol","ng/mL"):0.1, ("morning_cortisol","nmol/L"):1/27.59, ("cortisol","nmol/L"):1/27.59,
 ("vitamin_b12","pmol/L"):1.355, ("iron","umol/L"):5.585, ("total_iron_binding_capacity","umol/L"):5.585, ("ammonia","umol/L"):1/0.587}
# source scope keyword -> disease domain(s)
SCOPE2DOM = {
 "ckd":"renal","nephrology":"renal","egfr":"renal","albuminuria":"renal","aki":"renal","kidney":"renal","glomerular":"renal","dialysis":"renal",
 "diabetes":"endocrine","prediabetes":"endocrine","dka":"endocrine","glycemic":"endocrine","thyroid":"endocrine","adrenal":"endocrine","pituitary":"endocrine","parathyroid":"endocrine","vitamin_d":"endocrine","bone":"endocrine","endocrine":"endocrine","hypoglycemia":"endocrine","lipid":"cardiovascular","lipids":"cardiovascular","dyslipidemia":"cardiovascular","cholesterol":"cardiovascular",
 "anemia":"hematology","anaemia":"hematology","iron":"hematology","hemoglobin":"hematology","haematology":"hematology","hematology":"hematology","myeloid":"hematology","lymphoid":"hematology","leukemia":"hematology","lymphoma":"hematology","thalassemia":"hematology","hemolysis":"hematology","transfusion":"hematology","itp":"hematology","b12":"hematology","folate":"hematology",
 "coagulation":"coagulation","dic":"coagulation","thrombosis":"coagulation","anticoagulation":"coagulation","vte":"coagulation","bleeding":"coagulation","hemostasis":"coagulation",
 "infection":"infectious","infectious":"infectious","sepsis":"infectious","pneumonia":"infectious","hiv":"infectious","hepatitis_b":"infectious","hepatitis_c":"infectious","tuberculosis":"infectious","malaria":"infectious","uti":"infectious","meningitis":"infectious","antimicrobial":"infectious","covid":"infectious",
 "cardiology":"cardiovascular","cardiac":"cardiovascular","heart_failure":"cardiovascular","acs":"cardiovascular","troponin":"cardiovascular","myocardial":"cardiovascular","hypertension":"cardiovascular","cardiovascular":"cardiovascular",
 "liver":"liver","hepatology":"liver","cirrhosis":"liver","masld":"liver","nafld":"liver","hepatitis":"liver","cholestasis":"liver","wilson":"liver","hemochromatosis":"liver","alcohol":"liver",
 "rheumatology":"autoimmune","lupus":"autoimmune","sle":"autoimmune","gout":"autoimmune","arthritis":"autoimmune","vasculitis":"autoimmune","autoimmune":"autoimmune","celiac":"gastroenterology","ibd":"gastroenterology","pancreatitis":"gastroenterology","gastroenterology":"gastroenterology",
 "oncology":"oncology","cancer":"oncology","tumor":"oncology","myeloma":"oncology","tumor_lysis":"oncology",
 "electrolyte":"electrolyte_acid_base","electrolytes":"electrolyte_acid_base","sodium":"electrolyte_acid_base","potassium":"electrolyte_acid_base","hyponatremia":"electrolyte_acid_base","hyperkalemia":"electrolyte_acid_base","acid_base":"electrolyte_acid_base","calcium":"electrolyte_acid_base","magnesium":"electrolyte_acid_base","phosphate":"electrolyte_acid_base",
 "toxicology":"toxicology_tdm","poisoning":"toxicology_tdm","tdm":"toxicology_tdm","drug_monitoring":"toxicology_tdm","overdose":"toxicology_tdm","toxic_alcohols":"toxicology_tdm",
 "pregnancy":"pregnancy","obstetrics":"pregnancy","preeclampsia":"pregnancy","gestational":"pregnancy","neonatal":"pediatric_neonatal","pediatrics":"pediatric_neonatal","pediatric":"pediatric_neonatal",
 "allergy":"allergy","ige":"allergy","nutrition":"nutrition","vitamin":"nutrition","malnutrition":"nutrition","refeeding":"nutrition","genetics":"genetics","genetic":"genetics","newborn_screening":"genetics","inborn":"genetics",
 "critical_care":"critical_care","icu":"critical_care","shock":"critical_care","rhabdomyolysis":"critical_care","laboratory":"*","reference_intervals":"*","general":"*","essential_diagnostics":"*","diagnostics":"*"}
DOM_NEIGHBOURS = {  # domains that legitimately share sources
 "renal":{"electrolyte_acid_base","diabetes_metabolic","critical_care","cardiovascular"},"electrolyte_acid_base":{"renal","endocrine","critical_care","nutrition"},
 "endocrine":{"diabetes_metabolic","electrolyte_acid_base","nutrition","pregnancy","cardiovascular","genetics"},"diabetes_metabolic":{"endocrine","renal","cardiovascular","pregnancy"},
 "hematology":{"oncology","nutrition","coagulation","genetics","liver"},"coagulation":{"hematology","critical_care","liver"},"oncology":{"hematology","genetics"},
 "infectious":{"critical_care","liver","hematology"},"critical_care":{"infectious","renal","electrolyte_acid_base","coagulation","cardiovascular","toxicology_tdm"},
 "liver":{"infectious","hematology","gastroenterology","nutrition","genetics"},"cardiovascular":{"critical_care","renal","endocrine","diabetes_metabolic"},
 "autoimmune":{"renal","hematology","coagulation"},"gastroenterology":{"liver","nutrition","autoimmune"},"nutrition":{"hematology","endocrine","gastroenterology","pediatric_neonatal"},
 "pregnancy":{"endocrine","hematology","renal","cardiovascular"},"genetics":{"endocrine","hematology","pediatric_neonatal","nutrition","liver"},"toxicology_tdm":{"critical_care"},
 "allergy":{"autoimmune"},"pediatric_neonatal":{"nutrition","genetics","hematology"},"general":set()}
for _a, _b in [("endocrine","renal"),("autoimmune","gastroenterology"),("autoimmune","endocrine"),("critical_care","gastroenterology"),("critical_care","liver"),
               ("critical_care","nutrition"),("toxicology_tdm","hematology"),("toxicology_tdm","coagulation"),("cardiovascular","genetics"),("oncology","endocrine"),
               ("oncology","gastroenterology"),("oncology","liver"),("renal","autoimmune"),("renal","genetics"),("infectious","gastroenterology"),("infectious","pediatric_neonatal"),
               ("pregnancy","diabetes_metabolic"),("electrolyte_acid_base","toxicology_tdm"),("electrolyte_acid_base","genetics"),("hematology","infectious"),("hematology","pregnancy")]:
    DOM_NEIGHBOURS.setdefault(_a, set()).add(_b); DOM_NEIGHBOURS.setdefault(_b, set()).add(_a)

def leaves(e):
    if not isinstance(e, dict): return []
    if "feature_id" in e: return [e]
    for k in ("all", "any", "none"):
        if k in e: return [l for c in e[k] for l in leaves(c)]
    if "n_of" in e: return [l for c in e["n_of"].get("conditions", []) for l in leaves(c)]
    return []

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

class Audit:
    def __init__(self, registry, features, sources=None):
        self.R = registry["rules"] if "rules" in registry else registry
        self.D = registry.get("diseases", {}) if isinstance(registry, dict) else {}
        self.S = sources if sources is not None else registry.get("guideline_sources", {})
        self.F = features
        self.kind = {k: (v.get("classification") or {}).get("entity_kind") for k, v in self.D.items()}
        self.dom = {k: ((v.get("classification") or {}).get("domains") or [None])[0] for k, v in self.D.items()}
        self.scr = collections.defaultdict(set); self.dirs = collections.defaultdict(collections.Counter)
        for rid, r in self.R.items():
            if not r.get("executable"): continue
            for l in leaves(r.get("expression")):
                v = num(l.get("value"))
                if v is None: continue
                if r.get("rule_type") == "screening": self.scr[(r["disease_id"], l["feature_id"])].add(v)
                if l.get("operator") in ("<", "<=", ">", ">="): self.dirs[(r["disease_id"], l["feature_id"])][l["operator"][0]] += 1

    def ref(self, fid, pop=None):
        rr = (self.F.get(fid) or {}).get("reference_ranges") or []
        if pop: rr = [x for x in rr if x.get("population") == pop]
        else: rr = [x for x in rr if str(x.get("population", "")).startswith("adult")] or rr
        lows = [x["low"] for x in rr if isinstance(x.get("low"), (int, float))]; highs = [x["high"] for x in rr if isinstance(x.get("high"), (int, float))]
        return (min(lows) if lows else None, max(highs) if highs else None, rr[0].get("unit") if rr else None)
    def limits(self, fid):
        pl = ((self.F.get(fid) or {}).get("validation") or {}).get("physiological_limits") or {}
        return pl.get("min"), pl.get("max")
    def units_ok(self, fid):
        f = self.F.get(fid) or {}; u = set((f.get("measurement") or {}).get("allowed_units") or []) | set((f.get("units") or {}).get("accepted") or [])
        c = (f.get("measurement") or {}).get("canonical_unit") or (f.get("units") or {}).get("canonical")
        if c: u.add(c)
        return u, c

    def d_r2a(self, rid, r):
        L = leaves(r.get("expression")); dis = r["disease_id"]
        if self.kind.get(dis) != "clinical_entity" or len(L) != 1 or L[0]["feature_id"] not in UBIQUITOUS: return None
        if FINDING_ENTITY.search(dis) or r.get("rule_type") == "exclusion_criterion" or rid in KEEP_SINGLE: return None
        return f"single ubiquitous analyte {L[0]['feature_id']} for clinical entity {dis}"
    def d_r7(self, rid, r):
        if r.get("rule_type") not in ("staging_severity", "diagnostic_criterion"): return None
        L = leaves(r.get("expression")); dis = r["disease_id"]
        if not L: return None
        hits = []
        for l in L:
            v = num(l.get("value"))
            if v is None or (l["feature_id"], v) in ALLOW_TIER: return None
            m = [(s, f) for s in self.scr.get((dis, l["feature_id"]), ()) for f in (1.5, 0.5) if s != v and abs(v - s * f) < 1e-6]
            if not m: return None
            hits.append(f"{l['feature_id']} {v:g} = {m[0][1]}x{m[0][0]:g}")
        return "arithmetic tier: " + "; ".join(hits)
    def d_r9(self, rid, r):
        for l in leaves(r.get("expression")):
            v = num(l.get("value")); fid = l["feature_id"]
            if v is None: continue
            if v < 0 and not any(s in fid for s in SIGNED): return f"negative threshold {fid} {v}"
            if v == 0 and l.get("operator") in ("<", "<=") and not any(s in fid for s in SIGNED): return f"{fid} {l['operator']} 0 impossible"
            if fid in PHYS:
                u = l.get("unit"); _, canon = self.units_ok(fid)
                if u and canon and u != canon: continue
                lo, hi = PHYS[fid]
                if v < lo or v > hi: return f"{fid} {l['operator']} {v} outside physiological bounds [{lo}, {hi}]"
        return None
    def d_dir(self, rid, r):
        dis = r["disease_id"]; L = leaves(r.get("expression"))
        if r.get("rule_type") == "exclusion_criterion" or "none" in (r.get("expression") or {}): return None
        per_feat = collections.Counter(l["feature_id"] for l in L)
        for l in L:
            op = l.get("operator"); v = num(l.get("value")); fid = l["feature_id"]
            if op not in ("<", "<=", ">", ">=") or v is None: continue
            d = op[0]
            stem = fid.split("_")[0]
            if len(stem) >= 4 and re.search(rf"(^|_){stem}", dis) and per_feat[fid] == 1:
                if HIGH_WORDS.search(dis) and d == "<": return f"entity {dis} names a HIGH state but rule says {fid} {op} {v}"
                if LOW_WORDS.search(dis) and d == ">": return f"entity {dis} names a LOW state but rule says {fid} {op} {v}"
            if per_feat[fid] == 1:
                c = self.dirs.get((dis, fid))
                if c:
                    other = c[">" if d == "<" else "<"]; same = c[d] - 1
                    if other >= 3 and same <= 0: return f"{fid} {op} {v} contradicts {other} other rules of {dis} that use the opposite direction"
            lo, hi, ru = self.ref(fid); u = l.get("unit")
            if u and ru and u != ru: continue
            if FINDING_ENTITY.search(dis) and per_feat[fid] == 1:
                if d == "<" and hi and lo is not None and v > hi * 2: return f"{fid} < {v} but upper reference limit is {hi}"
                if d == ">" and lo and lo > 0 and hi is not None and v < lo / 2: return f"{fid} > {v} but lower reference limit is {lo}"
        return None
    def d_unit(self, rid, r):
        for l in leaves(r.get("expression")):
            u = l.get("unit"); fid = l["feature_id"]; v = num(l.get("value"))
            if not u or v is None or fid not in self.F: continue
            u = u.replace("µ", "u"); ok, canon = self.units_ok(fid); ok = {x.replace("µ", "u") for x in ok}; canon = (canon or "").replace("µ", "u")
            fac = CONV.get((fid, u), CONV.get((fid, u.replace("u", "µ"))))
            if fac is None and u == canon: continue
            if fac is None and u in QUANT_UNITS and canon in QUANT_UNITS and u not in ok:
                return f"unit {u} not accepted for {fid} (accepted {sorted(ok)[:4]})"
            if fac in (None, 1.0): continue
            vc = v * fac; lo, hi = PHYS.get(fid, (None, None))
            if lo is None:
                pl = ((self.F.get(fid) or {}).get("validation") or {}).get("physiological_limits") or {}; lo, hi = pl.get("min"), pl.get("max")
            if (lo is not None and vc < lo) or (hi is not None and vc > hi): return f"{fid} {v} {u} = {vc:g} {canon}, outside physiological bounds [{lo}, {hi}]"
        return None
    def d_pop(self, rid, r):
        ages = set((r.get("population") or {}).get("age_groups") or [])
        if not ages & {"neonate", "infant"}: return None
        for l in leaves(r.get("expression")):
            v = num(l.get("value")); fid = l["feature_id"]
            if v is None: continue
            nlo, nhi, _ = self.ref(fid, "neonate"); alo, ahi, _ = self.ref(fid)
            if nlo is None or alo is None: continue
            op = l.get("operator", "")
            if op.startswith("<") and nlo >= 1.15 * v and abs(v - alo) < 1e-6: return f"{fid} < {v} (adult lower limit) applied to neonates whose lower limit is {nlo}"
            if op.startswith(">") and nhi and ahi and abs(v - ahi) < 1e-6 and nhi >= 1.15 * v: return f"{fid} > {v} (adult upper limit) applied to neonates whose upper limit is {nhi}"
        return None
    def d_src(self, rid, r):
        sid = (r.get("source_ids") or [None])[0]; dis = r["disease_id"]; dom = self.dom.get(dis); dom = ENTITY_DOM_SYN.get(dom, dom)
        if not sid or not dom or dom in ("general", None) or dom not in DOM_NEIGHBOURS: return None
        if sid in ("reference_interval_convention", "generated_pair_pattern", "who_essential_lab_2024", "tietz_7e_2023"): return None
        s = self.S.get(sid) or {}
        scope = [str(x).lower().replace(" ", "_") for x in (s.get("scope") or [])]
        title = str(s.get("title", "")).lower()
        doms = set()
        for w in scope + re.findall(r"[a-z_]+", title.replace("-", "_")):
            if w in SCOPE2DOM: doms.add(SCOPE2DOM[w])
        if not doms or "*" in doms: return None
        if dom in doms or doms & DOM_NEIGHBOURS.get(dom, set()): return None
        return f"source {sid} scope {sorted(doms)} vs entity domain {dom}"

    DETECTORS = ("r2a", "r7", "r9", "dir", "unit", "pop", "src")
    def run_rule(self, rid, r):
        out = {}
        for d in self.DETECTORS:
            why = getattr(self, "d_" + d)(rid, r)
            if why: out[d] = why
        return out
    def run(self, only=None):
        rep = {}
        for rid, r in self.R.items():
            if not r.get("executable") or rid.startswith("co_"): continue
            if only and rid not in only: continue
            f = self.run_rule(rid, r)
            if f: rep[rid] = f
        return rep

def load_br(p): return json.loads(brotli.decompress(open(p, "rb").read()))

def densities(rep, n):
    c = collections.Counter(d for f in rep.values() for d in f)
    return {d: {"n": c[d], "per_100": round(100 * c[d] / n, 2)} for d in Audit.DETECTORS} | {"any": {"n": len(rep), "per_100": round(100 * len(rep) / n, 2)}, "rules": n}

if __name__ == "__main__":
    reg = load_br(sys.argv[1]); feats = load_br(os.path.join(HG, "HEMOGLYPH_FEATURE_REGISTRY.json.br"))["features"]
    a = Audit(reg, feats); rep = a.run()
    n = sum(1 for k, v in a.R.items() if v.get("executable") and not k.startswith("co_"))
    print(json.dumps(densities(rep, n), indent=1))
    if "--out" in sys.argv: json.dump(rep, open(sys.argv[sys.argv.index("--out") + 1], "w"), indent=0)
