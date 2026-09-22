"""Một đường nạp và duyệt nguồn: bản gốc → nội dung → căn cứ → xác nhận nguồn."""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import replace

from core.types import Domain, SourceStatus
from corpus.chunker import chunk_document
from corpus.extract_doc import extract_document
from corpus.lifecycle import activate_source
from corpus.metadata import MetadataDraft, MetadataProposal, propose_metadata, save_metadata
from corpus.store import (
    DatabasePath,
    SourceRecord,
    create_chunk,
    get_source,
    get_source_content,
    list_chunks,
    save_source_content,
    update_chunk,
)
from infra.audit import log_event
from infra.db import transaction


def materialize_source(source: SourceRecord, *, database_path: DatabasePath = None) -> int:
    """Chuẩn hóa bản trích xuất và lưu đơn vị pháp lý thật, không áp số đoạn cố định."""
    source = _pending_source(source.doc_id, database_path=database_path)
    original = get_source_content(source.doc_id, database_path=database_path)
    if original is None:
        raise ValueError("Nguồn chưa có bản gốc; hãy nạp lại tài liệu trước khi duyệt.")
    text = original.extracted_text
    if not text:
        if source.source_kind in {"text", "seed"}:
            text = unicodedata.normalize("NFC", original.content.decode("utf-8"))
        else:
            filename = original.filename or source.source_url or ""
            text = extract_document(original.content, filename)
    if not text.strip():
        raise ValueError("Không đọc được nội dung; PDF ảnh cần chuyển thành văn bản trước khi nạp.")
    save_source_content(replace(original, extracted_text=text), database_path=database_path)
    chunks = chunk_document(
        text,
        doc_id=source.doc_id,
        document_title=source.title or source.doc_id,
        domain=source.domains[0] if source.domains else Domain.UNKNOWN,
    )
    existing = {
        chunk.chunk_id: chunk for chunk in list_chunks(source.doc_id, database_path=database_path)
    }
    for chunk in chunks:
        previous = existing.get(chunk.chunk_id)
        if previous is not None:
            update_chunk(replace(chunk, label=previous.label), database_path=database_path)
        else:
            create_chunk(chunk, database_path=database_path)
    return len(chunks)


def prepare_source(
    source: SourceRecord, *, actor: str, database_path: DatabasePath = None
) -> MetadataProposal:
    """Trích xuất và đề xuất; mọi đề xuất đều phải qua xác nhận của người quản trị."""
    count = materialize_source(source, database_path=database_path)
    original = get_source_content(source.doc_id, database_path=database_path)
    assert original is not None
    log_event(
        case_id=None,
        actor=actor,
        action="SOURCE_METADATA_EDITED",
        input_ref=source.doc_id,
        reason=f"Đã đọc bản gốc và chuẩn bị {count} đoạn căn cứ; chưa duyệt nguồn.",
        sources=[source.doc_id],
        database_path=str(database_path) if database_path else None,
    )
    return propose_metadata(original.extracted_text, case_id=source.doc_id)


def approve_source(
    source: SourceRecord,
    draft: MetadataDraft,
    *,
    actor: str,
    reason: str,
    database_path: DatabasePath = None,
) -> SourceRecord:
    """Người quản trị xác nhận một lần ở cấp nguồn, không cần đổi nhãn từng đoạn."""
    with transaction(database_path):
        source = _pending_source(source.doc_id, database_path=database_path)
        if not reason.strip() or not actor.startswith("ADMIN:") or not actor[6:].strip():
            raise ValueError("Cần tên người quản trị và lý do xác nhận nguồn.")
        original = get_source_content(source.doc_id, database_path=database_path)
        if original is None or not original.extracted_text.strip():
            raise ValueError("Hãy chuẩn bị và đọc nội dung nguồn trước khi duyệt.")
        if not draft.title or not draft.issuer or not draft.effective_from or not draft.applies_to:
            raise ValueError(
                "Cần xác nhận tên nguồn, đơn vị ban hành, ngày hiệu lực và đối tượng áp dụng."
            )
        confirmed = replace(
            draft,
            document_id=source.doc_id,
            content_hash=hashlib.sha256(original.extracted_text.encode()).hexdigest(),
        )
        saved = save_metadata(
            confirmed, actor=actor, source_id=source.doc_id, database_path=database_path
        )
        materialize_source(saved, database_path=database_path)
        return activate_source(saved, actor=actor, reason=reason, database_path=database_path)


def _pending_source(doc_id: str, *, database_path: DatabasePath) -> SourceRecord:
    source = get_source(doc_id, database_path=database_path)
    if source is None or source.status is not SourceStatus.PENDING_REVIEW:
        raise ValueError("Nguồn đã thay đổi hoặc không còn chờ xác nhận. Hãy tải lại danh sách.")
    return source
