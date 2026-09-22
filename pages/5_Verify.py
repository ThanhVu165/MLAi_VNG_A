"""Chạy các bộ Verify theo đúng pipeline dùng chung."""

from __future__ import annotations

import json
from urllib.parse import quote

import streamlit as st

from core.types import Decision, EscalationType
from verify.harness import CASE_SETS, VerifyResult, run_cases


def _decision_label(decision: Decision, escalation_type: EscalationType | None) -> str:
    if decision is Decision.AUTO_REPLY:
        return "Trả lời tự động"
    if decision is Decision.ESCALATE:
        labels = {
            EscalationType.FACT_UNRESOLVED: "Thiếu dữ kiện",
            EscalationType.OUT_OF_POLICY: "Ngoài phạm vi quy định",
            EscalationType.AUTHORITY_REQUIRED: "Cần phê duyệt",
        }
        label = labels[escalation_type] if escalation_type is not None else "Chưa phân loại"
        return f"Chuyển tiếp — {label}"
    return "Dữ liệu đầu vào chưa hợp lệ"


def _audit_url(case_id: str) -> str:
    """Tạo liên kết audit tuyệt đối để DataFrame hiển thị được liên kết."""
    headers = st.context.headers
    host = headers.get("host")
    path = f"/Nhat_ky_kiem_toan?case_id={quote(case_id)}"
    if not host:
        return path
    protocol = headers.get("x-forwarded-proto", "http")
    return f"{protocol}://{host}{path}"


def _row(result: VerifyResult, *, include_question: bool = False) -> dict[str, str | int]:
    row: dict[str, str | int] = {
        "Case": result.case_id,
        "Xem audit log": _audit_url(result.case_ref),
        "Tóm tắt input": result.subject,
        "Kỳ vọng": _decision_label(result.expected_decision, result.expected_type),
        "Thực tế": _decision_label(result.actual_decision, result.actual_type),
        "Quy tắc": result.rule_id,
        "Kết quả": "PASS" if result.passed else "FAIL",
        "Thời gian (ms)": result.elapsed_ms,
        "Thời điểm (+07:00)": result.timestamp,
        "Phiên bản corpus": result.corpus_version,
    }
    if include_question:
        row["Câu hỏi chuyển tiếp"] = result.question or "—"
    return row


def _render_results(results: tuple[VerifyResult, ...], *, include_question: bool = False) -> None:
    st.dataframe(
        [_row(result, include_question=include_question) for result in results],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Xem audit log": st.column_config.LinkColumn(
                "Xem audit log", display_text="Xem audit log"
            )
        },
    )
    st.download_button(
        "Xuất JSON kết quả Verify",
        data=json.dumps(
            [_row(result, include_question=include_question) for result in results],
            ensure_ascii=False,
        ),
        file_name="ket-qua-verify.json",
        mime="application/json",
    )
    for result in results:
        st.link_button(f"Xem audit log: {result.case_id}", _audit_url(result.case_ref))
    if all(result.passed for result in results):
        st.success(f"Cả {len(results)} trường hợp đều PASS.")
    else:
        st.error("Có trường hợp FAIL. Hãy mở nhật ký kiểm toán để xem quyết định thực tế.")


def _run_set(case_set: str, *, include_question: bool = False) -> None:
    case_ids = "V01 đến V04" if case_set == "verify4" else "E01 đến E05"
    with st.spinner(f"Đang chạy tuần tự {case_ids} qua pipeline dùng chung."):
        results = run_cases(CASE_SETS[case_set], run_name=case_set)
    _render_results(results, include_question=include_question)


st.set_page_config(page_title="Verify", page_icon="✅", layout="wide")
st.title("Verify 4 trường hợp")
st.info("Chế độ mô phỏng — hệ thống không gửi email thật.")
st.caption("Bộ này chỉ gồm V01–V04; V03 là trường hợp từ chối bắt buộc.")

if st.button("Chạy Verify 4 trường hợp", type="primary"):
    _run_set("verify4")

st.divider()
st.subheader("Kiểm tra chuyển tiếp 5 trường hợp")
st.caption("E01–E03 phải trả lời tự động; E04–E05 phải chuyển tiếp kèm loại và câu hỏi.")
if st.button("Chạy kiểm tra chuyển tiếp 5 trường hợp", type="primary"):
    _run_set("escalation5", include_question=True)
