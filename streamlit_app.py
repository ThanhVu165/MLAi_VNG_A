"""Điểm vào giao diện local và các dịch vụ dùng chung."""

import logging
from sqlite3 import Error as DatabaseError

import streamlit as st

from core.controls import is_automation_paused, pause_automation, resume_automation
from core.worker import start_worker
from corpus.seed import ensure_seeded
from ui.presentation import readable_text


def main() -> None:
    st.set_page_config(page_title="Hỗ trợ email sinh viên", page_icon="📨", layout="wide")
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
            st.Page("pages/1_Xu_ly_email.py", title="Email", default=True),
            st.Page(
                "pages/2_Hang_cho_duyet.py",
                title="Cần chuyên viên xử lý",
                url_path="Hang_cho_duyet",
            ),
            st.Page("pages/3_Quan_tri_quy_dinh.py", title="Quy định", url_path="Quan_tri_quy_dinh"),
            st.Page(
                "pages/4_Nhat_ky_kiem_toan.py", title="Lịch sử xử lý", url_path="Nhat_ky_kiem_toan"
            ),
            st.Page("pages/5_Verify.py", title="Kiểm tra hệ thống", url_path="Verify"),
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
    page.run()


if __name__ == "__main__":
    main()
