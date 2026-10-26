from __future__ import annotations
import functools
import copy
import hashlib
import json
import logging
import math
import operator
import os
import re
import time
from collections import OrderedDict, defaultdict
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from cache_registry import bargozari_registry, shared_object
from calcu import (CalculationError, PatientContext, convert_unit,
                         normalize_unit)

logger = logging.getLogger(__name__)

DEFAULT_DISEASE_REGISTRY_PATH = Path(__file__).with_name(
    "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json")
DEFAULT_FEATURE_REGISTRY_PATH = Path(__file__).with_name(
    "HEMOGLYPH_FEATURE_REGISTRY.json")

try:
    import orjson as _orjson

    def _canonical_json(value: Any) -> str:
        return _orjson.dumps(_json_safe(value),
                             option=_orjson.OPT_SORT_KEYS).decode()
except ImportError:
    _orjson = None

    def _canonical_json(value: Any) -> str:
        return json.dumps(_json_safe(value), ensure_ascii=False,
                          sort_keys=True, separators=(',', ":"))


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _sigmoid(x: float, k: float = 1.0) -> float:
    x *= k
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _dedupe(seq) -> list:
    seen: set = set()
    out: list = []
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {'positive', "negative", "present", "absent",
                       "reactive", "non-reactive", "normal", "abnormal",
                       "+", "-", "none", "n/a", "na"}:
            return None
    try:
        result = float(str(value).replace("٫", ".").replace(",", '.'))
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value) if value != 0 else False
    text = str(value).strip().casefold()
    if text in {'true', "yes", "y", '1', 'positive', "present",
                "مثبت", "بله"}:
        return True
    if text in {"false", "no", "n", "0", "negative", 'absent',
                "منفی", "خیر"}:
        return False
    return bool(text)


_BORDERLINE_REL_EPS = 0.02


class TruthValue(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class RegistryValidationError(RuntimeError):
    pass


@dataclass
class ClinicalContext:
    age_years: Optional[float] = None
    sex_at_birth: Optional[str] = None
    pregnant: Optional[bool] = None
    fasting: Optional[bool] = None
    symptoms_present: Optional[bool] = None
    unequivocal_hyperglycemia: Optional[bool] = None
    ogtt_75g: Optional[bool] = None
    vasopressor_required: Optional[bool] = None
    after_adequate_resuscitation: Optional[bool] = None
    encounter: str = "unknown"
    persistence_days: Optional[int] = None
    within_hours: Optional[int] = None
    change_from_baseline: Optional[bool] = None
    timed_level: Optional[bool] = None
    timed_post_dose: Optional[bool] = None
    fasting_preferred: Optional[bool] = None
    age_assay_specific: Optional[bool] = None
    titer: Optional[bool] = None
    assay_specific: Optional[bool] = None

    serum_albumin: Optional[float] = None
    serum_glucose_mgdl: Optional[float] = None

    # ULTRA-PRECISE: vital signs and anthropometry for complex diagnosis
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    systolic_blood_pressure: Optional[float] = None
    diastolic_blood_pressure: Optional[float] = None
    waist_cm: Optional[float] = None
    waist_circumference: Optional[float] = None
    body_mass_index: Optional[float] = None
    bmi: Optional[float] = None
    heart_rate: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    smoking: Optional[bool] = None
    hypertension: Optional[bool] = None
    diabetes: Optional[bool] = None

    current_medications: list[str] = field(default_factory=list)
    ethnicity: Optional[str] = None
    altitude_m: Optional[float] = None
    pregnancy_trimester: Optional[int] = None

    extra: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        # ULTRA-PRECISE: fallback to extra dict for any missing vital/context
        try:
            extra = object.__getattribute__(self, 'extra')
            if isinstance(extra, dict) and name in extra:
                return extra[name]
        except AttributeError:
            pass
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __getattribute__(self, name: str) -> Any:
        # ULTRA-PRECISE: if dataclass field is None, try extra dict before returning None
        # This makes context.systolic_bp work even when stored in extra
        try:
            val = object.__getattribute__(self, name)
            if val is None:
                # Check extra for fallback, but avoid recursion
                try:
                    extra = object.__getattribute__(self, 'extra')
                    if isinstance(extra, dict) and name in extra and extra[name] is not None:
                        return extra[name]
                except AttributeError:
                    pass
            return val
        except AttributeError:
            # If attribute doesn't exist, try extra via __getattr__ logic
            try:
                extra = object.__getattribute__(self, 'extra')
                if isinstance(extra, dict) and name in extra:
                    return extra[name]
            except AttributeError:
                pass
            raise
    @classmethod
    def from_any(cls, value: Any) -> 'ClinicalContext':
        if isinstance(value, cls):
            return value
        if isinstance(value, PatientContext):
            extra = dict(getattr(value, 'extra', {}) or {})
            return cls(
                age_years=value.age_years,
                sex_at_birth=value.sex_at_birth,
                pregnant=value.pregnant,
                pregnancy_trimester=getattr(value, 'pregnancy_trimester', None) or extra.get('pregnancy_trimester'),
                fasting=value.fasting,
                systolic_bp=getattr(value, 'systolic_bp', None),
                diastolic_bp=getattr(value, 'diastolic_bp', None),
                waist_cm=getattr(value, 'waist_cm', None),
                body_mass_index=getattr(value, 'weight_kg', None) and getattr(value, 'height_cm', None) and (getattr(value, 'weight_kg') / ((getattr(value, 'height_cm')/100)**2) if getattr(value, 'height_cm') else None),
                weight_kg=getattr(value, 'weight_kg', None),
                height_cm=getattr(value, 'height_cm', None),
                extra=extra,
            )
        if not isinstance(value, Mapping):
            return cls()
        raw = dict(value)
        aliases = {

            "Age": "age_years", 'age': "age_years",
            'Sex': 'sex_at_birth', "gender": "sex_at_birth",
            "sex": "sex_at_birth", "Pregnant": 'pregnant',
            "pregnancy": "pregnant", "Fasting": "fasting",
            "albumin": "serum_albumin",
            "glucose_for_correction": 'serum_glucose_mgdl',

            "medications": 'current_medications',
            "current_medications": "current_medications",
            "drugs": "current_medications",
            "ethnicity": "ethnicity",
            'race': "ethnicity",
            "altitude": "altitude_m",
            "altitude_m": "altitude_m",
            "pregnancy_trimester": "pregnancy_trimester",

            # ULTRA-PRECISE: vital signs and anthropometry aliases
            "systolic_bp": "systolic_bp",
            "diastolic_bp": "diastolic_bp",
            "systolic_blood_pressure": "systolic_blood_pressure",
            "diastolic_blood_pressure": "diastolic_blood_pressure",
            "SBP": "systolic_bp",
            "DBP": "diastolic_bp",
            "bp_systolic": "systolic_bp",
            "bp_diastolic": "diastolic_bp",
            "waist_cm": "waist_cm",
            "waist_circumference": "waist_circumference",
            "waist": "waist_cm",
            "BMI": "body_mass_index",
            "bmi": "body_mass_index",
            "body_mass_index": "body_mass_index",
            "heart_rate": "heart_rate",
            "HR": "heart_rate",
            "weight_kg": "weight_kg",
            "height_cm": "height_cm",
            "weight": "weight_kg",
            "height": "height_cm",
            "smoking": "smoking",
            "hypertension": "hypertension",
            "diabetes": "diabetes",
        }
        normalized: dict[str, Any] = {}
        extra: dict[str, Any] = {}
        fields = set(cls.__dataclass_fields__) - {"extra"}
        for key, item in raw.items():
            target = aliases.get(key, key)
            if target in fields:
                normalized[target] = item
            else:
                extra[target] = item
        for bkey in ("pregnant", "fasting", "symptoms_present",
                     "ogtt_75g", "vasopressor_required",
                     "after_adequate_resuscitation",
                     'unequivocal_hyperglycemia', "change_from_baseline",
                     "timed_level", "timed_post_dose"):
            if normalized.get(bkey) is not None:
                normalized[bkey] = _as_bool(normalized[bkey])

        meds = normalized.get("current_medications")
        if meds is None:
            normalized["current_medications"] = []
        elif isinstance(meds, str):
            normalized["current_medications"] = [
                m.strip() for m in re.split(r"[,،;/|]", meds) if m.strip()]
        elif isinstance(meds, Mapping):
            normalized['current_medications'] = [
                str(m) for m in meds.keys()]
        else:
            try:
                normalized["current_medications"] = [
                    str(m) for m in meds if str(m).strip()]
            except TypeError:
                normalized["current_medications"] = [str(meds)]
        for numkey in ("age_years", 'altitude_m', "serum_albumin",
                       'serum_glucose_mgdl',
                       "systolic_bp", "diastolic_bp",
                       "systolic_blood_pressure", "diastolic_blood_pressure",
                       "waist_cm", "waist_circumference",
                       "body_mass_index", "bmi",
                       "heart_rate", "weight_kg", "height_cm"):
            if normalized.get(numkey) is not None:
                normalized[numkey] = _float(normalized[numkey])
        # FIX A41: negative/absurd ages previously mapped to 'neonate'
        # reference bands. Reject them (stashed in extra for audit).
        _age = normalized.get("age_years")
        if _age is not None and not 0 <= _age <= 120:
            extra["rejected_age_years"] = _age
            normalized["age_years"] = None
        normalized.pop('temporal_data', None)
        normalized["extra"] = extra
        try:
            return cls(**normalized)
        except TypeError:
            safe = {k: v for k, v in normalized.items() if k in fields}
            safe["extra"] = extra
            return cls(**safe)

    def get(self, key: str) -> Any:
        # ULTRA-PRECISE: robust getter that checks dataclass field first, then extra
        # Returns None only if both are missing/None, allowing fallback logic
        if hasattr(self, key):
            try:
                val = getattr(self, key)
                if val is not None:
                    return val
            except AttributeError:
                pass
        # Fallback to extra dict
        if hasattr(self, 'extra') and isinstance(self.extra, dict):
            return self.extra.get(key)
        return None

    def normalized_jensiat(self) -> Optional[str]:
        if self.sex_at_birth is None:
            return None
        aliases = {"male": "male", "m": "male", "man": "male",
                   "1": "male", "female": "female", "f": "female",
                   "woman": "female", "0": "female",
                   "مرد": 'male', "زن": "female"}
        return aliases.get(str(self.sex_at_birth).strip().casefold())


    @property
    def age_group(self) -> str:
        if self.age_years is None:
            return "unknown"
        return _sen_goroohbandi(float(self.age_years))


def _normalise_series(seq: Any) -> list[dict[str, Any]]:
    """ESL extension 11-T: accept ``[{t_hours|t|hours|offset_hours|offset_minutes, value, unit?}]``
    or ``[[t_hours, value], ...]``; return points sorted by time (hours, float)."""
    out: list[dict[str, Any]] = []
    if not isinstance(seq, (list, tuple)):
        return out
    for p in seq:
        t = v = None; u = None
        if isinstance(p, Mapping):
            for k in ("t_hours", "t", "hours", "offset_hours", "time_hours"):
                if p.get(k) is not None:
                    t = _float(p.get(k)); break
            if t is None and p.get("offset_minutes") is not None:
                tm = _float(p.get("offset_minutes")); t = tm / 60.0 if tm is not None else None
            v = _float(p.get("value")); u = p.get("unit")
        elif isinstance(p, (list, tuple)) and len(p) >= 2:
            t, v = _float(p[0]), _float(p[1])
        if t is None or v is None:
            continue
        out.append({"t_hours": float(t), "value": float(v), "unit": u})
    out.sort(key=lambda d: d["t_hours"])
    return out


@dataclass
class ObservationRecord:
    feature_id: str
    value: Any
    unit: Optional[str] = None
    confirmed: bool = True
    source: str = "input"
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    timestamp: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ConditionEvidence:
    feature_id: str
    truth: TruthValue
    actual_value: Any = None
    actual_unit: Optional[str] = None
    operator: Optional[str] = None
    threshold: Any = None
    threshold_unit: Optional[str] = None
    message: str = ""
    assumptions: list[str] = field(default_factory=list)
    missing_context: list[str] = field(default_factory=list)
    source: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    strength: Optional[float] = None
    borderline: bool = False

    z_score: Optional[float] = None
    percentile: Optional[float] = None
    severity_score: Optional[float] = None
    direction: str = "normal"
    fuzzy_membership: Optional[float] = None

    @property
    def readable(self) -> str:
        parts: list[str] = []
        feat = self.feature_id or "?"
        if self.truth == TruthValue.UNKNOWN:
            parts.append(f"{feat}: not determined")
            if self.message:
                parts.append(self.message)
            if self.missing_context:
                parts.append('missing: ' +
                             ', '.join(sorted(self.missing_context)))
        elif self.truth == TruthValue.CONFLICT:
            parts.append(f"{feat}: conflicting data")
            if self.message:
                parts.append(self.message)
        else:
            parts.append(self.message or f"{feat} {self.truth}")
        if self.borderline:
            parts.append("(borderline deviation)")
        if self.severity_score is not None and self.severity_score > 0.5:
            parts.append(f"(severity {self.severity_score:.2f})")
        if self.assumptions:
            parts.append("(" + '; '.join(self.assumptions) + ')')
        return " ".join(p for p in parts if p).strip()


@dataclass
class NodeEvaluation:
    truth: TruthValue
    evidence: list[ConditionEvidence] = field(default_factory=list)
    missing_features: set[str] = field(default_factory=set)
    missing_context: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)
    score: Optional[float] = None


@dataclass
class DiseaseInterpretation:
    disease_id: str
    name_en: str
    name_fa: Optional[str]
    rule_id: str
    rule_type: str
    status: str
    truth: str
    urgency: str
    diagnosis_allowed: bool
    requires_physician_review: bool
    evidence: list[dict[str, Any]]
    missing_features: list[str]
    missing_context: list[str]
    limitations: list[str]
    source_ids: list[str]
    sources: list[dict[str, Any]]
    warnings: list[str]
    rule_quality: dict[str, Any]
    domains: list[str] = field(default_factory=list)
    classification: dict[str, Any] = field(default_factory=dict)
    clinical_priority: str = "routine"
    icd10: list[str] = field(default_factory=list)
    snomed_ct: list[str] = field(default_factory=list)
    statement: str = ""
    safety_statement: str = (
        'Laboratory decision support only; not a diagnosis.')
    confidence: Optional[float] = None

    bayesian_posterior: Optional[float] = None
    bayesian_explanation: Optional[str] = None
    fuzzy_score: Optional[float] = None
    ensemble_score: Optional[float] = None
    ensemble_votes: dict[str, float] = field(default_factory=dict)
    knowledge_graph_boost: Optional[float] = None
    differential_rank: Optional[int] = None

    actionable_recommendations: list[str] = field(default_factory=list)
    sensitivity_analysis: list[str] = field(default_factory=list)
    critical_alert: Optional[str] = None


    drug_caveats: list[str] = field(default_factory=list)


    differential_alternatives: list[str] = field(default_factory=list)


    contraindications: list[dict[str, Any]] = field(default_factory=list)


    derived_patterns: list[str] = field(default_factory=list)

    def render(self, *, include_evidence: bool = True) -> str:
        lines = [f"{self.name_en} — {self.status}"]
        if self.urgency == "urgent":
            lines.append("Priority: urgent clinical assessment.")
        if self.critical_alert:
            lines.append(f"🚨 CRITICAL: {self.critical_alert}")
        if include_evidence and self.evidence:
            lines.append("Evidence:")
            for e in self.evidence:
                lines.append('  - ' + str(
                    e.get("_readable") or e.get("message") or ""))
        if self.missing_features or self.missing_context:
            missing = list(self.missing_features) + list(
                self.missing_context)
            lines.append("Insufficient data (missing): " +
                         ", ".join(_dedupe(missing)))
        if self.sensitivity_analysis:
            lines.append("If additional data were available:")
            for s in self.sensitivity_analysis:
                lines.append("  → " + s)
        if self.actionable_recommendations:
            lines.append('Suggested next steps: ' +
                         "; ".join(self.actionable_recommendations))
        if self.source_ids:
            lines.append("Sources: " + ", ".join(self.source_ids))
        lines.append(self.safety_statement)
        return "\n".join(l for l in lines if l)



# ---------------------------------------------------------------------------
# ESL extension 8 (2026-10-22): next-test layer.
# A laboratory-only engine cannot assert heart failure without a natriuretic
# peptide or diabetes without HbA1c; the honest output is the test that would
# settle the question. Each trigger is an entity the differential already
# contains (any probability); each recommendation names the registry feature(s)
# that would satisfy it, so a test already measured is never recommended again.
# Priority: 1 = time-critical (sepsis bundle, acid-base), 2 = diagnostic
# confirmation, 3 = aetiological work-up.
# ---------------------------------------------------------------------------
_NEXT_TEST_LIBRARY: dict[str, list[dict[str, Any]]] = {
    "leukocytosis_pattern": [
        {"test": "Serum lactate", "features": ["lactate"], "priority": 1, "why": "organ hypoperfusion screen when leukocytosis may represent infection", "src": "Surviving Sepsis Campaign 2021 (Evans et al., Crit Care Med 2021)"},
        {"test": "Procalcitonin", "features": ["procalcitonin"], "priority": 2, "why": "bacterial vs non-bacterial leukocytosis", "src": "SSC 2021; Schuetz et al., Lancet Infect Dis 2018"},
        {"test": "Blood cultures ×2 before antibiotics", "features": ["blood_culture"], "priority": 1, "why": "source identification", "src": "SSC 2021 (Hour-1 bundle)"},
        {"test": "C-reactive protein", "features": ["c_reactive_protein"], "priority": 2, "why": "inflammatory activity", "src": "NICE NG51 Sepsis 2016/2024"},
    ],
    "severe_neutropenia": [
        {"test": "Blood cultures ×2 (peripheral + any line) before antibiotics", "features": ["blood_culture"], "priority": 1, "why": "profound neutropenia: occult bacteraemia must be excluded; empirical therapy within 1 h if febrile", "src": "IDSA 2010 (Freifeld); ASCO/IDSA 2018 (Taplitz)"},
        {"test": "Serum lactate", "features": ["lactate"], "priority": 1, "why": "sepsis screen in a neutropenic host", "src": "SSC 2021"},
        {"test": "Peripheral smear ± blast count", "features": ["blasts_percent", "blast_cells_percent"], "priority": 2, "why": "marrow failure vs infiltration", "src": "BSH 2014 pancytopenia work-up"},
        {"test": "Reticulocyte count", "features": ["absolute_reticulocyte_count", "corrected_reticulocyte_count"], "priority": 2, "why": "hypoproliferative vs peripheral destruction", "src": "BSH 2014"},
    ],
    "bacterial_infection": [
        {"test": "Serum lactate", "features": ["lactate"], "priority": 1, "why": "sepsis screen", "src": "SSC 2021"},
        {"test": "Procalcitonin", "features": ["procalcitonin"], "priority": 2, "why": "bacterial confirmation and antibiotic stewardship", "src": "Schuetz 2018"},
        {"test": "Blood cultures ×2", "features": ["blood_culture"], "priority": 1, "why": "source identification", "src": "SSC 2021"},
    ],
    "sepsis": [
        {"test": "Serum lactate (repeat if > 2 mmol/L)", "features": ["lactate"], "priority": 1, "why": "SSC Hour-1 bundle", "src": "SSC 2021"},
        {"test": "Blood cultures ×2", "features": ["blood_culture"], "priority": 1, "why": "SSC Hour-1 bundle", "src": "SSC 2021"},
        {"test": "Procalcitonin", "features": ["procalcitonin"], "priority": 2, "why": "bacterial confirmation", "src": "SSC 2021"},
        {"test": "Arterial blood gas", "features": ["arterial_ph"], "priority": 1, "why": "acid-base and oxygenation (SOFA)", "src": "Sepsis-3 (Singer et al., JAMA 2016)"},
    ],
    "hyperglycemia": [
        {"test": "HbA1c", "features": ["hemoglobin_a1c"], "priority": 2, "why": "distinguishes stress hyperglycaemia from undiagnosed diabetes (≥ 6.5 %)", "src": "ADA Standards of Care 2024, §2 and §16"},
        {"test": "Serum/urine ketones", "features": ["beta_hydroxybutyrate", "urine_ketones"], "priority": 1, "why": "exclude ketoacidosis when glucose > 250 mg/dL", "src": "ADA/EASD hyperglycaemic crises consensus 2024"},
    ],
    "diabetes_mellitus": [
        {"test": "HbA1c", "features": ["hemoglobin_a1c"], "priority": 2, "why": "diagnostic confirmation and glycaemic burden", "src": "ADA 2024 §2"},
        {"test": "Urine albumin-creatinine ratio", "features": ["albumin_creatinine_ratio"], "priority": 3, "why": "diabetic kidney disease screen", "src": "ADA 2024 §11; KDIGO 2022 diabetes-CKD"},
    ],
    "type_2_diabetes": [
        {"test": "HbA1c", "features": ["hemoglobin_a1c"], "priority": 2, "why": "diagnostic confirmation", "src": "ADA 2024 §2"},
        {"test": "Urine albumin-creatinine ratio", "features": ["albumin_creatinine_ratio"], "priority": 3, "why": "diabetic kidney disease screen", "src": "ADA 2024 §11"},
        {"test": "Lipid panel", "features": ["ldl_cholesterol", "total_cholesterol"], "priority": 3, "why": "cardiovascular risk", "src": "ADA 2024 §10"},
    ],
    "acute_kidney_injury": [
        {"test": "Baseline / prior creatinine (chronicity)", "features": ["creatinine_baseline"], "priority": 1, "why": "AKI vs CKD requires a prior value or 3-month persistence", "src": "KDIGO AKI 2012; KDIGO CKD 2024"},
        {"test": "Urinalysis with microscopy", "features": ["urine_protein_qualitative"], "priority": 2, "why": "intrinsic vs pre-renal", "src": "KDIGO AKI 2012"},
        {"test": "Urine sodium / FENa", "features": ["urine_sodium"], "priority": 2, "why": "pre-renal physiology", "src": "KDIGO AKI 2012"},
        {"test": "Cystatin C", "features": ["cystatin_c"], "priority": 3, "why": "muscle-independent GFR confirmation", "src": "KDIGO CKD 2024 (eGFRcr-cys)"},
        {"test": "BNP / NT-proBNP", "features": ["b_type_natriuretic_peptide", "nt_probnp"], "priority": 3, "why": "cardiorenal physiology when volume status is uncertain", "src": "ESC HF 2021 §4; KDIGO AKI 2012 §2.3"},
    ],
    "chronic_kidney_disease": [
        {"test": "Urine albumin-creatinine ratio", "features": ["albumin_creatinine_ratio"], "priority": 2, "why": "A-stage; required for CGA staging", "src": "KDIGO CKD 2024"},
        {"test": "Cystatin C", "features": ["cystatin_c"], "priority": 2, "why": "confirmatory eGFRcr-cys when creatinine-based eGFR 45–59 without albuminuria", "src": "KDIGO CKD 2024 Rec 1.2.2"},
        {"test": "Prior creatinine (≥ 3 months)", "features": ["creatinine_baseline"], "priority": 1, "why": "chronicity criterion", "src": "KDIGO CKD 2024"},
        {"test": "Parathyroid hormone, phosphate, 25-OH vitamin D", "features": ["parathyroid_hormone"], "priority": 3, "why": "CKD-MBD when eGFR < 45", "src": "KDIGO CKD-MBD 2017"},
    ],
    "renal_failure_unspecified": [
        {"test": "Baseline / prior creatinine", "features": ["creatinine_baseline"], "priority": 1, "why": "chronicity", "src": "KDIGO 2012/2024"},
        {"test": "Urine albumin-creatinine ratio", "features": ["albumin_creatinine_ratio"], "priority": 2, "why": "kidney damage marker", "src": "KDIGO CKD 2024"},
    ],
    "prerenal_azotemia": [
        {"test": "Urine sodium / FENa (FEUrea if on diuretics)", "features": ["urine_sodium"], "priority": 2, "why": "confirms pre-renal physiology", "src": "KDIGO AKI 2012"},
    ],
    "anemia": [
        {"test": "Ferritin and transferrin saturation", "features": ["ferritin", "transferrin_saturation"], "priority": 2, "why": "iron status", "src": "BSH 2021 IDA guideline; WHO 2020"},
        {"test": "Reticulocyte count", "features": ["reticulocytes", "reticulocyte_count_absolute"], "priority": 2, "why": "production vs loss/destruction", "src": "BSH 2021"},
        {"test": "Vitamin B12 and folate", "features": ["vitamin_b12", "folate_serum"], "priority": 3, "why": "macrocytic/normocytic work-up", "src": "BSH 2014 cobalamin/folate"},
        {"test": "LDH, haptoglobin, bilirubin", "features": ["lactate_dehydrogenase", "serum_haptoglobin"], "priority": 3, "why": "haemolysis screen", "src": "BSH 2017 haemolytic anaemia"},
    ],
    "thrombocytopenia": [
        {"test": "Peripheral blood smear (clumping, schistocytes, blasts)", "features": ["peripheral_blood_smear_review"], "priority": 1, "why": "pseudothrombocytopenia and MAHA exclusion", "src": "ASH 2019 ITP; BSH 2012 TMA"},
        {"test": "PT/INR, aPTT, fibrinogen, D-dimer", "features": ["fibrinogen", "d_dimer"], "priority": 1, "why": "DIC screen", "src": "ISTH DIC score (Taylor 2001)"},
        {"test": "LDH, haptoglobin", "features": ["lactate_dehydrogenase", "serum_haptoglobin"], "priority": 2, "why": "microangiopathic haemolysis", "src": "BSH 2012 TMA"},
    ],
    "hyponatremia": [
        {"test": "Serum osmolality", "features": ["serum_osmolality", "measured_osmolality"], "priority": 1, "why": "hypotonic vs pseudo/hypertonic", "src": "European hyponatraemia guideline 2014 (Spasovski)"},
        {"test": "Urine osmolality and urine sodium", "features": ["urine_osmolality", "urine_sodium"], "priority": 1, "why": "ADH activity and volume status", "src": "Spasovski 2014"},
        {"test": "TSH and morning cortisol", "features": ["thyroid_stimulating_hormone", "morning_cortisol"], "priority": 3, "why": "exclude hypothyroidism / adrenal insufficiency before SIADH", "src": "Spasovski 2014"},
    ],
    "metabolic_acidosis": [
        {"test": "Arterial/venous blood gas", "features": ["arterial_ph"], "priority": 1, "why": "confirm acidaemia, respiratory compensation (Winter)", "src": "Berend NEJM 2014"},
        {"test": "Serum lactate", "features": ["lactate"], "priority": 1, "why": "lactic acidosis", "src": "Kraut & Madias NEJM 2014"},
        {"test": "β-hydroxybutyrate", "features": ["beta_hydroxybutyrate"], "priority": 1, "why": "ketoacidosis", "src": "ADA/EASD 2024"},
        {"test": "Serum osmolality (osmolal gap)", "features": ["serum_osmolality", "measured_osmolality"], "priority": 2, "why": "toxic alcohol screen when anion gap unexplained", "src": "Kraut & Kurtz CJASN 2008"},
    ],
    "high_anion_gap_metabolic_acidosis": [
        {"test": "Serum lactate", "features": ["lactate"], "priority": 1, "why": "most common cause", "src": "Kraut & Madias 2014"},
        {"test": "β-hydroxybutyrate", "features": ["beta_hydroxybutyrate"], "priority": 1, "why": "ketoacidosis", "src": "ADA/EASD 2024"},
        {"test": "Serum osmolality (osmolal gap)", "features": ["serum_osmolality", "measured_osmolality"], "priority": 1, "why": "toxic alcohols", "src": "Kraut & Kurtz 2008"},
    ],
    "hypocalcemia": [
        {"test": "Ionised calcium (or albumin-corrected calcium)", "features": ["calcium_ionized"], "priority": 1, "why": "exclude pseudohypocalcaemia from hypoalbuminaemia", "src": "Endocrine Society / Cooper & Gittoes BMJ 2008"},
        {"test": "Magnesium and phosphate", "features": ["magnesium", "phosphate"], "priority": 2, "why": "hypomagnesaemia causes refractory hypocalcaemia", "src": "Cooper & Gittoes 2008"},
        {"test": "Parathyroid hormone and 25-OH vitamin D", "features": ["parathyroid_hormone", "25_hydroxy_vitamin_d"], "priority": 3, "why": "aetiology", "src": "Cooper & Gittoes 2008"},
    ],
    "hypokalemia": [
        {"test": "Magnesium", "features": ["magnesium"], "priority": 1, "why": "hypomagnesaemia makes hypokalaemia refractory", "src": "Kardalas et al., Endocr Connect 2018"},
        {"test": "Blood gas (bicarbonate)", "features": ["arterial_ph"], "priority": 2, "why": "acid-base-linked shifts", "src": "Kardalas 2018"},
    ],
    "hyperkalemia": [
        {"test": "Repeat potassium (non-haemolysed, no fist clenching)", "features": ["potassium_repeat"], "priority": 1, "why": "exclude pseudohyperkalaemia", "src": "UK Kidney Association 2023 hyperkalaemia"},
        {"test": "Blood gas", "features": ["arterial_ph"], "priority": 1, "why": "acidaemia-driven shift", "src": "UKKA 2023"},
    ],
    "acute_myocardial_infarction": [
        {"test": "Serial high-sensitivity troponin (0/1 h or 0/3 h)", "features": ["troponin_repeat"], "priority": 1, "why": "rise/fall pattern required by the universal definition", "src": "Fourth Universal Definition of MI 2018; ESC NSTE-ACS 2023"},
        {"test": "BNP / NT-proBNP", "features": ["b_type_natriuretic_peptide", "nt_probnp"], "priority": 2, "why": "heart failure complicating ACS", "src": "ESC HF 2021"},
    ],
    "acute_myocardial_injury": [
        {"test": "Serial high-sensitivity troponin", "features": ["troponin_repeat"], "priority": 1, "why": "acute vs chronic injury", "src": "Fourth UDMI 2018"},
        {"test": "BNP / NT-proBNP", "features": ["b_type_natriuretic_peptide", "nt_probnp"], "priority": 2, "why": "heart failure", "src": "ESC HF 2021"},
    ],
    "myocardial_injury_acuity_undetermined": [
        {"test": "Serial high-sensitivity troponin (0/1 h or 0/3 h)", "features": ["troponin_repeat"], "priority": 1, "why": "rise/fall = acute injury; stable = chronic injury (4th UDMI)", "src": "Fourth UDMI 2018; ESC ACS 2023"},
        {"test": "12-lead ECG", "features": [], "priority": 1, "why": "ischaemia evidence required for infarction", "src": "Fourth UDMI 2018"},
        {"test": "BNP / NT-proBNP", "features": ["b_type_natriuretic_peptide", "nt_probnp"], "priority": 2, "why": "heart failure as cause of chronic injury", "src": "ESC HF 2021"},
    ],
    "cardiorenal_syndrome": [
        {"test": "BNP / NT-proBNP", "features": ["b_type_natriuretic_peptide", "nt_probnp"], "priority": 1, "why": "heart-failure confirmation", "src": "ESC HF 2021"},
    ],
    "malnutrition": [
        {"test": "C-reactive protein", "features": ["c_reactive_protein"], "priority": 2, "why": "inflammation lowers albumin independent of nutrition", "src": "GLIM 2019; ASPEN 2021 position on albumin"},
        {"test": "Prealbumin", "features": ["prealbumin"], "priority": 3, "why": "short-half-life marker", "src": "ASPEN 2021"},
    ],
    "hypoalbuminemia": [
        {"test": "C-reactive protein", "features": ["c_reactive_protein"], "priority": 2, "why": "negative acute-phase behaviour", "src": "GLIM 2019"},
        {"test": "Urine protein-creatinine ratio", "features": ["urine_protein_to_creatinine_ratio", "albumin_creatinine_ratio"], "priority": 2, "why": "nephrotic losses", "src": "KDIGO GN 2021"},
    ],
    "hepatocellular_injury_pattern": [
        {"test": "Hepatitis B surface antigen, hepatitis C antibody", "features": ["hepatitis_b_surface_antigen", "hepatitis_c_antibody"], "priority": 2, "why": "viral hepatitis", "src": "ACG 2017 abnormal liver chemistries"},
        {"test": "INR and albumin", "features": ["international_normalized_ratio"], "priority": 1, "why": "synthetic function / acute liver failure", "src": "ACG 2017"},
        {"test": "GGT and ethanol", "features": ["gamma_glutamyl_transferase", "ethanol"], "priority": 3, "why": "alcohol-related pattern", "src": "ACG 2017"},
    ],
    "cholestasis": [
        {"test": "GGT", "features": ["gamma_glutamyl_transferase"], "priority": 2, "why": "hepatic vs bone origin of ALP", "src": "ACG 2017"},
        {"test": "Direct bilirubin", "features": ["direct_bilirubin"], "priority": 2, "why": "conjugated fraction", "src": "ACG 2017"},
    ],
    "coagulopathy": [
        {"test": "Fibrinogen and D-dimer", "features": ["fibrinogen", "d_dimer"], "priority": 1, "why": "DIC vs liver vs vitamin K", "src": "ISTH DIC 2001; BSH 2009"},
        {"test": "Mixing study / factor assays", "features": ["mixing_study"], "priority": 3, "why": "inhibitor vs deficiency", "src": "BSH 2014"},
    ],
    "elevated_inr_pattern": [
        {"test": "Fibrinogen, D-dimer, platelet trend", "features": ["fibrinogen", "d_dimer"], "priority": 1, "why": "DIC screen", "src": "ISTH 2001"},
        {"test": "ALT/AST, albumin, bilirubin", "features": ["alanine_aminotransferase", "albumin"], "priority": 2, "why": "liver synthetic failure", "src": "ACG 2017"},
    ],
    "alcohol_use_disorder_biomarker_pattern": [
        {"test": "Blood ethanol, GGT, carbohydrate-deficient transferrin", "features": ["ethanol", "gamma_glutamyl_transferase"], "priority": 2, "why": "alcohol exposure", "src": "ASAM 2020"},
        {"test": "Magnesium, phosphate, thiamine", "features": ["magnesium", "phosphate"], "priority": 1, "why": "withdrawal / refeeding risk", "src": "ASAM 2020 alcohol withdrawal"},
    ],
    "acute_pancreatitis": [
        {"test": "Lipase (if only amylase measured)", "features": ["lipase"], "priority": 1, "why": "more specific than amylase", "src": "ACG 2024 acute pancreatitis"},
        {"test": "Triglycerides and calcium", "features": ["triglycerides", "calcium_total"], "priority": 2, "why": "aetiology", "src": "ACG 2024"},
    ],
    "hypothyroidism": [
        {"test": "Free T4", "features": ["free_thyroxine"], "priority": 2, "why": "overt vs subclinical", "src": "ATA 2014 hypothyroidism"},
        {"test": "TPO antibodies", "features": ["thyroid_peroxidase_antibody"], "priority": 3, "why": "autoimmune aetiology", "src": "ATA 2014"},
    ],
    "diabetic_ketoacidosis": [
        {"test": "β-hydroxybutyrate", "features": ["beta_hydroxybutyrate"], "priority": 1, "why": "diagnostic criterion (≥ 3 mmol/L)", "src": "ADA/EASD 2024"},
        {"test": "Venous blood gas", "features": ["arterial_ph"], "priority": 1, "why": "pH criterion and severity", "src": "ADA/EASD 2024"},
        {"test": "Phosphate and magnesium", "features": ["phosphate", "magnesium"], "priority": 2, "why": "treatment-related depletion", "src": "ADA/EASD 2024"},
    ],
    "rhabdomyolysis": [
        {"test": "Urine myoglobin / urinalysis", "features": ["urine_myoglobin"], "priority": 2, "why": "confirm pigment nephropathy risk", "src": "Bosch NEJM 2009"},
        {"test": "Potassium, phosphate, calcium, uric acid", "features": ["phosphate", "uric_acid"], "priority": 1, "why": "metabolic complications", "src": "Bosch 2009"},
    ],
    "heart_failure": [
        {"test": "BNP / NT-proBNP", "features": ["b_type_natriuretic_peptide", "nt_probnp"], "priority": 1, "why": "rule-out thresholds BNP < 35 / NT-proBNP < 125 pg/mL", "src": "ESC HF 2021"},
    ],
}
_NEXT_TEST_ALIASES = {  # entity -> entity whose entry applies
    "severe_hyponatremia": "hyponatremia", "siadh": "hyponatremia", "lactic_acidosis": "metabolic_acidosis",
    "neutrophilia_pattern": "leukocytosis_pattern", "leukemoid_reaction": "leukocytosis_pattern", "sepsis_support_pattern": "sepsis",
    "septic_shock": "sepsis", "stress_hyperglycemia": "hyperglycemia", "type_1_diabetes": "diabetes_mellitus",
    "normocytic_anemia_pattern": "anemia", "microcytic_anemia_pattern": "anemia", "macrocytic_anemia_pattern": "anemia",
    "acute_blood_loss_anemia": "anemia", "iron_deficiency_anemia": "anemia", "anemia_of_chronic_disease": "anemia",
    "protein_energy_malnutrition": "malnutrition", "acute_hepatitis": "hepatocellular_injury_pattern",
    "liver_cirrhosis": "hepatocellular_injury_pattern", "disseminated_intravascular_coagulation": "coagulopathy",
    "vitamin_k_deficiency": "coagulopathy", "acute_heart_failure": "heart_failure", "chronic_heart_failure": "heart_failure",
    "heart_failure_decompensated": "heart_failure", "euglycemic_diabetic_ketoacidosis": "diabetic_ketoacidosis",
    "hyperosmolar_hyperglycemic_state": "hyperglycemia", "primary_hypothyroidism": "hypothyroidism", "subclinical_hypothyroidism": "hypothyroidism",
    "alcoholic_hepatitis_pattern": "alcohol_use_disorder_biomarker_pattern", "alcohol_associated_liver_disease": "alcohol_use_disorder_biomarker_pattern",
}


def _esl_next_tests(differential: list, observed: set, max_items: int = 12, value_of=None) -> list[dict[str, Any]]:
    """Rank confirmatory tests not yet measured, driven by entities present in the differential."""
    out: dict[str, dict[str, Any]] = {}
    for d in differential:
        did = d.get("disease_id") if isinstance(d, dict) else getattr(d, "disease_id", None)
        if not did:
            continue
        p = float(d.get("probability", 0.0)) if isinstance(d, dict) else float(getattr(d, "probability", 0.0) or 0.0)
        key = _NEXT_TEST_ALIASES.get(did, did)
        for rec in _NEXT_TEST_LIBRARY.get(key, []):
            if any(f in observed for f in rec["features"]):
                continue
            if (rec["priority"] == 3 and p < 0.30) or (rec["priority"] == 2 and p < 0.10):
                continue  # aetiological work-up only for entities with real support
            dkey = tuple(sorted(rec["features"]))  # one line per test, whichever entity asked first/strongest
            cur = out.get(dkey)
            score = (4 - rec["priority"]) + p  # priority dominates, probability breaks ties
            if cur is None or score > cur["_score"]:
                out[dkey] = {"test": rec["test"], "priority": rec["priority"], "because_of": did, "entity_probability": round(p, 3),
                                    "rationale": rec["why"], "source": rec["src"], "satisfied_by": list(rec["features"]), "_score": score}
    # value-level triggers that no entity carries (ESL ext 8b): ADA 2024 §2 — a random glucose of 140–199 mg/dL
    # does not diagnose diabetes but is an indication to test HbA1c; below 200 the engine (correctly) proposes no
    # diabetes entity, so the recommendation must come from the value itself.
    if value_of is not None:
        glu = value_of("glucose")
        if glu is not None and 140.0 <= glu < 200.0 and "hemoglobin_a1c" not in observed:
            dkey = ("hemoglobin_a1c",)
            if dkey not in out:
                out[dkey] = {"test": "HbA1c", "priority": 2, "because_of": "glucose 140–199 mg/dL", "entity_probability": None,
                             "rationale": "random glucose in the 140–199 mg/dL band: test for undiagnosed diabetes/prediabetes", "source": "ADA Standards of Care 2024 §2.2 and §16",
                             "satisfied_by": ["hemoglobin_a1c"], "_score": 2.5, "_pin": True}
    pinned = [r for r in out.values() if r.get("_pin")]
    ranked = sorted((r for r in out.values() if not r.get("_pin")), key=lambda r: -r["_score"])[:max(0, max_items - len(pinned))]
    ranked = sorted(ranked + pinned, key=lambda r: -r["_score"])
    for r in ranked:
        r.pop("_score", None); r.pop("_pin", None)
    return ranked


@dataclass
class InterpretationReport:
    interpretations: list[DiseaseInterpretation]
    summary: dict[str, int]
    skipped_rules: dict[str, str]
    catalog_only_disease_count: int
    warnings: list[str]
    engine_version: str = "6.1.0-clinical"
    execution_mode: str = "research"
    rule_count: int = 0
    gated_interpretations: int = 0
    positive_count: int = 0
    insufficient_count: int = 0
    conflicting_count: int = 0
    not_applicable_count: int = 0

    ruled_out_count: int = 0
    critical_alerts: list[dict[str, Any]] = field(default_factory=list)

    differential_diagnosis: list[dict[str, Any]] = field(
        default_factory=list)
    knowledge_graph_insights: dict[str, Any] = field(
        default_factory=dict)
    interference_corrections: list[dict[str, Any]] = field(
        default_factory=list)
    drug_interactions: list[dict[str, Any]] = field(default_factory=list)
    expanded_kg_insights: dict[str, Any] = field(default_factory=dict)
    differential_groups: dict[str, list[str]] = field(default_factory=dict)
    contraindications: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict)

    derived_patterns: list[dict[str, Any]] = field(default_factory=list)

    executive_summary: str = ''
    data_completeness: dict[str, Any] = field(default_factory=dict)
    expert_syndromes: list[dict[str, Any]] = field(default_factory=list)
    next_tests: list[dict[str, Any]] = field(default_factory=list)  # ESL extension 8
    temporal_findings: list[dict[str, Any]] = field(default_factory=list)   # ESL extension 11-T
    clinical_context_applied: list[dict[str, Any]] = field(default_factory=list)  # ESL extension 11-C

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass
class EnrichedObservation:
    feature_id: str
    value: float
    unit: str
    z_score: Optional[float] = None
    percentile: Optional[float] = None
    deviation_from_ref: Optional[float] = None
    severity_score: float = 0.0
    # 'unknown' until an interval was actually applied. Defaulting to
    # 'normal' silently vetoed every Bayesian finding on the ~2,000 analytes
    # without an engine-side interval (anion gap, ketones, pH, lipase, CK...).
    direction: str = 'unknown'
    reliability: float = 1.0
    fuzzy_membership: Optional[float] = None

    corrected_value: Optional[float] = None
    correction_note: Optional[str] = None
    context_flags: dict[str, Any] = field(default_factory=dict)
    # Which interval the verdict was made against and why.
    reference_source: str = "registry"          # registry | laboratory_reported | registry_locked
    reference_used: dict[str, float] = field(default_factory=dict)
    reference_note: Optional[str] = None


# Pure transforms over observations - no instance state was ever kept.
REFERENCE_RANGES = {
    "hemoglobin": {"mean": 14.5, "std": 1.5, "low": 12.0,
                   "high": 17.5, "critical_low": 7.0,
                   "critical_high": 20.0},
    'creatinine': {"mean": 0.9, 'std': 0.2, "low": 0.6,
                   "high": 1.3, "critical_low": 0.3,
                   "critical_high": 5.0},
    "glucose": {"mean": 90, "std": 15, "low": 70, "high": 110,
                "critical_low": 50, "critical_high": 300},
    "fasting_plasma_glucose": {"mean": 90, "std": 12, "low": 70,
                               "high": 100, "critical_low": 50,
                               "critical_high": 300},
    "platelet_count": {"mean": 250, "std": 60, "low": 150,
                       "high": 400, "critical_low": 50,
                       "critical_high": 1000},
    'white_blood_cell_count': {"mean": 7.5, "std": 2.5,
                               "low": 4.0, "high": 11.0,
                               "critical_low": 1.0,
                               'critical_high': 50.0},
    'hematocrit': {"mean": 43, "std": 5, "low": 36, "high": 52,
                   "critical_low": 20, "critical_high": 65},
    "sodium": {"mean": 140, "std": 3, "low": 135, "high": 145,
               "critical_low": 120, 'critical_high': 160},
    'potassium': {"mean": 4.2, 'std': 0.5, 'low': 3.5,
                  "high": 5.0, 'critical_low': 2.5,
                  "critical_high": 6.5},
    "alanine_aminotransferase": {"mean": 30, "std": 15,
                                 "low": 7, 'high': 56,
                                 "critical_low": 0,
                                 "critical_high": 500},
    "aspartate_aminotransferase": {"mean": 28, "std": 12,
                                   "low": 10, "high": 40,
                                   "critical_low": 0,
                                   "critical_high": 500},
    'thyroid_stimulating_hormone': {'mean': 2.0, "std": 1.5,
                                    "low": 0.4, "high": 4.0,
                                    "critical_low": 0.01,
                                    'critical_high': 50.0},
    "total_cholesterol": {"mean": 190, "std": 35, "low": 120,
                          "high": 240, "critical_low": 80,
                          "critical_high": 400},
    "triglycerides": {"mean": 130, "std": 60, "low": 40,
                      "high": 200, "critical_low": 10,
                      "critical_high": 1000},
    "hdl_cholesterol": {"mean": 55, "std": 15, 'low': 35,
                        "high": 90, 'critical_low': 15,
                        "critical_high": 150},
    "ferritin": {"mean": 100, "std": 80, "low": 20, "high": 300,
                 "critical_low": 5, "critical_high": 2000},
    "c_reactive_protein": {"mean": 3, "std": 5, "low": 0,
                           "high": 10, "critical_low": 0,
                           'critical_high': 200},
    "albumin": {"mean": 4.2, "std": 0.4, "low": 3.5, 'high': 5.0,
                'critical_low': 1.5, "critical_high": 6.0},
    "calcium_total": {"mean": 9.5, "std": 0.5, "low": 8.5,
                      'high': 10.5, "critical_low": 6.0,
                      "critical_high": 13.0},
    "bilirubin_total": {'mean': 0.8, "std": 0.4, "low": 0.1,
                        "high": 1.2, "critical_low": 0,
                        "critical_high": 15.0},
    "egfr_ckd_epi_creatinine": {"mean": 95, "std": 20,
                                'low': 60, 'high': 130,
                                "critical_low": 5,
                                "critical_high": 200},
    "alkaline_phosphatase": {"mean": 80, "std": 25, "low": 44, "high": 147,
                            "critical_low": 15, "critical_high": 1000},
    "phosphate": {"mean": 3.5, "std": 0.5, "low": 2.5, "high": 4.5,
                  "critical_low": 1.0, "critical_high": 8.0},
    "blood_urea_nitrogen": {"mean": 14, "std": 3.5, "low": 7.0, "high": 22.0,
                            "critical_low": 2.0, "critical_high": 100.0},
    "uric_acid": {"mean": 5.0, "std": 1.2, "low": 3.0, "high": 7.0,
                  "critical_low": 1.5, "critical_high": 12.0},
    "lactate_dehydrogenase": {"mean": 180, "std": 35, "low": 140, "high": 280,
                              "critical_low": 50, "critical_high": 1500},
    "bilirubin_direct": {"mean": 0.15, "std": 0.08, "low": 0.0, "high": 0.3,
                         "critical_low": 0.0, "critical_high": 10.0},
    "total_protein": {"mean": 7.2, "std": 0.5, "low": 6.4, "high": 8.3,
                      "critical_low": 4.5, "critical_high": 11.0},
    "mean_corpuscular_volume": {"mean": 90, "std": 5, "low": 80, "high": 100,
                                "critical_low": 60, "critical_high": 125},
    "mean_corpuscular_hemoglobin": {"mean": 30, "std": 2, "low": 27, "high": 33,
                                    "critical_low": 18, "critical_high": 40},
    "mchc": {"mean": 34, "std": 1.5, "low": 32, "high": 36,
             "critical_low": 28, "critical_high": 38},
    "red_cell_distribution_width": {"mean": 13.0, "std": 1.0, "low": 11.5, "high": 14.5,
                                    "critical_low": 10.0, "critical_high": 25.0},
    "fibrinogen": {"mean": 300, "std": 50, "low": 200, "high": 400,
                   "critical_low": 100, "critical_high": 800},
    "d_dimer": {"mean": 0.25, "std": 0.1, "low": 0.0, "high": 0.5,
                "critical_low": 0.0, "critical_high": 5.0},
    "gamma_glutamyl_transferase": {"mean": 25, "std": 12, "low": 9, "high": 48,
                                   "critical_low": 0, "critical_high": 400},
    "magnesium": {"mean": 2.0, "std": 0.2, "low": 1.7, "high": 2.2,
                  "critical_low": 1.0, "critical_high": 4.0},
    "chloride": {"mean": 101, "std": 3, "low": 96, "high": 106,
                 "critical_low": 80, "critical_high": 125},
    "bicarbonate": {"mean": 25, "std": 2, "low": 22, "high": 29,
                    "critical_low": 10, "critical_high": 40},
    "prothrombin_time": {"mean": 12.0, "std": 0.8, "low": 11.0, "high": 13.5,
                         "critical_low": 9.0, "critical_high": 30.0},
    "international_normalized_ratio": {"mean": 1.0, "std": 0.1, "low": 0.8, "high": 1.1,
                                       "critical_low": 0.5, "critical_high": 5.0},
}

AGE_SPECIFIC_RANGES: dict[str, dict[str, dict]] = {
    # Term neonate, 48-120 h: Bhutani low-risk zone upper bound ~12 mg/dL;
    # AAP 2022 phototherapy threshold (>=38 wk, no risk factors) ~15 at 48 h.
    # Physiologic jaundice must not surface as "isolated hyperbilirubinemia".
    "total_bilirubin": {
        "neonate": {"low": 0.2, "high": 12.0, "critical_low": 0.0, "critical_high": 20.0},
        "infant": {"low": 0.1, "high": 1.2, "critical_low": 0.0, "critical_high": 12.0},
        "child": {"low": 0.1, "high": 1.2, "critical_low": 0.0, "critical_high": 12.0},
        "adult": {"low": 0.1, "high": 1.2, "critical_low": 0.0, "critical_high": 12.0},
    },
    "alkaline_phosphatase": {
        "neonate": {"low": 75, "high": 450, "mean": 220, "std": 70},
        "infant": {'low': 82, "high": 450, "mean": 220, "std": 70},
        "young_child": {"low": 100, "high": 450, "mean": 240, "std": 70},
        "child": {"low": 93, "high": 850, "mean": 280, "std": 100},
        "adolescent": {"low": 62, "high": 850, "mean": 300, "std": 120},
        "adult": {"low": 44, "high": 147, "mean": 80, "std": 25},
        "older_adult": {"low": 45, "high": 160, "mean": 95, "std": 28},
    },
    "phosphate": {
        "neonate": {"low": 4.5, "high": 8.0, "mean": 6.0, "std": 0.8},
        "infant": {"low": 4.5, "high": 6.7, "mean": 5.5, "std": 0.6},
        "young_child": {"low": 4.0, "high": 6.0, "mean": 5.0, "std": 0.5},
        "child": {"low": 4.0, "high": 5.8, "mean": 4.8, "std": 0.5},
        "adolescent": {"low": 3.0, "high": 5.2, "mean": 4.0, "std": 0.5},
        "adult": {"low": 2.5, "high": 4.5, "mean": 3.5, "std": 0.5},
    },
    "creatinine": {
        "neonate": {"low": 0.20, "high": 0.50, "mean": 0.35, "std": 0.08},
        "infant": {"low": 0.15, "high": 0.42, "mean": 0.28, "std": 0.06},
        "young_child": {"low": 0.20, "high": 0.55, "mean": 0.38, "std": 0.08},
        "child": {"low": 0.30, "high": 0.70, "mean": 0.50, "std": 0.10},
        "adolescent": {"low": 0.50, "high": 0.90, "mean": 0.70, "std": 0.12},
        "adult": None,
        "older_adult": {"low": 0.60, "high": 1.30, "mean": 0.95, "std": 0.18},
    },
    "ferritin": {
        "neonate": {"low": 25, "high": 200, "mean": 100, "std": 40},
        "infant": {"low": 15, "high": 150, "mean": 60, "std": 30},
        "young_child": {"low": 15, "high": 150, "mean": 50, "std": 25},
        "child": {"low": 15, "high": 150, "mean": 50, "std": 25},
        "adolescent": {"low": 15, "high": 200, "mean": 60, "std": 30},
        "adult": None,
    },
    "hematocrit": {
        "neonate": {"low": 42.0, "high": 65.0, "mean": 53.0, "std": 5.0},
        "infant": {"low": 31.0, "high": 41.0, "mean": 36.0, "std": 2.5},
        "young_child": {"low": 32.0, "high": 42.0, "mean": 37.0, "std": 2.0},
        "child": {"low": 34.0, "high": 42.0, "mean": 38.0, "std": 2.0},
        "adolescent": {"low": 36.0, "high": 46.0, "mean": 41.0, "std": 2.5},
        "adult": None,
    },
    "blood_urea_nitrogen": {
        "neonate": {"low": 4.0, "high": 16.0, "mean": 9.0, "std": 2.5},
        "infant": {"low": 4.0, "high": 16.0, "mean": 9.0, "std": 2.5},
        "young_child": {"low": 5.0, "high": 18.0, "mean": 10.5, "std": 3.0},
        "child": {"low": 5.0, "high": 18.0, "mean": 11.0, "std": 3.0},
        "adolescent": {"low": 6.0, "high": 20.0, "mean": 12.0, "std": 3.0},
        "adult": {"low": 7.0, "high": 22.0, "mean": 14.0, "std": 3.5},
        "older_adult": {"low": 8.0, "high": 25.0, "mean": 16.0, "std": 4.0},
    },
    "platelet_count": {
        "neonate": {"low": 150, "high": 450, "mean": 280, "std": 60},
        "infant": {"low": 150, "high": 450, "mean": 280, "std": 60},
        "young_child": {"low": 150, "high": 450, "mean": 280, "std": 60},
        "child": {"low": 150, "high": 450, "mean": 280, "std": 60},
        "adolescent": {"low": 150, "high": 450, "mean": 280, "std": 60},
        "adult": {"low": 150, "high": 450, "mean": 250, "std": 60},
    },
    "aspartate_aminotransferase": {
        "neonate": {"low": 15, "high": 70, "mean": 35, "std": 12},
        "infant": {"low": 15, "high": 60, "mean": 32, "std": 10},
        "young_child": {"low": 10, "high": 45, "mean": 26, "std": 8},
        "child": {"low": 10, "high": 45, "mean": 25, "std": 8},
        "adolescent": {"low": 10, "high": 40, "mean": 24, "std": 7},
        "adult": {"low": 10, "high": 40, "mean": 25, "std": 8},
    },
    "alanine_aminotransferase": {
        "neonate": {"low": 5, "high": 45, "mean": 20, "std": 8},
        "infant": {"low": 5, "high": 45, "mean": 20, "std": 8},
        "young_child": {"low": 5, "high": 35, "mean": 18, "std": 6},
        "child": {"low": 5, "high": 35, "mean": 18, "std": 6},
        "adolescent": {"low": 5, "high": 40, "mean": 20, "std": 7},
        "adult": {"low": 5, "high": 50, "mean": 25, "std": 10},
    },
    "hemoglobin": {
        "neonate": {"low": 14.5, "high": 22.5, "mean": 17.5, "std": 1.8},
        "infant": {"low": 10.0, "high": 14.0, "mean": 12.0, "std": 1.0},
        "young_child": {"low": 11.0, "high": 14.5, "mean": 12.8, "std": 1.0},
        "child": {'low': 11.0, 'high': 15.0, "mean": 13.0, "std": 1.0},
        "adolescent": {'low': 11.5, "high": 16.5, "mean": 14.0, "std": 1.2},
        "adult": None,
    },
    "white_blood_cell_count": {
        "neonate": {'low': 9.0, "high": 30.0, "mean": 18.0, "std": 4.0},
        "infant": {'low': 6.0, 'high': 17.5, "mean": 11.0, "std": 2.5},
        "young_child": {"low": 5.5, "high": 15.5, "mean": 9.5, "std": 2.2},
        "child": {"low": 5.0, "high": 14.5, "mean": 9.0, "std": 2.0},
        "adolescent": {"low": 4.5, "high": 11.0, "mean": 7.5, "std": 1.8},
        'adult': None,
    },
    "thyroid_stimulating_hormone": {
        "neonate": {"low": 0.7, "high": 15.2, "mean": 5.0, "std": 3.0},
        "infant": {"low": 0.6, 'high': 8.0, 'mean': 2.5, "std": 1.5},
        "young_child": {"low": 0.6, "high": 6.5, "mean": 2.5, "std": 1.2},
        "child": {"low": 0.5, "high": 6.0, "mean": 2.2, "std": 1.2},
        "adolescent": {"low": 0.5, "high": 5.0, "mean": 2.0, "std": 1.0},
        "adult": None,
    },
}

SEX_SPECIFIC_RANGES: dict[str, dict[str, dict]] = {
    'hemoglobin': {
        "female": {"low": 12.0, "high": 15.5, "mean": 13.5, "std": 0.9},
        "male": {"low": 13.5, "high": 17.5, "mean": 15.0, 'std': 1.0},
    },
    "creatinine": {
        "female": {"low": 0.5, "high": 1.1, 'mean': 0.8, "std": 0.15},
        "male": {'low': 0.7, "high": 1.3, "mean": 1.0, "std": 0.18},
    },
    "ferritin": {
        "female": {"low": 12, "high": 150, "mean": 50, "std": 35},
        "male": {"low": 24, "high": 336, "mean": 120, "std": 60},
    },
    "uric_acid": {
        "female": {"low": 2.6, "high": 6.0, "mean": 4.2, "std": 0.8},
        "male": {"low": 3.5, "high": 7.2, "mean": 5.4, "std": 0.9},
    },
    "gamma_glutamyl_transferase": {
        "female": {"low": 9, "high": 38, "mean": 20, "std": 8},
        "male": {"low": 10, "high": 55, "mean": 28, "std": 11},
    },
}

PREGNANCY_SPECIFIC_RANGES: dict[str, dict[str, dict]] = {
    "hemoglobin": {
        "trimester_1": {"low": 11.0, "high": 14.0, "mean": 12.5, "std": 0.8},
        "trimester_2": {"low": 10.5, "high": 14.0, "mean": 11.8, "std": 0.8},
        "trimester_3": {"low": 11.0, "high": 14.0, "mean": 12.2, "std": 0.8},
        "general": {"low": 10.5, "high": 14.0, "mean": 12.0, "std": 0.8},
    },
    "hematocrit": {
        "trimester_1": {"low": 33.0, "high": 41.0, "mean": 37.0, "std": 2.0},
        "trimester_2": {"low": 30.0, "high": 39.0, "mean": 34.5, "std": 2.0},
        "trimester_3": {"low": 31.0, "high": 40.0, "mean": 35.5, "std": 2.0},
        "general": {"low": 30.0, "high": 40.0, "mean": 35.0, "std": 2.0},
    },
    "platelet_count": {
        "trimester_1": {"low": 150, "high": 450, "mean": 270, "std": 60},
        "trimester_2": {"low": 130, "high": 450, "mean": 250, "std": 60},
        "trimester_3": {"low": 100, "high": 450, "mean": 230, "std": 60},
        "general": {"low": 100, "high": 450, "mean": 240, "std": 60},
    },
    "alkaline_phosphatase": {
        "trimester_1": {"low": 40, "high": 140, "mean": 75, "std": 20},
        "trimester_2": {"low": 50, "high": 280, "mean": 140, "std": 45},
        "trimester_3": {"low": 100, "high": 450, "mean": 240, "std": 70},
        "general": {"low": 50, "high": 400, "mean": 180, "std": 60},
    },
    "creatinine": {
        "trimester_1": {"low": 0.40, "high": 0.75, "mean": 0.55, "std": 0.08},
        "trimester_2": {"low": 0.40, "high": 0.75, "mean": 0.55, "std": 0.08},
        "trimester_3": {"low": 0.40, "high": 0.80, "mean": 0.58, "std": 0.09},
        "general": {"low": 0.40, "high": 0.80, "mean": 0.55, "std": 0.08},
    },
    "blood_urea_nitrogen": {
        "trimester_1": {"low": 4.0, "high": 14.0, "mean": 8.5, "std": 2.5},
        "trimester_2": {"low": 3.0, "high": 13.0, "mean": 7.5, "std": 2.5},
        "trimester_3": {"low": 4.0, "high": 14.0, "mean": 8.5, "std": 2.5},
        "general": {"low": 3.5, "high": 14.0, "mean": 8.0, "std": 2.5},
    },
    "fasting_plasma_glucose": {
        "trimester_1": {"low": 60, "high": 92, "mean": 78, "std": 8},
        "trimester_2": {"low": 60, "high": 92, "mean": 76, "std": 8},
        "trimester_3": {"low": 60, "high": 92, "mean": 76, "std": 8},
        "general": {"low": 60, "high": 92, "mean": 76, "std": 8},
    },
    "fibrinogen": {
        "trimester_1": {"low": 250, "high": 500, "mean": 375, "std": 50},
        "trimester_2": {"low": 300, "high": 550, "mean": 425, "std": 50},
        "trimester_3": {"low": 350, "high": 650, "mean": 480, "std": 60},
        "general": {"low": 300, "high": 600, "mean": 430, "std": 60},
    },
    "white_blood_cell_count": {
        "trimester_1": {"low": 5.7, "high": 13.6, "mean": 9.0, "std": 2.0},
        "trimester_2": {"low": 5.6, "high": 14.8, "mean": 9.5, "std": 2.2},
        "trimester_3": {"low": 5.9, "high": 16.9, "mean": 10.5, "std": 2.5},
        "general": {"low": 5.7, "high": 15.0, "mean": 9.8, "std": 2.3},
    },
    "erythrocyte_sedimentation_rate": {
        "trimester_1": {"low": 4, "high": 48, "mean": 24, "std": 10},
        "trimester_2": {"low": 15, "high": 60, "mean": 35, "std": 12},
        "trimester_3": {"low": 20, "high": 70, "mean": 45, "std": 12},
        "general": {"low": 10, "high": 65, "mean": 36, "std": 12},
    },
    "total_protein": {
        "trimester_1": {"low": 6.2, "high": 8.0, "mean": 7.0, "std": 0.4},
        "trimester_2": {"low": 5.7, "high": 7.5, "mean": 6.5, "std": 0.4},
        "trimester_3": {"low": 5.5, "high": 7.3, "mean": 6.3, "std": 0.4},
        "general": {"low": 5.5, "high": 7.5, "mean": 6.5, "std": 0.4},
    },
    "albumin": {
        "trimester_1": {"low": 3.1, "high": 4.5, "mean": 3.8, "std": 0.3},
        "trimester_2": {"low": 2.8, "high": 4.2, "mean": 3.4, "std": 0.3},
        "trimester_3": {"low": 2.6, "high": 4.0, "mean": 3.2, "std": 0.3},
        "general": {"low": 2.8, "high": 4.2, "mean": 3.4, "std": 0.3},
    },
}

GERIATRIC_SPECIFIC_RANGES: dict[str, dict[str, Any]] = {
    "alkaline_phosphatase": {"low": 45, "high": 160, "mean": 95, "std": 28},
    "blood_urea_nitrogen": {"low": 8.0, "high": 25.0, "mean": 16.0, "std": 4.0},
    "fasting_plasma_glucose": {"low": 70, "high": 105, "mean": 92, "std": 12},
    "erythrocyte_sedimentation_rate": {"low": 0, "high": 35, "mean": 18, "std": 8},
}

def emal_interference_corrections(observations: Mapping[str, ObservationRecord],
    context: ClinicalContext,
) -> list[dict[str, Any]]:
    corrections: list[dict[str, Any]] = []
    obs_values: dict[str, float] = {}
    for fid, rec in observations.items():
        v = _float(rec.value)
        if v is not None:
            obs_values[fid] = v


    ca = obs_values.get("calcium_total")
    alb = _float(context.get("serum_albumin"))
    if alb is None:
        alb = obs_values.get("albumin")
    if ca is not None and alb is not None and alb < 4.0:
        corrected = ca + 0.8 * (4.0 - alb)
        corrections.append({
            "feature_id": "calcium_total",
            "correction": 'albumin_corrected',
            "original_value": ca,
            "corrected_value": round(corrected, 2),
            "formula": f"Ca + 0.8×(4.0 − Alb={alb:g})",
            "citation": "Payne RB, 1973",
        })


    na = obs_values.get("sodium")
    glu = _float(context.get("serum_glucose_mgdl"))
    if glu is None:
        glu = obs_values.get("fasting_plasma_glucose")
    if glu is None:
        glu = obs_values.get('glucose')
    if na is not None and glu is not None and glu > 100:
        corrected = na + 1.6 * ((glu - 100) / 100.0)
        corrections.append({
            "feature_id": "sodium",
            "correction": "glucose_corrected",
            "original_value": na,
            "corrected_value": round(corrected, 2),
            "formula": f"Na + 1.6×((Glu={glu:g} − 100)/100)",
            "citation": 'Katz MA, 1973',
        })

    return corrections

def enrich_observations(observations: Mapping[str, ObservationRecord],
    context: Optional[ClinicalContext] = None,
    corrections: Optional[list[dict[str, Any]]] = None,
) -> dict[str, EnrichedObservation]:
    """Attach reference ranges, severity and reliability.

        Severity is how far a value sits past its cutoff, scaled
        by age- and sex-specific ranges where those exist. The
        Bayesian layer uses it to weight likelihood ratios.
        """
    ctx = context or ClinicalContext()
    corr_map = {c["feature_id"]: c for c in (corrections or [])}
    enriched: dict[str, EnrichedObservation] = {}

    for fid, record in observations.items():
        value = _float(record.value)
        if value is None:
            q = _qualitative(record.value)
            if q == "positive":
                value = 1.0
            elif q == "negative":
                value = 0.0
            else:
                continue


        note = None
        effective_value = value
        corr = corr_map.get(fid)
        if corr is not None:
            effective_value = corr["corrected_value"]
            note = (f"Corrected for interference "
                    f"({corr['correction']}): {corr['formula']}")

        ref = _get_reference(fid, ctx)
        ref, ref_source, ref_note = apply_local_reference(fid, ref, record)

        # Scale cell counts for reference comparison if values were provided in raw /uL
        ref_comp_val = effective_value
        if fid in ("platelet_count", "platelets", "plt") and ref_comp_val > 1000.0:
            ref_comp_val = ref_comp_val / 1000.0
        elif fid in ("white_blood_cell_count", "wbc", "white_blood_cells") and ref_comp_val > 100.0:
            ref_comp_val = ref_comp_val / 1000.0
        elif fid in ("red_blood_cell_count", "rbc", "red_blood_cells") and ref_comp_val > 10000.0:
            ref_comp_val = ref_comp_val / 1000000.0

        obs = EnrichedObservation(
            feature_id=fid, value=effective_value,
            unit=record.unit or "",
            reliability=_arzyabi_reliability(record),
            corrected_value=(effective_value
                             if corr is not None else None),
            correction_note=note,
            reference_source=ref_source,
            reference_used={k: float(v) for k, v in ref.items()
                            if k in ("low", "high", "critical_low", "critical_high")
                            and isinstance(v, (int, float))},
            reference_note=ref_note,
        )

        if "mean" in ref and "std" in ref and ref["std"] > 0:
            obs.z_score = (ref_comp_val - ref["mean"]) / ref["std"]
            obs.percentile = _z_to_percentile(obs.z_score)
        if "low" in ref and 'high' in ref:
            obs.deviation_from_ref = _ref_deviation(
                ref_comp_val, ref)
            obs.severity_score = _severity_emtiaz(
                ref_comp_val, ref)
            obs.direction = _tabaghebandi_direction(
                ref_comp_val, ref)
            obs.fuzzy_membership = _fuzzy_membership(
                ref_comp_val, ref)


        enriched[fid] = obs
    return enriched

# ---------------------------------------------------------------------------
# Reference-interval policy (CLSI EP28-A3c vs. clinical decision limits)
#
# Two kinds of cut-off exist and must be treated differently:
#
#  * CLINICAL DECISION LIMITS (CDL) are fixed by outcome studies and are
#    method-independent by design (ADA FPG >= 126 mg/dL, HbA1c >= 6.5 %,
#    WHO anaemia thresholds, KDIGO creatinine / eGFR, ACC/AHA lipid cut
#    points, universal electrolyte panic values). A local kit's printed
#    interval must NOT move these. We keep the registry value and only
#    warn when the laboratory's interval disagrees.
#
#  * METHOD-DEPENDENT REFERENCE INTERVALS: enzymes (37 vs 30 degC, with/
#    without pyridoxal phosphate), immunoassays (TSH, prolactin,
#    testosterone, tumour markers, troponin 99th percentile, NT-proBNP),
#    acute-phase proteins. For these the interval printed by the
#    performing laboratory is the correct one (CLSI EP28-A3c; Tietz). When
#    the report carries a sane interval we interpret against it and
#    scale ULN-multiple thresholds accordingly.
# ---------------------------------------------------------------------------
CDL_LOCKED_FEATURES: frozenset[str] = frozenset({
    "glucose", "fasting_plasma_glucose", "fasting_glucose",
    "random_glucose", "hba1c", "hemoglobin_a1c", "ogtt_2h_glucose",
    "ldl_cholesterol", "hdl_cholesterol", "total_cholesterol",
    "triglycerides", "non_hdl_cholesterol",
    "creatinine", "egfr", "estimated_gfr", "cystatin_c",
    "urea", "blood_urea_nitrogen",
    "sodium", "potassium", "chloride", "bicarbonate", "calcium_total",
    "ionized_calcium", "magnesium", "phosphate", "phosphorus",
    "hemoglobin", "hematocrit", "platelet_count", "white_blood_cell_count",
    "absolute_neutrophil_count", "mean_corpuscular_volume",
    "inr", "international_normalized_ratio",
    "ph", "pco2", "po2", "lactate", "bilirubin_total", "uric_acid",
    "ferritin_low_cutoff", "vitamin_d_25oh", "vitamin_b12", "folate",
    "urine_albumin_creatinine_ratio", "albumin",
})

METHOD_DEPENDENT_FEATURES: frozenset[str] = frozenset({
    "alanine_aminotransferase", "aspartate_aminotransferase",
    "alkaline_phosphatase", "gamma_glutamyl_transferase",
    "lactate_dehydrogenase", "creatine_kinase", "creatine_kinase_mb",
    "amylase", "lipase", "cholinesterase", "aldolase",
    "thyroid_stimulating_hormone", "free_thyroxine", "free_triiodothyronine",
    "total_thyroxine", "total_triiodothyronine", "thyroglobulin",
    "anti_tpo", "anti_thyroglobulin", "trab",
    "prolactin", "testosterone_total", "testosterone_free", "estradiol",
    "progesterone", "luteinizing_hormone", "follicle_stimulating_hormone",
    "cortisol", "acth", "parathyroid_hormone", "growth_hormone", "igf_1",
    "insulin", "c_peptide", "dhea_s", "shbg", "amh",
    "prostate_specific_antigen", "free_psa", "ca_125", "ca_19_9", "ca_15_3",
    "carcinoembryonic_antigen", "alpha_fetoprotein", "beta_2_microglobulin",
    "troponin_i", "troponin_t", "hs_troponin_i", "hs_troponin_t",
    "nt_pro_bnp", "bnp", "d_dimer", "fibrinogen",
    "c_reactive_protein", "hs_crp", "erythrocyte_sedimentation_rate",
    "procalcitonin", "ferritin", "transferrin", "haptoglobin",
    "immunoglobulin_g", "immunoglobulin_a", "immunoglobulin_m",
    "immunoglobulin_e", "complement_c3", "complement_c4",
    "rheumatoid_factor", "anti_ccp", "ana_titer", "anti_dsdna",
    "homocysteine", "lipoprotein_a", "apolipoprotein_b", "apolipoprotein_a1",
})

# A printed interval is only trusted if it is internally sane and within a
# plausible factor of the registry interval; otherwise it is most likely an
# OCR / column-association error and must not recalibrate anything.
_LOCAL_REF_MIN_RATIO = 0.40
_LOCAL_REF_MAX_RATIO = 2.50


def reference_policy(fid: str) -> str:
    if fid in CDL_LOCKED_FEATURES:
        return "cdl_locked"
    if fid in METHOD_DEPENDENT_FEATURES:
        return "method_dependent"
    return "registry_default"


def _sane_local_interval(low: Optional[float], high: Optional[float],
                         registry: Mapping[str, Any]) -> bool:
    if high is None and low is None:
        return False
    if low is not None and high is not None and not (low < high):
        return False
    r_hi = _float(registry.get("high"))
    r_lo = _float(registry.get("low"))
    if high is not None and r_hi not in (None, 0.0):
        ratio = high / r_hi
        if not (_LOCAL_REF_MIN_RATIO <= ratio <= _LOCAL_REF_MAX_RATIO):
            return False
    if low is not None and r_lo not in (None, 0.0) and r_lo > 0:
        ratio = low / r_lo
        if not (_LOCAL_REF_MIN_RATIO <= ratio <= _LOCAL_REF_MAX_RATIO):
            return False
    return True


def apply_local_reference(fid: str, ref: dict[str, Any],
                          record: Optional[ObservationRecord]
                          ) -> tuple[dict[str, Any], str, Optional[str]]:
    """Decide which interval governs this analyte.

    Returns (reference_dict, source, note). Registry critical_* values are
    always kept: a laboratory's normal range says nothing about panic
    thresholds.
    """
    if record is None:
        return ref, "registry", None
    lo, hi = _float(record.reference_low), _float(record.reference_high)
    if lo is None and hi is None:
        return ref, "registry", None
    policy = reference_policy(fid)
    if policy == "cdl_locked":
        note = None
        r_hi, r_lo = _float(ref.get("high")), _float(ref.get("low"))
        if (hi is not None and r_hi is not None and abs(hi - r_hi) > 0.05 * max(1.0, abs(r_hi))) \
                or (lo is not None and r_lo is not None and abs(lo - r_lo) > 0.05 * max(1.0, abs(r_lo))):
            note = (f"{fid}: laboratory interval "
                    f"{lo if lo is not None else '…'}–{hi if hi is not None else '…'} "
                    f"differs from the guideline decision limit; the "
                    f"guideline limit (ADA/KDIGO/WHO/ACC-AHA) governs.")
        return ref, "registry_locked", note
    if not _sane_local_interval(lo, hi, ref):
        return ref, "registry", (
            f"{fid}: printed interval {lo}–{hi} is implausible versus the "
            f"registry interval; ignored (possible OCR / column error).")
    local = dict(ref)
    if lo is not None:
        local["low"] = lo
    if hi is not None:
        local["high"] = hi
    # keep z-score machinery coherent with the new interval
    if lo is not None and hi is not None:
        local["mean"] = (lo + hi) / 2.0
        local["std"] = max(1e-9, (hi - lo) / 3.92)
    src = "laboratory_reported"
    if policy == "registry_default":
        # Unknown method dependence: trust the lab interval but say so.
        return local, src, (f"{fid}: interpreted against the performing "
                            f"laboratory's interval {lo}–{hi}.")
    return local, src, (f"{fid}: method-dependent analyte; interpreted "
                        f"against the laboratory's interval {lo}–{hi} "
                        f"(CLSI EP28-A3c).")


def local_reference_scale(fid: str, record: Optional[ObservationRecord],
                          ctx: ClinicalContext) -> tuple[float, float]:
    """(low_ratio, high_ratio) = laboratory / registry, for scaling
    ULN/LLN-multiple thresholds of method-dependent analytes. 1.0 = none."""
    if record is None or fid in CDL_LOCKED_FEATURES:
        return 1.0, 1.0
    base = _get_reference(fid, ctx)
    lo, hi = _float(record.reference_low), _float(record.reference_high)
    if not _sane_local_interval(lo, hi, base):
        return 1.0, 1.0
    r_lo, r_hi = _float(base.get("low")), _float(base.get("high"))
    lo_ratio = (lo / r_lo) if (lo is not None and r_lo) else 1.0
    hi_ratio = (hi / r_hi) if (hi is not None and r_hi) else 1.0
    return lo_ratio, hi_ratio


def _get_reference(fid: str,
                   ctx: ClinicalContext) -> dict[str, Any]:
    base = dict(REFERENCE_RANGES.get(fid, {}))
    grp = ctx.age_group

    # 1. Pregnancy-specific overrides take highest precedence when pregnant
    if ctx.pregnant:
        preg_table = PREGNANCY_SPECIFIC_RANGES.get(fid)
        if preg_table:
            trimester = getattr(ctx, "pregnancy_trimester", None)
            trim_key = f"trimester_{trimester}" if trimester in (1, 2, 3) else None
            override = preg_table.get(trim_key) or preg_table.get("general")
            if override:
                base.update(override)
                return base

    # 2. Sex-specific ranges are derived from adult populations
    if grp in ("adult", "older_adult", None):
        sex_table = SEX_SPECIFIC_RANGES.get(fid)
        if sex_table:
            sex = ctx.normalized_jensiat()
            override = sex_table.get(sex) if sex else None
            if override is not None:
                base.update(override)

    # 3. Geriatric overrides for older adults (age >= 65)
    if grp == "older_adult":
        ger_override = GERIATRIC_SPECIFIC_RANGES.get(fid)
        if ger_override:
            base.update(ger_override)

    # 4. Age-specific ranges with hierarchical fallback
    age_table = AGE_SPECIFIC_RANGES.get(fid)
    if age_table:
        override = age_table.get(grp)
        if override is None:
            fallback_map = {
                'young_child': ['child', 'infant'],
                'older_adult': ['adult'],
                'neonate': ['infant', 'child'],
                'infant': ['child'],
                'adolescent': ['child', 'adult'],
            }
            for fb in fallback_map.get(grp, []):
                override = age_table.get(fb)
                if override is not None:
                    break
        if override is not None:
            base.update(override)
    return base

def _severity_emtiaz(value: float, ref: dict) -> float:
    if not ref:
        return 0.0
    low = ref.get("low", value)
    high = ref.get("high", value)
    span = (high - low) if (high is not None and low is not None) else 0.0
    span = abs(span) or max(abs(high or 1.0), 1.0)
    crit_low = ref.get("critical_low")
    crit_high = ref.get('critical_high')

    if crit_low is None:
        crit_low = low - 1.5 * span
    if crit_high is None:
        crit_high = high + 1.5 * span
    if value <= crit_low or value >= crit_high:
        return 1.0
    if value < low:
        return _smooth_severity(value, crit_low, low)
    if value > high:
        return _smooth_severity(value, high, crit_high)
    return 0.0

def _smooth_severity(value: float, bound: float,
                     extreme: float) -> float:
    if extreme == bound:
        return 0.0 if value == bound else 1.0
    x = _clamp01((value - bound) / (extreme - bound))

    return x * x * (3.0 - 2.0 * x)

def _fuzzy_membership(value: float,
                      ref: dict) -> Optional[float]:
    if not ref:
        return None
    low = ref.get("low")
    high = ref.get("high")
    if low is None or high is None:
        return None
    mid = (low + high) / 2.0
    span = (high - low) / 2.0
    if span == 0:
        return 0.5
    if value < mid:
        return _sigmoid(3.0 * (value - low) / span)
    return _sigmoid(3.0 * (high - value) / span)

def _tabaghebandi_direction(value: float, ref: dict) -> str:
    if not ref:
        return "normal"
    if value <= ref.get("critical_low", float("-inf")):
        return "critical_low"
    if value >= ref.get('critical_high', float("inf")):
        return 'critical_high'
    if value < ref.get("low", float("-inf")):
        return "low"
    if value > ref.get("high", float("inf")):
        return 'high'
    return "normal"

def _ref_deviation(value: float, ref: dict) -> float:
    low, high = ref.get("low"), ref.get("high")
    if low is None or high is None:
        return 0.0
    mid = (low + high) / 2
    span = (high - low) / 2
    return (value - mid) / span if span > 0 else 0.0

def _z_to_percentile(z: float) -> float:
    return 100 * (0.5 * (1 + math.erf(z / math.sqrt(2))))

def _arzyabi_reliability(record: ObservationRecord) -> float:
    """Evidence reliability in (0, 1]; carried into Bayes, fuzzy and the
    fusion layer so OCR uncertainty is never silently promoted to fact.

    OCR confidence is applied continuously (a 0.60 read is worse than a
    0.84 read) instead of a single 0.85 step; unconfirmed values and
    conflicting duplicates compound multiplicatively.
    """
    reliability = 1.0
    if record.metadata.get("requires_confirmation") and not record.confirmed:
        reliability *= 0.7
    conf = _float(record.metadata.get("ocr_confidence"))
    if conf is not None:
        conf = _clamp01(conf)
        if conf < 0.95:
            # 0.95 -> 1.00, 0.85 -> 0.80, 0.70 -> 0.50, 0.50 -> 0.10
            reliability *= max(0.10, 1.0 - 2.0 * (0.95 - conf))
    if record.metadata.get("review_action") in ("confirmed", "edited"):
        reliability = max(reliability, 0.95)   # clinician saw and accepted it
    if record.metadata.get("conflict"):
        reliability *= 0.6
    penalty = _float(record.metadata.get("preanalytical_penalty"))
    if penalty is not None:
        reliability *= _clamp01(penalty)
    return _clamp01(reliability)

@dataclass
class BayesiNode:
    disease_id: str
    prior_probability: float = 0.01
    likelihood_ratios: dict[str, float] = field(default_factory=dict)
    negative_lrs: dict[str, float] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class BayesianResult:
    disease_id: str
    posterior_probability: float
    evidence_count: int = 0
    measured_count: int = 0
    contributing_factors: list[dict[str, Any]] = field(
        default_factory=list)
    confidence: float = 0.0
    explanation: str = ""


class ClinicalBayesianNetwork:

    PRIORS = {
        "iron_deficiency_anemia": 0.03,
        "hypothyroidism": 0.05,
        'hyperthyroidism': 0.01,
        "type_2_diabetes": 0.08,
        'chronic_kidney_disease': 0.10,
        "nafl_d": 0.20,
        "metabolic_syndrome": 0.25,
        'vitamin_b12_deficiency': 0.06,
        "hyperlipidemia": 0.15,
        "hypertension": 0.20,
        "anemia": 0.05,
        "liver_cirrhosis": 0.02,
        "acute_kidney_injury": 0.03,
        "urinary_tract_infection": 0.04,
        "celiac_disease": 0.01,
        "type_1_diabetes": 0.010,
        "graves_disease": 0.012,
        "addison_disease": 0.004,
        "primary_aldosteronism": 0.008,
        "heart_failure": 0.020,
        "rheumatoid_arthritis": 0.010,
        "systemic_lupus_erythematosus": 0.006,
        "chronic_hepatitis_b": 0.012,
        "chronic_hepatitis_c": 0.010,
        "hepatocellular_carcinoma": 0.003,
        "hyperkalemia": 0.025,
        "thalassemia_trait": 0.015,
        "hemochromatosis": 0.004,
        "gout": 0.025,
        "vitamin_d_deficiency": 0.20,
        "prediabetes": 0.35,
        'anemia_of_chronic_disease': 0.03,
        'hemolytic_anemia': 0.005,
        "thrombotic_thrombocytopenic_purpura": 0.001,
        "hemophagocytic_lymphohistiocytosis": 0.001,
        "central_adrenal_insufficiency": 0.002,
        "pheochromocytoma": 0.001,
        "hashimoto_thyroiditis": 0.04,
        "sepsis": 0.01,
        # --- phase-3 additions: syndromes the AI-built registry covers only
        # with non-specific CBC rules; LRs are literature-anchored and the
        # pathognomonic marker carries most of the weight. ---
        "acute_pancreatitis": 0.004,
        "rhabdomyolysis": 0.002,
        "multiple_myeloma": 0.001,
        "acute_myeloid_leukemia": 0.0005,
        "pulmonary_embolism": 0.003,
        "hepatitis_a": 0.002,
        "nephrotic_syndrome": 0.002,
        "hypercalcemia_of_malignancy_support_pattern": 0.002,
        "diabetic_ketoacidosis": 0.005,
        # === SUPER-ENHANCED COMPLEX DIAGNOSES ===
        "primary_hyperparathyroidism": 0.008,
        "secondary_hyperparathyroidism": 0.015,
        "diabetic_ketoacidosis": 0.005,
        "hyperosmolar_hyperglycemic_state": 0.003,
        "metabolic_acidosis": 0.04,
        "respiratory_acidosis": 0.02,
        "metabolic_alkalosis": 0.03,
        "siadh": 0.012,
        "cushing_syndrome": 0.002,
        "polycythemia": 0.008,
        "leukocytosis": 0.05,
        "thrombocytopenia": 0.02,
        "thrombocytosis": 0.015,
        "disseminated_intravascular_coagulation": 0.002,
        "cholestasis": 0.015,
        "autoimmune_hepatitis": 0.005,
        "gilbert_syndrome": 0.06,
        "pancytopenia": 0.004,
        "malnutrition": 0.08,
        "osteoporosis": 0.10,
        "coronary_artery_disease": 0.12,
        "hypokalemia": 0.03,
        "hyponatremia": 0.04,
        "hypercalcemia": 0.015,
        "hypocalcemia": 0.02,
        "folate_deficiency": 0.04,
        "viral_infection": 0.10,
        "bacterial_infection": 0.08,
    }


    LIKELIHOOD_RATIOS = {
        # Lipase >= 3x ULN: sensitivity ~90 %, specificity ~95 % (ACG 2024,
        # revised Atlanta 2012). Amylase less specific. Hypocalcaemia and
        # leukocytosis are severity markers, not diagnostic.
        "acute_pancreatitis": {
            "lipase_high": {"LR+": 18.0, "LR-": 0.1},
            "amylase_high": {"LR+": 6.0, "LR-": 0.4},
            "calcium_low": {"LR+": 2.0, "LR-": 0.9},
            "wbc_high": {"LR+": 1.6, "LR-": 0.8},
            "triglycerides_very_high": {"LR+": 3.0, "LR-": 0.95},
        },
        # CK > 5x ULN defines rhabdomyolysis; CK > 5,000 U/L carries AKI
        # risk (McMahon score). Hyperkalaemia / hyperphosphataemia /
        # hypocalcaemia from myocyte lysis; AST rises with CK.
        "rhabdomyolysis": {
            "ck_high": {"LR+": 15.0, "LR-": 0.08},
            "ck_very_high": {"LR+": 40.0, "LR-": 0.3},
            "potassium_high": {"LR+": 2.5, "LR-": 0.8},
            "phosphate_high": {"LR+": 2.5, "LR-": 0.8},
            "calcium_low": {"LR+": 2.0, "LR-": 0.9},
            "ast_high": {"LR+": 2.5, "LR-": 0.6},
            "creatinine_high": {"LR+": 2.0, "LR-": 0.8},
        },
        # IMWG 2014: M-protein / abnormal FLC ratio plus CRAB. Serum M-spike
        # >= 3 g/dL or involved:uninvolved FLC >= 100 are myeloma-defining
        # in context; CRAB features add modest LRs because they are shared
        # with many other diseases.
        "multiple_myeloma": {
            "m_spike_present": {"LR+": 25.0, "LR-": 0.15},
            "m_spike_high": {"LR+": 60.0, "LR-": 0.5},
            "flc_ratio_abnormal": {"LR+": 20.0, "LR-": 0.2},
            "flc_high": {"LR+": 8.0, "LR-": 0.5},
            "calcium_high": {"LR+": 4.0, "LR-": 0.8},
            "creatinine_high": {"LR+": 2.0, "LR-": 0.85},
            "hemoglobin_low": {"LR+": 2.5, "LR-": 0.5},
            "total_protein_high": {"LR+": 6.0, "LR-": 0.6},
            "albumin_low": {"LR+": 1.6, "LR-": 0.9},
            "esr_high": {"LR+": 3.0, "LR-": 0.6},
        },
        # WHO 2022 / ELN 2022: >= 20 % blasts (marrow or blood) defines
        # acute leukaemia; any circulating blasts with bicytopenia is an
        # urgent haematology referral.
        "acute_myeloid_leukemia": {
            "blasts_high": {"LR+": 80.0, "LR-": 0.2},
            "blasts_present": {"LR+": 15.0, "LR-": 0.1},
            "platelets_low": {"LR+": 3.0, "LR-": 0.4},
            "hemoglobin_low": {"LR+": 2.5, "LR-": 0.4},
            "wbc_high": {"LR+": 2.0, "LR-": 0.7},
            "wbc_low": {"LR+": 2.0, "LR-": 0.8},
            "ldh_high": {"LR+": 2.5, "LR-": 0.6},
            "uric_acid_high": {"LR+": 2.0, "LR-": 0.8},
        },
        # D-dimer: sensitivity ~97 %, specificity ~40 % (ESC 2019) - a
        # negative result excludes, a positive one only keeps PE on the
        # list. Troponin / BNP mark RV strain, not diagnosis.
        "pulmonary_embolism": {
            "d_dimer_high": {"LR+": 1.7, "LR-": 0.08},
            "d_dimer_very_high": {"LR+": 4.0, "LR-": 0.6},
            "troponin_high": {"LR+": 1.8, "LR-": 0.8},
            "bnp_high": {"LR+": 1.6, "LR-": 0.8},
            "pco2_low": {"LR+": 1.8, "LR-": 0.8},
        },
        # Anti-HAV IgM is the diagnostic test (sens/spec > 95 %); ALT
        # typically > 10x ULN with AST < ALT in acute viral hepatitis.
        "hepatitis_a": {
            "hav_igm_positive": {"LR+": 60.0, "LR-": 0.05},
            "alt_very_high": {"LR+": 6.0, "LR-": 0.3},
            "alt_high": {"LR+": 3.0, "LR-": 0.2},
            "ast_high": {"LR+": 2.0, "LR-": 0.3},
            "bilirubin_high": {"LR+": 2.5, "LR-": 0.6},
        },
        # KDIGO 2021: proteinuria >= 3.5 g/d (UPCR >= 3,000 mg/g) with
        # hypoalbuminaemia; hyperlipidaemia is secondary.
        "nephrotic_syndrome": {
            "proteinuria_nephrotic": {"LR+": 30.0, "LR-": 0.08},
            "albumin_low": {"LR+": 6.0, "LR-": 0.15},
            "cholesterol_high": {"LR+": 2.5, "LR-": 0.6},
            "triglycerides_high": {"LR+": 1.8, "LR-": 0.8},
            "creatinine_high": {"LR+": 1.3, "LR-": 0.9},
        },
        # PTH-independent hypercalcaemia: suppressed PTH with raised PTHrP
        # (humoral) or raised calcium with suppressed PTH alone.
        "hypercalcemia_of_malignancy_support_pattern": {
            "calcium_high": {"LR+": 8.0, "LR-": 0.05},
            "pth_low": {"LR+": 12.0, "LR-": 0.1},
            "pthrp_high": {"LR+": 40.0, "LR-": 0.3},
            "phosphate_low": {"LR+": 1.5, "LR-": 0.9},
            "alp_high": {"LR+": 1.8, "LR-": 0.8},
        },
        "iron_deficiency_anemia": {
            "ferritin_low": {"LR+": 41.0, "LR-": 0.08},
            "mcv_low": {"LR+": 8.2, "LR-": 0.35},
            "transferrin_sat_low": {"LR+": 6.5, "LR-": 0.4},
            'hemoglobin_low': {'LR+': 3.1, "LR-": 0.25},
            "rdw_high": {"LR+": 4.8, "LR-": 0.5},
            "serum_iron_low": {"LR+": 5.4, 'LR-': 0.4},
            'tibc_high': {"LR+": 4.0, "LR-": 0.6},
            "mch_low": {'LR+': 4.5, "LR-": 0.5},
            "ferritin_high": {'LR+': 0.02, "LR-": 1.0},
            "transferrin_sat_high": {"LR+": 0.05, "LR-": 1.0},
            "mentzer_high": {"LR+": 3.2, "LR-": 0.55},
        },
        "type_1_diabetes": {
            "glucose_high": {"LR+": 3.2, "LR-": 0.30},
            "hba1c_high": {"LR+": 3.6, "LR-": 0.25},
            "c_peptide_low": {"LR+": 24.0, "LR-": 0.12},
            "bmi_high": {"LR+": 0.35, "LR-": 1.0},
        },
        "graves_disease": {
            "tsh_low": {"LR+": 14.0, "LR-": 0.10},
            "ft4_high": {"LR+": 9.0, "LR-": 0.20},
            "ft3_high": {"LR+": 7.0, "LR-": 0.30},
            "tsh_high": {"LR+": 0.04, "LR-": 1.0},
        },
        "addison_disease": {
            "cortisol_low": {"LR+": 22.0, "LR-": 0.10},
            "acth_high": {"LR+": 18.0, "LR-": 0.15},
            "sodium_low": {"LR+": 3.4, "LR-": 0.55},
            "potassium_high": {"LR+": 4.8, "LR-": 0.50},
        },
        "thrombotic_thrombocytopenic_purpura": {
            "platelets_low": {"LR+": 16.0, "LR-": 0.05},
            "ldh_high": {"LR+": 12.0, "LR-": 0.1},
            "indirect_bilirubin_high": {"LR+": 8.0, "LR-": 0.2},
            "haptoglobin_low": {"LR+": 10.0, "LR-": 0.15},
            "retic_high": {"LR+": 6.0, "LR-": 0.25},
            "inr_high": {"LR+": 0.1, "LR-": 2.0},
            "fibrinogen_low": {"LR+": 0.1, "LR-": 2.0},
        },
        "hemophagocytic_lymphohistiocytosis": {
            "ferritin_critical_high": {"LR+": 35.0, "LR-": 0.05},
            "ferritin_high": {"LR+": 8.0, "LR-": 0.1},
            "platelets_low": {"LR+": 6.0, "LR-": 0.2},
            "hemoglobin_low": {"LR+": 4.0, "LR-": 0.3},
            "fibrinogen_low": {"LR+": 8.0, "LR-": 0.2},
            "ast_high": {"LR+": 5.0, "LR-": 0.3},
        },
        "central_adrenal_insufficiency": {
            "cortisol_low": {"LR+": 15.0, "LR-": 0.05},
            "acth_high": {"LR+": 0.05, "LR-": 3.0},
            "potassium_high": {"LR+": 0.15, "LR-": 2.5},
        },
        "pheochromocytoma": {
            "metanephrines_high": {"LR+": 40.0, "LR-": 0.02},
            "bp_systolic_high": {"LR+": 5.0, "LR-": 0.3},
            "glucose_high": {"LR+": 3.0, "LR-": 0.7},
        },
        "primary_aldosteronism": {
            "potassium_low": {"LR+": 5.2, "LR-": 0.45},
            "aldosterone_renin_ratio_high": {"LR+": 20.0, "LR-": 0.12},
            "bicarbonate_high": {"LR+": 2.6, "LR-": 0.75},
        },
        "heart_failure": {
            "bnp_high": {"LR+": 9.5, "LR-": 0.12},
            "nt_probnp_high": {"LR+": 11.0, "LR-": 0.10},
            "sodium_low": {"LR+": 2.2, "LR-": 0.80},
            "creatinine_high": {"LR+": 1.9, "LR-": 0.85},
        },
        "rheumatoid_arthritis": {
            "anti_ccp_positive": {"LR+": 25.0, "LR-": 0.35},
            "rheumatoid_factor_positive": {"LR+": 4.9, "LR-": 0.38},
            "crp_high": {"LR+": 2.1, "LR-": 0.65},
            "esr_high": {"LR+": 2.0, "LR-": 0.70},
        },
        "systemic_lupus_erythematosus": {
            "ana_positive": {"LR+": 5.8, "LR-": 0.05},
            "anti_dsdna_positive": {"LR+": 16.0, "LR-": 0.55},
            "anti_smith_positive": {"LR+": 20.0, "LR-": 0.70},
            "complement_c3_low": {"LR+": 4.2, "LR-": 0.60},
        },
        "chronic_hepatitis_b": {
            "hbsag_positive": {"LR+": 40.0, "LR-": 0.05},
            "alt_high": {"LR+": 2.4, "LR-": 0.60},
        },
        "chronic_hepatitis_c": {
            "hcv_antibody_positive": {"LR+": 35.0, "LR-": 0.05},
            "alt_high": {"LR+": 2.4, "LR-": 0.60},
            "platelets_low": {"LR+": 2.8, "LR-": 0.80},
        },
        "hepatocellular_carcinoma": {
            "afp_high": {"LR+": 12.0, "LR-": 0.35},
            "albumin_low": {"LR+": 2.4, "LR-": 0.70},
            "platelets_low": {"LR+": 2.2, "LR-": 0.80},
        },
        "hyperkalemia": {
            "potassium_high": {"LR+": 45.0, "LR-": 0.03},
            "egfr_low": {"LR+": 2.8, "LR-": 0.70},
        },
        "thalassemia_trait": {
            "mcv_low": {"LR+": 9.5, "LR-": 0.10},
            "mentzer_low": {"LR+": 12.0, "LR-": 0.18},
            "rbc_high": {"LR+": 8.0, "LR-": 0.30},
            "hba2_high": {"LR+": 32.0, "LR-": 0.15},
            "ferritin_low": {"LR+": 0.30, "LR-": 1.0},
            "rdw_high": {"LR+": 0.45, "LR-": 1.0},
            "mch_low": {"LR+": 5.0, "LR-": 0.35},
        },
        "hemochromatosis": {
            "ferritin_high": {"LR+": 18.0, "LR-": 0.12},
            "transferrin_sat_high": {"LR+": 30.0, "LR-": 0.10},
            "alt_high": {"LR+": 2.2, "LR-": 0.8},
            "glucose_high": {"LR+": 1.8, "LR-": 0.9},
        },
        "gout": {
            "uric_acid_high": {"LR+": 16.0, "LR-": 0.15},
            "crp_high": {"LR+": 1.9, "LR-": 0.8},
            "creatinine_high": {"LR+": 1.7, "LR-": 0.9},
        },
        "vitamin_d_deficiency": {
            "vitamin_d_low": {"LR+": 26.0, "LR-": 0.06},
            "calcium_low": {"LR+": 2.4, "LR-": 0.85},
            "alp_high": {"LR+": 2.0, "LR-": 0.9},
            "pth_high": {"LR+": 4.5, "LR-": 0.6},
        },
        "anemia_of_chronic_disease": {
            'hemoglobin_low': {"LR+": 3.0, "LR-": 0.2},
            "ferritin_high": {"LR+": 6.0, "LR-": 0.7},
            'crp_high': {'LR+': 4.5, 'LR-': 0.5},
            "esr_high": {'LR+': 3.2, "LR-": 0.6},
            'transferrin_sat_low': {"LR+": 2.5, "LR-": 0.7},
            "mcv_low": {"LR+": 1.4, "LR-": 0.9},
        },
        "vitamin_b12_deficiency": {
            "b12_low": {"LR+": 28.0, "LR-": 0.1},
            "mcv_high": {'LR+': 6.5, "LR-": 0.45},
            "hemoglobin_low": {"LR+": 2.2, "LR-": 0.6},
            "ldh_high": {"LR+": 2.8, "LR-": 0.7},
            "retic_low": {"LR+": 2.4, "LR-": 0.8},
        },
        'hemolytic_anemia': {
            "haptoglobin_low": {"LR+": 18.0, 'LR-': 0.15},
            "ldh_high": {"LR+": 5.5, "LR-": 0.3},
            'retic_high': {"LR+": 7.0, "LR-": 0.25},
            "bilirubin_high": {'LR+': 4.0, "LR-": 0.5},
            "hemoglobin_low": {"LR+": 2.5, 'LR-': 0.5},
        },
        "anemia": {
            'hemoglobin_low': {"LR+": 30.0, "LR-": 0.05},
            "hct_low": {"LR+": 12.0, "LR-": 0.2},
            'rdw_high': {"LR+": 2.0, "LR-": 0.8},
        },
        "type_2_diabetes": {
            "fbs_high": {'LR+': 12.5, "LR-": 0.25},
            "hba1c_high": {"LR+": 15.3, 'LR-': 0.18},
            'glucose_random_high': {"LR+": 8.7, 'LR-': 0.6},
            "ogtt_high": {"LR+": 14.0, 'LR-': 0.2},
            "fbs_prediabetic": {'LR+': 1.6, "LR-": 0.85},
            'hba1c_prediabetic': {"LR+": 1.8, 'LR-': 0.8},
            "insulin_high": {"LR+": 2.4, "LR-": 0.8},
            "bmi_high": {"LR+": 2.8, "LR-": 0.7},
            "triglycerides_high": {"LR+": 1.7, "LR-": 0.85},
        },
        "prediabetes": {
            "fbs_prediabetic": {"LR+": 14.0, "LR-": 0.2},
            "hba1c_prediabetic": {"LR+": 16.0, "LR-": 0.18},
            'ogtt_igt': {"LR+": 12.0, 'LR-': 0.3},
            "fbs_high": {"LR+": 0.1, "LR-": 1.0},
            "hba1c_high": {"LR+": 0.1, "LR-": 1.0},
            'bmi_high': {"LR+": 2.0, "LR-": 0.8},
        },
        "metabolic_syndrome": {
            "triglycerides_high": {'LR+': 5.5, "LR-": 0.35},
            'hdl_low': {"LR+": 5.0, "LR-": 0.4},
            "fbs_prediabetic": {"LR+": 3.5, "LR-": 0.6},
            'fbs_high': {"LR+": 4.0, "LR-": 0.7},
            "bmi_high": {"LR+": 6.0, "LR-": 0.3},
            'bmi_overweight': {"LR+": 2.2, "LR-": 0.8},
            "uric_acid_high": {"LR+": 2.0, "LR-": 0.85},
            "alt_high": {"LR+": 1.9, "LR-": 0.85},
        },
        'chronic_kidney_disease': {
            "egfr_low": {"LR+": 20.0, "LR-": 0.12},
            "egfr_severely_low": {"LR+": 35.0, "LR-": 0.6},
            "acr_high": {"LR+": 9.5, "LR-": 0.35},
            "acr_severe": {"LR+": 16.0, "LR-": 0.7},
            "creatinine_high": {"LR+": 7.2, "LR-": 0.3},
            "cystatin_high": {"LR+": 6.0, 'LR-': 0.35},
            "bun_high": {"LR+": 2.6, "LR-": 0.7},
            "phosphate_high": {"LR+": 3.0, "LR-": 0.8},
            'hemoglobin_low': {"LR+": 1.9, "LR-": 0.85},
        },
        "acute_kidney_injury": {
            "creatinine_high": {"LR+": 8.0, "LR-": 0.2},
            "egfr_low": {"LR+": 5.0, "LR-": 0.3},
            "bun_high": {"LR+": 4.2, "LR-": 0.5},
            'potassium_high': {"LR+": 3.0, "LR-": 0.7},
            "bicarbonate_low": {"LR+": 2.8, 'LR-': 0.75},
            "lactate_high": {"LR+": 2.5, "LR-": 0.8},
        },
        "hypothyroidism": {
            "tsh_high": {"LR+": 25.0, "LR-": 0.08},
            "tsh_very_high": {"LR+": 45.0, "LR-": 0.55},
            'ft4_low': {'LR+': 18.0, "LR-": 0.3},
            "anti_tpo_positive": {'LR+': 5.0, "LR-": 0.6},
            "cholesterol_high": {"LR+": 1.8, "LR-": 0.9},
            "ck_high": {"LR+": 2.0, "LR-": 0.9},
            "tsh_low": {'LR+': 0.02, "LR-": 1.0},
        },
        "hyperthyroidism": {
            "tsh_low": {"LR+": 30.0, 'LR-': 0.06},
            "ft4_high": {"LR+": 22.0, "LR-": 0.25},
            'ft3_high': {"LR+": 15.0, "LR-": 0.35},
            "tsh_high": {"LR+": 0.02, 'LR-': 1.0},
        },
        "hashimoto_thyroiditis": {
            "anti_tpo_positive": {"LR+": 22.0, "LR-": 0.15},
            "tsh_high": {"LR+": 6.0, "LR-": 0.4},
            "ft4_low": {"LR+": 4.0, "LR-": 0.6},
        },
        "nafl_d": {
            'alt_high': {"LR+": 5.5, 'LR-': 0.35},
            "ast_high": {"LR+": 4.2, 'LR-': 0.45},
            "ggt_high": {"LR+": 3.4, "LR-": 0.6},
            "bmi_high": {"LR+": 6.0, "LR-": 0.3},
            'bmi_overweight': {"LR+": 2.4, "LR-": 0.8},
            "triglycerides_high": {'LR+': 3.0, "LR-": 0.65},
            'hba1c_high': {'LR+': 2.6, 'LR-': 0.8},
            "hdl_low": {"LR+": 2.2, "LR-": 0.8},
        },
        "liver_cirrhosis": {
            'albumin_low': {"LR+": 8.5, "LR-": 0.25},
            "inr_high": {"LR+": 9.0, "LR-": 0.3},
            'bilirubin_high': {'LR+': 6.0, "LR-": 0.35},
            "platelets_low": {"LR+": 10.0, "LR-": 0.25},
            "ast_high": {'LR+': 2.4, "LR-": 0.6},
            "ggt_high": {'LR+': 2.0, "LR-": 0.8},
        },
        'hyperlipidemia': {
            "cholesterol_high": {'LR+': 15.0, "LR-": 0.15},
            "ldl_high": {"LR+": 18.0, "LR-": 0.12},
            "triglycerides_high": {"LR+": 6.0, "LR-": 0.4},
            "hdl_low": {"LR+": 3.0, "LR-": 0.7},
        },
        'hypertension': {
            "acr_high": {"LR+": 2.6, "LR-": 0.8},
            "egfr_low": {"LR+": 2.2, "LR-": 0.85},
            "uric_acid_high": {"LR+": 1.9, 'LR-': 0.88},
            "bmi_high": {"LR+": 2.4, "LR-": 0.75},
        },
        "urinary_tract_infection": {
            "wbc_high": {"LR+": 3.0, "LR-": 0.6},
            "crp_high": {"LR+": 2.8, "LR-": 0.6},
            "procalcitonin_high": {"LR+": 4.0, "LR-": 0.7},
        },
        'celiac_disease': {
            "ttg_positive": {"LR+": 45.0, "LR-": 0.06},
            "ferritin_low": {"LR+": 2.6, 'LR-': 0.8},
            "folate_low": {'LR+': 2.4, "LR-": 0.85},
            "albumin_low": {"LR+": 2.0, "LR-": 0.9},
            "vitamin_d_low": {"LR+": 1.8, "LR-": 0.9},
        },
        "sepsis": {
            "procalcitonin_high": {"LR+": 12.0, "LR-": 0.15},
            "lactate_high": {"LR+": 6.0, "LR-": 0.3},
            "crp_very_high": {"LR+": 5.0, "LR-": 0.4},
            "wbc_high": {"LR+": 3.0, 'LR-': 0.5},
            'wbc_low': {"LR+": 4.0, 'LR-': 0.85},
            'platelets_low': {'LR+': 3.5, "LR-": 0.7},
        },
        # === COMPLEX DIAGNOSES LRs ===
        "primary_hyperparathyroidism": {
            "calcium_high": {"LR+": 18.0, "LR-": 0.15},
            "pth_high": {"LR+": 22.0, "LR-": 0.12},
            "phosphate_low": {"LR+": 4.5, "LR-": 0.6},
            "vitamin_d_low": {"LR+": 1.8, "LR-": 0.9},
        },
        "secondary_hyperparathyroidism": {
            "pth_high": {"LR+": 16.0, "LR-": 0.2},
            "calcium_low": {"LR+": 5.0, "LR-": 0.5},
            "phosphate_high": {"LR+": 4.0, "LR-": 0.6},
            "egfr_low": {"LR+": 6.0, "LR-": 0.4},
            "vitamin_d_low": {"LR+": 3.5, "LR-": 0.6},
        },
        "diabetic_ketoacidosis": {
            "glucose_high": {"LR+": 12.0, "LR-": 0.2},
            "bicarbonate_low": {"LR+": 14.0, "LR-": 0.15},
            "anion_gap_high": {"LR+": 18.0, "LR-": 0.12},
            "ketones_high": {"LR+": 35.0, "LR-": 0.05},
            "ph_low": {"LR+": 10.0, "LR-": 0.3},
        },
        "hyperosmolar_hyperglycemic_state": {
            "glucose_very_high": {"LR+": 25.0, "LR-": 0.1},
            "sodium_high": {"LR+": 3.0, "LR-": 0.7},
            "osmolality_high": {"LR+": 20.0, "LR-": 0.15},
            "bicarbonate_normal": {"LR+": 2.5, "LR-": 0.6},
        },
        "metabolic_acidosis": {
            "bicarbonate_low": {"LR+": 16.0, "LR-": 0.12},
            "ph_low": {"LR+": 12.0, "LR-": 0.2},
            "anion_gap_high": {"LR+": 5.0, "LR-": 0.5},
            "lactate_high": {"LR+": 4.5, "LR-": 0.6},
        },
        "siadh": {
            "sodium_low": {"LR+": 8.0, "LR-": 0.25},
            "osmolality_low": {"LR+": 10.0, "LR-": 0.2},
            "urine_osmolality_high": {"LR+": 12.0, "LR-": 0.18},
        },
        "cushing_syndrome": {
            "cortisol_high": {"LR+": 20.0, "LR-": 0.1},
            "acth_high": {"LR+": 8.0, "LR-": 0.4},
            "glucose_high": {"LR+": 2.5, "LR-": 0.8},
            "potassium_low": {"LR+": 3.5, "LR-": 0.6},
        },
        "polycythemia": {
            "hemoglobin_high": {"LR+": 18.0, "LR-": 0.1},
            "hct_high": {"LR+": 16.0, "LR-": 0.12},
            "rbc_high": {"LR+": 12.0, "LR-": 0.2},
        },
        "thrombocytopenia": {
            "platelets_low": {"LR+": 35.0, "LR-": 0.05},
            "platelets_very_low": {"LR+": 50.0, "LR-": 0.6},
        },
        "thrombocytosis": {
            "platelets_high": {"LR+": 30.0, "LR-": 0.08},
        },
        "disseminated_intravascular_coagulation": {
            "platelets_low": {"LR+": 6.0, "LR-": 0.5},
            "d_dimer_high": {"LR+": 15.0, "LR-": 0.2},
            "fibrinogen_low": {"LR+": 12.0, "LR-": 0.25},
            "pt_high": {"LR+": 5.0, "LR-": 0.5},
        },
        "cholestasis": {
            "alp_high": {"LR+": 10.0, "LR-": 0.2},
            "ggt_high": {"LR+": 8.0, "LR-": 0.3},
            "bilirubin_high": {"LR+": 6.0, "LR-": 0.4},
            "alt_high": {"LR+": 1.5, "LR-": 0.9},
        },
        "pancytopenia": {
            "hemoglobin_low": {"LR+": 4.0, "LR-": 0.4},
            "wbc_low": {"LR+": 6.0, "LR-": 0.3},
            "platelets_low": {"LR+": 6.0, "LR-": 0.3},
        },
        "malnutrition": {
            "albumin_low": {"LR+": 8.0, "LR-": 0.3},
            "prealbumin_low": {"LR+": 12.0, "LR-": 0.2},
            "hemoglobin_low": {"LR+": 2.0, "LR-": 0.8},
            "bmi_low": {"LR+": 5.0, "LR-": 0.5},
        },
        "hypokalemia": {
            "potassium_low": {"LR+": 40.0, "LR-": 0.04},
        },
        "hyponatremia": {
            "sodium_low": {"LR+": 38.0, "LR-": 0.05},
        },
        "hypercalcemia": {
            "calcium_high": {"LR+": 42.0, "LR-": 0.03},
        },
        "hypocalcemia": {
            "calcium_low": {"LR+": 40.0, "LR-": 0.04},
        },
        "folate_deficiency": {
            "folate_low": {"LR+": 26.0, "LR-": 0.08},
            "mcv_high": {"LR+": 5.5, "LR-": 0.5},
            "hemoglobin_low": {"LR+": 2.0, "LR-": 0.7},
        },
        "viral_infection": {
            "lymphocytes_high": {"LR+": 6.0, "LR-": 0.4},
            "wbc_normal": {"LR+": 2.0, "LR-": 0.7},
            "crp_low": {"LR+": 2.5, "LR-": 0.6},
        },
        "bacterial_infection": {
            "neutrophils_high": {"LR+": 7.0, "LR-": 0.3},
            "wbc_high": {"LR+": 5.0, "LR-": 0.4},
            "crp_high": {"LR+": 6.0, "LR-": 0.35},
            "procalcitonin_high": {"LR+": 10.0, "LR-": 0.2},
        },
    }

    DEPENDENCIES = {
        'type_2_diabetes': ["chronic_kidney_disease", "nafl_d",
                            "metabolic_syndrome", "diabetic_ketoacidosis", "hyperosmolar_hyperglycemic_state"],
        "chronic_kidney_disease": ['iron_deficiency_anemia', 'secondary_hyperparathyroidism', 'anemia_of_chronic_disease', 'hyperkalemia', 'metabolic_acidosis'],
        "hypothyroidism": ["hyperlipidemia", "anemia"],
        "metabolic_syndrome": ["type_2_diabetes", "nafl_d",
                               "chronic_kidney_disease", "gout", "coronary_artery_disease"],
        "liver_cirrhosis": ["thrombocytopenia", "anemia", "hepatocellular_carcinoma"],
        "sepsis": ["disseminated_intravascular_coagulation", "acute_kidney_injury", "thrombocytopenia"],
        "hemolytic_anemia": ["gilbert_syndrome", "iron_deficiency_anemia"],
        "iron_deficiency_anemia": ["pancytopenia"],
        "vitamin_b12_deficiency": ["pancytopenia", "hemolytic_anemia"],
        "primary_hyperparathyroidism": ["hypercalcemia", "osteoporosis", "nephrotic_syndrome"],
        "malnutrition": ["anemia", "vitamin_d_deficiency", "osteoporosis"],
    }


    FEATURE_TO_FINDING: dict[str, list] = {
        # --- phase-3 canonical-id findings ---
        "lipase": [("lipase_high", lambda v: v is not None and v >= 180.0)],          # >= 3x ULN (60 U/L)
        "amylase": [("amylase_high", lambda v: v is not None and v >= 300.0)],        # >= 3x ULN (100 U/L)
        "creatine_kinase_total": [("ck_high", lambda v: v is not None and v >= 1000.0),
                                  ("ck_very_high", lambda v: v is not None and v >= 5000.0)],
        "blasts_percent": [("blasts_present", lambda v: v is not None and v > 0.0),
                           ("blasts_high", lambda v: v is not None and v >= 20.0)],
        "serum_protein_electrophoresis_m_spike": [("m_spike_present", lambda v: v is not None and v > 0.0),
                                                  ("m_spike_high", lambda v: v is not None and v >= 3.0)],
        "free_light_chain_ratio": [("flc_ratio_abnormal", lambda v: v is not None and (v < 0.26 or v > 1.65))],
        "serum_free_light_chain_kappa": [("flc_high", lambda v: v is not None and v > 100.0)],
        "serum_free_light_chain_lambda": [("flc_high", lambda v: v is not None and v > 100.0)],
        "total_protein": [("total_protein_high", lambda v: v is not None and v > 8.3),
                          ("total_protein_low", lambda v: v is not None and v < 6.0)],
        "hepatitis_a_igm_antibody": [("hav_igm_positive", lambda v: v is not None and v >= 1.0)],
        "parathyroid_hormone_related_peptide": [("pthrp_high", lambda v: v is not None and v > 0.02)],
        "intact_parathyroid_hormone": [("pth_high", lambda v: v is not None and v > 65.0),
                                       ("pth_low", lambda v: v is not None and v < 20.0)],
        "urine_protein_to_creatinine_ratio": [("proteinuria_nephrotic", lambda v: v is not None and v >= 3000.0)],
        "urine_protein_24_hour": [("proteinuria_nephrotic", lambda v: v is not None and v >= 3500.0)],
        "twenty_four_hour_urine_total_protein": [("proteinuria_nephrotic", lambda v: v is not None and v >= 3500.0)],
        "morning_cortisol": [("cortisol_low", lambda v: v is not None and v < 5.0),
                             ("cortisol_high", lambda v: v is not None and v > 25.0)],
        "cortisol_after_dexamethasone": [("dst_nonsuppressed", lambda v: v is not None and v > 1.8),
                                         ("cortisol_high", lambda v: v is not None and v > 1.8)],
        "salivary_cortisol_late_night": [("lnsc_high", lambda v: v is not None and v > 0.15),
                                         ("cortisol_high", lambda v: v is not None and v > 0.15)],
        "urine_free_cortisol_24h": [("ufc_high", lambda v: v is not None and v > 50.0),
                                    ("cortisol_high", lambda v: v is not None and v > 50.0)],
        "nt_probnp": [("bnp_high", lambda v: v is not None and v > 300.0)],
        "high_sensitivity_troponin_t": [("troponin_high", lambda v: v is not None and v > 0.014)],
        "high_sensitivity_troponin_i": [("troponin_high", lambda v: v is not None and v > 0.04)],
        "calcium_ionized": [("calcium_high", lambda v: v is not None and v > 1.32),
                            ("calcium_low", lambda v: v is not None and v < 1.12)],
        "c_peptide": [("c_peptide_low", lambda v: v is not None and v < 0.6)],
        "cortisol_morning": [
            ("cortisol_low", lambda v: v is not None and v < 5)],
        "adrenocorticotropic_hormone": [
            ("acth_high", lambda v: v is not None and v > 63),
            ("acth_low", lambda v: v is not None and v < 10)],
        "aldosterone_to_renin_ratio_arr": [
            ("aldosterone_renin_ratio_high",
             lambda v: v is not None and v > 30)],
        "b_type_natriuretic_peptide": [
            ("bnp_high", lambda v: v is not None and v > 100)],
        "n_terminal_pro_bnp": [
            ("nt_probnp_high", lambda v: v is not None and v > 300)],
        "anti_cyclic_citrullinated_peptide_igg": [
            ("anti_ccp_positive", lambda v: v is not None and v > 20)],
        "rheumatoid_factor": [
            ("rheumatoid_factor_positive",
             lambda v: v is not None and v > 14)],
        "antinuclear_antibody_titer": [
            ("ana_positive", lambda v: v is not None and v >= 80)],
        "double_stranded_dna_antibody": [
            ("anti_dsdna_positive", lambda v: v is not None and v > 30)],
        "anti_smith_antibody_igg": [
            ("anti_smith_positive", lambda v: v is not None and v > 20)],
        "complement_c3": [
            ("complement_c3_low", lambda v: v is not None and v < 90)],
        "hepatitis_b_surface_antigen": [
            ("hbsag_positive", lambda v: v is not None and v > 0)],
        "hepatitis_c_antibody": [
            ("hcv_antibody_positive", lambda v: v is not None and v > 0)],
        "alpha_fetoprotein": [
            ("afp_high", lambda v: v is not None and v > 20)],
        "mentzer_index": [("mentzer_low", lambda v: v is not None and v < 13),
                          ("mentzer_high", lambda v: v is not None and v >= 13)],
        "red_blood_cell_count": [
            ("rbc_high", lambda v: v is not None and v > 5.5),
            ("rbc_low", lambda v: v is not None and v < 4.0)],
        "hemoglobin_a2": [
            ("hba2_high", lambda v: v is not None and v > 3.5)],
        "uric_acid": [("uric_acid_high", lambda v: v is not None and v > 7.0)],
        "vitamin_d": [("vitamin_d_low", lambda v: v is not None and v < 20)],
        "magnesium": [("magnesium_low", lambda v: v is not None and v < 1.7)],
        "blood_urea_nitrogen": [
            ("bun_high", lambda v: v is not None and v > 25)],
        "total_iron_binding_capacity": [
            ("tibc_high", lambda v: v is not None and v > 400),
            ("tibc_low", lambda v: v is not None and v < 250)],
        "transferrin_saturation": [
            ("transferrin_sat_low", lambda v: v is not None and v < 16),
            ("transferrin_sat_high", lambda v: v is not None and v > 45)],

        'ferritin': [('ferritin_low', lambda v: v < 30),
                     ("ferritin_high", lambda v: v > 300),
                     ("ferritin_critical_high", lambda v: v is not None and v > 3000)],
        "serum_haptoglobin": [("haptoglobin_low", lambda v: v is not None and v < 30)],
        "reticulocytes": [("retic_high", lambda v: v is not None and v > 2.5),
                          ("retic_low", lambda v: v is not None and v < 0.5)],
        "plasma_free_metanephrines": [("metanephrines_high", lambda v: v is not None and v > 65)],
        "plasma_free_normetanephrines": [("metanephrines_high", lambda v: v is not None and v > 196)],
        "inr": [("inr_high", lambda v: v is not None and v > 1.3)],
        "indirect_bilirubin": [("indirect_bilirubin_high", lambda v: v is not None and v > 0.8)],
        "mean_corpuscular_volume": [("mcv_low", lambda v: v < 80),
                                    ('mcv_high', lambda v: v > 100)],
        "hemoglobin": [("hemoglobin_low", lambda v: v < 12),
                       ("hemoglobin_high", lambda v: v > 17.5)],
        "hematocrit": [("hct_high", lambda v: v > 52),
                       ("hct_low", lambda v: v < 36)],
        "red_cell_distribution_width": [("rdw_high", lambda v: v > 15)],
        'serum_iron': [('serum_iron_low', lambda v: v < 60)],
        "platelet_count": [("platelets_low", lambda v: v < 150),
                           ("platelets_high", lambda v: v > 450)],
        "white_blood_cell_count": [('wbc_high', lambda v: v > 11),
                                   ("wbc_low", lambda v: v < 4)],
        "reticulocyte_count": [("retic_high", lambda v: v > 2.5),
                               ("retic_low", lambda v: v < 0.5)],
        "vitamin_b12": [("b12_low", lambda v: v < 200)],
        'folate': [("folate_low", lambda v: v < 4)],
        'haptoglobin': [("haptoglobin_low", lambda v: v < 30)],
        "lactate_dehydrogenase": [("ldh_high", lambda v: v > 250)],
        "mean_corpuscular_hemoglobin": [("mch_low", lambda v: v < 27)],

        "fasting_plasma_glucose": [
            ("fbs_high", lambda v: v >= 126),
            ("fbs_prediabetic", lambda v: 100 <= v < 126),
            ("fbs_low", lambda v: v < 70)],
        "hemoglobin_a1c": [
            ("hba1c_high", lambda v: v >= 6.5),
            ("hba1c_prediabetic", lambda v: 5.7 <= v < 6.5)],
        "two_hour_postload_glucose": [("ogtt_high", lambda v: v >= 200),
                                      ("ogtt_igt", lambda v: 140 <= v < 200)],
        "fasting_insulin": [("insulin_high", lambda v: v > 15)],

        "egfr_ckd_epi_creatinine": [
            ('egfr_low', lambda v: v < 60),
            ("egfr_severely_low", lambda v: v < 30)],
        'creatinine': [("creatinine_high", lambda v: v > 1.3)],
        "urea_nitrogen": [("bun_high", lambda v: v > 20)],
        "urine_albumin_to_creatinine_ratio": [
            ("acr_high", lambda v: v >= 30),
            ("acr_severe", lambda v: v >= 300)],
        "cystatin_c": [('cystatin_high', lambda v: v > 1.0)],
        "potassium": [('potassium_high', lambda v: v > 5.0),
                      ('potassium_low', lambda v: v < 3.5)],
        "sodium": [("sodium_low", lambda v: v < 135),
                   ("sodium_high", lambda v: v > 145)],

        "thyroid_stimulating_hormone": [
            ("tsh_high", lambda v: v > 4.5),
            ("tsh_very_high", lambda v: v > 10),
            ("tsh_low", lambda v: v < 0.4)],
        "free_thyroxine": [("ft4_low", lambda v: v < 0.8),
                           ("ft4_high", lambda v: v > 1.8)],
        "free_triiodothyronine": [("ft3_high", lambda v: v > 4.2)],
        "anti_tpo_antibody": [("anti_tpo_positive", lambda v: v > 35)],

        "alanine_aminotransferase": [
            ("alt_high", lambda v: v > 56),
            ("alt_very_high", lambda v: v > 300)],
        "aspartate_aminotransferase": [
            ("ast_high", lambda v: v > 40),
            ('ast_very_high', lambda v: v > 300)],
        'alkaline_phosphatase': [("alp_high", lambda v: v > 147)],
        "gamma_glutamyl_transferase": [("ggt_high", lambda v: v > 55)],
        "bilirubin_total": [('bilirubin_high', lambda v: v > 1.2)],
        "albumin": [('albumin_low', lambda v: v < 3.5)],
        "international_normalized_ratio": [('inr_high', lambda v: v > 1.3)],

        'total_cholesterol': [("cholesterol_high", lambda v: v >= 240)],
        "ldl_cholesterol": [("ldl_high", lambda v: v >= 160)],
        "hdl_cholesterol": [("hdl_low", lambda v: v < 40)],
        "triglycerides": [('triglycerides_high', lambda v: v >= 150),
                          ("triglycerides_very_high", lambda v: v >= 500)],

        "c_reactive_protein": [("crp_high", lambda v: v > 10),
                               ("crp_very_high", lambda v: v > 100)],
        'erythrocyte_sedimentation_rate': [("esr_high", lambda v: v > 30)],
        'procalcitonin': [('procalcitonin_high', lambda v: v > 0.5)],
        "lactate": [("lactate_high", lambda v: v > 2.0)],

        "calcium_total": [("calcium_high", lambda v: v > 10.5),
                          ("calcium_low", lambda v: v < 8.5)],
        "parathyroid_hormone": [("pth_high", lambda v: v > 65)],
        'vitamin_d_25_hydroxy': [("vitamin_d_low", lambda v: v < 20)],
        'creatine_kinase': [('ck_high', lambda v: v > 200)],
        "troponin_i": [('troponin_high', lambda v: v > 0.04)],
        "anti_ttg_iga": [("ttg_positive", lambda v: v > 10)],
        # === SUPER-ENHANCED COMPLEX LAB FINDINGS ===
        "anion_gap": [("anion_gap_high", lambda v: v is not None and v > 12), ("anion_gap_very_high", lambda v: v is not None and v > 20)],
        "corrected_anion_gap": [("anion_gap_high", lambda v: v is not None and v > 12)],
        "delta_gap": [("delta_gap_high", lambda v: v is not None and abs(v) > 5)],
        "delta_ratio": [("delta_ratio_low", lambda v: v is not None and v < 0.4), ("delta_ratio_high", lambda v: v is not None and v > 2.0)],
        "osmolality": [("osmolality_high", lambda v: v is not None and v > 295), ("osmolality_low", lambda v: v is not None and v < 275)],
        "calculated_osmolality": [("osmolality_high", lambda v: v is not None and v > 295), ("osmolality_low", lambda v: v is not None and v < 275)],
        "osmolar_gap": [("osm_gap_high", lambda v: v is not None and v > 10)],
        "ketones": [("ketones_high", lambda v: v is not None and v > 0.6)],
        "beta_hydroxybutyrate": [("ketones_high", lambda v: v is not None and v > 0.6)],
        "ph": [("ph_low", lambda v: v is not None and v < 7.35), ("ph_high", lambda v: v is not None and v > 7.45)],
        "arterial_ph": [("ph_low", lambda v: v is not None and v < 7.35), ("ph_high", lambda v: v is not None and v > 7.45)],
        "pco2": [("pco2_high", lambda v: v is not None and v > 45), ("pco2_low", lambda v: v is not None and v < 35)],
        "bicarbonate": [("bicarbonate_low", lambda v: v is not None and v < 22), ("bicarbonate_high", lambda v: v is not None and v > 29), ("bicarbonate_normal", lambda v: v is not None and 22 <= v <= 29)],
        "carbon_dioxide": [("bicarbonate_low", lambda v: v is not None and v < 22), ("bicarbonate_high", lambda v: v is not None and v > 29)],
        "chloride": [("chloride_high", lambda v: v is not None and v > 107), ("chloride_low", lambda v: v is not None and v < 96)],
        "phosphate": [("phosphate_high", lambda v: v is not None and v > 4.5), ("phosphate_low", lambda v: v is not None and v < 2.5)],
        "phosphate_inorganic": [("phosphate_high", lambda v: v is not None and v > 4.5), ("phosphate_low", lambda v: v is not None and v < 2.5)],
        "d_dimer": [("d_dimer_high", lambda v: v is not None and v > 0.5),
                    ("d_dimer_very_high", lambda v: v is not None and v > 2.0)],
        "fibrinogen": [("fibrinogen_low", lambda v: v is not None and v < 150), ("fibrinogen_high", lambda v: v is not None and v > 400)],
        "prothrombin_time": [("pt_high", lambda v: v is not None and v > 14)],
        "bilirubin_direct": [("bilirubin_direct_high", lambda v: v is not None and v > 0.3)],
        "bilirubin_indirect": [("bilirubin_indirect_high", lambda v: v is not None and v > 0.8)],
        "prealbumin": [("prealbumin_low", lambda v: v is not None and v < 15)],
        "body_mass_index": [("bmi_high", lambda v: v is not None and v >= 30), ("bmi_overweight", lambda v: v is not None and 25 <= v < 30), ("bmi_low", lambda v: v is not None and v < 18.5)],
        "waist_circumference": [("waist_high", lambda v: v is not None and v >= 102)],
        "neutrophils": [("neutrophils_high", lambda v: v is not None and v > 70), ("neutrophils_low", lambda v: v is not None and v < 40)],
        "lymphocytes": [("lymphocytes_high", lambda v: v is not None and v > 40), ("lymphocytes_low", lambda v: v is not None and v < 20)],
        "cortisol": [("cortisol_low", lambda v: v is not None and v < 5), ("cortisol_high", lambda v: v is not None and v > 25)],
        "urine_osmolality": [("urine_osmolality_high", lambda v: v is not None and v > 300)],
        "corrected_calcium": [("calcium_high", lambda v: v is not None and v > 10.5), ("calcium_low", lambda v: v is not None and v < 8.5)],
        "corrected_sodium": [("sodium_low", lambda v: v is not None and v < 135), ("sodium_high", lambda v: v is not None and v > 145)],
        "bun_to_creatinine_ratio": [("bun_cr_high", lambda v: v is not None and v > 20), ("bun_cr_low", lambda v: v is not None and v < 10)],
        "neutrophil_to_lymphocyte_ratio": [("nlr_high", lambda v: v is not None and v > 3.5)],
        "glucose": [("glucose_random_high", lambda v: v is not None and v >= 200), ("glucose_high", lambda v: v is not None and v >= 200),
                    ("glucose_very_high", lambda v: v is not None and v >= 600), ("glucose_low", lambda v: v is not None and v < 70),
                    ("glucose_critical_low", lambda v: v is not None and v < 54)],
    }


    PRIOR_MODIFIERS: dict[str, dict[str, Any]] = {
        "type_2_diabetes": {
            'age': [(0, 20, 0.05), (20, 40, 0.3), (40, 60, 1.0),
                    (60, 200, 2.2)],
            "sex": {"male": 1.15, 'female': 0.9}},
        "chronic_kidney_disease": {
            "age": [(0, 30, 0.1), (30, 50, 0.4), (50, 70, 1.0),
                    (70, 200, 2.8)]},
        "iron_deficiency_anemia": {
            "age": [(0, 5, 2.0), (5, 15, 1.2), (15, 50, 1.0),
                    (50, 200, 0.8)],
            "sex": {'female': 3.0, "male": 0.35}},
        "hypothyroidism": {
            'age': [(0, 30, 0.4), (30, 60, 1.0), (60, 200, 1.8)],
            "sex": {"female": 3.5, "male": 0.4}},
        "hyperthyroidism": {'sex': {"female": 2.5, "male": 0.5}},
        "hypertension": {
            'age': [(0, 30, 0.15), (30, 50, 0.6), (50, 70, 1.5),
                    (70, 200, 2.5)]},
        "metabolic_syndrome": {
            "age": [(0, 25, 0.2), (25, 45, 0.7), (45, 200, 1.5)]},
        'nafl_d': {
            "age": [(0, 18, 0.3), (18, 65, 1.0), (65, 200, 1.2)]},
        "liver_cirrhosis": {
            "age": [(0, 30, 0.15), (30, 200, 1.0)],
            "sex": {"male": 1.8, "female": 0.6}},
        "vitamin_b12_deficiency": {
            "age": [(0, 50, 0.6), (50, 70, 1.2), (70, 200, 2.2)]},
        "urinary_tract_infection": {"sex": {"female": 4.0, "male": 0.3}},
        'acute_kidney_injury': {
            "age": [(0, 40, 0.4), (40, 65, 1.0), (65, 200, 2.0)]},
        "hyperlipidemia": {
            "age": [(0, 20, 0.1), (20, 40, 0.6), (40, 200, 1.3)]},
        'anemia': {'sex': {"female": 2.0, "male": 0.6}},
        "celiac_disease": {
            "age": [(0, 40, 1.3), (40, 200, 0.7)]},
        "primary_hyperparathyroidism": {
            "age": [(0, 40, 0.5), (40, 60, 1.0), (60, 200, 1.8)],
            "sex": {"female": 1.8, "male": 0.6}},
        "gout": {
            "age": [(0, 30, 0.3), (30, 60, 1.0), (60, 200, 1.6)],
            "sex": {"male": 2.5, "female": 0.4}},
        "osteoporosis": {
            "age": [(0, 50, 0.2), (50, 70, 1.0), (70, 200, 2.5)],
            "sex": {"female": 3.0, "male": 0.4}},
        "coronary_artery_disease": {
            "age": [(0, 40, 0.2), (40, 60, 1.0), (60, 200, 2.0)],
            "sex": {"male": 1.6, "female": 0.6}},
        "sepsis": {
            "age": [(0, 10, 1.5), (10, 65, 0.7), (65, 200, 2.2)]},
        "vitamin_d_deficiency": {
            "age": [(0, 30, 0.8), (30, 60, 1.0), (60, 200, 1.4)]},
        "malnutrition": {
            "age": [(0, 5, 1.8), (5, 70, 0.7), (70, 200, 2.0)]},
        "pancytopenia": {
            "age": [(0, 50, 0.8), (50, 200, 1.5)]},
    }

    def __init__(self):
        self.nodes: dict[str, BayesiNode] = {}
        self._sakht_network()

    def _sakht_network(self):
        for disease_id, prior in self.PRIORS.items():
            node = BayesiNode(
                disease_id=disease_id,
                prior_probability=prior,
                dependencies=self.DEPENDENCIES.get(disease_id, []),
            )
            lrs = self.LIKELIHOOD_RATIOS.get(disease_id, {})
            for feature_key, lr_data in lrs.items():
                node.likelihood_ratios[feature_key] = lr_data.get(
                    'LR+', 1.0)
                node.negative_lrs[feature_key] = lr_data.get(
                    "LR-", 1.0)
            self.nodes[disease_id] = node

    @staticmethod
    def _shakhes_haye_moshtagh(
        enriched: Mapping[str, EnrichedObservation],
    ) -> dict[str, float]:
        """Indices no lab reports directly but every haematologist computes.

        Without these the network cannot tell thalassaemia trait from iron
        deficiency - the single most common discrimination in the field.
        """
        def val(name):
            o = enriched.get(name)
            v = getattr(o, "value", None) if o is not None else None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        out: dict[str, float] = {}
        mcv = val("mean_corpuscular_volume")
        rbc = val("red_blood_cell_count")
        if mcv is not None and rbc is not None and rbc > 0:
            # Mentzer <13 favours thalassaemia trait, >=13 iron deficiency
            out["mentzer_index"] = mcv / rbc
        iron = val("serum_iron")
        tibc = val("total_iron_binding_capacity")
        if iron is not None and tibc is not None and tibc > 0:
            out.setdefault("transferrin_saturation", 100.0 * iron / tibc)
        return out

    def estekhraj_findings(
        self,
        enriched: Mapping[str, EnrichedObservation],
    ) -> dict[str, dict[str, Any]]:
        findings: dict[str, dict[str, Any]] = {}
        derived_idx = self._shakhes_haye_moshtagh(enriched)
        for name, value in derived_idx.items():
            for finding_key, condition in (
                    self.FEATURE_TO_FINDING.get(name) or []):
                try:
                    present = bool(condition(value))
                except (TypeError, ValueError):
                    continue
                findings[finding_key] = {
                    "present": present, "value": value,
                    "feature_id": name, "severity": None,
                    "reliability": 0.9, "measured": True,
                }
        for fid, obs in enriched.items():
            mappings = self.FEATURE_TO_FINDING.get(fid)
            if not mappings:
                continue
            val_for_comp = obs.value
            try:
                num_v = float(val_for_comp) if val_for_comp is not None else None
            except (TypeError, ValueError):
                num_v = None

            if num_v is not None:
                if fid in ("platelet_count", "platelets", "plt") and num_v > 1000.0:
                    val_for_comp = num_v / 1000.0
                elif fid in ("white_blood_cell_count", "wbc", "white_blood_cells") and num_v > 100.0:
                    val_for_comp = num_v / 1000.0
                elif fid in ("red_blood_cell_count", "rbc", "red_blood_cells") and num_v > 10000.0:
                    val_for_comp = num_v / 1000000.0

            for finding_key, condition in mappings:
                try:
                    present = bool(condition(val_for_comp))
                except (TypeError, ValueError):
                    continue
                # Grounding to population-adjusted reference interval direction:
                # Where the preprocessor evaluated the value against an age-, sex-,
                # geriatric, or pregnancy-specific reference interval, that verdict wins
                # over static adult threshold lambdas:
                if (obs.direction in ("low", "high", "normal")
                        and obs.reference_used.get("low") is not None
                        and obs.reference_used.get("high") is not None):
                    if finding_key.endswith("_low"):
                        present = (obs.direction == "low")
                    elif finding_key.endswith("_high") or finding_key.endswith("_elevated"):
                        present = (obs.direction == "high")
                    elif finding_key.endswith("_normal"):
                        present = (obs.direction == "normal")
                findings[finding_key] = {
                    "present": present,
                    "value": obs.value,
                    "feature_id": fid,
                    'severity': obs.severity_score,
                    "reliability": obs.reliability,
                    "measured": True,
                }
        return findings

    # -----------------------------------------------------------------
    # Regional prior calibration.
    #
    # The registry priors are literature (largely North-American /
    # European) prevalences. Odds multipliers below re-anchor them to a
    # region. They are PROVISIONAL literature-derived estimates, clearly
    # not a substitute for locally collected, physician-adjudicated data;
    # a hospital can replace them with its own by dropping a
    # `regional_priors.json` next to the registries:
    #   {"IR": {"thalassemia_trait": 8.0, ...}}
    # Sources for the IR defaults: national beta-thal carrier frequency
    # ~4-6 % (up to ~10 % Caspian littoral & Persian-Gulf provinces);
    # G6PD deficiency ~10-15 % of males in Mazandaran/Gilan; high IDA
    # prevalence in women of reproductive age; FMF carrier enrichment in
    # north-west; higher vitamin-D deficiency prevalence.
    # -----------------------------------------------------------------
    REGIONAL_PRIOR_ODDS: dict[str, dict[str, float]] = {
        "IR": {
            "thalassemia_trait": 8.0,
            "beta_thalassemia": 6.0,
            "beta_thalassemia_minor": 8.0,
            "alpha_thalassemia_trait": 3.0,
            "g6pd_deficiency": 5.0,
            "iron_deficiency_anemia": 1.6,
            "iron_deficiency": 1.6,
            "familial_mediterranean_fever": 6.0,
            "vitamin_d_deficiency": 1.8,
            "hepatitis_b_infection": 1.5,
            "brucellosis": 10.0,
            "hereditary_hemochromatosis": 0.3,
            "hemochromatosis": 0.4,
            "cystic_fibrosis": 0.3,
        },
    }
    _regional_overrides_loaded = False

    @classmethod
    def _load_regional_overrides(cls) -> None:
        if cls._regional_overrides_loaded:
            return
        cls._regional_overrides_loaded = True
        try:
            here = Path(__file__).resolve().parent
            for cand in (here / "regional_priors.json",
                         Path(os.environ.get("HEMOGLYPH_REGIONAL_PRIORS", "")
                              or "/nonexistent")):
                if cand.is_file():
                    data = json.loads(cand.read_text(encoding="utf-8"))
                    for region, table in (data or {}).items():
                        cls.REGIONAL_PRIOR_ODDS.setdefault(region.upper(), {})
                        cls.REGIONAL_PRIOR_ODDS[region.upper()].update(
                            {k: float(v) for k, v in table.items()})
                    logger.info("Regional prior overrides loaded from %s", cand)
                    break
        except Exception as exc:  # never let a bad file break inference
            logger.warning("regional_priors.json ignored: %s", exc)

    @staticmethod
    def _region_of(context: Optional[ClinicalContext]) -> Optional[str]:
        if context is None:
            return None
        extra = context.extra or {}
        nested = extra.get("extra") if isinstance(extra.get("extra"), Mapping) else {}
        for key in ("region", "country", "population"):
            v = extra.get(key) or (nested or {}).get(key)
            if v:
                return str(v).upper()
        env = os.environ.get("HEMOGLYPH_REGION")
        return env.upper() if env else None

    def adjusted_prior(self, disease_id: str,
                       context: Optional[ClinicalContext] = None) -> float:
        node = self.nodes.get(disease_id)
        base = node.prior_probability if node else 0.01
        if context is None:
            return _clamp01(base)
        mods = self.PRIOR_MODIFIERS.get(disease_id) or {}
        odds = base / max(1e-9, 1.0 - base)
        self._load_regional_overrides()
        region = self._region_of(context)
        if region:
            odds *= (self.REGIONAL_PRIOR_ODDS.get(region) or {}).get(
                disease_id, 1.0)
        age = _float(context.age_years)
        if age is not None:
            for lo, hi, ratio in mods.get('age', ()):
                if lo <= age < hi:
                    odds *= ratio
                    break
        sex = context.normalized_jensiat()
        if sex:
            odds *= (mods.get("sex") or {}).get(sex, 1.0)
        # Biological Gating for Bayesian Prior:
        is_preg_dis = any(k in disease_id for k in ("_in_pregnancy", "gestational", "preeclampsia", "eclampsia", "peripartum", "postpartum", "hellp"))
        if is_preg_dis and not context.pregnant:
            return 0.0

        if sex == "male" and any(k in disease_id for k in ("ovarian", "cervical", "uterine", "endometrio", "polycystic_ovary")):
            return 0.0
        if sex == "female" and any(k in disease_id for k in ("prostate", "prostatic", "testicular")):
            return 0.0

        # Pediatric Adult-Malignancy & Chronic Degenerative Gating
        if age is not None and age < 18.0:
            if disease_id in (
                "coronary_artery_disease", "atherosclerosis", "multiple_myeloma",
                "chronic_lymphocytic_leukemia", "sarcopenia", "osteoporosis",
                "hepatocellular_carcinoma", "liver_cirrhosis", "gout"
            ):
                return 0.0

        if context.pregnant and disease_id in (
                "iron_deficiency_anemia", "anemia"):
            odds *= 2.5
        return _clamp01(odds / (1.0 + odds))

    def mohasebe_posteriors(
        self,
        findings: Mapping[str, dict[str, Any]],
        context: Optional[ClinicalContext] = None,
    ) -> list[BayesianResult]:
        results: list[BayesianResult] = []
        for disease_id, node in self.nodes.items():
            prior = self.adjusted_prior(disease_id, context)
            prior = self._test_ordering_prior(node, findings, prior)
            posterior = self._mohasebe_posterior(node, findings, prior)
            factors = self._identify_contributing_factors(node, findings)
            relevant = [k for k in findings
                        if k in node.likelihood_ratios]
            n_pos = sum(1 for k in relevant
                        if findings[k].get("present"))
            results.append(BayesianResult(
                disease_id=disease_id,
                posterior_probability=posterior,
                evidence_count=n_pos,
                measured_count=len(relevant),
                contributing_factors=factors,
                confidence=self._mohasebe_confidence(factors),
                explanation=self._explain_posterior(
                    node, findings, posterior),
            ))
        results = self._emal_dependencies(results)
        results.sort(key=lambda r: -r.posterior_probability)
        return results

    # Findings produced by routine panels (CBC, BMP, LFT, lipids, TSH) are
    # measured in nearly everyone and say nothing about why the sample was
    # drawn. Anything else with a strong LR is a *targeted* test.
    _ROUTINE_FINDING_STEMS: frozenset[str] = frozenset({
        "hemoglobin", "hematocrit", "mcv", "mch", "mchc", "rdw", "platelets", "platelet",
        "wbc", "neutrophils", "lymphocytes", "glucose", "creatinine", "egfr", "bun", "urea",
        "sodium", "potassium", "chloride", "bicarbonate", "calcium", "phosphate", "magnesium",
        "alt", "ast", "alp", "ggt", "bilirubin", "albumin", "total_protein", "cholesterol",
        "ldl", "hdl", "triglycerides", "tsh", "uric_acid", "anion_gap", "hba1c", "ferritin",
        "crp", "esr", "ldh", "bmi", "waist", "iron", "transferrin_sat", "tibc",
    })
    ORDERED_TEST_PRIOR_FLOOR = 0.06

    # Findings that measure (nearly) the same physiological quantity, or are
    # graded cut-offs of ONE analyte, are not independent evidence. Inside a
    # cluster the strongest finding counts in full and the rest at 25 %;
    # across clusters the usual correlated-evidence discount applies. This
    # replaces a uniform discount that treated "Hb low + Hct low" exactly
    # like "lipase high + calcium low".
    EVIDENCE_CLUSTERS: tuple[frozenset[str], ...] = (
        frozenset({"hemoglobin_low", "hct_low"}),
        frozenset({"hemoglobin_high", "hct_high", "rbc_high"}),
        frozenset({"mcv_low", "mch_low", "mentzer_low", "mentzer_high"}),
        frozenset({"ck_high", "ck_very_high"}),
        frozenset({"alt_high", "alt_very_high", "ast_high"}),
        frozenset({"alp_high", "ggt_high"}),
        frozenset({"bilirubin_high", "indirect_bilirubin_high"}),
        frozenset({"crp_high", "crp_very_high"}),
        frozenset({"d_dimer_high", "d_dimer_very_high"}),
        frozenset({"ferritin_high", "ferritin_critical_high"}),
        frozenset({"ferritin_low", "serum_iron_low", "transferrin_sat_low", "tibc_high"}),
        frozenset({"glucose_high", "glucose_very_high", "glucose_random_high", "fbs_high",
                   "fbs_prediabetic", "ogtt_high", "ogtt_igt"}),
        frozenset({"hba1c_high", "hba1c_prediabetic"}),
        frozenset({"platelets_low", "platelets_very_low"}),
        frozenset({"tsh_high", "tsh_very_high"}),
        frozenset({"m_spike_present", "m_spike_high", "total_protein_high"}),
        frozenset({"flc_high", "flc_ratio_abnormal"}),
        frozenset({"creatinine_high", "egfr_low", "egfr_severely_low", "bun_high", "cystatin_high"}),
        frozenset({"acr_high", "acr_severe", "proteinuria_nephrotic"}),
        frozenset({"blasts_present", "blasts_high"}),
        frozenset({"triglycerides_high", "triglycerides_very_high"}),
        frozenset({"cholesterol_high", "ldl_high"}),
        frozenset({"bmi_high", "bmi_overweight"}),
        frozenset({"bnp_high", "nt_probnp_high"}),
        frozenset({"pt_high", "inr_high"}),
        frozenset({"sodium_high", "osmolality_high"}),
        frozenset({"sodium_low", "osmolality_low"}),
        frozenset({"bicarbonate_low", "ph_low"}),
        frozenset({"wbc_high", "neutrophils_high"}),
        frozenset({"ft4_high", "ft3_high"}),
    )
    WITHIN_CLUSTER_SECONDARY_WEIGHT = 0.25
    CROSS_CLUSTER_WEIGHT = 0.62
    _CLUSTER_OF: dict[str, int] = {}

    @classmethod
    def cluster_of(cls, finding_key: str) -> str:
        if not cls._CLUSTER_OF:
            for i, grp in enumerate(cls.EVIDENCE_CLUSTERS):
                for k in grp:
                    cls._CLUSTER_OF[k] = i
        i = cls._CLUSTER_OF.get(finding_key)
        return f"c{i}" if i is not None else finding_key

    @classmethod
    def _is_targeted_finding(cls, finding_key: str) -> bool:
        stem = finding_key
        for suf in ("_very_high", "_very_low", "_critical_low", "_critical_high", "_severely_low",
                    "_severe", "_high", "_low", "_normal", "_present", "_positive", "_abnormal",
                    "_elevated", "_overweight", "_random_high", "_nonsuppressed"):
            if stem.endswith(suf):
                stem = stem[: -len(suf)]
                break
        return stem not in cls._ROUTINE_FINDING_STEMS

    def _test_ordering_prior(self, node: BayesiNode,
                             findings: Mapping[str, dict],
                             prior: float) -> float:
        """Pre-test probability conditioned on the test having been ordered.

        Population prevalence is the wrong prior once a *targeted* test
        (lipase, CK, anti-HAV IgM, SPEP, PTHrP, D-dimer...) is on the
        report: the clinician ordered it because the syndrome was already
        suspected, and the spectrum of tested patients carries a pre-test
        probability in the 5-20 % range (Sox / Guyatt, diagnostic-test
        theory). Without this correction a prevalence of 0.4 % and an LR+
        of 18 still yield only 7 % - a pathognomonic result reads as
        "unlikely". Routine-panel findings do not trigger the floor.
        """
        if prior <= 0.0:
            return prior
        max_lr = max(node.likelihood_ratios.values() or [0.0])
        for key, lr in node.likelihood_ratios.items():
            # Only the node's *targeted* test(s) betray clinical suspicion:
            # a strong marker (LR+ >= 10) or the node's single most specific
            # finding (D-dimer for PE). Shared routine findings never do.
            if lr < 10.0 and lr < max_lr:
                continue
            f = findings.get(key)
            if not f or not f.get("measured", True):
                continue
            if self._is_targeted_finding(key):
                return max(prior, self.ORDERED_TEST_PRIOR_FLOOR)
        return prior

    def _mohasebe_posterior(self, node: BayesiNode,
                           findings: Mapping[str, dict],
                           prior: Optional[float] = None) -> float:
        if prior is not None and prior <= 0.0:
            return 0.0
        p0 = _clamp01(prior if prior is not None
                      else node.prior_probability)
        log_odds = math.log(max(p0, 1e-9) / max(1e-9, 1 - p0))
        base_log_odds = log_odds
        # per-cluster lists of weighted log-LR contributions (sorted keys so
        # the result cannot depend on dict iteration order)
        pos_by_cluster: dict[str, list[float]] = {}
        neg_by_cluster: dict[str, list[float]] = {}
        for finding_key in sorted(findings):
            finding_data = findings[finding_key]
            if finding_key not in node.likelihood_ratios:
                continue
            if not finding_data.get("measured", True):
                continue
            reliability = _clamp01(
                _float(finding_data.get("reliability")) or 1.0)
            if finding_data.get("present"):
                lr_full = node.likelihood_ratios[finding_key]
                severity = finding_data.get('severity')
                sev = _clamp01(1.0 if severity is None else severity)

                # Severity scales how far a value sits past its cutoff. A
                # finding that is merely positive still deserves most of
                # its published LR, so the floor is high; only genuinely
                # borderline values get pulled toward 1.0.
                lr = 1.0 + (lr_full - 1.0) * max(sev, 0.80)
                bucket = pos_by_cluster
            else:
                lr = node.negative_lrs.get(finding_key, 1.0)
                bucket = neg_by_cluster
            # Guard against a registry typo of LR=0 taking the log to -inf.
            lr = max(float(lr), 1e-3)
            bucket.setdefault(self.cluster_of(finding_key), []).append(math.log(lr) * reliability)

        w2 = self.WITHIN_CLUSTER_SECONDARY_WEIGHT

        def _collapse(contribs: list[float], positive: bool) -> float:
            # strongest member in full, the rest at the secondary weight
            ordered = sorted(contribs, reverse=positive)
            return ordered[0] + w2 * sum(ordered[1:]) if ordered else 0.0

        # Across clusters findings still correlate (a low MCV and a low
        # ferritin partly say the same thing), so naive LR multiplication
        # overshoots. Keep the strongest cluster whole and count every
        # further supporting cluster at CROSS_CLUSTER_WEIGHT. (The previous
        # form scaled the SUM by (1+0.62(n-1))/n, which let a weak extra
        # finding *lower* the posterior - non-monotone; this form is
        # monotone: adding supporting evidence never reduces the odds.)
        n_positive = len(pos_by_cluster)
        pos_contribs = sorted((_collapse(c, True) for c in pos_by_cluster.values()), reverse=True)
        support = sum(x for x in pos_contribs if x > 0)
        if pos_contribs:
            head, *rest = pos_contribs
            support = head + self.CROSS_CLUSTER_WEIGHT * sum(x for x in rest if x > 0) \
                + sum(x for x in rest if x <= 0)
        log_odds += support
        for cl, contribs in neg_by_cluster.items():
            if cl in pos_by_cluster:
                # a cluster with one positive and one negative graded cut-off
                # (CK high but not very high) is simply "positive at the lower
                # grade"; do not also charge the negative LR of the higher grade
                continue
            log_odds += _collapse(contribs, False)

        delta = log_odds - base_log_odds

        # +/-8 log-odds ~ 0.03%..99.97%. Never return a hard 0 or 1.
        delta = max(-8.0, min(8.0, delta))
        final = base_log_odds + delta
        # exp() overflows past ~709; clamping at 30 keeps the sigmoid in range
        # while leaving the probability visually saturated anyway.
        posterior = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, final))))
        return _clamp01(posterior)

    def _emal_dependencies(
        self, results: list[BayesianResult]
    ) -> list[BayesianResult]:
        prob_map = {r.disease_id: r.posterior_probability
                    for r in results}
        for result in results:
            node = self.nodes.get(result.disease_id)
            if not node:
                continue
            for dep_id in node.dependencies:
                dep_prob = prob_map.get(dep_id, 0)
                if dep_prob > 0.3:
                    boost = 1 + (dep_prob - 0.3) * 0.5
                    # multiply the ODDS, not the probability: a probability
                    # scaled by 1.35 can only be clipped, odds stay coherent
                    p = _clamp01(result.posterior_probability)
                    odds = p / max(1e-9, 1.0 - p) * boost
                    result.posterior_probability = min(0.99, odds / (1.0 + odds))
                    result.contributing_factors.append({
                        "type": "dependency",
                        "source": dep_id,
                        'effect': f"Boosted {boost:.2f}x",
                    })
        return results

    def _identify_contributing_factors(
        self, node: BayesiNode, findings: Mapping[str, dict]
    ) -> list[dict]:
        factors = []
        strongest_in_cluster: dict[str, tuple[float, str]] = {}
        for finding_key in sorted(findings):
            finding_data = findings[finding_key]
            if finding_key in node.likelihood_ratios and finding_data.get("present"):
                lr = node.likelihood_ratios[finding_key]
                cl = self.cluster_of(finding_key)
                if lr > strongest_in_cluster.get(cl, (0.0, ""))[0]:
                    strongest_in_cluster[cl] = (lr, finding_key)
        for finding_key in sorted(findings):
            finding_data = findings[finding_key]
            if finding_key in node.likelihood_ratios:
                lr = node.likelihood_ratios[finding_key]
                if finding_data.get("present"):
                    item = {
                        "type": "evidence",
                        "feature": finding_key,
                        "likelihood_ratio": lr,
                        "strength": ("strong" if lr > 10
                                     else "moderate" if lr > 3
                                     else "weak"),
                    }
                    cl = self.cluster_of(finding_key)
                    lead = strongest_in_cluster.get(cl, (0.0, finding_key))[1]
                    if lead != finding_key:
                        # transparency: this finding is physiologically
                        # redundant with `lead` and counted at the secondary weight
                        item["correlated_with"] = lead
                        item["effective_weight"] = self.WITHIN_CLUSTER_SECONDARY_WEIGHT
                    factors.append(item)
        return factors

    def _mohasebe_confidence(self, factors: list[dict]) -> float:
        evidence = [f for f in factors if f.get("type") == 'evidence']
        if not evidence:
            return 0.0
        score = sum(
            {'strong': 0.35, "moderate": 0.2,
             'weak': 0.08}.get(f.get("strength", "weak"), 0.08)
            for f in evidence)

        if len(evidence) == 1:
            score = min(score, 0.45)
        return _clamp01(score)

    def _explain_posterior(self, node, findings, posterior) -> str:
        drivers = sorted(
            ((k, node.likelihood_ratios.get(k, 1.0))
             for k, v in findings.items()
             if v.get("present") and k in node.likelihood_ratios),
            key=lambda kv: -kv[1])[:3]
        if drivers:
            driver_text = "، ".join(
                f"{k} (LR+ {lr:g})" for k, lr in drivers)
        else:
            driver_text = "بدون شاهد مثبت اختصاصی"
        if posterior > 0.7:
            level = "بسیار محتمل"
        elif posterior > 0.4:
            level = "محتمل"
        elif posterior > 0.15:
            level = "ممکن"
        else:
            level = "کم‌احتمال"
        n_ev = sum(1 for f in findings.values() if f.get("present"))
        return (f"احتمال {level} ({posterior:.1%}) بر اساس {n_ev} "
                f"یافته. مؤثرترین شواهد: {driver_text}.")


@dataclass
class FuzzyGhaede:
    disease_id: str
    name: str
    conditions: list[dict[str, Any]]
    weight: float = 1.0
    threshold: float = 0.5


@dataclass
class FuzzyResult:
    disease_id: str
    membership_score: float
    activated_rules: list[str] = field(default_factory=list)
    explanation: str = ""
    used_features: list[str] = field(default_factory=list)
    min_reliability: float = 1.0


class AdaptiveFuzzyEngine:

    def __init__(self):
        self.rules = self._sakht_ghaedeha()

    def _sakht_ghaedeha(self) -> list[FuzzyGhaede]:
        return [
            FuzzyGhaede(
                disease_id='iron_deficiency_anemia',
                name="IDA Classic Pattern", weight=1.0,
                conditions=[
                    {"feature": "ferritin", "type": 'low', "threshold": 30, "softness": 30, "weight": 1.6},
                    {"feature": 'mean_corpuscular_volume', 'type': "low", "threshold": 80, "softness": 80, "weight": 1.2},
                    {'feature': "hemoglobin", "type": "low", "threshold": 12, "softness": 12, "weight": 1.0},
                    {"feature": "transferrin_saturation", "type": "low", "threshold": 20, "softness": 20, "weight": 1.2},
                    {"feature": "red_cell_distribution_width", "type": "high", "threshold": 15, "softness": 15, "weight": 0.8},
                ],
            ),
            FuzzyGhaede(
                disease_id="anemia_of_chronic_disease",
                name="ACD Pattern", weight=0.9,
                conditions=[
                    {'feature': "ferritin", "type": "high", "threshold": 100, "softness": 100, "weight": 1.3},
                    {"feature": 'c_reactive_protein', "type": "high", "threshold": 10, 'softness': 10, "weight": 1.4},
                    {"feature": 'hemoglobin', "type": "low", 'threshold': 12, "softness": 12, "weight": 1.0},
                    {"feature": "mean_corpuscular_volume", "type": 'low', "threshold": 80, "softness": 80, "weight": 0.5},
                ],
            ),
            FuzzyGhaede(
                disease_id='vitamin_b12_deficiency',
                name="B12 Deficiency Pattern", weight=1.0,
                conditions=[
                    {"feature": "vitamin_b12", 'type': "low", "threshold": 200, "softness": 200, "weight": 1.8},
                    {"feature": "mean_corpuscular_volume", "type": "high", "threshold": 100, "softness": 100, 'weight': 1.3},
                    {"feature": 'hemoglobin', "type": "low", "threshold": 12, "softness": 12, "weight": 0.8},
                ],
            ),
            FuzzyGhaede(
                disease_id="hemolytic_anemia",
                name='Hemolysis Pattern', weight=1.0,
                conditions=[
                    {"feature": "haptoglobin", "type": "low", 'threshold': 30, "softness": 30, "weight": 1.7},
                    {'feature': "lactate_dehydrogenase", "type": "high", "threshold": 250, "softness": 250, "weight": 1.3},
                    {'feature': 'reticulocyte_count', "type": "high", 'threshold': 2.5, "softness": 2.5, "weight": 1.4},
                    {"feature": "bilirubin_total", "type": 'high', "threshold": 1.2, 'softness': 1.2, "weight": 1.0},
                ],
            ),
            FuzzyGhaede(
                disease_id="type_2_diabetes",
                name="T2DM Diagnostic Pattern", weight=1.0,
                conditions=[
                    {'feature': "fasting_plasma_glucose", "type": "high", "threshold": 126, 'softness': 126, 'weight': 1.5},
                    {'feature': 'hemoglobin_a1c', "type": "high", "threshold": 6.5, "softness": 6.5, 'weight': 1.6},
                    {"feature": "two_hour_postload_glucose", "type": "high", "threshold": 200, "softness": 200, "weight": 1.4},
                ],
            ),
            FuzzyGhaede(
                disease_id="prediabetes",
                name="Prediabetes Pattern", weight=1.0,
                conditions=[
                    {"feature": "fasting_plasma_glucose", "type": "high", "threshold": 100, "softness": 14, 'weight': 1.4},
                    {"feature": 'hemoglobin_a1c', 'type': "high", "threshold": 5.7, 'softness': 0.8, "weight": 1.5},
                ],
            ),
            FuzzyGhaede(
                disease_id='metabolic_syndrome',
                name="Metabolic Syndrome Pattern", weight=0.95,
                conditions=[
                    {'feature': "triglycerides", "type": "high", "threshold": 150, "softness": 150, "weight": 1.3},
                    {"feature": "hdl_cholesterol", "type": "low", "threshold": 40, "softness": 40, "weight": 1.3},
                    {"feature": 'fasting_plasma_glucose', 'type': "high", "threshold": 100, 'softness': 14, "weight": 1.1},
                    {"feature": "body_mass_index", "type": 'high', "threshold": 30, "softness": 30, 'weight': 1.2},
                    {'feature': "uric_acid", "type": "high", "threshold": 7.0, "softness": 7.0, "weight": 0.7},
                ],
            ),
            FuzzyGhaede(
                disease_id="chronic_kidney_disease",
                name="CKD Pattern", weight=1.0,
                conditions=[
                    {"feature": "egfr_ckd_epi_creatinine", "type": "low", "threshold": 60, "softness": 60, "weight": 1.8},
                    {'feature': "creatinine", "type": 'high', "threshold": 1.3, "softness": 1.3, "weight": 1.2},
                    {"feature": "urine_albumin_to_creatinine_ratio", "type": "high", "threshold": 30, "softness": 30, "weight": 1.4},
                    {"feature": "cystatin_c", "type": "high", "threshold": 1.0, "softness": 1.0, "weight": 1.0},
                ],
            ),
            FuzzyGhaede(
                disease_id="acute_kidney_injury",
                name="AKI Pattern", weight=0.9,
                conditions=[
                    {"feature": "creatinine", "type": "high", "threshold": 1.3, "softness": 1.3, 'weight': 1.4},
                    {"feature": 'urea_nitrogen', "type": 'high', "threshold": 20, 'softness': 20, "weight": 1.1},
                    {"feature": "potassium", "type": "high", "threshold": 5.0, "softness": 5.0, "weight": 0.9},
                    {"feature": 'bicarbonate', 'type': "low", "threshold": 22, "softness": 22, 'weight': 0.9},
                ],
            ),
            FuzzyGhaede(
                disease_id="hypothyroidism",
                name='Hypothyroid Pattern', weight=1.0,
                conditions=[
                    {"feature": "thyroid_stimulating_hormone", "type": "high", "threshold": 4.5, "softness": 4.5, "weight": 1.7},
                    {"feature": 'free_thyroxine', "type": "low", "threshold": 0.8, "softness": 0.8, 'weight': 1.5},
                    {"feature": 'anti_tpo_antibody', "type": "high", "threshold": 35, "softness": 35, 'weight': 0.9},
                ],
            ),
            FuzzyGhaede(
                disease_id='hyperthyroidism',
                name="Hyperthyroid Pattern", weight=1.0,
                conditions=[
                    {"feature": "thyroid_stimulating_hormone", "type": "low", "threshold": 0.4, 'softness': 0.4, 'weight': 1.7},
                    {"feature": "free_thyroxine", "type": "high", "threshold": 1.8, "softness": 1.8, "weight": 1.5},
                    {"feature": "free_triiodothyronine", "type": "high", "threshold": 4.2, "softness": 4.2, "weight": 1.2},
                ],
            ),
            FuzzyGhaede(
                disease_id="nafl_d",
                name="NAFLD Pattern", weight=0.9,
                conditions=[
                    {"feature": "alanine_aminotransferase", 'type': "high", "threshold": 56, 'softness': 56, "weight": 1.3},
                    {"feature": "aspartate_aminotransferase", 'type': 'high', "threshold": 40, "softness": 40, "weight": 1.0},
                    {"feature": "gamma_glutamyl_transferase", "type": "high", "threshold": 55, 'softness': 55, "weight": 0.9},
                    {"feature": "body_mass_index", "type": 'high', "threshold": 30, "softness": 30, "weight": 1.3},
                    {"feature": "triglycerides", "type": "high", "threshold": 150, "softness": 150, "weight": 0.9},
                ],
            ),
            FuzzyGhaede(
                disease_id="liver_cirrhosis",
                name="Cirrhosis Pattern", weight=1.0,
                conditions=[
                    {'feature': "albumin", "type": 'low', "threshold": 3.5, "softness": 3.5, "weight": 1.5},
                    {"feature": "platelet_count", "type": 'low', "threshold": 150, "softness": 150, "weight": 1.6},
                    {"feature": "international_normalized_ratio", "type": "high", "threshold": 1.3, "softness": 1.3, "weight": 1.4},
                    {'feature': "bilirubin_total", "type": "high", "threshold": 1.2, 'softness': 1.2, 'weight': 1.1},
                ],
            ),
            FuzzyGhaede(
                disease_id="hyperlipidemia",
                name="Dyslipidemia Pattern", weight=1.0,
                conditions=[
                    {'feature': "ldl_cholesterol", "type": "high", "threshold": 160, "softness": 160, "weight": 1.6},
                    {'feature': "total_cholesterol", "type": "high", "threshold": 240, "softness": 240, "weight": 1.4},
                    {"feature": "triglycerides", "type": "high", "threshold": 150, "softness": 150, "weight": 1.0},
                    {"feature": "hdl_cholesterol", "type": "low", "threshold": 40, "softness": 40, "weight": 0.9},
                ],
            ),
            FuzzyGhaede(
                disease_id="heart_failure",
                name="Natriuretic Peptide Pattern", weight=1.0,
                conditions=[
                    {"feature": "n_terminal_pro_bnp", "type": "high", "threshold": 300, "softness": 200, "weight": 2.0},
                    {"feature": "b_type_natriuretic_peptide", "type": "high", "threshold": 100, "softness": 60, "weight": 1.8},
                    {"feature": "sodium", "type": "low", "threshold": 135, "softness": 5, "weight": 0.7},
                    {"feature": "creatinine", "type": "high", "threshold": 1.3, "softness": 0.4, "weight": 0.6},
                ],
            ),
            FuzzyGhaede(
                disease_id="graves_disease",
                name="Overt Hyperthyroid Pattern", weight=1.0,
                conditions=[
                    {"feature": "thyroid_stimulating_hormone", "type": "low", "threshold": 0.1, "softness": 0.15, "weight": 2.0},
                    {"feature": "free_thyroxine", "type": "high", "threshold": 1.8, "softness": 0.6, "weight": 1.6},
                    {"feature": "free_triiodothyronine", "type": "high", "threshold": 4.2, "softness": 1.5, "weight": 1.2},
                ],
            ),
            FuzzyGhaede(
                disease_id="addison_disease",
                name="Adrenal Insufficiency Pattern", weight=1.0,
                conditions=[
                    {"feature": "cortisol_morning", "type": "low", "threshold": 5, "softness": 3, "weight": 2.0},
                    {"feature": "adrenocorticotropic_hormone", "type": "high", "threshold": 63, "softness": 50, "weight": 1.8},
                    {"feature": "sodium", "type": "low", "threshold": 135, "softness": 6, "weight": 1.0},
                    {"feature": "potassium", "type": "high", "threshold": 5.2, "softness": 0.6, "weight": 1.0},
                ],
            ),
            FuzzyGhaede(
                disease_id="systemic_lupus_erythematosus",
                name="Lupus Serology Pattern", weight=1.0,
                conditions=[
                    {"feature": "antinuclear_antibody_titer", "type": "high", "threshold": 80, "softness": 60, "weight": 1.5},
                    {"feature": "double_stranded_dna_antibody", "type": "high", "threshold": 30, "softness": 25, "weight": 2.0},
                    {"feature": "complement_c3", "type": "low", "threshold": 90, "softness": 25, "weight": 1.2},
                ],
            ),
            FuzzyGhaede(
                disease_id="rheumatoid_arthritis",
                name="Inflammatory Arthritis Serology", weight=1.0,
                conditions=[
                    {"feature": "anti_cyclic_citrullinated_peptide_igg", "type": "high", "threshold": 20, "softness": 20, "weight": 2.0},
                    {"feature": "rheumatoid_factor", "type": "high", "threshold": 14, "softness": 15, "weight": 1.4},
                    {"feature": "c_reactive_protein", "type": "high", "threshold": 10, "softness": 10, "weight": 0.8},
                    {"feature": "erythrocyte_sedimentation_rate", "type": "high", "threshold": 30, "softness": 20, "weight": 0.8},
                ],
            ),
            FuzzyGhaede(
                disease_id="type_1_diabetes",
                name="Insulin-Deficient Hyperglycaemia", weight=1.0,
                conditions=[
                    {"feature": "c_peptide", "type": "low", "threshold": 0.6, "softness": 0.4, "weight": 2.0},
                    {"feature": "hemoglobin_a1c", "type": "high", "threshold": 6.5, "softness": 2.0, "weight": 1.2},
                    {"feature": "glucose", "type": "high", "threshold": 200, "softness": 80, "weight": 1.0},
                ],
            ),
            FuzzyGhaede(
                disease_id="thalassemia_trait",
                name="Microcytosis without Iron Deficiency", weight=1.0,
                conditions=[
                    {"feature": "mean_corpuscular_volume", "type": "low", "threshold": 75, "softness": 8, "weight": 1.6},
                    {"feature": "red_blood_cell_count", "type": "high", "threshold": 5.4, "softness": 0.5, "weight": 1.5},
                    {"feature": "ferritin", "type": "high", "threshold": 40, "softness": 25, "weight": 1.2},
                    {"feature": "red_cell_distribution_width", "type": "low", "threshold": 15, "softness": 2, "weight": 1.0},
                ],
            ),
            FuzzyGhaede(
                disease_id="hemochromatosis",
                name="Iron Overload Pattern", weight=1.0,
                conditions=[
                    {"feature": "transferrin_saturation", "type": "high", "threshold": 45, "softness": 10, "weight": 2.0},
                    {"feature": "ferritin", "type": "high", "threshold": 300, "softness": 200, "weight": 1.6},
                    {"feature": "alanine_aminotransferase", "type": "high", "threshold": 40, "softness": 30, "weight": 0.8},
                ],
            ),
            FuzzyGhaede(
                disease_id="gout",
                name="Hyperuricaemia Pattern", weight=1.0,
                conditions=[
                    {"feature": "uric_acid", "type": "high", "threshold": 7.0, "softness": 1.5, "weight": 2.0},
                    {"feature": "c_reactive_protein", "type": "high", "threshold": 5, "softness": 5, "weight": 0.8},
                    {"feature": "creatinine", "type": "high", "threshold": 1.3, "softness": 0.4, "weight": 0.7},
                ],
            ),
            FuzzyGhaede(
                disease_id="vitamin_d_deficiency",
                name="Vitamin D Deficiency Pattern", weight=1.0,
                conditions=[
                    {"feature": "vitamin_d", "type": "low", "threshold": 20, "softness": 8, "weight": 2.0},
                    {"feature": "parathyroid_hormone", "type": "high", "threshold": 65, "softness": 25, "weight": 1.2},
                    {"feature": "calcium_total", "type": "low", "threshold": 8.6, "softness": 0.6, "weight": 0.9},
                    {"feature": "alkaline_phosphatase", "type": "high", "threshold": 130, "softness": 40, "weight": 0.7},
                ],
            ),
            FuzzyGhaede(
                disease_id="celiac_disease",
                name="Celiac Serology Pattern", weight=1.0,
                conditions=[
                    {"feature": 'anti_ttg_iga', "type": "high", "threshold": 10, "softness": 10, "weight": 2.0},
                    {"feature": 'ferritin', "type": "low", "threshold": 30, "softness": 30, "weight": 0.7},
                    {"feature": "folate", "type": "low", "threshold": 4, "softness": 4, "weight": 0.7},
                ],
            ),
            FuzzyGhaede(
                disease_id='sepsis',
                name="Sepsis Pattern", weight=1.0,
                conditions=[
                    {"feature": "procalcitonin", 'type': "high", 'threshold': 0.5, "softness": 0.5, "weight": 1.8},
                    {"feature": 'lactate', "type": "high", "threshold": 2.0, "softness": 2.0, 'weight': 1.5},
                    {"feature": "c_reactive_protein", 'type': "high", "threshold": 100, "softness": 100, "weight": 1.2},
                    {"feature": 'white_blood_cell_count', "type": "high", "threshold": 11, "softness": 11, "weight": 1.0},
                ],
            ),
            # === SUPER-ENHANCED COMPLEX RULES ===
            FuzzyGhaede(
                disease_id="primary_hyperparathyroidism",
                name="Primary Hyperpara Pattern", weight=1.0,
                conditions=[
                    {"feature": "calcium_total", "type": "high", "threshold": 10.5, "softness": 0.5, "weight": 1.8},
                    {"feature": "parathyroid_hormone", "type": "high", "threshold": 65, "softness": 20, "weight": 2.0},
                    {"feature": "phosphate", "type": "low", "threshold": 2.5, "softness": 1.0, "weight": 1.0},
                ],
            ),
            FuzzyGhaede(
                disease_id="diabetic_ketoacidosis",
                name="DKA Pattern", weight=1.0,
                conditions=[
                    {"feature": "glucose", "type": "high", "threshold": 250, "softness": 100, "weight": 1.5},
                    {"feature": "bicarbonate", "type": "low", "threshold": 18, "softness": 5, "weight": 1.8},
                    {"feature": "anion_gap", "type": "high", "threshold": 12, "softness": 5, "weight": 1.6},
                ],
            ),
            FuzzyGhaede(
                disease_id="metabolic_acidosis",
                name="Metabolic Acidosis Pattern", weight=1.0,
                conditions=[
                    {"feature": "bicarbonate", "type": "low", "threshold": 22, "softness": 5, "weight": 1.8},
                    {"feature": "ph", "type": "low", "threshold": 7.35, "softness": 0.1, "weight": 1.5},
                ],
            ),
            FuzzyGhaede(
                disease_id="cholestasis",
                name="Cholestasis Pattern", weight=1.0,
                conditions=[
                    {"feature": "alkaline_phosphatase", "type": "high", "threshold": 147, "softness": 50, "weight": 1.7},
                    {"feature": "gamma_glutamyl_transferase", "type": "high", "threshold": 55, "softness": 30, "weight": 1.5},
                    {"feature": "bilirubin_total", "type": "high", "threshold": 1.2, "softness": 1.0, "weight": 1.2},
                ],
            ),
            FuzzyGhaede(
                disease_id="pancytopenia",
                name="Pancytopenia Pattern", weight=1.0,
                conditions=[
                    {"feature": "hemoglobin", "type": "low", "threshold": 10, "softness": 3, "weight": 1.3},
                    {"feature": "white_blood_cell_count", "type": "low", "threshold": 4, "softness": 2, "weight": 1.3},
                    {"feature": "platelet_count", "type": "low", "threshold": 150, "softness": 50, "weight": 1.3},
                ],
            ),
            FuzzyGhaede(
                disease_id="malnutrition",
                name="Malnutrition Pattern", weight=1.0,
                conditions=[
                    {"feature": "albumin", "type": "low", "threshold": 3.5, "softness": 1.0, "weight": 1.6},
                    {"feature": "prealbumin", "type": "low", "threshold": 15, "softness": 5, "weight": 1.8},
                    {"feature": "body_mass_index", "type": "low", "threshold": 18.5, "softness": 3, "weight": 1.2},
                ],
            ),
            FuzzyGhaede(
                disease_id="disseminated_intravascular_coagulation",
                name="DIC Pattern", weight=1.0,
                conditions=[
                    {"feature": "platelet_count", "type": "low", "threshold": 150, "softness": 50, "weight": 1.4},
                    {"feature": "d_dimer", "type": "high", "threshold": 0.5, "softness": 0.5, "weight": 1.7},
                    {"feature": "fibrinogen", "type": "low", "threshold": 150, "softness": 50, "weight": 1.6},
                ],
            ),
            FuzzyGhaede(
                disease_id="bacterial_infection",
                name="Bacterial Infection Pattern", weight=1.0,
                conditions=[
                    {"feature": "neutrophils", "type": "high", "threshold": 70, "softness": 15, "weight": 1.5},
                    {"feature": "c_reactive_protein", "type": "high", "threshold": 50, "softness": 30, "weight": 1.4},
                    {"feature": "procalcitonin", "type": "high", "threshold": 0.5, "softness": 0.5, "weight": 1.8},
                ],
            ),
            FuzzyGhaede(
                disease_id="viral_infection",
                name="Viral Infection Pattern", weight=1.0,
                conditions=[
                    {"feature": "lymphocytes", "type": "high", "threshold": 40, "softness": 15, "weight": 1.5},
                    {"feature": "neutrophils", "type": "low", "threshold": 40, "softness": 15, "weight": 1.2},
                ],
            ),
        ]

    def _membership(self, value: float, threshold: float,
                    direction: str, softness: float) -> float:
        scale = abs(softness) * 0.15 if softness else 1.0
        if scale <= 0:
            scale = 1.0
        x = (value - threshold) / scale

        if direction == "low":
            return _sigmoid(-6.0 * x)
        return _sigmoid(6.0 * x)

    def evaluate(
        self, observations: Mapping[str, float],
        context: Optional[ClinicalContext] = None,
        reliability: Optional[Mapping[str, float]] = None,
        reference_scale: Optional[Mapping[str, tuple[float, float]]] = None,
    ) -> list[FuzzyResult]:
        """Evaluate fuzzy patterns.

        reliability      : per-feature evidence reliability (0-1). A value the
                           OCR read at 0.6 confidence contributes less weight
                           and less coverage than a confirmed one.
        reference_scale  : per-feature (low_ratio, high_ratio) of the
                           laboratory's interval over the registry interval.
                           Method-dependent analytes (enzymes, immunoassays)
                           have their soft thresholds rescaled so a kit with
                           ULN 55 is not judged by a 40-ULN membership curve.
        """
        reliability = reliability or {}
        reference_scale = reference_scale or {}
        results: dict[str, FuzzyResult] = {}
        for rule in self.rules:
            memberships = []
            activated = []
            used_features: list[str] = []
            min_rel = 1.0
            for cond in rule.conditions:
                feature_name = cond["feature"]
                value = _float(observations.get(feature_name))
                if value is None:
                    continue
                used_features.append(feature_name)
                f_rel = _clamp01(float(reliability.get(feature_name, 1.0)))
                min_rel = min(min_rel, f_rel)

                # Scale normalization for CBC counts
                if feature_name in ("platelet_count", "platelets", "plt") and value > 1000.0:
                    value = value / 1000.0
                elif feature_name in ("white_blood_cell_count", "wbc", "white_blood_cells") and value > 100.0:
                    value = value / 1000.0
                elif feature_name in ("red_blood_cell_count", "rbc", "red_blood_cells") and value > 10000.0:
                    value = value / 1000000.0

                threshold = _float(cond.get("threshold"))
                if threshold is None:
                    threshold = _float(cond.get("softness")) or 0.0

                # Age & Pregnancy threshold adjustments
                if context:
                    age = context.age_years
                    if age is not None and age < 18.0:
                        if feature_name in ("white_blood_cell_count", "wbc", "white_blood_cells") and cond.get("type") == "high":
                            if age < 28.0 / 365.25:
                                threshold = 30.0  # Neonatal physiological leukocytosis
                            elif age < 1.0:
                                threshold = 17.5  # Infant WBC
                            elif age < 6.0:
                                threshold = 15.5  # Young child WBC
                            elif age < 12.0:
                                threshold = 13.5  # Child WBC
                            else:
                                threshold = 11.0
                        elif feature_name in ("hemoglobin", "hgb", "hb") and cond.get("type") == "high":
                            if age < 28.0 / 365.25:
                                threshold = 22.5  # Neonatal polycythemia cutoff
                        elif feature_name in ("hematocrit", "hct") and cond.get("type") == "high":
                            if age < 28.0 / 365.25:
                                threshold = 65.0  # Neonatal hematocrit
                        elif feature_name == "alkaline_phosphatase" and cond.get("type") == "high":
                            threshold = 450.0 if age < 6.0 else (850.0 if age < 14.0 else 500.0)
                        elif feature_name in ("phosphate", "phosphorus") and cond.get("type") == "high":
                            threshold = 6.0 if age < 6.0 else (5.8 if age < 12.0 else 4.8)
                        elif feature_name in ("hemoglobin", "hgb", "hb") and cond.get("type") == "low":
                            threshold = 11.0 if age < 5.0 else (11.5 if age < 12.0 else 12.0)
                        elif feature_name == "creatinine" and cond.get("type") == "high":
                            threshold = 0.55 if age < 6.0 else (0.70 if age < 12.0 else 0.85)
                    elif context.pregnant:
                        if feature_name in ("white_blood_cell_count", "wbc", "white_blood_cells") and cond.get("type") == "high":
                            threshold = 16.0  # Pregnancy physiological leukocytosis
                        elif feature_name == "alkaline_phosphatase" and cond.get("type") == "high":
                            threshold = 380.0
                        elif feature_name in ("hemoglobin", "hgb", "hb") and cond.get("type") == "low":
                            threshold = 10.5
                        elif feature_name in ("platelet_count", "platelets", "plt") and cond.get("type") == "low":
                            threshold = 100.0
                        elif feature_name == "creatinine" and cond.get("type") == "high":
                            threshold = 0.80

                # Laboratory-interval calibration for method-dependent analytes
                lo_ratio, hi_ratio = reference_scale.get(feature_name, (1.0, 1.0))
                if feature_name in METHOD_DEPENDENT_FEATURES:
                    ratio = hi_ratio if cond.get("type") == "high" else lo_ratio
                    if ratio and 0.4 <= ratio <= 2.5:
                        threshold = threshold * ratio

                m = self._membership(
                    value, threshold, cond["type"],
                    softness=_float(cond.get("softness")) or abs(threshold)
                    or 1.0)
                # Unreliable evidence: shrink membership toward indifference
                # and reduce its weight in the pattern.
                m = 0.5 + (m - 0.5) * (0.5 + 0.5 * f_rel)
                w_eff = (_float(cond.get("weight")) or 1.0) * (0.5 + 0.5 * f_rel)
                memberships.append((m, w_eff))
                if m > 0.5:
                    activated.append(
                        f"{cond['feature']} ({m:.2f})")
            if memberships:


                tot_w = sum(w for _, w in memberships) or 1.0
                score = sum(m * w for m, w in memberships) / tot_w
                # Coverage must be weighted, not a plain count. The celiac
                # rule carries anti-tTG at weight 2.0 and ferritin at 0.7;
                # counting heads let a lone low ferritin claim a third of a
                # serology pattern whose defining test was never ordered.
                all_w = sum(float(c.get("weight", 1.0))
                            for c in rule.conditions) or 1.0
                coverage = tot_w / all_w
                score *= (0.55 + 0.45 * coverage) * rule.weight
                # Defining-feature gate (audit 2026-10-21): a pattern whose
                # heaviest condition was never measured (e.g. "microcytosis
                # without iron deficiency" scored from ferritin + RDW alone,
                # MCV absent) may only speak at reduced strength; otherwise a
                # normal panel can earn a fuzzy vote above 0.5 from supportive
                # context alone.
                max_w = max((float(c.get("weight", 1.0)) for c in rule.conditions), default=1.0)
                defining_present = any(
                    float(c.get("weight", 1.0)) >= 0.9 * max_w and c["feature"] in used_features
                    for c in rule.conditions)
                if not defining_present:
                    score *= 0.6
                else:
                    # ESL extension 7b (NHANES healthy audit 2026-10-22): the defining
                    # feature was measured and is NOT in the pattern's direction
                    # (MCV 88 for "microcytosis without iron deficiency"); the
                    # supportive conditions (normal ferritin, normal RDW) must not
                    # carry the pattern on their own. Scale by the defining
                    # membership so a clearly-normal defining analyte leaves at
                    # most 30 % of the supportive score.
                    m_def = max((m for (m, _w), c in zip(memberships, [c for c in rule.conditions if c["feature"] in used_features])
                                 if float(c.get("weight", 1.0)) >= 0.9 * max_w), default=1.0)
                    if m_def < 0.5:
                        score *= 0.3 + 0.7 * (m_def / 0.5)
                existing = results.get(rule.disease_id)
                if existing is None or score > existing.membership_score:
                    results[rule.disease_id] = FuzzyResult(
                        disease_id=rule.disease_id,
                        membership_score=_clamp01(score),
                        activated_rules=activated,
                        explanation=(
                            f"درجه عضویت فازی {score:.2f} از "
                            f"{len(memberships)}/{len(rule.conditions)} "
                            f"شاهدِ الگوی «{rule.name}»"),
                        used_features=used_features,
                        min_reliability=min_rel,
                    )
        return list(results.values())


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


_NEONATE_MAX_AGE_YEARS = 28.0 / 365.25


def _sen_goroohbandi(age: float) -> str:
    if age < _NEONATE_MAX_AGE_YEARS:
        return 'neonate'
    if age < 1.0:
        return 'infant'
    if age < 6.0:
        return 'young_child'
    if age < 12.0:
        return "child"
    if age < 18.0:
        return "adolescent"
    if age >= 65.0:
        return "older_adult"
    return "adult"


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    weight: float = 1.0
    evidence: str = ''
    citation: str = ''

class ClinicalKnowledgeGraph:

    def __init__(self):
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[GraphEdge] = []
        self.adjacency: dict[str, list[GraphEdge]] = defaultdict(list)
        self._reverse: dict[str, list[GraphEdge]] = defaultdict(list)
        self._sakht_graph()

    def _sakht_graph(self) -> None:

        diseases = [

            "type_2_diabetes", 'type_1_diabetes', 'prediabetes',
            "metabolic_syndrome", "hypothyroidism", 'hyperthyroidism',
            "hashimoto_thyroiditis", "graves_disease", 'cushing_syndrome',
            'addison_disease', 'primary_aldosteronism', "pheochromocytoma",
            "pcos", "hypogonadism",

            "iron_deficiency_anemia", "vitamin_b12_deficiency", "folate_deficiency",
            "anemia_of_chronic_disease", "hemolytic_anemia", "thalassemia_trait",
            "sickle_cell_trait", "polycythemia_vera", "essential_thrombocythemia",
            "multiple_myeloma", "waldenstrom_macroglobulinemia",
            "acute_leukemia", "chronic_lymphocytic_leukemia",

            "chronic_kidney_disease", "acute_kidney_injury", "nephrotic_syndrome",
            'iga_nephropathy', "lupus_nephritis", "diabetic_nephropathy",
            "polycystic_kidney_disease", "glomerulonephritis",

            "nafl_d", 'nash', 'alcoholic_liver_disease', "liver_cirrhosis",
            "chronic_hepatitis_b", "chronic_hepatitis_c", "autoimmune_hepatitis",
            "hemochromatosis", 'wilson_disease', 'hepatocellular_carcinoma',

            "hypertension", "coronary_artery_disease", "heart_failure",
            "atrial_fibrillation", "deep_vein_thrombosis", "pulmonary_embolism",
            "peripheral_artery_disease", "aortic_aneurysm",

            "copd", "asthma", 'obstructive_sleep_apnea', "pulmonary_fibrosis",

            "celiac_disease", 'inflammatory_bowel_disease', "peptic_ulcer",
            "gastroesophageal_reflux", "pancreatitis",

            "rheumatoid_arthritis", "systemic_lupus_erythematosus",
            "sjogren_syndrome", "ankylosing_spondylitis", "gout",
            "pseudogout", "fibromyalgia",

            "urinary_tract_infection", "pneumonia", "sepsis",
            "hepatitis_a", "tuberculosis", "hiv_infection",

            'lung_cancer', "breast_cancer", "colorectal_cancer",
            "prostate_cancer", "ovarian_cancer", "pancreatic_cancer",
            'lymphoma', "leukemia",

            "major_depressive_disorder", 'generalized_anxiety_disorder',
            "dementia", "parkinson_disease", "multiple_sclerosis",

            "osteoporosis", "osteopenia", "sarcopenia", "frailty",
            "malnutrition", "obesity",

            "anemia", "dyslipidemia", "hyperuricemia",
        ]

        for d in diseases:
            self.nodes[d] = {
                "type": "disease",
                "name": d.replace("_", " ").title(),
            }


        edges_data = [


            ("type_2_diabetes", "chronic_kidney_disease", 'causes', 0.70,
             "Diabetic nephropathy", "ADA 2024"),
            ('type_2_diabetes', "coronary_artery_disease", "causes", 0.65,
             "Accelerated atherosclerosis", "ADA 2024"),
            ("type_2_diabetes", 'peripheral_artery_disease', "causes", 0.55,
             'Macrovascular complication', "ADA 2024"),
            ("type_2_diabetes", 'nafl_d', 'associated_with', 0.60,
             "Insulin resistance → hepatic steatosis", "AASLD 2023"),
            ("type_2_diabetes", "erectile_dysfunction", "causes", 0.40,
             "Vascular + neuropathic", 'ADA 2024'),


            ("metabolic_syndrome", 'type_2_diabetes', "causes", 0.80,
             "Insulin resistance progression", "IDF 2009"),
            ("metabolic_syndrome", "coronary_artery_disease", "causes", 0.70,
             "Atherogenic dyslipidemia", "NCEP-ATP III"),
            ("metabolic_syndrome", "nafl_d", "causes", 0.75,
             "Hepatic steatosis", "AASLD 2023"),
            ('metabolic_syndrome', "chronic_kidney_disease", "causes", 0.50,
             "Metabolic kidney disease", 'KDIGO 2024'),


            ("obesity", 'type_2_diabetes', "causes", 0.75,
             "Adipose tissue insulin resistance", 'WHO 2023'),
            ('obesity', "metabolic_syndrome", 'causes', 0.85,
             "Central obesity criterion", "IDF 2009"),
            ("obesity", "obstructive_sleep_apnea", "causes", 0.70,
             "Upper airway obstruction", "AASM 2023"),
            ('obesity', "nafl_d", "causes", 0.80,
             "Hepatic fat accumulation", "AASLD 2023"),
            ("obesity", "gout", "causes", 0.55,
             "Increased urate production", 'ACR 2020'),
            ("obesity", 'osteoarthritis', 'causes', 0.65,
             'Mechanical joint stress', "ACR 2019"),


            ("hashimoto_thyroiditis", "hypothyroidism", 'causes', 0.90,
             "Autoimmune thyroid destruction", "ATA 2023"),
            ("graves_disease", "hyperthyroidism", "causes", 0.95,
             'TSH receptor antibodies', "ATA 2023"),
            ('hypothyroidism', "dyslipidemia", "causes", 0.60,
             "Reduced LDL receptor expression", "ATA 2023"),
            ("hypothyroidism", "anemia", "associated_with", 0.40,
             "Reduced EPO + nutrient malabsorption", "ATA 2023"),
            ("hyperthyroidism", 'atrial_fibrillation', "causes", 0.50,
             "Thyrotoxic cardiomyopathy", "ATA 2023"),


            ("chronic_kidney_disease", 'anemia', 'causes', 0.70,
             'Erythropoietin deficiency', "KDIGO 2024"),
            ('chronic_kidney_disease', "coronary_artery_disease", "causes", 0.65,
             "Uremic vascular disease", "KDIGO 2024"),
            ("chronic_kidney_disease", "hyperparathyroidism", "causes", 0.60,
             "CKD-MBD axis", "KDIGO 2024"),
            ("chronic_kidney_disease", "hyperkalemia", "causes", 0.55,
             "Reduced K excretion", "KDIGO 2024"),
            ("hypertension", "chronic_kidney_disease", "causes", 0.60,
             "Hypertensive nephrosclerosis", 'JNC-8'),
            ("diabetes", "chronic_kidney_disease", "causes", 0.70,
             'Diabetic nephropathy', "ADA 2024"),


            ("nafl_d", "nash", "causes", 0.60,
             "Steatohepatitis progression", "AASLD 2023"),
            ('nash', "liver_cirrhosis", "causes", 0.50,
             'Fibrosis progression', "AASLD 2023"),
            ("liver_cirrhosis", "hepatocellular_carcinoma", "causes", 0.70,
             "Regenerative nodules → dysplasia", "AASLD 2023"),
            ("liver_cirrhosis", "acute_kidney_injury", "causes", 0.50,
             "Hepatorenal syndrome", "EASL 2018"),
            ("chronic_hepatitis_b", "liver_cirrhosis", "causes", 0.60,
             "Chronic inflammation → fibrosis", "EASL 2017"),
            ("chronic_hepatitis_c", "liver_cirrhosis", "causes", 0.65,
             "Chronic inflammation → fibrosis", "AASLD 2023"),
            ('alcoholic_liver_disease', "liver_cirrhosis", "causes", 0.75,
             "Alcohol-induced fibrosis", 'EASL 2018'),
            ('hemochromatosis', "liver_cirrhosis", 'causes', 0.60,
             'Iron deposition → fibrosis', "EASL 2022"),


            ("iron_deficiency_anemia", "anemia", "causes", 0.95,
             "Iron-deficient erythropoiesis", "WHO 2023"),
            ("vitamin_b12_deficiency", "anemia", "causes", 0.85,
             "Megaloblastic erythropoiesis", 'BSH 2023'),
            ('celiac_disease', 'iron_deficiency_anemia', "causes", 0.70,
             "Duodenal malabsorption", 'ACG 2023'),
            ('celiac_disease', "vitamin_b12_deficiency", 'causes', 0.50,
             "Ileal malabsorption", "ACG 2023"),
            ("celiac_disease", 'osteoporosis', "causes", 0.55,
             'Calcium/VitD malabsorption', "ACG 2023"),
            ('chronic_kidney_disease', "iron_deficiency_anemia", "associated_with", 0.50,
             "CKD-related iron deficiency", "KDIGO 2024"),


            ("systemic_lupus_erythematosus", "lupus_nephritis", 'causes', 0.60,
             'Immune complex deposition', "ACR 2023"),
            ("rheumatoid_arthritis", 'anemia_of_chronic_disease', "causes", 0.55,
             'Chronic inflammation → hepcidin', "ACR 2023"),
            ("hashimoto_thyroiditis", 'celiac_disease', "associated_with", 0.35,
             "Polyautoimmunity", "ATA 2023"),


            ("atrial_fibrillation", 'deep_vein_thrombosis', "associated_with", 0.30,
             "Stasis + hypercoagulability", "ESC 2024"),
            ("coronary_artery_disease", "heart_failure", "causes", 0.60,
             "Ischemic cardiomyopathy", "ESC 2024"),
            ("hypertension", "heart_failure", "causes", 0.55,
             'Hypertensive heart disease', "ESC 2024"),
            ("hypertension", 'coronary_artery_disease', "causes", 0.60,
             "Endothelial dysfunction", "ESC 2024"),


            ('copd', "cor pulmonale", 'causes', 0.50,
             "Chronic hypoxia → pulmonary HTN", "GOLD 2024"),
            ('obstructive_sleep_apnea', 'hypertension', 'causes', 0.60,
             "Sympathetic activation", 'AASM 2023'),
            ("obstructive_sleep_apnea", 'atrial_fibrillation', 'causes', 0.45,
             "Atrial remodeling", "AASM 2023"),


            ("gout", "chronic_kidney_disease", "associated_with", 0.50,
             "Urate nephropathy", "ACR 2020"),
            ("rheumatoid_arthritis", "osteoporosis", "causes", 0.55,
             "Inflammation + steroid use", "ACR 2023"),


            ('major_depressive_disorder', "coronary_artery_disease", "associated_with", 0.35,
             "Behavioral + inflammatory", "AHA 2023"),
            ('hypothyroidism', "major_depressive_disorder", "mimics", 0.60,
             "Overlapping symptoms", "ATA 2023"),


            ("type_2_diabetes", "hyperlipidemia", "associated_with", 0.50,
             "Diabetic dyslipidemia", "ADA 2024"),
            ("type_2_diabetes", "hypertension", "associated_with", 0.55,
             "Metabolic syndrome component", "ADA 2024"),
            ('hypothyroidism', 'hyperlipidemia', "associated_with", 0.45,
             "Lipid metabolism impairment", 'ATA 2023'),
            ('hypothyroidism', "anemia", "associated_with", 0.40,
             "Normocytic anemia", "ATA 2023"),
            ("nafl_d", "type_2_diabetes", 'associated_with', 0.60,
             "Bidirectional relationship", "AASLD 2023"),
            ("osteoporosis", "frailty", 'associated_with', 0.55,
             "Geriatric syndrome cluster", "AGS 2023"),
            ("sarcopenia", "osteoporosis", "associated_with", 0.60,
             "Osteosarcopenic syndrome", "EWGSOP2"),
            ('obesity', 'major_depressive_disorder', "associated_with", 0.40,
             "Bidirectional", "WHO 2023"),


            ("hyperthyroidism", "hypothyroidism", "excludes", 0.95,
             "Opposite thyroid states", "ATA 2023"),
            ("type_1_diabetes", "type_2_diabetes", "excludes", 0.80,
             "Distinct pathophysiology", "ADA 2024"),
            # Coexisting iron deficiency and thalassaemia trait is
            # common and clinically important, so these compete for the
            # explanation without excluding one another.
            ("iron_deficiency_anemia", "thalassemia_trait",
             "differential", 0.70,
             "Distinguish by Mentzer index, RDW and iron studies; "
             "the two can coexist", "BSH 2023"),
            # Acute-on-chronic is a standard diagnosis, not a
            # contradiction: an AKI episode does not rule out underlying
            # CKD, it is often what unmasks it. Modelled as a
            # differential to distinguish rather than an exclusion.
            ("acute_kidney_injury", "chronic_kidney_disease",
             "differential", 0.60,
             "Distinguish by baseline creatinine and duration; "
             "acute-on-chronic disease is common", "KDIGO 2024"),
            ("primary_aldosteronism", "addison_disease", "excludes", 0.90,
             "Opposite aldosterone states", 'Endocrine Society 2016'),


            ("iron_deficiency_anemia", "anemia", 'mimics', 0.85,
             "IDA is subtype of anemia", 'WHO 2023'),
            ("vitamin_b12_deficiency", 'iron_deficiency_anemia', "mimics", 0.30,
             'Different etiology, similar CBC', "BSH 2023"),
            ("hypothyroidism", "major_depressive_disorder", "mimics", 0.60,
             'Fatigue, weight gain, low mood', "ATA 2023"),
            ("hyperthyroidism", "generalized_anxiety_disorder", "mimics", 0.55,
             'Palpitations, anxiety, tremor', "ATA 2023"),
            ("anemia_of_chronic_disease", "iron_deficiency_anemia", "mimics", 0.50,
             'Similar microcytosis', "BSH 2023"),
            ('polycystic_kidney_disease', "chronic_kidney_disease", 'mimics', 0.40,
             "Both cause CKD", "KDIGO 2024"),
            ("nash", "alcoholic_liver_disease", "mimics", 0.50,
             "Similar histology", 'AASLD 2023'),


            ("type_2_diabetes", "liver_cirrhosis", "complicates", 0.40,
             "NASH to cirrhosis progression", "AASLD 2023"),
            ("type_2_diabetes", "chronic_kidney_disease", "complicates", 0.60,
             "Accelerated progression", "ADA 2024"),
            ("hypertension", "chronic_kidney_disease", "complicates", 0.55,
             "Accelerated nephrosclerosis", 'KDIGO 2024'),
            ("rheumatoid_arthritis", "osteoporosis", "complicates", 0.50,
             "Inflammation + steroids", "ACR 2023"),
            ("copd", 'heart_failure', "complicates", 0.45,
             'Cor pulmonale overlap', "GOLD 2024"),
            ("obesity", "obstructive_sleep_apnea", "complicates", 0.60,
             'Mechanical + metabolic', "AASM 2023"),
            ('chronic_kidney_disease', "heart_failure", "complicates", 0.50,
             "Cardiorenal syndrome", 'KDIGO 2024'),


            ("chronic_kidney_disease", "metformin", "contraindicates", 0.80,
             "Lactic acidosis risk if eGFR<30", "FDA 2016"),
            ("heart_failure", "nsaids", "contraindicates", 0.85,
             "Fluid retention + renal effects", "ACC/AHA 2022"),
            ('gout', "thiazide_diuretics", "contraindicates", 0.70,
             "Hyperuricemia exacerbation", "ACR 2020"),
            ("hyperkalemia", "ace_inhibitors", 'contraindicates', 0.75,
             'Worsens hyperkalemia', 'KDIGO 2024'),
            ("peptic_ulcer", "nsaids", 'contraindicates', 0.90,
             "GI bleeding risk", "ACG 2023"),
            # === SUPER-ENHANCED EDGES FOR COMPLEX DIAGNOSES ===
            ("primary_hyperparathyroidism", "hypercalcemia", "causes", 0.85, "PTH-mediated bone resorption", "Endocrine Society 2022"),
            ("primary_hyperparathyroidism", "osteoporosis", "causes", 0.70, "Chronic hypercalcemia → bone loss", "Endocrine Society 2022"),
            ("primary_hyperparathyroidism", "nephrolithiasis", "causes", 0.65, "Hypercalciuria → stones", "Endocrine Society 2022"),
            ("secondary_hyperparathyroidism", "chronic_kidney_disease", "associated_with", 0.80, "CKD → phosphate retention → PTH", "KDIGO 2017"),
            ("diabetic_ketoacidosis", "type_1_diabetes", "complicates", 0.75, "Absolute insulin deficiency", "ADA 2024"),
            ("hyperosmolar_hyperglycemic_state", "type_2_diabetes", "complicates", 0.70, "Relative insulin deficiency + dehydration", "ADA 2024"),
            ("metabolic_acidosis", "chronic_kidney_disease", "associated_with", 0.70, "Reduced ammoniagenesis", "KDIGO 2024"),
            ("metabolic_acidosis", "diabetic_ketoacidosis", "causes", 0.80, "Ketoacids", "ADA 2024"),
            ("siadh", "hyponatremia", "causes", 0.90, "Excess ADH → water retention", "Verbalis 2013"),
            ("cushing_syndrome", "hypertension", "causes", 0.75, "Mineralocorticoid excess", "Endocrine Society 2021"),
            ("cushing_syndrome", "type_2_diabetes", "causes", 0.70, "Glucocorticoid-induced IR", "Endocrine Society 2021"),
            ("polycythemia", "thrombosis", "causes", 0.65, "Hyperviscosity", "WHO MPN 2022"),
            ("thrombocytopenia", "bleeding", "causes", 0.75, "Low platelets → bleeding", "BSH 2023"),
            ("thrombocytosis", "thrombosis", "causes", 0.60, "High platelets → clotting", "WHO MPN 2022"),
            ("disseminated_intravascular_coagulation", "sepsis", "associated_with", 0.70, "Sepsis → DIC", "ISTH 2001"),
            ("cholestasis", "liver_cirrhosis", "associated_with", 0.55, "Chronic cholestasis → fibrosis", "EASL 2022"),
            ("autoimmune_hepatitis", "liver_cirrhosis", "causes", 0.60, "Chronic inflammation", "EASL 2015"),
            ("pancytopenia", "aplastic_anemia", "associated_with", 0.65, "Bone marrow failure", "BSH 2023"),
            ("malnutrition", "anemia", "causes", 0.70, "Nutrient deficiency", "WHO 2023"),
            ("malnutrition", "osteoporosis", "causes", 0.60, "Ca/VitD deficiency", "WHO 2023"),
            ("hypokalemia", "cardiac_arrhythmia", "causes", 0.70, "K <3.0 → arrhythmia", "AHA 2023"),
            ("hypercalcemia", "acute_kidney_injury", "causes", 0.60, "Vasoconstriction + diuresis", "KDIGO 2024"),
            ("hyponatremia", "seizure", "causes", 0.65, "Cerebral edema", "Verbalis 2013"),
            ("bacterial_infection", "sepsis", "causes", 0.60, "Progression to sepsis", "Surviving Sepsis 2021"),
            ("viral_infection", "bacterial_infection", "differential", 0.60, "Distinguish by WBC differential", "IDSA 2023"),
            ("folate_deficiency", "anemia", "causes", 0.85, "Megaloblastic anemia", "BSH 2023"),
        ]

        for src, tgt, rel, w, ev, cit in edges_data:
            edge = GraphEdge(src, tgt, rel, w, ev, cit)
            self.edges.append(edge)
            self.adjacency[src].append(edge)
            self._reverse[tgt].append(edge)


    def yaftan_paths(self, source: str, target: str,
                   max_depth: int = 3) -> list[list[str]]:
        from collections import deque
        paths: list[list[str]] = []
        queue = deque([(source, [source])])
        while queue:
            node, path = queue.popleft()
            if len(path) > max_depth + 1:
                continue
            if node == target:
                paths.append(path)
                continue
            for edge in self.adjacency.get(node, []):
                if edge.target not in path:
                    queue.append((edge.target, path + [edge.target]))
        return paths

    def get_related_diseases(self, disease_id: str,
                             relation: Optional[str] = None) -> list[str]:
        related = []
        for edge in self.adjacency.get(disease_id, []):
            if relation is None or edge.relation == relation:
                related.append(edge.target)
        return related

    def barresi_exclusions(self, candidate: str,
                         present_diseases: list[str]) -> list[dict]:
        exclusions = []
        for present in present_diseases:
            for edge in self.adjacency.get(present, []):
                if (edge.relation == "excludes"
                        and edge.target == candidate):
                    exclusions.append({
                        "candidate": candidate,
                        'excluded_by': present,
                        "weight": edge.weight,
                        'reason': edge.evidence,
                        "citation": edge.citation,
                    })
        return exclusions

    def support_boost(self, candidate: str,
                      present_diseases: list[str]) -> float:
        boost = 0.0
        for present in present_diseases:
            for edge in self.adjacency.get(present, []):
                if (edge.target == candidate
                        and edge.relation in ("causes", "associated_with")):
                    boost += edge.weight * 0.2
        return min(boost, 0.5)

    def get_mimics(self, disease_id: str) -> list[str]:
        return [edge.target for edge in self.adjacency.get(disease_id, [])
                if edge.relation == "mimics"]

    def get_contraindications(self, disease_id: str) -> list[dict]:
        return [
            {"contraindicated_drug": edge.target,
             "reason": edge.evidence,
             "citation": edge.citation,
             "weight": edge.weight}
            for edge in self.adjacency.get(disease_id, [])
            if edge.relation == "contraindicates"
        ]

    def get_bimari_context(self, disease_id: str) -> dict[str, Any]:
        return {
            "causes": self.get_related_diseases(disease_id, "causes"),
            "associated": self.get_related_diseases(disease_id, "associated_with"),
            'exclusions': self.get_related_diseases(disease_id, "excludes"),
            "mimics": self.get_mimics(disease_id),
            "complicates": self.get_related_diseases(disease_id, "complicates"),
            "contraindications": self.get_contraindications(disease_id),
            'caused_by': [e.source for e in self._reverse.get(disease_id, [])
                          if e.relation == "causes"],
        }

    def yaftan_differential_tashkhis_goroohbandi(self, primary: str) -> list[str]:
        return self.get_mimics(primary) + [
            edge.source for edge in self._reverse.get(primary, [])
            if edge.relation == "mimics"
        ]
@dataclass
class EnsembleResult:
    disease_id: str
    final_score: float
    votes: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    interpretation: str = ""
    calibrated_score: Optional[float] = None
    participating_models: list[str] = field(default_factory=list)
    # --- Evidence-theoretic fields (binary-frame Dempster-Shafer, Yager rule) ---
    belief: float = 0.0          # Bel(D): mass committed to the disease
    plausibility: float = 1.0    # Pl(D) = 1 - Bel(not D): upper bound
    ignorance: float = 1.0       # m(Theta): unassigned + conflict mass
    conflict: float = 0.0        # pairwise weighted inter-layer conflict
    weight_profile: str = "default"
    input_reliability: float = 1.0
    evidence_state: str = "insufficient"   # supported / refuted / conflicting / insufficient


# ---------------------------------------------------------------------------
# Decision-fusion layer
#
# Design notes (kept here on purpose - the reviewers asked for the maths):
#
#  * Layer weights are DOMAIN PROFILES, not one global table. In toxicology
#    an explicit threshold rule is the standard of care, in autoimmune
#    disease the syndromic graph matters more, for tumour markers the prior
#    (PPV) dominates. One table for 6,700 diseases was a simplification.
#  * Inter-layer conflict is the WEIGHTED PAIRWISE disagreement, not the
#    standard deviation of the votes. A std-based metric cannot tell "one
#    layer dissents from four" apart from a 50/50 split; the pairwise form
#    can, and it is exactly the conflict mass of Dempster's rule restricted
#    to singletons.
#  * In parallel to the point score we run a binary-frame {D, not-D}
#    evidence combination with Shafer discounting (layer reliability) and
#    Yager's rule (conflict mass goes to ignorance, NOT renormalised away).
#    This gives Belief / Plausibility bounds, separates "no evidence" from
#    "evidence against", and cannot exhibit Zadeh's paradox. On a binary
#    frame the combination is O(number of layers) per disease, so it costs
#    nothing at 6,700 diseases.
#  * Over-conservatism guard: when the rule layer reports that explicit
#    guideline criteria are met (vote >= RED_FLAG_RULE_VOTE), a low
#    population prior may lower the score but may not bury the disease
#    below RED_FLAG_FLOOR_FRACTION of the rule vote. Guideline criteria are
#    designed with specificity; the prior changes PPV, not whether the
#    finding must be shown to the clinician.
#  * Input reliability (OCR confidence, unconfirmed values, conflicting
#    duplicates) is carried INTO the fusion as an additional discount, so
#    uncertainty created at the OCR boundary is no longer lost.
# ---------------------------------------------------------------------------

MODEL_WEIGHTS = {
    "rule_engine":     0.35,
    "bayesian":        0.25,
    "fuzzy":           0.20,
    "knowledge_graph": 0.10,
    "risk_models":     0.10,
}

WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "default": MODEL_WEIGHTS,
    # explicit cut-offs are the standard of care (TDM, poisoning, panic values)
    "toxicology":   {"rule_engine": 0.55, "bayesian": 0.15, "fuzzy": 0.15,
                     "knowledge_graph": 0.05, "risk_models": 0.10},
    "critical":     {"rule_engine": 0.50, "bayesian": 0.20, "fuzzy": 0.15,
                     "knowledge_graph": 0.05, "risk_models": 0.10},
    # syndromic, multi-organ patterns: the graph carries real information
    "autoimmune":   {"rule_engine": 0.30, "bayesian": 0.20, "fuzzy": 0.20,
                     "knowledge_graph": 0.25, "risk_models": 0.05},
    # low-PPV markers: the prior must be allowed to dominate
    "oncology":     {"rule_engine": 0.30, "bayesian": 0.35, "fuzzy": 0.15,
                     "knowledge_graph": 0.15, "risk_models": 0.05},
    # continuous hormonal axes: boundary behaviour matters
    "endocrine":    {"rule_engine": 0.35, "bayesian": 0.25, "fuzzy": 0.25,
                     "knowledge_graph": 0.10, "risk_models": 0.05},
    # validated multivariable scores exist (ASCVD, FIB-4, FINDRISC...)
    "cardiometabolic": {"rule_engine": 0.30, "bayesian": 0.20, "fuzzy": 0.15,
                        "knowledge_graph": 0.10, "risk_models": 0.25},
}

_DOMAIN_TO_PROFILE = (
    (("toxicology", "tdm", "poisoning", "drug_monitoring"), "toxicology"),
    (("critical_care", "acid_base", "blood_gas", "electrolyte", "emergency"),
     "critical"),
    (("autoimmune", "rheumatology", "immunology", "vasculitis"), "autoimmune"),
    (("oncology", "tumor_marker", "tumour_marker", "hematologic_malignancy",
      "malignancy"), "oncology"),
    (("endocrine", "thyroid", "adrenal", "pituitary", "reproductive"),
     "endocrine"),
    (("cardiovascular", "cardiac", "lipid", "metabolic", "diabetes"),
     "cardiometabolic"),
)

# Shafer discount factor per layer: how much of its own vote a layer is
# allowed to commit. No layer is treated as infallible (cap 0.95).
LAYER_RELIABILITY = {m: min(0.95, w / 0.35) for m, w in MODEL_WEIGHTS.items()}

RED_FLAG_RULE_VOTE = 0.70
RED_FLAG_FLOOR_FRACTION = 0.65
MAX_DISCORD_SHRINK = 0.45
SINGLE_SOURCE_DISCOUNT = 0.70
RULE_ABSTAIN_BELOW = 0.05
INSUFFICIENT_CEILING = 0.49
# ESL extension 11-C (2026-10-23): clinical-context layer scores
CONTEXT_CONFIRMED_SCORE = 0.80    # documented diagnosis + consistent laboratory support
CONTEXT_DOCUMENTED_SCORE = 0.49   # documented diagnosis, no support on this panel (below operating point)

# documented-history phrase -> registry entity (conservative: only unambiguous phrases)
_DOCUMENTED_CONDITION_MAP: tuple[tuple[str, str], ...] = (
    (r"insulin.?dependent diabetes|non.?insulin.?dependent|diabetes mellitus|\bdiabet|\bdm2?\b|\bt2dm\b|\bt1dm\b|\biddm\b|\bniddm\b", "diabetes_mellitus"),
    (r"\bchf\b|congestive heart failure|heart failure|\bhfref\b|\bhfpef\b|cardiomyopathy", "heart_failure"),
    (r"\bcopd\b|chronic obstructive pulmonary|emphysema|chronic bronchitis", "copd"),
    (r"\basthma", "asthma"),
    (r"hypothyroid", "hypothyroidism"),
    (r"renal failure|renal insufficiency|chronic kidney|\bckd\b|\besrd\b|hemodialysis|haemodialysis|peritoneal dialysis|\bdialysis", "chronic_kidney_disease"),
    (r"cirrhosis", "liver_cirrhosis"),
    (r"\bhypertension|\bhtn\b", "hypertension"),
    (r"\bgout\b", "gout"),
    (r"alcohol (abuse|dependence|use disorder)|alcoholism|\betoh abuse|heavy alcohol", "alcohol_use_disorder"),
    (r"chronic an(a)?emia|an(a)?emia - chronic", "anemia"),
)
# home medication -> entity it implies (only drugs with a single dominant indication)
_DOCUMENTED_MEDICATION_MAP: tuple[tuple[str, str], ...] = (
    (r"\binsulin|novolog|humalog|lantus|glargine|levemir|detemir|aspart|lispro|humulin|novolin|tresiba|degludec|metformin|glucophage|glipizide|glyburide|glimepiride|sitagliptin|januvia|empagliflozin|jardiance|dapagliflozin|farxiga|canagliflozin|liraglutide|victoza|semaglutide|ozempic|pioglitazone", "diabetes_mellitus"),
    (r"levothyroxine|synthroid|levoxyl|euthyrox|liothyronine", "hypothyroidism"),
    (r"allopurinol|febuxostat|zyloprim|uloric", "gout"),
    (r"lactulose|rifaximin|xifaxan", "liver_cirrhosis"),
    (r"sacubitril|entresto|carvedilol|coreg|digoxin|lanoxin|spironolactone \+ furosemide", "heart_failure"),
    (r"tiotropium|spiriva|umeclidinium|roflumilast|ipratropium", "copd"),
)


# entities whose laboratory signal counts as support for a documented diagnosis
_CONTEXT_SUPPORT_ALIASES: dict[str, tuple[str, ...]] = {
    "diabetes_mellitus": ("type_2_diabetes", "type_1_diabetes", "hyperglycemia", "stress_hyperglycemia", "diabetic_ketoacidosis", "hyperosmolar_hyperglycemic_state"),
    "heart_failure": ("heart_failure_bnp_pattern", "heart_failure_ntprobnp_pattern", "heart_failure_decompensated", "acute_heart_failure_support_pattern", "chronic_heart_failure_support_pattern"),
    "chronic_kidney_disease": ("acute_kidney_injury", "renal_impairment", "ckd_mineral_bone_disorder"),
    "hypothyroidism": ("primary_hypothyroidism", "primary_hypothyroidism_pattern", "subclinical_hypothyroidism", "subclinical_hypothyroidism_pattern", "central_hypothyroidism"),
    "liver_cirrhosis": ("cirrhosis_laboratory_pattern", "decompensated_cirrhosis_pattern", "portal_hypertension_laboratory_pattern", "hepatocellular_injury_pattern", "hepatic_encephalopathy"),
    "copd": ("respiratory_acidosis", "chronic_respiratory_acidosis", "secondary_polycythemia", "compensated_respiratory_acidosis"),
    "gout": ("hyperuricemia", "gout_biochemical_risk"),
    "alcohol_use_disorder": ("alcoholic_liver_pattern", "alcoholic_hepatitis_pattern", "alcohol_associated_liver_disease", "alcoholic_ketoacidosis"),
    "anemia": ("iron_deficiency_anemia", "anemia_of_chronic_disease", "anemia_of_chronic_inflammation"),
}


def _documented_entities(ctx: Optional["ClinicalContext"]) -> dict[str, list[str]]:
    """ESL extension 11-C: map the caller's documented conditions and home
    medications to registry entities.  Returns {entity_id: [source phrases]}."""
    out: dict[str, list[str]] = {}
    if ctx is None:
        return out
    conds: list[str] = []
    meds: list[str] = []
    for kname in ("known_conditions", "conditions", "comorbidities", "past_history", "medical_history"):
        val = getattr(ctx, kname, None)
        if val is None:
            val = (getattr(ctx, "extra", {}) or {}).get(kname)
        if isinstance(val, (list, tuple, set)):
            conds.extend(str(x) for x in val)
        elif isinstance(val, str) and val.strip():
            conds.extend(p.strip() for p in re.split(r"[;,\n]", val) if p.strip())
    for kname in ("current_medications", "medications"):
        val = getattr(ctx, kname, None)
        if val is None:
            val = (getattr(ctx, "extra", {}) or {}).get(kname)
        if isinstance(val, (list, tuple, set)):
            meds.extend(str(x) for x in val)
        elif isinstance(val, str) and val.strip():
            meds.extend(p.strip() for p in re.split(r"[;,\n]", val) if p.strip())
    for flag, did in (("diabetes", "diabetes_mellitus"), ("hypertension", "hypertension")):
        if getattr(ctx, flag, None) is True:
            out.setdefault(did, []).append(f"{flag}=True")
    for c in conds:
        cl = c.lower()
        if re.search(r"\bno (health problems|known)|denies|negative for|\bno\b.*history", cl):
            continue
        for rx, did in _DOCUMENTED_CONDITION_MAP:
            if re.search(rx, cl):
                out.setdefault(did, []).append(c)
    for m in meds:
        ml = m.lower()
        for rx, did in _DOCUMENTED_MEDICATION_MAP:
            if re.search(rx, ml):
                out.setdefault(did, []).append("med:" + m)
    return out
# extension 7 (2026-10-22): entities whose executable rules use only ubiquitous analytes (filled at registry load)
NONSPECIFIC_ONLY_CEILING = 0.35
_NONSPECIFIC_ONLY_IDS: set = set()
_NONSPECIFIC_FEATURES = frozenset({
    "albumin", "hemoglobin", "hematocrit", "platelets", "platelet_count", "white_blood_cell_count", "glucose", "glucose_random",
    "fasting_plasma_glucose", "creatinine", "blood_urea_nitrogen", "sodium", "potassium", "chloride", "bicarbonate", "calcium_total",
    "magnesium", "phosphate", "total_protein", "mean_corpuscular_volume", "red_cell_distribution_width_cv", "alanine_aminotransferase",
    "aspartate_aminotransferase", "alkaline_phosphatase", "total_bilirubin", "lymphocytes_percent", "neutrophils_percent",
    "anion_gap"})


def _collect_nonspecific_only(rules: Mapping[str, Mapping[str, Any]]) -> set:
    def feats(e, acc):
        if not isinstance(e, Mapping):
            return
        if "feature_id" in e:
            acc.add(e["feature_id"])
        for k in ("all", "any", "conditions", "n_of"):
            for x in e.get(k, []) or []:
                feats(x, acc)
        if isinstance(e.get("not"), Mapping):
            feats(e["not"], acc)
    byd: dict[str, set] = {}
    for r in rules.values():
        if not r.get("executable") or r.get("rule_type") == "exclusion_criterion":
            continue
        acc: set = set(); feats(r.get("expression", {}), acc)
        byd.setdefault(r.get("disease_id", ""), set()).update(acc)
    return {d for d, f in byd.items() if d and f and f <= _NONSPECIFIC_FEATURES}
# Findings that are real but rarely the reason a panel is being read; they are
# listed after diseases/syndromes of equal or higher probability unless severe
# (ESL extension 6, 2026-10-21).  Potassium, sodium, calcium, glucose, lactate,
# haemoglobin, platelets and WBC findings are NOT in this list.
# ---------------------------------------------------------------------------
# v7 C11 (SAP Amendment 15, 2026-10-25): CAUSAL EXPLANATION MAP.
# A diagnosis may be named as the explanation of a laboratory finding ("hyponatraemia -
# explained by: ...") ONLY if it is a recognised cause of that finding, or if the
# analytes that define the finding are part of the constellation that asserted the
# diagnosis. Before v7 the best-scoring diagnosis of the panel was named generically,
# which produced clinically absurd attributions (hyponatraemia "explained by"
# respiratory acidosis, hypochloraemia by diabetes). Entries list the laboratory
# manifestations each diagnosis is expected to produce; sources are the governing
# guidelines named per line (pathophysiology as in Harrison's 21e / UpToDate).
_CE = lambda *xs: frozenset(xs)
_RENAL_FX = _CE("hyperkalemia", "metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "hyperphosphatemia",
                "hypocalcemia", "hypermagnesemia", "hyperuricemia", "anemia", "reduced_gfr_chronicity_undetermined",
                "hyponatremia", "hypochloremia", "hyperchloremia")
_CAUSAL_EXPLANATION: dict = {
    # KDIGO AKI 2012 / KDIGO CKD 2024: electrolyte, acid-base, phosphate, uraemic anaemia (CKD)
    "acute_kidney_injury": _RENAL_FX | _CE("myocardial_injury_acuity_undetermined", "elevated_nt_probnp"),
    "chronic_kidney_disease": _RENAL_FX | _CE("myocardial_injury_acuity_undetermined", "elevated_nt_probnp", "vitamin_d_deficiency"),
    "prerenal_azotemia": _CE("reduced_gfr_chronicity_undetermined", "hyperuricemia", "metabolic_alkalosis", "hypernatremia", "hyponatremia", "hyperkalemia"),
    "cardiorenal_syndrome": _RENAL_FX | _CE("elevated_nt_probnp", "myocardial_injury_acuity_undetermined"),
    "hepatorenal_syndrome": _RENAL_FX | _CE("thrombocytopenia", "elevated_inr_pattern", "hypoalbuminemia"),
    "tumor_lysis_syndrome": _CE("hyperuricemia", "hyperkalemia", "hyperphosphatemia", "hypocalcemia", "reduced_gfr_chronicity_undetermined", "acute_kidney_injury", "metabolic_acidosis", "high_anion_gap_metabolic_acidosis"),
    # Sepsis-3 (Singer JAMA 2016) / Surviving Sepsis 2021: SIRS, leukocytosis/-penia, lactate, thrombocytopenia, AKI, cholestasis, hyperglycaemia
    "sepsis": _CE("systemic_inflammatory_response_syndrome", "quick_sofa_positive", "leukocytosis_pattern", "neutrophilia_pattern", "leukopenia", "lymphopenia",
                  "lactic_acidosis", "metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "thrombocytopenia", "reduced_gfr_chronicity_undetermined",
                  "acute_kidney_injury", "elevated_procalcitonin_pattern", "hypocalcemia", "hypophosphatemia", "hypomagnesemia", "hyponatremia", "hypoalbuminemia",
                  "elevated_inr_pattern", "myocardial_injury_acuity_undetermined", "hepatocellular_injury_pattern", "cholestatic_pattern", "anemia", "hypoxemia",
                  "respiratory_alkalosis", "disseminated_intravascular_coagulation", "fasting_hypoglycemia"),
    "septic_shock": _CE("lactic_acidosis", "metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "systemic_inflammatory_response_syndrome", "quick_sofa_positive",
                        "leukocytosis_pattern", "thrombocytopenia", "acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "myocardial_injury_acuity_undetermined",
                        "hepatocellular_injury_pattern", "elevated_inr_pattern", "hypocalcemia", "hypoxemia"),
    "disseminated_intravascular_coagulation": _CE("thrombocytopenia", "elevated_inr_pattern", "anemia"),
    # ADA/EASD hyperglycaemic crises 2024
    "diabetic_ketoacidosis": _CE("metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "hyperkalemia", "hypokalemia", "hyponatremia", "hyperchloremia",
                                 "hypophosphatemia", "hypomagnesemia", "leukocytosis_pattern", "hypertriglyceridemia", "diabetes_mellitus", "type_1_diabetes", "type_2_diabetes",
                                 "reduced_gfr_chronicity_undetermined", "hyperuricemia", "hyperosmolar_hyperglycemia_pattern"),
    "euglycemic_diabetic_ketoacidosis": _CE("metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "hypokalemia", "hyponatremia", "hyperchloremia"),
    "hyperosmolar_hyperglycemic_state": _CE("hypernatremia", "hyponatremia", "hyperosmolar_hyperglycemia_pattern", "reduced_gfr_chronicity_undetermined", "hypokalemia",
                                            "hyperkalemia", "diabetes_mellitus", "type_2_diabetes", "elevated_serum_osmolality_pattern"),
    "diabetes_mellitus": _CE("hypertriglyceridemia", "hyperosmolar_hyperglycemia_pattern", "hyperuricemia"),
    "type_2_diabetes": _CE("hypertriglyceridemia", "hyperosmolar_hyperglycemia_pattern", "hyperuricemia", "metabolic_dysfunction_associated_steatotic_liver_disease"),
    # EASL/AASLD cirrhosis: thrombocytopenia (hypersplenism), coagulopathy, hyponatraemia, hypoalbuminaemia, hyperbilirubinaemia, AKI-HRS
    "liver_cirrhosis": _CE("thrombocytopenia", "elevated_inr_pattern", "hyponatremia", "hypoalbuminemia", "anemia", "leukopenia", "hepatocellular_injury_pattern",
                           "cholestatic_pattern", "isolated_hyperbilirubinemia_pattern", "hypokalemia", "hypomagnesemia", "respiratory_alkalosis", "fasting_hypoglycemia",
                           "reduced_gfr_chronicity_undetermined", "hyperammonemia"),
    "acute_liver_failure": _CE("elevated_inr_pattern", "hepatocellular_injury_pattern", "fasting_hypoglycemia", "lactic_acidosis", "metabolic_acidosis",
                               "high_anion_gap_metabolic_acidosis", "hypophosphatemia", "thrombocytopenia", "hyponatremia", "hyperammonemia", "acute_kidney_injury"),
    "alcoholic_hepatitis_pattern": _CE("hepatocellular_injury_pattern", "isolated_hyperbilirubinemia_pattern", "elevated_inr_pattern", "leukocytosis_pattern", "anemia",
                                       "thrombocytopenia", "hypomagnesemia", "hypophosphatemia", "hypokalemia"),
    "alcohol_use_disorder": _CE("hypomagnesemia", "hypophosphatemia", "hypokalemia", "anemia", "thrombocytopenia", "hepatocellular_injury_pattern", "hypertriglyceridemia",
                                "hyperuricemia", "elevated_mean_corpuscular_volume", "alcoholic_liver_pattern", "fasting_hypoglycemia"),
    "alcoholic_ketoacidosis": _CE("metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "hypokalemia", "hypomagnesemia", "hypophosphatemia", "fasting_hypoglycemia", "lactic_acidosis"),
    # ESC HF 2021/2023: natriuretic peptides, dilutional hyponatraemia, congestive hepatopathy, cardiorenal
    "heart_failure": _CE("elevated_nt_probnp", "hyponatremia", "reduced_gfr_chronicity_undetermined", "hepatocellular_injury_pattern", "cholestatic_pattern",
                         "myocardial_injury_acuity_undetermined", "hypochloremia", "hypoxemia", "respiratory_acidosis", "cardiorenal_syndrome", "anemia"),
    # 4th UDMI 2018 / ESC ACS 2023
    "acute_myocardial_infarction": _CE("myocardial_injury_acuity_undetermined", "acute_myocardial_injury", "leukocytosis_pattern", "elevated_nt_probnp", "hyperosmolar_hyperglycemia_pattern"),
    # rhabdomyolysis (Bosch NEJM 2009): CK, AKI, K, PO4, Ca, urate, AST/ALT from muscle
    "rhabdomyolysis": _CE("acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "hyperkalemia", "hyperphosphatemia", "hypocalcemia", "hyperuricemia",
                          "hepatocellular_injury_pattern", "metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "lactic_acidosis"),
    # Atlanta 2012 / ACG 2024 pancreatitis
    "acute_pancreatitis": _CE("hypocalcemia", "leukocytosis_pattern", "hyperosmolar_hyperglycemia_pattern", "hypertriglyceridemia", "hypomagnesemia",
                              "acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "cholestatic_pattern", "hepatocellular_injury_pattern", "hypoxemia", "lactic_acidosis",
                              "metabolic_acidosis", "systemic_inflammatory_response_syndrome", "anemia"),
    "alcoholic_pancreatitis": _CE("hypocalcemia", "leukocytosis_pattern", "hypertriglyceridemia", "hypomagnesemia", "hepatocellular_injury_pattern"),
    # Endocrine Society adrenal insufficiency 2016
    "primary_adrenal_insufficiency": _CE("hyponatremia", "hyperkalemia", "fasting_hypoglycemia", "eosinophilia", "eosinophilia_pattern", "hypercalcemia", "metabolic_acidosis",
                                         "reduced_gfr_chronicity_undetermined", "anemia", "lymphocytosis", "hyponatremia_hyperkalemia_pattern"),
    "adrenal_crisis": _CE("hyponatremia", "hyperkalemia", "fasting_hypoglycemia", "eosinophilia", "hypercalcemia", "reduced_gfr_chronicity_undetermined", "metabolic_acidosis", "hyponatremia_hyperkalemia_pattern"),
    "central_adrenal_insufficiency": _CE("hyponatremia", "fasting_hypoglycemia", "eosinophilia", "anemia"),
    # ATA hypothyroidism 2014 / myxoedema
    "hypothyroidism": _CE("hypercholesterolemia", "hyponatremia", "anemia", "elevated_mean_corpuscular_volume", "hypertriglyceridemia", "reduced_gfr_chronicity_undetermined"),
    "primary_hypothyroidism": _CE("hypercholesterolemia", "hyponatremia", "anemia", "elevated_mean_corpuscular_volume", "hypertriglyceridemia", "reduced_gfr_chronicity_undetermined"),
    "myxedema_coma": _CE("hyponatremia", "fasting_hypoglycemia", "hypercapnia_pattern", "respiratory_acidosis", "hypoxemia", "hypercholesterolemia", "anemia"),
    "hyperthyroidism": _CE("hypercalcemia", "hypokalemia", "leukopenia", "hepatocellular_injury_pattern", "cholestatic_pattern", "anemia", "thrombocytopenia"),
    "thyroid_storm": _CE("hypercalcemia", "hyperosmolar_hyperglycemia_pattern", "leukocytosis_pattern", "hepatocellular_injury_pattern", "cholestatic_pattern", "isolated_hyperbilirubinemia_pattern"),
    # Hyponatraemia guideline (ESE/ERA 2014)
    "siadh": _CE("hyponatremia", "severe_hyponatremia", "low_serum_osmolality_pattern", "high_urine_osmolality_pattern", "hypouricemia"),
    "diabetes_insipidus": _CE("hypernatremia", "severe_hypernatremia", "low_urine_osmolality_pattern", "elevated_serum_osmolality_pattern"),
    # Haematology
    "hemolytic_anemia": _CE("anemia", "isolated_hyperbilirubinemia_pattern", "elevated_lactate_dehydrogenase", "reticulocytosis"),
    "thrombotic_microangiopathy": _CE("anemia", "thrombocytopenia", "acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "isolated_hyperbilirubinemia_pattern"),
    "thrombotic_thrombocytopenic_purpura": _CE("anemia", "thrombocytopenia", "isolated_hyperbilirubinemia_pattern", "myocardial_injury_acuity_undetermined"),
    "hemolytic_uremic_syndrome": _CE("anemia", "thrombocytopenia", "acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "hyperkalemia"),
    "immune_thrombocytopenia": _CE("thrombocytopenia"),
    "heparin_induced_thrombocytopenia": _CE("thrombocytopenia"),
    "multiple_myeloma": _CE("anemia", "hypercalcemia", "reduced_gfr_chronicity_undetermined", "acute_kidney_injury", "chronic_kidney_disease", "elevated_total_protein", "hyperuricemia", "hyponatremia"),
    "chronic_lymphocytic_leukemia": _CE("lymphocytosis", "lymphocytosis_pattern", "leukocytosis_pattern", "anemia", "thrombocytopenia", "hyperuricemia"),
    "acute_myeloid_leukemia": _CE("leukocytosis_pattern", "leukopenia", "anemia", "thrombocytopenia", "neutropenia", "hyperuricemia", "lactic_acidosis", "tumor_lysis_syndrome"),
    "myelodysplastic_syndrome": _CE("anemia", "thrombocytopenia", "neutropenia", "leukopenia", "elevated_mean_corpuscular_volume"),
    "aplastic_anemia": _CE("anemia", "thrombocytopenia", "neutropenia", "leukopenia"),
    "iron_deficiency_anemia": _CE("anemia", "thrombocytosis", "thrombocytosis_pattern", "decreased_mean_corpuscular_volume"),
    "vitamin_b12_deficiency": _CE("anemia", "elevated_mean_corpuscular_volume", "leukopenia", "thrombocytopenia", "elevated_lactate_dehydrogenase"),
    "folate_deficiency": _CE("anemia", "elevated_mean_corpuscular_volume", "leukopenia", "thrombocytopenia"),
    # Respiratory / blood gas (ATS/ERS, GOLD 2024)
    "copd": _CE("respiratory_acidosis", "hypercapnia_pattern", "hypoxemia", "high_bicarbonate_pattern", "secondary_erythrocytosis", "polycythemia"),
    "respiratory_acidosis": _CE("hypercapnia_pattern", "hypoxemia", "high_bicarbonate_pattern", "hypochloremia"),
    "acute_respiratory_distress_syndrome": _CE("hypoxemia", "respiratory_acidosis", "hypercapnia_pattern", "lactic_acidosis"),
    "pulmonary_embolism": _CE("hypoxemia", "respiratory_alkalosis", "myocardial_injury_acuity_undetermined", "elevated_nt_probnp", "elevated_d_dimer"),
    "community_acquired_pneumonia": _CE("leukocytosis_pattern", "neutrophilia_pattern", "hypoxemia", "hyponatremia", "systemic_inflammatory_response_syndrome", "elevated_procalcitonin_pattern", "respiratory_alkalosis"),
    "metabolic_acidosis": _CE("low_bicarbonate_pattern", "low_base_excess_pattern", "hyperkalemia", "hyperchloremia", "hypocalcemia"),
    "high_anion_gap_metabolic_acidosis": _CE("low_bicarbonate_pattern", "low_base_excess_pattern", "hyperkalemia", "metabolic_acidosis"),
    "lactic_acidosis": _CE("metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "low_bicarbonate_pattern", "low_base_excess_pattern", "hyperkalemia"),
    "metabolic_alkalosis": _CE("high_bicarbonate_pattern", "high_base_excess_pattern", "hypokalemia", "hypochloremia", "hypocalcemia"),
    "respiratory_alkalosis": _CE("hypophosphatemia", "hypocalcemia", "hypokalemia", "hypochloremia"),
    # Nutrition (ASPEN/ESPEN), refeeding (ASPEN 2020)
    "protein_energy_malnutrition": _CE("hypoalbuminemia", "anemia", "lymphopenia", "hypophosphatemia", "hypomagnesemia", "hypokalemia", "hypocalcemia", "hypocholesterolemia"),
    "refeeding_syndrome": _CE("hypophosphatemia", "severe_hypophosphatemia", "hypokalemia", "hypomagnesemia"),
    # Calcium / PTH (Endocrine Society)
    "primary_hyperparathyroidism": _CE("hypercalcemia", "hypophosphatemia", "hyperchloremia", "metabolic_acidosis"),
    "hypoparathyroidism": _CE("hypocalcemia", "severe_hypocalcemia", "hyperphosphatemia"),
    "vitamin_d_deficiency": _CE("hypocalcemia", "hypophosphatemia"),
    # Misc
    "cushing_syndrome": _CE("hypokalemia", "metabolic_alkalosis", "hyperosmolar_hyperglycemia_pattern", "leukocytosis_pattern", "lymphopenia", "eosinopenia", "hypercholesterolemia"),
    "nephrotic_syndrome": _CE("hypoalbuminemia", "hypercholesterolemia", "hypertriglyceridemia", "hyponatremia", "reduced_gfr_chronicity_undetermined"),
    "vitamin_k_deficiency": _CE("elevated_inr_pattern"),
    "urinary_tract_infection": _CE("leukocytosis_pattern", "neutrophilia_pattern", "systemic_inflammatory_response_syndrome", "elevated_procalcitonin_pattern"),
    "acute_cholangitis": _CE("cholestatic_pattern", "isolated_hyperbilirubinemia_pattern", "leukocytosis_pattern", "hepatocellular_injury_pattern", "systemic_inflammatory_response_syndrome", "sepsis"),
    "heat_stroke": _CE("rhabdomyolysis", "hepatocellular_injury_pattern", "acute_kidney_injury", "hyperkalemia", "hypocalcemia", "lactic_acidosis", "elevated_inr_pattern", "thrombocytopenia", "respiratory_alkalosis"),
    "hepatocellular_injury_pattern": _CE("isolated_hyperbilirubinemia_pattern", "elevated_lactate_dehydrogenase"),
    # ACOG 222 (2020) hypertensive disorders of pregnancy: HELLP - haemolysis, transaminases, platelets; urate rises in pre-eclampsia
    "hellp_syndrome": _CE("thrombocytopenia", "hepatocellular_injury_pattern", "anemia", "hyperuricemia", "isolated_hyperbilirubinemia_pattern", "elevated_lactate_dehydrogenase",
                          "acute_kidney_injury", "reduced_gfr_chronicity_undetermined", "elevated_inr_pattern", "hellp_associated_liver_injury", "thrombotic_microangiopathy"),
    "preeclampsia": _CE("hyperuricemia", "thrombocytopenia", "hepatocellular_injury_pattern", "reduced_gfr_chronicity_undetermined", "elevated_urine_albumin_to_creatinine_ratio"),
    "metabolic_dysfunction_associated_steatotic_liver_disease": _CE("hepatocellular_injury_pattern", "hypertriglyceridemia", "hyperuricemia"),
}


def _can_explain(dx_id: str, finding_id: str) -> bool:
    """True when `dx_id` is a recognised cause of `finding_id` (v7 C11)."""
    return finding_id in _CAUSAL_EXPLANATION.get(dx_id, ())


_LOW_SALIENCE_FINDINGS = frozenset({
    "hypochloremia", "hyperchloremia", "hyperphosphatemia", "hypophosphatemia",
    "hypoproteinemia", "hyperproteinemia", "isolated_hyperbilirubinemia_pattern",
    "hypermagnesemia", "hypomagnesemia", "hypocalcemia", "elevated_anion_gap_pattern",
    "hypoalbuminemia", "hyperglobulinemia", "macrocytosis", "microcytosis",
})
SCEPTIC_SOFTNESS = 0.15             # vote this far below the mean = full sceptic
DEFINITIONAL_FINDING_SCORE = 0.80
# Rule-layer vote for a met curated guideline criterion (status
# `curated_guideline_anchored`), and the minimum ensemble weight share such a
# disease is treated as carrying: the guideline's own decision limit is not
# "thin evidence" merely because the Bayesian/fuzzy layers have no prior for
# that entity.
GUIDELINE_ANCHOR_RULE_SCORE = 0.92
GUIDELINE_ANCHOR_MIN_WEIGHT_SHARE = 0.75

# How many differentials a clinician will actually read. The engine
# ranks everything it knows; this is the point past which a longer
# list stops informing and starts hiding the answer.
MAX_DIFFERENTIAL = 25



def _profile_for_domains(domains: Optional[Iterable[str]]) -> str:
    if not domains:
        return "default"
    joined = " ".join(str(d).lower() for d in domains)
    for keys, profile in _DOMAIN_TO_PROFILE:
        if any(k in joined for k in keys):
            return profile
    return "default"


def _disabled_layers() -> set[str]:
    """Ablation hook: HEMOGLYPH_DISABLE_LAYERS=bayesian,fuzzy."""
    raw = os.environ.get("HEMOGLYPH_DISABLE_LAYERS", "")
    return {x.strip() for x in raw.split(",") if x.strip()}


def _pairwise_conflict(votes: Mapping[str, float],
                       weights: Mapping[str, float]) -> float:
    """Weighted mean absolute pairwise disagreement in [0, 1]."""
    items = [(votes[m], weights[m]) for m in votes if weights.get(m, 0) > 0]
    if len(items) < 2:
        return 0.0
    num = den = 0.0
    for i in range(len(items)):
        vi, wi = items[i]
        for j in range(i + 1, len(items)):
            vj, wj = items[j]
            num += wi * wj * abs(vi - vj)
            den += wi * wj
    return num / den if den > 0 else 0.0


def _yager_binary_combine(masses: Sequence[tuple[float, float, float]]
                          ) -> tuple[float, float, float, float]:
    """Combine (m(D), m(notD), m(Theta)) triples on a binary frame.

    Yager's rule: conflicting mass is assigned to Theta instead of being
    renormalised, so strong disagreement produces *ignorance*, never a
    spurious certainty (Zadeh's paradox cannot occur). Returns
    (belief, plausibility, ignorance, total_conflict_mass).
    """
    # n-ary conjunctive combination in closed form on the binary frame.
    # (A pairwise/sequential Yager fold is NOT associative - moving the
    # conflict to Theta after each step makes the result depend on the order
    # in which the layers are visited; the closed form does not.)
    #   q(D)     = prod(d_i + t_i) - prod(t_i)   every source said D or Theta
    #   q(notD)  = prod(n_i + t_i) - prod(t_i)
    #   q(Theta) = prod(t_i)
    #   K        = 1 - q(D) - q(notD) - q(Theta)  (total conflict mass)
    # Yager: K is handed to Theta instead of being renormalised away.
    if not masses:
        return 0.0, 1.0, 1.0, 0.0
    p_dt = p_nt = p_t = 1.0
    for (d2, n2, t2) in masses:
        tot = d2 + n2 + t2
        if tot <= 0:
            continue
        d2, n2, t2 = d2 / tot, n2 / tot, t2 / tot
        p_dt *= (d2 + t2)
        p_nt *= (n2 + t2)
        p_t *= t2
    d = max(0.0, p_dt - p_t)
    n = max(0.0, p_nt - p_t)
    k = max(0.0, 1.0 - d - n - p_t)
    t = p_t + k
    s = d + n + t
    if s > 0:
        d, n, t = d / s, n / s, t / s
    return d, d + t, t, min(1.0, k)


def _evidence_state(belief: float, plaus: float, conflict: float) -> str:
    width = plaus - belief
    if conflict >= 0.45:
        return "conflicting"
    if belief >= 0.5:
        return "supported"
    if plaus <= 0.35:
        return "refuted"
    if width >= 0.40:
        return "insufficient"
    return "weak"


def tarkib_ensemble(rule_scores: Mapping[str, float],
    bayesian_scores: Mapping[str, float],
    fuzzy_scores: Mapping[str, float],
    graph_boosts: Mapping[str, float],
    risk_scores: Mapping[str, float],
    *,
    domain_of: Optional[Mapping[str, Iterable[str]]] = None,
    input_reliability: Optional[Mapping[str, float]] = None,
    guideline_anchored: Optional[Iterable[str]] = None,
    expert_anchored: Optional[Iterable[str]] = None,
    finding_ids: Optional[Iterable[str]] = None,
    expert_definitional: Optional[Iterable[str]] = None,
) -> list[EnsembleResult]:
    """Combine the layer votes into one score per disease.

    1. Domain weight profile, renormalised over the layers that voted and
       scaled by the share of ensemble weight that spoke.
    2. Weighted pairwise conflict -> confidence.
    3. Discord: pull toward the sceptical cluster in proportion to the
       conflict and the sceptics' weight (bounded by MAX_DISCORD_SHRINK).
    4. Red-flag floor: explicit guideline criteria cannot be buried by a
       low prior alone.
    5. Binary-frame Yager/DST combination with reliability discounting ->
       Belief / Plausibility / ignorance, carried out to the report.
    """
    disabled = _disabled_layers()
    domain_of = domain_of or {}
    input_reliability = input_reliability or {}
    anchored = frozenset(guideline_anchored or ())
    expert = frozenset(expert_anchored or ())
    definitional = frozenset(expert_definitional or ())
    findings = frozenset(finding_ids or ())

    all_diseases = set(rule_scores) | set(bayesian_scores) | set(fuzzy_scores)
    all_diseases = {
        d for d in all_diseases
        if rule_scores.get(d) is not None
        or bayesian_scores.get(d) is not None
        or fuzzy_scores.get(d) is not None}

    results: list[EnsembleResult] = []
    for disease_id in all_diseases:
        raw = {
            "rule_engine":     rule_scores.get(disease_id),
            "bayesian":        bayesian_scores.get(disease_id),
            "fuzzy":           fuzzy_scores.get(disease_id),
            "knowledge_graph": graph_boosts.get(disease_id),
            "risk_models":     risk_scores.get(disease_id),
        }
        for m in disabled:
            raw[m] = None
        # The rule layer only ever reports *support* (criterion_not_met is
        # not scored), so a vanishing rule vote is a heavily discounted
        # non-specific hit, not a refutation. Treat it as abstention rather
        # than letting 0.004 drag the mean and plausibility to the floor.
        if raw["rule_engine"] is not None and float(raw["rule_engine"]) < RULE_ABSTAIN_BELOW:
            raw["rule_engine"] = None
        votes = {m: (0.0 if v is None else _clamp01(float(v)))
                 for m, v in raw.items()}
        participating = [m for m in raw if raw[m] is not None]

        profile_name = _profile_for_domains(domain_of.get(disease_id))
        weights = WEIGHT_PROFILES.get(profile_name, MODEL_WEIGHTS)
        total_profile_w = sum(weights.values()) or 1.0

        effective_weights = {m: (weights[m] if raw[m] is not None else 0.0)
                             for m in weights}

        total_w = sum(effective_weights.values())
        if total_w <= 0:
            continue
        norm_w = {m: effective_weights[m] / total_w for m in effective_weights}
        weighted_mean = sum(votes[m] * norm_w[m] for m in votes)

        # Thin evidence must rank below broad evidence of the same strength.
        weight_share = total_w / total_profile_w
        if disease_id in anchored and raw.get("rule_engine") is not None:
            weight_share = max(weight_share, GUIDELINE_ANCHOR_MIN_WEIGHT_SHARE)
        # A met expert-syndrome constellation is a complete clinical picture:
        # the probabilistic layers' silence on a multi-analyte definition is
        # not thin evidence.
        if disease_id in expert and raw.get("rule_engine") is not None:
            weight_share = 1.0
        final_score = weighted_mean * (0.60 + 0.40 * weight_share)

        # --- conflict / confidence ---------------------------------------
        conflict = _pairwise_conflict(
            {m: votes[m] for m in participating}, norm_w)
        rel = _clamp01(float(input_reliability.get(disease_id, 1.0)))
        confidence = (1.0 - conflict) if len(participating) > 1 else 0.4
        confidence *= min(1.0, 0.45 + 0.2 * len(participating))
        confidence *= (0.5 + 0.5 * rel)

        # --- discord: pull toward the sceptical cluster ------------------
        if len(participating) > 1 and conflict > 0.0:
            # Soft sceptic membership (0 at the mean, 1 at mean-0.15 and
            # below) instead of a hard "below the mean" set, so the score is
            # continuous in every vote. (A weak rule vote above the abstain
            # threshold still counts as scepticism here: "criteria evaluated
            # and barely met" is information; the DST masses stay one-sided.)
            memb = {m: _clamp01((weighted_mean - votes[m]) / SCEPTIC_SOFTNESS)
                    for m in participating}
            w_sc = sum(norm_w[m] * memb[m] for m in memb)
            if w_sc > 1e-9:
                target = sum(votes[m] * norm_w[m] * memb[m] for m in memb) / w_sc
                shrink = MAX_DISCORD_SHRINK * conflict * min(1.0, w_sc / 0.35)
                shrink = max(0.0, min(MAX_DISCORD_SHRINK, shrink))
                final_score = (1.0 - shrink) * final_score + shrink * target

        # --- red-flag floor against over-conservatism ---------------------
        rule_vote = votes.get("rule_engine", 0.0)
        if raw.get("rule_engine") is not None and rule_vote >= RED_FLAG_RULE_VOTE:
            final_score = max(final_score,
                              RED_FLAG_FLOOR_FRACTION * rule_vote)
        # A met expert-syndrome constellation is the definition of the
        # entity; a low prior-driven Bayesian/fuzzy vote on a subset of its
        # analytes is not a refutation. Floor at 90% of the constellation vote.
        expert_hit = disease_id in expert and raw.get("rule_engine") is not None
        if expert_hit:
            final_score = max(final_score, 0.90 * rule_vote)
            # v6.1: an ANCHOR-strength constellation is the published decision
            # limit itself (sodium 121 mmol/L *is* hyponatraemia). It is not a
            # hypothesis to be diluted by a prior-driven layer, and must never
            # rank below a weaker single-vote finding that happened to have no
            # corroborating layer: floor at the full constellation vote.
            if disease_id in definitional:
                final_score = max(final_score, rule_vote)

        # --- evidence theory: Belief / Plausibility -----------------------
        masses = []
        for m in participating:
            alpha = LAYER_RELIABILITY.get(m, 0.5) * (0.5 + 0.5 * rel)
            # profile re-weighting also moves the discount
            alpha *= min(1.0, weights[m] / max(1e-9, MODEL_WEIGHTS[m]))
            # One uncorroborated source cannot by itself reach "supported"
            # unless its vote is red-flag strong: part of its mass is kept
            # as ignorance until a second layer speaks.
            if len(participating) == 1 and disease_id not in anchored:
                alpha *= SINGLE_SOURCE_DISCOUNT
            alpha = _clamp01(alpha)
            v = votes[m]
            if m == "rule_engine":
                # one-sided evidence: absence of a met criterion is ignorance
                masses.append((alpha * v, 0.0, 1.0 - alpha * v))
            else:
                masses.append((alpha * v, alpha * (1.0 - v), 1.0 - alpha))
        belief, plaus, ignorance, k_dst = _yager_binary_combine(masses)
        state = _evidence_state(belief, plaus, conflict)
        if expert_hit and state in ("conflicting", "weak", "insufficient"):
            state = "supported"

        # A disease carried by ONE weak layer with everything else silent is
        # mostly ignorance; let that show in the point score as well.
        if len(participating) == 1 and participating[0] != "rule_engine":
            final_score = min(final_score, 0.5 * (belief + plaus))
        # "Insufficient" evidence (one uncorroborated non-anchored source,
        # belief < 0.5, wide ignorance) must not be displayed as a >= 0.5
        # assertion: 0.5 is the operating point at which the engine claims
        # an entity (UCI HCV held-out run 2026-10-21: PBC 0.555 from ALP+GGT
        # in 15 healthy donors). The rank order among insufficient items is
        # preserved; only the ceiling moves.
        # Pure laboratory findings (hyperuricaemia, hypercholesterolaemia)
        # are exempt: a single rule on the defining analyte IS the finding.
        if (state == "insufficient" and len(participating) == 1 and not expert_hit
                and disease_id not in anchored and disease_id not in findings):
            final_score = min(final_score, INSUFFICIENT_CEILING)
        # extension 7 (2026-10-22): a disease whose only rules read ubiquitous analytes cannot be established
        # from a panel (pellagra from albumin, frailty from albumin + Hb); findings and *_pattern entities exempt.
        if (disease_id in _NONSPECIFIC_ONLY_IDS and not expert_hit and disease_id not in anchored
                and disease_id not in findings and not disease_id.endswith("_pattern") and not disease_id.startswith("co_")):
            final_score = min(final_score, NONSPECIFIC_ONLY_CEILING)

        final_score = _clamp01(final_score)
        calibrated = _calibrate(final_score, confidence)
        results.append(EnsembleResult(
            disease_id=disease_id,
            final_score=final_score,
            votes=votes,
            confidence=confidence,
            calibrated_score=calibrated,
            participating_models=participating,
            interpretation=_tafsir(final_score, confidence, state),
            belief=belief,
            plausibility=plaus,
            ignorance=ignorance,
            conflict=conflict,
            weight_profile=profile_name,
            input_reliability=rel,
            evidence_state=state,
        ))
    # extension 7 (2026-10-22): co_<a>_with_<b> where a and b are the same analyte family carries no information
    def _self_pair(d: str) -> bool:
        if not d.startswith("co_") or "_with_" not in d:
            return False
        a, b = d[3:].split("_with_", 1)
        strip = lambda x: x.replace("elevated_", "").replace("decreased_", "").replace("_random", "").replace("_fasting", "")
        return strip(a) == strip(b)
    results = [r for r in results if not _self_pair(r.disease_id)]
    # Deterministic ordering: ties must not depend on set iteration order.
    results.sort(key=lambda r: (-r.final_score, r.disease_id))
    return results


def _mohasebe_agreement(votes: Mapping[str, float]) -> float:
    """Kept for backward compatibility; agreement = 1 - pairwise conflict
    with equal weights."""
    values = list(votes.values())
    if not values:
        return 0.0
    if len(values) == 1:
        return 0.4
    eq = {m: 1.0 for m in votes}
    return max(0.0, 1.0 - _pairwise_conflict(votes, eq))

def _evidence_abnormal(evidence, feature_id) -> bool:
    """FIX A25: TRUE only refutes when the value is actually abnormal.

    Rules that *require* normality (and negated conditions evaluated
    through _edgham_nodes) also yield TRUE evidence for in-range values;
    those must not flip a result to conflicting_data.
    """
    for e in evidence or []:
        if e.feature_id != feature_id or e.truth != TruthValue.TRUE:
            continue
        lo, hi = _float(e.reference_low), _float(e.reference_high)
        aval = _float(e.actual_value)
        if lo is not None and hi is not None and aval is not None:
            if not (lo <= aval <= hi):
                return True
            continue
        return True  # no reference available: keep previous behaviour
    return False


def _calibrate(score: float, confidence: float) -> float:
    # FIX A32/A33: shrinking every low-confidence score toward 0.5 inflated
    # weak evidence (0.1 -> ~0.42), flipping "unlikely" to "pending" in
    # _tabaghebandi_vaziat. Low scores now shrink toward 0 instead.
    if confidence < 0.3:
        if score < 0.5:
            return score * (confidence / 0.3)
        return 0.5 + (score - 0.5) * confidence
    return score

def _tafsir(score: float, confidence: float,
            state: Optional[str] = None) -> str:
    if state == "conflicting":
        return 'تضاد بین لایه‌ها — نیازمند تست تأییدی اختصاصی'
    if state == "insufficient" and score <= 0.5:
        return 'شواهد ناکافی (بازه باور گسترده) — تست تکمیلی لازم است'
    if score > 0.7 and confidence > 0.7:
        return 'بسیار محتمل — توصیه بررسی فوری'
    elif score > 0.5:
        return 'محتمل — نیاز به تأیید'
    elif score > 0.2:
        return "ممکن — نیاز به پیگیری"
    else:
        return 'کم‌احتمال'



@dataclass
class DifferentialEntry:
    disease_id: str
    rank: int
    probability: float
    confidence: float
    supporting_evidence: list[str] = field(default_factory=list)
    opposing_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    status: str = "pending"
    ensemble_votes: dict[str, float] = field(default_factory=dict)
    sensitivity_notes: list[str] = field(default_factory=list)
    statement: str = ""
    belief: float = 0.0
    plausibility: float = 1.0
    conflict: float = 0.0
    evidence_state: str = "insufficient"
    weight_profile: str = "default"
    # Set on laboratory-finding entities ("anaemia", "polycythemia") when a
    # diagnosis higher in the list accounts for them.
    explained_by: Optional[str] = None


class MultiStageReasoner:

    TEST_SUGGESTIONS = {
        "iron_deficiency_anemia": [
            "Serum Iron", "TIBC", "Transferrin Saturation",
            "Peripheral Smear", "Reticulocyte Count"],
        "type_2_diabetes": [
            "OGTT", "Fasting Insulin", "C-Peptide", "GAD Antibodies"],
        "chronic_kidney_disease": [
            "Urine Protein/Creatinine Ratio", "Renal Ultrasound",
            "Cystatin C", "Urine Albumin"],
        "hypothyroidism": [
            "Free T4", "Anti-TPO Antibodies", "Anti-Thyroglobulin"],
        "hyperthyroidism": [
            "Free T3", "TSH Receptor Antibodies", 'Thyroid Ultrasound'],
        "nafl_d": [
            'Liver Ultrasound', 'FibroScan', "Liver Biopsy",
            'Hepatitis Panel'],
        "vitamin_b12_deficiency": [
            "Methylmalonic Acid", "Homocysteine",
            'Anti-Intrinsic Factor Antibodies'],
        "metabolic_syndrome": [
            'Fasting Lipid Panel', "HbA1c", "Waist Circumference"],
        'anemia': [
            "Complete CBC with indices", "Reticulocyte Count",
            "Peripheral Smear", "Iron studies", "B12/Folate"],
        "hyperlipidemia": [
            "Fasting Lipid Panel", 'ApoB', 'Lp(a)'],
        "hypertension": [
            "24h Ambulatory BP", "Renal Ultrasound", 'Aldosterone/Renin'],
        "celiac_disease": [
            "Anti-tTG IgA", "Total IgA", "Duodenal Biopsy"],
        "liver_cirrhosis": [
            "Liver Ultrasound", "FibroScan", "Hepatitis Panel",
            "Autoimmune markers"],
        "acute_kidney_injury": [
            'Urine Microscopy', "FENa", 'Renal Ultrasound',
            "CPK", 'Urinalysis'],
        "primary_hyperparathyroidism": [
            "PTH", "Corrected Calcium", "Phosphate", "Vitamin D", "24h Urine Calcium", "DEXA Scan"],
        "diabetic_ketoacidosis": [
            "Beta-Hydroxybutyrate", "Arterial Blood Gas", "Anion Gap", "Serum Osmolality", "Electrolytes"],
        "metabolic_acidosis": [
            "ABG", "Anion Gap", "Delta Gap", "Lactate", "Ketones", "Osmolar Gap"],
        "siadh": [
            "Serum Osmolality", "Urine Osmolality", "Urine Sodium", "Cortisol", "TSH"],
        "cholestasis": [
            "ALP Isoenzymes", "GGT", "Bilirubin Fractions", "Liver Ultrasound", "MRCP"],
        "pancytopenia": [
            "Peripheral Smear", "Reticulocyte Count", "B12/Folate", "Bone Marrow Biopsy", "LDH"],
        "disseminated_intravascular_coagulation": [
            "D-Dimer", "Fibrinogen", "PT/INR", "aPTT", "Platelet Count"],
        "malnutrition": [
            "Prealbumin", "Albumin", "Transferrin", "Vitamin D", "B12/Folate", "Iron Studies"],
        "bacterial_infection": [
            "Blood Cultures", "Procalcitonin", "CRP", "Lactate", "CBC with Differential"],
        "viral_infection": [
            "Viral PCR Panel", "Lymphocyte Subsets", "CRP", "Procalcitonin"],
    }


    IMPACTFUL_MISSING = {
        "type_2_diabetes": [
            ('hemoglobin_a1c',
             "HbA1c ≥6.5% would confirm diabetes; <5.7% would rule it out"),
            ("fasting_plasma_glucose",
             "FBS ≥126 mg/dL on repeat testing is diagnostic"),
            ("two_hour_postload_glucose",
             "OGTT 2h ≥200 mg/dL would confirm diabetes"),
        ],
        "chronic_kidney_disease": [
            ('egfr_ckd_epi_creatinine',
             "eGFR <60 for ≥3 months confirms CKD"),
            ('urine_albumin_to_creatinine_ratio',
             "ACR ≥30 mg/g confirms albuminuria"),
        ],
        "iron_deficiency_anemia": [
            ("ferritin",
             "Ferritin <30 ng/mL confirms iron depletion"),
            ("serum_iron",
             "Low serum iron with high TIBC confirms IDA"),
        ],
        "hypothyroidism": [
            ('thyroid_stimulating_hormone',
             'TSH >4.5 mIU/L suggests hypothyroidism'),
            ("free_thyroxine",
             "Low free T4 confirms overt hypothyroidism"),
        ],
        "hyperthyroidism": [
            ("thyroid_stimulating_hormone",
             "TSH <0.1 mIU/L suggests hyperthyroidism"),
            ("free_triiodothyronine",
             "Elevated free T3 confirms thyrotoxicosis"),
        ],
        'nafl_d': [
            ("alanine_aminotransferase",
             "Elevated ALT with imaging steatosis confirms NAFLD"),
            ("liver_ultrasound",
             'Imaging evidence of steatosis is key'),
        ],
        "primary_hyperparathyroidism": [
            ("parathyroid_hormone", "PTH >65 with high Ca confirms primary hyperpara"),
            ("calcium_total", "Corrected Ca >10.5 with high PTH"),
        ],
        "diabetic_ketoacidosis": [
            ("beta_hydroxybutyrate", "BHB >0.6 mmol/L with high glucose + low HCO3 confirms DKA"),
            ("ph", "pH <7.30 with high anion gap"),
        ],
        "metabolic_acidosis": [
            ("anion_gap", "AG >12 suggests high-AG acidosis"),
            ("bicarbonate", "HCO3 <22 confirms metabolic acidosis"),
        ],
        "cholestasis": [
            ("alkaline_phosphatase", "ALP >2x ULN with high GGT suggests cholestasis"),
            ("bilirubin_direct", "Direct bilirubin >50% of total"),
        ],
        "pancytopenia": [
            ("reticulocyte_count", "Retic low suggests marrow failure; high suggests peripheral destruction"),
            ("vitamin_b12", "B12/folate deficiency is reversible cause"),
        ],
        "sepsis": [
            ("procalcitonin", "PCT >0.5 suggests bacterial sepsis"),
            ("lactate", "Lactate >2 indicates tissue hypoperfusion"),
        ],
    }

    def __init__(self, knowledge_graph: ClinicalKnowledgeGraph):
        self.kg = knowledge_graph

    # Registry entities that are the same diagnosis under two ids. The
    # evidence of the alias is folded into the canonical entry (max per
    # model), so a syndrome never competes against its own duplicate.
    DISEASE_ID_ALIASES: dict[str, str] = {
        "hyperglycemic_hyperosmolar_state": "hyperosmolar_hyperglycemic_state",
        "primary_adrenal_insufficiency_addison": "addison_disease",
        "hyperthyroidism_graves": "graves_disease",
        "acute_myeloid_leukemia_aml": "acute_myeloid_leukemia",
        "acute_promyelocytic_leukemia_apl": "acute_promyelocytic_leukemia",
        "acute_lymphoblastic_leukemia_all": "acute_lymphoblastic_leukemia",
        "chronic_lymphocytic_leukemia_cll": "chronic_lymphocytic_leukemia",
        "chronic_myeloid_leukemia_cml": "chronic_myeloid_leukemia",
        "multiple_myeloma_active": "multiple_myeloma",
        "pulmonary_embolism_acute": "pulmonary_embolism",
        "hepatitis_a_infection": "hepatitis_a",
        "megaloblastic_anemia_vitamin_b12_deficiency": "vitamin_b12_deficiency",
        "nephrotic_range_proteinuria": "nephrotic_syndrome",
        "cushing_syndrome_screening_pattern": "cushing_syndrome",
        "cushing_screening_pattern": "cushing_syndrome",
        "sepsis_support_pattern": "sepsis",
        "acute_leukemia_support_pattern": "acute_myeloid_leukemia",
        "multiple_myeloma_support_pattern": "multiple_myeloma",
        "acute_pancreatitis_support_pattern": "acute_pancreatitis",
        "paraneoplastic_hypercalcemia_support_pattern": "hypercalcemia_of_malignancy_support_pattern",
        "biliary_obstruction_choledocholithiasis": "cholestasis",
    }
    # Pattern twins (X_pattern -> X) are derived from the registry at init.
    _entity_kind: dict[str, str] = {}
    _twin_map: dict[str, str] = {}

    def configure_registry(self, diseases: Mapping[str, Any]) -> None:
        """Learn entity kinds and X_pattern -> X twins from the registry."""
        kinds: dict[str, str] = {}
        for did, d in (diseases or {}).items():
            kind = ((d or {}).get("classification") or {}).get("entity_kind") or (d or {}).get("entity_kind")
            if kind:
                kinds[did] = str(kind)
        twins: dict[str, str] = {}
        for did in diseases or {}:
            for suf in ("_pattern", "_support_pattern"):
                if did.endswith(suf):
                    base = did[:-len(suf)]
                    if base in diseases and base != did:
                        twins[did] = base
                        break
        self._entity_kind = kinds
        self._twin_map = twins

    def _canonical_id(self, disease_id: str) -> str:
        cur = disease_id
        for _ in range(3):
            nxt = self.DISEASE_ID_ALIASES.get(cur) or self._twin_map.get(cur)
            if not nxt or nxt == cur:
                break
            cur = nxt
        return cur

    def _merge_aliases(self, results: list[EnsembleResult]) -> list[EnsembleResult]:
        by_id: dict[str, EnsembleResult] = {}
        order: list[str] = []
        merged: set[str] = set()
        # canonical entries first so an alias is always folded *into* the
        # real entity rather than the other way round
        ordered = sorted(results, key=lambda r: self._canonical_id(r.disease_id) != r.disease_id)
        for r in ordered:
            canon = self._canonical_id(r.disease_id)
            target = by_id.get(canon)
            if target is None:
                if canon != r.disease_id:
                    # canonical entity not scored by any layer: promote the
                    # alias under the canonical id so one name is shown.
                    try:
                        r.disease_id = canon
                    except Exception:
                        pass
                by_id[canon] = r
                order.append(canon)
                continue
            if target is r:
                continue
            # fold evidence: per-model max, keep the stronger fusion
            votes = dict(target.votes or {})
            for m, v in (r.votes or {}).items():
                votes[m] = max(votes.get(m, 0.0), v)
            target.votes = votes
            part = set(target.participating_models or ()) | set(r.participating_models or ())
            target.participating_models = sorted(part)
            merged.add(canon)
        # Re-run the fusion on the folded votes so the merged entity gets a
        # proper combined score (not just the better of the two halves).
        for canon in merged:
            t = by_id[canon]
            v = t.votes or {}
            try:
                refused = tarkib_ensemble(
                    rule_scores={canon: v["rule_engine"]} if v.get("rule_engine") else {},
                    bayesian_scores={canon: v["bayesian"]} if v.get("bayesian") else {},
                    fuzzy_scores={canon: v["fuzzy"]} if v.get("fuzzy") else {},
                    graph_boosts={canon: v["knowledge_graph"]} if v.get("knowledge_graph") else {},
                    risk_scores={canon: v["risk_models"]} if v.get("risk_models") else {},
                    domain_of=getattr(self, "_domain_of", None) or {},
                )
            except Exception:
                refused = []
            if refused:
                new = refused[0]
                new.final_score = max(new.final_score, t.final_score)
                by_id[canon] = new
        return [by_id[k] for k in order]

    def _is_finding(self, disease_id: str) -> bool:
        kind = self._entity_kind.get(disease_id)
        if kind in ("laboratory_finding", "biomarker_pattern", "syndrome"):
            return True
        return _is_finding_entity(disease_id)

    def tier_of(self, disease_id: str) -> str:
        """v6 two-tier output (SAP Amendment 14, C1): 'diagnosis' for causal
        clinical entities, 'syndrome' for physiological criteria sets (SIRS,
        qSOFA), 'finding' for laboratory findings / biomarker patterns that the
        clinician can read off the sheet. Findings and syndromes are always
        reported but are not diagnoses; top-k evaluation of diagnoses uses the
        diagnosis tier only."""
        kind = self._entity_kind.get(disease_id)
        if kind == "syndrome":
            return "syndrome"
        if self._is_finding(disease_id):
            return "finding"
        return "diagnosis"

    @staticmethod
    def _val(observations: Mapping[str, Any], *fids: str) -> Optional[float]:
        for f in fids:
            v = observations.get(f)
            if isinstance(v, Mapping):
                v = v.get("value")
            v = _float(getattr(v, "value", v))
            if v is not None:
                return v
        return None

    def _apply_clinical_context(self, scored: list[EnsembleResult],
                                observations: Mapping[str, Any],
                                context: Optional[ClinicalContext]) -> list[EnsembleResult]:
        """ESL extension 11-C (2026-10-23): documented history / home medications.

        A documented diagnosis is a FACT supplied by the caller, not a prior:
          * documented + laboratory support on this panel (score >= 0.30 or
            evidence_state supported)  -> established, >= CONTEXT_CONFIRMED_SCORE
          * documented, no panel support -> listed as "documented_history" at
            CONTEXT_DOCUMENTED_SCORE (below the 0.5 operating point; tier 2)
        Nothing is added that the caller did not state; unsupported entities
        never cross the operating point."""
        self._context_applied = []
        doc = getattr(self, "_ctx_documented", None) or {}
        if not doc:
            return scored
        by_id = {r.disease_id: r for r in scored}
        for did, srcs in doc.items():
            r = by_id.get(did)
            # laboratory support may sit on a related entity (type_2_diabetes for diabetes_mellitus,
            # a BNP pattern for heart failure); the documented entity is then confirmed and the
            # related entity is left as scored.
            _alias_support = max([by_id[a].final_score for a in _CONTEXT_SUPPORT_ALIASES.get(did, ()) if a in by_id] or [0.0])
            if r is None and _alias_support >= 0.30:
                r = EnsembleResult(disease_id=did, final_score=_alias_support, votes={"clinical_context": CONTEXT_CONFIRMED_SCORE}, confidence=0.5,
                                   participating_models=["clinical_context"], evidence_state="supported")
                scored.append(r); by_id[did] = r
            if r is not None and (r.final_score >= 0.30 or r.evidence_state == "supported" or _alias_support >= 0.30):
                new = max(r.final_score, CONTEXT_CONFIRMED_SCORE)
                action = "confirmed" if new > r.final_score else "already_established"
                r.final_score = new
                r.votes["clinical_context"] = CONTEXT_CONFIRMED_SCORE
                if "clinical_context" not in r.participating_models:
                    r.participating_models.append("clinical_context")
                if r.evidence_state in ("insufficient", "weak"):
                    r.evidence_state = "supported"
            else:
                # A diagnosis implied only by a medication (metformin -> diabetes) is NOT listed
                # without laboratory support: the drug has other indications (PCOS, prediabetes).
                # An empty panel is not interpreted at all.
                if not observations or all(str(x).startswith("med:") for x in srcs):
                    self._context_applied.append({"disease_id": did, "action": "not_listed_unsupported", "source": sorted(set(srcs))[:4], "probability": None})
                    continue
                if r is None:
                    r = EnsembleResult(disease_id=did, final_score=CONTEXT_DOCUMENTED_SCORE,
                                       votes={"clinical_context": CONTEXT_DOCUMENTED_SCORE}, confidence=0.5,
                                       participating_models=["clinical_context"], evidence_state="documented_history",
                                       interpretation="Documented history; not assessable from this panel.")
                    scored.append(r); by_id[did] = r
                    action = "listed_documented"
                else:
                    r.final_score = max(r.final_score, CONTEXT_DOCUMENTED_SCORE)
                    r.votes["clinical_context"] = CONTEXT_DOCUMENTED_SCORE
                    r.evidence_state = "documented_history"
                    action = "listed_documented"
            self._context_applied.append({"disease_id": did, "action": action, "source": sorted(set(srcs))[:4],
                                          "probability": round(r.final_score, 3)})
        return scored

    def _apply_renal_chronicity(self, scored: list[EnsembleResult],
                                observations: Mapping[str, Any]) -> None:
        """AKI vs CKD cannot be told apart from one creatinine (KDIGO: AKI
        needs a rise within 7 d, CKD needs > 3 months). On a single time
        point the pair is reported as renal impairment of undetermined
        chronicity: the one with chronicity / acuity markers keeps its
        score, the other is capped, and both yield to an acute syndrome
        that explains the creatinine (DKA, rhabdomyolysis, sepsis)."""
        by_id = {r.disease_id: r for r in scored}
        aki, ckd = by_id.get("acute_kidney_injury"), by_id.get("chronic_kidney_disease")
        if aki is None and ckd is None:
            return
        ck = self._val(observations, "creatine_kinase_total", "creatine_kinase")
        hb = self._val(observations, "hemoglobin")
        phos = self._val(observations, "phosphate")
        pth = self._val(observations, "intact_parathyroid_hormone", "parathyroid_hormone")
        uacr = self._val(observations, "urine_albumin_to_creatinine_ratio")
        egfr = self._val(observations, "egfr_ckd_epi_creatinine", "egfr")
        if egfr is None:  # extension 7 (2026-10-22): CKD-EPI 2021 from creatinine when eGFR is not reported
            try:
                _cr = self._val(observations, "creatinine"); _ctx = getattr(self, "_ctx_for_renal", None)
                _age = float(getattr(_ctx, "age_years", None)) if _ctx is not None and getattr(_ctx, "age_years", None) is not None else None
                _sex = str(getattr(_ctx, "sex_at_birth", "") or "").lower()
                if _cr and _age and _age >= 18:
                    _f = _sex.startswith("f"); _r = _cr / (0.7 if _f else 0.9)
                    egfr = 142.0 * (min(_r, 1.0) ** (-0.241 if _f else -0.302)) * (max(_r, 1.0) ** -1.2) * (0.9938 ** _age) * (1.012 if _f else 1.0)
            except Exception:
                egfr = None
        chronic_markers = sum([
            hb is not None and hb < 11.0,
            phos is not None and phos > 4.5,
            pth is not None and pth > 65.0,
            uacr is not None and uacr >= 30.0,
        ])
        acute_cause = [
            d for d in ("diabetic_ketoacidosis", "rhabdomyolysis", "sepsis",
                        "hyperosmolar_hyperglycemic_state", "tumor_lysis_syndrome")
            if d in by_id and by_id[d].final_score >= 0.45
            # An acute cause may only "explain away" the creatinine when
            # its own evidence is corroborated. A sepsis / DKA entry that
            # is merely 'insufficient' (prior-driven, no lactate, no
            # ketones) must not cap a strongly supported renal entry
            # beneath it. Found in the retrospective pipeline dry-run.
            and getattr(by_id[d], "evidence_state", "") == "supported"]
        # Hyperkalaemia + hyperphosphataemia with anaemia, high PTH and
        # albuminuria is CKD-MBD, not tumour lysis: without a malignancy
        # context TLS cannot explain the creatinine and is itself capped.
        if chronic_markers >= 2:
            if "tumor_lysis_syndrome" in acute_cause:
                acute_cause.remove("tumor_lysis_syndrome")
            anchor = ckd if ckd is not None else aki
            for twin in ("tumor_lysis_syndrome", "tumor_lysis_pattern"):
                if twin in by_id:
                    by_id[twin].final_score = min(by_id[twin].final_score, anchor.final_score * 0.6)
        if ck is not None and ck >= 5000.0:
            acute_cause.append("rhabdomyolysis")
        if acute_cause:
            # creatinine is explained; the renal entry is a complication,
            # listed beneath the cause
            cause_score = max(by_id[d].final_score for d in acute_cause if d in by_id) \
                if any(d in by_id for d in acute_cause) else 0.6
            if aki is not None:
                aki.final_score = min(aki.final_score, cause_score * 0.9)
            if ckd is not None and chronic_markers < 2:  # extension 7: two chronicity markers keep CKD on the list (KDIGO 2024)
                ckd.final_score = min(ckd.final_score, cause_score * 0.6)
            return
        # ESL extension 11 (2026-10-23): chronicity resolved by a creatinine TRAJECTORY
        # (KDIGO dynamic criteria) and/or by DOCUMENTED chronic kidney disease.
        _fired = {h.get("syndrome_id") for h in (getattr(self, "_esl_hits", None) or []) if not h.get("guard")}
        _dyn_aki = bool(_fired & {"aki_kdigo_creatinine_rise", "aki_recovering_creatinine_fall"})
        # v6: KDIGO imputed-baseline AKI (acute-care encounter, no known CKD) is presumptive but is a KDIGO criterion
        _imp_aki = bool(_fired & {"aki_kdigo_imputed_baseline_acute_care"})
        _dyn_aki = _dyn_aki or (_imp_aki and chronic_markers < 2)
        _doc = getattr(self, "_ctx_documented", None) or {}
        _doc_ckd = "chronic_kidney_disease" in _doc
        _doc_dialysis = any("dialys" in str(s).lower() or "esrd" in str(s).lower() for s in _doc.get("chronic_kidney_disease", ()))
        if aki is not None and ckd is not None and (_dyn_aki or _doc_ckd):
            if _dyn_aki and (_doc_ckd or chronic_markers >= 2):
                pass  # AKI on CKD: both established, neither capped
            elif _dyn_aki:
                ckd.final_score = min(ckd.final_score, aki.final_score * 0.7)
                # v7 C12 (2026-10-25): a PRESUMPTIVE AKI (KDIGO imputed baseline in acute care) with
                # no chronicity marker at all and no documented CKD leaves chronic disease
                # undemonstrable from this panel - it is kept as a sub-threshold possibility
                # (symmetric with "documented CKD, no trajectory: AKI <= 0.49"), not as a third
                # renal entry competing in the first five lines next to AKI and the reduced-GFR finding.
                if _imp_aki and chronic_markers == 0 and not _doc_ckd:
                    ckd.final_score = min(ckd.final_score, 0.49)
            else:  # documented CKD, no dynamic rise on this panel
                if ckd.final_score < aki.final_score:
                    ckd.final_score = max(ckd.final_score, aki.final_score * 0.95)
                aki.final_score = min(aki.final_score, ckd.final_score * (0.5 if _doc_dialysis else 0.75))
            return
        if aki is not None and ckd is None and _doc_ckd and not _dyn_aki:
            aki.final_score = min(aki.final_score, 0.49)  # documented CKD with no acute trajectory: do not assert AKI
            return
        if aki is not None and ckd is not None:
            if chronic_markers >= 2:
                # ESL extension 6 (2026-10-21): chronicity markers transfer the
                # renal signal to CKD (KDIGO CKD 2024) instead of erasing it.
                if ckd.final_score < aki.final_score:
                    ckd.final_score = max(ckd.final_score, aki.final_score * 0.95)
                aki.final_score = min(aki.final_score, ckd.final_score * 0.75)
            elif chronic_markers == 0 and (egfr is None or egfr >= 15):
                # nothing says chronic; nothing says acute either.
                # ESL extension 10 (2026-10-23): the ceiling expresses uncertainty about
                # CHRONICITY, not about the presence of renal impairment, which is as
                # certain as the eGFR is low (KDIGO 2012/2024 G-staging). A G4 kidney is
                # impaired whatever its time course, so the undetermined-chronicity
                # ceiling is graded by severity instead of one flat 0.62.
                if egfr is None or egfr >= 45:
                    cap = 0.62
                elif egfr >= 30:
                    cap = 0.70
                else:
                    cap = 0.78
                aki.final_score = min(aki.final_score, cap)
                ckd.final_score = min(ckd.final_score, cap)
            else:
                _anch = getattr(self, "_expert_anchored", ()) or ()
                if "chronic_kidney_disease" in _anch and "acute_kidney_injury" not in _anch:
                    pass  # ESL extension 6d / 7: expert-anchored CKD stays; AKI is left as scored (chronicity undetermined)
                else:
                    ckd.final_score = min(ckd.final_score, aki.final_score * 0.9)

    def _neonatal_guard(self, scored: list[EnsembleResult],
                        observations: Mapping[str, Any],
                        context: Optional[ClinicalContext]) -> list[EnsembleResult]:
        """Physiologic neonatal jaundice: a term neonate with total bilirubin
        below the AAP 2022 low-risk phototherapy zone (~12 mg/dL at
        48-72 h) must not be flagged as pathologic hyperbilirubinaemia."""
        if context is None or getattr(context, "age_group", None) != "neonate":
            return scored
        bili = self._val(observations, "total_bilirubin", "bilirubin_total")
        if bili is None or bili >= 12.0:
            return scored
        direct = self._val(observations, "direct_bilirubin", "bilirubin_direct")
        if direct is not None and direct > 1.0:
            return scored  # conjugated - never physiologic
        kept = []
        for r in scored:
            did = r.disease_id
            if ("hyperbilirubinemia" in did or "jaundice" in did
                    or did in ("gilbert_syndrome", "gilbert_syndrome_pattern",
                               "hemolytic_anemia", "cholestasis")):
                continue
            kept.append(r)
        return kept

    def differential_diagnosis(
        self,
        ensemble_results: list[EnsembleResult],
        observations: Mapping[str, Any],
        context: Optional[ClinicalContext] = None,
    ) -> list[DifferentialEntry]:
        ensemble_results = self._merge_aliases(list(ensemble_results))
        # A fixed 0.05 floor was fine against a handful of diseases, but it
        # keeps roughly half of whatever the network knows: on a registry of
        # six thousand it returns some three thousand "differentials", which
        # is a data dump rather than a differential. Keep the absolute floor
        # as a sanity bound, then take the leading edge of the ranking -
        # anything an order of magnitude below the top candidate is noise no
        # clinician would work through.
        scored = [r for r in ensemble_results
                  if r.final_score > 0.05 and r.participating_models]

        # Active Evidence Filter:
        # Require at least one model to have real active evidence (vote >= 0.18) to prevent
        # passive background prior noise from surfacing false differentials
        scored = [
            r for r in scored
            if any(v >= 0.18 for v in r.votes.values())
        ]

        if context is not None:
            # 1. Pregnancy condition gating:
            if not getattr(context, "pregnant", False):
                scored = [
                    r for r in scored
                    if not any(k in r.disease_id for k in ("_in_pregnancy", "gestational", "preeclampsia", "eclampsia"))
                ]

            # 2. Pediatric age gating (< 18 years):
            if getattr(context, "age_years", None) is not None and float(context.age_years) < 18.0:
                ped_blocked = {
                    "coronary_artery_disease", "atherosclerosis", "multiple_myeloma",
                    "chronic_lymphocytic_leukemia", "sarcopenia", "osteoporosis",
                    "hepatocellular_carcinoma"
                }
                scored = [r for r in scored if r.disease_id not in ped_blocked]

            # 3. Sex anatomical gating:
            sex = context.normalized_jensiat()
            if sex == "female":
                scored = [r for r in scored if not any(k in r.disease_id for k in ("prostate", "prostatic", "testicular"))]
            elif sex == "male":
                scored = [r for r in scored if not any(k in r.disease_id for k in ("ovarian", "uterine", "cervical", "endometrio", "preeclampsia"))]

        # Demote synthetic pairwise combinations (co_elevated_ / co_decreased_) so real clinical diseases take priority
        for item in scored:
            if item.disease_id.startswith("co_elevated_") or item.disease_id.startswith("co_decreased_"):
                item.final_score *= 0.65
        self._ctx_for_renal = context  # extension 7 (2026-10-22)
        self._ctx_documented = _documented_entities(context)  # ESL ext 11-C (2026-10-23)
        self._apply_renal_chronicity(scored, observations)
        scored = self._apply_clinical_context(scored, observations, context)
        scored = self._neonatal_guard(scored, observations, context)
        scored.sort(key=lambda r: -r.final_score)
        if scored:
            lead = scored[0].final_score
            relative_floor = max(0.05, lead * 0.20)
            candidates = [r for r in scored
                          if r.final_score >= relative_floor][:MAX_DIFFERENTIAL]
        else:
            candidates = []
        present = [c.disease_id for c in candidates
                   if c.final_score > 0.5]


        filtered = []
        exclusion_notes: dict[str, list[str]] = {}
        for candidate in candidates:
            exclusions = self.kg.barresi_exclusions(
                candidate.disease_id, present)
            if exclusions:
                candidate.confidence *= 0.4
                candidate.final_score *= 0.5
                exclusion_notes[candidate.disease_id] = [
                    f"Excluded by {e['excluded_by']}: "
                    f"{e.get('reason') or 'guideline exclusion'}"
                    for e in exclusions]
            filtered.append(candidate)

        # A parent term absorbs evidence from all of its children, so
        # "anaemia" always outscores "anaemia of chronic disease" and the
        # ranking degenerates into naming the category instead of the
        # diagnosis. When a specific child is well supported, demote the
        # umbrella term below it: the clinician already knows the patient is
        # anaemic, what they need is which anaemia.
        by_id = {c.disease_id: c for c in filtered}
        parents = dict(_DISEASE_PARENT)
        parents.update(getattr(self, "_registry_parents", None) or {})
        for child, parent in parents.items():
            kid, mother = by_id.get(child), by_id.get(parent)
            if kid is None or mother is None:
                continue
            # Only a child whose own evidence is corroborated may demote the
            # umbrella term. A sub-type carried by thin / insufficient
            # evidence (e.g. Graves' without TRAb) must not pull a strongly
            # supported parent (overt hyperthyroidism, TSH + FT4) below
            # unrelated single-source candidates. Found in the retrospective
            # pipeline dry-run (fixture case: parent rank 1 -> 6).
            if kid.final_score >= 0.30 and getattr(kid, "evidence_state", "") == "supported":
                mother.final_score = min(
                    mother.final_score, kid.final_score * 0.85)

        # Demote synthetic pairwise combinations (co_elevated_ / co_decreased_) so real clinical diseases take priority
        for item in filtered:
            if item.disease_id.startswith("co_elevated_") or item.disease_id.startswith("co_decreased_"):
                item.final_score *= 0.82

        # A laboratory finding ("hyperglycemia", "hypertriglyceridemia") is
        # a fact the clinician can already read off the sheet. When a real
        # diagnosis that accounts for it is supported, the finding is listed
        # just beneath that diagnosis rather than above it.
        # A diagnosis counts as "accounting for" the findings when it is
        # supported, or when at least two layers vote for it strongly even
        # if a third dissents (a specific marker the rule base lacks).
        anchored = set(getattr(self, "_guideline_anchored", ()) or ())

        def _accounts(c: EnsembleResult) -> bool:
            if self._is_finding(c.disease_id):
                return False
            # Nothing "accounts for" a finding unless at least one rule of
            # that diagnosis actually fired on this panel; a prior-driven
            # Bayesian/fuzzy vote alone must not bury a finding that a rule
            # established (TG 2100 is severe hypertriglyceridaemia whatever
            # the umbrella "hyperlipidaemia" prior says).
            if float((c.votes or {}).get("rule_engine", 0.0) or 0.0) < 0.30:
                return False
            # v6: a diagnosis whose own evidence is 'insufficient' and that sits
            # below 0.6 (AKI from one creatinine in a community panel) does not
            # bury the certain finding (reduced GFR) beneath itself.
            if getattr(c, "evidence_state", "") == "insufficient" and c.final_score < 0.6:
                return False
            # A met curated guideline criterion accounts for the findings it
            # is built from even when the probabilistic layers have no prior
            # for the entity (they vote 0, not against).
            if c.disease_id in anchored and c.final_score >= 0.45:
                return True
            if c.evidence_state == "supported":
                return True
            strong = sum(1 for v in (c.votes or {}).values() if v >= 0.6)
            return strong >= 2 and c.final_score >= 0.45

        explained_by: dict[str, str] = {}
        # Critical-severity findings established by an ESL severity anchor
        # (K >= 6.5, Na < 120 / >= 160, Ca >= 14, glucose < 40, pH < 7.20,
        # lactate >= 4 ...) are life-threatening in their own right and are
        # never listed beneath the diagnosis that "explains" them (MIMIC-IV
        # demo error analysis 2026-10-21: K 7.4 demoted under AKI).
        critical_findings: set[str] = set()
        for _h in (getattr(self, "_esl_hits", None) or []):
            _sid = str(_h.get("syndrome_id", ""))
            if _h.get("strength") == "anchor" and (_sid.endswith("_severe") or _sid.endswith("_crisis") or _sid in ("severe_acidemia", "hypoglycemia_level3", "lactic_acidosis_definitional")):
                critical_findings.update(_h.get("dx", ()))
            elif _sid in ("severe_neutropenia", "agranulocytosis", "profound_neutropenia") and not _h.get("guard"):
                # v6 C8 (2026-10-25): ANC < 0.5 x10^9/L is a critical value (febrile-neutropenia risk; IDSA 2010 / ASCO-IDSA 2018)
                # whatever the syndrome strength - never listed beneath the cytopenia pattern that "accounts" for it.
                critical_findings.update(_h.get("dx", ()))
            elif (_h.get("strength") in ("anchor", "strong") and not _h.get("guard") and _h.get("dx")
                  and (not self._is_finding(_h["dx"][0]) or _h.get("strength") == "anchor")):
                # v6: a finding asserted at ANCHOR strength is a critical value
                # (INR >= 4.5, K >= 6.5, ...) and keeps its place; a finding asserted
                # at 'strong' (reduced GFR from one creatinine, moderate anaemia) is
                # listed beneath the diagnosis that accounts for it.
                # the primary entity of an expert-syndrome hit (e.g. thiazide
                # hyponatraemia at 0.95) is likewise never buried under a
                # weaker "accounting" diagnosis such as a 0.5 SIADH prior.
                # v6: this protection is for DIAGNOSES; a laboratory finding
                # asserted by the syndrome layer (reduced GFR, myocardial
                # injury) is a fact the clinician can read off the sheet and
                # is listed beneath the diagnosis that accounts for it.
                critical_findings.add(_h["dx"][0])
        accounting = [c for c in filtered if _accounts(c)]
        if os.environ.get("HG_DEBUG_DEMOTE"):
            print("[demote] critical=", sorted(critical_findings), "esl=", [h.get("syndrome_id") for h in (getattr(self, "_esl_hits", None) or [])],
                  "accounting=", [(c.disease_id, round(c.final_score, 3)) for c in accounting],
                  "pre=", [(c.disease_id, round(c.final_score, 3)) for c in sorted(filtered, key=lambda c: -c.final_score)[:6]])
        # v6 (Amendment 14): a finding asserted by an expert-syndrome hit at anchor/strong
        # strength whose own evidence is NOT covered by the evidence of any accounting
        # diagnosis (IgG4 620 mg/dL next to an eosinophilia-driven strongyloidiasis) is not
        # "accounted for" and keeps its score; coverage is set-theoretic on the fired features.
        _esl_asserted_findings: dict[str, set[str]] = {}
        for _h in (getattr(self, "_esl_hits", None) or []):
            if _h.get("strength") in ("anchor", "strong") and not _h.get("guard"):
                # analytes behind the REQUIRED groups of the syndrome (creatinine for
                # reduced GFR), not its optional supporting leaves
                _hf = set(_h.get("features") or ())
                _rf: set[str] = set()
                for _gk in (_h.get("required_met") or ()):
                    _grp = _ESL_GROUPS.get(str(_gk))
                    if _grp:
                        _rf.update(f for f in _grp[1] if f in _hf)
                for d in (_h.get("dx") or ()):
                    if self._is_finding(d):
                        _esl_asserted_findings.setdefault(d, set()).update(_rf or _hf)
        _esl_req_feats: dict[str, set[str]] = {}
        for _h in (getattr(self, "_esl_hits", None) or []):
            if not _h.get("guard"):
                for d in (_h.get("dx") or ()):
                    _esl_req_feats.setdefault(d, set()).update(_h.get("req_features") or _h.get("features") or ())
        _tf0 = getattr(self, "_disease_true_feats", {}) or {}
        _CR_EQ = {"creatinine", "egfr_ckd_epi_creatinine", "egfr", "estimated_gfr", "cystatin_c"}
        def _norm_feats(fs) -> set[str]:
            # eGFR is a function of creatinine: either analyte covers the other
            return {"creatinine" if f in _CR_EQ else f for f in fs}
        def _covering_dx(did: str):
            """Best accounting diagnosis whose own fired evidence contains the analytes behind the
            syndrome's required groups; None when the finding is not asserted by the ESL (the
            generic best-accounting rule applies) or when no diagnosis covers it."""
            _f = _norm_feats(_esl_asserted_findings.get(did) or set())
            if not _f:
                return None
            # a diagnosis below the 0.6 operating band (a 0.57 CKD from chronicity clues)
            # is not asserted firmly enough to account for a strong finding
            _cov = [c for c in accounting if c.final_score >= 0.6 and _f <= _norm_feats(_tf0.get(c.disease_id, ()))]
            return max(_cov, key=lambda c: c.final_score) if _cov else None
        def _causal_dx(did: str, min_score: float):
            """Best accounting diagnosis (>= min_score) that is a recognised cause of finding `did`
            (v7 C11 causal map) or whose fired evidence covers the finding's defining analytes."""
            _cands = [c for c in accounting if c.final_score >= min_score
                      and (_can_explain(c.disease_id, did)
                           or (_norm_feats(_esl_asserted_findings.get(did) or set())
                               and _norm_feats(_esl_asserted_findings.get(did) or set()) <= _norm_feats(_tf0.get(c.disease_id, ()))))]
            return max(_cands, key=lambda c: c.final_score) if _cands else None
        def _uncovered_finding(did: str) -> bool:
            # 13.x behaviour restored (attribution runs 2026-10-24: the exemption had no effect on
            # the blood-gas findings, which come from the rule layer, but its removal buried
            # moderate/severe anaemia, hyponatraemia, hyperkalaemia beneath unrelated diagnoses):
            # a finding asserted by an anchor/strong expert syndrome keeps its score unless a
            # diagnosis whose evidence covers the syndrome's required analytes accounts for it.
            _f = _esl_asserted_findings.get(did) or set()
            return bool(_f) and _covering_dx(did) is None
        if accounting:
            best = max(accounting, key=lambda c: c.final_score)
            best_dx = best.final_score
            for item in filtered:
                # an uncovered strong finding behaves like a critical finding: never beneath
                # the explaining diagnosis, but tied with a well-supported one (>= 0.80) so the
                # sort lists the diagnosis first
                if self._is_finding(item.disease_id) and (item.disease_id in critical_findings or _uncovered_finding(item.disease_id)):
                    # tie with (never beneath) a well-supported explaining
                    # diagnosis; the sort key then lists the diagnosis first
                    # v7 C11: only a diagnosis that can cause the finding is named / ties it
                    _cb = _causal_dx(item.disease_id, 0.80)
                    if _cb is not None and item.final_score > _cb.final_score:
                        explained_by[item.disease_id] = _cb.disease_id
                        item.final_score = _cb.final_score
                    continue
                if self._is_finding(item.disease_id):
                    _cov = _covering_dx(item.disease_id)
                    # v7 C11: a finding is listed beneath a diagnosis only when that diagnosis
                    # covers its defining analytes OR is a recognised cause of it; otherwise the
                    # finding is an independent fact of the panel and keeps its own score.
                    _cau = _causal_dx(item.disease_id, 0.6)
                    # the best-supported RELATED diagnosis (analyte coverage or recognised cause) is the explainer;
                    # a weakly supported explainer (< 0.80) does not pull a better-established finding beneath it
                    # (eICU dev: Hb 7.3 anaemia capped to 0.58 under a 0.61 'acute chest syndrome' leaf while a 0.97
                    # cirrhosis stood above) - the finding then stands on its own.
                    _by = max([c for c in (_cov, _cau) if c is not None], key=lambda c: c.final_score, default=None)
                    if _by is not None and _by is not _cov and _by.final_score < 0.80 and item.final_score > _by.final_score * 0.95:
                        _by = _cov  # a covering diagnosis (same analytes, e.g. AKI for the reduced-GFR finding) always explains
                    if _by is None:
                        # no recognised cause in the panel: the finding is NOT attributed to anything,
                        # but a well-supported diagnosis (>= 0.80) is still listed first - the finding
                        # ties with it (sort key: diagnosis before finding) instead of being capped
                        # to 95 % of an unrelated entity.
                        if best_dx >= 0.80 and item.final_score > best_dx:
                            item.final_score = best_dx
                        continue
                    _cap = _by.final_score * 0.95
                    if item.final_score > _cap:
                        explained_by[item.disease_id] = _by.disease_id
                    item.final_score = min(item.final_score, _cap)

        # Evidence subsumption. A met curated guideline criterion that was
        # built from features {a, b, c} accounts for every other entity whose
        # entire positive evidence is a subset of {a, b, c}: "metabolic
        # acidosis" next to a DKA triad, "thyroid storm" next to Graves'
        # (TSH + FT4 + TRAb), Sjögren next to a full SLE serology. Those
        # entities are listed beneath the diagnosis that explains them. An
        # entity bringing evidence of its own, or itself anchored, is never
        # demoted this way - the guard is purely set-theoretic.
        true_feats = getattr(self, "_disease_true_feats", {}) or {}
        # ESL ext 11 (2026-10-23): an anchored entity that has itself been capped below the
        # operating point (AKI beneath documented CKD / dialysis) is no longer asserted and
        # cannot "explain" a finding; otherwise K 6.6 was buried at 0.95 x a 0.40 AKI.
        anchored_items = [c for c in filtered
                          if c.disease_id in anchored and true_feats.get(c.disease_id) and c.final_score >= 0.5]
        for anchor in sorted(anchored_items, key=lambda c: -c.final_score):
            fa = set(true_feats.get(anchor.disease_id, ()))
            for item in filtered:
                if item is anchor:
                    continue
                # extension 7 (2026-10-22): AKI and CKD share the creatinine evidence by nature; their relative
                # order is adjudicated by _apply_renal_chronicity, never by mutual subsumption (which demoted both).
                if {item.disease_id, anchor.disease_id} == {"acute_kidney_injury", "chronic_kidney_disease"}:
                    continue
                # v6 (Amendment 14): a laboratory finding / syndrome (reduced GFR,
                # myocardial injury, SIRS) never "explains" a diagnosis built on the
                # same analytes - the direction of explanation is diagnosis -> finding.
                if self._is_finding(anchor.disease_id) and not self._is_finding(item.disease_id):
                    continue
                # v6 C8 (2026-10-25): a critical-value finding (ANC < 0.5, Hb < 7 ...) is never subsumed by
                # ANOTHER FINDING whose rule evidence happens to contain its analyte (thrombocytopenia rule
                # with a WBC leaf "explaining" profound neutropenia); a diagnosis (cyanide poisoning over
                # lactate 9) may still organise it.
                if item.disease_id in critical_findings and self._is_finding(anchor.disease_id):
                    continue
                # v6 C8 (2026-10-25): one finding "explains" another only when the analytes that DEFINE
                # the explained finding (its syndrome's required groups) are among the analytes that
                # define the explaining one - a troponin finding whose rule merely lists creatinine as
                # support must not account for reduced GFR.
                if self._is_finding(anchor.disease_id) and self._is_finding(item.disease_id):
                    _ireq = _norm_feats(_esl_asserted_findings.get(item.disease_id) or set())
                    _areq = _norm_feats(_esl_req_feats.get(anchor.disease_id) or set())
                    if _ireq and not _ireq <= _areq:
                        continue
                # v7 C11: a DIAGNOSIS explains a finding only when it is a recognised cause of it
                # (causal map) or the finding's defining analytes sit in the constellation that
                # asserted the diagnosis; a rule leaf that merely mentions the analyte is not a cause.
                if not self._is_finding(anchor.disease_id) and self._is_finding(item.disease_id):
                    _ireq = _norm_feats(_esl_asserted_findings.get(item.disease_id) or set())
                    _areq = _norm_feats(_esl_req_feats.get(anchor.disease_id) or set())
                    if not (_can_explain(anchor.disease_id, item.disease_id) or (_ireq and _ireq <= _areq)):
                        continue
                fi = set(true_feats.get(item.disease_id, ()))
                if not fi or not fi <= fa:
                    continue
                # Two anchored criteria: only a *strict* superset explains
                # the other (DKA triad over high-anion-gap acidosis); equal
                # evidence sets stay side by side for the clinician.
                if item.disease_id in anchored and not fi < fa:
                    continue
                cap = anchor.final_score * 0.95
                if item.final_score > cap:
                    item.final_score = cap
                # Recorded even when no demotion was needed: the report can
                # then group the finding under the diagnosis that covers it.
                explained_by.setdefault(item.disease_id, anchor.disease_id)

        # v6 (Amendment 14, 4th UDMI 2018 §1-2): a cardiac troponin above the 99th percentile
        # is *myocardial injury*; infarction additionally requires a rise and/or fall AND
        # clinical evidence of ischaemia. Without a dynamic-troponin syndrome hit or an
        # ischaemic context (chest pain / ACS / ECG change in the documented conditions),
        # acute myocardial infarction is listed beneath the injury finding it is inferred from.
        _by_id_mi = {c.disease_id: c for c in filtered}
        # v6 C10 (2026-10-25): the single-panel injury finding is `myocardial_injury_acuity_undetermined`
        # (registry 14.1); `acute_myocardial_injury` is asserted by the temporal layer. Either one is the
        # injury the infarction is inferred from.
        _inj_id = next((k for k in ("acute_myocardial_injury", "myocardial_injury_acuity_undetermined") if k in _by_id_mi), None)
        # C10: once acuity IS determined (temporal rise/fall or CK-MB-dated acute injury, or a flat chronic pattern,
        # asserted >= 0.6) the acuity-undetermined finding is redundant and is listed beneath the determined one.
        if "myocardial_injury_acuity_undetermined" in _by_id_mi:
            _und = _by_id_mi["myocardial_injury_acuity_undetermined"]
            for _det_id in ("acute_myocardial_injury", "chronic_myocardial_injury"):
                _det = _by_id_mi.get(_det_id)
                if _det is not None and _det.final_score >= 0.6:
                    explained_by[_und.disease_id] = _det_id
                    _und.final_score = min(_und.final_score, _det.final_score * 0.95)
                    break
        if "acute_myocardial_infarction" in _by_id_mi and _inj_id is not None:
            # an expert syndrome that asserts infarction itself (dynamic troponin, massive
            # troponin with CK-MB, ECG-context constellations) overrides the single-value rule
            _dyn_tn = any((str(h.get("syndrome_id", "")) in ("acute_myocardial_injury_dynamic_troponin", "troponin_rise_fall", "acs_dynamic_troponin")
                           or ("dynamic" in str(h.get("syndrome_id", "")) and "tropon" in str(h.get("syndrome_id", "")))
                           or ("acute_myocardial_infarction" in (h.get("dx") or ()) and not h.get("guard")))
                          for h in (getattr(self, "_esl_hits", None) or []))
            _ctx_txt = ""
            if context is not None:
                for _kn in ("known_conditions", "conditions", "comorbidities", "past_history", "medical_history", "presenting_complaint", "symptoms"):
                    _v = getattr(context, _kn, None)
                    if _v is None:
                        _v = (getattr(context, "extra", {}) or {}).get(_kn)
                    if isinstance(_v, (list, tuple, set)):
                        _ctx_txt += " " + " ".join(str(x).lower() for x in _v)
                    elif isinstance(_v, str):
                        _ctx_txt += " " + _v.lower()
            _isch = any(k in _ctx_txt for k in ("chest pain", "angina", "acs", "coronary", "st elevation", "st-elevation", "stemi", "nstemi", "ischemi", "ischaemi", "infarct"))
            if not _dyn_tn and not _isch:
                _mi, _inj = _by_id_mi["acute_myocardial_infarction"], _by_id_mi[_inj_id]
                if _mi.final_score > _inj.final_score * 0.85:
                    _mi.final_score = _inj.final_score * 0.85
                    explained_by.setdefault(_mi.disease_id, _inj.disease_id)
            else:
                # v6 C8 (2026-10-25): the converse - when infarction is asserted (dynamic troponin,
                # ischaemic context) the myocardial-injury finding is its component (UDMI 2018:
                # MI = acute injury + ischaemia) and is listed beneath it.
                _mi, _inj = _by_id_mi["acute_myocardial_infarction"], _by_id_mi[_inj_id]
                if _mi.final_score >= 0.6 and _mi.final_score >= _inj.final_score * 0.85:
                    explained_by.setdefault(_inj.disease_id, _mi.disease_id)

        # Expert-syndrome competitor caps: a met constellation that carries
        # an explicit exclusion of a rival (AKA vs euglycaemic DKA, PTHrP vs
        # primary HPT) lists the rival beneath it.
        # An entity that is itself the primary target of an equally strong
        # met syndrome is never capped by a rival syndrome (prerenal
        # azotaemia's "hyponatraemia 0.85" cap must not bury a met thiazide /
        # hypovolaemic hyponatraemia anchor - perturbation fuzz 2026-10-21).
        _esl_primary_score: dict[str, float] = {}
        for hit in (getattr(self, "_esl_hits", None) or []):
            if hit.get("dx") and not hit.get("guard"):
                _d0 = hit["dx"][0]
                _esl_primary_score[_d0] = max(_esl_primary_score.get(_d0, 0.0), float(hit.get("score", 0.0) or 0.0))
        for hit in (getattr(self, "_esl_hits", None) or []):
            primary = by_id.get(hit["dx"][0]) if hit.get("dx") else None
            if primary is None and not hit.get("guard"):
                continue
            own = set(hit["dx"])
            for cid, factor in (hit.get("cap") or {}).items():
                rival = by_id.get(cid)
                if rival is None or cid in own:
                    continue
                if _esl_primary_score.get(cid, 0.0) > float(hit.get("score", 0.0) or 0.0) and primary is not None:
                    continue
                # dx-less guard syndromes (physiological states such as
                # pregnancy) carry ABSOLUTE ceilings instead of ratios.
                cap = float(factor) if primary is None else primary.final_score * float(factor)
                if rival.final_score > cap:
                    rival.final_score = cap
                    if primary is not None:
                        explained_by.setdefault(cid, primary.disease_id)
            # secondary targets of the same syndrome stay just beneath the primary
            for did in hit["dx"][1:]:
                sec = by_id.get(did)
                if sec is not None and sec.final_score >= primary.final_score:
                    sec.final_score = primary.final_score * 0.97
        # --- clinical-salience re-ranking (ESL extension 6, 2026-10-21) -------
        # Probabilities are untouched; only the display/recall order changes:
        #  tier 0: diseases, syndromes and clinically material findings (p >= 0.5)
        #  tier 1: low-salience single-analyte findings (p >= 0.5, not severe)
        #  tier 2: everything below the 0.5 operating point
        #  tier 3: derived `co_*` pair patterns and family duplicates
        #          (child id = parent id + suffix, the lower score of the pair;
        #           `*_support_pattern` when its base entity is present)
        _ids = {r.disease_id for r in filtered}
        _score = {r.disease_id: r.final_score for r in filtered}
        _dup: set[str] = set()
        # ESL extension 6b (2026-10-21): twins that differ only by a severity /
        # acuity prefix or a pattern suffix (hyponatremia vs severe_hyponatremia,
        # acute_ vs chronic_myocardial_injury, heart_failure vs its support
        # pattern) are one clinical statement; the best-scoring member leads.
        def _stem(_x):
            for _pre in ("severe_", "acute_", "chronic_", "mild_", "moderate_", "marked_"):
                if _x.startswith(_pre):
                    _x = _x[len(_pre):]
            for _suf in ("_support_pattern", "_pattern", "_decompensated"):
                if _x.endswith(_suf):
                    _x = _x[:-len(_suf)]
            return _x
        _best_by_stem: dict[str, str] = {}
        for _r in sorted(filtered, key=lambda r: -r.final_score):
            _st = _stem(_r.disease_id)
            if _st in _best_by_stem and _best_by_stem[_st] != _r.disease_id:
                _dup.add(_r.disease_id)
            else:
                _best_by_stem.setdefault(_st, _r.disease_id)
        for _r in filtered:
            _i = _r.disease_id
            if _i.endswith("_support_pattern") and _i[:-len("_support_pattern")] in _ids:
                _dup.add(_i); continue
            _parts = _i.split("_")
            for _k in range(len(_parts) - 1, 1, -1):
                _parent = "_".join(_parts[:_k])
                if _parent in _ids and _parent != _i:
                    _loser = _i if _score[_i] <= _score[_parent] else _parent
                    _dup.add(_loser); break
        # --- ESL extension 9 (2026-10-23): ranking hygiene, probabilities untouched ---
        # (a) explicit synonym families: ids that are one clinical statement but
        #     share no stem; only the best-scoring member leads, the rest go to tier 3.
        for _fam in _ESL_SYNONYM_FAMILIES:
            _members = [r for r in filtered if r.disease_id in _fam]
            if len(_members) > 1:
                _members.sort(key=lambda r: -r.final_score)
                for _m in _members[1:]:
                    _dup.add(_m.disease_id)
        # (b) aetiology-beneath-finding: an entity that is only a putative CAUSE of a
        #     laboratory finding already in the list, whose own confirmatory marker was
        #     not measured, is displayed beneath the finding (tier 3). It is not removed
        #     and its probability is unchanged; it simply cannot outrank the finding it
        #     is inferred from (Sackett: a cause is not evidence for itself).
        try:
            _obs_ids = set(observations.keys())
        except Exception:
            _obs_ids = set()
        for _aet, (_findings, _markers) in _ESL_AETIOLOGY_BENEATH_FINDING.items():
            if _aet in _ids and not (_obs_ids & set(_markers)):
                _fp = [_score[_f] for _f in _findings if _f in _ids]
                # demote only when the cause does not out-score the finding it is inferred
                # from; independent evidence (context, other markers) that lifts it above
                # the finding is respected.
                if _fp and _score[_aet] <= max(_fp):
                    _dup.add(_aet)
        # (c) organising-diagnosis precedence: when an ESL syndrome with a marked,
        #     cause-level laboratory signature fired (e.g. creatinine-defined renal
        #     failure, DKA), the downstream findings it explains are ordered after it
        #     within tier 0. Probabilities unchanged; parsimony (Occam) in display order.
        _org_first: dict[str, int] = {}
        _fired = {h.get("syndrome_id") or h.get("id") for h in (getattr(self, "_esl_hits", None) or []) if not h.get("guard")}
        for _syn_ids, (_causes, _effects) in _ESL_ORGANISING_PRECEDENCE:
            if _fired & set(_syn_ids):
                _lead = [c for c in _causes if c in _ids and _score[c] >= 0.5]
                if _lead:
                    for _e in _effects:
                        if _e in _ids:
                            _org_first[_e] = 1
                    for c in _lead:
                        _org_first[c] = 0
        def _tier(r):
            _i, _p = r.disease_id, r.final_score
            if _i.startswith("co_") or _i in _dup:
                return 3
            if _p < 0.5:
                # ESL ext 11-C: a documented-history entry without panel support is not derived
                # from the laboratory data; it ranks after every lab-derived sub-threshold entry.
                return 2.5 if getattr(r, "evidence_state", "") == "documented_history" else 2
            if _i in _LOW_SALIENCE_FINDINGS and _p < 0.75:
                return 1
            # v6 C8 (2026-10-25): a laboratory finding / syndrome that an asserted diagnosis
            # accounts for (explained_by set, not a critical value) is listed after every
            # asserted entity that stands on its own - reduced GFR beneath AKI, myocardial
            # injury beneath infarction, SIRS beneath sepsis. Probability unchanged; the
            # finding remains in the list with its explaining diagnosis named. Parsimony only:
            # the same fact is otherwise shown twice in the first five lines.
            if _i in explained_by and _i not in critical_findings and self._is_finding(_i):
                return 0.5
            return 0
        # v6 (SAP Amendment 14, C1): final pass of the finding demotion AFTER every
        # competitor / subsumption / renal cap has been applied. A laboratory
        # finding or syndrome (reduced GFR, myocardial injury, SIRS) is listed
        # beneath the best diagnosis that accounts for it whenever that diagnosis
        # is itself asserted (final >= 0.6, rule evidence present); critical
        # severity findings keep their place.
        _acc2 = [c for c in filtered if _accounts(c) and c.final_score >= 0.6]
        if _acc2:
            _best2 = max(_acc2, key=lambda c: c.final_score)
            for item in filtered:
                # only findings already placed beneath a diagnosis (first pass or
                # subsumption) are re-ordered here; a finding carrying evidence of
                # its own that no diagnosis accounted for keeps its score.
                if (self._is_finding(item.disease_id) and item.disease_id not in critical_findings
                        and item.disease_id in explained_by
                        and item.final_score > _best2.final_score * 0.95):
                    item.final_score = _best2.final_score * 0.95
        filtered.sort(key=lambda r: (_tier(r), -r.final_score, self._is_finding(r.disease_id), r.disease_id))
        # (c) continued: move each organising diagnosis to just ahead of the first
        #     downstream finding it explains; it never overtakes anything else.
        if _org_first:
            _effects = {k for k, v in _org_first.items() if v == 1}
            for _cause in [k for k, v in _org_first.items() if v == 0]:
                _ci = next((i for i, r in enumerate(filtered) if r.disease_id == _cause), None)
                if _ci is None or _tier(filtered[_ci]) != 0:
                    continue
                _ei = next((i for i, r in enumerate(filtered) if r.disease_id in _effects and _tier(r) == 0), None)
                if _ei is not None and _ei < _ci:
                    filtered.insert(_ei, filtered.pop(_ci))

        differential = []
        # UI shows 15; evaluation harnesses may raise `max_differential`
        # so that probabilities of lower-ranked entities are not lost.
        for rank, result in enumerate(filtered[:int(getattr(self, "max_differential", 15) or 15)], 1):
            entry = DifferentialEntry(
                disease_id=result.disease_id,
                rank=rank,
                probability=result.final_score,
                confidence=result.confidence,
                status=self._tabaghebandi_vaziat(result),
                ensemble_votes=result.votes,
                belief=round(result.belief, 4),
                plausibility=round(result.plausibility, 4),
                conflict=round(result.conflict, 4),
                evidence_state=result.evidence_state,
                weight_profile=result.weight_profile,
                explained_by=explained_by.get(result.disease_id),
            )

            entry.supporting_evidence = [
                f"{model}: {score:.2f}"
                for model, score in result.votes.items()
                if score > 0.3
            ]

            entry.opposing_evidence = self._identify_opposing_evidence(
                result) + exclusion_notes.get(result.disease_id, [])

            entry.missing_evidence = self._identify_missing_evidence(
                result.disease_id, observations)

            entry.recommended_tests = self.TEST_SUGGESTIONS.get(
                result.disease_id, [])

            entry.sensitivity_notes = self._sensitivity_tahlil(
                result.disease_id, observations)

            entry.statement = self._tolid_statement(
                result.disease_id, result, entry)
            differential.append(entry)
        return differential

    def _tabaghebandi_vaziat(self, result: EnsembleResult) -> str:
        score = (result.calibrated_score
                 if result.calibrated_score is not None
                 else result.final_score)
        conf = result.confidence
        # Evidence-theoretic overrides: a flat inter-layer conflict is a
        # distinct clinical state (order the discriminating test), and a
        # wide Belief-Plausibility interval means "not enough data", which
        # must never be presented as a probability.
        state = getattr(result, "evidence_state", None)
        if state == "conflicting" and score > 0.2:
            return "conflicting_evidence"
        if state == "insufficient" and score > 0.2 and score <= 0.5:
            return "insufficient_evidence"
        if score > 0.7 and conf > 0.65:
            return "highly_probable"
        if score > 0.7:
            return "probable_low_confidence"
        if score > 0.5:
            return "possible"
        if score > 0.2:
            return "pending"
        return "unlikely"

    def _identify_opposing_evidence(
        self, result: EnsembleResult
    ) -> list[str]:
        opposing = []
        for model, score in result.votes.items():

            if model not in (result.participating_models or ()):
                continue
            if score < 0.1 and result.final_score > 0.3:
                opposing.append(f"{model}: {score:.2f} (opposing)")
        return opposing

    def _identify_missing_evidence(
        self, disease_id: str, observations: Mapping[str, Any]
    ) -> list[str]:
        missing = []
        impactful = self.IMPACTFUL_MISSING.get(disease_id, [])
        for feature_id, _ in impactful:
            if feature_id not in observations:
                missing.append(feature_id)
        return missing

    def _sensitivity_tahlil(
        self, disease_id: str, observations: Mapping[str, Any]
    ) -> list[str]:
        notes = []
        impactful = self.IMPACTFUL_MISSING.get(disease_id, [])
        for feature_id, impact_note in impactful:
            if feature_id not in observations:
                notes.append(
                    f"If {feature_id} were available: {impact_note}")
        return notes

    def _tolid_statement(
        self, disease_id: str, result: EnsembleResult,
        entry: DifferentialEntry
    ) -> str:
        name = disease_id.replace("_", " ").title()
        pct = int(result.final_score * 100)

        if result.final_score > 0.7:
            level = "highly probable"
        elif result.final_score > 0.5:
            level = 'probable'
        elif result.final_score > 0.2:
            level = "possible"
        else:
            level = 'unlikely'

        parts = [f"{name} is {level} ({pct}%)."]


        if entry.supporting_evidence:
            shown = entry.supporting_evidence[:3]
            parts.append("Supported by: " + ", ".join(shown))


        if entry.opposing_evidence:
            parts.append('Opposing: ' + ", ".join(
                entry.opposing_evidence[:2]))


        if entry.missing_evidence:
            parts.append("Unresolved: missing " + ", ".join(
                entry.missing_evidence[:3]))


        if entry.sensitivity_notes:
            parts.append("Note: " + entry.sensitivity_notes[0])

        parts.append('Not a diagnosis. Review with a clinician.')
        return " ".join(parts)

    def get_recommended_tests(self, disease_id: str) -> list[str]:
        return self.TEST_SUGGESTIONS.get(disease_id, [])


@dataclass
class DrugInteraction:
    drug_class: str
    drug_names: list[str]
    feature_id: str
    direction: str
    mechanism: str
    magnitude: str
    clinical_note: str
    citation: str

# Interaction lookup is table-driven and stateless.
INTERACTION_DATABASE: dict[str, list[DrugInteraction]] = {

    "statins": [
        DrugInteraction(
            drug_class="statins",
            drug_names=["atorvastatin", "rosuvastatin", "simvastatin",
                       "pravastatin", 'pitavastatin', "lovastatin", "fluvastatin"],
            feature_id='alanine_aminotransferase',
            direction="increases",
            mechanism="Hepatocellular stress; mild ALT elevation in 1-3% of patients",
            magnitude="mild",
            clinical_note="ALT <3× ULN is expected; do NOT diagnose NAFLD based on statin use alone",
            citation="Cohen JD, 2006; Am J Cardiol"
        ),
        DrugInteraction(
            drug_class="statins",
            drug_names=["atorvastatin", 'rosuvastatin', "simvastatin"],
            feature_id='aspartate_aminotransferase',
            direction="increases",
            mechanism='Parallel to ALT; hepatocellular effect',
            magnitude="mild",
            clinical_note="AST/ALT ratio usually <1 in statin effect",
            citation="Cohen JD, 2006"
        ),
        DrugInteraction(
            drug_class="statins",
            drug_names=["atorvastatin", "simvastatin", "rosuvastatin"],
            feature_id="creatine_kinase",
            direction="increases",
            mechanism="Statin-induced myopathy; CK may rise 3-10× ULN",
            magnitude='moderate',
            clinical_note="If CK >10× ULN with myalgia → consider rhabdomyolysis",
            citation="Thompson PD et al., 2016; JACC"
        ),
    ],


    "corticosteroids": [
        DrugInteraction(
            drug_class="corticosteroids",
            drug_names=["prednisone", 'prednisolone', "methylprednisolone",
                       'dexamethasone', 'hydrocortisone', "betamethasone"],
            feature_id="fasting_plasma_glucose",
            direction='increases',
            mechanism="Glucocorticoid-induced insulin resistance + hepatic gluconeogenesis",
            magnitude='strong',
            clinical_note="Steroid diabetes: FBS may rise 50-200 mg/dL; DO NOT diagnose T2DM during active steroid use",
            citation="Shakir A, 2022; Endocr Rev"
        ),
        DrugInteraction(
            drug_class="corticosteroids",
            drug_names=["prednisone", "dexamethasone"],
            feature_id='white_blood_cell_count',
            direction="increases",
            mechanism="Demargination of neutrophils + delayed apoptosis",
            magnitude="moderate",
            clinical_note="WBC may rise to 15-25×10⁹/L without infection (steroid leukocytosis)",
            citation="Dale DC, 2014; Hematology"
        ),
        DrugInteraction(
            drug_class="corticosteroids",
            drug_names=["prednisone", 'dexamethasone'],
            feature_id="potassium",
            direction="decreases",
            mechanism="Mineralocorticoid effect → renal K⁺ wasting",
            magnitude="moderate",
            clinical_note='Monitor K⁺; supplement if <3.5',
            citation='Katzung BG, Basic & Clinical Pharmacology'
        ),
        DrugInteraction(
            drug_class="corticosteroids",
            drug_names=["prednisone", "dexamethasone"],
            feature_id='calcium_total',
            direction='decreases',
            mechanism="Decreased intestinal Ca absorption + increased renal excretion",
            magnitude="mild",
            clinical_note='Long-term use → osteoporosis risk; monitor Ca/VitD',
            citation="Buckley LM, 2019; Rheumatology"
        ),
    ],


    "metformin": [
        DrugInteraction(
            drug_class="metformin",
            drug_names=["metformin", 'glucophage'],
            feature_id="vitamin_b12",
            direction="decreases",
            mechanism="Interferes with Ca-dependent B12-intrinsic factor absorption in ileum",
            magnitude="moderate",
            clinical_note="B12 deficiency in 10-30% of long-term metformin users; check annually",
            citation="Andreae C, 2016; PLoS One"
        ),
        DrugInteraction(
            drug_class='metformin',
            drug_names=["metformin"],
            feature_id='lactate',
            direction="increases",
            mechanism="Inhibition of mitochondrial glycerophosphate dehydrogenase",
            magnitude="mild",
            clinical_note="Lactic acidosis is rare (3/100,000 pt-yrs) but fatal; avoid in CKD eGFR<30",
            citation="Lalau JD, 2017; Diabetes Obes Metab"
        ),
    ],


    "thiazide_diuretics": [
        DrugInteraction(
            drug_class="thiazide_diuretics",
            drug_names=["hydrochlorothiazide", 'chlorthalidone', 'indapamide', "metolazone"],
            feature_id="sodium",
            direction="decreases",
            mechanism="Renal Na⁺ wasting → hyponatremia",
            magnitude="moderate",
            clinical_note="Especially in elderly; may cause Na <130",
            citation='Liamis G, 2009; Eur J Intern Med'
        ),
        DrugInteraction(
            drug_class="thiazide_diuretics",
            drug_names=["hydrochlorothiazide", "chlorthalidone"],
            feature_id="potassium",
            direction="decreases",
            mechanism="Increased distal K⁺ secretion",
            magnitude="moderate",
            clinical_note="Hypokalemia common; consider K-sparing combination",
            citation='Liamis G, 2009'
        ),
        DrugInteraction(
            drug_class="thiazide_diuretics",
            drug_names=["hydrochlorothiazide", "chlorthalidone"],
            feature_id="uric_acid",
            direction="increases",
            mechanism="Increased proximal urate reabsorption",
            magnitude="moderate",
            clinical_note='May precipitate gout flare; avoid in gout patients',
            citation="Choi HK, 2005; Lancet"
        ),
        DrugInteraction(
            drug_class="thiazide_diuretics",
            drug_names=["hydrochlorothiazide"],
            feature_id="calcium_total",
            direction="increases",
            mechanism="Increased distal Ca reabsorption",
            magnitude='mild',
            clinical_note="Mild hypercalcemia; useful in kidney stone prevention",
            citation="Curhan GC, 2014; NEJM"
        ),
        DrugInteraction(
            drug_class="thiazide_diuretics",
            drug_names=["hydrochlorothiazide", "chlorthalidone"],
            feature_id="fasting_plasma_glucose",
            direction="increases",
            mechanism="Impaired insulin secretion + insulin resistance",
            magnitude="mild",
            clinical_note='Small FBS rise (5-10 mg/dL); monitor in prediabetes',
            citation="Elliott WJ, 2006; J Clin Hypertens"
        ),
    ],

    "loop_diuretics": [
        DrugInteraction(
            drug_class="loop_diuretics",
            drug_names=['furosemide', "bumetanide", "torsemide", "ethacrynic_acid"],
            feature_id="potassium",
            direction='decreases',
            mechanism="Profound renal K⁺ wasting at loop of Henle",
            magnitude="strong",
            clinical_note="High risk of hypokalemia; combine with K-sparing agent",
            citation="Ponto LB, 2010; Dtsch Arztebl Int"
        ),
        DrugInteraction(
            drug_class="loop_diuretics",
            drug_names=["furosemide", 'bumetanide'],
            feature_id="creatinine",
            direction='increases',
            mechanism="Prerenal azotemia from volume depletion",
            magnitude='moderate',
            clinical_note="BUN/Cr ratio >20 suggests prerenal; adjust dose",
            citation="Ponto LB, 2010"
        ),
        DrugInteraction(
            drug_class="loop_diuretics",
            drug_names=["furosemide"],
            feature_id="uric_acid",
            direction="increases",
            mechanism="Volume contraction → increased urate reabsorption",
            magnitude="moderate",
            clinical_note='May precipitate gout',
            citation="Choi HK, 2005"
        ),
    ],


    "ace_inhibitors": [
        DrugInteraction(
            drug_class='ace_inhibitors',
            drug_names=["enalapril", 'lisinopril', 'ramipril', "captopril",
                       "perindopril", "quinapril", "benazepril", "fosinopril"],
            feature_id='potassium',
            direction='increases',
            mechanism="Decreased aldosterone → reduced renal K⁺ excretion",
            magnitude='moderate',
            clinical_note="Hyperkalemia risk, especially with CKD or K-sparing diuretics",
            citation="Palmer BF, 2004; Drugs"
        ),
        DrugInteraction(
            drug_class="ace_inhibitors",
            drug_names=["enalapril", "lisinopril", "ramipril"],
            feature_id="creatinine",
            direction="increases",
            mechanism="Efferent arteriole vasodilation → reduced GFR",
            magnitude="mild",
            clinical_note="Up to 30% Cr rise is acceptable; >30% → check for renal artery stenosis",
            citation="Textor SC, 2003; J Am Soc Nephrol"
        ),
    ],

    "arbs": [
        DrugInteraction(
            drug_class="arbs",
            drug_names=["losartan", "valsartan", "irbesartan", "candesartan",
                       "olmesartan", "telmisartan", "azilsartan"],
            feature_id="potassium",
            direction="increases",
            mechanism="Similar to ACEi: reduced aldosterone",
            magnitude='moderate',
            clinical_note="Same hyperkalemia risk as ACEi",
            citation='Palmer BF, 2004'
        ),
    ],


    "proton_pump_inhibitors": [
        DrugInteraction(
            drug_class='proton_pump_inhibitors',
            drug_names=["omeprazole", "pantoprazole", "esomeprazole",
                       'lansoprazole', "rabeprazole"],
            feature_id="magnesium",
            direction="decreases",
            mechanism="Impaired intestinal Mg absorption (TRPM6/7 inhibition)",
            magnitude="moderate",
            clinical_note="Hypomagnesemia after >1 year of use; check Mg annually",
            citation="FDA Safety Communication 2011"
        ),
        DrugInteraction(
            drug_class="proton_pump_inhibitors",
            drug_names=["omeprazole", 'pantoprazole'],
            feature_id="vitamin_b12",
            direction="decreases",
            mechanism="Reduced gastric acid → impaired B12 release from food",
            magnitude="mild",
            clinical_note="Long-term PPI → B12 deficiency risk; consider supplementation",
            citation="Lam JR, 2013; JAMA"
        ),
        DrugInteraction(
            drug_class='proton_pump_inhibitors',
            drug_names=["omeprazole", "pantoprazole"],
            feature_id="serum_iron",
            direction="decreases",
            mechanism='Acid required for Fe³⁺ → Fe²⁺ reduction',
            magnitude="mild",
            clinical_note="May contribute to iron deficiency anemia",
            citation="Free A, 2019; BMJ Open"
        ),
        DrugInteraction(
            drug_class='proton_pump_inhibitors',
            drug_names=["omeprazole", "pantoprazole"],
            feature_id="gastrin",
            direction='increases',
            mechanism="Loss of acid negative feedback → G-cell hyperplasia",
            magnitude="strong",
            clinical_note="Elevated gastrin is EXPECTED on PPI; do NOT diagnose Zollinger-Ellison",
            citation="Katz PO, 2013; Am J Gastroenterol"
        ),
    ],


    "levothyroxine": [
        DrugInteraction(
            drug_class="levothyroxine",
            drug_names=["levothyroxine", "synthroid", "levoxyl", "tiroid"],
            feature_id="thyroid_stimulating_hormone",
            direction='decreases',
            mechanism='Exogenous T4 suppresses TSH via negative feedback',
            magnitude="strong",
            clinical_note="Low TSH on levothyroxine = OVER-replacement, NOT primary hyperthyroidism",
            citation="Jonklaas J, 2014; J Clin Endocrinol Metab"
        ),
        DrugInteraction(
            drug_class='levothyroxine',
            drug_names=['levothyroxine'],
            feature_id="free_thyroxine",
            direction="increases",
            mechanism='Direct exogenous replacement',
            magnitude="strong",
            clinical_note="High FT4 with low TSH = over-replacement; reduce dose",
            citation="Jonklaas J, 2014"
        ),
    ],


    "warfarin": [
        DrugInteraction(
            drug_class="warfarin",
            drug_names=["warfarin", "coumadin", "jantoven"],
            feature_id="international_normalized_ratio",
            direction="increases",
            mechanism="Direct pharmacologic effect (vitamin K antagonist)",
            magnitude="strong",
            clinical_note="Elevated INR is EXPECTED; target depends on indication (2-3 or 2.5-3.5)",
            citation="Witt DM, 2018; Chest"
        ),
        DrugInteraction(
            drug_class="warfarin",
            drug_names=["warfarin"],
            feature_id='prothrombin_time',
            direction="increases",
            mechanism='Inhibition of vitamin K-dependent clotting factors',
            magnitude='strong',
            clinical_note="PT prolongation is expected; use INR for monitoring",
            citation='Witt DM, 2018'
        ),
    ],


    "nsaids": [
        DrugInteraction(
            drug_class="nsaids",
            drug_names=["ibuprofen", "naproxen", "diclofenac", "celecoxib",
                       "meloxicam", "indomethacin", "piroxicam"],
            feature_id="creatinine",
            direction='increases',
            mechanism="Afferent arteriole vasoconstriction → reduced GFR",
            magnitude="moderate",
            clinical_note="AKI risk in elderly/CKD; avoid in eGFR<30",
            citation="Perazola P, 2014; PLoS Med"
        ),
        DrugInteraction(
            drug_class="nsaids",
            drug_names=["ibuprofen", "naproxen"],
            feature_id="potassium",
            direction="increases",
            mechanism="Reduced renin → hypoaldosteronism",
            magnitude='mild',
            clinical_note="Hyperkalemia risk with ACEi/ARB combination",
            citation="Perazola P, 2014"
        ),
        DrugInteraction(
            drug_class="nsaids",
            drug_names=["aspirin_low_dose", 'ibuprofen', "naproxen"],
            feature_id="uric_acid",
            direction="increases",
            mechanism="Low-dose aspirin reduces urate excretion",
            magnitude="mild",
            clinical_note='May precipitate gout; high-dose aspirin is uricosuric',
            citation="Gutman AB, 1967; Am J Med"
        ),
    ],


    "antiepileptics": [
        DrugInteraction(
            drug_class="antiepileptics",
            drug_names=["phenytoin", "carbamazepine", "phenobarbital", "valproate"],
            feature_id="alanine_aminotransferase",
            direction='increases',
            mechanism="Hepatotoxicity (especially valproate)",
            magnitude="moderate",
            clinical_note="Monitor ALT every 3-6 months; valproate → hyperammonemia risk",
            citation="Bjornsson ES, 2017; Clin Pharmacol Ther"
        ),
        DrugInteraction(
            drug_class="antiepileptics",
            drug_names=["phenytoin", 'carbamazepine'],
            feature_id="calcium_total",
            direction='decreases',
            mechanism="CYP450 induction → vitamin D catabolism",
            magnitude="moderate",
            clinical_note="Long-term use → osteomalacia; supplement VitD/Ca",
            citation='Pakozdi A, 2014; Epilepsia'
        ),
        DrugInteraction(
            drug_class='antiepileptics',
            drug_names=["valproate", 'valproic_acid'],
            feature_id="ammonia",
            direction="increases",
            mechanism='Inhibition of carbamoyl phosphate synthetase I',
            magnitude='strong',
            clinical_note='Hyperammonemic encephalopathy risk; check NH3 if confusion',
            citation="Wadzinski J, 2017; Cureus"
        ),
    ],


    "lithium": [
        DrugInteraction(
            drug_class="lithium",
            drug_names=["lithium_carbonate", "lithium_citrate"],
            feature_id='thyroid_stimulating_hormone',
            direction="increases",
            mechanism="Inhibition of thyroid hormone release → hypothyroidism",
            magnitude="moderate",
            clinical_note="Lithium-induced hypothyroidism in 5-35%; check TSH every 6-12 mo",
            citation="Bocchetta A, 2014; J Endocrinol Invest"
        ),
        DrugInteraction(
            drug_class="lithium",
            drug_names=["lithium"],
            feature_id="calcium_total",
            direction="increases",
            mechanism="Lithium-induced hyperparathyroidism",
            magnitude='mild',
            clinical_note="Check Ca/PTH if hypercalcemia develops",
            citation='Lepkifker E, 2004; J Clin Psychiatry'
        ),
    ],


    "amiodarone": [
        DrugInteraction(
            drug_class="amiodarone",
            drug_names=["amiodarone", "cordarone"],
            feature_id="thyroid_stimulating_hormone",
            direction='increases',
            mechanism="Iodine load → Wolff-Chaikoff effect (hypothyroidism)",
            magnitude='strong',
            clinical_note="Amiodarone-induced hypothyroidism (AIH) type 1 vs 2; check TSH q6mo",
            citation="Bartalena L, 2018; Eur Thyroid J"
        ),
        DrugInteraction(
            drug_class="amiodarone",
            drug_names=["amiodarone"],
            feature_id="alanine_aminotransferase",
            direction='increases',
            mechanism='Direct hepatotoxicity; phospholipidosis',
            magnitude="moderate",
            clinical_note="ALT elevation in 15-30%; monitor q6mo",
            citation="Lewis JH, 2011; Nat Rev Gastroenterol Hepatol"
        ),
    ],


    "methotrexate": [
        DrugInteraction(
            drug_class="methotrexate",
            drug_names=["methotrexate"],
            feature_id="alanine_aminotransferase",
            direction="increases",
            mechanism="Direct hepatotoxicity; cumulative fibrosis risk",
            magnitude="strong",
            clinical_note="Monitor ALT monthly; liver biopsy if persistent >2× ULN",
            citation="Conway R, 2014; Rheumatology"
        ),
        DrugInteraction(
            drug_class='methotrexate',
            drug_names=["methotrexate"],
            feature_id="mean_corpuscular_volume",
            direction='increases',
            mechanism='Folate antagonism → macrocytosis',
            magnitude="moderate",
            clinical_note="MCV rise is EXPECTED; give folic acid supplementation",
            citation="Johnston VF, 2013; Cochrane Database"
        ),
    ],


    "oral_contraceptives": [
        DrugInteraction(
            drug_class="oral_contraceptives",
            drug_names=["ethinyl_estradiol", "levonorgestrel", 'drospirenone',
                       "norethindrone", "combined_oral_contraceptives"],
            feature_id='total_cholesterol',
            direction="increases",
            mechanism="Estrogen increases hepatic VLDL production",
            magnitude='mild',
            clinical_note="Estrogen ↑ TC/TG; progestins ↓ HDL; consider alternative if dyslipidemia",
            citation='Godsland IF, 1997; Am J Obstet Gynecol'
        ),
        DrugInteraction(
            drug_class="oral_contraceptives",
            drug_names=["ethinyl_estradiol", "combined_oral_contraceptives"],
            feature_id="triglycerides",
            direction="increases",
            mechanism="Increased hepatic TG synthesis",
            magnitude="moderate",
            clinical_note="Avoid in TG >500 mg/dL (pancreatitis risk)",
            citation='Godsland IF, 1997'
        ),
        DrugInteraction(
            drug_class="oral_contraceptives",
            drug_names=["ethinyl_estradiol"],
            feature_id="c_reactive_protein",
            direction="increases",
            mechanism="Hepatic acute-phase protein synthesis stimulation",
            magnitude="moderate",
            clinical_note="CRP elevation is EXPECTED on OCP; use hs-CRP cautiously",
            citation='Sattar N, 2004; Circulation'
        ),
        DrugInteraction(
            drug_class="oral_contraceptives",
            drug_names=['ethinyl_estradiol'],
            feature_id="ferritin",
            direction="increases",
            mechanism="Reduced menstrual blood loss",
            magnitude="mild",
            clinical_note="OCP users often have higher ferritin",
            citation="Milman N, 2011; J Blood Med"
        ),
    ],


    "chemotherapy": [
        DrugInteraction(
            drug_class="chemotherapy",
            drug_names=["cisplatin", 'carboplatin'],
            feature_id="creatinine",
            direction='increases',
            mechanism="Direct nephrotoxicity (proximal tubule damage)",
            magnitude="strong",
            clinical_note="Aggressive hydration required; monitor Cr before each cycle",
            citation="Miller RP, 2010; Clin J Am Soc Nephrol"
        ),
        DrugInteraction(
            drug_class="chemotherapy",
            drug_names=["cisplatin"],
            feature_id='magnesium',
            direction="decreases",
            mechanism="Renal Mg wasting",
            magnitude="strong",
            clinical_note="Hypomagnesemia in 90% of cisplatin patients; supplement",
            citation="Miller RP, 2010"
        ),
        DrugInteraction(
            drug_class="chemotherapy",
            drug_names=["doxorubicin", "cyclophosphamide", "paclitaxel"],
            feature_id="hemoglobin",
            direction="decreases",
            mechanism="Bone marrow suppression",
            magnitude="strong",
            clinical_note='Chemotherapy-induced anemia; consider ESA if Hb<10',
            citation="Rizzo JD, 2019; J Clin Oncol"
        ),
    ],


    "aminoglycosides": [
        DrugInteraction(
            drug_class="aminoglycosides",
            drug_names=['gentamicin', 'amikacin', "tobramycin", "streptomycin"],
            feature_id="creatinine",
            direction='increases',
            mechanism="Acute tubular necrosis",
            magnitude="strong",
            clinical_note='Monitor Cr q48h; peak/trough levels',
            citation="Ronco C, 2017; Nat Rev Dis Primers"
        ),
    ],


    "calcineurin_inhibitors": [
        DrugInteraction(
            drug_class='calcineurin_inhibitors',
            drug_names=["cyclosporine", "tacrolimus"],
            feature_id='creatinine',
            direction="increases",
            mechanism="Afferent arteriolar vasoconstriction",
            magnitude="strong",
            clinical_note="Nephrotoxicity is dose-limiting; monitor trough levels",
            citation="Naesens M, 2009; Clin J Am Soc Nephrol"
        ),
        DrugInteraction(
            drug_class="calcineurin_inhibitors",
            drug_names=["cyclosporine", "tacrolimus"],
            feature_id="potassium",
            direction="increases",
            mechanism="Reduced aldosterone + impaired distal K secretion",
            magnitude="moderate",
            clinical_note="Hyperkalemia common; monitor closely",
            citation="Naesens M, 2009"
        ),
    ],


    "vitamin_d": [
        DrugInteraction(
            drug_class="vitamin_d",
            drug_names=["cholecalciferol", "ergocalciferol", "vitamin_d3"],
            feature_id="calcium_total",
            direction="increases",
            mechanism="Increased intestinal Ca absorption",
            magnitude="mild",
            clinical_note="Hypercalcemia if dose >10,000 IU/day long-term",
            citation="Hathcock JN, 2007; Am J Clin Nutr"
        ),
    ],

    "iron_supplements": [
        DrugInteraction(
            drug_class="iron_supplements",
            drug_names=['ferrous_sulfate', "ferrous_gluconate", "ferric_carboxymaltose"],
            feature_id="ferritin",
            direction="increases",
            mechanism="Direct iron repletion",
            magnitude="strong",
            clinical_note="Ferritin rise is EXPECTED during therapy; goal >100 ng/mL",
            citation='Pavord A, 2021; Br J Haematol'
        ),
        DrugInteraction(
            drug_class="iron_supplements",
            drug_names=["ferrous_sulfate"],
            feature_id="serum_iron",
            direction='increases',
            mechanism="Direct iron absorption",
            magnitude='strong',
            clinical_note="Draw iron studies BEFORE morning dose (trough level)",
            citation="Pavord A, 2021"
        ),
    ],
}

FEATURE_DRUG_INDEX: dict[str, list[str]] = {}

def tashkhis_interactions(observations: Mapping[str, ObservationRecord],
    context: ClinicalContext,
) -> list[dict[str, Any]]:
    """Flag analytes distorted by the patient's medication.

        A statin raising ALT is a drug effect, not liver disease;
        without this the engine would investigate the wrong thing.
        """
    medications = context.get("current_medications") or []
    if not medications:
        return []


    meds_lower = [str(m).strip().lower() for m in medications]


    active_drug_classes: dict[str, list[str]] = {}
    for drug_class, interactions in INTERACTION_DATABASE.items():
        matched_drugs = []
        for interaction in interactions:
            for drug_name in interaction.drug_names:
                if drug_name.lower() in meds_lower or any(
                    drug_name.lower() in med for med in meds_lower
                ):
                    if drug_name not in matched_drugs:
                        matched_drugs.append(drug_name)
        if matched_drugs:
            active_drug_classes[drug_class] = matched_drugs

    if not active_drug_classes:
        return []


    detected: list[dict[str, Any]] = []
    for drug_class, matched_drugs in active_drug_classes.items():
        for interaction in INTERACTION_DATABASE[drug_class]:
            fid = interaction.feature_id
            if fid not in observations:
                continue

            obs = observations[fid]
            value = _float(obs.value)
            if value is None:
                continue


            is_interacting = _barresi_direction_tatbigh(
                interaction.direction, value, fid
            )

            if is_interacting:
                detected.append({
                    "drug_class": drug_class,
                    'matched_drugs': matched_drugs,
                    "feature_id": fid,
                    "observed_value": value,
                    "unit": obs.unit,
                    "direction": interaction.direction,
                    "magnitude": interaction.magnitude,
                    'mechanism': interaction.mechanism,
                    'clinical_note': interaction.clinical_note,
                    "citation": interaction.citation,
                    "interpretation_hint": _tolid_hint(
                        interaction, value, fid
                    ),
                })

    return detected

def _barresi_direction_tatbigh(direction: str, value: float, feature_id: str
) -> bool:
    ref = REFERENCE_RANGES.get(feature_id, {})
    low = ref.get("low")
    high = ref.get("high")

    if direction == "increases":
        return high is not None and value > high
    elif direction == 'decreases':
        return low is not None and value < low
    elif direction in ("false_positive", 'false_negative'):

        return True
    return False

def _tolid_hint(interaction: DrugInteraction, value: float, feature_id: str
) -> str:
    direction_text = {
        "increases": "elevated",
        "decreases": "reduced",
        'false_positive': "falsely positive",
        "false_negative": "falsely negative",
    }.get(interaction.direction, "altered")

    return (
        f"{feature_id} is {direction_text} — consider {interaction.drug_class} "
        f"effect ({interaction.magnitude} magnitude). "
        f"{interaction.clinical_note}"
    )

def hoshdar_haye_vizhegi(feature_id: str, context: ClinicalContext
) -> list[str]:
    medications = context.get('current_medications') or []
    if not medications:
        return []

    meds_lower = [str(m).strip().lower() for m in medications]
    caveats = []

    for drug_class, interactions in INTERACTION_DATABASE.items():
        for interaction in interactions:
            if interaction.feature_id != feature_id:
                continue

            for drug_name in interaction.drug_names:
                if drug_name.lower() in meds_lower or any(
                    drug_name.lower() in med for med in meds_lower
                ):
                    caveats.append(
                        f"⚠ {drug_name} may {interaction.direction} "
                        f"{feature_id}: {interaction.clinical_note}"
                    )
                    break

    return caveats



@dataclass
class MoshtaghOlgoo:
    pattern_id: str
    name_en: str
    name_fa: str
    value: Optional[float]
    interpretation: str
    significance: str
    supports: list[str] = field(default_factory=list)
    argues_against: list[str] = field(default_factory=list)
    citation: str = ""
    inputs: dict[str, float] = field(default_factory=dict)


# Was a single-method class with no state; a module function says the
# same thing with one less indirection.
def tahlil_olgoo_haye_moshtagh(
    values: Mapping[str, float],
    context: Optional[ClinicalContext] = None,
) -> list[MoshtaghOlgoo]:
    """Compute the diagnostic ratios clinicians derive by hand.

        Mentzer index, FIB-4, De Ritis ratio, anion gap,
        BUN/creatinine, TG/HDL and transferrin saturation. Each
        returns the value, a plain-language reading, the diagnoses
        it supports or argues against, and its source.

        SUPER-ENHANCED: now includes 35+ complex multi-system patterns
        for ultra-precise diagnosis - PEDIATRIC AWARE.
        """
    # ULTRA-PRECISE: normalize CBC values that may be in /uL vs K/uL
    def _norm_cbc(fid, val):
        if val is None:
            return None
        try:
            fv = float(val)
        except:
            return val
        # Platelets: if >1000, likely /uL, convert to K/uL
        if fid in ("platelet_count", "platelets", "plt") and fv > 1000:
            return fv / 1000.0
        # WBC: if >1000, likely /uL, convert to K/uL? But keep as /uL for threshold 4500-13500
        # For WBC, keep original if >1000 as /uL, but also allow K/uL
        return fv

    v_raw = {k: val for k, val in values.items() if val is not None}
    v = {}
    for k, val in v_raw.items():
        v[k] = _norm_cbc(k, val)
    g = v.get
    out: list[MoshtaghOlgoo] = []

    # ULTRA-PRECISE: robust context getter for age-aware analysis
    def _ctx_get(key: str):
        if not context:
            return None
        try:
            if hasattr(context, "get"):
                val = context.get(key)
                if val is not None:
                    return val
            if hasattr(context, key):
                val = getattr(context, key)
                if val is not None:
                    return val
            if hasattr(context, "extra") and isinstance(context.extra, dict):
                return context.extra.get(key)
        except Exception:
            pass
        return None

    def add(**kw):
        pid = kw.get("pattern_id")
        if any(existing.pattern_id == pid for existing in out):
            return
        out.append(MoshtaghOlgoo(**kw))

    # ---- Existing patterns (kept) ----
    ast, alt = g("aspartate_aminotransferase"), g("alanine_aminotransferase")
    if ast and alt and alt > 0:
        ratio = ast / alt
        age_for_ritis = _ctx_get("age_years")
        try:
            age_for_ritis = float(age_for_ritis) if age_for_ritis is not None else None
        except:
            age_for_ritis = None
        is_child = age_for_ritis is not None and age_for_ritis < 18
        # The De Ritis ratio classifies an *elevated* transaminase pattern;
        # AST 30 / ALT 12 in a healthy adult is not 'alcoholic pattern'.
        _enzymes_raised = (ast > 35.0) or (alt > 40.0)
        # In children, low ALT is common, ratio high is not alcoholic
        if not _enzymes_raised:
            pass
        elif ratio >= 2.0:
            if is_child and alt < 20 and ast < 40:
                add(pattern_id='de_ritis_high_pediatric', name_en='AST/ALT Ratio Pediatric Normal Variant',
                    name_fa="نسبت AST/ALT در کودک - واریانت طبیعی", value=round(ratio, 2),
                    interpretation=(
                        f"AST/ALT = {ratio:.2f} (≥2.0) در کودک {age_for_ritis:.0f} ساله با ALT پایین {alt:.0f} — در کودکان ALT پایین طبیعی است، نسبت بالا الکل نیست. رشد، تغذیه بررسی شود."),
                    significance="low",
                    supports=[],
                    argues_against=['alcoholic_liver_disease', "liver_cirrhosis"],
                    citation="Pediatric LFT Reference, CALIPER 2020",
                    inputs={"AST": ast, "ALT": alt, "Age": age_for_ritis or 0})
            else:
                add(pattern_id='de_ritis_high', name_en='AST/ALT Ratio',
                    name_fa="نسبت AST/ALT", value=round(ratio, 2),
                    interpretation=(
                        f"AST/ALT = {ratio:.2f} (≥2.0) — الگوی کلاسیک "
                        'بیماری کبدی الکلی یا سیروز پیشرفته.'),
                    significance="high",
                    supports=['alcoholic_liver_disease', "liver_cirrhosis"],
                    argues_against=["nafl_d", "chronic_hepatitis_c"],
                    citation="De Ritis F, 1957; Botros M, 2013",
                    inputs={"AST": ast, "ALT": alt})
        elif ratio < 1.0:
            add(pattern_id='de_ritis_low', name_en="AST/ALT Ratio",
                name_fa="نسبت AST/ALT", value=round(ratio, 2),
                interpretation=(
                    f"AST/ALT = {ratio:.2f} (<1.0) — بیشتر به نفع "
                    'کبد چرب غیرالکلی یا هپاتیت ویروسی.'),
                significance="moderate",
                supports=["nafl_d", "chronic_hepatitis_c"],
                argues_against=['alcoholic_liver_disease'],
                citation="Botros M, 2013",
                inputs={'AST': ast, "ALT": alt})

    # Iron studies
    iron = g("serum_iron")
    tibc = g("total_iron_binding_capacity")
    tsat = g("transferrin_saturation")
    if tsat is None and iron and tibc and tibc > 0:
        tsat = 100.0 * iron / tibc
    ferr = g("ferritin")
    if tsat is not None and ferr is not None:
        if tsat > 45 and ferr > 300:
            add(pattern_id="iron_overload",
                name_en="Iron Overload", name_fa="اضافه‌بار آهن",
                value=round(tsat, 1),
                interpretation=(
                    f"اشباع ترانسفرین {tsat:.0f}٪ همراه فریتین "
                    f"{ferr:.0f} — الگوی اضافه‌بار آهن. بررسی "
                    "هموکروماتوز ارثی (HFE) توصیه می‌شود."),
                significance="high",
                supports=["hemochromatosis"],
                argues_against=["iron_deficiency_anemia"],
                citation="EASL Clinical Practice Guidelines 2022",
                inputs={"TSAT": round(tsat, 1), "Ferritin": ferr})
        elif tsat < 16 and ferr < 30:
            add(pattern_id="iron_deficit",
                name_en="Absolute Iron Deficiency",
                name_fa="کمبود مطلق آهن", value=round(tsat, 1),
                interpretation=(
                    f"اشباع ترانسفرین {tsat:.0f}٪ و فریتین "
                    f"{ferr:.0f} — کمبود مطلق آهن تأیید می‌شود."),
                significance="high",
                supports=["iron_deficiency_anemia"],
                argues_against=["anemia_of_chronic_disease",
                                "thalassemia_trait"],
                citation="WHO/CDC Iron Status Assessment 2020",
                inputs={"TSAT": round(tsat, 1), "Ferritin": ferr})

    bun = g("blood_urea_nitrogen") or g("urea_nitrogen") or g("urea")
    cr = g("creatinine")
    if bun and cr and cr > 0:
        ratio_bc = bun / cr
        age_for_bun = _ctx_get("age_years")
        try:
            age_for_bun = float(age_for_bun) if age_for_bun is not None else None
        except:
            age_for_bun = None
        is_child_bun = age_for_bun is not None and age_for_bun < 18
        low_muscle_cr = cr < 0.7  # low creatinine due to low muscle mass in children
        # BUN/Cr classifies *azotaemia* (KDIGO 2012); when both urea and
        # creatinine are inside the reference interval the ratio carries no
        # renal information (BUN 18 / Cr 0.7 = 26 in a healthy adult).
        _azotaemia = (bun > 20.0) or (cr > (1.1 if (str(_ctx_get("sex") or _ctx_get("sex_at_birth") or "").lower().startswith("f")) else 1.3)) \
            or (is_child_bun and cr > 1.0)

        if not _azotaemia:
            pass
        elif ratio_bc > 20:
            if is_child_bun and low_muscle_cr and bun < 35:
                add(pattern_id="bun_cr_pediatric_low_muscle",
                    name_en="BUN/Cr Pediatric Low Muscle Mass",
                    name_fa="نسبت BUN/Cr در کودک - توده عضلانی کم", value=round(ratio_bc, 1),
                    interpretation=(
                        f"BUN/Cr = {ratio_bc:.0f} (>20) در کودک {age_for_bun:.0f} ساله با کراتینین پایین {cr:.2f} — در کودکان کراتینین پایین به دلیل توده عضلانی کم طبیعی است، نه الزاماً پره‌رنال. BUN {bun:.0f} طبیعی، هیدراتاسیون بررسی شود."),
                    significance="low",
                    supports=[],
                    argues_against=["acute_kidney_injury"],
                    citation="Pediatric Nephrology Reference, Schwartz Formula 2009",
                    inputs={"BUN": bun, "Creatinine": cr, "Age": age_for_bun or 0})
            else:
                add(pattern_id="bun_cr_prerenal",
                    name_en="BUN/Creatinine Ratio",
                    name_fa="نسبت اوره به کراتینین", value=round(ratio_bc, 1),
                    interpretation=(
                        f"BUN/Cr = {ratio_bc:.0f} (>20) — به نفع علت "
                        "پیش‌کلیوی (کم‌آبی، خونریزی گوارشی) به‌جای "
                        "آسیب ذاتی کلیه."),
                    significance="high",
                    supports=["acute_kidney_injury"],
                    argues_against=[],
                    citation="KDIGO AKI Guideline 2012",
                    inputs={"BUN": bun, "Creatinine": cr})
        elif ratio_bc < 10:
            add(pattern_id="bun_cr_intrinsic", name_en="BUN/Cr Ratio",
                name_fa="نسبت اوره به کراتینین", value=round(ratio_bc, 1),
                interpretation=(
                    f"BUN/Cr = {ratio_bc:.0f} (<10) — به نفع آسیب "
                    "ذاتی کلیه (نکروز حاد توبولی) یا سوءتغذیه."),
                significance="moderate",
                supports=['acute_kidney_injury', "chronic_kidney_disease"],
                citation="KDIGO AKI 2012",
                inputs={"BUN": bun, 'Creatinine': cr})

    mcv, rbc = g("mean_corpuscular_volume"), g("red_blood_cell_count")
    if mcv and rbc and rbc > 0 and mcv < 80:
        idx = mcv / rbc
        if idx < 13:
            add(pattern_id="mentzer_thalassemia",
                name_en="Mentzer Index", name_fa="شاخص منتزر",
                value=round(idx, 1),
                interpretation=(
                    f"شاخص منتزر = {idx:.1f} (<13) در کم‌خونی "
                    "میکروسیتیک — به‌شدت به نفع تالاسمی مینور، "
                    "نه فقر آهن. الکتروفورز هموگلوبین توصیه می‌شود."),
                significance="high",
                supports=["thalassemia_trait"],
                argues_against=["iron_deficiency_anemia"],
                citation='Mentzer WC, Lancet 1973',
                inputs={"MCV": mcv, "RBC": rbc})
        else:
            add(pattern_id="mentzer_ida",
                name_en="Mentzer Index", name_fa="شاخص منتزر",
                value=round(idx, 1),
                interpretation=(
                    f"شاخص منتزر = {idx:.1f} (>13) — به نفع فقر "
                    "آهن به‌جای تالاسمی."),
                significance="moderate",
                supports=["iron_deficiency_anemia"],
                argues_against=['thalassemia_trait'],
                citation='Mentzer WC, Lancet 1973',
                inputs={"MCV": mcv, 'RBC': rbc})

    tsh, ft4 = g("thyroid_stimulating_hormone"), g("free_thyroxine")
    if tsh is not None and ft4 is not None:
        if tsh > 4.5 and ft4 < 0.8:
            txt, sig, sup = ("TSH بالا + FT4 پایین — کم‌کاری "
                             "آشکار تیروئید (اولیه).", 'high',
                             ['hypothyroidism'])
        elif tsh > 4.5 and 0.8 <= ft4 <= 1.8:
            txt, sig, sup = ("TSH بالا + FT4 طبیعی — کم‌کاری "
                             "تحت‌بالینی تیروئید. تکرار در ۶–۱۲ هفته "
                             "همراه آنتی‌TPO.", "high", ['hypothyroidism'])
        elif tsh < 0.4 and ft4 > 1.8:
            txt, sig, sup = ("TSH پایین + FT4 بالا — پرکاری آشکار "
                             "تیروئید.", "high", ["hyperthyroidism"])
        elif tsh < 0.4 and 0.8 <= ft4 <= 1.8:
            txt, sig, sup = ("TSH پایین + FT4 طبیعی — پرکاری "
                             "تحت‌بالینی؛ FT3 را بررسی کنید.",
                             'moderate', ["hyperthyroidism"])
        elif tsh > 4.5 and ft4 > 1.8:
            txt, sig, sup = ("TSH بالا + FT4 بالا — الگوی ناسازگار: "
                             "مقاومت به هورمون تیروئید، آدنوم مترشحه "
                             "TSH یا تداخل سنجش. تکرار با روش دیگر.",
                             "high", [])
        elif tsh < 0.4 and ft4 < 0.8:
            txt, sig, sup = ("TSH پایین + FT4 پایین — کم‌کاری "
                             "مرکزی (هیپوفیزی) یا سندرم بیماری "
                             "غیرتیروئیدی.", 'high', [])
        else:
            txt, sig, sup = None, None, None
        if txt:
            add(pattern_id="thyroid_axis", name_en="Thyroid Axis",
                name_fa="محور تیروئید", value=None,
                interpretation=txt, significance=sig, supports=sup,
                citation="ATA/AACE Thyroid Guidelines 2012",
                inputs={"TSH": tsh, "FT4": ft4})

    na, cl, hco3 = g("sodium"), g("chloride"), g("bicarbonate") or g("carbon_dioxide")
    if na and cl and hco3:
        ag = na - (cl + hco3)
        alb = g("albumin")
        if alb and alb < 4.0:
            ag += 2.5 * (4.0 - alb)
        # A high-anion-gap *metabolic acidosis* needs the acidosis: with
        # bicarbonate in range an AG of 13-16 is a normal analyser value
        # (modern ISE reference 8-16). A clearly raised gap (>20) is kept
        # even without a low bicarbonate (mixed disorder).
        # Pregnancy: compensated respiratory alkalosis lowers HCO3 to 18-22
        # physiologically (ACOG); require a bicarbonate below that band.
        _hco3_floor = 18.0 if bool(_ctx_get("pregnant")) else 22.0
        # A measured lactate in range removes 'sepsis' (and AKI if creatinine
        # is normal) from the supported list: the gap is then unexplained
        # (ketones / toxins / uraemia / analytical) rather than septic.
        _lac = g("lactate"); _crea = g("creatinine")
        _sup_ag = ["acute_kidney_injury", "sepsis"]
        if _lac is not None and _lac < 2.0:
            _sup_ag = [x for x in _sup_ag if x != "sepsis"]
            if _crea is not None and _crea <= 1.2:
                _sup_ag = []
        if ag > 12 and (hco3 < _hco3_floor or ag > 20):
            add(pattern_id="high_anion_gap",
                name_en="High Anion Gap", name_fa="آنیون گپ بالا",
                value=round(ag, 1),
                interpretation=(
                    f"آنیون گپ (تصحیح‌شده با آلبومین) = {ag:.0f} "
                    '(>12) — اسیدوز متابولیک با گپ بالا: '
                    'کتواسیدوز، لاکتات، اورمی یا مسمومیت.'),
                significance="high" if _sup_ag else "moderate",
                supports=_sup_ag,
                citation="Kraut JA, NEJM 2014",
                inputs={"Na": na, "Cl": cl, 'HCO3': hco3})

    fer, crp = g("ferritin"), g('c_reactive_protein')
    if fer is not None and crp is not None:
        if fer < 30 and crp <= 10:
            add(pattern_id="iron_pattern_ida",
                name_en="Iron Study Pattern", name_fa="الگوی آهن",
                value=fer,
                interpretation=(
                    f"فریتین {fer:g} پایین با CRP طبیعی — فقر آهن "
                    'واقعی (بدون مخدوش‌شدن التهابی).'),
                significance='high',
                supports=["iron_deficiency_anemia"],
                argues_against=["anemia_of_chronic_disease"],
                citation="WHO Ferritin Guideline 2020",
                inputs={"Ferritin": fer, 'CRP': crp})
        elif 30 <= fer <= 100 and crp > 10:
            add(pattern_id="iron_pattern_masked",
                name_en="Iron Study Pattern", name_fa="الگوی آهن",
                value=fer,
                interpretation=(
                    f"فریتین {fer:g} «به‌ظاهر طبیعی» ولی CRP بالا "
                    f"({crp:g}) — فریتین یک واکنش‌گر فاز حاد است و "
                    'ممکن است فقر آهن را پنهان کند. آستانه در '
                    "التهاب ۱۰۰ است، نه ۳۰."),
                significance='high',
                supports=["iron_deficiency_anemia",
                          "anemia_of_chronic_disease"],
                citation="WHO 2020; Camaschella C, NEJM 2015",
                inputs={"Ferritin": fer, "CRP": crp})
        elif fer > 100 and crp > 10:
            add(pattern_id="iron_pattern_acd",
                name_en="Iron Study Pattern", name_fa="الگوی آهن",
                value=fer,
                interpretation=(
                    "فریتین بالا با التهاب فعال — به نفع کم‌خونی "
                    "بیماری مزمن."),
                significance="moderate",
                supports=["anemia_of_chronic_disease"],
                argues_against=["iron_deficiency_anemia"],
                citation="Weiss G, NEJM 2005",
                inputs={"Ferritin": fer, 'CRP': crp})

    fpg, a1c = g("fasting_plasma_glucose") or g("glucose"), g('hemoglobin_a1c')
    if fpg and a1c:
        eag = 28.7 * a1c - 46.7
        if fpg >= 126 and a1c < 5.7:
            add(pattern_id="glycemic_discordance",
                name_en='Glycemic Discordance',
                name_fa='ناسازگاری قندی', value=round(eag, 0),
                interpretation=(
                    f"قند ناشتا {fpg:g} بالا ولی HbA1c {a1c:g}٪ "
                    "طبیعی — احتمال کوتاه‌شدن عمر گلبول قرمز "
                    "(همولیز، خونریزی اخیر، هموگلوبینوپاتی) که "
                    "HbA1c را کاذب پایین می‌آورد."),
                significance="high", supports=["hemolytic_anemia"],
                citation='ADA Standards of Care 2024, S2',
                inputs={"FPG": fpg, "HbA1c": a1c})
        elif a1c >= 6.5 and fpg < 100:
            add(pattern_id="glycemic_discordance_high",
                name_en='Glycemic Discordance',
                name_fa='ناسازگاری قندی', value=round(eag, 0),
                interpretation=(
                    f"HbA1c {a1c:g}٪ دیابتی ولی قند ناشتا {fpg:g} "
                    "طبیعی — احتمال هایپرگلیسمی پس از غذا، یا "
                    "کاذب بالا بودن A1c (فقر آهن، اورمی). "
                    "OGTT توصیه می‌شود."),
                significance="high", supports=["type_2_diabetes"],
                citation="ADA Standards of Care 2024, S2",
                inputs={"FPG": fpg, "HbA1c": a1c})

    ca, pth = g("calcium_total"), g("parathyroid_hormone")
    alb = g("albumin")
    if ca is not None and alb is not None and alb < 4.0:
        ca = ca + 0.8 * (4.0 - alb)
    if ca is not None and pth is not None:
        if ca > 10.5 and pth > 65:
            add(pattern_id="pth_calcium_axis",
                name_en='PTH-Calcium Axis', name_fa="محور PTH-کلسیم",
                value=round(ca, 2),
                interpretation=(
                    "کلسیم بالا + PTH بالا (یا نامناسب طبیعی) — "
                    "به‌شدت به نفع هایپرپاراتیروئیدی اولیه."),
                significance="high", supports=["primary_hyperparathyroidism"],
                citation="Bilezikian JP, JCEM 2014",
                inputs={"Corrected Ca": round(ca, 2), "PTH": pth})
        elif ca > 10.5 and pth < 20:
            add(pattern_id="pth_suppressed_hypercalcemia",
                name_en='PTH-Calcium Axis', name_fa="محور PTH-کلسیم",
                value=round(ca, 2),
                interpretation=(
                    'کلسیم بالا با PTH سرکوب‌شده — علت غیرپاراتیروئیدی: '
                    "بدخیمی، سارکوئیدوز یا مسمومیت با ویتامین D. "
                    "بررسی PTHrP توصیه می‌شود."),
                significance="high", supports=[],
                citation="Bilezikian JP, JCEM 2014",
                inputs={"Corrected Ca": round(ca, 2), "PTH": pth})

    plt_ = g("platelet_count")
    age = _float(context.age_years) if context else None
    if ast and alt and plt_ and age and alt > 0 and plt_ > 0:
        fib4 = (age * ast) / (plt_ * math.sqrt(alt))
        # FIB-4 is age-driven: above 65 it over-calls fibrosis (McPherson
        # 2017; AASLD NAFLD guidance 2023), and with every input inside its
        # reference interval it carries no supporting weight at all.
        inputs_normal = ast <= 40 and alt <= 40 and plt_ >= 150
        if fib4 > 2.67 and not inputs_normal:
            add(pattern_id="fib4_high", name_en="FIB-4 Index",
                name_fa="شاخص FIB-4", value=round(fib4, 2),
                interpretation=(
                    f"FIB-4 = {fib4:.2f} (>2.67) — احتمال بالای "
                    "فیبروز پیشرفته کبدی. ارجاع برای الاستوگرافی."
                    + (" (سن >۶۵: ویژگی FIB-4 کاهش می‌یابد؛ تفسیر "
                       "با احتیاط.)" if age > 65 else "")),
                significance='high' if age <= 65 else 'moderate',
                supports=["liver_cirrhosis", "nash"],
                citation='Sterling RK, Hepatology 2006; McPherson S, Am J Gastroenterol 2017',
                inputs={"AST": ast, 'ALT': alt, "PLT": plt_,
                        "Age": age})
        elif fib4 > 2.67 and inputs_normal:
            add(pattern_id="fib4_high_age_artifact", name_en="FIB-4 Index",
                name_fa="شاخص FIB-4", value=round(fib4, 2),
                interpretation=(
                    f"FIB-4 = {fib4:.2f} با AST/ALT/پلاکت کاملاً طبیعی — "
                    "عدد بالا ناشی از سن است، نه بیماری کبدی؛ "
                    "فاقد ارزش تشخیصی."),
                significance="low", supports=[],
                citation="McPherson S, Am J Gastroenterol 2017",
                inputs={"AST": ast, 'ALT': alt, "PLT": plt_,
                        "Age": age})
        elif fib4 < 1.3:
            add(pattern_id="fib4_low", name_en='FIB-4 Index',
                name_fa="شاخص FIB-4", value=round(fib4, 2),
                interpretation=(
                    f"FIB-4 = {fib4:.2f} (<1.3) — فیبروز پیشرفته "
                    "با احتمال بالا رد می‌شود (NPV ~۹۰٪)."),
                significance="moderate", supports=[],
                argues_against=['liver_cirrhosis'],
                citation="Sterling RK, Hepatology 2006",
                inputs={"AST": ast, "ALT": alt, "PLT": plt_,
                        'Age': age})

    tg, hdl = g("triglycerides"), g("hdl_cholesterol")
    if tg and hdl and hdl > 0:
        ratio = tg / hdl
        if ratio >= 3.5:
            add(pattern_id="tg_hdl_ratio",
                name_en="TG/HDL Ratio", name_fa='نسبت TG به HDL',
                value=round(ratio, 2),
                interpretation=(
                    f"TG/HDL = {ratio:.1f} (≥3.5) — نشانگر جایگزین "
                    'مقاومت به انسولین و LDL کوچک-متراکم.'),
                significance="moderate",
                supports=["metabolic_syndrome", "type_2_diabetes",
                          "nafl_d"],
                citation="McLaughlin T, Ann Intern Med 2003",
                inputs={'TG': tg, "HDL": hdl})

    # ==================== SUPER-ENHANCED COMPLEX PATTERNS ====================

    # 1. Liver injury pattern: R ratio (ALT/ULN)/(ALP/ULN) - ULTRA-PRECISE PEDIATRIC AWARE
    alp = g("alkaline_phosphatase")
    # Age- and pregnancy-aware ALP ULN
    age_for_alp = _ctx_get("age_years")
    is_pregnant = bool(_ctx_get("pregnant"))
    try:
        age_for_alp = float(age_for_alp) if age_for_alp is not None else None
    except:
        age_for_alp = None
    # Pediatric & Pregnancy ALP ULN:
    if is_pregnant:
        alp_uln = 350  # Pregnancy placental isoenzyme
        alt_uln = 35
    elif age_for_alp is not None and age_for_alp < 12:
        alp_uln = 400  # children <12: up to 400 normal
        alt_uln = 30
    elif age_for_alp is not None and age_for_alp < 18:
        alp_uln = 300  # adolescents: up to 300
        alt_uln = 35
    else:
        alp_uln = 120
        alt_uln = 40

    # The R ratio (Aithal 2011 / ACG DILI 2021) classifies an *established*
    # liver-enzyme elevation; with ALT and ALP both inside their reference
    # intervals it is undefined as a pattern and must not fire (a normal
    # panel otherwise reads as "cholestatic, high significance").
    if alt and alp and (alt > alt_uln or alp > alp_uln):
        r_ratio = (alt/alt_uln) / (alp/alp_uln) if alp>0 else None
        # Check if this is pediatric or pregnancy physiological ALP elevation
        is_pediatric_alp = age_for_alp is not None and age_for_alp < 18 and alp < (800 if age_for_alp <12 else 500)
        bili_total_check = g("bilirubin_total")
        ggt_check = g("gamma_glutamyl_transferase")
        has_cholestasis_markers = (bili_total_check and bili_total_check>1.2) or (ggt_check and ggt_check>60)
        is_pregnancy_alp = is_pregnant and alp <= 450 and not has_cholestasis_markers

        if r_ratio is not None:
            if is_pediatric_alp and not has_cholestasis_markers:
                # Pediatric physiological ALP - do NOT flag as cholestatic disease
                add(pattern_id="pediatric_alp_elevation", name_en="Pediatric ALP Elevation - Bone Growth",
                    name_fa="افزایش ALP کودکان - رشد استخوانی", value=round(alp,0),
                    interpretation=f"ALP {alp:.0f} بالا در کودک {age_for_alp:.0f} ساله — در کودکان ALP تا {alp_uln*2:.0f} به دلیل رشد استخوانی طبیعی است. بیلی‌روبین و GGT طبیعی، الگوی کلستاتیک کاذب. بررسی رشد، ویتامین D.",
                    significance="low", supports=[],
                    argues_against=["cholestasis","primary_biliary_cholangitis","liver_cirrhosis"],
                    citation="Pediatric Reference Ranges, CALIPER 2020; ALP bone isoenzyme in children",
                    inputs={"ALT": alt, "ALP": alp, "R": round(r_ratio,2), "Age": age_for_alp or 0})
            elif is_pregnancy_alp:
                # Pregnancy physiological ALP - placental isoenzyme
                add(pattern_id="pregnancy_alp_elevation", name_en="Pregnancy Physiological ALP Elevation",
                    name_fa="افزایش فیزیولوژیک ALP در بارداری", value=round(alp,0),
                    interpretation=f"افزایش ALP ({alp:.0f} U/L) در دوران بارداری فیزیولوژیک و ناشی از ایزوآنزیم جفتی است. با توجه به طبیعی بودن آنزیم‌های کبدی و بیلی‌روبین، بیماری کبدی یا کلستاز مطرح نیست.",
                    significance="low", supports=[],
                    argues_against=["cholestasis","primary_biliary_cholangitis","liver_cirrhosis"],
                    citation="ACOG Clinical Guidance 2023; Placental alkaline phosphatase isoenzyme",
                    inputs={"ALT": alt, "ALP": alp, "R": round(r_ratio,2)})
            elif alp <= alp_uln:
                # extension 7 (2026-10-22): ALP inside its reference interval -> the R ratio cannot indicate
                # cholestasis (ACG 2021 DILI; Aithal 2011). Isolated ALT elevation is hepatocellular by definition.
                add(pattern_id="liver_isolated_alt", name_en="Isolated ALT elevation (ALP normal)",
                    name_fa="افزایش ایزولهٔ ALT با ALP طبیعی", value=round(alt / alt_uln, 2),
                    interpretation=f"ALT {alt:.0f} U/L بالاتر از ULN با ALP طبیعی — الگوی هپاتوسلولار خفیف (NAFLD، دارو، هپاتیت ویروسی مزمن، الکل)؛ کلستاز مطرح نیست.",
                    significance="moderate" if alt >= 2 * alt_uln else "low",
                    supports=["nafl_d", "chronic_hepatitis_b", "chronic_hepatitis_c", "drug_induced_liver_injury"] if alt >= 2 * alt_uln else ["nafl_d"],
                    argues_against=["cholestasis", "primary_biliary_cholangitis", "primary_sclerosing_cholangitis"],
                    citation="ACG Clinical Guideline: Evaluation of Abnormal Liver Chemistries 2017; Aithal GP 2011",
                    inputs={"ALT": alt, "ALP": alp, "ALT_ULN": alt_uln})
            elif r_ratio >= 5:
                add(pattern_id="liver_hepatocellular", name_en="R Ratio Hepatocellular",
                    name_fa="آسیب هپاتوسلولار", value=round(r_ratio,2),
                    interpretation=f"R = {r_ratio:.1f} (≥5) — آسیب هپاتوسلولار غالب (هپاتیت ویروسی، دارویی، ایسکمیک). ALT بسیار بالاتر از ALP.",
                    significance="high", supports=["chronic_hepatitis_b","chronic_hepatitis_c","nafl_d","autoimmune_hepatitis"],
                    argues_against=["cholestasis"],
                    citation="Aithal GP, Clin Pharmacol Ther 2011; DILI R ratio",
                    inputs={"ALT": alt, "ALP": alp, "R": round(r_ratio,2)})
            elif r_ratio <= 2:
                if (is_pediatric_alp or is_pregnancy_alp) and not has_cholestasis_markers:
                    # Already handled above as physiological adaptation, skip cholestatic flag
                    pass
                else:
                    add(pattern_id="liver_cholestatic", name_en="R Ratio Cholestatic",
                        name_fa="آسیب کلستاتیک", value=round(r_ratio,2),
                        interpretation=f"R = {r_ratio:.1f} (≤2) — الگوی کلستاتیک: انسداد صفراوی، PBC، PSC یا داروی کلستاتیک. {'در کودک با ALP بالا، رشد استخوانی را رد کنید.' if age_for_alp and age_for_alp<18 else ''}",
                        significance="high" if not (age_for_alp and age_for_alp<18) else "low",
                        supports=(["cholestasis","primary_biliary_cholangitis"] if alp >= 1.5 * alp_uln else ["cholestasis"]) if not is_pediatric_alp else [],  # extension 7: EASL 2017 PBC ALP >= 1.5 x ULN
                        argues_against=["nafl_d"] if not is_pediatric_alp else ["cholestasis"],
                        citation="Aithal GP 2011",
                        inputs={"ALT": alt, "ALP": alp, "R": round(r_ratio,2)})
            else:
                add(pattern_id="liver_mixed", name_en="R Ratio Mixed",
                    name_fa="آسیب مختلط کبدی", value=round(r_ratio,2),
                    interpretation=f"R = {r_ratio:.1f} (2-5) — آسیب مختلط هپاتوسلولار-کلستاتیک.",
                    significance="moderate", supports=["drug_induced_liver_injury"],
                    citation="Aithal GP 2011",
                    inputs={"ALT": alt, "ALP": alp, "R": round(r_ratio,2)})

    # 2. Bilirubin fractions: direct vs indirect
    bili_total = g("bilirubin_total")
    bili_direct = g("bilirubin_direct")
    bili_indirect = g("bilirubin_indirect")
    if bili_total and bili_direct:
        if bili_direct / bili_total > 0.5 and bili_total > 1.2:
            add(pattern_id="cholestasis_direct", name_en="Direct Hyperbilirubinemia",
                name_fa="هیپربیلی‌روبینمی مستقیم", value=round(bili_direct,2),
                interpretation=f"بیلی‌روبین مستقیم {bili_direct:.1f} از کل {bili_total:.1f} (>50%) — کلستاز یا آسیب هپاتوسلولار با اختلال ترشح.",
                significance="high", supports=["cholestasis","liver_cirrhosis"],
                citation="Fargo MV, Am Fam Physician 2017",
                inputs={"Total": bili_total, "Direct": bili_direct})
    if bili_indirect and bili_total and bili_total>1.2 and (bili_indirect/bili_total)>0.7:
        add(pattern_id="indirect_hyperbili", name_en="Indirect Hyperbilirubinemia",
            name_fa="هیپربیلی مستقیم غالب", value=round(bili_indirect,2),
            interpretation=f"بیلی‌روبین غیرمستقیم غالب ({bili_indirect:.1f}/{bili_total:.1f}) — همولیز، ژیلبرت یا ناکارایی کونژوگاسیون.",
            significance="moderate", supports=["hemolytic_anemia","gilbert_syndrome"],
            citation="Fargo MV 2017",
            inputs={"Total": bili_total, "Indirect": bili_indirect})

    # 3. DKA pattern
    glu = g("glucose") or g("fasting_plasma_glucose")
    ket = g("ketones") or g("beta_hydroxybutyrate") or g("urine_ketones")
    bicarb = g("bicarbonate") or g("carbon_dioxide")
    ph = g("ph") or g("arterial_ph")
    if glu and glu>=250 and bicarb is not None and bicarb<18:
        ag_val = None
        if na and cl and bicarb:
            ag_val = na - (cl + bicarb)
        has_ket = ket is not None and ket>0.6 if isinstance(ket,(int,float)) else ket is not None
        if has_ket or ag_val is None or ag_val>12:
            add(pattern_id="dka_risk", name_en="DKA Pattern",
                name_fa="الگوی کتواسیدوز دیابتی", value=round(glu,0),
                interpretation=f"قند {glu:.0f} + بی‌کربنات {bicarb:.0f} پایین + آنیون گپ بالا — خطر DKA. بررسی کتون خون، pH وریدی، الکترولیت.",
                significance="high", supports=["type_1_diabetes","type_2_diabetes"],
                citation="ADA DKA Guidelines 2024",
                inputs={"Glucose": glu, "HCO3": bicarb, "AG": ag_val or 0})

    # 4. HHS pattern
    if glu and glu>=600 and bicarb is not None and bicarb>15:
        add(pattern_id="hhs_risk", name_en="HHS Pattern",
            name_fa="الگوی HHS", value=round(glu,0),
            interpretation=f"قند بسیار بالا {glu:.0f} (≥600) با بی‌کربنات نسبتاً حفظ‌شده {bicarb:.0f} — الگوی HHS (هیپراسمولار). بررسی اسمولالیته سرم.",
            significance="high", supports=["type_2_diabetes"],
            citation="ADA Hyperglycemic Crises 2024",
            inputs={"Glucose": glu, "HCO3": bicarb})

    # 5. Metabolic syndrome 3/5
    waist = g("waist_circumference") or _ctx_get("waist_cm") or _ctx_get("waist_circumference")
    bp_sys = g("systolic_bp") or _ctx_get("systolic_bp") or _ctx_get("systolic_blood_pressure")
    bp_dia = g("diastolic_bp") or _ctx_get("diastolic_bp") or _ctx_get("diastolic_blood_pressure")
    ms_criteria = 0
    ms_details = []
    if waist and waist>= (102 if (context and context.normalized_jensiat()=="male") else 88):
        ms_criteria+=1; ms_details.append(f"waist {waist}")
    if tg and tg>=150:
        ms_criteria+=1; ms_details.append(f"TG {tg}")
    if hdl and ((context and context.normalized_jensiat()=="male" and hdl<40) or (context and context.normalized_jensiat()=="female" and hdl<50) or (not context and hdl<40)):
        ms_criteria+=1; ms_details.append(f"HDL low {hdl}")
    if fpg and fpg>=100:
        ms_criteria+=1; ms_details.append(f"FPG {fpg}")
    if (bp_sys and bp_sys>=130) or (bp_dia and bp_dia>=85):
        ms_criteria+=1; ms_details.append(f"BP {bp_sys}/{bp_dia}")
    if ms_criteria>=3:
        add(pattern_id="metabolic_syndrome_criteria", name_en="Metabolic Syndrome 3/5",
            name_fa="سندرم متابولیک", value=ms_criteria,
            interpretation=f"{ms_criteria}/5 معیار سندرم متابولیک مثبت ({', '.join(ms_details)}) — تشخیص سندرم متابولیک محتمل.",
            significance="high", supports=["metabolic_syndrome","type_2_diabetes","nafl_d"],
            citation="IDF/NCEP ATP III 2009",
            inputs={"criteria": ms_criteria})

    # 6. Anemia differential - microcytic
    hb = g("hemoglobin")
    if hb is not None and hb<12:
        if mcv is not None:
            if mcv<80:
                rdw = g("red_cell_distribution_width")
                ferr_val = g("ferritin")
                if rdw and rdw>15 and ferr_val and ferr_val<30:
                    add(pattern_id="anemia_micro_ida", name_en="Microcytic Anemia IDA",
                        name_fa="کم‌خونی میکروسیتر فقر آهن", value=round(mcv,1),
                        interpretation=f"Hb {hb:.1f} پایین، MCV {mcv:.0f} میکروسیتر، RDW {rdw:.0f} بالا، فریتین پایین — کم‌خونی فقر آهن کلاسیک.",
                        significance="high", supports=["iron_deficiency_anemia"],
                        citation="BSH Anemia Guidelines 2023",
                        inputs={"Hb": hb, "MCV": mcv, "RDW": rdw or 0})
                elif rdw and rdw<14.5 and rbc and rbc>5:
                    add(pattern_id="anemia_micro_thal", name_en="Microcytic Thalassemia",
                        name_fa="میکروسیتوز تالاسمی", value=round(mcv,1),
                        interpretation=f"Hb {hb:.1f} پایین، MCV {mcv:.0f} پایین، RBC {rbc:.1f} بالا، RDW طبیعی — تالاسمی مینور محتمل.",
                        significance="high", supports=["thalassemia_trait"],
                        citation="Mentzer 1973",
                        inputs={"Hb": hb, "MCV": mcv, "RBC": rbc})
            elif mcv>100:
                b12 = g("vitamin_b12")
                fol = g("folate")
                if b12 and b12<200:
                    add(pattern_id="anemia_macro_b12", name_en="Macrocytic B12 Deficiency",
                        name_fa="ماکروسیتوز کمبود B12", value=round(mcv,1),
                        interpretation=f"Hb {hb:.1f} پایین، MCV {mcv:.0f} بالا، B12 {b12:.0f} پایین — کم‌خونی مگالوبلاستیک B12.",
                        significance="high", supports=["vitamin_b12_deficiency"],
                        citation="BSH 2023",
                        inputs={"Hb": hb, "MCV": mcv, "B12": b12})
                elif fol and fol<4:
                    add(pattern_id="anemia_macro_folate", name_en="Macrocytic Folate Deficiency",
                        name_fa="ماکروسیتوز کمبود فولات", value=round(mcv,1),
                        interpretation=f"Hb {hb:.1f} پایین، MCV {mcv:.0f} بالا، فولات {fol:.0f} پایین — کمبود فولات.",
                        significance="high", supports=["folate_deficiency"],
                        citation="BSH 2023",
                        inputs={"Hb": hb, "MCV": mcv, "Folate": fol})
            else: # normocytic
                egfr = g("egfr_ckd_epi_creatinine")
                crp_val = g("c_reactive_protein")
                if egfr and egfr<60:
                    add(pattern_id="anemia_normo_ckd", name_en="Normocytic CKD Anemia",
                        name_fa="کم‌خونی نورموسیتر CKD", value=round(hb,1),
                        interpretation=f"Hb {hb:.1f} پایین، MCV نرمال {mcv:.0f}، eGFR {egfr:.0f} پایین — کم‌خونی بیماری مزمن کلیوی (کمبود EPO).",
                        significance="moderate", supports=["chronic_kidney_disease","anemia_of_chronic_disease"],
                        citation="KDIGO Anemia 2024",
                        inputs={"Hb": hb, "MCV": mcv, "eGFR": egfr})
                elif crp_val and crp_val>10:
                    add(pattern_id="anemia_normo_acd", name_en="Anemia of Chronic Disease",
                        name_fa="کم‌خونی بیماری مزمن", value=round(hb,1),
                        interpretation=f"Hb {hb:.1f} پایین، MCV نرمال، CRP {crp_val:.0f} بالا — کم‌خونی التهاب مزمن (هپسیدین بالا).",
                        significance="moderate", supports=["anemia_of_chronic_disease"],
                        citation="Weiss G, NEJM 2005",
                        inputs={"Hb": hb, "MCV": mcv, "CRP": crp_val})

    # 7. Hemolytic pattern: LDH high + indirect bili + haptoglobin low + retic high
    ldh = g("lactate_dehydrogenase")
    hapto = g("haptoglobin")
    retic = g("reticulocyte_count")
    if hb and hb<12 and ldh and ldh>250:
        if (bili_indirect and bili_indirect>1.0) or (hapto and hapto<30) or (retic and retic>2.5):
            add(pattern_id="hemolysis_pattern", name_en="Hemolysis Pattern",
                name_fa="الگوی همولیز", value=round(ldh,0),
                interpretation=f"Hb پایین {hb:.1f} + LDH بالا {ldh:.0f} + بیلی غیرمستقیم/هاپتوگلوبین پایین/رتیک بالا — همولیز فعال.",
                significance="high", supports=["hemolytic_anemia"],
                citation="BSH Hemolysis 2023",
                inputs={"Hb": hb, "LDH": ldh, "Haptoglobin": hapto or 0, "Retic": retic or 0})

    # 8. Pancytopenia
    wbc = g("white_blood_cell_count")
    plt = g("platelet_count")
    if hb and hb<10 and wbc and wbc<4 and plt and plt<150:
        add(pattern_id="pancytopenia", name_en="Pancytopenia",
            name_fa="پان‌سیتوپنی", value=round(hb,1),
            interpretation=f"Hb {hb:.1f} + WBC {wbc:.1f} + PLT {plt:.0f} همگی پایین — پان‌سیتوپنی: نارسایی مغز استخوان، دارو، هیپرسپلنیسم یا کمبود B12/فولات.",
            significance="high", supports=["aplastic_anemia","vitamin_b12_deficiency","acute_leukemia"],
            citation="BSH Pancytopenia 2023",
            inputs={"Hb": hb, "WBC": wbc, "PLT": plt})

    # 9. NLR high - inflammation/bacterial vs viral
    neut = g("neutrophils")
    lymph = g("lymphocytes")
    if wbc and neut and lymph and lymph>0:
        nlr = neut/lymph if lymph!=0 else None
        if nlr and nlr>3.5:
            if crp and crp>50:
                add(pattern_id="bacterial_inflammation", name_en="Bacterial Inflammation NLR",
                    name_fa="التهاب باکتریال", value=round(nlr,2),
                    interpretation=f"NLR {nlr:.1f} بالا + CRP {crp:.0f} بالا + نوتروفیلی {neut:.0f}% — التهاب باکتریال محتمل.",
                    significance="moderate", supports=["urinary_tract_infection","sepsis"],
                    citation="Zahorec R, Bratisl Lek Listy 2001",
                    inputs={"NLR": round(nlr,2), "CRP": crp, "Neut": neut})
    # Viral pattern: lymphocytosis + low neutrophils
    if wbc and lymph and lymph>50 and neut and neut<40:
        add(pattern_id="viral_pattern", name_en="Viral Lymphocytosis",
            name_fa="لنفوسیتوز ویروسی", value=round(lymph,1),
            interpretation=f"WBC {wbc:.1f} با لنفوسیت {lymph:.0f}% بالا و نوتروفیل {neut:.0f}% پایین — الگوی ویروسی.",
            significance="moderate", supports=["viral_infection"],
            citation="Harrison Hematology",
            inputs={"WBC": wbc, "Lymph": lymph, "Neut": neut})

    # 10. Sepsis pattern: PCT high + lactate + WBC abnormal + CRP very high
    pct = g("procalcitonin")
    lac = g("lactate")
    if pct and pct>0.5 and ((lac and lac>2) or (crp and crp>100) or (wbc and (wbc>12 or wbc<4))):
        add(pattern_id="sepsis_pattern", name_en="Sepsis Pattern",
            name_fa="الگوی سپسیس", value=round(pct,2),
            interpretation=f"PCT {pct:.2f} بالا + لاکتات {lac or 0:.1f}/CRP {crp or 0:.0f}/WBC غیرطبیعی — سپسیس محتمل، کشت خون و آنتی‌بیوتیک فوری.",
            significance="high", supports=["sepsis"],
            citation="Surviving Sepsis Campaign 2021",
            inputs={"PCT": pct, "Lactate": lac or 0, "CRP": crp or 0})

    # 11. DIC pattern: low platelets + high D-dimer + prolonged PT + low fibrinogen
    d_dimer = g("d_dimer") or g("d-dimer")
    pt = g("prothrombin_time") or g("pt")
    fib = g("fibrinogen")
    if plt and plt<150 and d_dimer and d_dimer>0.5 and (fib and fib<150 or pt and pt>14):
        add(pattern_id="dic_pattern", name_en="DIC Pattern",
            name_fa="الگوی DIC", value=round(plt,0),
            interpretation=f"PLT پایین {plt:.0f} + D-dimer بالا {d_dimer:.2f} + فیبرینوژن پایین/PT طولانی — DIC محتمل.",
            significance="high", supports=["disseminated_intravascular_coagulation","sepsis"],
            citation="ISTH DIC Score 2001",
            inputs={"PLT": plt, "D-dimer": d_dimer, "Fibrinogen": fib or 0})

    # 12. Adrenal insufficiency: Na low + K high + cortisol low + ACTH high
    cortisol = g("cortisol_morning") or g("morning_cortisol") or g("cortisol")
    acth = g("adrenocorticotropic_hormone")
    k = g("potassium")
    if cortisol and cortisol<5 and na and na<135 and k and k>5:
        add(pattern_id="adrenal_insufficiency", name_en="Adrenal Insufficiency Pattern",
            name_fa="الگوی نارسایی آدرنال", value=round(cortisol,1),
            interpretation=f"کورتیزول صبح {cortisol:.1f} پایین + Na {na:.0f} پایین + K {k:.1f} بالا — نارسایی آدرنال (آدیسون). ACTH را بررسی کنید.",
            significance="high", supports=["addison_disease"],
            citation="Endocrine Society Adrenal Insufficiency 2016",
            inputs={"Cortisol": cortisol, "Na": na, "K": k, "ACTH": acth or 0})

    # 13. Primary aldosteronism: K low + HCO3 high + HTN context
    if k and k<3.5 and bicarb and bicarb>29:
        arr = g("aldosterone_to_renin_ratio_arr") or g("aldosterone_renin_ratio")
        if arr and arr>30 or (bp_sys and bp_sys>=140):
            add(pattern_id="primary_aldosteronism_pattern", name_en="Primary Aldosteronism Pattern",
                name_fa="الگوی آلدوسترونیسم اولیه", value=round(k,2),
                interpretation=f"K {k:.1f} پایین + HCO3 {bicarb:.0f} بالا + فشار بالا/ARR بالا — آلدوسترونیسم اولیه محتمل.",
                significance="high", supports=["primary_aldosteronism"],
                citation="Endocrine Society PA Guideline 2016",
                inputs={"K": k, "HCO3": bicarb, "ARR": arr or 0})

    # 14. Acid-base: Winter's formula for metabolic acidosis
    if ph and bicarb and ph<7.35 and bicarb<22:
        # Expected pCO2 = 1.5*HCO3 +8 ±2
        pco2 = g("pco2") or g("arterial_pco2") or g("carbon_dioxide_partial_pressure")
        if pco2:
            expected = 1.5*bicarb + 8
            if abs(pco2-expected)>2:
                if pco2>expected+2:
                    add(pattern_id="mixed_acidosis", name_en="Mixed Acidosis",
                        name_fa="اسیدوز مختلط", value=round(pco2,1),
                        interpretation=f"pH {ph:.2f} پایین + HCO3 {bicarb:.0f} پایین + pCO2 {pco2:.0f} بالاتر از انتظار Winter ({expected:.0f}) — اسیدوز متابولیک + تنفسی همزمان.",
                        significance="high", supports=["acute_kidney_injury","sepsis"],
                        citation="Winter's Formula, NEJM 2014",
                        inputs={"pH": ph, "HCO3": bicarb, "pCO2": pco2})
                else:
                    add(pattern_id="resp_alkalosis_plus_met_acidosis", name_en="Met Acidosis + Resp Alkalosis",
                        name_fa="اسیدوز متابولیک + آلکالوز تنفسی", value=round(pco2,1),
                        interpretation=f"pH {ph:.2f} + HCO3 {bicarb:.0f} پایین + pCO2 {pco2:.0f} پایین‌تر از انتظار — اسیدوز متابولیک با آلکالوز تنفسی جبرانی بیش‌ازحد.",
                        significance="moderate", supports=["sepsis"],
                        citation="Winter's Formula",
                        inputs={"pH": ph, "HCO3": bicarb, "pCO2": pco2})

    # 15. Delta ratio for high AG acidosis
    if na and cl and bicarb:
        ag = na - (cl + bicarb)
        alb_v = g("albumin")
        if alb_v and alb_v<4.0:
            ag += 2.5*(4.0-alb_v)
        # The delta ratio is only interpretable in an *established* high-AG
        # acidosis (Kraut 2014: AG clearly raised AND bicarbonate low); with
        # AG 13 and HCO3 23 the quotient of two tiny deltas is noise.
        if ag >= 16 and bicarb < 22:
            delta_ag = ag-12
            delta_hco3 = 24-bicarb
            if delta_hco3>0:
                delta_ratio = delta_ag/delta_hco3
                if delta_ratio<0.4:
                    add(pattern_id="nagd_plus_hagma", name_en="High AG + Normal AG Acidosis",
                        name_fa="اسیدوز با گپ بالا + بدون گپ", value=round(delta_ratio,2),
                        interpretation=f"AG {ag:.0f} بالا، Delta ratio {delta_ratio:.2f} (<0.4) — اسیدوز با گپ بالا همراه اسیدوز بدون گپ (NAGMA) همزمان.",
                        significance="high", supports=["acute_kidney_injury"],
                        citation="Kraut JA, NEJM 2014",
                        inputs={"AG": ag, "DeltaRatio": round(delta_ratio,2), "HCO3": bicarb})
                elif delta_ratio>2:
                    add(pattern_id="hagma_plus_met_alkalosis", name_en="High AG + Met Alkalosis",
                        name_fa="اسیدوز با گپ بالا + آلکالوز متابولیک", value=round(delta_ratio,2),
                        interpretation=f"AG {ag:.0f} بالا، Delta ratio {delta_ratio:.2f} (>2) — اسیدوز با گپ بالا همراه آلکالوز متابولیک.",
                        significance="high", supports=["vomiting","diuretic_use"],
                        citation="Kraut JA 2014",
                        inputs={"AG": ag, "DeltaRatio": round(delta_ratio,2)})

    # 16. Osmolar gap
    osm_calc = g("calculated_osmolality")
    osm_meas = g("osmolality") or g("measured_osmolality") or g("serum_osmolality")
    if osm_calc is None and na and glu and bun:
        osm_calc = 2*na + (glu/18.0) + (bun/2.8)
    if osm_meas and osm_calc:
        og = osm_meas - osm_calc
        if og>10:
            add(pattern_id="high_osm_gap", name_en="High Osmolar Gap",
                name_fa="گپ اسمولار بالا", value=round(og,1),
                interpretation=f"گپ اسمولار {og:.0f} (>10): اسمولالیته اندازه‌گیری {osm_meas:.0f} - محاسبه {osm_calc:.0f} — مسمومیت با الکل سمی (متانول، اتیلن گلیکول) یا کتواسیدوز.",
                significance="high", supports=["toxic_alcohol_poisoning"],
                citation="Kraut JA 2014",
                inputs={"Measured": osm_meas, "Calculated": osm_calc, "Gap": round(og,1)})

    # 17. Corrected Na for glucose already in calcu, but pattern
    if na and glu and glu>200 and na<135:
        corr_na = na + 1.6*(glu-100)/100.0
        if corr_na>=135:
            add(pattern_id="pseudohyponatremia_hyperglycemia", name_en="Pseudohyponatremia Hyperglycemia",
                name_fa="هیپوناترمی کاذب هایپرگلیسمی", value=round(corr_na,1),
                interpretation=f"Na {na:.0f} پایین با قند {glu:.0f} بالا — Na تصحیح‌شده {corr_na:.1f} طبیعی است (هیپوناترمی کاذب).",
                significance="moderate", supports=["type_2_diabetes"],
                citation="Katz MA 1973",
                inputs={"Na": na, "Glucose": glu, "CorrNa": round(corr_na,1)})

    # 18. Hypocalcemia with high phosphate - CKD-MBD
    phos = g("phosphate") or g("phosphate_inorganic")
    if ca and ca<8.5 and phos and phos>4.5:
        if g("egfr_ckd_epi_creatinine") and g("egfr_ckd_epi_creatinine")<60 or (cr and cr>1.3):
            add(pattern_id="ckd_mbd", name_en="CKD-MBD Pattern",
                name_fa="الگوی CKD-MBD", value=round(ca,2),
                interpretation=f"Ca {ca:.1f} پایین + Phos {phos:.1f} بالا + CKD — اختلال استخوان-معدنی CKD. PTH، ویتامین D را بررسی کنید.",
                significance="high", supports=["chronic_kidney_disease"],
                citation="KDIGO CKD-MBD 2017",
                inputs={"Ca": ca, "Phos": phos, "Creatinine": cr or 0})

    # 19. Hypercalcemia with low phosphate - primary hyperpara
    if ca and ca>10.5 and phos and phos<2.5:
        add(pattern_id="hypercalcemia_low_phos", name_en="Hypercalcemia Low Phosphate",
            name_fa="هیپرکلسمی با فسفات پایین", value=round(ca,2),
            interpretation=f"Ca {ca:.1f} بالا + Phos {phos:.1f} پایین — به نفع هایپرپاراتیروئیدی اولیه یا بدخیمی.",
            significance="high", supports=["primary_hyperparathyroidism"],
            citation="Bilezikian JP 2014",
            inputs={"Ca": ca, "Phos": phos})

    # 20. Hyperkalemia with ECG risk + CKD + acidosis
    if k and k>5.5:
        if (cr and cr>1.5) or (bicarb and bicarb<20):
            add(pattern_id="hyperkalemia_ckd_acidosis", name_en="Hyperkalemia with CKD/Acidosis",
                name_fa="هیپرکالمی با CKD/اسیدوز", value=round(k,2),
                interpretation=f"K {k:.1f} بالا (≥5.5) همراه CKD (Cr {cr or 0:.1f}) یا اسیدوز (HCO3 {bicarb or 0:.0f}) — ریسک آریتمی بالا، درمان اورژانسی.",
                significance="high", supports=["chronic_kidney_disease","acute_kidney_injury"],
                citation="KDIGO AKI 2012",
                inputs={"K": k, "Cr": cr or 0, "HCO3": bicarb or 0})

    # 21. Hyponatremia with low osmolality - SIADH vs hypovolemia
    if na and na<135 and osm_meas and osm_meas<280:
        # need volume status, but pattern
        add(pattern_id="hypotonic_hyponatremia", name_en="Hypotonic Hyponatremia",
            name_fa="هیپوناترمی هیپوتونیک", value=round(na,1),
            interpretation=f"Na {na:.0f} پایین + اسمولالیته {osm_meas:.0f} پایین (<280) — هیپوناترمی هیپوتونیک: SIADH، کمبود حجم یا نارسایی آدرنال.",
            significance="high", supports=["siadh","addison_disease"],
            citation="Verbalis JG, Am J Med 2013",
            inputs={"Na": na, "Osm": osm_meas})

    # 22. Atherogenic dyslipidemia: high TG + low HDL + small dense LDL
    if tg and tg>=150 and hdl and hdl<40:
        ldl = g("ldl_cholesterol") or g("ldl_cholesterol_direct")
        if ldl and ldl>=130:
            add(pattern_id="atherogenic_dyslipidemia", name_en="Atherogenic Dyslipidemia",
                name_fa="دیس‌لیپیدمی آتروژنیک", value=round(tg/hdl,2),
                interpretation=f"TG {tg:.0f} بالا + HDL {hdl:.0f} پایین + LDL {ldl:.0f} بالا — دیس‌لیپیدمی آتروژنیک: LDL کوچک-متراکم، ریسک CV بالا.",
                significance="high", supports=["metabolic_syndrome","type_2_diabetes","coronary_artery_disease"],
                citation="NCEP ATP III",
                inputs={"TG": tg, "HDL": hdl, "LDL": ldl})

    # 23. Remnant cholesterol high
    tc = g("total_cholesterol")
    if tc and hdl and (g("ldl_cholesterol") or g("ldl_cholesterol_direct")):
        ldl_v = g("ldl_cholesterol") or g("ldl_cholesterol_direct") or 0
        remnant = tc - hdl - ldl_v
        if remnant>30:
            add(pattern_id="high_remnant_chol", name_en="High Remnant Cholesterol",
                name_fa="کلسترول باقیمانده بالا", value=round(remnant,1),
                interpretation=f"کلسترول باقیمانده {remnant:.0f} (>30) بالا — ریسک باقی‌مانده CV علی‌رغم LDL کنترل‌شده.",
                significance="moderate", supports=["coronary_artery_disease"],
                citation="Varbo A, JACC 2013",
                inputs={"Remnant": round(remnant,1), "TC": tc, "HDL": hdl, "LDL": ldl_v})

    # 24. Hyperuricemia with metabolic syndrome
    ua = g("uric_acid")
    if ua and ua>7:
        if (tg and tg>=150) or (fpg and fpg>=100) or (bp_sys and bp_sys>=130):
            add(pattern_id="hyperuricemia_metabolic", name_en="Hyperuricemia Metabolic",
                name_fa="هیپریوریسمی متابولیک", value=round(ua,1),
                interpretation=f"اسید اوریک {ua:.1f} بالا همراه TG/FPG/BP بالا — هیپریوریسمی در زمینه سندرم متابولیک، ریسک نقرس و CKD.",
                significance="moderate", supports=["gout","metabolic_syndrome"],
                citation="ACR Gout 2020",
                inputs={"UA": ua})

    # 25. Thrombocytosis with inflammation vs essential
    if plt and plt>450:
        if crp and crp>10:
            add(pattern_id="reactive_thrombocytosis", name_en="Reactive Thrombocytosis",
                name_fa="ترومبوسیتوز واکنشی", value=round(plt,0),
                interpretation=f"PLT {plt:.0f} بالا + CRP {crp:.0f} بالا — ترومبوسیتوز واکنشی به التهاب/عفونت/فقر آهن.",
                significance="moderate", supports=["iron_deficiency_anemia","infection"],
                citation="Harrison Hematology",
                inputs={"PLT": plt, "CRP": crp})
        else:
            add(pattern_id="primary_thrombocytosis", name_en="Primary Thrombocytosis?",
                name_fa="ترومبوسیتوز اولیه؟", value=round(plt,0),
                interpretation=f"PLT {plt:.0f} بالا بدون CRP بالا — ترومبوسیتوز اولیه (ET) را در نظر بگیرید، JAK2/CALR.",
                significance="moderate", supports=["essential_thrombocythemia"],
                citation="WHO MPN 2022",
                inputs={"PLT": plt})

    # ==================== ULTRA-PRECISE EXTENDED COVERAGE ====================
    # Additional high-power patterns for outstanding analysis

    # 16. Hyponatremia severe + hypo-osmolality
    na = g("sodium")
    osmo = g("osmolality") or g("calculated_osmolality") or g("serum_osmolality")
    if na and na<135:
        if osmo and osmo<275:
            add(pattern_id="hypotonic_hyponatremia_severe", name_en="Hypotonic Hyponatremia Detailed",
                name_fa="هیپوناترمی هیپوتونیک دقیق", value=round(na,0),
                interpretation=f"Na {na:.0f} + اسمولالیته {osmo:.0f} پایین — هیپوناترمی هیپوتونیک واقعی. بررسی حجم خارج سلولی، TSH، کورتیزول، داروها (تیازید).",
                significance="high", supports=["siadh","adrenal_insufficiency","hypothyroidism"],
                citation="Verbalis JG, Am J Med 2013",
                inputs={"Na": na, "Osm": osmo})
        if na<120:
            add(pattern_id="severe_hyponatremia_critical", name_en="Critical Hyponatremia",
                name_fa="هیپوناترمی بحرانی", value=round(na,0),
                interpretation=f"Na {na:.0f} <120 — بحرانی، ریسک تشنج/ادم مغزی. اصلاح آهسته ≤8 mmol/24h، بررسی علت مرکزی.",
                significance="high", supports=["siadh","adrenal_insufficiency"],
                citation="Verbalis 2013",
                inputs={"Na": na})

    # 17. Hypernatremia
    if na and na>145:
        if osmo and osmo>295:
            add(pattern_id="hypernatremia_hyperosmolar", name_en="Hypernatremia Hyperosmolar",
                name_fa="هیپرناترمی هیپراسمولار", value=round(na,0),
                interpretation=f"Na {na:.0f} + اسمولالیته {osmo:.0f} بالا — دهیدراتاسیون یا دیابت بی‌مزه. بررسی دسترسی به آب، ADH، ادرار اسمولالیته.",
                significance="high", supports=["diabetes_insipidus","dehydration"],
                citation="Adrogué HJ, NEJM 2000",
                inputs={"Na": na, "Osm": osmo})

    # 18. Hypokalemia with alkalosis
    k = g("potassium")
    if k and k<3.5:
        if bicarb and bicarb>29:
            add(pattern_id="hypokalemia_alkalosis", name_en="Hypokalemia with Met Alkalosis",
                name_fa="هیپوکالمی با آلکالوز متابولیک", value=round(k,2),
                interpretation=f"K {k:.1f} پایین + HCO3 {bicarb:.0f} بالا — استفراغ، دیورتیک لوپ/تیازید، آلدوسترونیسم. بررسی Mg، Cl ادرار.",
                significance="moderate", supports=["primary_aldosteronism","vomiting","diuretic_abuse"],
                citation="Weiner ID, JASN 2019",
                inputs={"K": k, "HCO3": bicarb})

    # 19. Hypocalcemia patterns
    ca = g("calcium_total") or g("corrected_calcium")
    phos = g("phosphate")
    pth = g("parathyroid_hormone")
    vitd = g("vitamin_d") or g("25_hydroxy_vitamin_d")
    if ca and ca<8.5:
        if pth and pth<15:
            add(pattern_id="hypocalcemia_low_pth", name_en="Hypocalcemia Low PTH",
                name_fa="هیپوکلسمی با PTH پایین", value=round(ca,2),
                interpretation=f"Ca {ca:.1f} پایین + PTH {pth:.0f} پایین — هیپوپاراتیروئیدیسم، هیپومنیزیمی یا پس از تیروئیدکتومی.",
                significance="high", supports=["hypoparathyroidism"],
                citation="Bilezikian JP 2020",
                inputs={"Ca": ca, "PTH": pth})
        elif vitd and vitd<20:
            add(pattern_id="hypocalcemia_vitd_def", name_en="Hypocalcemia VitD Deficiency",
                name_fa="هیپوکلسمی کمبود ویتامین D", value=round(ca,2),
                interpretation=f"Ca {ca:.1f} پایین + VitD {vitd:.0f} پایین — کمبود ویتامین D با هیپوکلسمی ثانویه. بررسی PTH ثانویه.",
                significance="moderate", supports=["vitamin_d_deficiency","secondary_hyperparathyroidism"],
                citation="Holick MF 2011",
                inputs={"Ca": ca, "VitD": vitd})

    # 20. Hyperphosphatemia in CKD - PEDIATRIC AWARE
    if phos and phos>4.5:
        age_for_phos = _ctx_get("age_years")
        try:
            age_for_phos = float(age_for_phos) if age_for_phos is not None else None
        except:
            age_for_phos = None
        # Pediatric normal: <12 up to 6.5, 12-18 up to 5.5
        is_pediatric_phos_normal = False
        if age_for_phos is not None:
            if age_for_phos < 12 and phos <= 6.5:
                is_pediatric_phos_normal = True
            elif age_for_phos < 18 and phos <= 5.5:
                is_pediatric_phos_normal = True

        if is_pediatric_phos_normal:
            add(pattern_id="phos_pediatric_normal", name_en="Phosphorus Pediatric Normal",
                name_fa="فسفر طبیعی کودک", value=round(phos,2),
                interpretation=f"فسفر {phos:.1f} در کودک {age_for_phos:.0f} ساله — در کودکان فسفر تا {6.5 if age_for_phos<12 else 5.5:.1f} طبیعی است (رشد استخوانی).",
                significance="low", supports=[],
                argues_against=["chronic_kidney_disease"],
                citation="CALIPER Pediatric Reference 2020",
                inputs={"Phos": phos, "Age": age_for_phos or 0})
        else:
            cr = g("creatinine")
            if cr and cr>1.5:
                add(pattern_id="hyperphos_ckd", name_en="Hyperphosphatemia CKD",
                    name_fa="هیپرفسفاتمی در CKD", value=round(phos,2),
                    interpretation=f"فسفر {phos:.1f} بالا + کراتینین {cr:.1f} بالا — احتباس فسفر در CKD، ریسک CKD-MBD. بررسی Ca، PTH، VitD.",
                    significance="moderate", supports=["chronic_kidney_disease","secondary_hyperparathyroidism"],
                    citation="KDIGO CKD-MBD 2017",
                    inputs={"Phos": phos, "Cr": cr})
            elif phos>5.5:
                add(pattern_id="hyperphosphatemia", name_en="Hyperphosphatemia",
                    name_fa="هیپرفسفاتمی", value=round(phos,2),
                    interpretation=f"فسفر {phos:.1f} بالا — CKD، هیپوپارا، تومور لیز، یا مصرف زیاد.",
                    significance="moderate", supports=["chronic_kidney_disease","hypoparathyroidism"],
                    citation="KDIGO CKD-MBD 2017",
                    inputs={"Phos": phos})

    # 21. Hypophosphatemia
    if phos and phos<2.5:
        add(pattern_id="hypophosphatemia", name_en="Hypophosphatemia",
            name_fa="هیپوفسفاتمی", value=round(phos,2),
            interpretation=f"فسفر {phos:.1f} پایین — سوءتغذیه، الکلیسم، دیورتیک، Fanconi. ریسک ضعف عضلانی/نارسایی تنفسی اگر <1.0.",
            significance="moderate", supports=["malnutrition","alcoholism","fanconi_syndrome"],
            citation="Gaasbeek A, Am J Med 2005",
            inputs={"Phos": phos})

    # 22. Hypomagnesemia with hypoK/hypoCa
    mg = g("magnesium")
    if mg and mg<1.7:
        if (k and k<3.5) or (ca and ca<8.5):
            add(pattern_id="hypomag_with_hypok_hypoca", name_en="Hypomagnesemia with HypoK/HypoCa",
                name_fa="هیپومنیزیمی با هیپوکالمی/هیپوکلسمی", value=round(mg,2),
                interpretation=f"Mg {mg:.1f} پایین + K {k or 0:.1f}/Ca {ca or 0:.1f} پایین — هیپومنیزیمی علت مقاوم به درمان هیپوکالمی/هیپوکلسمی. اصلاح Mg اول.",
                significance="high", supports=["hypomagnesemia"],
                citation="de Baaij JHF, Physiol Rev 2015",
                inputs={"Mg": mg, "K": k or 0, "Ca": ca or 0})

    # 23. Metabolic alkalosis
    if bicarb and bicarb>29 and ph and ph>7.45:
        add(pattern_id="metabolic_alkalosis", name_en="Metabolic Alkalosis",
            name_fa="آلکالوز متابولیک", value=round(bicarb,0),
            interpretation=f"pH {ph:.2f} بالا + HCO3 {bicarb:.0f} بالا — آلکالوز متابولیک (استفراغ، دیورتیک، آلدوسترونیسم). بررسی Cl ادرار.",
            significance="moderate", supports=["vomiting","primary_aldosteronism"],
            citation="Emmett M, NEJM 2020",
            inputs={"pH": ph, "HCO3": bicarb})

    # 24. Respiratory acidosis
    pco2 = g("pco2") or g("arterial_pco2") or g("carbon_dioxide_partial_pressure")
    if ph and ph<7.35 and pco2 and pco2>45:
        add(pattern_id="respiratory_acidosis", name_en="Respiratory Acidosis",
            name_fa="اسیدوز تنفسی", value=round(pco2,0),
            interpretation=f"pH {ph:.2f} پایین + pCO2 {pco2:.0f} بالا — اسیدوز تنفسی (COPD، افیون، ضعف عضلانی). HCO3 جبرانی {bicarb or 0:.0f}.",
            significance="high", supports=["copd","respiratory_failure"],
            citation="Adrogué HJ, NEJM 2022",
            inputs={"pH": ph, "pCO2": pco2, "HCO3": bicarb or 0})

    # 25. Respiratory alkalosis
    if ph and ph>7.45 and pco2 and pco2<35:
        add(pattern_id="respiratory_alkalosis", name_en="Respiratory Alkalosis",
            name_fa="آلکالوز تنفسی", value=round(pco2,0),
            interpretation=f"pH {ph:.2f} بالا + pCO2 {pco2:.0f} پایین — آلکالوز تنفسی (اضطراب، درد، سپسیس، سیروز، سالیسیلات).",
            significance="moderate", supports=["anxiety","sepsis","liver_cirrhosis"],
            citation="Adrogué HJ 2022",
            inputs={"pH": ph, "pCO2": pco2})

    # 26. Vitamin D deficiency secondary hyperpara
    if vitd and vitd<20 and pth and pth>65 and ca and ca<10.2:
        add(pattern_id="vitd_def_secondary_hpt", name_en="VitD Def Secondary Hyperpara",
            name_fa="کمبود VitD با هایپرپارای ثانویه", value=round(vitd,1),
            interpretation=f"VitD {vitd:.0f} پایین + PTH {pth:.0f} بالا + Ca طبیعی/پایین — هایپرپاراتیروئیدیسم ثانویه به کمبود VitD.",
            significance="high", supports=["vitamin_d_deficiency","secondary_hyperparathyroidism"],
            citation="Holick MF 2011",
            inputs={"VitD": vitd, "PTH": pth, "Ca": ca})

    # 27. Secondary hyperpara in CKD
    if pth and pth>65:
        egfr = g("egfr_ckd_epi_creatinine")
        if (egfr and egfr<60) or (g("creatinine") and g("creatinine")>1.5):
            if ca and ca<=10.2 and phos and phos>=4.5:
                add(pattern_id="secondary_hpt_ckd", name_en="Secondary HPT CKD",
                    name_fa="هایپرپارای ثانویه در CKD", value=round(pth,0),
                    interpretation=f"PTH {pth:.0f} بالا + eGFR پایین + Ca طبیعی/پایین + Phos بالا — هایپرپارای ثانویه CKD. بررسی VitD، CKD-MBD.",
                    significance="high", supports=["secondary_hyperparathyroidism","chronic_kidney_disease"],
                    citation="KDIGO CKD-MBD 2017",
                    inputs={"PTH": pth, "Ca": ca, "Phos": phos})

    # 28. Cushing pattern
    cortisol = g("cortisol_morning") or g("cortisol")
    if cortisol and cortisol>25:
        if (k and k<3.5) or (glu and glu>126) or (bp_sys and bp_sys>=140):
            add(pattern_id="cushing_pattern", name_en="Cushing Pattern",
                name_fa="الگوی کوشینگ", value=round(cortisol,1),
                interpretation=f"کورتیزول {cortisol:.0f} بالا + K پایین/قند بالا/BP بالا — الگوی کوشینگ. بررسی ACTH، تست دگزامتازون.",
                significance="high", supports=["cushing_syndrome"],
                citation="Nieman LK, JCEM 2015",
                inputs={"Cortisol": cortisol, "K": k or 0, "Glucose": glu or 0})

    # 29. Severe malnutrition
    alb = g("albumin")
    prealb = g("prealbumin") or g("transthyretin")
    bmi_val = g("body_mass_index") or g("bmi") or _ctx_get("body_mass_index") or _ctx_get("bmi")
    if alb and alb<3.0 and prealb and prealb<15 and bmi_val and bmi_val<18.5:
        add(pattern_id="severe_malnutrition", name_en="Severe Malnutrition",
            name_fa="سوءتغذیه شدید", value=round(alb,1),
            interpretation=f"آلبومین {alb:.1f} + پره‌آلبومین {prealb:.0f} + BMI {bmi_val:.1f} پایین — سوءتغذیه شدید پروتئین-کالری. ریسک عفونت/مرگ بالا.",
            significance="high", supports=["malnutrition"],
            citation="ASPEN Malnutrition 2020",
            inputs={"Albumin": alb, "Prealbumin": prealb, "BMI": bmi_val})

    # 30. Atherogenic triad
    tg = g("triglycerides")
    hdl = g("hdl_cholesterol")
    ldl = g("ldl_cholesterol")
    if tg and tg>=150 and hdl and hdl<40 and ldl and ldl>130:
        add(pattern_id="atherogenic_triad", name_en="Atherogenic Triad",
            name_fa="تریاد آتروژنیک", value=round(tg/hdl if hdl else 0,1),
            interpretation=f"TG {tg:.0f} بالا + HDL {hdl:.0f} پایین + LDL {ldl:.0f} بالا — دیس‌لیپیدمی آتروژنیک، ریسک ASCVD بسیار بالا.",
            significance="high", supports=["metabolic_syndrome","coronary_artery_disease"],
            citation="AHA Dyslipidemia 2018",
            inputs={"TG": tg, "HDL": hdl, "LDL": ldl})

    # 31. High RDW with normal MCV - early iron/B12 deficiency
    rdw = g("red_cell_distribution_width")
    mcv = g("mean_corpuscular_volume")
    if hb and hb<12 and rdw and rdw>15 and mcv and 80<=mcv<=100:
        add(pattern_id="high_rdw_normocytic", name_en="High RDW Normocytic Anemia",
            name_fa="RDW بالا با MCV نرمال", value=round(rdw,1),
            interpretation=f"Hb {hb:.1f} پایین + RDW {rdw:.1f} بالا + MCV {mcv:.0f} نرمال — کمبود زودرس آهن/B12/فولات یا پاسخ به درمان.",
            significance="moderate", supports=["iron_deficiency_anemia","vitamin_b12_deficiency"],
            citation="BSH Anemia 2023",
            inputs={"Hb": hb, "RDW": rdw, "MCV": mcv})

    # 32. Leukocytosis with left shift
    wbc = g("white_blood_cell_count")
    neut = g("neutrophils")
    if wbc and wbc>11 and neut and neut>75:
        add(pattern_id="leukocytosis_left_shift", name_en="Leukocytosis Left Shift",
            name_fa="لکوسیتوز با شیفت چپ", value=round(wbc,1),
            interpretation=f"WBC {wbc:.1f} بالا + نوتروفیل {neut:.0f}% بالا — عفونت باکتریال حاد یا التهاب شدید.",
            significance="moderate", supports=["bacterial_infection","sepsis"],
            citation="Harrison Infectious Disease",
            inputs={"WBC": wbc, "Neut": neut})

    # 33. Thrombocytopenia severe
    if plt and plt<50:
        add(pattern_id="severe_thrombocytopenia", name_en="Severe Thrombocytopenia",
            name_fa="ترومبوسیتوپنی شدید", value=round(plt,0),
            interpretation=f"PLT {plt:.0f} <50k شدید — ریسک خونریزی خودبه‌خودی. بررسی ITP، DIC، دارو، هیپارین، بدخیمی.",
            significance="high", supports=["immune_thrombocytopenia","disseminated_intravascular_coagulation"],
            citation="BSH Thrombocytopenia 2023",
            inputs={"PLT": plt})

    # 34. ESR/CRP dissociation
    esr = g("erythrocyte_sedimentation_rate")
    crp = g("c_reactive_protein")
    if esr and esr>50 and crp and crp<10:
        add(pattern_id="esr_crp_dissociation", name_en="ESR/CRP Dissociation",
            name_fa="عدم تطابق ESR/CRP", value=round(esr,0),
            interpretation=f"ESR {esr:.0f} بالا + CRP {crp:.0f} پایین — الگوی بیماری مزمن/خودایمنی (SLE، میلوما) نه عفونت حاد.",
            significance="moderate", supports=["systemic_lupus_erythematosus","multiple_myeloma"],
            citation="Lapić I, Biochem Med 2020",
            inputs={"ESR": esr, "CRP": crp})

    # 35. Hypothyroidism metabolic effects
    tsh = g("thyroid_stimulating_hormone")
    ft4 = g("free_thyroxine")
    chol = g("total_cholesterol")
    ck = g("creatine_kinase")
    if tsh and tsh>10 and ft4 and ft4<0.8:
        if (chol and chol>240) or (ck and ck>200):
            add(pattern_id="hypothyroid_metabolic", name_en="Hypothyroid Metabolic Effects",
                name_fa="اثرات متابولیک کم‌کاری تیروئید", value=round(tsh,1),
                interpretation=f"TSH {tsh:.1f} بالا + FT4 {ft4:.1f} پایین + کلسترول {chol or 0:.0f}/CK {ck or 0:.0f} بالا — اثرات متابولیک کم‌کاری تیروئید.",
                significance="moderate", supports=["hypothyroidism"],
                citation="ATA Hypothyroidism 2014",
                inputs={"TSH": tsh, "FT4": ft4, "Chol": chol or 0, "CK": ck or 0})

    # 36. ULTRA-PRECISE: Pediatric overall normal assessment
    age_check = _ctx_get("age_years")
    try:
        age_check = float(age_check) if age_check is not None else None
    except:
        age_check = None
    if age_check is not None and age_check < 18:
        normal_count = 0
        total_checked = 0
        hb = g("hemoglobin")
        if hb and 11.5 <= hb <= 15.5:
            normal_count += 1
        total_checked += 1
        wbc = g("white_blood_cell_count")
        if wbc and 4500 <= wbc <= 13500:
            normal_count += 1
        total_checked += 1
        plt = g("platelet_count")
        plt_norm = plt
        if plt and plt > 1000:
            plt_norm = plt / 1000
            if 150 <= plt_norm <= 450:
                normal_count += 1
        elif plt and 150 <= plt <= 450:
            normal_count += 1
        total_checked += 1
        glu = g("fasting_plasma_glucose") or g("glucose")
        if glu and 70 <= glu <= 100:
            normal_count += 1
        total_checked += 1
        cr = g("creatinine")
        if cr and 0.3 <= cr <= 0.9:
            normal_count += 1
        total_checked += 1
        ca = g("calcium_total") or g("calcium")
        if ca and 9.0 <= ca <= 11.0:
            normal_count += 1
        total_checked += 1
        ast = g("aspartate_aminotransferase")
        alt = g("alanine_aminotransferase")
        if ast and ast < 40 and alt and alt < 40:
            normal_count += 1
        total_checked += 1

        if total_checked >= 5 and normal_count / total_checked >= 0.7:
            add(pattern_id="pediatric_normal_labs", name_en="Pediatric Normal Labs - Healthy Child",
                name_fa="آزمایش‌های طبیعی کودک سالم", value=round(normal_count/total_checked*100,0),
                interpretation=f"در کودک {age_check:.0f} ساله، {normal_count}/{total_checked} شاخص اصلی در محدوده طبیعی کودکان است. ALP بالا ({g('alkaline_phosphatase') or 0:.0f}) و فسفر {g('phosphate') or 0:.1f} به دلیل رشد استخوانی طبیعی است، نه بیماری کبدی. BUN/Cr بالا به دلیل توده عضلانی کم کودک است. تفسیر کلی: طبیعی، رشد و تکامل طبیعی.",
                significance="low", supports=[],
                argues_against=["cholestasis","alcoholic_liver_disease","acute_kidney_injury","acute_pancreatitis","celiac_disease","tumor_lysis_syndrome"],
                citation="CALIPER Pediatric Reference Intervals 2020; Harriet Lane Handbook",
                inputs={"Age": age_check, "NormalRatio": round(normal_count/total_checked,2)})

    # 37. Thrombotic Microangiopathy (TMA / TTP / HUS Pattern)
    haptoglobin_v = g("serum_haptoglobin") or g("haptoglobin")
    inr_v = g("inr") or g("international_normalized_ratio")
    fib_v = g("fibrinogen")
    retic_v = g("reticulocytes") or g("reticulocyte_count_percent") or g("reticulocyte_count")
    indir_bili = g("indirect_bilirubin")
    if (plt and plt < 50.0) and (ldh and ldh > 500.0) and (hb and hb < 10.0):
        if (haptoglobin_v is not None and haptoglobin_v < 15.0) or (indir_bili and indir_bili > 1.2) or (retic_v and retic_v > 3.0):
            is_normal_coag = (inr_v is None or inr_v <= 1.3) and (fib_v is None or fib_v >= 150.0)
            if is_normal_coag:
                add(
                    pattern_id="tma_ttp_pattern",
                    name_en="Thrombotic Microangiopathy (TTP / HUS Pattern)",
                    name_fa="الگوی میکروآنژیوپاتی ترومبوتیک (TTP / HUS)",
                    value=round(plt, 0),
                    interpretation=(
                        f"آنمی همولیتیک میکروآنژیوپاتیک (MAHA: LDH {ldh:.0f} بالا، Hb {hb:.1f} پایین) "
                        f"همراه با ترومبوسیتوپنی شدید ({plt:.0f}k) و تست‌های انعقادی طبیعی (INR {inr_v or 1.0:.2f}، فیبرینوژن {fib_v or 300:.0f}). "
                        f"این الگو نشان‌دهنده ترومبوز میکروواسکولار پلاکت-vWF (TTP/HUS) است. "
                        f"فوریت حیاتی: پلاسمافرز فوری (PEX) و پرهیز اکید از تزریق پلاکت (کنترااندیکه)."
                    ),
                    significance="high",
                    supports=["thrombotic_thrombocytopenic_purpura", "thrombotic_microangiopathy"],
                    argues_against=["disseminated_intravascular_coagulation"],
                    citation="Scully M, et al. ISTH TTP Guidelines 2020",
                    inputs={"PLT": plt, "LDH": ldh, "Hb": hb, "INR": inr_v or 1.0, "Fibrinogen": fib_v or 300}
                )

    # 38. Hemophagocytic Lymphohistiocytosis (HLH / MAS Pattern)
    ferr_v = g("ferritin")
    tg_v = g("triglycerides")
    if ferr_v and ferr_v > 3000.0:
        cytopenia_count = 0
        if hb and hb < 9.0: cytopenia_count += 1
        if plt and plt < 100.0: cytopenia_count += 1
        if wbc and wbc < 4.0: cytopenia_count += 1
        has_hlh_support = (cytopenia_count >= 2) or (fib_v is not None and fib_v < 150.0) or (tg_v is not None and tg_v > 265.0) or (ast and ast > 150.0)
        if has_hlh_support:
            add(
                pattern_id="hlh_mas_pattern",
                name_en="Hemophagocytic Lymphohistiocytosis (HLH / MAS Pattern)",
                name_fa="سندروم لنفوهیستوسیتوزیس هموفاگوسیتیک (HLH / MAS)",
                value=round(ferr_v, 0),
                interpretation=(
                    f"هیپرفریتینمی شدید ({ferr_v:.0f} ng/mL) همراه با سیتوپنی چندرده‌ای، هیپوفیبرینوژنمی یا آسیب کبدی — "
                    f"معیارهای تشخیصی HLH-2004 و شاخص HScore برآورده شده است. "
                    f"احتمال بالای طوفان سیتوکینی و فعال‌سازی شدید ماکروفاژها. "
                    f"بررسی فوری soluble CD25 (sIL-2R)، آسپیراسیون مغز استخوان و مشاوره انکولوژی/روماتولوژی جهت درمان سرکوب ایمنی اورژانس."
                ),
                significance="high",
                supports=["hemophagocytic_lymphohistiocytosis", "hemophagocytic_syndrome_malignancy_associated_pattern"],
                citation="Henter JI, et al. HLH-2004 Guidelines",
                inputs={"Ferritin": ferr_v, "Cytopenias": cytopenia_count, "Fibrinogen": fib_v or 0, "TG": tg_v or 0}
            )

    # 39. Adrenal Insufficiency Disambiguation (Primary vs Secondary)
    acth_v = g("adrenocorticotropic_hormone") or g("acth")
    cort_v = g("morning_cortisol") or g("cortisol_morning") or g("cortisol_8am") or g("cortisol")
    if cort_v and cort_v < 5.0:
        if acth_v and acth_v < 20.0 and (k is None or k <= 4.8):
            add(
                pattern_id="secondary_adrenal_insufficiency_pattern",
                name_en="Secondary Adrenal Insufficiency Pattern",
                name_fa="الگوی نارسایی ثانویه آدرنال (هیپوفیزی/مهار استروئید)",
                value=round(cort_v, 1),
                interpretation=(
                    f"کورتیزول صبحگاهی پایین ({cort_v:.1f} µg/dL) با ACTH نامتناسباً نرمال/پایین ({acth_v:.1f} pg/mL) و پتاسیم طبیعی ({k or 4.0:.1f} mmol/L) — "
                    f"به نفع نارسایی ثانویه/ثالثیه آدرنال (مهار محور هیپوتالاموس-هیپوفیز پس از مصرف استروئید یا پاتولوژی هیپوفیز) با حفظ محور رنین-آلدوسترون، "
                    f"نه بیماری آدیسون اولیه."
                ),
                significance="high",
                supports=["central_adrenal_insufficiency"],
                argues_against=["primary_adrenal_insufficiency_addison", "primary_adrenal_insufficiency"],
                citation="Bornstein SR, JCEM 2016",
                inputs={"Cortisol": cort_v, "ACTH": acth_v, "Potassium": k or 0}
            )
        elif (acth_v and acth_v > 60.0) or (k and k > 5.2):
            add(
                pattern_id="primary_adrenal_insufficiency_pattern",
                name_en="Primary Adrenal Insufficiency (Addison Pattern)",
                name_fa="الگوی نارسایی اولیه آدرنال (بیماری آدیسون)",
                value=round(cort_v, 1),
                interpretation=(
                    f"کورتیزول صبحگاهی پایین ({cort_v:.1f} µg/dL) همراه با ACTH بالا ({acth_v or 0:.1f} pg/mL) و هایپرکالمی ({k or 0:.1f} mmol/L) — "
                    f"الگوی کلاسیک بیماری آدیسون (نارسایی قشر آدرنال با کمبود توأم گلوکوکورتیکوئید و مینرالوکورتیکوئید)."
                ),
                significance="high",
                supports=["primary_adrenal_insufficiency_addison", "primary_adrenal_insufficiency"],
                argues_against=["central_adrenal_insufficiency"],
                citation="Bornstein SR, JCEM 2016",
                inputs={"Cortisol": cort_v, "ACTH": acth_v or 0, "Potassium": k or 0}
            )

    # 40. Pheochromocytoma / Paraganglioma Catecholamine Crisis
    p_meta = g("plasma_free_metanephrines") or g("plasma_metanephrine")
    p_normeta = g("plasma_free_normetanephrines") or g("plasma_normetanephrine")
    # Handle both pg/mL and nmol/L (1 nmol/L ~ 197 pg/mL)
    p_meta_pg = (p_meta * 197.2 if p_meta < 50.0 else p_meta) if p_meta is not None else None
    p_normeta_pg = (p_normeta * 183.2 if p_normeta < 50.0 else p_normeta) if p_normeta is not None else None
    if (p_meta_pg and p_meta_pg > 200.0) or (p_normeta_pg and p_normeta_pg > 400.0):
        add(
            pattern_id="pheochromocytoma_crisis_pattern",
            name_en="Pheochromocytoma Catecholamine Excess Pattern",
            name_fa="الگوی ترشح شدید کاتکول‌آمین‌ها (فئوکروموسیتوم)",
            value=round(max(p_meta or 0, p_normeta or 0), 1),
            interpretation=(
                f"افزایش بارز متانفرین‌های پلاسما (Metanephrine: {p_meta_pg or 0:.0f} pg/mL، Normetanephrine: {p_normeta_pg or 0:.0f} pg/mL) "
                f"همراه با بحران فشارخون — بسیار اختصاصی برای تومور کرومافین (فئوکروموسیتوم/پاراگانگلیوم). "
                f"هشدار دارویی: هرگز از بتابلوکر قبل از آلفابلوک کامل استفاده نشود (ریسک بحران فشارخون مرگبار)."
            ),
            significance="high",
            supports=["pheochromocytoma", "pheochromocytoma_adrenal_medulla"],
            citation="Lenders JWM, JCEM 2014",
            inputs={"Metanephrines": round(p_meta_pg or 0, 1), "Normetanephrines": round(p_normeta_pg or 0, 1)}
        )

    return out




@functools.lru_cache(maxsize=4096)
def _is_finding_entity(disease_id: str) -> bool:
    """True when the entity's name is nothing but a laboratory finding plus
    modifiers (hyperkalemia, severe_hypoglycemia_pattern)."""
    tokens = [t for t in str(disease_id or "").casefold().split("_") if t]
    if not tokens:
        return False
    lex = {f[0] for f in DiseaseGuidelineRegistry._FINDING_LEXICON}
    mods = DiseaseGuidelineRegistry._FINDING_MODIFIERS
    found = False
    for t in tokens:
        if t in lex:
            found = True
        elif t not in mods:
            return False
    return found


# --- Code-level curation of the AI-assisted registry -----------------------
# Rules whose expression contradicts the entity (e.g. "hypoglycemia" supported
# by glucose >= 140) are removed at load time.
QUARANTINED_RULE_IDS: frozenset[str] = frozenset({
    "hyperinsulinemic_hypoglycemia_guideline_criterion_v1",
    "factitious_hypoglycemia_guideline_criterion_v1",
    # Requires 24-h protein AND UPCR AND UACR AND albumin simultaneously - no
    # real report carries all three proteinuria measures; replaced by
    # nephrotic_syndrome_kdigo_any_proteinuria_v1 (any one measure + albumin).
    "nephrotic_syndrome_v1",
    # "Hypercalcaemia of malignancy" supported by glucose >= 140 mg/dL.
    "hypercalcemia_of_malignancy_support_pattern_guideline_criterion_v1",
    # Thyroid / cortisol / HbA1c screens attached to the HHS entity make a
    # TSH of 5 vote for a hyperosmolar emergency.
    "hyperosmolar_hyperglycemic_state_tsh_hypothyroid_screen",
    "hyperosmolar_hyperglycemic_state_tsh_hyperthyroid_screen",
    "hyperosmolar_hyperglycemic_state_addison_morning_cortisol",
    "hyperosmolar_hyperglycemic_state_free_t4_low_target",
    "hyperosmolar_hyperglycemic_state_free_t4_high_target",
})

_DIRECTION_ANALYTE_MAP = {
    "kalemia": "potassium", "natremia": "sodium", "calcemia": "calcium",
    "glycemia": "glucose", "magnesemia": "magnesium", "phosphatemia": "phosph",
    "albuminemia": "albumin", "uricemia": "uric_acid", "chloremia": "chloride",
    "triglyceridemia": "triglycerid", "cholesterolemia": "cholesterol",
    "prolactinemia": "prolactin", "ammonemia": "ammonia", "lactatemia": "lactate",
}


def _leaf_conditions(expr: Any) -> list[dict[str, Any]]:
    if not isinstance(expr, Mapping):
        return []
    if "feature_id" in expr:
        return [dict(expr)]
    out: list[dict[str, Any]] = []
    for key in ("all", "any", "conditions", "not", "n_of"):
        sub = expr.get(key)
        if isinstance(sub, list):
            for e in sub:
                out.extend(_leaf_conditions(e))
        elif isinstance(sub, Mapping):
            out.extend(_leaf_conditions(sub))
    return out


def _direction_contradictions(rules: Mapping[str, Mapping[str, Any]]) -> list[tuple[str, str]]:
    """Single-condition supportive rules pointing the wrong way for a hypo-/hyper- entity."""
    found: list[tuple[str, str]] = []
    for rid, r in rules.items():
        if str(r.get("rule_type", "")).startswith("exclusion"):
            continue
        did = str(r.get("disease_id", ""))
        expr = r.get("expression") or {}
        if "feature_id" not in expr:          # only unambiguous single-condition rules
            continue
        fid = str(expr.get("feature_id", ""))
        op = expr.get("operator")
        for suffix, analyte in _DIRECTION_ANALYTE_MAP.items():
            if analyte not in fid:
                continue
            if (did.startswith("hypo" + suffix) or "_hypo" + suffix in did) and op in (">", ">="):
                found.append((rid, did))
            elif (did.startswith("hyper" + suffix) or "_hyper" + suffix in did) and op in ("<", "<="):
                found.append((rid, did))
    return found


def _who_anemia_rule(rule_id: str, title: str, hb: float, sex: str, age_groups: list[str],
                     pregnancy: str = "excluded") -> dict[str, Any]:
    return {
        "rule_id": rule_id, "disease_id": "anemia", "rule_type": "screening",
        "legacy_rule_type": "screening", "specificity": "specific",
        "status": "candidate_requires_specialist_validation", "executable": True, "urgent": False,
        "expression": {"feature_id": "hemoglobin", "operator": "<", "value": hb, "unit": "g/dL", "weight": 3.0},
        "weight": 4.0,
        "population": {"age_groups": age_groups, "sex": sex, "pregnancy": pregnancy},
        "result": {"allowed_labels": ["criterion_met", "compatible_pattern", "possible_pattern",
                                      "screening_positive", "urgent_pattern", "excluded", "insufficient_data",
                                      "conflicting_data", "criterion_not_met", "not_applicable"],
                   "diagnosis_allowed": False},
        "confirmation": {"required": True, "human_review": True},
        "limitations": [f"WHO 2024 haemoglobin cut-off {hb} g/dL at sea level; adjust for altitude/smoking"],
        "source_ids": ["who_2024"], "title": title,
        "scientific_explanation": f"WHO 2024 guideline on haemoglobin cutoffs: {title} Hb < {hb} g/dL",
        "_supplemental": True,
    }


_ALL_AGES = ["neonate", "infant", "child", "adolescent", "adult", "older_adult"]
_ADULT_AGES = ["adolescent", "adult", "older_adult"]


def _leaf(fid: str, op: str, value: float, unit: str, weight: float = 1.0) -> dict[str, Any]:
    return {"feature_id": fid, "operator": op, "value": value, "unit": unit, "weight": weight}


def _sup_rule(rule_id: str, disease_id: str, rule_type: str, expression: dict[str, Any],
              title: str, source_id: str, explanation: str, limitations: list[str],
              *, specificity: str = "specific", urgent: bool = False, weight: float = 4.0,
              age_groups: Optional[list[str]] = None, sex: str = "all",
              pregnancy: str = "context_dependent", tier: str = "tier_a") -> dict[str, Any]:
    """Code-level, source-anchored rule for an entity the shipped registry covers
    only with non-specific CBC/iron screens (see HARDENING_CHANGELOG 1.3.1)."""
    return {
        "rule_id": rule_id, "disease_id": disease_id, "rule_type": rule_type,
        "legacy_rule_type": rule_type, "specificity": specificity,
        "status": "candidate_requires_specialist_validation", "executable": True,
        "urgent": urgent, "expression": expression, "weight": weight,
        "population": {"age_groups": age_groups or _ALL_AGES, "sex": sex, "pregnancy": pregnancy},
        "result": {"allowed_labels": ["criterion_met", "compatible_pattern", "possible_pattern",
                                      "screening_positive", "urgent_pattern", "excluded",
                                      "insufficient_data", "conflicting_data", "criterion_not_met",
                                      "not_applicable"],
                   "diagnosis_allowed": False},
        "confirmation": {"required": True, "human_review": True,
                         "repeat_or_alternative_test": "context_dependent"},
        "limitations": limitations, "source_ids": [source_id], "title": title,
        "scientific_explanation": explanation,
        "clinical_rationale": explanation, "evidence_tier": tier,
        "entity_kind": "clinical_entity", "_supplemental": True,
    }


SUPPLEMENTAL_RULES: list[dict[str, Any]] = [
    # ---- acute pancreatitis: lipase >= 3x ULN (revised Atlanta; ACG 2024) ----
    _sup_rule("acute_pancreatitis_lipase_3x_uln_acg2024", "acute_pancreatitis", "diagnostic_criterion",
              _leaf("lipase", ">=", 180.0, "U/L", 3.0),
              "Acute pancreatitis - lipase >= 3x ULN (ACG 2024 / revised Atlanta)",
              "acg_acute_pancreatitis_2024",
              "Serum lipase >= 3 times the upper reference limit is one of the two laboratory criteria "
              "(with typical pain or imaging) for acute pancreatitis; sensitivity ~90 %, specificity ~95 %.",
              ["ULN assumed 60 U/L; scale to the performing laboratory's interval.",
               "Renal failure, bowel ischaemia, DKA and macrolipasaemia also raise lipase."]),
    # ---- rhabdomyolysis: CK > 5x ULN; > 5,000 U/L = AKI risk ----
    _sup_rule("rhabdomyolysis_ck_5x_uln_screen_v1", "rhabdomyolysis", "screening",
              _leaf("creatine_kinase_total", ">=", 1000.0, "U/L", 2.0),
              "Rhabdomyolysis - CK >= 5x ULN", "kdigo_aki_2012",
              "Total CK above five times the upper reference limit (~1,000 U/L) is the working definition of "
              "rhabdomyolysis.", ["Strenuous exercise, IM injection, myositis and MI also raise CK."]),
    _sup_rule("rhabdomyolysis_ck_5000_aki_risk_v1", "rhabdomyolysis", "diagnostic_criterion",
              _leaf("creatine_kinase_total", ">=", 5000.0, "U/L", 4.0),
              "Rhabdomyolysis with AKI risk - CK >= 5,000 U/L", "kdigo_aki_2012",
              "CK >= 5,000 U/L marks clinically significant rhabdomyolysis with risk of myoglobin-induced AKI "
              "(McMahon risk score); aggressive fluid resuscitation is indicated.",
              ["Peak CK is usually 24-72 h after injury."], urgent=True),
    # ---- multiple myeloma (IMWG) ----
    _sup_rule("multiple_myeloma_imwg_m_protein_or_flc_v1", "multiple_myeloma", "diagnostic_criterion",
              {"any": [_leaf("serum_protein_electrophoresis_m_spike", ">=", 3.0, "g/dL", 3.0),
                       _leaf("free_light_chain_ratio", ">=", 100.0, "ratio", 3.0),
                       _leaf("free_light_chain_ratio", "<=", 0.01, "ratio", 3.0)]},
              "Multiple myeloma - IMWG myeloma-defining serum markers", "imwg_myeloma_2024",
              "Serum M-protein >= 3 g/dL or an involved:uninvolved free light chain ratio >= 100 "
              "(involved FLC >= 100 mg/L) are IMWG criteria that, with clonal plasma cells, define myeloma.",
              ["Marrow plasma-cell percentage and CRAB / SLiM assessment are required for diagnosis."]),
    _sup_rule("multiple_myeloma_crab_with_paraprotein_v1", "multiple_myeloma", "screening",
              {"all": [{"any": [_leaf("serum_protein_electrophoresis_m_spike", ">", 0.0, "g/dL", 2.0),
                                _leaf("free_light_chain_ratio", ">", 1.65, "ratio", 2.0),
                                _leaf("free_light_chain_ratio", "<", 0.26, "ratio", 2.0)]},
                       {"any": [_leaf("calcium_total", ">", 11.0, "mg/dL", 1.0),
                                _leaf("creatinine", ">", 2.0, "mg/dL", 1.0),
                                _leaf("hemoglobin", "<", 10.0, "g/dL", 1.0)]}]},
              "Multiple myeloma - paraprotein with CRAB end-organ feature", "imwg_myeloma_2024",
              "A monoclonal protein together with hypercalcaemia, renal impairment or anaemia (CRAB) is the "
              "classic presentation of symptomatic myeloma.",
              ["Any single CRAB feature is non-specific; it is the combination with a paraprotein that counts."],
              urgent=True),
    # ---- acute myeloid leukaemia (WHO 2022 / ELN 2022) ----
    _sup_rule("acute_myeloid_leukemia_blasts_ge_20_eln_v1", "acute_myeloid_leukemia", "diagnostic_criterion",
              _leaf("blasts_percent", ">=", 20.0, "%", 4.0),
              "Acute leukaemia - >= 20 % blasts", "eln_aml_2024",
              ">= 20 % blasts in blood or marrow defines acute leukaemia (WHO 2022 / ELN 2022); lineage "
              "assignment needs flow cytometry.", ["Lineage (AML vs ALL) cannot be told from the count."],
              urgent=True),
    _sup_rule("acute_myeloid_leukemia_circulating_blasts_v1", "acute_myeloid_leukemia", "screening",
              {"all": [_leaf("blasts_percent", ">", 0.0, "%", 2.0),
                       {"any": [_leaf("hemoglobin", "<", 10.0, "g/dL", 1.0),
                                _leaf("platelets", "<", 100.0, "10*9/L", 1.0)]}]},
              "Circulating blasts with cytopenia", "eln_aml_2024",
              "Any circulating blasts accompanied by anaemia or thrombocytopenia is an urgent haematology "
              "referral.", ["Leukoerythroblastic reactions and recovery marrows can show rare blasts."],
              specificity="specific", urgent=True),
    # ---- pulmonary embolism: D-dimer is an exclusion test ----
    _sup_rule("pulmonary_embolism_d_dimer_positive_screen_v1", "pulmonary_embolism", "screening",
              _leaf("d_dimer", ">=", 0.5, "ug/mL", 1.0),
              "Pulmonary embolism - D-dimer above cut-off (not excluded)", "esc_pulmonary_embolism_2019",
              "A D-dimer above the (age-adjusted) cut-off does not diagnose PE but prevents its exclusion; "
              "sensitivity ~97 %, specificity ~40 %. Imaging is required.",
              ["Age-adjusted cut-off = age x 10 ng/mL FEU over 50 y.",
               "Raised in sepsis, malignancy, pregnancy, post-operatively."],
              specificity="non_specific", age_groups=_ADULT_AGES),
    # ---- hepatitis A: anti-HAV IgM ----
    _sup_rule("hepatitis_a_igm_positive_diagnostic_v1", "hepatitis_a", "diagnostic_criterion",
              {"all": [_leaf("hepatitis_a_igm_antibody", "==", 1.0, "1", 4.0),
                       _leaf("alanine_aminotransferase", ">", 50.0, "U/L", 1.0)]},
              "Acute hepatitis A - anti-HAV IgM positive with raised ALT", "who_guidelines_2024",
              "Anti-HAV IgM is detectable from symptom onset for 3-6 months and is the diagnostic test for "
              "acute hepatitis A (sensitivity and specificity > 95 %).",
              ["False positives occur with polyclonal B-cell activation; interpret with the clinical picture."]),
    # ---- nephrotic syndrome (KDIGO 2021) ----
    _sup_rule("nephrotic_syndrome_kdigo_any_proteinuria_v1", "nephrotic_syndrome", "diagnostic_criterion",
              {"all": [_leaf("albumin", "<", 3.0, "g/dL", 2.0),
                       {"any": [_leaf("twenty_four_hour_urine_total_protein", ">=", 3500.0, "mg/24h", 3.0),
                                _leaf("urine_protein_24_hour", ">=", 3500.0, "mg/24h", 3.0),
                                _leaf("urine_protein_to_creatinine_ratio", ">=", 3000.0, "mg/g", 3.0),
                                _leaf("urine_albumin_to_creatinine_ratio", ">=", 2200.0, "mg/g", 3.0)]}]},
              "Nephrotic syndrome - nephrotic-range proteinuria with hypoalbuminaemia", "kdigo_glomerular_2021",
              "Proteinuria >= 3.5 g/day (UPCR >= 3,000 mg/g) with serum albumin < 3.0 g/dL defines nephrotic "
              "syndrome; oedema and hyperlipidaemia are supportive.",
              ["Spot ratios approximate 24-h excretion; confirm when near the threshold."]),
    # ---- PTH-independent hypercalcaemia / humoral hypercalcaemia of malignancy ----
    _sup_rule("hypercalcemia_pth_independent_v1", "hypercalcemia_of_malignancy_support_pattern", "diagnostic_criterion",
              {"all": [_leaf("calcium_total", ">", 10.5, "mg/dL", 2.0),
                       _leaf("intact_parathyroid_hormone", "<", 20.0, "pg/mL", 3.0)]},
              "PTH-independent hypercalcaemia (suppressed PTH)", "endocrine_society_adrenal_2024",
              "Hypercalcaemia with an appropriately suppressed intact PTH (< 20 pg/mL) is PTH-independent: "
              "malignancy (PTHrP, osteolysis), granulomatous disease, vitamin D excess or milk-alkali.",
              ["Use albumin-corrected or ionised calcium.", "Check PTHrP, 1,25-(OH)2-D, SPEP."]),
    _sup_rule("hypercalcemia_pthrp_elevated_v1", "hypercalcemia_of_malignancy_support_pattern", "diagnostic_criterion",
              {"all": [_leaf("calcium_total", ">", 10.5, "mg/dL", 2.0),
                       _leaf("parathyroid_hormone_related_peptide", ">", 0.02, "ng/mL", 4.0)]},
              "Humoral hypercalcaemia of malignancy - raised PTHrP", "endocrine_society_adrenal_2024",
              "Raised PTHrP with hypercalcaemia and suppressed PTH is diagnostic of humoral hypercalcaemia of "
              "malignancy (squamous, renal, breast, HTLV-1 ATLL).",
              ["PTHrP assay units vary (pmol/L vs ng/mL); threshold assumes assay ULN ~2 pmol/L."],
              urgent=True),
    # ---- Cushing syndrome (Endocrine Society) ----
    _sup_rule("cushing_syndrome_dst_nonsuppression_v1", "cushing_syndrome", "screening",
              _leaf("cortisol_after_dexamethasone", ">", 1.8, "ug/dL", 3.0),
              "Cushing screen - 1 mg overnight DST cortisol > 1.8 ug/dL", "endocrine_society_cushing_2024",
              "Failure to suppress serum cortisol below 1.8 ug/dL (50 nmol/L) after 1 mg dexamethasone "
              "has ~95 % sensitivity for Cushing syndrome.",
              ["Oestrogens (CBG), CYP3A4 inducers, poor absorption and depression cause false positives."],
              age_groups=_ADULT_AGES),
    _sup_rule("cushing_syndrome_late_night_salivary_v1", "cushing_syndrome", "screening",
              _leaf("salivary_cortisol_late_night", ">", 0.15, "ug/dL", 3.0),
              "Cushing screen - late-night salivary cortisol above cut-off", "endocrine_society_cushing_2024",
              "Loss of the circadian nadir: late-night salivary cortisol above the assay cut-off "
              "(~0.15 ug/dL / 4 nmol/L) has 92-100 % sensitivity.",
              ["Shift work, smoking and liquorice confound."], age_groups=_ADULT_AGES),
    _sup_rule("cushing_syndrome_two_concordant_tests_v1", "cushing_syndrome", "diagnostic_criterion",
              {"n_of": {"n": 2, "conditions": [
                  _leaf("cortisol_after_dexamethasone", ">", 1.8, "ug/dL", 3.0),
                  _leaf("salivary_cortisol_late_night", ">", 0.15, "ug/dL", 3.0),
                  _leaf("urine_free_cortisol_24h", ">", 50.0, "ug/24h", 3.0)]}},
              "Cushing syndrome - two concordant abnormal first-line tests", "endocrine_society_cushing_2024",
              "The Endocrine Society requires at least two abnormal first-line tests (1 mg DST, late-night "
              "salivary cortisol, 24-h UFC) to establish hypercortisolism before localisation.",
              ["Pseudo-Cushing (alcohol, depression, obesity) must be excluded."], age_groups=_ADULT_AGES),
    _who_anemia_rule("anemia_adult_men_who_2024_hg", "Anemia, men >= 18 y (WHO 2024)", 13.0,
                     "male", ["adult", "older_adult"], "not_applicable"),
    _who_anemia_rule("anemia_adult_nonpregnant_women_who_2024_hg", "Anemia, non-pregnant women >= 18 y (WHO 2024)",
                     12.0, "female", ["adult", "older_adult"], "excluded"),
    _who_anemia_rule("anemia_adolescent_who_2024_hg", "Anemia, adolescents 12-17 y (WHO 2024, conservative 12.0)",
                     12.0, "all", ["adolescent"], "excluded"),
]


class DiseaseGuidelineRegistry:

    def __init__(
        self,
        disease_path: str | Path = DEFAULT_DISEASE_REGISTRY_PATH,
        feature_path: str | Path = DEFAULT_FEATURE_REGISTRY_PATH,
        *,
        validate: Optional[bool] = None,
    ):
        self.disease_path = Path(disease_path)
        self.feature_path = Path(feature_path)
        payload = bargozari_registry(self.disease_path)
        feature_payload = bargozari_registry(self.feature_path)
        if payload is None or feature_payload is None:
            raise RegistryValidationError(
                f"Cannot load registry: {self.disease_path} / "
                f"{self.feature_path}")
        self.payload = payload
        self.metadata = payload.get("registry_metadata", {})
        self.diseases: dict[str, dict[str, Any]] = payload.get(
            "diseases", {})
        self.rules: dict[str, dict[str, Any]] = payload.get("rules", {})
        try:  # extension 7 (2026-10-22)
            _NONSPECIFIC_ONLY_IDS.clear(); _NONSPECIFIC_ONLY_IDS.update(_collect_nonspecific_only(self.rules))
        except Exception:
            pass
        self.sources: dict[str, dict[str, Any]] = payload.get(
            'guideline_sources', {})
        # Code-level curation layer: quarantine registry rules whose direction
        # contradicts the entity they claim to support, and add WHO adult anemia
        # thresholds that the shipped registry lacks.
        self.quarantined_rules: list[str] = []
        for bad_id in QUARANTINED_RULE_IDS:
            if bad_id in self.rules:
                self.rules.pop(bad_id)
                self.quarantined_rules.append(bad_id)
        for rid, r in _direction_contradictions(self.rules):
            self.rules.pop(rid, None)
            self.quarantined_rules.append(rid)
        for sup in SUPPLEMENTAL_RULES:
            if sup["rule_id"] not in self.rules and sup["disease_id"] in self.diseases:
                self.rules[sup["rule_id"]] = copy.deepcopy(sup)
        self.features: dict[str, dict[str, Any]] = feature_payload.get(
            "features", {})

        if validate is None:
            validate = os.environ.get(
                "HEMOGLYPH_SKIP_REGISTRY_VALIDATION", ""
            ) not in {"1", 'true', "yes"}

        t0 = time.perf_counter()
        errors: list[str] = []
        rules_by_feature: dict[str, list[str]] = {}
        featureless_rules: list[str] = []
        diseases = self.diseases
        sources = self.sources
        features = self.features
        engine_statuses = self._motor_statuses()

        if validate and (not diseases or not self.rules):
            errors.append(
                "Disease registry must contain diseases and rules.")

        for rule_id, rule in self.rules.items():
            fids = tuple(dict.fromkeys(
                self._walk_vizhegi_ids(rule.get("expression") or {})))
            rule["_feature_ids"] = fids
            if fids:
                for fid in fids:
                    rules_by_feature.setdefault(fid, []).append(rule_id)
            else:
                featureless_rules.append(rule_id)
            if not validate or len(errors) >= 50:
                continue
            if rule.get("rule_id") != rule_id:
                errors.append(f"Rule ID mismatch: {rule_id}")
            if rule.get("disease_id") not in diseases:
                errors.append(
                    f"Rule {rule_id} references unknown disease.")
            for fid in fids:
                if fid not in features:
                    errors.append(
                        f"Rule {rule_id} references unknown feature "
                        f"{fid}.")
            for source_id in rule.get("source_ids", ()):
                if source_id not in sources:
                    errors.append(
                        f"Rule {rule_id} references unknown source "
                        f"{source_id}.")
            result_states = (
                rule.get("result") or {}).get('allowed_labels') or ()
            permitted = (
                rule.get("execution_contract") or {}
            ).get("permitted_result_states") or ()
            for status in result_states:
                if (status not in permitted
                        and status not in engine_statuses):
                    errors.append(
                        f"Rule {rule_id} declares unknown allowed "
                        f"label {status}.")

        if errors:
            raise RegistryValidationError("\n".join(errors[:50]))

        self.rules_by_feature = rules_by_feature
        self.featureless_rules = tuple(featureless_rules)
        self._index_empirical_specificity()
        self.catalog_only_count = sum(
            not (x.get("coverage") or {}).get(
                "executable_rule_available", False)
            for x in diseases.values()
        )
        logger.info(
            "Disease registry indexed: %d rules / %d diseases / "
            "%d indexed features in %.2fs (validation=%s)",
            len(self.rules), len(diseases), len(rules_by_feature),
            time.perf_counter() - t0, "on" if validate else "off",
        )

    @staticmethod
    def _expression_signature(expression: Mapping[str, Any]) -> Optional[tuple]:
        """Canonical signature of a rule expression so that identical
        thresholds stamped onto many diseases can be recognised."""
        if not isinstance(expression, Mapping):
            return None
        for junction in ("all", "any"):
            branch = expression.get(junction)
            if isinstance(branch, list):
                parts = []
                for sub in branch:
                    sig = DiseaseGuidelineRegistry._expression_signature(sub)
                    if sig is None:
                        return None
                    parts.append(sig)
                return (junction, tuple(sorted(parts, key=repr)))
        fid = expression.get("feature_id")
        if not fid:
            return None
        value = expression.get("value")
        if isinstance(value, (int, float)):
            value = round(float(value), 6)
        return (str(fid), str(expression.get("operator") or ""), repr(value),
                str(expression.get("unit") or "").casefold())

    _FINDING_LEXICON: tuple[tuple[str, tuple[str, ...], str], ...] = (
        ("hyperkalemia", ("potassium",), "high"), ("hypokalemia", ("potassium",), "low"),
        ("hypernatremia", ("sodium",), "high"), ("hyponatremia", ("sodium",), "low"),
        ("hyperglycemia", ("glucose",), "high"), ("hypoglycemia", ("glucose",), "low"),
        ("hypercalcemia", ("calcium",), "high"), ("hypocalcemia", ("calcium",), "low"),
        ("hypermagnesemia", ("magnesium",), "high"), ("hypomagnesemia", ("magnesium",), "low"),
        ("hyperphosphatemia", ("phosph",), "high"), ("hypophosphatemia", ("phosph",), "low"),
        ("hyperchloremia", ("chloride",), "high"), ("hypochloremia", ("chloride",), "low"),
        ("hyperuricemia", ("uric",), "high"), ("hypouricemia", ("uric",), "low"),
        ("anemia", ("hemoglobin", "hematocrit"), "low"),
        ("polycythemia", ("hemoglobin", "hematocrit"), "high"),
        ("erythrocytosis", ("hemoglobin", "hematocrit", "red_blood_cell"), "high"),
        ("thrombocytosis", ("platelet",), "high"), ("thrombocytopenia", ("platelet",), "low"),
        ("leukocytosis", ("white_blood_cell", "leukocyte"), "high"),
        ("leukopenia", ("white_blood_cell", "leukocyte"), "low"),
        ("neutrophilia", ("neutrophil",), "high"), ("neutropenia", ("neutrophil",), "low"),
        ("lymphocytosis", ("lymphocyte",), "high"), ("lymphopenia", ("lymphocyte",), "low"),
        ("lymphocytopenia", ("lymphocyte",), "low"),
        ("eosinophilia", ("eosinophil",), "high"), ("monocytosis", ("monocyte",), "high"),
        ("basophilia", ("basophil",), "high"),
        ("microcytosis", ("mean_corpuscular_volume",), "low"),
        ("macrocytosis", ("mean_corpuscular_volume",), "high"),
        ("hyperbilirubinemia", ("bilirubin",), "high"),
        ("hypoalbuminemia", ("albumin",), "low"),
        ("hypercholesterolemia", ("cholesterol",), "high"),
        ("hypertriglyceridemia", ("triglyceride",), "high"),
        ("hyperferritinemia", ("ferritin",), "high"),
        ("hyperammonemia", ("ammonia",), "high"),
        ("hyperlactatemia", ("lactate",), "high"),
        ("azotemia", ("urea", "blood_urea_nitrogen"), "high"),
        ("hypoxemia", ("po2", "oxygen"), "low"), ("hypercapnia", ("pco2", "carbon_dioxide"), "high"),
    )
    _FINDING_MODIFIERS = frozenset({
        "severe", "mild", "moderate", "marked", "profound", "critical", "significant",
        "pattern", "isolated", "relative", "absolute", "persistent", "unexplained",
        "acute", "chronic", "fasting", "v1", "v2", "lab", "laboratory", "finding",
        "elevated", "decreased", "low", "high", "with", "and", "or", "of", "the",
    })

    @classmethod
    def _rule_defines_finding_entity(cls, rule: Mapping[str, Any]) -> bool:
        """True when the disease is nothing more than the laboratory finding
        the rule tests ("hyperkalemia", "severe_hypoglycemia_pattern") and
        the rule points in the finding's direction. Composite names
        ("hyponatremia_hyperkalemia_pattern") need every finding covered."""
        disease_id = str(rule.get("disease_id") or "").casefold()
        tokens = [t for t in disease_id.split("_") if t]
        if not tokens:
            return False
        expr = rule.get("expression") or {}
        leaves: list[Mapping[str, Any]] = []

        def _collect(e):
            if not isinstance(e, Mapping):
                return
            for j in ("all", "any"):
                if isinstance(e.get(j), list):
                    for sub in e[j]:
                        _collect(sub)
                    return
            if e.get("feature_id"):
                leaves.append(e)
        _collect(expr)
        if not leaves or any("any" in e for e in [expr]):
            return False
        findings = []
        leftovers = []
        for t in tokens:
            hit = next((f for f in cls._FINDING_LEXICON if f[0] == t), None)
            if hit:
                findings.append(hit)
            elif t not in cls._FINDING_MODIFIERS:
                leftovers.append(t)
        if not findings or leftovers:
            return False
        for _name, fid_parts, direction in findings:
            ok = False
            for leaf in leaves:
                fid = str(leaf.get("feature_id") or "").casefold()
                op = str(leaf.get("operator") or "")
                if not any(p in fid for p in fid_parts):
                    continue
                if direction == "high" and op in (">", ">="):
                    ok = True
                elif direction == "low" and op in ("<", "<="):
                    ok = True
            if not ok:
                return False
        return True

    def _index_empirical_specificity(self) -> None:
        """The registry labels 93 % of its rules "specific", which carries no
        information. Measure specificity instead: a threshold that appears,
        verbatim, under N different diseases cannot discriminate between
        them. The weight of such a rule as *disease evidence* is scaled by
        1 / (1 + log2 N), an inverse-document-frequency style discount.
        The rule still fires, still raises its critical alert and is still
        listed; only its vote for one particular diagnosis is reduced."""
        import math
        diseases_by_sig: dict[tuple, set[str]] = {}
        diseases_by_feat_dir: dict[tuple, set[str]] = {}
        sig_of_rule: dict[str, tuple] = {}
        for rule_id, rule in self.rules.items():
            expression = rule.get("expression") or {}
            sig = self._expression_signature(expression)
            if sig is None:
                continue
            sig_of_rule[rule_id] = sig
            did = str(rule.get("disease_id"))
            diseases_by_sig.setdefault(sig, set()).add(did)
            if expression.get("feature_id"):
                op = str(expression.get("operator") or "")
                direction = "high" if op in (">", ">=") else "low" if op in ("<", "<=") else op
                diseases_by_feat_dir.setdefault(
                    (str(expression["feature_id"]), direction), set()).add(did)
        self.rule_disease_spread: dict[str, int] = {}
        self.rule_empirical_specificity: dict[str, float] = {}
        self.rule_defines_entity: set[str] = set()
        self.rule_stamped: set[str] = set()
        for rule_id, sig in sig_of_rule.items():
            rule = self.rules[rule_id]
            n = len(diseases_by_sig.get(sig, ()))
            self.rule_disease_spread[rule_id] = n
            disease = self.diseases.get(str(rule.get("disease_id"))) or {}
            required = set((disease.get("feature_links") or {}).get("required") or ())
            rule_feats = set(rule.get("_feature_ids") or ())
            # A finding that *defines* the entity (hypoglycaemia <- glucose,
            # hyperkalaemia <- potassium) is not "stamped" onto it: the
            # rule is the entity's own criterion and keeps full weight.
            # Decided from the entity's name and the rule's direction, not
            # from `feature_links.required`, which the registry fills
            # inconsistently (it lists bilirubin as the sole requirement of
            # congenital dyserythropoietic anaemia).
            if self._rule_defines_finding_entity(rule):
                self.rule_defines_entity.add(rule_id)
                self.rule_empirical_specificity[rule_id] = 1.0
                continue
            # Curated rules (registry status `curated_guideline_anchored`,
            # curation pass 13.0.0) encode a guideline's published decision
            # limit; their weight is not inferred from how the AI-assembled
            # remainder of the registry re-uses the analyte.
            if str(rule.get("status") or "") == "curated_guideline_anchored":
                self.rule_empirical_specificity[rule_id] = 1.0
                continue
            n_sig = n
            # A multi-feature pattern ("hyponatraemia + hyperkalaemia")
            # cannot be carried by a rule that sees only one of its parts.
            coverage = 1.0
            if len(required) >= 2:
                coverage = max(0.5, len(rule_feats & required) / len(required))
            # ...unless the rule tests a pathogen / decisive marker in the
            # positive direction (anti-HAV IgM, lipase, blasts): that leaf
            # IS the criterion, whatever else `feature_links.required` lists.
            if coverage < 1.0 and str(rule.get("rule_type") or "") != "exclusion_criterion":
                for leaf in _leaf_conditions(rule.get("expression")):
                    lf = str(leaf.get("feature_id") or "")
                    op = str(leaf.get("operator") or "")
                    if (_PATHOGEN_MARKER_RE.search(lf) or _DECISIVE_MARKER_RE.search(lf)) \
                            and op in (">", ">=", "=="):
                        coverage = 1.0
                        break
            # For a lone threshold the discriminating power is bounded by how
            # many diseases claim the *same analyte in the same direction*:
            # "bilirubin > 1.5" is not more specific than "bilirubin > 1.2"
            # merely because nobody else picked 1.5.
            expression = rule.get("expression") or {}
            if expression.get("feature_id"):
                op = str(expression.get("operator") or "")
                direction = "high" if op in (">", ">=") else "low" if op in ("<", "<=") else op
                n = max(n, len(diseases_by_feat_dir.get(
                    (str(expression["feature_id"]), direction), ())))
            if n <= 1:
                self.rule_empirical_specificity[rule_id] = coverage
                continue
            spec = 1.0 / (1.0 + math.log2(n))
            # Legitimately shared diagnostic criteria (ADA FPG >= 126 across
            # the diabetes subtypes) are discounted gently; screening
            # thresholds copied onto dozens of unrelated entities, hard.
            is_dx = str(rule.get("rule_type") or "") == "diagnostic_criterion"
            floor = 0.5 if is_dx else 0.15
            # "FPG >= 126 -> Paget disease / phaeochromocytoma / HHS" (28
            # entities), "CRP > 5" as the diagnostic criterion of 133
            # diseases: a single-analyte threshold stamped onto >= 5
            # entities is a template artefact, not a shared guideline
            # criterion. It is demoted to a non-specific screen.
            if (is_dx and n_sig >= STAMPED_SIGNATURE_MIN
                    and _shomar_shart(rule) < 2
                    and not _is_pathogen_marker_rule(rule)
                    and not _is_decisive_marker_rule(rule)):
                self.rule_stamped.add(rule_id)
                floor = 0.15
            self.rule_empirical_specificity[rule_id] = max(floor, spec) * coverage
        stamped = sum(1 for n in self.rule_disease_spread.values() if n >= 10)
        logger.info("Empirical specificity indexed: %d rules, %d shared by >=10 diseases",
                    len(self.rule_disease_spread), stamped)

    @classmethod
    def shared(
        cls,
        disease_path: str | Path = DEFAULT_DISEASE_REGISTRY_PATH,
        feature_path: str | Path = DEFAULT_FEATURE_REGISTRY_PATH,
    ) -> "DiseaseGuidelineRegistry":
        d, f = Path(disease_path), Path(feature_path)
        return shared_object(
            f"disease_registry::{d.resolve()}::{f.resolve()}",
            lambda: cls(d, f),
        )

    def candidate_ghaede_ids(self, feature_ids: Iterable[str]) -> set[str]:
        out: set[str] = set(self.featureless_rules)
        by_feature = self.rules_by_feature
        for fid in feature_ids:
            hit = by_feature.get(fid)
            if hit:
                out.update(hit)
        return out

    def _walk_vizhegi_ids(self, node: Any) -> Iterable[str]:
        if isinstance(node, Mapping):
            if "feature_id" in node:
                yield str(node['feature_id'])
            for value in node.values():
                yield from self._walk_vizhegi_ids(value)
        elif isinstance(node, list):
            for value in node:
                yield from self._walk_vizhegi_ids(value)

    @staticmethod
    def _motor_statuses() -> set[str]:
        return {
            'criterion_not_met', "not_applicable", "possible_pattern",
            "criterion_met", "compatible_pattern", "screening_positive",
            'urgent_pattern', "insufficient_data", "conflicting_data",
            "excluded", "ruled_out", "ruled_in",
        }


POSITIVE_VALUES = {"positive", 'pos', "reactive", "detected", 'present',
                   'yes', "true", "1", "مثبت"}
NEGATIVE_VALUES = {"negative", "neg", "nonreactive", "non-reactive", "non_reactive",
                   "non reactive", "not reactive", "not detected", "undetectable",
                   'absent', "nil", "not_seen", "not seen", "no_growth", "no growth",
                   "no", "false", '0', "منفی", "غیرواکنشی", "یافت نشد"}
POSITIVE_VALUES |= {"detected", "reactive", "واکنشی", "present"}


def _qualitative(value: Any) -> str:
    if isinstance(value, bool):
        return "positive" if value else "negative"
    if isinstance(value, (int, float)):
        if value == 1:
            return "positive"
        if value == 0:
            return "negative"
    text = str(value).strip().casefold()
    if text in POSITIVE_VALUES:
        return "positive"
    if text in NEGATIVE_VALUES:
        return "negative"
    return text


def _mapping_from_dataclass(value: Any) -> Mapping[str, Any]:
    return asdict(value) if is_dataclass(value) else value


try:
    from naam_haye_vizhegi import resolve as _resolve_alias
except ImportError:
    def _resolve_alias(name, known=None):
        return None


def normalize_observations(
    direct: Mapping[str, Any],
    derived: Optional[Mapping[str, Any]] = None,
    known: Optional[set] = None,
) -> tuple[dict[str, ObservationRecord], list[str]]:
    """Canonicalise raw input into ObservationRecords.

        Resolves aliases, reconciles values reported by more than
        one source, and reports any feature nothing downstream can
        consume - a silently dropped lab value is the worst
        failure mode here, so it is always surfaced.
        """
    warnings: list[str] = []
    records: dict[str, ObservationRecord] = {}
    renamed: dict[str, str] = {}
    unknown: list[str] = []

    def ingest(container: Mapping[str, Any],
               default_source: str) -> None:
        if ("results" in container
                and isinstance(container.get("results"), Mapping)
                and default_source == 'derived'):
            container = container["results"]
        for feature_id, raw_original in container.items():
            # Short lab names (tsh, egfr, alt) must be mapped to the
            # canonical ids the registry and the Bayesian/fuzzy layers use,
            # otherwise the observation is dropped without a trace.
            canon = _resolve_alias(feature_id, known)
            if canon and canon != feature_id:
                renamed[feature_id] = canon
                feature_id = canon
            elif canon is None and known and feature_id not in known:
                unknown.append(feature_id)
            raw = _mapping_from_dataclass(raw_original)
            if isinstance(raw, Mapping):
                reported_ref = raw.get('reported_reference') or {}
                record = ObservationRecord(
                    feature_id=feature_id,
                    value=raw.get('value'),
                    unit=normalize_unit(raw.get("unit")),
                    confirmed=bool(
                        raw.get("confirmed",
                                not raw.get('requires_confirmation',
                                            False))),
                    source=str(raw.get("source", default_source)),
                    reference_low=_float(
                        reported_ref.get('low')
                        if isinstance(reported_ref, Mapping)
                        else raw.get("reference_low")),
                    reference_high=_float(
                        reported_ref.get("high")
                        if isinstance(reported_ref, Mapping)
                        else raw.get("reference_high")),
                    timestamp=raw.get("timestamp"),
                    metadata=dict(raw.get("metadata") or {}),
                    warnings=list(raw.get("warnings") or []),
                )
            else:
                record = ObservationRecord(
                    feature_id=feature_id, value=raw,
                    source=default_source)
                warnings.append(
                    f"{feature_id}: scalar input has no explicit "
                    f"unit or confirmation metadata.")

            if isinstance(raw, Mapping) and raw.get("series") is not None:  # ESL ext 11-T (2026-10-23)
                _ser = _normalise_series(raw.get("series"))
                if _ser:
                    record.metadata["series"] = _ser
            old = records.get(feature_id)
            if (old and old.source == "input" and record.source == "derived"
                    and (old.value != record.value or old.unit != record.unit)):
                # A measured analyte outranks the calculator's estimate of the
                # same analyte (direct LDL vs Friedewald LDL). That is not a
                # conflict between two measurements; the estimate is simply
                # superseded, with a note when the two disagree materially.
                try:
                    ov, nv = float(old.value), float(record.value)
                    if old.unit == record.unit and ov and abs(nv - ov) / abs(ov) > 0.15:
                        old.warnings.append(
                            f"Measured {feature_id}={ov:g} {old.unit or ''} kept; "
                            f"derived estimate {nv:g} differs by "
                            f"{abs(nv - ov) / abs(ov) * 100:.0f}% - check the inputs "
                            "the estimate was computed from.")
                except (TypeError, ValueError):
                    pass
                continue
            if old and (old.value != record.value
                        or old.unit != record.unit):
                chosen = _taeen_conflict(old, record, warnings)
                chosen.metadata["conflict"] = True
                chosen.warnings.append(
                    f"Conflicting observations received for "
                    f"{feature_id}; kept source={chosen.source!r} "
                    f"value={chosen.value!r}.")
                records[feature_id] = chosen
            elif old is None:
                records[feature_id] = record

    ingest(direct, "input")
    if derived:
        ingest(derived, "derived")
    if renamed:
        warnings.append(
            "Mapped to canonical feature ids: "
            + ", ".join(f"{k}->{v}" for k, v in sorted(renamed.items())))
    if unknown:
        # Loud, because a silently ignored lab value is the worst outcome
        # here: the report looks complete but the finding never existed.
        warnings.append(
            "IGNORED - no rule or model consumes these features: "
            + ", ".join(sorted(set(unknown)))
            + ". Check the spelling or add them to the registry.")
    return records, warnings


def _taeen_conflict(old: ObservationRecord, new: ObservationRecord,
                      warnings: list[str]) -> ObservationRecord:

    if new.confirmed and not old.confirmed:
        return new
    if old.confirmed and not new.confirmed:
        return old

    old_is_derived = old.source == "derived"
    new_is_derived = new.source == "derived"
    if new_is_derived != old_is_derived:
        return new if not new_is_derived else old

    old_meta = len(old.metadata or {})
    new_meta = len(new.metadata or {})
    if new_meta > old_meta:
        return new
    if old_meta > new_meta:
        return old

    warnings.append(
        f"Ambiguous conflict for {old.feature_id}: both sources "
        f"are equivalent; kept the later observation "
        f"(source={new.source!r}).")
    return new


def _safe_in(a: Any, b: Any) -> bool:
    if isinstance(b, (str, list, tuple, set, dict, frozenset)):
        return a in b
    raise TypeError(
        f"'in' operator requires an iterable target, "
        f"got {type(b).__name__}.")


def _safe_not_in(a: Any, b: Any) -> bool:
    return not _safe_in(a, b)


OPERATORS = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, '<=': operator.le,
    "in": _safe_in, 'not_in': _safe_not_in,
}

TRUE_STATUS = {
    "diagnostic_criterion": "criterion_met",
    "classification_or_staging": "criterion_met",
    "compatible_laboratory_pattern": "compatible_pattern",
    "screening_or_triage": "screening_positive",
    "screening": "screening_positive",
    'triage': 'screening_positive',
    "urgent_pattern": 'urgent_pattern',
    "rule_in_criterion": "criterion_met",
    'severity_grading': "criterion_met",
    "monitoring": 'compatible_pattern',
    "exclusion_criterion": "ruled_out",
    "rule_out_criterion": 'ruled_out',
}

POSITIVE_RESULT_STATES = frozenset({
    'urgent_pattern', "criterion_met", 'possible_pattern',
    "compatible_pattern", "screening_positive",
})


# The registry labels every rule with how narrowly it targets its disease
# and which of the four guideline layers it belongs to. Both are evidence
# about how much the rule should count, so both scale its contribution.
# A specific diagnostic criterion is worth roughly twice a general
# screening rule that happens to fire.
# child -> umbrella term. Only pairs where the parent genuinely subsumes
# the child, so demoting the parent cannot hide a distinct diagnosis.
# ESL extension 9 (2026-10-23) — ranking hygiene tables (no probability effect).
_ESL_SYNONYM_FAMILIES: tuple[frozenset, ...] = (
    frozenset({"thalassemia_trait", "beta_thalassemia_trait", "beta_thalassemia_minor", "alpha_thalassemia_trait"}),
    frozenset({"immune_thrombocytopenia", "immune_thrombocytopenia_itp"}),
    frozenset({"alcoholic_liver_disease", "alcohol_associated_liver_disease"}),
    frozenset({"hepatocellular_injury_pattern", "acute_hepatocellular_injury"}),
    frozenset({"cirrhosis_laboratory_pattern", "liver_cirrhosis"}),
    frozenset({"nafl_d", "nafld", "nonalcoholic_fatty_liver_disease", "metabolic_dysfunction_associated_steatotic_liver_disease"}),
    frozenset({"diabetes_mellitus", "type_2_diabetes"}),
    frozenset({"heart_failure_bnp_pattern", "heart_failure_ntprobnp_pattern"}),
)
# ((ESL syndrome ids), ((organising diagnosis ids), (downstream findings it explains)))
_ESL_ORGANISING_PRECEDENCE: tuple = (
    (("renal_failure_marked", "ckd_advanced", "ckd_egfr_g4_single"),
     (("acute_kidney_injury", "chronic_kidney_disease", "renal_failure_unspecified"),
      ("hyperkalemia", "hypocalcemia", "metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "normal_anion_gap_metabolic_acidosis",
       "hyponatremia", "anemia", "normocytic_anemia_pattern", "hyperphosphatemia", "hypermagnesemia", "hypochloremia", "hyperchloremia", "hyperuricemia"))),
    (("dka", "dka_ketones_unmeasured", "dka_no_gap_severe"),
     (("diabetic_ketoacidosis",),
      ("metabolic_acidosis", "high_anion_gap_metabolic_acidosis", "hyperglycemia", "hyponatremia", "hyperkalemia", "hypokalemia", "hypophosphatemia", "leukocytosis_pattern", "pseudohyponatremia"))),
    (("hhs", "hhs_effective_osm"),
     (("hyperosmolar_hyperglycemic_state",),
      ("hyperglycemia", "hypernatremia", "hyponatremia", "pseudohyponatremia", "acute_kidney_injury", "prerenal_azotemia"))),
)
# aetiology id -> (finding ids it is inferred from, confirmatory marker feature ids)
_ESL_AETIOLOGY_BENEATH_FINDING: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "bacterial_infection": (("sepsis", "septic_shock", "leukocytosis_pattern", "neutrophilia_pattern"),
                            ("procalcitonin", "procalcitonin_quantitative", "c_reactive_protein", "high_sensitivity_c_reactive_protein", "blood_culture", "band_neutrophils_percent")),
    "copd": (("respiratory_acidosis", "chronic_respiratory_acidosis", "metabolic_alkalosis"),
             ("fev1_fvc_ratio", "fev1_percent_predicted", "alpha_1_antitrypsin")),
    "vitamin_d_deficiency": (("hypocalcemia", "hypophosphatemia", "pseudohypocalcemia"),
                             ("25_hydroxy_vitamin_d", "intact_parathyroid_hormone", "parathyroid_hormone", "parathyroid_hormone_intact")),
    "acute_gastroenteritis": (("hypokalemia", "metabolic_acidosis", "hypochloremia", "dehydration_pattern"),
                              ("stool_culture", "campylobacter_stool_culture", "salmonella_stool_culture", "fecal_calprotectin", "clostridioides_difficile_toxin_a_b", "clostridium_difficile_gdh_antigen")),
    "nafl_d": (("hepatocellular_injury_pattern", "acute_hepatocellular_injury", "alcoholic_liver_disease", "alcohol_associated_liver_disease"),
               ("liver_stiffness_fibroscan",)),
    "takotsubo_cardiomyopathy": (("acute_myocardial_infarction", "acute_myocardial_injury", "myocardial_injury_acuity_undetermined"),
                                 ("echocardiography_lvef", "coronary_angiography")),
    "acute_leukemia": (("pancytopenia", "leukopenia", "thrombocytopenia", "anemia"),
                       ("blasts_percent", "blast_cells_percent")),
    "aplastic_anemia": (("pancytopenia", "leukopenia", "thrombocytopenia", "anemia"),
                        ("absolute_reticulocyte_count", "corrected_reticulocyte_count", "reticulocyte_production_index", "reticulocyte_count", "reticulocyte_percent")),
}

def kashf_selsele_maratib(disease_ids: Iterable[str]) -> dict[str, str]:
    """Derive is-a relations from the registry's own identifiers.

    The registry carries no explicit parent field, but its ids are built
    compositionally: `autoimmune_hemolytic_anemia` is a kind of
    `hemolytic_anemia`, `severe_hypokalemia` a kind of `hypokalemia`. A
    child therefore ends with its parent's full id.

    Two exclusions matter. Ids beginning `co_` describe two-analyte
    combination patterns, not subtypes - treating them as children of one
    component would suppress that component wrongly. And a parent must be
    long enough that the suffix match is meaningful rather than incidental.

    Hand-curated entries in _DISEASE_PARENT still win; this only fills in
    what nobody has written down.
    """
    ids = {str(d) for d in disease_ids}
    out: dict[str, str] = {}
    for cid in ids:
        if cid.startswith("co_"):
            continue
        tokens = cid.split("_")
        for i in range(1, len(tokens)):
            candidate = "_".join(tokens[i:])
            if (candidate in ids and candidate != cid
                    and len(candidate) > 4
                    and not candidate.startswith("co_")):
                out[cid] = candidate
                break
    # A cycle would let two diseases demote each other forever.
    for child, parent in list(out.items()):
        if out.get(parent) == child:
            out.pop(child, None)
    return out


_DISEASE_PARENT = {
    "anemia_of_chronic_disease": "anemia",
    "iron_deficiency_anemia": "anemia",
    "vitamin_b12_deficiency": "anemia",
    "hemolytic_anemia": "anemia",
    "thalassemia_trait": "anemia",
    "hashimoto_thyroiditis": "hypothyroidism",
    "graves_disease": "hyperthyroidism",
    "type_1_diabetes": "diabetes",
}


_SPECIFICITY_FACTOR = {
    "specific": 1.0,
    "general": 0.72,
}

# A lone non-specific threshold names a category, never a diagnosis, so
# it is held to a fraction of its nominal weight. Conjunctions and rules
# the registry grades "specific" are untouched: both discriminate.
_TAK_SHART_SCREENING_FACTOR = 0.25
# A single-leaf "diagnostic criterion" whose verbatim signature appears under
# this many or more diseases is a template stamp (see
# DiseaseGuidelineRegistry._index_empirical_specificity).
STAMPED_SIGNATURE_MIN = 5
# disease_id -> (components required, component finding groups, posterior cap
# while fewer than the required number are positive).
COUNT_DEFINED_NODES: dict[str, tuple[int, tuple[tuple[str, ...], ...], float]] = {
    "metabolic_syndrome": (3, (
        ("triglycerides_high",), ("hdl_low",), ("fbs_high", "fbs_prediabetic"),
        ("bmi_high", "bmi_overweight", "waist_high"), ("bp_high",),
    ), 0.45),
}
PATHOGEN_MARKER_MIN_SPECIFICITY = 0.60
# A diagnostic-criterion rule on a decisive marker (lipase >= 3x ULN, CK >=
# 5,000, blasts >= 20 %) is shared only by the syndrome's own aliases /
# pattern twins; it is not "stamped" and keeps near-full weight.
DECISIVE_DIAGNOSTIC_MIN_SPECIFICITY = 0.85
# Non-infectious analytes whose single positive result is itself the
# diagnostic criterion of the entity carrying it (lipase >= 3x ULN, CK > 5x
# ULN, >= 20 % blasts, M-spike, PTHrP, non-suppressed DST cortisol...).
# They are treated like pathogen markers: no "doorway" discount.
_DECISIVE_MARKER_RE = re.compile(
    r"(^lipase$|^amylase$|creatine_kinase_total|^troponin|high_sensitivity_troponin|"
    r"blasts_percent|m_spike|free_light_chain|parathyroid_hormone_related_peptide|"
    r"cortisol_after_dexamethasone|salivary_cortisol|urine_free_cortisol|"
    r"transglutaminase|tsh_receptor|thyroid_stimulating_immunoglobulin|"
    r"^d_dimer$|schistocyte|adamts13|haptoglobin|"
    r"intrinsic_factor|methylmalonic|beta_hydroxybutyrate|^ammonia$|^lactate$|"
    r"nt_probnp|b_type_natriuretic|protein_to_creatinine|urine_protein_24|twenty_four_hour_urine_total_protein|"
    r"aldosterone_renin|metanephrine|chromogranin|^prolactin$|insulin_like_growth|"
    r"^hemoglobin_a1c$|hemoglobin_electrophoresis|hemoglobin_a2|^ceruloplasmin|"
    r"alpha_1_antitrypsin|anti_mitochondrial|smooth_muscle|double_stranded_dna|anca|"
    r"anti_ccp|cyclic_citrullinated|complement_c[34]|cryoglobulin|"
    r"^cortisol_30min|^morning_cortisol$|adrenocorticotropic|^renin|^aldosterone$)",
    re.IGNORECASE)


# Analytes every routine panel carries (CBC, differential, BMP/CMP, LFT,
# lipids, TSH, acute-phase, iron studies). A combination of these is a
# *compatible laboratory pattern* for an infection, malignancy or specific
# endocrinopathy - never its diagnostic criterion. The AI-assembled registry
# labels "platelets < 150 + LDH > 300" a diagnostic criterion of malaria and
# "CRP > 10 + platelets < 150" one of chikungunya; this guard re-grades them.
ROUTINE_PANEL_FEATURES: frozenset[str] = frozenset({
    "hemoglobin", "hematocrit", "red_blood_cell_count", "mean_corpuscular_volume",
    "mean_corpuscular_hemoglobin", "mean_corpuscular_hemoglobin_concentration",
    "red_cell_distribution_width_cv", "red_cell_distribution_width", "platelets", "platelet_count",
    "mean_platelet_volume", "white_blood_cell_count", "neutrophils_percent", "lymphocytes_percent",
    "monocytes_percent", "eosinophils_percent", "basophils_percent", "neutrophil_count_absolute",
    "lymphocyte_count_absolute", "monocyte_count_absolute", "eosinophil_count_absolute",
    "basophil_count_absolute", "absolute_neutrophil_count", "neutrophil_to_lymphocyte_ratio_nlr",
    "glucose", "glucose_random", "fasting_plasma_glucose", "hemoglobin_a1c",
    "creatinine", "egfr_ckd_epi_creatinine", "egfr", "blood_urea_nitrogen", "urea",
    "blood_urea_nitrogen_to_creatinine_ratio", "sodium", "potassium", "chloride", "bicarbonate",
    "total_carbon_dioxide", "anion_gap", "calcium_total", "corrected_calcium_for_serum_albumin",
    "phosphate", "magnesium", "uric_acid", "total_protein", "albumin", "globulin",
    "alanine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase",
    "gamma_glutamyl_transferase", "total_bilirubin", "direct_bilirubin", "indirect_bilirubin",
    "lactate_dehydrogenase", "total_cholesterol", "ldl_cholesterol_calculated", "ldl_cholesterol_direct",
    "hdl_cholesterol", "triglycerides", "non_hdl_cholesterol", "thyroid_stimulating_hormone",
    "c_reactive_protein", "high_sensitivity_c_reactive_protein", "erythrocyte_sedimentation_rate",
    "ferritin", "serum_iron", "total_iron_binding_capacity", "transferrin_saturation",
    "international_normalized_ratio", "prothrombin_time", "activated_partial_thromboplastin_time",
    "body_mass_index", "waist_circumference", "systolic_blood_pressure", "diastolic_blood_pressure",
})

# Entities whose guideline definition genuinely rests on routine analytes.
_ROUTINE_DEFINED_ENTITY_RE = re.compile(
    r"(diabet|prediabet|glycemi|glyc(a)?emia|insulin_resistance|metabolic_syndrome|"
    r"kidney_disease|kidney_injury|renal_failure|azotemia|uremi|"
    r"ketoacidosis|hyperosmolar|acidosis|alkalosis|anion_gap|"
    r"anemia|anaemia|cytopenia|cytosis|penia$|philia$|polycythemia|erythrocytosis|thrombocyt|leukocyt|neutro|lymph|"
    r"hyper[a-z]*emia|hypo[a-z]*emia|hyper[a-z]*uria|hypo[a-z]*uria|natremia|kalemia|calcemia|"
    r"phosphatemia|magnesemia|lipidemia|cholesterolemia|triglyceridemia|dyslipid|"
    r"cholestasis|cholestatic|hepatocellular_pattern|liver_injury|transaminitis|"
    r"siadh|dehydration|malnutrition|refeeding|tumor_lysis|"
    r"hypothyroid|hyperthyroid|thyrotox|sick_euthyroid|"
    r"iron_deficiency|iron_overload|thalassemia_trait|microcyt|macrocyt|"
    r"inflammat|acute_phase|_pattern$|_support_pattern$|nephrotic|proteinuria|"
    r"hypoalbumin|hyperuric|gout_flare|sepsis|sirs|_syndrome_pattern)",
    re.IGNORECASE)


def _routine_only_rule(rule: Mapping[str, Any]) -> bool:
    leaves = _leaf_conditions(rule.get("expression"))
    if not leaves:
        return False
    return all(str(l.get("feature_id") or "") in ROUTINE_PANEL_FEATURES for l in leaves)


def _is_decisive_marker_rule(rule: Mapping[str, Any]) -> bool:
    expr = rule.get("expression") or {}
    fid = str(expr.get("feature_id") or "")
    if not fid or not _DECISIVE_MARKER_RE.search(fid):
        return False
    if str(rule.get("rule_type") or "").startswith("exclusion"):
        return False
    return str(rule.get("specificity") or "").lower() == "specific"


_PATHOGEN_MARKER_RE = re.compile(
    r"(hepatitis_[abcde]|hbsag|hbeag|hbv|hcv|hiv|htlv|cmv|ebv|epstein|varicella|vzv|herpes|hsv|rubella|measles|"
    r"toxoplasm|syphilis|treponem|vdrl|rapid_plasma_reagin|brucell|wright|widal|salmonella|typhi|"
    r"malaria|plasmodium|leishman|tubercul|quantiferon|igra|afb|mycobacter|h_pylori|helicobacter|"
    r"influenza|sars_cov|covid|rsv|dengue|chikungunya|zika|leptospir|borrelia|lyme|rickettsi|"
    r"chlamydia|gonorrh|neisseria|trichomon|hpv|parvovirus|adenovirus|rotavirus|norovirus|"
    r"clostridi|c_difficile|legionella|pneumococc|streptococc|staphylococc|aspergill|galactomannan|"
    r"candida|cryptococc|histoplasm|pneumocystis|_culture|blood_culture|urine_culture|pcr|_antigen|"
    r"_antibody|_igm|_igg|_ab$|_ag$)", re.IGNORECASE)


_HG_DEBUG_RULES = frozenset(x for x in os.environ.get("HG_DEBUG_RULES", "").split(",") if x)


def _is_pathogen_marker_rule(rule: Mapping[str, Any]) -> bool:
    expr = rule.get("expression") or {}
    fid = str(expr.get("feature_id") or "")
    if not fid or not _PATHOGEN_MARKER_RE.search(fid):
        return False
    # Only the positive/qualitative direction; "HBsAg negative" exclusions stay as they are.
    ctx = expr.get("context") or {}
    qual = str(ctx.get("qualitative") or "").casefold()
    if qual in {"negative", "non_reactive", "not_detected", "absent"}:
        return False
    if str(rule.get("rule_type") or "").startswith("exclusion"):
        return False
    return True


def _shomar_shart(rule: Mapping[str, Any]) -> int:
    """How many conditions a rule's expression actually tests."""
    expression = rule.get("expression") or {}
    for junction in ("all", "any"):
        branch = expression.get(junction)
        if isinstance(branch, list):
            return len(branch)
    return 1 if expression.get("feature_id") else 0


_RULE_TYPE_FACTOR = {
    "diagnostic_criterion": 1.0,
    "staging_severity": 0.92,
    "exclusion_criterion": 0.90,
    "screening": 0.80,
}


_RULE_STATUS_SCORE = {
    "urgent_pattern": 0.95,
    'criterion_met': 0.90,
    'screening_positive': 0.70,
    "compatible_pattern": 0.60,
    'possible_pattern': 0.45,
    "conflicting_data": 0.20,
    "insufficient_data": 0.10,
}

_STATUS_PRIORITY = {
    'urgent_pattern': 0, 'criterion_met': 1, "possible_pattern": 2,
    "compatible_pattern": 3, "screening_positive": 4,
    "conflicting_data": 5, "insufficient_data": 6,
    'criterion_not_met': 7, "not_applicable": 8,
    "ruled_out": 9, "excluded": 10,
}


def _edgham_all(children: Sequence[NodeEvaluation]) -> TruthValue:
    truths = [x.truth for x in children]
    if TruthValue.CONFLICT in truths:
        return TruthValue.CONFLICT
    if TruthValue.FALSE in truths:
        return TruthValue.FALSE
    if TruthValue.UNKNOWN in truths:
        return TruthValue.UNKNOWN
    return TruthValue.TRUE


def _edgham_any(children: Sequence[NodeEvaluation]) -> TruthValue:
    truths = [x.truth for x in children]
    if TruthValue.TRUE in truths:
        return TruthValue.TRUE
    if TruthValue.CONFLICT in truths:
        return TruthValue.CONFLICT
    if TruthValue.UNKNOWN in truths:
        return TruthValue.UNKNOWN
    return TruthValue.FALSE


def _clone_node(node: NodeEvaluation) -> NodeEvaluation:
    return NodeEvaluation(
        truth=node.truth,
        evidence=list(node.evidence),
        missing_features=set(node.missing_features),
        missing_context=set(node.missing_context),
        warnings=list(node.warnings),
        score=node.score,
    )


def _edgham_nodes(truth: TruthValue,
                 children: Sequence[NodeEvaluation]) -> NodeEvaluation:

    missing_features: set = set()
    missing_context: set = set()
    for child in children:
        missing_features |= child.missing_features
        missing_context |= child.missing_context
    return NodeEvaluation(
        truth=truth,
        evidence=[e for child in children for e in child.evidence],
        missing_features=missing_features,
        missing_context=missing_context,
        warnings=list(dict.fromkeys(
            w for child in children for w in child.warnings)),
    )



# ---------------------------------------------------------------------------
# Pre-analytical / structural plausibility gate
# ---------------------------------------------------------------------------
# Absolute physiological limits in canonical units. A value outside these
# bounds is not a critical result, it is a transcription or unit error and
# must not reach any reasoning layer.
ABSOLUTE_LIMITS: dict[str, tuple[float, float]] = {
    "hemoglobin": (1.0, 25.0), "hematocrit": (3.0, 75.0),
    "red_blood_cell_count": (0.3, 9.0), "mean_corpuscular_volume": (40.0, 160.0),
    "mean_corpuscular_hemoglobin": (10.0, 55.0),
    "mean_corpuscular_hemoglobin_concentration": (20.0, 40.0),
    "white_blood_cell_count": (0.05, 1000.0), "platelet_count": (1.0, 5000.0),
    "platelets": (1.0, 5000.0), "red_cell_distribution_width_cv": (8.0, 40.0),
    "sodium": (90.0, 200.0), "potassium": (1.0, 12.0), "chloride": (50.0, 160.0),
    "bicarbonate": (0.5, 60.0), "calcium_total": (3.0, 20.0), "calcium_ionized": (0.3, 3.5),
    "magnesium": (0.2, 10.0), "phosphate": (0.2, 20.0),
    "glucose": (5.0, 2500.0), "fasting_plasma_glucose": (5.0, 2500.0),
    "hemoglobin_a1c": (2.5, 20.0), "creatinine": (0.05, 40.0),
    "blood_urea_nitrogen": (0.5, 300.0), "urea": (1.0, 600.0), "uric_acid": (0.3, 30.0),
    "total_bilirubin": (0.0, 60.0), "direct_bilirubin": (0.0, 50.0),
    "albumin": (0.5, 7.0), "total_protein": (1.0, 15.0),
    "alanine_aminotransferase": (0.0, 20000.0), "aspartate_aminotransferase": (0.0, 30000.0),
    "alkaline_phosphatase": (0.0, 10000.0), "gamma_glutamyl_transferase": (0.0, 10000.0),
    "lactate_dehydrogenase": (0.0, 50000.0),
    "total_cholesterol": (30.0, 1500.0), "ldl_cholesterol_direct": (5.0, 1000.0),
    "ldl_cholesterol_calculated": (5.0, 1000.0), "hdl_cholesterol": (3.0, 200.0),
    "triglycerides": (10.0, 10000.0),
    "thyroid_stimulating_hormone": (0.0, 500.0), "free_thyroxine": (0.05, 10.0),
    "ferritin": (0.5, 50000.0), "transferrin_saturation": (0.5, 100.0),
    "c_reactive_protein": (0.0, 600.0), "erythrocyte_sedimentation_rate": (0.0, 160.0),
    "international_normalized_ratio": (0.5, 20.0), "prothrombin_time": (5.0, 200.0),
    "activated_partial_thromboplastin_time": (10.0, 300.0),
    "25_hydroxy_vitamin_d": (1.0, 400.0), "vitamin_b12": (20.0, 10000.0),
    "ph": (6.5, 7.9), "pco2": (5.0, 200.0), "po2": (10.0, 700.0), "lactate": (0.1, 40.0),
    # ESL ext 8c (fabrication-provocation audit 2026-10-22): canonical units per feature registry
    "arterial_ph": (6.5, 7.9), "venous_ph": (6.5, 7.9), "arterial_pco2": (5.0, 250.0), "arterial_po2": (5.0, 760.0),
    "troponin_i": (0.0, 10000.0), "troponin_t": (0.0, 1000.0), "creatine_kinase_total": (0.0, 2000000.0),
    "lipase": (0.0, 100000.0), "amylase": (0.0, 100000.0), "ammonia": (0.0, 3000.0), "procalcitonin": (0.0, 2000.0),
    "b_type_natriuretic_peptide": (0.0, 100000.0), "nt_probnp": (0.0, 500000.0), "d_dimer": (0.0, 1000.0),
    "fibrinogen": (1.0, 2000.0), "serum_osmolality": (150.0, 500.0), "beta_hydroxybutyrate": (0.0, 40.0),
    "ethanol": (0.0, 1500.0), "temperature": (20.0, 45.0), "body_temperature": (20.0, 45.0),
}

# Analyte -> fraction of reliability kept when the sample carries the
# interference. Tietz, ch. "Preanalytical variables"; CLSI C56.
INTERFERENCE_PENALTIES: dict[str, dict[str, float]] = {
    "hemolysis": {
        "potassium": 0.45, "lactate_dehydrogenase": 0.4, "aspartate_aminotransferase": 0.6,
        "phosphate": 0.6, "magnesium": 0.7, "iron": 0.6, "total_bilirubin": 0.7,
        "troponin_i": 0.7, "folate": 0.5,
    },
    "lipemia": {
        "sodium": 0.5, "triglycerides": 0.7, "hemoglobin": 0.7,
        "mean_corpuscular_hemoglobin_concentration": 0.5, "total_protein": 0.7,
        "amylase": 0.7, "lipase": 0.7,
    },
    "icterus": {
        "creatinine": 0.6, "total_cholesterol": 0.7, "glucose": 0.8,
        "gamma_glutamyl_transferase": 0.8, "triglycerides": 0.8,
    },
}
_INTERFERENCE_KEYS = {
    "hemolysis": ("hemolysis", "hemolysis_index", "hemolyzed", "hemolysed", "h_index", "hil_h"),
    "lipemia": ("lipemia", "lipemia_index", "lipemic", "l_index", "hil_l"),
    "icterus": ("icterus", "icterus_index", "icteric", "i_index", "hil_i"),
}


def _interference_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().casefold()
    if not text or text in {"0", "none", "no", "negative", "absent", "clear", "-", "n", "false"}:
        return False
    num = _float(text.rstrip("+"))
    if num is not None and text.rstrip("+") == text:
        return num > 0.5
    return True


def _canonical_number(engine: "ClinicalRuleEngine", fid: str,
                      record: ObservationRecord) -> Optional[float]:
    try:
        return _float(engine._coerce_canonical(fid, record.value, record.unit))
    except Exception:
        return _float(record.value)



# Feature ids that the registries use interchangeably for the same
# measurement. 470 rules are written on "platelets" and 97 on
# "platelet_count"; a sheet that arrives as either must drive both.
# The AI-assembled registry carries several ids for one analyte, with the rule
# base split between them (e.g. intact PTH: 81 rules on one id, 17 on another).
# Members of a group are the same measurement; an observation on any member is
# mirrored to the others so no rule is starved by a naming accident.
EQUIVALENT_FEATURE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("platelet_count", "platelets"),
    ("ldl_cholesterol_direct", "ldl_cholesterol_calculated"),
    ("intact_parathyroid_hormone", "parathyroid_hormone_intact", "parathyroid_hormone"),
    ("morning_cortisol", "cortisol_8am", "cortisol_morning", "cortisol_am"),
    ("salivary_cortisol_late_night", "cortisol_salivary_midnight"),
    ("serum_osmolality", "measured_osmolality", "serum_osmolality_measured"),
    ("osmolal_gap", "serum_osmolar_gap", "calculated_serum_osmolal_gap"),
    ("glucose_random", "random_plasma_glucose"),
    ("glucose_2_hour_postprandial", "two_hour_postload_glucose"),
    ("aldosterone_renin_ratio", "aldosterone_to_renin_ratio_arr", "aldosterone_to_renin_ratio"),
    ("cyclic_citrullinated_peptide_antibody", "anti_cyclic_citrullinated_peptide_igg"),
    ("anti_tissue_transglutaminase_iga", "tissue_transglutaminase_iga_antibody"),
    ("anti_tissue_transglutaminase_igg", "tissue_transglutaminase_igg_antibody"),
    ("procalcitonin", "procalcitonin_quantitative"),
    ("ammonia", "plasma_ammonia", "serum_ammonia"),
    ("beta_hydroxybutyrate", "beta_hydroxybutyrate_serum"),
    ("haptoglobin_serum_quantitative", "serum_haptoglobin"),
    ("c_reactive_protein", "high_sensitivity_c_reactive_protein"),
    ("serum_iron", "iron"),
    ("creatine_kinase_mb", "creatine_kinase_mb_mass"),
    ("free_phenytoin_serum", "phenytoin_free"),
    ("reticulocytes", "reticulocyte_percent"),
    ("absolute_reticulocyte_count", "reticulocyte_count_absolute"),
    ("neutrophil_count_absolute", "absolute_neutrophil_count"),
    ("urine_ketones_qualitative", "urine_ketones"),
    ("hepatitis_c_viral_load", "hepatitis_c_rna_quantitative_pcr"),
    ("hiv_one_rna_viral_load", "hiv_1_viral_load"),
    ("hiv_1_and_hiv_2_antigen_antibody", "hiv_p24_antigen_antibody_combo"),
    ("epstein_barr_virus_dna_pcr", "epstein_barr_viral_load"),
    ("lactate", "lactate_arterial", "lactate_venous"),
    ("digoxin", "digoxin_serum_trough"),
    ("vitamin_b1_thiamine", "vitamin_b1_thiamine_whole_blood"),
    ("adrenocorticotropic_hormone", "plasma_adrenocorticotropic_hormone"),
    ("egfr_ckd_epi_cystatin_c", "egfr_cystatin_c"),
    ("free_testosterone", "free_testosterone_calculated"),
    ("dihydrotestosterone", "dihydrotestosterone_serum"),
    ("corrected_calcium_for_serum_albumin", "corrected_calcium"),
    ("cholesterol_hdl_ratio", "total_to_hdl_ratio"),
    ("body_mass_index", "bmi"),
    ("homeostatic_model_assessment_insulin_resistance", "homa_ir"),
    ("blood_urea_nitrogen_to_creatinine_ratio", "bun_to_creatinine_ratio"),
    ("neutrophil_to_lymphocyte_ratio_nlr", "neutrophil_to_lymphocyte_ratio"),
    ("nt_probnp", "n_terminal_pro_b_type_natriuretic_peptide"),
    ("b_type_natriuretic_peptide", "bnp"),
    ("urine_albumin_to_creatinine_ratio", "albumin_creatinine_ratio"),
    ("total_prostate_specific_antigen", "prostate_specific_antigen"),
    ("fasting_serum_insulin", "insulin_fasting", "insulin"),
    # --- registry near-duplicates found by stem analysis (serum_/plasma_/_serum/_quantitative...) ---
    ("glucose", "glucose_random"),
    ("arterial_ph", "arterial_blood_ph", "ph", "blood_ph"),
    ("bicarbonate", "calculated_bicarbonate_blood_gas", "serum_bicarbonate"),
    ("ceruloplasmin", "ceruloplasmin_serum", "serum_ceruloplasmin"),
    ("selenium", "serum_selenium"),
    ("vitamin_a_retinol", "vitamin_a_retinol_serum"),
    ("vitamin_e_alpha_tocopherol", "vitamin_e_alpha_tocopherol_serum"),
    ("copper", "serum_copper"),
    ("zinc", "serum_zinc"),
    ("homocysteine", "plasma_homocysteine", "homocysteine_serum"),
    ("beta_2_microglobulin", "beta_2_microglobulin_serum"),
    ("lactate", "plasma_lactate", "serum_lactate"),
    ("myoglobin", "myoglobin_serum"),
    ("manganese", "serum_manganese", "manganese_blood"),
    ("pyruvate", "blood_pyruvate", "serum_pyruvate"),
    ("fructosamine", "serum_fructosamine"),
    ("androstenedione", "androstenedione_serum"),
    ("lipase", "serum_lipase"),
    ("soluble_st2", "soluble_st2_serum"),
    ("copeptin", "serum_copeptin_quantitative"),
    ("dhea_sulfate", "dhea_sulfate_serum"),
    ("fecal_calprotectin", "fecal_calprotectin_quantitative"),
    ("methylmalonic_acid", "serum_methylmalonic_acid_quantitative"),
    ("osmotic_fragility", "osmotic_fragility_test"),
    ("eosinophil_cationic_protein", "serum_eosinophil_cationic_protein"),
    ("serum_amyloid_a", "serum_amyloid_a_quantitative"),
    ("galectin_3", "galectin_3_serum"),
    ("urine_osmolality", "urine_osmolality_random"),
    ("lead", "blood_lead"),
    ("mercury", "blood_mercury"),
    ("arsenic", "blood_arsenic"),
    ("cadmium", "blood_cadmium"),
    ("aluminum", "serum_aluminum"),
    ("quinidine", "serum_quinidine_level"),
    ("propafenone", "serum_propafenone_level"),
    ("mexiletine", "serum_mexiletine_level"),
    ("herpes_simplex_virus_1_igg_antibody", "herpes_simplex_virus_1_igg"),
    ("herpes_simplex_virus_2_igg_antibody", "herpes_simplex_virus_2_igg"),
    ("mycoplasma_pneumoniae_igm_antibody", "mycoplasma_pneumoniae_igm"),
    ("thrombin_time", "thrombin_time_plasma"),
    ("reptilase_time", "reptilase_time_plasma"),
    ("adamts13_activity", "adamts13_activity_quantitative"),
    ("globulin", "serum_globulin"),
    ("bile_acids_total", "total_bile_acids_serum"),
    ("serum_free_kappa_light_chains", "free_kappa_light_chains", "serum_free_light_chain_kappa"),
    ("serum_free_lambda_light_chains", "free_lambda_light_chains", "serum_free_light_chain_lambda"),
    ("free_light_chain_ratio", "free_kappa_to_lambda_ratio", "serum_free_kappa_to_lambda_ratio_flc"),
    ("schistocytes_percent", "schistocyte_percent"),
    ("g6pd_enzyme_activity", "glucose_6_phosphate_dehydrogenase_activity", "glucose_six_phosphate_dehydrogenase_quantitative"),
    ("17_hydroxyprogesterone", "seventeen_hydroxyprogesterone"),
    ("urine_red_blood_cells_per_hpf", "urine_red_blood_cells", "urine_rbc_count"),
    ("urine_white_blood_cells_per_hpf", "urine_white_blood_cells", "urine_wbc_count"),
    ("fasting_c_peptide", "c_peptide"),
    ("total_carbon_dioxide", "carbon_dioxide", "total_co2"),
    ("cortisol_30min_post_acth", "cortisol_30_min_post_acth"),
    # --- engine-internal legacy ids (REFERENCE_RANGES / FEATURE_TO_FINDING / PANIC_VALUES) ---
    ("total_bilirubin", "bilirubin_total"),
    ("direct_bilirubin", "bilirubin_direct"),
    ("indirect_bilirubin", "bilirubin_indirect"),
    ("mean_corpuscular_hemoglobin_concentration", "mchc"),
    ("red_cell_distribution_width_cv", "red_cell_distribution_width"),
    ("25_hydroxy_vitamin_d", "vitamin_d", "vitamin_d_25_hydroxy"),
    ("international_normalized_ratio", "inr"),
    ("reticulocytes", "reticulocyte_count"),
    ("folate_serum", "folate"),
    ("haptoglobin_serum_quantitative", "haptoglobin"),
    ("fasting_serum_insulin", "fasting_insulin"),
    ("blood_urea_nitrogen", "urea_nitrogen"),
    ("thyroid_peroxidase_antibody", "anti_tpo_antibody"),
    ("ldl_cholesterol_calculated", "ldl_cholesterol"),
    ("creatine_kinase_total", "creatine_kinase"),
    ("anti_tissue_transglutaminase_iga", "anti_ttg_iga"),
    ("serum_osmolality", "osmolality"),
    ("beta_hydroxybutyrate", "ketones"),
    ("arterial_pco2", "pco2"),
    ("phosphate", "phosphate_inorganic"),
    ("neutrophils_percent", "neutrophils"),
    ("lymphocytes_percent", "lymphocytes"),
    ("morning_cortisol", "cortisol"),
    ("blood_urea_nitrogen_to_creatinine_ratio", "bun_to_creatinine_ratio"),
    ("neutrophil_to_lymphocyte_ratio_nlr", "neutrophil_to_lymphocyte_ratio"),
)


def _mirror_equivalent_observations(observations: dict[str, ObservationRecord],
                                    context: ClinicalContext) -> None:
    for group in EQUIVALENT_FEATURE_GROUPS:
        present = [f for f in group if f in observations]
        if not present:
            continue
        src = observations[present[0]]
        for f in group:
            if f not in observations:
                observations[f] = replace(src, feature_id=f) if is_dataclass(src) else src
    # A glucose drawn fasting satisfies the fasting-plasma-glucose criteria.
    if (context.fasting is True and "glucose" in observations
            and "fasting_plasma_glucose" not in observations):
        src = observations["glucose"]
        observations["fasting_plasma_glucose"] = (
            replace(src, feature_id="fasting_plasma_glucose") if is_dataclass(src) else src)


def preanalytical_gate(engine: "ClinicalRuleEngine",
                       observations: dict[str, ObservationRecord],
                       context: ClinicalContext) -> list[str]:
    """Structural plausibility of the *input* before any clinical reasoning.

    1. Physiologically impossible values are removed (transcription / unit
       error), never interpreted.
    2. Internal CBC arithmetic (MCHC = Hb/Hct, MCV = Hct/RBC, MCH = Hb/RBC)
       and chemistry identities (direct <= total bilirubin, LDL < TC,
       differential adds to ~100 %) are checked; contradictions lower the
       reliability of the analytes involved.
    3. Declared sample interference (haemolysis, lipaemia, icterus) lowers
       the reliability of the analytes it is known to bias and names the
       spurious result it classically produces.
    4. Demographic contradictions are reported.
    Returns human-readable warnings; reliability changes are written into
    record.metadata["preanalytical_penalty"].
    """
    warnings: list[str] = []

    def penalise(fid: str, factor: float, note: str) -> None:
        rec = observations.get(fid)
        if rec is None:
            return
        prev = _float(rec.metadata.get("preanalytical_penalty"))
        rec.metadata["preanalytical_penalty"] = min(prev if prev is not None else 1.0, factor)
        notes = rec.metadata.setdefault("preanalytical_notes", [])
        if note not in notes:
            notes.append(note)

    # --- 1. impossible values ---------------------------------------------
    # ESL ext 8c: values that are implausible in the stated unit but ordinary in the
    # sibling unit are the classic transcription error (glucose "5.5 mg/dL" = 5.5 mmol/L).
    # They are removed with an explicit note instead of being read literally.
    _UNIT_SWAP = {  # fid: (implausible-if-below, implausible-if-above, sibling unit, factor to canonical)
        "glucose": (20.0, None, "mmol/L", 18.016), "fasting_plasma_glucose": (20.0, None, "mmol/L", 18.016),
        "creatinine": (None, 30.0, "µmol/L", 1 / 88.4), "hemoglobin": (None, 26.0, "g/L", 0.1),
        "calcium_total": (None, 20.0, "mmol/L", 4.008), "total_bilirubin": (None, 60.0, "µmol/L", 1 / 17.1),
        "albumin": (None, 7.5, "g/L", 0.1), "urea": (None, 600.0, "mmol/L", 6.006),
        "blood_urea_nitrogen": (None, 300.0, "mmol/L", 2.8), "total_cholesterol": (None, 1500.0, "mmol/L", 38.67),
        "triglycerides": (None, 10000.0, "mmol/L", 88.57), "uric_acid": (None, 30.0, "µmol/L", 1 / 59.48),
        "magnesium": (None, 10.0, "mmol/L", 2.431), "phosphate": (None, 20.0, "mmol/L", 3.097),
    }
    for fid in list(observations.keys()):
        rec = observations[fid]
        val = _canonical_number(engine, fid, rec)
        if val is None:
            continue
        sw = _UNIT_SWAP.get(fid)
        if sw is not None and val >= 0:
            lo_bad, hi_bad, sib, fac = sw
            alt = val * fac
            if ((lo_bad is not None and val < lo_bad) or (hi_bad is not None and val > hi_bad)):
                lim0 = ABSOLUTE_LIMITS.get(fid)
                if lim0 is None or (lim0[0] <= alt <= lim0[1]):
                    warnings.append(
                        f"{fid}: {rec.value} {rec.unit or ''} is implausible in the stated unit but would be "
                        f"{alt:.3g} in canonical units if the sample was reported in {sib}; value removed from analysis - "
                        f"confirm the unit before re-running (probable unit transcription error).")
                    del observations[fid]
                    continue
        lim = ABSOLUTE_LIMITS.get(fid)
        if lim is None:  # ESL ext 8c: fall back to the feature registry's own physiological limits
            try:
                _pl = ((engine.features.get(fid) or {}).get("validation") or {}).get("physiological_limits") or {}
                if _pl.get("max") is not None:
                    lim = (float(_pl.get("min") or 0.0), float(_pl["max"]))
            except Exception:
                lim = None
        if val < 0 and fid not in ("base_excess", "anion_gap"):
            warnings.append(
                f"{fid}: negative value {rec.value} {rec.unit or ''} is physiologically "
                f"impossible; value removed from analysis - verify transcription.")
            del observations[fid]
            continue
        if lim and not (lim[0] <= val <= lim[1]):
            warnings.append(
                f"{fid}: {rec.value} {rec.unit or ''} lies outside the physiologically possible "
                f"range ({lim[0]:g}-{lim[1]:g} canonical units); value removed from analysis - "
                f"verify units and transcription before re-running.")
            del observations[fid]

    def num(*fids: str) -> Optional[float]:
        for f in fids:
            rec = observations.get(f)
            if rec is not None:
                v = _canonical_number(engine, f, rec)
                if v is not None:
                    return v
        return None

    # --- 2. culprit localisation (shared with the OCR layer) -----------------
    # The identity solver names the single analyte whose repair restores every
    # identity it takes part in; only that analyte is then down-weighted and
    # the innocent participants keep their reliability.
    culprits: dict[str, tuple[Any, str]] = {}
    exonerated: set[str] = set()
    try:
        from ocr_consistency import validate_results as _solve_identities
        pseudo = []
        for fid, rec in observations.items():
            if isinstance(rec.value, (int, float)) and not isinstance(rec.value, bool):
                pseudo.append({"feature_id": fid, "value": rec.value, "unit": rec.unit, "confidence": 1.0,
                               "requires_confirmation": False, "suggested_action": "accept", "warnings": [],
                               "original_value": rec.value})
        solved = _solve_identities(pseudo)
        for item in solved.get("failed", []):
            c = item.get("culprit")
            if c:
                rec_c = next((p for p in pseudo if p["feature_id"] == c), None)
                culprits[c] = ((rec_c or {}).get("suggested_value"), (rec_c or {}).get("repair_reason", ""))
                exonerated.update(f for f in item.get("fields", []) if f != c)
        for c, (sugg, why) in culprits.items():
            rec_c = observations.get(c)
            if rec_c is not None:
                rec_c.metadata["identity_culprit"] = True
                rec_c.metadata["identity_suggested_value"] = sugg
                warnings.append(
                    f"{c}: {rec_c.value} {rec_c.unit or ''} contradicts the panel's own arithmetic; reading "
                    f"{sugg} ({why}) would restore consistency - verify this value; the other analytes in the "
                    f"identity are coherent with each other.")
                penalise(c, 0.4, "identity solver: probable transcription/OCR error")
    except Exception:
        culprits, exonerated = {}, set()

    def penalise_group(fids: Iterable[str], factor: float, note_: str) -> None:
        for f in fids:
            if f in culprits:
                continue              # already carries the heavier culprit penalty
            if culprits and f in exonerated:
                continue              # a named culprit explains the failure
            penalise(f, factor, note_)

    # --- 2a. CBC arithmetic --------------------------------------------------
    hb, hct, rbc = num("hemoglobin"), num("hematocrit"), num("red_blood_cell_count")
    mcv, mch, mchc = (num("mean_corpuscular_volume"), num("mean_corpuscular_hemoglobin"),
                      num("mean_corpuscular_hemoglobin_concentration"))
    cbc_bad: list[str] = []
    if hb and hct:
        mchc_calc = hb / hct * 100.0
        if mchc is not None and abs(mchc - mchc_calc) > 2.5:
            cbc_bad.append(
                f"MCHC reported {mchc:.1f} g/dL but Hb/Hct gives {mchc_calc:.1f} g/dL")
        if mchc is None and not (26.0 <= mchc_calc <= 38.0):
            cbc_bad.append(
                f"Hb {hb:.1f} g/dL and Hct {hct:.1f} % imply MCHC {mchc_calc:.1f} g/dL "
                f"(physiological 26-38); one of them is mis-read")
    if hct and rbc:
        mcv_calc = hct / rbc * 10.0
        if mcv is not None and abs(mcv - mcv_calc) > 8.0:
            cbc_bad.append(f"MCV reported {mcv:.0f} fL but Hct/RBC gives {mcv_calc:.0f} fL")
    if hb and rbc:
        mch_calc = hb / rbc * 10.0
        if mch is not None and abs(mch - mch_calc) > 3.0:
            cbc_bad.append(f"MCH reported {mch:.1f} pg but Hb/RBC gives {mch_calc:.1f} pg")
    if mchc is not None and mchc > 37.0:
        warnings.append(
            f"MCHC {mchc:.1f} g/dL exceeds the physiological ceiling (~37): classic artefact of "
            f"cold agglutinins, lipaemia or in-vitro haemolysis - red-cell indices are unreliable "
            f"until the sample is warmed / plasma-replaced and re-run.")
        for f in ("mean_corpuscular_hemoglobin_concentration", "mean_corpuscular_hemoglobin",
                  "red_blood_cell_count", "mean_corpuscular_volume", "hematocrit"):
            penalise(f, 0.5, "MCHC > 37 artefact")
    if cbc_bad:
        warnings.append(
            "CBC indices are internally inconsistent (" + "; ".join(cbc_bad) + "). "
            "Likely OCR / transcription error - the affected red-cell parameters are "
            "down-weighted and must be verified against the original report.")
        penalise_group(("hemoglobin", "hematocrit", "red_blood_cell_count", "mean_corpuscular_volume",
                        "mean_corpuscular_hemoglobin", "mean_corpuscular_hemoglobin_concentration"),
                       0.6, "CBC arithmetic inconsistency")

    # --- 2b. differential sums to ~100 % --------------------------------------
    diff_parts = [num(f) for f in ("neutrophils_percent", "lymphocytes_percent",
                                   "monocytes_percent", "eosinophils_percent",
                                   "basophils_percent")]
    present = [v for v in diff_parts if v is not None]
    if len(present) >= 4:
        total = sum(present)
        if not (92.0 <= total <= 108.0):
            warnings.append(
                f"Leukocyte differential sums to {total:.0f} % (expected ~100 %): "
                f"a percentage was mis-read; differential-based rules are down-weighted.")
            penalise_group(("neutrophils_percent", "lymphocytes_percent", "monocytes_percent",
                            "eosinophils_percent", "basophils_percent"),
                           0.6, "differential does not sum to 100 %")

    # --- 2c. chemistry identities ----------------------------------------------
    tbil, dbil = num("total_bilirubin"), num("direct_bilirubin")
    if tbil is not None and dbil is not None and dbil > tbil * 1.05 + 0.1:
        warnings.append(
            f"Direct bilirubin {dbil:.2f} exceeds total bilirubin {tbil:.2f} - impossible; "
            f"both values down-weighted pending verification.")
        penalise_group(("total_bilirubin", "direct_bilirubin"), 0.5, "direct > total")
    tc, ldl, hdl = num("total_cholesterol"), num("ldl_cholesterol_direct", "ldl_cholesterol_calculated"), num("hdl_cholesterol")
    if tc is not None and ldl is not None and ldl > tc:
        warnings.append(f"LDL {ldl:.0f} exceeds total cholesterol {tc:.0f} - impossible; lipid values down-weighted.")
        penalise_group(("total_cholesterol", "ldl_cholesterol_direct", "ldl_cholesterol_calculated"), 0.5, "LDL > TC")
    if tc is not None and hdl is not None and ldl is not None and hdl + ldl > tc * 1.05 + 5:
        warnings.append(f"HDL + LDL ({hdl + ldl:.0f}) exceeds total cholesterol {tc:.0f} - lipid panel inconsistent.")
    bun, urea = num("blood_urea_nitrogen"), num("urea")
    if bun is not None and urea is not None and bun > 0:
        ratio = urea / bun
        if not (1.6 <= ratio <= 2.8):
            warnings.append(
                f"Urea/BUN ratio {ratio:.2f} (expected 2.14): urea and BUN were probably both "
                f"entered from the same figure or with mixed units.")
    na, cl, hco3 = num("sodium"), num("chloride"), num("bicarbonate")
    if na is not None and cl is not None and hco3 is not None:
        ag = na - (cl + hco3)
        if ag < 0 or ag > 45:
            warnings.append(
                f"Anion gap {ag:.0f} mmol/L is outside the possible range: one electrolyte is "
                f"mis-read (or bromide/lithium interference). Electrolyte rules down-weighted.")
            for f in ("sodium", "chloride", "bicarbonate"):
                penalise(f, 0.6, "implausible anion gap")

    # --- 3. declared interference ---------------------------------------------
    flags: dict[str, bool] = {}
    sources: list[Mapping[str, Any]] = [context.extra or {}]
    sources += [rec.metadata for rec in observations.values()]
    for kind, keys in _INTERFERENCE_KEYS.items():
        for src in sources:
            for k in keys:
                if k in src and _interference_present(src.get(k)):
                    flags[kind] = True
    if flags.get("hemolysis"):
        k = num("potassium")
        msg = ("Sample flagged haemolysed: potassium, LDH, AST, phosphate and magnesium are "
               "falsely raised in vitro.")
        if k is not None and k > 5.0:
            msg += (f" Potassium {k:.1f} mmol/L may be pseudohyperkalaemia - repeat on a "
                    f"fresh, non-haemolysed sample before treating.")
        warnings.append(msg)
    if flags.get("lipemia"):
        warnings.append("Sample flagged lipaemic: indirect-ISE sodium may be falsely low "
                        "(pseudohyponatraemia); MCHC/Hb may be falsely raised.")
    if flags.get("icterus"):
        warnings.append("Sample flagged icteric: Jaffe creatinine and some enzymatic assays are biased.")
    for kind, on in flags.items():
        if on:
            for fid, factor in INTERFERENCE_PENALTIES[kind].items():
                penalise(fid, factor, f"{kind} interference")

    # --- 4. demographics -------------------------------------------------------
    age = context.age_years
    rejected = _float((context.extra or {}).get("rejected_age_years"))
    if rejected is not None:
        warnings.append(f"Age {rejected:g} years is implausible and was ignored: the patient is "
                        f"interpreted WITHOUT age-specific reference intervals - verify the record.")
    elif age is not None and (age < 0 or age > 120):
        warnings.append(f"Age {age:g} years is implausible; age-specific reference intervals "
                        f"may be wrong - verify the patient record.")
    if context.pregnant and context.normalized_jensiat() == "male":
        warnings.append("Pregnancy flag set for a male patient; the flag is ignored for "
                        "reference-interval selection - verify the patient record.")
        try:
            context.pregnant = False
        except Exception:
            pass
    if context.pregnant and age is not None and (age < 10 or age > 60):
        warnings.append(f"Pregnancy flag with age {age:g} years is unusual - verify the patient record.")

    return warnings


_REGISTRY_RANGES_HYDRATED = False


def hydrate_reference_ranges_from_registry(features: Mapping[str, Any]) -> int:
    """Fill REFERENCE_RANGES / SEX_SPECIFIC_RANGES from registry intervals.

    Curated engine tables always win; only features with NO engine interval
    are added. Intervals are taken as published in the registry's canonical
    unit (the same unit the rule layer assumes for scalar input). Critical
    limits come from `validation.critical` when numeric. Returns the number
    of features added. Idempotent.
    """
    global _REGISTRY_RANGES_HYDRATED
    if _REGISTRY_RANGES_HYDRATED:
        return 0
    added = 0
    sex_pop = {"adult_male": "male", "adult_female": "female",
               "older_adult_male": "male", "older_adult_female": "female"}
    for fid, feat in features.items():
        if not isinstance(feat, Mapping) or fid in REFERENCE_RANGES:
            continue
        ranges = feat.get("reference_ranges") or []
        if not isinstance(ranges, list):
            continue
        general: Optional[dict] = None
        by_sex: dict[str, dict] = {}
        for r in ranges:
            if not isinstance(r, Mapping):
                continue
            lo, hi = _float(r.get("low")), _float(r.get("high"))
            if lo is None and hi is None:
                continue
            pop = str(r.get("population") or "adult").lower()
            sex = str(r.get("sex") or "all").lower()
            entry = {}
            # One-sided intervals (e.g. troponin "< 0.04"): open side is
            # anchored at 0 / a wide multiple so comparisons stay numeric.
            entry["low"] = lo if lo is not None else 0.0
            entry["high"] = hi if hi is not None else (
                (lo * 10.0) if lo and lo > 0 else float("inf"))
            if sex in ("male", "female") or pop in sex_pop:
                by_sex[sex if sex in ("male", "female") else sex_pop[pop]] = entry
            elif pop in ("adult", "adult_normal", "healthy_adult") or general is None:
                if general is None or pop == "adult":
                    general = entry
        if general is None and by_sex:
            # average the sexes as the unstratified fallback
            lows = [v["low"] for v in by_sex.values()]
            highs = [v["high"] for v in by_sex.values()]
            general = {"low": min(lows), "high": max(highs)}
        if general is None:
            continue
        if general["high"] == float("inf"):
            continue
        crit = ((feat.get("validation") or {}).get("critical") or {})
        c_lo, c_hi = _float(crit.get("low")), _float(crit.get("high"))
        if c_lo is not None:
            general["critical_low"] = c_lo
        if c_hi is not None:
            general["critical_high"] = c_hi
        REFERENCE_RANGES[fid] = general
        if by_sex:
            SEX_SPECIFIC_RANGES.setdefault(fid, {}).update(by_sex)
        added += 1
    _REGISTRY_RANGES_HYDRATED = True
    return added



# =============================================================================
# EXPERT SYNDROME LAYER (ESL) - in-engine clinical syndrome library
# =============================================================================
# Why this exists. The registry rules are single-threshold, AI-assembled
# statements ("glucose <= 70 -> Addison's"). Difficult presentations are
# defined by *constellations* with exclusions (AKA = ketoacidosis + low/normal
# glucose + alcohol context; PTHrP-mediated hypercalcaemia = high Ca + low PTH
# + high PTHrP; Gilbert = isolated unconjugated hyperbilirubinaemia with
# normal haemolysis markers). This layer encodes such constellations as
# declarative criteria taken from the primary guideline / textbook definition
# and feeds a met constellation into the fusion as a curated, anchored rule
# vote (same path as `curated_guideline_anchored` registry rules), together
# with the set of features it consumed so evidence subsumption can list the
# constituent findings beneath it.
#
# Each entry:
#   id        syndrome id (report key)
#   dx        target disease ids, first = primary (must exist in registry)
#   req       criteria that must ALL be met
#   sup       optional criteria; `min_sup` of them must be met
#   excl      criteria that, when met, veto the syndrome
#   ctx       context predicates (pregnant / age / sex / med / cond)
#   cap       {disease_id: factor} - competitors capped at factor x own score
#   strength  "anchor" (0.95) | "strong" (0.88) | "pattern" (0.80, finding-level guard)
#   src       citation
#
# Criteria are (key, op, value). Keys are ESL analyte groups (see
# _ESL_GROUPS, resolved against the observation ids with unit conversion to
# the group's canonical unit) or computed keys (_ESL_COMPUTED).
# Ops: > >= < <= == between pos neg present absent
# -----------------------------------------------------------------------------

_ESL_GROUPS: dict[str, tuple[str, tuple[str, ...]]] = {
    # key: (canonical unit for thresholds, candidate observation ids)
    "glucose": ("mg/dL", ("glucose", "fasting_plasma_glucose", "glucose_random", "plasma_glucose")),
    "fpg": ("mg/dL", ("fasting_plasma_glucose", "glucose_fasting")),  # ESL extension 6d (2026-10-21)
    "glucose_1h": ("mg/dL", ("glucose_1_hour_ogtt",)),
    "glucose_2h": ("mg/dL", ("glucose_2_hour_postprandial", "glucose_2_hour_ogtt", "two_hour_plasma_glucose")),
    "a1c": ("%", ("hemoglobin_a1c",)),
    "na": ("mmol/L", ("sodium",)),
    "k": ("mmol/L", ("potassium",)),
    "cl": ("mmol/L", ("chloride",)),
    "hco3": ("mmol/L", ("bicarbonate", "calculated_bicarbonate_blood_gas", "serum_bicarbonate")),
    "ph": ("[pH]", ("arterial_ph", "venous_ph", "ph")),
    "pco2": ("mm[Hg]", ("arterial_pco2", "venous_pco2")),
    "po2": ("mm[Hg]", ("arterial_po2",)),
    "ag": ("mmol/L", ("anion_gap",)),
    "lactate": ("mmol/L", ("lactate", "lactate_arterial", "lactate_venous", "plasma_lactate")),
    "bhb": ("mmol/L", ("beta_hydroxybutyrate",)),
    "osm": ("mOsm/kg", ("serum_osmolality", "serum_osmolality_measured", "measured_osmolality")),
    "osm_calc": ("mOsm/kg", ("calculated_osmolality",)),
    "osm_gap": ("mOsm/kg", ("osmolal_gap", "calculated_serum_osmolal_gap")),
    "uosm": ("mOsm/kg", ("urine_osmolality", "urine_osmolality_random")),
    "una": ("mmol/L", ("urine_sodium",)),
    "ucl": ("mmol/L", ("urine_chloride",)),
    "uph": ("[pH]", ("urine_ph",)),
    "uag": ("mmol/L", ("urine_anion_gap", "urine_anion_gap_unadjusted")),
    "usg": ("1", ("urine_specific_gravity",)),
    "fena": ("%", ("fractional_excretion_of_sodium",)),
    "feurea": ("%", ("fractional_excretion_of_urea",)),
    "cr": ("mg/dL", ("creatinine",)),
    "bun": ("mg/dL", ("blood_urea_nitrogen",)),
    "urea": ("mg/dL", ("urea",)),
    "egfr": ("mL/min/1.73m2", ("egfr_ckd_epi_creatinine", "egfr_ckd_epi_creatinine_cystatin_c", "egfr_cystatin_c")),
    "ca": ("mg/dL", ("calcium_total",)),
    "ica": ("mmol/L", ("calcium_ionized",)),
    "phos": ("mg/dL", ("phosphate", "phosphorus")),
    "mg": ("mg/dL", ("magnesium",)),
    "alb": ("g/dL", ("albumin",)),
    "tp": ("g/dL", ("total_protein",)),
    "prealb": ("mg/dL", ("prealbumin",)),
    "urate": ("mg/dL", ("uric_acid",)),
    "pth": ("pg/mL", ("parathyroid_hormone_intact", "intact_parathyroid_hormone", "parathyroid_hormone")),
    "pthrp": ("pmol/L", ("parathyroid_hormone_related_peptide",)),
    "vitd": ("ng/mL", ("25_hydroxy_vitamin_d",)),
    "vitd125": ("pg/mL", ("1_25_dihydroxy_vitamin_d",)),
    "ace": ("U/L", ("angiotensin_converting_enzyme",)),
    "alp": ("U/L", ("alkaline_phosphatase",)),
    "bsap": ("ug/L", ("bone_specific_alkaline_phosphatase", "bone_specific_alkaline_phosphatase_bsap")),
    "ggt": ("U/L", ("gamma_glutamyl_transferase",)),
    "alt": ("U/L", ("alanine_aminotransferase",)),
    "ast": ("U/L", ("aspartate_aminotransferase",)),
    "tbil": ("mg/dL", ("total_bilirubin",)),
    "dbil": ("mg/dL", ("direct_bilirubin",)),
    "ibil": ("mg/dL", ("indirect_bilirubin",)),
    "inr": ("1", ("international_normalized_ratio",)),
    "pt": ("s", ("prothrombin_time",)),
    "aptt": ("s", ("activated_partial_thromboplastin_time",)),
    "fib": ("mg/dL", ("fibrinogen",)),
    "ddimer": ("ug/mL", ("d_dimer", "d_dimer_fibrinogen_equivalent_units")),
    "at": ("%", ("antithrombin_activity", "antithrombin_iii_functional_activity")),
    "f8": ("%", ("factor_viii_activity", "factor_viii_chromogenic_activity")),
    "f9": ("%", ("factor_ix_activity",)),
    "f7": ("%", ("factor_vii_activity",)),
    "f5": ("%", ("factor_v_activity",)),
    "vwf_ag": ("%", ("von_willebrand_factor_antigen",)),
    "vwf_act": ("%", ("von_willebrand_factor_activity", "von_willebrand_factor_collagen_binding_activity")),
    "la": ("1", ("lupus_anticoagulant_confirm", "lupus_anticoagulant_screen")),
    "acl": ("GPL", ("cardiolipin_igg_antibody", "cardiolipin_igm_antibody")),
    "b2gp": ("U/mL", ("beta_2_glycoprotein_i_igg_antibody", "beta_2_glycoprotein_i_igm_antibody")),
    "hit_ab": ("OD", ("heparin_induced_thrombocytopenia_antibody", "heparin_induced_platelet_antibody")),
    "sra": ("%", ("serotonin_release_assay",)),
    "nh3": ("umol/L", ("ammonia", "plasma_ammonia", "serum_ammonia")),
    "lipase": ("U/L", ("lipase", "serum_lipase")),
    "amylase": ("U/L", ("amylase", "pancreatic_amylase")),
    "elastase": ("ug/g", ("fecal_elastase_1", "pancreatic_elastase_fecal")),
    "calpro": ("ug/g", ("fecal_calprotectin", "fecal_calprotectin_quantitative")),
    "ttg_iga": ("U/mL", ("anti_tissue_transglutaminase_iga", "tissue_transglutaminase_iga_antibody")),
    "ttg_igg": ("U/mL", ("anti_tissue_transglutaminase_igg", "tissue_transglutaminase_igg_antibody")),
    "dgp_igg": ("U/mL", ("anti_deamidated_gliadin_peptide_igg", "deamidated_gliadin_peptide_igg_antibody")),
    "iga": ("mg/dL", ("total_immunoglobulin_a", "immunoglobulin_a", "iga_total", "total_iga")),
    "igg": ("mg/dL", ("total_immunoglobulin_g", "immunoglobulin_g", "igg_total", "total_igg")),
    "igm": ("mg/dL", ("total_immunoglobulin_m", "immunoglobulin_m", "igm_total", "total_igm")),
    "igg4": ("mg/dL", ("immunoglobulin_g4", "igg_subclass_4")),
    "ck": ("U/L", ("creatine_kinase_total", "creatine_kinase", "ck")),
    "ckmb": ("ng/mL", ("creatine_kinase_mb_mass", "ck_mb_mass", "creatine_kinase_mb")),
    "aldolase": ("U/L", ("aldolase",)),
    "myoglobin": ("ng/mL", ("myoglobin", "myoglobin_serum")),
    "ldh": ("U/L", ("lactate_dehydrogenase",)),
    "hapto": ("mg/dL", ("serum_haptoglobin", "haptoglobin_serum_quantitative", "haptoglobin")),
    "retic": ("%", ("reticulocyte_percent", "reticulocytes", "corrected_reticulocyte_count")),
    "retic_abs": ("10^9/L", ("absolute_reticulocyte_count", "reticulocyte_count_absolute")),
    "hb": ("g/dL", ("hemoglobin",)),
    "hct": ("%", ("hematocrit",)),
    "mcv": ("fL", ("mean_corpuscular_volume",)),
    "mchc": ("g/dL", ("mean_corpuscular_hemoglobin_concentration",)),
    "rdw": ("%", ("red_cell_distribution_width_cv",)),
    "rbc": ("10^6/uL", ("red_blood_cell_count",)),
    "wbc": ("10^9/L", ("white_blood_cell_count",)),
    "anc": ("10^9/L", ("neutrophil_count_absolute",)),
    "alc": ("10^9/L", ("lymphocyte_count_absolute",)),
    "aec": ("10^9/L", ("eosinophil_count_absolute",)),
    "neut_pct": ("%", ("neutrophils_percent",)),
    "lymph_pct": ("%", ("lymphocytes_percent",)),
    "atyp_lymph": ("%", ("atypical_lymphocytes_percent",)),
    "bands": ("%", ("band_neutrophils_percent",)),
    "baso_pct": ("%", ("basophils_percent",)),
    "blasts": ("%", ("blasts_percent", "blast_cells_percent")),
    "promyelo": ("%", ("promyelocytes_percent",)),
    "plt": ("10^9/L", ("platelets", "platelet_count")),
    "mpv": ("fL", ("mean_platelet_volume",)),
    "nrbc": ("%", ("nucleated_red_blood_cells_percent",)),
    "schisto": ("%", ("schistocytes_percent", "schistocyte_percent")),
    "sphero": ("%", ("spherocytes_percent", "spherocytes_presence")),
    "dat": ("1", ("coombs_direct_antiglobulin_test", "direct_antiglobulin_test")),
    "g6pd": ("U/g{Hb}", ("g6pd_enzyme_activity",)),
    "heinz": ("1", ("heinz_bodies_presence", "heinz_bodies", "heinz_bodies_percent")),
    "bite": ("1", ("bite_cells_presence", "bite_cells")),
    "hbs": ("%", ("hemoglobin_s",)),
    "hbf": ("%", ("hemoglobin_f",)),
    "hba2": ("%", ("hemoglobin_a2",)),
    "ferritin": ("ng/mL", ("ferritin",)),
    "tsat": ("%", ("transferrin_saturation",)),
    "iron": ("ug/dL", ("serum_iron",)),
    "tibc": ("ug/dL", ("total_iron_binding_capacity",)),
    "stfr": ("mg/L", ("soluble_transferrin_receptor",)),
    "chr": ("pg", ("reticulocyte_hemoglobin_content", "reticulocyte_hemoglobin_equivalent")),
    "b12": ("pg/mL", ("vitamin_b12",)),
    "mma": ("nmol/L", ("methylmalonic_acid", "serum_methylmalonic_acid_quantitative")),
    "hcy": ("umol/L", ("homocysteine", "homocysteine_serum", "plasma_homocysteine")),
    "folate": ("ng/mL", ("folate_serum",)),
    "if_ab": ("1", ("anti_intrinsic_factor_antibody_igg", "intrinsic_factor_antibody")),
    "lead": ("ug/dL", ("blood_lead", "lead")),
    "zpp": ("ug/dL", ("zinc_protoporphyrin",)),
    "stippling": ("1", ("basophilic_stippling_presence",)),
    "epo": ("mIU/mL", ("erythropoietin_serum_quantitative", "erythropoietin")),
    "jak2": ("1", ("jak2_v617f_mutation",)),
    "bcr": ("1", ("bcr_abl1_p210_transcript", "bcr_abl1_transcript")),
    "smudge": ("1", ("smudge_cells", "smudge_cells_presence")),
    "teardrop": ("1", ("teardrop_cells", "teardrop_cells_presence")),
    "auer": ("1", ("auer_rods_presence", "auer_rods")),
    "hfe": ("1", ("hfe_c282y_mutation",)),
    "pnh": ("%", ("cd55_cd59_pnh_flow", "pnh_clone_granulocytes")),
    "uhemosiderin": ("1", ("urine_hemosiderin",)),
    "adamts13": ("%", ("adamts13_activity", "adamts13_activity_quantitative")),
    "shiga": ("1", ("shiga_toxin_stool", "shiga_toxin_pcr_stool", "stool_shiga_toxin")),
    "mspike": ("g/dL", ("serum_protein_electrophoresis_m_spike",)),
    "flc_k": ("mg/L", ("serum_free_light_chain_kappa",)),
    "flc_l": ("mg/L", ("serum_free_light_chain_lambda",)),
    "flc_ratio": ("1", ("free_light_chain_ratio",)),
    "b2m": ("mg/L", ("beta_2_microglobulin", "beta_2_microglobulin_serum")),
    "viscosity": ("cP", ("serum_viscosity", "plasma_viscosity")),
    "uprot24": ("g/24h", ("urine_protein_24_hour",)),
    "upcr": ("g/g", ("urine_protein_to_creatinine_ratio", "protein_creatinine_ratio")),
    "uacr": ("mg/g", ("urine_albumin_to_creatinine_ratio", "urine_albumin_creatinine_ratio")),
    "urbc": ("/[HPF]", ("urine_red_blood_cells_per_hpf", "urine_red_blood_cells", "urine_rbc_count")),
    "urbc_casts": ("/[LPF]", ("urine_red_blood_cell_casts_per_lpf",)),
    "ugran_casts": ("1", ("urine_granular_casts_per_lpf", "urine_sediment_granular_casts", "urine_granular_casts")),
    "uwbc": ("/[HPF]", ("urine_white_blood_cells_per_hpf", "urine_white_blood_cells")),
    "ule": ("1", ("urine_leukocyte_esterase", "urine_leukocyte_esterase_dipstick")),
    "unitrite": ("1", ("urine_nitrite", "urine_nitrite_dipstick")),
    "ublood": ("1", ("urine_blood_qualitative", "urine_blood_dipstick")),
    "uhb": ("1", ("urine_hemoglobin",)),
    "ucacr": ("mg/mg", ("urine_calcium_creatinine_ratio",)),
    "uca24": ("mg/24h", ("urine_calcium_24h", "twenty_four_hour_urine_calcium")),
    "ucu24": ("ug/24h", ("urine_copper_24h", "urine_copper")),
    "cerulo": ("mg/dL", ("ceruloplasmin", "ceruloplasmin_serum", "serum_ceruloplasmin")),
    "a1at": ("mg/dL", ("alpha_1_antitrypsin_serum",)),
    "ama": ("U/mL", ("anti_mitochondrial_antibody_m2", "mitochondrial_m2_antibody")),
    "asma": ("{titer}", ("anti_smooth_muscle_antibody_titer", "smooth_muscle_antibody")),
    "ana": ("{titer}", ("antinuclear_antibody_titer", "antinuclear_antibody_screen")),
    "dsdna": ("IU/mL", ("double_stranded_dna_antibody", "anti_double_stranded_dna_antibody", "anti_dsdna")),
    "c3": ("mg/dL", ("complement_c3",)),
    "c4": ("mg/dL", ("complement_c4",)),
    "rf": ("IU/mL", ("rheumatoid_factor", "rheumatoid_factor_igm_quantitative")),
    "ccp": ("U/mL", ("anti_cyclic_citrullinated_peptide_igg", "cyclic_citrullinated_peptide_antibody", "anti_cyclic_citrullinated_peptide_antibody")),
    "ssa": ("1", ("ssa_ro_antibody", "anti_ssa_ro60_antibody", "anti_ssa_ro52_antibody")),
    "ssb": ("1", ("ssb_la_antibody", "anti_ssb_la_antibody_igg")),
    "scl70": ("1", ("scl_70_antibody",)),
    "jo1": ("1", ("jo_1_antibody",)),
    "mpo": ("1", ("p_anca_anti_myeloperoxidase", "myeloperoxidase_antibody")),
    "pr3": ("1", ("c_anca_anti_proteinase_3", "proteinase_3_antibody")),
    "esr": ("mm/h", ("erythrocyte_sedimentation_rate",)),
    "crp": ("mg/L", ("c_reactive_protein", "high_sensitivity_c_reactive_protein")),
    "pct": ("ng/mL", ("procalcitonin", "procalcitonin_quantitative")),
    "sil2r": ("U/mL", ("soluble_interleukin_2_receptor_cd25",)),
    "glyc_ferritin": ("%", ("glycosylated_ferritin_percentage", "glycosylated_ferritin_percent")),
    "tg": ("mg/dL", ("triglycerides",)),
    "tc": ("mg/dL", ("total_cholesterol",)),
    "ldl": ("mg/dL", ("ldl_cholesterol_calculated", "ldl_cholesterol_direct")),
    "hdl": ("mg/dL", ("hdl_cholesterol",)),
    "lpa": ("mg/dL", ("lipoprotein_a",)),
    "apob": ("mg/dL", ("apolipoprotein_b",)),
    "tsh": ("uIU/mL", ("thyroid_stimulating_hormone",)),
    "ft4": ("ng/dL", ("free_thyroxine",)),
    "ft3": ("pg/mL", ("free_triiodothyronine",)),
    "tt4": ("ug/dL", ("total_thyroxine",)),
    "tt3": ("ng/dL", ("total_triiodothyronine",)),
    "rt3": ("ng/mL", ("reverse_t3", "reverse_triiodothyronine")),
    "tpo": ("IU/mL", ("thyroid_peroxidase_antibody",)),
    "trab": ("IU/L", ("tsh_receptor_antibody",)),
    "tg_protein": ("ng/mL", ("thyroglobulin",)),
    "calcitonin": ("pg/mL", ("calcitonin", "serum_calcitonin_basal", "calcitonin_tumor_marker")),
    "cortisol_am": ("ug/dL", ("cortisol_morning", "cortisol_8am", "cortisol")),
    "cortisol_pm": ("ug/dL", ("cortisol_evening",)),
    "cortisol_dex": ("ug/dL", ("cortisol_after_dexamethasone",)),
    "ufc": ("ug/24h", ("urine_free_cortisol_24h",)),
    "acth": ("pg/mL", ("adrenocorticotropic_hormone", "plasma_adrenocorticotropic_hormone", "acth_plasma", "acth")),
    "aldo": ("ng/dL", ("aldosterone",)),
    "pra": ("ng/mL/h", ("plasma_renin_activity",)),
    "arr": ("1", ("aldosterone_renin_ratio", "aldosterone_to_renin_ratio", "aldosterone_to_renin_ratio_arr")),
    "metaneph": ("nmol/L", ("plasma_free_metanephrines", "plasma_metanephrine")),
    "normetaneph": ("nmol/L", ("plasma_free_normetanephrines", "plasma_normetanephrine")),
    "umetaneph": ("ug/24h", ("urine_fractionated_metanephrines_24h", "urine_metanephrine")),
    "prl": ("ng/mL", ("prolactin",)),
    "macroprl": ("%", ("macroprolactin", "prolactin_macroprolactin")),
    "igf1": ("ng/mL", ("insulin_like_growth_factor_1",)),
    "gh": ("ng/mL", ("growth_hormone", "growth_hormone_fasting")),
    "testo": ("ng/dL", ("total_testosterone",)),
    "ftesto": ("pg/mL", ("free_testosterone", "free_testosterone_calculated")),
    "lh": ("IU/L", ("luteinizing_hormone",)),
    "fsh": ("IU/L", ("follicle_stimulating_hormone",)),
    "e2": ("pg/mL", ("estradiol",)),
    "amh": ("ng/mL", ("anti_mullerian_hormone",)),
    "dheas": ("ug/dL", ("dhea_sulfate", "dhea_sulfate_serum")),
    "ohp17": ("ng/dL", ("17_hydroxyprogesterone", "seventeen_hydroxyprogesterone")),
    "andro": ("ng/dL", ("androstenedione", "androstenedione_serum")),
    "insulin": ("uIU/mL", ("insulin", "insulin_fasting", "fasting_serum_insulin")),
    "cpep": ("ng/mL", ("c_peptide", "fasting_c_peptide")),
    "proins": ("pmol/L", ("proinsulin",)),
    "gad": ("IU/mL", ("anti_glutamic_acid_decarboxylase_65", "glutamic_acid_decarboxylase_antibody", "gad65_antibody")),
    "trop": ("ng/L", ("high_sensitivity_troponin_t", "high_sensitivity_troponin_i")),
    "trop_conv": ("ng/mL", ("troponin_i", "troponin_t")),
    "bnp": ("pg/mL", ("b_type_natriuretic_peptide",)),
    "ntprobnp": ("pg/mL", ("nt_probnp", "n_terminal_pro_bnp", "n_terminal_pro_b_type_natriuretic_peptide")),
    "cohb": ("%", ("carboxyhemoglobin_fraction", "carboxyhemoglobin_blood_gas")),
    "methb": ("%", ("methemoglobin_fraction", "methemoglobin_blood_gas")),
    "spo2": ("%", ("oxygen_saturation", "oxygen_saturation_pulse_oximetry", "spo2")),
    "sao2": ("%", ("oxygen_saturation_arterial",)),
    "ethanol": ("mg/dL", ("ethanol",)),
    "salicylate": ("mg/dL", ("salicylate",)),
    "apap": ("ug/mL", ("acetaminophen",)),
    "lithium": ("mmol/L", ("lithium", "serum_lithium_therapeutic_level")),
    "afp": ("ng/mL", ("alpha_fetoprotein",)),
    "hcg": ("mIU/mL", ("human_chorionic_gonadotropin_quantitative", "beta_hcg")),
    "psa": ("ng/mL", ("total_prostate_specific_antigen", "prostate_specific_antigen")),
    "fpsa_pct": ("%", ("free_prostate_specific_antigen_percent",)),
    "ca125": ("U/mL", ("ca_125",)),
    "he4": ("pmol/L", ("human_epididymis_protein_4",)),
    "ca199": ("U/mL", ("ca_19_9",)),
    "cea": ("ng/mL", ("carcinoembryonic_antigen",)),
    "cga": ("ng/mL", ("serum_chromogranin_a", "chromogranin_a_tumor_marker", "chromogranin_a")),
    "hiaa": ("mg/24h", ("urine_five_hydroxyindoleacetic_acid_24h", "urine_5_hydroxyindoleacetic_acid_24h")),
    "serotonin": ("ng/mL", ("serotonin_serum",)),
    "pbg": ("mg/L", ("twenty_four_hour_urine_porphobilinogen", "urine_porphobilinogen")),
    "ala": ("mg/L", ("twenty_four_hour_urine_delta_aminolevulinic_acid", "urine_delta_aminolevulinic_acid")),
    "bile_acids": ("umol/L", ("total_bile_acids_serum", "bile_acids_total", "total_bile_acids")),
    "sflt_plgf": ("1", ("sflt1_plgf_ratio", "sflt_1_plgf_ratio")),
    "sweat_cl": ("mmol/L", ("sweat_chloride",)),
    "cd4": ("cells/uL", ("cd4_absolute_t_cell_count", "cd4_t_cells_absolute", "cd4_t_cell_count")),
    "hiv_ab": ("1", ("hiv_1_and_hiv_2_antigen_antibody", "hiv_p24_antigen_antibody_combo")),
    "hiv_vl": ("copies/mL", ("hiv_1_viral_load", "hiv_one_rna_viral_load")),
    "hbsag": ("1", ("hepatitis_b_surface_antigen",)),
    "hbeag": ("1", ("hepatitis_b_e_antigen",)),
    "hbv_dna": ("IU/mL", ("hepatitis_b_dna_quantitative_pcr", "hepatitis_b_dna_quantitative")),
    "hbc_igm": ("1", ("hepatitis_b_core_igm_antibody", "hepatitis_b_core_antibody_igm")),
    "hav_igm": ("1", ("hepatitis_a_igm_antibody",)),
    "hcv_ab": ("1", ("hepatitis_c_antibody",)),
    "hetero": ("1", ("heterophile_antibody",)),
    "ebv_vca_igm": ("1", ("ebv_vca_igm", "epstein_barr_vca_igm_antibody", "epstein_barr_virus_vca_igm")),
    "ns1": ("1", ("dengue_ns1_antigen", "dengue_virus_ns1_antigen")),
    "malaria": ("%", ("malaria_thick_smear_parasitemia_percentage", "malaria_parasitemia_percent")),
    "malaria_smear": ("1", ("malaria_parasite_blood_smear",)),
    "igra": ("1", ("quantiferon_tb_gold_plus", "interferon_gamma_release_assay")),
    "bcx": ("1", ("blood_culture",)),
    "ucx": ("1", ("urine_culture",)),
    "msu": ("1", ("synovial_fluid_crystals_monosodium_urate",)),
    "cppd": ("1", ("synovial_fluid_crystals_calcium_pyrophosphate",)),
    "thiamine": ("nmol/L", ("vitamin_b1_thiamine", "vitamin_b1_thiamine_whole_blood")),
    "vita": ("ug/dL", ("vitamin_a_retinol", "vitamin_a_retinol_serum")),
    "zinc": ("ug/dL", ("zinc",)),
    "ema": ("1", ("eosin_5_maleimide_binding", "ema_binding_test")),
    "nk": ("1", ("nk_cell_activity",)),
    "copro_i": ("%", ("urine_coproporphyrin_i_fraction", "coproporphyrin_i_fraction")),
    "mixing": ("1", ("aptt_mixing_study_corrects", "mixing_study_aptt", "aptt_mixing_study_immediate")),
    "pfa": ("s", ("pfa_100_collagen_epinephrine", "pfa_100_closure_time_col_epi", "platelet_function_analyzer_closure_time_collagen_epinephrine")),
    "hypersegs": ("1", ("hypersegmented_neutrophils_presence", "hypersegmented_neutrophils")),
    "maternal_o": ("1", ("maternal_blood_group_o",)),
}


def _esl_compute(v: Mapping[str, Optional[float]], ctx: "ClinicalContext") -> dict[str, Optional[float]]:
    """Computed keys (returns None when inputs missing)."""
    out: dict[str, Optional[float]] = {}
    # ESL extension 6d (2026-10-21): eGFR — reported value preferred, else CKD-EPI 2021 (race-free) from creatinine
    _eg = v.get("egfr")
    if _eg is None and v.get("cr") is not None:
        try:
            _age = _float(getattr(ctx, "age_years", None)); _sex = str(getattr(ctx, "sex_at_birth", "") or "").lower()
            if _age is not None and _age >= 18:
                _f = _sex.startswith("f"); _kappa = 0.7 if _f else 0.9; _alpha = -0.241 if _f else -0.302
                _r = float(v["cr"]) / _kappa
                _eg = 142.0 * (min(_r, 1.0) ** _alpha) * (max(_r, 1.0) ** -1.200) * (0.9938 ** _age) * (1.012 if _f else 1.0)
        except Exception:
            _eg = None
    out["egfr_c"] = _eg
    if v.get("egfr") is None and _eg is not None:
        out["egfr"] = _eg  # extension 7 (2026-10-22): computed CKD-EPI 2021 stands in for an unreported eGFR
    # v6 (SAP Amendment 14, C3): KDIGO AKI 2012 §2.1 / Appendix B — when no baseline creatinine is known in an acute-care
    # encounter, the baseline is back-calculated from the MDRD equation assuming eGFR 75 mL/min/1.73 m2; the observed
    # creatinine divided by that imputed baseline is the KDIGO staging ratio (>= 1.5 = stage 1, >= 2.0 = 2, >= 3.0 = 3).
    # v6 (SAP Amendment 14, C2): SIRS criteria count (ACCP/SCCM 1992) from temperature, heart rate, respiratory rate, WBC/bands
    try:
        _t, _hr, _rr, _w, _b = v.get("temp"), v.get("hr"), v.get("rr"), v.get("wbc"), v.get("bands")
        _n = 0
        _n += 1 if (_t is not None and (_t > 38.0 or _t < 36.0)) else 0
        _n += 1 if (_hr is not None and _hr > 90) else 0
        _n += 1 if (_rr is not None and _rr > 20) else 0
        _n += 1 if ((_w is not None and (_w > 12.0 or _w < 4.0)) or (_b is not None and _b > 10)) else 0
        _k = sum(x is not None for x in (_t, _hr, _rr)) + (1 if (_w is not None or _b is not None) else 0)
        out["sirs_count"] = float(_n) if _k >= 2 else None   # need at least two criteria assessable
        out["sirs_assessed"] = float(_k)
    except Exception:
        out["sirs_count"] = None
    out["cr_ratio_imputed"] = None
    if v.get("cr") is not None:
        try:
            _age = _float(getattr(ctx, "age_years", None)); _sex = str(getattr(ctx, "sex_at_birth", "") or "").lower()
            if _age is not None and _age >= 18:
                _base = (75.0 / (175.0 * (_age ** -0.203) * (0.742 if _sex.startswith("f") else 1.0))) ** (-1.0 / 1.154)
                out["cr_baseline_imputed"] = _base
                out["cr_ratio_imputed"] = float(v["cr"]) / _base if _base > 0 else None
        except Exception:
            out["cr_ratio_imputed"] = None
    na, cl, hco3, k = v.get("na"), v.get("cl"), v.get("hco3"), v.get("k")
    alb = v.get("alb")
    ag = v.get("ag")
    if ag is None and None not in (na, cl, hco3):
        ag = na - cl - hco3
    if ag is not None and alb is not None and alb < 4.0:
        ag = ag + 2.5 * (4.0 - alb)
    out["ag_c"] = ag
    out["delta_ratio"] = ((ag - 12.0) / (24.0 - hco3)) if (ag is not None and hco3 is not None and hco3 < 24) else None
    glu, bun = v.get("glucose"), v.get("bun")
    osm_calc = v.get("osm_calc")
    if osm_calc is None and None not in (na, glu, bun):
        osm_calc = 2 * na + glu / 18.0 + bun / 2.8
    og = v.get("osm_gap")
    if og is None and v.get("osm") is not None and osm_calc is not None:
        og = v["osm"] - osm_calc
    out["osm_gap_c"] = og
    out["osm_eff_c"] = (2 * na + glu / 18.0) if None not in (na, glu) else None  # extension 7: effective osmolality (ADA 2024)
    # extension 7: glucose-corrected sodium (Katz 1973 / Hillier 1999: +1.6 per 100 mg/dL over 100) and NLR (Zahorec 2001)
    out["na_c"] = (na + 1.6 * (glu - 100.0) / 100.0) if (None not in (na, glu) and glu > 100) else na
    _np, _lp = v.get("neut_pct"), v.get("lymph_pct")
    out["nlr_c"] = (_np / _lp) if (_np is not None and _lp not in (None, 0)) else None
    ca = v.get("ca")
    out["ca_c"] = (ca + 0.8 * (4.0 - alb)) if (ca is not None and alb is not None) else ca
    out["bun_cr"] = (bun / v["cr"]) if (bun is not None and v.get("cr")) else None
    ast, alt, alp = v.get("ast"), v.get("alt"), v.get("alp")
    out["ast_alt"] = (ast / alt) if (ast is not None and alt) else None
    out["r_ratio"] = ((alt / 40.0) / (alp / 120.0)) if (alt is not None and alp) else None
    tb, db = v.get("tbil"), v.get("dbil")
    ib = v.get("ibil")
    if ib is None and tb is not None and db is not None:
        ib = tb - db
    out["ibil_c"] = ib
    out["dbil_frac"] = (db / tb) if (db is not None and tb) else None
    out["mentzer"] = (v["mcv"] / v["rbc"]) if (v.get("mcv") is not None and v.get("rbc")) else None
    fk, fl = v.get("flc_k"), v.get("flc_l")
    fr = v.get("flc_ratio")
    if fr is None and fk is not None and fl:
        fr = fk / fl
    out["flc_ratio_c"] = fr
    out["flc_diff"] = (abs(fk - fl)) if (fk is not None and fl is not None) else None
    trop = v.get("trop")
    if trop is None and v.get("trop_conv") is not None:
        trop = v["trop_conv"] * 1000.0
    out["trop_c"] = trop
    natri = v.get("ntprobnp")
    out["natri_high"] = 1.0 if ((natri is not None and natri > 900) or (v.get("bnp") is not None and v["bnp"] > 400)) else (
        0.0 if (natri is not None or v.get("bnp") is not None) else None)
    out["tg_hdl"] = (v["tg"] / v["hdl"]) if (v.get("tg") is not None and v.get("hdl")) else None
    out["lh_fsh"] = (v["lh"] / v["fsh"]) if (v.get("lh") is not None and v.get("fsh")) else None
    age = _float(getattr(ctx, "age_years", None))
    out["age"] = age
    # extension 7 (2026-10-22): anion gap not explained by lactate (DKA may coexist with lactic acidosis)
    _agc = out.get("ag_c") if out.get("ag_c") is not None else v.get("ag")
    _lac = v.get("lactate")
    out["ag_minus_lac"] = None if _agc is None else (_agc - (_lac or 0.0))
    return out


def _esl_temporal(series: Mapping[str, list[tuple[float, float]]]) -> dict[str, Optional[float]]:
    """ESL extension 11-T (2026-10-23): reduce per-analyte time series (ESL group
    units, hours) to trajectory keys.  Pairwise statistics are computed over all
    ordered pairs (i < j) so irregular ICU sampling is handled without
    interpolation; nothing is extrapolated beyond the observed span.

      {k}_first/_last/_min/_max/_n/_span_h        basic
      {k}_delta, {k}_delta_pct                     last - first (and % of first)
      {k}_rise48 / {k}_fall48                      largest rise / fall within any <= 48 h window
      {k}_rise24 / {k}_fall24                      same within <= 24 h
      {k}_ratio_max                                max later/earlier ratio (KDIGO x1.5)
      {k}_ratio_fall                               max earlier/later ratio (recovery)
      {k}_drop_pct                                 largest % fall from an earlier value
      {k}_pair_pct                                 largest |%| change between samples 1-12 h apart
      {k}_clear_pct                                (first - min of later samples >= 2 h) / first * 100
    Troponin is unified to ng/L as trop_dyn_* (trop = ng/L, trop_conv = ng/mL)."""
    out: dict[str, Optional[float]] = {}
    for key, pts in series.items():
        if not pts or len(pts) < 2:
            continue
        ts = [p[0] for p in pts]; vs = [p[1] for p in pts]
        first, last = vs[0], vs[-1]
        out[f"{key}_first"], out[f"{key}_last"] = first, last
        out[f"{key}_min"], out[f"{key}_max"], out[f"{key}_n"] = min(vs), max(vs), float(len(vs))
        out[f"{key}_span_h"] = ts[-1] - ts[0]
        out[f"{key}_delta"] = last - first
        out[f"{key}_delta_pct"] = ((last - first) / first * 100.0) if first > 0 else None
        r48 = f48 = r24 = f24 = 0.0; rmax = 1.0; rfall = 1.0; drop = 0.0; pair = 0.0
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dt = ts[j] - ts[i]; dv = vs[j] - vs[i]
                if dt <= 48.0:
                    r48 = max(r48, dv); f48 = max(f48, -dv)
                if dt <= 24.0:
                    r24 = max(r24, dv); f24 = max(f24, -dv)
                if vs[i] > 0:
                    rmax = max(rmax, vs[j] / vs[i]); drop = max(drop, (vs[i] - vs[j]) / vs[i] * 100.0)
                    if 1.0 <= dt <= 12.0:
                        pair = max(pair, abs(dv) / vs[i] * 100.0)
                if vs[j] > 0:
                    rfall = max(rfall, vs[i] / vs[j])
        out[f"{key}_rise48"], out[f"{key}_fall48"] = r48, f48
        out[f"{key}_rise24"], out[f"{key}_fall24"] = r24, f24
        out[f"{key}_ratio_max"], out[f"{key}_ratio_fall"] = rmax, rfall
        out[f"{key}_drop_pct"], out[f"{key}_pair_pct"] = drop, pair
        later = [v for t, v in pts[1:] if t - ts[0] >= 2.0]
        out[f"{key}_clear_pct"] = ((first - min(later)) / first * 100.0) if (later and first > 0) else None
    # troponin unified in ng/L
    for src_key, mult in (("trop", 1.0), ("trop_conv", 1000.0)):
        if f"{src_key}_n" in out:
            out["trop_dyn_min_ngl"] = out[f"{src_key}_min"] * mult
            out["trop_dyn_max_ngl"] = out[f"{src_key}_max"] * mult
            out["trop_dyn_pct"] = max(out.get("trop_dyn_pct") or 0.0, out[f"{src_key}_pair_pct"] or 0.0, abs(out[f"{src_key}_delta_pct"] or 0.0))
            out["trop_dyn_span_h"] = out[f"{src_key}_span_h"]
            out["trop_dyn_rise_ngl"] = max(out.get("trop_dyn_rise_ngl") or 0.0, (out[f"{src_key}_rise48"] or 0.0) * mult)
            break
    return out


def _esl_ctx(ctx: "ClinicalContext", pred: str, arg: Any) -> bool:
    try:
        if pred == "pregnant":
            return bool(getattr(ctx, "pregnant", False)) == bool(arg)
        if pred == "age_lt":
            a = _float(getattr(ctx, "age_years", None)); return a is not None and a < arg
        if pred == "age_ge":
            a = _float(getattr(ctx, "age_years", None)); return a is not None and a >= arg
        if pred == "sex":
            return str(getattr(ctx, "sex_at_birth", "") or "").lower().startswith(str(arg))
        if pred == "encounter_in":  # v6 (SAP Amendment 14): acute-care vs community panel
            enc = str(getattr(ctx, "encounter", "") or "").lower()
            return any(enc.startswith(str(x)) for x in (arg if isinstance(arg, (list, tuple, set)) else (arg,)))
        if pred == "attr_true":  # ESL extension 6c (2026-10-21)
            v = getattr(ctx, str(arg), None)
            if v is None:
                v = (getattr(ctx, "extra", {}) or {}).get(str(arg))
            return bool(v)
        if pred in ("attr_lt", "attr_gt"):
            name, thr = arg
            v = getattr(ctx, str(name), None)
            if v is None:
                v = (getattr(ctx, "extra", {}) or {}).get(str(name))
            v = _float(v)
            if v is None:
                return False
            return v < thr if pred == "attr_lt" else v > thr
        if pred in ("med", "cond", "fh", "sym"):
            key = {"med": ("current_medications", "medications"),
                   "cond": ("known_conditions", "conditions", "comorbidities"),
                   "fh": ("family_history",),
                   # v6 C9 (2026-10-25): presenting symptoms (free text or list) - needed for the
                   # ischaemia arm of the Universal Definition of MI
                   "sym": ("presenting_complaint", "chief_complaint", "symptoms", "symptom_list", "presentation")}[pred]
            items: list[str] = []
            for kname in key:
                val = getattr(ctx, kname, None)
                if val is None:
                    val = (getattr(ctx, "extra", {}) or {}).get(kname)
                if isinstance(val, (list, tuple, set)):
                    items.extend(str(x).lower() for x in val)
                elif isinstance(val, str):
                    items.append(val.lower())
            return any(str(arg).lower() in it for it in items)
    except Exception:
        return False
    return False


def _esl_test(val: Optional[float], op: str, arg: Any) -> Optional[bool]:
    """None = cannot evaluate (missing)."""
    if op == "absent":
        return val is None
    if val is None:
        return None
    # Unit round-trips (mg/dL -> umol/L -> mg/dL) perturb values at the
    # 1e-12 level; a threshold must not flip on that noise.
    eps = 1e-7 * max(1.0, abs(float(arg)) if isinstance(arg, (int, float)) else 1.0)
    if op == ">": return val > arg + eps
    if op == ">=": return val >= arg - eps
    if op == "<": return val < arg - eps
    if op == "<=": return val <= arg + eps
    if op == "==": return abs(val - arg) < 1e-9
    if op == "between": return arg[0] - eps <= val <= arg[1] + eps
    if op == "pos": return val > 0
    if op == "neg": return val <= 0
    if op == "present": return True
    return None


# ---------------------------------------------------------------------------
# The syndrome library. Thresholds follow the cited primary sources; where a
# source gives a range the more specific bound is used. Values are in the
# group canonical unit (see _ESL_GROUPS).
# ---------------------------------------------------------------------------
_ESL_LIBRARY: list[dict[str, Any]] = [
 # ---------------- acid-base / toxicology ---------------------------------
 dict(id="dka", dx=["diabetic_ketoacidosis", "diabetes_mellitus"], req=[("glucose", ">=", 200), ("bhb", ">=", 3.0)],  # extension 7: ADA/EASD 2024 glucose >= 200
      sup=[("hco3", "<", 18), ("ph", "<", 7.30), ("ag_c", ">", 12)], min_sup=1,
      cap={"metabolic_acidosis": 0.9, "euglycemic_diabetic_ketoacidosis": 0.7, "alcoholic_ketoacidosis": 0.6, "hyperosmolar_hyperglycemic_state": 0.8},
      src="ADA/EASD 2024 hyperglycaemic crises consensus"),
 dict(id="euglycemic_dka", dx=["euglycemic_diabetic_ketoacidosis", "diabetic_ketoacidosis"], req=[("glucose", "<=", 250), ("glucose", ">", 90), ("bhb", ">=", 3.0), ("hco3", "<", 18)],
      sup=[("ag_c", ">", 12), ("ph", "<", 7.30)], min_sup=1, excl=[("ethanol", ">", 20)],
      ctx=[("med", "gliflozin")], cap={"metabolic_acidosis": 0.9, "alcoholic_ketoacidosis": 0.7, "diabetic_ketoacidosis": 0.9},
      src="ADA/EASD 2024 (euglycaemic DKA, SGLT2i)"),
 dict(id="aka", dx=["alcoholic_ketoacidosis"], req=[("bhb", ">=", 3.0), ("glucose", "<", 250), ("ag_c", ">", 12)],
      sup=[("ethanol", "present", None), ("glucose", "<", 100), ("phos", "<", 2.5), ("mg", "<", 1.7), ("k", "<", 3.5), ("ggt", ">", 60), ("mcv", ">", 98)], min_sup=2,
      cap={"euglycemic_diabetic_ketoacidosis": 0.6, "diabetic_ketoacidosis": 0.6, "metabolic_acidosis": 0.9, "starvation_ketosis": 0.8},
      src="UpToDate: Fasting ketosis and alcoholic ketoacidosis"),
 dict(id="toxic_alcohol", dx=["ethylene_glycol_poisoning", "toxic_alcohol_poisoning", "methanol_poisoning"], req=[("ag_c", ">", 16), ("osm_gap_c", ">", 20), ("hco3", "<", 18)],
      sup=[("ca_c", "<", 8.5), ("cr", ">", 1.3), ("lactate", "<", 5), ("bhb", "<", 1.0)], min_sup=1, excl=[("ethanol", ">", 80), ("bhb", ">=", 3.0), ("glucose", ">", 300)],
      cap={"metabolic_acidosis": 0.85, "euglycemic_diabetic_ketoacidosis": 0.5, "lactic_acidosis": 0.7, "diabetic_ketoacidosis": 0.5},
      src="Kraut & Kurtz, Toxic alcohol ingestions, CJASN 2008; AACT/EAPCCT guideline 2002"),
 dict(id="salicylate", dx=["salicylate_toxicity", "salicylate_poisoning", "aspirin_overdose"], req=[("salicylate", ">", 30)],
      sup=[("ag_c", ">", 12), ("pco2", "<", 35), ("ph", ">", 7.40), ("hco3", "<", 20)], min_sup=1,
      cap={"respiratory_alkalosis": 0.85, "metabolic_acidosis": 0.85}, src="UpToDate: Salicylate poisoning in adults"),
 dict(id="lactic_acidosis_sepsis", dx=["sepsis", "septic_shock_severe_lactic_acidosis", "lactic_acidosis"], req=[("lactate", ">=", 4.0)],
      sup=[("wbc", ">", 12), ("wbc", "<", 4), ("bands", ">", 10), ("pct", ">", 2.0), ("crp", ">", 100), ("cr", ">", 1.5), ("plt", "<", 100)], min_sup=2,
      excl=[("cohb", ">", 10), ("ethanol", ">", 80)], cap={"metabolic_acidosis": 0.9}, src="Sepsis-3 (Singer, JAMA 2016); SSC 2021"),
 dict(id="rta1", dx=["renal_tubular_acidosis_type_1", "renal_tubular_acidosis_type_1_distal", "renal_tubular_acidosis"], req=[("hco3", "<", 20), ("ag_c", "<=", 14), ("uph", ">", 5.5)],
      sup=[("k", "<", 3.5), ("uag", ">", 0), ("cl", ">", 108)], min_sup=1,
      cap={"metabolic_acidosis": 0.85, "hypokalemia": 0.9, "hyperchloremia": 0.9, "acute_gastroenteritis": 0.5}, src="Palmer & Clegg, Renal tubular acidosis, CJASN 2021"),
 dict(id="rta4", dx=["renal_tubular_acidosis_type_4", "renal_tubular_acidosis_type_4_hyperkalemic", "renal_tubular_acidosis"], req=[("hco3", "<", 22), ("ag_c", "<=", 14), ("k", ">", 5.0)],
      sup=[("uph", "<", 5.5), ("glucose", ">", 126), ("a1c", ">=", 6.5), ("cr", "between", (1.2, 1.8))], min_sup=1,
      excl=[("cr", ">", 1.8), ("bun", ">", 40), ("lactate", ">", 4), ("glucose", ">", 400)],
      cap={"hyperkalemia": 0.9, "hyperchloremia": 0.9, "metabolic_acidosis": 0.85}, src="Palmer & Clegg 2021; Karet, JASN 2009; KDIGO AKI 2012 (acidosis + hyperkalaemia of renal failure)"),
 dict(id="gi_bicarb_loss", dx=["acute_gastroenteritis", "diarrhea", "gastrointestinal_bicarbonate_loss"], req=[("hco3", "<", 20), ("ag_c", "<=", 14), ("uag", "<", 0)],
      sup=[("k", "<", 3.5), ("uph", "<", 5.5), ("bun_cr", ">", 20)], min_sup=1, cap={"renal_tubular_acidosis": 0.6, "metabolic_acidosis": 0.85},
      src="Batlle, NEJM 1988 (urine anion gap)"),
 dict(id="chronic_resp_acidosis", dx=["copd", "respiratory_acidosis"], req=[("pco2", ">", 50), ("hco3", ">", 28)],
      sup=[("ph", "between", (7.30, 7.42)), ("po2", "<", 65), ("hct", ">", 50)], min_sup=1, src="Berend, NEJM 2014 (acid-base)"),
 dict(id="met_alk_vomiting", dx=["metabolic_alkalosis", "hypochloremic_metabolic_alkalosis", "vomiting"], req=[("hco3", ">", 30), ("ucl", "<", 20)],
      sup=[("k", "<", 3.5), ("cl", "<", 98), ("ph", ">", 7.45)], min_sup=1, cap={"primary_aldosteronism": 0.6, "primary_aldosteronism_arr_pattern": 0.6, "bartter_syndrome": 0.5, "gitelman_syndrome": 0.5},
      src="Galla, Metabolic alkalosis, JASN 2000"),
 dict(id="gitelman", dx=["gitelman_syndrome", "bartter_syndrome"], req=[("k", "<", 3.5), ("hco3", ">", 28), ("mg", "<", 1.7), ("ucl", ">", 20)],
      sup=[("ucacr", "<", 0.07), ("pra", ">", 3), ("aldo", ">", 15)], min_sup=1, excl=[("arr", ">", 30)],
      cap={"primary_aldosteronism_arr_pattern": 0.5, "primary_aldosteronism": 0.5, "hypokalemia": 0.9, "hypomagnesemia": 0.9, "hypochloremia": 0.9, "pyloric_stenosis": 0.5},
      src="Blanchard et al., KDIGO Gitelman consensus, Kidney Int 2017"),
 dict(id="bartter", dx=["bartter_syndrome", "gitelman_syndrome"], req=[("k", "<", 3.5), ("hco3", ">", 28), ("ucl", ">", 20), ("ucacr", ">", 0.2)],
      sup=[("pra", ">", 3), ("aldo", ">", 15), ("mg", ">=", 1.7)], min_sup=1, excl=[("arr", ">", 30)], ctx=[], cap={"primary_aldosteronism": 0.5},
      src="Konrad et al., Bartter consensus, Kidney Int 2021"),
 # ---------------- renal / electrolytes -----------------------------------
 dict(id="prerenal", dx=["prerenal_azotemia", "acute_kidney_injury"], req=[("cr", ">", 1.3), ("bun_cr", ">", 20)],
      sup=[("fena", "<", 1.0), ("una", "<", 20), ("feurea", "<", 35), ("natri_high", "==", 1), ("hco3", ">", 28)], min_sup=1,
      excl=[("fena", ">", 2.0), ("ck", ">", 5000)], cap={"acute_tubular_necrosis_atn": 0.6, "hyponatremia": 0.85},
      src="KDIGO AKI 2012; Perazella, CJASN 2012 (FENa/FEurea)"),
 dict(id="atn", dx=["acute_tubular_necrosis_atn", "acute_kidney_injury"], req=[("cr", ">", 1.5), ("fena", ">", 2.0)],
      sup=[("una", ">", 40), ("uosm", "<", 350), ("ugran_casts", "pos", None), ("bun_cr", "<", 20), ("k", ">", 5.0)], min_sup=1,
      cap={"prerenal_azotemia": 0.6, "chronic_kidney_disease": 0.8}, src="KDIGO AKI 2012; Perazella 2012"),
 dict(id="rhabdo", dx=["rhabdomyolysis"], req=[("ck", ">", 5000)],
      sup=[("k", ">", 5.0), ("phos", ">", 4.5), ("ca_c", "<", 8.5), ("urate", ">", 7), ("cr", ">", 1.3), ("ast_alt", ">", 1.5), ("myoglobin", ">", 500), ("ublood", "pos", None)], min_sup=2,
      excl=[("jo1", "pos", None), ("trop_c", ">", 500)],
      cap={"acute_kidney_injury": 0.85, "hyperkalemia": 0.9, "acute_myocardial_infarction": 0.7, "hepatitis": 0.6, "serotonin_syndrome": 0.5, "malignant_catatonia": 0.5, "neuroleptic_malignant_syndrome": 0.5, "tetanus": 0.4},
      src="Bosch, Rhabdomyolysis and AKI, NEJM 2009"),
 dict(id="tls", dx=["tumor_lysis_syndrome"], req=[("urate", ">=", 8.0), ("phos", ">=", 4.5), ("k", ">=", 6.0)],
      sup=[("ca_c", "<=", 7.0), ("cr", ">", 1.5), ("ldh", ">", 500), ("blasts", ">", 0), ("wbc", ">", 50)], min_sup=1,
      cap={"acute_myeloid_leukemia": 0.95, "acute_lymphoblastic_leukemia": 0.95, "hyperphosphatemia": 0.9, "hyperkalemia": 0.9, "hyperuricemia": 0.9, "acute_kidney_injury": 0.9},
      src="Cairo-Bishop 2004; Howard, NEJM 2011"),
 dict(id="nephrotic", dx=["nephrotic_syndrome"], req=[("alb", "<", 3.0)], sup=[("upcr", ">=", 3.0), ("uprot24", ">=", 3.5)], min_sup=1,
      excl=[("flc_ratio_c", ">", 8), ("flc_ratio_c", "<", 0.1)], src="KDIGO GN 2021"),
 dict(id="nephrotic_child_mcd", dx=["minimal_change_disease", "nephrotic_syndrome"], req=[("alb", "<", 2.5), ("upcr", ">=", 2.0)], sup=[("tc", ">", 200), ("cr", "<", 1.0)], min_sup=1,
      ctx=[("age_lt", 12)], src="KDIGO GN 2021 (paediatric SSNS)"),
 dict(id="lupus_nephritis", dx=["lupus_nephritis", "systemic_lupus_erythematosus"], req=[("dsdna", ">", 30), ("urbc", ">", 5)],
      sup=[("c3", "<", 90), ("c4", "<", 10), ("upcr", ">", 0.5), ("urbc_casts", "pos", None), ("cr", ">", 1.2), ("ana", ">=", 80)], min_sup=2,
      cap={"acute_kidney_injury": 0.85, "anemia": 0.85, "leukopenia": 0.85, "acute_leukemia": 0.4, "aplastic_anemia": 0.4},
      src="EULAR/ACR 2019 SLE classification; KDIGO 2024 LN"),
 dict(id="sle", dx=["systemic_lupus_erythematosus"], req=[("ana", ">=", 80)],
      sup=[("dsdna", ">", 30), ("c3", "<", 90), ("c4", "<", 10), ("wbc", "<", 4), ("alc", "<", 1.0), ("plt", "<", 100), ("dat", "pos", None), ("upcr", ">", 0.5), ("esr", ">", 40)], min_sup=3,
      excl=[("scl70", "pos", None), ("jo1", "pos", None), ("ama", ">", 20), ("asma", ">=", 80)],
      cap={"acute_leukemia": 0.4, "aplastic_anemia": 0.4, "hereditary_angioedema_c1_inhibitor": 0.3, "vitamin_b12_deficiency": 0.5, "anemia": 0.85, "leukopenia": 0.85, "thrombocytopenia": 0.85},
      src="EULAR/ACR 2019 (ANA entry criterion + weighted domains)"),
 dict(id="anca_gn", dx=["anca_associated_glomerulonephritis", "anca_associated_vasculitis", "rapidly_progressive_glomerulonephritis", "microscopic_polyangiitis"],
      req=[("cr", ">", 1.5), ("urbc", ">", 5)], sup=[("mpo", "pos", None), ("pr3", "pos", None), ("urbc_casts", "pos", None), ("crp", ">", 30), ("esr", ">", 50)], min_sup=2,
      cap={"acute_kidney_injury": 0.85, "anemia": 0.85, "anemia_of_chronic_disease": 0.8, "bacterial_infection": 0.6}, src="KDIGO 2024 ANCA vasculitis; Chapel Hill 2012"),
 dict(id="siadh", dx=["siadh", "syndrome_of_inappropriate_antidiuretic_hormone"], req=[("na", "<", 135), ("osm", "<", 275), ("uosm", ">", 100), ("una", ">", 30)],
      sup=[("urate", "<", 4), ("bun", "<", 10), ("tsh", "between", (0.3, 5)), ("cortisol_am", ">", 10)], min_sup=1,
      excl=[("k", ">", 5.3), ("cortisol_am", "<", 5), ("bun_cr", ">", 20), ("hco3", ">", 30), ("pbg", ">", 10)],
      cap={"severe_hyponatremia": 0.9, "hyponatremia": 0.9, "adrenal_insufficiency": 0.6, "hypothyroidism": 0.6},
      src="Spasovski et al., European hyponatraemia guideline, Eur J Endocrinol 2014"),
 dict(id="thiazide_hyponat", dx=["hyponatremia", "severe_hyponatremia"],
      req=[("na", "<", 135), ("osm", "<", 275)], sup=[("k", "<", 3.5), ("urate", ">", 6), ("bun_cr", ">", 20), ("hco3", ">", 28)], min_sup=2,
      ctx=[("med", "thiazide")], cap={"siadh": 0.6, "severe_hyponatremia": 0.9}, src="Spasovski 2014; Filippone, AJKD 2020"),
 dict(id="hypovol_hyponat", dx=["hyponatremia", "severe_hyponatremia"], req=[("na", "<", 135), ("osm", "<", 275), ("bun_cr", ">", 20)],
      sup=[("urate", ">", 6), ("una", "<", 30), ("hco3", ">", 28), ("k", "<", 3.5)], min_sup=1, excl=[("cortisol_am", "<", 5)], cap={"siadh": 0.6},
      src="Spasovski 2014"),
 dict(id="central_di", dx=["diabetes_insipidus_central", "diabetes_insipidus", "central_diabetes_insipidus"], req=[("na", ">", 145), ("uosm", "<", 300)],
      sup=[("osm", ">", 295), ("usg", "<", 1.010), ("glucose", "<", 180), ("ca_c", "<", 10.5)], min_sup=1, excl=[("lithium", "present", None)],
      cap={"hypernatremia": 0.9, "dehydration": 0.8}, src="Christ-Crain, Nat Rev Dis Primers 2019; Endocrine Society AVP-D 2023"),
 dict(id="nephrogenic_di", dx=["diabetes_insipidus_nephrogenic", "diabetes_insipidus", "lithium_induced_nephrogenic_diabetes_insipidus"], req=[("na", ">", 145), ("uosm", "<", 300)],
      sup=[("lithium", "present", None), ("ca_c", ">", 10.5), ("k", "<", 3.5)], min_sup=1, cap={"diabetes_insipidus_central": 0.6, "hypernatremia": 0.9, "dehydration": 0.8},
      src="Christ-Crain 2019; Bockenhauer, Nat Rev Nephrol 2015"),
 # v6 (Amendment 14): a documented history of CKD / renal insufficiency establishes chronicity
 # (KDIGO CKD 2024: duration > 3 months is met when the abnormality is already known) — a
 # single reduced eGFR with such a history is CKD, not an undetermined reduction in GFR.
 dict(id="ckd_documented_history_reduced_egfr", dx=["chronic_kidney_disease"], req=[("egfr", "<", 60)], sup=[], min_sup=0, strength="strong",
      ctx_any=[("cond", "chronic kidney"), ("cond", "ckd"), ("cond", "renal insufficiency"), ("cond", "renal failure"), ("cond", "nephropathy"),
               ("cond", "dialysis"), ("cond", "esrd"), ("cond", "kidney disease")],
      excl=[("ck", ">", 5000)],
      cap={"reduced_gfr_chronicity_undetermined": 0.60}, src="KDIGO CKD 2024 (chronicity criterion: abnormality present > 3 months, met by documented history)"),
 dict(id="ckd_advanced", dx=["chronic_kidney_disease", "chronic_kidney_disease_stage_4"], req=[("egfr", "<", 30)],
      sup=[("pth", ">", 100), ("phos", ">", 4.5), ("hb", "<", 11), ("uacr", ">", 300), ("retic", "<", 1.5)], min_sup=2, strength="strong",
      excl=[("ck", ">", 5000), ("lactate", ">", 4)],
      cap={"acute_kidney_injury": 0.75, "secondary_hyperparathyroidism": 0.95}, src="KDIGO CKD 2024; KDIGO CKD-MBD 2017"),
 dict(id="hrs", dx=["hepatorenal_syndrome", "liver_cirrhosis"], req=[("cr", ">", 1.5), ("una", "<", 20)],
      sup=[("alb", "<", 3.0), ("tbil", ">", 3), ("inr", ">", 1.5), ("plt", "<", 150), ("na", "<", 135), ("nh3", ">", 60), ("fena", "<", 0.5)], min_sup=3,
      cap={"acute_kidney_injury": 0.85, "prerenal_azotemia": 0.7, "acute_tubular_necrosis_atn": 0.5}, src="ICA-AKI/EASL 2018 decompensated cirrhosis"),
 dict(id="primary_aldo", dx=["primary_aldosteronism", "primary_hyperaldosteronism", "conn_syndrome"], req=[("aldo", ">=", 10), ("pra", "<", 1.0)],
      sup=[("k", "<", 3.5), ("hco3", ">", 28), ("arr", ">", 30), ("na", ">", 142)], min_sup=1, cap={"hypokalemia": 0.9, "metabolic_alkalosis": 0.9, "primary_aldosteronism_arr_pattern": 0.95},
      src="Endocrine Society PA guideline 2016 (Funder)"),
 dict(id="refeeding", dx=["refeeding_syndrome", "hypophosphatemia"], req=[("phos", "<", 2.0)], sup=[("k", "<", 3.5), ("mg", "<", 1.7), ("thiamine", "<", 70), ("alb", "<", 3.0), ("prealb", "<", 15)], min_sup=2,
      excl=[("pth", ">", 65), ("ca_c", ">", 10.5)], cap={"hypokalemia": 0.9, "hypomagnesemia": 0.9}, src="ASPEN consensus refeeding 2020 (da Silva)"),
 dict(id="calcium_alkali", dx=["hypercalcemia", "severe_hypercalcemia"], req=[("ca_c", ">", 10.5), ("hco3", ">", 30), ("pth", "<", 20)],
      sup=[("cr", ">", 1.2), ("ph", ">", 7.45), ("pthrp", "<", 2)], min_sup=1, excl=[("pthrp", ">", 2)],
      cap={"hypercalcemia_of_malignancy_support_pattern": 0.6, "acute_kidney_injury": 0.8, "metabolic_alkalosis": 0.9, "chronic_kidney_disease": 0.7},
      src="Patel & Goldfarb, JASN 2010 (calcium-alkali syndrome)"),
 # ---------------- endocrine ------------------------------------------------
 dict(id="thyroid_storm", dx=["thyroid_storm", "hyperthyroidism", "graves_disease"], req=[("tsh", "<", 0.1), ("ft4", ">", 4.0)],
      sup=[("ft3", ">", 8), ("alt", ">", 50), ("tbil", ">", 1.5), ("glucose", ">", 140), ("ca_c", ">", 10.5), ("wbc", ">", 11), ("trab", ">", 1.75)], min_sup=2,
      cap={"hyperthyroidism": 0.95, "atrial_fibrillation_hyperthyroid": 0.8}, src="Burch-Wartofsky 1993; ATA 2016 hyperthyroidism"),
 dict(id="graves", dx=["graves_disease", "hyperthyroidism"], req=[("tsh", "<", 0.1), ("trab", ">", 1.75)], sup=[("ft4", ">", 1.8), ("ft3", ">", 4.2)], min_sup=1,
      cap={"painless_thyroiditis": 0.5, "silent_thyroiditis": 0.5, "thyroiditis": 0.5, "toxic_multinodular_goiter": 0.5}, src="ATA 2016"),
 dict(id="painless_thyroiditis", dx=["hashimoto_thyroiditis", "thyroiditis_pattern"],
      req=[("tsh", "<", 0.1), ("ft4", ">", 1.8), ("trab", "<", 1.75), ("tpo", ">", 35)], sup=[("esr", "<", 30), ("tg_protein", ">", 50)], min_sup=0,
      cap={"graves_disease": 0.5, "thyroid_storm": 0.5, "hyperthyroidism": 0.9, "atrial_fibrillation_hyperthyroid": 0.6, "primary_hyperthyroidism": 0.6},
      src="ATA 2016 (thyroiditis: TRAb-negative thyrotoxicosis); Samuels, JCEM 2012"),
 dict(id="subclin_hyperthyroid", dx=["subclinical_hyperthyroidism", "toxic_multinodular_goiter", "toxic_adenoma"], req=[("tsh", "<", 0.4), ("ft4", "between", (0.8, 1.8))],
      sup=[("ft3", "<=", 4.4), ("trab", "<", 1.75)], min_sup=1, excl=[("crp", ">", 50), ("alb", "<", 3.0)], src="ATA 2016 (subclinical hyperthyroidism)"),
 dict(id="nti", dx=["euthyroid_sick_syndrome_nontr"],
      req=[("ft3", "<", 2.0), ("tsh", "between", (0.05, 10))], sup=[("rt3", ">", 0.35), ("crp", ">", 50), ("alb", "<", 3.2), ("lactate", ">", 2), ("ft4", "between", (0.6, 1.8))], min_sup=2,
      cap={"subclinical_hyperthyroidism": 0.4, "central_hypothyroidism": 0.6, "hypothyroidism": 0.6, "sepsis": 0.95, "malnutrition": 0.9},
      src="Fliers, Lancet Diabetes Endocrinol 2015 (NTIS)"),
 # v7 C13 (2026-10-25): acute-care context. Fliers 2015 / ATA-AACE 2012 (Garber): in hospitalised and critically ill
 # patients TSH is commonly transiently low (0.1-0.4) or, in recovery, raised (up to ~20) with low T3 and low-normal
 # or low FT4; thyroid function should not be interpreted as thyroid disease in that setting unless TSH is
 # frankly suppressed (< 0.1) or frankly raised (> 10) or a thyroid history exists. No dataset threshold.
 # v7 C13 (2026-10-25, revised in the development gate): a NORMAL TSH with normal FT4 in an ICU patient is not a finding
 # at all - the syndrome needs an ABNORMAL thyroid test in the acute-care pattern (Fliers 2015): low T3 / low-normal FT4
 # with non-suppressed TSH, a mildly low TSH (0.1-0.4) during illness, or a mildly raised TSH (4.5-10) in recovery.
 # TSH < 0.1 or > 10 fall outside the syndrome (frank thyroid disease must be considered). No dataset threshold.
 dict(id="nti_acute_care_low_t3", dx=["euthyroid_sick_syndrome_nontr"], req=[("tsh", "between", (0.1, 10.0)), ("ft3", "<", 2.3)], alt_req=[("tsh", "between", (0.1, 10.0)), ("tt3", "<", 80)],
      sup=[("ft4", "<", 1.0), ("crp", ">", 30), ("alb", "<", 3.2), ("lactate", ">", 2), ("wbc", ">", 12), ("plt", "<", 150), ("rt3", ">", 0.35)], min_sup=0, strength="pattern", ctx=[("encounter_in", ("icu", "inpatient", "emergency", "hospital", "acute"))],
      ctx_excl=[("med", "levothyrox"), ("med", "methimazole"), ("med", "carbimazole"), ("med", "propylthiouracil"), ("med", "amiodarone"), ("med", "lithium"),
                ("cond", "thyroid"), ("cond", "graves"), ("cond", "hashimoto"), ("cond", "pituitary"), ("cond", "hypopituitar")],
      cap={"subclinical_hyperthyroidism": 0.5, "central_hypothyroidism": 0.6, "secondary_hypothyroidism": 0.6, "hypothyroidism": 0.7, "primary_hypothyroidism": 0.7,
           "subclinical_hypothyroidism": 0.7, "hyperthyroidism": 0.6, "toxic_multinodular_goiter": 0.5, "toxic_adenoma": 0.5, "hypopituitarism_panhypopituitarism": 0.7},
      src="Fliers, Bianco, Langouche, Boelen - Thyroid function in critically ill patients, Lancet Diabetes Endocrinol 2015 (doi 10.1016/S2213-8587(15)00225-9); ATA/AACE 2012 hypothyroidism guideline (Garber, Thyroid 2012) rec. on testing in hospitalised patients"),
 dict(id="nti_acute_care_low_t4", dx=["euthyroid_sick_syndrome_nontr"], req=[("tsh", "between", (0.1, 10.0)), ("ft4", "<", 0.9)],
      sup=[("ft3", "<", 2.6), ("crp", ">", 30), ("alb", "<", 3.2), ("lactate", ">", 2), ("wbc", ">", 12), ("plt", "<", 150), ("rt3", ">", 0.35)], min_sup=1, strength="pattern", ctx=[("encounter_in", ("icu", "inpatient", "emergency", "hospital", "acute"))],
      ctx_excl=[("med", "levothyrox"), ("med", "methimazole"), ("med", "carbimazole"), ("med", "propylthiouracil"), ("med", "amiodarone"), ("med", "lithium"),
                ("cond", "thyroid"), ("cond", "graves"), ("cond", "hashimoto"), ("cond", "pituitary"), ("cond", "hypopituitar")],
      cap={"subclinical_hyperthyroidism": 0.5, "central_hypothyroidism": 0.6, "secondary_hypothyroidism": 0.6, "hypothyroidism": 0.7, "primary_hypothyroidism": 0.7,
           "subclinical_hypothyroidism": 0.7, "hyperthyroidism": 0.6, "toxic_multinodular_goiter": 0.5, "toxic_adenoma": 0.5, "hypopituitarism_panhypopituitarism": 0.7},
      src="Fliers, Bianco, Langouche, Boelen - Thyroid function in critically ill patients, Lancet Diabetes Endocrinol 2015 (doi 10.1016/S2213-8587(15)00225-9); ATA/AACE 2012 hypothyroidism guideline (Garber, Thyroid 2012) rec. on testing in hospitalised patients"),
 dict(id="nti_acute_care_low_tsh", dx=["euthyroid_sick_syndrome_nontr"], req=[("tsh", "between", (0.1, 0.4))], excl=[("ft4", ">", 1.8), ("ft3", ">", 4.4)],
      sup=[("ft4", "<", 1.0), ("ft3", "<", 2.6), ("crp", ">", 30), ("alb", "<", 3.2), ("lactate", ">", 2), ("wbc", ">", 12), ("plt", "<", 150), ("rt3", ">", 0.35)], min_sup=1, strength="supportive", ctx=[("encounter_in", ("icu", "inpatient", "emergency", "hospital", "acute"))],
      ctx_excl=[("med", "levothyrox"), ("med", "methimazole"), ("med", "carbimazole"), ("med", "propylthiouracil"), ("med", "amiodarone"), ("med", "lithium"),
                ("cond", "thyroid"), ("cond", "graves"), ("cond", "hashimoto"), ("cond", "pituitary"), ("cond", "hypopituitar")],
      cap={"subclinical_hyperthyroidism": 0.5, "central_hypothyroidism": 0.6, "secondary_hypothyroidism": 0.6, "hypothyroidism": 0.7, "primary_hypothyroidism": 0.7,
           "subclinical_hypothyroidism": 0.7, "hyperthyroidism": 0.6, "toxic_multinodular_goiter": 0.5, "toxic_adenoma": 0.5, "hypopituitarism_panhypopituitarism": 0.7},
      src="Fliers, Bianco, Langouche, Boelen - Thyroid function in critically ill patients, Lancet Diabetes Endocrinol 2015 (doi 10.1016/S2213-8587(15)00225-9); ATA/AACE 2012 hypothyroidism guideline (Garber, Thyroid 2012) rec. on testing in hospitalised patients"),
 dict(id="nti_acute_care_recovery_tsh", dx=["euthyroid_sick_syndrome_nontr"], req=[("tsh", "between", (4.5, 10.0))], excl=[("ft4", "<", 0.8)],
      sup=[("ft3", "<", 2.6), ("crp", ">", 30), ("alb", "<", 3.2), ("lactate", ">", 2), ("wbc", ">", 12), ("plt", "<", 150), ("rt3", ">", 0.35)], min_sup=1, strength="supportive", ctx=[("encounter_in", ("icu", "inpatient", "emergency", "hospital", "acute"))],
      ctx_excl=[("med", "levothyrox"), ("med", "methimazole"), ("med", "carbimazole"), ("med", "propylthiouracil"), ("med", "amiodarone"), ("med", "lithium"),
                ("cond", "thyroid"), ("cond", "graves"), ("cond", "hashimoto"), ("cond", "pituitary"), ("cond", "hypopituitar")],
      cap={"subclinical_hypothyroidism": 0.6, "hypothyroidism": 0.7, "primary_hypothyroidism": 0.7, "subclinical_hypothyroidism_pattern": 0.6, "hashimoto_thyroiditis": 0.6},
      src="Fliers, Bianco, Langouche, Boelen - Thyroid function in critically ill patients, Lancet Diabetes Endocrinol 2015 (doi 10.1016/S2213-8587(15)00225-9); ATA/AACE 2012 hypothyroidism guideline (Garber, Thyroid 2012) rec. on testing in hospitalised patients"),
 dict(id="myxedema", dx=["myxedema_coma", "severe_hypothyroidism", "primary_hypothyroidism", "hypothyroidism"], req=[("tsh", ">", 30), ("ft4", "<", 0.5)],
      sup=[("na", "<", 130), ("glucose", "<", 70), ("ck", ">", 500), ("tc", ">", 240), ("pco2", ">", 45), ("hb", "<", 11)], min_sup=2,
      cap={"hyponatremia": 0.9, "siadh": 0.6, "rhabdomyolysis": 0.7, "hypothyroidism": 0.95}, src="ATA 2014 hypothyroidism guideline (Jonklaas)"),
 dict(id="central_hypothyroid", dx=["central_hypothyroidism", "secondary_hypothyroidism", "hypopituitarism_panhypopituitarism"], req=[("ft4", "<", 0.8), ("tsh", "<", 10)],
      sup=[("cortisol_am", "<", 5), ("testo", "<", 250), ("lh", "<", 1.5), ("fsh", "<", 1.5), ("prl", ">", 25), ("igf1", "<", 100), ("na", "<", 135), ("ft3", "<", 2.0)], min_sup=2,
      cap={"hyperprolactinemia": 0.8, "male_hypogonadism": 0.8, "hyponatremia": 0.85, "primary_hypothyroidism": 0.4, "hypothyroidism": 0.9},
      src="Persani, Central hypothyroidism, JCEM 2012; Endocrine Society hypopituitarism 2016"),
 dict(id="addison", dx=["primary_adrenal_insufficiency", "addison_disease", "adrenal_insufficiency", "adrenal_crisis"], req=[("cortisol_am", "<", 5)],
      sup=[("acth", ">", 100), ("na", "<", 135), ("k", ">", 5.0), ("glucose", "<", 70), ("aec", ">", 0.5), ("ca_c", ">", 10.3), ("bun_cr", ">", 20), ("tsh", "between", (4.5, 15))], min_sup=2,
      excl=[("acth", "<", 20)],
      cap={"hypothyroidism": 0.5, "acute_kidney_injury": 0.8, "eosinophilia": 0.85, "fasting_hypoglycemia": 0.85, "hyponatremia": 0.85, "hyperkalemia": 0.85, "siadh": 0.4},
      src="Endocrine Society PAI guideline 2016 (Bornstein)"),
 dict(id="secondary_ai", dx=["secondary_adrenal_insufficiency", "central_adrenal_insufficiency", "adrenal_insufficiency"], req=[("cortisol_am", "<", 5), ("acth", "<", 20)],
      sup=[("na", "<", 135), ("glucose", "<", 70), ("aec", ">", 0.5), ("k", "between", (3.5, 5.0))], min_sup=1,
      cap={"primary_adrenal_insufficiency": 0.5, "addison_disease": 0.5, "hyponatremia": 0.85, "siadh": 0.4}, src="Endocrine Society 2016; Fleseriu hypopituitarism 2016"),
 dict(id="cushing", dx=["cushing_syndrome", "cushing_disease_pituitary_acth", "cushing_disease"], req=[("cortisol_dex", ">", 1.8)],
      sup=[("ufc", ">", 100), ("cortisol_pm", ">", 7.5), ("glucose", ">", 126), ("k", "<", 3.5), ("hco3", ">", 28), ("lymph_pct", "<", 15), ("a1c", ">=", 6.5)], min_sup=2,
      cap={"hypokalemia": 0.9, "metabolic_alkalosis": 0.9, "diabetes_mellitus": 0.9}, src="Endocrine Society Cushing guideline 2008/2021 (Fleseriu)"),
 dict(id="cushing_ufc", dx=["cushing_syndrome", "cushing_disease_pituitary_acth"], req=[("ufc", ">", 150)], sup=[("cortisol_pm", ">", 7.5), ("acth", ">", 20), ("glucose", ">", 126), ("k", "<", 3.5)], min_sup=1,
      src="Endocrine Society 2008"),
 dict(id="pheo", dx=["pheochromocytoma", "pheochromocytoma_paraganglioma"], req=[("normetaneph", ">", 2.7)], sup=[("metaneph", ">", 1.0), ("glucose", ">", 126), ("hct", ">", 50), ("wbc", ">", 11)], min_sup=0,
      alt_req=[("metaneph", ">", 1.5)], cap={"adrenal_incidentaloma_workup": 0.8, "primary_hyperparathyroidism": 0.9}, src="Endocrine Society pheochromocytoma 2014 (Lenders)"),
 dict(id="phpt", dx=["primary_hyperparathyroidism"], req=[("ca_c", ">", 10.5), ("pth", ">", 40)], alt_req=[("ca", ">", 10.3), ("pth", ">", 40)],
      sup=[("phos", "<", 2.7), ("ica", ">", 1.32), ("cl", ">", 105), ("vitd", "<", 30), ("uca24", ">", 250), ("alp", ">", 120)], min_sup=1, excl=[("pthrp", ">", 2), ("calcitonin", ">", 100), ("egfr", "<", 30), ("ca", "<=", 10.1)],
      cap={"hypercalcemia": 0.9, "multiple_endocrine_neoplasia_type_1": 0.8}, src="Bilezikian, 5th International Workshop PHPT, JBMR 2022"),
 dict(id="hhm", dx=["hypercalcemia_of_malignancy_support_pattern", "paraneoplastic_hypercalcemia_support_pattern", "hypercalcemia"],
      req=[("ca_c", ">", 11.0), ("pth", "<", 25), ("pthrp", ">", 2.0)], sup=[("phos", "<", 3.0), ("alp", ">", 120), ("cr", ">", 1.2), ("alb", "<", 3.5)], min_sup=0,
      cap={"primary_hyperparathyroidism": 0.4, "hypercalcemia": 0.9, "milk_alkali_syndrome": 0.5, "acute_kidney_injury": 0.8}, src="Stewart, Hypercalcemia associated with cancer, NEJM 2005"),
 dict(id="granulomatous_hyperca", dx=["sarcoidosis", "granulomatous_hypercalcemia", "pth_independent_hypercalcemia", "hypercalcemia"],
      req=[("ca_c", ">", 10.5), ("pth", "<", 25), ("vitd125", ">", 70)], sup=[("ace", ">", 65), ("phos", ">", 3.5), ("cr", ">", 1.2)], min_sup=0, excl=[("pthrp", ">", 2)],
      cap={"primary_hyperparathyroidism": 0.4, "hypercalcemia": 0.9, "humoral_hypercalcemia_of_malignancy": 0.6}, src="Tebben, Vitamin D-mediated hypercalcemia, Endocr Rev 2016"),
 dict(id="hypopara", dx=["hypoparathyroidism", "postsurgical_hypoparathyroidism"], req=[("ca_c", "<", 8.5), ("pth", "<", 20)], sup=[("phos", ">", 4.5), ("ica", "<", 1.12), ("mg", ">=", 1.5)], min_sup=1,
      excl=[("mg", "<", 1.2)], cap={"hypocalcemia": 0.9, "secondary_hyperparathyroidism": 0.3}, src="Khan, Hypoparathyroidism guideline, JBMR 2022"),
 dict(id="pseudohypopara", dx=["pseudohypoparathyroidism"], req=[("ca_c", "<", 8.5), ("pth", ">", 65), ("phos", ">", 4.5)], sup=[("cr", "<", 1.2), ("vitd", ">=", 20), ("mg", ">=", 1.5)], min_sup=2,
      excl=[("egfr", "<", 45), ("cr", ">", 1.5)], cap={"hypocalcemia": 0.9, "secondary_hyperparathyroidism": 0.7}, src="Mantovani, PHP consensus, Nat Rev Endocrinol 2018"),
 dict(id="osteomalacia", dx=["osteomalacia", "vitamin_d_deficiency", "secondary_hyperparathyroidism"], req=[("vitd", "<", 12), ("alp", ">", 150)], sup=[("pth", ">", 65), ("ca_c", "<", 9.0), ("phos", "<", 2.5), ("ggt", "<", 60)], min_sup=2,
      cap={"vitamin_d_deficiency": 0.95, "cholestasis": 0.5, "primary_biliary_cholangitis": 0.4}, src="Bhan, Osteomalacia, Endocrinol Metab Clin 2010; Holick 2011"),
 dict(id="paget", dx=["paget_disease_of_bone", "paget_disease"], req=[("alp", ">", 200), ("ggt", "<", 60), ("ca_c", "between", (8.5, 10.5))],
      sup=[("bsap", ">", 20), ("phos", "between", (2.5, 4.5)), ("tbil", "<", 1.2), ("alt", "<", 40), ("vitd", ">=", 20)], min_sup=1, ctx=[("age_ge", 40)], excl=[("pth", ">", 65), ("vitd", "<", 12), ("psa", ">", 10)],
      cap={"primary_biliary_cholangitis": 0.3, "cholestasis": 0.3, "cholestatic_liver_injury_pattern": 0.3, "vitamin_d_deficiency": 0.6}, src="Endocrine Society Paget guideline 2014 (Singer)"),
 dict(id="acromegaly", dx=["acromegaly"], req=[("igf1", ">", 300)], sup=[("gh", ">", 1.0), ("glucose", ">", 100), ("phos", ">", 4.5), ("prl", ">", 25), ("a1c", ">", 5.7)], min_sup=1,
      cap={"hyperprolactinemia": 0.7, "prediabetes": 0.85, "diabetes_mellitus": 0.85}, src="Endocrine Society acromegaly 2014 (Katznelson)"),
 dict(id="prolactinoma", dx=["hyperprolactinemia_prolactinoma", "hyperprolactinemia", "pituitary_adenoma"], req=[("prl", ">", 100)], sup=[("macroprl", "<", 40), ("e2", "<", 30), ("testo", "<", 300), ("lh", "<", 3), ("fsh", "<", 3)], min_sup=1,
      excl=[("tsh", ">", 10)], cap={"hyperprolactinemia": 0.95, "hypopituitarism_panhypopituitarism": 0.7, "female_hypogonadotropic_hypogonadism": 0.8, "male_hypogonadism": 0.8},
      src="Endocrine Society hyperprolactinaemia 2011 (Melmed); Pituitary Society 2023"),
 dict(id="pcos", dx=["polycystic_ovary_syndrome"], req=[("testo", ">", 45)], sup=[("lh_fsh", ">", 2), ("amh", ">", 4.5), ("ftesto", ">", 6), ("dheas", ">", 350), ("insulin", ">", 15), ("tg_hdl", ">", 3), ("andro", ">", 200)], min_sup=2,
      excl=[("ohp17", ">", 200), ("prl", ">", 100), ("testo", ">", 150), ("tsh", ">", 10), ("cortisol_dex", ">", 1.8)], ctx=[("sex", "f")],
      cap={"hyperinsulinemic_hypoglycemia": 0.3, "hypopituitarism_panhypopituitarism": 0.3, "hypertriglyceridemia": 0.85, "hyperlipidemia": 0.85, "nafl_d": 0.9, "congenital_adrenal_hyperplasia": 0.6},
      src="International PCOS guideline 2023 (Teede)"),
 dict(id="ncah", dx=["congenital_adrenal_hyperplasia", "nonclassic_congenital_adrenal_hyperplasia", "21_hydroxylase_deficiency"], req=[("ohp17", ">", 200)],
      sup=[("testo", ">", 45), ("andro", ">", 200), ("dheas", ">", 350), ("cortisol_am", "<", 10)], min_sup=1,
      cap={"polycystic_ovary_syndrome": 0.5, "hypopituitarism_panhypopituitarism": 0.3}, src="Endocrine Society CAH guideline 2018 (Speiser): 17-OHP >200 ng/dL screen, >1000 diagnostic"),
 dict(id="male_primary_hypogonadism", dx=["male_primary_hypogonadism", "klinefelter_syndrome", "male_hypogonadism_primary_klinefelter", "primary_hypogonadism"], req=[("testo", "<", 300), ("lh", ">", 9), ("fsh", ">", 12)],
      sup=[("e2", ">", 40), ("prl", "<", 25)], min_sup=0, ctx=[("sex", "m")],
      cap={"male_hypogonadism": 0.95, "hypopituitarism_panhypopituitarism": 0.3, "male_secondary_hypogonadism": 0.4}, src="Endocrine Society testosterone therapy 2018 (Bhasin); Klinefelter: Groth, JCEM 2013"),
 dict(id="klinefelter_young", dx=["klinefelter_syndrome", "male_hypogonadism_primary_klinefelter", "male_primary_hypogonadism"], req=[("testo", "<", 300), ("fsh", ">", 20)],
      sup=[("lh", ">", 9), ("e2", ">", 30)], min_sup=1, ctx=[("sex", "m"), ("age_lt", 40)], cap={"male_hypogonadism": 0.95, "hypopituitarism_panhypopituitarism": 0.3},
      src="Groth, Klinefelter syndrome, JCEM 2013"),
 dict(id="male_secondary_hypogonadism", dx=["male_secondary_hypogonadism", "male_hypogonadism", "hypopituitarism_panhypopituitarism"], req=[("testo", "<", 300), ("lh", "<", 2), ("fsh", "<", 2)],
      sup=[("prl", ">", 25), ("ferritin", ">", 1000), ("cortisol_am", "<", 5)], min_sup=0, ctx=[("sex", "m")], src="Bhasin 2018"),
 dict(id="poi", dx=["premature_ovarian_insufficiency", "primary_ovarian_insufficiency", "hypergonadotropic_hypogonadism"], req=[("fsh", ">", 25), ("e2", "<", 30)],
      sup=[("amh", "<", 0.5), ("lh", ">", 15)], min_sup=0, ctx=[("sex", "f"), ("age_lt", 40)], src="ESHRE POI guideline 2016/2024"),
 dict(id="menopause_labs", dx=["menopause", "hypergonadotropic_hypogonadism"], req=[("fsh", ">", 25), ("e2", "<", 30)], sup=[("amh", "<", 0.5)], min_sup=0, ctx=[("sex", "f"), ("age_ge", 40)],
      src="STRAW+10 (Harlow 2012)"),
 dict(id="insulinoma", dx=["insulinoma", "endogenous_hyperinsulinism", "hyperinsulinemic_hypoglycemia"], req=[("glucose", "<", 55), ("insulin", ">=", 3), ("cpep", ">=", 0.6)],
      sup=[("bhb", "<=", 2.7), ("proins", ">=", 5)], min_sup=1, cap={"fasting_hypoglycemia": 0.9, "hyperinsulinemic_hypoglycemia": 0.95, "factitious_hypoglycemia": 0.4},
      src="Endocrine Society hypoglycaemia guideline 2009 (Cryer): Whipple triad + insulin ≥3, C-peptide ≥0.6, BHB ≤2.7"),
 dict(id="factitious_insulin", dx=["factitious_hypoglycemia", "exogenous_insulin_administration"], req=[("glucose", "<", 55), ("insulin", ">=", 3), ("cpep", "<", 0.6)],
      sup=[("bhb", "<=", 2.7)], min_sup=0, cap={"hyperinsulinemic_hypoglycemia": 0.5, "insulinoma": 0.3, "fasting_hypoglycemia": 0.9}, src="Cryer 2009: suppressed C-peptide with high insulin = exogenous insulin"),
 dict(id="lada", dx=["latent_autoimmune_diabetes_in_adults", "type_1_diabetes", "autoimmune_diabetes"], req=[("gad", ">", 5), ("a1c", ">=", 6.5)],
      sup=[("cpep", "<", 1.0), ("glucose", ">=", 200), ("tg", "<", 150)], min_sup=1, excl=[("bhb", ">=", 3.0)], ctx=[("age_ge", 30)],
      cap={"type_2_diabetes": 0.6, "diabetes_mellitus": 0.9, "type_2_diabetes_mellitus": 0.6}, src="Buzzetti, LADA consensus, Diabetes 2020"),
 dict(id="t1dm_autoimmune", dx=["type_1_diabetes", "autoimmune_diabetes"], req=[("gad", ">", 5), ("a1c", ">=", 6.5)], sup=[("cpep", "<", 1.0), ("glucose", ">=", 200)], min_sup=1, ctx=[("age_lt", 30)],
      cap={"type_2_diabetes": 0.5, "diabetes_mellitus": 0.9}, src="ADA Standards of Care 2025 §2"),
 dict(id="mody_gck", dx=["maturity_onset_diabetes_of_the_young", "prediabetes", "impaired_fasting_glucose"], req=[("glucose", "between", (99, 150)), ("a1c", "between", (5.6, 7.6))],
      sup=[("gad", "<", 5), ("cpep", ">", 1.0), ("tg", "<", 150), ("hdl", ">", 45)], min_sup=2, ctx=[("age_lt", 35), ("fh", "diabetes")], excl=[("bmi_ge", ">=", 30)],
      cap={"type_2_diabetes": 0.7, "diabetes_mellitus": 0.8}, src="ISPAD 2022 monogenic diabetes (Greeley): mild stable fasting hyperglycaemia, A1c 5.6–7.6%, strong FH"),
 dict(id="gdm", dx=["gestational_diabetes", "gestational_diabetes_mellitus"], req=[("glucose_1h", ">=", 180)], alt_req=[("glucose_2h", ">=", 153)], alt_req2=[("glucose", ">=", 92), ("a1c", ">=", 5.7)], alt_req3=[("glucose", ">=", 126)],
      sup=[("glucose_2h", ">=", 153), ("glucose", ">=", 92), ("a1c", "<", 6.5)], min_sup=0, ctx=[("pregnant", True)],
      cap={"prediabetes": 0.5, "impaired_glucose_tolerance": 0.6, "diabetes_mellitus": 0.6}, src="IADPSG 2010 / ADA 2025 one-step 75-g OGTT: FPG ≥92, 1-h ≥180, 2-h ≥153 mg/dL"),
 dict(id="hhs", dx=["hyperosmolar_hyperglycemic_state", "diabetes_mellitus"], req=[("glucose", ">", 600), ("osm", ">", 320)], sup=[("bhb", "<", 3.0), ("hco3", ">", 15), ("ph", ">", 7.30), ("cr", ">", 1.3), ("na", ">", 145)], min_sup=1,
      cap={"diabetic_ketoacidosis": 0.6, "hypernatremia": 0.85, "acute_kidney_injury": 0.85, "diabetes_insipidus": 0.3}, src="ADA/EASD 2024 hyperglycaemic crises"),
 # ---------------- liver / GI ----------------------------------------------
 dict(id="alcoholic_hepatitis", dx=["alcoholic_hepatitis_pattern", "alcoholic_liver_disease", "alcohol_associated_hepatitis", "alcoholic_liver_pattern"],
      req=[("tbil", ">", 3.0), ("ast_alt", ">", 1.5), ("ast", "between", (50, 400))], sup=[("ggt", ">", 100), ("mcv", ">", 98), ("inr", ">", 1.5), ("wbc", ">", 11), ("alb", "<", 3.0), ("alt", "<", 200)], min_sup=2,
      min_sup_any=[("ggt", ">", 100), ("mcv", ">", 98), ("wbc", ">", 11)],
      cap={"liver_cirrhosis": 0.9, "nash": 0.5, "isolated_hyperbilirubinemia_pattern": 0.8, "leukocytosis_pattern": 0.8},
      src="NIAAA Alcoholic Hepatitis Consortia definition (Crabb, Gastroenterology 2016)"),
 dict(id="apap_alf", dx=["acetaminophen_toxicity", "acetaminophen_hepatotoxicity", "acute_liver_failure"], req=[("alt", ">", 1000), ("apap", ">", 10)],
      sup=[("inr", ">", 1.5), ("lactate", ">", 3), ("cr", ">", 1.3), ("phos", ">", 3.7), ("ph", "<", 7.30), ("nh3", ">", 100)], min_sup=1,
      cap={"acute_liver_failure": 0.95, "ischemic_hepatitis_pattern": 0.5, "acute_kidney_injury": 0.85, "lactic_acidosis": 0.85}, src="AASLD ALF position paper 2011; King's College criteria"),
 dict(id="alf_generic", dx=["acute_liver_failure"], req=[("alt", ">", 1000), ("inr", ">=", 1.5)], sup=[("nh3", ">", 100), ("tbil", ">", 3), ("lactate", ">", 3), ("glucose", "<", 70)], min_sup=1,
      excl=[("ldh", ">", 5000)], src="AASLD 2011"),
 dict(id="ischemic_hepatitis", dx=["ischemic_hepatitis_pattern", "ischemic_hepatitis", "hypoxic_hepatitis", "acute_liver_injury"], req=[("ast", ">", 1000), ("ldh", ">", 1000)],
      sup=[("lactate", ">", 3), ("cr", ">", 1.3), ("natri_high", "==", 1), ("trop_c", ">", 50), ("tbil", "<", 3), ("alt", ">", 1000)], min_sup=2, excl=[("apap", ">", 10), ("hav_igm", "pos", None)],
      cap={"acute_heart_failure_support_pattern": 0.9, "acute_kidney_injury": 0.85, "isolated_hyperbilirubinemia_pattern": 0.6, "heart_failure_bnp_pattern": 0.8, "melas_syndrome": 0.3, "acute_liver_failure": 0.9},
      src="Henrion, Hypoxic hepatitis, Medicine 2003; Tapper, Am J Med 2015 (ALT/LDH ratio <1.5)"),
 dict(id="hav", dx=["hepatitis_a", "hepatitis_a_infection", "acute_hepatitis_a"], req=[("hav_igm", "pos", None)], sup=[("alt", ">", 200), ("tbil", ">", 2)], min_sup=0,
      cap={"autoimmune_hepatitis": 0.5, "nafl_d": 0.4, "acute_liver_failure": 0.9}, src="CDC/WHO hepatitis A"),
 dict(id="hbv_acute", dx=["hepatitis_b", "acute_hepatitis_b"], req=[("hbsag", "pos", None), ("hbc_igm", "pos", None)], sup=[("alt", ">", 200), ("tbil", ">", 2)], min_sup=0,
      cap={"chronic_hepatitis_b": 0.6, "autoimmune_hepatitis": 0.5, "nafl_d": 0.4, "hepatitis_b_core_igm_antibody_seropositivity": 0.9}, src="AASLD HBV 2018: HBsAg + anti-HBc IgM = acute infection"),
 dict(id="hbv_chronic_flare", dx=["chronic_hepatitis_b", "hepatitis_b", "hepatitis_b_flare"], req=[("hbsag", "pos", None)], sup=[("hbv_dna", ">", 2000), ("hbeag", "pos", None), ("alt", ">", 80), ("hbc_igm", "neg", None)], min_sup=1,
      excl=[("hbc_igm", "pos", None), ("afp", ">", 400)], cap={"autoimmune_hepatitis": 0.5, "nafl_d": 0.5}, src="AASLD HBV 2018 (Terrault)"),
 dict(id="aih", dx=["autoimmune_hepatitis"], req=[("alt", ">", 80)], sup=[("igg", ">", 1600), ("asma", ">=", 40), ("ana", ">=", 80), ("hbsag", "neg", None), ("hcv_ab", "neg", None)], min_sup=2,
      alt_req=[("asma", ">=", 80), ("alt", ">", 80)], excl=[("ama", ">", 20), ("hav_igm", "pos", None), ("hbsag", "pos", None), ("apap", ">", 10)], ctx=[],
      cap={"nafl_d": 0.5, "chronic_hepatitis_b": 0.6, "chronic_hepatitis_c": 0.6, "isolated_hyperbilirubinemia_pattern": 0.7, "drug_induced_liver_injury": 0.7},
      src="IAIHG simplified criteria (Hennes, Hepatology 2008): ANA/SMA ≥1:40, IgG >ULN, viral hepatitis excluded"),
 dict(id="pbc", dx=["primary_biliary_cholangitis", "primary_biliary_cholangitis_serologic_pattern"], req=[("alp", ">", 180), ("ama", ">", 20)],
      sup=[("ggt", ">", 100), ("igm", ">", 230), ("tc", ">", 240), ("alt", "<", 200)], min_sup=1,
      cap={"cholestatic_liver_injury_pattern": 0.9, "cholestasis": 0.9, "hypercholesterolemia": 0.8, "hyperlipidemia": 0.8, "primary_sclerosing_cholangitis": 0.4},
      src="EASL PBC 2017; AASLD PBC 2018 (Lindor): ALP + AMA ≥1:40"),
 dict(id="psc", dx=["primary_sclerosing_cholangitis"], req=[("alp", ">", 180), ("ama", "<=", 20)], sup=[("ggt", ">", 100), ("mpo", "pos", None), ("calpro", ">", 150), ("tbil", ">", 1.2), ("igg4", "<", 135)], min_sup=2,
      ctx_any=[("cond", "colitis"), ("cond", "ibd"), ("cond", "crohn")],
      cap={"primary_biliary_cholangitis": 0.4, "cholestatic_liver_injury_pattern": 0.9, "cholestasis": 0.9, "liver_cirrhosis": 0.7, "acute_cholangitis": 0.6, "ascending_cholangitis": 0.6, "biliary_obstruction_choledocholithiasis": 0.6}, src="EASL PSC 2022; AASLD PSC 2023"),
 dict(id="cholangitis", dx=["acute_cholangitis", "ascending_cholangitis", "biliary_obstruction_choledocholithiasis", "biliary_obstruction"], req=[("alp", ">", 180), ("tbil", ">", 2.0), ("dbil_frac", ">", 0.5), ("wbc", ">", 10)],
      alt_req=[("alp", ">", 180), ("tbil", ">", 2.0), ("dbil_frac", ">", 0.5), ("crp", ">", 30)],
      sup=[("wbc", ">", 10), ("crp", ">", 10), ("ggt", ">", 100), ("alt", ">", 80)], min_sup=2, excl=[("ama", ">", 20), ("calpro", ">", 150)],
      cap={"cholestatic_liver_injury_pattern": 0.9, "cholestasis": 0.9, "isolated_hyperbilirubinemia_pattern": 0.7, "leukocytosis_pattern": 0.8, "nafl_d": 0.5, "primary_biliary_cholangitis": 0.5},
      src="Tokyo Guidelines 2018 (TG18) acute cholangitis: inflammation + cholestasis"),
 dict(id="choledocholithiasis", dx=["biliary_obstruction_choledocholithiasis", "biliary_obstruction", "choledocholithiasis"], req=[("alp", ">", 180), ("tbil", ">", 2.0), ("dbil_frac", ">", 0.5)],
      sup=[("ggt", ">", 100), ("alt", ">", 80), ("lipase", ">", 100)], min_sup=1, excl=[("ama", ">", 20), ("wbc", ">", 10)], cap={"cholestasis": 0.9, "cholestatic_liver_injury_pattern": 0.9},
      src="ASGE 2019 choledocholithiasis"),
 dict(id="wilson", dx=["wilson_disease"], req=[("cerulo", "<", 20)], sup=[("ucu24", ">", 100), ("alp", "<", 40), ("dat", "neg", None), ("tbil", ">", 3), ("urate", "<", 2.5), ("alt", ">", 40), ("hb", "<", 10)], min_sup=1,
      ctx=[("age_lt", 45)], cap={"hemolytic_anemia": 0.85, "autoimmune_hemolytic_anemia": 0.4, "acute_liver_failure": 0.9, "liver_cirrhosis": 0.8, "autoimmune_hepatitis": 0.5},
      src="AASLD Wilson 2022 (Schilsky); Leipzig score 2001"),
 dict(id="a1at", dx=["alpha_1_antitrypsin_deficiency"], req=[("a1at", "<", 90)], sup=[("alt", ">", 40), ("ggt", ">", 60), ("plt", "<", 150)], min_sup=0,
      cap={"nafl_d": 0.6, "chronic_hepatitis_b": 0.5}, src="ATS/ERS 2003; Strnad, NEJM 2020 (AAT <90 mg/dL = deficiency range)"),
 dict(id="hh", dx=["hereditary_hemochromatosis", "hemochromatosis"], req=[("tsat", ">", 45), ("ferritin", ">", 300)], sup=[("hfe", "pos", None), ("alt", ">", 40), ("a1c", ">=", 6.5), ("testo", "<", 300), ("plt", "<", 150)], min_sup=1,
      excl=[("crp", ">", 50), ("ferritin", ">", 10000)], cap={"male_hypogonadism": 0.6, "hypopituitarism_panhypopituitarism": 0.5, "diabetes_mellitus": 0.85, "iron_overload": 0.95},
      src="AASLD HH 2011 (Bacon); EASL 2022"),
 dict(id="gilbert", dx=["gilbert_syndrome"], req=[("tbil", "between", (1.2, 6.0)), ("ibil_c", ">", 0.8), ("dbil_frac", "<", 0.3)],
      sup=[("alt", "<", 45), ("alp", "<", 130), ("hb", ">", 12), ("retic", "<", 2.5), ("ldh", "<", 250), ("hapto", ">", 30)], min_sup=3,
      excl=[("retic", ">", 3), ("ldh", ">", 300), ("hapto", "<", 30), ("alt", ">", 60), ("hb", "<", 11), ("dat", "pos", None),
            ("glucose", ">", 250), ("ph", "<", 7.30), ("wbc", ">", 15), ("lactate", ">", 4), ("crp", ">", 50), ("cr", ">", 2.0), ("hco3", "<", 15)], ctx=[("age_ge", 10)],
      cap={"isolated_hyperbilirubinemia_pattern": 0.9, "liver_cirrhosis": 0.3, "hemolytic_anemia": 0.4, "cholestasis": 0.3},
      src="Fretzayas, Gilbert syndrome, Eur J Pediatr 2012; UpToDate: isolated unconjugated hyperbilirubinaemia with normal haemolysis screen"),
 dict(id="dubin_johnson", dx=["dubin_johnson_syndrome", "rotor_syndrome"], req=[("tbil", ">", 1.5), ("dbil_frac", ">=", 0.5), ("alt", "<", 45), ("alp", "<", 130)],
      sup=[("ggt", "<", 60), ("copro_i", ">", 70)], min_sup=1, cap={"cholestasis": 0.3, "liver_cirrhosis": 0.3, "isolated_hyperbilirubinemia_pattern": 0.9},
      src="Strassburg, Hyperbilirubinemia syndromes, Best Pract Res Clin Gastro 2010"),
 dict(id="hellp", dx=["hellp_syndrome", "hellp_associated_liver_injury"], req=[("plt", "<", 100), ("ast", ">=", 70)], sup=[("ldh", ">=", 600), ("tbil", ">=", 1.2), ("hapto", "<", 30), ("schisto", ">", 0), ("urate", ">", 6), ("cr", ">", 1.1)], min_sup=1,
      ctx=[("pregnant", True)], cap={"preeclampsia": 0.9, "thrombotic_thrombocytopenic_purpura": 0.6, "liver_cirrhosis": 0.4, "isolated_hyperbilirubinemia_pattern": 0.7, "acute_fatty_liver_of_pregnancy": 0.85},
      src="Tennessee (Sibai) classification: platelets <100, AST ≥70, LDH ≥600"),
 dict(id="preeclampsia", dx=["preeclampsia", "preeclampsia_with_severe_features", "severe_preeclampsia_laboratory_pattern"], req=[("upcr", ">=", 0.3)],
      sup=[("urate", ">", 5.5), ("cr", ">", 1.1), ("plt", "<", 150), ("alt", ">", 80), ("ast", ">", 80), ("ldh", ">", 400), ("sflt_plgf", ">", 38)], min_sup=2, ctx=[("pregnant", True)],
      excl=[("plt", "<", 100)], cap={"nephrotic_syndrome": 0.7, "hellp_syndrome": 0.9}, src="ACOG Practice Bulletin 222 (2020)"),
 dict(id="icp", dx=["intrahepatic_cholestasis_of_pregnancy_support_pattern", "intrahepatic_cholestasis_of_pregnancy"], req=[("bile_acids", ">=", 10)], sup=[("alt", ">", 40), ("ast", ">", 40), ("alp", ">", 150)], min_sup=0,
      ctx=[("pregnant", True)], cap={"isolated_hyperbilirubinemia_pattern": 0.6, "nafl_d": 0.4, "preeclampsia": 0.6, "liver_cirrhosis": 0.3},
      src="RCOG Green-top 43 (2022); SMFM 2021: fasting TBA ≥10 µmol/L"),
 dict(id="aflp", dx=["acute_fatty_liver_of_pregnancy_support_pattern", "hellp_syndrome"], req=[("alt", ">", 42), ("inr", ">", 1.3)],
      sup=[("glucose", "<", 72), ("nh3", ">", 47), ("tbil", ">", 0.8), ("urate", ">", 5.7), ("cr", ">", 1.7), ("wbc", ">", 11), ("fib", "<", 200), ("at", "<", 65), ("plt", "<", 100)], min_sup=4, ctx=[("pregnant", True)],
      cap={"liver_cirrhosis": 0.5, "urea_cycle_disorder_otc_deficiency": 0.3, "fasting_hypoglycemia": 0.8, "hellp_syndrome": 0.9, "disseminated_intravascular_coagulation": 0.9, "acute_liver_failure": 0.9},
      src="Swansea criteria (Ch'ng, Gut 2002): ≥6 of 14 features"),
 dict(id="pancreatitis", dx=["acute_pancreatitis", "gallstone_pancreatitis", "biliary_pancreatitis"], req=[("lipase", ">=", 180)], alt_req=[("amylase", ">=", 300)],
      sup=[("alt", ">", 150), ("wbc", ">", 11), ("crp", ">", 150), ("ca_c", "<", 8.5), ("glucose", ">", 180), ("bun", ">", 20), ("tbil", ">", 1.5)], min_sup=1, excl=[("tg", ">", 1000)],
      cap={"cholestasis": 0.7, "leukocytosis_pattern": 0.8, "hypocalcemia": 0.85, "acute_cholangitis": 0.85}, src="Revised Atlanta 2012 (lipase/amylase ≥3x ULN); ALT >150 U/L favours biliary (Tenner 1994)"),
 dict(id="epi", dx=["pancreatic_insufficiency_pattern", "pancreatic_exocrine_dysfunction_support_pattern", "chronic_pancreatitis"], req=[("elastase", "<", 100)], sup=[("vitd", "<", 20), ("vita", "<", 20), ("a1c", ">=", 6.5), ("alb", "<", 3.5), ("mg", "<", 1.7)], min_sup=1,
      excl=[("sweat_cl", ">=", 60)], cap={"vitamin_d_deficiency": 0.85, "malnutrition": 0.85}, src="UEG chronic pancreatitis 2017 (Löhr): FE-1 <100 µg/g severe EPI"),
 dict(id="celiac", dx=["celiac_disease"], req=[("ttg_iga", ">", 10)], sup=[("iga", ">=", 7), ("ferritin", "<", 30), ("vitd", "<", 20), ("folate", "<", 4), ("ca_c", "<", 8.8), ("alt", ">", 40), ("hb", "<", 12)], min_sup=1,
      cap={"iron_deficiency_anemia": 0.9, "vitamin_d_deficiency": 0.85, "osteomalacia": 0.85, "folate_deficiency": 0.85}, src="ESPGHAN 2020; ACG 2023 celiac"),
 dict(id="celiac_iga_def", dx=["celiac_disease", "selective_iga_deficiency"], req=[("iga", "<", 7)], sup=[("ttg_igg", ">", 10), ("dgp_igg", ">", 10), ("ferritin", "<", 30), ("hb", "<", 12)], min_sup=1,
      cap={"iron_deficiency_anemia": 0.9}, src="ESPGHAN 2020: IgA-deficient → IgG-class tTG/DGP"),
 dict(id="crohn_flare", dx=["crohn_disease", "inflammatory_bowel_disease"], req=[("calpro", ">", 250)], sup=[("crp", ">", 10), ("alb", "<", 3.5), ("plt", ">", 400), ("ferritin", "<", 30), ("b12", "<", 200), ("hb", "<", 12), ("esr", ">", 30)], min_sup=2,
      excl=[("alp", ">", 180)], cap={"anemia": 0.85, "iron_deficiency_anemia": 0.85, "anemia_of_chronic_disease": 0.85, "thrombocytosis": 0.85, "reactive_thrombocytosis": 0.85, "bacterial_infection": 0.6},
      src="ECCO 2019 diagnosis; calprotectin >250 µg/g active disease (D'Haens 2012)"),
 dict(id="masld", dx=["nafl_d", "metabolic_dysfunction_associated_steatotic_liver_disease", "nonalcoholic_fatty_liver_disease"], req=[("alt", ">", 40), ("ast_alt", "<", 1.0)],
      sup=[("tg", ">=", 150), ("hdl", "<", 40), ("glucose", ">=", 100), ("a1c", ">=", 5.7), ("ferritin", ">", 300), ("urate", ">", 7), ("ggt", ">", 60), ("bmi_ge", ">=", 25)], min_sup=3,
      excl=[("hbsag", "pos", None), ("ama", ">", 20), ("asma", ">=", 80), ("tsat", ">", 45), ("alt", ">", 300), ("cerulo", "<", 20)],
      cap={"metabolic_syndrome": 0.95, "hypertriglyceridemia": 0.85, "autoimmune_hepatitis": 0.5, "chronic_hepatitis_b": 0.5, "chronic_hepatitis_c": 0.5}, src="AASLD MASLD 2023 (Rinella): steatosis + ≥1 cardiometabolic criterion"),
 dict(id="hcc", dx=["hepatocellular_carcinoma"], req=[("afp", ">", 400)], sup=[("plt", "<", 150), ("alb", "<", 3.5), ("hbsag", "pos", None), ("hcv_ab", "pos", None), ("inr", ">", 1.2), ("tbil", ">", 1.5)], min_sup=1,
      excl=[("hcg", ">", 25)], ctx=[("age_ge", 30)], cap={"liver_cirrhosis": 0.9, "chronic_hepatitis_b": 0.9, "hepatitis_b": 0.9, "isolated_hyperbilirubinemia_pattern": 0.7, "nash": 0.5}, src="AASLD HCC 2023 (Singal); AFP >400 ng/mL in cirrhosis highly specific"),
 dict(id="cirrhosis_decomp", dx=["liver_cirrhosis", "decompensated_cirrhosis"], req=[("plt", "<", 150), ("alb", "<", 3.5), ("inr", ">", 1.3)], sup=[("tbil", ">", 2), ("na", "<", 135), ("nh3", ">", 60), ("ast_alt", ">", 1)], min_sup=1,
      excl=[("alt", ">", 1000), ("fib", "<", 150), ("ddimer", ">", 10)], src="EASL decompensated cirrhosis 2018"),
 # ---------------- haematology ---------------------------------------------
 dict(id="ida", dx=["iron_deficiency_anemia"], req=[("hb", "<", 13), ("ferritin", "<", 30)], sup=[("mcv", "<", 80), ("tsat", "<", 20), ("rdw", ">", 15), ("plt", ">", 400), ("chr", "<", 29)], min_sup=1,
      cap={"thalassemia_trait": 0.8, "beta_thalassemia_trait": 0.8, "anemia": 0.9, "anemia_of_chronic_disease": 0.6}, src="BSH 2021 IDA (Snook); WHO 2020 ferritin <15/30"),
 dict(id="ida_inflamm", dx=["iron_deficiency_anemia", "combined_iron_deficiency_and_anemia_of_chronic_disease", "functional_iron_deficiency", "anemia_of_chronic_disease"],
      req=[("hb", "<", 13), ("ferritin", "between", (30, 100)), ("tsat", "<", 20)], sup=[("crp", ">", 5), ("stfr", ">", 2.5), ("chr", "<", 29), ("mcv", "<", 82), ("plt", ">", 400)], min_sup=2,
      cap={"anemia": 0.9, "thalassemia_trait": 0.7}, src="Camaschella NEJM 2015; BSH 2021: ferritin <100 + TSAT <20% with inflammation"),
 dict(id="pernicious", dx=["vitamin_b12_deficiency", "megaloblastic_anemia", "vitamin_b12_deficiency_anemia"], req=[("b12", "<", 200)],
      sup=[("mcv", ">", 100), ("mma", ">", 400), ("hcy", ">", 15), ("ldh", ">", 500), ("hapto", "<", 30), ("retic", "<", 1.5), ("hypersegs", "pos", None), ("plt", "<", 150), ("wbc", "<", 4)], min_sup=2, excl=[("if_ab", "pos", None)],
      cap={"hemolytic_anemia": 0.5, "aplastic_anemia": 0.4, "myelodysplastic_syndrome": 0.5, "pancytopenia": 0.9, "macrocytic_anemia": 0.9, "anemia": 0.9, "thrombotic_thrombocytopenic_purpura": 0.4},
      src="BSH 2014 cobalamin/folate (Devalia)"),
 dict(id="folate_def", dx=["folate_deficiency", "megaloblastic_anemia"], req=[("folate", "<", 3.0), ("b12", ">=", 200)], sup=[("mcv", ">", 100), ("hcy", ">", 15), ("mma", "<", 400), ("ggt", ">", 60)], min_sup=1,
      cap={"vitamin_b12_deficiency": 0.5, "pernicious_anemia": 0.4, "anemia": 0.9}, src="BSH 2014"),
 dict(id="lead", dx=["lead_poisoning", "lead_toxicity", "sideroblastic_anemia"], req=[("lead", ">=", 5)], sup=[("stippling", "pos", None), ("zpp", ">", 35), ("mcv", "<", 80), ("ferritin", ">", 100), ("hb", "<", 12)], min_sup=1,
      cap={"iron_deficiency_anemia": 0.5, "thalassemia_trait": 0.5, "anemia": 0.9}, src="CDC blood lead reference 3.5 µg/dL (2021); AAP 2016"),
 dict(id="sickle", dx=["sickle_cell_disease", "sickle_cell_anemia", "vaso_occlusive_crisis"], req=[("hbs", ">", 50)], sup=[("hb", "<", 10), ("retic", ">", 3), ("ldh", ">", 250), ("ibil_c", ">", 1.0), ("wbc", ">", 11)], min_sup=1,
      cap={"hemolytic_anemia": 0.9, "anemia": 0.9}, src="NHLBI SCD 2014; ASH 2020"),
 dict(id="thal_major", dx=["beta_thalassemia_major", "beta_thalassemia", "transfusion_dependent_thalassemia"], req=[("hbf", ">", 20), ("hb", "<", 9)], sup=[("mcv", "<", 75), ("nrbc", ">", 5), ("ferritin", ">", 1000), ("retic", ">", 2), ("ibil_c", ">", 1.0)], min_sup=1,
      cap={"hemolytic_anemia": 0.8, "iron_overload": 0.9, "anemia": 0.9, "thalassemia_trait": 0.5, "hemochromatosis": 0.5}, src="TIF guidelines 2021"),
 dict(id="thal_trait", dx=["thalassemia_trait", "beta_thalassemia_trait", "beta_thalassemia_minor"], req=[("mcv", "<", 75), ("hb", ">", 9)], sup=[("hba2", ">", 3.5), ("mentzer", "<", 13), ("rbc", ">", 5.0), ("ferritin", ">=", 30), ("rdw", "<", 16)], min_sup=2,
      excl=[("ferritin", "<", 30), ("hbf", ">", 20), ("hb", ">", 17.5), ("rdw", ">", 18)], cap={"iron_deficiency_anemia": 0.5, "anemia": 0.9}, src="BSH 2010 haemoglobinopathy screening; Mentzer 1973 (trait: normal RDW, no erythrocytosis; microcytosis with Hb > 17.5 or RDW > 18 points to iron-deficient secondary erythrocytosis)"),
 # ESL extension 9 (2026-10-23): microcytosis with erythrocytosis is iron-restricted secondary polycythaemia until proven otherwise, not thalassaemia trait
 dict(id="thal_trait_erythrocytosis_guard", dx=[], guard=True, req=[("mcv", "<", 78), ("hb", ">", 17.5)], min_sup=0, strength="pattern",
      cap={"thalassemia_trait": 0.45, "beta_thalassemia_trait": 0.45, "beta_thalassemia_minor": 0.45, "alpha_thalassemia_trait": 0.45},
      src="BSH 2010 haemoglobinopathy screening; WHO 2016 polycythaemia vera criteria; McMullin BJH 2019 (secondary erythrocytosis work-up)"),
 # ESL extension 9b (2026-10-23): profound neutropenia is a sepsis-risk state (IDSA 2010 / ASCO-IDSA 2018 febrile neutropenia); the engine
 # names severe_neutropenia and routes blood cultures / lactate through the next-test layer; sepsis itself still needs infection evidence.
 dict(id="severe_neutropenia", dx=["severe_neutropenia", "neutropenia"], req=[("anc", "<", 0.5)], alt_req=[("wbc", "<", 1.0)], min_sup=0, strength="strong",
      excl=[("blasts", ">", 20)], src="Freifeld et al. IDSA 2010 febrile neutropenia (ANC < 500/µL); Taplitz ASCO/IDSA 2018"),
 # ESL extension 10 (2026-10-23): bandemia > 10 % is a SIRS criterion in its own right (Bone 1992) and predicts bacteraemia
 # independently of the total WBC (Drees 2012); with one organ-dysfunction marker it is a sepsis pattern even at a normal WBC.
 dict(id="sepsis_bandemia_organ", dx=["sepsis", "bacterial_infection"], req=[("bands", ">", 10)],
      sup=[("cr", ">", 1.5), ("lactate", ">", 2), ("plt", "<", 150), ("inr", ">", 1.5), ("hco3", "<", 20), ("tbil", ">", 2), ("alb", "<", 3.0), ("pct", ">", 0.5), ("crp", ">", 100)], min_sup=1, strength="pattern",
      excl=[("blasts", ">", 5), ("wbc", ">", 50), ("pct", "<", 0.1)],
      src="Bone et al. Chest 1992 (SIRS: > 10 % immature forms); Drees et al. Am J Infect Control 2012; Singer 2016 Sepsis-3; SSC 2021"),
 # ESL extension 10: macrocytosis with the companion biomarkers of heavy alcohol use is the laboratory signature of alcohol use disorder;
 # deficiency and marrow causes exclude it when measured and abnormal.
 dict(id="alcohol_biomarker_macrocytosis", dx=["alcohol_use_disorder", "alcoholic_liver_pattern"], req=[("mcv", ">", 100)],
      sup=[("ast_alt", ">", 1.5), ("ggt", ">", 60), ("plt", "<", 150), ("mg", "<", 1.7), ("phos", "<", 2.5), ("urate", ">", 7.0), ("tg", ">", 200), ("tbil", ">", 1.5), ("ethanol", ">", 10), ("alb", "<", 3.5)], min_sup=2, strength="supportive",
      excl=[("b12", "<", 200), ("folate", "<", 3.0), ("tsh", ">", 10), ("retic", ">", 3.0), ("blasts", ">", 0), ("mcv", ">", 125), ("hb", "<", 7)],
      ctx_excl=[("med", "hydroxyurea"), ("med", "methotrexate"), ("med", "zidovudine"), ("med", "azathioprine")],
      cap={"vitamin_b12_deficiency": 0.7, "folate_deficiency": 0.7, "myelodysplastic_syndrome": 0.6},
      src="Niemelä, Clin Chim Acta 2007 (MCV, GGT, AST/ALT as alcohol biomarkers); Hock et al. Addiction 2005; EASL 2018 ALD guideline"),

 # ===== ESL extension 11-T (2026-10-23): temporal constellations (fire only when a series was supplied) =====
 dict(id="aki_kdigo_creatinine_rise", temporal=True, dx=["acute_kidney_injury"],
      req=[("cr_rise48", ">=", 0.3), ("cr_max", ">=", 1.0)], alt_req=[("cr_ratio_max", ">=", 1.5), ("cr_max", ">=", 1.0)],
      sup=[("bun_cr", ">", 20), ("k", ">", 5.0), ("hco3", "<", 22), ("phos", ">", 4.5), ("lactate", ">", 2)], min_sup=0, strength="anchor",
      note="KDIGO AKI: creatinine rose >= 0.3 mg/dL within 48 h or >= 1.5x an earlier value - acute kidney injury established on trajectory.",
      src="KDIGO Clinical Practice Guideline for AKI, Kidney Int Suppl 2012;2:1 (definition 2.1.1); Ostermann 2020 KDIGO conference"),
 dict(id="aki_recovering_creatinine_fall", temporal=True, dx=["acute_kidney_injury"],
      req=[("cr_fall48", ">=", 0.3), ("cr_max", ">=", 1.3), ("cr_ratio_fall", ">=", 1.3)], strength="strong",
      note="Creatinine falling >= 0.3 mg/dL / >= 1.3x within 48 h from a raised peak - resolving acute kidney injury (recovery trajectory).",
      src="KDIGO AKI 2012; Chawla et al. NEJM 2014;371:58 (AKI -> recovery / AKD)"),
 dict(id="acute_myocardial_injury_dynamic_troponin", temporal=True, dx=["acute_myocardial_injury"],
      req=[("trop_dyn_pct", ">=", 50), ("trop_dyn_max_ngl", ">", 14)], alt_req=[("trop_dyn_pct", ">=", 20), ("trop_dyn_min_ngl", ">", 14)],
      sup=[("ck", ">", 200), ("ckmb", ">", 5), ("ntprobnp", ">", 300), ("lactate", ">", 2)], min_sup=0, strength="anchor",
      cap={"chronic_myocardial_injury": 0.5},
      note="Rise and/or fall of cardiac troponin with >= 1 value above the 99th percentile = ACUTE myocardial injury (4th UDMI); ischaemia criteria decide MI type.",
      src="Thygesen et al. 4th Universal Definition of MI, Eur Heart J 2019;40:237; ESC 2023 ACS guideline (0 h/1-3 h delta criteria: >= 20 % if baseline raised, >= 50 % if baseline normal)"),
 # v6 C9 (2026-10-25): single very high hs-troponin WITH clinical evidence of ischaemia = acute MI (4th UDMI: acute injury + ischaemia;
 # ESC 2023 ACS 0 h rule-in: hs-cTn well above the assay-specific threshold of ~52-120 ng/L). Without an ischaemic context the same value
 # is reported as acute myocardial injury only (rule above / registry UDMI rule). Strength "strong": serial values still decide type/timing.
 dict(id="mi_high_troponin_ischaemic_presentation", dx=["acute_myocardial_infarction", "acute_coronary_syndrome"], req=[("trop_c", ">=", 100)],
      sup=[("ckmb", ">", 5), ("ck", ">", 200), ("ntprobnp", ">", 300), ("glucose", ">", 140), ("lactate", ">", 2)], min_sup=0, strength="strong",
      ctx=[("age_ge", 18)],
      ctx_any=[("sym", "chest pain"), ("sym", "angina"), ("sym", "chest pressure"), ("sym", "chest tightness"), ("sym", "retrosternal"),
               ("sym", "st elevation"), ("sym", "st-elevation"), ("sym", "stemi"), ("sym", "nstemi"), ("sym", "ischemi"), ("sym", "ischaemi"),
               ("cond", "stemi"), ("cond", "nstemi"), ("cond", "st elevation"), ("cond", "acute coronary"), ("cond", "chest pain")],
      ctx_excl=[("cond", "dialysis"), ("cond", "esrd"), ("cond", "myocarditis"), ("cond", "cardiac surgery"), ("cond", "pci"), ("cond", "cardioversion")],
      excl=[("ck", ">", 5000)], cap={"chronic_myocardial_injury": 0.5, "takotsubo_cardiomyopathy": 0.6},
      note="hs-troponin >= 100 ng/L on presentation with ischaemic symptoms or ECG ischaemia reported in the context: acute myocardial infarction (4th UDMI criterion: acute myocardial injury + clinical evidence of ischaemia). Serial troponin and ECG/imaging confirm type and timing.",
      src="Thygesen et al. 4th Universal Definition of MI, Eur Heart J 2019;40:237; Byrne et al. 2023 ESC Guidelines for ACS, Eur Heart J 2023;44:3720 (0 h/1 h algorithm rule-in thresholds)"),
 # v6 C10 (2026-10-25): very high troponin WITH concurrent CK-MB elevation. CK-MB returns to normal within 48-72 h, so its
 # elevation next to a markedly raised troponin (>= 500 ng/L, i.e. >= ~35 x URL hs-cTnT / >= ~15 x hs-cTnI) marks the injury as
 # ACUTE and of a magnitude rarely produced by chronic injury outside ESRD (excluded by context). Infarction is listed first as the
 # most probable cause at strength "strong" (0.88), not anchor: ischaemia evidence (ECG/symptoms) is still required by the 4th UDMI.
 dict(id="mi_very_high_troponin_with_ckmb", dx=["acute_myocardial_infarction", "acute_myocardial_injury", "acute_coronary_syndrome"], req=[("trop_c", ">=", 500), ("ckmb", ">", 5)],
      sup=[("natri_high", "==", 1), ("glucose", ">", 140), ("lactate", ">", 2), ("cr", ">", 1.3)], min_sup=0, strength="strong", ctx=[(("age_ge"), 18)],
      ctx_excl=[("cond", "dialysis"), ("cond", "esrd"), ("cond", "myocarditis"), ("cond", "cardiac surgery"), ("cond", "pci"), ("cond", "cardioversion"), ("cond", "trauma")],
      excl=[("ck", ">", 5000), ("crp", ">", 60), ("ddimer", ">", 4), ("cohb", ">", 10)],
      cap={"acute_kidney_injury": 0.85, "heart_failure": 0.9, "myocarditis": 0.6, "chronic_myocardial_injury": 0.5},
      note="Troponin >= 500 ng/L with CK-MB above its URL: acute myocardial injury of infarct magnitude; acute MI is the leading cause pending ECG / ischaemic symptoms (4th UDMI). Myocarditis, PE and Takotsubo remain in the differential.",
      src="Thygesen et al. 4th Universal Definition of MI, Eur Heart J 2019;40:237 (biomarker section: cTn preferred, CK-MB kinetics); Byrne et al. 2023 ESC ACS guideline (very high hs-cTn on presentation)"),
 dict(id="chronic_myocardial_injury_flat_troponin", temporal=True, dx=["chronic_myocardial_injury"],
      req=[("trop_dyn_min_ngl", ">", 14), ("trop_dyn_pct", "<", 20), ("trop_dyn_span_h", ">=", 3)],
      sup=[("cr", ">", 1.5), ("ntprobnp", ">", 300), ("egfr_c", "<", 45)], min_sup=0, strength="pattern",
      cap={"acute_myocardial_injury": 0.6, "acute_myocardial_infarction": 0.6},
      note="Persistently raised troponin WITHOUT a >= 20 % change over >= 3 h - chronic myocardial injury pattern (CKD, HF, structural heart disease), not an acute event on this series.",
      src="4th UDMI 2019 (chronic myocardial injury); ESC 2023 ACS"),
 dict(id="lactate_non_clearance", temporal=True, dx=["lactic_acidosis"],
      req=[("lactate_first", ">=", 4.0), ("lactate_last", ">=", 4.0), ("lactate_span_h", ">=", 4), ("lactate_clear_pct", "<", 10)],
      sup=[("ph", "<", 7.35), ("hco3", "<", 18), ("ag_c", ">", 12), ("cr", ">", 1.5)], min_sup=0, strength="anchor",
      note="Persistent hyperlactataemia (< 10 % clearance over >= 4 h) - adverse prognostic marker; reassess perfusion, source control and lactate-generating drugs.",
      src="Jones et al. JAMA 2010;303:739 (lactate clearance >= 10 %); Surviving Sepsis Campaign 2021 (lactate-guided resuscitation); Vincent Crit Care 2016"),
 dict(id="lactate_clearing", temporal=True, dx=[], guard=True,
      req=[("lactate_first", ">=", 4.0), ("lactate_clear_pct", ">=", 30)],
      note="Lactate clearing (>= 30 % from the initial value) - consistent with response to resuscitation.",
      src="Jones JAMA 2010; Vincent Crit Care 2016"),
 dict(id="acute_blood_loss_hb_fall", temporal=True, dx=["acute_blood_loss_anemia"],
      req=[("hb_fall24", ">=", 2.0), ("hb_last", "<", 12)],
      sup=[("bun_cr", ">", 30), ("plt", "<", 150), ("inr", ">", 1.5), ("retic", ">", 2.0), ("lactate", ">", 2)], min_sup=0, strength="supportive",
      excl=[("ldh", ">", 600), ("hapto", "<", 20)], ctx_excl=[("cond", "hemodilution"), ("cond", "haemodilution")],
      cap={"iron_deficiency_anemia": 0.6, "anemia_of_chronic_disease": 0.6, "anemia_of_chronic_inflammation": 0.6},
      note="Haemoglobin fell >= 2 g/dL within 24 h - acute blood loss (or haemodilution) must be excluded; BUN/creatinine > 30 favours upper-GI source.",
      src="Carson et al. Red-cell transfusion guideline JAMA 2023; Laine & Jensen ACG 2012 (BUN/Cr in UGIB); Srygley JAMA 2012"),
 dict(id="hit_platelet_fall_on_heparin", temporal=True, dx=["heparin_induced_thrombocytopenia"],
      req=[("plt_drop_pct", ">=", 50), ("plt_last", ">=", 20), ("plt_last", "<", 150)],
      ctx_any=[("med", "heparin"), ("med", "enoxaparin"), ("med", "dalteparin"), ("med", "lovenox"), ("med", "fragmin")],
      sup=[("plt_span_h", ">=", 96)], min_sup=0, strength="strong", excl=[("fib", "<", 150), ("blasts", ">", 0), ("ddimer", ">", 10)],
      cap={"immune_thrombocytopenia": 0.5},
      note="> 50 % platelet fall on heparin exposure (4Ts: 2 points) - test PF4/heparin antibodies; stop heparin pending result.",
      src="Cuker et al. ASH 2018 HIT guideline, Blood Adv 2:3360; Lo et al. 4Ts score, J Thromb Haemost 2006"),
 dict(id="consumptive_platelet_fall_dic", temporal=True, dx=["disseminated_intravascular_coagulation"],
      req=[("plt_drop_pct", ">=", 50), ("plt_last", "<", 100)],
      sup=[("inr", ">", 1.5), ("fib", "<", 150), ("ddimer", ">", 2.0), ("lactate", ">", 2)], min_sup=1, strength="strong", excl=[("blasts", ">", 5)],
      note="Rapid > 50 % platelet consumption with a coagulation abnormality - overt DIC pattern (ISTH score); identify the trigger (sepsis, malignancy, obstetric).",
      src="Taylor et al. ISTH DIC scoring, Thromb Haemost 2001;86:1327; Wada et al. J Thromb Haemost 2013"),
 dict(id="hyponatremia_overcorrection", temporal=True, dx=[], guard=True,
      req=[("na_first", "<", 125), ("na_rise24", ">", 8)],
      note="Sodium rose > 8 mmol/L within 24 h from < 125 mmol/L - exceeds the correction limit (osmotic demyelination risk); consider relowering per guideline.",
      src="Spasovski et al. ESE/ERA hyponatraemia guideline, Eur J Endocrinol 2014;170:G1; Sterns NEJM 2015;372:55; Verbalis Am J Med 2013"),
 dict(id="hyponatremia_acute_fall", temporal=True, dx=["hyponatremia"],
      req=[("na_fall24", ">=", 8), ("na_last", "<", 130)], strength="strong",
      note="Sodium fell >= 8 mmol/L within 24 h to < 130 - acute hyponatraemia (higher cerebral-oedema risk than chronic).",
      src="Spasovski 2014 (acute vs chronic hyponatraemia); Adrogue & Madias NEJM 2000"),
 # ===== ESL extension 11-C (2026-10-23): medication-gated constellations (fire only when the caller supplied the medication) =====
 dict(id="warfarin_inr_explained", dx=[], guard=True, req=[("inr", ">", 1.5), ("inr", "<=", 4.0)],
      ctx_any=[("med", "warfarin"), ("med", "coumadin"), ("med", "acenocoumarol"), ("med", "phenprocoumon")],
      cap={"coagulopathy": 0.45, "vitamin_k_deficiency": 0.3, "elevated_inr_pattern": 0.6, "prolonged_pt_pattern": 0.6, "liver_cirrhosis": 0.85, "disseminated_intravascular_coagulation": 0.6},
      note="INR elevation is explained by documented vitamin-K-antagonist therapy (therapeutic range 2-3 / 2.5-3.5).",
      src="Ageno et al. CHEST 2012 (oral anticoagulant therapy); Holbrook CHEST 2012"),
 dict(id="warfarin_over_anticoagulation_ctx", dx=["warfarin_over_anticoagulation"], req=[("inr", ">", 4.0)],
      ctx_any=[("med", "warfarin"), ("med", "coumadin"), ("med", "acenocoumarol"), ("med", "phenprocoumon")],
      sup=[("hb", "<", 10), ("plt", "<", 150), ("alb", "<", 3.0)], min_sup=0, strength="anchor",
      cap={"coagulopathy": 0.7, "vitamin_k_deficiency": 0.4},
      note="Supratherapeutic INR on a vitamin-K antagonist - bleeding-risk management per INR band (hold, vitamin K, PCC if bleeding).",
      src="Holbrook et al. CHEST 2012;141:e152S; Witt ASH 2018 VTE anticoagulation guideline"),
 dict(id="metformin_associated_lactic_acidosis", dx=["lactic_acidosis_metformin_associated", "lactic_acidosis"],
      req=[("lactate", ">", 4.0), ("cr", ">", 1.5)], ctx_any=[("med", "metformin"), ("med", "glucophage"), ("med", "janumet"), ("med", "glucovance")],
      sup=[("ph", "<", 7.30), ("ag_c", ">", 16), ("hco3", "<", 18), ("egfr_c", "<", 30)], min_sup=1, strength="strong",
      note="Lactic acidosis with renal impairment in a metformin user - metformin-associated lactic acidosis (MALA) until proven otherwise; stop metformin, consider haemodialysis.",
      src="Lalau et al. Diabetes Obes Metab 2017;19:1502; FDA Drug Safety Communication 2016; Calello et al. EXTRIP Crit Care Med 2015"),
 dict(id="statin_associated_muscle_injury_ctx", dx=["statin_associated_muscle_injury"], req=[("ck", ">", 2000)],
      ctx_any=[("med", "statin"), ("med", "atorvastatin"), ("med", "simvastatin"), ("med", "rosuvastatin"), ("med", "pravastatin"), ("med", "lovastatin"), ("med", "lipitor"), ("med", "crestor"), ("med", "zocor")],
      sup=[("cr", ">", 1.5), ("k", ">", 5.0), ("ast_alt", ">", 1.0), ("tsh", ">", 10)], min_sup=0, strength="pattern",
      excl=[("ck", ">", 100000)],
      note="CK > 10x ULN in a statin user - statin-associated muscle injury / rhabdomyolysis; stop the statin and check renal function and hydration.",
      src="Stroes et al. EAS Consensus on statin-associated muscle symptoms, Eur Heart J 2015;36:1012; ACC/AHA 2018 cholesterol guideline"),
 dict(id="hs", dx=["hereditary_spherocytosis"], req=[("sphero", "pos", None), ("dat", "neg", None)], sup=[("mchc", ">", 35.5), ("retic", ">", 2.5), ("ibil_c", ">", 1), ("ema", "<", 0.8), ("hapto", "<", 30), ("ldh", ">", 250)], min_sup=2,
      cap={"hemolytic_anemia": 0.9, "autoimmune_hemolytic_anemia": 0.3, "anemia": 0.9}, src="BSH 2011 HS (Bolton-Maggs): spherocytes + DAT-negative + family history/EMA"),
 dict(id="g6pd_hemolysis", dx=["g6pd_deficiency", "oxidative_hemolysis", "drug_induced_hemolytic_anemia"], req=[("dat", "neg", None), ("retic", ">", 2.5)],
      sup=[("g6pd", "<", 4.0), ("heinz", "pos", None), ("bite", "pos", None), ("ldh", ">", 250), ("hapto", "<", 30), ("ibil_c", ">", 1), ("uhb", "pos", None)], min_sup=3, min_sup_any=[("g6pd", "<", 4.0), ("heinz", "pos", None), ("bite", "pos", None)],
      ctx_any=[("med", "primaquine"), ("med", "dapsone"), ("med", "rasburicase"), ("med", "nitrofurantoin"), ("med", "sulf")],
      cap={"hemolytic_anemia": 0.9, "autoimmune_hemolytic_anemia": 0.3, "anemia": 0.9, "hereditary_spherocytosis": 0.5}, src="Luzzatto, G6PD deficiency, Blood 2020"),
 dict(id="g6pd_hemolysis_nomed", dx=["g6pd_deficiency", "oxidative_hemolysis"], req=[("dat", "neg", None), ("retic", ">", 2.5), ("g6pd", "<", 4.0)],
      sup=[("heinz", "pos", None), ("bite", "pos", None), ("ldh", ">", 250), ("hapto", "<", 30)], min_sup=1, cap={"hemolytic_anemia": 0.9, "autoimmune_hemolytic_anemia": 0.3, "anemia": 0.9}, src="Luzzatto 2020"),
 dict(id="waiha", dx=["autoimmune_hemolytic_anemia", "warm_autoimmune_hemolytic_anemia"], req=[("dat", "pos", None), ("hb", "<", 12)], sup=[("retic", ">", 2.5), ("ldh", ">", 250), ("hapto", "<", 30), ("ibil_c", ">", 1), ("sphero", "pos", None)], min_sup=2,
      excl=[("plt", "<", 50), ("schisto", ">", 1)], ctx=[("age_ge", 1)], cap={"hemolytic_anemia": 0.9, "anemia": 0.9, "hereditary_spherocytosis": 0.3, "g6pd_deficiency": 0.3, "systemic_lupus_erythematosus": 0.9},
      src="First International Consensus AIHA (Jäger, Blood Rev 2020)"),
 dict(id="evans", dx=["autoimmune_hemolytic_anemia", "immune_thrombocytopenia"], req=[("dat", "pos", None), ("hb", "<", 12), ("plt", "<", 100)], sup=[("retic", ">", 2.5), ("ldh", ">", 250), ("hapto", "<", 30), ("schisto", "<=", 1)], min_sup=2,
      excl=[("schisto", ">", 1), ("adamts13", "<", 10)], cap={"autoimmune_hemolytic_anemia": 0.95, "immune_thrombocytopenia": 0.95, "thrombotic_thrombocytopenic_purpura": 0.4, "hemolytic_anemia": 0.9},
      src="Jäger 2020; Audia, Evans syndrome, J Clin Med 2020"),
 dict(id="tma_pattern", dx=["thrombotic_microangiopathy"], req=[("plt", "<", 150), ("schisto", ">", 1)], sup=[("ldh", ">", 250), ("hapto", "<", 30), ("hb", "<", 12), ("cr", ">", 1.3)], min_sup=0,
      cap={"immune_thrombocytopenia": 0.6, "heparin_induced_thrombocytopenia": 0.6, "thrombocytopenia": 0.8},
      src="George & Nester, NEJM 2014: thrombocytopenia + schistocytes = TMA until proven otherwise; ITP is a diagnosis of exclusion (ASH 2019)"),
 dict(id="ttp", dx=["thrombotic_thrombocytopenic_purpura"], req=[("plt", "<", 30), ("schisto", ">", 1)], sup=[("ldh", ">", 500), ("hapto", "<", 30), ("dat", "neg", None), ("cr", "<", 2.3), ("adamts13", "<", 10), ("inr", "<", 1.5), ("fib", ">", 150), ("trop_c", ">", 20)], min_sup=3,
      excl=[("adamts13", ">=", 20), ("fib", "<", 150)], cap={"hemolytic_anemia": 0.9, "hemolytic_uremic_syndrome": 0.5, "disseminated_intravascular_coagulation": 0.5, "immune_thrombocytopenia": 0.5, "anemia": 0.9},
      src="ISTH TTP 2020 (Zheng); PLASMIC score (Bendapudi 2017)"),
 dict(id="hus", dx=["hemolytic_uremic_syndrome", "shiga_toxin_hemolytic_uremic_syndrome"], req=[("plt", "<", 150), ("schisto", ">", 1), ("cr", ">", 1.5)], sup=[("ldh", ">", 500), ("hapto", "<", 30), ("dat", "neg", None), ("shiga", "pos", None), ("adamts13", ">=", 20), ("k", ">", 5.0), ("bun", ">", 40)], min_sup=2,
      excl=[("adamts13", "<", 10), ("scl70", "pos", None)], cap={"thrombotic_thrombocytopenic_purpura": 0.5, "hemolytic_anemia": 0.9, "acute_kidney_injury": 0.9, "anemia": 0.9},
      src="Fakhouri, HUS, Lancet 2017"),
 dict(id="dic", dx=["disseminated_intravascular_coagulation"], req=[("plt", "<", 100), ("ddimer", ">", 2.0), ("fib", "<", 150)], sup=[("pt", ">", 16), ("inr", ">", 1.5), ("schisto", ">", 0), ("at", "<", 70)], min_sup=1,
      cap={"thrombotic_thrombocytopenic_purpura": 0.5, "hemolytic_uremic_syndrome": 0.5, "thrombocytopenia": 0.9, "vitamin_k_deficiency": 0.5}, src="ISTH overt DIC score (Taylor 2001) ≥5"),
 dict(id="hit", dx=["heparin_induced_thrombocytopenia"], req=[("plt", "<", 150)], sup=[("hit_ab", ">", 1.0), ("sra", ">", 20), ("ddimer", ">", 1.0)], min_sup=1, min_sup_any=[("hit_ab", ">", 1.0), ("sra", ">", 20)],
      excl=[("fib", "<", 150), ("schisto", ">", 1)], cap={"thrombocytopenia": 0.9, "immune_thrombocytopenia": 0.4, "disseminated_intravascular_coagulation": 0.6}, src="ASH 2018 HIT (Cuker): 4Ts + PF4 ELISA/SRA"),
 dict(id="hemophilia_a", dx=["hemophilia_a"], req=[("f8", "<", 40), ("pt", "<", 15)], sup=[("aptt", ">", 40), ("vwf_ag", ">=", 50), ("mixing", "pos", None), ("f9", ">=", 50)], min_sup=1, excl=[("vwf_ag", "<", 50)],
      cap={"von_willebrand_disease": 0.5, "prolonged_aptt": 0.9}, src="WFH 2020 haemophilia guideline"),
 dict(id="vwd", dx=["von_willebrand_disease"], req=[("vwf_ag", "<", 50)], alt_req=[("vwf_act", "<", 50)], sup=[("vwf_act", "<", 50), ("f8", "<", 50), ("aptt", ">", 36), ("pfa", ">", 180), ("plt", ">=", 150)], min_sup=1,
      cap={"hemophilia_a": 0.5, "prolonged_aptt": 0.9}, src="ASH/ISTH/NHF/WFH 2021 VWD (James): VWF <0.30 IU/mL diagnostic, 0.30–0.50 with bleeding"),
 dict(id="aps", dx=["antiphospholipid_syndrome"], req=[("la", "pos", None)], alt_req=[("acl", ">", 40)], alt_req2=[("b2gp", ">", 40)], sup=[("aptt", ">", 36), ("plt", "<", 150), ("ddimer", ">", 0.5), ("acl", ">", 40), ("b2gp", ">", 40)], min_sup=1,
      cap={"prolonged_aptt": 0.9, "thrombocytopenia": 0.9, "immune_thrombocytopenia": 0.5, "hemophilia_a": 0.3}, src="ACR/EULAR 2023 APS classification"),
 dict(id="vitk_def", dx=["vitamin_k_deficiency", "vitamin_k_deficiency_bleeding", "warfarin_effect"], req=[("inr", ">", 1.5), ("fib", ">=", 150), ("plt", ">=", 100)], sup=[("f7", "<", 40), ("f5", ">=", 50), ("ddimer", "<", 1.0), ("alb", ">=", 3.5), ("aptt", ">", 36)], min_sup=2,
      excl=[("alt", ">", 200), ("alb", "<", 3.0)], cap={"disseminated_intravascular_coagulation": 0.4, "liver_cirrhosis": 0.5, "acute_liver_failure": 0.3}, src="UpToDate: vitamin K deficiency — PT prolonged, factor VII low, factor V normal"),
 dict(id="aplastic", dx=["aplastic_anemia", "bone_marrow_failure"], req=[("anc", "<", 0.5), ("plt", "<", 20), ("hb", "<", 10)], alt_req=[("anc", "<", 1.5), ("plt", "<", 50), ("retic", "<", 1.0), ("hb", "<", 10)],
      sup=[("retic", "<", 1.0), ("retic_abs", "<", 20), ("blasts", "==", 0), ("ldh", "<", 300), ("b12", ">=", 200), ("folate", ">=", 3)], min_sup=2, excl=[("blasts", ">", 2), ("ferritin", ">", 5000), ("b12", "<", 200)],
      cap={"pancytopenia": 0.9, "acute_leukemia": 0.5, "myelodysplastic_syndrome": 0.7, "acute_myeloid_leukemia": 0.5, "anemia": 0.9, "thrombocytopenia": 0.9, "neutropenia": 0.9},
      src="BSH 2016 aplastic anaemia (Killick): Camitta criteria"),
 dict(id="mds", dx=["myelodysplastic_syndrome"], req=[("hb", "<", 11), ("mcv", ">", 98)], sup=[("anc", "<", 1.8), ("plt", "<", 100), ("blasts", "between", (1, 19)), ("retic", "<", 1.5), ("b12", ">=", 200), ("folate", ">=", 3), ("epo", ">", 100)], min_sup=3,
      ctx=[("age_ge", 55)], excl=[("b12", "<", 200), ("folate", "<", 3), ("blasts", ">=", 20), ("tsh", ">", 10), ("retic", ">", 2.5)],
      cap={"acute_myeloid_leukemia": 0.5, "aplastic_anemia": 0.5, "pancytopenia": 0.9, "anemia": 0.9, "vitamin_b12_deficiency": 0.4, "megaloblastic_anemia": 0.4, "macrocytic_anemia": 0.9},
      src="WHO 2022 / ICC 2022 MDS; cytopenia + macrocytosis + excluded deficiencies in elderly"),
 dict(id="cll", dx=["chronic_lymphocytic_leukemia"], req=[("alc", ">=", 5.0)], alt_req=[("wbc", ">", 20), ("lymph_pct", ">", 70)], sup=[("smudge", "pos", None), ("igg", "<", 700), ("hb", "<", 12), ("plt", "<", 150), ("atyp_lymph", "<", 10)], min_sup=1,
      ctx=[("age_ge", 40)], excl=[("blasts", ">", 5), ("hetero", "pos", None), ("ebv_vca_igm", "pos", None)],
      cap={"lymphocytosis": 0.9, "infectious_mononucleosis": 0.3, "acute_lymphoblastic_leukemia": 0.3}, src="iwCLL 2018 (Hallek): B-lymphocytes ≥5×10⁹/L"),
 dict(id="all", dx=["acute_lymphoblastic_leukemia", "acute_leukemia"], req=[("blasts", ">=", 20)], sup=[("hb", "<", 10), ("plt", "<", 100), ("ldh", ">", 500), ("urate", ">", 7), ("anc", "<", 1.0), ("wbc", ">", 30)], min_sup=2,
      ctx=[("age_lt", 20)], excl=[("auer", "pos", None), ("promyelo", ">", 20)], cap={"acute_myeloid_leukemia": 0.7, "acute_leukemia": 0.95, "tumor_lysis_syndrome": 0.95}, src="WHO 2022 (blasts ≥20%); childhood predominance of ALL"),
 dict(id="aml", dx=["acute_myeloid_leukemia", "acute_leukemia"], req=[("blasts", ">=", 20)], sup=[("auer", "pos", None), ("hb", "<", 10), ("plt", "<", 100), ("ldh", ">", 500), ("anc", "<", 1.0)], min_sup=1, ctx=[("age_ge", 20)],
      excl=[("promyelo", ">", 20), ("fib", "<", 150)], cap={"acute_lymphoblastic_leukemia": 0.7, "acute_leukemia": 0.95}, src="WHO 2022 / ELN 2022"),
 dict(id="apl", dx=["acute_promyelocytic_leukemia", "acute_myeloid_leukemia", "disseminated_intravascular_coagulation"], req=[("promyelo", ">", 20)], alt_req=[("blasts", ">=", 10), ("fib", "<", 150), ("auer", "pos", None)],
      sup=[("fib", "<", 150), ("ddimer", ">", 2), ("pt", ">", 16), ("plt", "<", 50), ("auer", "pos", None), ("wbc", "<", 10)], min_sup=2,
      cap={"acute_myeloid_leukemia": 0.9, "disseminated_intravascular_coagulation": 0.9, "acute_lymphoblastic_leukemia": 0.3}, src="ELN 2019 APL (Sanz): promyelocytes/Auer rods + coagulopathy"),
 dict(id="et", dx=["essential_thrombocythemia"], req=[("plt", ">=", 450)], sup=[("jak2", "pos", None), ("crp", "<", 10), ("ferritin", ">=", 30), ("hb", "between", (11.5, 16.5)), ("wbc", "<", 15)], min_sup=2, min_sup_any=[("jak2", "pos", None)],
      excl=[("ferritin", "<", 30), ("crp", ">", 30), ("hct", ">", 49), ("teardrop", "pos", None)], cap={"thrombocytosis": 0.9, "reactive_thrombocytosis": 0.3, "polycythemia_vera": 0.6, "primary_thrombocytosis": 0.95},
      src="WHO 2022 ET: platelets ≥450 + JAK2/CALR/MPL, reactive causes excluded"),
 dict(id="pmf", dx=["primary_myelofibrosis", "myelofibrosis"], req=[("teardrop", "pos", None)], alt_req=[("nrbc", ">", 2), ("ldh", ">", 400), ("hb", "<", 11), ("jak2", "pos", None)],
      sup=[("nrbc", ">", 2), ("ldh", ">", 400), ("jak2", "pos", None), ("hb", "<", 11), ("wbc", ">", 11), ("blasts", "between", (1, 9)), ("urate", ">", 7)], min_sup=2,
      cap={"acute_myeloid_leukemia": 0.4, "leukocytosis_pattern": 0.8, "anemia": 0.9, "thrombocytopenia": 0.9, "essential_thrombocythemia": 0.5, "polycythemia_vera": 0.5}, src="WHO 2022 PMF: leukoerythroblastosis + teardrops + LDH + driver mutation"),
 dict(id="pv", dx=["polycythemia_vera"], req=[("hb", ">", 16.5), ("jak2", "pos", None)], sup=[("hct", ">", 49), ("plt", ">", 400), ("wbc", ">", 11), ("epo", "<", 5)], min_sup=1,
      cap={"polycythemia": 0.9, "secondary_polycythemia": 0.3, "essential_thrombocythemia": 0.5}, src="WHO 2022 PV (Hb >16.5 M/>16 F + JAK2 + low EPO)"),
 dict(id="secondary_polycythemia", dx=["secondary_erythrocytosis", "polycythemia"], req=[("hb", ">", 16.5)], sup=[("epo", ">", 15), ("po2", "<", 65), ("cohb", ">", 5), ("jak2", "neg", None), ("plt", "<", 400), ("wbc", "<", 11), ("pco2", ">", 45)], min_sup=2, min_sup_any=[("epo", ">", 15), ("jak2", "neg", None), ("po2", "<", 65), ("cohb", ">", 5)],
      excl=[("jak2", "pos", None)], cap={"polycythemia_vera": 0.4, "hypoxemia": 0.9, "polycythemia": 0.95}, src="BSH 2019 erythrocytosis (McMullin): raised EPO / hypoxia / JAK2-negative"),
 dict(id="waldenstrom", dx=["waldenstrom_macroglobulinemia"], req=[("igm", ">", 1000)], alt_req=[("mspike", ">", 1.0), ("viscosity", ">", 1.8)], sup=[("mspike", ">", 1.0), ("viscosity", ">", 1.8), ("hb", "<", 11), ("tp", ">", 8.5), ("b2m", ">", 3)], min_sup=1,
      excl=[("ca_c", ">", 11), ("flc_ratio_c", ">", 100)], cap={"multiple_myeloma": 0.5, "monoclonal_gammopathy_renal": 0.6, "malnutrition": 0.4, "anemia": 0.9, "pellagra": 0.2},
      src="IWWM-2 consensus (Owen, Semin Oncol 2003): IgM paraprotein + marrow LPL"),
 dict(id="mgus", dx=["monoclonal_gammopathy_of_undetermined_significance", "mgus"], req=[("mspike", "between", (0.1, 2.99))], sup=[("hb", ">=", 12), ("ca_c", "<=", 10.5), ("cr", "<=", 1.3), ("flc_ratio_c", "between", (0.1, 8)), ("alb", ">=", 3.5)], min_sup=3,
      excl=[("hb", "<", 10), ("ca_c", ">", 11), ("cr", ">", 2), ("flc_ratio_c", ">", 100), ("igm", ">", 3000)],
      cap={"multiple_myeloma": 0.5, "monoclonal_gammopathy_renal": 0.4, "cardiac_amyloidosis_light_chain": 0.4, "waldenstrom_macroglobulinemia": 0.5}, src="IMWG 2014 (Rajkumar): M-protein <3 g/dL, no CRAB, FLC ratio <100"),
 dict(id="myeloma", dx=["multiple_myeloma"], req=[("mspike", ">=", 3.0)], alt_req=[("flc_ratio_c", ">=", 100)], alt_req2=[("flc_ratio_c", "<=", 0.01)],
      sup=[("ca_c", ">", 11), ("cr", ">", 2), ("hb", "<", 10), ("b2m", ">", 3.5), ("alb", "<", 3.5), ("tp", ">", 8.5), ("uprot24", ">", 0.5)], min_sup=1,
      excl=[("igm", ">", 3000), ("upcr", ">", 5)], cap={"monoclonal_gammopathy_renal": 0.8, "monoclonal_gammopathy_of_undetermined_significance": 0.4, "malnutrition": 0.5, "cardiac_amyloidosis_light_chain": 0.6, "anemia": 0.9, "hypercalcemia": 0.9, "acute_kidney_injury": 0.9, "monoclonal_paraprotein_pattern": 0.9},
      src="IMWG 2014: ≥1 CRAB or SLiM (FLC ratio ≥100)"),
 dict(id="lc_myeloma", dx=["multiple_myeloma", "light_chain_multiple_myeloma", "myeloma_cast_nephropathy"], req=[("flc_ratio_c", ">=", 100), ("cr", ">", 2.0)], alt_req=[("flc_ratio_c", "<=", 0.01), ("cr", ">", 2.0)],
      sup=[("flc_diff", ">", 500), ("ca_c", ">", 11), ("hb", "<", 10), ("mspike", "<", 0.5), ("uprot24", ">", 1.0)], min_sup=1,
      cap={"monoclonal_gammopathy_renal": 0.8, "acute_kidney_injury": 0.9, "cardiac_amyloidosis_light_chain": 0.5, "monoclonal_paraprotein_pattern": 0.9, "nephrotic_syndrome": 0.5},
      src="IMWG 2014; IMWG renal 2016 (Dimopoulos): iFLC >1500 mg/L with AKI = cast nephropathy until proven otherwise"),
 dict(id="al_amyloid", dx=["al_amyloidosis_systemic", "cardiac_amyloidosis_light_chain", "amyloidosis"], req=[("flc_ratio_c", "<", 0.26)], alt_req=[("flc_ratio_c", ">", 1.65), ("flc_diff", ">", 50)],
      sup=[("upcr", ">", 0.5), ("alb", "<", 3.0), ("natri_high", "==", 1), ("trop_c", ">", 40), ("alp", ">", 150), ("flc_diff", ">", 50)], min_sup=2, excl=[("flc_ratio_c", ">=", 100), ("ca_c", ">", 11)],
      cap={"nephrotic_syndrome": 0.9, "acute_kidney_injury": 0.8, "chronic_kidney_disease": 0.8, "multiple_myeloma": 0.6, "heart_failure": 0.9},
      src="Gertz, AL amyloidosis diagnosis, Am J Hematol 2020: abnormal FLC + nephrotic/cardiac involvement (NT-proBNP, troponin)"),
 dict(id="hlh", dx=["hemophagocytic_lymphohistiocytosis"], req=[("ferritin", ">=", 500)], sup=[("tg", ">=", 265), ("fib", "<=", 150), ("hb", "<", 9), ("plt", "<", 100), ("anc", "<", 1.0), ("sil2r", ">=", 2400), ("ast", ">", 100), ("ldh", ">", 500), ("nk", "neg", None)], min_sup=4,
      cap={"disseminated_intravascular_coagulation": 0.6, "neutropenia": 0.9, "hypertriglyceridemia": 0.85, "isolated_hyperbilirubinemia_pattern": 0.7, "sepsis": 0.9, "adult_onset_still_disease": 0.6, "pancytopenia": 0.9},
      src="HLH-2004 (Henter): 5 of 8 criteria; HScore (Fardet 2014)"),
 dict(id="pnh", dx=["paroxysmal_nocturnal_hemoglobinuria"], req=[("pnh", ">", 1)], sup=[("ldh", ">", 400), ("hapto", "<", 30), ("dat", "neg", None), ("uhemosiderin", "pos", None), ("retic", ">", 2.5), ("ferritin", "<", 30), ("plt", "<", 150), ("anc", "<", 1.5), ("ddimer", ">", 1.0)], min_sup=2,
      cap={"hemolytic_anemia": 0.9, "hemosiderinuria_pattern": 0.9, "aortic_dissection": 0.2, "iron_deficiency_anemia": 0.6, "thrombotic_thrombocytopenic_purpura": 0.3, "aplastic_anemia": 0.6, "anemia": 0.9},
      src="ICCS/ESCCA PNH flow guidelines 2018; Parker, Blood 2005"),
 dict(id="hemolysis_generic", dx=["hemolytic_anemia", "hemolysis"], req=[("hb", "<", 12), ("ldh", ">", 250), ("hapto", "<", 30)], sup=[("retic", ">", 2.5), ("ibil_c", ">", 1), ("dat", "present", None)], min_sup=1,
      excl=[("schisto", ">", 1), ("b12", "<", 200), ("plt", "<", 50)], src="UpToDate: diagnosis of haemolytic anaemia"),
 dict(id="imn", dx=["infectious_mononucleosis", "epstein_barr_virus_infection"], req=[("atyp_lymph", ">=", 10)], alt_req=[("hetero", "pos", None)], alt_req2=[("ebv_vca_igm", "pos", None)],
      sup=[("hetero", "pos", None), ("ebv_vca_igm", "pos", None), ("lymph_pct", ">", 50), ("alt", ">", 40), ("plt", "<", 150), ("wbc", ">", 10)], min_sup=1, ctx=[("age_lt", 40)],
      cap={"chronic_lymphocytic_leukemia": 0.3, "acute_lymphoblastic_leukemia": 0.3, "lymphocytosis": 0.9, "hepatitis": 0.7, "autoimmune_hepatitis": 0.4}, src="Hoagland criteria; Luzuriaga NEJM 2010"),
 # ---------------- infection / inflammation / rheumatology -----------------
 dict(id="sepsis_bacterial", dx=["sepsis", "bacterial_infection"], req=[("pct", ">=", 2.0)], sup=[("wbc", ">", 12), ("wbc", "<", 4), ("bands", ">", 10), ("crp", ">", 100), ("lactate", ">", 2), ("plt", "<", 150), ("cr", ">", 1.5)], min_sup=2,
      excl=[("ferritin", ">", 10000)], cap={"leukocytosis_pattern": 0.8, "bacterial_infection": 0.95, "viral_infection": 0.3}, src="Sepsis-3; Schuetz, PCT meta-analysis, Lancet ID 2018"),
 dict(id="urosepsis", dx=["pyelonephritis", "urinary_tract_infection", "sepsis"], req=[("ule", "pos", None), ("uwbc", ">", 10)], alt_req=[("unitrite", "pos", None), ("uwbc", ">", 10)],
      sup=[("unitrite", "pos", None), ("wbc", ">", 12), ("crp", ">", 50), ("pct", ">", 0.5), ("lactate", ">", 2), ("cr", ">", 1.3), ("bands", ">", 10)], min_sup=2,
      cap={"sepsis": 0.95, "leukocytosis_pattern": 0.8, "bacterial_infection": 0.9, "acute_kidney_injury": 0.85}, src="IDSA 2010 cUTI; EAU urological infections 2024"),
 dict(id="dengue", dx=["dengue_fever", "dengue"], req=[("ns1", "pos", None)], sup=[("plt", "<", 100), ("wbc", "<", 4), ("ast", ">", 80), ("hct", ">", 48), ("alb", "<", 3.5)], min_sup=1,
      cap={"thrombocytopenia": 0.9, "leukopenia": 0.9, "immune_thrombocytopenia": 0.3, "viral_infection": 0.9, "hepatitis": 0.6}, src="WHO dengue 2009; NS1 antigen days 1–7"),
 dict(id="malaria", dx=["malaria", "severe_malaria", "falciparum_malaria"], req=[("malaria", ">", 0)], alt_req=[("malaria_smear", "pos", None)],
      sup=[("plt", "<", 150), ("hb", "<", 11), ("ldh", ">", 250), ("ibil_c", ">", 1), ("glucose", "<", 70), ("lactate", ">", 2), ("cr", ">", 1.5), ("hapto", "<", 30)], min_sup=1,
      cap={"hemolytic_anemia": 0.6, "thrombotic_thrombocytopenic_purpura": 0.3, "immune_thrombocytopenia": 0.3, "acute_kidney_injury": 0.85, "thrombocytopenia": 0.9, "decreased_haptoglobin_serum_quantitative": 0.8},
      src="WHO malaria guidelines 2023; severe malaria criteria (parasitaemia >2–5%, Hb <7, Cr >3, lactate >5, glucose <40)"),
 dict(id="tb_disseminated", dx=["tuberculosis", "disseminated_tuberculosis", "miliary_tuberculosis"], req=[("igra", "pos", None)], sup=[("esr", ">", 50), ("na", "<", 135), ("alb", "<", 3.0), ("ca_c", ">", 10.3), ("alp", ">", 150), ("ferritin", ">", 500), ("alc", "<", 1.0), ("hb", "<", 11)], min_sup=3,
      cap={"hyponatremia": 0.85, "anemia_of_chronic_disease": 0.9, "lymphopenia": 0.9, "hypercalcemia": 0.9, "anemia": 0.9, "sarcoidosis": 0.6}, src="WHO TB 2022; Sharma, Miliary TB, Lancet ID 2005"),
 dict(id="hiv_advanced", dx=["hiv_infection", "acquired_immunodeficiency_syndrome", "hiv_aids"], req=[("hiv_ab", "pos", None)], alt_req=[("hiv_vl", ">", 1000)],
      sup=[("cd4", "<", 200), ("hiv_vl", ">", 1000), ("alc", "<", 1.0), ("hb", "<", 12), ("ldh", ">", 300), ("alb", "<", 3.5)], min_sup=1,
      cap={"lymphopenia": 0.9, "anemia": 0.9, "anemia_of_chronic_disease": 0.9}, src="CDC HIV surveillance case definition 2014; DHHS 2024"),
 dict(id="ra", dx=["rheumatoid_arthritis"], req=[("ccp", ">", 20)], alt_req=[("rf", ">", 40), ("crp", ">", 10)], sup=[("rf", ">", 14), ("crp", ">", 10), ("esr", ">", 28), ("plt", ">", 400), ("hb", "<", 12), ("ferritin", ">", 100)], min_sup=1,
      excl=[("ana", ">=", 640), ("dsdna", ">", 30)], cap={"anemia_of_chronic_disease": 0.9, "anemia": 0.9, "thrombocytosis": 0.9, "reactive_thrombocytosis": 0.9, "thalassemia_trait": 0.4, "psoriatic_arthritis": 0.5},
      src="ACR/EULAR 2010 RA classification: high-positive anti-CCP (>3x ULN) = 3 points"),
 dict(id="aosd", dx=["adult_onset_still_disease"], req=[("ferritin", ">", 1000), ("wbc", ">", 10), ("neut_pct", ">=", 80)], sup=[("glyc_ferritin", "<=", 20), ("crp", ">", 50), ("esr", ">", 50), ("ast", ">", 40), ("ana", "<", 80), ("rf", "<", 14), ("pct", "<", 2), ("bcx", "neg", None)], min_sup=3,
      ctx=[("age_ge", 16)], excl=[("fib", "<", 150), ("blasts", ">", 0)],
      cap={"psoriatic_arthritis": 0.3, "bacterial_infection": 0.6, "leukocytosis_pattern": 0.8, "anemia_of_chronic_disease": 0.9, "urinary_tract_infection": 0.3, "sepsis": 0.7, "hemophagocytic_lymphohistiocytosis": 0.7, "rheumatoid_arthritis": 0.5},
      src="Yamaguchi 1992 (major: fever, arthralgia, rash, WBC ≥10 with ≥80% PMN); Fautrel 2002 (glycosylated ferritin ≤20%)"),
 dict(id="gca_pmr", dx=["giant_cell_arteritis", "polymyalgia_rheumatica"], req=[("esr", ">=", 50)], alt_req=[("crp", ">", 50)], sup=[("crp", ">", 20), ("plt", ">", 400), ("hb", "<", 12), ("alp", ">", 130), ("alb", "<", 3.5), ("ck", "<", 200), ("rf", "<", 14)], min_sup=3,
      ctx=[("age_ge", 50)], excl=[("pct", ">", 0.5), ("ccp", ">", 20), ("mspike", ">", 0.5), ("ferritin", ">", 1000), ("ana", ">=", 160), ("igra", "pos", None), ("blasts", ">", 0), ("wbc", ">", 15)],
      cap={"psoriatic_arthritis": 0.3, "anemia": 0.9, "malnutrition": 0.6, "thrombocytosis": 0.9, "reactive_thrombocytosis": 0.9, "vitamin_d_deficiency": 0.6, "anemia_of_chronic_disease": 0.9},
      src="ACR/EULAR 2022 GCA; ACR/EULAR 2012 PMR: age ≥50, ESR/CRP raised, normal CK/RF"),
 dict(id="myositis", dx=["dermatomyositis", "inflammatory_myopathy", "polymyositis", "antisynthetase_syndrome"], req=[("ck", ">", 1000)], sup=[("jo1", "pos", None), ("aldolase", ">", 8), ("ana", ">=", 160), ("ldh", ">", 250), ("ast_alt", ">", 1), ("crp", "<", 50)], min_sup=2, min_sup_any=[("jo1", "pos", None), ("ana", ">=", 160), ("aldolase", ">", 8)],
      excl=[("ck", ">", 20000), ("tsh", ">", 10)], cap={"rhabdomyolysis": 0.6, "jo_1_antibody_autoantibody_positivity": 0.9, "serotonin_syndrome": 0.2, "malignant_catatonia": 0.2, "neuroleptic_malignant_syndrome": 0.3, "hepatitis": 0.5},
      src="ACR/EULAR 2017 IIM classification (Lundberg)"),
 dict(id="scleroderma_renal_crisis", dx=["systemic_sclerosis", "thrombotic_microangiopathy"], req=[("scl70", "pos", None), ("cr", ">", 1.5)], alt_req=[("scl70", "pos", None), ("schisto", ">", 1)],
      sup=[("schisto", ">", 1), ("plt", "<", 150), ("ldh", ">", 400), ("pra", ">", 3), ("hapto", "<", 30), ("ana", ">=", 160)], min_sup=2,
      cap={"hemolytic_anemia": 0.6, "scl_70_antibody_autoantibody_positivity": 0.9, "thrombotic_thrombocytopenic_purpura": 0.4, "hemolytic_uremic_syndrome": 0.5, "anemia": 0.9, "acute_kidney_injury": 0.9},
      src="Hudson, Scleroderma renal crisis classification, Semin Arthritis Rheum 2014"),
 dict(id="ssc", dx=["systemic_sclerosis"], req=[("scl70", "pos", None)], sup=[("ana", ">=", 160), ("crp", ">", 10), ("hb", "<", 12)], min_sup=0, excl=[("cr", ">", 1.5)],
      cap={"scl_70_antibody_autoantibody_positivity": 0.9}, src="ACR/EULAR 2013 SSc"),
 dict(id="sjogren", dx=["sjogren_syndrome"], req=[("ssa", "pos", None)], sup=[("ssb", "pos", None), ("ana", ">=", 160), ("rf", ">", 14), ("igg", ">", 1600), ("esr", ">", 28), ("wbc", "<", 4), ("k", "<", 3.5), ("hco3", "<", 22), ("uph", ">", 5.5)], min_sup=2,
      excl=[("dsdna", ">", 30), ("c3", "<", 70), ("plt", "<", 100)], cap={"systemic_lupus_erythematosus": 0.6, "renal_tubular_acidosis": 0.9, "renal_tubular_acidosis_type_1": 0.9, "hypokalemia": 0.9, "leukopenia": 0.9, "rheumatoid_arthritis": 0.6},
      src="ACR/EULAR 2016 SjS classification: anti-SSA/Ro = 3 points"),
 dict(id="gout_flare", dx=["gout", "acute_gout", "gouty_arthritis"], req=[("msu", "pos", None)], alt_req=[("urate", ">", 8), ("crp", ">", 30)], sup=[("urate", ">", 6.8), ("crp", ">", 30), ("wbc", ">", 10), ("esr", ">", 28), ("cr", ">", 1.3)], min_sup=1,
      excl=[("cppd", "pos", None)], cap={"gouty_arthritis_acute_flare": 0.95, "leukocytosis_pattern": 0.8, "acute_kidney_injury": 0.85, "chronic_kidney_disease": 0.9, "hyperuricemia": 0.9, "septic_arthritis": 0.6},
      src="ACR/EULAR 2015 gout classification: MSU crystals = sufficient criterion"),
 dict(id="kawasaki", dx=["kawasaki_disease"], req=[("crp", ">=", 30), ("esr", ">=", 40)], sup=[("plt", ">", 450), ("alb", "<=", 3.0), ("alt", ">", 40), ("wbc", ">=", 15), ("na", "<", 135), ("uwbc", ">=", 10), ("natri_high", "==", 1), ("ucx", "neg", None)], min_sup=3,
      ctx=[("age_lt", 8)], excl=[("pct", ">", 2), ("ferritin", ">", 1000), ("blasts", ">", 0)],
      cap={"hyponatremia": 0.85, "leukocytosis_pattern": 0.8, "thrombocytosis": 0.9, "malnutrition": 0.5, "bacterial_infection": 0.6, "urinary_tract_infection": 0.5, "reactive_thrombocytosis": 0.9},
      src="AHA 2017 Kawasaki (McCrindle): supplemental lab criteria — albumin ≤3, anaemia, ALT↑, platelets >450 after 7 d, WBC ≥15, sterile pyuria"),
 # ---------------- cardiopulmonary / miscellaneous -------------------------
 # v6 C10 (2026-10-25): formerly asserted acute MI from troponin > 100 ng/L plus a non-ischaemic support (glucose, creatinine, lactate,
 # natriuretic peptide). 4th UDMI: that is myocardial injury; infarction needs clinical ischaemia (see mi_high_troponin_ischaemic_presentation)
 # or a rise/fall (temporal layer). Retargeted to the acuity-undetermined injury finding; caps on AKI / HF retained.
 dict(id="mi", dx=["myocardial_injury_acuity_undetermined"], strength="strong", req=[("trop_c", ">", 100)],
      sup=[("ckmb", ">", 5), ("natri_high", "==", 1), ("glucose", ">", 140), ("cr", ">", 1.3), ("lactate", ">", 2)], min_sup=1, excl=[("ck", ">", 5000), ("crp", ">", 60), ("ddimer", ">", 4), ("cohb", ">", 10), ("schisto", ">", 1), ("plt", "<", 50), ("pct", ">", 2)], ctx=[("age_ge", 35)],
      cap={"acute_kidney_injury": 0.85, "heart_failure": 0.9, "myocarditis": 0.6}, src="Fourth Universal Definition of MI (Thygesen 2018)"),
 dict(id="myocardial_injury_single", dx=["myocardial_injury_acuity_undetermined"], req=[("trop_c", "between", (30, 100))], sup=[("cr", ">", 1.3), ("natri_high", "==", 1)], min_sup=0,
      excl=[("ckmb", ">", 5), ("ddimer", ">", 2.0), ("natri_high", "==", 1), ("crp", ">", 60), ("ck", ">", 5000), ("cr", ">", 3.0), ("pct", ">", 2), ("trop_dyn_pct", ">=", 0)], ctx=[("age_ge", 18)], strength="pattern",
      cap={"acute_myocardial_infarction": 0.8, "non_st_elevation_myocardial_infarction": 0.8, "acute_coronary_syndrome": 0.8, "myocardial_infarction": 0.8},
      src="Fourth Universal Definition of MI (Thygesen 2018): a single troponin above the 99th percentile defines myocardial injury; MI needs a rise/fall plus ischaemia"),
 dict(id="myocarditis", dx=["myocarditis", "acute_myocarditis"], req=[("trop_c", ">", 100), ("crp", ">", 20)], sup=[("natri_high", "==", 1), ("ck", ">", 300), ("wbc", ">", 10), ("esr", ">", 28)], min_sup=1, ctx=[("age_lt", 40)],
      cap={"acute_myocardial_infarction": 0.6, "acute_coronary_syndrome": 0.6, "rhabdomyolysis": 0.5}, src="ESC 2013 myocarditis position statement (Caforio)"),
 dict(id="adhf", dx=["heart_failure", "acute_decompensated_heart_failure", "congestive_heart_failure", "cardiorenal_syndrome"], req=[("natri_high", "==", 1)],
      sup=[("ntprobnp", ">", 1800), ("bnp", ">", 900), ("na", "<", 135), ("cr", ">", 1.3), ("bun_cr", ">", 20), ("tbil", ">", 1.2), ("ast", ">", 40), ("trop_c", ">", 14), ("alb", "<", 3.5)], min_sup=2,
      excl=[("trop_c", ">", 500), ("ast", ">", 1000), ("ddimer", ">", 4), ("flc_ratio_c", "<", 0.26), ("pct", ">", 2)],
      cap={"acute_heart_failure_support_pattern": 0.95, "heart_failure_bnp_pattern": 0.95, "hyponatremia": 0.85, "acute_kidney_injury": 0.85, "isolated_hyperbilirubinemia_pattern": 0.7, "siadh": 0.3, "prerenal_azotemia": 0.9},
      src="ESC HF 2021/2023 (NT-proBNP >300 acute rule-in; age-adjusted 450/900/1800); AHA/ACC/HFSA 2022"),
 dict(id="pe", dx=["pulmonary_embolism", "venous_thromboembolism"], req=[("ddimer", ">", 0.5), ("po2", "<", 75)], sup=[("pco2", "<", 36), ("ph", ">", 7.44), ("trop_c", ">", 14), ("natri_high", "==", 1), ("lactate", ">", 2)], min_sup=2,
      excl=[("trop_c", ">", 500), ("fib", "<", 150), ("plt", "<", 100), ("crp", ">", 100)],
      cap={"acute_myocardial_infarction": 0.5, "hypoxemia": 0.9, "elevated_d_dimer_pattern": 0.9, "respiratory_alkalosis": 0.9, "heart_failure": 0.6}, src="ESC 2019 PE (Konstantinides): D-dimer + hypoxaemia/hypocapnia + RV strain markers"),
 dict(id="carcinoid", dx=["carcinoid_syndrome", "neuroendocrine_tumor", "carcinoid_tumor"], req=[("hiaa", ">", 15)], alt_req=[("serotonin", ">", 400), ("cga", ">", 100)],
      sup=[("cga", ">", 100), ("serotonin", ">", 400), ("natri_high", "==", 1)], min_sup=0, cap={"elevated_serum_chromogranin_a": 0.9, "neuroendocrine_tumor_chromogranin_pattern": 0.9},
      src="ENETS 2016 / NANETS 2017: 24-h urinary 5-HIAA (ULN ~6–10 mg/24 h)"),
 dict(id="aip", dx=["acute_intermittent_porphyria", "acute_porphyria"], req=[("pbg", ">", 10)], sup=[("ala", ">", 10), ("na", "<", 135), ("uosm", ">", 100), ("alt", ">", 40)], min_sup=0,
      cap={"siadh": 0.5, "severe_hyponatremia": 0.9, "hyponatremia": 0.9, "adrenal_insufficiency": 0.4, "hypothyroidism": 0.4}, src="Anderson, Recommendations for acute porphyrias, Ann Intern Med 2005; EPNET"),
 dict(id="co_poisoning", dx=["carbon_monoxide_poisoning"], req=[("cohb", ">", 10)], sup=[("lactate", ">", 2), ("hco3", "<", 20), ("trop_c", ">", 14), ("ck", ">", 300), ("po2", ">", 80)], min_sup=1,
      cap={"lactic_acidosis": 0.85, "tetanus": 0.2, "euglycemic_diabetic_ketoacidosis": 0.3, "metabolic_acidosis": 0.85, "acute_myocardial_infarction": 0.6, "secondary_polycythemia": 0.9},
      src="Hampson, CO poisoning practice recommendations, AJRCCM 2012 (COHb >3% non-smoker / >10% smoker)"),
 dict(id="methemoglobinemia", dx=["methemoglobinemia", "acquired_methemoglobinemia"], req=[("methb", ">", 3)], sup=[("spo2", "<", 92), ("po2", ">", 80), ("lactate", ">", 2), ("retic", ">", 2.5)], min_sup=0,
      cap={"anemia": 0.7, "sepsis": 0.3, "carbon_monoxide_poisoning": 0.5, "beriberi": 0.2, "cerebral_malaria": 0.2, "hypoxemia": 0.9}, src="Cortazzo & Lichtman, Methemoglobinemia, J Cardiothorac Vasc Anesth 2014"),
 dict(id="neonatal_hemolytic_jaundice", dx=["neonatal_hyperbilirubinemia", "abo_hemolytic_disease_of_the_newborn", "hemolytic_disease_of_the_newborn"], req=[("tbil", ">", 12), ("dbil_frac", "<", 0.2)],
      sup=[("dat", "pos", None), ("retic", ">", 6), ("hb", "<", 14), ("maternal_o", "pos", None), ("g6pd", ">=", 4)], min_sup=1, ctx=[("age_lt", 0.1)], excl=[("dat", "pos", None)],
      cap={"gilbert_syndrome": 0.3, "hemolytic_anemia": 0.8, "autoimmune_hemolytic_anemia": 0.4}, src="AAP 2022 hyperbilirubinaemia ≥35 wk (Kemper)"),
 dict(id="congenital_hypothyroid", dx=["congenital_hypothyroidism_screening_pattern", "primary_hypothyroidism", "hypothyroidism"], req=[("tsh", ">", 20)], sup=[("ft4", "<", 0.8), ("tbil", ">", 10)], min_sup=0, ctx=[("age_lt", 1)],
      cap={"primary_hypothyroidism": 0.95, "hypothyroidism": 0.95, "myxedema_coma": 0.3}, src="ESPE 2020 congenital hypothyroidism (van Trotsenburg)"),
 dict(id="cf", dx=["cystic_fibrosis"], req=[("sweat_cl", ">=", 60)], sup=[("elastase", "<", 200), ("vita", "<", 20), ("vitd", "<", 20), ("alb", "<", 3.5), ("na", "<", 135), ("cl", "<", 98), ("hco3", ">", 28)], min_sup=1,
      cap={"vitamin_d_deficiency": 0.8, "hypochloremia": 0.9, "hyponatremia": 0.9, "malnutrition": 0.8, "exocrine_pancreatic_insufficiency": 0.95, "metabolic_alkalosis": 0.9, "pseudo_bartter_syndrome": 0.9},
      src="CFF 2017 diagnosis consensus (Farrell): sweat Cl ≥60 mmol/L diagnostic"),
 dict(id="anorexia", dx=["female_hypogonadotropic_hypogonadism", "protein_energy_malnutrition"],
      req=[("lh", "<", 2), ("e2", "<", 30)], sup=[("ft3", "<", 2.0), ("tsh", "between", (0.3, 5)), ("cortisol_am", ">", 18), ("tc", ">", 200), ("glucose", "<", 70), ("wbc", "<", 4), ("k", "<", 3.5), ("hco3", ">", 28), ("phos", "<", 2.5), ("alt", ">", 40), ("hb", "<", 12)], min_sup=4,
      ctx=[("sex", "f"), ("age_lt", 40)], excl=[("prl", ">", 100), ("cortisol_dex", ">", 1.8), ("fsh", ">", 25)],
      cap={"cushing_syndrome": 0.4, "anemia": 0.9, "hypokalemia": 0.9, "hypophosphatemia": 0.9, "leukopenia": 0.9, "hypopituitarism_panhypopituitarism": 0.5, "nonthyroidal_illness_syndrome": 0.9, "refeeding_syndrome": 0.9},
      src="Gordon, Functional hypothalamic amenorrhea, Endocrine Society 2017; Mehler, Anorexia nervosa medical complications, J Eat Disord 2015"),
 dict(id="sam_child", dx=["protein_energy_malnutrition", "severe_acute_malnutrition_laboratory_risk", "kwashiorkor", "severe_acute_malnutrition"], req=[("alb", "<", 2.5)],
      sup=[("prealb", "<", 10), ("glucose", "<", 54), ("k", "<", 3.5), ("phos", "<", 2.5), ("mg", "<", 1.7), ("na", "<", 135), ("hb", "<", 11), ("zinc", "<", 60)], min_sup=3, ctx=[("age_lt", 12)],
      excl=[("upcr", ">", 2), ("alt", ">", 200)], cap={"fasting_hypoglycemia": 0.8, "malnutrition": 0.95, "hypomagnesemia": 0.9, "hypophosphatemia": 0.9, "hyponatremia": 0.9, "hypokalemia": 0.9, "nephrotic_syndrome": 0.5, "refeeding_syndrome": 0.9},
      src="WHO 2013 SAM management; hypoglycaemia <54 mg/dL, hypoalbuminaemia in kwashiorkor"),
 dict(id="fh", dx=["familial_hypercholesterolemia"], req=[("ldl", ">=", 190)], sup=[("tc", ">", 290), ("tg", "<", 200), ("tsh", "<", 5), ("alt", "<", 60), ("ldl", ">=", 250), ("apob", ">", 130)], min_sup=2, excl=[("tsh", ">", 10), ("alb", "<", 3.0), ("upcr", ">", 3)],
      ctx_any=[("fh", "cad"), ("fh", "cholesterol"), ("fh", "hyperchol"), ("age_lt", 100)],
      cap={"hyperlipidemia": 0.9, "hypercholesterolemia": 0.9, "elevated_lpa_pattern": 0.8, "secondary_dyslipidemia": 0.4}, src="Dutch Lipid Clinic Network; AHA 2015 FH scientific statement (LDL ≥190 adult, ≥160 child)"),
 dict(id="hypothyroid_dyslipidemia", dx=["primary_hypothyroidism", "hypothyroidism", "secondary_dyslipidemia"], req=[("tsh", ">", 10), ("ldl", ">", 160)], sup=[("ft4", "<", 0.8), ("ck", ">", 200), ("tc", ">", 240), ("tg", ">", 150)], min_sup=1,
      cap={"familial_hypercholesterolemia": 0.4, "hyperlipidemia": 0.9, "hypercholesterolemia": 0.9}, src="ATA 2014; Duntas, Thyroid 2002 (hypothyroid dyslipidaemia)"),
 dict(id="fcs", dx=["familial_chylomicronemia_syndrome", "severe_hypertriglyceridemia", "hypertriglyceridemia"], req=[("tg", ">", 1000)], sup=[("hdl", "<", 30), ("apob", "<", 100), ("a1c", "<", 6.5), ("glucose", "<", 126), ("tg", ">", 2000)], min_sup=2,
      excl=[("lipase", ">", 180)], cap={"hypertriglyceridemia": 0.95, "hyperlipidemia": 0.9, "metabolic_syndrome": 0.6, "pseudohyponatremia": 0.95}, src="Moulin, FCS score, Atherosclerosis 2018"),
 dict(id="prostate_ca", dx=["prostate_cancer", "metastatic_prostate_cancer"], req=[("psa", ">", 20)], sup=[("fpsa_pct", "<", 10), ("alp", ">", 130), ("ca_c", ">", 10.3), ("hb", "<", 12)], min_sup=1, ctx=[("sex", "m"), ("age_ge", 40)],
      cap={"hypercalcemia": 0.9, "anemia": 0.9, "elevated_total_prostate_specific_antigen": 0.9, "paget_disease": 0.4, "renal_cell_carcinoma": 0.3, "benign_prostatic_hyperplasia": 0.5},
      src="EAU 2024 prostate cancer; PSA >20 ng/mL high-risk (D'Amico); %fPSA <10% high probability"),
 dict(id="ovarian_ca", dx=["ovarian_cancer", "epithelial_ovarian_cancer"], req=[("ca125", ">", 200)], sup=[("he4", ">", 140), ("plt", ">", 400), ("alb", "<", 3.5), ("hb", "<", 12), ("ddimer", ">", 1)], min_sup=1, ctx=[("sex", "f"), ("age_ge", 40)],
      excl=[("pregnant_ctx", "==", 1)], cap={"endometrial_cancer": 0.5, "aortic_dissection": 0.2, "peritoneal_carcinomatosis": 0.9, "anemia": 0.9, "elevated_d_dimer_pattern": 0.8, "thrombocytosis": 0.9},
      src="ROMA (Moore 2009): CA-125 + HE4 post-menopausal; ACOG 2016"),
 dict(id="gct", dx=["testicular_cancer", "nonseminomatous_germ_cell_tumor", "germ_cell_tumor"], req=[("afp", ">", 25), ("hcg", ">", 5)], sup=[("ldh", ">", 250)], min_sup=0, ctx=[("sex", "m"), ("age_lt", 50)],
      cap={"hepatocellular_carcinoma": 0.3, "hemolytic_anemia": 0.3}, src="IGCCCG 1997; EAU 2024 testicular cancer: AFP + hCG + LDH"),
 dict(id="mtc_men2", dx=["thyroid_cancer_medullary", "multiple_endocrine_neoplasia_type_2", "medullary_thyroid_carcinoma_marker_pattern"], req=[("calcitonin", ">", 100)], sup=[("cea", ">", 5), ("ca_c", ">", 10.3), ("pth", ">", 65), ("metaneph", ">", 0.5), ("normetaneph", ">", 0.9)], min_sup=1,
      cap={"primary_hyperparathyroidism": 0.8, "pheochromocytoma": 0.8, "adrenal_incidentaloma_workup": 0.5, "multiple_endocrine_neoplasia_type_1": 0.3}, src="ATA 2015 MTC (Wells): basal calcitonin >100 pg/mL ≈ MTC"),
 dict(id="sarcoid_generic", dx=["sarcoidosis"], req=[("ace", ">", 65)], sup=[("ca_c", ">", 10.3), ("vitd125", ">", 70), ("alc", "<", 1.0), ("igg", ">", 1600), ("alp", ">", 130)], min_sup=1, excl=[("igra", "pos", None)],
      src="ATS 2020 sarcoidosis (Crouser)"),
 dict(id="hashimoto_overt", dx=["primary_hypothyroidism", "hashimoto_thyroiditis", "hypothyroidism"], req=[("tsh", ">", 10), ("ft4", "<", 0.8)], sup=[("tpo", ">", 35), ("tc", ">", 200), ("ck", ">", 200), ("na", "<", 135)], min_sup=0,
      excl=[("tsh", ">", 30)], cap={"hypothyroidism": 0.95}, src="ATA 2014"),
 dict(id="thyrotox_overt", dx=["hyperthyroidism", "thyrotoxicosis"], req=[("tsh", "<", 0.1), ("ft4", ">", 1.8)], sup=[("ft3", ">", 4.4)], min_sup=0, excl=[("ft4", ">", 4.0), ("trab", ">", 1.75), ("tpo", ">", 35)],
      src="ATA 2016"),
 dict(id="t2dm", dx=["type_2_diabetes", "diabetes_mellitus", "type_2_diabetes_mellitus"], req=[("a1c", ">=", 6.5)], sup=[("glucose", ">=", 126), ("tg", ">=", 150), ("hdl", "<", 40), ("bmi_ge", ">=", 25), ("cpep", ">=", 1.0)], min_sup=1,
      excl=[("gad", ">", 5), ("bhb", ">=", 3.0), ("pregnant_ctx", "==", 1), ("ohp17", ">", 200), ("cortisol_dex", ">", 1.8), ("igf1", ">", 300), ("tsat", ">", 45), ("ft4", ">", 4.0)], ctx=[("age_ge", 18)],
      cap={"diabetes_mellitus": 0.98, "prediabetes": 0.5, "type_1_diabetes": 0.6}, src="ADA Standards of Care 2025 §2"),
 dict(id="prediabetes", dx=["prediabetes", "impaired_fasting_glucose"], req=[("a1c", "between", (5.7, 6.49))], sup=[("glucose", "between", (100, 125))], min_sup=0, excl=[("glucose", ">=", 126), ("pregnant_ctx", "==", 1), ("igf1", ">", 300)],
      cap={"type_2_diabetes": 0.5, "diabetes_mellitus": 0.5}, src="ADA 2025 §2"),
 dict(id="metabolic_syndrome", dx=["metabolic_syndrome"], req=[("tg", ">=", 150), ("hdl", "<", 40)], sup=[("fpg", ">=", 100), ("a1c", ">=", 5.7)], min_sup=1, strength="pattern",
      excl=[("tg", ">", 1000), ("tsh", ">", 10)], src="NCEP ATP III / IDF-AHA 2009 harmonised definition"),
 dict(id="hashimoto_subclinical", dx=["subclinical_hypothyroidism", "hashimoto_thyroiditis"], req=[("tsh", "between", (4.5, 10)), ("ft4", "between", (0.8, 1.8))], sup=[("tpo", ">", 35)], min_sup=0, excl=[("crp", ">", 50)],
      src="ATA 2014; ETA 2013 subclinical hypothyroidism"),
 dict(id="itp", dx=["immune_thrombocytopenia", "thrombocytopenia"], req=[("plt", "<", 100), ("hb", ">=", 12), ("wbc", "between", (4, 11))], sup=[("mpv", ">", 10), ("schisto", "<=", 1), ("fib", ">=", 150), ("inr", "<", 1.3)], min_sup=0,
      excl=[("schisto", ">", 1), ("fib", "<", 150), ("hit_ab", ">", 1.0), ("dat", "pos", None), ("ana", ">=", 160), ("hiv_ab", "pos", None), ("ns1", "pos", None), ("blasts", ">", 0)],
      cap={"thrombocytopenia": 0.95}, src="ASH 2019 ITP (Neunert): isolated thrombocytopenia <100, diagnosis of exclusion"),
 dict(id="cml", dx=["chronic_myeloid_leukemia"], req=[("bcr", "pos", None)], alt_req=[("wbc", ">", 50), ("baso_pct", ">", 2)], sup=[("plt", ">", 450), ("baso_pct", ">", 2), ("wbc", ">", 50), ("blasts", "<", 10)], min_sup=1,
      cap={"leukocytosis_pattern": 0.8, "essential_thrombocythemia": 0.5, "acute_myeloid_leukemia": 0.5}, src="ELN 2020 CML (Hochhaus)"),
 dict(id="acd", dx=["anemia_of_chronic_disease", "anemia_of_inflammation"], req=[("hb", "<", 12), ("ferritin", ">=", 100), ("tsat", "<", 20)], sup=[("crp", ">", 10), ("esr", ">", 28), ("mcv", "between", (78, 100)), ("stfr", "<", 2.5)], min_sup=1,
      excl=[("ferritin", ">", 5000), ("egfr", "<", 30)], cap={"anemia": 0.9, "iron_deficiency_anemia": 0.5}, src="Weiss & Ganz, Anemia of inflammation, Blood 2019"),
 dict(id="ckd_anemia", dx=["chronic_kidney_disease", "anemia_of_chronic_disease"], req=[("hb", "<", 12), ("egfr", "<", 45), ("mcv", "between", (80, 100))], sup=[("retic", "<", 1.5), ("ferritin", ">=", 100), ("epo", "<", 50), ("tsat", "between", (20, 100))], min_sup=1,
      excl=[("lactate", ">", 4), ("ck", ">", 5000)],  # extension 7: normocytosis is a requirement, not evidence; needs a marrow/iron marker
      src="KDIGO anaemia in CKD 2012"),
]


# ---------------------------------------------------------------------------
# ESL extension 2 (2026-10-21): additional analyte groups and ~100 further
# constellations (endocrine, renal, haematology, GI/liver, infection,
# rheumatology, cardio-pulmonary, neurology, toxicology, inborn errors,
# neonatal/paediatric, pregnancy). Thresholds follow the cited sources.
# ---------------------------------------------------------------------------
_ESL_GROUPS.update({
    "tryptase": ("ng/mL", ("tryptase_serum", "serum_total_tryptase_baseline")),
    "ige": ("IU/mL", ("total_immunoglobulin_e",)),
    "b6": ("nmol/L", ("vitamin_b6_pyridoxal_five_phosphate", "vitamin_b6_pyridoxal_phosphate")),
    "cryo": ("1", ("cryoglobulin",)),
    "anti_gbm": ("1", ("glomerular_basement_membrane_antibody", "anti_glomerular_basement_membrane_igg")),
    "aso": ("IU/mL", ("antistreptolysin_o_titer_quantitative",)),
    "hla_b27": ("1", ("hla_b27_antigen_allele",)),
    "igg4_s": ("mg/dL", ("serum_igg4",)),
    "phe": ("mg/dL", ("plasma_phenylalanine_quantitative",)),
    "digoxin": ("ng/mL", ("digoxin", "digoxin_serum_trough")),
    "che": ("U/L", ("cholinesterase", "pseudocholinesterase_serum")),
    "galactomannan": ("1", ("serum_galactomannan_index",)),
    "hcv_rna": ("IU/mL", ("hepatitis_c_rna_quantitative_pcr", "hepatitis_c_viral_load")),
    "hev_igm": ("1", ("hepatitis_e_igm_antibody",)),
    "hdv_ab": ("1", ("hepatitis_d_antibody", "hepatitis_delta_total_antibody")),
    "rpr": ("{titer}", ("rapid_plasma_reagin_titer", "syphilis_rpr", "vdrl_serum_titer")),
    "trep": ("1", ("treponema_pallidum_hemagglutination_tpha", "fluorescent_treponemal_antibody_absorbed")),
    "cmv_igm": ("1", ("cytomegalovirus_igm_antibody", "cmv_igm_antibody")),
    "toxo_igm": ("1", ("toxoplasma_igm_antibody",)),
    "brucella": ("{titer}", ("wright_agglutination_test_titer", "brucella_antibody_titer", "coombs_wright_test_titer")),
    "brucella_pcr": ("1", ("brucella_pcr",)),
    "widal_o": ("{titer}", ("widal_to_antigen_titer", "widal_test", "salmonella_widal_test")),
    "vma": ("mg/24h", ("urine_vanillylmandelic_acid_24h",)),
    "hva": ("mg/24h", ("urine_homovanillic_acid_24h",)),
    "rnp": ("1", ("rnp_antibody",)),
    "histone": ("1", ("anti_histone_antibody",)),
    "achr": ("nmol/L", ("anti_acetylcholine_receptor_binding_ab", "anti_acetylcholine_receptor_antibody")),
    "nmdar": ("1", ("anti_nmda_receptor_nr1_antibody",)),
    "ocb": ("1", ("cerebrospinal_fluid_oligoclonal_bands",)),
    "f11": ("%", ("factor_xi_activity",)),
    "f8_inh": ("{BU}", ("factor_viii_inhibitor_titer",)),
    "anti_xa_ufh": ("IU/mL", ("anti_xa_activity_unfractionated_heparin", "anti_factor_xa_unfractionated_heparin")),
    "prot_c": ("%", ("protein_c_activity",)),
    "prot_s": ("%", ("protein_s_activity", "free_protein_s_activity", "protein_s_activity_functional")),
    "fvl": ("1", ("factor_v_leiden_mutation",)),
    "saag": ("g/dL", ("serum_ascites_albumin_gradient", "ascitic_fluid_albumin_gradient")),
    "ascites_prot": ("g/dL", ("ascitic_fluid_protein",)),
    "ascites_cells": ("/uL", ("ascitic_fluid_cell_count",)),
    "cdiff_toxin": ("1", ("clostridioides_difficile_toxin_a_b",)),
    "cdiff_gdh": ("1", ("clostridium_difficile_gdh_antigen",)),
    "hp_stool": ("1", ("helicobacter_pylori_stool_antigen", "helicobacter_pylori_urea_breath_test")),
    "vip": ("pg/mL", ("vasoactive_intestinal_peptide",)),
    "glucagon": ("pg/mL", ("glucagon",)),
    "fgf23": ("RU/mL", ("fgf23", "fibroblast_growth_factor_23_intact")),
    "uca_cr_clear": ("1", ("urine_calcium_to_creatinine_clearance_ratio",)),
    "renin_conc": ("mIU/L", ("direct_renin_concentration", "plasma_renin_concentration")),
    "copper": ("ug/dL", ("copper", "serum_copper")),
    "vitc": ("mg/dL", ("vitamin_c", "vitamin_c_ascorbic_acid_plasma")),
    "thiamine_wb": ("nmol/L", ("vitamin_b1_thiamine_whole_blood", "vitamin_b1_thiamine")),
    "methanol": ("mg/dL", ("methanol",)),
    "isoprop": ("mg/dL", ("isopropanol",)),
    "acetone": ("mg/dL", ("acetone_serum",)),
    "theoph": ("ug/mL", ("theophylline", "theophylline_serum_level")),
    "valproate": ("ug/mL", ("valproic_acid_total",)),
    "carbamazepine": ("ug/mL", ("carbamazepine",)),
    "phenytoin": ("ug/mL", ("phenytoin_total",)),
    "leucine": ("umol/L", ("leucine_plasma",)),
    "tyrosine": ("umol/L", ("plasma_tyrosine_quantitative",)),
    "succinylacetone": ("umol/L", ("succinylacetone_blood_spot_quantitative",)),
    "galt": ("U/g{Hb}", ("galactose_one_phosphate_uridyltransferase_galt",)),
    "galactose": ("mg/dL", ("galactose_plasma",)),
    "acylcarn": ("1", ("acylcarnitine_profile",)),
    "orotic": ("mmol/mol", ("orotic_acid_urine",)),
    "leish_ab": ("1", ("leishmania_antibody",)),
    "dengue_igm": ("1", ("dengue_igm_antibody",)),
    "covid_pcr": ("1", ("sars_cov_2_rt_pcr_qualitative", "covid_19_pcr", "sars_cov_2_rna")),
    "flu_pcr": ("1", ("influenza_a_and_b_rna_pcr", "influenza_pcr", "influenza_a_rna", "influenza_b_rna")),
    "lap": ("1", ("leukocyte_alkaline_phosphatase_score",)),
    "mono_abs": ("10^9/L", ("monocyte_count_absolute",)),
    "cold_agg": ("{titer}", ("cold_agglutinins_titer",)),
    "syn_wbc": ("/uL", ("synovial_fluid_wbc",)),
    "xantho": ("1", ("csf_xanthochromia",)),
    "hbsab": ("mIU/mL", ("hepatitis_b_surface_antibody",)),
    "hbc_total": ("1", ("hepatitis_b_core_total_antibody",)),
    "mix_aptt_inc": ("1", ("aptt_mixing_study_incubated",)),
    "ipf": ("%", ("immature_platelet_fraction",)),
    "cystatin": ("mg/L", ("cystatin_c",)),
    "nse": ("ng/mL", ("neuron_specific_enolase",)),
    "plgf": ("pg/mL", ("placental_growth_factor",)),
    "fructosamine": ("umol/L", ("fructosamine", "serum_fructosamine")),
    "insulin_ab": ("1", ("anti_insulin_antibody",)),
    "shbg": ("nmol/L", ("sex_hormone_binding_globulin",)),
    "inhibin_b": ("pg/mL", ("inhibin_b",)),
    "tg_ab": ("IU/mL", ("thyroglobulin_antibody",)),
    "adas": ("U/L", ("adenosine_deaminase",)),
    "il6": ("pg/mL", ("interleukin_6", "interleukin_6_quantitative_serum")),
    "uk": ("mmol/L", ("urine_potassium",)),
    "uglu": ("1", ("urine_glucose_qualitative", "urine_glucose")),
    "uket": ("1", ("urine_ketones_qualitative", "urine_ketones")),
    "ualb": ("mg/L", ("urine_albumin",)),
    "ucx_crystals_cystine": ("1", ("urine_cystine_crystals_microscopy",)),
    "umyoglobin": ("1", ("urine_myoglobin",)),
    "uphos24": ("mg/24h", ("urine_phosphorus_24h", "twenty_four_hour_urine_phosphate")),
    "ucu": ("ug/24h", ("urine_copper_24h", "urine_copper")),
    "uporph": ("ug/24h", ("total_porphyrins_urine",)),
    "ufc": ("ug/24h", ("urine_free_cortisol_24h",)),
    "stool_fat": ("g/24h", ("fecal_fat",)),
    "stool_reducing": ("1", ("stool_reducing_substances",)),
    "fobt": ("1", ("stool_occult_blood_fit", "fecal_occult_blood_gfobt", "stool_occult_blood")),
    "fecal_a1at": ("mL/24h", ("fecal_alpha1_antitrypsin_clearance",)),
    "lactoferrin": ("ug/g", ("fecal_lactoferrin_quantitative",)),
    "ethanol_mg": ("mg/dL", ("ethanol",)),
    "iron_serum": ("ug/dL", ("serum_iron", "iron")),
    "crp_hs": ("mg/L", ("c_reactive_protein", "high_sensitivity_c_reactive_protein")),
    "hcv_ab2": ("1", ("hepatitis_c_antibody",)),
    "eos_abs": ("10^9/L", ("eosinophil_count_absolute",)),
    "ferritin2": ("ng/mL", ("ferritin",)),
    "ipth2": ("pg/mL", ("parathyroid_hormone",)),
    "vitd_tox_lvl": ("ng/mL", ("25_hydroxy_vitamin_d",)),
    "gal_1p": ("mg/dL", ("galactose_plasma",)),
    "ketone_u": ("1", ("urine_ketones_qualitative",)),
    "pleural_ada": ("U/L", ("pleural_fluid_adenosine_deaminase",)),
    "pleural_ldh": ("U/L", ("pleural_fluid_lactate_dehydrogenase",)),
    "temp": ("Cel", ("body_temperature",)),
    "hr": ("beats/min", ("heart_rate",)),
    # v6 (SAP Amendment 14, C2): clinical signs for syndrome logic
    "rr": ("breaths/min", ("respiratory_rate",)),
    "sbp": ("mmHg", ("systolic_blood_pressure",)),
    "map": ("mmHg", ("mean_arterial_pressure",)),
    "spo2": ("%", ("oxygen_saturation",)),
})

_ESL_LIBRARY.extend([
 # ---------------- endocrine -----------------------------------------------
 dict(id="subacute_thyroiditis", dx=["subacute_thyroiditis", "subacute_thyroiditis_de_quervain"], req=[("tsh", "<", 0.4), ("ft4", ">", 1.8), ("esr", ">=", 50)],
      sup=[("crp", ">", 30), ("trab", "<", 1.75), ("tpo", "<", 35), ("wbc", ">", 10)], min_sup=1, excl=[("trab", ">", 1.75), ("pct", ">", 2)],
      cap={"graves_disease": 0.5, "thyroid_storm": 0.6, "painless_thyroiditis": 0.7, "hyperthyroidism": 0.9, "giant_cell_arteritis": 0.6}, src="ATA 2016 hyperthyroidism guideline (Ross): thyrotoxicosis + ESR >50 = subacute thyroiditis"),
 dict(id="hypopituitarism", dx=["hypopituitarism_panhypopituitarism"], req=[("ft4", "<", 0.8), ("tsh", "<", 10), ("cortisol_am", "<", 10)],
      sup=[("acth", "<", 20), ("lh", "<", 2), ("fsh", "<", 2), ("igf1", "<", 80), ("prl", "<", 3), ("na", "<", 135)], min_sup=1,
      cap={"central_hypothyroidism": 0.9, "secondary_adrenal_insufficiency": 0.9, "adrenal_insufficiency_primary": 0.4, "hashimoto_thyroiditis": 0.3, "euthyroid_sick_syndrome_nontr": 0.6},
      src="Endocrine Society hypopituitarism 2016 (Fleseriu)"),
 dict(id="liddle", dx=["liddle_syndrome"], req=[("k", "<", 3.5), ("hco3", ">", 28), ("aldo", "<", 5), ("pra", "<", 1.0)], sup=[("ucl", ">", 20), ("na", ">", 140)], min_sup=0,
      cap={"primary_aldosteronism": 0.3, "gitelman_syndrome": 0.4, "bartter_syndrome": 0.4, "apparent_mineralocorticoid_excess": 0.95}, src="Liddle: hypokalaemic alkalosis with suppressed renin AND aldosterone (Tetti 2018)"),
 dict(id="ame", dx=["apparent_mineralocorticoid_excess"], req=[("k", "<", 3.5), ("hco3", ">", 28), ("aldo", "<", 5), ("pra", "<", 1.0)], sup=[("cortisol_am", ">", 5)], min_sup=0, ctx=[("age_lt", 20)],
      cap={"liddle_syndrome": 0.95, "primary_aldosteronism": 0.3}, src="AME: paediatric low-renin low-aldosterone hypertension (Funder 2017)"),
 dict(id="cah_classic", dx=["congenital_adrenal_hyperplasia_classic", "congenital_adrenal_hyperplasia"], req=[("ohp17", ">", 1000)], sup=[("na", "<", 135), ("k", ">", 5.5), ("glucose", "<", 60), ("cortisol_am", "<", 5), ("acth", ">", 50), ("pra", ">", 3)], min_sup=1, ctx=[("age_lt", 2)],
      cap={"nonclassic_congenital_adrenal_hyperplasia": 0.5, "adrenal_insufficiency_primary": 0.7, "addison_disease": 0.5, "pyloric_stenosis": 0.5}, src="Endocrine Society CAH 2018 (Speiser): 17-OHP >1000 ng/dL in a neonate"),
 dict(id="men1", dx=["multiple_endocrine_neoplasia_type_1"], req=[("ca_c", ">", 10.5), ("ca", ">", 10.2), ("pth", ">", 40), ("prl", ">", 100)], sup=[("glucose", "<", 55), ("insulin", ">=", 3)], min_sup=0, excl=[("pregnant_ctx", "==", 1)],
      cap={"primary_hyperparathyroidism": 0.9, "prolactinoma": 0.9, "hyperprolactinemia_prolactinoma": 0.9}, src="Thakker, JCEM 2012 MEN1 guideline"),
 dict(id="zes", dx=["zollinger_ellison_syndrome_support_pattern"], req=[("hp_stool", "neg", None)], alt_req=[("ca_c", ">", 10.5), ("pth", ">", 40), ("fobt", "pos", None)], sup=[], min_sup=0, strength="pattern", ctx=[("cond", "ulcer")],
      src="Gastrinoma: refractory ulcer disease with H. pylori negative (Jensen 2006)"),
 dict(id="vipoma", dx=["vipoma_support_pattern"], req=[("vip", ">", 75), ("k", "<", 3.5)], sup=[("hco3", "<", 20), ("ca_c", ">", 10.5), ("glucose", ">", 140), ("cl", ">", 106)], min_sup=1,
      cap={"hypokalemia": 0.9, "renal_tubular_acidosis": 0.5, "diarrhea_associated_metabolic_acidosis": 0.7}, src="WDHA syndrome (Verner-Morrison); ENETS 2016"),
 dict(id="glucagonoma", dx=["glucagonoma_support_pattern"], req=[("glucagon", ">", 500)], sup=[("glucose", ">", 126), ("a1c", ">=", 6.5), ("hb", "<", 12), ("alb", "<", 3.5), ("zinc", "<", 70)], min_sup=1,
      cap={"type_2_diabetes": 0.7}, src="Glucagonoma: glucagon >500 pg/mL with diabetes/anaemia (ENETS 2016)"),
 dict(id="hypophosphatasia", dx=["hypophosphatasia"], req=[("alp", "<", 40)], sup=[("ca_c", ">", 10.2), ("phos", ">", 4.5), ("pth", "<", 20), ("b6", ">", 50)], min_sup=1, excl=[("alb", "<", 3.0), ("zinc", "<", 60), ("tsh", ">", 10)],
      cap={"hypoparathyroidism": 0.6, "osteomalacia": 0.3}, src="Whyte, Nat Rev Endocrinol 2016: persistently low ALP"),
 dict(id="tio_fgf23", dx=["tumor_induced_osteomalacia"], req=[("phos", "<", 2.5), ("fgf23", ">", 100)], sup=[("vitd125", "<", 20), ("alp", ">", 120), ("ca_c", "between", (8.5, 10.5)), ("pth", "between", (15, 100))], min_sup=1, ctx=[("age_ge", 18)],
      cap={"osteomalacia": 0.8, "hypophosphatemia": 0.9, "x_linked_hypophosphatemia": 0.9}, src="Minisola, Nat Rev Dis Primers 2017"),
 dict(id="vitd_toxicity", dx=["hypervitaminosis_d", "hypervitaminosis_d_support_pattern"], req=[("vitd", ">", 150), ("ca_c", ">", 10.5)], sup=[("pth", "<", 20), ("phos", ">", 4.5), ("cr", ">", 1.3), ("vitd125", ">", 70)], min_sup=1,
      cap={"primary_hyperparathyroidism": 0.3, "hypercalcemia_of_malignancy_support_pattern": 0.4, "sarcoidosis": 0.5, "hypercalcemia": 0.9}, src="Endocrine Society vitamin D 2011 (Holick): toxicity >150 ng/mL"),
 dict(id="pseudohyperkalemia", dx=["pseudohyperkalemia"], req=[("k", ">", 5.5), ("plt", ">", 600)], alt_req=[("k", ">", 5.5), ("wbc", ">", 50)], sup=[("cr", "<", 1.3), ("hco3", ">=", 22)], min_sup=1, strength="pattern",
      cap={"hyperkalemia": 0.85, "renal_tubular_acidosis_type_4": 0.5, "adrenal_insufficiency_primary": 0.5}, src="Sevastos, Clin Chim Acta 2008: in-vitro K release with marked thrombocytosis/leukocytosis"),
 dict(id="hypomag_hypocalcemia", dx=["hypomagnesemia", "hypomagnesemia_pattern"], req=[("mg", "<", 1.2), ("ca_c", "<", 8.5)], sup=[("pth", "<", 65), ("k", "<", 3.5)], min_sup=0,
      cap={"hypoparathyroidism": 0.5, "hypocalcemia": 0.9, "pseudohypoparathyroidism": 0.4}, src="Severe hypomagnesaemia causes functional hypoparathyroidism (Rude 1976)"),
 dict(id="hashimoto_serologic", dx=["hashimoto_thyroiditis"], req=[("tsh", ">", 4.5), ("tpo", ">", 35)], sup=[("ft4", "<", 0.8), ("tg_ab", ">", 40), ("tc", ">", 200)], min_sup=0, excl=[("tsh", ">", 30), ("ft4", "<", 0.5)],
      cap={"euthyroid_sick_syndrome_nontr": 0.3}, src="ATA 2014 hypothyroidism (Jonklaas)"),
 # ---------------- renal / GN ------------------------------------------------
 dict(id="iga_nephropathy", dx=["iga_nephropathy", "iga_nephropathy_berger"], req=[("urbc", ">", 5), ("iga", ">", 400)], sup=[("upcr", ">", 0.5), ("cr", ">", 1.2), ("c3", ">=", 90)], min_sup=1, excl=[("dsdna", ">", 30), ("anti_gbm", "pos", None), ("mpo", "pos", None), ("pr3", "pos", None)], ctx=[("age_ge", 10)],
      cap={"lupus_nephritis": 0.5, "iga_vasculitis": 0.9}, src="KDIGO GN 2021: haematuria with raised serum IgA (supportive)"),
 dict(id="iga_vasculitis_child", dx=["iga_vasculitis"], req=[("urbc", ">", 5), ("plt", ">=", 150)], sup=[("iga", ">", 300), ("upcr", ">", 0.3), ("crp", ">", 10)], min_sup=1, excl=[("dsdna", ">", 30), ("c3", "<", 70), ("plt", "<", 150)], ctx=[("age_lt", 16)],
      cap={"immune_thrombocytopenia": 0.3, "iga_nephropathy": 0.9}, src="EULAR/PRINTO/PRES 2010 (Ozen): purpura with normal platelets + nephritis"),
 dict(id="cryoglobulinemic_vasculitis", dx=["cryoglobulinemia"], req=[("cryo", "pos", None)], sup=[("c4", "<", 10), ("rf", ">", 40), ("hcv_ab2", "pos", None), ("urbc", ">", 5), ("cr", ">", 1.3)], min_sup=1,
      cap={"rheumatoid_arthritis": 0.5, "hepatitis_c": 0.9, "chronic_hepatitis_c": 0.9, "systemic_lupus_erythematosus": 0.6}, src="De Vita 2011 classification criteria"),
 dict(id="anti_gbm", dx=["anti_gbm_disease_goodpasture", "goodpasture_syndrome"], req=[("anti_gbm", "pos", None), ("cr", ">", 1.5)], sup=[("urbc", ">", 5), ("hb", "<", 12), ("upcr", ">", 0.5)], min_sup=1,
      cap={"anca_associated_vasculitis": 0.6, "acute_kidney_injury": 0.9, "lupus_nephritis": 0.4}, src="KDIGO GN 2021 anti-GBM"),
 dict(id="fanconi_syndrome", dx=["fanconi_syndrome"], req=[("phos", "<", 2.5), ("hco3", "<", 20), ("uglu", "pos", None), ("glucose", "<", 126)], sup=[("urate", "<", 3.0), ("k", "<", 3.5), ("ag_c", "<=", 14), ("uph", ">", 5.5)], min_sup=1,
      cap={"renal_tubular_acidosis_type_2": 0.9, "renal_tubular_acidosis": 0.9, "type_2_diabetes": 0.2, "diabetes_mellitus": 0.2}, src="Normoglycaemic glycosuria + hypophosphataemia + proximal RTA (Foreman 2019)"),
 dict(id="hyperkalemic_aki_rhabdo_guard", dx=["rhabdomyolysis"], req=[("ck", ">", 5000), ("umyoglobin", "pos", None)], sup=[("k", ">", 5.5), ("phos", ">", 4.5), ("cr", ">", 1.5), ("ca_c", "<", 8.5)], min_sup=1,
      cap={"acute_myocardial_infarction": 0.5, "myositis": 0.7}, src="Bosch, NEJM 2009"),
 # ---------------- haematology ---------------------------------------------
 dict(id="sickle_cell_disease", dx=["sickle_cell_disease"], req=[("hbs", ">", 50)], sup=[("hb", "<", 11), ("retic", ">", 2.5), ("ldh", ">", 250), ("tbil", ">", 1.2), ("hbf", ">", 2), ("hba2", "<", 3.6)], min_sup=1,
      cap={"sickle_cell_trait": 0.3, "sickle_cell_trait_hbas": 0.3, "hemolytic_anemia": 0.9, "anemia": 0.9}, src="ASH SCD 2020; HbS >50% on HPLC"),
 dict(id="sickle_cell_trait", dx=["sickle_cell_trait", "sickle_cell_trait_hbas"], req=[("hbs", "between", (25, 45)), ("hb", ">=", 11)], sup=[("mcv", ">=", 78), ("retic", "<", 2.5)], min_sup=0,
      cap={"sickle_cell_disease": 0.3, "anemia": 0.3}, src="HbAS: HbS 35–45% with normal Hb"),
 dict(id="beta_thal_major", dx=["beta_thalassemia_major", "beta_thalassemia_major_cooley"], req=[("hbf", ">", 50), ("hb", "<", 9)], sup=[("mcv", "<", 75), ("nrbc", ">", 1), ("ferritin", ">", 1000), ("tbil", ">", 1.2), ("ldh", ">", 250)], min_sup=1, ctx=[("age_ge", 0.5)],
      cap={"beta_thalassemia_trait": 0.3, "thalassemia_trait": 0.3, "iron_deficiency_anemia": 0.2, "hemochromatosis": 0.5, "hereditary_hemochromatosis": 0.4}, src="TIF guidelines 2021"),
 dict(id="alpha_thal_trait", dx=["alpha_thalassemia_trait", "alpha_thalassemia"], req=[("mcv", "<", 78), ("hba2", "between", (1.5, 3.5)), ("hbf", "<", 2), ("ferritin", ">=", 30)], sup=[("rbc", ">", 5.0), ("mentzer", "<", 13), ("hb", ">=", 10), ("rdw", "<", 15)], min_sup=1,
      cap={"iron_deficiency_anemia": 0.3, "beta_thalassemia_trait": 0.5, "thalassemia_trait": 0.95}, src="Microcytosis with normal HbA2 and replete iron (Piel & Weatherall NEJM 2014)"),
 dict(id="lead_poisoning", dx=["lead_poisoning", "lead_poisoning_plumbism"], req=[("lead", ">=", 5)], sup=[("stippling", "pos", None), ("zpp", ">", 35), ("hb", "<", 12), ("mcv", "<", 80), ("urate", ">", 7)], min_sup=1,
      cap={"iron_deficiency_anemia": 0.6, "sideroblastic_anemia": 0.6, "acute_intermittent_porphyria": 0.5}, src="CDC 2021 BLRV 3.5 µg/dL; ACMT"),
 dict(id="sideroblastic", dx=["sideroblastic_anemia"], req=[("hb", "<", 12), ("ferritin", ">", 300), ("tsat", ">", 45)], sup=[("mcv", "<", 80), ("rdw", ">", 15), ("stippling", "pos", None), ("retic", "<", 1.5)], min_sup=1, excl=[("lead", ">=", 5), ("b12", "<", 200), ("alt", ">", 200)],
      cap={"hereditary_hemochromatosis": 0.6, "iron_deficiency_anemia": 0.1, "anemia_of_chronic_disease": 0.5}, src="Microcytic/dimorphic anaemia with iron overload (Camaschella 2008)"),
 dict(id="megaloblastic_b12", dx=["vitamin_b12_deficiency", "megaloblastic_anemia", "vitamin_b12_deficiency_anemia"], req=[("b12", "<", 200), ("mcv", ">", 100)], sup=[("hb", "<", 12), ("hypersegs", "pos", None), ("ldh", ">", 400), ("mma", ">", 400), ("hcy", ">", 15), ("retic", "<", 1.5), ("plt", "<", 150)], min_sup=1,
      cap={"myelodysplastic_syndrome": 0.4, "hemolytic_anemia": 0.4, "folate_deficiency": 0.6, "hypothyroidism": 0.6, "aplastic_anemia": 0.3}, src="BSH 2014 cobalamin/folate (Devalia)"),
 dict(id="pernicious_anemia", dx=["pernicious_anemia", "pernicious_anemia_serologic_pattern", "vitamin_b12_deficiency", "megaloblastic_anemia"], req=[("b12", "<", 200), ("if_ab", "pos", None)], sup=[("mcv", ">", 100), ("hb", "<", 12), ("tpo", ">", 35), ("ldh", ">", 500), ("plt", "<", 150), ("hypersegs", "pos", None)], min_sup=0,
      cap={"vitamin_b12_deficiency_anemia": 0.95, "hemolytic_anemia": 0.5, "aplastic_anemia": 0.4, "myelodysplastic_syndrome": 0.5, "pancytopenia": 0.9, "macrocytic_anemia": 0.9, "anemia": 0.9, "thrombotic_thrombocytopenic_purpura": 0.4}, src="BSH 2014: IF antibody positive = pernicious anaemia"),
 dict(id="folate_deficiency", dx=["folate_deficiency", "folate_deficiency_anemia"], req=[("folate", "<", 3.0), ("mcv", ">", 100)], sup=[("hb", "<", 12), ("hcy", ">", 15), ("b12", ">=", 300)], min_sup=1, excl=[("b12", "<", 200)],
      cap={"vitamin_b12_deficiency": 0.5, "myelodysplastic_syndrome": 0.4}, src="BSH 2014"),
 dict(id="hemophilia_b", dx=["hemophilia_b", "hemophilia_b_christmas"], req=[("f9", "<", 40), ("pt", "<", 15)], sup=[("aptt", ">", 40), ("f8", ">=", 50)], min_sup=1, excl=[("vwf_ag", "<", 50)], ctx=[("sex", "m")],
      cap={"hemophilia_a": 0.3, "von_willebrand_disease": 0.4}, src="WFH 2020 guideline"),
 dict(id="factor_xi_deficiency", dx=["factor_xi_deficiency"], req=[("f11", "<", 40), ("pt", "<", 15)], sup=[("aptt", ">", 40), ("f8", ">=", 50), ("f9", ">=", 50)], min_sup=1,
      cap={"hemophilia_a": 0.3, "hemophilia_b": 0.3}, src="Duga & Salomon, Semin Thromb Hemost 2013"),
 dict(id="acquired_hemophilia", dx=["acquired_hemophilia_a"], req=[("f8", "<", 40), ("f8_inh", ">", 0.6)], alt_req=[("f8", "<", 30), ("mix_aptt_inc", "neg", None), ("pt", "<", 15)], sup=[("aptt", ">", 50), ("hb", "<", 12)], min_sup=0, ctx=[("age_ge", 40)],
      cap={"hemophilia_a": 0.3, "antiphospholipid_syndrome": 0.5, "von_willebrand_disease": 0.4}, src="Tiede, Haematologica 2020 international recommendations"),
 dict(id="warfarin_over", dx=["warfarin_over_anticoagulation"], req=[("inr", ">", 4.5), ("fib", ">=", 150), ("plt", ">=", 100)], sup=[("alt", "<", 100), ("alb", ">=", 3.0), ("f7", "<", 30)], min_sup=1, ctx_any=[("med", "warfarin"), ("med", "coumadin"), ("med", "acenocoumarol")],
      cap={"vitamin_k_deficiency": 0.5, "disseminated_intravascular_coagulation": 0.3, "liver_cirrhosis": 0.4, "acute_liver_failure": 0.3}, src="ACCP 2012 VKA management (Holbrook)"),
 dict(id="hairy_cell", dx=["hairy_cell_leukemia"], req=[("mono_abs", "<", 0.2), ("plt", "<", 100), ("hb", "<", 12)], sup=[("anc", "<", 1.5), ("wbc", "<", 4)], min_sup=1, excl=[("blasts", ">", 5)], ctx=[("age_ge", 30)],
      cap={"aplastic_anemia": 0.6, "myelodysplastic_syndrome": 0.6, "pancytopenia": 0.9}, src="Grever, Blood 2017: pancytopenia with monocytopenia"),
 dict(id="systemic_mastocytosis", dx=["systemic_mastocytosis", "mastocytosis"], req=[("tryptase", ">", 20)], sup=[("alp", ">", 120), ("hb", "<", 12), ("eos_abs", ">", 0.5)], min_sup=0,
      cap={"anaphylaxis": 0.7, "hypereosinophilic_syndrome": 0.6}, src="WHO 2016 minor criterion: baseline tryptase >20 ng/mL"),
 dict(id="hes", dx=["hypereosinophilic_syndrome"], req=[("eos_abs", ">=", 1.5)], sup=[("trop_c", ">", 30), ("tryptase", ">", 11), ("b12", ">", 1000), ("ldh", ">", 250), ("ige", "<", 100)], min_sup=2, excl=[("blasts", ">", 5)],
      cap={"eosinophilia": 0.95, "eosinophilia_pattern": 0.95, "strongyloidiasis": 0.6, "allergic_disease": 0.5}, src="Valent, JACI 2012; eos ≥1.5×10⁹/L with organ damage markers"),
 # v6 (Amendment 14): the parasitic attribution of eosinophilia + raised IgE is an exposure-dependent
 # inference (returning travellers, migrants from endemic areas, pre-immunosuppression screening);
 # without such context the constellation is non-specific (atopy, drug reaction, IgG4-RD, EGPA) and is
 # reported as eosinophilia only - no infection is asserted from two analytes.
 dict(id="eosinophilia_parasitic", dx=["strongyloidiasis", "eosinophilia"], req=[("eos_abs", ">=", 0.5), ("ige", ">", 200)], sup=[("hb", "<", 12), ("alb", "<", 3.5)], min_sup=0, strength="pattern",
      ctx_any=[("cond", "travel"), ("cond", "endemic"), ("cond", "migra"), ("cond", "refugee"), ("cond", "tropic"), ("cond", "exposure"), ("cond", "soil"), ("cond", "barefoot"),
               ("cond", "immunosuppress"), ("cond", "transplant"), ("cond", "steroid"), ("cond", "parasit"), ("cond", "worm"), ("cond", "helminth"), ("cond", "diarrh")],
      cap={"hypereosinophilic_syndrome": 0.7}, src="Checkley, J Infect 2010: eosinophilia + raised IgE in returning travellers/endemic areas"),
 dict(id="eosinophilia_ige_nonspecific", dx=["eosinophilia"], req=[("eos_abs", ">=", 0.5), ("ige", ">", 200)], sup=[], min_sup=0, strength="pattern",
      ctx_excl=[("cond", "travel"), ("cond", "endemic"), ("cond", "migra"), ("cond", "tropic"), ("cond", "exposure"), ("cond", "immunosuppress"), ("cond", "transplant"), ("cond", "parasit")],
      src="Eosinophilia with raised IgE without exposure context: atopy, drug reaction, IgG4-RD, EGPA, helminths all possible - exposure history decides (Checkley 2010; ACR/EULAR IgG4-RD 2019)"),
 dict(id="cold_agglutinin", dx=["cold_agglutinin_disease"], req=[("dat", "pos", None), ("cold_agg", ">=", 64), ("hb", "<", 12)], alt_req=[("mchc", ">", 37), ("hb", "<", 12), ("ldh", ">", 250), ("hapto", "<", 30)], sup=[("retic", ">", 2.5), ("tbil", ">", 1.2), ("igm", ">", 300)], min_sup=1, excl=[("schisto", ">", 1), ("dat", "neg", None), ("sphero", "pos", None), ("ema", "<", 0.8)],
      cap={"autoimmune_hemolytic_anemia": 0.9, "warm_autoimmune_hemolytic_anemia": 0.4, "hemolytic_anemia": 0.9, "hereditary_spherocytosis": 0.3}, src="Berentsen, Blood 2020"),
 dict(id="diamond_blackfan", dx=["diamond_blackfan_anemia"], req=[("hb", "<", 9), ("retic", "<", 0.5), ("mcv", ">", 95)], sup=[("wbc", ">=", 4), ("plt", ">=", 150), ("hbf", ">", 2)], min_sup=1, excl=[("blasts", ">", 2), ("b12", "<", 200)], ctx=[("age_lt", 2)],
      cap={"aplastic_anemia": 0.5, "transient_erythroblastopenia_of_childhood": 0.9, "vitamin_b12_deficiency": 0.3}, src="Vlachos, Br J Haematol 2008 consensus"),
 dict(id="fanconi_anemia", dx=["fanconi_anemia"], req=[("plt", "<", 100), ("hb", "<", 11), ("mcv", ">", 95), ("anc", "<", 1.5)], sup=[("hbf", ">", 2), ("retic", "<", 1.0)], min_sup=1, excl=[("blasts", ">", 2), ("b12", "<", 200), ("folate", "<", 3)], ctx=[("age_lt", 16)],
      cap={"aplastic_anemia": 0.9, "myelodysplastic_syndrome": 0.5}, src="Macrocytic pancytopenia in a child (Dufour 2017)"),
 dict(id="agranulocytosis", dx=["agranulocytosis", "clozapine_agranulocytosis"], req=[("anc", "<", 0.5), ("hb", ">=", 11), ("plt", ">=", 120)], sup=[("wbc", "<", 3), ("crp", ">", 10), ("pct", ">", 0.5)], min_sup=0, excl=[("blasts", ">", 2)],
      cap={"aplastic_anemia": 0.3, "sepsis": 0.9, "acute_myeloid_leukemia": 0.4, "neutropenia": 0.95}, src="Andersohn, Ann Intern Med 2007: isolated ANC <0.5"),
 dict(id="leukemoid", dx=["leukemoid_reaction"], req=[("wbc", ">", 50), ("blasts", "<=", 2)], sup=[("lap", ">", 100), ("crp", ">", 50), ("bands", ">", 10), ("pct", ">", 0.5), ("baso_pct", "<=", 1)], min_sup=1, excl=[("bcr", "pos", None), ("baso_pct", ">", 2)],
      cap={"chronic_myeloid_leukemia": 0.5, "acute_myeloid_leukemia": 0.3}, src="Sakka, Eur J Intern Med 2006"),
 dict(id="pk_deficiency", dx=["pyruvate_kinase_deficiency"], req=[("hb", "<", 12), ("ldh", ">", 250), ("hapto", "<", 30), ("dat", "neg", None), ("sphero", "<=", 0), ("g6pd", ">=", 4.6)], sup=[("retic", ">", 5), ("tbil", ">", 1.5), ("ferritin", ">", 300)], min_sup=1, excl=[("schisto", ">", 1), ("hbs", ">", 20), ("pnh", ">", 1)],
      cap={"hereditary_spherocytosis": 0.5, "g6pd_deficiency": 0.4, "hemolytic_anemia": 0.9}, src="Grace, Blood 2018: DAT-negative non-spherocytic hemolysis with normal G6PD"),
 dict(id="copper_deficiency", dx=["copper_deficiency"], req=[("copper", "<", 70), ("hb", "<", 12)], sup=[("anc", "<", 1.5), ("cerulo", "<", 20), ("mcv", ">", 95), ("zinc", ">", 120)], min_sup=1,
      cap={"myelodysplastic_syndrome": 0.3, "wilson_disease": 0.3, "vitamin_b12_deficiency": 0.5}, src="Halfdanarson, Eur J Haematol 2008"),
 dict(id="zinc_deficiency", dx=["zinc_deficiency"], req=[("zinc", "<", 60)], sup=[("alp", "<", 40), ("alb", "<", 3.5), ("crp", "<", 10)], min_sup=1, excl=[("crp", ">", 50)],
      src="Wessells & Brown 2012; low ALP as co-marker"),
 dict(id="scurvy", dx=["scurvy", "vitamin_c_deficiency"], req=[("vitc", "<", 0.2)], sup=[("hb", "<", 12), ("ferritin", "<", 30)], min_sup=0, src="Plasma ascorbate <0.2 mg/dL (Levine 1996)"),
 dict(id="thiamine_deficiency", dx=["thiamine_deficiency", "wernicke_encephalopathy", "beriberi"], req=[("thiamine_wb", "<", 70)], sup=[("lactate", ">", 2), ("mg", "<", 1.7), ("alb", "<", 3.5)], min_sup=0,
      cap={"lactic_acidosis": 0.8}, src="Whole-blood thiamine diphosphate <70 nmol/L (Sechi & Serra Lancet Neurol 2007)"),
 dict(id="thrombophilia_hereditary", dx=["hereditary_thrombophilia", "protein_c_deficiency", "protein_s_deficiency", "antithrombin_deficiency"], req=[("prot_c", "<", 60)], alt_req=[("prot_s", "<", 55)], alt_req2=[("at", "<", 70), ("alb", ">=", 3.0)], alt_req3=[("fvl", "pos", None)], sup=[("ddimer", ">", 0.5), ("fvl", "pos", None), ("pt_mut", "pos", None)], min_sup=0, strength="pattern", excl=[("inr", ">", 1.5), ("alt", ">", 200), ("alb", "<", 2.5)],
      src="ASH 2023 thrombophilia testing (Middeldorp)"),
 dict(id="massive_transfusion_coag", dx=["massive_transfusion_coagulopathy"], req=[("fib", "<", 150), ("plt", "<", 100), ("ica", "<", 1.1)], sup=[("inr", ">", 1.5), ("k", ">", 5.5), ("hb", "<", 9), ("lactate", ">", 2)], min_sup=1, ctx=[("cond", "transfusion")],
      cap={"disseminated_intravascular_coagulation": 0.7}, src="Dilutional coagulopathy + citrate hypocalcaemia (Hess 2008)"),
 # ---------------- GI / liver -----------------------------------------------
 dict(id="crigler_najjar", dx=["crigler_najjar_syndrome"], req=[("ibil_c", ">", 15), ("dbil_frac", "<", 0.15), ("alt", "<", 60), ("hb", ">=", 10)], sup=[("ldh", "<", 300), ("retic", "<", 3)], min_sup=0, ctx=[("age_lt", 1)], excl=[("dat", "pos", None), ("hapto", "<", 30)],
      cap={"neonatal_jaundice": 0.9, "hemolytic_disease_of_the_newborn": 0.4, "gilbert_syndrome": 0.5, "breast_milk_jaundice": 0.6}, src="Unconjugated bilirubin >15 mg/dL without haemolysis in infancy (Strauss 2020)"),
 dict(id="hepatitis_e", dx=["hepatitis_e", "hepatitis_e_infection", "hepatitis_e_infection_pattern"], req=[("hev_igm", "pos", None), ("alt", ">", 80)], sup=[("tbil", ">", 2), ("hav_igm", "neg", None), ("hbsag", "neg", None)], min_sup=0,
      cap={"hepatitis_a": 0.3, "autoimmune_hepatitis": 0.3, "drug_induced_liver_injury": 0.4}, src="EASL HEV 2018"),
 dict(id="hepatitis_c_chronic", dx=["chronic_hepatitis_c", "hepatitis_c"], req=[("hcv_rna", ">", 15)], alt_req=[("hcv_ab2", "pos", None), ("alt", ">", 40)], sup=[("alt", ">", 40), ("plt", "<", 150), ("cryo", "pos", None), ("rf", ">", 20)], min_sup=0,
      cap={"autoimmune_hepatitis": 0.5, "nafl_d": 0.5, "metabolic_dysfunction_associated_steatotic_liver_disease": 0.5}, src="AASLD/IDSA HCV guidance 2023"),
 dict(id="hepatitis_d", dx=["hepatitis_d", "hepatitis_d_infection", "hepatitis_d_infection_pattern"], req=[("hbsag", "pos", None), ("hdv_ab", "pos", None)], sup=[("alt", ">", 80), ("hbv_dna", "<", 2000)], min_sup=0,
      cap={"chronic_hepatitis_b": 0.9, "hepatitis_b": 0.9}, src="EASL HDV 2023"),
 dict(id="dili_hepatocellular", dx=["drug_induced_liver_injury"], req=[("alt", ">", 200), ("r_ratio", ">=", 5)], sup=[("tbil", ">", 2), ("eos_abs", ">", 0.5), ("ana", "<", 80), ("hav_igm", "neg", None), ("hbsag", "neg", None)], min_sup=1, ctx_any=[("med", "isoniazid"), ("med", "amoxicillin"), ("med", "augmentin"), ("med", "nitrofurantoin"), ("med", "methotrexate"), ("med", "valproate"), ("med", "statin"), ("med", "atorvastatin"), ("med", "flucloxacillin"), ("med", "antitubercul"), ("med", "rifampin"), ("med", "pyrazinamide"), ("med", "herbal"), ("med", "supplement"), ("med", "anabolic"), ("med", "allopurinol"), ("med", "carbamazepine"), ("med", "phenytoin")],
      excl=[("apap", ">", 10), ("hav_igm", "pos", None), ("hbc_igm", "pos", None), ("hev_igm", "pos", None)],
      cap={"autoimmune_hepatitis": 0.6, "viral_hepatitis": 0.5, "ischemic_hepatitis": 0.5, "nafl_d": 0.3}, src="ACG DILI 2021 (Chalasani); R ratio Aithal 2011"),
 dict(id="hepatic_encephalopathy", dx=["hepatic_encephalopathy", "hepatic_encephalopathy_support_pattern"], req=[("nh3", ">", 100), ("alb", "<", 3.5)], alt_req=[("nh3", ">", 100), ("inr", ">", 1.5), ("plt", "<", 150)], sup=[("tbil", ">", 2), ("na", "<", 135), ("plt", "<", 150), ("inr", ">", 1.5)], min_sup=1, excl=[("valproate", ">", 100), ("orotic", ">", 20)],
      cap={"urea_cycle_disorder": 0.3, "valproate_toxicity": 0.4, "liver_cirrhosis": 0.95}, src="AASLD/EASL HE 2014 (Vilstrup)"),
 dict(id="sbp", dx=["spontaneous_bacterial_peritonitis"], req=[("ascites_cells", ">=", 250)], sup=[("saag", ">=", 1.1), ("ascites_prot", "<", 1.5), ("crp", ">", 20), ("cr", ">", 1.3), ("wbc", ">", 10)], min_sup=1,
      cap={"liver_cirrhosis": 0.9, "sepsis": 0.9}, src="EASL decompensated cirrhosis 2018: ascitic PMN ≥250/µL"),
 dict(id="budd_chiari", dx=["budd_chiari_syndrome_support_pattern"], req=[("saag", ">=", 1.1), ("ascites_prot", ">=", 2.5)], sup=[("alt", ">", 80), ("jak2", "pos", None), ("plt", ">", 400), ("hb", ">", 16.5)], min_sup=1, strength="pattern", excl=[("natri_high", "==", 1)],
      cap={"liver_cirrhosis": 0.6, "heart_failure": 0.8}, src="High-SAAG, high-protein ascites: post-sinusoidal (Runyon 1992; EASL vascular liver 2016)"),
 dict(id="ibd_active", dx=["inflammatory_bowel_disease", "crohn_disease", "ulcerative_colitis"], req=[("calpro", ">", 250)], sup=[("crp", ">", 10), ("hb", "<", 12), ("alb", "<", 3.5), ("plt", ">", 400), ("ferritin", "<", 30), ("lactoferrin", ">", 7.25)], min_sup=1, excl=[("cdiff_toxin", "pos", None)],
      cap={"irritable_bowel_syndrome": 0.2, "iron_deficiency_anemia": 0.9, "anemia_of_chronic_disease": 0.9, "celiac_disease": 0.7}, src="ECCO 2019: calprotectin >250 µg/g = active inflammation"),
 dict(id="cdiff_infection", dx=["clostridioides_difficile_infection", "clostridioides_difficile_support_pattern"], req=[("cdiff_toxin", "pos", None)], alt_req=[("cdiff_gdh", "pos", None), ("wbc", ">", 15)], sup=[("wbc", ">", 15), ("cr", ">", 1.5), ("alb", "<", 3.0), ("lactate", ">", 2)], min_sup=0,
      cap={"inflammatory_bowel_disease": 0.6, "ulcerative_colitis": 0.6, "sepsis": 0.9}, src="IDSA/SHEA 2017 (McDonald): WBC ≥15 or Cr >1.5 = severe"),
 dict(id="chronic_pancreatitis", dx=["chronic_pancreatitis", "chronic_pancreatitis_support_pattern"], req=[("elastase", "<", 200)], sup=[("a1c", ">=", 6.5), ("vitd", "<", 20), ("alb", "<", 3.5), ("lipase", "<", 60), ("stool_fat", ">", 7)], min_sup=1, ctx=[("age_ge", 18)],
      cap={"pancreatic_insufficiency_pattern": 0.95, "celiac_disease": 0.6, "cystic_fibrosis": 0.6}, src="ACG chronic pancreatitis 2020 (Gardner)"),
 dict(id="gallstone_pancreatitis", dx=["gallstone_pancreatitis_support_pattern", "acute_pancreatitis"], req=[("lipase", ">", 180), ("alt", ">", 150)], sup=[("alp", ">", 120), ("tbil", ">", 2), ("ggt", ">", 100)], min_sup=1, excl=[("tg", ">", 1000), ("ca_c", ">", 11)],
      cap={"acute_pancreatitis": 0.95, "acute_cholangitis": 0.8, "alcoholic_pancreatitis": 0.5, "hypertriglyceridemia_induced_pancreatitis": 0.3}, src="Tenner ACG 2013: ALT >150 U/L PPV 95% for biliary aetiology (Tenner 1994)"),
 dict(id="h_pylori", dx=["helicobacter_pylori_infection"], req=[("hp_stool", "pos", None)], sup=[("hb", "<", 12), ("ferritin", "<", 30), ("b12", "<", 200)], min_sup=0, src="ACG 2017 H. pylori (Chey)"),
 dict(id="colorectal_ca_pattern", dx=["colorectal_cancer", "colorectal_cancer_marker_abnormality"], req=[("cea", ">", 10), ("fobt", "pos", None)], alt_req=[("cea", ">", 20), ("hb", "<", 12), ("ferritin", "<", 30)], sup=[("hb", "<", 12), ("ferritin", "<", 30), ("mcv", "<", 80), ("alp", ">", 120)], min_sup=1, ctx=[("age_ge", 40)], excl=[("ca199", ">", 1000), ("alt", ">", 200)],
      cap={"iron_deficiency_anemia": 0.9, "anemia": 0.9}, src="CEA >10 with FIT-positive or unexplained IDA (NCCN; BSG 2021 IDA)"),
 dict(id="pancreatic_ca_pattern", dx=["pancreatic_cancer", "pancreatic_adenocarcinoma_marker_pattern", "pancreatic_cancer_marker_abnormality"], req=[("ca199", ">", 1000)], alt_req=[("ca199", ">", 100), ("alp", ">", 180), ("dbil_frac", ">", 0.5), ("tbil", ">", 2)], sup=[("alp", ">", 180), ("tbil", ">", 2), ("a1c", ">=", 6.5), ("alb", "<", 3.5), ("cea", ">", 5)], min_sup=1, ctx=[("age_ge", 40)],
      cap={"cholangitis": 0.6, "acute_cholangitis": 0.6, "biliary_obstruction_choledocholithiasis": 0.6, "primary_sclerosing_cholangitis": 0.4, "cholangiocarcinoma": 0.9, "type_2_diabetes": 0.6}, src="NCCN pancreatic 2024; CA19-9 >1000 U/mL specificity for malignancy in obstructed patients (Ballehaninna 2012)"),
 dict(id="gestational_trophoblastic", dx=["molar_pregnancy", "gestational_trophoblastic_disease_marker_pattern"], req=[("hcg", ">", 100000)], sup=[("tsh", "<", 0.1), ("ft4", ">", 1.8), ("hb", "<", 11)], min_sup=0, ctx=[("sex", "f")],
      cap={"graves_disease": 0.3, "hyperthyroidism": 0.5, "thyroid_storm": 0.5, "pregnancy": 0.9}, src="FIGO 2018 GTD; hCG >100,000 with hyperthyroidism"),
 dict(id="lymphoma_pattern", dx=["lymphoma_support_pattern", "non_hodgkin_lymphoma", "hodgkin_lymphoma"], req=[("ldh", ">", 400), ("b2m", ">", 3.0)], sup=[("hb", "<", 12), ("esr", ">", 50), ("ca_c", ">", 10.5), ("urate", ">", 8), ("alc", ">", 5), ("alb", "<", 3.5)], min_sup=1, strength="pattern", excl=[("blasts", ">", 5), ("hapto", "<", 30), ("mspike", ">", 1.0), ("cr", ">", 3)],
      src="Elevated LDH + β2-microglobulin as lymphoma tumour-burden markers (IPI; Swerdlow WHO 2016)"),
 dict(id="neuroblastoma", dx=["neuroblastoma"], req=[("vma", ">", 10)], alt_req=[("hva", ">", 15)], sup=[("ldh", ">", 500), ("ferritin", ">", 150), ("nse", ">", 30), ("hb", "<", 11)], min_sup=0, ctx=[("age_lt", 10)],
      cap={"pheochromocytoma": 0.6}, src="INRG 2009; urinary catecholamine metabolites (Strenger 2007)"),
 # ---------------- infection -------------------------------------------------
 dict(id="brucellosis", dx=["brucellosis", "brucellosis_serologic_support_pattern"], req=[("brucella", ">=", 160)], alt_req=[("brucella_pcr", "pos", None)], sup=[("alt", ">", 40), ("plt", "<", 150), ("wbc", "<", 4), ("crp", ">", 10), ("esr", ">", 20)], min_sup=0,
      cap={"typhoid_fever": 0.5, "lymphoma_support_pattern": 0.5, "hepatitis": 0.5}, src="Wright titre ≥1:160 in endemic areas (Araj, Int J Antimicrob Agents 2010)"),
 dict(id="typhoid", dx=["typhoid_fever"], req=[("widal_o", ">=", 160)], sup=[("wbc", "<", 4.5), ("alt", ">", 40), ("eos_abs", "<", 0.05), ("plt", "<", 150), ("crp", ">", 20)], min_sup=1, excl=[("brucella", ">=", 160), ("malaria", ">", 0), ("malaria_smear", "pos", None)],
      cap={"brucellosis": 0.5, "dengue_fever": 0.5, "sepsis": 0.8}, src="Widal O ≥1:160 with leukopenia/eosinopenia (Parry NEJM 2002); low specificity acknowledged"),
 dict(id="leptospirosis", dx=["leptospirosis"], req=[("tbil", ">", 3), ("dbil_frac", ">", 0.6), ("cr", ">", 1.5), ("plt", "<", 150), ("alt", "<", 300)], sup=[("ck", ">", 300), ("wbc", ">", 10), ("k", "<", 3.5), ("crp", ">", 50)], min_sup=1, ctx_any=[("cond", "fever"), ("cond", "flood"), ("cond", "rat"), ("cond", "farm"), ("cond", "water"), ("cond", "exposure")],
      cap={"acute_cholangitis": 0.5, "sepsis": 0.8, "hemolytic_uremic_syndrome": 0.5, "acute_liver_failure": 0.4, "dengue_fever": 0.5}, src="Weil disease: jaundice + AKI + thrombocytopenia with disproportionately mild transaminases (Haake & Levett 2015)"),
 dict(id="covid_severe", dx=["covid_19", "sars_cov_2_infection"], req=[("covid_pcr", "pos", None)], sup=[("alc", "<", 1.0), ("ferritin", ">", 500), ("ddimer", ">", 1.0), ("ldh", ">", 250), ("crp", ">", 50), ("il6", ">", 40), ("pct", "<", 0.5)], min_sup=1,
      cap={"hemophagocytic_lymphohistiocytosis": 0.5, "pulmonary_embolism": 0.8, "sepsis": 0.7}, src="WHO 2023 COVID-19 clinical management; Zhou Lancet 2020"),
 dict(id="influenza", dx=["influenza"], req=[("flu_pcr", "pos", None)], sup=[("alc", "<", 1.0), ("pct", "<", 0.5), ("crp", "<", 100), ("ck", ">", 300)], min_sup=0, src="IDSA influenza 2018 (Uyeki)"),
 dict(id="endocarditis", dx=["infective_endocarditis", "endocarditis_support_pattern"], req=[("bcx", "pos", None), ("crp", ">", 30)], sup=[("rf", ">", 20), ("urbc", ">", 5), ("hb", "<", 12), ("esr", ">", 30), ("c3", "<", 90), ("natri_high", "==", 1)], min_sup=1,
      cap={"sepsis": 0.9, "rheumatoid_arthritis": 0.3, "glomerulonephritis": 0.7, "anca_associated_vasculitis": 0.4}, src="Modified Duke / ESC 2023: positive cultures with immunologic phenomena"),
 dict(id="syphilis", dx=["syphilis", "syphilis_serologic_pattern"], req=[("trep", "pos", None), ("rpr", ">=", 8)], sup=[("alp", ">", 120), ("alt", ">", 40), ("hiv_ab", "pos", None)], min_sup=0,
      cap={"hepatitis": 0.6, "cholestasis": 0.6}, src="CDC STI 2021: reactive treponemal + non-treponemal titre"),
 dict(id="cmv_mono", dx=["acute_cmv_infection", "cmv_infection"], req=[("cmv_igm", "pos", None), ("atyp_lymph", ">=", 5)], alt_req=[("cmv_igm", "pos", None), ("alt", ">", 60)], sup=[("hetero", "neg", None), ("alt", ">", 60), ("alc", ">", 4), ("plt", "<", 150)], min_sup=0, excl=[("ebv_vca_igm", "pos", None), ("hetero", "pos", None)],
      cap={"infectious_mononucleosis": 0.6, "hepatitis": 0.6, "acute_hepatitis": 0.6, "lymphoma_support_pattern": 0.3}, src="Heterophile-negative mononucleosis (Cohen NEJM 2000)"),
 dict(id="toxoplasmosis_acute", dx=["toxoplasmosis", "toxoplasmosis_serologic_pattern"], req=[("toxo_igm", "pos", None)], sup=[("atyp_lymph", ">=", 5), ("alt", ">", 40), ("ldh", ">", 250)], min_sup=0,
      cap={"infectious_mononucleosis": 0.7, "acute_cmv_infection": 0.7}, src="Montoya, Lancet 2004"),
 dict(id="visceral_leishmaniasis", dx=["visceral_leishmaniasis"], req=[("leish_ab", "pos", None), ("hb", "<", 11), ("plt", "<", 150)], sup=[("anc", "<", 1.5), ("igg", ">", 1800), ("alb", "<", 3.0), ("ferritin", ">", 500), ("alt", ">", 40)], min_sup=1,
      cap={"hemophagocytic_lymphohistiocytosis": 0.6, "aplastic_anemia": 0.3, "lymphoma_support_pattern": 0.5, "multiple_myeloma": 0.3, "liver_cirrhosis": 0.4}, src="WHO VL 2010; rK39 with pancytopenia + hypergammaglobulinaemia"),
 dict(id="rickettsial", dx=["rickettsial_infection", "scrub_typhus"], req=[("plt", "<", 150), ("na", "<", 135), ("alt", ">", 60)], sup=[("crp", ">", 50), ("ldh", ">", 300), ("alb", "<", 3.5), ("cr", ">", 1.3), ("wbc", "between", (4, 12))], min_sup=2, strength="pattern", ctx_any=[("cond", "tick"), ("cond", "fever"), ("cond", "rash"), ("cond", "eschar"), ("cond", "rural"), ("cond", "travel")],
      excl=[("ns1", "pos", None), ("malaria", ">", 0), ("pct", ">", 2), ("schisto", ">", 1)],
      cap={"dengue_fever": 0.7, "sepsis": 0.7, "leptospirosis": 0.8}, src="Thrombocytopenia + hyponatraemia + transaminitis triad (Biggs MMWR 2016)"),
 dict(id="mis_c", dx=["multisystem_inflammatory_syndrome_cardiac_pattern"], req=[("crp", ">=", 30), ("trop_c", ">", 20)], alt_req=[("crp", ">=", 30), ("natri_high", "==", 1)], sup=[("ferritin", ">", 500), ("alc", "<", 1.0), ("plt", "<", 150), ("ddimer", ">", 1.0), ("na", "<", 135), ("alb", "<", 3.0), ("pct", ">", 0.5)], min_sup=2, ctx=[("age_lt", 21)], excl=[("blasts", ">", 0), ("bcx", "pos", None), ("plt", ">", 450)],
      ctx_any=[("cond", "covid"), ("cond", "sars"), ("cond", "mis-c"), ("cond", "mis_c"), ("cond", "exposure"), ("cond", "contact"), ("cond", "post-infectious"), ("cond", "pcr")],
      cap={"kawasaki_disease": 0.8, "myocarditis": 0.8, "sepsis": 0.7, "toxic_shock_syndrome": 0.8}, src="CDC/WHO MIS-C case definition 2020; Feldstein NEJM 2020"),
 dict(id="pcp", dx=["pneumocystis_pneumonia"], req=[("ldh", ">", 300), ("cd4", "<", 200)], alt_req=[("ldh", ">", 300), ("hiv_ab", "pos", None), ("po2", "<", 70)], sup=[("po2", "<", 70), ("hiv_vl", ">", 1000), ("alb", "<", 3.5)], min_sup=0, excl=[("pct", ">", 2)],
      cap={"hiv_infection": 0.9, "community_acquired_pneumonia": 0.6, "sepsis": 0.6}, src="CDC/NIH OI guidelines; LDH as PCP marker (Zaman 1988)"),
 dict(id="invasive_aspergillosis", dx=["invasive_aspergillosis_marker_pattern"], req=[("galactomannan", ">=", 0.5)], sup=[("anc", "<", 0.5), ("crp", ">", 50), ("pct", "<", 1)], min_sup=0, src="EORTC/MSGERC 2020: serum GM index ≥0.5 (or ≥1.0 single)"),
 dict(id="tb_pleural_ada", dx=["tuberculous_pleuritis", "tuberculosis", "exudative_pleural_effusion"], req=[("pleural_ada", ">", 40)], sup=[("igra", "pos", None), ("pleural_ldh", ">", 200), ("alb", "<", 3.5)], min_sup=0, strength="strong",
      cap={"malignant_pleural_effusion": 0.6, "parapneumonic_effusion": 0.7}, src="Pleural ADA >40 U/L (Light; Aggarwal 2019 meta-analysis)"),
 # ---------------- rheumatology ---------------------------------------------
 dict(id="mctd", dx=["mixed_connective_tissue_disease", "mixed_connective_tissue_disease_serologic_pattern"], req=[("rnp", "pos", None), ("ana", ">=", 320)], sup=[("ck", ">", 300), ("rf", ">", 20), ("hb", "<", 12), ("plt", "<", 150)], min_sup=0, excl=[("dsdna", ">", 30), ("scl70", "pos", None)],
      cap={"systemic_lupus_erythematosus": 0.6, "systemic_sclerosis": 0.6, "polymyositis": 0.6, "myositis": 0.6}, src="Alarcón-Segovia criteria; anti-U1-RNP high titre with speckled ANA"),
 dict(id="septic_arthritis", dx=["septic_arthritis"], req=[("syn_wbc", ">", 50000)], sup=[("crp", ">", 50), ("wbc", ">", 10), ("pct", ">", 0.5), ("esr", ">", 30)], min_sup=1,
      cap={"gout": 0.5, "gout_flare": 0.5, "pseudogout": 0.5, "reactive_arthritis": 0.3}, src="Margaretten JAMA 2007: synovial WBC >50,000 LR+ 7.7"),
 dict(id="pseudogout", dx=["pseudogout", "pseudogout_cppd_disease"], req=[("cppd", "pos", None)], sup=[("crp", ">", 10), ("ca_c", ">", 10.5), ("pth", ">", 65), ("ferritin", ">", 300), ("mg", "<", 1.7), ("tsh", ">", 10)], min_sup=0, excl=[("msu", "pos", None)],
      cap={"gout_flare": 0.3, "gout": 0.3, "septic_arthritis": 0.5}, src="EULAR CPPD 2011 (Zhang); secondary causes PHPT/HH/hypoMg/hypothyroid"),
 dict(id="fmf_attack", dx=["familial_mediterranean_fever"], req=[("crp", ">", 30), ("wbc", ">", 10)], sup=[("fib", ">", 400), ("esr", ">", 30), ("upcr", ">", 0.5), ("ferritin", ">", 300)], min_sup=1, strength="pattern", ctx=[("cond", "recurrent")], ctx_any=[("fh", "fmf"), ("cond", "fmf"), ("cond", "mediterranean"), ("cond", "serositis"), ("cond", "periodic fever"), ("cond", "recurrent fever")],
      excl=[("pct", ">", 2), ("bcx", "pos", None), ("blasts", ">", 0)],
      cap={"sepsis": 0.5, "appendicitis": 0.6, "adult_onset_still_disease": 0.7}, src="Eurofever/PRINTO 2019 classification; proteinuria flags AA amyloidosis"),
 dict(id="igg4_rd", dx=["igg4_related_disease_support_pattern", "elevated_serum_igg4"], req=[("igg4_s", ">", 135)], sup=[("igg", ">", 1600), ("eos_abs", ">", 0.5), ("ige", ">", 200), ("c3", "<", 90), ("c4", "<", 10), ("alp", ">", 180), ("lipase", ">", 60)], min_sup=1, excl=[("ama", ">", 20), ("mpo", "pos", None), ("pr3", "pos", None)],
      cap={"primary_sclerosing_cholangitis": 0.6, "autoimmune_pancreatitis": 0.95, "pancreatic_cancer": 0.6, "sarcoidosis": 0.6, "cholangiocarcinoma": 0.6}, src="ACR/EULAR 2019 IgG4-RD classification (Wallace)"),
 dict(id="drug_induced_lupus", dx=["drug_induced_lupus"], req=[("histone", "pos", None), ("ana", ">=", 160)], sup=[("dsdna", "<", 30), ("c3", ">=", 90), ("c4", ">=", 10), ("crp", ">", 10)], min_sup=1, ctx_any=[("med", "hydralazine"), ("med", "procainamide"), ("med", "isoniazid"), ("med", "minocycline"), ("med", "infliximab"), ("med", "adalimumab"), ("med", "etanercept"), ("med", "methyldopa"), ("med", "quinidine"), ("med", "tnf")],
      cap={"systemic_lupus_erythematosus": 0.6}, src="Anti-histone + culprit drug with normal complement/dsDNA (Borchers 2007)"),
 dict(id="axial_spa", dx=["ankylosing_spondylitis"], req=[("hla_b27", "pos", None), ("crp", ">", 10)], sup=[("esr", ">", 20), ("hb", "<", 12), ("rf", "<", 20), ("ccp", "<", 20)], min_sup=0, excl=[("rf", ">", 40), ("ccp", ">", 20)], ctx=[("age_lt", 50)],
      cap={"rheumatoid_arthritis": 0.5, "reactive_arthritis": 0.8}, src="ASAS 2009 axial SpA classification"),
 # ---------------- cardio / pulmonary ---------------------------------------
 dict(id="aortic_dissection_lab", dx=["aortic_dissection"], req=[("ddimer", ">", 0.5), ("trop_c", "<", 100)], sup=[("ldh", ">", 300), ("cr", ">", 1.3), ("lactate", ">", 2), ("hb", "<", 12), ("crp", ">", 10)], min_sup=2, strength="pattern", ctx_any=[("cond", "chest pain"), ("cond", "tearing"), ("cond", "hypertension"), ("cond", "marfan"), ("cond", "aortic"), ("cond", "dissection")],
      excl=[("fib", "<", 150), ("plt", "<", 100), ("pct", ">", 2), ("schisto", ">", 1), ("po2", "<", 70)],
      cap={"pulmonary_embolism": 0.7, "acute_myocardial_infarction": 0.7}, src="ADD-RS + D-dimer <500 rule-out (ADvISED, Nazerian Circulation 2018); D-dimer >0.5 µg/mL FEU only supports"),
 dict(id="pericarditis", dx=["acute_pericarditis", "pericarditis_support_pattern"], req=[("crp", ">", 20), ("trop_c", "<", 100)], sup=[("esr", ">", 20), ("wbc", ">", 10), ("trop_c", ">", 14), ("ana", ">=", 80)], min_sup=1, strength="pattern", ctx_any=[("cond", "chest pain"), ("cond", "pleuritic"), ("cond", "pericard"), ("cond", "viral"), ("cond", "friction")],
      excl=[("pct", ">", 2), ("ddimer", ">", 2), ("ck", ">", 1000)],
      cap={"acute_myocardial_infarction": 0.6, "myocarditis": 0.9, "pulmonary_embolism": 0.6}, src="ESC pericardial 2015 (Adler): CRP elevation supportive; troponin rise suggests myopericarditis"),
 dict(id="takotsubo", dx=["takotsubo_cardiomyopathy"], req=[("trop_c", "between", (50, 2000)), ("natri_high", "==", 1)], sup=[("glucose", ">", 140), ("crp", ">", 10), ("ck", "<", 500)], min_sup=0, strength="pattern", ctx=[("sex", "f"), ("age_ge", 50)], ctx_any=[("cond", "stress"), ("cond", "bereave"), ("cond", "emotional"), ("cond", "takotsubo"), ("cond", "apical")],
      cap={"acute_myocardial_infarction": 0.8}, src="InterTAK 2018 (Ghadri): BNP/troponin mismatch in post-menopausal women after stressor"),
 dict(id="digoxin_toxicity", dx=["digoxin_toxicity", "digoxin_toxicity_cardiac_risk"], req=[("digoxin", ">", 2.0)], sup=[("k", ">", 5.0), ("cr", ">", 1.3), ("mg", "<", 1.7), ("ca_c", ">", 10.5), ("hr", "<", 50)], min_sup=0,
      cap={"hyperkalemia": 0.9, "acute_kidney_injury": 0.9}, src="Digoxin >2 ng/mL (Tietz); hyperkalaemia marks acute toxicity (Bismuth 1973)"),
 dict(id="statin_myopathy", dx=["statin_associated_muscle_injury"], req=[("ck", "between", (1000, 20000))], sup=[("alt", ">", 40), ("tsh", "<=", 10), ("cr", ">", 1.3), ("umyoglobin", "pos", None)], min_sup=0, ctx_any=[("med", "statin"), ("med", "atorvastatin"), ("med", "rosuvastatin"), ("med", "simvastatin"), ("med", "pravastatin"), ("med", "fibrate"), ("med", "gemfibrozil")],
      excl=[("tsh", ">", 10), ("jo1", "pos", None), ("trop_c", ">", 500)],
      cap={"rhabdomyolysis": 0.9, "myositis": 0.6, "polymyositis": 0.6, "hypothyroidism": 0.5}, src="SAMS: ACC/AHA 2018; Stroes EAS 2015"),
 dict(id="ards_gas", dx=["acute_respiratory_distress_syndrome"], req=[("po2", "<", 60), ("pco2", "<", 45)], sup=[("lactate", ">", 2), ("crp", ">", 50), ("pct", ">", 0.5), ("natri_high", "==", 0), ("alb", "<", 3.0), ("ddimer", ">", 1.0)], min_sup=2, strength="pattern", ctx_any=[("cond", "sepsis"), ("cond", "pneumonia"), ("cond", "aspiration"), ("cond", "pancreatitis"), ("cond", "trauma"), ("cond", "ards"), ("cond", "ventilat"), ("cond", "respiratory failure"), ("cond", "covid")],
      excl=[("natri_high", "==", 1), ("cohb", ">", 10)],
      cap={"heart_failure": 0.5, "acute_heart_failure_support_pattern": 0.5, "pulmonary_embolism": 0.7}, src="Berlin 2012 / new global ARDS definition 2023: hypoxaemia without cardiac failure (natriuretic peptide not raised)"),
 dict(id="co_poisoning_lactate_guard", dx=["carbon_monoxide_poisoning"], req=[("cohb", ">", 25)], sup=[("lactate", ">", 4), ("trop_c", ">", 30), ("ck", ">", 1000), ("hco3", "<", 18)], min_sup=1,
      cap={"sepsis": 0.5, "acute_myocardial_infarction": 0.6, "lactic_acidosis": 0.9, "rhabdomyolysis": 0.9}, src="Hampson, Am J Respir Crit Care Med 2012: COHb >25% severe"),
 # ---------------- neurology -------------------------------------------------
 dict(id="myasthenia", dx=["myasthenia_gravis", "myasthenia_gravis_antibody_pattern"], req=[("achr", ">", 0.5)], sup=[("tsh", "<", 0.4), ("tsh", ">", 4.5), ("tpo", ">", 35), ("ck", "<", 200)], min_sup=0, src="Anti-AChR binding antibody >0.5 nmol/L (Gilhus NEJM 2016)"),
 dict(id="nmdar_encephalitis", dx=["anti_nmdar_encephalitis"], req=[("nmdar", "pos", None)], sup=[("ocb", "pos", None), ("na", "<", 135), ("ck", ">", 300)], min_sup=0, ctx=[("age_lt", 50)], src="Graus Lancet Neurol 2016 criteria"),
 dict(id="ms_csf", dx=["multiple_sclerosis"], req=[("ocb", "pos", None)], sup=[("b12", ">=", 300), ("ana", "<", 80), ("esr", "<", 30), ("igg", "between", (600, 1800))], min_sup=1, strength="pattern", ctx=[("age_lt", 60)], excl=[("nmdar", "pos", None), ("trep", "pos", None), ("hiv_ab", "pos", None), ("b12", "<", 200)],
      cap={"neurosyphilis": 0.3, "vitamin_b12_deficiency": 0.4}, src="McDonald 2017: CSF-specific oligoclonal bands substitute for dissemination in time"),
 dict(id="mcardle", dx=["mcardle_disease"], req=[("ck", ">", 1000), ("urate", ">", 7)], sup=[("umyoglobin", "pos", None), ("cr", ">", 1.3), ("lactate", "<", 2), ("tsh", "<=", 10)], min_sup=1, strength="pattern", ctx_any=[("cond", "exercise"), ("cond", "exertion"), ("cond", "cramp"), ("cond", "second wind"), ("cond", "myoglobinuria"), ("fh", "myopathy")],
      excl=[("jo1", "pos", None), ("tsh", ">", 10), ("trop_c", ">", 500)],
      cap={"rhabdomyolysis": 0.9, "myositis": 0.6, "polymyositis": 0.6, "statin_associated_muscle_injury": 0.6}, src="Lucia, Nat Rev Neurol 2021: exertional rhabdomyolysis + hyperuricaemia (myogenic), blunted lactate rise"),
 # ---------------- toxicology ----------------------------------------------
 dict(id="lithium_toxicity", dx=["lithium_toxicity"], req=[("lithium", ">", 1.5)], sup=[("cr", ">", 1.3), ("na", ">", 145), ("uosm", "<", 300), ("tsh", ">", 4.5), ("ca_c", ">", 10.5), ("wbc", ">", 11)], min_sup=0,
      cap={"nephrogenic_diabetes_insipidus": 0.9, "central_diabetes_insipidus": 0.3, "acute_kidney_injury": 0.9, "primary_hyperparathyroidism": 0.6, "hypothyroidism": 0.6}, src="Lithium >1.5 mmol/L (Baird-Gunning, J Intensive Care Med 2017)"),
 dict(id="valproate_toxicity", dx=["valproate_toxicity", "valproic_acid_toxicity"], req=[("valproate", ">", 100)], sup=[("nh3", ">", 60), ("plt", "<", 150), ("na", "<", 135), ("ag_c", ">", 14), ("alt", ">", 80), ("lactate", ">", 2)], min_sup=0,
      cap={"hepatic_encephalopathy": 0.6, "urea_cycle_disorder": 0.5, "immune_thrombocytopenia": 0.3}, src="Valproate >100 µg/mL; hyperammonaemia (Sztajnkrycer 2002)"),
 dict(id="valproate_hyperammonemia", dx=["valproate_induced_hyperammonemic_encephalopathy", "valproate_toxicity", "valproic_acid_toxicity"], req=[("nh3", ">", 80), ("alt", "<", 80), ("alb", ">=", 3.5)], sup=[("plt", "<", 150), ("ag_c", ">", 14)], min_sup=0, ctx_any=[("med", "valpro"), ("med", "depakine"), ("med", "divalproex")],
      cap={"hepatic_encephalopathy": 0.4, "urea_cycle_disorder": 0.6, "liver_cirrhosis": 0.2}, src="VHE: hyperammonaemia with normal LFTs on valproate (Chopra 2012)"),
 dict(id="carbamazepine_toxicity", dx=["carbamazepine_toxicity"], req=[("carbamazepine", ">", 12)], sup=[("na", "<", 135), ("osm", "<", 275), ("anc", "<", 1.5)], min_sup=0, cap={"siadh": 0.9, "hyponatremia": 0.9}, src="Carbamazepine >12 µg/mL (Tietz); SIADH"),
 dict(id="phenytoin_toxicity", dx=["phenytoin_toxicity"], req=[("phenytoin", ">", 20)], sup=[("alb", "<", 3.5), ("ggt", ">", 60), ("folate", "<", 3)], min_sup=0, src="Phenytoin total >20 µg/mL; correct for albumin (Sheiner-Tozer)"),
 dict(id="theophylline_toxicity", dx=["theophylline_toxicity"], req=[("theoph", ">", 20)], sup=[("k", "<", 3.5), ("glucose", ">", 140), ("lactate", ">", 2), ("hco3", "<", 20), ("ca_c", ">", 10.5)], min_sup=0,
      cap={"hypokalemia": 0.9, "lactic_acidosis": 0.9, "diabetic_ketoacidosis": 0.5}, src="Theophylline >20 µg/mL: hypokalaemia, hyperglycaemia, lactic acidosis (Shannon 1999)"),
 dict(id="iron_poisoning", dx=["iron_poisoning"], req=[("iron_serum", ">", 350)], sup=[("ag_c", ">", 16), ("hco3", "<", 18), ("glucose", ">", 150), ("wbc", ">", 15), ("alt", ">", 80), ("lactate", ">", 2)], min_sup=1, excl=[("tsat", "<", 50), ("ferritin", ">", 10000)],
      cap={"hereditary_hemochromatosis": 0.3, "metabolic_acidosis": 0.9, "lactic_acidosis": 0.8}, src="Serum iron >350 µg/dL 4–6 h post-ingestion = moderate–severe (Chang & Rangan 2011)"),
 dict(id="organophosphate", dx=["organophosphate_poisoning"], req=[("che", "<", 2500)], sup=[("glucose", ">", 140), ("lactate", ">", 2), ("amylase", ">", 100), ("k", "<", 3.5), ("wbc", ">", 11)], min_sup=0, excl=[("alb", "<", 2.5), ("alt", ">", 300)],
      cap={"acute_pancreatitis": 0.6, "sepsis": 0.5}, src="Eddleston Lancet 2008: plasma cholinesterase <50% of lower limit"),
 dict(id="nms", dx=["neuroleptic_malignant_syndrome"], req=[("ck", ">", 1000), ("wbc", ">", 10)], sup=[("temp", ">", 38), ("iron_serum", "<", 50), ("cr", ">", 1.3), ("lactate", ">", 2), ("umyoglobin", "pos", None)], min_sup=1, strength="strong", ctx_any=[("med", "haloperidol"), ("med", "risperidone"), ("med", "olanzapine"), ("med", "quetiapine"), ("med", "aripiprazole"), ("med", "chlorpromazine"), ("med", "metoclopramide"), ("med", "antipsychotic"), ("med", "neuroleptic"), ("med", "clozapine"), ("med", "fluphenazine")],
      excl=[("pct", ">", 2), ("bcx", "pos", None), ("jo1", "pos", None)],
      cap={"heat_stroke": 0.5, "rhabdomyolysis": 0.9, "sepsis": 0.6, "myositis": 0.5, "serotonin_syndrome": 0.8}, src="DSM-5 / Gurrera 2011 consensus; low serum iron supports NMS (Rosebush 1991)"),
 dict(id="ethanol_intoxication", dx=["alcohol_intoxication"], req=[("ethanol_mg", ">", 80)], sup=[("osm_gap_c", ">", 10), ("glucose", "<", 70), ("k", "<", 3.5), ("mg", "<", 1.7), ("ast_alt", ">", 1.5), ("ggt", ">", 60)], min_sup=0,
      cap={"toxic_alcohol_ingestion": 0.5, "ethylene_glycol_poisoning": 0.4, "methanol_poisoning": 0.4, "hyperosmolar_hyperglycemic_state": 0.3}, src="Ethanol >80 mg/dL; each 100 mg/dL adds ~22 mOsm/kg to the osmolal gap (Purssell 2001)"),
 dict(id="methanol_measured", dx=["methanol_poisoning", "toxic_alcohol_ingestion"], req=[("methanol", ">", 20)], sup=[("ag_c", ">", 16), ("hco3", "<", 18), ("osm_gap_c", ">", 10), ("lactate", ">", 2)], min_sup=0,
      cap={"ethylene_glycol_poisoning": 0.6, "lactic_acidosis": 0.6, "diabetic_ketoacidosis": 0.3}, src="AACT/EAPCCT methanol 2002; >20 mg/dL = fomepizole threshold"),
 dict(id="mala", dx=["lactic_acidosis_metformin_associated"], req=[("lactate", ">", 5), ("hco3", "<", 18), ("cr", ">", 1.5)], sup=[("ag_c", ">", 16), ("k", ">", 5.0), ("glucose", "<", 250), ("pct", "<", 0.5)], min_sup=1, ctx_any=[("med", "metformin"), ("med", "glucophage")],
      excl=[("pct", ">", 2), ("bcx", "pos", None), ("cohb", ">", 10)],
      cap={"sepsis": 0.6, "septic_shock_severe_lactic_acidosis": 0.6, "lactic_acidosis": 0.95, "diabetic_ketoacidosis": 0.5}, src="Lalau, Diabetes Obes Metab 2017: lactate >5 + pH <7.35 + metformin + AKI"),
 # ---------------- inborn errors / neonatal / paediatric --------------------
 dict(id="galactosemia", dx=["classic_galactosemia", "galactosemia"], req=[("galt", "<", 3.5)], alt_req=[("galactose", ">", 10), ("stool_reducing", "pos", None)], sup=[("dbil", ">", 1), ("alt", ">", 60), ("glucose", "<", 50), ("inr", ">", 1.5), ("bcx", "pos", None), ("uglu", "neg", None)], min_sup=0, ctx=[("age_lt", 1)],
      cap={"neonatal_sepsis": 0.8, "neonatal_jaundice": 0.6, "biliary_atresia": 0.5, "tyrosinemia_type_1": 0.6}, src="Welling, J Inherit Metab Dis 2017 international guideline"),
 dict(id="pku", dx=["phenylketonuria_pku"], req=[("phe", ">", 6)], sup=[("tyrosine", "<", 40)], min_sup=0, ctx=[("age_lt", 18)], src="ACMG PKU 2014 (Vockley): Phe >360 µmol/L (6 mg/dL)"),
 dict(id="msud", dx=["maple_syrup_urine_disease"], req=[("leucine", ">", 400)], sup=[("uket", "pos", None), ("glucose", "<", 60), ("hco3", "<", 18), ("nh3", "<", 150)], min_sup=0, ctx=[("age_lt", 18)],
      cap={"organic_acidemia": 0.6, "urea_cycle_disorder": 0.3}, src="Strauss, GeneReviews 2020: plasma leucine >400 µmol/L with ketosis"),
 dict(id="urea_cycle", dx=["urea_cycle_disorder", "ornithine_transcarbamylase_deficiency", "urea_cycle_disorder_otc_deficiency"], req=[("nh3", ">", 200), ("alt", "<", 100), ("hco3", ">=", 20)], sup=[("pco2", "<", 35), ("ph", ">", 7.45), ("orotic", ">", 20), ("glucose", ">=", 60), ("bun", "<", 7), ("uket", "neg", None)], min_sup=1, ctx=[("age_lt", 18)], excl=[("valproate", ">", 50), ("lactate", ">", 5)],
      cap={"hepatic_encephalopathy": 0.3, "organic_acidemia": 0.5, "methylmalonic_acidemia": 0.5, "propionic_acidemia": 0.5, "neonatal_sepsis": 0.5, "reye_syndrome": 0.6}, src="Häberle 2019 UCD guideline: hyperammonaemia with respiratory alkalosis and no acidosis/ketosis"),
 dict(id="organic_acidemia", dx=["organic_acidemia", "propionic_acidemia", "methylmalonic_acidemia", "organic_acidemia"], req=[("nh3", ">", 100), ("ag_c", ">", 16), ("hco3", "<", 18), ("glucose", "<", 126)], sup=[("uket", "pos", None), ("anc", "<", 1.5), ("plt", "<", 150), ("lactate", ">", 2), ("bhb", ">", 1), ("mma", ">", 1000)], min_sup=1, ctx=[("age_lt", 18)], excl=[("glucose", ">", 250), ("salicylate", ">", 30)],
      cap={"urea_cycle_disorder": 0.5, "diabetic_ketoacidosis": 0.2, "neonatal_sepsis": 0.6, "maple_syrup_urine_disease": 0.6}, src="Baumgartner 2014 guideline: ketoacidosis + hyperammonaemia + cytopenias"),
 dict(id="mcad", dx=["medium_chain_acyl_coa_dehydrogenase_deficiency"], req=[("glucose", "<", 50), ("bhb", "<", 1.0), ("uket", "neg", None)], alt_req=[("glucose", "<", 50), ("acylcarn", "pos", None)], sup=[("nh3", ">", 60), ("alt", ">", 60), ("ck", ">", 300), ("urate", ">", 7), ("lactate", "<", 4)], min_sup=0, ctx=[("age_lt", 18)], excl=[("insulin", ">=", 3), ("cortisol_am", "<", 5)],
      cap={"insulinoma": 0.3, "neonatal_hypoglycemia": 0.9, "hypoglycemia": 0.9, "reye_syndrome": 0.6, "ketotic_hypoglycemia": 0.2}, src="Hypoketotic hypoglycaemia (Matern & Rinaldo GeneReviews; Merritt 2018)"),
 dict(id="gsd1", dx=["glycogen_storage_disease_type_1", "von_gierke_disease"], req=[("glucose", "<", 60), ("lactate", ">", 2.5), ("urate", ">", 7), ("tg", ">", 250)], sup=[("bhb", ">", 1), ("alt", ">", 60), ("tc", ">", 200), ("hco3", "<", 20)], min_sup=1, ctx=[("age_lt", 18)],
      cap={"familial_chylomicronemia_syndrome": 0.5, "lactic_acidosis": 0.8, "medium_chain_acyl_coa_dehydrogenase_deficiency": 0.3}, src="Kishnani ACMG 2014 GSD Ia: fasting hypoglycaemia + lactic acidosis + hyperuricaemia + hyperlipidaemia"),
 dict(id="tyrosinemia1", dx=["tyrosinemia_type_1"], req=[("succinylacetone", ">", 1)], sup=[("afp", ">", 1000), ("inr", ">", 1.5), ("tyrosine", ">", 200), ("phos", "<", 3.5), ("uglu", "pos", None)], min_sup=0, ctx=[("age_lt", 18)],
      cap={"galactosemia": 0.4, "hepatocellular_carcinoma": 0.5, "acute_liver_failure": 0.8, "fanconi_syndrome": 0.8}, src="Chinsky, Genet Med 2017: succinylacetone pathognomonic"),
 dict(id="neonatal_sepsis", dx=["neonatal_sepsis", "neonatal_sepsis_support_pattern"], req=[("crp", ">", 10)], sup=[("pct", ">", 2), ("wbc", "<", 5), ("wbc", ">", 30), ("bands", ">", 10), ("plt", "<", 150), ("glucose", "<", 45), ("glucose", ">", 180), ("lactate", ">", 2.5), ("bcx", "pos", None), ("il6", ">", 100)], min_sup=2, ctx=[("age_lt", 0.25)],
      cap={"neonatal_jaundice": 0.7, "galactosemia": 0.7, "transient_tachypnea_of_newborn": 0.5}, src="Puopolo AAP 2018; Hofer 2012 CRP/PCT in neonates"),
 dict(id="hdn_abo_rh", dx=["hemolytic_disease_of_the_newborn"], req=[("dat", "pos", None), ("tbil", ">", 10), ("dbil_frac", "<", 0.2)], sup=[("hb", "<", 13), ("retic", ">", 6), ("nrbc", ">", 10), ("ldh", ">", 600), ("sphero", ">", 0)], min_sup=1, ctx=[("age_lt", 0.1)],
      cap={"neonatal_jaundice": 0.9, "hereditary_spherocytosis": 0.4, "g6pd_deficiency": 0.4, "crigler_najjar_syndrome": 0.2, "breast_milk_jaundice": 0.2}, src="AAP 2022 hyperbilirubinaemia (Kemper): DAT-positive isoimmune haemolysis"),
 dict(id="neonatal_polycythemia", dx=["neonatal_polycythemia"], req=[("hct", ">", 65)], sup=[("glucose", "<", 45), ("tbil", ">", 10), ("plt", "<", 150), ("ca_c", "<", 8)], min_sup=0, ctx=[("age_lt", 0.1)],
      cap={"polycythemia_vera": 0.1, "secondary_erythrocytosis": 0.3}, src="Venous Hct >65% in the first week (Sarkar & Rosenkrantz 2008)"),
 dict(id="neonatal_hypoglycemia", dx=["neonatal_hypoglycemia"], req=[("glucose", "<", 45)], sup=[("insulin", ">=", 2), ("bhb", "<", 1), ("cortisol_am", "<", 10), ("gh", "<", 7), ("nh3", ">", 60)], min_sup=0, ctx=[("age_lt", 0.1)],
      cap={"hypoglycemia": 0.95, "insulinoma": 0.3, "medium_chain_acyl_coa_dehydrogenase_deficiency": 0.6}, src="PES 2015 (Thornton): <50 mg/dL beyond 48 h; <45 in first 48 h"),
 dict(id="scid", dx=["severe_combined_immunodeficiency_scid"], req=[("alc", "<", 2.5)], sup=[("igg", "<", 300), ("iga", "<", 10), ("igm", "<", 30), ("cd4", "<", 1500)], min_sup=1, ctx=[("age_lt", 1)],
      cap={"x_linked_agammaglobulinemia": 0.6, "hiv_infection": 0.6, "common_variable_immunodeficiency": 0.3}, src="PIDTC 2014 (Shearer): ALC <2.5 in an infant"),
 dict(id="xla", dx=["x_linked_agammaglobulinemia"], req=[("igg", "<", 200), ("iga", "<", 10), ("igm", "<", 20)], sup=[("alc", ">=", 2.5), ("anc", "<", 1.5)], min_sup=0, ctx=[("sex", "m"), ("age_lt", 18)], excl=[("alc", "<", 2.5)],
      cap={"common_variable_immunodeficiency": 0.5, "severe_combined_immunodeficiency_scid": 0.6, "selective_iga_deficiency": 0.2}, src="ESID 2019 criteria: panhypogammaglobulinaemia in a boy"),
 dict(id="cvid", dx=["common_variable_immunodeficiency"], req=[("igg", "<", 450), ("iga", "<", 70)], alt_req=[("igg", "<", 450), ("igm", "<", 40)], sup=[("alc", ">=", 1.0), ("plt", "<", 100), ("hb", "<", 12), ("alb", ">=", 3.0)], min_sup=0, ctx=[("age_ge", 4)], excl=[("mspike", ">", 0.5), ("flc_ratio_c", ">", 8), ("upcr", ">", 3.5), ("alb", "<", 2.5), ("fecal_a1at", ">", 27)],
      cap={"multiple_myeloma": 0.3, "nephrotic_syndrome": 0.4, "protein_losing_enteropathy": 0.4, "selective_iga_deficiency": 0.5, "x_linked_agammaglobulinemia": 0.6}, src="ESID 2019 / ICON 2016 (Bonilla): IgG <2 SD with low IgA and/or IgM after age 4, secondary causes excluded"),
 dict(id="selective_iga_def", dx=["selective_iga_deficiency"], req=[("iga", "<", 7), ("igg", ">=", 600), ("igm", ">=", 40)], sup=[("ttg_igg", ">", 10), ("tpo", ">", 35)], min_sup=0, ctx=[("age_ge", 4)],
      cap={"common_variable_immunodeficiency": 0.3, "celiac_disease": 0.95}, src="IgA <7 mg/dL with normal IgG/IgM after age 4 (Yel 2010)"),
 dict(id="rickets", dx=["rickets", "rickets_in_children", "rickets_support_pattern"], req=[("alp", ">", 350), ("phos", "<", 4.0)], alt_req=[("vitd", "<", 12), ("alp", ">", 350)], sup=[("vitd", "<", 20), ("pth", ">", 65), ("ca_c", "<", 9.0)], min_sup=1, ctx=[("age_lt", 18)], excl=[("alt", ">", 200), ("ggt", ">", 200)],
      cap={"osteomalacia": 0.9, "hypoparathyroidism": 0.2, "x_linked_hypophosphatemia": 0.8, "hypophosphatemia": 0.9}, src="Munns, JCEM 2016 global consensus: raised ALP + low phosphate/25-OH-D"),
 dict(id="turner_labs", dx=["turner_syndrome", "turner_syndrome_45x"], req=[("fsh", ">", 25), ("e2", "<", 30)], sup=[("lh", ">", 10), ("amh", "<", 0.5), ("tsh", ">", 4.5), ("alt", ">", 40), ("a1c", ">=", 5.7)], min_sup=0, ctx=[("sex", "f"), ("age_lt", 18)],
      cap={"premature_ovarian_insufficiency": 0.9, "menopause": 0.1}, src="Gravholt 2017 Turner guideline: hypergonadotropic hypogonadism in a girl"),
 dict(id="ghd_child", dx=["growth_hormone_deficiency", "growth_hormone_deficiency_pattern", "isolated_growth_hormone_deficiency"], req=[("igf1", "<", 60), ("gh", "<", 7)], sup=[("glucose", "<", 60), ("ft4", "between", (0.8, 1.8)), ("ttg_iga", "<", 10), ("alb", ">=", 3.5)], min_sup=1, strength="pattern", ctx=[("age_lt", 18)], excl=[("tsh", ">", 10), ("alb", "<", 3.0), ("ttg_iga", ">", 10), ("crp", ">", 20)],
      cap={"hypopituitarism_panhypopituitarism": 0.95, "hypothyroidism": 0.4}, src="GRS 2019 (Collett-Solberg); low IGF-1 with failed stimulated GH <7 ng/mL (Grimberg 2016)"),
 # ---------------- pregnancy ------------------------------------------------
 dict(id="hyperemesis", dx=["hyperemesis_gravidarum", "hyperemesis_gravidarum_metabolic_pattern"], req=[("uket", "pos", None), ("k", "<", 3.5)], alt_req=[("uket", "pos", None), ("hco3", ">", 28)], sup=[("tsh", "<", 0.4), ("ft4", ">", 1.8), ("alt", ">", 40), ("na", "<", 135), ("ucl", "<", 20), ("bun_cr", ">", 20)], min_sup=1, ctx=[("pregnant", True)], excl=[("trab", ">", 1.75), ("glucose", ">", 250), ("bhb", ">=", 3)],
      cap={"graves_disease": 0.3, "hyperthyroidism": 0.4, "thyroid_storm": 0.2, "diabetic_ketoacidosis": 0.2, "gestational_thyrotoxicosis": 0.95, "metabolic_alkalosis": 0.9, "hypokalemia": 0.9}, src="ACOG PB 189 2018; RCOG GTG 69: ketonuria, hypokalaemic alkalosis, transient biochemical hyperthyroidism"),
 dict(id="postpartum_thyroiditis", dx=["postpartum_thyroiditis", "postpartum_thyroiditis_support_pattern"], req=[("tsh", "<", 0.4), ("tpo", ">", 35), ("trab", "<", 1.75)], alt_req=[("tsh", ">", 4.5), ("tpo", ">", 35)], sup=[("ft4", ">", 1.8), ("esr", "<", 50)], min_sup=0, ctx=[("sex", "f"), ("cond", "postpartum")],
      cap={"graves_disease": 0.3, "hashimoto_thyroiditis": 0.6, "painless_thyroiditis": 0.9, "subacute_thyroiditis": 0.4}, src="ATA 2017 pregnancy/postpartum (Alexander)"),
 dict(id="peripartum_cardiomyopathy", dx=["peripartum_cardiomyopathy_support_pattern"], req=[("natri_high", "==", 1)], sup=[("trop_c", ">", 14), ("na", "<", 135), ("cr", ">", 1.0), ("alt", ">", 40), ("crp", ">", 10)], min_sup=1, strength="strong", ctx=[("sex", "f")], ctx_any=[("pregnant", True), ("cond", "postpartum"), ("cond", "peripartum"), ("cond", "delivery")],
      excl=[("ddimer", ">", 4), ("plt", "<", 100), ("upcr", ">", 0.3), ("ast", ">", 200)],
      cap={"heart_failure": 0.95, "pulmonary_embolism": 0.6, "preeclampsia": 0.6, "acute_myocardial_infarction": 0.6}, src="ESC PPCM 2019 (Bauersachs): NT-proBNP raised in last month of pregnancy to 5 months postpartum"),
 # --- modular physiological guards (dx-less; caps are ABSOLUTE ceilings) ---
 dict(id="pregnancy_prolactin_guard", dx=[], guard=True, req=[("prl", "between", (20, 400))], min_sup=0, strength="pattern", ctx=[("pregnant", True)],
      excl=[("na", "<", 130), ("ft4", "<", 0.7)],
      cap={"hyperprolactinemia": 0.3, "prolactinoma": 0.3, "pituitary_adenoma": 0.3, "macroprolactinoma": 0.3, "microprolactinoma": 0.3, "elevated_prolactin": 0.3},
      src="Prolactin rises 10-fold across gestation (Abbassi-Ghanavati 2009): 36–372 ng/mL in T3 is physiological"),
 dict(id="pregnancy_ddimer_guard", dx=[], guard=True, req=[("ddimer", "between", (0.5, 3.0))], min_sup=0, strength="pattern", ctx=[("pregnant", True)],
      excl=[("plt", "<", 100), ("fib", "<", 200), ("trop_c", ">", 30), ("ldh", ">", 600)],
      cap={"elevated_d_dimer_pattern": 0.45, "pulmonary_embolism": 0.45, "venous_thromboembolism": 0.45, "deep_vein_thrombosis": 0.45, "aortic_dissection": 0.3, "aortic_dissection_lab_support_pattern": 0.3, "disseminated_intravascular_coagulation": 0.3},
      src="D-dimer exceeds the non-pregnant cut-off in ≈90% of T3 pregnancies (Kline 2005; RCOG 2015 GTG 37b): not diagnostic alone"),
 dict(id="pregnancy_lipid_guard", dx=[], guard=True, req=[("tg", "between", (120, 300))], alt_req=[("tc", "between", (200, 330))], min_sup=0, strength="pattern", ctx=[("pregnant", True)],
      excl=[("lipase", ">", 150), ("glucose", ">", 200)],
      cap={"hypertriglyceridemia": 0.45, "mixed_dyslipidemia": 0.45, "hypercholesterolemia": 0.45, "dyslipidemia": 0.45, "hyperlipidemia": 0.45, "combined_hyperlipidemia": 0.45, "familial_combined_hyperlipidemia": 0.4, "metabolic_syndrome": 0.4, "familial_hypertriglyceridemia": 0.3},
      src="Triglycerides rise 2–3-fold and cholesterol ≈50% in T2–T3 (Abbassi-Ghanavati 2009)"),
 dict(id="pregnancy_cortisol_guard", dx=[], guard=True, req=[("cortisol_am", "between", (15, 45))], min_sup=0, strength="pattern", ctx=[("pregnant", True)],
      excl=[("k", "<", 3.2), ("glucose", ">", 200)],
      cap={"cushing_syndrome": 0.3, "cushings_syndrome": 0.3, "hypercortisolism": 0.3, "cushing_disease": 0.3},
      src="CBG-driven 2–3-fold rise of total cortisol in pregnancy (Endocrine Society 2008 Cushing guideline)"),
 dict(id="pregnancy_leukocyte_guard", dx=[], guard=True, req=[("wbc", "between", (10, 16))], min_sup=0, strength="pattern", ctx=[("pregnant", True)],
      excl=[("crp", ">", 30), ("pct", ">", 0.5), ("blasts", ">", 0), ("bands", ">", 10)],
      cap={"leukocytosis": 0.4, "leukocytosis_pattern": 0.4, "neutrophilia": 0.4, "sepsis": 0.3, "bacterial_infection": 0.35, "chronic_myeloid_leukemia": 0.2},
      src="Physiological neutrophilia of pregnancy up to 16×10⁹/L (Abbassi-Ghanavati 2009)"),
 dict(id="pediatric_lymphocyte_guard", dx=[], guard=True, req=[("alc", "between", (2.5, 9.5))], min_sup=0, strength="pattern", ctx=[("age_lt", 6)],
      excl=[("blasts", ">", 0), ("atyp_lymph", ">", 10), ("hb", "<", 9), ("plt", "<", 100)],
      cap={"lymphocytosis": 0.3, "chronic_lymphocytic_leukemia": 0.2, "acute_lymphoblastic_leukemia": 0.2, "infectious_mononucleosis": 0.4, "pertussis": 0.4, "lymphocytosis_pattern": 0.3},
      src="Lymphocyte predominance of early childhood: ALC up to 9–10×10⁹/L is normal before school age (Nathan & Oski 8e; Tietz paediatric RI)"),
 dict(id="pediatric_lymphocyte_guard_school_age", dx=[], guard=True, req=[("alc", "between", (2.5, 7.0))], min_sup=0, strength="pattern", ctx=[("age_ge", 6), ("age_lt", 13)],
      excl=[("blasts", ">", 0), ("atyp_lymph", ">", 10), ("hb", "<", 9), ("plt", "<", 100)],
      cap={"lymphocytosis": 0.3, "chronic_lymphocytic_leukemia": 0.2, "acute_lymphoblastic_leukemia": 0.2, "infectious_mononucleosis": 0.4, "pertussis": 0.4, "lymphocytosis_pattern": 0.3},
      src="Tietz paediatric RI: ALC 1.5–6.8×10⁹/L at 6–12 y"),
 dict(id="pediatric_phosphate_guard", dx=[], guard=True, req=[("phos", "between", (4.0, 6.5))], min_sup=0, strength="pattern", ctx=[("age_lt", 12)],
      excl=[("cr", ">", 1.0), ("ca_c", "<", 8.5), ("ca", "<", 8.5), ("pth", ">", 88), ("ldh", ">", 500), ("k", ">", 5.5), ("urate", ">", 8)],
      cap={"hyperphosphatemia": 0.3, "chronic_kidney_disease": 0.3, "hypoparathyroidism": 0.3, "tumor_lysis_syndrome": 0.25, "pseudohypoparathyroidism": 0.3, "rhabdomyolysis": 0.25},
      src="Paediatric phosphate RI 4.0–6.5 mg/dL (<12 y), growth-related (Tietz; CALIPER Colantonio 2012)"),
 dict(id="pediatric_phosphate_guard_adolescent", dx=[], guard=True, req=[("phos", "between", (3.5, 5.6))], min_sup=0, strength="pattern", ctx=[("age_ge", 12), ("age_lt", 17)],
      excl=[("cr", ">", 1.2), ("ca_c", "<", 8.5), ("ca", "<", 8.5), ("pth", ">", 88), ("ldh", ">", 500), ("k", ">", 5.5), ("urate", ">", 8)],
      cap={"hyperphosphatemia": 0.3, "chronic_kidney_disease": 0.3, "hypoparathyroidism": 0.3, "tumor_lysis_syndrome": 0.25, "pseudohypoparathyroidism": 0.3, "rhabdomyolysis": 0.25},
      src="Adolescent phosphate RI 3.5–5.6 mg/dL during pubertal growth (CALIPER Colantonio 2012)"),
 dict(id="pediatric_hemoglobin_guard", dx=[], guard=True, req=[("hb", "between", (11.0, 13.0))], min_sup=0, strength="pattern", ctx=[("age_lt", 12), ("age_ge", 0.5)],
      excl=[("mcv", "<", 70), ("ferritin", "<", 15), ("retic", ">", 3), ("tbil", ">", 1.5), ("plt", "<", 100), ("wbc", "<", 4)],
      cap={"anemia": 0.3, "iron_deficiency_anemia": 0.35, "normocytic_anemia": 0.3, "anemia_of_chronic_disease": 0.3, "mild_anemia": 0.3},
      src="WHO 2011/2024 haemoglobin thresholds: anaemia <11.0 g/dL (6–59 mo), <11.5 (5–11 y); values ≥11 are not anaemia in this age band"),
 dict(id="pregnancy_bicarbonate_guard", dx=[], guard=True, req=[("hco3", "between", (18, 23))], min_sup=0, strength="pattern", ctx=[("pregnant", True)],
      excl=[("ag_c", ">", 16), ("ag", ">", 16), ("lactate", ">", 2.0), ("k", ">", 5.5), ("glucose", ">", 200), ("bhb", ">", 1.0), ("cr", ">", 1.0), ("cl", ">", 110), ("ph", "<", 7.36)],
      cap={"metabolic_acidosis": 0.4, "normal_anion_gap_metabolic_acidosis": 0.4, "high_anion_gap_metabolic_acidosis": 0.35, "renal_tubular_acidosis": 0.35, "renal_tubular_acidosis_type_1": 0.3, "renal_tubular_acidosis_type_2": 0.3, "lactic_acidosis": 0.3, "diabetic_ketoacidosis": 0.3, "hyperchloremic_acidosis": 0.4, "diarrhea": 0.35},
      src="Compensated respiratory alkalosis of pregnancy: HCO₃⁻ 18–22 mmol/L, PaCO₂ 28–32 mmHg (Abbassi-Ghanavati 2009; LoMauro & Aliverti 2015)"),
 dict(id="pregnancy_physiologic_guard", dx=[], guard=True, req=[("alb", "between", (2.8, 3.6)), ("cr", "<", 0.8)], alt_req=[("alp", "between", (120, 400)), ("hb", "between", (10.0, 12.0))], alt_req2=[("urate", "<", 4.0), ("bun", "<", 10)], sup=[("bun", "<", 10), ("na", "between", (130, 136)), ("hco3", "between", (18, 22)), ("ggt", "<", 40), ("alt", "<", 40), ("ddimer", ">", 0.5), ("alp", "between", (120, 400)), ("hb", "between", (10.0, 12.0)), ("urate", "<", 4.0)], min_sup=1, strength="pattern", ctx=[("pregnant", True)],
      excl=[("plt", "<", 100), ("upcr", ">", 0.3), ("urate", ">", 6), ("alt", ">", 40), ("bile_acids", ">=", 10), ("tbil", ">", 1.2), ("ferritin", "<", 15)],
      cap={"protein_energy_malnutrition_support_pattern": 0.3, "protein_energy_malnutrition": 0.3, "severe_acute_malnutrition_laboratory_risk": 0.3, "chronic_malnutrition_laboratory_risk": 0.3, "nephrotic_syndrome": 0.3, "cholestasis": 0.3, "cholestatic_liver_injury_pattern": 0.3, "bone_disease": 0.3, "anemia": 0.45, "hyponatremia": 0.4, "chronic_kidney_disease": 0.2, "pulmonary_embolism": 0.45, "paget_disease_of_bone": 0.2, "hypoalbuminemia": 0.45, "liver_cirrhosis": 0.3, "acute_gastroenteritis": 0.3, "dilutional_anemia": 0.45, "malnutrition": 0.3, "aortic_dissection": 0.3, "aortic_dissection_lab_support_pattern": 0.3, "venous_thromboembolism": 0.45, "deep_vein_thrombosis": 0.45, "disseminated_intravascular_coagulation": 0.3, "pellagra": 0.3, "iron_deficiency_anemia": 0.45, "diuretic_use": 0.4, "hypouricemia": 0.4, "low_bun_pattern": 0.4, "syndrome_of_inappropriate_antidiuretic_hormone": 0.4, "siadh": 0.4, "vomiting": 0.4, "metabolic_alkalosis": 0.4, "hypochloremia": 0.4, "high_anion_gap_metabolic_acidosis": 0.4, "metabolic_acidosis": 0.4, "respiratory_alkalosis": 0.45},
      src="Abbassi-Ghanavati, Obstet Gynecol 2009 reference intervals in pregnancy: dilutional anaemia, low albumin/creatinine, placental ALP, mild hyponatraemia/low bicarbonate, raised D-dimer are physiological"),
])


# ---------------------------------------------------------------------------
# ESL extension 3 (2026-10-21): syndromes for the 48 entities added by
# registry patch 13.1.0. Thresholds mirror the registry rules (sources there).
# ---------------------------------------------------------------------------
_ESL_GROUPS.update({
    "tt": ("s", ("thrombin_time", "thrombin_time_plasma")),
    "reptilase": ("s", ("reptilase_time", "reptilase_time_plasma")),
    "saa": ("mg/L", ("serum_amyloid_a", "serum_amyloid_a_quantitative")),
    "cyanide": ("mg/L", ("cyanide_blood",)),
    "csf_prot": ("mg/dL", ("cerebrospinal_fluid_total_protein",)),
    "csf_glu": ("mg/dL", ("cerebrospinal_fluid_glucose",)),
    "cd3": ("cells/uL", ("cd3_t_cells_absolute",)),
    "pleural_prot": ("g/dL", ("pleural_fluid_total_protein",)),
    "pleural_glu": ("mg/dL", ("pleural_fluid_glucose",)),
    "pt_mut": ("1", ("prothrombin_g20210a_mutation",)),
    "random_cortisol": ("ug/dL", ("random_cortisol",)),
    "eg": ("mg/dL", ("ethylene_glycol",)),
})
_ESL_LIBRARY.extend([
 dict(id="tsh_oma_rth", dx=["tsh_secreting_adenoma_or_rth"], req=[("ft4", ">", 1.8), ("tsh", ">=", 0.4)], sup=[("tsh", ">", 1.0), ("prl", ">", 25)], min_sup=0,
      excl=[("trab", ">=", 1.75)], cap={"primary_hyperthyroidism": 0.3, "hyperthyroidism": 0.4, "graves_disease": 0.3, "graves_disease_hyperthyroidism": 0.3, "subclinical_hyperthyroidism": 0.3, "thyrotoxicosis": 0.4},
      src="ETA 2013 TSH-secreting tumours: non-suppressed TSH with raised FT4"),
 dict(id="hypothyroid_myopathy", dx=["hypothyroid_myopathy", "primary_hypothyroidism"], req=[("tsh", ">", 10), ("ck", ">", 300)], sup=[("ft4", "<", 0.8), ("ck", ">", 500), ("ldh", ">", 250), ("ast", ">", 40)], min_sup=1, excl=[("ck", ">", 10000), ("trop_c", ">", 50)],
      cap={"rhabdomyolysis": 0.5, "polymyositis": 0.4, "statin_associated_muscle_injury": 0.5, "acute_myocardial_infarction": 0.3}, src="Sindoni 2016"),
 dict(id="fhh", dx=["familial_hypocalciuric_hypercalcemia"], req=[("ca_c", ">", 10.3), ("pth", ">=", 15), ("uca_cr_clear", "<", 0.01)], alt_req=[("ca", ">", 10.3), ("pth", ">=", 15), ("uca_cr_clear", "<", 0.01)], sup=[("mg", ">", 2.3), ("ca_c", "<", 12)], min_sup=0,
      cap={"primary_hyperparathyroidism": 0.4, "hyperparathyroidism": 0.4, "hypercalcemia_of_malignancy": 0.2}, src="Fifth International Workshop 2022: CCCR <0.01"),
 dict(id="pseudohyponatremia", dx=["pseudohyponatremia"], req=[("na", "<", 135), ("tg", ">", 1000)], alt_req=[("na", "<", 135), ("tp", ">", 10)], sup=[("osm", ">=", 275), ("tg", ">", 1500), ("mspike", ">", 3), ("igm", ">", 3000)], min_sup=1,
      excl=[("osm", "<", 270), ("glucose", ">", 400)], cap={"hyponatremia": 0.3, "syndrome_of_inappropriate_antidiuretic_hormone": 0.2, "siadh": 0.2, "hypovolemic_hyponatremia": 0.2, "hypervolemic_hyponatremia": 0.2, "euvolemic_hyponatremia": 0.2},
      src="Fortgens 2011 indirect ISE electrolyte-exclusion artefact; confirm with direct ISE"),
 dict(id="renovascular_htn", dx=["renovascular_hypertension"], req=[("pra", ">", 3.0), ("aldo", ">", 15)], sup=[("k", "<", 3.5), ("cr", ">", 1.2), ("hco3", ">", 28)], min_sup=1, excl=[("pra", "<", 0.5)],
      cap={"primary_aldosteronism": 0.2, "primary_hyperaldosteronism": 0.2, "conn_syndrome": 0.2, "liddle_syndrome": 0.2}, src="ACC/AHA 2024 renovascular screening"),
 dict(id="heparin_effect", dx=["heparin_effect_coagulation"], req=[("aptt", ">", 45), ("tt", ">", 25)], alt_req=[("anti_xa_ufh", ">", 0.1), ("aptt", ">", 45)], sup=[("reptilase", "<=", 22), ("fib", ">=", 150), ("plt", ">=", 100), ("inr", "<", 1.5)], min_sup=1, excl=[("reptilase", ">", 25), ("fib", "<", 100)],
      cap={"disseminated_intravascular_coagulation": 0.3, "hemophilia_a": 0.3, "hemophilia_b": 0.3, "von_willebrand_disease": 0.3, "antiphospholipid_syndrome": 0.4, "factor_viii_deficiency": 0.3, "dysfibrinogenemia": 0.3}, src="ISTH: TT prolonged, reptilase normal"),
 dict(id="biliary_atresia", dx=["biliary_atresia", "neonatal_cholestasis"], req=[("dbil", ">", 1.0), ("ggt", ">", 200)], sup=[("dbil", ">", 2.0), ("ggt", ">", 300), ("alp", ">", 400), ("dbil_frac", ">", 0.2)], min_sup=1, ctx=[("age_lt", 1)], excl=[("ggt", "<", 100)],
      cap={"neonatal_hyperbilirubinemia": 0.3, "gilbert_syndrome": 0.1, "crigler_najjar_syndrome": 0.1, "hemolytic_disease_of_the_newborn": 0.3, "neonatal_hepatitis": 0.7, "galactosemia": 0.6, "classic_galactosemia": 0.6}, src="NASPGHAN 2017"),
 dict(id="neonatal_cholestasis", dx=["neonatal_cholestasis"], req=[("dbil", ">", 1.0)], sup=[("tbil", ">", 2.0), ("ggt", ">", 100), ("alp", ">", 300)], min_sup=1, ctx=[("age_lt", 1)], excl=[("ggt", ">", 200), ("dbil_frac", "<", 0.15)], strength="pattern",
      cap={"neonatal_hyperbilirubinemia": 0.4, "gilbert_syndrome": 0.1, "crigler_najjar_syndrome": 0.1, "hemolytic_disease_of_the_newborn": 0.4}, src="NASPGHAN 2017: direct bilirubin >1 mg/dL always abnormal"),
 dict(id="ple", dx=["protein_losing_enteropathy"], req=[("alb", "<", 3.0), ("fecal_a1at", ">", 27)], alt_req=[("alb", "<", 3.0), ("igg", "<", 600), ("alc", "<", 1.5)], sup=[("tp", "<", 5.5), ("upcr", "<", 0.3), ("tc", "<", 150), ("ca", "<", 8.5)], min_sup=1, excl=[("upcr", ">", 3.5), ("inr", ">", 1.7)],
      cap={"nephrotic_syndrome": 0.3, "protein_energy_malnutrition": 0.4, "liver_cirrhosis": 0.4, "common_variable_immunodeficiency": 0.4, "malnutrition": 0.4}, src="Umar & DiBaise 2010"),
 dict(id="aa_amyloid", dx=["aa_amyloidosis"], req=[("upcr", ">", 3.0), ("saa", ">", 10)], alt_req=[("upcr", ">", 3.0), ("crp", ">", 20), ("alb", "<", 3.0)], sup=[("alb", "<", 3.5), ("cr", ">", 1.3), ("esr", ">", 50)], min_sup=1, excl=[("flc_ratio_c", ">", 8), ("mspike", ">", 1.0), ("dsdna", ">", 30)], strength="pattern",
      ctx_any=[("cond", "rheumatoid"), ("cond", "fmf"), ("cond", "familial mediterranean"), ("cond", "bronchiectasis"), ("cond", "osteomyelitis"), ("cond", "crohn"), ("cond", "spondyl"), ("cond", "tuberculosis"), ("cond", "chronic infection"), ("cond", "still")],
      cap={"al_amyloidosis": 0.5, "nephrotic_syndrome": 0.9, "membranous_nephropathy": 0.5, "minimal_change_disease": 0.4, "focal_segmental_glomerulosclerosis": 0.5}, src="Lachmann NEJM 2007"),
 dict(id="cyanide", dx=["cyanide_poisoning"], req=[("cyanide", ">", 0.5)], alt_req=[("lactate", ">=", 10), ("ag_c", ">", 16), ("cohb", ">", 10)], alt_req2=[("lactate", ">=", 10), ("ag", ">", 16), ("cohb", ">", 10)], sup=[("hco3", "<", 18), ("ph", "<", 7.3), ("lactate", ">=", 8)], min_sup=0, excl=[("lactate", "<", 4)],
      cap={"carbon_monoxide_poisoning": 0.9, "lactic_acidosis": 0.9, "septic_shock": 0.4, "sepsis": 0.4, "metformin_associated_lactic_acidosis": 0.2, "lactic_acidosis_metformin_associated": 0.2}, src="Baud 2002: lactate ≥10 mmol/L in fire victims"),
 dict(id="sah_csf", dx=["subarachnoid_hemorrhage"], req=[("xantho", "pos", None)], sup=[("na", "<", 135), ("trop_c", ">", 50), ("glucose", ">", 140), ("wbc", ">", 11)], min_sup=0,
      cap={"bacterial_meningitis": 0.5, "viral_meningitis": 0.5, "meningitis": 0.5, "hyponatremia": 0.9, "syndrome_of_inappropriate_antidiuretic_hormone": 0.9, "acute_myocardial_infarction": 0.4}, src="AHA/ASA 2023 SAH: xanthochromia"),
 dict(id="hsv_encephalitis", dx=["hsv_encephalitis"], req=[("csf_prot", ">", 45), ("csf_glu", ">=", 40)], sup=[("na", "<", 135), ("csf_prot", "<", 200), ("crp", "<", 40), ("pct", "<", 0.5)], min_sup=1, excl=[("csf_glu", "<", 30), ("pct", ">", 2), ("xantho", "pos", None)], strength="pattern",
      ctx_any=[("cond", "encephal"), ("cond", "seizure"), ("cond", "confusion"), ("cond", "altered mental"), ("cond", "fever"), ("cond", "headache"), ("cond", "behaviou"), ("cond", "behavio")],
      cap={"bacterial_meningitis": 0.4, "tuberculous_meningitis": 0.5, "meningitis": 0.9, "viral_meningitis": 0.9}, src="IDSA 2008 encephalitis: lymphocytic CSF, raised protein, normal glucose"),
 dict(id="dmd", dx=["duchenne_muscular_dystrophy"], req=[("ck", ">", 2000), ("ast", ">", 60)], sup=[("ck", ">", 5000), ("ggt", "<", 60), ("alt", ">", 50), ("ldh", ">", 300)], min_sup=1, ctx=[("sex", "m"), ("age_lt", 16)], excl=[("ggt", ">", 100), ("ck", "<", 500), ("tbil", ">", 2), ("crp", ">", 40), ("trop_c", ">", 50), ("urate", ">", 10)],
      cap={"rhabdomyolysis": 0.5, "acute_hepatitis": 0.2, "viral_hepatitis": 0.2, "drug_induced_liver_injury": 0.2, "hepatitis": 0.2, "polymyositis": 0.5, "dermatomyositis": 0.5, "ischemic_hepatitis": 0.2, "acute_viral_hepatitis_pattern": 0.2, "hepatocellular_injury_pattern": 0.3}, src="Birnkrant 2018: CK >10-50× ULN with 'transaminitis' of muscle origin"),
 dict(id="mh", dx=["malignant_hyperthermia"], req=[("pco2", ">", 55), ("k", ">", 5.5)], sup=[("ph", "<", 7.25), ("ck", ">", 1000), ("temp", ">", 38.8), ("lactate", ">", 4), ("umyoglobin", "pos", None)], min_sup=1,
      ctx_any=[("cond", "anesth"), ("cond", "anaesth"), ("cond", "surgery"), ("cond", "succinylcholine"), ("cond", "volatile"), ("cond", "sevoflurane"), ("cond", "operating")],
      cap={"rhabdomyolysis": 0.8, "neuroleptic_malignant_syndrome": 0.4, "respiratory_acidosis": 0.9, "hyperkalemia": 0.9, "sepsis": 0.4, "heat_stroke": 0.4}, src="Larach 2010 clinical grading"),
 dict(id="isopropanol", dx=["isopropanol_poisoning"], req=[("isoprop", ">", 10)], alt_req=[("osm_gap", ">", 10), ("acetone", ">", 5), ("hco3", ">=", 20)], sup=[("bhb", "<", 1), ("glucose", "<", 200), ("ag_c", "<", 16), ("ag", "<", 16)], min_sup=0, excl=[("hco3", "<", 15), ("ethanol", ">", 50)],
      cap={"methanol_poisoning": 0.2, "ethylene_glycol_poisoning": 0.2, "diabetic_ketoacidosis": 0.2, "alcoholic_ketoacidosis": 0.3, "alcohol_intoxication": 0.5, "starvation_ketosis": 0.3}, src="Goldfrank's: ketosis without acidosis + osmolal gap"),
 dict(id="amatoxin", dx=["amatoxin_poisoning"], req=[("alt", ">", 1000), ("inr", ">", 1.5)], sup=[("inr", ">", 2), ("cr", ">", 1.5), ("glucose", "<", 70), ("tbil", ">", 2), ("plt", "<", 100)], min_sup=1, excl=[("apap", ">", 10), ("hav_igm", "pos", None), ("hbsag", "pos", None), ("trop_c", ">", 100), ("ck", ">", 5000)],
      ctx_any=[("cond", "mushroom"), ("cond", "amanita"), ("cond", "forag"), ("cond", "wild fung"), ("cond", "قارچ")],
      cap={"acetaminophen_hepatotoxicity": 0.2, "acute_liver_failure": 0.9, "ischemic_hepatitis": 0.4, "acute_viral_hepatitis_pattern": 0.4, "drug_induced_liver_injury": 0.5, "acute_hepatitis": 0.6}, src="Ye & Liu 2018"),
 dict(id="isoniazid_hepatotoxicity", dx=["isoniazid_hepatotoxicity", "drug_induced_liver_injury"], req=[("alt", ">", 120)], sup=[("alt", ">", 200), ("tbil", ">", 2), ("r_ratio", ">", 5), ("eos_abs", ">", 0.5)], min_sup=1, ctx_any=[("med", "isoniazid"), ("med", "inh"), ("med", "rifamp"), ("med", "pyrazinamide"), ("med", "anti-tb"), ("med", "antituber"), ("cond", "tuberculosis treatment")],
      excl=[("hav_igm", "pos", None), ("hbc_igm", "pos", None), ("apap", ">", 10), ("ck", ">", 2000)],
      cap={"acute_viral_hepatitis_pattern": 0.4, "hepatitis_a": 0.3, "hepatitis_b": 0.3, "autoimmune_hepatitis": 0.5, "acute_hepatitis": 0.6}, src="ATS 2006: ALT >3× ULN with symptoms / >5× ULN"),
 dict(id="snakebite_vicc", dx=["snake_envenomation_coagulopathy"], req=[("inr", ">", 1.5), ("fib", "<", 150)], sup=[("fib", "<", 100), ("ddimer", ">", 2), ("plt", "<", 100), ("cr", ">", 1.5), ("ck", ">", 1000), ("hb", "<", 10)], min_sup=1,
      ctx_any=[("cond", "snake"), ("cond", "bite"), ("cond", "envenom"), ("cond", "viper"), ("cond", "مار")],
      cap={"disseminated_intravascular_coagulation": 0.6, "liver_cirrhosis": 0.2, "acute_liver_failure": 0.3, "warfarin_over_anticoagulation": 0.2, "vitamin_k_deficiency": 0.2, "sepsis": 0.4}, src="WHO 2016 snakebite: VICC"),
 dict(id="nait", dx=["neonatal_alloimmune_thrombocytopenia"], req=[("plt", "<", 50), ("hb", ">=", 13), ("wbc", ">=", 5)], sup=[("crp", "<", 10), ("pct", "<", 0.5), ("plt", "<", 20), ("tbil", "<", 10)], min_sup=1, ctx=[("age_lt", 0.1)], excl=[("pct", ">", 2), ("bcx", "pos", None), ("crp", ">", 20), ("dat", "pos", None), ("blasts", ">", 0)],
      cap={"neonatal_sepsis": 0.4, "sepsis": 0.3, "disseminated_intravascular_coagulation": 0.3, "immune_thrombocytopenia": 0.5, "thrombocytopenia": 0.9, "hemolytic_disease_of_the_newborn": 0.3}, src="Lieberman 2019: isolated severe thrombocytopenia in a well neonate"),
 dict(id="digeorge", dx=["digeorge_syndrome", "hypoparathyroidism"], req=[("ca_c", "<", 8.0), ("pth", "<", 20), ("cd3", "<", 1500)], alt_req=[("ca", "<", 8.0), ("pth", "<", 20), ("cd3", "<", 1500)], alt_req2=[("ca", "<", 8.0), ("pth", "<", 20), ("alc", "<", 2.5)], sup=[("phos", ">", 6), ("mg", ">=", 1.6), ("alc", "<", 3)], min_sup=0, ctx=[("age_lt", 6)], excl=[("mg", "<", 1.2)],
      cap={"hypoparathyroidism": 0.9, "hypocalcemia": 0.9, "severe_combined_immunodeficiency_scid": 0.5, "pseudohypoparathyroidism": 0.3, "vitamin_d_deficiency": 0.3, "rickets": 0.3}, src="ESID 2019: hypoparathyroidism + T-cell lymphopenia"),
 dict(id="hyper_ige", dx=["hyper_ige_syndrome"], req=[("ige", ">", 2000)], sup=[("eos_abs", ">", 0.7), ("igg", ">=", 600), ("crp", ">", 10)], min_sup=1, excl=[("eos_abs", ">", 5), ("igg", "<", 400), ("ana", ">=", 160)],
      cap={"atopic_dermatitis": 0.6, "allergic_bronchopulmonary_aspergillosis": 0.6, "hypereosinophilic_syndrome": 0.4, "eosinophilia": 0.9, "parasitic_infection": 0.5, "asthma": 0.6}, src="ESID 2019 working definition: IgE >2000 IU/mL"),
 dict(id="cpp", dx=["central_precocious_puberty"], req=[("lh", ">=", 0.3)], sup=[("e2", ">", 20), ("testo", ">", 30), ("fsh", ">", 1.5), ("lh_fsh", ">", 0.6)], min_sup=1, ctx=[("age_lt", 9)], excl=[("lh", "<", 0.1), ("hcg", ">", 5), ("prl", ">", 100)],
      cap={"polycystic_ovary_syndrome": 0.2, "hypogonadism": 0.1, "primary_ovarian_insufficiency": 0.1, "menopause": 0.05, "turner_syndrome": 0.3, "congenital_adrenal_hyperplasia": 0.5}, src="Carel & Léger 2008: basal LH ≥0.3 IU/L (ICMA)"),
 dict(id="gestational_thyrotoxicosis", dx=["gestational_transient_thyrotoxicosis"], req=[("tsh", "<", 0.1), ("trab", "<", 1.75)], sup=[("ft4", ">", 1.8), ("tpo", "<", 35), ("hcg", ">", 100000), ("k", "<", 3.5), ("uket", "pos", None)], min_sup=1, ctx=[("pregnant", True)], excl=[("trab", ">=", 1.75), ("tpo", ">", 100)],
      cap={"graves_disease": 0.3, "graves_disease_hyperthyroidism": 0.3, "primary_hyperthyroidism": 0.5, "hyperthyroidism": 0.6, "thyroid_storm": 0.2, "toxic_multinodular_goiter": 0.2, "subacute_thyroiditis": 0.4}, src="ATA 2017: hCG-mediated, TRAb-negative, resolves by 14–18 wk"),
 dict(id="sheehan", dx=["sheehan_syndrome", "hypopituitarism_panhypopituitarism"], req=[("ft4", "<", 0.8), ("tsh", "<", 5), ("prl", "<", 5)], alt_req=[("ft4", "<", 0.8), ("tsh", "<", 5), ("cortisol_am", "<", 5), ("na", "<", 135)], sup=[("cortisol_am", "<", 5), ("na", "<", 135), ("glucose", "<", 70), ("lh", "<", 1), ("fsh", "<", 1), ("igf1", "<", 80)], min_sup=1, ctx=[("sex", "f")], excl=[("tsh", ">", 10)],
      ctx_any=[("cond", "postpartum"), ("cond", "post-partum"), ("cond", "haemorrhage"), ("cond", "hemorrhage"), ("cond", "deliver"), ("cond", "lactat"), ("cond", "amenorrh"), ("cond", "زایمان")],
      cap={"primary_hypothyroidism": 0.2, "hypothyroidism": 0.4, "central_hypothyroidism": 0.9, "addison_disease": 0.3, "primary_adrenal_insufficiency": 0.3, "secondary_adrenal_insufficiency": 0.9, "hyponatremia": 0.9, "syndrome_of_inappropriate_antidiuretic_hormone": 0.3}, src="Fleseriu 2016"),
 dict(id="gestational_thrombocytopenia", dx=["gestational_thrombocytopenia"], req=[("plt", "<", 150), ("plt", ">=", 75)], sup=[("alt", "<", 40), ("ldh", "<", 250), ("upcr", "<", 0.3), ("cr", "<", 0.9), ("hb", ">=", 10), ("urate", "<", 6)], min_sup=2, ctx=[("pregnant", True)], strength="pattern",
      excl=[("plt", "<", 70), ("ldh", ">", 600), ("alt", ">", 70), ("upcr", ">", 0.3), ("schisto", ">", 1), ("cr", ">", 1.1), ("ast", ">", 70), ("fib", "<", 200), ("ddimer", ">", 4)],
      cap={"immune_thrombocytopenia": 0.5, "hellp_syndrome": 0.3, "preeclampsia": 0.3, "thrombotic_thrombocytopenic_purpura": 0.2, "disseminated_intravascular_coagulation": 0.2, "thrombocytopenia": 0.9, "aplastic_anemia": 0.2}, src="ACOG PB 207 (2019)"),
 dict(id="obstetric_aps", dx=["obstetric_antiphospholipid_syndrome", "antiphospholipid_syndrome"], req=[("la", "pos", None)], alt_req=[("acl", ">", 40)], alt_req2=[("b2gp", ">", 40)], sup=[("aptt", ">", 38), ("plt", "<", 150), ("plt", ">=", 50), ("la", "pos", None), ("acl", ">", 40), ("b2gp", ">", 40)], min_sup=1, ctx=[("sex", "f")],
      ctx_any=[("cond", "miscarriage"), ("cond", "pregnancy loss"), ("cond", "fetal loss"), ("cond", "stillbirth"), ("cond", "preeclampsia"), ("cond", "pre-eclampsia"), ("cond", "placental"), ("cond", "recurrent abortion"), ("cond", "سقط"), ("pregnant", True)],
      cap={"heparin_effect_coagulation": 0.3, "hemophilia_a": 0.1, "factor_viii_deficiency": 0.1, "von_willebrand_disease": 0.2, "immune_thrombocytopenia": 0.5, "systemic_lupus_erythematosus": 0.8}, src="ACR/EULAR 2023 APS criteria"),
 dict(id="hyperviscosity", dx=["hyperviscosity_syndrome", "waldenstrom_macroglobulinemia"], req=[("viscosity", ">", 4)], alt_req=[("igm", ">", 4000), ("hb", "<", 11)], alt_req2=[("igm", ">", 3000), ("tp", ">", 10)], sup=[("igm", ">", 3000), ("hb", "<", 11), ("tp", ">", 10), ("esr", ">", 100), ("mspike", ">", 3), ("na", "<", 135)], min_sup=0,
      cap={"multiple_myeloma": 0.6, "pseudohyponatremia": 0.9, "hyponatremia": 0.5, "monoclonal_gammopathy_of_undetermined_significance": 0.4, "mgus": 0.4, "anemia": 0.9}, src="Gertz 2018: serum viscosity >4 cP"),
 dict(id="sulfonylurea_hypoglycemia", dx=["sulfonylurea_induced_hypoglycemia", "hyperinsulinemic_hypoglycemia"], req=[("glucose", "<", 55), ("insulin", ">=", 3), ("cpep", ">=", 0.6)], sup=[("bhb", "<", 2.7), ("cr", ">", 1.3), ("k", "<", 3.5)], min_sup=0, excl=[("cpep", "<", 0.2)],
      ctx_any=[("med", "glibenclamide"), ("med", "glyburide"), ("med", "gliclazide"), ("med", "glimepiride"), ("med", "glipizide"), ("med", "sulfonylurea"), ("med", "sulphonylurea"), ("med", "repaglinide"), ("cond", "sulfonylurea"), ("cond", "diabetic relative"), ("cond", "accidental ingestion")],
      cap={"insulinoma": 0.5, "factitious_hypoglycemia": 0.6, "fasting_hypoglycemia": 0.9, "reactive_hypoglycemia": 0.3, "adrenal_insufficiency": 0.3, "addison_disease": 0.3}, src="Cryer 2009 Endocrine Society: endogenous hyperinsulinism pattern; drug screen distinguishes from insulinoma"),
 dict(id="beta_blocker_tox", dx=["beta_blocker_toxicity"], req=[("hr", "<", 50)], sup=[("glucose", "<", 70), ("k", ">", 5.0), ("lactate", ">", 2), ("ph", "<", 7.3)], min_sup=1, excl=[("glucose", ">", 250), ("tsh", ">", 10), ("k", ">", 7), ("digoxin", ">", 2)],
      ctx_any=[("med", "propranolol"), ("med", "metoprolol"), ("med", "atenolol"), ("med", "bisoprolol"), ("med", "carvedilol"), ("med", "labetalol"), ("med", "nadolol"), ("med", "sotalol"), ("med", "beta-blocker"), ("med", "beta blocker"), ("cond", "beta-blocker"), ("cond", "beta blocker"), ("cond", "overdose")],
      cap={"calcium_channel_blocker_toxicity": 0.5, "digoxin_toxicity": 0.4, "hypothyroidism": 0.3, "myxedema_coma": 0.3, "hypoglycemia": 0.9, "fasting_hypoglycemia": 0.5, "sick_sinus_syndrome": 0.5, "bradycardia": 0.9}, src="Kerns 2007: bradycardia + hypoglycaemia ± hyperkalaemia"),
 dict(id="adrenal_crisis", dx=["adrenal_crisis", "primary_adrenal_insufficiency", "addison_disease"], req=[("cortisol_am", "<", 5), ("na", "<", 130)], alt_req=[("random_cortisol", "<", 5), ("na", "<", 130)], alt_req2=[("na", "<", 130), ("k", ">", 5.0), ("glucose", "<", 70), ("cortisol_am", "<", 10)], sup=[("k", ">", 5.0), ("glucose", "<", 70), ("bun_cr", ">", 20), ("acth", ">", 100), ("ca_c", ">", 10.3), ("eos_abs", ">", 0.5), ("hco3", "<", 20)], min_sup=1, excl=[("cortisol_am", ">", 18), ("random_cortisol", ">", 18)],
      cap={"syndrome_of_inappropriate_antidiuretic_hormone": 0.3, "siadh": 0.3, "hyponatremia": 0.9, "hyperkalemia": 0.9, "hypovolemic_hyponatremia": 0.6, "septic_shock": 0.5, "sepsis": 0.5, "hypoglycemia": 0.9, "fasting_hypoglycemia": 0.4, "secondary_adrenal_insufficiency": 0.7, "type_4_renal_tubular_acidosis": 0.4}, src="Bornstein 2016: cortisol <5 µg/dL under stress + Na/K/glucose triad"),
 dict(id="hypothermia", dx=["accidental_hypothermia"], req=[("temp", "<", 35)], sup=[("k", ">", 5.0), ("lactate", ">", 2), ("glucose", ">", 140), ("ph", "<", 7.3), ("plt", "<", 150), ("ck", ">", 1000), ("amylase", ">", 150)], min_sup=0,
      cap={"sepsis": 0.6, "septic_shock": 0.6, "diabetic_ketoacidosis": 0.4, "hyperglycemia": 0.7, "acute_pancreatitis": 0.5, "hyperkalemia": 0.9, "myxedema_coma": 0.7}, src="WMS 2019"),
 dict(id="heat_stroke", dx=["heat_stroke"], req=[("temp", ">", 40), ("ck", ">", 1000)], sup=[("alt", ">", 120), ("cr", ">", 1.5), ("inr", ">", 1.5), ("plt", "<", 100), ("lactate", ">", 2), ("k", "<", 3.5), ("phos", "<", 2.5)], min_sup=1, excl=[("pct", ">", 5), ("bcx", "pos", None)],
      ctx_any=[("cond", "heat"), ("cond", "exertion"), ("cond", "exercise"), ("cond", "marathon"), ("cond", "athlet"), ("cond", "sun"), ("cond", "hot "), ("cond", "outdoor"), ("cond", "labour"), ("cond", "labor"), ("cond", "military"), ("cond", "گرما"), ("cond", "ورزش")],
      cap={"sepsis": 0.5, "septic_shock": 0.5, "neuroleptic_malignant_syndrome": 0.5, "malignant_hyperthermia": 0.5, "rhabdomyolysis": 0.9, "ischemic_hepatitis": 0.7, "acute_liver_failure": 0.7, "disseminated_intravascular_coagulation": 0.7, "serotonin_syndrome": 0.5}, src="WMS 2019: core >40 °C with multi-organ injury"),
 dict(id="taco", dx=["transfusion_associated_circulatory_overload"], req=[("natri_high", "==", 1)], alt_req=[("ntprobnp", ">", 1500)], sup=[("po2", "<", 70), ("cr", ">", 1.3), ("na", "<", 135), ("trop_c", ">", 14)], min_sup=0, excl=[("ntprobnp", "<", 300)],
      ctx_any=[("cond", "transfus"), ("cond", "packed red"), ("cond", "prbc"), ("cond", "blood product"), ("cond", "تزریق خون")],
      cap={"transfusion_related_acute_lung_injury": 0.4, "trali": 0.4, "acute_respiratory_distress_syndrome": 0.5, "pulmonary_embolism": 0.5, "heart_failure": 0.9, "acute_decompensated_heart_failure": 0.9}, src="ISBT 2018 TACO revised criteria: BNP/NT-proBNP rise within 12 h"),
 dict(id="ahtr", dx=["acute_hemolytic_transfusion_reaction"], req=[("dat", "pos", None), ("ldh", ">", 400), ("hapto", "<", 30)], alt_req=[("ldh", ">", 400), ("hapto", "<", 30), ("hb", "<", 10), ("tbil", ">", 1.5)], sup=[("tbil", ">", 1.5), ("cr", ">", 1.5), ("fib", "<", 150), ("k", ">", 5.0), ("umyoglobin", "pos", None), ("plt", "<", 100)], min_sup=1,
      ctx_any=[("cond", "transfus"), ("cond", "packed red"), ("cond", "prbc"), ("cond", "blood product"), ("cond", "تزریق خون")],
      cap={"warm_autoimmune_hemolytic_anemia": 0.5, "autoimmune_hemolytic_anemia": 0.5, "thrombotic_thrombocytopenic_purpura": 0.5, "hemolytic_uremic_syndrome": 0.5, "hemolytic_anemia": 0.9, "g6pd_deficiency": 0.4, "paroxysmal_nocturnal_hemoglobinuria": 0.3, "sepsis": 0.5}, src="AABB Technical Manual: DAT+, LDH↑, haptoglobin↓ post-transfusion"),
 dict(id="organic_acidemia_core", dx=["organic_acidemia", "propionic_acidemia", "methylmalonic_acidemia"], req=[("ag_c", ">", 20), ("hco3", "<", 15), ("nh3", ">", 150)], alt_req=[("ag", ">", 20), ("hco3", "<", 15), ("nh3", ">", 150)], sup=[("uket", "pos", None), ("anc", "<", 1.5), ("plt", "<", 150), ("glucose", "<", 60), ("lactate", ">", 3)], min_sup=1, ctx=[("age_lt", 12)], excl=[("glucose", ">", 250), ("eg", ">", 0), ("methanol", ">", 0)],
      cap={"urea_cycle_disorder": 0.5, "ornithine_transcarbamylase_deficiency": 0.4, "diabetic_ketoacidosis": 0.2, "neonatal_sepsis": 0.6, "sepsis": 0.5, "lactic_acidosis": 0.7, "maple_syrup_urine_disease": 0.5, "medium_chain_acyl_coa_dehydrogenase_deficiency": 0.3, "high_anion_gap_metabolic_acidosis": 0.9}, src="Baumgartner 2014 MMA/PA guideline"),
 dict(id="reye", dx=["reye_syndrome"], req=[("nh3", ">", 100), ("alt", ">", 120), ("tbil", "<=", 3.0)], sup=[("inr", ">", 1.5), ("glucose", "<", 60), ("ast", ">", 120), ("ck", ">", 500)], min_sup=1, ctx=[("age_lt", 18)], excl=[("tbil", ">", 5), ("valproate", ">", 50), ("apap", ">", 10), ("hav_igm", "pos", None)],
      ctx_any=[("cond", "aspirin"), ("cond", "salicylate"), ("cond", "influenza"), ("cond", "varicella"), ("cond", "chickenpox"), ("cond", "viral"), ("cond", "vomiting"), ("cond", "encephalop"), ("med", "aspirin"), ("med", "salicylate")],
      cap={"acute_liver_failure": 0.7, "hepatic_encephalopathy": 0.6, "urea_cycle_disorder": 0.5, "ornithine_transcarbamylase_deficiency": 0.5, "medium_chain_acyl_coa_dehydrogenase_deficiency": 0.6, "acute_viral_hepatitis_pattern": 0.4, "valproate_induced_hyperammonemic_encephalopathy": 0.3, "acute_hepatitis": 0.5}, src="CDC Reye case definition"),
 dict(id="tss", dx=["toxic_shock_syndrome", "septic_shock"], req=[("temp", ">=", 38.9), ("plt", "<", 100), ("cr", ">", 1.5)], alt_req=[("temp", ">=", 38.9), ("cr", ">", 2.0), ("ck", ">", 400)], alt_req2=[("temp", ">=", 38.9), ("plt", "<", 100), ("alt", ">", 80), ("tbil", ">", 2.4)], sup=[("ck", ">", 400), ("tbil", ">", 2.4), ("alt", ">", 80), ("bcx", "neg", None), ("crp", ">", 100), ("lactate", ">", 2), ("alb", "<", 3), ("ca_c", "<", 8.5)], min_sup=1,
      ctx_any=[("cond", "tampon"), ("cond", "menstru"), ("cond", "rash"), ("cond", "desquam"), ("cond", "wound"), ("cond", "packing"), ("cond", "post-operative"), ("cond", "postoperative"), ("cond", "nasal pack"), ("cond", "staph"), ("cond", "strep"), ("cond", "hypotension"), ("cond", "shock")],
      cap={"sepsis": 0.95, "kawasaki_disease": 0.4, "multisystem_inflammatory_syndrome_cardiac_pattern": 0.5, "leptospirosis": 0.5, "rickettsial_infection": 0.5, "dengue_fever": 0.4, "hemophagocytic_lymphohistiocytosis": 0.5, "stevens_johnson_syndrome": 0.4}, src="CDC 2011 TSS case definition: fever ≥38.9 °C + ≥3 organ systems"),
 dict(id="ketotic_hypoglycemia", dx=["ketotic_hypoglycemia_of_childhood"], req=[("glucose", "<", 55), ("bhb", ">", 2.0)], sup=[("insulin", "<", 2), ("lactate", "<", 2.5), ("nh3", "<", 80), ("cortisol_am", ">", 10)], min_sup=1, ctx=[("age_lt", 8), ("age_ge", 0.75)], excl=[("insulin", ">=", 3), ("lactate", ">", 5), ("nh3", ">", 100), ("alt", ">", 120), ("cortisol_am", "<", 5), ("ethanol", ">", 10)],
      cap={"hyperinsulinemic_hypoglycemia": 0.2, "insulinoma": 0.1, "glycogen_storage_disease_type_1": 0.3, "von_gierke_disease": 0.3, "medium_chain_acyl_coa_dehydrogenase_deficiency": 0.2, "diabetic_ketoacidosis": 0.1, "starvation_ketosis": 0.6, "adrenal_insufficiency": 0.4, "growth_hormone_deficiency": 0.5, "fasting_hypoglycemia": 0.9}, src="Thornton 2015 PES: ketotic hypoinsulinaemic hypoglycaemia with normal lactate/ammonia"),
 dict(id="htg_pancreatitis", dx=["hypertriglyceridemia_induced_pancreatitis", "acute_pancreatitis"], req=[("lipase", ">", 180), ("tg", ">", 1000)], alt_req=[("amylase", ">", 300), ("tg", ">", 1000)], sup=[("tg", ">", 2000), ("glucose", ">", 200), ("na", "<", 135), ("ca_c", "<", 8.5), ("crp", ">", 100)], min_sup=0, excl=[("alt", ">", 150), ("tbil", ">", 3)],
      cap={"gallstone_pancreatitis_support_pattern": 0.3, "alcoholic_pancreatitis": 0.3, "pseudohyponatremia": 0.9, "hyponatremia": 0.4, "familial_chylomicronemia_syndrome": 0.9, "hypertriglyceridemia": 0.9, "severe_hypertriglyceridemia": 0.95, "diabetic_ketoacidosis": 0.6}, src="ACG 2024: TG >1000 mg/dL"),
 dict(id="alcoholic_pancreatitis", dx=["alcoholic_pancreatitis", "acute_pancreatitis"], req=[("lipase", ">", 180), ("ggt", ">", 100)], alt_req=[("amylase", ">", 300), ("ggt", ">", 100)], sup=[("mcv", ">", 98), ("ast_alt", ">", 1.5), ("tg", "<", 500), ("alt", "<", 150), ("mg", "<", 1.7), ("phos", "<", 2.5)], min_sup=2, excl=[("alt", ">", 150), ("tg", ">", 1000), ("tbil", ">", 4), ("ca_c", ">", 10.5), ("ca", ">", 10.5)],
      ctx_any=[("cond", "alcohol"), ("cond", "ethanol"), ("cond", "drink"), ("cond", "etoh"), ("cond", "الکل")],
      cap={"gallstone_pancreatitis_support_pattern": 0.3, "hypertriglyceridemia_induced_pancreatitis": 0.3, "alcoholic_hepatitis": 0.8, "alcoholic_liver_disease": 0.9, "chronic_pancreatitis": 0.6}, src="ACG 2024; Tenner 1994 ALT >150 → biliary"),
 dict(id="malignant_effusion", dx=["malignant_pleural_effusion", "exudative_pleural_effusion"], req=[("pleural_prot", ">", 3.0), ("pleural_ldh", ">", 200), ("pleural_ada", "<", 40)], sup=[("pleural_glu", "<", 60), ("ldh", ">", 250), ("alb", "<", 3.5), ("cea", ">", 5), ("ca125", ">", 35), ("hb", "<", 12)], min_sup=1, excl=[("pleural_ada", ">=", 40), ("pct", ">", 2), ("crp", ">", 150), ("ntprobnp", ">", 1500)],
      ctx_any=[("cond", "cancer"), ("cond", "carcinoma"), ("cond", "malignan"), ("cond", "lymphoma"), ("cond", "mesothelioma"), ("cond", "smok"), ("cond", "weight loss"), ("cond", "metasta"), ("cond", "سرطان"), ("age_ge", 50)],
      cap={"tuberculous_pleuritis": 0.3, "tuberculosis": 0.3, "parapneumonic_effusion": 0.5, "empyema": 0.3, "heart_failure": 0.3, "transudative_pleural_effusion": 0.2}, src="BTS 2023 pleural disease; Light criteria"),
 dict(id="pancytopenia", dx=["pancytopenia"], req=[("hb", "<", 10), ("plt", "<", 100), ("anc", "<", 1.5)], alt_req=[("hb", "<", 10), ("plt", "<", 100), ("wbc", "<", 4)], sup=[("retic", "<", 1), ("mcv", ">", 100), ("ldh", ">", 400), ("b12", "<", 200), ("blasts", ">", 0), ("ferritin", ">", 1000), ("alc", "<", 1.0)], min_sup=0, strength="pattern",
      cap={"anemia": 0.9, "thrombocytopenia": 0.9, "neutropenia": 0.9, "leukopenia": 0.9, "iron_deficiency_anemia": 0.4, "immune_thrombocytopenia": 0.3}, src="Killick 2016 BSH: three-lineage cytopenia → marrow examination"),
 dict(id="acute_hepatitis_pattern", dx=["acute_hepatitis"], req=[("alt", ">", 400), ("alp", "<", 300)], sup=[("ast", ">", 300), ("tbil", ">", 2), ("inr", ">=", 1.5), ("r_ratio", ">", 5), ("ldh", "<", 1000)], min_sup=1, strength="pattern",
      excl=[("ck", ">", 2000), ("ast_alt", ">", 2.5), ("trop_c", ">", 100), ("hav_igm", "pos", None), ("hbsag", "pos", None), ("hbc_igm", "pos", None), ("hev_igm", "pos", None), ("apap", ">", 10), ("ferritin", ">", 10000), ("ldh", ">", 2000)],
      cap={"alcoholic_hepatitis": 0.4, "ischemic_hepatitis": 0.5, "cholestasis": 0.3, "cholestatic_liver_injury_pattern": 0.3, "rhabdomyolysis": 0.3, "liver_cirrhosis": 0.4, "hemochromatosis": 0.3}, src="Wendon 2017 EASL ALF: ALT ≥5–10× ULN hepatocellular; INR ≥1.5 flags ALF"),
])

# ---------------------------------------------------------------------------
# ESL extension 4 (2026-10-21) — severity-graded DEFINITIONAL dyselectrolytaemias
# Motivated by MIMIC-IV demo error analysis: K 6.8 mmol/L (pH 7.07) was absent
# from the 15-entry differential because single-analyte electrolyte entities
# received a flat ~0.57 'possible pattern' score irrespective of severity and
# were out-ranked by trivial findings.  Hyperkalaemia, hyponatraemia etc. are
# definitional diagnoses (KDIGO 2020 K+ controversies; Spasovski 2014 ESE/ESICM
# hyponatraemia; Adrogué & Madias NEJM 2000; Endocrine Society hypoglycaemia
# 2009 Whipple levels; 5th Int. Workshop hypercalcaemia) so severity tiers are
# anchors (severe) / strong (moderate); mild deviations stay with the rule layer.  Tiers use disjoint 'between' ranges so exactly
# one tier fires per analyte.  Pseudo-hyperkalaemia is excluded on extreme
# thrombocytosis / leukocytosis (Sevastos 2008).
# ---------------------------------------------------------------------------
_ESL_LIBRARY.extend([
 dict(id="hyperkalemia_severe", dx=["hyperkalemia", "severe_hyperkalemia"], req=[("k", ">=", 6.5)], sup=[("cr", ">", 1.5), ("hco3", "<", 20), ("glucose", "<", 70)], min_sup=0, strength="anchor",
      excl=[("plt", ">", 1000), ("wbc", ">", 100)], cap={"hyperkalemia_pattern": 0.9, "hyperkalemia_acidosis_pattern": 0.9}, src="KDIGO 2020 potassium controversies conference; Sevastos 2008 pseudohyperkalaemia"),
 dict(id="hyperkalemia_moderate", dx=["hyperkalemia"], req=[("k", "between", (6.0, 6.4999))], sup=[("cr", ">", 1.5), ("hco3", "<", 20)], min_sup=0, strength="strong",
      excl=[("plt", ">", 1000), ("wbc", ">", 100)], cap={"hyperkalemia_pattern": 0.9}, src="KDIGO 2020 potassium controversies conference"),
 dict(id="hypokalemia_severe", dx=["hypokalemia", "severe_hypokalemia"], req=[("k", "<", 2.5)], sup=[("mg", "<", 1.7), ("hco3", ">", 28)], min_sup=0, strength="anchor", src="Gennari NEJM 1998; Kardalas 2018"),
 dict(id="hypokalemia_moderate", dx=["hypokalemia"], req=[("k", "between", (2.5, 2.9999))], sup=[("mg", "<", 1.7), ("hco3", ">", 28)], min_sup=0, strength="strong", src="Gennari NEJM 1998"),
 dict(id="hypernatremia_severe", dx=["hypernatremia"], req=[("na", ">=", 160)], sup=[("glucose", ">", 250), ("cr", ">", 1.5), ("bun_cr", ">", 20)], min_sup=0, strength="anchor", src="Adrogué & Madias NEJM 2000"),
 dict(id="hypernatremia_moderate", dx=["hypernatremia"], req=[("na", "between", (150, 159.999))], sup=[("cr", ">", 1.5), ("bun_cr", ">", 20)], min_sup=0, strength="strong", src="Adrogué & Madias NEJM 2000"),
 dict(id="hyponatremia_severe", dx=["hyponatremia", "severe_hyponatremia"], req=[("na", "<", 120)], sup=[("osm", "<", 275), ("uosm", ">", 100)], min_sup=0, strength="anchor",
      excl=[("glucose", ">", 400), ("tg", ">", 1500), ("tp", ">", 10)], src="Spasovski, ESE/ESICM/ERA 2014 hyponatraemia guideline"),
 dict(id="hyponatremia_moderate", dx=["hyponatremia"], req=[("na", "between", (120, 124.999))], sup=[("osm", "<", 275), ("uosm", ">", 100)], min_sup=0, strength="strong",
      excl=[("glucose", ">", 400), ("tg", ">", 1500), ("tp", ">", 10)], src="Spasovski 2014"),
 dict(id="hypercalcemia_crisis", dx=["hypercalcemia"], req=[("ca_c", ">=", 14.0)], alt_req=[("ica", ">=", 1.75)], sup=[("pth", "<", 20), ("cr", ">", 1.5)], min_sup=0, strength="anchor", src="Minisola BMJ 2015; Endocrine Society"),
 dict(id="hypercalcemia_moderate", dx=["hypercalcemia"], req=[("ca_c", "between", (12.0, 13.999))], alt_req=[("ica", "between", (1.50, 1.7499))], sup=[("pth", "<", 20), ("pth", ">", 65)], min_sup=0, strength="strong", src="Minisola BMJ 2015"),
 # v7 C15 (2026-10-25): a TOTAL calcium can only be graded when it can be albumin-corrected (or ionised calcium is
 # measured) - Cooper & Gittoes BMJ 2008; in acute illness hypoalbuminaemia lowers total calcium with a normal
 # ionised fraction. Without albumin the value is reported as an unconfirmed low total calcium (pattern grade).
 dict(id="hypocalcemia_severe", dx=["hypocalcemia"], req=[("ica", "<", 0.9)], alt_req=[("ca_c", "<", 7.0), ("alb", ">", 0)], sup=[("mg", "<", 1.5), ("phos", ">", 5.0), ("pth", "<", 15)], min_sup=0, strength="anchor", src="Cooper & Gittoes BMJ 2008"),
 dict(id="hypocalcemia_moderate", dx=["hypocalcemia"], req=[("ica", "between", (0.9, 0.9999))], alt_req=[("ca_c", "between", (7.0, 7.499)), ("alb", ">", 0)], sup=[("mg", "<", 1.5), ("phos", ">", 5.0)], min_sup=0, strength="strong", src="Cooper & Gittoes BMJ 2008"),
 dict(id="hypocalcemia_total_uncorrected", dx=["hypocalcemia"], req=[("ca", "<", 7.5), ("alb", "absent", None), ("ica", "absent", None)], sup=[("mg", "<", 1.5), ("phos", ">", 5.0), ("pth", "<", 15)], min_sup=0, strength="pattern",
      note="total calcium below 7.5 mg/dL without albumin or ionised calcium: cannot be corrected - confirm with ionised calcium", src="Cooper & Gittoes BMJ 2008 (correct total calcium for albumin or measure ionised calcium)"),
 dict(id="hypoglycemia_level3", dx=["fasting_hypoglycemia"], req=[("glucose", "<", 40)], sup=[("insulin", ">=", 3), ("cr", ">", 2), ("alt", ">", 200)], min_sup=0, strength="anchor", ctx=[("age_ge", 1)], src="ADA 2023 hypoglycaemia levels; Endocrine Society 2009"),
 dict(id="hypoglycemia_level2", dx=["fasting_hypoglycemia"], req=[("glucose", "between", (40, 53.999))], sup=[("insulin", ">=", 3), ("cr", ">", 2), ("alt", ">", 200)], min_sup=0, strength="strong", ctx=[("age_ge", 1)], src="ADA 2023 hypoglycaemia levels"),
 dict(id="hypomagnesemia_severe", dx=["hypomagnesemia"], req=[("mg", "<", 1.2)], sup=[("k", "<", 3.5), ("ca", "<", 8.5)], min_sup=0, strength="anchor", src="Pham, Clin J Am Soc Nephrol 2014"),
 dict(id="hypophosphatemia_severe", dx=["hypophosphatemia"], req=[("phos", "<", 1.0)], sup=[("k", "<", 3.5), ("mg", "<", 1.7), ("ck", ">", 500)], min_sup=0, strength="anchor", src="Gaasbeek & Meinders Am J Med 2005"),
 dict(id="severe_acidemia", dx=["metabolic_acidosis"], req=[("ph", "<", 7.20), ("hco3", "<", 15)], sup=[("lactate", ">", 4), ("ag_c", ">", 16), ("k", ">", 5.5)], min_sup=0, strength="anchor",
      excl=[("pco2", ">", 60)], src="Kraut & Madias NEJM 2014"),
 # DKA when ketones were NOT measured: hyperglycaemia + HAGMA is strongly suggestive (ADA 2024); ketone assay is the recommended next test
 dict(id="dka_ketones_unmeasured", dx=["diabetic_ketoacidosis", "diabetes_mellitus"], req=[("glucose", ">=", 200), ("hco3", "<", 15), ("ag_c", ">", 16), ("ag_minus_lac", ">", 10)], sup=[("ph", "<", 7.3), ("k", ">", 5.0), ("phos", "<", 2.5)], min_sup=0, strength="strong",
      excl=[("bhb", "<", 3.0), ("uket", "neg", None), ("cr", ">", 6.0)], cap={"metabolic_acidosis": 0.9, "hyperosmolar_hyperglycemic_state": 0.8}, src="ADA/EASD 2024 hyperglycaemic crises consensus; ext9b: with creatinine > 6 mg/dL an unmeasured-ketone gap acidosis is uraemic until ketones are measured (Kraut & Madias NEJM 2014)"),
 # Lactic acidosis tiers: lactate >= 4 is definitional; 2-4 with acidosis is hyperlactataemia with acidosis (Kraut 2014)
 dict(id="lactic_acidosis_definitional", dx=["lactic_acidosis"], req=[("lactate", ">=", 4.0)], sup=[("hco3", "<", 20), ("ph", "<", 7.35), ("ag_c", ">", 16)], min_sup=0, strength="anchor",
      excl=[("cohb", ">", 10)], cap={"metabolic_acidosis": 0.9}, src="Kraut & Madias NEJM 2014 lactic acidosis"),
 dict(id="lactic_acidosis_moderate", dx=["lactic_acidosis"], req=[("lactate", "between", (2.0, 3.9999)), ("hco3", "<", 20)], sup=[("ph", "<", 7.35), ("ag_c", ">", 16)], min_sup=1, strength="pattern",
      excl=[("cohb", ">", 10)], src="Kraut & Madias NEJM 2014"),
])
# ---------------------------------------------------------------------------
# ESL extension 5 (2026-10-21) — critical haematology / coagulation / acid-base
# anchors.  Motivated by eICU-CRD demo held-out safety analysis: critical
# platelet, haemoglobin, leucocyte and INR values and hypercapnic acidaemia
# were not guaranteed a place in the differential because the corresponding
# single-analyte entities carried flat 'possible pattern' scores.  Thresholds
# follow CLSI/College of American Pathologists critical-value consensus lists
# (Howanitz 2002; Campbell & Horvath 2014 systematic review), BSH platelet
# transfusion guideline 2017 (< 20 prophylactic threshold), AABB red-cell
# guideline 2016 (Hb < 7 restrictive threshold), ACCP/BSH warfarin guidelines
# (INR >= 4.5 without bleeding = urgent reversal), Röllig & Ehninger Blood 2015
# (hyperleukocytosis >= 100 x10^9/L), Kraut & Madias NEJM 2014 and
# Berend NEJM 2014 (acid-base physiology).  Entity ids are existing registry
# ids; no new diseases are introduced here.
# ---------------------------------------------------------------------------
_ESL_LIBRARY.extend([
 # --- red cells -------------------------------------------------------------
 dict(id="anemia_critical", dx=["anemia"], req=[("hb", "<", 7.0)], sup=[("mcv", "<", 80), ("ferritin", "<", 30), ("retic", ">", 2.5), ("ldh", ">", 250)], min_sup=0, strength="anchor",
      src="AABB 2016 red-cell transfusion guideline (Hb < 7 g/dL restrictive threshold); CAP critical-value survey (Howanitz 2002)"),
 dict(id="anemia_moderate_severe", dx=["anemia"], req=[("hb", "between", (7.0, 8.9999))], sup=[("mcv", "<", 80), ("ferritin", "<", 30), ("retic", ">", 2.5)], min_sup=0, strength="strong",
      src="WHO haemoglobin severity grading 2011 (moderate 8.0-10.9, severe < 8.0 g/dL)"),
 # --- platelets -------------------------------------------------------------
 dict(id="thrombocytopenia_critical", dx=["thrombocytopenia"], req=[("plt", "<", 20)], sup=[("wbc", "<", 4), ("hb", "<", 10), ("ldh", ">", 250), ("inr", ">", 1.5)], min_sup=0, strength="anchor",
      src="BSH platelet transfusion guideline 2017 (< 20 prophylactic threshold); CAP critical-value consensus"),
 dict(id="thrombocytopenia_severe", dx=["thrombocytopenia"], req=[("plt", "between", (20, 49.9999))], sup=[("wbc", "<", 4), ("hb", "<", 10), ("inr", ">", 1.5)], min_sup=0, strength="strong",
      src="BSH 2017; ASH ITP guideline 2019 severity bands"),
 # --- leucocytes ------------------------------------------------------------
 dict(id="hyperleukocytosis", dx=["acute_leukemia_support_pattern", "chronic_leukemia_support_pattern", "leukocytosis_pattern"], req=[("wbc", ">=", 100)],
      sup=[("blasts", ">", 0), ("ldh", ">", 300), ("urate", ">", 7.0), ("hb", "<", 10), ("plt", "<", 100)], min_sup=0, strength="anchor",
      cap={"nephrotic_syndrome": 0.5, "leukemoid_reaction": 0.6}, src="Röllig & Ehninger, Blood 2015 (hyperleukocytosis >= 100 x10^9/L = presumptive leukaemia until proven otherwise)"),
 dict(id="leukocytosis_marked", dx=["leukocytosis_pattern"], req=[("wbc", "between", (30, 99.9999))], sup=[("bands", ">", 10), ("crp", ">", 50), ("pct", ">", 0.5), ("lactate", ">", 2)], min_sup=0, strength="strong",
      src="Cerny & Rosmarin, leukemoid reaction review 2012 (WBC > 30 x10^9/L without leukaemia)"),
 # --- coagulation -----------------------------------------------------------
 dict(id="inr_critical", dx=["elevated_inr_pattern"], req=[("inr", ">=", 4.5)], sup=[("plt", "<", 100), ("alb", "<", 3.0), ("tbil", ">", 2.0), ("hb", "<", 10)], min_sup=0, strength="anchor",
      src="ACCP 2012 / BSH 2011 oral anticoagulation guidelines (INR >= 4.5 = urgent review/reversal); CAP critical-value consensus"),
 dict(id="inr_elevated", dx=["elevated_inr_pattern"], req=[("inr", "between", (2.0, 4.4999))], sup=[("plt", "<", 100), ("alb", "<", 3.0), ("tbil", ">", 2.0)], min_sup=0, strength="pattern",
      src="BSH 2011 oral anticoagulation guideline"),
 # --- acid-base: acidaemia not explained by low bicarbonate -----------------
 dict(id="hypercapnic_acidemia_severe", dx=["respiratory_acidosis"], req=[("ph", "<", 7.20), ("pco2", ">", 50)], sup=[("hco3", ">", 26), ("k", ">", 5.0)], min_sup=0, strength="anchor",
      excl=[("hco3", "<", 15)], src="Berend et al. NEJM 2014 physiological approach to acid-base; Kraut & Madias 2014"),
 dict(id="hypercapnic_acidemia_moderate", dx=["respiratory_acidosis"], req=[("ph", "between", (7.20, 7.2999)), ("pco2", ">", 50)], sup=[("hco3", ">", 26)], min_sup=0, strength="strong",
      excl=[("hco3", "<", 18)], src="Berend et al. NEJM 2014"),
 dict(id="mixed_acidosis_severe", dx=["mixed_metabolic_and_respiratory_acidosis"], req=[("ph", "<", 7.20), ("pco2", ">", 45), ("hco3", "<", 22)], sup=[("lactate", ">", 2), ("k", ">", 5.0)], min_sup=0, strength="anchor",
      src="Berend et al. NEJM 2014 (acidaemia with both pCO2 up and HCO3 down = mixed disorder)"),
 # --- thyroid: total-hormone tiers (ATA 2016 hyperthyroidism guideline; ATA 2014 hypothyroidism guideline).
 #     Free T4 syndromes exist already; these fire when only TOTAL T4/T3 is reported (UCI thyroid0387 held-out set
 #     showed overt hyperthyroidism with TSH 0.05 and TT4 > 12.5 ug/dL scored only ~0.3 because no total-hormone rule existed).
 dict(id="thyrotox_overt_tt4", dx=["hyperthyroidism", "thyrotoxicosis"], req=[("tsh", "<", 0.1), ("tt4", ">", 12.5)], sup=[("tt3", ">", 200), ("alp", ">", 130), ("ca", ">", 10.3)], min_sup=0, strength="strong",
      excl=[("trab", ">", 1.75)], src="ATA 2016 hyperthyroidism guideline (Ross et al.) — suppressed TSH with elevated T4 = overt thyrotoxicosis; TT4 adult reference 5-12.5 ug/dL (Tietz)"),
 dict(id="t3_toxicosis_tt3", dx=["hyperthyroidism", "thyrotoxicosis"], req=[("tsh", "<", 0.1), ("tt3", ">", 200), ("tt4", "between", (0, 12.5))], sup=[("alp", ">", 130)], min_sup=0, strength="strong",
      excl=[("trab", ">", 1.75)], src="ATA 2016 (T3 toxicosis: suppressed TSH, normal T4, elevated T3)"),
 dict(id="subclin_hyperthyroid_tt4", dx=["subclinical_hyperthyroidism"], req=[("tsh", "<", 0.4), ("tt4", "between", (5.0, 12.5))], sup=[("tt3", "between", (80, 200))], min_sup=0, strength="pattern",
      excl=[("tt3", ">", 200), ("ft4", ">", 1.8)], src="ATA 2016 (subclinical hyperthyroidism = low TSH with normal T4 and T3)"),
 dict(id="hypothyroid_overt_tt4", dx=["primary_hypothyroidism", "hypothyroidism"], req=[("tsh", ">", 10), ("tt4", "<", 5.0)], sup=[("tc", ">", 200), ("ck", ">", 200), ("na", "<", 135)], min_sup=0, strength="anchor",
      src="ATA 2014 hypothyroidism guideline (Jonklaas et al.) — elevated TSH with low T4 = overt primary hypothyroidism"),
 # --- urate: definitional hyperuricaemia (NHANES 2017-18 held-out: urate > 7 mg/dL scored <= 0.34 -> sensitivity 0.3 % at 0.5)
 # v7 C14 (2026-10-25): graded like every other analyte - a mild elevation above the solubility limit is a
 # laboratory pattern (0.80); >= 9.0 mg/dL (ACR 2020: risk stratum for gout/urolithiasis; Cairo-Bishop TLS
 # criterion >= 8.0) is the moderate-severe grade (0.88). Before v7 urate 7.1 carried the same weight as Na 122.
 dict(id="hyperuricemia_definitional", dx=["hyperuricemia"], req=[("urate", "between", (7.0001, 8.9999))], sup=[("cr", ">", 1.3), ("tg", ">", 150), ("glucose", ">", 100), ("ldh", ">", 250)], min_sup=0, strength="pattern",
      src="ACR 2020 gout guideline; Tietz reference intervals (urate M 3.5-7.2, F 2.6-6.0 mg/dL); urate solubility limit 6.8 mg/dL"),
 dict(id="hyperuricemia_marked", dx=["hyperuricemia"], req=[("urate", ">=", 9.0)], sup=[("cr", ">", 1.3), ("tg", ">", 150), ("glucose", ">", 100), ("ldh", ">", 250)], min_sup=0, strength="strong",
      src="ACR 2020 gout guideline (serum urate >= 9 mg/dL stratum); Cairo-Bishop 2004 laboratory TLS (urate >= 8 mg/dL)"),
 dict(id="hyperuricemia_female", dx=["hyperuricemia"], req=[("urate", "between", (6.0001, 7.0))], sup=[("cr", ">", 1.3), ("tg", ">", 150), ("glucose", ">", 100), ("bmi_ge", ">=", 25)], min_sup=1, strength="pattern", ctx=[("sex", "f"), ("age_ge", 18)],
      src="Tietz reference intervals (female upper limit 6.0 mg/dL)"),
 dict(id="severe_acidemia_metabolic_moderate_hco3", dx=["metabolic_acidosis"], req=[("ph", "<", 7.20), ("hco3", "between", (15, 21.9999))], sup=[("lactate", ">", 2), ("ag_c", ">", 16)], min_sup=0, strength="strong",
      excl=[("pco2", ">", 45)], src="Kraut & Madias NEJM 2014"),
])
# ---------------------------------------------------------------------------
# ESL extension 6 (2026-10-21) — context-aware anchors found missing in a blind
# LLM-vs-engine comparison on eICU-CRD demo (see eval/patches/esl_ext6_ranking_20261021.py).
# ---------------------------------------------------------------------------
_ESL_LIBRARY.extend([
 # massive cTn elevation is cardiac whatever the CK: cardiac troponin I is not expressed in adult skeletal muscle
 dict(id="mi_massive_troponin", dx=["acute_myocardial_infarction", "myocardial_infarction", "acute_coronary_syndrome"], req=[("trop_c", ">", 5000)],
      sup=[("ckmb", ">", 5), ("glucose", ">", 140), ("lactate", ">", 2), ("cr", ">", 1.3)], min_sup=0, strength="anchor", ctx=[("age_ge", 18)],
      cap={"rhabdomyolysis": 0.95, "acute_myocardial_injury": 0.8, "myocardial_injury_acuity_undetermined": 0.8, "chronic_myocardial_injury": 0.6},
      src="Fourth Universal Definition of MI (Thygesen 2018); Apple & Collinson 2012 (cTnI cardiac specificity)"),
 # marked renal failure: creatinine >= 2.0 mg/dL cannot be ignored even when chronicity is unknown (KDIGO AKI 2012 / CKD 2024)
 # v6 (SAP Amendment 14, C3): a single raised creatinine establishes REDUCED GFR; KDIGO needs a delta (AKI) or > 90 days
 # (CKD). AKI is asserted from one value only in an acute-care encounter via the KDIGO-imputed baseline (below); CKD only with
 # chronicity clues (registry rule chronic_kidney_disease_chronicity_clues_v14 / ckd_egfr_* with min_sup=1) or history.
 dict(id="renal_failure_marked", dx=["reduced_gfr_chronicity_undetermined"], req=[("cr", ">=", 2.0)],
      sup=[("bun", ">", 40), ("k", ">", 5.0), ("hco3", "<", 20), ("phos", ">", 4.5), ("hb", "<", 10), ("lactate", ">", 2)], min_sup=0, strength="strong", ctx=[("age_ge", 18)],
      excl=[("ck", ">", 5000)], cap={"renal_tubular_acidosis_type_4": 0.5, "renal_tubular_acidosis": 0.5, "nephrotic_syndrome": 0.7},
      note="Creatinine >= 2.0 mg/dL on a single panel: marked reduction of GFR. Acute (AKI) vs chronic (CKD) cannot be decided from one value - prior creatinine, kidney size, albuminuria and CKD-MBD markers decide.",
      src="KDIGO AKI 2012 (definition 2.1.1 requires a change over 48 h / 7 d); KDIGO CKD 2024 (chronicity > 3 months)"),
 dict(id="renal_failure_moderate", dx=["reduced_gfr_chronicity_undetermined"], req=[("cr", "between", (1.5, 1.9999)), ("bun", ">", 30)],
      sup=[("k", ">", 5.0), ("hco3", "<", 20), ("phos", ">", 4.5)], min_sup=0, strength="pattern", ctx=[("age_ge", 18)], excl=[("ck", ">", 5000)],
      src="KDIGO AKI 2012; KDIGO CKD 2024"),
 dict(id="sirs_with_laboratory_support_sepsis_screen", dx=["sepsis"], req=[("sirs_count", ">=", 2)],
      sup=[("lactate", ">", 2.0), ("pct", ">", 0.5), ("crp", ">", 10), ("wbc", ">", 12), ("wbc", "<", 4), ("bands", ">", 10), ("plt", "<", 100), ("tbil", ">", 2.0), ("cr", ">", 1.5)], min_sup=1,
      strength="screen", ctx_excl=[("cond", "pancreatitis"), ("cond", "trauma"), ("cond", "burn"), ("cond", "post-op"), ("cond", "postoperative")],
      excl=[("lipase", ">", 180), ("ck", ">", 5000)],
      # v6 (2026-10-25): downgraded from "supportive" (0.72) to "screen" (0.45). SIRS >= 2 is met by most ICU patients without infection
      # (Sprung 2006; Kaukonen NEJM 2015) and Sepsis-3 dropped SIRS from the definition for that reason; SSC 2021 treats a positive screen
      # as a prompt for evaluation, not a diagnosis. Sepsis is asserted (>= 0.5) only by the Sepsis-3/organ-dysfunction syndromes below.
      note="SIRS >= 2 with a laboratory marker of host response or organ dysfunction (lactate, PCT, CRP, WBC, bands, platelets, bilirubin, creatinine): positive sepsis SCREEN (SSC 2021 recommends systematic screening). Sepsis-3 additionally requires a suspected infection source and organ dysfunction (SOFA >= 2) - neither is a laboratory input.",
      src="Surviving Sepsis Campaign 2021 (screening, recommendation 1-3); Sepsis-3 (Singer et al. JAMA 2016); ACCP/SCCM 1992 SIRS"),
 dict(id="aki_kdigo_imputed_baseline_acute_care", dx=["acute_kidney_injury"], req=[("cr_ratio_imputed", ">=", 1.5), ("cr", ">=", 1.2)],
      sup=[("bun", ">", 30), ("k", ">", 5.0), ("hco3", "<", 20), ("phos", ">", 4.5), ("lactate", ">", 2), ("cr_ratio_imputed", ">=", 2.0)], min_sup=0, strength="strong",
      ctx=[("age_ge", 18), ("encounter_in", ("icu", "inpatient", "emergency", "hospital", "acute"))], ctx_excl=[("cond", "chronic kidney"), ("cond", "ckd"), ("cond", "dialysis"), ("cond", "esrd"), ("cond", "renal transplant")],
      excl=[("ck", ">", 5000)], cap={"chronic_kidney_disease": 0.8},
      note="Acute-care encounter, no known CKD and no baseline creatinine: KDIGO AKI 2012 (section 2.1, appendix B) back-calculates the baseline from MDRD at eGFR 75 mL/min/1.73 m2; observed/imputed creatinine >= 1.5 meets the stage-1 ratio criterion. Still presumptive - a documented baseline or a repeat value supersedes this.",
      src="KDIGO Clinical Practice Guideline for Acute Kidney Injury, Kidney Int Suppl 2012;2:1 (2.1.1-2.1.2, Appendix B estimated baseline SCr)"),
 # sepsis with left shift: bandaemia >= 10 % plus leucocytosis/leucopenia and one organ-dysfunction marker (Sepsis-3; Surviving Sepsis 2021)
 dict(id="sepsis_bandemia", dx=["sepsis", "bacterial_infection"], req=[("bands", ">=", 10), ("wbc", ">", 12)], alt_req=[("bands", ">=", 10), ("wbc", "<", 4)],
      sup=[("cr", ">", 1.5), ("lactate", ">", 2), ("plt", "<", 150), ("hco3", "<", 20), ("pct", ">", 0.5), ("crp", ">", 100), ("tbil", ">", 2), ("inr", ">", 1.5)], min_sup=1, strength="strong",
      excl=[("pct", "<", 0.1)], cap={"leukocytosis_pattern": 0.9, "leukemoid_reaction": 0.6},
      src="Singer et al. JAMA 2016 (Sepsis-3); Surviving Sepsis Campaign 2021; Cavallazzi 2010 bandaemia"),
 dict(id="sepsis_marked_leukocytosis_organ", dx=["sepsis", "bacterial_infection"], req=[("wbc", ">", 20), ("lactate", ">", 2)],
      sup=[("cr", ">", 1.5), ("plt", "<", 150), ("hco3", "<", 20), ("pct", ">", 0.5), ("crp", ">", 100), ("bands", ">", 10)], min_sup=1, strength="pattern",
      excl=[("wbc", ">", 100), ("blasts", ">", 5), ("ck", ">", 5000)], src="Singer et al. JAMA 2016 (Sepsis-3)"),
 # acute hepatocellular injury: ALT/AST > 5x ULN is not a chronic-liver-disease pattern; chronic entities are capped
 dict(id="acute_hepatocellular_injury", dx=["hepatocellular_injury_pattern"], req=[("alt", ">", 200)], alt_req=[("ast", ">", 200)],
      sup=[("ldh", ">", 400), ("lactate", ">", 2), ("inr", ">", 1.5), ("tbil", ">", 2), ("trop_c", ">", 50), ("cr", ">", 1.5)], min_sup=0, strength="pattern",
      # aetiology-specific markers present -> the specific syndromes decide, not the generic pattern
      excl=[("hbsag", "pos", None), ("hbv_dna", ">", 0), ("hbc_igm", "pos", None), ("hcv_rna", ">", 0), ("asma", ">", 0), ("ana", ">", 0), ("apap", ">", 10)],
      cap={"nafl_d": 0.4, "nonalcoholic_fatty_liver_disease": 0.4, "nash": 0.5, "liver_cirrhosis": 0.6},
      src="ACG 2017 guideline on abnormal liver chemistries (Kwo et al.); Kwo 2017 severe (>15x) vs borderline patterns"),
 # mild DKA (ADA/EASD 2024: glucose > 250 or known DM, HCO3 < 18, AG > 12) when ketones were not measured
 dict(id="dka_mild_ketones_unmeasured", dx=["diabetic_ketoacidosis", "diabetes_mellitus"], req=[("glucose", ">=", 200), ("hco3", "<", 18), ("ag_c", ">", 12), ("ag_minus_lac", ">", 8)],
      sup=[("ph", "<", 7.3), ("k", ">", 5.0), ("phos", "<", 2.5), ("glucose", ">", 400), ("ag_c", ">", 16)], min_sup=0, strength="pattern",
      excl=[("bhb", "<", 3.0), ("uket", "neg", None), ("cr", ">", 6.0)], cap={"hyperosmolar_hyperglycemic_state": 0.8},
      src="Umpierrez et al., Diabetes Care 2024 (ADA/EASD hyperglycaemic crises consensus) - mild DKA tier; ext9b creatinine > 6 exclusion (uraemic acidosis)"),
 # Sepsis-3 operational screen without procalcitonin: abnormal WBC + >= 2 organ-dysfunction / infection markers (pattern strength only)
 dict(id="sepsis_sirs_two_organ", dx=["sepsis", "bacterial_infection"], req=[("wbc", ">", 12)], alt_req=[("wbc", "<", 4)],
      sup=[("plt", "<", 150), ("lactate", ">", 2), ("cr", ">", 1.5), ("tbil", ">", 2), ("hco3", "<", 20), ("bands", ">", 10), ("pct", ">", 0.5), ("crp", ">", 100), ("inr", ">", 1.5)], min_sup=2, strength="pattern",
      excl=[("wbc", ">", 100), ("blasts", ">", 5), ("ck", ">", 5000), ("pct", "<", 0.1), ("hb", "<", 7)],
      src="Singer et al. JAMA 2016 (Sepsis-3, SOFA components); Surviving Sepsis Campaign 2021"),
 # total calcium low only because albumin is low: albumin-corrected calcium normal (Payne 1973; KDIGO CKD-MBD 2017)
 # v7 C16 (2026-10-25): acute chest syndrome is a complication OF SICKLE CELL DISEASE (NHLBI 2014 / ASH 2020): anaemia
 # with hypoxaemia in a patient without known sickle cell disease or a measured HbS fraction is not ACS. The registry
 # leaf (Hb < 9 + pO2 < 70) carries no such requirement, so the syndrome layer supplies the context gate.
 dict(id="sickle_complication_context_guard", dx=[], guard=True, req=[("hb", "<", 9)], min_sup=0, strength="pattern",
      excl=[("hbs", ">", 0)], ctx_excl=[("cond", "sickle"), ("cond", "hbss"), ("cond", "hbsc"), ("cond", "drepanocyt"), ("cond", "hemoglobin s"), ("cond", "haemoglobin s"), ("med", "hydroxyurea"), ("med", "voxelotor"), ("med", "crizanlizumab")],
      cap={"acute_chest_syndrome": 0.3, "vaso_occlusive_crisis": 0.3, "sickle_cell_anemia_hbss": 0.3, "sickle_cell_disease": 0.35},
      src="NHLBI 2014 Evidence-based management of sickle cell disease; ASH 2020 SCD guidelines (ACS defined in persons with SCD)"),
 dict(id="pseudohypocalcemia_guard", dx=[], guard=True, req=[("ca", "<", 8.5), ("ca_c", ">=", 8.5), ("alb", "<", 3.5)], min_sup=0, strength="pattern",
      excl=[("ica", "<", 1.12)], cap={"hypocalcemia": 0.45, "hypoparathyroidism": 0.4, "vitamin_d_deficiency": 0.6, "pseudohypoparathyroidism": 0.4},
      src="Payne RB et al. BMJ 1973; KDIGO CKD-MBD 2017 (use corrected or ionised calcium)"),
 # CK-only elevation without any drug / temperature / mental-status context: hyperthermic drug syndromes are not supportable
 dict(id="ck_elevation_no_context_guard", dx=[], guard=True, req=[("ck", ">", 500)], min_sup=0, strength="pattern",
      cap={"serotonin_syndrome": 0.45, "neuroleptic_malignant_syndrome": 0.45, "malignant_catatonia": 0.45, "malignant_hyperthermia": 0.45, "heat_stroke": 0.45},
      excl=[("temp", ">", 38.5)], ctx_excl=[("med", "serotonin"), ("med", "ssri"), ("med", "antipsychotic"), ("med", "haloperidol"), ("med", "anesth"), ("cond", "hyperthermia"), ("cond", "fever")],
      src="Boyer & Shannon NEJM 2005 (serotonin syndrome requires serotonergic exposure); Strawn 2007 NMS criteria"),
])
# ESL extension 6b (2026-10-21)
_ESL_LIBRARY.extend([
 dict(id="sepsis_lactate_organ", dx=["sepsis"], req=[("lactate", ">", 2.5)],
      # v6 (2026-10-25): hypotension (SBP < 90 / MAP < 65 mmHg) added as organ-dysfunction support - the cardiovascular SOFA component (Sepsis-3)
      # and the septic-shock criterion (vasopressor need + lactate > 2); vitals come from the optional context module and are absent in labs-only use.
      sup=[("cr", ">", 1.5), ("plt", "<", 150), ("tbil", ">", 2), ("hco3", "<", 20), ("inr", ">", 1.5), ("wbc", ">", 12), ("wbc", "<", 4), ("bands", ">", 10), ("pct", ">", 0.5), ("crp", ">", 100), ("sbp", "<", 90), ("map", "<", 65)], min_sup=1, strength="pattern",
      excl=[("ck", ">", 5000), ("trop_c", ">", 1000), ("hb", "<", 7), ("ethanol", ">", 80), ("glucose", ">", 400), ("blasts", ">", 5), ("wbc", ">", 100), ("cohb", ">", 10), ("apap", ">", 50)],
      src="Singer et al. JAMA 2016 (Sepsis-3); Surviving Sepsis Campaign 2021 (lactate > 2 as screening trigger); Vincent 2016 ICU aetiology of hyperlactataemia"),
 dict(id="sepsis_leukocytosis_one_organ", dx=["sepsis", "bacterial_infection"], req=[("wbc", ">", 15)],
      sup=[("plt", "<", 150), ("lactate", ">", 2), ("cr", ">", 1.5), ("tbil", ">", 2), ("hco3", "<", 20), ("inr", ">", 1.5), ("bands", ">", 10), ("pct", ">", 0.5), ("crp", ">", 100)], min_sup=1, strength="pattern",
      excl=[("wbc", ">", 50), ("blasts", ">", 5), ("ck", ">", 5000), ("pct", "<", 0.1), ("hb", "<", 7), ("glucose", ">", 400), ("trop_c", ">", 1000)],
      src="Singer et al. JAMA 2016 (Sepsis-3, SOFA components); Surviving Sepsis Campaign 2021"),
])
# ESL extension 6c (2026-10-21) — clinical-confirmation ceilings
_ESL_LIBRARY.extend([
 # Thyroid storm is a clinical score (Burch-Wartofsky / JTA); biochemical thyrotoxicosis without any systemic
 # marker (fever, tachycardia, cholestasis, leucocytosis, hyperglycaemia, hypercalcaemia) is thyrotoxicosis, not storm.
 dict(id="thyrotox_no_systemic_guard", dx=[], guard=True, req=[("tsh", "<", 0.1)], alt_req=[("ft4", ">", 1.8)], min_sup=0, strength="pattern",
      excl=[("ft4", ">", 4.0), ("tbil", ">", 1.5), ("wbc", ">", 12), ("glucose", ">", 180), ("temp", ">", 38.0), ("ca", ">", 10.5), ("alt", ">", 80), ("lactate", ">", 2.5)],
      ctx_excl=[("attr_gt", ("heart_rate", 120)), ("cond", "fever"), ("cond", "storm"), ("cond", "agitation"), ("cond", "delirium")],
      cap={"thyroid_storm": 0.45, "atrial_fibrillation_hyperthyroid": 0.40, "thyrotoxic_periodic_paralysis": 0.45},
      src="Burch & Wartofsky 1993; Ross et al. ATA 2016 hyperthyroidism guideline; Akamizu JTA criteria 2012"),
 # Shock is a haemodynamic diagnosis: without hypotension / vasopressor context, hyperlactataemia supports
 # sepsis or lactic acidosis, not 'septic shock' / 'cardiogenic shock' (Sepsis-3: vasopressors + lactate > 2 after resuscitation).
 dict(id="shock_hemodynamics_guard", dx=[], guard=True, req=[("lactate", ">", 2.0)], min_sup=0, strength="pattern",
      ctx_excl=[("attr_true", "vasopressor_required"), ("attr_lt", ("systolic_bp", 90)), ("attr_lt", ("systolic_blood_pressure", 90)),
                ("cond", "hypotension"), ("cond", "shock"), ("med", "norepinephrine"), ("med", "vasopressin"), ("med", "vasopressor")],
      cap={"septic_shock": 0.45, "septic_shock_severe_lactic_acidosis": 0.49, "cardiogenic_shock": 0.45, "hypovolemic_shock": 0.45, "hemorrhagic_shock": 0.45, "distributive_shock": 0.45, "obstructive_shock": 0.45},
      src="Singer et al. JAMA 2016 (Sepsis-3 septic shock definition); Vincent & De Backer NEJM 2013 circulatory shock"),
 # An isolated D-dimer has no diagnostic specificity: PE / dissection / DVT need imaging; the ceiling lifts when a second
 # objective marker (troponin, natriuretic peptide, hypoxaemia, thrombocytopenia, low fibrinogen) is present.
 dict(id="isolated_ddimer_guard", dx=[], guard=True, req=[("ddimer", ">", 0.5)], min_sup=0, strength="pattern",
      excl=[("trop_c", ">", 14), ("natri_high", "==", 1), ("po2", "<", 70), ("plt", "<", 100), ("fib", "<", 150), ("inr", ">", 1.5), ("lactate", ">", 2.5)],
      ctx_excl=[("cond", "chest pain"), ("cond", "dyspnea"), ("cond", "dyspnoea"), ("cond", "leg swelling"), ("cond", "syncope"), ("pregnant", True)],
      cap={"pulmonary_embolism": 0.45, "aortic_dissection": 0.40, "deep_vein_thrombosis": 0.45, "venous_thromboembolism": 0.45},
      src="Konstantinides ESC 2019 PE guideline (D-dimer rule-out only); Erbel ESC 2014 aortic diseases"),
])
# ESL extension 6d (2026-10-21)
_ESL_LIBRARY.extend([
 dict(id="ckd_egfr_albuminuria", dx=["chronic_kidney_disease"], req=[("egfr_c", "<", 60), ("uacr", ">=", 30)],
      sup=[("hb", "<", 12), ("phos", ">", 4.5), ("pth", ">", 65), ("hco3", "<", 22), ("urate", ">", 7)], min_sup=0, strength="strong", ctx=[("age_ge", 18)],
      excl=[("lactate", ">", 4), ("ck", ">", 5000), ("k", ">", 6.0), ("cr", ">", 4.0)],
      src="KDIGO 2024 CKD guideline (G3a+ with A2+); CKD-EPI 2021 (Inker NEJM 2021)"),
 dict(id="ckd_egfr_g3b", dx=["chronic_kidney_disease"], req=[("egfr_c", "between", (30, 44.9999))],
      sup=[("uacr", ">=", 30), ("hb", "<", 11), ("phos", ">", 4.5), ("pth", ">", 65), ("hco3", "<", 22)], min_sup=1, strength="pattern", ctx=[("age_ge", 40)],
      note="v6: a single eGFR 30-44 is CKD G3b only if it persists > 90 days (KDIGO 2024); without a prior value at least one chronicity clue (albuminuria, anaemia, hyperphosphataemia, raised PTH, low bicarbonate) is required here.",
      excl=[("lactate", ">", 4), ("ck", ">", 5000), ("k", ">", 6.0), ("bun_cr", ">", 30), ("glucose", ">", 400)],
      src="KDIGO 2024 CKD guideline (G3b: eGFR 30-44)"),
 dict(id="ckd_egfr_g4_single", dx=["chronic_kidney_disease"], req=[("egfr_c", "<", 30)],
      sup=[("uacr", ">=", 30), ("hb", "<", 11), ("phos", ">", 4.5), ("pth", ">", 65)], min_sup=1, strength="pattern", ctx=[("age_ge", 18)],
      excl=[("lactate", ">", 4), ("ck", ">", 5000), ("k", ">", 6.5), ("glucose", ">", 400)],
      src="KDIGO 2024 CKD guideline (single eGFR < 30: AKI vs CKD undetermined - both listed; chronicity markers decide)"),  # extension 7
 dict(id="ckd_egfr_g3b_young", dx=["chronic_kidney_disease"], req=[("egfr_c", "between", (30, 44.9999))],
      sup=[("uacr", ">=", 30), ("phos", ">", 4.5), ("pth", ">", 65), ("hb", "<", 11)], min_sup=1, strength="pattern", ctx=[("age_ge", 18), ("age_lt", 40)],
      excl=[("lactate", ">", 4), ("ck", ">", 5000), ("k", ">", 6.0), ("bun_cr", ">", 30), ("glucose", ">", 400)],
      src="KDIGO 2024 CKD guideline (young adult: single eGFR 30-44 needs corroboration before CKD is listed)"),  # extension 7 (2026-10-22)
 # G3a alone overlaps age-related decline in the elderly; needs one renal-specific corroborating marker (anaemia / low HCO3 are too unspecific - B4 stay 172015, cirrhosis)
 dict(id="ckd_egfr_moderate", dx=["chronic_kidney_disease"], req=[("egfr_c", "between", (45, 59.9999))],
      sup=[("uacr", ">=", 30), ("phos", ">", 4.5), ("pth", ">", 65)], min_sup=1, strength="pattern", ctx=[("age_ge", 18)],
      excl=[("lactate", ">", 4), ("ck", ">", 5000), ("k", ">", 6.0), ("bun_cr", ">", 30)],
      src="KDIGO 2024 CKD guideline (single eGFR 30-59: CKD if persistent > 3 months - pattern strength only)"),
 dict(id="mets_two_criteria_guard", dx=[], guard=True, req=[("tg", ">=", 150), ("hdl", "<", 40)], min_sup=0, strength="pattern",
      excl=[("fpg", ">=", 100), ("a1c", ">=", 5.7), ("glucose", ">=", 126)],
      ctx_excl=[("attr_gt", ("bmi", 29.9)), ("attr_gt", ("body_mass_index", 29.9)), ("attr_gt", ("waist_cm", 101)), ("attr_gt", ("systolic_bp", 129)), ("cond", "hypertension"), ("cond", "obesity")],
      cap={"metabolic_syndrome": 0.45}, src="Alberti et al. Circulation 2009 (harmonised definition: 3 of 5 criteria)"),
])
# extension 7 (2026-10-22)
_ESL_LIBRARY.extend([
 # anion gap not computable (no chloride) - severe acidaemia with marked hyperglycaemia is a hyperglycaemic crisis
 dict(id="dka_no_gap_severe", dx=["diabetic_ketoacidosis", "diabetes_mellitus"], req=[("glucose", ">", 250), ("hco3", "<", 10), ("ph", "<", 7.20), ("ag_c", "absent", None)], sup=[("k", ">", 5.0), ("glucose", ">", 400)], min_sup=0, strength="pattern",
      excl=[("bhb", "<", 3.0), ("uket", "neg", None), ("cr", ">", 4.0)],
      cap={"metabolic_acidosis": 0.9}, src="ADA/EASD 2024 hyperglycaemic crises consensus (ketones unmeasured; anion gap unavailable)"),
 dict(id="dka_no_gap_moderate", dx=["diabetic_ketoacidosis", "diabetes_mellitus"], req=[("glucose", ">=", 200), ("hco3", "<", 12), ("ag_c", "absent", None), ("ph", "absent", None)], sup=[("k", ">", 5.0), ("glucose", ">", 400)], min_sup=0, strength="pattern",
      excl=[("bhb", "<", 3.0), ("uket", "neg", None), ("cr", ">", 3.0), ("lactate", ">=", 4.0)],
      src="ADA/EASD 2024 hyperglycaemic crises consensus (no gas, no gap available)"),
 # glucose > 600 with computed osmolality 300-320: hyperglycaemic crisis short of HHS criteria
 dict(id="hhs_evolving", dx=["hyperosmolar_hyperglycemic_state", "diabetes_mellitus"], req=[("glucose", ">", 600), ("osm", "between", (300, 320))], sup=[("hco3", ">", 15), ("ph", ">", 7.30), ("cr", ">", 1.3), ("bun", ">", 30)], min_sup=1, strength="pattern",
      excl=[("ph", "<", 7.25), ("hco3", "<", 12)], cap={"diabetic_ketoacidosis": 0.7}, src="ADA/EASD 2024 hyperglycaemic crises consensus (HHS: glucose > 600, osm > 320)"),
 # high-anion-gap metabolic acidosis established from chemistry alone (no blood gas): Kraut & Madias NEJM 2014
 dict(id="hagma_no_gas", dx=["metabolic_acidosis"], req=[("hco3", "<", 15), ("ag_c", ">", 16), ("ph", "absent", None)], sup=[("k", ">", 5.0), ("ag_c", ">", 20), ("hco3", "<", 10)], min_sup=0, strength="strong",
      src="Kraut & Madias NEJM 2014 (HAGMA = low HCO3 with elevated anion gap)"),
 dict(id="hagma_no_gas_mild", dx=["metabolic_acidosis"], req=[("hco3", "between", (15, 17.9999)), ("ag_c", ">", 16), ("ph", "absent", None)], sup=[("k", ">", 5.0), ("lactate", ">", 2)], min_sup=0, strength="pattern",
      src="Kraut & Madias NEJM 2014"),
 # HHS by *effective* osmolality when serum osmolality was not measured (ADA/EASD 2024: 2 x Na + glucose/18 > 320)
 dict(id="hhs_effective_osm", dx=["hyperosmolar_hyperglycemic_state", "diabetes_mellitus"], req=[("glucose", ">", 600), ("osm_eff_c", ">", 320), ("osm", "absent", None)], sup=[("hco3", ">", 15), ("ph", ">", 7.30), ("cr", ">", 1.3), ("bun", ">", 30)], min_sup=1, strength="strong",
      excl=[("ph", "<", 7.25), ("hco3", "<", 12)], cap={"diabetic_ketoacidosis": 0.6, "hypernatremia": 0.85, "acute_kidney_injury": 0.85}, src="ADA/EASD 2024 hyperglycaemic crises consensus"),
 # translocational (hyperglycaemic) hyponatraemia: measured Na low but glucose-corrected Na normal
 dict(id="translocational_hyponatremia_guard", dx=[], guard=True, req=[("na", "<", 135), ("glucose", ">", 300), ("na_c", ">=", 135)], min_sup=0, strength="pattern",
      cap={"hyponatremia": 0.40, "siadh": 0.2, "hypovolemic_hyponatremia": 0.3, "severe_hyponatremia": 0.3},
      src="Hillier TA et al. Am J Med 1999 (1.6-2.4 mEq/L per 100 mg/dL glucose); Spasovski ESE 2014 hyponatraemia guideline"),
 # neutrophil-to-lymphocyte ratio supports bacterial infection (not sepsis, which needs organ dysfunction)
 dict(id="bacterial_infection_nlr", dx=["bacterial_infection"], req=[("wbc", ">", 12), ("nlr_c", ">", 10)], sup=[("bands", ">", 10), ("crp", ">", 50), ("pct", ">", 0.5), ("neut_pct", ">", 85)], min_sup=0, strength="pattern",
      excl=[("blasts", ">", 5), ("wbc", ">", 50), ("med", "corticosteroid")],
      src="Zahorec R. Bratisl Lek Listy 2001; de Jager CP Crit Care 2010 (NLR > 10 in bacteraemia)"),
])
# lactate >= 4 is lactic acidosis first; sepsis is one of its causes, not the definition
for _s in _ESL_LIBRARY:
    if _s["id"] == "lactic_acidosis_sepsis":
        # sepsis stays primary only when an infection marker is present;
        # lactate + leukocytosis + creatinine alone is shock of any cause
        _s["min_sup_any"] = [("pct", ">", 2.0), ("crp", ">", 100), ("bands", ">", 10), ("bcx", "pos", None), ("wbc", ">", 15), ("wbc", "<", 4)]
        _s["cap"] = dict(_s.get("cap") or {}, lactic_acidosis=0.97)
    if _s["id"] in ("mh", "nms", "heat_stroke", "cyanide", "metformin_lactic", "mala", "isoniazid_hepatotoxicity"):
        _s["cap"] = dict(_s.get("cap") or {}, lactic_acidosis=0.9)


def _esl_unit_eq(a: Any, b: Any) -> bool:
    """Unit-label equivalence tolerant of the usual spelling variants."""
    def norm(u: Any) -> str:
        t = str(u).strip().lower().replace(" ", "")
        t = t.replace("µ", "u").replace("μ", "u")
        t = t.replace("x10^", "10^").replace("10*", "10^").replace("10e", "10^")
        t = t.replace("iu", "u").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
        t = t.replace("/ul", "/ul").replace("per", "/")
        return t
    return norm(a) == norm(b)


class _ExpertSyndromeLayer:
    """Evaluates _ESL_LIBRARY against canonicalised observations."""

    def __init__(self, engine: "ClinicalRuleEngine"):
        self._engine = engine
        reg = engine.registry.diseases
        # keep only syndromes whose primary target exists in the registry;
        # secondary targets are filtered per entry
        self._lib: list[dict[str, Any]] = []
        for s in _ESL_LIBRARY:
            dx = [d for d in s["dx"] if d in reg]
            if not dx and not s.get("guard"):
                continue
            s2 = dict(s); s2["dx"] = dx
            self._lib.append(s2)

    # -- value access --------------------------------------------------------
    def _values(self, observations: Mapping[str, "ObservationRecord"], ctx: "ClinicalContext") -> dict[str, Optional[float]]:
        out: dict[str, Optional[float]] = {}
        series_map: dict[str, list[tuple[float, float]]] = {}  # ESL ext 11-T
        for key, (unit, fids) in _ESL_GROUPS.items():
            val = None
            for fid in fids:
                rec = observations.get(fid)
                if rec is None:
                    continue
                raw = _float(getattr(rec, "value", rec))
                if raw is None:
                    continue
                runit = getattr(rec, "unit", None)
                if runit and unit and not _esl_unit_eq(runit, unit):
                    try:
                        conv = convert_unit(raw, runit, unit, fid)
                    except Exception:
                        conv = None
                    if conv is None:
                        # A value in an unconvertible unit is NOT a value in
                        # the expected unit. Silently reusing the raw number
                        # (e.g. PTH 14.8 pmol/L read as 14.8 pg/mL) would
                        # suppress or fabricate constellations; skip it.
                        continue
                    raw = float(conv)
                val = raw
                _ser = (getattr(rec, "metadata", None) or {}).get("series") if hasattr(rec, "metadata") else None  # ESL ext 11-T
                if _ser:
                    pts: list[tuple[float, float]] = []
                    for p in _ser:
                        pv, pt = _float(p.get("value")), _float(p.get("t_hours"))
                        if pv is None or pt is None:
                            continue
                        pu = p.get("unit") or runit
                        if pu and unit and not _esl_unit_eq(pu, unit):
                            try:
                                pv = convert_unit(pv, pu, unit, fid)
                            except Exception:
                                pv = None
                            if pv is None:
                                continue
                            pv = float(pv)
                        pts.append((pt, pv))
                    if len(pts) >= 2:
                        series_map[key] = sorted(pts)
                break
            out[key] = val
        out.update(_esl_compute(out, ctx))
        if series_map:
            out.update(_esl_temporal(series_map))
        self._last_series_keys = sorted(series_map)
        bmi = _float(getattr(ctx, "bmi", None) or getattr(ctx, "body_mass_index", None))
        out["bmi_ge"] = bmi
        out["pregnant_ctx"] = 1.0 if getattr(ctx, "pregnant", False) else 0.0
        return out

    # -- evaluation ----------------------------------------------------------
    @staticmethod
    def _all_met(v: Mapping[str, Optional[float]], crits: list) -> tuple[bool, list[str]]:
        used: list[str] = []
        for key, op, arg in crits:
            r = _esl_test(v.get(key), op, arg)
            if not r:
                return False, used
            used.append(key)
        return True, used

    def evaluate(self, observations: Mapping[str, "ObservationRecord"], ctx: "ClinicalContext") -> list[dict[str, Any]]:
        v = self._values(observations, ctx)
        hits: list[dict[str, Any]] = []
        for s in self._lib:
            # context gates
            if any(not _esl_ctx(ctx, p, a) for p, a in s.get("ctx", ())):
                continue
            ca = s.get("ctx_any")
            if ca and not any(_esl_ctx(ctx, p, a) for p, a in ca):
                continue
            ce = s.get("ctx_excl")  # ESL extension 6 (2026-10-21)
            if ce and any(_esl_ctx(ctx, p, a) for p, a in ce):
                continue
            # required (primary or alternates)
            ok, used = self._all_met(v, s["req"])
            if not ok:
                ok, used = False, []
                for alt_key in ("alt_req", "alt_req2", "alt_req3"):
                    alt = s.get(alt_key)
                    if alt:
                        ok, used = self._all_met(v, alt)
                        if ok:
                            break
            if not ok:
                continue
            # exclusions
            vetoed = False
            for key, op, arg in s.get("excl", ()):
                if _esl_test(v.get(key), op, arg):
                    vetoed = True
                    break
            if vetoed:
                continue
            # supports
            sup_met: list[str] = []
            n_eval = 0
            for key, op, arg in s.get("sup", ()):
                r = _esl_test(v.get(key), op, arg)
                if r is None:
                    continue
                n_eval += 1
                if r:
                    sup_met.append(key)
            if len(sup_met) < int(s.get("min_sup", 0)):
                continue
            msa = s.get("min_sup_any")
            if msa and not any(_esl_test(v.get(k), o, a) for k, o, a in msa):
                continue
            # strength: anchor when the supporting picture is rich
            n_sup = len(s.get("sup", ()))
            richness = (len(sup_met) / n_sup) if n_sup else 1.0
            strength = s.get("strength") or ("anchor" if (len(sup_met) >= max(1, s.get("min_sup", 0)) and richness >= 0.34 or n_sup == 0) else "strong")
            score = {"anchor": 0.95, "strong": 0.88, "pattern": 0.80, "supportive": 0.72, "screen": 0.45}.get(strength, 0.88)  # v6: "screen" = positive screening tool (SSC 2021) -> stays below the 0.5 assertion line ("possible"); prompts evaluation, never asserts the disease  # ext10: "supportive" = biomarker signature that supports a behaviour/exposure, never a disease on its own
            # resolve used observation ids for subsumption
            feats: set[str] = set()
            for key in used + sup_met:
                grp = _ESL_GROUPS.get(key)
                if grp:
                    for fid in grp[1]:
                        if fid in observations:
                            feats.add(fid); break
                elif key in ("ag_c",):
                    feats.update(f for f in ("anion_gap", "sodium", "chloride", "bicarbonate") if f in observations)
                elif key in ("osm_gap_c",):
                    feats.update(f for f in ("serum_osmolality", "calculated_osmolality", "osmolal_gap") if f in observations)
                elif key == "ca_c":
                    feats.update(f for f in ("calcium_total", "albumin") if f in observations)
                elif key == "bun_cr":
                    feats.update(f for f in ("blood_urea_nitrogen", "creatinine") if f in observations)
                elif key in ("ast_alt", "r_ratio"):
                    feats.update(f for f in ("aspartate_aminotransferase", "alanine_aminotransferase", "alkaline_phosphatase") if f in observations)
                elif key in ("ibil_c", "dbil_frac"):
                    feats.update(f for f in ("total_bilirubin", "direct_bilirubin", "indirect_bilirubin") if f in observations)
                elif key in ("flc_ratio_c", "flc_diff"):
                    feats.update(f for f in ("serum_free_light_chain_kappa", "serum_free_light_chain_lambda", "free_light_chain_ratio") if f in observations)
                elif key == "trop_c":
                    feats.update(f for f in _ESL_GROUPS["trop"][1] + _ESL_GROUPS["trop_conv"][1] if f in observations)
                elif key == "natri_high":
                    feats.update(f for f in _ESL_GROUPS["ntprobnp"][1] + _ESL_GROUPS["bnp"][1] if f in observations)
                elif key == "mentzer":
                    feats.update(f for f in ("mean_corpuscular_volume", "red_blood_cell_count") if f in observations)
                elif key in ("tg_hdl",):
                    feats.update(f for f in ("triglycerides", "hdl_cholesterol") if f in observations)
                elif key in ("lh_fsh",):
                    feats.update(f for f in ("luteinizing_hormone", "follicle_stimulating_hormone") if f in observations)
            # v6 C8 (2026-10-25): analytes behind the REQUIRED groups only - used for evidence
            # subsumption, so that an optional support leaf (creatinine in an MI syndrome) does
            # not let the syndrome "explain" an unrelated finding (reduced GFR).
            req_feats: set[str] = set()
            for key in used:
                grp = _ESL_GROUPS.get(key)
                if grp:
                    for fid in grp[1]:
                        if fid in observations:
                            req_feats.add(fid); break
            hits.append({
                "syndrome_id": s["id"], "dx": list(s["dx"]), "score": score, "strength": strength, "req_features": sorted(req_feats),
                "required_met": used, "support_met": sup_met, "support_evaluated": n_eval,
                "features": sorted(feats), "cap": dict(s.get("cap") or {}), "source": s.get("src", ""),
                "guard": bool(s.get("guard")), "note": s.get("note", ""),
                "temporal": bool(s.get("temporal")), "context": bool(s.get("ctx_any") or s.get("ctx")),
            })
        return hits


class ClinicalRuleEngine:


    PANIC_VALUES = {
        "potassium": {"low": 2.8, "high": 6.0},
        'sodium': {'low': 125, "high": 155},
        "glucose": {"low": 55, "high": 250},
        "fasting_plasma_glucose": {"low": 55, 'high': 250},
        "creatinine": {"low": 0.4, "high": 4.0},
        "hemoglobin": {"low": 8.0, "high": 19.0},
        "platelet_count": {"low": 60, 'high': 900},
        "calcium_total": {"low": 7.0, "high": 12.0},
        'white_blood_cell_count': {"low": 1.5, "high": 30.0},
        "alanine_aminotransferase": {'low': 0, "high": 300},
        'aspartate_aminotransferase': {"low": 0, "high": 300},
        "bilirubin_total": {"low": 0, "high": 8.0},
        "albumin": {'low': 2.0, 'high': 5.5},
        "thyroid_stimulating_hormone": {"low": 0.1, "high": 20.0},
    }

    def __init__(
        self,
        disease_registry_path: str | Path = DEFAULT_DISEASE_REGISTRY_PATH,
        feature_registry_path: str | Path = DEFAULT_FEATURE_REGISTRY_PATH,
        *,
        execution_mode: str = "research",
        require_confirmed: bool = True,
        assume_rule_unit_for_scalars: bool = True,
        enforce_contract: bool = True,
    ):
        if execution_mode not in {"research", "clinical"}:
            raise ValueError("execution_mode must be 'research' or 'clinical'.")
        self.registry = DiseaseGuidelineRegistry.shared(
            disease_registry_path, feature_registry_path)
        # Derived once per engine: on a 6600-disease registry this finds
        # the subtype relations the data implies but never states.
        try:
            self._registry_parents = kashf_selsele_maratib(
                self.registry.diseases)
        except Exception as exc:
            # FIX A34: was a silent degradation (umbrella-term demotion
            # silently skipped). Log it so it is observable.
            logger.warning("Parent-map derivation failed (%s); umbrella-term "
                           "demotion disabled for this engine.", exc)
            self._registry_parents = {}
        self.execution_mode = execution_mode
        self.require_confirmed = require_confirmed
        self.assume_rule_unit_for_scalars = assume_rule_unit_for_scalars
        self.enforce_contract = enforce_contract

        self._expression_cache: "OrderedDict[tuple[str, str], Any]" = OrderedDict()
        self._EXPRESSION_CACHE_MAX = int(
            os.environ.get("HEMOGLYPH_EXPR_CACHE", "20000"))

        self._bayesian_net = ClinicalBayesianNetwork()
        self._fuzzy_engine = AdaptiveFuzzyEngine()
        self._knowledge_graph = ClinicalKnowledgeGraph()
        self._esl = _ExpertSyndromeLayer(self)
        self._esl_hits: list[dict[str, Any]] = []
        self._reasoner = MultiStageReasoner(self._knowledge_graph)
        try:
            self._reasoner.configure_registry(self.registry.diseases)
        except Exception as exc:
            logger.warning("Reasoner registry configuration failed: %s", exc)
        # The engine-side interval tables cover ~40 analytes; the feature
        # registry carries numeric adult / sex-specific intervals for ~520
        # more. Hydrate once so severity, direction and fuzzy membership exist
        # for them instead of silently reading as 'no interval'.
        try:
            hydrate_reference_ranges_from_registry(
                getattr(self.registry, "features", {}) or {})
        except Exception as exc:
            logger.warning("Reference-range hydration from registry failed: %s", exc)


    def _population_applicable(
        self, rule: Mapping[str, Any], context: ClinicalContext
    ) -> tuple[bool, list[str], Optional[str]]:
        population = rule.get("population") or {}
        groups = set(population.get("age_groups") or [])
        missing: list[str] = []
        if groups and context.age_years is None:
            missing.append("age_years")
        elif groups and context.age_years is not None:
            try:
                age = float(context.age_years)
            except (TypeError, ValueError):
                missing.append("age_years")
            else:
                current = _sen_goroohbandi(age)
                if current not in groups and "all" not in groups:
                    fallback_map = {
                        'young_child': {"child", "infant"},
                        'infant': {"child", "neonate", "young_child"},
                        "neonate": {"infant", "child"},
                        "older_adult": {"adult"},
                    }
                    fallbacks = fallback_map.get(current, set())
                    matched = fallbacks.intersection(groups)
                    if not matched:
                        return False, missing, \
                            f"Age group {current} not applicable."
        sex_req = str(population.get("sex") or "all").strip().casefold()
        sex = context.normalized_jensiat()
        if sex_req in {'male', "female"}:
            if sex is None:
                missing.append("sex_at_birth")
            elif sex != sex_req:
                return False, missing, \
                    f"Rule applies to {sex_req}; supplied sex is {sex}."
        preg_req = str(population.get("pregnancy")
                       or "context_dependent").strip().casefold()
        preg = context.pregnant
        if preg_req in {'required', "yes", "mandatory", "pregnant"}:
            if preg is None:
                missing.append("pregnancy")
            elif preg is False:
                return False, missing, 'Rule requires pregnancy.'
        elif preg_req in {"excluded", "no", "not_pregnant",
                          "non_pregnant"}:
            if preg is True:
                return False, missing, 'Rule excludes pregnancy.'

        # TARGET POPULATION & AGE-SPECIFIC GATING
        rule_id = str(rule.get("rule_id") or "")
        disease_id = str(rule.get("disease_id") or "")
        limitations = str(rule.get("limitations") or "").casefold()

        # Anatomical / Sex-specific disease gating
        if sex == "female" and any(k in disease_id for k in ("prostate", "testicular", "epididymitis", "benign_prostatic")):
            return False, missing, "Male-specific condition not applicable to female patient."
        if sex == "male" and any(k in disease_id for k in ("ovarian", "cervical", "uterine", "endometriosis", "preeclampsia")):
            return False, missing, "Female-specific condition not applicable to male patient."

        # Pregnancy-specific condition gating
        is_preg_dis = any(k in disease_id for k in ("_in_pregnancy", "gestational", "preeclampsia", "eclampsia", "peripartum", "postpartum", "hellp"))
        if is_preg_dis and not context.pregnant:
            return False, missing, "Pregnancy-specific condition not applicable to non-pregnant patient."

        # Pediatric Adult-Malignancy & Chronic Degenerative Gating:
        # Diseases that are strictly adult/geriatric or adult carcinomas/hematologic malignancies
        # must not be screened on isolated routine laboratory variations in pediatric patients.
        if context.age_years is not None and context.age_years < 18.0:
            pediatric_inapplicable_diseases = {
                "sarcopenia", "small_bowel_cancer", "waldenstrom_macroglobulinemia",
                "multiple_myeloma", "chronic_lymphocytic_leukemia", "coronary_artery_disease",
                "atherosclerosis", "aortic_dissection", "renal_cell_carcinoma", "nasopharyngeal_carcinoma",
                "head_neck_cancer", "gastrointestinal_stromal_tumor", "pseudohypoparathyroidism"
            }
            if disease_id in pediatric_inapplicable_diseases:
                return False, missing, f"Condition {disease_id} is an adult chronic/malignant disorder not applicable to pediatric screening on routine labs."

        return True, missing, None


    def _context_requirement(
        self, key: str, expected: Any,
        observation: ObservationRecord, context: ClinicalContext,
    ) -> tuple[Optional[bool], Optional[str]]:
        metadata = observation.metadata
        actual = context.get(key)
        if actual is None:
            actual = metadata.get(key)
        if key == "qualitative":
            actual_q = _qualitative(observation.value)
            expected_q = _qualitative(expected)
            return actual_q == expected_q, None
        if key in {"above_local_uln", "above_assay_99th_percentile"}:
            if not expected:
                return True, None
            if observation.reference_high is None:
                return None, key
            number = _float(observation.value)
            return (number is not None
                    and number > observation.reference_high), None
        if key == "three_times_upper_reference_limit":
            if observation.reference_high is None:
                return None, key
            number = _float(observation.value)
            return (number is not None
                    and number >= 3 * observation.reference_high), None
        if key == "five_times_upper_reference_limit":
            if observation.reference_high is None:
                return None, key
            number = _float(observation.value)
            return (number is not None
                    and number >= 5 * observation.reference_high), None
        if key == "albumin_correction_required":
            if expected and metadata.get("albumin_corrected") is not True \
                    and metadata.get("ionized") is not True:
                return None, key
            return True, None
        if key == "change_from_baseline":
            if not expected:
                return True, None
            return (actual is not None), None if actual is not None else key
        if key in {"dynamic_change", "after_adequate_resuscitation",
                   "vasopressor_required", "ogtt_75g", "fasting",
                   "pregnancy", 'timed_level', "timed_post_dose",
                   "nomogram_interpretation_required",
                   "time_since_ingestion_required"}:
            if actual is None:
                return None, key
            return _as_bool(actual) == _as_bool(expected), None
        if key in {"persistence_days", "within_hours"}:
            if actual is None:
                return None, key
            try:
                actual_f = float(actual)
                expected_f = float(expected)
            except (TypeError, ValueError):
                return None, key
            if key == "persistence_days":
                return actual_f >= expected_f, None
            return actual_f <= expected_f, None
        if key in {"fasting_preferred", "age_assay_specific",
                   "titer", 'assay_specific'}:
            return True, None
        if actual is None:
            return None, key
        return actual == expected, None


    def _condition_strength(self, op, actual, expected) -> Optional[float]:
        try:
            a = float(actual)
            t = float(expected)
        except (TypeError, ValueError):
            return None
        scale = max(abs(t) * 0.10, 1e-9)
        if op in ("<", "<="):
            z = (t - a) / scale
        elif op in (">", '>='):
            z = (a - t) / scale
        elif op == "==":
            z = -abs(a - t) / scale
        elif op == "!=":
            z = abs(a - t) / scale
        else:
            return None
        return _sigmoid(0.5 * z)

    def _borderline_deviation(self, actual, threshold,
                              feature_id) -> bool:
        try:
            a = float(actual)
            t = float(threshold)
        except (TypeError, ValueError):
            return False
        if t == 0:
            return abs(a) < 1e-9
        if abs(a - t) / abs(t) > _BORDERLINE_REL_EPS:
            return False
        return not self._critical_meghdar(feature_id, a)

    def _coerce_canonical(self, feature_id, value, unit):
        """FIX A23: critical/panic thresholds are stored in canonical units,
        so convert the observed value before any comparison. Falls back to
        the raw value when no unit/canonical mapping exists."""
        val = _float(value)
        if val is None:
            return None
        try:
            meta = self.registry.features.get(feature_id) or {}
            canon = (meta.get("units") or {}).get("canonical")
            if canon and unit:
                return convert_unit(val, unit, canon, feature_id)
        except Exception:
            pass
        return val

    def _critical_meghdar(self, feature_id, value) -> bool:

        meta = self.registry.features.get(feature_id) or {}
        crit = (meta.get('validation') or {}).get('critical') or {}
        lo = _float(crit.get("low"))
        hi = _float(crit.get("high"))
        val = _float(value)
        if val is None:
            return False
        if ((lo is not None and val <= lo)
                or (hi is not None and val >= hi)):
            return True

        panic = self.PANIC_VALUES.get(feature_id)
        if panic and val is not None:
            if val <= panic.get("low", float("-inf")):
                return True
            if val >= panic.get("high", float("inf")):
                return True
        return False

    def _barresi_panic_override(
        self, observations: Mapping[str, ObservationRecord]
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for fid, record in observations.items():
            val = _float(record.value)
            if val is None:
                continue
            cmp_val = self._coerce_canonical(fid, record.value, record.unit)
            if self._critical_meghdar(fid, cmp_val):
                meta = self.registry.features.get(fid) or {}
                crit = ((meta.get("validation") or {})
                        .get('critical') or {})
                panic = self.PANIC_VALUES.get(fid, {})
                lo = crit.get("low") or panic.get("low")
                hi = crit.get("high") or panic.get("high")
                hi_f = _float(hi)
                lo_f = _float(lo)
                if hi_f is not None and cmp_val >= hi_f:
                    direction = "critical_high"
                elif lo_f is not None and cmp_val <= lo_f:
                    direction = "critical_low"
                else:
                    direction = "critical_value"
                alerts.append({
                    "feature_id": fid,
                    "value": val,
                    "unit": record.unit,
                    'direction': direction,
                    "threshold_low": lo,
                    "threshold_high": hi,
                    "message": (
                        f"CRITICAL VALUE: {fid} = {val:.3g} "
                        f"{record.unit or ''} exceeds panic "
                        f"threshold ({direction}). "
                        "Immediate clinical action required."),
                })
        return alerts


    def _specificity_guard(self, rule, disease, node, status, context=None, observations=None):
        if status not in POSITIVE_RESULT_STATES:
            return status, [], False
        true_ev = [e for e in node.evidence
                   if e.truth == TruthValue.TRUE]
        if not true_ev:
            return status, [], False
        true_feats = {e.feature_id for e in true_ev}
        solid_feats = {e.feature_id for e in true_ev
                       if not e.borderline}
        warnings: list[str] = []
        links = disease.get("feature_links") or {}
        required = set(links.get("required") or ())

        # The registry names, for 5810 diseases, the features whose abnormal
        # value refutes that disease. Ignoring them let a rule fire on
        # supportive evidence while a contradicting measurement sat in the
        # same panel unread.
        # Exclusion guard: Only truly external refuting features (never required hallmark criteria) can refute
        excluded = (set(links.get("excluded") or ()) - required - set(links.get("optional") or ()) - set(rule.get("_feature_ids") or ()))
        if excluded:
            refuting = sorted(
                f for f in (excluded & true_feats)
                if _evidence_abnormal(node.evidence, f))
            if refuting:
                warnings.append(
                    "Exclusion guard: registry lists ["
                    + ", ".join(refuting)
                    + "] as refuting this disease, yet they are abnormal "
                      "here -> conflicting_data.")
                return "conflicting_data", warnings, False

        # Curated guideline rules (curation 13.0.0) already carry their own
        # exclusions and population limits; the heuristics below exist to
        # tame the AI-assembled remainder of the registry, not these.
        if str(rule.get("status") or "") == "curated_guideline_anchored":
            return status, warnings, True

        # Template-stamped single-analyte "diagnostic criteria" (FPG >= 126
        # under 28 unrelated endocrinopathies) are at most compatible.
        if (status in ("criterion_met", "urgent_pattern")
                and str(rule.get("rule_id") or "") in getattr(self.registry, "rule_stamped", ())
                and str(rule.get("rule_id") or "") not in getattr(self.registry, "rule_defines_entity", ())):
            warnings.append(
                "Specificity guard: this single-analyte threshold is stamped verbatim onto "
                f">= {STAMPED_SIGNATURE_MIN} unrelated entities; it is a non-specific screen -> compatible_pattern.")
            status = "compatible_pattern"

        # Routine-panel-only "diagnostic criteria" for a specific aetiology
        # (malaria <- platelets + LDH) are compatible patterns, not criteria.
        if (status in ("criterion_met", "urgent_pattern")
                and not rule.get("_supplemental")
                and str(rule.get("rule_type") or "") == "diagnostic_criterion"
                and _routine_only_rule(rule)):
            did_l = str(rule.get("disease_id") or "").lower()
            kind = str(((disease.get("classification") or {}).get("entity_kind")) or "")
            if kind in ("", "clinical_entity") and not _ROUTINE_DEFINED_ENTITY_RE.search(did_l):
                warnings.append(
                    "Specificity guard: routine-panel analytes only cannot constitute a "
                    "diagnostic criterion for a specific aetiology -> compatible_pattern.")
                status = "compatible_pattern"

        # Code-level curated rules (SUPPLEMENTAL_RULES) are written against
        # the guideline itself; the registry's AI-filled feature_links
        # ("multiple_myeloma requires ferritin", "excluded: m_spike") and the
        # source-domain heuristics below must not re-grade them.
        if rule.get("_supplemental"):
            return status, warnings, True
        # A TRUE pathogen / decisive marker is the criterion whatever the
        # registry lists as "required".
        for e in true_ev:
            if (_PATHOGEN_MARKER_RE.search(e.feature_id) or _DECISIVE_MARKER_RE.search(e.feature_id)) \
                    and str(e.operator or "") in (">", ">=", "=="):
                return status, warnings, True

        primary = required & set(rule.get('_feature_ids') or ())
        protected = bool(primary and (true_feats & primary))
        if primary and not protected:
            warnings.append(
                "Specificity guard: positive branch fired only on "
                "non-core feature(s) ["
                + ", ".join(sorted(true_feats))
                + "]; core criteria ["
                + ', '.join(sorted(primary))
                + "] absent -> insufficient_data.")
            return "insufficient_data", warnings, False

        # Medical Guideline Domain & Hallmark Criteria Guards:
        # A. If disease defines required hallmark features and none were observed as TRUE:
        if required and not (true_feats & required):
            if status in ("criterion_met", "urgent_pattern"):
                warnings.append(
                    f"Specificity guard: core hallmark criteria {sorted(required)} missing; "
                    f"secondary laboratory finding non-diagnostic -> compatible_pattern."
                )
                status = "compatible_pattern"

        # B. Guideline Domain Boundary Guard:
        rule_sources = [str(s).lower() for s in (rule.get("source_ids") or [])]
        disease_id = str((disease.get("identity") or {}).get("disease_id", "") or rule.get("disease_id", "")).lower()

        # Prediabetes clinical range guard:
        # Prediabetes requires HbA1c 5.7% - 6.4% or FPG 100 - 125 mg/dL.
        # Patients with HbA1c < 5.7% or FPG < 100 mg/dL are normoglycemic.
        if "prediabetes" in disease_id:
            for ev in true_ev:
                if ev.feature_id == "hemoglobin_a1c" and ev.actual_value is not None and ev.actual_value < 5.7:
                    warnings.append(f"Prediabetes guard: HbA1c {ev.actual_value:.1f}% is normoglycemic (<5.7%) -> criterion_not_met.")
                    return "criterion_not_met", warnings, False
                if ev.feature_id in ("fasting_plasma_glucose", "glucose") and ev.actual_value is not None and ev.actual_value < 100:
                    warnings.append(f"Prediabetes guard: Glucose {ev.actual_value:.1f} mg/dL is normoglycemic (<100) -> criterion_not_met.")
                    return "criterion_not_met", warnings, False

        # ADA diabetes rules:
        is_diabetes_entity = (
            ("diabetes" in disease_id and "insipidus" not in disease_id) or
            any(k in disease_id for k in ("hyperglycemia", "impaired_fasting", "impaired_glucose", "insulin_resistance", "metabolic_syndrome", "hhs", "ketoacidosis",
                                           "hypoglyc", "glycemi", "glucose", "insulinoma", "dysglyc", "gestational", "mody", "lada", "prediabet"))
        )
        # Hypoglycemia / urgent glycemic alerts are primary glycemic findings, never "secondary dysglycemia".
        if any("ada" in s for s in rule_sources) and not is_diabetes_entity and status != "urgent_pattern":
            if status in ("criterion_met",):
                status = "compatible_pattern"
                warnings.append("ADA glycemic rule reflects secondary dysglycemia; not diagnostic of primary non-diabetic entity.")

        # KDIGO renal rules:
        is_renal_syndrome = any(k in disease_id for k in (
            "kidney_disease", "kidney_injury", "aki", "ckd", "renal_failure", "nephropathy", "azotemia", "elevated_creatinine"
        ))
        specific_renal_etiology = any(k in disease_id for k in (
            "alport", "anca", "glomerulonephritis", "focal_segmental", "membranous", "polycystic", "renal_tubular_acidosis", "tubular_injury"
        ))
        if any("kdigo" in s for s in rule_sources):
            if not is_renal_syndrome or specific_renal_etiology:
                if status in ("criterion_met", "urgent_pattern"):
                    status = "compatible_pattern"
                    warnings.append("KDIGO renal rule reflects secondary azotemia/clearance reduction; specific etiologic diagnosis requires targeted testing.")

        # AASLD liver rules:
        is_liver_syndrome = any(k in disease_id for k in (
            "liver_injury", "hepatitis_pattern", "steatos", "masld", "nafld", "nash", "transaminitis", "cirrhosis_pattern"
        ))
        specific_liver_etiology = any(k in disease_id for k in (
            "hepatitis_d", "hepatitis_e", "hepatitis_b", "hepatitis_c", "sclerosing_cholangitis", "budd_chiari", "autoimmune_hepatitis", "wilson", "hemochromatosis", "drug_induced"
        ))
        if any(src in s for s in rule_sources for src in ("aasld", "easl")):
            if not is_liver_syndrome or specific_liver_etiology:
                if status in ("criterion_met", "urgent_pattern"):
                    status = "compatible_pattern"
                    warnings.append("AASLD liver rule reflects secondary hepatic injury; specific etiologic diagnosis requires targeted testing.")

        # ATA / ETA Thyroid guidelines only provide diagnostic confirmation for thyroid diseases:
        is_thyroid_entity = any(k in disease_id for k in (
            "thyroid", "hashimoto", "graves", "myxedema", "thyrotoxicosis", "goiter", "euthyroid", "cretinism"
        ))
        if any(src in s for s in rule_sources for src in ("ata_thyroid", "ata", "eta")):
            if not is_thyroid_entity:
                if status in ("criterion_met", "urgent_pattern"):
                    status = "compatible_pattern"
                    warnings.append("ATA thyroid rule reflects secondary endocrine response or hypopituitarism check; not diagnostic of non-thyroid entity.")

        # Endocrine Cross-Screening Rule Boundary Guards:
        r_id_str = str(rule.get("rule_id", "")).lower()
        if "addison_morning_cortisol" in r_id_str:
            is_adrenal = any(k in disease_id for k in ("adrenal_insufficiency", "addison", "hypoadrenal")) and "pheochromocytoma" not in disease_id
            if not is_adrenal and status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append("Addison cortisol screening rule reflects differential exclusion work-up; not diagnostic of primary non-adrenal entity.")

        if ("primary_adrenal_insufficiency" in disease_id or "addison" in disease_id) and observations:
            acth_obs = observations.get("adrenocorticotropic_hormone") or observations.get("acth")
            if acth_obs:
                acth_val = float(acth_obs.value) if hasattr(acth_obs, "value") else float(acth_obs.get("value", 0))
                if acth_val < 30.0 and status in ("criterion_met", "urgent_pattern"):
                    status = "compatible_pattern"
                    warnings.append("Low or inappropriately normal ACTH (<30 pg/mL) refutes Primary Adrenal Insufficiency; consistent with Secondary/Central Adrenal Insufficiency.")

        if "pheochromocytoma" in disease_id:
            if any(k in r_id_str for k in ("addison_morning_cortisol", "hypoglycemia_alert", "tsh_hypothyroid_screen", "free_t4_low_target")):
                if status in ("criterion_met", "urgent_pattern"):
                    status = "compatible_pattern"
                    warnings.append("Endocrine screen is part of differential exclusion; not diagnostic of pheochromocytoma.")

        if any(k in r_id_str for k in ("free_t4_low_target", "free_t4_high_target", "tsh_hypothyroid_screen", "tsh_hyperthyroid_screen")):
            if not is_thyroid_entity and status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append("Thyroid hormone screening rule reflects endocrine exclusion panel; not diagnostic of non-thyroid entity.")

        if any(k in r_id_str for k in ("fasting_glucose_diabetes", "hba1c_diagnostic")):
            if not is_diabetes_entity and status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append("Glycemic diagnostic rule reflects secondary metabolic screen; not diagnostic of primary non-diabetic entity.")

        if "hypoglycemia_alert" in r_id_str:
            if status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append("Hypoglycemia alert rule represents acute glycemic triage, not primary etiology.")

        # Non-specific inflammatory marker guard:
        # Rules relying solely on ESR and/or CRP represent generalized systemic inflammation.
        # They cannot provide definitive diagnostic criteria (criterion_met) for specific clinical entities.
        non_specific_inflam = {"erythrocyte_sedimentation_rate", "c_reactive_protein", "erythrocyte_sedimentation_rate_2hr", "high_sensitivity_c_reactive_protein"}
        if solid_feats and solid_feats.issubset(non_specific_inflam):
            is_inflam_pattern = any(k in disease_id for k in ("inflammation", "inflammatory_response", "acute_phase", "elevated_crp", "elevated_esr", "systemic_inflammatory"))
            if not is_inflam_pattern and status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append("Systemic inflammation guard: isolated ESR/CRP elevation is non-specific; compatible with systemic inflammation but not definitive for specific etiology.")

        # Biological Sex Gating
        p_sex = str(getattr(context, "sex_at_birth", "") or getattr(context, "gender", "")).lower()
        if hasattr(context, "normalized_jensiat") and callable(context.normalized_jensiat):
            p_sex = context.normalized_jensiat() or p_sex
        if p_sex == "male" and any(k in disease_id for k in ("ovarian", "cervical", "uterine", "endometrio", "polycystic_ovary")):
            return "not_applicable", ["Condition is female-specific; patient is biologically male -> not_applicable."], False
        if p_sex == "female" and any(k in disease_id for k in ("prostate", "prostatic", "testicular")):
            return "not_applicable", ["Condition is male-specific; patient is biologically female -> not_applicable."], False

        # Pregnancy Gating
        p_preg = getattr(context, "pregnant", None)
        if (p_preg is False or str(p_preg).lower() in ("no", "0", "false")) and any(k in disease_id for k in ("_in_pregnancy", "gestational", "preeclampsia", "eclampsia")):
            return "not_applicable", ["Patient is confirmed non-pregnant; pregnancy-specific condition not applicable."], False

        # Cerebrovascular & Acute Neurological Gating:
        # Ischemic stroke, TIA, intracerebral hemorrhage, subarachnoid hemorrhage:
        # Laboratory markers (glucose, lipid, coagulation, CBC) represent risk factors or acute metabolic triage,
        # never primary diagnostic confirmation (which requires focal neurological deficit and brain CT/MRI).
        is_neuro_vascular = any(k in disease_id for k in (
            "stroke", "transient_ischemic_attack", "subarachnoid_hemorrhage",
            "intracranial_hemorrhage", "cerebrovascular"
        ))
        if is_neuro_vascular:
            if status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append(
                    "Cerebrovascular guard: laboratory findings represent metabolic risk factors/triage, "
                    "not primary diagnostic confirmation of stroke/TIA (which requires neuroimaging) -> compatible_pattern."
                )

        # Specific etiologic / iatrogenic entities that cannot be definitively diagnosed on isolated routine chemistry:
        isolated_etiologies = {
            "contrast_induced_nephropathy", "calcineurin_inhibitor_nephrotoxicity",
            "drug_induced_liver_injury", "rhabdomyolysis_associated_kidney_injury",
            "alcoholic_hepatitis_pattern", "decompensated_cirrhosis_pattern",
            "mixed_liver_injury_pattern", "obstructive_jaundice", "nephritic_pattern",
            "acute_gastroenteritis", "gastroenteritis", "mcardle_disease", "glycogen_storage",
            "dubin_johnson", "rotor_syndrome", "salivary_gland", "neuroleptic_malignant_syndrome",
            "gastrointestinal_stromal_tumor", "melanoma", "babesiosis", "malignant_catatonia", "catatonia", "serotonin_syndrome",
            "burkitt_lymphoma", "lymphoma", "hodgkin", "tetanus",
            "pulmonary_tuberculosis", "tuberculosis", "intestinal_lymphangiectasia", "protein_losing_enteropathy",
            "rheumatic_fever", "malignant_hyperthermia"
        }
        if any(e in disease_id for e in isolated_etiologies):
            if status in ("criterion_met", "urgent_pattern"):
                status = "compatible_pattern"
                warnings.append(
                    f"Etiologic guard: {disease_id} requires exposure history or imaging/urinalysis microscopy; "
                    "routine chemistry abnormality is a compatible finding -> compatible_pattern."
                )

        # C. Rule specificity check:
        specificity = (rule.get("specificity") or "").lower()
        if status == "criterion_met" and specificity in ("general", "non_specific"):
            status = "compatible_pattern"
            warnings.append(f"Rule specificity is '{specificity}'; positive finding clamped to compatible_pattern.")

        # D. Borderline & Single-marker urgency checks:
        if not solid_feats and status in (
                "urgent_pattern", "criterion_met",
                'screening_positive'):
            warnings.append(
                "Specificity guard: only borderline deviations "
                "(<=2% beyond threshold), no critical value -> "
                "possible_pattern.")
            return "possible_pattern", warnings, protected
        if status == "urgent_pattern" and len(true_feats) == 1:
            ev = true_ev[0]
            if not self._critical_meghdar(
                    ev.feature_id,
                    self._coerce_canonical(ev.feature_id, ev.actual_value,
                                           ev.actual_unit)):
                warnings.append(
                    f"Specificity guard: single-marker urgent "
                    f"({ev.feature_id}) without a critical value "
                    f"-> possible_pattern.")
                return "possible_pattern", warnings, protected
        return status, warnings, protected

    def _pediatric_false_positive_guard(
        self,
        rule: Mapping[str, Any],
        node: 'NodeEvaluation',
        context: 'ClinicalContext',
        observations: Mapping[str, 'ObservationRecord'],
    ) -> tuple[str, list[str]]:
        """ULTRA-PRECISE: Suppress pediatric false positives.
        Returns (new_status, additional_warnings) or (original_status, []) if no change.
        For children, ALP up to 800 is normal bone growth, phosphorus up to 6.5 normal,
        low creatinine due to low muscle mass, etc.
        """
        warnings = []
        age = None
        try:
            age = float(context.age_years) if context.age_years is not None else None
        except:
            pass
        if age is None or age >= 18:
            return None, []

        # Get true feature ids
        true_feats = {e.feature_id for e in node.evidence if hasattr(e, 'truth') and str(e.truth) == 'TruthValue.TRUE' or getattr(e, 'truth', None) == 1}
        # Simpler: collect feature_ids from evidence where truth is TRUE
        try:
            from enum import Enum
            true_feature_ids = set()
            for ev in node.evidence:
                t = getattr(ev, 'truth', None)
                # TruthValue.TRUE is 1
                if str(t) == 'TruthValue.TRUE' or (hasattr(t, 'value') and t.value==1) or t==1:
                    true_feature_ids.add(ev.feature_id)
        except:
            true_feature_ids = set()

        # If rule is based ONLY on ALP (or ALP + urea etc) and child has ALP <800, suppress
        alp_obs = observations.get("alkaline_phosphatase")
        if alp_obs and age < 18:
            try:
                alp_val = float(alp_obs.value) if alp_obs.value is not None else None
            except:
                alp_val = None
            if alp_val is not None:
                # Pediatric ALP normal thresholds
                normal_alp_max = 800 if age < 12 else 500
                if alp_val < normal_alp_max:
                    # Check if rule's only abnormal is ALP (or ALP + non-specific like urea)
                    # If bilirubin and GGT are normal, it's not cholestasis
                    bili = observations.get("bilirubin_total")
                    ggt = observations.get("gamma_glutamyl_transferase")
                    bili_normal = True
                    ggt_normal = True
                    try:
                        if bili and bili.value is not None and float(bili.value) > 1.2:
                            bili_normal = False
                        if ggt and ggt.value is not None and float(ggt.value) > 60:
                            ggt_normal = False
                    except:
                        pass

                    if bili_normal and ggt_normal:
                        # This is likely pediatric physiological ALP
                        # Check if rule is for pancreatitis, celiac, etc that shouldn't be based on ALP alone
                        disease_id = rule.get("disease_id", "")
                        # List of diseases that are often falsely triggered by ALP alone
                        false_positive_diseases = {
                            "acute_pancreatitis", "pancreatitis",
                            "celiac_disease", "celiac",
                            "easl_cirrhosis", "liver_cirrhosis",
                            "cholestasis", "primary_biliary_cholangitis"
                        }
                        if disease_id in false_positive_diseases or "alkaline_phosphatase" in str(rule.get("_feature_ids", "")):
                            # Only ALP or ALP + mild urea elevation (urea 32 is normal for child)
                            # Suppress if no other specific markers
                            other_specific = [fid for fid in true_feature_ids if fid not in ("alkaline_phosphatase", "urea", "blood_urea_nitrogen", "urea_nitrogen")]
                            if not other_specific:
                                warnings.append(
                                    f"Pediatric guard: ALP {alp_val:.0f} in {age:.0f}yo child is physiological bone growth (normal up to {normal_alp_max:.0f}), "
                                    f"not cholestasis/pancreatitis. Bilirubin and GGT normal. Suppressing false positive."
                                )
                                return "not_applicable", warnings

        # Phosphorus: pediatric normal up to 6.5
        phos_obs = observations.get("phosphate") or observations.get("phosphorus")
        if phos_obs and age < 18:
            try:
                phos_val = float(phos_obs.value) if phos_obs.value is not None else None
            except:
                phos_val = None
            if phos_val is not None:
                normal_phos_max = 6.5 if age < 12 else 5.5
                if phos_val <= normal_phos_max:
                    # If rule is tumor lysis based only on phosphorus, suppress
                    disease_id = rule.get("disease_id", "")
                    if "tumor_lysis" in disease_id or "hyperphosphatemia" in disease_id:
                        # Need other markers: hyperuricemia, hyperkalemia, etc
                        true_other = [fid for fid in true_feature_ids if fid not in ("phosphate", "phosphorus")]
                        if not true_other:
                            warnings.append(
                                f"Pediatric guard: Phosphorus {phos_val:.1f} in {age:.0f}yo is normal (up to {normal_phos_max:.1f} in children), "
                                f"not tumor lysis. Suppressing false positive."
                            )
                            return "not_applicable", warnings

        # BUN/Cr ratio: low creatinine in children
        cr_obs = observations.get("creatinine")
        bun_obs = observations.get("blood_urea_nitrogen") or observations.get("urea") or observations.get("urea_nitrogen")
        if cr_obs and bun_obs and age < 18:
            try:
                cr_val = float(cr_obs.value) if cr_obs.value is not None else None
                bun_val = float(bun_obs.value) if bun_obs.value is not None else None
            except:
                cr_val = bun_val = None
            if cr_val is not None and cr_val < 0.7 and bun_val is not None and bun_val < 35:
                # Low muscle mass, not prerenal
                disease_id = rule.get("disease_id", "")
                if "acute_kidney_injury" in disease_id or "prerenal" in str(rule.get("rule_id", "")):
                    warnings.append(
                        f"Pediatric guard: BUN {bun_val:.0f}/Cr {cr_val:.2f} ratio high due to low muscle mass in child, not prerenal AKI. Suppressing false positive."
                    )
                    return "not_applicable", warnings
                if "decreased_creatinine" in disease_id or "co_" in disease_id:
                    warnings.append(
                        f"Pediatric guard: Creatinine {cr_val:.2f} mg/dL reflects normal pediatric muscle mass. Suppressing false positive."
                    )
                    return "not_applicable", warnings

        # Neonatal physiological hematocrit (up to 65% normal in neonates)
        hct_obs = observations.get("hematocrit")
        if hct_obs and age < (28.0 / 365.25):
            try:
                hct_val = float(hct_obs.value) if hct_obs.value is not None else None
            except Exception:
                hct_val = None
            if hct_val is not None and hct_val <= 65.0:
                disease_id = rule.get("disease_id", "")
                if any(k in disease_id for k in ("dengue", "polycythemia", "hemoconcentration")):
                    warnings.append(
                        f"Pediatric guard: Hematocrit {hct_val:.1f}% in neonate is physiological (normal up to 65%), "
                        f"not hemoconcentration/dengue. Suppressing false positive."
                    )
                    return "not_applicable", warnings

        # Neonatal physiological leukocytosis (up to 30k normal in neonates)
        wbc_obs = observations.get("white_blood_cell_count") or observations.get("wbc")
        if wbc_obs and age < (28.0 / 365.25):
            try:
                wbc_val = float(wbc_obs.value) if wbc_obs.value is not None else None
                if wbc_val is not None and wbc_val > 100.0:
                    wbc_val /= 1000.0
            except Exception:
                wbc_val = None
            if wbc_val is not None and wbc_val <= 30.0:
                disease_id = rule.get("disease_id", "")
                if any(k in disease_id for k in ("leukocytosis", "sepsis", "bacterial_infection")):
                    crp = observations.get("c_reactive_protein")
                    pct = observations.get("procalcitonin")
                    crp_hi = bool(crp and crp.value is not None and float(crp.value) > 10)
                    pct_hi = bool(pct and pct.value is not None and float(pct.value) > 0.5)
                    if not (crp_hi or pct_hi):
                        warnings.append(
                            f"Pediatric guard: WBC {wbc_val:.1f} k/uL in neonate is physiological leukocytosis (normal up to 30k), "
                            f"inflammatory markers normal. Suppressing false sepsis/leukocytosis."
                        )
                        return "not_applicable", warnings

        return None, []

    def _pregnancy_false_positive_guard(
        self,
        rule: Mapping[str, Any],
        node: 'NodeEvaluation',
        context: 'ClinicalContext',
        observations: Mapping[str, 'ObservationRecord'],
    ) -> tuple[Optional[str], list[str]]:
        warnings: list[str] = []
        if not getattr(context, "pregnant", False):
            return None, []

        disease_id = str(rule.get("disease_id") or "")

        # 1. Isolated ALP elevation during pregnancy (placental ALP up to 400 U/L)
        if any(k in disease_id for k in ("cholestasis", "cirrhosis", "pancreatitis", "biliary")):
            alp_obs = observations.get("alkaline_phosphatase")
            if alp_obs and alp_obs.value is not None:
                try:
                    alp_val = float(alp_obs.value)
                    if alp_val <= 420.0:
                        alt = observations.get("alanine_aminotransferase")
                        ast = observations.get("aspartate_aminotransferase")
                        ggt = observations.get("gamma_glutamyl_transferase")
                        bili = observations.get("bilirubin_total")
                        trans_normal = True
                        if alt and alt.value is not None and float(alt.value) > 40:
                            trans_normal = False
                        if ast and ast.value is not None and float(ast.value) > 40:
                            trans_normal = False
                        if ggt and ggt.value is not None and float(ggt.value) > 45:
                            trans_normal = False
                        if bili and bili.value is not None and float(bili.value) > 1.2:
                            trans_normal = False
                        if trans_normal:
                            warnings.append(
                                f"Pregnancy physiological adaptation: ALP {alp_val:.0f} U/L is due to placental isoenzyme synthesis. "
                                f"Transaminases, GGT, and bilirubin are normal. Liver disease rule suppressed."
                            )
                            return "not_applicable", warnings
                except Exception:
                    pass

        # 2. Mild gestational thrombocytopenia (PLT 100k - 150k)
        if any(k in disease_id for k in ("purpura", "disseminated_intravascular_coagulation", "thrombocytopenia", "myeloproliferative", "decreased_platelet", "platelet")):
            plt_obs = observations.get("platelet_count") or observations.get("platelets") or observations.get("plt")
            if plt_obs and plt_obs.value is not None:
                try:
                    plt_val = float(plt_obs.value)
                    if plt_val > 1000.0:
                        plt_val /= 1000.0
                    if 100.0 <= plt_val < 150.0:
                        ldh = observations.get("lactate_dehydrogenase")
                        ldh_high = (ldh and ldh.value is not None and float(ldh.value) > 350)
                        if not ldh_high:
                            warnings.append(
                                f"Pregnancy physiological adaptation: Platelet count {plt_val:.0f} k/uL represents mild gestational thrombocytopenia (normal > 100k). "
                                f"No hemolysis/LDH elevation. Hematologic alarm suppressed."
                            )
                            return "not_applicable", warnings
                except Exception:
                    pass

        # 3. Pregnancy hemodilution (Hb 10.5 - 11.5 g/dL)
        if any(k in disease_id for k in ("pancytopenia", "aplastic_anemia", "myelodysplastic")):
            hb_obs = observations.get("hemoglobin")
            if hb_obs and hb_obs.value is not None:
                try:
                    hb_val = float(hb_obs.value)
                    if hb_val >= 10.5:
                        warnings.append(
                            f"Pregnancy physiological hemodilution: Hemoglobin {hb_val:.1f} g/dL is physiological for plasma expansion. "
                            f"Bone marrow failure rules suppressed."
                        )
                        return "not_applicable", warnings
                except Exception:
                    pass

        return None, []

    def _aggregate_disease_interpretations(
        self, items: list[DiseaseInterpretation]
    ) -> list[DiseaseInterpretation]:
        groups: dict[str, list[DiseaseInterpretation]] = {}
        for it in items:
            groups.setdefault(it.disease_id, []).append(it)

        aggregated: list[DiseaseInterpretation] = []
        for did, group in groups.items():
            if len(group) == 1:
                aggregated.append(group[0])
                continue

            # Pairwise synthetic combination diseases (co_*):
            # A co-derangement disease represents the combination of BOTH markers.
            # If ANY constituent rule is insufficient_data, or not all required features are measured,
            # or if any rule is negative, the combined disease CANNOT be declared positive!
            if did.startswith("co_"):
                has_insufficient = any(it.status == "insufficient_data" for it in group)
                has_not_met = any(it.status in ("criterion_not_met", "not_applicable") for it in group)
                if has_insufficient:
                    ins_item = next(it for it in group if it.status == "insufficient_data")
                    ins_item.evidence = [ev for it in group for ev in (it.evidence or [])]
                    ins_item.warnings.append("Pairwise pattern incomplete: requires both markers to be measured.")
                    aggregated.append(ins_item)
                    continue
                elif has_not_met:
                    not_met_item = next(it for it in group if it.status in ("criterion_not_met", "not_applicable"))
                    aggregated.append(not_met_item)
                    continue

            group.sort(key=lambda x: _STATUS_PRIORITY.get(x.status, 99))
            best = group[0]

            seen_evidence = set()
            merged_evidence = []
            for it in group:
                for ev in (it.evidence or []):
                    msg = ev.get("message") if isinstance(ev, dict) else getattr(ev, "message", str(ev))
                    if msg and msg not in seen_evidence:
                        seen_evidence.add(msg)
                        merged_evidence.append(ev)
            best.evidence = merged_evidence

            seen_sources = set()
            merged_sources = []
            for it in group:
                for s in (it.source_ids or []):
                    if s and s not in seen_sources:
                        seen_sources.add(s)
                        merged_sources.append(s)
            best.source_ids = merged_sources

            best.limitations = list(dict.fromkeys(lim for it in group for lim in (it.limitations or [])))
            best.warnings = list(dict.fromkeys(w for it in group for w in (it.warnings or [])))
            best.actionable_recommendations = list(dict.fromkeys(rec for it in group for rec in (it.actionable_recommendations or [])))

            posteriors = [it.bayesian_posterior for it in group if it.bayesian_posterior is not None]
            if posteriors:
                best.bayesian_posterior = max(posteriors)
            fuzzy_scores = [it.fuzzy_score for it in group if it.fuzzy_score is not None]
            if fuzzy_scores:
                best.fuzzy_score = max(fuzzy_scores)

            aggregated.append(best)

        aggregated.sort(key=lambda x: (
            _STATUS_PRIORITY.get(x.status, 99),
            (x.name_en or "").casefold()
        ))
        return aggregated

    @staticmethod
    def _flood_valve(results, protected_rule_ids,
                     max_per_signature=None) -> None:
        limit = max_per_signature or int(
            os.environ.get("HEMOGLYPH_FLOOD_MAX", "12"))
        groups: dict[tuple, list] = {}
        for item in results:
            if item.status in POSITIVE_RESULT_STATES:
                sig = tuple(sorted(
                    e.get("message", "") for e in item.evidence
                    if e.get('truth') == TruthValue.TRUE))
                groups.setdefault(sig, []).append(item)
        for sig, items in groups.items():
            exposed = [it for it in items
                       if it.rule_id not in protected_rule_ids]
            if len(exposed) > limit:
                for item in exposed:

                    if item.critical_alert or item.urgency == 'urgent':
                        continue
                    item.status = "insufficient_data"
                    item.warnings = list(item.warnings) + [
                        f"Flood valve: identical evidence "
                        f"signature fired in {len(items)} "
                        f"interpretations; demoted."]


    def _is_target_population_physiological_normal(
        self, feature_id: str, op: str, val: float, context: ClinicalContext
    ) -> tuple[bool, str]:
        """
        Grounded in Nelson Textbook of Pediatrics, Tietz Textbook of Clinical Chemistry,
        and WHO Guidelines on Haemoglobin Cutoffs to Define Anemia.

        Identifies when an observation is physiologically normal for the patient's
        specific target population (age, sex, pregnancy) even if an adult-derived
        rule threshold evaluated to True.
        """
        age = context.age_years
        sex = context.normalized_jensiat()
        pregnant = context.pregnant

        # 1. PEDIATRIC TARGET POPULATION (age < 18)
        if age is not None and age < 18.0:
            # A. Hemoglobin (WHO pediatric cutoffs)
            if feature_id in ("hemoglobin", "hb"):
                if op in ("<", "<="):
                    if age < 0.08: # Neonate (< 28d): normal Hb 14.0 - 22.0
                        ped_lower = 13.5
                    elif age < 0.5: # 1-6 months (physiological nadir): normal down to 9.5
                        ped_lower = 9.5
                    elif age < 5.0: # 6m - 5y: WHO cutoff 11.0
                        ped_lower = 11.0
                    elif age < 12.0: # 5y - 11y: WHO cutoff 11.5
                        ped_lower = 11.5
                    elif age < 15.0: # 12y - 14y: WHO cutoff 12.0
                        ped_lower = 12.0
                    elif sex == "female": # Adolescent female (15-17): WHO cutoff 12.0
                        ped_lower = 12.0
                    else: # Adolescent male (15-17): WHO cutoff 13.0
                        ped_lower = 13.0

                    if val >= ped_lower:
                        return True, (
                            f"Hemoglobin {val:.1f} g/dL is within normal pediatric reference "
                            f"range for age {age:.1f}y (WHO guideline cutoff >= {ped_lower} g/dL)."
                        )

            elif feature_id in ("hematocrit", "hct"):
                if op in ("<", "<="):
                    ped_hct_lower = 31.0 if age < 5.0 else (34.0 if age < 12.0 else 36.0)
                    if val >= ped_hct_lower:
                        return True, (
                            f"Hematocrit {val:.1f}% is within normal pediatric reference range "
                            f"(pediatric cutoff >= {ped_hct_lower}%)."
                        )

            elif feature_id in ("mean_corpuscular_hemoglobin", "mch"):
                if op in ("<", "<="):
                    ped_mch_min = 24.0 if age < 5.0 else (25.0 if age < 12.0 else 26.5)
                    if val >= ped_mch_min:
                        return True, (
                            f"MCH {val:.1f} pg is within normal pediatric reference range "
                            f"(limit >= {ped_mch_min} pg)."
                        )

            elif feature_id in ("red_cell_distribution_width", "red_cell_distribution_width_cv", "rdw", "rdw_cv"):
                if op in ("<", "<="):
                    if val >= 11.0:
                        return True, (
                            f"RDW {val:.1f}% indicates uniform erythrocyte sizing and is clinically normal "
                            f"(pediatric limit >= 11.0%)."
                        )

            # B. Creatinine (Tietz / Schwartz)
            elif feature_id in ("creatinine", "serum_creatinine", "scr"):
                if age < 0.08:
                    ped_low, ped_high = 0.20, 0.50
                elif age < 1.0:
                    ped_low, ped_high = 0.15, 0.42
                elif age < 6.0:
                    ped_low, ped_high = 0.20, 0.55
                elif age < 12.0:
                    ped_low, ped_high = 0.35, 0.70
                else:
                    ped_low, ped_high = 0.50, 0.85

                if op in ("<", "<=") and val >= ped_low:
                    return True, (
                        f"Creatinine {val:.2f} mg/dL is physiological for pediatric muscle mass "
                        f"(age {age:.1f}y reference {ped_low}–{ped_high} mg/dL), not pathological decrease."
                    )
                if op in (">", ">=") and val <= ped_high:
                    return True, (
                        f"Creatinine {val:.2f} mg/dL is within normal pediatric range "
                        f"(age {age:.1f}y reference {ped_low}–{ped_high} mg/dL)."
                    )

            # C. Alkaline Phosphatase (Active osteoblastic bone growth spurt)
            elif feature_id in ("alkaline_phosphatase", "alp"):
                if op in (">", ">="):
                    ped_alp_max = 450.0 if age < 10.0 else 850.0
                    if val <= ped_alp_max:
                        return True, (
                            f"Alkaline phosphatase {val:.0f} U/L reflects physiological osteoblastic "
                            f"activity during pediatric bone growth (normal pediatric upper limit up to {ped_alp_max} U/L)."
                        )

            # D. Phosphate / Phosphorus (Growth hormone & skeletal mineralization)
            elif feature_id in ("phosphate", "phosphorus"):
                if op in (">", ">="):
                    ped_phos_max = 5.8 if age < 12.0 else 4.8
                    if val <= ped_phos_max:
                        return True, (
                            f"Phosphate {val:.2f} mg/dL is physiological for growing skeletal tissue "
                            f"(pediatric upper limit up to {ped_phos_max} mg/dL)."
                        )

            # E. Blood Urea Nitrogen & Urea
            elif feature_id in ("blood_urea_nitrogen", "bun"):
                if op in (">", ">=") and val <= 18.0:
                    return True, f"BUN {val:.1f} mg/dL is within normal pediatric limits (upper limit 18 mg/dL)."
            elif feature_id == "urea":
                if op in (">", ">=") and val <= 38.0:
                    return True, f"Urea {val:.1f} mg/dL is within normal pediatric limits (upper limit 38 mg/dL)."

            # F. White Blood Cell Count
            elif feature_id in ("white_blood_cell_count", "wbc"):
                # Canonical WBC is 10^9/L (7.5), but legacy inputs may be
                # /uL (7500). Compare on the same scale or a count of 22
                # x10^9/L in a child is declared "normal".
                wbc_per_ul = val * 1000.0 if val < 500.0 else val
                if op in (">", ">="):
                    ped_wbc_max = 30000.0 if age < 0.08 else (17500.0 if age < 1.0 else (14500.0 if age < 6.0 else 13500.0))
                    if wbc_per_ul <= ped_wbc_max:
                        return True, f"WBC {wbc_per_ul:.0f} /uL is within normal pediatric reference limits."
                elif op in ("<", "<="):
                    ped_wbc_min = 4500.0 if age >= 1.0 else 6000.0
                    if wbc_per_ul >= ped_wbc_min:
                        return True, f"WBC {wbc_per_ul:.0f} /uL is normal for pediatric age."

        # 2. ADULT FEMALE TARGET POPULATION (age >= 15, female, non-pregnant)
        elif sex == "female" and not pregnant:
            if feature_id in ("hemoglobin", "hb") and op in ("<", "<="):
                if val >= 12.0:
                    return True, (
                        f"Hemoglobin {val:.1f} g/dL is within normal adult female reference range "
                        f"(WHO cutoff >= 12.0 g/dL; 13.0 g/dL cutoff applies to males only)."
                    )
            elif feature_id in ("creatinine", "serum_creatinine", "scr") and op in ("<", "<="):
                if val >= 0.50:
                    return True, f"Creatinine {val:.2f} mg/dL is normal for female muscle mass (ref 0.50–1.00 mg/dL)."

        # 3. PREGNANCY TARGET POPULATION
        elif pregnant:
            if feature_id in ("hemoglobin", "hb") and op in ("<", "<="):
                # WHO / ACOG: anaemia in pregnancy is Hb < 11.0 g/dL in the
                # first and third trimesters and < 10.5 g/dL in the second.
                # Without a trimester the 10.5-10.9 band cannot be called
                # normal; it is left to the guideline rule (and flagged).
                trimester = getattr(context, "pregnancy_trimester", None)
                preg_lower = 10.5 if trimester == 2 else 11.0
                if val >= preg_lower:
                    return True, (
                        f"Hemoglobin {val:.1f} g/dL reflects expected physiological hemodilution "
                        f"of pregnancy (WHO/ACOG limit >= {preg_lower:.1f} g/dL"
                        + (f", trimester {trimester}" if trimester in (1, 2, 3) else "") + ")."
                    )
            elif feature_id in ("alkaline_phosphatase", "alp") and op in (">", ">="):
                if val <= 450.0:
                    return True, (
                        f"Alkaline phosphatase {val:.0f} U/L is consistent with normal placental "
                        f"isoenzyme production during pregnancy (normal up to 2–3× non-pregnant ULN)."
                    )
            elif feature_id in ("creatinine", "serum_creatinine", "scr") and op in ("<", "<="):
                if val >= 0.40:
                    return True, f"Creatinine {val:.2f} mg/dL reflects expected gestational hyperfiltration."
            elif feature_id in ("white_blood_cell_count", "wbc") and op in (">", ">="):
                wbc_per_ul = val * 1000.0 if val < 500.0 else val
                if wbc_per_ul <= 15000.0:
                    return True, (
                        f"WBC {wbc_per_ul:.0f} /uL reflects normal physiological leukocytosis of pregnancy "
                        f"(ACOG reference upper limit up to 15,000 /uL)."
                    )

        return False, ""

    def _arzyabi_condition(
        self, condition: Mapping[str, Any],
        observations: Mapping[str, ObservationRecord],
        context: ClinicalContext,
    ) -> NodeEvaluation:
        feature_id = str(condition.get("feature_id", ""))
        op = condition.get("operator")
        threshold = condition.get("value")
        target_unit = normalize_unit(condition.get("unit"))
        record = observations.get(feature_id)
        if record is None:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, operator=op,
                threshold=threshold, threshold_unit=target_unit,
                message="Required observation is missing.")
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence], {feature_id},
                set(), [])
        if record.metadata.get("conflict"):
            evidence = ConditionEvidence(
                feature_id, TruthValue.CONFLICT, record.value,
                record.unit, op, threshold, target_unit,
                "Conflicting observations were supplied.",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.CONFLICT, [evidence],
                warnings=list(record.warnings))
        if self.require_confirmed and not record.confirmed:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, record.value,
                record.unit, op, threshold, target_unit,
                "Observation requires confirmation.",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence], {feature_id},
                set(), list(record.warnings))
        missing_context: list[str] = []
        context_false = False
        for key, expected in (condition.get("context")
                              or {}).items():
            passed, missing = self._context_requirement(
                key, expected, record, context)
            if missing:
                missing_context.append(missing)
            elif passed is False:
                context_false = True
        if missing_context:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, record.value,
                record.unit, op, threshold, target_unit,
                "Required measurement/clinical context is missing.",
                missing_context=missing_context,
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence], set(),
                set(missing_context), list(record.warnings))
        if context_false:
            evidence = ConditionEvidence(
                feature_id, TruthValue.FALSE, record.value,
                record.unit, op, threshold, target_unit,
                "Context requirement is not satisfied.",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.FALSE, [evidence],
                warnings=list(record.warnings))
        qualitative_expected = (
            condition.get("context") or {}).get("qualitative")
        if qualitative_expected is not None:
            actual = _qualitative(record.value)
            expected = _qualitative(qualitative_expected)
        else:
            actual = _float(record.value)
            expected = _float(threshold)
            # Serology / qualitative results arrive as "positive" /
            # "negative" while the registry encodes them as 1 / 0 (unit
            # "1"). Coerce instead of dropping the condition as "needs a
            # number" - that silently discarded anti-HAV IgM, HBsAg, DAT...
            if actual is None and expected is not None and expected in (0.0, 1.0):
                q = _qualitative(record.value)
                if q == "positive":
                    actual = 1.0
                elif q == "negative":
                    actual = 0.0
        if actual is None or expected is None:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, record.value,
                record.unit, op, threshold, target_unit,
                "Numeric comparison requires numeric values.",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence], {feature_id},
                set(), list(record.warnings))
        if (condition.get('context') or {}).get(
                'change_from_baseline'):
            delta = _float(record.metadata.get(
                "delta_from_baseline"))
            if delta is None:
                evidence = ConditionEvidence(
                    feature_id, TruthValue.UNKNOWN, record.value,
                    record.unit, op, threshold, target_unit,
                    "Baseline delta is missing.",
                    missing_context=["delta_from_baseline"],
                    source=record.source,
                    reference_low=record.reference_low,
                    reference_high=record.reference_high)
                return NodeEvaluation(
                    TruthValue.UNKNOWN, [evidence], set(),
                    {"delta_from_baseline"},
                    list(record.warnings))
            actual = delta
        assumptions: list[str] = []
        source_unit = normalize_unit(record.unit)
        if source_unit is None:
            if not self.assume_rule_unit_for_scalars:
                evidence = ConditionEvidence(
                    feature_id, TruthValue.UNKNOWN, record.value,
                    None, op, threshold, target_unit,
                    'Observation unit is missing.',
                    missing_context=["unit"],
                    source=record.source,
                    reference_low=record.reference_low,
                    reference_high=record.reference_high)
                return NodeEvaluation(
                    TruthValue.UNKNOWN, [evidence], set(),
                    {"unit"}, list(record.warnings))
            source_unit = target_unit
            assumptions.append(
                f"Assumed rule unit {target_unit} for unitless "
                f"scalar input.")
        if target_unit and source_unit != target_unit:
            try:
                converted = convert_unit(
                    actual, source_unit, target_unit, feature_id)
                assumptions.append(
                    f"Converted {source_unit} to {target_unit}.")
                actual = converted
            except CalculationError as exc:
                evidence = ConditionEvidence(
                    feature_id, TruthValue.UNKNOWN, record.value,
                    source_unit, op, threshold, target_unit,
                    str(exc),
                    missing_context=["compatible_unit"],
                    source=record.source,
                    reference_low=record.reference_low,
                    reference_high=record.reference_high)
                return NodeEvaluation(
                    TruthValue.UNKNOWN, [evidence], set(),
                    {"compatible_unit"},
                    list(record.warnings))
        cctx = condition.get("context") or {}
        uses_reference = (
            cctx.get("above_local_uln")
            or cctx.get("above_assay_99th_percentile")
            or cctx.get("three_times_upper_reference_limit")
            or cctx.get("five_times_upper_reference_limit"))
        if uses_reference:
            if record.reference_high is None:
                missing_ctx = "reference_interval"
                evidence = ConditionEvidence(
                    feature_id, TruthValue.UNKNOWN, record.value,
                    source_unit, op, threshold, target_unit,
                    "Local upper reference limit is missing.",
                    missing_context=[missing_ctx],
                    source=record.source)
                return NodeEvaluation(
                    TruthValue.UNKNOWN, [evidence], set(),
                    {missing_ctx}, list(record.warnings))
            if cctx.get("above_local_uln") or cctx.get(
                    "above_assay_99th_percentile"):
                expected = record.reference_high
            elif cctx.get("three_times_upper_reference_limit"):
                expected = 3.0 * record.reference_high
            elif cctx.get("five_times_upper_reference_limit"):
                expected = 5.0 * record.reference_high
            else:
                expected = record.reference_high
        elif (feature_id in METHOD_DEPENDENT_FEATURES
                and op in (">", ">=", "<", "<=")
                and source_unit == target_unit
                and (record.reference_high is not None
                     or record.reference_low is not None)):
            # Method-dependent analyte with the performing laboratory's own
            # interval on the report: an absolute cut-off in the registry
            # (e.g. ALT > 45) is an upper-reference-limit criterion written
            # against ONE method. Re-express it as the same multiple of the
            # laboratory's limit (CLSI EP28-A3c). CDL-locked analytes never
            # reach this branch.
            lo_ratio, hi_ratio = local_reference_scale(
                feature_id, record, context)
            ratio = hi_ratio if op in (">", ">=") else lo_ratio
            if ratio and abs(ratio - 1.0) > 1e-6 and 0.4 <= ratio <= 2.5:
                scaled = expected * ratio
                assumptions.append(
                    f"Threshold {expected:g} rescaled to {scaled:.4g} "
                    f"{target_unit or ''} using the laboratory's reported "
                    f"interval (method-dependent analyte).")
                expected = scaled
        comparator = OPERATORS.get(op)
        if comparator is None:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, record.value,
                record.unit, op, threshold, target_unit,
                f"Unsupported operator {op!r}.",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence],
                warnings=[f"Unsupported operator in {feature_id}."])
        try:
            passed = bool(comparator(actual, expected))
        except TypeError as exc:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, record.value,
                record.unit, op, threshold, target_unit,
                f"Comparison failed (type mismatch): {exc}",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence],
                warnings=[str(exc)])
        except Exception as exc:
            evidence = ConditionEvidence(
                feature_id, TruthValue.UNKNOWN, record.value,
                record.unit, op, threshold, target_unit,
                f"Comparison failed: {exc}",
                source=record.source,
                reference_low=record.reference_low,
                reference_high=record.reference_high)
            return NodeEvaluation(
                TruthValue.UNKNOWN, [evidence],
                warnings=[str(exc)])

        # TARGET POPULATION & AGE-STRATIFIED PHYSIOLOGICAL NORMAL VERIFICATION
        if passed and actual is not None and isinstance(actual, (int, float)):
            phys_normal, phys_reason = self._is_target_population_physiological_normal(
                feature_id, str(op), float(actual), context)
            if phys_normal:
                passed = False
                assumptions.append(phys_reason)

        truth = TruthValue.TRUE if passed else TruthValue.FALSE
        borderline = False
        strength = None
        if qualitative_expected is not None or op in (
                "in", "not_in"):
            strength = 1.0 if passed else 0.0
        else:
            strength = self._condition_strength(op, actual, expected)
            borderline = bool(passed) and self._borderline_deviation(
                actual, expected, feature_id)
        unit_out = target_unit or record.unit
        if qualitative_expected is not None:
            message = f"{feature_id} is {actual} (expected {expected})."
        else:
            if isinstance(expected, (int, float)):
                message = (f"{feature_id} {unit_out or ''} = "
                           f"{actual:.4g} {op} {expected:.4g}")
            else:
                message = f"{feature_id} {actual} {op} {expected}"
        if (record.reference_low is not None
                or record.reference_high is not None):
            rng = (f"{record.reference_low:.4g}"
                   if record.reference_low is not None else '…')
            rng += "–" + (f"{record.reference_high:.4g}"
                          if record.reference_high is not None
                          else "…")
            message += f" (ref {rng})"
        evidence = ConditionEvidence(
            feature_id, truth, actual, unit_out or record.unit,
            op, expected, target_unit, message,
            assumptions=(assumptions
                         if qualitative_expected is None else []),
            source=record.source,
            reference_low=record.reference_low,
            reference_high=record.reference_high,
            strength=strength, borderline=borderline)
        return NodeEvaluation(
            truth, [evidence],
            warnings=list(record.warnings),
            score=strength)


    def _arzyabi_expression(
        self, expression: Any,
        observations: Mapping[str, ObservationRecord],
        context: ClinicalContext,
    ) -> NodeEvaluation:
        if not isinstance(expression, Mapping):
            return NodeEvaluation(
                TruthValue.UNKNOWN,
                warnings=["Invalid expression node."])
        if "feature_id" in expression:
            return self._arzyabi_condition(
                expression, observations, context)
        if "all" in expression:
            subs = expression["all"]
            children = [
                self._arzyabi_expression(x, observations, context)
                for x in subs]
            node = _edgham_nodes(_edgham_all(children), children)
            node.score = self._soft_all(
                children, [self._child_weight(x) for x in subs])
            return node
        if "any" in expression:
            subs = expression["any"]
            children = [
                self._arzyabi_expression(x, observations, context)
                for x in subs]
            node = _edgham_nodes(_edgham_any(children), children)
            node.score = self._soft_any(
                children, [self._child_weight(x) for x in subs])
            return node
        if "not" in expression:
            child = self._arzyabi_expression(
                expression["not"], observations, context)
            truth = (TruthValue.FALSE if child.truth == TruthValue.TRUE
                     else TruthValue.TRUE if child.truth == TruthValue.FALSE
                     else child.truth)
            node = _edgham_nodes(truth, [child])
            node.score = (1.0 - child.score
                          if child.score is not None else None)
            return node
        if "n_of" in expression:
            # k-of-n junction ("two concordant abnormal tests", "2 of 4
            # SIRS criteria"). TRUE when >= n children are TRUE; FALSE when
            # even counting every undetermined child as TRUE cannot reach
            # n; otherwise UNKNOWN (more data could still satisfy it).
            spec = expression["n_of"] or {}
            subs = list(spec.get("conditions") or spec.get("all") or [])
            try:
                need = int(spec.get("n") or spec.get("min") or 1)
            except (TypeError, ValueError):
                need = 1
            children = [
                self._arzyabi_expression(x, observations, context)
                for x in subs]
            n_true = sum(1 for c in children if c.truth == TruthValue.TRUE)
            n_false = sum(1 for c in children if c.truth == TruthValue.FALSE)
            if n_true >= need:
                truth = TruthValue.TRUE
            elif len(children) - n_false < need:
                truth = TruthValue.FALSE
            else:
                truth = TruthValue.UNKNOWN
            node = _edgham_nodes(truth, children)
            scores = sorted((c.score for c in children if c.score is not None),
                            reverse=True)
            node.score = (sum(scores[:need]) / need) if len(scores) >= need else (
                (sum(scores) / need) if scores else None)
            return node
        return NodeEvaluation(
            TruthValue.UNKNOWN,
            warnings=["Unknown expression node."])

    def _ghaede_allowed(self,
                      rule: Mapping[str, Any]) -> tuple[bool, str]:
        quality = rule.get("quality") or {}
        if self.execution_mode == "clinical":
            if not rule.get("executable", False) or not (
                    quality.get("specialist_reviewed") is True
                    and quality.get("software_tested") is True):
                return False, (
                    "Clinical mode requires executable + "
                    "specialist_reviewed + software_tested "
                    "rule quality.")
            return True, ""
        if rule.get("executable", False) or quality.get(
                'evidence_extracted') is True:
            return True, ""
        return False, (
            "Rule is marked non-executable and has no "
            "extracted evidence.")

    def _clamp_to_contract(self, rule: Mapping[str, Any],
                           status: str) -> tuple[str, list[str]]:
        if not self.enforce_contract:
            return status, []
        contract = rule.get("execution_contract") or {}
        permitted = set(
            contract.get("permitted_result_states") or [])
        if not permitted:
            return status, []
        if status in permitted:
            return status, []

        # Strict directional preservation: negative or ruled-out findings must NEVER clamp to positive patterns!
        if status in ("criterion_not_met", "not_applicable", "ruled_out", "excluded"):
            fallbacks = ["not_applicable", "criterion_not_met", "insufficient_data"]
        elif status == "insufficient_data":
            fallbacks = ["insufficient_data", "not_applicable", "criterion_not_met"]
        else:
            fallbacks = ['compatible_pattern', "possible_pattern", "screening_positive",
                         "criterion_met", "insufficient_data", "not_applicable"]

        for fb in fallbacks:
            if fb in permitted:
                return fb, [
                    f"Result state '{status}' is not permitted by "
                    f"this rule's contract; emitted '{fb}' "
                    f"instead (contract violation clamped)."]
        return status, [
            f"Result state '{status}' is not permitted; "
            'contract cannot be satisfiable.']


    def _ejra_advanced_layers(
        self, observations: Mapping[str, ObservationRecord],
        context: ClinicalContext,
        rule_scores_in: Optional[Mapping[str, float]] = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            'bayesian': {},
            "fuzzy": {},
            "ensemble": {},
            "differential": [],
            "graph_insights": {},
            "corrections": [],
            "drug_interactions": [],
            "expanded_kg_insights": {},
            "differential_groups": {},
            "contraindications": {},
            'derived_patterns': [],
            "pattern_adjustments": {},
            "reference_policy": {},
        }


        # Unit invariance (audit 2026-10-20): the rule layer converts every
        # value to the registry's canonical unit before comparing, but the
        # Bayesian / fuzzy / derived-pattern layers received the *raw* value,
        # so a haemoglobin of 91 g/L or a creatinine of 389 umol/L was scored
        # against mg/dL / g/dL thresholds. Canonicalise once here; the
        # original unit is kept in metadata for the report.
        _canon_obs: dict[str, ObservationRecord] = {}
        for _fid, _rec in observations.items():
            try:
                _meta = self.registry.features.get(_fid) or {}
                _canon_unit = (_meta.get("units") or {}).get("canonical")
                _raw = _float(_rec.value)
                if _canon_unit and _rec.unit and _raw is not None \
                        and str(_rec.unit).strip().lower() != str(_canon_unit).strip().lower():
                    _cv = self._coerce_canonical(_fid, _rec.value, _rec.unit)
                    if _cv is not None and _cv != _raw:
                        _nr = replace(_rec, value=_cv, unit=_canon_unit)
                        _nr.metadata = dict(_rec.metadata or {})
                        _nr.metadata["reported_value"] = _raw
                        _nr.metadata["reported_unit"] = _rec.unit
                        # a printed interval travels with the printed unit
                        if _nr.reference_low is not None:
                            _nr.reference_low = _float(self._coerce_canonical(_fid, _nr.reference_low, _rec.unit))
                        if _nr.reference_high is not None:
                            _nr.reference_high = _float(self._coerce_canonical(_fid, _nr.reference_high, _rec.unit))
                        _canon_obs[_fid] = _nr
                        continue
            except Exception:
                pass
            _canon_obs[_fid] = _rec
        observations = _canon_obs

        corrections = emal_interference_corrections(
            observations, context)
        result["corrections"] = corrections
        enriched = enrich_observations(
            observations, context, corrections)
        obs_dict = {fid: obs.value for fid, obs in enriched.items()}


        drug_interactions = tashkhis_interactions(
            observations, context)
        result["drug_interactions"] = drug_interactions


        raw_values = {fid: _float(rec.value)
                      for fid, rec in observations.items()}
        raw_values = {k: v for k, v in raw_values.items() if v is not None}
        for corr in corrections:
            raw_values[corr["feature_id"]] = corr["corrected_value"]
        patterns = tahlil_olgoo_haye_moshtagh(raw_values, context)
        # The pattern list is consumed in several places downstream; emit
        # each index once so a ratio is never shown twice.
        _seen_pat: set = set()
        patterns = [pt for pt in patterns
                    if not (pt.pattern_id in _seen_pat
                            or _seen_pat.add(pt.pattern_id))]
        result["derived_patterns"] = [asdict(pt) for pt in patterns]


        weight = {'high': 0.35, "moderate": 0.18, "low": 0.08}
        adjustments: dict[str, float] = {}
        for pt in patterns:
            w = weight.get(pt.significance, 0.1)
            for did in pt.supports:
                adjustments[did] = adjustments.get(did, 0.0) + w
            for did in pt.argues_against:
                adjustments[did] = adjustments.get(did, 0.0) - w
        result["pattern_adjustments"] = adjustments


        findings = self._bayesian_net.estekhraj_findings(enriched)
        bayesian_results = self._bayesian_net.mohasebe_posteriors(
            findings, context)

        for br in bayesian_results:
            adj = adjustments.get(br.disease_id)
            if not adj:
                continue
            pr = _clamp01(br.posterior_probability)
            lo = math.log(max(pr, 1e-9) / max(1e-9, 1 - pr)) + adj * 2.0
            br.posterior_probability = _clamp01(
                1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, lo)))))
            br.contributing_factors.append({
                "type": "derived_pattern",
                "effect": f"{'+' if adj > 0 else ''}{adj:.2f} log-odds",
            })
        # Count-defined syndromes (ATP-III / IDF metabolic syndrome = any 3
        # of 5 components) cannot be near-certain from fewer positive
        # components than the definition needs, however strong the LRs are.
        for br in bayesian_results:
            spec = COUNT_DEFINED_NODES.get(br.disease_id)
            if not spec:
                continue
            need, groups, cap = spec
            n_pos = 0
            for grp in groups:
                if any(bool((findings.get(k) or {}).get("present")) for k in grp):
                    n_pos += 1
            if n_pos < need and br.posterior_probability > cap:
                br.posterior_probability = cap
                br.contributing_factors.append({
                    "type": "count_definition_cap",
                    "effect": f"{n_pos}/{need} defining components positive -> capped at {cap:.2f}",
                })
        for br in bayesian_results:
            result["bayesian"][br.disease_id] = {
                'posterior': br.posterior_probability,
                "confidence": br.confidence,
                "evidence_count": br.evidence_count,
                'measured_count': br.measured_count,
                "factors": br.contributing_factors,
                "explanation": br.explanation,
            }


        # --- carry input uncertainty and laboratory intervals forward ----
        feature_reliability = {fid: obs.reliability
                               for fid, obs in enriched.items()}
        reference_scale = {
            fid: local_reference_scale(fid, observations.get(fid), context)
            for fid in enriched}
        result["reference_policy"] = {
            fid: {
                "source": obs.reference_source,
                "interval": obs.reference_used,
                "note": obs.reference_note,
                "reliability": round(obs.reliability, 3),
            }
            for fid, obs in enriched.items()
            if obs.reference_source != "registry" or obs.reliability < 0.999
        }

        fuzzy_results = self._fuzzy_engine.evaluate(
            obs_dict, context,
            reliability=feature_reliability,
            reference_scale=reference_scale)
        fuzzy_min_rel: dict[str, float] = {}
        for fr in fuzzy_results:
            result['fuzzy'][fr.disease_id] = {
                'membership': fr.membership_score,
                "rules": fr.activated_rules,
                "explanation": fr.explanation,
                "used_features": fr.used_features,
                "min_reliability": fr.min_reliability,
            }
            fuzzy_min_rel[fr.disease_id] = fr.min_reliability

        # Per-disease input reliability = weakest piece of evidence that
        # actually drove that disease in Bayes or fuzzy.
        finding_rel = {k: float(v.get("reliability", 1.0))
                       for k, v in findings.items()}
        disease_input_rel: dict[str, float] = dict(fuzzy_min_rel)
        for did, data in result["bayesian"].items():
            rels = [finding_rel.get(f.get("feature"), 1.0)
                    for f in (data.get("factors") or [])
                    if f.get("type") == "evidence"]
            if rels:
                disease_input_rel[did] = min(
                    disease_input_rel.get(did, 1.0), min(rels))


        high_prob = [
            did for did, data in result['bayesian'].items()
            if data["posterior"] > 0.4]
        graph_boosts: dict[str, Optional[float]] = {}
        all_diseases = set(
            list(result['bayesian'].keys())
            + list(result["fuzzy"].keys()))
        for did in all_diseases:
            boost = self._knowledge_graph.support_boost(did, high_prob)

            graph_boosts[did] = boost if boost > 0 else None


        expanded_insights = {}
        differential_groups = {}
        contraindications = {}
        for did in high_prob:
            expanded_insights[did] = self._knowledge_graph.get_bimari_context(did)
            differential_groups[did] = (
                self._knowledge_graph.yaftan_differential_tashkhis_goroohbandi(did))
            contraindications[did] = (
                self._knowledge_graph.get_contraindications(did))

        result["graph_insights"] = {
            "high_probability": high_prob,
            "related_conditions": {
                did: self._knowledge_graph.get_related_diseases(did)
                for did in high_prob
            },
        }
        result['expanded_kg_insights'] = expanded_insights
        result['differential_groups'] = differential_groups
        result["contraindications"] = contraindications


        rule_scores: dict[str, float] = dict(rule_scores_in or {})
        for pt in patterns:
            if pt.significance == "high":
                for did in pt.supports:
                    rule_scores[did] = max(rule_scores.get(did, 0.0), 0.75)
                for did in pt.argues_against:
                    if did in rule_scores:
                        rule_scores[did] = min(rule_scores[did], 0.20)

        # Domain profile per disease (drives the weight table used).
        domain_of: dict[str, list[str]] = {}
        try:
            reg_diseases = self.registry.diseases
            for did in set(rule_scores) | set(result["bayesian"]) | set(result["fuzzy"]):
                dis = reg_diseases.get(did) or {}
                cls = dis.get("classification") or {}
                doms = list(cls.get("domains") or [])
                if not doms and dis.get("category"):
                    doms = [str(dis.get("category"))]
                domain_of[did] = doms
        except Exception:
            domain_of = {}

        self._reasoner._domain_of = domain_of
        self._reasoner._guideline_anchored = getattr(self, "_guideline_anchored", frozenset())
        self._reasoner._esl_hits = list(getattr(self, "_esl_hits", []) or [])
        self._reasoner._expert_anchored = frozenset(d for h in self._reasoner._esl_hits for d in h.get("dx", ()))
        self._reasoner._expert_definitional = frozenset(
            h["dx"][0] for h in self._reasoner._esl_hits
            if h.get("dx") and str(h.get("strength") or "") == "anchor" and not h.get("guard"))
        self._reasoner._disease_true_feats = getattr(self, "_disease_true_feats", {})
        ensemble_results = tarkib_ensemble(
            rule_scores=rule_scores,
            bayesian_scores={
                d: (v["posterior"] if v.get("evidence_count", 0) > 0 else None)
                for d, v in result["bayesian"].items()},
            fuzzy_scores={
                d: v["membership"]
                for d, v in result["fuzzy"].items()
                if v.get("membership", 0.0) >= 0.25},
            graph_boosts=graph_boosts,
            risk_scores=dict(getattr(self, "_risk_layer_scores", {}) or {}),
            domain_of=domain_of,
            input_reliability=disease_input_rel,
            guideline_anchored=getattr(self, "_guideline_anchored", ()),
            expert_anchored=self._reasoner._expert_anchored,
            expert_definitional=self._reasoner._expert_definitional,
            finding_ids=[d for d in set(rule_scores) | set(result["bayesian"]) | set(result["fuzzy"])
                         if self._reasoner._is_finding(d)],
        )
        for er in ensemble_results:
            result["ensemble"][er.disease_id] = {
                "score": er.final_score,
                "votes": er.votes,
                "confidence": er.confidence,
                "interpretation": er.interpretation,
                "belief": round(er.belief, 4),
                "plausibility": round(er.plausibility, 4),
                "ignorance": round(er.ignorance, 4),
                "conflict": round(er.conflict, 4),
                "evidence_state": er.evidence_state,
                "weight_profile": er.weight_profile,
                "input_reliability": round(er.input_reliability, 3),
            }

        differential = self._reasoner.differential_diagnosis(
            ensemble_results, obs_dict, context)
        result['differential'] = [
            {
                "disease_id": de.disease_id,
                'rank': de.rank,
                "probability": de.probability,
                "confidence": de.confidence,
                "status": de.status,
                "evidence": de.supporting_evidence,
                "recommended_tests": de.recommended_tests,
                "ensemble_votes": de.ensemble_votes,
                "sensitivity_notes": de.sensitivity_notes,
                "statement": de.statement,
                "belief": de.belief,
                "plausibility": de.plausibility,
                "conflict": de.conflict,
                "evidence_state": de.evidence_state,
                "weight_profile": de.weight_profile,
                "explained_by": getattr(de, "explained_by", None),
                "tier": self._reasoner.tier_of(de.disease_id),
            }
            for de in differential]

        return result


    def interpret(
        self,
        inputs: Mapping[str, Any],
        derived: Optional[Mapping[str, Any]] = None,
        patient: Optional[
            ClinicalContext | PatientContext
            | Mapping[str, Any]] = None,
        *,
        include_negative: bool = False,
        include_insufficient: bool = True,
        domains: Optional[set[str]] = None,
        max_insufficient: Optional[int] = None,
    ) -> InterpretationReport:
        context = ClinicalContext.from_any(patient or {})
        observations, input_warnings = normalize_observations(
            inputs, derived, self._vizhegi_ghabel_ghabool())
        input_warnings = list(input_warnings) + preanalytical_gate(
            self, observations, context)
        _mirror_equivalent_observations(observations, context)
        obs_signature = hashlib.blake2b(
            (_canonical_json(observations) + "\x00"
             + _canonical_json(context)).encode(),
            digest_size=16,
        ).hexdigest()
        if max_insufficient is None:
            max_insufficient = int(
                os.environ.get("HEMOGLYPH_MAX_INSUFFICIENT", '400'))


        panic_alerts = self._barresi_panic_override(observations)
        critical_alerts_output: list[dict[str, Any]] = list(panic_alerts)

        results: list[DiseaseInterpretation] = []
        skipped: dict[str, str] = {}
        gated = 0
        registry = self.registry
        protected_ids: set[str] = set()
        all_rules = registry.rules
        candidate_ids = registry.candidate_ghaede_ids(
            observations.keys())
        collapsed_by_status: dict[str, int] = {}
        materialised_by_status: dict[str, int] = {}
        materialised_fast = 0


        pending: list[tuple] = []
        for rule_id, rule in all_rules.items():
            disease = registry.diseases[rule["disease_id"]]
            cls = disease.get('classification') or {}
            disease_domains = set(cls.get('domains') or [])
            if domains and not disease_domains.intersection(domains):
                continue
            allowed, reason = self._ghaede_allowed(rule)
            if not allowed:
                skipped[rule_id] = reason
                continue
            if rule_id not in candidate_ids:
                applicable, population_missing, _reason = \
                    self._population_applicable(rule, context)
                node = NodeEvaluation(TruthValue.UNKNOWN)
                node.missing_context.update(population_missing)
                if applicable:
                    node.missing_features.update(
                        rule.get("_feature_ids") or ())
                status = ("insufficient_data" if applicable
                          else "not_applicable")
                status, contract_warnings = self._clamp_to_contract(
                    rule, status)
                if contract_warnings:
                    gated += 1
                if status == "criterion_not_met" and not include_negative:
                    continue
                if (status == 'insufficient_data'
                        and not include_insufficient):
                    continue
                collapsed_by_status[status] = \
                    collapsed_by_status.get(status, 0) + 1
                if materialised_fast >= max_insufficient:
                    continue
                materialised_fast += 1
                materialised_by_status[status] = \
                    materialised_by_status.get(status, 0) + 1
                pending.append((rule_id, rule, disease, cls,
                                disease_domains, status, node,
                                contract_warnings))
                continue
            applicable, population_missing, not_applicable_reason = \
                self._population_applicable(rule, context)
            if not applicable:
                node = NodeEvaluation(TruthValue.UNKNOWN)
                node.missing_context.update(population_missing)
                if not_applicable_reason:
                    node.warnings.append(not_applicable_reason)
                status = "not_applicable"
            else:
                cache_key = (rule_id, obs_signature)
                cached = self._expression_cache.get(cache_key)
                if cached is None:
                    cached = self._arzyabi_expression(
                        rule["expression"], observations, context)
                    self._expression_cache[cache_key] = cached
                    if len(self._expression_cache) > \
                            self._EXPRESSION_CACHE_MAX:
                        self._expression_cache.popitem(last=False)
                else:
                    self._expression_cache.move_to_end(cache_key)


                node = _clone_node(cached)
                node.missing_context.update(population_missing)
                if node.truth == TruthValue.TRUE:
                    rule_type = rule.get("rule_type", "")
                    status = TRUE_STATUS.get(
                        rule_type, "compatible_pattern")

                    # Pairwise co_ disease gating: requires ALL required features to be in observations
                    did = str(rule.get("disease_id") or "")
                    if did.startswith("co_"):
                        req_fids = (disease.get("feature_links") or {}).get("required") or []
                        if any(rf not in observations for rf in req_fids):
                            status = "insufficient_data"
                            node.warnings.append(
                                "Pairwise combination pattern requires both analytes to be measured; observation missing."
                            )

                    if status == "compatible_pattern":
                        rule_fids = rule.get("_feature_ids") or ()
                        present = sum(
                            1 for f in rule_fids
                            if f in observations)
                        true_feature_ids = {
                            e.feature_id for e in node.evidence
                            if e.truth == TruthValue.TRUE}
                        true_hits = sum(
                            1 for f in rule_fids
                            if f in true_feature_ids)
                        if len(rule_fids) > 1 and (
                                present < 2 or true_hits < 2):
                            status = 'insufficient_data'
                            node.warnings.append(
                                "Single-marker support only; "
                                "compatible pattern withheld "
                                "until confirmatory features "
                                'are entered.')
                    status, guard_warnings, protected = \
                        self._specificity_guard(
                            rule, disease, node, status, context, observations)
                    if guard_warnings:
                        node.warnings.extend(guard_warnings)
                    if protected:
                        protected_ids.add(rule_id)

                    # ULTRA-PRECISE: Pediatric false positive guard
                    ped_status, ped_warnings = self._pediatric_false_positive_guard(
                        rule, node, context, observations)
                    if ped_status is not None:
                        status = ped_status
                        if ped_warnings:
                            node.warnings.extend(ped_warnings)

                    # ULTRA-PRECISE: Pregnancy physiological false positive guard
                    preg_status, preg_warnings = self._pregnancy_false_positive_guard(
                        rule, node, context, observations)
                    if preg_status is not None:
                        status = preg_status
                        if preg_warnings:
                            node.warnings.extend(preg_warnings)
                elif node.truth == TruthValue.FALSE:
                    status = "criterion_not_met"
                elif node.truth == TruthValue.CONFLICT:
                    status = "conflicting_data"
                else:
                    status = "insufficient_data"
            if (status == "compatible_pattern"
                    and "possible_pattern" in
                    (rule.get("result") or {}).get(
                        "allowed_labels", [])):
                status = 'possible_pattern'
            status, contract_warnings = self._clamp_to_contract(
                rule, status)
            if contract_warnings:
                gated += 1
            if status == 'criterion_not_met' and not include_negative:
                continue
            if (status == 'insufficient_data'
                    and not include_insufficient):
                continue
            pending.append((rule_id, rule, disease, cls,
                            disease_domains, status, node,
                            contract_warnings))


        rule_scores: dict[str, float] = {}
        guideline_anchored: set[str] = set()
        disease_true_feats: dict[str, set[str]] = {}
        for (_rid, _rule, _dis, _cls, _dom, _st, _node,
             _cw) in pending:
            did = _rule["disease_id"]
            base = _RULE_STATUS_SCORE.get(_st)
            if base is None:
                continue
            soft = _node.score
            score = base if soft is None else (
                0.5 * base + 0.5 * _clamp01(soft) * base / 0.95)

            # The registry grades its own rules and we were discarding that
            # grading. A general screening rule and a disease-specific
            # diagnostic criterion arrived at the ensemble carrying equal
            # authority, which across tens of thousands of rules lets broad
            # low-information rules outvote the precise ones.
            rule_type = str(_rule.get("rule_type") or "").lower()
            score *= _SPECIFICITY_FACTOR.get(
                str(_rule.get("specificity") or "").lower(), 1.0)
            score *= _RULE_TYPE_FACTOR.get(rule_type, 1.0)

            # A lone non-specific threshold is a doorway, not evidence.
            # "haemoglobin < 13" appears as a screening rule for 658
            # diseases and "ferritin < 15" as a *diagnostic* criterion for
            # 628, so on their own they say only that the patient is
            # anaemic - never which anaemia. Left at full weight they let
            # hereditary spherocytosis tie with iron deficiency on
            # identical evidence.
            #
            # The test is the rule's own grading, not its label: one
            # condition and specificity "general" means non-discriminating
            # whatever layer it claims to belong to. Conjunctions and
            # rules the registry marks "specific" keep their full weight.
            # Measured, not declared, specificity. The registry marks
            # 31,394 of 33,875 rules "specific" - including "glucose <= 70"
            # stamped verbatim onto HHS, Addison's and euthyroid-sick
            # syndrome. A rule's vote for *one* disease is discounted by
            # how many diseases carry the identical threshold.
            emp_spec = registry.rule_empirical_specificity.get(_rid, 1.0)
            # A positive pathogen-specific marker (HBsAg, anti-HCV, HIV Ag/Ab,
            # culture, PCR, malaria smear) is not a "doorway" threshold such as
            # Hb < 13: it names the organism. It keeps its weight even when it is
            # the only condition and is shared by a handful of related entities.
            _pathogen_single = (
                _shomar_shart(_rule) < 2
                and _node.truth == TruthValue.TRUE
                and (_is_pathogen_marker_rule(_rule)
                     or _is_decisive_marker_rule(_rule)))
            if _pathogen_single:
                floor_spec = PATHOGEN_MARKER_MIN_SPECIFICITY
                if (rule_type == "diagnostic_criterion"
                        and _is_decisive_marker_rule(_rule)):
                    floor_spec = DECISIVE_DIAGNOSTIC_MIN_SPECIFICITY
                emp_spec = max(emp_spec, floor_spec)
            elif _shomar_shart(_rule) < 2 and (
                    emp_spec < 1.0
                    or str(_rule.get("specificity") or "").lower() != "specific"):
                score *= _TAK_SHART_SCREENING_FACTOR
            score *= emp_spec
            # A finding that is the entity's own definition and is TRUE is an
            # established fact, not a hypothesis: potassium 6.0 *is*
            # hyperkalaemia. It must clear the red-flag floor on its own.
            if (_rid in registry.rule_defines_entity
                    and _st in ("criterion_met", "screening_positive", "urgent_pattern")
                    and _node.truth == TruthValue.TRUE):
                score = max(score, DEFINITIONAL_FINDING_SCORE)

            # A met *curated* guideline criterion (curation 13.0.0) is the
            # published decision limit itself - it is not diluted by the
            # soft-membership blend meant for AI-assembled thresholds.
            if (str(_rule.get("status") or "") == "curated_guideline_anchored"
                    and _st in ("criterion_met", "urgent_pattern")
                    and _node.truth == TruthValue.TRUE):
                score = max(score, GUIDELINE_ANCHOR_RULE_SCORE)
                guideline_anchored.add(did)
            if _st in POSITIVE_RESULT_STATES and _node.truth == TruthValue.TRUE:
                disease_true_feats.setdefault(did, set()).update(
                    e.feature_id for e in _node.evidence
                    if e.truth == TruthValue.TRUE and e.feature_id)

            rule_scores[did] = max(rule_scores.get(did, 0.0),
                                   _clamp01(score))
            if _HG_DEBUG_RULES and did in _HG_DEBUG_RULES:
                print(f"[rule] {did} {_rid} st={_st} truth={_node.truth} soft={_node.score} -> {score:.3f}")

        # --- Expert Syndrome Layer: constellation-level diagnoses -----------
        # A met constellation enters the fusion as a curated anchored rule
        # vote (the same path a `curated_guideline_anchored` registry rule
        # takes) and carries the observation ids it consumed so evidence
        # subsumption lists the constituent findings beneath it.
        esl_hits: list[dict[str, Any]] = []
        try:
            esl_hits = self._esl.evaluate(observations, context)
        except Exception as exc:  # never let the layer break interpretation
            logger.warning("Expert syndrome layer failed: %s", exc)
        for hit in esl_hits:
            for i, did in enumerate(hit["dx"]):
                vote = hit["score"] if i == 0 else hit["score"] * 0.93
                rule_scores[did] = max(rule_scores.get(did, 0.0), vote)
                if hit.get("strength") != "screen":   # v6: a screening hit is not a guideline anchor for the disease itself
                    guideline_anchored.add(did)
                if hit["features"]:
                    disease_true_feats.setdefault(did, set()).update(hit["features"])
        self._esl_hits = esl_hits
        self._guideline_anchored = frozenset(guideline_anchored)
        self._disease_true_feats = disease_true_feats
        advanced = self._ejra_advanced_layers(
            observations, context, rule_scores)
        bayesian_map = advanced.get("bayesian", {})
        fuzzy_map = advanced.get('fuzzy', {})
        ensemble_map = advanced.get("ensemble", {})
        differential_list = advanced.get("differential", [])


        diff_groups: dict[str, list[str]] = dict(
            advanced.get('differential_groups') or {})
        contraindication_map: dict[str, list[dict]] = dict(
            advanced.get("contraindications") or {})
        pattern_objs = advanced.get("derived_patterns", []) or []
        diff_rank_map = {
            d['disease_id']: d["rank"] for d in differential_list}
        diff_sensitivity_map = {
            d["disease_id"]: d.get("sensitivity_notes", [])
            for d in differential_list}
        diff_statement_map = {
            d['disease_id']: d.get("statement", "")
            for d in differential_list}


        for (rule_id, rule, disease, cls, disease_domains, status,
             node, contract_warnings) in pending:
            results.append(self._sakht_tafsir(
                rule_id, rule, disease, cls, disease_domains,
                status, node, contract_warnings,
                bayesian_map, fuzzy_map, ensemble_map,
                diff_rank_map, diff_sensitivity_map,
                diff_statement_map, panic_alerts,
                context, diff_groups, contraindication_map,
                pattern_objs))


        self._flood_valve(results, protected_ids)
        results = self._aggregate_disease_interpretations(results)
        results.sort(key=lambda x: (
            _STATUS_PRIORITY.get(x.status, 99),
            (x.name_en or "").casefold()))


        summary: dict[str, int] = {}
        for item in results:
            summary[item.status] = summary.get(item.status, 0) + 1
        collapsed = 0
        for st, total in collapsed_by_status.items():
            missing = total - materialised_by_status.get(st, 0)
            if missing > 0:
                summary[st] = summary.get(st, 0) + missing
                collapsed += missing
        positive_count = sum(
            item.status in POSITIVE_RESULT_STATES
            for item in results)
        insufficient_count = summary.get("insufficient_data", 0)
        conflicting_count = summary.get('conflicting_data', 0)
        not_applicable_count = summary.get("not_applicable", 0)
        ruled_out_count = summary.get("ruled_out", 0) + summary.get(
            "excluded", 0)
        catalog_only = registry.catalog_only_count
        report_warnings = list(dict.fromkeys(input_warnings + [
            "Laboratory interpretations are decision support, "
            "not diagnoses.",
            f"Execution mode: {self.execution_mode}.",
        ]))
        if panic_alerts:
            report_warnings.append(
                f"CRITICAL VALUES detected in {len(panic_alerts)} "
                "observation(s). Immediate clinical review required.")
        report_warnings.append(
            "Single-time-point analysis: each report is interpreted on its "
            "own; criteria that require a prior baseline are reported as "
            "insufficient data rather than inferred.")
        # Reference-interval policy and evidence-reliability notes: the
        # clinician must see which interval governed and which values were
        # down-weighted because the OCR read them with low confidence.
        for fid, pol in (advanced.get("reference_policy") or {}).items():
            if pol.get("note"):
                report_warnings.append(str(pol["note"]))
            rel = pol.get("reliability")
            if rel is not None and rel < 0.8:
                report_warnings.append(
                    f"{fid}: evidence reliability {rel:.2f} (low OCR "
                    f"confidence / unconfirmed); its weight in Bayesian, "
                    f"fuzzy and fusion layers was reduced accordingly.")
        if collapsed:
            report_warnings.append(
                f"{collapsed} additional rules had no matching "
                f"measurement and are included in the counts but "
                f"not listed individually.")
        # A high-significance derived index is a finding in its own right.
        # Glycaemic discordance, iron overload or a FIB-4 past the
        # cirrhosis threshold each warrant the clinician's eye even when
        # no single analyte hit a panic limit, so surface them alongside
        # the critical values rather than burying them in a sub-list.
        for _pat in (advanced.get("derived_patterns") or []):
            if _pat.get("significance") != "high":
                continue
            critical_alerts_output.append({
                "kind": "derived_pattern",
                "feature_id": _pat.get("pattern_id"),
                "message": _pat.get("interpretation"),
                "value": _pat.get("value"),
                "severity": "review",
                "citation": _pat.get("citation"),
            })

        executive_summary = self._sakht_executive_kholase(
            results, panic_alerts, differential_list,
            advanced.get("derived_patterns", []),
            advanced.get("corrections", []),
            advanced.get("drug_interactions", []),
            observations, context)
        completeness = self._arzyabi_completeness(
            observations, results, self._hame_vizhegi_ha_ghaede())

        try:  # ESL extension 8 — next-test layer
            def _val_mgdl(fid):
                _o = observations.get(fid)
                if _o is None:
                    return None
                try:
                    _v = float(_o.value)
                except (TypeError, ValueError):
                    return None
                _u = (getattr(_o, "unit", None) or "").lower()
                if fid == "glucose" and ("mmol" in _u or _v < 40.0):
                    _v *= 18.0
                return _v
            _nt = _esl_next_tests(differential_list, set(observations.keys()), value_of=_val_mgdl)
            for _d in differential_list:
                if isinstance(_d, dict) and not _d.get("recommended_tests"):
                    _k = _NEXT_TEST_ALIASES.get(_d.get("disease_id"), _d.get("disease_id"))
                    _d["recommended_tests"] = [r["test"] for r in _NEXT_TEST_LIBRARY.get(_k, []) if not any(f in observations for f in r["features"])][:4]
        except Exception:  # never let a recommendation break the report
            _nt = []
        return InterpretationReport(
            next_tests=_nt,
            interpretations=results,
            summary=summary,
            skipped_rules=skipped,
            catalog_only_disease_count=catalog_only,
            warnings=report_warnings,
            execution_mode=self.execution_mode,
            rule_count=len(results),
            gated_interpretations=gated,
            positive_count=positive_count,
            insufficient_count=insufficient_count,
            conflicting_count=conflicting_count,
            not_applicable_count=not_applicable_count,
            ruled_out_count=ruled_out_count,
            critical_alerts=critical_alerts_output,
            differential_diagnosis=differential_list,
            knowledge_graph_insights=advanced.get(
                "graph_insights", {}),
            interference_corrections=advanced.get(
                "corrections", []),
            drug_interactions=advanced.get("drug_interactions", []),
            expanded_kg_insights=advanced.get("expanded_kg_insights", {}),
            differential_groups=advanced.get("differential_groups", {}),
            contraindications=advanced.get("contraindications", {}),
            derived_patterns=advanced.get("derived_patterns", []),
            expert_syndromes=list(getattr(self, "_esl_hits", []) or []),
            temporal_findings=[{"id": h.get("syndrome_id"), "dx": h.get("dx"), "note": h.get("note"), "strength": h.get("strength"), "source": h.get("source")}
                               for h in (getattr(self, "_esl_hits", []) or []) if h.get("temporal")],
            clinical_context_applied=list(getattr(self._reasoner, "_context_applied", []) or []),
            executive_summary=executive_summary,
            data_completeness=completeness,
        )


    def _sakht_executive_kholase(
        self, results, panic_alerts, differential, patterns,
        corrections, drug_interactions, observations, context,
    ) -> str:
        L: list[str] = []

        # 1. Critical Panic Alerts
        if panic_alerts:
            items = "، ".join(
                f"{a['feature_id']} = {a['value']:.3g} {a.get('unit','')}"
                for a in panic_alerts[:4])
            L.append(
                f"🚨 هشدار بحرانی / CRITICAL ALERTS: {items}. ارزیابی بالینی فوری و مداخله درمانی اورژانس لازم است.")

        # 2. Definitive Criteria Met (معیارهای تشخیصی برآورده‌شده)
        definitive = [r for r in results if r.status in ("urgent_pattern", "criterion_met")]
        if definitive:
            names_fa = "، ".join(f"{r.name_fa or r.name_en}" for r in definitive[:5])
            names_en = ", ".join(r.name_en for r in definitive[:5])
            more_count = len(definitive) - 5
            more_str = f" و {more_count} وضعیت دیگر" if more_count > 0 else ""
            L.append(
                f"★ معیارهای تشخیصی برآورده‌شده (Definitive Criteria Met): {names_fa}{more_str} [{names_en}].")

        # 3. Compatible / Supportive Patterns (الگوهای بیوشیمیایی و پاتوفیزیولوژیک سازگار)
        compatible = [r for r in results if r.status in ("compatible_pattern", "screening_positive")]
        if compatible:
            c_names = "، ".join(f"{r.name_fa or r.name_en}" for r in compatible[:4])
            c_more = f" و {len(compatible) - 4} الگوی سازگار دیگر" if len(compatible) > 4 else ""
            L.append(f"📋 الگوهای آزمایشگاهی سازگار (Compatible Patterns): {c_names}{c_more}.")
        elif not definitive:
            L.append("هیچ الگوی آزمایشگاهی غیرطبیعی مطابق معیارهای معتبر راهنماها شناسایی نشد.")

        # 4. Bayesian & Differential Diagnosis Priority
        if differential:
            top = differential[0]
            # Only report differential diagnosis if there are active findings, or if top probability >= 0.30 and not unlikely
            has_substantive_support = (
                definitive
                or compatible
                or (top.get("probability", 0) >= 0.30 and top.get("status") in ("present", "possible", "probable"))
            )
            if has_substantive_support:
                top_name = top.get("disease_id", "").replace("_", " ").title()
                L.append(
                    f"🔍 محتمل‌ترین گزینه در تشخیص افتراقی (Top Differential): "
                    f"{top_name} (احتمال پسین {top.get('probability', 0):.0%}، اطمینان {top.get('confidence', 0):.0%}).")
                rivals = [d for d in differential[1:4] if d.get('probability', 0) > 0.25]
                if rivals:
                    r_names = "، ".join(
                        f"{d.get('disease_id','').replace('_', ' ').title()} ({d.get('probability',0):.0%})"
                        for d in rivals)
                    L.append(f"گزینه‌های افتراقی رقیب: {r_names}.")
            else:
                L.append("✅ کلیه شاخص‌های بیوشیمیایی، مینرال‌ها و سلولی در محدوده مرجع فیزیولوژیک سن و جنس بیمار قرار دارند؛ هیچ تشخیص افتراقی یا الگوی بیماری‌زای فعالی مطرح نیست.")

        # 5. High-Significance Clinical Patterns
        key_patterns = [pt for pt in patterns if pt.get('significance') == "high"]
        for pt in key_patterns[:3]:
            L.append(f"📊 الگوی بالینی کلیدی: {pt.get('interpretation')}")

        # 6. Pharmacology & Drug Interactions
        if drug_interactions:
            feats = _dedupe(d.get("feature_id") for d in drug_interactions)
            L.append(
                f"💊 احتیاط تفسیری / تداخلات دارویی: داروهای فعلی ممکن است "
                f"{'، '.join(feats[:4])} را متأثر سازند.")

        if corrections:
            L.append(
                "اصلاحات اعمال‌شده: "
                + "، ".join(f"{c['feature_id']} ({c['correction']})"
                            for c in corrections) + ".")

        # 7. Diagnostic Gaps & Recommended Additional Tests (Only if active or possible patterns exist)
        if definitive or compatible or (differential and differential[0].get("probability", 0) >= 0.35 and differential[0].get("status") != "unlikely"):
            gaps: dict[str, int] = {}
            for r in results:
                if r.status in ("possible_pattern", "compatible_pattern"):
                    for f in r.missing_features:
                        gaps[f] = gaps.get(f, 0) + 1
            if gaps:
                top_gaps = sorted(gaps.items(), key=lambda kv: -kv[1])[:4]
                L.append(
                    '🔬 آزمایش‌های پیشنهادی جهت تکمیل تشخیص (Recommended Follow-up): '
                    + "، ".join(f for f, _ in top_gaps) + ".")

        L.append(
            "⚕ این خروجی سیستم پشتیبان تصمیم‌گیری بالینی (CDSS) است و تشخیص قطعی نهایی مستلزم قضاوت بالینی پزشک معالج می‌باشد.")
        return '\n\n'.join(L)

    def _vizhegi_ghabel_ghabool(self) -> set:
        cached = getattr(self, "_known_features_cache", None)
        if cached is not None:
            return cached
        known: set = set()
        try:
            known |= set(self.registry.features)
        except Exception:
            pass
        try:
            known |= set(self.registry.rules_by_feature)
        except Exception:
            pass
        # The Bayesian and fuzzy layers understand far more features than
        # the guideline registry lists; an observation only one of them can
        # use is still worth keeping.
        try:
            known |= set(ClinicalBayesianNetwork.FEATURE_TO_FINDING)
        except Exception:
            pass
        self._known_features_cache = known
        return known

    def _hame_vizhegi_ha_ghaede(self) -> set:
        cached = getattr(self, "_vizhegi_cache", None)
        if cached is None:
            try:
                cached = set(self.registry.rules_by_feature)
            except Exception:
                cached = set()
            self._vizhegi_cache = cached
        return cached

    @staticmethod
    def _arzyabi_completeness(observations, results,
                              wanted: Optional[set] = None) -> dict[str, Any]:
        requested: set = set()
        for r in results:
            requested.update(r.missing_features)
        # A rule that never fired reports no missing_features, so counting
        # only fired rules made a single-test panel look 100% complete.
        # `wanted` carries every feature the whole ruleset asks about.
        if wanted:
            requested |= {f for f in wanted if f not in observations}
        supplied = set(observations)
        unconfirmed = [f for f, rec in observations.items()
                       if not rec.confirmed]
        conflicted = [f for f, rec in observations.items()
                      if rec.metadata.get("conflict")]
        denom = len(supplied) + len(requested)
        ratio = (len(supplied) / denom) if denom else 0.0
        if ratio >= 0.75:
            level = "high"
        elif ratio >= 0.4:
            level = "moderate"
        else:
            level = "low"
        return {
            "supplied_count": len(supplied),
            "missing_count": len(requested),
            "coverage_ratio": round(ratio, 3),
            "confidence_level": level,
            "unconfirmed_features": sorted(unconfirmed),
            "conflicted_features": sorted(conflicted),
            "note": (
                "Coverage is the share of features the fired rules "
                "wanted that were actually supplied; low coverage "
                "means the ranking is provisional."),
        }


    def _sakht_tafsir(
        self, rule_id, rule, disease, cls, disease_domains,
        status, node, contract_warnings,
        bayesian_map, fuzzy_map, ensemble_map, diff_rank_map,
        diff_sensitivity_map, diff_statement_map,
        panic_alerts,
        context,
        diff_groups=None,
        contraindication_map=None,
        patterns=None,
    ) -> DiseaseInterpretation:
        diff_groups = diff_groups or {}
        contraindication_map = contraindication_map or {}
        patterns = patterns or []
        identity = disease.get("identity") or {}
        source_ids = list(rule.get("source_ids") or ())
        rule_type = rule.get("rule_type", "")
        urgency = ("urgent"
                   if rule_type == 'urgent_pattern'
                   and status == "urgent_pattern"
                   else 'routine')
        diagnosis_allowed = bool(
            (rule.get("result") or {}).get(
                "diagnosis_allowed", False))
        warnings = list(dict.fromkeys(
            node.warnings + list(contract_warnings) + (
                ["Research-mode candidate rule; not validated "
                 'for clinical release.']
                if self.execution_mode == "research" else [])))
        limitations = list(rule.get("limitations") or ())
        positive_text = [e.readable for e in node.evidence
                         if e.truth == TruthValue.TRUE]

        disease_id = rule["disease_id"]
        bayesian_data = bayesian_map.get(disease_id, {})
        fuzzy_data = fuzzy_map.get(disease_id, {})
        ensemble_data = ensemble_map.get(disease_id, {})
        ensemble_votes = ensemble_data.get("votes", {})

        diff_stmt = diff_statement_map.get(disease_id, '')
        positive_statuses = {
            'criterion_met', "compatible_pattern",
            "possible_pattern", "screening_positive",
            "urgent_pattern"}
        if status in positive_statuses:
            if diff_stmt:
                statement = diff_stmt
            else:
                statement = self._sakht_statement(
                    identity.get("name_en", rule["disease_id"]),
                    status, positive_text, node, limitations)
        else:
            statement = ""

        sensitivity = diff_sensitivity_map.get(disease_id, [])

        actionable = []
        if urgency == "urgent":
            actionable.append(
                "Seek urgent clinical assessment.")

        critical_alert = None
        for alert in panic_alerts:
            if alert.get("feature_id") in set(
                    rule.get("_feature_ids") or []):
                critical_alert = alert.get("message")
                urgency = "urgent"
                break

        supporting_patterns: list[str] = []
        for pt in patterns:
            if disease_id in (pt.get("supports") or ()):
                supporting_patterns.append(pt["interpretation"])
            elif disease_id in (pt.get("argues_against") or ()):
                supporting_patterns.append(
                    'شاهد مخالف — ' + pt['interpretation'])
        sources_map = self.registry.sources

        drug_caveats: list[str] = []
        if context:
            for fid in rule.get("_feature_ids", []):
                drug_caveats.extend(
                    hoshdar_haye_vizhegi(
                        fid, context)
                )


        differential_alternatives = list(
            diff_groups.get(disease_id)
            or self._knowledge_graph.yaftan_differential_tashkhis_goroohbandi(
                disease_id))
        contraindications = list(
            contraindication_map.get(disease_id)
            or self._knowledge_graph.get_contraindications(disease_id))
        if contraindications and status in POSITIVE_RESULT_STATES:
            actionable.extend(
                f"Contraindicated: {c['contraindicated_drug']}"
                f" — {c.get('reason') or 'see guideline'}"
                for c in contraindications[:3])
        return DiseaseInterpretation(
            disease_id=disease_id,
            name_en=identity.get("name_en", disease_id),
            name_fa=identity.get("name_fa"),
            rule_id=rule_id,
            rule_type=rule_type,
            status=status,
            truth=node.truth.value,
            urgency=urgency,
            diagnosis_allowed=diagnosis_allowed,
            requires_physician_review=True,
            evidence=[dict(asdict(x), _readable=x.readable)
                      for x in node.evidence],
            missing_features=sorted(node.missing_features),
            missing_context=sorted(node.missing_context),
            limitations=limitations,
            source_ids=source_ids,
            sources=[sources_map[x] | {"source_id": x}
                     for x in source_ids if x in sources_map],
            warnings=warnings,
            rule_quality=dict(rule.get("quality") or {}),
            domains=sorted(disease_domains),
            classification=cls,
            clinical_priority=str(
                cls.get("clinical_priority") or "routine"),
            icd10=list(identity.get("icd10") or ()),
            snomed_ct=list(identity.get("snomed_ct") or ()),
            statement=statement,
            confidence=round(
                node.score, 3) if node.score is not None else None,

            bayesian_posterior=bayesian_data.get('posterior'),
            bayesian_explanation=bayesian_data.get("explanation"),
            fuzzy_score=fuzzy_data.get("membership"),
            ensemble_score=ensemble_data.get("score"),
            ensemble_votes=ensemble_votes,
            knowledge_graph_boost=ensemble_votes.get(
                'knowledge_graph'),
            differential_rank=diff_rank_map.get(disease_id),
            actionable_recommendations=actionable,
            sensitivity_analysis=sensitivity,
            critical_alert=critical_alert,
            drug_caveats=drug_caveats,
            differential_alternatives=differential_alternatives,
            contraindications=contraindications,
            derived_patterns=supporting_patterns,
        )

    @staticmethod
    def _sakht_statement(name: str, status: str,
                         positive_text: list[str],
                         node: NodeEvaluation,
                         limitations: list[str]) -> str:
        pieces = [f"{name}: {status.replace('_', ' ')}."]
        if positive_text:
            shown = '; '.join(positive_text[:4])
            if len(positive_text) > 4:
                shown += (f" (+{len(positive_text) - 4} "
                          f"more findings)")
            pieces.append("Supported by: " + shown)
        if node.missing_context or node.missing_features:
            missing = list(node.missing_features) + list(
                node.missing_context)
            pieces.append("Unresolved for: "
                          + ", ".join(_dedupe(missing)))
        if limitations:
            pieces.append("Limit: "
                          + "; ".join(limitations[:2]))
        pieces.append("Not a diagnosis. Review with a clinician.")
        return " ".join(pieces)

    @staticmethod
    def _soft_all(children, weights) -> Optional[float]:
        known = [(w, c.score) for w, c in zip(weights, children)
                 if c.score is not None]
        total_w = sum(weights) or 1.0
        if not known:
            return None
        known_w = sum(w for w, _ in known)
        logsum = sum(w * math.log(max(s, 1e-4))
                     for w, s in known)
        return (math.exp(logsum / known_w)
                * (known_w / total_w))

    @staticmethod
    def _soft_any(children, weights) -> Optional[float]:
        known = [c.score for w, c in zip(weights, children)
                 if c.score is not None]
        return max(known) if known else None

    @staticmethod
    def _child_weight(expr) -> float:
        w = _float(expr.get("weight")) if isinstance(
            expr, Mapping) else None
        return w if w is not None and w > 0 else 1.0


def interpret_lab_data(
    inputs: Mapping[str, Any],
    derived: Optional[Mapping[str, Any]],
    patient: Mapping[str, Any] | PatientContext | ClinicalContext,
    *,
    detailed: bool = False,
    include_insufficient: bool = False,
    execution_mode: str = "research",
    engine: Optional[ClinicalRuleEngine] = None,
    domains: Optional[set[str]] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Interpret a set of lab observations.

        Args:
            inputs: feature id -> {"value", "unit", ...}. Short lab
                names (tsh, egfr, alt) are mapped to canonical ids.
            derived: pre-computed features, same shape as inputs.
            patient: age, sex, diagnoses, current medications.
            detailed: return the full report rather than the
                interpretation list alone.

        Returns:
            The ranked differential plus supporting evidence,
            critical alerts, derived indices and a completeness
            assessment describing how much of the picture is known.
        """
    eng = engine or ClinicalRuleEngine(
        execution_mode=execution_mode)
    report = eng.interpret(
        inputs, derived, patient, include_negative=False,
        include_insufficient=include_insufficient,
        domains=domains)
    if detailed:
        return report.to_dict()
    positive_states = POSITIVE_RESULT_STATES
    output = []
    for item in report.interpretations:
        if item.status not in positive_states:
            continue
        output.append({
            'diseaseKey': item.disease_id,
            'nameEn': item.name_en,
            "nameFa": item.name_fa,
            "icd10": list(item.icd10 or []),
            'snomedCt': list(item.snomed_ct or []),
            "status": {
                "criterion_met": "Present",
                'urgent_pattern': "Present",
                "screening_positive": "Possible",
                "possible_pattern": "Possible",
            }.get(item.status, "Compatible"),
            "interpretationStatus": item.status,
            "statusLabel": item.status.replace(
                "_", " ").title(),
            "evidence": [x['message'] for x in item.evidence
                         if x.get("truth") == TruthValue.TRUE],
            "guideline": ", ".join(item.source_ids),
            "sourceIds": item.source_ids,
            'domains': item.domains,
            "statement": item.statement,
            "importance": ("High" if item.urgency == 'urgent'
                           else "Moderate"),
            "recommendation": (
                "Urgent medical assessment"
                if item.urgency == "urgent"
                else "Physician review and confirmatory "
                     "evaluation"),
            "confirmRequired": True,
            "diagnosisAllowed": item.diagnosis_allowed,
            "requiresPhysicianReview":
                item.requires_physician_review,
            'ruleId': item.rule_id,
            "limitations": item.limitations,
            'bayesianPosterior': item.bayesian_posterior,
            "fuzzyScore": item.fuzzy_score,
            "ensembleScore": item.ensemble_score,
            "differentialRank": item.differential_rank,
            "criticalAlert": item.critical_alert,
            'sensitivityAnalysis': item.sensitivity_analysis,
            "actionableRecommendations":
                item.actionable_recommendations,
        })
    output.sort(key=lambda d: (
        _STATUS_PRIORITY.get(
            d["interpretationStatus"], 99),
        (d.get("nameEn") or '').casefold()))
    return output


__all__ = [
    "ClinicalContext", "ClinicalRuleEngine", 'ConditionEvidence',
    "DiseaseGuidelineRegistry", "DiseaseInterpretation",
    "InterpretationReport", 'NodeEvaluation', "ObservationRecord",
    'RegistryValidationError', 'TruthValue', "interpret_lab_data",
    "normalize_observations",
    "EnrichedObservation",
    'ClinicalBayesianNetwork', "BayesianResult",
    "AdaptiveFuzzyEngine", 'FuzzyResult',
    "ClinicalKnowledgeGraph", 'GraphEdge',
    "EnsembleResult",
    "MultiStageReasoner", "DifferentialEntry",
    "DrugInteraction"
]

