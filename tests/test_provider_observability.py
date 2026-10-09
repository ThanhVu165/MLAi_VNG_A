from __future__ import annotations

import hashlib
import json
import logging
import socket
from types import SimpleNamespace

import pytest
import openai
from openai._exceptions import httpx2 as httpx

from infra import llm
from infra.provider_observability import (
    MAX_TEXT,
    REDACTED,
    exception_diagnostic,
    sanitize_diagnostic,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network/DB access forbidden in these tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(llm, "execute", forbidden)
    monkeypatch.setattr(llm, "fetch_one", forbidden)
    monkeypatch.setattr(llm, "_record_latency", lambda *args: None)
    monkeypatch.setattr(llm, "sleep", lambda _: None)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "runtime-openai-key")
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "0")


@pytest.mark.parametrize(
    "secret",
    [
        "runtime-openai-key",
        "AIza" + "a" * 35,
        "Bearer short-bearer",
        "student@example.test",
        "12345678901",
        "012345678901",
        "0912345678",
        "password=short-password",
        "token: short-token",
        "secret='short-secret'",
        "Authorization: Basic short-auth",
        "Cookie: session=short-cookie",
        "auth_token=short-auth",
        "credentials: short-credential",
        "api_key=short-key",
        "eyJ" + "a" * 35 + ".abcdef.ghijkl",
    ],
)
def test_secrets_and_pii_are_redacted(secret):
    rendered = sanitize_diagnostic("Invalid schema\n" + secret)
    assert secret not in rendered
    assert REDACTED in rendered
    assert "Invalid schema" in rendered


@pytest.mark.parametrize("value", [None, "invalid schema", {}, [], object(), 3.5])
def test_supported_and_unexpected_inputs_never_crash(value):
    json.dumps(sanitize_diagnostic(value))


def test_safe_metadata_survives_but_payloads_headers_and_unknown_fields_do_not():
    diagnostic = {
        "error": {
            "code": 429,
            "status": "RESOURCE_EXHAUSTED",
            "message": "Quota exceeded",
            "details": [
                {
                    "reason": "RATE_LIMIT_EXCEEDED",
                    "domain": "api.openai.com",
                    "metadata": {"prompt": "hidden", "token": "hidden"},
                }
            ],
            "headers": {"Authorization": "hidden"},
            "request": "hidden",
            "response": "hidden",
            "body": "hidden",
            "output": "hidden",
            "password": "hidden",
            "token": "hidden",
            "secret": "hidden",
        },
    }
    safe = sanitize_diagnostic(diagnostic)
    assert safe["error"]["code"] == 429
    assert safe["error"]["status"] == "RESOURCE_EXHAUSTED"
    assert safe["error"]["message"] == "Quota exceeded"
    assert safe["error"]["details"][0]["reason"] == "RATE_LIMIT_EXCEEDED"
    assert "hidden" not in json.dumps(safe)


def test_exception_diagnostic_redacts_all_repo_pii_patterns():
    pii = ("student@example.edu", "12345678901", "012345678901", "0912345678")
    joined = " ".join(pii)

    class ProviderError(Exception):
        message = f"Invalid input: {joined}"
        status = "INVALID_ARGUMENT"
        reason = "INVALID_SCHEMA"
        details = {
            "error": {
                "code": 400,
                "status": status,
                "message": joined,
                "details": [{"reason": reason, "domain": "api.openai.com"}],
            }
        }

    diagnostic = exception_diagnostic(ProviderError(), prompt="private")
    rendered = json.dumps(diagnostic)
    assert all(value not in rendered for value in pii)
    assert diagnostic["provider_status"] == "INVALID_ARGUMENT"
    assert diagnostic["provider_reason"] == "INVALID_SCHEMA"
    assert diagnostic["sanitized_details"]["error"]["code"] == 400


