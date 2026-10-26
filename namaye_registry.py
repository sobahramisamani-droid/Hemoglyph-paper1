from __future__ import annotations
import logging
import threading
import time
from collections import OrderedDict
from functools import lru_cache, wraps
from typing import Any, Dict, Generator, Iterable, List, Mapping, Optional, Tuple, Callable

__all__ = [
    "s", 'fmt', "expression_text", "population_text", "rule_type_label",
    'status_label', "feature_rows", "guideline_rows", "disease_rows", "disease_detail",
    "reference_rows", "registry_summary", "global_search", "clear_cache",
    'get_cache_stats', "invalidate_cache", "warm_indexes"
]


_DEFAULT_LIMIT = 200
_CACHE_SIZE = 1024
_CACHE_TTL = 300
_MAX_EXPRESSION_DEPTH = 15


logger = logging.getLogger(__name__)


class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self._lock = threading.Lock()

    def record_hit(self):
        with self._lock:
            self.hits += 1

    def record_miss(self):
        with self._lock:
            self.misses += 1

    def record_eviction(self):
        with self._lock:
            self.evictions += 1

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'hits': self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": f"{self.hit_rate:.2f}%"
            }

metrics = CacheMetrics()


class TtlCache:

    def __init__(self, max_size: int = _CACHE_SIZE, ttl: int = _CACHE_TTL):
        self._cache: "OrderedDict[str, Tuple[Any, float]]" = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is not None:
                value, timestamp = entry
                if time.time() - timestamp < self._ttl:
                    self._cache.move_to_end(key)
                    metrics.record_hit()
                    return value
                del self._cache[key]
                metrics.record_eviction()
            metrics.record_miss()
            return None

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, time.time())
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
                metrics.record_eviction()

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def invalidate(self, pattern: str) -> int:
        with self._lock:
            keys_to_remove = [k for k in self._cache if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)


_cache = TtlCache()


def fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)

def s(v: Any, fallback: str = "") -> str:
    if v is None:
        return fallback
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, (list, tuple)):
        return ", ".join(s(x) for x in v if x not in (None, ""))
    if isinstance(v, dict):
        return ", ".join(s(x) for x in v.values() if x not in (None, ""))
    return str(v)

def status_label(status: str) -> str:
    labels = {
        "urgent_pattern": 'Urgent pattern',
        "criterion_met": 'Criterion met',
        "compatible_pattern": "Compatible pattern",
        'possible_pattern': "Possible pattern",
        "screening_positive": "Screening positive",
        "conflicting_data": "Conflicting data",
        'insufficient_data': "Insufficient data",
        "criterion_not_met": "Not met",
        "not_applicable": "Not applicable",
    }
    return labels.get(s(status), s(status))

def rule_type_label(rule_type: Any) -> str:
    labels = {
        "diagnostic_criterion": "Diagnostic criterion",
        "classification_or_staging": "Classification / staging",
        "compatible_laboratory_pattern": 'Compatible pattern',
        "screening_or_triage": "Screening / triage",
        "urgent_pattern": 'Urgent pattern',
    }
    return labels.get(s(rule_type), s(rule_type))


def expression_text(expr: Any, depth: int = 0) -> str:
    if not isinstance(expr, Mapping):
        return ""

    if depth > _MAX_EXPRESSION_DEPTH:
        return "…"

    try:
        if isinstance(expr.get("all"), list):
            parts = [expression_text(c, depth + 1) for c in expr["all"]]
            return " AND ".join(p for p in parts if p)

        if isinstance(expr.get("any"), list):
            parts = [expression_text(c, depth + 1) for c in expr["any"]]
            return " OR ".join(p for p in parts if p)

        fid = s(expr.get("feature_id"))
        if fid:
            op = s(expr.get("operator"), '?')
            val = fmt(expr.get("value"))
            unit = s(expr.get("unit"))
            text = f"{fid} {op} {val}".strip()

            if unit:
                text += f" {unit}"

            ctx = expr.get("context") or {}
            if isinstance(ctx, Mapping) and ctx:
                ctx_parts = [f"{k}={s(v)}" for k, v in ctx.items() if v is not None]
                if ctx_parts:
                    text += " [" + ", ".join(ctx_parts[:3]) + "]"
                    if len(ctx) > 3:
                        text += f" +{len(ctx) - 3}"

            return text

        return s(expr.get('context'))
    except Exception as e:
        logger.warning(f"Error rendering expression: {e}")
        return 'Error'

