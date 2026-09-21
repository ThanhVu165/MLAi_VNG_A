"""Ghi và truy vấn nhật ký kiểm toán."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from uuid import uuid4

from infra.db import execute, fetch_all, now_iso

ACTIONS: frozenset[str] = frozenset(
    {
        "CASE_RECEIVED",
        "CASE_SANITIZED",
        "FACTS_EXTRACTED",
        "PREPOLICY_LOCKED",
        "EVIDENCE_RETRIEVED",
        "EVIDENCE_VALIDATED",
        "POLICY_DECIDED",
        "DRAFT_GENERATED",
        "GROUNDEDNESS_FAILED",
        "QUESTION_GENERATED",
        "QUESTION_GUARD_FAILED",
        "CASE_QUEUED",
        "CASE_RESUMED",
        "CASE_RESOLVED",
        "CASE_ERROR",
        "SEND_SCHEDULED",
        "SEND_DISPATCHED",
        "CANCEL_SEND",
        "CORRECTION_CREATED",
        "HUMAN_DECISION",
        "HUMAN_APPROVED_SEND",
        "HUMAN_REJECTED_DRAFT",
        "EXPLAIN_REQUESTED",
        "PAUSE_AUTOMATION",
        "RESUME_AUTOMATION",
        "OVERRIDE_DECISION",
        "RERUN_CASE",
        "SOURCE_UPLOADED",
        "SOURCE_METADATA_EDITED",
        "CHUNK_LABELLED",
        "ACTIVATE_SOURCE",
        "REJECT_SOURCE",
        "SUPERSEDE_SOURCE",
        "ROLLBACK_SOURCE",
        "FLAG_NEEDS_RECHECK",
        "SOURCE_RECHECKED",
        "VERIFY_RUN_STARTED",
        "VERIFY_RUN_FINISHED",
    }
)
REASON_REQUIRED_ACTIONS: frozenset[str] = frozenset(
    {"OVERRIDE_DECISION", "PAUSE_AUTOMATION", "HUMAN_DECISION", "CANCEL_SEND"}
)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    case_id: str | None
    ts: str
    actor: str
    action: str
    rule_id: str | None
    input_ref: str | None
    output_ref: str | None
    reason: str | None
    sources: list[str] | None
    corpus_version: str | None


def _event_from_row(row: sqlite3.Row) -> AuditEvent:
    values = dict(row)
    sources = values["sources_json"]
    return AuditEvent(
        event_id=values["event_id"],
        case_id=values["case_id"],
        ts=values["ts"],
        actor=values["actor"],
        action=values["action"],
        rule_id=values["rule_id"],
        input_ref=values["input_ref"],
        output_ref=values["output_ref"],
        reason=values["reason"],
        sources=json.loads(sources) if sources else None,
        corpus_version=values["corpus_version"],
    )


def log_event(
    *,
    case_id: str | None,
    actor: str,
    action: str,
    rule_id: str | None = None,
    input_ref: str | None = None,
    output_ref: str | None = None,
    reason: str | None = None,
    sources: list[str] | None = None,
    corpus_version: str | None = None,
    database_path: str | None = None,
) -> str:
    """Ghi một sự kiện hợp lệ và trả về mã sự kiện."""
    if action not in ACTIONS:
        raise ValueError(f"Action audit không hợp lệ: {action}")
    if action in REASON_REQUIRED_ACTIONS and not (reason and reason.strip()):
        raise ValueError(f"Action {action} bắt buộc có reason.")

    event_id = str(uuid4())
    execute(
        """
        INSERT INTO audit_events (
            event_id, case_id, ts, actor, action, rule_id, input_ref, output_ref,
            reason, sources_json, corpus_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            case_id,
            now_iso(),
            actor,
            action,
            rule_id,
            input_ref,
            output_ref,
            reason,
            json.dumps(sources, ensure_ascii=False) if sources is not None else None,
            corpus_version,
        ),
        database_path=database_path,
    )
    return event_id


def events_for_case(case_id: str, *, database_path: str | None = None) -> list[AuditEvent]:
    """Trả về chuỗi event của một case theo thời gian tăng dần."""
    rows = fetch_all(
        "SELECT * FROM audit_events WHERE case_id = ? ORDER BY ts ASC, rowid ASC",
        (case_id,),
        database_path=database_path,
    )
    return [_event_from_row(row) for row in rows]


def recent_events(limit: int = 200, *, database_path: str | None = None) -> list[AuditEvent]:
    """Trả về các event mới nhất, tối đa theo limit."""
    if limit < 0:
        raise ValueError("limit phải không âm.")
    rows = fetch_all(
        "SELECT * FROM audit_events ORDER BY ts DESC, rowid DESC LIMIT ?",
        (limit,),
        database_path=database_path,
    )
    return [_event_from_row(row) for row in rows]
