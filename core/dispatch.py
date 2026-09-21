"""Vòng đời gửi mô phỏng, với mốc dừng được lưu ở SQLite."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from sqlite3 import Row
from uuid import uuid4

from core.pipeline import _new_ulid
from core.sanitize import mask_pii
from core.types import CaseStatus, Decision, DraftReply, PolicyDecision
from infra.audit import log_event
from infra.db import execute, fetch_one, now_iso, to_utc_iso
from infra.settings import PENDING_SEND_SECONDS

logger = logging.getLogger(__name__)


def _utc_now(value: datetime | None = None) -> datetime:
    now = value or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Thời điểm gửi phải có múi giờ.")
    return now.astimezone(timezone.utc)


def _case(case_id: str) -> Row:
    row = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if row is None:
        raise ValueError(f"Không tìm thấy case {case_id}.")
    return row


def _pending_case(case_id: str, now: datetime) -> Row:
    row = _case(case_id)
    if row["status"] != CaseStatus.PENDING_SEND:
        raise ValueError(f"Case {case_id} không ở trạng thái PENDING_SEND.")
    deadline = datetime.fromisoformat(row["send_deadline"].replace("Z", "+00:00"))
    if deadline <= now:
        dispatch_due(case_id, now=now)
        raise ValueError(f"Case {case_id} đã SENT nên không thể sửa.")
    return row


def schedule_auto_reply(case_id: str, *, decision: PolicyDecision, actor: str) -> None:
    """Lên lịch gửi cho một quyết định AUTO_REPLY đã được Policy Engine duyệt."""
    if decision.decision is not Decision.AUTO_REPLY:
        raise ValueError("Chỉ AUTO_REPLY mới được lên lịch gửi.")
    row = _case(case_id)
    if row["status"] not in (CaseStatus.RECEIVED, CaseStatus.PROCESSING):
        raise ValueError(f"Case {case_id} ở trạng thái {row['status']} không thể lên lịch gửi.")
    deadline = to_utc_iso(_utc_now() + timedelta(seconds=PENDING_SEND_SECONDS))
    if (
        execute(
            """
            UPDATE cases SET status = ?, send_deadline = ?
            WHERE case_id = ? AND status IN (?, ?)
            """,
            (
                CaseStatus.PENDING_SEND,
                deadline,
                case_id,
                CaseStatus.RECEIVED,
                CaseStatus.PROCESSING,
            ),
        )
        != 1
    ):
        raise ValueError(f"Case {case_id} không thể lên lịch gửi.")
    log_event(
        case_id=case_id,
        actor=actor,
        action="SEND_SCHEDULED",
        rule_id=decision.rule_id,
        reason="Đã lên lịch gửi mô phỏng sau thời gian chờ.",
        corpus_version=decision.corpus_version,
    )
    logger.info("Đã lên lịch gửi case %s.", case_id)


def cancel_send(case_id: str, actor: str, reason: str) -> None:
    """Hủy một lần gửi còn trong khoảng chờ và giữ lại lý do của người dùng."""
    row = _pending_case(case_id, _utc_now())
    if (
        execute(
            "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ? AND status = ?",
            (CaseStatus.CANCELLED, case_id, CaseStatus.PENDING_SEND),
        )
        != 1
    ):
        raise ValueError(f"Case {case_id} không thể hủy gửi.")
    log_event(
        case_id=case_id,
        actor=actor,
        action="CANCEL_SEND",
        reason=reason,
        corpus_version=row["corpus_version"],
    )
    logger.info("Đã hủy gửi case %s.", case_id)


def escalate_from_pending(case_id: str, *, actor: str, reason: str) -> None:
    """Chuyển một lần gửi còn chờ sang hàng đợi người duyệt."""
    row = _pending_case(case_id, _utc_now())
    if (
        execute(
            "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ? AND status = ?",
            (CaseStatus.AWAITING_HUMAN, case_id, CaseStatus.PENDING_SEND),
        )
        != 1
    ):
        raise ValueError(f"Case {case_id} không thể chuyển cho người duyệt.")
    log_event(
        case_id=case_id,
        actor=actor,
        action="CASE_QUEUED",
        reason=reason,
        corpus_version=row["corpus_version"],
    )
    logger.info("Đã chuyển case %s cho người duyệt.", case_id)


def dispatch_due(case_id: str, *, actor: str = "SYSTEM", now: datetime | None = None) -> bool:
    """Gửi mô phỏng khi mốc DB đã hết hạn, trả ``True`` nếu đã chuyển trạng thái."""
    row = _case(case_id)
    if row["status"] != CaseStatus.PENDING_SEND:
        return False
    current = _utc_now(now)
    deadline = datetime.fromisoformat(row["send_deadline"].replace("Z", "+00:00"))
    if deadline > current:
        return False
    if (
        execute(
            """
            UPDATE cases SET status = ?, send_deadline = NULL
            WHERE case_id = ? AND status = ? AND send_deadline = ?
            """,
            (CaseStatus.SENT, case_id, CaseStatus.PENDING_SEND, row["send_deadline"]),
        )
        != 1
    ):
        return False
    log_event(
        case_id=case_id,
        actor=actor,
        action="SEND_DISPATCHED",
        reason="Đã hết thời gian chờ gửi mô phỏng.",
        corpus_version=row["corpus_version"],
    )
    logger.info("Đã gửi mô phỏng case %s.", case_id)
    return True


def create_correction_email(parent_case_id: str, *, actor: str, draft: DraftReply) -> str:
    """Tạo Correction Email mới cho một case SENT, không sửa case gốc."""
    parent = _case(parent_case_id)
    if parent["status"] != CaseStatus.SENT:
        raise ValueError("Correction Email chỉ được tạo từ case SENT.")
    case_id = f"c_{_new_ulid()}"
    created_at = now_iso()
    body_masked = mask_pii(draft.body)
    execute(
        """
        INSERT INTO cases (
            case_id, trace_id, channel, sender, subject, body_raw, body_clean, body_masked,
            received_at, created_at, status, corpus_version, parent_case_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            str(uuid4()),
            parent["channel"],
            parent["sender"],
            draft.subject,
            draft.body,
            body_masked,
            body_masked,
            created_at,
            created_at,
            CaseStatus.PENDING_APPROVAL,
            parent["corpus_version"],
            parent_case_id,
        ),
    )
    execute(
        """
        INSERT INTO drafts (
            draft_id, case_id, kind, subject, body, citations_json, grounded, guard_failures_json,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            case_id,
            "correction",
            draft.subject,
            body_masked,
            json.dumps(draft.citations, ensure_ascii=False),
            int(draft.grounded),
            json.dumps(draft.guard_failures, ensure_ascii=False),
            created_at,
        ),
    )
    log_event(
        case_id=parent_case_id,
        actor=actor,
        action="CORRECTION_CREATED",
        output_ref=case_id,
        reason="Đã tạo Correction Email liên kết với case đã gửi.",
        corpus_version=parent["corpus_version"],
    )
    logger.info("Đã tạo Correction Email %s cho case %s.", case_id, parent_case_id)
    return case_id
