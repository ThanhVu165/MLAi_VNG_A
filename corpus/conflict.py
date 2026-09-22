"""Phát hiện mâu thuẫn nguồn và chuẩn bị danh sách hạ cấp khi kích hoạt."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date
from itertools import combinations

from core.types import SourceStatus
from corpus.store import (
    ChunkRecord,
    DatabasePath,
    SourceRecord,
    get_source,
    list_chunks,
    list_sources,
    update_chunk,
)
from infra.audit import log_event

NUMBER_PATTERN = re.compile(r"\b\d+(?:[/-]\d+)*\b")
LEGAL_PREFIX = re.compile(r"^(?:Điều\s+\w+\.|Khoản\s+\w+\.|(?:Điểm\s+)?[a-zđ]\))\s*", re.I)
WORD_PATTERN = re.compile(r"[A-Za-zÀ-ỹ]{3,}")
STOP_WORDS = frozenset(
    {"các", "cho", "của", "được", "học", "khi", "là", "này", "theo", "trong", "và"}
)
MIN_SHARED_TOPIC_WORDS = 2
MIN_TOPIC_OVERLAP = 0.5


@dataclass(frozen=True)
class ConflictPair:
    first_chunk_id: str
    second_chunk_id: str


def scheduled_supersede_ids(
    source: SourceRecord, *, database_path: DatabasePath = None
) -> tuple[str, ...]:
    """Trả tài liệu ACTIVE cần hạ cấp khi ``source`` được kích hoạt ở B-11."""
    return tuple(
        doc_id
        for doc_id in source.supersedes
        if (previous := get_source(doc_id, database_path=database_path))
        and previous.status is SourceStatus.ACTIVE
    )


def flag_active_conflicts(
    *,
    actor: str,
    database_path: DatabasePath = None,
) -> list[ConflictPair]:
    """Gắn cờ các chunk ACTIVE cùng chủ đề nhưng có mốc số khác nhau."""
    sources = {
        source.doc_id: source
        for source in list_sources(SourceStatus.ACTIVE, database_path=database_path)
    }
    chunks = [
        chunk for chunk in list_chunks(database_path=database_path) if chunk.doc_id in sources
    ]
    pairs: list[ConflictPair] = []
    for first, second in combinations(chunks, 2):
        if (
            first.doc_id == second.doc_id
            or not _scopes_overlap(sources[first.doc_id], sources[second.doc_id])
            or not _conflicts(first, second)
        ):
            continue
        update_chunk(
            replace(first, conflict_flag=True, conflict_with=second.chunk_id),
            database_path=database_path,
        )
        update_chunk(
            replace(second, conflict_flag=True, conflict_with=first.chunk_id),
            database_path=database_path,
        )
        _log_conflict(first, second, actor=actor, database_path=database_path)
        pairs.append(ConflictPair(first.chunk_id, second.chunk_id))
    flagged_ids = {
        chunk_id for pair in pairs for chunk_id in (pair.first_chunk_id, pair.second_chunk_id)
    }
    for chunk in chunks:
        if chunk.conflict_flag and chunk.chunk_id not in flagged_ids:
            update_chunk(
                replace(chunk, conflict_flag=False, conflict_with=None), database_path=database_path
            )
            log_event(
                case_id=None,
                actor=actor,
                action="SOURCE_METADATA_EDITED",
                input_ref=chunk.chunk_id,
                reason="Đã đối chiếu lại: đoạn này không còn cặp mâu thuẫn trong cùng phạm vi áp dụng.",
                sources=[chunk.doc_id],
                database_path=str(database_path) if database_path else None,
            )
    return pairs


def _conflicts(first: ChunkRecord, second: ChunkRecord) -> bool:
    return (
        first.domain == second.domain
        and _same_topic(first.text, second.text)
        and bool(_numbers(first.text))
        and bool(_numbers(second.text))
        and _numbers(first.text) != _numbers(second.text)
    )


def relevant_conflict(chunk: ChunkRecord, candidates: list[ChunkRecord]) -> bool:
    """Cờ dành cho email: chỉ xét đối phương còn trong phạm vi của email đó."""
    if not chunk.conflict_flag:
        return False
    if chunk.conflict_flag and not chunk.conflict_with:
        return True
    return any(other.doc_id != chunk.doc_id and _conflicts(chunk, other) for other in candidates)


def _scopes_overlap(first: SourceRecord, second: SourceRecord) -> bool:
    for left, right in ((first.applies_to, second.applies_to), (first.cohorts, second.cohorts)):
        if left and right and not set(left) & set(right):
            return False
    first_start = date.fromisoformat(first.effective_from) if first.effective_from else date.min
    second_start = date.fromisoformat(second.effective_from) if second.effective_from else date.min
    first_end = date.fromisoformat(first.effective_to) if first.effective_to else date.max
    second_end = date.fromisoformat(second.effective_to) if second.effective_to else date.max
    return max(first_start, second_start) <= min(first_end, second_end)


def _same_topic(first: str, second: str) -> bool:
    first_words, second_words = _topic_words(first), _topic_words(second)
    shared_words = first_words & second_words
    return len(shared_words) >= MIN_SHARED_TOPIC_WORDS and (
        len(shared_words) / min(len(first_words), len(second_words)) >= MIN_TOPIC_OVERLAP
    )


def _topic_words(text: str) -> set[str]:
    return {word.lower() for word in WORD_PATTERN.findall(text) if word.lower() not in STOP_WORDS}


def _numbers(text: str) -> set[str]:
    return set(NUMBER_PATTERN.findall(LEGAL_PREFIX.sub("", text)))


def _log_conflict(
    first: ChunkRecord,
    second: ChunkRecord,
    *,
    actor: str,
    database_path: DatabasePath,
) -> None:
    log_event(
        case_id=None,
        actor=actor,
        action="SOURCE_METADATA_EDITED",
        input_ref=first.chunk_id,
        output_ref=second.chunk_id,
        reason="Đã gắn cờ mâu thuẫn giữa hai chunk cùng chủ đề có mốc số khác nhau.",
        sources=[first.doc_id, second.doc_id],
        database_path=str(database_path) if database_path is not None else None,
    )
