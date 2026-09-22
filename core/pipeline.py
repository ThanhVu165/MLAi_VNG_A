"""Đường chạy duy nhất R0--R14 cho paste, inbox và Verify."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from secrets import randbits
from time import perf_counter, time_ns
from typing import Literal, TypeVar, cast
from uuid import uuid4

from core.evidence import validate_evidence
from core.extract import extract_facts
from core.generate import generate_reply
from core.ground_guard import guard_groundedness
from core.policy_engine import PolicyInput, decide_policy
from core.prepolicy import decision_lock, multi_intent_plan
from core.question_gen import generate_escalation_card, generate_multi_intent_card
from core.question_guard import guard_question
from core.retrieval import retrieve_evidence
from core.results import load_result, save_result
from core.sanitize import (
    InputGuardResult,
    detect_language,
    guard_input,
    mask_pii,
    sanitize_body,
    strip_prompt_injection,
)
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    DraftReply,
    EscalationCard,
    EscalationType,
    EvidenceResult,
    EvidenceStatus,
    Extraction,
    PipelineResult,
    PolicyDecision,
)
from corpus.api import get_corpus_version
from infra.audit import log_event
from infra.db import execute, fetch_one, now_iso, to_utc_iso
from infra.llm import case_call_budget

logger = logging.getLogger(__name__)

MILLISECONDS_PER_SECOND = 1_000
NANOSECONDS_PER_MILLISECOND = 1_000_000
ULID_RANDOM_BITS = 80
CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
STEP_NAMES = tuple(f"R{number}" for number in range(15))
FAIL_SAFE_REASON = "Chưa xử lý được email do lỗi dịch vụ hoặc dữ liệu hệ thống. Hãy kiểm tra kết nối và chạy lại; chưa có thư nào được gửi."
INVALID_INPUT_REASON = "Email thiếu thông tin bắt buộc để tiếp nhận xử lý."
RECEIVED_REASON = "Đã tiếp nhận email để xử lý theo quy trình."
PROCESSING_REASON = "Đã làm sạch nội dung email và bắt đầu xử lý."
QUEUED_REASON = "Case cần chuyên viên quyết định trước khi trả lời."
PAUSED_REASON = "Tự động hóa đang tạm dừng nên case chờ chuyên viên duyệt."

T = TypeVar("T")


@dataclass(frozen=True)
class _Intake:
    case_id: str
    trace_id: str
    corpus_version: str
    status: CaseStatus
    input_guard: InputGuardResult


def _new_ulid() -> str:
    value = (time_ns() // NANOSECONDS_PER_MILLISECOND << ULID_RANDOM_BITS) | randbits(
        ULID_RANDOM_BITS
    )
    return "".join(CROCKFORD_BASE32[value >> (index * 5) & 31] for index in range(25, -1, -1))


def _is_missing_required(inp: CaseInput) -> bool:
    return not all((inp.sender.strip(), inp.subject.strip(), inp.body.strip())) or (
        inp.received_at.tzinfo is None or inp.received_at.utcoffset() is None
    )


def _r0_intake(inp: CaseInput, actor: str, case_id: str, trace_id: str) -> _Intake:
    existing = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if existing is not None:
        if existing["status"] != CaseStatus.RECEIVED or (
            existing["sender"],
            existing["subject"],
            existing["body_raw"],
        ) != (inp.sender, inp.subject, inp.body):
            raise ValueError("Email đã được xử lý hoặc dữ liệu tiếp nhận không khớp.")
        return _Intake(
            case_id,
            existing["trace_id"],
            existing["corpus_version"],
            CaseStatus.RECEIVED,
            guard_input(sanitize_body(inp.body)),
        )
    corpus_version = get_corpus_version()
    input_guard = guard_input(sanitize_body(inp.body))
    status = (
        CaseStatus.INVALID_INPUT
        if _is_missing_required(inp) or input_guard.decision is Decision.INVALID_INPUT
        else CaseStatus.RECEIVED
    )
    execute(
        """
        INSERT INTO cases (
            case_id, trace_id, channel, sender, subject, body_raw, body_masked, received_at, created_at,
            status, corpus_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            trace_id,
            inp.channel,
            inp.sender,
            inp.subject,
            inp.body,
            mask_pii(inp.body),
            to_utc_iso(inp.received_at),
            now_iso(),
            status,
            corpus_version,
        ),
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="CASE_RECEIVED",
        input_ref=case_id,
        reason=(
            (input_guard.reason or INVALID_INPUT_REASON)
            if status is CaseStatus.INVALID_INPUT
            else RECEIVED_REASON
        ),
        corpus_version=corpus_version,
    )
    return _Intake(case_id, trace_id, corpus_version, status, input_guard)


