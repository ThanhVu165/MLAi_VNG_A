"""Nguồn quy định: giữ bản gốc, xác nhận nguồn và đọc toàn văn."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import date

import streamlit as st

from core.types import Domain, SourceStatus
from corpus.intake import ingest_file, ingest_text
from corpus.lifecycle import reject_source
from corpus.metadata import MetadataDraft
from corpus.store import SourceRecord, get_source, get_source_content, list_chunks, list_sources
from corpus.workflow import approve_source, prepare_source

LOGGER = logging.getLogger(__name__)
DOMAIN_NAMES = {
    Domain.CONDUCT_SCORE.value: "Điểm rèn luyện",
    Domain.COURSE_WITHDRAWAL.value: "Rút học phần",
    Domain.GRADE_APPEAL.value: "Phúc khảo điểm",
}
STATUS_NAMES = {
    SourceStatus.PENDING_REVIEW: "Chờ xác nhận",
    SourceStatus.ACTIVE: "Đã duyệt",
    SourceStatus.SUPERSEDED: "Đã thay thế",
    SourceStatus.REJECTED: "Đã từ chối",
}


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
    original = get_source_content(source.doc_id)
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
            original.filename or "ban-goc.txt",
            key=f"download:{key}",
        )
        text = original.extracted_text
        if not text.strip():
            st.info("Chưa có nội dung đã đọc. Hãy bấm Đọc lại và đề xuất thông tin hoặc nạp bản văn bản.")
    else:
        st.warning(
            "Nguồn cũ chưa lưu bản gốc. Nội dung dưới đây được ghép từ các đoạn đã lưu, không thay thế bản gốc."
        )
        text = "\n".join(chunk.text for chunk in list_chunks(source.doc_id))
    st.text_area("Nội dung tài liệu", text, height=320, disabled=True, key=f"content:{key}")
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
    with st.spinner("Đang đọc tài liệu và đề xuất thông tin nguồn..."):
        proposal = prepare_source(source, actor=actor)
    if proposal.draft is not None:
        st.session_state[f"proposal:{source.doc_id}"] = proposal.draft
    if proposal.error:
        st.warning(
            "Đã lưu nội dung nhưng chưa đề xuất được thông tin nguồn. Bạn có thể tự xác nhận thông tin bên dưới."
        )


def _upload(actor: str, identified: bool) -> None:
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
                st.info("Nội dung này đã có trong Kho quy định. Không tạo bản sao hoặc thay đổi nguồn đã lưu.")
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
        value=_date(draft.effective_to), format="DD/MM/YYYY",
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
    replacements = {item.doc_id: item for item in list_sources(SourceStatus.ACTIVE)}
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


st.title("Quy định")
st.caption("Tài liệu chỉ được dùng trả lời sau khi bạn xác nhận nguồn, hiệu lực và phạm vi.")
name = st.text_input("Tên người quản trị để ghi nhận thao tác", key="source-reviewer")
actor = f"ADMIN:{name.strip()}"
upload_tab, pending_tab, library_tab = st.tabs(["Nạp tài liệu", "Chờ xác nhận", "Kho quy định"])
with upload_tab:
    _upload(actor, bool(name.strip()))
with pending_tab:
    pending = {source.doc_id: source for source in list_sources(SourceStatus.PENDING_REVIEW)}
    if not pending:
        st.info("Chưa có tài liệu chờ xác nhận. Hãy nạp tài liệu mới nếu cần bổ sung căn cứ.")
    else:
        selected_id = st.selectbox(
            "Chọn tài liệu chờ xác nhận", list(pending),
            format_func=lambda doc_id: pending[doc_id].title or "Tài liệu chưa có tên",
        )
        source = get_source(selected_id)
        if source is not None and source.status is SourceStatus.PENDING_REVIEW:
            _review(source, actor, bool(name.strip()))
        else:
            st.info("Tài liệu vừa được xử lý ở nơi khác. Hãy tải lại danh sách.")
with library_tab:
    library = {source.doc_id: source for source in list_sources()
               if source.status is not SourceStatus.PENDING_REVIEW}
    if not library:
        st.info("Chưa có quy định đã duyệt. Hoàn tất xác nhận nguồn để hệ thống sử dụng.")
    else:
        selected_id = st.selectbox(
            "Chọn quy định để đọc", list(library),
            format_func=lambda doc_id: library[doc_id].title or "Tài liệu chưa có tên",
        )
        source = get_source(selected_id)
        if source is not None:
            st.caption(STATUS_NAMES[source.status])
            _show_content(source, f"library:{source.doc_id}")
        else:
            st.info("Tài liệu không còn trong danh sách. Hãy tải lại trang.")
