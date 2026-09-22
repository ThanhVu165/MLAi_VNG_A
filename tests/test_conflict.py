from pathlib import Path
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from core.types import Domain, SourceStatus
from corpus import api
from corpus.conflict import flag_active_conflicts, scheduled_supersede_ids
from corpus.indexer import active_chunks
from corpus.lifecycle import (
    activate_source,
    flag_cases_for_recheck,
    pending_reviews,
    reject_source,
    request_change,
    rollback_source,
)
from corpus.seed import ensure_seeded
from corpus.store import (
    ChunkRecord,
    SourceRecord,
    SourceContent,
    create_chunk,
    create_source,
    get_chunk_record,
    get_current_corpus_version,
    get_source,
    save_source_content,
    update_source,
)
from infra.audit import recent_events
from infra import db
from infra.db import execute, now_iso


def test_conflicting_active_sources_are_flagged_and_supersede_is_scheduled(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "corpus.db"
    previous = SourceRecord(doc_id="QD-2025", status=SourceStatus.ACTIVE)
    source_three = SourceRecord(doc_id="QD-2026-3", status=SourceStatus.ACTIVE)
    source_five = SourceRecord(doc_id="QD-2026-5", status=SourceStatus.ACTIVE)
    replacement = SourceRecord(
        doc_id="QD-2027",
        status=SourceStatus.PENDING_REVIEW,
        supersedes=(previous.doc_id,),
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
    stored_first = get_chunk_record("chunk-3", database_path=database_path)
    stored_second = get_chunk_record("chunk-5", database_path=database_path)
    assert stored_first is not None and stored_first.conflict_with == "chunk-5"
    assert stored_second is not None and stored_second.conflict_with == "chunk-3"
    assert scheduled_supersede_ids(replacement, database_path=database_path) == ("QD-2025",)
    assert recent_events(database_path=str(database_path))[0].action == "SOURCE_METADATA_EDITED"


def test_seed_refund_conflict_is_limited_to_matching_legal_unit(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"
    ensure_seeded(database_path=database_path)

    pairs = flag_active_conflicts(actor="ADMIN:tester", database_path=database_path)

    assert [(pair.first_chunk_id, pair.second_chunk_id) for pair in pairs] == [
        ("HP-2026-1:seed:8", "RH-2026-101:seed:8")
    ]


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
        pending,
        actor="ADMIN:test",
        reason="Bổ sung căn cứ.",
        database_path=database_path,
    )
    assert (
        reject_source(
            pending,
            actor="ADMIN:test",
            reason="Sai ngày hiệu lực.",
            database_path=database_path,
        ).status
        is SourceStatus.REJECTED
    )


def test_activate_source_records_human_audit_version_and_scheduled_supersede(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "corpus.db"
    previous = SourceRecord(doc_id="old", status=SourceStatus.ACTIVE, content_hash="old")
    pending = SourceRecord(
        doc_id="new",
        status=SourceStatus.PENDING_REVIEW,
        supersedes=(previous.doc_id,),
        content_hash="new",
        title="Quy định mới",
        issuer="Phòng CTSV giả lập",
        effective_from="2026-07-07",
        applies_to=("undergraduate",),
        domains=(Domain.CONDUCT_SCORE,),
    )
    create_source(previous, database_path=database_path)
    create_source(pending, database_path=database_path)
    save_source_content(
        SourceContent(pending.doc_id, "Nội dung mới.".encode(), "Nội dung mới.", "quy-dinh.txt"),
        database_path=database_path,
    )
    create_chunk(
        ChunkRecord("old-1", previous.doc_id, "Điều 1", "Nội dung cũ.", Domain.CONDUCT_SCORE),
        database_path=database_path,
    )
    create_chunk(
        ChunkRecord("new-1", pending.doc_id, "Điều 1", "Nội dung mới.", Domain.CONDUCT_SCORE),
        database_path=database_path,
    )

    activated = activate_source(
        pending,
        actor="ADMIN:lan",
        reason="Đã duyệt quy định mới.",
        database_path=database_path,
    )

    superseded = get_source(previous.doc_id, database_path=database_path)
    events = recent_events(database_path=str(database_path))
    assert activated.status is SourceStatus.ACTIVE
    assert activated.activated_by == "ADMIN:lan"
    assert activated.activated_at is not None and activated.activated_at.endswith("Z")
    assert superseded is not None and superseded.status is SourceStatus.SUPERSEDED
    assert superseded.superseded_by == activated.doc_id
    assert superseded.superseded_at == activated.activated_at
    assert get_current_corpus_version(database_path=database_path) is not None
    assert [chunk.doc_id for chunk in active_chunks(database_path=database_path)] == [
        activated.doc_id
    ]
    assert events[0].action == "ACTIVATE_SOURCE"
    assert events[0].actor == "ADMIN:lan"
    assert events[0].reason == "Đã duyệt quy định mới."
    assert events[0].sources == [activated.doc_id]
    assert events[0].corpus_version == get_current_corpus_version(database_path=database_path)
    assert events[1].action == "SUPERSEDE_SOURCE"
    assert events[1].actor == "ADMIN:lan"
    assert events[1].sources == [previous.doc_id, activated.doc_id]


def test_superseded_source_flags_recent_cases_using_its_chunks(tmp_path: Path) -> None:
    database_path = tmp_path / "corpus.db"
    execute(
        "INSERT INTO cases (case_id, trace_id, channel, created_at, status, corpus_version) VALUES (?, ?, ?, ?, ?, ?)",
        ("case-1", "trace-1", "paste", now_iso(), "RESOLVED", "cv-old"),
        database_path=database_path,
    )
    execute(
        "INSERT INTO decisions (decision_id, case_id, decision, rule_id, reason, evidence_ids_json, corpus_version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "decision-1",
            "case-1",
            "AUTO_REPLY",
            "P01",
            "Đủ căn cứ.",
            '["old:chunk:1"]',
            "cv-old",
            now_iso(),
        ),
        database_path=database_path,
    )

    assert flag_cases_for_recheck("old", actor="ADMIN:lan", database_path=database_path) == [
        "case-1"
    ]
    assert [event.action for event in recent_events(database_path=str(database_path))] == [
        "FLAG_NEEDS_RECHECK"
    ]


def test_conflicts_require_overlapping_dates_and_cohorts_not_article_numbers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "overlap.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    first = SourceRecord(
        "first",
        status=SourceStatus.ACTIVE,
        effective_from="2026-01-01",
        effective_to="2026-06-30",
        cohorts=("K49",),
    )
    second = SourceRecord(
        "second", status=SourceStatus.ACTIVE, effective_from="2026-07-01", cohorts=("K49",)
    )
    for source in (first, second):
        create_source(source, database_path=database_path)
    for source, article, rate in ((first, "1", "70"), (second, "9", "60")):
        create_chunk(
            ChunkRecord(
                source.doc_id + ":1",
                source.doc_id,
                f"Điều {article}",
                f"Khoản 1. Hoàn học phí {rate} phần trăm.",
                Domain.COURSE_WITHDRAWAL,
                article_no=article,
            ),
            database_path=database_path,
        )
    assert flag_active_conflicts(actor="ADMIN:test", database_path=database_path) == []
    update_source(replace(first, effective_to=None, cohorts=("K48",)), database_path=database_path)
    assert flag_active_conflicts(actor="ADMIN:test", database_path=database_path) == []
    update_source(
        replace(
            first, effective_to=None, cohorts=("K48", "K49"), domains=(Domain.COURSE_WITHDRAWAL,)
        ),
        database_path=database_path,
    )
    update_source(replace(second, domains=(Domain.COURSE_WITHDRAWAL,)), database_path=database_path)
    assert len(flag_active_conflicts(actor="ADMIN:test", database_path=database_path)) == 1
    at = datetime(2026, 9, 22, tzinfo=timezone.utc)
    earlier = datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert not any(
        item.conflict_flag
        for item in api.available_evidence([Domain.COURSE_WITHDRAWAL], at, cohort="K48")
    )
    assert all(
        item.conflict_flag
        for item in api.available_evidence([Domain.COURSE_WITHDRAWAL], at, cohort="K49")
    )
    assert not any(
        item.conflict_flag
        for item in api.available_evidence([Domain.COURSE_WITHDRAWAL], earlier, cohort="K49")
    )


def test_rollback_requires_original_and_recomputes_current_conflicts(tmp_path: Path) -> None:
    path = tmp_path / "rollback.db"
    archived = create_source(
        SourceRecord("archived", status=SourceStatus.SUPERSEDED), database_path=path
    )
    with pytest.raises(ValueError):
        rollback_source(archived, actor="ADMIN:test", reason="Khôi phục", database_path=path)
    archived = replace(
        archived,
        title="Nguồn cũ",
        issuer="Đơn vị giả lập",
        effective_from="2026-01-01",
        applies_to=("undergraduate",),
        domains=(Domain.COURSE_WITHDRAWAL,),
    )
    update_source(archived, database_path=path)
    save_source_content(
        SourceContent(archived.doc_id, b"original", "Hoàn học phí 70 phần trăm."),
        database_path=path,
    )
    create_source(replace(archived, doc_id="other", status=SourceStatus.ACTIVE), database_path=path)
    for doc_id, rate in (("archived", "70"), ("other", "60")):
        create_chunk(
            ChunkRecord(
                doc_id + ":1",
                doc_id,
                "Điều 1",
                f"Hoàn học phí {rate} phần trăm.",
                Domain.COURSE_WITHDRAWAL,
            ),
            database_path=path,
        )
    restored = rollback_source(
        archived, actor="ADMIN:test", reason="Đã xác nhận bản gốc", database_path=path
    )
    assert restored.status is SourceStatus.ACTIVE
    chunk = get_chunk_record("archived:1", database_path=path)
    assert chunk is not None and chunk.conflict_flag
