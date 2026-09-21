from datetime import datetime, timedelta, timezone

import core.pipeline as pipeline
from core.types import CaseInput, CaseStatus, Decision
from infra import db
from infra.audit import events_for_case


def _input(*, sender: str = "student@example.edu") -> CaseInput:
    return CaseInput(
        sender=sender,
        subject="Hỏi quy trình",
        body="Em cần biết quy trình xử lý yêu cầu này.",
        received_at=datetime(2026, 9, 21, 8, 30, tzinfo=timezone(timedelta(hours=7))),
        channel="paste",
    )


def test_r0_creates_one_case_and_freezes_corpus_version(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "app.db"
    versions = iter(("cv_before", "cv_after"))
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: next(versions))

    result = pipeline.process_case(_input())

    rows = db.fetch_all("SELECT * FROM cases", database_path=database_path)
    events = events_for_case(result.case_id, database_path=str(database_path))
    assert len(rows) == 1
    assert rows[0]["case_id"] == result.case_id
    assert rows[0]["status"] == CaseStatus.RECEIVED
    assert rows[0]["corpus_version"] == result.corpus_version == "cv_before"
    assert rows[0]["received_at"].endswith("Z")
    assert result.case_id.startswith("c_") and len(result.case_id) == 28
    assert len(events) == 1 and events[0].action == "CASE_RECEIVED"


def test_r0_marks_missing_required_input_invalid(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "app.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)

    result = pipeline.process_case(_input(sender=""))

    row = db.fetch_one(
        "SELECT status FROM cases WHERE case_id = ?", (result.case_id,), database_path=database_path
    )
    assert result.decision.decision is Decision.INVALID_INPUT
    assert result.status is CaseStatus.INVALID_INPUT
    assert row is not None and row["status"] == CaseStatus.INVALID_INPUT
