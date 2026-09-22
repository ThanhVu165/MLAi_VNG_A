"""Trang hàng chờ để chuyên viên duyệt các case được chuyển tiếp."""

import json
import logging
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Row
from uuid import uuid4

import streamlit as st

from core.resume import validate_human_draft
from core.results import load_result
from core.sanitize import mask_pii
from core.types import CaseStatus, DraftReply, EscalationType
from core.worker import queue_resume
from corpus.api import get_corpus_version
from infra.audit import log_event
from infra.db import execute, fetch_all, fetch_one, get_connection, now_iso, transaction
from infra.settings import PENDING_STATUS_REFRESH_SECONDS
from ui.presentation import TYPE_LABELS, local_time, readable_text, reply_text

LOGGER = logging.getLogger(__name__)
UI_ACTOR = "HUMAN:local"
CHOICES = ("Chấp thuận", "Từ chối", "Quyết định khác")


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


@dataclass(frozen=True)
class PreviewDraft:
    case_id: str
    draft_id: str
    corpus_version: str
    subject: str
    body: str
    citations: tuple[str, ...]
    grounded: bool
    guard_failures: tuple[str, ...]


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
        LEFT JOIN escalations AS e ON e.case_id = c.case_id
        WHERE c.status IN (?, ?)
        ORDER BY queued_at ASC
        """,
        (CaseStatus.AWAITING_HUMAN, CaseStatus.HUMAN_DECIDED),
    )
    return tuple(
        QueueCase(
            case_id=row["case_id"],
            subject=row["subject"] or "Không có tiêu đề",
            body_masked=row["body_masked"] or "",
            corpus_version=row["corpus_version"],
            queued_at=row["queued_at"],
            escalation_type=row["escalation_type"] or EscalationType.FACT_UNRESOLVED,
            summary=row["summary"] or "Chưa có tóm tắt.",
            facts=_strings(row["facts_json"]),
            basis=_basis(row["basis_json"]),
            question=row["question"] or "Chưa có câu hỏi chuyển tiếp.",
            options=_strings(row["options_json"]),
        )
        for row in rows
    )


def _preview_drafts() -> tuple[PreviewDraft, ...]:
    rows = fetch_all(
        """
        SELECT c.case_id, c.corpus_version, d.draft_id, d.subject, d.body,
               d.citations_json, d.grounded, d.guard_failures_json
        FROM cases AS c
        JOIN drafts AS d ON d.case_id = c.case_id
        WHERE c.status = ?
          AND d.rowid = (
              SELECT MAX(rowid) FROM drafts WHERE case_id = c.case_id
          )
        ORDER BY d.rowid DESC
        """,
        (CaseStatus.PENDING_APPROVAL,),
    )
    return tuple(
        PreviewDraft(
            case_id=row["case_id"],
            draft_id=row["draft_id"],
            corpus_version=row["corpus_version"],
            subject=row["subject"] or "Không có tiêu đề",
            body=row["body"] or "",
            citations=_strings(row["citations_json"]),
            grounded=bool(row["grounded"]),
            guard_failures=_strings(row["guard_failures_json"]),
        )
        for row in rows
    )


def _open_decision(case_id: str) -> Row:
    case = fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))
    if case is not None and case["status"] == CaseStatus.HUMAN_DECIDED:
        decided = fetch_one(
            "SELECT * FROM human_decisions WHERE case_id = ? AND decided_at IS NOT NULL ORDER BY rowid DESC LIMIT 1",
            (case_id,),
        )
        if decided is not None:
            return decided
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
        (
            decision_id,
            case_id,
            UI_ACTOR,
            "PENDING_REVIEW",
            "Đã mở thẻ để đọc.",
            shown_at,
        ),
    )
    row = fetch_one("SELECT * FROM human_decisions WHERE id = ?", (decision_id,))
    if row is None:
        raise RuntimeError("Không tạo được bản ghi thời điểm mở thẻ.")
    return row


def _record_decision(case: QueueCase, record: Row, choice: str, reason: str) -> None:
    reason = reason.strip()
    if not reason:
        raise ValueError("Cần nhập lý do trước khi ghi quyết định.")
    decided_at = now_iso()
    shown_at = datetime.fromisoformat(record["shown_at"].replace("Z", "+00:00"))
    review_seconds = (
        datetime.fromisoformat(decided_at.replace("Z", "+00:00")) - shown_at
    ).total_seconds()
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if (
            connection.execute(
                "UPDATE cases SET status = ? WHERE case_id = ? AND status = ?",
                (CaseStatus.HUMAN_DECIDED, case.case_id, CaseStatus.AWAITING_HUMAN),
            ).rowcount
            != 1
        ):
            raise ValueError("Email đã có quyết định hoặc không còn trong hàng chờ. Hãy tải lại.")
        if (
            connection.execute(
                """UPDATE human_decisions SET choice = ?, reason = ?, decided_at = ?, review_seconds = ?
               WHERE id = ? AND decided_at IS NULL""",
                (choice, reason, decided_at, review_seconds, record["id"]),
            ).rowcount
            != 1
        ):
            raise ValueError("Quyết định đã được ghi nhận. Hãy tải lại.")
        queue_resume(case.case_id, connection=connection)
        log_event(
            case_id=case.case_id,
            actor=UI_ACTOR,
            action="HUMAN_DECISION",
            reason=mask_pii(reason),
            corpus_version=case.corpus_version,
            connection=connection,
        )


def _save_draft(preview: PreviewDraft, subject: str, body: str) -> None:
    with transaction() as connection:
        draft = validate_human_draft(
            preview.case_id,
            DraftReply(subject.strip(), body.strip(), list(preview.citations), False, []),
        )
        if not draft.subject or not draft.body:
            raise ValueError("Tiêu đề và nội dung email không được để trống.")
        changed = connection.execute(
            """
            UPDATE drafts
            SET subject = ?, body = ?, grounded = ?, guard_failures_json = ?
            WHERE draft_id = ? AND EXISTS (SELECT 1 FROM cases WHERE case_id = drafts.case_id AND status = 'PENDING_APPROVAL')
            """,
            (
                draft.subject,
                mask_pii(draft.body),
                int(draft.grounded),
                json.dumps(draft.guard_failures, ensure_ascii=False),
                preview.draft_id,
            ),
        ).rowcount
        if changed != 1:
            raise ValueError("Không tìm thấy bản nháp để sửa. Hãy tải lại trang.")
        log_event(
            case_id=preview.case_id,
            actor=UI_ACTOR,
            action="DRAFT_GENERATED",
            reason="Chuyên viên đã sửa nội dung và yêu cầu kiểm tra lại căn cứ trước khi duyệt gửi.",
            sources=draft.citations,
            corpus_version=get_corpus_version(),
        )


def _approve_send(preview: PreviewDraft) -> None:
    version = get_corpus_version()
    checked = validate_human_draft(
        preview.case_id,
        DraftReply(preview.subject, preview.body, list(preview.citations), False, []),
    )
    if not checked.grounded:
        raise ValueError("Phản hồi chưa vượt qua kiểm tra căn cứ. Hãy sửa và kiểm tra lại.")
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute(
            "SELECT * FROM drafts WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (preview.case_id,)
        ).fetchone()
        if (
            current is None
            or current["draft_id"] != preview.draft_id
            or current["body"] != preview.body
            or current["subject"] != preview.subject
            or _strings(current["citations_json"]) != preview.citations
        ):
            raise ValueError("Nội dung đã thay đổi. Hãy tải lại và đọc bản mới trước khi duyệt.")
        if get_corpus_version() != version:
            raise ValueError(
                "Quy định đã thay đổi trong lúc duyệt. Hãy đối chiếu lại trước khi gửi."
            )
        if (
            connection.execute(
                "UPDATE cases SET status = ?, send_deadline = NULL WHERE case_id = ? AND status = ?",
                (CaseStatus.SENT, preview.case_id, CaseStatus.PENDING_APPROVAL),
            ).rowcount
            != 1
        ):
            raise ValueError("Email không còn chờ duyệt gửi. Hãy tải lại.")
        log_event(
            case_id=preview.case_id,
            actor=UI_ACTOR,
            action="HUMAN_APPROVED_SEND",
            reason="Chuyên viên đã đọc bản hiện tại, duyệt và gửi email mô phỏng.",
            corpus_version=version,
            sources=list(preview.citations),
            connection=connection,
        )


def _return_to_queue(preview: PreviewDraft) -> None:
    with transaction() as connection:
        changed = connection.execute(
            "UPDATE cases SET status = ? WHERE case_id = ? AND status = ?",
            (CaseStatus.AWAITING_HUMAN, preview.case_id, CaseStatus.PENDING_APPROVAL),
        ).rowcount
        if changed != 1:
            raise ValueError("Email không còn chờ duyệt gửi. Hãy tải lại trang.")
        log_event(
            case_id=preview.case_id,
            actor=UI_ACTOR,
            action="HUMAN_REJECTED_DRAFT",
            reason="Chuyên viên trả bản nháp về hàng chờ để quyết định lại.",
            corpus_version=preview.corpus_version,
        )


def _render_card(case: QueueCase) -> None:
    st.subheader(case.subject)
    st.caption(
        f"Đang chờ từ {local_time(case.queued_at)} · {TYPE_LABELS.get(case.escalation_type, 'Cần chuyên viên xử lý')}"
    )
    st.write(readable_text(case.summary))
    with st.expander("Email và thông tin đã có"):
        st.text(case.body_masked)
        for fact in case.facts:
            st.write(readable_text(fact))
    for breadcrumb, excerpt in case.basis:
        with st.expander(breadcrumb):
            st.write(excerpt)
    if not case.basis:
        st.info("Chưa có quy định phù hợp. Chuyên viên cần xác nhận căn cứ hoặc hướng xử lý.")
    saved = load_result(case.case_id)
    prepared = saved.draft if saved else None
    if prepared:
        with st.expander("Phần trả lời đã chuẩn bị, chưa gửi"):
            st.text(reply_text(prepared.body, prepared.citations))
            if not prepared.grounded:
                st.warning("Phần này chưa đủ căn cứ để gửi; cần chỉnh sửa khi soạn phản hồi cuối.")
    st.subheader("Câu hỏi cần quyết định")
    st.write(case.question)


def _render_decision_form(case: QueueCase, record: Row) -> None:
    previous = fetch_one(
        "SELECT * FROM human_decisions WHERE case_id = ? AND decided_at IS NOT NULL ORDER BY rowid DESC LIMIT 1",
        (case.case_id,),
    )
    current = fetch_one("SELECT status FROM cases WHERE case_id = ?", (case.case_id,))
    decided = current is not None and current["status"] == CaseStatus.HUMAN_DECIDED
    if decided and previous:
        job = fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case.case_id,))
        pending = job is not None and job["state"] in ("queued", "running")
        st.info(
            "Quyết định đã lưu. Hệ thống đang soạn phản hồi; bạn có thể chuyển trang."
            if pending
            else "Quyết định đã lưu nhưng chưa soạn xong phản hồi. Bạn có thể thử soạn lại."
        )
        st.write(previous["choice"])
        st.write(previous["reason"])
        if job is not None and job["state"] == "failed":
            failure = fetch_one(
                "SELECT reason FROM audit_events WHERE case_id = ? AND action = 'CASE_ERROR' ORDER BY rowid DESC LIMIT 1",
                (case.case_id,),
            )
            if failure and failure["reason"]:
                st.warning(readable_text(failure["reason"]))
        if st.button("Thử soạn phản hồi lại", disabled=pending, key=f"resume_{case.case_id}"):
            try:
                queue_resume(case.case_id)
            except (RuntimeError, ValueError) as error:
                st.error(readable_text(str(error)))
            else:
                st.rerun()
        return
    choice = st.radio(
        "Quyết định của chuyên viên",
        (*case.options, "Quyết định khác") if case.options else CHOICES,
        key=f"choice_{case.case_id}",
    )
    reason = st.text_area(
        "Câu trả lời và lý do cụ thể",
        help="Ghi thông tin bổ sung hoặc quyết định của bạn. Hệ thống sẽ diễn đạt lại để bạn duyệt trước khi gửi.",
        key=f"reason_{case.case_id}",
    )
    if st.button(
        "Ghi quyết định và soạn phản hồi", disabled=not reason.strip(), key=f"decide_{case.case_id}"
    ):
        try:
            _record_decision(case, record, choice, reason)
        except (RuntimeError, ValueError) as error:
            st.error(readable_text(str(error)))
        else:
            st.rerun()


def _render_preview(preview: PreviewDraft) -> None:
    st.subheader("Đọc và duyệt phản hồi")
    if preview.grounded:
        st.caption("Nội dung đã được kiểm tra khi soạn và sẽ được đối chiếu lại khi bạn duyệt gửi.")
    else:
        st.warning(
            "Nội dung cần được kiểm tra lại trước khi gửi. Hãy chỉnh sửa và lưu để kiểm tra."
        )
    subject = st.text_input(
        "Tiêu đề email", value=preview.subject, key=f"subject_{preview.draft_id}"
    )
    display_body = reply_text(preview.body, list(preview.citations))
    body = st.text_area(
        "Nội dung email", value=display_body, height=240, key=f"body_{preview.draft_id}"
    )
    for index, citation in enumerate(preview.citations, start=1):
        from corpus.api import get_chunk

        chunk = get_chunk(citation)
        if chunk:
            with st.expander(f"[{index}] {chunk.breadcrumb}"):
                st.write(chunk.text)
    unsaved = subject != preview.subject or body != display_body
    if unsaved:
        st.info("Bạn đã chỉnh sửa. Hãy lưu và kiểm tra trước khi duyệt gửi.")
    approve, edit, return_to_queue = st.columns(3)
    if approve.button(
        "Duyệt và gửi", disabled=not preview.grounded or unsaved, key=f"approve_{preview.draft_id}"
    ):
        try:
            _approve_send(preview)
        except ValueError as error:
            st.error(readable_text(str(error)))
        else:
            st.rerun()
    if edit.button("Lưu và kiểm tra", key=f"edit_{preview.draft_id}"):
        for index, citation in enumerate(preview.citations, start=1):
            body = body.replace(f"[{index}]", f"[{citation}]")
        try:
            _save_draft(preview, subject, body)
        except ValueError as error:
            st.error(readable_text(str(error)))
        else:
            st.rerun()
    if return_to_queue.button("Trả lại hàng chờ", key=f"return_{preview.draft_id}"):
        try:
            _return_to_queue(preview)
        except ValueError as error:
            st.error(readable_text(str(error)))
        else:
            st.rerun()


@st.fragment(run_every=PENDING_STATUS_REFRESH_SECONDS)
def main() -> None:
    st.title("Cần chuyên viên xử lý")
    cases, previews = _queue_cases(), _preview_drafts()
    if not cases and not previews:
        st.info("Không có email đang chờ chuyên viên quyết định hoặc duyệt gửi.")
        return
    if cases:
        case_id = st.selectbox(
            "Email cần quyết định",
            [case.case_id for case in cases],
            format_func=lambda value: next(
                f"{case.subject} · {local_time(case.queued_at)}"
                for case in cases
                if case.case_id == value
            ),
        )
        selected = next(case for case in cases if case.case_id == case_id)
        record = _open_decision(selected.case_id)
        _render_card(selected)
        _render_decision_form(selected, record)
    if previews:
        st.divider()
        draft_id = st.selectbox(
            "Phản hồi chờ duyệt gửi",
            [item.draft_id for item in previews],
            format_func=lambda value: next(
                item.subject for item in previews if item.draft_id == value
            ),
        )
        preview = next(item for item in previews if item.draft_id == draft_id)
        _render_preview(preview)


main()