def test_prompt_json_body_and_output_redaction_and_bounds():
    prompt = 'Private email\n"an unstructured sentence"'
    for value in [
        prompt,
        json.dumps(prompt)[1:-1],
        "body: raw-private-data",
        "prompt is raw-private-data",
        "response: raw-private-data",
        "400 INVALID_ARGUMENT. {'unknown': 'raw-private-data'}",
    ]:
        safe = sanitize_diagnostic(value, prompt=prompt)
        assert "raw-private-data" not in safe
        assert "unstructured sentence" not in safe
    safe = sanitize_diagnostic("x" * 500 + "runtime-openai-key")
    assert "runtime" not in safe and len(safe) <= MAX_TEXT
    assert len(sanitize_diagnostic(["safe"] * 100)) == 8
    cycle = {"details": None}
    cycle["details"] = cycle
    assert REDACTED in json.dumps(sanitize_diagnostic(cycle))
    large = [{"message": "!" * 512, "reason": "?" * 512} for _ in range(8)]
    assert sanitize_diagnostic(large) == REDACTED


def test_unicode_escaped_prompt_and_sanitizer_internal_failure(monkeypatch):
    from infra import provider_observability

    prompt = "Private email: chào bạn"
    assert "ch\\u00e0o" not in sanitize_diagnostic(json.dumps(prompt)[1:-1], prompt=prompt)

    def broken(*args):
        raise RuntimeError("sanitizer unavailable")

    monkeypatch.setattr(provider_observability, "_text", broken)
    assert sanitize_diagnostic("private") == REDACTED


def test_response_http_status_without_serializing_request_or_body():
    class Response:
        status_code = 502

        @property
        def text(self):
            raise AssertionError("must not read response body")

        @property
        def headers(self):
            raise AssertionError("must not read headers")

    error = Exception("upstream unavailable")
    error.response = Response()
    diagnostic = exception_diagnostic(error, prompt="private")
    assert diagnostic["http_status"] == 502
    assert diagnostic["provider_code"] is None
    assert diagnostic["provider_status"] is None


def test_hostile_object_is_not_stringified_and_bad_attributes_do_not_throw():
    class Hostile:
        def __str__(self):
            raise AssertionError("must not stringify")

    class HostileError(Exception):
        @property
        def details(self):
            raise RuntimeError("unavailable")

        @property
        def response(self):
            raise RuntimeError("unavailable")

    assert sanitize_diagnostic(Hostile()) == REDACTED
    assert (
        exception_diagnostic(HostileError("invalid schema"), prompt="private")["sanitized_message"]
        == "invalid schema"
    )


def events(caplog):
    return [
        record.provider_attempt for record in caplog.records if hasattr(record, "provider_attempt")
    ]


def sdk_error(status, code=None, message="raw provider body"):
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    error_type = {
        400: openai.BadRequestError,
        429: openai.RateLimitError,
        500: openai.InternalServerError,
        503: openai.InternalServerError,
    }[status]
    return error_type(
        message,
        response=httpx.Response(status, request=request),
        body={"code": code, "private": "student@example.test"},
    )


@pytest.mark.parametrize("status,code", [(400, "invalid_schema"), (429, "insufficient_quota")])
def test_real_sdk_client_error_retains_diagnostics_without_retry(monkeypatch, caplog, status, code):
    error = sdk_error(status, code)
    seen = []
    monkeypatch.setattr(llm, "sleep", lambda _: pytest.fail("must not sleep"))

    def invalid(*args):
        seen.append(args)
        raise error

    monkeypatch.setattr(llm, "_request_openai", invalid)
    with llm.case_call_budget():
        result = llm.call_json("private", schema={}, step="R2_extract", case_id="case-1")
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - 1
    assert not result.ok and len(seen) == 1
    event = events(caplog)[0]
    assert event["case_id"] == "case-1" and event["step"] == "R2_extract"
    assert event["http_status"] == status and event["provider_code"] == code
    assert event["provider"] == "openai"
    assert event["exception_class"] == type(error).__name__
    assert event["retryable"] is False and event["will_retry"] is False
    assert event["stop_reason"] == "non_retryable"
    assert "student@example.test" not in caplog.text + result.error
    assert "raw provider body" not in caplog.text + result.error
    assert error.code == code


