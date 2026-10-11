"""Nhật ký kiểm toán & Truy vết quyết định — Lịch sử sự kiện, căn cứ đối chiếu và can thiệp quản trị."""

from __future__ import annotations

import json
from dataclasses import asdict
from urllib.parse import quote

import streamlit as st

from core.controls import override_decision
from core.pipeline import load_result
from core.types import Decision
from core.worker import retry_case
from corpus.api import get_chunk
from infra.audit import events_for_case, recent_events
from infra.db import fetch_all, fetch_one
from ui.presentation import (
    ACTION_LABELS,
    action_badge_html,
    actor_badge_html,
    inject_app_css,
    local_time,
    page_header_html,
    readable_text,
    status_badge_html,
    status_label,
)


def _build_story_summary(case: dict, events: list) -> list[str]:
    """Tạo chuỗi tóm tắt tiến trình tự nhiên (Story of the Case) từ các sự kiện thực tế."""
    bullets: list[str] = []
    # 1. Tiếp nhận
    recv_ev = next((e for e in events if e.action == "CASE_RECEIVED"), None)
    recv_time = local_time(recv_ev.ts if recv_ev else case.get("received_at"))
    bullets.append(f"<strong>Tiếp nhận:</strong> Email gửi từ <code>{case.get('sender', 'ẩn danh')}</code> lúc {recv_time}.")

    # 2. Đối chiếu căn cứ
    evid_ev = next((e for e in events if e.action in ("EVIDENCE_RETRIEVED", "EVIDENCE_VALIDATED")), None)
    if evid_ev:
        src_cnt = len(evid_ev.sources or [])
        bullets.append(f"<strong>Đối chiếu căn cứ:</strong> Hệ thống đã rà soát {src_cnt} đoạn quy định có hiệu lực ({evid_ev.corpus_version or 'phiên bản chuẩn'}).")

    # 3. Quyết định AI ban đầu
    dec_ev = next((e for e in events if e.action == "POLICY_DECIDED"), None)
    if dec_ev:
        rule_info = f" (theo quy tắc <code>{dec_ev.rule_id}</code>)" if dec_ev.rule_id else ""
        bullets.append(f"<strong>Quyết định AI:</strong> Đưa ra phương án xử lý{rule_info}: {readable_text(dec_ev.reason or 'Theo quy định.')}")

    # 4. Can thiệp con người (nếu có)
    human_evs = [e for e in events if e.action in ("HUMAN_DECISION", "OVERRIDE_DECISION", "HUMAN_APPROVED_SEND", "HUMAN_REJECTED_DRAFT")]
    if human_evs:
        for he in human_evs:
            act_name = ACTION_LABELS.get(he.action, he.action)
            bullets.append(f"<strong>Can thiệp con người ({he.actor}):</strong> {act_name} — {readable_text(he.reason or 'Đã xác nhận.')}")
    else:
        bullets.append("<strong>Can thiệp con người:</strong> Chưa có can thiệp ngoại lệ từ chuyên viên hoặc quản trị viên.")

    # 5. Kết quả hiện tại
    status_str = status_label(case.get("status", "UNKNOWN"))
    bullets.append(f"<strong>Trạng thái hiện hành:</strong> <code>{status_str}</code>.")
    return bullets


