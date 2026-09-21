"""Facade đọc corpus ACTIVE cho Runtime."""

from __future__ import annotations

import logging
from datetime import date, datetime

from core.types import Domain, EvidenceChunk, SourceStatus
from corpus.indexer import search_active
from corpus.store import (
    ChunkRecord,
    compute_corpus_version,
    get_chunk_record,
    get_current_corpus_version,
    get_source,
    list_sources,
)

LOGGER = logging.getLogger(__name__)
RETRIEVAL_CANDIDATE_MULTIPLIER = 3


def get_corpus_version() -> str:
    """Trả phiên bản corpus đang hiệu lực, kể cả trước lần bump đầu tiên."""
    return get_current_corpus_version() or compute_corpus_version()


def search(
    query: str,
    domains: list[Domain],
    top_k: int = 6,
    at: datetime | None = None,
) -> list[EvidenceChunk]:
    """Tìm trong index ACTIVE, lọc domain và ngày hiệu lực trước khi trả evidence."""
    if top_k <= 0 or not domains:
        return []
    try:
        records = search_active(query, top_k=top_k * RETRIEVAL_CANDIDATE_MULTIPLIER)
    except (OSError, RuntimeError, ValueError) as error:
        LOGGER.warning("Không thể truy vấn index corpus: %s", error)
        return []
    requested_at = at.date() if at is not None else None
    chunks = [
        evidence
        for result in records
        if result.chunk.domain in domains
        if (evidence := _evidence_chunk(result.chunk, result.score)) is not None
        if _is_effective(evidence, requested_at)
    ]
    return chunks[:top_k]


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


def _evidence_chunk(chunk: ChunkRecord, score: float) -> EvidenceChunk | None:
    source = get_source(chunk.doc_id)
    if source is None:
        LOGGER.warning("Chunk %s không có nguồn tương ứng.", chunk.chunk_id)
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
        text=chunk.text,
        domain=chunk.domain,
        label=chunk.label,
        score=score,
        effective_from=effective_from,
        effective_to=effective_to,
        applies_to=list(source.applies_to),
        cohorts=list(source.cohorts),
        transitional_clause=source.transitional_clause,
        conflict_flag=chunk.conflict_flag,
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
