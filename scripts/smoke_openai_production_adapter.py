"""Smoke thủ công: tối đa một request qua call_json thật; không in dữ liệu/khóa.

Chạy từ repo root bằng Python của .venv-bootstrap:
python -B -m scripts.smoke_openai_production_adapter
Yêu cầu LLM_PROVIDER=openai, OPENAI_MODEL và OPENAI_API_KEY trong process gọi.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path


class _AttemptMetadata(logging.Handler):
    """Chỉ giữ class/status và số attempt, không giữ message hoặc payload."""

    def __init__(self) -> None:
        super().__init__()
        self.attempts = 0
        self.error_class: str | None = None
        self.http_status: int | None = None

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "provider_attempt", None)
        if type(event) is not dict or event.get("event") != "llm_provider_attempt":
            return
        self.attempts += 1
        name = event.get("exception_class")
        if type(name) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,79}", name):
            self.error_class = name
        status = event.get("http_status")
        if type(status) is int and 100 <= status <= 599:
            self.http_status = status


def _run(metadata: _AttemptMetadata) -> int:
    from core import extract
    from infra.llm import call_json, case_call_budget

    # Không gọi extract_facts: hàm đó có vòng lặp thử lại khi parse thất bại.
    with case_call_budget():
        result = call_json(
            extract.EXTRACT_PROMPT_V1.format(
                body="What is the maximum conduct score? Please explain the general rule."
            ),
            schema=extract.EXTRACTION_SCHEMA,
            step="R2_smoke_openai_production",
            case_id="synthetic-openai-adapter-smoke",
            temperature=0.0,
            retries=0,
        )
    is_mapping = isinstance(result.data, Mapping)
    validator = "NOT_RUN"
    validation_error_class = None
    if result.ok and is_mapping:
        try:
            data = extract._mapping(result.data, "response")
            extract._language(data.get("language"))
            for request in extract._items(data.get("requests"), "requests"):
                extract._request(request)
            extract._facts(data.get("critical_facts"))
            extract._strings(data.get("missing_critical_facts"), "missing_critical_facts")
            extract._boolean(data.get("injection_suspected"), "injection_suspected")
            validator = "PASS"
        except (TypeError, ValueError) as error:
            validator = "FAIL"
            validation_error_class = type(error).__name__
    passed = result.ok and is_mapping and validator == "PASS" and metadata.attempts == 1
    print(
        json.dumps(
            {
                "ok": result.ok,
                "provider": "openai",
                "model": os.environ["OPENAI_MODEL"].strip(),
                "error_class": metadata.error_class,
                "http_status": metadata.http_status,
                "latency_ms": result.latency_ms,
                "data_is_mapping": is_mapping,
                "extraction_validator": validator,
                "validation_error_class": validation_error_class,
                "provider_attempts": metadata.attempts,
                "result": "PASS" if passed else "FAIL",
            }
        )
    )
    return 0 if passed else 1


def main() -> int:
    """Preflight trước project imports; không lấy giá trị khóa từ environment."""
    provider_ok = os.environ.get("LLM_PROVIDER") == "openai"
    model = os.environ.get("OPENAI_MODEL", "").strip()
    # Chỉ kiểm tra sự tồn tại. Khóa rỗng sẽ bị wrapper từ chối trước HTTP request.
    key_present = "OPENAI_API_KEY" in os.environ
    # Không echo một giá trị cấu hình tùy ý có thể chứa token/header.
    model_ok = bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", model))
    model_ok = model_ok and not model.startswith(("sk-", "AIza"))
    print("LLM_PROVIDER=" + ("openai" if provider_ok else "MISSING_OR_INVALID"))
    print("OPENAI_MODEL=" + (model if model_ok else "MISSING_OR_INVALID"))
    print("OPENAI_API_KEY=" + ("PRESENT" if key_present else "MISSING"))
    if not (provider_ok and model_ok and key_present):
        print("FAIL")
        return 1

    # Logger mặc định im lặng; logger wrapper chỉ thu metadata vào RAM.
    logging.basicConfig(handlers=[logging.NullHandler()], force=True)
    metadata = _AttemptMetadata()
    logger = logging.getLogger("infra.llm")
    logger.handlers = [metadata]
    logger.propagate = False
    logger.setLevel(logging.WARNING)
    overrides = {"LLM_MODE": "live", "LLM_CACHE": "0", "LLM_RETRIES": "0"}
    previous = {name: os.environ.get(name) for name in (*overrides, "DATABASE_PATH")}
    previous_cwd = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix="openai_production_smoke_") as directory:
            os.environ.update(overrides)
            os.environ["DATABASE_PATH"] = str(Path(directory) / "smoke.db")
            # Tránh loader đọc .env local; imports vẫn dùng repo root từ python -m.
            os.chdir(directory)
            try:
                return _run(metadata)
            finally:
                # Windows cần rời thư mục trước khi TemporaryDirectory xóa nó.
                os.chdir(previous_cwd)
    except Exception as error:
        print(json.dumps({"local_error_class": type(error).__name__, "result": "FAIL"}))
        return 1
    finally:
        os.chdir(previous_cwd)
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


if __name__ == "__main__":
    raise SystemExit(main())
