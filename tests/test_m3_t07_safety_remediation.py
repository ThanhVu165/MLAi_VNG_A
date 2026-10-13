"""M3-T07: replay R11 thật với SQLite synthetic và không có provider/email LIVE."""

from __future__ import annotations

import json
from datetime import datetime
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

from core.pipeline import process_case
from core.resume import validate_human_draft
from core.types import CaseInput, CaseStatus, DraftReply
from core.worker import worker_tick
from infra import db, llm
from infra.audit import events_for_case
from infra.llm import LLMResult


R11_CASSETTE = "2447ffcce6d7372fd5cdc1810653804259f0f7b82402b57472679884de20d015.json"
HUMAN_CHOICE = "Yêu cầu bản dịch"
HUMAN_REASON = "Đề nghị bổ sung nội dung bằng tiếng Việt hoặc tiếng Anh để đối chiếu quy định."


def _restart_snapshot(case_id: str, status: CaseStatus) -> None:
    code = """
import os
from infra import db
case_id = os.environ["M3_T07_CASE_ID"]
expected = os.environ["M3_T07_STATUS"]
case = db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
human = db.fetch_one("SELECT choice, reason, actor FROM human_decisions WHERE case_id = ?", (case_id,))
drafts = db.fetch_one("SELECT COUNT(*) AS n FROM drafts WHERE case_id = ?", (case_id,))
assert case is not None and case["status"] == expected
assert human is not None and all(human[field] for field in ("choice", "reason", "actor"))
assert drafts is not None and drafts["n"] == 1
"""
    environment = os.environ.copy()
    environment.update(
        DATABASE_PATH=str(db.DEFAULT_DATABASE_PATH.resolve()),
        LLM_MODE="replay",
        LLM_CACHE="0",
        M3_T07_CASE_ID=case_id,
        M3_T07_STATUS=status,
        PYTHONDONTWRITEBYTECODE="1",
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).parents[1],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture
def replay_r11(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[str, dict]:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "runtime.db")
    monkeypatch.setattr(llm, "CASSETTE_DIRECTORY", Path(__file__).parent / "cassettes")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    assert (llm.CASSETTE_DIRECTORY / R11_CASSETTE).is_file()

    result = process_case(
        CaseInput(
            "synthetic@example.invalid",
            "Synthetic DEV — yêu cầu bản dịch",
            "学生の質問を確認してください。",
            datetime.fromisoformat("2026-09-21T09:04:00+07:00"),
            "paste",
        )
    )
    assert result.status is CaseStatus.AWAITING_HUMAN
    page = runpy.run_path(str(Path(__file__).parents[1] / "pages/2_Hang_cho_duyet.py"))
    case = next(item for item in page["_queue_cases"]() if item.case_id == result.case_id)
    record = page["_open_decision"](case.case_id)
    page["_record_decision"](case, record, HUMAN_CHOICE, HUMAN_REASON)
    return case.case_id, page


def test_existing_r11_replay_creates_one_safe_pending_approval_draft(replay_r11) -> None:
    case_id, page = replay_r11

    worker_tick()
    worker_tick()

    case = db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
    job = db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))
    drafts = db.fetch_all("SELECT * FROM drafts WHERE case_id = ?", (case_id,))
    human = db.fetch_one(
        "SELECT choice, reason, actor FROM human_decisions WHERE case_id = ?", (case_id,)
    )
    r11_calls = db.fetch_all(
        "SELECT ok FROM step_latencies WHERE case_id = ? AND step = 'R11_resume'", (case_id,)
    )
    assert case is not None and case["status"] == CaseStatus.PENDING_APPROVAL
    assert job is not None and job["state"] == "done"
    assert len(drafts) == 1 and drafts[0]["kind"] == "resume" and drafts[0]["grounded"] == 1
    assert human is not None and dict(human) == {
        "choice": HUMAN_CHOICE,
        "reason": HUMAN_REASON,
        "actor": "HUMAN:local",
    }
    assert HUMAN_CHOICE in drafts[0]["body"] and HUMAN_REASON in drafts[0]["body"]
    assert json.loads(drafts[0]["guard_failures_json"]) == []
    assert len(r11_calls) == 1 and r11_calls[0]["ok"] == 1
    actions = [event.action for event in events_for_case(case_id)]
    assert actions.count("HUMAN_DECISION") == actions.count("CASE_RESUMED") == 1
    assert "CASE_ERROR" not in actions and "SEND_DISPATCHED" not in actions
    _restart_snapshot(case_id, CaseStatus.PENDING_APPROVAL)

    preview = next(item for item in page["_preview_drafts"]() if item.case_id == case_id)
    page["_approve_send"](preview)
    with pytest.raises(ValueError, match="không còn chờ duyệt"):
        page["_approve_send"](preview)
    actions = [event.action for event in events_for_case(case_id)]
    assert actions.count("HUMAN_APPROVED_SEND") == 1
    assert "SEND_DISPATCHED" not in actions
    _restart_snapshot(case_id, CaseStatus.SENT)


