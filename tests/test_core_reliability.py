"""Synthetic F-01–F-04 regressions; real wrapper, no network/provider access."""

from copy import deepcopy
from datetime import datetime, timezone

import pytest

from core.pipeline import process_case
from core.judge_input import process_judge_case
from core.dispatch import dispatch_due
from core.results import load_result
from core.types import CaseInput, CaseStatus, Decision, EscalationType
from core.worker import submit_case, worker_tick
from corpus.seed import ensure_seeded
from infra import db, llm, judge_access
from infra.demo_access import DemoAccessDenied
from test_judge_new_input_offline import _extraction, _question, _selection


@pytest.fixture
def provider(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "synthetic.db")
    monkeypatch.setenv("APP_MODE", "private")
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("OPENAI_MODEL", "offline-model")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-placeholder")
    monkeypatch.setattr(llm, "sleep", lambda _: None)
    db.initialize_database()
    ensure_seeded()
    responses, calls = [], []

    def request(prompt, schema, prompt_hash, model, api_key, timeout_s):
        calls.append(prompt)
        assert responses, "Unexpected provider request"
        data = responses.pop(0)
        if isinstance(data, Exception):
            raise data
        return llm._success(data, prompt_hash, model)

    monkeypatch.setattr(llm, "_request_openai", request)
    return responses, calls


def _input():
    return CaseInput(
        "synthetic@example.invalid",
        "Hỏi lệ phí và xin nộp phúc khảo trễ",
        "Cho em hỏi lệ phí phúc khảo một học phần. Em xin được nộp phúc khảo sau hạn.",
        datetime(2026, 10, 15, tzinfo=timezone.utc),
        "paste",
    )


def _retry_payload(payload):
    return dict(
        deepcopy(payload),
        critical_facts=[{"name": "cohort", "value": "K48"}, {"name": "cohort", "value": "K49"}],
    )


def _reply():
    return {
        "subject": "Lệ phí phúc khảo",
        "body": "Lệ phí phúc khảo là 150.000 đồng cho mỗi học phần [PK-2026-204:seed:2].",
        "citations": ["PK-2026-204:seed:2"],
    }


@pytest.mark.parametrize("retry", [False, True])
@pytest.mark.parametrize("worker", [False, True])
def test_multi_intent_completes_within_three_attempts(provider, retry, worker):
    responses, calls = provider
    payload = _extraction("JUDGE-AUTHORITY")
    payload["requests"].insert(0, _extraction("JUDGE-AUTO")["requests"][0])
    selection = _selection("JUDGE-AUTHORITY")
    selection["chunk_ids"].insert(0, "PK-2026-204:seed:2")
    if retry:
        responses.append(_retry_payload(payload))
    responses.extend([payload, selection, _reply(), _question("JUDGE-AUTHORITY")])
    if worker:
        case_id = submit_case(_input())
        worker_tick()
        result = load_result(case_id)
        assert db.fetch_one("SELECT state FROM case_jobs WHERE case_id=?", (case_id,))[0] == "done"
    else:
        result = process_case(_input())
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.decision is Decision.ESCALATE
    assert result.decision.rule_id == "P01"
    assert result.card.escalation_type is EscalationType.AUTHORITY_REQUIRED
    assert len(calls) == 3
    if not retry:
        assert result.card.partial_draft and result.card.partial_draft.grounded
    else:
        assert result.card.partial_draft is None
        assert any("Hỏi lệ phí phúc khảo" in fact for fact in result.card.facts)
    assert load_result(result.case_id).card == result.card
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action='SEND_DISPATCHED'")


def test_r2_retry_authority_keeps_policy_without_fourth_call(provider):
    responses, calls = provider
    payload = _extraction("JUDGE-AUTHORITY")
    responses.extend([_retry_payload(payload), payload, _selection("JUDGE-AUTHORITY")])
    result = process_case(_input())
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.rule_id == "P01"
    assert result.card.basis and len(calls) == 3


def test_r2_retry_routine_cannot_fail_open(provider):
    responses, calls = provider
    payload = _extraction("JUDGE-AUTO")
    responses.extend([_retry_payload(payload), payload, _selection("JUDGE-AUTO")])
    result = process_case(_input())
    assert result.status is CaseStatus.ERROR
    assert result.decision.decision is Decision.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR"
    assert result.decision.escalation_type is None
    assert result.card is None and result.draft is None and len(calls) == 3
    assert "số lượt" in result.decision.reason


