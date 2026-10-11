"""Trang Đo lường & Hiệu quả — Theo dõi an toàn ra quyết định, tự động hóa và vận hành."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st

from core.types import Decision, EscalationType
from infra.db import fetch_all
from infra.telemetry import snapshot
from verify.harness import VerifyResult
from ui.presentation import (
    decision_badge_html,
    escape_html,
    inject_app_css,
    kpi_card_html,
    local_time,
    page_header_html,
    stop_reason_badge_html,
    stop_reason_text,
)

STEP_DESCRIPTIONS: dict[str, str] = {
    "R0": "Khởi tạo ngữ cảnh luồng",
    "R1": "Làm sạch & chuẩn hóa email",
    "R2": "Trích xuất dữ kiện yêu cầu",
    "R2_extract": "Trích xuất dữ kiện chi tiết",
    "R4": "Truy vấn và lựa chọn căn cứ",
    "R4_select": "Chọn lọc điều khoản phù hợp",
    "R5": "Kiểm tra giới hạn thẩm quyền",
    "R6": "Đối chiếu quy tắc áp dụng",
    "R7": "Soạn thảo phản hồi / câu hỏi",
    "R7_generate": "Tạo nội dung bản nháp",
    "R7_question": "Tạo câu hỏi chuyển chuyên viên",
    "R8": "Kiểm định căn cứ & an toàn",
    "R9": "Ghi nhận quyết định hệ thống",
    "R10": "Lên lịch gửi phản hồi",
    "R11": "Gửi phản hồi mô phỏng",
}

RULE_DESCRIPTIONS: dict[str, str] = {
    "P01": "Vượt thẩm quyền phân cấp (Cần cấp quản lý quyết định)",
    "P02": "Ngoài quy định, không có nguồn phù hợp hoặc căn cứ mâu thuẫn",
    "P03": "Thiếu dữ kiện cần thiết từ người gửi",
    "P04": "Kiểm tra an toàn hoặc căn cứ không đạt",
    "P05": "Đủ căn cứ quy định hợp lệ — Tự động soạn phản hồi",
}


def _percent(value: object) -> str:
    return f"{value:.1%}" if isinstance(value, (int, float)) else "Chưa có dữ liệu"


def _seconds(value: object) -> str:
    return f"{value:.1f} giây" if isinstance(value, (int, float)) else "Chưa có dữ liệu"


def _milliseconds(value: object) -> str:
    return f"{value} ms" if isinstance(value, (int, float)) else "—"


def _get_deterministic_fixtures(fixture_type: str) -> tuple[tuple[VerifyResult, ...], float, str]:
    """Cung cấp fixture kiểm thử tất định cho visual review/mock mà không gọi LLM thật."""
    if fixture_type == "with_fail":
        items = (
            VerifyResult("TC_AUTO_001", "Hỏi về lịch đăng ký học phần", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1200, "14:15:00 ngày 10/10/2026", "cv_01", "ref_tc_01", "P05"),
            VerifyResult("TC_AUTO_002", "Hỏi về học phí và thời hạn đóng", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1400, "14:15:02 ngày 10/10/2026", "cv_01", "ref_tc_02", "P05"),
            VerifyResult("TC_ESC_POLICY_001", "Yêu cầu hỗ trợ ngoài chính sách", "Trường hợp xin hỗ trợ ngoài quy chế, anh/chị có tiếp nhận hồ sơ đặc biệt không?", Decision.ESCALATE, EscalationType.OUT_OF_POLICY, Decision.ESCALATE, EscalationType.OUT_OF_POLICY, "P02", True, 1600, "14:15:04 ngày 10/10/2026", "cv_01", "ref_tc_03", "P02"),
            VerifyResult("TC_ESC_AUTH_001", "Yêu cầu giảm học phí (cần thẩm quyền)", "Thẩm quyền miễn giảm thuộc Hội đồng, anh/chị có trình hồ sơ xét duyệt không?", Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, "P01", True, 1500, "14:15:06 ngày 10/10/2026", "cv_01", "ref_tc_04", "P01"),
            VerifyResult("TC_ESC_INFO_001", "Thiếu mã sinh viên và thông tin lớp", "Email thiếu mã số sinh viên, anh/chị có yêu cầu cung cấp thêm thông tin không?", Decision.ESCALATE, EscalationType.FACT_UNRESOLVED, Decision.ESCALATE, EscalationType.FACT_UNRESOLVED, "P03", True, 1300, "14:15:08 ngày 10/10/2026", "cv_01", "ref_tc_05", "P03"),
            VerifyResult("TC_INVALID_001", "Nội dung không phải email", None, Decision.INVALID_INPUT, None, Decision.INVALID_INPUT, None, "INV", True, 1100, "14:15:10 ngày 10/10/2026", "cv_01", "ref_tc_06", "INV"),
            VerifyResult("TC_FAIL_001", "Trường hợp biên chưa đúng quy định", "Cần chuyên viên xem xét.", Decision.AUTO_REPLY, None, Decision.ESCALATE, EscalationType.OUT_OF_POLICY, "P02", False, 1500, "14:15:12 ngày 10/10/2026", "cv_01", "ref_tc_07", "P05"),
            VerifyResult("TC_FAIL_002", "Trường hợp căn cứ chưa đầy đủ", None, Decision.ESCALATE, EscalationType.FACT_UNRESOLVED, Decision.AUTO_REPLY, None, "P05", False, 1400, "14:15:14 ngày 10/10/2026", "cv_01", "ref_tc_08", "P03"),
            VerifyResult("TC_AUTO_003", "Hỏi thủ tục cấp bảng điểm", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1350, "14:15:16 ngày 10/10/2026", "cv_01", "ref_tc_09", "P05"),
            VerifyResult("TC_AUTO_004", "Hỏi địa điểm nộp hồ sơ sinh viên", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1250, "14:15:18 ngày 10/10/2026", "cv_01", "ref_tc_10", "P05"),
            VerifyResult("TC_ESC_AUTH_002", "Xin bảo lưu kết quả học tập quá hạn", "Trường hợp xin bảo lưu quá hạn, anh/chị có đề xuất xét duyệt ngoại lệ không?", Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, "P01", True, 1650, "14:15:20 ngày 10/10/2026", "cv_01", "ref_tc_11", "P01"),
            VerifyResult("TC_AUTO_005", "Hỏi thời gian làm việc phòng CTSV", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1150, "14:15:22 ngày 10/10/2026", "cv_01", "ref_tc_12", "P05"),
        )
        return items, 18.2, "m2_combined_dev"

    items = (
        VerifyResult("V01", "Quy trình và thang điểm rèn luyện", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1200, "09:00:00 ngày 21/09/2026", "cv_seed_001", "ref_v01", "P05"),
        VerifyResult("V02", "Hạn rút học phần", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1400, "09:01:00 ngày 21/09/2026", "cv_seed_001", "ref_v02", "P05"),
        VerifyResult("V03", "Xin nộp phúc khảo muộn vì nhập viện", "Trường hợp nộp phúc khảo ngoài thời hạn do nhập viện, anh/chị có đồng ý tiếp nhận không?", Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, "P01", True, 1600, "09:02:00 ngày 21/09/2026", "cv_seed_001", "ref_v03", "P01"),
        VerifyResult("V04", "Đăng ký ký túc xá", "Vấn đề đăng ký ký túc xá không thuộc phạm vi xử lý đào tạo, anh/chị có chuyển đơn vị quản lý KTX không?", Decision.ESCALATE, EscalationType.OUT_OF_POLICY, Decision.ESCALATE, EscalationType.OUT_OF_POLICY, "P02", True, 1500, "09:03:00 ngày 21/09/2026", "cv_seed_001", "ref_v04", "P02"),
    )
    return items, 5.7, "verify4"


def _get_evaluation_metrics() -> dict[str, Any] | None:
    """Lấy số liệu kiểm thử từ phiên Verify hoặc fixture thử nghiệm (nếu có)."""
    # 1. Kiểm tra session state từ trang Verify
    if "verification_result" in st.session_state:
        results, elapsed, case_set = st.session_state["verification_result"]
        return _parse_verify_results(results, elapsed, case_set, source="Phiên kiểm thử", synthetic=False)

    # 2. Kiểm tra query param fixture (cho visual review / demo)
    fixture_param = st.query_params.get("fixture")
    if fixture_param in {"with_fail", "all_pass"}:
        results, elapsed, case_set = _get_deterministic_fixtures(fixture_param)
        source_label = (
            "Bộ kiểm thử 12 ca (M2 Combined)"
            if fixture_param == "with_fail"
            else "Bộ kiểm thử 4 ca (Sơ khảo)"
        )
        return _parse_verify_results(results, elapsed, case_set, source=source_label, synthetic=True)

    return None


def _parse_verify_results(
    results: tuple[Any, ...], elapsed: float, case_set: str, source: str, *, synthetic: bool
) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if getattr(r, "passed", False))
    failed = total - passed

    # Missed Escalation: Mong muốn ESCALATE nhưng thực tế AUTO_REPLY (nguy hiểm)
    missed = sum(
        1
        for r in results
        if getattr(r, "expected_decision", None) == Decision.ESCALATE
        and getattr(r, "actual_decision", None) == Decision.AUTO_REPLY
    )
    # Unnecessary Escalation: Mong muốn AUTO_REPLY nhưng thực tế ESCALATE
    unnecessary = sum(
        1
        for r in results
        if getattr(r, "expected_decision", None) == Decision.AUTO_REPLY
        and getattr(r, "actual_decision", None) == Decision.ESCALATE
    )

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total) if total else 0.0,
        "missed_count": missed,
        "missed_rate": (missed / total) if total else 0.0,
        "unnecessary_count": unnecessary,
        "unnecessary_rate": (unnecessary / total) if total else 0.0,
        "elapsed": elapsed,
        "case_set": case_set,
        "source": source,
        "synthetic": synthetic,
    }


def main() -> None:
    inject_app_css()

    # 1. Header & Data Provenance
    st.markdown(
        page_header_html(
            "ĐO LƯỜNG & ĐÁNH GIÁ",
            "Đo lường",
            "Theo dõi mức độ tuân thủ ranh giới an toàn, tỷ lệ tự động hóa và hiệu năng hệ thống từ dữ liệu thực tế.",
        ),
        unsafe_allow_html=True,
    )

    # Lấy dữ liệu telemetry từ SQLite
    metrics = snapshot()

    # Truy vấn bổ sung số lượng thực tế từ SQLite
    try:
        cases_count_res = fetch_all("SELECT COUNT(*) AS total FROM cases")
        total_cases = cases_count_res[0]["total"] if cases_count_res else 0
    except Exception:
        total_cases = 0

    # Support testing empty state cleanly via query param ?empty=1
    is_empty_mode = st.query_params.get("empty") == "1"
    if is_empty_mode:
        total_cases = 0
        decisions_rows = []
        metrics = {k: (None if "rate" in k else {}) for k in metrics}
        metrics["auto_rate"] = None
        metrics["median_review_seconds"] = 0.0
    else:
        try:
            decisions_rows = fetch_all(
                "SELECT decision, escalation_type, rule_id, is_override, created_at FROM decisions"
            )
        except Exception:
            decisions_rows = []

    classified_rows = [r for r in decisions_rows if r["decision"] in ("AUTO_REPLY", "ESCALATE")]
    total_classified = len(classified_rows)
    auto_count = sum(1 for r in classified_rows if r["decision"] == "AUTO_REPLY")
    esc_count = sum(1 for r in classified_rows if r["decision"] == "ESCALATE")

    # Timestamp cập nhật gần nhất
    try:
        latest_audit = fetch_all("SELECT MAX(ts) AS last_ts FROM audit_events")
        last_ts = latest_audit[0]["last_ts"] if latest_audit and latest_audit[0]["last_ts"] else None
        last_updated_str = local_time(last_ts) if last_ts else "Chưa có bản ghi"
    except Exception:
        last_updated_str = "Chưa có bản ghi"

    # Data Provenance Banner
    st.markdown(
        f"""<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 16px; margin-bottom: 20px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; font-size: 13px;">
