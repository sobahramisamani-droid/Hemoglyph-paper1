#!/usr/bin/env python3
"""
HEMOGLYPH Brotli Registry Compressor
Compresses raw JSON clinical registries into compact .json.br archives.
"""
import os
from pathlib import Path
import brotli

def compress_file(p: Path):
    out = p.with_suffix(p.suffix + ".br")
    data = p.read_bytes()
    compressed = brotli.compress(data, quality=9)
    out.write_bytes(compressed)
    ratio = (len(compressed) / len(data)) * 100
    print(f"[*] Compressed {p.name} ({len(data):,} bytes -> {len(compressed):,} bytes, ratio: {ratio:.1f}%) -> {out.name}")

def main():
    root = Path(__file__).resolve().parent
    targets = [
        "HEMOGLYPH_FEATURE_REGISTRY.json",
        "HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json",
        "HEMOGLYPH_GUIDELINE_REGISTRY.json",
    ]
    # Also find any other HEMOGLYPH_*.json files
    for f in root.glob("HEMOGLYPH_*.json"):
        if f.name not in targets and not f.name.endswith(".br"):
            targets.append(f.name)

    compressed_count = 0
    for target_name in targets:
        target_path = root / target_name
        br_path = target_path.with_suffix(target_path.suffix + ".br")
        if target_path.exists():
            # If .br doesn't exist or is older than the .json, compress it
            if not br_path.exists():
                compress_file(target_path)
                compressed_count += 1
            else:
                # SAFETY: an existing .br is the curated, hash-pinned registry (license_engine
                # verifies its SHA-256). Never overwrite it from a loose .json, even if the
                # .json looks newer. Delete the .br manually if you really intend to rebuild.
                print(f"[*] Keeping existing {br_path.name} ({br_path.stat().st_size:,} bytes); "
                      f"{target_name} ignored (set HEMOGLYPH_FORCE_BR=1 to override)")
                if os.environ.get("HEMOGLYPH_FORCE_BR") == "1":
                    compress_file(target_path)
                    compressed_count += 1
        elif br_path.exists():
            print(f"[*] Present (Brotli): {br_path.name} ({br_path.stat().st_size:,} bytes)")
        else:
            print(f"[-] Not found: {target_name}")

    print(f"[*] Compression check complete ({compressed_count} file(s) compressed).")

if __name__ == "__main__":
    main()
