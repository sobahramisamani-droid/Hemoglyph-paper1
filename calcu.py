from __future__ import annotations
import os
import json
import math
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from cache_registry import bargozari_registry, shared_object


class CalculationError(ValueError):
    pass


_UNIT_ALIASES: dict[str, str] = {
    "": "1",
    "1": "1",
    "unitless": "1",
    'ratio': "1",
    "%": "%",
    "ph": "[pH]",
    "[ph]": "[pH]",
    "percent": "%",
    "pct": '%',
    '%ofwbc': '%',

    "mg/dl": 'mg/dL',
    "mgdl": 'mg/dL',
    'mmol/l': "mmol/L",
    "meq/l": 'mmol/L',
    'mval/l': 'mmol/L',
    "u/l": 'U/L',
    "ul": "U/L",
    'iu/l': "U/L",
    "tu/l": 'U/L',

    'tul': "U/L", "u/1": "U/L",

    "m[iu]/l": "m[IU]/L",
    "miu/l": "mIU/L",
    "miu/ml": "mIU/mL",
    "m[iu]/ml": 'm[IU]/mL',
    "µiu/ml": "u[IU]/mL",
    "uiu/ml": "u[IU]/mL",
    "u[iu]/ml": "u[IU]/mL",
    "microiu/ml": "u[IU]/mL",
    "miu/l": "m[IU]/L",
    "m[iu]/l": "m[IU]/L",
    "[iu]/ml": "[IU]/mL",
    "iu/ml": "U/mL",
    "tu/ml": "U/mL",

    'uiml': "U/mL", "uimt": "U/mL", "uim1": 'U/mL', "u1ml": "U/mL",

    "ng/ml": "ng/mL",
    "ug/ml": "µg/mL",
    "mcg/ml": 'µg/mL',
    "µg/ml": "µg/mL",
    "pg/ml": "pg/mL",
    "ng/l": 'ng/L',
    "ng/dl": "ng/dL",
    "ug/dl": "µg/dL", "mcg/dl": "µg/dL",
    "ug/l": "µg/L", "mcg/l": "µg/L", "µg/l": "µg/L",

    "g/dl": "g/dL",

    'gid': "g/dL", 'grid': "g/dL", "grdl": "g/dL", "grld": "g/dL",
    "gdi": "g/dL", 'g/d1': "g/dL", "gr/dl": "g/dL",

    "g/l": "g/L",
    "mg/l": "mg/L",
    "mg/24h": "mg/24h",
    "mg/(24.h)": "mg/24h",
    "g/24h": "g/24h",
    "mg/g": 'mg/g',
    "g/g": "g/g",
    "ml/min/{1.73_m2}": "mL/min/1.73m2",
    "ml/min/1.73m2": "mL/min/1.73m2",
    "mmhg": "mmHg",
    "mm[hg]": "mmHg", "torr": "mmHg",   # UCUM mm[Hg] (v6: vital-sign inputs from HL7/FHIR observations)
    "/min": "/min", "1/min": "/min", "bpm": "/min", "beats/min": "beats/min", "breaths/min": "breaths/min", "{beats}/min": "beats/min", "{breaths}/min": "breaths/min",
    "cel": "Cel", "degc": "Cel", "°c": "Cel", "[degf]": "[degF]", "°f": "[degF]", "degf": "[degF]",
    'kpa': "kPa",
    "[arb'u]/ml": "[arb'U]/mL",
    "arb'u/ml": "[arb'U]/mL",
    "umol/l": "µmol/L",
    "µmol/l": "µmol/L",
    "mmol/kg": "mmol/kg",

    "fl": "fL",
    "femtoliter": "fL",
    "femtolitre": 'fL',
    "µm3": "fL",
    'um3': "fL",
    "pg": 'pg',
    "picogram": "pg",
    'pg/cell': "pg",

    "cumm": "1/µL",
    '/cumm': "1/µL",
    "cmm": "1/µL",
    '/cmm': "1/µL",
    "cu.mm": "1/µL",
    'mm3': "1/µL",
    "/mm3": "1/µL",
    "cells/cumm": "1/µL",
    "cells/ul": "1/µL",
    "percumm": '1/µL',
    "1/ul": "1/µL",
    "/ul": "1/µL",
    "/µl": "1/µL",

    "jul": '1/µL', "ful": "1/µL", "iul": "1/µL", "lul": "1/µL",

    "1/µl": "1/µL",

    "10^9/l": '10^9/L',
    "x10^9/l": "10^9/L",
    "10*9/l": '10^9/L',
    "thousand/cumm": "10^9/L",
    "10^3/cumm": "10^9/L",

    'mill/cumm': "10^6/µL",
    'mill/cmm': "10^6/µL",
    "million/cumm": "10^6/µL",
    "million/cmm": "10^6/µL",
    "mil/cumm": "10^6/µL",
    '10^6/cumm': "10^6/µL",
    "10^6/ul": "10^6/µL",

    "106/ul": "10^6/µL", "106/µl": "10^6/µL", "106/cumm": "10^6/µL",

    '10^6/µl': "10^6/µL",
    "10^12/l": "10^12/L",
    "10*12/l": "10^12/L",
    '10*6/l': "10^6/µL", "10*6/ul": '10^6/µL', "10*3/l": '10^9/L',
    "10*3/ul": "10^9/L",
    "10^3/µl": "10^9/L",
    "10^3/ul": "10^9/L",
    "x10^3/µl": "10^9/L", "x10^3/ul": "10^9/L", "x10³/µl": "10^9/L", "10³/µl": "10^9/L", "10³/ul": "10^9/L",
    "x10^9/l": "10^9/L", "x10⁹/l": "10^9/L", "10⁹/l": "10^9/L", "10e9/l": "10^9/L", "10e3/ul": "10^9/L",
    "k/ul": "10^9/L", "k/µl": "10^9/L", "k/mm3": "10^9/L", "k/mm³": "10^9/L", "thou/ul": "10^9/L",
    "thou/µl": "10^9/L", "thousand/ul": "10^9/L", "giga/l": "10^9/L", "g/l{cells}": "10^9/L",
    "x10^6/µl": "10^6/µL", "x10^6/ul": "10^6/µL", "x10⁶/µl": "10^6/µL", "10⁶/µl": "10^6/µL", "10⁶/ul": "10^6/µL",
    "m/ul": "10^6/µL", "m/µl": "10^6/µL", "mil/ul": "10^6/µL", "mil/µl": "10^6/µL", "million/ul": "10^6/µL",
    "x10^12/l": "10^12/L", "x10¹²/l": "10^12/L", "10¹²/l": "10^12/L", "10e12/l": "10^12/L", "tera/l": "10^12/L",
    "cells/mm3": "/µL", "cells/mm³": "/µL", "cell/mm3": "/µL", "/mm3": "/µL", "/mm³": "/µL", "/cmm": "/µL",
    "cells/ul": "/µL", "cells/µl": "/µL", "/ul": "/µL", "per µl": "/µL", "per ul": "/µL",
    "ng/mlfeu": "ng/mL", "ng/ml{feu}": "ng/mL", "mg/lfeu": "mg/L", "µg/mlfeu": "µg/mL", "ug/mlfeu": "µg/mL",
    "ng/mlddu": "ng/mL", "ng/ml{ddu}": "ng/mL", "µg/lfeu": "µg/L", "ug/lfeu": "µg/L",
    "mmol/mol": "mmol/mol", "mmol/molhb": "mmol/mol", "ifcc": "mmol/mol", "%ngsp": "%", "%dcct": "%",
    "ug{feu}/ml": "µg/mL",
    "mg{feu}/l": "mg/L",
    "mg/l feu": "mg/L",
    "ug/ml feu": "µg/mL",


    "lakhs/cumm": "10^5/µL",
    "lakh/cumm": "10^5/µL",
    "lac/cumm": '10^5/µL',
    '10^5/cumm': "10^5/µL",
    '10^5/ul': "10^5/µL",
    '10^5/µl': "10^5/µL",

    "mm/hr": "mm/h",
    "mm/hour": "mm/h",
    "mm/h": "mm/h",
    "103/ul": "10^9/L",
    "103/µl": "10^9/L",
    "10^3/ul": "10^9/L",
    "103/cumm": "10^9/L",
    # FIX P13 support: fold ASCII/mu spellings to canonical mass units.
    "ug/mg": "mg/g",
    "µg/mg": "mg/g",
    "uiu/ml": "µIU/mL",
    "\u03bciu/ml": "µIU/mL",
    "ukat/l": "µkat/L",
    "µkat/l": "µkat/L",
    "mu/l": "mU/L",
}


_CASE_CANONICAL = {
    "MG/DL": "mg/dL", "MMOL/L": "mmol/L", "NG/ML": "ng/mL", "PG/ML": 'pg/mL',
    "U/L": "U/L", 'IU/L': "IU/L", 'G/DL': 'g/dL', "MG/L": "mg/L", "G/L": "g/L",
    "NMOL/L": "nmol/L", "UG/ML": "µg/mL", "IU/ML": "IU/mL", 'G/24H': 'g/24h',
    "FL": "fL", "PG": 'pg', 'MM/H': 'mm/h', 'MM/HR': 'mm/h',
    # time / physiology / misc labels seen on reports (unit audit 2026-10-21)
    "sec": "s", "secs": "s", "seconds": "s", "second": "s",
    "minutes": "min", "minute": "min", "mins": "min",
    "mosm/kg": "mOsm/kg", "mosm/kgh2o": "mOsm/kg", "mosmol/kg": "mOsm/kg", "mosm/l": "mOsm/L",
    "kg/m²": "kg/m2", "kg/m^2": "kg/m2",
    "degc": "Cel", "°c": "Cel", "c": "Cel", "cel": "Cel", "celsius": "Cel", "[degc]": "Cel",
    "degf": "[degF]", "°f": "[degF]", "f": "[degF]", "[degf]": "[degF]", "fahrenheit": "[degF]",
    "bpm": "beats/min", "/min": "/min", "beats/min": "beats/min", "breaths/min": "breaths/min",
    "fraction": "fraction",
    "g/l_cells": "10^9/L", "giga/l": "10^9/L", "billion/l": "10^9/L", "10^9/l": "10^9/L", "10*9/l": "10^9/L", "x10^9/l": "10^9/L", "10e9/l": "10^9/L",
    "tera/l": "10^12/L", "trillion/l": "10^12/L", "10^12/l": "10^12/L", "10*12/l": "10^12/L", "x10^12/l": "10^12/L",
    "k/ul": "10^3/µL", "k/µl": "10^3/µL", "k/pl": "10^3/µL", "thou/ul": "10^3/µL", "10^3/ul": "10^3/µL", "10*3/ul": "10^3/µL", "x10^3/ul": "10^3/µL",
    "m/ul": "10^6/µL", "m/µl": "10^6/µL", "mil/ul": "10^6/µL", "10^6/ul": "10^6/µL", "10*6/ul": "10^6/µL",
    "ui": "U/L", "ui/l": "U/L", "units/l": "U/L", "unit/l": "U/L", "u/i": "U/L",
    "iu/dl": "IU/dL", "u/dl": "U/dL",
    "eu/dl": "EU/dL", "ehrlichunits/dl": "EU/dL", "eu/l": "EU/L",
    "uu/ml": "u[IU]/mL", "µu/ml": "u[IU]/mL", "mu/l": "m[IU]/L", "ulu/mt": "u[IU]/mL",
    "index": "index", "umol/l": "µmol/L", "µmol/l": "µmol/L", "nmol/l": "nmol/L", "pmol/l": "pmol/L",
}


_LEGACY_UNITS = bool(os.environ.get("HG_LEGACY_UNITS"))
_V6_UNIT_KEYS = {"mm[hg]", "torr", "/min", "1/min", "bpm", "{beats}/min", "{breaths}/min", "cel", "degc", "°c", "[degf]", "°f", "degf"}


def normalize_unit(unit: Any) -> Optional[str]:
    if unit is None:
        return None
    if isinstance(unit, (int, float)):
        unit = str(unit)
    text = str(unit).strip()
    if not text:
        return None
    key = text.lower().replace(" ", "").replace("\u200e", "").replace("\u200f", "")
    if _LEGACY_UNITS and key in _V6_UNIT_KEYS:
        # evaluation control arm only (HG_LEGACY_UNITS=1): reproduce the pre-v6 behaviour in which
        # UCUM mm[Hg]/Cel/… were not recognised (arterial pO2/pCO2 silently dropped)
        return text
    if key in _UNIT_ALIASES:
        return _UNIT_ALIASES[key]
    if key in _CASE_CANONICAL:
        return _CASE_CANONICAL[key]
    return _CASE_CANONICAL.get(text.upper().replace(" ", ""), text.strip())


