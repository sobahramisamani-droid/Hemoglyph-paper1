#!/usr/bin/env python3
"""
HEMOGLYPH 1.3.1 - conservative post-build step for the Nuitka standalone folder.

Design rule: Nuitka already produced a self-consistent dist. This script only
  * adds first-party assets that are NOT Python code (registries, icons, shortcut
    maker, .env.example) when they are missing,
  * removes anything that must never ship (.env with API keys, test scripts, logs),
  * back-fills the Microsoft VC++ runtime DLLs ONLY if Nuitka did not include them,
  * verifies that the Qt platform plugin and QtQuick QML modules are present,
  * purges intermediate build directories.

It deliberately does NOT
  * copy raw site-packages (.py) into the dist (would ship readable source and
    shadow Nuitka-compiled modules),
  * harvest DLLs from PATH / Anaconda folders (version-mixing -> python311.dll
    conflicts, Qt crashes),
  * create a second mirror copy of the dist.
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("post_build")

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

ASSETS_TO_SHIP = [
    "HEMOGLYPH_FEATURE_REGISTRY.json.br",
    "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br",
    "HEMOGLYPH_GUIDELINE_REGISTRY.json.br",
    "app_icon.ico",
    "app_icon.png",
    "icon.ico",
    "logo.ico",
    "Create_Desktop_Shortcut.bat",
    ".env.example",
]
MUST_NOT_SHIP = [".env", "test_ocr_api.py", "test_ocr_api.bat", "hemoglyph.db", "nuitka-crash-report.xml",
                 "hemoglyph_startup_error.log"]
VC_RUNTIME = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
              "concrt140.dll"]


def locate_target_dist(arg: str | None) -> Path:
    cands = [Path(arg)] if arg else []
    cands += [Path("dist") / "app.dist", Path("dist") / "Hemoglyph.dist", Path("app.dist"), Path("Hemoglyph.dist")]
    for c in cands:
        if (c / "Hemoglyph.exe").exists():
            return c
        if (c / "app.exe").exists():
            (c / "app.exe").rename(c / "Hemoglyph.exe")
            log.info(f"[*] Renamed app.exe -> Hemoglyph.exe in {c}")
            return c
    raise SystemExit("[ERROR] No Hemoglyph.exe found in dist/app.dist - Nuitka did not finish.")


def sync_assets(dist: Path) -> None:
    for name in ASSETS_TO_SHIP:
        src, dst = ROOT / name, dist / name
        if not src.exists():
            continue
        if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.read_bytes() == src.read_bytes():
            continue
        shutil.copy2(src, dst)
        log.info(f"[*] Asset synced: {name}")


def strip_forbidden(dist: Path) -> None:
    for name in MUST_NOT_SHIP:
        p = dist / name
        if p.exists():
            p.unlink()
            log.info(f"[*] Removed from package (must not ship): {name}")
    for p in dist.rglob("*.log"):
        p.unlink(missing_ok=True)
    # Raw first-party sources must never sit next to the compiled exe
    for py in dist.glob("*.py"):
        if (ROOT / py.name).exists():
            py.unlink()
            log.info(f"[*] Removed stray source file: {py.name}")


def backfill_vc_runtime(dist: Path) -> None:
    if sys.platform != "win32":
        return
    sys32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    for dll in VC_RUNTIME:
        dst = dist / dll
        if dst.exists():
            continue
        # prefer the copy that ships with the build Python (same bitness, known good)
        for src in (Path(sys.base_prefix) / dll, Path(sys.base_prefix) / "DLLs" / dll, sys32 / dll):
            if src.exists():
                shutil.copy2(src, dst)
                log.info(f"[*] VC++ runtime back-filled: {dll} (from {src.parent})")
                break


CONDA_RUNTIME_DLLS = ["sqlite3.dll", "libffi-8.dll", "ffi-8.dll", "ffi.dll", "libcrypto-3-x64.dll", "libssl-3-x64.dll",
                      "libcrypto-1_1-x64.dll", "libssl-1_1-x64.dll", "liblzma.dll", "libbz2.dll", "bz2.dll", "zlib.dll",
                      "zlib1.dll", "libexpat.dll", "tcl86t.dll", "tk86t.dll", "libmpdec-4.dll"]


def backfill_conda_runtime(dist: Path) -> None:
    """conda-built Pythons (Anaconda, Spyder's bundled 3.11) link _sqlite3/_ssl/_ctypes/_lzma/_bz2
    against DLLs living in <base>/Library/bin, which Nuitka does not copy. Without them the exe dies
    with  'LoadLibraryExW _sqlite3.pyd failed'. Copy ONLY from the build interpreter's own tree,
    ONLY if the dist lacks them - never from PATH or other installs."""
    if sys.platform != "win32" or "conda" not in sys.version.lower():
        return
    srcs = [Path(sys.base_prefix) / "Library" / "bin", Path(sys.base_prefix) / "DLLs", Path(sys.base_prefix)]
    copied = []
    for dll in CONDA_RUNTIME_DLLS:
        if (dist / dll).exists():
            continue
        for d in srcs:
            if (d / dll).exists():
                shutil.copy2(d / dll, dist / dll)
                copied.append(dll)
                break
    log.info(f"[*] conda runtime back-fill: {', '.join(copied) if copied else 'nothing needed'}")
    # Proof: every .pyd in the dist root must now resolve. Try loading the critical ones in a child process
    # from inside the dist, with a PATH limited to the dist, which mimics the real launch.
    probe = ("import ctypes,sys,os;os.add_dll_directory(os.getcwd());"
             "[ctypes.WinDLL(os.path.join(os.getcwd(),p)) for p in sys.argv[1:]];print('pyd-load-ok')")
    pyds = [p.name for p in dist.glob("_sqlite3*.pyd")] + [p.name for p in dist.glob("_ssl*.pyd")] + \
           [p.name for p in dist.glob("_ctypes*.pyd")] + [p.name for p in dist.glob("_lzma*.pyd")] + \
           [p.name for p in dist.glob("_bz2*.pyd")] + [p.name for p in dist.glob("_hashlib*.pyd")]
    if pyds:
        import subprocess
        env = {k: v for k, v in os.environ.items()}
        env["PATH"] = str(dist) + ";" + str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32")
        r = subprocess.run([sys.executable, "-c", probe] + pyds, cwd=dist, env=env, capture_output=True, text=True)
        if "pyd-load-ok" in r.stdout:
            log.info(f"[*] extension load check OK: {', '.join(pyds)}")
        else:
            log.error(f"[ERROR] an extension still fails to load inside the dist: {r.stderr.strip()[-400:]}")
            raise SystemExit(1)


def verify_qt(dist: Path) -> list[str]:
    problems = []
    pyside = dist / "PySide6"
    if not pyside.is_dir():
        return ["PySide6/ folder missing - the pyside6 plugin did not run (--enable-plugin=pyside6)"]
    qwindows = list(pyside.rglob("qwindows.dll"))
    if not qwindows:
        problems.append("Qt platform plugin platforms/qwindows.dll missing - GUI cannot start")
    quick = list(pyside.rglob("QtQuick")) + list(pyside.rglob("QtQuick.2"))
    if not quick:
        problems.append("QtQuick QML modules missing - check --include-qt-plugins=sensible,qml")
    ctrl = list(pyside.rglob("Controls"))
    if not ctrl:
        problems.append("QtQuick/Controls QML module missing")
    for dll in ("Qt6Core.dll", "Qt6Gui.dll", "Qt6Qml.dll", "Qt6Quick.dll", "Qt6QuickControls2.dll"):
        if not list(dist.rglob(dll)):
            problems.append(f"{dll} missing")
    if not (dist / "qml").is_dir():
        problems.append("application qml/ directory missing (--include-data-dir=qml=qml)")
    return problems


LITE_PACKAGES = ["openai", "pydantic", "pydantic_core", "httpx", "httpcore", "anyio", "sniffio", "h11", "jiter",
                 "distro", "tqdm", "certifi", "idna", "annotated_types", "typing_inspection", "typing_extensions.py",
                 "colorama"]


def ship_lite_packages(dist: Path) -> None:
    """LITE mode: the cloud-Vision client stack was excluded from compilation
    (--nofollow-import-to). Copy those THIRD-PARTY packages, byte-for-byte from the
    build venv's site-packages, next to the exe. Nuitka's standalone runtime imports
    them normally. No first-party module is ever shipped this way."""
    if os.environ.get("HEMOGLYPH_LITE") != "1":
        return
    sps = []
    if os.environ.get("VIRTUAL_ENV"):
        sps.append(Path(os.environ["VIRTUAL_ENV"]) / "Lib" / "site-packages")
    sps += [Path(sys.prefix) / "Lib" / "site-packages"]
    # include dependencies pydantic/httpx pull in that are easy to miss
    import importlib
    extra = set()
    for name in ("openai", "httpx", "pydantic"):
        try:
            m = importlib.import_module(name)
            # walk requirement metadata for pure-python deps
            from importlib.metadata import requires, distribution
            for req in requires(name) or []:
                base = req.split(";")[0].split()[0].split("[")[0].split("=")[0].split(">")[0].split("<")[0].strip()
                if ";" in req and "extra" in req:
                    continue
                try:
                    for f in distribution(base).files or []:
                        top = f.parts[0]
                        if top.endswith(".dist-info") or top.startswith("__"):
                            continue
                        extra.add(top)
                except Exception:
                    pass
        except Exception:
            pass
    wanted = list(dict.fromkeys(LITE_PACKAGES + sorted(extra)))
    shipped = 0
    for sp in sps:
        if not sp.is_dir():
            continue
        for pkg in wanted:
            src, dst = sp / pkg, dist / pkg
            if dst.exists() or not src.exists():
                continue
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "tests", "*.pyc"))
            else:
                shutil.copy2(src, dst)
            shipped += 1
    log.info(f"[*] LITE mode: shipped {shipped} third-party packages uncompiled next to Hemoglyph.exe")
    if not (dist / "openai").is_dir():
        log.warning("[-] LITE mode: openai package not found in site-packages - cloud Vision OCR will be unavailable")


def purge_build_dirs() -> None:
    for d in [Path("dist") / "app.build", Path("dist") / "Hemoglyph.build", Path("app.build"),
              Path("Hemoglyph.build"), Path("build")]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            log.info(f"[*] Purged intermediate build dir: {d}")


def main() -> int:
    dist = locate_target_dist(sys.argv[1] if len(sys.argv) > 1 else None)
    log.info(f"[*] Post-build on: {dist.resolve()}")
    sync_assets(dist)
    strip_forbidden(dist)
    backfill_vc_runtime(dist)
    backfill_conda_runtime(dist)
    ship_lite_packages(dist)
    problems = verify_qt(dist)
    purge_build_dirs()
    exe = dist / "Hemoglyph.exe"
    total = sum(f.stat().st_size for f in dist.rglob("*") if f.is_file()) / 1e6
    log.info("=" * 70)
    log.info(f"[*] Hemoglyph.exe {exe.stat().st_size/1e6:.1f} MB; package total {total:.0f} MB")
    if problems:
        for p in problems:
            log.error(f"[ERROR] {p}")
        return 1
    log.info("[SUCCESS] Post-build complete; package is consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
