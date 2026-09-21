from __future__ import annotations

import inspect
from datetime import datetime, timezone

import core.pipeline as pipeline
from core.ground_guard import GroundednessResult
from core.types import (
    CaseInput,
    CaseStatus,
    ChunkLabel,
    Decision,
    Domain,
    DraftReply,
    EvidenceChunk,
    EvidenceResult,
    EvidenceStatus,
    Extraction,
    PolicyDecision,
    RequestItem,
)
from infra import db


def _input(channel: str) -> CaseInput:
    return CaseInput(
        sender="student@example.edu",
        subject="Hỏi hạn rút học phần",
        body="Em cần biết hạn rút học phần trong học kỳ này là khi nào?",
        received_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        channel=channel,  # type: ignore[arg-type]
    )


def _extraction() -> Extraction:
    return Extraction(
        "vi",
        [
            RequestItem(
                Domain.COURSE_WITHDRAWAL, "hạn rút học phần", True, False, False, False, False
            )
        ],
        {"semester": "2026-1"},
        [],
        False,
        "{}",
    )


def _evidence() -> EvidenceResult:
    return EvidenceResult(
        EvidenceStatus.OK,
        [
            EvidenceChunk(
                "chunk-1",
                "doc-1",
                "Điều 1",
                "Hạn rút học phần là ngày 30/09/2026.",
                Domain.COURSE_WITHDRAWAL,
                ChunkLabel.AUTO_ANSWERABLE,
                0.9,
                datetime(2026, 1, 1, tzinfo=timezone.utc).date(),
                None,
                [],
                [],
                False,
                False,
            )
        ],
        [],
    )


def _install_success_path(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    evidence = _evidence()
    decision = PolicyDecision(Decision.AUTO_REPLY, None, "P05", "Đủ căn cứ.", ["chunk-1"], "cv")
    draft = DraftReply("Hạn rút học phần", "Hạn là 30/09/2026. [chunk-1]", ["chunk-1"], True, [])
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: "cv")
    monkeypatch.setattr(pipeline, "extract_facts", lambda body, case_id: _extraction())
    monkeypatch.setattr(pipeline, "retrieve_evidence", lambda **kwargs: evidence)
    monkeypatch.setattr(pipeline, "validate_evidence", lambda **kwargs: evidence)
    monkeypatch.setattr(pipeline, "decide_policy", lambda policy_input: decision)
    monkeypatch.setattr(pipeline, "generate_reply", lambda **kwargs: draft)
    monkeypatch.setattr(
        pipeline,
        "guard_groundedness",
        lambda **kwargs: GroundednessResult(draft, None, []),
    )


def test_paste_inbox_and_verify_share_the_same_pipeline(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    _install_success_path(monkeypatch)

    results = [pipeline.process_case(_input(channel)) for channel in ("paste", "inbox", "verify")]

    assert {result.status for result in results} == {CaseStatus.PENDING_SEND}
    assert {result.decision.rule_id for result in results} == {"P05"}
    assert {tuple(result.draft.citations) for result in results if result.draft} == {("chunk-1",)}
    assert all(
        set(result.step_latencies_ms) == {f"R{step}" for step in range(15)} for result in results
    )
    assert "if inp.channel" not in inspect.getsource(pipeline.process_case)


def test_pipeline_step_failure_returns_p04_without_raising(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: "cv")
    monkeypatch.setattr(
        pipeline,
        "extract_facts",
        lambda body, case_id: (_ for _ in ()).throw(RuntimeError("extract failed")),
    )

    result = pipeline.process_case(_input("verify"))

    assert result.decision.decision is Decision.ESCALATE
    assert result.decision.rule_id == "P04"
    assert result.status is CaseStatus.AWAITING_HUMAN
