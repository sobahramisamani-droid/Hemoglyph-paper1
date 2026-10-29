"""Build the two human-validation instruments (A1 rule audit, B1 blind panel reading) and their scoring scripts' inputs.

python3 eval/human/make_forms.py
  -> eval/human/A1_rule_audit_form.docx / .csv / A1_rule_audit_sample.json   (100 rules, stratified by rule_type, seed 20261023)
  -> eval/human/B1_blind_panel_form.docx / .csv                                 (40 B8 panels = same 40 as the LLM re-read)
Scoring afterwards: python3 eval/human/score_forms.py
"""
import os, sys, json, random, csv, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
import brotli
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
H = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(ROOT, "eval", "results", "eicu_demo")


def doc_base(title_short, title_en):
    d = Document()
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:cs"), "Calibri"); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    for s in d.sections:
        s.left_margin = s.right_margin = Cm(1.5); s.top_margin = s.bottom_margin = Cm(1.5)
    h = d.add_heading(title_short, 0)
    p = d.add_paragraph(title_en); p.runs[0].font.size = Pt(9)
    return d


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), hexcolor); tcPr.append(shd)


def build_a1():
    reg = json.loads(brotli.decompress(open(os.path.join(ROOT, "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"), "rb").read()))
    rules = list(reg["rules"].values()); dis = reg["diseases"]; src = reg["guideline_sources"]
    dis = {(v.get("identity", {}).get("disease_id") or k): v for k, v in dis.items()}
    exe = [r for r in rules if r.get("executable")]
    top = set()
    for r in json.load(open(os.path.join(ROOT, "eval/results/run_20261023_v5/eicu_per_stay_v5_1.json"))):
        top.update(x[0] for x in r["top5"])
    op = [r for r in exe if r["disease_id"] in top]
    rnd = random.Random(20261023)
    def strat(pool, n):
        by = collections.defaultdict(list)
        for r in pool: by[r["rule_type"]].append(r)
        q = {k: max(1, round(n * len(v) / len(pool))) for k, v in by.items()}
        while sum(q.values()) > n: q[max(q, key=q.get)] -= 1
        while sum(q.values()) < n: q[max(q, key=lambda k: len(by[k]))] += 1
        out = []
        for k, m in q.items(): out += rnd.sample(sorted(by[k], key=lambda r: r["rule_id"]), m)
        return out, q
    s1, q1 = strat(op, 60); s2, q2 = strat([r for r in exe if r["disease_id"] not in top], 40)
    for r in s1: r["_stratum"] = "S1_operational"
    for r in s2: r["_stratum"] = "S2_whole_registry"
    sample = s1 + s2; rnd.shuffle(sample)
    quota = {"S1_operational": q1, "S2_whole_registry": q2}
    rows = []
    for i, r in enumerate(sample, 1):
        ex = r.get("expression", {}); d = dis.get(r["disease_id"], {})
        if "feature_id" in ex:
            expr = f'{ex["feature_id"]} {ex.get("operator","")} {ex.get("value","")} {ex.get("unit","") or ""}'.strip()
        else:
            expr = json.dumps(ex, ensure_ascii=False)[:300]
        srcs = "; ".join(f'{src.get(s, {}).get("organization", "")} — {src.get(s, {}).get("title", s)} ({src.get(s, {}).get("year", "")})' for s in r.get("source_ids", []))[:400]
        rows.append(dict(n=i, stratum=r["_stratum"], rule_id=r["rule_id"], disease=d.get("identity", {}).get("name_en", r["disease_id"]),
                         rule_type=r["rule_type"], expression=expr, population="/".join(r.get("population", {}).get("age_groups", [])) + "; sex " + str(r.get("population", {}).get("sex", "")),
                         urgent=bool(r.get("urgent")), sources=srcs, explanation=(r.get("scientific_explanation") or "")[:600], limitations=" | ".join(r.get("limitations", []))[:300]))
    json.dump(rows, open(os.path.join(H, "A1_rule_audit_sample.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(H, "A1_rule_audit_form.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["n", "stratum", "rule_id", "disease", "rule_type", "expression", "population", "sources", "VERDICT (1=correct,2=incorrect,3=ambiguous)", "SEVERITY if incorrect (A=unsafe,B=wrong threshold/unit,C=wrong source/attribution,D=cosmetic)", "comment"])
        for r in rows: w.writerow([r["n"], r["stratum"], r["rule_id"], r["disease"], r["rule_type"], r["expression"], r["population"], r["sources"], "", "", ""])
    d = doc_base("Form A1 — Random audit of 100 rules from the Hemoglyph knowledge base", "Form A1 — Random audit of 100 executable rules, Hemoglyph guideline registry v13.1.0: 60 from the operational set (diseases surfaced on eICU) + 40 from the whole registry; stratified by rule type; seed 20261023")
    for t in ["Purpose: to estimate the error rate of knowledge-base rules that were drafted with AI assistance and reviewed by the first author. Your answers are reported in the paper as an error rate with a 95% confidence interval.",
                        "Instruction: for each rule answer only the following question — is this threshold/direction/population clinically defensible for this disease and this rule type (screening / diagnostic criterion / exclusion criterion / severity), on the basis of the cited source?",
                        "Options: 1 = correct   2 = incorrect   3 = ambiguous/context-dependent. If incorrect, grade severity: A = unsafe (could lead to a dangerous decision), B = wrong threshold/unit, C = wrong source or attribution but rule correct, D = cosmetic.",
                        "Important: screening rules are deliberately sensitivity-oriented and non-specific (diagnosis_allowed=false); do not judge them as 'does not diagnose on its own' but ask whether they are reasonable as a warning sign for this disease.",
                        "Two strata: 60 rules from the operational set (diseases that appeared in any eICU top-5) and 40 from the whole registry (mostly auto-generated biomarker-pattern entities). The stratum is shown on the form and reported separately; judge both with the same rigour.", "Approximate time: 90–150 minutes. Please add your name, specialty, years of experience and the date at the end. Answers may be entered in this file or in the accompanying CSV."]:
        p = d.add_paragraph(t)
    for r in rows:
        d.add_paragraph()
        h = d.add_paragraph(); h.add_run(f'#{r["n"]}  [{r["stratum"]}]  {r["disease"]}  —  {r["rule_type"]}' + ("  ⚠ urgent" if r["urgent"] else "")).bold = True
        tb = d.add_table(rows=0, cols=2); tb.style = "Table Grid"; tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        for k, v in (("rule_id", r["rule_id"]), ("expression", r["expression"]), ("population", r["population"]), ("sources", r["sources"]), ("explanation", r["explanation"]), ("limitations", r["limitations"])):
            c = tb.add_row().cells; c[0].text = k; c[1].text = v; shade(c[0], "EEEEEE"); c[0].width = Cm(2.5); c[1].width = Cm(15)
        c = tb.add_row().cells; c[0].text = "VERDICT"; c[1].text = "[ ] 1 correct    [ ] 2 incorrect    [ ] 3 ambiguous        severity (if incorrect): [ ]A [ ]B [ ]C [ ]D"; shade(c[0], "FFF2CC"); shade(c[1], "FFF2CC")
        c = tb.add_row().cells; c[0].text = "comment"; c[1].text = "\n"; shade(c[0], "FFF2CC")
    d.add_paragraph(); p = d.add_paragraph("Name: ______________  Specialty: ______________  Years of experience: ____  Date: __________  Signature: ________")
    d.save(os.path.join(H, "A1_rule_audit_form.docx"))
    return quota


AB = {"troponin_i": "Troponin I (ng/mL)", "troponin_t": "Troponin T (ng/mL)", "mean_corpuscular_volume": "MCV (fL)", "mean_platelet_volume": "MPV (fL)", "hemoglobin": "Hb (g/dL)", "red_blood_cell_count": "RBC (10^6/µL)", "hematocrit": "Hct (%)", "white_blood_cell_count": "WBC (10^3/µL)", "platelet_count": "Platelets (10^3/µL)", "glucose": "Glucose (mg/dL)", "alkaline_phosphatase": "ALP (U/L)", "mean_corpuscular_hemoglobin": "MCH (pg)", "creatinine": "Creatinine (mg/dL)", "total_bilirubin": "Total bilirubin (mg/dL)", "direct_bilirubin": "Direct bilirubin (mg/dL)", "potassium": "K (mEq/L)", "mean_corpuscular_hemoglobin_concentration": "MCHC (g/dL)", "blood_urea_nitrogen": "BUN (mg/dL)", "total_protein": "Total protein (g/dL)", "thyroid_stimulating_hormone": "TSH (mIU/L)", "sodium": "Na (mEq/L)", "chloride": "Cl (mEq/L)", "calcium_total": "Calcium (mg/dL)", "calcium_ionized": "Ionized Ca (as reported)", "aspartate_aminotransferase": "AST (U/L)", "bicarbonate": "HCO3 (mEq/L)", "albumin": "Albumin (g/dL)", "alanine_aminotransferase": "ALT (U/L)", "basophils_percent": "Basophils (%)", "eosinophils_percent": "Eosinophils (%)", "neutrophils_percent": "Neutrophils (%)", "lymphocytes_percent": "Lymphocytes (%)", "monocytes_percent": "Monocytes (%)", "band_neutrophils_percent": "Bands (%)", "creatine_kinase_total": "CK (U/L)", "creatine_kinase_mb": "CK-MB (ng/mL)", "arterial_po2": "paO2 (mmHg)", "arterial_ph": "pH", "arterial_pco2": "paCO2 (mmHg)", "base_excess": "Base excess (mEq/L)", "magnesium": "Mg (mg/dL)", "phosphate": "Phosphate (mg/dL)", "anion_gap": "Anion gap", "lactate": "Lactate (mmol/L)", "prothrombin_time": "PT (s)", "international_normalized_ratio": "INR", "activated_partial_thromboplastin_time": "aPTT (s)", "red_cell_distribution_width_cv": "RDW (%)", "uric_acid": "Uric acid (mg/dL)", "serum_osmolality": "Osmolality (mOsm/kg)", "b_type_natriuretic_peptide": "BNP (pg/mL)", "ammonia": "Ammonia (µg/dL)", "amylase": "Amylase (U/L)", "lipase": "Lipase (U/L)", "triglycerides": "Triglycerides (mg/dL)", "total_cholesterol": "Total cholesterol (mg/dL)", "lactate_dehydrogenase": "LDH (U/L)"}


def build_b1():
    cases = json.load(open(os.path.join(R, "b8_rerun40_cases.json")))
    panels = {p["case"]: p for p in json.load(open(os.path.join(R, "b8_blind_panels_n240.json")))}
    d = doc_base("Form B1 — Blind reading of 40 ICU laboratory panels", "Form B1 — Blind physician reading of 40 ICU admission laboratory panels (eICU-CRD demo, open access; same 40 panels as the LLM test–retest set)")
    for t in ["Purpose: a third comparison arm (physician / language model / Hemoglyph) on identical panels. You see only age, sex and the laboratory values of the first 24 h of ICU admission — exactly the information given to the engine and the language model.",
                        "Instruction: for each panel list up to 10 diagnoses/syndromes in order of likelihood (1 = most likely). Generic terms (e.g. acute kidney injury, sepsis, diabetic ketoacidosis, GI bleeding, heart failure, anemia, hypokalemia) are sufficient. Do not use references, the internet or AI; note the time spent per panel.",
                        "Scoring is automatic, with the same keyword map used for the language model (Recall@5 against the documented ICU diagnoses). Approximate time: 3–5 minutes per panel, 2–3 hours in total.",
                        "Confidentiality: the data are part of the public eICU-CRD demo (PhysioNet, open access) and are de-identified."]:
        p = d.add_paragraph(t)
    with open(os.path.join(H, "B1_blind_panel_form.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["case", "rank", "diagnosis", "probability_0_to_1 (optional)", "minutes_spent"])
        for c in cases:
            for k in range(1, 11): w.writerow([c, k, "", "", ""])
    for c in cases:
        p = panels[c]
        d.add_page_break()
        h = d.add_paragraph(); h.add_run(f'{c}   —   age {p["age"]}, {p["sex"]}').bold = True
        labs = list(p["labs"].items()); half = (len(labs) + 1) // 2
        tb = d.add_table(rows=half, cols=4); tb.style = "Table Grid"
        for i in range(half):
            for j, (k, v) in enumerate([labs[i]] + ([labs[i + half]] if i + half < len(labs) else [])):
                tb.cell(i, 2 * j).text = AB.get(k, k); tb.cell(i, 2 * j + 1).text = f"{v:g}"; shade(tb.cell(i, 2 * j), "F2F2F2")
        d.add_paragraph()
        t2 = d.add_table(rows=11, cols=3); t2.style = "Table Grid"
        t2.cell(0, 0).text = "#"; t2.cell(0, 1).text = "Diagnosis / syndrome (most likely first)"; t2.cell(0, 2).text = "probability (optional)"
        for i in range(1, 11): t2.cell(i, 0).text = str(i)
        for j in range(3): shade(t2.cell(0, j), "FFF2CC")
        d.add_paragraph("Time spent (minutes): ____")
    d.add_paragraph(); p = d.add_paragraph("Name: ______________  Specialty: ______________  Years of experience: ____  Date: __________  Signature: ________")
    d.save(os.path.join(H, "B1_blind_panel_form.docx"))
    return len(cases)


if __name__ == "__main__":
    q = build_a1(); n = build_b1()
    print("A1 quota by rule_type:", q); print("B1 panels:", n)