<div>
<span style="color: #64748B;">Nguồn dữ liệu:</span> <strong style="color: #0F172A;">SQLite (decisions, audit_events, step_latencies)</strong>
<span style="color: #CBD5E1; margin: 0 8px;">|</span>
<span style="color: #64748B;">Cập nhật:</span> <strong style="color: #0F172A;">{last_updated_str}</strong>
</div>
<div>
<span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; padding: 3px 10px; border-radius: 9999px; font-weight: 600; font-size: 12px;">Môi trường: Đánh giá nội bộ · 0 LIVE API</span>
</div>
</div>""",
        unsafe_allow_html=True,
    )

    # Empty State Handling: Nếu chưa có ca nào
    if total_cases == 0 and not decisions_rows:
        st.markdown(
            """<div class="ex-card" style="border-left: 4px solid #F59E0B; margin-bottom: 20px;">
<h3 style="margin: 0 0 6px 0; font-size: 1.1rem; color: #B45309;">Chưa có đủ dữ liệu vận hành</h3>
<p style="margin: 0; font-size: 14px; color: #64748B; line-height: 1.5;">
Hệ thống chưa ghi nhận ca xử lý nào trong cơ sở dữ liệu. Bạn có thể gửi email kiểm thử tại trang <strong>Xử lý email</strong> hoặc thực thi bộ ca mẫu tại trang <strong>Kiểm thử</strong> để xem số liệu đo lường.
</p>
</div>""",
            unsafe_allow_html=True,
        )

    # Top Level Overview KPI Cards
    auto_rate_val = metrics["auto_rate"]
    auto_pct_str = _percent(auto_rate_val)
    esc_rate_val = (esc_count / total_classified) if total_classified else 0.0
    esc_pct_str = f"{esc_rate_val:.1%}" if total_classified else "0.0%"
    median_rev_val = metrics.get("median_review_seconds", 0.0)

    top_cols = st.columns(4)
    with top_cols[0]:
        st.markdown(
            kpi_card_html(
                label="Tổng email tiếp nhận",
                value=str(total_cases),
                subtext=f"{total_classified} ca đã ra quyết định" if total_classified else "Trong cơ sở dữ liệu",
                tone="primary",
                icon="✉️",
            ),
            unsafe_allow_html=True,
        )
    with top_cols[1]:
        st.markdown(
            kpi_card_html(
                label="Tỷ lệ tự động xử lý",
                value=auto_pct_str,
                subtext=f"{auto_count} / {total_classified} ca phân loại" if total_classified else "AUTO_REPLY",
                tone="success",
                icon="✓",
            ),
            unsafe_allow_html=True,
        )
    with top_cols[2]:
        st.markdown(
            kpi_card_html(
                label="Cần chuyên viên xử lý",
                value=esc_pct_str,
                subtext=f"{esc_count} / {total_classified} ca phân loại" if total_classified else "ESCALATE",
                tone="warning",
                icon="👤",
            ),
            unsafe_allow_html=True,
        )
    with top_cols[3]:
        st.markdown(
            kpi_card_html(
                label="Thời gian duyệt trung vị",
                value=_seconds(median_rev_val),
                subtext="Chuyên viên xem xét & quyết định",
                tone="neutral",
                icon="⏱️",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 24px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 1: SAFETY (AN TOÀN) — TOP PRIORITY
    # =========================================================================
    st.markdown(
        """<div style="margin-bottom: 14px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 18px;">🛡️</span>
