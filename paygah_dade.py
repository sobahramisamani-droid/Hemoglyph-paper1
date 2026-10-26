"""SQLite persistence for patients, analyses and history."""

import base64
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

try:
    import orjson

    def _fast_loads(val: Any) -> Any:
        if val is None or isinstance(val, (dict, list)):
            return val
        if not val or val == "null":
            return {}
        try:
            return orjson.loads(val)
        except Exception:
            return json.loads(val)

    def _fast_dumps(val: Any) -> str:
        try:
            return orjson.dumps(val).decode("utf-8")
        except Exception:
            return json.dumps(val, ensure_ascii=False)

except ImportError:
    def _fast_loads(val: Any) -> Any:
        if val is None or isinstance(val, (dict, list)):
            return val
        if not val or val == "null":
            return {}
        return json.loads(val)

    def _fast_dumps(val: Any) -> str:
        return json.dumps(val, ensure_ascii=False)


def _resolve_db_path() -> str:
    # 1. Standard persistent user directory (~/.hemoglyph/hemoglyph.db)
    # Storing in ~/.hemoglyph ensures users, logins, and tests persist across builds and updates!
    try:
        user_dir = Path.home() / ".hemoglyph"
        user_db = user_dir / "hemoglyph.db"
        if user_db.exists() and user_db.stat().st_size > 0:
            return str(user_db.resolve())
    except Exception:
        pass

    # 2. Local database in application directory (if present and non-empty)
    try:
        local_db = Path("hemoglyph.db")
        if local_db.exists() and local_db.stat().st_size > 0 and os.access(str(local_db), os.W_OK):
            return str(local_db.resolve())
    except Exception:
        pass

    # 3. Create persistent database in ~/.hemoglyph
    try:
        user_dir = Path.home() / ".hemoglyph"
        user_dir.mkdir(parents=True, exist_ok=True)
        return str((user_dir / "hemoglyph.db").resolve())
    except Exception:
        pass

    appdata = os.getenv("LOCALAPPDATA")
    if appdata:
        try:
            user_dir = Path(appdata) / "Hemoglyph"
            user_dir.mkdir(parents=True, exist_ok=True)
            return str((user_dir / "hemoglyph.db").resolve())
        except Exception:
            pass

    import tempfile
    return str(Path(tempfile.gettempdir()) / "hemoglyph.db")


DB_NAME = _resolve_db_path()


