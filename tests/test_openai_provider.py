"""Provider checks: SDK responses mocked, network and database access forbidden."""

import copy
import hashlib
import json
import socket
from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest
from openai._exceptions import httpx2 as httpx

from infra import llm
from infra.provider_observability import sanitize_case_id, sanitize_diagnostic
from scripts.probe_openai_compat import strict_copy


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Network/DB/provider fallback forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(llm, "execute", forbidden)
    monkeypatch.setattr(llm, "fetch_one", forbidden)
    monkeypatch.setattr(llm, "_record_latency", lambda *args: None)
    monkeypatch.setattr(llm, "_store_cache", lambda *args: None)
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setattr(llm, "sleep", lambda _: None)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    monkeypatch.delenv("OPENAI_REASONING_EFFORT", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "short-openai-secret")
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "0")


def call():
    return llm.call_json("private email", schema={}, step="R2", case_id="case")


def test_dispatch_and_pin_case_configuration(monkeypatch, caplog):
    monkeypatch.delenv("LLM_PROVIDER")
    assert llm._provider_config() == ("openai", "configured-model")
    seen = []

    def request(*args):
        seen.append(args)
        return llm._success({"answer": True}, args[2], args[3])

    monkeypatch.setattr(llm, "_request_openai", request)
    with llm.case_call_budget():
        assert call().ok
        monkeypatch.setenv("OPENAI_MODEL", "changed")
        assert call().ok
    assert len(seen) == 2 and all(args[3] == "configured-model" for args in seen)
    events = [r.provider_attempt for r in caplog.records if hasattr(r, "provider_attempt")]
    assert all(event["provider"] == "openai" for event in events)


@pytest.mark.parametrize("mode", ["live", "record", "replay"])
@pytest.mark.parametrize("provider", ["gemini", "unknown short-openai-secret student@example.test"])
def test_invalid_provider_fails_safely_before_any_mode(monkeypatch, mode, provider, caplog):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_MODE", mode)
    result = call()
    assert not result.ok and "LLM_PROVIDER" in result.error
    assert "short-openai-secret" not in result.error + caplog.text
    assert "student@example.test" not in result.error + caplog.text


def test_missing_openai_model_and_key_fail_closed(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL")
    assert "OPENAI_MODEL" in call().error
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    monkeypatch.delenv("OPENAI_API_KEY")
    assert not call().ok


def test_schema_matches_probe_recursively_without_mutation():
    schema = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {"value": {"type": "string", "enum": ["a", "b"]}},
                            "required": ["value"],
                            "additionalProperties": True,
                        },
                        {"type": "null"},
                    ]
                },
            }
        },
    }
    original = copy.deepcopy(schema)
    normalized = llm._openai_schema(schema)
    assert normalized == strict_copy(schema)
    assert normalized["additionalProperties"] is False
    assert normalized["properties"]["items"]["items"]["anyOf"][0]["additionalProperties"] is False
    assert schema == original


@pytest.mark.parametrize(
    "content,refusal,finish,ok",
    [
        ('{"answer": "safe"}', None, "stop", True),
        ('{"answer": "safe"}', "refusal body", "stop", False),
        ('{"answer": "safe"}', None, "length", False),
        ("[]", None, "stop", False),
        ("not-json", None, "stop", False),
        (None, None, "stop", False),
    ],
)
def test_sdk_config_and_structured_parsing(monkeypatch, content, refusal, finish, ok):
    # Use the real adapter, mocking only the official SDK client.
    adapter = ORIGINAL_OPENAI_REQUEST
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, refusal=refusal),
                finish_reason=finish,
            )
        ]
    )
    constructor = MagicMock(return_value=client)
    monkeypatch.setattr(openai, "OpenAI", constructor)
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }
    if ok:
        result = adapter("private email", schema, "hash", "configured-model", "fake-key", 17)
        assert result == llm.LLMResult(
            True, {"answer": "safe"}, None, 0, "hash", "configured-model"
        )
    else:
        with pytest.raises(ValueError):
            adapter("private email", schema, "hash", "configured-model", "fake-key", 17)
    constructor.assert_called_once_with(
        api_key="fake-key",
        base_url="https://api.openai.com/v1",
        max_retries=0,
        timeout=17,
    )
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "configured-model" and kwargs["temperature"] == 0.0
    assert kwargs["reasoning_effort"] == "none"
    assert kwargs["response_format"]["json_schema"]["schema"] == strict_copy(schema)
    assert kwargs["response_format"]["json_schema"]["strict"] is True
    assert "additionalProperties" not in schema
    client.__exit__.assert_called_once()


