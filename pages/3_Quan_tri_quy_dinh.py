"""Trang quản trị vòng đời tài liệu quy định."""

from __future__ import annotations

import streamlit as st

from core.types import ChunkLabel, SourceStatus
from corpus import api
from corpus.coverage import set_chunk_label, suggest_chunk_label
from corpus.intake import ingest_file, ingest_text, ingest_url, recheck_url_sources
from corpus.lifecycle import activate_source, pending_reviews, reject_source, request_change
from corpus.metadata import MetadataDraft, SUPPORTED_DOMAIN_VALUES, save_metadata
from corpus.store import ChunkRecord, SourceRecord, list_chunks, list_sources
from infra.audit import recent_events

ADMIN_ACTOR = "ADMIN:local"

st.set_page_config(page_title="Quản trị quy định", page_icon="📚")
st.title("Quản trị quy định")
st.caption("Nạp, duyệt và theo dõi vòng đời văn bản quy định.")


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


def _save_metadata(source: SourceRecord | None, key: str) -> None:
    draft = _draft_from_source(source)
    with st.form(f"metadata:{key}"):
        document_id = st.text_input(
            "Mã tài liệu", value=draft.document_id or "", disabled=source is not None
        )
        title = st.text_input("Tiêu đề", value=draft.title or "")
        issuer = st.text_input("Đơn vị ban hành", value=draft.issuer or "")
        published_at = st.text_input("Ngày ban hành (YYYY-MM-DD)", value=draft.published_at or "")
        effective_from = st.text_input("Hiệu lực từ (YYYY-MM-DD)", value=draft.effective_from or "")
        effective_to = st.text_input("Hiệu lực đến (YYYY-MM-DD)", value=draft.effective_to or "")
        applies_to = st.text_input("Đối tượng áp dụng", value=_csv(draft.applies_to or ()))
        cohorts = st.text_input("Khóa áp dụng", value=_csv(draft.cohorts or ()))
        supersedes = st.text_input("Tài liệu thay thế", value=_csv(draft.supersedes or ()))
        domains = st.multiselect(
            "Lĩnh vực", sorted(SUPPORTED_DOMAIN_VALUES), default=list(draft.domains or ())
        )
        transitional_clause = st.checkbox(
            "Có điều khoản chuyển tiếp", value=bool(draft.transitional_clause)
        )
        submitted = st.form_submit_button("Lưu metadata chờ duyệt")
    if not submitted:
        return
    try:
        save_metadata(
            MetadataDraft(
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
            ),
            actor=ADMIN_ACTOR,
            source_id=source.doc_id if source else None,
        )
    except ValueError as error:
        st.error(str(error))
    else:
        st.success("Đã lưu metadata ở trạng thái chờ duyệt.")


def _label_chunks(chunks: list[ChunkRecord]) -> None:
    for chunk in chunks:
        st.caption(f"{chunk.breadcrumb} — {chunk.text[:180]}")
        current = st.selectbox(
            "Nhãn thẩm quyền",
            [label.value for label in ChunkLabel],
            index=list(ChunkLabel).index(chunk.label),
            key=f"label:{chunk.chunk_id}",
        )
        left, right = st.columns(2)
        if left.button("Lưu nhãn", key=f"save-label:{chunk.chunk_id}"):
            set_chunk_label(chunk.chunk_id, ChunkLabel(current), actor=ADMIN_ACTOR)
            st.success("Đã lưu nhãn do người quản trị chọn.")
        if right.button("Lấy gợi ý nhãn", key=f"suggest-label:{chunk.chunk_id}"):
            suggestion = suggest_chunk_label(chunk, case_id=f"label:{chunk.chunk_id}")
            if suggestion.label is not None:
                st.info(f"Gợi ý chưa áp dụng: {suggestion.label.value}")
            else:
                st.warning(suggestion.error or "Chưa có gợi ý nhãn.")


upload_tab, review_tab, active_tab, history_tab = st.tabs(
    ["Nạp tài liệu", "Chờ duyệt", "Đang hiệu lực", "Lịch sử"]
)

