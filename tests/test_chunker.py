from datetime import datetime, timezone

from core.types import ChunkLabel, Domain
from corpus.api import get_chunk, get_corpus_version, search, supported_domains


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
