from pathlib import Path

from core.types import Domain, SourceStatus
from corpus.conflict import flag_active_conflicts, scheduled_supersede_ids
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
