"""Điểm vào giao diện local và các dịch vụ dùng chung."""

import logging
from sqlite3 import Error as DatabaseError

import streamlit as st

from core.controls import is_automation_paused, pause_automation, resume_automation
from core.worker import start_worker
from corpus.seed import ensure_seeded
from ui.presentation import readable_text


def main() -> None:
    st.set_page_config(page_title="Exodia · Trợ lý email sinh viên", page_icon="🏛️", layout="wide")
    try:
        ensure_seeded()
        start_worker()
    except (OSError, RuntimeError, ValueError, DatabaseError):
        logging.getLogger(__name__).exception("Không khởi động được dữ liệu và xử lý nền.")
        st.error(
            "Chưa mở được dữ liệu hệ thống. Hãy kiểm tra tệp dữ liệu, quy định và bản sao lưu trước khi khởi động lại."
        )
        st.stop()
    page = st.navigation(
        [
            st.Page("pages/1_Xu_ly_email.py", title="Xử lý email", icon="✉️", default=True),
            st.Page(
                "pages/2_Hang_cho_duyet.py",
                title="Cần chuyên viên xử lý",
                icon="👤",
                url_path="Hang_cho_duyet",
            ),
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
            st.Page("pages/5_Verify.py", title="Verify", icon="🛡️", url_path="Verify"),
            st.Page("pages/6_Do_luong.py", title="Đo lường", icon="📊", url_path="Do_luong"),
        ]
    )
    paused = is_automation_paused()
    st.sidebar.caption("Chưa kết nối hộp thư. Thao tác gửi hiện được ghi nhận mô phỏng.")
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
    st.sidebar.markdown(
        """
        <div style="margin-top: 1.5rem; padding: 10px 12px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;">
            <div style="font-size: 11.5px; font-weight: 700; color: #047857; display: flex; align-items: center; gap: 6px;">
                <span>🟢</span> Hệ thống hoạt động
            </div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">
                Môi trường mô phỏng an toàn
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page.run()


if __name__ == "__main__":
    main()
