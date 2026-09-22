from pathlib import Path

import streamlit as st


FLOW_DIAGRAM_PATH = Path(__file__).parent / "docs" / "slide2_flow.svg"


def main() -> None:
    st.set_page_config(page_title="Escalation Referee", page_icon="📨", layout="wide")
    st.write("Dán email sinh viên vào ô bên dưới và bấm Xử lý.")
    st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
    st.title("Escalation Referee")
    st.subheader("Luồng xử lý và hai điểm con người quyết định")
    if FLOW_DIAGRAM_PATH.is_file():
        st.image(str(FLOW_DIAGRAM_PATH), use_column_width=True)
    else:
        st.error("Không tìm thấy sơ đồ luồng. Hãy kiểm tra lại tệp docs/slide2_flow.svg.")


if __name__ == "__main__":
    main()
