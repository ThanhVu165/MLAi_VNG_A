from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from core.controls import (
    is_automation_paused,
    override_decision,
    pause_automation,
    rerun_case,
    resume_automation,
)
from core.types import CaseInput, Decision
from infra.db import fetch_all

FLOW_DIAGRAM_PATH = Path(__file__).parent / "docs" / "slide2_flow.svg"
ADMIN_ACTOR = "ADMIN:demo"
PAGE_NAMES = (
    "Xử lý email",
    "Hàng chờ xử lý",
    "Quản trị quy định",
    "Nhật ký kiểm toán",
    "Verify",
    "Đo lường",
)


def _case_options() -> tuple[tuple[str, Decision], ...]:
    rows = fetch_all(
        """
        SELECT decision, case_id FROM decisions AS current
        WHERE rowid = (
            SELECT MAX(rowid) FROM decisions WHERE case_id = current.case_id
        ) AND decision IN (?, ?)
        ORDER BY rowid DESC
        """,
        (Decision.AUTO_REPLY.value, Decision.ESCALATE.value),
    )
    return tuple((row["case_id"], Decision(row["decision"])) for row in rows)


def _decision_label(decision: Decision) -> str:
    return "Trả lời tự động" if decision is Decision.AUTO_REPLY else "Chuyển tiếp chuyên viên"


def _render_override(options: tuple[tuple[str, Decision], ...]) -> None:
    if not options:
        st.sidebar.info("Chưa có case có thể ghi đè quyết định.")
        return
    selected = st.sidebar.selectbox(
        "Case cần ghi đè",
        options,
        format_func=lambda item: f"{item[0]} · {_decision_label(item[1])}",
    )
    target = Decision.ESCALATE if selected[1] is Decision.AUTO_REPLY else Decision.AUTO_REPLY
    st.sidebar.caption(f"Quyết định mới: {_decision_label(target)}")
    reason = st.sidebar.text_area("Lý do ghi đè", key="override_reason")
    if st.sidebar.button("Ghi đè quyết định", disabled=not reason.strip()):
        try:
            override_decision(selected[0], target, ADMIN_ACTOR, reason)
        except ValueError as error:
            st.sidebar.error(str(error))
        else:
            st.sidebar.success("Đã ghi đè quyết định.")


def _render_rerun(options: tuple[tuple[str, Decision], ...]) -> None:
    if not options:
        return
    case_id = st.sidebar.selectbox("Case cần chạy lại", options, format_func=lambda item: item[0])[
        0
    ]
    if st.sidebar.button("Chạy lại case"):
        try:
            _, diff = rerun_case(case_id, ADMIN_ACTOR)
        except ValueError as error:
            st.sidebar.error(str(error))
        else:
            st.sidebar.success("Đã chạy lại case trên quy định hiện tại.")
            st.sidebar.dataframe(
                [
                    {"Nội dung": field, "Lần trước": value["before"], "Lần này": value["after"]}
                    for field, value in diff.items()
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_global_controls() -> None:
    """Hiển thị các can thiệp quản trị dùng chung ở thanh bên."""
    st.sidebar.divider()
    st.sidebar.subheader("Điều khiển quản trị")
    pause_reason = st.sidebar.text_input("Lý do tạm dừng", key="pause_reason")
    if st.sidebar.button("Tạm dừng tự động", disabled=not pause_reason.strip()):
        try:
            pause_automation(ADMIN_ACTOR, pause_reason)
        except ValueError as error:
            st.sidebar.error(str(error))
        else:
            st.sidebar.success("Đã tạm dừng tự động hóa.")
    if st.sidebar.button("Tiếp tục"):
        resume_automation(ADMIN_ACTOR)
        st.sidebar.success("Đã tiếp tục tự động hóa.")
    if is_automation_paused():
        st.sidebar.error("Tự động hóa đang tạm dừng — email mới sẽ vào hàng chờ.")
    else:
        st.sidebar.success("Tự động hóa đang hoạt động.")
    options = _case_options()
    _render_override(options)
    _render_rerun(options)


def render_sidebar() -> None:
    st.sidebar.title("Điều hướng")
    for page_name in PAGE_NAMES:
        st.sidebar.write(f"• {page_name}")
    render_global_controls()


def main() -> None:
    st.set_page_config(page_title="Escalation Referee", page_icon="📨", layout="wide")
    st.write("Dán email sinh viên vào ô bên dưới và bấm Xử lý.")
    sender = st.text_input("Email người gửi", key="home_email_sender")
    subject = st.text_input("Tiêu đề", key="home_email_subject")
    body = st.text_area(
        "Nội dung email sinh viên",
        placeholder="Dán toàn bộ nội dung email vào đây.",
        key="home_email_body",
    )
    if st.button("Xử lý email", type="primary"):
        if not all(value.strip() for value in (sender, subject, body)):
            st.error("Hãy nhập đủ email người gửi, tiêu đề và nội dung trước khi xử lý.")
        else:
            st.session_state["home_email_to_process"] = CaseInput(
                sender=sender,
                subject=subject,
                body=body,
                received_at=datetime.now(timezone.utc),
                channel="paste",
            )
            st.switch_page("pages/1_Xu_ly_email.py")
    st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
    render_sidebar()
    st.title("Escalation Referee")
    st.subheader("Luồng xử lý và hai điểm con người quyết định")
    if FLOW_DIAGRAM_PATH.is_file():
        st.markdown(FLOW_DIAGRAM_PATH.read_text(encoding="utf-8"), unsafe_allow_html=True)
    else:
        st.error("Không tìm thấy sơ đồ luồng. Hãy kiểm tra lại tệp docs/slide2_flow.svg.")


if __name__ == "__main__":
    main()
