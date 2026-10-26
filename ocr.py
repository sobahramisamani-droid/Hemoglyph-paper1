from __future__ import annotations
import sys
from pathlib import Path
import base64
import difflib
import hashlib
import io
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
import threading
import time
from array import array
from collections import OrderedDict
from typing import (Any, Callable, Iterable, Iterator, Mapping, Optional,
                    Sequence)

from cache_registry import bargozari_registry, shared_object
from calcu import (
    CalculationError,
    convert_unit,
)

logger = logging.getLogger(__name__)

_cv2 = _np = _Image = _fitz = _PaddleOCR = _pytesseract_mod = None

def _need_cv2():
    global _cv2
    if _cv2 is None:
        try:
            import cv2 as _m; _cv2 = _m
        except Exception:
            pass
    return _cv2

def _need_np():
    global _np
    if _np is None:
        try:
            import numpy as _m; _np = _m
        except Exception:
            pass
    return _np

def _need_pil():
    global _Image
    if _Image is None:
        try:
            from PIL import Image as _m; _Image = _m
        except Exception:
            pass
    return _Image

def _need_fitz():
    global _fitz
    if _fitz is None:
        try:
            import pymupdf as _m; _fitz = _m
        except ImportError:
            try:
                import fitz as _m; _fitz = _m
            except Exception:
                pass
    return _fitz

def _need_paddle():
    global _PaddleOCR
    if _PaddleOCR is None:
        try:
            from paddleocr import PaddleOCR as _m; _PaddleOCR = _m
        except Exception:
            pass
    return _PaddleOCR

def _tesseract_binary() -> Optional[str]:
    try:
        cand = shutil.which('tesseract')
        if cand:
            return cand
    except Exception:
        pass
    exe_dir = Path(sys.executable).resolve().parent
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        str(exe_dir / "bin" / "tesseract.exe"),
        str(exe_dir / "tesseract.exe"),
        str(exe_dir / "bin" / "tesseract" / "tesseract.exe"),
        str(Path(__file__).parent / "bin" / "tesseract.exe"),
        str(Path(__file__).parent / "bin" / "tesseract" / "tesseract.exe"),
        str(Path.cwd() / "bin" / "tesseract.exe"),
        str(Path.cwd() / "tesseract.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _need_pytesseract():
    global _pytesseract_mod
    if _pytesseract_mod is None:
        try:
            import pytesseract as _m
            tb = _tesseract_binary()
            if tb:
                _m.pytesseract.tesseract_cmd = tb
            # Probe the binary once. pytesseract raises SystemExit (a
            # BaseException) for a version string it cannot parse, e.g. the
            # ancient "tesseract 3.05.00dev" build some PDF tools ship on
            # PATH; left uncaught it terminates the whole application.
            try:
                import io as _io, contextlib as _ctx
                with _ctx.redirect_stderr(_io.StringIO()):
                    ver = _m.get_tesseract_version()
                try:
                    major = int(str(ver).split(".")[0])
                except Exception:
                    major = 0
                if major < 4:
                    logger.warning("Tesseract %s is too old for pytesseract (need >= 4); local OCR disabled.", ver)
                    _m = False
            except BaseException as exc:  # SystemExit / TesseractNotFoundError
                logger.warning("Tesseract binary unusable (%s); local OCR disabled.", exc)
                _m = False
            _pytesseract_mod = _m
        except Exception:
            pass
    return _pytesseract_mod or None


try:
    from _ocr_support import (
        DIGIT_MAP as _SUP_DIGIT_MAP,
        CHAR_MAP as _SUP_CHAR_MAP,
        SAFE_PUNCT as _SUP_SAFE_PUNCT,
        CURATED_ABBREVIATIONS as _SUP_CURATED_ABBREVIATIONS,
        STATIC_OCR_ERRORS as _SUP_STATIC_OCR_ERRORS,
        UNIT_MISREADS as _SUP_UNIT_MISREADS,
        LINE_MISREADS as _SUP_LINE_MISREADS,
        UNIT_ALIASES as _SUP_UNIT_ALIASES,
        UNIT_CASE_CANONICAL as _SUP_UNIT_CASE_CANONICAL,
        EXACT_DISAMBIGUATION as _SUP_EXACT_DISAMBIGUATION,
        QUALITATIVE_NAME_MAP as _SUP_QUALITATIVE_NAME_MAP,
        CATEGORICAL as _SUP_CATEGORICAL,
        QUALITATIVE as _SUP_QUALITATIVE,
        NOISE_WORDS as _SUP_NOISE_WORDS,
        FLAG_WORDS as _SUP_FLAG_WORDS,
        FLAG_CLEAN_WORDS as _SUP_FLAG_CLEAN_WORDS,
        COUNT_CANON as _SUP_COUNT_CANON,
        UNIT_DIMENSION as _SUP_UNIT_DIMENSION,
        PERSIAN_UNIT_ALIASES as _SUP_PERSIAN_UNIT_ALIASES,
        UNIT_PATTERN as _SUP_UNIT_PATTERN,
        build_ocr_block as _SUP_build_ocr_block,
    )
except Exception:
    _SUP_DIGIT_MAP = {"۰": "0", "۱": "1", '۲': "2", "۳": "3", "۴": "4", "۵": '5',
                      "۶": '6', '۷': "7", "۸": "8", '۹': '9', "٠": "0", "١": "1",
                      "٢": "2", "٣": "3", "٤": "4", '٥': "5", '٦': "6", '٧': "7",
                      "٨": "8", "٩": "9", "٫": ".", "٬": ","}
    _SUP_CHAR_MAP = {"ي": "ی", "ك": "ک", "ى": "ی", "ئ": "ی", "ة": "ه", "ؤ": 'و',
                     "إ": "ا", "أ": "ا", "آ": "ا", "ھ": 'ه', 'ٱ': "ا", "ے": 'ی'}
    _SUP_SAFE_PUNCT = ['[', ']', '{', '}', '<', '>', '!', '?', '"', "'", '`', '~', '@', '#', '$', '%', '^', '&', '*', '\\', '|', ';', ':', '=', '+', ',', '’', '‘', '“', '”', '№', '_', '·', '•', '°', '×', '±']
    _SUP_CURATED_ABBREVIATIONS = {}
    _SUP_STATIC_OCR_ERRORS = {}
    _SUP_UNIT_MISREADS = []
    _SUP_LINE_MISREADS = []
    _SUP_UNIT_ALIASES = {}
    _SUP_UNIT_CASE_CANONICAL = {}
    _SUP_EXACT_DISAMBIGUATION = {}
    _SUP_QUALITATIVE_NAME_MAP = {}
    _SUP_CATEGORICAL = []
    _SUP_QUALITATIVE = {}
    _SUP_NOISE_WORDS = []
    _SUP_FLAG_WORDS = {}
    _SUP_FLAG_CLEAN_WORDS = []
    _SUP_COUNT_CANON = {}
    _SUP_UNIT_DIMENSION = {}
    _SUP_PERSIAN_UNIT_ALIASES = {}
    _SUP_UNIT_PATTERN = r"(?!)"
    _SUP_build_ocr_block = lambda: {}

_DIGIT_MAP = str.maketrans(dict(_SUP_DIGIT_MAP))
_CHAR_MAP = str.maketrans(dict(_SUP_CHAR_MAP))
_SAFE_PUNCT = set(_SUP_SAFE_PUNCT)

def unicode_nfkc(s: str) -> str:
    # NFKC folds the full-width digits and ligature characters that
    # lab-report PDFs are full of.
    return unicodedata.normalize("NFKC", s)

def normalize_digits(s: str) -> str:
    return s.translate(_DIGIT_MAP)

def normalize_persian_arabic_chars(s: str) -> str:
    return s.translate(_CHAR_MAP)

def strip_safe_punctuation(s: str) -> str:
    return "".join(ch for ch in s if ch not in _SAFE_PUNCT)

def normalize_whitespace(s: str) -> str:
    return " ".join(s.split())

def casefold(s: str) -> str:
    return s.casefold()

def trim(s: str) -> str:
    return s.strip()

def normalize_zwnj(s: str) -> str:
    return s.replace("\u200c", ' ')


_BIDI_CONTROL_RE = re.compile(r"[\u200e\u200f\u202a-\u202e\u2060-\u2069]")


def strip_bidi_controls(s: str) -> str:
    return _BIDI_CONTROL_RE.sub("", s)


class TextNormalizer:
    def __init__(self, pipeline: Optional[Sequence[str]] = None):
        self.pipeline = list(pipeline or [
            "unicode_nfkc", 'trim', "casefold", "normalize_whitespace",
            "normalize_persian_arabic_chars", "normalize_digits", 'strip_safe_punctuation',
        ])
        self._OPS: dict[str, Callable[[str], str]] = {
            "unicode_nfkc": unicode_nfkc, 'trim': trim, "casefold": casefold,
            'normalize_whitespace': normalize_whitespace,
            "normalize_persian_arabic_chars": normalize_persian_arabic_chars,
            "normalize_digits": lambda t: normalize_digits(t),
            "strip_safe_punctuation": strip_safe_punctuation,
        }

    def __call__(self, text: str) -> str:
        out = str(text)
        for op in self.pipeline:
            fn = self._OPS.get(op)
            if fn:
                out = fn(out)
        return out

    def for_nam(self, text: str) -> str:
        return self(text)

    def yeksansazi(self, text: str) -> str:
        return self(text)

    def for_meghdar(self, text: str) -> str:
        out = unicode_nfkc(str(text))
        out = normalize_persian_arabic_chars(out)
        out = normalize_digits(out)
        return out.strip()


def normalize_report_units(text: str, aliases: Optional[Mapping[str, str]] = None) -> str:
    if not text:
        return text
    amap = dict(aliases or {})
    out = []
    for line in text.splitlines():
        normalized = normalize_whitespace(line.replace("\u200c", " "))
        for key, value in amap.items():
            if re.search(r'[A-Za-z]', key):
                normalized = re.sub(r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])', value, normalized, flags=re.IGNORECASE)
            else:
                normalized = normalized.replace(key, value)
        out.append(normalized)
    return "\n".join(out)

def normalize_extracted_text(text: str, aliases: Optional[Mapping[str, str]] = None) -> str:
    if not text:
        return text
    out = []
    for line in text.splitlines():
        line = strip_bidi_controls(line)
        line = normalize_digits(line)
        line = normalize_persian_arabic_chars(line)
        line = normalize_zwnj(line)
        line = normalize_report_units(line, aliases)
        out.append(line)
    return "\n".join(out)

def _yeksansazi_model_line(line: str) -> str:
    return re.sub(r"[ \t]+", " ", line).strip()


_GLYPH_DIGIT_MAP = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1"})
_GLYPH_NUM_RE = re.compile(r"(?<![A-Za-z0-9.,])(\d[\dOoIl|]*|[OoIl|]+\d[\dOoIl|]*)(?![A-Za-z0-9])")
_GLYPH_FRAC_RE = re.compile(r"(?<=\d[.,])[Oo]+(?![A-Za-z0-9])")
_GLYPH_NAME_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]{2,}[015][A-Za-z]{2,})(?![A-Za-z0-9])")
_GLYPH_NAME_SAFE = frozenset({
    "hba1c", "hgba1c", "apoa1", "apob100", "igg4", "ca125", "ca153", "ca199", "ca724", "cd4", "cd8",
    "il6", "il1", "pro1", "fe2", "hbe1", "he4", "sf1", "p53", "sp1", "a1at", "b12", "cyp2d6",
})
_GLYPH_NAME_MAP = str.maketrans({"0": "o", "1": "l", "5": "s"})


def _repair_numeric_glyphs(line: str) -> str:
    """OCR commonly reads 0 as O and 1 as l/I inside numbers ("1O.8", "8O-1OO",
    "1O^3/uL"). Repair only tokens that are clearly numeric so that analyte
    names such as HbA1c, B12 or CD4 are never touched."""
    def _num(m):
        tok = m.group(1)
        if not any(ch.isdigit() for ch in tok):
            return tok
        return tok.translate(_GLYPH_DIGIT_MAP)
    line = _GLYPH_NUM_RE.sub(_num, line)
    line = _GLYPH_FRAC_RE.sub(lambda m: "0" * len(m.group(0)), line)

    def _name(m):
        tok = m.group(1)
        if tok.casefold() in _GLYPH_NAME_SAFE or len(tok) < 6:
            return tok
        if sum(ch.isdigit() for ch in tok) != 1:
            return tok
        return tok.translate(_GLYPH_NAME_MAP)
    return _GLYPH_NAME_RE.sub(_name, line)


# Tumour markers written with a space ("CA 125 20 U/mL") were parsed as calcium=125.
_CA_MARKER_RE = re.compile(r"\bCA\s*[- ]?\s*(125|19[\s-]?9|15[\s-]?3|72[\s-]?4|27[\s-]?29|50)\b(?!\s*%)", re.IGNORECASE)
# A leading "Mg" is magnesium, not the unit milligram ("Mg 0.8 mmol/L").
_MG_LEAD_RE = re.compile(r"^(\s*)Mg(?:\+\+|2\+)?(?=\s*[:=]?\s*[+-]?\d)")
# Element symbols that the unit grammar otherwise swallows as a unit token.
_ELEMENT_LEAD_RE = re.compile(r"^(\s*)(Fe|Zn|Cu|Se|Li|Pb|Hg|As|Al)(?:\+\+|2\+|3\+)?(?=\s*[:=]?\s*[+-]?\d)")
_ELEMENT_NAMES = {"fe": "Iron", "zn": "Zinc", "cu": "Copper", "se": "Selenium", "li": "Lithium",
                  "pb": "Lead", "hg": "Mercury", "as": "Arsenic", "al": "Aluminium"}
# Urine microscopy counted "/hpf" must never become blood WBC/RBC.
_HPF_RE = re.compile(r"^(\s*)(WBC|RBC|W\.B\.C|R\.B\.C|Leukocytes?|Erythrocytes?)\b(?=.*?/\s*[hl]pf)", re.IGNORECASE)
# Numeric serum hCG (mIU/mL, IU/L) is the quantitative assay, not the urine strip.
_HCG_QUANT_RE = re.compile(r"^(\s*)(?:serum\s+)?(?:total\s+)?(?:beta|b|β)?[\s-]*hcg\b(?=\s*(?:\(serum\)|quantitative|titer)?\s*[:=]?\s*[+-]?\d[\d.,]*\s*(?:m?iu/m?l|u/l))", re.IGNORECASE)
_BLOOD_GROUP_RE = re.compile(r"^(\s*)(blood\s*(?:group|type)|abo(?:/rh)?|گروه\s*خونی?)\s*[:=]?\s*(A|B|AB|O)\s*(\+|-|pos(?:itive)?|neg(?:ative)?|positive|negative)?\s*$", re.IGNORECASE)


def _repair_context_names(line: str) -> str:
    l = _CA_MARKER_RE.sub(lambda m: "CA-" + re.sub(r"[\s-]", "-", m.group(1)), line)
    l = _MG_LEAD_RE.sub(r"\1Magnesium", l)
    l = _ELEMENT_LEAD_RE.sub(lambda m: m.group(1) + _ELEMENT_NAMES[m.group(2).lower()], l)
    l = _HPF_RE.sub(lambda m: m.group(1) + "Urine " + m.group(2).replace(".", "").upper(), l)
    l = _HCG_QUANT_RE.sub(r"\1Beta hCG tumor marker", l)
    m = _BLOOD_GROUP_RE.match(l)
    if m:
        rh = (m.group(4) or "").lower()
        rh = "+" if rh.startswith(("+", "pos")) else ("-" if rh.startswith(("-", "neg")) else "")
        l = f"{m.group(1)}Blood Group: {m.group(3).upper()}{rh}"
    return l


def repair_ocr_matn(text: str, support: "OCRSupport") -> str:
    if not text:
        return text
    text = "\n".join(_repair_numeric_glyphs(l) for l in text.splitlines())
    text = "\n".join(_repair_context_names(l) for l in text.splitlines())
    if not (support.line_misreads or support.unit_misreads):
        return text
    out: list[str] = []
    for line in text.splitlines():
        l = line
        for pat, rep in support.line_misreads:
            l = re.sub(pat, rep, l, flags=re.IGNORECASE)
        for pat, rep in support.unit_misreads:
            l = re.sub(pat, rep, l, flags=re.IGNORECASE)
        l = _repair_colon_decimals(l)
        l = _repair_comma_decimals(l)
        out.append(l)
    return "\n".join(out)


def _dim_norm(s: str) -> str:
    return str(s).casefold().replace("\u03bc", "\u00b5")


_COUNT_PREFIX = {
    "": 0, "1": 0, "cells": 0, "cell": 0, "10^0": 0,
    "k": 3, "thou": 3, "thous": 3, "thousand": 3, "thousands": 3, "10^3": 3,
    "lakh": 5, "lakhs": 5, "lac": 5, "lacs": 5,
    "m": 6, "mil": 6, "mill": 6, "million": 6, "millions": 6, "10^6": 6,
    "b": 9, "bil": 9, "billion": 9, "g": 9, "10^9": 9,
    "t": 12, "tril": 12, "trillion": 12, "10^12": 12,
}
_COUNT_DENOM = {"µl": 6, "ul": 6, "mcl": 6, "mm3": 6, "mm^3": 6, "mm³": 6, "cumm": 6, "cmm": 6,
                "cu.mm": 6, "cu.mm.": 6, "nl": 9, "ml": 3, "dl": 1, "l": 0}
_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


_EASTERN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_QUALIFIER_RE = re.compile(r"^\s*(<=|>=|≤|≥|<|>|less than|greater than|under|over|up to)\s*", re.I)
_NUM_TOKEN_RE = re.compile(r"^([-+]?\d[\d.,]*|[-+]?[.,]\d+)")
_QUALIFIER_MAP = {"less than": "<", "under": "<", "up to": "<=", "greater than": ">", "over": ">", "≤": "<=", "≥": ">="}


def _parse_value_cell(value: Any, unit: Optional[str]) -> tuple[Optional[float], Optional[str], Optional[str], str]:
    """Parse one structured 'value' cell.

    Returns (number, unit, qualifier, remainder):
      number     float or None
      unit       the given unit, or a unit found glued to the number
                 ("13.5 g/dL", "5.7%") when none was given
      qualifier  "<", "<=", ">", ">=" for censored results ("<0.5")
      remainder  text that was not consumed (qualitative words etc.)
    Decimal comma ("7,1") and thousands comma ("1,250") are told apart by
    digit grouping; Persian/Arabic digits and the Arabic decimal separator
    are accepted."""
    if value is None:
        return None, unit, None, ""
    if isinstance(value, bool):
        return None, unit, None, str(value)
    if isinstance(value, (int, float)):
        return float(value), unit, None, ""
    t = str(value).translate(_EASTERN_DIGITS).replace("\u066b", ".").replace("\u060c", ",").strip()
    t = t.replace("\u2212", "-")                          # unicode minus
    qual = None
    m = _QUALIFIER_RE.match(t)
    if m:
        q = m.group(1).lower()
        qual = _QUALIFIER_MAP.get(q, q)
        t = t[m.end():].strip()
    m = _NUM_TOKEN_RE.match(t)
    if not m:
        return None, unit, qual, t
    tok, rest = m.group(1), t[m.end():].strip()
    tok = tok.rstrip(".,")
    if "," in tok and "." in tok:
        # whichever separator comes last is the decimal mark
        if tok.rfind(",") > tok.rfind("."):
            tok = tok.replace(".", "").replace(",", ".")
        else:
            tok = tok.replace(",", "")
    elif "," in tok:
        parts = tok.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            tok = parts[0] + "." + parts[1]                # 7,1 -> 7.1
        elif all(len(p) == 3 for p in parts[1:]):
            tok = "".join(parts)                           # 1,250 -> 1250
        else:
            tok = parts[0] + "." + "".join(parts[1:])
    elif tok.count(".") > 1:
        tok = tok.replace(".", "")                         # 1.250.000 style (all thousands)
    try:
        num = float(tok)
    except ValueError:
        return None, unit, qual, t
    if not unit and rest:
        cand = rest.split()[0] if not rest.startswith("%") else "%"
        if re.fullmatch(r"[%A-Za-zµμ°/^*0-9.\-³⁹]{1,14}", cand):
            unit = cand
            rest = rest[len(cand):].strip() if not rest.startswith("%") else rest[1:].strip()
    return num, unit, qual, rest


