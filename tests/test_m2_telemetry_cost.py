"""Telemetry correction: SDK mocked; network, production pipeline and API forbidden."""

from dataclasses import replace
from datetime import date, timedelta
import json
import socket
from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest

from infra import llm
from infra.provider_observability import provider_correlation, current_correlation, sanitize_case_id
from verify import m2_dev_live as live
from verify import m2_dev_assessment as dev
from verify import m2_dev_execution as execution

SDK_REQUEST = llm._request_openai
CASE_ID = "live_m2_dev_live_probe_01_M2DEV-A1"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Real network/provider/pipeline forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setattr(llm, "_record_latency", lambda *args: None)
    monkeypatch.setattr(llm, "sleep", lambda *args: None)
    from core import pipeline

    monkeypatch.setattr(pipeline, "process_case", forbidden)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-secret")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setattr(live, "PRICING_VERIFIED_ON", date.today())
    monkeypatch.setattr(live, "PRICING_VALID_THROUGH", date.today() + timedelta(days=7))


def usage(**kwargs):
    return {
        "input_tokens": 1000,
        "output_tokens": 100,
        "cached_input_tokens": None,
        "cache_write_tokens": None,
        "response_model": "gpt-6-luna",
        "service_tier": "default",
        **kwargs,
    }


def event(**kwargs):
    return {
        "event": "llm_provider_attempt",
        "provider": "openai",
        "model": "gpt-6-luna",
        "call_id": "test-call",
        "step": "R2_extract",
        "attempt_index": 1,
        "elapsed_ms": 5,
        "success": True,
        "usage": usage(),
        **kwargs,
    }


def test_emitter_observer_long_id_retry_and_skipped_direct_capture(monkeypatch):
    attempts = []

    def request(*args):
        attempts.append(True)
        if len(attempts) == 1:
            raise TimeoutError("synthetic timeout")
        return replace(llm._success({}, args[2], args[3]), usage=usage())

    monkeypatch.setattr(llm, "_request_openai", request)
    with provider_correlation(CASE_ID) as cid, llm.case_call_budget():
        observer = live._AttemptObserver(CASE_ID, cid)
        llm.LOGGER.addHandler(observer)
        try:
            assert llm._call_live(
                "private body", {}, "hash", "gpt-6-luna", 30, 1, case_id=CASE_ID, step="R2_extract"
            ).ok
            llm._BUDGET.get().remaining = 0
            assert not llm._call_live(
                "private body",
                {},
                "hash",
                "gpt-6-luna",
                30,
                1,
                case_id=CASE_ID,
                step="R7_question_repair",
            ).ok
        finally:
            llm.LOGGER.removeHandler(observer)
    assert len(attempts) == 2
    assert len(observer.attempts) == 4
    assert [e["event"] for e in observer.attempts] == [
        "llm_provider_attempt",
        "llm_provider_attempt",
        "llm_provider_attempt_skipped",
        "llm_provider_attempt_skipped",
    ]
    assert all(e["case_id"] == "[REDACTED]" for e in observer.attempts)
    assert all(e["correlation_id"] == cid for e in observer.attempts)
    diagnostics = observer.diagnostics()
    assert len(diagnostics.logical_calls) == 2
    assert diagnostics.logical_calls[0]["ok"] and not diagnostics.logical_calls[1]["ok"]
    assert live._retries(diagnostics) == 1
    assert diagnostics.cost is None  # timeout request has unknown usage; don't undercount.


@pytest.mark.parametrize(
    "case_id",
    [
        "synthetic-test-secret",
        "Bearer synthetic-test-secret",
        "student@example.test",
        "sk-" + "a" * 40,
    ],
)
def test_sensitive_case_ids_stay_redacted_under_correlation(case_id, monkeypatch):
    def request(*args):
        return replace(llm._success({}, args[2], args[3]), usage=usage())

    monkeypatch.setattr(llm, "_request_openai", request)
    with provider_correlation(case_id) as cid, llm.case_call_budget():
        observer = live._AttemptObserver(case_id, cid)
        llm.LOGGER.addHandler(observer)
        try:
            assert llm._call_live(
                "private body", {}, "hash", "gpt-6-luna", 30, 0, case_id=case_id, step="R2_extract"
            ).ok
        finally:
            llm.LOGGER.removeHandler(observer)
    text = json.dumps(observer.attempts)
    assert (
        case_id not in text and "synthetic-test-secret" not in text and "private body" not in text
    )
    assert len(observer.attempts) == 1


