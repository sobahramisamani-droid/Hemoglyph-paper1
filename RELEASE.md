# Release and deposit — the exact order for Paper 1 (one sitting, ≈ 40 minutes plus one optional 10-minute check)

Everything below is free. Do the steps in this order; each step depends on the previous one.

## 0. Gate (2 min)
```bash
bash tools/release_check.sh          # must print no FAIL
```

## 1. GitHub push (5 min)
```bash
git remote add origin https://github.com/sobahramisamani-droid/Hemoglyph-AlA_1.3.git   # once
git push origin main --tags
```
Then on GitHub: Settings → General → confirm the repository is **public**; About → add the paper title and the topics
`clinical-decision-support`, `laboratory-medicine`, `verification`, `reproducibility`. The licence badge should read AGPL-3.0.

## 2. Public-clone check (10 min, optional but worth it)
On any machine with Python ≥ 3.11:
```bash
git clone https://github.com/sobahramisamani-droid/Hemoglyph-AlA_1.3.git && cd Hemoglyph-AlA_1.3
bash reproduce.sh quick
```
Paste the last 20 lines into `REPRODUCTION_LOG.md` under "public clone" and commit. (This is what Supplementary Note 21 points to.)

## 3. Zenodo (10 min)
1. zenodo.org → log in with the GitHub account → **GitHub** tab → flip the switch next to `Hemoglyph-AlA_1.3` to ON.
2. On GitHub: Releases → *Draft a new release* → tag **`paper1-R9-submitted`** (create on `main`), title
   `Paper 1 — CMPB submission snapshot (R9)`, description: one line pointing to `README.md` and `reproduce.sh` → *Publish release*.
   Zenodo picks up `.zenodo.json` (title, creators, licence, description) automatically; the archive is created within a few minutes.
3. Zenodo → *Upload* → the new record → copy the **version DOI** (`10.5281/zenodo.NNNNNNN`, not the concept DOI).

## 4. Put the DOI into the manuscript (5 min)
```bash
python3 tools/finalize_doi.py 10.5281/zenodo.NNNNNNN            # dry run, shows 4 edits
python3 tools/finalize_doi.py 10.5281/zenodo.NNNNNNN --apply
python3 docs/paper1/v7/build_docx.py && python3 docs/paper1/v7/build_supplement.py
git commit -am "Zenodo DOI inserted" && git push origin main
```
The package folder (`ارسال پیپر ۱/`) now holds the final .docx files.

## 5. OSF registration of the human-audit protocol (10 min)
osf.io → *Create new project* `Hemoglyph human concordance audit (Note 19)` → *Registrations* → *New registration* →
**Open-Ended Registration** → paste `eval/audit/human_audit/rater_package/OSF_REGISTRATION_Note19.md` → attach
`human_audit_sample_100.csv`, `SHA256SUMS`, `analyse_human_audit.py` → *Register* → choose **make public immediately**.
Copy the registration URL into Supplementary Note 19 ("Status" paragraph) with the same `finalize` discipline: a single sentence,
`Registered on OSF on <date>: <url>.`, then rebuild the supplement and commit.

## 6. Submit
`submit.elsevier.com/CMPB` with the files listed in `docs/paper1/v7/submission_CMPB/CHECKLIST.md`. After the confirmation e-mail:
```bash
git tag -a paper1-R9-submitted-final -m "as submitted, manuscript id <id>" && git push origin --tags
```

## What must *not* be done at release time
No edit to engine, registries, evaluation scripts, frozen outputs or any number; no re-run of a frozen cohort. If `release_check.sh`
fails, fix the thing it names (usually `__pycache__` or an uncommitted file) and nothing else.
