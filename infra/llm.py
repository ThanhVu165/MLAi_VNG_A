"""Wrapper Gemini có replay cassette và cache SQLite cho các bước LLM."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter
from typing import cast

from infra.db import execute, fetch_one, now_iso
from infra.settings import CASE_TIMEOUT_SECONDS, LLM_MAX_ATTEMPTS, LLM_RETRIES, LLM_TIMEOUT_S

LOGGER = logging.getLogger(__name__)
CASSETTE_DIRECTORY = Path("tests/cassettes")
CACHE_KEY_PREFIX = "llm_cache:"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MILLISECONDS_PER_SECOND = 1_000
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


@dataclass
class _CallBudget:
    remaining: int
    deadline: float


_BUDGET: ContextVar[_CallBudget | None] = ContextVar("llm_case_budget", default=None)


@contextmanager
def case_call_budget() -> Iterator[None]:
    """Một ngân sách chung cho toàn bộ lượt xử lý, kể cả các lần thử lại."""
    token = _BUDGET.set(_CallBudget(LLM_MAX_ATTEMPTS, perf_counter() + CASE_TIMEOUT_SECONDS))
    try:
        yield
    finally:
        _BUDGET.reset(token)


def _attempt_timeout(timeout_s: int) -> int:
    budget = _BUDGET.get()
    if budget is None:
        return min(timeout_s, LLM_TIMEOUT_S)
    remaining_seconds = int(budget.deadline - perf_counter())
    if budget.remaining <= 0 or remaining_seconds <= 0:
        raise TimeoutError("Đã hết thời gian hoặc số lần xử lý cho phép.")
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
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    prompt_hash = hashlib.sha256(
        json.dumps([model, schema, prompt, temperature], sort_keys=True, ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()
    result: LLMResult
    try:
        if temperature != 0.0:
            result = _failure("temperature phải bằng 0.", prompt_hash, model)
        elif timeout_s <= 0:
            result = _failure("timeout_s phải lớn hơn 0.", prompt_hash, model)
        else:
            result = _run_mode(prompt, schema, prompt_hash, model, timeout_s, retries)
    except Exception as error:
        LOGGER.exception("Lỗi không mong đợi khi gọi LLM", extra={"case_id": case_id, "step": step})
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
) -> LLMResult:
    mode = os.getenv("LLM_MODE", "live").lower()
    if mode == "replay":
        return _replay(prompt_hash, model)
    if mode not in {"live", "record"}:
        return _failure("LLM_MODE phải là live, replay hoặc record.", prompt_hash, model)

    cached = _load_cache(prompt_hash, model) if os.getenv("LLM_CACHE", "1") != "0" else None
    if cached is not None:
        return cached

    result = _call_live(prompt, schema, prompt_hash, model, timeout_s, retries)
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
) -> LLMResult:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _failure(
            "Chưa cấu hình kết nối dịch vụ AI. Hãy nhờ người quản trị bổ sung khóa truy cập rồi thử lại.",
            prompt_hash,
            model,
        )

    retry_count = min(max(retries, 0), LLM_RETRIES, 1)
    for attempt in range(retry_count + 1):
        try:
            remaining_timeout = _attempt_timeout(timeout_s)
            return _request_gemini(prompt, schema, prompt_hash, model, api_key, remaining_timeout)
        except Exception as error:
            LOGGER.warning("Lần gọi LLM %s thất bại: %s", attempt + 1, type(error).__name__)
            transient = isinstance(error, (TimeoutError, ConnectionError)) or type(
                error
            ).__name__ in {
                "DeadlineExceeded",
                "ServiceUnavailable",
                "ResourceExhausted",
                "InternalServerError",
                "ReadTimeout",
                "ConnectTimeout",
                "ConnectionError",
            }
            if not transient or attempt == retry_count:
                error_name = type(error).__name__
                if error_name in {
                    "TimeoutError",
                    "DeadlineExceeded",
                    "ReadTimeout",
                    "ConnectTimeout",
                }:
                    message = "Dịch vụ AI không phản hồi trong thời gian cho phép."
                elif error_name in {"ServiceUnavailable", "InternalServerError"}:
                    message = "Dịch vụ AI đang quá tải hoặc tạm thời không sẵn sàng."
                elif error_name == "ResourceExhausted":
                    message = "Dịch vụ AI báo đã chạm hạn mức của tài khoản."
                elif error_name in {"PermissionDenied", "Unauthenticated", "Forbidden"}:
                    message = "Dịch vụ AI không chấp nhận quyền truy cập hiện tại."
                elif error_name == "NotFound":
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
    return _failure("Dịch vụ AI chưa sẵn sàng; email được giữ lại để thử sau.", prompt_hash, model)


def _request_gemini(
    prompt: str,
    schema: dict[str, object],
    prompt_hash: str,
    model: str,
    api_key: str,
    timeout_s: int,
) -> LLMResult:
    import google.generativeai as genai

    genai.configure(api_key=api_key, transport="rest")
    response = genai.GenerativeModel(model).generate_content(
        prompt,
        generation_config={
            "temperature": 0.0,
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
        request_options={"timeout": min(timeout_s, LLM_TIMEOUT_S), "retry": None},
    )
    return _success(_parse_object(response.text), prompt_hash, model)


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
            _parse_object(payload["data"]), prompt_hash, str(payload.get("model", model))
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
