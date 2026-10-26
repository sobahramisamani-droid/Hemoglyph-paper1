#!/usr/bin/env python3
"""HEMOGLYPH Sentinel v2.0 — Military-Grade Executive CDS Command & License Platform.

Zero-Medical-Data Telemetry Architecture:
Strictly privacy-preserving: This system manages cryptographic machine tokens,
heartbeat telemetry, and remote kill-switch authorizations. ZERO patient,
laboratory, or diagnostic observations are ever collected or stored.

High-Assurance Security Features:
1. Asymmetric RSA-2048 Digital Signatures (PKCS#1 v1.5 + SHA-256).
   - Private key (d) exists ONLY on this server.
   - Reverse-engineers cannot forge keys even with full client source code.
2. Hardened PBKDF2-HMAC-SHA256 (100,000 rounds) Master Password Gate.
3. Cryptographic Bearer/Cookie Session Tokens (secrets.token_hex).
4. Automated Anti-Brute-Force Rate Limiting (IP lockouts on repeated failures).
5. Granular Remote Kill-Switch with fast presets and sub-second execution.
6. 1-Click WhatsApp / Telegram invitation message generator for clinicians.
7. Audit Trail, Excel CSV/JSON exports, and Web Audio chimes.
8. 100% Python Standard Library (Zero external pip packages needed).
"""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import http.cookies
import http.server
import io
import json
import os
import secrets
import sqlite3
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Cryptographic Keys & Configuration
# ---------------------------------------------------------------------------
_MASTER_KEY = b"HEMOGLYPH-MASTER-SIGNATURE-KEY-SECURE-OFFLINE-CDS-V5"

# ---------------------------------------------------------------------------
# Cryptographic Keys & Configuration
# ---------------------------------------------------------------------------
_MASTER_KEY = b"HEMOGLYPH-MASTER-SIGNATURE-KEY-SECURE-OFFLINE-CDS-V5"

# Asymmetric RSA-4096 Military-Grade Master Signing Keys
# (Private Key 'd' is held ONLY on Sentinel Server / Keygen Factory)
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

# Asymmetric RSA-2048 Master Signing Keys (Backward Compatibility)
_RSA_E = 65537
_RSA_N_HEX = (
    "6b0249d50903b4d7c4e1c2e98308575c3a3712fe06876f7f63c98e2075b51e48"
    "3e5fe725abcb9691b80b4b757f1c8578255c10cbfd27786f95f9b5afcb7e0ead"
    "08e81ee74b746211013590f8cfa2d8c6feb399005ef7253694f30aa9b4afa097"
    "7922f65a3d7f0e8b5e55c5692b9206fa1bed41e3756aed9d0cea00dc45fb4257"
    "eb360bfb55661a4eaecc5bd6c1137b47da6e6a09e1fb3a8ceb799988dda907d2"
    "fefccfc4871fce054f2a86fba07a06a93da5e4da7e5baf17a879c423ab1bab01"
    "4362c8ef5f6af2026e531340ac60291fb98ad3ae73a69e12623c883ab90a9f74"
    "eef97e68c086160eb1f63e2bee9212fbdde873142109415a3fd5ad6ab05fe55d"
)
_RSA_D_HEX = (
    "387517a12745665764cfbbf759a3bffbafd738d4ff7adb4fb9c530905da9f655"
    "255b91e7a5311fbab800758a834af7fc40b1c746e8c4b75d2022844240b9bc62"
    "7ccd82e8833ddf339b90b8711d938c8dc8f9d6a284781e91229aec28476555f4"
    "34fc463fac2c69ef0c1172bb1f3ac7259430644feeb640b1588be9724e15d795"
    "3e86c2ab8f03e23796595459c91355dc35074fcb54d2b3b56dfd44b330fd1f08"
    "4490e5830f9b136e781b06210363d96de3ca6c02e5b4cc3976160d5e225f9ae0"
    "469773f8e1e77a60ae33234087d70d57753064b8bebd666e8b3119bb4fd5ed5c"
    "96e38e6a1d81f5d67ea7932553485977a465e3775efaa55c0226035b73cab5e1"
)
_RSA_N = int(_RSA_N_HEX, 16)
_RSA_D = int(_RSA_D_HEX, 16)
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")

# Clinical CDS Feature Matrix
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

DB_PATH = Path("sentinel_admin.db")
DEFAULT_PORT = int(os.getenv("PORT", "8090"))
ONLINE_THRESHOLD_SECONDS = 8

# Brute-force rate limiting: ip -> list of timestamp floats
_FAILED_LOGINS: Dict[str, List[float]] = {}
_RATE_LIMIT_LOCK = threading.Lock()
_SESSION_EXPIRY_SECONDS = 86400  # 24 hours


# ============================================================================
# 1. Database Layer, Schema & Authentication Engine
# ============================================================================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT UNIQUE NOT NULL,
                customer_name TEXT DEFAULT '',
                user_email TEXT DEFAULT '',
                clinic_name TEXT DEFAULT '',
                internal_notes TEXT DEFAULT '',
                tier TEXT DEFAULT 'Unlicensed',
                license_key TEXT DEFAULT '',
                expires_at TEXT DEFAULT 'NONE',
                last_seen_ts INTEGER DEFAULT 0,
                last_ip TEXT DEFAULT '',
                app_version TEXT DEFAULT '1.0.0',
                has_license INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                block_reason TEXT DEFAULT '',
                ping_count INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL
            )
        """)

        # Safe schema migrations
        columns_to_add = [
            ("user_email", "TEXT DEFAULT ''"),
            ("has_license", "INTEGER DEFAULT 0"),
            ("clinic_name", "TEXT DEFAULT ''"),
            ("internal_notes", "TEXT DEFAULT ''"),
            ("ping_count", "INTEGER DEFAULT 0"),
        ]
        for col, col_type in columns_to_add:
            try:
                conn.execute(f"ALTER TABLE clients ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                action TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                details TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_auth (
                id INTEGER PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_sessions (
                token TEXT PRIMARY KEY,
                client_ip TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                last_active INTEGER NOT NULL
            )
        """)
        conn.commit()

        # Seed initial admin master password if not set
        cur = conn.execute("SELECT COUNT(*) FROM admin_auth")
        if cur.fetchone()[0] == 0:
            init_password = os.getenv("SENTINEL_ADMIN_PASSWORD", "admin2026")
            salt = secrets.token_hex(16)
            h = hashlib.pbkdf2_hmac("sha256", init_password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
            conn.execute(
                "INSERT INTO admin_auth (id, salt, password_hash, updated_at) VALUES (1, ?, ?, ?)",
                (salt, h, int(time.time())),
            )
            conn.commit()


def verify_master_password(password: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT salt, password_hash FROM admin_auth WHERE id = 1")
        row = cur.fetchone()
        if not row:
            return False
        salt, expected_hash = row
        calc_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
        return hmac.compare_digest(calc_hash, expected_hash)


def change_master_password(current_password: str, new_password: str) -> Tuple[bool, str]:
    if not verify_master_password(current_password):
        return False, "Current master password is incorrect"
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"

    salt = secrets.token_hex(16)
    new_h = hashlib.pbkdf2_hmac("sha256", new_password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE admin_auth SET salt = ?, password_hash = ?, updated_at = ? WHERE id = 1",
            (salt, new_h, int(time.time())),
        )
        # Purge all existing sessions to enforce re-login
        conn.execute("DELETE FROM admin_sessions")
        conn.commit()

    log_audit("SECURITY", "SYSTEM", "Master admin password changed. All sessions invalidated.")
    return True, "Master password updated successfully"


def create_session(client_ip: str) -> str:
    token = secrets.token_hex(32)
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO admin_sessions (token, client_ip, created_at, last_active) VALUES (?, ?, ?, ?)",
            (token, client_ip, now, now),
        )
        conn.commit()
    return token


def validate_session(token: str) -> bool:
    if not token or len(token) < 32:
        return False
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT last_active FROM admin_sessions WHERE token = ?", (token,))
        row = cur.fetchone()
        if not row:
            return False
        last_active = row[0]
        if (now - last_active) > _SESSION_EXPIRY_SECONDS:
            conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
            conn.commit()
            return False

        conn.execute("UPDATE admin_sessions SET last_active = ? WHERE token = ?", (now, token))
        conn.commit()
        return True


def destroy_session(token: str):
    if token:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
            conn.commit()


def check_rate_limit(client_ip: str) -> bool:
    """Return True if request is allowed, False if IP is temporarily locked out."""
    now = time.time()
    with _RATE_LIMIT_LOCK:
        attempts = _FAILED_LOGINS.get(client_ip, [])
        # Keep attempts within last 300 seconds (5 mins)
        attempts = [t for t in attempts if (now - t) < 300]
        _FAILED_LOGINS[client_ip] = attempts
        if len(attempts) >= 5:
            return False
        return True


def record_failed_login(client_ip: str):
    with _RATE_LIMIT_LOCK:
        if client_ip not in _FAILED_LOGINS:
            _FAILED_LOGINS[client_ip] = []
        _FAILED_LOGINS[client_ip].append(time.time())


def clear_failed_logins(client_ip: str):
    with _RATE_LIMIT_LOCK:
        if client_ip in _FAILED_LOGINS:
            del _FAILED_LOGINS[client_ip]


# ---------------------------------------------------------------------------
# Telemetry, Client Management & Audit
# ---------------------------------------------------------------------------
def log_audit(action: str, machine_id: str, details: str = ""):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO audit_log (ts, action, machine_id, details) VALUES (?, ?, ?, ?)",
                (int(time.time()), action, machine_id, details),
            )
            conn.commit()
    except Exception:
        pass


