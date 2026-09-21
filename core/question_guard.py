"""Question Quality Guard R8b với một lần regenerate và fallback YAML."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import yaml  # type: ignore[import-untyped]

from core.types import EscalationCard
from infra.audit import log_event
from infra.settings import QUESTION_WORDS_MAX, QUESTION_WORDS_MIN

logger = logging.getLogger(__name__)

BLOCKLIST_PATH = Path(__file__).parents[1] / "policies" / "blocklist.yaml"
FALLBACK_PATH = Path(__file__).parents[1] / "policies" / "fallback_questions.yaml"
WORD_PATTERN = re.compile(r"\b\w+\b")
NO_SOURCE_BREADCRUMB = "Không tìm thấy quy định đang hiệu lực"


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
    if not any(fact and fact.casefold() in question.casefold() for fact in card.facts):
        failures.append("fact")
    if not options_min <= len(card.options) <= options_max or not all(card.options):
        failures.append("options")
    if not _has_breadcrumb(card):
        failures.append("breadcrumb")
    if any(phrase.casefold() in question.casefold() for phrase in phrases):
        failures.append("blocklist")
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


def _fallback(card: EscalationCard) -> EscalationCard:
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
    regenerate: Callable[[], EscalationCard],
) -> EscalationCard:
    """Chặn card lỗi, regenerate đúng một lần rồi dùng fallback nếu vẫn lỗi."""
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
    try:
        regenerated = regenerate()
    except Exception as error:
        logger.exception("Không thể regenerate câu hỏi: %s", error, extra={"case_id": case_id})
        return _fallback(card)
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
    return _fallback(regenerated)