_FEATURE_ANALYTE: dict[str, str] = {
    "fasting_plasma_glucose": "glucose",
    'random_plasma_glucose': "glucose",
    "two_hour_postload_glucose": "glucose",
    "glucose": 'glucose',
    "total_cholesterol": "cholesterol",
    "hdl_cholesterol": "cholesterol",
    "ldl_cholesterol_direct": "cholesterol",
    "ldl_cholesterol_calculated": "cholesterol",
    "non_hdl_cholesterol": "cholesterol",
    "triglycerides": "triglycerides",
    "creatinine": "creatinine",
    "urea": 'urea',
    'blood_urea_nitrogen': "bun",
    "calcium_total": 'calcium',
    'calcium_ionized': "calcium",
    "phosphate_inorganic": "phosphate",
    "magnesium": 'magnesium',
    "bilirubin_total": "bilirubin",
    "bilirubin_direct": "bilirubin",
    'bilirubin_indirect': "bilirubin",
    'lactate': "lactate",
    "uric_acid": "uric_acid",

    "ammonia": "ammonia",
    "homocysteine": "homocysteine",
    "serum_iron": "iron",
    "iron_serum": 'iron',
    "folate_serum": "folate",
    'folate_rbc': "folate",
    "morning_cortisol": "cortisol",
    'cortisol_am': "cortisol",
    "cortisol_pm": "cortisol",
    "cortisol_morning": "cortisol",
    "cortisol_total": "cortisol",
    'cortisol_after_dexamethasone': "cortisol",
    "total_testosterone": "testosterone",
    "free_testosterone": "testosterone",
    "bioavailable_testosterone": "testosterone",
    "estradiol": "estradiol",
    "progesterone": "progesterone",
    "17_hydroxyprogesterone": "17oh_progesterone",
    "dehydroepiandrosterone_sulfate": "dhea_s",
    "dhea_s": 'dhea_s',
    "aldosterone": "aldosterone",
    'plasma_metanephrine': 'metanephrine',
    "plasma_normetanephrine": "normetanephrine",
    "androstenedione": 'androstenedione',
    # peptide hormones / markers reported both in mass and molar SI units
    "parathyroid_hormone": "pth", "pth_intact": "pth", "intact_pth": "pth",
    "intact_parathyroid_hormone": "pth", "parathyroid_hormone_intact": "pth", "pth": "pth",
    "c_peptide": "c_peptide",
    "calcitonin": "calcitonin",
    "insulin_like_growth_factor_1": "igf1", "igf_1": "igf1",
    "adrenocorticotropic_hormone": "acth", "acth": "acth",
    "b_type_natriuretic_peptide": "bnp", "bnp": "bnp",
    "n_terminal_pro_bnp": "nt_probnp", "nt_probnp": "nt_probnp",
    "gastrin": "gastrin",
    "serotonin": "serotonin",
    "5_hydroxyindoleacetic_acid": "hiaa", "urine_5_hiaa": "hiaa",
    "blood_lead": "lead",
    "porphobilinogen": "pbg", "urine_porphobilinogen": "pbg",
    "1_25_dihydroxy_vitamin_d": "vitamin_d_125",
    "vitamin_b1": "thiamine", "thiamine": "thiamine",
    "vitamin_b6": "plp", "pyridoxal_5_phosphate": "plp",
    "vitamin_c": "ascorbate", "ascorbic_acid": "ascorbate",
    "selenium": "selenium", "mercury": "mercury", "arsenic": "arsenic",
    "manganese": "manganese",
}


_ANALYTE_KEYWORDS: Sequence[tuple[str, str]] = (
    ("urea_nitrogen", "bun"), ("bun", "bun"),
    ("glucose", 'glucose'),
    ("triglycerid", "triglycerides"),
    ("cholesterol", "cholesterol"),
    ('creatinine', 'creatinine'),
    ('uric', 'uric_acid'),
    ("bilirubin", "bilirubin"),
    ("lactate", "lactate"),
    ("phosphat", "phosphate"), ("phosphorus", "phosphate"),
    ('magnesium', "magnesium"),
    ("calcium", "calcium"),
    ("urea", "urea"),

    ("normetanephrine", "normetanephrine"),
    ("metanephrine", "metanephrine"),
    ("17_hydroxyprogesterone", '17oh_progesterone'), ("17-oh", "17oh_progesterone"),
    ("androstenedione", "androstenedione"),
    ("homocysteine", "homocysteine"),
    ("ammonia", "ammonia"),
    ("cortisol", "cortisol"),
    ("testosterone", 'testosterone'),
    ("estradiol", "estradiol"),
    ("progesteron", "progesterone"),
    ("folate", "folate"), ('folic', "folate"),
    ("b12", "cobalamin"), ("cobalamin", "cobalamin"),
    ("dhea", "dhea_s"),
    ("aldosterone", "aldosterone"),
    ("serum_iron", 'iron'), ("iron", "iron"),
    ("thyroxine", "thyroxine"), ("free_t4", "thyroxine"), ("total_t4", "thyroxine"), ("_t4", "thyroxine"),
    ("triiodothyronine", "triiodothyronine"), ("free_t3", "triiodothyronine"), ("total_t3", "triiodothyronine"), ("_t3", "triiodothyronine"),
    ("25_hydroxy", "vitamin_d"), ("vitamin_d", "vitamin_d"), ("calcidiol", "vitamin_d"), ("25_oh", "vitamin_d"),
    ("vitamin_a", "vitamin_a"), ("retinol", "vitamin_a"), ("vitamin_e", "vitamin_e"), ("tocopherol", "vitamin_e"),
    ("hemoglobin", "hemoglobin"), ("albumin", "albumin"), ("transferrin", "transferrin"),
    ("copper", "copper"), ("zinc", "zinc"), ("lithium", "lithium"), ("ethanol", "ethanol"), ("alcohol", "ethanol"),
    ("pyruvate", "pyruvate"), ("hydroxybutyrate", "beta_hydroxybutyrate"),
    ("insulin_like", "igf1"), ("proinsulin", "proinsulin"), ("insulin", "insulin"),
    ("immunoglobulin_e", "ige"), ("total_ige", "ige"), ("specific_ige", "ige"),
    ("chorionic_gonadotropin", "hcg"), ("hcg", "hcg"),
    ("prolactin", "prolactin"), ("growth_hormone", "growth_hormone"), ("erythropoietin", "erythropoietin"),
    ("ferritin", "ferritin"), ("fibrinogen", "fibrinogen"), ("histamine", "histamine"),
    ("cobalamin", "cobalamin"), ("vitamin_b12", "vitamin_b12"), ("prostate_specific", "psa"),
    ("myoglobin", "myoglobin"), ("cystatin", "cystatin_c"), ("beta_2_microglobulin", "beta2_microglobulin"),
    ("methylmalonic", "methylmalonic_acid"), ("oxalate", "oxalate"), ("citrate", "citrate"),
    ("bile_acid", "bile_acids"), ("free_fatty", "free_fatty_acids"), ("acetoacetate", "acetoacetate"),
    ("glucagon", "glucagon"), ("leptin", "leptin"), ("adiponectin", "adiponectin"),
    ("carnitine", "carnitine"), ("coenzyme_q10", "coenzyme_q10"), ("riboflavin", "vitamin_b2"),
    ("vitamin_b2", "vitamin_b2"), ("vitamin_k", "vitamin_k"), ("creatine_total", "creatine"),
    ("phenytoin", "phenytoin"), ("valpro", "valproate"), ("carbamazepine", "carbamazepine"), ("digoxin", "digoxin"),
    ("theophylline", "theophylline"), ("methotrexate", "methotrexate"), ("acetaminophen", "acetaminophen"),
    ("paracetamol", "acetaminophen"), ("salicylate", "salicylate"), ("cyclosporin", "cyclosporine"), ("tacrolimus", "tacrolimus"),
)

_MOLAR_MASS: dict[str, float] = {
    "glucose": 180.16,
    "cholesterol": 386.65,
    'triglycerides': 885.4,
    "creatinine": 113.12,
    "urea": 60.06,
    "bun": 28.01,
    'calcium': 40.08,
    "phosphate": 30.97,
    "magnesium": 24.31,
    "bilirubin": 584.66,
    "lactate": 90.08,
    "uric_acid": 168.11,

    "ammonia": 17.03,
    "homocysteine": 135.18,
    "cortisol": 362.46,
    "testosterone": 288.42,
    "estradiol": 272.38,
    "progesterone": 314.47,
    "folate": 441.40,
    "iron": 55.85,
    "dhea_s": 368.49,
    "aldosterone": 360.45,
    "17oh_progesterone": 330.46,
    "cobalamin": 1355.38,
    "metanephrine": 197.23,
    "normetanephrine": 183.20,
    'androstenedione': 286.41,
    "thyroxine": 776.87,        # T4 (free/total)
    "triiodothyronine": 650.97, # T3 (free/total)
    "vitamin_d": 400.64,        # 25-OH-D3 (1 ng/mL = 2.496 nmol/L)
    "vitamin_a": 286.45,
    "vitamin_e": 430.71,
    "hemoglobin": 16114.5,      # per monomer with Fe (g/dL <-> mmol/L, 1 g/dL = 0.6206 mmol/L)
    "albumin": 66500.0,
    "transferrin": 79570.0,
    "copper": 63.55,
    "zinc": 65.38,
    "lithium": 6.94,
    "ethanol": 46.07,
    "pyruvate": 88.06,
    "beta_hydroxybutyrate": 104.1,
    "phenytoin": 252.27,
    "valproate": 144.21,
    "carbamazepine": 236.27,
    "digoxin": 780.94,
    "theophylline": 180.16,
    "methotrexate": 454.44,
    "acetaminophen": 151.16,
    "salicylate": 138.12,
    "cyclosporine": 1202.6,
    "tacrolimus": 804.0,
    # peptide hormones (intact molecule; 1 pmol/L = MW/1000 pg/mL)
    "pth": 9425.0,              # intact PTH 1-84: 1 pmol/L = 9.43 pg/mL
    "c_peptide": 3020.3,        # 1 ng/mL = 0.331 nmol/L
    "calcitonin": 3418.0,       # 1 pg/mL = 0.293 pmol/L
    "igf1": 7649.0,             # 1 ng/mL = 0.131 nmol/L
    "acth": 4541.0,             # 1 pg/mL = 0.220 pmol/L
    "bnp": 3464.0,              # 1 pg/mL = 0.289 pmol/L
    "nt_probnp": 8457.0,        # 1 pg/mL = 0.118 pmol/L
    "gastrin": 2098.0,          # 1 pg/mL = 0.477 pmol/L
    "serotonin": 176.22,
    "hiaa": 191.18,
    "lead": 207.2,              # 1 ug/dL = 0.0483 umol/L
    "pbg": 226.23,
    "vitamin_d_125": 416.64,    # 1,25(OH)2D: 1 pg/mL = 2.4 pmol/L
    "thiamine": 265.35,
    "plp": 247.14,
    "ascorbate": 176.12,
    "selenium": 78.97,
    "mercury": 200.59,
    "arsenic": 74.92,
    "manganese": 54.94,
    "ferritin": 450000.0,       # 1 pmol/L = 0.45 ng/mL
    "fibrinogen": 340000.0,     # 1 umol/L = 34 mg/dL
    "histamine": 111.15,
    "insulin": 5808.0,          # see _ANALYTE_PAIR_FACTORS for IU-based insulin units
    "proinsulin": 9390.0,
    "glucagon": 3485.0,
    "leptin": 16000.0,
    "adiponectin": 30000.0,
    "myoglobin": 17000.0,
    "vitamin_b2": 376.37,
    "vitamin_k": 450.7,
    "coenzyme_q10": 863.3,
    "carnitine": 161.2,
    "oxalate": 90.03,
    "citrate": 192.12,
    "bile_acids": 500.0,        # mixed conjugated bile acids, approximate
    "free_fatty_acids": 280.0,  # approximate mean
    "acetoacetate": 102.09,
    "methylmalonic_acid": 118.09,
    "creatine": 131.13,
    "cystatin_c": 13343.0,
    "beta2_microglobulin": 11800.0,
    "myoglobin_urine": 17000.0,
}

# Analyte-specific non-molar conversions (IU-defined units). Key: (analyte, source, target).
_ANALYTE_PAIR_FACTORS: dict[tuple[str, str, str], float] = {
    ("insulin", "pmol/L", "u[IU]/mL"): 1.0 / 6.945, ("insulin", "u[IU]/mL", "pmol/L"): 6.945,
    ("insulin", "pmol/L", "mIU/L"): 1.0 / 6.945, ("insulin", "mIU/L", "pmol/L"): 6.945,
    ("insulin", "mIU/L", "u[IU]/mL"): 1.0, ("insulin", "u[IU]/mL", "mIU/L"): 1.0,
    ("insulin", "pmol/L", "µIU/mL"): 1.0 / 6.945, ("insulin", "µIU/mL", "pmol/L"): 6.945,
    ("insulin", "mIU/L", "µIU/mL"): 1.0, ("insulin", "µIU/mL", "mIU/L"): 1.0,
    ("insulin", "u[IU]/mL", "µIU/mL"): 1.0, ("insulin", "µIU/mL", "u[IU]/mL"): 1.0,
    ("ige", "mg/dL", "U/mL"): 10000.0 / 2.4, ("ige", "U/mL", "mg/dL"): 2.4 / 10000.0,
    ("ige", "ng/mL", "U/mL"): 1.0 / 2.4, ("ige", "U/mL", "ng/mL"): 2.4,
    ("ige", "µg/L", "U/mL"): 1.0 / 2.4, ("ige", "U/mL", "µg/L"): 2.4,
    ("ige", "kIU/L", "U/mL"): 1.0, ("ige", "U/mL", "kIU/L"): 1.0, ("ige", "k[IU]/L", "U/mL"): 1.0, ("ige", "U/mL", "k[IU]/L"): 1.0,
    ("ige", "mg/dL", "IU/mL"): 10000.0 / 2.4, ("ige", "IU/mL", "mg/dL"): 2.4 / 10000.0,  # 1 IU IgE = 2.4 ng
    ("ige", "ng/mL", "IU/mL"): 1.0 / 2.4, ("ige", "IU/mL", "ng/mL"): 2.4,
    ("ige", "µg/L", "IU/mL"): 1.0 / 2.4, ("ige", "IU/mL", "µg/L"): 2.4,
    ("ige", "kIU/L", "IU/mL"): 1.0, ("ige", "IU/mL", "kIU/L"): 1.0,
    ("hcg", "ng/mL", "mIU/mL"): 9.3, ("hcg", "mIU/mL", "ng/mL"): 1.0 / 9.3,                # WHO 4th IS approx.
    ("vitamin_d", "ng/mL", "IU/L"): 1.0, ("prolactin", "ng/mL", "mIU/L"): 21.2, ("prolactin", "mIU/L", "ng/mL"): 1.0 / 21.2,  # WHO 3rd IS 84/500
    ("prolactin", "µg/L", "mIU/L"): 21.2, ("prolactin", "mIU/L", "µg/L"): 1.0 / 21.2,
    ("growth_hormone", "ng/mL", "mIU/L"): 3.0, ("growth_hormone", "mIU/L", "ng/mL"): 1.0 / 3.0,  # WHO 98/574
    ("growth_hormone", "µg/L", "mIU/L"): 3.0, ("growth_hormone", "mIU/L", "µg/L"): 1.0 / 3.0,
    ("erythropoietin", "mIU/mL", "IU/L"): 1.0, ("erythropoietin", "IU/L", "mIU/mL"): 1.0,
    ("cortisol", "µg/dL", "nmol/L"): 27.59, ("cortisol", "nmol/L", "µg/dL"): 1.0 / 27.59,
    ("ferritin", "ng/mL", "pmol/L"): 2.247, ("ferritin", "pmol/L", "ng/mL"): 1.0 / 2.247,
    ("fibrinogen", "mg/dL", "µmol/L"): 1.0 / 34.0, ("fibrinogen", "µmol/L", "mg/dL"): 34.0,
    ("fibrinogen", "g/L", "µmol/L"): 100.0 / 34.0, ("fibrinogen", "µmol/L", "g/L"): 0.34,
    ("vitamin_b12", "pg/mL", "pmol/L"): 0.7378, ("vitamin_b12", "pmol/L", "pg/mL"): 1.3554,
    ("psa", "ng/mL", "µg/L"): 1.0,
}


