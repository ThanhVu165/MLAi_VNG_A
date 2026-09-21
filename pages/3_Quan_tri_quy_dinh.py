"""Trang kiểm tra thủ công các URL nguồn quy định."""

from __future__ import annotations

import streamlit as st

from core.types import ChunkLabel
from corpus.coverage import chunks_for_coverage, set_chunk_label, suggest_chunk_label
from corpus.intake import recheck_url_sources
from corpus.lifecycle import approve_for_activation, pending_reviews, reject_source, request_change
from corpus.metadata import MetadataDraft, SUPPORTED_DOMAIN_VALUES, save_metadata
from corpus.store import SourceRecord, list_sources


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


def _csv(values: tuple[str, ...]) -> str:
    return ", ".join(values)


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _draft_from_source(source: SourceRecord | None) -> MetadataDraft:
    return MetadataDraft(
        document_id=source.doc_id if source else None,
        title=source.title if source else None,
        issuer=source.issuer if source else None,
        published_at=source.published_at if source else None,
        effective_from=source.effective_from if source else None,
        effective_to=source.effective_to if source else None,
        applies_to=source.applies_to if source else None,
        cohorts=source.cohorts if source else None,
        supersedes=source.supersedes if source else None,
        transitional_clause=source.transitional_clause if source else None,
        domains=tuple(domain.value for domain in source.domains) if source else None,
        content_hash=source.content_hash if source else "",
    )


sources = list_sources()
source_by_id = {source.doc_id: source for source in sources}
selected_id = st.selectbox("Nguồn cần chỉnh metadata", ["Tạo nguồn mới", *source_by_id])
selected = source_by_id.get(selected_id)
draft = _draft_from_source(selected)

with st.form("metadata-form"):
    document_id = st.text_input(
        "Mã tài liệu", value=draft.document_id or "", disabled=selected is not None
    )
    title = st.text_input("Tiêu đề", value=draft.title or "")
    issuer = st.text_input("Đơn vị ban hành", value=draft.issuer or "")
    published_at = st.text_input("Ngày ban hành (YYYY-MM-DD)", value=draft.published_at or "")
    effective_from = st.text_input("Hiệu lực từ (YYYY-MM-DD)", value=draft.effective_from or "")
    effective_to = st.text_input("Hiệu lực đến (YYYY-MM-DD)", value=draft.effective_to or "")
    applies_to = st.text_input(
        "Đối tượng áp dụng (cách nhau bằng dấu phẩy)", value=_csv(draft.applies_to or ())
    )
    cohorts = st.text_input(
        "Khóa áp dụng (cách nhau bằng dấu phẩy)", value=_csv(draft.cohorts or ())
    )
    supersedes = st.text_input(
        "Tài liệu thay thế (cách nhau bằng dấu phẩy)", value=_csv(draft.supersedes or ())
    )
    domains = st.multiselect(
        "Lĩnh vực", sorted(SUPPORTED_DOMAIN_VALUES), default=list(draft.domains or ())
    )
    transitional_clause = st.checkbox(
        "Có điều khoản chuyển tiếp", value=bool(draft.transitional_clause)
    )
    submitted = st.form_submit_button("Lưu metadata chờ duyệt")

if submitted:
    edited = MetadataDraft(
        document_id=document_id,
        title=title or None,
        issuer=issuer or None,
        published_at=published_at or None,
        effective_from=effective_from or None,
        effective_to=effective_to or None,
        applies_to=_split_csv(applies_to) or None,
        cohorts=_split_csv(cohorts) or None,
        supersedes=_split_csv(supersedes) or None,
        transitional_clause=transitional_clause,
        domains=tuple(domains),
        content_hash=draft.content_hash,
    )
    try:
        save_metadata(edited, actor="ADMIN:local", source_id=selected.doc_id if selected else None)
    except ValueError as error:
        st.error(str(error))
    else:
        st.success("Đã lưu metadata ở trạng thái chờ duyệt.")


st.divider()
st.subheader("Tài liệu chờ duyệt")
reviews = pending_reviews()
if not reviews:
    st.info("Chưa có tài liệu nào chờ duyệt.")
for review in reviews:
    source = review.source
    with st.expander(source.title or source.doc_id):
        st.write(
            f"Mã: {source.doc_id} · Lĩnh vực: {', '.join(domain.value for domain in source.domains)}"
        )
        st.write(f"Thay thế: {', '.join(source.supersedes) or 'Không có'}")
        for chunk in review.chunks:
            st.caption(f"{chunk.breadcrumb} · {chunk.label.value}")
        if review.diff_lines:
            st.code("\n".join(review.diff_lines), language="diff")
        reason = st.text_area(
            "Lý do duyệt/từ chối/yêu cầu chỉnh sửa", key=f"review-reason:{source.doc_id}"
        )
        confirmed = st.checkbox("Tôi xác nhận thao tác này", key=f"review-confirm:{source.doc_id}")
        if st.button("Duyệt để kích hoạt", key=f"approve:{source.doc_id}"):
            if reason.strip() and confirmed:
                approve_for_activation(source, actor="ADMIN:local", reason=reason)
                st.success("Nguồn đã được duyệt, sẵn sàng cho bước kích hoạt.")
            else:
                st.error("Cần xác nhận thao tác và nhập lý do trước khi duyệt.")
        if st.button("Từ chối tài liệu", key=f"reject:{source.doc_id}"):
            try:
                if not confirmed:
                    raise ValueError("Cần xác nhận thao tác trước khi từ chối.")
                reject_source(source, actor="ADMIN:local", reason=reason)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Đã từ chối tài liệu.")
        if st.button("Yêu cầu chỉnh sửa", key=f"change:{source.doc_id}"):
            try:
                if not confirmed:
                    raise ValueError("Cần xác nhận thao tác trước khi yêu cầu chỉnh sửa.")
                request_change(source, actor="ADMIN:local", reason=reason)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success("Đã ghi yêu cầu chỉnh sửa.")

st.divider()
st.subheader("Gán nhãn thẩm quyền từng điều khoản")
coverage_source_id = st.selectbox("Nguồn có chunk cần gán nhãn", ["", *source_by_id])
if coverage_source_id:
    for chunk in chunks_for_coverage(coverage_source_id):
        st.caption(f"{chunk.breadcrumb} — {chunk.text[:180]}")
        if st.button("Lấy gợi ý nhãn", key=f"suggest-label:{chunk.chunk_id}"):
            suggestion = suggest_chunk_label(chunk, case_id=f"label:{chunk.chunk_id}")
            if suggestion.label is not None:
                st.info(f"Gợi ý (chưa áp dụng): {suggestion.label.value}")
            else:
                st.warning(suggestion.error or "Chưa có gợi ý nhãn.")
        current = st.selectbox(
            "Nhãn hiện tại",
            [label.value for label in ChunkLabel],
            index=list(ChunkLabel).index(chunk.label),
            key=f"label:{chunk.chunk_id}",
        )
        if st.button("Lưu nhãn", key=f"save-label:{chunk.chunk_id}"):
            set_chunk_label(chunk.chunk_id, ChunkLabel(current), actor="ADMIN:local")
            st.success("Đã lưu nhãn do người quản trị chọn.")
