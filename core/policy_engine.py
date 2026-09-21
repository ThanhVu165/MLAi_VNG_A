"""Policy Engine R6 với ngôn ngữ điều kiện giới hạn."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml  # type: ignore[import-untyped]

from core.types import Decision, EscalationType, EvidenceResult, PolicyDecision
from infra.audit import log_event

logger = logging.getLogger(__name__)

POLICY_PATH = Path(__file__).parents[1] / "policies" / "policy.yaml"
P04_REASON = "Hệ thống không hoàn tất được bước xử lý nên dừng lại thay vì phỏng đoán."
TOKEN_PATTERN = re.compile(r"\s*(==|!=|\[|\]|,|\(|\)|'(?:[^']*)'|[A-Za-z_]\w*)")


@dataclass(frozen=True)
class PolicyInput:
    case_id: str
    actor: str
    corpus_version: str
    decision_lock: EscalationType | None
    evidence: EvidenceResult
    llm_error: bool
    parse_error: bool
    timeout: bool
    guard_failed: bool


class _WhenParser:
    def __init__(self, expression: str, context: dict[str, str | bool | None]) -> None:
        self.tokens = _tokens(expression)
        self.context = context
        self.position = 0

    def parse(self) -> bool:
        value = self._or_expression()
        if self._peek() is not None:
            raise ValueError("Biểu thức policy có token không hợp lệ.")
        return value

    def _or_expression(self) -> bool:
        value = self._and_expression()
        while self._accept("or"):
            value = self._and_expression() or value
        return value

    def _and_expression(self) -> bool:
        value = self._not_expression()
        while self._accept("and"):
            value = self._not_expression() and value
        return value

    def _not_expression(self) -> bool:
        if self._accept("not"):
            return not self._not_expression()
        return self._comparison()

    def _comparison(self) -> bool:
        if self._accept("("):
            value = self._or_expression()
            self._expect(")")
            return value
        left = self._value()
        operator = self._peek()
        if operator not in {"==", "!=", "in"}:
            if not isinstance(left, bool):
                raise ValueError("Biến policy độc lập phải là boolean.")
            return left
        self.position += 1
        if operator == "in":
            return left in self._list()
        right = self._value()
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        raise ValueError("Toán tử policy không được phép.")

    def _list(self) -> list[str | bool | None]:
        self._expect("[")
        values: list[str | bool | None] = []
        if self._peek() != "]":
            values.append(self._value())
            while self._accept(","):
                values.append(self._value())
        self._expect("]")
        return values

    def _value(self) -> str | bool | None:
        token = self._next()
        if token.startswith("'") and token.endswith("'"):
            return token[1:-1]
        if token == "true":
            return True
        if token == "false":
            return False
        if token in self.context:
            return self.context[token]
        raise ValueError(f"Tên biến policy không được phép: {token}")

    def _peek(self) -> str | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def _next(self) -> str:
        token = self._peek()
        if token is None:
            raise ValueError("Biểu thức policy kết thúc không đầy đủ.")
        self.position += 1
        return token

    def _accept(self, token: str) -> bool:
        if self._peek() == token:
            self.position += 1
            return True
        return False

    def _expect(self, token: str) -> None:
        if not self._accept(token):
            raise ValueError(f"Thiếu token policy: {token}")


def _tokens(expression: str) -> list[str]:
    tokens: list[str] = []
    position = 0
    while position < len(expression):
        match = TOKEN_PATTERN.match(expression, position)
        if match is None:
            raise ValueError("Biểu thức policy chứa ký tự không được phép.")
        tokens.append(match.group(1))
        position = match.end()
    return tokens


def _load_rules() -> list[dict[str, object]]:
    payload = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("priority_order"), list):
        raise ValueError("policy.yaml không có priority_order hợp lệ.")
    rules = payload["priority_order"]
    if not all(isinstance(rule, dict) for rule in rules):
        raise ValueError("Mỗi policy rule phải là mapping.")
    return cast(list[dict[str, object]], rules)


def _context(inp: PolicyInput) -> dict[str, str | bool | None]:
    return {
        "decision_lock": inp.decision_lock.value if inp.decision_lock else None,
        "evidence_status": inp.evidence.status.value,
        "llm_error": inp.llm_error,
        "parse_error": inp.parse_error,
        "timeout": inp.timeout,
        "guard_failed": inp.guard_failed,
    }


def _record(inp: PolicyInput, decision: PolicyDecision) -> PolicyDecision:
    log_event(
        case_id=inp.case_id,
        actor=inp.actor,
        action="POLICY_DECIDED",
        rule_id=decision.rule_id,
        input_ref=inp.case_id,
        reason=decision.reason,
        sources=decision.evidence_ids,
        corpus_version=inp.corpus_version,
    )
    return decision


def _fallback(inp: PolicyInput) -> PolicyDecision:
    return PolicyDecision(
        decision=Decision.ESCALATE,
        escalation_type=EscalationType.FACT_UNRESOLVED,
        rule_id="P04",
        reason=P04_REASON,
        evidence_ids=[chunk.chunk_id for chunk in inp.evidence.chunks],
        corpus_version=inp.corpus_version,
    )


def decide_policy(inp: PolicyInput) -> PolicyDecision:
    """Áp dụng luật YAML đầu tiên khớp; lỗi cấu hình luôn hạ về P04."""
    try:
        context = _context(inp)
        for rule in _load_rules():
            when = rule.get("when")
            matches = rule.get("else") is True or (
                isinstance(when, str) and _WhenParser(when, context).parse()
            )
            if matches:
                decision = PolicyDecision(
                    decision=Decision(str(rule["decision"])),
                    escalation_type=(
                        EscalationType(str(rule["type"])) if rule.get("type") is not None else None
                    ),
                    rule_id=str(rule["id"]),
                    reason=str(rule["reason_vi"]),
                    evidence_ids=[chunk.chunk_id for chunk in inp.evidence.chunks],
                    corpus_version=inp.corpus_version,
                )
                return _record(inp, decision)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
        logger.exception("Không thể đánh giá policy: %s", error, extra={"case_id": inp.case_id})
    return _record(inp, _fallback(inp))
