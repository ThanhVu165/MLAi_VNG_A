"""Judge LIVE qua provider mock; network, deploy và email thật luôn bị cấm."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest

from core.judge_input import process_judge_case
from core.pipeline import process_case
from core.results import load_result
from core.types import CaseInput, CaseStatus, Decision
from infra import db, judge_access as access, llm
from infra.demo_access import canonical_demo_inputs
from test_judge_input_c1 import NONCE, SECRET, _input
from test_judge_input_c1 import judge as _judge_fixture
from test_judge_new_input_offline import _extraction, _question, _selection
from ui import judge_gateway as gateway
from verify.harness import run_cases

judge = _judge_fixture


@pytest.fixture
def live(judge, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "approved-mocked-model")
    monkeypatch.setenv("JUDGE_LIVE_MODEL", "approved-mocked-model")
    monkeypatch.setenv("JUDGE_LIVE_ENABLED", "1")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-placeholder-never-sent")
    return judge


def _mock_pipeline_provider(monkeypatch, scenario="JUDGE-AUTO", *, usage=True):
    responses = [_extraction(scenario), _selection(scenario)]
    responses.append(
        {
            "subject": "Lệ phí phúc khảo",
            "body": "Lệ phí là 150.000 đồng [PK-2026-204:seed:2].",
            "citations": ["PK-2026-204:seed:2"],
        }
        if scenario == "JUDGE-AUTO"
        else _question(scenario)
    )
    calls = []

    def request(prompt, schema, prompt_hash, model, api_key, timeout, *, max_output_tokens):
        calls.append((model, timeout, max_output_tokens))
        return replace(
            llm._success(responses.pop(0), prompt_hash, model),
            usage={"input_tokens": 500, "output_tokens": 100} if usage else None,
        )

    monkeypatch.setattr(llm, "_request_openai", request)
    return calls


def _live_state(case_id):
    row = db.fetch_one(
        "SELECT value FROM settings WHERE key=?", (access.LIVE_ATTEMPT_PREFIX + case_id,)
    )
    return json.loads(row["value"])


def test_arbitrary_new_email_runs_live_pipeline_with_preview_and_session_audit(live, monkeypatch):
    calls = _mock_pipeline_provider(monkeypatch)
    inp = replace(_input(), sender="judge@new-domain.example")
    result = process_judge_case(inp, grant=live, session="session-a", nonce=NONCE)

    assert result.status is CaseStatus.PREVIEW_READY
    assert result.decision.decision is Decision.AUTO_REPLY
    assert result.draft and result.draft.citations
    assert calls == [("approved-mocked-model", 30, 2_000)] * 3
    assert _live_state(result.case_id) == {
        "version": 1,
        "attempts": 3,
        "reserved_output_tokens": 6_000,
        "input_tokens": 1_500,
        "output_tokens": 300,
        "pending": False,
        "blocked": False,
    }
    assert access.can_read(result.case_id, live, "session-a")
    assert not access.can_read(result.case_id, live, "another-session")
    assert db.fetch_all("SELECT action FROM audit_events WHERE case_id=?", (result.case_id,))
    assert not db.fetch_all("SELECT * FROM case_jobs WHERE case_id=?", (result.case_id,))
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


def test_same_live_config_routes_canonical_and_verify4_to_replay(live, monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("JUDGE_LIVE_MODEL", "gpt-6-luna")
    judge_provider_calls = _mock_pipeline_provider(monkeypatch)
    judge_result = process_judge_case(_input(), grant=live, session="session-a", nonce=NONCE)
    provider_calls = []
    replay_calls = []
    replay = llm._replay

    def forbidden_provider(*args, **kwargs):
        provider_calls.append(args)
        raise AssertionError("Non-judge request reached provider")

    def observed_replay(prompt_hash, model):
        replay_calls.append((prompt_hash, model))
        return replay(prompt_hash, model)

    monkeypatch.setattr(llm, "_request_openai", forbidden_provider)
    monkeypatch.setattr(llm, "_replay", observed_replay)
    sample = canonical_demo_inputs()[0]
    result = process_case(
        CaseInput(
            sample.sender,
            sample.subject,
            sample.body,
            datetime.fromisoformat(sample.received_at),
            sample.channel,
        )
    )
    verify = run_cases(Path("verify/cases_verify4.json"), run_name="live-replay-regression")

    assert result.decision.decision is Decision.AUTO_REPLY
    assert judge_result.status is CaseStatus.PREVIEW_READY and len(judge_provider_calls) == 3
    assert len(verify) == 4 and all(item.passed for item in verify)
    assert replay_calls and provider_calls == []


def test_live_gateway_keeps_two_browser_sessions_isolated(live, monkeypatch):
    context = SimpleNamespace(session_id="browser-a", connection="connection-a")
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/unopened/live.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    monkeypatch.setattr(gateway, "get_script_run_ctx", lambda **kwargs: context)
    monkeypatch.setattr(gateway, "_connection_fingerprint", lambda: context.connection)
    reference = gateway.prepare_session()
    gateway._operate(
        {
            "operation": "provision",
            "reference": reference,
            "request_id": "live-browser-a-provision",
            "secret": SECRET,
        }
    )
    _mock_pipeline_provider(monkeypatch)
    result = gateway.submit(_input())
    assert gateway.can_read(result.case_id)

    context.session_id, context.connection = "browser-b", "connection-b"
    gateway.prepare_session()
    assert not gateway.grant_valid() and not gateway.can_read(result.case_id)
    with pytest.raises(access.JudgeDenied):
        gateway.submit(_input())

    context.session_id, context.connection = "browser-a", "connection-a"
    assert gateway.grant_valid() and gateway.can_read(result.case_id)
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


def test_railway_image_prepares_private_operator_socket_directory():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "install -d -m 0700 /app/.judge-ipc" in dockerfile


def test_live_escalation_keeps_policy_grounding_and_never_dispatches(live, monkeypatch):
    _mock_pipeline_provider(monkeypatch, "JUDGE-AUTHORITY")
    result = process_judge_case(
        _input("JUDGE-AUTHORITY"), grant=live, session="session-a", nonce=NONCE
    )
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.decision is Decision.ESCALATE
    assert result.decision.rule_id == "P01" and result.card and result.card.basis
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


def test_missing_usage_poisoned_case_fails_closed_without_second_provider_call(live, monkeypatch):
    calls = _mock_pipeline_provider(monkeypatch, usage=False)
    result = process_judge_case(_input(), grant=live, session="session-a", nonce=NONCE)
    assert result.status is CaseStatus.ERROR
    assert result.decision.decision is Decision.ERROR
    assert len(calls) == 1
    state = _live_state(result.case_id)
    assert state["attempts"] == 1 and state["blocked"] and not state["pending"]
    assert load_result(result.case_id).status is CaseStatus.ERROR
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


@pytest.mark.parametrize("action", ["model", "kill", "revoke"])
def test_model_pin_kill_switch_and_revoke_deny_before_provider(live, monkeypatch, action):
    calls = _mock_pipeline_provider(monkeypatch)
    if action == "model":
        monkeypatch.setenv("JUDGE_LIVE_MODEL", "different-model")
    elif action == "kill":
        monkeypatch.setenv("JUDGE_LIVE_ENABLED", "0")
    else:
        access.revoke_grant(live, SECRET)
    if action == "revoke":
        with pytest.raises(access.JudgeDenied):
            process_judge_case(_input(), grant=live, session="session-a", nonce=NONCE + action)
    else:
        result = process_judge_case(_input(), grant=live, session="session-a", nonce=NONCE + action)
        assert result.status is CaseStatus.ERROR
    assert calls == []


@pytest.mark.parametrize("action", ["kill", "revoke", "hold"])
def test_runtime_guard_change_after_provider_step_stops_live_case(live, monkeypatch, action):
    calls = _mock_pipeline_provider(monkeypatch)
    request = llm._request_openai

    def change_guard(*args, **kwargs):
        result = request(*args, **kwargs)
        if len(calls) == 1:
            if action == "kill":
                monkeypatch.setenv("JUDGE_INPUT_ENABLED", "0")
            elif action == "revoke":
                access.revoke_grant(live, SECRET)
            else:
                assert set(access.recover_reservations(SECRET).values()) == {"HOLD"}
        return result

    monkeypatch.setattr(llm, "_request_openai", change_guard)
    result = process_judge_case(_input(), grant=live, session="session-a", nonce=NONCE)
    assert result.status is CaseStatus.ERROR and result.decision.decision is Decision.ERROR
    assert len(calls) == 1
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


def test_openai_request_receives_real_output_limit(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4, total_tokens=14),
        model="approved-mocked-model",
        service_tier="default",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content='{"answer": "safe"}', refusal=None),
                finish_reason="stop",
            )
        ],
    )
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    result = llm._request_openai(
        "synthetic prompt",
        {"type": "object"},
        "hash",
        "approved-mocked-model",
        "offline-placeholder-never-sent",
        9,
        max_output_tokens=access.JUDGE_LIVE_MAX_OUTPUT_TOKENS,
    )
    assert result.ok and result.usage["output_tokens"] == 4
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["max_completion_tokens"] == access.JUDGE_LIVE_MAX_OUTPUT_TOKENS
    assert kwargs["model"] == "approved-mocked-model"
