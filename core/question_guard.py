"""Question Quality Guard R8b với một lần regenerate và fallback YAML."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import cast

import yaml  # type: ignore[import-untyped]

from core.types import EscalationCard, EscalationType, EvidenceResult, EvidenceStatus, Extraction
from infra.audit import log_event
from infra.settings import QUESTION_WORDS_MAX, QUESTION_WORDS_MIN

logger = logging.getLogger(__name__)

BLOCKLIST_PATH = Path(__file__).parents[1] / "policies" / "blocklist.yaml"
FALLBACK_PATH = Path(__file__).parents[1] / "policies" / "fallback_questions.yaml"
WORD_PATTERN = re.compile(r"\b\w+\b")
DURATION_PATTERN = re.compile(
    r"(?<![\w.,])([0-9]+(?:[.,][0-9]+)?)\s*(giây|phút|giờ|ngày|tuần|tháng|năm)\b"
)
NO_SOURCE_BREADCRUMB = "Không tìm thấy quy định đang hiệu lực"


def _durations(text: str) -> set[tuple[str, str]]:
    # ponytail: chỉ đối chiếu số + đơn vị, không suy luận nghĩa hay quy đổi thời lượng.
    return set(DURATION_PATTERN.findall(text.casefold()))


def _load_blocklist() -> tuple[tuple[str, ...], int, int]:
    payload = yaml.safe_load(BLOCKLIST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("blocklist.yaml không hợp lệ.")
    phrases = payload.get("phrases")
    limits = payload.get("limits")
    options_min = limits.get("options_min") if isinstance(limits, Mapping) else None
    options_max = limits.get("options_max") if isinstance(limits, Mapping) else None
    if (
        not isinstance(phrases, list)
        or not all(isinstance(phrase, str) for phrase in phrases)
        or not isinstance(limits, Mapping)
        or not isinstance(options_min, int)
        or not isinstance(options_max, int)
    ):
        raise ValueError("blocklist.yaml thiếu phrases hoặc limits hợp lệ.")
    return tuple(phrases), options_min, options_max


def _has_breadcrumb(card: EscalationCard) -> bool:
    return bool(card.basis)


def question_failures(card: EscalationCard) -> list[str]:
    """Trả mọi luật Question Guard không đạt, theo thứ tự đặc tả."""
    phrases, options_min, options_max = _load_blocklist()
    question = card.question.strip()
    word_count = len(WORD_PATTERN.findall(question))
    failures: list[str] = []
    if not question.endswith("?"):
        failures.append("ends_with_question")
    if not QUESTION_WORDS_MIN <= word_count <= QUESTION_WORDS_MAX:
        failures.append("word_count")
    if question.count("?") != 1:
        failures.append("question_count")
    if not card.facts and not card.summary.strip():
        failures.append("fact")
    if not options_min <= len(card.options) <= options_max or not all(card.options):
        failures.append("options")
    if not _has_breadcrumb(card) and card.escalation_type is not EscalationType.OUT_OF_POLICY:
        failures.append("breadcrumb")
    if any(phrase.casefold() in question.casefold() for phrase in phrases):
        failures.append("blocklist")
    supported = {duration for _, quote in card.basis for duration in _durations(quote)}
    if any(_durations(option) - supported for option in card.options):
        failures.append("unsupported_option_duration")
    return failures


def _record_failure(
    *, case_id: str, actor: str, corpus_version: str, card: EscalationCard, failures: list[str]
) -> None:
    log_event(
        case_id=case_id,
        actor=actor,
        action="QUESTION_GUARD_FAILED",
        input_ref=case_id,
        reason=f"Câu hỏi chuyển tiếp không đạt: {', '.join(failures)}.",
        sources=[breadcrumb for breadcrumb, _ in card.basis],
        corpus_version=corpus_version,
    )


def _fallback_requests(
    extraction: Extraction, escalation_type: EscalationType
) -> tuple[list[str], str]:
    requests = [f"Yêu cầu {i}: {item.intent}" for i, item in enumerate(extraction.requests, 1)]
    pending = [
        i
        for i, item in enumerate(extraction.requests, 1)
        if item.requires_personal_record
        or item.asks_exception
        or item.asks_appeal
        or item.asks_authority_decision
    ]
    if escalation_type is not EscalationType.AUTHORITY_REQUIRED or not pending:
        pending = list(range(1, len(requests) + 1))
    scope = "yêu cầu " + ", ".join(map(str, pending)) if pending else "yêu cầu chưa được xác định"
    return requests, scope


def _fallback_facts(extraction: Extraction, evidence: EvidenceResult) -> list[str]:
    facts = [
        f"Thông tin từ email (chưa xác minh): {value}"
        for value in extraction.critical_facts.values()
    ]
    facts.extend(
        f"Cần bổ sung hoặc xác minh: {value}" for value in extraction.missing_critical_facts
    )
    uncertainty = {
        EvidenceStatus.CONFLICTING_SOURCES: "Các nguồn đang mâu thuẫn; chưa xác định nguồn áp dụng.",
        EvidenceStatus.NO_AUTHORITATIVE_SOURCE: "Chưa có căn cứ có thẩm quyền trả lời đầy đủ yêu cầu.",
        EvidenceStatus.FACT_MISSING: "Còn thiếu dữ kiện để áp dụng quy định.",
        EvidenceStatus.SCOPE_MISMATCH: "Chưa xác minh được phạm vi áp dụng của căn cứ.",
        EvidenceStatus.UNSUPPORTED_DOMAIN: "Yêu cầu có nội dung ngoài phạm vi được hỗ trợ.",
    }
    if evidence.status in uncertainty:
        facts.append(uncertainty[evidence.status])
    if "unanswered_request" in evidence.failed_checks:
        facts.append("Còn nội dung yêu cầu chưa có căn cứ trả lời.")
    if not evidence.chunks:
        facts.append("Không có trích dẫn được chọn; cần xác minh căn cứ trước khi quyết định.")
    if not facts:
        facts.append("Chưa có dữ kiện được xác minh; cần làm rõ yêu cầu trước khi quyết định.")
    return facts


def _structured_fallback(
    card: EscalationCard, extraction: Extraction, evidence: EvidenceResult
) -> EscalationCard:
    requests, scope = _fallback_requests(extraction, card.escalation_type)
    actions = {
        EscalationType.AUTHORITY_REQUIRED: [
            f"Cấp có thẩm quyền ghi quyết định và căn cứ cho {scope} sau khi xác minh dữ kiện.",
            f"Chưa quyết định {scope}; xác minh các mục chưa rõ nêu trong thẻ.",
        ],
        EscalationType.OUT_OF_POLICY: [
            f"Chuyển {scope} đến đơn vị có thẩm quyền để làm rõ căn cứ áp dụng.",
            f"Chưa có căn cứ trả lời {scope}; xác minh các điểm chưa rõ nêu trong thẻ.",
        ],
        EscalationType.FACT_UNRESOLVED: [
            f"Bổ sung hoặc xác minh dữ kiện cho {scope} theo các mục nêu trong thẻ.",
            f"Chưa có dữ kiện bổ sung cho {scope}; giữ chờ xác minh.",
        ],
    }
    if not requests:
        options = [
            "Yêu cầu làm rõ nội dung cần người xử lý quyết định.",
            "Chưa xác định được nội dung yêu cầu; giữ chờ xác minh.",
        ]
    else:
        options = actions[card.escalation_type]
    return EscalationCard(
        summary=f"Chờ người xử lý xác nhận cách xử lý {scope}; chưa có quyết định tự động.",
        facts=requests + _fallback_facts(extraction, evidence),
        basis=[(chunk.breadcrumb, chunk.text) for chunk in evidence.chunks if chunk.text.strip()],
        question=f"Anh/chị chọn cách xử lý nào cho {scope}, dựa trên dữ kiện và căn cứ nêu trong thẻ?",
        options=options,
        escalation_type=card.escalation_type,
        partial_draft=card.partial_draft,
    )


def _fallback(
    card: EscalationCard,
    extraction: Extraction | None = None,
    evidence: EvidenceResult | None = None,
) -> EscalationCard:
    if extraction is not None and evidence is not None:
        return _structured_fallback(card, extraction, evidence)
    payload = yaml.safe_load(FALLBACK_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or not isinstance(payload.get("templates"), Mapping):
        raise ValueError("fallback_questions.yaml không hợp lệ.")
    templates = cast(Mapping[str, object], payload["templates"])
    template = templates.get(card.escalation_type.value)
    if not isinstance(template, Mapping):
        raise ValueError("Thiếu fallback cho escalation type.")
    key_fact = card.facts[0] if card.facts else "chưa xác định"
    basis = card.basis[0][0] if card.basis else NO_SOURCE_BREADCRUMB
    values = {"key_fact": key_fact, "basis": basis, "request_summary": card.summary}
    facts = [_format(value, values) for value in _strings(template.get("facts"), "facts")]
    basis_items = [_format(value, values) for value in _strings(template.get("basis"), "basis")]
    return EscalationCard(
        summary=_format(_string(template.get("summary"), "summary"), values),
        facts=facts,
        basis=[(item, "") for item in basis_items],
        question=_format(_string(template.get("question"), "question"), values),
        options=[_format(value, values) for value in _strings(template.get("options"), "options")],
        escalation_type=card.escalation_type,
        partial_draft=card.partial_draft,
    )


def _format(template: str, values: dict[str, str]) -> str:
    try:
        return template.format(**values)
    except KeyError as error:
        raise ValueError("Template fallback có biến không hợp lệ.") from error


def _strings(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} fallback không hợp lệ.")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} fallback không hợp lệ.")
    return value


def guard_question(
    *,
    case_id: str,
    actor: str,
    corpus_version: str,
    card: EscalationCard,
    regenerate: Callable[[], EscalationCard] | None,
    extraction: Extraction | None = None,
    evidence: EvidenceResult | None = None,
) -> EscalationCard:
    """Contain duration sai ngay; lỗi chất lượng khác regenerate tối đa một lần."""
    failures = question_failures(card)
    if not failures:
        return card
    _record_failure(
        case_id=case_id,
        actor=actor,
        corpus_version=corpus_version,
        card=card,
        failures=failures,
    )
    if "unsupported_option_duration" in failures:
        fallback = _fallback(card, extraction, evidence)
        if extraction is not None and evidence is not None:
            return fallback
        return replace(card, question=fallback.question, options=fallback.options)
    if regenerate is None:
        # Email đa yêu cầu đã dùng lượt đọc, chọn nguồn, soạn phần đáp án và đặt câu hỏi.
        return _fallback(card, extraction, evidence)
    try:
        regenerated = regenerate()
    except Exception as error:
        logger.exception("Không thể regenerate câu hỏi: %s", error, extra={"case_id": case_id})
        return _fallback(card, extraction, evidence)
    retry_failures = question_failures(regenerated)
    if not retry_failures:
        return regenerated
    _record_failure(
        case_id=case_id,
        actor=actor,
        corpus_version=corpus_version,
        card=regenerated,
        failures=retry_failures,
    )
    fallback = _fallback(regenerated, extraction, evidence)
    if extraction is not None and evidence is not None:
        return fallback
    if "unsupported_option_duration" in retry_failures:
        return replace(regenerated, question=fallback.question, options=fallback.options)
    return fallback
