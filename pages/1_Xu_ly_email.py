"""Trang tiếp nhận email bằng một đường xử lý chung."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from sqlite3 import Row
from time import perf_counter
from urllib.parse import quote

import streamlit as st

from core.dispatch import (
    cancel_send,
    create_correction_email,
    dispatch_due,
    escalate_from_pending,
)
from core.explain import explain_plainly
from core.pipeline import process_case
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    DraftReply,
    EscalationCard,
    EscalationType,
    PipelineResult,
)
from corpus.api import get_chunk
from infra.db import fetch_one, seconds_until, to_local
from infra.settings import PENDING_STATUS_REFRESH_SECONDS

logger = logging.getLogger(__name__)
INBOX_PATH = Path("data/seed_inbox.json")
UI_ACTOR = "HUMAN:demo"
STEP_NAMES = tuple(f"R{step}" for step in range(1, 14))
ESCALATION_TYPE_LABELS: dict[EscalationType, str] = {
    EscalationType.FACT_UNRESOLVED: "Thiếu dữ kiện",
    EscalationType.OUT_OF_POLICY: "Ngoài phạm vi quy định",
    EscalationType.AUTHORITY_REQUIRED: "Cần phê duyệt",
}


@dataclass(frozen=True)
class InboxEmail:
    external_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime


def load_inbox() -> tuple[InboxEmail, ...]:
    """Đọc các email mô phỏng hợp lệ, không để dữ liệu lỗi làm hỏng trang."""
    try:
        payload: object = json.loads(INBOX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.warning("Không đọc được hộp thư mô phỏng: %s", error)
        return ()
    if not isinstance(payload, list):
        logger.warning("Hộp thư mô phỏng không phải danh sách email.")
        return ()
    emails: list[InboxEmail] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        values = (item.get("id"), item.get("sender"), item.get("subject"), item.get("body"))
        if item.get("is_synthetic") is True and all(
            isinstance(value, str) and value.strip() for value in values
        ):
            try:
                received_at = datetime.fromisoformat(item.get("received_at", ""))
                if received_at.utcoffset() is None:
                    raise ValueError("received_at thiếu múi giờ")
            except (TypeError, ValueError) as error:
                logger.warning("Bỏ qua email mô phỏng có thời điểm nhận không hợp lệ: %s", error)
                continue
            email_id, sender, subject, body = values
            emails.append(
                InboxEmail(str(email_id), str(sender), str(subject), str(body), received_at)
            )
    return tuple(emails)


def run_case(case_input: CaseInput) -> tuple[PipelineResult, int]:
    """Gọi duy nhất pipeline dùng chung và đo thời gian đầu-cuối cho giao diện."""
    progress = st.progress(0, text="Đang chạy các bước R1 đến R13.")
    started_at = perf_counter()
    with st.spinner("Hệ thống đang xử lý email, vui lòng chờ."):
        result = process_case(case_input, actor=UI_ACTOR)
    elapsed_ms = round((perf_counter() - started_at) * 1_000)
    progress.progress(100, text="Đã hoàn tất các bước R1 đến R13.")
    return result, elapsed_ms


def render_decision(result: PipelineResult) -> None:
    """Hiển thị huy hiệu quyết định và lý do từ Policy Engine."""
    if result.decision.decision is Decision.AUTO_REPLY:
        st.success("Trả lời tự động")
    elif result.decision.decision is Decision.ESCALATE:
        st.warning("Chuyển tiếp chuyên viên")
    else:
        st.error("Dữ liệu đầu vào chưa hợp lệ")
    st.write(f"Quy tắc áp dụng: {result.decision.rule_id}")
    st.write(f"Lý do: {result.decision.reason}")


def render_draft(result: PipelineResult) -> None:
    """Hiển thị nguyên văn bản nháp khi pipeline tạo được email."""
    if result.draft is None:
        st.info("Chưa có email nháp vì case cần chuyên viên xử lý tiếp.")
        return
    st.subheader("Nội dung email nháp")
    st.write(f"Tiêu đề: {result.draft.subject}")
    st.text(result.draft.body)


def render_citations(result: PipelineResult) -> None:
    """Hiển thị mỗi trích dẫn cùng breadcrumb và nguyên văn điều khoản."""
    citation_ids = (
        result.draft.citations if result.draft is not None else result.decision.evidence_ids
    )
    if not citation_ids:
        st.info("Case này không có trích dẫn quy định để tự động trả lời.")
        return
    st.subheader("Căn cứ quy định")
    for citation_id in citation_ids:
        chunk = get_chunk(citation_id)
        if chunk is None:
            st.warning(f"Không mở được trích dẫn {citation_id} trong corpus đang hiệu lực.")
            continue
        with st.expander(f"{chunk.breadcrumb} · {chunk.chunk_id}"):
            st.write(chunk.text)


def render_escalation_card(card: EscalationCard, case_id: str) -> None:
    """Hiển thị đủ thông tin để chuyên viên chọn phương án chuyển tiếp."""
    st.subheader("Thẻ chuyển tiếp chuyên viên")

    st.markdown("#### Tóm tắt")
    st.write(card.summary)
    st.caption(f"Loại chuyển tiếp: {ESCALATION_TYPE_LABELS[card.escalation_type]}")

    st.markdown("#### Dữ kiện")
    if card.facts:
        for fact in card.facts:
            st.write(f"• {fact}")
    else:
        st.info("Chưa có dữ kiện đã xác nhận; hãy dựa vào căn cứ và câu hỏi bên dưới.")

    st.markdown("#### Căn cứ")
    if card.basis:
        for breadcrumb, citation in card.basis:
            with st.expander(breadcrumb):
                st.write(citation)
    else:
        st.info("Chưa có căn cứ quy định đang hiệu lực cho case này.")

    st.markdown("#### Câu hỏi")
    st.write(card.question)
    if card.options:
        st.radio("Chọn một phương án", card.options, key=f"escalation_choice_{case_id}")
    else:
        st.error("Thẻ chưa có phương án. Hãy mở nhật ký kiểm toán để xử lý case này an toàn.")

    if card.partial_draft is not None:
        st.markdown("#### Phần A đã soạn sẵn")
        st.write(f"Tiêu đề: {card.partial_draft.subject}")
        st.text(card.partial_draft.body)


def render_plain_explanation(case_id: str, key: str) -> None:
    """Cho phép mở phần giải thích đơn giản và lưu audit qua API dùng chung."""
    if st.button("Giải thích cho người không chuyên", key=key):
        try:
            explanation = explain_plainly(case_id)
        except ValueError:
            st.error("Chưa thể tạo giải thích cho case này. Hãy xử lý email rồi thử lại.")
        else:
            with st.container(border=True):
                st.subheader("Vì sao hệ thống xử lý như vậy?")
                st.write(explanation)


def _case_row(case_id: str) -> Row | None:
    row = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if row is not None and row["status"] == CaseStatus.PENDING_SEND:
        dispatch_due(case_id)
        row = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    return row


def _correction_draft(case_id: str) -> DraftReply | None:
    row = fetch_one(
        """
        SELECT subject, body, citations_json, grounded, guard_failures_json
        FROM drafts WHERE case_id = ? ORDER BY rowid DESC LIMIT 1
        """,
        (case_id,),
    )
    if row is None:
        return None
    try:
        citations = json.loads(row["citations_json"] or "[]")
        failures = json.loads(row["guard_failures_json"] or "[]")
    except json.JSONDecodeError as error:
        logger.warning("Không đọc được bản nháp Correction Email: %s", error)
        return None
    if not isinstance(citations, list) or not isinstance(failures, list):
        return None
    return DraftReply(
        subject=row["subject"] or "Correction Email",
        body=row["body"] or "",
        citations=[citation for citation in citations if isinstance(citation, str)],
        grounded=bool(row["grounded"]),
        guard_failures=[failure for failure in failures if isinstance(failure, str)],
    )


def _render_correction(case_id: str) -> None:
    draft = _correction_draft(case_id)
    st.subheader("Tạo Correction Email")
    if draft is None:
        st.error("Không có bản nháp gốc để tạo Correction Email an toàn.")
        return
    subject = st.text_input(
        "Tiêu đề Correction Email", value=draft.subject, key=f"correction_subject_{case_id}"
    )
    body = st.text_area(
        "Nội dung Correction Email", value=draft.body, key=f"correction_body_{case_id}"
    )
    if st.button("Tạo Correction Email", key=f"create_correction_{case_id}"):
        if not subject.strip() or not body.strip():
            st.error("Correction Email cần có tiêu đề và nội dung.")
            return
        correction_id = create_correction_email(
            case_id,
            actor=UI_ACTOR,
            draft=DraftReply(subject, body, draft.citations, draft.grounded, draft.guard_failures),
        )
        st.success(f"Đã tạo Correction Email {correction_id} để chờ duyệt.")


@st.fragment(run_every=PENDING_STATUS_REFRESH_SECONDS)
def render_delivery_controls(case_id: str) -> None:
    """Hiển thị và cập nhật vòng đời gửi từ trạng thái được lưu trong DB."""
    row = _case_row(case_id)
    if row is None:
        st.error("Không tìm thấy case để kiểm tra trạng thái gửi.")
        return
    status = CaseStatus(row["status"])
    st.subheader("Trạng thái gửi mô phỏng")
    if status is CaseStatus.PENDING_SEND:
        deadline = row["send_deadline"]
        if not isinstance(deadline, str):
            st.error("Case chờ gửi thiếu mốc hết hạn trong DB.")
            return
        st.metric("Thời gian còn lại", f"{seconds_until(deadline)} giây")
        st.caption(f"Mốc hết hạn từ DB: {to_local(deadline)}")
        reason = st.text_input("Lý do can thiệp", key=f"send_reason_{case_id}")
        cancel_column, escalate_column = st.columns(2)
        if cancel_column.button("Hủy gửi", key=f"cancel_send_{case_id}"):
            if not reason.strip():
                st.error("Hãy ghi lý do trước khi hủy gửi.")
            else:
                cancel_send(case_id, UI_ACTOR, reason.strip())
                st.rerun(scope="fragment")
        if escalate_column.button("Chuyển cho người", key=f"escalate_send_{case_id}"):
            if not reason.strip():
                st.error("Hãy ghi lý do trước khi chuyển cho người.")
            else:
                escalate_from_pending(case_id, actor=UI_ACTOR, reason=reason.strip())
                st.rerun(scope="fragment")
    elif status is CaseStatus.SENT:
        st.success("Đã gửi (mô phỏng)")
        _render_correction(case_id)
    else:
        st.info(f"Case đang ở trạng thái {status}. Các nút gửi đã khóa.")


def render_result(result: PipelineResult, elapsed_ms: int) -> None:
    """Hiển thị kết quả có căn cứ và đường dẫn sang audit của case."""
    st.success("Đã xử lý email.")
    render_decision(result)
    st.write(f"Thời gian xử lý: {elapsed_ms} ms")
    st.write(f"Mã case: {result.case_id} · Trạng thái: {result.status}")
    st.write(f"Phiên bản corpus: {result.corpus_version}")
    render_draft(result)
    if result.card is None:
        render_citations(result)
    else:
        render_escalation_card(result.card, result.case_id)
    render_plain_explanation(result.case_id, f"explain_result_{result.case_id}")
    audit_url = f"/Nhat_ky_kiem_toan?case_id={quote(result.case_id)}"
    st.link_button("Mở nhật ký kiểm toán của case", audit_url)
    with st.expander("Thời gian theo bước R1–R13"):
        for step in STEP_NAMES:
            st.write(f"{step}: {result.step_latencies_ms.get(step, 0)} ms")


def paste_input(sender: str, subject: str, body: str) -> CaseInput:
    if not all(value.strip() for value in (sender, subject, body)):
        raise ValueError("Hãy nhập đủ email người gửi, tiêu đề và nội dung trước khi xử lý.")
    return CaseInput(
        sender=sender,
        subject=subject,
        body=body,
        received_at=datetime.now(timezone.utc),
        channel="paste",
    )


def inbox_input(email: InboxEmail) -> CaseInput:
    return CaseInput(
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        received_at=email.received_at,
        channel="inbox",
        external_id=email.external_id,
    )


def main() -> None:
    st.title("Xử lý email")
    st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
    paste_tab, inbox_tab = st.tabs(("Dán nội dung email", "Hộp thư mô phỏng"))
    with paste_tab:
        home_input = st.session_state.pop("home_email_to_process", None)
        if home_input:
            st.session_state["paste_sender"] = home_input.sender
            st.session_state["paste_subject"] = home_input.subject
            st.session_state["paste_body"] = home_input.body
        sender = st.text_input("Email người gửi", key="paste_sender")
        subject = st.text_input("Tiêu đề", key="paste_subject")
        body = st.text_area(
            "Nội dung email",
            placeholder="Dán toàn bộ nội dung email vào đây.",
            key="paste_body",
        )
        if home_input and all(
            value.strip() for value in (home_input.sender, home_input.subject, home_input.body)
        ):
            result, elapsed_ms = run_case(home_input)
            st.session_state["active_case_id"] = result.case_id
            render_result(result, elapsed_ms)
        if st.button("Xử lý email đã dán", key="process_paste"):
            if not all(value.strip() for value in (sender, subject, body)):
                st.error("Hãy nhập đủ email người gửi, tiêu đề và nội dung trước khi xử lý.")
            else:
                result, elapsed_ms = run_case(paste_input(sender, subject, body))
                st.session_state["active_case_id"] = result.case_id
                render_result(result, elapsed_ms)
    with inbox_tab:
        emails = load_inbox()
        if not emails:
            st.error("Không có email mô phỏng. Hãy kiểm tra tệp data/seed_inbox.json.")
            return
        selected = st.selectbox(
            "Chọn email mô phỏng", emails, format_func=lambda email: email.subject
        )
        st.caption(
            f"Từ: {selected.sender}\n\nNhận lúc: {to_local(selected.received_at.isoformat())}"
            f"\n\n{selected.body}"
        )
        if st.button("Xử lý email mô phỏng", key="process_inbox"):
            result, elapsed_ms = run_case(inbox_input(selected))
            st.session_state["active_case_id"] = result.case_id
            render_result(result, elapsed_ms)
    query_case_id = st.query_params.get("case_id")
    active_case_id = st.session_state.get("active_case_id", query_case_id)
    if isinstance(active_case_id, str):
        render_delivery_controls(active_case_id)


main()
