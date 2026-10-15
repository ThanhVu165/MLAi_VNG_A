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

# Envelope dự toán offline cho tối đa 3 attempts; chưa là usage hoặc provider hard cap.
C2_STATE_KEY = "judge_c2a:ledger"
C2_ANCHOR_KEY = "judge_c2a:initialized"
CASE_INPUT_TOKEN_RESERVATION = 24_000
CASE_OUTPUT_TOKEN_RESERVATION = 6_000
SESSION_TOKEN_RESERVATION_LIMIT = 300_000
GLOBAL_TOKEN_RESERVATION_LIMIT = 600_000
CASE_ESTIMATE_MICRO_USD = 10_000
SESSION_ESTIMATE_MICRO_USD_LIMIT = 100_000
GLOBAL_ESTIMATE_MICRO_USD_LIMIT = 200_000
_C2_PHASES = {"RESERVED", "PROCESSING", "FINISHED", "HOLD", "RECOVERED"}


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
    _check_revocation(key)
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


def _require_operator(operator_secret: str) -> None:
    configured = os.getenv("JUDGE_ISSUER_SECRET", "")
    if (
        not isinstance(operator_secret, str)
        or len(configured) < 32
        or not hmac.compare_digest(configured, operator_secret)
    ):
        raise JudgeDenied("Không có quyền vận hành judge.")


def _reservation_record(grant_hash: str, session_hash: str, phase: str) -> dict:
    return {
        "grant": grant_hash,
        "session": session_hash,
        "phase": phase,
        "input_tokens": CASE_INPUT_TOKEN_RESERVATION,
        "output_tokens": CASE_OUTPUT_TOKEN_RESERVATION,
        "estimated_micro_usd": CASE_ESTIMATE_MICRO_USD,
    }


def _validate_c2(state: object) -> None:
    if (
        not isinstance(state, dict)
        or set(state) != {"version", "provisioned", "revoked", "requests"}
        or type(state["version"]) is not int
        or state["version"] != 1
        or not isinstance(state["provisioned"], dict)
        or not isinstance(state["revoked"], list)
        or not isinstance(state["requests"], dict)
    ):
        raise JudgeDenied("Ledger C2-A không hợp lệ; giữ HOLD.")
    if not all(
        isinstance(k, str) and isinstance(v, str) for k, v in state["provisioned"].items()
    ) or not all(isinstance(v, str) for v in state["revoked"]):
        raise JudgeDenied("Provenance C2-A không hợp lệ; giữ HOLD.")
    for case_id, record in state["requests"].items():
        if (
            not isinstance(case_id, str)
            or not isinstance(record, dict)
            or set(record)
            != {"grant", "session", "phase", "input_tokens", "output_tokens", "estimated_micro_usd"}
            or not isinstance(record["grant"], str)
            or not isinstance(record["session"], str)
            or record["phase"] not in _C2_PHASES
            or any(
                not _valid_count(record[k])
                for k in ("input_tokens", "output_tokens", "estimated_micro_usd")
            )
        ):
            raise JudgeDenied("Reservation C2-A không hợp lệ; giữ HOLD.")


def _load_c2(connection: sqlite3.Connection) -> dict:
    row = connection.execute("SELECT value FROM settings WHERE key=?", (C2_STATE_KEY,)).fetchone()
    if row is not None:
        try:
            state = json.loads(row["value"])
            _validate_c2(state)
        except (ValueError, TypeError, KeyError):
            raise JudgeDenied("Không đọc được ledger C2-A; giữ HOLD.") from None
        legacy = _load(connection)
        markers = {
            r["key"][len(CASE_PREFIX) :]: r["value"]
            for r in connection.execute(
                "SELECT key,value FROM settings WHERE key LIKE 'judge_c1:case:%'"
            )
        }
        if (
            len(state["requests"]) != legacy["total"]
            or set(markers) != set(state["requests"])
            or any(
                r["grant"] != markers[k]
                or r["grant"] not in legacy["grants"]
                or r["session"] != legacy["grants"][r["grant"]]["session"]
                for k, r in state["requests"].items()
            )
        ):
            raise JudgeDenied("Không đối soát được ledger C2-A; giữ HOLD.")
        return state
    if connection.execute("SELECT 1 FROM settings WHERE key=?", (C2_ANCHOR_KEY,)).fetchone():
        raise JudgeDenied("Ledger C2-A bị mất; không tự cấp lại quyền hoặc budget.")
    # Nâng dữ liệu JSON nội bộ, không migration/schema; debit bảo thủ toàn bộ case C1 cũ.
    legacy = _load(connection)
    state = {"version": 1, "provisioned": {}, "revoked": [], "requests": {}}
    for row in connection.execute(
        "SELECT key,value FROM settings WHERE key LIKE 'judge_c1:case:%'"
    ):
        grant = legacy["grants"].get(row["value"])
        if grant is None:
            raise JudgeDenied("Provenance C1 cũ không rõ; giữ HOLD.")
        state["requests"][row["key"][len(CASE_PREFIX) :]] = _reservation_record(
            row["value"], grant["session"], "HOLD"
        )
    if len(state["requests"]) != legacy["total"]:
        raise JudgeDenied("Không đối soát được ngân sách C1 cũ; giữ HOLD.")
    return state


