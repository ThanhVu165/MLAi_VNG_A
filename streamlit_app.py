"""Điểm vào giao diện local và các dịch vụ dùng chung."""

import logging
import os
from sqlite3 import Error as DatabaseError

import streamlit as st

from core.controls import is_automation_paused, pause_automation, resume_automation
from core.worker import start_worker
from corpus.seed import ensure_seeded
from infra.demo_access import is_restricted_demo, validate_runtime_mode
from infra.judge_access import live_enabled
from infra.public_demo import enabled as public_demo_enabled
from ui.presentation import inject_app_css, readable_text


def main() -> None:
    st.set_page_config(page_title="Exodia · Trợ lý email sinh viên", page_icon="🏛️", layout="wide")
    inject_app_css()
    try:
        validate_runtime_mode()
        ensure_seeded()
        start_worker()
    except (OSError, RuntimeError, ValueError, DatabaseError):
        logging.getLogger(__name__).exception("Không khởi động được dữ liệu và xử lý nền.")
        st.error(
            "Chưa mở được dữ liệu hệ thống. Hãy kiểm tra tệp dữ liệu, quy định và bản sao lưu trước khi khởi động lại."
        )
        st.stop()
    restricted_demo = is_restricted_demo()
    judge_live = live_enabled() and os.getenv("LLM_MODE", "").strip().lower() == "live"
    pages = [
        st.Page("pages/1_Xu_ly_email.py", title="Xử lý email", icon="✉️", default=True),
    ]
    if not restricted_demo:
        pages.append(
            st.Page(
                "pages/2_Hang_cho_duyet.py",
                title="Cần chuyên viên xử lý",
                icon="👤",
                url_path="Hang_cho_duyet",
            )
        )
    pages.extend(
        [
            st.Page(
                "pages/3_Quan_tri_quy_dinh.py",
                title="Quy định & căn cứ",
                icon="📚",
                url_path="Quan_tri_quy_dinh",
            ),
            st.Page(
                "pages/4_Nhat_ky_kiem_toan.py",
                title="Nhật ký kiểm toán",
                icon="📋",
                url_path="Nhat_ky_kiem_toan",
            ),
            st.Page("pages/5_Verify.py", title="Kiểm thử", icon="🛡️", url_path="Verify"),
        ]
    )
    if not restricted_demo:
        pages.append(
            st.Page("pages/6_Do_luong.py", title="Đo lường", icon="📊", url_path="Do_luong")
        )
    page = st.navigation(pages)
    paused = is_automation_paused()
    if restricted_demo:
        st.sidebar.caption(
            "Restricted DEMO: Judge LIVE có kiểm soát; không kết nối hộp thư và "
            "không gửi email thật."
            if judge_live
            else "Restricted DEMO: replay offline trên dữ liệu synthetic; không kết nối hộp thư, "
            "không gửi email thật và không gọi provider LIVE."
        )
    else:
        st.sidebar.caption("Chưa kết nối hộp thư. Thao tác gửi hiện được ghi nhận mô phỏng.")
    if not restricted_demo:
        with st.sidebar.expander("Điều khiển gửi tự động", expanded=paused):
            st.caption("Đang tạm dừng gửi" if paused else "Đang cho phép gửi sau 60 giây")
            if paused:
                if st.button("Tiếp tục gửi tự động"):
                    resume_automation("ADMIN:local")
                    st.rerun()
            else:
                reason = st.text_input("Lý do tạm dừng", key="pause_reason")
                if st.button("Tạm dừng tự động", disabled=not reason.strip()):
                    try:
                        pause_automation("ADMIN:local", reason)
                    except ValueError as error:
                        st.error(readable_text(str(error)))
                    else:
                        st.rerun()
    if restricted_demo:
        shell_title = "🔵 Restricted DEMO"
        shell_description = (
            "Public LIVE: nhập email synthetic mới, tối đa 10 email/phiên; không gửi email."
            if judge_live and public_demo_enabled()
            else (
                "Judge LIVE được giới hạn; chỉ phiên có operator grant mới xử lý email mới."
                if judge_live
                else "Môi trường mô phỏng dùng replay offline; email LIVE không hoạt động."
            )
        )
    else:
        shell_title = "🟢 Ứng dụng sẵn sàng"
        shell_description = "Môi trường mô phỏng; email LIVE chưa được kết nối."
    st.sidebar.markdown(
        f"""
        <div class="ex-shell-status">
            <div class="ex-shell-status-title">{shell_title}</div>
            <div class="ex-shell-status-description">{shell_description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page.run()


if __name__ == "__main__":
    main()