_MASS_PREFIX = {"": 1.0, 'm': 1e-3, "µ": 1e-6, "u": 1e-6,
                "n": 1e-9, 'p': 1e-12, 'k': 1e3}
_MOLE_PREFIX = {"": 1.0, 'm': 1e-3, "µ": 1e-6, "u": 1e-6,
                "n": 1e-9, "p": 1e-12}
_VOLUME_L = {'l': 1.0, 'dl': 0.1, 'ml': 1e-3, "µl": 1e-6, "ul": 1e-6}


def _molar_scale(s: str, t: str, mass: float) -> Optional[float]:
    def split(u: str) -> Optional[tuple[str, float]]:
        # Analysers emit U+03BC (Greek mu) and U+00B5 (micro sign)
        # interchangeably; fold them before any unit lookup.
        u = str(u).strip().lower().replace(" ", '').replace("\u03bc", "µ")
        if "/" not in u:
            return None
        num, den = u.split("/", 1)
        if num.endswith("g") and den.endswith("l"):
            g = _MASS_PREFIX.get(num[:-1])
            vol = _VOLUME_L.get(den)
            if g is None or vol is None:
                return None
            return ("mass", g / vol)
        if num.endswith('mol') and den.endswith('l'):
            m = _MOLE_PREFIX.get(num[:-3])
            vol = _VOLUME_L.get(den)
            if m is None or vol is None:
                return None
            return ("molar", m / vol)
        return None

    a, b = split(s), split(t)
    if not a or not b:
        return None
    if a[0] == b[0]:
        # same dimension (mass->mass or molar->molar): pure prefix/volume rescale
        return a[1] / b[1]
    if not mass:
        return None
    if a[0] == 'mass':
        return a[1] / (mass * b[1])
    return (mass * a[1]) / b[1]


def _analyte_for(feature_id: Optional[str]) -> Optional[str]:
    if not feature_id:
        return None
    fid = str(feature_id).casefold()
    if fid in _FEATURE_ANALYTE:
        return _FEATURE_ANALYTE[fid]
    for keyword, analyte in _ANALYTE_KEYWORDS:
        if keyword in fid:
            return analyte
    return None


_STATIC_FACTORS: dict[tuple[str, str], float] = {
    ("/µL", "10^9/L"): 0.001, ("10^9/L", "/µL"): 1000.0,
    ("/µL", "10^6/µL"): 1e-6, ("10^6/µL", "/µL"): 1e6,
    ("10^6/µL", "10^12/L"): 1.0, ("10^12/L", "10^6/µL"): 1.0,
    ("10^9/L", "10^3/µL"): 1.0, ("10^3/µL", "10^9/L"): 1.0,
    ("ng/mL", "µg/L"): 1.0, ("µg/L", "ng/mL"): 1.0,
    ("pg/mL", "ng/L"): 1.0, ("ng/L", "pg/mL"): 1.0,
    ("ng/dL", "ng/mL"): 0.01, ("ng/mL", "ng/dL"): 100.0,
    ("ng/dL", "pg/mL"): 10.0, ("pg/mL", "ng/dL"): 0.1,
    ("µg/dL", "ng/mL"): 10.0, ("ng/mL", "µg/dL"): 0.1,
    ("mg/dL", "µg/mL"): 10.0, ("µg/mL", "mg/dL"): 0.1,
    ("mg/L", "µg/mL"): 1.0, ("µg/mL", "mg/L"): 1.0,
    ("µg/mL", "ng/mL"): 1000.0, ("ng/mL", "µg/mL"): 0.001,
    ('g/dL', "g/L"): 10.0,
    # anthropometrics (audit 2026-10-21)
    ("kg", "lb"): 2.2046226218, ("lb", "kg"): 0.45359237, ("kg", "lbs"): 2.2046226218, ("lbs", "kg"): 0.45359237,
    ("cm", "in"): 0.3937007874, ("in", "cm"): 2.54, ("cm", "m"): 0.01, ("m", "cm"): 100.0,
    # urine albumin/protein : creatinine — "ratio" means g/g (mg/mg); mg/g = 1e-3 of that
    ("mg/g", "g/g"): 0.001, ("g/g", "mg/g"): 1000.0, ("mg/g", "1"): 0.001, ("1", "mg/g"): 1000.0,
    ("mg/mmol", "g/g"): 0.00884956, ("g/g", "mg/mmol"): 113.0,
    ("g/L", "g/dL"): 0.1,
    ('mg/dL', 'mg/L'): 10.0,
    ('mg/L', "mg/dL"): 0.1,
    ('µg/dL', 'µg/L'): 10.0,
    ('µg/L', 'µg/dL'): 0.1,
    ('g/dL', 'mg/dL'): 1000.0,
    ('mg/dL', 'g/dL'): 0.001,
    ('mg/dL', 'µg/dL'): 1000.0,
    ('µg/dL', 'mg/dL'): 0.001,
    ('10^3/µL', '10^9/L'): 1.0,
    ('10^9/L', '10^3/µL'): 1.0,
    ("g/24h", "mg/24h"): 1000.0,
    ("mg/24h", "g/24h"): 0.001,
    ("mmHg", "kPa"): 0.13332,
    ("kPa", "mmHg"): 7.50062,
    # unit audit 2026-10-21 -----------------------------------------------
    ("fraction", "%"): 100.0, ("%", "fraction"): 0.01,
    ("IU/dL", "%"): 1.0, ("%", "IU/dL"): 1.0,       # coagulation factor / vWF activity
    ("U/dL", "%"): 1.0, ("%", "U/dL"): 1.0,
    ("EU/dL", "mg/dL"): 1.0, ("mg/dL", "EU/dL"): 1.0,  # urobilinogen Ehrlich unit ~ 1 mg/dL
    ("EU/L", "mg/dL"): 0.1, ("mg/dL", "EU/L"): 10.0,
    ("10^12/L", "10^6/µL"): 1.0, ("10^9/L", "10^9/L"): 1.0,
    ("10^9/L", "10*9/L"): 1.0, ("10*9/L", "10^9/L"): 1.0,
    ("10^3/µL", "10*3/uL"): 1.0, ("10*3/uL", "10^3/µL"): 1.0, ("10^9/L", "10*3/uL"): 1.0, ("10*3/uL", "10^9/L"): 1.0,
    ("10^12/L", "10*6/uL"): 1.0, ("10*6/uL", "10^12/L"): 1.0, ("10^6/µL", "10*6/uL"): 1.0, ("10*6/uL", "10^6/µL"): 1.0,
    ("/min", "beats/min"): 1.0, ("/min", "breaths/min"): 1.0, ("beats/min", "/min"): 1.0, ("breaths/min", "/min"): 1.0,
    ("beats/min", "breaths/min"): 1.0, ("breaths/min", "beats/min"): 1.0,
    ("mOsm/kg", "mOsm/L"): 1.0, ("mOsm/L", "mOsm/kg"): 1.0,
    ("s", "min"): 1.0 / 60.0, ("min", "s"): 60.0,
    ("index", "1"): 1.0, ("1", "index"): 1.0, ("Index", "index"): 1.0,
    ("%", "g/dL"): 1.0, ("g/dL", "%"): 1.0,          # MCHC legacy % == g/dL

    ("1/µL", "10^9/L"): 0.001,
    ("10^9/L", "1/µL"): 1000.0,
    ("1/µL", "10^6/L"): 1.0,
    ("10^6/L", "1/µL"): 1.0,
    ('10^5/µL', "10^9/L"): 100.0,
    ("10^9/L", "10^5/µL"): 0.01,
    ("1/µL", "10^6/µL"): 1e-6,
    ("10^6/µL", "1/µL"): 1e6,
    ("10^6/µL", "10^12/L"): 1.0,
    ("10^12/L", "10^6/µL"): 1.0,
    # FIX P13 support: same-dimension mass-prefix conversions.
    ("g/L", "mg/dL"): 100.0,
    ("mg/dL", "g/L"): 0.01,
    ("mg/L", "µg/L"): 1000.0,
    ("µg/L", "mg/L"): 0.001,
    ("µg/L", "ng/mL"): 1.0,
    ("ng/mL", "µg/L"): 1.0,
    ("ng/mL", "µg/dL"): 0.1,
    ("µg/dL", "ng/mL"): 10.0,
    ("pg/mL", "ng/mL"): 0.001,
    ("ng/mL", "pg/mL"): 1000.0,
    ("pg/mL", "ng/L"): 1.0,
    ("ng/L", "pg/mL"): 1.0,
    ("µg/mL", "ng/mL"): 1000.0,
    ("ng/mL", "µg/mL"): 0.001,
    ("µg/mL", "mg/L"): 1.0,
    ("mg/L", "µg/mL"): 1.0,
    ("mg/L", "ng/mL"): 1000.0,
    ("ng/mL", "mg/L"): 0.001,
    ("ng/dL", "ng/mL"): 0.01,
    ("ng/mL", "ng/dL"): 100.0,
    ("u[IU]/mL", "m[IU]/L"): 1.0,
    ("m[IU]/L", "u[IU]/mL"): 1.0,
    ("u[IU]/mL", "mIU/L"): 1.0,
    ("mIU/L", "u[IU]/mL"): 1.0,
    ("µIU/mL", "u[IU]/mL"): 1.0,
    ("u[IU]/mL", "µIU/mL"): 1.0,
    ("µIU/mL", "m[IU]/L"): 1.0,
    ("m[IU]/L", "µIU/mL"): 1.0,
    ("µIU/mL", "mIU/L"): 1.0,
    ("mIU/L", "µIU/mL"): 1.0,
    ("g/g", "mg/g"): 1000.0,
    ("mg/g", "g/g"): 0.001,
    ("mg/mmol", "mg/g"): 8.84,
    ("mg/g", "mg/mmol"): 0.1131,
    ("L/L", "%"): 100.0,
    ("%","L/L"): 0.01,
    ("U/L", "µkat/L"): 0.01667,
    ("µkat/L", "U/L"): 59.988,
    ("µIU/mL", "mIU/L"): 1.0,
    ("mIU/L", "µIU/mL"): 1.0,
    ("mU/L", "µIU/mL"): 1.0,
    ("µIU/mL", "mU/L"): 1.0,
    ("mIU/mL", "µIU/mL"): 1000.0,
    ("µIU/mL", "mIU/mL"): 0.001,
}

_EQUIV_MONOVALENT = {"mmol/L", "mEq/L", "mmol/l", "meq/l", "mval/l"}


def _factor(source: str, target: str, feature_id: Optional[str] = None) -> Optional[float]:
    s, t = source, target
    if s == t:
        return 1.0

    if s in _EQUIV_MONOVALENT and t in _EQUIV_MONOVALENT:
        return 1.0

    if s in ("1", "[pH]", "pH", "") and t in ("1", "[pH]", "pH", ""):
        return 1.0

    if s in ("U/mL", "[arb'U]/mL", "[IU]/mL") and t in ("U/mL", "[arb'U]/mL", "[IU]/mL"):
        return 1.0

    f = _STATIC_FACTORS.get((s, t))
    if f is not None:
        return f

    analyte = _analyte_for(feature_id) or ""
    f = _ANALYTE_PAIR_FACTORS.get((analyte, s, t))
    if f is not None:
        return f
    mass = _MOLAR_MASS.get(analyte)
    f = _molar_scale(s, t, mass or 0.0)
    if f is not None:
        return f

    return _STATIC_FACTORS.get((s, t))


