"""Trang kiểm tra thủ công các URL nguồn quy định."""

from __future__ import annotations

import streamlit as st

from corpus.intake import recheck_url_sources


st.set_page_config(page_title="Quản trị quy định", page_icon="📚")
st.title("Quản trị quy định")
st.caption("Chỉ kiểm tra khi bạn bấm nút; hệ thống không chạy nền hay định kỳ.")

if st.button("Kiểm tra nguồn mới", type="primary"):
    with st.spinner("Đang tải lại các URL đã đăng ký..."):
        results = recheck_url_sources(actor="ADMIN:local")
    if not results:
        st.info("Chưa có URL nguồn nào để kiểm tra.")
    for result in results:
        if result.error:
            st.error(f"{result.source.title or result.source.doc_id}: {result.message}")
        elif result.changed:
            st.warning(f"{result.source.title or result.source.doc_id}: {result.message}")
        else:
            st.success(f"{result.source.title or result.source.doc_id}: {result.message}")
