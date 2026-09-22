"""Trang hàng chờ để chuyên viên duyệt các case được chuyển tiếp."""

from __future__ import annotations

import streamlit as st

from core.explain import explain_plainly


st.title("Hàng chờ duyệt")
st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
st.info("Chưa có case đang chờ duyệt. Hãy xử lý email cần chuyển tiếp để xem thẻ quyết định.")
case_id = st.text_input("Mã case cần giải thích", placeholder="Ví dụ: c_01")
if st.button("Giải thích cho người không chuyên"):
    if not case_id.strip():
        st.error("Hãy nhập mã case trước khi yêu cầu giải thích.")
    else:
        try:
            explanation = explain_plainly(case_id.strip())
        except ValueError:
            st.error("Chưa thể tạo giải thích cho case này. Hãy kiểm tra lại mã case.")
        else:
            with st.container(border=True):
                st.subheader("Vì sao hệ thống xử lý như vậy?")
                st.write(explanation)