def main() -> None:
    inject_app_css()

    # 1. Header matching mockup
    header_col1, header_col2 = st.columns([8, 2], vertical_alignment="center")
    with header_col1:
        st.markdown(
            page_header_html(
                "Audit & Traceability",
                "Nhật ký kiểm toán",
                "Theo dõi và truy vết toàn bộ hành động của AI và con người trong quá trình xử lý email.",
            ),
            unsafe_allow_html=True,
        )
    with header_col2:
        all_recent = recent_events(limit=200)
        st.download_button(
            "📥 Xuất báo cáo",
            json.dumps([asdict(e) for e in all_recent], ensure_ascii=False, indent=2),
            file_name="nhat-ky-kiem-toan-exodia.json",
            mime="application/json",
            use_container_width=True,
            key="btn_export_all_audit",
        )

    with st.expander("ℹ️ Hướng dẫn — Xem cách đọc nhật ký kiểm toán và thẩm quyền", expanded=False):
        st.markdown(
            """
            - **Tính bất biến (Immutability):** Toàn bộ sự kiện kiểm toán được ghi nhận tuần tự cùng dấu thời gian chính xác UTC/Giờ VN và không thể sửa đổi hoặc xóa bỏ.
            - **Chủ thể thực hiện (Actor):**
              - `Hệ thống (SYSTEM)`: Tác vụ tự động hóa (tiếp nhận, đối chiếu căn cứ, lập lịch gửi).
              - `Chuyên viên (HUMAN)`: Cán bộ phòng ban phê duyệt phản hồi hoặc xử lý các ca escalation.
              - `Quản trị viên (ADMIN)`: Người có thẩm quyền điều chỉnh quyết định hoặc xử lý lại ca.
            - **Quy trình can thiệp:** Mọi thao tác điều chỉnh quyết định đều yêu cầu lý do giải trình, bước xác nhận hai lớp (Two-Step Confirmation) và lưu dấu vết vĩnh viễn.
            """
        )

    # 2. Truy xuất dữ liệu ca từ Database
    raw_cases = fetch_all("SELECT * FROM cases ORDER BY rowid DESC LIMIT 200")
    cases: list[dict] = [dict(c) for c in raw_cases]

    # Kiểm tra query parameter ?case_id=... (Deep-link từ Verify hoặc Human Review)
    query_id = st.query_params.get("case_id")
    if isinstance(query_id, str) and query_id:
        existing_ids = {c["case_id"] for c in cases}
        if query_id not in existing_ids:
            older = fetch_one("SELECT * FROM cases WHERE case_id = ?", (query_id,))
            if older is not None:
                cases.insert(0, dict(older))

    # Xác định ca có can thiệp người hay tự động
    try:
        human_ev_rows = fetch_all(
            "SELECT DISTINCT case_id FROM audit_events WHERE action IN ('HUMAN_DECISION', 'OVERRIDE_DECISION', 'HUMAN_APPROVED_SEND', 'HUMAN_REJECTED_DRAFT')"
        )
        human_case_ids = {r["case_id"] for r in human_ev_rows if r["case_id"]}
    except Exception:
        human_case_ids = set()

    for c in cases:
        cid = c["case_id"]
        c["has_human"] = (cid in human_case_ids) or (c.get("status") in ("AWAITING_HUMAN", "PENDING_APPROVAL"))

    total_cases_count = len(cases)
    human_cases_count = sum(1 for c in cases if c.get("has_human"))
    auto_cases_count = total_cases_count - human_cases_count
    human_pct = round((human_cases_count / total_cases_count * 100)) if total_cases_count else 0
    auto_pct = 100 - human_pct if total_cases_count else 0

    latest_time_str = local_time(cases[0]["received_at"]).split("ngày")[0].strip() if cases else "Chưa có"
    latest_id_str = cases[0]["case_id"] if cases else "N/A"

    # KPI Metric Cards matching 03_audit_BASE.png
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(
            '<div class="ex-kpi-card">'
            '<div class="ex-kpi-label">📄 Tổng số case</div>'
            f'<div class="ex-kpi-val" style="color: #0F172A;">{total_cases_count:,}</div>'
            '<div class="ex-kpi-sub">Hồ sơ đã tiếp nhận</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            '<div class="ex-kpi-card">'
            '<div class="ex-kpi-label">👥 Có can thiệp người</div>'
            f'<div class="ex-kpi-val" style="color: #D97706;">{human_cases_count} <span style="font-size: 15px; font-weight: 500; color: #64748B;">({human_pct}%)</span></div>'
            '<div class="ex-kpi-sub">Cần chuyên viên / quản trị</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with kpi3:
        st.markdown(
            '<div class="ex-kpi-card">'
            '<div class="ex-kpi-label">⚙️ Tự động xử lý</div>'
            f'<div class="ex-kpi-val" style="color: #059669;">{auto_cases_count} <span style="font-size: 15px; font-weight: 500; color: #64748B;">({auto_pct}%)</span></div>'
            '<div class="ex-kpi-sub">Đã hoàn tất tự động</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with kpi4:
        st.markdown(
            '<div class="ex-kpi-card">'
            '<div class="ex-kpi-label">🕒 Hoạt động gần đây</div>'
            f'<div class="ex-kpi-val" style="font-size: 18px; color: #2563EB; padding-top: 6px;">{latest_time_str}</div>'
            f'<div class="ex-kpi-sub">Ca: {latest_id_str}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # 3. Bố cục Split-pane (Cột trái: Danh sách Ca | Cột phải: Workspace Chi tiết & Dòng thời gian)
    col_left, col_right = st.columns([4, 6], gap="medium")

    # ==================== CỘT TRÁI: DANH SÁCH CA ====================
    with col_left:
        st.markdown('<div class="ex-card-title">📋 Hàng đợi kiểm toán & Hồ sơ ca</div>', unsafe_allow_html=True)

        search_query = st.text_input(
            "Tìm kiếm ca hoặc sự kiện",
            placeholder="Tìm theo mã case, email, tiêu đề...",
            label_visibility="collapsed",
            key="audit_search_input",
        ).strip().lower()

        type_filter = st.radio(
            "Phân loại hồ sơ",
            [
                f"Tất cả ({total_cases_count})",
                f"Có can thiệp người ({human_cases_count})",
                f"Tự động xử lý ({auto_cases_count})",
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="audit_type_filter",
        )

        col_fa, col_fs = st.columns(2)
        with col_fa:
            filter_actor = st.selectbox(
                "Chủ thể",
                ["Tất cả chủ thể", "Hệ thống (SYSTEM)", "Chuyên viên (HUMAN)", "Quản trị viên (ADMIN)"],
                index=0,
                key="audit_filter_actor",
            )
        with col_fs:
            filter_status = st.selectbox(
                "Trạng thái",
                ["Tất cả trạng thái", "SENT", "AWAITING_HUMAN", "PENDING_APPROVAL", "INVALID_INPUT"],
                index=0,
                key="audit_filter_status",
            )

        # Áp dụng bộ lọc
        filtered_cases = list(cases)
        if "Có can thiệp người" in type_filter:
            filtered_cases = [c for c in filtered_cases if c.get("has_human")]
        elif "Tự động xử lý" in type_filter:
            filtered_cases = [c for c in filtered_cases if not c.get("has_human")]

        if search_query:
            filtered_cases = [
                c for c in filtered_cases
                if search_query in c["case_id"].lower()
                or search_query in (c.get("subject") or "").lower()
                or search_query in (c.get("sender") or "").lower()
            ]

        if filter_status != "Tất cả trạng thái":
            filtered_cases = [c for c in filtered_cases if c["status"] == filter_status]

        GLOBAL_OPTION = "__GLOBAL_RECENT_EVENTS__"
        options = [GLOBAL_OPTION] + [c["case_id"] for c in filtered_cases]

        default_idx = 0
        if query_id and query_id in options:
            default_idx = options.index(query_id)
        elif len(options) > 1:
            default_idx = 1

        case_map = {c["case_id"]: c for c in cases}

        def _format_option(opt: str) -> str:
            if opt == GLOBAL_OPTION:
                return "🌐 Toàn bộ hoạt động hệ thống gần đây"
            c = case_map.get(opt)
            if c:
                sub = c.get("subject", "")
                sub_short = (sub[:30] + "...") if len(sub) > 30 else sub
                return f"[{c.get('status', '')}] {c['case_id']} — {sub_short}"
            return opt

        selected_option = st.selectbox(
            "Chọn hồ sơ kiểm toán",
            options,
            index=default_idx,
            format_func=_format_option,
            label_visibility="collapsed",
            key="audit_case_selector",
        )

        st.caption(f"Hiển thị {len(filtered_cases)}/{len(cases)} ca phù hợp")

        # Danh sách thẻ compact xem nhanh ở cột trái
        st.markdown("<div style='max-height: 600px; overflow-y: auto; padding-right: 4px;'>", unsafe_allow_html=True)
        for c in filtered_cases[:30]:
            is_active = (c["case_id"] == selected_option)
            border_color = "#2563EB" if is_active else "#E2E8F0"
            bg_color = "#EFF6FF" if is_active else "#FFFFFF"
            human_tag = (
                '<span style="background: #FEF3C7; color: #92400E; font-size: 10.5px; font-weight: 600; padding: 1px 6px; border-radius: 4px;">Có can thiệp người</span>'
                if c.get("has_human")
                else '<span style="background: #ECFDF5; color: #065F46; font-size: 10.5px; font-weight: 600; padding: 1px 6px; border-radius: 4px;">Tự động xử lý</span>'
            )
            card_html = (
                f'<div style="background: {bg_color}; border: 1.5px solid {border_color}; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">'
                f'<span style="font-family: monospace; font-size: 11.5px; font-weight: 700; color: #1E40AF;">{c["case_id"]}</span>'
                f'<div style="display: flex; gap: 4px;">{status_badge_html(c["status"])} {human_tag}</div>'
                f'</div>'
                f'<div style="font-size: 13px; font-weight: 600; color: #0F172A; margin-bottom: 3px; line-height: 1.35;">{c["subject"]}</div>'
                f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; color: #64748B;">'
                f'<span>👤 {c["sender"][:22]}...</span>'
                f'<span>{local_time(c["received_at"]).split("ngày")[0]}</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ==================== CỘT PHẢI: WORKSPACE CHI TIẾT ====================
    with col_right:
        if selected_option == GLOBAL_OPTION:
            # Chế độ xem toàn cục các sự kiện gần đây
            st.markdown('<div class="ex-card-title">🌐 Toàn bộ hoạt động hệ thống gần đây</div>', unsafe_allow_html=True)
            all_events = recent_events(limit=150)
            if filter_actor != "Tất cả chủ thể":
                actor_prefix = filter_actor.split("(")[-1].rstrip(")")
                all_events = [e for e in all_events if e.actor.startswith(actor_prefix)]

            if not all_events:
                st.info("Chưa có sự kiện nào được ghi nhận phù hợp với bộ lọc.")
            else:
                st.markdown(
                    f'<div class="ex-card">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                    f'<span style="font-weight: 600; color: #0F172A;">Tổng số sự kiện gần đây: {len(all_events)}</span>'
                    f'<span style="font-size: 12px; color: #64748B;">Múi giờ Việt Nam (UTC+7)</span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                for ev in all_events[:40]:
                    action_label = ACTION_LABELS.get(ev.action, ev.action)
                    with st.expander(f"{local_time(ev.ts)} · {ev.actor} · {action_label}", expanded=False):
                        st.markdown(f"**Mã ca:** `{ev.case_id or 'Hệ thống chung'}`")
                        st.markdown(f"**Lý do:** {readable_text(ev.reason or 'Không có ghi chú.')}")
                        if ev.rule_id:
                            st.markdown(f"**Mã quy tắc:** `{ev.rule_id}`")
                        if ev.sources:
                            st.caption(f"Căn cứ: {', '.join(ev.sources)}")
                        if ev.case_id:
                            st.link_button(f"🔍 Xem chi tiết ca {ev.case_id}", f"/Nhat_ky_kiem_toan?case_id={quote(ev.case_id)}")

                st.download_button(
                    "📥 Tải toàn bộ nhật ký hệ thống (JSON)",
                    json.dumps([asdict(e) for e in all_events], ensure_ascii=False, indent=2),
                    file_name="nhat-ky-toan-bo-he-thong.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            # Chế độ xem chi tiết một ca kiểm toán cụ thể
            selected_case = next(c for c in cases if c["case_id"] == selected_option)
            case_id = selected_case["case_id"]
            events = events_for_case(case_id)

            # A. Case Header Card matching 03_audit_BASE.png
            human_tag_header = (
                '<span style="background: #FEF3C7; color: #92400E; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid #FDE68A;">Có can thiệp người</span>'
                if selected_case.get("has_human")
                else '<span style="background: #ECFDF5; color: #065F46; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid #A7F3D0;">Tự động xử lý</span>'
            )
            header_html = (
                f'<div class="ex-card" style="border-top: 3px solid #2563EB;">'
                f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">'
                f'<div>'
                f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
                f'<span style="font-family: monospace; font-size: 12px; font-weight: 700; color: #2563EB; background: #EFF6FF; padding: 2px 8px; border-radius: 4px;">{case_id}</span>'
                f'{status_badge_html(selected_case["status"])} {human_tag_header}'
                f'</div>'
                f'<h2 style="margin: 4px 0 2px 0; font-size: 1.25rem; font-weight: 700; color: #0F172A;">{selected_case["subject"]}</h2>'
                f'<div style="font-size: 13px; color: #64748B;">'
                f'👤 Người gửi: <strong style="color: #1E293B;">{selected_case["sender"]}</strong> · 📅 Nhận lúc: {local_time(selected_case["received_at"])}'
                f'</div>'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(header_html, unsafe_allow_html=True)

            # Nút liên kết nghiệp vụ nhanh
            col_lk1, col_lk2 = st.columns(2)
            with col_lk1:
                st.link_button("✉️ Xem nội dung & phản hồi", f"/?case_id={quote(case_id)}", use_container_width=True)
            with col_lk2:
                if selected_case["status"] in ("AWAITING_HUMAN", "PENDING_APPROVAL"):
                    st.link_button("👤 Mở trong Hàng chờ duyệt", f"/Hang_cho_duyet?case_id={quote(case_id)}", use_container_width=True)
                else:
                    st.link_button("🧪 Chạy kiểm thử Verify", "/Verify", use_container_width=True)

            # B. Story of the Case (Tiến trình tóm tắt tự nhiên)
            st.markdown('<div class="ex-card-title" style="margin-top: 14px;">📖 Tiến trình xử lý (Story of the Case)</div>', unsafe_allow_html=True)
            story_bullets = _build_story_summary(selected_case, events)
            story_html = "".join(f"<div style='margin-bottom: 6px; font-size: 13.5px; color: #1E293B; line-height: 1.5;'>• {bullet}</div>" for bullet in story_bullets)
            st.markdown(
                f'<div class="ex-card" style="background: #F8FAFC; border-left: 3px solid #10B981;">{story_html}</div>',
                unsafe_allow_html=True,
            )

            # C. Case Timeline (Dòng thời gian sự kiện)
            st.markdown(f'<div class="ex-card-title" style="margin-top: 14px;">⏱️ Dòng thời gian sự kiện ({len(events)} sự kiện)</div>', unsafe_allow_html=True)
            if not events:
                st.info("Chưa có sự kiện kiểm toán nào được ghi nhận cho ca này.")
            else:
                timeline_items_html: list[str] = []
                for ev in events:
                    dot_class = "ex-timeline-dot-admin" if ev.actor.startswith("ADMIN:") else ("ex-timeline-dot-human" if ev.actor.startswith("HUMAN:") else "ex-timeline-dot-system")
                    badge_actor = actor_badge_html(ev.actor)
                    badge_action = action_badge_html(ev.action)

                    detail_lines: list[str] = []
                    if ev.reason:
                        detail_lines.append(f"<div style='margin-bottom: 3px;'><strong>Lý do / Giải trình:</strong> {readable_text(ev.reason)}</div>")
                    if ev.rule_id:
                        detail_lines.append(f"<div style='margin-bottom: 3px;'><strong>Mã quy tắc áp dụng:</strong> <span style='font-family: monospace; font-weight: 600; color: #047857;'>{ev.rule_id}</span></div>")
                    if ev.sources:
                        detail_lines.append(f"<div style='font-size: 12px; color: #64748B;'><strong>Căn cứ:</strong> {', '.join(ev.sources)}</div>")

                    body_content = "".join(detail_lines) if detail_lines else "<div style='color: #64748B;'>Đã hoàn tất bước xử lý tiêu chuẩn.</div>"

                    extra_border = ""
                    if ev.action == "OVERRIDE_DECISION":
                        extra_border = "border-left: 3px solid #7C3AED;"
                    elif ev.action == "HUMAN_APPROVED_SEND":
                        extra_border = "border-left: 3px solid #10B981;"

                    item_html = (
                        f'<div class="ex-timeline-item">'
                        f'<div class="ex-timeline-dot {dot_class}"></div>'
                        f'<div class="ex-timeline-header">'
                        f'<div class="ex-timeline-title">{badge_action} {badge_actor}</div>'
                        f'<span class="ex-timeline-time">{local_time(ev.ts)}</span>'
                        f'</div>'
                        f'<div class="ex-timeline-body" style="{extra_border}">{body_content}</div>'
                        f'</div>'
                    )
                    timeline_items_html.append(item_html)

                timeline_html = f'<div class="ex-timeline">{"".join(timeline_items_html)}</div>'
                st.markdown(timeline_html, unsafe_allow_html=True)

            # D. Căn cứ áp dụng (Evidence & Trích dẫn gốc)
            st.markdown('<div class="ex-card-title" style="margin-top: 14px;">📑 Căn cứ và quy định áp dụng</div>', unsafe_allow_html=True)
            res = load_result(case_id)
            chunks_to_display: list[dict] = []
            if res and res.evidence and res.evidence.chunks:
                chunks_to_display = [{"breadcrumb": c.breadcrumb, "text": c.text, "chunk_id": c.chunk_id} for c in res.evidence.chunks]
            else:
                all_source_ids = set()
                for ev in events:
                    if ev.sources:
                        all_source_ids.update(ev.sources)
                for sid in all_source_ids:
                    ck = get_chunk(sid)
                    if ck:
                        chunks_to_display.append({"breadcrumb": ck.breadcrumb, "text": ck.text, "chunk_id": ck.chunk_id})

            if not chunks_to_display:
                st.markdown(
                    '<div class="ex-card" style="background: #F8FAFC;">'
                    '<span style="font-size: 13.5px; color: #64748B;">Không có đoạn trích dẫn quy định nào được liên kết cho ca này (hoặc yêu cầu nằm ngoài phạm vi quy chế).</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                for ck in chunks_to_display:
                    st.markdown(
                        f'<div class="ex-evidence-box">'
                        f'<div class="ex-evidence-breadcrumb">📌 {ck["breadcrumb"]} · <span style="font-family: monospace; font-size: 11px;">{ck["chunk_id"]}</span></div>'
                        f'<div class="ex-evidence-text">{ck["text"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # E. Can thiệp của Người quản trị (Admin Intervention với Two-Step Confirm)
            st.markdown("<hr style='margin: 22px 0 16px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
            st.markdown('<div class="ex-card-title">🛡️ Quyền can thiệp của người quản trị (Admin Intervention)</div>', unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    '<div style="font-size: 13px; color: #64748B; margin-bottom: 12px; line-height: 1.5;">'
                    'Quản trị viên có thẩm quyền điều chỉnh hướng xử lý khi phát hiện sai lệch hoặc yêu cầu đặc biệt. '
                    'Mọi thao tác đều bắt buộc ghi nhận lý do giải trình và lưu vĩnh viễn vào nhật ký kiểm toán.'
                    '</div>',
                    unsafe_allow_html=True,
                )

                override_choice = st.selectbox(
                    "Hướng xử lý mới",
                    [Decision.ESCALATE, Decision.AUTO_REPLY],
                    format_func=lambda val: (
                        "Chuyển chuyên viên xử lý (ESCALATE)"
                        if val is Decision.ESCALATE
                        else "Đưa phản hồi đã kiểm tra sang chờ duyệt gửi (AUTO_REPLY)"
                    ),
                    key=f"override_choice_{case_id}",
                )

                override_reason = st.text_area(
                    "Lý do điều chỉnh (bắt buộc)*",
                    placeholder="Nêu rõ căn cứ hoặc lý do quản trị viên can thiệp thay đổi quyết định...",
                    key=f"override_reason_{case_id}",
                )

                # Action Preview Box (Ngôn ngữ nghiệp vụ rõ ràng theo UX Blueprint)
                target_status_desc = "Cần chuyên viên xử lý (AWAITING_HUMAN)" if override_choice is Decision.ESCALATE else "Chờ duyệt nội dung gửi (PENDING_APPROVAL)"
                st.markdown(
                    f'<div class="ex-action-preview">'
                    f'<div class="ex-action-preview-title">Sau khi xác nhận điều chỉnh:</div>'
                    f'<div class="ex-action-preview-item">• Ghi nhận quyết định mới: <strong>{override_choice.value}</strong></div>'
                    f'<div class="ex-action-preview-item">• Ca sẽ được chuyển sang: <strong>{target_status_desc}</strong></div>'
                    f'<div class="ex-action-preview-item">• Ghi nhận nhật ký kiểm toán với chủ thể: <strong>ADMIN:local</strong></div>'
                    f'<div class="ex-action-preview-item">• Email chưa được gửi ra ngoài cho đến khi hoàn tất phê duyệt.</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Two-Step Confirmation State
                confirm_key = f"confirm_override_active_{case_id}"
                if st.query_params.get("confirm") == "override":
                    st.session_state[confirm_key] = True

                is_confirming = st.session_state.get(confirm_key, False)

                if not is_confirming:
                    btn_request = st.button(
                        "🛡️ Yêu cầu điều chỉnh cách xử lý",
                        disabled=not bool(override_reason.strip()),
                        key=f"btn_request_override_{case_id}",
                    )
                    if btn_request:
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    # Hộp thoại xác nhận 2 bước
                    st.warning(
                        f"⚠️ **Xác nhận điều chỉnh quyết định:** Bạn sắp ghi đè quyết định của ca `{case_id}` sang `{override_choice.value}`. "
                        f"Thao tác này sẽ được ghi vào nhật ký kiểm toán vĩnh viễn và không thể thu hồi."
                    )
                    col_cf_btn1, col_cf_btn2 = st.columns([1, 1])
                    with col_cf_btn1:
                        if st.button("Hủy bỏ", key=f"cancel_override_{case_id}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
                    with col_cf_btn2:
                        if st.button("Xác nhận điều chỉnh ngay", type="primary", key=f"execute_override_{case_id}", use_container_width=True):
                            try:
                                override_decision(case_id, override_choice, "ADMIN:local", override_reason.strip())
                                st.session_state[confirm_key] = False
                                st.success(f"Đã ghi nhận điều chỉnh cho ca {case_id}. Nhật ký kiểm toán đã được cập nhật.")
                                st.rerun()
                            except ValueError as error:
                                st.error(readable_text(str(error)))

                # Trường hợp ca lỗi cần xử lý lại (Retry)
                if selected_case["status"] in ("ERROR", "NEEDS_RECHECK", "CANCELLED"):
                    st.markdown("<hr style='margin: 14px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
                    retry_confirm_key = f"confirm_retry_active_{case_id}"
                    if not st.session_state.get(retry_confirm_key, False):
                        if st.button("🔄 Xử lý lại bằng quy định hiện tại", key=f"btn_retry_{case_id}"):
                            st.session_state[retry_confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ Bạn có chắc muốn tạo một chu trình xử lý mới cho ca này? Hồ sơ cũ vẫn được lưu toàn vẹn.")
                        col_rc1, col_rc2 = st.columns(2)
                        with col_rc1:
                            if st.button("Hủy", key=f"cancel_retry_{case_id}", use_container_width=True):
                                st.session_state[retry_confirm_key] = False
                                st.rerun()
                        with col_rc2:
                            if st.button("Xác nhận xử lý lại", type="primary", key=f"confirm_retry_{case_id}", use_container_width=True):
                                try:
                                    new_id = retry_case(case_id, actor="ADMIN:local")
                                    st.session_state[retry_confirm_key] = False
                                    st.success(f"Đã tạo lượt xử lý mới `{new_id}`.")
                                    st.link_button("Mở lần xử lý mới", f"/Nhat_ky_kiem_toan?case_id={quote(new_id)}")
                                except ValueError as err:
                                    st.error(readable_text(str(err)))

            # F. Raw Metadata Drill-down & Tải JSON
            st.markdown("<hr style='margin: 22px 0 16px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
            with st.expander("🛠️ Chi tiết kỹ thuật & Dữ liệu sự kiện thô (JSON)", expanded=False):
                st.caption("Dữ liệu thô dùng cho kiểm toán độc lập và đối soát bảo mật hệ thống:")
                raw_json = json.dumps([asdict(e) for e in events], ensure_ascii=False, indent=2)
                st.code(raw_json, language="json")

            st.download_button(
                f"📥 Tải dữ liệu kiểm toán ca {case_id} (JSON)",
                raw_json,
                file_name=f"audit_{case_id}.json",
                mime="application/json",
                use_container_width=True,
                key=f"dl_json_{case_id}",
            )


main()
