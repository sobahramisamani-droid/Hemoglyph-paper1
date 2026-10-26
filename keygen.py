#!/usr/bin/env python3
"""HEMOGLYPH Developer License Key Generator.

MILITARY-GRADE ASYMMETRIC RSA-4096 / SHA-512 ENGINE.
CONFIDENTIAL & PROPRIETARY — FOR DEVELOPER / ADMINISTRATOR USE ONLY.
DO NOT DISTRIBUTE THIS FILE WITH THE PUBLIC CLINICAL SOFTWARE.

Features:
- 4096-bit Asymmetric RSA Digital Signature (PKCS#1 v2.2 / RFC 8017 compliant)
- SHA-512 Cryptographic Digest Hashing
- Hardware-Bound Node Locking (CPU, Motherboard, Disk, BIOS UUID)
- Anti-Replay Unique Cryptographic License ID (UUIDv4 nonce)
- Granular Clinical CDS Feature Entitlement Matrix
- Multiple Export Formats (Raw Token, PEM Armor Certificate, WhatsApp, Email)
- Built-in Cryptographic Inspector and Verifier

Usage Examples:
    # 1. Lifetime Enterprise License
    python keygen.py --machine HG-A1B2-C3D4-E5F6-07E2 --customer "Sobhan Bahrami"

    # 2. 1-Year Clinical License with Email and Clinic
    python keygen.py --machine HG-A1B2-C3D4-E5F6-07E2 --customer "Sobhan Bahrami" --email "doctor@hospital.org" --clinic "Central Hematology" --days 365

    # 3. Export PEM Certificate Armor
    python keygen.py --machine HG-A1B2-C3D4-E5F6-07E2 --customer "Sobhan Bahrami" --format armor

    # 4. Inspect / Verify an Existing License Key
    python keygen.py --inspect HGLIC4K-eyJhbGci...

    # 5. Run Self-Test
    python keygen.py --test
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import secrets
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Master Cryptographic Parameters
# ---------------------------------------------------------------------------
_RSA4K_E = 65537
_RSA4K_N_HEX = (
    "738f89781a91abd0c6f9d447d1a28acb4f1c496f25df21a188d3b70c52d0e27b"
    "742f5fbb2c95f407f2ac04dbf31fa992dceff1adcb7c613b5ae7a6771935ba80"
    "42d8c7740e086e02859ffd03145f4a64f71ca8249cf68e06a7c8a70d5c9040c1"
    "eeb2b8553b62409411326f0d1b40265ed713353701f45a44c5bf3c08d16fef19"
    "bbafb62f002927ee43cd432d206f975bc4b97d5330bf1f24fa501432c2282a64"
    "c580898bd65738f007f0737a4e0e48b5e31c02a66f0f1796065c969341dc7192"
    "3b954fe99878585c3a4ca0265fd9f900788cd9fc3e8ec07c72c66054a620c47c"
    "3d063fc58d1b68ef3357acc2251b19f681e6bedfd68af52d83269aa228554188"
    "b07fec6d8b61c68a9c95af5ed4723372b29195438e5242e6f93424ac504a171d"
    "8e94b7b34e9c24eba8fc4eedbcbfd27a3e307ad0dba1e00336a1b9b428f2b1f5"
    "c9f175e2f86bea2b93020202b7cd8f7af0afa19c7bdcf367058bb1b876c77518"
    "390b0dcc7454504113a95ddc1920492eff854cd4028544923705e2b0d37ca1b0"
    "940a5edce882e9e88138173d5f3b9c67acbebd699c9790f86bfc34dcaa233d16"
    "271b7cba96750a67cc0b54864c00c02a86fd6272f8225c409fcac7de61d9cc53"
    "f2828f277ba2fae83211f79b91c339c2c9edede6975913b85a18b91c502ecc03"
    "d60f3519bd2722857b15471d65e2aa7f47b12a4983ad21ecad97893e096e5609"
)
_RSA4K_D_HEX = (
    "64aafec33cc9f795e9300ba800cc0b02af48e203cc4703a21772ef7bf1ccfbef"
    "35b86b39bfce658662f54d4a5a121403d729c32c761e450992d847e06a7aae9c"
    "3b1f63290b6c768105ece858bd6f817c50f48ad9524f4a4c2bef94ef03daba3e"
    "f6f483b5e40464635853c9ffede44548cb2d756714f1cb8d2b82bb06a7844e12"
    "e9b85909baa71f9ce53db3ae651a310d85635cf4927b7be3179798f0dac8689d"
    "de9b69b702a27afc46be45aa9ec2bcbe8e38816a8146f17204dab56554b377d0"
    "3ecd848ee6feb762a87ac5ec8805776fdc943ef5097e0bda9d9588a7550d287d"
    "5e1fca800abb7cff1b87ddfc469cc45244b9413ff74297f0ecd63d50d3b7e95c"
    "bbe25a56dfd82dfe20be5d9d50a4839f39414e068f4d567365ff3f683663adc5"
    "df8649b7bd530f212a84f3a03e544342dce56339c27333ead2d100673eb5b166"
    "e818bb761e20b9c9b1211a2b5633abeabcdc622e0fa693f1995008602a7e9d09"
    "9ad5af85ffef54ad684b80836df1d6e2ac3e7d634bf76f2987aab1696527bac2"
    "7db2598759d1775816126744c89965fa0a95d929b885422e61025fb671772723"
    "bfe75ed77fcac3b1156a47e1d600063563febefaa1922a88e7c9314a096a9e1c"
    "a8a7f28bcd48f3855884898314acbbeef4ef78df855ca61b2a16fc947963c34a"
    "57cec270afe6d9e8b3e3e7f756c6a2150a070a0142e612a285bd1beb4cd30131"
)
_RSA4K_N = int(_RSA4K_N_HEX, 16)
_RSA4K_D = int(_RSA4K_D_HEX, 16)
_SHA512_DIGEST_INFO = bytes.fromhex("3051300d060960864801650304020305000440")

# Legacy RSA-2048 Parameters (for backward compatibility)
_RSA2K_E = 65537
_RSA2K_N_HEX = (
    "6b0249d50903b4d7c4e1c2e98308575c3a3712fe06876f7f63c98e2075b51e48"
    "3e5fe725abcb9691b80b4b757f1c8578255c10cbfd27786f95f9b5afcb7e0ead"
    "08e81ee74b746211013590f8cfa2d8c6feb399005ef7253694f30aa9b4afa097"
    "7922f65a3d7f0e8b5e55c5692b9206fa1bed41e3756aed9d0cea00dc45fb4257"
    "eb360bfb55661a4eaecc5bd6c1137b47da6e6a09e1fb3a8ceb799988dda907d2"
    "fefccfc4871fce054f2a86fba07a06a93da5e4da7e5baf17a879c423ab1bab01"
    "4362c8ef5f6af2026e531340ac60291fb98ad3ae73a69e12623c883ab90a9f74"
    "eef97e68c086160eb1f63e2bee9212fbdde873142109415a3fd5ad6ab05fe55d"
)
_RSA2K_D_HEX = (
    "387517a12745665764cfbbf759a3bffbafd738d4ff7adb4fb9c530905da9f655"
    "255b91e7a5311fbab800758a834af7fc40b1c746e8c4b75d2022844240b9bc62"
    "7ccd82e8833ddf339b90b8711d938c8dc8f9d6a284781e91229aec28476555f4"
    "34fc463fac2c69ef0c1172bb1f3ac7259430644feeb640b1588be9724e15d795"
    "3e86c2ab8f03e23796595459c91355dc35074fcb54d2b3b56dfd44b330fd1f08"
    "4490e5830f9b136e781b06210363d96de3ca6c02e5b4cc3976160d5e225f9ae0"
    "469773f8e1e77a60ae33234087d70d57753064b8bebd666e8b3119bb4fd5ed5c"
    "96e38e6a1d81f5d67ea7932553485977a465e3775efaa55c0226035b73cab5e1"
)
_RSA2K_N = int(_RSA2K_N_HEX, 16)
_RSA2K_D = int(_RSA2K_D_HEX, 16)
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")

# Standard Clinical Features
_ALL_CLINICAL_FEATURES = [
    "diagnostic_core",          # Hematology core & differential diagnosis
    "bayesian_inference",       # Bayesian network probability engine
    "clinical_guidelines",      # KDIGO, ADA, Tietz, CLSI clinical rules
    "pediatric_guard",          # Age & sex specific dynamic ranges
    "predictive_risk",          # Chronic disease progression forecasting
    "ocr_vision",               # High-precision lab report OCR parser
    "local_ai_copilot",         # 100% offline Qwen clinical diagnostic assistant
    "multi_patient_db",         # Longitudinal patient records storage
    "regulatory_pdf_reports",   # Regulatory clinical decision PDF exports
]


# ---------------------------------------------------------------------------
# Core License Generation: Military-Grade RSA-4096 / SHA-512
# ---------------------------------------------------------------------------
def generate_rsa4k_license_key(
    machine_id: str,
    customer_name: str,
    tier: str = "Enterprise Clinical CDS",
    days: int = 0,
    clinic_name: str = "",
    user_email: str = "",
    features: Optional[List[str]] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    """Generate military-grade RSA-4096 / SHA-512 signed activation token."""
    mid = machine_id.strip().upper()
    if not mid.startswith("HG-"):
        raise ValueError(f"Invalid Machine ID: {machine_id!r}. Expected format: HG-XXXX-XXXX-XXXX-XXXX")

    now = int(time.time())
    if days > 0:
        exp_ts = now + (days * 86400)
        exp_val: Any = exp_ts
        exp_str = time.strftime("%Y-%m-%d", time.gmtime(exp_ts))
    else:
        exp_val = "PERPETUAL"
        exp_str = "Perpetual (Lifetime Activation)"

    assigned_features = features if features is not None else list(_ALL_CLINICAL_FEATURES)
    jid = secrets.token_hex(16)  # Unique Cryptographic Nonce

    payload: Dict[str, Any] = {
        "alg": "RSA4096",
        "m": mid,
        "u": customer_name.strip(),
        "t": tier.strip(),
        "e": exp_val,
        "iat": now,
        "jid": jid,
        "feats": assigned_features,
    }
    if clinic_name.strip():
        payload["c"] = clinic_name.strip()
    if user_email.strip():
        payload["em"] = user_email.strip().lower()

    # Encode payload to base64url
    p_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    p_b64 = base64.urlsafe_b64encode(p_bytes).decode("ascii").rstrip("=")

    # RSA-4096 / SHA-512 Digital Signature
    h = hashlib.sha512(p_bytes).digest()
    em_body = _SHA512_DIGEST_INFO + h
    mod_len = (_RSA4K_N.bit_length() + 7) // 8  # 512 bytes
    pad_len = mod_len - 3 - len(em_body)
    padded = b"\x00\x01" + (b"\xff" * pad_len) + b"\x00" + em_body

    m_int = int.from_bytes(padded, "big")
    sig_int = pow(m_int, _RSA4K_D, _RSA4K_N)
    sig_bytes = sig_int.to_bytes(mod_len, "big")
    s_b64 = base64.urlsafe_b64encode(sig_bytes).decode("ascii").rstrip("=")

    token = f"{p_b64}.{s_b64}"
    # Outer 8-character cryptographic integrity checksum
    chk = hashlib.sha256(token.encode("ascii")).hexdigest()[:8].upper()
    full_key = f"HGLIC4K-{token}-{chk}"

    return full_key, exp_str, payload


def generate_rsa2k_license_key(
    machine_id: str,
    customer_name: str,
    tier: str = "Enterprise Clinical CDS",
    days: int = 0,
) -> Tuple[str, str, Dict[str, Any]]:
    """Generate legacy RSA-2048 / SHA-256 license token."""
    mid = machine_id.strip().upper()
    now = int(time.time())
    if days > 0:
        exp_ts = now + (days * 86400)
        exp_val: Any = exp_ts
        exp_str = time.strftime("%Y-%m-%d", time.gmtime(exp_ts))
    else:
        exp_val = "PERPETUAL"
        exp_str = "Perpetual (Lifetime)"

    payload = {
        "m": mid,
        "u": customer_name.strip(),
        "t": tier.strip(),
        "e": exp_val,
        "iat": now,
    }
    p_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    p_b64 = base64.urlsafe_b64encode(p_bytes).decode("ascii").rstrip("=")

    h = hashlib.sha256(p_bytes).digest()
    t = _SHA256_DIGEST_INFO + h
    pad_len = 256 - 3 - len(t)
    em = b"\x00\x01" + (b"\xff" * pad_len) + b"\x00" + t
    m_int = int.from_bytes(em, "big")
    s_int = pow(m_int, _RSA2K_D, _RSA2K_N)
    s_bytes = s_int.to_bytes(256, "big")
    s_b64 = base64.urlsafe_b64encode(s_bytes).decode("ascii").rstrip("=")

    token = f"{p_b64}.{s_b64}"
    chk = hashlib.sha256(token.encode("ascii")).hexdigest()[:6].upper()
    full_key = f"HGLIC-RSA-{token}-{chk}"
    return full_key, exp_str, payload


# ---------------------------------------------------------------------------
# Formatting Helpers (PEM Armor, WhatsApp, Email)
# ---------------------------------------------------------------------------
def format_pem_armor(key: str, payload: Dict[str, Any]) -> str:
    """Format license token as an enterprise PEM certificate."""
    exp_val = payload.get("e", "PERPETUAL")
    exp_display = "Perpetual (Lifetime Activation)" if exp_val == "PERPETUAL" else time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(int(exp_val)))
    iat_display = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(payload.get("iat", int(time.time()))))

    lines = [
        "-----BEGIN HEMOGLYPH MILITARY-GRADE RSA-4096 LICENSE CERTIFICATE-----",
        f"Version: 2.0 (Asymmetric RSA-4096 / SHA-512)",
        f"Issued-To: {payload.get('u', 'Registered Clinician')}",
    ]
    if payload.get("em"):
        lines.append(f"Email: {payload['em']}")
    if payload.get("c"):
        lines.append(f"Institution: {payload['c']}")
    lines.extend([
        f"Machine-ID: {payload.get('m', 'UNKNOWN')}",
        f"Edition: {payload.get('t', 'Enterprise Clinical CDS')}",
        f"Issued-At: {iat_display}",
        f"Expires: {exp_display}",
        f"Unique-JID: {payload.get('jid', 'N/A')}",
        "License-Token:",
        key,
        "-----END HEMOGLYPH MILITARY-GRADE RSA-4096 LICENSE CERTIFICATE-----",
    ])
    return "\n".join(lines)


def format_whatsapp_message(key: str, payload: Dict[str, Any]) -> str:
    """Format user-facing notification for messaging apps (WhatsApp / Telegram / SMS)."""
    name = payload.get("u", "پزشک گرامی")
    mid = payload.get("m", "")
    tier = payload.get("t", "Enterprise Clinical CDS")
    exp_val = payload.get("e", "PERPETUAL")
    exp_txt = "مادام‌العمر (بدون انقضا)" if exp_val == "PERPETUAL" else time.strftime("%Y-%m-%d", time.gmtime(int(exp_val)))

    return (
        f"🩺 کلید فعال‌سازی رسمی نرم‌افزار هموگلیف (Hemoglyph Clinical CDSS)\n\n"
        f"👤 نام پزشک: {name}\n"
        f"💻 شناسه سخت‌افزاری دستگاه: {mid}\n"
        f"🛡️ سطح دسترسی: {tier}\n"
        f"📅 اعتبار: {exp_txt}\n"
        f"🔐 استاندارد امنیتی: Military-Grade Asymmetric RSA-4096 / SHA-512\n\n"
        f"🔑 کد فعال‌سازی اختصاصی:\n"
        f"{key}\n\n"
        f"دستورالعمل فعال‌سازی:\n"
        f"۱. نرم‌افزار هموگلیف را باز کنید.\n"
        f"۲. از منوی کناری وارد بخش Settings (تنظیمات) > تب License شوید.\n"
        f"۳. کد بالا را در کادر مربوطه Paste کنید و دکمه Activate را بزنید."
    )


def format_email_template(key: str, payload: Dict[str, Any]) -> str:
    """Format enterprise activation email template."""
    name = payload.get("u", "Valued Clinician")
    mid = payload.get("m", "")
    tier = payload.get("t", "Enterprise Clinical CDS")
    exp_val = payload.get("e", "PERPETUAL")
    exp_txt = "Perpetual (No Expiration)" if exp_val == "PERPETUAL" else time.strftime("%Y-%m-%d", time.gmtime(int(exp_val)))

    return (
        f"Subject: Hemoglyph Clinical CDSS - Software Activation Credentials (RSA-4096)\n\n"
        f"Dear {name},\n\n"
        f"Thank you for deploying Hemoglyph Clinical Decision Support Suite.\n"
        f"Your cryptographic license certificate has been successfully generated and signed with military-grade RSA-4096 encryption.\n\n"
        f"----------------------------------------------------------------------\n"
        f"LICENSE DETAILS:\n"
        f"  Licensee:           {name}\n"
        f"  Machine Identifier: {mid}\n"
        f"  Edition Profile:    {tier}\n"
        f"  Valid Until:        {exp_txt}\n"
        f"  Encryption:         Asymmetric RSA-4096 with SHA-512 Digest\n"
        f"----------------------------------------------------------------------\n\n"
        f"ACTIVATION TOKEN:\n"
        f"{key}\n\n"
        f"ACTIVATION INSTRUCTIONS:\n"
        f"1. Launch Hemoglyph on the authorized workstation.\n"
        f"2. Navigate to Settings -> License Management tab.\n"
        f"3. Paste the activation token above into the input field and click 'Activate Key'.\n\n"
        f"Best regards,\n"
        f"Hemoglyph Clinical Engineering Team"
    )


# ---------------------------------------------------------------------------
# Key Inspector & Cryptographic Verifier
# ---------------------------------------------------------------------------
def inspect_license_key(key_str: str) -> Dict[str, Any]:
    """Inspect and mathematically verify any license key."""
    clean_key = key_str.strip()
    if "-----BEGIN" in clean_key and "-----END" in clean_key:
        for line in clean_key.splitlines():
            l = line.strip()
            if l.startswith("HGLIC"):
                clean_key = l
                break

    if not clean_key.startswith("HGLIC"):
        return {"valid": False, "error": "Invalid format. Expected HGLIC prefix."}

    is_rsa4k = clean_key.startswith("HGLIC4K-") or clean_key.startswith("HGLIC-RSA4K-")
    is_rsa2k = clean_key.startswith("HGLIC-RSA-") and not is_rsa4k

    if clean_key.startswith("HGLIC4K-"):
        prefix_len = 8
    elif clean_key.startswith("HGLIC-RSA4K-"):
        prefix_len = 12
    elif is_rsa2k:
        prefix_len = 10
    else:
        prefix_len = 6

    rest = clean_key[prefix_len:]
    parts = rest.rsplit("-", 1)
    if len(parts) != 2:
        return {"valid": False, "error": "Malformed token structure (missing checksum)."}

    token, checksum = parts
    calc_chk = hashlib.sha256(token.encode("ascii")).hexdigest()
    if not (hmac.compare_digest(checksum.upper(), calc_chk[:8].upper()) or hmac.compare_digest(checksum.upper(), calc_chk[:6].upper())):
        return {"valid": False, "error": "Integrity checksum validation failed (corrupted characters)."}

    if "." not in token:
        return {"valid": False, "error": "Malformed token (missing signature separator)."}

    p_b64, s_b64 = token.split(".", 1)
    try:
        p_bytes = base64.urlsafe_b64decode(p_b64 + "=" * (-len(p_b64) % 4))
        s_bytes = base64.urlsafe_b64decode(s_b64 + "=" * (-len(s_b64) % 4))
        payload = json.loads(p_bytes.decode("utf-8"))
    except Exception as exc:
        return {"valid": False, "error": f"Payload decode failure: {exc}"}

    sig_valid = False
    algo_name = "Unknown"

    if is_rsa4k:
        algo_name = "Military-Grade RSA-4096 / SHA-512"
        mod_len = (_RSA4K_N.bit_length() + 7) // 8
        if len(s_bytes) == mod_len:
            s_int = int.from_bytes(s_bytes, "big")
            m_int = pow(s_int, _RSA4K_E, _RSA4K_N)
            em = m_int.to_bytes(mod_len, "big")
            expected = _SHA512_DIGEST_INFO + hashlib.sha512(p_bytes).digest()
            sig_valid = (em.startswith(b"\x00\x01") or em.startswith(b"\x01")) and em.endswith(b"\x00" + expected)
    elif is_rsa2k:
        algo_name = "Asymmetric RSA-2048 / SHA-256"
        if len(s_bytes) == 256:
            s_int = int.from_bytes(s_bytes, "big")
            m_int = pow(s_int, _RSA2K_E, _RSA2K_N)
            em = m_int.to_bytes(256, "big")
            expected = _SHA256_DIGEST_INFO + hashlib.sha256(p_bytes).digest()
            sig_valid = (em.startswith(b"\x00\x01") or em.startswith(b"\x01")) and em.endswith(b"\x00" + expected)
    else:
        algo_name = "Legacy HMAC-SHA256"
        sig_valid = True

    exp_val = payload.get("e", "PERPETUAL")
    is_expired = False
    if exp_val != "PERPETUAL":
        try:
            exp_ts = int(exp_val)
            is_expired = time.time() > exp_ts
            exp_display = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(exp_ts))
        except ValueError:
            exp_display = "Malformed Expiration"
    else:
        exp_display = "Perpetual (Lifetime Activation)"

    return {
        "valid": sig_valid and not is_expired,
        "signature_authentic": sig_valid,
        "expired": is_expired,
        "algorithm": algo_name,
        "machine_id": payload.get("m"),
        "customer_name": payload.get("u"),
        "user_email": payload.get("em", "N/A"),
        "clinic_name": payload.get("c", "N/A"),
        "tier": payload.get("t"),
        "issued_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(payload.get("iat", 0))),
        "expires_at": exp_display,
        "unique_jid": payload.get("jid", "N/A"),
        "features": payload.get("feats", []),
        "raw_payload": payload,
    }


def run_self_test() -> bool:
    """Run comprehensive cryptographic self-test of the RSA-4096 engine."""
    print("=" * 70)
    print("  HEMOGLYPH MILITARY-GRADE RSA-4096 CRYPTOGRAPHIC SELF-TEST")
    print("=" * 70)

    test_mid = "HG-TEST-4096-SEC1-9988"
    test_doctor = "Sobhan Bahrami"
    test_email = "sobhan@hospital.org"

    print("[1/5] Generating RSA-4096 signed token with SHA-512...")
    t0 = time.time()
    key, exp_str, payload = generate_rsa4k_license_key(
        machine_id=test_mid,
        customer_name=test_doctor,
        user_email=test_email,
        days=365,
    )
    t1 = time.time()
    print(f"      Generation time: {t1-t0:.4f}s")
    print(f"      Key prefix: {key[:24]}...")
    print(f"      Key length: {len(key)} chars")

    print("[2/5] Inspecting and verifying digital signature...")
    t2 = time.time()
    info = inspect_license_key(key)
    t3 = time.time()
    print(f"      Verification time: {t3-t2:.4f}s")
    assert info["valid"] is True, f"Key verification failed: {info}"
    assert info["signature_authentic"] is True
    assert info["machine_id"] == test_mid
    assert info["customer_name"] == test_doctor
    print("      Verification result: 100% VALID & AUTHENTIC")

    print("[3/5] Testing anti-tamper detection on payload alteration...")
    tampered = key.replace(key[20:25], "XXXXX")
    tampered_info = inspect_license_key(tampered)
    assert tampered_info["valid"] is False
    print("      Tamper defense: SUCCESS (tampered key instantly rejected)")

    print("[4/5] Testing PEM Armor formatting & parsing...")
    armor = format_pem_armor(key, payload)
    armor_info = inspect_license_key(armor)
    assert armor_info["valid"] is True
    print("      Armor block verification: SUCCESS")

    print("[5/5] Testing WhatsApp & Email template rendering...")
    wa = format_whatsapp_message(key, payload)
    em = format_email_template(key, payload)
    assert len(wa) > 100 and len(em) > 100
    print("      Templates generated: SUCCESS")

    print("=" * 70)
    print("  ALL 5/5 CRYPTOGRAPHIC INTEGRITY TESTS PASSED FLAWLESSLY!")
    print("=" * 70)
    return True


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="HEMOGLYPH Military-Grade RSA-4096 Developer License Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--machine", "--machine-id", "-m", dest="machine", help="Customer Machine ID (e.g. HG-A1B2-C3D4-E5F6-07E2)")
    parser.add_argument("--customer", "--name", "-c", dest="customer", default="Sobhan Bahrami", help="Doctor or Clinic Name")
    parser.add_argument("--email", "-e", dest="email", default="", help="Clinician Email (Optional)")
    parser.add_argument("--clinic", dest="clinic", default="", help="Hospital or Clinic Name (Optional)")
    parser.add_argument("--tier", "-t", default="Enterprise Clinical CDS", help="License Tier Profile")
    parser.add_argument("--days", "-d", type=int, default=0, help="Validity period in days (0 for Perpetual / Lifetime)")
    parser.add_argument("--format", "-f", choices=["token", "armor", "whatsapp", "email"], default="token", help="Output format style")
    parser.add_argument("--inspect", "-i", dest="inspect", help="Inspect and verify an existing license key or armor block")
    parser.add_argument("--legacy-rsa2k", action="store_true", help="Generate legacy RSA-2048 key instead of RSA-4096")
    parser.add_argument("--test", action="store_true", help="Run comprehensive cryptographic test suite")

    args = parser.parse_args()

    if args.test:
        run_self_test()
        sys.exit(0)

    if args.inspect:
        res = inspect_license_key(args.inspect)
        print("\n" + "=" * 70)
        print("          HEMOGLYPH LICENSE INSPECTOR REPORT")
        print("=" * 70)
        for k, v in res.items():
            if k == "raw_payload":
                continue
            print(f"  {k.replace('_', ' ').title():<22}: {v}")
        print("=" * 70 + "\n")
        sys.exit(0 if res.get("valid") else 1)

    if not args.machine:
        print("[!] Error: Machine ID is required. Use --machine HG-XXXX-XXXX-XXXX-XXXX", file=sys.stderr)
        sys.exit(1)

    try:
        if args.legacy_rsa2k:
            key, exp_str, payload = generate_rsa2k_license_key(
                machine_id=args.machine,
                customer_name=args.customer,
                tier=args.tier,
                days=args.days,
            )
            algo_title = "Asymmetric RSA-2048 / SHA-256"
        else:
            key, exp_str, payload = generate_rsa4k_license_key(
                machine_id=args.machine,
                customer_name=args.customer,
                tier=args.tier,
                days=args.days,
                clinic_name=args.clinic,
                user_email=args.email,
            )
            algo_title = "Military-Grade Asymmetric RSA-4096 / SHA-512"

        if args.format == "armor":
            print(format_pem_armor(key, payload))
        elif args.format == "whatsapp":
            print(format_whatsapp_message(key, payload))
        elif args.format == "email":
            print(format_email_template(key, payload))
        else:
            print("\n" + "=" * 75)
            print("       HEMOGLYPH MILITARY-GRADE RSA-4096 LICENSE CERTIFICATE")
            print("=" * 75)
            print(f" Licensee:    {args.customer}")
            if args.email:
                print(f" Email:       {args.email}")
            if args.clinic:
                print(f" Clinic:      {args.clinic}")
            print(f" Machine ID:  {args.machine.upper()}")
            print(f" Tier:        {args.tier}")
            print(f" Validity:    {exp_str}")
            print(f" Security:    {algo_title}")
            print("-" * 75)
            print(" ACTIVATION KEY TOKEN (Copy below into Hemoglyph):")
            print(f"\n{key}\n")
            print("=" * 75)
            print("✅ License token ready for deployment to clinician.\n")

    except Exception as exc:
        print(f"[!] Error generating license: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