def test_nested_context_reset_and_cross_case_isolation():
    assert current_correlation(CASE_ID) is None
    with provider_correlation(CASE_ID) as first:
        assert current_correlation("other") is None
        with provider_correlation("other") as second:
            assert second != first and current_correlation(CASE_ID) is None
        assert current_correlation(CASE_ID) == first
    assert current_correlation(CASE_ID) is None


def test_sdk_usage_is_captured_without_response_payload(monkeypatch):
    response = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=1000,
            completion_tokens=100,
            total_tokens=1100,
            prompt_tokens_details=SimpleNamespace(cached_tokens=200, cache_write_tokens=300),
        ),
        model="gpt-6-luna",
        service_tier="default",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="{}", refusal=None), finish_reason="stop"
            )
        ],
        headers={"Authorization": "synthetic-test-secret"},
        raw_payload="private body",
    )
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = response
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    result = SDK_REQUEST("private body", {}, "hash", "gpt-6-luna", "synthetic-test-secret", 30)
    assert result.ok and result.usage == usage(cached_input_tokens=200, cache_write_tokens=300)
    assert "synthetic-test-secret" not in json.dumps(result.usage)
    assert "private body" not in json.dumps(result.usage)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        SimpleNamespace(prompt_tokens=-1, completion_tokens=1, total_tokens=0),
        SimpleNamespace(prompt_tokens=True, completion_tokens=1, total_tokens=2),
        SimpleNamespace(prompt_tokens=10, completion_tokens=1, total_tokens=999),
    ],
)
def test_missing_or_invalid_sdk_usage_never_becomes_zero(raw):
    assert llm._response_usage(SimpleNamespace(usage=raw)) is None
    assert live._estimated_cost([event(usage=None)]) is None


def test_bad_usage_accessor_cannot_change_business_result():
    class BadUsage:
        @property
        def usage(self):
            raise RuntimeError("synthetic accessor failure")

    assert llm._response_usage(BadUsage()) is None


def test_conservative_short_long_context_and_skipped_cost():
    assert live._estimated_cost([event()]) == pytest.approx(0.000175)
    assert live._estimated_cost([event(usage=usage(input_tokens=272000))]) == pytest.approx(0.03405)
    assert live._estimated_cost([event(usage=usage(input_tokens=272001))]) == pytest.approx(
        0.06807525
    )
    assert live._estimated_cost(
        [event(), event(event="llm_provider_attempt_skipped", usage=None)]
    ) == pytest.approx(0.000175)
    assert live._estimated_cost([event(usage=usage(cached_input_tokens=500))]) == pytest.approx(
        0.000175
    )


@pytest.mark.parametrize(
    "changed",
    [
        None,
        usage(input_tokens=True),
        usage(input_tokens=1_050_001),
        usage(output_tokens=-1),
        usage(service_tier="priority"),
        usage(service_tier=None),
        usage(response_model="other-model"),
    ],
)
def test_unknown_pricing_or_usage_fails_closed(changed):
    assert live._estimated_cost([event(usage=changed)]) is None


def test_stale_price_and_unobserved_attempts_fail_closed(monkeypatch):
    assert live._estimated_cost([]) is None
    monkeypatch.setattr(live, "PRICING_VALID_THROUGH", date.today() - timedelta(days=1))
    assert live._estimated_cost([event()]) is None


