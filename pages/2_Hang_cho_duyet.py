"""Trang hàng chờ để chuyên viên duyệt các case được chuyển tiếp."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Row
from uuid import uuid4

import streamlit as st

from core.explain import explain_plainly
from core.types import CaseStatus, EscalationType
from infra.audit import log_event
from infra.db import execute, fetch_all, fetch_one, now_iso, to_local


LOGGER = logging.getLogger(__name__)
UI_ACTOR = "HUMAN:demo"
CHOICES = ("Chấp thuận", "Từ chối", "Quyết định khác")
TYPE_LABELS: dict[str, str] = {
    EscalationType.FACT_UNRESOLVED: "Thiếu dữ kiện",
    EscalationType.OUT_OF_POLICY: "Ngoài phạm vi quy định",
    EscalationType.AUTHORITY_REQUIRED: "Cần phê duyệt",
}


@dataclass(frozen=True)
class QueueCase:
    case_id: str
    subject: str
    body_masked: str
    corpus_version: str
    queued_at: str
    escalation_type: str
    summary: str
    facts: tuple[str, ...]
    basis: tuple[tuple[str, str], ...]
    question: str
    options: tuple[str, ...]


def _strings(value: str | None) -> tuple[str, ...]:
    try:
        payload: object = json.loads(value or "[]")
    except json.JSONDecodeError as error:
        LOGGER.warning("Không đọc được dữ liệu thẻ chuyển tiếp: %s", error)
        return ()
    return (
        tuple(item for item in payload if isinstance(item, str))
        if isinstance(payload, list)
        else ()
    )


def _basis(value: str | None) -> tuple[tuple[str, str], ...]:
    try:
        payload: object = json.loads(value or "[]")
    except json.JSONDecodeError as error:
        LOGGER.warning("Không đọc được căn cứ của thẻ chuyển tiếp: %s", error)
        return ()
    if not isinstance(payload, list):
        return ()
    return tuple(
        (item[0], item[1])
        for item in payload
        if isinstance(item, list)
        and len(item) == 2
        and isinstance(item[0], str)
        and isinstance(item[1], str)
    )


def _queue_cases() -> tuple[QueueCase, ...]:
    rows = fetch_all(
        """
        SELECT c.case_id, c.subject, c.body_masked, c.corpus_version,
               COALESCE((
                   SELECT a.ts FROM audit_events AS a
                   WHERE a.case_id = c.case_id AND a.action = 'CASE_QUEUED'
                   ORDER BY a.rowid DESC LIMIT 1
               ), c.created_at) AS queued_at,
               e.escalation_type, e.summary, e.facts_json, e.basis_json, e.question, e.options_json
        FROM cases AS c
        JOIN escalations AS e ON e.case_id = c.case_id
        WHERE c.status = ?
        ORDER BY queued_at ASC
        """,
        (CaseStatus.AWAITING_HUMAN,),
    )
    return tuple(
        QueueCase(
            case_id=row["case_id"],
            subject=row["subject"] or "Không có tiêu đề",
            body_masked=row["body_masked"] or "",
            corpus_version=row["corpus_version"],
            queued_at=row["queued_at"],
            escalation_type=row["escalation_type"],
            summary=row["summary"] or "Chưa có tóm tắt.",
            facts=_strings(row["facts_json"]),
            basis=_basis(row["basis_json"]),
            question=row["question"] or "Chưa có câu hỏi chuyển tiếp.",
            options=_strings(row["options_json"]),
        )
        for row in rows
    )


def _open_decision(case_id: str) -> Row:
    row = fetch_one(
        """
        SELECT * FROM human_decisions
        WHERE case_id = ? AND actor = ? AND decided_at IS NULL
        ORDER BY rowid DESC LIMIT 1
        """,
        (case_id, UI_ACTOR),
    )
    if row is not None:
        return row
    shown_at = now_iso()
    decision_id = str(uuid4())
    execute(
        """
        INSERT INTO human_decisions (id, case_id, actor, choice, reason, shown_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (decision_id, case_id, UI_ACTOR, "PENDING_REVIEW", "Đã mở thẻ để đọc.", shown_at),
    )
    row = fetch_one("SELECT * FROM human_decisions WHERE id = ?", (decision_id,))
    if row is None:
        raise RuntimeError("Không tạo được bản ghi thời điểm mở thẻ.")
    return row


