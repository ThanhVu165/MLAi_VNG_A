from __future__ import annotations

import pytest

from infra import llm


def test_budget_counts_retries_and_never_exceeds_four_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def unavailable(*args: object) -> llm.LLMResult:
        calls.append(1)
        raise TimeoutError("offline")

    monkeypatch.setenv("GOOGLE_API_KEY", "test-not-a-secret")
    monkeypatch.setattr(llm, "_request_gemini", unavailable)
    with llm.case_call_budget():
        for _ in range(4):
            result = llm._call_live("test", {}, "hash", "model", 20, 10)
            assert not result.ok
    assert len(calls) == 4


def test_permanent_error_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def invalid(*args: object) -> llm.LLMResult:
        calls.append(1)
        raise ValueError("bad configuration")

    monkeypatch.setenv("GOOGLE_API_KEY", "test-not-a-secret")
    monkeypatch.setattr(llm, "_request_gemini", invalid)
    with llm.case_call_budget():
        assert not llm._call_live("test", {}, "hash", "model", 20, 1).ok
    assert len(calls) == 1
