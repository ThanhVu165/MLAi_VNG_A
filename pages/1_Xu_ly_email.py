"""Trang tiếp nhận email bằng một đường xử lý chung."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.parse import quote

import streamlit as st

from corpus.api import get_chunk
from core.pipeline import process_case
from core.types import CaseInput, Decision, PipelineResult


logger = logging.getLogger(__name__)
INBOX_PATH = Path("data/seed_inbox.json")
PASTE_SENDER = "student@mo-phong.local"
PASTE_SUBJECT = "Email sinh viên được dán"
UI_ACTOR = "HUMAN:demo"
STEP_NAMES = tuple(f"R{step}" for step in range(1, 14))


@dataclass(frozen=True)
class InboxEmail:
    external_id: str
    sender: str
    subject: str
    body: str


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
        if item.get("is_synthetic") is True and all(isinstance(value, str) for value in values):
            email_id, sender, subject, body = values
            emails.append(InboxEmail(str(email_id), str(sender), str(subject), str(body)))
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


def render_result(result: PipelineResult, elapsed_ms: int) -> None:
    """Hiển thị kết quả có căn cứ và đường dẫn sang audit của case."""
    st.success("Đã xử lý email.")
    render_decision(result)
    st.write(f"Thời gian xử lý: {elapsed_ms} ms")
    st.write(f"Mã case: {result.case_id} · Trạng thái: {result.status}")
    st.write(f"Phiên bản corpus: {result.corpus_version}")
    render_draft(result)
    render_citations(result)
    audit_url = f"/Nhat_ky_kiem_toan?case_id={quote(result.case_id)}"
    st.link_button("Mở nhật ký kiểm toán của case", audit_url)
    with st.expander("Thời gian theo bước R1–R13"):
        for step in STEP_NAMES:
            st.write(f"{step}: {result.step_latencies_ms.get(step, 0)} ms")


def paste_input(body: str) -> CaseInput:
    return CaseInput(
        sender=PASTE_SENDER,
        subject=PASTE_SUBJECT,
        body=body,
        received_at=datetime.now(timezone.utc),
        channel="paste",
    )


def inbox_input(email: InboxEmail) -> CaseInput:
    return CaseInput(
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        received_at=datetime.now(timezone.utc),
        channel="inbox",
        external_id=email.external_id,
    )


def main() -> None:
    st.title("Xử lý email")
    st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
    paste_tab, inbox_tab = st.tabs(("Dán nội dung email", "Hộp thư mô phỏng"))
    with paste_tab:
        body = st.text_area("Nội dung email", placeholder="Dán toàn bộ nội dung email vào đây.")
        if st.button("Xử lý email đã dán", key="process_paste"):
            if not body.strip():
                st.error("Chưa có nội dung email. Hãy dán email rồi bấm xử lý lại.")
            else:
                render_result(*run_case(paste_input(body)))
    with inbox_tab:
        emails = load_inbox()
        if not emails:
            st.error("Không có email mô phỏng. Hãy kiểm tra tệp data/seed_inbox.json.")
            return
        selected = st.selectbox(
            "Chọn email mô phỏng", emails, format_func=lambda email: email.subject
        )
        st.caption(f"Từ: {selected.sender}\n\n{selected.body}")
        if st.button("Xử lý email mô phỏng", key="process_inbox"):
            render_result(*run_case(inbox_input(selected)))


main()
