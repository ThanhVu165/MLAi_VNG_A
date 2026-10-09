"""Regression offline cho clock grounding và một lần sửa provenance basis."""

from copy import deepcopy
from datetime import date, datetime, timezone
import socket

import pytest

from core import ground_guard, question_gen
from core.types import (
    CaseInput,
    ChunkLabel,
    Domain,
    DraftReply,
    EscalationType,
    EvidenceChunk,
    EvidenceResult,
    EvidenceStatus,
    Extraction,
)
from infra import llm


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Network/DB/provider calls forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(llm, "execute", forbidden)
    monkeypatch.setattr(llm, "fetch_one", forbidden)
    monkeypatch.setattr(llm, "_record_latency", lambda *args: None)
    monkeypatch.setattr(llm, "_store_cache", lambda *args: None)
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setattr(question_gen, "log_event", lambda **kwargs: None)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "offline-model")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-offline-key")
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "0")


def evidence(text="Câu đầu.\nĐiểm a) Câu sau."):
    chunk = EvidenceChunk(
        "chunk-1",
        "doc-1",
        "Điều 1",
        text,
        Domain.GRADE_APPEAL,
        ChunkLabel.AUTO_ANSWERABLE,
        1.0,
        date(2026, 1, 1),
        None,
        [],
        [],
        False,
        False,
    )
    return EvidenceResult(EvidenceStatus.OK, [chunk], [])


@pytest.mark.parametrize(
    "draft,source,failed",
    [
        ("5 p.m.", "17:00", False),
        ("5:00 p.m.", "17 giờ 00", False),
        ("5:00 p.m.", "17h00", False),
        ("5 p.m.", "17 giờ", False),
        ("5 a.m.", "17:00", True),
        ("12:00 a.m.", "00:00", False),
        ("12 a.m.", "0 giờ", False),
        ("12 p.m.", "12:00", False),
        ("12:00 p.m.", "12 giờ 00", False),
        ("5:30 p.m.", "17 giờ 00", True),
        ("5:30 p.m.", "17:30", False),
        ("5:30 p.m.", "17 giờ", True),
        ("5 p.m. and 5 days", "17:00", True),
        ("5:00", "17:00", True),
        ("5 p.m.", "117:00", True),
        ("5 p.m.", "17:000", True),
        ("5 p.m.", "17 giờ 30", True),
        ("5 p.m. on 06/10/2026", "17:00 on 05/10/2026", True),
        ("5 p.m. Điều 5", "17:00 Điều 17", True),
        ("5 p.m. Mẫu PK-05", "17:00 Mẫu PK-17", True),
        ("5 p.m. on 05/10/2026 Điều 2 Mẫu PK-01", "17:00 on 05/10/2026 Điều 2 Mẫu PK-01", False),
    ],
)
def test_clock_is_removed_only_when_exact_equivalent_is_grounded(draft, source, failed):
    result = DraftReply("Synthetic", draft, ["chunk-1"], True, [])
    assert ground_guard._unsupported_value_failure(result, evidence(source)) is failed
    assert result.body == draft


def payload(quote="Câu đầu.", chunk_id="chunk-1"):
    return {
        "summary": "Synthetic summary",
        "facts": [],
        "basis": [{"chunk_id": chunk_id, "quote": quote}],
        "question": "Chuyên viên có chấp thuận yêu cầu này không?",
        "options": ["Có", "Không"],
    }


def generate():
    return question_gen.generate_escalation_card(
        case_id="synthetic-case",
        actor="SYSTEM",
        corpus_version="cv",
        escalation_type=EscalationType.AUTHORITY_REQUIRED,
        extraction=Extraction("vi", [], {}, [], False, "{}"),
        evidence=evidence(),
        inp=CaseInput(
            "synthetic@example.test",
            "Synthetic",
            "Synthetic request",
            datetime(2026, 10, 5, tzinfo=timezone.utc),
            "verify",
        ),
    )


