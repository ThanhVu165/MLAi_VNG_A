"""R3 lock: chặn trả lời tự động, không chặn thu thập evidence."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import EscalationType, Extraction, RequestItem


@dataclass(frozen=True)
class MultiIntentPlan:
    routine_requests: tuple[RequestItem, ...]
    locked_requests: tuple[RequestItem, ...]


def decision_lock(extraction: Extraction) -> EscalationType | None:
    """Khóa AUTO_REPLY khi yêu cầu cần xem hồ sơ hoặc quyền quyết định."""
    for request in extraction.requests:
        if any(
            (
                request.requires_personal_record,
                request.asks_exception,
                request.asks_appeal,
                request.asks_authority_decision,
            )
        ):
            return EscalationType.AUTHORITY_REQUIRED
    return None


def multi_intent_plan(extraction: Extraction) -> MultiIntentPlan | None:
    """Tách phần thông tin thường quy khỏi phần cần thẩm quyền của email đa ý định."""
    if len(extraction.requests) < 2:
        return None
    locked = tuple(
        request
        for request in extraction.requests
        if any(
            (
                request.requires_personal_record,
                request.asks_exception,
                request.asks_appeal,
                request.asks_authority_decision,
            )
        )
    )
    routine = tuple(request for request in extraction.requests if request not in locked)
    return MultiIntentPlan(routine, locked) if locked and routine else None
