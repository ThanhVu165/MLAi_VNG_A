"""Configured LLM provider with shared budgets, replay and SQLite cache."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from copy import deepcopy
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter, sleep
from typing import cast
from uuid import uuid4

from infra.db import execute, fetch_one, now_iso
from infra.demo_access import is_restricted_demo
from infra.judge_access import (
    CASE_INPUT_TOKEN_RESERVATION,
    CASE_OUTPUT_TOKEN_RESERVATION,
    JUDGE_LIVE_MAX_OUTPUT_TOKENS,
    active_case,
    check_active,
    finish_live_attempt,
    require_live_configuration,
    reserve_live_attempt,
)
from infra.provider_observability import (
    current_correlation,
    sanitize_case_id,
    sanitize_diagnostic,
)
from infra.settings import (
    CASE_TIMEOUT_SECONDS,
    LLM_MAX_ATTEMPTS,
    LLM_PROCESSING_MAX_ATTEMPTS,
    LLM_RETRIES,
    LLM_TIMEOUT_S,
)

LOGGER = logging.getLogger(__name__)
CASSETTE_DIRECTORY = Path("tests/cassettes")
CACHE_KEY_PREFIX = "llm_cache:"
MILLISECONDS_PER_SECOND = 1_000
LLM_RETRY_BACKOFF_SECONDS = 1.0
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


@dataclass
class _CallBudget:
    remaining: int
    deadline: float
    provider: str
    model: str


_BUDGET: ContextVar[_CallBudget | None] = ContextVar("llm_case_budget", default=None)


@dataclass
class _SimulationBudget:
    case_id: str
    directory: Path
    deadline: float
    input_tokens: int = 0
    output_tokens: int = 0
    attempts: int = 0
    blocked: bool = False


_SIMULATION: ContextVar[_SimulationBudget | None] = ContextVar("c2c_simulation", default=None)


@contextmanager
def _c2c_simulation(case_id: str, directory: Path) -> Iterator[_SimulationBudget]:
    """Server/test-only scope; usage khai báo synthetic, không phải provider hard cap."""
    if _SIMULATION.get() is not None or active_case() != case_id:
        raise ValueError("Scope mô phỏng phải gắn reservation judge, không được khởi tạo lồng.")
    check_active()
    if os.getenv("LLM_MODE", "live").lower() != "replay":
        raise ValueError("Mô phỏng C2-C chỉ cho phép replay.")
    state = _SimulationBudget(case_id, directory, perf_counter() + CASE_TIMEOUT_SECONDS)
    token = _SIMULATION.set(state)
    try:
        yield state
    finally:
        _SIMULATION.reset(token)


def _check_simulation(state: _SimulationBudget) -> None:
    if (
        state.blocked
        or active_case() != state.case_id
        or os.getenv("LLM_MODE", "live").lower() != "replay"
    ):
        raise ValueError("Scope mô phỏng không còn hợp lệ; giữ fail-closed.")
    if int(state.deadline - perf_counter()) <= 0:
        raise CaseDeadlineExhausted("Đã hết thời gian xử lý email cho phép.")


class CaseAttemptsExhausted(TimeoutError):
    """Không còn lượt gọi trong ngân sách hiện tại."""


class CaseDeadlineExhausted(TimeoutError):
    """Đã hết thời gian xử lý email."""


def has_call_capacity() -> bool:
    """Kiểm tra lượt còn lại; deadline và quyền judge vẫn phải hợp lệ."""
    if active_case() is not None:
        check_active()
    simulation = _SIMULATION.get()
    if simulation is not None:
        _check_simulation(simulation)
        if simulation.attempts >= LLM_PROCESSING_MAX_ATTEMPTS:
            return False
    budget = _BUDGET.get()
    if budget is None:
        return True
    if int(budget.deadline - perf_counter()) <= 0:
        raise CaseDeadlineExhausted("Đã hết thời gian xử lý email cho phép.")
    return budget.remaining > 0


@contextmanager
def case_call_budget(max_attempts: int = LLM_MAX_ATTEMPTS) -> Iterator[None]:
    """Một ngân sách chung cho toàn bộ lượt xử lý, kể cả các lần thử lại."""
    if not 0 < max_attempts <= LLM_MAX_ATTEMPTS:
        raise ValueError("Ngân sách lượt gọi phải nằm trong giới hạn của mỗi case.")
    provider, model = _provider_config()
    token = _BUDGET.set(
        _CallBudget(max_attempts, perf_counter() + CASE_TIMEOUT_SECONDS, provider, model)
    )
    try:
        yield
    finally:
        _BUDGET.reset(token)


def _attempt_timeout(timeout_s: int) -> int:
    if not has_call_capacity():
        raise CaseAttemptsExhausted("Đã hết số lượt xử lý email cho phép.")
    budget = _BUDGET.get()
    if budget is None:
        return min(timeout_s, LLM_TIMEOUT_S)
    remaining_seconds = int(budget.deadline - perf_counter())
    if remaining_seconds <= 0:
        raise CaseDeadlineExhausted("Đã hết thời gian xử lý email cho phép.")
    budget.remaining -= 1
    return min(timeout_s, LLM_TIMEOUT_S, remaining_seconds)


@dataclass(frozen=True)
class LLMResult:
    """Kết quả có cấu trúc của một lần gọi LLM, kể cả khi lỗi."""

    ok: bool
    data: JsonObject
    error: str | None
    latency_ms: int
    prompt_hash: str
    model: str
    usage: dict[str, object] | None = None


def _provider_config() -> tuple[str, str]:
    if os.getenv("LLM_PROVIDER", "openai").strip().lower() != "openai":
        raise ValueError("LLM_PROVIDER chỉ hỗ trợ openai.")
    return "openai", os.getenv("OPENAI_MODEL", "").strip()


def _prompt_hash(identity: list[object]) -> str:
    return hashlib.sha256(
        json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def call_json(
    prompt: str,
    *,
    schema: dict[str, object],
    step: str,
    case_id: str,
    timeout_s: int = LLM_TIMEOUT_S,
    retries: int = LLM_RETRIES,
    temperature: float = 0.0,
) -> LLMResult:
    """Gọi LLM theo chế độ cấu hình và luôn trả về ``LLMResult``."""
    started = perf_counter()
    budget = _BUDGET.get()
    try:
        provider, model = (budget.provider, budget.model) if budget else _provider_config()
    except ValueError:
        prompt_hash = _prompt_hash(["openai", "", schema, prompt, temperature])
        latency_ms = round((perf_counter() - started) * MILLISECONDS_PER_SECOND)
        _record_latency(case_id, step, False, latency_ms)
        return replace(
            _failure("LLM_PROVIDER chỉ hỗ trợ openai.", prompt_hash, ""),
            latency_ms=latency_ms,
        )
    prompt_hash = _prompt_hash([provider, model, schema, prompt, temperature])
    result: LLMResult
    try:
        if not model:
            result = _failure("Chưa cấu hình OPENAI_MODEL.", prompt_hash, model)
        elif temperature != 0.0:
            result = _failure("temperature phải bằng 0.", prompt_hash, model)
        elif timeout_s <= 0:
            result = _failure("timeout_s phải lớn hơn 0.", prompt_hash, model)
        else:
            result = _run_mode(
                prompt,
                schema,
                prompt_hash,
                model,
                timeout_s,
                retries,
                case_id=case_id,
                step=step,
                provider=provider,
            )
    except (CaseAttemptsExhausted, CaseDeadlineExhausted) as error:
        result = _failure(f"{error} Email được giữ lại, chưa gửi phản hồi.", prompt_hash, model)
    except Exception as error:
        LOGGER.warning("Lỗi không mong đợi khi gọi LLM: %s", type(error).__name__)
        result = _failure(f"Lỗi LLM: {type(error).__name__}", prompt_hash, model)

    latency_ms = round((perf_counter() - started) * MILLISECONDS_PER_SECOND)
    result = replace(result, latency_ms=latency_ms)
    _record_latency(case_id, step, result.ok, latency_ms)
    return result


def _run_mode(
    prompt: str,
    schema: dict[str, object],
    prompt_hash: str,
    model: str,
    timeout_s: int,
    retries: int,
    *,
    case_id: str | None = None,
    step: str | None = None,
    provider: str = "openai",
) -> LLMResult:
    mode = os.getenv("LLM_MODE", "live").lower()
    simulation = _SIMULATION.get()
    if simulation is not None:
        _check_simulation(simulation)
        check_active()
        if case_id != simulation.case_id:
            return _failure("Case không khớp scope mô phỏng C2-C.", prompt_hash, model)
        return _c2c_replay(simulation, prompt_hash, model, timeout_s)
    if active_case() is not None:
        check_active()
        if case_id != active_case():
            return _failure("Case không khớp reservation judge.", prompt_hash, model)
        if mode == "replay":
            _attempt_timeout(timeout_s)
            return _replay(prompt_hash, model)
        if mode == "live":
            try:
                require_live_configuration()
            except Exception:
                return _failure("Cấu hình Judge LIVE không hợp lệ.", prompt_hash, model)
            return _call_live(
                prompt,
                schema,
                prompt_hash,
                model,
                timeout_s,
                retries,
                case_id=case_id,
                step=step,
                provider=provider,
            )
        return _failure("Judge chỉ cho phép replay hoặc LIVE được cấp quyền.", prompt_hash, model)
    if is_restricted_demo():
        if mode in {"live", "replay"}:
            # Chỉ active Judge lease ở nhánh trên được phép đi LIVE.
            return _replay(prompt_hash, model)
        return _failure("Restricted DEMO không cho phép record hoặc mode lạ.", prompt_hash, model)
    if mode not in {"live", "record"}:
        return _failure("LLM_MODE phải là live, replay hoặc record.", prompt_hash, model)

    cached = _load_cache(prompt_hash, model) if os.getenv("LLM_CACHE", "1") != "0" else None
    if cached is not None:
        return cached

    result = _call_live(
        prompt,
        schema,
        prompt_hash,
        model,
        timeout_s,
        retries,
        case_id=case_id,
        step=step,
        provider=provider,
    )
    if result.ok:
        _store_cache(result)
        if mode == "record":
            _record_cassette(result)
    return result


def _call_live(
    prompt: str,
    schema: dict[str, object],
    prompt_hash: str,
    model: str,
    timeout_s: int,
    retries: int,
    *,
    case_id: str | None = None,
    step: str | None = None,
    provider: str = "openai",
) -> LLMResult:
    if provider != "openai":
        return _failure("LLM_PROVIDER chỉ hỗ trợ openai.", prompt_hash, model)
    if not model:
        return _failure("Chưa cấu hình OPENAI_MODEL.", prompt_hash, model)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _failure(
            "Chưa cấu hình kết nối dịch vụ AI. Hãy nhờ người quản trị bổ sung khóa truy cập rồi thử lại.",
            prompt_hash,
            model,
        )

    call_id = uuid4().hex
    retry_count = min(max(retries, 0), LLM_RETRIES, 1)
    for attempt in range(retry_count + 1):
        budget = _BUDGET.get()
        attempts_before = budget.remaining if budget is not None else None
        remaining_case_time = (
            max(0.0, budget.deadline - perf_counter()) if budget is not None else None
        )
        started = perf_counter()
        remaining_timeout = None
        request_started = False
        judge_live = active_case() is not None
        try:
            remaining_timeout = _attempt_timeout(timeout_s)
            if judge_live:
                reserve_live_attempt(JUDGE_LIVE_MAX_OUTPUT_TOKENS)
            request_started = True
            result = _request_openai(
                prompt,
                schema,
                prompt_hash,
                model,
                api_key,
                remaining_timeout,
                **({"max_output_tokens": JUDGE_LIVE_MAX_OUTPUT_TOKENS} if judge_live else {}),
            )
        except Exception as error:
            accounting_ok = True
            if judge_live and request_started:
                try:
                    accounting_ok = finish_live_attempt(
                        getattr(error, "_validated_response_usage", None),
                        response_received=bool(
                            getattr(error, "_provider_response_received", False)
                        ),
                    )
                except Exception:
                    accounting_ok = False
            LOGGER.warning("Lần gọi LLM %s thất bại: %s", attempt + 1, type(error).__name__)
            transient = accounting_ok and request_started and _openai_retryable(error)
            will_retry = request_started and transient and attempt < retry_count
            retry_backoff_s = 0.0
            if will_retry:
                budget = _BUDGET.get()
                if (
                    budget is None
                    or budget.deadline - perf_counter() > LLM_RETRY_BACKOFF_SECONDS + 1
                ):
                    retry_backoff_s = LLM_RETRY_BACKOFF_SECONDS
            _record_provider_attempt(
                prompt=prompt,
                provider=provider,
                model=model,
                case_id=case_id,
                step=step,
                call_id=call_id,
                attempt_index=attempt + 1,
                started=started,
                effective_timeout_s=remaining_timeout,
                attempts_before=attempts_before,
                remaining_case_time_s=remaining_case_time,
                request_started=request_started,
                success=False,
                error=error,
                usage=getattr(error, "_validated_response_usage", None),
                retryable=request_started and transient,
                will_retry=will_retry,
                retry_backoff_ms=round(retry_backoff_s * MILLISECONDS_PER_SECOND),
                stop_reason=(
                    (
                        "case_deadline_exhausted"
                        if isinstance(error, CaseDeadlineExhausted)
                        else (
                            "case_attempts_exhausted"
                            if isinstance(error, CaseAttemptsExhausted)
                            else "non_retryable"
                        )
                    )
                    if not request_started
                    else (
                        "non_retryable"
                        if not transient
                        else "retry_limit" if attempt == retry_count else None
                    )
                ),
            )
            if not will_retry:
                error_name = type(error).__name__
                if isinstance(error, (CaseAttemptsExhausted, CaseDeadlineExhausted)):
                    return _failure(
                        f"{error} Email được giữ lại, chưa gửi phản hồi.", prompt_hash, model
                    )
                if error_name in {
                    "TimeoutError",
                    "APITimeoutError",
                }:
                    message = "Dịch vụ AI không phản hồi trong thời gian cho phép."
                elif error_name in {
                    "InternalServerError",
                }:
                    message = "Dịch vụ AI đang quá tải hoặc tạm thời không sẵn sàng."
                elif error_name == "RateLimitError":
                    message = "Dịch vụ AI báo đã chạm hạn mức của tài khoản."
                elif error_name in {
                    "AuthenticationError",
                    "PermissionDeniedError",
                }:
                    message = "Dịch vụ AI không chấp nhận quyền truy cập hiện tại."
                elif error_name == "NotFoundError":
                    message = "Dịch vụ AI không tìm thấy mô hình đã cấu hình."
                else:
                    message = (
                        "Dịch vụ AI chưa xử lý được yêu cầu do kết nối hoặc cấu hình chưa phù hợp."
                    )
                return _failure(
                    f"{message} Email được giữ lại, chưa gửi phản hồi. Hãy kiểm tra kết nối/cấu hình rồi thử lại.",
                    prompt_hash,
                    model,
                )
            if retry_backoff_s:
                sleep(retry_backoff_s)
        else:
            if judge_live:
                try:
                    if not finish_live_attempt(result.usage, response_received=True):
                        return _failure(
                            "Usage Judge LIVE thiếu hoặc không hợp lệ; đã dừng fail-closed.",
                            prompt_hash,
                            model,
                        )
                except Exception:
                    return _failure(
                        "Không đối soát được usage Judge LIVE; đã dừng fail-closed.",
                        prompt_hash,
                        model,
                    )
            _record_provider_attempt(
                prompt=prompt,
                provider=provider,
                model=model,
                case_id=case_id,
                step=step,
                call_id=call_id,
                attempt_index=attempt + 1,
                started=started,
                effective_timeout_s=remaining_timeout,
                attempts_before=attempts_before,
                remaining_case_time_s=remaining_case_time,
                request_started=True,
                success=result.ok,
                error=None,
                retryable=False,
                will_retry=False,
                retry_backoff_ms=0,
                stop_reason=None,
                usage=result.usage,
            )
            return result
    return _failure("Dịch vụ AI chưa sẵn sàng; email được giữ lại để thử sau.", prompt_hash, model)


def _record_provider_attempt(
    *,
    prompt: str,
    provider: str,
    model: str,
    case_id: str | None,
    step: str | None,
    call_id: str,
    attempt_index: int,
    started: float,
    effective_timeout_s: int | None,
    attempts_before: int | None,
    remaining_case_time_s: float | None,
    request_started: bool,
    success: bool,
    error: Exception | None,
    retryable: bool,
    will_retry: bool,
    retry_backoff_ms: int,
    stop_reason: str | None,
    usage: dict[str, object] | None = None,
) -> None:
    """Reuse the existing logger; diagnostics must never mask the original outcome."""
    try:
        budget = _BUDGET.get()
        event = {
            "correlation_id": current_correlation(case_id),
            "usage": usage,
            "event": (
                "llm_provider_attempt" if request_started else "llm_provider_attempt_skipped"
            ),
            "case_id": sanitize_case_id(case_id, prompt=prompt),
            # No trace_id is propagated to this wrapper; do not invent one or query/write DB.
            "trace_id": None,
            "call_id": call_id,
            "step": sanitize_diagnostic(step, prompt=prompt),
            "attempt_index": attempt_index,
            "elapsed_ms": round((perf_counter() - started) * MILLISECONDS_PER_SECOND),
            "effective_timeout_s": effective_timeout_s,
            "attempts_remaining_before": attempts_before,
            "attempts_remaining_after": (budget.remaining if budget is not None else None),
            "remaining_case_time_s": remaining_case_time_s,
            "model": sanitize_diagnostic(model, prompt=prompt),
            "provider": provider,
            "prompt_chars": len(prompt),
            "prompt_hash12": hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12],
            "success": success,
            "retryable": retryable,
            "will_retry": will_retry,
            "retry_backoff_ms": retry_backoff_ms,
            "stop_reason": stop_reason,
        }
        if error is not None:
            # SDK messages may contain arbitrary response bodies. Metadata only.
            event.update(
                {
                    "exception_class": type(error).__name__,
                    "http_status": getattr(error, "status_code", None),
                    "provider_code": sanitize_diagnostic(
                        getattr(error, "code", None), prompt=prompt
                    ),
                }
            )
        # WARNING ensures successful attempts are retained alongside failures by default.
        LOGGER.warning(
            "LLM provider evidence %s",
            json.dumps(event, ensure_ascii=False),
            extra={"provider_attempt": event},
        )
    except Exception:
        # Logging/SDK metadata failures cannot change retry, budget, or return values.
        pass


def _openai_retryable(error: Exception) -> bool:
    from openai import APIConnectionError, APIStatusError

    if isinstance(error, (TimeoutError, ConnectionError, APIConnectionError)):
        return True
    if isinstance(error, APIStatusError):
        return 500 <= error.status_code <= 599 or (
            error.status_code == 429 and error.code == "rate_limit_exceeded"
        )
    return False


def _openai_schema(schema: dict[str, object]) -> dict[str, object]:
    """Exact strict_copy transformation from the compatibility probe."""
    normalized = deepcopy(schema)

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(normalized)
    return normalized


def _request_openai(
    prompt: str,
    schema: dict[str, object],
    prompt_hash: str,
    model: str,
    api_key: str,
    timeout_s: int,
    *,
    temperature: float = 0.0,
    max_output_tokens: int | None = None,
) -> LLMResult:
    if _SIMULATION.get() is not None:
        raise ValueError("Mô phỏng C2-C không được gọi provider LIVE.")
    from openai import OpenAI

    reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "none").strip().lower()
    sampling = {"temperature": temperature} if reasoning_effort == "none" else {}
    with OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        max_retries=0,
        timeout=min(timeout_s, LLM_TIMEOUT_S),
    ) as client:
        output_limit = (
            {"max_completion_tokens": max_output_tokens}
            if type(max_output_tokens) is int and max_output_tokens > 0
            else {}
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            reasoning_effort=reasoning_effort,
            **sampling,
            **output_limit,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "result",
                    "strict": True,
                    "schema": _openai_schema(schema),
                },
            },
        )
    usage = _response_usage(response)
    try:
        choice = response.choices[0]
        if choice.message.refusal or choice.finish_reason != "stop":
            raise ValueError("Refused or incomplete structured output")
        return replace(
            _success(_parse_object(choice.message.content or ""), prompt_hash, model),
            usage=usage,
        )
    except Exception as error:
        # Giữ nguyên loại lỗi; chỉ mang numeric usage đã kiểm tra sang attempt telemetry.
        error._validated_response_usage = usage
        error._provider_response_received = True
        raise


def _response_usage(response: object) -> dict[str, object] | None:
    try:
        return _extract_usage(response)
    except Exception:
        # Telemetry không được biến successful business output thành failure.
        return None


def _extract_usage(response: object) -> dict[str, object] | None:
    """Chỉ numeric usage + nhãn an toàn; không serialize SDK response."""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens, total)):
        return None
    if total != input_tokens + output_tokens:
        return None
    details = getattr(usage, "prompt_tokens_details", None)
    cached = getattr(details, "cached_tokens", None)
    written = getattr(details, "cache_write_tokens", None)
    if any(
        n is not None and (type(n) is not int or not 0 <= n <= input_tokens)
        for n in (cached, written)
    ):
        return None
    if cached is not None and written is not None and cached + written > input_tokens:
        return None
    tier = getattr(response, "service_tier", None)
    response_model = getattr(response, "model", None)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached,
        "cache_write_tokens": written,
        "response_model": (
            sanitize_diagnostic(response_model) if type(response_model) is str else None
        ),
        "service_tier": (
            tier
            if type(tier) is str and tier in ("default", "flex", "priority", "scale", "auto")
            else None
        ),
    }


def _c2c_replay(
    state: _SimulationBudget, prompt_hash: str, model: str, timeout_s: int
) -> LLMResult:
    """Debit trước response mô phỏng; chỉ đối soát bằng usage synthetic hợp lệ."""
    try:
        payload = json.loads((state.directory / f"{prompt_hash}.json").read_text(encoding="utf-8"))
        if (
            payload["is_synthetic"] is not True
            or payload["model"] != model
            or payload["prompt_hash"] != prompt_hash
        ):
            raise ValueError("Không xác minh được fixture mô phỏng.")
        request = payload["request"]
        input_tokens, output_limit = request["input_tokens"], request["max_output_tokens"]
        if (
            type(input_tokens) is not int
            or input_tokens < 0
            or type(output_limit) is not int
            or output_limit <= 0
            or state.input_tokens + input_tokens > CASE_INPUT_TOKEN_RESERVATION
            or state.output_tokens + output_limit > CASE_OUTPUT_TOKEN_RESERVATION
        ):
            raise ValueError("Không đủ ngân sách token mô phỏng.")
        _attempt_timeout(timeout_s)
        state.attempts += 1
        state.input_tokens += input_tokens
        state.output_tokens += output_limit
        usage = payload["usage"]
        if (
            type(usage["input_tokens"]) is not int
            or usage["input_tokens"] != input_tokens
            or type(usage["output_tokens"]) is not int
            or not 0 <= usage["output_tokens"] <= output_limit
        ):
            raise ValueError("Usage mô phỏng thiếu hoặc không đáng tin cậy.")
        # Chỉ đối soát allocation trong RAM khi usage hợp lệ; không refund ledger C2-A.
        state.output_tokens -= output_limit - usage["output_tokens"]
        return replace(
            _success(_parse_object(payload["data"]), prompt_hash, model),
            usage={**usage, "source": "synthetic"},
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        state.blocked = True
        return _failure("Mô phỏng C2-C bị chặn; chưa xác minh ngân sách/usage.", prompt_hash, model)


def _replay(prompt_hash: str, model: str) -> LLMResult:
    cassette_path = CASSETTE_DIRECTORY / f"{prompt_hash}.json"
    try:
        payload = json.loads(cassette_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Cassette phải là JSON object.")
        data = payload.get("data", payload)
        return _success(_parse_object(data), prompt_hash, str(payload.get("model", model)))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        LOGGER.warning("Không đọc được cassette %s: %s", prompt_hash, type(error).__name__)
        return _failure("Không có cassette hợp lệ cho prompt này.", prompt_hash, model)


def _load_cache(prompt_hash: str, model: str) -> LLMResult | None:
    try:
        row = fetch_one("SELECT value FROM settings WHERE key = ?", (_cache_key(prompt_hash),))
        if row is None:
            return None
        payload = json.loads(row["value"])
        if not isinstance(payload, dict):
            raise ValueError("Cache phải là JSON object.")
        return _success(
            _parse_object(payload["data"]),
            prompt_hash,
            str(payload.get("model", model)),
        )
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        LOGGER.warning("Bỏ qua cache LLM lỗi: %s", type(error).__name__)
        return None


def _store_cache(result: LLMResult) -> None:
    payload = json.dumps({"data": result.data, "model": result.model}, ensure_ascii=False)
    try:
        execute(
            "INSERT INTO settings (key, value, updated_at, actor) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (_cache_key(result.prompt_hash), payload, now_iso(), "SYSTEM"),
        )
    except Exception as error:
        LOGGER.warning("Không lưu được cache LLM: %s", type(error).__name__)


def _record_cassette(result: LLMResult) -> None:
    try:
        CASSETTE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cassette = {"data": result.data, "model": result.model}
        (CASSETTE_DIRECTORY / f"{result.prompt_hash}.json").write_text(
            json.dumps(cassette, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as error:
        LOGGER.warning("Không ghi được cassette LLM: %s", type(error).__name__)


def _record_latency(case_id: str, step: str, ok: bool, latency_ms: int) -> None:
    try:
        execute(
            "INSERT INTO step_latencies (case_id, step, ms, ok, ts) VALUES (?, ?, ?, ?, ?)",
            (case_id, step, latency_ms, int(ok), now_iso()),
        )
    except Exception as error:
        LOGGER.warning("Không ghi được latency LLM: %s", type(error).__name__)


def _parse_object(value: object) -> JsonObject:
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, dict):
        raise ValueError("LLM phải trả về JSON object.")
    return cast(JsonObject, parsed)


def _success(data: JsonObject, prompt_hash: str, model: str) -> LLMResult:
    return LLMResult(True, data, None, 0, prompt_hash, model)


def _failure(error: str, prompt_hash: str, model: str) -> LLMResult:
    return LLMResult(False, {}, error, 0, prompt_hash, model)


def _cache_key(prompt_hash: str) -> str:
    return f"{CACHE_KEY_PREFIX}{prompt_hash}"
