"""Tiếp nhận email, xem kết quả bền vững và can thiệp lịch gửi."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from core.controls import is_automation_paused
from core.dispatch import cancel_send, create_correction_email, escalate_from_pending
from core.explain import explain_plainly
from core.pipeline import load_result
from core.types import CaseInput, CaseStatus, Decision, DraftReply, PipelineResult
from core.worker import submit_case
from corpus.api import get_chunk
from infra.db import fetch_all, fetch_one, seconds_until
from infra.settings import PENDING_STATUS_REFRESH_SECONDS
from ui.presentation import local_time, readable_text, reply_text, status_label

logger = logging.getLogger(__name__)
INBOX_PATH = Path("data/seed_inbox.json")
UI_ACTOR = "HUMAN:local"


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


def paste_input(sender: str, subject: str, body: str) -> CaseInput:
    if not all(value.strip() for value in (sender, subject, body)):
        raise ValueError("Hãy nhập đủ email người gửi, tiêu đề và nội dung trước khi xử lý.")
    return CaseInput(sender, subject, body, datetime.now(timezone.utc), "paste")


def inbox_input(email: InboxEmail) -> CaseInput:
    return CaseInput(
        email.sender, email.subject, email.body, email.received_at, "inbox", email.external_id
    )


def _submit(inp: CaseInput) -> None:
    case_id = submit_case(inp, actor=UI_ACTOR)
    st.session_state["active_case_id"] = case_id
    st.query_params["case_id"] = case_id


def render_result(result: PipelineResult) -> None:
    """Nội dung và căn cứ; trạng thái gửi được đọc riêng từ DB."""
    if result.decision.decision in (Decision.ERROR, Decision.INVALID_INPUT):
        st.error(readable_text(result.decision.reason))
        return
    st.write(readable_text(result.decision.reason))
    elapsed = (result.finished_at - result.started_at).total_seconds()
    st.caption(f"Xử lý trong {elapsed:.1f} giây · {local_time(result.finished_at)}")
    draft = result.draft or (result.card.partial_draft if result.card else None)
    if draft:
        waiting = result.status in (CaseStatus.AWAITING_HUMAN, CaseStatus.HUMAN_DECIDED)
        st.subheader("Phần trả lời đã chuẩn bị, chưa gửi" if waiting else "Nội dung phản hồi")
        st.write(f"**{draft.subject}**")
        st.text(reply_text(draft.body, draft.citations))
    if result.card:
        st.subheader(
            "Chuyên viên cần quyết định"
            if result.status is CaseStatus.AWAITING_HUMAN
            else "Nội dung đã chuyển cho chuyên viên"
        )
        st.write(result.card.question)
        if result.card.facts:
            with st.expander("Thông tin đã có"):
                for fact in result.card.facts:
                    st.write(readable_text(fact))
        st.page_link("pages/2_Hang_cho_duyet.py", label="Mở mục Cần chuyên viên xử lý")
    citation_ids = draft.citations if draft else result.decision.evidence_ids
    if citation_ids:
        st.subheader("Căn cứ")
        snapshots = (
            {chunk.chunk_id: chunk for chunk in result.evidence.chunks} if result.evidence else {}
        )
        for index, citation_id in enumerate(citation_ids, start=1):
            chunk = snapshots.get(citation_id) or get_chunk(citation_id)
            if chunk:
                with st.expander(f"[{index}] {chunk.breadcrumb}"):
                    st.write(chunk.text)
            else:
                st.warning(f"Căn cứ [{index}] không còn trong các quy định đang áp dụng.")
    elif result.card and result.card.basis:
        with st.expander("Căn cứ đã chuyển cho chuyên viên"):
            for breadcrumb, text in result.card.basis:
                st.write(breadcrumb)
                st.write(text)


def _render_correction(case_id: str) -> None:
    row = fetch_one(
        "SELECT * FROM drafts WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
    )
    if row is None:
        return
    with st.expander("Cần đính chính email đã gửi?"):
        citations = json.loads(row["citations_json"] or "[]")
        subject = st.text_input(
            "Tiêu đề thư đính chính", value=row["subject"], key=f"correction_subject_{case_id}"
        )
        body = st.text_area(
            "Nội dung thư đính chính",
            value=reply_text(row["body"], citations),
            key=f"correction_body_{case_id}",
        )
        st.caption("Thư đính chính phải được kiểm tra và chuyên viên duyệt trước khi gửi.")
        if st.button("Tạo thư đính chính", key=f"create_correction_{case_id}"):
            if not subject.strip() or not body.strip():
                st.error("Hãy nhập tiêu đề và nội dung thư đính chính.")
                return
            for index, citation in enumerate(citations, start=1):
                body = body.replace(f"[{index}]", f"[{citation}]")
            try:
                create_correction_email(
                    case_id, actor=UI_ACTOR, draft=DraftReply(subject, body, citations, False, [])
                )
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.success("Đã tạo thư đính chính. Mở mục Cần chuyên viên xử lý để duyệt nội dung.")


@st.fragment(run_every=PENDING_STATUS_REFRESH_SECONDS)
def render_saved_case(case_id: str) -> None:
    row = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if row is None:
        st.warning("Không tìm thấy email này trong lịch sử.")
        return
    st.divider()
    st.subheader(row["subject"])
    status = CaseStatus(row["status"])
    if status in (CaseStatus.ERROR, CaseStatus.INVALID_INPUT):
        st.error(status_label(status))
    elif status in (
        CaseStatus.AWAITING_HUMAN,
        CaseStatus.NEEDS_RECHECK,
        CaseStatus.PENDING_APPROVAL,
    ):
        st.warning(status_label(status))
    elif status in (CaseStatus.RECEIVED, CaseStatus.PROCESSING):
        st.info("Email đã được lưu. Hệ thống đang xử lý; bạn có thể chuyển trang.")
    else:
        st.success(status_label(status))
    with st.expander("Email đã tiếp nhận"):
        st.caption(f"Từ {row['sender']} · Nhận lúc {local_time(row['received_at'])}")
        st.text(row["body_raw"])
    result = load_result(case_id)
    if result:
        render_result(result)
        explanation_key = f"explanation_{case_id}_{status}_{result.decision.reason}"
        if st.button("Vì sao hệ thống xử lý như vậy?", key=f"explain_{case_id}"):
            st.session_state[explanation_key] = readable_text(explain_plainly(case_id))
        if explanation := st.session_state.get(explanation_key):
            st.info(explanation)
    elif status is CaseStatus.ERROR:
        st.write("Lần xử lý trước bị gián đoạn. Chưa có phản hồi nào được gửi; bạn có thể thử lại.")
    elif status not in (CaseStatus.RECEIVED, CaseStatus.PROCESSING):
        st.info(
            "Email cũ chưa có bản kết quả đầy đủ. Nội dung và các thao tác vẫn còn trong lịch sử."
        )
    if status is CaseStatus.ERROR:
        if st.button("Thử xử lý lại", key=f"retry_{case_id}"):
            from core.worker import retry_case

            try:
                new_id = retry_case(case_id, actor=UI_ACTOR)
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.session_state["active_case_id"] = new_id
                st.query_params["case_id"] = new_id
                st.rerun()
    if status is CaseStatus.PENDING_SEND:
        if is_automation_paused():
            st.info("Đang tạm dừng gửi tự động. Phản hồi vẫn được giữ để bạn kiểm tra.")
        else:
            st.caption(
                f"Sẽ gửi mô phỏng sau {seconds_until(row['send_deadline'])} giây. Không cần giữ trang này mở."
            )
        reason = st.text_input("Lý do can thiệp", key=f"send_reason_{case_id}")
        left, right = st.columns(2)
        if left.button("Hủy gửi", key=f"cancel_send_{case_id}", disabled=not reason.strip()):
            try:
                cancel_send(case_id, UI_ACTOR, reason.strip())
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.rerun()
        if right.button(
            "Chuyển cho chuyên viên", key=f"escalate_send_{case_id}", disabled=not reason.strip()
        ):
            try:
                escalate_from_pending(case_id, actor=UI_ACTOR, reason=reason.strip())
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.rerun()
    elif status is CaseStatus.SENT:
        _render_correction(case_id)
    st.link_button("Xem lịch sử xử lý email", f"/Nhat_ky_kiem_toan?case_id={quote(case_id)}")


def main() -> None:
    st.title("Email")
    st.caption(
        "Nhập nguyên email cần xử lý. Hệ thống sẽ đọc yêu cầu, tìm quy định và chuẩn bị phản hồi."
    )
    st.caption(
        "Chưa kết nối hộp thư: tiếp nhận bằng biểu mẫu; thao tác gửi được ghi nhận mô phỏng, không gửi ra ngoài."
    )
    with st.form("email_form"):
        sender = st.text_input("Email người gửi", key="paste_sender")
        subject = st.text_input("Tiêu đề", key="paste_subject")
        body = st.text_area("Nội dung email", height=160, key="paste_body")
        submitted = st.form_submit_button("Xử lý email", type="primary")
    if submitted:
        try:
            _submit(paste_input(sender, subject, body))
        except (ValueError, RuntimeError) as error:
            st.error(readable_text(str(error)))
    with st.expander("Thử bằng email minh họa"):
        emails = load_inbox()
        if emails:
            selected = st.selectbox("Chọn email", emails, format_func=lambda email: email.subject)
            st.caption(f"Từ {selected.sender} · {local_time(selected.received_at)}")
            st.text(selected.body)
            if st.button("Xử lý email minh họa", key="process_inbox"):
                try:
                    _submit(inbox_input(selected))
                except (ValueError, RuntimeError) as error:
                    st.error(readable_text(str(error)))
        else:
            st.info("Không có email minh họa. Bạn vẫn có thể nhập email phía trên.")
    recent = fetch_all(
        "SELECT case_id, subject, status, received_at FROM cases ORDER BY rowid DESC LIMIT 30"
    )
    with st.expander("Mở lại email gần đây"):
        if recent:
            selected_id = st.selectbox(
                "Email đã lưu",
                [row["case_id"] for row in recent],
                format_func=lambda value: next(
                    f"{row['subject']} · {status_label(row['status'])} · {local_time(row['received_at'])}"
                    for row in recent
                    if row["case_id"] == value
                ),
            )
            if st.button("Mở kết quả đã lưu"):
                st.session_state["active_case_id"] = selected_id
                st.query_params["case_id"] = selected_id
        else:
            st.info("Chưa có email đã lưu. Nhập email phía trên để bắt đầu.")
    case_id = st.query_params.get("case_id") or st.session_state.get("active_case_id")
    if isinstance(case_id, str):
        render_saved_case(case_id)


main()
