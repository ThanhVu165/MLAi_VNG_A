"""Hàng chờ duyệt nguồn và diff trước khi kích hoạt."""

from __future__ import annotations

from dataclasses import dataclass, replace
from difflib import unified_diff

from core.types import SourceStatus
from corpus.conflict import scheduled_supersede_ids
from corpus.store import (
    ChunkRecord,
    DatabasePath,
    SourceRecord,
    bump_corpus_version,
    get_source,
    list_chunks,
    list_sources,
    update_source,
)
from infra.audit import log_event
from infra.db import now_iso


@dataclass(frozen=True)
class PendingReview:
    source: SourceRecord
    chunks: list[ChunkRecord]
    previous_text: str
    proposed_text: str
    diff_lines: list[str]


def pending_reviews(*, database_path: DatabasePath = None) -> list[PendingReview]:
    """Trả nguồn chờ duyệt cùng nhãn chunk và diff nguồn bị thay thế."""
    return [
        _review(source, database_path=database_path)
        for source in list_sources(SourceStatus.PENDING_REVIEW, database_path=database_path)
    ]


def reject_source(
    source: SourceRecord, *, actor: str, reason: str, database_path: DatabasePath = None
) -> SourceRecord:
    """Từ chối nguồn chờ duyệt với lý do bắt buộc."""
    _require_reason(reason)
    rejected = replace(source, status=SourceStatus.REJECTED)
    update_source(rejected, database_path=database_path)
    log_event(
        case_id=None,
        actor=actor,
        action="REJECT_SOURCE",
        output_ref=source.doc_id,
        reason=reason,
        sources=[source.doc_id],
        database_path=str(database_path) if database_path else None,
    )
    return rejected


def request_change(
    source: SourceRecord, *, actor: str, reason: str, database_path: DatabasePath = None
) -> None:
    """Lưu yêu cầu chỉnh sửa; nguồn vẫn ở PENDING_REVIEW."""
    _require_reason(reason)
    log_event(
        case_id=None,
        actor=actor,
        action="SOURCE_METADATA_EDITED",
        output_ref=source.doc_id,
        reason=f"Yêu cầu chỉnh sửa: {reason}",
        sources=[source.doc_id],
        database_path=str(database_path) if database_path else None,
    )


def approve_for_activation(
    source: SourceRecord, *, actor: str, reason: str, database_path: DatabasePath = None
) -> None:
    """Ghi nhận duyệt, vẫn để nguồn ở PENDING_REVIEW cho B-11 kích hoạt."""
    _require_reason(reason)
    log_event(
        case_id=None,
        actor=actor,
        action="SOURCE_METADATA_EDITED",
        output_ref=source.doc_id,
        reason=f"Đã duyệt để kích hoạt: {reason}",
        sources=[source.doc_id],
        database_path=str(database_path) if database_path else None,
    )


def activate_source(
    source: SourceRecord, *, actor: str, reason: str, database_path: DatabasePath = None
) -> SourceRecord:
    """Kích hoạt nguồn đã duyệt, hạ nguồn bị thay và tăng phiên bản corpus."""
    _require_reason(reason)
    _require_admin_actor(actor)
    stored = get_source(source.doc_id, database_path=database_path)
    if stored is None:
        raise KeyError(f"Không tìm thấy nguồn {source.doc_id}.")
    if stored.status is not SourceStatus.PENDING_REVIEW:
        raise ValueError("Chỉ nguồn PENDING_REVIEW mới được kích hoạt.")

    activated_at = now_iso()
    activated = replace(
        stored,
        status=SourceStatus.ACTIVE,
        activated_at=activated_at,
        activated_by=actor,
    )
    update_source(activated, database_path=database_path)
    _supersede_scheduled_sources(activated, activated_at, database_path=database_path)
    corpus_version = bump_corpus_version(
        actor, f"Kích hoạt nguồn {activated.doc_id}.", database_path=database_path
    )
    log_event(
        case_id=None,
        actor=actor,
        action="ACTIVATE_SOURCE",
        input_ref=activated.doc_id,
        output_ref="ACTIVE",
        reason=reason,
        sources=[activated.doc_id],
        corpus_version=corpus_version,
        database_path=str(database_path) if database_path is not None else None,
    )
    return activated


def _review(source: SourceRecord, *, database_path: DatabasePath) -> PendingReview:
    chunks = list_chunks(source.doc_id, database_path=database_path)
    previous_chunks = [
        chunk
        for doc_id in source.supersedes
        for chunk in list_chunks(doc_id, database_path=database_path)
    ]
    previous_text = "\n".join(chunk.text for chunk in previous_chunks)
    proposed_text = "\n".join(chunk.text for chunk in chunks)
    return PendingReview(
        source,
        chunks,
        previous_text,
        proposed_text,
        list(
            unified_diff(
                previous_text.splitlines(),
                proposed_text.splitlines(),
                fromfile="phiên bản cũ",
                tofile="bản đề xuất",
                lineterm="",
            )
        ),
    )


def _require_reason(reason: str) -> None:
    if not reason.strip():
        raise ValueError("Cần nhập lý do.")


def _require_admin_actor(actor: str) -> None:
    if not actor.startswith("ADMIN:") or not actor.removeprefix("ADMIN:").strip():
        raise ValueError("Kích hoạt nguồn phải do ADMIN:<người_dùng> thực hiện.")


def _supersede_scheduled_sources(
    source: SourceRecord, superseded_at: str, *, database_path: DatabasePath
) -> None:
    for doc_id in scheduled_supersede_ids(source, database_path=database_path):
        previous = get_source(doc_id, database_path=database_path)
        if previous is not None:
            update_source(
                replace(
                    previous,
                    status=SourceStatus.SUPERSEDED,
                    superseded_by=source.doc_id,
                    superseded_at=superseded_at,
                ),
                database_path=database_path,
            )
