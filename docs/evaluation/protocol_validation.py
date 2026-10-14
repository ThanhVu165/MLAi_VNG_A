"""Kiểm chứng offline M4-T01; không có collector hoặc quyền chạy evaluation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from math import isfinite, sqrt
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROUTES = {"AUTO_REPLY", "ESCALATE"}
STOPS = {"FACT_UNRESOLVED", "OUT_OF_POLICY", "AUTHORITY_REQUIRED"}
GOLD_RULES = {
    "P01": ("ESCALATE", "AUTHORITY_REQUIRED"),
    "P02": ("ESCALATE", "OUT_OF_POLICY"),
    "P03": ("ESCALATE", "FACT_UNRESOLVED"),
    "P04": ("ESCALATE", "FACT_UNRESOLVED"),
    "P05": ("AUTO_REPLY", None),
}
Z95 = 1.959963984540054
SCHEMA = json.loads(Path(__file__).with_name("M4_T01_SCHEMA.json").read_text(encoding="utf-8"))


def _validate_record(value: object, kind: str) -> None:
    validator = Draft202012Validator(
        {"$ref": f"#/$defs/{kind}", "$defs": SCHEMA["$defs"]}, format_checker=FormatChecker()
    )
    try:
        validator.validate(value)
    except ValidationError:
        raise ValueError(f"Record {kind} không đúng schema") from None


def proportion(n: int, total: int) -> dict:
    """Trả raw n/N và Wilson 95%; mẫu số rỗng là UNDEFINED."""
    if type(n) is not int or type(total) is not int or not 0 <= n <= total:
        raise ValueError("Cần số nguyên 0 <= n <= N")
    if total == 0:
        return {"n": n, "N": total, "rate": None, "wilson95": None, "status": "UNDEFINED"}
    p = n / total
    z2 = Z95**2
    divisor = 1 + z2 / total
    center = (p + z2 / (2 * total)) / divisor
    half = Z95 * sqrt(p * (1 - p) / total + z2 / (4 * total**2)) / divisor
    return {
        "n": n,
        "N": total,
        "rate": p,
        "wilson95": [max(0.0, center - half), min(1.0, center + half)],
        "status": "DEFINED",
    }


def outcome(row: dict | None) -> str:
    """Phân loại output trước khi tính metric; lỗi không trở thành business route."""
    if row is None:
        return "MISSING"
    try:
        _validate_record(row, "result")
    except ValueError:
        return "MALFORMED"
    elapsed = row["elapsed_ms"]
    if elapsed is not None and not isfinite(elapsed):
        return "MALFORMED"
    return row["outcome"]


def validate_cases(cases: list[dict]) -> list[str]:
    """Kiểm Gold route/stop/rule và identity; không sửa nhãn."""
    if not isinstance(cases, list):
        raise ValueError("Cases phải là array")
    for case in cases:
        _validate_record(case, "case")
    ids = [case["id"] for case in cases]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("Case IDs trống hoặc trùng")
    for case in cases:
        expected = (case["expected_decision"], case["expected_type"])
        if GOLD_RULES.get(case["expected_rule_id"]) != expected:
            raise ValueError("Gold rule/route/stop không nhất quán")
        timestamp = datetime.fromisoformat(case["input"]["received_at"])
        if timestamp.utcoffset() is None:
            raise ValueError("received_at cần timezone")
    return ids


def criterion_summary(judgments: list[str]) -> dict:
    """Chỉ nhận quần thể applicable đã khóa; không tự loại NOT_REVIEWED."""
    if any(j not in {"PASS", "FAIL", "NOT_REVIEWED"} for j in judgments):
        raise ValueError("Judgment không hợp lệ trong applicable population")
    counts = Counter(judgments)
    reviewed = counts["PASS"] + counts["FAIL"]
    return {
        "success": proportion(counts["PASS"], len(judgments)),
        "review_coverage": proportion(reviewed, len(judgments)),
        "reviewed_only": proportion(counts["PASS"], reviewed),
        "not_reviewed": counts["NOT_REVIEWED"],
    }


def validate_manifest(
    manifest: dict, case_bytes: bytes, protocol_bytes: bytes, *, runtime_sha: str
) -> None:
    """So exact bytes/count/ordered IDs; không xác nhận lịch sử preregistration."""
    _validate_record(manifest, "manifest")
    if manifest["runtime_sha"] != runtime_sha:
        raise ValueError("Runtime SHA mismatch với receipt kỳ vọng")
    cases = json.loads(case_bytes)
    ids = validate_cases(cases)
    if manifest["case_ids"] != ids or manifest["planned_count"] != len(ids):
        raise ValueError("Manifest case inventory mismatch")
    if any(case["gold_version"] != manifest["gold_version"] for case in cases):
        raise ValueError("Gold version mismatch")
    if manifest["dataset_sha256"] != sha256(case_bytes).hexdigest():
        raise ValueError("Dataset digest mismatch")
    if manifest["protocol_sha256"] != sha256(protocol_bytes).hexdigest():
        raise ValueError("Protocol digest mismatch")
    if manifest["execution_authorized"]:
        raise ValueError("T01 validator chỉ nhận preparation manifest không có quyền chạy")


def summarize(cases: list[dict], rows: list[dict]) -> dict:
    """Metric synthetic, giữ toàn planned population và mọi missing/failure."""
    ids = validate_cases(cases)
    outputs: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Output không có identity; cần reconciliation")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or case_id not in ids or case_id in outputs:
            raise ValueError("Output ID thiếu, lạ hoặc trùng; cần reconciliation")
        outputs[case_id] = row
    matrix = Counter({"TP": 0, "FN": 0, "FP": 0, "TN": 0})
    counts = Counter(
        {k: 0 for k in ("VALID", "TECHNICAL_ERROR", "MALFORMED", "MISSING", "INVALID_INPUT")}
    )
    by_gold = {route: Counter() for route in sorted(ROUTES)}
    stop_matrix: dict[str, Counter] = {stop: Counter() for stop in sorted(STOPS)}
    stop_correct = rule_correct = 0
    for case in cases:
        row = outputs.get(case["id"])
        category = outcome(row)
        counts[category] += 1
        gold = case["expected_decision"]
        column = row["actual_decision"] if category == "VALID" else category
        by_gold[gold][column] += 1
        if category != "VALID":
            continue
        pred = row["actual_decision"]
        key = (
            ("TP" if pred == "ESCALATE" else "FN")
            if gold == "ESCALATE"
            else ("FP" if pred == "ESCALATE" else "TN")
        )
        matrix[key] += 1
        rule_correct += row["rule_id"] == case["expected_rule_id"]
        if gold == "ESCALATE":
            stop_matrix[case["expected_type"]][row["actual_type"] or "AUTO_REPLY"] += 1
            stop_correct += row["actual_type"] == case["expected_type"]
    tp, fn, fp, tn = (matrix[k] for k in ("TP", "FN", "FP", "TN"))
    valid, total = counts["VALID"], len(ids)
    metrics = {
        "MER": proportion(fn, tp + fn),
        "OER": proportion(fp, tn + fp),
        "escalation_precision": proportion(tp, tp + fp),
        "escalation_recall": proportion(tp, tp + fn),
        "route_correctness": proportion(tp + tn, valid),
        "coverage": proportion(valid, total),
        "technical_failure": proportion(counts["TECHNICAL_ERROR"] + counts["MALFORMED"], total),
        "missingness": proportion(counts["MISSING"], total),
        "invalid_input": proportion(counts["INVALID_INPUT"], total),
        "end_to_end_route_success": proportion(tp + tn, total),
        "stop_correctness": proportion(stop_correct, tp + fn),
        "conditional_stop_correctness": proportion(stop_correct, tp),
        "rule_correctness": proportion(rule_correct, valid),
    }
    bounds = {}
    for route, error_count in (("ESCALATE", fn), ("AUTO_REPLY", fp)):
        planned = sum(case["expected_decision"] == route for case in cases)
        nonbusiness = sum(by_gold[route][k] for k in counts if k != "VALID")
        bounds[route] = {
            "planned": planned,
            "nonbusiness": nonbusiness,
            "lower": error_count / planned if planned else None,
            "upper": (error_count + nonbusiness) / planned if planned else None,
        }
    return {
        "confusion": dict(matrix),
        "outcomes": dict(counts),
        "by_gold": by_gold,
        "stop_matrix": stop_matrix,
        "metrics": metrics,
        "missing_outcome_bounds": bounds,
    }
