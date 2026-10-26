"""Evidence model for per-row OCR confidence (Hemoglyph v1.3.1, Phase 8).

Why this exists
---------------
The previous composite was a linear blend (name .45 + engine .20 + unit .15
+ value .10 + context .10) that later stages scaled by ad-hoc factors
(x0.45 for an identity culprit, +0.03 for corroboration). That has three
defects: the number has no probabilistic meaning, evidence added later is
not commensurable with evidence added earlier, and nothing can be fitted
once labelled data exist.

Model
-----
`confidence = sigma( logit(PRIOR) + sum_i LLR_i )`

Every piece of evidence about a row - how well its label matched a
registry feature, how sure the extraction engine was, whether the unit is
consistent, whether the value is numeric, whether the alias is ambiguous,
whether the panel's own arithmetic corroborates or contradicts the value,
whether two vision passes agreed - contributes an additive log-likelihood
ratio. The combination is therefore:

* coherent   : the same evidence always moves the log-odds by the same amount,
               no matter where in the pipeline it is learned;
* monotone   : stronger support never lowers confidence (property-tested);
* explainable: `record["confidence_evidence"]` lists every term and its LLR;
* fittable   : `fit_llr_weights()` re-estimates the table from labelled rows
               by regularised logistic regression - the *shape* of the model
               is final, the numbers are priors until data arrive.

The LLR priors below are expert-set and documented term by term. They are
NOT calibrated against a labelled image set (none exists yet); they are
chosen so that the decision thresholds used by the pipeline keep their
intended meaning (perfect row ~0.99, any single hard defect < 0.86).
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Optional, Sequence

PRIOR = 0.85                      # a typical extracted row is right ~85 % of the time

# name-match similarity -> LLR, linear in similarity around NAME_PIVOT
NAME_SLOPE = 8.0
NAME_PIVOT = 0.88
# engine confidence -> LLR, shrunk logit around ENGINE_PIVOT (engines are over-confident)
ENGINE_SHRINK = 0.8
ENGINE_PIVOT = 0.75

# categorical evidence terms (log-likelihood ratios, natural log)
LLR: dict[str, float] = {
    "unit_consistent": +0.5,
    "unit_inconsistent": -2.5,
    "value_numeric": +0.2,
    "value_missing": -3.0,
    "alias_unambiguous": +0.3,
    "alias_ambiguous": -2.8,
    # panel arithmetic (ocr_consistency)
    "identity_corroborated": +1.0,        # per passing identity, capped by CORROBORATION_CAP
    "identity_culprit": -5.0,             # a digit-level repair of THIS value restores every identity
    "identity_unresolved": -2.5,          # took part in a failed identity nobody can explain
    "identity_exonerated": +0.4,          # failed identity explained by another value
    "implausible_value": -6.0,            # outside physiological limits
    "flag_mismatch": -1.5,                # printed H/L flag contradicts value vs printed interval
    "duplicate_conflict": -1.0,
    # multi-pass vision agreement
    "vision_agree": +0.7,
    "vision_disagree": -2.2,
    "censored_value": -0.3,               # "<0.5": the number is a bound
    "scale_mismatch_vs_reference": -3.0,  # value a power of ten outside the row's own printed interval
    "column_shift_corrected": -0.8,
}
CORROBORATION_CAP = 2.0


def _logit(p: float) -> float:
    p = min(1.0 - 1e-6, max(1e-6, p))
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def name_llr(similarity: float) -> float:
    return NAME_SLOPE * (max(0.0, min(1.0, float(similarity))) - NAME_PIVOT)


def engine_llr(engine_conf: float) -> float:
    return ENGINE_SHRINK * (_logit(float(engine_conf)) - _logit(ENGINE_PIVOT))


def base_evidence(name_score: float, engine: float, unit_ok: Optional[bool],
                  value_ok: bool, unambiguous: bool) -> list[dict[str, Any]]:
    """Evidence terms known at mapping time."""
    ev = [{"term": "name_match", "value": round(float(name_score), 3), "llr": name_llr(name_score)},
          {"term": "engine", "value": round(float(engine), 3), "llr": engine_llr(engine)}]
    if unit_ok is True:
        ev.append({"term": "unit_consistent", "llr": LLR["unit_consistent"]})
    elif unit_ok is False:
        ev.append({"term": "unit_inconsistent", "llr": LLR["unit_inconsistent"]})
    ev.append({"term": "value_numeric" if value_ok else "value_missing",
               "llr": LLR["value_numeric"] if value_ok else LLR["value_missing"]})
    ev.append({"term": "alias_unambiguous" if unambiguous else "alias_ambiguous",
               "llr": LLR["alias_unambiguous"] if unambiguous else LLR["alias_ambiguous"]})
    return ev


def combine(evidence: Iterable[Mapping[str, Any]]) -> float:
    """Posterior probability that the row is correct."""
    total = _logit(PRIOR)
    corroboration = 0.0
    for e in evidence:
        llr = float(e.get("llr", 0.0))
        if e.get("term") == "identity_corroborated":
            corroboration += llr
            continue
        total += llr
    total += min(CORROBORATION_CAP, corroboration)
    return _sigmoid(total)


def composite(name_score: float, engine: float, unit_ok: Optional[bool],
              value_ok: bool, unambiguous: bool) -> float:
    return combine(base_evidence(name_score, engine, unit_ok, value_ok, unambiguous))


def attach(record: dict[str, Any], evidence: Sequence[Mapping[str, Any]]) -> float:
    """Store the evidence list on the record and set its confidence."""
    record["confidence_evidence"] = [dict(e) for e in evidence]
    record["confidence"] = round(combine(record["confidence_evidence"]), 2)
    return record["confidence"]


def add_evidence(record: dict[str, Any], term: str, *, llr: Optional[float] = None,
                 note: Optional[str] = None, once: bool = True) -> float:
    """Append one evidence term (by name from LLR, or an explicit llr) and
    recompute the confidence. Records produced before this module existed
    (no `confidence_evidence`) are seeded from their current confidence so
    the update is still an additive log-odds move."""
    ev = record.setdefault("confidence_evidence", None)
    if ev is None:
        ev = record["confidence_evidence"] = [
            {"term": "legacy_confidence", "value": record.get("confidence"),
             "llr": _logit(float(record.get("confidence", PRIOR) or PRIOR)) - _logit(PRIOR)}]
    if once and any(e.get("term") == term and e.get("note") == note for e in ev):
        return float(record.get("confidence", 0.0))
    item = {"term": term, "llr": float(LLR[term] if llr is None else llr)}
    if note:
        item["note"] = note
    ev.append(item)
    record["confidence"] = round(combine(ev), 2)
    return record["confidence"]


def explain(record: Mapping[str, Any]) -> str:
    """Human-readable breakdown of a row's confidence."""
    ev = record.get("confidence_evidence") or []
    parts = [f"prior {PRIOR:.2f}"]
    for e in ev:
        v = f"={e['value']}" if "value" in e and e["value"] is not None else ""
        parts.append(f"{e['term']}{v}: {e['llr']:+.2f}")
    return "; ".join(parts) + f" -> {record.get('confidence')}"


