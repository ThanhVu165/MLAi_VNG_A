"""Hàng chờ duyệt nguồn và diff trước khi kích hoạt."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from difflib import unified_diff

from core.types import Domain, SourceStatus
from corpus.conflict import flag_active_conflicts, scheduled_supersede_ids
from corpus.store import (
    ChunkRecord,
    DatabasePath,
    SourceRecord,
    bump_corpus_version,
    get_source,
    get_source_content,
    list_chunks,
    list_sources,
    update_source,
)
from infra.audit import log_event
from infra.db import execute, fetch_all, now_iso, transaction


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
    with transaction(database_path):
        _require_reason(reason)
        _require_admin_actor(actor)
        stored = get_source(source.doc_id, database_path=database_path)
        if stored is None or stored.status is not SourceStatus.PENDING_REVIEW:
            raise ValueError("Nguồn không còn chờ xác nhận. Hãy tải lại danh sách trước khi thao tác.")
        affected = execute(
            "UPDATE sources SET status = ? WHERE doc_id = ? AND status = ?",
            (SourceStatus.REJECTED, stored.doc_id, SourceStatus.PENDING_REVIEW),
            database_path=database_path,
        )
        if affected != 1:
            raise ValueError("Nguồn vừa được xử lý ở nơi khác. Hãy tải lại danh sách.")
        rejected = replace(stored, status=SourceStatus.REJECTED)
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
    with transaction(database_path):
        _require_reason(reason)
        _require_admin_actor(actor)
        stored = get_source(source.doc_id, database_path=database_path)
        if stored is None:
            raise KeyError(f"Không tìm thấy nguồn {source.doc_id}.")
        if stored.status is not SourceStatus.PENDING_REVIEW:
            raise ValueError("Chỉ có thể đưa vào sử dụng nguồn đang chờ xác nhận. Hãy tải lại danh sách.")
        if not list_chunks(stored.doc_id, database_path=database_path):
            raise ValueError("Tài liệu chưa có nội dung; hãy chuẩn bị bản gốc trước khi duyệt.")
        _validate_approval(stored, database_path=database_path)

        activated_at = now_iso()
        activated = replace(
            stored,
            status=SourceStatus.ACTIVE,
            activated_at=activated_at,
            activated_by=actor,
        )
        update_source(activated, database_path=database_path)
        _supersede_scheduled_sources(activated, activated_at, actor, database_path=database_path)
        flag_active_conflicts(actor=actor, database_path=database_path)
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


def _validate_approval(source: SourceRecord, *, database_path: DatabasePath) -> None:
    original = get_source_content(source.doc_id, database_path=database_path)
    if original is None or not original.content or not original.extracted_text.strip():
        raise ValueError("Không thể duyệt nguồn thiếu bản gốc hoặc nội dung đã đọc.")
    if not list_chunks(source.doc_id, database_path=database_path):
        raise ValueError("Nguồn chưa có đoạn căn cứ; hãy chuẩn bị nội dung trước khi duyệt.")
    if not source.title or not source.issuer or not source.effective_from or not source.applies_to:
        raise ValueError("Cần tên nguồn, đơn vị ban hành, ngày hiệu lực và đối tượng áp dụng.")
    if not source.domains or Domain.UNKNOWN in source.domains:
        raise ValueError("Hãy xác nhận lĩnh vực được hỗ trợ trước khi duyệt.")
    start = date.fromisoformat(source.effective_from)
    if source.effective_to and start > date.fromisoformat(source.effective_to):
        raise ValueError("Ngày hết hiệu lực phải sau hoặc bằng ngày bắt đầu.")
    if source.transitional_clause and not source.cohorts:
        raise ValueError("Nguồn có điều khoản chuyển tiếp cần xác nhận khóa áp dụng.")


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
        raise ValueError("Hãy nhập tên người quản trị trước khi xác nhận nguồn.")


def _supersede_scheduled_sources(
    source: SourceRecord, superseded_at: str, actor: str, *, database_path: DatabasePath
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
            log_event(
                case_id=None,
                actor=actor,
                action="SUPERSEDE_SOURCE",
                input_ref=previous.doc_id,
                output_ref=source.doc_id,
                reason=f"Nguồn {previous.doc_id} được thay thế bởi {source.doc_id}.",
                sources=[previous.doc_id, source.doc_id],
                database_path=str(database_path) if database_path is not None else None,
            )
            flag_cases_for_recheck(previous.doc_id, actor=actor, database_path=database_path)


def flag_cases_for_recheck(
    doc_id: str, *, actor: str, database_path: DatabasePath = None
) -> list[str]:
    """Đánh dấu case 30 ngày gần nhất đã trích dẫn chunk của nguồn bị hạ cấp."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
    rows = fetch_all(
        """SELECT c.case_id, d.evidence_ids_json FROM cases c
           JOIN decisions d ON d.case_id = c.case_id WHERE c.created_at >= ?""",
        (cutoff,),
        database_path=database_path,
    )
    case_ids = [
        row["case_id"]
        for row in rows
        if any(
            str(chunk_id).startswith(f"{doc_id}:")
            for chunk_id in json.loads(row["evidence_ids_json"] or "[]")
        )
    ]
    for case_id in case_ids:
        execute(
            "UPDATE cases SET status = ? WHERE case_id = ?",
            ("NEEDS_RECHECK", case_id),
            database_path=database_path,
        )
        log_event(
            case_id=case_id,
            actor=actor,
            action="FLAG_NEEDS_RECHECK",
            input_ref=doc_id,
            output_ref="NEEDS_RECHECK",
            reason=f"Nguồn {doc_id} không còn ACTIVE; cần kiểm tra lại căn cứ.",
            sources=[doc_id],
            database_path=str(database_path) if database_path is not None else None,
        )
    return case_ids


def rollback_source(
    source: SourceRecord, *, actor: str, reason: str, database_path: DatabasePath = None
) -> SourceRecord:
    """Khôi phục nguồn SUPERSEDED và hạ nguồn đang thay thế nó."""
    with transaction(database_path):
        _require_reason(reason)
        _require_admin_actor(actor)
        stored = get_source(source.doc_id, database_path=database_path)
        if stored is None or stored.status is not SourceStatus.SUPERSEDED:
            raise ValueError("Chỉ có thể rollback nguồn SUPERSEDED.")
        _validate_approval(stored, database_path=database_path)
        replacement = get_source(stored.superseded_by or "", database_path=database_path)
        if replacement is not None and replacement.status is SourceStatus.ACTIVE:
            update_source(
                replace(
                    replacement,
                    status=SourceStatus.SUPERSEDED,
                    superseded_by=stored.doc_id,
                    superseded_at=now_iso(),
                ),
                database_path=database_path,
            )
            flag_cases_for_recheck(replacement.doc_id, actor=actor, database_path=database_path)
        restored = replace(stored, status=SourceStatus.ACTIVE, superseded_by=None, superseded_at=None)
        update_source(restored, database_path=database_path)
        flag_active_conflicts(actor=actor, database_path=database_path)
        corpus_version = bump_corpus_version(
            actor, f"Rollback nguồn {restored.doc_id}.", database_path=database_path
        )
        log_event(
            case_id=None,
            actor=actor,
            action="ROLLBACK_SOURCE",
            input_ref=restored.doc_id,
            output_ref="ACTIVE",
            reason=reason,
            sources=[restored.doc_id],
            corpus_version=corpus_version,
            database_path=str(database_path) if database_path is not None else None,
        )
        return restored
