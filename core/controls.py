"""Các can thiệp quản trị vào lifecycle case."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlite3 import Row
from typing import Literal, cast
from uuid import uuid4

from core.dispatch import cancel_send
from core.pipeline import process_case
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    EscalationType,
    PipelineResult,
    PolicyDecision,
)
from infra.audit import log_event
from infra.db import execute, fetch_one, now_iso

AUTOMATION_PAUSED_KEY = "automation_paused"
PAUSED_VALUE = "1"
RUNNING_VALUE = "0"
__all__ = (
    "cancel_send",
    "is_automation_paused",
    "override_decision",
    "pause_automation",
    "rerun_case",
    "resume_automation",
)


def _require_admin(actor: str) -> None:
    if not actor.startswith("ADMIN:") or not actor.removeprefix("ADMIN:").strip():
        raise ValueError("Chỉ ADMIN:<user> được dùng thao tác này.")


def _set_automation(value: str, actor: str) -> None:
    execute(
        """
        INSERT INTO settings (key, value, updated_at, actor) VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at,
        actor = excluded.actor
        """,
        (AUTOMATION_PAUSED_KEY, value, now_iso(), actor),
    )


def is_automation_paused() -> bool:
    """Trả trạng thái dừng tự động hóa được lưu bền trong DB."""
    row = fetch_one("SELECT value FROM settings WHERE key = ?", (AUTOMATION_PAUSED_KEY,))
    return row is not None and row["value"] == PAUSED_VALUE


def pause_automation(actor: str, reason: str) -> None:
    """Dừng lịch gửi tự động, vẫn tiếp nhận case vào hàng chờ."""
    _require_admin(actor)
    if not reason.strip():
        raise ValueError("Lý do tạm dừng là bắt buộc.")
    _set_automation(PAUSED_VALUE, actor)
    log_event(case_id=None, actor=actor, action="PAUSE_AUTOMATION", reason=reason)


def resume_automation(actor: str) -> None:
    """Bật lại lịch gửi tự động cho các case mới."""
    _require_admin(actor)
    _set_automation(RUNNING_VALUE, actor)
    log_event(
        case_id=None, actor=actor, action="RESUME_AUTOMATION", reason="Đã bật lại tự động hóa."
    )


def _latest_decision(case_id: str) -> Row:
    row = fetch_one(
        "SELECT * FROM decisions WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
    )
    if row is None:
        raise ValueError(f"Case {case_id} chưa có quyết định.")
    return row


def _result(case: Row, decision: PolicyDecision) -> PipelineResult:
    now = datetime.now(timezone.utc)
    return PipelineResult(
        case["case_id"],
        case["trace_id"],
        CaseStatus(case["status"]),
        decision,
        None,
        None,
        None,
        None,
        case["corpus_version"],
        {},
        now,
        now,
    )


def override_decision(
    case_id: str, new_decision: Decision, actor: str, reason: str
) -> PipelineResult:
    """Thay AUTO_REPLY bằng ESCALATE hoặc ngược lại, với lý do bắt buộc."""
    _require_admin(actor)
    if not reason.strip():
        raise ValueError("Lý do ghi đè là bắt buộc.")
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if case is None:
        raise ValueError(f"Không tìm thấy case {case_id}.")
    previous = _latest_decision(case_id)
    if Decision(previous["decision"]) is new_decision:
        raise ValueError("Quyết định ghi đè phải khác quyết định hiện tại.")
    decision_id = str(uuid4())
    escalation_type = EscalationType.FACT_UNRESOLVED if new_decision is Decision.ESCALATE else None
    evidence_ids = json.loads(previous["evidence_ids_json"] or "[]")
    decision = PolicyDecision(
        new_decision,
        escalation_type,
        "ADMIN_OVERRIDE",
        reason,
        evidence_ids,
        case["corpus_version"],
    )
    execute(
        """
        INSERT INTO decisions (
            decision_id, case_id, decision, escalation_type, rule_id, reason, evidence_ids_json,
            corpus_version, is_override, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            decision_id,
            case_id,
            decision.decision,
            decision.escalation_type,
            decision.rule_id,
            reason,
            json.dumps(evidence_ids, ensure_ascii=False),
            decision.corpus_version,
            1,
            now_iso(),
        ),
    )
    execute(
        "UPDATE decisions SET superseded_by = ? WHERE decision_id = ?",
        (decision_id, previous["decision_id"]),
    )
    status = (
        CaseStatus.AWAITING_HUMAN
        if new_decision is Decision.ESCALATE
        else CaseStatus.PENDING_APPROVAL
    )
    execute(
        "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ?", (status, case_id)
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="OVERRIDE_DECISION",
        rule_id=decision.rule_id,
        reason=reason,
        sources=evidence_ids,
        corpus_version=decision.corpus_version,
    )
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if case is None:
        raise ValueError(f"Không tìm thấy case {case_id} sau khi ghi đè.")
    return _result(case, decision)


def _input_from_case(case: Row) -> CaseInput:
    received_at = datetime.fromisoformat(case["received_at"].replace("Z", "+00:00"))
    return CaseInput(
        sender=case["sender"] or "",
        subject=case["subject"] or "",
        body=case["body_raw"] or "",
        received_at=received_at,
        channel=cast(Literal["paste", "inbox", "verify"], case["channel"]),
    )


def rerun_case(case_id: str, actor: str) -> tuple[PipelineResult, dict]:
    """Chạy lại case trên corpus hiện tại và trả ba khác biệt phục vụ UI."""
    _require_admin(actor)
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if case is None:
        raise ValueError(f"Không tìm thấy case {case_id}.")
    before = _latest_decision(case_id)
    result = process_case(_input_from_case(case), actor=actor)
    before_ids = json.loads(before["evidence_ids_json"] or "[]")
    diff = {
        "decision": {"before": before["decision"], "after": result.decision.decision.value},
        "rule_id": {"before": before["rule_id"], "after": result.decision.rule_id},
        "evidence_ids": {"before": before_ids, "after": result.decision.evidence_ids},
    }
    log_event(
        case_id=case_id,
        actor=actor,
        action="RERUN_CASE",
        output_ref=result.case_id,
        reason="Đã chạy lại case trên phiên bản quy định hiện tại.",
        sources=result.decision.evidence_ids,
        corpus_version=result.corpus_version,
    )
    return result, diff
