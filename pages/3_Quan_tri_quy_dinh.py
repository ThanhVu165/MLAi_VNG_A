"""Trang kiểm tra thủ công các URL nguồn quy định."""

from __future__ import annotations

import streamlit as st

from corpus.intake import recheck_url_sources
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
    document_id = st.text_input("Mã tài liệu", value=draft.document_id or "", disabled=selected is not None)
    title = st.text_input("Tiêu đề", value=draft.title or "")
    issuer = st.text_input("Đơn vị ban hành", value=draft.issuer or "")
    published_at = st.text_input("Ngày ban hành (YYYY-MM-DD)", value=draft.published_at or "")
    effective_from = st.text_input("Hiệu lực từ (YYYY-MM-DD)", value=draft.effective_from or "")
    effective_to = st.text_input("Hiệu lực đến (YYYY-MM-DD)", value=draft.effective_to or "")
    applies_to = st.text_input("Đối tượng áp dụng (cách nhau bằng dấu phẩy)", value=_csv(draft.applies_to or ()))
    cohorts = st.text_input("Khóa áp dụng (cách nhau bằng dấu phẩy)", value=_csv(draft.cohorts or ()))
    supersedes = st.text_input("Tài liệu thay thế (cách nhau bằng dấu phẩy)", value=_csv(draft.supersedes or ()))
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
