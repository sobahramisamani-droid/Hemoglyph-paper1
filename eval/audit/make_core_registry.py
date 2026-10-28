"""Part 2 (PROTOCOL_AUDIT.md): build the CORE registry = 15.1.0 with everything non-executable except
curated_* rules, rules with provenance.verified_quote, and rules whose first source is reference_interval_convention.
Output goes to /tmp (not a release artefact); this script is the reproducible definition."""
import brotli, json, sys, collections, hashlib
SRC = "/home/user/Hemoglyph/HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/REGISTRY_CORE_15_1_0.json.br"
d = json.loads(brotli.decompress(open(SRC, "rb").read()))
assert d["registry_metadata"]["version"].startswith("15.1.0")
keep = collections.Counter(); off = 0
for rid, r in d["rules"].items():
    if not r.get("executable"): continue
    st = str(r.get("status", "")); p = r.get("provenance") or {}
    if st.startswith("curated"): keep["curated"] += 1
    elif p.get("verified_quote"): keep["verified_quote"] += 1
    elif (r.get("source_ids") or [""])[0] == "reference_interval_convention": keep["convention"] += 1
    else: r["executable"] = False; r["status"] = "off_for_core_arm"; off += 1
d["registry_metadata"]["version"] = "15.1.0-CORE-ARM"
raw = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
open(OUT, "wb").write(brotli.compress(raw, quality=5))
print("kept", dict(keep), "total", sum(keep.values()), "off", off, "sha256", hashlib.sha256(raw).hexdigest()[:16])
