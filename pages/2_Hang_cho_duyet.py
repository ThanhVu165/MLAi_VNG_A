"""Trang hàng chờ để chuyên viên duyệt các case được chuyển tiếp (Human Review Workspace)."""

import json
import logging
from contextlib import closing
from datetime import datetime
from sqlite3 import Error as DatabaseError, Row
from typing import NamedTuple
from uuid import uuid4

import streamlit as st

from core.resume import validate_human_draft
from core.results import load_result
from core.sanitize import mask_pii
from core.types import CaseStatus, DraftReply, EscalationType
from core.worker import queue_resume
from corpus.api import get_chunk, get_corpus_version
from infra.audit import log_event
from infra.db import execute, fetch_all, fetch_one, get_connection, now_iso, transaction
from infra.settings import PENDING_STATUS_REFRESH_SECONDS
from ui.presentation import (
    TYPE_LABELS,
    badge_html,
    decision_badge_html,
    empty_state_card_html,
    inject_app_css,
    local_time,
    page_header_html,
    readable_text,
    reply_text,
    status_badge_html,
    stop_reason_badge_html,
    stop_reason_text,
)

LOGGER = logging.getLogger(__name__)
UI_ACTOR = "HUMAN:local"
CHOICES = ("Chấp thuận", "Từ chối", "Quyết định khác")


class QueueCase(NamedTuple):
    case_id: str
    subject: str
    sender: str
    body_masked: str
    corpus_version: str
    queued_at: str
    status: str
    escalation_type: str
    summary: str
    facts: tuple[str, ...]
    basis: tuple[tuple[str, str], ...]
    question: str
    options: tuple[str, ...]


