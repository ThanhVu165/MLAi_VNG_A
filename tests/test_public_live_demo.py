"""Public LIVE offline: admission, quota, accounting và session ownership thật."""

import importlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest
from streamlit.runtime.pages_manager import PagesManager
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
from streamlit.testing.v1 import AppTest

from core.judge_input import process_judge_case
from infra import db, judge_access as access, llm, public_demo as public
from test_judge_input_c1 import SECRET, _input
from test_judge_input_c1 import judge as _judge_fixture
from test_judge_input_live import _mock_pipeline_provider
from test_judge_input_live import live as _live_fixture
from ui import judge_gateway as gateway

judge = _judge_fixture
live = _live_fixture


@pytest.fixture
def ready(live, monkeypatch):
    monkeypatch.setenv("JUDGE_PUBLIC_DEMO_ENABLED", "1")
    clock = [access.time.time()]
    monkeypatch.setattr(public.time, "time", lambda: clock[0])
    return clock


def _reserve(grant, session, index):
    return access.request_scope(
        grant, session, f"public-request-{index:04}", f"public-{index}", "hash"
    )


def _snapshot():
    return [
        (r["key"], r["value"]) for r in db.fetch_all("SELECT key,value FROM settings ORDER BY key")
    ]


def test_quota_ten_then_eleven_denied_and_reconnect_cannot_reset(ready):
    grant = public.admit("binding-a", "server-a")
    for index in range(10):
        ready[0] += 61
        with _reserve(grant, "binding-a", index):
            pass
    before = _snapshot()
    with pytest.raises(access.JudgeDenied):
        with _reserve(grant, "binding-a", 10):
            pytest.fail("Request 11 admitted")
    assert _snapshot() == before
    replacement = public.admit("binding-b", "server-a")
    importlib.reload(public)
    with pytest.raises(access.JudgeDenied):
        with _reserve(replacement, "binding-b", 11):
            pytest.fail("Reconnect reset quota")


def test_operator_still_three_and_public_off_by_default(live, monkeypatch):
    monkeypatch.delenv("JUDGE_PUBLIC_DEMO_ENABLED", raising=False)
    with pytest.raises(access.JudgeDenied):
        public.admit("binding", "server")
    for i in range(3):
        with _reserve(live, "session-a", i):
            pass
    with pytest.raises(access.JudgeDenied):
        with _reserve(live, "session-a", 4):
            pytest.fail("Operator limit increased")


def test_session_rate_limit_and_restart_persistence(ready):
    g = public.admit("a", "server")
    for i in range(2):
        with _reserve(g, "a", i):
            pass
    before = _snapshot()
    importlib.reload(public)
    with pytest.raises(access.JudgeDenied):
        with _reserve(g, "a", 2):
            pytest.fail("Rate limiter reset")
    assert before == _snapshot()
    ready[0] += 61
    with _reserve(g, "a", 3):
        pass


def test_global_admission_limit_and_lifetime_cap(ready, monkeypatch):
    for i in range(10):
        public.admit(f"binding-{i}", f"server-{i}")
    before = _snapshot()
    with pytest.raises(access.JudgeDenied):
        public.admit("over-rate", "new-server")
    assert _snapshot() == before
    ready[0] += 61
    monkeypatch.setattr(public, "SESSION_ADMISSION_LIMIT", 10)
    with pytest.raises(access.JudgeDenied):
        public.admit("over-cap", "new-server")


def test_admission_race_cannot_bypass_rate_limit(ready):
    barrier = Barrier(12)

    def admit(index):
        barrier.wait(timeout=5)
        try:
            public.admit(f"race-binding-{index}", f"race-server-{index}")
            return True
        except access.JudgeDenied:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        assert sum(pool.map(admit, range(12))) == public.ADMISSIONS_PER_MINUTE