@pytest.mark.parametrize(
    "initial,repaired,error,expected_calls",
    [
        (payload(), None, None, 1),
        (payload("Câu đầu. Câu sau."), payload(), None, 2),
        (payload(chunk_id="absent"), payload(), None, 2),
        (
            payload("Câu đầu. Câu sau."),
            payload("Câu đầu. Câu sau."),
            question_gen.BasisValidationError,
            2,
        ),
        (payload("Câu  đầu."), payload("Câu  đầu."), question_gen.BasisValidationError, 2),
        (dict(payload(), basis=None), None, ValueError, 1),
        (payload(""), None, ValueError, 1),
        (dict(payload(), summary=""), None, ValueError, 1),
        (None, None, ValueError, 1),
        (payload("Câu đầu. Câu sau."), None, ValueError, 2),
    ],
)
def test_basis_repairs_only_provenance_once(monkeypatch, initial, repaired, error, expected_calls):
    responses = [deepcopy(initial), deepcopy(repaired)]
    calls = []

    def call(prompt, **kwargs):
        calls.append((prompt, kwargs))
        data = responses[len(calls) - 1]
        return llm.LLMResult(
            data is not None, data or {}, None if data else "offline failure", 0, "h", "m"
        )

    monkeypatch.setattr(question_gen, "call_json", call)
    if error:
        with pytest.raises(error):
            generate()
    else:
        assert generate().basis == [("Điều 1", "Câu đầu.")]
    assert len(calls) == expected_calls
    assert calls[0][1]["step"] == "R7_question"
    for _, kwargs in calls:
        assert kwargs["case_id"] == "synthetic-case" and kwargs["temperature"] == 0.0
        assert kwargs["schema"] is question_gen.QUESTION_SCHEMA
    if expected_calls == 2:
        assert calls[1][1]["step"] == "R7_question_repair"
        assert calls[1][0].startswith(calls[0][0])
        assert all(
            word in calls[1][0]
            for word in ("nguyên văn", "liên tục", "Không nối", '"Điểm a)"', "không diễn đạt lại")
        )


def test_basis_repair_preserves_primary_fields(monkeypatch):
    primary = dict(
        payload("Câu đầu. Câu sau."),
        summary="Primary summary",
        facts=["Primary fact"],
        question="Primary question?",
        options=["Primary yes", "Primary no"],
    )
    repaired = dict(
        payload("Câu sau."),
        summary="Repair summary",
        facts=["Repair fact"],
        question="Repair question?",
        options=["Repair yes", "Repair no"],
    )
    calls = []

    def call(prompt, **kwargs):
        calls.append(kwargs["step"])
        data = (primary, repaired)[len(calls) - 1]
        return llm.LLMResult(True, deepcopy(data), None, 0, "h", "m")

    monkeypatch.setattr(question_gen, "call_json", call)
    card = generate()
    for field in ("summary", "facts", "question", "options"):
        assert getattr(card, field) == primary[field]
    assert card.basis == [("Điều 1", "Câu sau.")]
    assert calls == ["R7_question", "R7_question_repair"]


@pytest.mark.parametrize("limit", ["available", "attempts_exhausted", "deadline_exhausted"])
def test_repair_uses_real_public_wrapper_shared_budget(monkeypatch, caplog, limit):
    requests = []

    def request(*args):
        requests.append(args)
        if len(requests) == 1:
            if limit == "deadline_exhausted":
                llm._BUDGET.get().deadline = llm.perf_counter() - 1
            return llm._success(payload("Câu đầu. Câu sau."), args[2], args[3])
        return llm._success(payload(), args[2], args[3])

    monkeypatch.setattr(llm, "_request_openai", request)
    monkeypatch.setattr(llm, "perf_counter", lambda: 100.0)
    with llm.case_call_budget():
        budget = llm._BUDGET.get()
        deadline = budget.deadline
        preconsumed = llm.LLM_MAX_ATTEMPTS - 1 if limit == "attempts_exhausted" else 0
        for _ in range(preconsumed):
            llm._attempt_timeout(30)
        assert budget.remaining == llm.LLM_MAX_ATTEMPTS - preconsumed
        if limit == "available":
            assert generate().basis == [("Điều 1", "Câu đầu.")]
            assert len(requests) == 2
            assert budget.deadline == deadline
        else:
            with pytest.raises(ValueError):
                generate()
            assert len(requests) == 1
            if limit == "attempts_exhausted":
                assert budget.remaining == 0
                assert budget.deadline == deadline > llm.perf_counter()
            else:
                assert budget.remaining > 0
                assert budget.deadline < llm.perf_counter()
        assert budget.remaining == llm.LLM_MAX_ATTEMPTS - preconsumed - len(requests)
        events = [r.provider_attempt for r in caplog.records if hasattr(r, "provider_attempt")]
        started = [e for e in events if e["event"] == "llm_provider_attempt"]
        skipped = [e for e in events if e["event"] == "llm_provider_attempt_skipped"]
        assert len(started) == len(requests)
        if limit == "available":
            assert [e["step"] for e in started] == ["R7_question", "R7_question_repair"]
            assert skipped == []
        else:
            assert len(skipped) == 2
            assert all(e["step"] == "R7_question_repair" for e in skipped)
            assert all(e["stop_reason"] == "case_budget_or_deadline" for e in skipped)
            assert all(e["attempts_remaining_before"] == budget.remaining for e in skipped)
            assert all(e["attempts_remaining_after"] == budget.remaining for e in skipped)
            assert all(e["retryable"] is False and e["will_retry"] is False for e in skipped)
        assert llm._BUDGET.get() is budget
    assert llm.LLM_MAX_ATTEMPTS == 5 and llm.CASE_TIMEOUT_SECONDS == 60