def gereftan_ettesal() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-64000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception:
        pass
    return conn


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _parse_timestamp(ts: Any) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    clean = ts.strip().replace("Z", "")
    if "." in clean:
        clean = clean.split(".")[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(clean, fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def init_db() -> None:
    conn = gereftan_ettesal()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT DEFAULT '',
        age INTEGER,
        sex TEXT DEFAULT 'female',
        weight REAL,
        height REAL,
        waist REAL,
        systolic_bp REAL,
        diastolic_bp REAL,
        heart_rate REAL,
        sleep_hours REAL,
        smoking TEXT,
        physical_activity TEXT,
        family_history_dm TEXT,
        family_history_cad TEXT,
        family_history_htn TEXT,
        family_history_obesity TEXT,
        birth_date TEXT,
        stable_profile TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS blood_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        selected_panels TEXT,
        patient_inputs TEXT,
        derived_metrics TEXT,
        diagnoses TEXT,
        risk_predictions TEXT,
        ai_report TEXT,
        initial_summary TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        analysis_id INTEGER,
        title TEXT DEFAULT '',
        language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        messages TEXT DEFAULT '[]',
        summary TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')

    for col_sql in (
        "ALTER TABLE users ADD COLUMN birth_date TEXT",
        "ALTER TABLE users ADD COLUMN stable_profile TEXT DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN waist REAL",
        "ALTER TABLE users ADD COLUMN systolic_bp REAL",
        "ALTER TABLE users ADD COLUMN diastolic_bp REAL",
        "ALTER TABLE users ADD COLUMN heart_rate REAL",
        "ALTER TABLE users ADD COLUMN sleep_hours REAL",
        "ALTER TABLE users ADD COLUMN smoking TEXT",
        "ALTER TABLE users ADD COLUMN physical_activity TEXT",
        'ALTER TABLE users ADD COLUMN family_history_dm TEXT',
        "ALTER TABLE users ADD COLUMN family_history_cad TEXT",
        "ALTER TABLE users ADD COLUMN family_history_htn TEXT",
        'ALTER TABLE users ADD COLUMN family_history_obesity TEXT',
    ):
        try:
            c.execute(col_sql)
        except sqlite3.OperationalError:
            pass

    # High-performance composite indexes for rapid retrieval of consecutive test pairs and delta checks
    for idx_sql in (
        "CREATE INDEX IF NOT EXISTS idx_blood_tests_user_date ON blood_tests(user_id, test_date DESC, id DESC)",
        "CREATE INDEX IF NOT EXISTS idx_blood_tests_user_id ON blood_tests(user_id, id DESC)",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated ON chat_sessions(user_id, updated_at DESC)",
    ):
        try:
            c.execute(idx_sql)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac('sha256', (pw or '').encode('utf-8'), salt, 310000)
    return ('pbkdf2_sha256$310000$'
            + base64.b64encode(salt).decode('utf-8') + "$"
            + base64.b64encode(h).decode('utf-8'))


def verify_password(pw: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        if stored.startswith("pbkdf2_sha256$") and stored.count('$') == 3:
            _algo, _iters, salt_b64, hash_b64 = stored.split('$')
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(hash_b64)
            actual = hashlib.pbkdf2_hmac('sha256', (pw or '').encode('utf-8'),
                                         salt, int(_iters))
            return secrets.compare_digest(actual, expected)

        legacy = hashlib.sha256((pw or '').encode('utf-8')).hexdigest()
        return secrets.compare_digest(legacy, stored)
    except Exception:
        return False


PASSWORD_HASH_PREFIX = "pbkdf2_sha256$310000$"


def password_needs_rehash(stored: str) -> bool:
    """True for legacy unsalted SHA-256 hashes or weaker PBKDF2 parameters."""
    if not stored:
        return False
    if not stored.startswith("pbkdf2_sha256$"):
        return True
    try:
        _algo, iters, _salt, _h = stored.split('$')
        return int(iters) < 310000
    except Exception:
        return True


def upgrade_password_hash(user_id: int, pw: str, current_stored: str) -> bool:
    """Transparently re-hash a legacy password after a successful verification.

    Atomic: the UPDATE is guarded by the old hash so a concurrent change (or a
    password reset in another session) cannot be clobbered.
    """
    if not password_needs_rehash(current_stored):
        return False
    new_hash = hash_password(pw)
    conn = gereftan_ettesal()
    try:
        cur = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ? AND password_hash = ?",
            (new_hash, user_id, current_stored))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()


def register_user(email: str, password_hash: str, full_name: str = "",
                  age: Optional[int] = None, sex: Optional[str] = None,
                  weight: Optional[float] = None, height: Optional[float] = None,
                  **kwargs) -> Optional[int]:
    conn = gereftan_ettesal()
    c = conn.cursor()
    try:
        c.execute('''
        INSERT INTO users (
            email, password_hash, full_name, age, sex, weight, height,
            waist, systolic_bp, diastolic_bp, heart_rate, sleep_hours,
            smoking, physical_activity,
            family_history_dm, family_history_cad,
            family_history_htn, family_history_obesity,
            birth_date, stable_profile, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                (email or '').strip().lower(), password_hash, full_name or '',
                age, sex, weight, height,
                kwargs.get('waist'), kwargs.get('systolic_bp'),
                kwargs.get('diastolic_bp'), kwargs.get('heart_rate'),
                kwargs.get('sleep_hours'), kwargs.get('smoking'),
                kwargs.get('physical_activity'),
                kwargs.get('family_history_dm'), kwargs.get('family_history_cad'),
                kwargs.get('family_history_htn'), kwargs.get('family_history_obesity'),
                kwargs.get('birth_date'),
                kwargs.get('stable_profile') or '{}',
                _utc_now(),
            ))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def sakht_karbar(*args, **kwargs):
    return register_user(*args, **kwargs)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = gereftan_ettesal()
    try:
        cur = conn.execute("SELECT * FROM users WHERE email = ?",
                           ((email or '').strip().lower(),))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def karbar_ba_shenase(user_id: int) -> Optional[Dict[str, Any]]:
    conn = gereftan_ettesal()
    try:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


_PROFILE_ALLOWED = {
    'full_name', 'age', 'sex', 'weight', 'height', 'waist',
    'systolic_bp', 'diastolic_bp', 'heart_rate', 'sleep_hours',
    'smoking', 'physical_activity',
    'family_history_dm', 'family_history_cad',
    'family_history_htn', 'family_history_obesity',
    'birth_date', 'stable_profile',
}

_PROFILE_ALIASES = {'weight_kg': 'weight', 'height_cm': 'height',
                    'name': 'full_name', 'fullName': 'full_name'}


def update_user_profile(user_id: int, **kwargs) -> bool:
    updates: Dict[str, Any] = {}
    for k, v in kwargs.items():
        key = _PROFILE_ALIASES.get(k, k)
        if key not in _PROFILE_ALLOWED or v is None:
            continue
        if key == 'stable_profile' and isinstance(v, dict):
            v = _fast_dumps(v)
        updates[key] = v
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [user_id]
    conn = gereftan_ettesal()
    try:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()


def profile_paydar(user_id: int) -> Dict[str, Any]:
    user = karbar_ba_shenase(user_id)
    if not user:
        return {}
    try:
        return _fast_loads(user.get('stable_profile') or '{}')
    except Exception:
        return {}


def save_blood_test(
    user_id: int,
    selected_panels: List[str],
    patient_inputs: Dict[str, Any],
    derived_metrics: Dict[str, Any],
    diagnoses: List[Dict],
    risk_predictions: List[Dict],
    ai_report: str = "",
    initial_summary: str = "",
    notes: str = "",
    test_date: Optional[str] = None,
) -> int:
    conn = gereftan_ettesal()
    c = conn.cursor()
    if test_date:
        c.execute('''
        INSERT INTO blood_tests (
            user_id, test_date, selected_panels, patient_inputs, derived_metrics,
            diagnoses, risk_predictions, ai_report, initial_summary, notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (
                user_id,
                test_date,
                _fast_dumps(selected_panels or []),
                _fast_dumps(patient_inputs or {}),
                _fast_dumps(derived_metrics or {}),
                _fast_dumps(diagnoses or []),
                _fast_dumps(risk_predictions or []),
                ai_report or "",
                initial_summary or '',
                notes or "",
            ))
    else:
        c.execute('''
        INSERT INTO blood_tests (
            user_id, selected_panels, patient_inputs, derived_metrics,
            diagnoses, risk_predictions, ai_report, initial_summary, notes
        ) VALUES (?,?,?,?,?,?,?,?,?)''',
            (
                user_id,
                _fast_dumps(selected_panels or []),
                _fast_dumps(patient_inputs or {}),
                _fast_dumps(derived_metrics or {}),
                _fast_dumps(diagnoses or []),
                _fast_dumps(risk_predictions or []),
                ai_report or "",
                initial_summary or '',
                notes or "",
            ))
    conn.commit()
    test_id = c.lastrowid
    conn.close()
    return test_id


ALLOWED_TEST_COLUMNS = (
    "id",
    "user_id",
    "test_date",
    "selected_panels",
    "patient_inputs",
    "derived_metrics",
    "diagnoses",
    "risk_predictions",
    "ai_report",
    "initial_summary",
    "notes",
)

_JSON_FIELDS = (
    "selected_panels",
    "patient_inputs",
    "derived_metrics",
    "diagnoses",
    "risk_predictions",
)


def get_user_tests(
    user_id: int,
    limit: int = 20,
    include_full: bool = False,
    *,
    fields: Optional[Sequence[str]] = None,
    consecutive_pairs: bool = False,
    max_interval_days: Optional[float] = None,
    since_date: Optional[str] = None,
    before_date: Optional[str] = None,
    order_asc: bool = False,
    offset: int = 0,
    as_tuples: bool = False,
) -> List[Any]:
    """
    Retrieve blood tests for a given user with optional selective field projection,
    date filtering, and high-speed consecutive test pairing for delta-check engines.

    Parameters:
        user_id: ID of the user.
        limit: Maximum number of tests or pairs to return (default 20).
        include_full: If True, loads all table columns including heavy report text.
        fields: Explicit column list to select (e.g. ['patient_inputs', 'derived_metrics']).
                Overwrites include_full and drastically reduces DB I/O and JSON parsing overhead.
        consecutive_pairs: If True, transforms chronologically ordered tests into consecutive pairs
                           (current newer test vs. previous prior test) for longitudinal delta-checks.
        max_interval_days: Optional cutoff filter for consecutive pairs (e.g. only pairs <= 30.0 days apart).
        since_date: Lower bound timestamp filter (test_date >= since_date).
        before_date: Upper bound timestamp filter (test_date <= before_date).
        order_asc: True for oldest first; False for newest first (default).
        offset: Pagination offset.
        as_tuples: If True and consecutive_pairs=True, returns (current, previous) 2-tuples instead of dicts.
    """
    # 1. Determine projected columns
    if fields is not None:
        requested = [str(f).strip() for f in fields if str(f).strip() in ALLOWED_TEST_COLUMNS]
        # Always ensure 'id' and 'test_date' are present for chronological sorting and delta computations
        for mandatory in ("id", "test_date"):
            if mandatory not in requested:
                requested.insert(0, mandatory)
        selected_cols = requested
        cols_sql = ", ".join(selected_cols)
    elif include_full:
        selected_cols = list(ALLOWED_TEST_COLUMNS)
        cols_sql = "*"
    else:
        selected_cols = ["id", "test_date", "selected_panels", "notes"]
        cols_sql = ", ".join(selected_cols)

    # 2. Build SQL statement
    query_parts = [f"SELECT {cols_sql} FROM blood_tests WHERE user_id = ?"]
    params: List[Any] = [user_id]

    if since_date:
        query_parts.append("AND test_date >= ?")
        params.append(since_date)
    if before_date:
        query_parts.append("AND test_date <= ?")
        params.append(before_date)

    order_str = "ASC" if order_asc else "DESC"
    query_parts.append(f"ORDER BY test_date {order_str}, id {order_str}")

    # For consecutive pairs, fetch limit+1 records to yield limit pairs
    if consecutive_pairs:
        fetch_limit = (limit + 1) if (limit and limit > 0) else None
    else:
        fetch_limit = limit if (limit and limit > 0) else None

    if fetch_limit is not None:
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([fetch_limit, max(0, offset)])
    elif offset > 0:
        query_parts.append("LIMIT -1 OFFSET ?")
        params.append(offset)

    sql = " ".join(query_parts)

    conn = gereftan_ettesal()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    # 3. Fast JSON deserialization
    records: List[Dict[str, Any]] = []
    for r in rows:
        rec = dict(r)
        # Parse only the JSON columns that were actually requested and present
        for field in _JSON_FIELDS:
            if field in rec and rec[field]:
                rec[field] = _fast_loads(rec[field])
        records.append(rec)

    if not consecutive_pairs:
        return records[:limit] if limit else records

    # 4. Generate Consecutive Pairs for Delta-Checks
    if len(records) < 2:
        return []

    pairs: List[Any] = []
    for i in range(len(records) - 1):
        if order_asc:
            prev_test = records[i]
            curr_test = records[i + 1]
        else:
            curr_test = records[i]
            prev_test = records[i + 1]

        # Calculate time delta between consecutive tests
        t_curr = _parse_timestamp(curr_test.get("test_date"))
        t_prev = _parse_timestamp(prev_test.get("test_date"))

        delta_seconds = None
        delta_hours = None
        delta_days = None
        if t_curr and t_prev:
            delta_seconds = abs((t_curr - t_prev).total_seconds())
            delta_hours = round(delta_seconds / 3600.0, 2)
            delta_days = round(delta_seconds / 86400.0, 3)

        # Apply maximum delta-check interval constraint if specified
        if max_interval_days is not None and delta_days is not None:
            if delta_days > max_interval_days:
                continue

        if as_tuples:
            pairs.append((curr_test, prev_test))
        else:
            pairs.append({
                "current": curr_test,
                "previous": prev_test,
                "current_id": curr_test.get("id"),
                "previous_id": prev_test.get("id"),
                "current_date": curr_test.get("test_date"),
                "previous_date": prev_test.get("test_date"),
                "interval_seconds": delta_seconds,
                "interval_hours": delta_hours,
                "interval_days": delta_days,
            })

        if limit and len(pairs) >= limit:
            break

    return pairs


def get_consecutive_test_pairs(
    user_id: int,
    limit: int = 10,
    *,
    fields: Optional[Sequence[str]] = ("patient_inputs", "derived_metrics"),
    max_interval_days: Optional[float] = None,
    since_date: Optional[str] = None,
    as_tuples: bool = False,
) -> List[Any]:
    """
    High-performance specialized query for retrieving consecutive test pairs.
    Defaults to selecting only 'patient_inputs' and 'derived_metrics' to avoid
    loading large report blobs, providing optimal throughput for delta-check engines.
    """
    return get_user_tests(
        user_id=user_id,
        limit=limit,
        include_full=False,
        fields=fields,
        consecutive_pairs=True,
        max_interval_days=max_interval_days,
        since_date=since_date,
        as_tuples=as_tuples,
    )


def get_test_pair_for_delta_check(
    user_id: int,
    current_test_id: int,
    *,
    fields: Optional[Sequence[str]] = ("patient_inputs", "derived_metrics"),
    max_interval_days: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Given a current test ID, retrieves that test and its immediate prior test
    for the patient, formatted with interval statistics for instantaneous delta-checking.
    """
    current_test = get_test_by_id(current_test_id)
    if not current_test or current_test.get("user_id") != user_id:
        return None

    curr_date = current_test.get("test_date")
    if not curr_date:
        return None

    conn = gereftan_ettesal()
    try:
        cur = conn.cursor()
        cols = ["id", "test_date"]
        if fields:
            for f in fields:
                if f in ALLOWED_TEST_COLUMNS and f not in cols:
                    cols.append(f)
        cols_sql = ", ".join(cols)

        cur.execute(
            f"""SELECT {cols_sql} FROM blood_tests
                WHERE user_id = ? AND (test_date < ? OR (test_date = ? AND id < ?))
                ORDER BY test_date DESC, id DESC LIMIT 1""",
            (user_id, curr_date, curr_date, current_test_id),
        )
        prev_row = cur.fetchone()
    finally:
        conn.close()

    if not prev_row:
        return None

    prev_test = dict(prev_row)
    for field in _JSON_FIELDS:
        if field in prev_test and prev_test[field]:
            prev_test[field] = _fast_loads(prev_test[field])

    if fields:
        filtered_curr = {"id": current_test.get("id"), "test_date": current_test.get("test_date")}
        for f in fields:
            if f in current_test:
                filtered_curr[f] = current_test[f]
        curr_obj = filtered_curr
    else:
        curr_obj = current_test

    t_curr = _parse_timestamp(curr_obj.get("test_date"))
    t_prev = _parse_timestamp(prev_test.get("test_date"))

    delta_seconds = None
    delta_hours = None
    delta_days = None
    if t_curr and t_prev:
        delta_seconds = abs((t_curr - t_prev).total_seconds())
        delta_hours = round(delta_seconds / 3600.0, 2)
        delta_days = round(delta_seconds / 86400.0, 3)

    if max_interval_days is not None and delta_days is not None and delta_days > max_interval_days:
        return None

    return {
        "current": curr_obj,
        "previous": prev_test,
        "current_id": curr_obj.get("id"),
        "previous_id": prev_test.get("id"),
        "current_date": curr_obj.get("test_date"),
        "previous_date": prev_test.get("test_date"),
        "interval_seconds": delta_seconds,
        "interval_hours": delta_hours,
        "interval_days": delta_days,
    }


def get_test_by_id(test_id: int) -> Optional[Dict[str, Any]]:
    conn = gereftan_ettesal()
    try:
        cur = conn.execute("SELECT * FROM blood_tests WHERE id = ?", (test_id,))
        row = cur.fetchone()
        if not row:
            return None
        rec = dict(row)
        for field in _JSON_FIELDS:
            if rec.get(field):
                rec[field] = _fast_loads(rec[field])
        return rec
    finally:
        conn.close()


def delete_test(test_id: int, user_id: int) -> bool:
    conn = gereftan_ettesal()
    c = conn.cursor()
    c.execute('DELETE FROM blood_tests WHERE id = ? AND user_id = ?',
              (test_id, user_id))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted


def rahandazi_chat_jadval() -> None:
    init_db()


def zakhire_chat_neshast(user_id: int, messages: List[Dict], title: str = '',
                      language: str = "en",
                      analysis_id: Optional[int] = None,
                      summary: str = '',
                      session_id: Optional[int] = None) -> int:
    conn = gereftan_ettesal()
    c = conn.cursor()
    blob = _fast_dumps(messages or [])
    try:
        if session_id:
            c.execute('''UPDATE chat_sessions
                         SET messages=?, title=?, language=?, analysis_id=?,
                             summary=?, updated_at=CURRENT_TIMESTAMP
                         WHERE id=? AND user_id=?''',
                      (blob, title or "Chat", language, analysis_id,
                       summary or "", session_id, user_id))
            if c.rowcount > 0:
                conn.commit()
                return session_id
        c.execute('''INSERT INTO chat_sessions
                     (user_id, analysis_id, title, language, messages, summary)
                     VALUES (?,?,?,?,?,?)''',
                  (user_id, analysis_id, title or "Chat", language, blob,
                   summary or ''))
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()


def neshast_haye_karbar(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    conn = gereftan_ettesal()
    c = conn.cursor()
    c.execute('''SELECT id, analysis_id, title, language, created_at, updated_at,
                        LENGTH(messages) as msg_size, summary
                 FROM chat_sessions WHERE user_id = ?
                 ORDER BY updated_at DESC LIMIT ?''', (user_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def neshast_ba_shenase(session_id: int,
                           user_id: int) -> Optional[Dict[str, Any]]:
    conn = gereftan_ettesal()
    try:
        cur = conn.execute('SELECT * FROM chat_sessions WHERE id=? AND user_id=?',
                           (session_id, user_id))
        row = cur.fetchone()
        if not row:
            return None
        rec = dict(row)
        if rec.get("messages"):
            try:
                rec["messages"] = _fast_loads(rec["messages"])
            except Exception:
                rec["messages"] = []
        return rec
    finally:
        conn.close()


def hazf_chat_neshast(session_id: int, user_id: int) -> bool:
    conn = gereftan_ettesal()
    c = conn.cursor()
    c.execute("DELETE FROM chat_sessions WHERE id=? AND user_id=?",
              (session_id, user_id))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted


def shenase_neshast_jari(user_id: int,
                                analysis_id: Optional[int]) -> Optional[int]:
    if not analysis_id:
        return None
    conn = gereftan_ettesal()
    try:
        cur = conn.execute('SELECT id FROM chat_sessions WHERE user_id=? AND analysis_id=? LIMIT 1',
                           (user_id, analysis_id))
        row = cur.fetchone()
        return dict(row)["id"] if row else None
    finally:
        conn.close()