_RANGE_LIKE_RE = re.compile(r"^\s*[<>≤≥]?\s*\d[\d.,]*\s*(?:-|–|—|to|~)\s*\d[\d.,]*\s*$", re.I)
_NUMBER_LIKE_RE = re.compile(r"^\s*[<>≤≥]?\s*[-+]?\d[\d.,]*\s*%?\s*$")
_ROW_KEY_ALIASES = {
    "test_name": ("test_name", "name", "test", "parameter", "analyte", "item", "investigation", "label"),
    "value": ("value", "result", "observed", "observed_value", "reading"),
    "unit": ("unit", "units", "uom"),
    "flag": ("flag", "abnormal", "indicator", "h_l", "status"),
    "reference_range": ("reference_range", "reference", "ref_range", "range", "normal_range", "reference_interval",
                        "biological_reference_interval", "ref"),
}


def _repair_json_text(t: str) -> str:
    """Make common vision-model JSON mistakes parseable: smart quotes,
    single-quoted strings, Python literals, NaN, comments, trailing commas,
    unquoted keys. Only syntax is touched, never values."""
    t = t.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    t = re.sub(r"//[^\n]*", "", t)
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    # single-quoted strings -> double-quoted (not touching apostrophes inside double quotes)
    out, in_dq, i = [], False, 0
    while i < len(t):
        ch = t[i]
        if ch == '"' and (i == 0 or t[i - 1] != "\\"):
            in_dq = not in_dq
            out.append(ch)
        elif ch == "'" and not in_dq:
            j = i + 1
            while j < len(t) and t[j] != "'":
                j += 1
            inner = t[i + 1:j].replace('"', '\\"')
            out.append('"' + inner + '"')
            i = j
        else:
            out.append(ch)
        i += 1
    t = "".join(out)
    t = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*)(\s*:)", lambda m: f'{m.group(1)}"{m.group(2).strip()}"{m.group(3)}', t)
    t = re.sub(r"\b(True)\b", "true", t)
    t = re.sub(r"\b(False)\b", "false", t)
    t = re.sub(r"\b(None|NaN|nan|undefined)\b", "null", t)
    t = re.sub(r",\s*([}\]])", r"\1", t)
    return t


