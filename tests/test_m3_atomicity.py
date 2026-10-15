"""SQLite failure injection cho control/correction, hoàn toàn offline."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import sqlite3
from threading import Event

import pytest

from core import controls, dispatch
from core.types import CaseStatus, DraftReply
from infra import db


@pytest.fixture
def database(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "atomicity.db")
    db.initialize_database()


def _snapshot():
    return {
        table: [tuple(row) for row in db.fetch_all(f"SELECT * FROM {table} ORDER BY rowid")]
        for table in ("settings", "cases", "drafts", "audit_events")
    }


def _inject(monkeypatch, module, stage, timing):
    """Lỗi trước SQL hoặc sau SQL thật để phát hiện các commit rời rạc."""
    original_execute = module.execute
    original_audit = module.log_event

    def fail(call, *args, **kwargs):
        if timing == "before":
            raise sqlite3.OperationalError(f"injected {stage} before")
        result = call(*args, **kwargs)
        raise sqlite3.OperationalError(f"injected {stage} after {type(result).__name__}")

    def execute(statement, *args, **kwargs):
        target = {
            "setting": "INSERT INTO settings",
            "case": "INSERT INTO cases",
            "draft": "INSERT INTO drafts",
        }.get(stage)
        if target and target in statement:
            return fail(original_execute, statement, *args, **kwargs)
        return original_execute(statement, *args, **kwargs)

    def audit(**kwargs):
        if stage == "audit":
            return fail(original_audit, **kwargs)
        return original_audit(**kwargs)

    monkeypatch.setattr(module, "execute", execute)
    monkeypatch.setattr(module, "log_event", audit)


@pytest.mark.parametrize("operation", ["pause", "resume"])
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("stage", ["setting", "audit"])
@pytest.mark.parametrize("timing", ["before", "after"])
def test_control_failure_rolls_back_every_write(
    database, monkeypatch, operation, existing, stage, timing
):
    if existing:
        db.execute(
            "INSERT INTO settings(key, value, updated_at, actor) VALUES (?, ?, ?, ?)",
            (
                "automation_paused",
                "0" if operation == "pause" else "1",
                "2026-01-01T00:00:00Z",
                "ADMIN:previous",
            ),
        )
    before = _snapshot()
    _inject(monkeypatch, controls, stage, timing)
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        if operation == "pause":
            controls.pause_automation("ADMIN:test", "Tạm dừng để kiểm tra an toàn.")
        else:
            controls.resume_automation("ADMIN:test")
    assert _snapshot() == before


@pytest.mark.parametrize("actor", ["SYSTEM", "HUMAN:test", "ADMIN:", "ADMIN: "])
def test_controls_still_require_admin(database, actor):
    before = _snapshot()
    with pytest.raises(ValueError, match="ADMIN"):
        controls.pause_automation(actor, "Lý do hợp lệ.")
    with pytest.raises(ValueError, match="ADMIN"):
        controls.resume_automation(actor)
    assert _snapshot() == before


def test_controls_success_and_reason_requirement(database):
    with pytest.raises(ValueError, match="bắt buộc"):
        controls.pause_automation("ADMIN:test", "  ")
    assert _snapshot()["settings"] == _snapshot()["audit_events"] == []
    controls.pause_automation("ADMIN:test", "Tạm dừng để kiểm tra.")
    assert controls.is_automation_paused()
    controls.resume_automation("ADMIN:test")
    assert not controls.is_automation_paused()
    assert [
        (r["action"], r["actor"])
        for r in db.fetch_all("SELECT action, actor FROM audit_events ORDER BY rowid")
    ] == [("PAUSE_AUTOMATION", "ADMIN:test"), ("RESUME_AUTOMATION", "ADMIN:test")]


def _parent(status=CaseStatus.SENT):
    db.execute(
        """INSERT INTO cases(case_id, trace_id, channel, sender, subject, body_raw,
           received_at, created_at, status, corpus_version) VALUES
           ('parent', 'trace', 'paste', 'synthetic@example.test', 'Thư gốc', 'Nội dung gốc',
            '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', ?, 'original-corpus')""",
        (status,),
    )
    db.execute(
        "INSERT INTO audit_events(event_id, case_id, ts, actor, action, reason) "
        "VALUES ('saved-event', 'parent', ?, 'SYSTEM', 'SEND_DISPATCHED', 'Đã gửi mô phỏng.')",
        (db.now_iso(),),
    )


def _draft():
    return DraftReply(
        "Đính chính",
        "Liên hệ synthetic@example.test, MSSV 12345678901.",
        ["source-test"],
        False,
        ["needs_review"],
    )


@pytest.mark.parametrize("stage", ["case", "draft", "audit"])
@pytest.mark.parametrize("timing", ["before", "after"])
def test_correction_failure_preserves_parent_and_leaves_no_orphans(
    database, monkeypatch, stage, timing
):
    _parent()
    before = _snapshot()
    _inject(monkeypatch, dispatch, stage, timing)
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        dispatch.create_correction_email("parent", actor="HUMAN:test", draft=_draft())
    assert _snapshot() == before


def test_correction_success_preserves_lineage_masking_and_never_auto_sends(database):
    _parent()
    before_parent = dict(db.fetch_one("SELECT * FROM cases WHERE case_id = 'parent'"))
    child_id = dispatch.create_correction_email("parent", actor="HUMAN:test", draft=_draft())
    child = db.fetch_one("SELECT * FROM cases WHERE case_id = ?", (child_id,))
    draft = db.fetch_one("SELECT * FROM drafts WHERE case_id = ?", (child_id,))
    event = db.fetch_one("SELECT * FROM audit_events WHERE action = 'CORRECTION_CREATED'")
    assert dict(db.fetch_one("SELECT * FROM cases WHERE case_id = 'parent'")) == before_parent
    assert child["parent_case_id"] == event["case_id"] == "parent"
    assert event["output_ref"] == child_id
    assert child["corpus_version"] == event["corpus_version"] == "original-corpus"
    assert child["status"] == CaseStatus.PENDING_APPROVAL and child["send_deadline"] is None
    assert child["body_raw"] == _draft().body
    assert child["body_clean"] == child["body_masked"] == draft["body"]
    assert "synthetic@example.test" not in draft["body"] and "12345678901" not in draft["body"]
    assert draft["kind"] == "correction" and not draft["grounded"]
    assert json.loads(draft["citations_json"]) == _draft().citations
    assert json.loads(draft["guard_failures_json"]) == _draft().guard_failures
    assert not dispatch.dispatch_due(child_id)
    assert len(db.fetch_all("SELECT * FROM audit_events")) == 2


@pytest.mark.parametrize(
    "status",
    [
        CaseStatus.PENDING_SEND,
        CaseStatus.PENDING_APPROVAL,
        CaseStatus.CANCELLED,
        CaseStatus.AWAITING_HUMAN,
    ],
)
def test_correction_rejects_non_sent_parent_without_writes(database, status):
    _parent(status)
    before = _snapshot()
    with pytest.raises(ValueError, match="SENT"):
        dispatch.create_correction_email("parent", actor="HUMAN:test", draft=_draft())
    assert _snapshot() == before


def test_correction_checks_parent_after_obtaining_write_lock(database, monkeypatch):
    _parent()
    started, release = Event(), Event()
    original_connection, original_case = db.get_connection, dispatch._case

    def connection(*args, **kwargs):
        result = original_connection(*args, **kwargs)
        result.set_trace_callback(lambda sql: started.set() if sql == "BEGIN IMMEDIATE" else None)
        return result

    def case(case_id):
        result = original_case(case_id)
        started.set()
        assert release.wait(5), "writer was not released"
        return result

    # Writer thay trạng thái trước khi correction lấy khóa; WAL reader cũ vẫn thấy SENT.
    with closing(original_connection()) as writer, ThreadPoolExecutor(max_workers=1) as pool:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE cases SET status = 'PENDING_APPROVAL' WHERE case_id = 'parent'")
        monkeypatch.setattr(db, "get_connection", connection)
        monkeypatch.setattr(dispatch, "_case", case)
        future = pool.submit(
            dispatch.create_correction_email, "parent", actor="HUMAN:test", draft=_draft()
        )
        try:
            assert started.wait(5), "correction did not reach read/lock"
        finally:
            writer.commit()
            release.set()
        with pytest.raises(ValueError, match="SENT"):
            future.result(timeout=5)
    assert len(db.fetch_all("SELECT * FROM cases")) == 1
    assert not db.fetch_all("SELECT * FROM drafts")
    assert len(db.fetch_all("SELECT * FROM audit_events")) == 1