def convert_unit(value: Any, source: Optional[str], target: Optional[str],
                 feature_id: Optional[str] = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CalculationError(f"Non-numeric value for {feature_id or 'feature'}: {exc}") from exc
    s = normalize_unit(source)
    t = normalize_unit(target)
    if s is None or t is None:
        raise CalculationError(
            f"Missing unit for {feature_id or 'feature'} (source={source!r}, target={target!r}).")
    if s == t:
        return number
    # HbA1c IFCC (mmol/mol) <-> NGSP (%) is affine, not proportional:
    # NGSP% = 0.09148 * IFCC + 2.152  (Hoelzel et al., Clin Chem 2004)
    if {s, t} == {"mmol/mol", "%"}:
        return (0.09148 * number + 2.152) if t == "%" else ((number - 2.152) / 0.09148)
    # Temperature scales are affine.
    if {s, t} == {"Cel", "[degF]"}:
        return (number - 32.0) * 5.0 / 9.0 if t == "Cel" else number * 9.0 / 5.0 + 32.0
    if {s, t} == {"Cel", "K"}:
        return number - 273.15 if t == "Cel" else number + 273.15
    factor = _factor(s, t, feature_id)
    if factor is None:
        raise CalculationError(f"Cannot convert {s!r} to {t!r} for {feature_id or 'feature'}.")
    return number * factor


@dataclass
class PatientContext:
    age_years: Optional[float] = None
    sex_at_birth: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    pregnant: Optional[bool] = None
    pregnancy_trimester: Optional[int] = None
    fasting: Optional[bool] = None
    smoking: Optional[bool] = None
    physical_activity: Optional[bool] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    family_history_dm: Optional[bool] = None
    family_history_cad: Optional[bool] = None
    family_history_htn: Optional[bool] = None
    sleep_hours: Optional[float] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def normalized_jensiat(self) -> Optional[str]:
        aliases = {"male": 'male', "m": 'male', "man": "male", '1': "male",
                   "female": "female", "f": "female", "woman": 'female', "0": "female",
                   "مرد": "male", "زن": "female"}
        if self.sex_at_birth is None:
            return None
        return aliases.get(str(self.sex_at_birth).strip().lower())


def _number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        n = float(str(value).replace("٫", '.').replace(",", "."))
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


@dataclass
class MoshtaghRecord:
    value: Any = None
    unit: Optional[str] = None
    formula_id: Optional[str] = None
    formula: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class CalculationReport:
    results: dict[str, MoshtaghRecord] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'results': {
                k: (asdict(v) if is_dataclass(v) else dict(v))
                for k, v in self.results.items()
            },
            'errors': list(self.errors)
        }


