from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from core.types import ChunkLabel, Domain, SourceStatus
from corpus.api import get_chunk, get_corpus_version, search, supported_domains
from corpus.intake import ingest_file, ingest_text, ingest_url
from corpus.store import (
    ChunkRecord,
    CorpusVersionRecord,
    SourceRecord,
    bump_corpus_version,
    compute_corpus_version,
    create_chunk,
    create_corpus_version,
    create_source,
    delete_chunk,
    delete_corpus_version,
    delete_source,
    get_chunk_record,
    get_corpus_version_record,
    get_current_corpus_version,
    get_source,
    list_sources,
    update_chunk,
    update_corpus_version,
    update_source,
)
from infra.audit import recent_events


def test_stub_corpus_api_exposes_contract_chunks() -> None:
    domains = supported_domains()
    chunks = [chunk for domain in domains for chunk in search("", [domain])]

    assert domains == [Domain.CONDUCT_SCORE, Domain.COURSE_WITHDRAWAL, Domain.GRADE_APPEAL]
    assert get_corpus_version() == "stub-v1"
    assert len(chunks) == 12
    assert sum(chunk.label is ChunkLabel.HUMAN_ONLY for chunk in chunks) == 2
    assert sum(chunk.transitional_clause for chunk in chunks) == 1
    assert get_chunk(chunks[0].chunk_id) == chunks[0]


def test_search_filters_domains_and_limits_results() -> None:
    chunks = search(
        "Hạn chót rút học phần là khi nào?",
        [Domain.COURSE_WITHDRAWAL],
        top_k=2,
        at=datetime(2026, 9, 21, tzinfo=timezone.utc),
    )

    assert len(chunks) == 2
    assert {chunk.domain for chunk in chunks} == {Domain.COURSE_WITHDRAWAL}


def test_store_versions_only_active_sources(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"
    pending = SourceRecord(doc_id="source-1", content_hash="first")

    stored_pending = create_source(pending, database_path=database_path)
    empty_version = compute_corpus_version(database_path=database_path)
    assert get_source("source-1", database_path=database_path) == stored_pending

    update_source(
        replace(stored_pending, status=SourceStatus.ACTIVE),
        database_path=database_path,
    )
    active_version = bump_corpus_version(
        "ADMIN:tester", "Kích hoạt nguồn", database_path=database_path
    )
    assert active_version != empty_version
    assert get_current_corpus_version(database_path=database_path) == active_version

    update_source(
        replace(stored_pending, status=SourceStatus.SUPERSEDED),
        database_path=database_path,
    )
    assert (
        bump_corpus_version("ADMIN:tester", "Hạ cấp nguồn", database_path=database_path)
        == empty_version
    )


def test_store_crud_for_chunks_and_versions(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"
    source = SourceRecord(doc_id="source-1", content_hash="first")
    chunk = ChunkRecord(
        chunk_id="chunk-1",
        doc_id=source.doc_id,
        breadcrumb="QĐ 1 · Điều 1",
        text="Nội dung nguồn.",
        domain=Domain.CONDUCT_SCORE,
    )
    version = CorpusVersionRecord("cv_manual", "ADMIN:tester", "Ghi chú", (source.doc_id,))

    create_source(source, database_path=database_path)
    create_chunk(chunk, database_path=database_path)
    assert get_chunk_record(chunk.chunk_id, database_path=database_path) == chunk

    updated_chunk = replace(chunk, label=ChunkLabel.AUTO_ANSWERABLE)
    update_chunk(updated_chunk, database_path=database_path)
    assert get_chunk_record(chunk.chunk_id, database_path=database_path) == updated_chunk

    stored_version = create_corpus_version(version, database_path=database_path)
    updated_version = replace(stored_version, note="Đã sửa")
    update_corpus_version(updated_version, database_path=database_path)
    assert (
        get_corpus_version_record(version.corpus_version, database_path=database_path)
        == updated_version
    )

    delete_chunk(chunk.chunk_id, database_path=database_path)
    delete_corpus_version(version.corpus_version, database_path=database_path)
    delete_source(source.doc_id, database_path=database_path)
    assert get_chunk_record(chunk.chunk_id, database_path=database_path) is None
    assert get_corpus_version_record(version.corpus_version, database_path=database_path) is None
    assert get_source(source.doc_id, database_path=database_path) is None


def test_intake_deduplicates_content_and_writes_audit(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"

    first = ingest_text(
        "Điều 1. Nội dung quy định.",
        actor="ADMIN:tester",
        database_path=database_path,
    )
    duplicate = ingest_text(
        "Điều 1. Nội dung quy định.",
        actor="ADMIN:tester",
        database_path=database_path,
    )

    assert first.created is True
    assert duplicate.created is False
    assert duplicate.message == "Tài liệu không thay đổi"
    assert len(list_sources(database_path=database_path)) == 1
    assert [event.action for event in recent_events(database_path=str(database_path))] == [
        "SOURCE_UPLOADED"
    ]


def test_intake_accepts_supported_files_and_manual_url(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"

    uploaded = ingest_file(
        b"%PDF-1.7", "quy_dinh.pdf", actor="ADMIN:tester", database_path=database_path
    )
    downloaded = ingest_url(
        "https://example.edu/quy-dinh.docx",
        actor="ADMIN:tester",
        fetch=lambda _: b"docx bytes",
        database_path=database_path,
    )

    assert uploaded.source.source_kind == "pdf"
    assert downloaded.source.source_kind == "url"
    assert downloaded.source.source_url == "https://example.edu/quy-dinh.docx"
