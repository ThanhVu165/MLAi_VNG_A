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
CLOCK_PATTERN = re.compile(
    r"(?<![\w:])(?P<hour>1[0-2]|[1-9])(?::(?P<minute>[0-5]\d))?\s*"
    r"(?P<period>[ap])\.?m\.?(?!\w)",
    re.IGNORECASE,
)
FORBIDDEN_AUTHORITY_PHRASES = (
    "chúng tôi đồng ý",
    "đã được duyệt",
    "được chấp thuận",
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


def _without_grounded_clocks(body: str, evidence_text: str) -> str:
    """Chỉ bỏ clock 12 giờ khi có giờ 24 tương đương nguyên vẹn trong evidence."""

    def replace_clock(match: re.Match[str]) -> str:
        hour = int(match["hour"])
        minute = match["minute"] or "00"
        if match["period"].lower() == "a":
            hour = 0 if hour == 12 else hour
        elif hour != 12:
            hour += 12
        hour_pattern = f"0?{hour}" if hour < 10 else str(hour)
        time_pattern = rf"{hour_pattern}\s*(?::|giờ|h)\s*{minute}(?![\d:])"
        if minute == "00":
            time_pattern += rf"|{hour_pattern}\s+giờ(?!\s*\d)"
        grounded = re.search(rf"(?<![\w:])(?:{time_pattern})(?!\w)", evidence_text)
        return " " if grounded else match.group()

    return CLOCK_PATTERN.sub(replace_clock, body)


def _unsupported_value_failure(
    draft: DraftReply,
    evidence: EvidenceResult,
    extra_text: str = "",
    *,
    course_code: str = "",
    input_text: str = "",
) -> bool:
    evidence_text = "\n".join([extra_text] + [chunk.text for chunk in evidence.chunks]).casefold()
    body = CITATION_MARKER_PATTERN.sub("", draft.body)
    values = {
        match.group().casefold().rstrip(".,/")
        for pattern in (ARTICLE_PATTERN, FORM_PATTERN)
        for match in pattern.finditer(body)
    }

    def normalize_number(value: str) -> str:
        return re.sub(r"[.,](?=\d{3}(?:\D|$))", "", value.rstrip(".,/"))

    source_numbers = {
        normalize_number(match.group()) for match in NUMBER_PATTERN.finditer(evidence_text)
    }
    numeric_body = _without_grounded_clocks(body, evidence_text)
    numeric_body = _without_input_course_code(numeric_body, course_code, input_text)
    draft_numbers = {
        normalize_number(match.group()) for match in NUMBER_PATTERN.finditer(numeric_body)
    }
    return not draft_numbers <= source_numbers or any(
        value not in evidence_text for value in values
    )


def _without_input_course_code(body: str, course_code: str, input_text: str) -> str:
    """Chỉ bỏ mã R2 nhận diện khi input gắn chính mã đó với môn/học phần."""
    if not re.fullmatch(r"[A-Z]{2,4}[0-9]{3}", course_code):
        return body
    token = rf"(?<!\w){re.escape(course_code)}(?!\w)"
    context = rf"\b(?:môn(?: học)?|học phần)\s+[^.!?\n;:]*?{token}"
    if not re.search(context, input_text, re.IGNORECASE):
        return body
    # Không miễn kiểm tra khi token được dùng như một giá trị có đơn vị nghiệp vụ.
    units = r"%|₫|đồng\b|vnd\b|ngày\b|giờ\b|tuần\b|tháng\b|năm\b|phần\s+trăm\b"
    return re.sub(rf"{token}(?!\s*(?:{units}))", " ", body, flags=re.IGNORECASE)


def _authority_failure(draft: DraftReply) -> bool:
    sentences = SENTENCE_PATTERN.split(draft.body.casefold())
    return any(
        any(phrase in sentence for phrase in FORBIDDEN_AUTHORITY_PHRASES)
        and not any(
            word in sentence for word in ("không ", "chưa ", "chỉ khi ", "sau khi ", "nếu ")
        )
        for sentence in sentences
    )


def _citation_ratio_failure(draft: DraftReply) -> bool:
    # LLM thường đặt trích dẫn ngay sau dấu chấm; nó vẫn dẫn cho câu đứng trước.
    body = re.sub(r"([.!?])\s*(\[[^\]]+\])", r" \2\1", draft.body)
    sentences = [sentence.strip() for sentence in SENTENCE_PATTERN.split(body) if sentence.strip()]
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
    record_event: bool = True,
    course_code: str = "",
    input_text: str = "",
) -> GroundednessResult:
    """Kiểm tra bốn điều kiện groundedness, giữ nguyên draft khi hạ cấp."""
    checks = (
        ("citation", _citation_failure(draft, evidence)),
        (
            "number",
            _unsupported_value_failure(
                draft, evidence, course_code=course_code, input_text=input_text
            ),
        ),
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
    if record_event:
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