def test_invalid_basis_does_not_need_fourth_attempt_or_invent_quote(provider):
    responses, calls = provider
    card = _question("JUDGE-AUTHORITY")
    card["basis"][0]["quote"] = "INVENTED SYNTHETIC QUOTE"
    responses.extend([_extraction("JUDGE-AUTHORITY"), _selection("JUDGE-AUTHORITY"), card])
    result = process_case(_input())
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.rule_id == "P01" and len(calls) == 3
    chunk = result.evidence.chunks[0]
    assert result.card.basis == [(chunk.breadcrumb, chunk.text)]
    assert "INVENTED" not in str(result.card)


def test_provider_failure_is_never_replaced_by_business_fallback(provider):
    responses, calls = provider
    responses.extend(
        [_extraction("JUDGE-AUTHORITY"), _selection("JUDGE-AUTHORITY"), TimeoutError("offline")]
    )
    result = process_case(_input())
    assert result.status is CaseStatus.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR"
    assert result.decision.escalation_type is None and result.card is None
    assert len(calls) == 3


def test_judge_retry_fallback_keeps_grant_ownership_and_no_dispatch(provider, monkeypatch):
    responses, calls = provider
    secret = "synthetic-operator-secret-for-offline-only"
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("JUDGE_INPUT_ENABLED", "1")
    monkeypatch.setenv("JUDGE_ISSUER_SECRET", secret)
    grant = judge_access.issue_grant("synthetic-session", secret)
    payload = _extraction("JUDGE-AUTHORITY")
    responses.extend([_retry_payload(payload), payload, _selection("JUDGE-AUTHORITY")])

    def replay(prompt_hash, model):
        calls.append(prompt_hash)
        assert responses
        return llm._success(responses.pop(0), prompt_hash, model)

    monkeypatch.setattr(llm, "_replay", replay)
    result = process_judge_case(
        _input(), grant=grant, session="synthetic-session", nonce="synthetic-reliability-request"
    )
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.rule_id == "P01" and result.card and len(calls) == 3
    assert judge_access.can_read(result.case_id, grant, "synthetic-session")
    assert not judge_access.can_read(result.case_id, grant, "another-session")
    with pytest.raises(DemoAccessDenied):
        dispatch_due(result.case_id)
    monkeypatch.setenv("APP_MODE", "private")
    assert dispatch_due(result.case_id) is False
    assert not db.fetch_all(
        "SELECT * FROM audit_events WHERE action IN ('SEND_SCHEDULED', 'SEND_DISPATCHED')"
    )
    assert load_result(result.case_id).card == result.card


def test_deadline_cannot_be_hidden_by_card_fallback(provider, monkeypatch):
    responses, calls = provider
    card = _question("JUDGE-AUTHORITY")
    card["basis"][0]["quote"] = "INVENTED SYNTHETIC QUOTE"
    responses.extend([_extraction("JUDGE-AUTHORITY"), _selection("JUDGE-AUTHORITY"), card])
    request = llm._request_openai

    def expire(*args):
        result = request(*args)
        if len(calls) == 3:
            llm._BUDGET.get().deadline = llm.perf_counter() - 1
        return result

    monkeypatch.setattr(llm, "_request_openai", expire)
    result = process_case(_input())
    assert result.status is CaseStatus.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR" and result.card is None
    assert len(calls) == 3
    assert "thời gian xử lý email" in result.decision.reason


def test_invalid_primary_fields_are_not_hidden_by_basis_fallback(provider):
    responses, calls = provider
    card = _question("JUDGE-AUTHORITY")
    card.update(summary="", basis=[{"chunk_id": "absent", "quote": "invented"}])
    responses.extend([_extraction("JUDGE-AUTHORITY"), _selection("JUDGE-AUTHORITY"), card])
    result = process_case(_input())
    assert result.status is CaseStatus.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR" and result.card is None
    assert len(calls) == 3


@pytest.mark.parametrize("kind", ["attempts", "deadline"])
def test_pre_request_exhaustion_is_distinct_and_never_retried(provider, caplog, kind):
    _, calls = provider
    with llm.case_call_budget(3):
        budget = llm._BUDGET.get()
        if kind == "attempts":
            budget.remaining = 0
        else:
            budget.deadline = llm.perf_counter() - 1
        result = llm.call_json("synthetic", schema={}, case_id="synthetic", step="R7_question")
    assert not result.ok and calls == []
    events = [
        record.provider_attempt for record in caplog.records if hasattr(record, "provider_attempt")
    ]
    assert len(events) == 1
    assert events[0]["stop_reason"] == f"case_{kind}_exhausted"
    assert events[0]["will_retry"] is False and events[0]["retryable"] is False
    assert events[0]["event"] == "llm_provider_attempt_skipped"
    assert ("số lượt" if kind == "attempts" else "thời gian xử lý email") in result.error
