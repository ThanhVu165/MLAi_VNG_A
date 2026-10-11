"""Trang Verify (Kiểm thử tự động) — Kiểm tra hành vi AI theo quy định và ranh giới kiểm soát."""

from __future__ import annotations

import json
from dataclasses import asdict
from time import perf_counter
from urllib.parse import quote

import streamlit as st

from core.types import Decision, EscalationType
from ui.presentation import (
    decision_badge_html,
    decision_label,
    inject_app_css,
    page_header_html,
    pass_fail_badge_html,
    stop_reason_badge_html,
)
from verify.harness import CASE_SETS, VerifyResult, load_cases, run_cases


SET_LABELS: dict[str, str] = {
    "verify4": "Bộ kiểm thử 4 ca bắt buộc (Sơ khảo)",
    "escalation5": "Bộ 5 ca kiểm thử chuyển tiếp (Escalation 5)",
    "full15": "Bộ kiểm thử toàn diện 15 ca (Full 15)",
    "m2_combined_dev": "Bộ 12 ca kiểm thử phát triển (M2 Combined)",
}


def _get_deterministic_fixtures(fixture_type: str) -> tuple[tuple[VerifyResult, ...], float, str]:
    """Cung cấp fixture kiểm thử tất định cho visual review/mock mà không gọi LLM thật."""
    if fixture_type == "with_fail":
        # 12 test cases: 10 PASS, 2 FAIL (tương ứng chính xác với visual mockup)
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

    # Default all PASS fixture (4 ca sơ khảo)
    items = (
        VerifyResult("V01", "Quy trình và thang điểm rèn luyện", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1200, "09:00:00 ngày 21/09/2026", "cv_seed_001", "ref_v01", "P05"),
        VerifyResult("V02", "Course withdrawal deadline", None, Decision.AUTO_REPLY, None, Decision.AUTO_REPLY, None, "P05", True, 1400, "09:01:00 ngày 21/09/2026", "cv_seed_001", "ref_v02", "P05"),
        VerifyResult("V03", "Xin nộp phúc khảo muộn vì nhập viện", "Trường hợp nộp phúc khảo ngoài thời hạn do nhập viện, anh/chị có đồng ý tiếp nhận không?", Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, Decision.ESCALATE, EscalationType.AUTHORITY_REQUIRED, "P01", True, 1600, "09:02:00 ngày 21/09/2026", "cv_seed_001", "ref_v03", "P01"),
        VerifyResult("V04", "Đăng ký ký túc xá", "Vấn đề đăng ký ký túc xá không thuộc phạm vi xử lý đào tạo, anh/chị có chuyển đơn vị quản lý KTX không?", Decision.ESCALATE, EscalationType.OUT_OF_POLICY, Decision.ESCALATE, EscalationType.OUT_OF_POLICY, "P02", True, 1500, "09:03:00 ngày 21/09/2026", "cv_seed_001", "ref_v04", "P02"),
    )
    return items, 5.7, "verify4"