ORIGINAL_OPENAI_REQUEST = llm._request_openai


def test_sdk_exception_identity_and_wrapper_parse_failure(monkeypatch, caplog):
    client = MagicMock()
    client.__enter__.return_value = client
    monkeypatch.setattr(openai, "OpenAI", MagicMock(return_value=client))
    error = sdk_error("invalid")
    client.chat.completions.create.side_effect = error
    with pytest.raises(openai.BadRequestError) as captured:
        ORIGINAL_OPENAI_REQUEST("private", {}, "hash", "model", "fake-key", 20)
    assert captured.value is error

    client.chat.completions.create.side_effect = None
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="not-json-private", refusal=None),
                finish_reason="stop",
            )
        ]
    )
    monkeypatch.setattr(llm, "_request_openai", ORIGINAL_OPENAI_REQUEST)
    assert not call().ok
    events = [r.provider_attempt for r in caplog.records if hasattr(r, "provider_attempt")]
    assert len(events) == 1 and events[0]["retryable"] is False
    assert "not-json-private" not in caplog.text


@pytest.mark.parametrize(
    "effort,temperature",
    [
        ("none", 0.0),
        ("none", 0.25),
        ("low", 0.0),
        ("medium", 0.0),
        ("high", 0.0),
    ],
)
def test_reasoning_effort_controls_temperature(monkeypatch, effort, temperature):
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", effort)
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content='{"answer": "safe"}', refusal=None),
                finish_reason="stop",
            )
        ]
    )
    constructor = MagicMock(return_value=client)
    monkeypatch.setattr(openai, "OpenAI", constructor)
    result = ORIGINAL_OPENAI_REQUEST(
        "synthetic", {}, "hash", "gpt-6-luna", "fake-key", 17, temperature=temperature
    )
    assert result.ok
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["reasoning_effort"] == effort
    if effort == "none":
        assert kwargs["temperature"] == temperature
    else:
        assert "temperature" not in kwargs
    assert constructor.call_args.kwargs["max_retries"] == 0
    client.chat.completions.create.assert_called_once()


def sdk_error(kind, code=None):
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    if kind == "timeout":
        return openai.APITimeoutError(request)
    if kind == "connection":
        return openai.APIConnectionError(request=request)
    cls, status = {
        "5xx": (openai.InternalServerError, 503),
        "429": (openai.RateLimitError, 429),
        "auth": (openai.AuthenticationError, 401),
        "permission": (openai.PermissionDeniedError, 403),
        "invalid": (openai.BadRequestError, 400),
    }[kind]
    return cls(
        "arbitrary raw provider body",
        response=httpx.Response(status, request=request),
        body={"code": code, "private": "raw email body"},
    )


@pytest.mark.parametrize(
    "kind,code,retryable",
    [
        ("timeout", None, True),
        ("connection", None, True),
        ("5xx", None, True),
        ("429", "rate_limit_exceeded", True),
        ("429", "insufficient_quota", False),
        ("429", None, False),
        ("auth", None, False),
        ("permission", None, False),
        ("invalid", None, False),
    ],
)
def test_error_mapping_no_fallback_and_no_body_logging(monkeypatch, caplog, kind, code, retryable):
    error = sdk_error(kind, code)
    seen = []

    def request(*args):
        seen.append(args)
        raise error

    monkeypatch.setattr(llm, "_request_openai", request)
    with llm.case_call_budget():
        result = call()
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - len(seen)
    assert not result.ok and len(seen) == (2 if retryable else 1)
    events = [r.provider_attempt for r in caplog.records if hasattr(r, "provider_attempt")]
    assert events[0]["retryable"] is retryable
    assert events[0]["will_retry"] is retryable
    assert events[-1]["stop_reason"] == ("retry_limit" if retryable else "non_retryable")
    assert events[0]["exception_class"] == type(error).__name__
    assert events[0]["http_status"] == getattr(error, "status_code", None)
    assert "arbitrary raw provider body" not in caplog.text + result.error
    assert "raw email body" not in caplog.text + result.error


