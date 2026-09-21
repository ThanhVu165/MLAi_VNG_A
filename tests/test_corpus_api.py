import inspect

from core.types import Domain, SourceStatus
from corpus import api
from corpus.indexer import SearchResult
from corpus.store import ChunkRecord, SourceRecord


def test_corpus_api_contract_is_available_with_an_empty_database(monkeypatch) -> None:
    monkeypatch.setattr(api, "search_active", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(api, "get_current_corpus_version", lambda: None)
    monkeypatch.setattr(api, "compute_corpus_version", lambda: "cv_empty")
    monkeypatch.setattr(api, "get_chunk_record", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(api, "list_sources", lambda *_args, **_kwargs: [])

    assert list(inspect.signature(api.search).parameters) == [
        "query",
        "domains",
        "top_k",
        "at",
    ]
    assert inspect.signature(api.search).parameters["top_k"].default == 6
    assert inspect.signature(api.search).parameters["at"].default is None
    assert api.get_corpus_version() == "cv_empty"
    assert api.search("câu hỏi", [Domain.CONDUCT_SCORE]) == []
    assert api.get_chunk("missing") is None
    assert api.is_active("missing") is False
    assert api.supported_domains() == []


def test_corpus_api_never_returns_a_non_active_source_chunk(monkeypatch) -> None:
    active = SourceRecord(doc_id="active", effective_from="2026-01-01", status=SourceStatus.ACTIVE)
    superseded = SourceRecord(
        doc_id="superseded", effective_from="2026-01-01", status=SourceStatus.SUPERSEDED
    )
    active_chunk = ChunkRecord(
        "active-chunk", "active", "Điều 1", "Nội dung.", Domain.CONDUCT_SCORE
    )
    old_chunk = ChunkRecord(
        "old-chunk", "superseded", "Điều 1", "Nội dung cũ.", Domain.CONDUCT_SCORE
    )
    sources = {active.doc_id: active, superseded.doc_id: superseded}
    chunks = {active_chunk.chunk_id: active_chunk, old_chunk.chunk_id: old_chunk}
    monkeypatch.setattr(
        api,
        "search_active",
        lambda *_args, **_kwargs: [
            SearchResult(active_chunk, 1.0, 1.0, 1.0),
            SearchResult(old_chunk, 0.9, 0.9, 0.9),
        ],
    )
    monkeypatch.setattr(api, "get_source", lambda doc_id: sources.get(doc_id))
    monkeypatch.setattr(api, "get_chunk_record", lambda chunk_id: chunks.get(chunk_id))

    assert [chunk.chunk_id for chunk in api.search("nội dung", [Domain.CONDUCT_SCORE])] == [
        "active-chunk"
    ]
    assert api.get_chunk("old-chunk") is None
    assert api.is_active("old-chunk") is False