def test_server_retry_then_success_correlates_and_preserves_request_and_result(monkeypatch, caplog):
    seen = []
    sleeps = []
    expected = llm._success({"answer": "unchanged"}, "hash", "model")

    def request(*args):
        seen.append(args)
        if len(seen) == 1:
            raise sdk_error(503, message="Overloaded")
        return expected

    monkeypatch.setattr(llm, "_request_openai", request)
    monkeypatch.setattr(llm, "perf_counter", lambda: 100.0)
    monkeypatch.setattr(llm, "sleep", sleeps.append)
    schema = {"type": "object"}
    with llm.case_call_budget():
        result = llm._call_live(
            "private", schema, "hash", "model", 20, 10, case_id="case", step="R4_select"
        )
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - 2
    assert result is expected
    assert sleeps == [llm.LLM_RETRY_BACKOFF_SECONDS]
    assert seen == [("private", schema, "hash", "model", "runtime-openai-key", 20)] * 2
    first, second = events(caplog)
    assert first["call_id"] == second["call_id"]
    assert [first["attempt_index"], second["attempt_index"]] == [1, 2]
    assert first["http_status"] == 503 and first["will_retry"] is True
    assert first["event"] == "llm_provider_attempt" and first["retryable"] is True
    assert first["retry_backoff_ms"] == 1000
    assert second["success"] is True and second["will_retry"] is False
    assert second["retry_backoff_ms"] == 0
    assert second["attempts_remaining_before"] == llm.LLM_MAX_ATTEMPTS - 1
    assert second["attempts_remaining_after"] == llm.LLM_MAX_ATTEMPTS - 2
    assert second["remaining_case_time_s"] == 60
    assert second["prompt_chars"] == len("private")
    assert second["prompt_hash12"] == hashlib.sha256(b"private").hexdigest()[:12]
    assert second["effective_timeout_s"] == 20
    assert "private" not in caplog.text and "unchanged" not in caplog.text


def test_transient_final_attempt_does_not_sleep(monkeypatch, caplog):
    monkeypatch.setattr(llm, "sleep", lambda _: pytest.fail("must not sleep"))
    monkeypatch.setattr(
        llm,
        "_request_openai",
        lambda *args: (_ for _ in ()).throw(sdk_error(503, message="Overloaded")),
    )
    assert not llm._call_live("private", {}, "hash", "model", 20, 0).ok
    event = events(caplog)[0]
    assert event["will_retry"] is False and event["retry_backoff_ms"] == 0


def test_retry_backoff_skips_sleep_near_deadline_and_preserves_budget(monkeypatch, caplog):
    seen = []
    sleeps = []

    def unavailable(*args):
        seen.append(args)
        raise sdk_error(503, message="Overloaded")

    monkeypatch.setattr(llm, "_request_openai", unavailable)
    monkeypatch.setattr(llm, "perf_counter", lambda: 100.0)
    monkeypatch.setattr(llm, "sleep", sleeps.append)
    with llm.case_call_budget():
        llm._BUDGET.get().deadline = 101.5
        assert not llm._call_live("private", {}, "hash", "model", 20, 1).ok
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - 2
    assert len(seen) == 2 and sleeps == []
    assert [event["retry_backoff_ms"] for event in events(caplog)] == [0, 0]


def test_shared_budget_skips_requests_after_four_attempts(monkeypatch, caplog):
    monkeypatch.setattr(llm, "LLM_MAX_ATTEMPTS", 4)
    seen = []

    def unavailable(*args):
        seen.append(args)
        raise sdk_error(500, message="offline")

    monkeypatch.setattr(llm, "_request_openai", unavailable)
    with llm.case_call_budget():
        for _ in range(3):
            assert not llm._call_live("private", {}, "hash", "model", 20, 1).ok
    assert len(seen) == 4
    recorded = events(caplog)
    assert sum(event["event"] == "llm_provider_attempt" for event in recorded) == 4
    skipped = [event for event in recorded if event["event"].endswith("skipped")]
    assert len(skipped) == 2
    assert all(event["attempts_remaining_before"] == 0 for event in skipped)
    assert all(event["retryable"] is False and event["will_retry"] is False for event in skipped)
    assert all(event["stop_reason"] == "case_budget_or_deadline" for event in skipped)


