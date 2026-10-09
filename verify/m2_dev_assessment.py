"""Capture/assessment DEV thuần offline; không gọi hoặc import pipeline/harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field as dataclass_field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from core.types import CaseInput, PipelineResult
from verify.m2_dev_rubric import criterion_dimensions

FIXTURE = Path(__file__).with_name("cases_m2_combined_dev.json")
FIXTURE_SHA256 = "d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04"
Status = Literal["PASS", "FAIL", "REVIEW_REQUIRED", "NOT_APPLICABLE"]
DIMENSIONS = (
    "decision_match",
    "escalation_type_match",
    "rule_id_match",
    "case_status_consistency",
    "technical_error",
    "grounding_and_citation",
    "question_quality",
    "options_quality",
    "temporal_safety",
    "selective_conflict_handling",
)
CONFIG_LABELS = {
    "LLM_PROVIDER",
    "OPENAI_MODEL",
    "OPENAI_REASONING_EFFORT",
    "LLM_MODE",
    "LLM_CACHE",
    "LLM_RETRIES",
    "LLM_MAX_ATTEMPTS",
    "CASE_TIMEOUT_SECONDS",
    "LLM_TIMEOUT_S",
}
VIETNAM_TIME = timezone(timedelta(hours=7))
REVIEW_EVIDENCE_ROOTS = {
    "decision_match": ("/result/decision/decision",),
    "escalation_type_match": ("/result/decision/escalation_type",),
    "rule_id_match": ("/result/decision/rule_id",),
    "grounding_and_citation": (
        "/result/draft",
        "/result/card",
        "/result/evidence",
        "/diagnostics/source_status",
    ),
    "question_quality": ("/result/card/question",),
    "options_quality": ("/result/card/options",),
    "temporal_safety": (
        "/result/draft",
        "/result/card",
        "/result/extraction",
        "/identity/submitted_input",
    ),
    "selective_conflict_handling": ("/result/evidence", "/result/card", "/result/draft"),
}
TOKEN = re.compile(r"\bsk-[\w-]+|\bAIza[\w-]+|\bBearer\s+\S+", re.IGNORECASE)
SECRET_LABEL = re.compile(
    r"(?:OPENAI_API_KEY|GOOGLE_API_KEY|GEMINI_API_KEY|api[_ -]?key|authorization)"
    r"[\"']?\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
RISK_PATTERN = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%|phần trăm|ngày|tuần|giờ)|"
    r"\d{1,2}/\d{1,2}(?:/\d{4})?|mẫu\s+[\w-]+|chuyển khoản|"
    r"đã được duyệt|được chấp thuận|hồ sơ.*hợp lệ|hôm nay|thứ hai tuần sau",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CaptureDiagnostics:
    # None là unavailable, không suy attempts/guards từ số stage hoặc final card.
    provider_attempts: list[dict[str, object]] | None = None
    logical_calls: list[dict[str, object]] | None = None
    cost: float | None = None
    source_status: dict[str, str] | None = None
    guard_failures: list[str] | None = None
    error_class: str | None = None
    stop_reason: str | None = None
    cost_metadata: dict[str, str] | None = None
    r2_validation: list[dict[str, object]] | None = None


@dataclass(frozen=True)
class ExecutionContext:
    case_id: str
    observation_id: str
    result_case_id: str
    result_trace_id: str
    submitted_input: dict[str, object]
    submitted_input_sha256: str
    fixture_input_sha256: str


@dataclass(frozen=True)
class Capture:
    fixture_sha256: str
    case_id: str
    observation_id: str
    result: dict[str, object]
    config: dict[str, str]
    diagnostics: dict[str, object]
    identity: dict[str, object] | None = None


@dataclass(frozen=True)
class DimensionResult:
    status: Status
    evidence: list[str]


@dataclass(frozen=True)
class EvidenceReference:
    path: str  # JSON pointer vào capture, ví dụ /result/card/options/0.
    quote: str


@dataclass(frozen=True)
class ReviewDecision:
    dimension: str
    verdict: Literal["PASS", "FAIL"]
    rationale: str
    evidence: list[EvidenceReference]


@dataclass(frozen=True)
class CriterionReview:
    criterion_id: str
    judgments: list[ReviewDecision]


@dataclass(frozen=True)
class HumanReview:
    capture_sha256: str
    reviewer: str
    reviewed_at: str
    criteria: list[CriterionReview]
    dimension_reviews: list[ReviewDecision] = dataclass_field(default_factory=list)
    schema_version: int = 2


@dataclass(frozen=True)
class CriterionResult:
    status: Status
    required_dimensions: tuple[str, ...]
    evidence: list[str]
    # Không đồng nhất validated pointers với proof về semantic truth.
    judgment_source: str = "unreviewed"


@dataclass(frozen=True)
class Assessment:
    fixture_sha256: str
    capture_sha256: str
    case_id: str
    observation_id: str
    verdict: str
    expected: dict[str, object]
    dimensions: dict[str, DimensionResult]
    rubric: dict[str, str]
    risk_findings: list[str]
    review: HumanReview | None
    criteria: dict[str, CriterionResult]


def _safe(value: object) -> object:
    if isinstance(value, str):
        return SECRET_LABEL.sub("[REDACTED]", TOKEN.sub("[REDACTED]", value))
    if isinstance(value, dict):
        return {
            k: (
                "[REDACTED]"
                if re.search(r"api[_ -]?key|authorization|credential|secret|bearer", str(k), re.I)
                else _safe(v)
            )
            for k, v in value.items()
            if k != "raw_json"
        }
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def capture_hash(capture: Capture) -> str:
    """Bind review với toàn bộ capture; không bind chỉ case ID."""
    return hashlib.sha256(_json(asdict(capture)).encode("utf-8")).hexdigest()


def load_prereg(case_id: str, fixture: Path = FIXTURE) -> dict[str, object]:
    """Fail closed trước khi đọc gold nếu final-byte hash khác bản freeze."""
    raw = fixture.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError("BLOCKED_FIXTURE_HASH_MISMATCH")
    for item in json.loads(raw):
        if item["id"] == case_id:
            return item
    raise ValueError("Case không thuộc preregistration đã freeze.")


def canonical_input(payload: CaseInput | Mapping[str, object]) -> str:
    """NFC text, UTC microseconds, sorted compact UTF-8 JSON; giữ nguyên whitespace."""
    if isinstance(payload, CaseInput):
        payload = asdict(payload)
    if not isinstance(payload, Mapping):
        raise ValueError("INPUT_IDENTITY_REQUIRED: thiếu submitted input payload.")
    required = {"sender", "subject", "body", "received_at", "channel"}
    if not required <= payload.keys() or set(payload) - required - {"external_id"}:
        raise ValueError("INPUT_IDENTITY_INVALID: input fields không hợp lệ.")
    text = {}
    for key in ("sender", "subject", "body", "channel"):
        if not isinstance(payload[key], str):
            raise ValueError("INPUT_IDENTITY_INVALID: text phải là string.")
        text[key] = unicodedata.normalize("NFC", payload[key])
    stamp = payload["received_at"]
    try:
        stamp = datetime.fromisoformat(stamp) if isinstance(stamp, str) else stamp
        if not isinstance(stamp, datetime) or stamp.utcoffset() is None:
            raise ValueError("Timestamp phải timezone-aware.")
    except ValueError as error:
        raise ValueError("INPUT_IDENTITY_INVALID: received_at.") from error
    text["received_at"] = stamp.astimezone(timezone.utc).isoformat(timespec="microseconds")
    external = payload.get("external_id")
    if external is not None and not isinstance(external, str):
        raise ValueError("INPUT_IDENTITY_INVALID: external_id.")
    text["external_id"] = unicodedata.normalize("NFC", external) if external is not None else None
    return json.dumps(text, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def input_hash(payload: CaseInput | Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_input(payload).encode("utf-8")).hexdigest()


def execution_context(
    submitted_input: CaseInput | Mapping[str, object],
    result: PipelineResult,
    *,
    case_id: str,
    observation_id: str,
    fixture: Path = FIXTURE,
) -> ExecutionContext:
    """Caller cung cấp payload đã submit tại invocation boundary; không tự gọi pipeline."""
    prereg = load_prereg(case_id, fixture)
    actual = asdict(submitted_input) if isinstance(submitted_input, CaseInput) else submitted_input
    actual_hash = input_hash(actual)
    expected_hash = input_hash(prereg["input"])
    context = ExecutionContext(
        case_id,
        observation_id,
        result.case_id,
        result.trace_id,
        _safe(dict(actual)),
        actual_hash,
        expected_hash,
    )
    _validate_identity(asdict(context), case_id, observation_id, asdict(result), prereg)
    return context


def _validate_identity(
    identity: dict[str, object] | None,
    case_id: str,
    observation_id: str,
    result: dict[str, object],
    prereg: dict[str, object],
) -> None:
    if not isinstance(identity, dict):
        raise ValueError("INPUT_IDENTITY_REQUIRED: capture thiếu execution context.")
    try:
        context = ExecutionContext(**identity)
    except TypeError as error:
        raise ValueError("INPUT_IDENTITY_INVALID: malformed execution context.") from error
    ids = (case_id, observation_id, context.result_case_id, context.result_trace_id)
    if any(not isinstance(value, str) or not value.strip() for value in ids):
        raise ValueError("INPUT_IDENTITY_INVALID: nonempty string IDs required.")
    if (
        not observation_id.strip()
        or context.case_id != case_id
        or context.observation_id != observation_id
    ):
        raise ValueError("INPUT_IDENTITY_MISMATCH: case/observation identity.")
    if (
        not context.result_case_id
        or not context.result_trace_id
        or context.result_case_id != result.get("case_id")
        or context.result_trace_id != result.get("trace_id")
    ):
        raise ValueError("INPUT_IDENTITY_MISMATCH: result identity.")
    actual = input_hash(context.submitted_input)
    expected = input_hash(prereg["input"])
    if (
        actual != context.submitted_input_sha256
        or expected != context.fixture_input_sha256
        or actual != expected
    ):
        raise ValueError("INPUT_IDENTITY_MISMATCH: submitted/frozen input hash.")


def capture_result(
    result: PipelineResult,
    *,
    case_id: str,
    observation_id: str,
    execution: ExecutionContext | None = None,
    config: dict[str, str] | None = None,
    diagnostics: CaptureDiagnostics | None = None,
    fixture: Path = FIXTURE,
) -> Capture:
    """Nhận result từ orchestrator tương lai; chỉ chuyển dữ liệu, không chạy case."""
    prereg = load_prereg(case_id, fixture)
    identity = asdict(execution) if isinstance(execution, ExecutionContext) else None
    _validate_identity(identity, case_id, observation_id, asdict(result), prereg)
    labels = config or {}
    if set(labels) - CONFIG_LABELS or any(not isinstance(v, str) for v in labels.values()):
        raise ValueError("Config chỉ nhận nhãn allowlist không có credentials.")
    if TOKEN.search(_json(labels)) or SECRET_LABEL.search(_json(labels)):
        raise ValueError("Config có token không được ghi.")
    data = _safe(asdict(result))
    assert isinstance(data, dict)
    diagnostic_data = _safe(asdict(diagnostics or CaptureDiagnostics()))
    assert isinstance(diagnostic_data, dict)
    _validate_diagnostics(diagnostic_data)
    return Capture(
        FIXTURE_SHA256, case_id, observation_id, data, dict(labels), diagnostic_data, identity
    )


R2_VALIDATION_VALUES = {
    "event": {"r2_validation"},
    "phase": {"R2_extract"},
    "provider_result": {"SUCCESS", "FAILURE"},
    "domain_validation": {"PASS", "FAIL", "NOT_RUN"},
    "validation_stage": {
        "provider_result",
        "response",
        "requests",
        "language",
        "critical_facts",
        "missing_critical_facts",
        "injection_suspected",
        "serialization",
        "complete",
    },
    "reason_code": {
        None,
        "FACT_NAME_EMPTY",
        "FACT_VALUE_EMPTY",
        "FACT_DUPLICATE_CONFLICT",
        "R2_PAYLOAD_INVALID",
    },
    "retry_reason": {
        "NONE",
        "PROVIDER_FAILURE",
        "INTERNAL_VALIDATION_RETRY",
        "VALIDATION_RETRY_EXHAUSTED",
    },
}
R2_VALIDATION_FIELDS = set(R2_VALIDATION_VALUES) | {
    "correlation_id",
    "logical_call_index",
}


def _valid_r2_validation(event: object) -> bool:
    """Closed metadata vocabulary: arbitrary strings cannot carry raw content."""
    if not isinstance(event, dict) or set(event) != R2_VALIDATION_FIELDS:
        return False
    correlation = event["correlation_id"]
    return (
        isinstance(correlation, str)
        and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", correlation) is not None
        and type(event["logical_call_index"]) is int
        and event["logical_call_index"] > 0
        and all(
            (value is None or type(value) is str) and value in allowed
            for key, allowed in R2_VALIDATION_VALUES.items()
            for value in (event[key],)
        )
    )


def _validate_diagnostics(diagnostic_data: dict[str, object]) -> None:
    validation = diagnostic_data.get("r2_validation")
    if validation is not None and (
        not isinstance(validation, list) or not all(_valid_r2_validation(e) for e in validation)
    ):
        raise ValueError("R2 validation chỉ nhận metadata allowlist.")
    attempts = diagnostic_data["provider_attempts"]
    if attempts is not None:
        allowed = {
            "correlation_id",
            "usage",
            "event",
            "case_id",
            "call_id",
            "step",
            "attempt_index",
            "elapsed_ms",
            "effective_timeout_s",
            "attempts_remaining_before",
            "attempts_remaining_after",
            "remaining_case_time_s",
            "provider",
            "model",
            "success",
            "retryable",
            "will_retry",
            "retry_backoff_ms",
            "stop_reason",
            "exception_class",
            "http_status",
            "provider_code",
        }
        if not isinstance(attempts, list) or any(
            not isinstance(e, dict) or set(e) - allowed for e in attempts
        ):
            raise ValueError("Telemetry chỉ nhận metadata; không nhận body/prompt.")
        for event in attempts:
            _validate_usage(event.get("usage"))
    cost_meta = diagnostic_data.get("cost_metadata")
    if cost_meta is not None and (
        not isinstance(cost_meta, dict)
        or set(cost_meta)
        - {
            "kind",
            "pricing_source",
            "pricing_verified_on",
            "pricing_valid_through",
            "method",
            "billing_scope",
        }
        or any(not isinstance(v, str) for v in cost_meta.values())
    ):
        raise ValueError("Cost metadata chỉ nhận nhãn pricing allowlist.")
    calls = diagnostic_data["logical_calls"]
    if calls is not None and (
        not isinstance(calls, list)
        or any(
            not isinstance(c, dict) or set(c) - {"step", "ok", "latency_ms", "model", "error_class"}
            for c in calls
        )
    ):
        raise ValueError("Logical calls chỉ nhận metadata.")


def _validate_usage(usage: object) -> None:
    if usage is None:
        return
    numeric = {"input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens"}
    if (
        not isinstance(usage, dict)
        or set(usage) != numeric | {"response_model", "service_tier"}
        or any(
            usage[k] is not None and (type(usage[k]) is not int or usage[k] < 0) for k in numeric
        )
        or any(
            usage[k] is not None and not isinstance(usage[k], str)
            for k in ("response_model", "service_tier")
        )
    ):
        raise ValueError("Usage chỉ nhận validated counts và nhãn metadata.")


def _objects(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _rubric(prereg: dict[str, object]) -> dict[str, str]:
    meta = _objects(prereg["meta"])
    return {
        f"{group}:{index}": text
        for group in ("pass_criteria", "fail_signals", "forbidden_assumptions")
        for index, text in enumerate(meta[group])
    }


def _content(capture: Capture) -> dict[str, str]:
    result = capture.result
    card = _objects(result.get("card"))
    fields = {}
    for key in ("summary", "question"):
        if isinstance(card.get(key), str):
            fields[f"/result/card/{key}"] = card[key]
    for key in ("facts", "options"):
        for i, text in enumerate(card.get(key, [])):
            fields[f"/result/card/{key}/{i}"] = text
    for base, draft in (
        ("/result/draft", result.get("draft")),
        ("/result/card/partial_draft", card.get("partial_draft")),
    ):
        for key in ("subject", "body"):
            text = _objects(draft).get(key)
            if isinstance(text, str):
                fields[f"{base}/{key}"] = text
    return fields


def _structural(capture: Capture, prereg: dict[str, object]) -> dict[str, DimensionResult]:
    actual = _objects(capture.result.get("decision"))
    dimensions = {}
    for name, field, expected in (
        ("decision_match", "decision", "expected_decision"),
        ("escalation_type_match", "escalation_type", "expected_type"),
        ("rule_id_match", "rule_id", "expected_rule_id"),
    ):
        match = field in actual and actual[field] == prereg[expected]
        dimensions[name] = DimensionResult(
            "PASS" if match else "FAIL",
            [f"expected={prereg[expected]}; actual={actual.get(field)}"],
        )
    technical = (
        actual.get("decision") == "ERROR"
        or actual.get("rule_id") == "TECHNICAL_ERROR"
        or capture.result.get("status") == "ERROR"
    )
    dimensions["technical_error"] = DimensionResult(
        "FAIL" if technical else "PASS",
        [
            f"decision={actual.get('decision')}; rule={actual.get('rule_id')}; "
            f"status={capture.result.get('status')}; diagnostics={capture.diagnostics}"
        ],
    )
    statuses = {
        "AUTO_REPLY": {"PENDING_SEND", "PENDING_APPROVAL", "SENT"},
        "ESCALATE": {"AWAITING_HUMAN"},
        "ERROR": {"ERROR"},
    }
    consistent = capture.result.get("status") in statuses.get(actual.get("decision"), set())
    dimensions["case_status_consistency"] = DimensionResult(
        "PASS" if consistent else "FAIL",
        [f"decision={actual.get('decision')}; status={capture.result.get('status')}"],
    )
    return dimensions


def _grounding(capture: Capture) -> DimensionResult:
    result = capture.result
    evidence = _objects(result.get("evidence"))
    chunks = evidence.get("chunks")
    ids = {c["chunk_id"] for c in chunks} if isinstance(chunks, list) else None
    drafts = [result.get("draft"), _objects(result.get("card")).get("partial_draft")]
    if _objects(result.get("decision")).get("decision") == "AUTO_REPLY" and not drafts[0]:
        return DimensionResult("FAIL", ["AUTO_REPLY thiếu final draft."])
    for item in drafts:
        if item is None:
            continue
        draft = _objects(item)
        if draft.get("grounded") is False or draft.get("guard_failures"):
            return DimensionResult(
                "FAIL", [f"Draft guard không đạt: {draft.get('guard_failures')}"]
            )
        citations = draft.get("citations", [])
        if not citations or (ids is not None and not set(citations) <= ids):
            return DimensionResult("FAIL", [f"Draft citations={citations}; selected IDs={ids}"])
    return DimensionResult(
        "REVIEW_REQUIRED",
        [
            f"Selected evidence={evidence}; source statuses={capture.diagnostics.get('source_status')}",
            "Citation/guard hợp lệ không chứng minh entailment, coverage hoặc current policy claims.",
        ],
    )


def _question_options(capture: Capture, name: str, expected: str) -> DimensionResult:
    if expected != "ESCALATE":
        return DimensionResult("NOT_APPLICABLE", [])
    card = _objects(capture.result.get("card"))
    field = "question" if name == "question_quality" else "options"
    value = card.get(field)
    valid = (
        isinstance(value, str) and bool(value.strip()) and value.strip().endswith("?")
        if field == "question"
        else isinstance(value, list)
        and bool(value)
        and all(isinstance(v, str) and v.strip() for v in value)
    )
    if not valid:
        return DimensionResult("FAIL", [f"/result/card/{field} thiếu hoặc không hợp lệ: {value}"])
    return DimensionResult(
        "REVIEW_REQUIRED",
        [
            f"/result/card/{field}={value}",
            "Cần phân biệt câu hỏi/placeholder với factual claim; không suy PASS từ regex vắng mặt.",
        ],
    )


def _semantic_dimensions(capture: Capture, prereg: dict[str, object]) -> dict[str, DimensionResult]:
    dimensions = {"grounding_and_citation": _grounding(capture)}
    for name in ("question_quality", "options_quality"):
        dimensions[name] = _question_options(capture, name, prereg["expected_decision"])
    applicable = {
        name for names in criterion_dimensions(capture.case_id).values() for name in names
    }
    temporal = "temporal_safety" in applicable
    inp = _objects(prereg["input"])
    local_date = datetime.fromisoformat(inp["received_at"]).astimezone(VIETNAM_TIME).date()
    dimensions["temporal_safety"] = DimensionResult(
        "REVIEW_REQUIRED" if temporal else "NOT_APPLICABLE",
        (
            [
                f"received_at={inp['received_at']}; ngày Việt Nam={local_date}; "
                "tuần học là lời khai; C2 không tự quy đổi; C3 deadline chỉ là lời khai; C4 nguồn hiện hành."
            ]
            if temporal
            else []
        ),
    )
    conflict = "selective_conflict_handling" in applicable
    dimensions["selective_conflict_handling"] = DimensionResult(
        "REVIEW_REQUIRED" if conflict else "NOT_APPLICABLE",
        (
            [
                "A2 P01 ưu tiên; B3 phải giữ 70%/60% conflict; B4 chỉ hỏi hạn, "
                "không xác nhận tỷ lệ hoặc escalate vì refund conflict."
            ]
            if conflict
            else []
        ),
    )
    return dimensions


def _resolve(capture: Capture, path: str) -> object:
    if not path.startswith("/"):
        raise ValueError("Evidence phải có JSON pointer vào capture.")
    value: object = asdict(capture)
    try:
        for part in path[1:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            value = value[int(part)] if isinstance(value, list) else value[part]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError("Evidence pointer không tồn tại trong capture.") from error
    return value


def review_scope(capture: Capture, dimension: str) -> dict[str, str]:
    """Full-scope evidence cần cho PASS; chỉ integrity/coverage, không proof về nghĩa."""
    automatic = {
        "decision_match": "decision",
        "escalation_type_match": "escalation_type",
        "rule_id_match": "rule_id",
    }
    if dimension in automatic:
        paths = ["/result/decision/" + automatic[dimension]]
    elif dimension == "question_quality":
        paths = ["/result/card/question"]
    elif dimension == "options_quality":
        paths = ["/result/card/options"]
    else:
        paths = [
            "/result/" + key for key in ("card", "draft") if capture.result.get(key) is not None
        ]
        if dimension in {"grounding_and_citation", "selective_conflict_handling"}:
            paths += ["/result/evidence"]
        if dimension == "temporal_safety":
            paths += ["/identity/submitted_input"]
    values = {path: _resolve(capture, path) for path in paths}
    return {
        path: value if isinstance(value, str) else _json(value) for path, value in values.items()
    }


def _review_judgment(
    capture: Capture, row: ReviewDecision, automatic: DimensionResult
) -> DimensionResult:
    if row.verdict not in {"PASS", "FAIL"} or not row.rationale.strip() or not row.evidence:
        raise ValueError("Review thiếu verdict, rationale hoặc evidence.")
    if automatic.status in {"PASS", "FAIL"} and row.verdict != automatic.status:
        raise ValueError("Review không được override automatic condition.")
    if automatic.status == "NOT_APPLICABLE":
        raise ValueError("Review dimension không applicable.")
    quotes = []
    for ref in row.evidence:
        if not any(
            ref.path == root or ref.path.startswith(root + "/")
            for root in REVIEW_EVIDENCE_ROOTS[row.dimension]
        ):
            raise ValueError("Review evidence không thuộc dimension được chấm.")
        value = _resolve(capture, ref.path)
        text = value if isinstance(value, str) else _json(value)
        if not ref.quote.strip() or ref.quote not in text:
            raise ValueError("Review quote không khớp evidence trong capture.")
        quotes.append(f"{ref.path}: {ref.quote}")
    required = review_scope(capture, row.dimension)
    full = {(ref.path, ref.quote) for ref in row.evidence}
    complete = bool(required) and all((path, quote) in full for path, quote in required.items())
    if (
        row.dimension in {"grounding_and_citation", "selective_conflict_handling"}
        and capture.result.get("evidence") is None
    ):
        complete = False
    status = row.verdict if row.verdict == "FAIL" or complete else "REVIEW_REQUIRED"
    note = "Evidence structurally valid; semantic judgment do reviewer cung cấp."
    if not complete and row.verdict == "PASS":
        note += " Chưa cover full output/source scope; generic quote không đủ PASS."
    return DimensionResult(status, [row.rationale, note] + quotes)


def _criterion_review(
    capture: Capture,
    row: CriterionReview,
    required: tuple[str, ...],
    dimensions: dict[str, DimensionResult],
) -> dict[str, DimensionResult]:
    states = {
        name: DimensionResult(
            "REVIEW_REQUIRED", [f"Chưa review criterion {row.criterion_id} / {name}"]
        )
        for name in required
    }
    seen = set()
    for judgment in row.judgments:
        if judgment.dimension not in required or judgment.dimension in seen:
            raise ValueError("Criterion dimension invalid hoặc duplicate/contradictory.")
        seen.add(judgment.dimension)
        states[judgment.dimension] = _review_judgment(
            capture, judgment, dimensions[judgment.dimension]
        )
    return states


def _review_states(
    capture: Capture,
    dimensions: dict[str, DimensionResult],
    mapping: dict[str, tuple[str, ...]],
    review: HumanReview | None,
) -> dict[str, dict[str, DimensionResult]]:
    states = {
        key: {
            name: DimensionResult("REVIEW_REQUIRED", [f"Chưa có review {key}/{name}"])
            for name in names
        }
        for key, names in mapping.items()
    }
    if review is not None:
        if review.schema_version != 2 or _safe(asdict(review)) != asdict(review):
            raise ValueError("REVIEW_SCHEMA_V2_REQUIRED hoặc review chưa sanitized.")
        if review.capture_sha256 != capture_hash(capture):
            raise ValueError("Review không bind đúng capture SHA-256.")
        if (
            not review.reviewer.strip()
            or datetime.fromisoformat(review.reviewed_at).utcoffset() is None
        ):
            raise ValueError("Review thiếu reviewer hoặc timestamp timezone-aware.")
        seen = set()
        for row in review.criteria:
            if row.criterion_id not in mapping or row.criterion_id in seen:
                raise ValueError("Unknown hoặc duplicate/contradictory criterion ID.")
            seen.add(row.criterion_id)
            states[row.criterion_id] = _criterion_review(
                capture, row, mapping[row.criterion_id], dimensions
            )
    return states


def _apply_review(
    capture: Capture,
    dimensions: dict[str, DimensionResult],
    mapping: dict[str, tuple[str, ...]],
    review: HumanReview | None,
) -> dict[str, CriterionResult]:
    states = _review_states(capture, dimensions, mapping, review)
    results = {}
    for key, values in states.items():
        statuses = {d.status for d in values.values()}
        status = (
            "FAIL"
            if "FAIL" in statuses
            else "REVIEW_REQUIRED" if "REVIEW_REQUIRED" in statuses else "PASS"
        )
        results[key] = CriterionResult(
            status,
            mapping[key],
            [e for d in values.values() for e in d.evidence],
            "reviewer_semantic_judgment" if review else "unreviewed",
        )
    for name, automatic in list(dimensions.items()):
        if automatic.status != "REVIEW_REQUIRED":
            continue
        relevant = [values[name] for values in states.values() if name in values]
        if relevant:
            statuses = {d.status for d in relevant}
            status = (
                "FAIL"
                if "FAIL" in statuses
                else "REVIEW_REQUIRED" if "REVIEW_REQUIRED" in statuses else "PASS"
            )
            dimensions[name] = DimensionResult(
                status, automatic.evidence + [e for d in relevant for e in d.evidence]
            )
    if review is not None:
        seen = set()
        mapped = {name for names in mapping.values() for name in names}
        for row in review.dimension_reviews:
            if row.dimension in mapped or row.dimension in seen or row.dimension not in dimensions:
                raise ValueError(
                    "Supplemental dimension review không được cover/override criterion."
                )
            seen.add(row.dimension)
            dimensions[row.dimension] = _review_judgment(capture, row, dimensions[row.dimension])
    return results


def assess_capture(
    capture: Capture,
    *,
    review: HumanReview | None = None,
    fixture: Path = FIXTURE,
) -> Assessment:
    """Route đúng không đủ full PASS; mọi content rubric phải được review đầy đủ."""
    prereg = load_prereg(capture.case_id, fixture)
    if capture.fixture_sha256 != FIXTURE_SHA256:
        raise ValueError("BLOCKED_FIXTURE_HASH_MISMATCH")
    if _safe(asdict(capture)) != asdict(capture):
        raise ValueError("Capture chưa sanitized; không được đổi raw capture khi assessment.")
    _validate_identity(
        capture.identity, capture.case_id, capture.observation_id, capture.result, prereg
    )
    if set(capture.config) - CONFIG_LABELS:
        raise ValueError("Capture config chứa field ngoài allowlist.")
    dimensions = _structural(capture, prereg)
    dimensions.update(_semantic_dimensions(capture, prereg))
    rubric = _rubric(prereg)
    findings = [
        f"{path}: {text}" for path, text in _content(capture).items() if RISK_PATTERN.search(text)
    ]
    # Có/không có keyword chỉ là vị trí cần xem, không phải proof về nghĩa.
    for name, d in dimensions.items():
        if d.status == "REVIEW_REQUIRED":
            d.evidence.append(f"Frozen rubric: {rubric}")
            d.evidence.extend(findings)
    mapping = criterion_dimensions(capture.case_id)
    if set(mapping) != set(rubric):
        raise ValueError("CRITERION_MAPPING_INCOMPLETE")
    criteria = _apply_review(capture, dimensions, mapping, review)
    statuses = {d.status for d in dimensions.values()} | {c.status for c in criteria.values()}
    verdict = (
        "TECHNICAL_ERROR"
        if dimensions["technical_error"].status == "FAIL"
        else (
            "FAIL"
            if "FAIL" in statuses
            else "REVIEW_REQUIRED" if "REVIEW_REQUIRED" in statuses else "PASS"
        )
    )
    return Assessment(
        FIXTURE_SHA256,
        capture_hash(capture),
        capture.case_id,
        capture.observation_id,
        verdict,
        {
            field: prereg[field]
            for field in ("expected_decision", "expected_type", "expected_rule_id")
        },
        dimensions,
        rubric,
        findings,
        review,
        criteria,
    )


def write_artifacts(
    directory: Path,
    capture: Capture,
    *,
    review: HumanReview | None = None,
    fixture: Path = FIXTURE,
) -> Assessment:
    """Mỗi assessment là bundle mới; không ghi đè capture hoặc review cũ."""
    assessment = assess_capture(capture, review=review, fixture=fixture)
    directory.mkdir(parents=True, exist_ok=False)
    files = {"capture.json": asdict(capture), "assessment.json": asdict(assessment)}
    if review is not None:
        files["human_review.json"] = asdict(review)
    for name, data in files.items():
        with (directory / name).open("x", encoding="utf-8") as f:
            f.write(_json(_safe(data)) + "\n")
    rows = [
        f"# DEV / DIAGNOSTIC — {capture.case_id} / {capture.observation_id}",
        "",
        "NOT Set B; không phải independent final evaluation.",
        f"Verdict: {assessment.verdict}",
        f"Fixture SHA-256: {FIXTURE_SHA256}",
        f"Capture SHA-256: {assessment.capture_sha256}",
        "",
        "| Dimension | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, dimension in assessment.dimensions.items():
        evidence = " / ".join(dimension.evidence).replace("|", "\\|").replace("\n", "<br>")
        rows.append(f"| {name} | {dimension.status} | {evidence} |")
    rows += [
        "",
        "| Criterion | Status | Required dimensions | Judgment source |",
        "| --- | --- | --- | --- |",
    ]
    for key, criterion in assessment.criteria.items():
        rows.append(
            f"| {key} | {criterion.status} | {', '.join(criterion.required_dimensions)} "
            f"| {criterion.judgment_source} |"
        )
    rows += [
        "",
        "## Capture đầy đủ",
        "",
        "```json",
        _json(asdict(capture)),
        "```",
        "",
        "## Frozen rubric",
        "",
        _json(assessment.rubric),
        "",
    ]
    with (directory / "report.md").open("x", encoding="utf-8") as f:
        f.write(str(_safe("\n".join(rows))))
    return assessment


def main(arguments: list[str] | None = None) -> int:
    """CLI chỉ đọc capture/review đã có, không có nhánh LIVE/orchestration."""
    parser = argparse.ArgumentParser(description="Assessment M2 DEV offline từ capture đã lưu.")
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(arguments)
    capture = Capture(**json.loads(args.capture.read_text(encoding="utf-8")))
    review = None
    if args.review:
        raw = json.loads(args.review.read_text(encoding="utf-8"))
        if raw.get("schema_version") != 2 or "decisions" in raw or "criteria" not in raw:
            raise ValueError("REVIEW_SCHEMA_V2_REQUIRED: old review không được auto-upgrade.")

        def decision(row):
            return ReviewDecision(
                **{**row, "evidence": [EvidenceReference(**e) for e in row["evidence"]]}
            )

        criteria = [
            CriterionReview(row["criterion_id"], [decision(d) for d in row["judgments"]])
            for row in raw.pop("criteria")
        ]
        supplemental = [decision(row) for row in raw.pop("dimension_reviews", [])]
        review = HumanReview(**raw, criteria=criteria, dimension_reviews=supplemental)
    write_artifacts(args.output, capture, review=review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
