"""C2-B gateway/local staging, synthetic SQLite, không network/provider thật."""

import asyncio
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

import pytest
from streamlit.runtime.app_session import AppSession
from streamlit.runtime.memory_session_storage import MemorySessionStorage
from streamlit.runtime.memory_uploaded_file_manager import MemoryUploadedFileManager
from streamlit.runtime.script_data import ScriptData
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
from streamlit.runtime.websocket_session_manager import WebsocketSessionManager
from streamlit.testing.v1 import AppTest
from streamlit.web.server.browser_websocket_handler import BrowserWebSocketHandler

from infra import db, judge_access as access
from ui import judge_gateway as gateway
from test_judge_input_c1 import SECRET, _input, _provider
from test_judge_input_c1 import judge as _judge_fixture

judge = _judge_fixture
_REAL_START = gateway._start_listener


@pytest.fixture
def session(judge, monkeypatch):
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/unopened/offline.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    context = SimpleNamespace(session_id="server-session-a", connection="connection-a")
    monkeypatch.setattr(gateway, "get_script_run_ctx", lambda **kwargs: context)
    monkeypatch.setattr(gateway, "_connection_fingerprint", lambda: context.connection)
    return context, gateway.prepare_session()


def _operator(operation, reference=None, request_id="c2b-provision-once-0001", secret=SECRET):
    return gateway._operate(
        dict(operation=operation, reference=reference, request_id=request_id, secret=secret)
    )


def _ledger():
    with db.transaction() as connection:
        return access._load(connection), access._load_c2(connection)


def test_guest_forgery_and_cross_session_denied(session, monkeypatch):
    context, reference = session
    before = _ledger()
    for operation in ("sessions", "holds", "recover", "provision", "revoke"):
        with pytest.raises(access.JudgeDenied):
            _operator(operation, reference, secret="guest")
    assert _ledger() == before
    assert not gateway.grant_valid()
    with pytest.raises(access.JudgeDenied):
        gateway.submit(_input())
    _operator("provision", reference)
    _provider(monkeypatch)
    result = gateway.submit(_input())
    assert result.status.value == "PREVIEW_READY"
    assert gateway.can_read(result.case_id)
    context.session_id = "server-session-b"
    context.connection = "connection-b"
    gateway.prepare_session()
    assert not gateway.grant_valid() and not gateway.can_read(result.case_id)
    # C2-B không tin credential/state/query do caller giả mạo.
    monkeypatch.setattr(
        gateway.st,
        "session_state",
        {"judge_grant": access.JudgeGrant("forged"), "judge_session": "server-session-a"},
    )
    assert not gateway.grant_valid()
    with pytest.raises(access.JudgeDenied):
        gateway.submit(_input())


def test_rerun_replay_restart_never_reissues_or_resets(session, monkeypatch):
    context, reference = session
    _operator("provision", reference)
    _provider(monkeypatch)
    gateway.submit(_input())
    before = _ledger()
    assert gateway.prepare_session() == reference
    with pytest.raises(access.JudgeDenied):
        _operator("provision", reference, request_id="another-operator-request")
    assert _ledger() == before
    # Browser reload tạo session mới; không kế thừa quyền bằng mã đối chiếu cũ.
    context.session_id = "reloaded-server-session"
    context.connection = "reloaded-connection"
    new_reference = gateway.prepare_session()
    assert new_reference != reference and not gateway.grant_valid()
    with pytest.raises(access.JudgeDenied):
        _operator("provision", new_reference)
    assert _ledger() == before
    # Process restart làm mất registry, không tạo lại grant/budget từ DB.
    gateway._BINDINGS.clear()
    assert gateway.prepare_session() != new_reference
    assert not gateway.grant_valid()
    assert _ledger() == before