def population_text(rule: Optional[Mapping[str, Any]]) -> str:
    try:
        pop = (rule or {}).get("population") or {}
        ages = s(pop.get("age_groups"), "all ages")
        sex = s(pop.get("sex"), "all")
        pregnancy = s(pop.get("pregnancy"))

        text = f"{ages} · {sex}"
        if pregnancy and pregnancy not in {"any", "all", ""}:
            text += f" · pregnancy: {pregnancy}"
        return text
    except Exception as e:
        logger.warning(f"Error generating population text: {e}")
        return "Population not specified"

def _ghaede_vizhegi_ids(expr: Any) -> Generator[str, None, None]:
    if isinstance(expr, Mapping):
        if expr.get("feature_id"):
            yield s(expr.get("feature_id"))
        for key in ('all', "any", "not"):
            if key in expr:
                yield from _ghaede_vizhegi_ids(expr[key])
    elif isinstance(expr, list):
        for item in expr:
            yield from _ghaede_vizhegi_ids(item)


def _bimari_description(
    disease: Mapping[str, Any],
    identity: Mapping[str, Any],
    classification: Mapping[str, Any],
    links: Mapping[str, Any],
) -> str:
    try:

        for key in ['description', "summary", "definition",
                   "clinical_summary", "clinical_description"]:
            desc = identity.get(key) or disease.get(key)
            if desc:
                return s(desc)


        for section in ["education", "patient_information", "safety"]:
            sec_data = disease.get(section)
            if isinstance(sec_data, Mapping):
                for key in ["description", "summary", "patient_summary"]:
                    desc = sec_data.get(key)
                    if desc:
                        return s(desc)


        parts: List[str] = []

        domains = s(classification.get("domains"))
        if domains:
            parts.append(f"A laboratory-defined clinical concept in the domain(s) {domains}.")

        required = s(links.get("required"))
        if required:
            parts.append(f"Key laboratory inputs: {required}.")

        optional = s(links.get("optional"))
        if optional:
            parts.append(f"Supporting (optional) inputs: {optional}.")

        parts.append(
            "Its interpretation is derived only from the candidate rules and "
            'guideline sources listed in this registry.'
        )

        return " ".join(parts)
    except Exception as e:
        logger.warning(f"Error generating disease description: {e}")
        return "Description not available"


class FeatureIndex:
    def __init__(self):
        self._index: Dict[str, List[Tuple[str, float]]] = {}
        self._built = False
        self._lock = threading.RLock()
        self._build_time = 0

    def build(self, features: Mapping[str, Any]) -> None:
        with self._lock:
            if self._built:
                return

            start_time = time.time()
            idx: Dict[str, List[Tuple[str, float]]] = {}
            term_buckets = ("synonyms", "abbreviations", "ocr_variants",
                          "common_report_names")

            for fid, meta in features.items():
                ident = meta.get('identity') or {}
                name = s(ident.get("display_name") or ident.get("canonical_name")
                        or ident.get("name_en") or ident.get("name_fa") or fid)


                for word in name.lower().split():
                    if len(word) >= 2:
                        idx.setdefault(word, []).append((fid, 1.0))


                for word in fid.lower().split("_"):
                    if len(word) >= 2:
                        idx.setdefault(word, []).append((fid, 0.8))


                term = meta.get("terminology") or {}
                for bucket in term_buckets:
                    vals = term.get(bucket) or []
                    if isinstance(vals, list):
                        for v in vals:
                            for word in s(v).lower().split():
                                if len(word) >= 2:
                                    idx.setdefault(word, []).append((fid, 0.6))

            self._index = idx
            self._built = True
            self._build_time = time.time() - start_time
            logger.info(f"Feature index built in {self._build_time:.3f}s with {len(idx)} terms")

    def search(self, query: str, limit: int = 100) -> List[str]:
        if not self._built:
            return []

        q = query.strip().lower()
        words = q.split()

        if not words:
            return []


        scores: Dict[str, float] = {}
        for word in words:
            for indexed_word, entries in self._index.items():
                if indexed_word == word or indexed_word.startswith(word):
                    for fid, weight in entries:
                        scores[fid] = scores.get(fid, 0.0) + weight


        return sorted(scores.keys(), key=lambda f: -scores[f])[:limit]

