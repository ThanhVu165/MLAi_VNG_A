"""Failure injection qua pipeline/SQLite thật, không gọi mạng."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from core import pipeline
from core.dispatch import dispatch_due
from core.types import CaseStatus, Decision, EscalationType
from infra import db
from core.worker import retry_case, worker_tick
from test_runtime_worker import _email, runtime as _runtime

runtime = _runtime


def _evidence(case_id):
    case = dict(db.fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,)))
    decisions = [
        dict(row)
        for row in db.fetch_all(
            "SELECT decision, rule_id FROM decisions WHERE case_id = ? ORDER BY rowid", (case_id,)
        )
    ]
    snapshot = db.fetch_one("SELECT payload_json FROM case_results WHERE case_id = ?", (case_id,))
    actions = [
        row["action"]
        for row in db.fetch_all(
            "SELECT action FROM audit_events WHERE case_id = ? ORDER BY rowid", (case_id,)
        )
    ]
    try:
        payload = json.loads(snapshot[0]) if snapshot else None
    except ValueError:
        payload = snapshot[0]
    return {
        "status": case["status"],
        "deadline": case["send_deadline"],
        "decisions": decisions,
        "snapshot": payload,
        "actions": actions,
    }


def _dispatch(case_id):
    return dispatch_due(case_id, now=datetime.now(timezone.utc) + timedelta(minutes=2))


def test_p04_routes_to_human_and_never_dispatches(runtime, monkeypatch):
    original = pipeline.generate_reply
    monkeypatch.setattr(
        pipeline,
        "generate_reply",
        lambda **kw: replace(original(**kw), body="Lệ phí là 999.000 đồng [fee]."),
    )
    result = pipeline.process_case(_email())
    before = _evidence(result.case_id)
    sent = _dispatch(result.case_id)
    print("P04 evidence:", before, "returned:", result.decision, "dispatch:", sent)
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.decision.decision is Decision.ESCALATE
    assert result.decision.escalation_type is EscalationType.FACT_UNRESOLVED
    assert result.decision.rule_id == "P04"
    assert result.card and result.card.question and len(result.card.options) >= 2
    assert before["decisions"][-1] == {"decision": "ESCALATE", "rule_id": "P04"}
    assert before["snapshot"]["decision"]["rule_id"] == "P04"
    assert "GROUNDEDNESS_FAILED" in before["actions"]
    assert "CASE_QUEUED" in before["actions"]
    assert "CASE_ERROR" not in before["actions"]
    assert "SEND_SCHEDULED" not in before["actions"]
    assert not sent


@pytest.mark.parametrize("failure", ["snapshot", "decision", "both", "snapshot_and_error"])
def test_persistence_failure_blocks_send_even_without_error_write(runtime, monkeypatch, failure):
    original = pipeline._save_decision

    def fail_decision(intake, decision):
        if failure in {"decision", "both"} or decision.decision is Decision.ERROR:
            raise sqlite3.OperationalError("injected decision failure")
        original(intake, decision)

    if failure != "decision":
        monkeypatch.setattr(
            pipeline,
            "save_result",
            lambda result: (_ for _ in ()).throw(
                sqlite3.OperationalError("injected snapshot failure")
            ),
        )
    if failure != "snapshot":
        monkeypatch.setattr(pipeline, "_save_decision", fail_decision)
    result = pipeline.process_case(_email())
    before = _evidence(result.case_id)
    sent = _dispatch(result.case_id)
    after = _evidence(result.case_id)
    print("Persistence evidence:", failure, before, "dispatch:", sent, "after:", after)
    assert result.decision.decision is Decision.ERROR
    assert not sent
    assert "SEND_DISPATCHED" not in after["actions"]
    assert "SEND_SCHEDULED" not in before["actions"]
    assert before["status"] != CaseStatus.PENDING_SEND
    assert before["deadline"] is None
    assert before["actions"][:2] == ["CASE_RECEIVED", "CASE_SANITIZED"]


def test_valid_finalization_retry_and_concurrent_dispatch(runtime):
    inp = _email()
    result = pipeline.process_case(inp)
    assert pipeline.process_case(inp, case_id=result.case_id) == result
    assert len(runtime) == 3
    with ThreadPoolExecutor(max_workers=2) as pool:
        sent = list(pool.map(_dispatch, [result.case_id] * 2))
    assert sorted(sent) == [False, True]
    evidence = _evidence(result.case_id)
    assert evidence["status"] == CaseStatus.SENT
    assert evidence["actions"].count("SEND_SCHEDULED") == 1
    assert evidence["actions"].count("SEND_DISPATCHED") == 1


@pytest.mark.parametrize(
    "damage",
    [
        "missing_snapshot",
        "bad_json",
        "null_draft",
        "stale_snapshot",
        "decision",
        "draft",
        "trace",
        "version",
        "missing_decision",
        "guard_failures",
    ],
)
def test_dispatch_rejects_incomplete_or_inconsistent_finalization(runtime, damage):
    result = pipeline.process_case(_email())
    case_id = result.case_id
    payload = _evidence(case_id)["snapshot"]
    if damage == "missing_snapshot":
        db.execute("DELETE FROM case_results WHERE case_id = ?", (case_id,))
    elif damage == "bad_json":
        db.execute("UPDATE case_results SET payload_json = '{' WHERE case_id = ?", (case_id,))
    elif damage == "stale_snapshot":
        db.execute(
            "UPDATE audit_events SET ts = ? WHERE case_id = ? AND action = 'CASE_SANITIZED'",
            (db.to_utc_iso(datetime.now(timezone.utc) + timedelta(seconds=1)), case_id),
        )
    elif damage == "decision":
        db.execute("UPDATE decisions SET decision = 'ERROR' WHERE case_id = ?", (case_id,))
    elif damage == "missing_decision":
        db.execute("DELETE FROM decisions WHERE case_id = ?", (case_id,))
    elif damage == "draft":
        db.execute("UPDATE drafts SET body = 'different' WHERE case_id = ?", (case_id,))
    elif damage == "guard_failures":
        db.execute(
            "UPDATE drafts SET guard_failures_json = '[\"number\"]' WHERE case_id = ?", (case_id,)
        )
    else:
        if damage == "null_draft":
            payload["draft"] = None
        elif damage == "trace":
            payload["trace_id"] = "stale-trace"
        else:
            payload["corpus_version"] = "stale-version"
        db.execute(
            "UPDATE case_results SET payload_json = ? WHERE case_id = ?",
            (json.dumps(payload), case_id),
        )
    assert not _dispatch(case_id)
    after = _evidence(case_id)
    assert after["status"] == CaseStatus.NEEDS_RECHECK
    assert after["actions"].count("FLAG_NEEDS_RECHECK") == 1
    assert "SEND_DISPATCHED" not in after["actions"]


def test_snapshot_partial_write_rolls_back_and_retry_uses_new_case(runtime, monkeypatch):
    original = pipeline.save_result
    with monkeypatch.context() as patched:

        def fail_after_write(result):
            original(result)
            raise sqlite3.OperationalError("injected after snapshot insert")

        patched.setattr(pipeline, "save_result", fail_after_write)
        result = pipeline.process_case(_email())
    before = _evidence(result.case_id)
    assert before["status"] == CaseStatus.PROCESSING
    assert before["snapshot"] is None
    assert "CASE_ERROR" not in before["actions"]
    assert "SEND_SCHEDULED" not in before["actions"]
    assert not _dispatch(result.case_id)
    # Mô phỏng hết lease của case bị gián đoạn, dùng recovery hiện hành.
    db.execute(
        "UPDATE cases SET created_at = '2020-01-01T00:00:00Z' WHERE case_id = ?", (result.case_id,)
    )
    worker_tick()
    recovered = _evidence(result.case_id)
    assert recovered["status"] == CaseStatus.ERROR
    retried = retry_case(result.case_id)
    assert retried != result.case_id
    worker_tick()
    assert _dispatch(retried)
    after = _evidence(result.case_id)
    assert after["actions"] == recovered["actions"] + ["RERUN_CASE"]
    assert {key: value for key, value in after.items() if key != "actions"} == {
        key: value for key, value in recovered.items() if key != "actions"
    }


def test_schedule_audit_failure_rolls_back_snapshot_and_deadline(runtime, monkeypatch):
    from core import dispatch

    original = dispatch.log_event

    def fail_schedule(**kwargs):
        original(**kwargs)
        if kwargs["action"] == "SEND_SCHEDULED":
            raise sqlite3.OperationalError("injected after schedule audit")

    monkeypatch.setattr(dispatch, "log_event", fail_schedule)
    result = pipeline.process_case(_email())
    evidence = _evidence(result.case_id)
    assert evidence["status"] == CaseStatus.ERROR
    assert evidence["deadline"] is None
    assert evidence["snapshot"]["decision"]["decision"] == "ERROR"
    assert evidence["decisions"][-1]["decision"] == "ERROR"
    assert evidence["actions"].count("CASE_ERROR") == 1
    assert "SEND_SCHEDULED" not in evidence["actions"]
    assert not _dispatch(result.case_id)


def test_real_guard_service_error_remains_technical_error(runtime, monkeypatch):
    def fail_guard(**kwargs):
        raise TimeoutError("injected guard service failure")

    monkeypatch.setattr(pipeline, "guard_groundedness", fail_guard)
    result = pipeline.process_case(_email())
    assert result.status is CaseStatus.ERROR
    assert result.decision.decision is Decision.ERROR
    assert result.decision.escalation_type is None
    assert result.card is None
    evidence = _evidence(result.case_id)
    assert "CASE_QUEUED" not in evidence["actions"]
    assert evidence["actions"].count("CASE_ERROR") == 1
    assert not _dispatch(result.case_id)


def test_old_auto_reply_and_snapshot_do_not_authorize_failed_new_attempt(runtime, monkeypatch):
    inp = _email()
    previous = pipeline.process_case(inp)
    before = _evidence(previous.case_id)
    # Mô phỏng dữ liệu legacy tái sử dụng case, vẫn giữ toàn bộ lịch sử đã lưu.
    db.execute(
        "UPDATE cases SET status = 'RECEIVED', send_deadline = NULL WHERE case_id = ?",
        (previous.case_id,),
    )

    def fail_decision(*args):
        raise sqlite3.OperationalError("injected all decision writes")

    monkeypatch.setattr(pipeline, "_save_decision", fail_decision)
    failed = pipeline.process_case(inp, case_id=previous.case_id)
    assert failed.decision.decision is Decision.ERROR
    assert not _dispatch(previous.case_id)
    after = _evidence(previous.case_id)
    assert after["status"] == CaseStatus.PROCESSING
    assert after["decisions"] == before["decisions"]
    assert after["snapshot"] == before["snapshot"]
    # Dispatcher cũng chặn nếu dữ liệu cũ còn PENDING_SEND sau một lần lỗi.
    db.execute(
        "UPDATE cases SET status = 'PENDING_SEND', send_deadline = ? WHERE case_id = ?",
        (db.now_iso(), previous.case_id),
    )
    assert not _dispatch(previous.case_id)
    assert _evidence(previous.case_id)["status"] == CaseStatus.NEEDS_RECHECK


def test_dispatch_racing_failed_finalization_cannot_send(runtime, monkeypatch):
    original = pipeline.save_result
    futures = []
    with ThreadPoolExecutor(max_workers=1) as pool:

        def fail_after_write(result):
            original(result)
            futures.append(pool.submit(_dispatch, result.case_id))
            raise sqlite3.OperationalError("injected failure with concurrent dispatcher")

        monkeypatch.setattr(pipeline, "save_result", fail_after_write)
        result = pipeline.process_case(_email())
    assert futures and not any(future.result() for future in futures)
    evidence = _evidence(result.case_id)
    assert evidence["snapshot"] is None
    assert evidence["deadline"] is None
    assert "SEND_SCHEDULED" not in evidence["actions"]
    assert "SEND_DISPATCHED" not in evidence["actions"]
