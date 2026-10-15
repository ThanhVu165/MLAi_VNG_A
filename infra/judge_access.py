"""Capability judge offline; quota/ownership bền vững trong settings, không migration.

Issuer chỉ dành cho operator phía server, không được gọi từ form/query. Session là
ngữ cảnh sở hữu ẩn danh, không phải danh tính đã xác thực. C1 không mở provider LIVE.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import secrets
import sqlite3
import time
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime

from infra.db import fetch_one, now_iso, transaction

STATE_KEY = "judge_c1:ledger"
CASE_PREFIX = "judge_c1:case:"
GRANT_TTL_SECONDS = 600
GRANT_REQUEST_LIMIT = 3
SESSION_REQUEST_LIMIT = 10
GLOBAL_REQUEST_LIMIT = 20
GLOBAL_CONCURRENCY = 2
MAX_SENDER_CHARS = 254
MAX_SUBJECT_CHARS = 300
MAX_BODY_CHARS = 5_000
MAX_PAYLOAD_CHARS = 6_000


class JudgeDenied(RuntimeError):
    """Từ chối an toàn, không chứa payload hoặc grant thô."""


@dataclass(frozen=True)
class JudgeGrant:
    token: str = field(repr=False)


@dataclass(frozen=True)
class _Lease:
    grant_hash: str
    session_hash: str
    case_id: str
    payload_hash: str


_ACTIVE: ContextVar[_Lease | None] = ContextVar("judge_c1_lease", default=None)


def enabled() -> bool:
    return os.getenv("JUDGE_INPUT_ENABLED", "0") == "1"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _valid_count(value: object) -> bool:
    return type(value) is int and value >= 0


def _validate_state(state: object) -> None:
    valid = isinstance(state, dict) and set(state) == {"grants", "sessions", "total", "active"}
    if not valid or not all(
        isinstance(state[key], dict) for key in ("grants", "sessions", "active")
    ):
        raise JudgeDenied("Kho quyền judge không hợp lệ; hãy liên hệ người vận hành.")
    if not _valid_count(state["total"]) or not all(
        _valid_count(n) for n in state["sessions"].values()
    ):
        raise JudgeDenied("Hạn mức judge không hợp lệ.")
    for key, record in state["grants"].items():
        if (
            not isinstance(key, str)
            or not isinstance(record, dict)
            or set(record) != {"session", "expires", "count", "nonces"}
            or not isinstance(record["session"], str)
            or type(record["expires"]) not in (int, float)
            or not math.isfinite(record["expires"])
            or not _valid_count(record["count"])
            or not isinstance(record["nonces"], list)
            or not all(isinstance(n, str) for n in record["nonces"])
            or record["count"] != len(record["nonces"])
        ):
            raise JudgeDenied("Grant trong kho quyền không hợp lệ.")
    if (
        sum(state["sessions"].values()) != state["total"]
        or sum(g["count"] for g in state["grants"].values()) != state["total"]
        or not all(isinstance(k, str) and isinstance(v, str) for k, v in state["active"].items())
    ):
        raise JudgeDenied("Ledger judge không nhất quán.")


def _load(connection: sqlite3.Connection) -> dict:
    row = connection.execute("SELECT value FROM settings WHERE key = ?", (STATE_KEY,)).fetchone()
    if row is None:
        if connection.execute(
            "SELECT 1 FROM settings WHERE key LIKE 'judge_c1:case:%' LIMIT 1"
        ).fetchone():
            raise JudgeDenied("Ledger judge bị mất; không tự cấp lại ngân sách.")
        return {"grants": {}, "sessions": {}, "total": 0, "active": {}}
    state = json.loads(row["value"])
    _validate_state(state)
    return state


def _save(connection: sqlite3.Connection, state: dict) -> None:
    _validate_state(state)
    connection.execute(
        "INSERT INTO settings(key,value,updated_at,actor) VALUES(?,?,?,'SYSTEM') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (STATE_KEY, json.dumps(state), now_iso()),
    )


def _grant(state: dict, grant: object, session: object) -> tuple[str, dict]:
    if not enabled() or not isinstance(grant, JudgeGrant) or not isinstance(grant.token, str):
        raise JudgeDenied("Quyền nhập judge chưa được bật hoặc không hợp lệ.")
    if not isinstance(session, str) or not session or len(session) > 256:
        raise JudgeDenied("Phiên judge không hợp lệ.")
    key = _hash(grant.token)
    record = state["grants"].get(key)
    if not record or record["session"] != _hash(session) or record["expires"] <= time.time():
        raise JudgeDenied("Quyền judge không hợp lệ hoặc đã hết hạn.")
    return key, record


def issue_grant(session: str, operator_secret: str) -> JudgeGrant:
    """Operator cấp grant riêng cho session; không có caller phát hành từ UI."""
    configured = os.getenv("JUDGE_ISSUER_SECRET", "")
    if (
        not enabled()
        or len(configured) < 32
        or not hmac.compare_digest(configured, operator_secret)
    ):
        raise JudgeDenied("Không có quyền cấp grant judge.")
    if not isinstance(session, str) or not session or len(session) > 256:
        raise JudgeDenied("Phiên judge không hợp lệ.")
    grant = JudgeGrant(secrets.token_urlsafe(32))
    with transaction() as connection:
        state = _load(connection)
        if state["total"] >= GLOBAL_REQUEST_LIMIT or len(state["grants"]) >= GLOBAL_REQUEST_LIMIT:
            raise JudgeDenied("Đã hết ngân sách judge toàn cục.")
        state["grants"][_hash(grant.token)] = {
            "session": _hash(session),
            "expires": time.time() + GRANT_TTL_SECONDS,
            "count": 0,
            "nonces": [],
        }
        _save(connection, state)
    return grant


def validate_text(sender: object, subject: object, body: object) -> None:
    values = (sender, subject, body)
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError("Hãy nhập đủ người gửi, tiêu đề và nội dung dạng văn bản.")
    for value, limit in zip(values, (MAX_SENDER_CHARS, MAX_SUBJECT_CHARS, MAX_BODY_CHARS)):
        if len(value) > limit or unicodedata.normalize("NFC", value) != value:
            raise ValueError("Email vượt giới hạn hoặc chưa chuẩn hóa Unicode NFC.")
        if any(
            unicodedata.category(char) in {"Cs", "Cc"} and char not in "\n\r\t" for char in value
        ):
            raise ValueError("Email chứa ký tự không hợp lệ.")
    if sum(map(len, values)) > MAX_PAYLOAD_CHARS:
        raise ValueError("Tổng email vượt giới hạn cho phép.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.(?:invalid|test)", sender):
        raise ValueError("Chỉ dùng địa chỉ synthetic kết thúc bằng .invalid hoặc .test.")


def payload_hash(sender: str, subject: str, body: str, received_at: datetime) -> str:
    return _hash(json.dumps([sender, subject, body, received_at.isoformat()], ensure_ascii=True))


@contextmanager
def request_scope(
    grant: JudgeGrant, session: str, nonce: str, case_id: str, fingerprint: str
) -> Iterator[None]:
    """Reserve nguyên tử trước pipeline; crash giữ reservation để fail closed."""
    if os.getenv("APP_MODE", "restricted_demo") != "restricted_demo":
        raise JudgeDenied("Judge chỉ được chạy trong Restricted DEMO.")
    if not isinstance(nonce, str) or not 16 <= len(nonce) <= 128:
        raise JudgeDenied("Mã yêu cầu judge không hợp lệ.")
    with transaction() as connection:
        state = _load(connection)
        key, record = _grant(state, grant, session)
        session_hash = _hash(session)
        if (
            _hash(nonce) in record["nonces"]
            or record["count"] >= GRANT_REQUEST_LIMIT
            or state["sessions"].get(session_hash, 0) >= SESSION_REQUEST_LIMIT
            or state["total"] >= GLOBAL_REQUEST_LIMIT
            or len(state["active"]) >= GLOBAL_CONCURRENCY
            or session_hash in state["active"].values()
        ):
            raise JudgeDenied("Yêu cầu trùng, đang xử lý hoặc đã chạm hạn mức judge.")
        record["count"] += 1
        record["nonces"].append(_hash(nonce))
        state["sessions"][session_hash] = state["sessions"].get(session_hash, 0) + 1
        state["total"] += 1
        state["active"][case_id] = session_hash
        connection.execute(
            "INSERT INTO settings(key,value,updated_at,actor) VALUES(?,?,?,'SYSTEM')",
            (CASE_PREFIX + case_id, key, now_iso()),
        )
        _save(connection, state)
    token = _ACTIVE.set(_Lease(key, session_hash, case_id, fingerprint))
    try:
        yield
    finally:
        _ACTIVE.reset(token)
        with transaction() as connection:
            state = _load(connection)
            state["active"].pop(case_id, None)
            _save(connection, state)


def active_case() -> str | None:
    lease = _ACTIVE.get()
    return lease.case_id if lease else None


def check_active() -> None:
    lease = _ACTIVE.get()
    if lease is None or not enabled():
        raise JudgeDenied("Không có reservation judge đang hiệu lực.")
    with transaction() as connection:
        state = _load(connection)
        record = state["grants"].get(lease.grant_hash)
        if (
            not record
            or record["expires"] <= time.time()
            or state["active"].get(lease.case_id) != lease.session_hash
        ):
            raise JudgeDenied("Reservation judge không còn hợp lệ.")


def authorize_payload(sender: str, subject: str, body: str, received_at: datetime) -> bool:
    lease = _ACTIVE.get()
    if lease is None:
        return False
    if not enabled() or payload_hash(sender, subject, body, received_at) != lease.payload_hash:
        raise JudgeDenied("Ngữ cảnh judge không khớp email hoặc đã bị tắt.")
    check_active()
    return True


def is_judge_case(case_id: str) -> bool:
    return fetch_one("SELECT 1 FROM settings WHERE key = ?", (CASE_PREFIX + case_id,)) is not None


def can_read(case_id: str, grant: object, session: object) -> bool:
    try:
        with transaction() as connection:
            state = _load(connection)
            key, _ = _grant(state, grant, session)
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?", (CASE_PREFIX + case_id,)
            ).fetchone()
            return row is not None and hmac.compare_digest(row["value"], key)
    except (JudgeDenied, sqlite3.Error, OSError, ValueError, TypeError, KeyError):
        return False


def grant_is_valid(grant: object, session: object) -> bool:
    try:
        with transaction() as connection:
            _grant(_load(connection), grant, session)
        return True
    except (JudgeDenied, sqlite3.Error, OSError, ValueError, TypeError, KeyError):
        return False