def _save_c2(connection: sqlite3.Connection, state: dict) -> None:
    _validate_c2(state)
    connection.execute(
        "INSERT INTO settings(key,value,updated_at,actor) VALUES(?,?,?,'SYSTEM') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
        (C2_STATE_KEY, json.dumps(state), now_iso()),
    )
    connection.execute(
        "INSERT OR IGNORE INTO settings(key,value,updated_at,actor) VALUES(?,'1',?,'SYSTEM')",
        (C2_ANCHOR_KEY, now_iso()),
    )


def _check_revocation(grant_hash: str) -> None:
    with transaction() as connection:
        state = _load_c2(connection)
        if grant_hash in state["revoked"]:
            raise JudgeDenied("Grant judge đã bị thu hồi.")


def provision_grant(session: str, operator_secret: str, provisioning_id: str) -> JudgeGrant:
    """Cấp một lần phía server; refresh/replay ID không phát hành thêm grant."""
    _require_operator(operator_secret)
    if not isinstance(provisioning_id, str) or not 16 <= len(provisioning_id) <= 128:
        raise JudgeDenied("Mã provisioning không hợp lệ.")
    with transaction() as connection:
        state = _load_c2(connection)
        key = _hash(provisioning_id)
        if key in state["provisioned"]:
            raise JudgeDenied("Lần provisioning này đã dùng; không cấp lại quyền.")
        grant = issue_grant(session, operator_secret)
        state["provisioned"][key] = _hash(grant.token)
        _save_c2(connection, state)
    return grant


def revoke_grant(grant: JudgeGrant, operator_secret: str) -> None:
    """Thu hồi bền vững; hoạt động cả khi kill switch đã OFF, không hoàn quota."""
    _require_operator(operator_secret)
    if not isinstance(grant, JudgeGrant) or not isinstance(grant.token, str):
        raise JudgeDenied("Grant không hợp lệ.")
    with transaction() as connection:
        if _hash(grant.token) not in _load(connection)["grants"]:
            raise JudgeDenied("Không tìm thấy grant được cấp.")
        state = _load_c2(connection)
        if _hash(grant.token) not in state["revoked"]:
            state["revoked"].append(_hash(grant.token))
        _save_c2(connection, state)


def _reserve_budget(connection: sqlite3.Connection, case_id: str, key: str, session: str) -> None:
    state = _load_c2(connection)
    if case_id in state["requests"]:
        raise JudgeDenied("Case đã có reservation; không xử lý lặp.")
    record = _reservation_record(key, session, "RESERVED")
    all_records = list(state["requests"].values())
    same_session = [r for r in all_records if r["session"] == session]
    for records, token_limit, cost_limit in (
        (all_records, GLOBAL_TOKEN_RESERVATION_LIMIT, GLOBAL_ESTIMATE_MICRO_USD_LIMIT),
        (same_session, SESSION_TOKEN_RESERVATION_LIMIT, SESSION_ESTIMATE_MICRO_USD_LIMIT),
    ):
        tokens = sum(r["input_tokens"] + r["output_tokens"] for r in records)
        cost = sum(r["estimated_micro_usd"] for r in records)
        if (
            tokens + record["input_tokens"] + record["output_tokens"] > token_limit
            or cost + record["estimated_micro_usd"] > cost_limit
        ):
            raise JudgeDenied("Không đủ ngân sách reservation judge.")
    state["requests"][case_id] = record
    _save_c2(connection, state)


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
        _reserve_budget(connection, case_id, key, session_hash)
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
            c2 = _load_c2(connection)
            if c2["requests"][case_id]["phase"] == "PROCESSING" and not _terminal_snapshot_matches(
                connection, case_id
            ):
                c2["requests"][case_id]["phase"] = "HOLD"
            if c2["requests"][case_id]["phase"] != "HOLD":
                state["active"].pop(case_id, None)
            if c2["requests"][case_id]["phase"] not in {"HOLD", "RECOVERED"}:
                c2["requests"][case_id]["phase"] = "FINISHED"
            _save_c2(connection, c2)
            _save(connection, state)


def active_case() -> str | None:
    lease = _ACTIVE.get()
    return lease.case_id if lease else None