def _normalize_structured_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Canonicalise key spellings and undo the two column shifts vision
    models make most often: the reference interval placed in `value` (and
    the result in `reference_range`), and a unit string placed in `value`."""
    low = {str(k).strip().lower().replace(" ", "_"): v for k, v in row.items()}
    out: dict[str, Any] = {}
    for canon, aliases in _ROW_KEY_ALIASES.items():
        for a in aliases:
            if a in low and low[a] not in (None, ""):
                out[canon] = low[a]
                break
    known = set(sum(_ROW_KEY_ALIASES.values(), ()))
    for k, v in row.items():                       # keep private / unknown keys (e.g. _agreement)
        if str(k).startswith("_") or str(k).strip().lower().replace(" ", "_") not in known:
            out.setdefault(str(k), v)
    val, ref = out.get("value"), out.get("reference_range")
    if isinstance(val, str) and _RANGE_LIKE_RE.match(val) and (
            ref is None or (isinstance(ref, (int, float)) or (isinstance(ref, str) and _NUMBER_LIKE_RE.match(ref)))):
        out["value"], out["reference_range"] = ref, val
        out["_column_shift"] = "value<->reference_range"
    unit = out.get("unit")
    if isinstance(val, str) and not _NUMBER_LIKE_RE.match(val) and not _RANGE_LIKE_RE.match(val) \
            and isinstance(unit, (int, float, str)) and unit not in (None, "") \
            and _NUMBER_LIKE_RE.match(str(unit)) and re.search(r"[A-Za-zµ%/]", val):
        out["value"], out["unit"] = unit, val
        out["_column_shift"] = "value<->unit"
    return out


def _scale_mismatch_against_reference(value: float, lo: Optional[float], hi: Optional[float]) -> Optional[float]:
    """If the value sits a power of ten away from the row's own printed
    interval (a lost or extra decimal point / thousands separator), return
    the rescaled value that falls inside [lo/3, hi*3]; else None."""
    if lo is None or hi is None or hi <= lo or lo < 0 or value <= 0:
        return None
    if lo / 3.0 <= value <= hi * 3.0:
        return None
    for f in (0.1, 10.0, 0.01, 100.0, 0.001, 1000.0):
        v = value * f
        if lo / 3.0 <= v <= hi * 3.0:
            return v
    return None


def _parse_count_unit(u: str) -> Optional[tuple[str, float]]:
    """Dimensional parse of a cell-count unit -> (canonical unit, factor).

    Handles every spelling family (K/uL, thou/mm3, x10^3/µL, 10e6/uL,
    10⁹/L, mil/cumm, lakh/cumm, cells/µL, /µL ...) by multiplying the
    prefix exponent with the per-volume exponent (1 µL = 1e-6 L), instead of
    a spelling table that can only ever be incomplete. Returns None for
    anything that is not a count per volume."""
    raw = str(u).translate(_SUPERSCRIPT).replace(" ", "")
    t = raw.casefold().replace("\u03bc", "µ")
    t = t.replace("×", "x").replace("*", "^").replace("10e", "10^").replace("10^^", "10^")
    t = re.sub(r"^x", "", t)
    t = re.sub(r"^10(\d{1,2})/", r"10^\1/", t)          # "103/ul" (lost caret)
    if "/" not in t:
        return None
    num, _, den = t.partition("/")
    den = den.rstrip(".")
    if den not in _COUNT_DENOM:
        return None
    exp = _COUNT_PREFIX.get(num)
    if exp is None:
        m = re.fullmatch(r"10\^(\d{1,2})", num)
        if not m:
            return None
        exp = int(m.group(1))
    # Single-letter SI prefixes are only cell-count notation when written
    # as capitals against a litre-type denominator (European "G/L" = 1e9/L,
    # "T/L" = 1e12/L). Lower-case "g/l", "g/dl", "mg/..." are mass units.
    if num in ("g", "t", "b", "m", "k") and den in ("l", "dl", "ml", "nl"):
        raw_num = raw.split("/", 1)[0]
        if raw_num != raw_num.upper() or num in ("m", "k", "b"):
            return None
    total = exp + _COUNT_DENOM[den]                     # per litre
    if total == 12:
        return ("10^12/L", 1.0)
    if total == 9:
        return ("10^9/L", 1.0)
    if 0 <= total <= 15:
        return ("10^9/L", 10.0 ** (total - 9))
    return None


class OCRSupport:

    def __init__(self, block: Optional[Mapping[str, Any]] = None):
        if block is None:
            try:
                b: dict[str, Any] = _SUP_build_ocr_block()
            except Exception:
                b = {}
        else:
            b = dict(block)

        sup_pat = str(_SUP_UNIT_PATTERN or "").strip()
        b_pat = str(b.get("unit_pattern") or "").strip()
        if sup_pat and b_pat and sup_pat != b_pat:
            self.unit_pattern = f"(?:{sup_pat})|(?:{b_pat})"
        else:
            self.unit_pattern = sup_pat or b_pat or r"(?!)"

        self.units: list[dict[str, Any]] = [dict(u) for u in (b.get("units") or [])]

        u_alias = dict(b.get("unit_alias") or {})
        u_alias.update(_SUP_UNIT_ALIASES)
        self.unit_alias: dict[str, str] = {
            _dim_norm(k): str(v) for k, v in u_alias.items()}

        self.unit_case_canonical: dict[str, str] = {
            str(k).upper().replace(" ", ""): str(v)
            for k, v in (b.get("unit_case_canonical") or {}).items()}

        u_dim = dict(b.get("unit_dimension") or {})
        u_dim.update(_SUP_UNIT_DIMENSION)
        self.unit_dimension: dict[str, str] = {
            _dim_norm(k): str(v) for k, v in u_dim.items()}
        self.count_canon: dict[str, tuple[str, float]] = {
            _dim_norm(k): (str(v[0]), float(v[1]))
            for k, v in (b.get("count_canon") or {}).items()}
        self.count_fallbacks: list[tuple[str, str, float]] = [
            (str(p), str(c), float(f)) for p, c, f in (b.get("count_fallbacks") or [])]

        self.flags: dict[str, str] = {
            str(k).casefold(): str(v) for k, v in (b.get('flags') or {}).items()}
        self.flag_clean: set[str] = {str(x).casefold() for x in (b.get("flag_clean") or [])}
        qual = dict(_SUP_QUALITATIVE)
        qual.update(b.get("qualitative") or {})
        self.qualitative: dict[str, str] = {
            str(k).casefold(): str(v) for k, v in qual.items()}
        self.categorical: set[str] = {str(x).casefold() for x in (b.get("categorical") or [])}
        self.noise_words: set[str] = {str(x).casefold() for x in (b.get('noise_words') or [])}
        self.noise_token_re = re.compile(str(b.get("noise_token_pattern") or r"(?!)"), re.IGNORECASE)
        self.name_noise_re = re.compile(str(b.get("name_noise_pattern") or r"(?!)"), re.IGNORECASE)
        self.time_unit_name_re = re.compile(str(b.get("time_unit_name_re") or r"(?!)"), re.IGNORECASE)
        cur_abbr = {}
        for k, v in _SUP_CURATED_ABBREVIATIONS.items():
            cur_abbr[k] = list(v)
        for k, v in (b.get("curated_abbreviations") or {}).items():
            lst = cur_abbr.setdefault(k, [])
            for item in v:
                if item not in lst:
                    lst.append(item)
        self.curated_abbreviations: dict[str, list[str]] = {
            str(k): [str(x) for x in v] for k, v in cur_abbr.items()}

        stat_err = dict(b.get("static_errors") or {})
        stat_err.update(_SUP_STATIC_OCR_ERRORS)
        self.static_errors: dict[str, str] = {
            str(k).casefold(): str(v) for k, v in stat_err.items()}

        disam = dict(b.get("disambiguation") or {})
        disam.update(_SUP_EXACT_DISAMBIGUATION)
        self.disambiguation: dict[str, Any] = {
            str(k): v for k, v in disam.items()}

        qnm = dict(_SUP_QUALITATIVE_NAME_MAP)
        qnm.update(b.get("qualitative_name_map") or {})
        self.qualitative_name_map: dict[str, str] = {
            str(k).casefold(): str(v) for k, v in qnm.items()}

        p_unit = dict(_SUP_PERSIAN_UNIT_ALIASES)
        p_unit.update(b.get("persian_unit_aliases") or {})
        self.persian_unit_aliases: dict[str, str] = {
            str(k): str(v) for k, v in p_unit.items()}

        self._unit_hint = re.compile(self.unit_pattern, re.IGNORECASE)

        self.unit_misreads: list[tuple[str, str]] = [
            (str(p), str(r)) for p, r in (b.get("unit_misreads") or [])]
        self.line_misreads: list[tuple[str, str]] = [
            (str(p), str(r)) for p, r in (b.get('line_misreads') or [])]

    @classmethod
    def from_registry(cls, payload: Optional[Mapping[str, Any]]) -> "OCRSupport":
        block = payload.get("ocr") if isinstance(payload, dict) else None
        return cls(block)


    def is_vahed(self, tok: str) -> bool:
        if not tok:
            return False
        t = str(tok).strip().rstrip(":,;.-")
        if not t:
            return False
        return bool(re.fullmatch(self.unit_pattern, t, re.IGNORECASE))

    def vahed_canonical(self, unit: Optional[str]) -> Optional[str]:
        if unit is None:
            return None
        text = str(unit).strip()
        if not text:
            return None
        text = (text.replace("[", "").replace("]", "")
                     .replace('{', "").replace("}", "").replace("_", ""))
        key = _dim_norm(text).replace(" ", "").replace("\u200e", "").replace("\u200f", "")
        if key in self.unit_alias:
            return self.unit_alias[key]
        return self.unit_case_canonical.get(text.upper().replace(" ", ""), text.strip())

    def dimension_of(self, unit: Optional[str]) -> Optional[str]:
        if not unit:
            return None
        d = self.unit_dimension.get(_dim_norm(unit))
        if d:
            return d
        canon = self.vahed_canonical(unit)
        return self.unit_dimension.get(_dim_norm(canon)) if canon else None

    def is_percent_vahed(self, unit: Optional[str]) -> bool:
        canon = self.vahed_canonical(unit) if unit else None
        return canon in ("%", "percent", "pct")


    def flag_word(self, tok: Optional[str]) -> Optional[str]:
        return self.flags.get(str(tok or "").casefold().rstrip("."))

    def qualitative_word(self, tok: Optional[str]) -> Optional[str]:
        t = (tok or "").strip().casefold()
        return self.qualitative.get(t) or self.qualitative.get(t.rstrip('.'))

    def looks_qualitative(self, tok: str) -> bool:
        return self.qualitative_word(tok) is not None

_RANGE_RE = re.compile(r"([+-]?\d[\d,٫]*(?:\.\d+)?)\s*(?:[-–—~]|\b(?:to|تا)\b)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)", re.IGNORECASE)
_TRAILING_RANGE_RE = re.compile(
    r"([+-]?\d[\d,٫]*(?:\.\d+)?)\s*(?:[-–—~]|\b(?:to|تا)\b)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*(\S+)?\s*$", re.IGNORECASE)
_DEMO_RANGE_RE = re.compile(
    r"(adult|male|female|males|females|child|children|infant|ref(?:erence)?|normal|normat|"
    r"person|persons|desirable|optimal)\b[^0-9\n]{0,24}?"
    r"([0-9][\d,]*(?:\.\d+)?)\s*[-–—~]\s*([0-9][\d,]*(?:\.\d+)?)",
    re.IGNORECASE)
_DEMO_PRIORITY = {"adult": 0, "ref": 1, "reference": 1, "normal": 1, "normat": 1,
                  "male": 2, "female": 2, "males": 2, "females": 2, "child": 3,
                  "children": 3, 'infant': 3, "person": 4, "persons": 4,
                  'desirable': 5, "optimal": 5}
_CUTOFF_RE = re.compile(
    r"[\(\[\{]?\s*(?:(?:up\s*to|ap\s*to|upto|less\s*than|کمتر از)|[<≤])"
    r"\s*([0-9][\d,]*(?:\.\d+)?)\s*[\)\]\}]?\s*$",
    re.IGNORECASE)
_CUTOFF_HIGH_RE = re.compile(
    r"[\(\[\{]?\s*(?:(?:more\s*than|greater\s*than|بیشتر از|بیش از)|[>≥])"
    r"\s*([0-9][\d,]*(?:\.\d+)?)\s*[\)\]\}]?\s*$",
    re.IGNORECASE)

def _has_standalone_number(s: str) -> bool:
    for w in s.split():
        w = w.strip(".,:;()[]<>≤≥")
        if re.fullmatch(r"[+-]?\d[\d,٫]*(?:\.\d+)?", w):
            return True
    return False


def _is_zaman_vahed(unit: Optional[str]) -> bool:
    u = (unit or '').strip().casefold().rstrip(".")
    return u in {"s", "sec", "secs", "second", 'seconds'}


_TITER_DILUTIONS = {"2", "4", "8", "10", "16", "20", "32", "40", "64", "80", "100", "128",
                    "160", "256", "320", "512", "640", "1024", "1280", "2560"}
_TITER_NAME_RE = re.compile(r"titer|titre|widal|wright|coombs|ana\b|asо|aso\b|vdrl|rpr|tpha|dilution|رقت|تیتر",
                            re.IGNORECASE)


def _repair_colon_decimals(line: str) -> str:
    """OCR renders a decimal point as a colon ("Creatinine 2:8", "Hb 12:5").

    Serial dilutions ("1:80", "1:16") are kept verbatim: either because the
    line names a titer assay or because "1:<dilution>" matches a standard
    two-fold/ten-fold series.
    """
    titer_line = bool(_TITER_NAME_RE.search(line))
    if titer_line:
        line = re.sub(r"(?<![\d:.])1:(\d{1,4})(?![\d:])", r"\1", line)
    time_line = bool(re.search(r"time|date|ساعت|تاریخ|collected|received|reported|printed", line, re.IGNORECASE))

    def _repl(m):
        a, b = m.group(1), m.group(2)
        if titer_line or (a == "1" and b in _TITER_DILUTIONS):
            # "1:160" -> "160": numeric reciprocal of the serial dilution
            return b if a == "1" else m.group(0)
        if time_line and len(b) == 2 and int(a) <= 23 and int(b) <= 59:
            return m.group(0)
        return a + "." + b
    return re.sub(r"(?<![\d:.])(\d{1,3}):(\d{1,2})(?![\d:])", _repl, line)


def _repair_comma_decimals(line: str) -> str:
    line = re.sub(r"(\d+),(\d{1,2})(?=[^\d,]|$)", r"\1.\2", line)
    line = re.sub(r"(\d),\.(\d)", r"\1.\2", line)
    return line


def _strip_noise(text: str, support: "OCRSupport") -> str:
    if not text:
        return text
    out = []
    text_lower = text.lower()
    is_comp_word = any(k in text_lower for k in ["sensitivity", "density", "molecular"])
    for t in text.split():
        lt = t.casefold().rstrip(".,:;")
        if lt in ("high", "low") and is_comp_word:
            out.append(t)
            continue
        if lt in support.noise_words or support.noise_token_re.match(t):
            continue
        out.append(t)
    return " ".join(out).strip()


_MULTI_RANGE_AT_RE = re.compile(
    r"^\s*(?:\d[\d,\u066b]*(?:\.\d+)?\s*[-–—~]\s*\d[\d,\u066b]*(?:\.\d+)?"
    r"|[<≤>≥]\s*\d[\d,\u066b]*(?:\.\d+)?|(?:up\s*to|ap\s*to|upto|less\s*than|more\s*than)"
    r"\s*\d[\d,\u066b]*(?:\.\d+)?)")
_MULTI_LEAD_JUNK_RE = re.compile(r"^\s*(?:\d[\d,\u066b]*(?:\.\d+)?|%|[-–—~:;=])\s*")


def _tafkik_multi_azmayesh_lines(lines, support: "OCRSupport"):
    # Step 1: Clean line artifacts, strip row numbering, unglue tokens
    row_num_re = re.compile(r'^\s*\|?\s*(?:\d{1,2}\s*\|\s*|\d{1,2}\s*[.:°)]\s*(?=[A-Za-z؀-ۿ])|\d{1,2}\s+(?=[A-Za-z؀-ۿ]{2,}))')
    address_re = re.compile(r'\b(complex|opposite|road|street|mumbai|pincode|lane|avenue)\b', re.IGNORECASE)
    lab_signal_re = re.compile(r'\b(test|result|hemoglobin|glucose|wbc|rbc|platelet|cholesterol|creatinine|urea)\b', re.IGNORECASE)

    cleaned = []
    for l in lines:
        s = l.strip()
        if not s:
            continue
        if address_re.search(s) and not lab_signal_re.search(s):
            continue
        s = s.replace("10°9", "10*9").replace("10°12", "10*12").replace("10°3", "10*3").replace("10°", "10*")
        s = re.sub(r'(\d+(?:\.\d+)?)(10\*[0-9]+/[a-zA-Z]+)', r'\1 \2', s)
        s = re.sub(r'(\d+(?:\.\d+)?)(g/L|L/L|fL|pg|mg/dL|mmol/L)', r'\1 \2', s, flags=re.IGNORECASE)
        s = s.replace("|", " ")
        s = re.sub(r'\b(?:OhaOx|GhaOx|GOD-PAP|Capillary|End\s*Po(?:w|st|int)|Enz(?:y)?matic|Ennmatic|Dry\s*Chemistry)\b', ' ', s, flags=re.IGNORECASE)
        s = re.sub(r'(\d+(?:\.\d+)?)\s*(?:agit|maid|medi|meld|mgd|meal|wng/dl)\b', r'\1 mg/dL', s, flags=re.IGNORECASE)
        s = row_num_re.sub('', s)
        if s.strip():
            cleaned.append(s.strip())

    # Step 2: Merge lines broken by word wrapping
    merged = []
    i = 0
    while i < len(cleaned):
        cur = cleaned[i]
        if i + 1 < len(cleaned):
            nxt = cleaned[i + 1]
            if ((re.search(r'\d\s*[-–—~]$', cur.rstrip()) and not re.search(r'\d\s*[-–—~]\s*\d', cur))
                or re.match(r'^(?:\d[\d.]*10\*|\d[\d.]*(?:g/L|L/L|%|fL|pg|mg|mmol)|\([A-Za-z0-9]+\)\s*\d|width\s*\d|count\s*\d)', nxt, re.IGNORECASE)):
                merged.append(f"{cur} {nxt}")
                i += 2
                continue
        merged.append(cur)
        i += 1

    out = []
    for line in merged:
        out.extend(_tafkik_multi_azmayesh_line(line, support))
    return out


def _meghdar_vahed_anchors(line: str, support: "OCRSupport") -> list[tuple[int, int, bool]]:
    value_unit_re = re.compile(
        r"(\b\d[\d,\u066b]*(?:\.\d+)?)\s*(" + support.unit_pattern + r")(?:\b|\s|$)",
        re.IGNORECASE)
    anchors = []
    for m in value_unit_re.finditer(line):
        pre = line[:m.start()]
        if re.search(r'\b\d[\d,\u066b]*(?:\.\d+)?\s*[-–—~]\s*(?:[a-zA-Z()]{1,30}\s*)?$', pre):
            continue
        anchors.append((m.start(), m.end(), True))
    return anchors


def _bare_meghdar_bazeh_anchors(line: str, support: "OCRSupport") -> list[tuple[int, int, bool]]:
    unit_re = re.compile(r"^\s*(?:" + support.unit_pattern + r")", re.IGNORECASE)
    range_re = re.compile(r"(\d[\d,\u066b]*(?:\.\d+)?)\s*[-–—~]\s*(\d[\d,\u066b]*(?:\.\d+)?)")
    num_re = re.compile(r"\d[\d,\u066b]*(?:\.\d+)?")
    out: list[tuple[int, int, bool]] = []
    for m in range_re.finditer(line):
        pre = line[:m.start()]
        nums = list(num_re.finditer(pre))
        if not nums:
            continue
        vn = nums[-1]
        gap = pre[vn.end():]
        if unit_re.match(gap):
            continue
        if len(gap.strip()) > 6:
            continue
        out.append((vn.start(), m.end(), False))
    return out


def _tafkik_multi_azmayesh_line(line, support: "OCRSupport"):
    if _DUAL_DIFF_RE.match(line):


        return [line]
    anchors = _meghdar_vahed_anchors(line, support)
    if len(anchors) < 2:


        for a in _bare_meghdar_bazeh_anchors(line, support):
            if not any(a[0] < b[1] and b[0] < a[1] for b in anchors):
                anchors.append(a)
        anchors.sort(key=lambda a: a[0])
    if len(anchors) < 2:
        return [line]
    pieces = []
    cursor = 0
    for i, a in enumerate(anchors):
        name_i = line[cursor:a[0]].strip()
        if i + 1 < len(anchors):
            between = line[a[1]:anchors[i + 1][0]]
            if a[2]:
                range_i, name_off = _bazeh_nam_offset(between)
                pieces.append(f"{name_i} {line[a[0]:a[1]]} {range_i}".strip())
                cursor = a[1] + name_off
            else:
                pieces.append(f"{name_i} {line[a[0]:a[1]]}".strip())
                cursor = a[1]
        else:
            pieces.append(f"{name_i} {line[a[0]:a[1]]} {line[a[1]:].strip()}".strip())
    return [p for p in pieces if p]


def _bazeh_nam_offset(between):
    m = _MULTI_RANGE_AT_RE.match(between)
    if m:
        return between[:m.end()].strip(), m.end()
    m2 = _MULTI_LEAD_JUNK_RE.match(between)
    if m2:
        rest = between[m2.end():]
        m = _MULTI_RANGE_AT_RE.match(rest)
        if m:
            return between[:m2.end() + m.end()].strip(), m2.end() + m.end()
    return "", 0


class FeatureIndex:
    _CACHE_MAX = 4096
    _POSTING_CAP = int(os.environ.get("HEMOGLYPH_POSTING_CAP", "3000"))
    _MAX_FUZZY_CANDIDATES = int(os.environ.get("HEMOGLYPH_FUZZY_CANDIDATES", "300"))

    def __init__(self, features: Mapping[str, Any], normalizer: TextNormalizer, *,
                 similarity: float = 0.94, min_alias_len: int = 5, fuzzy_abbr: bool = False,
                 support: Optional['OCRSupport'] = None):
        self.features = features
        self.norm = normalizer
        self.support = support or OCRSupport()
        self.similarity = similarity
        self.min_alias_len = min_alias_len
        self.fuzzy_abbr = fuzzy_abbr
        self._exact: dict[str, list[str]] = {}
        self._exact_seen: dict[str, set[str]] = {}
        self._short: set[str] = set()
        self._errors: dict[str, str] = {}
        self._substring_keys: list[tuple[str, str]] = []
        self._display: dict[str, str] = {}
        self._token_index: dict[str, list[str]] = {}
        self._gram_index: dict[str, list[tuple[str, str]]] = {}
        self._by_len: dict[int, list[str]] = {}
        self._keys: list[str] = []
        self._tri_postings: dict[str, array] = {}
        self._tok_postings: dict[str, array] = {}
        self._grams_ready = False
        self._pool_lock = threading.RLock()
        self._cache: "OrderedDict[str, list[tuple[str, float]]]" = OrderedDict()
        self._sakht()

    def _afzoodan(self, key: str, fid: str, short: bool = False) -> None:
        if not key:
            return
        if short:
            self._short.add(key)
        seen = self._exact_seen.get(key)
        if seen is None:
            seen = self._exact_seen[key] = set()
            self._exact[key] = []
            self._by_len.setdefault(len(key), []).append(key)
            for tok in set(key.split()):
                self._token_index.setdefault(tok, []).append(key)
        if fid not in seen:
            seen.add(fid)
            self._exact[key].append(fid)

    def _afzoodan_substring(self, key: str, fid: str) -> None:
        self._substring_keys.append((key, fid))
        self._gram_index.setdefault(key[:4], []).append((key, fid))

    def _sakht(self) -> None:
        norm = self.norm.for_nam
        for fid, meta in self.features.items():
            ident = meta.get("identity") or {}
            self._display[fid] = str(ident.get("display_name") or fid)
            self._afzoodan(norm(fid), fid)
            for name in (ident.get('canonical_name'), ident.get("display_name"),
                         ident.get("short_name")):
                if name:
                    self._afzoodan(norm(name), fid)
            terms = meta.get("terminology") or {}
            pref = terms.get("preferred") or {}
            for lang in ("en", 'fa'):
                if pref.get(lang):
                    self._afzoodan(norm(pref[lang]), fid)
            for abbr in terms.get("abbreviations") or []:
                if abbr:
                    self._afzoodan(norm(abbr), fid, short=True)
            ocr_info = meta.get("ocr_mapping") or meta.get("ocr") or {}
            # Index all clinical synonyms in English and Persian
            syn = terms.get("synonyms") or {}
            for lang in ("en", "fa"):
                for s in syn.get(lang) or []:
                    if s and len(s) >= 2:
                        self._afzoodan(norm(s), fid)

            for alias in ocr_info.get("safe_aliases") or []:
                n = norm(alias)
                self._afzoodan(n, fid)
                if len(n) >= 5:
                    self._afzoodan_substring(n, fid)
            for abbr in ocr_info.get("abbreviations") or []:
                if abbr:
                    self._afzoodan(norm(abbr), fid, short=True)
            for err in ocr_info.get("common_errors") or []:
                if err:
                    self._errors.setdefault(norm(err), fid)
            for alias in self.support.curated_abbreviations.get(fid, []):
                self._afzoodan(norm(alias), fid, short=True)
        for err, fix in self.support.static_errors.items():


            self._errors[self.norm.for_nam(err)] = self._disambig_taeen(fix, None) or fix
        self._exact_seen = {}

    def _ensure_gram_pools(self) -> None:
        if self._grams_ready:
            return
        with self._pool_lock:
            if self._grams_ready:
                return
            t0 = time.perf_counter()
            keys = list(self._exact)
            tri: dict[str, array] = {}
            tok: dict[str, array] = {}
            for i, key in enumerate(keys):
                if key in self._short:
                    continue
                for g in {key[j:j + 3] for j in range(max(1, len(key) - 2))}:
                    bucket = tri.get(g)
                    if bucket is None:
                        bucket = tri[g] = array('i')
                    bucket.append(i)
                for t in set(key.split()):
                    bucket = tok.get(t)
                    if bucket is None:
                        bucket = tok[t] = array("i")
                    bucket.append(i)
            self._keys = keys
            self._tri_postings = tri
            self._tok_postings = tok
            self._grams_ready = True
            logger.info("FeatureIndex fuzzy pools built in %.2fs (%d keys, %d trigrams)",
                        time.perf_counter() - t0, len(keys), len(tri))

    def _ranked_candidates(self, q_norm: str, tokens: set[str],
                           limit: int) -> list[str]:
        self._ensure_gram_pools()
        keys = self._keys
        q_len = len(q_norm)
        lo = min(q_len - 3, int(0.6 * q_len))
        hi = max(q_len + 3, int(q_len / 0.6) + 1)

        scores: dict[int, int] = {}
        cap = self._POSTING_CAP

        grams = {q_norm[j:j + 3] for j in range(max(1, q_len - 2))}
        tri = self._tri_postings
        for g in grams:
            bucket = tri.get(g)
            if bucket is None or len(bucket) > cap:
                continue
            for i in bucket:
                scores[i] = scores.get(i, 0) + 1

        tokp = self._tok_postings
        for t in tokens:
            bucket = tokp.get(t)
            if bucket is None or len(bucket) > cap:
                continue
            for i in bucket:
                scores[i] = scores.get(i, 0) + 3

        if not scores:
            return []

        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        out: list[str] = []
        for i, _score in ranked:
            key = keys[i]
            if lo <= len(key) <= hi:
                out.append(key)
                if len(out) >= limit:
                    break
        return out

    def _disambig_taeen(self, entry: Any, unit: Optional[str]) -> Optional[str]:
        if isinstance(entry, Mapping):
            u_clean = (unit or "").lower().strip()
            u_canon = (self.support.vahed_canonical(unit) or "").lower().strip()
            if u_clean and u_clean in entry:
                cand = entry[u_clean]
                return cand[0] if isinstance(cand, (list, tuple)) else cand
            if u_canon and u_canon in entry:
                cand = entry[u_canon]
                return cand[0] if isinstance(cand, (list, tuple)) else cand
            if self.support.is_percent_vahed(unit) and "pct" in entry:
                pool = list(entry["pct"])
            elif "abs" in entry and not self.support.is_percent_vahed(unit):
                pool = list(entry["abs"])
            elif "default" in entry:
                cand = entry["default"]
                return cand[0] if isinstance(cand, (list, tuple)) else cand
            elif "any" in entry:
                pool = list(entry["any"])
            else:
                pool = []
        elif isinstance(entry, (list, tuple)):
            pool = list(entry)
        else:
            pool = [entry]
        if unit and len(pool) > 1:
            u_dim = self.support.dimension_of(unit)
            if u_dim:
                matching = [fid for fid in pool if self.support.dimension_of(self.features.get(fid, {}).get("measurement", {}).get("canonical_unit")) == u_dim]
                if matching:
                    return matching[0]
        for fid in pool:
            if fid in self.features:
                return fid
        if isinstance(entry, Mapping) and "default" in entry:
            cand = entry["default"]
            return cand[0] if isinstance(cand, (list, tuple)) else cand
        return None

    def display_name(self, feature_id: str) -> str:
        return self._display.get(feature_id, feature_id)

    def candidates(self, raw_name: str, *, specimen: Optional[str] = None,
                   unit: Optional[str] = None) -> list[tuple[str, float]]:
        q_raw = (raw_name or "").strip()
        if not q_raw:
            return []

        ck = f"{q_raw}\x00{unit or ''}\x00{specimen or ''}"
        cached = self._cache.get(ck)
        if cached is not None:
            self._cache.move_to_end(ck)
            return list(cached)

        result = self._candidates_uncached(q_raw, unit)

        self._cache[ck] = result
        if len(self._cache) > self._CACHE_MAX:
            self._cache.popitem(last=False)
        return list(result)

    def _candidates_uncached(self, q_raw: str,
                             unit: Optional[str]) -> list[tuple[str, float]]:
        # 1. Extract parenthetical expressions BEFORE normalization strips them
        pm = re.search(r"\(([^)]+)\)", q_raw)
        paren_text = pm.group(1).strip() if pm else ""
        raw_no_paren = re.sub(r"\([^)]*\)", " ", q_raw).strip()

        # 2. Collapse dotted acronyms (e.g. W.B.C -> WBC, F.B.S -> FBS, Alk. Phos. -> Alk Phos)
        def _collapse_dots(s: str) -> str:
            s0 = re.sub(r"\b([A-Za-z])\.([A-Za-z]{2,})", r"\1 \2", s)
            s1 = re.sub(r"\b([A-Za-z])\.", r"\1", s0)
            s2 = re.sub(r"\.+", " ", s1)
            return " ".join(s2.split())

        # 3. Strip laboratory methodology noise tags (without stripping physiological qualifiers like fasting, random, calculated)
        method_noise_re = re.compile(
            r"\b(chemiluminescence|hplc|clia|eclia|elisa|ria|ise|turbidimetry|immunoturbidimetry|colorimetric|enzymatic|"
            r"quantitative|qualitative|semi-quantitative|quant|qual|automated|manual|slide)\b", re.IGNORECASE
        )

        norm = self.norm.for_nam
        q_norm = norm(q_raw)
        q_lower = q_raw.strip().lower()

        # STEP 0: Direct exact query check
        # First check exact disambiguation on full query:
        if q_lower in self.support.disambiguation:
            fid = self._disambig_taeen(self.support.disambiguation[q_lower], unit)
            if fid:
                return [(fid, 1.0)]
        if q_norm in self.support.disambiguation:
            fid = self._disambig_taeen(self.support.disambiguation[q_norm], unit)
            if fid:
                return [(fid, 1.0)]

        # Check _exact for direct query:
        hit0 = self._exact.get(q_norm) or self._exact.get(q_lower)
        if hit0:
            if len(hit0) == 1:
                return [(hit0[0], 1.0)]
            if unit:
                u_dim = self.support.dimension_of(unit)
                if u_dim:
                    best_u = [f for f in hit0 if self.support.dimension_of(self.features.get(f, {}).get("measurement", {}).get("canonical_unit")) == u_dim]
                    if len(best_u) == 1:
                        return [(best_u[0], 1.0)]

        # Build prioritized variants to test against exact index
        candidate_forms: list[str] = []
        raw_variants = [q_raw]
        if raw_no_paren and raw_no_paren != q_raw:
            raw_variants.append(raw_no_paren)
        if paren_text:
            raw_variants.append(paren_text)

        for rv in raw_variants:
            rv_norm = norm(rv)
            candidate_forms.append(rv_norm)
            candidate_forms.append(rv.lower())

            # Collapsed dots
            rv_col = _collapse_dots(rv)
            if rv_col != rv:
                candidate_forms.append(norm(rv_col))
                candidate_forms.append(rv_col.lower())

            # Method noise stripped
            rv_no_m = method_noise_re.sub(" ", rv_col).strip()
            if rv_no_m and rv_no_m != rv_col:
                candidate_forms.append(norm(rv_no_m))
                candidate_forms.append(rv_no_m.lower())

            # Hyphen & slash to space
            candidate_forms.append(norm(rv.replace("-", " ")))
            candidate_forms.append(norm(rv.replace("/", " ")))
            candidate_forms.append(norm(rv.replace("_", " ")))
            candidate_forms.append(norm(rv_col.replace("-", " ")))

            # Inverted word order for modifiers (e.g. 'psa total' -> 'total psa')
            rv_norm_clean = norm(rv)
            if rv_norm_clean.endswith(" total"):
                candidate_forms.append("total " + rv_norm_clean[:-6].strip())
            elif rv_norm_clean.endswith(" direct"):
                candidate_forms.append("direct " + rv_norm_clean[:-7].strip())
            elif rv_norm_clean.endswith(" free"):
                candidate_forms.append("free " + rv_norm_clean[:-5].strip())

            # Strip antibody suffix 'ab' (e.g. 'anti tpo ab' -> 'anti tpo', 'hiv 1/2 ab' -> 'hiv 1/2')
            if re.search(r'\s*\bab\b\s*$', rv_norm_clean):
                no_ab = re.sub(r'\s*\bab\b\s*$', '', rv_norm_clean).strip()
                candidate_forms.append(no_ab)
                candidate_forms.append(no_ab + " antibody")

        # Deduplicate while preserving order
        unique_forms = list(dict.fromkeys(f for f in candidate_forms if f))

        # STEP A: Check exact disambiguation table
        for form in unique_forms:
            if form in self.support.disambiguation:
                fid = self._disambig_taeen(self.support.disambiguation[form], unit)
                if fid:
                    return [(fid, 0.99)]

        # STEP B: Check exact index matches (_exact)
        for form in unique_forms:
            hit = self._exact.get(form)
            if hit:
                if len(hit) > 1 and unit:
                    best_u = [f for f in hit if self.support.dimension_of(unit) == self.support.dimension_of(self.features.get(f, {}).get("measurement", {}).get("canonical_unit"))]
                    if best_u:
                        return [(best_u[0], 0.99)]
                return [(fid, 0.99) for fid in hit]

        # STEP C: Noise-stripped clean exact match
        q_norm = norm(q_raw)
        clean = self.support.name_noise_re.sub("", q_norm)
        clean = " ".join(clean.split())
        if clean and clean != q_norm:
            hit = self._exact.get(clean)
            if hit:
                return [(fid, 0.98) for fid in hit]
            if clean in self.support.disambiguation:
                fid = self._disambig_taeen(self.support.disambiguation[clean], unit)
                if fid:
                    return [(fid, 0.98)]

        # STEP D: Substring Gram matching
        if len(q_norm) >= 4:
            grams = {q_norm[idx:idx + 4] for idx in range(len(q_norm) - 3)}
            gram_index = self._gram_index
            best_key, best_fid = "", None
            for g in grams:
                bucket = gram_index.get(g)
                if not bucket:
                    continue
                for key, fid in bucket:
                    if len(key) >= 5 and key in q_norm and len(key) > len(best_key):
                        best_key, best_fid = key, fid
            if best_fid is not None:
                return [(best_fid, 0.95)]

        # STEP E: Ranked fuzzy candidate pools (Dice & Levenshtein SequenceMatcher)
        scored: list[tuple[str, float]] = []
        exact = self._exact
        nw = set(q_norm.split())
        pool = self._ranked_candidates(q_norm, nw, self._MAX_FUZZY_CANDIDATES)

        if len(nw) >= 2:
            len_nw = len(nw)
            for key in pool:
                kw = key.split()
                inter = len(nw.intersection(kw))
                if inter:
                    dice = 2.0 * inter / (len_nw + len(kw))
                    if dice >= 0.55:
                        score = 0.88 + 0.10 * dice
                        for f in exact[key]:
                            scored.append((f, score))

        if len(q_norm) >= self.min_alias_len or self.fuzzy_abbr:
            short = self._short
            matcher = difflib.SequenceMatcher(None)
            matcher.set_seq1(q_norm)
            for key in pool:
                if key in short:
                    continue
                matcher.set_seq2(key)
                if matcher.quick_ratio() < 0.82:
                    continue
                r = matcher.ratio()
                if r >= 0.82:
                    for f in exact[key]:
                        scored.append((f, r))

        if scored:
            scored.sort(key=lambda x: x[1], reverse=True)
            best = scored[0][1]
            return [(f, s) for f, s in scored if s >= best - 0.03][:4]

        # STEP F: ONLY AFTER EXACT AND FUZZY FAIL, check static OCR errors (_errors)
        for form in unique_forms:
            fid = self._errors.get(form)
            if fid and fid in self.features:
                return [(fid, 0.90)]

        return []


class FeatureRegistry:
    def __init__(self, path: str | Path, *, language: str = "en"):
        self.path = Path(path)
        self.language = language
        payload = bargozari_registry(self.path)
        if payload is None:
            raise RuntimeError(f"Cannot load feature registry: {self.path}")
        self.payload = payload
        self.features: dict[str, dict[str, Any]] = payload.get('features', {})
        self.feature_count = len(self.features)
        self.normalizer = TextNormalizer()
        sim = 0.94
        try:
            sample = next(iter(self.features.values()), {})
            sim = float((sample.get("ocr_mapping") or sample.get("ocr") or {})
                        .get("confidence_threshold", 0.94))
        except Exception:
            sim = 0.94
        self.ocr = OCRSupport.from_registry(payload)
        self.index = shared_object(
            f"feature_index::{self.path.resolve()}::{sim}",
            lambda: FeatureIndex(self.features, self.normalizer, similarity=sim,
                                 support=self.ocr),
        )

    @classmethod
    def shared(cls, path: str | Path, *, language: str = "en") -> "FeatureRegistry":
        p = Path(path)
        return shared_object(
            f"feature_registry::{p.resolve()}::{language}",
            lambda: cls(p, language=language),
        )

    def display_name(self, feature_id: str) -> str:
        return self.index.display_name(feature_id)

    def get(self, feature_id: str) -> dict[str, Any]:
        return self.features.get(feature_id, {})

    def short_name(self, feature_id: str) -> str:
        return str((self.get(feature_id).get("identity") or {}).get("short_name") or feature_id)

    def suggested_vahed(self, feature_id: str) -> Optional[str]:
        meta = self.get(feature_id)
        return ((meta.get("units") or {}).get("canonical")
                or (meta.get('measurement') or {}).get('canonical_unit'))

    def category(self, feature_id: str) -> str:
        return str((self.get(feature_id).get("identity") or {}).get("category") or "")

    def value_type(self, feature_id: str) -> str:
        m = self.get(feature_id).get('measurement') or {}
        return str(m.get('value_type') or "quantitative")

    def normalizer_for(self, feature_id: str) -> TextNormalizer:
        return self.normalizer


@dataclass
class ParsedLine:
    raw: str
    name: Optional[str] = None
    value: Any = None
    unit: Optional[str] = None
    qualitative: Optional[str] = None
    flag: Optional[str] = None
    report_range_low: Optional[float] = None
    report_range_high: Optional[float] = None
    note: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


class ReportLineParser:
    def __init__(self, support: Optional["OCRSupport"] = None):
        self.support = support or OCRSupport()

    def _tafsir_piped(self, raw: str, normalizer: TextNormalizer) -> Optional[ParsedLine]:
        parts = [p.strip() for p in raw.split("|")]
        parts = (parts + ["", "", "", '', ""])[:5]
        name_s, value_s, unit_s, flag_s, ref_s = parts
        name_s, flag_tail = self._tafkik_nam_flag(name_s)
        if not name_s or len(name_s) < 2:
            return None
        if re.fullmatch(r"[\s_=\-·.—|]+", name_s):
            return None
        if not ref_s and _RANGE_RE.search(flag_s):
            ref_s, flag_s = flag_s, ""
        if not ref_s and not flag_s and _RANGE_RE.search(unit_s) and not self._is_vahed(unit_s):
            ref_s, unit_s = unit_s, ""
        parsed = ParsedLine(raw=raw)
        parsed.name = normalizer.for_nam(name_s)
        parsed.unit = unit_s or None
        flag = flag_tail or (self.support.flags.get(flag_s.casefold().rstrip('.')) if flag_s else None)
        value_tok = None
        for t in value_s.split():
            if value_tok is None and self._looks_numeric(t):
                value_tok = t
            elif not flag:
                flag = self.support.flags.get(t.casefold().rstrip("."))
        if value_s and self._looks_qualitative(value_s):
            parsed.qualitative = self._qualitative_word(value_s)
            parsed.value = parsed.qualitative
        elif value_tok is not None:
            parsed.value = self._to_number(value_tok)
        parsed.flag = flag
        m = _RANGE_RE.search(ref_s)
        if m:
            parsed.report_range_low = self._to_number(m.group(1))
            parsed.report_range_high = self._to_number(m.group(2))
        return parsed

    def parse(self, line: str, normalizer: TextNormalizer) -> Optional[ParsedLine]:
        raw = line.strip()
        if not raw:
            return None
        # Two or more pipes means the PDF text layer preserved the table
        # grid; that path is far more reliable than column reconstruction.
        m_bg = _BLOOD_GROUP_RE.match(raw)
        if m_bg:
            rh = (m_bg.group(4) or "").lower()
            rh = "+" if rh.startswith(("+", "pos")) else ("-" if rh.startswith(("-", "neg")) else "")
            parsed = ParsedLine(raw=raw)
            parsed.name = normalizer.for_nam("blood group")
            parsed.qualitative = m_bg.group(3).upper() + rh
            parsed.value = parsed.qualitative
            return parsed
        if raw.count("|") >= 2:
            return self._tafsir_piped(raw, normalizer)
        if raw.startswith(("•", "-", "*", "▪", "○", '●', '✓', "☑")):
            raw2 = raw.lstrip("•-*▪○●✓☑ ") or raw
        else:
            raw2 = raw
        # Rule lines and table borders survive OCR as punctuation soup.
        if re.fullmatch(r"[\s_=\-·.—|*•]+", raw2) or len(raw2) < 2:
            return None

        cleaned = raw2
        # Pre-normalize parenthesized, bracketed, and Persian reference ranges
        cleaned = re.sub(r'[\(\[]\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*(?:[-–—~]|الی|تا)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*[\)\]]', r' \g<1> - \g<2>', cleaned)
        cleaned = re.sub(r'\b(?:الی|تا|طبیعی)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*(?:[-–—~]|الی|تا)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)', r' \1 - \2', cleaned)
        cleaned = re.sub(r'\b(?:الی|تا|طبیعی)\s*([a-zA-Z\u0600-\u06FF]+)\s*$', r' \1', cleaned)
        cleaned = re.sub(r'[\(\[]\s*(?:حداکثر|کمتر از|زیر)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*[\)\]]', r' < \g<1>', cleaned)
        cleaned = re.sub(r'[\(\[]\s*(?:حداقل|بیشتر از|بالای)\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*[\)\]]', r' > \g<1>', cleaned)

        # Unpack parenthesized single numbers or percentages (e.g. "Hematocrit (46.1 %) [41-53]" -> "Hematocrit 46.1 % [41-53]")
        cleaned = re.sub(r'\(\s*([+-]?\d[\d,٫]*(?:\.\d+)?(?:\s*%)?)\s*\)', r' \1 ', cleaned)

        # Handle parenthesized or bracketed qualitative values at the end of line:
        # If line already has a value, it's a reference range -> strip it.
        # If line has no value yet (e.g. "Urine Protein (Negative)", "Urine Protein (1+)"), unpack it as the patient's value!
        m_qref = re.search(r'[\(\[]\s*([0-9a-zA-Z\u0600-\u06FF\s\-+]+)\s*[\)\]]\s*$', cleaned)
        if m_qref:
            q_word = m_qref.group(1).strip().lower()
            if q_word in self.support.qualitative or q_word in self.support.categorical or q_word in (
                'rare', 'negative', 'normal', 'non-reactive', 'nonreactive', 'few', 'none', 'trace', '1+', '2+', '3+', '4+', 'منفی', 'طبیعی', 'نرمال'
            ):
                prefix = cleaned[:m_qref.start()].strip()
                has_val = bool(re.search(r'[:=]\s*[+-]?\d[\d,.]*|\b\d[\d,.]*\s*(?:' + self.support.unit_pattern + r')?\s*$', prefix)) or any(
                    w.lower().rstrip(".,:;=-") in self.support.qualitative or w.lower().rstrip(".,:;=-") in self.support.categorical
                    for w in prefix.split()
                )
                if has_val:
                    cleaned = prefix
                else:
                    cleaned = prefix + " " + m_qref.group(1).strip()

        # Multi-word qualitative phrase detection (only when after separator : = or at end of line)
        found_phrase = None
        # longest phrase first so "non reactive" wins over "reactive"
        for q_phrase, q_canon in sorted(self.support.qualitative.items(),
                                        key=lambda kv: -len(kv[0])):
            if len(q_phrase) >= 4:
                # Check after colon or equal
                m_sep = re.search(r'[:=]\s*' + re.escape(q_phrase) + r'\s*$', cleaned, re.IGNORECASE)
                m_end = re.search(r'\s+' + re.escape(q_phrase) + r'\s*$', cleaned, re.IGNORECASE)
                if m_sep:
                    found_phrase = (m_sep.start(), m_sep.end(), q_canon)
                    break
                elif m_end and not re.search(r'\b(c-reactive|reactive protein|protein c)\b', cleaned, re.IGNORECASE):
                    found_phrase = (m_end.start(), m_end.end(), q_canon)
                    break

        if found_phrase:
            p_start, p_end, q_c = found_phrase
            cleaned = cleaned[:p_start].strip().rstrip(":=-")
            cat_value = q_c
            # Check if cleaned STILL ends with a qualitative word preceded by a separator:
            # e.g., "Protein Negative - Negative", "Color Yellow - Yellow", "Appearance Clear : Clear"
            while True:
                cleaned = cleaned.rstrip(":=-—· 	")
                words = cleaned.split()
                if not words:
                    break
                last_word = words[-1].lower().rstrip(".,:;=")
                if last_word in self.support.qualitative or last_word in self.support.categorical:
                    cat_value = self.support.qualitative.get(last_word) or cat_value or last_word
                    cleaned = " ".join(words[:-1]).strip()
                    continue
                break
        else:
            cat_value = None

        trailing_unit = None
        m = re.search(r"\s+(" + self.support.unit_pattern + r")\s*$", cleaned, re.IGNORECASE)
        if m:
            trailing_unit = m.group(1).strip()
            cleaned = cleaned[:m.start()].strip()

        flag = None
        while True:
            words = cleaned.split()
            if not words:
                break
            wf = words[-1].casefold().rstrip(".")
            wf_star = wf.rstrip("*")
            if wf in self.support.flags or (words[-1].endswith("*") and wf_star in self.support.flags):
                tok = wf_star if (words[-1].endswith("*") and wf_star in self.support.flags) else wf
                if flag is None:
                    flag = self.support.flags.get(tok, words[-1].upper())
                cleaned = ' '.join(words[:-1]).strip()
                continue
            break

        # If cat_value was detected, but cleaned still ends with a qualitative token
        # (e.g. because a flag or reference separated them: "Protein Negative H Negative"):
        if cat_value:
            while True:
                words = cleaned.split()
                if not words:
                    break
                last_word = words[-1].lower().rstrip(".,:;=-")
                if last_word in self.support.qualitative or last_word in self.support.categorical:
                    cleaned = " ".join(words[:-1]).strip().rstrip(":=-")
                    continue
                break


        ref_low = ref_high = None
        demo_hits = list(_DEMO_RANGE_RE.finditer(cleaned))
        if demo_hits:
            best = min(demo_hits, key=lambda mm: _DEMO_PRIORITY.get(mm.group(1).lower(), 9))
            ref_low = self._to_number(best.group(2))
            ref_high = self._to_number(best.group(3))
            cleaned = cleaned[:demo_hits[0].start()].strip()


        if ref_low is None:
            m_ratio = re.search(
                r"\s+([+-]?\d[\d,٫]*(?:\.\d+)?)\s+[-–—]\s+([+-]?\d[\d,٫]*(?:\.\d+)?)\s*[-–—~]\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*$",
                cleaned)
            if m_ratio:
                ref_low = self._to_number(m_ratio.group(2))
                ref_high = self._to_number(m_ratio.group(3))
                cleaned = cleaned[:m_ratio.start()].strip() + " " + m_ratio.group(1)

        if ref_low is None:
            m = _TRAILING_RANGE_RE.search(cleaned)
            if m:
                g3 = m.group(3)
                is_unit = self._is_vahed(g3) if g3 else False
                if g3 is None or is_unit or g3 in (")", "]", "}", "»"):
                    prefix = cleaned[:m.start()].strip()
                    # Only treat as ref range if there is a number before it, or if it was bracketed
                    if _has_standalone_number(prefix) or re.search(r'\b\d{1,3}\s*[-–—~]\s*\d{1,3}\b', prefix):
                        ref_low = self._to_number(m.group(1))
                        ref_high = self._to_number(m.group(2))
                        if is_unit and not trailing_unit:
                            trailing_unit = g3
                        cleaned = prefix


        comparator_value = None
        comparator_flag = None
        if ref_low is None:
            m = _CUTOFF_RE.search(cleaned)
            if m:
                before = cleaned[:m.start()].strip()
                if _has_standalone_number(before):
                    ref_low, ref_high = 0.0, self._to_number(m.group(1))
                    cleaned = before
                else:
                    comparator_value = self._to_number(m.group(1))
                    comparator_flag = "L"
                    cleaned = before
        if ref_low is None and comparator_value is None:
            m = _CUTOFF_HIGH_RE.search(cleaned)
            if m:
                before = cleaned[:m.start()].strip()
                if _has_standalone_number(before):
                    ref_low, ref_high = self._to_number(m.group(1)), None
                    cleaned = before
                else:
                    comparator_value = self._to_number(m.group(1))
                    comparator_flag = "H"
                    cleaned = before


        if ref_low is None and comparator_value is None:
            m = re.search(
                r"\s+([+-]?\d[\d,\u066b]*(?:\.\d+)?)\s+([+-]?\d[\d,\u066b]*(?:\.\d+)?)\s*$",
                cleaned)
            if m:
                lo, hi = self._to_number(m.group(1)), self._to_number(m.group(2))
                if lo is not None and hi is not None and lo <= hi \
                        and re.search(r"\d[\d,\u066b]*(?:\.\d+)?", cleaned[:m.start()]):
                    ref_low, ref_high = lo, hi
                    cleaned = cleaned[:m.start()].strip()


        cleaned = _strip_noise(cleaned, self.support)


        if cat_value is None and any(sep in cleaned for sep in (":", "=")):
            clean_sep = re.sub(r'(?<=\d):(?=\d)', '§COLON§', cleaned)
            for sep in (":", "="):
                if sep in clean_sep:
                    parts = clean_sep.split(sep, 1)
                    val_candidate = parts[1].strip().lower().rstrip(".,; ")
                    canon_val = self.support.qualitative.get(val_candidate)
                    if canon_val:
                        cat_value = canon_val
                        cleaned = parts[0].replace('§COLON§', ':').strip()
                        break

        if cat_value is None:
            qual_tokens = cleaned.split()
            while qual_tokens:
                t = qual_tokens[-1]
                lt = t.lower().rstrip(".,:;=")
                if lt in self.support.categorical or lt in self.support.qualitative or t in ("=", ":", ".", "-"):
                    t = qual_tokens.pop()
                    if t in ("=", ":"):
                        break
                    if t not in (".", "-"):
                        cat_value = self.support.qualitative.get(lt) or lt
                    continue
                if len(qual_tokens) >= 2 and re.fullmatch(r"\d{1,3}", t.rstrip(".,:;")) \
                        and (qual_tokens[-2].casefold().rstrip(".,:;=") in self.support.categorical
                             or qual_tokens[-2] in ("=", ':', ".", "-")):
                    qual_tokens.pop()
                    continue
                break
            if cat_value is not None:
                cleaned = " ".join(qual_tokens).strip()

        # Check for microscopy count range like "1-2", "2-3", "0-2" at end of line (e.g. "Urine RBC: 1-2", "Urine RBC - 1-2 - 0 - 3"):
        if cat_value is None:
            cleaned_trim = cleaned.rstrip(" -–—:=;,.")
            m_mrange = re.search(r'\b(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*(?:/([a-zA-Z]+))?\s*$', cleaned_trim)
            if m_mrange:
                cat_value = f"{m_mrange.group(1)}-{m_mrange.group(2)}"
                if m_mrange.group(3):
                    trailing_unit = f"/{m_mrange.group(3)}"
                cleaned = cleaned_trim[:m_mrange.start()].strip().rstrip(":= -–—")


        mm = re.search(
            r"(\b\d[\d,٫]*(?:\.\d+)?)\s+([HLhl]|high|low|crit(?:ical)?|abn(?:ormal)?|↑|↓)\s+("
            + self.support.unit_pattern + r")(?:\b|\s|$)",
            cleaned, re.IGNORECASE)
        if mm:
            tok = mm.group(2)
            if flag is None:
                flag = self.support.flags.get(tok.casefold(),
                                              {"↑": "H", "↓": "L"}.get(tok))
            cleaned = cleaned[:mm.start()] + " " + mm.group(1) + ' ' + mm.group(3) + cleaned[mm.end():]


        value = None
        unit = trailing_unit
        name = cleaned


        cm = re.search(r"(\S+)\s*([<≤>≥])\s*([+-]?\d[\d,٫]*(?:\.\d+)?)\s*$", cleaned)
        if cm and self._is_vahed(cm.group(1)) and not re.search(r"\d", cleaned[:cm.start()]):
            unit = cm.group(1)
            value = self._to_number(cm.group(3))
            flag = {'<': "L", "≤": "L", ">": "H", "≥": "H"}.get(cm.group(2))
            cleaned = cleaned[:cm.start()].strip()
            name = cleaned
        m = re.search(r"(\b\d[\d,٫]*(?:\.\d+)?)\s*(" + self.support.unit_pattern + r")(?:\b|\s|$)",
                      cleaned, re.IGNORECASE)
        if m:
            value = self._to_number(m.group(1))
            unit = m.group(2).strip()
            name = cleaned[:m.start()].strip()
        else:


            um = re.search(r"(\S+)\s+([+-]?\d[\d,٫]*(?:\.\d+)?)\s*$", cleaned)
            if um and self._is_vahed(um.group(1)):
                unit = um.group(1)
                value = self._to_number(um.group(2))
                name = cleaned[:um.start()].strip()
            else:


                num_tokens = [w for w in cleaned.split()
                              if re.fullmatch(r"\d[\d,٫]*(?:\.\d+)?", w)]
                if num_tokens:
                    pick = num_tokens[0]
                    if len(num_tokens) > 1 and ref_low is not None and ref_high is not None:
                        def _dist(tok: str) -> float:
                            v = self._to_number(tok)
                            if v is None:
                                return float("inf")
                            if ref_low <= v <= ref_high:
                                return 0.0
                            return min(abs(v - ref_low), abs(v - ref_high))
                        pick = min(num_tokens, key=_dist)
                    value = self._to_number(pick)
                    name = cleaned.replace(pick, "", 1).strip()


        if unit is not None and _is_zaman_vahed(unit) \
                and not self.support.time_unit_name_re.search(name):
            unit = None


        clean_tokens = []
        for t in name.split():
            lt = t.lower().rstrip(".,")


            punct_flag = re.fullmatch(r'[.:=,;|·]*(?:[HLhl])[.:=,;|·]*', t)
            is_comp_word = any(k in name.lower() for k in ["sensitivity", "density", "molecular"])
            is_valid_letter = (len(t) == 1 and t.lower() in ("a", "b", "c", "d", "e", "k", "t", "i", "s", "p", "v", "x", "y"))
            if lt in self.support.flag_clean and lt != "calculated" and not (lt in ("high", "low") and is_comp_word):
                if not flag:
                    flag = self.support.flags.get(lt, t.upper())
            elif punct_flag and not flag:
                flag = self.support.flags.get(t.upper().strip('.:=,;|·'), t.upper())
            elif (lt not in self.support.noise_words or (lt in ("high", "low") and is_comp_word)) \
                    and not self.support.noise_token_re.match(t) \
                    and not (len(t) == 1 and t.islower() and not is_valid_letter) \
                    and not (len(t) == 1 and t in '.:;=,-—–|~<>+*') \
                    and not re.fullmatch(r"\d{4,}", t):
                clean_tokens.append(t)


        is_hla = 'hla' in name.lower()
        cleaned2: list[str] = []
        for j, t in enumerate(clean_tokens):
            if not is_hla and re.fullmatch(r"\d{1,4}", t) and (
                    (j > 0 and re.fullmatch(r"\d{1,4}", clean_tokens[j - 1]))
                    or (j + 1 < len(clean_tokens) and re.fullmatch(r"\d{1,4}", clean_tokens[j + 1]))):
                continue
            cleaned2.append(t)
        clean_tokens = cleaned2
        name = re.sub(r"[,:\-—|+]+$", "", " ".join(clean_tokens)).strip()


        name = re.sub(r"\(\s*%?\s*\)", "", name).strip()


        pm = re.search(r"\(\s*(\S+)\s*\)\s*$", name)
        if pm and self._is_vahed(pm.group(1)):
            if unit is None:
                unit = pm.group(1)
            name = name[:pm.start()].strip()


        clean_col = re.sub(r'(?<=\d):(?=\d)', '§COLON§', name)
        if any(t in ("=", ":") for t in clean_col.split()):
            clean_col = re.split(r'[=:]', clean_col, 1)[0].strip()
        name = clean_col.replace('§COLON§', ':')
        toks = name.split()
        changed = True
        while changed and toks:
            changed = False
            if re.fullmatch(r"10/\d{1,3}", toks[-1]):
                toks.pop(); changed = True
            elif re.fullmatch(r"\d{1,2}", toks[-1].rstrip(".,")):
                toks.pop(); changed = True
            elif re.fullmatch(r"[<>≥≤+]", toks[-1]):
                toks.pop(); changed = True
            elif re.fullmatch(r"\d{1,4}[/:]\d{1,4}", toks[-1]):
                toks.pop(); changed = True
        name = re.sub(r"[,:\-—|+]+\s*$", "", " ".join(toks)).strip()
        if not unit and "%" in raw:
            unit = "%"


        if value is None and comparator_value is not None:
            value = comparator_value
            unit = unit or trailing_unit
            if flag is None:
                flag = comparator_flag


        if ref_low is not None and ref_high is not None and ref_low > ref_high:
            fixed_low = False
            for _div in (10.0, 100.0):
                if ref_low / _div <= ref_high:
                    ref_low = ref_low / _div
                    fixed_low = True
                    break
            if fixed_low and value is not None and value > ref_high * 3.0:
                for _div in (10.0, 100.0, 1000.0):
                    if ref_low <= value / _div <= ref_high:
                        value = value / _div
                        break

        parsed = ParsedLine(raw=raw)
        if name:
            name_col = re.sub(r'\b([A-Za-z])\.([A-Za-z]{2,})', r'\1 \2', name)
            name_col = re.sub(r'\b([A-Za-z])\.', r'\1', name_col)
            name_col = re.sub(r'\.+', ' ', name_col).strip()
            name = name_col if name_col else name
        parsed.name = normalizer.for_nam(name) if name else None
        parsed.unit = unit
        parsed.flag = flag
        parsed.report_range_low = ref_low
        parsed.report_range_high = ref_high
        if value is not None:
            parsed.value = value
        elif cat_value is not None:
            parsed.qualitative = self.support.qualitative.get(cat_value) or cat_value
            parsed.value = parsed.qualitative
        elif name and self._looks_qualitative(name.split()[-1] if name.split() else ""):
            parsed.qualitative = self._qualitative_word(name.split()[-1])
            parsed.value = parsed.qualitative
        return parsed

    def tafsir_all(self, line: str, normalizer: TextNormalizer) -> list[ParsedLine]:
        raw = line.strip()
        if not raw:
            return []
        m = _DUAL_DIFF_RE.match(raw)
        if m:
            name = m.group('name').strip()
            if not name:
                single = self.parse(raw, normalizer)
                return [single] if single is not None else []
            tail = m.group("tail").strip()
            ranges = list(_RANGE_RE.finditer(tail))
            pct_low = pct_high = abs_low = abs_high = None
            if len(ranges) >= 2:
                pct_low = self._to_number(ranges[0].group(1))
                pct_high = self._to_number(ranges[0].group(2))
                abs_low = self._to_number(ranges[1].group(1))
                abs_high = self._to_number(ranges[1].group(2))
            elif len(ranges) == 1:
                abs_low = self._to_number(ranges[0].group(1))
                abs_high = self._to_number(ranges[0].group(2))
            out: list[ParsedLine] = []
            pct = ParsedLine(raw=raw)
            pct.name = normalizer.for_nam(name)
            pct.value = self._to_number(m.group("pct"))
            pct.unit = "%"
            pct.report_range_low = pct_low
            pct.report_range_high = pct_high
            out.append(pct)
            ab = ParsedLine(raw=raw)
            ab.name = normalizer.for_nam(name)
            ab.value = self._to_number(m.group("abs"))
            ab.unit = m.group("unit").strip()
            ab.report_range_low = abs_low
            ab.report_range_high = abs_high
            out.append(ab)
            return out
        single = self.parse(raw, normalizer)
        return [single] if single is not None else []

    def _tafkik_nam_flag(self, text: str):
        m = re.search(
            r"(\b(?:CRIT|CRITICAL|HIGH|LOW|BORDERLINE|ABNORMAL|ABN|H|L|N)\b|بالا|پایین|طبیعی)\s*$",
            text, re.IGNORECASE)
        flag = None
        if m:
            flag = self.support.flags.get(m.group(1).casefold())
            text = re.sub(
                r"(\s*\b(?:CRIT|CRITICAL|HIGH|LOW|BORDERLINE|ABNORMAL|ABN|H|L|N)\b\s*|بالا|پایین|طبیعی)\s*$",
                "", text, flags=re.IGNORECASE)
        return text.strip(), flag

    def _is_vahed(self, tok: str) -> bool:
        return self.support.is_vahed(tok or "")

    def _looks_numeric(self, tok: str) -> bool:
        return self._to_number(tok) is not None

    def _to_number(self, tok: Optional[str]):
        if tok is None:
            return None
        t = str(tok).strip()


        t = (t.replace("\u066b", '.').replace("\u060c", '.')
              .replace("\u066c", ","))
        if "," in t:
            parts = t.split(',')


            if (len(parts) == 2 and len(parts[-1]) in (1, 2)
                    and len(parts[0]) <= 3):
                t = parts[0] + "." + parts[1]
            else:
                t = ''.join(parts)
        try:
            return float(t)
        except ValueError:
            return None

    def _looks_qualitative(self, tok: str) -> bool:
        return self._qualitative_word(tok) is not None

    def _qualitative_word(self, tok: str) -> Optional[str]:
        return self.support.qualitative_word(tok)

class ExtractionBackend:
    name = "base"
    language = "en"

    def extract(self, upload: Any) -> str:
        raise NotImplementedError


class RawTextBackend(ExtractionBackend):
    name = "raw_text"

    def extract(self, upload: Any) -> str:
        if upload is None:
            return ""
        if isinstance(upload, (bytes, bytearray)):
            return bytes(upload).decode("utf-8", errors='ignore')
        if isinstance(upload, str):
            p = upload
            if p.lower().endswith((".txt", ".csv", '.tsv')):
                try:
                    return Path(p).read_text(encoding='utf-8', errors="ignore")
                except Exception:
                    return ''
            if "\n" in p or p.strip().count(" ") > 2:
                return p
            return ""
        if hasattr(upload, 'read'):
            try:
                data = upload.read()
                return data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data)
            except Exception:
                return ""
        return ""


_PERSIAN_RE = re.compile("[\u0600-\u06FF]")


_TESS_LANGS: Optional[set] = None


def _tesseract_langs(binpath: str) -> set:
    global _TESS_LANGS
    if _TESS_LANGS is None:
        try:
            out = subprocess.run([binpath, "--list-langs"], capture_output=True,
                                 text=True, timeout=30)
            _TESS_LANGS = set(out.stdout.split())
        except Exception:
            _TESS_LANGS = set()
    return _TESS_LANGS


def _ocr_tsv_words(binpath: str, img_path: str, lang: str) -> list[tuple[int, int, int, int, int, int, int, float, str]]:
    try:
        out = subprocess.run(
            [binpath, img_path, "stdout", "-l", lang, '--psm', "6", "tsv"],
            capture_output=True, text=True, timeout=180)
    except Exception:
        return []
    words: list[tuple[int, int, int, int, int, int, int, float, str]] = []
    for line in (out.stdout or "").splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) < 12:
            continue
        conf, text = cols[10], cols[11]
        if conf == "-1" or not (text or '').strip():
            continue
        try:
            block, par, ln = int(cols[2]), int(cols[3]), int(cols[4])
            left, top, w, h = int(cols[6]), int(cols[7]), int(cols[8]), int(cols[9])
            words.append((block, par, ln, left, top, w, h, float(conf), text.strip()))
        except ValueError:
            continue
    return words


def _lane_centers(words: list[tuple[int, int, int, int, int, int, int, float, str]]) -> Optional[list[float]]:
    test_xs = sorted({w[3] for w in words if w[8].casefold().rstrip() == "test"})
    if not test_xs:
        return None
    clusters: list[int] = []
    for x in test_xs:
        if not clusters or x - clusters[-1] > 200:
            clusters.append(x)
    range_xs = sorted({w[3] for w in words if w[8].casefold().rstrip() == "range"})
    centers: list[float] = []
    for t in clusters:
        right = [r for r in range_xs if r > t]
        r = min(right) if right else t + 900
        centers.append((t + r) / 2.0)
    return centers or None


def _lane_index(x: int, centers: Sequence[float]) -> int:
    return int(min(range(len(centers)), key=lambda i: abs(x - centers[i])))


def _lane_bounds(centers: Sequence[float], img_w: int) -> list[tuple[int, int]]:
    mids = [int((centers[i] + centers[i + 1]) / 2) for i in range(len(centers) - 1)]
    edges = [0] + mids + [img_w]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def _satrha_from_words(words: list[tuple[int, int, int, int, int, int, int, float, str]],
                     centers: Optional[Sequence[float]] = None) -> list[list[tuple[int, int, int, int, int, int, int, float, str]]]:
    if not words:
        return []
    groups: dict[tuple, list[tuple[int, int, int, int, int, int, int, float, str]]] = {}
    for w in words:
        lane = None if centers is None else _lane_index(w[3], centers)
        groups.setdefault((lane, w[0], w[1], w[2]), []).append(w)
    rows = [grp for _, grp in sorted(groups.items(), key=lambda kv: min(x[4] for x in kv[1]))]


    tops_by_lane: dict[object, list[int]] = {}
    for grp in rows:
        lane = None if centers is None else _lane_index(min(x[3] for x in grp), centers)
        tops_by_lane.setdefault(lane, []).append(min(x[4] for x in grp))
    gaps: list[int] = []
    for ts in tops_by_lane.values():
        for i in range(len(ts) - 1):
            d = ts[i + 1] - ts[i]
            if 0 < d < 400:
                gaps.append(d)
    if gaps:
        gaps.sort()
        pitch = gaps[len(gaps) // 2]
        merge_gap = max(8.0, pitch * 0.55)
    else:
        merge_gap = 24.0

    merged: list[tuple[object, list[tuple[int, int, int, int, int, int, int, float, str]]]] = []
    for grp in rows:
        lane = None if centers is None else _lane_index(min(x[3] for x in grp), centers)
        if merged and merged[-1][0] == lane \
                and min(x[4] for x in grp) - max(x[4] + x[6] for x in merged[-1][1]) <= merge_gap:
            merged[-1][1].extend(grp)
        else:
            merged.append((lane, list(grp)))
    return [w for _, w in merged]


_FOOTER_RE = re.compile(
    r"\b(reviewed|approved|license|signature|electronically|generated|valid\s+without|"
    r"lab\s+comment|comment\b|for\s+any\s+questions|questions|contact)\b",
    re.IGNORECASE)


_JUNK_LINE_RE = re.compile(
    r"\b(page\s+\d+\s+of|work\s+timings?|received\s+on|referred?\s+by|ref\.?\s*by\b|"
    r"reg(?:istration)?\.?\s*no\.?\b|pid\s*[:=]|sample\s+collection|collection\s+(?:date|time)\b|"
    r"lab\s+(?:incharge|director|technician|manager|comment)\b|possible\s+causes?\b|"
    r"machine\s+error|typing\s+error|phone|mobile|e-?mail|website|www\.|https?://|"
    r"pin\s*code|pincode|\\b(?:road|street|complex|bungalow|building|floor|colony|"
    r"mumbai|delhi|chennai|kolkata|bengaluru|pune|india)\\b|\\d{7,}|"
    r"\\b(?:mr|mrs|ms|dr|prof)\\.\\s*[a-z])\\b",
    re.IGNORECASE)


def _looks_like_junk(line: str) -> bool:
    return bool(_JUNK_LINE_RE.search(line or ""))


_THRESHOLD_NOTE_RE = re.compile(
    r"\b(?:diabetic\s+patients?|prediabetic\s+patients?|prediabetes|prediahetes)\b"
    r"|\bpatients?\s*:"
    r"|\bno\s+risk\b"
    r"|\brisk\s*:"
    r"|\bdiabetes\s*:"
    r"|(?:borderline|bordertine)\s*[=:]"
    r"|\belevated\s*[>≥]",
    re.IGNORECASE)


def _looks_like_threshold_yaddasht(line: str) -> bool:
    return bool(_THRESHOLD_NOTE_RE.search(line or ''))


def _trim_lane_lines(lines: list[str]) -> list[str]:
    start = 0
    for i, l in enumerate(lines):
        if re.search(r"test\s+result\s+unit|result\s+unit\s+reference|reference\s+range", l, re.I):
            start = i
            break
    lines = lines[start:]
    out: list[str] = []
    for l in lines:
        if _FOOTER_RE.search(l):
            break
        out.append(l)
    return out


def _lines_from_satrha(rows: list[list[tuple[int, int, int, int, int, int, int, float, str]]]) -> list[str]:
    lines: list[str] = []
    for row in rows:
        row.sort(key=lambda x: x[3])
        if len(row) == 1 and not any(c.isdigit() for c in row[0][8]) and len(row[0][8]) <= 3:
            continue
        text = ' '.join(w[8] for w in row).strip()
        if text:
            lines.append(text)
    return lines


def reconstruct_columns(words: list[tuple[int, int, int, int, int, int, int, float, str]]) -> list[str]:
    centers = _lane_centers(words)
    return _lines_from_satrha(_satrha_from_words(words, centers))


def _reconstruct_from_words(binpath: str, img_path: str, lang: str,
                            words: list[tuple[int, int, int, int, int, int, int, float, str]],
                            img: Any) -> list[str]:
    centers = _lane_centers(words)
    if centers and len(centers) > 1 and img is not None:
        try:
            from PIL import Image as _PILImage
        except Exception:
            _PILImage = None
        if _PILImage is not None:
            lane_lines: list[str] = []
            for lo, hi in _lane_bounds(centers, img.size[0]):
                crop = img.crop((max(0, lo - 8), 0, min(img.size[0], hi + 8), img.size[1]))
                if crop.size[0] < 120:
                    continue


                for target in (1700, 2200):
                    c = crop
                    if c.size[0] < target:
                        r = target / c.size[0]
                        c = c.resize((int(c.size[0] * r), int(c.size[1] * r)), _PILImage.LANCZOS)
                    tmpc = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmpc.close()
                    try:
                        c.save(tmpc.name)
                        out = subprocess.run(
                            [binpath, tmpc.name, "stdout", "-l", lang, "--psm", "6"],
                            capture_output=True, text=True, timeout=180)
                        lane_lines.extend(_trim_lane_lines(
                            [l.strip() for l in (out.stdout or "").splitlines() if l.strip()]))
                    except Exception:
                        pass
                    finally:
                        try:
                            os.unlink(tmpc.name)
                        except Exception:
                            pass
            if len(lane_lines) >= 3:
                return lane_lines
    return _lines_from_satrha(_satrha_from_words(words, centers))


def _ocr_plain(binpath: str, img_path: str, lang: str, psm: str) -> list[str]:
    try:
        out = subprocess.run(
            [binpath, img_path, "stdout", "-l", lang, "--psm", psm],
            capture_output=True, text=True, timeout=180)
    except Exception:
        return []
    return [l.strip() for l in (out.stdout or '').splitlines() if l.strip()]


_GLITCH_RE = re.compile(r"[A-Za-z]\d|\$\d|=\s*\$|\b\d{5,}\b|[A-Za-z][-–—]\d")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


_FOOTNOTE_GLYPH_RE = re.compile(r"\d\s*[°”)\*>»]+\s*$")


def _line_glitched(line: str) -> bool:
    return bool(_GLITCH_RE.search(line))


def _line_quality(line: str) -> float:
    if not line:
        return -10.0


    line = normalize_digits(line)


    line = _repair_comma_decimals(line)
    s = 0.0
    if _line_glitched(line):
        s -= 0.6
    nums = _NUM_RE.findall(line)
    if nums:
        s += 1.0

    m = re.search(r"(\d+(?:\.\d+)?)\s*[-–—~]\s*(\d+(?:\.\d+)?)", line)
    val = None
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo > hi:

            return s - 2.5
        s += 2.0
        prefix = line[:m.start()]
        val = _last_number_before(prefix, nums)
        if val is not None:
            span = (hi - lo) or 1.0
            if lo <= val <= hi:
                s += 1.5
            else:
                near = lo if val < lo else hi
                rel = abs(val - near) / span


                s += 0.0 if rel <= 0.5 else -1.0
        else:


            s -= 2.0
    else:
        c = re.search(r"[<≤>≥]\s*(\d+(?:\.\d+)?)", line)
        if c:
            s += 0.75
            cutoff = float(c.group(1))
            prefix = line[:c.start()]
            val = _last_number_before(prefix, nums)
            if val is not None:
                if c.group(0)[0] in "<≤":
                    s += 1.5 if val <= cutoff else -1.0
                else:
                    s += 1.5 if val >= cutoff else -1.0
    return s


def _last_number_before(prefix: str, nums: list[str]) -> Optional[float]:
    pn = _NUM_RE.findall(prefix)
    if pn:
        try:
            return float(pn[-1])
        except ValueError:
            return None


    return None


def _latinish_satr(line: str) -> bool:
    letters = [c for c in line if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if c.lower() in "abcdefghijklmnopqrstuvwxyz")
    return latin / len(letters) >= 0.6


def _reconcile_lines(a_lines: list[str], b_lines: list[str]) -> list[str]:
    if not b_lines:
        return list(a_lines)
    out: list[str] = []
    used_b = [False] * len(b_lines)
    for la in a_lines:
        best_j, best_ratio, best_line = -1, 0.0, la
        for j, lb in enumerate(b_lines):
            if used_b[j]:
                continue
            r = difflib.SequenceMatcher(None, la, lb).ratio()
            if r >= 0.55 and r > best_ratio:
                best_ratio, best_j, best_line = r, j, lb
        if best_j >= 0:
            used_b[best_j] = True
            la_q = _line_quality(la)
            lb_q = _line_quality(best_line)
            if lb_q > la_q:
                out.append(best_line)
            elif la_q > lb_q:
                out.append(la)
            else:


                if _FOOTNOTE_GLYPH_RE.search(best_line) and not _FOOTNOTE_GLYPH_RE.search(la):
                    out.append(best_line)
                else:
                    out.append(la)
        else:
            out.append(la)
    for j, lb in enumerate(b_lines):
        if used_b[j]:
            continue
        if _looks_like_satr(lb) and all(
                difflib.SequenceMatcher(None, lb, la).ratio() < 0.55 for la in a_lines):
            out.append(lb)
    return out


_ROW_UNIT_HINT_RE = re.compile(
    r"\b(?:%|g/dl|g/l|mg/dl|mg/l|µg/dl|µg/l|mmol/l|µmol/l|umol/l|nmol/l|"
    r"u/l|iu/l|tu/l|u/ml|iu/ml|miu/l|miu/ml|ng/ml|ng/dl|ng/l|pg/ml|pg/l|"
    r"ug/dl|ug/ml|mcg/dl|mcg/ml|mm/h|mm/hr|fl|pg\b|10[\^°*]?[369]?\s*/|"
    r"ml/min|meq/l|kat/l)\b", re.IGNORECASE)


def _looks_like_satr(line: str) -> bool:
    if not line or not re.search(r"\d", line):
        return False
    if _ROW_UNIT_HINT_RE.search(line):
        return True
    return bool(re.search(r"\d\s*[-–—~]\s*\d", line))


def _deskew_pil(img: Any) -> Any:
    cv2 = _need_cv2()
    np = _need_np()
    Image = _need_pil()
    if cv2 is None or np is None or Image is None:
        return img
    try:


        max_angle, step, min_angle = 15.0, 0.25, 1.0
        gray = np.asarray(img, dtype=np.uint8)

        h, w = gray.shape[:2]
        small_w = min(w, 700)
        small = cv2.resize(gray, (small_w, max(1, int(h * small_w / w))),
                           interpolation=cv2.INTER_AREA)
        _, binary = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        sh, sw = binary.shape[:2]
        center = (sw // 2, sh // 2)
        best_angle, best_score = 0.0, -1.0
        for ang in np.arange(-max_angle, max_angle + step, step):
            M = cv2.getRotationMatrix2D(center, float(ang), 1.0)
            rot = cv2.warpAffine(binary, M, (sw, sh), flags=cv2.INTER_NEAREST,
                                 borderValue=0)
            proj = np.sum(rot, axis=1, dtype=np.float64)
            score = float(np.var(proj))
            if score > best_score:
                best_score, best_angle = score, float(ang)
        if abs(best_angle) < min_angle:
            return img
        M = cv2.getRotationMatrix2D((w // 2, h // 2), best_angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REPLICATE)
        return Image.fromarray(rotated)
    except Exception:
        return img


def _binarize_pil(img: Any) -> Any:
    cv2 = _need_cv2()
    np = _need_np()
    Image = _need_pil()
    if cv2 is None or np is None or Image is None:
        return img
    try:
        gray = np.asarray(img, dtype=np.uint8)
        gray = cv2.medianBlur(gray, 3)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(binary)
    except Exception:
        return img


class TesseractBackend(ExtractionBackend):
    name = 'tesseract'

    def __init__(self, language: str = "eng", preprocess: bool = True, dpi: int = 300,
                 unit_pattern: Optional[str] = None):
        self.language = language
        self.preprocess = preprocess
        self.dpi = dpi
        self.unit_pattern = unit_pattern or r"(?!)"

    @property
    def available(self) -> bool:
        return _need_pytesseract() is not None or _tesseract_binary() is not None

    def extract(self, upload: Any) -> str:
        data = self._as_bytes(upload)
        if not data:
            return ""
        Image = _need_pil()
        cv2 = _need_cv2()
        np = _need_np()
        tmp = None
        # Smart multi-column document extraction
        if cv2 is not None and np is not None and Image is not None:
            try:
                np_img = np.array(Image.open(io.BytesIO(data)).convert("RGB"))
                orig_h, orig_w, _ = np_img.shape
                if orig_w >= 800 and orig_h >= 600:
                    gray_mid = cv2.cvtColor(np_img[int(orig_h*0.1):int(orig_h*0.9), :], cv2.COLOR_RGB2GRAY)
                    proj = np.mean(gray_mid, axis=0)
                    w3 = orig_w / 3.0
                    g1_region = proj[int(w3*0.80):int(w3*1.20)]
                    g2_region = proj[int(w3*1.80):int(w3*2.20)]
                    if len(g1_region) > 0 and len(g2_region) > 0 and np.max(g1_region) > 225 and np.max(g2_region) > 225:
                        g1_x = int(w3*0.80) + int(np.argmax(g1_region))
                        g2_x = int(w3*1.80) + int(np.argmax(g2_region))
                        pyt = _need_pytesseract()
                        is_multi_panel = False
                        if pyt is not None:
                            col1_crop = np_img[int(orig_h*0.06):int(orig_h*0.96), g1_x:g2_x]
                            col1_probe = pyt.image_to_string(cv2.cvtColor(col1_crop, cv2.COLOR_RGB2GRAY), config="--psm 6", lang="eng").lower()
                            probe_hits = sum(1 for term in [
                                "glucose", "sugar", "urea", "bun", "creatinine", "uric", "protein", "albumin",
                                "bilirubin", "ast", "alt", "alp", "ggt", "ldh", "sodium", "potassium",
                                "calcium", "phosphorus", "cholesterol", "triglycerides", "iron", "ferritin", "tsh", "crp"
                            ] if re.search(r'\b' + term + r'\b', col1_probe))
                            if probe_hits >= 5:
                                is_multi_panel = True

                        if is_multi_panel:
                            col_slices = [
                                (int(orig_w*0.005), g1_x),
                                (g1_x, g2_x),
                                (g2_x, int(orig_w*0.995))
                            ]
                            col_lines = []
                            for cx1, cx2 in col_slices:
                                col_crop = np_img[int(orig_h*0.06):int(orig_h*0.96), cx1:cx2]
                                col_scaled = cv2.resize(col_crop, (col_crop.shape[1]*2, col_crop.shape[0]*2), interpolation=cv2.INTER_LANCZOS4)
                                col_gray = cv2.cvtColor(col_scaled, cv2.COLOR_RGB2GRAY)
                                txt = pyt.image_to_string(col_gray, config="--psm 6", lang="eng")
                                for l in txt.splitlines():
                                    sl = l.strip()
                                    if not sl:
                                        continue
                                    if any(h in sl.lower() for h in [
                                        "lab comment", "reviewed & approved", "clinical pathologist",
                                        "license no", "dr. m. hosseini", "h: high", "l: low"
                                    ]):
                                        break
                                    # Clean known optical artifacts in font
                                    sl = re.sub(r'\bHbAt1c\b', 'HbA1c', sl, flags=re.IGNORECASE)
                                    sl = re.sub(r'Basophils\s*%\s*(?:ald|WW|ll|1l|l1)\s*%', 'Basophils % 1.1 %', sl, flags=re.IGNORECASE)
                                    sl = re.sub(r'10[°\^][7\*]/[pP][lL]', '10^3/uL', sl)
                                    sl = re.sub(r'yg/d[lL]', 'ug/dL', sl)
                                    sl = re.sub(r'HIU/mL', 'uIU/mL', sl)
                                    sl = re.sub(r'mg/db', 'mg/dL', sl)
                                    sl = re.sub(r'pg/db', 'ug/dL', sl)
                                    sl = re.sub(r'g/db', 'g/dL', sl)
                                    col_lines.append(sl)
                            if len(col_lines) >= 15:
                                return "\n".join(col_lines)
            except Exception as e:
                pass
        try:
            img_path = None
            if Image is not None:
                img = Image.open(io.BytesIO(data))
                w, h = img.size


                if w < 1000:
                    scale = max(1.5, min(3.0, 1500.0 / w))
                    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                img = img.convert("L")

                img = _deskew_pil(img)
                if self.preprocess:
                    try:
                        from PIL import ImageOps, ImageFilter
                        img = ImageOps.autocontrast(img)
                        img = img.filter(ImageFilter.SHARPEN)
                    except Exception:
                        pass
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.close()
                img.save(tmp.name)
                img_path = tmp.name
            else:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(data)
                tmp.flush()
                tmp.close()
                img_path = tmp.name

            lang = "fas+eng" if self.language == 'both' else (self.language or "eng")
            binpath = _tesseract_binary()
            if lang == "fas+eng" and binpath and "fas" not in _tesseract_langs(binpath):
                lang = "eng"
            lines: list[str] = []

            pyt = _need_pytesseract()
            if pyt is not None and cv2 is not None and np is not None:

                try:
                    gray = np.array(Image.open(img_path).convert("L"))
                    text = pyt.image_to_string(gray, config="--psm 6", lang=lang.replace('+', "+"))
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                except Exception:
                    lines = []

            if binpath:
                if not lines:
                    lines = _ocr_plain(binpath, img_path, lang, "6")


                if len(lines) < 5:
                    lines = _reconcile_lines(lines, _ocr_plain(binpath, img_path, lang, '4'))


                if "fas" in lang:
                    eng_lines = [l for l in _ocr_plain(binpath, img_path, "eng", "6")
                                 if _latinish_satr(l)]
                    if eng_lines:
                        lines = _reconcile_lines(lines, eng_lines)


                if len(lines) < 8:
                    tsv_lines: list[str] = []
                    try:
                        words = _ocr_tsv_words(binpath, img_path, lang)
                        if words:
                            tsv_lines = _reconstruct_from_words(binpath, img_path, lang, words, img)
                    except Exception:
                        tsv_lines = []
                    if tsv_lines and self._satr_emtiaz(tsv_lines) > self._satr_emtiaz(lines):
                        lines = tsv_lines
                if not lines:
                    for psm in ('4', "11", "3"):
                        lines = _ocr_plain(binpath, img_path, lang, psm)
                        if len(lines) >= 3:
                            break


            if binpath and Image is not None and (len(lines) < 8 or self._satr_emtiaz(lines) < 4):
                try:
                    raw_img = Image.open(io.BytesIO(data)).convert("L")
                    w0, h0 = raw_img.size
                    if w0 < 2400:
                        s0 = max(2.0, min(6.0, 2400.0 / w0))
                        raw_img = raw_img.resize((int(w0 * s0), int(h0 * s0)), Image.LANCZOS)
                    bin_img = _binarize_pil(_deskew_pil(raw_img))
                    tmp2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp2.close()
                    try:
                        bin_img.save(tmp2.name)
                        bin_lines = _ocr_plain(binpath, tmp2.name, lang, "6")
                        bin_lines = _reconcile_lines(bin_lines, _ocr_plain(binpath, tmp2.name, lang, "4"))
                        if self._satr_emtiaz(bin_lines) > self._satr_emtiaz(lines):
                            lines = bin_lines
                    finally:
                        try:
                            os.unlink(tmp2.name)
                        except Exception:
                            pass
                except Exception:
                    pass
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("Tesseract extraction failed: %s", exc)
            return ''
        finally:
            if tmp:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass

    def _satr_emtiaz(self, lines: Sequence[str]) -> int:
        unit_re = re.compile(self.unit_pattern, re.IGNORECASE)
        score = 0
        for l in lines:
            if not l or not re.search(r"\d", l):
                continue
            if unit_re.search(l) or re.search(r"\d\s*[-–—~]\s*\d", l):
                score += 1
        return score

    @staticmethod
    def _as_bytes(upload: Any) -> Optional[bytes]:
        if isinstance(upload, (bytes, bytearray)):
            return bytes(upload)
        if isinstance(upload, str) and Path(upload).is_file() and not upload.lower().endswith((".txt", '.csv')):
            try:
                return Path(upload).read_bytes()
            except Exception:
                return None
        if hasattr(upload, 'read'):
            try:
                return upload.read()
            except Exception:
                return None
        return None


class PaddleBackend(ExtractionBackend):
    name = "paddle"

    def __init__(self, language: str = "fa"):
        self.language = language
        self._ocr_engine = None

    @property
    def available(self) -> bool:
        return _need_paddle() is not None

    def extract(self, upload: Any) -> str:
        PaddleOCR = _need_paddle()
        if PaddleOCR is None:
            return ""
        if self._ocr_engine is None:
            try:
                self._ocr_engine = PaddleOCR(use_angle_cls=True, lang=self.language, show_log=False)
            except Exception as exc:
                logger.error("PaddleOCR init failed: %s", exc)
                return ''
        data = TesseractBackend._as_bytes(upload)
        if not data:
            return ""
        try:
            import io
            import numpy as np
            Image = _need_pil()
            if Image is None:
                return ""
            img = Image.open(io.BytesIO(data))
            arr = np.array(img)
            if len(arr.shape) == 2:
                arr = np.stack((arr,) * 3, axis=-1)
            elif arr.shape[2] == 4:
                arr = arr[:, :, :3]
            result = self._ocr_engine.ocr(arr, cls=True)
            if not result or not result[0]:
                return ""
            boxes = []
            for line in result[0]:
                pts, (text, conf) = line
                if text and text.strip():
                    boxes.append((min(p[1] for p in pts), min(p[0] for p in pts), text.strip()))
            boxes.sort(key=lambda b: b[0])
            rows, curr, curr_y = [], [], None
            for b in boxes:
                if curr_y is None or abs(b[0] - curr_y) <= 12:
                    curr.append(b); curr_y = b[0]
                else:
                    curr.sort(key=lambda x: x[1])
                    rows.append(" ".join(x[2] for x in curr))
                    curr, curr_y = [b], b[0]
            if curr:
                curr.sort(key=lambda x: x[1])
                rows.append(" ".join(x[2] for x in curr))
            return "\n".join(rows)
        except Exception as exc:
            logger.warning("PaddleOCR extraction failed: %s", exc)
            return ''


def _row_key(row: Mapping[str, Any]) -> str:
    name = str(row.get("test_name") or row.get("name") or "").strip().lower()
    return re.sub(r"[\s\.\-_()/:]+", "", name)


def _row_value_sig(row: Mapping[str, Any]) -> tuple:
    v = row.get("value")
    try:
        v = round(float(str(v).replace(",", "")), 6)
    except (TypeError, ValueError):
        v = str(v).strip().lower() if v is not None else None
    return (v, str(row.get("unit") or "").strip().lower(), str(row.get("flag") or "").strip().lower())


def merge_vision_passes(passes: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    """Merge the structured rows of several vision passes by test name.

    Returns rows in first-pass order (then rows only later passes saw), each
    with `_agreement` in {"agree", "disagree", "single"}, `_passes` (how many
    passes produced the row) and, on disagreement, `_alternatives` with the
    other readings. Pure function - unit-tested without network access."""
    n = len(passes)
    seen: dict[str, list[Mapping[str, Any]]] = {}
    order: list[str] = []
    for rows in passes:
        local: set[str] = set()
        for row in rows or []:
            k = _row_key(row)
            if not k or k in local:
                continue
            local.add(k)
            if k not in seen:
                seen[k] = []
                order.append(k)
            seen[k].append(row)
    merged: list[dict[str, Any]] = []
    for k in order:
        rows = seen[k]
        base = dict(rows[0])
        sigs = {_row_value_sig(r) for r in rows}
        if len(rows) == 1 and n > 1:
            base["_agreement"] = "single"
        elif len(sigs) == 1:
            base["_agreement"] = "agree"
        else:
            counts: dict[tuple, int] = {}
            for r in rows:
                counts[_row_value_sig(r)] = counts.get(_row_value_sig(r), 0) + 1
            best_sig = max(counts.items(), key=lambda kv: kv[1])[0]
            if counts[best_sig] > 1:
                base = dict(next(r for r in rows if _row_value_sig(r) == best_sig))
            base["_agreement"] = "disagree"
            base["_alternatives"] = [
                {"value": r.get("value"), "unit": r.get("unit"), "flag": r.get("flag")}
                for r in rows if _row_value_sig(r) != _row_value_sig(base)]
        base["_passes"] = len(rows)
        merged.append(base)
    return merged


class VisionBackend(ExtractionBackend):
    name = "vision"

    def __init__(self, api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 base_url: Optional[str] = None, timeout: float = 90.0,
                 language: str = 'en'):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.language = language
        self._client = None
        self.last_error: str = ""

        # Smart default model based on API Key prefix
        if model:
            self.model = model
        elif api_key and (api_key.startswith("sk-proj-") or api_key.startswith("sk-")):
            self.model = "gpt-4o-mini"
        elif api_key and api_key.startswith("gsk_"):
            self.model = os.getenv("OCR_VISION_MODEL") or "qwen/qwen3.8-27b"
        else:
            self.model = os.getenv("OCR_VISION_MODEL") or "qwen/qwen3.8-27b"

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            self.last_error = "API key is missing or empty."
            sys.stderr.write("[OCR Vision] Error: API key is missing.\n")
            return None
        try:
            from openai import OpenAI
            kwargs = {"api_key": self.api_key, "timeout": self.timeout}
            base_url = self.base_url or os.getenv("OCR_BASE_URL")
            if not base_url and self.api_key:
                if self.api_key.startswith("gsk_"):
                    base_url = "https://api.groq.com/openai/v1"
                elif self.api_key.startswith("sk-or-") or (self.model and "/" in self.model):
                    base_url = "https://openrouter.ai/api/v1"
            if base_url:
                kwargs["base_url"] = base_url
            self._client = OpenAI(**kwargs)
            return self._client
        except ImportError as exc:
            self.last_error = f"Required Python package 'openai' is not installed: {exc}"
            logger.error(self.last_error)
            sys.stderr.write(f"[OCR Vision] Error: {self.last_error}\n")
            return None
        except Exception as exc:
            self.last_error = f"Failed to initialize OpenAI client: {exc}"
            logger.error(self.last_error)
            sys.stderr.write(f"[OCR Vision] Error: {self.last_error}\n")
            return None

    @property
    def available(self) -> bool:
        return self.api_key is not None

    def extract(self, upload: Any) -> str:
        client = self._get_client()
        if client is None:
            return ''
        pages = self._namayesh_pages(upload)
        if pages:
            chunks = []
            for blob, mime in pages:
                url = f"data:{mime};base64," + base64.b64encode(blob).decode()
                text = self._extract_with_agreement(client, url)
                if text:
                    chunks.append(text)
            return "\n".join(chunks).strip()
        data = self._as_dade_url(upload)
        if not data:
            self.last_error = f"Invalid image or file path: {upload}"
            sys.stderr.write(f"[OCR Vision] Error: {self.last_error}\n")
            return ""
        return self._extract_with_agreement(client, data)

    def _extract_with_agreement(self, client: Any, data: str) -> str:
        """Run the vision model `OCR_VISION_PASSES` times (default 1) and
        merge the structured rows by test name. Rows whose value, unit and
        flag agree across passes are tagged `_agreement: "agree"`; rows that
        differ are tagged `"disagree"` and carry both readings so the mapper
        can force human review; rows seen in a single pass are tagged
        `"single"`. Vision LLM output is not deterministic even at
        temperature 0, so a second pass is the cheapest honest confidence
        signal available without ground truth."""
        passes = max(1, min(3, int(os.getenv("OCR_VISION_PASSES", "1") or 1)))
        first = self._estekhraj_from_tasvir_url(client, data)
        if passes == 1 or not first:
            return first
        outputs = [first]
        for _ in range(passes - 1):
            t = self._estekhraj_from_tasvir_url(client, data)
            if t:
                outputs.append(t)
        if len(outputs) == 1:
            return first
        merged = merge_vision_passes([BloodLabPipeline._try_tafsir_structured(t) or [] for t in outputs])
        return json.dumps(merged, ensure_ascii=False) if merged else first

    def _estekhraj_from_tasvir_url(self, client: Any, data: str) -> str:
        prompt = (
            "You are a precision medical laboratory report digitizer (CBC, chemistry, "
            "hormones, renal, liver, thyroid — any panel). The image may use ANY layout: "
            "multi-column tables (Test/Result/Unit/Reference), key-value lists, or mixed text.\n\n"
            "STRICT COLUMN RULES:\n"
            "- value = the patient's measured result ONLY (bold/colored number or plain integer/float), e.g. 5380, 4.89, 12.7, 282000.\n"
            "- test_name = exact test marker name e.g. 'WBCs', 'RBCs', 'Hb', 'Hct', 'P-LCR', 'SGOT(AST)', 'SGPT(ALT)', 'Alk.Phosphatase', 'Fasting Blood Glucose'.\n"
            "- unit = exactly as printed (g/dL, gr/dL, %, fL, pg, /uL, mil/uL, U/L, U/ml, IU/L, mg/dL...).\n"
            "- flag: printed flag first (H/L/High/Low/Borderline); else null.\n"
            "- reference_range = the printed reference interval for that row exactly as printed (e.g. '12-16', '4.0 - 10.0', '<200'); else null.\n\n"
            "READ EVERY RESULT ROW without exception.\n"
            "SKIP: panel titles without values ('CBC', 'General Biochemistry'), headers ('Test Result Unit'), and footer notes ('Results reported by...').\n"
            "Do not invent or correct anything. If a row is unreadable, omit it.\n\n"
            "OUTPUT: a single MINIFIED JSON array only (no whitespace, no markdown, no commentary, no reasoning text):\n"
            '[{"test_name":"WBCs","value":5380,"unit":"/uL","flag":null,"reference_range":"4000-10000"},'
            '{"test_name":"SGOT(AST)","value":26,"unit":"IU/L","flag":null,"reference_range":"<40"}]'
        )

        # Build candidate models depending on key and user preference
        models_to_try = [self.model]
        is_openai_key = self.api_key and (self.api_key.startswith("sk-proj-") or self.api_key.startswith("sk-"))
        is_groq_key = self.api_key and self.api_key.startswith("gsk_")

        if is_openai_key:
            for m_cand in ["gpt-4o-mini", "gpt-4o"]:
                if m_cand not in models_to_try:
                    models_to_try.append(m_cand)
        elif is_groq_key:
            # Groq free/developer tier (2026-07-17 deprecations): llama-4-scout and qwen3-32b are gone;
            # qwen3.8-27b is the only vision-capable model left on the self-serve tier.
            for m_cand in [
                "qwen/qwen3.8-27b",
            ]:
                if m_cand not in models_to_try:
                    models_to_try.append(m_cand)
        else:
            # Fallback for generic proxies / custom endpoints
            for m_cand in ["qwen/qwen3.8-27b", "gpt-4o-mini"]:
                if m_cand not in models_to_try:
                    models_to_try.append(m_cand)

        import re as _re
        max_tok = int(os.getenv("OCR_VISION_MAX_TOKENS", "4096"))
        for m in models_to_try:
            try:
                sys.stdout.write(f"[OCR Vision] Calling model '{m}' with API key...\n")
                sys.stdout.flush()
                _msgs = [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", 'image_url': {"url": data}},
                ]}]
                # 950 tokens truncated any panel beyond ~25 rows; a full 2-page chemistry + CBC report
                # needs ~2500.  BUT Groq's free tier enforces an output-tokens-per-minute cap (currently
                # 1000 for qwen3.8-27b) and rejects the request up-front with HTTP 429 when max_tokens
                # exceeds it.  Strategy: ask for the full budget; on that specific 429 parse the enforced
                # limit and retry once with max_tokens just under it (compact JSON keeps most panels < 900).
                # Qwen3.x on Groq is a reasoning model: hidden "thinking" tokens count against the output
                # budget, so switch reasoning off when the provider accepts the parameter.
                _extra = {"reasoning_effort": "none"} if ("qwen3" in m and is_groq_key) else {}
                def _call(_mt_):
                    try:
                        return client.chat.completions.create(model=m, messages=_msgs, temperature=0.0, max_tokens=_mt_, extra_body=_extra)
                    except Exception as _ep:
                        if _extra and "reasoning" in str(_ep).lower():
                            return client.chat.completions.create(model=m, messages=_msgs, temperature=0.0, max_tokens=_mt_)
                        raise
                try:
                    resp = _call(max_tok)
                except Exception as _e429:
                    _txt = str(_e429)
                    _mt = _re.search(r"[Ll]imit\s+(\d+)\s*,\s*Requested\s+(\d+)", _txt)
                    if "429" in _txt and "tokens" in _txt and _mt and int(_mt.group(1)) < max_tok:
                        _lim = max(256, int(_mt.group(1)) - 40)
                        sys.stdout.write(f"[OCR Vision] Provider output-token cap {_mt.group(1)} < {max_tok}; retrying '{m}' with max_tokens={_lim}.\n")
                        sys.stdout.flush()
                        resp = _call(_lim)
                    else:
                        raise
                text = (resp.choices[0].message.content or '').strip()
                if text:
                    sys.stdout.write(f"[OCR Vision] Successfully received extraction from '{m}' ({len(text)} chars).\n")
                    sys.stdout.flush()
                    self.last_error = ""
                    return text
            except Exception as exc:
                err_msg = f"{exc.__class__.__name__}: {exc}"
                self.last_error = err_msg
                logger.warning("Vision extraction attempt failed with model %s: %s", m, exc)
                sys.stderr.write(f"[OCR Vision ERROR] Model '{m}' failed: {err_msg}\n")
                sys.stderr.flush()
        return ""

    @staticmethod
    def _namayesh_pages(upload: Any, max_pages: int = 4, dpi: int = 160) -> list[tuple[bytes, str]]:
        fitz = _need_fitz()
        images: list[tuple[bytes, str]] = []
        if not fitz:
            return images
        try:
            doc = None
            if isinstance(upload, str) and upload.lower().endswith(".pdf"):
                doc = fitz.open(upload)
            elif isinstance(upload, (bytes, bytearray)) and bytes(upload).startswith(b"%PDF"):
                doc = fitz.open(stream=bytes(upload), filetype="pdf")
            if not doc:
                return images
            Image = _need_pil()
            import io
            for page_number in range(min(len(doc), max_pages)):
                pix = doc[page_number].get_pixmap(dpi=dpi)
                blob = pix.tobytes("png")
                mime = 'image/png'
                if Image:
                    try:
                        im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                        buf = io.BytesIO()
                        im.save(buf, format="JPEG", quality=88, optimize=True)
                        blob = buf.getvalue()
                        mime = 'image/jpeg'
                    except Exception:
                        pass
                images.append((blob, mime))
            doc.close()
        except Exception as exc:
            logger.warning("PDF render failed: %s", exc)
        return images

    @staticmethod
    def _as_dade_url(upload: Any) -> Optional[str]:
        if isinstance(upload, str) and upload.lower().startswith(("data:", "http")):
            return upload
        if isinstance(upload, str) and Path(upload).is_file():
            try:
                mime = mimetypes.guess_type(upload)[0] or "image/png"
                if not mime.startswith("image/"):
                    return None
                data = Path(upload).read_bytes()
                if len(data) > 2_500_000:
                    Image = _need_pil()
                    if Image:
                        import io
                        im = Image.open(io.BytesIO(data)).convert("RGB")
                        im.thumbnail((1800, 1800))
                        buf = io.BytesIO()
                        im.save(buf, format='JPEG', quality=88, optimize=True)
                        data = buf.getvalue()
                        mime = "image/jpeg"
                return f"data:{mime};base64," + base64.b64encode(data).decode()
            except Exception:
                return None
        if isinstance(upload, (bytes, bytearray)):
            return "data:image/png;base64," + base64.b64encode(bytes(upload)).decode()
        return None


class PassthroughBackend(ExtractionBackend):
    name = "passthrough"

    def __init__(self, language: str = "en"):
        self.language = language

    def extract(self, upload: Any) -> str:
        if isinstance(upload, str):
            if upload.lower().endswith((".txt", ".csv", ".tsv")):
                try:
                    return Path(upload).read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    return ''
            return upload
        if isinstance(upload, (bytes, bytearray)):
            return bytes(upload).decode('utf-8', errors='ignore')
        if hasattr(upload, "read"):
            try:
                return upload.read().decode('utf-8', errors='ignore')
            except Exception:
                return ""
        return ""


_CONF_WEIGHTS = {"name": 0.45, "engine": 0.20, "unit": 0.15, "value": 0.10, 'context': 0.10}  # legacy blend (documentation only)
import ocr_confidence as _ocr_conf  # noqa: E402  additive log-odds evidence model
_METADATA_RE = re.compile(
    r"^(patient|pt\b|dob|date of birth|name\b|age|sex|gender|born|id|mrn|accession|"
    r"sample\b|fasting\s*:|referring|ref\.?\s*by|physician|doctor|dr\b|hospital|clinic|address|phone|tel\b|fax|email|"
    r"account|lab\s*(rep|reference|report|results?|values?)|page\s*\d|collection|collected|"
    r"received|reported|registered|generated|instrument|instruments|interpretation|"
    r"specimen|comment|comments?|notes?|important|result\s+unit\s+ref|test\s+name\b|"
    r"results reported by|hitachi|roche|diagnostics|general biochemistry|cbc\b|"
    r"license|reviewed|approved|clinical|pathologist|electronically|valid|without|signature|"
    r"questions|contact|reference\s+range|reference\s+value|"
    r"بیمار|نام|سن|جنس|تاریخ|پزشک|بیمارستان|آزمایشگاه|پاتوبیولوژی|ژنتیک|پذیرش|"
    r"مراجعه|نمونه|کد ملی|شماره پرونده|تلفن)",
    re.IGNORECASE,
)
_HEADER_LINE_RE = re.compile(
    r"^(result|value|unit|ref(erence)?(\s+value)?|range|flag|status|investigation|test|method|"
    r"blood\s+chemicals|hematology|haematology|complete\s+blood\s+count.*|general\s+biochemistry|"
    r"test\s+result\s+unit.*)\s*$",
    re.IGNORECASE,
)
_DIGITS_ONLY_RE = re.compile(r"^[\d\s\-.:/]+$")


_DUAL_DIFF_RE = re.compile(
    r"^(?P<name>[^\d%]+?)\s+(?P<pct>\d{1,3}(?:\.\d+)?)\s*%\s+"
    r"(?P<abs>\d{1,3}(?:\.\d+)?)\s+(?P<unit>x?10\^?\s*(?:9|12)\s*/[lL])\s*"
    r"(?P<tail>.*)$")



# ---------------------------------------------------------------------------
# Pre-analytical / specimen provenance flags read from the report text (2026-10-23).
# Printed HIL indices or comments ("hemolyzed", "lipemic", "همولیز") are the single most
# common cause of spurious hyperkalaemia / raised LDH-AST; the engine's preanalytical_gate
# already down-weights the affected analytes when the flags are passed in the clinical
# context (keys hemolysis / lipemia / icterus) - this detector closes the OCR -> engine gap.
_PREANALYTICAL_PATTERNS = {
    "hemolysis": re.compile(r"\b(h[ae]moly[sz](?:ed|is|e)|hemoliz|hem\.?\s*index|h[- ]?index\s*[:=]?\s*(?:[2-9]|[1-9]\d+|\+{1,3}|moderate|severe|gross)|\bHIL\b.*\bH\s*[:=]\s*[1-9]|همولیز|همولیزه|لیز\s*شده)", re.IGNORECASE),
    "lipemia": re.compile(r"\b(lip[ae]mi[ac]|lipemic|l[- ]?index\s*[:=]?\s*(?:[2-9]|[1-9]\d+|\+{1,3}|moderate|severe)|turbid|chylous|لیپمیک|لیپمی|کدر)", re.IGNORECASE),
    "icterus": re.compile(r"\b(icteri[ac]|icterus|i[- ]?index\s*[:=]?\s*(?:[2-9]|[1-9]\d+|\+{1,3}|moderate|severe)|ایکتریک|ایکتر)", re.IGNORECASE),
    "clotted": re.compile(r"\b(clotted|clot\s*(?:present|detected)|لخته)", re.IGNORECASE),
    "recollect": re.compile(r"\b(re-?collect(?:ion)?\s*(?:requested|required|advised)|repeat\s+sample|نمونه\s*مجدد|تکرار\s*نمونه)", re.IGNORECASE),
}
_NEGATED_PREANALYTICAL = re.compile(r"\b(no|non|not|without|absent|negative|نه|بدون|فاقد)\W{0,3}(h[ae]moly|lip[ae]mi|icter|همولیز|لیپمی|ایکتر)", re.IGNORECASE)
_SPECIMEN_PATTERNS = (
    ("arterial_blood", re.compile(r"\b(arterial|ABG|خون\s*شریانی)\b", re.IGNORECASE)),
    ("venous_blood", re.compile(r"\b(venous|VBG|خون\s*وریدی)\b", re.IGNORECASE)),
    ("urine", re.compile(r"\b(urine|urinalysis|U/A|ادرار)\b", re.IGNORECASE)),
    ("csf", re.compile(r"\b(CSF|cerebrospinal|مایع\s*مغزی)\b", re.IGNORECASE)),
    ("plasma", re.compile(r"\b(plasma|پلاسما)\b", re.IGNORECASE)),
    ("serum", re.compile(r"\b(serum|سرم)\b", re.IGNORECASE)),
    ("whole_blood", re.compile(r"\b(whole\s*blood|EDTA|خون\s*کامل)\b", re.IGNORECASE)),
)
_COLLECTED_AT = re.compile(r"(collect(?:ed|ion)(?:\s*(?:date|time|at))?|sampl(?:e|ing)\s*(?:date|time)|drawn|تاریخ\s*(?:نمونه|پذیرش|جمع\s*آوری)|ساعت\s*نمونه)\s*[:：]?\s*([0-9]{2,4}[/\-.][0-9]{1,2}[/\-.][0-9]{1,4}(?:[ T,]+[0-9]{1,2}:[0-9]{2})?)", re.IGNORECASE)
_MORPHOLOGY_TERMS = re.compile(r"\b(blasts?\s*(?:seen|present|\d+\s*%)|toxic\s+granulation|left\s+shift|schistocytes?|spherocytes?|target\s+cells?|rouleaux|anisocytosis|poikilocytosis|hypersegmented|smudge\s+cells?|atypical\s+lymph|dohle|d[öo]hle|nucleated\s+rbc|nRBC|sickle|teardrop|dacrocyte|basophilic\s+stippling|howell[- ]jolly|platelet\s+clump|auer\s+rods?)\b", re.IGNORECASE)


def detect_preanalytical(raw_text: str) -> dict[str, Any]:
    """Return {flags: {hemolysis: bool, ...}, evidence: {kind: snippet}, specimen: str|None,
    collected_at: str|None, morphology: [terms]} from the OCR text. Conservative: a negated
    mention ("non-hemolyzed", "no hemolysis") never sets a flag."""
    text = raw_text or ""
    out: dict[str, Any] = {"flags": {}, "evidence": {}, "specimen": None, "collected_at": None, "morphology": []}
    if not text.strip():
        return out
    for kind, rx in _PREANALYTICAL_PATTERNS.items():
        for m in rx.finditer(text):
            window = text[max(0, m.start() - 12):m.start()]
            if _NEGATED_PREANALYTICAL.search(window + m.group(0)):
                continue
            out["flags"][kind] = True
            out["evidence"][kind] = text[max(0, m.start() - 25):m.end() + 25].replace("\n", " ").strip()
            break
    for name, rx in _SPECIMEN_PATTERNS:
        if rx.search(text):
            out["specimen"] = name
            break
    m = _COLLECTED_AT.search(text)
    if m:
        out["collected_at"] = m.group(2)
    seen: list[str] = []
    for m in _MORPHOLOGY_TERMS.finditer(text):
        t = re.sub(r"\s+", " ", m.group(0).lower())
        if t not in seen:
            seen.append(t)
    out["morphology"] = seen[:12]
    return out


class BloodLabPipeline:
    def __init__(self, *, api_key: Optional[str] = None, registry_path: str | Path = "",
                 registry: Optional[FeatureRegistry] = None,
                 enable_derived: bool = False, language: str = "en",
                 backend: Optional[str] = None, vision_model: Optional[str] = None,
                 min_auto_accept: float = 0.86, similarity: Optional[float] = None):
        self.api_key = api_key
        self.language = language
        self.enable_derived = enable_derived
        self.min_auto_accept = min_auto_accept
        if not registry and not registry_path:
            for cand_name in ["HEMOGLYPH_FEATURE_REGISTRY.json.br", "HEMOGLYPH_FEATURE_REGISTRY.json"]:
                for base in [Path.cwd(), Path(sys.executable).resolve().parent, Path(__file__).resolve().parent]:
                    cand = base / cand_name
                    if cand.is_file():
                        registry_path = cand
                        break
                if registry_path:
                    break
        self.registry = registry or (FeatureRegistry.shared(registry_path) if registry_path else None)
        self.normalizer = self.registry.normalizer if self.registry else TextNormalizer()
        self._support = self.registry.ocr if self.registry else OCRSupport()
        self.parser = ReportLineParser(support=self._support)
        self.backend: ExtractionBackend = self._entekhab_backend(backend, vision_model)

    def _entekhab_backend(self, backend: Optional[str], vision_model: Optional[str]) -> ExtractionBackend:
        backend = backend or os.getenv("OCR_BACKEND")
        vision_model = vision_model or os.getenv("OCR_VISION_MODEL")
        base_url = os.getenv("OCR_BASE_URL")

        # 1. When an API key exists or backend is explicitly vision -> VISION IS ABSOLUTE TOP PRIORITY
        if backend == "vision" or (self.api_key and backend in (None, "", "auto")):
            if not base_url and self.api_key:
                if self.api_key.startswith("gsk_"):
                    base_url = "https://api.groq.com/openai/v1"
                elif self.api_key.startswith("sk-or-") or (vision_model and "/" in vision_model):
                    base_url = "https://openrouter.ai/api/v1"
            vis = VisionBackend(api_key=self.api_key, model=vision_model or self._vision_default(),
                                base_url=base_url, language=self.language)
            if vis.available:
                return vis

        # 2. Explicit backend overrides
        if backend == "paddle":
            paddle = PaddleBackend(language="fa")
            if paddle.available:
                return paddle
        if backend == "tesseract":
            tess = TesseractBackend(language="both", unit_pattern=self._support.unit_pattern)
            if tess.available:
                return tess
            return PassthroughBackend(self.language)
        if backend == "passthrough":
            return PassthroughBackend(self.language)
        if backend == "rawtext":
            return RawTextBackend()

        # 3. Fallbacks when no API key is present
        tess = TesseractBackend(language="both" if self.language == "fa" else "eng",
                                unit_pattern=self._support.unit_pattern)
        if tess.available and _tesseract_binary() is not None:
            return tess
        paddle = PaddleBackend(language="fa")
        if paddle.available:
            return paddle
        if tess.available:
            return tess
        return PassthroughBackend(self.language)

    def _vision_default(self) -> str:
        return os.getenv("OCR_VISION_MODEL") or 'qwen/qwen3.8-27b'

    def _tashkhis_zaban(self, text: str) -> str:
        return 'fa' if re.search(r"[\u0600-\u06FF]", text) else 'en'

    def process(self, upload: Any, panel_hint: Optional[str] = None) -> dict[str, Any]:
        raw_text = None
        if isinstance(upload, str):
            looks_like_path = False
            try:
                looks_like_path = len(upload) <= 4096 and Path(upload).is_file()
            except OSError:
                looks_like_path = False
            if not looks_like_path:
                raw_text = upload
        if raw_text is None:
            raw_text = self.backend.extract(upload)


        if (not raw_text or len(raw_text.splitlines()) < 3) and self.api_key \
                and getattr(self.backend, 'name', "") != "vision":
            vis = VisionBackend(api_key=self.api_key, model=self._vision_default(),
                                base_url=os.getenv("OCR_BASE_URL"), language=self.language)
            if vis.available:
                try:
                    alt = vis.extract(upload)
                except Exception:
                    alt = ""
                if alt and (not raw_text or len(alt.splitlines()) > len(raw_text.splitlines())):
                    raw_text = alt
        if not raw_text:
            err_msg = "No text could be extracted from the report."
            if hasattr(self.backend, "last_error") and self.backend.last_error:
                err_msg = f"Vision OCR failed: {self.backend.last_error}"
            sys.stderr.write(f"[BloodLabPipeline ERROR] {err_msg}\n")
            sys.stderr.flush()
            return self._empty_natije(err_msg,
                                      warnings=["Verify the file is a readable image, API key is valid, and network is connected."])
        doc_lang = self._tashkhis_zaban(raw_text)
        normalized = normalize_extracted_text(raw_text, self._support.persian_unit_aliases)
        normalized = repair_ocr_matn(normalized, self._support)

        structured = self._try_tafsir_structured(raw_text) or self._try_tafsir_structured(normalized)
        if structured is not None:
            results = self._negasht_structured_satrha(structured)
        else:
            lines = [_yeksansazi_model_line(l) for l in normalized.splitlines() if l.strip()]
            lines = _tafkik_multi_azmayesh_lines(lines, self._support)
            results = self._tafsir_and_negasht(lines, panel_hint)

        # Structural self-consistency pass: the panel's own arithmetic
        # (red-cell indices, differential sum, Friedewald, bilirubin
        # fractions, urea/BUN, anion gap ...) plus hard physiological limits
        # and the printed H/L flags localise OCR digit errors to a field and
        # propose the single reading that restores consistency.
        consistency: dict[str, Any] = {}
        try:
            from ocr_consistency import validate_results as _validate_consistency
            consistency = dict(_validate_consistency(
                results, registry_features=(self.registry.features if self.registry else None)))
        except Exception as exc:  # never let the validator break extraction
            consistency = {"error": f"consistency validation unavailable: {exc}"}

        confidence = 0.0
        if results:
            confidence = sum(r.get("confidence", 0.0) for r in results) / len(results)
        warnings = [
            "OCR output is unverified; every value requires human confirmation before analysis.",
            f"Document language detected: {doc_lang}; extraction backend: {self.backend.name}.",
        ]
        n_manual = sum(1 for r in results if r.get("suggested_action") == "edit_or_reject")
        if n_manual:
            warnings.append(f"{n_manual} item(s) need review/editing before analysis.")
        if consistency.get("checks_run"):
            warnings.append(
                f"Panel self-consistency: {consistency.get('checks_passed', 0)}/{consistency.get('checks_run', 0)} "
                f"identities hold; {len(consistency.get('suspects') or [])} suspect value(s), "
                f"{consistency.get('repairs_suggested', 0)} repair(s) proposed.")
        if consistency.get("plausibility_violations"):
            warnings.append("Physiologically impossible value(s): "
                            + ", ".join(consistency["plausibility_violations"]) + " - verify before analysis.")
        errors = [] if results else ["No features could be mapped from the report."]
        try:
            preanalytical = detect_preanalytical(raw_text)
        except Exception as exc:  # never let provenance parsing break extraction
            preanalytical = {"flags": {}, "evidence": {}, "specimen": None, "collected_at": None, "morphology": [], "error": str(exc)}
        for _kind in ("hemolysis", "lipemia", "icterus", "clotted", "recollect"):
            if preanalytical["flags"].get(_kind):
                warnings.append(f"Specimen flag detected in report: {_kind} ({preanalytical['evidence'].get(_kind, '')[:60]}). "
                                f"Affected analytes will be down-weighted by the engine; confirm the flag in the review screen.")
        if preanalytical.get("morphology"):
            warnings.append("Smear morphology comment detected: " + ", ".join(preanalytical["morphology"][:6]) + ". Not yet used by the engine (planned input).")
        return {
            "extraction_success": bool(results),
            "preanalytical": preanalytical,
            'raw_text': self._privacy_hash(raw_text),
            "raw_text_preview": raw_text[:400],
            "language": doc_lang,
            'results': results,
            "confidence": round(confidence, 2),
            "consistency": consistency,
            "warnings": warnings,
            "errors": errors,
        }

    def _empty_natije(self, error: str, *, warnings: Optional[list[str]] = None) -> dict[str, Any]:
        return {"extraction_success": False, "raw_text": "", "raw_text_preview": '',
                "language": self.language, "results": [], 'confidence': 0.0,
                "warnings": warnings or [], "errors": [error]}

    @staticmethod
    def _try_tafsir_structured(text: str) -> Optional[list[dict[str, Any]]]:
        t = (text or "").strip()
        if t.startswith("```"):
            t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
            t = re.sub(r"\s*```$", '', t)
        # models sometimes wrap the array: {"results": [...]} / {"rows": [...]}
        first_obj, first_arr = t.find("{"), t.find("[")
        if first_obj != -1 and (first_arr == -1 or first_obj < first_arr):
            try:
                obj = json.loads(_repair_json_text(t[first_obj:t.rfind("}") + 1]))
            except Exception:
                obj = None
            if isinstance(obj, Mapping):
                for v in obj.values():
                    if isinstance(v, list) and v and all(isinstance(x, Mapping) for x in v):
                        t = json.dumps(v, ensure_ascii=False)
                        break
        start = t.find("[")
        if start == -1:
            return None
        sub = t[start:].strip()
        data = None
        end = sub.rfind("]")
        for candidate in ([sub[:end + 1]] if end != -1 else []):
            for attempt in (candidate, _repair_json_text(candidate)):
                try:
                    data = json.loads(attempt)
                    break
                except Exception:
                    data = None
            if data is not None:
                break
        # Auto-salvage truncated JSON array (cut mid-row: drop the partial row)
        if data is None:
            last_brace = sub.rfind("}")
            if last_brace != -1:
                for attempt in (sub[:last_brace + 1] + "]", _repair_json_text(sub[:last_brace + 1]) + "]"):
                    try:
                        data = json.loads(attempt)
                        break
                    except Exception:
                        data = None
        if not isinstance(data, list) or not data:
            return None
        rows = [_normalize_structured_row(x) for x in data if isinstance(x, Mapping)]
        rows = [x for x in rows if x and (x.get("test_name") or x.get("name"))]
        return rows or None

    def _canon_tedad(self, unit, value, low, high):
        u = _dim_norm(unit or "")
        entry = self._support.count_canon.get(u)
        if not entry:
            # the table mixes "µl" and "ul" spellings; look both ways
            alt = u.replace("µ", "u") if "µ" in u else u.replace("u", "µ")
            entry = self._support.count_canon.get(alt)
        if not entry:
            entry = _parse_count_unit(unit or "")
        if not entry:


            for pattern, canon, factor in self._support.count_fallbacks:
                if re.fullmatch(pattern, u):
                    entry = (canon, factor)
                    break
        if not entry:
            return unit, value, low, high
        canon, factor = entry


        if factor < 1.0 and value is not None and low is not None and high is not None \
                and value >= 1.0 and value < low and low * 0.6 <= value * 1000.0 <= high * 1.2:
            value = value * 1000.0


        if factor == 1.0 and value is not None and low is not None and high is not None \
                and 0 < value < low / 2.0:
            for _div in (10.0, 100.0):
                lo2, hi2 = low / _div, high / _div
                if lo2 <= value <= hi2:
                    low, high = lo2, hi2
                    break
        def sc(x):
            return None if x is None else round(x * factor, 4)
        return canon, sc(value), sc(low), sc(high)

    def _fix_glyph_vahed(self, feature_id: str, unit: Optional[str]) -> Optional[str]:
        if not unit or self.registry is None:
            return unit
        meta = self.registry.get(feature_id) or {}
        accepted = (meta.get('units') or {}).get('accepted') or []
        if not accepted:
            return unit
        key = _dim_norm(str(unit)).replace(" ", "")
        accepted_keys = {_dim_norm(str(u)).replace(" ", "") for u in accepted}
        if key in accepted_keys:
            return unit
        fixed = key.replace("pmol", 'µmol')
        if fixed in accepted_keys:
            return str(unit).replace('pmol', "µmol", 1)
        return unit

    def _negasht_structured_satrha(self, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for idx, row in enumerate(rows):
            name = str(row.get("test_name") or row.get("name") or "").strip()
            if not name or len(name) < 2:
                continue
            first_word = name.split()[0]
            name_clean = name.strip().lower()
            is_coag_test = name_clean in ("pt", "inr", "ptt", "aptt")
            if not is_coag_test and (_HEADER_LINE_RE.match(name) or _METADATA_RE.match(first_word)):
                continue
                continue
            if _DIGITS_ONLY_RE.match(name):
                continue
            parsed = ParsedLine(raw=f"{name} | {row.get('value')}")
            parsed.name = self.normalizer.for_nam(name)
            value = row.get('value')
            unit_in = str(row.get("unit") or "").strip() or None
            num, unit_in, qualifier, rest = _parse_value_cell(value, unit_in)
            if num is not None:
                parsed.value = num
            else:
                v = (rest or (str(value).strip() if value is not None else "")).strip()
                if v and self.parser._looks_qualitative(v):
                    parsed.qualitative = self.parser._qualitative_word(v)
                    parsed.value = parsed.qualitative
                else:
                    parsed.value = v or None
            parsed.unit = unit_in
            parsed.flag = self._yeksansazi_flag(row.get("flag"))
            low = self.parser._to_number(str(row.get("reference_range") or "").split("-")[0]) \
                if isinstance(row.get("reference_range"), str) and '-' in str(row.get("reference_range")) else None
            m = _RANGE_RE.search(str(row.get("reference_range") or ''))
            if m:
                parsed.report_range_low = self.parser._to_number(m.group(1))
                parsed.report_range_high = self.parser._to_number(m.group(2))
            agreement = row.get("_agreement")
            engine_conf = {"agree": 0.97, "single": 0.80, "disagree": 0.50}.get(agreement, 0.92)
            res = self._finalize(parsed, idx, engine_conf=engine_conf, auto_threshold=0.90)
            if agreement == "agree":
                _ocr_conf.add_evidence(res, "vision_agree")
            if agreement == "disagree":
                alts = row.get("_alternatives") or []
                _ocr_conf.add_evidence(res, "vision_disagree")
                res["requires_confirmation"] = True
                if res.get("suggested_action") == "accept":
                    res["suggested_action"] = "review"
                res.setdefault("warnings", []).append(
                    "Vision passes disagreed on this row: "
                    + "; ".join(f"{a.get('value')} {a.get('unit') or ''} {a.get('flag') or ''}".strip() for a in alts)
                    + " - confirm against the original image.")
                res["vision_alternatives"] = alts
            if agreement:
                res["vision_agreement"] = agreement
            if row.get("_column_shift"):
                _ocr_conf.add_evidence(res, "column_shift_corrected")
                res.setdefault("warnings", []).append(
                    f"Columns were swapped by the vision model ({row['_column_shift']}) and corrected; confirm.")
                res["requires_confirmation"] = True
                if res.get("suggested_action") == "accept":
                    res["suggested_action"] = "review"
            if isinstance(res.get("value"), (int, float)) and isinstance(res.get("original_value"), (int, float)):
                lo0, hi0 = parsed.report_range_low, parsed.report_range_high
                fix = _scale_mismatch_against_reference(float(res["original_value"]), lo0, hi0) \
                    if (lo0 is not None and hi0 is not None and res.get("unit") == res.get("original_unit")) else None
                if fix is not None and res.get("suggested_value") is None:
                    res["suggested_value"] = round(fix, 4)
                    res["repair_reason"] = "value is a power of ten away from the row's own printed interval"
                    res["requires_confirmation"] = True
                    if res.get("suggested_action") == "accept":
                        res["suggested_action"] = "review"
                    _ocr_conf.add_evidence(res, "scale_mismatch_vs_reference")
                    res.setdefault("warnings", []).append(
                        f"{res['original_value']:g} lies outside the printed interval {lo0:g}-{hi0:g} by a power of ten; "
                        f"{fix:g} would fit - probable decimal-point misread, confirm against the image.")
            if qualifier and num is not None:
                # censored result ("<0.5"): keep the numeric bound for the
                # engine, record the comparator, never auto-accept silently
                res["value_qualifier"] = qualifier
                _ocr_conf.add_evidence(res, "censored_value")
                res.setdefault("warnings", []).append(
                    f"Reported as '{qualifier} {num:g}' (beyond the assay's reporting limit); "
                    f"the number is a bound, not a measurement.")
            out.append(res)
        self._dedupe_results(out)
        return out

    def _tafsir_and_negasht(self, lines: Sequence[str], panel_hint: Optional[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for idx, line in enumerate(lines):
            if _looks_like_junk(line):
                continue
            if _looks_like_threshold_yaddasht(line) and not _looks_like_satr(line):
                continue
            for parsed in self.parser.tafsir_all(line, self.normalizer):
                if parsed.value is None and parsed.qualitative is None:
                    if not parsed.flag:
                        continue
                    if len((parsed.name or "").strip()) < 2:
                        continue
                name = parsed.name
                if not name:
                    continue
                if _DIGITS_ONLY_RE.match(name):
                    continue
                name_clean = (name or "").strip().lower()
                is_coag_test = name_clean in ("pt", "inr", "ptt", "aptt") and (parsed.value is not None or parsed.unit is not None)
                if not is_coag_test and (_HEADER_LINE_RE.match(name) or "test result unit" in name or _METADATA_RE.search(name)):
                    continue
                    continue
                ll = line.lower()
                if 'test result unit' in ll or "result unit reference" in ll \
                        or ("result" in ll and "reference range" in ll):
                    continue
                res = self._finalize(parsed, idx, engine_conf=0.85, auto_threshold=self.min_auto_accept)


                if res.get("feature_id") is None \
                        and res.get("suggested_action") == "edit_or_reject" \
                        and not self._has_natije_signal(parsed):
                    continue


                if res.get('feature_id') is None \
                        and res.get("suggested_action") == "edit_or_reject" \
                        and _looks_like_threshold_yaddasht(line):
                    continue
                out.append(res)
        self._dedupe_results(out)
        return out

    @staticmethod
    def _has_natije_signal(parsed: ParsedLine) -> bool:
        if parsed.unit:
            return True
        if parsed.report_range_low is not None or parsed.report_range_high is not None:
            return True
        if parsed.qualitative is not None:
            return True
        if parsed.flag in ("H", "L", "CRIT"):
            return True
        if re.search(r"[<≤>≥]", parsed.raw or ''):
            return True
        return False

    def _finalize(self, parsed: ParsedLine, idx: int, *,
                  engine_conf: float, auto_threshold: float) -> dict[str, Any]:
        orig_value, orig_unit = parsed.value, parsed.unit
        if isinstance(parsed.value, (int, float)) and parsed.unit:
            parsed.unit, parsed.value, parsed.report_range_low, parsed.report_range_high = \
                self._canon_tedad(parsed.unit, parsed.value,
                                  parsed.report_range_low, parsed.report_range_high)
        if self.registry is None:
            return self._candidate(None, parsed, idx, engine=0.5, name_score=0.0, manual=True,
                                   warnings="Feature registry not loaded.",
                                   orig_value=orig_value, orig_unit=orig_unit)


        if parsed.qualitative is not None:
            qfid = self._support.qualitative_name_map.get((parsed.name or "").strip().casefold())
            if qfid and qfid in self.registry.features:
                target = self.registry.features[qfid]
                if ((target.get("measurement") or {}).get('value_type') or "quantitative") != "quantitative":
                    return self._candidate(qfid, parsed, idx, engine=engine_conf, name_score=0.99,
                                           manual=False, unit_ok=True, ambiguous=False, warnings="",
                                           orig_value=orig_value, orig_unit=orig_unit)
        candidates = self.registry.index.candidates(parsed.name or "", unit=parsed.unit)
        if not candidates:
            return self._candidate(None, parsed, idx, engine=0.7, name_score=0.0, manual=True,
                                   warnings=f"Could not map '{parsed.raw}'. Match manually.",
                                   orig_value=orig_value, orig_unit=orig_unit)
        amb = len(candidates) > 1
        best_fid, best_score = candidates[0]


        if isinstance(parsed.value, (int, float)) and orig_unit:
            u = (orig_unit or '').strip().lower()
            if re.fullmatch(r"10\d{1,3}/[^\s]{0,6}", u) or re.fullmatch(r"10/\d{2,3}", u):
                sugg = self.registry.suggested_vahed(best_fid)
                if sugg and self._support.dimension_of(sugg) == "cell_count":
                    parsed.unit = sugg


        if isinstance(parsed.value, (int, float)) and parsed.unit:
            canon = self._support.vahed_canonical(parsed.unit)
            if canon:
                parsed.unit = canon


        if isinstance(parsed.value, (int, float)) and parsed.unit:
            parsed.unit = self._fix_glyph_vahed(best_fid, parsed.unit)


        if best_fid == "hematocrit" and isinstance(parsed.value, (int, float)) \
                and parsed.value <= 1 \
                and (parsed.report_range_high is None or parsed.report_range_high <= 1):
            parsed.unit = "L/L"


        if isinstance(parsed.value, (int, float)) and not parsed.unit and best_score >= 0.9:
            sugg = self.registry.suggested_vahed(best_fid)
            if sugg:
                canon = self._support.vahed_canonical(sugg) or sugg
                if canon:
                    parsed.unit = canon
        unit_ok = self._vahed_consistent(best_fid, parsed.unit)
        numeric_ok = (parsed.value is None or isinstance(parsed.value, (int, float))
                      or parsed.qualitative is not None
                      or self.registry.value_type(best_fid) != "quantitative")
        score = self._composite(best_score, engine_conf, unit_ok, parsed.value is not None, not amb)
        manual = (score < auto_threshold or amb or not unit_ok
                  or not numeric_ok or parsed.value is None)
        return self._candidate(best_fid, parsed, idx, engine=engine_conf, name_score=best_score,
                               manual=manual, unit_ok=unit_ok, ambiguous=amb,
                               warnings="Ambiguous alias; confirm the intended feature." if amb else "",
                               alternatives=[x[0] for x in candidates],
                               orig_value=orig_value, orig_unit=orig_unit)

    @staticmethod
    def _yeksansazi_flag(flag: Any) -> Optional[str]:
        if flag is None:
            return None
        t = str(flag).strip()
        if not t:
            return None
        k = t.casefold().rstrip(".")
        table = {"h": 'H', "high": "H", "hh": "CRIT", "l": "L", "low": "L", "ll": "CRIT",
                 "crit": 'CRIT', "critical": "CRIT", "a": "A", "abn": "A", "abnormal": 'A',
                 "n": "N", "normal": "N", "b": "B", "borderline": 'B', 'equivocal': 'B',
                 "بالا": 'H', "پایین": "L", "طبیعی": "N"}
        return table.get(k)

    def _candidate(self, feature_id, parsed: ParsedLine, index: int, *, engine: float,
                   name_score: float, manual: bool, warnings: str = "", unit_ok: bool = True,
                   ambiguous: bool = False, alternatives: Sequence[str] = (),
                   orig_value: Any = None, orig_unit: Optional[str] = None) -> dict[str, Any]:
        display = self.registry.display_name(feature_id) if (feature_id and self.registry) \
            else (parsed.name or parsed.raw)
        evidence = _ocr_conf.base_evidence(name_score, engine, unit_ok,
                                           parsed.value is not None, not ambiguous)
        conf = round(_ocr_conf.combine(evidence), 2)
        auto_accepted = (not manual and unit_ok and not ambiguous
                         and parsed.value is not None
                         and self._composite(name_score, engine, unit_ok, True,
                                             not ambiguous) >= self.min_auto_accept)
        record = {
            'index': index, "feature_id": feature_id, "display_name": display,
            "value": parsed.value, "qualitative": parsed.qualitative, "unit": parsed.unit,
            "flag": parsed.flag, "report_range_low": parsed.report_range_low,
            "report_range_high": parsed.report_range_high,
            "confidence": conf,
            "requires_confirmation": not auto_accepted,
            "suggested_action": ("accept" if auto_accepted
                                 else ("review" if (name_score >= 0.70 and parsed.value is not None)
                                       else "edit_or_reject")),
            "unit_ok": unit_ok,
            "alternatives": list(alternatives), 'ambiguous': ambiguous,
            "reported_reference": {"low": parsed.report_range_low, "high": parsed.report_range_high}
            if (parsed.report_range_low is not None or parsed.report_range_high is not None) else None,
            "warnings": [w for w in [warnings] if w],
            "raw_line": parsed.raw, "line_number": index, "raw_name": parsed.name,
            "original_value": orig_value if orig_value is not None else parsed.value,
            "original_unit": orig_unit or parsed.unit,
            "confidence_evidence": evidence,
        }
        identity = {k: record[k] for k in ("feature_id", "value", "unit", "flag", "raw_line")}
        record["result_id"] = 'ocr_' + hashlib.sha256(
            json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest()[:20]
        return record

    def _composite(self, name_score: float, engine: float, unit_ok: bool,
                   value_ok: bool, unambiguous: bool) -> float:
        """Row confidence = posterior P(row correct) from the additive
        log-likelihood evidence model in `ocr_confidence` (see that module
        for the term table). `_CONF_WEIGHTS` is kept only for tooling that
        introspects the legacy blend."""
        return _ocr_conf.composite(name_score, engine, unit_ok, value_ok, unambiguous)

    def _vahed_consistent(self, feature_id: Optional[str], unit: Optional[str]) -> bool:
        if feature_id is None or not unit:
            return True
        suggested = self.registry.suggested_vahed(feature_id) if self.registry else None
        if not suggested:
            return True
        observed = self._support.vahed_canonical(unit) or str(unit).strip()
        expected = self._support.vahed_canonical(suggested) or str(suggested).strip()
        if observed == expected:
            return True


        if self.registry is not None:
            allowed: set[str] = set()
            meta = self.registry.get(feature_id) or {}
            for u in (meta.get("measurement") or {}).get("allowed_units") or []:
                c = self._support.vahed_canonical(str(u)) or str(u).strip()
                if c:
                    allowed.add(c)
            if allowed and observed in allowed:
                return True
        obs_dim = self._support.dimension_of(observed)
        exp_dim = self._support.dimension_of(expected)

        if feature_id == "mean_corpuscular_hemoglobin_concentration" \
                and observed in ("%", "percent", 'pct'):
            return True
        if obs_dim and exp_dim and obs_dim == exp_dim:
            return True
        try:
            convert_unit(1.0, observed, expected, feature_id)
            return True
        except CalculationError:
            return False

    def _dedupe_results(self, results: list[dict[str, Any]]) -> None:
        seen: dict[str, int] = {}
        drop: list[int] = []
        for i, r in enumerate(results):
            fid = r.get("feature_id")
            if fid is None:
                continue
            if fid not in seen:
                seen[fid] = i
                continue
            other = results[seen[fid]]
            same_value = (str(r.get("value")) == str(other.get("value"))
                          and (r.get("unit") or "") == (other.get("unit") or ""))
            if same_value:
                if (r.get("confidence") or 0) > (other.get("confidence") or 0):
                    drop.append(seen[fid]); seen[fid] = i
                else:
                    drop.append(i)
                continue

            def quality(x):
                base = 0 if x.get("suggested_action") == "edit_or_reject" else 1
                v = x.get("value")
                ref = x.get('reported_reference') or {}
                lo, hi = ref.get("low"), ref.get('high')
                in_range = 0
                if isinstance(v, (int, float)) and (lo is not None or hi is not None):
                    if (lo is None or v >= lo) and (hi is None or v <= hi):
                        in_range = 1
                has_unit = 1 if (x.get("unit") and x.get("unit_ok", True)) else 0
                return (base, in_range, has_unit, float(x.get("confidence") or 0.0))
            if quality(other) >= quality(r):
                kept_idx, lost_idx = seen[fid], i
            else:
                kept_idx, lost_idx = i, seen[fid]
            kept, lost = results[kept_idx], results[lost_idx]

            if lost.get("unit_ok", True):
                drop.append(lost_idx)
                kept["warnings"] = list(kept.get("warnings") or [])
                kept["warnings"].append(
                    "Duplicate conflicting row removed automatically; this row was kept.")
            else:
                kept["warnings"] = list(kept.get('warnings') or [])
                kept["warnings"].append(
                    "Another row mapped to this feature with a unit/alias mismatch; review it.")
            seen[fid] = kept_idx
        for i in sorted(set(drop), reverse=True):
            results.pop(i)

    @staticmethod
    def _privacy_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = [
    "BloodLabPipeline", "FeatureRegistry", "FeatureIndex", "TextNormalizer",
    "ReportLineParser", "ParsedLine", "OCRSupport",
    "ExtractionBackend", "TesseractBackend", "VisionBackend", 'RawTextBackend',
    'PassthroughBackend', "PaddleBackend",
    "normalize_extracted_text", "normalize_report_units", "normalize_zwnj",
]