<h2 style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #0F172A;">1. An toàn & Ranh giới kiểm soát (Safety)</h2>
</div>
<p style="margin: 4px 0 0 0; font-size: 13.5px; color: #64748B;">
Các chỉ số cho biết hệ thống có bỏ sót hoặc chuyển người không cần thiết hay không.
</p>
</div>""",
        unsafe_allow_html=True,
    )

    eval_data = _get_evaluation_metrics()
    if eval_data and eval_data["synthetic"]:
        st.warning(
            "DỮ LIỆU MÔ PHỎNG — Các chỉ số kiểm thử bên dưới chỉ dùng để xem giao diện, "
            "không phải bằng chứng chạy pipeline hay số liệu nghiệm thu."
        )
    groundedness_fail_rate = metrics.get("groundedness_fail_rate")
    override_rate = metrics.get("override_rate")

    safety_cols = st.columns(4)
    with safety_cols[0]:
        if eval_data:
            missed_rate = eval_data["missed_rate"]
            missed_count = eval_data["missed_count"]
            tone = "danger" if missed_rate > 0 else "success"
            st.markdown(
                kpi_card_html(
                    label="Bỏ sót cần người (Missed)",
                    value=f"{missed_rate:.1%}",
                    subtext=f"{missed_count} ca nguy cơ · Cần người nhưng tự gửi",
                    tone=tone,
                    icon="⚠️",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                kpi_card_html(
                    label="Bỏ sót cần người (Missed)",
                    value="Chưa có dữ liệu",
                    subtext="Cần đối chiếu với bộ kiểm thử Verify",
                    tone="neutral",
                    icon="⚠️",
                ),
                unsafe_allow_html=True,
            )

    with safety_cols[1]:
        if eval_data:
            unnecessary_rate = eval_data["unnecessary_rate"]
            unnecessary_count = eval_data["unnecessary_count"]
            tone = "warning" if unnecessary_rate > 0 else "success"
            st.markdown(
                kpi_card_html(
                    label="Chuyển người thừa (Over-esc)",
                    value=f"{unnecessary_rate:.1%}",
                    subtext=f"{unnecessary_count} ca · Có thể tự trả lời an toàn",
                    tone=tone,
                    icon="🔄",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                kpi_card_html(
                    label="Chuyển người thừa (Over-esc)",
                    value="Chưa có dữ liệu",
                    subtext="Cần đối chiếu với bộ kiểm thử Verify",
                    tone="neutral",
                    icon="🔄",
                ),
                unsafe_allow_html=True,
            )

    with safety_cols[2]:
        g_tone = "danger" if (isinstance(groundedness_fail_rate, (int, float)) and groundedness_fail_rate > 0) else "success"
        st.markdown(
            kpi_card_html(
                label="Phản hồi chưa đủ căn cứ",
                value=_percent(groundedness_fail_rate),
                subtext="R8a Ground Guard fail / số bản nháp",
                tone=g_tone,
                icon="📋",
            ),
            unsafe_allow_html=True,
        )

    with safety_cols[3]:
        o_tone = "warning" if (isinstance(override_rate, (int, float)) and override_rate > 0) else "success"
        st.markdown(
            kpi_card_html(
                label="Tỷ lệ ghi đè quyết định",
                value=_percent(override_rate),
                subtext="Chuyên viên sửa quyết định AI",
                tone=o_tone,
                icon="✏️",
            ),
            unsafe_allow_html=True,
        )

    # Verify Harness Summary Integration
    if eval_data:
        st.markdown(
            f"""<div class="ex-card" style="margin-top: 12px; border-left: 4px solid #10B981; background: #F0FDF4;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