class DerivedFeatureEngine:

    def __init__(self, registry_path: str | Path, *, require_confirmed: bool = True):
        self.registry_path = Path(registry_path)
        self.require_confirmed = require_confirmed


        self.payload = bargozari_registry(self.registry_path) or {"features": {}}
        self.features: dict[str, dict[str, Any]] = self.payload.get("features", {})

    @classmethod
    def shared(cls, registry_path: str | Path, *,
               require_confirmed: bool = True) -> 'DerivedFeatureEngine':
        p = Path(registry_path)
        return shared_object(
            f"derived_engine::{p.resolve()}::{require_confirmed}",
            lambda: cls(p, require_confirmed=require_confirmed),
        )

    def unit(self, feature_id: str) -> Optional[str]:
        meta = self.features.get(feature_id, {})
        return normalize_unit((meta.get('units') or {}).get('canonical'))


    def compute(self, observations: Mapping[str, Mapping[str, Any]],
                patient: PatientContext | Mapping[str, Any]) -> CalculationReport:
        if isinstance(patient, Mapping) and not isinstance(patient, PatientContext):
            fields = set(PatientContext.__dataclass_fields__)
            patient = PatientContext(
                **{k: v for k, v in patient.items() if k in fields},
                extra={k: v for k, v in patient.items() if k not in fields}
            )
        report = CalculationReport()
        inputs = {fid: record for fid, record in observations.items()
                  if self._confirmed(record)}

        # Pre-analytical validation gates
        self._check_edta_contamination(inputs, report)
        self._check_pseudohyponatremia(inputs, report)
        self._check_in_vitro_hemolysis(inputs, report)

        # Core renal / metabolic & anthropometric
        self._mohasebe_bsa(patient, report)
        self._mohasebe_urea_bun_conversion(inputs, report)
        self._mohasebe_egfr(inputs, patient, report)
        self._mohasebe_egfr_cystatin(inputs, patient, report)
        self._mohasebe_egfr_combined(inputs, patient, report)
        self._mohasebe_bmi(inputs, patient, report)
        self._mohasebe_bun_cr_ratio(inputs, report)
        # Lipids
        self._mohasebe_ldl(inputs, report)
        self._mohasebe_non_hdl(inputs, report)
        self._mohasebe_lipid_ratios(inputs, report)
        self._mohasebe_atherogenic_index(inputs, report)
        # Proteins / liver (globulin first so the A/G ratio can use it)
        self._mohasebe_globulin(inputs, report)
        self._mohasebe_a_g_ratio(inputs, report)
        self._mohasebe_indirect_bilirubin(inputs, report)
        self._mohasebe_corrected_calcium(inputs, report)
        self._mohasebe_corrected_sodium(inputs, report)
        # Acid-base / electrolytes
        self._mohasebe_anion_gap(inputs, report)
        self._mohasebe_corrected_anion_gap(inputs, report)
        self._mohasebe_delta_gap_ratio(inputs, report)
        self._mohasebe_osmolality(inputs, report)
        # Hematology
        self._mohasebe_kappa_lambda(inputs, report)
        self._mohasebe_fib4(inputs, patient, report)
        self._mohasebe_apri(inputs, report)
        self._mohasebe_red_cell_indices(inputs, report)
        self._mohasebe_absolute_neutrophil_tedad(inputs, report)
        self._mohasebe_nlr_plr(inputs, report)
        self._mohasebe_transferrin_saturation(inputs, report)
        self._mohasebe_homa_ir(inputs, report)
        self._mohasebe_de_ritis(inputs, report)
        self._mohasebe_eag(inputs, report)
        self._mohasebe_uric_acid_ratios(inputs, report)
        # Extended coverage (v1.3.1 hardening)
        self._mohasebe_differential_absolute(inputs, report)
        self._mohasebe_reticulocyte_indices(inputs, report)
        self._mohasebe_urine_ratios(inputs, report)
        self._mohasebe_fractional_excretions(inputs, report)
        self._mohasebe_urine_anion_gap(inputs, report)
        self._mohasebe_lipid_extended(inputs, report)
        self._mohasebe_calcium_phosphate_product(inputs, report)
        self._mohasebe_stfr_index(inputs, report)
        self._mohasebe_map(inputs, patient, report)
        self._mohasebe_tyg(inputs, report)
        self._mirror_canonical_ids(report)
        return report

    # Engine output id -> registry feature id consumed by the rule base.
    DERIVED_CANONICAL_ALIASES: dict[str, tuple[str, ...]] = {
        "bmi": ("body_mass_index",),
        "corrected_calcium": ("corrected_calcium_for_serum_albumin",),
        "corrected_sodium": ("corrected_sodium_for_hyperglycemia",),
        "egfr_ckd_epi_cystatin": ("egfr_ckd_epi_cystatin_c", "egfr_cystatin_c"),
        "egfr_ckd_epi_combined": ("egfr_ckd_epi_creatinine_cystatin_c",),
        "homa_ir": ("homeostatic_model_assessment_insulin_resistance",),
        "quicki": ("quicki_quantitative_insulin_sensitivity_index",),
        "neutrophil_to_lymphocyte_ratio": ("neutrophil_to_lymphocyte_ratio_nlr",),
        "platelet_to_lymphocyte_ratio": ("platelet_to_lymphocyte_ratio_plr",),
        "bun_to_creatinine_ratio": ("blood_urea_nitrogen_to_creatinine_ratio",),
        "total_to_hdl_ratio": ("cholesterol_hdl_ratio",),
        "osmolar_gap": ("osmolal_gap", "serum_osmolar_gap", "calculated_serum_osmolal_gap"),
        "corrected_anion_gap": ("serum_anion_gap_unadjusted",),
        "absolute_neutrophil_count": ("neutrophil_count_absolute",),
        "delta_ratio": ("delta_gap_delta_ratio",),
        "absolute_reticulocyte_count": ("reticulocyte_count_absolute",),
    }

    def _mirror_canonical_ids(self, report) -> None:
        for src, targets in self.DERIVED_CANONICAL_ALIASES.items():
            rec = report.results.get(src)
            if rec is None:
                continue
            for tgt in targets:
                report.results.setdefault(tgt, MoshtaghRecord(
                    value=rec.value, unit=rec.unit, formula_id=rec.formula_id,
                    formula=rec.formula, warnings=list(rec.warnings)))

    # ------------------------------------------------------------------
    # Extended derived metrics
    # ------------------------------------------------------------------
    def _first(self, inputs, ids, unit):
        for fid in ids:
            v = self._to(inputs, fid, unit)
            if v is not None:
                return v
        return None

    def _mohasebe_differential_absolute(self, inputs, report) -> None:
        """Absolute differential counts from WBC x percentage (10^9/L)."""
        wbc = self._to(inputs, "white_blood_cell_count", "10^9/L")
        if wbc is None or wbc <= 0:
            return
        pairs = (
            ("neutrophils_percent", ("neutrophils", "neutrophil_percent"), "neutrophil_count_absolute"),
            ("lymphocytes_percent", ("lymphocytes", "lymphocyte_percent"), "lymphocyte_count_absolute"),
            ("eosinophils_percent", ("eosinophils", "eosinophil_percent"), "eosinophil_count_absolute"),
            ("monocytes_percent", ("monocytes", "monocyte_percent"), "monocyte_count_absolute"),
            ("basophils_percent", ("basophils", "basophil_percent"), "basophil_count_absolute"),
        )
        total_pct = 0.0
        for primary, alts, out in pairs:
            pct = self._first(inputs, (primary,) + alts, "%")
            if pct is None or pct < 0 or pct > 100:
                continue
            total_pct += pct
            if out in inputs:
                continue
            report.results.setdefault(out, MoshtaghRecord(
                value=round(wbc * pct / 100.0, 2), unit="10^9/L", formula_id="abs_diff",
                formula=f"{out} = WBC x {primary} / 100",
                warnings=["Derived from the percentage differential; confirm with the analyser's absolute count."]))
        if total_pct and not (95.0 <= total_pct <= 105.0):
            report.errors.append(
                f"Differential percentages sum to {total_pct:.0f}% (expected ~100%); absolute counts derived from them are unreliable.")

    def _mohasebe_reticulocyte_indices(self, inputs, report) -> None:
        """Corrected reticulocyte count and reticulocyte production index (RPI)."""
        retic_pct = self._first(inputs, ("reticulocytes", "reticulocyte_percent"), "%")
        hct = self._to(inputs, "hematocrit", "%")
        rbc = self._first(inputs, ("red_blood_cell_count",), "10^12/L")
        if retic_pct is None or retic_pct < 0:
            return
        if rbc is not None and rbc > 0 and "absolute_reticulocyte_count" not in inputs:
            report.results.setdefault("absolute_reticulocyte_count", MoshtaghRecord(
                value=round(retic_pct / 100.0 * rbc * 1000.0, 1), unit="10^9/L", formula_id="abs_retic",
                formula="Retic% x RBC (10^12/L) x 1000"))
        if hct is None or hct <= 0:
            return
        corrected = retic_pct * hct / 45.0
        report.results.setdefault("corrected_reticulocyte_count", MoshtaghRecord(
            value=round(corrected, 2), unit="%", formula_id="corrected_retic",
            formula="Retic% x (Hct / 45)"))
        if hct >= 35:
            maturation = 1.0
        elif hct >= 25:
            maturation = 1.5
        elif hct >= 20:
            maturation = 2.0
        else:
            maturation = 2.5
        rpi = corrected / maturation
        report.results.setdefault("reticulocyte_production_index", MoshtaghRecord(
            value=round(rpi, 2), unit="1", formula_id="rpi",
            formula="Corrected retic / maturation factor (1 / 1.5 / 2 / 2.5 by Hct)",
            warnings=["RPI < 2 with anaemia = hypoproliferative; > 3 = adequate marrow response (haemolysis/blood loss)."]))

    def _mohasebe_urine_ratios(self, inputs, report) -> None:
        """UACR (mg/g) and UPCR (mg/g) from spot urine albumin/protein and creatinine."""
        ucr = self._to(inputs, "urine_creatinine", "mg/dL")
        if ucr is None or ucr <= 0:
            return
        ualb = self._first(inputs, ("urine_albumin", "urine_microalbumin"), "mg/L")
        if ualb is not None and ualb >= 0 and "urine_albumin_to_creatinine_ratio" not in inputs:
            # mg/L albumin ; mg/dL creatinine -> mg/g = (ualb/10 mg/dL) / (ucr/1000 g/dL)
            report.results.setdefault("urine_albumin_to_creatinine_ratio", MoshtaghRecord(
                value=round((ualb / 10.0) / (ucr / 1000.0), 1), unit="mg/g", formula_id="uacr",
                formula="Urine albumin (mg/dL) / urine creatinine (g/dL)",
                warnings=["Spot UACR; confirm persistence on 2 of 3 samples over 3 months (KDIGO)."]))
        uprot = self._first(inputs, ("urine_protein_total", "urine_protein"), "mg/dL")
        if uprot is not None and uprot >= 0 and "urine_protein_to_creatinine_ratio" not in inputs:
            report.results.setdefault("urine_protein_to_creatinine_ratio", MoshtaghRecord(
                value=round(uprot / (ucr / 1000.0), 0), unit="mg/g", formula_id="upcr",
                formula="Urine protein (mg/dL) / urine creatinine (g/dL)"))

    def _mohasebe_fractional_excretions(self, inputs, report) -> None:
        pcr = self._to(inputs, "creatinine", "mg/dL")
        ucr = self._to(inputs, "urine_creatinine", "mg/dL")
        if pcr is None or ucr is None or pcr <= 0 or ucr <= 0:
            return
        pna = self._to(inputs, "sodium", "mmol/L")
        una = self._to(inputs, "urine_sodium", "mmol/L")
        if pna and una is not None and pna > 0:
            fena = 100.0 * (una * pcr) / (pna * ucr)
            report.results.setdefault("fractional_excretion_of_sodium", MoshtaghRecord(
                value=round(fena, 2), unit="%", formula_id="fena",
                formula="(UNa x PCr) / (PNa x UCr) x 100",
                warnings=["FENa < 1% prerenal, > 2% intrinsic (ATN); unreliable under diuretics - use FEUrea."]))
        purea = (self._to(inputs, "blood_urea_nitrogen", "mg/dL")
                 or (self._to(inputs, "urea", "mg/dL") or 0) / 2.1428 or None)
        uurea = self._first(inputs, ("urine_urea_nitrogen", "urine_urea"), "mg/dL")
        if purea and uurea is not None and purea > 0:
            feurea = 100.0 * (uurea * pcr) / (purea * ucr)
            report.results.setdefault("fractional_excretion_of_urea", MoshtaghRecord(
                value=round(feurea, 1), unit="%", formula_id="feurea",
                formula="(UUrea x PCr) / (PUrea x UCr) x 100",
                warnings=["FEUrea < 35% prerenal; valid under diuretic therapy."]))

    def _mohasebe_urine_anion_gap(self, inputs, report) -> None:
        una = self._to(inputs, "urine_sodium", "mmol/L")
        uk = self._to(inputs, "urine_potassium", "mmol/L")
        ucl = self._to(inputs, "urine_chloride", "mmol/L")
        if una is None or uk is None or ucl is None:
            return
        uag = una + uk - ucl
        report.results.setdefault("urine_anion_gap", MoshtaghRecord(
            value=round(uag, 1), unit="mmol/L", formula_id="uag", formula="UNa + UK - UCl",
            warnings=["Negative UAG = appropriate renal NH4+ excretion (GI loss); positive = distal RTA."]))

    def _mohasebe_lipid_extended(self, inputs, report) -> None:
        total = self._to(inputs, "total_cholesterol", "mg/dL")
        hdl = self._to(inputs, "hdl_cholesterol", "mg/dL")
        tg = self._to(inputs, "triglycerides", "mg/dL")
        ldl = self._first(inputs, ("ldl_cholesterol_direct", "ldl_cholesterol_calculated"), "mg/dL")
        if ldl is None:
            rec = report.results.get("ldl_cholesterol_calculated")
            ldl = _number(rec.value) if rec else None
        if tg is not None and tg < 400 and "vldl_cholesterol" not in inputs:
            report.results.setdefault("vldl_cholesterol", MoshtaghRecord(
                value=round(tg / 5.0, 1), unit="mg/dL", formula_id="vldl", formula="TG / 5 (TG < 400)"))
        if total is not None and hdl is not None and ldl is not None:
            report.results.setdefault("remnant_cholesterol", MoshtaghRecord(
                value=round(max(total - hdl - ldl, 0.0), 1), unit="mg/dL", formula_id="remnant_c",
                formula="TC - HDL - LDL"))
        if ldl is not None and hdl is not None and hdl > 0:
            report.results.setdefault("ldl_hdl_ratio", MoshtaghRecord(
                value=round(ldl / hdl, 2), unit="1", formula_id="ldl_hdl", formula="LDL / HDL"))

    def _mohasebe_calcium_phosphate_product(self, inputs, report) -> None:
        ca = self._to(inputs, "calcium_total", "mg/dL")
        rec = report.results.get("corrected_calcium")
        if rec is not None and _number(rec.value) is not None:
            ca = _number(rec.value)
        p = self._first(inputs, ("phosphate", "phosphate_inorganic", "phosphorus"), "mg/dL")
        if ca is None or p is None:
            return
        report.results.setdefault("calcium_phosphate_product", MoshtaghRecord(
            value=round(ca * p, 1), unit="mg2/dL2", formula_id="ca_x_p", formula="Ca (corrected) x PO4",
            warnings=["> 55 mg2/dL2 associated with vascular/soft-tissue calcification (CKD-MBD)."]))

    def _mohasebe_stfr_index(self, inputs, report) -> None:
        stfr = self._to(inputs, "soluble_transferrin_receptor", "mg/L")
        ferr = self._to(inputs, "ferritin", "ng/mL")
        if stfr is None or ferr is None or ferr <= 0 or stfr <= 0:
            return
        idx = stfr / math.log10(ferr)
        report.results.setdefault("soluble_transferrin_receptor_to_log_ferritin_index", MoshtaghRecord(
            value=round(idx, 2), unit="1", formula_id="stfr_index", formula="sTfR / log10(ferritin)",
            warnings=["Assay-dependent cut-offs (~>1.5 iron deficiency with ACD when CRP raised, >2.5 otherwise)."]))

    def _mohasebe_map(self, inputs, patient, report) -> None:
        sbp = self._first(inputs, ("systolic_blood_pressure", "systolic_bp"), "mmHg")
        dbp = self._first(inputs, ("diastolic_blood_pressure", "diastolic_bp"), "mmHg")
        if sbp is None:
            sbp = _number(getattr(patient, "systolic_bp", None))
        if dbp is None:
            dbp = _number(getattr(patient, "diastolic_bp", None))
        if sbp is None or dbp is None or sbp <= dbp:
            return
        report.results.setdefault("mean_arterial_pressure", MoshtaghRecord(
            value=round(dbp + (sbp - dbp) / 3.0, 1), unit="mmHg", formula_id="map", formula="DBP + (SBP - DBP)/3"))

    def _mohasebe_tyg(self, inputs, report) -> None:
        fpg = self._first(inputs, ("fasting_plasma_glucose", "glucose"), "mg/dL")
        tg = self._to(inputs, "triglycerides", "mg/dL")
        if fpg is None or tg is None or fpg <= 0 or tg <= 0:
            return
        report.results.setdefault("triglyceride_glucose_index_tyg", MoshtaghRecord(
            value=round(math.log(tg * fpg / 2.0), 2), unit="1", formula_id="tyg",
            formula="ln[TG (mg/dL) x FPG (mg/dL) / 2]",
            warnings=["Scale ln(TG x FPG / 2): insulin resistance cut-offs ~8.5-8.8 (population-dependent); requires fasting sample."]))

    def _confirmed(self, record: Mapping[str, Any]) -> bool:
        if self.require_confirmed:
            return bool(record.get("confirmed", not record.get("requires_confirmation", False)))
        return True

    def _num(self, inputs: Mapping[str, Mapping[str, Any]], feature_id: str):
        record = inputs.get(feature_id)
        if not record:
            return None
        value = _number(record.get('value'))
        if value is None:
            return None
        return (value, normalize_unit(record.get('unit')))

    def _to(self, inputs: Mapping[str, Mapping[str, Any]], feature_id: str,
            target_unit: Optional[str]) -> Optional[float]:
        entry = inputs.get(feature_id)
        if not entry:
            return None
        value = _number(entry.get("value"))
        if value is None:
            return None
        src = normalize_unit(entry.get("unit"))
        tgt = normalize_unit(target_unit)
        if tgt is None:
            tgt = src
        if src is None or src == tgt:
            return value if src is not None or tgt is None else None
        try:
            return convert_unit(value, src, tgt, feature_id)
        except CalculationError:
            return None


    # ==================== PRE-ANALYTICAL VALIDATION GATES ====================

    def _check_edta_contamination(self, inputs: Mapping[str, Mapping[str, Any]], report: CalculationReport) -> None:
        """Pre-analytical validation gate: Detects K2/K3-EDTA phlebotomy carryover artifact.

        When EDTA tubes are drawn before clot/serum tubes or blood is transferred,
        potassium is falsely elevated (often > 6.0 mmol/L) while calcium is strongly
        chelated (often < 6.5 mg/dL) and alkaline phosphatase is inhibited (< 30 U/L).
        Reference: CLSI H3-A6, Tietz Clinical Chemistry, Cornes et al.
        """
        k = self._to(inputs, "potassium", "mmol/L")
        ca = self._to(inputs, "calcium", "mg/dL") or self._to(inputs, "calcium_total", "mg/dL")
        ca_ion = self._to(inputs, "calcium_ionized", "mmol/L")

        if k is None or (ca is None and ca_ion is None):
            return

        is_hypocalcemic = (ca is not None and ca <= 6.5) or (ca_ion is not None and ca_ion <= 0.8)
        is_severe_hypocalcemia = (ca is not None and ca <= 5.5) or (ca_ion is not None and ca_ion <= 0.65)
        is_hyperkalemic = k >= 6.0
        is_extreme_hyperkalemic = k >= 7.0

        if is_hyperkalemic and is_hypocalcemic:
            alp = self._to(inputs, "alkaline_phosphatase", "U/L")
            mg = self._to(inputs, "magnesium", "mg/dL")

            is_definite = is_extreme_hyperkalemic or is_severe_hypocalcemia or (alp is not None and alp < 25.0)
            status_text = "DEFINITE" if is_definite else "SUSPECTED"

            warns = [
                f"CRITICAL PRE-ANALYTICAL ALERT: High potassium ({k:.1f} mmol/L) accompanied by severe hypocalcemia ({ca if ca is not None else ca_ion:.1f}) strongly indicates K2/K3-EDTA tube carryover during phlebotomy (order-of-draw artifact; CLSI H3-A6).",
                "DO NOT initiate emergency medical treatment for hyperkalemia (calcium gluconate, insulin/glucose, emergent dialysis) without immediate verification on a fresh, non-EDTA clot tube and urgent 12-lead ECG assessment.",
            ]
            if alp is not None and alp < 30.0:
                warns.append(f"Markedly depressed alkaline phosphatase ({alp:.1f} U/L) corroborates severe divalent cation chelation by EDTA.")
            if mg is not None and mg < 1.0:
                warns.append(f"Concomitant hypomagnesemia ({mg:.1f} mg/dL) further confirms EDTA chelation artifact.")

            report.results["edta_contamination_alert"] = MoshtaghRecord(
                value=status_text,
                unit="1",
                formula_id="preanalytical_edta_screen",
                formula="K >= 6.0 mmol/L + Ca <= 6.5 mg/dL (CLSI H3-A6)",
                warnings=warns,
            )
            report.errors.append(f"Pre-analytical alert: {status_text} K2/K3-EDTA tube contamination artifact detected.")

    def _check_pseudohyponatremia(self, inputs: Mapping[str, Mapping[str, Any]], report: CalculationReport) -> None:
        """Pre-analytical validation gate: Detects and corrects pseudohyponatremia.

        Indirect ion-selective electrodes (indirect ISE) dilute whole serum under
        the assumption of 93% aqueous fraction. Extreme hypertriglyceridemia (>= 500 mg/dL)
        or hyperproteinemia (>= 8.5 g/dL, e.g. multiple myeloma) expands the non-aqueous
        fraction, causing a falsely low reported sodium despite normal plasma water sodium.
        Reference: Waugh WH 1969, Fortgens & Pillay 2011, Tietz Clinical Chemistry.
        """
        na = self._to(inputs, "sodium", "mmol/L")
        if na is None:
            return

        tg = self._to(inputs, "triglycerides", "mg/dL")
        tp = self._to(inputs, "total_protein", "g/dL") or self._to(inputs, "protein_total", "g/dL")

        has_hypertriglyceridemia = tg is not None and tg >= 500.0
        has_hyperproteinemia = tp is not None and tp >= 8.5

        if not (has_hypertriglyceridemia or has_hyperproteinemia):
            return

        # Calculate correction factors:
        # Delta Na from triglycerides: approx +1.0 mmol/L per 500 mg/dL above 150 mg/dL
        delta_tg = (max(0.0, tg - 150.0) / 500.0) if tg is not None else 0.0

        # Delta Na from protein: approx +1.25 mmol/L per 1.0 g/dL above 7.5 g/dL
        delta_tp = (max(0.0, tp - 7.5) * 1.25) if tp is not None else 0.0

        corrected_na = round(na + delta_tg + delta_tp, 1)

        warns = [
            f"Pre-analytical artifact: Measured sodium ({na:.1f} mmol/L) is spuriously lowered due to non-aqueous volume displacement from hypertriglyceridemia ({tg:.0f} mg/dL)."
            if has_hypertriglyceridemia and not has_hyperproteinemia else
            f"Pre-analytical artifact: Measured sodium ({na:.1f} mmol/L) is spuriously lowered due to non-aqueous volume displacement from hyperproteinemia ({tp:.1f} g/dL)."
            if has_hyperproteinemia and not has_hypertriglyceridemia else
            f"Pre-analytical artifact: Measured sodium ({na:.1f} mmol/L) is spuriously lowered by non-aqueous phase expansion (TG={tg:.0f} mg/dL, TP={tp:.1f} g/dL)."
        ]
        warns.append(
            f"Physiological plasma water sodium is estimated at ~{corrected_na:.1f} mmol/L. "
            "Patient does NOT have true hypoosmolar hyponatremia; fluid restriction or hypertonic saline may induce severe hypernatremia. "
            "Measure sodium via direct-ISE (blood gas analyzer) or direct potentiometry to confirm."
        )

        report.results["pseudohyponatremia_corrected_sodium"] = MoshtaghRecord(
            value=corrected_na,
            unit="mmol/L",
            formula_id="pseudohyponatremia_waugh_tietz",
            formula="Na_meas + (max(0,TG-150)/500) + (max(0,TP-7.5)*1.25)",
            warnings=warns,
        )

    def _check_in_vitro_hemolysis(self, inputs: Mapping[str, Mapping[str, Any]], report: CalculationReport) -> None:
        """Pre-analytical validation gate: Detects in-vitro phlebotomy hemolysis artifact.

        When red blood cells rupture in vitro during difficult venipuncture, potassium,
        LDH, and AST are falsely elevated. Differentiating this from in-vivo hemolysis
        prevents misdiagnosing hemolytic anemia or acute myocardial/tissue necrosis.
        """
        k = self._to(inputs, "potassium", "mmol/L")
        ldh = self._to(inputs, "lactate_dehydrogenase", "U/L")
        if k is None or ldh is None:
            return

        # Elevated K and LDH with normal haptoglobin rules against in-vivo intravascular hemolysis
        if k >= 5.2 and ldh >= 350.0:
            hapto = self._to(inputs, "haptoglobin", "mg/dL")
            if hapto is not None and hapto >= 30.0:
                report.results["in_vitro_hemolysis_alert"] = MoshtaghRecord(
                    value="SUSPECTED",
                    unit="1",
                    formula_id="preanalytical_hemolysis_screen",
                    formula="K >= 5.2 mmol/L + LDH >= 350 U/L + Haptoglobin >= 30 mg/dL",
                    warnings=[
                        f"Elevated potassium ({k:.1f} mmol/L) and LDH ({ldh:.0f} U/L) in the presence of normal haptoglobin ({hapto:.1f} mg/dL) strongly suggests mechanical in-vitro hemolysis during blood collection, rather than true in-vivo hemolysis.",
                        "Inspect specimen for pink/red serum discoloration and repeat collection if clinical correlation is inconsistent."
                    ]
                )

    def _mohasebe_bsa(self, patient: PatientContext, report: CalculationReport) -> None:
        """Computes Body Surface Area (BSA) in m^2 using the Mosteller formula.

        BSA = sqrt(Height(cm) * Weight(kg) / 3600)
        Standard metric for indexing pediatric/adult GFR and precision pharmacotherapy dosing.
        """
        wt = _number(patient.weight_kg)
        ht = _number(patient.height_cm)
        if wt is None or ht is None or wt <= 0 or ht <= 0:
            return

        bsa = round(math.sqrt((ht * wt) / 3600.0), 2)
        report.results["body_surface_area_mosteller"] = MoshtaghRecord(
            value=bsa,
            unit="m2",
            formula_id="mosteller_bsa",
            formula="sqrt(Height(cm) × Weight(kg) / 3600)",
            warnings=["Mosteller Body Surface Area; used for normalizing physiological clearance and chemotherapy dosing."]
        )

    def _mohasebe_egfr(self, inputs, patient, report) -> None:
        fid = "egfr_ckd_epi_creatinine"
        if fid in inputs and _number(inputs[fid].get("value")) is not None:
            report.results[fid] = MoshtaghRecord(
                value=inputs[fid]["value"], unit=self.unit(fid) or "mL/min/1.73m2",
                formula_id="reported", formula="Reported eGFR (not recomputed).",
            )
            return
        cr = self._to(inputs, "creatinine", "mg/dL")
        if cr is None or cr <= 0:
            return
        age = _number(patient.age_years)
        sex = patient.normalized_jensiat()
        if age is None or age <= 0:
            report.errors.append('eGFR omitted: age is required.')
            return

        # Pediatric GFR: Bedside Schwartz Equation (2009 CKiD) for age < 18
        if age < 18:
            height = _number(patient.height_cm)
            weight = _number(patient.weight_kg)

            if height is None or height <= 0:
                report.errors.append(
                    "Pediatric eGFR (age < 18) strictly requires measured patient height (cm) for the Bedside Schwartz equation (KDIGO 2024). "
                    "eGFR calculation was omitted because unmeasured height leads to severe false-normal misclassification in pediatric CKD."
                )
                return

            # Age-stratified k constant according to Schwartz CKiD (2009):
            # - Preterm infants < 1 year: k = 0.33
            # - Full-term infants < 1 year: k = 0.45
            # - Children and adolescents 1 to 17 years: k = 0.413
            k_constant = 0.45 if age < 1.0 else 0.413
            schwartz_egfr = round(k_constant * height / cr, 1)

            warns = [
                f"Pediatric eGFR calculated via Bedside Schwartz 2009 (k={k_constant}, age={age}y; CKiD JASN 2009)."
            ]
            if weight is not None and weight > 0:
                bsa = math.sqrt((height * weight) / 3600.0)
                unindexed_gfr = round(schwartz_egfr * (bsa / 1.73), 1)
                warns.append(f"Unindexed absolute clearance for drug dosing: ~{unindexed_gfr:.1f} mL/min (BSA={bsa:.2f} m2).")
            else:
                warns.append("Patient weight (kg) not provided; weight is recommended to calculate Mosteller BSA for drug clearance dosing.")

            if schwartz_egfr < 60.0:
                warns.append(f"Pediatric eGFR < 60 mL/min/1.73m2 ({schwartz_egfr:.1f}) indicates pediatric renal impairment; consult pediatric nephrology.")

            report.results[fid] = MoshtaghRecord(
                value=schwartz_egfr,
                unit=self.unit(fid) or "mL/min/1.73m2",
                formula_id="bedside_schwartz_2009",
                formula=f"Bedside Schwartz 2009: eGFR = {k_constant} × Height(cm) / SCr(mg/dL)",
                warnings=warns,
            )
            return

        if sex is None:
            report.errors.append('Adult eGFR omitted: sex_at_birth is required.')
            return
        kappa = 0.7 if sex == "female" else 0.9
        alpha = -0.241 if sex == "female" else -0.302
        sexf = 1.012 if sex == "female" else 1.0
        ratio = cr / kappa
        egfr = (142 * _m_pow(min(ratio, 1), alpha) * _m_pow(max(ratio, 1), -1.200)
                * _m_pow(0.9938, age) * sexf)
        report.results[fid] = MoshtaghRecord(
            value=round(egfr, 1), unit=self.unit(fid) or "mL/min/1.73m2",
            formula_id='ckd_epi_2021_creatinine',
            formula="CKD-EPI 2021 creatinine (race-free).",
            warnings=["Derived adult eGFR; confirm with a validated lab report before clinical use."],
        )

    def _mohasebe_bmi(self, inputs, patient, report) -> None:
        fid = "bmi"
        weight = _number(patient.weight_kg)
        height = _number(patient.height_cm)
        if weight is None or height is None or height <= 0:
            return
        bmi = weight / ((height / 100.0) ** 2)
        warns = []
        age = _number(patient.age_years)
        if age is not None and age < 18:
            warns.append("Pediatric BMI: Adult BMI cutoffs do not apply to patients < 18 years. Interpret relative to CDC/WHO age-and-sex-specific percentiles.")
        report.results[fid] = MoshtaghRecord(
            value=round(bmi, 1), unit='kg/m2',
            formula_id="bmi", formula="Weight / height^2",
            warnings=warns
        )


    def _mohasebe_ldl(self, inputs, report) -> None:
        out = "ldl_cholesterol_calculated"
        total = self._to(inputs, "total_cholesterol", "mg/dL")
        hdl = self._to(inputs, "hdl_cholesterol", "mg/dL")
        tg = self._to(inputs, 'triglycerides', 'mg/dL')
        if total is None or hdl is None or tg is None:
            return
        if tg > 800:
            report.errors.append('LDL omitted: triglycerides > 800 mg/dL; use LDL direct or ultracentrifugation.')
            return
        non_hdl = total - hdl
        if tg <= 400 and non_hdl - tg / 5.0 >= 70:
            ldl = non_hdl - (tg / 5.0)
            formula_id, formula = "friedewald", "Friedewald: TC - HDL - TG/5"
            warn = ["Friedewald estimate (valid TG < 400 mg/dL, LDL >= 70)."]
        else:
            # Sampson-NIH equation 2 (JAMA Cardiol 2020) - validated to TG 800 mg/dL and low LDL.
            ldl = (total / 0.948 - hdl / 0.971
                   - (tg / 8.56 + tg * non_hdl / 2140.0 - tg * tg / 16100.0) - 9.44)
            formula_id, formula = "sampson_nih", "Sampson-NIH 2020 LDL equation"
            warn = ["Sampson-NIH estimate used (TG 400-800 mg/dL or LDL < 70); direct LDL preferred when TG > 400."]
        if ldl < 0:
            report.errors.append("Calculated LDL negative - lipid inputs inconsistent; LDL omitted.")
            return
        report.results[out] = MoshtaghRecord(
            value=round(ldl, 1), unit=self.unit(out) or "mg/dL",
            formula_id=formula_id, formula=formula, warnings=warn,
        )

    def _mohasebe_non_hdl(self, inputs, report) -> None:
        out = 'non_hdl_cholesterol'
        total = self._to(inputs, "total_cholesterol", "mg/dL")
        hdl = self._to(inputs, 'hdl_cholesterol', "mg/dL")
        if total is None or hdl is None:
            return
        report.results[out] = MoshtaghRecord(value=round(total - hdl, 1),
                                            unit=self.unit(out) or 'mg/dL',
                                            formula_id="non_hdl", formula="TC - HDL")

    def _mohasebe_a_g_ratio(self, inputs, report) -> None:
        out = "albumin_to_globulin_ratio"
        alb = self._to(inputs, 'albumin', 'g/dL')
        glob = self._to(inputs, "globulin", "g/dL")
        if glob is None:
            rec = report.results.get("globulin")
            glob = _number(rec.value) if rec else None
        if alb is None or glob is None or glob <= 0:
            return
        report.results[out] = MoshtaghRecord(value=round(alb / glob, 2), unit='1',
                                            formula_id="a_g_ratio", formula="Albumin / globulin")

    def _mohasebe_kappa_lambda(self, inputs, report) -> None:
        out = "free_kappa_to_lambda_ratio"
        kappa = (self._num(inputs, 'free_kappa_light_chains')
                 or self._num(inputs, 'serum_free_kappa_light_chains')
                 or self._num(inputs, 'serum_free_light_chain_kappa'))
        lamb = (self._num(inputs, "free_lambda_light_chains")
                or self._num(inputs, "serum_free_lambda_light_chains")
                or self._num(inputs, "serum_free_light_chain_lambda"))
        if not kappa or not lamb:
            return
        if kappa[1] and lamb[1] and kappa[1] != lamb[1]:
            return
        kv, lv = kappa[0], lamb[0]
        if lv <= 0:
            return
        report.results[out] = MoshtaghRecord(value=round(kv / lv, 2), unit="1",
                                            formula_id="kappa_lambda",
                                            formula="Free kappa / free lambda")

    def _mohasebe_fib4(self, inputs, patient, report) -> None:
        out = 'fibrosis_4_index'
        age = _number(patient.age_years)
        if age is None or age < 18:
            return
        ast = self._to(inputs, "aspartate_aminotransferase", "U/L")
        alt = self._to(inputs, "alanine_aminotransferase", "U/L")
        plts = self._to(inputs, "platelet_count", '10^9/L')
        if ast is None or alt is None or plts is None or plts <= 0 or alt <= 0:
            return
        fib = (age * ast) / (plts * math.sqrt(alt))
        report.results[out] = MoshtaghRecord(
            value=round(fib, 2), unit='1', formula_id="fib4",
            formula="FIB-4: age*AST/(platelets*sqrt(ALT))",
            warnings=["FIB-4 is a research index; confirm with a clinician."])

    def _mohasebe_apri(self, inputs, report) -> None:
        out = "ast_to_platelet_ratio_index"
        ast = self._to(inputs, "aspartate_aminotransferase", 'U/L')
        plts = self._to(inputs, "platelet_count", "10^9/L")
        if ast is None or plts is None or plts <= 0:
            return
        apri = (ast / 40.0 * 100.0) / plts
        report.results[out] = MoshtaghRecord(
            value=round(apri, 2), unit="1", formula_id="apri",
            formula="APRI (AST/ULN*100)/platelets; ULN=40",
            warnings=["APRI ULN assumed 40 U/L; confirm local normal range."])


    def _mohasebe_red_cell_indices(self, inputs, report) -> None:
        hb = self._to(inputs, 'hemoglobin', "g/dL")
        hct = self._to(inputs, "hematocrit", "%") or self._to(inputs, "packed_cell_volume", "%")
        rbc = self._to(inputs, 'red_blood_cell_count', "10^6/µL")
        rdw = self._to(inputs, "red_cell_distribution_width_cv", "%") or self._to(inputs, "rdw", "%")
        warn = ["Derived from CBC components; analyzer-reported value takes precedence."]
        if rbc is not None and rbc > 0:
            if hb is not None and 'mean_corpuscular_hemoglobin' not in inputs:
                report.results.setdefault(
                    'mean_corpuscular_hemoglobin',
                    MoshtaghRecord(value=round(hb * 10.0 / rbc, 1),
                                  unit=self.unit("mean_corpuscular_hemoglobin") or "pg",
                                  formula_id='mch',
                                  formula="MCH (pg) = Hb(g/dL)×10 / RBC(10^6/µL)",
                                  warnings=warn))
            if hct is not None and hct > 0 and "mean_corpuscular_volume" not in inputs:
                report.results.setdefault(
                    'mean_corpuscular_volume',
                    MoshtaghRecord(value=round(hct * 10.0 / rbc, 1),
                                  unit=self.unit("mean_corpuscular_volume") or 'fL',
                                  formula_id="mcv",
                                  formula='MCV (fL) = HCT(%)×10 / RBC(10^6/µL)',
                                  warnings=warn))
        if hb is not None and hct is not None and hct > 0 \
                and "mean_corpuscular_hemoglobin_concentration" not in inputs:
            report.results.setdefault(
                "mean_corpuscular_hemoglobin_concentration",
                MoshtaghRecord(value=round(hb * 100.0 / hct, 1),
                              unit=self.unit('mean_corpuscular_hemoglobin_concentration') or "g/dL",
                              formula_id="mchc",
                              formula="MCHC (g/dL) = Hb(g/dL)×100 / HCT(%)",
                              warnings=warn))

        # Mentzer Index: MCV / RBC
        mcv_val = None
        if "mean_corpuscular_volume" in report.results:
            mcv_val = report.results["mean_corpuscular_volume"].value
        elif "mean_corpuscular_volume" in inputs:
            mcv_val = self._to(inputs, "mean_corpuscular_volume", "fL")

        if mcv_val is not None and rbc is not None and rbc > 0:
            mentzer = round(mcv_val / rbc, 2)
            if (hb is not None and hb < 12.0) and mcv_val < 80.0:
                if mentzer < 13.0:
                    m_warn = ["In microcytic anemia, Mentzer < 13 suggests Thalassemia trait; confirm with Hb electrophoresis."]
                else:
                    m_warn = ["In microcytic anemia, Mentzer > 13 suggests Iron deficiency anemia; confirm with ferritin/iron studies."]
            else:
                m_warn = ["Normal red cell indices; Mentzer index is clinically valid only in the presence of microcytic anemia (MCV < 80 fL, low Hb)."]
            report.results.setdefault(
                "mentzer_index_anemia_discrimination",
                MoshtaghRecord(value=mentzer, unit="1", formula_id="mentzer_index",
                              formula="MCV (fL) / RBC (10^6/µL)", warnings=m_warn))

            if rdw is not None and hb is not None and hb > 0:
                gk = round((mcv_val**2 * rdw) / (hb * 100.0), 1)
                if (hb is not None and hb < 12.0) and mcv_val < 80.0:
                    if gk < 72.0:
                        gk_warn = ["In microcytic anemia, Green-King < 72 suggests Thalassemia trait."]
                    else:
                        gk_warn = ["In microcytic anemia, Green-King > 72 suggests Iron deficiency."]
                else:
                    gk_warn = ["Normal red cell parameters; Green-King index is clinically valid only in microcytic anemia."]
                report.results.setdefault(
                    "green_and_king_index",
                    MoshtaghRecord(value=gk, unit="1", formula_id="green_king_index",
                                  formula="(MCV^2 × RDW) / (Hb × 100)", warnings=gk_warn))


    def _mohasebe_absolute_neutrophil_tedad(self, inputs, report) -> None:
        fid = "absolute_neutrophil_count"
        wbc = self._to(inputs, "white_blood_cell_count", '10^9/L')
        neut = self._to(inputs, "neutrophils", "%")
        if wbc is None or neut is None or wbc <= 0 or neut < 0 or fid in inputs:
            return
        report.results[fid] = MoshtaghRecord(
            value=round(wbc * neut / 100.0, 2), unit=self.unit(fid) or "10^9/L",
            formula_id="anc", formula="ANC = WBC × neutrophils% / 100",
            warnings=["Derived differential; confirm with the laboratory report."])

    # ==================== NEW SUPER-ACCURATE DERIVED METRICS ====================

    def _mohasebe_urea_bun_conversion(self, inputs, report) -> None:
        """
        Stoichiometric interconversion between Urea and Blood Urea Nitrogen (BUN).
        Urea (MW 60.06 g/mol) contains two Nitrogen atoms (2 * 14.007 = 28.014 g/mol).
        Conversion factor: 60.06 / 28.014 = 2.1428.
        BUN (mg/dL) = Urea (mg/dL) / 2.1428
        Urea (mg/dL) = BUN (mg/dL) * 2.1428
        """
        urea = self._to(inputs, "urea", "mg/dL") or self._to(inputs, "serum_urea", "mg/dL")
        bun = self._to(inputs, "blood_urea_nitrogen", "mg/dL") or self._to(inputs, "urea_nitrogen", "mg/dL")

        if bun is None and urea is not None:
            derived_bun = round(urea / 2.1428, 2)
            report.results.setdefault(
                "blood_urea_nitrogen",
                MoshtaghRecord(
                    value=derived_bun,
                    unit="mg/dL",
                    formula_id="urea_to_bun",
                    formula="BUN = Urea / 2.1428",
                    warnings=["Stoichiometrically derived from serum urea (MW 60.06 vs N2 28.01)."]
                )
            )
        elif urea is None and bun is not None:
            derived_urea = round(bun * 2.1428, 2)
            report.results.setdefault(
                "urea",
                MoshtaghRecord(
                    value=derived_urea,
                    unit="mg/dL",
                    formula_id="bun_to_urea",
                    formula="Urea = BUN * 2.1428",
                    warnings=["Stoichiometrically derived from Blood Urea Nitrogen."]
                )
            )

    def _mohasebe_bun_cr_ratio(self, inputs, report) -> None:
        bun = self._to(inputs, "blood_urea_nitrogen", "mg/dL") or self._to(inputs, "urea_nitrogen", "mg/dL")
        if bun is None:
            urea = self._to(inputs, "urea", "mg/dL") or self._to(inputs, "serum_urea", "mg/dL")
            if urea is not None:
                bun = urea / 2.1428
        cr = self._to(inputs, "creatinine", "mg/dL")
        if bun is None or cr is None or cr <= 0:
            return
        ratio = bun / cr
        report.results.setdefault("bun_to_creatinine_ratio",
            MoshtaghRecord(value=round(ratio, 1), unit="1", formula_id="bun_cr", formula="BUN/Creatinine"))

    def _mohasebe_indirect_bilirubin(self, inputs, report) -> None:
        tb = self._to(inputs, "total_bilirubin", "mg/dL")
        db = self._to(inputs, "direct_bilirubin", "mg/dL")
        if tb is None or db is None:
            return
        indir = max(0.0, tb - db)
        report.results.setdefault(
            "indirect_bilirubin",
            MoshtaghRecord(
                value=round(indir, 2),
                unit="mg/dL",
                formula_id="indirect_bilirubin",
                formula="Total Bilirubin - Direct Bilirubin"
            )
        )

    def _mohasebe_globulin(self, inputs, report) -> None:
        tp = self._to(inputs, "total_protein", "g/dL")
        alb = self._to(inputs, "albumin", "g/dL")
        if tp is None or alb is None:
            return
        glob = tp - alb
        if glob < 0:
            return
        report.results.setdefault("globulin",
            MoshtaghRecord(value=round(glob, 2), unit="g/dL", formula_id="globulin", formula="Total Protein - Albumin"))

    def _mohasebe_corrected_calcium(self, inputs, report) -> None:
        ca = self._to(inputs, "calcium_total", "mg/dL")
        alb = self._to(inputs, "albumin", "g/dL")
        if ca is None or alb is None:
            return
        # Payne formula: corrected Ca = Ca + 0.8*(4.0 - albumin)
        corr = ca + 0.8 * (4.0 - alb)
        report.results.setdefault("corrected_calcium",
            MoshtaghRecord(value=round(corr, 2), unit="mg/dL", formula_id="payne",
                           formula="Corrected Ca = Ca + 0.8*(4.0 - albumin)",
                           warnings=["Payne correction; use ionized Ca when available."]))

    def _mohasebe_corrected_sodium(self, inputs, report) -> None:
        na = self._to(inputs, "sodium", "mmol/L")
        glu = self._to(inputs, "glucose", "mg/dL") or self._to(inputs, "fasting_plasma_glucose", "mg/dL")
        if na is None or glu is None:
            return
        # Hillier 1999: corrected Na = Na + 1.6*(glucose-100)/100 for glucose>100
        if glu > 100:
            corr = na + 1.6 * (glu - 100) / 100.0
            # For very high glucose >400, factor 2.4 is more accurate
            if glu > 400:
                corr = na + 2.4 * (glu - 100) / 100.0
            report.results.setdefault("corrected_sodium",
                MoshtaghRecord(value=round(corr, 1), unit="mmol/L", formula_id="katz_hillier",
                               formula="Corrected Na for hyperglycemia",
                               warnings=["Corrects pseudohyponatremia due to hyperglycemia."]))

    def _mohasebe_anion_gap(self, inputs, report) -> None:
        na = self._to(inputs, "sodium", "mmol/L")
        cl = self._to(inputs, "chloride", "mmol/L")
        hco3 = self._to(inputs, "bicarbonate", "mmol/L") or self._to(inputs, "carbon_dioxide", "mmol/L")
        if na is None or cl is None or hco3 is None:
            return
        ag = na - (cl + hco3)
        report.results.setdefault("anion_gap",
            MoshtaghRecord(value=round(ag, 1), unit="mmol/L", formula_id="anion_gap",
                           formula="Na - (Cl + HCO3)"))

    def _mohasebe_corrected_anion_gap(self, inputs, report) -> None:
        # Requires anion_gap + albumin
        ag_rec = report.results.get("anion_gap")
        if ag_rec is None:
            # compute on fly if not yet
            na = self._to(inputs, "sodium", "mmol/L")
            cl = self._to(inputs, "chloride", "mmol/L")
            hco3 = self._to(inputs, "bicarbonate", "mmol/L") or self._to(inputs, "carbon_dioxide", "mmol/L")
            if na is None or cl is None or hco3 is None:
                return
            ag = na - (cl + hco3)
        else:
            ag = _number(ag_rec.value)
            if ag is None:
                return
        alb = self._to(inputs, "albumin", "g/dL")
        if alb is None:
            return
        # Figge correction: corrected AG = AG + 0.25*(4.0 - albumin)*10  (albumin in g/dL, factor 2.5 per 1g)
        corr_ag = ag + 2.5 * (4.0 - alb)
        report.results.setdefault("corrected_anion_gap",
            MoshtaghRecord(value=round(corr_ag, 1), unit="mmol/L", formula_id="figge",
                           formula="Corrected AG = AG + 2.5*(4.0 - albumin)"))

    def _mohasebe_delta_gap_ratio(self, inputs, report) -> None:
        ag_rec = report.results.get("anion_gap")
        if ag_rec is None:
            return
        ag = _number(ag_rec.value)
        if ag is None:
            return
        hco3 = self._to(inputs, "bicarbonate", "mmol/L") or self._to(inputs, "carbon_dioxide", "mmol/L")
        if hco3 is None:
            return

        is_hagma = (ag > 12.0 and hco3 < 22.0)
        # Delta gap = (AG - 12) - (24 - HCO3)
        delta_gap = (ag - 12) - (24 - hco3)
        dg_warn = []
        if not is_hagma:
            dg_warn.append("Electrolytes are physiological or do not represent high anion gap metabolic acidosis; Delta gap carries no pathological significance.")
        report.results.setdefault("delta_gap",
            MoshtaghRecord(value=round(delta_gap, 1), unit="mmol/L", formula_id="delta_gap",
                           formula="(AG-12) - (24-HCO3)", warnings=dg_warn))

        # Delta ratio = (AG-12)/(24-HCO3) if denominator !=0
        denom = 24 - hco3
        if abs(denom) > 0.1:
            delta_ratio = round((ag - 12) / denom, 2)
            dr_warn = []
            if not is_hagma:
                dr_warn.append("Delta ratio is clinically interpretable only in high anion gap metabolic acidosis (AG > 12 and HCO3 < 22).")
            else:
                if delta_ratio < 0.4:
                    dr_warn.append("Delta ratio < 0.4: concurrent normal anion gap metabolic acidosis (NAGMA/hyperchloremic acidosis) with HAGMA.")
                elif delta_ratio < 1.0:
                    dr_warn.append("Delta ratio 0.4-1.0: mixed high anion gap and normal anion gap acidosis.")
                elif delta_ratio <= 2.0:
                    dr_warn.append("Delta ratio 1.0-2.0: uncomplicated high anion gap metabolic acidosis (e.g. DKA, lactic acidosis).")
                else:
                    dr_warn.append("Delta ratio > 2.0: concurrent metabolic alkalosis or preexisting respiratory acidosis.")
            report.results.setdefault("delta_ratio",
                MoshtaghRecord(value=delta_ratio, unit="1", formula_id="delta_ratio",
                               formula="(AG-12)/(24-HCO3)", warnings=dr_warn))

    def _mohasebe_osmolality(self, inputs, report) -> None:
        na = self._to(inputs, "sodium", "mmol/L")
        glu = self._to(inputs, "glucose", "mg/dL") or self._to(inputs, "fasting_plasma_glucose", "mg/dL")
        bun = self._to(inputs, "blood_urea_nitrogen", "mg/dL") or self._to(inputs, "urea_nitrogen", "mg/dL")
        if na is None or glu is None or bun is None:
            return
        # Calculated osmolality = 2*Na + Glu/18 + BUN/2.8
        calc_osm = 2 * na + glu / 18.0 + bun / 2.8
        report.results.setdefault("calculated_osmolality",
            MoshtaghRecord(value=round(calc_osm, 1), unit="mOsm/kg", formula_id="calc_osm",
                           formula="2*Na + Glu/18 + BUN/2.8"))
        # Osmolar gap if measured osmolality available
        meas_osm = self._to(inputs, "osmolality", "mOsm/kg") or self._to(inputs, "measured_osmolality", "mOsm/kg")
        if meas_osm is not None:
            gap = meas_osm - calc_osm
            report.results.setdefault("osmolar_gap",
                MoshtaghRecord(value=round(gap, 1), unit="mOsm/kg", formula_id="osm_gap",
                               formula="Measured Osm - Calculated Osm",
                               warnings=["Osmolar gap >10 suggests toxic alcohol."]))

    def _mohasebe_lipid_ratios(self, inputs, report) -> None:
        total = self._to(inputs, "total_cholesterol", "mg/dL")
        hdl = self._to(inputs, "hdl_cholesterol", "mg/dL")
        ldl = self._to(inputs, "ldl_cholesterol", "mg/dL") or self._to(inputs, "ldl_cholesterol_direct", "mg/dL") or self._to(inputs, "ldl_cholesterol_calculated", "mg/dL")
        tg = self._to(inputs, "triglycerides", "mg/dL")
        if total is not None and hdl is not None and hdl > 0:
            report.results.setdefault("total_to_hdl_ratio",
                MoshtaghRecord(value=round(total/hdl, 2), unit="1", formula_id="tc_hdl", formula="TC/HDL"))
        if ldl is not None and hdl is not None and hdl > 0:
            report.results.setdefault("ldl_to_hdl_ratio",
                MoshtaghRecord(value=round(ldl/hdl, 2), unit="1", formula_id="ldl_hdl", formula="LDL/HDL"))
        if tg is not None and hdl is not None and hdl > 0:
            report.results.setdefault("tg_to_hdl_ratio",
                MoshtaghRecord(value=round(tg/hdl, 2), unit="1", formula_id="tg_hdl", formula="TG/HDL"))
        # Remnant cholesterol
        if total is not None and hdl is not None and ldl is not None:
            remnant = total - hdl - ldl
            report.results.setdefault("remnant_cholesterol",
                MoshtaghRecord(value=round(remnant, 1), unit="mg/dL", formula_id="remnant", formula="TC - HDL - LDL"))

    def _mohasebe_atherogenic_index(self, inputs, report) -> None:
        tg = self._to(inputs, "triglycerides", "mmol/L")
        hdl = self._to(inputs, "hdl_cholesterol", "mmol/L")
        if tg is None or hdl is None or hdl <= 0 or tg <= 0:
            # try mg/dL conversion: AIP uses log(TG/HDL) in mmol/L, but can approximate from mg/dL
            tg_mg = self._to(inputs, "triglycerides", "mg/dL")
            hdl_mg = self._to(inputs, "hdl_cholesterol", "mg/dL")
            if tg_mg is None or hdl_mg is None or hdl_mg <= 0 or tg_mg <= 0:
                return
            # convert mg/dL to mmol/L for AIP
            tg = tg_mg * 0.01129
            hdl = hdl_mg * 0.02586
        import math
        aip = math.log10(tg / hdl)
        report.results.setdefault("atherogenic_index_of_plasma",
            MoshtaghRecord(value=round(aip, 3), unit="1", formula_id="aip",
                           formula="log10(TG/HDL) in mmol/L",
                           warnings=["AIP >0.21 high CV risk."]))

    def _mohasebe_nlr_plr(self, inputs, report) -> None:
        wbc = self._to(inputs, "white_blood_cell_count", "10^9/L")
        anc = (self._to(inputs, "neutrophil_count_absolute", "10^9/L")
               or self._to(inputs, "absolute_neutrophil_count", "10^9/L"))
        alc = (self._to(inputs, "lymphocyte_count_absolute", "10^9/L")
               or self._to(inputs, "absolute_lymphocyte_count", "10^9/L"))
        amc = (self._to(inputs, "monocyte_count_absolute", "10^9/L")
               or self._to(inputs, "absolute_monocyte_count", "10^9/L"))

        neut_pct = (self._to(inputs, "neutrophils_percent", "%")
                    or self._to(inputs, "neutrophils", "%"))
        lymph_pct = (self._to(inputs, "lymphocytes_percent", "%")
                     or self._to(inputs, "lymphocytes", "%"))
        mono_pct = (self._to(inputs, "monocytes_percent", "%")
                    or self._to(inputs, "monocytes", "%"))
        plt = self._to(inputs, "platelet_count", "10^9/L")

        if wbc is not None and wbc > 0:
            if anc is None and neut_pct is not None:
                anc = wbc * neut_pct / 100.0
            if alc is None and lymph_pct is not None:
                alc = wbc * lymph_pct / 100.0
            if amc is None and mono_pct is not None:
                amc = wbc * mono_pct / 100.0

        if anc is not None and alc is not None and alc > 0:
            nlr = round(anc / alc, 2)
            nlr_warn = []
            if nlr > 3.0:
                nlr_warn.append("NLR > 3.0 indicates systemic inflammatory response.")
            report.results.setdefault("neutrophil_to_lymphocyte_ratio",
                MoshtaghRecord(value=nlr, unit="1", formula_id="nlr", formula="ANC / ALC", warnings=nlr_warn))

        if plt is not None and alc is not None and alc > 0:
            plr = round(plt / alc, 1)
            report.results.setdefault("platelet_to_lymphocyte_ratio",
                MoshtaghRecord(value=plr, unit="1", formula_id="plr", formula="Platelets / ALC"))

        if alc is not None and amc is not None and amc > 0:
            lmr = round(alc / amc, 2)
            report.results.setdefault("lymphocyte_to_monocyte_ratio",
                MoshtaghRecord(value=lmr, unit="1", formula_id="lmr", formula="ALC / AMC"))
        elif lymph_pct is not None and mono_pct is not None and mono_pct > 0:
            lmr = round(lymph_pct / mono_pct, 2)
            report.results.setdefault("lymphocyte_to_monocyte_ratio",
                MoshtaghRecord(value=lmr, unit="1", formula_id="lmr", formula="Lymph% / Mono%"))

        if plt is not None and anc is not None and alc is not None and alc > 0:
            sii = round(plt * anc / alc, 1)
            report.results.setdefault("systemic_immune_inflammation_index",
                MoshtaghRecord(value=sii, unit="1", formula_id="sii", formula="Platelets × ANC / ALC"))

    def _mohasebe_transferrin_saturation(self, inputs, report) -> None:
        iron = self._to(inputs, "serum_iron", "µg/dL") or self._to(inputs, "iron_serum", "µg/dL")
        tibc = self._to(inputs, "total_iron_binding_capacity", "µg/dL")
        warn: list[str] = []
        if tibc is None:
            trf = self._to(inputs, "transferrin", "mg/dL")
            if trf is not None and trf > 0:
                tibc = trf * 1.389          # µg/dL iron per mg/dL transferrin (2 Fe per 79.6 kDa)
                report.results.setdefault("total_iron_binding_capacity", MoshtaghRecord(
                    value=round(tibc, 0), unit="µg/dL", formula_id="tibc_from_transferrin",
                    formula="TIBC = transferrin (mg/dL) x 1.389",
                    warnings=["Estimated from transferrin; measured TIBC preferred."]))
                warn.append("TIBC estimated from transferrin.")
        if iron is None or tibc is None or tibc <= 0:
            return
        tsat = 100.0 * iron / tibc
        if tsat > 100:
            report.errors.append(f"Transferrin saturation {tsat:.0f}% > 100%: iron/TIBC inputs inconsistent (unit or sample error).")
            return
        report.results.setdefault("transferrin_saturation",
            MoshtaghRecord(value=round(tsat, 1), unit="%", formula_id="tsat", formula="Iron/TIBC*100", warnings=warn))

    def _mohasebe_homa_ir(self, inputs, report) -> None:
        fpg = (self._to(inputs, "fasting_plasma_glucose", "mg/dL")
               or self._to(inputs, "glucose", "mg/dL"))
        insulin = (self._to(inputs, "fasting_serum_insulin", "µIU/mL")
                   or self._to(inputs, "fasting_insulin", "µIU/mL")
                   or self._to(inputs, "insulin_fasting", "µIU/mL")
                   or self._to(inputs, "insulin", "µIU/mL"))
        if fpg is None or insulin is None or fpg <= 0 or insulin <= 0:
            return
        # HOMA-IR = FPG(mg/dL) * Insulin / 405 ; QUICKI = 1/(log FPG + log Insulin)
        homa = round(fpg * insulin / 405.0, 2)
        homa_warn = ["HOMA-IR calculation assumes an 8-12 hour fasting blood specimen; invalid for random/postprandial samples."]
        if homa >= 2.5:
            homa_warn.append("HOMA-IR >= 2.5 indicates significant insulin resistance.")
        report.results.setdefault("homa_ir",
            MoshtaghRecord(value=homa, unit="1", formula_id="homa_ir",
                           formula="FPG(mg/dL) × Insulin(µIU/mL) / 405", warnings=homa_warn))
        try:
            import math
            quicki = round(1.0 / (math.log10(fpg) + math.log10(insulin)), 3)
            q_warn = []
            if quicki < 0.339:
                q_warn.append("QUICKI < 0.339 indicates impaired insulin sensitivity.")
            report.results.setdefault("quicki",
                MoshtaghRecord(value=quicki, unit="1", formula_id="quicki",
                               formula="1 / [log10(FPG) + log10(Insulin)]", warnings=q_warn))
        except Exception:
            pass
        # TyG = Ln(TG*FPG)/2
        tg = self._to(inputs, "triglycerides", "mg/dL")
        if tg is not None and tg > 0 and fpg > 0:
            import math
            tyg = round(math.log(tg * fpg) / 2.0, 2)
            tyg_warn = []
            if tyg >= 4.49:
                tyg_warn.append("TyG index >= 4.49 correlates with insulin resistance and metabolic syndrome.")
            report.results.setdefault("triglyceride_glucose_index",
                MoshtaghRecord(value=tyg, unit="1", formula_id="tyg",
                               formula="Ln[TG(mg/dL) × FPG(mg/dL)] / 2", warnings=tyg_warn))

    def _mohasebe_uric_acid_ratios(self, inputs, report) -> None:
        ua = self._to(inputs, "uric_acid", "mg/dL")
        cr = self._to(inputs, "creatinine", "mg/dL")
        if ua is not None and cr is not None and cr > 0:
            report.results.setdefault("uric_acid_to_creatinine_ratio",
                MoshtaghRecord(value=round(ua/cr, 2), unit="1", formula_id="ua_cr", formula="UA/Cr"))

    def _mohasebe_egfr_cystatin(self, inputs, patient, report) -> None:
        # CKD-EPI cystatin C 2012 if cystatin available
        cys = self._to(inputs, "cystatin_c", "mg/L")
        if cys is None or cys <= 0:
            return
        age = _number(patient.age_years)
        sex = patient.normalized_jensiat()
        if age is None or sex is None or age <= 0:
            return
        # Simplified CKD-EPI cystatin: 133 * min(Scys/0.8,1)^-0.499 * max(Scys/0.8,1)^-1.328 * 0.996^age * (0.932 if female)
        ratio = cys / 0.8
        egfr = 133 * _m_pow(min(ratio, 1), -0.499) * _m_pow(max(ratio, 1), -1.328) * _m_pow(0.996, age)
        if sex == "female":
            egfr *= 0.932
        report.results.setdefault("egfr_ckd_epi_cystatin",
            MoshtaghRecord(value=round(egfr, 1), unit="mL/min/1.73m2",
                           formula_id="ckd_epi_cys", formula="CKD-EPI 2012 cystatin C",
                           warnings=["Derived; confirm with lab."]))

    def _mohasebe_egfr_combined(self, inputs, patient, report) -> None:
        cr = self._to(inputs, "creatinine", "mg/dL")
        cys = self._to(inputs, "cystatin_c", "mg/L")
        if cr is None or cys is None or cr <= 0 or cys <= 0:
            return
        age = _number(patient.age_years)
        sex = patient.normalized_jensiat()
        if age is None or sex is None or age <= 0:
            return
        # CKD-EPI combined 2021: 135 * min(Scr/k,1)^a * max(Scr/k,1)^-0.544 * min(Scys/0.8,1)^-0.323 * max(Scys/0.8,1)^-0.778 * 0.9961^age * sex factor
        k = 0.7 if sex == "female" else 0.9
        a = -0.241 if sex == "female" else -0.302
        scr_ratio = cr / k
        scys_ratio = cys / 0.8
        egfr = 135 * _m_pow(min(scr_ratio, 1), a) * _m_pow(max(scr_ratio, 1), -0.544) * \
               _m_pow(min(scys_ratio, 1), -0.323) * _m_pow(max(scys_ratio, 1), -0.778) * \
               _m_pow(0.9961, age)
        if sex == "female":
            egfr *= 1.012
        report.results.setdefault("egfr_ckd_epi_combined",
            MoshtaghRecord(value=round(egfr, 1), unit="mL/min/1.73m2",
                           formula_id="ckd_epi_combined", formula="CKD-EPI 2021 Cr+Cys",
                           warnings=["Gold standard eGFR when both markers available."]))


    def _mohasebe_de_ritis(self, inputs, report) -> None:
        ast = self._to(inputs, "aspartate_aminotransferase", "U/L")
        alt = self._to(inputs, "alanine_aminotransferase", "U/L")
        if ast is not None and alt is not None and alt > 0:
            ratio = round(ast / alt, 2)
            warn = []
            if ast > 40.0 or alt > 40.0:
                if ratio >= 2.0:
                    warn.append("In the setting of transaminitis, AST/ALT >= 2.0 is suggestive of alcoholic liver disease, ischemic injury, or advanced cirrhosis.")
                elif ratio > 1.0:
                    warn.append("In the setting of transaminitis, AST/ALT > 1.0 may signify progressive hepatic fibrosis or non-alcoholic steatohepatitis (NASH).")
                else:
                    warn.append("In the setting of transaminitis, AST/ALT < 1.0 is characteristic of acute viral hepatitis or uncomplicated hepatic steatosis.")
            else:
                warn.append("Transaminases are within normal physiological limits; De Ritis ratio is of no pathological significance when liver enzymes are normal.")
            report.results.setdefault(
                "ast_to_alt_ratio_de_ritis",
                MoshtaghRecord(value=ratio, unit="1", formula_id="de_ritis",
                              formula="AST(U/L) / ALT(U/L)", warnings=warn))

    def _mohasebe_eag(self, inputs, report) -> None:
        a1c = self._to(inputs, "hemoglobin_a1c", "%")
        if a1c is not None and a1c > 0 and "estimated_average_glucose" not in inputs:
            eag = round(28.7 * a1c - 46.7, 1)
            report.results.setdefault(
                "estimated_average_glucose",
                MoshtaghRecord(value=eag, unit="mg/dL", formula_id="adag_eag",
                              formula="28.7 × HbA1c(%) - 46.7",
                              warnings=["Estimated average glucose based on ADAG/ADA study."]))


def _m_pow(base: float, exponent: float) -> float:
    if base <= 0:
        return 0.0
    return math.pow(base, exponent)

__all__ = [
    "CalculationError", "CalculationReport", "DerivedFeatureEngine",
    "PatientContext", "convert_unit", "normalize_unit",
]