# --------------------------------------------------------------------------- #
# Calibration hook: fit the LLR table from labelled rows.
# --------------------------------------------------------------------------- #
def _features(evidence: Sequence[Mapping[str, Any]], terms: Sequence[str]) -> list[float]:
    x = [0.0] * len(terms)
    idx = {t: i for i, t in enumerate(terms)}
    for e in evidence:
        t = e.get("term")
        if t == "name_match":
            x[idx["name_match"]] = float(e.get("value", NAME_PIVOT)) - NAME_PIVOT
        elif t == "engine":
            x[idx["engine"]] = _logit(float(e.get("value", ENGINE_PIVOT))) - _logit(ENGINE_PIVOT)
        elif t in idx:
            x[idx[t]] += 1.0
    return x


def fit_llr_weights(rows: Sequence[Mapping[str, Any]], labels: Sequence[int], *,
                    l2: float = 1.0, iterations: int = 300, lr: float = 0.1) -> dict[str, float]:
    """Regularised logistic regression of `labels` (1 = row correct) on the
    evidence terms of `rows` (each must carry `confidence_evidence`).
    Returns a new weight table {term: llr, "name_slope": .., "engine_shrink": ..,
    "prior": ..}; the L2 penalty pulls each weight toward its current prior,
    so with few labels the table barely moves and with many it is data-driven.
    Pure Python (no numpy) on purpose: it must run inside the frozen build."""
    terms = ["name_match", "engine"] + [t for t in LLR]
    prior_w = [NAME_SLOPE, ENGINE_SHRINK] + [LLR[t] for t in LLR]
    X = [_features(r.get("confidence_evidence") or [], terms) for r in rows]
    y = [1.0 if v else 0.0 for v in labels]
    w = list(prior_w)
    b = _logit(PRIOR)
    n = max(1, len(X))
    for _ in range(iterations):
        gw = [l2 * (w[j] - prior_w[j]) / n for j in range(len(w))]
        gb = 0.0
        for xi, yi in zip(X, y):
            p = _sigmoid(b + sum(wj * xj for wj, xj in zip(w, xi)))
            err = p - yi
            gb += err / n
            for j, xj in enumerate(xi):
                if xj:
                    gw[j] += err * xj / n
        w = [wj - lr * g for wj, g in zip(w, gw)]
        b -= lr * gb
    out = {t: w[i] for i, t in enumerate(terms) if t not in ("name_match", "engine")}
    out["name_slope"] = w[0]
    out["engine_shrink"] = w[1]
    out["prior"] = _sigmoid(b)
    return out


def apply_weights(table: Mapping[str, float]) -> None:
    """Install a fitted table (from `fit_llr_weights`) process-wide."""
    global NAME_SLOPE, ENGINE_SHRINK, PRIOR
    for t, v in table.items():
        if t in LLR:
            LLR[t] = float(v)
    if "name_slope" in table:
        NAME_SLOPE = float(table["name_slope"])
    if "engine_shrink" in table:
        ENGINE_SHRINK = float(table["engine_shrink"])
    if "prior" in table:
        PRIOR = float(table["prior"])