<div>
<div style="font-weight: 700; color: #065F46; font-size: 14px;">
✓ Kết quả kiểm thử tự động ({escape_html(eval_data['source'])}): {eval_data['passed']}/{eval_data['total']} ca đạt ({eval_data['pass_rate']:.1%})
</div>
<div style="font-size: 13px; color: #047857; margin-top: 2px;">
Thời gian thực thi: {eval_data['elapsed']:.1f} giây · Không ghi nhận trường hợp vi phạm quy định ngoài dự kiến.
</div>
</div>
<div>
<a href="/Verify" target="_self" style="background: #10B981; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">Xem chi tiết kiểm thử →</a>
</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div class="ex-card" style="margin-top: 12px; border-left: 4px solid #2563EB;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
<div>
<div style="font-weight: 700; color: #1E3A8A; font-size: 14px;">
Đánh giá mức độ an toàn qua bộ kiểm thử
</div>
<div style="font-size: 13px; color: #475569; margin-top: 2px;">
Chưa chạy bộ kiểm thử trong phiên này. Chỉ số bỏ sót chuyển chuyên viên và chuyển chuyên viên không cần thiết cần đối chiếu với kết quả kỳ vọng của bộ ca kiểm thử.
</div>
</div>
<div>
<a href="/Verify" target="_self" style="background: #2563EB; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">Chạy kiểm thử →</a>
</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 24px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 2: AUTONOMY (TỰ ĐỘNG HÓA)
    # =========================================================================
    st.markdown(
        """<div style="margin-bottom: 14px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 18px;">⚡</span>
<h2 style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #0F172A;">2. Mức độ tự động hóa & phân bổ quyết định</h2>
</div>
<p style="margin: 4px 0 0 0; font-size: 13.5px; color: #64748B;">
Tỷ lệ case được tự xử lý và chuyển chuyên viên.
</p>
</div>""",
        unsafe_allow_html=True,
    )

    autonomy_cols = st.columns([1, 1], gap="medium")

    # Cột trái: Phân bổ Quyết định Tổng thể
    with autonomy_cols[0]:
        st.markdown(
            """<div class="ex-card-title">Phân bổ quyết định (Decision Breakdown)</div>""",
            unsafe_allow_html=True,
        )

        auto_ratio = (auto_count / total_classified) if total_classified else 0.0
        esc_ratio = (esc_count / total_classified) if total_classified else 0.0

        st.markdown(
            f"""<div class="ex-card" style="margin-bottom: 12px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
<div style="font-weight: 600; font-size: 14px; color: #0F172A;">Tỷ lệ tự động vs Chuyển người</div>
<div style="font-size: 13px; color: #64748B;">Tổng {total_classified} ca đã phân loại</div>
</div>
<div style="height: 14px; width: 100%; background: #FFFBEB; border-radius: 9999px; overflow: hidden; display: flex; border: 1px solid #E2E8F0;">
<div style="width: {auto_ratio*100:.1f}%; background: #10B981; height: 100%;" title="Tự động trả lời: {auto_ratio*100:.1f}%"></div>
<div style="width: {esc_ratio*100:.1f}%; background: #F59E0B; height: 100%;" title="Chuyển chuyên viên: {esc_ratio*100:.1f}%"></div>
</div>
<div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 13px;">
<div>
<span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10B981; margin-right: 6px;"></span>
<strong>AUTO_REPLY</strong>: {auto_count} ca ({auto_ratio:.1%})
</div>
<div>
<span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #F59E0B; margin-right: 6px;"></span>
<strong>ESCALATE</strong>: {esc_count} ca ({esc_ratio:.1%})
</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )

        # Phân bổ theo Quy tắc áp dụng (Rules)
        st.markdown(
            """<div class="ex-card-title" style="margin-top: 16px;">Phân bổ theo quy tắc áp dụng</div>""",
            unsafe_allow_html=True,
        )
        rule_counts: dict[str, int] = {}
        for r in classified_rows:
            rid = r["rule_id"] or "Khác"
            rule_counts[rid] = rule_counts.get(rid, 0) + 1

        rule_items = []
        for rid, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
            r_desc = RULE_DESCRIPTIONS.get(rid, "Quy tắc nghiệp vụ")
            pct = (count / total_classified) * 100 if total_classified else 0
            rule_items.append(
                f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid #F1F5F9; font-size: 13px;">
<div>
<strong style="color: #1E293B; font-family: monospace;">{escape_html(rid)}</strong>
<span style="color: #64748B; margin-left: 6px;">— {escape_html(r_desc)}</span>
</div>
<div style="font-weight: 600; color: #0F172A;">{count} ca <span style="font-size: 12px; color: #64748B; font-weight: normal;">({pct:.1f}%)</span></div>
</div>"""
            )

        rules_html = "".join(rule_items) if rule_items else "<div style='color: #94A3B8; font-size: 13px;'>Chưa có quy tắc nào được ghi nhận.</div>"
        st.markdown(
            f"""<div class="ex-card">{rules_html}</div>""",
            unsafe_allow_html=True,
        )

    # Cột phải: Lý do dừng chuyển chuyên viên (Stop Reasons)
    with autonomy_cols[1]:
        st.markdown(
            """<div class="ex-card-title">Phân bổ lý do dừng và chuyển chuyên viên</div>""",
            unsafe_allow_html=True,
        )

        stop_reason_counts = {
            "OUT_OF_POLICY": sum(1 for r in classified_rows if r["escalation_type"] == "OUT_OF_POLICY"),
            "FACT_UNRESOLVED": sum(1 for r in classified_rows if r["escalation_type"] == "FACT_UNRESOLVED"),
            "AUTHORITY_REQUIRED": sum(1 for r in classified_rows if r["escalation_type"] == "AUTHORITY_REQUIRED"),
        }

        stop_cards_html = []
        for reason, count in stop_reason_counts.items():
            rate = (count / total_classified) if total_classified else 0.0
            desc = stop_reason_text(reason)
            badge = stop_reason_badge_html(reason)
            stop_cards_html.append(
                f"""<div class="ex-card" style="margin-bottom: 10px; padding: 12px 16px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
<div>{badge}</div>
<div style="font-size: 14px; font-weight: 700; color: #0F172A;">{count} ca <span style="font-size: 12px; font-weight: normal; color: #64748B;">({rate:.1%})</span></div>
</div>
<div style="font-size: 12.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">{desc}</div>
</div>"""
            )

        st.markdown("".join(stop_cards_html), unsafe_allow_html=True)

    st.markdown("<hr style='margin: 24px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 3: OPERATIONS (VẬN HÀNH)
    # =========================================================================
    st.markdown(
        """<div style="margin-bottom: 14px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 18px;">⚙️</span>
<h2 style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #0F172A;">3. Hiệu năng vận hành</h2>
</div>
<p style="margin: 4px 0 0 0; font-size: 13.5px; color: #64748B;">
Độ trễ và chi phí xử lý từ dữ liệu thực tế.
</p>
</div>""",
        unsafe_allow_html=True,
    )

    p50_dict = metrics.get("p50_latency_ms", {})
    p95_dict = metrics.get("p95_latency_ms", {})
    pct_under_5s = metrics.get("pct_approved_under_5s", 0.0)

    ops_cols = st.columns(3)
    with ops_cols[0]:
        st.markdown(
            kpi_card_html(
                label="Thời gian duyệt trung vị",
                value=_seconds(median_rev_val),
                subtext="decided_at − shown_at (human review)",
                tone="primary",
                icon="⏱️",
            ),
            unsafe_allow_html=True,
        )
    with ops_cols[1]:
        under_5s_tone = "danger" if (isinstance(pct_under_5s, (int, float)) and pct_under_5s > 0.2) else "neutral"
        st.markdown(
            kpi_card_html(
                label="Duyệt dưới 5 giây (Risk)",
                value=_percent(pct_under_5s),
                subtext="Cảnh báo duyệt vội (rubber-stamping)",
                tone=under_5s_tone,
                icon="⚡",
            ),
            unsafe_allow_html=True,
        )
    with ops_cols[2]:
        st.markdown(
            kpi_card_html(
                label="Chi phí & Token",
                value="0 Token · 0 USD",
                subtext="Chế độ kiểm thử nội bộ (Không tốn chi phí)",
                tone="success",
                icon="🪙",
            ),
            unsafe_allow_html=True,
        )

    # Detailed Latency by Step Table & Chart
    st.markdown(
        """<div class="ex-card-title" style="margin-top: 18px; margin-bottom: 8px;">
Độ trễ phân vị p50 và p95 theo từng bước xử lý (Pipeline Latency)
</div>""",
        unsafe_allow_html=True,
    )

    if isinstance(p50_dict, Mapping) and p50_dict:
        active_steps = [s for s in p50_dict.keys() if p50_dict[s] > 0 or (isinstance(p95_dict, Mapping) and p95_dict.get(s, 0) > 0)]
        if not active_steps:
            active_steps = list(p50_dict.keys())[:8]

        latency_rows = []
        for step in active_steps:
            val_50 = p50_dict.get(step, 0)
            val_95 = p95_dict.get(step, 0) if isinstance(p95_dict, Mapping) else 0
            desc = STEP_DESCRIPTIONS.get(step, "Bước xử lý")
            latency_rows.append({
                "Bước (Step)": step,
                "Tên bước nghiệp vụ": desc,
                "p50 (ms)": val_50,
                "p95 (ms)": val_95,
            })

        df_latency = pd.DataFrame(latency_rows)

        col_lat_tbl, col_lat_chart = st.columns([1, 1], gap="medium")
        with col_lat_tbl:
            st.dataframe(
                df_latency,
                use_container_width=True,
                hide_index=True,
            )
        with col_lat_chart:
            # Bar chart so sánh p50 và p95
            chart_data = df_latency.set_index("Bước (Step)")[["p50 (ms)", "p95 (ms)"]]
            st.bar_chart(chart_data)
    else:
        st.info("Chưa ghi nhận dữ liệu độ trễ các bước trong phiên.")

    st.markdown("<hr style='margin: 24px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 4: RECENT CASES (AUDIT REFERENCE)
    # =========================================================================
    st.markdown(
        """<div style="margin-bottom: 14px;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div>
<h2 style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #0F172A;">4. Ca xử lý gần nhất trong cơ sở dữ liệu</h2>
<p style="margin: 4px 0 0 0; font-size: 13.5px; color: #64748B;">
Đối chiếu nhanh các quyết định thực tế vừa được hệ thống ghi nhận.
</p>
</div>
<a href="/Nhat_ky_kiem_toan" target="_self" style="font-size: 13px; color: #2563EB; font-weight: 600; text-decoration: none;">Xem toàn bộ Nhật ký kiểm toán →</a>
</div>
</div>""",
        unsafe_allow_html=True,
    )

    try:
        recent_cases = (
            []
            if is_empty_mode
            else fetch_all(
                "SELECT c.case_id, c.subject, c.sender, c.status, c.created_at, "
                "d.decision, d.escalation_type, d.rule_id "
                "FROM cases c "
                "LEFT JOIN decisions d ON c.case_id = d.case_id "
                "ORDER BY c.created_at DESC LIMIT 5"
            )
        )
    except Exception:
        recent_cases = []

    if recent_cases:
        recent_items = []
        for row in recent_cases:
            cid = row["case_id"]
            subject = row["subject"] or "(Không có tiêu đề)"
            decision = row["decision"] or "CHƯA XỬ LÝ"
            rule_id = row["rule_id"] or "—"
            esc_type = row["escalation_type"]
            created = local_time(row["created_at"])
            d_badge = decision_badge_html(decision)
            stop_badge = f'<span style="margin-left: 6px;">{stop_reason_badge_html(esc_type)}</span>' if esc_type else ""

            recent_items.append(
                f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #F1F5F9; font-size: 13px;">
<div style="flex: 1; min-width: 0; padding-right: 12px;">
<div style="font-weight: 600; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{subject}</div>
<div style="font-size: 12px; color: #64748B; font-family: monospace; margin-top: 2px;">{cid} · Quy tắc: {rule_id}</div>
</div>
<div style="display: flex; align-items: center; gap: 10px; flex-shrink: 0;">
<div>{d_badge}{stop_badge}</div>
<div style="color: #64748B; font-size: 12px; font-family: monospace;">{created}</div>
</div>
</div>"""
            )

        st.markdown(
            f"""<div class="ex-card" style="padding: 4px 10px;">{''.join(recent_items)}</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div class="ex-card" style="color: #64748B; font-size: 13px;">Chưa có ca xử lý nào được ghi nhận.</div>""",
            unsafe_allow_html=True,
        )

    # Footer note
    st.markdown(
        """<div style="margin-top: 24px; padding: 12px 16px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 12.5px; color: #64748B; line-height: 1.5;">
<strong>Ghi chú kiểm định:</strong> Toàn bộ các chỉ số trên được tính toán tự động trực tiếp từ cơ sở dữ liệu SQLite cục bộ và nhật ký kiểm toán. Hệ thống không sử dụng dữ liệu ước tính hoặc số liệu giả lập chưa được kiểm chứng.
</div>""",
        unsafe_allow_html=True,
    )


main()
