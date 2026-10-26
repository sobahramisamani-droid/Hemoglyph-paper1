from __future__ import annotations
import json
import logging
import os
import re
import sys
import time
import threading
import traceback
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from datetime import datetime
from functools import wraps

if sys.platform == "win32":
    # Prioritize PySide6 and venv directories before any Anaconda/Spyder in PATH
    try:
        pyside_site = Path(sys.prefix) / "Lib" / "site-packages" / "PySide6"
        if pyside_site.is_dir() and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(pyside_site))
            if (pyside_site / "Qt" / "bin").is_dir():
                os.add_dll_directory(str(pyside_site / "Qt" / "bin"))
    except Exception:
        pass

from PySide6.QtCore import (QAbstractListModel, QModelIndex, QObject, QSettings, qInstallMessageHandler, QtMsgType,
                           Property, Signal, Slot, Qt, QTimer, QUrl)
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from cache_registry import bargozari_registry, prefetch, cache_stats
import license_engine

# Attach to parent console if invoked from Windows cmd.exe/PowerShell
if sys.platform == "win32":
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(0xFFFFFFFF):
            try:
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
            except Exception:
                pass
    except Exception:
        pass

def _top_level_crash_handler(exctype, value, tb):
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    sys.stderr.write(f"\n[HEMOGLYPH STARTUP FATAL ERROR]\n{err_msg}\n")
    try:
        with open("hemoglyph_startup_error.log", "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
            f.write(err_msg)
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"Hemoglyph Startup Error:\n\n{value}\n\nSee hemoglyph_startup_error.log for details.", "Hemoglyph Critical Error", 0x10)
    except Exception:
        pass
    sys.exit(1)

sys.excepthook = _top_level_crash_handler

def _resolve_data_dir() -> Path:
    try:
        user_dir = Path.home() / ".hemoglyph"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    except Exception:
        pass

    appdata = os.getenv("LOCALAPPDATA")
    if appdata:
        try:
            user_dir = Path(appdata) / "Hemoglyph"
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir
        except Exception:
            pass

    import tempfile
    user_dir = Path(tempfile.gettempdir()) / "Hemoglyph"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

_DATA_DIR = _resolve_data_dir()
_LOG_PATH = _DATA_DIR / "hemoglyph.log"

_log_handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
try:
    _log_handlers.append(logging.FileHandler(str(_LOG_PATH), mode="a", encoding="utf-8", delay=True))
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=_log_handlers
)
logger = logging.getLogger("hemoglyph")

def _qt_message_logger(mode, context, message):
    if mode == QtMsgType.QtFatalMsg:
        logger.fatal(f"[Qt Fatal] {message}")
    elif mode == QtMsgType.QtCriticalMsg:
        logger.error(f"[Qt Critical] {message}")
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning(f"[Qt Warning] {message}")
    else:
        logger.info(f"[Qt Info] {message}")

try:
    qInstallMessageHandler(_qt_message_logger)
except Exception:
    pass

def _determine_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    exe_dir = Path(sys.executable).resolve().parent
    if (exe_dir / "qml").exists() or (exe_dir / "hemoglyph.db").exists() or (exe_dir / "HEMOGLYPH_FEATURE_REGISTRY.json.br").exists():
        return exe_dir
    try:
        f_dir = Path(__file__).resolve().parent
        if (f_dir / "qml").exists():
            return f_dir
    except Exception:
        pass
    return exe_dir

ROOT = _determine_root()

def _load_local_env():
    for cand in [ROOT / ".env", Path(sys.executable).resolve().parent / ".env", Path.cwd() / ".env", Path(__file__).resolve().parent / ".env"]:
        if cand.is_file():
            try:
                for line in cand.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
                logger.info(f"Loaded environment variables from: {cand}")
                break
            except Exception as e:
                logger.debug(f"Could not parse {cand}: {e}")

_load_local_env()

def _resolve_registry(name: str) -> Path:
    p = ROOT / name
    if p.exists():
        return p
    p_br = ROOT / (name + ".br")
    if p_br.exists():
        return p_br
    return p

DISEASE_REGISTRY = _resolve_registry("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json")
FEATURE_REGISTRY = _resolve_registry("HEMOGLYPH_FEATURE_REGISTRY.json")
APP_NAME = "HEMOGLYPH"
APP_ORG = "HEMOGLYPH"
APP_VERSION = "1.3.1"

_MAX_FEATURE_OPTIONS = int(os.getenv('HEMOGLYPH_MAX_FEATURE_OPTIONS', "5000"))
_MAX_BROWSE_ROWS = int(os.getenv("HEMOGLYPH_MAX_BROWSE_ROWS", "5000"))
_MAX_MIRROR_ROWS = int(os.getenv("HEMOGLYPH_MAX_MIRROR_ROWS", '5000'))

