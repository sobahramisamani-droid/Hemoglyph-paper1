#!/usr/bin/env python3
"""Hemoglyph v1.3.1 - pre-build verification.

Run before compiling. Exits non-zero on any blocking problem so the build
script stops instead of producing a broken executable.

Checks
  1. Python 3.10-3.12, 64-bit, not Anaconda-polluted
  2. PySide6 importable, version 6.5-6.8 (6.9+/6.10+ need UCRT newer than
     many Iranian Windows 10 installs - see HARDENING changelog)
  3. Nuitka importable (>= 2.0)
  4. A C compiler Nuitka can use (MSVC cl.exe or Nuitka's MinGW cache)
  5. Every first-party module compiles and imports (syntax / import errors)
  6. Clinical registries present, Brotli-decodable, and the guideline
     registry hash matches license_engine's pinned value
  7. app_icon.ico is a valid multi-size icon (16..256 px)
  8. qml/ tree present with pages/ and components/
  9. No secrets are about to be shipped (.env must NOT be bundled)
 10. Optional: pytest suite passes (--with-tests)
"""
from __future__ import annotations

import hashlib
import importlib
import os
import py_compile
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

FIRST_PARTY = ["app", "license_engine", "sarvis_tahlil", "calcu", "paygah_dade", "naam_haye_vizhegi",
               "models_scientific_references", "namaye_registry", "analyse_gidlines", "ocr", "_ocr_support",
               "ocr_consistency", "ocr_confidence", "prdicter", "AI", "cache_registry"]
IMPORT_SAFE = [m for m in FIRST_PARTY if m not in ("app",)]      # app.py starts Qt; compile-check only
REGISTRIES = ["HEMOGLYPH_FEATURE_REGISTRY.json.br", "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br",
              "HEMOGLYPH_GUIDELINE_REGISTRY.json.br"]

errors: list[str] = []
warnings: list[str] = []


def ok(msg):  print(f"  [OK]   {msg}")
def warn(msg): warnings.append(msg); print(f"  [WARN] {msg}")
def fail(msg): errors.append(msg); print(f"  [FAIL] {msg}")


def check_python():
    v = sys.version_info
    if not (3, 10) <= (v.major, v.minor) <= (3, 12):
        fail(f"Python {v.major}.{v.minor} - use 3.10, 3.11 or 3.12 for Nuitka + PySide6 6.8")
    else:
        ok(f"Python {sys.version.split()[0]}")
    if sys.maxsize <= 2 ** 32:
        fail("32-bit Python - Hemoglyph targets Windows x64")
    if "conda" in sys.version.lower() or os.environ.get("CONDA_PREFIX"):
        warn("Anaconda Python detected - build from a clean venv (python -m venv .venv) to avoid DLL conflicts")


def check_pyside():
    try:
        import PySide6
        from PySide6 import QtCore  # noqa: F401
    except Exception as e:
        fail(f"PySide6 not importable: {e}")
        return
    ver = tuple(int(x) for x in PySide6.__version__.split(".")[:2])
    if ver >= (6, 9):
        fail(f"PySide6 {PySide6.__version__} - pin 6.8.3 (Qt 6.9+/6.10+ fail with 'QtCore DLL load failed' on older Windows 10)")
    elif ver < (6, 5):
        warn(f"PySide6 {PySide6.__version__} is old; 6.8.3 is the tested version")
    else:
        ok(f"PySide6 {PySide6.__version__}")


def check_nuitka():
    try:
        import nuitka  # noqa: F401
        from nuitka import Version
        ver = Version.getNuitkaVersion()
        ok(f"Nuitka {ver}")
        if int(ver.split(".")[0]) < 2:
            fail("Nuitka < 2.0 - upgrade (pip install -U nuitka)")
    except Exception as e:
        fail(f"Nuitka not importable: {e}  (pip install nuitka zstandard ordered-set)")


def check_compiler():
    if sys.platform != "win32":
        warn("not on Windows - compiler check skipped")
        return
    if shutil.which("cl.exe"):
        ok("MSVC cl.exe on PATH (fastest, lowest-memory backend)")
        return
    cache = Path(os.environ.get("LOCALAPPDATA", "")) / "Nuitka" / "Nuitka" / "Cache" / "downloads" / "gcc"
    if cache.exists():
        ok("Nuitka MinGW64 cache present")
    else:
        warn("No compiler found yet - Nuitka will download MinGW64 (~100 MB) on first build; "
             "if your network blocks it, install 'Build Tools for Visual Studio' and re-run")


