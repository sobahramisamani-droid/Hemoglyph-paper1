from __future__ import annotations
import sys
from pathlib import Path
"""Process-wide cache for registry payloads and derived objects.
Supports transparent Brotli (.br) and JSON decompression with thread-safe caching.
"""

import json
import logging
from pathlib import Path
import threading
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import brotli
except ImportError:
    brotli = None

# RLock, not Lock: FeatureRegistry's factory calls shared_object()
# again for its FeatureIndex, so the same thread re-enters here.
_lock = threading.RLock()
_objects: Dict[str, Any] = {}
_registries: Dict[str, Any] = {}


def bargozari_registry(path: str | Path) -> Optional[dict[str, Any]]:
    """Load a registry file from disk (JSON or Brotli .br), caching the result in memory.
    If the requested path does not exist, checks for .br or bare .json alternatives,
    and searches alongside the running executable or script directory.
    """
    p = Path(path)

    # Resolve fallback paths if the exact path does not exist
    if not p.exists():
        exe_dir = Path(sys.executable).resolve().parent
        curr_dir = Path(__file__).resolve().parent

        candidates = [
            exe_dir / p.name,
            Path(str(exe_dir / p.name) + ".br") if not p.name.endswith(".br") else exe_dir / p.name,
            curr_dir / p.name,
            Path(str(curr_dir / p.name) + ".br") if not p.name.endswith(".br") else curr_dir / p.name,
            p.with_suffix("") if p.suffix == ".br" else Path(str(p) + ".br"),
        ]
        found = False
        for cand in candidates:
            if cand.exists():
                p = cand
                found = True
                break
        if not found:
            logger.warning(f"Registry file not found: {path}")
            return None

    key = str(p.resolve())
    with _lock:
        if key in _registries:
            return _registries[key]

    raw_bytes = p.read_bytes()
    data: Optional[dict[str, Any]] = None

    # Check if file is Brotli compressed (by extension or header bytes)
    is_br = p.suffix == ".br" or (len(raw_bytes) > 0 and raw_bytes[0] in (0xce, 0xcb, 0x1b, 0x8b))

    if is_br:
        if brotli is None:
            raise RuntimeError(f"Brotli library required to decompress: {p}")
        try:
            decompressed = brotli.decompress(raw_bytes).decode("utf-8")
            data = json.loads(decompressed)
        except Exception as e:
            # Fallback to UTF-8 plain text if brotli decompression fails
            try:
                data = json.loads(raw_bytes.decode("utf-8"))
            except Exception:
                raise RuntimeError(f"Failed to decompress and parse {p}: {e}")
    else:
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except UnicodeDecodeError:
            if brotli is not None:
                try:
                    decompressed = brotli.decompress(raw_bytes).decode("utf-8")
                    data = json.loads(decompressed)
                except Exception as be:
                    raise RuntimeError(f"Failed to decode binary registry {p}: {be}")
            else:
                raise

    if data is not None:
        with _lock:
            _registries[key] = data

    return data


def shared_object(key: str, factory: Callable[[], Any]) -> Any:
    """Thread-safe singleton factory for expensive derived objects (like FeatureIndex)."""
    with _lock:
        if key not in _objects:
            _objects[key] = factory()
        return _objects[key]


def prefetch(*paths: str | Path) -> None:
    """Prefetch and cache one or more registries."""
    for p in paths:
        bargozari_registry(p)


def cache_stats() -> dict[str, int]:
    """Return runtime cache telemetry."""
    with _lock:
        return {"registries": len(_registries), "objects": len(_objects)}


__all__ = ["bargozari_registry", "shared_object", "prefetch", "cache_stats"]