_CLINICAL_SEARCH_EXPANSIONS: Dict[str, List[str]] = {
    # Fasting Glucose & Glycemic Markers
    "fps": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "fbs": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "fpg": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "fasting sugar": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose"],
    "fasting plasma sugar": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose"],
    "fasting blood sugar": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose"],
    "fasting glucose": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose"],
    "fasting": ["fasting_plasma_glucose", "fasting_serum_insulin", "fasting_c_peptide", "growth_hormone_fasting"],
    "sugar": ["glucose", "fasting_plasma_glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "blood sugar": ["fasting_plasma_glucose", "glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "glucose": ["glucose", "fasting_plasma_glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "a1c": ["hemoglobin_a1c", "fasting_plasma_glucose", "estimated_average_glucose"],
    "hba1c": ["hemoglobin_a1c", "fasting_plasma_glucose", "estimated_average_glucose"],
    "insulin": ["fasting_serum_insulin", "fasting_c_peptide", "homeostatic_model_assessment_insulin_resistance"],

    # Complete Blood Count (CBC) & Hematology
    "cbc": [
        "white_blood_cell_count", "hemoglobin", "hematocrit", "platelet_count",
        "red_blood_cell_count", "mean_corpuscular_volume", "mean_corpuscular_hemoglobin",
        "mean_corpuscular_hemoglobin_concentration", "red_cell_distribution_width_cv",
        "neutrophils_percent", "lymphocytes_percent", "monocytes_percent", "eosinophils_percent", "basophils_percent"
    ],
    "wbc": ["white_blood_cell_count", "neutrophils_percent", "lymphocytes_percent"],
    "rbc": ["red_blood_cell_count", "hemoglobin", "hematocrit", "mean_corpuscular_volume"],
    "hb": ["hemoglobin", "hematocrit", "hemoglobin_a1c"],
    "hgb": ["hemoglobin", "hematocrit", "hemoglobin_a1c"],
    "hct": ["hematocrit", "hemoglobin"],
    "plt": ["platelet_count", "mean_platelet_volume"],
    "platelets": ["platelet_count", "mean_platelet_volume"],
    "diff": ["neutrophils_percent", "lymphocytes_percent", "monocytes_percent", "eosinophils_percent", "basophils_percent"],
    "mcv": ["mean_corpuscular_volume", "mean_corpuscular_hemoglobin", "red_cell_distribution_width_cv"],
    "mch": ["mean_corpuscular_hemoglobin", "mean_corpuscular_hemoglobin_concentration", "mean_corpuscular_volume"],
    "mchc": ["mean_corpuscular_hemoglobin_concentration", "mean_corpuscular_hemoglobin"],
    "rdw": ["red_cell_distribution_width_cv", "mean_corpuscular_volume"],

    # Liver Function Tests (LFT)
    "lft": ["alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase", "total_bilirubin", "direct_bilirubin", "gamma_glutamyl_transferase", "albumin", "total_protein"],
    "liver": ["alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase", "total_bilirubin", "direct_bilirubin", "gamma_glutamyl_transferase", "albumin"],
    "alt": ["alanine_aminotransferase", "aspartate_aminotransferase"],
    "sgpt": ["alanine_aminotransferase", "aspartate_aminotransferase"],
    "ast": ["aspartate_aminotransferase", "alanine_aminotransferase"],
    "sgot": ["aspartate_aminotransferase", "alanine_aminotransferase"],
    "alp": ["alkaline_phosphatase", "gamma_glutamyl_transferase"],
    "alk phos": ["alkaline_phosphatase"],
    "bili": ["total_bilirubin", "direct_bilirubin", "indirect_bilirubin"],
    "bilirubin": ["total_bilirubin", "direct_bilirubin", "indirect_bilirubin"],
    "ggt": ["gamma_glutamyl_transferase", "alkaline_phosphatase"],

    # Renal Function Tests (RFT / KFT)
    "rft": ["creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "uric_acid", "cystatin_c"],
    "kft": ["creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "uric_acid", "cystatin_c"],
    "renal": ["creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "uric_acid", "urine_albumin_to_creatinine_ratio"],
    "kidney": ["creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "uric_acid", "cystatin_c"],
    "cr": ["creatinine", "egfr_ckd_epi_creatinine", "blood_urea_nitrogen"],
    "creat": ["creatinine", "egfr_ckd_epi_creatinine", "blood_urea_nitrogen"],
    "creatinine": ["creatinine", "egfr_ckd_epi_creatinine", "urine_albumin_to_creatinine_ratio"],
    "bun": ["blood_urea_nitrogen", "creatinine"],
    "urea": ["blood_urea_nitrogen", "creatinine"],
    "egfr": ["egfr_ckd_epi_creatinine", "creatinine", "cystatin_c"],
    "gfr": ["egfr_ckd_epi_creatinine", "creatinine", "cystatin_c"],
    "uacr": ["urine_albumin_to_creatinine_ratio", "creatinine"],

    # Lipids & Cardiovascular
    "lipid": ["total_cholesterol", "triglycerides", "hdl_cholesterol", "ldl_cholesterol_calculated", "non_hdl_cholesterol", "vldl_cholesterol"],
    "lipids": ["total_cholesterol", "triglycerides", "hdl_cholesterol", "ldl_cholesterol_calculated", "non_hdl_cholesterol"],
    "chol": ["total_cholesterol", "ldl_cholesterol_calculated", "hdl_cholesterol", "triglycerides"],
    "cholesterol": ["total_cholesterol", "ldl_cholesterol_calculated", "hdl_cholesterol", "triglycerides", "non_hdl_cholesterol"],
    "tg": ["triglycerides", "total_cholesterol", "hdl_cholesterol", "ldl_cholesterol_calculated"],
    "trig": ["triglycerides", "total_cholesterol"],
    "triglycerides": ["triglycerides", "total_cholesterol", "hdl_cholesterol", "ldl_cholesterol_calculated"],
    "hdl": ["hdl_cholesterol", "total_cholesterol", "ldl_cholesterol_calculated"],
    "ldl": ["ldl_cholesterol_calculated", "ldl_cholesterol_direct", "total_cholesterol", "hdl_cholesterol"],
    "vldl": ["vldl_cholesterol", "triglycerides"],

    # Thyroid Panel
    "tsh": ["thyroid_stimulating_hormone", "free_thyroxine", "free_triiodothyronine", "thyroid_peroxidase_antibody"],
    "tft": ["thyroid_stimulating_hormone", "free_thyroxine", "free_triiodothyronine", "total_thyroxine", "total_triiodothyronine"],
    "thyroid": ["thyroid_stimulating_hormone", "free_thyroxine", "free_triiodothyronine", "thyroid_peroxidase_antibody"],
    "t4": ["free_thyroxine", "total_thyroxine", "thyroid_stimulating_hormone"],
    "ft4": ["free_thyroxine", "thyroid_stimulating_hormone"],
    "t3": ["free_triiodothyronine", "total_triiodothyronine", "thyroid_stimulating_hormone"],
    "ft3": ["free_triiodothyronine", "thyroid_stimulating_hormone"],
    "anti tpo": ["thyroid_peroxidase_antibody", "thyroid_stimulating_hormone"],

    # Iron & Anemia
    "iron": ["serum_iron", "ferritin", "total_iron_binding_capacity", "transferrin_saturation"],
    "fe": ["serum_iron", "ferritin", "total_iron_binding_capacity", "transferrin_saturation"],
    "ferritin": ["ferritin", "serum_iron", "total_iron_binding_capacity"],
    "tibc": ["total_iron_binding_capacity", "serum_iron", "transferrin_saturation"],
    "anemia": ["hemoglobin", "hematocrit", "ferritin", "serum_iron", "mean_corpuscular_volume", "vitamin_b12", "folate_serum", "reticulocytes"],

    # Vitamins & Electrolytes
    "b12": ["vitamin_b12", "folate_serum", "homocysteine"],
    "vit b12": ["vitamin_b12"],
    "vitamin b12": ["vitamin_b12"],
    "vit d": ["25_hydroxy_vitamin_d", "calcium_total", "parathyroid_hormone"],
    "vitamin d": ["25_hydroxy_vitamin_d", "calcium_total"],
    "d3": ["25_hydroxy_vitamin_d"],
    "folate": ["folate_serum", "vitamin_b12", "homocysteine"],
    "na": ["sodium", "potassium", "chloride"],
    "k": ["potassium", "sodium", "chloride"],
    "ca": ["calcium_total", "calcium_ionized", "parathyroid_hormone", "phosphate"],
    "mg": ["magnesium", "calcium_total", "potassium"],
    "p": ["phosphate", "calcium_total", "parathyroid_hormone"],
    "lytes": ["sodium", "potassium", "chloride", "bicarbonate"],
    "electrolytes": ["sodium", "potassium", "chloride", "bicarbonate"],

    # Inflammation & Cardiac
    "esr": ["erythrocyte_sedimentation_rate", "c_reactive_protein"],
    "crp": ["c_reactive_protein", "high_sensitivity_c_reactive_protein", "erythrocyte_sedimentation_rate"],
    "hscrp": ["high_sensitivity_c_reactive_protein", "c_reactive_protein"],
    "trop": ["troponin_i", "troponin_t", "high_sensitivity_troponin_i", "high_sensitivity_troponin_t"],
    "troponin": ["troponin_i", "troponin_t", "high_sensitivity_troponin_i", "high_sensitivity_troponin_t", "creatine_kinase_mb"],
    "bnp": ["nt_probnp"],
    "ck": ["creatine_kinase_total", "creatine_kinase_mb"],
    "cpk": ["creatine_kinase_total", "creatine_kinase_mb"],

    # Coagulation
    "pt": ["prothrombin_time", "international_normalized_ratio"],
    "ptt": ["activated_partial_thromboplastin_time", "prothrombin_time"],
    "aptt": ["activated_partial_thromboplastin_time", "prothrombin_time"],
    "inr": ["international_normalized_ratio", "prothrombin_time"],
    "d dimer": ["d_dimer", "fibrinogen"],
    "fibrinogen": ["fibrinogen", "d_dimer"],

    # Urinalysis
    "ua": ["urine_specific_gravity", "urine_ph", "urine_protein_qualitative", "urine_glucose_qualitative", "urine_white_blood_cells", "urine_red_blood_cells"],
    "u/a": ["urine_specific_gravity", "urine_ph", "urine_protein_qualitative", "urine_glucose_qualitative", "urine_white_blood_cells", "urine_red_blood_cells"],
    "urinalysis": ["urine_specific_gravity", "urine_ph", "urine_protein_qualitative", "urine_glucose_qualitative", "urine_white_blood_cells", "urine_red_blood_cells"],

    # Persian Lab Terms
    "قند": ["fasting_plasma_glucose", "glucose", "hemoglobin_a1c", "random_plasma_glucose"],
    "قند ناشتا": ["fasting_plasma_glucose"],
    "قند خون": ["fasting_plasma_glucose", "glucose", "hemoglobin_a1c", "random_plasma_glucose"],
    "گلوکز": ["glucose", "fasting_plasma_glucose", "random_plasma_glucose", "hemoglobin_a1c"],
    "چربی": ["total_cholesterol", "triglycerides", "hdl_cholesterol", "ldl_cholesterol_calculated"],
    "چربی خون": ["total_cholesterol", "triglycerides", "hdl_cholesterol", "ldl_cholesterol_calculated"],
    "کلسترول": ["total_cholesterol", "ldl_cholesterol_calculated", "hdl_cholesterol", "triglycerides"],
    "تری گلیسیرید": ["triglycerides", "total_cholesterol"],
    "کبد": ["alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase", "total_bilirubin", "direct_bilirubin", "gamma_glutamyl_transferase", "albumin"],
    "آنزیم کبدی": ["alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase"],
    "کلیه": ["creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "uric_acid", "cystatin_c"],
    "کراتینین": ["creatinine", "egfr_ckd_epi_creatinine"],
    "اوره": ["blood_urea_nitrogen", "creatinine"],
    "کم خونی": ["hemoglobin", "hematocrit", "ferritin", "serum_iron", "mean_corpuscular_volume", "platelet_count"],
    "خون": ["hemoglobin", "hematocrit", "white_blood_cell_count", "platelet_count", "red_blood_cell_count"],
    "گلبول سفید": ["white_blood_cell_count", "neutrophils_percent", "lymphocytes_percent"],
    "گلبول قرمز": ["red_blood_cell_count", "hemoglobin", "hematocrit"],
    "پلاکت": ["platelet_count"],
    "آهن": ["serum_iron", "ferritin", "total_iron_binding_capacity", "transferrin_saturation"],
    "فریتین": ["ferritin", "serum_iron"],
    "تیروئید": ["thyroid_stimulating_hormone", "free_thyroxine", "free_triiodothyronine", "thyroid_peroxidase_antibody"],
    "التهاب": ["c_reactive_protein", "erythrocyte_sedimentation_rate"],
    "عفونت": ["white_blood_cell_count", "c_reactive_protein", "erythrocyte_sedimentation_rate", "procalcitonin"],
    "ادرار": ["urine_specific_gravity", "urine_ph", "urine_protein_qualitative", "urine_glucose_qualitative", "urine_white_blood_cells", "urine_red_blood_cells"],
    "اسید اوریک": ["uric_acid"],
    "ویتامین دی": ["25_hydroxy_vitamin_d"],
    "ویتامین": ["25_hydroxy_vitamin_d", "vitamin_b12", "folate_serum"],
}

_PRIMARY_CLINICAL_FEATURES: List[str] = [
    # Glycemic & Diabetes
    "fasting_plasma_glucose", "glucose", "hemoglobin_a1c", "random_plasma_glucose",
    # CBC & Hematology
    "white_blood_cell_count", "hemoglobin", "hematocrit", "platelet_count", "red_blood_cell_count",
    "mean_corpuscular_volume", "mean_corpuscular_hemoglobin", "mean_corpuscular_hemoglobin_concentration",
    "red_cell_distribution_width_cv", "neutrophils_percent", "lymphocytes_percent", "monocytes_percent",
    "eosinophils_percent", "basophils_percent",
    # Renal & Electrolytes
    "creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "uric_acid", "sodium", "potassium",
    "calcium_total", "calcium_ionized", "phosphate", "bicarbonate", "magnesium", "chloride",
    # Hepatic & Pancreatic
    "alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase", "total_bilirubin",
    "direct_bilirubin", "gamma_glutamyl_transferase", "albumin", "total_protein",
    # Lipids & Cardiovascular
    "total_cholesterol", "triglycerides", "hdl_cholesterol", "ldl_cholesterol_calculated", "vldl_cholesterol", "non_hdl_cholesterol",
    # Thyroid & Endocrine
    "thyroid_stimulating_hormone", "free_thyroxine", "free_triiodothyronine", "thyroid_peroxidase_antibody", "fasting_serum_insulin",
    # Iron & Vitamins
    "serum_iron", "ferritin", "total_iron_binding_capacity", "transferrin_saturation",
    "25_hydroxy_vitamin_d", "vitamin_b12", "folate_serum",
    # Inflammatory & Coagulation
    "c_reactive_protein", "high_sensitivity_c_reactive_protein", "erythrocyte_sedimentation_rate",
    "prothrombin_time", "international_normalized_ratio", "activated_partial_thromboplastin_time", "d_dimer",
    # Urinalysis
    "urine_specific_gravity", "urine_ph", "urine_protein_qualitative", "urine_glucose_qualitative",
    "urine_white_blood_cells", "urine_red_blood_cells", "urine_albumin_to_creatinine_ratio",
]
_PRIMARY_FEATURE_ORDER: Dict[str, int] = {fid: idx for idx, fid in enumerate(_PRIMARY_CLINICAL_FEATURES)}

CLINICAL_PANEL_DEFINITIONS: List[Tuple[str, str]] = [
    ("all", "All Panels (2,045 Features)"),
    ("cbc", "CBC & Hematology"),
    ("metabolic", "Metabolic & Diabetes (BMP/CMP)"),
    ("lipid", "Lipid Profile"),
    ("liver", "Liver Function (LFT)"),
    ("renal", "Renal Function (RFT)"),
    ("urinalysis", "Complete Urinalysis (U/A)"),
    ("thyroid", "Thyroid Panel (TFT)"),
    ("iron", "Iron & Anemia Panel"),
    ("coagulation", "Coagulation & Hemostasis"),
    ("cardiac", "Cardiac Biomarkers"),
    ("inflammatory", "Inflammatory & Rheumatology"),
    ("vitamins", "Vitamins & Minerals"),
    ("endocrine", "Endocrine & Hormones"),
    ("tumor", "Tumor Markers (Oncology)"),
    ("blood_gas", "Blood Gas & Acid-Base (ABG)"),
    ("infectious", "Infectious Serology & Microbiology"),
    ("toxicology", "Toxicology & Drug Monitoring (TDM)"),
    ("allergy", "Allergy Panel (Specific IgE)"),
    ("genetics", "Genetics & Molecular"),
]

_CBC_FIDS: Set[str] = {
    'white_blood_cell_count', 'hemoglobin', 'hematocrit', 'platelet_count', 'red_blood_cell_count',
    'mean_corpuscular_volume', 'mean_corpuscular_hemoglobin', 'mean_corpuscular_hemoglobin_concentration',
    'red_cell_distribution_width_cv', 'red_cell_distribution_width_sd', 'neutrophils_percent', 'lymphocytes_percent',
    'monocytes_percent', 'eosinophils_percent', 'basophils_percent', 'reticulocytes', 'erythrocyte_sedimentation_rate',
    'neutrophil_count_absolute', 'lymphocyte_count_absolute', 'monocyte_count_absolute',
    'eosinophil_count_absolute', 'basophil_count_absolute', 'mean_platelet_volume', 'platelet_large_cell_ratio',
    'nucleated_red_blood_cell_count', 'immature_granulocytes_percent'
}

_METABOLIC_FIDS: Set[str] = {
    'fasting_plasma_glucose', 'glucose', 'hemoglobin_a1c', 'random_plasma_glucose',
    'sodium', 'potassium', 'chloride', 'bicarbonate', 'calcium_total', 'calcium_ionized',
    'phosphate', 'magnesium', 'blood_urea_nitrogen', 'creatinine', 'egfr_ckd_epi_creatinine',
    'uric_acid', 'total_protein', 'albumin', 'anion_gap_serum', 'osmolality_serum',
    'fasting_serum_insulin', 'c_peptide', 'lactate_dehydrogenase', 'alkaline_phosphatase',
    'alanine_aminotransferase', 'aspartate_aminotransferase', 'total_bilirubin'
}

_LIVER_FIDS: Set[str] = {
    'alanine_aminotransferase', 'aspartate_aminotransferase', 'alkaline_phosphatase',
    'total_bilirubin', 'direct_bilirubin', 'indirect_bilirubin', 'gamma_glutamyl_transferase',
    'albumin', 'total_protein', 'lactate_dehydrogenase', 'prothrombin_time', 'international_normalized_ratio',
    'cholinesterase', '5_nucleotidase', 'albi_grade_albumin_bilirubin_score'
}

_RENAL_FIDS: Set[str] = {
    'creatinine', 'blood_urea_nitrogen', 'urea', 'egfr_ckd_epi_creatinine', 'uric_acid',
    'cystatin_c', 'urine_albumin_to_creatinine_ratio', 'fractional_excretion_of_sodium',
    'fractional_excretion_of_urea', 'blood_urea_nitrogen_to_creatinine_ratio',
    'sodium', 'potassium', 'bicarbonate', 'calcium_total', 'phosphate'
}

_IRON_FIDS: Set[str] = {
    'serum_iron', 'ferritin', 'total_iron_binding_capacity', 'transferrin_saturation',
    'reticulocytes', 'vitamin_b12', 'folate_serum', 'haptoglobin_serum_quantitative',
    'hemoglobin', 'hematocrit', 'mean_corpuscular_volume', 'mean_corpuscular_hemoglobin',
    'red_cell_distribution_width_cv', 'soluble_transferrin_receptor'
}

_CARDIAC_FIDS: Set[str] = {
    'troponin_i', 'troponin_t', 'high_sensitivity_troponin_i', 'high_sensitivity_troponin_t',
    'creatine_kinase_total', 'creatine_kinase_mb', 'creatine_kinase_mb_index', 'creatine_kinase_mb_mass',
    'nt_probnp', 'b_type_natriuretic_peptide', 'myoglobin', 'high_sensitivity_c_reactive_protein',
    'lactate_dehydrogenase', 'homocysteine'
}

_INFLAMMATORY_FIDS: Set[str] = {
    'c_reactive_protein', 'high_sensitivity_c_reactive_protein', 'erythrocyte_sedimentation_rate',
    'procalcitonin', 'ferritin', 'rheumatoid_factor', 'anti_cyclic_citrullinated_peptide_antibody',
    'antinuclear_antibodies_ana', 'complement_component_c3', 'complement_component_c4'
}

_COAG_FIDS: Set[str] = {
    'prothrombin_time', 'international_normalized_ratio', 'activated_partial_thromboplastin_time',
    'd_dimer', 'fibrinogen', 'thrombin_time', 'bleeding_time', 'platelet_count',
    'antithrombin_iii_activity', 'protein_c_activity', 'protein_s_activity'
}


def _resolve_panel_key(cat_sel: str) -> str:
    s = (cat_sel or "").strip().lower()
    if not s or s in ("all", "all panels", "all panels (2,045 features)", "all features", "all categories"):
        return "all"
    for k, label in CLINICAL_PANEL_DEFINITIONS:
        if s == k or s == label.lower():
            return k
    if "urin" in s or "u/a" in s:
        return "urinalysis"
    if "cbc" in s or "hematol" in s:
        return "cbc"
    if "metabol" in s or "bmp" in s or "cmp" in s or "diabet" in s:
        return "metabolic"
    if "lipid" in s or "cholest" in s:
        return "lipid"
    if "liver" in s or "lft" in s or "hepat" in s or "pancreas" in s:
        return "liver"
    if "renal" in s or "rft" in s or "kidney" in s:
        return "renal"
    if "thyroid" in s or "tft" in s:
        return "thyroid"
    if "iron" in s or "anemia" in s:
        return "iron"
    if "coag" in s or "hemostas" in s:
        return "coagulation"
    if "cardiac" in s or "heart" in s:
        return "cardiac"
    if "inflam" in s or "rheum" in s or "autoimmun" in s:
        return "inflammatory"
    if "vit" in s or "nutrit" in s or "electrolyt" in s:
        return "vitamins"
    if "endo" in s or "hormon" in s or "semen" in s:
        return "endocrine"
    if "tumor" in s or "oncol" in s or "cancer" in s:
        return "tumor"
    if "gas" in s or "abg" in s or "vbg" in s:
        return "blood_gas"
    if "infect" in s or "serol" in s or "microbio" in s:
        return "infectious"
    if "toxic" in s or "tdm" in s or "drug" in s:
        return "toxicology"
    if "allerg" in s or "ige" in s:
        return "allergy"
    if "gene" in s or "flow" in s or "cytometry" in s:
        return "genetics"
    return s


def _is_feature_in_panel(fid: str, meta: Dict, panel_key: str) -> bool:
    if not panel_key or panel_key == "all":
        return True

    c = str((meta.get("identity") or {}).get("category") or "").lower()
    fid_l = fid.lower()

    if panel_key == "cbc":
        return c == "hematology" or fid in _CBC_FIDS
    elif panel_key == "metabolic":
        return c in ("chemistry_metabolic", "chemistry_diabetes", "chemistry_enzymes") or fid in _METABOLIC_FIDS
    elif panel_key == "lipid":
        return c == "lipids_apolipoproteins" or any(x in fid_l for x in ("cholesterol", "triglyceride", "lipoprotein", "apolipoprotein", "vldl", "hdl", "ldl"))
    elif panel_key == "liver":
        return c == "liver_pancreas" or fid in _LIVER_FIDS
    elif panel_key == "renal":
        return (c == "renal" and not fid_l.startswith("urine_")) or fid in _RENAL_FIDS
    elif panel_key == "urinalysis":
        return c == "urinalysis" or "urine" in fid_l or "urinary" in fid_l
    elif panel_key == "thyroid":
        return c == "thyroid_endocrine" or any(x in fid_l for x in ("thyroid", "thyroxine", "triiodothyronine", "tsh", "anti_tpo", "thyroglobulin"))
    elif panel_key == "iron":
        return fid in _IRON_FIDS or any(x in fid_l for x in ("serum_iron", "ferritin", "transferrin", "tibc", "hepcidin", "hemopexin", "iron_binding"))
    elif panel_key == "coagulation":
        return c == "coagulation" or fid in _COAG_FIDS or any(x in fid_l for x in ("prothrombin", "thrombin_time", "thromboplastin", "inr", "fibrinogen", "d_dimer", "antithrombin", "protein_c", "protein_s"))
    elif panel_key == "cardiac":
        return c == "cardiac_inflammation" or fid in _CARDIAC_FIDS or any(x in fid_l for x in ("troponin", "natriuretic", "myoglobin", "ck_mb", "cardiac"))
    elif panel_key == "inflammatory":
        return c in ("rheumatology", "cardiac_inflammation") or fid in _INFLAMMATORY_FIDS or any(x in fid_l for x in ("c_reactive_protein", "erythrocyte_sedimentation_rate", "procalcitonin", "rheumatoid", "anti_ccp", "ana_"))
    elif panel_key == "vitamins":
        return c == "vitamins_nutrition" or any(x in fid_l for x in ("vitamin", "folate", "b12", "cobalamin", "calcium", "magnesium", "phosphate", "zinc", "copper", "selenium"))
    elif panel_key == "endocrine":
        return c in ("chemistry_endocrine", "thyroid_endocrine", "semen_analysis") or any(x in fid_l for x in ("cortisol", "acth", "prolactin", "testosterone", "estradiol", "progesterone", "fsh", "lh", "growth_hormone", "dhea", "aldosterone", "renin", "insulin", "c_peptide", "parathyroid_hormone"))
    elif panel_key == "tumor":
        return c == "tumor_markers" or any(x in fid_l for x in ("psa", "cea", "ca_125", "ca_19", "ca_15", "afp", "calcitonin", "chromogranin"))
    elif panel_key == "blood_gas":
        return c == "blood_gas" or any(x in fid_l for x in ("pco2", "po2", "base_excess", "lactate", "bicarbonate", "oxygen_saturation"))
    elif panel_key == "infectious":
        return c in ("infectious_serology_molecular", "microbiology") or any(x in fid_l for x in ("antibody", "antigen", "virus", "hepatitis", "hiv", "covid", "pylori", "strep", "rubella", "toxoplasma"))
    elif panel_key == "toxicology":
        return c == "therapeutic_drug_monitoring_toxicology"
    elif panel_key == "allergy":
        return c == "allergy_specific_ige" or "ige" in fid_l
    elif panel_key == "genetics":
        return c in ("genetics_flow_cytometry", "neurology", "body_fluids")

    return c == panel_key

class PerformanceMonitor:
    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def track(self, operation: str, duration: float):
        with self._lock:
            if operation not in self._metrics:
                self._metrics[operation] = []
            self._metrics[operation].append(duration)

            if len(self._metrics[operation]) > 100:
                self._metrics[operation] = self._metrics[operation][-100:]

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            stats = {}
            for op, durations in self._metrics.items():
                if durations:
                    stats[op] = {
                        "count": len(durations),
                        'avg': sum(durations) / len(durations),
                        "min": min(durations),
                        "max": max(durations),
                    }
            return stats

perf_monitor = PerformanceMonitor()

def timed_operation(operation_name: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                perf_monitor.track(operation_name, duration)
        return wrapper
    return decorator

def _fatal_startup(msg: str) -> None:
    """Never die silently: log, write a file next to the exe, show a dialog, exit 1."""
    try:
        logger.error(msg)
    except Exception:
        pass
    try:
        with open("hemoglyph_startup_error.log", "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n{msg}\n")
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg[:1200], "Hemoglyph Startup Error", 0x10)
    except Exception:
        pass
    sys.exit(1)

try:
    from paygah_dade import (init_db, get_user_by_email, register_user, update_user_profile,
                         get_user_tests, get_test_by_id, delete_test, save_blood_test,
                         verify_password, hash_password, DB_NAME, gereftan_ettesal,
                         upgrade_password_hash)
    logger.info("✅ Database module loaded")
except ImportError as e:
    _fatal_startup(f"Database module not found: {e}")

try:
    from sarvis_tahlil import AnalysisService
    logger.info("✅ Analysis service loaded")
except ImportError as e:
    _fatal_startup(f"Analysis service not found: {e}")

try:
    from AI import BloodLabChatbot, EmbeddedAIEngine, download_embedded_model_stream
    logger.info("✅ AI chatbot loaded")
except ImportError as e:
    logger.warning(f"⚠️ AI chatbot not available: {e}")
    BloodLabChatbot = None
    EmbeddedAIEngine = None
    download_embedded_model_stream = None

try:
    from ocr import FeatureRegistry
    logger.info('✅ OCR module loaded')
except ImportError as e:
    logger.warning(f"⚠️ OCR module not available: {e}")
    FeatureRegistry = None

try:
    from namaye_registry import (
        s as _s,
        disease_detail as _registry_disease_detail,
        guideline_rows as _registry_guideline_rows,
        disease_rows as _registry_disease_rows,
    )
    logger.info("✅ Registry views loaded")
except ImportError as e:
    _fatal_startup(f"Registry views not found: {e}")

try:
    from namaye_registry import warm_indexes as _registry_warm_indexes
except ImportError:
    _registry_warm_indexes = None

HAS_REFERENCES = False
HAS_NEW_PREDICTION = False
_predict_risks = None
RISK_MODELS = []
_get_model_catalog = None

try:
    import models_scientific_references
    HAS_REFERENCES = True
    logger.info("✅ Scientific references loaded")
except ImportError:
    logger.warning("⚠️ Scientific references not found")

try:
    from prdicter import predict_chronic_disease_risks as _predict_risks
    HAS_NEW_PREDICTION = True
    logger.info("✅ Prediction engine (v2) loaded")
except ImportError:
    try:
        from prdicter import predict_2year_risks as _predict_risks
        HAS_NEW_PREDICTION = False
        logger.info('✅ Legacy prediction engine loaded')
    except ImportError:
        logger.warning("⚠️ Prediction engine not available")

try:
    from prdicter import MODELS as RISK_MODELS
    logger.info(f"✅ Loaded {len(RISK_MODELS)} risk models")
except Exception as e:
    logger.warning(f"⚠️ Risk models not available: {e}")

try:
    from prdicter import fehrest_model_ha as _get_model_catalog
    logger.info("✅ Model catalog available")
except Exception:
    logger.warning("⚠️ Model catalog not available")

# Unit conversion and alias resolution are handled natively by prdicter and calcu.

def _bargozari_json(path: Path) -> Optional[dict]:
    return bargozari_registry(path)


def _preflight_files() -> List[str]:
    problems: List[str] = []
    for label, path in (("feature", FEATURE_REGISTRY), ("disease", DISEASE_REGISTRY)):
        if not path.exists():
            problems.append(f"Missing {label} registry: {path.name}")
        elif path.stat().st_size < 64:
            problems.append(f"Empty {label} registry: {path.name}")
    return problems


def _validate_environment() -> None:
    problems = _preflight_files()

    fp = _bargozari_json(FEATURE_REGISTRY)
    dp = _bargozari_json(DISEASE_REGISTRY)

    if fp is None or not fp.get("features"):
        problems.append(f"Missing/empty feature registry: {FEATURE_REGISTRY.name}")

    if dp is None or not dp.get("rules") or not dp.get("diseases"):
        problems.append(f"Missing/empty disease registry: {DISEASE_REGISTRY.name}")

    if problems:
        raise RuntimeError("HEMOGLYPH cannot start:\n" +
                           "\n".join(f"  - {p}" for p in problems))

def _chat_db_rahandazi():
    try:
        conn = gereftan_ettesal()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_id INTEGER,
                title TEXT DEFAULT '',
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                messages TEXT DEFAULT '[]',
                summary TEXT DEFAULT ''
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize chat table: {e}")

def _chat_db_zakhire(user_id: int, messages: List[Dict], title: str,
                   language: str, analysis_id: Optional[int],
                   summary: str, session_id: Optional[int]) -> int:
    try:
        conn = gereftan_ettesal()
        c = conn.cursor()
        blob = json.dumps(messages, ensure_ascii=False)

        if session_id:
            c.execute('''UPDATE chat_sessions
                        SET messages=?, title=?, language=?, analysis_id=?,
                            summary=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=? AND user_id=?''',
                     (blob, title, language, analysis_id, summary, session_id, user_id))

            if c.rowcount > 0:
                conn.commit()
                conn.close()
                return session_id

        c.execute('''INSERT INTO chat_sessions
                    (user_id, analysis_id, title, language, messages, summary)
                    VALUES (?,?,?,?,?,?)''',
                 (user_id, analysis_id, title, language, blob, summary))
        conn.commit()
        rid = c.lastrowid
        conn.close()
        return rid
    except Exception as e:
        logger.error(f"Failed to save chat: {e}")
        return session_id or 0

def _chat_db_list(user_id: int, limit: int = 30) -> List[Dict]:
    try:
        conn = gereftan_ettesal()
        c = conn.cursor()
        c.execute('''SELECT id, analysis_id, title, language, created_at,
                            updated_at, summary
                     FROM chat_sessions WHERE user_id=?
                     ORDER BY updated_at DESC LIMIT ?''', (user_id, limit))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Failed to list chats: {e}")
        return []

def _chat_db_get(session_id: int, user_id: int) -> Optional[Dict]:
    try:
        conn = gereftan_ettesal()
        c = conn.cursor()
        c.execute("SELECT * FROM chat_sessions WHERE id=? AND user_id=?",
                 (session_id, user_id))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        rec = dict(row)
        try:
            rec["messages"] = json.loads(rec.get("messages") or '[]')
        except Exception:
            rec["messages"] = []
        return rec
    except Exception as e:
        logger.error(f"Failed to get chat: {e}")
        return None

def _chat_db_hazf(session_id: int, user_id: int) -> bool:
    try:
        conn = gereftan_ettesal()
        c = conn.cursor()
        c.execute("DELETE FROM chat_sessions WHERE id=? AND user_id=?",
                 (session_id, user_id))
        conn.commit()
        n = c.rowcount
        conn.close()
        return n > 0
    except Exception as e:
        logger.error(f"Failed to delete chat: {e}")
        return False

def _chat_db_yaftan_for_tahlil(user_id: int, analysis_id: Optional[int]) -> Optional[int]:
    if not analysis_id:
        return None

    try:
        conn = gereftan_ettesal()
        c = conn.cursor()
        c.execute('''SELECT id FROM chat_sessions WHERE user_id=? AND analysis_id=?
                     ORDER BY updated_at DESC LIMIT 1''', (user_id, analysis_id))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Failed to find chat for analysis: {e}")
        return None

class _AsyncHub(QObject):
    done = Signal(str, object)
    failed = Signal(str, str)

class ListModel(QAbstractListModel):
    rowsChanged = Signal()
    countChanged = Signal()

    def __init__(self, roles: List[str], parent=None):
        super().__init__(parent)
        self._roles = list(roles)
        self._rows: List[Dict[str, Any]] = []
        self._role_index = {i + Qt.UserRole + 1: r for i, r in enumerate(self._roles)}
        self._role_names = {i + Qt.UserRole + 1: r.encode()
                            for i, r in enumerate(self._roles)}

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._rows)

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def roleNames(self) -> Dict[int, bytes]:
        return self._role_names

    def data(self, index: QModelIndex, role: int) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        name = self._role_index.get(role)
        return self._rows[index.row()].get(name) if name else None

    def set_satrha(self, rows: List[Dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()
        self.rowsChanged.emit()
        self.countChanged.emit()

    def update(self, i: int, row: Dict[str, Any]) -> None:
        if 0 <= i < len(self._rows):
            self._rows[i].update(row)
            idx = self.index(i, 0)
            self.dataChanged.emit(idx, idx)
            self.rowsChanged.emit()

    def get(self) -> List[Dict[str, Any]]:
        return self._rows

    def clear(self) -> None:
        self.set_satrha([])

def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)

def _vaziat_label(status: str) -> str:
    labels = {
        'urgent_pattern': "Urgent pattern",
        "criterion_met": 'Criterion met',
        "compatible_pattern": "Compatible pattern",
        "possible_pattern": "Possible pattern",
        "screening_positive": "Screening positive",
        "conflicting_data": "Conflicting data",
        "insufficient_data": "Insufficient data",
        "criterion_not_met": "Not met",
        "not_applicable": "Not applicable",
        'ruled_out': "Ruled out",
        "excluded": "Excluded",
    }
    return labels.get(status, status)

def _tarikhche_title(t: Dict) -> str:
    try:
        panels = t.get("selected_panels")
        if isinstance(panels, list) and panels:
            clean_names = [str(x).replace("_", " ").title() for x in panels[:2]]
            return ", ".join(clean_names) + ('…' if len(panels) > 2 else "")
    except Exception:
        pass
    return "Laboratory analysis"

def _tarikhche_subtitle(t: Dict) -> str:
    try:
        inputs = t.get('patient_inputs') or {}
        if isinstance(inputs, str):
            try:
                inputs = json.loads(inputs)
            except Exception:
                inputs = {}
        ctx = inputs.get("context", inputs) if isinstance(inputs, dict) else {}
        age = ctx.get("age_years") or ctx.get("age")
        if age:
            return f"Age {age}"
        obs = inputs.get("observations") if isinstance(inputs, dict) else None
        if isinstance(obs, dict) and obs:
            return f"{len(obs)} biomarkers"
    except Exception:
        pass
    return "Clinical analysis"

# ==============================================================================
# Predictor & Clinical Interpretation Invariants
# (All feature aliases, units, and clinical derivations are handled natively by prdicter.py)
# ==============================================================================

POSITIVE_STATUSES = {
    "urgent_pattern", "criterion_met", "compatible_pattern",
    "possible_pattern", "screening_positive",
}

# Only firmly-established interpretations count as "has disease" for
# AlreadyDiagnosed exclusions and population gates.
DIAGNOSED_STATUSES = {"urgent_pattern", "criterion_met"}

class Backend(QObject):
    toast = Signal(str, str)
    licenseChanged = Signal()
    remoteBlockChanged = Signal()
    sentinelStatusChanged = Signal()
    remoteRevokeSignal = Signal(str)
    remoteRestoreSignal = Signal()
    chatReplyReady = Signal(str, bool)
    chatBusyChanged = Signal()
    chatReady = Signal()
    chatAvailableChanged = Signal()
    ocrErrorChanged = Signal()
    ocrAutoRejectedChanged = Signal()
    ocrApiKeyChanged = Signal()
    chatSessionOpened = Signal()
    analysisReset = Signal()
    guidelinesFocusChanged = Signal()

    readyChanged = Signal()
    bootstrapTextChanged = Signal()
    featureCategoriesChanged = Signal()
    riskCatalogChanged = Signal()

    loggedInChanged = Signal()
    currentPageChanged = Signal()
    sidebarCollapsedChanged = Signal()
    userNameChanged = Signal()
    busyChanged = Signal()
    busyTextChanged = Signal()
    selectedFileChanged = Signal()
    rememberedEmailChanged = Signal()
    hasCurrentAnalysisChanged = Signal()
    analysisSavedChanged = Signal()
    measuredCountChanged = Signal()
    derivedCountChanged = Signal()
    clinicalCountChanged = Signal()
    urgentCountChanged = Signal()
    insufficientCountChanged = Signal()
    conflictingCountChanged = Signal()
    chatLanguageChanged = Signal()
    chatProviderChanged = Signal()
    chatModelChanged = Signal()
    chatIsLocalChanged = Signal()
    chatSummaryLoadingChanged = Signal()
    chatHistoryRowsChanged = Signal()
    currentChatSessionIdChanged = Signal()
    currentAnalysisIdChanged = Signal()
    chatAnalysisOptionsChanged = Signal()
    patientContextRowsChanged = Signal()
    diseaseRowsChanged = Signal()

    featureRowsChanged = Signal()
    manualRowsChanged = Signal()
    reviewRowsChanged = Signal()
    referenceRowsChanged = Signal()
    guidelineRowsChanged = Signal()
    measuredRowsChanged = Signal()
    derivedRowsChanged = Signal()
    clinicalRowsChanged = Signal()
    riskRowsChanged = Signal()
    resultWarningsChanged = Signal()
    criticalAlertsChanged = Signal()
    historyRowsChanged = Signal()
    globalSearchRowsChanged = Signal()
    triageChanged = Signal()
    executiveSummaryChanged = Signal()
    embeddedAIAvailableChanged = Signal()
    embeddedDownloadingChanged = Signal()
    embeddedDownloadProgressChanged = Signal()
    patientRowsChanged = Signal()
    activePatientChanged = Signal()

    _ready = False
    _bootstrapText = "Starting…"
    _bootstrapError = ""
    _bootstrap_started = False
    _is_embedded_downloading = False
    _embedded_download_progress = 0.0
    _embedded_download_status_text = ""
    _loggedIn = False
    _currentPage = "home"
    _sidebarCollapsed = False
    _userName = ""
    _userEmail = ''
    _appBuild = f"{APP_VERSION}-enterprise"
    _busy = False
    _busyText = ""
    _selectedFile = ""
    _executiveSummary = ""
    _primaryClinicalStatus = "PHYSIOLOGICAL_BASELINE"
    _tier1Rows = []
    _tier2Rows = []
    _tier3Rows = []
    _targetPopulationInfo = ""
    _hasCurrentAnalysis = False
    _analysisSaved = False
    _measuredCount = 0
    _derivedCount = 0
    _clinicalCount = 0
    _urgentCount = 0
    _ocr_auto_rejected = 0
    _ocr_api_key = ""
    _insufficientCount = 0
    _conflictingCount = 0
    _license_valid = False
    _is_remotely_blocked = False
    _remote_block_reason = ""
    _sentinel_online = False
    _license_mid = ""
    _license_tier = "Unlicensed"
    _license_customer = ""
    _license_expiry = ""
    _license_error = ""
    _license_algorithm = "Military-Grade RSA-4096 / SHA-512"
    _license_features: List[str] = []
    _chat_busy = False
    _chat_lang = "en"
    _chat_available = False
    _cached_summary = ""
    _ocr_error = ""
    _extract_gen = 0
    _summary_gen = 0
    _current_user_id = None
    _current_profile = {}
    _manual = {}
    _confirmed = {}
    _context = {}
    _current_result = None
    _review = {"session": None}
    _last_risks = []
    _task_counter = 0
    _handlers = {}
    _err_handlers = {}
    _current_analysis_db_id = None
    _currentChatSessionId = None
    _guidelineFocus = ""
    _page_loaded = {}
    _chatHistoryRows = []
    _featureRows = []
    _manualRows = []
    _reviewRows = []
    _referenceRows = []
    _guidelineRows = []
    _diseaseRows = []
    _measuredRows = []
    _derivedRows = []
    _clinicalRows = []
    _riskRows = []
    _resultWarnings = []
    _criticalAlerts = []
    _historyRows = []
    _globalSearchRows = []
    _featureCategories = []
    _featureOptions = []
    _riskCatalog = []
    _patient_context_rows: List[Dict] = []

    _state_lock = threading.RLock()
    _cache_lock = threading.Lock()

    def __init__(self):
        super().__init__()
        logger.debug('=== Backend.__init__ started (phase 1: instant) ===')
        t0 = time.perf_counter()
        self._ready = False
        self._bootstrapError = ""
        self._bootstrapText = "Starting…"

        problems = _preflight_files()
        if problems:
            self._bootstrapError = "; ".join(problems)
            logger.error("Preflight failed: %s", self._bootstrapError)

        self._settings = QSettings(APP_ORG, APP_NAME)
        self._rememberedEmail = str(self._settings.value("rememberedEmail", ''))

        stored_lang = str(self._settings.value('chatLanguage', "en"))
        self._chat_lang = "en"
        self._chat_provider = "local"
        self._chat_model = "qwen2.5:1.5b"
        self._chat_is_local = True
        self._chat_local_url = "http://127.0.0.1:11434/v1"
        self._chat_summary_loading = False
        self._chat_available = False
        init_db()

        # Hardware-bound cryptographic licensing
        self._license_mid = license_engine.get_machine_id()
        self._pending_remote_block = None
        self.remoteRevokeSignal.connect(self._handle_remote_revocation)
        self.remoteRestoreSignal.connect(self._handle_remote_restoration)

        # GUI-thread 500ms safety poll timer
        self._sentinel_gui_poll_timer = QTimer(self)
        self._sentinel_gui_poll_timer.setInterval(500)
        self._sentinel_gui_poll_timer.timeout.connect(self._check_pending_remote_block)
        self._sentinel_gui_poll_timer.start()

        self._refresh_license()
        self._start_sentinel_heartbeat_worker()

        if self._settings.contains("ocrApiKey"):
            saved_key = str(self._settings.value("ocrApiKey") or "").strip()
        else:
            saved_key = ""
            try:
                cfg_file = Path.home() / ".hemoglyph" / "config.json"
                if cfg_file.exists():
                    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                    saved_key = str(cfg.get("ocrApiKey") or "").strip()
            except Exception:
                pass

            if not saved_key:
                saved_key = os.getenv("OCR_API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip()

            if not saved_key:
                for cand_dir in (_determine_root(), Path(__file__).resolve().parent):
                    try:
                        env_file = cand_dir / ".env"
                        if env_file.exists():
                            for line in env_file.read_text(encoding="utf-8").splitlines():
                                if line.startswith("OCR_API_KEY=") or line.startswith("GROQ_API_KEY="):
                                    saved_key = line.split("=", 1)[1].strip()
                                    if saved_key:
                                        break
                        if saved_key:
                            break
                    except Exception:
                        pass

        self._ocr_api_key = saved_key
        if self._ocr_api_key:
            os.environ["OCR_API_KEY"] = self._ocr_api_key
            os.environ["GROQ_API_KEY"] = self._ocr_api_key
        else:
            os.environ.pop("OCR_API_KEY", None)
            os.environ.pop("GROQ_API_KEY", None)
        self._settings.setValue("ocrApiKey", self._ocr_api_key)
        try:
            self._settings.sync()
        except Exception:
            pass

        try:
            _chat_db_rahandazi()
        except Exception as exc:
            logger.warning(f"chat table init skipped: {exc}")

        self.feature_registry = None
        self.features: Dict[str, Any] = {}
        self.disease_payload: Dict[str, Any] = {}
        self.service = None
        self.ai = None
        self._featureCategories = [label for _, label in CLINICAL_PANEL_DEFINITIONS]
        self._featureOptions = []
        self._riskCatalog = []
        self._feature_search_cache: Dict[str, List[Dict]] = {}
        self._async_hub = _AsyncHub()
        self._async_hub.done.connect(self._dispatch_done)
        self._async_hub.failed.connect(self._dispatch_failed)

        logger.info("Backend phase 1 done in %.0f ms — showing UI now",
                    (time.perf_counter() - t0) * 1000)

    @Slot()
    def startBootstrap(self) -> None:
        if getattr(self, '_bootstrap_started', False):
            return
        self._bootstrap_started = True

        def work():
            return self._bootstrap()

        def ok(_res):
            self._ready = True
            self._bootstrapText = "Ready"
            self.readyChanged.emit()
            self.bootstrapTextChanged.emit()
            self.featureCategoriesChanged.emit()
            self.riskCatalogChanged.emit()
            logger.info("✅ Bootstrap complete — %s", cache_stats())
            if self._page_loaded.get('manual'):
                self.searchFeatures("", "All")
            if self._page_loaded.get("guidelines"):
                self.searchDiseases('')
            if self._page_loaded.get("references"):
                self.searchReferences("")

            QTimer.singleShot(300, self._probe_chat)
        def err(msg):
            self._bootstrapError = str(msg)
            self._bootstrapText = "Startup failed"
            self.readyChanged.emit()
            self.bootstrapTextChanged.emit()
            logger.error("Bootstrap failed: %s", msg)
            self.toast.emit("error", f"Startup failed: {msg}")

        self._ejra_async(work, ok, err)

    def _set_bootstrap_matn(self, text: str) -> None:
        self._bootstrapText = text
        self.bootstrapTextChanged.emit()

    def _bootstrap(self) -> bool:
        t_all = time.perf_counter()

        self._set_bootstrap_matn("Reading clinical registries…")
        _validate_environment()

        self._set_bootstrap_matn("Indexing laboratory features…")
        try:
            if FeatureRegistry:
                self.feature_registry = FeatureRegistry.shared(FEATURE_REGISTRY)
                self.features = self.feature_registry.features or {}
        except Exception as e:
            logger.error(f"FeatureRegistry engine failed ({e}); using raw JSON fallback.")

        if not self.features:
            payload = _bargozari_json(FEATURE_REGISTRY) or {}
            self.features = payload.get("features", {}) or {}

        logger.info(f"✅ Feature registry ready: {len(self.features)} features")

        self.disease_payload = _bargozari_json(DISEASE_REGISTRY) or {}
        logger.info(f"✅ Disease registry ready: {len(self.disease_payload.get('diseases', {}))} diseases, "
                    f"{len(self.disease_payload.get('guideline_sources', {}))} sources, "
                    f"{len(self.disease_payload.get('rules', {}))} rules")

        self._featureCategories = [label for _, label in CLINICAL_PANEL_DEFINITIONS]
        self._featureOptions = sorted(self.features.keys())[:_MAX_FEATURE_OPTIONS]
        self.featureCategoriesChanged.emit()

        self._set_bootstrap_matn("Loading risk models…")
        self._riskCatalog = []
        if _get_model_catalog:
            try:
                self._riskCatalog = _get_model_catalog()
            except Exception as exc:
                logger.error(f"get_model_catalog failed: {exc}")

        if not self._riskCatalog and RISK_MODELS:
            for m in RISK_MODELS:
                try:
                    if not isinstance(m, dict):
                        continue
                    self._riskCatalog.append({
                        "diseaseKey": _s(m.get("diseaseKey")),
                        "nameEn": _s(m.get("nameEn")),
                        "modelName": _s(m.get("modelName")),
                        'kind': _s(m.get("kind")),
                        "horizonYears": float(m.get("horizonYears") or 0),
                        "requiredFeatures": list(m.get("requiredFeatures") or []),
                        "weights": {},
                        'baseIncidence': 0.0,
                        "citation": _s(m.get("citation")),
                        "doi": _s(m.get("doi")),
                        "pmid": _s(m.get("pmid")),
                        "articleTitle": _s(m.get('article_title')),
                        "journal": _s(m.get("journal")),
                        "publicationYear": _s(m.get('publication_year') or m.get('year')),
                        "referenceUrl": _s(m.get("reference_url")),
                    })
                except Exception:
                    continue

        logger.info(f"✅ Risk model catalog: {len(self._riskCatalog)} entries")

        self._set_bootstrap_matn("Preparing analysis engine…")
        self.service = AnalysisService(
            feature_registry_path=FEATURE_REGISTRY,
            disease_registry_path=DISEASE_REGISTRY,
            ocr_api_key=os.getenv("OCR_API_KEY") or os.getenv("GROQ_API_KEY"),
            execution_mode="research",
        )

        try:
            _b = self.service.ocr.backend
            if hasattr(_b, "preprocess"):
                _b.preprocess = False
            if hasattr(_b, "timeout"):
                _b.timeout = 90
            if getattr(_b, "name", "") == "vision":
                _b.base_url = os.getenv("OCR_BASE_URL", "https://api.groq.com/openai/v1")
                try:
                    from openai import OpenAI
                    _b._client = OpenAI(api_key=_b.api_key, base_url=_b.base_url,
                                        timeout=_b.timeout, max_retries=1)
                except Exception as cx:
                    logger.warning(f"OpenAI client pre-create skipped: {cx}")
            logger.info(f"OCR backend selected: {getattr(_b, 'name', '?')}")
        except Exception as exc:
            logger.warning(f"OCR speed tweak skipped: {exc}")

        self.ai = self._sakht_chatbot()

        self._set_bootstrap_matn("Warming search indexes…")
        if _registry_warm_indexes is not None:
            try:
                _registry_warm_indexes({"features": self.features}, self.disease_payload)
            except Exception:
                logger.exception("index warm-up skipped")

        try:
            self._feature_search_cache["|All"] = self._mohasebe_vizhegi_satrha("", "All")
        except Exception:
            logger.exception("feature row pre-render skipped")

        logger.info("Bootstrap total: %.2fs", time.perf_counter() - t_all)
        return True


    def _sakht_chatbot(self) -> Optional[BloodLabChatbot]:
        if not BloodLabChatbot:
            return None

        try:
            bot = BloodLabChatbot(language=self._chat_lang)
            if bot is not None:
                self._chat_provider = getattr(bot, "provider", "local")
                self._chat_model = getattr(bot, "model", "qwen2.5:1.5b")
                self._chat_is_local = getattr(bot, "is_local", True)
                logger.info(
                    "✅ Chatbot initialized: provider=%s, model=%s, is_local=%s",
                    self._chat_provider, self._chat_model, self._chat_is_local,
                )
            return bot
        except Exception as exc:
            logger.warning(f"Chat assistant initialization skipped: {exc}")
            return None

    def _probe_chat(self) -> None:
        self._chat_available = False
        self.chatAvailableChanged.emit()

    @Property(int, constant=True)
    def totalRuleCount(self) -> int:
        return len(self.disease_payload.get('rules', {})) if hasattr(self, 'disease_payload') and self.disease_payload else 0
    @Property("QVariantList", notify=diseaseRowsChanged)
    def diseaseRows(self) -> List[Dict]:
        return self._diseaseRows
    @Property(int, constant=True)
    def totalFeatureCount(self) -> int:
        return len(self.features) if hasattr(self, 'features') else 0

    @Property(int, constant=True)
    def totalDiseaseCount(self) -> int:
        return len(self.disease_payload.get('diseases', {})) if hasattr(self, 'disease_payload') and self.disease_payload else 0
    @Property(bool, notify=loggedInChanged)
    def loggedIn(self) -> bool:
        return self._loggedIn

    @Property(str, notify=currentPageChanged)
    def currentPage(self) -> str:
        return self._currentPage

    @Property(int, notify=ocrAutoRejectedChanged)
    def ocrAutoRejected(self) -> int:
        return self._ocr_auto_rejected

    @Property(str, constant=True)
    def appBuild(self) -> str:
        return self._appBuild

    @Property(bool, notify=sidebarCollapsedChanged)
    def sidebarCollapsed(self) -> bool:
        return self._sidebarCollapsed

    @Property(str, notify=userNameChanged)
    def userName(self) -> str:
        return self._userName

    @Property(str, notify=userNameChanged)
    def userEmail(self) -> str:
        return self._userEmail

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=busyTextChanged)
    def busyText(self) -> str:
        return self._busyText

    @Property(str, notify=selectedFileChanged)
    def selectedFile(self) -> str:
        return self._selectedFile

    @Property(bool, notify=rememberedEmailChanged)
    def hasRememberedEmail(self) -> bool:
        return bool(self._rememberedEmail)

    @Property(str, notify=rememberedEmailChanged)
    def rememberedEmail(self) -> str:
        return self._rememberedEmail

    @Property(bool, notify=hasCurrentAnalysisChanged)
    def hasCurrentAnalysis(self) -> bool:
        return self._hasCurrentAnalysis

    @Property(bool, notify=analysisSavedChanged)
    def analysisSaved(self) -> bool:
        return self._analysisSaved

    @Property(int, notify=measuredCountChanged)
    def measuredCount(self) -> int:
        return self._measuredCount

    @Property(int, notify=derivedCountChanged)
    def derivedCount(self) -> int:
        return self._derivedCount

    @Property(int, notify=clinicalCountChanged)
    def clinicalCount(self) -> int:
        return self._clinicalCount

    @Property(int, notify=urgentCountChanged)
    def urgentCount(self) -> int:
        return self._urgentCount

    @Property(int, notify=insufficientCountChanged)
    def insufficientCount(self) -> int:
        return self._insufficientCount

    @Property(int, notify=conflictingCountChanged)
    def conflictingCount(self) -> int:
        return self._conflictingCount

    @Property(bool, notify=chatBusyChanged)
    def chatBusy(self) -> bool:
        return self._chat_busy

    @Property(bool, notify=hasCurrentAnalysisChanged)
    def chatHasAnalysis(self) -> bool:
        return self._hasCurrentAnalysis and self.ai is not None

    @Property(bool, notify=readyChanged)
    def chatConfigured(self) -> bool:
        return self.ai is not None

    @Property(str, notify=chatReady)
    def chatSummary(self) -> str:
        return self._cached_summary

    @Property(str, notify=chatLanguageChanged)
    def chatLanguage(self) -> str:
        return self._chat_lang

    @Property(str, notify=chatProviderChanged)
    def chatProvider(self) -> str:
        if self.ai is not None and hasattr(self.ai, "provider"):
            return self.ai.provider
        return self._chat_provider

    @Property(str, notify=chatModelChanged)
    def chatModel(self) -> str:
        if self.ai is not None and hasattr(self.ai, "model"):
            return self.ai.model
        return self._chat_model

    @Property(bool, notify=chatIsLocalChanged)
    def chatIsLocal(self) -> bool:
        if self.ai is not None and hasattr(self.ai, "is_local"):
            return bool(self.ai.is_local)
        return self._chat_is_local

    @Property(str, constant=True)
    def chatLocalUrl(self) -> str:
        return self._chat_local_url

    @Property(bool, notify=embeddedAIAvailableChanged)
    def isEmbeddedAIAvailable(self) -> bool:
        if EmbeddedAIEngine:
            return EmbeddedAIEngine.is_configured()
        return False

    @Property(bool, notify=embeddedDownloadingChanged)
    def isEmbeddedDownloading(self) -> bool:
        return self._is_embedded_downloading

    @Property(float, notify=embeddedDownloadProgressChanged)
    def embeddedDownloadProgress(self) -> float:
        return self._embedded_download_progress

    @Property(str, notify=embeddedDownloadProgressChanged)
    def embeddedDownloadStatusText(self) -> str:
        return self._embedded_download_status_text

    @Slot()
    def downloadEmbeddedAI(self) -> None:
        if self._is_embedded_downloading:
            return
        if not download_embedded_model_stream:
            self.toast.emit("error", "Embedded AI downloader not available.")
            return

        self._is_embedded_downloading = True
        self._embedded_download_progress = 0.0
        self._embedded_download_status_text = "Connecting to model repository..."
        self.embeddedDownloadingChanged.emit()
        self.embeddedDownloadProgressChanged.emit()

        def _do_download():
            def _progress_cb(prog: float, text: str):
                self._embedded_download_progress = prog
                self._embedded_download_status_text = text
                self.embeddedDownloadProgressChanged.emit()

            try:
                ok, res = download_embedded_model_stream(progress_callback=_progress_cb)
                self._is_embedded_downloading = False
                self.embeddedDownloadingChanged.emit()
                if ok:
                    self._embedded_download_status_text = "Download complete. Initializing embedded engine..."
                    self.embeddedDownloadProgressChanged.emit()
                    self.embeddedAIAvailableChanged.emit()
                    self.toast.emit("success", "Embedded AI model installed! Initializing offline assistant...")
                    self.ai = self._sakht_chatbot()
                    self._probe_chat()
                    self.readyChanged.emit()
                else:
                    self._embedded_download_status_text = f"Download error: {res}"
                    self.embeddedDownloadProgressChanged.emit()
                    self.toast.emit("error", f"Model download failed: {res}")
            except Exception as exc:
                self._is_embedded_downloading = False
                self.embeddedDownloadingChanged.emit()
                self._embedded_download_status_text = f"Download failed: {exc}"
                self.embeddedDownloadProgressChanged.emit()
                self.toast.emit("error", f"Download failed: {exc}")

        threading.Thread(target=_do_download, daemon=True).start()

    @Property(bool, notify=chatSummaryLoadingChanged)
    def chatSummaryLoading(self) -> bool:
        return self._chat_summary_loading

    def _refresh_license(self) -> None:
        st = license_engine.get_current_license_status()
        self._license_valid = bool(st.get("valid", False))
        self._license_mid = st.get("machine_id", self._license_mid)
        self._license_tier = st.get("tier", "Unlicensed")
        self._license_customer = st.get("licensee", "")
        self._license_expiry = st.get("expires", "")
        self._license_error = st.get("error", "")
        self._license_algorithm = st.get("algorithm", "RSA-4096 (Military-Grade)")
        self._license_features = list(st.get("features", []))
        self.licenseChanged.emit()

    @Property(bool, notify=licenseChanged)
    def licenseValid(self) -> bool:
        return self._license_valid

    @Property(str, notify=licenseChanged)
    def licenseMachineId(self) -> str:
        return self._license_mid

    @Property(str, notify=licenseChanged)
    def licenseTier(self) -> str:
        return self._license_tier

    @Property(str, notify=licenseChanged)
    def licenseExpiry(self) -> str:
        return self._license_expiry

    @Property(str, notify=licenseChanged)
    def licenseCustomer(self) -> str:
        return self._license_customer

    @Property(str, notify=licenseChanged)
    def licenseError(self) -> str:
        return self._license_error

    @Property(str, notify=licenseChanged)
    def licenseAlgorithm(self) -> str:
        return self._license_algorithm

    @Property("QVariantList", notify=licenseChanged)
    def licenseFeatures(self) -> List[str]:
        return self._license_features

    @Slot(str, result=bool)
    def licenseHasFeature(self, feat: str) -> bool:
        return license_engine.license_has_feature(feat)

    @Slot(result=str)
    def openLicenseFile(self) -> str:
        """Opens native file picker to load .lic / .key / .txt license certificate."""
        try:
            from PySide6.QtWidgets import QFileDialog, QApplication
            active_win = QApplication.activeWindow()
            path, _ = QFileDialog.getOpenFileName(
                active_win,
                "Select Hemoglyph License File",
                "",
                "License Files (*.lic *.key *.txt);;All Files (*.*)"
            )
            if path:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                return content
        except Exception as exc:
            logger.warning("openLicenseFile error: %s", exc)
        return ""

    @Property(bool, notify=remoteBlockChanged)
    def isRemotelyBlocked(self) -> bool:
        return self._is_remotely_blocked

    @Property(str, notify=remoteBlockChanged)
    def remoteBlockReason(self) -> str:
        return self._remote_block_reason

    @Property(bool, notify=sentinelStatusChanged)
    def sentinelOnline(self) -> bool:
        return self._sentinel_online

    @Slot(str, result=bool)
    def activateLicense(self, key_str: str) -> bool:
        ok, msg, payload = license_engine.verify_license_token(key_str, self._license_mid)
        if ok:
            clean_token = license_engine.extract_license_token(key_str)
            license_engine.save_installed_license(clean_token)
            self._license_valid = True
            self._is_remotely_blocked = False
            self._license_tier = payload.get("t", "Standard")
            self._license_customer = payload.get("u", "")
            self._license_algorithm = "Military-Grade RSA-4096 / SHA-512" if (clean_token.startswith("HGLIC4K-") or clean_token.startswith("HGLIC-RSA4K-")) else ("Asymmetric RSA-2048" if clean_token.startswith("HGLIC-RSA-") else "Legacy HMAC-SHA256")
            self._license_features = list(payload.get("feats", []))
            exp = payload.get("e", "PERPETUAL")
            if exp != "PERPETUAL" and str(exp).isdigit():
                exp = time.strftime("%Y-%m-%d", time.gmtime(int(exp)))
            self._license_expiry = str(exp)
            self._license_error = ""
            self.remoteBlockChanged.emit()
            self.licenseChanged.emit()
            logger.info("✅ License activated: %s (%s, %s)", self._license_customer, self._license_tier, self._license_algorithm)
            return True
        else:
            self._license_error = msg
            self.licenseChanged.emit()
            logger.warning("❌ License activation failed: %s", msg)
            return False

    def _check_pending_remote_block(self) -> None:
        """Executed on GUI thread every 500ms to guarantee zero dropped block events."""
        if self._pending_remote_block and not self._is_remotely_blocked:
            r = self._pending_remote_block
            self._pending_remote_block = None
            self._handle_remote_revocation(r)
            return

        # Check local revocation marker
        if not self._is_remotely_blocked:
            is_revoked, reason = license_engine.is_revoked_locally()
            if is_revoked:
                self._handle_remote_revocation(reason)

    def _start_sentinel_heartbeat_worker(self) -> None:
        """Start high-velocity daemon thread to sync license status with Sentinel platform."""
        def _heartbeat_loop():
            time.sleep(0.5)
            first_log = True
            while True:
                try:
                    u_name = self._userName or ""
                    u_email = self._userEmail or ""
                    if not u_name or not u_email:
                        try:
                            from paygah_dade import gereftan_ettesal
                            conn = gereftan_ettesal()
                            cur = conn.cursor()
                            cur.execute("SELECT full_name, email FROM users ORDER BY last_login DESC, id DESC LIMIT 1")
                            row = cur.fetchone()
                            conn.close()
                            if row:
                                if not u_name and row[0]:
                                    u_name = str(row[0])
                                if not u_email and row[1]:
                                    u_email = str(row[1])
                        except Exception:
                            pass

                    connected, status, data = license_engine.send_remote_heartbeat(
                        user_name=u_name,
                        user_email=u_email
                    )
                    if connected != self._sentinel_online:
                        self._sentinel_online = connected
                        self.sentinelStatusChanged.emit()
                        if connected:
                            logger.info("🟢 [SENTINEL LINK] Connected to Sentinel Dashboard (MID: %s)", self._license_mid)
                        else:
                            logger.info("⚪ [SENTINEL LINK] Disconnected (Operating in local CDS mode)")

                    if connected:
                        if status == "revoked":
                            reason = data.get("reason", "License suspended by administrator.")
                            logger.warning("🚨 [HEARTBEAT THREAD] Received revocation: %s", reason)
                            self._pending_remote_block = reason
                            self.remoteRevokeSignal.emit(reason)
                        elif status == "active" and self._is_remotely_blocked:
                            logger.info("🟢 [HEARTBEAT THREAD] Received restoration!")
                            self._pending_remote_block = None
                            self.remoteRestoreSignal.emit()
                    else:
                        if first_log:
                            err_msg = data.get("error", "unreachable")
                            logger.info("ℹ️ Sentinel link idle at %s (%s). Working in local CDS mode.", license_engine.get_sentinel_url(), err_msg)
                            first_log = False
                except Exception as exc:
                    if self._sentinel_online:
                        self._sentinel_online = False
                        self.sentinelStatusChanged.emit()
                    logger.debug("Sentinel heartbeat exception: %s", exc)

                time.sleep(15.0 if self._sentinel_online else 60.0)

        t = threading.Thread(target=_heartbeat_loop, daemon=True, name="SentinelHeartbeatWorker")
        t.start()

    def _handle_remote_revocation(self, reason: str) -> None:
        """Invoked on GUI thread when remote kill-switch is activated."""
        if not self._is_remotely_blocked:
            logger.warning("🚨 [GUI THREAD] BRUTAL REMOTE KILL-SWITCH TRIGGERED: %s", reason)
            self._is_remotely_blocked = True
            self._remote_block_reason = reason
            self._license_valid = False
            self._logged_in = False

            # Emergency alert sound
            try:
                QGuiApplication.beep()
            except Exception:
                pass

            # Purge active patient data in memory
            self._patient_current = {}
            self._current_analysis = {}

            # Instantly display lockdown shield and hide main workspace
            self.loggedInChanged.emit()
            self.remoteBlockChanged.emit()
            self.licenseChanged.emit()
            self.toast.emit("error", f"ACCESS TERMINATED: {reason}")

    def _handle_remote_restoration(self) -> None:
        """Invoked when administrator restores access."""
        if self._is_remotely_blocked:
            logger.info("🟢 Central command restored access!")
            self._is_remotely_blocked = False
            self._remote_block_reason = ""
            self._refresh_license()
            self.remoteBlockChanged.emit()
            self.licenseChanged.emit()
            self.toast.emit("success", "Workstation access restored by administrator.")

    @Slot()
    def copyMachineId(self) -> None:
        try:
            from PySide6.QtGui import QGuiApplication
            clip = QGuiApplication.clipboard()
            if clip:
                clip.setText(self._license_mid)
        except Exception as exc:
            logger.warning("Clipboard copy failed: %s", exc)

    @Slot(str)
    def copyText(self, val: str) -> None:
        try:
            from PySide6.QtGui import QGuiApplication
            clip = QGuiApplication.clipboard()
            if clip:
                clip.setText(str(val))
        except Exception as exc:
            logger.warning("Clipboard copy failed: %s", exc)

    @Slot(result=bool)
    def checkLicense(self) -> bool:
        self._refresh_license()
        return self._license_valid

    @Property(str, notify=ocrApiKeyChanged)
    def ocrApiKey(self) -> str:
        return self._ocr_api_key

    @Property(bool, notify=ocrApiKeyChanged)
    def hasOcrApiKey(self) -> bool:
        return bool(self._ocr_api_key and len(self._ocr_api_key.strip()) > 5)

    @Slot(str)
    def setOcrApiKey(self, key_str: str) -> None:
        key_str = key_str.strip()
        self._ocr_api_key = key_str
        self._settings.setValue("ocrApiKey", key_str)
        try:
            self._settings.sync()
        except Exception:
            pass
        if key_str:
            os.environ["OCR_API_KEY"] = key_str
            os.environ["GROQ_API_KEY"] = key_str
        else:
            os.environ.pop("OCR_API_KEY", None)
            os.environ.pop("GROQ_API_KEY", None)

        # 1. Persist to ~/.hemoglyph/config.json
        try:
            user_dir = Path.home() / ".hemoglyph"
            user_dir.mkdir(parents=True, exist_ok=True)
            cfg_file = user_dir / "config.json"
            cfg = {}
            if cfg_file.exists():
                try:
                    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            cfg["ocrApiKey"] = key_str
            cfg_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Could not persist key to ~/.hemoglyph/config.json: {exc}")

        # 2. Persist to .env in root and app directories
        for cand_dir in (_determine_root(), Path(__file__).resolve().parent):
            try:
                env_file = cand_dir / ".env"
                lines = []
                if env_file.exists():
                    lines = [l for l in env_file.read_text(encoding="utf-8").splitlines()
                             if not l.startswith("OCR_API_KEY=") and not l.startswith("GROQ_API_KEY=")]
                if key_str:
                    lines.append(f"OCR_API_KEY={key_str}")
                    lines.append(f"GROQ_API_KEY={key_str}")
                env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            except Exception as exc:
                logger.debug(f"Could not persist key to .env: {exc}")

        # 3. Also persist to user stable profile if logged in
        if getattr(self, "_current_user_id", None) is not None:
            try:
                self._current_profile["ocr_api_key"] = key_str
                self._current_profile["groq_api_key"] = key_str
                blob = json.dumps(self._current_profile, ensure_ascii=False)
                update_user_profile(self._current_user_id, stable_profile=blob)
            except Exception as exc:
                logger.debug(f"Could not persist key to DB profile: {exc}")

        self._reinit_ocr_pipeline()
        self.ocrApiKeyChanged.emit()

    def _reinit_ocr_pipeline(self) -> None:
        if self.service is None:
            return
        try:
            from ocr import BloodLabPipeline
            api_key = self._ocr_api_key or os.getenv("OCR_API_KEY") or os.getenv("GROQ_API_KEY") or None
            backend_name = "vision" if api_key else "tesseract"
            self.service.ocr = BloodLabPipeline(
                api_key=api_key,
                registry=self.service.feature_registry,
                registry_path=self.service.feature_registry_path,
                enable_derived=False,
                backend=backend_name,
                language="fa",
                vision_model=os.getenv("OCR_VISION_MODEL") or "qwen/qwen3.8-27b",
            )
            _b = self.service.ocr.backend
            if hasattr(_b, "preprocess"):
                _b.preprocess = False
            if hasattr(_b, "timeout"):
                _b.timeout = 90
            if getattr(_b, "name", "") == "vision":
                _b.base_url = os.getenv("OCR_BASE_URL", "https://api.groq.com/openai/v1")
                try:
                    from openai import OpenAI
                    _b._client = OpenAI(api_key=_b.api_key, base_url=_b.base_url,
                                        timeout=_b.timeout, max_retries=1)
                except Exception:
                    pass
            self._set_ocr_khata("")
            logger.info("OCR Pipeline updated with backend: %s", getattr(_b, "name", "unknown"))
        except Exception as exc:
            logger.warning("OCR reinit failed: %s", exc)

    @Property(bool, notify=chatAvailableChanged)
    def chatAvailable(self) -> bool:
        return self._chat_available

    @Property(str, notify=ocrErrorChanged)
    def ocrError(self) -> str:
        return self._ocr_error

    @Property(int, notify=readyChanged)
    def featureCount(self) -> int:
        return len(self.features)

    @Property(int, notify=readyChanged)
    def diseaseCount(self) -> int:
        return len(self.disease_payload.get("diseases") or {})

    @Property(int, notify=readyChanged)
    def ruleCount(self) -> int:
        return len(self.disease_payload.get("rules") or {})

    @Property(int, notify=readyChanged)
    def sourceCount(self) -> int:
        return len(self.disease_payload.get("guideline_sources") or {})

    @Property(int, notify=currentAnalysisIdChanged)
    def currentAnalysisId(self) -> int:
        return int(self._current_analysis_db_id or 0)

    @Property(int, notify=currentChatSessionIdChanged)
    def currentChatSessionId(self) -> int:
        return self._currentChatSessionId or 0

    @Property(str, notify=guidelinesFocusChanged)
    def guidelineFocus(self) -> str:
        return self._guidelineFocus


    @Property(bool, notify=readyChanged)
    def ready(self) -> bool:
        return self._ready

    @Property(str, notify=bootstrapTextChanged)
    def bootstrapText(self) -> str:
        return self._bootstrapText

    @Property(str, notify=readyChanged)
    def bootstrapError(self) -> str:
        return self._bootstrapError

    @Property("QVariantList", notify=featureCategoriesChanged)
    def featureCategories(self) -> List[str]:
        return self._featureCategories

    @Property('QVariantList', notify=featureCategoriesChanged)
    def featureOptions(self) -> List[str]:
        return self._featureOptions

    @Property('QVariantList', notify=riskCatalogChanged)
    def riskModelCatalog(self) -> List[Dict]:
        return self._riskCatalog

    @Slot(str, result="QVariantList")
    def featureOptionsFor(self, prefix: str) -> List[str]:
        p = (prefix or "").strip().lower()
        out: List[str] = []
        if p:
            for fid in self.features:
                if p in fid.lower():
                    out.append(fid)
                    if len(out) >= 50:
                        break
        if not out:
            out = self._featureOptions[:50]
        if prefix and prefix not in out:
            out.insert(0, prefix)
        return out

    @Property("QVariantList", notify=featureRowsChanged)
    def featureRows(self) -> List[Dict]:
        return self._featureRows

    @Property('QVariantList', notify=manualRowsChanged)
    def manualRows(self) -> List[Dict]:
        return self._manualRows

    @Property("QVariantList", notify=reviewRowsChanged)
    def reviewRows(self) -> List[Dict]:
        return self._reviewRows

    @Property('QVariantList', notify=referenceRowsChanged)
    def referenceRows(self) -> List[Dict]:
        return self._referenceRows

    @Property("QVariantList", notify=guidelineRowsChanged)
    def guidelineRows(self) -> List[Dict]:
        return self._guidelineRows

    @Property("QVariantList", notify=measuredRowsChanged)
    def measuredRows(self) -> List[Dict]:
        return self._measuredRows

    @Property("QVariantList", notify=derivedRowsChanged)
    def derivedRows(self) -> List[Dict]:
        return self._derivedRows

    @Property('QVariantList', notify=clinicalRowsChanged)
    def clinicalRows(self) -> List[Dict]:
        return self._clinicalRows

    @Property("QVariantList", notify=riskRowsChanged)
    def riskRows(self) -> List[Dict]:
        return self._riskRows

    @Property('QVariantList', notify=historyRowsChanged)
    def historyRows(self) -> List[Dict]:
        return self._historyRows

    @Property("QVariantList", notify=globalSearchRowsChanged)
    def globalSearchRows(self) -> List[Dict]:
        return self._globalSearchRows

    @Property(str, notify=executiveSummaryChanged)
    def executiveSummary(self) -> str:
        return self._executiveSummary

    @Property(str, notify=triageChanged)
    def primaryClinicalStatus(self) -> str:
        return self._primaryClinicalStatus

    @Property("QVariantList", notify=triageChanged)
    def tier1CriticalRows(self) -> List[Dict]:
        return self._tier1Rows

    @Property("QVariantList", notify=triageChanged)
    def tier2ActionableRows(self) -> List[Dict]:
        return self._tier2Rows

    @Property("QVariantList", notify=triageChanged)
    def tier3PhysiologicalRows(self) -> List[Dict]:
        return self._tier3Rows

    @Property(int, notify=triageChanged)
    def tier1Count(self) -> int:
        return len(self._tier1Rows)

    @Property(int, notify=triageChanged)
    def tier2Count(self) -> int:
        return len(self._tier2Rows)

    @Property(int, notify=triageChanged)
    def tier3Count(self) -> int:
        return len(self._tier3Rows)

    @Property(str, notify=triageChanged)
    def targetPopulationInfo(self) -> str:
        return self._targetPopulationInfo

    @Property('QVariantList', notify=chatHistoryRowsChanged)
    def chatHistoryRows(self) -> List[Dict]:
        return self._chatHistoryRows

    @Property("QVariantList", notify=chatAnalysisOptionsChanged)
    def chatAnalysisOptions(self) -> List[Dict]:
        opts = []

        if self._hasCurrentAnalysis:
            opts.append({
                'testId': int(self._current_analysis_db_id or 0),
                'label': "Current analysis" + ('' if self._current_analysis_db_id else " (unsaved)"),
            })

        for r in self._historyRows:
            try:
                tid = int(r["testId"])
            except Exception:
                continue

            if tid and tid == int(self._current_analysis_db_id or 0):
                continue

            opts.append({
                "testId": tid,
                "label": (r.get('date') or "") + " — " + (r.get("title") or "Analysis")
            })

        return opts
    @Property("QVariantList", notify=patientContextRowsChanged)
    def patientContextRows(self) -> List[Dict]:
        return self._patient_context_rows

    @Property("QVariantList", notify=patientRowsChanged)
    def patientRows(self) -> List[Dict]:
        return []

    @Property("QVariantMap", notify=activePatientChanged)
    def activePatient(self) -> Dict[str, Any]:
        return {}

    @Slot(str)
    def searchPatients(self, query: str = "") -> None:
        pass

    @Property("QVariantList", notify=riskRowsChanged)
    def filteredRiskRows(self) -> List[Dict]:
        return [r for r in self._riskRows
                if str(r.get('status', '')).startswith("Evaluated")]

    # FIX U1: skipped-model layers were computed but unreachable from QML
    # (ResultsPage only saw filteredRiskRows; legacy counts hardcoded 0).
    @Property("QVariantList", notify=riskRowsChanged)
    def insufficientRiskRows(self) -> List[Dict]:
        return [r for r in self._riskRows
                if r.get("status") == "Insufficient Data"]

    @Property("QVariantList", notify=riskRowsChanged)
    def alreadyDiagnosedRows(self) -> List[Dict]:
        return [r for r in self._riskRows
                if r.get("status") == "AlreadyDiagnosed"]

    @Property(int, notify=riskRowsChanged)
    def insufficientRiskCount(self) -> int:
        return sum(1 for r in self._riskRows
                   if r.get("status") == "Insufficient Data")

    @Property(int, notify=riskRowsChanged)
    def alreadyDiagnosedCount(self) -> int:
        return sum(1 for r in self._riskRows
                   if r.get("status") == "AlreadyDiagnosed")

    @Property("QVariantList", notify=resultWarningsChanged)
    def resultWarnings(self) -> List[str]:
        return self._resultWarnings

    @Property("QVariantList", notify=criticalAlertsChanged)
    def criticalAlerts(self) -> List[Dict]:
        return self._criticalAlerts

    def _set_satrha(self, attr: str, signal: Signal, rows: List[Dict]) -> None:
        if len(rows) > _MAX_MIRROR_ROWS:
            setattr(self, attr, list(rows[:_MAX_MIRROR_ROWS]))
        else:
            setattr(self, attr, list(rows))
        signal.emit()

    def _emit_tahlil_options(self) -> None:
        self.chatAnalysisOptionsChanged.emit()

    def _set_ocr_khata(self, msg: str) -> None:
        if self._ocr_error != msg:
            self._ocr_error = msg
            self.ocrErrorChanged.emit()

    def _set_busy(self, text: str = "") -> None:
        self._busy = True
        self._busyText = text
        self.busyChanged.emit()
        self.busyTextChanged.emit()

    def _unset_busy(self) -> None:
        self._busy = False
        self._busyText = ""
        self.busyChanged.emit()
        self.busyTextChanged.emit()

    def _workspace_dirty(self) -> bool:
        return bool(self._hasCurrentAnalysis or self._manual or self._confirmed
                   or self._review.get("session") or self._selectedFile
                   or self._current_result is not None)

    @Slot()
    def toggleSidebar(self) -> None:
        self._sidebarCollapsed = not self._sidebarCollapsed
        self.sidebarCollapsedChanged.emit()

    @Slot(str)
    def navigate(self, page: str) -> None:
        if not self._require_license():
            return
        if page == 'newAnalysis' and self._workspace_dirty():
            self.newAnalysis()
            return
        if self._currentPage != page:
            self._currentPage = page
            self.currentPageChanged.emit()
        if page == "chat":
            self.loadChatHistory()
            self._probe_chat()
            if (self.ai is not None and self._hasCurrentAnalysis
                    and not self._cached_summary):
                self._gen_kholase_async(self._chat_lang)
        elif page == "manual" and not self._page_loaded.get("manual"):
            self._page_loaded['manual'] = True
            self.searchFeatures("", "All")
        elif page == "guidelines" and not self._page_loaded.get("guidelines"):
            self._page_loaded["guidelines"] = True
            self.searchDiseases("")
        elif page == "references" and not self._page_loaded.get("references"):
            self._page_loaded["references"] = True
            self.searchReferences("")
        elif page == "history":
            self.load_history()
    @Slot()
    def newAnalysis(self) -> None:
        try:
            self._autosave_chat()
        except Exception:
            pass

        self._extract_gen += 1
        self._manual.clear()
        self._confirmed.clear()
        self._context = {}
        self._current_result = None
        self._review = {'session': None}
        self._last_risks = []
        self._patient_context_rows = []
        self.patientContextRowsChanged.emit()
        self._ocr_auto_rejected = 0
        self.ocrAutoRejectedChanged.emit()
        self._hasCurrentAnalysis = False
        self._analysisSaved = False
        self._cached_summary = ""
        self._current_analysis_db_id = None
        self._selectedFile = ""
        self.selectedFileChanged.emit()
        self._set_ocr_khata("")
        self._currentChatSessionId = None
        self.currentChatSessionIdChanged.emit()
        self.currentAnalysisIdChanged.emit()
        manualModel.clear()
        reviewModel.clear()
        measuredModel.clear()
        derivedModel.clear()
        clinicalModel.clear()
        riskModel.clear()
        insufficientModel.clear()
        conflictingModel.clear()

        self._set_satrha("_manualRows", self.manualRowsChanged, [])
        self._set_satrha("_reviewRows", self.reviewRowsChanged, [])
        self._set_satrha("_measuredRows", self.measuredRowsChanged, [])
        self._set_satrha("_derivedRows", self.derivedRowsChanged, [])
        self._set_satrha("_clinicalRows", self.clinicalRowsChanged, [])
        self._set_satrha("_riskRows", self.riskRowsChanged, [])
        self._resultWarnings = []
        self._criticalAlerts = []
        self._tier1Rows = []
        self._tier2Rows = []
        self._tier3Rows = []
        self._executiveSummary = ""
        self._targetPopulationInfo = ""
        self._primaryClinicalStatus = "PHYSIOLOGICAL_BASELINE"
        self.triageChanged.emit()
        self.executiveSummaryChanged.emit()

        self._measuredCount = 0
        self._derivedCount = 0
        self._clinicalCount = 0
        self._urgentCount = 0
        self._insufficientCount = 0
        self._conflictingCount = 0

        if self.ai is not None:
            try:
                self.ai.reset(clear_analysis=True)
            except Exception:
                pass

        self.hasCurrentAnalysisChanged.emit()
        self.analysisSavedChanged.emit()
        self.measuredCountChanged.emit()
        self.derivedCountChanged.emit()
        self.clinicalCountChanged.emit()
        self.urgentCountChanged.emit()
        self.insufficientCountChanged.emit()
        self.conflictingCountChanged.emit()
        self.resultWarningsChanged.emit()
        self.criticalAlertsChanged.emit()
        self._emit_tahlil_options()
        self.searchFeatures("", "All")
        self.analysisReset.emit()

        if self._currentPage != "newAnalysis":
            self._currentPage = 'newAnalysis'
            self.currentPageChanged.emit()

        self.toast.emit("success", "Workspace cleared — ready for a new analysis.")

    # FIX UPL2/UPL3: selective clears — old clearCurrentInputs nuked everything
    @Slot()
    def clearCurrentInputs(self) -> None:
        # Legacy full clear — kept for compatibility but now delegates
        self._manual.clear()
        manualModel.clear()
        self._set_satrha("_manualRows", self.manualRowsChanged, [])
        reviewModel.clear()
        self._set_satrha("_reviewRows", self.reviewRowsChanged, [])
        self._review = {"session": None}
        self._selectedFile = ""
        self.selectedFileChanged.emit()
        self.analysisReset.emit()
        self.toast.emit("success", "All current inputs cleared.")
        self._ocr_auto_rejected = 0
        self.ocrAutoRejectedChanged.emit()

    @Slot()
    def clearReviewOnly(self) -> None:
        reviewModel.clear()
        self._set_satrha("_reviewRows", self.reviewRowsChanged, [])
        self._review = {"session": None}
        self._ocr_auto_rejected = 0
        self.ocrAutoRejectedChanged.emit()
        self.toast.emit("info", "Extracted review cleared — manual entries kept.")

    @Slot()
    def clearManualOnly(self) -> None:
        self._manual.clear()
        manualModel.clear()
        self._set_satrha("_manualRows", self.manualRowsChanged, [])
        self.toast.emit("info", "Manual entries cleared — review kept.")

    @Slot()
    def clearFileOnly(self) -> None:
        self._selectedFile = ""
        self.selectedFileChanged.emit()
        self.clearReviewOnly()

    # FIX M1: missing slots for ManualPage — Undo/Redo/Save/Import/Export
    @Slot(list)
    def restoreManualState(self, state: List[Dict]) -> None:
        try:
            new_manual = {}
            for row in (state or []):
                fid = row.get("featureId") or row.get("feature_id")
                if not fid:
                    continue
                meta = self.features.get(fid) or {}
                new_manual[fid] = {
                    'feature_id': fid,
                    "value": row.get("value"),
                    'unit': row.get("unit") or (meta.get("units") or {}).get("canonical"),
                    "confirmed": True,
                    "source": "manual"
                }
            self._manual = new_manual
            self.beroozresani_manual_model()
        except Exception as exc:
            logger.warning(f"restoreManualState failed: {exc}")

    @Slot()
    def saveManualSession(self) -> None:
        try:
            # Save to QSettings as JSON
            data = {
                "manual": self._manual,
                "context": getattr(self, "_context", {}),
                "ts": __import__("datetime").datetime.utcnow().isoformat()
            }
            self._settings.setValue("manualSession", json.dumps(data, ensure_ascii=False))
            self.toast.emit("success", "Session saved locally.")
        except Exception as exc:
            self.toast.emit("error", f"Save failed: {exc}")

    @Slot(str)
    def importFromFile(self, path: str) -> None:
        try:
            local = QUrl(path).toLocalFile() if str(path).startswith('file:') else str(path)
            p = Path(local)
            if not p.is_file():
                self.toast.emit("error", f"File not found: {local}")
                return
            raw = json.loads(p.read_text(encoding="utf-8"))
            # Support both our export format and plain manualRows
            if isinstance(raw, dict) and "measurements" in raw:
                rows = raw.get("measurements") or []
                ctx = raw.get("context") or {}
            elif isinstance(raw, dict) and "manual" in raw:
                # internal save format
                self._manual = raw.get("manual") or {}
                self._context = raw.get("context") or {}
                self.beroozresani_manual_model()
                self.toast.emit("success", "Session imported.")
                return
            else:
                rows = raw if isinstance(raw, list) else []
                ctx = {}
            # rebuild _manual
            new_manual = {}
            for r in rows:
                fid = r.get("featureId") or r.get("feature_id")
                if not fid:
                    continue
                new_manual[fid] = {
                    'feature_id': fid,
                    "value": r.get("value"),
                    'unit': r.get("unit"),
                    "confirmed": True,
                    "source": "manual"
                }
            self._manual = new_manual
            if ctx:
                self._context = dict(ctx)
            self.beroozresani_manual_model()
            self.toast.emit("success", f"Imported {len(new_manual)} measurements.")
        except Exception as exc:
            logger.exception("importFromFile failed")
            self.toast.emit("error", f"Import failed: {exc}")

    @Slot(str, str)
    def exportToFile(self, json_str: str, filename: str) -> None:
        if not self._require_license():
            return
        try:
            # If json_str already contains full export, use it; otherwise build
            if json_str and json_str.strip().startswith("{"):
                content = json_str
            else:
                data = {
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                    "measurements": manualModel.get(),
                    "context": getattr(self, "_context", {}) or {}
                }
                content = json.dumps(data, ensure_ascii=False, indent=2)
            # filename may be a full path or just name; save to Documents or temp
            fname = (filename or "measurements.json").strip() or "measurements.json"
            # If filename is just a name, put in home
            if "/" not in fname and "\\" not in fname:
                out_path = Path.home() / fname
            else:
                local = QUrl(fname).toLocalFile() if str(fname).startswith('file:') else fname
                out_path = Path(local)
            out_path.write_text(content, encoding="utf-8")
            self.toast.emit("success", f"Exported to {out_path}")
        except Exception as exc:
            logger.exception("exportToFile failed")
            self.toast.emit("error", f"Export failed: {exc}")

    @Slot(result="QVariantMap")
    def getLastContext(self) -> Dict[str, Any]:
        return dict(getattr(self, "_context", {}) or {})

    @Slot(dict)
    def saveContext(self, ctx: Dict[str, Any]) -> None:
        if isinstance(ctx, dict):
            self._context = dict(ctx)

    @Slot()
    def editAnalysis(self) -> None:
        if not self._hasCurrentAnalysis:
            self.toast.emit("warning", 'No analysis to edit. Run an analysis first.')
            return

        self._manual = {fid: dict(rec) for fid, rec in self._confirmed.items()
                       if isinstance(rec, dict)}
        # FIX E6: also restore context so re-run is identical
        self._context = dict(getattr(self, "_context", {}) or {})
        self.beroozresani_manual_model()
        self.navigate("manual")
        self.toast.emit('info', "Editing confirmed measurements. Re-run to apply changes.")

    @Slot()
    def logout(self) -> None:
        try:
            self.newAnalysis()
        except Exception:
            pass
        self._loggedIn = False
        self._current_user_id = None
        self._userName = ""
        self._userEmail = ""
        self._historyRows = []
        self._chatHistoryRows = []
        try:
            historyModel.clear()
        except Exception:
            pass
        self.historyRowsChanged.emit()
        self.chatHistoryRowsChanged.emit()
        self.loggedInChanged.emit()
        self.userNameChanged.emit()
        self.navigate("home")


    def _next_task_id(self) -> str:
        self._task_counter += 1
        return f"task_{self._task_counter}"

    def _ejra_async(self, fn: Callable, on_ok: Callable, on_err: Optional[Callable] = None) -> None:
        task_id = self._next_task_id()
        self._handlers[task_id] = on_ok
        self._err_handlers[task_id] = on_err

        def _thread_main():
            try:
                payload = fn()
            except Exception as exc:
                traceback.print_exc()
                self._async_hub.failed.emit(task_id, f"{type(exc).__name__}: {exc}")
                return
            self._async_hub.done.emit(task_id, payload)

        t = threading.Thread(target=_thread_main, daemon=True)
        t.start()

    def _dispatch_done(self, task_id: str, payload: Any) -> None:
        handler = self._handlers.pop(task_id, None)
        self._err_handlers.pop(task_id, None)

        if handler:
            try:
                handler(payload)
            except Exception as exc:
                logger.exception(f"Handler error for {task_id}")
                self._unset_busy()
                self.toast.emit("error", f"Unexpected error: {exc}")

    def _dispatch_failed(self, task_id: str, message: str) -> None:
        handler = self._err_handlers.pop(task_id, None)
        self._handlers.pop(task_id, None)

        if handler:
            handler(message)
        else:
            self._unset_busy()
            self.toast.emit("error", message)


    @Slot(str, result="QVariantMap")
    def assessPassword(self, text: str) -> Dict[str, Any]:
        score, missing = 0, []

        if text and len(text) >= 8:
            score += 1
        else:
            missing.append("8+ characters")

        if re.search(r"[A-Z]", text):
            score += 1
        else:
            missing.append("uppercase")

        if re.search(r"[0-9]", text):
            score += 1
        else:
            missing.append("a number")

        if re.search(r"[^A-Za-z0-9]", text):
            score += 1
        else:
            missing.append("a symbol")

        return {"score": score, "strong": score >= 4, "missing": missing}

    @Slot(str, str, str, str, str)
    @Slot(str, str, str, str, str, str)
    def register(self, name: str, email: str, password: str,
                confirm: str, birth: str, sex: str = "Female") -> None:
        if not self._require_license():
            return
        email = (email or "").strip().lower()
        name = (name or "").strip()
        password = (password or "").strip()
        confirm = (confirm or "").strip()

        if not name or len(name) < 2:
            self.toast.emit("error", "Enter your full name.")
            return

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            self.toast.emit("error", "Enter a valid email address.")
            return

        if not password or len(password) < 8:
            self.toast.emit("error", "Password must be at least 8 characters.")
            return

        if not self.assessPassword(password)["strong"]:
            self.toast.emit("error",
                          "Password is too weak. Use upper/lower, a number and a symbol.")
            return

        if password != confirm:
            self.toast.emit('error', "Passwords do not match.")
            return

        try:
            hashed = hash_password(password)
            uid = register_user(email, hashed, name, birth_date=birth or None, sex=sex)
        except Exception as exc:
            logger.exception("Registration exception:")
            self.toast.emit("error", f"Could not create account: {exc}")
            return

        if uid is None:
            self.toast.emit("error", "An account with this email already exists.")
            return

        logger.info(f"Registration successful for {email} (uid={uid})")
        self._set_remembered(email)
        self._login_by_id(uid, name, email, birth, sex)

    @Slot(str, str)
    def login(self, email: str, password: str) -> None:
        if not self._require_license():
            return
        email = (email or '').strip().lower()
        password = (password or "").strip()

        logger.info(f"Login attempt for: {email}")

        user = get_user_by_email(email)
        if not user:
            logger.warning(f"Login failed: No account found in database for '{email}'")
            self.toast.emit("error", "No account found with this email. Click 'Create an account' below.")
            return

        try:
            verified = verify_password(password, user.get("password_hash"))
        except Exception:
            logger.exception("verify_password threw an exception:")
            self.toast.emit("error", "Internal error during password verification.")
            return

        if not verified:
            self.toast.emit("error", "Incorrect password for this account.")
            return

        logger.info(f"Login successful for {email}")
        # Legacy unsalted SHA-256 hashes are upgraded to PBKDF2-HMAC-SHA256
        # (310k iterations, random salt) the first time they verify correctly.
        try:
            if upgrade_password_hash(user["id"], password, user.get("password_hash") or ""):
                logger.info("Password hash upgraded to PBKDF2 for user id %s", user["id"])
        except Exception:
            logger.exception("Password hash upgrade failed (login continues):")
        self._set_remembered(email)
        self._login_by_id(user["id"], user.get("full_name", ""), email,
                         user.get("birth_date"), user.get("sex"))

    def _login_by_id(self, uid: int, name: str, email: str,
                    birth: Optional[str], sex: Optional[str]) -> None:
        self._current_user_id = uid
        self._userName = name or (email.split("@")[0])
        self._userEmail = email
        self._current_profile = self._profile_from_db(birth, sex)
        self._loggedIn = True

        # Keep current profile in sync with system OCR API key setting
        if self._current_profile:
            self._current_profile["ocr_api_key"] = self._ocr_api_key
            self._current_profile["groq_api_key"] = self._ocr_api_key
            try:
                blob = json.dumps(self._current_profile, ensure_ascii=False)
                update_user_profile(self._current_user_id, stable_profile=blob)
            except Exception:
                pass

        self.loggedInChanged.emit()
        self.userNameChanged.emit()

        QTimer.singleShot(0, lambda: self.navigate("home"))
        self.toast.emit("success", f"Welcome back, {self._userName}")

        QTimer.singleShot(200, self.load_history)
        QTimer.singleShot(250, self.loadChatHistory)

    def _set_remembered(self, email: str) -> None:
        self._rememberedEmail = email
        self._settings.setValue("rememberedEmail", email)
        self.rememberedEmailChanged.emit()

    @Slot()
    def forgetRememberedEmail(self) -> None:
        self._rememberedEmail = ""
        self._settings.remove("rememberedEmail")
        self.rememberedEmailChanged.emit()


    @staticmethod
    def _sen_from_birth(birth: Optional[str]) -> Optional[float]:
        if not birth:
            return None

        try:
            import datetime
            b = datetime.date.fromisoformat(str(birth))
            return max(0.0, (datetime.date.today() - b).days / 365.25)
        except Exception:
            return None

    def _profile_from_db(self, birth: Optional[str] = None,
                        sex: Optional[str] = None) -> Dict[str, Any]:
        user = get_user_by_email(self._userEmail) if self._userEmail else None
        birth = (user or {}).get("birth_date") if user else birth
        sex = (user or {}).get("sex") if user else sex
        age = (user or {}).get("age") if user else None

        if age is None:
            age = self._sen_from_birth(birth)

        prof = {
            "full_name": (user or {}).get("full_name") or '',
            "birth_date": birth or '',
            "sex": sex or "female",
            "weight_kg": (user or {}).get("weight"),
            'height_cm': (user or {}).get("height"),
            'age_years': age,
            "smoking": (user or {}).get("smoking"),
            'family_history_dm': (user or {}).get("family_history_dm"),
            "family_history_cad": (user or {}).get("family_history_cad")
        }


        try:
            stable = json.loads((user or {}).get("stable_profile") or "{}")
            if isinstance(stable, dict):
                prof.update(stable)
        except Exception:
            pass

        return prof

    @Slot(result="QVariantMap")
    def profile(self) -> Dict[str, Any]:
        if self._current_user_id is None:
            return self._current_profile
        self._current_profile = self._profile_from_db()
        return self._current_profile

    @Slot(dict)
    def saveProfile(self, data: Dict[str, Any]) -> None:
        self.saveStableProfile(data)

    @Slot(dict)
    def saveStableProfile(self, data: Dict[str, Any]) -> None:
        if self._current_user_id is None:
            self.toast.emit("warning", 'Sign in to save a profile.')
            return

        data_dict = dict(data or {})
        try:
            blob = json.dumps(data_dict, ensure_ascii=False)
            update_user_profile(self._current_user_id, stable_profile=blob, **data_dict)
        except Exception as exc:
            self.toast.emit("error", f"Could not save stable profile: {exc}")
            return

        self._current_profile.update(data_dict)
        if data_dict.get("full_name"):
            self._userName = str(data_dict["full_name"]).strip()
            self.userNameChanged.emit()
        elif data_dict.get("name"):
            self._userName = str(data_dict["name"]).strip()
            self.userNameChanged.emit()
        self.toast.emit("success", "Stable profile saved — applied automatically to every analysis.")

    @Slot(result="QVariantMap")
    def healthcheck(self) -> Dict[str, Any]:
        if self.service is None:
            return {"status": "starting", "ready": False,
                    "detail": self._bootstrapText,
                    "error": self._bootstrapError,
                    "app": {"name": APP_NAME, 'version': APP_VERSION}}
        hc = self.service.healthcheck()
        hc["app"] = {
            "name": APP_NAME,
            "version": APP_VERSION,
            "build": self._appBuild,
            "python": sys.version.split()[0]
        }
        hc["chat_configured"] = self.ai is not None
        hc["chat_available"] = self._chat_available
        hc["ocr_backend"] = getattr(self.service.ocr.backend, "name", "unknown")
        hc['prediction_engine'] = "validated-models v2" if HAS_NEW_PREDICTION else "legacy"
        hc["references_db"] = HAS_REFERENCES
        return hc


    @Slot(str, str)
    def searchFeatures(self, query: str, category: str) -> None:
        if not self._require_license():
            return
        q = (query or "").strip().lower()
        cat_sel = (category or "").strip() or "All"
        cache_key = f"{q}|{cat_sel}"

        cached = self._feature_search_cache.get(cache_key)
        if cached is None:
            cached = self._mohasebe_vizhegi_satrha(q, cat_sel)
            if len(self._feature_search_cache) > 128:
                self._feature_search_cache.clear()
            self._feature_search_cache[cache_key] = cached

        featureSearchModel.set_satrha(cached)
        self._set_satrha("_featureRows", self.featureRowsChanged, cached)

    def _mohasebe_vizhegi_satrha(self, q: str, cat_sel: str) -> List[Dict]:
        rows: List[Dict] = []
        features = self.features
        if not features:
            return rows

        limit = max(_MAX_BROWSE_ROWS, len(features))
        q_clean = (q or "").strip().lower()
        panel_key = _resolve_panel_key(cat_sel)

        # If search query is empty, return ALL features belonging to this panel
        # When filter is 'All Features', sort strictly alphabetically (A-Z)
        # For specific clinical panels, routine primary tests appear first
        if not q_clean:
            matching_fids = [f for f, m in features.items() if _is_feature_in_panel(f, m, panel_key)]
            if panel_key == "all":
                sorted_fids = sorted(
                    matching_fids,
                    key=lambda f: str((features[f].get("identity") or {}).get("display_name") or
                                      (features[f].get("identity") or {}).get("canonical_name") or f).strip().lower()
                )
            else:
                sorted_fids = sorted(
                    matching_fids,
                    key=lambda f: (
                        0 if f in _PRIMARY_FEATURE_ORDER else 1,
                        _PRIMARY_FEATURE_ORDER.get(f, 0),
                        str((features[f].get("identity") or {}).get("display_name") or f).lower()
                    )
                )
            for fid in sorted_fids:
                meta = features[fid]
                ident = meta.get("identity") or {}
                rows.append({
                    "featureId": _s(fid),
                    "featureName": _s(ident.get("display_name") or
                                      ident.get("canonical_name") or fid),
                    'category': _s(ident.get("category") or ''),
                    "unit": _s((meta.get("units") or {}).get("canonical")),
                    "status": _s(ident.get("status"))
                })
                if len(rows) >= limit:
                    break
            return rows

        scores: Dict[str, int] = {}

        # 1. Direct Clinical Search Expansions (instant highest priority if in selected panel)
        if q_clean in _CLINICAL_SEARCH_EXPANSIONS:
            for idx, target_fid in enumerate(_CLINICAL_SEARCH_EXPANSIONS[q_clean]):
                if target_fid in features and _is_feature_in_panel(target_fid, features[target_fid], panel_key):
                    scores[target_fid] = max(scores.get(target_fid, 0), 1000 - (idx * 20))

        # 2. Canonical alias resolution via naam_haye_vizhegi
        try:
            from naam_haye_vizhegi import resolve as _resolve_alias
            resolved_fid = _resolve_alias(q_clean)
            if resolved_fid and resolved_fid in features and _is_feature_in_panel(resolved_fid, features[resolved_fid], panel_key):
                scores[resolved_fid] = max(scores.get(resolved_fid, 0), 990)
        except Exception:
            pass

        # 3. FeatureRegistry OCR fuzzy index candidates
        if self.feature_registry is not None:
            try:
                for cand_fid, cand_score in self.feature_registry.index.candidates(q_clean):
                    if cand_fid in features and _is_feature_in_panel(cand_fid, features[cand_fid], panel_key):
                        scores[cand_fid] = max(scores.get(cand_fid, 0), int(cand_score * 850))
            except Exception as exc:
                logger.debug(f"registry candidate search failed: {exc}")

        # 4. Feature scan across registry metadata strictly within the selected panel
        for fid, meta in features.items():
            if not _is_feature_in_panel(fid, meta, panel_key):
                continue

            ident = meta.get("identity") or {}
            d_name = str(ident.get("display_name") or "").lower()
            c_name = str(ident.get("canonical_name") or "").lower()
            s_name = str(ident.get("short_name") or "").lower()
            fid_l = fid.lower()

            # Exact match on identifier or primary names
            if q_clean in (fid_l, d_name, c_name, s_name):
                scores[fid] = max(scores.get(fid, 0), 950)
                continue

            # Prefix match on name or ID
            if d_name.startswith(q_clean) or c_name.startswith(q_clean) or fid_l.startswith(q_clean):
                scores[fid] = max(scores.get(fid, 0), 800)
                continue

            # Word boundary prefix match
            words = set(d_name.split() + c_name.split() + fid_l.split('_'))
            if any(w.startswith(q_clean) for w in words):
                scores[fid] = max(scores.get(fid, 0), 750)
                continue

            # Substring match in primary names
            if q_clean in d_name or q_clean in c_name or q_clean in fid_l:
                scores[fid] = max(scores.get(fid, 0), 600)
                continue

            # Terminology and aliases
            term = meta.get("terminology") or {}
            abbrs = [str(a).lower() for a in (term.get("abbreviations") or [])]
            if q_clean in abbrs:
                scores[fid] = max(scores.get(fid, 0), 720)
                continue

            pref = term.get("preferred") or {}
            for lang in ("en", "fa"):
                p_val = str(pref.get(lang) or "").lower()
                if p_val:
                    if q_clean == p_val:
                        scores[fid] = max(scores.get(fid, 0), 720)
                        break
                    elif q_clean in p_val:
                        scores[fid] = max(scores.get(fid, 0), 550)
                        break

            syns = term.get("synonyms") or {}
            syn_list = []
            if isinstance(syns, list):
                syn_list = syns
            elif isinstance(syns, dict):
                syn_list = (syns.get("en") or []) + (syns.get("fa") or [])

            for s in syn_list:
                s_l = str(s).lower()
                if q_clean == s_l:
                    scores[fid] = max(scores.get(fid, 0), 500)
                    break
                elif q_clean in s_l and not s_l.startswith(('(fasting)', '(24h)', '(24 hour)', '(random)', '(spot)')):
                    scores[fid] = max(scores.get(fid, 0), 300)
                    break

        ranked_fids = sorted(
            scores.keys(),
            key=lambda f: (-scores[f], str((features[f].get("identity") or {}).get("display_name") or f))
        )

        for fid in ranked_fids:
            meta = features.get(fid) or {}
            ident = meta.get("identity") or {}
            if not _is_feature_in_panel(fid, meta, panel_key):
                continue

            rows.append({
                "featureId": _s(fid),
                "featureName": _s(ident.get("display_name") or
                                  ident.get("canonical_name") or fid),
                'category': _s(ident.get("category") or ''),
                "unit": _s((meta.get("units") or {}).get("canonical")),
                "status": _s(ident.get("status"))
            })
            if len(rows) >= limit:
                break

        return rows

    @Slot(str)
    def addManualFeature(self, feature_id: str) -> None:
        meta = self.features.get(feature_id)
        if not meta:
            self.toast.emit("error", f"Unknown feature: {feature_id}")
            return

        if feature_id in self._manual:
            self.toast.emit("info", f"Already added: {feature_id}")
            return

        self._manual[feature_id] = {
            'feature_id': feature_id,
            "value": None,
            'unit': (meta.get("units") or {}).get("canonical"),
            "confirmed": True,
            "source": "manual"
        }

        self.beroozresani_manual_model()

    @Slot(int, str, str)
    def updateManualRow(self, index: int, field: str, value: str) -> None:
        rows = manualModel.get()

        if not (0 <= index < len(rows)):
            return

        fid = rows[index].get("featureId")
        if not fid or fid not in self._manual:
            return

        value = "" if value is None else str(value)

        if field == "value":
            self._manual[fid]["value"] = value
        elif field == "unit":
            self._manual[fid]["unit"] = value
        # FIX M2: don't rebuild model on every keystroke — update in place
        try:
            # update ListModel row via set_satrha is heavy; use direct update if available
            manualModel._rows[index][field] = value
            idx = manualModel.index(index, 0)
            manualModel.dataChanged.emit(idx, idx)
            self._set_satrha("_manualRows", self.manualRowsChanged, manualModel.get())
        except Exception:
            pass

    @Slot(str, str)
    def updateManualValueByFeatureId(self, feature_id: str, value: str) -> None:
        if feature_id not in self._manual:
            return
        self._manual[feature_id]["value"] = "" if value is None else str(value)
        # FIX M2: keep model stable — only patch the row, don't reset whole model
        try:
            rows = manualModel.get()
            for i, r in enumerate(rows):
                if r.get("featureId") == feature_id:
                    manualModel._rows[i]["value"] = _fmt(self._manual[feature_id]["value"])
                    idx = manualModel.index(i, 0)
                    manualModel.dataChanged.emit(idx, idx)
                    break
            self._set_satrha("_manualRows", self.manualRowsChanged, manualModel.get())
        except Exception:
            pass

    @Slot(str, str)
    def updateManualUnitByFeatureId(self, feature_id: str, unit: str) -> None:
        if feature_id not in self._manual:
            return
        self._manual[feature_id]["unit"] = "" if unit is None else str(unit)
        try:
            rows = manualModel.get()
            for i, r in enumerate(rows):
                if r.get("featureId") == feature_id:
                    manualModel._rows[i]["unit"] = _s(self._manual[feature_id]["unit"])
                    idx = manualModel.index(i, 0)
                    manualModel.dataChanged.emit(idx, idx)
                    break
            self._set_satrha("_manualRows", self.manualRowsChanged, manualModel.get())
        except Exception:
            pass

    @Slot(str)
    def removeManualFeatureByFeatureId(self, feature_id: str) -> None:
        if not feature_id:
            return
        fid = str(feature_id).strip()
        if fid in self._manual:
            self._manual.pop(fid, None)
            self.beroozresani_manual_model()
            return
        for k in list(self._manual.keys()):
            if k.lower() == fid.lower():
                self._manual.pop(k, None)
                self.beroozresani_manual_model()
                return

    @Slot(int)
    @Slot(str)
    def removeManualFeature(self, target: Any) -> None:
        if target is None:
            return
        target_str = str(target).strip()
        if target_str in self._manual:
            self._manual.pop(target_str, None)
            self.beroozresani_manual_model()
            return

        try:
            idx = int(target)
        except (ValueError, TypeError):
            idx = -1

        rows = manualModel.get()
        if 0 <= idx < len(rows):
            fid = rows[idx].get("featureId")
            if fid and fid in self._manual:
                self._manual.pop(fid, None)
                self.beroozresani_manual_model()
                return

        keys = list(self._manual.keys())
        if 0 <= idx < len(keys):
            self._manual.pop(keys[idx], None)
            self.beroozresani_manual_model()

    def beroozresani_manual_model(self) -> None:
        rows = []

        for i, (fid, rec) in enumerate(self._manual.items()):
            ident = self.features.get(fid, {}).get("identity") or {}
            rows.append({
                "index": i,
                "featureId": _s(fid),
                "featureName": _s(ident.get("display_name") or
                                 ident.get("canonical_name") or fid),
                "category": _s(ident.get('category')),
                "value": _fmt(rec.get("value")),
                "unit": _s(rec.get("unit"))
            })

        manualModel.set_satrha(rows)
        self._set_satrha("_manualRows", self.manualRowsChanged, rows)


    @Slot(dict)
    def analyzeManual(self, context: Dict[str, Any]) -> None:
        # FIX M3/M4: collect which rows are missing/invalid before failing
        confirmed = {}
        empty_rows = []
        for fid, rec in self._manual.items():
            v = rec.get("value")
            if v is None or str(v).strip() == "":
                ident = self.features.get(fid, {}).get("identity") or {}
                empty_rows.append(ident.get("display_name") or fid)
                continue
            confirmed[fid] = {
                "value": v,
                'unit': rec.get("unit"),
                "confirmed": True,
                "source": "manual",
                "requires_confirmation": False
            }

        if not confirmed:
            if empty_rows:
                self.toast.emit("error", f"Enter values for: {', '.join(empty_rows[:3])}{'...' if len(empty_rows)>3 else ''}")
            else:
                self.toast.emit("error", "Enter at least one measurement value.")
            return

        if empty_rows:
            self.toast.emit("warning", f"{len(empty_rows)} empty row(s) ignored: {', '.join(empty_rows[:2])}")

        # FIX E6: persist context for editAnalysis / re-run
        self._context = dict(context) if isinstance(context, dict) else {}
        self._ejra_tahlil(confirmed, self._context)

    def _require_license(self) -> bool:
        """Enforces hard cryptographic license verification across all clinical and user operations."""
        if not getattr(self, "_license_valid", False):
            self.toast.emit("error", "Access Denied: Hemoglyph requires a valid RSA-4096 license key.")
            return False
        return True

    def _require_ready(self) -> bool:
        if not self._require_license():
            return False
        if self._ready and self.service is not None:
            return True
        self.toast.emit("info", "Still loading the clinical registries — one moment…")
        return False

    def _ejra_tahlil(self, confirmed: Dict[str, Any], context: Dict[str, Any]) -> None:
        if not self._require_ready():
            return
        confirmed = {k: dict(v) for k, v in confirmed.items() if isinstance(v, dict)}
        context = dict(context) if isinstance(context, dict) else {}

        if not confirmed:
            self.toast.emit('error', "No confirmed measurements to analyze.")
            return

        # FIX E6: always keep last context for edit / re-run
        self._context = dict(context)
        sc, sx = dict(confirmed), dict(context)
        self._set_busy("Analyzing values…")

        @timed_operation("analyze")
        def work():
            return self.service.analyze(sc, sx)

        def ok(result):
            self._unset_busy()
            self._emal_tahlil_natije(result, sc, sx)

        def err(msg):
            self._unset_busy()
            self.toast.emit("error", f"Analysis failed: {msg}")

        self._ejra_async(work, ok, err)

    def _emal_tahlil_natije(self, result: Any, confirmed: Dict, context: Dict) -> None:
        self._confirmed = confirmed
        self._context = context
        self._current_result = result
        self._hasCurrentAnalysis = True
        self._analysisSaved = False
        self._current_analysis_db_id = None
        self._currentChatSessionId = None
        self.currentChatSessionIdChanged.emit()
        self.currentAnalysisIdChanged.emit()
        self._sakht_natije_models(result.to_dict())
        self.hasCurrentAnalysisChanged.emit()
        self.analysisSavedChanged.emit()
        self._emit_tahlil_options()
        self.navigate("results")
        self._set_chat_context(result.to_dict())
        if self._current_user_id is not None:
            self._auto_save_analysis()
        else:
            self.toast.emit("success", "Analysis complete.")
    def _auto_save_analysis(self) -> None:
        if self._current_user_id is None or self._current_result is None:
            return

        try:
            data = self._current_result.to_dict()
            combined_inputs = {
                "observations": dict(data.get("observations") or {}),
                "context": dict(data.get("context") or {}),
            }
            test_id = save_blood_test(
                self._current_user_id,
                selected_panels=sorted((data.get("observations") or {}).keys()),
                patient_inputs=combined_inputs,
                derived_metrics=data.get("derived") or {},
                diagnoses=(data.get("interpretations") or {}).get("interpretations", []),
                risk_predictions=self._last_risks,
                ai_report=json.dumps(data, ensure_ascii=False),
                initial_summary=self._cached_summary,
            )
            self._current_analysis_db_id = test_id
            self._analysisSaved = True
            self.analysisSavedChanged.emit()
            self.currentAnalysisIdChanged.emit()
            self._emit_tahlil_options()

            self.toast.emit("success", "Analysis complete and saved to history ✓")
            QTimer.singleShot(100, self.load_history)
        except Exception as exc:
            logger.exception("_auto_save_analysis failed")
            self.toast.emit("warning", f"Analysis complete, but auto-save failed: {exc}")

    @timed_operation("build_result_models")
    def _sakht_natije_models(self, data: Dict[str, Any]) -> None:
        features = self.features
        obs = data.get("observations") or {}
        derived = (data.get("derived") or {}).get('results') or {}
        interp = (data.get("interpretations") or {}).get("interpretations") or []
        measured, derived_rows, clinical = [], [], []


        for fid, rec in obs.items():
            ident = features.get(fid, {}).get("identity") or {}
            measured.append({
                "featureId": _s(fid),
                "featureName": _s(ident.get("display_name") or ident.get("canonical_name") or fid),
                "value": _fmt(rec.get("value")),
                'unit': _s(rec.get("unit")),
                "category": _s(ident.get("category")),
                "formula": '',
                "flag": _s(rec.get("flag")),
            })

        for fid, rec in derived.items():
            ident = features.get(fid, {}).get("identity") or {}
            derived_rows.append({
                "featureId": _s(fid),
                "featureName": _s(ident.get("display_name") or ident.get('canonical_name') or fid),
                "value": _fmt(rec.get("value")),
                "unit": _s(rec.get("unit")),
                "formula": _s(rec.get("formula_id") or rec.get("formula")),
                "category": _s(ident.get("category")),
                "flag": ""
            })

        for x in interp:
            status = _s(x.get("status"))
            if status in POSITIVE_STATUSES:
                evidence = " ".join(_s(e.get("message")) for e in x.get("evidence", [])
                                    if e.get("truth") == "true")
                clinical.append({
                    "diseaseId": _s(x.get("disease_id")),
                    "name": _s(x.get("name_en") or x.get("name_fa") or x.get("name") or x.get("disease_id")),
                    "status": status,
                    "statusLabel": _vaziat_label(status),
                    "urgency": _s(x.get("urgency") or x.get("clinical_priority") or "routine"),
                    "evidence": evidence,
                    "limitations": " ".join(_s(v) for v in (x.get("limitations") or [])),
                    "sources": ", ".join(_s(v) for v in (x.get("source_ids") or [])),
                    'ruleId': _s(x.get('rule_id')),
                    "statement": _s(x.get("statement")),
                    'kind': "disease" if status == "criterion_met" else "pattern"
                })

        measuredModel.set_satrha(measured)
        self._set_satrha("_measuredRows", self.measuredRowsChanged, measured)
        derivedModel.set_satrha(derived_rows)
        self._set_satrha("_derivedRows", self.derivedRowsChanged, derived_rows)
        clinicalModel.set_satrha(clinical[:_MAX_MIRROR_ROWS])
        self._set_satrha("_clinicalRows", self.clinicalRowsChanged, clinical)
        insufficientModel.clear()
        conflictingModel.clear()

        self._measuredCount = len(measured)
        self._derivedCount = len(derived_rows)
        self._clinicalCount = len(clinical)
        self._insufficientCount = 0
        self._conflictingCount = 0
        self._urgentCount = sum(1 for x in interp if x.get('status') == "urgent_pattern")
        self.measuredCountChanged.emit()
        self.derivedCountChanged.emit()
        self.clinicalCountChanged.emit()
        self.urgentCountChanged.emit()
        self.insufficientCountChanged.emit()
        self.conflictingCountChanged.emit()

        risk_rows = self._mohasebe_risks(data)
        self._last_risks = risk_rows
        riskModel.set_satrha(risk_rows)
        self._set_satrha("_riskRows", self.riskRowsChanged, risk_rows)

        self._sakht_bimar_context_satrha(data.get("context") or {})
        self._set_result_warnings(data)

        triaged = data.get("triaged_findings") or {}
        self._tier1Rows = list(triaged.get("tier_1_critical") or [])
        self._tier2Rows = list(triaged.get("tier_2_actionable") or [])
        self._tier3Rows = list(triaged.get("tier_3_physiological") or [])
        stats = triaged.get("summary_stats") or {}
        self._primaryClinicalStatus = _s(stats.get("primary_clinical_status") or (
            "CRITICAL_EMERGENCY" if self._tier1Rows else
            "ACTIONABLE_WORKUP" if self._tier2Rows else
            "PHYSIOLOGICAL_BASELINE"
        ))
        self._executiveSummary = _s(data.get("executive_summary") or "")
        self._targetPopulationInfo = _s(data.get("target_pop_info") or "")
        if self._tier1Rows:
            self._urgentCount = len(self._tier1Rows)
            self.urgentCountChanged.emit()

        self.triageChanged.emit()
        self.executiveSummaryChanged.emit()

    # FIX U2/U3: surface engine-level warnings and panic values to QML.
    # AnalysisResult.warnings (QA notes: plausibility clamps, unit fallbacks),
    # AnalysisResult.errors, per-observation QA notes, critical_alerts and
    # critical safety_flags previously never reached any QML property
    # (only the AI chat consumed critical_alerts/safety_flags).
    def _set_result_warnings(self, data: Dict[str, Any]) -> None:
        warns: List[str] = []
        for e in data.get("errors") or []:
            t = _s(e).strip()
            if t:
                warns.append("Error: " + t)
        for w in data.get("warnings") or []:
            t = _s(w).strip()
            if t and t not in warns:
                warns.append(t)
        for fid, rec in (data.get("observations") or {}).items():
            if not isinstance(rec, dict):
                continue
            for w in rec.get("warnings") or []:
                t = _s(w).strip()
                if t:
                    warns.append(f"{fid}: {t}")
                if len(warns) >= 25:
                    break
            if len(warns) >= 25:
                break
        for f in data.get("safety_flags") or []:
            if isinstance(f, dict) and _s(f.get("type")) == "reported_borderline_flag":
                t = f"Borderline flag reported by lab: {_s(f.get('feature_id'))}"
                if t not in warns:
                    warns.append(t)
        self._resultWarnings = warns[:30]
        self.resultWarningsChanged.emit()

        crits: List[Dict] = []
        for a in data.get("critical_alerts") or []:
            if not isinstance(a, dict):
                continue
            msg = _s(a.get("message")).strip()
            fid = _s(a.get("feature_id"))
            title = msg or f"Critical value: {fid or 'unknown feature'}"
            detail = ""
            if msg and fid:
                lo = _fmt(a.get("threshold_low"))
                hi = _fmt(a.get("threshold_high"))
                rng = " - ".join(x for x in (lo, hi) if x)
                detail = f"{fid} = {_fmt(a.get('value'))} {_s(a.get('unit'))}".strip()
                if rng:
                    detail += f" (panic range outside {rng})"
            crits.append({"title": title, "detail": detail})
        for f in data.get("safety_flags") or []:
            if not isinstance(f, dict):
                continue
            ftype = _s(f.get("type"))
            if ftype in ("critical_low", "critical_high", "reported_critical_flag"):
                fid = _s(f.get("feature_id"))
                if ftype == "critical_low":
                    title = f"Critical low value: {fid}"
                elif ftype == "critical_high":
                    title = f"Critical high value: {fid}"
                else:
                    title = f"Critical flag reported by lab: {fid}"
                parts = [f"value {_fmt(f.get('value'))}".strip()]
                if _s(f.get("unit")):
                    parts[0] += f" {_s(f.get('unit'))}"
                if _fmt(f.get("threshold")):
                    parts.append(f"threshold {_fmt(f.get('threshold'))}")
                crits.append({
                    "title": title,
                    "detail": " - ".join(parts),
                })
        self._criticalAlerts = crits[:20]
        self.criticalAlertsChanged.emit()

    def _sakht_bimar_context_satrha(self, context: Dict[str, Any]) -> None:
        if not context:
            self._patient_context_rows = []
            self.patientContextRowsChanged.emit()
            return

        _LABELS = {
            'age_years':              ("Age", "years"),
            'sex_at_birth':           ("Sex at birth", ""),
            "weight_kg":              ('Weight', 'kg'),
            "height_cm":              ('Height', "cm"),
            'bmi':                    ("BMI", "kg/m²"),
            "waist_cm":               ("Waist", "cm"),
            "neck_cm":                ("Neck", "cm"),
            "systolic_bp":            ("Systolic BP", "mmHg"),
            'diastolic_bp':           ("Diastolic BP", "mmHg"),
            "heart_rate":             ('Heart rate', "bpm"),
            "fasting":                ("Fasting", ""),
            "pregnant":               ("Pregnant", ""),
            "smoking":                ("Smoking", ''),
            "physical_activity":      ("Physical activity", ''),
            "family_history_dm":      ("FHx: Diabetes", ''),
            'family_history_cad':     ("FHx: CAD", ""),
            'family_history_htn':     ("FHx: Hypertension", ''),
            'family_history_stroke':  ("FHx: Stroke", ""),
            'family_history_crc':     ("FHx: Colorectal CA", ""),
            "family_history_lung_ca": ("FHx: Lung CA", ""),
            "family_history_hcc":     ("FHx: Liver CA (HCC)", ""),
            "sleep_hours":            ("Sleep", "hours"),
            "cigarettes_per_day":     ("Cigarettes/day", ""),
            "smoking_years":          ("Smoking years", ""),
        }

        rows: List[Dict] = []
        for key, value in context.items():
            if value is None or value == "":
                continue
            label, unit = _LABELS.get(key, (key.replace("_", " ").title(), ""))
            if isinstance(value, bool):
                display = "Yes" if value else "No"
            else:
                display = _fmt(value)
            if key == "age_years":
                try:
                    display = str(int(round(float(value))))
                except (TypeError, ValueError):
                    display = _fmt(value)
            if unit:
                display = f"{display} {unit}"
            rows.append({"label": label, "value": display})

        self._patient_context_rows = rows
        self.patientContextRowsChanged.emit()

    @timed_operation('compute_risks')
    def _mohasebe_risks(self, data: Dict[str, Any]) -> List[Dict]:
        if _predict_risks is None:
            return []

        obs = data.get("observations") or {}
        derived = (data.get("derived") or {}).get("results") or {}
        interp = (data.get('interpretations') or {}).get("interpretations") or []

        def _num(rec):
            v = rec.get("value") if isinstance(rec, dict) else rec
            if isinstance(v, bool) or v is None:
                return None
            try:
                f = float(str(v).replace(",", ".").strip())
            except (TypeError, ValueError):
                return None
            return f if f == f and f not in (float("inf"), float("-inf")) else None

        # FIX C5: NEVER leak operator's own profile into patient's report.
        # Only the per-encounter clinical context (ctx) is used. If a field
        # is missing it stays None and is disclosed via assumedInputs.
        ctx = getattr(self, "_context", {}) or {}

        def _yn(*vals):
            for v in vals:
                if v in (1, True, "1", "Yes", "yes", 'true', "True"): return 1
                if v in (0, False, '0', "No", "no", "false", "False"): return 0
            return None

        def _yn_ctx(*keys):
            for k in keys:
                v = ctx.get(k)
                if v is not None:
                    if v in (1, True, "1", "Yes", "yes", 'true', "True"): return 1
                    if v in (0, False, '0', "No", "no", "false", "False"): return 0
                    # numeric 1/0
                    try:
                        fv = float(v)
                        if fv == 1: return 1
                        if fv == 0: return 0
                    except Exception:
                        pass
            return None

        _sex_src = ctx.get("sex_at_birth")
        sex_raw = str(_sex_src).strip().lower() if _sex_src else ""
        if sex_raw in ("male", "m", "1", "مرد"):
            _sex = "Male"
        elif sex_raw in ("female", "f", "0", "زن"):
            _sex = "Female"
        else:
            _sex = None  # FIX P14: unknown sex is disclosed per model, not defaulted silently

        # FIX C1-C4: map ALL clinical chips to canonical patient keys
        # Smoking: Never=0, Former=0+quit, Current=1
        smoking_val = ctx.get("smoking")
        # former_smoker flag kept for PLCO etc
        former_smoker = 1 if ctx.get("former_smoker") else 0

        patient = {
            "Age": ctx.get("age_years"),
            "Sex": _sex,
            "Race": ctx.get("race") or ctx.get("ethnicity") or "other",
            "Country": ctx.get("country") or ctx.get("Country") or "",
            "country": ctx.get("country") or "",
            "Education_Years": ctx.get("education_years"),
            "Education_Level": ctx.get("education_years"),  # alias for PLCOm
            "Height": ctx.get("height_cm"),
            "Weight": ctx.get("weight_kg"),
            "Waist": ctx.get("waist_cm"),
            'NeckCircumference': ctx.get("neck_cm"),
            "Systolic_BP": ctx.get('systolic_bp'),
            "Diastolic_BP": ctx.get('diastolic_bp'),
            "Heart_Rate": ctx.get("heart_rate"),
            "Fasting": ctx.get("fasting"),
            "Pregnant": ctx.get('pregnant'),
            "Pregnancy_Trimester": ctx.get("pregnancy_trimester"),
            'Smoking': _yn_ctx("smoking"),
            "Former_Smoker": former_smoker,
            "Cigarettes_Per_Day": ctx.get("cigarettes_per_day"),
            "Smoking_Years": ctx.get('smoking_years'),
            "Quit_Years": ctx.get("quit_years"),
            "quit_years": ctx.get("quit_years"),
            "PhysicalActivity": _yn_ctx("physical_activity"),
            'DailyFruitVeg': _yn_ctx("daily_fruit_veg"),
            "FamilyHistory_DM": _yn_ctx("family_history_dm"),
            "FamilyHistory_CAD": _yn_ctx("family_history_cad"),
            "FamilyHistory_Stroke": _yn_ctx("family_history_stroke"),
            "FamilyHistory_CRC": _yn_ctx("family_history_crc"),
            "FamilyHistory_LungCa": _yn_ctx("family_history_lung_ca", "family_history_lung"),
            "FamilyHistory_HCC": _yn_ctx("family_history_hcc"),
            # Personal history — FIX C1: now from ctx not from dead prof.hx_*
            "Diabetes": _yn_ctx("diabetes_flag", "diabetes", "hx_diabetes"),
            "DiabetesFlag": _yn_ctx("diabetes_flag", "diabetes", "hx_diabetes"),
            "Hypertension": _yn_ctx("hypertension", "hx_hypertension"),
            "BpTreated": _yn_ctx("bp_treated", "hypertension"),
            "Hyperlipidemia": _yn_ctx("hyperlipidemia", "hx_dyslipidemia"),
            'CAD': _yn_ctx("cad", "hx_cad", "coronary_artery_disease"),
            "AF": _yn_ctx("af", "hx_af"),
            "HF": _yn_ctx("hf", "hx_hf"),
            "Stroke": _yn_ctx("stroke", "hx_stroke"),
            "COPD": _yn_ctx("copd", "hx_copd"),
            "CKD": _yn_ctx("ckd", "hx_ckd"),
            "Cirrhosis": _yn_ctx("liver_disease", "cirrhosis", "hx_liver"),
            'Liver_Disease': _yn_ctx("liver_disease", "hx_liver"),
            "PriorVTE": _yn_ctx("prior_vte", "hx_vte"),
            "ActiveCancer": _yn_ctx("active_cancer", "hx_cancer"),
            "Personal_History_Cancer": _yn_ctx("personal_history_cancer", "hx_cancer_personal"),
            'Cancer': _yn_ctx("active_cancer", "personal_history_cancer", "hx_cancer"),
            "Retinopathy": _yn_ctx("retinopathy", "hx_retinopathy"),
            "Dialysis": _yn_ctx("dialysis", "hx_dialysis"),
            "Postmenopausal": _yn_ctx("postmenopausal", "postmeno"),
            "GestationalDM": _yn_ctx("gestational_dm", "hx_gdm"),
            "Current_Estrogen_Use": _yn_ctx("current_estrogen_use", "estrogen"),
            # Sleep / STOP-BANG / NoSAS / Berlin
            "Snoring_Loud": _yn_ctx("snoring_loud"),
            "Daytime_Tiredness": _yn_ctx("daytime_tiredness"),
            "Observed_Apnea": _yn_ctx("observed_apnea"),
            "Reduced_Mobility_3d": _yn_ctx("reduced_mobility_3d"),
            "Recent_Trauma_Surgery_1mo": _yn_ctx("recent_trauma_surgery_1mo"),
            "Ongoing_Hormone_Treatment": _yn_ctx("ongoing_hormone_treatment"),
            # HAS-BLED / CHA2DS2-VASc
            "Prior_Bleeding": _yn_ctx("prior_bleeding"),
            "Labile_INR": _yn_ctx("labile_inr"),
            "Antiplatelet": _yn_ctx("antiplatelet"),
            "NSAID": _yn_ctx("nsaid"),
            "Vascular_Disease": _yn_ctx("vascular_disease", "pad"),
            "PAD": _yn_ctx("vascular_disease", "pad"),
            "Alcohol_8_per_week": _yn_ctx("alcohol_8_per_week"),
            "AlcoholDrinksPerOccasion": ctx.get("alcohol_drinks_per_week"),
            # Wells / Caprini detailed
            "Bedridden_3d_Or_Surgery_4wk": _yn_ctx("bedridden_3d_or_surgery_4wk"),
            "Leg_Tenderness": _yn_ctx("leg_tenderness"),
            "Whole_Leg_Swelling": _yn_ctx("whole_leg_swelling"),
            "Calf_Swelling_3cm": _yn_ctx("calf_swelling_3cm"),
            "Pitting_Edema_Unilateral": _yn_ctx("pitting_edema_unilateral"),
            "Collateral_Veins": _yn_ctx("collateral_veins"),
            "Alternative_Diagnosis_More_Likely": _yn_ctx("alternative_diagnosis_more_likely"),
            "Clinical_Signs_DVT": _yn_ctx("clinical_signs_dvt"),
            "PE_Most_Likely_Diagnosis": _yn_ctx("pe_most_likely_diagnosis"),
            "Known_Thrombophilia": _yn_ctx("known_thrombophilia"),
            "Respiratory_Failure": _yn_ctx("respiratory_failure"),
            "Acute_MI_Or_Stroke": _yn_ctx("acute_mi_or_stroke"),
            "Acute_Infection_Or_Rheumatologic": _yn_ctx("acute_infection_or_rheumatologic"),
            "Surgery_Immobilization_4wk": _yn_ctx("bedridden_3d_or_surgery_4wk", "recent_trauma_surgery_1mo"),
            # Additional PLCO / general
            "Alcohol_8": _yn_ctx("alcohol_8_per_week"),
        }


        # FIX P17/P47: only DIAGNOSED_STATUSES count as "has disease" for
        # predictor exclusions/gates; suspected findings stay "Suspected" so
        # their risk scores are still computed. Non-positive interpretations
        # (insufficient/negative/ruled-out/...) are excluded entirely.
        diagnoses = [
            {
                "diseaseKey": _s(x.get("disease_id")),
                "nameEn": _s(x.get("name_en")),
                "status": "Present" if x.get("status") in DIAGNOSED_STATUSES else "Suspected"
            }
            for x in interp
            if _s(x.get("status")) in POSITIVE_STATUSES
        ]

        # Direct invocation of predictor engine with native unit normalization & alias resolution
        try:
            raw = _predict_risks(inputs=obs, derived=derived, patient=patient, diagnoses=diagnoses)
        except Exception as exc:
            logger.warning(f"Risk prediction failed: {exc}")
            return []

        rows = []
        for r in raw:
            st = _s(r.get("status"))


            if st not in ("Evaluated", "Evaluated (Provisional)",
                          "AlreadyDiagnosed", "Insufficient Data"):
                continue

            rows.append({
                "diseaseKey": _s(r.get("diseaseKey")),
                'nameEn': _s(r.get("nameEn")),
                "modelName": _s(r.get("modelName") or ""),
                "kind": _s(r.get("kind") or ""),
                "horizonYears": float(r.get('horizonYears') or 0),
                'probability': float(r.get("probability") or 0.0),
                "riskLevel": _s(r.get('riskLevel') or r.get("riskBand") or ""),
                "riskBand": _s(r.get("riskBand") or ''),
                "status": st,
                "scoreText": _s(r.get("score") if r.get('score') is not None else r.get("points")),
                "interpretationFa": _s(r.get('interpretationFa') or ""),
                "citation": _s(r.get('citation') or ""),
                "journal": _s(r.get('journal') or ""),
                'publicationYear': _s(r.get("publication_year") or ''),
                "referenceUrl": _s(r.get("reference_url") or ""),
                "doi": _s(r.get("doi") or ""),
                "pmid": _s(r.get('pmid') or ""),
                'article_title': _s(r.get("article_title") or ""),
                "requiredFeatures": ", ".join(r.get('requiredFeatures') or []),
                "missingFeatures": ", ".join(r.get("missingFeatures") or []),
                "exclusionReason": _s(r.get('exclusionReason') or ""),
                "warnings": " | ".join(r.get("warnings") or []),

                "provisional": bool(r.get("provisional")),
                "approximation": bool(r.get('approximation')),
                "assumedInputs": ", ".join(
                    str(a.get("field")) for a in (r.get("assumedInputs") or [])),
                "assumedCriticalCount": int(
                    r.get("assumedCriticalCount") or 0),
                "citationCaveat": _s(r.get("citationCaveat") or ""),
            })

        # Provisional rows sort just under fully-evaluated ones so a result
        # resting on assumed inputs never leads the list.
        order = {"Evaluated": 0, "Evaluated (Provisional)": 1,
                 'AlreadyDiagnosed': 2, 'Insufficient Data': 3}
        rows.sort(key=lambda x: (order.get(x["status"], 9), -x["probability"]))
        return rows

    @Slot()
    def saveAnalysis(self) -> None:
        if self._current_user_id is None:
            self.toast.emit("warning", "Sign in to save an analysis.")
            return

        if self._current_result is None:
            self.toast.emit("warning", "Run an analysis first.")
            return

        try:
            data = self._current_result.to_dict()
            combined_inputs = {
                "observations": dict(data.get("observations") or {}),
                "context": dict(data.get("context") or {}),
            }
            test_id = save_blood_test(
                self._current_user_id,
                selected_panels=sorted((data.get("observations") or {}).keys()),
                patient_inputs=combined_inputs,
                derived_metrics=data.get("derived") or {},
                diagnoses=(data.get("interpretations") or {}).get("interpretations", []),
                risk_predictions=self._last_risks,
                ai_report=json.dumps(data, ensure_ascii=False),
                initial_summary=self._cached_summary
            )
            self._current_analysis_db_id = test_id
            self._analysisSaved = True
            self.analysisSavedChanged.emit()
            self.currentAnalysisIdChanged.emit()
            self._emit_tahlil_options()
            self.toast.emit("success", "Analysis saved to history.")
            QTimer.singleShot(100, self.load_history)
        except Exception as exc:
            logger.exception('saveAnalysis failed')
            self.toast.emit("error", f"Could not save analysis: {exc}")

    @Slot()
    def continueToChat(self) -> None:
        if self.ai is None:
            try:
                self.ai = self._sakht_chatbot()
            except Exception:
                pass
        self.navigate("chat")


    @Slot(str)
    def selectFile(self, path: str) -> None:
        local = QUrl(path).toLocalFile() if str(path).startswith('file:') else str(path)
        # FIX UPL1: changing file invalidates previous review
        if self._selectedFile != local:
            if local == "":
                # clearing file
                self._selectedFile = ""
                self.selectedFileChanged.emit()
                self.clearReviewOnly()
                return
            # new file selected — clear old review
            reviewModel.clear()
            self._set_satrha("_reviewRows", self.reviewRowsChanged, [])
            self._review = {"session": None}
            self._ocr_auto_rejected = 0
            self.ocrAutoRejectedChanged.emit()
            self._selectedFile = local
            self.selectedFileChanged.emit()

    @Slot(result="QVariantMap")
    def ocrStatus(self) -> Dict[str, Any]:
        info = {
            "backend": "unknown",
            "ocr_key": bool(self._ocr_api_key or os.getenv('OCR_API_KEY') or os.getenv("GROQ_API_KEY")),
            "pytesseract": False,
            'tesseract_binary': False
        }
        try:
            if self.service is not None:
                info["backend"] = getattr(self.service.ocr.backend, "name", "unknown")
        except Exception:
            pass

        try:
            import pytesseract
            info["pytesseract"] = True
            try:
                from ocr import _tesseract_binary
                tb = _tesseract_binary()
                if tb:
                    pytesseract.pytesseract.tesseract_cmd = tb
            except Exception:
                pass
            try:
                import io, contextlib
                with contextlib.redirect_stderr(io.StringIO()):
                    pytesseract.get_tesseract_version()
                info["tesseract_binary"] = True
            except SystemExit:
                # pytesseract raises SystemExit (not Exception) when the
                # installed binary reports a version string it cannot parse
                # (e.g. "tesseract 3.05.00dev"). It must never take the UI
                # process down; the binary is simply treated as unusable.
                info["tesseract_binary"] = False
            except BaseException:
                info["tesseract_binary"] = False
        except Exception:
            pass

        return info

    @Slot()
    def extractSelectedFile(self) -> None:
        if not self._require_ready():
            return
        if not self._selectedFile:
            self.toast.emit('warning', "Choose a report file first.")
            return

        path = self._selectedFile
        if not Path(path).is_file():
            self.toast.emit('error', f"File not found on disk: {path}")
            return

        st = self.ocrStatus()
        engine = st["backend"]

        if engine == "vision":
            self._set_ocr_khata("")

        if engine == "tesseract" and not st["tesseract_binary"]:
            self._set_ocr_khata("OCR NOT working: Tesseract binary missing. Use a .txt report or install Tesseract.")
            self.toast.emit("error", "OCR not working — see banner.")
            return

        if engine == "passthrough" and not path.lower().endswith((".txt", ".csv", ".tsv")):
            self._set_ocr_khata("No OCR engine active — images cannot be read. Use a .txt report or install Tesseract.")
            self.toast.emit('warning', "No OCR engine active — use .txt or manual entry.")

        self._extract_gen += 1
        gen = self._extract_gen

        self._set_busy(f"Extracting… (engine: {engine})")
        watchdog = QTimer(self)
        watchdog.setSingleShot(True)

        def _watch():
            if gen != self._extract_gen:
                return
            if self._busy:
                self._unset_busy()
                self._set_ocr_khata(f"Extraction timed out (engine: {engine}).")
                self.toast.emit("error", "Extraction timed out — OCR marked as not working.")

        watchdog.timeout.connect(_watch)
        watchdog.start(120000)

        @timed_operation("ocr_extract")
        def work():
            logger.info(f"🧾 OCR start | engine={engine}")
            session = self.service.amadesazi_ocr_review(path)
            logger.info(f"🧾 OCR finished | items={len(session.items)}")
            return session

        def ok(session):
            if gen != self._extract_gen:
                return
            watchdog.stop()
            self._unset_busy()

            data = session.to_dict()
            items = data.get("items", []) or []
            keep, rejected = [], 0

            for it in items:
                fid = _s(it.get("feature_id"))
                val = it.get("value")
                if (not fid) or (val is None) or (str(val).strip() == ''):
                    rejected += 1
                    continue
                keep.append(it)

            data["items"] = keep
            self._review = {"session": data}

            if rejected != self._ocr_auto_rejected:
                self._ocr_auto_rejected = rejected
                self.ocrAutoRejectedChanged.emit()

            rows = []
            for it in keep:
                sa = (it.get("suggested_action") or "").casefold()
                rows.append({
                    "index": len(rows),
                    "resultId": _s(it.get("result_id")),
                    "decision": {"accept": "Accept", 'reject': "Reject"}.get(sa, "Edit"),
                    "featureId": _s(it.get("feature_id")),
                    "featureName": _s(it.get('display_name') or it.get("feature_id")),
                    "value": _fmt(it.get("value")),
                    "unit": _s(it.get("unit")),
                    "confidence": float(it.get("confidence") or 0.0),
                    "flag": _s(it.get("flag")),
                    'warning': " | ".join(w for w in (it.get("warnings") or []) if w)
                })

            reviewModel.set_satrha(rows)
            self._set_satrha("_reviewRows", self.reviewRowsChanged, rows)

            if not rows:
                err_detail = ""
                if getattr(session, "errors", None):
                    err_detail = " | ".join(str(e) for e in session.errors if e)
                if not err_detail and getattr(session, "warnings", None):
                    err_detail = " | ".join(str(w) for w in session.warnings if w)
                
                if err_detail:
                    sys.stderr.write(f"[OCR UI Alert] Extraction failed: {err_detail}\n")
                    sys.stderr.flush()
                    self._set_ocr_khata(f"OCR Error: {err_detail}")
                    self.toast.emit("error", f"OCR Error: {err_detail[:80]}")
                else:
                    self._set_ocr_khata("No usable features extracted. Try manual entry or check API key.")
                    self.toast.emit("error", "No usable features extracted. Try manual entry.")

        def err(msg):
            if gen != self._extract_gen:
                return
            watchdog.stop()
            self._unset_busy()
            self._set_ocr_khata(f"OCR NOT working: {msg}")
            self.toast.emit('error', f"Extraction failed: {msg}")

        self._ejra_async(work, ok, err)

    @Slot(int, str, str)
    def updateReviewRow(self, index: int, field: str, value: str) -> None:
        rows = reviewModel.get()
        if 0 <= index < len(rows):
            rows[index][field] = value
            # FIX UPL4: when featureId changes, also refresh display name
            if field == "featureId":
                fid = value
                meta = self.features.get(fid) or {}
                ident = meta.get("identity") or {}
                disp = ident.get("display_name") or ident.get("canonical_name") or fid
                rows[index]["featureName"] = disp
                # also update canonical unit if empty
                if not rows[index].get("unit"):
                    rows[index]["unit"] = (meta.get("units") or {}).get("canonical") or ""
            idx = reviewModel.index(index, 0)
            reviewModel.dataChanged.emit(idx, idx)
            self._set_satrha("_reviewRows", self.reviewRowsChanged, rows)

    @Slot(dict)
    def confirmReviewAndAnalyze(self, context: Dict[str, Any]) -> None:
        decisions = []
        for row in reviewModel.get():
            decisions.append({
                'result_id': row["resultId"],
                "action": row["decision"].lower(),
                'feature_id': row["featureId"],
                "value": row["value"],
                "unit": row["unit"]
            })

        if not self._require_ready():
            return

        self._set_busy("Applying review…")

        def work():
            return self.service.emal_review_decisions(
                self._review.get("session") or {}, decisions)

        def ok(confirmed):
            self._unset_busy()
            if not confirmed:
                self.toast.emit("error", 'No accepted measurements to analyze.')
                return

            # FIX UPL3: merge manual + OCR confirmed instead of overwriting
            # Manual entries that were already present are kept unless OCR overrides same fid
            merged = dict(self._manual)  # keep existing manual
            for fid, rec in confirmed.items():
                if isinstance(rec, dict):
                    merged[fid] = dict(rec)
            self._manual = merged
            # FIX E6: persist context
            self._context = dict(context) if isinstance(context, dict) else {}
            self._ejra_tahlil(merged, self._context)

        def err(msg):
            self._unset_busy()
            # FIX M4: include which feature failed if possible
            self.toast.emit("error", f"Review must be complete: {msg}")

        self._ejra_async(work, ok, err)

    def _set_chat_context(self, data: Dict[str, Any]) -> None:
        if self.ai is not None:
            try:
                enriched = dict(data)
                enriched["risk_predictions"] = self._last_risks or []
                self.ai.set_analysis(enriched)
            except Exception as exc:
                logger.warning(f"Chat context setup failed: {exc}")
        self._cached_summary = ""
        self._hasCurrentAnalysis = True
        self.hasCurrentAnalysisChanged.emit()

    def _gen_kholase_async(self, lang: str = "en") -> None:
        self._cached_summary = self._executiveSummary or ""
        self._chat_summary_loading = False
        self.chatSummaryLoadingChanged.emit()
        self.chatReady.emit()

    @Slot(result=bool)
    def probeChatConnection(self) -> bool:
        self._probe_chat()
        return self._chat_available

    @Slot(str)
    def setChatModel(self, model_name: str) -> None:
        self.configureChatProvider("local", model_name, self._chat_local_url)

    @Slot(str, str, str)
    def configureChatProvider(self, provider: str, model: str, base_url: str) -> None:
        try:
            mdl = (model or "").strip()
            burl = (base_url or "").strip()

            bot = BloodLabChatbot(
                provider="local",
                model=mdl if mdl else None,
                base_url=burl if burl else None,
                language=self._chat_lang,
            )
            self.ai = bot
            self._chat_provider = "local"
            self._chat_model = bot.model
            self._chat_is_local = True
            self.chatProviderChanged.emit()
            self.chatModelChanged.emit()
            self.chatIsLocalChanged.emit()

            if self._current_result:
                self._set_chat_context(self._current_result.to_dict())

            self._probe_chat()
            self.toast.emit("success", f"Local AI model set to {self._chat_model}")
        except Exception as exc:
            logger.error(f"Failed to configure AI provider: {exc}")
            self.toast.emit("error", f"AI configuration failed: {exc}")

    @Slot(str)
    def chatSend(self, message: str) -> None:
        self.chatReplyReady.emit(
            "The offline clinical AI assistant is currently under active development and disabled in Release v1.3.1.",
            False
        )

    def _set_chat_busy(self, v: bool) -> None:
        if self._chat_busy != v:
            self._chat_busy = v
            self.chatBusyChanged.emit()

    def _autosave_chat(self) -> None:
        if self._current_user_id is None or self.ai is None:
            return

        try:
            history = self.ai.khorooji_tarikhche()
            if not history:
                return

            first_user = next((m["content"] for m in history if m["role"] == 'user'), "")
            title = (first_user[:40] + '…') if first_user else "Lab chat"

            new_id = _chat_db_zakhire(
                self._current_user_id, history, title, self._chat_lang,
                self._current_analysis_db_id, (self._cached_summary or "")[:300],
                self._currentChatSessionId
            )

            if new_id != self._currentChatSessionId:
                self._currentChatSessionId = new_id
                self.currentChatSessionIdChanged.emit()
                self.loadChatHistory()
        except Exception as exc:
            logger.warning(f"chat autosave failed: {exc}")

    @Slot()
    def chatReset(self) -> None:
        if self.ai is not None:
            self.ai.reset()

    @Slot(str)
    def chatSetLanguage(self, language: str) -> None:
        if language not in {"en", 'fa'}:
            self.toast.emit("warning", "Unsupported language. Use 'en' or 'fa'.")
            return

        self._chat_lang = language
        self._settings.setValue('chatLanguage', language)

        if self.ai is not None:
            try:
                self.ai.set_zaban(language)
                if self._current_result:
                    self._gen_kholase_async(language)
            except Exception as exc:
                logger.warning(f"Language switch failed: {exc}")

        self.chatLanguageChanged.emit()

    @Slot(int)
    def selectAnalysisForChat(self, test_id: int) -> None:
        if self.ai is None:
            self.toast.emit("warning", 'AI not configured.')
            return

        try:
            current = int(self._current_analysis_db_id or 0)
            if test_id and test_id != current:
                rec = get_test_by_id(test_id)
                if not rec:
                    self.toast.emit("error", "Analysis not found.")
                    return

                try:
                    report = json.loads(rec.get("ai_report") or "{}")
                except Exception:
                    report = {}

                if not report.get("observations") and not (report.get("derived") or {}).get("results"):
                    report = self._saved_to_gozaresh(rec)

                self._context = dict(report.get("context") or {})
                self._sakht_natije_models(report)
                self._confirmed = {fid: dict(v) for fid, v in (report.get("observations") or {}).items()}
                self._current_result = None
                self._current_analysis_db_id = test_id
                self._hasCurrentAnalysis = True
                self._cached_summary = rec.get("initial_summary") or ""

                self.ai.set_analysis(report)

                if not self._cached_summary:
                    self._gen_kholase_async(self._chat_lang)

                sid = _chat_db_yaftan_for_tahlil(self._current_user_id, test_id) if self._current_user_id else None

                if sid:
                    rec2 = _chat_db_get(sid, self._current_user_id)
                    history, uc = [], 0
                    for m in (rec2 or {}).get("messages") or []:
                        if isinstance(m, dict) and m.get('role') in ("user", "assistant") and (m.get('content') or '').strip():
                            history.append({"role": m["role"], "content": m['content']})
                            if m["role"] == "user":
                                uc += 1
                    self.ai.history = history
                    self.ai.question_count = uc
                    self._currentChatSessionId = sid
                else:
                    self.ai.reset()
                    self._currentChatSessionId = None

                self.hasCurrentAnalysisChanged.emit()
                self.analysisSavedChanged.emit()
                self.currentAnalysisIdChanged.emit()
                self.currentChatSessionIdChanged.emit()
                self._emit_tahlil_options()
                self.chatSessionOpened.emit()
                self.toast.emit("info", "Analysis loaded for chat.")
            else:
                self.chatSessionOpened.emit()
        except Exception as exc:
            logger.exception("selectAnalysisForChat failed")
            self.toast.emit("error", f"Could not load analysis: {exc}")

    @Slot()
    def openResultsForCurrentChat(self) -> None:
        if not self._hasCurrentAnalysis:
            self.toast.emit("warning", "No analysis attached to this chat.")
            return
        self.navigate("results")

    @Slot()
    def loadChatHistory(self) -> None:
        if self._current_user_id is None:
            return

        try:
            rows_raw = _chat_db_list(self._current_user_id, limit=30)
            rows = []
            for r in rows_raw:
                rows.append({
                    "sessionId": int(r["id"]),
                    "analysisId": int(r["analysis_id"]) if r.get("analysis_id") else 0,
                    "title": _s(r.get("title") or "Untitled chat"),
                    "language": _s(r.get("language") or "en"),
                    "date": str(r.get("updated_at") or r.get("created_at") or '')[:16],
                    "summary": _s(r.get("summary") or ""),
                })
            self._set_satrha("_chatHistoryRows", self.chatHistoryRowsChanged, rows)
        except Exception as exc:
            logger.error(f"loadChatHistory failed: {exc}")

    @Slot(int)
    @Slot(str)
    def openChatSession(self, session_id: Any) -> None:
        if self._current_user_id is None or self.ai is None:
            self.toast.emit("warning", "Sign in to load a chat.")
            return

        try:
            sid = int(session_id)
        except (ValueError, TypeError):
            self.toast.emit("error", "Invalid chat session ID.")
            return

        try:
            rec = _chat_db_get(sid, self._current_user_id)
            if not rec:
                self.toast.emit("error", "Chat not found.")
                return

            if rec.get("analysis_id"):
                try:
                    self.openHistory(int(rec["analysis_id"]))
                except Exception:
                    pass

            history = []
            for m in rec.get("messages") or []:
                if not isinstance(m, dict):
                    continue
                role, content = m.get("role"), m.get('content')
                if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                    history.append({"role": role, "content": content})

            if hasattr(self.ai, "import_history"):
                self.ai.import_history(history)
            else:
                self.ai.history = history
                self.ai.question_count = sum(1 for m in history if m.get("role") == "user")

            lang = rec.get("language") or "en"
            if lang in ("en", 'fa') and lang != self._chat_lang:
                self._chat_lang = lang
                self._settings.setValue("chatLanguage", lang)
                try:
                    self.ai.set_zaban(lang)
                except Exception:
                    pass
                self.chatLanguageChanged.emit()

            self._currentChatSessionId = sid
            self.currentChatSessionIdChanged.emit()
            self.navigate("chat")
            self.chatSessionOpened.emit()
            self.toast.emit("info", f"Chat loaded: {rec.get('title') or ''}")
        except Exception as exc:
            logger.exception("openChatSession failed")
            self.toast.emit("error", f"Could not load chat: {exc}")

    @Slot(int)
    @Slot(str)
    def deleteChatSession(self, session_id: Any) -> None:
        if self._current_user_id is None:
            return

        try:
            sid = int(session_id)
        except (ValueError, TypeError):
            return

        try:
            if _chat_db_hazf(sid, self._current_user_id):
                if self._currentChatSessionId == sid:
                    self._currentChatSessionId = None
                    self.currentChatSessionIdChanged.emit()
                self.loadChatHistory()
                self.toast.emit("success", "Chat deleted.")
        except Exception as exc:
            logger.exception('deleteChatSession failed')
            self.toast.emit("error", f"Could not delete chat: {exc}")

    @Slot()
    def newChatSession(self) -> None:
        if self.ai is not None:
            self.ai.reset()
        self._currentChatSessionId = None
        self.currentChatSessionIdChanged.emit()
        self.navigate("chat")
        self.chatSessionOpened.emit()

    @Slot(result="QVariantList")
    def chatSessionMessages(self) -> List[Dict]:
        out = []
        if self.ai is not None:
            for m in self.ai.khorooji_tarikhche():
                out.append({"role": _s(m.get("role")), "text": _s(m.get("content"))})
        return out


    @Slot(str)
    def searchReferences(self, query: str) -> None:
        if not self._require_license():
            return
        q = (query or "").strip().lower()
        sources = self.disease_payload.get("guideline_sources", {})
        rows = []
        limit = _MAX_BROWSE_ROWS

        for sid, s in sources.items():
            org = str(s.get("organization") or "")
            title = str(s.get("title") or "")
            scope = s.get('scope') or ''

            if isinstance(scope, list):
                scope = ", ".join(str(x) for x in scope)

            if q and q not in title.lower() and q not in org.lower() and q not in str(scope).lower():
                continue

            rows.append({
                "sourceId": _s(sid),
                "organization": _s(org),
                "title": _s(title),
                "year": _s(s.get("year")),
                'url': _s(s.get('url')),
                "scope": _s(scope),
                "accessed": _s(s.get('accessed_at')),
                "evidenceStatus": _s(s.get("evidence_status")).replace("__", ' · ').replace("_", " ")
            })

            if len(rows) >= limit:
                break

        referenceModel.set_satrha(rows)
        self._set_satrha("_referenceRows", self.referenceRowsChanged, rows)

    @Slot(str)
    def searchGuidelines(self, query: str) -> None:
        if not self._require_license():
            return
        q = (query or '').strip().lower()
        limit = 5000 if q else 200

        rules_count = len((self.disease_payload.get('rules') or {}))
        logger.info(f"🔍 searchGuidelines called | query='{q}' | rules_loaded={rules_count} | limit={limit}")

        rows = []
        for r in _registry_guideline_rows(self.disease_payload, q, limit=limit):
            row = dict(r)
            row["executable"] = row.pop("executableLabel", "")
            rows.append(row)

        guidelineModel.set_satrha(rows)
        self._set_satrha("_guidelineRows", self.guidelineRowsChanged, rows)

    @Slot(str, result="QVariantMap")
    def diseaseDetail(self, disease_id: str) -> Dict[str, Any]:
        if not self._require_license():
            return {}
        return _registry_disease_detail(self.disease_payload, disease_id)

    @Slot(str)
    def openGuidelinesForDisease(self, disease_id: str) -> None:
        self._guidelineFocus = str(disease_id or "")
        self.guidelinesFocusChanged.emit()
        self.navigate("guidelines")

    @Slot()
    def load_history(self) -> None:
        rows = []
        if self._current_user_id is not None:
            try:
                tests = get_user_tests(self._current_user_id, limit=50, fields=['selected_panels', 'patient_inputs'])
                for t in tests:
                    rows.append({
                        "testId": int(t["id"]),
                        "date": str(t.get("test_date") or "")[:10],
                        "title": _tarikhche_title(t),
                        "subtitle": _tarikhche_subtitle(t),
                        'status': "Saved"
                    })
            except Exception as exc:
                logger.error(f"load_history failed: {exc}")

        historyModel.set_satrha(rows)
        self._set_satrha("_historyRows", self.historyRowsChanged, rows)
        self._emit_tahlil_options()

    @Slot(int)
    @Slot(str)
    def openHistory(self, test_id: Any) -> None:
        if self._current_user_id is None:
            return

        try:
            test_id = int(test_id)
        except (ValueError, TypeError):
            self.toast.emit("error", "Invalid analysis ID.")
            return

        rec = get_test_by_id(test_id)
        if not rec:
            self.toast.emit("error", "Analysis not found.")
            return

        try:
            report = json.loads(rec.get("ai_report") or "{}")
        except Exception:
            report = {}

        if not report.get("observations") and not (report.get("derived") or {}).get("results"):
            report = self._saved_to_gozaresh(rec)

        self._context = dict(report.get("context") or {})
        self._sakht_natije_models(report)
        self._confirmed = {fid: dict(v) for fid, v in (report.get("observations") or {}).items()}
        self._current_result = None
        self._current_analysis_db_id = test_id
        self._hasCurrentAnalysis = True
        self._cached_summary = rec.get("initial_summary") or ''

        if self.ai is not None:
            try:
                self.ai.set_analysis(report)
                self.chatReady.emit()
            except Exception:
                pass

        self.hasCurrentAnalysisChanged.emit()
        self.analysisSavedChanged.emit()
        self.currentAnalysisIdChanged.emit()
        self._emit_tahlil_options()
        self.navigate("results")
        self.toast.emit("info", "Saved analysis restored.")

    @staticmethod
    def _saved_to_gozaresh(rec: Dict) -> Dict:
        p_inputs = rec.get("patient_inputs") or {}
        if isinstance(p_inputs, str):
            try:
                p_inputs = json.loads(p_inputs)
            except Exception:
                p_inputs = {}
        obs = p_inputs.get("observations") if (isinstance(p_inputs, dict) and "observations" in p_inputs) else p_inputs
        ctx = p_inputs.get("context") if (isinstance(p_inputs, dict) and "context" in p_inputs) else {}
        return {
            'context': ctx or {},
            "observations": obs or {},
            "derived": {
                "results": (rec.get("derived_metrics") or {}).get("results") or rec.get("derived_metrics") or {}
            },
            'interpretations': {
                "interpretations": rec.get("diagnoses") or []
            }
        }

    @Slot(int)
    @Slot(str)
    def deleteHistory(self, test_id: Any) -> None:
        if self._current_user_id is not None:
            try:
                test_id = int(test_id)
            except (ValueError, TypeError):
                return
            delete_test(test_id, self._current_user_id)
            if self._current_analysis_db_id == test_id:
                self._current_analysis_db_id = None
                self._hasCurrentAnalysis = False
                self._analysisSaved = False
                self.hasCurrentAnalysisChanged.emit()
                self.analysisSavedChanged.emit()
                self.currentAnalysisIdChanged.emit()
            self.load_history()
            self.toast.emit('success', 'Deleted.')

    @Slot(str)
    def globalSearch(self, query: str) -> None:
        if not self._require_license():
            return
        q = (query or "").strip().lower()
        rows = []

        if not q:
            globalSearchModel.set_satrha([])
            self._set_satrha("_globalSearchRows", self.globalSearchRowsChanged, [])
            return

        for fid, meta in self.features.items():
            ident = meta.get("identity") or {}
            name = str(ident.get("display_name") or fid)
            if q in name.lower() or q in fid.lower():
                rows.append({
                    'title': _s(name),
                    "subtitle": _s(ident.get("category")),
                    "kind": 'feature',
                    "itemId": _s(fid)
                })
            if len(rows) >= 20:
                break

        if len(rows) < 12:
            for did, d in (self.disease_payload.get("diseases") or {}).items():
                ident = d.get("identity") or {}
                name = str(ident.get("name_en") or did)
                if q in name.lower() or q in did.lower():
                    rows.append({
                        "title": _s(name),
                        "subtitle": "Disease/concept",
                        "kind": 'disease',
                        'itemId': _s(did)
                    })

            for sid, s in (self.disease_payload.get('guideline_sources') or {}).items():
                title = str(s.get("title") or "")
                org = str(s.get("organization") or "")
                if q in title.lower() or q in org.lower():
                    rows.append({
                        "title": _s(org + " — " + title),
                        "subtitle": "Guideline source",
                        'kind': "source",
                        "itemId": _s(sid)
                    })

        globalSearchModel.set_satrha(rows[:20])
        self._set_satrha("_globalSearchRows", self.globalSearchRowsChanged, rows[:20])

    @Slot(str, str)
    def openSearchResult(self, kind: str, item_id: str) -> None:
        if kind == "feature":
            self.addManualFeature(item_id)
            self.navigate("manual")
        elif kind == 'disease':
            self.openGuidelinesForDisease(item_id)
        else:
            self.navigate("references")
            self.searchReferences(item_id)
    @Slot(str)
    def searchDiseases(self, query: str) -> None:
        if not self._require_license():
            return
        q = (query or '').strip().lower()
        limit = 500 if q else 300

        diseases = self.disease_payload.get("diseases", {})
        rules = self.disease_payload.get("rules", {})

        rule_counts = {}
        for rule in rules.values():
            did = rule.get("disease_id")
            if did: rule_counts[did] = rule_counts.get(did, 0) + 1

        rows = []
        for did, d in diseases.items():
            ident = d.get("identity") or {}
            name_en = str(ident.get("name_en") or did)
            name_fa = str(ident.get("name_fa") or "")
            domains = ident.get("domains") or d.get('classification', {}).get("domains") or []
            wiki = str(ident.get("wikipedia_url") or "")

            if q:
                haystack = f"{did} {name_en} {name_fa} {' '.join(domains) if isinstance(domains, list) else str(domains)}".lower()
                if q not in haystack: continue

            rows.append({
                "diseaseId": _s(did), "name": _s(name_en), 'name_fa': _s(name_fa),
                "domains": ", ".join(_s(x) for x in domains) if isinstance(domains, list) else _s(domains),
                "wikipedia_url": wiki, "ruleCount": rule_counts.get(did, 0)
            })
            if len(rows) >= limit: break

        diseaseModel.set_satrha(rows)
        self._set_satrha("_diseaseRows", self.diseaseRowsChanged, rows)

diseaseModel = ListModel(["diseaseId", "name", "name_fa", "domains", "wikipedia_url", "ruleCount"])
featureSearchModel = ListModel(["featureId", "featureName", 'category', "unit", "status"])
manualModel = ListModel(["index", 'featureId', "featureName", "category", "value", "unit"])
reviewModel = ListModel(["index", 'resultId', "decision", "featureId", "featureName",
                        "value", 'unit', "confidence", "flag", "warning"])
referenceModel = ListModel(["sourceId", 'organization', "title", "year", 'url', "scope",
                           "accessed", "evidenceStatus"])
guidelineModel = ListModel(["diseaseId", "diseaseName", 'ruleId', 'ruleType', "ruleTypeLabel",
                           "expression", "population", "sourceId", "organization",
                           "year", "url", 'executable', 'domains'])
measuredModel = ListModel(["featureId", 'featureName', 'value', "unit", 'category', 'formula', "flag"])
derivedModel = ListModel(["featureId", "featureName", 'value', "unit", "category", "formula", "flag"])
clinicalModel = ListModel(["diseaseId", "name", "status", "statusLabel", "urgency",
                          "evidence", "limitations", "sources", "ruleId", "statement", "kind"])
insufficientModel = ListModel(["diseaseId", "name", "statusLabel", "ruleId", 'limitations',
                              'missingFeatures', "missingContext"])
conflictingModel = ListModel(["diseaseId", "name", "statusLabel", "ruleId", "evidence", "limitations"])
riskModel = ListModel(["diseaseKey", "nameEn", "modelName", "kind", "horizonYears",
                      'probability', 'riskLevel', "riskBand", "status", "scoreText",
                      "interpretationFa", "citation", "journal", 'publicationYear',
                      "referenceUrl", 'doi', "pmid", 'article_title',
                      "requiredFeatures", "missingFeatures", "exclusionReason", "warnings"])
historyModel = ListModel(["testId", "date", "title", "subtitle", "status"])
globalSearchModel = ListModel(["title", "subtitle", "kind", "itemId"])

MODELS = {
    'featureSearchModel': featureSearchModel,
    "manualModel": manualModel,
    "reviewModel": reviewModel,
    "referenceModel": referenceModel,
    "guidelineModel": guidelineModel,
    "measuredModel": measuredModel,
    "diseaseModel": diseaseModel,
    'derivedModel': derivedModel,
    "clinicalModel": clinicalModel,
    "insufficientModel": insufficientModel,
    "conflictingModel": conflictingModel,
    "riskModel": riskModel,
    "historyModel": historyModel,
    "globalSearchModel": globalSearchModel
}

def main():
    os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', "Fusion")
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "0")
    os.environ.setdefault("QSG_RENDER_LOOP", 'threaded')

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
    except ImportError:
        app = QGuiApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion(APP_VERSION)

    if sys.platform == "win32":
        try:  # taskbar/pin icon must be the app's own, not a generic python one
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SobhanBahrami.Hemoglyph.CDSS.1.3.1")
        except Exception:
            pass

    for icon_name in ['app_icon.ico', 'icon.ico', 'logo.ico', 'app_icon.png', 'logo.png']:
        icon_path = ROOT / icon_name
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            break

    # Register Qt platform plugins search paths
    exe_dir = Path(sys.executable).resolve().parent
    from PySide6.QtCore import QCoreApplication
    for p_dir in [
        ROOT / "PySide6" / "Qt" / "plugins",
        ROOT / "PySide6" / "plugins",
        ROOT / "plugins",
        exe_dir / "PySide6" / "Qt" / "plugins",
        exe_dir / "PySide6" / "plugins",
        exe_dir / "plugins",
    ]:
        if p_dir.is_dir():
            QCoreApplication.addLibraryPath(str(p_dir.resolve()))

    engine = QQmlApplicationEngine()

    # Register all potential QML search paths (including PySide6 bundled QML plugins for Nuitka)
    for qml_cand in [
        ROOT / "PySide6" / "Qt" / "qml",
        ROOT / "PySide6" / "qml",
        ROOT / "qml_plugins",
        exe_dir / "PySide6" / "Qt" / "qml",
        exe_dir / "PySide6" / "qml",
        exe_dir / "qml_plugins",
        ROOT / "Qt" / "qml",
        exe_dir / "Qt" / "qml",
        ROOT / "qml",
        ROOT / "qml" / "components",
        ROOT / "qml" / "pages",
        ROOT,
    ]:
        if qml_cand.exists():
            engine.addImportPath(str(qml_cand.resolve()))

    backend = Backend()

    ctx = engine.rootContext()
    ctx.setContextProperty("backend", backend)

    for name, model in MODELS.items():
        ctx.setContextProperty(name, model)

    # Auto-sanitize any lingering relative import in qml/LoginPage.qml
    _login_file = ROOT / "qml" / "LoginPage.qml"
    if _login_file.exists():
        try:
            _txt = _login_file.read_text(encoding="utf-8")
            if "../components" in _txt:
                _login_file.write_text(_txt.replace("../components", "components"), encoding="utf-8")
                logger.info("Auto-repaired relative import in qml/LoginPage.qml")
        except Exception as _e:
            pass

    main_qml = ROOT / "qml" / "Main.qml"
    if not main_qml.exists():
        main_qml = ROOT / "Main.qml"

    qml_errors = []
    def _on_qml_warning(warnings):
        for w in warnings:
            msg = w.toString()
            qml_errors.append(msg)
            logger.error(f"[QML Warning] {msg}")
    try:
        engine.warnings.connect(_on_qml_warning)
    except Exception:
        pass

    engine.load(QUrl.fromLocalFile(str(main_qml.resolve())))

    if not engine.rootObjects():
        err_details = "\n".join(qml_errors[-8:]) if qml_errors else "No QML warnings captured."
        err_msg = (
            f"Failed to load QML interface from:\n{main_qml}\n\n"
            f"Details:\n{err_details}\n\n"
            "Ensure you compiled with --include-qt-plugins=sensible,qml"
        )
        logger.error(err_msg)
        try:
            with open("qml_load_error.log", "w", encoding="utf-8") as f:
                f.write(err_msg + "\n\nAll warnings:\n" + "\n".join(qml_errors))
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, err_msg[:1000], "Hemoglyph UI Error", 0x10)
        except Exception:
            pass
        sys.exit(1)

    root_objects = engine.rootObjects()
    if root_objects:
        root_window = root_objects[0]
        if hasattr(root_window, "showMaximized"):
            root_window.showMaximized()

    QTimer.singleShot(0, backend.startBootstrap)

    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        err = traceback.format_exc()
        try:
            with open("hemoglyph_startup_error.log", "w", encoding="utf-8") as f:
                f.write(err)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Hemoglyph failed to start:\n\n{exc}\n\nSee hemoglyph_startup_error.log for full details.", "Hemoglyph Startup Error", 0x10)
        except Exception:
            pass
        sys.exit(1)

