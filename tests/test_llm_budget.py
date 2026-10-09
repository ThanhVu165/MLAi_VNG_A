from __future__ import annotations

import pytest
import openai
from openai._exceptions import httpx2 as httpx

from infra import llm


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "sleep", lambda _: None)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-test-key")


def test_budget_counts_retries_and_never_exceeds_configured_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def unavailable(*args: object) -> llm.LLMResult:
        calls.append(1)
        raise TimeoutError("offline")

    monkeypatch.setattr(llm, "_request_openai", unavailable)
    with llm.case_call_budget():
        for _ in range(4):
            result = llm._call_live("test", {}, "hash", "model", 20, 10)
            assert not result.ok
    assert len(calls) == llm.LLM_MAX_ATTEMPTS


def test_permanent_error_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def invalid(*args: object) -> llm.LLMResult:
        calls.append(1)
        raise ValueError("bad configuration")

    monkeypatch.setattr(llm, "_request_openai", invalid)
    with llm.case_call_budget():
        assert not llm._call_live("test", {}, "hash", "model", 20, 1).ok
    assert len(calls) == 1


def test_server_error_is_retried_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    server_error = openai.InternalServerError(
        "offline", response=httpx.Response(503, request=request), body={}
    )

    def unavailable(*args: object) -> llm.LLMResult:
        calls.append(1)
        raise server_error

    monkeypatch.setattr(llm, "_request_openai", unavailable)
    with llm.case_call_budget():
        assert not llm._call_live("test", {}, "hash", "model", 20, 1).ok
    assert len(calls) == 2