@pytest.mark.parametrize("action", ["expired", "revoke", "kill", "live", "private"])
def test_expiry_revocation_kill_and_modes_fail_closed(session, monkeypatch, action):
    _, reference = session
    _operator("provision", reference)
    if action == "expired":
        monkeypatch.setattr(access.time, "time", lambda: 99_999_999_999)
    elif action == "revoke":
        _operator("revoke", reference)
    elif action == "kill":
        monkeypatch.setenv("JUDGE_INPUT_ENABLED", "0")
        _operator("revoke", reference)
    elif action == "live":
        monkeypatch.setenv("LLM_MODE", "live")
    else:
        monkeypatch.setenv("APP_MODE", "private")
    before = _ledger()
    assert not gateway.grant_valid()
    with pytest.raises(access.JudgeDenied):
        gateway.submit(_input())
    assert _ledger() == before
    assert not db.fetch_all("SELECT * FROM cases")


def test_hold_operator_inspection_recovery_does_not_process_or_send(session, monkeypatch):
    _, reference = session
    _operator("provision", reference)
    grant, server_session = gateway._credentials()
    inp = _input()
    fingerprint = access.payload_hash(inp.sender, inp.subject, inp.body, inp.received_at)
    with access.request_scope(grant, server_session, "c2b-hold-nonce-0001", "c_hold", fingerprint):
        access.mark_processing()
        _operator("revoke", reference)
        assert _operator("recover") == {"recovery": {"c_hold": "HOLD"}}
        assert _operator("holds") == {"holds": {"c_hold": "HOLD"}}
    before = _ledger()
    assert _operator("recover") == {"recovery": {"c_hold": "HOLD"}}
    assert _ledger() == before
    assert not db.fetch_all("SELECT * FROM cases")
    assert not db.fetch_all("SELECT * FROM audit_events")
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert "c_hold" in before[0]["active"]


def test_operator_concurrency_and_unknown_actions_do_not_reissue(session):
    _, reference = session
    before = _ledger()[0]

    def attempt(index):
        try:
            _operator("provision", reference, request_id=f"parallel-operation-{index:04}")
            return True
        except access.JudgeDenied:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(8))) == 1
    state = _ledger()
    assert len(state[0]["grants"]) == len(before["grants"]) + 1
    with pytest.raises(access.JudgeDenied):
        _operator("unknown", reference)
    with pytest.raises(access.JudgeDenied):
        _operator("provision", "forged-reference")
    assert _ledger() == state
    grant = gateway._credentials()[0]
    assert grant.token not in str(_operator("sessions"))
    assert grant.token not in str(_operator("holds"))


def test_ui_rerun_binding_and_audit_ownership(judge, monkeypatch, caplog):
    get_context = gateway.get_script_run_ctx

    def test_context(**kwargs):
        context = get_context(**kwargs)
        # AppTest gán cùng literal session_id cho mọi browser giả lập. Phân biệt các
        # context server của harness; không dùng key do widget/query cung cấp.
        return SimpleNamespace(session_id=str(id(context.session_state._state)))

    monkeypatch.setattr(gateway, "get_script_run_ctx", test_context)
    monkeypatch.setattr(gateway, "_connection_fingerprint", lambda: "apptest-connection")
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/unopened/ui.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    app = AppTest.from_file("pages/1_Xu_ly_email.py").run()
    assert not app.exception
    reference = next(iter(gateway._BINDINGS.values()))["reference"]
    assert any(reference in item.value for item in app.caption)
    assert _operator("provision", reference) == {"ok": True}
    grant = next(iter(gateway._BINDINGS.values()))["grant"]
    _provider(monkeypatch)
    app.text_input(key="paste_sender").set_value("new@example.invalid")
    app.text_input(key="paste_subject").set_value("Hỏi lệ phí phúc khảo")
    app.text_area(key="paste_body").set_value("Cho em hỏi lệ phí phúc khảo một học phần?")
    app.button(key="FormSubmitter:email_form-Xử lý email").click().run()
    assert not app.exception
    case_id = app.session_state["active_case_id"]
    assert (
        db.fetch_one("SELECT status FROM cases WHERE case_id=?", (case_id,))[0] == "PREVIEW_READY"
    )
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
    app.run()
    assert not app.exception
    other = AppTest.from_file("pages/4_Nhat_ky_kiem_toan.py")
    other.query_params["case_id"] = case_id
    other.session_state["judge_grant"] = grant
    other.session_state["judge_session"] = next(iter(gateway._BINDINGS.values()))["session"]
    other.run()
    assert not other.exception
    assert any("quyền" in item.value or "phiên" in item.value for item in other.warning)
    rendered = str([item.value for item in app.markdown]) + str(
        [item.value for item in app.caption]
    )
    assert grant.token not in rendered and SECRET not in rendered
    assert grant.token not in str(dict(app.query_params)) and SECRET not in caplog.text


