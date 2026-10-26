#!/usr/bin/env python3
"""
HEMOGLYPH Vision OCR CLI Diagnostic & Test Suite
Directly tests Vision API connection, model responses, and lab extraction in CMD.
"""

import os
import sys
import json
import base64
import time
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def print_banner():
    print("=" * 72)
    print("  HEMOGLYPH CLINICAL CDSS - VISION OCR CMD DIAGNOSTIC TOOL")
    print("=" * 72)

def get_registry_api_key() -> str:
    """Read saved OCR API key from Windows Registry if available."""
    if sys.platform != "win32":
        return ""
    try:
        import winreg
        key_path = r"Software\HEMOGLYPH\HEMOGLYPH"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            for val_name in ["ocrApiKey", "ocr_api_key", "groqApiKey"]:
                try:
                    val, _ = winreg.QueryValueEx(k, val_name)
                    if val and str(val).strip():
                        return str(val).strip()
                except OSError:
                    pass
    except Exception:
        pass
    return ""

def load_env_file():
    """Load .env file if present in current dir or script dir."""
    candidates = [Path.cwd() / ".env", Path(__file__).resolve().parent / ".env"]
    for c in candidates:
        if c.is_file():
            try:
                for line in c.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
                print(f"[+] Loaded environment variables from: {c}")
                break
            except Exception as e:
                print(f"[-] Could not read {c}: {e}")