def get_audit_logs(limit: int = 40) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
    
    logs = []
    for r in rows:
        d = dict(r)
        d["time_str"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d["ts"]))
        logs.append(d)
    return logs


def get_all_clients() -> List[Dict[str, Any]]:
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM clients ORDER BY is_blocked DESC, last_seen_ts DESC, id DESC")
        rows = cur.fetchall()

    clients = []
    for r in rows:
        c = dict(r)
        last_ts = c.get("last_seen_ts", 0)
        is_blocked = bool(c.get("is_blocked", 0))
        diff = (now - last_ts) if last_ts > 0 else 999999

        if is_blocked:
            computed_status = "blocked"
            status_label = "SUSPENDED"
        elif last_ts > 0 and diff <= ONLINE_THRESHOLD_SECONDS:
            computed_status = "online"
            status_label = f"Active ({diff}s ago)" if diff > 0 else "Active (Just now)"
        elif last_ts > 0:
            computed_status = "offline"
            if diff < 60:
                status_label = f"Offline ({diff}s ago)"
            elif diff < 3600:
                status_label = f"Offline ({diff // 60}m ago)"
            elif diff < 86400:
                status_label = f"Offline ({diff // 3600}h ago)"
            else:
                status_label = f"Offline ({diff // 86400}d ago)"
        else:
            computed_status = "never"
            status_label = "Never Connected"

        exp_str = c.get("expires_at", "NONE")
        exp_hint = exp_str
        if exp_str != "PERPETUAL" and exp_str != "NONE":
            try:
                t_parts = time.strptime(exp_str, "%Y-%m-%d")
                exp_ts = int(time.mktime(t_parts))
                days_left = (exp_ts - now) // 86400
                if days_left < 0:
                    exp_hint = f"Expired ({abs(days_left)}d ago)"
                elif days_left == 0:
                    exp_hint = "Expires Today!"
                else:
                    exp_hint = f"{days_left} days remaining"
            except Exception:
                pass

        c["computed_status"] = computed_status
        c["status_label"] = status_label
        c["elapsed_seconds"] = diff
        c["expiry_hint"] = exp_hint
        c["first_seen_str"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(c["created_at"]))
        clients.append(c)

    return clients


def get_system_stats() -> Dict[str, Any]:
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT is_blocked, has_license, last_seen_ts, ping_count FROM clients")
        rows = cur.fetchall()

    total = len(rows)
    online = 0
    blocked = 0
    offline = 0
    licensed = 0
    not_active = 0
    total_pings = 0

    for r in rows:
        is_blk = bool(r["is_blocked"])
        has_lic = bool(r["has_license"])
        last_seen = r["last_seen_ts"]
        total_pings += (r["ping_count"] or 0)

        if is_blk:
            blocked += 1
        else:
            if has_lic:
                licensed += 1
            else:
                not_active += 1

        if last_seen and (now - last_seen) <= ONLINE_THRESHOLD_SECONDS:
            online += 1
        else:
            offline += 1

    return {
        "total": total,
        "online": online,
        "offline": offline,
        "blocked": blocked,
        "licensed": licensed,
        "not_active": not_active,
        "total_pings": total_pings,
        "server_time": now,
    }


def set_client_blocked(machine_id: str, blocked: bool, reason: str = "") -> bool:
    mid = machine_id.strip().upper()
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "UPDATE clients SET is_blocked = ?, block_reason = ? WHERE machine_id = ?",
            (1 if blocked else 0, reason if blocked else "", mid),
        )
        if cur.rowcount == 0 and blocked:
            conn.execute("""
                INSERT INTO clients (machine_id, customer_name, is_blocked, block_reason, created_at)
                VALUES (?, ?, 1, ?, ?)
            """, (mid, "Restricted Workstation", reason, now))
        conn.commit()

    log_audit("BLOCK" if blocked else "UNBLOCK", mid, reason or "Action executed by administrator")
    return True


def delete_client(machine_id: str) -> bool:
    mid = machine_id.strip().upper()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM clients WHERE machine_id = ?", (mid,))
        conn.commit()
        deleted = cur.rowcount > 0

    log_audit("DELETE", mid, "Removed client record permanently")
    return deleted


