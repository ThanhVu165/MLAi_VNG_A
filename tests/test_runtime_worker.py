"""Kiểm chứng đường thật qua SQLite; chỉ thay dịch vụ LLM ở biên để test offline."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.controls import override_decision, pause_automation, resume_automation
from core.dispatch import cancel_send, dispatch_due, escalate_from_pending
from core.pipeline import load_result, process_case
from core.resume import resume_case, validate_human_draft
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    Domain,
    EscalationType,
    RequestItem,
    PipelineResult,
    DraftReply,
)
from core.worker import queue_resume, retry_case, submit_case, worker_tick
from infra import db
from infra.llm import LLMResult, JsonObject


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "runtime.db")
    db.execute(
        """INSERT INTO sources(doc_id, title, status, effective_from, domains_json,
               applies_to_json, cohorts_json, content_hash, is_synthetic)
               VALUES ('rule', 'Quy định thử nghiệm', 'ACTIVE', '2020-01-01', ?, '[]', '[]', 'v1', 1)""",
        (json.dumps([Domain.GRADE_APPEAL]),),
    )
    db.execute(
        """INSERT INTO chunks(chunk_id, doc_id, article_no, clause_no, breadcrumb,
               text, domain, label) VALUES ('fee', 'rule', '1', '1', 'Điều 1 · Khoản 1',
               'Lệ phí phúc khảo là 150.000 đồng.', ?, 'human_only')""",
        (Domain.GRADE_APPEAL,),
    )
    seen: list[tuple[str, str]] = []

    def llm(prompt: str, **kwargs: object) -> LLMResult:
        data: JsonObject
        step = str(kwargs["step"])
        seen.append((step, prompt))
        if step == "R2_extract":
            data = {
                "language": "vi",
                "requests": [
                    asdict(
                        RequestItem(
                            Domain.GRADE_APPEAL,
                            "Lệ phí phúc khảo",
                            True,
                            False,
                            False,
                            False,
                            False,
                        )
                    )
                ],
                "critical_facts": {},
                "missing_critical_facts": [],
                "injection_suspected": False,
            }
        elif step == "R4_select":
            data = {"chunk_ids": ["fee"], "missing_facts": [], "unanswered_requests": []}
        elif step == "R7_generate":
            amount = re.search(r"Lệ phí phúc khảo là ([\d.]+) đồng", prompt)
            assert amount is not None
            data = {
                "subject": "Phản hồi về lệ phí",
                "body": f"Lệ phí phúc khảo là {amount.group(1)} đồng [fee].",
                "citations": ["fee"],
            }
        else:
            raise AssertionError(f"Lời gọi không dự kiến: {step}")
        return LLMResult(True, data, None, 0, "offline-boundary", "test")

    for module in ("extract", "retrieval", "generate"):
        monkeypatch.setattr(f"core.{module}.call_json", llm)
    return seen


def _email() -> CaseInput:
    return CaseInput(
        "student@example.test",
        "Hỏi lệ phí phúc khảo",
        "Em muốn biết lệ phí phúc khảo.",
        datetime.now(timezone.utc),
        "paste",
    )


def _loaded(case_id: str) -> PipelineResult:
    result = load_result(case_id)
    assert result is not None
    return result


def test_meaningful_short_email_reaches_llm_with_subject_and_round_trips(runtime) -> None:
    inp = _email()
    result = process_case(inp)
    assert result.status is CaseStatus.PENDING_SEND
    assert result.decision.rule_id == "P05"
    assert [step for step, _ in runtime] == ["R2_extract", "R4_select", "R7_generate"]
    assert all(inp.subject in prompt and inp.body in prompt for _, prompt in runtime)
    restored = load_result(result.case_id)
    assert restored is not None and restored == result
    assert process_case(inp, case_id=result.case_id) == result
    assert len(runtime) == 3
    count = db.fetch_one("SELECT COUNT(*) AS n FROM cases")
    assert count is not None and count["n"] == 1


def test_queue_survives_navigation_deduplicates_and_sends_once(runtime) -> None:
    inp = replace(_email(), channel="inbox", external_id="message-unique")
    case_id = submit_case(inp)
    assert submit_case(inp) == case_id
    assert load_result(case_id) is None
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.PENDING_SEND
    db.execute(
        "UPDATE cases SET send_deadline = ? WHERE case_id = ?",
        (db.to_utc_iso(datetime.now(timezone.utc) - timedelta(seconds=1)), case_id),
    )
    worker_tick()
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.SENT
    count = db.fetch_one(
        "SELECT COUNT(*) AS n FROM audit_events WHERE case_id = ? AND action = 'SEND_DISPATCHED'",
        (case_id,),
    )
    assert count is not None and count["n"] == 1


def test_retry_reuses_existing_child_even_after_it_has_been_processed(runtime) -> None:
    original = submit_case(_email())
    db.execute("UPDATE case_jobs SET state = 'failed' WHERE case_id = ?", (original,))
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (CaseStatus.ERROR, original))
    child = retry_case(original)
    assert retry_case(original) == child
    worker_tick()
    assert retry_case(original) == child
    children = db.fetch_all("SELECT case_id FROM cases WHERE parent_case_id = ?", (original,))
    assert [row["case_id"] for row in children] == [child]
    assert len(db.fetch_all("SELECT event_id FROM audit_events WHERE action = 'RERUN_CASE'")) == 1


def test_mixed_supported_and_unknown_requests_keep_partial_reply_without_sending(
    runtime, monkeypatch
) -> None:
    from core import extract

    original_llm = extract.call_json

    def llm(prompt: str, **kwargs: object) -> LLMResult:
        if kwargs["step"] == "R7_question":
            runtime.append(("R7_question", prompt))
            return LLMResult(
                True,
                {
                    "summary": "Sinh viên hỏi thêm về chỗ ở ký túc xá.",
                    "facts": ["Nhu cầu còn lại là tìm chỗ ở ký túc xá."],
                    "basis": [],
                    "question": "Với yêu cầu về chỗ ở ký túc xá, chuyên viên chuyển đến đơn vị phụ trách hay yêu cầu bổ sung thông tin?",
                    "options": ["Chuyển đơn vị phụ trách", "Yêu cầu bổ sung thông tin"],
                },
                None,
                0,
                "offline-boundary",
                "test",
            )
        result = original_llm(prompt, **kwargs)
        if kwargs["step"] == "R2_extract":
            requests = result.data["requests"]
            assert isinstance(requests, list)
            requests.append(
                asdict(RequestItem(Domain.UNKNOWN, "Chỗ ở ký túc xá", True, False, False, False, False))
            )
        return result

    for module in ("extract", "retrieval", "generate", "question_gen"):
        monkeypatch.setattr(f"core.{module}.call_json", llm)
    result = process_case(replace(_email(), body="Em hỏi lệ phí phúc khảo và chỗ ở ký túc xá."))
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.escalation_type is EscalationType.OUT_OF_POLICY
    assert result.decision.rule_id == "P02"
    assert result.decision.evidence_ids == ["fee"]
    assert result.card is not None and result.card.partial_draft is not None
    assert result.card.partial_draft.grounded
    assert "150.000" in result.card.partial_draft.body
    assert result.card.partial_draft.citations == ["fee"]
    assert len(runtime) == 4
    worker_tick()
    assert _loaded(result.case_id).status is CaseStatus.AWAITING_HUMAN
    assert not db.fetch_all("SELECT event_id FROM audit_events WHERE action = 'SEND_DISPATCHED'")


def test_pause_after_schedule_and_cancel_after_deadline_never_sends(runtime) -> None:
    case_id = submit_case(_email())
    worker_tick()
    pause_automation("ADMIN:test", "Kiểm tra trước khi gửi.")
    db.execute(
        "UPDATE cases SET send_deadline = ? WHERE case_id = ?",
        (db.to_utc_iso(datetime.now(timezone.utc) - timedelta(seconds=1)), case_id),
    )
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.PENDING_SEND
    cancel_send(case_id, "HUMAN:test", "Hủy thư đang tạm dừng.")
    resume_automation("ADMIN:test")
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.CANCELLED


def test_restart_marks_interrupted_job_error_and_retry_keeps_original(runtime) -> None:
    original = submit_case(_email())
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (CaseStatus.PROCESSING, original))
    db.execute(
        "UPDATE case_jobs SET state = 'running', lease_until = '2020-01-01T00:00:00Z' WHERE case_id = ?",
        (original,),
    )
    worker_tick()
    restored = _loaded(original)
    assert restored.status is CaseStatus.ERROR and restored.card is None
    rerun = retry_case(original)
    worker_tick()
    assert _loaded(rerun).status is CaseStatus.PENDING_SEND
    assert _loaded(original).status is CaseStatus.ERROR
    parent = db.fetch_one("SELECT parent_case_id FROM cases WHERE case_id = ?", (rerun,))
    assert parent is not None and parent["parent_case_id"] == original


def test_source_change_alters_answer_and_stops_previous_pending_send(runtime) -> None:
    first = process_case(_email())
    db.execute(
        "UPDATE chunks SET text = 'Lệ phí phúc khảo là 200.000 đồng.' WHERE chunk_id = 'fee'"
    )
    db.execute("UPDATE sources SET content_hash = 'v2' WHERE doc_id = 'rule'")
    second = process_case(_email())
    assert first.draft is not None and second.draft is not None
    assert "150.000" in first.draft.body and "200.000" in second.draft.body
    db.execute(
        "UPDATE cases SET send_deadline = '2020-01-01T00:00:00Z' WHERE case_id = ?",
        (first.case_id,),
    )
    worker_tick()
    restored = _loaded(first.case_id)
    assert restored.status is CaseStatus.NEEDS_RECHECK and restored.evidence is not None
    assert "150.000" in restored.evidence.chunks[0].text


def test_finalized_case_cannot_be_overridden_or_requeued(runtime) -> None:
    result = process_case(_email())
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (CaseStatus.SENT, result.case_id))
    with pytest.raises(ValueError):
        override_decision(result.case_id, Decision.ESCALATE, "ADMIN:test", "Yêu cầu thay đổi.")
    with pytest.raises(ValueError):
        retry_case(result.case_id)


def test_manual_stop_requires_reason_and_saves_specific_card_atomically(runtime, monkeypatch) -> None:
    result = process_case(_email())
    with pytest.raises(ValueError, match="lý do"):
        cancel_send(result.case_id, "HUMAN:test", " ")
    assert _loaded(result.case_id).status is CaseStatus.PENDING_SEND
    assert not db.fetch_all("SELECT event_id FROM audit_events WHERE action = 'CANCEL_SEND'")
    reason = "Kiểm tra địa chỉ nhận student@example.test trước khi gửi."
    escalate_from_pending(result.case_id, actor="HUMAN:test", reason=reason)
    stopped = _loaded(result.case_id)
    assert stopped.status is CaseStatus.AWAITING_HUMAN and stopped.card is not None
    assert stopped.decision.decision is Decision.ESCALATE
    assert stopped.decision.rule_id == "HUMAN_REVIEW_REQUESTED"
    assert stopped.card.basis and "[EMAIL]" in stopped.card.question
    assert "150.000" in stopped.card.basis[0][1]
    before = len(db.fetch_all("SELECT decision_id FROM decisions"))

    def audit_failure(**kwargs: object) -> str:
        raise RuntimeError("Không ghi được nhật ký.")

    monkeypatch.setattr("core.controls.log_event", audit_failure)
    with pytest.raises(RuntimeError, match="nhật ký"):
        override_decision(result.case_id, Decision.AUTO_REPLY, "ADMIN:test", "Đã kiểm tra.")
    assert _loaded(result.case_id).status is CaseStatus.AWAITING_HUMAN
    assert len(db.fetch_all("SELECT decision_id FROM decisions")) == before


def test_dispatch_keeps_pending_status_when_audit_cannot_be_saved(runtime, monkeypatch) -> None:
    result = process_case(_email())

    def audit_failure(**kwargs: object) -> str:
        raise RuntimeError("Không ghi được nhật ký gửi.")

    monkeypatch.setattr("core.dispatch.log_event", audit_failure)
    with pytest.raises(RuntimeError, match="nhật ký gửi"):
        dispatch_due(result.case_id, now=datetime.now(timezone.utc) + timedelta(seconds=61))
    assert _loaded(result.case_id).status is CaseStatus.PENDING_SEND
    assert not db.fetch_all("SELECT event_id FROM audit_events WHERE action = 'SEND_DISPATCHED'")


def test_resume_job_survives_failure_and_crash_without_losing_human_decision(runtime, monkeypatch) -> None:
    case_id = submit_case(_email())
    db.execute("UPDATE case_jobs SET state = 'done' WHERE case_id = ?", (case_id,))
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (CaseStatus.HUMAN_DECIDED, case_id))
    choice, reason = "Yêu cầu bổ sung", "Cần bản chụp nội dung đang hỏi."
    db.execute(
        "INSERT INTO human_decisions(id, case_id, actor, choice, reason, decided_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("resume-worker", case_id, "HUMAN:test", choice, reason, db.now_iso()),
    )
    queue_resume(case_id)
    queue_resume(case_id)
    assert len(db.fetch_all("SELECT case_id FROM case_jobs WHERE case_id = ?", (case_id,))) == 1
    db.execute(
        "UPDATE case_jobs SET state = 'running', lease_until = '2020-01-01T00:00:00Z' WHERE case_id = ?",
        (case_id,),
    )
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.HUMAN_DECIDED
    failed = db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))
    assert failed is not None and failed["state"] == "failed"
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(False, {}, "Timeout", 0, "test", "test"),
    )
    queue_resume(case_id)
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.HUMAN_DECIDED
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(
            True, {"subject": "Bổ sung thông tin", "body": f"{choice}. {reason}", "citations": []},
            None, 0, "test", "test",
        ),
    )
    queue_resume(case_id)
    worker_tick()
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.PENDING_APPROVAL
    assert len(db.fetch_all("SELECT draft_id FROM drafts WHERE case_id = ?", (case_id,))) == 1
    assert len(db.fetch_all("SELECT id FROM human_decisions WHERE case_id = ?", (case_id,))) == 1


def test_human_decision_without_policy_source_is_editable_and_retryable(
    runtime, monkeypatch
) -> None:
    case_id = submit_case(_email())
    db.execute("UPDATE case_jobs SET state = 'done' WHERE case_id = ?", (case_id,))
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (CaseStatus.HUMAN_DECIDED, case_id))
    choice = "Yêu cầu bổ sung"
    reason = "Cần bản chụp rõ nội dung đang hỏi, gửi đến support@example.test cho MSSV 12345678901."
    db.execute(
        "INSERT INTO human_decisions(id, case_id, actor, choice, reason, decided_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("human-test", case_id, "HUMAN:test", choice, reason, db.now_iso()),
    )
    monkeypatch.setattr(
        "core.resume.call_json",
        lambda *args, **kwargs: LLMResult(False, {}, "Timeout", 0, "test", "test"),
    )
    with pytest.raises(ValueError, match="Timeout"):
        resume_case(case_id, choice, reason, "HUMAN:test")
    assert _loaded(case_id).status is CaseStatus.HUMAN_DECIDED

    def respond(prompt: str, **kwargs: object) -> LLMResult:
        assert _email().subject in prompt and _email().body in prompt
        return LLMResult(
            True,
            {"subject": "Bổ sung thông tin", "body": f"{choice}. {reason}", "citations": []},
            None,
            0,
            "test",
            "test",
        )

    monkeypatch.setattr("core.resume.call_json", respond)
    draft = resume_case(case_id, choice, reason, "HUMAN:test")
    assert draft.grounded and not draft.citations
    assert validate_human_draft(case_id, draft).grounded
    stored = _loaded(case_id).draft
    assert stored is not None and "[EMAIL]" in stored.body and "[MSSV]" in stored.body
    assert validate_human_draft(case_id, stored).grounded
    invented = replace(draft, body=f"{draft.body} Vui lòng nộp lệ phí 500.000 đồng.")
    assert not validate_human_draft(case_id, invented).grounded
    changed = replace(draft, body="Yêu cầu đã được chấp thuận.")
    assert not validate_human_draft(case_id, changed).grounded


def test_grounding_accepts_normal_wording_but_rejects_substring_money(runtime) -> None:
    from core.ground_guard import guard_groundedness
    from corpus.api import get_chunk
    from core.types import EvidenceResult, EvidenceStatus

    chunk = get_chunk("fee")
    assert chunk is not None
    evidence = EvidenceResult(EvidenceStatus.OK, [chunk], [])
    draft = DraftReply("Lệ phí", "Lệ phí phúc khảo là 150000 đồng. [fee]", ["fee"], False, [])
    assert guard_groundedness(
        case_id="test-wording",
        actor="SYSTEM",
        corpus_version="test",
        draft=draft,
        evidence=evidence,
    ).draft.grounded
    unsupported = replace(draft, body="Lệ phí phúc khảo là 50 đồng [fee].")
    assert not guard_groundedness(
        case_id="test-money",
        actor="SYSTEM",
        corpus_version="test",
        draft=unsupported,
        evidence=evidence,
    ).draft.grounded


def test_ui_cancel_saved_email_survives_reload_without_duplicate(runtime) -> None:
    result = process_case(_email())
    page = AppTest.from_file(str(Path(__file__).parents[1] / "pages/1_Xu_ly_email.py"))
    page.query_params["case_id"] = result.case_id
    page.run()
    assert not page.exception
    assert page.button(key=f"cancel_send_{result.case_id}").disabled
    page.text_input(key=f"send_reason_{result.case_id}").set_value(
        "Kiểm tra lại trước khi gửi."
    ).run()
    page.button(key=f"cancel_send_{result.case_id}").click().run()
    assert not page.exception
    assert _loaded(result.case_id).status is CaseStatus.CANCELLED
    # Mô phỏng tải lại trình duyệt bằng phiên mới, không tái dùng cây widget fragment của AppTest.
    page = AppTest.from_file(str(Path(__file__).parents[1] / "pages/1_Xu_ly_email.py"))
    page.query_params["case_id"] = result.case_id
    page.run()
    assert not page.exception
    assert len(db.fetch_all("SELECT case_id FROM cases")) == 1
    assert len(db.fetch_all("SELECT event_id FROM audit_events WHERE action = 'CANCEL_SEND'")) == 1


def test_ui_requires_save_before_human_approval_and_sends_once(runtime) -> None:
    pause_automation("ADMIN:test", "Kiểm tra thao tác duyệt trên giao diện.")
    result = process_case(_email())
    assert result.status is CaseStatus.PENDING_APPROVAL
    draft = db.fetch_one("SELECT draft_id FROM drafts WHERE case_id = ?", (result.case_id,))
    assert draft is not None
    draft_id = draft["draft_id"]
    page = AppTest.from_file(str(Path(__file__).parents[1] / "pages/2_Hang_cho_duyet.py")).run()
    assert not page.exception
    assert not page.button(key=f"approve_{draft_id}").disabled
    body = page.text_area(key=f"body_{draft_id}")
    assert body.value is not None
    body.set_value(body.value.replace("150.000", "150000")).run()
    assert page.button(key=f"approve_{draft_id}").disabled
    assert _loaded(result.case_id).status is CaseStatus.PENDING_APPROVAL
    page.button(key=f"edit_{draft_id}").click().run()
    assert not page.exception
    stored = db.fetch_one("SELECT * FROM drafts WHERE draft_id = ?", (draft_id,))
    assert stored is not None
    assert not page.button(key=f"approve_{draft_id}").disabled, (
        stored["body"],
        stored["grounded"],
        stored["guard_failures_json"],
        [item.value for item in page.info],
        [item.value for item in page.error],
        page.text_area(key=f"body_{draft_id}").value,
    )
    # Cho AppTest hoàn tất lượt st.rerun từ thao tác lưu trước khi phát sự kiện duyệt mới.
    page.run()
    page.button(key=f"approve_{draft_id}").click().run()
    assert not page.exception
    assert not page.error, [item.value for item in page.error]
    assert _loaded(result.case_id).status is CaseStatus.SENT, (
        [item.value for item in page.info], page.text_area(key=f"body_{draft_id}").value,
        [(item.label, item.disabled, item.value) for item in page.button],
    )
    page = AppTest.from_file(str(Path(__file__).parents[1] / "pages/2_Hang_cho_duyet.py")).run()
    assert not page.exception
    assert not any(button.label == "Duyệt và gửi" for button in page.button)
    assert (
        len(db.fetch_all("SELECT event_id FROM audit_events WHERE action = 'HUMAN_APPROVED_SEND'"))
        == 1
    )


def test_restart_recovers_legacy_processing_case_without_job(runtime) -> None:
    case_id = submit_case(_email())
    db.execute("DELETE FROM case_jobs WHERE case_id = ?", (case_id,))
    db.execute(
        "UPDATE cases SET status = ?, created_at = '2020-01-01T00:00:00Z' WHERE case_id = ?",
        (CaseStatus.PROCESSING, case_id),
    )
    worker_tick()
    assert _loaded(case_id).status is CaseStatus.ERROR
    assert _loaded(case_id).decision.decision is Decision.ERROR
    worker_tick()
    assert len(db.fetch_all("SELECT decision_id FROM decisions WHERE case_id = ?", (case_id,))) == 1


def test_extraction_named_facts_keep_legacy_dict_compatible() -> None:
    from core.extract import _facts

    assert _facts([{"name": "cohort", "value": "K49"}]) == _facts({"cohort": "K49"})
    with pytest.raises(ValueError, match="mâu thuẫn"):
        _facts([{"name": "cohort", "value": "K49"}, {"name": "cohort", "value": "K48"}])
