from dataclasses import replace
from collections.abc import Sequence
from time import perf_counter

from core.types import Domain, SourceStatus
from corpus.indexer import build_active_index, tokenize
from corpus.store import (
    ChunkRecord,
    SourceRecord,
    create_chunk,
    create_source,
    update_source,
)


class FakeEncoder:
    def encode(self, texts: Sequence[str], **_: object) -> list[list[float]]:
        return [
            [float("thang" in text.casefold()), float("điểm" in text.casefold())]
            for text in texts
        ]


def test_tokenize_keeps_vietnamese_diacritics() -> None:
    assert tokenize("Thang điểm rèn luyện") == ["thang", "điểm", "rèn", "luyện"]


def test_indexes_only_active_sources_and_ranks_hybrid_result(tmp_path) -> None:
    database_path = tmp_path / "corpus.db"
    active = create_source(
        SourceRecord(doc_id="active", status=SourceStatus.ACTIVE),
        database_path=database_path,
    )
    create_source(
        SourceRecord(doc_id="old", status=SourceStatus.SUPERSEDED),
        database_path=database_path,
    )
    create_chunk(
        ChunkRecord(
            "right",
            active.doc_id,
            "QĐ · Điều 8",
            "Điểm rèn luyện theo thang điểm 100.",
            Domain.CONDUCT_SCORE,
        ),
        database_path=database_path,
    )
    create_chunk(
        ChunkRecord(
            "old", "old", "QĐ cũ · Điều 1", "Thang điểm cũ.", Domain.CONDUCT_SCORE
        ),
        database_path=database_path,
    )

    started = perf_counter()
    index = build_active_index(database_path=database_path, encoder=FakeEncoder())
    found = index.search("thang điểm rèn luyện")

    assert perf_counter() - started < 0.3
    assert [chunk.chunk_id for chunk in index.chunks] == ["right"]
    assert found[0].chunk.chunk_id == "right"
    assert 0 <= found[0].score <= 1


def test_downgrade_removes_document_when_index_rebuilt(tmp_path) -> None:
    database_path = tmp_path / "corpus.db"
    source = create_source(
        SourceRecord(doc_id="active", status=SourceStatus.ACTIVE),
        database_path=database_path,
    )
    create_chunk(
        ChunkRecord(
            "chunk",
            source.doc_id,
            "QĐ · Điều 8",
            "Điểm rèn luyện.",
            Domain.CONDUCT_SCORE,
        ),
        database_path=database_path,
    )
    assert build_active_index(
        database_path=database_path, encoder=FakeEncoder()
    ).search("điểm")

    update_source(
        replace(source, status=SourceStatus.SUPERSEDED), database_path=database_path
    )
    assert (
        build_active_index(database_path=database_path, encoder=FakeEncoder()).search(
            "điểm"
        )
        == []
    )
