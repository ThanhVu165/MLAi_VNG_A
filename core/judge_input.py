"""Facade đồng bộ Judge; không hàng gửi và không thay public interfaces cũ."""

from __future__ import annotations

import sqlite3

from core.pipeline import _new_ulid, process_case
from core.types import CaseInput, PipelineResult
from infra.judge_access import (
    JudgeDenied,
    JudgeGrant,
    mark_processing,
    payload_hash,
    request_scope,
    validate_text,
)


def process_judge_case(
    inp: CaseInput, *, grant: JudgeGrant, session: str, nonce: str
) -> PipelineResult:
    """Capability được server cấp; nonce chỉ chống replay, không cấp quyền."""
    validate_text(inp.sender, inp.subject, inp.body)
    if inp.received_at.utcoffset() is None or inp.channel != "paste" or inp.external_id is not None:
        raise ValueError("Judge chỉ nhận email dán mới có thời điểm hợp lệ.")
    case_id = "c_" + _new_ulid()
    fingerprint = payload_hash(inp.sender, inp.subject, inp.body, inp.received_at)
    try:
        with request_scope(grant, session, nonce, case_id, fingerprint):
            mark_processing()
            return process_case(inp, actor="SYSTEM", case_id=case_id)
    except (sqlite3.Error, OSError):
        raise JudgeDenied(
            "Kho quyền judge chưa sẵn sàng; chưa xác nhận xử lý thành công."
        ) from None
