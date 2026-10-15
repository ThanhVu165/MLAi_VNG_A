"""M3-T06: SQLite/handler thật; LLM fixture là stub, không phải runtime replay E2E."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.controls import is_automation_paused, pause_automation, resume_automation
from core.dispatch import cancel_send, create_correction_email, dispatch_due, escalate_from_pending
from core.pipeline import load_result, process_case
from core.types import CaseStatus, Decision
from core.worker import queue_resume, submit_case, worker_tick
from infra import db
from infra import llm
from infra.llm import LLMResult
from infra.telemetry import snapshot
from test_runtime_worker import _email, approval_case as _approval_case, runtime as _runtime
from ui.presentation import decision_label, status_label

runtime = _runtime
approval_case = _approval_case


def _case(case_id: str) -> dict:
    row = db.fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    assert row is not None
    return dict(row)


def _actions(case_id: str) -> list[str]:
    return [
        row["action"]
        for row in db.fetch_all(
            "SELECT action FROM audit_events WHERE case_id = ? ORDER BY rowid", (case_id,)
        )
    ]


def _due(case_id: str) -> None:
    db.execute(
        "UPDATE cases SET send_deadline = ? WHERE case_id = ?",
        (db.to_utc_iso(datetime.now(timezone.utc) - timedelta(seconds=1)), case_id),
    )


def _restart() -> None:
    # Tiến trình mới đọc cùng SQLite; chặn network/provider và mọi bước LLM trước worker.
    code = """
import socket
import openai
class OfflineViolation(BaseException):
    pass
def forbidden(*args, **kwargs):
    raise OfflineViolation('M3_T06_OFFLINE_ONLY')
socket.socket.connect = socket.socket.connect_ex = socket.socket.sendto = forbidden
socket.create_connection = socket.getaddrinfo = forbidden
openai.OpenAI = openai.AsyncOpenAI = forbidden
from core import extract, retrieval, generate, resume
for module in (extract, retrieval, generate, resume):
    module.call_json = forbidden
