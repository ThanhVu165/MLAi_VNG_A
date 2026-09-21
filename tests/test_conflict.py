from pathlib import Path

from core.types import Domain, SourceStatus
from corpus.conflict import flag_active_conflicts, scheduled_supersede_ids
from corpus.lifecycle import pending_reviews, reject_source, request_change
from corpus.store import ChunkRecord, SourceRecord, create_chunk, create_source, get_chunk_record
from infra.audit import recent_events


def test_conflicting_active_sources_are_flagged_and_supersede_is_scheduled(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"
    previous = SourceRecord(doc_id="QD-2025", status=SourceStatus.ACTIVE)
    source_three = SourceRecord(doc_id="QD-2026-3", status=SourceStatus.ACTIVE)
    source_five = SourceRecord(doc_id="QD-2026-5", status=SourceStatus.ACTIVE)
    replacement = SourceRecord(
        doc_id="QD-2027", status=SourceStatus.PENDING_REVIEW, supersedes=(previous.doc_id,)
    )
    for source in (previous, source_three, source_five, replacement):
        create_source(source, database_path=database_path)

    first = ChunkRecord(
        "chunk-3",
        source_three.doc_id,
        "Điều 1",
        "Hạn chót rút học phần là 15/09/2026.",
        Domain.COURSE_WITHDRAWAL,
    )
    second = ChunkRecord(
        "chunk-5",
        source_five.doc_id,
        "Điều 2",
        "Hạn chót rút học phần là 20/09/2026.",
        Domain.COURSE_WITHDRAWAL,
    )
    create_chunk(first, database_path=database_path)
    create_chunk(second, database_path=database_path)

    pairs = flag_active_conflicts(actor="ADMIN:tester", database_path=database_path)

    assert [(pair.first_chunk_id, pair.second_chunk_id) for pair in pairs] == [
        ("chunk-3", "chunk-5")
    ]
    assert get_chunk_record("chunk-3", database_path=database_path).conflict_with == "chunk-5"
    assert get_chunk_record("chunk-5", database_path=database_path).conflict_with == "chunk-3"
    assert scheduled_supersede_ids(replacement, database_path=database_path) == ("QD-2025",)
    assert recent_events(database_path=str(database_path))[0].action == "SOURCE_METADATA_EDITED"


def test_pending_review_shows_diff_and_requires_reason(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"
    old = SourceRecord(doc_id="old", status=SourceStatus.ACTIVE)
    pending = SourceRecord(doc_id="new", status=SourceStatus.PENDING_REVIEW, supersedes=("old",))
    create_source(old, database_path=database_path)
    create_source(pending, database_path=database_path)
    create_chunk(
        ChunkRecord("old-1", "old", "Điều 1", "Nội dung cũ.", Domain.CONDUCT_SCORE),
        database_path=database_path,
    )
    create_chunk(
        ChunkRecord("new-1", "new", "Điều 1", "Nội dung mới.", Domain.CONDUCT_SCORE),
        database_path=database_path,
    )

    review = pending_reviews(database_path=database_path)[0]
    assert "-Nội dung cũ." in review.diff_lines
    assert "+Nội dung mới." in review.diff_lines
    request_change(
        pending, actor="ADMIN:test", reason="Bổ sung căn cứ.", database_path=database_path
    )
    assert (
        reject_source(
            pending, actor="ADMIN:test", reason="Sai ngày hiệu lực.", database_path=database_path
        ).status
        is SourceStatus.REJECTED
    )
