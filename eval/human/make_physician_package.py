"""Physician (haematologist) review package for Paper 1 — two instruments, one workbook.

  python3 eval/human/make_physician_package.py
  -> eval/human/Hemoglyph_physician_review_package_v1.xlsx
  -> eval/human/PHYSICIAN_REVIEW_INSTRUCTIONS.md

Instrument P1 — output review: 100 eICU-demo stays (frozen engine v7 outputs), 50 whose top-5 contains a haematological
entry and 50 random others (seed 20261027). One row per suggestion (500 rows) + one summary row per case.
Instrument P2 — haematology rule audit: the stratum-A rules from the frozen source-concordance sample whose disease is
haematological (quote from the cited source is mandatory for CONCORDANT/DISCORDANT).
The reviewer is blind to the clinician problem list and to which suggestions are counted as hits.
"""
import os, sys, gzip, json, csv, random, collections
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
H = os.path.dirname(os.path.abspath(__file__))
SEED = 20261027
UNITS = {"sodium": "mmol/L", "potassium": "mmol/L", "chloride": "mmol/L", "bicarbonate": "mmol/L", "anion_gap": "mmol/L",
         "blood_urea_nitrogen": "mg/dL", "creatinine": "mg/dL", "glucose": "mg/dL", "calcium_total": "mg/dL", "calcium_ionized": "mmol/L",
         "magnesium": "mg/dL", "phosphate": "mg/dL", "albumin": "g/dL", "total_protein": "g/dL", "total_bilirubin": "mg/dL",
         "direct_bilirubin": "mg/dL", "aspartate_aminotransferase": "U/L", "alanine_aminotransferase": "U/L", "alkaline_phosphatase": "U/L",
         "lactate_dehydrogenase": "U/L", "lipase": "U/L", "amylase": "U/L", "creatine_kinase_total": "U/L", "creatine_kinase_mb": "ng/mL",
         "troponin_i": "ng/mL", "troponin_t": "ng/mL", "b_type_natriuretic_peptide": "pg/mL", "ammonia": "µmol/L", "lactate": "mmol/L",
         "uric_acid": "mg/dL", "triglycerides": "mg/dL", "total_cholesterol": "mg/dL", "c_reactive_protein": "mg/dL",
         "serum_osmolality": "mOsm/kg", "thyroid_stimulating_hormone": "mIU/L", "free_thyroxine": "ng/dL",
         "hemoglobin": "g/dL", "hematocrit": "%", "red_blood_cell_count": "10^6/µL", "white_blood_cell_count": "10^3/µL",
         "platelet_count": "10^3/µL", "mean_corpuscular_volume": "fL", "mean_corpuscular_hemoglobin": "pg",
         "mean_corpuscular_hemoglobin_concentration": "g/dL", "red_cell_distribution_width_cv": "%", "mean_platelet_volume": "fL",
         "neutrophils_percent": "%", "lymphocytes_percent": "%", "monocytes_percent": "%", "eosinophils_percent": "%",
         "basophils_percent": "%", "band_neutrophils_percent": "%", "international_normalized_ratio": "ratio",
         "prothrombin_time": "s", "activated_partial_thromboplastin_time": "s", "fibrinogen": "mg/dL",
         "arterial_ph": "", "arterial_pco2": "mmHg", "arterial_po2": "mmHg", "base_excess": "mmol/L"}
HEME_TERMS = ("anemia", "thrombocyt", "leukocyt", "leukopenia", "neutropen", "pancytopenia", "polycythemia", "erythrocytosis",
              "thalassemia", "iron_deficiency", "b12", "folate", "hemolysis", "hemolytic", "coagulation", "inr", "dic",
              "hemochromatosis", "myelo", "lymph", "sickle", "gaucher", "immune_thrombocytopenia")


def heme(name):
    return any(t in name for t in HEME_TERMS)


def pretty(name):
    return name.replace("_", " ")