with upload_tab:
    st.subheader("Nạp tài liệu mới")
    uploaded = st.file_uploader("Chọn tệp PDF hoặc DOCX", type=["pdf", "docx"])
    file_id = st.text_input("Mã tài liệu cho tệp (không bắt buộc)", key="file-id")
    if st.button("Nạp tệp", type="primary"):
        if uploaded is None:
            st.error("Hãy chọn tệp PDF hoặc DOCX trước khi nạp.")
        else:
            try:
                result = ingest_file(
                    uploaded.getvalue(),
                    uploaded.name,
                    actor=ADMIN_ACTOR,
                    document_id=file_id or None,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"{result.message}: {result.source.doc_id}")

    with st.expander("Nạp văn bản hoặc URL"):
        pasted_text = st.text_area("Dán nội dung văn bản", key="pasted-text")
        text_title = st.text_input("Tiêu đề văn bản", key="text-title")
        text_id = st.text_input("Mã tài liệu", key="text-id")
        if st.button("Nạp văn bản đã dán"):
            try:
                text_result = ingest_text(
                    pasted_text,
                    actor=ADMIN_ACTOR,
                    title=text_title or "Văn bản dán trực tiếp",
                    document_id=text_id or None,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"{text_result.message}: {text_result.source.doc_id}")

        source_url = st.text_input("URL nguồn", key="source-url")
        url_id = st.text_input("Mã tài liệu URL", key="url-id")
        if st.button("Nạp từ URL"):
            try:
                url_result = ingest_url(source_url, actor=ADMIN_ACTOR, document_id=url_id or None)
            except (OSError, ValueError) as error:
                st.error(f"Không thể nạp URL: {error}")
            else:
                st.success(f"{url_result.message}: {url_result.source.doc_id}")

    if st.button("Kiểm tra nguồn mới"):
        with st.spinner("Đang tải lại các URL đã đăng ký..."):
            results = recheck_url_sources(actor=ADMIN_ACTOR)
        if not results:
            st.info("Chưa có URL nguồn nào để kiểm tra.")
        for recheck_result in results:
            message = (
                f"{recheck_result.source.title or recheck_result.source.doc_id}: "
                f"{recheck_result.message}"
            )
            (
                st.error
                if recheck_result.error
                else st.warning if recheck_result.changed else st.success
            )(message)

    sources = list_sources()
    source_by_id = {source.doc_id: source for source in sources}
    selected_id = st.selectbox("Chỉnh metadata nguồn", ["Tạo nguồn mới", *source_by_id])
    _save_metadata(source_by_id.get(selected_id), selected_id)

with review_tab:
    st.subheader("Tài liệu chờ duyệt")
    reviews = pending_reviews()
    if not reviews:
        st.info("Chưa có tài liệu nào chờ duyệt.")
    for review in reviews:
        source = review.source
        with st.expander(source.title or source.doc_id):
            st.write(
                f"Mã: {source.doc_id} · Thay thế: {', '.join(source.supersedes) or 'Không có'}"
            )
            if review.diff_lines:
                st.code("\n".join(review.diff_lines), language="diff")
            _label_chunks(review.chunks)
            reason = st.text_area("Lý do", key=f"reason:{source.doc_id}")
            confirmed = st.checkbox("Tôi xác nhận thao tác này", key=f"confirm:{source.doc_id}")
            if st.button("Kích hoạt tài liệu", key=f"activate:{source.doc_id}"):
                try:
                    if not confirmed:
                        raise ValueError("Cần xác nhận thao tác trước khi kích hoạt.")
                    activate_source(source, actor=ADMIN_ACTOR, reason=reason)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.success("Đã kích hoạt tài liệu.")
            if st.button("Từ chối tài liệu", key=f"reject:{source.doc_id}"):
                try:
                    if not confirmed:
                        raise ValueError("Cần xác nhận thao tác trước khi từ chối.")
                    reject_source(source, actor=ADMIN_ACTOR, reason=reason)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.success("Đã từ chối tài liệu.")
            if st.button("Yêu cầu chỉnh sửa", key=f"change:{source.doc_id}"):
                try:
                    if not confirmed:
                        raise ValueError("Cần xác nhận thao tác trước khi yêu cầu chỉnh sửa.")
                    request_change(source, actor=ADMIN_ACTOR, reason=reason)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.success("Đã ghi yêu cầu chỉnh sửa.")

with active_tab:
    st.subheader("Tài liệu đang hiệu lực")
    active_sources = list_sources(SourceStatus.ACTIVE)
    active_ids = {source.doc_id for source in active_sources}
    active_chunks = [chunk for chunk in list_chunks() if chunk.doc_id in active_ids]
    st.metric("Phiên bản corpus", api.get_corpus_version())
    counts = {label: sum(chunk.label is label for chunk in active_chunks) for label in ChunkLabel}
    left, right = st.columns(2)
    left.metric("Chunk trả lời tự động", counts[ChunkLabel.AUTO_ANSWERABLE])
    right.metric("Chunk cần chuyên viên", counts[ChunkLabel.HUMAN_ONLY])
    if active_sources:
        st.dataframe(
            [
                {
                    "Mã": source.doc_id,
                    "Tiêu đề": source.title or "",
                    "Hiệu lực từ": source.effective_from or "",
                    "Số chunk": sum(chunk.doc_id == source.doc_id for chunk in active_chunks),
                }
                for source in active_sources
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Chưa có tài liệu ACTIVE. Hãy duyệt và kích hoạt một tài liệu ở tab Chờ duyệt.")

with history_tab:
    st.subheader("Lịch sử tài liệu và thao tác")
    historical_sources = [
        source for source in list_sources() if source.status is not SourceStatus.ACTIVE
    ]
    if historical_sources:
        st.dataframe(
            [
                {
                    "Mã": source.doc_id,
                    "Trạng thái": source.status.value,
                    "Thay bởi": source.superseded_by or "",
                    "Thời điểm thay": source.superseded_at or "",
                }
                for source in historical_sources
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Chưa có tài liệu trong lịch sử.")
    events = recent_events(limit=50)
    if events:
        st.dataframe(
            [
                {
                    "Thời gian": event.ts,
                    "Thao tác": event.action,
                    "Người thực hiện": event.actor,
                    "Lý do": event.reason or "",
                    "Nguồn": ", ".join(event.sources or []),
                }
                for event in events
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Chưa có nhật ký thao tác.")