def check_active() -> None:
    lease = _ACTIVE.get()
    if lease is None or not enabled():
        raise JudgeDenied("Không có reservation judge đang hiệu lực.")
    with transaction() as connection:
        _check_revocation(lease.grant_hash)
        request = _load_c2(connection)["requests"].get(lease.case_id)
        state = _load(connection)
        record = state["grants"].get(lease.grant_hash)
        if (
            not record
            or record["expires"] <= time.time()
            or state["active"].get(lease.case_id) != lease.session_hash
            or request is None
            or request["phase"] not in {"RESERVED", "PROCESSING"}
        ):
            raise JudgeDenied("Reservation judge không còn hợp lệ.")


def mark_processing() -> None:
    """Ghi nhận trước pipeline, không khôi phục request mơ hồ bằng cách gọi lại AI."""
    check_active()
    with transaction() as connection:
        c2 = _load_c2(connection)
        case_id = active_case()
        record = c2["requests"].get(case_id)
        if not record or record["phase"] != "RESERVED":
            raise JudgeDenied("Reservation không ở trạng thái bắt đầu xử lý.")
        record["phase"] = "PROCESSING"
        _save_c2(connection, c2)


def recover_reservations(operator_secret: str) -> dict[str, str]:
    """Chỉ nhả slot khi snapshot terminal đối soát được; quota/budget luôn giữ debit."""
    _require_operator(operator_secret)
    outcomes: dict[str, str] = {}
    with transaction() as connection:
        state, c2 = _load(connection), _load_c2(connection)
        for case_id in list(state["active"]):
            record = c2["requests"].get(case_id)
            if record is None:
                raise JudgeDenied("Không có reservation recovery; giữ HOLD.")
            terminal = _terminal_snapshot_matches(connection, case_id)
            record["phase"] = "RECOVERED" if terminal else "HOLD"
            outcomes[case_id] = record["phase"]
            if terminal:
                state["active"].pop(case_id)
        _save_c2(connection, c2)
        _save(connection, state)
    return outcomes


def _terminal_snapshot_matches(connection: sqlite3.Connection, case_id: str) -> bool:
    # Import trễ để dùng đúng reader/decoder mà không tạo vòng import lúc khởi động.
    from core.results import load_result

    case = connection.execute(
        "SELECT status,send_deadline FROM cases WHERE case_id=?", (case_id,)
    ).fetchone()
    snapshot = connection.execute(
        "SELECT payload_json FROM case_results WHERE case_id=?", (case_id,)
    ).fetchone()
    if (
        not case
        or not snapshot
        or case["status"] not in {"PREVIEW_READY", "AWAITING_HUMAN", "ERROR", "INVALID_INPUT"}
    ):
        return False
    try:
        payload = json.loads(snapshot["payload_json"])
        if payload["case_id"] != case_id or payload["status"] != case["status"]:
            return False
        decision = connection.execute(
            "SELECT decision,escalation_type,rule_id FROM decisions WHERE case_id=? ORDER BY rowid DESC LIMIT 1",
            (case_id,),
        ).fetchone()
        expected = {
            "PREVIEW_READY": "AUTO_REPLY",
            "AWAITING_HUMAN": "ESCALATE",
            "ERROR": "ERROR",
            "INVALID_INPUT": "INVALID_INPUT",
        }
        if (
            decision is None
            or decision["decision"] != expected[case["status"]]
            or any(
                payload["decision"][k] != decision[k]
                for k in ("decision", "escalation_type", "rule_id")
            )
        ):
            return False
        # fetch_one của reader dùng cùng transaction; không fallback khi snapshot hỏng.
        result = load_result(case_id)
        if result is None or result.case_id != case_id or result.status.value != case["status"]:
            return False
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, OverflowError):
        return False
    sends = connection.execute(
        "SELECT 1 FROM audit_events WHERE case_id=? AND action IN ('SEND_SCHEDULED','SEND_DISPATCHED')",
        (case_id,),
    ).fetchone()
    jobs = connection.execute("SELECT 1 FROM case_jobs WHERE case_id=?", (case_id,)).fetchone()
    return case["send_deadline"] is None and sends is None and jobs is None


def authorize_payload(sender: str, subject: str, body: str, received_at: datetime) -> bool:
    lease = _ACTIVE.get()
    if lease is None:
        return False
    if not enabled() or payload_hash(sender, subject, body, received_at) != lease.payload_hash:
        raise JudgeDenied("Ngữ cảnh judge không khớp email hoặc đã bị tắt.")
    check_active()
    # Caller server dùng scope trực tiếp vẫn phải đánh dấu PROCESSING trước intake/provider.
    with transaction() as connection:
        c2 = _load_c2(connection)
        if c2["requests"][lease.case_id]["phase"] == "RESERVED":
            c2["requests"][lease.case_id]["phase"] = "PROCESSING"
            _save_c2(connection, c2)
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
