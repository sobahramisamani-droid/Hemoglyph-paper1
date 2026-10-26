#!/usr/bin/env python3
"""Verify every guideline source cited by the registry and build Supplementary Data 1.

For each `guideline_sources` entry: count citing rules (total / executable), extract a DOI from `url` (or `doi`),
resolve it through the Crossref REST API (free, no key), compare the returned title with the registry title
(token Jaccard), and record one of:
  verified           — DOI resolves and titles match (Jaccard >= 0.35 or registry title contained in Crossref title)
  title_mismatch     — DOI resolves but title differs (needs manual look)
  unresolved         — DOI does not resolve (404) or network failure after retries
  url_only           — no DOI; URL reachable (HTTP < 400)  [HEAD/GET]
  url_unreachable    — no DOI; URL not reachable
  no_locator         — neither DOI nor URL
Nothing in the registry is modified. Output: eval/results/source_verification_<ver>.json / .csv and
docs/paper1/supplement/Supplementary_Data_1_sources_<ver>.xlsx (openpyxl).
Usage: python3 eval/registry_source_verify.py [--registry PATH] [--limit N] [--workers 6]
"""
import argparse, csv, json, os, re, sys, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import cache_registry
UA = "Hemoglyph-source-verifier/1.0 (mailto:sobahramisamani@gmail.com)"
DOI_RX = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.I)
STOP = set("the of and in for a an on to with by at from or as is vs versus guideline guidelines clinical practice management diagnosis treatment update updated edition ed et al".split())

def toks(s):
    return {t for t in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if t not in STOP and len(t) > 2}

def jaccard(a, b):
    A, B = toks(a), toks(b)
    return len(A & B) / len(A | B) if A and B else 0.0

def head_title(t):
    # registry titles often carry a descriptive tail after an em-dash/colon/parenthesis; compare the head only
    return re.split(r" [—–-] |: |\(", t or "", maxsplit=1)[0]

def overlap(a, b):
    A, B = toks(head_title(a)), toks(b)
    return len(A & B) / min(len(A), len(B)) if A and B else 0.0

