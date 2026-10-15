"""Quy định & căn cứ: tra cứu, đối chiếu căn cứ pháp lý, quản lý nguồn và vòng đời tài liệu."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import replace
from datetime import date
from typing import Callable, TypeVar

import streamlit as st

from core.types import Domain, SourceStatus
from corpus.intake import ingest_file, ingest_text
from corpus.lifecycle import reject_source
from corpus.metadata import MetadataDraft
from corpus.store import SourceRecord, get_source, get_source_content, list_chunks, list_sources
from corpus.workflow import approve_source, prepare_source
from infra.db import fetch_all
from infra.demo_access import authorize_demo_action, is_restricted_demo
from ui.presentation import (
    badge_html,
    decision_badge_html,
    escape_html,
    inject_app_css,
    kpi_card_html,
    local_time,
    page_header_html,
    readable_text,
)

LOGGER = logging.getLogger(__name__)

DOMAIN_NAMES = {
    Domain.CONDUCT_SCORE.value: "Điểm rèn luyện",
    Domain.COURSE_WITHDRAWAL.value: "Rút học phần",
    Domain.GRADE_APPEAL.value: "Phúc khảo điểm",
}

STATUS_NAMES = {
    SourceStatus.PENDING_REVIEW: "Chờ xác nhận",
    SourceStatus.ACTIVE: "Đang áp dụng",
    SourceStatus.SUPERSEDED: "Đã thay thế",
    SourceStatus.REJECTED: "Đã từ chối",
}

SOURCE_READ_ERROR = (
    "Hiện chưa thể truy xuất danh mục quy chế. " "Vui lòng thử lại sau hoặc liên hệ người quản trị."
)
_T = TypeVar("_T")


def _read_or_stop(read: Callable[[], _T]) -> _T:
    try:
        return read()
    except (sqlite3.Error, OSError):
        LOGGER.exception("Không truy xuất được dữ liệu trang quy chế.")
        st.error(SOURCE_READ_ERROR)
        st.stop()


def _list_sources_or_stop(status: SourceStatus | None = None) -> list[SourceRecord]:
    return _read_or_stop(lambda: list_sources(status))


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        LOGGER.warning("Nguồn có ngày không hợp lệ: %s", value)
        st.warning("Ngày trong thông tin nguồn chưa hợp lệ. Hãy đối chiếu và chọn lại ngày.")
        return None


def _date_text(value: str | None) -> str:
    parsed = _date(value)
    return parsed.strftime("%d/%m/%Y") if parsed is not None else "chưa xác định"


def _iso_date(value: object) -> str | None:
    return value.isoformat() if isinstance(value, date) else None


def _show_content(source: SourceRecord, key: str) -> None:
    original = _read_or_stop(lambda: get_source_content(source.doc_id))
    if source.is_synthetic:
        st.warning("Tài liệu giả lập để kiểm thử, không có giá trị pháp lý.")
    st.caption(
        f"{source.issuer or 'Chưa rõ đơn vị ban hành'} · Hiệu lực từ "
        f"{_date_text(source.effective_from)} đến {_date_text(source.effective_to)}"
    )
    if original is not None:
        st.download_button(
            "Tải bản gốc",
            original.content,
            original.filename or f"{source.doc_id}.txt",
            key=f"download:{key}",
        )
        text = original.extracted_text
        if not text.strip():
            st.info(
                "Chưa có nội dung đã đọc. Hãy bấm Đọc lại và đề xuất thông tin hoặc nạp bản văn bản."
            )
    else:
        st.warning(
            "Nguồn cũ chưa lưu bản gốc. Nội dung dưới đây được ghép từ các đoạn đã lưu, không thay thế bản gốc."
        )
        text = "\n\n".join(
            chunk.text for chunk in _read_or_stop(lambda: list_chunks(source.doc_id))
        )
    st.text_area("Nội dung tài liệu", text, height=360, disabled=True, key=f"content:{key}")
    if source.cohorts:
        st.caption("Khóa áp dụng: " + ", ".join(source.cohorts))


def _proposal(source: SourceRecord) -> MetadataDraft:
    value = st.session_state.get(f"proposal:{source.doc_id}")
    if isinstance(value, MetadataDraft):
        return replace(value, document_id=source.doc_id)
    return MetadataDraft(
        source.doc_id,
        source.title,
        source.issuer,
        source.published_at,
        source.effective_from,
        source.effective_to,
        source.applies_to,
        source.cohorts,
        source.supersedes,
        source.transitional_clause,
        tuple(domain.value for domain in source.domains),
        source.content_hash,
    )


def _prepare(source: SourceRecord, actor: str) -> None:
    authorize_demo_action("chuẩn bị nguồn từ giao diện")
    with st.spinner("Đang đọc tài liệu và đề xuất thông tin nguồn..."):
        proposal = prepare_source(source, actor=actor)
    if proposal.draft is not None:
        st.session_state[f"proposal:{source.doc_id}"] = proposal.draft
    if proposal.error:
        st.warning(
            "Đã lưu nội dung nhưng chưa đề xuất được thông tin nguồn. Bạn có thể tự xác nhận thông tin bên dưới."
        )


def _upload(actor: str, identified: bool) -> None:
    authorize_demo_action("nạp nguồn từ giao diện")
    st.markdown("#### Nạp quy định mới vào hệ thống")
    st.caption(
        "Hệ thống trích xuất nội dung gốc, lập chỉ mục ngữ nghĩa và đề xuất thông tin trước khi duyệt."
    )
    method = st.radio("Cách nạp tài liệu", ["Dán văn bản", "Chọn tệp"], horizontal=True)
    title = st.text_input("Tên tài liệu", key="new-title")
    text = st.text_area("Nội dung văn bản", height=220) if method == "Dán văn bản" else ""
    upload = (
        st.file_uploader("Tệp PDF hoặc DOCX", type=["pdf", "docx"])
        if method == "Chọn tệp"
        else None
    )
    if st.button("Nạp và đọc tài liệu", type="primary", disabled=not identified):
        try:
            if method == "Dán văn bản":
                result = ingest_text(text, actor=actor, title=title or "Văn bản dán trực tiếp")
            elif upload:
                result = ingest_file(upload.getvalue(), upload.name, actor=actor)
            else:
                raise ValueError("Hãy chọn tệp trước khi nạp.")
            if not result.created and result.source.status is not SourceStatus.PENDING_REVIEW:
                st.info(
                    "Nội dung này đã có trong Kho quy định. Không tạo bản sao hoặc thay đổi nguồn đã lưu."
                )
                return
            if result.created or result.source.status is SourceStatus.PENDING_REVIEW:
                _prepare(result.source, actor)
            st.success(result.message + ". Mở mục Chờ xác nhận để kiểm tra nguồn.")
        except ValueError as error:
            st.error(str(error))
        except Exception:
            LOGGER.exception("Không hoàn tất đọc tài liệu.")
            st.error(
                "Chưa đọc được tài liệu. Bản đã nạp vẫn được giữ; kiểm tra định dạng hoặc thử nạp văn bản."
            )


def _review(source: SourceRecord, actor: str, identified: bool) -> None:
    authorize_demo_action("duyệt nguồn từ giao diện")
    _show_content(source, f"review:{source.doc_id}")
    if st.button(
        "Đọc lại và đề xuất thông tin", key=f"prepare:{source.doc_id}", disabled=not identified
    ):
        try:
            _prepare(source, actor)
        except Exception:
            LOGGER.exception("Không chuẩn bị được nguồn %s", source.doc_id)
            st.error("Chưa đọc được nguồn. Hãy kiểm tra bản gốc hoặc nạp lại dưới dạng văn bản.")
    with st.form(f"approve:{source.doc_id}"):
        st.caption("Kiểm tra nguồn, thời gian và phạm vi. Không cần cấp quyền cho từng đoạn.")
        draft = _edit_fields(_proposal(source))
        reason = st.text_area("Lý do xác nhận hoặc từ chối")
        confirmed = st.checkbox("Tôi đã đối chiếu bản gốc, ngày hiệu lực và phạm vi áp dụng")
        approve = st.form_submit_button("Xác nhận và đưa vào sử dụng", disabled=not identified)
        reject = st.form_submit_button("Từ chối nguồn", disabled=not identified)
    if not (approve or reject):
        return
    try:
        if not confirmed:
            raise ValueError("Hãy xác nhận đã đối chiếu nguồn trước khi tiếp tục.")
        if approve:
            approve_source(source, draft, actor=actor, reason=reason)
        else:
            reject_source(source, actor=actor, reason=reason)
    except ValueError as error:
        st.error(str(error))
    except Exception:
        LOGGER.exception("Không hoàn tất xác nhận nguồn %s", source.doc_id)
        st.error(
            "Chưa hoàn tất xác nhận nguồn. Kiểm tra lịch sử trước khi thử lại; không cần nạp lại bản gốc."
        )
    else:
        st.rerun()


def _edit_fields(draft: MetadataDraft) -> MetadataDraft:
    title = st.text_input("Tên tài liệu", value=draft.title or "")
    issuer = st.text_input("Đơn vị ban hành", value=draft.issuer or "")
    published = st.date_input("Ngày ban hành", value=_date(draft.published_at), format="DD/MM/YYYY")
    start = st.date_input("Hiệu lực từ", value=_date(draft.effective_from), format="DD/MM/YYYY")
    end = st.date_input(
        "Hiệu lực đến, để trống nếu chưa xác định",
        value=_date(draft.effective_to),
        format="DD/MM/YYYY",
    )
    domains = st.multiselect(
        "Lĩnh vực áp dụng",
        list(DOMAIN_NAMES),
        default=[d for d in draft.domains or () if d in DOMAIN_NAMES],
        format_func=lambda value: DOMAIN_NAMES[value],
    )
    undergraduate = st.checkbox(
        "Áp dụng cho sinh viên đại học chính quy", value="undergraduate" in (draft.applies_to or ())
    )
    cohorts = st.text_input(
        "Khóa áp dụng, phân cách bằng dấu phẩy", value=", ".join(draft.cohorts or ())
    )
    transitional = st.checkbox(
        "Có điều khoản chuyển tiếp giữa các khóa hoặc thời điểm",
        value=bool(draft.transitional_clause),
    )
    replacements = {item.doc_id: item for item in _list_sources_or_stop(SourceStatus.ACTIVE)}
    supersedes = st.multiselect(
        "Thay thế tài liệu đã duyệt",
        list(replacements),
        default=[item for item in draft.supersedes or () if item in replacements],
        format_func=lambda item: replacements[item].title or item,
    )
    return replace(
        draft,
        title=title.strip(),
        issuer=issuer.strip(),
        published_at=_iso_date(published),
        effective_from=_iso_date(start),
        effective_to=_iso_date(end),
        domains=tuple(domains),
        applies_to=("undergraduate",) if undergraduate else (),
        cohorts=tuple(item.strip() for item in cohorts.split(",") if item.strip()),
        transitional_clause=transitional,
        supersedes=tuple(supersedes),
    )


# --- MAIN PAGE EXECUTION ---
inject_app_css()

# Header
st.markdown(
    page_header_html(
        "Policy & Regulatory Evidence",
        "Quy định & căn cứ",
        "Quản lý văn bản quy định, trích xuất điều khoản và minh bạch căn cứ quyết định của trợ lý AI.",
    ),
    unsafe_allow_html=True,
)

if is_restricted_demo():
    synthetic_sources = [source for source in _list_sources_or_stop() if source.is_synthetic]
    public_sources = [
        {
            "Mã nguồn": source.doc_id,
            "Tên quy định": source.title,
            "Trạng thái": STATUS_NAMES.get(source.status, source.status.value),
            "Lĩnh vực": ", ".join(
                DOMAIN_NAMES.get(domain.value, domain.value) for domain in source.domains
            ),
        }
        for source in synthetic_sources
    ]
    st.info(
        "Chế độ công khai chỉ cho phép tra cứu corpus synthetic; mọi thao tác quản trị đã bị khóa phía máy chủ."
    )
    if public_sources:
        st.dataframe(public_sources, hide_index=True, use_container_width=True)
    else:
        st.info(
            "Danh mục quy chế synthetic hiện chưa có dữ liệu để tra cứu. "
            "Hãy quay lại sau khi quản trị viên đã chuẩn bị nguồn mô phỏng."
        )
    st.stop()

# Admin Reviewer Identity
name = st.text_input("Tên người quản trị để ghi nhận thao tác", key="source-reviewer")
actor = f"ADMIN:{name.strip()}"
identified = bool(name.strip())

# Sources inventory and metrics
all_sources = _list_sources_or_stop()
active_count = sum(1 for s in all_sources if s.status is SourceStatus.ACTIVE)
superseded_count = sum(1 for s in all_sources if s.status is SourceStatus.SUPERSEDED)
pending_count = sum(1 for s in all_sources if s.status is SourceStatus.PENDING_REVIEW)
domains_count = len({d for s in all_sources for d in s.domains})

latest_date = max((s.activated_at or s.created_at or "" for s in all_sources), default="")
latest_date_display = local_time(latest_date) if latest_date else "Chưa có"
if " ngày " in latest_date_display:
    latest_date_short = latest_date_display.split(" ngày ")[-1]
else:
    latest_date_short = latest_date_display

# Top KPI Summary Cards
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
with kpi_c1:
    st.markdown(
        kpi_card_html(
            "Quy định trong hệ thống",
            f"{len(all_sources)}",
            f"{active_count} đang áp dụng · {superseded_count} đã thay thế",
            "primary",
            "📄",
        ),
        unsafe_allow_html=True,
    )
with kpi_c2:
    st.markdown(
        kpi_card_html(
            "Lĩnh vực nghiệp vụ",
            f"{domains_count}",
            "Rèn luyện, Rút môn, Phúc khảo",
            "purple",
            "📚",
        ),
        unsafe_allow_html=True,
    )
with kpi_c3:
    st.markdown(
        kpi_card_html(
            "Cập nhật gần nhất",
            latest_date_short,
            "Toàn vẹn SHA-256 xác thực",
            "neutral",
            "🕒",
        ),
        unsafe_allow_html=True,
    )
with kpi_c4:
    st.markdown(
        kpi_card_html(
            "Sẵn sàng kiểm toán",
            "100%",
            "Đầy đủ căn cứ & versioning",
            "success",
            "🛡️",
        ),
        unsafe_allow_html=True,
    )

st.write("")

# 3 Tab structure: Browse (Default) / Pending / Upload
tab_param = st.query_params.get("tab", "browse")
if tab_param == "upload":
    main_tab_names = ["Nạp tài liệu mới", "Tra cứu quy định & Căn cứ", "Chờ xác nhận"]
elif tab_param == "pending":
    main_tab_names = ["Chờ xác nhận", "Tra cứu quy định & Căn cứ", "Nạp tài liệu mới"]
else:
    main_tab_names = ["Tra cứu quy định & Căn cứ", "Chờ xác nhận", "Nạp tài liệu mới"]

tabs_map = {name: tab for name, tab in zip(main_tab_names, st.tabs(main_tab_names))}
browse_tab = tabs_map["Tra cứu quy định & Căn cứ"]
pending_tab = tabs_map["Chờ xác nhận"]
upload_tab = tabs_map["Nạp tài liệu mới"]

with upload_tab:
    _upload(actor, identified)

with pending_tab:
    pending = {
        source.doc_id: source for source in _list_sources_or_stop(SourceStatus.PENDING_REVIEW)
    }
    if not pending:
        st.info("Chưa có tài liệu chờ xác nhận. Hãy nạp tài liệu mới nếu cần bổ sung căn cứ.")
    else:
        st.caption(f"Có {len(pending)} tài liệu cần người quản trị đối chiếu và phê duyệt.")
        selected_id = st.selectbox(
            "Chọn tài liệu chờ xác nhận",
            list(pending),
            format_func=lambda doc_id: pending[doc_id].title or "Tài liệu chưa có tên",
        )
        source = _read_or_stop(lambda: get_source(selected_id))
        if source is not None and source.status is SourceStatus.PENDING_REVIEW:
            _review(source, actor, identified)
        else:
            st.info("Tài liệu vừa được xử lý ở nơi khác. Hãy tải lại danh sách.")

with browse_tab:
    # Filter Bar
    if "search" in st.query_params and "policy_search_query" not in st.session_state:
        st.session_state["policy_search_query"] = st.query_params["search"]

    f_col1, f_col2, f_col3 = st.columns([6, 3, 3])
    with f_col1:
        search_query = st.text_input(
            "Tìm quy định, từ khóa, căn cứ",
            placeholder="🔍 Tìm theo mã, tên quy định, điều khoản, lệ phí, thời hạn...",
            key="policy_search_query",
        ).strip()
    with f_col2:
        status_filter = st.selectbox(
            "Trạng thái",
            ["Tất cả trạng thái", "Đang áp dụng", "Đã thay thế", "Chờ xác nhận"],
            key="policy_filter_status",
        )
    with f_col3:
        domain_filter = st.selectbox(
            "Lĩnh vực",
            ["Tất cả lĩnh vực", "Điểm rèn luyện", "Rút học phần", "Phúc khảo điểm"],
            key="policy_filter_domain",
        )

    # Filter evaluation
    filtered_sources: list[SourceRecord] = []
    for s in all_sources:
        if status_filter == "Đang áp dụng" and s.status is not SourceStatus.ACTIVE:
            continue
        if status_filter == "Đã thay thế" and s.status is not SourceStatus.SUPERSEDED:
            continue
        if status_filter == "Chờ xác nhận" and s.status is not SourceStatus.PENDING_REVIEW:
            continue

        if domain_filter != "Tất cả lĩnh vực":
            if not any(DOMAIN_NAMES.get(d.value) == domain_filter for d in s.domains):
                continue

        if search_query:
            q = search_query.lower()
            matches_title = q in (s.title or "").lower()
            matches_id = q in s.doc_id.lower()
            matches_issuer = q in (s.issuer or "").lower()
            matches_chunks = any(
                q in c.text.lower() or q in c.breadcrumb.lower()
                for c in _read_or_stop(lambda: list_chunks(s.doc_id))
            )
            if not (matches_title or matches_id or matches_issuer or matches_chunks):
                continue

        filtered_sources.append(s)

    # Split-pane layout: List on Left (5), Detail on Right (7)
    list_col, detail_col = st.columns([5, 7], gap="large")

    with list_col:
        st.markdown(
            f"<div style='font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 8px;'>"
            f"Danh sách quy định ({len(filtered_sources)}/{len(all_sources)})</div>",
            unsafe_allow_html=True,
        )

        if not filtered_sources:
            if not all_sources:
                st.info(
                    "Danh mục quy chế hiện chưa có dữ liệu. Hãy nạp và xác nhận nguồn trước "
                    "khi tra cứu."
                )
            else:
                st.info("Không tìm thấy quy định phù hợp với bộ lọc tìm kiếm.")
            selected_source: SourceRecord | None = None
        else:
            source_dict = {s.doc_id: s for s in filtered_sources}
            query_doc = st.query_params.get("doc_id")
            if query_doc in source_dict and "selected_policy_id" not in st.session_state:
                st.session_state["selected_policy_id"] = query_doc
            selected_id_prev = st.session_state.get("selected_policy_id")
            default_index = 0
            if selected_id_prev in source_dict:
                default_index = list(source_dict.keys()).index(selected_id_prev)

            selected_id = st.selectbox(
                "Chọn quy định để tra cứu chi tiết",
                list(source_dict.keys()),
                index=default_index,
                format_func=lambda did: f"[{did}] {source_dict[did].title or 'Chưa có tên'} ({STATUS_NAMES.get(source_dict[did].status, '')})",
                key="policy_selector_select",
            )
            st.session_state["selected_policy_id"] = selected_id
            selected_source = source_dict[selected_id]

            # Visual summary cards list
            for s in filtered_sources:
                is_cur = s.doc_id == selected_id
                card_border = "2px solid #2563EB" if is_cur else "1px solid #E2E8F0"
                card_bg = "#EFF6FF" if is_cur else "#FFFFFF"

                if s.status is SourceStatus.ACTIVE:
                    status_pill = badge_html("Đang áp dụng", "auto")
                elif s.status is SourceStatus.SUPERSEDED:
                    status_pill = badge_html("Đã thay thế", "neutral")
                else:
                    status_pill = badge_html("Chờ duyệt", "escalate")

                domains_pills = " ".join(
                    badge_html(DOMAIN_NAMES.get(d.value, d.value), "info") for d in s.domains
                )
                chunk_count = len(_read_or_stop(lambda: list_chunks(s.doc_id)))

                st.markdown(
                    f"""
                    <div style="border: {card_border}; background: {card_bg}; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 13px; font-weight: 700; color: #1E293B;">📄 {escape_html(s.doc_id)}</span>
                            <div>{status_pill}</div>
                        </div>
                        <div style="font-size: 13.5px; font-weight: 600; color: #0F172A; margin-bottom: 6px; line-height: 1.35;">
                            {escape_html(s.title or 'Chưa có tên tài liệu')}
                        </div>
                        <div style="display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 6px;">
                            {domains_pills}
                            <span style="font-size: 11px; color: #64748B; padding: 2px 6px; background: #F1F5F9; border-radius: 4px;">
                                {chunk_count} điều khoản
                            </span>
                        </div>
                        <div style="font-size: 11.5px; color: #64748B;">
                            {escape_html(s.issuer or 'Chưa rõ đơn vị')} · Hiệu lực từ: {escape_html(_date_text(s.effective_from))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with detail_col:
        if selected_source is not None:
            # Header card of the selected document
            st.markdown(
                f"""
                <div class="ex-card" style="margin-bottom: 12px; border-left: 4px solid #2563EB;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="font-size: 12px; font-weight: 700; color: #2563EB; margin-bottom: 2px;">
                                MÃ VĂN BẢN: {escape_html(selected_source.doc_id)}
                            </div>
                            <h3 style="margin: 0 0 6px 0; font-size: 17px; font-weight: 700; color: #0F172A;">
                                {escape_html(selected_source.title or 'Tài liệu chưa có tiêu đề')}
                            </h3>
                            <div style="font-size: 12.5px; color: #64748B;">
                                🏢 {escape_html(selected_source.issuer or 'Chưa rõ đơn vị ban hành')} &nbsp;·&nbsp;
                                📅 Hiệu lực: {escape_html(_date_text(selected_source.effective_from))} → {escape_html(_date_text(selected_source.effective_to))}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            {badge_html("Đang áp dụng", "auto") if selected_source.status is SourceStatus.ACTIVE else badge_html("Đã thay thế", "neutral")}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Sub-tabs within detail view
            detail_tab_param = st.query_params.get("detail_tab", "clauses")
            if detail_tab_param == "meta":
                sub_names = [
                    "Thông tin & Phạm vi",
                    "Điều khoản & Căn cứ",
                    "Toàn văn tài liệu",
                    "Ca xử lý trích dẫn",
                ]
            elif detail_tab_param == "original":
                sub_names = [
                    "Toàn văn tài liệu",
                    "Điều khoản & Căn cứ",
                    "Thông tin & Phạm vi",
                    "Ca xử lý trích dẫn",
                ]
            elif detail_tab_param == "cases":
                sub_names = [
                    "Ca xử lý trích dẫn",
                    "Điều khoản & Căn cứ",
                    "Thông tin & Phạm vi",
                    "Toàn văn tài liệu",
                ]
            else:
                sub_names = [
                    "Điều khoản & Căn cứ",
                    "Thông tin & Phạm vi",
                    "Toàn văn tài liệu",
                    "Ca xử lý trích dẫn",
                ]

            sub_map = {name: tab for name, tab in zip(sub_names, st.tabs(sub_names))}
            sub_clauses = sub_map["Điều khoản & Căn cứ"]
            sub_meta = sub_map["Thông tin & Phạm vi"]
            sub_original = sub_map["Toàn văn tài liệu"]
            sub_cases = sub_map["Ca xử lý trích dẫn"]

            with sub_clauses:
                chunks = _read_or_stop(lambda: list_chunks(selected_source.doc_id))
                st.caption(
                    f"Hiển thị {len(chunks)} điều khoản/căn cứ đã được trích xuất ngữ nghĩa và sẵn sàng kiểm toán."
                )
                if search_query:
                    st.info(f"Đang làm nổi bật căn cứ khớp với từ khóa: **{search_query}**")

                for chunk in chunks:
                    is_hit = bool(
                        search_query
                        and (
                            search_query.lower() in chunk.text.lower()
                            or search_query.lower() in chunk.breadcrumb.lower()
                        )
                    )
                    border_style = (
                        "border-left: 4px solid #10B981; background: #F0FDF4;"
                        if is_hit
                        else "border-left: 3px solid #2563EB; background: #F8FAFC;"
                    )
                    safe_chunk_text = escape_html(chunk.text.strip()).replace("\n", "<br/>")
                    st.markdown(
                        f"""
                        <div class="ex-evidence-box" style="{border_style} margin-bottom: 12px; border-radius: 6px; padding: 12px 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                                <span class="ex-evidence-breadcrumb" style="font-weight: 700; color: #1E40AF; font-size: 12.5px;">
                                    📌 {escape_html(chunk.breadcrumb)}
                                </span>
                                <span style="font-size: 11px; font-family: monospace; color: #64748B;">
                                    {escape_html(chunk.chunk_id)}
                                </span>
                            </div>
                            <div class="ex-evidence-text" style="font-size: 13.5px; line-height: 1.55; color: #1E293B; background: #FFFFFF; padding: 10px 12px; border-radius: 4px; border: 1px solid #E2E8F0;">
                                {safe_chunk_text}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with sub_meta:
                st.markdown("##### Thuộc tính văn bản & Phạm vi áp dụng")
                m_left, m_right = st.columns(2)
                with m_left:
                    st.markdown(f"**Đơn vị ban hành:** {selected_source.issuer or 'Chưa xác định'}")
                    st.markdown(f"**Ngày ban hành:** {_date_text(selected_source.published_at)}")
                    st.markdown(f"**Hiệu lực từ:** {_date_text(selected_source.effective_from)}")
                    st.markdown(f"**Hiệu lực đến:** {_date_text(selected_source.effective_to)}")
                    domains_str = ", ".join(
                        DOMAIN_NAMES.get(d.value, d.value) for d in selected_source.domains
                    )
                    st.markdown(f"**Lĩnh vực áp dụng:** {domains_str or 'Chưa xác định'}")
                with m_right:
                    applies_str = (
                        "Sinh viên đại học chính quy"
                        if "undergraduate" in selected_source.applies_to
                        else "Tất cả đối tượng"
                    )
                    st.markdown(f"**Đối tượng:** {applies_str}")
                    cohorts_str = (
                        ", ".join(selected_source.cohorts)
                        if selected_source.cohorts
                        else "Tất cả các khóa"
                    )
                    st.markdown(f"**Khóa áp dụng:** {cohorts_str}")
                    st.markdown(
                        f"**Điều khoản chuyển tiếp:** {'Có quy định chuyển tiếp' if selected_source.transitional_clause else 'Không'}"
                    )
                    supersedes_str = (
                        ", ".join(selected_source.supersedes)
                        if selected_source.supersedes
                        else "Không thay thế tài liệu nào"
                    )
                    st.markdown(f"**Thay thế tài liệu:** {supersedes_str}")
                    if selected_source.superseded_by:
                        st.markdown(f"**Bị thay thế bởi:** {selected_source.superseded_by}")

                st.divider()
                st.markdown(
                    f"**Mã kiểm tra toàn vẹn (SHA-256):** `{selected_source.sha256 or selected_source.content_hash or 'Chưa có'}`"
                )
                if selected_source.activated_at:
                    st.caption(
                        f"Kích hoạt lúc {local_time(selected_source.activated_at)} bởi {selected_source.activated_by or 'quản trị viên'}"
                    )

            with sub_original:
                _show_content(selected_source, f"browse:{selected_source.doc_id}")

            with sub_cases:
                st.markdown("##### Ca xử lý đã trích dẫn văn bản này")
                cases_cited = _read_or_stop(
                    lambda: fetch_all(
                        """
                        SELECT d.case_id, d.decision, d.reason, d.created_at AS timestamp, c.subject, c.sender
                        FROM decisions d
                        LEFT JOIN cases c ON d.case_id = c.case_id
                        WHERE d.evidence_ids_json LIKE ?
                        ORDER BY d.created_at DESC
                        LIMIT 15
                        """,
                        (f"%{selected_source.doc_id}%",),
                    )
                )
                if cases_cited:
                    st.caption(
                        f"Tìm thấy {len(cases_cited)} ca xử lý đã trích dẫn {selected_source.doc_id} làm căn cứ pháp lý:"
                    )
                    for c in cases_cited:
                        safe_reason = escape_html(readable_text(c["reason"] or "").strip()).replace(
                            "\n", "<br/>"
                        )
                        st.markdown(
                            f"""
                            <div class="ex-card" style="margin-bottom: 8px; padding: 10px 14px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <span style="font-weight: 700; font-size: 13px;">📩 {escape_html(c['case_id'])} · {escape_html(c['subject'] or 'Không có tiêu đề')}</span>
                                    <div>{decision_badge_html(c['decision'])}</div>
                                </div>
                                <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">
                                    Sinh viên: {escape_html(c['sender'] or 'Ẩn')} · Thời điểm: {escape_html(local_time(c['timestamp']))}
                                </div>
                                <div style="font-size: 12.5px; color: #334155; background: #F8FAFC; padding: 6px 10px; border-radius: 4px; border: 1px solid #E2E8F0;">
                                    <b>Căn cứ đã áp dụng:</b> {safe_reason}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info(
                        f"Chưa có ca xử lý nào trong phiên hiện tại trích dẫn {selected_source.doc_id}."
                    )
        else:
            st.info("Vui lòng chọn một quy định trong danh sách bên trái để xem chi tiết.")
