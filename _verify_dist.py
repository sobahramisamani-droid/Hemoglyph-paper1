#!/usr/bin/env python3
"""Final gate: verify a finished Hemoglyph dist folder before it is shipped.

usage: python _verify_dist.py dist\\app.dist
Exit 1 on any blocking problem.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

REQUIRED_FILES = [
    "Hemoglyph.exe",
    "HEMOGLYPH_FEATURE_REGISTRY.json.br",
    "HEMOGLYPH_GUIDELINE_REGISTRY.json.br",
    "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br",
    "app_icon.ico",
    "Create_Desktop_Shortcut.bat",
]
REQUIRED_GLOBS = ["qml/*.qml", "qml/pages/*.qml", "qml/components/*.qml", "PySide6/**/qwindows.dll",
                  "**/Qt6Core.dll", "**/Qt6Qml.dll", "**/Qt6Quick.dll", "**/Qt6QuickControls2.dll",
                  "**/QtQuick/Controls/**/*", "python3*.dll"]
FORBIDDEN = [".env", "test_ocr_api.py", "test_ocr_api.bat", "hemoglyph.db"]
FIRST_PARTY_SRC = ["app.py", "license_engine.py", "analyse_gidlines.py", "ocr.py", "AI.py", "calcu.py",
                   "sarvis_tahlil.py", "prdicter.py", "ocr_confidence.py", "ocr_consistency.py"]
SECRET_MARKERS = (b"GROQ_API_KEY=gsk_", b"OPENROUTER_API_KEY=sk-", b"OPENAI_API_KEY=sk-")


def pe_has_icon_and_version(exe: Path) -> tuple[bool, bool]:
    data = exe.read_bytes()
    # cheap heuristics: RT_GROUP_ICON appears as resource type 14; version info block has the UTF-16 tag
    has_version = "VS_VERSION_INFO".encode("utf-16-le") in data and "1.3.1.0".encode("utf-16-le") in data
    # icon payload: PNG signature of the 256px image or BMP DIB headers inside .rsrc
    has_icon = b"\x89PNG\r\n\x1a\n" in data or data.count(b"\x28\x00\x00\x00\x20\x00\x00\x00\x40\x00\x00\x00") > 0
    return has_icon, has_version


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _verify_dist.py <dist folder>")
        return 2
    dist = Path(sys.argv[1])
    errs: list[str] = []
    warns: list[str] = []
    if not dist.is_dir():
        print(f"[ERROR] {dist} is not a directory")
        return 1
    for f in REQUIRED_FILES:
        if not (dist / f).exists():
            errs.append(f"missing {f}")
    for g in REQUIRED_GLOBS:
        if not any(dist.glob(g)):
            errs.append(f"missing {g}")
    for f in FORBIDDEN:
        if (dist / f).exists():
            errs.append(f"FORBIDDEN file present: {f}")
    for f in FIRST_PARTY_SRC:
        if (dist / f).exists():
            errs.append(f"readable source shipped: {f} (anti-tamper violation)")
    pyc = list(dist.rglob("*.pyc"))
    if pyc:
        warns.append(f"{len(pyc)} .pyc files present (Nuitka should not emit bytecode for first-party code)")
    # secrets scan over small text files
    for p in dist.rglob("*"):
        if p.is_file() and p.stat().st_size < 200_000 and p.suffix.lower() in {".env", ".txt", ".ini", ".cfg", ".json", ".example", ".bat", ".qml"}:
            b = p.read_bytes()
            if any(m in b for m in SECRET_MARKERS):
                errs.append(f"API key found inside {p.relative_to(dist)}")
    # registry hash pin
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import license_engine  # type: ignore
        pins = getattr(license_engine, "_REGISTRY_HASHES", {})
        for name, sha in pins.items():
            p = dist / name
            if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() != sha:
                errs.append(f"{name} hash != license_engine pin (app will refuse to start)")
    except Exception as e:
        warns.append(f"could not check registry pins: {e}")
    exe = dist / "Hemoglyph.exe"
    if exe.exists():
        has_icon, has_ver = pe_has_icon_and_version(exe)
        if not has_icon:
            warns.append("could not detect embedded icon resource in Hemoglyph.exe")
        if not has_ver:
            errs.append("Hemoglyph.exe lacks version resource 1.3.1.0")
        mz = exe.read_bytes()[:2]
        if mz != b"MZ":
            errs.append("Hemoglyph.exe is not a PE file")
    big = [p for p in dist.rglob("*") if p.is_file() and p.stat().st_size > 300_000_000]
    for p in big:
        warns.append(f"very large file in package: {p.relative_to(dist)} ({p.stat().st_size/1e6:.0f} MB)")
    for w in warns:
        print(f"[WARN] {w}")
    for e in errs:
        print(f"[ERROR] {e}")
    if errs:
        print(f"DIST VERIFICATION FAILED ({len(errs)} error(s))")
        return 1
    print("DIST VERIFICATION OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
