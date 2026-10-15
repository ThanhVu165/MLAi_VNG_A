"""Gateway judge local: capability chỉ nằm trong registry server, không qua widget/URL.

Không dùng session_state hoặc query để xác định session C2-B. Operator dùng Unix socket
trong thư mục riêng 0700 và secret server; không có HTTP/authentication public.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import socket
import stat
from threading import RLock, Thread

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from core.judge_input import process_judge_case
from core.types import CaseInput, PipelineResult
from infra import judge_access as access
from infra.db import transaction

_MAX_MESSAGE = 4096
_MAX_SESSIONS = 100
_TIMEOUT_SECONDS = 3
_KEY = "JUDGE_GATEWAY_SOCKET"
_LOCK = RLock()
_BINDINGS: dict[str, dict] = {}
_LISTENER: socket.socket | None = None


def configured() -> bool:
    return bool(os.getenv(_KEY, ""))


def _offline() -> None:
    if (
        os.getenv("APP_MODE", "restricted_demo") != "restricted_demo"
        or os.getenv("LLM_MODE", "live").lower() != "replay"
    ):
        raise access.JudgeDenied("Gateway chỉ hoạt động trong restricted replay offline.")


def _current() -> dict | None:
    context = get_script_run_ctx(suppress_warning=True)
    if context is None:
        return None
    # session_id do Streamlit server tạo, không lấy từ session_state/query/browser input.
    return _BINDINGS.get(context.session_id)


def prepare_session() -> str | None:
    """Đăng ký session chưa có quyền; trả mã đối chiếu không phải capability."""
    if not configured():
        return None
    _offline()
    _start_listener()
    context = get_script_run_ctx(suppress_warning=True)
    if context is None:
        raise access.JudgeDenied("Không có phiên server hợp lệ.")
    with _LOCK:
        if context.session_id not in _BINDINGS:
            if len(_BINDINGS) >= _MAX_SESSIONS:
                raise access.JudgeDenied("Gateway đã đầy; cần operator kiểm tra.")
            _BINDINGS[context.session_id] = {
                "reference": secrets.token_hex(8),
                "session": secrets.token_urlsafe(32),
                "grant": None,
                "provisioned": False,
            }
        return _BINDINGS[context.session_id]["reference"]


def _credentials() -> tuple[object, object]:
    if configured():
        _offline()
        with _LOCK:
            record = _current()
            return (record["grant"], record["session"]) if record else (None, None)
    # Giữ seam C1 server-only khi gateway chưa được cấu hình; không tạo issuer UI.
    return st.session_state.get("judge_grant"), st.session_state.get("judge_session")


def grant_valid() -> bool:
    try:
        return access.grant_is_valid(*_credentials())
    except access.JudgeDenied:
        return False


def can_read(case_id: str) -> bool:
    try:
        grant, session = _credentials()
        return access.can_read(case_id, grant, session)
    except access.JudgeDenied:
        return False


def submit(inp: CaseInput) -> PipelineResult:
    grant, session = _credentials()
    return process_judge_case(inp, grant=grant, session=session, nonce=secrets.token_urlsafe(24))


def _operate(message: dict) -> dict:
    """Chỉ gọi bởi IPC local; không expose qua Streamlit widget hoặc HTTP."""
    secret = message.get("secret")
    access._require_operator(secret)
    _offline()
    operation = message.get("operation")
    with _LOCK:
        if operation == "sessions":
            return {"sessions": [r["reference"] for r in _BINDINGS.values()]}
        if operation == "holds":
            with transaction() as connection:
                state = access._load_c2(connection)
                return {"holds": {k: r["phase"] for k, r in state["requests"].items()}}
        if operation == "recover":
            return {"recovery": access.recover_reservations(secret)}
        record = next(
            (r for r in _BINDINGS.values() if r["reference"] == message.get("reference")), None
        )
        if record is None:
            raise access.JudgeDenied("Không có session server tương ứng.")
        if operation == "provision":
            if record["provisioned"]:
                raise access.JudgeDenied("Session đã được cấp; không cấp lại sau reload/revoke.")
            grant = access.provision_grant(record["session"], secret, message.get("request_id"))
            record["grant"], record["provisioned"] = grant, True
        elif operation == "revoke":
            access.revoke_grant(record["grant"], secret)
        else:
            raise access.JudgeDenied("Thao tác operator không hợp lệ.")
    return {"ok": True}


def _receive(connection: socket.socket) -> dict:
    connection.settimeout(_TIMEOUT_SECONDS)
    payload = bytearray()
    while not payload.endswith(b"\n"):
        chunk = connection.recv(_MAX_MESSAGE + 1 - len(payload))
        if not chunk or len(payload) + len(chunk) > _MAX_MESSAGE:
            raise ValueError("Invalid IPC envelope")
        payload.extend(chunk)
    message = json.loads(payload)
    if not isinstance(message, dict):
        raise ValueError("Invalid IPC object")
    return message


def _serve_connection(connection: socket.socket) -> None:
    with connection:
        try:
            response = _operate(_receive(connection))
        except (Exception,):
            # Không echo exception/payload/secret; lỗi operator không tạo quyền.
            response = {"ok": False, "error": "Yêu cầu operator bị từ chối; kiểm tra phía server."}
        try:
            connection.sendall(json.dumps(response).encode("utf-8") + b"\n")
        except OSError:
            # Mất response không rollback quyền đã persist hoặc tự retry provisioning.
            return


def _listen(listener: socket.socket) -> None:
    while True:
        try:
            connection, _ = listener.accept()
        except OSError:
            return
        _serve_connection(connection)


def _start_listener() -> None:
    global _LISTENER
    with _LOCK:
        if _LISTENER is not None:
            return
        path = Path(os.environ[_KEY])
        parent = path.parent
        metadata = parent.lstat()
        if (
            not path.is_absolute()
            or parent.resolve() != parent
            or not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700
            or path.exists()
            or path.is_symlink()
        ):
            raise access.JudgeDenied("Socket cần thư mục riêng 0700; không ghi đè socket cũ.")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(path))
            path.chmod(0o600)
            listener.listen(4)
        except OSError:
            listener.close()
            raise access.JudgeDenied("Không mở được kênh operator local.") from None
        _LISTENER = listener
        Thread(target=_listen, args=(listener,), daemon=True, name="judge-local-operator").start()