def test_cost_and_usage_survive_capture_with_context(tmp_path):
    spec = execution.load_frozen_cases()[0]
    payload = live._payload(spec)
    out = execution.DeterministicMockAdapter()(spec, payload, "test-capture", "OFFLINE")
    observer = live._AttemptObserver(CASE_ID)
    observer.attempts = [event(case_id=sanitize_case_id(CASE_ID, prompt=""))]
    diagnostics = observer.diagnostics()
    assert diagnostics.cost_metadata["kind"] == "ESTIMATED_USD"
    context = dev.execution_context(
        payload, out.result, case_id=spec["id"], observation_id="test-capture"
    )
    capture = dev.capture_result(
        out.result,
        case_id=spec["id"],
        observation_id="test-capture",
        execution=context,
        diagnostics=diagnostics,
    )
    assessment = dev.write_artifacts(tmp_path / "capture", capture)
    assert assessment.verdict == "REVIEW_REQUIRED"
    assert capture.diagnostics["provider_attempts"][0]["usage"]["input_tokens"] == 1000
    assert capture.diagnostics["cost"] == pytest.approx(0.000175)
    assert capture.diagnostics["cost_metadata"]["pricing_source"] == live.PRICING_SOURCE


def test_usage_payload_fields_are_rejected():
    diagnostics = dev.CaptureDiagnostics(
        provider_attempts=[event(usage={**usage(), "raw_payload": "private body"})]
    )
    with pytest.raises(ValueError, match="Usage"):
        dev._validate_diagnostics(dev.asdict(diagnostics))


def test_adapter_direct_usage_cost_capture_with_mock_sdk(tmp_path, monkeypatch):
    from core import pipeline

    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = SimpleNamespace(
        model="gpt-6-luna",
        service_tier="default",
        usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=100, total_tokens=1100),
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="{}", refusal=None), finish_reason="stop"
            )
        ],
    )
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    monkeypatch.setattr(llm, "_request_openai", SDK_REQUEST)
    spec = execution.load_frozen_cases()[0]
    payload = live._payload(spec)

    def fake_process(inp, *, actor, case_id):
        with llm.case_call_budget():
            assert llm._call_live(
                "synthetic private body",
                {},
                "hash",
                "gpt-6-luna",
                30,
                0,
                case_id=case_id,
                step="R2_extract",
            ).ok
        mock = execution.DeterministicMockAdapter()(spec, inp, "test", "OFFLINE")
        return replace(mock.result, case_id=case_id)

    monkeypatch.setattr(pipeline, "process_case", fake_process)
    output = live.LivePipelineAdapter().invoke(
        payload, case_id=CASE_ID, database=tmp_path / "fresh.db"
    )
    assert len(output.diagnostics.provider_attempts) == 1
    assert output.diagnostics.provider_attempts[0]["case_id"] == "[REDACTED]"
    assert output.diagnostics.provider_attempts[0]["usage"] == usage()
    assert output.diagnostics.cost == pytest.approx(0.000175)
    assert output.diagnostics.cost_metadata["kind"] == "ESTIMATED_USD"
    assert len(output.diagnostics.logical_calls) == 1
    assert current_correlation(CASE_ID) is None


def test_observer_rejects_unrelated_correlation():
    import logging

    observer = live._AttemptObserver(CASE_ID, "trusted-random-uuid")
    record = logging.LogRecord("test", logging.WARNING, "", 0, "", (), None)
    record.provider_attempt = event(case_id=CASE_ID, correlation_id="different-uuid")
    observer.emit(record)
    assert observer.attempts == []
    assert observer.diagnostics().cost is None


def _sdk_response(content="{}", *, refusal=None, finish_reason="stop", valid_usage=True):
    return SimpleNamespace(
        usage=(
            SimpleNamespace(prompt_tokens=1000, completion_tokens=100, total_tokens=1100)
            if valid_usage
            else None
        ),
        model="gpt-6-luna",
        service_tier="default",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, refusal=refusal),
                finish_reason=finish_reason,
            )
        ],
    )


