"""Preserved UI trên backend dev: AppTest thật, SQLite tạm, không gọi mạng."""

from pathlib import Path
import sqlite3

import pytest
from streamlit.testing.v1 import AppTest

from core.pipeline import process_case
from core.types import CaseStatus
from infra import audit, db
from test_runtime_worker import _email, approval_case as _approval_case, runtime as _runtime

runtime = _runtime
approval_case = _approval_case
ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "pages/2_Hang_cho_duyet.py"


def _status(case_id):
    return db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))["status"]


def _events(case_id):
    return db.fetch_all(
        "SELECT * FROM audit_events WHERE case_id = ? AND action = 'HUMAN_APPROVED_SEND'",
        (case_id,),
    )


@pytest.mark.parametrize(
    "page",
    [
        "1_Xu_ly_email.py",
        "2_Hang_cho_duyet.py",
        "3_Quan_tri_quy_dinh.py",
        "4_Nhat_ky_kiem_toan.py",
        "5_Verify.py",
        "6_Do_luong.py",
    ],
)
def test_all_six_preserved_pages_render_real_data(runtime, page):
    result = process_case(_email())
    app = AppTest.from_file(str(ROOT / "pages" / page))
    if page == "4_Nhat_ky_kiem_toan.py":
        app.query_params["case_id"] = result.case_id
    app.run(timeout=20)
    assert not app.exception
    assert not app.error
    assert any("<h1" in item.value for item in app.markdown)


def test_navigation_preserves_all_six_pages(runtime, monkeypatch):
    monkeypatch.setattr("core.worker.start_worker", lambda: None)
    monkeypatch.setattr("corpus.seed.ensure_seeded", lambda: None)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=20)
    assert not app.exception
    for page in (
        "2_Hang_cho_duyet.py",
        "3_Quan_tri_quy_dinh.py",
        "4_Nhat_ky_kiem_toan.py",
        "5_Verify.py",
        "6_Do_luong.py",
    ):
        app.switch_page("pages/" + page).run(timeout=20)
        assert not app.exception


@pytest.mark.parametrize("field", ["recipient", "corpus", "body", "grounded"])
@pytest.mark.parametrize("after_first_click", [False, True])
def test_two_step_confirmation_keeps_original_preview_and_blocks_stale(
    approval_case, field, after_first_click
):
    _, preview = approval_case
    app = AppTest.from_file(str(QUEUE)).run()
    if after_first_click:
        app.button(key=f"approve_{preview.draft_id}").click().run()
    if field == "recipient":
        db.execute(
            "UPDATE cases SET sender = 'changed@example.test' WHERE case_id = ?", (preview.case_id,)
        )
    elif field == "corpus":
        db.execute("UPDATE sources SET content_hash = 'changed-corpus' WHERE doc_id = 'rule'")
    elif field == "body":
        db.execute(
            "UPDATE drafts SET body = 'Thay đổi sau khi xem trước.' WHERE draft_id = ?",
            (preview.draft_id,),
        )
    else:
        db.execute("UPDATE drafts SET grounded = 0 WHERE draft_id = ?", (preview.draft_id,))
    app.run()
    assert not app.exception
    key = f"{'confirm_send' if after_first_click else 'approve'}_{preview.draft_id}"
    assert app.button(key=key).disabled
    assert any("đã thay đổi" in item.value for item in app.warning)
    pinned = app.session_state[f"approval_preview_{preview.draft_id}"]
    assert pinned["recipient"] == preview.recipient
    assert pinned["corpus_version"] == preview.corpus_version
    assert pinned["body"] == preview.body
    assert _status(preview.case_id) == CaseStatus.PENDING_APPROVAL
    assert not _events(preview.case_id)


def test_explicit_refresh_requires_both_steps_and_sends_once(approval_case):
    _, preview = approval_case
    app = AppTest.from_file(str(QUEUE)).run()
    app.button(key=f"approve_{preview.draft_id}").click().run()
    db.execute(
        "UPDATE cases SET sender = 'changed@example.test' WHERE case_id = ?", (preview.case_id,)
    )
    app.run()
    app.button(key=f"refresh_preview_{preview.draft_id}").click().run()
    assert not app.exception
    assert not any(b.key == f"confirm_send_{preview.draft_id}" for b in app.button)
    assert (
        app.session_state[f"approval_preview_{preview.draft_id}"]["recipient"]
        == "changed@example.test"
    )
    app.button(key=f"approve_{preview.draft_id}").click().run()
    assert _status(preview.case_id) == CaseStatus.PENDING_APPROVAL
    app.button(key=f"confirm_send_{preview.draft_id}").click().run()
    assert not app.exception and not app.error
    assert _status(preview.case_id) == CaseStatus.SENT
    app.run()
    assert len(_events(preview.case_id)) == 1


def test_two_sessions_confirmation_does_not_send_twice(approval_case):
    _, preview = approval_case
    sessions = [AppTest.from_file(str(QUEUE)).run() for _ in range(2)]
    for app in sessions:
        app.button(key=f"approve_{preview.draft_id}").click().run()
        assert not app.exception
    sessions[0].button(key=f"confirm_send_{preview.draft_id}").click().run()
    sessions[1].button(key=f"confirm_send_{preview.draft_id}").click().run()
    assert all(not app.exception for app in sessions)
    assert _status(preview.case_id) == CaseStatus.SENT
    assert len(_events(preview.case_id)) == 1


def test_confirmation_audit_insert_failure_rolls_back_state(approval_case, monkeypatch):
    _, preview = approval_case
    app = AppTest.from_file(str(QUEUE)).run()
    app.button(key=f"approve_{preview.draft_id}").click().run()
    original = audit.log_event

    def fail(**kwargs):
        event_id = original(**kwargs)
        if kwargs["action"] == "HUMAN_APPROVED_SEND":
            raise sqlite3.OperationalError("injected approval audit failure")
        return event_id

    monkeypatch.setattr(audit, "log_event", fail)
    app.button(key=f"confirm_send_{preview.draft_id}").click().run()
    assert not app.exception
    assert app.error
    assert _status(preview.case_id) == CaseStatus.PENDING_APPROVAL
    assert not _events(preview.case_id)


def test_confirmation_query_parameter_cannot_skip_first_step(approval_case):
    _, preview = approval_case
    app = AppTest.from_file(str(QUEUE))
    app.query_params["confirm"] = preview.draft_id
    app.run()
    assert not app.exception
    assert not any(b.key == f"confirm_send_{preview.draft_id}" for b in app.button)
    assert _status(preview.case_id) == CaseStatus.PENDING_APPROVAL