class PreviewDraft(NamedTuple):
    case_id: str
    draft_id: str
    recipient: str
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
        SELECT c.case_id, c.subject, c.sender, c.body_masked, c.corpus_version, c.status,
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
            sender=row["sender"] or "Không rõ người gửi",
            body_masked=row["body_masked"] or "",
            corpus_version=row["corpus_version"],
            queued_at=row["queued_at"],
            status=row["status"] or CaseStatus.AWAITING_HUMAN,
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
    # Giữ người nhận, nội dung và phiên bản nguồn cùng một thời điểm đọc.
    with transaction():
        version = get_corpus_version()
        rows = fetch_all(
            """
            SELECT c.case_id, c.sender, d.draft_id, d.subject, d.body,
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
            recipient=row["sender"] or "",
            corpus_version=version,
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
        case = connection.execute(
            "SELECT sender FROM cases WHERE case_id = ?", (preview.case_id,)
        ).fetchone()
        if case is None or (case["sender"] or "") != preview.recipient:
            raise ValueError("Người nhận đã thay đổi. Hãy tải lại và đọc bản mới trước khi duyệt.")
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
        if version != preview.corpus_version or get_corpus_version() != preview.corpus_version:
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
    # A. Case Header
    st.markdown(
        f"""
        <div class="ex-card">
            <div class="ex-card-title">Hồ sơ xem xét · Case ID: <code>{case.case_id[:16]}</code></div>
            <h2 style="margin: 0 0 10px 0; font-size: 1.25rem; font-weight: 700; color: #0F172A;">{case.subject}</h2>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 12px;">
                {decision_badge_html('ESCALATE')}
                {status_badge_html(case.status)}
                {stop_reason_badge_html(case.escalation_type)}
            </div>
            <div style="font-size: 12.5px; color: #64748B; display: flex; gap: 20px; flex-wrap: wrap; border-top: 1px solid #F1F5F9; padding-top: 10px;">
                <span><strong>Sinh viên:</strong> {case.sender}</span>
                <span><strong>Thời điểm tiếp nhận:</strong> {local_time(case.queued_at)}</span>
                <span><strong>Phiên bản quy định:</strong> <code>{case.corpus_version}</code></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # B. Why Exodia stopped (Vì sao Exodia dừng ở đây)
    stop_label = TYPE_LABELS.get(case.escalation_type, "Cần chuyên viên xử lý")
    stop_desc = stop_reason_text(case.escalation_type)
    st.markdown(
        f"""
        <div class="ex-stop-card">
            <div class="ex-stop-header">
                <span>⚠️ Vì sao Exodia dừng ở đây: <strong>{stop_label}</strong></span>
            </div>
            <p class="ex-stop-desc">{stop_desc}</p>
            <div style="margin-top: 8px; font-size: 13px; color: #92400E;">
                <strong>Tóm tắt nhận định:</strong> {readable_text(case.summary)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # C. Yêu cầu gốc <-> Căn cứ áp dụng (Evidence near decision)
    col_orig, col_basis = st.columns(2, gap="medium")
    with col_orig:
        st.markdown('<div class="ex-card-title">📩 Yêu cầu gốc từ sinh viên</div>', unsafe_allow_html=True)
        st.text_area(
            "Nội dung email",
            value=case.body_masked,
            height=200,
            disabled=True,
            label_visibility="collapsed",
            key=f"orig_body_{case.case_id}",
        )
        if case.facts:
            with st.expander(f"Dữ kiện trích xuất ({len(case.facts)})", expanded=True):
                for fact in case.facts:
                    st.markdown(f"• {readable_text(fact)}")

    with col_basis:
        st.markdown('<div class="ex-card-title">📖 Căn cứ quy chế đối chiếu</div>', unsafe_allow_html=True)
        if case.basis:
            for breadcrumb, excerpt in case.basis:
                st.markdown(
                    f"""
                    <div class="ex-evidence-box">
                        <div class="ex-evidence-breadcrumb">{breadcrumb}</div>
                        <div class="ex-evidence-text">{excerpt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Chưa có quy định nào trong bộ dữ liệu hiện hành khớp với yêu cầu này. Chuyên viên cần xác nhận căn cứ hoặc hướng xử lý ngoài quy chế.")

    # D. Missing information / Question
    st.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 12px 16px; margin: 12px 0 16px 0;">
            <div style="font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 4px;">❓ Câu hỏi cần chuyên viên kết luận</div>
            <div style="font-size: 14px; font-weight: 600; color: #0F172A;">{case.question}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saved = load_result(case.case_id)
    prepared = saved.draft if saved else None
    if prepared:
        with st.expander("Phần trả lời dự kiến (chưa hoàn thiện, chưa gửi)", expanded=False):
            st.text(reply_text(prepared.body, prepared.citations))
            if not prepared.grounded:
                st.warning("Bản nháp dự kiến này chưa vượt qua kiểm tra căn cứ (Ground Guard); cần chỉnh sửa khi duyệt gửi.")


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
        st.markdown(
            f"""
            <div class="ex-card" style="border-left: 4px solid #7C3AED;">
                <div class="ex-card-title">Đã ghi nhận quyết định của chuyên viên</div>
                <div style="font-size: 14px; font-weight: 600; color: #4C1D95; margin-bottom: 6px;">Quyết định: {previous['choice']}</div>
                <div style="font-size: 13px; color: #334155; margin-bottom: 8px;"><strong>Lý do:</strong> {previous['reason']}</div>
                <div style="font-size: 12px; color: #64748B;">Thời gian xem xét: {previous['review_seconds'] or 0:.1f} giây · Người duyệt: <code>{previous['actor']}</code></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if pending:
            st.info("Hệ thống đang chạy worker nền để soạn thảo lại phản hồi theo chỉ đạo của bạn...")
        else:
            st.caption("Quyết định đã lưu. Nếu cần tạo lại phản hồi, bạn có thể bấm nút bên dưới:")
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

    st.markdown('<div class="ex-card-title">⚖️ Quyết định chuyên môn của bạn</div>', unsafe_allow_html=True)
    choices_options = (*case.options, "Quyết định khác") if case.options else CHOICES
    choice = st.radio(
        "Lựa chọn hướng giải quyết",
        choices_options,
        index=None,
        key=f"choice_{case.case_id}",
    )
    reason = st.text_area(
        "Lý do & chỉ đạo nghiệp vụ cụ thể",
        placeholder="Ghi rõ lý do hoặc chỉ đạo bổ sung. Hệ thống sẽ căn cứ vào đây để soạn thảo bản nháp phản hồi gửi sinh viên.",
        help="Ghi thông tin bổ sung hoặc quyết định của bạn. Hệ thống sẽ diễn đạt lại để bạn duyệt trước khi gửi.",
        key=f"reason_{case.case_id}",
    )

    # CR2: Professional Action Preview
    choice_label = f'"{choice}"' if choice else "(chưa chọn hướng giải quyết)"
    st.markdown(
        f"""
        <div class="ex-action-preview">
            <div class="ex-action-preview-title">📋 Sau khi xác nhận quyết định</div>
            <div class="ex-action-preview-item">• <strong>Ghi nhận quyết định:</strong> Lưu lựa chọn {choice_label} và lý do chuyên môn của bạn vào hồ sơ xử lý.</div>
            <div class="ex-action-preview-item">• <strong>Chuẩn bị phản hồi:</strong> Hệ thống tự động tạo bản nháp thư trả lời sinh viên theo đúng chỉ đạo trên.</div>
            <div class="ex-action-preview-item">• <strong>Chưa gửi email:</strong> Email <u>chưa</u> được gửi ra ngoài cho đến khi bạn kiểm tra và duyệt bản nháp.</div>
            <div class="ex-action-preview-item">• <strong>Bước tiếp theo:</strong> Bản nháp sẽ chuyển sang hàng chờ "Bản nháp chờ duyệt gửi" để bạn đối chiếu căn cứ lần cuối.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Chi tiết kỹ thuật & kiểm toán (Audit trace)", expanded=False):
        st.caption("Chuyển trạng thái: HUMAN_DECIDED · Người thao tác: HUMAN:local · Sự kiện kiểm toán: HUMAN_DECISION · Xếp lịch tác tử nền")

    can_submit = choice is not None and bool(reason.strip())
    if not can_submit:
        st.caption("ℹ️ Hãy chọn một hướng giải quyết và nhập lý do nghiệp vụ để kích hoạt nút ghi quyết định.")

    if st.button(
        "Ghi quyết định và soạn phản hồi",
        type="primary",
        disabled=not can_submit,
        key=f"decide_{case.case_id}",
    ):
        try:
            _record_decision(case, record, choice, reason)
        except (RuntimeError, ValueError) as error:
            st.error(readable_text(str(error)))
        else:
            st.rerun()


def _render_preview(preview: PreviewDraft) -> None:
    # Giữ đúng bản người dùng đã đọc qua rerun và cả hai bước xác nhận.
    preview_key = f"approval_preview_{preview.draft_id}"
    current = preview
    if preview_key not in st.session_state:
        st.session_state[preview_key] = preview._asdict()
    preview = PreviewDraft(**st.session_state[preview_key])
    stale = preview != current
    if stale:
        st.warning("Người nhận, quy định hoặc bản nháp đã thay đổi. Hãy tải lại bản xem trước.")
        if st.button("Tải lại bản xem trước", key=f"refresh_preview_{preview.draft_id}"):
            st.session_state[preview_key] = current._asdict()
            st.session_state[f"confirm_pending_{preview.draft_id}"] = False
            st.rerun()
    # A. Header
    st.markdown(
        f"""
        <div class="ex-card">
            <div class="ex-card-title">Kiểm tra phản hồi trước khi gửi · Draft ID: <code>{preview.draft_id[:16]}</code></div>
            <h2 style="margin: 0 0 10px 0; font-size: 1.25rem; font-weight: 700; color: #0F172A;">{preview.subject}</h2>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 12px;">
                {status_badge_html('PENDING_APPROVAL')}
                {badge_html('Căn cứ hợp lệ (Grounding OK)', 'auto') if preview.grounded else badge_html('Cần kiểm tra căn cứ', 'danger')}
                <span style="font-size: 12px; color: #64748B;">Quy chế: <code>{preview.corpus_version}</code></span>
            </div>
            <div style="font-size: 12.5px; color: #64748B; border-top: 1px solid #F1F5F9; padding-top: 8px;">
                <strong>Người nhận:</strong> {preview.recipient}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # B. Grounding & Stale validation alert
    if preview.grounded:
        st.caption("✓ Bản nháp đã vượt qua kiểm tra căn cứ. Hệ thống sẽ đối chiếu lại nguyên văn và phiên bản quy chế khi bạn bấm duyệt.")
    else:
        st.warning("⚠️ Bản nháp này chưa đạt tiêu chuẩn căn cứ (Ground Guard). Bạn cần chỉnh sửa nội dung hoặc bổ sung trích dẫn và bấm 'Lưu và kiểm tra' trước khi được phép duyệt gửi.")

    # C. Editors
    subject = st.text_input(
        "Tiêu đề email phản hồi", value=preview.subject, key=f"subject_{preview.draft_id}"
    )
    display_body = reply_text(preview.body, list(preview.citations))
    body = st.text_area(
        "Nội dung email phản hồi (có trích dẫn [1], [2]...)",
        value=display_body,
        height=220,
        key=f"body_{preview.draft_id}",
    )

    if preview.citations:
        st.markdown('<div class="ex-card-title" style="margin-top: 12px;">📚 Các điều khoản được trích dẫn trong thư</div>', unsafe_allow_html=True)
        for index, citation in enumerate(preview.citations, start=1):
            chunk = get_chunk(citation)
            if chunk:
                with st.expander(f"[{index}] {chunk.breadcrumb}"):
                    st.write(chunk.text)

    unsaved = subject != preview.subject or body != display_body
    if unsaved:
        st.info("ℹ️ Bạn đã chỉnh sửa nội dung. Hãy bấm 'Lưu và kiểm tra' để đối chiếu lại căn cứ trước khi duyệt gửi.")

    # CR2: Professional Action Preview
    st.markdown(
        f"""
        <div class="ex-action-preview">
            <div class="ex-action-preview-title">📋 Kết quả sau khi thực hiện hành động</div>
            <div class="ex-action-preview-item">• <strong>Duyệt và gửi:</strong> Hoàn tất xử lý, gửi phản hồi chính thức đến sinh viên ({preview.recipient}) và hủy lịch hẹn tự động.</div>
            <div class="ex-action-preview-item">• <strong>Lưu và kiểm tra:</strong> Cập nhật nội dung sửa đổi và kiểm tra lại căn cứ trích dẫn (Ground Guard) mà chưa gửi thư.</div>
            <div class="ex-action-preview-item">• <strong>Trả lại hàng chờ:</strong> Chuyển hồ sơ trở lại hàng chờ quyết định để chuyên viên định hướng lại từ đầu.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Chi tiết kỹ thuật & kiểm toán (Audit trace)", expanded=False):
        st.caption("Trạng thái chuyển tiếp: SENT (nếu duyệt) hoặc AWAITING_HUMAN (nếu trả lại) · Sự kiện kiểm toán: HUMAN_APPROVED_SEND / HUMAN_REJECTED_DRAFT")

    confirm_key = f"confirm_pending_{preview.draft_id}"
    is_confirming = st.session_state.get(confirm_key, False)

    # Nếu người dùng sửa text chưa lưu thì tự động hủy trạng thái chờ xác nhận
    if unsaved:
        is_confirming = False
        st.session_state[confirm_key] = False

    if is_confirming:
        st.warning(
            f"⚠️ **XÁC NHẬN PHÁT HÀNH EMAIL CHÍNH THỨC**\n\n"
            f"• **Người nhận:** `{preview.recipient}`\n\n"
            f"• **Tiêu đề:** {subject}\n\n"
            f"• **Cảnh báo:** Email này sẽ được chính thức phát hành ngay lập tức tới người nhận và không thể hoàn tác trong hàng chờ.",
            icon="⚠️",
        )
        col_cancel, col_confirm = st.columns(2)
        if col_cancel.button("Hủy", key=f"cancel_send_{preview.draft_id}"):
            st.session_state[confirm_key] = False
            if "confirm" in st.query_params:
                del st.query_params["confirm"]
            st.rerun()

        if col_confirm.button(
            "Xác nhận gửi", type="primary", key=f"confirm_send_{preview.draft_id}",
            disabled=stale or not preview.grounded or unsaved,
        ):
            try:
                _approve_send(preview)
                del st.session_state[preview_key]
                st.session_state[confirm_key] = False
                if "confirm" in st.query_params:
                    del st.query_params["confirm"]
            except (ValueError, DatabaseError) as error:
                st.error(readable_text(str(error)))
            else:
                st.rerun()
    else:
        approve, edit, return_to_queue = st.columns(3)
        if approve.button(
            "Duyệt và gửi",
            disabled=not preview.grounded or unsaved or stale,
            key=f"approve_{preview.draft_id}",
        ):
            st.session_state[confirm_key] = True
            st.rerun()

        if edit.button("Lưu và kiểm tra", key=f"edit_{preview.draft_id}"):
            for index, citation in enumerate(preview.citations, start=1):
                body = body.replace(f"[{index}]", f"[{citation}]")
            try:
                _save_draft(preview, subject, body)
                del st.session_state[preview_key]
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.rerun()

        if return_to_queue.button("Trả lại hàng chờ", key=f"return_{preview.draft_id}"):
            try:
                _return_to_queue(preview)
                del st.session_state[preview_key]
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.rerun()


@st.fragment(run_every=PENDING_STATUS_REFRESH_SECONDS)
def main() -> None:
    inject_app_css()
    st.markdown(
        page_header_html(
            "Human Review Workspace",
            "Cần chuyên viên xử lý",
            "Trung tâm kiểm soát con người — Xem xét và xử lý các email vượt thẩm quyền, ngoài quy chế hoặc cần phê duyệt.",
        ),
        unsafe_allow_html=True,
    )

    cases = _queue_cases()
    previews = _preview_drafts()

    if not cases and not previews:
        st.markdown(
            empty_state_card_html(
                "🎉",
                "Hàng chờ hiện đang trống",
                "Không có email nào đang chờ chuyên viên quyết định hoặc chờ duyệt gửi.",
            ),
            unsafe_allow_html=True,
        )
        return

    col_queue, col_workspace = st.columns([3.5, 7.5], gap="large")

    selected_case = None
    selected_preview = None

    with col_queue:
        if cases:
            st.markdown('<div class="ex-card-title">📋 Yêu cầu cần quyết định</div>', unsafe_allow_html=True)
            search_query = st.text_input(
                "Tìm kiếm yêu cầu",
                placeholder="Tìm tiêu đề, người gửi...",
                label_visibility="collapsed",
                key="search_cases_queue",
            ).strip().lower()

            filtered_cases = cases
            if search_query:
                filtered_cases = tuple(
                    c for c in filtered_cases
                    if search_query in c.subject.lower() or search_query in c.sender.lower() or search_query in c.case_id.lower()
                )

            if not filtered_cases:
                st.caption("Không có yêu cầu nào khớp với tìm kiếm.")
                selected_case = cases[0]
            else:
                case_id = st.selectbox(
                    "Email cần quyết định",
                    [c.case_id for c in filtered_cases],
                    format_func=lambda cid: next(
                        f"{c.subject} · {c.sender}"
                        for c in filtered_cases
                        if c.case_id == cid
                    ),
                    label_visibility="collapsed",
                    key="selected_case_id_select",
                )
                selected_case = next((c for c in filtered_cases if c.case_id == case_id), filtered_cases[0])

        if previews:
            if cases:
                st.markdown("<hr style='margin: 16px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
            st.markdown('<div class="ex-card-title">📬 Bản nháp chờ duyệt gửi</div>', unsafe_allow_html=True)
            draft_id = st.selectbox(
                "Phản hồi chờ duyệt gửi",
                [p.draft_id for p in previews],
                format_func=lambda did: next(
                    f"{p.subject} ({'Đạt căn cứ' if p.grounded else 'Chưa đạt'})"
                    for p in previews
                    if p.draft_id == did
                ),
                label_visibility="collapsed",
                key="selected_draft_id_select",
            )
            selected_preview = next((p for p in previews if p.draft_id == draft_id), previews[0])

    with col_workspace:
        if selected_case:
            record = _open_decision(selected_case.case_id)
            _render_card(selected_case)
            _render_decision_form(selected_case, record)

        if selected_preview:
            if selected_case:
                st.divider()
            _render_preview(selected_preview)


main()