def _r1_sanitize(intake: _Intake, inp: CaseInput, actor: str) -> tuple[str, InputGuardResult]:
    body_clean = sanitize_body(inp.body)
    language = detect_language(body_clean)
    guard = guard_input(body_clean)
    injection = strip_prompt_injection(body_clean)
    execute(
        """
        UPDATE cases
        SET body_clean = ?, body_masked = ?, language = ?, injection_suspected = ?, status = ?
        WHERE case_id = ?
        """,
        (
            body_clean,
            mask_pii(body_clean),
            language,
            int(bool(injection.removed)),
            CaseStatus.PROCESSING,
            intake.case_id,
        ),
    )
    log_event(
        case_id=intake.case_id,
        actor=actor,
        action="CASE_SANITIZED",
        input_ref=intake.case_id,
        reason=PROCESSING_REASON,
        corpus_version=intake.corpus_version,
    )
    return body_clean, guard


def _transition(
    intake: _Intake,
    *,
    status: CaseStatus,
    actor: str,
    action: str,
    reason: str,
    rule_id: str | None = None,
) -> None:
    execute("UPDATE cases SET status = ? WHERE case_id = ?", (status, intake.case_id))
    log_event(
        case_id=intake.case_id,
        actor=actor,
        action=action,
        rule_id=rule_id,
        input_ref=intake.case_id,
        reason=reason,
        corpus_version=intake.corpus_version,
    )


def _save_extraction(intake: _Intake, extraction: Extraction) -> None:
    execute(
        "INSERT OR REPLACE INTO extractions (case_id, payload_json, llm_error, created_at) VALUES (?, ?, ?, ?)",
        (
            intake.case_id,
            json.dumps(asdict(extraction), ensure_ascii=False),
            extraction.llm_error,
            now_iso(),
        ),
    )


def _save_decision(intake: _Intake, decision: PolicyDecision) -> None:
    execute(
        """
        INSERT INTO decisions (
            decision_id, case_id, decision, escalation_type, rule_id, reason, evidence_ids_json,
            corpus_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            intake.case_id,
            decision.decision,
            decision.escalation_type,
            decision.rule_id,
            decision.reason,
            json.dumps(decision.evidence_ids, ensure_ascii=False),
            decision.corpus_version,
            now_iso(),
        ),
    )


def _save_draft(intake: _Intake, draft: DraftReply, *, kind: str = "auto") -> None:
    execute(
        """
        INSERT INTO drafts (
            draft_id, case_id, kind, subject, body, citations_json, grounded, guard_failures_json,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            intake.case_id,
            kind,
            draft.subject,
            mask_pii(draft.body),
            json.dumps(draft.citations, ensure_ascii=False),
            int(draft.grounded),
            json.dumps(draft.guard_failures, ensure_ascii=False),
            now_iso(),
        ),
    )


