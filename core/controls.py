"""Các can thiệp quản trị vào lifecycle case."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import datetime, timezone
from sqlite3 import Connection, Row
from typing import Literal, cast
from uuid import uuid4

from core.dispatch import cancel_send
from core.pipeline import process_case
from core.sanitize import mask_pii
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    EscalationType,
    PipelineResult,
    PolicyDecision,
)
from infra.audit import log_event
from corpus.api import get_chunk
from infra.db import execute, fetch_one, get_connection, now_iso

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


def _store_manual_decision(
    connection: Connection,
    case: Row,
    new_decision: Decision,
    actor: str,
    reason: str,
    *,
    rule_id: str,
    action: str,
) -> PolicyDecision:
    """Lưu quyết định, câu hỏi và trạng thái cùng giao dịch đang khóa của người gọi."""
    case_id = case["case_id"]
    reason = mask_pii(reason.strip())
    if new_decision is Decision.AUTO_REPLY:
        draft = connection.execute(
            "SELECT grounded FROM drafts WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
        ).fetchone()
        if draft is None or not draft["grounded"]:
            raise ValueError("Cần bản nháp đã kiểm tra căn cứ trước khi duyệt trả lời.")
    previous = connection.execute(
        "SELECT * FROM decisions WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
    ).fetchone()
    if previous is None:
        raise ValueError("Email chưa có quyết định để thay đổi.")
    if Decision(previous["decision"]) is new_decision:
        raise ValueError("Quyết định ghi đè phải khác quyết định hiện tại.")
    decision_id = str(uuid4())
    escalation_type = EscalationType.FACT_UNRESOLVED if new_decision is Decision.ESCALATE else None
    evidence_ids = json.loads(previous["evidence_ids_json"] or "[]")
    decision = PolicyDecision(
        new_decision,
        escalation_type,
        rule_id,
        reason,
        evidence_ids,
        case["corpus_version"],
    )
    connection.execute(
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
    connection.execute(
        "UPDATE decisions SET superseded_by = ? WHERE decision_id = ?",
        (decision_id, previous["decision_id"]),
    )
    status = (
        CaseStatus.AWAITING_HUMAN
        if new_decision is Decision.ESCALATE
        else CaseStatus.PENDING_APPROVAL
    )
    connection.execute(
        "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ?", (status, case_id)
    )
    if new_decision is Decision.ESCALATE:
        extraction = connection.execute(
            "SELECT payload_json FROM extractions WHERE case_id = ?", (case_id,)
        ).fetchone()
        facts = json.loads(extraction["payload_json"]).get("critical_facts", {}) if extraction else {}
        basis = [
            (chunk.breadcrumb, chunk.text)
            for cid in evidence_ids
            if (chunk := get_chunk(cid)) is not None
        ]
        connection.execute(
            """INSERT OR REPLACE INTO escalations(case_id, escalation_type, summary, facts_json,
               basis_json, question, options_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case_id,
                escalation_type,
                mask_pii(case["subject"]),
                json.dumps([f"Lý do dừng gửi: {reason}"] + [mask_pii(f"{key}: {value}") for key, value in facts.items()], ensure_ascii=False),
                json.dumps(basis, ensure_ascii=False),
                f"Với email “{mask_pii(case['subject'])}” đang dừng vì “{reason}”, anh/chị xác nhận phản hồi đã soạn hay yêu cầu bổ sung trước khi trả lời?",
                json.dumps(["Xác nhận phản hồi", "Yêu cầu bổ sung"], ensure_ascii=False),
                now_iso(),
            ),
        )
    log_event(
        case_id=case_id,
        actor=actor,
        action=action,
        rule_id=decision.rule_id,
        reason=reason,
        sources=evidence_ids,
        corpus_version=decision.corpus_version,
        connection=connection,
    )
    return decision


def override_decision(
    case_id: str, new_decision: Decision, actor: str, reason: str
) -> PipelineResult:
    """Đổi hướng xử lý trong khóa DB; không ghi đè thư vừa được tiến trình nền gửi."""
    _require_admin(actor)
    if not reason.strip():
        raise ValueError("Lý do ghi đè là bắt buộc.")
    if new_decision not in (Decision.AUTO_REPLY, Decision.ESCALATE):
        raise ValueError("Chỉ có thể chuyển giữa trả lời thông tin và chờ chuyên viên.")
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        case = connection.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        if case is None:
            raise ValueError("Không tìm thấy email cần thay đổi.")
        if case["status"] not in (
            CaseStatus.PENDING_SEND, CaseStatus.AWAITING_HUMAN, CaseStatus.PENDING_APPROVAL,
            CaseStatus.NEEDS_RECHECK,
        ):
            raise ValueError("Không được ghi đè email đã kết thúc, đang xử lý hoặc đã có quyết định của chuyên viên.")
        decision = _store_manual_decision(
            connection, case, new_decision, actor, reason,
            rule_id="ADMIN_OVERRIDE", action="OVERRIDE_DECISION",
        )
        updated = connection.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        assert updated is not None
        return _result(updated, decision)


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
    if case["status"] in (
        CaseStatus.SENT,
        CaseStatus.RESOLVED,
        CaseStatus.RECEIVED,
        CaseStatus.PROCESSING,
        CaseStatus.PENDING_SEND,
    ):
        raise ValueError(
            "Không chạy lại thư đã gửi hoặc đang xử lý/chờ gửi; hãy hủy lần gửi trước nếu còn được phép."
        )
    before = _latest_decision(case_id)
    result = process_case(_input_from_case(case), actor=actor)
    execute("UPDATE cases SET parent_case_id = ? WHERE case_id = ?", (case_id, result.case_id))
    execute(
        "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ? AND status IN (?, ?, ?)",
        (
            CaseStatus.CANCELLED,
            case_id,
            CaseStatus.AWAITING_HUMAN,
            CaseStatus.HUMAN_DECIDED,
            CaseStatus.PENDING_APPROVAL,
        ),
    )
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
