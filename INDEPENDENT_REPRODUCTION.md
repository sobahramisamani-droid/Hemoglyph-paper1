# Independent reproduction — instructions and log template

Anyone with a laptop can re-derive the main results of the paper without medical knowledge. If you do, please fill in the
log at the bottom and send it (or open a pull request); logs from people outside the author group are reported in
Supplementary Note 21 with the name, date, hardware and outcome exactly as received.

## What you need
Linux or macOS (Windows: WSL2), Python ≥ 3.11, about 3 GB of disk, 2 GB of RAM, an internet connection for the first step only.

## Steps (copy–paste)

```bash
git clone https://github.com/sobahramisamani-droid/Hemoglyph-paper1.git        # or unpack the Zenodo archive
cd Hemoglyph
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bash reproduce.sh quick        # ≈ 10 min, no external data: tests (720), verification ledger, mutation table
bash reproduce.sh v7           # ≈ 60 min: frozen engine v7 on NHANES 2017-18 (downloads ≈ 1 MB from CDC) → Table 4
```

Optional (Table 3, ≈ 40 min): download the eICU-CRD demo v2.0.1 CSVs from physionet.org/content/eicu-crd-demo/2.0.1/ into
`eval/realdata/eicu_demo/` and run `bash reproduce.sh eicu`.

Every step prints `PASS` or `FAIL` and the script stops at the first failure. Nothing is tuned or refitted; the frozen engine is
rebuilt from the git tag `engine-v7-frozen`, so the result does not depend on the working copy.

## What "PASS" means
- `quick`: the 720 tests pass; the verification ledger counts equal those in Supplementary Note 18; the mutation recall table
  equals Supplementary Note 16.
- `v7`: the nine NHANES AUROCs equal Table 4 to three decimals.
- `eicu`: flat recall@3/5/10 = 47.9/60.8/74.1 and two-tier @1/3/5 = 33.1/62.0/71.9 (Table 3).

Expected, documented difference: the integrity step reports the feature registry as `DOCUMENTED-DIFFERENCE` (see
`REPRODUCTION_LOG.md`). Anything else that fails is a finding — please report it.

## Log template (fill in and send)

```
Reproducer: <name>, <affiliation or "independent">, relationship to authors: <none / colleague / co-author>
Date: <YYYY-MM-DD>     Commit or Zenodo DOI: <git rev-parse HEAD>
Hardware / OS / Python: <e.g. laptop, 4 cores, 8 GB RAM, Ubuntu 24.04, Python 3.12>
quick : PASS / FAIL   wall time: <min>   notes: <...>
v7    : PASS / FAIL   wall time: <min>   notes: <...>
eicu  : PASS / FAIL / not run   wall time: <min>   notes: <...>
Anything unexpected: <...>
Signature (typed name is enough): <...>
```