@pytest.mark.parametrize(
    "data",
    [
        {"subject": "Thiếu body", "citations": []},
        {
            "subject": "Mâu thuẫn",
            "body": "Chuyên viên không yêu cầu bản dịch.",
            "citations": [],
        },
        {
            "subject": "Vượt thẩm quyền",
            "body": "Yêu cầu của bạn đã được duyệt.",
            "citations": [],
        },
        {
            "subject": "Bịa số liệu",
            "body": "Vui lòng nộp lệ phí 500.000 đồng.",
            "citations": [],
        },
        {
            "subject": "Bịa căn cứ",
            "body": "Đề nghị bổ sung bản dịch [không-tồn-tại].",
            "citations": ["không-tồn-tại"],
        },
    ],
)
def test_unsafe_r11_candidate_fails_closed(replay_r11, monkeypatch, data) -> None:
    case_id, _ = replay_r11
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(True, data, None, 0, "test", "test"),
    )

    worker_tick()

    case = db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
    job = db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))
    drafts = db.fetch_one("SELECT COUNT(*) AS n FROM drafts WHERE case_id = ?", (case_id,))
    human = db.fetch_one(
        "SELECT choice, reason, actor FROM human_decisions WHERE case_id = ?", (case_id,)
    )
    actions = [event.action for event in events_for_case(case_id)]
    assert case is not None and case["status"] == CaseStatus.HUMAN_DECIDED
    assert job is not None and job["state"] == "failed"
    assert drafts is not None and drafts["n"] == 0
    assert human is not None and dict(human) == {
        "choice": HUMAN_CHOICE,
        "reason": HUMAN_REASON,
        "actor": "HUMAN:local",
    }
    assert actions.count("CASE_ERROR") == 1
    assert "CASE_RESUMED" not in actions and "HUMAN_APPROVED_SEND" not in actions


def test_edited_resume_draft_cannot_reverse_human_decision(replay_r11) -> None:
    case_id, _ = replay_r11
    worker_tick()
    row = db.fetch_one("SELECT * FROM drafts WHERE case_id = ?", (case_id,))
    assert row is not None
    contradictory = DraftReply(
        row["subject"],
        f'{row["body"]}\n\nChuyên viên không yêu cầu bản dịch.',
        json.loads(row["citations_json"]),
        False,
        [],
    )

    checked = validate_human_draft(case_id, contradictory)

    assert not checked.grounded and "human_conflict" in checked.guard_failures


def test_authority_wording_is_allowed_only_from_positive_human_decision(
    replay_r11, monkeypatch
) -> None:
    case_id, _ = replay_r11
    choice = "Chấp thuận"
    reason = "Chuyên viên đã xem xét hồ sơ và ghi nhận quyết định này."
    db.execute(
        "UPDATE human_decisions SET choice = ?, reason = ? WHERE case_id = ?",
        (choice, reason, case_id),
    )
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(
            True,
            {"subject": "Kết quả", "body": "Yêu cầu đã được duyệt.", "citations": []},
            None,
            0,
            "test",
            "test",
        ),
    )

    worker_tick()

    case = db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
    draft = db.fetch_one("SELECT body, grounded FROM drafts WHERE case_id = ?", (case_id,))
    assert case is not None and case["status"] == CaseStatus.PENDING_APPROVAL
    assert draft is not None and draft["grounded"] == 1
    assert choice in draft["body"] and reason in draft["body"]


def test_authority_wording_is_not_authorized_by_reason_only(replay_r11, monkeypatch) -> None:
    case_id, _ = replay_r11
    choice = "Yêu cầu bổ sung"
    reason = "Hồ sơ tham chiếu trước đây đã được duyệt, nhưng case này còn thiếu tài liệu."
    db.execute(
        "UPDATE human_decisions SET choice = ?, reason = ? WHERE case_id = ?",
        (choice, reason, case_id),
    )
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(
            True,
            {"subject": "Kết quả", "body": "Yêu cầu của bạn đã được duyệt.", "citations": []},
            None,
            0,
            "test",
            "test",
        ),
    )

    worker_tick()

    case = db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
    job = db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))
    drafts = db.fetch_one("SELECT COUNT(*) AS n FROM drafts WHERE case_id = ?", (case_id,))
    actions = [event.action for event in events_for_case(case_id)]
    assert case is not None and case["status"] == CaseStatus.HUMAN_DECIDED
    assert job is not None and job["state"] == "failed"
    assert drafts is not None and drafts["n"] == 0
    assert actions.count("CASE_ERROR") == 1
    assert "CASE_RESUMED" not in actions and "HUMAN_APPROVED_SEND" not in actions


def test_review_only_choice_does_not_authorize_approval_claim(replay_r11, monkeypatch) -> None:
    case_id, _ = replay_r11
    choice = "Đồng ý xem xét thêm"
    reason = "Cần kiểm tra tài liệu trước khi quyết định."
    db.execute(
        "UPDATE human_decisions SET choice = ?, reason = ? WHERE case_id = ?",
        (choice, reason, case_id),
    )
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(
            True,
            {"subject": "Kết quả", "body": "Yêu cầu của bạn đã được duyệt.", "citations": []},
            None,
            0,
            "test",
            "test",
        ),
    )

    worker_tick()

    case = db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
    job = db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))
    drafts = db.fetch_one("SELECT COUNT(*) AS n FROM drafts WHERE case_id = ?", (case_id,))
    actions = [event.action for event in events_for_case(case_id)]
    assert case is not None and case["status"] == CaseStatus.HUMAN_DECIDED
    assert job is not None and job["state"] == "failed"
    assert drafts is not None and drafts["n"] == 0
    assert actions.count("CASE_ERROR") == 1
    assert "CASE_RESUMED" not in actions and "HUMAN_APPROVED_SEND" not in actions