def main():
    stays = json.load(gzip.open(os.path.join(ROOT, "eval", "results", "eicu_demo", "per_stay_v7.json.gz")))
    rng = random.Random(SEED)
    with_heme = sorted(x["stay"] for x in stays if any(heme(t[0]) for t in x["top5"]))
    others = sorted(x["stay"] for x in stays if x["stay"] not in set(with_heme))
    pick = rng.sample(with_heme, 50) + rng.sample(others, 50)
    rng.shuffle(pick)
    by = {x["stay"]: x for x in stays}
    cases = [by[s] for s in pick]

    wb = Workbook()
    bold = Font(bold=True); wrap = Alignment(wrap_text=True, vertical="top")
    fill_in = PatternFill("solid", fgColor="FFF2CC")   # cells the reviewer fills
    fill_hd = PatternFill("solid", fgColor="D9E1F2")

    # ---------------- Instructions
    ws = wb.active; ws.title = "Instructions"
    lines = [
        "Hemoglyph — physician review package v1 (2026-10-27). Please read PHYSICIAN_REVIEW_INSTRUCTIONS.md (Persian + English) first.",
        "",
        "P1_output_review: 100 ICU admission panels (public eICU-CRD demo, de-identified), each with the 5 suggestions of the frozen engine v7.",
        "  For EVERY suggestion fill VERDICT: 1 = reasonable given this panel · 2 = not supported by this panel · 3 = potentially harmful if acted on · 4 = outside my expertise.",
        "  Optional: a short reason (one phrase) for verdicts 2 and 3.",
        "  Then, for each CASE, fill the two summary cells in P1_case_summary: MISSED (an important diagnosis evident from the panel that the engine did not list; write 'none' if none) and OVERALL (1–5).",
        "P2_rule_audit_heme: haematology rules with their cited source. Open the source URL/DOI; label CONCORDANT / DISCORDANT / UNRESOLVABLE.",
        "  For CONCORDANT or DISCORDANT, paste the EXACT sentence from the source that contains the number or criterion, with page/section. A title is not a quote. When in doubt: UNRESOLVABLE.",
        "Rules of the game: judge only from the panel shown (no history is available to the engine either); do not look up cases; do not discuss rows with the first author before returning the file;",
        "  spend at most 3 minutes per case and 5 minutes per rule; return this .xlsx file (not CSV). Fill the yellow cells only.",
        "Blindness: you are not told the clinicians' documented diagnoses or which suggestions count as 'hits'. Your verdicts are analysed as given; nothing is 'resolved' afterwards.",
    ]
    for i, l in enumerate(lines, 1):
        ws.cell(i, 1, l).alignment = wrap
    ws.column_dimensions["A"].width = 150

    # ---------------- P1 panels (reference)
    wp = wb.create_sheet("P1_panels")
    wp.append(["case", "age", "sex", "n analytes", "panel (analyte = value unit; first admission panel)"])
    for c in wp[1]: c.font = bold; c.fill = fill_hd
    for k, x in enumerate(cases, 1):
        panel = "\n".join(f"{pretty(a)} = {x['vals'][a]:g} {UNITS.get(a, '')}".rstrip() for a in sorted(x["labs"]))
        wp.append([k, x["age"], x["sex"], x["n_in"], panel])
        wp.cell(k + 1, 5).alignment = wrap
    wp.column_dimensions["E"].width = 70

    # ---------------- P1 output review
    wo = wb.create_sheet("P1_output_review")
    hdr = ["case", "age", "sex", "panel (compact)", "rank", "engine suggestion", "engine score",
           "VERDICT (1 reasonable / 2 unsupported / 3 potentially harmful / 4 outside expertise)", "reason (optional, one phrase)"]
    wo.append(hdr)
    for c in wo[1]: c.font = bold; c.fill = fill_hd; c.alignment = wrap
    dv = DataValidation(type="list", formula1='"1,2,3,4"', allow_blank=True); wo.add_data_validation(dv)
    r = 2
    for k, x in enumerate(cases, 1):
        compact = "; ".join(f"{pretty(a)} {x['vals'][a]:g}" for a in sorted(x["labs"]))
        for rank, (dx, score) in enumerate(x["top5"], 1):
            wo.append([k, x["age"], x["sex"], compact if rank == 1 else "", rank, pretty(dx), round(score, 3), None, None])
            wo.cell(r, 8).fill = fill_in; wo.cell(r, 9).fill = fill_in; dv.add(wo.cell(r, 8)); wo.cell(r, 4).alignment = wrap
            r += 1
    for col, w in zip("ABCDEFGHI", (6, 5, 8, 60, 5, 38, 8, 22, 30)): wo.column_dimensions[col].width = w
    wo.freeze_panes = "A2"

    # ---------------- P1 case summary
    wc = wb.create_sheet("P1_case_summary")
    wc.append(["case", "MISSED: important diagnosis evident from this panel that the engine did not list ('none' if none)",
               "OVERALL quality of the 5 suggestions for this panel (1 poor … 5 excellent)", "minutes spent"])
    for c in wc[1]: c.font = bold; c.fill = fill_hd; c.alignment = wrap
    dv5 = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True); wc.add_data_validation(dv5)
    for k in range(1, 101):
        wc.append([k, None, None, None])
        for col in (2, 3, 4): wc.cell(k + 1, col).fill = fill_in
        dv5.add(wc.cell(k + 1, 3))
    wc.column_dimensions["B"].width = 70; wc.column_dimensions["C"].width = 30

    # ---------------- P2 haematology rule audit
    wr = wb.create_sheet("P2_rule_audit_heme")
    rows = list(csv.DictReader(open(os.path.join(ROOT, "eval", "source_audit", "sample_200.csv"), encoding="utf-8")))
    heme_rules = [x for x in rows if heme(x["disease_id"] + " " + x["rule_id"])]   # both strata; stratum shown
    wr.append(["#", "rule id", "stratum (A curated anchor / B AI-drafted candidate)", "disease", "rule type", "rule statement (analyte operator threshold unit)", "population", "source id(s)", "source URL(s)",
               "LABEL (CONCORDANT / DISCORDANT / UNRESOLVABLE)", "EXACT quoted sentence from the source (required for C/D) + page/section",
               "if UNRESOLVABLE, reason (403-blocked / landing page / abstract only / generic standard / no threshold found / ambiguous)",
               "clinical note (optional): is the threshold clinically current? "])
    for c in wr[1]: c.font = bold; c.fill = fill_hd; c.alignment = wrap
    dvl = DataValidation(type="list", formula1='"CONCORDANT,DISCORDANT,UNRESOLVABLE"', allow_blank=True); wr.add_data_validation(dvl)
    dvu = DataValidation(type="list", formula1='"403-blocked,landing page,abstract only,generic standard,no threshold found,ambiguous"', allow_blank=True); wr.add_data_validation(dvu)
    for i, x in enumerate(heme_rules, 1):
        wr.append([i, x["rule_id"], x["stratum"], x["disease_id"], x["rule_type"], x["expression"], x["population"], x["source_ids"], x["source_urls"], None, None, None, None])
        for col in (10, 11, 12, 13): wr.cell(i + 1, col).fill = fill_in
        dvl.add(wr.cell(i + 1, 10)); dvu.add(wr.cell(i + 1, 12))
    for col, w in zip("ABCDEFGHIJKLM", (4, 30, 10, 24, 16, 50, 24, 20, 40, 18, 60, 22, 30)): wr.column_dimensions[col].width = w
    wr.freeze_panes = "A2"

    # ---------------- Reviewer
    wv = wb.create_sheet("Reviewer")
    for i, (k, v) in enumerate([("Name", ""), ("Specialty / board certification", ""), ("Affiliation (hospital / university)", ""), ("ORCID", ""), ("Email", ""),
                                ("Relationship to the first author (none / family / colleague / other)", ""), ("Date started", ""), ("Date completed", ""),
                                ("I confirm I completed this review myself, from the panels and sources shown, without AI assistance (yes/no)", "")], 1):
        wv.cell(i, 1, k).font = bold; wv.cell(i, 2, v).fill = fill_in
    wv.column_dimensions["A"].width = 95; wv.column_dimensions["B"].width = 40

    out = os.path.join(H, "Hemoglyph_physician_review_package_v1.xlsx")
    wb.save(out)
    json.dump({"seed": SEED, "cases": pick, "n_heme_rules": len(heme_rules), "heme_rule_ids": [x["rule_id"] for x in heme_rules]},
              open(os.path.join(H, "physician_package_v1_manifest.json"), "w"), indent=1)
    print("saved", out, "| cases", len(cases), "| suggestions", r - 2, "| heme rules", len(heme_rules))


if __name__ == "__main__":
    main()