def test_process_restart_preserves_quota_and_rate(ready):
    g = public.admit("a", "server")
    with _reserve(g, "a", 0):
        pass
    code = """
import socket, openai, sqlite3
def forbidden(*args, **kwargs):
    raise AssertionError('OFFLINE_ONLY')
socket.socket.connect = socket.create_connection = openai.OpenAI = forbidden
from infra import public_demo as p, judge_access as a, db
g = p.admit('after-restart', 'server')
with a.request_scope(g, 'after-restart', 'restart-second-nonce', 'restart-second-case', 'hash'):
    pass
try:
    with a.request_scope(g, 'after-restart', 'restart-third-nonce', 'restart-third-case', 'hash'):
        raise AssertionError('Rate reset by process restart')
except a.JudgeDenied:
    pass
with db.transaction() as c:
    assert a._load(c)['total'] == 2
print('restart-preserved')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        env={**os.environ, "DATABASE_PATH": str(db.DEFAULT_DATABASE_PATH)},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "restart-preserved"


def test_global_request_rate_across_new_sessions(ready):
    grants = [public.admit(f"binding-{i}", f"server-{i}") for i in range(6)]
    for i in range(10):
        with _reserve(grants[i // 2], f"binding-{i // 2}", i):
            pass
    before = _snapshot()
    with pytest.raises(access.JudgeDenied):
        with _reserve(grants[5], "binding-5", 10):
            pytest.fail("Global rate bypass")
    assert _snapshot() == before


def test_mixed_operator_public_cost_boundary_is_atomic(ready, live, monkeypatch):
    with _reserve(live, "session-a", 100):
        pass
    g = public.admit("public-binding", "server")
    monkeypatch.setattr(access, "GLOBAL_ESTIMATE_MICRO_USD_LIMIT", 20_000)
    barrier = Barrier(2)

    def attempt(index):
        barrier.wait(timeout=5)
        grant, session = (live, "session-a") if index == 0 else (g, "public-binding")
        try:
            with _reserve(grant, session, index):
                return True
        except access.JudgeDenied:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(attempt, range(2))) == 1
    with db.transaction() as c:
        state = access._load_c2(c)
    assert sum(r["estimated_micro_usd"] for r in state["requests"].values()) == 20_000


def test_global_two_and_same_quota_one_concurrent(ready):
    a = public.admit("a", "quota-a")
    b = public.admit("b", "quota-b")
    c = public.admit("c", "quota-c")
    replacement = public.admit("replacement", "quota-a")
    with _reserve(a, "a", 0):
        with pytest.raises(access.JudgeDenied):
            with _reserve(replacement, "replacement", 1):
                pytest.fail("Same quota concurrent")
        with _reserve(b, "b", 2):
            with pytest.raises(access.JudgeDenied):
                with _reserve(c, "c", 3):
                    pytest.fail("Third concurrent request")


@pytest.mark.parametrize("damage", ["missing", "corrupt", "provenance"])
def test_public_ledger_damage_fails_closed(ready, damage):
    g = public.admit("a", "server")
    if damage == "missing":
        db.execute("DELETE FROM settings WHERE key=?", (public.STATE_KEY,))
    elif damage == "corrupt":
        db.execute("UPDATE settings SET value='{}' WHERE key=?", (public.STATE_KEY,))
    else:
        with db.transaction() as c:
            state = access._load_c2(c)
            state["provisioned"].clear()
            access._save_c2(c, state)
    before = _snapshot()
    with pytest.raises(access.JudgeDenied):
        with _reserve(g, "a", 0):
            pytest.fail("Corrupt public state admitted")
    with pytest.raises(access.JudgeDenied):
        public.admit("new-binding", "server")
    assert _snapshot() == before


def test_kill_switch_stops_public_next_attempt_but_operator_remains(ready, live, monkeypatch):
    g = public.admit("a", "server")
    with _reserve(g, "a", 0):
        access.mark_processing()
        monkeypatch.setenv("JUDGE_PUBLIC_DEMO_ENABLED", "0")
        with pytest.raises(access.JudgeDenied):
            access.reserve_live_attempt(2000)
    with _reserve(live, "session-a", 1):
        access.check_active()
    with pytest.raises(access.JudgeDenied):
        public.admit("b", "server-b")


def test_revoked_or_expired_public_cannot_reissue_same_binding(ready):
    g = public.admit("a", "server")
    access.revoke_grant(g, SECRET)
    with pytest.raises(access.JudgeDenied):
        with _reserve(g, "a", 0):
            pytest.fail("Revoked public grant admitted")
    with pytest.raises(access.JudgeDenied):
        public.admit("a", "server")
    with pytest.raises(access.JudgeDenied):
        public.admit("reconnected-a", "server")
    h = public.admit("b", "other-server")
    ready[0] += public.TTL_SECONDS + 1
    assert not access.grant_is_valid(h, "b")


def test_gateway_auto_admission_and_reconnect_has_no_case_ownership(ready, monkeypatch):
    context = SimpleNamespace(session_id="server-a", connection="connection-a")
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/unopened/public.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    monkeypatch.setattr(gateway, "get_script_run_ctx", lambda **kwargs: context)
    monkeypatch.setattr(gateway, "_connection_fingerprint", lambda: context.connection)
    gateway.prepare_session()
    assert gateway.input_available() and not gateway.grant_valid()
    calls = _mock_pipeline_provider(monkeypatch)
    result = gateway.submit(_input())
    assert len(calls) == 3 and result.status.value == "PREVIEW_READY"
    assert gateway.can_read(result.case_id)
    context.connection = "reconnected"
    assert not gateway.can_read(result.case_id)
    gateway.prepare_session()
    assert not gateway.grant_valid() and not gateway.can_read(result.case_id)
    context.session_id, context.connection = "server-b", "connection-b"
    gateway.prepare_session()
    assert not gateway.can_read(result.case_id)
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


@pytest.mark.parametrize(
    "scenario,expected", [("JUDGE-AUTO", "PREVIEW_READY"), ("JUDGE-AUTHORITY", "AWAITING_HUMAN")]
)
def test_public_business_outcomes_are_common_pipeline(ready, monkeypatch, scenario, expected):
    g = public.admit("a", "server")
    calls = _mock_pipeline_provider(monkeypatch, scenario)
    result = process_judge_case(
        _input(scenario), grant=g, session="a", nonce="public-business-request"
    )
    assert result.status.value == expected and calls
    assert access.can_read(result.case_id, g, "a")
    assert not access.can_read(result.case_id, g, "other")
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


def test_public_invalid_input_stops_before_provider_and_debit(ready, monkeypatch):
    g = public.admit("a", "server")
    calls = _mock_pipeline_provider(monkeypatch)
    before = _snapshot()
    with pytest.raises(ValueError):
        process_judge_case(
            replace(_input(), body=""), grant=g, session="a", nonce="invalid-request-nonce"
        )
    assert not calls and _snapshot() == before


def test_missing_usage_blocks_new_public_but_error_still_readable(ready, monkeypatch):
    g = public.admit("a", "server")
    calls = _mock_pipeline_provider(monkeypatch, usage=False)
    result = process_judge_case(_input(), grant=g, session="a", nonce="usage-failure-nonce")
    assert result.status.value == "ERROR" and len(calls) == 1
    assert access.can_read(result.case_id, g, "a")
    before = _snapshot()
    with pytest.raises(access.JudgeDenied):
        public.admit("b", "another-server")
    with pytest.raises(access.JudgeDenied):
        with _reserve(g, "a", 2):
            pytest.fail("Usage failure bypassed")
    assert _snapshot() == before


def test_orphan_pending_usage_blocks_admission(ready):
    with db.transaction() as c:
        c.execute(
            "INSERT INTO settings(key,value,updated_at,actor) VALUES(?,?,?,'SYSTEM')",
            (
                access.LIVE_ATTEMPT_PREFIX + "orphan",
                json.dumps(
                    {
                        "version": 1,
                        "attempts": 1,
                        "reserved_output_tokens": 2000,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "pending": True,
                        "blocked": False,
                    }
                ),
                db.now_iso(),
            ),
        )
    with pytest.raises(access.JudgeDenied):
        public.admit("a", "server")


def test_public_entry_through_navigation_without_operator(ready, monkeypatch):
    get_context = gateway.get_script_run_ctx
    monkeypatch.setattr(
        gateway,
        "get_script_run_ctx",
        lambda **kwargs: SimpleNamespace(
            session_id=str(id(get_context(**kwargs).session_state._state))
        ),
    )
    monkeypatch.setattr(gateway, "_connection_fingerprint", lambda: "browser-connection")
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/unopened/public-ui.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    monkeypatch.setattr("core.worker.start_worker", lambda: None)
    monkeypatch.setattr("corpus.seed.ensure_seeded", lambda: None)
    cache = ScriptCache()
    monkeypatch.setattr(
        PagesManager, "get_page_script_byte_code", lambda self, path: cache.get_bytecode(path)
    )
    monkeypatch.setattr(
        llm, "_replay", lambda *args: pytest.fail("New public email reached replay")
    )
    app = AppTest.from_file(str(Path.cwd() / "streamlit_app.py")).run(timeout=20)
    case_ids = set()
    for index in range(10):
        ready[0] += 61
        calls = _mock_pipeline_provider(monkeypatch)
        app.text_input(key="paste_sender").set_value("public-new@example.invalid")
        app.text_input(key="paste_subject").set_value(f"Hỏi lệ phí phúc khảo mới {index}")
        app.text_area(key="paste_body").set_value("Cho em hỏi lệ phí phúc khảo một học phần?")
        app.button(key="FormSubmitter:email_form-Xử lý email").click().run(timeout=20)
        assert not app.exception and not app.error
        assert len(calls) == 3
        case_ids.add(app.session_state["active_case_id"])
    assert len(case_ids) == 10
    monkeypatch.setattr(
        llm, "_request_openai", lambda *args, **kwargs: pytest.fail("Request 11 reached provider")
    )
    ready[0] += 61
    app.text_input(key="paste_subject").set_value("Request 11 must deny")
    app.button(key="FormSubmitter:email_form-Xử lý email").click().run(timeout=20)
    assert not app.exception and app.error
    assert len(db.fetch_all("SELECT * FROM cases")) == 10
    case_id = app.session_state["active_case_id"]
    assert (
        db.fetch_one("SELECT status FROM cases WHERE case_id=?", (case_id,))[0] == "PREVIEW_READY"
    )
    assert db.fetch_all("SELECT * FROM audit_events WHERE case_id=?", (case_id,))
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
    rendered = str([x.value for items in (app.markdown, app.info, app.caption) for x in items])
    binding = next(iter(gateway._BINDINGS.values()))
    assert binding["grant"].token not in rendered and SECRET not in rendered
    assert "Bản nháp sẵn sàng" in rendered and "Căn cứ quy định" in rendered
    app.button(key=f"open_audit_{case_id}").click().run(timeout=20)
    assert not app.exception
    assert any("Nhật ký kiểm toán" in item.value for item in app.markdown)