def _record_decision(case: QueueCase, record: Row, choice: str, reason: str) -> None:
    decided_at = now_iso()
    shown_at = datetime.fromisoformat(record["shown_at"].replace("Z", "+00:00"))
    review_seconds = (
        datetime.fromisoformat(decided_at.replace("Z", "+00:00")) - shown_at
    ).total_seconds()
    if (
        execute(
            """
        UPDATE human_decisions
        SET choice = ?, reason = ?, decided_at = ?, review_seconds = ?
        WHERE id = ? AND decided_at IS NULL
        """,
            (choice, reason, decided_at, review_seconds, record["id"]),
        )
        != 1
    ):
        raise ValueError("Case này đã có quyết định; hãy tải lại hàng chờ.")
    if (
        execute(
            "UPDATE cases SET status = ? WHERE case_id = ? AND status = ?",
            (CaseStatus.HUMAN_DECIDED, case.case_id, CaseStatus.AWAITING_HUMAN),
        )
        != 1
    ):
        raise ValueError("Case không còn ở hàng chờ; hãy tải lại.")
    log_event(
        case_id=case.case_id,
        actor=UI_ACTOR,
        action="HUMAN_DECISION",
        reason=reason,
        corpus_version=case.corpus_version,
    )


def _render_card(case: QueueCase) -> None:
    st.subheader("Thẻ chuyển tiếp chuyên viên")
    st.caption(
        f"Đang chờ từ {to_local(case.queued_at)} · {TYPE_LABELS.get(case.escalation_type, case.escalation_type)}"
    )
    st.markdown("#### Tóm tắt")
    st.write(case.summary)
    st.markdown("#### Dữ kiện")
    for fact in case.facts or ("Chưa có dữ kiện đã xác nhận.",):
        st.write(f"• {fact}")
    st.markdown("#### Căn cứ")
    for breadcrumb, excerpt in case.basis:
        with st.expander(breadcrumb):
            st.write(excerpt)
    if not case.basis:
        st.info("Chưa có căn cứ quy định đang hiệu lực.")
    st.markdown("#### Câu hỏi")
    st.write(case.question)
    if case.options:
        st.radio("Phương án đề xuất", case.options, key=f"options_{case.case_id}")


def _render_decision_form(case: QueueCase, record: Row) -> None:
    st.subheader("Quyết định của chuyên viên")
    choice = st.radio("Chọn quyết định", CHOICES, key=f"choice_{case.case_id}")
    reason = st.text_area("Lý do quyết định", key=f"reason_{case.case_id}")
    if st.button("Ghi quyết định", disabled=not reason.strip(), key=f"decide_{case.case_id}"):
        try:
            _record_decision(case, record, choice, reason.strip())
        except (RuntimeError, ValueError) as error:
            st.error(str(error))
        else:
            st.success("Đã ghi quyết định và lý do vào nhật ký kiểm toán.")
            st.rerun()


def _render_explanation(case_id: str) -> None:
    if st.button("Giải thích cho người không chuyên", key=f"explain_{case_id}"):
        try:
            explanation = explain_plainly(case_id)
        except ValueError:
            st.error("Chưa thể tạo giải thích cho case này. Hãy kiểm tra lại dữ liệu.")
        else:
            with st.container(border=True):
                st.write(explanation)


def main() -> None:
    st.set_page_config(page_title="Hàng chờ duyệt", page_icon="🧑‍⚖️", layout="wide")
    st.title("Hàng chờ duyệt")
    st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
    cases = _queue_cases()
    if not cases:
        st.info("Chưa có case chờ duyệt. Hãy xử lý email cần chuyển tiếp để tạo thẻ quyết định.")
        return
    selected = st.selectbox(
        "Chọn case đang chờ",
        cases,
        format_func=lambda case: f"{case.subject} · {to_local(case.queued_at)}",
    )
    st.caption(f"Nội dung đã che dữ liệu cá nhân: {selected.body_masked}")
    record = _open_decision(selected.case_id)
    _render_card(selected)
    _render_decision_form(selected, record)
    _render_explanation(selected.case_id)


main()
