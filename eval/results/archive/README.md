Archived 2026-10-26 to reclaim workspace space (nothing deleted; extract with `tar -xJf`):
- run_20261023_v5.tar.xz, run_20261023_v53.tar.xz — eICU/NHANES runs of engine v5.x (superseded by v7; kept for the first-submission audit trail)
- frozen_v1_20261021.tar.xz — frozen engine v1 source and results
- patches_history.tar.xz — registry patch scripts and candidate registries 13.2–13.4 (`eval/patches/`); `make_benchmark_package.py` paths referring to `eval/patches/` need extraction first
Exact-duplicate registry copies were replaced by symlinks to the canonical file (release/registry_*/ and eval/frozen_registry_13_3_0/); SHA-256 unchanged.