def test_deadline_block_and_effective_timeout_are_unchanged(monkeypatch, caplog):
    seen = []
    monkeypatch.setattr(llm, "perf_counter", lambda: 100.0)
    monkeypatch.setattr(
        llm, "_request_openai", lambda *args: seen.append(args) or llm._success({}, "hash", "model")
    )
    with llm.case_call_budget():
        llm._BUDGET.get().deadline = 107.9
        assert llm._call_live("private", {}, "hash", "model", 50, 0).ok
        assert seen[0][-1] == 7
        llm._BUDGET.get().deadline = 100.0
        assert not llm._call_live("private", {}, "hash", "model", 50, 1).ok
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - 1
    assert len(seen) == 1
    skipped = events(caplog)[1:]
    assert len(skipped) == 2
    assert all(event["event"] == "llm_provider_attempt_skipped" for event in skipped)
    assert all(event["retryable"] is False and event["will_retry"] is False for event in skipped)
    assert all(event["stop_reason"] == "case_budget_or_deadline" for event in skipped)
    assert llm.LLM_MAX_ATTEMPTS == 5 and llm.CASE_TIMEOUT_SECONDS == 60


def test_without_budget_and_distinct_calls_do_not_invent_context(monkeypatch, caplog):
    monkeypatch.setattr(llm, "_request_openai", lambda *args: llm._success({}, "hash", "model"))
    for _ in range(2):
        assert llm._call_live("private", {}, "hash", "model", 20, 0).ok
    first, second = events(caplog)
    assert first["call_id"] != second["call_id"]
    for field in (
        "case_id",
        "trace_id",
        "step",
        "attempts_remaining_before",
        "attempts_remaining_after",
        "remaining_case_time_s",
    ):
        assert first[field] is None
    assert "http_status" not in first


def test_real_case_uuid_remains_correlatable(monkeypatch, caplog):
    case_id = "4cb9832c-3df9-4b52-a5d8-314f29e25bde"
    monkeypatch.setattr(llm, "_request_openai", lambda *args: llm._success({}, "hash", "model"))
    assert llm._call_live("private", {}, "hash", "model", 20, 0, case_id=case_id).ok
    assert events(caplog)[0]["case_id"] == case_id


def test_diagnostic_and_logging_failure_preserve_original_semantics(monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("diagnostics unavailable")

    expected = llm._success({"answer": "same"}, "hash", "model")
    monkeypatch.setattr(llm, "_request_openai", lambda *args: expected)
    monkeypatch.setattr(llm, "LOGGER", SimpleNamespace(warning=broken))
    assert llm._call_live("private", {}, "hash", "model", 20, 1) is expected
    monkeypatch.setattr(llm, "LOGGER", logging.getLogger("offline-test"))
    monkeypatch.setattr(llm, "sanitize_diagnostic", broken)
    error = sdk_error(400, "invalid_schema")

    def invalid(*args):
        raise error

    monkeypatch.setattr(llm, "_request_openai", invalid)
    with llm.case_call_budget():
        assert not llm._call_live("private", {}, "hash", "model", 20, 1).ok
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - 1


def test_cache_replay_and_missing_key_do_not_emit_provider_attempts(monkeypatch, caplog):
    expected = llm._success({}, "hash", "model")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setattr(llm, "_replay", lambda *args: expected)
    assert llm.call_json("private", schema={}, step="R2_extract", case_id="case").ok
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "1")
    monkeypatch.setattr(llm, "_load_cache", lambda *args: expected)
    assert llm.call_json("private", schema={}, step="R2_extract", case_id="case").ok
    monkeypatch.delenv("OPENAI_API_KEY")
    assert not llm._call_live("private", {}, "hash", "model", 20, 1).ok
    assert not events(caplog)
