"""Judge LIVE qua provider mock; network, deploy và email thật luôn bị cấm."""

from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest

from core.judge_input import process_judge_case
from core.results import load_result
from core.types import CaseStatus, Decision
from infra import db, judge_access as access, llm
from test_judge_input_c1 import NONCE, SECRET, _input
from test_judge_input_c1 import judge as _judge_fixture
from test_judge_new_input_offline import _extraction, _question, _selection

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