_feature_index = FeatureIndex()


class GhaedeIndex:

    def __init__(self):
        self._tokens: Dict[str, List[str]] = {}
        self._built = False
        self._lock = threading.RLock()

    def build(self, disease_payload: Mapping[str, Any]) -> None:
        with self._lock:
            if self._built:
                return
            start = time.time()
            rules = disease_payload.get('rules') or {}
            diseases = disease_payload.get("diseases") or {}
            tokens: Dict[str, List[str]] = {}

            for rule_id, rule in rules.items():
                disease_id = str(rule.get("disease_id") or "")
                identity = (diseases.get(disease_id) or {}).get("identity") or {}
                bag = {rule_id.lower(), disease_id.lower()}
                bag.update(str(identity.get("name_en") or "").lower().split())
                bag.update(str(rule.get("rule_type") or "").lower().split("_"))
                for src in rule.get("source_ids") or ():
                    bag.add(str(src).lower())
                for fid in _ghaede_vizhegi_ids(rule.get("expression") or {}):
                    low = fid.lower()
                    bag.add(low)
                    bag.update(low.split("_"))
                for part in list(bag):
                    bag.update(part.split('_'))
                for tok in bag:
                    if len(tok) >= 2:
                        tokens.setdefault(tok, []).append(rule_id)

            self._tokens = tokens
            self._built = True
            logger.info('Rule index built in %.3fs (%d tokens, %d rules)',
                        time.time() - start, len(tokens), len(rules))

    def search(self, query: str, limit: int = 800) -> List[str]:
        if not self._built:
            return []
        q = query.strip().lower()
        if not q:
            return []
        out: List[str] = []
        seen: set = set()
        exact = self._tokens.get(q)
        if exact:
            for rid in exact:
                if rid not in seen:
                    seen.add(rid)
                    out.append(rid)
        if len(out) < limit:
            for tok, postings in self._tokens.items():
                if q in tok and tok != q:
                    for rid in postings:
                        if rid not in seen:
                            seen.add(rid)
                            out.append(rid)
                            if len(out) >= limit:
                                return out
        return out[:limit]

    def clear(self) -> None:
        with self._lock:
            self._tokens = {}
            self._built = False


_rule_index = GhaedeIndex()


def feature_rows(features: Mapping[str, Any], query: str = "",
                category: str = "All", limit: int = _DEFAULT_LIMIT) -> List[Dict[str, str]]:
    cache_key = f"feat_{query}_{category}_{limit}"
    cached = _cache.get(cache_key)

    if cached is not None:
        return cached

    try:
        q = (query or "").strip().lower()
        cat_sel = (category or "").strip()


        if not _feature_index._built:
            _feature_index.build(features)


        if q:
            candidate_ids = _feature_index.search(q, limit * 2)
        else:
            candidate_ids = list(features.keys())[:limit * 2]

        rows: List[Dict[str, str]] = []
        seen: set = set()

        for fid in candidate_ids:
            if fid in seen:
                continue

            meta = features.get(fid)
            if not meta:
                continue

            ident = meta.get("identity") or {}
            cat = s(ident.get('category'))
            name = s(ident.get("display_name") or ident.get('canonical_name')
                    or ident.get("name_en") or ident.get("name_fa") or fid)

            if cat_sel and cat_sel != "All" and cat != cat_sel:
                continue

            seen.add(fid)
            rows.append({
                'featureId': s(fid),
                "featureName": name,
                "category": cat,
                "unit": s((meta.get("units") or {}).get("canonical")),
                "status": s(ident.get("status")),
            })

            if len(rows) >= limit:
                break

        _cache.put(cache_key, rows)
        return rows
    except Exception as e:
        logger.error(f"Error in feature_rows: {e}")
        return []