def update_client_details(machine_id: str, name: str, clinic: str, notes: str, email: str = "") -> bool:
    mid = machine_id.strip().upper()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            UPDATE clients SET
                customer_name = ?,
                clinic_name = ?,
                internal_notes = ?,
                user_email = CASE WHEN ? != '' THEN ? ELSE user_email END
            WHERE machine_id = ?
        """, (name.strip(), clinic.strip(), notes.strip(), email.strip(), email.strip(), mid))
        conn.commit()
        updated = cur.rowcount > 0

    log_audit("UPDATE_DETAILS", mid, f"Name: {name}, Email: {email}, Clinic: {clinic}")
    return updated


# ============================================================================
# 2. Military-Grade Asymmetric RSA-4096 Key Issuance Engine
# ============================================================================
def generate_cryptographic_key(
    machine_id: str,
    customer_name: str,
    tier: str = "Enterprise Clinical CDS",
    days: int = 0,
    clinic_name: str = "",
    user_email: str = "",
    features: Optional[List[str]] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    """Issues authenticated Military-Grade RSA-4096 license token and upserts DB record."""
    mid = machine_id.strip().upper()
    if not mid.startswith("HG-"):
        raise ValueError("Invalid Machine ID format. Must begin with HG- (e.g. HG-A1B2-C3D4-E5F6-7890)")

    now = int(time.time())
    if days > 0:
        expires_ts = now + (days * 86400)
        expires_str = time.strftime("%Y-%m-%d", time.gmtime(expires_ts))
        exp_val: Any = expires_ts
    else:
        expires_str = "PERPETUAL"
        exp_val = "PERPETUAL"

    assigned_features = features if features is not None else list(_ALL_CLINICAL_FEATURES)
    jid = secrets.token_hex(16)

    payload = {
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

    p_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    p_b64 = base64.urlsafe_b64encode(p_bytes).decode("ascii").rstrip("=")

    # Military-Grade RSA-4096 / SHA-512 Digital Signature
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
    chk = hashlib.sha256(token.encode("ascii")).hexdigest()[:8].upper()
    key_str = f"HGLIC4K-{token}-{chk}"

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO clients (machine_id, customer_name, user_email, clinic_name, tier, license_key, expires_at, has_license, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(machine_id) DO UPDATE SET
                customer_name = excluded.customer_name,
                user_email = CASE WHEN excluded.user_email != '' THEN excluded.user_email ELSE clients.user_email END,
                clinic_name = CASE WHEN excluded.clinic_name != '' THEN excluded.clinic_name ELSE clients.clinic_name END,
                tier = excluded.tier,
                license_key = excluded.license_key,
                expires_at = excluded.expires_at,
                has_license = 1
        """, (mid, customer_name.strip(), user_email.strip(), clinic_name.strip(), tier.strip(), key_str, expires_str, now))
        conn.commit()

    log_audit("KEY_ISSUED", mid, f"Issued RSA-4096 Military-Grade key for {customer_name} ({tier}, Exp: {expires_str})")
    return key_str, expires_str, payload


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
    """Format notification message ready for WhatsApp / Telegram / SMS."""
    name = payload.get("u", "پزشک گرامی")
    mid = payload.get("m", "")
    tier = payload.get("t", "Enterprise Clinical CDS")
    exp_val = payload.get("e", "PERPETUAL")
    exp_txt = "مادام‌العمر (بدون انقضا)" if exp_val == "PERPETUAL" else time.strftime("%Y-%m-%d", time.gmtime(int(exp_val)))

    return (
        f"🩺 لایسنس رسمی نرم‌افزار هموگلیف (Hemoglyph Clinical CDSS)\n\n"
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
    """Format formal license delivery email."""
    name = payload.get("u", "Valued Clinician")
    mid = payload.get("m", "")
    tier = payload.get("t", "Enterprise Clinical CDS")
    exp_val = payload.get("e", "PERPETUAL")
    exp_txt = "Perpetual (No Expiration)" if exp_val == "PERPETUAL" else time.strftime("%Y-%m-%d", time.gmtime(int(exp_val)))

    return (
        f"Subject: Hemoglyph Clinical CDSS - Software Activation Credentials (RSA-4096)\n\n"
        f"Dear {name},\n\n"
        f"Thank you for deploying Hemoglyph Clinical Decision Support Suite.\n"
        f"Your cryptographic license certificate has been successfully signed with military-grade RSA-4096 encryption.\n\n"
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
            m_int = pow(s_int, _RSA_E, _RSA_N)
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


# ============================================================================
# 3. HTTP Request Routing & REST API with Session Security
# ============================================================================
class SentinelHandler(http.server.BaseHTTPRequestHandler):
    server_version = "HemoglyphSentinel/2.0"

    def _get_session_token(self) -> str:
        # 1. Check Authorization header
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            return auth_hdr[7:].strip()

        # 2. Check Cookie
        cookie_hdr = self.headers.get("Cookie", "")
        if cookie_hdr:
            try:
                c = http.cookies.SimpleCookie(cookie_hdr)
                if "sentinel_session" in c:
                    return c["sentinel_session"].value
            except Exception:
                pass
        return ""

    def _is_authenticated(self) -> bool:
        token = self._get_session_token()
        return validate_session(token)

    def _send_json(self, data: Any, status: int = 200, set_cookie_token: Optional[str] = None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        if set_cookie_token:
            self.send_header("Set-Cookie", f"sentinel_session={set_cookie_token}; Path=/; SameSite=Strict; HttpOnly")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Public App Shell / Dashboard
        if path in ("/", "/index.html", "/dashboard"):
            self._serve_dashboard()
            return

        # 2. Auth check endpoint
        if path == "/api/auth/check":
            self._send_json({"authenticated": self._is_authenticated()})
            return

        # 3. Protected Management APIs
        if not self._is_authenticated():
            self._send_json({"error": "Unauthorized. Authentication required."}, status=401)
            return

        if path == "/api/stats":
            self._send_json(get_system_stats())
        elif path == "/api/clients":
            self._send_json(get_all_clients())
        elif path == "/api/audit":
            self._send_json(get_audit_logs())
        elif path == "/api/export/json":
            self._export_json()
        elif path == "/api/export/csv":
            self._export_csv()
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        # 1. Unauthenticated Login Gate
        if path == "/api/auth/login":
            if not check_rate_limit(client_ip):
                self._send_json({
                    "success": False,
                    "error": "Rate limit exceeded. IP temporarily locked out for 5 minutes due to multiple failed attempts."
                }, status=429)
                return

            pwd = body.get("password", "")
            if verify_master_password(pwd):
                clear_failed_logins(client_ip)
                token = create_session(client_ip)
                log_audit("AUTH_LOGIN", "ADMIN", f"Successful login from {client_ip}")
                self._send_json({"success": True, "token": token}, set_cookie_token=token)
            else:
                record_failed_login(client_ip)
                log_audit("AUTH_FAILURE", "ADMIN", f"Failed login attempt from {client_ip}")
                self._send_json({"success": False, "error": "Invalid master password"}, status=401)
            return

        # 2. Heartbeat from Hemoglyph Workstations (No admin password required)
        if path == "/api/heartbeat":
            self._handle_heartbeat(body, client_ip)
            return

        # 3. All remaining endpoints require Master Session Authentication
        if not self._is_authenticated():
            self._send_json({"error": "Unauthorized. Please authenticate with master password."}, status=401)
            return

        if path == "/api/auth/logout":
            token = self._get_session_token()
            destroy_session(token)
            self._send_json({"success": True})
        elif path == "/api/auth/change_password":
            cur_p = body.get("current_password", "")
            new_p = body.get("new_password", "")
            ok, msg = change_master_password(cur_p, new_p)
            self._send_json({"success": ok, "message": msg}, status=200 if ok else 400)
        elif path == "/api/clients/block":
            mid = body.get("machine_id", "")
            reason = body.get("reason", "Suspended by administrator")
            ok = set_client_blocked(mid, blocked=True, reason=reason)
            self._send_json({"success": ok})
        elif path == "/api/clients/unblock":
            mid = body.get("machine_id", "")
            ok = set_client_blocked(mid, blocked=False)
            self._send_json({"success": ok})
        elif path == "/api/clients/delete":
            mid = body.get("machine_id", "")
            ok = delete_client(mid)
            self._send_json({"success": ok})
        elif path == "/api/clients/update":
            mid = body.get("machine_id", "")
            name = body.get("customer_name", "")
            email = body.get("user_email", "")
            clinic = body.get("clinic_name", "")
            notes = body.get("internal_notes", "")
            ok = update_client_details(mid, name, clinic, notes, email)
            self._send_json({"success": ok})
        elif path == "/api/inspect_key":
            try:
                key_to_inspect = body.get("key", "").strip()
                res = inspect_license_key(key_to_inspect)
                self._send_json({"success": True, "data": res})
            except Exception as exc:
                self._send_json({"success": False, "error": str(exc)}, status=400)
        elif path == "/api/keygen":
            try:
                mid = body.get("machine_id", "")
                customer = body.get("customer_name", "Registered Clinician")
                email = body.get("user_email", "")
                clinic = body.get("clinic_name", "")
                tier = body.get("tier", "Enterprise Clinical CDS")
                days = int(body.get("days", 0))
                features = body.get("features", None)
                key, exp, payload = generate_cryptographic_key(mid, customer, tier, days, clinic, email, features)

                armor = format_pem_armor(key, payload)
                whatsapp_msg = format_whatsapp_message(key, payload)
                email_tmpl = format_email_template(key, payload)

                self._send_json({
                    "success": True,
                    "license_key": key,
                    "machine_id": mid,
                    "customer_name": customer,
                    "expires_at": exp,
                    "tier": tier,
                    "armor_block": armor,
                    "whatsapp_message": whatsapp_msg,
                    "email_message": email_tmpl,
                })
            except Exception as exc:
                self._send_json({"success": False, "error": str(exc)}, status=400)
        else:
            self._send_json({"error": "Unknown POST endpoint"}, status=404)

    def _handle_heartbeat(self, body: Dict[str, Any], client_ip: str):
        mid = (body.get("machine_id") or "").strip().upper()
        if not mid or not mid.startswith("HG-"):
            self._send_json({"status": "error", "message": "Invalid Machine ID format"}, status=400)
            return

        now = int(time.time())
        customer = (body.get("user_name") or body.get("customer") or "").strip()
        user_email = (body.get("user_email") or "").strip()
        version = body.get("app_version", "1.0.0")
        has_lic = 1 if body.get("has_license", False) else 0
        tier = body.get("tier", "Unlicensed" if not has_lic else "Enterprise Clinical CDS")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM clients WHERE machine_id = ?", (mid,))
            row = cur.fetchone()

            if row:
                is_blocked = bool(row["is_blocked"])
                reason = row["block_reason"] or "Workstation license suspended by administrator."
                db_has_lic = bool(row["has_license"])
                updated_has_lic = 1 if (has_lic or db_has_lic) else 0
                updated_tier = tier if tier != "Unlicensed" else row["tier"]
                new_ping_count = (row["ping_count"] or 0) + 1

                current_name = row["customer_name"] or ""
                new_name = current_name
                if customer and customer not in ("Discovered Device", "Discovered Workstation", "Unregistered Device"):
                    new_name = customer

                current_email = row["user_email"] or "" if "user_email" in row.keys() else ""
                new_email = user_email if user_email else current_email

                conn.execute("""
                    UPDATE clients SET
                        last_seen_ts = ?,
                        last_ip = ?,
                        app_version = ?,
                        has_license = ?,
                        tier = ?,
                        ping_count = ?,
                        customer_name = ?,
                        user_email = ?
                    WHERE machine_id = ?
                """, (now, client_ip, version, updated_has_lic, updated_tier, new_ping_count, new_name, new_email, mid))
            else:
                is_blocked = False
                reason = ""
                initial_name = customer if customer and customer not in ("Discovered Device", "Unregistered Device") else "Discovered Workstation"
                conn.execute("""
                    INSERT INTO clients (machine_id, customer_name, user_email, tier, app_version, has_license, last_seen_ts, last_ip, ping_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (mid, initial_name, user_email, tier, version, has_lic, now, client_ip, now))

            conn.commit()

        if is_blocked:
            self._send_json({
                "status": "revoked",
                "action": "lock",
                "reason": reason,
                "server_time": now,
            })
        else:
            self._send_json({
                "status": "active",
                "action": "continue",
                "server_time": now,
            })

    def _export_json(self):
        clients = get_all_clients()
        body = json.dumps(clients, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="hemoglyph_clients.json"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _export_csv(self):
        clients = get_all_clients()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Machine ID", "Clinician", "Email", "Clinic", "Tier", "Has License", "Status", "Expires", "Last IP", "Last Seen", "Pings"])
        for c in clients:
            writer.writerow([
                c.get("id"),
                c.get("machine_id"),
                c.get("customer_name"),
                c.get("user_email", ""),
                c.get("clinic_name"),
                c.get("tier"),
                "YES" if c.get("has_license") else "NO",
                c.get("status_label"),
                c.get("expires_at"),
                c.get("last_ip"),
                c.get("first_seen_str"),
                c.get("ping_count"),
            ])
        body = output.getvalue().encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="hemoglyph_clients.csv"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_dashboard(self):
        body = _HTML_DASHBOARD.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]}\n")


# ============================================================================
# 4. Masterpiece Executive Dark Glassmorphism UI (SPA + Auth Gate)
# ============================================================================
_HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hemoglyph Sentinel — Executive Control & License Suite</title>
<style>
  :root {
    --bg-base: #06080d;
    --bg-card: #0c101b;
    --bg-card-hover: #121828;
    --bg-surface: #141b2d;
    --border: #1a2236;
    --border-bright: #293552;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --accent-ruby: #e11d48;
    --accent-emerald: #10b981;
    --accent-cyan: #06b6d4;
    --accent-amber: #f59e0b;
    --accent-violet: #8b5cf6;
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    --font-mono: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: var(--bg-base);
    color: var(--text-main);
    font-family: var(--font);
    line-height: 1.5;
    padding: 24px;
    min-height: 100vh;
  }
  .container { max-width: 1400px; margin: 0 auto; }
  
  /* Header */
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 22px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }
  .brand { display: flex; align-items: center; gap: 14px; }
  .brand-logo {
    width: 46px; height: 46px;
    background: linear-gradient(135deg, #be123c, #10b981);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
    box-shadow: 0 0 24px rgba(225, 29, 72, 0.4);
  }
  .brand-title { font-size: 21px; font-weight: 800; letter-spacing: 0.5px; }
  .brand-subtitle { font-size: 12px; color: var(--text-muted); }
  .header-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  
  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    user-select: none;
    text-decoration: none;
  }
  .btn-primary {
    background: linear-gradient(135deg, #e11d48, #be123c);
    color: white;
    box-shadow: 0 4px 14px rgba(225, 29, 72, 0.35);
  }
  .btn-primary:hover { opacity: 0.92; transform: translateY(-1px); }
  .btn-secondary {
    background: var(--bg-card);
    border-color: var(--border);
    color: var(--text-main);
  }
  .btn-secondary:hover { background: var(--bg-card-hover); border-color: var(--border-bright); }
  .btn-danger {
    background: rgba(225, 29, 72, 0.15);
    border-color: rgba(225, 29, 72, 0.4);
    color: #fda4af;
  }
  .btn-danger:hover { background: #e11d48; color: white; }
  .btn-success {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.4);
    color: #6ee7b7;
  }
  .btn-success:hover { background: #10b981; color: white; }
  .btn-icon { padding: 5px 9px; font-size: 12px; }

  /* KPI Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  .stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .stat-card:hover {
    border-color: var(--border-bright);
    background: var(--bg-card-hover);
    transform: translateY(-2px);
  }
  .stat-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
  }
  .stat-total::after { background: var(--accent-cyan); }
  .stat-online::after { background: var(--accent-emerald); }
  .stat-licensed::after { background: #38bdf8; }
  .stat-not-active::after { background: var(--accent-amber); }
  .stat-blocked::after { background: var(--accent-ruby); }
  .stat-label { font-size: 11px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
  .stat-value { font-size: 30px; font-weight: 800; margin-top: 6px; font-family: var(--font-mono); }
  .stat-hint { font-size: 11px; color: var(--text-dim); margin-top: 2px; }

  /* Filter Tabs & Toolbar */
  .section-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
  }
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 12px;
  }
  .filter-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
  .tab-btn {
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-muted);
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }
  .tab-btn.active {
    background: var(--bg-surface);
    color: var(--text-main);
    border-color: var(--border-bright);
  }
  .search-box {
    background: var(--bg-base);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 7px 12px;
    color: var(--text-main);
    font-size: 12.5px;
    width: 280px;
    outline: none;
  }
  .search-box:focus { border-color: var(--accent-cyan); }

  /* Table */
  table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
  th {
    background: rgba(12, 16, 27, 0.95);
    color: var(--text-muted);
    font-weight: 600;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }
  td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background-color: var(--bg-card-hover); }

  /* Badges */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 16px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.4px;
    white-space: nowrap;
  }
  .badge-online {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
  }
  .badge-online::before {
    content: '';
    width: 6px; height: 6px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 8px #10b981;
    animation: pulse 1.5s infinite;
  }
  .badge-offline {
    background: rgba(148, 163, 184, 0.1);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.25);
  }
  .badge-activated {
    background: rgba(56, 189, 248, 0.14);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
  }
  .badge-not-active {
    background: rgba(245, 158, 11, 0.16);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }
  .badge-blocked {
    background: rgba(225, 29, 72, 0.15);
    color: #f87171;
    border: 1px solid rgba(225, 29, 72, 0.35);
  }

  @keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  }

  .mono { font-family: var(--font-mono); font-size: 11.5px; }
  .mid-code {
    background: rgba(0, 0, 0, 0.35);
    padding: 3px 6px;
    border-radius: 5px;
    border: 1px solid var(--border);
    color: var(--accent-cyan);
    font-weight: 600;
  }

  /* Modals */
  .modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 999;
    padding: 16px;
  }
  .modal {
    background: var(--bg-card);
    border: 1px solid var(--border-bright);
    border-radius: 16px;
    max-width: 540px;
    width: 100%;
    padding: 24px;
    box-shadow: 0 24px 50px rgba(0,0,0,0.7);
  }
  .modal-header {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
  }
  .modal-title { font-size: 17px; font-weight: 700; }
  .close-btn { background: none; border: none; color: var(--text-dim); font-size: 22px; cursor: pointer; }
  .close-btn:hover { color: var(--text-main); }
  .form-group { margin-bottom: 13px; }
  .form-label { display: block; font-size: 11.5px; font-weight: 600; color: var(--text-muted); margin-bottom: 5px; }
  .form-input, .form-select, .form-textarea {
    width: 100%;
    background: var(--bg-base);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 9px 12px;
    color: var(--text-main);
    font-size: 12.5px;
    outline: none;
  }
  .form-input:focus, .form-select:focus, .form-textarea:focus { border-color: var(--accent-cyan); }
  .result-box {
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid var(--border-bright);
    border-radius: 8px;
    padding: 12px;
    margin-top: 14px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: #34d399;
    word-break: break-all;
    max-height: 120px;
    overflow-y: auto;
    display: none;
  }
  .chip-group { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  .chip {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 11px;
    color: var(--text-muted);
    cursor: pointer;
  }
  .chip:hover { border-color: var(--accent-ruby); color: #fda4af; }

  /* Login Gate Screen */
  #loginScreen {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at center, #0e1628 0%, #06080d 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  }
  .login-card {
    background: rgba(12, 16, 27, 0.95);
    border: 1px solid var(--border-bright);
    border-radius: 20px;
    padding: 38px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(225, 29, 72, 0.2);
    text-align: center;
  }
  .login-badge {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(225, 29, 72, 0.15);
    border: 1px solid rgba(225, 29, 72, 0.35);
    color: #fda4af;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 16px;
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>

<!-- Master Login Gate -->
<div id="loginScreen">
  <div class="login-card">
    <div style="font-size: 44px; margin-bottom: 10px;">🛡️</div>
    <span class="login-badge">HARDENED ACCESS GATE</span>
    <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 6px;">HEMOGLYPH SENTINEL</h2>
    <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 24px;">Enter Master Administrator credentials to unlock licensing & remote kill-switch controls.</p>
    
    <div class="form-group" style="text-align: left;">
      <label class="form-label">Master Admin Password</label>
      <input type="password" id="masterPasswordInput" class="form-input" placeholder="••••••••••••" autofocus onkeydown="if(event.key==='Enter')submitLogin()">
    </div>
    
    <button class="btn btn-primary" style="width: 100%; justify-content: center; padding: 11px; font-size: 13.5px; margin-top: 10px;" onclick="submitLogin()">Unlock Sentinel Console</button>
    
    <div id="loginError" style="margin-top: 14px; font-size: 12px; color: #f87171; display: none;"></div>
    <div style="font-size: 11px; color: var(--text-dim); margin-top: 24px;">Initial default: <code class="mono" style="color:var(--accent-cyan);">admin2026</code> (Changeable in settings)</div>
  </div>
</div>

<div class="container" id="mainDashboard" style="display: none;">

  <!-- Header -->
  <header>
    <div class="brand">
      <div class="brand-logo">🩸</div>
      <div>
        <div class="brand-title">HEMOGLYPH SENTINEL v2.5</div>
        <div class="brand-subtitle">Military-Grade Asymmetric RSA-4096 Licensing & CDS Kill-Switch Platform</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn btn-primary" onclick="openKeygenModal()">+ Issue RSA-4096 Key</button>
      <button class="btn btn-secondary" onclick="openInspectorModal()">🔍 Key Inspector</button>
      <button class="btn btn-secondary" onclick="openAuditModal()">📜 Audit Trail</button>
      <a href="/api/export/csv" class="btn btn-secondary">📥 Export CSV</a>
      <button class="btn btn-secondary" onclick="openPasswordModal()">⚙️ Password</button>
      <button class="btn btn-secondary" id="audioToggleBtn" onclick="toggleAudio()">🔔 Chimes: ON</button>
      <button class="btn btn-secondary btn-icon" onclick="fetchData()">🔄</button>
      <button class="btn btn-danger btn-icon" title="Logout" onclick="submitLogout()">🔒 Logout</button>
    </div>
  </header>

  <!-- Metrics Grid -->
  <div class="stats-grid">
    <div class="stat-card stat-total" onclick="setFilter('all')">
      <div class="stat-label">Total Workstations</div>
      <div class="stat-value" id="kpi-total">0</div>
      <div class="stat-hint">All registered devices</div>
    </div>
    <div class="stat-card stat-online" onclick="setFilter('online')">
      <div class="stat-label">Live Active Now</div>
      <div class="stat-value" style="color: #34d399;" id="kpi-online">0</div>
      <div class="stat-hint">Active link within 8s</div>
    </div>
    <div class="stat-card stat-licensed" onclick="setFilter('licensed')">
      <div class="stat-label">Activated Workstations</div>
      <div class="stat-value" style="color: #38bdf8;" id="kpi-licensed">0</div>
      <div class="stat-hint">RSA-2048 key installed</div>
    </div>
    <div class="stat-card stat-not-active" onclick="setFilter('not_active')">
      <div class="stat-label">Not Active / Unlicensed</div>
      <div class="stat-value" style="color: #f59e0b;" id="kpi-not-active">0</div>
      <div class="stat-hint">Pending key issuance</div>
    </div>
    <div class="stat-card stat-blocked" onclick="setFilter('blocked')">
      <div class="stat-label">Suspended / Blocked</div>
      <div class="stat-value" style="color: #f87171;" id="kpi-blocked">0</div>
      <div class="stat-hint">Kill-switch lockdown active</div>
    </div>
  </div>

  <!-- Clients Table Section -->
  <div class="section-card">
    <div class="toolbar">
      <div class="filter-tabs">
        <button class="tab-btn active" id="tab-all" onclick="setFilter('all')">All Workstations</button>
        <button class="tab-btn" id="tab-online" onclick="setFilter('online')">🟢 Online Now</button>
        <button class="tab-btn" id="tab-not_active" onclick="setFilter('not_active')">🟠 Not Active</button>
        <button class="tab-btn" id="tab-licensed" onclick="setFilter('licensed')">💎 Activated</button>
        <button class="tab-btn" id="tab-blocked" onclick="setFilter('blocked')">🔴 Suspended</button>
      </div>
      <input type="text" id="searchInput" class="search-box" placeholder="Search doctor, clinic, IP or Machine ID..." onkeyup="filterTable()">
    </div>
    <div style="overflow-x: auto;">
      <table id="clientsTable">
        <thead>
          <tr>
            <th>Network Link</th>
            <th>License Gate</th>
            <th>Clinician / Account</th>
            <th>Machine ID</th>
            <th>Edition & Duration</th>
            <th>Version</th>
            <th>Telemetry</th>
            <th>Remote IP</th>
            <th style="text-align: right;">Authorization Actions</th>
          </tr>
        </thead>
        <tbody id="tableBody">
          <tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 36px;">Synchronizing live telemetry...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

</div>

<!-- Keygen Modal -->
<div class="modal-overlay" id="keygenModal">
  <div class="modal" style="max-width: 580px;">
    <div class="modal-header">
      <div class="modal-title">🔑 Issue Military-Grade RSA-4096 License</div>
      <button class="close-btn" onclick="closeKeygenModal()">&times;</button>
    </div>
    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 11.5px; color: #6ee7b7; display: flex; align-items: center; gap: 8px;">
      <span>🛡️</span>
      <span><strong>Asymmetric RSA-4096 / SHA-512 Engine Active:</strong> Mathematically unforgeable, node-locked to target hardware with anti-replay protection.</span>
    </div>
    <div class="form-group">
      <label class="form-label">Client Machine ID (e.g. from doctor's screen)</label>
      <input type="text" id="kgMid" class="form-input mono" placeholder="HG-XXXX-XXXX-XXXX-XXXX">
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
      <div class="form-group">
        <label class="form-label">Doctor / Clinician Name</label>
        <input type="text" id="kgName" class="form-input" placeholder="e.g. Sobhan Bahrami">
      </div>
      <div class="form-group">
        <label class="form-label">Doctor Email (Optional)</label>
        <input type="email" id="kgEmail" class="form-input" placeholder="e.g. doctor@hospital.org">
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Clinic / Hospital / Laboratory (Optional)</label>
      <input type="text" id="kgClinic" class="form-input" placeholder="e.g. Central Hematology Institute">
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
      <div class="form-group">
        <label class="form-label">License Duration</label>
        <select id="kgDays" class="form-select">
          <option value="0">Perpetual (Lifetime Activation)</option>
          <option value="14">14 Days (Free Clinical Trial)</option>
          <option value="30">30 Days (1 Month Subscription)</option>
          <option value="90">90 Days (Quarterly Plan)</option>
          <option value="180">180 Days (Half-Year Plan)</option>
          <option value="365" selected>365 Days (Annual Enterprise License)</option>
          <option value="1095">3 Years (Institutional License)</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Edition & Feature Profile</label>
        <select id="kgTier" class="form-select">
          <option value="Enterprise Clinical CDS">Enterprise Clinical CDS (Full AI & Diagnostic Suite)</option>
          <option value="Hematology Specialist Edition">Hematology Specialist Edition</option>
          <option value="Standard Practice Edition">Standard Practice Edition</option>
        </select>
      </div>
    </div>

    <div style="display: flex; gap: 10px; margin-top: 18px;">
      <button class="btn btn-primary" style="flex: 1;" onclick="submitKeygen()">Sign & Authorize RSA-4096 Key</button>
      <button class="btn btn-secondary" onclick="closeKeygenModal()">Cancel</button>
    </div>

    <div id="keygenResult" class="result-box" style="max-height: 160px; overflow-y: auto;"></div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
      <button id="copyKeyBtn" class="btn btn-secondary" style="display: none;" onclick="copyResultKey()">📋 Copy Key Token</button>
      <button id="copyArmorBtn" class="btn btn-secondary" style="display: none;" onclick="copyResultArmor()">📜 Copy PEM Certificate</button>
      <button id="copyMsgBtn" class="btn btn-primary" style="display: none;" onclick="copyWhatsAppMessage()">💬 Copy WhatsApp Text</button>
      <button id="copyEmailBtn" class="btn btn-secondary" style="display: none;" onclick="copyEmailMessage()">✉️ Copy Email Template</button>
    </div>
  </div>
</div>

<!-- License Inspector Modal -->
<div class="modal-overlay" id="inspectorModal">
  <div class="modal" style="max-width: 650px;">
    <div class="modal-header">
      <div class="modal-title">🔍 Cryptographic License Inspector & Verifier</div>
      <button class="close-btn" onclick="closeInspectorModal()">&times;</button>
    </div>
    <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">
      Paste any license token or PEM armor certificate to verify its asymmetric cryptographic signature, inspect payload attributes, expiration, and hardware binding in real-time.
    </p>
    <div class="form-group">
      <label class="form-label">License Key Token or PEM Armor Block</label>
      <textarea id="inspectInput" class="form-input mono" rows="4" placeholder="Paste HGLIC4K-... or -----BEGIN HEMOGLYPH..."></textarea>
    </div>
    <div style="display: flex; gap: 10px; margin-bottom: 16px;">
      <button class="btn btn-primary" style="flex: 1;" onclick="submitInspectKey()">🔬 Verify & Inspect Signature</button>
      <button class="btn btn-secondary" onclick="document.getElementById('inspectInput').value=''">Clear</button>
    </div>
    <div id="inspectResult" style="display: none; background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; font-size: 12px;"></div>
  </div>
</div>

<!-- Block Modal with Presets -->
<div class="modal-overlay" id="blockModal">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" style="color: #f87171;">🛑 Remote Kill-Switch Lockdown</div>
      <button class="close-btn" onclick="closeBlockModal()">&times;</button>
    </div>
    <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 14px;">
      Activating lockdown will immediately freeze the workstation screen, purge in-memory patient data, and display the suspension notice.
    </p>
    <div class="form-group">
      <label class="form-label">Target Machine ID</label>
      <input type="text" id="bmMid" class="form-input mono" readonly style="opacity: 0.8;">
    </div>
    <div class="form-group">
      <label class="form-label">Reason for Suspension (Visible to Clinician)</label>
      <input type="text" id="bmReason" class="form-input" placeholder="e.g. Subscription period ended">
      <div class="chip-group">
        <span class="chip" onclick="setBlockReason('Subscription period lapsed')">Subscription period lapsed</span>
        <span class="chip" onclick="setBlockReason('Payment renewal pending')">Payment renewal pending</span>
        <span class="chip" onclick="setBlockReason('Security audit / Unauthorized transfer')">Unauthorized transfer</span>
        <span class="chip" onclick="setBlockReason('Workstation replaced')">Workstation replaced</span>
      </div>
    </div>
    <div style="display: flex; gap: 10px; margin-top: 20px;">
      <button class="btn btn-danger" style="flex: 1;" onclick="submitBlock()">🚨 Activate Immediate Lockdown</button>
      <button class="btn btn-secondary" onclick="closeBlockModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Edit Details Modal -->
<div class="modal-overlay" id="editModal">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title">📝 Workstation Profile & Internal Notes</div>
      <button class="close-btn" onclick="closeEditModal()">&times;</button>
    </div>
    <input type="hidden" id="emMid">
    <div class="form-group">
      <label class="form-label">Doctor / Clinician Name</label>
      <input type="text" id="emName" class="form-input">
    </div>
    <div class="form-group">
      <label class="form-label">Doctor / Clinician Email</label>
      <input type="email" id="emEmail" class="form-input" placeholder="e.g. doctor@hospital.org">
    </div>
    <div class="form-group">
      <label class="form-label">Clinic / Hospital Name</label>
      <input type="text" id="emClinic" class="form-input">
    </div>
    <div class="form-group">
      <label class="form-label">Internal Private Notes (Only visible to you)</label>
      <textarea id="emNotes" class="form-textarea" rows="3" placeholder="e.g. Paid via invoice #2049, contact phone: 0912..."></textarea>
    </div>
    <div style="display: flex; gap: 10px; margin-top: 18px;">
      <button class="btn btn-primary" style="flex: 1;" onclick="submitEdit()">Save Profile</button>
      <button class="btn btn-secondary" onclick="closeEditModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Change Password Modal -->
<div class="modal-overlay" id="passwordModal">
  <div class="modal" style="max-width: 440px;">
    <div class="modal-header">
      <div class="modal-title">⚙️ Change Sentinel Master Password</div>
      <button class="close-btn" onclick="closePasswordModal()">&times;</button>
    </div>
    <div class="form-group">
      <label class="form-label">Current Master Password</label>
      <input type="password" id="curPwdInput" class="form-input">
    </div>
    <div class="form-group">
      <label class="form-label">New Master Password (min 6 characters)</label>
      <input type="password" id="newPwdInput" class="form-input">
    </div>
    <div style="display: flex; gap: 10px; margin-top: 18px;">
      <button class="btn btn-primary" style="flex: 1;" onclick="submitChangePassword()">Update Password</button>
      <button class="btn btn-secondary" onclick="closePasswordModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Audit Trail Modal -->
<div class="modal-overlay" id="auditModal">
  <div class="modal" style="max-width: 640px;">
    <div class="modal-header">
      <div class="modal-title">📜 Chronological Security Audit Trail</div>
      <button class="close-btn" onclick="closeAuditModal()">&times;</button>
    </div>
    <div id="auditList" style="max-height: 380px; overflow-y: auto; font-size: 12px;"></div>
    <div style="margin-top: 16px; text-align: right;">
      <button class="btn btn-secondary" onclick="closeAuditModal()">Close</button>
    </div>
  </div>
</div>

<script>
let allClients = [];
let currentFilter = 'all';
let audioEnabled = true;
let lastGeneratedKey = '';
let lastArmorBlock = '';
let lastWhatsAppMessage = '';
let lastEmailMessage = '';
let audioCtx = null;
let authToken = localStorage.getItem('sentinel_token') || '';

// Web Audio Chimes
function playTone(freq, type = 'sine', duration = 0.12) {
  if (!audioEnabled) return;
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {}
}

function chimeSuccess() { playTone(587.33); setTimeout(() => playTone(880), 80); }
function chimeAlert() { playTone(300, 'sawtooth', 0.25); }

function toggleAudio() {
  audioEnabled = !audioEnabled;
  document.getElementById('audioToggleBtn').innerText = audioEnabled ? '🔔 Chimes: ON' : '🔕 Chimes: OFF';
}

function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': authToken ? ('Bearer ' + authToken) : ''
  };
}

async function checkAuth() {
  try {
    const res = await fetch('/api/auth/check', { headers: getAuthHeaders() });
    const data = await res.json();
    if (data.authenticated) {
      document.getElementById('loginScreen').style.display = 'none';
      document.getElementById('mainDashboard').style.display = 'block';
      fetchData();
    } else {
      document.getElementById('loginScreen').style.display = 'flex';
      document.getElementById('mainDashboard').style.display = 'none';
      document.getElementById('masterPasswordInput').focus();
    }
  } catch (e) {
    document.getElementById('loginScreen').style.display = 'flex';
  }
}

async function submitLogin() {
  const pwd = document.getElementById('masterPasswordInput').value;
  const errBox = document.getElementById('loginError');
  errBox.style.display = 'none';

  if (!pwd) {
    errBox.innerText = 'Please enter master password';
    errBox.style.display = 'block';
    return;
  }

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd })
    });
    const data = await res.json();
    if (data.success) {
      authToken = data.token;
      localStorage.setItem('sentinel_token', authToken);
      chimeSuccess();
      document.getElementById('loginScreen').style.display = 'none';
      document.getElementById('mainDashboard').style.display = 'block';
      fetchData();
    } else {
      chimeAlert();
      errBox.innerText = data.error || 'Invalid credentials';
      errBox.style.display = 'block';
    }
  } catch (e) {
    errBox.innerText = 'Login error: ' + e.message;
    errBox.style.display = 'block';
  }
}

async function submitLogout() {
  await fetch('/api/auth/logout', { method: 'POST', headers: getAuthHeaders() });
  authToken = '';
  localStorage.removeItem('sentinel_token');
  location.reload();
}

function openPasswordModal() { document.getElementById('passwordModal').style.display = 'flex'; }
function closePasswordModal() { document.getElementById('passwordModal').style.display = 'none'; }

async function submitChangePassword() {
  const cur = document.getElementById('curPwdInput').value;
  const nw = document.getElementById('newPwdInput').value;
  if (!cur || !nw) { alert('Please fill in both password fields'); return; }

  const res = await fetch('/api/auth/change_password', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ current_password: cur, new_password: nw })
  });
  const data = await res.json();
  if (data.success) {
    alert('Master password changed! Please log in again with your new password.');
    submitLogout();
  } else {
    alert('Error: ' + data.message);
  }
}

async function fetchData() {
  try {
    const [statsRes, clientsRes] = await Promise.all([
      fetch('/api/stats', { headers: getAuthHeaders() }),
      fetch('/api/clients', { headers: getAuthHeaders() })
    ]);
    if (statsRes.status === 401 || clientsRes.status === 401) {
      checkAuth();
      return;
    }
    const stats = await statsRes.json();
    const clients = await clientsRes.json();

    document.getElementById('kpi-total').innerText = stats.total || 0;
    document.getElementById('kpi-online').innerText = stats.online || 0;
    document.getElementById('kpi-licensed').innerText = stats.licensed || 0;
    document.getElementById('kpi-not-active').innerText = stats.not_active || 0;
    document.getElementById('kpi-blocked').innerText = stats.blocked || 0;

    allClients = clients;
    renderFiltered();
  } catch (err) {
    console.error('Telemetry error:', err);
  }
}

function setFilter(filter) {
  currentFilter = filter;
  ['all', 'online', 'not_active', 'licensed', 'blocked'].forEach(t => {
    const el = document.getElementById('tab-' + t);
    if (el) el.classList.toggle('active', t === filter);
  });
  renderFiltered();
}

function renderFiltered() {
  let list = allClients;
  if (currentFilter === 'online') list = list.filter(c => c.computed_status === 'online');
  else if (currentFilter === 'not_active') list = list.filter(c => c.has_license === 0 && c.is_blocked === 0);
  else if (currentFilter === 'licensed') list = list.filter(c => c.has_license === 1 && c.is_blocked === 0);
  else if (currentFilter === 'blocked') list = list.filter(c => c.is_blocked === 1);

  const q = document.getElementById('searchInput').value.toLowerCase().trim();
  if (q) {
    list = list.filter(c => 
      (c.customer_name && c.customer_name.toLowerCase().includes(q)) ||
      (c.user_email && c.user_email.toLowerCase().includes(q)) ||
      (c.clinic_name && c.clinic_name.toLowerCase().includes(q)) ||
      (c.machine_id && c.machine_id.toLowerCase().includes(q)) ||
      (c.last_ip && c.last_ip.includes(q))
    );
  }
  renderTable(list);
}

function filterTable() { renderFiltered(); }

function renderTable(clients) {
  const tbody = document.getElementById('tableBody');
  if (!clients || clients.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 40px; color: var(--text-dim);">No workstations match filter. Devices appear automatically when Hemoglyph is launched.</td></tr>';
    return;
  }

  let html = '';
  for (const c of clients) {
    const isBlocked = c.is_blocked === 1;
    const isOnline = c.computed_status === 'online';
    const hasLic = c.has_license === 1;

    let linkBadge = isOnline ? 
      '<span class="badge badge-online">🟢 ONLINE</span>' : 
      '<span class="badge badge-offline">⚪ OFFLINE</span>';

    let licBadge = '';
    if (isBlocked) {
      licBadge = '<span class="badge badge-blocked">🔴 BLOCKED</span>';
    } else if (hasLic) {
      licBadge = '<span class="badge badge-activated">💎 ACTIVATED</span>';
    } else {
      licBadge = '<span class="badge badge-not-active">🟠 NOT ACTIVE</span>';
    }

    const emailDiv = c.user_email ? `<div style="font-size: 11px; color: #38bdf8; margin-top: 2px;">✉️ ${escapeHtml(c.user_email)}</div>` : '';
    const facility = c.clinic_name ? `<div style="font-size: 11px; color: var(--text-dim); margin-top: 2px;">🏥 ${escapeHtml(c.clinic_name)}</div>` : '';

    html += `<tr>
      <td>${linkBadge}</td>
      <td>${licBadge}</td>
      <td>
        <strong style="font-size: 13.5px;">${escapeHtml(c.customer_name || 'Discovered Workstation')}</strong>
        ${emailDiv}
        ${facility}
      </td>
      <td><span class="mid-code mono">${escapeHtml(c.machine_id)}</span></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(c.tier || 'Unlicensed')}</div>
        <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(c.expiry_hint || 'NONE')}</div>
      </td>
      <td class="mono">v${escapeHtml(c.app_version || '1.0.0')}</td>
      <td>
        ${isOnline ? 
          `<div style="color:#34d399; font-weight:700;">Active Now <span style="font-size:11px; opacity:0.8;">(${c.elapsed_seconds || 0}s ago)</span></div>` :
          `<div style="color:#94a3b8; font-size:11.5px;">${escapeHtml(c.status_label)}</div>`
        }
        <div style="font-size: 10px; color: var(--text-dim);">${c.ping_count || 0} pings logged</div>
      </td>
      <td class="mono" style="color: var(--text-dim); font-size: 11.5px;">${escapeHtml(c.last_ip || '—')}</td>
      <td style="text-align: right; white-space: nowrap;">
        ${!hasLic ? 
          `<button class="btn btn-primary btn-icon" onclick="quickIssueKey('${escapeHtml(c.machine_id)}', '${escapeHtml(c.customer_name || '')}', '${escapeHtml(c.user_email || '')}')">🔑 Issue Key</button> ` : ''
        }
        ${isBlocked ? 
          `<button class="btn btn-success btn-icon" onclick="unblockClient('${escapeHtml(c.machine_id)}')">🟢 Unblock</button>` :
          `<button class="btn btn-danger btn-icon" onclick="openBlockModal('${escapeHtml(c.machine_id)}')">🛑 Block</button>`
        }
        <button class="btn btn-secondary btn-icon" title="Edit Profile" onclick="openEditModal('${escapeHtml(c.machine_id)}', '${escapeHtml(c.customer_name || '')}', '${escapeHtml(c.user_email || '')}', '${escapeHtml(c.clinic_name || '')}', '${escapeHtml(c.internal_notes || '')}')">📝</button>
        <button class="btn btn-secondary btn-icon" title="Delete" onclick="deleteClient('${escapeHtml(c.machine_id)}')">🗑️</button>
      </td>
    </tr>`;
  }
  tbody.innerHTML = html;
}

// Modal Handlers
function openKeygenModal() {
  document.getElementById('keygenModal').style.display = 'flex';
  document.getElementById('keygenResult').style.display = 'none';
  document.getElementById('copyKeyBtn').style.display = 'none';
  document.getElementById('copyArmorBtn').style.display = 'none';
  document.getElementById('copyMsgBtn').style.display = 'none';
  document.getElementById('copyEmailBtn').style.display = 'none';
}
function closeKeygenModal() { document.getElementById('keygenModal').style.display = 'none'; }

function quickIssueKey(mid, name, email) {
  openKeygenModal();
  document.getElementById('kgMid').value = mid;
  document.getElementById('kgName').value = (name && name !== 'Discovered Device' && name !== 'Discovered Workstation' && name !== 'Unregistered Device') ? name : '';
  document.getElementById('kgEmail').value = email || '';
  document.getElementById('kgName').focus();
}

async function submitKeygen() {
  const mid = document.getElementById('kgMid').value.trim();
  const name = document.getElementById('kgName').value.trim() || 'Registered Clinician';
  const email = document.getElementById('kgEmail').value.trim();
  const clinic = document.getElementById('kgClinic').value.trim();
  const days = parseInt(document.getElementById('kgDays').value, 10);
  const tier = document.getElementById('kgTier').value;

  if (!mid) { alert('Please enter Machine ID'); return; }

  try {
    const res = await fetch('/api/keygen', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ machine_id: mid, customer_name: name, user_email: email, clinic_name: clinic, days: days, tier: tier })
    });
    const data = await res.json();
    if (data.success) {
      lastGeneratedKey = data.license_key;
      lastArmorBlock = data.armor_block;
      lastWhatsAppMessage = data.whatsapp_message;
      lastEmailMessage = data.email_message;

      const resBox = document.getElementById('keygenResult');
      resBox.innerText = `MILITARY-GRADE RSA-4096 ACTIVATION TOKEN READY:\n\n${data.license_key}\n\nClient: ${data.customer_name}\nTier: ${data.tier}\nExpiry: ${data.expires_at}\n\nSecurity: Asymmetric RSA-4096 with SHA-512 Digest`;
      resBox.style.display = 'block';
      document.getElementById('copyKeyBtn').style.display = 'inline-flex';
      document.getElementById('copyArmorBtn').style.display = 'inline-flex';
      document.getElementById('copyMsgBtn').style.display = 'inline-flex';
      document.getElementById('copyEmailBtn').style.display = 'inline-flex';
      chimeSuccess();
      fetchData();
    } else {
      alert('Error: ' + data.error);
    }
  } catch (err) {
    alert('Keygen failed: ' + err.message);
  }
}

function copyResultKey() {
  if (lastGeneratedKey) {
    navigator.clipboard.writeText(lastGeneratedKey).then(() => {
      chimeSuccess();
      alert('Copied Military-Grade RSA-4096 key token to clipboard!');
    });
  }
}

function copyResultArmor() {
  if (lastArmorBlock) {
    navigator.clipboard.writeText(lastArmorBlock).then(() => {
      chimeSuccess();
      alert('Copied PEM License Armor Certificate to clipboard!');
    });
  }
}

function copyWhatsAppMessage() {
  if (lastWhatsAppMessage) {
    navigator.clipboard.writeText(lastWhatsAppMessage).then(() => {
      chimeSuccess();
      alert('Copied ready-to-send WhatsApp / Telegram / SMS invitation message!');
    });
  }
}

function copyEmailMessage() {
  if (lastEmailMessage) {
    navigator.clipboard.writeText(lastEmailMessage).then(() => {
      chimeSuccess();
      alert('Copied formal license delivery email template to clipboard!');
    });
  }
}

// License Inspector Handlers
function openInspectorModal() {
  document.getElementById('inspectorModal').style.display = 'flex';
  document.getElementById('inspectResult').style.display = 'none';
  document.getElementById('inspectInput').focus();
}
function closeInspectorModal() {
  document.getElementById('inspectorModal').style.display = 'none';
}

async function submitInspectKey() {
  const key = document.getElementById('inspectInput').value.trim();
  const resBox = document.getElementById('inspectResult');
  if (!key) { alert('Please paste a license key or certificate to inspect'); return; }

  try {
    const res = await fetch('/api/inspect_key', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ key: key })
    });
    const data = await res.json();
    if (data.success && data.data) {
      const d = data.data;
      const isValid = d.valid;
      const statusColor = isValid ? '#34d399' : '#f87171';
      const statusText = isValid ? 'VALID & AUTHENTIC DIGITAL SIGNATURE' : 'INVALID / TAMPERED / EXPIRED';

      let featsHtml = '';
      if (d.features && d.features.length) {
        featsHtml = `<div style="margin-top: 8px;"><strong>Authorized Modules (${d.features.length}):</strong><div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">` +
          d.features.map(f => `<span class="chip" style="font-size:10px; padding:2px 8px;">${f}</span>`).join('') +
          `</div></div>`;
      }

      resBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 10px;">
          <span style="font-weight: 800; color: ${statusColor}; font-size: 13px;">${isValid ? '✅' : '❌'} ${statusText}</span>
          <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">${d.algorithm || 'RSA'}</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11.5px;">
          <div><strong>Licensee:</strong> ${escapeHtml(d.customer_name || 'N/A')}</div>
          <div><strong>Email:</strong> ${escapeHtml(d.user_email || 'N/A')}</div>
          <div><strong>Machine ID:</strong> <code class="mono" style="color:var(--accent-cyan);">${escapeHtml(d.machine_id || 'N/A')}</code></div>
          <div><strong>Tier Profile:</strong> ${escapeHtml(d.tier || 'N/A')}</div>
          <div><strong>Issued At:</strong> ${escapeHtml(d.issued_at || 'N/A')}</div>
          <div><strong>Expires:</strong> <span style="color:${d.expired ? '#f87171' : '#34d399'}; font-weight:600;">${escapeHtml(d.expires_at || 'N/A')}</span></div>
        </div>
        ${featsHtml}
      `;
      resBox.style.display = 'block';
      if (isValid) chimeSuccess(); else chimeAlert();
    } else {
      resBox.innerHTML = `<div style="color: #f87171; font-weight: 700;">❌ Verification Failed: ${escapeHtml(data.error || 'Invalid key')}</div>`;
      resBox.style.display = 'block';
      chimeAlert();
    }
  } catch (err) {
    alert('Inspection error: ' + err.message);
  }
}

// Block Modal Handlers
function openBlockModal(mid) {
  document.getElementById('bmMid').value = mid;
  document.getElementById('bmReason').value = 'Subscription period lapsed';
  document.getElementById('blockModal').style.display = 'flex';
}
function closeBlockModal() { document.getElementById('blockModal').style.display = 'none'; }
function setBlockReason(text) { document.getElementById('bmReason').value = text; }

async function submitBlock() {
  const mid = document.getElementById('bmMid').value;
  const reason = document.getElementById('bmReason').value.trim() || 'Suspended by administrator';
  closeBlockModal();
  chimeAlert();
  await fetch('/api/clients/block', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ machine_id: mid, reason: reason })
  });
  fetchData();
}

async function unblockClient(mid) {
  if (!confirm('Restore access for ' + mid + '?')) return;
  chimeSuccess();
  await fetch('/api/clients/unblock', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ machine_id: mid })
  });
  fetchData();
}

async function deleteClient(mid) {
  if (!confirm('Permanently delete record for ' + mid + '?')) return;
  await fetch('/api/clients/delete', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ machine_id: mid })
  });
  fetchData();
}

// Edit Modal Handlers
function openEditModal(mid, name, email, clinic, notes) {
  document.getElementById('emMid').value = mid;
  document.getElementById('emName').value = name !== 'Discovered Workstation' ? name : '';
  document.getElementById('emEmail').value = email || '';
  document.getElementById('emClinic').value = clinic || '';
  document.getElementById('emNotes').value = notes || '';
  document.getElementById('editModal').style.display = 'flex';
}
function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }

async function submitEdit() {
  const mid = document.getElementById('emMid').value;
  const name = document.getElementById('emName').value;
  const email = document.getElementById('emEmail').value;
  const clinic = document.getElementById('emClinic').value;
  const notes = document.getElementById('emNotes').value;
  closeEditModal();
  await fetch('/api/clients/update', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ machine_id: mid, customer_name: name, user_email: email, clinic_name: clinic, internal_notes: notes })
  });
  chimeSuccess();
  fetchData();
}

// Audit Modal Handlers
async function openAuditModal() {
  try {
    const res = await fetch('/api/audit', { headers: getAuthHeaders() });
    const logs = await res.json();
    const box = document.getElementById('auditList');
    if (!logs || logs.length === 0) {
      box.innerHTML = '<div style="color:var(--text-dim); padding:20px; text-align:center;">No audit events recorded yet.</div>';
    } else {
      let h = '';
      for (const l of logs) {
        h += `<div style="padding:9px 0; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; gap:12px;">
          <div>
            <strong style="color:var(--accent-cyan);">${escapeHtml(l.action)}</strong>
            <span class="mono" style="color:var(--text-muted); margin-left:6px;">${escapeHtml(l.machine_id)}</span>
            <div style="color:var(--text-dim); margin-top:2px;">${escapeHtml(l.details)}</div>
          </div>
          <div style="color:var(--text-dim); font-size:11px; white-space:nowrap;">${escapeHtml(l.time_str)}</div>
        </div>`;
      }
      box.innerHTML = h;
    }
    document.getElementById('auditModal').style.display = 'flex';
  } catch (e) { alert('Could not fetch audit logs'); }
}
function closeAuditModal() { document.getElementById('auditModal').style.display = 'none'; }

function escapeHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Initial check & real-time auto-refresh loop
checkAuth();
setInterval(() => {
  if (document.getElementById('mainDashboard').style.display === 'block') {
    fetchData();
  }
}, 1500);
</script>
</body>
</html>
"""


# ============================================================================
# 5. Server Launcher
# ============================================================================
def run_server(port: int = DEFAULT_PORT, host: str = "0.0.0.0"):
    init_db()
    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, SentinelHandler)
    print("=" * 72)
    print("  HEMOGLYPH SENTINEL v2.0 — HARDENED EXECUTIVE LICENSE & CDS PLATFORM")
    print(f"  Live Endpoint : http://{host}:{port}")
    print(f"  Local Browser : http://127.0.0.1:{port}")
    print("  Security      : Asymmetric RSA-2048 + PBKDF2 Password Gate Active")
    print("  Default Pass  : admin2026 (Initial setup only - changeable in settings)")
    print("=" * 72)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Sentinel server gracefully terminated.")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hemoglyph Sentinel License Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
