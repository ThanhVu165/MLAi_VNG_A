"""Admission public phía server; dùng chung ledger Judge, không schema mới."""

from __future__ import annotations

import json
import math
import os
import secrets
import sqlite3
import time

from infra import judge_access as access
from infra.db import now_iso, transaction

STATE_KEY = "public_demo:ledger"
TOKEN_PREFIX = "public."
MARKER_PREFIX = "public:"
SESSION_LIMIT = 10
SESSION_ADMISSION_LIMIT = 100
ADMISSIONS_PER_MINUTE = 10
REQUESTS_PER_MINUTE = 10
SESSION_REQUESTS_PER_MINUTE = 2
WINDOW_SECONDS = 60
TTL_SECONDS = 1800


def enabled() -> bool:
    return os.getenv("JUDGE_PUBLIC_DEMO_ENABLED", "0") == "1"


def require_enabled() -> None:
    if not enabled():
        raise access.JudgeDenied("Public LIVE đang tắt; không nhận email mới.")
    access.require_live_configuration()


def _timestamps(value: object) -> bool:
    return isinstance(value, list) and all(
        type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in value
    )


def _validate(state: object, legacy: dict, markers: dict) -> None:
    if (
        not isinstance(state, dict)
        or set(state) != {"version", "grants", "sessions", "admissions", "requests"}
        or type(state["version"]) is not int
        or state["version"] != 1
        or not isinstance(state["grants"], dict)
        or not isinstance(state["sessions"], dict)
        or len(state["sessions"]) > SESSION_ADMISSION_LIMIT
        or not _timestamps(state["admissions"])
        or not _timestamps(state["requests"])
    ):
        raise ValueError("Invalid public ledger")
    if (
        not all(isinstance(k, str) and _timestamps(v) for k, v in state["sessions"].items())
        or set(markers.values()) != set(state["grants"])
        or len(markers) != len(state["grants"])
    ):
        raise ValueError("Invalid public provenance")
    for key, item in state["grants"].items():
        if (
            not isinstance(item, dict)
            or set(item) != {"quota", "session"}
            or item["quota"] not in state["sessions"]
            or legacy["grants"][key]["session"] != item["session"]
            or markers[MARKER_PREFIX + item["session"]] != key
        ):
            raise ValueError("Invalid public binding")


def check_accounting(connection: sqlite3.Connection) -> None:
    """Chặn xử lý khi usage mơ hồ; không chặn owner đọc kết quả lỗi/Audit."""
    legacy, c2 = access._load(connection), access._load_c2(connection)
    if any(r["phase"] == "HOLD" for r in c2["requests"].values()):
        raise access.JudgeDenied("Có reservation HOLD; Public LIVE chưa sẵn sàng.")
    for attempt in connection.execute(
        "SELECT key,value FROM settings WHERE key LIKE ?", (access.LIVE_ATTEMPT_PREFIX + "%",)
    ):
        try:
            usage = json.loads(attempt["value"])
            access._validate_live_attempts(usage)
        except (ValueError, TypeError, KeyError):
            raise access.JudgeDenied("Ledger usage không hợp lệ; Public LIVE bị chặn.") from None
        case_id = attempt["key"][len(access.LIVE_ATTEMPT_PREFIX) :]
        if usage["blocked"] or (usage["pending"] and case_id not in legacy["active"]):
            raise access.JudgeDenied("Có attempt chưa đối soát; Public LIVE bị chặn.")


def _load(connection: sqlite3.Connection) -> dict:
    legacy, c2 = access._load(connection), access._load_c2(connection)
    markers = {k: v for k, v in c2["provisioned"].items() if k.startswith(MARKER_PREFIX)}
    row = connection.execute("SELECT value FROM settings WHERE key=?", (STATE_KEY,)).fetchone()
    if row is None:
        if markers:
            raise access.JudgeDenied("Thiếu ledger Public LIVE; không tự reset quota.")
        return {"version": 1, "grants": {}, "sessions": {}, "admissions": [], "requests": []}
    try:
        state = json.loads(row["value"])
        _validate(state, legacy, markers)
        return state
    except (ValueError, TypeError, KeyError):
        raise access.JudgeDenied("Ledger Public LIVE không hợp lệ; giữ quyền đóng.") from None


