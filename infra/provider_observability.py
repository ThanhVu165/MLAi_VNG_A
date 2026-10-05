"""Bounded, fail-closed diagnostics; never serialize SDK requests or responses."""

from __future__ import annotations

import json
import os
import re

MAX_TEXT = 512
MAX_ITEMS = 8
MAX_DEPTH = 4
MAX_DIAGNOSTIC_CHARS = 4096
REDACTED = "[REDACTED]"
_SAFE_FIELDS = frozenset(
    {"error", "code", "status", "reason", "message", "details", "domain", "@type"}
)
_SENSITIVE_LABEL = (
    r"authorization|cookie|set-cookie|password|passwd|pwd|"
    r"[\w-]*(?:token|secret|credential)[\w-]*|api[_ -]?key|"
    r"prompt|contents?|request|response|body|payload|headers?|output"
)
_LABELED_VALUE = re.compile(
    rf"(?i)(?:[\"']?\b(?:{_SENSITIVE_LABEL})\b[\"']?\s*[:=]\s*).*$",
    re.MULTILINE,
)
_BEARER = re.compile(r"(?i)\bBearer\s+[^\s,;\"']+")
_API_KEY = re.compile(r"AIza[A-Za-z0-9_-]{20,}")
_EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+\.[A-Za-z]{2,}")
_MSSV = re.compile(r"(?<!\d)\d{11}(?!\d)")
_CCCD = re.compile(r"(?<!\d)\d{12}(?!\d)")
_PHONE = re.compile(r"(?<!\d)(?:\+84|84|0)[35789]\d{8}(?!\d)")
_OPAQUE_TOKEN = re.compile(r"\b[A-Za-z0-9_-]{32,}(?:\.[A-Za-z0-9_-]+){0,2}\b")
_UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")


def sanitize_case_id(value: str | None, *, prompt: str) -> object:
    """Keep canonical case UUIDs usable as identity, not mistaken for opaque tokens."""
    if (
        type(value) is str
        and _UUID.fullmatch(value)
        and value not in prompt
        and value not in (os.getenv("GOOGLE_API_KEY"), os.getenv("GEMINI_API_KEY"))
    ):
        return value
    return sanitize_diagnostic(value, prompt=prompt)


def _text(value: str, prompt: str | None) -> str:
    # Replace before truncating, so a secret crossing the limit cannot leak a prefix.
    if prompt:
        for representation in (
            prompt,
            json.dumps(prompt, ensure_ascii=False)[1:-1],
            json.dumps(prompt, ensure_ascii=True)[1:-1],
        ):
            value = value.replace(representation, REDACTED)
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        secret = os.getenv(name)
        if secret:
            value = value.replace(secret, REDACTED)
    # A message can itself be a raw JSON/body fallback from the SDK.
    value = re.sub(r"[\{\[<].*$", REDACTED, value, flags=re.DOTALL)
    value = _LABELED_VALUE.sub(REDACTED, value)
    value = re.sub(
        r"(?i)\b(?:authorization|cookie|prompt|contents|body|payload|response|output)\b.*$",
        REDACTED,
        value,
        flags=re.MULTILINE,
    )
    for pattern in (_BEARER, _API_KEY, _EMAIL, _MSSV, _CCCD, _PHONE, _OPAQUE_TOKEN):
        value = pattern.sub(REDACTED, value)
    value = "".join(char if char.isprintable() else " " for char in value)
    return value[:MAX_TEXT]


def sanitize_diagnostic(value: object, *, prompt: str | None = None) -> object:
    """Accept built-in values only; drop unknown fields/objects without repr/str."""

    def visit(item: object, depth: int) -> object:
        if depth > MAX_DEPTH:
            return REDACTED
        if item is None or type(item) in (bool, int):
            return item
        if type(item) is str:
            return _text(item, prompt)
        if type(item) is dict:
            return {
                key: visit(child, depth + 1)
                for key, child in item.items()
                if type(key) is str and key in _SAFE_FIELDS
            }
        if type(item) is list:
            return [visit(child, depth + 1) for child in item[:MAX_ITEMS]]
        return REDACTED

    try:
        result = visit(value, 0)
        if len(json.dumps(result, ensure_ascii=False)) > MAX_DIAGNOSTIC_CHARS:
            return REDACTED
        return result
    except Exception:
        return REDACTED


def exception_diagnostic(error: Exception, *, prompt: str) -> dict[str, object]:
    """Extract SDK metadata without reading response bodies, requests or headers."""

    def attribute(name: str) -> object:
        try:
            return getattr(error, name, None)
        except Exception:
            return None

    code = attribute("code")
    http_status = code if type(code) is int and 100 <= code <= 599 else None
    if http_status is None:
        try:
            status_code = getattr(attribute("response"), "status_code", None)
            if type(status_code) is int and 100 <= status_code <= 599:
                http_status = status_code
        except Exception:
            pass
    message = attribute("message")
    if message is None:
        # Avoid SDK __str__: it embeds the whole response_json in APIError.args.
        args = attribute("args")
        if type(args) is tuple and len(args) == 1 and type(args[0]) is str:
            message = args[0]
    details = sanitize_diagnostic(attribute("details"), prompt=prompt)
    reason = attribute("reason")
    if reason is None and type(details) is dict:
        root = details.get("error", details)
        if type(root) is dict:
            reason = root.get("reason")
            if reason is None and type(root.get("details")) is list:
                for detail in root["details"]:
                    if type(detail) is dict and detail.get("reason") is not None:
                        reason = detail["reason"]
                        break
    return {
        "exception_class": type(error).__name__,
        "http_status": http_status,
        "provider_code": sanitize_diagnostic(code, prompt=prompt),
        "provider_status": sanitize_diagnostic(attribute("status"), prompt=prompt),
        "provider_reason": sanitize_diagnostic(reason, prompt=prompt),
        "sanitized_message": sanitize_diagnostic(message, prompt=prompt),
        "sanitized_details": details,
    }