def main():
    print_banner()
    load_env_file()

    # 1. Check Python packages
    print("\n[Step 1/5] Checking Required Python Libraries...")
    has_openai = False
    try:
        import openai
        from openai import OpenAI
        has_openai = True
        print(f"  [OK] openai package found: version {getattr(openai, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"  [ERROR] 'openai' package is NOT installed: {e}")
        print("          Fix: Run 'pip install openai'")

    try:
        import PIL
        from PIL import Image
        print(f"  [OK] Pillow (PIL) found: version {getattr(PIL, '__version__', 'unknown')}")
    except ImportError:
        print("  [WARN] Pillow not installed. Some image formats may fail.")

    try:
        import brotli
        print("  [OK] brotli compression library found.")
    except ImportError:
        print("  [WARN] brotli library not installed.")

    # 2. Check API Key
    print("\n[Step 2/5] Detecting OCR API Key...")
    api_key = None
    source = "None"

    # Command line argument override
    if len(sys.argv) > 2 and sys.argv[2].strip():
        api_key = sys.argv[2].strip()
        source = "CLI Argument"
    elif os.getenv("OCR_API_KEY"):
        api_key = os.getenv("OCR_API_KEY").strip()
        source = "Environment (OCR_API_KEY)"
    elif os.getenv("GROQ_API_KEY"):
        api_key = os.getenv("GROQ_API_KEY").strip()
        source = "Environment (GROQ_API_KEY)"
    else:
        reg_key = get_registry_api_key()
        if reg_key:
            api_key = reg_key
            source = "Windows Registry (HKCU\\Software\\HEMOGLYPH)"

    if not api_key:
        print("  [ERROR] No API Key found in Registry, Environment (.env), or CLI arguments!")
        print("  Usage: test_ocr_api.bat [path_to_image.jpg] [YOUR_API_KEY]")
        print("  Or add OCR_API_KEY=your_key in .env file.")
        return 1

    masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"  [OK] Found API Key from: {source}")
    print(f"  [OK] Key: {masked_key}")

    # Determine Provider and Base URL
    base_url = os.getenv("OCR_BASE_URL")
    if not base_url:
        if api_key.startswith("gsk_"):
            base_url = "https://api.groq.com/openai/v1"
            provider = "Groq Cloud"
        elif api_key.startswith("sk-proj-") or api_key.startswith("sk-"):
            base_url = "https://api.openai.com/v1"
            provider = "OpenAI Official"
        else:
            base_url = "https://api.openai.com/v1"
            provider = "OpenAI Compatible / Custom"
    else:
        provider = f"Custom Endpoint ({base_url})"

    print(f"  [OK] Provider: {provider}")
    print(f"  [OK] Base URL: {base_url}")

    # 3. Test Network & Client Initialization
    print("\n[Step 3/5] Testing Client Connection to API...")
    if not has_openai:
        print("  [FATAL] Cannot proceed without 'openai' package.")
        return 1

    client = None
    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0)
        print("  [OK] OpenAI client initialized successfully.")
    except Exception as exc:
        print(f"  [FATAL] OpenAI client creation failed: {exc}")
        return 1

    # 4. Determine Models to Test
    print("\n[Step 4/5] Testing Vision Models Availability...")
    custom_model = os.getenv("OCR_VISION_MODEL")
    candidate_models = []
    if custom_model:
        candidate_models.append(custom_model)

    if provider == "Groq Cloud":
        candidate_models.extend([
            "qwen/qwen3.8-27b",
            "meta-llama/llama-4-scout-17b-16e-instruct"
        ])
    else:
        candidate_models.extend([
            "gpt-4o-mini",
            "qwen/qwen3.8-27b",
            "gpt-4o",
        ])

    # Remove duplicates preserving order
    seen = set()
    models = [m for m in candidate_models if not (m in seen or seen.add(m))]
    print(f"  Target models to test: {models}")

    # 5. Check Test Image File
    print("\n[Step 5/5] Testing Vision Image Extraction...")
    image_path = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        cand_img = Path(sys.argv[1].strip())
        if cand_img.is_file():
            image_path = cand_img

    if not image_path:
        # Search for any test image in cwd
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            found = list(Path.cwd().glob(ext))
            if found:
                image_path = found[0]
                break

    if not image_path:
        print("  [NOTICE] No image path provided. Creating a minimal 1x1 test pixel to verify API handshake...")
        # Minimal transparent 1x1 PNG data URL
        data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        image_name = "Synthetic Test Pixel (1x1 PNG)"
    else:
        print(f"  [+] Testing with image: {image_path.resolve()}")
        image_name = image_path.name
        mime = "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        raw_bytes = image_path.read_bytes()
        b64 = base64.b64encode(raw_bytes).decode("utf-8")
        data_url = f"data:{mime};base64,{b64}"
        print(f"  [+] Image size: {len(raw_bytes):,} bytes, MIME: {mime}")

    prompt = (
        "Extract any laboratory test names and values from this image as a JSON array: "
        '[{"test_name": "...", "value": 0.0, "unit": "..."}]. If none, return []'
    )

    success = False
    for model_name in models:
        print(f"\n  ---> Sending Vision Request to Model: '{model_name}'...")
        start_t = time.time()
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ]
                }],
                temperature=0.0,
                max_tokens=500,
            )
            elapsed = time.time() - start_t
            content = resp.choices[0].message.content or ""
            print(f"  [SUCCESS] Response received in {elapsed:.2f}s!")
            print("  ---------------- Raw API Response Content ----------------")
            print(content.strip()[:1000])
            print("  ---------------------------------------------------------")
            success = True
            break
        except Exception as exc:
            elapsed = time.time() - start_t
            err_str = str(exc)
            print(f"  [FAILED] Model '{model_name}' returned error after {elapsed:.2f}s:")
            print(f"  >>> {exc.__class__.__name__}: {err_str}")

            # Specific diagnostics
            if "AuthenticationError" in err_str or "401" in err_str:
                print("  [DIAGNOSIS] Invalid API Key! The key is rejected by the server.")
            elif "NotFoundError" in err_str or "model_not_found" in err_str or "404" in err_str:
                print(f"  [DIAGNOSIS] Model '{model_name}' is not supported or deprecated on this endpoint.")
            elif "RateLimitError" in err_str or "429" in err_str:
                print("  [DIAGNOSIS] Rate limit exceeded or out of quota/credits.")
            elif "ConnectError" in err_str or "APIConnectionError" in err_str or "timeout" in err_str.lower():
                print("  [DIAGNOSIS] Connection failed! Check internet, proxy/VPN, or firewall blocking the API.")

    print("\n" + "=" * 72)
    if success:
        print("  [RESULT: PASS] Vision API is WORKING correctly!")
        print("  Hemoglyph will be able to extract lab features with this key and model.")
    else:
        print("  [RESULT: FAIL] Vision API failed with all tested models.")
        print("  Please check the exact error message printed above to fix the root cause.")
    print("=" * 72)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