def test_connection_fingerprint_uses_websocket_key_and_fails_closed(monkeypatch):
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    monkeypatch.setattr(gateway.st, "context", SimpleNamespace(headers={"Sec-Websocket-Key": key}))
    assert gateway._connection_fingerprint() == hashlib.sha256(key.encode()).hexdigest()
    monkeypatch.setattr(gateway.st, "context", SimpleNamespace(headers={}))
    with pytest.raises(access.JudgeDenied):
        gateway._connection_fingerprint()


def test_native_known_id_reconnect_requires_new_operator_approval(judge, monkeypatch):
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/not-opened/reconnect.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    monkeypatch.setattr(AppSession, "register_file_watchers", lambda self: None)
    context = SimpleNamespace(session_id="", connection="")
    monkeypatch.setattr(gateway, "get_script_run_ctx", lambda **kwargs: context)
    monkeypatch.setattr(gateway, "_connection_fingerprint", lambda: context.connection)
    _provider(monkeypatch)

    async def exercise():
        script = ScriptData(str(Path.cwd() / "streamlit_app.py"))
        manager = WebsocketSessionManager(
            MemorySessionStorage(), MemoryUploadedFileManager("/unused"), ScriptCache(), None
        )

        class LocalRuntime:
            def connect_session(self, client, user_info, existing_session_id=None):
                return manager.connect_session(client, script, user_info, existing_session_id)

        runtime = LocalRuntime()

        def open_client(connection, previous=None):
            headers = {"Sec-Websocket-Key": connection}
            if previous is not None:
                headers["Sec-Websocket-Protocol"] = "streamlit,unused," + previous
            client = SimpleNamespace(request=SimpleNamespace(headers=headers), _runtime=runtime)
            BrowserWebSocketHandler.open(client)
            return client

        victim = open_client("victim-websocket-key")
        context.session_id, context.connection = victim._session_id, "victim-connection"
        reference = gateway.prepare_session()
        _operator("provision", reference, request_id="native-reconnect-victim-0001")
        result = gateway.submit(_input())
        assert result.status.value == "PREVIEW_READY"
        victim_session = manager.get_active_session_info(victim._session_id).session
        victim_session.session_state["restricted_demo_case_ids"] = [result.case_id]
        assert gateway.grant_valid() and gateway.can_read(result.case_id)
        ledger_before = _ledger()

        # Control: ID của phiên vẫn active không thể nối vào cùng AppSession/binding.
        active_attacker = open_client("active-attacker-key", victim._session_id)
        assert active_attacker._session_id != victim._session_id
        context.session_id, context.connection = active_attacker._session_id, "active-attacker"
        assert not gateway.grant_valid() and not gateway.can_read(result.case_id)
        manager.close_session(active_attacker._session_id)

        manager.disconnect_session(victim._session_id)
        attacker = open_client("reconnect-attacker-key", victim._session_id)
        assert attacker._session_id == victim._session_id
        restored = manager.get_active_session_info(attacker._session_id).session
        assert restored is victim_session
        assert restored.session_state["restricted_demo_case_ids"] == [result.case_id]
        context.session_id, context.connection = attacker._session_id, "reconnect-attacker"

        # Biết ID cũ không còn đủ để nhận grant/read; prepare tạo binding cần duyệt mới.
        assert not gateway.grant_valid() and not gateway.can_read(result.case_id)
        new_reference = gateway.prepare_session()
        assert new_reference != reference
        assert not gateway.grant_valid() and not gateway.can_read(result.case_id)
        assert _ledger() == ledger_before
        _operator("provision", new_reference, request_id="native-reconnect-new-approval-0001")
        assert gateway.grant_valid() and not gateway.can_read(result.case_id)
        _operator("revoke", new_reference)
        assert not gateway.grant_valid()
        assert not db.fetch_all("SELECT * FROM case_jobs")
        assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
        manager.close_session(attacker._session_id)

    asyncio.run(exercise())


