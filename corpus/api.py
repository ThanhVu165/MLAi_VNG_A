"""Facade đọc corpus ACTIVE cho Runtime."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import date, datetime

from core.types import Domain, EvidenceChunk, SourceStatus
from corpus.conflict import relevant_conflict
from corpus.indexer import search_active
from corpus.store import (
    ChunkRecord,
    compute_corpus_version,
    get_chunk_record,
    get_source,
    list_sources,
    list_chunks,
)

LOGGER = logging.getLogger(__name__)
RETRIEVAL_CANDIDATE_MULTIPLIER = 3


def get_corpus_version() -> str:
    """Trả phiên bản corpus đang hiệu lực, kể cả trước lần bump đầu tiên."""
    return compute_corpus_version()


def search(
    query: str,
    domains: list[Domain],
    top_k: int = 6,
    at: datetime | None = None,
) -> list[EvidenceChunk]:
    """Tìm trong index ACTIVE, lọc domain và ngày hiệu lực trước khi trả evidence."""
    if top_k <= 0 or not domains:
        return []
    records = search_active(query, top_k=top_k * RETRIEVAL_CANDIDATE_MULTIPLIER)
    requested_at = at.date() if at is not None else None
    chunks = [
        evidence
        for result in records
        if result.chunk.domain in domains
        if (evidence := _evidence_chunk(result.chunk, result.score)) is not None
        if _is_effective(evidence, requested_at)
    ]
    return chunks[:top_k]


def available_evidence(
    domains: list[Domain],
    at: datetime | None = None,
    *,
    cohort: str | None = None,
    applies_to: str | None = None,
) -> list[EvidenceChunk]:
    """Các đoạn nguồn đã duyệt để mô hình chọn căn cứ, không lọc nhãn lịch sử."""
    requested_at = at.date() if at is not None else None
    sources = {
        source.doc_id: source
        for source in list_sources(SourceStatus.ACTIVE)
        if set(source.domains) & set(domains)
        if not cohort
        or not source.cohorts
        or cohort.casefold() in {item.casefold() for item in source.cohorts}
        if not applies_to or not source.applies_to or applies_to in source.applies_to
    }
    records = [record for record in list_chunks() if record.doc_id in sources]
    candidates = {
        record.chunk_id: chunk
        for record in records
        if (chunk := _evidence_chunk(record, 1.0, expand=False)) is not None
        if _is_effective(chunk, requested_at)
    }
    relevant_records = [record for record in records if record.chunk_id in candidates]
    evidence: list[EvidenceChunk] = []
    for record in relevant_records:
        chunk = candidates[record.chunk_id]
        matching_domain = next(
            domain for domain in domains if domain in sources[record.doc_id].domains
        )
        evidence.append(
            replace(
                chunk,
                domain=matching_domain,
                conflict_flag=relevant_conflict(record, relevant_records),
            )
        )
    return evidence


def get_chunk(chunk_id: str) -> EvidenceChunk | None:
    """Trả evidence theo ID để UI và Ground Guard đọc breadcrumb gốc."""
    chunk = get_chunk_record(chunk_id)
    return _evidence_chunk(chunk, 1.0) if chunk is not None else None


def is_active(chunk_id: str) -> bool:
    """Chỉ chunk thuộc nguồn ACTIVE mới có thể là căn cứ trả lời tự động."""
    chunk = get_chunk_record(chunk_id)
    if chunk is None:
        return False
    source = get_source(chunk.doc_id)
    return source is not None and source.status is SourceStatus.ACTIVE


def supported_domains() -> list[Domain]:
    """Liệt kê domain có ít nhất một nguồn ACTIVE."""
    domains = {domain for source in list_sources(SourceStatus.ACTIVE) for domain in source.domains}
    return sorted(domains, key=lambda domain: domain.value)


def _evidence_chunk(
    chunk: ChunkRecord, score: float, *, expand: bool = True
) -> EvidenceChunk | None:
    source = get_source(chunk.doc_id)
    if source is None:
        LOGGER.warning("Chunk %s không có nguồn tương ứng.", chunk.chunk_id)
        return None
    if source.status is not SourceStatus.ACTIVE:
        return None
    try:
        effective_from = _date(source.effective_from, "effective_from")
        effective_to = _optional_date(source.effective_to)
    except ValueError as error:
        LOGGER.warning("Không thể dùng chunk %s: %s", chunk.chunk_id, error)
        return None
    return EvidenceChunk(
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        breadcrumb=chunk.breadcrumb,
        text=_article_context(chunk) if expand else chunk.text,
        domain=chunk.domain,
        label=chunk.label,
        score=score,
        effective_from=effective_from,
        effective_to=effective_to,
        applies_to=list(source.applies_to),
        cohorts=list(source.cohorts),
        transitional_clause=source.transitional_clause,
        conflict_flag=chunk.conflict_flag or (expand and _article_has_conflict(chunk)),
    )


def _article_context(chunk: ChunkRecord) -> str:
    if chunk.article_no is None:
        return chunk.text
    siblings = [
        sibling.text
        for sibling in list_chunks(chunk.doc_id)
        if sibling.article_no == chunk.article_no
    ]
    return "\n".join(siblings) or chunk.text


def _article_has_conflict(chunk: ChunkRecord) -> bool:
    return chunk.article_no is not None and any(
        sibling.conflict_flag
        for sibling in list_chunks(chunk.doc_id)
        if sibling.article_no == chunk.article_no
    )


def _date(value: str | None, field: str) -> date:
    if value is None:
        raise ValueError(f"Nguồn thiếu {field}.")
    return date.fromisoformat(value)


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value is not None else None


def _is_effective(chunk: EvidenceChunk, at: date | None) -> bool:
    return at is None or (
        chunk.effective_from <= at and (chunk.effective_to is None or at <= chunk.effective_to)
    )