def _save_card(intake: _Intake, card: EscalationCard) -> None:
    execute(
        """
        INSERT OR REPLACE INTO escalations (
            case_id, escalation_type, summary, facts_json, basis_json, question, options_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            intake.case_id,
            card.escalation_type,
            card.summary,
            json.dumps(card.facts, ensure_ascii=False),
            json.dumps(card.basis, ensure_ascii=False),
            card.question,
            json.dumps(card.options, ensure_ascii=False),
            now_iso(),
        ),
    )


def _save_latencies(intake: _Intake, latencies: dict[str, int]) -> None:
    for step, milliseconds in latencies.items():
        execute(
            "INSERT INTO step_latencies (case_id, step, ms, ok, ts) VALUES (?, ?, ?, ?, ?)",
            (intake.case_id, step, milliseconds, 1, now_iso()),
        )


def _run_step(name: str, step: Callable[[], T], latencies: dict[str, int]) -> T:
    started = perf_counter()
    try:
        return step()
    finally:
        latencies[name] = round((perf_counter() - started) * MILLISECONDS_PER_SECOND)


def _fill_skipped_steps(latencies: dict[str, int]) -> None:
    for step in STEP_NAMES:
        latencies.setdefault(step, 0)


def _fail_safe_decision(corpus_version: str, error: str = "") -> PolicyDecision:
    reason = (
        mask_pii(error)
        if error.startswith(("Dịch vụ AI", "Chưa cấu hình", "Quy định đã thay đổi"))
        else FAIL_SAFE_REASON
    )
    return PolicyDecision(
        Decision.ERROR,
        None,
        "TECHNICAL_ERROR",
        reason,
        [],
        corpus_version,
    )


def _invalid_input_decision(corpus_version: str, reason: str | None = None) -> PolicyDecision:
    return PolicyDecision(
        Decision.INVALID_INPUT, None, "R0", reason or INVALID_INPUT_REASON, [], corpus_version
    )


def _out_of_policy_decision(corpus_version: str, reason: str) -> PolicyDecision:
    return PolicyDecision(
        Decision.ESCALATE, EscalationType.OUT_OF_POLICY, "R1", reason, [], corpus_version
    )


def _result(
    intake: _Intake,
    status: CaseStatus,
    decision: PolicyDecision,
    latencies: dict[str, int],
    started_at: datetime,
    extraction: Extraction | None = None,
    evidence: EvidenceResult | None = None,
    draft: DraftReply | None = None,
    card: EscalationCard | None = None,
) -> PipelineResult:
    return PipelineResult(
        intake.case_id,
        intake.trace_id,
        status,
        decision,
        extraction,
        evidence,
        draft,
        card,
        intake.corpus_version,
        latencies,
        started_at,
        datetime.now(timezone.utc),
    )


def _finalize(
    intake: _Intake,
    status: CaseStatus,
    decision: PolicyDecision,
    latencies: dict[str, int],
    started_at: datetime,
    extraction: Extraction | None = None,
    evidence: EvidenceResult | None = None,
    draft: DraftReply | None = None,
    card: EscalationCard | None = None,
) -> PipelineResult:
    _fill_skipped_steps(latencies)
    _run_step("R14", lambda: None, latencies)
    _save_latencies(intake, latencies)
    result = _result(
        intake, status, decision, latencies, started_at, extraction, evidence, draft, card
    )
    save_result(result)
    return result


def _queue(
    intake: _Intake, actor: str, decision: PolicyDecision, card: EscalationCard | None = None
) -> CaseStatus:
    if card is not None:
        _save_card(intake, card)
        if card.partial_draft is not None:
            _save_draft(intake, card.partial_draft, kind="partial")
    _transition(
        intake,
        status=CaseStatus.AWAITING_HUMAN,
        actor=actor,
        action="CASE_QUEUED",
        rule_id=decision.rule_id,
        reason=decision.reason or QUEUED_REASON,
    )
    return CaseStatus.AWAITING_HUMAN


def _escalation_card(
    intake: _Intake,
    actor: str,
    extraction: Extraction,
    evidence: EvidenceResult,
    decision: PolicyDecision,
    inp: CaseInput,
) -> EscalationCard:
    if (
        multi_intent_plan(extraction) is not None
        and evidence.chunks
        and evidence.status in (EvidenceStatus.OK, EvidenceStatus.UNSUPPORTED_DOMAIN)
        and not any(check != "supported_domain" for check in evidence.failed_checks)
    ):
        return generate_multi_intent_card(
            case_id=intake.case_id,
            actor=actor,
            corpus_version=intake.corpus_version,
            extraction=extraction,
            evidence=evidence,
            inp=inp,
            escalation_type=decision.escalation_type or EscalationType.AUTHORITY_REQUIRED,
        )
    return generate_escalation_card(
        case_id=intake.case_id,
        actor=actor,
        corpus_version=intake.corpus_version,
        escalation_type=decision.escalation_type or EscalationType.FACT_UNRESOLVED,
        extraction=extraction,
        evidence=evidence,
        inp=inp,
    )


def process_case(
    inp: CaseInput, *, actor: str = "SYSTEM", case_id: str | None = None
) -> PipelineResult:
    """Đường vào chung, giới hạn ngân sách gọi và trả lại kết quả đã lưu khi chạy trùng."""
    try:
        if case_id is not None:
            existing = load_result(case_id)
            if existing is not None:
                return existing
        with case_call_budget():
            return _process_case(inp, actor=actor, case_id=case_id)
    except Exception:
        logger.exception("Không thể đọc dữ liệu email để bắt đầu xử lý.")
        failed = _Intake(
            case_id or f"c_{_new_ulid()}",
            str(uuid4()),
            "",
            CaseStatus.ERROR,
            InputGuardResult(None, None, None),
        )
        return _result(
            failed, CaseStatus.ERROR, _fail_safe_decision(""), {}, datetime.now(timezone.utc)
        )


def _process_case(
    inp: CaseInput, *, actor: str = "SYSTEM", case_id: str | None = None
) -> PipelineResult:
    """Chạy duy nhất R0--R14 cho mọi channel và luôn trả kết quả fail-safe."""
    started_at = datetime.now(timezone.utc)
    case_id = case_id or f"c_{_new_ulid()}"
    trace_id = str(uuid4())
    latencies: dict[str, int] = {}
    intake: _Intake | None = None
    extraction: Extraction | None = None
    evidence: EvidenceResult | None = None
    draft: DraftReply | None = None
    card: EscalationCard | None = None
    try:
        intake = _run_step("R0", lambda: _r0_intake(inp, actor, case_id, trace_id), latencies)
        if intake.status is CaseStatus.INVALID_INPUT:
            _save_decision(
                intake, _invalid_input_decision(intake.corpus_version, intake.input_guard.reason)
            )
            return _finalize(
                intake,
                CaseStatus.INVALID_INPUT,
                _invalid_input_decision(intake.corpus_version, intake.input_guard.reason),
                latencies,
                started_at,
            )
        body_clean, input_guard = _run_step(
            "R1", lambda: _r1_sanitize(intake, inp, actor), latencies
        )
        if input_guard.decision is Decision.ESCALATE:
            decision = _out_of_policy_decision(
                intake.corpus_version, input_guard.reason or FAIL_SAFE_REASON
            )
            _save_decision(intake, decision)
            card = EscalationCard(
                inp.subject,
                ["Email sử dụng ngôn ngữ ngoài phạm vi tiếng Việt và tiếng Anh."],
                [],
                "Chuyên viên có thể xử lý bằng ngôn ngữ gốc hay cần yêu cầu người gửi bổ sung bản dịch?",
                ["Xử lý bằng ngôn ngữ gốc", "Yêu cầu bản dịch"],
                EscalationType.OUT_OF_POLICY,
                None,
            )
            return _finalize(
                intake,
                _queue(intake, actor, decision, card),
                decision,
                latencies,
                started_at,
                card=card,
            )
        extraction = _run_step(
            "R2",
            lambda: extract_facts(
                f"Tiêu đề: {inp.subject}\nNội dung: {body_clean}", intake.case_id
            ),
            latencies,
        )
        _save_extraction(intake, extraction)
        if extraction.llm_error:
            raise RuntimeError(extraction.llm_error)
        lock = _run_step("R3", lambda: decision_lock(extraction), latencies)
        log_event(
            case_id=intake.case_id,
            actor=actor,
            action="PREPOLICY_LOCKED",
            input_ref=intake.case_id,
            reason=(
                "Đã khóa quyền trả lời tự động."
                if lock
                else "Không cần khóa quyền trả lời tự động."
            ),
            corpus_version=intake.corpus_version,
        )
        retrieved = _run_step(
            "R4",
            lambda: retrieve_evidence(
                case_id=intake.case_id,
                actor=actor,
                inp=inp,
                body_clean=body_clean,
                extraction=extraction,
                corpus_version=intake.corpus_version,
            ),
            latencies,
        )
        evidence = _run_step(
            "R5",
            lambda: validate_evidence(
                case_id=intake.case_id,
                actor=actor,
                corpus_version=intake.corpus_version,
                evidence=retrieved,
                extraction=extraction,
            ),
            latencies,
        )
        _save_extraction(intake, extraction)
        decision = _run_step(
            "R6",
            lambda: decide_policy(
                PolicyInput(
                    intake.case_id,
                    actor,
                    intake.corpus_version,
                    lock,
                    evidence,
                    bool(extraction.llm_error),
                    False,
                    False,
                    False,
                )
            ),
            latencies,
        )
        if get_corpus_version() != intake.corpus_version:
            raise RuntimeError(
                "Quy định đã thay đổi trong khi đọc email. Hãy chạy lại để dùng nguồn mới."
            )
        _save_decision(intake, decision)
        if decision.decision is Decision.ERROR:
            raise RuntimeError(decision.reason)
        if decision.decision is Decision.AUTO_REPLY:
            if extraction.language not in {"vi", "en"}:
                raise ValueError("Ngôn ngữ không đủ điều kiện tự động trả lời.")
            draft = _run_step(
                "R7",
                lambda: generate_reply(
                    case_id=intake.case_id,
                    actor=actor,
                    corpus_version=intake.corpus_version,
                    language=cast(Literal["vi", "en"], extraction.language),
                    evidence=evidence,
                    inp=inp,
                    extraction=extraction,
                ),
                latencies,
            )
            assert draft is not None
            generated_draft = draft
            grounded = _run_step(
                "R8",
                lambda: guard_groundedness(
                    case_id=intake.case_id,
                    actor=actor,
                    corpus_version=intake.corpus_version,
                    draft=generated_draft,
                    evidence=evidence,
                ),
                latencies,
            )
            draft = grounded.draft
            _save_draft(intake, draft)
            if grounded.decision is not None:
                decision = grounded.decision
                _save_decision(intake, decision)
                raise ValueError(
                    "Bản nháp chưa vượt qua kiểm tra căn cứ: " + ", ".join(grounded.failed_checks)
                )
            else:
                from core.controls import is_automation_paused
                from core.dispatch import schedule_auto_reply

                if get_corpus_version() != intake.corpus_version:
                    raise RuntimeError("Quy định đã thay đổi trong khi soạn thư. Hãy chạy lại.")
                if is_automation_paused():
                    _run_step(
                        "R9",
                        lambda: _transition(
                            intake,
                            status=CaseStatus.PENDING_APPROVAL,
                            actor=actor,
                            action="CASE_QUEUED",
                            rule_id=decision.rule_id,
                            reason=PAUSED_REASON,
                        ),
                        latencies,
                    )
                    status = CaseStatus.PENDING_APPROVAL
                else:
                    _run_step(
                        "R9",
                        lambda: schedule_auto_reply(intake.case_id, decision=decision, actor=actor),
                        latencies,
                    )
                    status = CaseStatus.PENDING_SEND
        else:
            generated_card = _run_step(
                "R7",
                lambda: _escalation_card(intake, actor, extraction, evidence, decision, inp),
                latencies,
            )
            assert isinstance(generated_card, EscalationCard)
            card = _run_step(
                "R8",
                lambda: guard_question(
                    case_id=intake.case_id,
                    actor=actor,
                    corpus_version=intake.corpus_version,
                    card=generated_card,
                    regenerate=(
                        None
                        if generated_card.partial_draft is not None
                        else lambda: _escalation_card(
                            intake, actor, extraction, evidence, decision, inp
                        )
                    ),
                ),
                latencies,
            )
            status = _queue(intake, actor, decision, card)
        for step in ("R10", "R11", "R12", "R13"):
            _run_step(step, lambda: None, latencies)
        return _finalize(
            intake, status, decision, latencies, started_at, extraction, evidence, draft, card
        )
    except Exception as error:
        logger.exception(
            "Pipeline failed safely: %s", error, extra={"case_id": case_id, "trace_id": trace_id}
        )
        failed_intake = intake or _Intake(
            case_id, trace_id, "", CaseStatus.ERROR, InputGuardResult(None, None, None)
        )
        decision = _fail_safe_decision(failed_intake.corpus_version, str(error))
        if intake is not None:
            try:
                card = None
                _save_decision(intake, decision)
                _transition(
                    intake,
                    status=CaseStatus.ERROR,
                    actor=actor,
                    action="CASE_ERROR",
                    rule_id=decision.rule_id,
                    reason=decision.reason,
                )
                return _finalize(
                    intake,
                    CaseStatus.ERROR,
                    decision,
                    latencies,
                    started_at,
                    extraction,
                    evidence,
                    draft,
                    card,
                )
            except Exception as persistence_error:
                logger.exception("Không thể lưu trạng thái fail-safe: %s", persistence_error)
        _fill_skipped_steps(latencies)
        return _result(
            failed_intake,
            CaseStatus.ERROR,
            decision,
            latencies,
            started_at,
            extraction,
            evidence,
            draft,
            card,
        )