def test_socket_path_rejects_unsafe_directory(session, monkeypatch, tmp_path):
    # Không mở socket nếu parent không riêng tư, không xóa/ghi đè path hiện hữu.
    monkeypatch.setattr(gateway, "_LISTENER", None)
    tmp_path.chmod(0o755)
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", str(tmp_path / "operator.sock"))
    with pytest.raises(access.JudgeDenied):
        _REAL_START()


def test_local_ipc_staging_smoke_network_and_provider_blocked(tmp_path):
    code = r"""
import json, os, socket, tempfile
from pathlib import Path
from types import SimpleNamespace
import openai, pytest
RealSocket = socket.socket
class LocalOnly(RealSocket):
    def __init__(self, family=socket.AF_INET, *args, **kwargs):
        if family != socket.AF_UNIX:
            raise AssertionError("NETWORK_FORBIDDEN")
        super().__init__(family, *args, **kwargs)
def forbidden(*args, **kwargs):
    raise AssertionError("NETWORK_PROVIDER_FORBIDDEN")
socket.socket = LocalOnly
socket.getaddrinfo = forbidden
socket.create_connection = forbidden
openai.OpenAI = openai.AsyncOpenAI = forbidden
from corpus.seed import ensure_seeded
from infra import db
from ui import judge_gateway as g
from test_judge_input_c1 import SECRET, _provider, _input
db.initialize_database()
ensure_seeded()
with tempfile.TemporaryDirectory(prefix="c2b-", dir="/private/tmp") as directory:
    os.chmod(directory, 0o700)
    path = Path(directory) / "o.sock"
    os.environ["JUDGE_GATEWAY_SOCKET"] = str(path)
    g.get_script_run_ctx = lambda **kwargs: SimpleNamespace(session_id="smoke-session")
    g._connection_fingerprint = lambda: "smoke-connection"
    reference = g.prepare_session()
    assert path.stat().st_mode & 0o777 == 0o600
    def rpc(operation, secret=SECRET, **kwargs):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(4)
            client.connect(str(path))
            client.sendall(json.dumps(dict(operation=operation, secret=secret, **kwargs)).encode()+b"\n")
            data = bytearray()
            while not data.endswith(b"\n"):
                data.extend(client.recv(4096))
            assert SECRET.encode() not in data
            return json.loads(data)
    assert rpc("sessions", secret="guest")["ok"] is False
    assert rpc("sessions") == {"sessions": [reference]}
    assert rpc("provision", reference=reference, request_id="staging-offline-0001") == {"ok": True}
    assert rpc("provision", reference=reference, request_id="staging-offline-0001")["ok"] is False
    patch = pytest.MonkeyPatch()
    calls = _provider(patch)
    result = g.submit(_input())
    assert result.status.value == "PREVIEW_READY" and len(calls) == 3
    assert g.can_read(result.case_id)
    from scripts import judge_operator
    import getpass, sys
    patch.setattr(getpass, "getpass", lambda _: SECRET)
    patch.setattr(sys.stdin, "isatty", lambda: True)
    patch.setattr(sys, "argv", ["operator", "--socket", str(path), "revoke", "--reference", reference])
    judge_operator.main()
    assert not g.can_read(result.case_id)
    assert rpc("recover") == {"recovery": {}}
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
    g._LISTENER.close()
"""
    root = Path(__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "DATABASE_PATH": str(tmp_path / "smoke.db"),
        "APP_MODE": "restricted_demo",
        "LLM_MODE": "replay",
        "JUDGE_INPUT_ENABLED": "1",
        "JUDGE_ISSUER_SECRET": SECRET,
        "OPENAI_API_KEY": "",
        "OPENAI_MODEL": "offline-controlled-provider",
        "PYTHONPATH": str(root / "tests") + os.pathsep + str(root),
    }
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], env=environment, capture_output=True, timeout=20
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
