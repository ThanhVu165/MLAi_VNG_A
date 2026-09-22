"""Chạy các bộ Verify theo đúng pipeline dùng chung."""

from __future__ import annotations

import streamlit as st

from verify.harness import CASE_SETS, VerifyResult, run_cases


def _row(result: VerifyResult) -> dict[str, str | int]:
    return {
        "Case": result.case_id,
        "Kỳ vọng": f"{result.expected_decision}/{result.expected_type or '—'}",
        "Thực tế": f"{result.actual_decision}/{result.actual_type or '—'}",
        "Quy tắc": result.rule_id,
        "Kết quả": "PASS" if result.passed else "FAIL",
        "Thời gian (ms)": result.elapsed_ms,
    }


st.set_page_config(page_title="Verify", page_icon="✅", layout="wide")
st.title("Verify 4 trường hợp")
st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
st.caption("Bộ này chỉ gồm V01–V04; V03 là trường hợp từ chối bắt buộc.")

if st.button("Chạy Verify 4 trường hợp", type="primary"):
    with st.spinner("Đang chạy tuần tự V01 đến V04 qua pipeline dùng chung."):
        results = run_cases(CASE_SETS["verify4"], run_name="verify4")
    st.dataframe([_row(result) for result in results], use_container_width=True, hide_index=True)
    if all(result.passed for result in results):
        st.success("Cả 4 trường hợp đều PASS.")
    else:
        st.error("Có trường hợp FAIL. Hãy mở nhật ký kiểm toán để xem quyết định thực tế.")
