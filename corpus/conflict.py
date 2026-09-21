"""Phát hiện mâu thuẫn nguồn và chuẩn bị danh sách hạ cấp khi kích hoạt."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
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
    active_ids = {
        source.doc_id for source in list_sources(SourceStatus.ACTIVE, database_path=database_path)
    }
    chunks = [
        chunk for chunk in list_chunks(database_path=database_path) if chunk.doc_id in active_ids
    ]
    pairs: list[ConflictPair] = []
    for first, second in combinations(chunks, 2):
        if first.doc_id == second.doc_id or not _conflicts(first, second):
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
    return pairs


def _conflicts(first: ChunkRecord, second: ChunkRecord) -> bool:
    return (
        first.domain == second.domain
        and first.article_no == second.article_no
        and first.clause_no == second.clause_no
        and _same_topic(first.text, second.text)
        and _numbers(first.text) != _numbers(second.text)
    )


def _same_topic(first: str, second: str) -> bool:
    first_words, second_words = _topic_words(first), _topic_words(second)
    shared_words = first_words & second_words
    return len(shared_words) >= MIN_SHARED_TOPIC_WORDS and (
        len(shared_words) / min(len(first_words), len(second_words)) >= MIN_TOPIC_OVERLAP
    )


def _topic_words(text: str) -> set[str]:
    return {word.lower() for word in WORD_PATTERN.findall(text) if word.lower() not in STOP_WORDS}


def _numbers(text: str) -> set[str]:
    return set(NUMBER_PATTERN.findall(text))


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
