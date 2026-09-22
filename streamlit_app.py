from pathlib import Path

import streamlit as st


FLOW_DIAGRAM_PATH = Path(__file__).parent / "docs" / "slide2_flow.svg"
PAGE_NAMES = (
    "Xử lý email",
    "Hàng chờ xử lý",
    "Quản trị quy định",
    "Nhật ký kiểm toán",
    "Verify",
    "Đo lường",
)


def render_sidebar() -> None:
    st.sidebar.title("Điều hướng")
    for page_name in PAGE_NAMES:
        st.sidebar.write(f"• {page_name}")


def main() -> None:
    st.set_page_config(page_title="Escalation Referee", page_icon="📨", layout="wide")
    st.write("Dán email sinh viên vào ô bên dưới và bấm Xử lý.")
    st.text_area("Nội dung email sinh viên", placeholder="Dán toàn bộ nội dung email vào đây.")
    st.button("Xử lý email")
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
