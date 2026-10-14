"""Offline-only M4-T01 collector and freeze validation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


HERE = Path(__file__).resolve().parent
FREEZE_SCHEMA = json.loads((HERE / "M4_T01_FREEZE_SCHEMA.json").read_text(encoding="utf-8"))
ATTEMPT_KEYS = {
    "run_id",
    "case_id",
    "attempt_id",
    "timestamp",
    "runtime_source_sha",
    "collector_revision",
    "manifest_ref",
    "config_ref",
    "result_status",
    "terminal",
    "business_result",
    "technical_failure",
    "evidence_ref",
}
BUSINESS_KEYS = {"decision", "stop_type", "rule_id"}
TECHNICAL_KEYS = {"code"}
RESULT_STATUSES = {"BUSINESS_RESULT", "TECHNICAL_ERROR", "MALFORMED"}
STOP_TYPES = {"AUTHORITY_REQUIRED", "OUT_OF_POLICY", "FACT_UNRESOLVED"}


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def _valid_attempt(row: object, binding: dict) -> bool:
    if not isinstance(row, dict) or set(row) != ATTEMPT_KEYS:
        return False
    strings = (
        "run_id",
        "case_id",
        "attempt_id",
        "runtime_source_sha",
        "collector_revision",
        "manifest_ref",
        "config_ref",
        "result_status",
        "evidence_ref",
    )
    if any(not isinstance(row[key], str) or not row[key].strip() for key in strings):
        return False
    if type(row["terminal"]) is not bool or row["result_status"] not in RESULT_STATUSES:
        return False
    try:
        _timestamp(row["timestamp"])
    except (TypeError, ValueError):
        return False
    for key in (
        "run_id",
        "runtime_source_sha",
        "collector_revision",
        "manifest_ref",
        "config_ref",
    ):
        if row[key] != binding[key]:
            raise ValueError(f"{key} mismatch")
    business = row["business_result"]
    technical = row["technical_failure"]
    if row["result_status"] == "BUSINESS_RESULT":
        return (
            row["terminal"]
            and isinstance(business, dict)
            and set(business) == BUSINESS_KEYS
            and business["decision"] in {"AUTO_REPLY", "ESCALATE", "INVALID_INPUT"}
            and isinstance(business["rule_id"], str)
            and bool(business["rule_id"].strip())
            and (
                (business["decision"] == "ESCALATE" and business["stop_type"] in STOP_TYPES)
                or (business["decision"] != "ESCALATE" and business["stop_type"] is None)
            )
            and technical is None
        )
    if row["result_status"] == "TECHNICAL_ERROR":
        return (
            business is None
            and isinstance(technical, dict)
            and set(technical) == TECHNICAL_KEYS
            and isinstance(technical["code"], str)
            and bool(technical["code"].strip())
        )
    return business is None and technical is None and row["terminal"]


def _record(case_id: str, status: str, **values: object) -> dict:
    return {
        "case_id": case_id,
        "status": status,
        "terminal_outcome": status,
        "attempt_id": values.get("attempt_id"),
        "timestamp": values.get("timestamp"),
        "business_result": values.get("business_result"),
        "technical_failure": values.get("technical_failure"),
        "evidence_ref": values.get("evidence_ref"),
    }


def reconcile(expected_case_ids: list[str], attempts: list[object], binding: dict) -> dict:
    """Reconcile attempts without dropping missing, malformed, duplicate, or unexpected IDs."""
    required_binding = {
        "run_id",
        "runtime_source_sha",
        "collector_revision",
        "manifest_ref",
        "config_ref",
    }
    if set(binding) != required_binding or any(
        not isinstance(binding[key], str) or not binding[key].strip() for key in required_binding
    ):
        raise ValueError("collector binding is incomplete")
    if (
        not isinstance(expected_case_ids, list)
        or any(not isinstance(value, str) or not value.strip() for value in expected_case_ids)
        or len(expected_case_ids) != len(set(expected_case_ids))
    ):
        raise ValueError("expected case IDs must be unique non-empty strings")
    if not isinstance(attempts, list):
        raise ValueError("attempts must be an array")

    expected = set(expected_case_ids)
    grouped: dict[str, list[dict]] = {case_id: [] for case_id in expected_case_ids}
    unexpected: list[dict] = []
    malformed_without_id = 0
    for row in attempts:
        case_id = row.get("case_id") if isinstance(row, dict) else None
        if not isinstance(case_id, str) or not case_id.strip():
            malformed_without_id += 1
            continue
        if case_id not in expected:
            unexpected.append(_record(case_id, "UNEXPECTED"))
            continue
        if not _valid_attempt(row, binding):
            grouped[case_id].append({"case_id": case_id, "_malformed": True})
            continue
        grouped[case_id].append(row)

    results = []
    for case_id in expected_case_ids:
        rows = grouped[case_id]
        if not rows:
            results.append(_record(case_id, "MISSING"))
            continue
        if any(row.get("_malformed") for row in rows):
            results.append(_record(case_id, "MALFORMED"))
            continue
        attempt_ids = [row["attempt_id"] for row in rows]
        terminal = [row for row in rows if row["terminal"]]
        if len(attempt_ids) != len(set(attempt_ids)) or len(terminal) > 1:
            results.append(_record(case_id, "DUPLICATE"))
            continue
        if not terminal:
            results.append(_record(case_id, "MALFORMED"))
            continue
        row = terminal[0]
        results.append(
            _record(
                case_id,
                row["result_status"],
                attempt_id=row["attempt_id"],
                timestamp=row["timestamp"],
                business_result=row["business_result"],
                technical_failure=row["technical_failure"],
                evidence_ref=row["evidence_ref"],
            )
        )

    all_results = results + unexpected
    counts = Counter(result["status"] for result in all_results)
    return {
        **binding,
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "expected_count": len(expected_case_ids),
        "attempt_count": len(attempts),
        "malformed_without_id": malformed_without_id,
        "results": all_results,
        "counts": dict(sorted(counts.items())),
        "complete": len(results) == len(expected_case_ids)
        and all(result["status"] != "MISSING" for result in results),
    }


def _unresolved_paths(value: object, path: str = "$") -> list[str]:
    if value == "NOT_RESOLVED":
        return [path]
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in _unresolved_paths(child, f"{path}.{key}")
        ]
    if isinstance(value, list):
        return [
            item
            for index, child in enumerate(value)
            for item in _unresolved_paths(child, f"{path}[{index}]")
        ]
    return []


def validate_freeze_manifest(
    manifest: dict, *, expected_runtime_sha: str, official_execution_ready: bool = False
) -> str:
    """Validate the template; official readiness fails closed until every gate is resolved."""
    try:
        Draft202012Validator(FREEZE_SCHEMA, format_checker=FormatChecker()).validate(manifest)
    except ValidationError as error:
        raise ValueError("freeze manifest does not match schema") from error
    if manifest["runtime_source_sha"] != expected_runtime_sha:
        raise ValueError("runtime_source_sha mismatch")
    unresolved = _unresolved_paths(manifest)
    expected_status = "FREEZE_INCOMPLETE" if unresolved else "FROZEN"
    if manifest["freeze_status"] != expected_status:
        raise ValueError("freeze_status does not match unresolved fields")
    if official_execution_ready and (
        unresolved
        or not manifest["execution_authorized"]
        or manifest["budget"] <= 0
        or manifest["execution_mode"] != "LIVE"
    ):
        raise ValueError("OFFICIAL_EXECUTION_READY validation failed")
    return expected_status
