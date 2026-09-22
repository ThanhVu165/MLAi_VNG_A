"""Groundedness Guard R8a: hạ cấp thay vì tự sửa bản nháp."""

from __future__ import annotations

import re
from dataclasses import dataclass

from corpus.api import is_active
from core.types import Decision, DraftReply, EscalationType, EvidenceResult, PolicyDecision
from infra.audit import log_event
from infra.settings import CITATION_RATIO_MIN

NUMBER_PATTERN = re.compile(r"\d[\d.,/]*")
ARTICLE_PATTERN = re.compile(r"Điều \d+", re.IGNORECASE)
FORM_PATTERN = re.compile(r"Mẫu [A-Z0-9-]+", re.IGNORECASE)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
CITATION_MARKER_PATTERN = re.compile(r"\[[^\]]+\]")
FORBIDDEN_AUTHORITY_PHRASES = (
    "chúng tôi đồng ý",
    "đã được duyệt",
    "được chấp thuận",
    "ngoại lệ",
    "bạn sẽ được",
    "we approve",
)


@dataclass(frozen=True)
class GroundednessResult:
    draft: DraftReply
    decision: PolicyDecision | None
    failed_checks: list[str]


def _citation_failure(draft: DraftReply, evidence: EvidenceResult) -> bool:
    evidence_ids = {chunk.chunk_id for chunk in evidence.chunks}
    return not draft.citations or any(
        citation not in evidence_ids or not is_active(citation) for citation in draft.citations
    )


def _unsupported_value_failure(draft: DraftReply, evidence: EvidenceResult) -> bool:
    evidence_text = "\n".join(chunk.text for chunk in evidence.chunks).casefold()
    body = CITATION_MARKER_PATTERN.sub("", draft.body)
    values = {
        match.group().casefold()
        for pattern in (NUMBER_PATTERN, ARTICLE_PATTERN, FORM_PATTERN)
        for match in pattern.finditer(body)
    }
    return any(value not in evidence_text for value in values)


def _authority_failure(draft: DraftReply) -> bool:
    body = draft.body.casefold()
    return any(phrase in body for phrase in FORBIDDEN_AUTHORITY_PHRASES)


def _citation_ratio_failure(draft: DraftReply) -> bool:
    sentences = [
        sentence.strip() for sentence in SENTENCE_PATTERN.split(draft.body) if sentence.strip()
    ]
    cited = sum(
        any(f"[{citation}]" in sentence for citation in draft.citations) for sentence in sentences
    )
    return not sentences or cited / len(sentences) < CITATION_RATIO_MIN


def _draft_with_grounding(draft: DraftReply, grounded: bool, failures: list[str]) -> DraftReply:
    return DraftReply(
        subject=draft.subject,
        body=draft.body,
        citations=draft.citations,
        grounded=grounded,
        guard_failures=failures,
    )


def guard_groundedness(
    *,
    case_id: str,
    actor: str,
    corpus_version: str,
    draft: DraftReply,
    evidence: EvidenceResult,
) -> GroundednessResult:
    """Kiểm tra bốn điều kiện groundedness, giữ nguyên draft khi hạ cấp."""
    checks = (
        ("citation", _citation_failure(draft, evidence)),
        ("number", _unsupported_value_failure(draft, evidence)),
        ("authority", _authority_failure(draft)),
        ("citation_ratio", _citation_ratio_failure(draft)),
    )
    failures = [name for name, failed in checks if failed]
    if not failures:
        return GroundednessResult(_draft_with_grounding(draft, True, []), None, [])
    reason = f"groundedness_failed:{failures[0]}"
    decision = PolicyDecision(
        decision=Decision.ESCALATE,
        escalation_type=EscalationType.FACT_UNRESOLVED,
        rule_id="P04",
        reason=reason,
        evidence_ids=[chunk.chunk_id for chunk in evidence.chunks],
        corpus_version=corpus_version,
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="GROUNDEDNESS_FAILED",
        rule_id=decision.rule_id,
        input_ref=case_id,
        reason=reason,
        sources=decision.evidence_ids,
        corpus_version=corpus_version,
    )
    return GroundednessResult(_draft_with_grounding(draft, False, failures), decision, failures)


def guard_resume_groundedness(draft: DraftReply) -> DraftReply:
    """Chạy hai kiểm tra R11: không vượt thẩm quyền và đủ citation theo câu."""
    failures = [
        name
        for name, failed in (
            ("authority", _authority_failure(draft)),
            ("citation_ratio", _citation_ratio_failure(draft)),
        )
        if failed
    ]
    return _draft_with_grounding(draft, not failures, failures)
