"""Tiếp nhận email, xem kết quả bền vững và can thiệp lịch gửi."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote

import streamlit as st

from core.controls import is_automation_paused
from core.dispatch import cancel_send, create_correction_email, escalate_from_pending
from core.explain import explain_plainly
from core.pipeline import load_result, process_case
from core.types import CaseInput, CaseStatus, Decision, DraftReply
from core.worker import submit_case
from corpus.api import get_chunk
from infra.db import fetch_all, fetch_one, seconds_until
from infra.demo_access import (
    authorize_case_input,
    canonical_demo_input,
    canonical_demo_inputs,
    case_is_owned,
    is_restricted_demo,
    validate_public_text,
)
from infra.settings import PENDING_STATUS_REFRESH_SECONDS
from ui.presentation import (
    decision_badge_html,
    escape_html,
    inject_app_css,
    local_time,
    page_header_html,
    readable_text,
    reply_text,
    status_badge_html,
    status_label,
    stop_reason_badge_html,
)

logger = logging.getLogger(__name__)
INBOX_PATH = Path("data/seed_inbox.json")
UI_ACTOR = "HUMAN:local"

# 3 email mẫu đại diện cho 3 luồng xử lý canonical
SAMPLES = [
    {
        "id": item.sample_id,
        "tag": item.tag,
        "desc": item.description,
        "sender": item.sender,
        "subject": item.subject,
        "body": item.body,
    }
    for item in canonical_demo_inputs()
]


class InboxEmail(NamedTuple):
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
    validate_public_text(sender, subject, body)
    canonical = canonical_demo_input(sender, subject, body)
    if canonical is not None:
        return CaseInput(
            canonical.sender,
            canonical.subject,
            canonical.body,
            datetime.fromisoformat(canonical.received_at),
            "paste",
        )
    return CaseInput(sender, subject, body, datetime.now(timezone.utc), "paste")


def inbox_input(email: InboxEmail) -> CaseInput:
    return CaseInput(
        email.sender, email.subject, email.body, email.received_at, "inbox", email.external_id
    )


def _submit(inp: CaseInput) -> None:
    if is_restricted_demo():
        authorize_case_input(
            sender=inp.sender,
            subject=inp.subject,
            body=inp.body,
            received_at=inp.received_at,
            channel=inp.channel,
            external_id=inp.external_id,
        )
        result = process_case(inp, actor="SYSTEM")
        if result.decision.decision is Decision.ERROR and not result.corpus_version:
            raise RuntimeError(result.decision.reason)
        case_id = result.case_id
    else:
        case_id = submit_case(inp, actor=UI_ACTOR)
    owned = _owned_case_ids()
    if case_id not in owned:
        owned.append(case_id)
    st.session_state["active_case_id"] = case_id
    st.query_params["case_id"] = case_id


def _owned_case_ids() -> list[str]:
    values = st.session_state.setdefault("restricted_demo_case_ids", [])
    return values if isinstance(values, list) else []


def _render_first_time_guidance() -> None:
    """Giải thích đúng khả năng của từng mode trước khi người dùng nhập email."""
    if is_restricted_demo():
        st.info(
            "Restricted DEMO đang chạy replay offline với 3 email mẫu synthetic canonical. "
            "Hãy chọn một mẫu rồi nhấn **Xử lý email**. Email tự nhập mới vẫn hiển thị để "
            "minh họa giao diện nhưng không được lưu hoặc xử lý ở chế độ công khai; hệ thống "
            "không gọi provider LIVE."
        )
    else:
        st.info(
            "Chọn một email mẫu để thử nhanh, hoặc nhập email đầy đủ nếu môi trường private "
            "đã được cấp quyền xử lý."
        )

    st.markdown(
        """
        **Bắt đầu trong 5 bước**

        1. Chọn một email mẫu phía dưới để điền nội dung.
        2. Nhấn **Xử lý email**.
        3. Đọc quyết định, lý do và căn cứ được hiển thị.
        4. Mở **Verify** để chạy bộ kiểm thử được phép.
        5. Sau khi có kết quả, chỉ mở **Nhật ký kiểm toán** của ca thuộc cùng phiên khi nút điều hướng hợp lệ xuất hiện.
        """
    )


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


def _render_stepper(current_step: int) -> str:
    """Render Stepper 5 bước theo đúng mockup 04_email_entry_BASE.png."""
    steps = [
        ("1", "Tiếp nhận", "Nhận email và trích xuất thông tin"),
        ("2", "Đối chiếu căn cứ", "Tìm quy định liên quan"),
        ("3", "Ra quyết định", "AUTO_REPLY hoặc ESCALATE"),
        ("4", "Soạn phản hồi / Chuyển người", "Tạo email hoặc chuyển chuyên viên"),
        ("5", "Kết quả", "Hiển thị quyết định và căn cứ"),
    ]
    items_html = []
    for idx, (num, title, desc) in enumerate(steps, start=1):
        if idx < current_step:
            cls = "ex-step ex-step-done"
            badge = "✓"
        elif idx == current_step:
            cls = "ex-step ex-step-active"
            badge = num
        else:
            cls = "ex-step"
            badge = num
        items_html.append(
            f'<div class="{cls}">'
            f'<div class="ex-step-num">{badge}</div>'
            f'<div class="ex-step-title">{title}</div>'
            f'<div class="ex-step-desc">{desc}</div>'
            f"</div>"
        )
    return f'<div class="ex-stepper">{"".join(items_html)}</div>'


@st.fragment(run_every=PENDING_STATUS_REFRESH_SECONDS)
def render_saved_case(case_id: str) -> None:
    if not case_is_owned(case_id, _owned_case_ids()):
        st.warning("Bạn không có quyền xem email này trong phiên hiện tại.")
        return
    row = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if row is None:
        st.warning("Không tìm thấy email này trong lịch sử.")
        return

    status = CaseStatus(row["status"])
    result = load_result(case_id)

    # 1. Trạng thái lỗi hoặc input không hợp lệ
    if status in (CaseStatus.ERROR, CaseStatus.INVALID_INPUT):
        st.error(status_label(status))
        if status is CaseStatus.ERROR:
            st.info("Lần xử lý trước bị gián đoạn. Chưa có phản hồi nào được gửi.")
            if not is_restricted_demo() and st.button("🔄 Thử xử lý lại", key=f"retry_{case_id}"):
                from core.worker import retry_case

                try:
                    new_id = retry_case(case_id, actor=UI_ACTOR)
                except ValueError as error:
                    st.error(readable_text(str(error)))
                else:
                    st.session_state["active_case_id"] = new_id
                    st.query_params["case_id"] = new_id
                    st.rerun()
        return

    # 2. Trạng thái đang xử lý nền
    if status in (CaseStatus.RECEIVED, CaseStatus.PROCESSING):
        st.info("Email đã được lưu vào hệ thống. Đang tiến hành phân tích và đối chiếu quy định...")
        return

    # 3. Trạng thái đã có kết quả (AUTO_REPLY hoặc ESCALATE)
    if not result:
        st.info(
            "Email cũ chưa có bản kết quả đầy đủ. Nội dung và các thao tác vẫn còn trong lịch sử."
        )
        return

    decision = result.decision.decision
    elapsed = (result.finished_at - result.started_at).total_seconds()
    finished_time = local_time(result.finished_at)

    # ==================== A. RESULT BANNER ====================
    if decision == Decision.AUTO_REPLY:
        # Thông điệp trạng thái gửi thật từ DB
        if status == CaseStatus.SENT:
            exec_note = "✅ <strong>Đã phát hành:</strong> Đã gửi phản hồi mô phỏng tới người gửi."
        elif status == CaseStatus.PENDING_SEND:
            sec_left = seconds_until(row["send_deadline"])
            exec_note = f"⏳ <strong>Chưa gửi (Đang đếm ngược):</strong> Sẽ tự động gửi sau {sec_left} giây nếu không có can thiệp hủy."
        elif status in (CaseStatus.AWAITING_HUMAN, CaseStatus.PENDING_APPROVAL):
            exec_note = "👤 <strong>Chưa gửi:</strong> Bản thảo đã chuẩn bị, đang chờ chuyên viên phê duyệt trước khi phát hành."
        else:
            exec_note = f"ℹ️ <strong>Trạng thái:</strong> {status_label(status)}."

        banner_html = (
            f'<div class="ex-card" style="border-top: 3px solid #10B981; margin-bottom: 14px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
            f'<div style="display: flex; gap: 12px; align-items: center;">'
            f'<div style="width: 38px; height: 38px; border-radius: 50%; background: #ECFDF5; border: 2px solid #10B981; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #10B981; font-weight: 700;">✓</div>'
            f"<div>"
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'{decision_badge_html("AUTO_REPLY")} {status_badge_html(status.value)}'
            f"</div>"
            f'<div style="font-size: 15px; font-weight: 700; color: #065F46; margin-top: 2px;">'
            f"Đã xử lý — Phản hồi tự động"
            f"</div>"
            f'<div style="font-size: 13.5px; color: #047857; margin-top: 2px; font-weight: 500;">'
            f"Có đủ căn cứ để tự động phản hồi."
            f"</div>"
            f"</div>"
            f"</div>"
            f'<div style="text-align: right; font-size: 12px; color: #64748B;">'
            f"<div>📅 Xử lý lúc {finished_time}</div>"
            f"<div>⏱️ Thời gian: {elapsed:.1f}s</div>"
            f"</div>"
            f"</div>"
            f'<div style="margin-top: 10px; font-size: 12.5px; color: #334155; background: #F8FAFC; border: 1px solid #E2E8F0; padding: 7px 12px; border-radius: 6px;">'
            f"{exec_note}"
            f"</div>"
            f"</div>"
        )
        st.markdown(banner_html, unsafe_allow_html=True)
    else:
        # Nhánh ESCALATE
        esc_row = fetch_one("SELECT * FROM escalations WHERE case_id = ?", (case_id,))
        esc_type = (
            esc_row["escalation_type"]
            if esc_row
            else (result.decision.rule_id or "FACT_UNRESOLVED")
        )

        banner_html = (
            f'<div class="ex-card" style="border-top: 3px solid #D97706; margin-bottom: 14px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
            f'<div style="display: flex; gap: 12px; align-items: center;">'
            f'<div style="width: 38px; height: 38px; border-radius: 50%; background: #FFFBEB; border: 2px solid #D97706; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #D97706; font-weight: 700;">⚠️</div>'
            f"<div>"
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'{decision_badge_html("ESCALATE")} {stop_reason_badge_html(esc_type)} {status_badge_html(status.value)}'
            f"</div>"
            f'<div style="font-size: 15px; font-weight: 700; color: #92400E; margin-top: 2px;">'
            f"Cần chuyên viên xem xét trước khi tiếp tục."
            f"</div>"
            f'<div style="font-size: 13.5px; color: #B45309; margin-top: 2px;">'
            f"Yêu cầu đã được chuyển vào Hàng chờ duyệt để cán bộ phòng ban xử lý."
            f"</div>"
            f"</div>"
            f"</div>"
            f'<div style="text-align: right; font-size: 12px; color: #64748B;">'
            f"<div>📅 Tiếp nhận: {finished_time}</div>"
            f"<div>⏱️ Thời gian: {elapsed:.1f}s</div>"
            f"</div>"
            f"</div>"
            f'<div style="margin-top: 10px; font-size: 13px; color: #78350F; background: #FFFDF5; border: 1px solid #FDE68A; padding: 8px 12px; border-radius: 6px;">'
            f"<strong>Lý do dừng:</strong> {escape_html(readable_text(result.decision.reason))}"
            f"</div>"
            f"</div>"
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    # ==================== B. SPLIT WORKSPACE: PHẢN HỒI VS CĂN CỨ ====================
    col_resp, col_evid = st.columns([5, 5], gap="medium")

    with col_resp:
        if decision == Decision.AUTO_REPLY:
            st.markdown(
                '<div class="ex-card-title">📝 Nội dung phản hồi (đã chuẩn bị)</div>',
                unsafe_allow_html=True,
            )
            draft = result.draft or (result.card.partial_draft if result.card else None)
            if draft:
                st.markdown(
                    f'<div style="font-size: 13.5px; font-weight: 600; color: #0F172A; margin-bottom: 6px;">'
                    f"<strong>Tiêu đề:</strong> {escape_html(draft.subject)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                formatted_body = reply_text(draft.body, draft.citations)
                st.text_area(
                    "Bản thảo phản hồi",
                    value=formatted_body,
                    height=200,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"draft_view_{case_id}",
                )

                # Nút sao chép nội dung
                if st.button("📋 Sao chép nội dung phản hồi", key=f"copy_resp_{case_id}"):
                    st.toast("Đã sao chép phản hồi!")

                # Can thiệp hủy gửi / chuyển chuyên viên nếu đang PENDING_SEND
                if status is CaseStatus.PENDING_SEND and not is_restricted_demo():
                    st.markdown(
                        "<hr style='margin: 12px 0; border-color: #E2E8F0;'>",
                        unsafe_allow_html=True,
                    )
                    if is_automation_paused():
                        st.info("Đang tạm dừng gửi tự động. Phản hồi vẫn được giữ để bạn kiểm tra.")
                    else:
                        st.caption(
                            f"Sẽ gửi mô phỏng sau {seconds_until(row['send_deadline'])} giây."
                        )
                    reason = st.text_input("Lý do can thiệp", key=f"send_reason_{case_id}")
                    if st.button(
                        "Hủy gửi",
                        key=f"cancel_send_{case_id}",
                        disabled=not reason.strip(),
                        use_container_width=True,
                    ):
                        try:
                            cancel_send(case_id, UI_ACTOR, reason.strip())
                        except ValueError as error:
                            st.error(readable_text(str(error)))
                        else:
                            st.rerun()
                    if st.button(
                        "Chuyển cho chuyên viên",
                        key=f"escalate_send_{case_id}",
                        disabled=not reason.strip(),
                        use_container_width=True,
                    ):
                        try:
                            escalate_from_pending(case_id, actor=UI_ACTOR, reason=reason.strip())
                        except ValueError as error:
                            st.error(readable_text(str(error)))
                        else:
                            st.rerun()
                elif status is CaseStatus.SENT and not is_restricted_demo():
                    _render_correction(case_id)
            else:
                st.info("Chưa có bản thảo phản hồi được tạo.")
        else:
            # Escalation workspace
            st.markdown(
                '<div class="ex-card-title">👤 Chuyên viên cần xử lý</div>', unsafe_allow_html=True
            )
            if result.card:
                st.markdown(
                    f'<div style="font-size: 13.5px; font-weight: 600; color: #1E293B; margin-bottom: 6px;">'
                    f"<strong>Vấn đề cần quyết định:</strong> {escape_html(result.card.question)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if result.card.facts:
                    with st.expander("📌 Dữ kiện đã trích xuất từ email", expanded=True):
                        for f in result.card.facts:
                            st.markdown(f"• {readable_text(f)}")

                if result.card.partial_draft:
                    with st.expander("📝 Bản nháp gợi ý ban đầu", expanded=False):
                        st.text(
                            reply_text(
                                result.card.partial_draft.body, result.card.partial_draft.citations
                            )
                        )

                st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
                if not is_restricted_demo():
                    st.link_button(
                        "👤 Mở trong mục Cần chuyên viên xử lý",
                        f"/Hang_cho_duyet?case_id={quote(case_id)}",
                        type="primary",
                        use_container_width=True,
                    )

    with col_evid:
        st.markdown(
            '<div class="ex-card-title">📑 Căn cứ quy định đã sử dụng</div>', unsafe_allow_html=True
        )
        draft = result.draft or (result.card.partial_draft if result.card else None)
        citation_ids = draft.citations if draft else result.decision.evidence_ids

        has_citations = False
        if citation_ids:
            snapshots = (
                {chunk.chunk_id: chunk for chunk in result.evidence.chunks}
                if result.evidence
                else {}
            )
            for index, citation_id in enumerate(citation_ids, start=1):
                chunk = snapshots.get(citation_id) or get_chunk(citation_id)
                if chunk:
                    has_citations = True
                    st.markdown(
                        f'<div class="ex-evidence-box">'
                        f'<div class="ex-evidence-breadcrumb">📌 [{index}] {escape_html(chunk.breadcrumb)} · <span style="font-family: monospace; font-size: 11px;">{escape_html(chunk.chunk_id)}</span></div>'
                        f'<div class="ex-evidence-text">"{escape_html(chunk.text)}"</div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        elif result.card and result.card.basis:
            has_citations = True
            for breadcrumb, text in result.card.basis:
                st.markdown(
                    f'<div class="ex-evidence-box">'
                    f'<div class="ex-evidence-breadcrumb">📌 {escape_html(breadcrumb)}</div>'
                    f'<div class="ex-evidence-text">"{escape_html(text)}"</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        if not has_citations:
            st.markdown(
                '<div class="ex-card" style="background: #F8FAFC;">'
                '<span style="font-size: 13px; color: #64748B;">Không có đoạn trích dẫn quy định nào được liên kết cho ca này (hoặc nội dung nằm ngoài phạm vi quy chế hiện hành).</span>'
                "</div>",
                unsafe_allow_html=True,
            )

        st.link_button(
            "📚 Tra cứu Quy định & căn cứ", "/Quan_tri_quy_dinh", use_container_width=True
        )

    # ==================== C. EXPLAINABILITY & TIẾP THEO ====================
    st.markdown(
        "<hr style='margin: 18px 0 14px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True
    )
    explanation_key = f"explanation_{case_id}_{status}_{result.decision.reason}"
    col_exp, _ = st.columns([4, 6])
    with col_exp:
        if st.button(
            "💡 Vì sao hệ thống xử lý như vậy?", key=f"explain_{case_id}", use_container_width=True
        ):
            st.session_state[explanation_key] = readable_text(explain_plainly(case_id))
    if explanation := st.session_state.get(explanation_key):
        st.info(explanation)

    st.markdown(
        '<div class="ex-card-title" style="margin-top: 14px;">👉 Tiếp theo bạn có thể:</div>',
        unsafe_allow_html=True,
    )
    col_nxt1, col_nxt2, col_nxt3 = st.columns(3)
    with col_nxt1:
        if not is_restricted_demo():
            st.link_button(
                "👤 Cần chuyên viên xử lý",
                f"/Hang_cho_duyet?case_id={quote(case_id)}",
                use_container_width=True,
            )
        else:
            st.caption("Hàng duyệt đặc quyền không mở cho khách.")
    with col_nxt2:
        st.link_button(
            "📋 Nhật ký kiểm toán",
            f"/Nhat_ky_kiem_toan?case_id={quote(case_id)}",
            use_container_width=True,
        )
    with col_nxt3:
        st.link_button("🛡️ Verify (Kiểm thử tự động)", "/Verify", use_container_width=True)


def main() -> None:
    inject_app_css()

    # 1. Header matching mockup 04_email_entry_BASE.png
    st.markdown(
        page_header_html(
            "AI Ingestion & Evaluation",
            "Xử lý email",
            "Exodia tự động đối chiếu quy định và quyết định phản hồi tự động (AUTO_REPLY) hoặc chuyển chuyên viên (ESCALATE).",
        ),
        unsafe_allow_html=True,
    )

    _render_first_time_guidance()

    # 2. Thử nhanh với email mẫu (Quick Samples matching 04_email_entry_BASE.png)
    st.markdown(
        '<div style="font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">'
        '⚡ Thử nhanh với email mẫu: <span style="font-size: 12px; font-weight: 400; color: #64748B;">(Bấm để tự động điền nội dung)</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    col_s1, col_s2, col_s3 = st.columns(3)
    for col, s in zip((col_s1, col_s2, col_s3), SAMPLES):
        with col:
            if st.button(
                f"📌 {s['tag']}\n\n{s['desc']}",
                key=f"btn_{s['id']}",
                use_container_width=True,
            ):
                st.session_state["paste_sender"] = s["sender"]
                st.session_state["paste_subject"] = s["subject"]
                st.session_state["paste_body"] = s["body"]
                st.rerun()

    # Xác định bước Stepper hiện tại
    active_case_id = st.query_params.get("case_id") or st.session_state.get("active_case_id")
    if active_case_id and not case_is_owned(active_case_id, _owned_case_ids()):
        active_case_id = None
        st.session_state.pop("active_case_id", None)
        st.query_params.pop("case_id", None)
    step = 1
    if active_case_id:
        active_row = fetch_one("SELECT * FROM cases WHERE case_id = ?", (active_case_id,))
        if active_row:
            act_status = CaseStatus(active_row["status"])
            if act_status in (CaseStatus.ERROR, CaseStatus.INVALID_INPUT):
                step = 3
            elif act_status in (CaseStatus.RECEIVED, CaseStatus.PROCESSING):
                step = 2
            else:
                step = 5

    # 3. Processing Stepper (5 bước)
    st.markdown(_render_stepper(step), unsafe_allow_html=True)

    # 4. Main Body Split: Nhập email (Trái 4) vs Kết quả xử lý (Phải 6)
    col_left, col_right = st.columns([4, 6], gap="large")

    # ==================== CỘT TRÁI: NHẬP EMAIL CẦN XỬ LÝ ====================
    with col_left:
        st.markdown(
            '<div class="ex-card-title">📥 Nhập email cần xử lý</div>', unsafe_allow_html=True
        )
        if is_restricted_demo():
            st.caption("Public mode chỉ xử lý nội dung được điền từ 3 email mẫu ở phía trên.")
        else:
            st.caption(
                "Bạn có thể nhập email tự do trong private mode khi máy chủ được cấp quyền xử lý."
            )

        with st.form("email_form"):
            sender = st.text_input(
                "Email người gửi",
                placeholder="Ví dụ: sample.student4@example.test",
                key="paste_sender",
            )
            subject = st.text_input(
                "Tiêu đề",
                placeholder="Ví dụ: Xin nộp phúc khảo môn Kỹ thuật lập trình",
                key="paste_subject",
            )
            body = st.text_area(
                "Nội dung email",
                height=180,
                placeholder="Kính gửi Phòng Đào tạo / CTSV,\n\nEm là sinh viên...",
                key="paste_body",
            )
            st.caption(f"{len(body)}/5000 ký tự")

            with st.expander("📎 Đính kèm tệp (nếu có)", expanded=False):
                st.caption(
                    "Chức năng nhận tệp đính kèm (PDF/Ảnh) — Hiện đang chạy ở chế độ mô phỏng."
                )

            submitted = st.form_submit_button(
                "Xử lý email", type="primary", use_container_width=True
            )

        if submitted:
            try:
                _submit(paste_input(sender, subject, body))
                st.rerun()
            except (ValueError, RuntimeError) as error:
                st.error(readable_text(str(error)))

        # Expander: Thử bằng email minh họa (Giữ nguyên để tương thích AppTest)
        if not is_restricted_demo():
            with st.expander("📂 Hoặc chọn từ hộp thư mô phỏng (Inbox Synthetic)", expanded=False):
                emails = load_inbox()
                if emails:
                    selected = st.selectbox(
                        "Chọn email", emails, format_func=lambda email: email.subject
                    )
                    st.caption(f"Từ {selected.sender} · {local_time(selected.received_at)}")
                    st.text(selected.body)
                    if st.button(
                        "Xử lý email minh họa", key="process_inbox", use_container_width=True
                    ):
                        try:
                            _submit(inbox_input(selected))
                            st.rerun()
                        except (ValueError, RuntimeError) as error:
                            st.error(readable_text(str(error)))
                else:
                    st.info("Không có email minh họa. Bạn có thể nhập email trực tiếp ở trên.")

        # Expander: Mở lại email gần đây
        if is_restricted_demo():
            recent = [
                row
                for case_id in _owned_case_ids()
                if (
                    row := fetch_one(
                        "SELECT case_id, subject, status, received_at FROM cases WHERE case_id = ?",
                        (case_id,),
                    )
                )
                is not None
            ]
        else:
            recent = fetch_all(
                "SELECT case_id, subject, status, received_at FROM cases ORDER BY rowid DESC LIMIT 30"
            )
        with st.expander("🕒 Mở lại email đã lưu gần đây", expanded=False):
            if recent:
                selected_id = st.selectbox(
                    "Email đã lưu",
                    [row["case_id"] for row in recent],
                    format_func=lambda value: next(
                        f"{row['subject']} · {status_label(row['status'])} · {local_time(row['received_at'])}"
                        for row in recent
                        if row["case_id"] == value
                    ),
                    key="recent_saved_selector",
                )
                if st.button(
                    "Mở kết quả đã lưu", key="btn_open_recent_saved", use_container_width=True
                ):
                    st.session_state["active_case_id"] = selected_id
                    st.query_params["case_id"] = selected_id
                    st.rerun()
            else:
                st.info("Chưa có email đã lưu. Nhập email phía trên để bắt đầu.")

    # ==================== CỘT PHẢI: KẾT QUẢ XỬ LÝ & CĂN CỨ ====================
    with col_right:
        if not active_case_id:
            # Empty State
            st.markdown(
                """
                <div class="ex-card" style="text-align: center; padding: 48px 24px; background: #F8FAFC; border: 1.5px dashed #CBD5E1;">
                    <div style="font-size: 42px; margin-bottom: 12px;">📨</div>
                    <h3 style="font-size: 1.15rem; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
                        Chưa có email nào được chọn để xử lý
                    </h3>
                    <p style="font-size: 13.5px; color: #64748B; max-width: 440px; margin: 0 auto 18px auto; line-height: 1.5;">
                        Hãy nhập nội dung email ở cột bên trái hoặc bấm vào một trong các <strong>Email mẫu</strong> phía trên để Exodia tự động đối chiếu quy định.
                    </p>
                    <div style="display: flex; justify-content: center; gap: 18px; font-size: 12.5px; color: #475569;">
                        <span>✓ Đối chiếu quy chế tự động</span>
                        <span>✓ Phân định AUTO_REPLY / ESCALATE</span>
                        <span>✓ Minh bạch căn cứ pháp lý</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            render_saved_case(active_case_id)


main()