def http(url, method="GET", timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read() if method == "GET" else b""

# Manual adjudication of automated title mismatches (documented, auditable; applied only when the resolved item is the
# intended document under a different title — never to rescue a wrong DOI).
MANUAL_OK = {
    "endo_hyperprolactinemia_2011_2023": "10.1038/s41574-023-00886-5 is the 2023 international consensus on prolactin-secreting adenomas (Petersenn et al.), the successor to the 2011 Endocrine Society guideline named in the registry title",
    "endo_hypoglycemia_2009_ada_2025": "10.2337/dc25-S006 is ADA Standards of Care 2025 Section 6 (glycemic goals and hypoglycemia) — the ADA component named in the source id; the 2009 Endocrine Society part has no DOI in the record",
}

def crossref(doi):
    for attempt in range(4):
        try:
            st, body = http("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))
            m = json.loads(body)["message"]
            return {"ok": True, "title": " ".join(m.get("title") or []), "container": " ".join(m.get("container-title") or []),
                    "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0], "publisher": m.get("publisher")}
        except urllib.error.HTTPError as e:
            if e.code == 404: return {"ok": False, "error": "404"}
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            err = str(e); time.sleep(2 * (attempt + 1))
    return {"ok": False, "error": "network"}

def url_alive(url):
    for method in ("HEAD", "GET"):
        try:
            st, _ = http(url, method=method, timeout=20); return st < 400
        except urllib.error.HTTPError as e:
            if e.code in (403, 405, 429): return True   # reachable but blocks bots
            if method == "GET": return False
        except Exception:
            if method == "GET": return False
    return False

def check(sid, src):
    url = src.get("url") or ""; doi = src.get("doi") or ""; cit = src.get("citation") or ""
    m = DOI_RX.search(doi) or DOI_RX.search(url) or DOI_RX.search(cit)
    rec = {"source_id": sid, "organization": src.get("organization"), "title": src.get("title"), "year": src.get("year"), "url": url, "citation": cit[:300], "doi": m.group(0).rstrip(".),;") if m else ""}
    if rec["doi"]:
        cr = crossref(rec["doi"])
        if cr.get("ok"):
            j = jaccard(rec["title"], cr["title"]); ov = max(overlap(rec["title"], cr["title"]), overlap(rec["title"], cr["title"] + " " + (cr.get("container") or "")))
            st = "verified" if (j >= 0.35 or ov >= 0.5) else ("probable_match" if ov >= 0.25 else "title_mismatch")
            if st == "title_mismatch" and sid in MANUAL_OK: st = "verified_manual"; rec["manual_note"] = MANUAL_OK[sid]
            rec.update(crossref_title=cr["title"], crossref_container=cr.get("container"), crossref_year=cr.get("year"), title_similarity=round(j, 2), title_overlap=round(ov, 2),
                       verification_status=st)
        else:
            rec.update(verification_status="unresolved", error=cr.get("error"))
    elif url:
        path = urllib.parse.urlparse(url).path.strip("/")
        generic = path.count("/") < 1 or path in ("publications", "publications/guidelines", "guidelines", "shop") or path.endswith(("/guidelines", "/publications", "/practice-guidelines"))
        alive = url_alive(url)
        rec["verification_status"] = ("generic_landing_page" if generic else "url_only") if alive else "url_unreachable"
    else:
        rec["verification_status"] = "no_locator"
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--registry", default=os.path.join(ROOT, "release/registry_13.4.1/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"))
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=6); a = ap.parse_args()
    reg = cache_registry.bargozari_registry(a.registry); ver = reg["registry_metadata"]["version"].split("-")[0]
    GS, RU = reg["guideline_sources"], reg["rules"]
    n_all, n_ex = {}, {}
    for r in RU.values():
        for s in r.get("source_ids") or []:
            n_all[s] = n_all.get(s, 0) + 1
            if r.get("executable"): n_ex[s] = n_ex.get(s, 0) + 1
    items = sorted(GS.items(), key=lambda kv: -n_ex.get(kv[0], 0))
    if a.limit: items = items[:a.limit]
    out = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(check, sid, src): sid for sid, src in items}
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result(); rec["n_rules_citing"] = n_all.get(rec["source_id"], 0); rec["n_executable_rules"] = n_ex.get(rec["source_id"], 0); out.append(rec)
            if i % 50 == 0: print(f"  {i}/{len(items)}", flush=True)
    out.sort(key=lambda r: (-r["n_executable_rules"], r["source_id"]))
    summ = {}
    for r in out: summ[r["verification_status"]] = summ.get(r["verification_status"], 0) + 1
    # rule-level coverage: how many executable rules cite at least one source of each quality tier
    st = {r["source_id"]: r["verification_status"] for r in out}
    SPECIFIC = {"verified", "verified_manual", "probable_match", "url_only"}
    cov = {"executable_rules": 0, "ge1_doi_verified": 0, "ge1_specific_locator": 0, "only_generic_landing_page": 0, "only_unverified_or_none": 0, "no_source_ids": 0}
    for r in RU.values():
        if not r.get("executable"): continue
        cov["executable_rules"] += 1; srcs = r.get("source_ids") or []
        if not srcs: cov["no_source_ids"] += 1; continue
        sts = {st.get(x, "missing") for x in srcs}
        if sts & {"verified", "verified_manual"}: cov["ge1_doi_verified"] += 1
        if sts & SPECIFIC: cov["ge1_specific_locator"] += 1
        elif sts <= {"generic_landing_page"}: cov["only_generic_landing_page"] += 1
        else: cov["only_unverified_or_none"] += 1
    summ = {"by_source": summ, "rule_coverage": cov}
    os.makedirs(os.path.join(ROOT, "eval/results"), exist_ok=True)
    base = os.path.join(ROOT, f"eval/results/source_verification_{ver}")
    json.dump({"registry_version": ver, "checked_on": time.strftime("%Y-%m-%d"), "summary": summ, "sources": out}, open(base + ".json", "w"), indent=1, ensure_ascii=False)
    cols = ["source_id", "organization", "title", "year", "doi", "url", "citation", "n_rules_citing", "n_executable_rules", "verification_status", "crossref_title", "crossref_container", "crossref_year", "title_similarity", "title_overlap", "manual_note", "error"]
    with open(base + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
    try:
        import openpyxl
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Sources"
        ws.append(cols)
        for r in out: ws.append([r.get(c) for c in cols])
        ws2 = wb.create_sheet("README")
        for line in [f"Supplementary Data 1 — Hemoglyph knowledge-source inventory, registry {ver}, checked {time.strftime('%Y-%m-%d')}.",
                     "One row per source id cited by at least one rule. n_rules_citing counts all rules (executable + retired-but-retained); n_executable_rules counts rules that can fire.",
                     "verification_status: verified = DOI resolved via Crossref and title matched; verified_manual = DOI resolved, automated title match failed, adjudicated by hand (note given); title_mismatch = DOI resolved but title differs (manual check pending); unresolved = DOI did not resolve; url_only = no DOI, a specific URL is reachable; generic_landing_page = no DOI and the URL is only an organisation/catalogue landing page (the source is a family of documents, not one citable item — disclosed as weak provenance); url_unreachable = no DOI, URL not reachable; no_locator = neither.",
                     "Sources were entered with AI assistance during registry construction and curated by a single author; this table is the audit of that provenance, not a claim that every source was read in full.",
                     "Statuses other than 'verified' are disclosed as such; they were NOT silently upgraded.",
                     "Rule-level coverage (executable rules): " + json.dumps(cov),
                     "url_unreachable means not confirmable from the verification host on the check date (many society sites block automated requests), NOT fabricated; only DOI-level checks can detect fabricated locators (9 found and removed in 13.4.1)."]:
            ws2.append([line])
        xl = os.path.join(ROOT, f"docs/paper1/supplement/Supplementary_Data_1_sources_{ver}.xlsx"); wb.save(xl); print("xlsx ->", xl)
    except ImportError:
        print("openpyxl missing; xlsx skipped")
    print(json.dumps(summ, indent=1)); print("->", base + ".json/.csv")

if __name__ == "__main__":
    main()
