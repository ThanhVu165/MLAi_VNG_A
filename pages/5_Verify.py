"""Kiểm tra cùng đường xử lý với email nhập trên giao diện."""

from __future__ import annotations

import json
from dataclasses import asdict
from time import perf_counter
from urllib.parse import quote

import streamlit as st

from ui.presentation import decision_label, local_time
from verify.harness import CASE_SETS, VerifyResult, run_cases


def render_results(results: tuple[VerifyResult, ...], elapsed: float, case_set: str) -> None:
    st.dataframe(
        [
            {
                "Email": result.subject,
                "Mong đợi": decision_label(result.expected_decision, result.expected_type),
                "Thực tế": decision_label(result.actual_decision, result.actual_type),
                "Kết quả": "Đạt" if result.passed else "Chưa đạt",
                "Thời gian (giây)": round(result.elapsed_ms / 1000, 2),
                "Câu hỏi chuyên viên": result.question or "Không cần",
                "Thời điểm": local_time(result.timestamp),
            }
            for result in results
        ],
        hide_index=True,
        use_container_width=True,
    )
    within_limit = case_set != "escalation5" or elapsed <= 90
    if all(result.passed for result in results) and within_limit:
        st.success(
            f"{len(results)}/{len(results)} tình huống đạt yêu cầu · Tổng thời gian {elapsed:.1f} giây."
        )
    else:
        st.error(
            f"Còn tình huống chưa đạt hoặc vượt thời gian cho phép · Tổng thời gian {elapsed:.1f} giây."
        )
    if case_set == "escalation5":
        st.caption(
            "Bộ năm email phải có ba phản hồi tự động, hai chuyển tiếp đúng lý do và hoàn thành trong 90 giây."
        )
    with st.expander("Mở từng lần xử lý"):
        for result in results:
            st.link_button(result.subject, f"/Nhat_ky_kiem_toan?case_id={quote(result.case_ref)}")
    st.download_button(
        "Tải kết quả kiểm tra đầy đủ",
        json.dumps(
            {
                "set": case_set,
                "elapsed_seconds": elapsed,
                "within_time_limit": within_limit,
                "results": [asdict(result) for result in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        file_name="ket-qua-kiem-tra.json",
        mime="application/json",
    )


st.title("Kiểm tra hệ thống")
st.caption(
    "Mỗi email đi qua cùng cách xử lý với trang Email. Kết quả kiểm tra cả quyết định, lý do chuyển tiếp, quy tắc và căn cứ."
)
st.caption("Bài kiểm tra tạo lịch sử xử lý thật trong dữ liệu local; không gửi email ra ngoài.")
sets = {
    "full15": "Toàn bộ 15 tình huống",
    "verify4": "Bốn tình huống sơ khảo",
    "escalation5": "Năm tình huống chuyển tiếp",
}
case_set = st.selectbox("Bài kiểm tra", list(sets), format_func=lambda value: sets[value])
if st.button("Chạy kiểm tra", type="primary"):
    with st.spinner("Đang xử lý lần lượt các email. Bạn có thể mở lịch sử ở tab khác."):
        started = perf_counter()
        results = run_cases(CASE_SETS[case_set], run_name=case_set)
        st.session_state["verification_result"] = (results, perf_counter() - started, case_set)
if "verification_result" in st.session_state:
    render_results(*st.session_state["verification_result"])
