from __future__ import annotations
FEATURE_ALIASES: dict[str, str] = {
    # Calcium & Minerals
    "calcium": "calcium_total",
    "ca": "calcium_total",
    "serum_calcium": "calcium_total",
    "total_calcium": "calcium_total",
    "ionized_calcium": "calcium_ionized",
    "ica": "calcium_ionized",
    "phos": "phosphate",
    "phosphorus": "phosphate",
    "phosphate_serum": "phosphate",
    "serum_phosphate": "phosphate",
    "mg": "magnesium",
    "magnesium_serum": "magnesium",

    # Bilirubin & Liver
    "bilirubin_total": "total_bilirubin",
    "t_bili": "total_bilirubin",
    "tbili": "total_bilirubin",
    "total_bili": "total_bilirubin",
    "bilirubin_direct": "direct_bilirubin",
    "d_bili": "direct_bilirubin",
    "dbili": "direct_bilirubin",
    "direct_bili": "direct_bilirubin",
    "bilirubin_indirect": "indirect_bilirubin",
    "i_bili": "indirect_bilirubin",
    "ast": "aspartate_aminotransferase",
    "sgot": "aspartate_aminotransferase",
    "alt": "alanine_aminotransferase",
    "sgpt": "alanine_aminotransferase",
    "alp": "alkaline_phosphatase",
    "alk_phos": "alkaline_phosphatase",
    "ggt": "gamma_glutamyl_transferase",
    "ldh": "lactate_dehydrogenase",
    "total_protein_serum": "total_protein",
    "serum_protein": "total_protein",
    "serum_albumin": "albumin",

    # Coagulation
    "inr": "international_normalized_ratio",
    "pt_inr": "international_normalized_ratio",
    "prothrombin_time_inr": "international_normalized_ratio",
    "pt": "prothrombin_time",
    "ptt": "activated_partial_thromboplastin_time",
    "aptt": "activated_partial_thromboplastin_time",

    # Thyroid & Endocrine
    "tsh": "thyroid_stimulating_hormone",
    "ft4": "free_thyroxine",
    "free_t4": "free_thyroxine",
    "free_thyroxine_ft4": "free_thyroxine",
    "t4_free": "free_thyroxine",
    "t3_free": "free_triiodothyronine",
    "ft3": "free_triiodothyronine",
    "anti_tpo": "thyroid_peroxidase_antibody",
    "tpo_ab": "thyroid_peroxidase_antibody",
    "tpo": "thyroid_peroxidase_antibody",
    "pth": "parathyroid_hormone",
    "pth_intact": "parathyroid_hormone_intact",
    "ipth": "parathyroid_hormone_intact",

    # Glucose / Diabetes
    "fbs": "fasting_plasma_glucose",
    "fpg": "fasting_plasma_glucose",
    "fasting_blood_sugar": "fasting_plasma_glucose",
    "fasting_glucose": "fasting_plasma_glucose",
    "bs": "glucose",
    "blood_sugar": "glucose",
    "rbs": "glucose",
    "random_glucose": "glucose",
    "hba1c": "hemoglobin_a1c",
    "a1c": "hemoglobin_a1c",
    "insulin": "fasting_serum_insulin",
    "fasting_insulin": "fasting_serum_insulin",
    "c_peptide": "fasting_c_peptide",
    "beta_hydroxybutyrate": "beta_hydroxybutyrate",
    "b_ohb": "beta_hydroxybutyrate",

    # Renal & Metabolic
    "cr": "creatinine",
    "scr": "creatinine",
    "serum_creatinine": "creatinine",
    "bun": "blood_urea_nitrogen",
    "urea": "urea",
    "serum_urea": "urea",
    "blood_urea": "urea",
    "urea_nitrogen": "blood_urea_nitrogen",
    "ua": "uric_acid",
    "uric": "uric_acid",

    # Electrolytes & Blood Gas
    "na": "sodium",
    "k": "potassium",
    "cl": "chloride",
    "hco3": "bicarbonate",
    "bicarb": "bicarbonate",
    "co2": "bicarbonate",
    "total_co2": "bicarbonate",
    "lactate": "lactate",
    "lactic_acid": "lactate",
    "serum_lactate": "lactate",
    "ph": "arterial_blood_ph",

    # Lipids
    "tc": "total_cholesterol",
    "chol": "total_cholesterol",
    "cholesterol": "total_cholesterol",
    "tg": "triglycerides",
    "triglyceride": "triglycerides",
    "hdl": "hdl_cholesterol",
    "ldl": "ldl_cholesterol_calculated",
    "ldl_c": "ldl_cholesterol_calculated",
    "ldl_cholesterol": "ldl_cholesterol_calculated",

    # CBC
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "hct": "hematocrit",
    "rbc": "red_blood_cell_count",
    "wbc": "white_blood_cell_count",
    "plt": "platelet_count",
    "platelets": "platelet_count",
    "rdw": "red_cell_distribution_width_cv",
    "rdw_cv": "red_cell_distribution_width_cv",
    "rdw_sd": "red_cell_distribution_width_sd",
    "red_cell_distribution_width": "red_cell_distribution_width_cv",
    "red_cell_distribution_width_cv": "red_cell_distribution_width_cv",
    "red_cell_distribution_width_sd": "red_cell_distribution_width_sd",
    "mcv": "mean_corpuscular_volume",
    "mch": "mean_corpuscular_hemoglobin",
    "mchc": "mean_corpuscular_hemoglobin_concentration",
    "neut": "neutrophils_percent",
    "neutrophil_pct": "neutrophils_percent",
    "lymph": "lymphocytes_percent",
    "lymphocyte_pct": "lymphocytes_percent",
    "mono": "monocytes_percent",
    "monocyte_pct": "monocytes_percent",
    "schistocytes": "schistocytes_percent",
    "schistocyte": "schistocytes_percent",
    "schistocyte_pct": "schistocytes_percent",

    # Cardiac & Inflammatory & Anemia
    "trop_i": "troponin_i",
    "hs_trop_i": "high_sensitivity_troponin_i",
    "troponin": "troponin_i",
    "ck_mb": "creatine_kinase_mb",
    "ckmb": "creatine_kinase_mb",
    "ck": "creatine_kinase_total",
    "creatine_kinase": "creatine_kinase_total",
    "total_creatine_kinase": "creatine_kinase_total",
    "total_ck": "creatine_kinase_total",
    "total_cpk": "creatine_kinase_total",
    "cpk": "creatine_kinase_total",
    "crp": "c_reactive_protein",
    "hs_crp": "high_sensitivity_c_reactive_protein",
    "esr": "erythrocyte_sedimentation_rate",
    "pct": "procalcitonin",
    "fer": "ferritin",
    "fe": "iron",
    "serum_iron": "iron",
    "tibc": "total_iron_binding_capacity",
    "b12": "vitamin_b12",
    "vit_b12": "vitamin_b12",
    "folate": "folate_serum",
    "serum_folate": "folate_serum",
    "hcy": "homocysteine",
    "homocysteine_serum": "homocysteine",

    # Autoimmune
    "c3": "complement_c3",
    "c4": "complement_c4",
    "ana": "antinuclear_antibody_titer",
    "anti_nuclear_antibodies_ana": "antinuclear_antibody_titer",
    "antinuclear_antibodies": "antinuclear_antibody_titer",
    "dsdna": "double_stranded_dna_antibody",
    "anti_dsdna": "double_stranded_dna_antibody",
    "anti_double_stranded_dna": "double_stranded_dna_antibody",
    "anti_dna": "double_stranded_dna_antibody",

    # Cortisol & Adrenal & Neuroendocrine
    "cortisol": "morning_cortisol",
    "serum_cortisol": "morning_cortisol",
    "morning_cortisol": "morning_cortisol",
    "cortisol_morning": "morning_cortisol",
    "acth": "adrenocorticotropic_hormone",
    "adrenocorticotropin": "adrenocorticotropic_hormone",

    # Heart Failure & Vasoactive Markers
    "bnp": "b_type_natriuretic_peptide",
    "brain_natriuretic_peptide": "b_type_natriuretic_peptide",
    "nt_probnp": "nt_probnp",
    "pro_bnp": "nt_probnp",
    "d_dimer": "d_dimer",
    "ddimer": "d_dimer",
    "fibrinogen": "fibrinogen",

    # Pancreas & GI & Specialized Metals
    "lipase": "lipase",
    "amylase": "amylase",
    "ceruloplasmin": "ceruloplasmin",
    "serum_copper": "serum_copper",
    "copper": "serum_copper",

    # Hematology & Hemolysis
    "reticulocytes": "reticulocytes",
    "retic_count": "reticulocytes",
    "reticulocyte_count": "reticulocytes",
    "haptoglobin": "serum_haptoglobin",
    "serum_haptoglobin": "serum_haptoglobin",

    # Rheumatology & Autoantibodies
    "rf": "rheumatoid_factor",
    "rheumatoid_factor": "rheumatoid_factor",
    "rf_igm": "rheumatoid_factor_igm_quantitative",
    "rheumatoid_factor_igm": "rheumatoid_factor_igm_quantitative",
    "anti_ccp": "anti_cyclic_citrullinated_peptide_igg",
    "anti_ccp_igg": "anti_cyclic_citrullinated_peptide_igg",
    "anti_cyclic_citrullinated_peptide": "anti_cyclic_citrullinated_peptide_igg",
    "trab": "tsh_receptor_antibody",
    "tsh_receptor_antibody": "tsh_receptor_antibody",

    # Renal & Urine Protein
    # Metanephrines & Catecholamines
    "plasma_free_normetanephrine": "plasma_free_normetanephrines",
    "plasma_free_metanephrine": "plasma_free_metanephrines",
    "plasma_normetanephrine": "plasma_free_normetanephrines",
    "plasma_normetanephrines": "plasma_free_normetanephrines",
    "plasma_metanephrine": "plasma_free_metanephrines",
    "plasma_metanephrines": "plasma_free_metanephrines",
    "normetanephrine": "plasma_free_normetanephrines",
    "normetanephrines": "plasma_free_normetanephrines",
    "metanephrine": "plasma_free_metanephrines",
    "metanephrines": "plasma_free_metanephrines",

    # Prostate Markers
    "psa": "total_prostate_specific_antigen",
    "total_psa": "total_prostate_specific_antigen",
    "psa_total": "total_prostate_specific_antigen",
    "prostate_specific_antigen": "total_prostate_specific_antigen",
    "psa_free": "free_prostate_specific_antigen",
    "free_psa": "free_prostate_specific_antigen",

    "uacr": "urine_albumin_to_creatinine_ratio",
    "urine_albumin_to_creatinine_ratio": "urine_albumin_to_creatinine_ratio",
    "upcr": "urine_protein_to_creatinine_ratio",
    "urine_protein_to_creatinine_ratio": "urine_protein_to_creatinine_ratio",
    "urine_protein_24h": "twenty_four_hour_urine_total_protein",
    "twenty_four_hour_urine_total_protein": "twenty_four_hour_urine_total_protein",
}


import hashlib
import json
import logging
import math
import os
import sys
import threading
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from calcu import (
    CalculationError,
    CalculationReport,
    DerivedFeatureEngine,
    PatientContext,
    convert_unit,
    normalize_unit,
)
from analyse_gidlines import (
    ClinicalContext,
    ClinicalRuleEngine,
    InterpretationReport,
)
from ocr import BloodLabPipeline, FeatureRegistry

logger = logging.getLogger(__name__)

def _determine_sarvis_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    exe_dir = Path(sys.executable).resolve().parent
    if (exe_dir / "HEMOGLYPH_FEATURE_REGISTRY.json.br").exists() or (exe_dir / "HEMOGLYPH_FEATURE_REGISTRY.json").exists():
        return exe_dir
    try:
        f_dir = Path(__file__).resolve().parent
        if (f_dir / "HEMOGLYPH_FEATURE_REGISTRY.json.br").exists() or (f_dir / "HEMOGLYPH_FEATURE_REGISTRY.json").exists():
            return f_dir
    except Exception:
        pass
    return exe_dir

ROOT = _determine_sarvis_root()
FEATURE_REGISTRY_PATH = ROOT / 'HEMOGLYPH_FEATURE_REGISTRY.json'
DISEASE_REGISTRY_PATH = ROOT / "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json"
SERVICE_VERSION = "4.0.0-clinical"
SCHEMA_VERSION = "3.0.0"
_ACTION_RANK = {"accept": 0, "review": 1, "edit_or_reject": 2}


class AnalysisServiceError(RuntimeError):
    pass


class InputValidationError(AnalysisServiceError):
    def __init__(self, message: str,
                 issues: Optional[list[dict[str, Any]]] = None):
        super().__init__(message)
        self.issues = issues or []


class ReviewValidationError(AnalysisServiceError):
    pass


@dataclass
class ConfirmedObservation:
    feature_id: str
    value: Any
    unit: Optional[str]
    confirmed: bool = True
    source: str = "manual"
    reported_reference: Optional[dict[str, Any]] = None
    flag: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewItem:
    result_id: str
    feature_id: str
    display_name: str
    value: Any
    unit: Optional[str]
    reported_reference: Optional[dict[str, Any]]
    flag: Optional[str]
    confidence: float
    suggested_action: str
    requires_confirmation: bool
    alternatives: list[dict[str, Any]]
    warnings: list[str]
    source: dict[str, Any]


@dataclass
class OCRReviewSession:
    review_session_id: str
    status: str
    created_at: str
    raw_text_hash: str
    items: list[ReviewItem]
    extraction_confidence: float
    warnings: list[str]
    errors: list[str]
    registry_version: str
    registry_feature_count: int

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass
class AnalysisResult:
    analysis_id: str
    status: str
    created_at: str
    schema_version: str
    versions: dict[str, str]
    context: dict[str, Any]
    observations: dict[str, dict[str, Any]]
    derived: dict[str, Any]
    interpretations: dict[str, Any]
    urgent_findings: list[dict[str, Any]]
    safety_flags: list[dict[str, Any]]
    insufficient_rules: list[dict[str, Any]]
    warnings: list[str]
    errors: list[str]
    audit: dict[str, Any]

    critical_alerts: list[dict[str, Any]] = field(default_factory=list)
    differential_diagnosis: list[dict[str, Any]] = field(
        default_factory=list)
    knowledge_graph_insights: dict[str, Any] = field(
        default_factory=dict)
    interference_corrections: list[dict[str, Any]] = field(
        default_factory=list)

    drug_interactions: list[dict[str, Any]] = field(default_factory=list)
    expanded_kg_insights: dict[str, Any] = field(default_factory=dict)
    differential_groups: dict[str, Any] = field(default_factory=dict)
    contraindications: dict[str, Any] = field(default_factory=dict)

    derived_patterns: list[dict[str, Any]] = field(default_factory=list)
    executive_summary: str = ""
    data_completeness: dict[str, Any] = field(default_factory=dict)
    multi_system_analysis: dict[str, Any] = field(default_factory=dict)
    complex_warnings: list[str] = field(default_factory=list)
    risk_predictions: list[dict[str, Any]] = field(default_factory=list)
    triaged_findings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "value") and value.__class__.__module__ == "enum":
        return value.value
    if isinstance(value, float) and (math.isnan(value)
                                     or math.isinf(value)):
        return None
    return value


try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