def reference_rows(disease_payload: Mapping[str, Any],
                  query: str = '') -> List[Dict[str, str]]:
    cache_key = f"ref_{query}"
    cached = _cache.get(cache_key)

    if cached is not None:
        return cached

    try:
        q = (query or "").strip().lower()
        sources = disease_payload.get("guideline_sources") or {}
        rows: List[Dict[str, str]] = []

        for sid, src in sources.items():
            org = s(src.get("organization"))
            title = s(src.get("title"))
            scope = s(src.get("scope"))

            if q and q not in title.lower() and q not in org.lower() and q not in scope.lower():
                continue

            rows.append({
                'sourceId': s(sid),
                'organization': org,
                "title": title,
                "year": s(src.get("year")),
                "url": s(src.get("url")),
                "scope": scope,
                "accessed": s(src.get("accessed_at")),
                "evidenceStatus": s(src.get('evidence_status')).replace("__", " · ").replace("_", " "),
            })

        _cache.put(cache_key, rows)
        return rows
    except Exception as e:
        logger.error(f"Error in reference_rows: {e}")
        return []

def guideline_rows(disease_payload: Mapping[str, Any],
                   query: str = "", limit: int = 200) -> List[Dict[str, Any]]:


    if not disease_payload or not disease_payload.get("rules"):
        return []

    cache_key = f"guide_{query}_{limit}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        q = (query or "").strip().lower()
        diseases = disease_payload.get("diseases") or {}
        sources = disease_payload.get("guideline_sources") or {}
        rules = disease_payload.get("rules") or {}

        if q:
            _rule_index.build(disease_payload)
            candidate_ids: Iterable[str] = _rule_index.search(q, limit * 4)
        else:
            candidate_ids = rules.keys()

        rows: List[Dict[str, Any]] = []
        for rule_id in candidate_ids:
            rule = rules.get(rule_id)
            if not rule:
                continue
            disease_id = s(rule.get("disease_id"))
            disease = diseases.get(disease_id) or {}
            identity = disease.get("identity") or {}
            name = s(identity.get("name_en") or disease_id)
            domains = s((disease.get("classification") or {}).get("domains"))
            source_ids = [s(x) for x in (rule.get('source_ids') or [])]
            primary = sources.get(source_ids[0]) if source_ids else None
            expression = expression_text(rule.get("expression") or {})
            feature_ids = sorted(set(_ghaede_vizhegi_ids(rule.get("expression") or {})))

            if q:

                haystack = " ".join([disease_id, name, s(rule_id), expression, domains,
                                     " ".join(source_ids), " ".join(feature_ids)]).lower()
                if q not in haystack:
                    continue

            rows.append({
                "diseaseId": disease_id,
                'diseaseName': name,
                "ruleId": s(rule_id),
                "ruleType": s(rule.get("rule_type")),
                "ruleTypeLabel": rule_type_label(rule.get("rule_type")),
                "expression": expression,
                "featureIds": ", ".join(feature_ids),
                "population": population_text(rule),
                'sourceId': s(source_ids[0] if source_ids else ""),
                "sourceIds": ", ".join(source_ids),
                "organization": s((primary or {}).get("organization")),
                'year': s((primary or {}).get("year")),
                "url": s((primary or {}).get('url')),
                "executable": bool(rule.get('executable')),
                "executableLabel": "Executable candidate" if rule.get("executable")
                                 else 'Candidate — specialist validation required',
                "domains": domains,
            })

            if len(rows) >= limit:
                break

        _cache.put(cache_key, rows)
        return rows
    except Exception as e:
        logger.error(f"Error in guideline_rows: {e}")
        return []

