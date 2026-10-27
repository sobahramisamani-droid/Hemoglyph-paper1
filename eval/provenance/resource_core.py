#!/usr/bin/env python3
"""Phase B of eval/provenance/PROTOCOL.md: locate the ACTIVE-CORE rules' thresholds in their cited sources.

For every core rule (core_rules.json.gz) the cited source is fetched once from the sandbox (PDF, HTML, Europe PMC
full text for DOIs, PubMed abstract as last resort), cached under /tmp (not persisted), and searched for the
rule's threshold near an analyte term. Only a short verbatim quote (<= 300 chars) and a page/section locator are
written to core_locators.json. Nothing in the registry is modified; thresholds are never edited.

Match classes
  statement_found      analyte term and threshold number within 250 characters in full text
  statement_abstract   same, but only the PubMed abstract was reachable
  number_only          threshold number present, no analyte term near it
  number_absent        source text reachable, threshold number not present
  generic_landing      locator is an organisation/landing page without the document
  unreachable          fetch failed (HTTP error / block / timeout)
  no_locator           rule cites no source
"""
import gzip, json, os, re, sys, time, html, subprocess, hashlib, collections, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = "/tmp/src_cache"; os.makedirs(CACHE, exist_ok=True)
import brotli
reg = json.loads(brotli.decompress(open(os.path.join(ROOT, "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"), "rb").read()))
feat = json.loads(brotli.decompress(open(os.path.join(ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json.br"), "rb").read()))["features"]
S = reg["guideline_sources"]; S = {s.get("source_id", i): s for i, s in (S.items() if isinstance(S, dict) else enumerate(S))}
core = json.load(gzip.open(os.path.join(HERE, "core_rules.json.gz"), "rt"))
UA = "Mozilla/5.0 (X11; Linux x86_64) Hemoglyph-provenance/1.0"
GENERIC = re.compile(r"^(https?://)?(www\.)?[^/]+/?$|/publications/?$|/guidelines/?$|/clinical-practice-guidelines/?$", re.I)
DOI_RX = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.I)
# conversions used only to search for the same threshold expressed in the other common unit
CONV = {"creatinine": [("mg/dL", "umol/L", 88.4)], "glucose": [("mg/dL", "mmol/L", 1 / 18.0)], "blood_urea_nitrogen": [("mg/dL", "mmol/L", 0.357)],
        "total_bilirubin": [("mg/dL", "umol/L", 17.1)], "calcium_total": [("mg/dL", "mmol/L", 0.2495)], "hemoglobin": [("g/dL", "g/L", 10.0)],
        "albumin": [("g/dL", "g/L", 10.0)], "total_cholesterol": [("mg/dL", "mmol/L", 0.02586)], "ldl_cholesterol": [("mg/dL", "mmol/L", 0.02586)],
        "triglycerides": [("mg/dL", "mmol/L", 0.01129)], "lactate": [("mmol/L", "mg/dL", 9.01)], "phosphate": [("mg/dL", "mmol/L", 0.3229)],
        "magnesium": [("mg/dL", "mmol/L", 0.4114)], "uric_acid": [("mg/dL", "umol/L", 59.48)], "ferritin": [("ng/mL", "ug/L", 1.0)]}

def curl(url, out):
    try:
        r = subprocess.run(["curl", "-sL", "-m", "40", "-A", UA, "-o", out, "-w", "%{http_code} %{content_type}", url], capture_output=True, text=True, timeout=60)
        code, _, ctype = r.stdout.partition(" "); return int(code or 0), ctype
    except Exception:
        return 0, ""

def pdf_pages(path):
    from pypdf import PdfReader
    try:
        rd = PdfReader(path); return [(i + 1, (p.extract_text() or "")) for i, p in enumerate(rd.pages[:400])]
    except Exception:
        return []

def html_text(raw):
    raw = re.sub(r"(?is)<(script|style|nav|footer).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<(h[1-4])[^>]*>", r"\n@@H@@", raw); raw = re.sub(r"(?i)</h[1-4]>", "@@/H@@\n", raw)
    raw = re.sub(r"(?i)<(p|br|li|tr|div|td)[^>]*>", "\n", raw); raw = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(re.sub(r"[ \t\xa0]+", " ", raw))

def europepmc(doi):
    tmp = os.path.join(CACHE, "epmc_" + hashlib.md5(doi.encode()).hexdigest())
    code, _ = curl("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" + urllib.parse.quote(f'DOI:"{doi}"') + "&format=json&resultType=lite", tmp)
    if code != 200: return None, None
    try:
        res = json.load(open(tmp)).get("resultList", {}).get("result", [])
    except Exception:
        return None, None
    if not res: return None, None
    r = res[0]; pmcid, pmid = r.get("pmcid"), r.get("pmid")
    if pmcid:
        code, _ = curl(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML", tmp + ".xml")
        if code == 200 and os.path.getsize(tmp + ".xml") > 2000:
            return html_text(open(tmp + ".xml", errors="ignore").read()), "fulltext_epmc"
    if pmid:
        code, _ = curl(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract&retmode=text", tmp + ".abs")
        if code == 200: return open(tmp + ".abs", errors="ignore").read(), "abstract"
    return None, None

def fetch_source(sid):
    cp = os.path.join(CACHE, sid + ".json")
    if os.path.exists(cp): return json.load(open(cp))
    s = S.get(sid) or {}; url = (s.get("url") or "").strip(); doi = (s.get("doi") or "").strip() or (DOI_RX.search(url).group(0) if DOI_RX.search(url) else "")
    out = {"kind": "unreachable", "pages": [], "url": url, "doi": doi}
    if not url and not doi: out["kind"] = "no_locator"
    elif GENERIC.search(url) and not doi: out["kind"] = "generic_landing"
    else:
        if doi:
            txt, kind = europepmc(doi)
            if txt: out.update(kind=kind, pages=[(0, txt)])
        if out["kind"] in ("unreachable",) and url:
            tmp = os.path.join(CACHE, sid + ".bin"); code, ctype = curl(url, tmp)
            if code == 200 and os.path.exists(tmp):
                head = open(tmp, "rb").read(5)
                if head.startswith(b"%PDF") or "pdf" in ctype:
                    pages = pdf_pages(tmp)
                    if pages: out.update(kind="fulltext_pdf", pages=pages)
                else:
                    txt = html_text(open(tmp, errors="ignore").read())
                    out.update(kind="fulltext_html" if len(txt) > 3000 else "landing_short", pages=[(0, txt)])
            else:
                out["http"] = code
    json.dump(out, open(cp, "w")); return out

def terms(fid):
    f = feat.get(fid) or {}; t = f.get("terminology", {})
    names = {f.get("identity", {}).get("canonical_name", ""), f.get("identity", {}).get("short_name", "")}
    for k in ("synonyms", "abbreviations", "common_report_names"):
        v = t.get(k) or []; names |= set(v if isinstance(v, list) else [])
    names |= {fid.replace("_", " ")}
    return [n for n in names if n and len(n) >= 2]

def num_variants(v, fid, unit):
    vals = [("same", v)]
    for u_from, u_to, f in CONV.get(fid, []):
        if unit and unit.lower().replace("µ", "u") == u_from.lower(): vals.append((u_to, v * f))
        elif unit and unit.lower().replace("µ", "u") == u_to.lower(): vals.append((u_from, v / f))
    pats = []
    for tag, x in vals:
        s = (f"{x:.2f}".rstrip("0").rstrip(".")) if x != int(x) else str(int(x))
        alt = s.replace(".", "·")
        pats.append((tag, re.compile(r"(?<![\d.])(" + re.escape(s) + "|" + re.escape(alt) + r")(?![\d])")))
        if x != int(x) and len(s.split(".")[-1]) == 1: pats.append((tag, re.compile(r"(?<![\d.])" + re.escape(s + "0") + r"(?![\d])")))
    return pats

def heading_before(txt, pos):
    hs = [m for m in re.finditer(r"@@H@@(.*?)@@/H@@", txt[:pos], re.S)]
    return hs[-1].group(1).strip()[:120] if hs else ""

def leaves(ex):
    if not isinstance(ex, dict): return []
    if "feature_id" in ex: return [ex]
    out = []
    for k in ("all", "any", "all_of", "any_of", "none", "not"):
        for sub in (ex.get(k) or []): out += leaves(sub)
    return out

def search(rule, src):
    L = [l for l in leaves(rule.get("expression") or {}) if isinstance(l.get("value"), (int, float)) and l.get("feature_id")]
    if not L: return {"match": "non_numeric"}
    res = [search_leaf(l, src) for l in L]
    found = [r for r in res if r["match"] == "statement_found"]
    if found:
        r = dict(found[0]); r["leaves_found"] = f"{len(found)}/{len(L)}"
        if len(found) < len(L): r["match"] = "statement_found_partial"
        return r
    return {"match": "number_only" if any(r["match"] == "number_only" for r in res) else "number_absent", "leaves_found": f"0/{len(L)}"}

def search_leaf(ex, src):
    fid = ex.get("feature_id"); v = ex.get("value"); unit = ex.get("unit")
    T = [re.compile(r"(?i)(?<![a-z])" + re.escape(t) + r"(?![a-z])") for t in terms(fid)]
    best = None; number_seen = False
    for page, txt in src["pages"]:
        for tag, rx in num_variants(float(v), fid, unit):
            for m in rx.finditer(txt):
                number_seen = True; a, b = max(0, m.start() - 250), min(len(txt), m.end() + 250); win = txt[a:b]
                hit = next((t for t in T if t.search(win)), None)
                if hit:
                    q = re.sub(r"\s+", " ", txt[max(0, m.start() - 150): m.end() + 150]).replace("@@H@@", "").replace("@@/H@@", "").strip()
                    cand = {"match": "statement_found", "page": page, "section": heading_before(txt, m.start()), "unit_variant": tag, "quote": q[:300]}
                    if tag == "same": return cand
                    best = best or cand
    if best: return best
    return {"match": "number_only" if number_seen else "number_absent"}

def main():
    out_p = os.path.join(HERE, "core_locators.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    by_src = collections.Counter((r.get("source_ids") or ["(none)"])[0] for r in core.values())
    print(f"{len(core)} core rules, {len(by_src)} first sources", flush=True)
    t0 = time.time()
    for i, (rid, r) in enumerate(core.items()):
        if rid in out: continue
        sids = r.get("source_ids") or []
        if not sids: out[rid] = {"match": "no_locator"}; continue
        res = None
        for sid in sids[:3]:
            src = fetch_source(sid)
            if src["kind"] in ("no_locator", "generic_landing", "unreachable", "landing_short"):
                res = res or {"match": src["kind"] if src["kind"] != "landing_short" else "generic_landing", "source_id": sid}; continue
            m = search(r, src); m["source_id"] = sid; m["source_kind"] = src["kind"]
            if m["match"].startswith("statement_found") and src["kind"] == "abstract": m["match"] = "statement_abstract"
            if m["match"].startswith("statement"): res = m; break
            res = m if (res is None or res["match"] in ("generic_landing", "unreachable", "number_absent")) else res
        out[rid] = res
        if (i + 1) % 25 == 0:
            json.dump(out, open(out_p, "w")); print(f"{i+1}/{len(core)} {(time.time()-t0):.0f}s {collections.Counter(v['match'] for v in out.values()).most_common()}", flush=True)
    json.dump(out, open(out_p, "w"))
    c = collections.Counter(v["match"] for v in out.values()); print("DONE", c.most_common(), flush=True)

if __name__ == "__main__":
    main()