def _canonical_json(value: Any) -> str:
    safe = _json_safe(value)
    if HAS_ORJSON:
        return orjson.dumps(safe, option=orjson.OPT_SORT_KEYS).decode()
    return json.dumps(safe, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")).hexdigest()


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace("٫", ".").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _natije_id(item: Mapping[str, Any], index: int) -> str:
    identity = {
        "index": index,
        'feature_id': item.get("feature_id") or item.get("feature"),
        'raw_line': item.get("raw_line"),
        "page": item.get('page'),
        "line_number": item.get("line_number"),
        "value": item.get("original_value", item.get('value')),
        "unit": item.get("original_unit", item.get("unit")),
    }
    return "ocr_" + _sha256(identity)[:20]


def _stricter_action(a: str, b: str) -> str:
    return (a if _ACTION_RANK.get(str(a).casefold(), 2)
            >= _ACTION_RANK.get(str(b).casefold(), 2) else b)


class AnalysisService:

    def __init__(
        self,
        *,
        feature_registry_path: str | Path = FEATURE_REGISTRY_PATH,
        disease_registry_path: str | Path = DISEASE_REGISTRY_PATH,
        ocr_api_key: Optional[str] = None,
        ocr_backend: Optional[str] = None,
        execution_mode: str = "research",
        require_confirmed: bool = True,
        strict_units: bool = True,
    ):
        self.feature_registry_path = Path(feature_registry_path)
        self.disease_registry_path = Path(disease_registry_path)
        self.feature_registry = FeatureRegistry.shared(self.feature_registry_path)
        vision_api_key = ocr_api_key or os.getenv("OCR_API_KEY") or os.getenv("GROQ_API_KEY")
        vision_model = os.getenv("OCR_VISION_MODEL") or "qwen/qwen3.8-27b"
        backend = ocr_backend or os.getenv("OCR_BACKEND")
        if not backend or backend == "auto":
            backend = "vision" if vision_api_key else "tesseract"
        logger.info("🔧 OCR Configuration: backend=%s, model=%s", backend, vision_model)
        self.ocr = BloodLabPipeline(
            api_key=vision_api_key,
            registry=self.feature_registry,
            registry_path=self.feature_registry_path,
            enable_derived=False,
            backend=backend,
            language="fa",
            vision_model=vision_model,
        )
        self.calculator = DerivedFeatureEngine.shared(
            self.feature_registry_path,
            require_confirmed=require_confirmed,
        )
        self.interpreter = ClinicalRuleEngine(
            disease_registry_path=self.disease_registry_path,
            feature_registry_path=self.feature_registry_path,
            execution_mode=execution_mode,
            require_confirmed=require_confirmed,
            assume_rule_unit_for_scalars=not strict_units,
        )
        self.execution_mode = execution_mode
        self.require_confirmed = require_confirmed
        self.strict_units = strict_units
        self.feature_metadata = self.feature_registry.payload
        self.disease_metadata = self.interpreter.registry.payload
        self._cache: dict[str, Any] = {}
        self._cache_lock = threading.Lock()


    def healthcheck(self) -> dict[str, Any]:
        feature_count = len(self.feature_registry.features)
        disease_count = len(self.interpreter.registry.diseases)
        rule_count = len(self.interpreter.registry.rules)
        issues = []
        if feature_count < 1:
            issues.append("Feature registry is empty.")
        if disease_count < 1 or rule_count < 1:
            issues.append("Disease/rule registry is empty.")
        return {
            "ready": not issues,
            "execution_mode": self.execution_mode,
            "feature_count": feature_count,
            "disease_count": disease_count,
            "candidate_rule_count": rule_count,
            "ocr_backend": getattr(self.ocr.backend, 'name', "unknown"),
            "ocr_vision_model": getattr(self.ocr.backend, "model", None),
            "issues": issues,
            "versions": self._versions(),
        }

    def _versions(self) -> dict[str, str]:
        fm = self.feature_metadata.get("registry_metadata", {})
        dm = self.disease_metadata.get("registry_metadata", {})
        return {
            "schema": SCHEMA_VERSION,
            'analysis_service': SERVICE_VERSION,
            "feature_registry": str(fm.get("registry_version", "unknown")),
            "disease_registry": str(dm.get("version", "unknown")),
            'calculator': '3.0.0',
            'rule_engine': getattr(self.interpreter, "engine_version",
                                   "5.0.0-clinical"),
            "ocr": "3.0.0-research",
        }


    def amadesazi_ocr_review(
        self, upload: Any, panel_hint: Optional[str] = None
    ) -> OCRReviewSession:
        result = self.ocr.process(upload, panel_hint=panel_hint)
        # 2026-10-23: specimen provenance (HIL flags, specimen type, collection time) travels with the
        # session so analyze() can hand it to the engine's preanalytical gate when the clinician does not
        # override it in the questionnaire.
        self._last_preanalytical = dict(result.get("preanalytical") or {})
        if not result.get("extraction_success", False):
            return OCRReviewSession(
                review_session_id=str(uuid.uuid4()),
                status="ocr_failed",
                created_at=_utc_now(),
                raw_text_hash='',
                items=[],
                extraction_confidence=0.0,
                warnings=list(result.get("warnings") or []),
                errors=list(result.get("errors") or []),
                registry_version=self._versions()["feature_registry"],
                registry_feature_count=len(self.feature_registry.features),
            )
        return self.review_from_ocr_natije(result)

    def review_from_ocr_natije(
        self, result: Mapping[str, Any]
    ) -> OCRReviewSession:
        raw_text_hash = hashlib.sha256(
            str(result.get("raw_text", "")).encode("utf-8")
        ).hexdigest()
        items: list[ReviewItem] = []
        for index, raw in enumerate(result.get("results") or []):
            feature_id = str(
                raw.get("feature_id") or raw.get("feature") or "")
            if feature_id and feature_id not in self.feature_registry.features:
                continue
            unmapped = not feature_id
            confidence = float(raw.get("confidence") or 0.0)
            requires_confirmation = bool(
                raw.get("requires_confirmation", True))
            if confidence < 0.86:
                conf_suggested = "edit_or_reject"
            elif requires_confirmation:
                conf_suggested = "review"
            else:
                conf_suggested = "accept"
            ocr_suggested = str(
                raw.get("suggested_action") or "review").casefold()
            suggested = _stricter_action(ocr_suggested, conf_suggested)
            if unmapped:
                suggested = "edit_or_reject"
            warnings = list(raw.get("warnings") or [])
            if unmapped:
                warnings.append(
                    "Not mapped to the registry; select the correct "
                    "feature in Edit mode or reject.")
            warnings.extend(self._qa_warnings(raw))
            items.append(ReviewItem(
                result_id=_natije_id(raw, index),
                feature_id=feature_id,
                display_name=str(
                    raw.get("display_name")
                    or (self.feature_registry.display_name(feature_id)
                        if feature_id
                        else raw.get('raw_name') or "Unmapped row")),
                value=raw.get("value"),
                unit=normalize_unit(raw.get("unit")),
                reported_reference=(
                    raw.get("reported_reference")
                    or raw.get('reference')),
                flag=raw.get("flag"),
                confidence=confidence,
                suggested_action=suggested,
                requires_confirmation=True,
                alternatives=list(raw.get("alternatives") or []),
                warnings=warnings,
                source={
                    "page": raw.get("page"),
                    "line_number": raw.get("line_number"),
                    "raw_line": raw.get("raw_line"),
                    "raw_name": raw.get("raw_name"),
                    "original_value": raw.get("original_value"),
                    "original_unit": raw.get("original_unit"),
                },
            ))
        status = "awaiting_review" if items else "no_results"
        return OCRReviewSession(
            review_session_id=str(uuid.uuid4()),
            status=status,
            created_at=_utc_now(),
            raw_text_hash=raw_text_hash,
            items=items,
            extraction_confidence=float(
                result.get("confidence") or 0.0),
            warnings=list(result.get("warnings") or []),
            errors=list(result.get("errors") or []),
            registry_version=self._versions()["feature_registry"],
            registry_feature_count=len(self.feature_registry.features),
        )

    def _qa_warnings(self, raw: Mapping[str, Any]) -> list[str]:
        warns: list[str] = []
        num = _number(raw.get("value"))
        if num is None:
            return warns
        ref = raw.get('reported_reference') or raw.get("reference")
        flag = str(raw.get("flag") or "").upper()
        if isinstance(ref, Mapping):
            lo = _number(ref.get("low"))
            hi = _number(ref.get("high"))
            if (hi is not None and num > hi
                    and flag not in {"H", "HIGH", "HH", "CRIT",
                                     "CRITICAL", "B", "A"}):
                warns.append(
                    "Value is above the printed reference high but no "
                    "H flag was captured; verify transcription.")
            if (lo is not None and num < lo
                    and flag not in {"L", "LOW", 'LL', "CRIT",
                                     "CRITICAL", "B", "A"}):
                warns.append(
                    "Value is below the printed reference low but no "
                    'L flag was captured; verify transcription.')
        return warns

    # The reviewer's edits win over OCR, but only for fields they actually
    # touched - untouched fields keep their original confidence score.
    def emal_review_decisions(
        self,
        session: OCRReviewSession | Mapping[str, Any],
        decisions: Sequence[Mapping[str, Any]],
        *,
        require_decision_for_every_item: bool = True,
    ) -> dict[str, dict[str, Any]]:
        session_dict = (session.to_dict()
                        if isinstance(session, OCRReviewSession)
                        else dict(session))
        items = {x['result_id']: x
                 for x in session_dict.get("items", [])}
        decision_map: dict[str, Mapping[str, Any]] = {}
        issues: list[dict[str, Any]] = []
        for decision in decisions:
            result_id = str(decision.get("result_id", ""))
            if result_id not in items:
                issues.append(
                    {"result_id": result_id,
                     "error": 'Unknown review item.'})
                continue
            if result_id in decision_map:
                issues.append(
                    {"result_id": result_id,
                     'error': "Duplicate decision."})
            decision_map[result_id] = decision
        if require_decision_for_every_item:
            for result_id in items:
                if result_id not in decision_map:
                    issues.append(
                        {"result_id": result_id,
                         "error": 'Review decision is required.'})
        if issues:
            raise ReviewValidationError(
                f"Invalid OCR review decisions: {issues}")
        confirmed: dict[str, dict[str, Any]] = {}
        for result_id, item in items.items():
            decision = decision_map.get(result_id)
            if not decision:
                continue
            action = str(decision.get("action", "")).casefold()
            if action == 'reject':
                continue
            if action not in {"accept", "edit"}:
                raise ReviewValidationError(
                    f"Unsupported action {action!r} for {result_id}.")
            feature_id = str(
                decision.get('feature_id', item["feature_id"]))
            if (not feature_id
                    or feature_id not in self.feature_registry.features):
                raise ReviewValidationError(
                    f"Row {result_id}: select a valid feature in "
                    f"Edit mode (or reject it).")
            value = decision.get("value", item.get("value"))
            unit = normalize_unit(
                decision.get("unit", item.get("unit")))
            if not unit:
                feat_m = (self.feature_registry.get(feature_id).get('measurement') or {})
                canonical = feat_m.get("canonical_unit")
                allowed = feat_m.get("allowed_units") or []
                if canonical in ('1', 'ratio', '[pH]', 'score', '', None) or '1' in allowed or 'ratio' in allowed:
                    unit = canonical or "1"
            try:
                self._etebarsanji_single_observation(
                    feature_id, value, unit, confirmed=True)
            except InputValidationError as exc:
                raise ReviewValidationError(
                    f"Invalid value for {feature_id}: {exc}",
                ) from exc
            record = {
                "value": value,
                "unit": unit,
                "confirmed": True,
                "source": "ocr_reviewed",
                "reported_reference": decision.get(
                    "reported_reference",
                    item.get("reported_reference")),
                "flag": decision.get("flag", item.get('flag')),
                "metadata": {
                    "ocr_confidence": item.get("confidence"),
                    "review_action": action,
                    "review_session_id": session_dict.get(
                        "review_session_id"),
                },
                'lineage': {
                    "result_id": result_id,
                    "source": item.get("source"),
                },
            }
            old = confirmed.get(feature_id)
            if old and (old["value"] != value
                        or old.get('unit') != unit):
                old_action = (
                    old.get("metadata") or {}).get("review_action")
                old_conf = float(
                    (old.get("metadata") or {}).get(
                        'ocr_confidence') or 0)
                new_conf = float(item.get("confidence") or 0)
                note = ("Conflicting duplicate for the same analyte; "
                        "one row was kept and the other discarded.")
                if ((action == "edit" and old_action != 'edit')
                        or (action == old_action
                            and new_conf > old_conf)):
                    record.setdefault("warnings", []).append(note)
                    confirmed[feature_id] = record
                else:
                    old.setdefault("warnings", []).append(note)
                continue
            confirmed[feature_id] = record
        return confirmed


    def _etebarsanji_single_observation(
        self, feature_id: str, value: Any,
        unit: Optional[str], confirmed: bool,
    ) -> None:
        if feature_id not in self.feature_registry.features:
            raise InputValidationError(
                "Unknown feature_id.",
                [{"feature_id": feature_id,
                  "error": "not_in_registry"}])
        if self.require_confirmed and not confirmed:
            raise InputValidationError(
                "Unconfirmed observation is not analyzable.",
                [{"feature_id": feature_id, "error": "unconfirmed"}])
        if (value is None
                or (isinstance(value, float)
                    and not math.isfinite(value))):
            raise InputValidationError(
                'Observation value is missing or non-finite.',
                [{"feature_id": feature_id,
                  "error": "invalid_value"}])
        value_type = (
            self.feature_registry.get(feature_id).get('measurement')
            or {}).get("value_type")
        if value_type in {"qualitative", 'ordinal', "nominal",
                          "categorical"}:
            if not str(value).strip():
                raise InputValidationError(
                    "Qualitative value cannot be empty.",
                    [{'feature_id': feature_id,
                      "error": "empty_qualitative"}])
            return
        if value_type == "quantitative" and _number(value) is None:
            raise InputValidationError(
                "Quantitative feature requires numeric value.",
                [{"feature_id": feature_id, 'error': "not_numeric"}])
        if (self.strict_units and value_type == "quantitative"
                and not unit):
            feat_m = (self.feature_registry.get(feature_id).get('measurement') or {})
            canonical = feat_m.get("canonical_unit")
            allowed = feat_m.get("allowed_units") or []
            is_dimensionless = (canonical in ('1', 'ratio', '[pH]', 'score', '', None) or '1' in allowed or 'ratio' in allowed)
            if not is_dimensionless:
                raise InputValidationError(
                    'Quantitative feature requires explicit unit in '
                    "strict mode.",
                    [{"feature_id": feature_id, "error": 'missing_unit'}])

    def _plausibility_warnings(
        self, feature_id: str, value: Any, unit: Optional[str],
    ) -> list[str]:
        meta = self.feature_registry.get(feature_id)
        validation = meta.get("validation") or {}
        plausible = validation.get("plausible") or {}
        num = _number(value)
        if num is None:
            return []
        canon = (meta.get("units") or {}).get("canonical")
        if canon and unit:
            try:
                num = convert_unit(num, unit, canon, feature_id)
            except CalculationError:
                return [
                    f"{feature_id}: unit {unit!r} is not convertible "
                    f"to {canon!r}; verify the unit."]
        warns: list[str] = []
        lo = _number(plausible.get("low")) if plausible else None
        hi = _number(plausible.get("high")) if plausible else None
        if lo is not None and num < lo:
            warns.append(
                f"{feature_id}: value below plausible minimum "
                f"({lo:g}); verify decimal point/unit.")
        if hi is not None and num > hi:
            warns.append(
                f"{feature_id}: value above plausible maximum "
                f"({hi:g}); verify decimal point/unit.")
        if plausible:
            mean = _number((meta.get("reference") or {}).get("mean"))
            if mean is None:
                mean = (lo + hi)/2 if lo is not None and hi is not None else None
            if mean and mean != 0:
                deviation_pct = abs(num - mean) / abs(mean) * 100
                if deviation_pct > 300:
                    warns.append(f"{feature_id}: extreme deviation {deviation_pct:.0f}% from expected mean; verify sample integrity.")
        return warns

    def _complex_plausibility_checks(
        self, observations: Mapping[str, Mapping[str, Any]]
    ) -> list[str]:
        """Super-accurate cross-analyte plausibility for complex diagnoses."""
        warns = []
        def get_val(fid):
            rec = observations.get(fid)
            if not rec:
                return None
            return _number(rec.get("value"))
        tb = get_val("total_bilirubin") or get_val("bilirubin_total")
        db = get_val("direct_bilirubin") or get_val("bilirubin_direct")
        ib = get_val("indirect_bilirubin") or get_val("bilirubin_indirect")
        if tb and db and ib:
            if abs((db + ib) - tb) > tb * 0.3 and tb > 0.5:
                warns.append(f"Bilirubin fractions mismatch: direct {db:.2f} + indirect {ib:.2f} != total {tb:.2f}; check lab error.")
        ca = get_val("calcium_total") or get_val("calcium")
        alb = get_val("albumin")
        if ca and alb and alb < 2.0:
            warns.append(f"Albumin {alb:.1f} critically low — calcium {ca:.1f} may be falsely low; corrected calcium essential.")
        na = get_val("sodium")
        glu = get_val("glucose") or get_val("fasting_plasma_glucose")
        if na and glu and glu > 400 and na < 130:
            warns.append(f"Hyponatremia with severe hyperglycemia: Na {na:.0f}, Glu {glu:.0f} — likely pseudohyponatremia; calculate corrected Na.")
        k = get_val("potassium")
        if k and k > 6.0:
            if ca and ca <= 6.5:
                warns.append(f"Pre-analytical plausibility alert: Extreme hyperkalemia (K={k:.1f}) with hypocalcemia (Ca={ca:.1f}) strongly suggests K2/K3-EDTA phlebotomy contamination artifact.")
            else:
                warns.append(f"Hyperkalemia K={k:.1f} — verify hemolysis, sample handling, and urgent ECG; risk of arrhythmia.")
        hb = get_val("hemoglobin")
        mcv = get_val("mean_corpuscular_volume")
        rdw = get_val("red_cell_distribution_width") or get_val("rdw")
        if hb and hb < 10 and mcv and 80 <= mcv <= 100 and rdw and rdw > 16:
            warns.append(f"Normocytic anemia with high RDW {rdw:.1f} — suggests mixed deficiency (iron + B12/folate) or early response to therapy; check peripheral smear.")

        tp = get_val("total_protein") or get_val("protein_total")
        glob = get_val("globulin")
        if tp and alb and glob:
            if (alb + glob) > tp * 1.15:
                warns.append(f"Protein fractions discrepancy: Albumin ({alb:.1f}) + Globulin ({glob:.1f}) exceeds Total Protein ({tp:.1f} g/dL).")

        hct = get_val("hematocrit")
        rbc = get_val("red_blood_cell_count")
        if hct and rbc and rbc > 1.0 and hct > 10.0 and mcv:
            calc_mcv = hct * 10.0 / rbc
            if abs(mcv - calc_mcv) > calc_mcv * 0.15:
                warns.append(f"Coulter index discrepancy: Reported MCV ({mcv:.1f} fL) differs by >15% from HCT/RBC ({calc_mcv:.1f} fL).")

        return warns

    def _analyze_multi_system(
        self, observations: Mapping[str, Mapping[str, Any]],
        calculation_report: CalculationReport,
        interpretation_report: Any,
        context: Optional[PatientContext] = None,
    ) -> dict[str, Any]:
        """Super-accurate multi-system complexity analysis."""
        result = {
            "systems_involved": [],
            "complexity_score": 0,
            "multi_system_patterns": [],
            "recommendations": [],
        }
        def gv(fid):
            r = observations.get(fid)
            return _number(r.get("value")) if r else None
        renal_markers = ["creatinine", "blood_urea_nitrogen", "egfr_ckd_epi_creatinine", "urine_albumin_to_creatinine_ratio", "cystatin_c"]
        liver_markers = ["alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase", "gamma_glutamyl_transferase", "total_bilirubin", "direct_bilirubin", "albumin"]
        hematologic = ["hemoglobin", "white_blood_cell_count", "platelet_count", "mean_corpuscular_volume", "reticulocytes"]
        endocrine = ["thyroid_stimulating_hormone", "free_thyroxine", "fasting_plasma_glucose", "hemoglobin_a1c", "cortisol_8am", "cortisol_morning", "morning_cortisol", "parathyroid_hormone"]
        electrolyte = ["sodium", "potassium", "calcium_total", "phosphate", "magnesium", "bicarbonate", "chloride"]
        inflammatory = ["c_reactive_protein", "erythrocyte_sedimentation_rate", "procalcitonin", "ferritin"]
        cardiovascular = ["troponin_i", "high_sensitivity_troponin_i", "b_type_natriuretic_peptide", "nt_probnp", "creatine_kinase_mb", "myoglobin"]
        systems = {
            "renal": renal_markers,
            "hepatic": liver_markers,
            "hematologic": hematologic,
            "endocrine": endocrine,
            "electrolyte": electrolyte,
            "inflammatory": inflammatory,
            "cardiovascular": cardiovascular,
        }
        for sys_name, markers in systems.items():
            count = sum(1 for m in markers if m in observations)
            is_abnormal = False
            for m in markers:
                r = observations.get(m)
                if not r:
                    continue
                v = _number(r.get("value"))
                if v is None:
                    continue
                flg = str(r.get("flag") or "").upper()
                if flg in ("H", "HIGH", "L", "LOW", "CRIT", "CRITICAL"):
                    is_abnormal = True
                    break
                if m in ("c_reactive_protein", "procalcitonin") and v > 5.0:
                    is_abnormal = True; break
                if m in ("fasting_plasma_glucose", "glucose") and (v > 125.0 or v < 70.0):
                    is_abnormal = True; break
                if m == "hemoglobin_a1c" and v >= 6.5:
                    is_abnormal = True; break
                if m == "creatinine":
                    cr_max = 0.70 if (context and context.age_years is not None and context.age_years < 12) else 1.3
                    if v > cr_max:
                        is_abnormal = True; break
                if m == "alkaline_phosphatase":
                    alp_max = 850.0 if (context and context.age_years is not None and context.age_years < 16) else 130.0
                    if v > alp_max:
                        is_abnormal = True; break
                if m in ("alanine_aminotransferase", "aspartate_aminotransferase") and v > 50.0:
                    is_abnormal = True; break
                if m in ("total_bilirubin", "direct_bilirubin") and v > 1.5:
                    is_abnormal = True; break
                if m == "platelet_count":
                    plt_val = v if v <= 1000.0 else v / 1000.0
                    if plt_val < 150.0 or plt_val > 450.0:
                        is_abnormal = True; break
                if m == "white_blood_cell_count":
                    wbc_val = v if v <= 100.0 else v / 1000.0
                    wbc_max = 13.5 if (context and context.age_years is not None and context.age_years < 12) else 11.0
                    if wbc_val < 4.0 or wbc_val > wbc_max:
                        is_abnormal = True; break
                if m == "sodium" and (v < 135.0 or v > 145.0):
                    is_abnormal = True; break
                if m == "potassium" and (v < 3.5 or v > 5.2):
                    is_abnormal = True; break
                if m == "bicarbonate" and (v < 22.0 or v > 29.0):
                    is_abnormal = True; break
                if m in ("troponin_i", "high_sensitivity_troponin_i") and v > 0.04:
                    is_abnormal = True; break
                if m in ("b_type_natriuretic_peptide", "nt_probnp") and v > 100.0:
                    is_abnormal = True; break
                if m == "creatine_kinase_mb" and v > 5.0:
                    is_abnormal = True; break

            if is_abnormal:
                result["systems_involved"].append(sys_name)
                result["complexity_score"] += 1
        if "cardiovascular" in result["systems_involved"] and "renal" in result["systems_involved"]:
            result["multi_system_patterns"].append({
                "pattern": "cardiorenal",
                "title": "Cardiorenal Syndrome (Types 1-5)",
                "title_fa": "سندروم کاردیورنال (انواع ۱ تا ۵)",
                "interpretation": "Cardiorenal syndrome (Type 1-5): dual cardiac and renal impairment. Monitor hemodynamics, volume status, and avoid nephrotoxic agents.",
                "interpretation_fa": "سندروم کاردیورنال: نارسایی هم‌زمان قلبی و کلیوی. پایش دقیق همودینامیک، بالانس مایعات و پرهیز از داروهای نفروتوکسیک الزامی است."
            })
        if "hepatic" in result["systems_involved"] and "renal" in result["systems_involved"]:
            result["multi_system_patterns"].append({
                "pattern": "hepatorenal",
                "title": "Hepatorenal Axis Dysfunction (HRS-AKI)",
                "title_fa": "اختلال محور هپاتورنال (سندروم هپاتورنال)",
                "interpretation": "Hepatorenal axis dysfunction: severe hepatic impairment with renal azotemia. Assess for Hepatorenal Syndrome (HRS-AKI), urinary sodium, and volume challenge.",
                "interpretation_fa": "اختلال محور هپاتورنال: آسیب توأم کبدی و کلیوی (بررسی HRS-AKI، سدیم ادرار و پایش پاسخ به آلبومین)."
            })
        if "renal" in result["systems_involved"] and "hematologic" in result["systems_involved"]:
            result["multi_system_patterns"].append({
                "pattern": "renal+hematologic",
                "title": "Renal-Hematologic Axis Involvement",
                "title_fa": "درگیری توأم کلیوی و خونی",
                "interpretation": "CKD with anemia or marrow infiltration — check EPO, iron, B12, PTH, proteinuria.",
                "interpretation_fa": "درگیری توأم کلیوی و خونی (آنمی ناشی از نارسایی کلیه یا دیسکرازی مغز استخوان)."
            })
        if "hepatic" in result["systems_involved"] and "hematologic" in result["systems_involved"]:
            result["multi_system_patterns"].append({
                "pattern": "hepatic+hematologic",
                "title": "Hepatosplenic-Hematologic Axis Dysfunction",
                "title_fa": "اختلال محور کبدی-خونی و هیپراسپلنیسم",
                "interpretation": "Liver disease with cytopenias — hypersplenism, alcohol, viral hepatitis, or marrow failure.",
                "interpretation_fa": "بیماری کبدی همراه با سیتوپنی (هیپراسپلنیسم، اثر الکل، هپاتیت یا نارسایی مغز استخوان)."
            })
        if "endocrine" in result["systems_involved"] and "electrolyte" in result["systems_involved"]:
            result["multi_system_patterns"].append({
                "pattern": "endocrine+electrolyte",
                "title": "Endocrine-Electrolyte Decompensation",
                "title_fa": "بحران غدد و عدم تعادل الکترولیتی",
                "interpretation": "Endocrine disorder affecting electrolytes — check adrenal, thyroid, PTH axis.",
                "interpretation_fa": "اختلال غدد همراه با عدم تعادل الکترولیتی شدید (نیازمند بررسی محور آدرنال، پاراتیروئید یا کتواسیدوز)."
            })
        # Check metabolic acid-base crisis
        gluc_v = None
        for _gk in ("glucose", "fasting_plasma_glucose", "blood_glucose"):
            if _gk in observations:
                gluc_v = _number(observations[_gk].get("value"))
                if gluc_v is not None: break
        bicarb_v = None
        if "bicarbonate" in observations:
            bicarb_v = _number(observations["bicarbonate"].get("value"))
        if (gluc_v is not None and (gluc_v > 250.0 or gluc_v < 60.0)) and (bicarb_v is not None and bicarb_v < 18.0):
            result["multi_system_patterns"].append({
                "pattern": "metabolic_acid_base_crisis",
                "title": "Metabolic & Acid-Base Crisis (DKA/HHS)",
                "title_fa": "بحران متابولیک و اسید-باز (کتواسیدوز / کما)",
                "interpretation": "Severe metabolic decompensation with high anion gap metabolic acidosis. Urgent protocolized fluid and electrolyte resuscitation required.",
                "interpretation_fa": "بحران حاد متابولیک همراه با اسیدوز متابولیک شدید (DKA/HHS). احیای فوری با مایعات وریدی، انسولین و پایش مکرر پتاسیم الزامی است."
            })
        if "inflammatory" in result["systems_involved"] and len(result["systems_involved"]) >= 3:
            result["multi_system_patterns"].append({
                "pattern": "systemic_sepsis_or_inflammation",
                "title": "Systemic Multi-Organ Inflammatory Response (SIRS / Sepsis)",
                "title_fa": "پاسخ التهابی سیستمیک و نارسایی چندارگانی (سپسیس/SIRS)",
                "interpretation": "Marked systemic inflammation with multi-organ dysfunction — evaluate for sepsis/septic shock, macrophage activation, or autoimmune flare.",
                "interpretation_fa": "پاسخ التهابی سیستمیک شدید همراه با نارسایی چندارگانی (ارزیابی فوری سپسیس/شوک سپتیک یا بحران خودایمنی)."
            })
        if len(result["systems_involved"]) >= 3:
            result["recommendations"].append("Multi-system involvement detected — consider systemic disease (SLE, sepsis, malignancy, metabolic syndrome). Recommend comprehensive review.")
            result["complexity_score"] += 5
        if hasattr(interpretation_report, 'derived_patterns'):
            dp = interpretation_report.derived_patterns or []
            high_sig = [p for p in dp if isinstance(p, dict) and p.get("significance")=="high"]
            if len(high_sig) >= 2:
                result["complexity_score"] += len(high_sig)*2
                result["multi_system_patterns"].append({"pattern": "multiple_high_significance_derived", "interpretation": f"{len(high_sig)} high-significance derived patterns — complex diagnosis likely."})
        return result


    def etebarsanji_confirmed_inputs(
        self, inputs: Mapping[str, Any],
    ) -> tuple[dict[str, dict[str, Any]], list[str]]:
        normalized: dict[str, dict[str, Any]] = {}
        warnings: list[str] = []
        issues: list[dict[str, Any]] = []
        for raw_fid, raw in inputs.items():
            clean_key = str(raw_fid).lower().strip()
            feature_id = FEATURE_ALIASES.get(clean_key, raw_fid)
            if feature_id not in self.feature_registry.features and clean_key in FEATURE_ALIASES:
                feature_id = FEATURE_ALIASES[clean_key]
            if isinstance(raw, Mapping):
                value = raw.get("value")
                unit = normalize_unit(raw.get('unit'))
                confirmed = bool(
                    raw.get("confirmed",
                            not raw.get("requires_confirmation",
                                        False)))
                source = str(raw.get("source", "manual"))
                record = dict(raw)
            else:
                value, unit, confirmed, source = (
                    raw, None, True, "manual_scalar")
                record = {"value": raw, "unit": None,
                          "confirmed": True, "source": source}
                warnings.append(
                    f"{feature_id}: scalar input lacks explicit "
                    f"unit and lineage.")
            try:
                self._etebarsanji_single_observation(
                    feature_id, value, unit, confirmed)
            except InputValidationError as exc:
                issues.extend(exc.issues)
                continue
            warnings.extend(
                self._plausibility_warnings(feature_id, value, unit))
            num_val = _number(value)
            if num_val is not None:
                value = num_val
            record.update({
                "value": value, 'unit': unit,
                "confirmed": confirmed, "source": source,
            })
            normalized[feature_id] = _json_safe(record)
        if issues:
            raise InputValidationError(
                "One or more observations are invalid.", issues)
        if not normalized:
            raise InputValidationError(
                "No confirmed observations were supplied.")
        return normalized, warnings


    def _merge_preanalytical(
        self, patient: "PatientContext | Mapping[str, Any]",
    ) -> "PatientContext | Mapping[str, Any]":
        """Add OCR-detected specimen flags (hemolysis / lipemia / icterus, specimen type,
        collection time) to the clinical context unless the clinician already set them.
        Keys are the ones analyse_gidlines.preanalytical_gate reads from context.extra."""
        pre = getattr(self, "_last_preanalytical", None) or {}
        flags = {k: True for k, v in (pre.get("flags") or {}).items() if v and k in ("hemolysis", "lipemia", "icterus")}
        if (not flags and not pre.get("specimen") and not pre.get("collected_at")) or isinstance(patient, PatientContext):
            return patient
        merged = dict(patient or {})
        for k, v in flags.items():
            merged.setdefault(k, v)
        if pre.get("specimen"):
            merged.setdefault("specimen_type", pre["specimen"])
        if pre.get("collected_at"):
            merged.setdefault("specimen_collected_at", pre["collected_at"])
        merged.setdefault("preanalytical_source", "ocr_report_text")
        return merged

    @staticmethod
    def _contexts(
        patient: PatientContext | Mapping[str, Any],
    ) -> tuple[PatientContext, ClinicalContext, dict[str, Any]]:
        if isinstance(patient, PatientContext):
            calc_context = patient
            clinical_context = ClinicalContext.from_any(patient)
            raw = asdict(patient)
            return calc_context, clinical_context, raw
        raw = dict(patient)
        aliases = {
            "Age": "age_years", "age": "age_years",
            "Sex": "sex_at_birth", "gender": 'sex_at_birth',
            "Weight": 'weight_kg', "Height": "height_cm",
            "Fasting": "fasting", "Pregnant": "pregnant",
            "persistence_days": "persistence_days",
            "timed_level": "timed_level",
            "change_from_baseline": 'change_from_baseline',
            "within_hours": "within_hours",
            'ogtt_75g': 'ogtt_75g',
            "vasopressor_required": 'vasopressor_required',
            "after_adequate_resuscitation":
                "after_adequate_resuscitation",
        }
        normalized = {aliases.get(k, k): v for k, v in raw.items()}
        calc_fields = set(PatientContext.__dataclass_fields__)
        calc_context = PatientContext(
            **{k: v for k, v in normalized.items()
               if k in calc_fields})
        clinical_context = ClinicalContext.from_any(normalized)
        return calc_context, clinical_context, normalized

    @staticmethod
    def _etebarsanji_context(context: PatientContext) -> list[str]:
        warnings = []
        if context.age_years is None:
            warnings.append(
                "Age is missing; age-dependent formulas and "
                "population rules may be unavailable.")
        elif not 0 <= context.age_years <= 120:
            raise InputValidationError(
                "age_years is outside supported bounds.")
        if (context.weight_kg is not None
                and not 0 < context.weight_kg <= 500):
            raise InputValidationError(
                "weight_kg is outside supported bounds.")
        if (context.height_cm is not None
                and not 20 <= context.height_cm <= 280):
            raise InputValidationError(
                "height_cm is outside supported bounds.")
        if context.sex_at_birth is None:
            # The clinician now enters demographics per patient, so a blank
            # sex is an ordinary state rather than a configuration error.
            # It still has to be said out loud: haemoglobin, ferritin and
            # creatinine all have sex-specific limits, and several risk
            # models refuse to run without it.
            warnings.append(
                "Sex is missing; sex-specific reference ranges fall back "
                "to general limits and sex-dependent risk models are "
                "skipped.")
        elif context.normalized_jensiat() is None:
            warnings.append(
                "sex_at_birth is not recognized; sex-specific "
                "equations will be skipped.")
        return warnings

    def _triage_clinical_findings(
        self,
        normalized: Mapping[str, Mapping[str, Any]],
        calculation_report: CalculationReport,
        interpretation_report: Any,
        calc_context: PatientContext,
        critical_alerts: list[dict[str, Any]],
        differential_diagnosis: list[dict[str, Any]],
        derived_patterns: list[dict[str, Any]],
        risk_predictions: list[dict[str, Any]],
        contraindications: dict[str, Any],
    ) -> dict[str, Any]:
        """Synthesizes all findings into a tri-tier actionable clinical priority matrix.

        Tier 1 (🔴 Immediate Emergency / < 2 Hours):
          - Pre-analytical critical specimen artifacts (EDTA carryover, severe in-vitro hemolysis)
          - Lethal contraindications (Platelet transfusion in TTP/TMA, Beta-blockade in Pheo)
          - True critical panic values (Hyperkalemia K>=6.0, Severe Thrombocytopenia Plt<30k, Extreme Acidosis)
          - Cytokine storm (HLH/MAS), Acute Severe Hepatocellular Injury (Transaminases > 500)

        Tier 2 (🟡 Subacute Actionable Diagnostics / 24-72 Hours):
          - Top ranked differential diagnoses (prob >= 25%) with Gold Standard Next Tests
          - Pre-analytical correction advisories (Pseudohyponatremia due to severe TG/Protein)
          - Pediatric eGFR height requirement notices
          - High/Critical 10-year chronic disease risk predictions (ASCVD/CVD >= 20%)
          - Moderate renal impairment drug adjustments (eGFR 30-59 mL/min)

        Tier 3 (🟢 Physiological Reassurance & Baseline Monitoring):
          - Age- and cohort-adapted normal physiology (Pediatric growth ALP 300-850 U/L, Pregnancy hemodilution)
          - Physiological De Ritis AST/ALT ratio in normal enzymes
          - Normal Delta Gap / Delta Ratio baseline
          - Negative screens across all evaluated organ axes
          - Lifestyle and preventive wellness guidance
        """
        tier_1: list[dict[str, Any]] = []
        tier_2: list[dict[str, Any]] = []
        tier_3: list[dict[str, Any]] = []

        calc_dict = calculation_report.results
        k_val = _number(normalized.get("potassium", {}).get("value"))
        ca_val = _number(normalized.get("calcium_total", {}).get("value")) or _number(normalized.get("calcium", {}).get("value"))
        plt_val = _number(normalized.get("platelet_count", {}).get("value"))
        ast_val = _number(normalized.get("aspartate_aminotransferase", {}).get("value"))
        alt_val = _number(normalized.get("alanine_aminotransferase", {}).get("value"))

        # -------------------------------------------------------------------
        # TIER 1: IMMEDIATE CRITICAL EMERGENCIES (< 2 HOURS)
        # -------------------------------------------------------------------
        # 1.1 Pre-analytical EDTA Tube Contamination
        edta_rec = calc_dict.get("edta_contamination_alert")
        suppress_hyperkalemia = False
        if edta_rec:
            edta_val = edta_rec.value if hasattr(edta_rec, "value") else edta_rec.get("value")
            suppress_hyperkalemia = True
            tier_1.append({
                "id": "edta_contamination_critical",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 2 hours",
                "category": "PREANALYTICAL_CRITICAL",
                "title": f"Pre-Analytical Alert: K2/K3-EDTA Tube Carryover ({edta_val})",
                "title_fa": f"هشدار حیاتی پیش‌آزمایشگاهی: آلودگی لوله با ضد انعقاد EDTA (سطح {edta_val})",
                "action_en": f"Extreme hyperkalemia (K={k_val or 0:.1f} mmol/L) with severe hypocalcemia (Ca={ca_val or 0:.1f} mg/dL) is an artifact of phlebotomy tube carryover. DO NOT administer calcium gluconate, insulin/glucose, or emergency dialysis. Immediately redraw blood using a plain serum clot tube and verify with a 12-lead ECG.",
                "action_fa": "پتاسیم بالا همراه با افت شدید کلسیم ناشی از خطای ترتیب پر کردن لوله‌ها حین خونگیری است. اکیداً از تجویز درمان هایپرکالمی یا دیالیز خودداری کنید؛ تکرار فوری خونگیری با لوله لخته و نوار قلب الزامی است.",
            })

        # 1.2 Pre-analytical In-Vitro Hemolysis
        hemo_rec = calc_dict.get("in_vitro_hemolysis_alert")
        if hemo_rec:
            tier_1.append({
                "id": "in_vitro_hemolysis_advisory",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 2 hours",
                "category": "PREANALYTICAL_ADVISORY",
                "title": "Pre-Analytical Alert: Mechanical In-Vitro Hemolysis Suspected",
                "title_fa": "هشدار پیش‌آزمایشگاهی: احتمال بالای همولیز مکانیکی حین خونگیری",
                "action_en": "Elevated potassium and LDH with normal haptoglobin indicates red cell trauma during venipuncture rather than in-vivo intravascular hemolysis. Inspect serum coloration.",
                "action_fa": "افزایش هم‌زمان پتاسیم و LDH در حضور هاپتوگلوبین نرمال ناشی از ترومای خونگیری است و همولیز پاتولوژیک داخل عروق را رد می‌کند.",
            })

        # 1.3 Lethal Contraindication: TTP / TMA Platelet Transfusion
        has_tma = any(p.get("pattern_id") == "tma_ttp_pattern" for p in derived_patterns) or any(
            d.get("disease_id") in ("thrombotic_thrombocytopenic_purpura", "thrombotic_microangiopathy") and d.get("probability", 0) > 0.35
            for d in differential_diagnosis
        )
        if has_tma:
            tier_1.append({
                "id": "ttp_tma_platelet_contraindication",
                "tier": 1,
                "urgency": "LETHAL_CONTRAINDICATION",
                "timeframe": "< 1 hour",
                "category": "HEMATOLOGY_EMERGENCY",
                "title": "TTP/HUS Emergency: Platelet Transfusion Strictly Contraindicated",
                "title_fa": "اورژانس سندروم TTP/HUS: تزریق پلاکت اکیداً ممنوع (کنترااندیکه)",
                "action_en": "Platelet transfusion precipitates acute widespread microvascular thrombosis and organ infarction. Initiate emergent plasma exchange (PEX) and high-dose glucocorticoids immediately.",
                "action_fa": "تزریق پلاکت به دلیل تشدید ترومبوزهای میکروواسکولار و مرگ بافتی اکیداً ممنوع است؛ شروع فوری پلاسمافرز اورژانسی (PEX) و گلوکوکورتیکوئید الزامی است.",
            })

        # 1.4 Lethal Contraindication: Pheochromocytoma Beta-Blockade
        has_pheo = any(p.get("pattern_id") == "pheochromocytoma_crisis_pattern" for p in derived_patterns) or any(
            "pheochromocytoma" in str(d.get("disease_id")) and d.get("probability", 0) > 0.35
            for d in differential_diagnosis
        )
        if has_pheo:
            tier_1.append({
                "id": "pheo_crisis_contraindication",
                "tier": 1,
                "urgency": "LETHAL_CONTRAINDICATION",
                "timeframe": "< 2 hours",
                "category": "ENDOCRINE_EMERGENCY",
                "title": "Pheochromocytoma Crisis: Unopposed Beta-Blockade Contraindicated",
                "title_fa": "بحران فئوکروموسیتوم: منع مصرف بتابلوکر تنهایی بدون آلفابلوک کامل",
                "action_en": "Beta-blockade alone triggers paradoxical massive vasoconstriction and lethal hypertensive crisis. Complete alpha-blockade (phenoxybenzamine/doxazosin) is mandatory first.",
                "action_fa": "بتابلوکر بدون مهار آلفا منجر به اسپاسم عروقی شدید و بحران فشارخون کشنده می‌شود؛ ابتدا بلوک کامل گیرنده‌های آلفا الزامی است.",
            })

        # 1.5 Severe Acute Hepatocellular Necrosis (Transaminases > 500)
        if (alt_val is not None and alt_val > 500.0) or (ast_val is not None and ast_val > 500.0):
            tier_1.append({
                "id": "severe_hepatocellular_injury",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 2 hours",
                "category": "HEPATIC_EMERGENCY",
                "title": f"Severe Acute Hepatocellular Injury (ALT: {alt_val or 0:.0f}, AST: {ast_val or 0:.0f} U/L)",
                "title_fa": "آسیب حاد هپاتوسلولار شدید (ترانس‌آمینازها > 500 U/L)",
                "action_en": "Discontinue all potentially hepatotoxic medications immediately (acetaminophen, statins, specific antibiotics). Urgently evaluate coagulation profile (INR/PT) and clinical encephalopathy.",
                "action_fa": "قطع فوری کلیه داروهای هپاتوتوکسیک بالقوه (استامینوفن، استاتین‌ها) و بررسی فوری وضعیت انعقادی و هوشیاری بیمار.",
            })

        # 1.6 HLH / MAS Cytokine Storm
        has_hlh = any(p.get("pattern_id") == "hlh_mas_pattern" for p in derived_patterns) or any(
            "hemophagocytic" in str(d.get("disease_id")) and d.get("probability", 0) > 0.35
            for d in differential_diagnosis
        )
        if has_hlh:
            tier_1.append({
                "id": "hlh_mas_cytokine_storm",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 2 hours",
                "category": "IMMUNOLOGIC_CRISIS",
                "title": "HLH/MAS Cytokine Storm: Emergent Oncology/Rheumatology Protocol",
                "title_fa": "طوفان سایتوکاینی و سندروم HLH/MAS: فوریت انکولوژی و روماتولوژی",
                "action_en": "Initiate high-dose dexamethasone / etoposide protocol. Urgently monitor fibrinogen, ferritin, and soluble CD25.",
                "action_fa": "آغاز سریع پروتکل کورتیکواستروئید دوز بالا (دگزامتازون) / اتوپوزید و پایش دقیق فیبرینوژن و فریتین.",
            })

        # 1.7 True Hyperkalemia (when not suppressed by EDTA artifact)
        if k_val and k_val >= 6.0 and not suppress_hyperkalemia:
            tier_1.append({
                "id": "panic_hyperkalemia",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 1 hour",
                "category": "ELECTROLYTE_EMERGENCY",
                "title": f"True Severe Hyperkalemia (K = {k_val:.1f} mmol/L)",
                "title_fa": f"هایپرکالمی شدید و خطرناک (پتاسیم = {k_val:.1f} mmol/L)",
                "action_en": "Immediate 12-lead ECG. Administer IV calcium gluconate for myocardial membrane stabilization, insulin-glucose, and discontinue RAAS inhibitors and potassium-sparing diuretics.",
                "action_fa": "نوار قلب فوری، تزریق گلوکونات کلسیم وریدی جهت پایدارسازی میوکارد، انسولین و گلوکز، و قطع فوری مهارکننده‌های RAAS.",
            })
        elif k_val and k_val < 2.8:
            tier_1.append({
                "id": "panic_hypokalemia",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 1 hour",
                "category": "ELECTROLYTE_EMERGENCY",
                "title": f"Severe Hypokalemia (K = {k_val:.1f} mmol/L)",
                "title_fa": f"هیپوکالمی شدید و بحرانی (پتاسیم = {k_val:.1f} mmol/L)",
                "action_en": "Continuous cardiac telemetry. Slow IV potassium chloride repletion and correct concomitant hypomagnesemia.",
                "action_fa": "مانیتورینگ قلبی، جایگزینی آرام کلرید پتاسیم وریدی و بررسی و تصحیح هم‌زمان هیپومنیزیمی.",
            })

        # 1.8 Critical Thrombocytopenia
        if plt_val and plt_val < 30.0:
            tier_1.append({
                "id": "panic_thrombocytopenia",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 2 hours",
                "category": "HEMATOLOGY_EMERGENCY",
                "title": f"Critical Thrombocytopenia (Platelets = {plt_val:,.0f} /uL)",
                "title_fa": f"ترومبوسیتوپنی شدید و بحرانی (پلاکت = {plt_val:,.0f} /uL)",
                "action_en": "High risk of spontaneous life-threatening hemorrhage. Withhold all anticoagulants and antiplatelet agents. Avoid invasive procedures and intramuscular injections.",
                "action_fa": "خطر بالای خونریزی خودبه‌خودی کشنده؛ قطع فوری کلیه داروهای ضدانعقاد و ضدپلاکت و پرهیز از تزریقات عضلانی و اقدامات تهاجمی.",
            })

        # 1.9 Advanced Renal Failure (eGFR < 30)
        calc_dict_res = calculation_report.to_dict().get("results", {})
        egfr_item = calc_dict_res.get("egfr_ckd_epi_creatinine") or calc_dict_res.get("egfr_ckd_epi_2021") or calc_dict_res.get("egfr")
        raw_egfr = egfr_item.get("value") if isinstance(egfr_item, dict) else (getattr(egfr_item, "value", None) if egfr_item else None)
        egfr_val = _number(raw_egfr)
        if egfr_val is not None and egfr_val < 30.0:
            tier_1.append({
                "id": "advanced_renal_failure_tier1",
                "tier": 1,
                "urgency": "IMMEDIATE",
                "timeframe": "< 2 hours",
                "category": "RENAL_EMERGENCY",
                "title": f"Advanced Renal Failure (eGFR = {egfr_val:.1f} mL/min/1.73m2)",
                "title_fa": f"نارسایی پیشرفته کلیوی (eGFR = {egfr_val:.1f} mL/min/1.73m²)",
                "action_en": "Immediate discontinuation or strict renal dose reduction of metformin, NSAIDs, and avoidance of iodinated radiocontrast. Urgent nephrology consultation.",
                "action_fa": "قطع فوری یا بازبینی اکید دوز متفورمین، داروهای ضدالتهاب غیراستروئیدی (NSAIDs) و پرهیز از کنتراست یددار؛ مشاوره فوری نفرولوژی.",
            })

        # 1.10 Additional Critical Alerts from guideline engine
        for al in critical_alerts:
            fid = str(al.get("feature_id") or al.get("name") or "critical_alert").lower()
            val = _number(al.get("value"))
            msg = al.get("message") or al.get("title") or "Critical Alert"

            # Physiological neonatal protective filtering (0-28 days: <= 0.08 years)
            if calc_context.age_years is not None and calc_context.age_years < 0.08:
                if fid in ("hematocrit", "hct") and val is not None and val <= 65.0:
                    continue
                if fid in ("wbc", "white_blood_cell_count") and val is not None and val <= 30.0:
                    continue

            # Physiological young child alkaline phosphatase protective filtering (< 18 years)
            if calc_context.age_years is not None and calc_context.age_years < 18.0:
                if fid in ("alkaline_phosphatase", "alp") and val is not None and val <= 850.0:
                    continue

            # Physiological pregnancy hemodilution filtering
            if calc_context.pregnant:
                if fid in ("alkaline_phosphatase", "alp") and val is not None and val <= 250.0:
                    continue
                if fid in ("hemoglobin", "hb") and val is not None and val >= 10.0:
                    continue

            if not any(item["id"] in str(fid) for item in tier_1):
                tier_1.append({
                    "id": f"alert_{fid}",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 2 hours",
                    "category": "CRITICAL_ALERT",
                    "title": str(msg)[:80],
                    "title_fa": str(msg)[:80],
                    "action_en": "Immediate clinical evaluation and physician review.",
                    "action_fa": "بررسی فوری بالینی توسط پزشک معالج.",
                })

        # -------------------------------------------------------------------
        # 1.11 ACUTE LIFE-THREATENING PREDICTION MODELS (TIER 1 < 2 HOURS)
        # -------------------------------------------------------------------
        for r in risk_predictions:
            st = r.get("status")
            if st not in ("Evaluated", "Evaluated (Provisional)"):
                continue
            key = str(r.get("diseaseKey", ""))
            score = _number(r.get("score") if r.get("score") is not None else r.get("points"))
            prob = _number(r.get("probability"))
            lvl = str(r.get("riskLevel", "")).lower()
            name = r.get("modelName") or r.get("nameEn") or key

            # ACS HEART Score >= 7 or High MACE risk
            if key == "ACS_HEART" and ((score is not None and score >= 7) or lvl in ("high", "critical") or (prob and prob >= 0.50)):
                tier_1.append({
                    "id": "acute_heart_score_critical",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 1 hour",
                    "category": "CARDIOLOGY_EMERGENCY",
                    "title": f"High Acute Coronary Syndrome Risk: HEART Score = {score if score is not None else 'High'}",
                    "title_fa": f"خطر بالای سندروم حاد کرونری: امتیاز HEART = {score if score is not None else 'بالا'}",
                    "action_en": "Immediate 12-lead ECG, continuous telemetry, serial troponins at 0/1/3 hours, and emergent cardiology evaluation for invasive angiography.",
                    "action_fa": "نوار قلب فوری، مانیتورینگ قلبی، پایش سریال تروپونین و ارزیابی فوری مداخله‌ای قلب و عروق.",
                })

            # High TIMI Risk Score >= 5
            elif key == "CAD_TIMI_NSTEMI" and ((score is not None and score >= 5) or lvl in ("high", "critical")):
                tier_1.append({
                    "id": "acute_timi_score_critical",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 2 hours",
                    "category": "CARDIOLOGY_EMERGENCY",
                    "title": f"High-Risk UA/NSTEMI: TIMI Score = {score}",
                    "title_fa": f"ریسک بالای آنژین ناپایدار و NSTEMI: امتیاز TIMI = {score}",
                    "action_en": "Urgent invasive coronary strategy indicated (cardiac catheterization < 24h). Dual antiplatelet therapy and parenteral anticoagulation.",
                    "action_fa": "اندیکاسیون آنژیوگرافی و استراتژی تهاجمی فوری عروق کرونر، درمان دوگانه ضدپلاکت و ضدانعقاد وریدی.",
                })

            # High-Risk Pulmonary Embolism (sPESI >= 1 or Bova High)
            elif (key == "PE_30d_sPESI" and score is not None and score >= 1) or (key == "PE_Bova_Score" and lvl in ("high", "critical")):
                tier_1.append({
                    "id": "acute_pe_risk_critical",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 1 hour",
                    "category": "PULMONARY_EMERGENCY",
                    "title": f"High-Risk Pulmonary Embolism Alert ({name})",
                    "title_fa": f"هشدار ریسک بالای آمبولی حاد ریه ({name})",
                    "action_en": "Elevated 30-day mortality risk. Immediate echocardiography to assess right ventricular strain, CT pulmonary angiogram (CTPA), and therapeutic anticoagulation.",
                    "action_fa": "احتمال بالای ناپایداری همودینامیک و مورتالیتی؛ اکوکاردیوگرافی فوری جهت بررسی عملکرد بطن راست، سی‌تی آنژیوگرافی ریه و شروع ضدانعقاد درمانی.",
                })

            # Critical Liver Failure / High MELD >= 25 or King's College Criteria
            elif (key in ("Cirrhosis_MELD_Na", "Cirrhosis_MELD3") and score is not None and score >= 25) or (key == "Liver_Failure_Kings_College" and lvl in ("high", "critical")):
                tier_1.append({
                    "id": "critical_meld_liver_failure",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 2 hours",
                    "category": "HEPATIC_EMERGENCY",
                    "title": f"Critical End-Stage Liver Disease / Acute Liver Failure (MELD = {score if score is not None else 'High'})",
                    "title_fa": f"نارسایی حاد یا مرحله نهایی کبد با مرگ‌ومیر بالا (MELD = {score if score is not None else 'بحرانی'})",
                    "action_en": "Estimated 90-day mortality exceeds 50%. Urgent hepatology/liver transplant center contact, coagulopathy surveillance, and renal protection.",
                    "action_fa": "مرگ‌ومیر ۹۰ روزه بالای ۵۰ درصد؛ ارجاع اورژانسی به مرکز پیوند کبد، پایش انسفالوپاتی و کوآگولوپاتی و محافظت عملکرد کلیه.",
                })

            # Overt DIC (ISTH Score >= 5)
            elif key == "DIC_ISTH" and ((score is not None and score >= 5) or lvl in ("high", "critical")):
                tier_1.append({
                    "id": "isth_overt_dic_critical",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 1 hour",
                    "category": "HEMATOLOGY_EMERGENCY",
                    "title": f"Overt Disseminated Intravascular Coagulation (ISTH DIC Score = {score})",
                    "title_fa": f"انعقاد داخل عروقی منتشر حاد (ISTH DIC = {score})",
                    "action_en": "High risk of concurrent microvascular thrombosis and life-threatening bleeding. Urgent identification and treatment of underlying cause (sepsis, trauma, obstetric). Fibrinogen/cryoprecipitate repletion as clinically indicated.",
                    "action_fa": "خطر بالای ترومبوز و خونریزی همزمان؛ جستجو و درمان علت زمینه‌ای (سپسیس، تروما)، پایش فیبرینوژن و تزریق کرایوپریسیپیتات در صورت اندیکاسیون.",
                })

            # Critical Acuity / Imminent Collapse (NEWS2 >= 7, APACHE II >= 25, SAPS II >= 50)
            elif (key == "Acuity_NEWS2_Score" and score is not None and score >= 7) or (key == "ICU_APACHE_II" and score is not None and score >= 25) or (key == "ICU_SAPS_II" and score is not None and score >= 50):
                tier_1.append({
                    "id": "critical_physiological_acuity",
                    "tier": 1,
                    "urgency": "IMMEDIATE",
                    "timeframe": "< 30 minutes",
                    "category": "CRITICAL_CARE_ACUITY",
                    "title": f"Critical Physiological Deterioration ({name} = {score})",
                    "title_fa": f"افت بحرانی وضعیت فیزیولوژیک بیمار ({name} = {score})",
                    "action_en": "Imminent clinical collapse. Immediate Medical Emergency Team (MET) / Intensive Care Unit (ICU) consultation and advanced airway/hemodynamic resuscitation.",
                    "action_fa": "خطر قریب‌الوقوع ایست قلبی-تنفسی؛ فراخوانی فوری تیم واکنش سریع اورژانس (MET) یا انتقال به بخش مراقبت‌های ویژه (ICU).",
                })

        # -------------------------------------------------------------------
        # TIER 2: SUBACUTE DIAGNOSTICS & WORKUP (24-72 HOURS)
        # -------------------------------------------------------------------
        # 2.1 Pseudohyponatremia Advisory
        pseudo_rec = calc_dict.get("pseudohyponatremia_corrected_sodium")
        if pseudo_rec:
            corr_val = pseudo_rec.value if hasattr(pseudo_rec, "value") else pseudo_rec.get("value")
            tier_2.append({
                "id": "pseudohyponatremia_advisory",
                "tier": 2,
                "urgency": "SUBACUTE",
                "timeframe": "24-48 hours",
                "category": "PREANALYTICAL_ADVISORY",
                "title": "Pseudohyponatremia Advisory: Non-Aqueous Phase Displacement",
                "title_fa": "هشدار هیپوناترمی کاذب ناشی از جابه‌جایی فاز غیرآبی",
                "action_en": f"Measured sodium is artifactually decreased by hypertriglyceridemia/hyperproteinemia. True plasma water sodium is estimated at ~{corr_val} mmol/L. Direct-ISE blood gas measurement recommended; fluid restriction or hypertonic saline is contraindicated.",
                "action_fa": f"سدیم اندازه‌گیری‌شده به دلیل تری‌گلیسیرید یا پروتئین بالا کاذب است؛ سدیم حقیقی فاز آب ~{corr_val} mmol/L تخمین زده می‌شود. تجویز سرم هایپرتونیک کنترااندیکه است و اندازه‌گیری با گازهای خونی (direct-ISE) توصیه می‌شود.",
            })

        # 2.2 Pediatric eGFR Height Withheld
        ped_egfr_error = any("strictly requires measured patient height" in err for err in calculation_report.errors)
        if ped_egfr_error:
            tier_2.append({
                "id": "pediatric_egfr_height_withheld",
                "tier": 2,
                "urgency": "SUBACUTE",
                "timeframe": "24 hours",
                "category": "PEDIATRIC_MONITORING",
                "title": "Pediatric eGFR Withheld: Measured Height Required (KDIGO 2024)",
                "title_fa": "توقف محاسبه eGFR اطفال: لزوم ثبت قد بیمار (گایدلاین KDIGO 2024)",
                "action_en": "Measure patient height (cm) to calculate Bedside Schwartz eGFR. Estimation without height is withheld to avoid false-normal misclassification in pediatric CKD.",
                "action_fa": "جهت محاسبه دقیق eGFR اطفال ثبت قد بیمار به سانتی‌متر الزامی است تا از تشخیص کاذب سلامت کلیه جلوگیری شود.",
            })

        # 2.3 Top Differential Diagnoses with Gold Standard Next Tests
        GOLD_STANDARD_NEXT_TESTS = {
            # 1. Endocrine & Metabolic (20)
            "diabetes": ("Repeat fasting plasma glucose, 2h 75g OGTT, and confirmatory HbA1c panel per ADA guidelines.", "سنجش مجدد قند خون ناشتا، تست تحمل گلوکز خوراکی (OGTT دو ساعته با ۷۵ گرم گلوکز) و پنل تاییدی HbA1c طبق گایدلاین ADA."),
            "diabetic": ("Repeat fasting plasma glucose, 2h 75g OGTT, and confirmatory HbA1c panel per ADA guidelines.", "سنجش مجدد قند خون ناشتا، آزمون OGTT دو ساعته و پنل تاییدی HbA1c طبق گایدلاین ADA."),
            "prediabetes": ("Standard 75g Oral Glucose Tolerance Test (OGTT), fasting lipid profile, and structured lifestyle intervention.", "آزمون تحمل گلوکز خوراکی (OGTT)، پروفایل لیپید ناشتا و برنامه مداخله سبک زندگی."),
            "hypoglycemia": ("Whipple's triad workup: plasma glucose, serum insulin, C-peptide, beta-hydroxybutyrate, and oral hypoglycemic agent screen during spontaneous hypoglycemia.", "بررسی تریاد ویپل: قند پلاسما، انسولین سرم، C-پپتید، بتا-هیدروکسی‌بوتیرات و غربالگری داروهای خوراکی کاهنده قند در زمان افت قند."),
            "ketoacidosis": ("Arterial/venous blood gas (ABG/VBG), serum beta-hydroxybutyrate, serum osmolality, anion gap calculation, and urine ketones.", "گازهای خونی شریانی/وریدی، بتا-هیدروکسی‌بوتیرات سرم، اسمولالیته، شکاف آنیونی و کتون ادرار."),
            "hypothyroidism": ("Free T4, Free T3, and Thyroid Peroxidase Antibodies (Anti-TPO) to confirm primary autoimmune etiology.", "سنجش Free T4، Free T3 و آنتی‌بادی Anti-TPO جهت بررسی و تایید اتیولوژی خودایمنی."),
            "hyperthyroidism": ("Free T4, Free T3, TSH-receptor antibodies (TRAb/TSI), and radioactive iodine uptake (RAIU) scan.", "سنجش Free T4، Free T3، آنتی‌بادی گیرنده TSH (TRAb/TSI) و اسکن جذب ید رادیواکتیو تیروئید."),
            "graves": ("TSH-receptor antibodies (TRAb/TSI), thyroid duplex ultrasound, and ophthalmologic assessment.", "سنجش آنتی‌بادی تحریک‌کننده تیروئید (TSI/TRAb)، سونوگرافی داپلر تیروئید و ارزیابی افتالمولوژی."),
            "hashimoto": ("Thyroid Peroxidase Antibodies (Anti-TPO), Anti-Thyroglobulin (Anti-Tg), and high-resolution thyroid ultrasound.", "سنجش آنتی‌بادی‌های Anti-TPO و Anti-Tg و سونوگرافی دقیق تیروئید."),
            "thyroid": ("Free T4, Free T3, and Thyroid Peroxidase Antibodies (Anti-TPO).", "سنجش Free T4، Free T3 و آنتی‌بادی Anti-TPO."),
            "hyperparathyroidism": ("Intact PTH (iPTH), 25-OH Vitamin D, 24-hour urine calcium-to-creatinine clearance ratio (to rule out FHH), and sestamibi parathyroid scan.", "سنجش iPTH، ویتامین D، نسبت کلیرانس کلسیم به کراتینین ادرار ۲۴ ساعته (جهت رد FHH) و اسکن پاراتیروئید سستامیبی."),
            "hypercalcemia": ("Intact PTH (iPTH), PTHrP (PTH-related peptide for malignancy), 25-OH and 1,25-(OH)2 Vitamin D, and serum protein electrophoresis.", "سنجش iPTH، پروتئین مرتبط با PTH (PTHrP برای بدخیمی)، فرم‌های فعال ویتامین D و الکتروفورز پروتئین‌های سرم."),
            "hypoparathyroidism": ("Intact PTH (iPTH), serum magnesium, phosphorus, and 25-OH Vitamin D.", "سنجش هورمون iPTH، منیزیم، فسفر سرم و ۲۵-هیدروکسی ویتامین D."),
            "hypocalcemia": ("Intact PTH (iPTH), serum magnesium, ionized calcium, and 25-OH Vitamin D.", "سنجش کلسیم یونیزه، هورمون iPTH، منیزیم سرم و ویتامین D."),
            "cushing": ("Late-night salivary cortisol (x2), 24-hour urinary free cortisol (UFC), or 1mg overnight dexamethasone suppression test (ODST).", "سنجش کورتیزول بزاقی آخر شب (۲ نوبت)، کورتیزول آزاد ادرار ۲۴ ساعته (UFC) یا تست مهار دگزامتازون شبانه (ODST ۱ میلی‌گرم)."),
            "addison": ("Morning 8 AM cortisol and ACTH, followed by high-dose (250 mcg) Cosyntropin (ACTH) stimulation test.", "سنجش کورتیزول و ACTH ساعت ۸ صبح همراه با آزمون تحریک سریع با کوسینتروپین (ACTH Stimulation Test)."),
            "adrenal": ("Morning 8 AM cortisol, plasma ACTH, and 250 mcg Cosyntropin stimulation test with renin/aldosterone profiling.", "کورتیزول و ACTH ناشتا ساعت ۸ صبح، تست تحریک کوسینتروپین و ارزیابی رنین و آلدوسترون."),
            "pheochromocytoma": ("Fractionated plasma free metanephrines or 24-hour urinary fractionated metanephrines and catecholamines.", "سنجش متانفرین‌های آزاد پلاسما یا متانفرین‌ها و کاتکول‌آمین‌های تجزیه‌شده در ادرار ۲۴ ساعته."),
            "hyperaldosteronism": ("Morning plasma aldosterone concentration (PAC) to plasma renin activity (PRA) ratio (ARR > 20-30) under standardized conditions.", "نسبت غلظت آلدوسترون به فعالیت رنین پلاسما (PAC/PRA ratio) در شرایط استاندارد با قطع داروهای مخدوش‌کننده."),
            "conn": ("Plasma aldosterone to renin ratio (ARR), oral sodium loading confirmatory test, and adrenal CT imaging.", "نسبت آلدوسترون به رنین پلاسما، آزمون تاییدی بارگذاری خوراکی سدیم و سی‌تی اسکن غدد فوق کلیوی."),
            "prolactin": ("Serum prolactin (with serial dilutions to rule out hook effect), macroprolactin screening, and pituitary MRI with gadolinium.", "سنجش پرولاکتین سرم (با رقت‌های سریالی جهت رد Hook effect)، غربالگری ماکروپرولاکتین و MRI هیپوفیز با تزریق گادولینیوم."),
            "pcos": ("Total and free testosterone, DHEA-S, LH/FSH ratio, 17-OH progesterone (to rule out late-onset CAH), and pelvic ultrasound.", "تستوسترون تام و آزاد، DHEA-S، نسبت LH/FSH، ۱۷-هیدروکسی پروژسترون (جهت رد CAH دیررس) و سونوگرافی لگن."),
            "hypogonadism": ("Morning 8 AM fasting total and free testosterone (repeated on two separate days), LH, FSH, and serum prolactin.", "سنجش تستوسترون تام و آزاد ناشتا ساعت ۸ صبح (تکرار در ۲ روز مجزا)، LH، FSH و پرولاکتین سرم."),

            # 2. Hematology & Coagulation (25)
            "anemia": ("Complete blood count (CBC), reticulocyte count, peripheral blood smear, and iron/B12/folate panel.", "شمارش کامل سلول‌های خون (CBC)، شمارش رتیکولوسیت، لام خون محیطی و پنل بررسی آهن، B12 و فولات."), "iron_deficiency": ("Serum Ferritin, Transferrin Saturation (TSAT), Total Iron-Binding Capacity (TIBC), and search for occult GI blood loss.", "سنجش فریتین سرم، درصد اشباع ترانسفرین (TSAT)، ظرفیت تام اتصال به آهن (TIBC) و بررسی منشأ خونریزی مخفی گوارشی."),
            "anemia_of_chronic": ("Serum Ferritin, Soluble Transferrin Receptor (sTfR), sTfR-Ferritin index, and high-sensitivity CRP.", "سنجش فریتین سرم، گیرنده محلول ترانسفرین (sTfR)، شاخص sTfR-فریتین و پروتئین واکنشی C فوق حساس (hs-CRP)."),
            "thalassemia": ("Hemoglobin Electrophoresis (HPLC / Capillary) for HbA2 and HbF quantitation, CBC indices (Mentzer index < 13), and globin gene testing.", "الکتروفورز هموگلوبین به روش HPLC/کاپیلاری جهت سنجش HbA2 و HbF، شاخص منتزر (کمتر از ۱۳) و بررسی ژنتیکی ژن‌های گلوبین."),
            "b12": ("Serum Vitamin B12, serum Methylmalonic Acid (MMA), total Homocysteine, and Anti-Intrinsic Factor antibodies.", "سنجش ویتامین B12، متیل‌مالونیک اسید (MMA)، هوموسیستئین تام و آنتی‌بادی ضد فاکتور داخلی معده (Anti-IF)."),
            "megaloblastic": ("Serum Vitamin B12, red blood cell (RBC) folate, Methylmalonic Acid (MMA), peripheral blood smear, and reticulocyte count.", "سنجش ویتامین B12، فولات داخل گلبول قرمز (RBC Folate)، متیل‌مالونیک اسید، لام خون محیطی و شمارش رتیکولوسیت."),
            "folate": ("Red Blood Cell (RBC) folate, serum folate, homocysteine, and peripheral blood smear for hypersegmented neutrophils.", "سنجش فولات داخل اریتروسیت (RBC Folate)، فولات سرم، هوموسیستئین و بررسی نوتروفیل‌های هایپرسگمانته در لام محیطی."),
            "hemolytic": ("Reticulocyte count, Haptoglobin, indirect Bilirubin, Lactate Dehydrogenase (LDH), and Direct Antiglobulin (Coombs) Test (DAT).", "شمارش رتیکولوسیت، هاپتوگلوبین، بیلی‌روبین غیرمستقیم، آنزیم LDH و تست کومبس مستقیم (DAT)."),
            "autoimmune_hemolytic": ("Direct Antiglobulin Test (DAT/Coombs) with polyspecific and monospecific (anti-IgG, anti-C3d) reagents, and cold agglutinin titer.", "تست کومبس مستقیم (DAT) با معرف‌های منواسپسیفیک (Anti-IgG و Anti-C3d) و تیتر آگلوتینین سرد."),
            "g6pd": ("Quantitative G6PD enzyme activity assay (performed after acute hemolytic crisis resolution) and reticulocyte analysis.", "سنجش کمی فعالیت آنزیم G6PD (انجام پس از فروکش بحران حاد همولیتیک) و بررسی لام خون محیطی برای Heinz bodies."),
            "spherocytosis": ("Osmotic fragility test, Eosin-5-maleimide (EMA) binding test by flow cytometry, and acidified glycerol lysis test.", "تست اتصال ائوزین-۵-مالئیمید (EMA) با فلوسیتومتری، شکنندگی اسمزی (Osmotic Fragility) و لام خون محیطی."),
            "sickle": ("Hemoglobin electrophoresis / HPLC (quantifying HbS, HbA, HbF), sickling test, and genetic counseling.", "الکتروفورز هموگلوبین به روش HPLC (سنجش HbS و HbF)، تست داسی‌شدن و مشاوره ژنتیک."),
            "aplastic": ("Bone marrow aspiration and core biopsy with cytogenetics, paroxysmal nocturnal hemoglobinuria (PNH) clone screen, and viral serologies.", "آسپیراسیون و بیوپسی مغز استخوان با سایتوژنتیک، غربالگری کلون PNH (فلوسیتومتری FLAER) و سرولوژی‌های ویروسی."),
            "myelodysplastic": ("Bone marrow biopsy with iron staining (ring sideroblasts), cytogenetics (karyotyping/FISH for del 5q, -7), and next-generation sequencing.", "بیوپسی مغز استخوان با رنگ‌آمیزی اختصاصی آهن (سیدروبلاست‌های حلقوی)، کاریوتایپ/FISH و توالی‌یابی ژنی NGS."),
            "myeloma": ("Serum and urine protein electrophoresis with immunofixation (SPEP/UPEP), serum free light chain (sFLC) ratio, and bone marrow biopsy.", "الکتروفورز و ایمونوفیکساسیون پروتئین سرم و ادرار (SPEP/UPEP)، نسبت زنجیره‌های سبک آزاد (sFLC) و بیوپسی مغز استخوان."),
            "mgus": ("Serum protein electrophoresis (SPEP), serum free light chain ratio, CBC, creatinine, calcium, and periodic surveillance.", "الکتروفورز پروتئین سرم (SPEP)، نسبت زنجیره‌های سبک آزاد سرم، سنجش کلسیم و کراتینین و پایش دوره‌ای سالیانه."),
            "polycythemia": ("JAK2 V617F mutation testing (exon 14 and exon 12), serum erythropoietin (EPO) level, and bone marrow morphology.", "تست جهش ژن JAK2 V617F (اگزون ۱۴ و ۱۲)، سنجش سطح اریتروپویتین سرم (EPO) و بررسی هیستولوژی مغز استخوان."),
            "thrombocythemia": ("Driver mutation panel (JAK2 V617F, CALR, MPL), bone marrow core biopsy, and exclusion of reactive thrombocytosis.", "پنل جهش‌های محرک میلوپرولیفراتیو (JAK2, CALR, MPL)، بیوپسی مغز استخوان و رد قطعی ترومبوسیتوز واکنشی."),
            "myelofibrosis": ("Bone marrow biopsy showing reticulin/collagen fibrosis, JAK2/CALR/MPL mutation screen, and abdominal ultrasound for splenomegaly.", "بیوپسی مغز استخوان جهت ارزیابی فیبروز رتیکولینی/کلاژنی، جهش‌های JAK2/CALR و سونوگرافی شکم برای اسپلنومگالی."),
            "leukemia": ("Peripheral blood flow cytometry, bone marrow aspiration/biopsy, and molecular cytogenetics (FISH for BCR-ABL1, PML-RARA).", "فلوسیتومتری خون محیطی، بیوپسی مغز استخوان و آنالیز سیتوژنتیک مولکولی (FISH برای ژن‌های انکوژنیک مانند BCR-ABL1)."),
            "itp": ("Diagnosis of exclusion: complete peripheral blood smear, Helicobacter pylori testing, HIV/HCV serologies, and bone marrow biopsy if atypical.", "تشخیص رد تداخلات: لام خون محیطی، سرولوژی HIV و هپاتیت C، تست هلیکوباکتر پیلوری و بیوپسی مغز استخوان در صورت لزوم."),
            "ttp": ("Immediate plasma ADAMTS13 activity assay, peripheral blood smear for schistocytes (helmet cells > 1%), and direct Coombs test.", "سنجش فوری فعالیت آنزیم ADAMTS13، بررسی لام محیطی جهت شیستوسیت‌ها (بالای ۱٪) و انجام تست کومبس مستقیم."),
            "dic": ("ISTH DIC panel: serial PT/INR, aPTT, Fibrinogen, D-Dimer, and Platelet count every 6-8 hours with aggressive treatment of trigger.", "پنل پایش سریال انعقاد ISTH: زمان‌های PT و PTT، سطح فیبرینوژن، دی-دایمر و پلاکت هر ۶ تا ۸ ساعت همراه با درمان عامل زمینه‌ای."),
            "hemophilia": ("Specific factor VIII and factor IX coagulant activity assays, mixing studies (1:1 with normal plasma), and inhibitor screen.", "سنجش اختصاصی فاکتور ۸ و فاکتور ۹ انعقادی، آزمون اختلاط (Mixing study) و غربالگری مهارکننده‌های فاکتور."),
            "willebrand": ("von Willebrand factor (vWF) antigen, vWF ristocetin cofactor activity (vWF:RCo), and factor VIII coagulant activity.", "سنجش آنتی‌ژن فاکتور فون‌ویلبراند (vWF:Ag)، فعالیت ریستوستین کوفاکتور (vWF:RCo) و سطح فاکتور ۸ انعقادی."),
            "antiphospholipid": ("Lupus anticoagulant (dRVVT and aPTT mix), Anti-Cardiolipin IgG/IgM, and Anti-Beta2-Glycoprotein-I IgG/IgM repeated after 12 weeks.", "تست آنتی‌کواگولان لوپوسی (dRVVT)، آنتی‌بادی‌های ضد کاردیولیپین و Anti-Beta2-Glycoprotein-I با تکرار پس از ۱۲ هفته."),

            # 3. Nephrology & Fluids (16)
            "chronic_kidney": ("Spot Urine Albumin-to-Creatinine Ratio (UACR), serum cystatin C, and renal duplex ultrasound.", "نسبت آلبومین به کراتینین ادرار (UACR)، سیستاتین C سرم و سونوگرافی داپلر کلیه‌ها."),
            "ckd": ("Spot Urine Albumin-to-Creatinine Ratio (UACR), serum cystatin C, and serial eGFR monitoring.", "سنجش نسبت آلبومین به کراتینین ادرار (UACR)، سیستاتین C سرم و پایش سریال فیلتراسیون گلومرولی."),
            "nephropathy": ("Spot Urine Albumin-to-Creatinine Ratio (UACR) and renal ultrasound to evaluate cortical echogenicity.", "نسبت آلبومین به کراتینین ادرار (UACR) و سونوگرافی کلیه‌ها جهت بررسی اکوژنیسیته کورتکس."),
            "acute_kidney": ("Urinary indices (Fractional Excretion of Sodium - FeNa, FeUrea), urine microscopy for casts, and urgent renal ultrasound.", "شاخص‌های ادراری (دفع کسر کسری سدیم FeNa و اوره FeUrea)، سدیمان و میکروسکوپی ادرار و سونوگرافی اورژانسی کلیه‌ها."),
            "aki": ("Urinary indices (FeNa / FeUrea), urine sediment examination for muddy brown granular casts, and renal ultrasound.", "بررسی شاخص‌های FeNa و FeUrea، بررسی سدیمان ادرار جهت سیلندرهای گرانولار کدر (Muddy Brown) و سونوگرافی کلیه."),
            "nephrotic": ("24-hour urine protein or spot urine protein-to-creatinine ratio (UPCR > 3.5 g/g), serum albumin, lipid panel, and renal biopsy.", "پروتئین ادرار ۲۴ ساعته (بالای ۳.۵ گرم) یا نسبت UPCR، آلبومین سرم، پروفایل لیپید و بیوپسی سوزنی کلیه."),
            "glomerulonephritis": ("Urinalysis for dysmorphic RBCs and RBC casts, serum complements (C3, C4), ANA, ANCA, Anti-GBM, and renal biopsy.", "آنالیز ادرار جهت اریتروسیت‌های دیسمورفیک و سیلندر خونی، کمپلمان‌های C3 و C4، اتوآنتی‌بادی‌ها و بیوپسی کلیه."),
            "iga_nephropathy": ("Renal biopsy with immunofluorescence showing mesangial IgA deposition, spot UACR, and hearing/systemic evaluation.", "بیوپسی کلیه با ایمونوفلورسانس نشان‌دهنده رسوب مزانژیال IgA، نسبت UACR ادرار و ارزیابی سیستمیک."),
            "goodpasture": ("Circulating anti-glomerular basement membrane (Anti-GBM) antibodies by ELISA, chest CT (pulmonary hemorrhage), and urgent renal biopsy.", "سنجش آنتی‌بادی ضد غشای پایه گلومرولی (Anti-GBM) به روش الایزا، سی‌تی اسکن قفسه سینه و بیوپسی فوری کلیه."),
            "anti_gbm": ("Circulating anti-glomerular basement membrane (Anti-GBM) antibodies, chest imaging, and urgent renal biopsy.", "آنتی‌بادی Anti-GBM سرم، بررسی خونریزی ریوی و بیوپسی کلیه."),
            "anca": ("Anti-neutrophil cytoplasmic antibodies (PR3-ANCA / c-ANCA and MPO-ANCA / p-ANCA), urinalysis, and tissue biopsy.", "آنتی‌بادی‌های ضد سیتوپلاسم نوتروفیل (PR3/c-ANCA و MPO/p-ANCA)، آنالیز ادرار و بیوپسی بافت درگیر."),
            "lupus_nephritis": ("Quantitation of proteinuria (UACR/UPCR), active urine sediment microscopy, Anti-dsDNA titers, C3/C4 levels, and renal biopsy.", "سنجش کمی پروتئینوری (UACR/UPCR)، سدیمان ادرار، تیتر Anti-dsDNA، سطوح C3/C4 و انجام بیوپسی کلیه جهت گریدینگ پاتولوژی."),
            "nephrolithiasis": ("Non-contrast helical abdominal/pelvic CT scan (low-dose), urinalysis with crystal examination, and 24-hour stone risk urine profile.", "سی‌تی اسکن هلیکال بدون کنتراست شکم و لگن، بررسی کریستال‌های سدیمان ادرار و پنل متابولیک ادرار ۲۴ ساعته."),
            "kidney_stone": ("Non-contrast abdominal CT scan, stone chemical analysis, serum calcium, uric acid, PTH, and 24-hour urine metabolic screen.", "سی‌تی اسکن بدون کنتراست، آنالیز شیمیایی سنگ، کلسیم، اسید اوریک، PTH و آنالیز متابولیک ادرار ۲۴ ساعته."),
            "tubular_acidosis": ("Simultaneous blood gas, serum electrolytes (anion gap), urine anion gap (UAG = Na + K - Cl), urine pH, and urine fractional excretion of HCO3.", "گازهای خونی، الکترولیت‌های سرم، محاسبه شکاف آنیونی ادرار (UAG)، pH ادرار و کسر دفعی بی‌کربنات."),
            "rta": ("Simultaneous blood gas, serum electrolytes (anion gap), urine anion gap (UAG), and urine pH.", "گازهای خونی، الکترولیت‌ها، شکاف آنیونی ادرار و بررسی اسیدیته ادرار جهت تشخیص نوع RTA."),
            "polycystic": ("Renal ultrasound applying Ravine-Pei diagnostic criteria, genetic testing for PKD1/PKD2 mutations, and blood pressure monitoring.", "سونوگرافی کلیه‌ها بر اساس معیارهای تشخیصی Ravine-Pei، تست ژنتیک جهش ژن‌های PKD1/PKD2 و پایش دقیق فشار خون."),
            "siadh": ("Simultaneous plasma osmolality (< 275 mOsm/kg), urine osmolality (> 100 mOsm/kg), urine sodium (> 30-40 mEq/L), and exclusion of thyroid/adrenal disease.", "سنجش همزمان اسمولالیته پلاسما و ادرار، سدیم ادرار بالای ۴۰ همراه با تایید بالینی یُوولمی و رد نارسایی تیروئید و آدرنال."),
            "insipidus": ("Simultaneous plasma and urine osmolality, water deprivation test followed by desmopressin (DDAVP) response challenge, and pituitary MRI.", "تست محرومیت از آب با ارزیابی پاسخ به دسموپرسین (DDAVP) جهت افتراق نوع مرکزی از نفروژنیک و MRI هیپوفیز."),

            # 4. Hepatology & Gastroenterology (18)
            "fatty_liver": ("Abdominal ultrasound, serial FIB-4 / NAFLD fibrosis score calculation, and cardiometabolic risk stratification.", "سونوگرافی کبد و مجاری صفراوی، محاسبه شاخص فیبروز FIB-4 و طبقه‌بندی خطر بیماری‌های متابولیک."),
            "nafld": ("Abdominal ultrasound, serial FIB-4 calculation, and cardiometabolic risk stratification.", "سونوگرافی کبد، ارزیابی شاخص فیبروز FIB-4 و مداخله در فاکتورهای خطرساز متابولیک."),
            "masld": ("Liver ultrasound, FIB-4 calculation, and metabolic profiling.", "سونوگرافی کبد، ارزیابی شاخص فیبروز FIB-4 و مداخله در فاکتورهای خطرساز متابولیک."),
            "steatohepatitis": ("Vibration-controlled transient elastography (FibroScan), viral hepatitis serologies (HBsAg, Anti-HCV), and serial FIB-4 monitoring.", "الاستوگرافی کبد (فیبرواسکن)، سرولوژی هپاتیت B و C، و پایش دوره‌ای شاخص FIB-4."),
            "nash": ("Vibration-controlled transient elastography (FibroScan) and serial FIB-4 monitoring.", "الاستوگرافی کبد (فیبرواسکن) و پایش سریال شاخص‌های فیبروز."),
            "cirrhosis": ("Abdominal ultrasound with Doppler portal flow, surveillance alpha-fetoprotein (AFP), screening upper endoscopy (EGD) for varices, and MELD score.", "سونوگرافی شکم با داپلر ورید پورت، آلفافتوپروتئین (AFP) جهت غربالگری HCC، آندوسکوپی فوقانی برای واریس مری و امتیاز MELD."),
            "alcoholic": ("Maddrey's Discriminant Function (DF) score, AST/ALT ratio (> 2.0), screening for thiamine deficiency, and abdominal Doppler ultrasound.", "محاسبه امتیاز مدری (Maddrey DF)، بررسی نسبت AST/ALT بالای ۲، بررسی کمبود تیامین و سونوگرافی داپلر کبد."),
            "hepatitis_b": ("Complete HBV panel: HBsAg, Anti-HBs, HBeAg, Anti-HBe, Anti-HBc (total and IgM), and quantitative HBV-DNA PCR viral load.", "پنل کامل سرولوژی هپاتیت B: سنجش HBsAg، Anti-HBs، HBeAg، Anti-HBc و سنجش کمی بار ویروسی HBV-DNA PCR."),
            "hepatitis_c": ("HCV Antibody confirmation by quantitative HCV-RNA PCR viral load, HCV genotype determination, and hepatic fibrosis staging.", "تایید آنتی‌بادی با تست کمی HCV-RNA PCR، تعیین ژنوتیپ ویروس و استیجینگ فیبروز کبد."),
            "autoimmune_hepatitis": ("Serum IgG levels, Anti-Nuclear Antibodies (ANA), Anti-Smooth Muscle Antibodies (ASMA / Anti-Actin), Anti-LKM1, and liver biopsy.", "سنجش IgG تام سرم، آنتی‌بادی‌های ANA و ASMA (ضد عضله صاف)، Anti-LKM1 و انجام بیوپسی سوزنی کبد."),
            "biliary_cholangitis": ("Anti-Mitochondrial Antibodies (AMA / AMA-M2), elevated Alkaline Phosphatase, serum IgM, and high-resolution MRCP.", "سنجش آنتی‌بادی ضد میتوکندری (AMA-M2)، آلکالین فسفاتاز، سطح سرمی IgM و کولانژیوگرافی رزونانس مغناطیسی (MRCP)."),
            "pbc": ("Anti-Mitochondrial Antibodies (AMA / AMA-M2), serum IgM, and liver ultrasound.", "سنجش آنتی‌بادی ضد میتوکندری (AMA-M2) و سطح سرمی IgM."),
            "sclerosing_cholangitis": ("Magnetic Resonance Cholangiopancreatography (MRCP) demonstrating multifocal strictures and beading, colonoscopy (to screen for IBD), and IgG4 level.", "کولانژیوگرافی رزونانس مغناطیسی (MRCP) جهت مشاهده نمای دانه تسبیحی مجاری صفراوی، کولونوسکوپی (رد IBD) و سنجش IgG4."),
            "psc": ("High-resolution MRCP, screening colonoscopy for concurrent inflammatory bowel disease, and IgG4.", "تصویربرداری MRCP، کولونوسکوپی غربالگری بیماری التهابی روده و سنجش سطح IgG4."),
            "wilson": ("Serum ceruloplasmin, 24-hour urinary copper excretion, slit-lamp eye examination for Kayser-Fleischer (KF) rings, and liver biopsy for copper dry weight.", "سرولوپلاسمین سرم، مس ۲۴ ساعته ادرار، معاینه اسلیت لمپ چشم جهت حلقه کایزر-فلایشر (KF ring) و بیوپسی کبد."),
            "hemochromatosis": ("Fasting Transferrin Saturation (TSAT > 45%), serum Ferritin, HFE gene mutation analysis (C282Y and H63D), and liver MRI T2* for iron overload.", "درصد اشباع ترانسفرین ناشتا (TSAT)، فریتین سرم، تست ژنتیک جهش‌های ژن HFE (C282Y/H63D) و MRI اختصاصی کبد T2* جهت بار آهن."),
            "alpha_1": ("Serum Alpha-1 Antitrypsin (AAT) concentration, AAT protein phenotyping (isoelectric focusing), and SERPINA1 genotype testing.", "سنجش غلظت آلفا-۱ آنتی‌تریپسین سرم (AAT)، فنوتیپینگ پروتئین به روش فوکوسینگ ایزوالکتریک و ژنوتایپینگ SERPINA1."),
            "pancreatitis": ("Serum Lipase (diagnostic at > 3x upper reference limit), serum Amylase, abdominal ultrasound (gallstone etiology), and contrast-enhanced abdominal CT at 48-72h if severe.", "سنجش لیپاز سرم (افزایش بالای ۳ برابر رفرنس)، آمیلاز، سونوگرافی صفراوی و در صورت لزوم CT اسکن شکم با کنتراست پس از ۴۸ تا ۷۲ ساعت."),
            "chronic_pancreatitis": ("Fecal Elastase-1 test (FE-1 < 200 mcg/g indicates pancreatic exocrine insufficiency), non-contrast CT for calcifications, and secretin MRCP.", "سنجش الاستاز-۱ مدفوع (Fecal Elastase-1) جهت بررسی نارسایی برون‌ریز پانکراس، سی‌تی بدون کنتراست برای کلسیفیکاسیون و MRCP."),
            "celiac": ("IgA Anti-Tissue Transglutaminase (Anti-tTG IgA) with total serum IgA (to rule out IgA deficiency), followed by confirmatory duodenal mucosal biopsy.", "سنجش آنتی‌بادی Anti-tTG IgA به همراه سطح کل IgA سرم و در صورت مثبت بودن انجام بیوپسی آندوسکوپیک دوازدهه (مارش کریتریا)."),
            "crohn": ("Fecal Calprotectin, ileocolonoscopy with segmented mucosal biopsies, and magnetic resonance enterography (MRE) of the small bowel.", "کالپروتکتین مدفوع، ایلئوکولونوسکوپی با بیوپسی‌های قطعه‌ای و انتروگرافی رزونانس مغناطیسی (MRE) روده باریک."),
            "ulcerative_colitis": ("Fecal Calprotectin, flexible sigmoidoscopy or colonoscopy with mucosal biopsy, and infectious stool culture/Clostridioides difficile PCR.", "سنجش کالپروتکتین مدفوع، سیگموئیدوسکوپی یا کولونوسکوپی با بیوپسی و رد عفونت‌های روده و کلستریدیوم دیفیسیل."),
            "ibd": ("Fecal Calprotectin, colonoscopy with segmented mucosal biopsies, and inflammatory markers.", "سنجش کالپروتکتین مدفوع، کولونوسکوپی با بیوپسی و ارزیابی مارکرهای التهابی."),
            "cholecystitis": ("Right upper quadrant (RUQ) abdominal ultrasound evaluating gallbladder wall thickening, sonographic Murphy's sign, pericholecystic fluid, or HIDA cholescintigraphy.", "سونوگرافی ربع فوقانی راست شکم (بررسی ضخامت جدار، علامت مورفی سونوگرافیک و مایع دور کیسه صفرا) یا اسکن HIDA."),
            "cholangitis": ("Urgent biliary ultrasound / MRCP, blood cultures, liver enzymes, and emergent ERCP for biliary decompression.", "سونوگرافی و MRCP مجاری صفراوی، کشت خون، آنزیم‌های کبدی و ERCP اورژانسی جهت رفع انسداد صفرا."),

            # 5. Rheumatology & Musculoskeletal (14)
            "gout": ("Arthrocentesis with polarized light synovial fluid microscopy for negatively birefringent needle-shaped monosodium urate (MSU) crystals, and 24-hour urine uric acid.", "آرتروسنتز و بررسی مایع مفصلی زیر میکروسکوپ نور پلاریزه جهت کریستال‌های سوزنی اورات مونوسدیم (MSU) و اسید اوریک ۲۴ ساعته ادرار."),
            "hyperuricemia": ("Serum Uric Acid, 24-hour urinary uric acid excretion, serum creatinine, and dietary purine / medication review.", "سنجش اسید اوریک سرم، دفع ادراری ۲۴ ساعته اسید اوریک، کراتینین و بازبینی مصرف داروهای دیورتیک و رژیم پرپورین."),
            "pseudogout": ("Synovial fluid analysis for positively birefringent rhomboid calcium pyrophosphate (CPPD) crystals, plain joint radiographs (chondrocalcinosis), and screening for hemochromatosis / hyperparathyroidism.", "بررسی مایع مفصلی برای کریستال‌های لوزی پیروفسفات کلسیم (CPPD)، رادیوگرافی ساده جهت کندروکلسینوز و بررسی هموکروماتوز."),
            "cppd": ("Synovial fluid polarized microscopy for rhomboid calcium pyrophosphate crystals and radiographs for chondrocalcinosis.", "بررسی مایع مفصلی برای کریستال‌های لوزی پیروفسفات کلسیم (CPPD) و رادیوگرافی ساده."),
            "rheumatoid": ("Rheumatoid Factor (RF), Anti-Cyclic Citrullinated Peptide (Anti-CCP / ACPA), ESR, CRP, and bilateral hands/feet radiographs.", "سنجش فاکتور روماتوئید (RF)، آنتی‌بادی Anti-CCP، مارکرهای التهابی ESR و CRP و رادیوگرافی مفاصل دست و پا."),
            "lupus": ("Antinuclear Antibody (ANA) by indirect immunofluorescence, Anti-dsDNA, Anti-Smith (Anti-Sm), serum complements (C3/C4), and urinalysis.", "تیتر ANA به روش ایمونوفلورسانس غیرمستقیم، Anti-dsDNA، Anti-Smith، سطوح C3/C4 و آنالیز کامل ادرار جهت پروتئینوری."),
            "sle": ("ANA titer, Anti-dsDNA, Anti-Smith, C3, C4, urinalysis for proteinuria/cellular casts, and antiphospholipid antibody screening.", "تیتر ANA، آنتی‌بادی‌های اختصاصی Anti-dsDNA و Anti-Sm، کمپلمان‌ها و غربالگری سندرم آنتی‌فسفولیپید."),
            "sjogren": ("Anti-SSA (Ro) and Anti-SSB (La) antibodies, Schirmer's tear test, ocular surface staining, and minor salivary gland labial lip biopsy.", "سنجش آنتی‌بادی‌های Anti-SSA (Ro) و Anti-SSB (La)، آزمون اشک شیرمر، ارزیابی خشکی چشم و بیوپسی غدد بزاقی لب."),
            "scleroderma": ("Anti-Scl-70 (anti-topoisomerase I), Anti-Centromere Antibodies (ACA), Anti-RNA Polymerase III, nailfold capillaroscopy, and high-resolution chest CT.", "سنجش Anti-Scl-70، آنتی‌بادی ضد سانترومر (ACA)، کاپیلاروسکوپی بستر ناخن و سی‌تی اسکن ریه جهت ارزیابی فیبروز بینابینی."),
            "systemic_sclerosis": ("Anti-Scl-70, Anti-Centromere, high-resolution chest CT, and echocardiography.", "سنجش اتوآنتی‌بادی‌های Anti-Scl-70 و Anti-Centromere، سی‌تی اسکن قفسه سینه و اکوکاردیوگرافی."),
            "myositis": ("Serum Creatine Kinase (CK), Aldolase, myositis-specific autoantibodies (Anti-Jo-1), electromyography (EMG), and muscle MRI / biopsy.", "سنجش کراتین کیناز (CK)، آلدولاز، آنتی‌بادی‌های اختصاصی میوزیت (Anti-Jo-1)، نوار عصب و عضله (EMG) و بیوپسی عضله."),
            "dermatomyositis": ("Creatine kinase, Aldolase, Anti-Mi-2, Anti-MDA5, muscle MRI, and skin biopsy.", "سنجش کراتین کیناز، آلدولاز، پنل اتوآنتی‌بادی‌های میوزیت و بیوپسی پوست و عضله."),
            "ankylosing": ("HLA-B27 typing, high-sensitivity CRP, ESR, and MRI of the sacroiliac joints (STIR sequences detecting active sacroiliitis).", "تایپینگ آنتی‌ژن HLA-B27، مارکرهای التهابی CRP و ESR و تصویربرداری MRI مفاصل ساکروایلیاک جهت بررسی ساکروایلیت حاد."),
            "spondyloarthritis": ("HLA-B27 typing, pelvic/sacroiliac MRI, and inflammatory markers.", "تایپینگ HLA-B27، ام‌آر‌آی مفاصل ساکروایلیاک و ارزیابی مارکرهای التهابی."),
            "arteritis": ("Urgent ESR, high-sensitivity CRP, temporal artery color Doppler ultrasound, and unilateral/bilateral temporal artery biopsy.", "سنجش فوری ESR و CRP، سونوگرافی داپلر شریان گیجگاهی (علامت هاله Halo sign) و بیوپسی شریان تمپورال."),
            "polymyalgia": ("ESR, high-sensitivity CRP, complete CBC, screening for temporal arteritis, and trial of low-dose prednisone.", "سنجش ESR و CRP، شمارش گلبول‌های خون، بررسی آرتریت تمپورال و ارزیابی پاسخ به دوز پایین پردنیزولون."),
            "behcet": ("Pathergy test, ophthalmologic slit-lamp / fluorescein angiography examination, HLA-B51 typing, and inflammatory markers.", "تست پاتِرژی، معاینه دقیق چشم پزشکی با آنژیوگرافی فلورسئین، تایپینگ ژنتیکی HLA-B51 و مارکرهای التهابی."),
            "vasculitis": ("ANCA panel (PR3/MPO), ANA, Cryoglobulins, Hepatitis B/C serologies, complements C3/C4, and involved tissue biopsy.", "پنل کامل ANCA، کرایوگلوبولین، سرولوژی هپاتیت، کمپلمان‌ها و بیوپسی بافت درگیر."),
            "osteoporosis": ("Dual-energy X-ray Absorptiometry (DXA) bone mineral density of lumbar spine and femoral neck, 25-OH Vitamin D, calcium, and FRAX score.", "سنجش تراکم استخوان به روش DXA در مهره‌های کمری و گردن فمور، ویتامین D، کلسیم سرم و محاسبه ریسک شکستگی با FRAX."),
            "paget": ("Bone-specific Alkaline Phosphatase (bALP), plain radiographs of affected skeletal sites, and whole-body Tc-99m bone scintigraphy.", "سنجش ایزوآنزیم استخوانی آلکالین فسفاتاز (bALP)، رادیوگرافی ساده استخوان‌های درگیر و اسکن هسته‌ای کل اسکلت با تکنسیم ۹۹."),

            # 6. Cardiovascular (10)
            "coronary": ("12-lead ECG, high-sensitivity Cardiac Troponin (hs-cTn), exercise stress testing or coronary CT angiography (CCTA).", "نوار قلب ۱۲ لید، تروپونین قلبی با حساسیت بالا (hs-cTn)، تست ورزش یا سی‌تی آنژیوگرافی عروق کرونر (CCTA)."),
            "angina": ("12-lead ECG, stress echocardiography or myocardial perfusion imaging (SPECT/PET), and fasting lipid / glycemic profile.", "الکتروکاردیوگرام، اکوکاردیوگرافی استرس یا اسکن پرفیوژن میوکارد (اسپکت) و بررسی پروفایل قند و چربی."),
            "heart_failure": ("Serum B-type Natriuretic Peptide (BNP) or NT-proBNP, comprehensive transthoracic echocardiography (TTE), and chest radiograph.", "سنجش پپتید ناتریورتیک (BNP یا NT-proBNP)، اکوکاردیوگرافی داپلر ترانس‌توراسیک (TTE) و رادیوگرافی قفسه سینه."),
            "hyperlipidemia": ("Fasting full lipid profile (TC, HDL-C, LDL-C, Triglycerides), calculated Non-HDL cholesterol, and Apolipoprotein B (ApoB).", "پروفایل کامل چربی ناشتا، محاسبه کلسترول Non-HDL، آپولیپوپروتئین B (ApoB) و ارزیابی ریسک قلبی ۱۰ ساله."),
            "hypertriglyceridemia": ("Fasting serum triglycerides, ruling out secondary causes (hypothyroidism, nephrotic syndrome, alcohol), and serum lipase/amylase.", "سنجش تری‌گلیسیرید ناشتا، رد علل ثانویه (تیروئید، کلیه، مصرف الکل) و پایش آنزیم‌های پانکراس جهت پیشگیری از پانکراتیت."),
            "dvt": ("Clinical Wells DVT Score, high-sensitivity D-Dimer (rule-out in low/intermediate risk), and whole-leg venous duplex ultrasound.", "محاسبه نمره کلینیکی Wells، سنجش دی-دایمر با حساسیت بالا و سونوگرافی داپلر عروقی وریدی کامل اندام تحتانی."),
            "pulmonary_embolism": ("Wells / Geneva PE score, D-Dimer, CT Pulmonary Angiography (CTPA), and bedside echocardiography for RV strain.", "نمره احتمال بالینی ولز، دی-دایمر، سی‌تی آنژیوگرافی عروق ریوی (CTPA) و اکوکاردیوگرافی جهت بررسی فشار بطن راست."),
            "pericarditis": ("12-lead ECG (diffuse PR depression and ST elevation), high-sensitivity troponin, inflammatory markers (CRP/ESR), and echocardiography.", "نوار قلب ۱۲ لید (افت سگمان PR و صعود منتشر ST)، تروپونین قلبی، مارکرهای CRP و ESR و اکوکاردیوگرافی جهت افیوژن پریکارد."),
            "myocarditis": ("Cardiac MRI with late gadolinium enhancement (Lake Louise criteria), high-sensitivity troponin, and viral serologies.", "ام‌آر‌آی اختصاصی قلب (Cardiac MRI) با تزریق گادولینیوم، تروپونین با حساسیت بالا و اکوکاردیوگرافی."),
            "endocarditis": ("Three sets of blood cultures drawn from separate venipuncture sites prior to antimicrobials, and transesophageal echocardiography (TEE).", "حداقل ۳ نوبت کشت خون از وریدهای مجزا قبل از شروع آنتی‌بیوتیک و انجام اکوکاردیوگرافی از راه مری (TEE) برای مشاهده وژتاسیون."),
            "hypertension": ("24-hour Ambulatory Blood Pressure Monitoring (ABPM), spot urine ACR, serum creatinine, electrolytes, and screening for secondary causes.", "هولتر فشار خون ۲۴ ساعته (ABPM)، نسبت آلبومین به کراتینین ادرار، کراتینین، الکترولیت‌ها و رد علل ثانویه فشار خون."),

            # 7. Infectious Diseases & Sepsis (11)
            "sepsis": ("Two sets of blood cultures prior to antibiotic initiation, serum Lactate, Procalcitonin (PCT), CBC, and arterial blood gas.", "کشت خون ۲ گانه قبل از شروع آنتی‌بیوتیک، سنجش لاکتات سرم، پروکلسیتونین (PCT)، شمارش گلبول‌های خون و گازهای خونی."),
            "pneumonia": ("Chest radiograph / thoracic CT, sputum Gram stain and culture, urinary Streptococcus pneumoniae and Legionella pneumophila antigen tests.", "رادیوگرافی قفسه سینه، رنگ‌آمیزی گرم و کشت خلط، و سنجش آنتی‌ژن ادراری استرپتوکوک پنومونیه و لژیونلا."),
            "urinary_tract": ("Clean-catch midstream urine analysis, microscopic urine sediment examination, and quantitative urine culture with antimicrobial susceptibility.", "آنالیز ادرار میانی تمیز، بررسی سدیمان ادرار و کشت کمی ادرار همراه با آنتی‌بیوگرام (تعیین حساسیت ضدمیکروبی)."),
            "pyelonephritis": ("Urinalysis, urine culture, blood cultures, renal duplex ultrasound (to exclude obstruction/abscess), and serum creatinine.", "کشت ادرار، کشت خون، سونوگرافی کلیه جهت رد انسداد یا آبسه و ارزیابی کراتینین و الکترولیت‌ها."),
            "meningitis": ("Urgent lumbar puncture for CSF analysis (opening pressure, cell count/differential, protein, glucose ratio, Gram stain, bacterial/viral PCR).", "پونکسیون کمری اورژانسی جهت آنالیز مایع مغزی-نخاعی (CSF: فشار، شمارش سلولی، پروتئین، قند، رنگ‌آمیزی گرم و پنل مولکولی PCR)."),
            "tuberculosis": ("Interferon-Gamma Release Assay (IGRA / QuantiFERON-TB) or Tuberculin Skin Test (TST), sputum acid-fast bacilli (AFB) smear/culture, and GeneXpert PCR.", "سنجش رهایش اینترفرون گاما (IGRA/کوآنتی‌فرون) یا تست پوستی مانتو، اسمیر و کشت خلط برای باسیل اسید-فست (AFB) و GeneXpert PCR."),
            "mononucleosis": ("Heterophile antibody test (Monospot), Epstein-Barr Virus (EBV) specific serologies (VCA IgM, VCA IgG, EBNA IgG), and peripheral blood smear for atypical lymphocytes.", "تست آنتی‌بادی هتروفیل (منواسپات)، سرولوژی اختصاصی ویروس EBV (آنتی‌بادی‌های VCA IgM و EBNA) و بررسی لنفوسیت‌های آتیپیک در لام خون."),
            "ebv": ("EBV VCA-IgM, VCA-IgG, and EBNA serologies.", "سرولوژی اختصاصی ویروس اپشتین-بار (EBV VCA IgM/IgG)."),
            "cytomegalovirus": ("Quantitative CMV DNA PCR in plasma, CMV IgM and IgG serologies with avidity testing, and liver enzymes.", "سنجش کمی CMV-DNA PCR در پلاسما، آنتی‌بادی‌های CMV IgM و IgG با تست آویدیتی و پایش آنزیم‌های کبدی."),
            "cmv": ("Quantitative CMV DNA PCR in plasma and CMV IgM/IgG serology.", "سنجش کمی CMV-DNA PCR و آنتی‌بادی‌های اختصاصی."),
            "clostridium": ("Stool Clostridioides difficile toxin A/B enzyme immunoassay (EIA) combined with GDH antigen or C. difficile nucleic acid amplification test (NAAT/PCR).", "سنجش سموم A و B کلستریدیوم دیفیسیل در مدفوع به همراه آنتی‌ژن GDH یا تست تقویت اسید نوکلئیک (PCR)."),
            "brucellosis": ("Standard tube agglutination test (Wright test), 2-Mercaptoethanol (2-ME) test, Coombs-Wright test, and prolonged blood cultures (Bactec).", "تست‌های آگلوتیناسیون لوله‌ای استاندارد (تست رایت)، تست ۲-مرکاپتواتانول (2-ME)، کومبس رایت و کشت خون اختصاصی طولانی‌مدت."),
            "hiv": ("4th-generation HIV-1/2 antigen/antibody immunoassay (detecting p24 Ag and antibodies), followed by HIV-1/HIV-2 differentiation assay and viral load RNA PCR.", "تست نسل چهارم الایزا برای آنتی‌ژن p24 و آنتی‌بادی‌های HIV-1/2 و در صورت مثبت بودن تایید با تست تفکیکی و بار ویروسی HIV-RNA PCR."),

            # 8. Pulmonology, Toxicology & Critical Care (8)
            "copd": ("Post-bronchodilator spirometry (confirming FEV1/FVC < 0.70), arterial blood gas (ABG) for hypercapnia/hypoxemia, and alpha-1 antitrypsin screening.", "اسپیرومتری پس از برونکودیلاتور (تایید FEV1/FVC زیر ۰.۷۰)، گازهای خونی شریانی (ABG) جهت پایش هایپرکاپنی و هیپوکسمی و رد کمبود AAT."),
            "asthma": ("Pre- and post-bronchodilator spirometry demonstrating reversible airflow obstruction (> 12% and > 200 mL increase in FEV1), or methacholine bronchial challenge test.", "اسپیرومتری قبل و بعد از برونکودیلاتور (اثبات بازگشت‌پذیری با بهبود بیش از ۱۲٪ و ۲۰۰ میلی‌لیتر در FEV1) یا تست چالش متاکولین."),
            "sarcoidosis": ("Serum Angiotensin-Converting Enzyme (ACE), 24-hour urine calcium, high-resolution chest CT (bilateral hilar lymphadenopathy), and tissue biopsy showing non-caseating granulomas.", "سنجش آنزیم مبدل آنژیوتانسین (ACE)، کلسیم ادرار ۲۴ ساعته، سی‌تی با رزولوشن بالای قفسه سینه و بیوپسی بافت حاوی گرانولوم غیرپنیری."),
            "rhabdomyolysis": ("Serum Creatine Kinase (CK > 5x normal), serum/urine Myoglobin, electrolytes (urgent potassium, calcium, phosphate), and renal function monitoring.", "سنجش کراتین کیناز تام سرم (CK بالای ۵ برابر رفرنس)، میوگلوبین سرم و ادرار، پایش فوری پتاسیم و پیشگیری از نارسایی کلیه."),
            "acetaminophen": ("Serum Acetaminophen (Paracetamol) concentration plotted on Rumack-Matthew nomogram (at 4-24h post-ingestion), AST/ALT, and INR.", "سنجش سطح سرمی استامینوفن در نوموگرام روماک-متیو (۴ تا ۲۴ ساعت پس از مصرف)، آنزیم‌های کبد AST/ALT و زمان پروترومبین/INR."),
            "salicylate": ("Serum Salicylate concentration, arterial blood gas (mixed respiratory alkalosis and metabolic acidosis), and urinary alkalinization monitoring.", "سنجش سطح سالیسیلات پلاسما، گازهای شریانی (آلکالوز تنفسی توأم با اسیدوز متابولیک) و پایش قلیایی‌سازی ادرار."),
            "carbon_monoxide": ("Co-oximetry blood gas measuring Carboxyhemoglobin (COHb) percentage, continuous ECG monitoring, and troponin.", "کو-اکسیمتری گازهای خونی و سنجش درصد کربوکسی‌هموگلوبین (COHb)، مانیتورینگ قلبی و سنجش تروپونین."),
            "methemoglobinemia": ("Co-oximetry arterial blood gas measuring Methemoglobin (MetHb) percentage, glucose-6-phosphate dehydrogenase (G6PD) screen prior to methylene blue therapy.", "کو-اکسیمتری گازهای خونی جهت سنجش درصد متهموگلوبین (MetHb) و بررسی فاویسم/G6PD قبل از تجویز متیلن بلو.")
        }

        for d in differential_diagnosis[:6]:
            prob = d.get("probability", 0)
            did = str(d.get("disease_id", "")).lower()
            name = d.get("name") or d.get("name_en") or did
            name_fa = d.get("name_fa") or name
            if prob >= 0.20 or d.get("rank", 99) <= 2:
                next_en, next_fa = ("Follow-up confirmatory testing and clinical correlation.", "انجام تست‌های تکمیلی تشخیصی و پیگیری بالینی")
                for key, (test_en, test_fa) in sorted(GOLD_STANDARD_NEXT_TESTS.items(), key=lambda x: len(x[0]), reverse=True):
                    if key in did or key in name.lower() or key in str(d.get("name_fa", "")).lower():
                        next_en, next_fa = test_en, test_fa
                        break
                tier_2.append({
                    "id": f"diff_{did}",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "24-72 hours",
                    "category": "DIFFERENTIAL_DIAGNOSIS",
                    "title": f"Diagnostic Hypothesis: {name} (Probability: {prob*100:.1f}%)",
                    "title_fa": f"فرضیه تشخیصی: {name_fa} (احتمال: {prob*100:.1f}%)",
                    "action_en": f"Recommended Gold Standard Next Test: {next_en}",
                    "action_fa": f"تست تکمیلی استاندارد طلایی بعدی: {next_fa}",
                })

        # 2.4 Moderate Renal Impairment Drug Review (eGFR 30-59)
        if egfr_val is not None and 30.0 <= egfr_val < 60.0:
            tier_2.append({
                "id": "moderate_ckd_drug_review",
                "tier": 2,
                "urgency": "SUBACUTE",
                "timeframe": "48-72 hours",
                "category": "PHARMACOTHERAPY_REVIEW",
                "title": f"Moderate Renal Impairment (eGFR = {egfr_val:.1f} mL/min/1.73m2)",
                "title_fa": f"نقص متوسط عملکرد کلیه (eGFR = {egfr_val:.1f} mL/min/1.73m²)",
                "action_en": "Dose adjustment of renally eliminated drugs (ACEi/ARBs, gabapentin, metformin). Maintain adequate hydration and avoid NSAIDs.",
                "action_fa": "تنظیم دوز داروهای دفع‌شونده کلیوی (مهارکننده‌های RAAS، گاباپنتین، متفورمین)، هیدراتاسیون کافی و پرهیز از NSAIDs.",
            })

        # -------------------------------------------------------------------
        # 2.5 CHRONIC PREDICTIVE RISK STRATIFICATION (TIER 2: 24-72 HOURS)
        # -------------------------------------------------------------------
        for r in risk_predictions:
            st = r.get("status")
            if st not in ("Evaluated", "Evaluated (Provisional)"):
                continue
            key = str(r.get("diseaseKey", ""))
            score = _number(r.get("score") if r.get("score") is not None else r.get("points"))
            prob = _number(r.get("probability"))
            lvl = str(r.get("riskLevel", "")).lower()
            band = r.get("riskBand", "")
            name = r.get("modelName") or r.get("nameEn") or key

            # High 10-Year ASCVD Risk (PCE >= 20% or Framingham >= 20% or SCORE2 High/Very High)
            if key in ("Cardiovascular_Risk", "Framingham_General_CVD") and ((prob is not None and prob >= 0.20) or lvl in ("high", "very high", "critical")):
                prob_pct = f"{prob*100:.1f}%" if prob is not None else "High"
                tier_2.append({
                    "id": f"chronic_cvd_{key.lower()}",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "24-48 hours",
                    "category": "CARDIOVASCULAR_RISK",
                    "title": f"High 10-Year Cardiovascular Risk ({name}: {prob_pct})",
                    "title_fa": f"خطر بالای بیماری‌های قلبی-عروقی در ۱۰ سال آینده ({name}: {prob_pct})",
                    "action_en": "High-intensity statin therapy (Atorvastatin 40-80mg or Rosuvastatin 20-40mg), strict blood pressure target (< 130/80 mmHg), dietary modification, and outpatient cardiology evaluation.",
                    "action_fa": "اندیکاسیون شروع استاتین با دوز بالا، کنترل دقیق فشار خون زیر ۱۳۰/۸۰، اصلاح سبک زندگی و ویزیت سرپایی متخصص قلب و عروق.",
                })
            elif key == "SCORE2_10Y" and lvl in ("high", "very high"):
                prob_pct = f"{prob*100:.1f}%" if prob is not None else "High"
                tier_2.append({
                    "id": "chronic_cvd_score2",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "24-48 hours",
                    "category": "CARDIOVASCULAR_RISK",
                    "title": f"Elevated 10-Year CVD Mortality Risk (SCORE2: {prob_pct} [{band}])",
                    "title_fa": f"ریسک بالای مرگ‌ومیر قلبی-عروقی ۱۰ ساله (SCORE2: {prob_pct})",
                    "action_en": "Guideline-directed preventive intervention: target LDL-C < 55-70 mg/dL based on ESC 2021 guidelines.",
                    "action_fa": "مداخله پیشگیرانه بر اساس گایدلاین ESC 2021: هدف‌گذاری سطح LDL زیر ۵۵ تا ۷۰ میلی‌گرم در دسی‌لیتر.",
                })

            # Advanced Liver Fibrosis (FIB-4 >= 2.67, APRI >= 1.5, NFS > 0.675)
            elif key == "NASH" and ((score is not None and score >= 2.67) or lvl == "high"):
                tier_2.append({
                    "id": "chronic_liver_fib4_high",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "48-72 hours",
                    "category": "HEPATOLOGY_WORKUP",
                    "title": f"High Probability of Advanced Liver Fibrosis (FIB-4 = {score:.2f})",
                    "title_fa": f"احتمال بالای فیبروز پیشرفته کبدی (شاخص FIB-4 = {score:.2f})",
                    "action_en": "Positive predictive value ~80% for advanced fibrosis (F3-F4). Hepatology referral, vibration-controlled transient elastography (FibroScan), and screening for portal hypertension.",
                    "action_fa": "ارزش اخباری مثبت ۸۰٪ برای فیبروز پیشرفته؛ ارجاع به متخصص گوارش و کبد جهت الاستوگرافی (فیبرو اسکن) و پایش هیپرتانسیون پورت.",
                })
            elif key == "Liver_Fibrosis_APRI" and ((score is not None and score >= 1.5) or lvl in ("high", "very high")):
                tier_2.append({
                    "id": "chronic_liver_apri_high",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "48-72 hours",
                    "category": "HEPATOLOGY_WORKUP",
                    "title": f"Significant Liver Fibrosis / Cirrhosis Likely (APRI = {score:.2f})",
                    "title_fa": f"احتمال بالای فیبروز قابل توجه یا سیروز (شاخص APRI = {score:.2f})",
                    "action_en": "APRI > 1.5 indicates significant fibrosis/cirrhosis. Comprehensive hepatobiliary ultrasound and confirmatory elastography.",
                    "action_fa": "نشان‌دهنده احتمال بالای فیبروز شدید یا سیروز؛ انجام سونوگرافی دقیق کبد و مجاری صفراوی و الاستوگرافی تاییدی.",
                })

            # Progressive Renal Failure (KFRE >= 15%)
            elif key in ("Chronic_Kidney_Disease", "CKD_KFRE_8Var") and ((prob is not None and prob >= 0.15) or lvl in ("high", "very high", "critical")):
                prob_pct = f"{prob*100:.1f}%" if prob is not None else "High"
                tier_2.append({
                    "id": f"chronic_renal_kfre_{key.lower()}",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "48-72 hours",
                    "category": "NEPHROLOGY_WORKUP",
                    "title": f"High Risk of End-Stage Kidney Failure (Tangri KFRE: {prob_pct})",
                    "title_fa": f"خطر بالای پیشرفت به مرحله نهایی نارسایی کلیه (KFRE: {prob_pct})",
                    "action_en": "Elevated 2-to-5-year risk of ESRD requiring renal replacement therapy. Outpatient nephrology referral, strict proteinuria control with SGLT2 inhibitors and RAAS blockade.",
                    "action_fa": "ریسک بالای نارسایی کلیه نیازمند دیالیز در ۲ تا ۵ سال آینده؛ ارجاع به متخصص نفرولوژی، کنترل پروتئینوری با مهارکننده‌های SGLT2 و داروی RAAS.",
                })

            # Metabolic Syndrome & Severe Insulin Resistance
            elif key == "Metabolic_Syndrome" and lvl in ("high", "critical"):
                tier_2.append({
                    "id": "metabolic_syndrome_actionable",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "48-72 hours",
                    "category": "METABOLIC_INTERVENTION",
                    "title": "Confirmed Metabolic Syndrome (Harmonized IDF/AHA Criteria)",
                    "title_fa": "سندرم متابولیک قطعی (بر اساس معیارهای مشترک IDF/AHA)",
                    "action_en": "Synergistic 2-fold increase in CVD events and 5-fold increase in T2DM. Structured lifestyle intervention (Mediterranean diet, 150 min/wk aerobic exercise) and metabolic pharmacotherapy.",
                    "action_fa": "افزایش ۲ برابری خطر حوادث قلبی و ۵ برابری دیابت؛ رژیم غذایی مدیترانه‌ای، ورزش منظم و بررسی درمان دارویی کاهنده مقاومت انسولین.",
                })

            # High Bleeding Risk in Atrial Fibrillation (HAS-BLED >= 3)
            elif key == "AF_Bleeding_HASBLED" and ((score is not None and score >= 3) or lvl in ("high", "very high")):
                tier_2.append({
                    "id": "hasbled_high_risk",
                    "tier": 2,
                    "urgency": "SUBACUTE",
                    "timeframe": "24-48 hours",
                    "category": "ANTICOAGULATION_SAFETY",
                    "title": f"High Bleeding Risk on Anticoagulation (HAS-BLED = {score})",
                    "title_fa": f"خطر بالای خونریزی با مصرف داروی ضدانعقاد (HAS-BLED = {score})",
                    "action_en": "HAS-BLED >= 3 is NOT a reason to withhold anticoagulation; it mandates identifying and correcting reversible risk factors (uncontrolled hypertension, concomitant NSAID/aspirin use, labile INR).",
                    "action_fa": "نمره بالای ۳ دلیلی بر قطع ضدانعقاد نیست، بلکه نشان‌دهنده لزوم اصلاح فاکتورهای خطرساز قابل‌برگشت (کنترل فشارخون، قطع مصرف همزمان بروفن و NSAIDs) است.",
                })

        # -------------------------------------------------------------------
        # TIER 3: PHYSIOLOGICAL REASSURANCE & BASELINE MONITORING
        # -------------------------------------------------------------------
        # 3.1 Pediatric Growth ALP Elevation
        alp_val = _number(normalized.get("alkaline_phosphatase", {}).get("value"))
        if calc_context.age_years and calc_context.age_years < 18.0 and alp_val and alp_val > 147.0:
            if (not ast_val or ast_val <= 40.0) and (not alt_val or alt_val <= 40.0):
                tier_3.append({
                    "id": "pediatric_bone_alp_reassurance",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Physiological Bone Growth ALP Elevation ({alp_val:.0f} U/L)",
                    "title_fa": f"افزایش فیزیولوژیک آلکالین فسفاتاز استخوانی دوران رشد ({alp_val:.0f} U/L)",
                    "details_en": "Elevated alkaline phosphatase reflects osteoblastic bone formation during pediatric/adolescent growth spurts; normal liver transaminases rule out hepatobiliary disease.",
                    "details_fa": "افزایش آلکالین فسفاتاز در دوران رشد اسکلتی اطفال و بلوغ کاملاً طبیعی است و نرمال بودن آنزیم‌های کبدی هرگونه پاتولوژی کبد را رد می‌کند.",
                })

        # 3.2 Pregnancy Hemodilution
        if calc_context.pregnant:
            hb_v = _number(normalized.get("hemoglobin", {}).get("value"))
            if hb_v and 10.5 <= hb_v < 12.0:
                tier_3.append({
                    "id": "pregnancy_hemodilution_reassurance",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Physiological Pregnancy Hemodilution (Hb = {hb_v:.1f} g/dL)",
                    "title_fa": f"رقت فیزیولوژیک خون در دوران بارداری (هموگلوبین = {hb_v:.1f} g/dL)",
                    "details_en": "Mild hemoglobin reduction (>= 10.5 g/dL) is physiological in pregnancy due to disproportionate 50% plasma volume expansion over red cell mass.",
                    "details_fa": "کاهش خفیف هموگلوبین در بارداری ناشی از اتساع ۵۰ درصدی حجم پلاسما است و پاتولوژیک تلقی نمی‌شود.",
                })

        # 3.3 Normal De Ritis Ratio Reassurance
        deritis_item = calc_dict.get("ast_to_alt_ratio_de_ritis")
        if deritis_item:
            deritis_val = deritis_item.value if hasattr(deritis_item, "value") else deritis_item.get("value")
            if (not ast_val or ast_val <= 40.0) and (not alt_val or alt_val <= 40.0):
                tier_3.append({
                    "id": "deritis_normal_reassurance",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Normal Liver Enzymes & Physiological De Ritis Ratio ({deritis_val})",
                    "title_fa": f"آنزیم‌های کبدی سالم و نسبت فیزیولوژیک دِ ریتیس ({deritis_val})",
                    "details_en": "Transaminases are within normal limits; De Ritis ratio is of no pathological significance when liver enzymes are normal.",
                    "details_fa": "ترانس‌آمینازهای کبدی در محدوده طبیعی هستند و نسبت دِ ریتیس دلالت پاتولوژیک ندارد.",
                })

        # 3.4 Neonatal Physiological Leukocytosis & Polycythemia Reassurance
        if calc_context.age_years is not None and calc_context.age_years < 0.08:
            wbc_val = _number(normalized.get("wbc", {}).get("value")) or _number(normalized.get("white_blood_cell_count", {}).get("value"))
            hct_val = _number(normalized.get("hematocrit", {}).get("value")) or _number(normalized.get("hct", {}).get("value"))
            if (wbc_val and wbc_val <= 30.0) or (hct_val and hct_val <= 65.0):
                tier_3.append({
                    "id": "neonatal_hematology_reassurance",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Physiological Neonatal Hematology (WBC: {wbc_val or 'Normal'}, Hct: {hct_val or 'Normal'}%)",
                    "title_fa": "هماتولوژی فیزیولوژیک دوره نوزادی (لکوسیتوز و هماتوکریت بالای طبیعی بدو تولد)",
                    "details_en": "Elevated leukocyte count (up to 30.0 x10^3/uL) and hematocrit (up to 65%) represent benign fetal-neonatal hematopoietic transition and do not indicate sepsis or polycythemia vera.",
                    "details_fa": "لکوسیتوز نوزادی (تا ۳۰ هزار) و هماتوکریت بالا (تا ۶۵٪) تغییرات گذار فیزیولوژیک روزهای اول تولد هستند و دلالت بر سپسیس یا بیماری خونی ندارند.",
                })

        # 3.5 Geriatric Age-Adapted GFR Senescence Reassurance
        if calc_context.age_years is not None and calc_context.age_years >= 65.0:
            if egfr_val is not None and 50.0 <= egfr_val < 75.0 and (not k_val or k_val <= 5.0):
                tier_3.append({
                    "id": "geriatric_renal_senescence_reassurance",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Physiological Age-Related Renal Senescence (eGFR = {egfr_val:.1f} mL/min/1.73m2)",
                    "title_fa": f"افت فیزیولوژیک فیلتراسیون گلومرولی مرتبط با سن در سالمندان (eGFR = {egfr_val:.1f})",
                    "details_en": "Mild GFR reduction in elderly asymptomatic patients (eGFR 50-74 mL/min without proteinuria or electrolyte derangement) reflects normal nephron senescence rather than intrinsic acute renal disease.",
                    "details_fa": "کاهش ملایم GFR در افراد سالمند بدون دفع پروتئین یا اختلال الکترولیتی، ناشی از پیری طبیعی نفرون‌ها بوده و بیماری حاد کلیوی نیست.",
                })

        # 3.6 Low-Risk Predictive Model Reassurance
        for r in risk_predictions:
            st = r.get("status")
            if st not in ("Evaluated", "Evaluated (Provisional)"):
                continue
            key = str(r.get("diseaseKey", ""))
            score = _number(r.get("score") if r.get("score") is not None else r.get("points"))
            prob = _number(r.get("probability"))
            lvl = str(r.get("riskLevel", "")).lower()

            if key in ("Cardiovascular_Risk", "SCORE2_10Y") and ((prob is not None and prob < 0.05) or lvl == "low"):
                prob_pct = f"{prob*100:.1f}%" if prob is not None else "Low"
                tier_3.append({
                    "id": f"low_cvd_reassurance_{key.lower()}",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Low 10-Year Cardiovascular Risk ({r.get('modelName') or key}: {prob_pct})",
                    "title_fa": f"خطر پایین حوادث قلبی-عروقی ۱۰ ساله ({prob_pct})",
                    "details_en": "Estimated 10-year risk of ASCVD is under 5%; routine primary prevention lifestyle measures are sufficient.",
                    "details_fa": "خطر ۱۰ ساله ابتلا به سکته قلبی و مغزی زیر ۵ درصد است؛ تداوم سبک زندگی سالم و پایش دوره‌ای سالیانه کافی است.",
                })
            elif key == "NASH" and ((score is not None and score < 1.30) or lvl == "low"):
                tier_3.append({
                    "id": "low_fib4_reassurance",
                    "tier": 3,
                    "urgency": "REASSURANCE",
                    "category": "PHYSIOLOGICAL_BENIGN",
                    "title": f"Advanced Liver Fibrosis Ruled Out (FIB-4 = {score:.2f})",
                    "title_fa": f"رد فیبروز پیشرفته کبدی (شاخص FIB-4 = {score:.2f})",
                    "details_en": "FIB-4 < 1.30 has a negative predictive value > 90% for ruling out advanced fibrosis (F3-F4); reassuring hepatobiliary status.",
                    "details_fa": "شاخص FIB-4 زیر ۱.۳۰ با ارزش اخباری منفی بالای ۹۰ درصد، فیبروز پیشرفته کبدی را رد می‌کند و حاکی از سلامت کبد است.",
                })

        # 3.7 Normal Panel Reassurance (if Tier 1 and Tier 2 are empty)
        if not tier_1 and not tier_2:
            tier_3.append({
                "id": "normal_organ_panel_reassurance",
                "tier": 3,
                "urgency": "REASSURANCE",
                "category": "PHYSIOLOGICAL_BENIGN",
                "title": "Comprehensive Organ Panels Within Physiological Limits",
                "title_fa": "کلیه شاخص‌های آزمایشگاهی در محدوده فیزیولوژیک نرمال قرار دارند",
                "details_en": "Evaluated metabolic, hematologic, renal, and hepatic analytes match target physiological reference intervals for age and demographic cohort.",
                "details_fa": "کلیه شاخص‌های بیوشیمیایی و سلولی بررسی‌شده با استانداردهای مرجع سن و جنس بیمار منطبق هستند.",
            })

        return {
            "tier_1_critical": tier_1,
            "tier_2_actionable": tier_2,
            "tier_3_physiological": tier_3,
            "summary_stats": {
                "tier_1_count": len(tier_1),
                "tier_2_count": len(tier_2),
                "tier_3_count": len(tier_3),
                "primary_clinical_status": (
                    "CRITICAL_EMERGENCY" if tier_1 else
                    "ACTIONABLE_WORKUP" if tier_2 else
                    "PHYSIOLOGICAL_BASELINE"
                ),
            }
        }


    def analyze(
        self,
        confirmed_inputs: Mapping[str, Any],
        patient_context: PatientContext | Mapping[str, Any],
        *,
        include_insufficient: bool = True,
        include_negative: bool = False,
        domains: Optional[set[str]] = None,
        request_id: Optional[str] = None,
    ) -> AnalysisResult:
        # Cryptographic Hard Lockout Check (Native C++ enforced)
        try:
            import license_engine
            st = license_engine.get_current_license_status()
            if not st.get("valid"):
                raise PermissionError(
                    f"HEMOGLYPH CDSS Cryptographic Lockout: Unlicensed workstation ({st.get('machine_id')}). "
                    "Diagnostic computation halted."
                )
        except Exception as exc:
            if isinstance(exc, PermissionError):
                raise

        created_at = _utc_now()
        errors: list[str] = []


        normalized, input_warnings = self.etebarsanji_confirmed_inputs(
            confirmed_inputs)


        patient_context = self._merge_preanalytical(patient_context)
        calc_context, clinical_context, context_snapshot = (
            self._contexts(patient_context))
        context_warnings = self._etebarsanji_context(calc_context)


        cache_key = hashlib.sha256(
            _canonical_json({
                "inputs": confirmed_inputs,
                'context': context_snapshot,
            }).encode()
        ).hexdigest()
        with self._cache_lock:
            if cache_key in self._cache:
                return AnalysisResult(**self._cache[cache_key])


        calculation_report: CalculationReport = (
            self.calculator.compute(normalized, calc_context))


        interpretation_report: InterpretationReport = (
            self.interpreter.interpret(
                inputs=normalized,
                derived=calculation_report.to_dict(),
                patient=clinical_context,
                include_negative=include_negative,
                include_insufficient=include_insufficient,
                domains=domains,
            ))
        interpretation_dict = interpretation_report.to_dict()


        urgent = [
            x for x in interpretation_dict["interpretations"]
            if x['status'] == 'urgent_pattern']
        insufficient = [
            {
                "disease_id": x["disease_id"],
                "name_en": x["name_en"],
                "missing_features": x["missing_features"],
                "missing_context": x["missing_context"],
            }
            for x in interpretation_dict["interpretations"]
            if x["status"] == "insufficient_data"
        ]


        # SUPER-ENHANCED: complex cross-analyte plausibility
        complex_warnings = self._complex_plausibility_checks(normalized)

        safety_flags = self._gerdavari_safety_flags(
            normalized, calculation_report, urgent)

        # Multi-system complexity analysis
        multi_system_analysis = self._analyze_multi_system(
            normalized, calculation_report, interpretation_report, calc_context)


        critical_alerts = getattr(
            interpretation_report, "critical_alerts", [])


        status = ("urgent_review_required" if urgent
                  else "review_required"
                  if interpretation_dict["interpretations"]
                  else "completed_no_rule_match")


        audit_payload = {
            "request_id": request_id,
            "input_hash": _sha256({
                "observations": normalized,
                "context": context_snapshot,
            }),
            "feature_ids": sorted(normalized),
            'derived_feature_ids': sorted(
                calculation_report.results),
            "executed_interpretation_count": len(
                interpretation_dict["interpretations"]),
            'execution_mode': self.execution_mode,
            "strict_units": self.strict_units,
            "require_confirmed": self.require_confirmed,
            "multi_system": multi_system_analysis,
            "complex_warnings_count": len(complex_warnings),
        }
        analysis_id = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            audit_payload["input_hash"]
            + _canonical_json(self._versions())))


        warnings = _dedupe(
            input_warnings
            + context_warnings
            + complex_warnings
            + calculation_report.errors
            + [w for result in calculation_report.results.values()
               for w in result.warnings]
            + interpretation_report.warnings
            + (['URGENT PATTERN: prompt clinical assessment is '
                "required."] if urgent else [])
            + ([f"MULTI-SYSTEM: {', '.join(multi_system_analysis.get('systems_involved',[]))} involvement — complexity score {multi_system_analysis.get('complexity_score',0)}"] if multi_system_analysis.get('systems_involved') and len(multi_system_analysis.get('systems_involved'))>=2 else [])
        )


        differential_diagnosis = getattr(
            interpretation_report, "differential_diagnosis", [])
        knowledge_graph_insights = getattr(
            interpretation_report, "knowledge_graph_insights", {})
        interference_corrections = getattr(
            interpretation_report, "interference_corrections", [])

        drug_interactions = getattr(
            interpretation_report, "drug_interactions", []) or []
        expanded_kg_insights = getattr(
            interpretation_report, "expanded_kg_insights", {}) or {}
        differential_groups = getattr(
            interpretation_report, "differential_groups", {}) or {}
        contraindications = getattr(
            interpretation_report, 'contraindications', {}) or {}
        derived_patterns = getattr(
            interpretation_report, 'derived_patterns', []) or []
        executive_summary = getattr(
            interpretation_report, 'executive_summary', "") or ''
        data_completeness = getattr(
            interpretation_report, 'data_completeness', {}) or {}


        # Chronic Disease & Risk Prediction via prdicter.py
        try:
            from prdicter import predict_chronic_disease_risks
            risk_predictions = predict_chronic_disease_risks(
                inputs=normalized,
                derived=calculation_report.to_dict().get("results", {}),
                patient=context_snapshot,
                diagnoses=[x.get("disease_id") for x in interpretation_dict.get("interpretations", [])],
            )
        except Exception as exc:
            logger.warning("predict_chronic_disease_risks failed: %s", exc)
            risk_predictions = []

        audit_payload["evaluated_risk_models_count"] = len(
            [r for r in risk_predictions if r.get("status") == "Evaluated"]
        )

        # Triaged Clinical Findings (Tier 1: Emergency < 2h, Tier 2: Subacute < 24-72h, Tier 3: Reassurance)
        triaged_findings = self._triage_clinical_findings(
            normalized=normalized,
            calculation_report=calculation_report,
            interpretation_report=interpretation_report,
            calc_context=calc_context,
            critical_alerts=critical_alerts,
            differential_diagnosis=differential_diagnosis,
            derived_patterns=derived_patterns,
            risk_predictions=risk_predictions,
            contraindications=contraindications,
        )

        exec_sections: list[str] = []

        # 0. Target Population & Physiological Context
        target_pop_info = []
        if calc_context.pregnant:
            target_pop_info.append("مادر باردار (Pregnancy Cohort) — تطبیق محدوده‌های مرجع برای رقت فیزیولوژیک و آلکالین فسفاتاز جفتی طبق دستورالعمل ACOG")
        elif calc_context.age_years is not None:
            if calc_context.age_years < 0.08:
                target_pop_info.append(f"نوزاد {calc_context.age_years*365.25:.0f} روزه (Neonate) — ارزیابی طبق محدوده‌های خونی و متابولیک فیزیولوژیک نوزادی")
            elif calc_context.age_years < 1.0:
                target_pop_info.append(f"شیرخوار {calc_context.age_years*12:.0f} ماهه (Infant) — استانداردهای مرجع تکاملی شیرخواران")
            elif calc_context.age_years < 12.0:
                target_pop_info.append(f"کودک {calc_context.age_years:.0f} ساله (Pediatric) — استانداردهای رشد و فیزیولوژی اطفال (Nelson / Tietz)")
            elif calc_context.age_years < 18.0:
                target_pop_info.append(f"نوجوان {calc_context.age_years:.0f} ساله (Adolescent) — تفکیک جهش رشد بلوغ و آلکالین فسفاتاز استخوانی")
            elif calc_context.age_years >= 65.0:
                target_pop_info.append(f"سالمند {calc_context.age_years:.0f} ساله (Geriatric) — تطبیق فیزیولوژیک افت GFR سنی و آستانه‌های تشخیصی")
            else:
                target_pop_info.append(f"بزرگسال {calc_context.age_years:.0f} ساله (Adult)")

        if target_pop_info:
            target_header = "👥 بافتار فیزیولوژیک و جامعه هدف:\n• " + "\n• ".join(target_pop_info)
            exec_sections.append(target_header)

        # 1. Tier 1: Critical Emergencies & Pre-analytical Artifacts
        tier_1 = triaged_findings.get("tier_1_critical", [])
        if tier_1:
            t1_lines = []
            for item in tier_1:
                title = item.get("title_fa") or item.get("title")
                action = item.get("action_fa") or item.get("action_en")
                t1_lines.append(f"• 🚨 {title}\n  ↳ اقدام فوری (< ۲ ساعت): {action}")
            exec_sections.append("🔴 سطح ۱: اورژانس‌های حیاتی و هشدارهای فوری (< ۲ ساعت):\n" + "\n".join(t1_lines))

        # 2. Tier 2: Subacute Diagnostics & Workup
        tier_2 = triaged_findings.get("tier_2_actionable", [])
        if tier_2:
            t2_lines = []
            for item in tier_2:
                title = item.get("title_fa") or item.get("title")
                action = item.get("action_fa") or item.get("action_en")
                t2_lines.append(f"• 🟡 {title}\n  ↳ بررسی تکمیلی (۲۴ تا ۷۲ ساعت): {action}")
            exec_sections.append("🟡 سطح ۲: اقدامات تشخیصی تحت‌حاد و طبقه‌بندی خطر (۲۴ تا ۷۲ ساعت):\n" + "\n".join(t2_lines))

        # 3. Tier 3: Physiological Reassurance & Baseline
        tier_3 = triaged_findings.get("tier_3_physiological", [])
        if tier_3 or (not tier_1 and not tier_2):
            t3_lines = []
            if tier_3:
                for item in tier_3:
                    title = item.get("title_fa") or item.get("title")
                    details = item.get("details_fa") or item.get("details_en")
                    t3_lines.append(f"• 🟢 {title}: {details}")
            else:
                t3_lines.append("• 🟢 کلیه شاخص‌های بیوشیمیایی و سلولی بیمار در محدوده فیزیولوژیک طبیعی جامعه هدف مربوطه (Nelson / Tietz / CLSI) قرار دارند.")
            exec_sections.append("🟢 سطح ۳: اطمینان‌بخشی فیزیولوژیک و پایش پایه:\n" + "\n".join(t3_lines))

        # 4. Multi-System Axis Analysis
        ms_patterns = multi_system_analysis.get("multi_system_patterns", [])
        if ms_patterns:
            ms_lines = []
            for p in ms_patterns:
                title = p.get("title_fa") or p.get("pattern", "").replace("_", " ").title()
                interp = p.get("interpretation_fa") or p.get("interpretation", "")
                ms_lines.append(f"• {title}: {interp}")
            exec_sections.append("🌐 تحلیل چندارگانی و تعامل محورها (Multi-System Axis Analysis):\n" + "\n".join(ms_lines))

        # 5. Predictive Risk Stratification (Chronic Disease & Long-Term Outcomes)
        evaluated_models = [
            r for r in risk_predictions
            if r.get("status") in ("Evaluated", "Evaluated (Provisional)")
        ]
        if evaluated_models:
            high_eval = [
                r for r in evaluated_models
                if r.get("riskLevel") in ("High", "Very High", "Critical")
                or (isinstance(r.get("probability"), (int, float)) and r.get("probability") >= 0.20)
                or (isinstance(r.get("score"), (int, float)) and r.get("score") >= 20.0)
            ]
            mod_low_eval = [r for r in evaluated_models if r not in high_eval]

            r_lines = []
            seen_models = set()

            if high_eval:
                r_lines.append("🔻 مدل‌های با ریسک بالا و بسیار بالا (High & Very High Risk Stratification):")
                for r in high_eval[:8]:
                    name = r.get("modelName") or r.get("nameEn") or r.get("diseaseKey")
                    if not name or name in seen_models:
                        continue
                    seen_models.add(name)
                    level = r.get("riskLevel") or r.get("riskBand") or "High"
                    prob = r.get("probability")
                    score = r.get("score") if r.get("score") is not None else r.get("points")
                    val_str = f" ({prob*100:.1f}%)" if isinstance(prob, (int, float)) else (f" (امتیاز: {score})" if score is not None else "")
                    band = f" [{r.get('riskBand')}]" if r.get("riskBand") else ""
                    r_lines.append(f"  • {name}: سطح ریسک {level}{val_str}{band}")

            if mod_low_eval:
                r_lines.append("🔹 مدل‌های با ریسک متوسط و پایین (Moderate & Low Risk Profiles):")
                for r in mod_low_eval[:6]:
                    name = r.get("modelName") or r.get("nameEn") or r.get("diseaseKey")
                    if not name or name in seen_models:
                        continue
                    seen_models.add(name)
                    level = r.get("riskLevel") or r.get("riskBand") or "Low"
                    prob = r.get("probability")
                    score = r.get("score") if r.get("score") is not None else r.get("points")
                    val_str = f" ({prob*100:.1f}%)" if isinstance(prob, (int, float)) else (f" (امتیاز: {score})" if score is not None else "")
                    r_lines.append(f"  • {name}: سطح ریسک {level}{val_str}")

            if r_lines:
                exec_sections.append("📈 ارزیابی و طبقه‌بندی خطر بیماری‌های مزمن (Predictive Risk Stratification):\n" + "\n".join(r_lines))

        # Build English Executive Summary (Strictly English CDS output)
        exec_sections_en: list[str] = []
        if calc_context.pregnant:
            exec_sections_en.append("👥 Physiological Context & Target Cohort:\n• Pregnant Mother (ACOG reference intervals adjusted for hemodilution and placental alkaline phosphatase).")
        elif calc_context.age_years is not None:
            exec_sections_en.append(f"👥 Physiological Context & Target Cohort:\n• Patient Age: {calc_context.age_years:.1f} y (Evaluated against age-specific pediatric/geriatric benchmarks).")

        if tier_1:
            t1_en = []
            for item in tier_1:
                t = item.get("title") or item.get("title_en") or item.get("title_fa")
                act = item.get("action_en") or item.get("action") or item.get("action_fa")
                t1_en.append(f"• 🚨 {t}\n  ↳ Urgent Action (< 2h): {act}")
            exec_sections_en.append("🔴 Tier 1: Critical Emergencies & Pre-analytical Artifacts (< 2h):\n" + "\n".join(t1_en))

        if tier_2:
            t2_en = []
            for item in tier_2:
                t = item.get("title") or item.get("title_en") or item.get("title_fa")
                act = item.get("action_en") or item.get("action") or item.get("action_fa")
                t2_en.append(f"• 🟡 {t}\n  ↳ Subacute Workup (24-72h): {act}")
            exec_sections_en.append("🟡 Tier 2: Subacute Diagnostics & Actionable Findings (24-72h):\n" + "\n".join(t2_en))

        if tier_3 or (not tier_1 and not tier_2):
            t3_en = []
            if tier_3:
                for item in tier_3:
                    t = item.get("title") or item.get("title_en") or item.get("title_fa")
                    det = item.get("details_en") or item.get("details") or item.get("details_fa")
                    t3_en.append(f"• 🟢 {t}: {det}")
            else:
                t3_en.append("• 🟢 All biochemical and cellular indices are within normal physiological bounds (Nelson / Tietz / CLSI).")
            exec_sections_en.append("🟢 Tier 3: Physiological Reassurance & Baseline Monitoring:\n" + "\n".join(t3_en))

        if ms_patterns:
            ms_en = []
            for p in ms_patterns:
                t = p.get("pattern", "").replace("_", " ").title()
                interp = p.get("interpretation") or p.get("interpretation_fa") or ""
                ms_en.append(f"• {t}: {interp}")
            exec_sections_en.append("🌐 Multi-System Axis Analysis:\n" + "\n".join(ms_en))

        if evaluated_models:
            r_en = []
            if high_eval:
                r_en.append("🔻 High & Very High Risk Stratification:")
                for r in high_eval[:8]:
                    name = r.get("modelName") or r.get("nameEn") or r.get("diseaseKey")
                    level = r.get("riskLevel") or r.get("riskBand") or "High"
                    prob = r.get("probability")
                    val_str = f" ({prob*100:.1f}%)" if isinstance(prob, (int, float)) else ""
                    r_en.append(f"  • {name}: Risk Level {level}{val_str}")
            if mod_low_eval:
                r_en.append("🔹 Moderate & Low Risk Profiles:")
                for r in mod_low_eval[:6]:
                    name = r.get("modelName") or r.get("nameEn") or r.get("diseaseKey")
                    level = r.get("riskLevel") or r.get("riskBand") or "Low"
                    prob = r.get("probability")
                    val_str = f" ({prob*100:.1f}%)" if isinstance(prob, (int, float)) else ""
                    r_en.append(f"  • {name}: Risk Level {level}{val_str}")
            if r_en:
                exec_sections_en.append("📈 Chronic Disease Risk Stratification:\n" + "\n".join(r_en))

        executive_summary = "\n\n".join(exec_sections_en) if exec_sections_en else "\n\n".join(exec_sections)

        result = AnalysisResult(
            analysis_id=analysis_id,
            status=status,
            created_at=created_at,
            schema_version=SCHEMA_VERSION,
            versions=self._versions(),
            context=_json_safe(context_snapshot),
            observations=normalized,
            derived=calculation_report.to_dict(),
            interpretations=interpretation_dict,
            urgent_findings=urgent,
            safety_flags=safety_flags,
            insufficient_rules=insufficient,
            warnings=warnings,
            errors=errors,
            audit=audit_payload | {
                "output_hash": _sha256({
                    "derived": calculation_report.to_dict(),
                    "interpretations": interpretation_dict,
                    "multi_system": multi_system_analysis,
                }),
            },
            multi_system_analysis=multi_system_analysis,
            complex_warnings=complex_warnings,

            critical_alerts=critical_alerts,
            differential_diagnosis=differential_diagnosis,
            knowledge_graph_insights=knowledge_graph_insights,
            interference_corrections=interference_corrections,
            drug_interactions=drug_interactions,
            expanded_kg_insights=expanded_kg_insights,
            differential_groups=differential_groups,
            contraindications=contraindications,
            derived_patterns=derived_patterns,
            executive_summary=executive_summary,
            data_completeness=data_completeness,
            risk_predictions=risk_predictions,
            triaged_findings=triaged_findings,
        )


        with self._cache_lock:
            self._cache[cache_key] = result.to_dict()
            if len(self._cache) > 50:
                self._cache.pop(next(iter(self._cache)))

        return result


    def _gerdavari_safety_flags(
        self,
        observations: Mapping[str, Mapping[str, Any]],
        calculations: CalculationReport,
        urgent_interpretations: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        flags: list[dict[str, Any]] = []
        for feature_id, record in observations.items():
            feature = self.feature_registry.get(feature_id)
            critical = (
                feature.get("validation") or {}).get('critical') or {}
            number = _number(record.get("value"))
            low = _number(critical.get("low"))
            high = _number(critical.get("high"))
            if (number is not None and low is not None
                    and number <= low):
                flags.append({
                    "type": "critical_low",
                    "feature_id": feature_id,
                    "value": number,
                    "unit": record.get("unit"),
                    "threshold": low,
                    "severity": "critical",
                })
            if (number is not None and high is not None
                    and number >= high):
                flags.append({
                    "type": "critical_high",
                    "feature_id": feature_id,
                    "value": number,
                    "unit": record.get('unit'),
                    "threshold": high,
                    "severity": "critical",
                })
            flag = str(record.get("flag", "")).upper()
            if flag in {'CRITICAL', "HH", "LL", 'CRIT'}:
                flags.append({
                    "type": 'reported_critical_flag',
                    "feature_id": feature_id,
                    "value": record.get("value"),
                    'unit': record.get("unit"),
                    "severity": "critical",
                })
            if flag in {"B", "BORDERLINE"}:
                flags.append({
                    "type": "reported_borderline_flag",
                    "feature_id": feature_id,
                    'value': record.get("value"),
                    "unit": record.get("unit"),
                    "severity": "warning",
                })
        for item in urgent_interpretations:
            flags.append({
                "type": "urgent_rule_pattern",
                "disease_id": item["disease_id"],
                "rule_id": item["rule_id"],
                "status": item["status"],
                "severity": "urgent",
            })
        # SUPER-ENHANCED: complex multi-analyte safety flags
        def gv(fid):
            r = observations.get(fid)
            return _number(r.get("value")) if r else None
        glu = gv("glucose") or gv("fasting_plasma_glucose")
        hco3 = gv("bicarbonate") or gv("carbon_dioxide")
        if glu and glu>=250 and hco3 and hco3<18:
            flags.append({"type": "dka_risk", "feature_id": "glucose+bicarbonate", "value": glu, "message": f"DKA risk: Glucose {glu:.0f} + HCO3 {hco3:.0f} low", "severity": "critical"})
        k = gv("potassium")
        if k and k>5.5:
            flags.append({"type": "hyperkalemia", "feature_id": "potassium", "value": k, "message": f"Hyperkalemia K={k:.1f} — urgent ECG and treatment", "severity": "critical"})
        na = gv("sodium")
        if na and na<120:
            flags.append({"type": "severe_hyponatremia", "feature_id": "sodium", "value": na, "message": f"Severe hyponatremia Na={na:.0f} — seizure risk", "severity": "critical"})
        hb = gv("hemoglobin")
        wbc = gv("white_blood_cell_count")
        plt = gv("platelet_count")
        if hb and hb<8 and wbc and wbc<2 and plt and plt<50:
            flags.append({"type": "severe_pancytopenia", "feature_id": "cbc", "message": f"Severe pancytopenia: Hb {hb:.1f}, WBC {wbc:.1f}, PLT {plt:.0f}", "severity": "critical"})
        cl = gv("chloride")
        if na and cl and hco3:
            ag = na - (cl + hco3)
            alb = gv("albumin")
            if alb and alb<4.0:
                ag += 2.5*(4.0-alb)
            if ag>20:
                flags.append({"type": "high_anion_gap_critical", "feature_id": "anion_gap", "value": ag, "message": f"Critical high anion gap {ag:.0f} — consider toxic ingestion, lactic acidosis, DKA", "severity": "critical"})
        for fid, rec in calculations.results.items():
            if hasattr(rec, 'value'):
                v = _number(rec.value)
                if v is None:
                    continue
                if fid=="corrected_calcium" and v>13:
                    flags.append({"type": "hypercalcemia_crisis", "feature_id": fid, "value": v, "message": f"Hypercalcemia crisis corrected Ca {v:.1f}", "severity": "critical"})
                if fid=="osmolar_gap" and v>20:
                    flags.append({"type": "toxic_alcohol", "feature_id": fid, "value": v, "message": f"High osmolar gap {v:.0f} — toxic alcohol ingestion", "severity": "critical"})
        return flags


    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()
        logger.info("Analysis service cache cleared.")


    @staticmethod
    def dumps(result: AnalysisResult, *, indent: int = 2) -> str:
        data = result.to_dict()
        if HAS_ORJSON:
            if indent > 0:
                return orjson.dumps(
                    data,
                    option=orjson.OPT_INDENT_2
                    | orjson.OPT_SORT_KEYS,
                ).decode()
            return orjson.dumps(
                data, option=orjson.OPT_SORT_KEYS).decode()
        return json.dumps(
            data, ensure_ascii=False, indent=indent, sort_keys=True)

    @staticmethod
    def save(result: AnalysisResult, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(
            destination.suffix + ".tmp")
        temporary.write_text(
            AnalysisService.dumps(result), encoding='utf-8')
        temporary.replace(destination)
        return destination


def interpret_lab_data(
    inputs: Mapping[str, Any],
    derived: Optional[Mapping[str, Any]],
    patient: Mapping[str, Any] | Any,
    *,
    detailed: bool = False,
    include_insufficient: bool = False,
    execution_mode: str = "research",
    engine: Optional[ClinicalRuleEngine] = None,
    domains: Optional[set[str]] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    from analyse_gidlines import (
        ClinicalRuleEngine as _Engine,
        POSITIVE_RESULT_STATES,
        TruthValue,
        _STATUS_PRIORITY,
    )
    eng = engine or _Engine(execution_mode=execution_mode)
    report = eng.interpret(
        inputs, derived, patient, include_negative=False,
        include_insufficient=include_insufficient, domains=domains)
    if detailed:
        return report.to_dict()
    positive_states = POSITIVE_RESULT_STATES
    output = []
    for item in report.interpretations:
        if item.status not in positive_states:
            continue
        output.append({
            "diseaseKey": item.disease_id,
            'nameEn': item.name_en,
            'nameFa': item.name_fa,
            "icd10": list(item.icd10 or []),
            "snomedCt": list(item.snomed_ct or []),
            "status": ("Present" if item.status == "criterion_met"
                       else "Possible" if item.status == "possible_pattern"
                       else "Compatible"),
            "interpretationStatus": item.status,
            "statusLabel": item.status.replace("_", ' ').title(),
            'evidence': [x["message"] for x in item.evidence
                         if x.get("truth") == TruthValue.TRUE],
            'guideline': ", ".join(item.source_ids),
            'sourceIds': item.source_ids,
            "domains": item.domains,
            'statement': item.statement,
            "importance": ("High" if item.urgency == "urgent"
                           else 'Moderate'),
            'recommendation': (
                "Urgent medical assessment" if item.urgency == "urgent"
                else "Physician review and confirmatory evaluation"),
            "confirmRequired": True,
            "diagnosisAllowed": item.diagnosis_allowed,
            "requiresPhysicianReview": item.requires_physician_review,
            "ruleId": item.rule_id,
            "limitations": item.limitations,

            "bayesianPosterior": item.bayesian_posterior,
            "fuzzyScore": item.fuzzy_score,
            "ensembleScore": item.ensemble_score,
            'differentialRank': item.differential_rank,
            "criticalAlert": item.critical_alert,
            'sensitivityAnalysis': item.sensitivity_analysis,
            "actionableRecommendations": item.actionable_recommendations,
        })
    output.sort(key=lambda d: (
        _STATUS_PRIORITY.get(d["interpretationStatus"], 99),
        (d.get("nameEn") or "").casefold()))
    return output


def build_enhanced_analysis_result(
    base_result: AnalysisResult,
    interpretation_report: Any,
) -> AnalysisResult:

    if hasattr(interpretation_report, "critical_alerts"):
        base_result.critical_alerts = list(
            interpretation_report.critical_alerts or [])
    if hasattr(interpretation_report, "differential_diagnosis"):
        base_result.differential_diagnosis = list(
            interpretation_report.differential_diagnosis or [])
    if hasattr(interpretation_report, "knowledge_graph_insights"):
        base_result.knowledge_graph_insights = dict(
            interpretation_report.knowledge_graph_insights or {})
    if hasattr(interpretation_report, "interference_corrections"):
        base_result.interference_corrections = list(
            interpretation_report.interference_corrections or [])
    for _fname in ("drug_interactions", "derived_patterns"):
        if hasattr(interpretation_report, _fname):
            setattr(base_result, _fname,
                    list(getattr(interpretation_report, _fname) or []))
    for _fname in ("expanded_kg_insights", "differential_groups",
                   "contraindications", "data_completeness"):
        if hasattr(interpretation_report, _fname):
            setattr(base_result, _fname,
                    dict(getattr(interpretation_report, _fname) or {}))
    if hasattr(interpretation_report, 'executive_summary'):
        base_result.executive_summary = (
            interpretation_report.executive_summary or "")
    return base_result


__all__ = [
    "AnalysisResult",
    "AnalysisService",
    "AnalysisServiceError",
    "ConfirmedObservation",
    "InputValidationError",
    "OCRReviewSession",
    "ReviewItem",
    "ReviewValidationError",
    "SCHEMA_VERSION",
    "SERVICE_VERSION",
    'interpret_lab_data',
    'build_enhanced_analysis_result',
]


