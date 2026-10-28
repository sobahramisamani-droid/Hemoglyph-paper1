"""Insert the minted Zenodo DOI into every place that currently says the snapshot "will be archived".

    python3 tools/finalize_doi.py 10.5281/zenodo.NNNNNNN [--apply]

Without --apply it only shows what would change. Each replacement is asserted to match exactly once, so a
second run is a no-op failure rather than a silent duplicate. After --apply, rebuild the .docx files
(docs/paper1/v7/build_docx.py, build_supplement.py) and commit.
"""
import re
import sys

ROOT = __import__("os").path.join(__import__("os").path.dirname(__file__), "..")
DOI = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
APPLY = "--apply" in sys.argv
assert re.fullmatch(r"10\.5281/zenodo\.\d+", DOI), "expected a Zenodo DOI like 10.5281/zenodo.1234567"

EDITS = [
    ("docs/paper1/v7/Paper1_Hemoglyph_CMPB_EN_v7_R9.md",
     "The frozen v7/14.1.0 snapshot with SHA-256 manifests will be archived on Zenodo with a DOI before publication.",
     f"The frozen v7/14.1.0 snapshot with SHA-256 manifests is archived on Zenodo (doi:{DOI})."),
    ("docs/paper1/v7/Paper1_Hemoglyph_CMPB_EN_v7_R9_long.md",
     "The frozen v7/14.1.0 snapshot with SHA-256 manifests will be archived on Zenodo with a DOI before publication.",
     f"The frozen v7/14.1.0 snapshot with SHA-256 manifests is archived on Zenodo (doi:{DOI})."),
    ("CITATION.cff",
     'repository-code: "https://github.com/sobahramisamani-droid/Hemoglyph-AlA_1.3"',
     f'repository-code: "https://github.com/sobahramisamani-droid/Hemoglyph-AlA_1.3"\ndoi: "{DOI}"'),
    ("docs/paper1/v7/submission_CMPB/CHECKLIST.md",
     '2. Mint the Zenodo DOI for the frozen snapshot and replace "will be archived" with the DOI in Data availability',
     f'2. DONE — Zenodo DOI {DOI} inserted by tools/finalize_doi.py'),
]

for rel, old, new in EDITS:
    path = f"{ROOT}/{rel}"
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        sys.exit(f"{rel}: expected exactly one match, found {n} — stop and inspect")
    print(f"{'APPLY' if APPLY else 'would change'}  {rel}")
    if APPLY:
        open(path, "w", encoding="utf-8").write(text.replace(old, new))
if APPLY:
    print("done. Next: python3 docs/paper1/v7/build_docx.py && python3 docs/paper1/v7/build_supplement.py; commit; retag.")
