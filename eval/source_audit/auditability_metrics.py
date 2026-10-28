"""Two-level auditability metrics for the frozen 200-rule concordance sample (Supplementary Note 8), computed
from the committed files only — no new rating, no new retrieval.

Level 1  Locator granularity (from the URL string of every cited source):
           doi_or_pmc (document-level persistent identifier) | document_page (a specific page/PDF) | organisation_landing.
Level 2  Source retrievability: at least one cited URL returned document text in the frozen retrieval log
           (source_access_status.json: ok == True and >= 500 characters).
Level 3  Statement located = rule verifiable: the rater found the statement (verdict CONCORDANT or DISCORDANT).
           Otherwise the frozen reason code of the UNRESOLVABLE verdict is kept.

Verifiable Evidence Coverage (VEC) = rules whose statement was located / all sampled rules (denominator = n sampled,
not the retrievable subset). Wilson 95% CIs. Output: auditability_metrics.{json,md}.
"""
import csv, json, math, re, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "sample_200.csv"), encoding="utf-8")))
acc = json.load(open(os.path.join(HERE, "source_access_status.json")))
def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))
def pct(k, n): lo, hi = wilson(k, n); return f"{100*k/n:.1f}% ({100*lo:.1f}–{100*hi:.1f})" if n else "—"
def locator_class(u):
    u = u.lower()
    if "doi.org" in u or re.search(r"/10\.\d{4,}/", u) or "pubmed" in u or "/pmc" in u: return "doi_or_pmc"
    if ".pdf" in u or len(u.strip("/").split("/")) > 4: return "document_page"
    return "organisation_landing"
RANK = {"doi_or_pmc": 2, "document_page": 1, "organisation_landing": 0}
per = []
for r in rows:
    urls = [u.strip() for u in r["source_urls"].split(";") if u.strip()]
    best = max((locator_class(u) for u in urls), key=lambda c: RANK[c], default="none")
    retr = any((acc.get(u) or {}).get("ok") and (acc.get(u) or {}).get("chars", 0) >= 500 for u in urls)
    lab = r["rater1_label"]; located = lab in ("CONCORDANT", "DISCORDANT")
    per.append({"rule_id": r["rule_id"], "stratum": r["stratum"], "best_locator": best, "retrievable": retr, "located": located,
                "verdict": lab, "reason": "" if located else r["rater1_note"].strip()})
out = {"n": len(per), "definitions": __doc__.strip(), "by_stratum": {}, "by_locator": {}, "reasons_by_locator": {}}
lines = ["## Supplementary Table S18 — Two-level auditability of the frozen 200-rule sample (computed from the committed Note 8 files; no new rating)", "",
         "| Stratum | n | Level 2: source retrievable | Level 3: statement located (VEC) | concordant | discordant | unresolvable |", "|---|---|---|---|---|---|---|"]
for s in ["A", "B1", "B2", "all"]:
    P = [p for p in per if s == "all" or p["stratum"] == s]; n = len(P)
    k2 = sum(p["retrievable"] for p in P); k3 = sum(p["located"] for p in P)
    C = sum(p["verdict"] == "CONCORDANT" for p in P); D = sum(p["verdict"] == "DISCORDANT" for p in P)
    out["by_stratum"][s] = {"n": n, "retrievable": k2, "located": k3, "C": C, "D": D, "U": n - k3, "VEC": k3 / n, "VEC_ci": wilson(k3, n)}
    name = {"A": "A curated anchors", "B1": "B1 eICU-relevant AI-drafted", "B2": "B2 uniform AI-drafted", "all": "**All**"}[s]
    lines.append(f"| {name} | {n} | {pct(k2, n)} | {pct(k3, n)} | {C} | {D} | {n - k3} |")
lines += ["", "| Level 1: best locator class among the rule's sources | n rules | source retrievable | statement located | most frequent unresolvable reason |", "|---|---|---|---|---|"]
for c in ["doi_or_pmc", "document_page", "organisation_landing"]:
    P = [p for p in per if p["best_locator"] == c]; n = len(P)
    if not n: continue
    k2 = sum(p["retrievable"] for p in P); k3 = sum(p["located"] for p in P)
    reasons = collections.Counter(p["reason"] for p in P if not p["located"])
    out["by_locator"][c] = {"n": n, "retrievable": k2, "located": k3}; out["reasons_by_locator"][c] = dict(reasons)
    top = reasons.most_common(1)[0] if reasons else ("—", 0)
    lines.append(f"| {c} | {n} | {pct(k2, n)} | {pct(k3, n)} | {top[0].replace('_', ' ')} ({top[1]}) |")
reasons_all = collections.Counter(p["reason"] for p in per if not p["located"])
lines += ["", "Unresolvable reason codes (frozen with the verdicts): " + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in reasons_all.most_common()) + ".",
          "", "Reading: retrievability (a document opens) and verifiability (the document contains the encoded threshold, operator, unit and population) are different properties; the gap between the two columns is the cost of organisation-level and methodological locators. VEC uses all sampled rules as denominator. These are properties of the registry's locators as rated by the single declared AI rater (Note 8); they are not clinical validity."]
out["reasons_all"] = dict(reasons_all); out["per_rule"] = per
json.dump(out, open(os.path.join(HERE, "auditability_metrics.json"), "w"), indent=0)
open(os.path.join(HERE, "auditability_metrics.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
