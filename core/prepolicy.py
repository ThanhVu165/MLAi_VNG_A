"""R3 lock: chặn trả lời tự động, không chặn thu thập evidence."""

from __future__ import annotations

from core.types import EscalationType, Extraction


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
