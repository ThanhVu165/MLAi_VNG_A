"""Hàng công việc SQLite và tiến trình gửi chạy độc lập với trang Streamlit."""

from __future__ import annotations

import logging
from contextlib import closing
from datetime import datetime, timedelta, timezone
from sqlite3 import Connection, Row
from threading import Event, Lock, Thread
from typing import Literal, cast
from uuid import uuid4

from core.dispatch import dispatch_due
from core.pipeline import _is_missing_required, _new_ulid, process_case
from core.resume import resume_case
from core.sanitize import guard_input, mask_pii, sanitize_body
from core.types import CaseInput, CaseStatus, Decision
from corpus.api import get_corpus_version
from infra.audit import log_event
from infra.db import execute, fetch_all, fetch_one, get_connection, now_iso, to_utc_iso

logger = logging.getLogger(__name__)
POLL_SECONDS = 1
JOB_LEASE_SECONDS = 120
_start_lock = Lock()
_threads: list[Thread] = []
_stop = Event()


def submit_case(inp: CaseInput, *, actor: str = "SYSTEM", parent_case_id: str | None = None) -> str:
    """Lưu nguyên email và công việc trong cùng giao dịch; cùng mã hộp thư chỉ nhận một lần."""
    if (
        _is_missing_required(inp)
        or guard_input(sanitize_body(inp.body)).decision is Decision.INVALID_INPUT
    ):
        raise ValueError("Hãy điền người gửi, tiêu đề, nội dung và thời điểm nhận có múi giờ.")
    case_id = f"c_{_new_ulid()}"
    version = get_corpus_version()
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if parent_case_id is not None:
            parent = connection.execute(
                "SELECT status FROM cases WHERE case_id = ?", (parent_case_id,)
            ).fetchone()
            if parent is None or parent["status"] not in (
                CaseStatus.ERROR,
                CaseStatus.NEEDS_RECHECK,
                CaseStatus.CANCELLED,
            ):
                raise ValueError("Chỉ chạy lại email lỗi, đã hủy hoặc cần kiểm tra lại.")
            child = connection.execute(
                "SELECT case_id FROM cases WHERE parent_case_id = ? ORDER BY rowid DESC LIMIT 1",
                (parent_case_id,),
            ).fetchone()
            if child is not None:
                # Bấm lại đi đến lần chạy đã tạo; muốn thử tiếp thì chạy lại chính lần đó.
                return str(child["case_id"])
        if inp.external_id:
            existing = connection.execute(
                "SELECT case_id FROM cases WHERE channel = ? AND external_id = ?",
                (inp.channel, inp.external_id),
            ).fetchone()
            if existing:
                return str(existing["case_id"])
        connection.execute(
            """INSERT INTO cases(case_id, trace_id, channel, sender, subject, body_raw,
                body_masked, received_at, created_at, status, corpus_version, external_id, parent_case_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case_id,
                str(uuid4()),
                inp.channel,
                inp.sender,
                inp.subject,
                inp.body,
                mask_pii(inp.body),
                to_utc_iso(inp.received_at),
                now_iso(),
                CaseStatus.RECEIVED,
                version,
                inp.external_id,
                parent_case_id,
            ),
        )
        connection.execute("INSERT INTO case_jobs(case_id, actor) VALUES (?, ?)", (case_id, actor))
        log_event(
            case_id=case_id,
            actor=actor,
            action="CASE_RECEIVED",
            input_ref=case_id,
            reason="Đã nhận email và đưa vào hàng xử lý.",
            corpus_version=version,
            connection=connection,
        )
        if parent_case_id:
            log_event(
                case_id=parent_case_id,
                actor=actor,
                action="RERUN_CASE",
                output_ref=case_id,
                reason="Đã yêu cầu chạy lại email; giữ nguyên lần xử lý trước để đối chiếu.",
                corpus_version=version,
                connection=connection,
            )
    return case_id


def _recover_interrupted() -> None:
    expired = fetch_all(
        "SELECT case_id FROM case_jobs WHERE state = 'running' AND lease_until < ?", (now_iso(),)
    )
    for job in expired:
        case_id = job["case_id"]
        if execute(
            "UPDATE case_jobs SET state = 'failed' WHERE case_id = ? AND state = 'running' AND lease_until < ?",
            (case_id, now_iso()),
        ):
            _mark_interrupted(case_id)
    cutoff = to_utc_iso(datetime.now(timezone.utc) - timedelta(seconds=JOB_LEASE_SECONDS))
    for orphan in fetch_all(
        """SELECT case_id FROM cases WHERE status IN (?, ?) AND created_at < ?
           AND NOT EXISTS(SELECT 1 FROM case_jobs j WHERE j.case_id = cases.case_id)""",
        (CaseStatus.RECEIVED, CaseStatus.PROCESSING, cutoff),
    ):
        _mark_interrupted(orphan["case_id"])


def _mark_interrupted(case_id: str) -> None:
    reason = "Lần xử lý bị gián đoạn khi hệ thống dừng. Hãy chạy lại; chưa gửi email."
    with closing(get_connection()) as connection, connection:
        case = connection.execute("SELECT status FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        if case is not None and case["status"] == CaseStatus.HUMAN_DECIDED:
            log_event(
                case_id=case_id, actor="SYSTEM", action="CASE_ERROR",
                reason="Bước soạn thư bị gián đoạn. Quyết định của chuyên viên vẫn được giữ; hãy yêu cầu soạn lại.",
                connection=connection,
            )
            return
        changed = connection.execute(
            "UPDATE cases SET status = ? WHERE case_id = ? AND status IN (?, ?)",
            (CaseStatus.ERROR, case_id, CaseStatus.RECEIVED, CaseStatus.PROCESSING),
        ).rowcount
        if not changed:
            return
        connection.execute(
            """INSERT INTO decisions(decision_id, case_id, decision, rule_id, reason, evidence_ids_json, corpus_version, created_at)
               SELECT ?, case_id, ?, 'TECHNICAL_ERROR', ?, '[]', corpus_version, ? FROM cases WHERE case_id = ?""",
            (str(uuid4()), Decision.ERROR, reason, now_iso(), case_id),
        )
        log_event(
            case_id=case_id, actor="SYSTEM", action="CASE_ERROR", reason=reason,
            connection=connection,
        )


def retry_case(case_id: str, *, actor: str = "HUMAN:local") -> str:
    """Tạo lần chạy mới liên kết email lỗi/đã hủy, không chỉnh sửa lần chạy cũ."""
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if case is None:
        raise ValueError("Không tìm thấy email cần chạy lại.")
    inp = CaseInput(
        case["sender"],
        case["subject"],
        case["body_raw"],
        datetime.fromisoformat(case["received_at"]),
        cast(Literal["paste", "inbox", "verify"], case["channel"]),
        None,
    )
    return submit_case(inp, actor=actor, parent_case_id=case_id)


def queue_resume(case_id: str, *, connection: Connection | None = None) -> None:
    """Xếp việc soạn thư theo quyết định đã lưu, có thể cùng giao dịch của giao diện."""
    if connection is None:
        with closing(get_connection()) as owned, owned:
            owned.execute("BEGIN IMMEDIATE")
            queue_resume(case_id, connection=owned)
        return
    case = connection.execute("SELECT status FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    human = connection.execute(
        "SELECT * FROM human_decisions WHERE case_id = ? AND decided_at IS NOT NULL ORDER BY rowid DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if case is None or case["status"] != CaseStatus.HUMAN_DECIDED or human is None:
        raise ValueError("Cần lưu quyết định của chuyên viên trước khi yêu cầu soạn thư.")
    if not human["actor"].startswith("HUMAN:") or not all(
        str(human[field]).strip() for field in ("choice", "reason")
    ):
        raise ValueError("Quyết định cần có người thực hiện, lựa chọn và lý do đầy đủ.")
    changed = connection.execute(
        """INSERT INTO case_jobs(case_id, actor, state) VALUES (?, ?, 'queued')
           ON CONFLICT(case_id) DO UPDATE SET actor = excluded.actor, state = 'queued', lease_until = NULL
           WHERE case_jobs.state NOT IN ('queued', 'running')""",
        (case_id, human["actor"]),
    ).rowcount
    if changed:
        log_event(
            case_id=case_id, actor=human["actor"], action="CASE_QUEUED",
            reason="Đã lưu yêu cầu soạn thư theo quyết định của chuyên viên; chưa gửi email.",
            connection=connection,
        )


def _resume_job(case: Row, lease: str) -> None:
    case_id = case["case_id"]
    try:
        human = fetch_one(
            "SELECT * FROM human_decisions WHERE case_id = ? AND decided_at IS NOT NULL ORDER BY rowid DESC LIMIT 1",
            (case_id,),
        )
        if human is None:
            raise ValueError("Không tìm thấy quyết định đã lưu của chuyên viên.")
        resume_case(case_id, human["choice"], human["reason"], human["actor"])
    except Exception as error:
        logger.exception("Chưa soạn được thư theo quyết định của chuyên viên.")
        state = "failed"
        with closing(get_connection()) as connection, connection:
            connection.execute(
                "UPDATE case_jobs SET state = ?, lease_until = NULL WHERE case_id = ? AND state = 'running' AND lease_until = ?",
                (state, case_id, lease),
            )
            log_event(
                case_id=case_id, actor="SYSTEM", action="CASE_ERROR",
                reason=(
                    mask_pii(str(error))
                    if str(error).startswith(("Dịch vụ AI", "Chưa cấu hình"))
                    else "Chưa soạn được thư. Quyết định của chuyên viên vẫn được giữ; hãy yêu cầu soạn lại."
                ),
                connection=connection,
            )
    else:
        execute(
            "UPDATE case_jobs SET state = 'done', lease_until = NULL WHERE case_id = ? AND state = 'running' AND lease_until = ?",
            (case_id, lease),
        )


def _dispatch_pending() -> None:
    for row in fetch_all("SELECT case_id FROM cases WHERE status = ?", (CaseStatus.PENDING_SEND,)):
        dispatch_due(row["case_id"])


def worker_tick() -> None:
    """Khôi phục lease hết hạn, gửi thư đến hạn, nhận tối đa một công việc bằng khóa DB."""
    _recover_interrupted()
    _dispatch_pending()
    job = fetch_one("SELECT * FROM case_jobs WHERE state = 'queued' ORDER BY rowid LIMIT 1")
    if job is None:
        return
    lease = to_utc_iso(datetime.now(timezone.utc) + timedelta(seconds=JOB_LEASE_SECONDS))
    if not execute(
        "UPDATE case_jobs SET state = 'running', lease_until = ? WHERE case_id = ? AND state = 'queued'",
        (lease, job["case_id"]),
    ):
        return
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (job["case_id"],))
    if case is None:
        raise RuntimeError("Công việc không có email gốc.")
    if case["status"] == CaseStatus.HUMAN_DECIDED:
        _resume_job(case, lease)
        return
    inp = CaseInput(
        case["sender"],
        case["subject"],
        case["body_raw"],
        datetime.fromisoformat(case["received_at"]),
        cast(Literal["paste", "inbox", "verify"], case["channel"]),
        case["external_id"],
    )
    result = process_case(inp, actor=job["actor"], case_id=job["case_id"])
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute(
            "SELECT status FROM cases WHERE case_id = ?", (case["case_id"],)
        ).fetchone()
        # Người duyệt có thể lưu quyết định ngay trước khi lượt xử lý ban đầu nhả job.
        state = "queued" if current and current["status"] == CaseStatus.HUMAN_DECIDED else (
            "failed" if result.status is CaseStatus.ERROR else "done"
        )
        connection.execute(
            "UPDATE case_jobs SET state = ?, lease_until = NULL WHERE case_id = ? AND state = 'running' AND lease_until = ?",
            (state, case["case_id"], lease),
        )


def _loop(dispatch_only: bool = False) -> None:
    while not _stop.is_set():
        try:
            _dispatch_pending() if dispatch_only else worker_tick()
        except Exception:
            logger.exception(
                "Tiến trình nền gặp lỗi; công việc giữ trong DB để kiểm tra/khôi phục."
            )
        _stop.wait(POLL_SECONDS)


def start_worker() -> None:
    """Khởi động một lần mỗi tiến trình; đổi trang/tải lại không tạo thêm worker."""
    with _start_lock:
        if _threads and all(thread.is_alive() for thread in _threads):
            return
        for name, dispatch_only in (("email-processing", False), ("email-dispatch", True)):
            thread = Thread(target=_loop, args=(dispatch_only,), name=name, daemon=True)
            thread.start()
            _threads.append(thread)