@pytest.mark.parametrize(
    "changed,error_class",
    [
        ({"refusal": "private refusal"}, "ValueError"),
        ({"finish_reason": "length"}, "ValueError"),
        ({"content": "private invalid JSON"}, "JSONDecodeError"),
        ({"content": "[]"}, "ValueError"),
    ],
)
@pytest.mark.parametrize("valid_usage", [True, False])
def test_failed_structured_response_preserves_usage(
    monkeypatch, caplog, changed, error_class, valid_usage
):
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = _sdk_response(**changed, valid_usage=valid_usage)
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    monkeypatch.setattr(llm, "_request_openai", SDK_REQUEST)
    observer = live._AttemptObserver("usage-case")
    llm.LOGGER.addHandler(observer)
    try:
        result = llm._call_live(
            "private prompt", {}, "hash", "gpt-6-luna", 30, 1, case_id="usage-case"
        )
    finally:
        llm.LOGGER.removeHandler(observer)
    assert not result.ok
    assert client.chat.completions.create.call_count == 1
    assert len(observer.attempts) == 1
    attempt = observer.attempts[0]
    assert not attempt["success"] and not attempt["will_retry"]
    assert attempt["exception_class"] == error_class
    assert attempt["usage"] == (usage() if valid_usage else None)
    assert observer.diagnostics().cost == (pytest.approx(0.000175) if valid_usage else None)
    assert not observer.diagnostics().logical_calls[0]["ok"]
    for secret in (
        "private prompt",
        "private refusal",
        "private invalid JSON",
        "synthetic-test-secret",
    ):
        assert secret not in caplog.text + json.dumps(observer.attempts) + result.error


def test_failure_usage_not_duplicated_or_leaked_to_next_attempt(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.side_effect = [
        _sdk_response(content="[]"),
        _sdk_response(),
        TimeoutError("synthetic"),
        _sdk_response(),
    ]
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    monkeypatch.setattr(llm, "_request_openai", SDK_REQUEST)
    observer = live._AttemptObserver("usage-case")
    llm.LOGGER.addHandler(observer)
    try:
        with llm.case_call_budget():
            results = [
                llm._call_live("private", {}, "hash", "gpt-6-luna", 30, 1, case_id="usage-case")
                for _ in range(3)
            ]
    finally:
        llm.LOGGER.removeHandler(observer)
    assert [result.ok for result in results] == [False, True, True]
    assert client.chat.completions.create.call_count == 4
    assert [event["usage"] for event in observer.attempts] == [usage(), usage(), None, usage()]
    assert [event["attempt_index"] for event in observer.attempts] == [1, 1, 1, 2]
    assert len(observer.diagnostics().logical_calls) == 3
    assert live._estimated_cost(observer.attempts[:2]) == pytest.approx(0.00035)
    assert observer.diagnostics().cost is None


@pytest.mark.parametrize("name", ["OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"])
@pytest.mark.parametrize("value", ["tiny-secret", "12345678-1234-1234-1234-123456789abc"])
def test_all_environment_secrets_redacted_without_losing_uuid_correlation(monkeypatch, name, value):
    from infra.provider_observability import sanitize_diagnostic

    monkeypatch.setenv(name, value)
    assert value not in str(sanitize_diagnostic({"message": "error " + value}))
    assert sanitize_case_id(value, prompt="unrelated") == "[REDACTED]"
    with provider_correlation(CASE_ID) as correlation_id:
        assert current_correlation(CASE_ID) == correlation_id
        assert sanitize_case_id(correlation_id, prompt="unrelated") == correlation_id


def test_downstream_schema_failure_keeps_usage_for_each_logical_call(monkeypatch, tmp_path):
    from core.extract import extract_facts
    from infra import db

    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "schema.db")
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = _sdk_response(content="{}")
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    monkeypatch.setattr(llm, "_request_openai", SDK_REQUEST)
    observer = live._AttemptObserver("schema-case")
    llm.LOGGER.addHandler(observer)
    try:
        with llm.case_call_budget():
            result = extract_facts("synthetic request", "schema-case")
    finally:
        llm.LOGGER.removeHandler(observer)
    assert result.llm_error and not result.requests
    assert client.chat.completions.create.call_count == 2
    assert len(observer.attempts) == 2
    assert all(item["usage"] == usage() for item in observer.attempts)
    # HTTP/JSON thành công, validation domain thất bại; không đổi semantics telemetry.
    assert all(item["success"] for item in observer.attempts)
    assert len(observer.diagnostics().logical_calls) == 2
    assert live._retries(observer.diagnostics()) == 0
    assert observer.diagnostics().cost == pytest.approx(0.00035)