def disease_rows(disease_payload: Mapping[str, Any],
                 query: str = "", limit: int = 300) -> List[Dict[str, str]]:
    cache_key = f"dis_{query}_{limit}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        q = (query or "").strip().lower()
        diseases = disease_payload.get("diseases") or {}
        rows: List[Dict[str, str]] = []


        sorted_diseases = sorted(
            diseases.items(),
            key=lambda item: s((item[1].get("identity") or {}).get("name_en") or item[0]).lower()
        )

        for did, d in sorted_diseases:
            identity = d.get("identity") or {}
            name = s(identity.get("name_en") or did)
            name_fa = s(identity.get("name_fa") or "")
            domains = s((d.get("classification") or {}).get("domains"))
            wiki = s(identity.get("wikipedia_url") or "")
            rule_count = len(d.get("rule_ids") or [])

            if q:
                haystack = f"{did} {name} {name_fa} {domains}".lower()
                if q not in haystack:
                    continue

            rows.append({
                "diseaseId": s(did),
                "name": name,
                "name_fa": name_fa,
                "domains": domains,
                "wikipedia_url": wiki,
                "ruleCount": str(rule_count)
            })
            if len(rows) >= limit:
                break

        _cache.put(cache_key, rows)
        return rows
    except Exception as e:
        logger.error(f"Error in disease_rows: {e}")
        return []
def disease_detail(disease_payload: Mapping[str, Any],
                  disease_id: str) -> Dict[str, Any]:
    try:
        disease = (disease_payload.get("diseases") or {}).get(disease_id)

        if not disease:
            return {
                "found": False,
                "diseaseId": s(disease_id),
                "name": s(disease_id),
                "description": '',
            }

        identity = disease.get("identity") or {}
        classification = disease.get("classification") or {}
        coverage = disease.get("coverage") or {}
        safety = disease.get("safety") or {}
        links = disease.get("feature_links") or {}
        sources = disease_payload.get("guideline_sources") or {}
        rules = disease_payload.get("rules") or {}

        rule_rows = []
        for rid in disease.get("rule_ids") or []:
            rule = rules.get(rid) or {}
            rule_rows.append({
                "ruleId": s(rid),
                "ruleTypeLabel": rule_type_label(rule.get("rule_type")),
                'expression': expression_text(rule.get("expression") or {}),
                "population": population_text(rule),
                "status": s(rule.get("status")).replace('_', " "),
                "sourceIds": ", ".join(s(x) for x in (rule.get("source_ids") or [])),
            })

        source_rows = []
        for sid in disease.get("guideline_source_ids") or []:
            src = sources.get(sid) or {}
            source_rows.append({
                "sourceId": s(sid),
                "organization": s(src.get('organization')),
                "title": s(src.get("title")),
                "year": s(src.get("year")),
                "url": s(src.get("url")),
                "scope": s(src.get('scope')),
            })

        return {
            "found": True,
            "diseaseId": s(disease_id),
            "name": s(identity.get("name_en") or disease_id),
            "name_fa": s(identity.get("name_fa")),
            "description": _bimari_description(disease, identity, classification, links),
            "icd10": s(identity.get("icd10"), "—"),
            "domains": s(classification.get("domains"), '—'),
            'priority': s(classification.get("clinical_priority"), 'routine'),
            "ruleType": s(classification.get("rule_type")).replace("_", " "),
            "coverage": "Executable rule available" if coverage.get("executable_rule_available")
                       else s(coverage.get("status")).replace("_", " "),
            "coverageReason": s(coverage.get('reason')),
            "safety": s(safety.get("emergency_message")),
            "evidenceLevel": s(coverage.get("evidence_level")).replace("_", ' '),
            "requiredFeatures": s(links.get("required"), "—"),
            "optionalFeatures": s(links.get("optional"), "—"),
            "rules": rule_rows,
            "sources": source_rows,
            'wikipedia_url': s(identity.get("wikipedia_url") or "")
        }

    except Exception as e:
        logger.error(f"Error in disease_detail: {e}")
        return {
            "found": False,
            "diseaseId": s(disease_id),
            "name": "Error loading disease",
            'description': f"Error: {str(e)}"
        }
def _vaziat_label(status: str) -> str:
    labels = {
        'urgent_pattern': "Urgent pattern",
        "criterion_met": 'Criterion met',
        "compatible_pattern": "Compatible pattern",
        "possible_pattern": "Possible pattern",
        "screening_positive": "Screening positive",
        "conflicting_data": "Conflicting data",
        "insufficient_data": "Insufficient data",
        'criterion_not_met': "Not met",
        "not_applicable": "Not applicable",
        'ruled_out': "Ruled out",
        "excluded": "Excluded",
    }
    return labels.get(status, status)
