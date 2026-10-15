"""Regression quyền hạn và replay cho Restricted Public DEMO."""

from __future__ import annotations

import runpy
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, cast

import pytest
from streamlit.testing.v1 import AppTest

from core.controls import pause_automation
from core.dispatch import cancel_send, dispatch_due, schedule_auto_reply
from core.pipeline import process_case
from core.resume import resume_case
from core.types import CaseInput, CaseStatus, Decision
from core.worker import queue_resume, submit_case, worker_tick
from corpus.intake import ingest_text
from corpus.lifecycle import reject_source
from corpus.seed import ensure_seeded
from corpus.store import SourceRecord
from infra import llm
from infra.db import execute, fetch_one, get_connection
from infra.demo_access import (
    DemoAccessDenied,
    app_mode,
    canonical_demo_inputs,
    case_is_owned,
    validate_runtime_mode,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def restricted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("OPENAI_API_KEY", "")


def _snapshot() -> dict[str, int]:
    names = (
        "cases",
        "case_jobs",
        "human_decisions",
        "sources",
        "chunks",
        "corpus_versions",
        "audit_events",
        "settings",
    )
    with get_connection() as connection:
        return {
            name: int(connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
            for name in names
        }


def _new_input(body: str = "Cho em hỏi một nội dung hoàn toàn mới?") -> CaseInput:
    return CaseInput(
        "guest@example.invalid",
        "Câu hỏi mới",
        body,
        datetime.now(timezone.utc),
        "paste",
    )


def test_mode_defaults_closed_and_rejects_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_MODE", raising=False)
    assert app_mode() == "restricted_demo"
    monkeypatch.setenv("APP_MODE", "public-admin")
    with pytest.raises(RuntimeError, match="APP_MODE"):
        app_mode()


def test_restricted_runtime_only_accepts_replay(
    restricted: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    validate_runtime_mode()
    monkeypatch.setenv("LLM_MODE", "live")
    with pytest.raises(RuntimeError, match="LLM_MODE=replay"):
        validate_runtime_mode()


@pytest.mark.parametrize("actor", ["ADMIN:fake", "HUMAN:fake", "SYSTEM"])
def test_fake_actor_cannot_mutate_admin_or_dispatch(restricted: None, actor: str) -> None:
    before = _snapshot()
    with pytest.raises(DemoAccessDenied):
        pause_automation(actor, "Thử giả quyền")
    with pytest.raises(DemoAccessDenied):
        cancel_send("case-khong-ton-tai", actor, "Thử giả quyền")
    with pytest.raises(DemoAccessDenied):
        dispatch_due("case-khong-ton-tai", actor=actor)
    with pytest.raises(DemoAccessDenied):
        worker_tick()
    assert _snapshot() == before


@pytest.mark.parametrize("actor", ["ADMIN:fake", "HUMAN:fake", "SYSTEM", "guest"])
def test_direct_schedule_spoof_is_denied_without_side_effect(restricted: None, actor: str) -> None:
    ensure_seeded()
    sample = canonical_demo_inputs()[0]
    result = process_case(
        CaseInput(
            sample.sender,
            sample.subject,
            sample.body,
            datetime.fromisoformat(sample.received_at),
            sample.channel,
        )
    )
    execute(
        "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ?",
        (CaseStatus.PROCESSING, result.case_id),
    )
    execute(
        "DELETE FROM audit_events WHERE case_id = ? AND action = 'SEND_SCHEDULED'",
        (result.case_id,),
    )
    before_case = dict(
        fetch_one("SELECT status, send_deadline FROM cases WHERE case_id = ?", (result.case_id,))
    )
    before_events = fetch_one(
        "SELECT COUNT(*) AS count FROM audit_events WHERE case_id = ? AND action = 'SEND_SCHEDULED'",
        (result.case_id,),
    )["count"]

    with pytest.raises(DemoAccessDenied, match="pipeline nội bộ"):
        schedule_auto_reply(result.case_id, decision=result.decision, actor=actor)

    after_case = dict(
        fetch_one("SELECT status, send_deadline FROM cases WHERE case_id = ?", (result.case_id,))
    )
    after_events = fetch_one(
        "SELECT COUNT(*) AS count FROM audit_events WHERE case_id = ? AND action = 'SEND_SCHEDULED'",
        (result.case_id,),
    )["count"]
    assert after_case == before_case == {"status": CaseStatus.PROCESSING, "send_deadline": None}
    assert after_events == before_events == 0


def test_direct_human_resume_is_denied_before_side_effect(restricted: None) -> None:
    before = _snapshot()
    with pytest.raises(DemoAccessDenied):
        queue_resume("case-khong-ton-tai")
    with pytest.raises(DemoAccessDenied):
        resume_case("case-khong-ton-tai", "Chấp thuận", "Giả quyền", "HUMAN:fake")
    assert _snapshot() == before


def test_corpus_ingest_and_lifecycle_are_denied_before_side_effect(restricted: None) -> None:
    before = _snapshot()
    with pytest.raises(DemoAccessDenied):
        ingest_text("Nội dung giả", actor="ADMIN:fake")
    with pytest.raises(DemoAccessDenied):
        reject_source(SourceRecord("source-khong-ton-tai"), actor="ADMIN:fake", reason="Giả")
    assert _snapshot() == before


def test_rejected_and_oversized_input_has_no_persistence(restricted: None) -> None:
    before = _snapshot()
    for inp in (_new_input(), _new_input("x" * 5_001)):
        with pytest.raises((DemoAccessDenied, ValueError)):
            submit_case(inp, actor="SYSTEM")
        assert _snapshot() == before


def test_direct_pipeline_replay_miss_is_technical_error_without_persistence(
    restricted: None,
) -> None:
    before = _snapshot()
    result = process_case(_new_input(), actor="ADMIN:fake")
    assert result.decision.decision is Decision.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR"
    assert _snapshot() == before


def test_query_or_session_value_does_not_grant_cross_session_access(restricted: None) -> None:
    assert case_is_owned("case-a", ["case-a"])
    assert not case_is_owned("case-b", ["case-a"])
    assert not case_is_owned("case-a", "case-a")


def test_live_and_record_never_reach_provider(
    restricted: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    def forbidden(*args: object, **kwargs: object) -> None:
        nonlocal called
        called = True
        raise AssertionError("provider không được gọi")

    monkeypatch.setattr(llm, "_call_live", forbidden)
    for mode in ("live", "record"):
        monkeypatch.setenv("LLM_MODE", mode)
        result = llm._run_mode("prompt", {}, "0" * 64, "gpt-6-luna", 1, 0)
        assert not result.ok
    assert not called


def test_restricted_ui_keeps_free_form_but_rejects_before_persistence(restricted: None) -> None:
    ensure_seeded()
    before = _snapshot()
    app = AppTest.from_file(str(ROOT / "pages" / "1_Xu_ly_email.py")).run(timeout=20)
    app.text_input(key="paste_sender").set_value("guest@example.invalid")
    app.text_input(key="paste_subject").set_value("Câu hỏi mới")
    app.text_area(key="paste_body").set_value("Cho em hỏi một nội dung chưa có cassette?")
    next(button for button in app.button if button.label == "Xử lý email").click().run(timeout=20)
    assert not app.exception
    assert any("chưa được bật" in item.value for item in app.error)
    assert not any(button.key == "process_inbox" for button in app.button)
    assert _snapshot() == before


def test_restricted_human_and_admin_pages_are_read_only(restricted: None) -> None:
    ensure_seeded()
    queue = AppTest.from_file(str(ROOT / "pages" / "2_Hang_cho_duyet.py")).run(timeout=20)
    corpus = AppTest.from_file(str(ROOT / "pages" / "3_Quan_tri_quy_dinh.py")).run(timeout=20)
    assert not queue.exception and not corpus.exception
    assert not queue.button
    assert not any(item.key == "source-reviewer" for item in corpus.text_input)
    assert any("đặc quyền" in item.value for item in queue.info)
    assert any("khóa phía máy chủ" in item.value for item in corpus.info)


def test_direct_human_page_sql_helpers_are_denied(restricted: None) -> None:
    before = _snapshot()
    namespace = runpy.run_path(str(ROOT / "pages" / "2_Hang_cho_duyet.py"))
    open_decision = cast(Callable[[str], object], namespace["_open_decision"])
    approve_send = cast(Callable[[object], None], namespace["_approve_send"])

    with pytest.raises(DemoAccessDenied):
        open_decision("case-khong-ton-tai")
    with pytest.raises(DemoAccessDenied):
        approve_send(object())
    assert _snapshot() == before


def test_query_parameter_cannot_open_another_session_case(restricted: None) -> None:
    ensure_seeded()
    sample = canonical_demo_inputs()[0]
    result = process_case(
        CaseInput(
            sample.sender,
            sample.subject,
            sample.body,
            datetime.fromisoformat(sample.received_at),
            sample.channel,
        )
    )

    email_page = AppTest.from_file(str(ROOT / "pages" / "1_Xu_ly_email.py"))
    email_page.query_params["case_id"] = result.case_id
    email_page.run(timeout=20)
    audit_page = AppTest.from_file(str(ROOT / "pages" / "4_Nhat_ky_kiem_toan.py"))
    audit_page.query_params["case_id"] = result.case_id
    audit_page.run(timeout=20)

    assert not email_page.exception and "case_id" not in email_page.query_params
    assert not audit_page.exception
    assert any("không có quyền" in item.value for item in audit_page.warning)


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, Decision.AUTO_REPLY),
        (1, Decision.ESCALATE),
        (2, Decision.ESCALATE),
    ],
)
def test_canonical_demo_sample_hits_replay_and_uses_server_actor(
    restricted: None, index: int, expected: Decision
) -> None:
    ensure_seeded()
    sample = canonical_demo_inputs()[index]
    inp = CaseInput(
        sample.sender,
        sample.subject,
        sample.body,
        datetime.fromisoformat(sample.received_at),
        "paste",
    )
    result = process_case(inp, actor="ADMIN:fake")
    assert result.decision.decision is expected
    assert result.decision.rule_id != "TECHNICAL_ERROR"
    actor = fetch_one(
        "SELECT actor FROM audit_events WHERE case_id = ? AND action = 'CASE_RECEIVED'",
        (result.case_id,),
    )
    assert actor is not None and actor["actor"] == "SYSTEM"
    if expected is Decision.AUTO_REPLY:
        scheduled = fetch_one(
            "SELECT status, send_deadline FROM cases WHERE case_id = ?", (result.case_id,)
        )
        event = fetch_one(
            "SELECT actor FROM audit_events WHERE case_id = ? AND action = 'SEND_SCHEDULED'",
            (result.case_id,),
        )
        assert scheduled is not None and scheduled["status"] == CaseStatus.PENDING_SEND
        assert scheduled["send_deadline"]
        assert event is not None and event["actor"] == "SYSTEM"


def test_verify4_canonical_payloads_run_in_restricted_mode(restricted: None) -> None:
    from pathlib import Path

    from verify.harness import run_cases

    results = run_cases(Path("verify/cases_verify4.json"), run_name="restricted-demo-test")

    assert len(results) == 4
    assert all(result.passed for result in results)