def test_shared_budget_deadline_and_retry_cap(monkeypatch, caplog):
    seen = []
    monkeypatch.setattr(llm, "perf_counter", lambda: 100.0)

    def request(*args):
        seen.append(args)
        raise sdk_error("timeout")

    monkeypatch.setattr(llm, "_request_openai", request)
    with llm.case_call_budget():
        for _ in range(3):
            assert not llm._call_live("private", {}, "hash", "model", 50, 99, provider="openai").ok
        assert llm._BUDGET.get().remaining == 0
    assert len(seen) == llm.LLM_MAX_ATTEMPTS and all(args[-1] == llm.LLM_TIMEOUT_S for args in seen)
    seen.clear()
    with llm.case_call_budget():
        llm._BUDGET.get().deadline = 107.9
        assert not llm._call_live("private", {}, "hash", "model", 50, 0, provider="openai").ok
        assert seen[0][-1] == 7
        llm._BUDGET.get().deadline = 100.0
        assert not call().ok
        assert llm._BUDGET.get().remaining == llm.LLM_MAX_ATTEMPTS - 1
    assert len(seen) == 1
    assert llm.LLM_MAX_ATTEMPTS == 5 and llm.CASE_TIMEOUT_SECONDS == 60


def test_model_hash_isolates_cache_and_cassettes(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "CASSETTE_DIRECTORY", tmp_path)
    cache = {}
    monkeypatch.setattr(llm, "_load_cache", lambda h, m: cache.get(h))
    monkeypatch.setattr(llm, "_store_cache", lambda r: cache.update({r.prompt_hash: r}))
    monkeypatch.setenv("LLM_CACHE", "1")
    monkeypatch.setenv("LLM_MODE", "record")
    seen = []

    def request(*args):
        seen.append(args[3])
        return llm._success({"model": args[3]}, args[2], args[3])

    monkeypatch.setattr(llm, "_request_openai", request)
    hashes = []
    for model in ("model-a", "model-b"):
        monkeypatch.setenv("OPENAI_MODEL", model)
        result = call()
        hashes.append(result.prompt_hash)
        assert call().data == {"model": model}
    assert seen == ["model-a", "model-b"]
    assert hashes[0] != hashes[1] and set(cache) == set(hashes)
    assert llm._cache_key(hashes[0]) != llm._cache_key(hashes[1])
    assert len(list(tmp_path.glob("*.json"))) == 2
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setattr(
        llm, "_request_openai", lambda *a: pytest.fail("replay must not call provider")
    )
    for model in ("model-a", "model-b"):
        monkeypatch.setenv("OPENAI_MODEL", model)
        assert call().data == {"model": model}


@pytest.mark.parametrize("mode", ["replay", "live"])
def test_unscoped_identity_is_not_used(monkeypatch, tmp_path, mode):
    unscoped = hashlib.sha256(
        json.dumps(
            ["configured-model", {}, "private email", 0.0], sort_keys=True, ensure_ascii=False
        ).encode()
    ).hexdigest()
    path = tmp_path / f"{unscoped}.json"
    path.write_text(
        json.dumps({"data": {"unscoped": True}, "model": "configured-model"}), encoding="utf-8"
    )
    original = path.read_bytes()
    monkeypatch.setattr(llm, "CASSETTE_DIRECTORY", tmp_path)
    monkeypatch.setenv("LLM_CACHE", "1")
    monkeypatch.setenv("LLM_MODE", mode)
    lookups = []

    def load(h, m):
        lookups.append(h)
        return llm._success({"unscoped": True}, h, m) if h == unscoped else None

    monkeypatch.setattr(llm, "_load_cache", load)
    monkeypatch.delenv("OPENAI_API_KEY")
    assert not call().ok
    assert unscoped not in lookups and path.read_bytes() == original


def test_openai_key_redaction_including_case_uuid(monkeypatch):
    assert "short-openai-secret" not in sanitize_diagnostic("short-openai-secret")
    secret = "4cb9832c-3df9-4b52-a5d8-314f29e25bde"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    assert sanitize_case_id(secret, prompt="private") != secret