def check_modules():
    bad = 0
    for m in FIRST_PARTY:
        p = ROOT / f"{m}.py"
        if not p.exists():
            fail(f"missing module {m}.py"); bad += 1; continue
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            fail(f"{m}.py does not compile: {e}"); bad += 1
    if not bad:
        ok(f"{len(FIRST_PARTY)} first-party modules compile")
    import logging
    logging.disable(logging.CRITICAL)
    for m in IMPORT_SAFE:
        try:
            importlib.import_module(m)
        except Exception as e:
            fail(f"import {m} failed: {type(e).__name__}: {e}")
    ok("first-party modules import")


def check_registries():
    try:
        import brotli
    except ImportError:
        fail("brotli not installed (pip install brotli)"); return
    pinned = None
    try:
        import license_engine
        for name in dir(license_engine):
            v = getattr(license_engine, name)
            if isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v):
                pinned = v
                break
    except Exception:
        pass
    for r in REGISTRIES:
        p = ROOT / r
        if not p.exists():
            fail(f"registry missing: {r}"); continue
        try:
            raw = brotli.decompress(p.read_bytes())
        except Exception as e:
            fail(f"{r} is not valid Brotli: {e}"); continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        ok(f"{r}: {len(raw)/1e6:.1f} MB json, sha256 {sha[:12]}…")
        if r == "HEMOGLYPH_GUIDELINE_REGISTRY.json.br" and pinned and sha != pinned:
            fail(f"{r} sha256 does not match the value pinned in license_engine.py - the app will refuse to start")
    a, b = ROOT / "HEMOGLYPH_GUIDELINE_REGISTRY.json.br", ROOT / "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br"
    if a.exists() and b.exists() and a.read_bytes() != b.read_bytes():
        fail("HEMOGLYPH_GUIDELINE_REGISTRY.json.br and HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br differ - they must be identical")
    for stale in ROOT.glob("HEMOGLYPH_*.json"):
        warn(f"uncompressed {stale.name} present - br.py will NOT overwrite the .br, but remove it to avoid confusion")


def check_icon():
    p = ROOT / "app_icon.ico"
    if not p.exists():
        fail("app_icon.ico missing"); return
    d = p.read_bytes()
    try:
        _, typ, n = struct.unpack("<HHH", d[:6])
    except Exception:
        fail("app_icon.ico is not an ICO"); return
    if typ != 1 or n == 0:
        fail("app_icon.ico is not an ICO (type/entries)"); return
    sizes = set()
    for i in range(n):
        w, h = d[6 + 16 * i], d[7 + 16 * i]
        sizes.add(w or 256)
    need = {16, 32, 48, 256}
    if not need <= sizes:
        warn(f"app_icon.ico has sizes {sorted(sizes)}; Windows wants at least {sorted(need)}")
    else:
        ok(f"app_icon.ico valid ({n} images: {sorted(sizes)})")


def check_qml():
    q = ROOT / "qml"
    if not q.is_dir():
        fail("qml/ directory missing"); return
    for sub in ("pages", "components"):
        if not (q / sub).is_dir():
            fail(f"qml/{sub}/ missing (strict page/component separation)")
    mains = list(q.glob("*.qml"))
    ok(f"qml/ present ({len(list(q.rglob('*.qml')))} files, {len(mains)} root files)")


def check_secrets():
    env = ROOT / ".env"
    if env.exists():
        txt = env.read_text(encoding="utf-8", errors="ignore")
        if any(k in txt for k in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "sk-")):
            warn(".env contains API keys - the build scripts no longer bundle it; distribute .env.example instead")
    for script in ("build_nuitka.bat", "build_all.bat", "_post_build.py", "_organize_release.py"):
        p = ROOT / script
        if p.exists() and "include-data-files=.env=" in p.read_text(encoding="utf-8", errors="ignore"):
            fail(f"{script} still bundles .env (API keys would ship inside the release)")
    ok("no secret bundling in build scripts")


def run_tests():
    print("\n  running pytest …")
    r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"], cwd=ROOT)
    if r.returncode != 0:
        fail("pytest suite failed")
    else:
        ok("pytest suite passed")


def main() -> int:
    print("Hemoglyph 1.3.1 pre-flight\n")
    for name, fn in [("Python", check_python), ("PySide6", check_pyside), ("Nuitka", check_nuitka),
                     ("Compiler", check_compiler), ("Modules", check_modules), ("Registries", check_registries),
                     ("Icon", check_icon), ("QML", check_qml), ("Secrets", check_secrets)]:
        print(f"[{name}]")
        try:
            fn()
        except Exception as e:  # a check must never crash the build
            fail(f"{name} check crashed: {e}")
    if "--with-tests" in sys.argv:
        run_tests()
    print()
    if errors:
        print(f"PRE-FLIGHT FAILED: {len(errors)} blocking problem(s)")
        for e in errors:
            print("   -", e)
        return 1
    print(f"PRE-FLIGHT OK ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