def _save(connection: sqlite3.Connection, state: dict) -> None:
    connection.execute(
        "INSERT INTO settings(key,value,updated_at,actor) VALUES(?,?,?,'SYSTEM') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
        (STATE_KEY, json.dumps(state), now_iso()),
    )


def _window(values: list, now: float) -> list:
    if any(x > now for x in values):
        raise access.JudgeDenied("Đồng hồ admission không nhất quán; thử lại sau.")
    return [x for x in values if now - x < WINDOW_SECONDS]


def admit(session: str, server_session_id: str) -> access.JudgeGrant:
    """Chỉ gateway gọi với binding server; ID chỉ giữ quota, không cấp quyền đọc."""
    require_enabled()
    if not all(isinstance(v, str) and 0 < len(v) <= 256 for v in (session, server_session_id)):
        raise access.JudgeDenied("Không xác minh được phiên public.")
    now = time.time()
    quota, session_hash = access._hash(server_session_id), access._hash(session)
    with transaction() as connection:
        check_accounting(connection)
        state = _load(connection)
        legacy, c2 = access._load(connection), access._load_c2(connection)
        if MARKER_PREFIX + session_hash in c2["provisioned"]:
            raise access.JudgeDenied("Binding public đã được cấp; không cấp lại.")
        if any(
            key in c2["revoked"] for key, item in state["grants"].items() if item["quota"] == quota
        ):
            raise access.JudgeDenied("Phiên public đã bị thu hồi; không tự cấp lại khi reconnect.")
        recent = _window(state["admissions"], now)
        if len(recent) >= ADMISSIONS_PER_MINUTE:
            raise access.JudgeDenied("Public LIVE đang nhận nhiều phiên; hãy thử lại sau một phút.")
        if quota not in state["sessions"] and len(state["sessions"]) >= SESSION_ADMISSION_LIMIT:
            raise access.JudgeDenied("Đã đạt hạn mức admission Public LIVE.")
        if len(legacy["grants"]) >= access.GLOBAL_REQUEST_LIMIT:
            raise access.JudgeDenied("Đã đạt hạn mức grant toàn ứng dụng.")
        token = TOKEN_PREFIX + secrets.token_urlsafe(32)
        key = access._hash(token)
        legacy["grants"][key] = {
            "session": session_hash,
            "expires": now + TTL_SECONDS,
            "count": 0,
            "nonces": [],
        }
        state["sessions"].setdefault(quota, [])
        state["grants"][key] = {"quota": quota, "session": session_hash}
        state["admissions"] = recent + [now]
        c2["provisioned"][MARKER_PREFIX + session_hash] = key
        access._save(connection, legacy)
        access._save_c2(connection, c2)
        _save(connection, state)
    return access.JudgeGrant(token)


def validate_grant(connection: sqlite3.Connection, key: str) -> None:
    if key not in _load(connection)["grants"]:
        raise access.JudgeDenied("Không có provenance cho grant public.")


def reserve(connection: sqlite3.Connection, key: str) -> None:
    """Quota/rate/concurrency public nằm trong cùng transaction debit Judge."""
    require_enabled()
    check_accounting(connection)
    state, legacy = _load(connection), access._load(connection)
    quota = state["grants"][key]["quota"]
    keys = [k for k, v in state["grants"].items() if v["quota"] == quota]
    if sum(legacy["grants"][k]["count"] for k in keys) >= SESSION_LIMIT:
        raise access.JudgeDenied("Phiên public đã dùng đủ 10 email.")
    bindings = {state["grants"][k]["session"] for k in keys}
    if bindings.intersection(legacy["active"].values()):
        raise access.JudgeDenied("Phiên public đang xử lý một email.")
    now = time.time()
    recent = _window(state["requests"], now)
    per_session = _window(state["sessions"][quota], now)
    if len(recent) >= REQUESTS_PER_MINUTE or len(per_session) >= SESSION_REQUESTS_PER_MINUTE:
        raise access.JudgeDenied("Public LIVE đang giới hạn tốc độ; hãy thử lại sau một phút.")
    state["requests"], state["sessions"][quota] = recent + [now], per_session + [now]
    _save(connection, state)