def registry_summary(feature_payload: Mapping[str, Any],
                    disease_payload: Mapping[str, Any]) -> Dict[str, Any]:
    cache_key = "registry_summary"
    cached = _cache.get(cache_key)

    if cached is not None:
        return cached

    try:
        fm = feature_payload.get("registry_metadata") or {}
        dm = disease_payload.get("registry_metadata") or {}

        summary = {
            "featureCount": len(feature_payload.get("features") or {}),
            "diseaseCount": len(feature_payload.get("diseases") or {}) if "diseases" in feature_payload
                           else len(disease_payload.get("diseases") or {}),
            'ruleCount': len(disease_payload.get("rules") or {}),
            "sourceCount": len(disease_payload.get("guideline_sources") or {}),
            "featureRegistryVersion": s(fm.get("registry_version")),
            "diseaseRegistryVersion": s(dm.get("version")),
            "allowedResultStates": [s(x) for x in (dm.get("allowed_result_states") or [])],
            "clinicalRelease": bool(dm.get("clinical_release")),
            "intendedUse": s(dm.get('intended_use')),
        }

        _cache.put(cache_key, summary)
        return summary
    except Exception as e:
        logger.error(f"Error in registry_summary: {e}")
        return {}

def global_search(feature_payload: Mapping[str, Any],
                 disease_payload: Mapping[str, Any],
                 query: str,
                 limit: int = 20) -> List[Dict[str, str]]:
    cache_key = f"global_{query}_{limit}"
    cached = _cache.get(cache_key)

    if cached is not None:
        return cached

    try:
        q = (query or "").strip().lower()

        if not q:
            return []

        rows: List[Dict[str, str]] = []


        if not _feature_index._built:
            _feature_index.build(feature_payload.get("features") or {})

        feature_ids = _feature_index.search(q, limit)

        for fid in feature_ids:
            meta = (feature_payload.get("features") or {}).get(fid)
            if not meta:
                continue

            ident = meta.get("identity") or {}
            name = s(ident.get("display_name") or ident.get('canonical_name') or fid)

            rows.append({
                "title": name,
                "subtitle": s(ident.get("category")),
                "kind": "feature",
                'itemId': s(fid),
            })

            if len(rows) >= limit:
                break


        if len(rows) < limit:
            for did, d in (disease_payload.get("diseases") or {}).items():
                if len(rows) >= limit:
                    break

                ident = d.get("identity") or {}
                name = s(ident.get("name_en") or did)

                if q in name.lower() or q in did.lower():
                    rows.append({
                        'title': name,
                        "subtitle": 'Disease/concept',
                        "kind": 'disease',
                        "itemId": s(did),
                    })


        if len(rows) < limit:
            for sid, src in (disease_payload.get("guideline_sources") or {}).items():
                if len(rows) >= limit:
                    break

                title = s(src.get("title"))
                org = s(src.get("organization"))

                if q in title.lower() or q in org.lower():
                    rows.append({
                        "title": org + " — " + title,
                        'subtitle': "Guideline source",
                        "kind": 'source',
                        "itemId": s(sid),
                    })

        _cache.put(cache_key, rows[:limit])
        return rows[:limit]
    except Exception as e:
        logger.error(f"Error in global_search: {e}")
        return []

def warm_indexes(feature_payload: Mapping[str, Any],
                 disease_payload: Mapping[str, Any]) -> None:
    try:
        _feature_index.build(feature_payload.get("features") or {})
    except Exception:
        logger.exception("feature index warm-up failed")
    try:
        _rule_index.build(disease_payload)
    except Exception:
        logger.exception("rule index warm-up failed")


def clear_cache() -> None:
    _cache.clear()
    _rule_index.clear()
    logger.info("All caches cleared")

def invalidate_cache(pattern: str) -> int:
    count = _cache.invalidate(pattern)
    logger.info(f"Invalidated {count} cache entries matching '{pattern}'")
    return count

def get_cache_stats() -> Dict[str, Any]:
    return {
        "cache": metrics.get_stats(),
        "feature_index_built": _feature_index._built,
        'feature_index_terms': len(_feature_index._index) if _feature_index._built else 0,
    }