from core.worker import worker_tick
worker_tick()
worker_tick()
"""
    environment = os.environ.copy()
    environment.update(
        DATABASE_PATH=str(db.DEFAULT_DATABASE_PATH.resolve()),
        LLM_MODE="replay",
        LLM_CACHE="0",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONIOENCODING="utf-8",
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


def test_pause_resume_pending_send_survives_process_restart(runtime) -> None:
    result = process_case(_email())
    assert result.status is CaseStatus.PENDING_SEND
    _due(result.case_id)
    pause_automation("ADMIN:test", "Tạm dừng gửi để kiểm chứng restart synthetic.")
    before = _case(result.case_id)
    _restart()
    assert is_automation_paused()
    assert _case(result.case_id) == before
    assert "SEND_DISPATCHED" not in _actions(result.case_id)
    resume_automation("ADMIN:test")
    _restart()
    assert _case(result.case_id)["status"] == CaseStatus.SENT
    assert _case(result.case_id)["send_deadline"] is None
    assert _actions(result.case_id).count("SEND_DISPATCHED") == 1
    assert [
        row["action"]
        for row in db.fetch_all(
            "SELECT action FROM audit_events WHERE case_id IS NULL ORDER BY rowid"
        )
    ] == ["PAUSE_AUTOMATION", "RESUME_AUTOMATION"]


def test_global_pause_allows_explicit_human_approval_and_persists(approval_case) -> None:
    page, preview = approval_case
    assert is_automation_paused()
    assert _case(preview.case_id)["status"] == CaseStatus.PENDING_APPROVAL
    page["_approve_send"](preview)
    _restart()
    assert is_automation_paused()
    assert _case(preview.case_id)["status"] == CaseStatus.SENT
    assert _actions(preview.case_id).count("HUMAN_APPROVED_SEND") == 1
    assert "SEND_DISPATCHED" not in _actions(preview.case_id)
    with pytest.raises(ValueError, match="không còn chờ duyệt"):
        page["_approve_send"](preview)


def test_cancel_before_send_survives_restart_and_rejects_repeat(runtime) -> None:
    result = process_case(_email())
    assert result.status is CaseStatus.PENDING_SEND
    cancel_send(result.case_id, "HUMAN:test", "Hủy dữ liệu synthetic trước gửi.")
    _restart()
    assert _case(result.case_id)["status"] == CaseStatus.CANCELLED
    assert _case(result.case_id)["send_deadline"] is None
    assert _actions(result.case_id).count("CANCEL_SEND") == 1
    assert "SEND_DISPATCHED" not in _actions(result.case_id)
    with pytest.raises(ValueError, match="PENDING_SEND"):
        cancel_send(result.case_id, "HUMAN:test", "Thử hủy lần hai.")


def test_cancel_audit_failure_rolls_back_then_retry_succeeds(runtime, monkeypatch) -> None:
    result = process_case(_email())
    before = _case(result.case_id)
    actions = _actions(result.case_id)

    def fail_audit(**kwargs: object) -> None:
        raise RuntimeError("synthetic cancel audit failure")

    with monkeypatch.context() as patch:
        patch.setattr("core.dispatch.log_event", fail_audit)
        with pytest.raises(RuntimeError, match="synthetic cancel audit failure"):
            cancel_send(result.case_id, "HUMAN:test", "Hủy synthetic.")
    assert _case(result.case_id) == before
    assert _actions(result.case_id) == actions
    cancel_send(result.case_id, "HUMAN:test", "Thử lại sau lỗi audit synthetic.")
    assert _case(result.case_id)["status"] == CaseStatus.CANCELLED
    assert _actions(result.case_id).count("CANCEL_SEND") == 1


def test_queue_human_decision_resume_failure_and_retry(runtime, monkeypatch) -> None:
    page = runpy.run_path(str(Path(__file__).parents[1] / "pages/2_Hang_cho_duyet.py"))
    result = process_case(_email())
    escalate_from_pending(result.case_id, actor="HUMAN:test", reason="Cần người đối chiếu.")
    case = next(case for case in page["_queue_cases"]() if case.case_id == result.case_id)
    assert case.status == CaseStatus.AWAITING_HUMAN
    record = page["_open_decision"](case.case_id)
    choice, reason = "Yêu cầu bổ sung", "Cần bản chụp nội dung đang hỏi."
    page["_record_decision"](case, record, choice, reason)
    with pytest.raises(ValueError, match="đã có quyết định"):
        page["_record_decision"](case, record, choice, reason)
    decided = dict(db.fetch_one("SELECT * FROM human_decisions WHERE id = ?", (record["id"],)))
    assert (decided["choice"], decided["reason"]) == (choice, reason)
    pause_automation("ADMIN:test", "Tạm dừng global không xóa quyết định của người.")
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *a, **k: LLMResult(False, {}, "synthetic timeout", 0, "test", "test"),
    )
    worker_tick()
    assert _case(case.case_id)["status"] == CaseStatus.HUMAN_DECIDED
    job = db.fetch_one("SELECT * FROM case_jobs WHERE case_id = ?", (case.case_id,))
    assert job["state"] == "failed"
    assert (
        dict(db.fetch_one("SELECT * FROM human_decisions WHERE id = ?", (record["id"],))) == decided
    )
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *a, **k: LLMResult(
            True,
            {"subject": "Bổ sung", "body": f"{choice}. {reason}", "citations": []},
            None,
            0,
            "test",
            "test",
        ),
    )
    queue_resume(case.case_id)
    worker_tick()
    preview = next(p for p in page["_preview_drafts"]() if p.case_id == case.case_id)
    assert _case(case.case_id)["status"] == CaseStatus.PENDING_APPROVAL
    assert is_automation_paused()
    page["_approve_send"](preview)
    _restart()
    assert _case(case.case_id)["status"] == CaseStatus.SENT
    actions = _actions(case.case_id)
    assert actions.count("HUMAN_DECISION") == actions.count("CASE_RESUMED") == 1
    assert actions.count("HUMAN_APPROVED_SEND") == 1
    assert "CASE_ERROR" in actions and "SEND_DISPATCHED" not in actions


def test_correction_preserves_sent_parent_and_requires_approval(approval_case) -> None:
    page, preview = approval_case
    page["_approve_send"](preview)
    parent = _case(preview.case_id)
    draft = load_result(preview.case_id).draft
    assert draft is not None
    child_id = create_correction_email(
        preview.case_id,
        actor="HUMAN:test",
        draft=replace(draft, subject="Thư đính chính synthetic"),
    )
    _restart()
    assert _case(preview.case_id) == parent
    assert _case(child_id)["parent_case_id"] == preview.case_id
    assert _case(child_id)["status"] == CaseStatus.PENDING_APPROVAL
    assert _actions(preview.case_id).count("CORRECTION_CREATED") == 1
    assert not _actions(child_id)
    child = next(p for p in page["_preview_drafts"]() if p.case_id == child_id)
    page["_approve_send"](child)
    assert _case(child_id)["status"] == CaseStatus.SENT
    assert _case(preview.case_id) == parent
    assert _actions(child_id).count("HUMAN_APPROVED_SEND") == 1


@pytest.mark.parametrize("operation", ["edit", "return", "approve"])
def test_terminal_sent_rejects_stale_review_operations(approval_case, operation) -> None:
    page, preview = approval_case
    page["_approve_send"](preview)
    before = _case(preview.case_id)
    actions = _actions(preview.case_id)
    draft = dict(db.fetch_one("SELECT * FROM drafts WHERE draft_id = ?", (preview.draft_id,)))
    with pytest.raises(ValueError):
        if operation == "edit":
            page["_save_draft"](preview, preview.subject + " sửa", preview.body)
        elif operation == "return":
            page["_return_to_queue"](preview)
        else:
            page["_approve_send"](preview)
    assert _case(preview.case_id) == before
    assert _actions(preview.case_id) == actions
    assert (
        dict(db.fetch_one("SELECT * FROM drafts WHERE draft_id = ?", (preview.draft_id,))) == draft
    )


@pytest.mark.parametrize("status", [CaseStatus.PROCESSING, CaseStatus.HUMAN_DECIDED])
def test_expired_worker_lease_recovered_in_new_process(runtime, status) -> None:
    case_id = submit_case(_email())
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (status, case_id))
    db.execute(
        "UPDATE case_jobs SET state = 'running', lease_until = '2020-01-01T00:00:00Z' WHERE case_id = ?",
        (case_id,),
    )
    if status is CaseStatus.HUMAN_DECIDED:
        db.execute(
            "INSERT INTO human_decisions(id, case_id, actor, choice, reason, decided_at) "
            "VALUES ('restart-human', ?, 'HUMAN:test', 'Yêu cầu bổ sung', 'Cần bản chụp.', ?)",
            (case_id, db.now_iso()),
        )
    _restart()
    expected = CaseStatus.ERROR if status is CaseStatus.PROCESSING else CaseStatus.HUMAN_DECIDED
    assert _case(case_id)["status"] == expected
    assert (
        db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))["state"]
        == "failed"
    )
    assert _actions(case_id).count("CASE_ERROR") == 1
    assert "SEND_DISPATCHED" not in _actions(case_id)
    if status is CaseStatus.HUMAN_DECIDED:
        human = db.fetch_one("SELECT * FROM human_decisions WHERE case_id = ?", (case_id,))
        assert (human["choice"], human["reason"]) == ("Yêu cầu bổ sung", "Cần bản chụp.")
    else:
        decision = db.fetch_one("SELECT * FROM decisions WHERE case_id = ?", (case_id,))
        assert decision["decision"] == Decision.ERROR and decision["rule_id"] == "TECHNICAL_ERROR"


@pytest.mark.parametrize("failure", ["extract_timeout", "extract_schema", "guard_exception"])
def test_technical_error_state_audit_and_display_are_consistent(
    runtime, monkeypatch, failure, record_property
) -> None:
    if failure == "guard_exception":

        def fail_guard(**kwargs: object) -> None:
            raise TimeoutError("synthetic guard timeout")

        monkeypatch.setattr("core.pipeline.guard_groundedness", fail_guard)
    else:
        response = (
            LLMResult(False, {}, "synthetic timeout", 0, "test", "test")
            if failure == "extract_timeout"
            else LLMResult(True, {"language": "invalid"}, None, 0, "test", "test")
        )
        monkeypatch.setattr(
            "core.extract.call_json",
            lambda *a, **k: response,
        )
    result = process_case(_email())
    assert result.status is CaseStatus.ERROR and result.decision.decision is Decision.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR"
    assert result.decision.escalation_type is None and result.card is None
    assert _case(result.case_id)["status"] == CaseStatus.ERROR
    decision = db.fetch_one(
        "SELECT * FROM decisions WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (result.case_id,)
    )
    assert decision["decision"] == Decision.ERROR and decision["escalation_type"] is None
    actions = _actions(result.case_id)
    assert not {
        "CASE_QUEUED",
        "CASE_RESOLVED",
        "HUMAN_APPROVED_SEND",
        "HUMAN_DECISION",
        "SEND_SCHEDULED",
        "SEND_DISPATCHED",
    }.intersection(actions)
    assert not dispatch_due(result.case_id, now=datetime.now(timezone.utc) + timedelta(minutes=2))
    restored = load_result(result.case_id)
    assert restored is not None and restored.status is CaseStatus.ERROR
    assert (
        status_label(restored.status)
        == decision_label(restored.decision.decision)
        == "Chưa xử lý được"
    )
    record_property(
        "error_classification",
        json.dumps(
            {
                "status": _case(result.case_id)["status"],
                "decision": decision["decision"],
                "rule": decision["rule_id"],
                "display": status_label(restored.status),
                "audit": [
                    dict(row)
                    for row in db.fetch_all(
                        "SELECT actor, action, rule_id, reason FROM audit_events "
                        "WHERE case_id = ? AND action = 'CASE_ERROR' ORDER BY rowid",
                        (result.case_id,),
                    )
                ],
            },
            ensure_ascii=False,
        ),
    )
    error_events = db.fetch_all(
        "SELECT rule_id, reason FROM audit_events "
        "WHERE case_id = ? AND action = 'CASE_ERROR' ORDER BY rowid",
        (result.case_id,),
    )
    diagnostic_events = [event for event in error_events if event["rule_id"] is None]
    terminal_events = [event for event in error_events if event["rule_id"] == "TECHNICAL_ERROR"]
    assert len(diagnostic_events) == (1 if failure.startswith("extract_") else 0)
    assert len(terminal_events) == 1
    assert all(event["reason"] for event in diagnostic_events)
    assert terminal_events[0]["reason"]
    if failure.startswith("extract_"):
        assert (
            db.fetch_one(
                "SELECT COUNT(*) AS total FROM decisions "
                "WHERE decision IN ('AUTO_REPLY', 'ESCALATE')"
            )["total"]
            == 0
        )
        assert snapshot()["auto_rate"] == 0.0
    record_property("diagnostic_error_events", len(diagnostic_events))
    record_property("terminal_error_events", len(terminal_events))


@pytest.mark.parametrize("step", ["R2", "R11"])
def test_real_replay_missing_pack_fails_safe(
    runtime, monkeypatch, tmp_path, step, record_property
) -> None:
    # Thư mục rỗng riêng chỉ kiểm missing-pack; không dựng/sửa cassette của M6-T05.
    monkeypatch.setattr(llm, "CASSETTE_DIRECTORY", tmp_path / "empty-cassettes")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "none")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("LLM_CACHE", "0")
    misses = []
    original = llm._replay

    def observe_replay(prompt_hash: str, model: str) -> LLMResult:
        result = original(prompt_hash, model)
        misses.append((prompt_hash, result.error))
        return result

    monkeypatch.setattr(llm, "_replay", observe_replay)
    if step == "R2":
        monkeypatch.setattr("core.extract.call_json", llm.call_json)
        result = process_case(_email())
        case_id = result.case_id
        assert result.status is CaseStatus.ERROR and result.decision.rule_id == "TECHNICAL_ERROR"
        assert result.decision.escalation_type is None
    else:
        monkeypatch.setattr("core.resume.call_json", llm.call_json)
        case_id = submit_case(_email())
        db.execute(
            "UPDATE cases SET status = ? WHERE case_id = ?", (CaseStatus.HUMAN_DECIDED, case_id)
        )
        db.execute(
            "INSERT INTO human_decisions(id, case_id, actor, choice, reason, decided_at) "
            "VALUES ('missing-r11', ?, 'HUMAN:test', 'Yêu cầu bổ sung', 'Cần bản chụp.', ?)",
            (case_id, db.now_iso()),
        )
        worker_tick()
        assert _case(case_id)["status"] == CaseStatus.HUMAN_DECIDED
        assert (
            db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))["state"]
            == "failed"
        )
        assert (
            db.fetch_one("SELECT choice FROM human_decisions WHERE case_id = ?", (case_id,))[
                "choice"
            ]
            == "Yêu cầu bổ sung"
        )
    assert len(misses) == 1 and "cassette" in misses[0][1]
    record_property("missing_prompt_hash", misses[0][0])
    record_property("missing_replay_step", step)
    assert not {"SEND_DISPATCHED", "HUMAN_APPROVED_SEND"}.intersection(_actions(case_id))
    assert not db.fetch_all("SELECT draft_id FROM drafts WHERE case_id = ?", (case_id,))
    record_property("actual_error_events", _actions(case_id).count("CASE_ERROR"))
    error_events = db.fetch_all(
        "SELECT rule_id, reason FROM audit_events "
        "WHERE case_id = ? AND action = 'CASE_ERROR' ORDER BY rowid",
        (case_id,),
    )
    if step == "R2":
        assert sum(event["rule_id"] is None for event in error_events) == 1
        assert sum(event["rule_id"] == "TECHNICAL_ERROR" for event in error_events) == 1
        assert all(event["reason"] for event in error_events)
    else:
        assert len(error_events) == 1
