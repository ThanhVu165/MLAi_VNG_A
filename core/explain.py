"""Giải thích ngắn cho người không chuyên từ dữ liệu case đã lưu."""

from __future__ import annotations

import json

from core.types import Decision, EscalationType, PolicyDecision
from infra.audit import log_event
from infra.db import fetch_all, fetch_one

BANNED_TERMS = ("rule_id", "similarity", "chunk")
MAX_EXPLANATION_WORDS = 120


def _decision(case_id: str) -> PolicyDecision:
    row = fetch_one(
        "SELECT * FROM decisions WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
    )
    if row is None:
        raise ValueError("Case chưa có quyết định để giải thích.")
    return PolicyDecision(
        Decision(row["decision"]),
        EscalationType(row["escalation_type"]) if row["escalation_type"] else None,
        row["rule_id"],
        row["reason"],
        json.loads(row["evidence_ids_json"] or "[]"),
        row["corpus_version"],
    )


def _titles(evidence_ids: list[str]) -> str:
    if not evidence_ids:
        return "các quy định đang hiệu lực"
    placeholders = ", ".join("?" for _ in evidence_ids)
    rows = fetch_all(
        f"""
        SELECT DISTINCT COALESCE(s.title, c.breadcrumb) AS title
        FROM chunks c LEFT JOIN sources s ON s.doc_id = c.doc_id
        WHERE c.chunk_id IN ({placeholders})
        """,
        evidence_ids,
    )
    titles = [row["title"] for row in rows if row["title"]]
    return ", ".join(titles) if titles else "các quy định đang hiệu lực"


def _reason(decision: PolicyDecision) -> str:
    reason = decision.reason.strip()
    if reason and not any(term in reason.casefold() for term in BANNED_TERMS):
        return reason
    if decision.decision is Decision.INVALID_INPUT:
        return "Nội dung cần được làm rõ thêm trước khi xử lý."
    if decision.escalation_type is EscalationType.AUTHORITY_REQUIRED:
        return "Yêu cầu này cần người có thẩm quyền xem xét."
    return "Cần chuyên viên kiểm tra thêm để bảo đảm trả lời đúng."


def _next_step(decision: PolicyDecision) -> str:
    if decision.decision is Decision.AUTO_REPLY:
        return "Bạn có thể đọc bản trả lời và gửi thêm thông tin nếu vẫn cần làm rõ."
    if decision.decision is Decision.INVALID_INPUT:
        return "Bạn có thể gửi lại câu hỏi với nội dung cụ thể hơn."
    return "Chuyên viên sẽ xem xét và phản hồi theo quy trình."


def _trim(text: str) -> str:
    words = text.split()
    return " ".join(words[:MAX_EXPLANATION_WORDS])


def explain_plainly(case_id: str) -> str:
    """Trả lời ngắn hệ thống đã làm gì, vì sao, dựa vào đâu và bước tiếp theo."""
    decision = _decision(case_id)
    explanation = _trim(
        "Hệ thống đã đọc nội dung yêu cầu và đối chiếu với quy định hiện có. "
        f"{_reason(decision)} "
        f"Thông tin này dựa trên {_titles(decision.evidence_ids)}. "
        f"{_next_step(decision)}"
    )
    log_event(
        case_id=case_id,
        actor="HUMAN:viewer",
        action="EXPLAIN_REQUESTED",
        input_ref=case_id,
        reason="Đã tạo phần giải thích dễ hiểu cho người dùng.",
        sources=decision.evidence_ids,
        corpus_version=decision.corpus_version,
    )
    return explanation
