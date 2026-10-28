"""Assemble the frozen Paper-1 engine (v7 + registry 14.1.0) into a directory, verified against the freeze manifest.

    python3 tools/make_frozen_engine_dir.py /tmp/hemoglyph_v7

Engine files come from git tag `engine-v7-frozen` (commit 3968fec); the disease registry from
release/registry_14.1.0/; the feature registry from the repository root. Every file is hashed against
FREEZE_v15_20261025_sha256.txt. The feature registry is the one documented exception: the frozen bytes
(sha256 953d8daa...) were modified in place by registry patch 15.2.0 (ACTH unit block only, see
eval/registry_patches/patch_15_2_0.py::patch_features) and not archived; the current file (115427e7...) is
used and the difference is reported. No cohort used in the paper contains ACTH, so no frozen number depends on it.
"""
import hashlib, os, shutil, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAG = "engine-v7-frozen"
MANIFEST = os.path.join(ROOT, "FREEZE_v15_20261025_sha256.txt")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def main(out):
    os.makedirs(out, exist_ok=True)
    want = {l.split()[1]: l.split()[0] for l in open(MANIFEST) if l.strip()}
    for f in ("analyse_gidlines.py", "cache_registry.py", "calcu.py"):
        blob = subprocess.run(["git", "-C", ROOT, "show", f"{TAG}:{f}"], capture_output=True, check=True).stdout
        open(os.path.join(out, f), "wb").write(blob)
    src = os.path.join(ROOT, "release", "registry_14.1.0", "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br")
    for n in ("HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br", "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"): shutil.copy2(src, os.path.join(out, n))
    shutil.copy2(os.path.join(ROOT, "HEMOGLYPH_FEATURE_REGISTRY.json.br"), os.path.join(out, "HEMOGLYPH_FEATURE_REGISTRY.json.br"))
    ok = True
    for f in sorted(os.listdir(out)):
        h = sha(os.path.join(out, f)); exp = want.get(f)
        status = "OK" if h == exp else ("DOCUMENTED-DIFFERENCE" if f == "HEMOGLYPH_FEATURE_REGISTRY.json.br" else "MISMATCH")
        if status == "MISMATCH": ok = False
        print(f"{status:22s} {f}  {h[:16]}  (freeze {str(exp)[:16]})")
    print("frozen engine dir:", out, "| integrity", "PASS" if ok else "FAIL"); return 0 if ok else 1
if __name__ == "__main__": sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/hemoglyph_v7"))