def main() -> None:
    inject_app_css()

    # 1. Header
    st.markdown(
        page_header_html(
            "AUTOMATED VERIFICATION & BENCHMARK",
            "Verify",
            "Chạy bộ kiểm thử các tình huống mẫu để kiểm tra hành vi AI theo quy định, ranh giới và quy trình kiểm soát.",
        ),
        unsafe_allow_html=True,
    )

    with st.expander("ℹ️ Hướng dẫn — Xem cách diễn giải kết quả kiểm thử", expanded=False):
        st.markdown(
            """
            - **AUTO_REPLY:** Hệ thống đối chiếu đủ căn cứ hợp lệ đang có hiệu lực và tự động soạn thảo phản hồi kèm trích dẫn.
            - **ESCALATE:** Hệ thống phát hiện vượt thẩm quyền (`AUTHORITY_REQUIRED`), ngoài quy định (`OUT_OF_POLICY`), hoặc thiếu dữ kiện (`FACT_UNRESOLVED`) và dừng lại để chuyên viên xử lý.
            - **PASS:** Hành vi thực tế khớp hoàn toàn với mong đợi (về quyết định, loại chuyển tiếp và quy tắc áp dụng).
            - **FAIL:** Hành vi thực tế không khớp với mong đợi, cần kiểm tra lại quy định hoặc logic xử lý.
            - **Audit Trail:** Toàn bộ quá trình chạy kiểm thử được ghi nhận đầy đủ trong Nhật ký kiểm toán như email thật.
            """
        )

    # 2. Primary Run Card
    with st.container():
        st.markdown(
            """
            <div class="ex-card" style="border-left: 4px solid #2563EB; margin-bottom: 16px;">
                <div style="display: flex; align-items: flex-start; gap: 14px;">
                    <div style="font-size: 28px; line-height: 1;">🧪</div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 4px 0; font-size: 1.05rem; font-weight: 700; color: #0F172A;">
                            Bộ kiểm thử mô phỏng các tình huống thực tế
                        </h3>
                        <p style="margin: 0; font-size: 13.5px; color: #64748B; line-height: 1.5;">
                            Bao gồm email thường quy, ngoài chính sách, cần thẩm quyền, thiếu dữ kiện... để đánh giá độ an toàn, tuân thủ và hiệu quả xử lý.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_select, col_btn = st.columns([7, 3], vertical_alignment="bottom")
    with col_select:
        case_set = st.selectbox(
            "Lựa chọn bộ kiểm thử",
            list(SET_LABELS.keys()),
            format_func=lambda k: SET_LABELS[k],
            index=0,
            key="verify_case_set_selector",
        )
    with col_btn:
        run_clicked = st.button("▶ Chạy kiểm thử", type="primary", use_container_width=True, key="run_verify_main_btn")
        st.caption("Thời gian dự kiến: ~5–15 giây")

    # 3. Execution logic
    if run_clicked:
        # Xóa query param fixture nếu có để chạy thực tế
        if "fixture" in st.query_params:
            del st.query_params["fixture"]
        with st.spinner("Đang chạy kiểm thử qua pipeline chuẩn..."):
            started = perf_counter()
            try:
                results = run_cases(CASE_SETS[case_set], run_name=case_set)
                elapsed = perf_counter() - started
                st.session_state["verification_result"] = (results, elapsed, case_set)
            except Exception as error:
                st.error(f"Sự cố khi thực thi bộ kiểm thử: {error}")

    # 4. Determine Active Data (Real vs Deterministic Fixture)
    fixture_param = st.query_params.get("fixture")
    if fixture_param in {"all_pass", "with_fail"}:
        results, elapsed, active_set = _get_deterministic_fixtures(fixture_param)
    elif "verification_result" in st.session_state:
        results, elapsed, active_set = st.session_state["verification_result"]
    else:
        results, elapsed, active_set = None, 0.0, case_set

    # 5. Empty State (Chưa chạy)
    if results is None:
        st.markdown("<hr style='margin: 20px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="ex-card-title">📋 Danh sách các tình huống chuẩn bị chạy ({SET_LABELS[case_set]})</div>',
            unsafe_allow_html=True,
        )
        try:
            cases_manifest = load_cases(CASE_SETS[case_set])
            manifest_data = [
                {
                    "#": idx + 1,
                    "Mã ca": c.case_id,
                    "Tiêu đề email": c.input.subject,
                    "Quyết định kỳ vọng": decision_label(c.expected_decision, c.expected_type),
                    "Nội dung tóm tắt": (c.input.body[:90] + "...") if len(c.input.body) > 90 else c.input.body,
                }
                for idx, c in enumerate(cases_manifest)
            ]
            st.dataframe(manifest_data, hide_index=True, use_container_width=True)
        except Exception:
            st.info(f"Bộ ca kiểm thử: {SET_LABELS[case_set]}. Bấm '▶ Chạy kiểm thử' để bắt đầu.")
        return

    # 6. Completed State — Summary-first KPI Cards
    total = len(results)
    pass_count = sum(1 for r in results if r.passed)
    fail_count = total - pass_count
    pass_pct = (pass_count / total * 100) if total else 0.0
    fail_pct = (fail_count / total * 100) if total else 0.0
    avg_per_case = (elapsed / total) if total else 0.0

    st.markdown("<hr style='margin: 20px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.markdown(
            f"""
            <div class="ex-kpi-card">
                <div class="ex-kpi-label">📄 Tổng test cases</div>
                <div class="ex-kpi-val" style="color: #0F172A;">{total}</div>
                <div class="ex-kpi-sub">Đã chạy tất cả</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_kpi2:
        st.markdown(
            f"""
            <div class="ex-kpi-card" style="border-top: 3px solid #10B981;">
                <div class="ex-kpi-label" style="color: #047857;">✓ PASS</div>
                <div class="ex-kpi-val" style="color: #047857;">{pass_count}</div>
                <div class="ex-kpi-sub" style="color: #059669; font-weight: 600;">{pass_pct:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_kpi3:
        st.markdown(
            f"""
            <div class="ex-kpi-card" style="border-top: 3px solid #EF4444;">
                <div class="ex-kpi-label" style="color: #B91C1C;">✕ FAIL</div>
                <div class="ex-kpi-val" style="color: #B91C1C;">{fail_count}</div>
                <div class="ex-kpi-sub" style="color: #DC2626; font-weight: 600;">{fail_pct:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_kpi4:
        st.markdown(
            f"""
            <div class="ex-kpi-card">
                <div class="ex-kpi-label">⏱️ Tổng thời gian chạy</div>
                <div class="ex-kpi-val" style="color: #0F172A;">{elapsed:.1f}s</div>
                <div class="ex-kpi-sub">~ {avg_per_case:.1f}s / test case</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 7. Prominent Failure Alert Banner (Nếu có ca FAIL)
    if fail_count > 0:
        st.markdown(
            f"""
            <div class="ex-fail-banner">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="font-size: 24px; line-height: 1;">⚠️</div>
                    <div>
                        <div style="font-weight: 700; color: #991B1B; font-size: 14.5px;">Có {fail_count} test case chưa đạt</div>
                        <div style="color: #B91C1C; font-size: 13px;">Vui lòng xem chi tiết từng test case bên dưới để hiểu nguyên nhân và điều chỉnh quy định hoặc logic xử lý.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 8. Filter Bar
    filter_options = [f"Tất cả ({total})", f"PASS ({pass_count})"]
    if fail_count > 0:
        filter_options.append(f"FAIL ({fail_count})")
    filter_options.extend(["AUTO_REPLY", "ESCALATE"])

    col_filter, col_down = st.columns([8, 2], vertical_alignment="center")
    with col_filter:
        active_filter = st.radio(
            "Lọc kết quả",
            filter_options,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="verify_filter_radio",
        )
    with col_down:
        st.download_button(
            "📥 Tải JSON",
            json.dumps(
                {
                    "set": active_set,
                    "elapsed_seconds": elapsed,
                    "total": total,
                    "passed": pass_count,
                    "failed": fail_count,
                    "results": [asdict(r) for r in results],
                },
                ensure_ascii=False,
                indent=2,
            ),
            file_name=f"verify_{active_set}_results.json",
            mime="application/json",
            use_container_width=True,
        )

    # Lọc danh sách ca
    filtered_results = list(results)
    if active_filter:
        if active_filter.startswith("PASS"):
            filtered_results = [r for r in filtered_results if r.passed]
        elif active_filter.startswith("FAIL"):
            filtered_results = [r for r in filtered_results if not r.passed]
        elif active_filter == "AUTO_REPLY":
            filtered_results = [r for r in filtered_results if r.expected_decision == Decision.AUTO_REPLY]
        elif active_filter == "ESCALATE":
            filtered_results = [r for r in filtered_results if r.expected_decision == Decision.ESCALATE]

    # 9. Compact Case Results Table (Render trực tiếp HTML đồng bộ, màu sắc chuẩn mockup)
    st.markdown('<div class="ex-card-title" style="margin-top: 14px;">📋 Bảng kết quả chi tiết từng tình huống</div>', unsafe_allow_html=True)
    rows_html: list[str] = []
    for idx, r in enumerate(filtered_results, start=1):
        row_bg = "#FEF2F2" if not r.passed else ("#FFFFFF" if idx % 2 != 0 else "#F8FAFC")
        rows_html.append(
            f'<tr style="border-bottom: 1px solid #E2E8F0; background: {row_bg};">'
            f'<td style="padding: 10px 14px; color: #64748B;">{idx}</td>'
            f'<td style="padding: 10px 14px; font-weight: 600; font-family: monospace; color: #0F172A;">{r.case_id}</td>'
            f'<td style="padding: 10px 14px; color: #1E293B;">{r.subject}</td>'
            f'<td style="padding: 10px 14px;">{decision_badge_html(r.expected_decision.value)}</td>'
            f'<td style="padding: 10px 14px;">{decision_badge_html(r.actual_decision.value)}</td>'
            f'<td style="padding: 10px 14px;">{pass_fail_badge_html(r.passed)}</td>'
            f'<td style="padding: 10px 14px; color: #64748B;">{r.elapsed_ms / 1000:.1f}s</td>'
            f'</tr>'
        )
    table_rows = "".join(rows_html)
    table_html = (
        '<div style="overflow-x: auto; border: 1px solid #E2E8F0; border-radius: 8px; background: #FFFFFF; margin-bottom: 16px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);">'
        '<table style="width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: left;">'
        '<thead>'
        '<tr style="background: #F8FAFC; border-bottom: 1px solid #E2E8F0; color: #475569; font-weight: 600;">'
        '<th style="padding: 11px 14px; width: 40px;">#</th>'
        '<th style="padding: 11px 14px; width: 140px;">Mã test case</th>'
        '<th style="padding: 11px 14px;">Tình huống</th>'
        '<th style="padding: 11px 14px; width: 190px;">Quyết định kỳ vọng</th>'
        '<th style="padding: 11px 14px; width: 190px;">Kết quả thực tế</th>'
        '<th style="padding: 11px 14px; width: 100px;">Trạng thái</th>'
        '<th style="padding: 11px 14px; width: 90px;">Thời gian</th>'
        '</tr>'
        '</thead>'
        f'<tbody>{table_rows}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # 10. Selected Case Inspector (Expected vs Actual)
    st.markdown("<hr style='margin: 20px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    st.markdown('<div class="ex-card-title">🔍 Đối chiếu chi tiết Expected vs Actual</div>', unsafe_allow_html=True)

    case_ids = [r.case_id for r in filtered_results]
    if not case_ids:
        st.info("Không có ca nào phù hợp với bộ lọc hiện tại.")
        return

    inspect_target = st.query_params.get("inspect")
    if inspect_target and inspect_target in case_ids:
        default_idx = case_ids.index(inspect_target)
    else:
        # Default to first failure if failures exist, otherwise 0
        first_fail = next((r.case_id for r in filtered_results if not r.passed and r.case_id in case_ids), None)
        if first_fail:
            default_idx = case_ids.index(first_fail)
        else:
            default_idx = 0

    inspector_key = f"select_case_inspector_{inspect_target or ('fail' if fail_count > 0 else 'all')}"
    selected_id = st.selectbox(
        "Chọn test case để đối chiếu",
        case_ids,
        index=default_idx,
        format_func=lambda cid: next(
            f"[{'PASS' if r.passed else 'FAIL'}] {r.case_id} — {r.subject}"
            for r in filtered_results
            if r.case_id == cid
        ),
        label_visibility="collapsed",
        key=inspector_key,
    )
    selected_result = next((r for r in filtered_results if r.case_id == selected_id), filtered_results[0])

    # Card so sánh Expected vs Actual
    with st.container():
        st.markdown(
            f"""
            <div class="ex-card" style="border-top: 3px solid {'#10B981' if selected_result.passed else '#EF4444'};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">{selected_result.case_id}: {selected_result.subject}</span>
                    </div>
                    <div>
                        {pass_fail_badge_html(selected_result.passed)}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_exp, col_act = st.columns(2)
    with col_exp:
        st.markdown(
            f"""
            <div class="ex-card" style="background: #F8FAFC;">
                <div class="ex-card-title" style="color: #2563EB;">🎯 Kỳ vọng (Expected)</div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 13px; color: #64748B;">Quyết định:</span><br/>
                    {decision_badge_html(selected_result.expected_decision.value)}
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 13px; color: #64748B;">Lý do / Phân loại:</span><br/>
                    {stop_reason_badge_html(selected_result.expected_type.value) if selected_result.expected_type else '<span class="ex-badge ex-badge-neutral">Không phân loại</span>'}
                </div>
                <div>
                    <span style="font-size: 13px; color: #64748B;">Mã quy tắc kỳ vọng:</span>
                    <code>{selected_result.expected_rule_id or 'Không ràng buộc'}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_act:
        st.markdown(
            f"""
            <div class="ex-card" style="background: #F8FAFC;">
                <div class="ex-card-title" style="color: #475569;">⚙️ Thực tế (Actual)</div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 13px; color: #64748B;">Quyết định:</span><br/>
                    {decision_badge_html(selected_result.actual_decision.value)}
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 13px; color: #64748B;">Lý do / Phân loại:</span><br/>
                    {stop_reason_badge_html(selected_result.actual_type.value) if selected_result.actual_type else '<span class="ex-badge ex-badge-neutral">Không phân loại</span>'}
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 13px; color: #64748B;">Mã quy tắc áp dụng:</span>
                    <code>{selected_result.rule_id}</code>
                </div>
                <div>
                    <span style="font-size: 13px; color: #64748B;">Thời gian thực thi:</span>
                    <code>{selected_result.elapsed_ms} ms</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not selected_result.passed:
        st.markdown(
            f"""
            <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 6px; padding: 12px 16px; margin: 10px 0; font-size: 13.5px; color: #991B1B;">
                ⚠️ <strong>Phát hiện sai lệch:</strong> Kỳ vọng là <strong>{decision_label(selected_result.expected_decision, selected_result.expected_type)}</strong> nhưng kết quả thực tế là <strong>{decision_label(selected_result.actual_decision, selected_result.actual_type)}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if selected_result.question:
        st.markdown(
            f"""
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; font-size: 13px; color: #92400E;">
                ❓ <strong>Câu hỏi tham vấn chuyên viên:</strong> {selected_result.question}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.link_button(
        f"🔍 Xem nhật ký kiểm toán (Audit Trail) của ca {selected_result.case_id} →",
        f"/Nhat_ky_kiem_toan?case_id={quote(selected_result.case_ref)}",
        use_container_width=True,
    )


main()
